"""
    Credential redaction for the debug and error tooling.

    Error logs, the debug error page and the request inspector all show
    request data. Request data carries credentials: ``Authorization`` and
    ``Cookie`` headers, passwords in form posts, tokens in JSON bodies and
    secrets held in local variables. This module masks those values before
    anything is logged, rendered or stored, so the tooling never becomes a
    way to read another user's session or password.

    Redaction is by name. A header, body field, query parameter or variable
    whose name marks it as a credential has its value replaced with
    :data:`REDACTED`. Matching errs on the side of masking: a harmless
    value that is masked costs a little convenience, a credential that is
    shown does not come back.
"""

import json
import re

from typing import Any, Dict, Mapping, Optional
from urllib.parse import parse_qsl, urlencode


REDACTED = "[REDACTED]"
"""Replacement text for a masked value."""

SENSITIVE_HEADER_NAMES = frozenset([
    "authorization",
    "proxy-authorization",
    "cookie",
    "set-cookie",
    "x-api-key",
    "x-auth-token",
    "x-csrf-token",
    "x-xsrf-token",
])
"""Header names, in lower case, whose values are always masked."""

SENSITIVE_NAME_FRAGMENTS = (
    "password",
    "passwd",
    "passphrase",
    "secret",
    "token",
    "authorization",
    "cookie",
    "credential",
    "apikey",
    "privatekey",
    "session",
)
"""Fragments that mark a name as sensitive wherever they occur in it."""

SENSITIVE_NAME_WORDS = frozenset([
    "key",
    "keys",
    "pwd",
    "pass",
    "pin",
    "otp",
    "auth",
    "csrf",
    "xsrf",
    "jwt",
    "signature",
])
"""Short words that mark a name as sensitive only when they are a whole word of it."""

_WORD_BOUNDARY_PATTERN = re.compile(r"[^A-Za-z0-9]+|(?<=[a-z0-9])(?=[A-Z])")
"""Splits ``api_key``, ``api-key`` and ``apiKey`` into their words."""


def is_sensitive_name(name: Any) -> bool:
    """
        Decide whether a name marks its value as a credential.

        The name is matched in two ways. Long, unambiguous fragments such as
        ``password`` or ``token`` match anywhere in the name
        (``user_password``, ``accessToken``). Short words such as ``key`` or
        ``pin`` match only as a whole word of the name, so ``api_key`` is
        sensitive while ``keyboard`` and ``spinner`` are not.

        :param name: The header, field, parameter or variable name.

        :returns: ``True`` if the value under this name must be masked.
    """
    if not isinstance(name, str):
        name = str(name)

    compact = re.sub(r"[^a-z0-9]", "", name.lower())

    for fragment in SENSITIVE_NAME_FRAGMENTS:
        if fragment in compact:
            return True

    words = _WORD_BOUNDARY_PATTERN.split(name)

    for word in words:
        if word.lower() in SENSITIVE_NAME_WORDS:
            return True

    return False


def redact_header_value(name: Any, value: Any) -> Any:
    """
        Mask the value of a header when the header carries a credential.

        The authentication scheme of an ``Authorization`` value is kept
        (``Bearer [REDACTED]``) because it helps debugging and reveals
        nothing.

        :param name: The header name.
        :param value: The header value.

        :returns: The value, or its masked form.
    """
    name_text = name.decode("latin-1") if isinstance(name, bytes) else str(name)
    lower_name = name_text.lower()

    is_sensitive = lower_name in SENSITIVE_HEADER_NAMES or is_sensitive_name(name_text)

    if not is_sensitive:
        return value

    redacted = REDACTED

    if lower_name in ("authorization", "proxy-authorization"):
        value_text = value.decode("latin-1") if isinstance(value, bytes) else str(value)
        scheme, separator, _credentials = value_text.strip().partition(" ")

        if len(separator) > 0 and scheme.isalpha():
            redacted = "{} {}".format(scheme, REDACTED)

    return redacted


def redact_headers(headers: Optional[Mapping[Any, Any]]) -> Dict[Any, Any]:
    """
        Copy a header mapping with credential values masked.

        :param headers: The header name-to-value mapping, or ``None``.

        :returns: A new dictionary; the input is not modified.
    """
    redacted: Dict[Any, Any] = {}

    if headers is None:
        return redacted

    for name, value in headers.items():
        redacted[name] = redact_header_value(name, value)

    return redacted


def redact_data(data: Any) -> Any:
    """
        Copy a parsed body or parameter structure with credential values masked.

        Dictionaries are walked recursively; a value under a sensitive key
        is replaced whole, whatever its type. Lists and tuples are walked
        so that dictionaries inside them are covered.

        :param data: A JSON-like structure of dictionaries, lists and scalars.

        :returns: A redacted copy; the input is not modified.
    """
    if isinstance(data, Mapping):
        redacted_dict: Dict[Any, Any] = {}

        for key, value in data.items():
            if is_sensitive_name(key):
                redacted_dict[key] = REDACTED
            else:
                redacted_dict[key] = redact_data(value)

        return redacted_dict

    if isinstance(data, (list, tuple)):
        redacted_list = [redact_data(item) for item in data]
        return redacted_list

    return data


def get_header(headers: Optional[Mapping[Any, Any]], name: str) -> Optional[str]:
    """
        Look up a header value by name, ignoring case.

        :param headers: The header mapping, or ``None``.
        :param name: The header name to find.

        :returns: The value as text, or ``None`` if the header is absent.
    """
    if headers is None:
        return None

    lower_name = name.lower()

    for header_name, header_value in headers.items():
        name_text = header_name.decode("latin-1") if isinstance(header_name, bytes) else str(header_name)

        if name_text.lower() == lower_name:
            if isinstance(header_value, bytes):
                return header_value.decode("latin-1")
            return str(header_value)

    return None


def redact_body(body: Any, content_type: Optional[str]) -> Any:
    """
        Mask credentials inside a request body.

        JSON and URL-encoded form bodies are parsed, redacted by field name
        and serialised again. A multipart body can hold credentials in
        fields that cannot be told apart cheaply, so it is replaced by a
        note of its size. A JSON or form body that cannot be parsed is
        replaced as well: content that claims to be structured but is not
        cannot be redacted by field. Other content types are returned
        unchanged.

        :param body: The body as ``bytes`` or ``str``, or ``None``.
        :param content_type: The value of the ``Content-Type`` header.

        :returns: The redacted body, of the same type as the input.
    """
    if body is None:
        return None

    is_bytes = isinstance(body, (bytes, bytearray))

    if is_bytes:
        size = len(body)
        try:
            text = bytes(body).decode("utf-8")
        except UnicodeDecodeError:
            text = None
    else:
        text = str(body)
        size = len(text)

    if size == 0:
        return body

    media_type = ""
    if content_type is not None:
        media_type = content_type.split(";", 1)[0].strip().lower()

    redacted_text = None

    if media_type == "application/json" or media_type.endswith("+json"):
        redacted_text = "{} JSON body: {} bytes, not parseable".format(REDACTED, size)

        if text is not None:
            try:
                parsed = json.loads(text)
                redacted_text = json.dumps(redact_data(parsed))
            except ValueError:
                # Not valid JSON; keep the placeholder set above.
                pass

    elif media_type == "application/x-www-form-urlencoded":
        redacted_text = "{} form body: {} bytes, not parseable".format(REDACTED, size)

        if text is not None:
            try:
                pairs = parse_qsl(text, keep_blank_values=True)
                redacted_pairs = []
                for key, value in pairs:
                    if is_sensitive_name(key):
                        redacted_pairs.append((key, REDACTED))
                    else:
                        redacted_pairs.append((key, value))
                redacted_text = urlencode(redacted_pairs)
            except ValueError:
                # Not a parseable form; keep the placeholder set above.
                pass

    elif media_type.startswith("multipart/"):
        redacted_text = "{} multipart body: {} bytes".format(REDACTED, size)

    if redacted_text is None:
        return body

    if is_bytes:
        return redacted_text.encode("utf-8")

    return redacted_text
