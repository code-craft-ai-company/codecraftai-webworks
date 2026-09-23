"""
.. module:: multipart
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: ``multipart/form-data`` parser implemented on the
        Python standard library.

.. moduleauthor:: Code Craft AI LLC

This module provides :func:`parse_multipart`, a stdlib-only parser
for ``multipart/form-data`` request bodies. It powers
:meth:`Request.form` and :meth:`Request.files` for HTTP requests
that carry file uploads (typically Twine / Poetry package publish,
HTML form file uploads, etc.) without webworks consumers needing
to depend on ``werkzeug.formparser`` or ``python-multipart``.

The parsing strategy is pragmatic:

  * The request's ``Content-Type`` header is parsed with
    :func:`parse_options_header` to extract the boundary parameter.
  * The body bytes are wrapped in a synthesised email-message header
    and handed to :class:`email.parser.BytesParser`. Python's email
    machinery is the most thoroughly tested multipart implementation
    in the stdlib; HTTP and email share the same RFC 2046 multipart
    framing, so the parser produces the same parts.
  * Each parsed part's ``Content-Disposition`` header determines
    whether the part is a regular form field (no ``filename``) or an
    uploaded file (has ``filename``).

The implementation is in-memory — the entire request body is
materialised before parsing. That trades memory for simplicity.
For the use cases webworks is targeting today (package publish
endpoints capped at low-tens of MB) this is fine; streaming
support is a future PR if a consumer needs uploads in the
hundreds-of-MB range.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []


import logging
import os
import re
import unicodedata

from dataclasses import dataclass, field
from email.parser import BytesParser
from email.policy import default as _default_email_policy
from typing import Dict, List, Tuple


# Module-level logger. ``parse_multipart`` returns an empty result
# rather than raising on parser failure (so a malformed upload
# becomes "no fields" instead of a 500), but the operator wants the
# breadcrumb in the journal so a sudden surge of empty parses isn't
# silently shrugged off as "the client sent nothing".
logger = logging.getLogger(__name__)


# Characters allowed in a "safe" filename. Everything else is
# stripped to defang directory traversal, control characters, and
# shell metacharacters in one pass.
_FILENAME_SAFE_CHARS_RE: re.Pattern = re.compile(r"[^A-Za-z0-9_.-]")


# Reserved Windows device names that must not appear as file names
# (or the prefix-before-extension of one). Falsy on POSIX hosts —
# the check is platform-aware so the behaviour matches what
# ``werkzeug.utils.secure_filename`` produces.
_WINDOWS_DEVICE_FILES: frozenset = frozenset(
    {
        "CON", "PRN", "AUX", "NUL",
        "COM1", "COM2", "COM3", "COM4", "COM5",
        "COM6", "COM7", "COM8", "COM9",
        "LPT1", "LPT2", "LPT3", "LPT4", "LPT5",
        "LPT6", "LPT7", "LPT8", "LPT9",
    }
)


def secure_filename(filename: str) -> str:
    """
        Return a version of *filename* that is safe to use as part of
        an on-disk path.

        Replacement for ``werkzeug.utils.secure_filename``. Behaviour
        matches werkzeug's:

          * Unicode is NFKD-normalised and stripped to ASCII so
            characters that look like ``.``/``/`` but aren't can't
            sneak through.
          * OS path separators (``/``, plus ``\\`` and the platform
            ``altsep``) are replaced with whitespace, then collapsed
            to a single ``_``.
          * Anything outside ``[A-Za-z0-9_.-]`` is dropped.
          * Leading and trailing ``.`` / ``_`` characters are
            stripped — protects against hidden files
            (``.htaccess``-style) and against the empty-after-strip
            edge case below.
          * On Windows hosts, names whose extension-less prefix
            matches a reserved device (``CON``, ``PRN``, ``COM1``, …)
            are prefixed with ``_`` so the OS doesn't open the
            device handle when the file is later created.
          * Returns the empty string when nothing useful survives.
            Callers should treat ``""`` as "supply a different name"
            rather than writing it to disk.

        :param filename: The user-supplied filename to sanitise.

        :returns: A filename safe to join with a fixed directory
                  prefix. Will not contain path separators, parent-
                  directory traversal sequences, or non-ASCII
                  characters.
    """
    if filename is None:
        return ""

    text = str(filename)
    if text == "":
        return ""

    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")

    separators = [os.sep]
    if os.path.altsep is not None:
        separators.append(os.path.altsep)
    separators.append("/")

    for sep in separators:
        if sep != "":
            text = text.replace(sep, " ")

    collapsed = "_".join(text.split())
    stripped = _FILENAME_SAFE_CHARS_RE.sub("", collapsed)
    stripped = stripped.strip("._")

    if (
        os.name == "nt"
        and stripped != ""
        and stripped.split(".")[0].upper() in _WINDOWS_DEVICE_FILES
    ):
        stripped = "_" + stripped

    rtnval = stripped
    return rtnval


@dataclass
class UploadedFile:
    """
        A single file part parsed out of a ``multipart/form-data``
        body.

        :param name: The form-field name supplied by the client (the
                     ``name`` parameter of the ``Content-Disposition``
                     header). Multiple parts may share the same
                     name; consumers that care should pull the raw
                     parts list rather than the by-name dict.
        :param filename: The original filename the client supplied.
                         May be empty when the client did not send
                         a ``filename`` parameter. Always treat as
                         untrusted input and pass through
                         :func:`ccai.webworks.utils.filenames.secure_filename`
                         before using it as an on-disk path.
        :param content_type: The ``Content-Type`` of the part, or
                             ``"application/octet-stream"`` when the
                             client did not declare one.
        :param content: The raw bytes of the part. Decoding is the
                        consumer's responsibility — uploads are
                        typically binary blobs.
    """

    name: str
    filename: str
    content_type: str
    content: bytes

    def save(self, destination_path: str) -> int:
        """
            Write the part's bytes to *destination_path*.

            The destination directory must already exist; this method
            does not create intermediate directories. Returns the
            number of bytes written.

            :param destination_path: Absolute filesystem path to
                                     write to.

            :returns: The number of bytes written.
        """
        with open(destination_path, "wb") as fh:
            fh.write(self.content)

        rtnval = len(self.content)
        return rtnval


@dataclass
class MultipartResult:
    """
        Output of :func:`parse_multipart`.

        :param form: Single-valued form fields. When a field appears
                     more than once, the last occurrence wins. For
                     full multi-value access, walk
                     :attr:`form_parts`.
        :param files: Uploaded files keyed by the form-field name.
                      When a name appears more than once, the last
                      occurrence wins. For full multi-value access,
                      walk :attr:`file_parts`.
        :param form_parts: Every form-field part in the order it
                           appeared in the body. Useful for callers
                           that need duplicate-name semantics.
        :param file_parts: Every file part in the order it appeared
                           in the body.
    """

    form: Dict[str, str] = field(default_factory=dict)
    files: Dict[str, UploadedFile] = field(default_factory=dict)
    form_parts: List[Tuple[str, str]] = field(default_factory=list)
    file_parts: List[UploadedFile] = field(default_factory=list)


def parse_options_header(header_value: str) -> Tuple[str, Dict[str, str]]:
    """
        Parse a header value of the form ``main; key1=val1; key2=val2``
        into a ``(main, params)`` tuple.

        Replaces the equivalent ``werkzeug.http.parse_options_header``
        call. Tolerates quoted values (``key="some value"``), values
        with embedded ``;`` inside quotes, and surrounding whitespace.

        :param header_value: The raw header value string.

        :returns: A tuple of ``(main_value, params_dict)``. The main
                  value is lowercased so callers can compare against
                  a literal lowercase MIME type
                  (``"multipart/form-data"``). Param keys are
                  lowercased; param values keep their original case.
    """
    if header_value is None:
        return "", {}

    text = str(header_value).strip()
    if text == "":
        return "", {}

    segments: List[str] = []
    current: List[str] = []
    in_quotes = False

    for ch in text:
        if ch == '"':
            in_quotes = not in_quotes
            current.append(ch)
            continue
        if ch == ";" and not in_quotes:
            segments.append("".join(current).strip())
            current = []
            continue
        current.append(ch)

    if len(current) > 0:
        segments.append("".join(current).strip())

    if len(segments) == 0:
        return "", {}

    main_value = segments[0].lower()
    params: Dict[str, str] = {}

    for segment in segments[1:]:
        if "=" not in segment:
            continue
        key, _, value = segment.partition("=")
        key_clean = key.strip().lower()
        if key_clean == "":
            continue
        value_clean = value.strip()
        if len(value_clean) >= 2 and value_clean[0] == '"' and value_clean[-1] == '"':
            value_clean = value_clean[1:-1]
        params[key_clean] = value_clean

    rtnval = (main_value, params)
    return rtnval


def parse_multipart(
    body: bytes,
    content_type: str,
) -> MultipartResult:
    """
        Parse a ``multipart/form-data`` request body.

        Raises no exceptions on malformed input — instead, an empty
        :class:`MultipartResult` is returned so callers can treat
        a missing / corrupt upload as "no data" without wrapping
        the call in a try/except.

        :param body: The raw HTTP request body.
        :param content_type: The full ``Content-Type`` header value
                             — including the ``boundary`` parameter.

        :returns: A :class:`MultipartResult` carrying the parsed
                  form fields and uploaded files.
    """
    if not isinstance(body, (bytes, bytearray)):
        return MultipartResult()

    main_type, params = parse_options_header(content_type or "")
    if main_type != "multipart/form-data":
        return MultipartResult()

    boundary = params.get("boundary", "")
    if boundary == "":
        return MultipartResult()

    # The email parser consumes a complete RFC 5322 message:
    # ``Content-Type`` header (declaring the boundary), blank line,
    # then the multipart body. Synthesise that wrapper here so the
    # raw HTTP request body becomes a parseable email message. The
    # ``Content-Type`` header is reproduced verbatim so the parser
    # picks up the same boundary the client used.
    header_bytes = "Content-Type: {}\r\n\r\n".format(content_type).encode("latin-1")
    message_bytes = header_bytes + bytes(body)

    try:
        message = BytesParser(policy=_default_email_policy).parsebytes(message_bytes)
    except Exception as exc:
        logger.warning(
            "parse_multipart: BytesParser failed (boundary=%r): %s",
            boundary,
            exc,
        )
        return MultipartResult()

    if not message.is_multipart():
        return MultipartResult()

    result = MultipartResult()

    for part in message.iter_parts():
        disposition_header = part.get("Content-Disposition", "")
        disposition_main, disposition_params = parse_options_header(
            str(disposition_header)
        )

        if disposition_main != "form-data":
            continue

        field_name = disposition_params.get("name", "")
        if field_name == "":
            continue

        filename = disposition_params.get("filename", "")

        part_content_type = str(part.get("Content-Type", "")).strip()
        part_content_main, _part_content_params = parse_options_header(part_content_type)

        if filename == "":
            # Regular form field — surface as a string.
            payload = part.get_payload(decode=True)
            if payload is None:
                payload_bytes: bytes = b""
            else:
                payload_bytes = bytes(payload)

            charset = part.get_content_charset(failobj="utf-8")
            try:
                value_text = payload_bytes.decode(charset, errors="replace")
            except (LookupError, UnicodeDecodeError):
                value_text = payload_bytes.decode("utf-8", errors="replace")

            result.form[field_name] = value_text
            result.form_parts.append((field_name, value_text))
            continue

        # File upload.
        payload = part.get_payload(decode=True)
        if payload is None:
            file_content: bytes = b""
        else:
            file_content = bytes(payload)

        if part_content_main == "":
            file_content_type = "application/octet-stream"
        else:
            file_content_type = part_content_main

        upload = UploadedFile(
            name=field_name,
            filename=filename,
            content_type=file_content_type,
            content=file_content,
        )

        result.files[field_name] = upload
        result.file_parts.append(upload)

    return result


__all__ = [
    "MultipartResult",
    "UploadedFile",
    "parse_multipart",
    "parse_options_header",
    "secure_filename",
]
