"""
    ASGI HTTP Handler module.
    
    This module provides the HTTPHandler class that handles HTTP request/response
    cycles over ASGI, integrating scope parsing, body reading, response sending,
    middleware execution, and background tasks.
"""

import asyncio
import logging
import traceback

from typing import Any, Awaitable, Callable, Dict, List, Optional

from ccai.webworks.asgi.constants import (
    DEFAULT_MAX_REQUEST_BODY_SIZE,
    MESSAGE_HTTP_RESPONSE_START,
)
from ccai.webworks.asgi.scopeparser import ScopeParser
from ccai.webworks.asgi.bodyreader import BodyReader
from ccai.webworks.asgi.errorhandler import ErrorHandler
from ccai.webworks.asgi.responsesender import ResponseSender
from ccai.webworks.asgi.backgroundtasks import BackgroundTasks
from ccai.webworks.asgi.exceptions import (
    BadRequestBody,
    ClientDisconnected,
    RequestEntityTooLarge,
    RequestTimeout,
)
from ccai.webworks.routing.request import Request
from ccai.webworks.wsgi.response import Response


# Module-level logger. The ASGI HTTP handler turns unhandled
# exceptions into 500 responses; without this the operator only
# sees the wire response and loses the underlying traceback.
logger = logging.getLogger(__name__)


# Type aliases for clarity
ReceiveCallable = Callable[[], Awaitable[Dict[str, Any]]]
SendCallable = Callable[[Dict[str, Any]], Awaitable[None]]
HandlerCallable = Callable[[Request], Awaitable[Response]]
MiddlewareCallable = Callable[[Request, HandlerCallable], Awaitable[Response]]


class HTTPHandler:
    """
        Handles HTTP request/response cycles over ASGI.
        
        This class integrates the ScopeParser, BodyReader, ResponseSender,
        and BackgroundTasks components to provide complete HTTP request handling
        with support for async middleware, handlers, and background tasks.
    """
    
    def __init__(
        self,
        scope_parser: Optional[ScopeParser] = None,
        body_reader: Optional[BodyReader] = None,
        response_sender: Optional[ResponseSender] = None,
        debug: bool = False,
        request_timeout: Optional[float] = None,
        error_handler: Optional[ErrorHandler] = None,
        max_body_size: Optional[int] = None,
    ):
        """
            Construct an HTTPHandler instance.
            
            :param scope_parser: ScopeParser instance for parsing ASGI scopes.
            :param body_reader: BodyReader instance for reading request bodies.
            :param response_sender: ResponseSender instance for sending responses.
            :param debug: If True, include stack traces in error responses.
            :param request_timeout: Optional timeout in seconds for request handling.
            :param error_handler: ErrorHandler that exceptions of the handler are
                                  routed through, so that registered custom handlers
                                  and exceptions that carry a status code take
                                  effect. If None, such exceptions are answered
                                  with a plain 500.
            :param max_body_size: Maximum request body size in bytes for the
                                  BodyReader created when none is passed. The body
                                  is read into memory before the request is routed,
                                  so the default is a limit and not unlimited.
                                  Pass 0 for unlimited.
        """
        if scope_parser is None:
            self._scope_parser = ScopeParser()
        else:
            self._scope_parser = scope_parser
        
        if body_reader is None:
            if max_body_size is None:
                max_body_size = DEFAULT_MAX_REQUEST_BODY_SIZE
            self._body_reader = BodyReader(max_size=max_body_size)
        else:
            self._body_reader = body_reader
        
        if response_sender is None:
            self._response_sender = ResponseSender()
        else:
            self._response_sender = response_sender
        
        self._debug = debug
        self._request_timeout = request_timeout
        self._error_handler = error_handler
        self._middleware: List[MiddlewareCallable] = []
        self._handler: Optional[HandlerCallable] = None
        
        return

    @property
    def debug(self) -> bool:
        """
            Get the debug mode setting.
            
            :returns: True if debug mode is enabled.
        """
        return self._debug
    
    @property
    def request_timeout(self) -> Optional[float]:
        """
            Get the request timeout setting.
            
            :returns: Timeout in seconds or None for no timeout.
        """
        return self._request_timeout
    
    @property
    def error_handler(self) -> Optional[ErrorHandler]:
        """
            Get the error handler exceptions are routed through.
            
            :returns: ErrorHandler instance or None if none is set.
        """
        return self._error_handler
    
    @property
    def body_reader(self) -> BodyReader:
        """
            Get the reader used for request bodies.
            
            :returns: BodyReader instance.
        """
        return self._body_reader
    
    def set_error_handler(self, error_handler: Optional[ErrorHandler]) -> None:
        """
            Set the error handler exceptions are routed through.
            
            :param error_handler: ErrorHandler instance, or None to answer
                                  exceptions with a plain 500.
        """
        self._error_handler = error_handler
        return
    
    def set_handler(self, handler: HandlerCallable) -> None:
        """
            Set the request handler.
            
            The handler is an async function that receives a Request and
            returns a Response.
            
            :param handler: Async handler function.
        """
        self._handler = handler
        return
    
    def add_middleware(self, middleware: MiddlewareCallable) -> None:
        """
            Add middleware to the request pipeline.
            
            Middleware is executed in the order it is added. Each middleware
            receives the request and a callable to invoke the next handler
            in the chain.
            
            :param middleware: Async middleware function.
        """
        self._middleware.append(middleware)
        return
    
    async def handle(
        self,
        scope: Dict[str, Any],
        receive: ReceiveCallable,
        send: SendCallable,
    ) -> None:
        """
            Handle a complete HTTP request/response cycle.
            
            This method parses the ASGI scope into a Request, reads the body,
            executes the middleware pipeline and handler, sends the response,
            and then executes any background tasks.
            
            :param scope: ASGI HTTP scope dictionary.
            :param receive: ASGI receive callable.
            :param send: ASGI send callable.
        """
        # Create a BackgroundTasks instance for this request
        background_tasks = BackgroundTasks()
        
        # Once the response has started, an error can no longer be turned
        # into an error response: a second response start is a violation of
        # the ASGI protocol. Every message goes through this wrapper so the
        # error handling below knows whether that point has been passed.
        response_started = False
        
        async def tracking_send(message: Dict[str, Any]) -> None:
            nonlocal response_started
            
            if message.get("type") == MESSAGE_HTTP_RESPONSE_START:
                response_started = True
            
            await send(message)
            return
        
        try:
            # Parse the scope into a Request object
            request = self._scope_parser.parse_http(scope)
            
            # Read the request body
            body = await self._read_body(receive, request.content_length)
            
            # Create a new request with the body and background tasks
            request = self._create_request_with_body(request, body)
            
            # Attach background tasks to the request for handler access
            request.background_tasks = background_tasks
            
            # Store the request in the scope for framework use
            self._scope_parser.set_framework_scope(scope, request)
            
            # Execute the handler with middleware
            if self._request_timeout is not None:
                response = await self._execute_with_timeout(request)
            else:
                response = await self._execute_handler(request)
            
            # Send the response
            await self._response_sender.send(tracking_send, response)
            
            # Execute background tasks after response is sent
            if background_tasks.has_tasks:
                await background_tasks.run()
            
        except ClientDisconnected:
            # Client disconnected, nothing to send
            # Still run background tasks if any were scheduled
            if background_tasks.has_tasks:
                await background_tasks.run()
            return
        
        except Exception as err:
            if response_started:
                # Part of the response is with the client. Returning without
                # completing it makes the server close the connection, which
                # is how the client learns the response was cut short.
                logger.exception(
                    "ASGI HTTP handler: %s after the response had started for %s %s, "
                    "the response is left incomplete",
                    type(err).__name__,
                    scope.get("method", "?"),
                    scope.get("path", "?"),
                )
            else:
                await self._send_error(err, scope, tracking_send)
        
        return
    
    async def _send_error(
        self,
        err: Exception,
        scope: Dict[str, Any],
        send: SendCallable,
    ) -> None:
        """
            Answer a request whose handling raised, before any response was sent.
            
            A custom handler registered on the error handler comes first. Then
            the conditions this class raises itself are answered: 413, 400 and
            the request timeout. Everything else goes to the error handler,
            which maps an exception that carries a status code to that status
            and answers the rest with 500. Without an error handler everything
            else is answered with a plain 500.
            
            :param err: The exception that was raised.
            :param scope: ASGI HTTP scope dictionary.
            :param send: ASGI send callable.
        """
        error_handler = self._error_handler
        
        if error_handler is not None and error_handler.has_handler_for(type(err)):
            await error_handler.handle_http_error(err, send, scope)
            return
        
        if isinstance(err, RequestEntityTooLarge):
            # Send 413 response. Log at warning so an operator can
            # see a sustained surge of oversize uploads without
            # dropping into the 500 catch-all branch.
            logger.warning(
                "ASGI HTTP handler: 413 for %s %s: %s",
                scope.get("method", "?"),
                scope.get("path", "?"),
                err,
            )
            response = self._create_error_response(
                status_code=413,
                message="Request Entity Too Large",
                detail=str(err) if self._debug else None,
            )
            await self._response_sender.send(send, response)

        elif isinstance(err, BadRequestBody):
            # Send 400 response. The wire body is generic when debug
            # is off — log so the operator can correlate a 400 with
            # the underlying parse failure.
            logger.warning(
                "ASGI HTTP handler: 400 for %s %s: %s",
                scope.get("method", "?"),
                scope.get("path", "?"),
                err,
            )
            response = self._create_error_response(
                status_code=400,
                message="Bad Request",
                detail=str(err) if self._debug else None,
            )
            await self._response_sender.send(send, response)

        elif isinstance(err, RequestTimeout):
            # Send 504 response for timeout. Log so a recurring
            # timeout pattern is visible in the journal. Only the
            # timeout this class enforces lands here, a TimeoutError
            # raised by the code of a handler is an ordinary error.
            logger.warning(
                "ASGI HTTP handler: 504 timeout for %s %s",
                scope.get("method", "?"),
                scope.get("path", "?"),
            )
            response = self._create_error_response(
                status_code=504,
                message="Gateway Timeout",
                detail="Request processing timed out" if self._debug else None,
            )
            await self._response_sender.send(send, response)
        
        elif error_handler is not None:
            # Exceptions that carry a status code are answered with it,
            # the rest is logged and answered with 500.
            await error_handler.handle_http_error(err, send, scope)
        
        else:
            # Send 500 response for unhandled exceptions. Log
            # unconditionally so the operator sees the traceback in
            # the journal even when ``_debug`` is off and the wire
            # response carries only the generic message.
            logger.error(
                "ASGI HTTP handler: unhandled %s for %s %s",
                type(err).__name__,
                scope.get("method", "?"),
                scope.get("path", "?"),
                exc_info=err,
            )
            detail: Optional[str] = None
            if self._debug:
                tb_lines = traceback.format_exception(type(err), err, err.__traceback__)
                tb_str = "".join(tb_lines)
                detail = f"{type(err).__name__}: {err}\n{tb_str}"

            response = self._create_error_response(
                status_code=500,
                message="Internal Server Error",
                detail=detail,
            )
            await self._response_sender.send(send, response)
        
        return
    
    async def _read_body(
        self,
        receive: ReceiveCallable,
        content_length: Optional[int],
    ) -> bytes:
        """
            Read the complete request body from receive callable.
            
            :param receive: ASGI receive callable.
            :param content_length: Expected content length.
            
            :returns: Complete body as bytes.
            
            :raises RequestEntityTooLarge: If body exceeds max size.
            :raises ClientDisconnected: If client disconnects.
        """
        body = await self._body_reader.read(receive, content_length)
        return body
    
    def _create_request_with_body(
        self,
        request: Request,
        body: bytes,
    ) -> Request:
        """
            Create a new Request with the given body.

            ``request`` was constructed before the body was read (so
            handlers can be passed a Request with the actual body
            attached). The new Request must inherit the ORIGINAL
            ASGI scope dict so that anything middleware wrote onto
            ``scope[...]`` (e.g. ``scope['auth']`` from
            :class:`AuthenticationMiddleware`,
            ``scope['session']`` from session middleware,
            ``scope['request_id']`` from the request-id middleware)
            stays visible to handlers via :attr:`Request.scope` /
            :attr:`Request.auth` etc. Without ``scope=`` here the
            new Request has a fresh empty ``_scope`` dict and every
            ``request.auth`` read on the handler side returns
            ``None`` — exactly what was happening to ``/dashboard/``
            on a freshly-logged-in admin.

            :param request: Original request without body.
            :param body: Request body bytes.

            :returns: New Request with body.
        """
        new_request = Request(
            method=request.method,
            path=request.path,
            query_string=request.raw_query_string,
            headers={name: value for name, value in request.headers.items()},
            body=body,
            scheme=request.scheme,
            host=request.host,
            port=request.port,
            scope=request.scope,
        )
        return new_request

    async def _execute_handler(self, request: Request) -> Response:
        """
            Execute the handler with middleware pipeline.
            
            :param request: The HTTP request.
            
            :returns: The HTTP response.
        """
        if self._handler is None:
            # No handler set, return 404
            response = self._create_error_response(
                status_code=404,
                message="Not Found",
                detail=None,
            )
            return response
        
        # Build the middleware chain
        handler = self._handler
        
        # Apply middleware in reverse order so they execute in order
        for middleware in reversed(self._middleware):
            handler = self._wrap_middleware(middleware, handler)
        
        # Execute the handler chain
        response = await handler(request)
        return response
    
    def _wrap_middleware(
        self,
        middleware: MiddlewareCallable,
        next_handler: HandlerCallable,
    ) -> HandlerCallable:
        """
            Wrap a middleware around a handler.
            
            :param middleware: The middleware function.
            :param next_handler: The next handler in the chain.
            
            :returns: A new handler that executes the middleware.
        """
        async def wrapped_handler(request: Request) -> Response:
            response = await middleware(request, next_handler)
            return response
        
        return wrapped_handler
    
    async def _execute_with_timeout(self, request: Request) -> Response:
        """
            Execute the handler with a timeout.
            
            :param request: The HTTP request.
            
            :returns: The HTTP response.
            
            :raises RequestTimeout: If the timeout is exceeded. RequestTimeout is
                                    an asyncio.TimeoutError. A TimeoutError raised
                                    by the handler itself is passed on unchanged
                                    and is not a RequestTimeout.
        """
        if self._request_timeout is None:
            response = await self._execute_handler(request)
        else:
            handler_task = asyncio.ensure_future(self._execute_handler(request))
            
            try:
                done, _ = await asyncio.wait(
                    [handler_task],
                    timeout=self._request_timeout,
                )
            except asyncio.CancelledError:
                # The request itself was cancelled, take the handler along
                handler_task.cancel()
                raise
            
            if handler_task not in done:
                handler_task.cancel()
                try:
                    await handler_task
                except asyncio.CancelledError:
                    # Expected: the handler was just cancelled, awaiting it only reaps the task.
                    pass
                except Exception as cancel_exc:
                    logger.debug(
                        "ASGI HTTP handler: handler raised while being cancelled: %s",
                        cancel_exc,
                    )
                
                raise RequestTimeout(self._request_timeout)
            
            response = handler_task.result()
        
        return response
    
    def _create_error_response(
        self,
        status_code: int,
        message: str,
        detail: Optional[str] = None,
    ) -> Response:
        """
            Create an error response.
            
            :param status_code: HTTP status code.
            :param message: Error message.
            :param detail: Optional error detail (shown in debug mode).
            
            :returns: Error Response object.
        """
        # Build the response body
        if detail is not None:
            body_text = f"{message}\n\n{detail}"
        else:
            body_text = message
        
        body_bytes = body_text.encode("utf-8")
        
        headers = {
            "Content-Type": "text/plain; charset=utf-8",
            "Content-Length": str(len(body_bytes)),
        }
        
        response = Response(
            status_code=status_code,
            headers=headers,
            body=body_bytes,
        )
        
        return response
