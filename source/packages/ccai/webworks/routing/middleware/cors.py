"""
    CORS middleware module.

    This module provides the CORSMiddleware class for handling Cross-Origin
    Resource Sharing (CORS) in the middleware pipeline. It supports preflight
    OPTIONS requests, origin matching (including wildcard), and configurable
    CORS headers.

.. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

from typing import Any, Awaitable, Callable, Dict, List, Optional

from ccai.webworks.routing.request import Request
from ccai.webworks.routing.response import Response


WILDCARD_ORIGIN = "*"


class CORSMiddleware:
    """
        Cross-Origin Resource Sharing middleware.

        Handles preflight requests by returning a 204 response with
        appropriate CORS headers (short-circuiting the pipeline). For regular
        requests from allowed origins, CORS response headers are added to the
        response returned by the next handler. Requests from disallowed origins
        receive no CORS headers.

        A preflight request is an ``OPTIONS`` request that carries both an
        ``Origin`` and an ``Access-Control-Request-Method`` header. Any other
        ``OPTIONS`` request is an ordinary request and reaches the handler.

        When origins are allow-listed the response depends on the ``Origin``
        of the request, so ``Vary: Origin`` is added to every response --
        including the ones that receive no CORS headers. Without it a shared
        cache could replay a response approved for one origin to another.

        The wildcard origin can not be combined with credentials: reflecting
        whatever origin asks, with ``Access-Control-Allow-Credentials: true``,
        would let any site read authenticated responses. Credentialed CORS
        needs an explicit list of origins.

        The middleware runs in the synchronous pipeline through ``__call__``
        and in the asynchronous pipeline through ``call_async``.

        :param allowed_origins: List of allowed origins. Use ``"*"`` for wildcard.
        :param allowed_methods: List of allowed HTTP methods.
        :param allowed_headers: List of allowed request headers.
        :param exposed_headers: List of headers exposed to the browser.
        :param allow_credentials: Whether to allow credentials.
        :param max_age: Preflight cache duration in seconds.

        :raises ValueError: If ``allowed_origins`` contains ``"*"`` and
            ``allow_credentials`` is True.
    """

    name: str = "cors"

    def __init__(
        self,
        allowed_origins: Optional[List[str]] = None,
        allowed_methods: Optional[List[str]] = None,
        allowed_headers: Optional[List[str]] = None,
        exposed_headers: Optional[List[str]] = None,
        allow_credentials: bool = False,
        max_age: int = 600
    ):
        """
            Construct a CORSMiddleware.

            :param allowed_origins: List of allowed origins. Use ``"*"`` for wildcard.
            :param allowed_methods: List of allowed HTTP methods.
            :param allowed_headers: List of allowed request headers.
            :param exposed_headers: List of headers exposed to the browser.
            :param allow_credentials: Whether to allow credentials.
            :param max_age: Preflight cache duration in seconds.

            :raises ValueError: If ``allowed_origins`` contains ``"*"`` and
                ``allow_credentials`` is True.
        """
        self._allowed_origins: List[str] = allowed_origins if allowed_origins is not None else []
        self._allowed_methods: List[str] = allowed_methods if allowed_methods is not None else ["GET", "HEAD", "OPTIONS"]
        self._allowed_headers: List[str] = allowed_headers if allowed_headers is not None else []
        self._exposed_headers: List[str] = exposed_headers if exposed_headers is not None else []
        self._allow_credentials: bool = allow_credentials
        self._max_age: int = max_age

        if WILDCARD_ORIGIN in self._allowed_origins and self._allow_credentials:
            errmsg = (
                "CORSMiddleware: allowed_origins=['*'] can not be combined with "
                "allow_credentials=True, because every origin would then be allowed to "
                "read credentialed responses. List the origins that may send credentials."
            )
            raise ValueError(errmsg)

        return

    def _allows_any_origin(self) -> bool:
        """
            Check whether every origin is allowed.

            :returns: True if the wildcard origin is configured.
        """
        rtnval = WILDCARD_ORIGIN in self._allowed_origins
        return rtnval

    def _is_origin_allowed(self, origin: str) -> bool:
        """
            Check whether the given origin is allowed.

            :param origin: The Origin header value from the request.

            :returns: True if the origin is allowed, False otherwise.
        """
        if self._allows_any_origin():
            return True

        rtnval = origin in self._allowed_origins
        return rtnval

    def _build_cors_headers(self, origin: str) -> Dict[str, str]:
        """
            Build the CORS response headers for an allowed origin.

            :param origin: The allowed origin value.

            :returns: Dictionary of CORS headers.
        """
        headers: Dict[str, str] = {}

        # When wildcard is configured, answer "*". Otherwise reflect the
        # actual origin, which is one of the allow-listed ones.
        if self._allows_any_origin():
            headers["Access-Control-Allow-Origin"] = WILDCARD_ORIGIN
        else:
            headers["Access-Control-Allow-Origin"] = origin

        if self._allow_credentials:
            headers["Access-Control-Allow-Credentials"] = "true"

        if self._exposed_headers:
            headers["Access-Control-Expose-Headers"] = ", ".join(self._exposed_headers)

        return headers

    def _build_preflight_headers(self, origin: str) -> Dict[str, str]:
        """
            Build the full set of CORS headers for a preflight response.

            :param origin: The allowed origin value.

            :returns: Dictionary of preflight CORS headers.
        """
        headers = self._build_cors_headers(origin)

        headers["Access-Control-Allow-Methods"] = ", ".join(self._allowed_methods)

        if self._allowed_headers:
            headers["Access-Control-Allow-Headers"] = ", ".join(self._allowed_headers)

        headers["Access-Control-Max-Age"] = str(self._max_age)

        return headers

    def _get_preflight_response(self, request: Request) -> Optional[Response]:
        """
            Build the answer to a preflight request.

            :param request: The incoming Request.

            :returns: The 204 preflight Response when the request is a
                      preflight from an allowed origin, otherwise None.
        """
        rtnval: Optional[Response] = None

        origin = request.headers.get("Origin")

        if origin is not None and request.method == "OPTIONS":
            requested_method = request.headers.get("Access-Control-Request-Method")

            if requested_method is not None and self._is_origin_allowed(origin):
                preflight_headers = self._build_preflight_headers(origin)
                rtnval = Response(status_code=204, headers=preflight_headers, body=b"")
                self._add_vary_origin(rtnval)

        return rtnval

    def _set_response_header(self, response: Any, name: str, value: str) -> None:
        """
            Set a header on a response of any of the shapes a handler may
            return.

            :param response: The response object.
            :param name: Header name.
            :param value: Header value.
        """
        set_header = getattr(response, "set_header", None)

        if callable(set_header):
            set_header(name, value)
        else:
            # Template responses expose a copy of their headers and have no
            # setter; their stored mapping is ``_headers``.
            stored_headers = getattr(response, "_headers", None)
            if isinstance(stored_headers, dict):
                stored_headers[name] = value

        return

    def _add_vary_origin(self, response: Any) -> None:
        """
            Mark a response as depending on the ``Origin`` request header.

            Nothing is added when every origin receives the same answer
            (wildcard) or when the response already varies on Origin.

            :param response: The response object.
        """
        if not self._allows_any_origin():
            existing = None
            for header_name, header_value in dict(response.headers).items():
                if header_name.lower() == "vary":
                    existing = header_value

            if existing is None or existing.strip() == "":
                self._set_response_header(response, "Vary", "Origin")
            else:
                listed = [item.strip().lower() for item in existing.split(",")]
                if "origin" not in listed and "*" not in listed:
                    self._set_response_header(response, "Vary", f"{existing}, Origin")

        return

    def _apply_cors_headers(self, request: Request, response: Any) -> None:
        """
            Add the CORS headers a response to a non-preflight request needs.

            :param request: The incoming Request.
            :param response: The response from the next handler.
        """
        origin = request.headers.get("Origin")

        if origin is not None and self._is_origin_allowed(origin):
            cors_headers = self._build_cors_headers(origin)
            for header_name, header_value in cors_headers.items():
                self._set_response_header(response, header_name, header_value)

        self._add_vary_origin(response)

        return

    def __call__(self, request: Request, call_next: Callable) -> Response:
        """
            Process a request through the CORS middleware.

            For preflight requests from an allowed origin, returns a
            204 response with CORS headers without calling call_next. For
            regular requests from allowed origins, adds CORS headers to the
            response. For disallowed origins, no CORS headers are added.

            :param request: The incoming Request.
            :param call_next: Callable to invoke the next middleware/handler.

            :returns: Response with or without CORS headers.
        """
        response = self._get_preflight_response(request)

        if response is None:
            response = call_next(request)
            self._apply_cors_headers(request, response)

        return response

    async def call_async(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
            Process a request through the CORS middleware in the
            asynchronous pipeline. Behaves as :meth:`__call__`.

            :param request: The incoming Request.
            :param call_next: Async callable to invoke the next middleware/handler.

            :returns: Response with or without CORS headers.
        """
        response = self._get_preflight_response(request)

        if response is None:
            response = await call_next(request)
            self._apply_cors_headers(request, response)

        return response
