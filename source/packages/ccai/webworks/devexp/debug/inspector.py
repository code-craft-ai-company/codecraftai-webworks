"""
    Request inspector for the webworks framework.

    This module provides the :class:`RequestInspector` class that captures
    and stores detailed information about incoming HTTP requests for
    development-time debugging. The :class:`RequestInfo` class holds the
    captured data for a single request including method, path, query
    parameters, headers, body content, and parsed body data.

    The inspector supports configurable body size limits with truncation,
    JSON and form data parsing, path pattern filtering, and a debug
    endpoint for reviewing captured requests.
"""

import json
import re

from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs


# =============================================================================
# RequestInfo
# =============================================================================

class RequestInfo:
    """
        Captured request information.

        Holds detailed data about a single HTTP request including the
        timestamp, method, path, query parameters, headers, body content,
        whether the body was truncated, and any parsed body data.

        :param timestamp: The time the request was captured.
        :param method: The HTTP method string.
        :param path: The request path string.
        :param query_params: Dictionary of query parameter names to values.
        :param headers: Dictionary of header names to values.
        :param body: The raw request body bytes or None.
        :param body_truncated: Whether the body was truncated due to size limits.
        :param parsed_body: Parsed JSON or form data, or None.
    """

    def __init__(
        self,
        timestamp: datetime,
        method: str,
        path: str,
        query_params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[bytes] = None,
        body_truncated: bool = False,
        parsed_body: Optional[Any] = None,
    ):
        """
            Construct a RequestInfo.

            :param timestamp: The time the request was captured.
            :param method: The HTTP method string.
            :param path: The request path string.
            :param query_params: Dictionary of query parameter names to values.
            :param headers: Dictionary of header names to values.
            :param body: The raw request body bytes or None.
            :param body_truncated: Whether the body was truncated.
            :param parsed_body: Parsed JSON or form data, or None.
        """
        self._timestamp = timestamp
        self._method = method
        self._path = path
        self._query_params = dict(query_params) if query_params is not None else {}
        self._headers = dict(headers) if headers is not None else {}
        self._body = body
        self._body_truncated = body_truncated
        self._parsed_body = parsed_body
        return

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def timestamp(self) -> datetime:
        """
            The time the request was captured.

            :returns: The datetime of capture.
        """
        return self._timestamp

    @property
    def method(self) -> str:
        """
            The HTTP method string.

            :returns: The method string such as GET, POST, etc.
        """
        return self._method

    @property
    def path(self) -> str:
        """
            The request path string.

            :returns: The URL path.
        """
        return self._path

    @property
    def query_params(self) -> Dict[str, Any]:
        """
            The query parameters dictionary.

            :returns: A copy of the query parameters.
        """
        return dict(self._query_params)

    @property
    def headers(self) -> Dict[str, str]:
        """
            The request headers dictionary.

            :returns: A copy of the headers.
        """
        return dict(self._headers)

    @property
    def body(self) -> Optional[bytes]:
        """
            The raw request body bytes.

            :returns: The body bytes or None.
        """
        return self._body

    @property
    def body_truncated(self) -> bool:
        """
            Whether the body was truncated due to size limits.

            :returns: True if the body was truncated.
        """
        return self._body_truncated

    @property
    def parsed_body(self) -> Optional[Any]:
        """
            The parsed body data (JSON or form data).

            :returns: The parsed data or None.
        """
        return self._parsed_body

    # -------------------------------------------------------------------------
    # Serialization
    # -------------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """
            Convert the request info to a dictionary for JSON serialization.

            The body bytes are decoded to a UTF-8 string if present. The
            timestamp is converted to an ISO format string.

            :returns: A dictionary representation of the request info.
        """
        body_value = None
        if self._body is not None:
            try:
                body_value = self._body.decode("utf-8")
            except UnicodeDecodeError:
                body_value = "<binary data: {} bytes>".format(len(self._body))

        result = {
            "timestamp": self._timestamp.isoformat(),
            "method": self._method,
            "path": self._path,
            "query_params": self._query_params,
            "headers": self._headers,
            "body": body_value,
            "body_truncated": self._body_truncated,
            "parsed_body": self._parsed_body,
        }

        return result


# =============================================================================
# RequestInspector
# =============================================================================

class RequestInspector:
    """
        Development tool for inspecting incoming HTTP requests.

        Captures and stores detailed information about incoming requests
        for review during development. Supports configurable limits on
        the number of stored requests and body size, path pattern
        filtering, and a debug endpoint for reviewing captured requests.

        :param max_requests: Maximum number of requests to store in memory.
        :param max_body_size: Maximum body size in bytes before truncation.
        :param path_filter: Optional regex pattern to filter which paths
            are captured.
    """

    def __init__(
        self,
        max_requests: int = 100,
        max_body_size: int = 10240,
        path_filter: Optional[str] = None,
    ):
        """
            Construct a RequestInspector.

            :param max_requests: Maximum number of requests to store.
            :param max_body_size: Maximum body size in bytes before truncation.
            :param path_filter: Optional regex pattern for path filtering.
        """
        self._max_requests = max_requests
        self._max_body_size = max_body_size
        self._path_filter = path_filter
        self._requests: List[RequestInfo] = []
        return

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def max_requests(self) -> int:
        """
            The maximum number of requests stored in memory.

            :returns: The max requests integer.
        """
        return self._max_requests

    @property
    def max_body_size(self) -> int:
        """
            The maximum body size in bytes before truncation.

            :returns: The max body size integer.
        """
        return self._max_body_size

    @property
    def path_filter(self) -> Optional[str]:
        """
            The regex pattern used for path filtering.

            :returns: The path filter string or None.
        """
        return self._path_filter

    # -------------------------------------------------------------------------
    # Capture
    # -------------------------------------------------------------------------

    def capture(self, request: Any) -> None:
        """
            Capture request information for inspection.

            Extracts method, path, query parameters, headers, and body
            from the request. The body is truncated if it exceeds the
            configured max_body_size. JSON and form data are parsed
            when applicable. If a path_filter is set, only requests
            matching the pattern are captured.

            :param request: The incoming request object or dictionary.
        """
        method, path, query_params, headers, raw_body = self._extract_request_data(request)

        # Apply path filter if configured
        if self._path_filter is not None:
            match = re.search(self._path_filter, path)
            if match is None:
                return

        # Apply body size limiting and truncation
        body, body_truncated = self._apply_body_limit(raw_body)

        # Parse JSON or form data
        parsed_body = self._parse_body(raw_body, headers)

        request_info = RequestInfo(
            timestamp=datetime.now(),
            method=method,
            path=path,
            query_params=query_params,
            headers=headers,
            body=body,
            body_truncated=body_truncated,
            parsed_body=parsed_body,
        )

        self._requests.append(request_info)

        # Enforce max_requests limit by removing oldest entries
        while len(self._requests) > self._max_requests:
            self._requests.pop(0)

        return

    # -------------------------------------------------------------------------
    # Retrieval
    # -------------------------------------------------------------------------

    def get_requests(
        self,
        limit: Optional[int] = None,
        path_filter: Optional[str] = None,
    ) -> List[RequestInfo]:
        """
            Get captured requests with optional filtering.

            :param limit: Maximum number of requests to return.
            :param path_filter: Optional regex pattern to filter by path.

            :returns: A list of captured RequestInfo objects.
        """
        result = list(self._requests)

        if path_filter is not None:
            filtered = []
            for req in result:
                match = re.search(path_filter, req.path)
                if match is not None:
                    filtered.append(req)
            result = filtered

        if limit is not None:
            result = result[-limit:]

        return result

    def clear(self) -> None:
        """
            Clear all captured requests.
        """
        self._requests.clear()
        return

    # -------------------------------------------------------------------------
    # Debug Endpoint
    # -------------------------------------------------------------------------

    def handle_debug_endpoint(
        self,
        limit: Optional[int] = None,
        path_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
            Handle a debug endpoint request for reviewing captured requests.

            Returns a response dictionary suitable for serving at a debug
            endpoint such as ``/_debug/requests``.

            :param limit: Maximum number of requests to return.
            :param path_filter: Optional path filter for the response.

            :returns: A dictionary with ``status_code``, ``headers``, and
                ``body`` keys. The body is a JSON string of captured requests.
        """
        requests = self.get_requests(limit=limit, path_filter=path_filter)

        request_dicts = []
        for req in requests:
            request_dicts.append(req.to_dict())

        body_data = {
            "requests": request_dicts,
            "total": len(self._requests),
            "returned": len(request_dicts),
        }

        body_json = json.dumps(body_data, indent=2, default=str)

        response = {
            "status_code": 200,
            "headers": {"Content-Type": "application/json; charset=utf-8"},
            "body": body_json,
        }

        return response

    # -------------------------------------------------------------------------
    # Internal Helpers
    # -------------------------------------------------------------------------

    def _extract_request_data(self, request: Any):
        """
            Extract request data from a request object or dictionary.

            Supports both dictionary-style requests and objects with
            method, path, headers, query_params, and body attributes.

            :param request: The request object or dictionary.

            :returns: A tuple of (method, path, query_params, headers, body).
        """
        if isinstance(request, dict):
            method = request.get("method", "GET")
            path = request.get("path", "/")
            query_params = request.get("query_params", {})
            headers = request.get("headers", {})
            body = request.get("body", None)
        else:
            method = getattr(request, "method", "GET")
            path = getattr(request, "path", "/")
            query_params = getattr(request, "query_params", {})
            headers = getattr(request, "headers", {})
            body = getattr(request, "body", None)

        # Ensure body is bytes if present
        if body is not None and isinstance(body, str):
            body = body.encode("utf-8")

        # Ensure query_params is a dict
        if not isinstance(query_params, dict):
            query_params = {}

        # Ensure headers is a dict
        if not isinstance(headers, dict):
            headers = {}

        return method, path, query_params, headers, body

    def _apply_body_limit(self, raw_body: Optional[bytes]):
        """
            Apply body size limiting and truncation.

            If the body exceeds max_body_size, it is truncated and
            body_truncated is set to True.

            :param raw_body: The raw body bytes or None.

            :returns: A tuple of (body, body_truncated).
        """
        if raw_body is None:
            return None, False

        if len(raw_body) > self._max_body_size:
            truncated_body = raw_body[:self._max_body_size]
            return truncated_body, True

        return raw_body, False

    def _parse_body(
        self,
        raw_body: Optional[bytes],
        headers: Dict[str, str],
    ) -> Optional[Any]:
        """
            Parse the request body as JSON or form data when applicable.

            Uses the Content-Type header to determine the parsing strategy.
            Returns None if the body cannot be parsed or is not present.

            :param raw_body: The raw body bytes or None.
            :param headers: The request headers dictionary.

            :returns: The parsed body data or None.
        """
        if raw_body is None:
            return None

        if len(raw_body) == 0:
            return None

        content_type = self._get_content_type(headers)

        if content_type is not None and "application/json" in content_type:
            parsed = self._parse_json_body(raw_body)
            return parsed

        if content_type is not None and "application/x-www-form-urlencoded" in content_type:
            parsed = self._parse_form_body(raw_body)
            return parsed

        return None

    def _parse_json_body(self, raw_body: bytes) -> Optional[Any]:
        """
            Attempt to parse the body as JSON.

            :param raw_body: The raw body bytes.

            :returns: The parsed JSON data or None on failure.
        """
        try:
            body_str = raw_body.decode("utf-8")
            parsed = json.loads(body_str)
            return parsed
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None

    def _parse_form_body(self, raw_body: bytes) -> Optional[Dict[str, List[str]]]:
        """
            Attempt to parse the body as URL-encoded form data.

            :param raw_body: The raw body bytes.

            :returns: The parsed form data dictionary or None on failure.
        """
        try:
            body_str = raw_body.decode("utf-8")
            parsed = parse_qs(body_str)
            return parsed
        except (UnicodeDecodeError, ValueError):
            return None

    def _get_content_type(self, headers: Dict[str, str]) -> Optional[str]:
        """
            Get the Content-Type header value (case-insensitive lookup).

            :param headers: The request headers dictionary.

            :returns: The content type string or None.
        """
        for header_name, header_value in headers.items():
            if header_name.lower() == "content-type":
                return header_value

        return None
