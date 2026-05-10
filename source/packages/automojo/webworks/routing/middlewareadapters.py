"""
    Middleware Adapters module.

    This module provides adapter classes that bridge between the internal
    Middleware/AsyncMiddleware protocols used by MiddlewarePipeline and the
    external ASGI and WSGI middleware protocols.

    Adapters:
        - ASGIMiddlewareAdapter: Wraps ASGI middleware to AsyncMiddleware protocol.
        - AsyncMiddlewareToASGI: Wraps AsyncMiddleware to ASGI middleware protocol.
        - WSGIMiddlewareAdapter: Wraps WSGI middleware factory to Middleware protocol.
        - MiddlewareToWSGI: Wraps Middleware to WSGI middleware factory pattern.
"""

import io
import logging

from typing import Any, Awaitable, Callable, Dict, Iterable, List, Optional, Tuple, Union

from automojo.webworks.routing.request import Request
from automojo.webworks.routing.response import Response


# Module-level logger. The WSGI bridge falls back to a 500 status
# code when the start_response status string is malformed; without
# the breadcrumb the operator sees a 500 with no upstream context.
logger = logging.getLogger(__name__)


# =============================================================================
# ASGI Adapters
# =============================================================================

class ASGIMiddlewareAdapter:
    """
        Wraps an ASGI middleware (scope, receive, send) to conform to
        the AsyncMiddleware protocol used by MiddlewarePipeline.

        The ASGI middleware is expected to be a callable with the signature::

            async def asgi_middleware(scope, receive, send):
                ...

        This adapter converts the internal Request/Response flow into ASGI
        scope/receive/send calls, allowing ASGI middleware to participate
        in the MiddlewarePipeline.

        :param asgi_middleware: An ASGI middleware callable.
        :param name: Optional name for pipeline identification.
    """

    def __init__(self, asgi_middleware: Callable, name: str = "") -> None:
        self._asgi_middleware = asgi_middleware
        self._name = name
        return

    @property
    def name(self) -> str:
        """
            Get the adapter name.

            :returns: The middleware name.
        """
        rtnval = self._name
        return rtnval

    async def __call__(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
            Execute the wrapped ASGI middleware within the pipeline.

            Converts the Request to an ASGI scope, invokes the ASGI middleware,
            and captures the response sent via the ASGI send callable.

            :param request: The incoming Request.
            :param call_next: Async callable to invoke the next middleware/handler.

            :returns: Response from the ASGI middleware or the next handler.
        """
        # Build ASGI scope from the request
        scope = self._build_scope(request)

        # Track whether the ASGI middleware called the inner app
        inner_called = [False]
        captured_response = [None]

        async def receive() -> Dict[str, Any]:
            """
                Provide the request body as an ASGI receive event.
            """
            return {
                "type": "http.request",
                "body": request.body,
                "more_body": False,
            }

        # Collect response events sent by the ASGI middleware
        response_started = [False]
        response_status = [200]
        response_headers: List[Tuple[str, str]] = []
        response_body_parts: List[bytes] = []

        async def send(event: Dict[str, Any]) -> None:
            """
                Capture ASGI response events.
            """
            event_type = event.get("type", "")

            if event_type == "http.response.start":
                response_started[0] = True
                response_status[0] = event.get("status", 200)
                raw_headers = event.get("headers", [])
                for header_pair in raw_headers:
                    if len(header_pair) >= 2:
                        h_name = header_pair[0]
                        h_value = header_pair[1]
                        if isinstance(h_name, bytes):
                            h_name = h_name.decode("latin-1")
                        if isinstance(h_value, bytes):
                            h_value = h_value.decode("latin-1")
                        response_headers.append((h_name, h_value))

            elif event_type == "http.response.body":
                body_chunk = event.get("body", b"")
                if body_chunk:
                    response_body_parts.append(body_chunk)

            return

        # Create an inner ASGI app that delegates to call_next
        async def inner_app(inner_scope: Dict[str, Any], inner_receive: Callable, inner_send: Callable) -> None:
            inner_called[0] = True
            resp = await call_next(request)
            captured_response[0] = resp

            # Convert the Response back to ASGI events for the outer middleware
            asgi_data = resp.to_asgi()
            await inner_send(asgi_data["start"])
            await inner_send(asgi_data["body"])
            return

        # Invoke the ASGI middleware, passing our inner app
        await self._asgi_middleware(inner_app)(scope, receive, send)

        # If the ASGI middleware sent its own response (short-circuit)
        if response_started[0]:
            headers_dict: Dict[str, str] = {}
            for h_name, h_value in response_headers:
                headers_dict[h_name] = h_value

            body = b"".join(response_body_parts)
            response = Response(
                status_code=response_status[0],
                headers=headers_dict,
                body=body,
            )
            return response

        # If the inner app was called but no response was sent via send,
        # return the captured response from call_next
        if inner_called[0] and captured_response[0] is not None:
            return captured_response[0]

        # Fallback: call_next was never invoked by the ASGI middleware
        return await call_next(request)

    def _build_scope(self, request: Request) -> Dict[str, Any]:
        """
            Build an ASGI scope dictionary from a Request.

            :param request: The incoming Request.

            :returns: ASGI scope dictionary.
        """
        headers_list: List[List[bytes]] = []
        for h_name, h_value in request.headers.items():
            headers_list.append([
                h_name.lower().encode("latin-1"),
                h_value.encode("latin-1"),
            ])

        scope: Dict[str, Any] = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": request.method,
            "path": request.path,
            "query_string": request._query_string,
            "headers": headers_list,
            "server": (request._host, request._port),
            "scheme": request._scheme,
        }
        return scope


class AsyncMiddlewareToASGI:
    """
        Wraps an AsyncMiddleware to conform to the ASGI middleware protocol
        (scope, receive, send) for use with external ASGI servers.

        This adapter allows internal AsyncMiddleware components to be used
        as standard ASGI middleware that wraps an ASGI application.

        :param middleware: An AsyncMiddleware instance.
        :param app: The inner ASGI application to wrap.
    """

    def __init__(self, middleware: Any, app: Callable) -> None:
        self._middleware = middleware
        self._app = app
        return

    async def __call__(
        self,
        scope: Dict[str, Any],
        receive: Callable,
        send: Callable
    ) -> None:
        """
            Handle an ASGI request by delegating to the wrapped AsyncMiddleware.

            Converts the ASGI scope/receive/send into a Request, executes the
            AsyncMiddleware with a call_next that delegates to the inner ASGI
            app, and sends the resulting Response back via the ASGI send callable.

            :param scope: ASGI scope dictionary.
            :param receive: ASGI receive callable.
            :param send: ASGI send callable.
        """
        if scope.get("type") != "http":
            # Pass through non-HTTP scopes directly
            await self._app(scope, receive, send)
            return

        # Read the request body from receive
        body = await self._read_body(receive)

        # Build a Request from the ASGI scope
        request = Request.from_asgi(scope, body=body)

        # Define call_next that delegates to the inner ASGI app
        async def call_next(req: Request) -> Response:
            """
                Invoke the inner ASGI app and capture its response.
            """
            captured_status = [200]
            captured_headers: List[Tuple[str, str]] = []
            captured_body_parts: List[bytes] = []

            async def capture_send(event: Dict[str, Any]) -> None:
                event_type = event.get("type", "")
                if event_type == "http.response.start":
                    captured_status[0] = event.get("status", 200)
                    raw_headers = event.get("headers", [])
                    for header_pair in raw_headers:
                        if len(header_pair) >= 2:
                            h_name = header_pair[0]
                            h_value = header_pair[1]
                            if isinstance(h_name, bytes):
                                h_name = h_name.decode("latin-1")
                            if isinstance(h_value, bytes):
                                h_value = h_value.decode("latin-1")
                            captured_headers.append((h_name, h_value))
                elif event_type == "http.response.body":
                    body_chunk = event.get("body", b"")
                    if body_chunk:
                        captured_body_parts.append(body_chunk)
                return

            # Provide the request body back via receive
            body_sent = [False]

            async def inner_receive() -> Dict[str, Any]:
                if not body_sent[0]:
                    body_sent[0] = True
                    return {
                        "type": "http.request",
                        "body": req.body,
                        "more_body": False,
                    }
                return {"type": "http.disconnect"}

            await self._app(scope, inner_receive, capture_send)

            headers_dict: Dict[str, str] = {}
            for h_name, h_value in captured_headers:
                headers_dict[h_name] = h_value

            response = Response(
                status_code=captured_status[0],
                headers=headers_dict,
                body=b"".join(captured_body_parts),
            )
            return response

        # Execute the AsyncMiddleware
        response = await self._middleware(request, call_next)

        # Send the response back via ASGI
        asgi_data = response.to_asgi()
        await send(asgi_data["start"])
        await send(asgi_data["body"])
        return

    async def _read_body(self, receive: Callable) -> bytes:
        """
            Read the complete request body from the ASGI receive callable.

            :param receive: ASGI receive callable.

            :returns: Complete body as bytes.
        """
        body_parts: List[bytes] = []

        while True:
            event = await receive()
            event_type = event.get("type", "")

            if event_type == "http.request":
                chunk = event.get("body", b"")
                if chunk:
                    body_parts.append(chunk)
                if not event.get("more_body", False):
                    break
            elif event_type == "http.disconnect":
                break
            else:
                break

        return b"".join(body_parts)


# =============================================================================
# WSGI Adapters
# =============================================================================

class WSGIMiddlewareAdapter:
    """
        Wraps a WSGI middleware factory to conform to the Middleware protocol
        used by MiddlewarePipeline.

        A WSGI middleware factory is a callable that accepts a WSGI application
        and returns a wrapped WSGI application::

            def wsgi_middleware_factory(app):
                def middleware(environ, start_response):
                    # ... modify environ or response ...
                    return app(environ, start_response)
                return middleware

        This adapter converts the internal Request/call_next flow into WSGI
        environ/start_response calls, allowing WSGI middleware to participate
        in the MiddlewarePipeline.

        :param wsgi_factory: A WSGI middleware factory callable.
        :param name: Optional name for pipeline identification.
    """

    def __init__(self, wsgi_factory: Callable, name: str = "") -> None:
        self._wsgi_factory = wsgi_factory
        self._name = name
        return

    @property
    def name(self) -> str:
        """
            Get the adapter name.

            :returns: The middleware name.
        """
        rtnval = self._name
        return rtnval

    def __call__(
        self,
        request: Request,
        call_next: Callable[[Request], Response]
    ) -> Response:
        """
            Execute the wrapped WSGI middleware factory within the pipeline.

            Converts the Request to a WSGI environ, wraps call_next as a WSGI
            application, applies the WSGI middleware factory, and converts the
            result back to a Response.

            :param request: The incoming Request.
            :param call_next: Callable to invoke the next middleware/handler.

            :returns: Response from the WSGI middleware or the next handler.
        """
        # Build WSGI environ from the request
        environ = self._build_environ(request)

        # Create an inner WSGI app that delegates to call_next
        def inner_app(
            inner_environ: Dict[str, Any],
            inner_start_response: Callable
        ) -> Iterable[bytes]:
            # Reconstruct a Request from the (possibly modified) environ
            inner_request = Request.from_wsgi(inner_environ)
            resp = call_next(inner_request)

            # Convert Response to WSGI format
            status_line, headers_list, body_iterable = resp.to_wsgi()
            inner_start_response(status_line, headers_list)
            return body_iterable

        # Apply the WSGI middleware factory to the inner app
        wrapped_app = self._wsgi_factory(inner_app)

        # Execute the wrapped WSGI app
        captured_status = [None]
        captured_headers: List[Tuple[str, str]] = []

        def start_response(
            status: str,
            response_headers: List[Tuple[str, str]],
            exc_info: Any = None
        ) -> Callable:
            captured_status[0] = status
            captured_headers.clear()
            captured_headers.extend(response_headers)

            def write(data: bytes) -> None:
                # The write callable is deprecated in WSGI but must be supported
                pass

            return write

        body_iterable = wrapped_app(environ, start_response)

        # Collect the response body
        body_parts: List[bytes] = []
        for chunk in body_iterable:
            if chunk:
                body_parts.append(chunk)

        # Close the iterable if it has a close method
        if hasattr(body_iterable, "close"):
            body_iterable.close()

        # Parse the status code from the status line
        status_code = 200
        if captured_status[0] is not None:
            try:
                status_code = int(captured_status[0].split(" ", 1)[0])
            except (ValueError, IndexError) as exc:
                logger.warning(
                    "WSGI adapter: malformed status line %r; defaulting to 500: %s",
                    captured_status[0],
                    exc,
                )
                status_code = 500

        # Build headers dict
        headers_dict: Dict[str, str] = {}
        for h_name, h_value in captured_headers:
            headers_dict[h_name] = h_value

        response = Response(
            status_code=status_code,
            headers=headers_dict,
            body=b"".join(body_parts),
        )
        return response

    def _build_environ(self, request: Request) -> Dict[str, Any]:
        """
            Build a WSGI environ dictionary from a Request.

            :param request: The incoming Request.

            :returns: WSGI environ dictionary.
        """
        environ: Dict[str, Any] = {
            "REQUEST_METHOD": request.method,
            "PATH_INFO": request.path,
            "QUERY_STRING": request._query_string.decode("utf-8", errors="replace") if request._query_string else "",
            "SERVER_NAME": request._host,
            "SERVER_PORT": str(request._port),
            "wsgi.url_scheme": request._scheme,
            "wsgi.input": io.BytesIO(request.body),
            "wsgi.errors": io.BytesIO(),
            "wsgi.multithread": False,
            "wsgi.multiprocess": False,
            "wsgi.run_once": False,
        }

        # Add headers to environ
        for h_name, h_value in request.headers.items():
            key = h_name.upper().replace("-", "_")
            if key == "CONTENT_TYPE":
                environ["CONTENT_TYPE"] = h_value
            elif key == "CONTENT_LENGTH":
                environ["CONTENT_LENGTH"] = h_value
            else:
                environ[f"HTTP_{key}"] = h_value

        return environ


class MiddlewareToWSGI:
    """
        Wraps a Middleware to conform to the WSGI middleware factory pattern
        for use with external WSGI servers.

        This adapter allows internal Middleware components to be used as
        standard WSGI middleware factories. When called with a WSGI application,
        it returns a new WSGI application that applies the middleware.

        :param middleware: A Middleware instance.
    """

    def __init__(self, middleware: Any) -> None:
        self._middleware = middleware
        return

    def __call__(self, app: Callable) -> Callable:
        """
            Wrap a WSGI application with the internal Middleware.

            Returns a new WSGI application callable that applies the
            middleware before delegating to the inner application.

            :param app: The inner WSGI application.

            :returns: A wrapped WSGI application callable.
        """
        middleware = self._middleware

        def wsgi_app(
            environ: Dict[str, Any],
            start_response: Callable
        ) -> Iterable[bytes]:
            # Build a Request from the WSGI environ
            request = Request.from_wsgi(environ)

            # Define call_next that delegates to the inner WSGI app
            def call_next(req: Request) -> Response:
                # Rebuild environ from the (possibly modified) request
                inner_environ = _rebuild_environ(req, environ)

                captured_status = [None]
                captured_headers: List[Tuple[str, str]] = []

                def inner_start_response(
                    status: str,
                    response_headers: List[Tuple[str, str]],
                    exc_info: Any = None
                ) -> Callable:
                    captured_status[0] = status
                    captured_headers.clear()
                    captured_headers.extend(response_headers)

                    def write(data: bytes) -> None:
                        pass

                    return write

                body_iterable = app(inner_environ, inner_start_response)

                # Collect body
                body_parts: List[bytes] = []
                for chunk in body_iterable:
                    if chunk:
                        body_parts.append(chunk)

                if hasattr(body_iterable, "close"):
                    body_iterable.close()

                # Parse status code
                status_code = 200
                if captured_status[0] is not None:
                    try:
                        status_code = int(captured_status[0].split(" ", 1)[0])
                    except (ValueError, IndexError) as exc:
                        logger.warning(
                            "WSGI adapter: malformed status line %r; defaulting to 500: %s",
                            captured_status[0],
                            exc,
                        )
                        status_code = 500

                headers_dict: Dict[str, str] = {}
                for h_name, h_value in captured_headers:
                    headers_dict[h_name] = h_value

                response = Response(
                    status_code=status_code,
                    headers=headers_dict,
                    body=b"".join(body_parts),
                )
                return response

            # Execute the middleware
            response = middleware(request, call_next)

            # Convert the Response back to WSGI format
            status_line, headers_list, body_iterable = response.to_wsgi()
            start_response(status_line, headers_list)
            return body_iterable

        return wsgi_app


def _rebuild_environ(request: Request, original_environ: Dict[str, Any]) -> Dict[str, Any]:
    """
        Rebuild a WSGI environ dictionary from a Request, preserving
        original environ entries that are not part of the Request.

        :param request: The Request to build environ from.
        :param original_environ: The original WSGI environ to preserve.

        :returns: Updated WSGI environ dictionary.
    """
    environ = dict(original_environ)

    environ["REQUEST_METHOD"] = request.method
    environ["PATH_INFO"] = request.path
    environ["wsgi.input"] = io.BytesIO(request.body)

    # Update headers
    for h_name, h_value in request.headers.items():
        key = h_name.upper().replace("-", "_")
        if key == "CONTENT_TYPE":
            environ["CONTENT_TYPE"] = h_value
        elif key == "CONTENT_LENGTH":
            environ["CONTENT_LENGTH"] = h_value
        else:
            environ[f"HTTP_{key}"] = h_value

    return environ
