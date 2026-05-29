"""
.. module:: jsonwebtoken
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: In-house JSON Object Signing and Encryption (JOSE)
        primitives — JSON Web Key / Key Set parsing, JSON Web
        Signature verification, and JSON Web Token decode plus claims
        validation.

.. moduleauthor:: Automation Mojo LLC

This module provides the small, well-scoped slice of the JOSE
specifications that the webworks authentication stack actually needs:

    * Parse a JWK / JWKS document (RFC 7517) into verification keys.
    * Verify a compact JWS (RFC 7515) signature for the HMAC
      (``HS256`` / ``HS384`` / ``HS512``), RSASSA-PKCS1-v1_5
      (``RS256`` / ``RS384`` / ``RS512``), RSASSA-PSS (``PS256`` /
      ``PS384`` / ``PS512``), and ECDSA (``ES256`` / ``ES384`` /
      ``ES512``) algorithm families.
    * Decode a compact JWT (RFC 7519), verifying the signature and
      returning the header and claim set.
    * Validate claims against a small registry that mirrors the
      ``essential`` / ``value`` semantics every relying-party needs
      (``iss`` / ``aud`` / ``nonce`` exact-match plus ``exp`` / ``nbf``
      time-window checks).

The asymmetric signature verification is delegated to
:mod:`cryptography` (PyCA) — the de-facto standard primitive library
for RSA and ECDSA in Python. Everything else (base64url, the compact
serialization split, the claims registry, the HMAC path) is built on
the standard library. The module intentionally owns the protocol
logic rather than depending on a higher-level JOSE framework such as
``authlib`` or ``joserfc``.
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


import base64
import hashlib
import hmac
import json
import time

from typing import Any, Dict, List, Optional, Union


# Map each JWS algorithm identifier to the hash construction it uses.
# Restricting verification to this explicit table (rather than echoing
# whatever ``alg`` the token header advertises) is the primary defence
# against algorithm-confusion attacks.
HMAC_ALGORITHMS: Dict[str, str] = {
    "HS256": "sha256",
    "HS384": "sha384",
    "HS512": "sha512",
}

RSA_PKCS1_ALGORITHMS: Dict[str, str] = {
    "RS256": "sha256",
    "RS384": "sha384",
    "RS512": "sha512",
}

RSA_PSS_ALGORITHMS: Dict[str, str] = {
    "PS256": "sha256",
    "PS384": "sha384",
    "PS512": "sha512",
}

ECDSA_ALGORITHMS: Dict[str, str] = {
    "ES256": "sha256",
    "ES384": "sha384",
    "ES512": "sha512",
}


class JoseError(Exception):
    """
        Base class for all JOSE-related failures raised by this module.
    """


class DecodeError(JoseError):
    """
        Raised when a compact JWS / JWT cannot be parsed into its
        constituent segments, or a segment is not valid base64url /
        JSON.
    """


class UnsupportedAlgorithmError(JoseError):
    """
        Raised when a token requests, or a caller permits, a signing
        algorithm this module does not implement.
    """


class InvalidSignatureError(JoseError):
    """
        Raised when a token's signature does not verify against the
        supplied key.
    """


class InvalidClaimError(JoseError):
    """
        Raised when a claim is missing, has the wrong value, or falls
        outside its valid time window.

        :param claim: The name of the offending claim.
        :param description: Human-readable explanation.
    """

    def __init__(self, claim: str, description: str) -> None:
        self.claim = claim
        self.description = description
        message = "Invalid claim {!r}: {}".format(claim, description)
        super().__init__(message)
        return


def base64url_decode(segment: str) -> bytes:
    """
        Decode a base64url-encoded segment, restoring the padding that
        the compact serialization strips.

        :param segment: The base64url text to decode.

        :returns: The decoded bytes.
        :raises DecodeError: When the segment is not valid base64url.
    """
    segment_text = str(segment)

    remainder = len(segment_text) % 4
    if remainder != 0:
        pad_count = 4 - remainder
        segment_text = segment_text + ("=" * pad_count)

    try:
        decoded = base64.urlsafe_b64decode(segment_text.encode("ascii"))
    except (ValueError, UnicodeEncodeError) as decode_exc:
        errmsg = "Segment is not valid base64url."
        raise DecodeError(errmsg) from decode_exc

    return decoded


def base64url_encode(data: bytes) -> str:
    """
        Encode bytes as base64url text with the padding stripped, per
        the compact serialization rules.

        :param data: The bytes to encode.

        :returns: The base64url text.
    """
    encoded = base64.urlsafe_b64encode(data).rstrip(b"=")
    rtnval = encoded.decode("ascii")
    return rtnval


def _int_from_base64url(segment: str) -> int:
    """
        Decode a base64url big-endian unsigned integer (the encoding
        JWK uses for RSA modulus / exponent and EC coordinates).

        :param segment: The base64url text to decode.

        :returns: The decoded integer.
    """
    raw = base64url_decode(segment)
    rtnval = int.from_bytes(raw, byteorder="big")
    return rtnval


class JsonWebKey:
    """
        A single parsed JSON Web Key suitable for signature
        verification.

        The constructor takes the raw JWK mapping and eagerly builds
        the corresponding :mod:`cryptography` public key object so that
        a malformed key fails fast at parse time rather than at verify
        time.

        :param jwk: The raw JWK mapping (one entry from a JWKS
                    ``keys`` array).

        :raises JoseError: When the key type is unsupported or the key
                           material cannot be parsed.
    """

    def __init__(self, jwk: Dict[str, Any]) -> None:
        self._jwk = dict(jwk or {})
        self._kid = str(self._jwk.get("kid") or "").strip()
        self._kty = str(self._jwk.get("kty") or "").strip()
        self._alg = str(self._jwk.get("alg") or "").strip()
        self._public_key = self._build_public_key()
        return

    @property
    def kid(self) -> str:
        """
            :returns: The key id, or an empty string when the JWK omits
                      one.
        """
        return self._kid

    @property
    def kty(self) -> str:
        """
            :returns: The key type (``RSA`` or ``EC``).
        """
        return self._kty

    @property
    def algorithm(self) -> str:
        """
            :returns: The ``alg`` hint declared on the JWK, or an empty
                      string when absent.
        """
        return self._alg

    @property
    def public_key(self) -> Any:
        """
            :returns: The underlying :mod:`cryptography` public key
                      object.
        """
        return self._public_key

    def _build_public_key(self) -> Any:
        """
            Construct the cryptography public key object from the JWK
            material.

            :returns: An RSA or EC public key object.
            :raises JoseError: When the key type is unsupported.
        """
        if self._kty == "RSA":
            rtnval = self._build_rsa_public_key()
            return rtnval

        if self._kty == "EC":
            rtnval = self._build_ec_public_key()
            return rtnval

        errmsg = "Unsupported JWK key type {!r}.".format(self._kty)
        raise JoseError(errmsg)

    def _build_rsa_public_key(self) -> Any:
        """
            Build an RSA public key from the JWK ``n`` / ``e`` members.

            :returns: An RSA public key object.
            :raises JoseError: When the modulus / exponent are missing.
        """
        from cryptography.hazmat.primitives.asymmetric import rsa

        modulus_segment = str(self._jwk.get("n") or "").strip()
        exponent_segment = str(self._jwk.get("e") or "").strip()

        if modulus_segment == "" or exponent_segment == "":
            errmsg = "RSA JWK is missing the 'n' or 'e' member."
            raise JoseError(errmsg)

        modulus = _int_from_base64url(modulus_segment)
        exponent = _int_from_base64url(exponent_segment)

        public_numbers = rsa.RSAPublicNumbers(e=exponent, n=modulus)
        rtnval = public_numbers.public_key()
        return rtnval

    def _build_ec_public_key(self) -> Any:
        """
            Build an elliptic-curve public key from the JWK ``crv`` /
            ``x`` / ``y`` members.

            :returns: An EC public key object.
            :raises JoseError: When the curve is unsupported or the
                               coordinates are missing.
        """
        from cryptography.hazmat.primitives.asymmetric import ec

        curve_name = str(self._jwk.get("crv") or "").strip()
        x_segment = str(self._jwk.get("x") or "").strip()
        y_segment = str(self._jwk.get("y") or "").strip()

        if x_segment == "" or y_segment == "":
            errmsg = "EC JWK is missing the 'x' or 'y' coordinate."
            raise JoseError(errmsg)

        curve_by_name = {
            "P-256": ec.SECP256R1,
            "P-384": ec.SECP384R1,
            "P-521": ec.SECP521R1,
        }

        curve_factory = curve_by_name.get(curve_name)
        if curve_factory is None:
            errmsg = "Unsupported EC curve {!r}.".format(curve_name)
            raise JoseError(errmsg)

        x_value = _int_from_base64url(x_segment)
        y_value = _int_from_base64url(y_segment)

        public_numbers = ec.EllipticCurvePublicNumbers(
            x=x_value,
            y=y_value,
            curve=curve_factory(),
        )
        rtnval = public_numbers.public_key()
        return rtnval


class JsonWebKeySet:
    """
        A parsed JSON Web Key Set with lookup by key id.

        :param jwks: The raw JWKS mapping (with a ``keys`` array), the
                     ``keys`` array itself, or a single JWK mapping.

        :raises JoseError: When no usable keys can be parsed.
    """

    def __init__(self, jwks: Union[Dict[str, Any], List[Dict[str, Any]]]) -> None:
        self._keys: List[JsonWebKey] = []

        raw_keys = self._extract_raw_keys(jwks)

        for raw_key in raw_keys:
            if not isinstance(raw_key, dict):
                continue

            key_type = str(raw_key.get("kty") or "").strip()
            if key_type not in ("RSA", "EC"):
                # Skip key types this module does not verify against
                # (e.g. symmetric ``oct`` keys published in a JWKS).
                continue

            parsed_key = JsonWebKey(raw_key)
            self._keys.append(parsed_key)

        if len(self._keys) == 0:
            errmsg = "JWKS document contains no usable RSA or EC keys."
            raise JoseError(errmsg)

        return

    @classmethod
    def import_key_set(
        cls,
        jwks: Union[Dict[str, Any], List[Dict[str, Any]]],
    ) -> "JsonWebKeySet":
        """
            Parse a JWKS document into a key set.

            :param jwks: The raw JWKS mapping or ``keys`` array.

            :returns: The parsed key set.
        """
        rtnval = cls(jwks)
        return rtnval

    def _extract_raw_keys(
        self,
        jwks: Union[Dict[str, Any], List[Dict[str, Any]]],
    ) -> List[Any]:
        """
            Normalize the several accepted input shapes into a list of
            raw JWK mappings.

            :param jwks: The raw JWKS input.

            :returns: A list of candidate raw JWK mappings.
        """
        if isinstance(jwks, list):
            rtnval = list(jwks)
            return rtnval

        if isinstance(jwks, dict):
            keys_member = jwks.get("keys")
            if isinstance(keys_member, list):
                rtnval = list(keys_member)
                return rtnval

            # A bare single-key mapping.
            rtnval = [jwks]
            return rtnval

        errmsg = "JWKS input must be a mapping or a list of JWK mappings."
        raise JoseError(errmsg)

    def find_key(self, kid: Optional[str] = None) -> JsonWebKey:
        """
            Select the verification key for a token.

            When *kid* is supplied, the matching key is returned. When
            it is absent (or unmatched) and the set holds exactly one
            key, that key is returned — the common single-key provider
            case.

            :param kid: The key id from the token header, if any.

            :returns: The selected key.
            :raises JoseError: When no suitable key can be selected.
        """
        kid_value = str(kid or "").strip()

        if kid_value != "":
            for candidate in self._keys:
                if candidate.kid == kid_value:
                    return candidate

            errmsg = "No key in the JWKS matches kid {!r}.".format(kid_value)
            raise JoseError(errmsg)

        if len(self._keys) == 1:
            rtnval = self._keys[0]
            return rtnval

        errmsg = (
            "Token header has no 'kid' and the JWKS holds multiple "
            "keys; cannot select a verification key unambiguously."
        )
        raise JoseError(errmsg)


def _verify_hmac(
    signing_input: bytes,
    signature: bytes,
    key: Union[str, bytes],
    algorithm: str,
) -> bool:
    """
        Verify an HMAC (``HS*``) signature in constant time.

        :param signing_input: The ``header.payload`` ASCII bytes.
        :param signature: The decoded signature bytes from the token.
        :param key: The shared secret.
        :param algorithm: The ``HS*`` algorithm identifier.

        :returns: ``True`` when the signature matches.
    """
    digest_name = HMAC_ALGORITHMS[algorithm]

    if isinstance(key, str):
        key_bytes = key.encode("utf-8")
    else:
        key_bytes = bytes(key)

    computed = hmac.new(key_bytes, signing_input, digest_name).digest()

    rtnval = hmac.compare_digest(computed, signature)
    return rtnval


def _hash_for_digest_name(digest_name: str) -> Any:
    """
        Map a hashlib digest name to a :mod:`cryptography` hash
        instance.

        :param digest_name: One of ``sha256`` / ``sha384`` / ``sha512``.

        :returns: A cryptography hash algorithm instance.
    """
    from cryptography.hazmat.primitives import hashes

    hash_by_name = {
        "sha256": hashes.SHA256,
        "sha384": hashes.SHA384,
        "sha512": hashes.SHA512,
    }

    hash_factory = hash_by_name[digest_name]
    rtnval = hash_factory()
    return rtnval


def _verify_rsa_pkcs1(
    signing_input: bytes,
    signature: bytes,
    public_key: Any,
    algorithm: str,
) -> bool:
    """
        Verify an RSASSA-PKCS1-v1_5 (``RS*``) signature.

        :param signing_input: The ``header.payload`` ASCII bytes.
        :param signature: The decoded signature bytes from the token.
        :param public_key: The RSA public key object.
        :param algorithm: The ``RS*`` algorithm identifier.

        :returns: ``True`` when the signature verifies.
    """
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric import padding

    digest_name = RSA_PKCS1_ALGORITHMS[algorithm]
    hash_instance = _hash_for_digest_name(digest_name)

    try:
        public_key.verify(
            signature,
            signing_input,
            padding.PKCS1v15(),
            hash_instance,
        )
    except InvalidSignature:
        return False

    return True


def _verify_rsa_pss(
    signing_input: bytes,
    signature: bytes,
    public_key: Any,
    algorithm: str,
) -> bool:
    """
        Verify an RSASSA-PSS (``PS*``) signature.

        :param signing_input: The ``header.payload`` ASCII bytes.
        :param signature: The decoded signature bytes from the token.
        :param public_key: The RSA public key object.
        :param algorithm: The ``PS*`` algorithm identifier.

        :returns: ``True`` when the signature verifies.
    """
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric import padding

    digest_name = RSA_PSS_ALGORITHMS[algorithm]
    hash_instance = _hash_for_digest_name(digest_name)
    mgf_hash = _hash_for_digest_name(digest_name)

    pss_padding = padding.PSS(
        mgf=padding.MGF1(mgf_hash),
        salt_length=hash_instance.digest_size,
    )

    try:
        public_key.verify(
            signature,
            signing_input,
            pss_padding,
            hash_instance,
        )
    except InvalidSignature:
        return False

    return True


def _verify_ecdsa(
    signing_input: bytes,
    signature: bytes,
    public_key: Any,
    algorithm: str,
) -> bool:
    """
        Verify an ECDSA (``ES*``) signature.

        JOSE encodes the ECDSA signature as the fixed-length
        concatenation of the ``r`` and ``s`` values; :mod:`cryptography`
        expects the DER encoding, so the raw pair is converted before
        verification.

        :param signing_input: The ``header.payload`` ASCII bytes.
        :param signature: The decoded ``r || s`` signature bytes.
        :param public_key: The EC public key object.
        :param algorithm: The ``ES*`` algorithm identifier.

        :returns: ``True`` when the signature verifies.
    """
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives.asymmetric.utils import (
        encode_dss_signature,
    )

    digest_name = ECDSA_ALGORITHMS[algorithm]
    hash_instance = _hash_for_digest_name(digest_name)

    signature_length = len(signature)
    if signature_length % 2 != 0:
        return False

    half = signature_length // 2
    r_bytes = signature[:half]
    s_bytes = signature[half:]

    r_value = int.from_bytes(r_bytes, byteorder="big")
    s_value = int.from_bytes(s_bytes, byteorder="big")

    der_signature = encode_dss_signature(r_value, s_value)

    try:
        public_key.verify(
            der_signature,
            signing_input,
            ec.ECDSA(hash_instance),
        )
    except InvalidSignature:
        return False

    return True


def verify_signature(
    signing_input: bytes,
    signature: bytes,
    key: Any,
    algorithm: str,
) -> bool:
    """
        Verify a JWS signature for one of the supported algorithms.

        :param signing_input: The ASCII bytes of ``header.payload``.
        :param signature: The decoded signature bytes.
        :param key: The verification key. For ``HS*`` this is the
                    shared secret (``str`` or ``bytes``); for the
                    asymmetric families it is a :class:`JsonWebKey` or a
                    :mod:`cryptography` public key object.
        :param algorithm: The JWS algorithm identifier.

        :returns: ``True`` when the signature is valid.
        :raises UnsupportedAlgorithmError: When *algorithm* is not in
                                           the supported set.
    """
    if algorithm in HMAC_ALGORITHMS:
        rtnval = _verify_hmac(signing_input, signature, key, algorithm)
        return rtnval

    if isinstance(key, JsonWebKey):
        public_key = key.public_key
    else:
        public_key = key

    if algorithm in RSA_PKCS1_ALGORITHMS:
        rtnval = _verify_rsa_pkcs1(signing_input, signature, public_key, algorithm)
        return rtnval

    if algorithm in RSA_PSS_ALGORITHMS:
        rtnval = _verify_rsa_pss(signing_input, signature, public_key, algorithm)
        return rtnval

    if algorithm in ECDSA_ALGORITHMS:
        rtnval = _verify_ecdsa(signing_input, signature, public_key, algorithm)
        return rtnval

    errmsg = "Unsupported JWS algorithm {!r}.".format(algorithm)
    raise UnsupportedAlgorithmError(errmsg)


class JsonWebToken:
    """
        The decoded result of a verified JWT.

        :param header: The decoded JOSE header.
        :param claims: The decoded claim set.
    """

    def __init__(self, header: Dict[str, Any], claims: Dict[str, Any]) -> None:
        self._header = dict(header)
        self._claims = dict(claims)
        return

    @property
    def header(self) -> Dict[str, Any]:
        """
            :returns: The decoded JOSE header.
        """
        return self._header

    @property
    def claims(self) -> Dict[str, Any]:
        """
            :returns: The decoded claim set.
        """
        return self._claims


def decode_segments(token: str) -> List[str]:
    """
        Split a compact JWS / JWT into its three base64url segments.

        :param token: The compact-serialized token.

        :returns: The ``[header, payload, signature]`` segments.
        :raises DecodeError: When the token does not have three
                             dot-delimited segments.
    """
    token_text = str(token or "").strip()

    segments = token_text.split(".")
    if len(segments) != 3:
        errmsg = "Compact JWT must have exactly three segments."
        raise DecodeError(errmsg)

    return segments


def decode(
    token: str,
    key: Any,
    algorithms: List[str],
) -> JsonWebToken:
    """
        Decode and signature-verify a compact JWT.

        The token header's ``alg`` must be a member of the
        caller-supplied *algorithms* allow-list; this is what defeats
        algorithm-confusion attacks, so the list should be as narrow as
        the deployment permits (never include ``none``).

        :param token: The compact-serialized JWT.
        :param key: The verification key. A :class:`JsonWebKeySet` (the
                    common case for asymmetric tokens — the key is
                    selected by the header ``kid``), a single
                    :class:`JsonWebKey`, a :mod:`cryptography` public
                    key, or a shared secret (``str`` / ``bytes``) for
                    the ``HS*`` family.
        :param algorithms: The allow-list of acceptable ``alg`` values.

        :returns: The decoded token with verified signature.
        :raises DecodeError: When the token is malformed.
        :raises UnsupportedAlgorithmError: When the token's ``alg`` is
                                           not in *algorithms*.
        :raises InvalidSignatureError: When the signature does not
                                       verify.
    """
    if algorithms is None or len(algorithms) == 0:
        errmsg = "An explicit non-empty 'algorithms' allow-list is required."
        raise UnsupportedAlgorithmError(errmsg)

    header_segment, payload_segment, signature_segment = decode_segments(token)

    try:
        header_bytes = base64url_decode(header_segment)
        header = json.loads(header_bytes.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as header_exc:
        errmsg = "JWT header is not valid base64url JSON."
        raise DecodeError(errmsg) from header_exc

    if not isinstance(header, dict):
        errmsg = "JWT header did not decode to an object."
        raise DecodeError(errmsg)

    token_algorithm = str(header.get("alg") or "").strip()
    if token_algorithm not in algorithms:
        errmsg = (
            "JWT 'alg' {!r} is not in the permitted set {!r}.".format(
                token_algorithm,
                algorithms,
            )
        )
        raise UnsupportedAlgorithmError(errmsg)

    selected_key = _select_key_for_header(key, header)

    signing_input = "{}.{}".format(header_segment, payload_segment).encode("ascii")
    signature = base64url_decode(signature_segment)

    signature_ok = verify_signature(
        signing_input=signing_input,
        signature=signature,
        key=selected_key,
        algorithm=token_algorithm,
    )
    if signature_ok is not True:
        errmsg = "JWT signature verification failed."
        raise InvalidSignatureError(errmsg)

    try:
        payload_bytes = base64url_decode(payload_segment)
        claims = json.loads(payload_bytes.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as payload_exc:
        errmsg = "JWT payload is not valid base64url JSON."
        raise DecodeError(errmsg) from payload_exc

    if not isinstance(claims, dict):
        errmsg = "JWT payload did not decode to an object."
        raise DecodeError(errmsg)

    rtnval = JsonWebToken(header=header, claims=claims)
    return rtnval


def _select_key_for_header(key: Any, header: Dict[str, Any]) -> Any:
    """
        Resolve the verification key to use for a token header.

        When *key* is a :class:`JsonWebKeySet`, the key is selected by
        the header ``kid``; otherwise *key* is returned unchanged.

        :param key: The caller-supplied key or key set.
        :param header: The decoded JOSE header.

        :returns: The concrete key to verify against.
    """
    if isinstance(key, JsonWebKeySet):
        kid = header.get("kid")
        rtnval = key.find_key(kid=kid)
        return rtnval

    return key


class ClaimsRegistry:
    """
        A small claims-validation registry mirroring the
        ``essential`` / ``value`` semantics relying parties rely on.

        Each option maps a claim name to a spec dict:

            * ``{"essential": True}`` — the claim must be present.
            * ``{"essential": True, "value": X}`` — the claim must be
              present and equal ``X``.
            * ``{"value": X}`` — when present, the claim must equal
              ``X`` (a missing claim is tolerated).

        In addition, the standard time-window claims ``exp`` and
        ``nbf`` are always enforced when present.

        :param options: Mapping of claim name to spec dict.
        :param leeway: Clock-skew tolerance in seconds applied to the
                       ``exp`` / ``nbf`` checks.
    """

    def __init__(
        self,
        options: Optional[Dict[str, Dict[str, Any]]] = None,
        *,
        leeway: int = 0,
    ) -> None:
        self._options = dict(options or {})
        self._leeway = int(leeway)
        return

    def validate(self, claims: Dict[str, Any]) -> None:
        """
            Validate a claim set against the registered options and the
            standard time-window claims.

            :param claims: The decoded claim set.

            :raises InvalidClaimError: When a claim is missing, has the
                                       wrong value, or is outside its
                                       valid time window.
        """
        self._validate_time_windows(claims)

        for claim_name, spec in self._options.items():
            self._validate_one(claim_name, spec, claims)

        return

    def _validate_one(
        self,
        claim_name: str,
        spec: Dict[str, Any],
        claims: Dict[str, Any],
    ) -> None:
        """
            Validate a single registered claim against its spec.

            :param claim_name: The claim name.
            :param spec: The claim spec dict.
            :param claims: The decoded claim set.

            :raises InvalidClaimError: When the claim fails its spec.
        """
        is_essential = bool(spec.get("essential", False))
        is_present = claim_name in claims

        if is_essential is True and is_present is not True:
            raise InvalidClaimError(claim_name, "essential claim is missing")

        if "value" in spec and is_present is True:
            expected_value = spec.get("value")
            actual_value = claims.get(claim_name)

            if isinstance(actual_value, list):
                value_matches = expected_value in actual_value
            else:
                value_matches = actual_value == expected_value

            if value_matches is not True:
                description = "expected {!r}".format(expected_value)
                raise InvalidClaimError(claim_name, description)

        return

    def _validate_time_windows(self, claims: Dict[str, Any]) -> None:
        """
            Enforce the ``exp`` and ``nbf`` time-window claims when
            present.

            :param claims: The decoded claim set.

            :raises InvalidClaimError: When the token is expired or not
                                       yet valid.
        """
        now = int(time.time())

        if "exp" in claims:
            exp_value = claims.get("exp")
            if not isinstance(exp_value, (int, float)):
                raise InvalidClaimError("exp", "claim must be a number")

            if now > int(exp_value) + self._leeway:
                raise InvalidClaimError("exp", "token has expired")

        if "nbf" in claims:
            nbf_value = claims.get("nbf")
            if not isinstance(nbf_value, (int, float)):
                raise InvalidClaimError("nbf", "claim must be a number")

            if now + self._leeway < int(nbf_value):
                raise InvalidClaimError("nbf", "token is not yet valid")

        return


__all__ = [
    "ClaimsRegistry",
    "DecodeError",
    "InvalidClaimError",
    "InvalidSignatureError",
    "JoseError",
    "JsonWebKey",
    "JsonWebKeySet",
    "JsonWebToken",
    "UnsupportedAlgorithmError",
    "base64url_decode",
    "base64url_encode",
    "decode",
    "decode_segments",
    "verify_signature",
]
