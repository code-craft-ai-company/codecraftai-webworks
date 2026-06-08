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

from typing import Callable, Dict, List, Optional

from ccai.webworks.routing.request import Request
from ccai.webworks.routing.response import Response


class CORSMiddleware:
    """
        Cross-Origin Resource Sharing middleware.

        Handles preflight OPTIONS requests by returning a 204 response with
        appropriate CORS headers (short-circuiting the pipeline). For regular
        requests from allowed origins, CORS response headers are added to the
        response returned by the next handler. Requests from disallowed origins
        receive no CORS headers.

        :param allowed_origins: List of allowed origins. Use ``"*"`` for wildcard.
        :param allowed_methods: List of allowed HTTP methods.
        :param allowed_headers: List of allowed request headers.
        :param exposed_headers: List of headers exposed to the browser.
        :param allow_credentials: Whether to allow credentials.
        :param max_age: Preflight cache duration in seconds.
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
        """
        self._allowed_origins: List[str] = allowed_origins if allowed_origins is not None else []
        self._allowed_methods: List[str] = allowed_methods if allowed_methods is not None else ["GET", "HEAD", "OPTIONS"]
        self._allowed_headers: List[str] = allowed_headers if allowed_headers is not None else []
        self._exposed_headers: List[str] = exposed_headers if exposed_headers is not None else []
        self._allow_credentials: bool = allow_credentials
        self._max_age: int = max_age
        return

    def _is_origin_allowed(self, origin: str) -> bool:
        """
            Check whether the given origin is allowed.

            :param origin: The Origin header value from the request.

            :returns: True if the origin is allowed, False otherwise.
        """
        if "*" in self._allowed_origins:
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

        # When wildcard is configured and credentials are not allowed,
        # reflect "*" as the origin. Otherwise reflect the actual origin.
        if "*" in self._allowed_origins and not self._allow_credentials:
            headers["Access-Control-Allow-Origin"] = "*"
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

    def __call__(self, request: Request, call_next: Callable) -> Response:
        """
            Process a request through the CORS middleware.

            For preflight OPTIONS requests with an allowed origin, returns a
            204 response with CORS headers without calling call_next. For
            regular requests from allowed origins, adds CORS headers to the
            response. For disallowed origins, no CORS headers are added.

            :param request: The incoming Request.
            :param call_next: Callable to invoke the next middleware/handler.

            :returns: Response with or without CORS headers.
        """
        origin = request.headers.get("Origin")

        # No Origin header means this is not a CORS request
        if origin is None:
            response = call_next(request)
            return response

        # Check if the origin is allowed
        if not self._is_origin_allowed(origin):
            # Origin not allowed — omit CORS headers
            response = call_next(request)
            return response

        # Handle preflight OPTIONS request
        if request.method == "OPTIONS":
            preflight_headers = self._build_preflight_headers(origin)
            response = Response(status_code=204, headers=preflight_headers, body=b"")
            return response

        # Regular request from allowed origin — call next and add CORS headers
        response = call_next(request)

        cors_headers = self._build_cors_headers(origin)
        for header_name, header_value in cors_headers.items():
            response.set_header(header_name, header_value)

        return response
