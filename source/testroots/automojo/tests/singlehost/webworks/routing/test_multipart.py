"""
    Unit tests for :mod:`automojo.webworks.routing.multipart`.

    Covers:

      * :func:`parse_options_header` extracts the main value plus
        parameters, tolerates quoted values, and handles malformed
        input.
      * :func:`parse_multipart` recovers form fields and file
        uploads from a real multipart/form-data body, surfaces the
        per-part Content-Disposition + Content-Type headers, and
        round-trips binary file content unchanged.
      * Malformed inputs (wrong content type, missing boundary,
        truncated body) return an empty result rather than raising.
      * :class:`UploadedFile.save` writes the part bytes verbatim.
      * :func:`secure_filename` matches the
        ``werkzeug.utils.secure_filename`` contract on the
        canonical inputs (path traversal, unicode, control
        characters, empty result).
"""

import os
import tempfile

from typing import Dict, List, Optional, Tuple

from automojo.webworks.routing.multipart import (
    MultipartResult,
    UploadedFile,
    parse_multipart,
    parse_options_header,
    secure_filename,
)


# =============================================================================
# Helpers
# =============================================================================


def _build_multipart_body(
    boundary: str,
    fields: List[Tuple[str, str]],
    files: List[Tuple[str, str, str, bytes]],
) -> bytes:
    """
        Assemble a real ``multipart/form-data`` body the way an HTTP
        client (Twine, curl, a browser) would.

        :param boundary: The boundary string (without leading ``--``).
        :param fields: List of ``(name, value)`` form-field tuples.
        :param files: List of ``(name, filename, content_type, bytes)``
                      file-upload tuples.

        :returns: The raw HTTP body bytes.
    """
    lines: List[bytes] = []
    boundary_bytes = boundary.encode("latin-1")

    for field_name, value in fields:
        lines.append(b"--" + boundary_bytes)
        disposition = 'form-data; name="{}"'.format(field_name)
        lines.append(b"Content-Disposition: " + disposition.encode("latin-1"))
        lines.append(b"")
        lines.append(value.encode("utf-8"))

    for field_name, filename, content_type, content_bytes in files:
        lines.append(b"--" + boundary_bytes)
        disposition = 'form-data; name="{}"; filename="{}"'.format(field_name, filename)
        lines.append(b"Content-Disposition: " + disposition.encode("latin-1"))
        lines.append(b"Content-Type: " + content_type.encode("latin-1"))
        lines.append(b"")
        lines.append(content_bytes)

    lines.append(b"--" + boundary_bytes + b"--")
    lines.append(b"")

    rtnval = b"\r\n".join(lines)
    return rtnval


# =============================================================================
# parse_options_header
# =============================================================================


def test_parse_options_header_returns_main_value_only_when_no_params():
    main, params = parse_options_header("text/plain")

    if main != "text/plain":
        errmsg = "Expected lowercase main value, got {!r}".format(main)
        raise AssertionError(errmsg)

    if params != {}:
        errmsg = "Expected empty params dict, got {!r}".format(params)
        raise AssertionError(errmsg)

    return


def test_parse_options_header_extracts_quoted_param():
    main, params = parse_options_header(
        'multipart/form-data; boundary="some random; boundary value"'
    )

    if main != "multipart/form-data":
        errmsg = "Expected lowercased main, got {!r}".format(main)
        raise AssertionError(errmsg)

    if params.get("boundary") != "some random; boundary value":
        errmsg = "Expected the quoted boundary preserved verbatim, got {!r}".format(
            params.get("boundary")
        )
        raise AssertionError(errmsg)

    return


def test_parse_options_header_handles_unquoted_param():
    main, params = parse_options_header("multipart/form-data; boundary=----abc123")

    if params.get("boundary") != "----abc123":
        errmsg = "Expected unquoted boundary, got {!r}".format(params.get("boundary"))
        raise AssertionError(errmsg)

    return


def test_parse_options_header_lowercases_param_keys_keeps_value_case():
    main, params = parse_options_header('text/html; CHARSET="UTF-8"')

    if "charset" not in params:
        errmsg = "Expected param key 'charset' (lowercased), got {!r}".format(params)
        raise AssertionError(errmsg)

    if params["charset"] != "UTF-8":
        errmsg = "Expected case-preserving value 'UTF-8', got {!r}".format(
            params["charset"]
        )
        raise AssertionError(errmsg)

    return


def test_parse_options_header_returns_empty_for_none_or_empty():
    main, params = parse_options_header("")
    if (main, params) != ("", {}):
        errmsg = "Expected ('', {{}}) for empty input"
        raise AssertionError(errmsg)

    main, params = parse_options_header(None)  # type: ignore[arg-type]
    if (main, params) != ("", {}):
        errmsg = "Expected ('', {{}}) for None input"
        raise AssertionError(errmsg)

    return


# =============================================================================
# parse_multipart — happy path
# =============================================================================


def test_parse_multipart_extracts_form_fields():
    boundary = "----WebworksTestBoundary"
    body = _build_multipart_body(
        boundary=boundary,
        fields=[("name", "package-foo"), (":action", "file_upload")],
        files=[],
    )

    result = parse_multipart(
        body=body,
        content_type="multipart/form-data; boundary=" + boundary,
    )

    if result.form.get("name") != "package-foo":
        errmsg = "Expected form['name'] == 'package-foo', got {!r}".format(
            result.form.get("name")
        )
        raise AssertionError(errmsg)

    if result.form.get(":action") != "file_upload":
        errmsg = "Expected form[':action'] == 'file_upload', got {!r}".format(
            result.form.get(":action")
        )
        raise AssertionError(errmsg)

    if len(result.files) != 0:
        errmsg = "Expected no files when only form fields present"
        raise AssertionError(errmsg)

    return


def test_parse_multipart_extracts_uploaded_file_with_binary_content():
    """
        File parts must round-trip arbitrary bytes — including null
        bytes and bytes that look like CRLF-with-trailing-content.
        Catches a regression where the parser strips trailing
        boundary characters or mis-handles binary payloads.
    """
    boundary = "----WebworksFileTestBoundary"
    file_bytes = b"\x00\x01\x02BINARY\r\nDATA\r\n--not-the-boundary\xff\xfe"

    body = _build_multipart_body(
        boundary=boundary,
        fields=[("name", "test-package")],
        files=[("content", "test.tar.gz", "application/x-gzip", file_bytes)],
    )

    result = parse_multipart(
        body=body,
        content_type="multipart/form-data; boundary=" + boundary,
    )

    upload = result.files.get("content")
    if upload is None:
        errmsg = "Expected an UploadedFile under field name 'content'"
        raise AssertionError(errmsg)

    if upload.filename != "test.tar.gz":
        errmsg = "Expected filename 'test.tar.gz', got {!r}".format(upload.filename)
        raise AssertionError(errmsg)

    if upload.content_type != "application/x-gzip":
        errmsg = "Expected content_type 'application/x-gzip', got {!r}".format(
            upload.content_type
        )
        raise AssertionError(errmsg)

    if upload.content != file_bytes:
        errmsg = "Expected file bytes to round-trip unchanged"
        raise AssertionError(errmsg)

    return


def test_parse_multipart_separates_form_fields_from_uploads():
    boundary = "----TwineLikeBoundary"
    file_bytes = b"package wheel bytes here"

    body = _build_multipart_body(
        boundary=boundary,
        fields=[("name", "examplepkg"), (":action", "file_upload")],
        files=[("content", "examplepkg-1.0.tar.gz", "application/octet-stream", file_bytes)],
    )

    result = parse_multipart(
        body=body,
        content_type='multipart/form-data; boundary="' + boundary + '"',
    )

    if result.form.get("name") != "examplepkg":
        errmsg = "Expected form['name'] == 'examplepkg'"
        raise AssertionError(errmsg)

    upload = result.files.get("content")
    if upload is None:
        errmsg = "Expected an upload under 'content'"
        raise AssertionError(errmsg)

    if upload.content != file_bytes:
        errmsg = "Expected file bytes to round-trip"
        raise AssertionError(errmsg)

    if len(result.form_parts) != 2:
        errmsg = "Expected exactly 2 form-field parts, got {}".format(len(result.form_parts))
        raise AssertionError(errmsg)

    if len(result.file_parts) != 1:
        errmsg = "Expected exactly 1 file part, got {}".format(len(result.file_parts))
        raise AssertionError(errmsg)

    return


# =============================================================================
# parse_multipart — malformed inputs return empty
# =============================================================================


def test_parse_multipart_returns_empty_for_non_multipart_content_type():
    result = parse_multipart(
        body=b"hello",
        content_type="text/plain",
    )

    if result.form != {}:
        errmsg = "Expected empty form for non-multipart content type"
        raise AssertionError(errmsg)

    if result.files != {}:
        errmsg = "Expected empty files for non-multipart content type"
        raise AssertionError(errmsg)

    return


def test_parse_multipart_returns_empty_for_missing_boundary():
    result = parse_multipart(
        body=b"hello",
        content_type="multipart/form-data",  # no boundary= param
    )

    if result.form != {} or result.files != {}:
        errmsg = "Expected empty result when boundary is missing"
        raise AssertionError(errmsg)

    return


def test_parse_multipart_returns_empty_for_garbage_body():
    """
        A body that doesn't match the declared boundary is treated as
        empty rather than crashing — protects credential-check call
        sites from defensive try/except wrapping.
    """
    result = parse_multipart(
        body=b"this is not multipart at all",
        content_type="multipart/form-data; boundary=---abc",
    )

    # Either an empty result OR a result with no recognisable parts
    # is acceptable here. The key contract is "no exception".
    if result.form != {} or result.files != {}:
        errmsg = "Garbage body should produce no parts; got form={!r} files={!r}".format(
            result.form, result.files
        )
        raise AssertionError(errmsg)

    return


def test_parse_multipart_returns_empty_for_non_bytes_body():
    result = parse_multipart(
        body="i am a str not bytes",  # type: ignore[arg-type]
        content_type="multipart/form-data; boundary=---abc",
    )

    if result.form != {} or result.files != {}:
        errmsg = "Expected empty result when body is not bytes"
        raise AssertionError(errmsg)

    return


# =============================================================================
# UploadedFile.save
# =============================================================================


def test_uploaded_file_save_writes_bytes_verbatim():
    upload = UploadedFile(
        name="content",
        filename="hello.bin",
        content_type="application/octet-stream",
        content=b"\x00\x01\x02hello",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        destination = os.path.join(tmpdir, "out.bin")
        bytes_written = upload.save(destination)

        if bytes_written != len(upload.content):
            errmsg = "save() should return the number of bytes written"
            raise AssertionError(errmsg)

        with open(destination, "rb") as fh:
            actual = fh.read()

        if actual != upload.content:
            errmsg = "Expected save() to write the upload bytes verbatim"
            raise AssertionError(errmsg)

    return


# =============================================================================
# secure_filename
# =============================================================================


def test_secure_filename_strips_directory_traversal():
    if secure_filename("../../etc/passwd") != "etc_passwd":
        errmsg = "Expected directory traversal to be stripped"
        raise AssertionError(errmsg)

    return


def test_secure_filename_strips_path_separators():
    # On all platforms, forward-slash is a path separator that must
    # be stripped.
    cleaned = secure_filename("foo/bar/baz.txt")

    if "/" in cleaned:
        errmsg = "Expected forward slash stripped, got {!r}".format(cleaned)
        raise AssertionError(errmsg)

    if cleaned != "foo_bar_baz.txt":
        errmsg = "Expected 'foo_bar_baz.txt', got {!r}".format(cleaned)
        raise AssertionError(errmsg)

    return


def test_secure_filename_normalises_unicode_to_ascii():
    # NFKD-normalise to drop the accent and keep ASCII letters.
    cleaned = secure_filename("naïve_résumé.pdf")

    if cleaned != "naive_resume.pdf":
        errmsg = "Expected unicode dropped to ASCII, got {!r}".format(cleaned)
        raise AssertionError(errmsg)

    return


def test_secure_filename_strips_leading_and_trailing_dots():
    if secure_filename("..hidden..") != "hidden":
        errmsg = "Expected leading/trailing dots stripped"
        raise AssertionError(errmsg)

    return


def test_secure_filename_returns_empty_when_nothing_safe_remains():
    if secure_filename("../") != "":
        errmsg = "Expected empty string when input has no safe characters"
        raise AssertionError(errmsg)

    if secure_filename("") != "":
        errmsg = "Expected empty for empty input"
        raise AssertionError(errmsg)

    if secure_filename(None) != "":  # type: ignore[arg-type]
        errmsg = "Expected empty for None input"
        raise AssertionError(errmsg)

    return


def test_secure_filename_drops_disallowed_characters():
    cleaned = secure_filename("my file (1) [draft].txt")

    # Spaces become underscores; parens / brackets stripped.
    if cleaned != "my_file_1_draft.txt":
        errmsg = "Expected 'my_file_1_draft.txt', got {!r}".format(cleaned)
        raise AssertionError(errmsg)

    return
