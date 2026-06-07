"""
    Test fixtures for the webworks testing framework.

    This module provides resource factory functions that create
    preconfigured test resources for endpoint testing. The factories
    follow the testbase resource factory pattern and support
    configuration overrides via the *constraints* parameter.

    Each factory is a generator function that yields the resource
    and performs cleanup after the test completes.

    Available factories:

    - :func:`create_test_app` -- Creates a configurable test application.
    - :func:`create_test_client` -- Creates a :class:`TestClient` bound
      to a test application.
    - :func:`create_mock_request` -- Creates a mock request object with
      custom method, path, headers, and body.
    - :func:`create_mock_response` -- Creates a mock response object
      with custom status code, headers, and body.
"""

import json as _json_module

from typing import Any, Callable, Dict, Generator, Optional, Tuple

from ccai.webworks.devexp.testing.testclient import TestClient
from ccai.webworks.devexp.testing.testresponse import TestResponse


# =============================================================================
# MockRequest
# =============================================================================

class MockRequest:
    """
        A mock HTTP request object for testing.

        Provides a simple data container with the standard request
        attributes: method, path, headers, and body. Useful for
        testing middleware, handlers, and other components that
        accept request objects.

        :param method: The HTTP method string (e.g. ``GET``, ``POST``).
        :param path: The request path string.
        :param headers: A dictionary of request header name-value pairs.
        :param body: The raw request body as bytes.
    """

    def __init__(
        self,
        method: str = "GET",
        path: str = "/",
        headers: Optional[Dict[str, str]] = None,
        body: bytes = b"",
    ):
        """
            Construct a MockRequest.

            :param method: The HTTP method string.
            :param path: The request path.
            :param headers: Optional request headers dictionary.
            :param body: The request body bytes.
        """
        self._method = method
        self._path = path
        self._headers: Dict[str, str] = dict(headers) if headers is not None else {}
        self._body = bytes(body)
        return

    @property
    def method(self) -> str:
        """
            The HTTP method of the request.

            :returns: The method string.
        """
        return self._method

    @property
    def path(self) -> str:
        """
            The request path.

            :returns: The path string.
        """
        return self._path

    @property
    def headers(self) -> Dict[str, str]:
        """
            The request headers.

            :returns: A copy of the headers dictionary.
        """
        return dict(self._headers)

    @property
    def body(self) -> bytes:
        """
            The raw request body.

            :returns: The body as bytes.
        """
        return self._body

    def get_header(
        self,
        name: str,
        default: Optional[str] = None,
    ) -> Optional[str]:
        """
            Get a request header value by name (case-insensitive).

            :param name: The header name to look up.
            :param default: The value to return if the header is not found.

            :returns: The header value or the default.
        """
        lower_name = name.lower()

        for header_name, header_value in self._headers.items():
            if header_name.lower() == lower_name:
                return header_value

        return default


# =============================================================================
# TestApp
# =============================================================================

class TestApp:
    """
        A configurable test application for use in testing.

        Wraps an application callable and provides a configuration
        dictionary. When called, it delegates to the wrapped callable.
        If no callable is provided, a default echo application is used.

        :param app_callable: Optional application callable to wrap.
        :param config: Optional configuration dictionary.
    """

    def __init__(
        self,
        app_callable: Optional[Callable] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
            Construct a TestApp.

            :param app_callable: Optional application callable.
            :param config: Optional configuration dictionary.
        """
        self._config: Dict[str, Any] = dict(config) if config is not None else {}
        self._config.setdefault("TESTING", True)
        self._config.setdefault("DEBUG", False)

        if app_callable is not None:
            self._app_callable = app_callable
        else:
            self._app_callable = self._default_app

        self._is_cleaned_up = False
        return

    @property
    def config(self) -> Dict[str, Any]:
        """
            The application configuration dictionary.

            :returns: A reference to the configuration dictionary.
        """
        return self._config

    @property
    def is_cleaned_up(self) -> bool:
        """
            Whether cleanup has been performed on this app.

            :returns: True if cleanup has been called.
        """
        return self._is_cleaned_up

    def __call__(
        self,
        method: str,
        path: str,
        headers: Dict[str, str],
        body: bytes,
    ) -> Tuple[int, Dict[str, str], bytes]:
        """
            Handle a request by delegating to the wrapped callable.

            :param method: The HTTP method string.
            :param path: The request path.
            :param headers: The request headers dictionary.
            :param body: The request body bytes.

            :returns: A tuple of (status_code, headers, body).
        """
        result = self._app_callable(method, path, headers, body)
        return result

    def cleanup(self) -> None:
        """
            Perform cleanup of test application resources.
        """
        self._is_cleaned_up = True
        return

    def _default_app(
        self,
        method: str,
        path: str,
        headers: Dict[str, str],
        body: bytes,
    ) -> Tuple[int, Dict[str, str], bytes]:
        """
            A default echo application that returns request details
            as a JSON response.

            :param method: The HTTP method string.
            :param path: The request path.
            :param headers: The request headers dictionary.
            :param body: The request body bytes.

            :returns: A tuple of (status_code, headers, body).
        """
        response_data = {
            "method": method,
            "path": path,
            "headers": headers,
            "body": body.decode("utf-8") if body else "",
        }
        response_body = _json_module.dumps(response_data).encode("utf-8")
        response_headers = {"Content-Type": "application/json"}

        return 200, response_headers, response_body


# =============================================================================
# Resource Factory Functions
# =============================================================================

def create_test_app(
    constraints: Optional[Dict[str, Any]] = None,
) -> Generator[TestApp, None, None]:
    """
        Resource factory that creates a configurable test application.

        This factory follows the testbase resource factory pattern.
        It creates a :class:`TestApp` instance with the provided
        configuration overrides, yields it for use in tests, and
        performs cleanup after the test completes.

        Usage with testbase::

            @testbase.register.resource_factory()
            def create_test_app(constraints={}) -> Generator[TestApp, None, None]:
                ...

            testbase.originate.parameter(create_test_app, identifier='test_app')

        :param constraints: Optional configuration overrides. Supported
            keys include ``config`` (dict of app config values) and
            ``app_callable`` (a custom application callable).

        :yields: A configured :class:`TestApp` instance.
    """
    if constraints is None:
        constraints = {}

    app_config = constraints.get("config", {})
    app_callable = constraints.get("app_callable", None)

    app = TestApp(app_callable=app_callable, config=app_config)

    yield app

    # Cleanup
    app.cleanup()

    return


def create_test_client(
    constraints: Optional[Dict[str, Any]] = None,
) -> Generator[TestClient, None, None]:
    """
        Resource factory that creates a :class:`TestClient` bound
        to a test application.

        This factory follows the testbase resource factory pattern.
        It creates a :class:`TestApp` (or uses a provided one) and
        a :class:`TestClient` bound to it, yields the client for
        use in tests, and performs cleanup after the test completes.

        Usage with testbase::

            @testbase.register.resource_factory()
            def create_test_client(constraints={}) -> Generator[TestClient, None, None]:
                ...

            testbase.originate.parameter(create_test_client, identifier='test_client')

        :param constraints: Optional configuration overrides. Supported
            keys include ``app`` (a pre-existing app callable or TestApp),
            ``headers`` (default headers dict), and ``config`` (app config
            dict when creating a new TestApp).

        :yields: A configured :class:`TestClient` instance.
    """
    if constraints is None:
        constraints = {}

    app = constraints.get("app", None)
    default_headers = constraints.get("headers", None)

    owns_app = False

    if app is None:
        app_config = constraints.get("config", {})
        app = TestApp(config=app_config)
        owns_app = True

    client = TestClient(app=app, default_headers=default_headers)

    yield client

    # Cleanup: clear cookies and auth
    client.cookies.clear()
    client.clear_auth()

    if owns_app and isinstance(app, TestApp):
        app.cleanup()

    return


def create_mock_request(
    constraints: Optional[Dict[str, Any]] = None,
) -> Generator[MockRequest, None, None]:
    """
        Resource factory that creates a mock request object.

        This factory follows the testbase resource factory pattern.
        It creates a :class:`MockRequest` with the provided attributes
        and yields it for use in tests.

        Usage with testbase::

            @testbase.register.resource_factory()
            def create_mock_request(constraints={}) -> Generator[MockRequest, None, None]:
                ...

            testbase.originate.parameter(create_mock_request, identifier='mock_request')

        :param constraints: Optional request attributes. Supported keys
            include ``method`` (str), ``path`` (str), ``headers`` (dict),
            and ``body`` (bytes).

        :yields: A configured :class:`MockRequest` instance.
    """
    if constraints is None:
        constraints = {}

    method = constraints.get("method", "GET")
    path = constraints.get("path", "/")
    headers = constraints.get("headers", {})
    body = constraints.get("body", b"")

    request = MockRequest(
        method=method,
        path=path,
        headers=headers,
        body=body,
    )

    yield request

    return


def create_mock_response(
    constraints: Optional[Dict[str, Any]] = None,
) -> Generator[TestResponse, None, None]:
    """
        Resource factory that creates a mock response object.

        This factory follows the testbase resource factory pattern.
        It creates a :class:`TestResponse` with the provided attributes
        and yields it for use in tests.

        Usage with testbase::

            @testbase.register.resource_factory()
            def create_mock_response(constraints={}) -> Generator[TestResponse, None, None]:
                ...

            testbase.originate.parameter(create_mock_response, identifier='mock_response')

        :param constraints: Optional response attributes. Supported keys
            include ``status_code`` (int), ``headers`` (dict), ``body``
            (bytes), and ``json`` (any JSON-serializable value that will
            be encoded as the body).

        :yields: A configured :class:`TestResponse` instance.
    """
    if constraints is None:
        constraints = {}

    status_code = constraints.get("status_code", 200)
    headers = constraints.get("headers", {})

    json_data = constraints.get("json", None)
    if json_data is not None:
        body = _json_module.dumps(json_data).encode("utf-8")
        if "Content-Type" not in headers:
            headers["Content-Type"] = "application/json"
    else:
        body = constraints.get("body", b"")

    response = TestResponse(
        status_code=status_code,
        headers=headers,
        body=body,
    )

    yield response

    return
