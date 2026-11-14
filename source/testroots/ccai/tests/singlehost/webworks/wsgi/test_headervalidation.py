"""
    Tests for the response header validation of the WSGI layer.
    
    This module contains tests for the checks that keep a status or header that
    would split the response from being written.
"""

from ccai.webworks.wsgi.exceptions import InvalidResponseHeader
from ccai.webworks.wsgi.headervalidation import (
    validate_header_name,
    validate_header_value,
    validate_headers,
    validate_status,
)


def _raises_invalid_header(check, *args) -> bool:
    """
        Call a validation function and report whether it refused its input.
    """
    raised = False
    try:
        check(*args)
    except InvalidResponseHeader:
        raised = True
    return raised


def test_validate_header_value_rejects_carriage_return_line_feed():
    """
        Test that a header value with CRLF in it is refused.
    """
    if not _raises_invalid_header(validate_header_value, "Location", "/x\r\nSet-Cookie: sid=evil"):
        errmsg = "Expected InvalidResponseHeader for a value containing CRLF"
        raise AssertionError(errmsg)
    
    return


def test_validate_header_value_rejects_bare_line_feed():
    """
        Test that a header value with a line feed on its own is refused.
    """
    if not _raises_invalid_header(validate_header_value, "X-Test", "a\nb"):
        errmsg = "Expected InvalidResponseHeader for a value containing LF"
        raise AssertionError(errmsg)
    
    return


def test_validate_header_value_rejects_bare_carriage_return():
    """
        Test that a header value with a carriage return on its own is refused.
    """
    if not _raises_invalid_header(validate_header_value, "X-Test", "a\rb"):
        errmsg = "Expected InvalidResponseHeader for a value containing CR"
        raise AssertionError(errmsg)
    
    return


def test_validate_header_value_rejects_nul():
    """
        Test that a header value with a NUL character is refused.
    """
    if not _raises_invalid_header(validate_header_value, "X-Test", "a\x00b"):
        errmsg = "Expected InvalidResponseHeader for a value containing NUL"
        raise AssertionError(errmsg)
    
    return


def test_validate_header_value_rejects_non_string():
    """
        Test that a header value that is not a string is refused.
    """
    if not _raises_invalid_header(validate_header_value, "Content-Length", 5):
        errmsg = "Expected InvalidResponseHeader for a value that is not a string"
        raise AssertionError(errmsg)
    
    return


def test_validate_header_value_accepts_ordinary_value():
    """
        Test that an ordinary header value, including a tab, is accepted.
    """
    if _raises_invalid_header(validate_header_value, "Content-Type", "text/html;\tcharset=utf-8"):
        errmsg = "Expected an ordinary header value to be accepted"
        raise AssertionError(errmsg)
    
    return


def test_validate_header_name_rejects_name_with_colon_and_line_break():
    """
        Test that a header name that is not a token is refused.
    """
    if not _raises_invalid_header(validate_header_name, "X-A: 1\r\nX-B"):
        errmsg = "Expected InvalidResponseHeader for a name that is not a token"
        raise AssertionError(errmsg)
    
    return


def test_validate_header_name_rejects_trailing_line_feed():
    """
        Test that a header name ending in a line feed is refused.
    """
    if not _raises_invalid_header(validate_header_name, "X-A\n"):
        errmsg = "Expected InvalidResponseHeader for a name ending in LF"
        raise AssertionError(errmsg)
    
    return


def test_validate_header_name_rejects_empty_name():
    """
        Test that an empty header name is refused.
    """
    if not _raises_invalid_header(validate_header_name, ""):
        errmsg = "Expected InvalidResponseHeader for an empty name"
        raise AssertionError(errmsg)
    
    return


def test_validate_headers_accepts_ordinary_headers():
    """
        Test that a list of ordinary headers is accepted.
    """
    headers = [("Content-Type", "text/plain"), ("Set-Cookie", "a=1; Path=/"), ("X-Request-Id", "abc-123")]
    
    if _raises_invalid_header(validate_headers, headers):
        errmsg = "Expected ordinary headers to be accepted"
        raise AssertionError(errmsg)
    
    return


def test_validate_status_rejects_line_break():
    """
        Test that a status with a line break in the reason phrase is refused.
    """
    if not _raises_invalid_header(validate_status, "200 OK\r\nSet-Cookie: sid=evil"):
        errmsg = "Expected InvalidResponseHeader for a status containing CRLF"
        raise AssertionError(errmsg)
    
    return


def test_validate_status_rejects_missing_code():
    """
        Test that a status that does not start with a three digit code is refused.
    """
    if not _raises_invalid_header(validate_status, "OK"):
        errmsg = "Expected InvalidResponseHeader for a status without a code"
        raise AssertionError(errmsg)
    
    return


def test_validate_status_accepts_code_and_reason():
    """
        Test that an ordinary status string is accepted.
    """
    if _raises_invalid_header(validate_status, "404 Not Found"):
        errmsg = "Expected '404 Not Found' to be accepted"
        raise AssertionError(errmsg)
    
    return


def test_invalid_response_header_is_a_value_error():
    """
        Test that InvalidResponseHeader can be caught as ValueError.
    """
    raised = False
    try:
        validate_header_value("X-Test", "a\r\nb")
    except ValueError:
        raised = True
    
    if not raised:
        errmsg = "Expected InvalidResponseHeader to be a ValueError"
        raise AssertionError(errmsg)
    
    return
