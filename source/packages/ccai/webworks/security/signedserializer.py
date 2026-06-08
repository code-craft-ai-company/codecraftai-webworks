"""
.. module:: signedserializer
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: In-house HMAC-signed, timestamped serializer for small
        round-trip payloads such as the OAuth pre-auth state cookie.

.. moduleauthor:: Code Craft AI LLC

:class:`TimedSerializer` packs a small JSON-serializable payload into a
compact, URL-safe, tamper-evident token and reads it back, rejecting
tokens that have been altered, signed with a different key, or aged
past a caller-supplied maximum. It is the in-house replacement for the
narrow slice of ``itsdangerous.URLSafeTimedSerializer`` that the
webworks OAuth client blueprint relied on (``dumps`` / ``loads`` with a
``max_age``).

The token shape is::

    <payload_b64url>.<timestamp_b64url>.<signature_b64url>

where ``signature`` is an HMAC-SHA256 over
``"<payload_b64url>.<timestamp_b64url>"`` computed with a per-salt
signing key derived from the site secret. The whole module is built on
the standard library; it adds no third-party dependency.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


import base64
import hashlib
import hmac
import json
import time

from typing import Any, Optional, Union


# The HMAC construction used for the token signature. SHA-256 is a
# deliberate upgrade over itsdangerous' historical SHA-1 default; the
# token is only ever produced and consumed by webworks itself, so the
# wire format is free to be chosen for strength rather than
# compatibility.
_SIGNATURE_DIGEST = "sha256"

# Domain-separation label folded into the derived signing key so that a
# secret reused across subsystems produces distinct keys here.
_KEY_DERIVATION_LABEL = b"ccai.webworks.signedserializer"


class BadSignatureError(Exception):
    """
        Raised when a token's signature does not verify — the token was
        tampered with, truncated, or signed with a different key.
    """


class BadTimeSignatureError(BadSignatureError):
    """
        Raised when a token's signature is valid but it has aged past
        the caller-supplied ``max_age``.
    """


class BadPayloadError(Exception):
    """
        Raised when a token is structurally malformed or its payload is
        not valid JSON.
    """


def _b64url_encode(data: bytes) -> str:
    """
        Encode bytes as base64url text with padding stripped.

        :param data: The bytes to encode.

        :returns: The base64url text.
    """
    encoded = base64.urlsafe_b64encode(data).rstrip(b"=")
    rtnval = encoded.decode("ascii")
    return rtnval


def _b64url_decode(text: str) -> bytes:
    """
        Decode base64url text, restoring stripped padding.

        :param text: The base64url text.

        :returns: The decoded bytes.
        :raises BadPayloadError: When the text is not valid base64url.
    """
    text_value = str(text)

    remainder = len(text_value) % 4
    if remainder != 0:
        pad_count = 4 - remainder
        text_value = text_value + ("=" * pad_count)

    try:
        decoded = base64.urlsafe_b64decode(text_value.encode("ascii"))
    except (ValueError, UnicodeEncodeError) as decode_exc:
        errmsg = "Token segment is not valid base64url."
        raise BadPayloadError(errmsg) from decode_exc

    return decoded


class TimedSerializer:
    """
        Sign and timestamp a small payload into a URL-safe token, and
        verify it on the return trip.

        :param secret_key: The site signing secret. ``str`` values are
                           UTF-8 encoded.
        :param salt: Optional namespace salt mixed into the derived
                     signing key, so the same secret yields independent
                     signatures for different cookie purposes.

        :raises ValueError: When *secret_key* is empty.
    """

    def __init__(
        self,
        secret_key: Union[str, bytes],
        *,
        salt: Optional[Union[str, bytes]] = None,
    ) -> None:
        if isinstance(secret_key, str):
            secret_bytes = secret_key.encode("utf-8")
        else:
            secret_bytes = bytes(secret_key or b"")

        if len(secret_bytes) == 0:
            raise ValueError("TimedSerializer requires a non-empty secret_key.")

        if salt is None:
            salt_bytes = b""
        elif isinstance(salt, str):
            salt_bytes = salt.encode("utf-8")
        else:
            salt_bytes = bytes(salt)

        self._signing_key = self._derive_signing_key(secret_bytes, salt_bytes)
        return

    def _derive_signing_key(self, secret_bytes: bytes, salt_bytes: bytes) -> bytes:
        """
            Derive the per-salt HMAC signing key from the secret.

            :param secret_bytes: The raw secret bytes.
            :param salt_bytes: The raw salt bytes.

            :returns: The derived signing key.
        """
        message = _KEY_DERIVATION_LABEL + b"|" + salt_bytes
        derived = hmac.new(secret_bytes, message, _SIGNATURE_DIGEST).digest()
        return derived

    def _compute_signature(self, signing_input: bytes) -> bytes:
        """
            Compute the HMAC signature over the signing input.

            :param signing_input: The ASCII bytes being signed.

            :returns: The signature bytes.
        """
        signature = hmac.new(
            self._signing_key,
            signing_input,
            _SIGNATURE_DIGEST,
        ).digest()
        return signature

    def dumps(self, obj: Any) -> str:
        """
            Serialize, timestamp, and sign a payload into a token.

            :param obj: A JSON-serializable payload.

            :returns: The compact, URL-safe signed token.
        """
        payload_bytes = json.dumps(
            obj,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")

        payload_segment = _b64url_encode(payload_bytes)

        issued_at = int(time.time())
        timestamp_bytes = str(issued_at).encode("ascii")
        timestamp_segment = _b64url_encode(timestamp_bytes)

        signing_input = "{}.{}".format(
            payload_segment,
            timestamp_segment,
        ).encode("ascii")

        signature = self._compute_signature(signing_input)
        signature_segment = _b64url_encode(signature)

        rtnval = "{}.{}.{}".format(
            payload_segment,
            timestamp_segment,
            signature_segment,
        )
        return rtnval

    def loads(self, token: str, *, max_age: Optional[int] = None) -> Any:
        """
            Verify a token and return its payload.

            :param token: The signed token produced by :meth:`dumps`.
            :param max_age: Optional maximum token age in seconds. When
                            supplied, a token whose timestamp is older
                            than ``max_age`` is rejected.

            :returns: The deserialized payload.
            :raises BadPayloadError: When the token is malformed.
            :raises BadSignatureError: When the signature does not
                                       verify.
            :raises BadTimeSignatureError: When the token is older than
                                           ``max_age``.
        """
        token_text = str(token or "").strip()

        segments = token_text.split(".")
        if len(segments) != 3:
            errmsg = "Signed token must have exactly three segments."
            raise BadPayloadError(errmsg)

        payload_segment, timestamp_segment, signature_segment = segments

        signing_input = "{}.{}".format(
            payload_segment,
            timestamp_segment,
        ).encode("ascii")

        expected_signature = self._compute_signature(signing_input)
        provided_signature = _b64url_decode(signature_segment)

        signature_ok = hmac.compare_digest(expected_signature, provided_signature)
        if signature_ok is not True:
            errmsg = "Signed token signature does not verify."
            raise BadSignatureError(errmsg)

        timestamp_bytes = _b64url_decode(timestamp_segment)
        try:
            issued_at = int(timestamp_bytes.decode("ascii"))
        except (ValueError, UnicodeDecodeError) as ts_exc:
            errmsg = "Signed token timestamp is not a valid integer."
            raise BadPayloadError(errmsg) from ts_exc

        if max_age is not None:
            now = int(time.time())
            age = now - issued_at
            if age > int(max_age):
                errmsg = "Signed token is older than the permitted max_age."
                raise BadTimeSignatureError(errmsg)

        payload_bytes = _b64url_decode(payload_segment)
        try:
            rtnval = json.loads(payload_bytes.decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as payload_exc:
            errmsg = "Signed token payload is not valid JSON."
            raise BadPayloadError(errmsg) from payload_exc

        return rtnval


__all__ = [
    "BadPayloadError",
    "BadSignatureError",
    "BadTimeSignatureError",
    "TimedSerializer",
]
