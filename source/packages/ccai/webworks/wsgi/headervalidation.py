"""
    Response header validation module for the WSGI layer.

    This module provides the checks that are applied to a response status and to
    response header names and values before they are written to a client. A value
    that contains a carriage return or a line feed ends the header it is written
    in, so whoever controls the value could add headers or a whole second response
    (HTTP response splitting). Such values are refused, they are never repaired.
"""

import re
from typing import Any, List, Tuple

from ccai.webworks.wsgi.exceptions import InvalidResponseHeader


# A header field name is an HTTP token (RFC 7230 section 3.2.6)
HEADER_NAME_PATTERN = re.compile(r"[!#$%&'*+\-.^_`|~0-9A-Za-z]+")

# Control characters are not allowed in a header value or a reason phrase.
# Horizontal tab is the one exception the grammar makes.
FORBIDDEN_VALUE_PATTERN = re.compile(r"[\x00-\x08\x0a-\x1f\x7f]")

# A WSGI status is a three digit code, optionally followed by a space and a reason phrase
STATUS_PATTERN = re.compile(r"[0-9]{3}( .*)?")


def validate_header_name(name: Any) -> None:
    """
        Check that a response header name is safe to write.

        :param name: Header name to check.

        :raises: InvalidResponseHeader if the name is not a string or is not an HTTP token.
    """
    if not isinstance(name, str):
        errmsg = f"header name must be a string, got {type(name).__name__}"
        raise InvalidResponseHeader(errmsg)

    if HEADER_NAME_PATTERN.fullmatch(name) is None:
        errmsg = f"header name {name!r} is not a valid HTTP token"
        raise InvalidResponseHeader(errmsg)

    return


def validate_header_value(name: Any, value: Any) -> None:
    """
        Check that a response header value is safe to write.

        :param name: Name of the header, used in the error message.
        :param value: Header value to check.

        :raises: InvalidResponseHeader if the value is not a string, contains a control
                 character such as CR, LF or NUL, or cannot be encoded as latin-1.
    """
    if not isinstance(value, str):
        errmsg = f"value of header {name!r} must be a string, got {type(value).__name__}"
        raise InvalidResponseHeader(errmsg)

    if FORBIDDEN_VALUE_PATTERN.search(value) is not None:
        errmsg = f"value of header {name!r} contains a control character"
        raise InvalidResponseHeader(errmsg)

    try:
        value.encode("latin-1")
    except UnicodeEncodeError as encode_err:
        errmsg = f"value of header {name!r} cannot be encoded as latin-1"
        raise InvalidResponseHeader(errmsg) from encode_err

    return


def validate_headers(headers: List[Tuple[str, str]]) -> None:
    """
        Check that every response header in a list is safe to write.

        :param headers: List of (name, value) header tuples.

        :raises: InvalidResponseHeader if a name or a value is not safe to write.
    """
    for header in headers:
        if len(header) != 2:
            errmsg = f"header must be a (name, value) pair, got {header!r}"
            raise InvalidResponseHeader(errmsg)

        name, value = header
        validate_header_name(name)
        validate_header_value(name, value)

    return


def validate_reason_phrase(reason: Any) -> None:
    """
        Check that a reason phrase is safe to write in a status line.

        :param reason: Reason phrase to check.

        :raises: InvalidResponseHeader if the phrase is not a string, contains a control
                 character or cannot be encoded as latin-1.
    """
    if not isinstance(reason, str):
        errmsg = f"reason phrase must be a string, got {type(reason).__name__}"
        raise InvalidResponseHeader(errmsg)

    if FORBIDDEN_VALUE_PATTERN.search(reason) is not None:
        errmsg = "reason phrase contains a control character"
        raise InvalidResponseHeader(errmsg)

    try:
        reason.encode("latin-1")
    except UnicodeEncodeError as encode_err:
        errmsg = "reason phrase cannot be encoded as latin-1"
        raise InvalidResponseHeader(errmsg) from encode_err

    return


def validate_status(status: Any) -> None:
    """
        Check that a WSGI status string is safe to write as a status line.

        :param status: Status string such as "200 OK".

        :raises: InvalidResponseHeader if the status is not a string, does not start with
                 a three digit code or contains a control character.
    """
    if not isinstance(status, str):
        errmsg = f"status must be a string, got {type(status).__name__}"
        raise InvalidResponseHeader(errmsg)

    if FORBIDDEN_VALUE_PATTERN.search(status) is not None:
        errmsg = "status contains a control character"
        raise InvalidResponseHeader(errmsg)

    if STATUS_PATTERN.fullmatch(status) is None:
        errmsg = f"status {status!r} must be a three digit code followed by a reason phrase"
        raise InvalidResponseHeader(errmsg)

    try:
        status.encode("latin-1")
    except UnicodeEncodeError as encode_err:
        errmsg = "status cannot be encoded as latin-1"
        raise InvalidResponseHeader(errmsg) from encode_err

    return
