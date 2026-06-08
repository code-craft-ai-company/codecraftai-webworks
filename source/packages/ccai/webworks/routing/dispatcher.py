"""
    Dispatcher module.
    
    This module provides the Dispatcher class that orchestrates routing
    and middleware execution for incoming HTTP requests.
    
    The Dispatcher is the central component that:
    - Routes requests to find matching handlers
    - Populates request path parameters from route matches
    - Executes the middleware pipeline with the handler
    - Handles HTTP exceptions and converts them to responses
    - Handles unhandled exceptions with appropriate error responses
    
    Example:
        router = Router()
        pipeline = MiddlewarePipeline()
        dispatcher = Dispatcher(router, pipeline)
        
        response = dispatcher.dispatch(request)
"""

import logging
import traceback
from typing import Awaitable, Callable, Optional, TYPE_CHECKING

from ccai.webworks.routing.request import Request
from ccai.webworks.routing.response import (
    Response,
    JSONResponse,
    HTMLResponse,
)
from ccai.webworks.routing.router import Router, RouteMatch
from ccai.webworks.routing.middleware import MiddlewarePipeline
from ccai.webworks.routing.exceptions import HTTPException, MethodNotAllowed, NotFound
from ccai.webworks.templating.response import (
    StreamingTemplateResponse,
    TemplateResponse,
)


# Response shapes the dispatcher accepts back from a handler. Each
# carries the ``status_code`` / ``headers`` / ``body`` triple the
# ASGI :class:`ccai.webworks.asgi.responsesender.ResponseSender`
# duck-types over, so any of them flow through the rest of the
# pipeline unchanged. Anything else returned by a handler is
# wrapped in :class:`JSONResponse`.
_RESPONSE_TYPES = (Response, TemplateResponse, StreamingTemplateResponse)


# Module-level logger used when the dispatcher's catch-all converts
# an unhandled handler/middleware exception into a 500. Without
# this, every production 500 was silent — the response body said
# "Internal Server Error" with no record of the underlying
# exception in the journal, making post-hoc debugging impossible.
logger = logging.getLogger(__name__)


# Keys present on the ``{status, body, content_type}`` dict shape
# that :class:`ccai.webworks.authentication.blueprints.security.SecurityBlueprint`
# helpers (``format_error``, ``format_success``, ``establish_session``)
# return from auth handlers. The dispatcher recognises this shape and
# translates it into a real :class:`JSONResponse` with the embedded
# status code, optional headers, and body so the wire response carries
# the right HTTP status. Without this translation a handler that
# returns ``{"status": 401, "body": {...}}`` would surface as ``HTTP
# 200`` with the status code embedded in the JSON body — which is what
# was happening to ``POST /auth/session/login`` before this change.
_AUTH_RESPONSE_DICT_KEYS = frozenset(("status", "body", "content_type"))


def _is_auth_response_dict(result: object) -> bool:
    """
        Return ``True`` when ``result`` matches the auth-blueprint
        response-dict shape produced by
        :meth:`SecurityBlueprint.format_error`,
        :meth:`SecurityBlueprint.format_success`, and
        :meth:`SessionAuthBlueprint.establish_session`.

        The shape is::

            {"status": <int>, "body": <jsonable>,
             "content_type": <str>, "headers": <dict, optional>}

        Recognition is intentionally narrow — both ``status`` and
        ``body`` must be present, ``status`` must be an ``int``, and
        the dict must declare ``content_type``. Any other dict
        returned by a handler falls through to the default
        ``JSONResponse(result)`` wrapping with status 200.

        :param result: The handler return value.

        :returns: ``True`` if the dict should be translated into a
                  :class:`JSONResponse` with the embedded status.
    """
    if not isinstance(result, dict):
        return False

    if not _AUTH_RESPONSE_DICT_KEYS.issubset(result.keys()):
        return False

    status_value = result.get("status")
    if not isinstance(status_value, int):
        return False

    return True


def _auth_response_dict_to_response(result: dict) -> JSONResponse:
    """
        Translate an auth-blueprint response-dict into a
        :class:`JSONResponse` that carries the embedded HTTP status
        and any ``headers`` the handler attached (e.g. the
        ``Set-Cookie`` issued by
        :meth:`SessionAuthBlueprint.establish_session`).

        :param result: A dict matching :func:`_is_auth_response_dict`.

        :returns: A :class:`JSONResponse` with ``status_code`` set to
                  ``result["status"]``, ``content`` set to
                  ``result["body"]``, and ``headers`` merged from
                  ``result.get("headers", {})``.
    """
    status_code = int(result["status"])
    body = result["body"]
    headers = result.get("headers")
    if not isinstance(headers, dict):
        headers = {}

    response = JSONResponse(
        content=body,
        status_code=status_code,
        headers=headers,
    )
    return response


class Dispatcher:
    """
        Orchestrates routing and middleware execution for incoming requests.
        
        The Dispatcher is responsible for:
        - Matching requests to registered routes
        - Populating request.path_params from the route match
        - Executing the middleware pipeline with the matched handler
        - Converting HTTPExceptions to appropriate responses
        - Handling unhandled exceptions with 500 responses
        
        Configuration options:
        - debug: If True, include stack traces in error responses.
        - error_format: Format for error responses ("json", "html", "text").
        
        :param router: Router for URL matching.
        :param pipeline: MiddlewarePipeline for request processing.
        :param debug: If True, include stack traces in error responses.
        :param error_format: Format for error responses ("json", "html", "text").
        
        Example:
            router = Router()
            pipeline = MiddlewarePipeline()
            dispatcher = Dispatcher(router, pipeline, debug=True)
            
            response = dispatcher.dispatch(request)
    """
    
    def __init__(
        self,
        router: Router,
        pipeline: Optional[MiddlewarePipeline] = None,
        debug: bool = False,
        error_format: str = "json"
    ):
        """
            Construct a Dispatcher.
            
            :param router: Router for URL matching.
            :param pipeline: MiddlewarePipeline for request processing.
            :param debug: If True, include stack traces in error responses.
            :param error_format: Format for error responses ("json", "html", "text").
        """
        self._router = router
        self._pipeline = pipeline if pipeline is not None else MiddlewarePipeline()
        self._debug = debug
        self._error_format = error_format
        return
    
    @property
    def router(self) -> Router:
        """
            Get the router.
            
            :returns: Router instance.
        """
        return self._router
    
    @property
    def pipeline(self) -> MiddlewarePipeline:
        """
            Get the middleware pipeline.
            
            :returns: MiddlewarePipeline instance.
        """
        return self._pipeline
    
    @property
    def debug(self) -> bool:
        """
            Whether debug mode is enabled.
            
            :returns: True if debug mode is enabled.
        """
        return self._debug
    
    @debug.setter
    def debug(self, value: bool) -> None:
        """
            Set debug mode.
            
            :param value: True to enable debug mode.
        """
        self._debug = value
        return
    
    @property
    def error_format(self) -> str:
        """
            Get the error response format.
            
            :returns: Error format string ("json", "html", or "text").
        """
        return self._error_format
    
    @error_format.setter
    def error_format(self, value: str) -> None:
        """
            Set the error response format.
            
            :param value: Error format string ("json", "html", or "text").
        """
        self._error_format = value
        return

    def dispatch(self, request: Request) -> Response:
        """
            Dispatch a request through routing and middleware.
            
            This method:
            1. Routes the request to find a matching handler
            2. Populates request.path_params from the route match
            3. Executes the middleware pipeline with the handler
            4. Returns 404 if no route matches
            5. Converts HTTPExceptions to appropriate responses
            6. Handles unhandled exceptions with 500 responses
            
            :param request: The incoming Request.
            
            :returns: Response from handler or error response.
        """
        try:
            # Route the request to find a matching handler
            match = self._router.match(request)
            
            if match is None:
                # Check if the path exists with other methods before returning 404
                allowed_methods = self._router.get_allowed_methods(request.path)
                if allowed_methods:
                    raise MethodNotAllowed(allowed=allowed_methods)
                raise NotFound()
            
            # Populate request.path_params from the route match
            request.path_params = match.path_params
            
            # Create a handler wrapper that catches HTTPExceptions
            def handler_wrapper(req: Request) -> Response:
                try:
                    result = match.handler(req)
                    # If handler returns a known response shape (Response,
                    # TemplateResponse, StreamingTemplateResponse), use it
                    # directly. The auth blueprints return the
                    # ``{status, body, content_type}`` dict shape — translate
                    # it so the wire response carries the embedded status code
                    # and any attached headers (e.g. ``Set-Cookie`` from
                    # ``establish_session``). Everything else is wrapped in a
                    # default ``JSONResponse``.
                    if isinstance(result, _RESPONSE_TYPES):
                        return result
                    if _is_auth_response_dict(result):
                        return _auth_response_dict_to_response(result)
                    return JSONResponse(result)
                except HTTPException as exc:
                    return self._handle_http_exception(exc)
            
            # Execute the middleware pipeline with the handler
            try:
                response = self._pipeline.execute(request, handler_wrapper)
                return response
            except HTTPException as exc:
                return self._handle_http_exception(exc)
        
        except HTTPException as exc:
            # HTTPException raised outside middleware/handler
            return self._handle_http_exception(exc)
        
        except Exception as exc:
            # Unhandled exception
            return self._handle_unhandled_exception(exc)
    
    async def dispatch_async(self, request: Request) -> Response:
        """
            Dispatch a request asynchronously.
            
            This method is the async version of dispatch() and supports
            async handlers and middleware.
            
            :param request: The incoming Request.
            
            :returns: Response from handler or error response.
        """
        try:
            # Route the request to find a matching handler
            match = self._router.match(request)
            
            if match is None:
                # Check if the path exists with other methods before returning 404
                allowed_methods = self._router.get_allowed_methods(request.path)
                if allowed_methods:
                    raise MethodNotAllowed(allowed=allowed_methods)
                raise NotFound()
            
            # Populate request.path_params from the route match
            request.path_params = match.path_params
            
            # Create an async handler wrapper that catches HTTPExceptions
            async def async_handler_wrapper(req: Request) -> Response:
                try:
                    result = match.handler(req)
                    # Check if result is a coroutine
                    import asyncio
                    if asyncio.iscoroutine(result):
                        result = await result
                    # If handler returns a known response shape (Response,
                    # TemplateResponse, StreamingTemplateResponse), use it
                    # directly. The auth blueprints return the
                    # ``{status, body, content_type}`` dict shape — translate
                    # it so the wire response carries the embedded status code
                    # and any attached headers (e.g. ``Set-Cookie`` from
                    # ``establish_session``). Everything else is wrapped in a
                    # default ``JSONResponse``.
                    if isinstance(result, _RESPONSE_TYPES):
                        return result
                    if _is_auth_response_dict(result):
                        return _auth_response_dict_to_response(result)
                    return JSONResponse(result)
                except HTTPException as exc:
                    return self._handle_http_exception(exc)
            
            # Execute the middleware pipeline with the handler
            try:
                response = await self._pipeline.execute_async(
                    request, async_handler_wrapper
                )
                return response
            except HTTPException as exc:
                return self._handle_http_exception(exc)
        
        except HTTPException as exc:
            # HTTPException raised outside middleware/handler
            return self._handle_http_exception(exc)
        
        except Exception as exc:
            # Unhandled exception
            return self._handle_unhandled_exception(exc)
    
    def _handle_http_exception(self, exc: HTTPException) -> Response:
        """
            Convert HTTPException to appropriate response.

            The response format depends on the error_format setting:
            - "json": Returns JSONResponse with error details
            - "html": Returns HTMLResponse with error page
            - "text": Returns plain text Response

            :param exc: The HTTPException to convert.

            :returns: Response with appropriate status and body.
        """
        status_code = exc.status_code
        detail = exc.detail if exc.detail else self._get_status_phrase(status_code)
        headers = exc.headers.copy() if exc.headers else {}

        # 5xx HTTPException is a server-side failure that the operator
        # almost always wants to see in the journal. 4xx is typically
        # client-driven and is logged at lower levels by middleware
        # (audit/security) when needed, so we keep this branch quiet
        # to avoid drowning the journal in 401/404 noise.
        if status_code >= 500:
            logger.exception(
                "HTTPException %d in dispatcher: %s", status_code, detail
            )
        
        if self._error_format == "json":
            content = {
                "detail": detail,
                "status_code": status_code,
            }
            response = JSONResponse(content, status_code=status_code)
            # Add any additional headers from the exception
            for name, value in headers.items():
                response.set_header(name, value)
            return response
        
        elif self._error_format == "html":
            html_content = self._build_error_html(status_code, detail)
            response = HTMLResponse(html_content, status_code=status_code)
            for name, value in headers.items():
                response.set_header(name, value)
            return response
        
        else:
            # Plain text format
            body = detail.encode("utf-8") if detail else b""
            response = Response(status_code=status_code, body=body)
            response.set_header("Content-Type", "text/plain; charset=utf-8")
            for name, value in headers.items():
                response.set_header(name, value)
            return response
    
    def _handle_unhandled_exception(self, exc: Exception) -> Response:
        """
            Handle unhandled exceptions.

            In debug mode, includes the full stack trace in the response.
            In production mode, returns a generic error message.

            Always logs the exception via :data:`logger` so the
            traceback survives in the journal even when the response
            body is the generic "Internal Server Error" string —
            without this, every production 500 was opaque.

            :param exc: The unhandled exception.

            :returns: 500 Internal Server Error response.
        """
        # Log the exception unconditionally — debug mode controls
        # what reaches the client, but the operator always wants the
        # traceback in the journal.
        logger.exception(
            "Unhandled exception in dispatcher: %s", exc
        )

        status_code = 500

        if self._debug:
            # Include stack trace in debug mode
            detail = traceback.format_exc()
        else:
            # Generic message in production
            detail = "Internal Server Error"
        
        if self._error_format == "json":
            content = {
                "detail": detail,
                "status_code": status_code,
            }
            if self._debug:
                content["exception_type"] = type(exc).__name__
                content["exception_message"] = str(exc)
            return JSONResponse(content, status_code=status_code)
        
        elif self._error_format == "html":
            if self._debug:
                # Include formatted stack trace in HTML
                html_content = self._build_debug_error_html(status_code, detail, exc)
            else:
                html_content = self._build_error_html(status_code, detail)
            return HTMLResponse(html_content, status_code=status_code)
        
        else:
            # Plain text format
            body = detail.encode("utf-8")
            response = Response(status_code=status_code, body=body)
            response.set_header("Content-Type", "text/plain; charset=utf-8")
            return response

    def _get_status_phrase(self, status_code: int) -> str:
        """
            Get the HTTP status phrase for a status code.
            
            :param status_code: HTTP status code.
            
            :returns: Status phrase string.
        """
        phrases = {
            100: "Continue",
            101: "Switching Protocols",
            200: "OK",
            201: "Created",
            202: "Accepted",
            204: "No Content",
            301: "Moved Permanently",
            302: "Found",
            303: "See Other",
            304: "Not Modified",
            307: "Temporary Redirect",
            308: "Permanent Redirect",
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found",
            405: "Method Not Allowed",
            406: "Not Acceptable",
            408: "Request Timeout",
            409: "Conflict",
            410: "Gone",
            413: "Payload Too Large",
            415: "Unsupported Media Type",
            422: "Unprocessable Entity",
            429: "Too Many Requests",
            500: "Internal Server Error",
            501: "Not Implemented",
            502: "Bad Gateway",
            503: "Service Unavailable",
            504: "Gateway Timeout",
        }
        return phrases.get(status_code, "Unknown")
    
    def _build_error_html(self, status_code: int, detail: str) -> str:
        """
            Build an HTML error page.
            
            :param status_code: HTTP status code.
            :param detail: Error detail message.
            
            :returns: HTML string.
        """
        phrase = self._get_status_phrase(status_code)
        # Escape HTML special characters in detail
        escaped_detail = (
            detail
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{status_code} {phrase}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 40px;
            background-color: #f5f5f5;
        }}
        .error-container {{
            max-width: 600px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            margin-top: 0;
        }}
        p {{
            color: #666;
            line-height: 1.6;
        }}
    </style>
</head>
<body>
    <div class="error-container">
        <h1>{status_code} {phrase}</h1>
        <p>{escaped_detail}</p>
    </div>
</body>
</html>"""
        return html
    
    def _build_debug_error_html(
        self,
        status_code: int,
        detail: str,
        exc: Exception
    ) -> str:
        """
            Build a debug HTML error page with stack trace.
            
            :param status_code: HTTP status code.
            :param detail: Error detail (stack trace).
            :param exc: The exception that occurred.
            
            :returns: HTML string.
        """
        phrase = self._get_status_phrase(status_code)
        exc_type = type(exc).__name__
        exc_message = str(exc)
        
        # Escape HTML special characters
        escaped_detail = (
            detail
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )
        escaped_message = (
            exc_message
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{status_code} {phrase}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 40px;
            background-color: #f5f5f5;
        }}
        .error-container {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #c0392b;
            margin-top: 0;
        }}
        h2 {{
            color: #333;
            font-size: 1.2em;
        }}
        .exception-type {{
            color: #e74c3c;
            font-weight: bold;
        }}
        .exception-message {{
            color: #666;
            margin-bottom: 20px;
        }}
        pre {{
            background: #2d2d2d;
            color: #f8f8f2;
            padding: 20px;
            border-radius: 4px;
            overflow-x: auto;
            font-size: 13px;
            line-height: 1.5;
        }}
    </style>
</head>
<body>
    <div class="error-container">
        <h1>{status_code} {phrase}</h1>
        <h2>Exception</h2>
        <p class="exception-type">{exc_type}</p>
        <p class="exception-message">{escaped_message}</p>
        <h2>Traceback</h2>
        <pre>{escaped_detail}</pre>
    </div>
</body>
</html>"""
        return html
    
    def __repr__(self) -> str:
        """
            Get string representation.
            
            :returns: String representation.
        """
        return f"Dispatcher(debug={self._debug}, error_format={self._error_format!r})"
