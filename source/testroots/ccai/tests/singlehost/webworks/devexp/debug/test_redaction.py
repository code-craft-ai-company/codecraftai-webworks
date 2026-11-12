"""
    Tests for credential redaction in the debug tooling.

    This module contains unit tests for deciding which names mark a
    credential and for masking headers, parsed data and request bodies.
"""

import json

from ccai.webworks.devexp.debug.redaction import REDACTED
from ccai.webworks.devexp.debug.redaction import is_sensitive_name
from ccai.webworks.devexp.debug.redaction import redact_body
from ccai.webworks.devexp.debug.redaction import redact_data
from ccai.webworks.devexp.debug.redaction import redact_headers


# =============================================================================
# Unit Tests for is_sensitive_name
# =============================================================================

def test_is_sensitive_name_recognises_credential_names():
    """
        Test that names of credentials are recognised in the spellings
        that occur in headers, form fields, JSON keys and variables.
    """
    sensitive_names = [
        "password", "Password", "user_password", "passwd", "secret", "client_secret",
        "token", "access_token", "accessToken", "Authorization", "Cookie", "Set-Cookie",
        "api_key", "apiKey", "API-KEY", "X-Api-Key", "key", "private_key",
        "session", "session_id", "csrf", "pin", "credentials",
    ]

    for name in sensitive_names:
        if is_sensitive_name(name) is not True:
            errmsg = "Expected '{}' to be recognised as a credential name.".format(name)
            raise AssertionError(errmsg)

    return


def test_is_sensitive_name_leaves_ordinary_names():
    """
        Test that names that merely contain a short credential word as
        part of another word are not masked.
    """
    ordinary_names = [
        "username", "email", "keyboard", "monkey", "spinner", "pinned", "author",
        "Content-Type", "User-Agent", "Accept", "Host", "path", "count", "passenger",
    ]

    for name in ordinary_names:
        if is_sensitive_name(name) is not False:
            errmsg = "Did not expect '{}' to be treated as a credential name.".format(name)
            raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for redact_headers
# =============================================================================

def test_redact_headers_masks_credentials_and_keeps_the_rest():
    """
        Test that credential header values are masked and other headers
        are returned unchanged.
    """
    headers = {
        "Authorization": "Bearer abc.def",
        "Cookie": "session=xyz",
        "X-Api-Key": "k-1",
        "Accept": "application/json",
    }

    redacted = redact_headers(headers)

    if redacted["Authorization"] != "Bearer {}".format(REDACTED):
        errmsg = "Expected the scheme to be kept and the credential masked, got '{}'".format(
            redacted["Authorization"]
        )
        raise AssertionError(errmsg)

    if redacted["Cookie"] != REDACTED or redacted["X-Api-Key"] != REDACTED:
        errmsg = "Expected Cookie and X-Api-Key to be masked, got {}".format(redacted)
        raise AssertionError(errmsg)

    if redacted["Accept"] != "application/json":
        errmsg = "Expected Accept to be unchanged, got '{}'".format(redacted["Accept"])
        raise AssertionError(errmsg)

    return


def test_redact_headers_does_not_modify_its_input():
    """
        Test that the header mapping passed in is left as it was.
    """
    headers = {"Authorization": "Basic dXNlcjpwYXNz"}

    redact_headers(headers)

    if headers["Authorization"] != "Basic dXNlcjpwYXNz":
        errmsg = "The input headers were modified: {}".format(headers)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for redact_data
# =============================================================================

def test_redact_data_masks_nested_credential_fields():
    """
        Test that credential fields are masked at any depth, including
        inside lists.
    """
    data = {
        "user": {"name": "alice", "password": "p1"},
        "tokens": [{"access_token": "t1", "scope": "read"}],
        "count": 2,
    }

    redacted = redact_data(data)

    expected = {
        "user": {"name": "alice", "password": REDACTED},
        "tokens": REDACTED,
        "count": 2,
    }

    if redacted != expected:
        errmsg = "Unexpected redaction result: {}".format(redacted)
        raise AssertionError(errmsg)

    return


def test_redact_data_walks_lists_of_dictionaries():
    """
        Test that dictionaries inside a list under an ordinary key are
        redacted field by field.
    """
    data = {"entries": [{"label": "a", "secret": "s1"}, {"label": "b", "secret": "s2"}]}

    redacted = redact_data(data)

    expected = {"entries": [{"label": "a", "secret": REDACTED}, {"label": "b", "secret": REDACTED}]}

    if redacted != expected:
        errmsg = "Unexpected redaction result: {}".format(redacted)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for redact_body
# =============================================================================

def test_redact_body_masks_json_fields():
    """
        Test that credential fields of a JSON body are masked and the
        result is still JSON of the same type as the input.
    """
    body = json.dumps({"username": "alice", "password": "hunter2"}).encode("utf-8")

    redacted = redact_body(body, "application/json; charset=utf-8")

    if not isinstance(redacted, bytes):
        errmsg = "Expected bytes back for a bytes body, got {}".format(type(redacted).__name__)
        raise AssertionError(errmsg)

    if json.loads(redacted) != {"username": "alice", "password": REDACTED}:
        errmsg = "Unexpected redacted JSON body: {!r}".format(redacted)
        raise AssertionError(errmsg)

    return


def test_redact_body_masks_form_fields():
    """
        Test that credential fields of a URL-encoded form body are masked.
    """
    redacted = redact_body("username=alice&password=hunter2", "application/x-www-form-urlencoded")

    if "hunter2" in redacted or "username=alice" not in redacted:
        errmsg = "Unexpected redacted form body: {!r}".format(redacted)
        raise AssertionError(errmsg)

    return


def test_redact_body_replaces_multipart_body():
    """
        Test that a multipart body is replaced by a note of its size.
    """
    body = b"--b\r\nContent-Disposition: form-data; name=\"password\"\r\n\r\nhunter2\r\n--b--\r\n"

    redacted = redact_body(body, "multipart/form-data; boundary=b")

    if b"hunter2" in redacted:
        errmsg = "The multipart body was not replaced: {!r}".format(redacted)
        raise AssertionError(errmsg)

    return


def test_redact_body_replaces_unparseable_json():
    """
        Test that a body that claims to be JSON but is not is replaced,
        because it cannot be redacted by field.
    """
    redacted = redact_body(b'{"password": "hunter2"', "application/json")

    if b"hunter2" in redacted:
        errmsg = "The unparseable JSON body was not replaced: {!r}".format(redacted)
        raise AssertionError(errmsg)

    return


def test_redact_body_leaves_other_content_types():
    """
        Test that a body of another content type is returned unchanged.
    """
    body = b"plain text content"

    redacted = redact_body(body, "text/plain")

    if redacted != body:
        errmsg = "Expected the body to be unchanged, got {!r}".format(redacted)
        raise AssertionError(errmsg)

    return
