"""
    Dispatcher module.
    
    This module provides the Dispatcher class that orchestrates routing
    and middleware execution for incoming HTTP requests.
    
    The Dispatcher is the central component that:
    - Fires the request lifecycle hooks of the application's extensions
      around every request (when any has a callback)
    - Executes the middleware pipeline around routing and the handler
    - Routes requests to find matching handlers
    - Populates request path parameters from route matches
    - Enforces the access policy of the matched endpoint
    - Handles HTTP exceptions and converts them to responses
    - Handles unhandled exceptions with appropriate error responses
    
    Example:
        router = Router()
        pipeline = MiddlewarePipeline()
        dispatcher = Dispatcher(router, pipeline)
        
        response = dispatcher.dispatch(request)
"""

import asyncio
import concurrent.futures
import contextvars
import inspect
import logging
import threading
import traceback
import urllib.parse

from typing import Any, Awaitable, Callable, List, Optional, Tuple, TYPE_CHECKING, Union

from ccai.webworks.endpoints.descriptor import ENDPOINT_BLUEPRINT_NAME_EXTRA
from ccai.webworks.routing.request import Request
from ccai.webworks.routing.response import (
    Response,
    JSONResponse,
    HTMLResponse,
    RedirectResponse,
)
from ccai.webworks.routing.router import Router, RouteMatch, canonicalize_path
from ccai.webworks.routing.middleware import MiddlewarePipeline
from ccai.webworks.routing.middlewarecontext import MiddlewareContext
from ccai.webworks.routing.middlewareregistry import MiddlewareRegistry
from ccai.webworks.routing.exceptions import (
    Forbidden,
    HTTPException,
    MethodNotAllowed,
    NotFound,
    Unauthorized,
)
from ccai.webworks.security.accesspolicy import AccessPolicy
from ccai.webworks.security.securitycontext import (
    SECURITY_CONTEXT_SCOPE_KEY,
    SecurityContext,
)
from ccai.webworks.templating.response import (
    StreamingTemplateResponse,
    TemplateResponse,
)

if TYPE_CHECKING:
    from ccai.webworks.extensibility.requestlifecyclehooks import RequestLifecycleHooks


#: Key in :attr:`EndpointDescriptor.extras` naming the blueprint a route
#: belongs to. When a :class:`MiddlewareRegistry` is given to the dispatcher,
#: middleware registered at ``scope="blueprint"`` under that name runs for
#: the route. :class:`Blueprint` and :class:`RestBlueprint` record their
#: class name there (see
#: :data:`ccai.webworks.endpoints.descriptor.ENDPOINT_BLUEPRINT_NAME_EXTRA`).
BLUEPRINT_NAME_EXTRA = ENDPOINT_BLUEPRINT_NAME_EXTRA


# Event loop of the dispatcher that moved the current handler call to a
# worker thread. Set around the call, so it is visible in the worker
# thread through the copied context and nowhere else.
_application_loop: "contextvars.ContextVar[Optional[asyncio.AbstractEventLoop]]" = contextvars.ContextVar(
    "webworks_application_loop", default=None
)


def get_application_loop() -> Optional[asyncio.AbstractEventLoop]:
    """
        Get the event loop of the dispatcher that is running the current
        handler on a worker thread.

        ``dispatch_async`` runs a handler that is not a coroutine function
        on a worker thread. Such a handler has no running event loop of its
        own, yet it may need to drive a coroutine that belongs to the
        application's loop -- a database pool or a session store created on
        that loop. It can hand the coroutine to the loop this function
        returns with ``asyncio.run_coroutine_threadsafe(coro, loop)`` and
        wait for the result; the loop is free while the handler runs.

        :returns: The dispatcher's event loop while a handler runs on a
                  worker thread on its behalf, otherwise None.
    """
    rtnval = _application_loop.get()
    return rtnval


#: Characters left as they are when a path is written into a ``Location``
#: header. Everything else is percent-encoded, so a path that was decoded
#: from ``%0d%0a`` can not start a new header line.
_LOCATION_SAFE_CHARS = "/:@!$&'()*+,;=-._~"


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
        - Publishing the canonical request path before anything compares it
        - Executing the global middleware around routing, so middleware
          sees every request including the ones no route matches
        - Matching requests to registered routes
        - Populating request.path_params from the route match
        - Enforcing the access policy of the matched endpoint
        - Executing the blueprint and route middleware with the matched handler
        - Converting HTTPExceptions to appropriate responses
        - Handling unhandled exceptions with 500 responses

        Access policy enforcement: when the matched endpoint carries an
        :class:`AccessPolicy` -- from ``@require_auth`` / ``@require_roles`` /
        ``@require_scopes``, from ``attach_at(access_policy=...)`` or from a
        class-level default -- the handler runs only if the authentication
        context on the request satisfies it. A request without a usable
        authentication context is answered ``401``; an authenticated request
        that lacks a required role or scope is answered ``403``. The check
        fails closed: a policy that can not be evaluated denies the request.
        Endpoints without a policy stay public unless ``default_policy`` is
        set.
        
        Configuration options:
        - debug: If True, include stack traces in error responses.
        - error_format: Format for error responses ("json", "html", "text").
        
        :param router: Router for URL matching.
        :param pipeline: MiddlewarePipeline for request processing.
        :param debug: If True, include stack traces in error responses.
        :param error_format: Format for error responses ("json", "html", "text").
        :param registry: Optional MiddlewareRegistry. Its global middleware
            runs after the pipeline's; its blueprint and route middleware
            run for the routes they are registered for.
        :param default_policy: AccessPolicy applied to endpoints that declare
            none. ``None`` leaves such endpoints public.
        :param auth_challenge: Value of the ``WWW-Authenticate`` header sent
            with a ``401`` response.
        :param offload_sync_handlers: If True, ``dispatch_async`` runs
            handlers that are not coroutine functions on a worker thread so
            a blocking handler does not stall the event loop.
        :param config: Application configuration made available to
            middleware through ``request.middleware_context.config``.
        :param route_pipeline: MiddlewarePipeline that runs for every
            matched route, after routing. Its middleware can read the
            matched descriptor from ``request.middleware_context``, which
            the middleware of ``pipeline`` can not, because that runs
            before a route is known.
        :param request_hooks: The application's request lifecycle hooks
            (``RequestLifecycleHooks``). Fired around every request, the
            same way by ``dispatch`` and ``dispatch_async``:
            ``before_first_request`` once, ``before_request`` (a returned
            response short-circuits the pipeline), ``on_request_error``
            before an unhandled exception becomes the 500 response,
            ``after_request`` (may replace the response) and
            ``teardown_request`` always, last. A failing
            ``before_first_request``, ``before_request`` or ``after_request``
            callback makes the request a 500. When no request hook has a
            callback the request takes the plain path and pays nothing more
            than that check.
        :param on_first_request: Callable run once, before the first request
            is processed (before ``before_first_request``). A web
            application passes the one that fires ``on_app_ready`` when the
            server did not start it through the ASGI lifespan.
        
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
        error_format: str = "json",
        registry: Optional[MiddlewareRegistry] = None,
        default_policy: Optional[AccessPolicy] = None,
        auth_challenge: str = "Bearer",
        offload_sync_handlers: bool = True,
        config: Optional[Any] = None,
        route_pipeline: Optional[MiddlewarePipeline] = None,
        request_hooks: Optional["RequestLifecycleHooks"] = None,
        on_first_request: Optional[Callable[[], None]] = None
    ):
        """
            Construct a Dispatcher.
            
            :param router: Router for URL matching.
            :param pipeline: MiddlewarePipeline for request processing.
            :param debug: If True, include stack traces in error responses.
            :param error_format: Format for error responses ("json", "html", "text").
            :param registry: Optional MiddlewareRegistry of scoped middleware.
            :param default_policy: AccessPolicy for endpoints that declare none.
            :param auth_challenge: ``WWW-Authenticate`` value for ``401`` responses.
            :param offload_sync_handlers: If True, run non-coroutine handlers
                on a worker thread in ``dispatch_async``.
            :param config: Application configuration for the middleware context.
            :param route_pipeline: MiddlewarePipeline run for every matched route.
            :param request_hooks: The request lifecycle hooks to fire.
            :param on_first_request: Callable run once, before the first request.
        """
        self._router = router
        self._pipeline = pipeline if pipeline is not None else MiddlewarePipeline()
        self._debug = debug
        self._error_format = error_format
        self._registry = registry
        self._default_policy = default_policy
        self._auth_challenge = auth_challenge
        self._offload_sync_handlers = offload_sync_handlers
        self._config = config
        self._route_pipeline = route_pipeline if route_pipeline is not None else MiddlewarePipeline()

        self._request_hooks = request_hooks
        self._on_first_request = on_first_request

        # The first request runs the first-request work (on_first_request,
        # before_first_request) once; the flag is read without the lock on
        # every request and only the first ones take the lock.
        self._first_request_pending = request_hooks is not None or on_first_request is not None
        self._first_request_lock = threading.Lock()
        return

    @property
    def request_hooks(self) -> Optional["RequestLifecycleHooks"]:
        """
            Get the request lifecycle hooks the dispatcher fires.

            :returns: RequestLifecycleHooks instance or None.
        """
        return self._request_hooks
    
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
    def route_pipeline(self) -> MiddlewarePipeline:
        """
            Get the middleware pipeline that runs for every matched route.

            Middleware added here runs after routing, inside the global
            pipeline and before the blueprint and route middleware of the
            registry. ``request.middleware_context.endpoint_descriptor``
            is the matched descriptor when it runs.

            :returns: MiddlewarePipeline instance.
        """
        return self._route_pipeline

    @property
    def registry(self) -> Optional[MiddlewareRegistry]:
        """
            Get the registry of scoped middleware.

            :returns: MiddlewareRegistry instance or None.
        """
        return self._registry

    @registry.setter
    def registry(self, value: Optional[MiddlewareRegistry]) -> None:
        """
            Set the registry of scoped middleware.

            :param value: MiddlewareRegistry instance or None.
        """
        self._registry = value
        return

    @property
    def default_policy(self) -> Optional[AccessPolicy]:
        """
            Get the access policy applied to endpoints that declare none.

            :returns: AccessPolicy instance, or None when such endpoints
                      are public.
        """
        return self._default_policy

    @default_policy.setter
    def default_policy(self, value: Optional[AccessPolicy]) -> None:
        """
            Set the access policy applied to endpoints that declare none.

            :param value: AccessPolicy instance, or None to leave such
                          endpoints public.
        """
        self._default_policy = value
        return

    @property
    def auth_challenge(self) -> str:
        """
            Get the ``WWW-Authenticate`` value sent with ``401`` responses.

            :returns: The challenge string.
        """
        return self._auth_challenge

    @auth_challenge.setter
    def auth_challenge(self, value: str) -> None:
        """
            Set the ``WWW-Authenticate`` value sent with ``401`` responses.

            :param value: The challenge string.
        """
        self._auth_challenge = value
        return
    
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
            Dispatch a request through middleware and routing.
            
            This method:
            1. Publishes the canonical request path
            2. Executes the global middleware around the remaining steps
            3. Routes the request to find a matching handler; answers 404,
               405, an automatic ``OPTIONS`` or a trailing slash redirect
               when there is none
            4. Populates request.path_params from the route match
            5. Executes the blueprint and route middleware
            6. Enforces the endpoint's access policy and calls the handler
            7. Converts HTTPExceptions to appropriate responses
            8. Handles unhandled exceptions with 500 responses

            When request lifecycle hooks have callbacks, they are fired
            around these steps (see :meth:`_dispatch_with_hooks`).
            
            :param request: The incoming Request.
            
            :returns: Response from handler or error response.
        """
        if self._uses_request_hooks() is True:
            response = self._dispatch_with_hooks(request)
        else:
            response, _ = self._run_pipeline(request)
            response = self._finalize_response(request, response)

        return response
    
    async def dispatch_async(self, request: Request) -> Response:
        """
            Dispatch a request asynchronously.
            
            This method is the async version of dispatch() and supports
            async handlers and middleware. Handlers that are not coroutine
            functions run on a worker thread unless the dispatcher was
            constructed with ``offload_sync_handlers=False``. The request
            lifecycle hooks are fired exactly as :meth:`dispatch` fires them.
            
            :param request: The incoming Request.
            
            :returns: Response from handler or error response.
        """
        if self._uses_request_hooks() is True:
            response = await self._dispatch_with_hooks_async(request)
        else:
            response, _ = await self._run_pipeline_async(request)
            response = self._finalize_response(request, response)

        return response

    def _uses_request_hooks(self) -> bool:
        """
            Decide whether a request takes the path that fires the request
            lifecycle hooks.

            It does while the first-request work is pending, and whenever a
            request hook has a callback. Without either -- an application
            without extensions -- the answer costs a flag and a size check.

            :returns: True when the hooks path is taken.
        """
        rtnval = self._first_request_pending

        if rtnval is False and self._request_hooks is not None:
            rtnval = self._request_hooks.has_callbacks()

        return rtnval

    def _run_pipeline(self, request: Request) -> Tuple[Any, Optional[Exception]]:
        """
            Run the global middleware, routing, the scoped middleware and
            the handler, converting what they raise into a response.

            An exception nothing else handled is reported to the
            ``on_request_error`` hook before it becomes the 500 response.

            :param request: The incoming Request.

            :returns: The response, and the unhandled exception that became
                      it (None when there was none).
        """
        error: Optional[Exception] = None

        try:
            self._prepare_request(request)

            pipeline = self._get_global_pipeline()

            # Routing happens inside the innermost callable so that
            # middleware runs for every request, matched or not.
            response = pipeline.execute(request, self._route_and_handle)

        except HTTPException as exc:
            # HTTPException raised by middleware
            response = self._handle_http_exception(exc)

        except Exception as exc:
            # Unhandled exception
            error = exc
            self._fire_request_error(request, exc)
            response = self._handle_unhandled_exception(exc)

        rtnval = (response, error)
        return rtnval

    async def _run_pipeline_async(self, request: Request) -> Tuple[Any, Optional[Exception]]:
        """
            Async version of :meth:`_run_pipeline`.

            :param request: The incoming Request.

            :returns: The response, and the unhandled exception that became
                      it (None when there was none).
        """
        error: Optional[Exception] = None

        try:
            self._prepare_request(request)

            pipeline = self._get_global_pipeline()

            # Routing happens inside the innermost callable so that
            # middleware runs for every request, matched or not.
            response = await pipeline.execute_async(
                request, self._route_and_handle_async
            )

        except HTTPException as exc:
            # HTTPException raised by middleware
            response = self._handle_http_exception(exc)

        except Exception as exc:
            # Unhandled exception
            error = exc
            self._fire_request_error(request, exc)
            response = self._handle_unhandled_exception(exc)

        rtnval = (response, error)
        return rtnval

    def _dispatch_with_hooks(self, request: Request) -> Response:
        """
            Dispatch a request with the request lifecycle hooks fired around
            the pipeline:

            1. the canonical path is published, so the hooks see it;
            2. the first-request work runs, once (:meth:`_run_first_request`);
            3. ``before_request`` -- a response it returns is sent instead of
               running the pipeline;
            4. the pipeline (:meth:`_run_pipeline`; ``on_request_error`` is
               fired there for an unhandled exception);
            5. ``after_request`` -- may replace the response;
            6. ``teardown_request`` -- always, with the response and the
               exception that ended the request.

            A hook failure in steps 2, 3 or 5 is reported to
            ``on_request_error`` and answered with 500. ``ConfigurationError``
            and ``SemanticError`` are not caught: teardown still runs, then
            they propagate.

            :param request: The incoming Request.

            :returns: The response to send.
        """
        hooks = self._request_hooks
        response: Any = None
        error: Optional[Exception] = None

        try:
            try:
                self._prepare_request(request)
                self._run_first_request(request)

                short_circuit = None
                if hooks is not None:
                    short_circuit = hooks.fire_before_request(request)

                if short_circuit is not None:
                    response = self._convert_result(short_circuit)
                else:
                    response, error = self._run_pipeline(request)

                if hooks is not None:
                    response = hooks.fire_after_request(request, response)

            except Exception as exc:
                error = exc
                self._fire_request_error(request, exc)
                response = self._handle_unhandled_exception(exc)

            response = self._finalize_response(request, response)

        finally:
            if hooks is not None:
                hooks.fire_teardown_request(request, response, error)

        return response

    async def _dispatch_with_hooks_async(self, request: Request) -> Response:
        """
            Async version of :meth:`_dispatch_with_hooks`.

            :param request: The incoming Request.

            :returns: The response to send.
        """
        hooks = self._request_hooks
        response: Any = None
        error: Optional[Exception] = None

        try:
            try:
                self._prepare_request(request)
                self._run_first_request(request)

                short_circuit = None
                if hooks is not None:
                    short_circuit = hooks.fire_before_request(request)

                if short_circuit is not None:
                    response = self._convert_result(short_circuit)
                else:
                    response, error = await self._run_pipeline_async(request)

                if hooks is not None:
                    response = hooks.fire_after_request(request, response)

            except Exception as exc:
                error = exc
                self._fire_request_error(request, exc)
                response = self._handle_unhandled_exception(exc)

            response = self._finalize_response(request, response)

        finally:
            if hooks is not None:
                hooks.fire_teardown_request(request, response, error)

        return response

    def _run_first_request(self, request: Request) -> None:
        """
            Run the first-request work once: the ``on_first_request``
            callable, then the ``before_first_request`` hook.

            Concurrent first requests -- threads, or tasks of the event loop
            -- are serialised: the first runs the work and the others wait
            until it has finished. The work counts as done even when it
            failed, so it never runs twice.

            :param request: The first request.

            :raises HookExecutionError: If a ``before_first_request``
                callback raised.
        """
        if self._first_request_pending is False:
            return

        with self._first_request_lock:
            if self._first_request_pending is False:
                return

            try:
                if self._on_first_request is not None:
                    self._on_first_request()

                if self._request_hooks is not None:
                    self._request_hooks.fire_before_first_request(request)
            finally:
                self._first_request_pending = False

        return

    def _fire_request_error(self, request: Request, exc: Exception) -> None:
        """
            Tell the ``on_request_error`` hook about an unhandled exception,
            before it is turned into the 500 response.

            :param request: The request being processed.
            :param exc: The unhandled exception.
        """
        hooks = self._request_hooks

        if hooks is not None and hooks.has_callbacks() is True:
            hooks.fire_on_request_error(request, exc)

        return

    def _prepare_request(self, request: Request) -> None:
        """
            Publish the canonical path and an initial middleware context on
            the request before any middleware runs.

            The path is normalised once, here, so middleware, the router and
            the access policy check all compare the same spelling. A path
            without a canonical form (one with a ``..`` segment) is left as
            it was sent; the router matches nothing for it.

            :param request: The incoming Request.
        """
        canonical_path = canonicalize_path(request.path)

        if canonical_path is not None and canonical_path != request.path:
            request.path = canonical_path

        # No route is matched yet, so the context carries no descriptor.
        request.middleware_context = MiddlewareContext(
            endpoint_descriptor=None,
            scope="global",
            config=self._config
        )

        return

    def _get_global_pipeline(self) -> MiddlewarePipeline:
        """
            Get the middleware that runs for every request: the dispatcher's
            own pipeline followed by the registry's global middleware.

            :returns: The MiddlewarePipeline to execute around routing.
        """
        rtnval = self._pipeline

        if self._registry is not None:
            global_entries = self._registry.get_middleware_by_scope("global")

            if len(global_entries) > 0:
                rtnval = MiddlewarePipeline()
                rtnval.extend(self._pipeline)
                rtnval.extend(global_entries)

        return rtnval

    def _get_scoped_pipeline(self, match: RouteMatch) -> Optional[MiddlewarePipeline]:
        """
            Get the middleware that runs after routing for a matched
            route: the route pipeline, then the blueprint middleware and
            the route middleware registered for the route.

            :param match: The route match.

            :returns: A MiddlewarePipeline, or None when no such
                      middleware applies to the route.
        """
        rtnval: Optional[MiddlewarePipeline] = None

        entries = list(self._route_pipeline)

        if self._registry is not None:
            extras = getattr(match.descriptor, "extras", None)
            blueprint_name = None
            if isinstance(extras, dict):
                blueprint_name = extras.get(BLUEPRINT_NAME_EXTRA)

            if blueprint_name is not None:
                entries.extend(
                    self._registry.get_middleware_by_scope("blueprint", blueprint_name)
                )

            entries.extend(
                self._registry.get_middleware_by_scope("route", match.matched_path)
            )

        if len(entries) > 0:
            rtnval = MiddlewarePipeline()
            rtnval.extend(entries)

        return rtnval

    def _bind_match(self, request: Request, match: RouteMatch) -> None:
        """
            Record a route match on the request: the path parameters and a
            middleware context that carries the matched descriptor.

            :param request: The incoming Request.
            :param match: The route match.
        """
        # Populate request.path_params from the route match
        request.path_params = match.path_params

        request.middleware_context = MiddlewareContext(
            endpoint_descriptor=match.descriptor,
            scope="route",
            config=self._config
        )

        return

    def _resolve_route(self, request: Request) -> Union[RouteMatch, Response]:
        """
            Find the route for a request, or the response that answers a
            request no handler is registered for.

            :param request: The incoming Request.

            :returns: The RouteMatch, or a Response for an automatic
                      ``OPTIONS`` answer or a trailing slash redirect.

            :raises MethodNotAllowed: If the path is registered for other
                methods only.
            :raises NotFound: If no route matches the path.
        """
        match = self._router.match(request)

        if match is not None:
            return match

        # Check if the path exists with other methods before returning 404
        registered_methods = self._router.get_allowed_methods(request.path)

        if len(registered_methods) > 0:
            allowed_methods = self._get_allow_list(registered_methods)

            if request.method == "OPTIONS":
                # No OPTIONS handler is registered: answer with the
                # methods the path does support.
                response = Response(
                    status_code=204,
                    headers={"Allow": ", ".join(allowed_methods)}
                )
                return response

            raise MethodNotAllowed(allowed=allowed_methods)

        redirect_path = self._router.get_redirect_path(request.path, request.method)

        if redirect_path is not None:
            response = self._build_slash_redirect(request, redirect_path)
            return response

        raise NotFound()

    def _get_allow_list(self, registered_methods: List[str]) -> List[str]:
        """
            Get the methods a path supports: the registered ones plus the
            ones the framework answers automatically (``HEAD`` wherever
            ``GET`` is registered, and ``OPTIONS``).

            :param registered_methods: Methods with a registered handler.

            :returns: Sorted list of supported method names.
        """
        supported = set(registered_methods)

        if "GET" in supported:
            supported.add("HEAD")

        supported.add("OPTIONS")

        rtnval = sorted(supported)

        return rtnval

    def _build_slash_redirect(self, request: Request, redirect_path: str) -> Response:
        """
            Build the permanent redirect to the spelling of a path that is
            registered, keeping the query string.

            :param request: The incoming Request.
            :param redirect_path: The canonical path of the registered route.

            :returns: A 308 RedirectResponse.
        """
        location = urllib.parse.quote(redirect_path, safe=_LOCATION_SAFE_CHARS)

        query_string = request.query_string
        if query_string:
            location = f"{location}?{query_string}"

        # 308 keeps the method and the body, so a redirected POST is
        # repeated as a POST.
        rtnval = RedirectResponse(location, status_code=308)

        return rtnval

    def _route_and_handle(self, request: Request) -> Response:
        """
            Innermost callable of the global pipeline: route the request,
            then run the scoped middleware, the access policy check and the
            handler.

            HTTPExceptions are converted here so the middleware above sees
            the error response -- a 404 still receives CORS headers and is
            still logged.

            :param request: The incoming Request.

            :returns: Response from the handler or an error response.
        """
        try:
            resolution = self._resolve_route(request)

            if isinstance(resolution, RouteMatch):
                match = resolution

                self._bind_match(request, match)

                def invoke(req: Request) -> Response:
                    return self._authorize_and_invoke(req, match)

                scoped_pipeline = self._get_scoped_pipeline(match)

                if scoped_pipeline is None:
                    response = invoke(request)
                else:
                    response = scoped_pipeline.execute(request, invoke)
            else:
                response = resolution

        except HTTPException as exc:
            response = self._handle_http_exception(exc)

        return response

    async def _route_and_handle_async(self, request: Request) -> Response:
        """
            Async version of :meth:`_route_and_handle`.

            :param request: The incoming Request.

            :returns: Response from the handler or an error response.
        """
        try:
            resolution = self._resolve_route(request)

            if isinstance(resolution, RouteMatch):
                match = resolution

                self._bind_match(request, match)

                async def invoke(req: Request) -> Response:
                    return await self._authorize_and_invoke_async(req, match)

                scoped_pipeline = self._get_scoped_pipeline(match)

                if scoped_pipeline is None:
                    response = await invoke(request)
                else:
                    response = await scoped_pipeline.execute_async(request, invoke)
            else:
                response = resolution

        except HTTPException as exc:
            response = self._handle_http_exception(exc)

        return response

    def _authorize_and_invoke(self, request: Request, match: RouteMatch) -> Response:
        """
            Enforce the matched endpoint's access policy, then call its
            handler and convert the result to a response.

            :param request: The incoming Request.
            :param match: The route match.

            :returns: Response from the handler or an error response.
        """
        try:
            self._enforce_access_policy(request, match)

            result = match.handler(request)

            # A coroutine handler can not be awaited from synchronous
            # dispatch, so it is driven to completion here.
            if inspect.isawaitable(result):
                result = self._run_awaitable(result)

            response = self._convert_result(result)

        except HTTPException as exc:
            response = self._handle_http_exception(exc)

        return response

    async def _authorize_and_invoke_async(self, request: Request, match: RouteMatch) -> Response:
        """
            Async version of :meth:`_authorize_and_invoke`.

            :param request: The incoming Request.
            :param match: The route match.

            :returns: Response from the handler or an error response.
        """
        try:
            self._enforce_access_policy(request, match)

            handler = match.handler

            if self._offload_sync_handlers and not self._is_coroutine_handler(handler):
                # A handler that is not a coroutine function may block
                # (database call, file read, multipart parse). On the
                # event loop that would stall every other request. The
                # loop is published for the handler, which runs with a
                # copy of this context.
                loop_token = _application_loop.set(asyncio.get_running_loop())
                try:
                    result = await asyncio.to_thread(handler, request)
                finally:
                    _application_loop.reset(loop_token)
            else:
                result = handler(request)

            if inspect.isawaitable(result):
                result = await result

            response = self._convert_result(result)

        except HTTPException as exc:
            response = self._handle_http_exception(exc)

        return response

    def _is_coroutine_handler(self, handler: Callable) -> bool:
        """
            Decide whether calling a handler returns a coroutine straight
            away, so it can be called on the event loop.

            Looks through ``functools.wraps`` wrappers and at the
            ``__call__`` of callable objects.

            :param handler: The endpoint handler.

            :returns: True if the handler is a coroutine function.
        """
        rtnval = False

        try:
            unwrapped = inspect.unwrap(handler)
        except ValueError:
            unwrapped = handler

        if inspect.iscoroutinefunction(unwrapped):
            rtnval = True
        elif not inspect.isfunction(unwrapped) and not inspect.ismethod(unwrapped):
            call_method = getattr(unwrapped, "__call__", None)
            if call_method is not None and inspect.iscoroutinefunction(call_method):
                rtnval = True

        return rtnval

    def _run_awaitable(self, awaitable: Awaitable) -> Any:
        """
            Drive an awaitable to completion from synchronous code.

            When the calling thread has no running event loop the awaitable
            runs on a new loop here. When it has one -- ``dispatch`` was
            called from async code -- blocking on that loop would deadlock
            it, so the awaitable runs on a new loop in a helper thread.

            :param awaitable: The awaitable a handler returned.

            :returns: The result of the awaitable.
        """
        async def drive() -> Any:
            return await awaitable

        try:
            asyncio.get_running_loop()
            loop_is_running = True
        except RuntimeError:
            loop_is_running = False

        if loop_is_running:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(asyncio.run, drive())
                rtnval = future.result()
        else:
            rtnval = asyncio.run(drive())

        return rtnval

    def _convert_result(self, result: Any) -> Response:
        """
            Convert the value a handler returned into a response.

            If the handler returns a known response shape (Response,
            TemplateResponse, StreamingTemplateResponse), it is used
            directly. The auth blueprints return the
            ``{status, body, content_type}`` dict shape -- that is translated
            so the wire response carries the embedded status code and any
            attached headers (e.g. ``Set-Cookie`` from
            ``establish_session``). Everything else is wrapped in a default
            ``JSONResponse``.

            :param result: The handler return value.

            :returns: The response to send.
        """
        if isinstance(result, _RESPONSE_TYPES):
            rtnval = result
        elif _is_auth_response_dict(result):
            rtnval = _auth_response_dict_to_response(result)
        else:
            rtnval = JSONResponse(result)

        return rtnval

    def _get_route_policies(self, match: RouteMatch) -> List[Any]:
        """
            Get the access policies a request must satisfy to reach the
            handler of a matched route.

            The policy is read from the matched descriptor, never looked up
            by the request path, so every spelling of a path that reaches
            the handler is checked against the same policy.

            :param match: The route match.

            :returns: The policies to check; empty when the endpoint is public.
        """
        rtnval: List[Any] = []

        constraints = getattr(match.descriptor, "constraints", None)

        policy = None
        roles: Any = None
        scopes: Any = None

        if isinstance(constraints, dict):
            policy = constraints.get("access_policy")
            roles = constraints.get("roles")
            scopes = constraints.get("scopes")
        elif constraints is not None:
            policy = getattr(constraints, "access_policy", None)
            roles = getattr(constraints, "roles", None)
            scopes = getattr(constraints, "scopes", None)

        if policy is not None:
            rtnval.append(policy)

        # Roles and scopes can also be listed on the constraints directly.
        # They are reported in the security map, so they are enforced too.
        listed_roles = tuple(roles) if roles else tuple()
        listed_scopes = tuple(scopes) if scopes else tuple()

        if len(listed_roles) > 0 or len(listed_scopes) > 0:
            rtnval.append(
                AccessPolicy(roles=listed_roles, scopes=listed_scopes, require_auth=True)
            )

        if len(rtnval) == 0 and self._default_policy is not None:
            rtnval.append(self._default_policy)

        return rtnval

    def _get_auth_subject(self, request: Request) -> Optional[Any]:
        """
            Get the authenticated subject of a request.

            The subject is the :class:`AuthenticationContext` the
            authentication middleware stored on the scope
            (``request.auth``), or the :class:`SecurityContext` the
            :class:`SecurityMiddleware` stored there. An expired context is
            not a subject.

            :param request: The incoming Request.

            :returns: The subject, or None for an unauthenticated request.
        """
        rtnval: Optional[Any] = getattr(request, "auth", None)

        if rtnval is None:
            scope = getattr(request, "scope", None)

            if isinstance(scope, dict):
                candidate = scope.get(SECURITY_CONTEXT_SCOPE_KEY)

                if isinstance(candidate, SecurityContext) and candidate.is_authenticated is True:
                    rtnval = candidate

        if rtnval is not None and getattr(rtnval, "is_expired", False) is not False:
            rtnval = None

        return rtnval

    def _enforce_access_policy(self, request: Request, match: RouteMatch) -> None:
        """
            Refuse the request unless it satisfies the access policy of the
            matched endpoint.

            :param request: The incoming Request.
            :param match: The route match.

            :raises Unauthorized: If the endpoint requires more than the
                request offers and the request is not authenticated.
            :raises Forbidden: If the request is authenticated but does not
                satisfy the endpoint's policy.
        """
        policies = self._get_route_policies(match)

        if len(policies) > 0:
            subject = self._get_auth_subject(request)

            for policy in policies:
                allowed = False

                try:
                    allowed = policy.check(subject) is True
                except Exception:
                    # Fail closed: a policy that can not be evaluated
                    # grants nothing.
                    logger.exception(
                        "Access policy of %s could not be evaluated; denying the request",
                        match.matched_path
                    )

                if not allowed:
                    if subject is None:
                        logger.debug(
                            "Access denied for %s %s: authentication required",
                            request.method, match.matched_path
                        )
                        raise Unauthorized(
                            "Authentication required",
                            headers={"WWW-Authenticate": self._auth_challenge}
                        )

                    logger.debug(
                        "Access denied for %s %s: policy not satisfied",
                        request.method, match.matched_path
                    )
                    raise Forbidden("Access denied")

        return

    def _finalize_response(self, request: Request, response: Any) -> Any:
        """
            Apply the rules that hold for every response.

            A response to ``HEAD`` carries the status and headers of the
            ``GET`` response but never a body.

            :param request: The incoming Request.
            :param response: The response produced by the pipeline.

            :returns: The response to send.
        """
        rtnval = response

        if request.method == "HEAD":
            if isinstance(response, Response):
                rtnval = response.without_body()
            elif hasattr(response, "status_code") and hasattr(response, "headers"):
                # Template responses and other duck-typed shapes
                rtnval = Response(
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    body=b""
                )

        return rtnval
    
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
