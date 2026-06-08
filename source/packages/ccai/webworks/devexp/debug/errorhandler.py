"""
    Debug and production error handler for the webworks framework.

    This module provides the :class:`DebugErrorHandler` class that handles
    exceptions and generates appropriate error pages depending on the
    current mode. In debug mode, a detailed error page is rendered with
    stack traces, local variables, and request context. In production
    mode, a generic error page is rendered that hides internal details
    and includes an error reference ID for support purposes.

    The :class:`FrameInfo` dataclass captures information about a single
    stack frame including source context and local variables.
"""

import html
import logging
import os
import traceback
import uuid

from typing import Any, Dict, List, Optional, Tuple


logger = logging.getLogger(__name__)


# =============================================================================
# FrameInfo
# =============================================================================

class FrameInfo:
    """
        Information about a single stack frame.

        Captures the filename, line number, function name, surrounding
        source code lines, the index of the error line within the
        code context, and formatted local variables.

        :param filename: The source file path.
        :param lineno: The line number in the source file.
        :param function: The function or method name.
        :param code_context: Lines of source code around the error.
        :param highlight_line: Index of the error line in code_context.
        :param locals: Formatted local variables as name-value string pairs.
    """

    def __init__(
        self,
        filename: str,
        lineno: int,
        function: str,
        code_context: Optional[List[str]] = None,
        highlight_line: int = 0,
        locals: Optional[Dict[str, str]] = None,
    ):
        """
            Construct a FrameInfo.

            :param filename: The source file path.
            :param lineno: The line number in the source file.
            :param function: The function or method name.
            :param code_context: Lines of source code around the error.
            :param highlight_line: Index of the error line in code_context.
            :param locals: Formatted local variables as string pairs.
        """
        self._filename = filename
        self._lineno = lineno
        self._function = function
        self._code_context = list(code_context) if code_context is not None else []
        self._highlight_line = highlight_line
        self._locals = dict(locals) if locals is not None else {}
        return

    @property
    def filename(self) -> str:
        """
            The source file path.

            :returns: The filename string.
        """
        return self._filename

    @property
    def lineno(self) -> int:
        """
            The line number in the source file.

            :returns: The line number integer.
        """
        return self._lineno

    @property
    def function(self) -> str:
        """
            The function or method name.

            :returns: The function name string.
        """
        return self._function

    @property
    def code_context(self) -> List[str]:
        """
            Lines of source code around the error.

            :returns: A list of source code line strings.
        """
        return list(self._code_context)

    @property
    def highlight_line(self) -> int:
        """
            Index of the error line within code_context.

            :returns: The highlight line index.
        """
        return self._highlight_line

    @property
    def locals(self) -> Dict[str, str]:
        """
            Formatted local variables from the frame.

            :returns: A dictionary of variable name to string
                representation pairs.
        """
        return dict(self._locals)


# =============================================================================
# Constants
# =============================================================================

CONTEXT_LINES = 7
"""Number of source lines to show above and below the error line."""

DEFAULT_PRODUCTION_TITLE = "Server Error"
"""Default title for production error pages."""

DEFAULT_PRODUCTION_MESSAGE = "An unexpected error occurred. Please try again later."
"""Default user-friendly message for production error pages."""

STATUS_CODE_MESSAGES = {
    400: ("Bad Request", "The request could not be understood by the server."),
    403: ("Forbidden", "You do not have permission to access this resource."),
    404: ("Not Found", "The requested resource could not be found."),
    405: ("Method Not Allowed", "The request method is not supported for this resource."),
    408: ("Request Timeout", "The server timed out waiting for the request."),
    500: ("Internal Server Error", "An unexpected error occurred. Please try again later."),
    502: ("Bad Gateway", "The server received an invalid response from an upstream server."),
    503: ("Service Unavailable", "The server is temporarily unable to handle the request."),
}
"""Mapping of HTTP status codes to (title, message) tuples."""


# =============================================================================
# DebugErrorHandler
# =============================================================================

class DebugErrorHandler:
    """
        Handles exceptions and generates appropriate error pages.

        In debug mode, renders a detailed error page with stack traces,
        local variables, source context, and request information. In
        production mode, renders a generic error page that hides all
        internal details and includes an error reference ID.

        :param debug: Whether debug mode is enabled.
        :param interactive: Whether the interactive debugger is enabled.
        :param pin: Security PIN for the interactive debugger.
        :param template_path: Optional path to custom error page templates.
    """

    def __init__(
        self,
        debug: bool = False,
        interactive: bool = False,
        pin: Optional[str] = None,
        template_path: Optional[str] = None,
    ):
        """
            Construct a DebugErrorHandler.

            :param debug: Whether debug mode is enabled.
            :param interactive: Whether the interactive debugger is enabled.
            :param pin: Security PIN for the interactive debugger.
            :param template_path: Optional path to custom error page templates.
        """
        self._debug = debug
        self._interactive = interactive
        self._pin = pin
        self._template_path = template_path
        self._custom_templates: Dict[int, str] = {}
        return

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def debug(self) -> bool:
        """
            Whether debug mode is enabled.

            :returns: True if debug mode is active.
        """
        return self._debug

    @property
    def interactive(self) -> bool:
        """
            Whether the interactive debugger is enabled.

            :returns: True if interactive debugging is active.
        """
        return self._interactive

    @property
    def pin(self) -> Optional[str]:
        """
            The security PIN for the interactive debugger.

            :returns: The PIN string or None.
        """
        return self._pin

    @property
    def template_path(self) -> Optional[str]:
        """
            The path to custom error page templates.

            :returns: The template path string or None.
        """
        return self._template_path

    # -------------------------------------------------------------------------
    # Template Registration
    # -------------------------------------------------------------------------

    def register_template(self, status_code: int, template_content: str) -> None:
        """
            Register a custom error page template for a specific status code.

            :param status_code: The HTTP status code to associate with the template.
            :param template_content: The HTML template content string. The template
                may contain the placeholders ``{error_title}``, ``{error_message}``,
                ``{error_id}``, and ``{status_code}``.
        """
        self._custom_templates[status_code] = template_content
        return

    # -------------------------------------------------------------------------
    # Exception Handling
    # -------------------------------------------------------------------------

    def handle_exception(
        self,
        request: Any,
        exception: Exception,
        status_code: int = 500,
    ) -> Dict[str, Any]:
        """
            Handle an exception and return an appropriate error response.

            In debug mode, returns a detailed error page. In production
            mode, returns a generic error page and logs the full error
            details server-side.

            :param request: The request object or dictionary with request info.
            :param exception: The exception that was raised.
            :param status_code: The HTTP status code for the response.

            :returns: A dictionary with ``status_code``, ``headers``, and
                ``body`` keys.
        """
        if self._debug is True:
            body = self._render_debug_page(request, exception)
            response = {
                "status_code": status_code,
                "headers": {"Content-Type": "text/html; charset=utf-8"},
                "body": body,
            }
        else:
            error_id = str(uuid.uuid4())
            self._log_error(request, exception, error_id)
            body = self._render_production_page(
                request, exception, error_id, status_code=status_code,
            )
            response = {
                "status_code": status_code,
                "headers": {"Content-Type": "text/html; charset=utf-8"},
                "body": body,
            }

        return response

    # -------------------------------------------------------------------------
    # Debug Page Rendering
    # -------------------------------------------------------------------------

    def _render_debug_page(
        self,
        request: Any,
        exception: Exception,
    ) -> str:
        """
            Render the debug error page HTML.

            Extracts the traceback, local variables, and request
            information and formats them into a styled HTML page.

            :param request: The request object or dictionary.
            :param exception: The exception that was raised.

            :returns: The HTML string for the debug error page.
        """
        exc_type = type(exception).__name__
        exc_message = str(exception)
        frames = self._extract_traceback(exception)
        request_info = self._extract_request_info(request)

        html_parts = []
        html_parts.append(self._render_debug_header(exc_type, exc_message))
        html_parts.append(self._render_traceback_section(frames))
        html_parts.append(self._render_request_section(request_info))
        html_parts.append(self._render_debug_footer())

        page_html = "\n".join(html_parts)

        return page_html

    def _render_debug_header(self, exc_type: str, exc_message: str) -> str:
        """
            Render the header section of the debug error page.

            :param exc_type: The exception type name.
            :param exc_message: The exception message string.

            :returns: The HTML header string.
        """
        escaped_type = html.escape(exc_type)
        escaped_message = html.escape(exc_message)

        header_html = _DEBUG_PAGE_HEADER.format(
            exc_type=escaped_type,
            exc_message=escaped_message,
        )

        return header_html

    def _render_traceback_section(self, frames: List[FrameInfo]) -> str:
        """
            Render the traceback section with source context and
            local variables for each frame.

            :param frames: The list of FrameInfo objects.

            :returns: The HTML traceback section string.
        """
        parts = []
        parts.append('<div class="traceback">')
        parts.append("<h2>Traceback</h2>")

        for frame in frames:
            parts.append(self._render_frame(frame))

        parts.append("</div>")

        section_html = "\n".join(parts)

        return section_html

    def _render_frame(self, frame: FrameInfo) -> str:
        """
            Render a single stack frame with source context and
            local variables.

            :param frame: The FrameInfo object.

            :returns: The HTML frame string.
        """
        escaped_filename = html.escape(frame.filename)
        escaped_function = html.escape(frame.function)

        parts = []
        parts.append('<div class="frame">')
        parts.append(
            '<div class="frame-header">File "<span class="filename">{}</span>", '
            'line <span class="lineno">{}</span>, in '
            '<span class="function">{}</span></div>'.format(
                escaped_filename, frame.lineno, escaped_function,
            )
        )

        # Source code context
        if len(frame.code_context) > 0:
            parts.append('<pre class="source">')
            start_lineno = frame.lineno - frame.highlight_line

            for idx, line in enumerate(frame.code_context):
                line_number = start_lineno + idx
                escaped_line = html.escape(line.rstrip("\n"))
                css_class = "highlight" if idx == frame.highlight_line else "context"
                parts.append(
                    '<span class="line {css_class}">'
                    '<span class="line-number">{num:>4}</span> {code}</span>'.format(
                        css_class=css_class,
                        num=line_number,
                        code=escaped_line,
                    )
                )

            parts.append("</pre>")

        # Local variables
        if len(frame.locals) > 0:
            parts.append('<div class="locals">')
            parts.append("<h3>Local Variables</h3>")
            parts.append("<table>")

            for var_name, var_value in frame.locals.items():
                escaped_name = html.escape(var_name)
                escaped_value = html.escape(var_value)
                parts.append(
                    "<tr><td class=\"var-name\">{}</td>"
                    "<td class=\"var-value\">{}</td></tr>".format(
                        escaped_name, escaped_value,
                    )
                )

            parts.append("</table>")
            parts.append("</div>")

        parts.append("</div>")

        frame_html = "\n".join(parts)

        return frame_html

    def _render_request_section(self, request_info: Dict[str, Any]) -> str:
        """
            Render the request information section.

            :param request_info: Dictionary of request attributes.

            :returns: The HTML request section string.
        """
        parts = []
        parts.append('<div class="request-info">')
        parts.append("<h2>Request Information</h2>")
        parts.append("<table>")

        for key, value in request_info.items():
            escaped_key = html.escape(str(key))
            escaped_value = html.escape(str(value))
            parts.append(
                "<tr><td class=\"info-key\">{}</td>"
                "<td class=\"info-value\">{}</td></tr>".format(
                    escaped_key, escaped_value,
                )
            )

        parts.append("</table>")
        parts.append("</div>")

        section_html = "\n".join(parts)

        return section_html

    def _render_debug_footer(self) -> str:
        """
            Render the footer of the debug error page.

            :returns: The HTML footer string.
        """
        footer_html = "</div></body></html>"

        return footer_html

    # -------------------------------------------------------------------------
    # Production Page Rendering
    # -------------------------------------------------------------------------

    def _render_production_page(
        self,
        request: Any,
        exception: Exception,
        error_id: str,
        status_code: int = 500,
    ) -> str:
        """
            Render the production error page HTML.

            Displays a user-friendly message and error reference ID
            without exposing any internal details such as stack traces,
            local variables, or file paths.

            :param request: The request object or dictionary.
            :param exception: The exception that was raised.
            :param error_id: The unique error reference ID.
            :param status_code: The HTTP status code.

            :returns: The HTML string for the production error page.
        """
        # Check for custom template first
        if status_code in self._custom_templates:
            title, message = self._get_status_message(status_code)
            template = self._custom_templates[status_code]
            page_html = template.format(
                error_title=html.escape(title),
                error_message=html.escape(message),
                error_id=html.escape(error_id),
                status_code=status_code,
            )
            return page_html

        # Check for template file on disk
        if self._template_path is not None:
            template_file = os.path.join(
                self._template_path, "{}.html".format(status_code),
            )
            if os.path.isfile(template_file):
                title, message = self._get_status_message(status_code)
                with open(template_file, "r", encoding="utf-8") as fh:
                    template = fh.read()
                page_html = template.format(
                    error_title=html.escape(title),
                    error_message=html.escape(message),
                    error_id=html.escape(error_id),
                    status_code=status_code,
                )
                return page_html

        # Default production page
        title, message = self._get_status_message(status_code)
        page_html = _PRODUCTION_PAGE_TEMPLATE.format(
            error_title=html.escape(title),
            error_message=html.escape(message),
            error_id=html.escape(error_id),
            status_code=status_code,
        )

        return page_html

    def _get_status_message(self, status_code: int) -> Tuple[str, str]:
        """
            Get the title and message for a given HTTP status code.

            :param status_code: The HTTP status code.

            :returns: A tuple of (title, message) strings.
        """
        if status_code in STATUS_CODE_MESSAGES:
            title, message = STATUS_CODE_MESSAGES[status_code]
        else:
            title = DEFAULT_PRODUCTION_TITLE
            message = DEFAULT_PRODUCTION_MESSAGE

        return title, message

    # -------------------------------------------------------------------------
    # Traceback Extraction
    # -------------------------------------------------------------------------

    def _extract_traceback(self, exception: Exception) -> List[FrameInfo]:
        """
            Extract stack frames with source context from an exception.

            Walks the traceback chain and collects filename, line number,
            function name, surrounding source lines, and local variables
            for each frame.

            :param exception: The exception to extract frames from.

            :returns: A list of FrameInfo objects ordered from outermost
                to innermost frame.
        """
        frames = []

        tb = exception.__traceback__
        while tb is not None:
            frame_obj = tb.tb_frame
            lineno = tb.tb_lineno
            filename = frame_obj.f_code.co_filename
            function = frame_obj.f_code.co_name

            code_context, highlight_idx = self._get_source_context(
                filename, lineno,
            )
            local_vars = self._get_local_variables(frame_obj)

            frame_info = FrameInfo(
                filename=filename,
                lineno=lineno,
                function=function,
                code_context=code_context,
                highlight_line=highlight_idx,
                locals=local_vars,
            )
            frames.append(frame_info)

            tb = tb.tb_next

        return frames

    def _get_source_context(
        self,
        filename: str,
        lineno: int,
    ) -> Tuple[List[str], int]:
        """
            Read source lines around the given line number.

            :param filename: The source file path.
            :param lineno: The target line number.

            :returns: A tuple of (lines, highlight_index) where lines
                is a list of source code strings and highlight_index
                is the index of the target line within the list.
        """
        try:
            with open(filename, "r", encoding="utf-8") as fh:
                all_lines = fh.readlines()
        except (OSError, IOError):
            return [], 0

        total_lines = len(all_lines)
        start = max(0, lineno - 1 - CONTEXT_LINES)
        end = min(total_lines, lineno + CONTEXT_LINES)

        context_lines = all_lines[start:end]
        highlight_idx = (lineno - 1) - start

        return context_lines, highlight_idx

    def _get_local_variables(self, frame) -> Dict[str, str]:
        """
            Get formatted local variables from a frame object.

            Each variable value is converted to its string representation.
            Values that raise exceptions during conversion are replaced
            with an error placeholder.

            :param frame: The frame object from the traceback.

            :returns: A dictionary of variable name to string value pairs.
        """
        local_vars = {}

        for var_name, var_value in frame.f_locals.items():
            try:
                str_value = repr(var_value)
                # Truncate very long values
                if len(str_value) > 200:
                    str_value = str_value[:200] + "..."
            except Exception:
                str_value = "<error displaying value>"

            local_vars[var_name] = str_value

        return local_vars

    # -------------------------------------------------------------------------
    # Request Info Extraction
    # -------------------------------------------------------------------------

    def _extract_request_info(self, request: Any) -> Dict[str, Any]:
        """
            Extract request information from a request object or dictionary.

            Supports both dictionary-style requests and objects with
            method, path, headers, and body attributes.

            :param request: The request object or dictionary.

            :returns: A dictionary of request attribute name-value pairs.
        """
        info = {}

        if isinstance(request, dict):
            info["Method"] = request.get("method", "UNKNOWN")
            info["Path"] = request.get("path", "/")
            headers = request.get("headers", {})
            if isinstance(headers, dict):
                for hdr_name, hdr_value in headers.items():
                    info["Header: {}".format(hdr_name)] = hdr_value
            body = request.get("body", "")
            if body:
                info["Body"] = str(body)
        else:
            if hasattr(request, "method"):
                info["Method"] = getattr(request, "method", "UNKNOWN")
            if hasattr(request, "path"):
                info["Path"] = getattr(request, "path", "/")
            if hasattr(request, "headers"):
                headers = getattr(request, "headers", {})
                if isinstance(headers, dict):
                    for hdr_name, hdr_value in headers.items():
                        info["Header: {}".format(hdr_name)] = hdr_value
            if hasattr(request, "body"):
                body = getattr(request, "body", "")
                if body:
                    info["Body"] = str(body)

        return info

    # -------------------------------------------------------------------------
    # Server-Side Error Logging
    # -------------------------------------------------------------------------

    def _log_error(
        self,
        request: Any,
        exception: Exception,
        error_id: str,
    ) -> None:
        """
            Log the full error details server-side for debugging.

            This is called in production mode to ensure error details
            are captured in the server logs even though they are not
            displayed to the user.

            :param request: The request object or dictionary.
            :param exception: The exception that was raised.
            :param error_id: The unique error reference ID.
        """
        request_info = self._extract_request_info(request)
        tb_text = traceback.format_exception(
            type(exception), exception, exception.__traceback__,
        )
        tb_string = "".join(tb_text)

        log_lines = [
            "Error ID: {}".format(error_id),
            "Exception: {}: {}".format(type(exception).__name__, str(exception)),
        ]

        for key, value in request_info.items():
            log_lines.append("{}: {}".format(key, value))

        log_lines.append("Traceback:")
        log_lines.append(tb_string)

        log_message = os.linesep.join(log_lines)
        logger.error(log_message)

        return


# =============================================================================
# HTML Templates
# =============================================================================

_DEBUG_PAGE_HEADER = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{exc_type}: {exc_message}</title>
<style>
body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    margin: 0;
    padding: 20px;
    background-color: #f5f5f5;
    color: #333;
}}
.container {{
    max-width: 1200px;
    margin: 0 auto;
}}
h1 {{
    color: #c0392b;
    font-size: 24px;
    margin-bottom: 5px;
}}
h1 .exc-type {{
    font-weight: bold;
}}
.exc-message {{
    color: #555;
    font-size: 18px;
    margin-bottom: 20px;
    padding: 10px;
    background-color: #fdf2f2;
    border-left: 4px solid #c0392b;
}}
h2 {{
    color: #2c3e50;
    font-size: 18px;
    border-bottom: 2px solid #3498db;
    padding-bottom: 5px;
}}
h3 {{
    color: #2c3e50;
    font-size: 14px;
    margin: 10px 0 5px 0;
}}
.frame {{
    background-color: #fff;
    border: 1px solid #ddd;
    border-radius: 4px;
    margin-bottom: 15px;
    padding: 10px;
}}
.frame-header {{
    font-size: 13px;
    color: #666;
    margin-bottom: 8px;
}}
.filename {{
    color: #2980b9;
    font-weight: bold;
}}
.lineno {{
    color: #c0392b;
    font-weight: bold;
}}
.function {{
    color: #8e44ad;
    font-weight: bold;
}}
pre.source {{
    background-color: #2d2d2d;
    color: #f8f8f2;
    padding: 10px;
    border-radius: 4px;
    overflow-x: auto;
    font-size: 13px;
    line-height: 1.5;
    margin: 5px 0;
}}
.line {{
    display: block;
    white-space: pre;
}}
.line.highlight {{
    background-color: #49483e;
    border-left: 3px solid #e74c3c;
    padding-left: 5px;
}}
.line.context {{
    padding-left: 8px;
}}
.line-number {{
    color: #75715e;
    user-select: none;
    margin-right: 10px;
}}
.locals table, .request-info table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
}}
.locals td, .request-info td {{
    padding: 4px 8px;
    border-bottom: 1px solid #eee;
    vertical-align: top;
}}
.var-name, .info-key {{
    font-weight: bold;
    color: #2c3e50;
    width: 200px;
    font-family: monospace;
}}
.var-value, .info-value {{
    font-family: monospace;
    color: #555;
    word-break: break-all;
}}
.request-info {{
    background-color: #fff;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 10px;
    margin-top: 15px;
}}
</style>
</head>
<body>
<div class="container">
<h1><span class="exc-type">{exc_type}</span></h1>
<div class="exc-message">{exc_message}</div>"""

_PRODUCTION_PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{error_title}</title>
<style>
body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    margin: 0;
    padding: 0;
    background-color: #f5f5f5;
    color: #333;
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
}}
.error-container {{
    text-align: center;
    padding: 40px;
    background-color: #fff;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    max-width: 500px;
}}
.status-code {{
    font-size: 72px;
    font-weight: bold;
    color: #e74c3c;
    margin-bottom: 10px;
}}
h1 {{
    font-size: 24px;
    color: #2c3e50;
    margin-bottom: 15px;
}}
p {{
    font-size: 16px;
    color: #666;
    line-height: 1.5;
}}
.error-id {{
    font-size: 12px;
    color: #999;
    margin-top: 20px;
}}
</style>
</head>
<body>
<div class="error-container">
<div class="status-code">{status_code}</div>
<h1>{error_title}</h1>
<p>{error_message}</p>
<div class="error-id">Error Reference: {error_id}</div>
</div>
</body>
</html>"""
