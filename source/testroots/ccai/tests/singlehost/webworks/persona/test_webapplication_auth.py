"""
.. module:: test_webapplication_auth
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the WebApplication authentication management
        APIs: ``register_authenticator`` and ``configure_auth_middleware``.

.. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


import ccai.webworks.webapplication as webapp_module

from ccai.testbase.mocking import Mock, create_module_patch

from ccai.webworks.webapplication import (
    establish_webapp_persona,
    reset_webapp_persona,
)
from ccai.webworks.persona.lifecycle import LifecycleError, LifecyclePhase


# =============================================================================
# Helpers
# =============================================================================

def _create_app():
    """
        Creates a fresh WebApplication via ``establish_webapp_persona``
        after resetting any prior singleton state.

        :returns: A freshly created WebApplication instance.
    """
    reset_webapp_persona()

    app = establish_webapp_persona(
        name="testapp",
        logger_name="testapp",
        log_basename="testapp",
    )

    return app


def _startup_app(app):
    """
        Runs the full startup sequence on the given WebApplication
        with ManagedConfigRegistry mocked to avoid filesystem access.

        :param app: The WebApplication instance to start up.

        :returns: The patch object so the caller can deactivate it.
    """
    mock_registry_instance = Mock()
    mock_registry_instance.configure(recursive=True)

    patch = create_module_patch(webapp_module, "ManagedConfigRegistry")
    mock_cls = patch.activate()
    mock_cls.configure(return_value=mock_registry_instance)

    app.startup()

    return patch


def _advance_to_authentication_ready(app):
    """
        Advances the given WebApplication through all lifecycle phases
        up to and including ``AUTHENTICATION_READY`` by mocking
        ManagedConfigRegistry and calling each setup method in order.

        This intentionally does NOT call ``setup_infrastructure`` so
        the application remains at ``AUTHENTICATION_READY``.

        :param app: The WebApplication instance to advance.

        :returns: The patch object so the caller can deactivate it.
    """
    mock_registry_instance = Mock()
    mock_registry_instance.configure(recursive=True)

    patch = create_module_patch(webapp_module, "ManagedConfigRegistry")
    mock_cls = patch.activate()
    mock_cls.configure(return_value=mock_registry_instance)

    app.setup_configuration()
    app.setup_credentials()
    app.setup_data_profiles()
    app.setup_database()
    app.setup_authentication()

    return patch


# =============================================================================
# Unit Tests for register_authenticator
# =============================================================================

def test_register_authenticator_adds_authenticator_to_auth_system():
    """
        Test that ``register_authenticator`` delegates to the
        AuthenticationSystem and the authenticator becomes retrievable
        by its scheme via ``get_authenticator``.

        _Requirements: 7.2_
    """
    app = _create_app()
    patch = None

    try:
        patch = _advance_to_authentication_ready(app)

        mock_auth = Mock()
        mock_auth.configure(recursive=True)
        mock_auth.mock_context().set_attribute("scheme", "bearer")
        mock_auth.mock_context().mock_method("can_handle", return_value=True)

        app.register_authenticator(mock_auth, priority=10)

        retrieved = app._auth_system.get_authenticator("bearer")

        if retrieved is not mock_auth:
            errmsg = (
                "Expected get_authenticator('bearer') to return the "
                "registered mock authenticator, got "
                f"{type(retrieved)}"
            )
            raise AssertionError(errmsg)

    finally:
        if patch is not None:
            patch.deactivate()
        reset_webapp_persona()

    return


# =============================================================================
# Unit Tests for configure_auth_middleware
# =============================================================================

def test_configure_auth_middleware_creates_middleware_with_correct_properties():
    """
        Test that ``configure_auth_middleware`` creates an
        AuthenticationMiddleware whose ``app`` property returns the
        WebApplication's ASGIApplication and whose ``auth_system``
        property returns the WebApplication's AuthenticationSystem.

        _Requirements: 7.3_
    """
    app = _create_app()
    patch = None

    try:
        patch = _startup_app(app)

        middleware = app.configure_auth_middleware(
            exclude_paths={"/health"},
            realm="TestRealm",
        )

        if middleware.app is not app._asgi_app:
            errmsg = (
                "Expected middleware.app to be the same object as "
                "app._asgi_app"
            )
            raise AssertionError(errmsg)

        if middleware.auth_system is not app._auth_system:
            errmsg = (
                "Expected middleware.auth_system to be the same object "
                "as app._auth_system"
            )
            raise AssertionError(errmsg)

        if middleware.realm != "TestRealm":
            errmsg = (
                f"Expected middleware.realm to be 'TestRealm', "
                f"got '{middleware.realm}'"
            )
            raise AssertionError(errmsg)

        if "/health" not in middleware.exclude_paths:
            errmsg = (
                "Expected '/health' to be in middleware.exclude_paths, "
                f"got {middleware.exclude_paths}"
            )
            raise AssertionError(errmsg)

    finally:
        if patch is not None:
            patch.deactivate()
        reset_webapp_persona()

    return


def test_configure_auth_middleware_before_infrastructure_raises_lifecycle_error():
    """
        Test that calling ``configure_auth_middleware`` before the
        application has reached the ``INFRASTRUCTURE_READY`` phase
        raises a ``LifecycleError`` with a descriptive message.

        _Requirements: 7.4_
    """
    app = _create_app()
    patch = None

    try:
        patch = _advance_to_authentication_ready(app)

        # The app is at AUTHENTICATION_READY, not INFRASTRUCTURE_READY
        caught_error = None

        try:
            app.configure_auth_middleware(
                exclude_paths={"/health"},
                realm="TestRealm",
            )
        except LifecycleError as err:
            caught_error = err

        if caught_error is None:
            errmsg = (
                "Expected LifecycleError when calling "
                "configure_auth_middleware before INFRASTRUCTURE_READY"
            )
            raise AssertionError(errmsg)

        error_message = str(caught_error)

        if "infrastructure_ready" not in error_message.lower():
            errmsg = (
                "Expected LifecycleError message to reference "
                "'infrastructure_ready', got: "
                f"{error_message}"
            )
            raise AssertionError(errmsg)

        if "configure_auth_middleware" not in error_message:
            errmsg = (
                "Expected LifecycleError message to reference "
                "'configure_auth_middleware', got: "
                f"{error_message}"
            )
            raise AssertionError(errmsg)

        if caught_error.required_phase != LifecyclePhase.INFRASTRUCTURE_READY:
            errmsg = (
                "Expected required_phase to be INFRASTRUCTURE_READY, "
                f"got {caught_error.required_phase}"
            )
            raise AssertionError(errmsg)

        if caught_error.current_phase != LifecyclePhase.AUTHENTICATION_READY:
            errmsg = (
                "Expected current_phase to be AUTHENTICATION_READY, "
                f"got {caught_error.current_phase}"
            )
            raise AssertionError(errmsg)

    finally:
        if patch is not None:
            patch.deactivate()
        reset_webapp_persona()

    return


# =============================================================================
# Access policy enforcement through the served ASGI application
# =============================================================================

import asyncio

from ccai.webworks.asgi.application import ASGIApplication
from ccai.webworks.authentication.core import (
    AuthenticationContext,
    AuthenticationResult,
    AuthenticationStatus,
    Principal,
)
from ccai.webworks.authentication.middleware import AuthenticationMiddleware
from ccai.webworks.endpoints.accesspolicy import AccessPolicy
from ccai.webworks.routing.response import HTMLResponse
from ccai.webworks.security.decorators import require_roles


class _TokenAuthenticator:
    """
        Authenticator for tests: the ``X-Token`` header names the user,
        ``admin`` holds the system-admin role and ``user`` the viewer role.
    """

    scheme = "Token"

    ROLES_BY_TOKEN = {"admin": {"system-admin"}, "user": {"viewer"}}

    def can_handle(self, request) -> bool:
        return request.headers.get("X-Token") is not None

    async def authenticate(self, request) -> AuthenticationResult:
        token = request.headers.get("X-Token")
        roles = self.ROLES_BY_TOKEN.get(token)

        if roles is None:
            return AuthenticationResult(
                status=AuthenticationStatus.FAILURE,
                error_code="invalid_token",
                error_description="Unknown token"
            )

        context = AuthenticationContext(
            principal=Principal(identifier=token, roles=set(roles)),
            scheme=self.scheme
        )
        return AuthenticationResult(status=AuthenticationStatus.SUCCESS, context=context)


def _call_asgi(asgi_app, path, token=None, method="GET"):
    """
        Send one HTTP request to an ASGI application.

        :returns: Tuple of the response status and the response body.
    """
    sent = []

    headers = [(b"host", b"localhost")]
    if token is not None:
        headers.append((b"x-token", token.encode("ascii")))

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode("ascii"),
        "query_string": b"",
        "headers": headers,
        "server": ("127.0.0.1", 80),
        "client": ("127.0.0.1", 5000),
    }

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        sent.append(message)

    asyncio.run(asgi_app(scope, receive, send))

    status = [message["status"] for message in sent if message["type"] == "http.response.start"][0]
    body = b"".join(message.get("body", b"") for message in sent if message["type"] == "http.response.body")

    return status, body


def _attach_protected_routes(app):
    """
        Attach an admin-only route, a decorator-protected route and a public
        route to the application.
    """
    @app.attach_route("/admin/users", access_policy=AccessPolicy(roles=["system-admin"]))
    def admin_users(request):
        return HTMLResponse(content="SECRET ADMIN DATA")

    @app.attach_route("/decorated")
    @require_roles("system-admin")
    def decorated(request):
        return HTMLResponse(content="SECRET DECORATED DATA")

    @app.attach_route("/public")
    def public(request):
        return HTMLResponse(content="PUBLIC")

    return


def test_asgi_app_refuses_anonymous_request_to_protected_endpoint():
    """
        Without any authentication configured, the served application
        answers 401 for an endpoint with an access policy instead of running
        its handler -- for /admin/users and for //admin/users alike.
    """
    app = _create_app()
    patch = None

    try:
        _attach_protected_routes(app)
        patch = _startup_app(app)

        for path in ["/admin/users", "//admin/users", "/decorated"]:
            status, body = _call_asgi(app.asgi_app, path)

            if status != 401:
                errmsg = f"{path}: expected 401 for an anonymous request, got {status}"
                raise AssertionError(errmsg)

            if b"SECRET" in body:
                errmsg = f"{path}: the protected body was served to an anonymous request"
                raise AssertionError(errmsg)

    finally:
        if patch is not None:
            patch.deactivate()
        reset_webapp_persona()

    return


def test_asgi_app_serves_public_endpoint_without_authentication():
    """
        An endpoint without an access policy stays public.
    """
    app = _create_app()
    patch = None

    try:
        _attach_protected_routes(app)
        patch = _startup_app(app)

        status, body = _call_asgi(app.asgi_app, "/public")

        if status != 200 or body != b"PUBLIC":
            errmsg = f"Expected 200 PUBLIC for the public endpoint, got {status} {body!r}"
            raise AssertionError(errmsg)

    finally:
        if patch is not None:
            patch.deactivate()
        reset_webapp_persona()

    return


def test_asgi_app_returns_auth_middleware_after_configuration():
    """
        Once configure_auth_middleware has been called, asgi_app is the
        authentication middleware wrapped around the ASGIApplication.
    """
    app = _create_app()
    patch = None

    try:
        patch = _startup_app(app)

        if not isinstance(app.asgi_app, ASGIApplication):
            errmsg = "Expected asgi_app to be the ASGIApplication before configuration"
            raise AssertionError(errmsg)

        middleware = app.configure_auth_middleware(optional_patterns=["/**"])

        if app.asgi_app is not middleware:
            errmsg = "Expected asgi_app to return the configured authentication middleware"
            raise AssertionError(errmsg)

        if not isinstance(middleware, AuthenticationMiddleware):
            errmsg = "Expected an AuthenticationMiddleware instance"
            raise AssertionError(errmsg)

        if middleware.app is not app._asgi_app:
            errmsg = "Expected the middleware to wrap the ASGIApplication"
            raise AssertionError(errmsg)

    finally:
        if patch is not None:
            patch.deactivate()
        reset_webapp_persona()

    return


def test_asgi_app_enforces_endpoint_roles_with_authentication_configured():
    """
        With an authenticator registered and authentication optional
        everywhere, the endpoint policies decide: 401 without credentials,
        403 with insufficient roles, 200 with the required role -- for every
        spelling of the path.
    """
    app = _create_app()
    patch = None

    try:
        _attach_protected_routes(app)
        patch = _startup_app(app)

        app.register_authenticator(_TokenAuthenticator())
        app.configure_auth_middleware(optional_patterns=["/**"])

        for path in ["/admin/users", "//admin/users", "/admin//users", "/decorated"]:
            anonymous_status, _body = _call_asgi(app.asgi_app, path)
            viewer_status, _body = _call_asgi(app.asgi_app, path, token="user")
            admin_status, admin_body = _call_asgi(app.asgi_app, path, token="admin")

            if anonymous_status != 401:
                errmsg = f"{path}: expected 401 without credentials, got {anonymous_status}"
                raise AssertionError(errmsg)

            if viewer_status != 403:
                errmsg = f"{path}: expected 403 with insufficient roles, got {viewer_status}"
                raise AssertionError(errmsg)

            if admin_status != 200 or b"SECRET" not in admin_body:
                errmsg = f"{path}: expected 200 for the admin, got {admin_status} {admin_body!r}"
                raise AssertionError(errmsg)

        public_status, public_body = _call_asgi(app.asgi_app, "/public")

        if public_status != 200 or public_body != b"PUBLIC":
            errmsg = f"Expected the public endpoint to stay open, got {public_status} {public_body!r}"
            raise AssertionError(errmsg)

    finally:
        if patch is not None:
            patch.deactivate()
        reset_webapp_persona()

    return


def test_asgi_app_applies_path_policy_to_non_canonical_path():
    """
        A path policy configured for /reports is applied to //reports too:
        the authentication middleware compares the canonical path, the same
        one the router matches.
    """
    app = _create_app()
    patch = None

    try:
        @app.attach_route("/reports")
        def reports(request):
            return HTMLResponse(content="SECRET REPORTS")

        patch = _startup_app(app)

        app.register_authenticator(_TokenAuthenticator())
        app.configure_auth_middleware(
            path_policies={"/reports": AccessPolicy(roles=["system-admin"])},
        )

        for path in ["/reports", "//reports", "/reports//"]:
            viewer_status, viewer_body = _call_asgi(app.asgi_app, path, token="user")

            if viewer_status == 200 or b"SECRET" in viewer_body:
                errmsg = (
                    f"{path}: a low-privilege user reached the handler behind the "
                    f"path policy (status {viewer_status})"
                )
                raise AssertionError(errmsg)

        admin_status, admin_body = _call_asgi(app.asgi_app, "//reports", token="admin")

        if admin_status != 200 or admin_body != b"SECRET REPORTS":
            errmsg = f"Expected the admin to be served, got {admin_status} {admin_body!r}"
            raise AssertionError(errmsg)

    finally:
        if patch is not None:
            patch.deactivate()
        reset_webapp_persona()

    return


def test_asgi_app_redirects_dot_segment_path_before_applying_path_policies():
    """
        /files/./private names the resource /files/private. With path
        policies configured the request is redirected to that spelling
        instead of being decided under a path the policy does not list.
    """
    app = _create_app()
    patch = None

    try:
        @app.attach_route("/files/{document:path}")
        def files(request):
            return HTMLResponse(content="SECRET FILE")

        patch = _startup_app(app)

        app.register_authenticator(_TokenAuthenticator())
        app.configure_auth_middleware(
            path_policies={"/files/private": AccessPolicy(roles=["system-admin"])},
        )

        sent = []

        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/files/./private",
            "raw_path": b"/files/./private",
            "query_string": b"v=1",
            "headers": [(b"host", b"localhost"), (b"x-token", b"user")],
            "server": ("127.0.0.1", 80),
            "client": ("127.0.0.1", 5000),
        }

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(message):
            sent.append(message)

        asyncio.run(app.asgi_app(scope, receive, send))

        start = [message for message in sent if message["type"] == "http.response.start"][0]
        body = b"".join(message.get("body", b"") for message in sent if message["type"] == "http.response.body")

        if start["status"] != 308:
            errmsg = f"Expected a 308 redirect for a path with a '.' segment, got {start['status']}"
            raise AssertionError(errmsg)

        if dict(start["headers"]).get(b"location") != b"/files/private?v=1":
            errmsg = f"Unexpected Location header in {start['headers']!r}"
            raise AssertionError(errmsg)

        if b"SECRET" in body:
            errmsg = "The protected body was served for a path with a '.' segment"
            raise AssertionError(errmsg)

        viewer_status, _body = _call_asgi(app.asgi_app, "/files/private", token="user")

        if viewer_status != 403:
            errmsg = f"Expected 403 for the redirected path, got {viewer_status}"
            raise AssertionError(errmsg)

    finally:
        if patch is not None:
            patch.deactivate()
        reset_webapp_persona()

    return
