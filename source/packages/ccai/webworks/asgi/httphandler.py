"""
    ASGI HTTP Handler module.
    
    This module provides the HTTPHandler class that handles HTTP request/response
    cycles over ASGI, integrating scope parsing, body reading, response sending,
    middleware execution, and background tasks.
"""

import asyncio
import logging
import traceback

from typing import Any, Awaitable, Callable, Dict, List, Optional, Union

from ccai.webworks.asgi.scopeparser import ScopeParser
from ccai.webworks.asgi.bodyreader import BodyReader
from ccai.webworks.asgi.responsesender import ResponseSender
from ccai.webworks.asgi.backgroundtasks import BackgroundTasks
from ccai.webworks.asgi.constants import (
    SCOPE_REQUEST,
    SCOPE_ROUTE,
    SCOPE_PATH_PARAMS,
    HTTP_STATUS_PHRASES,
)
from ccai.webworks.asgi.exceptions import (
    ASGIError,
    BadRequestBody,
    ClientDisconnected,
    RequestEntityTooLarge,
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
    ):
        """
            Construct an HTTPHandler instance.
            
            :param scope_parser: ScopeParser instance for parsing ASGI scopes.
            :param body_reader: BodyReader instance for reading request bodies.
            :param response_sender: ResponseSender instance for sending responses.
            :param debug: If True, include stack traces in error responses.
            :param request_timeout: Optional timeout in seconds for request handling.
        """
        if scope_parser is None:
            self._scope_parser = ScopeParser()
        else:
            self._scope_parser = scope_parser
        
        if body_reader is None:
            self._body_reader = BodyReader()
        else:
            self._body_reader = body_reader
        
        if response_sender is None:
            self._response_sender = ResponseSender()
        else:
            self._response_sender = response_sender
        
        self._debug = debug
        self._request_timeout = request_timeout
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
            await self._response_sender.send(send, response)
            
            # Execute background tasks after response is sent
            if background_tasks.has_tasks:
                await background_tasks.run()
            
        except ClientDisconnected:
            # Client disconnected, nothing to send
            # Still run background tasks if any were scheduled
            if background_tasks.has_tasks:
                await background_tasks.run()
            return
        
        except RequestEntityTooLarge as err:
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

        except BadRequestBody as err:
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

        except asyncio.TimeoutError:
            # Send 504 response for timeout. Log so a recurring
            # timeout pattern is visible in the journal.
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
        
        except Exception as err:
            # Send 500 response for unhandled exceptions. Log
            # unconditionally so the operator sees the traceback in
            # the journal even when ``_debug`` is off and the wire
            # response carries only the generic message.
            logger.exception(
                "ASGI HTTP handler: unhandled %s for %s %s",
                type(err).__name__,
                scope.get("method", "?"),
                scope.get("path", "?"),
            )
            detail: Optional[str] = None
            if self._debug:
                detail = f"{type(err).__name__}: {err}\n{traceback.format_exc()}"

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
            
            :raises asyncio.TimeoutError: If the timeout is exceeded.
        """
        if self._request_timeout is None:
            response = await self._execute_handler(request)
        else:
            response = await asyncio.wait_for(
                self._execute_handler(request),
                timeout=self._request_timeout,
            )
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
