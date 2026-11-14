"""
    Unit tests for the SecurityBlueprint base class.

    This module verifies the behaviour every authentication blueprint
    inherits: endpoint registration, the endpoint wrapper (internal
    errors, sanitising, CORS, keeping the event loop free), registration
    with the authentication middleware, request parsing helpers and the
    in-memory fallback stores.
"""

import asyncio
import threading
import time

from ccai.webworks.authentication.basic import BasicAuthenticator
from ccai.webworks.authentication.blueprints.apikey import APIKeyBlueprint
from ccai.webworks.authentication.blueprints.oauth2 import OAuth2Blueprint
from ccai.webworks.authentication.blueprints.schemas import (
    SessionInfo,
    SessionLoginRequest,
)
from ccai.webworks.authentication.blueprints.security import (
    ExpiringMemoryStore,
    SecurityBlueprint,
    restrict_scope,
    run_async,
    split_scope,
)
from ccai.webworks.authentication.blueprints.session import SessionAuthBlueprint
from ccai.webworks.authentication.core import AuthenticationContext, Principal
from ccai.webworks.authentication.middleware import AuthenticationMiddleware
from ccai.webworks.authentication.system import AuthenticationSystem
from ccai.webworks.endpoints.accesspolicy import AccessPolicy
from ccai.webworks.routing.dispatcher import Dispatcher
from ccai.webworks.routing.exceptions import NotFound
from ccai.webworks.routing.middleware import MiddlewarePipeline
from ccai.webworks.routing.request import Request
from ccai.webworks.routing.router import Router


# =============================================================================
# Test Helpers
# =============================================================================


class HeaderRequest:
    """
        A mock request that carries headers and an optional JSON body.
    """

    def __init__(self, headers=None, data=None):
        self.headers = headers or {}
        self._data = data

    def json(self):
        return self._data


class NoUsersIdentityProvider:
    """
        An identity provider that rejects every credential pair.
    """

    async def validate_credentials(self, username, password):
        return None

    async def get_principal(self, identifier):
        return None


class RecordingApp:
    """
        An ASGI application that records whether it was called.
    """

    def __init__(self):
        self.called = False

    async def __call__(self, scope, receive, send):
        self.called = True


async def _receive():
    return {"type": "http.request", "body": b"", "more_body": False}


def _request_reaches_app(middleware, app, path, method="POST"):
    """
        Send an unauthenticated request through the middleware and report
        whether it reached the application.
    """
    sent = []

    async def send(message):
        sent.append(message)

    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "query_string": b"",
        "headers": [],
        "scheme": "http",
        "server": ("localhost", 8000),
    }

    app.called = False
    asyncio.run(middleware(scope, _receive, send))
    return app.called


def _create_protecting_middleware():
    """
        Create a middleware that requires Basic credentials everywhere.
    """
    app = RecordingApp()
    auth_system = AuthenticationSystem()
    auth_system.register(BasicAuthenticator(NoUsersIdentityProvider()))
    middleware = AuthenticationMiddleware(app=app, auth_system=auth_system)
    return middleware, app


def _fresh_session_blueprint():
    """
        Create an isolated SessionAuthBlueprint subclass.
    """
    class FreshSession(SessionAuthBlueprint):
        pass

    FreshSession.base_path = "/auth/session"
    FreshSession.enabled_endpoints = None
    FreshSession.access_policy = None
    return FreshSession


# =============================================================================
# Registration
# =============================================================================

def test_overridden_handler_yields_a_single_descriptor():
    """
        Verify that a subclass which redefines a decorated handler
        registers one descriptor for the route, the subclass's.
    """
    class Parent(SecurityBlueprint):
        base_path = "/auth/custom"

        @classmethod
        @SecurityBlueprint.create(leaf="login")
        def login(cls, request):
            return {"status": 200, "body": {"who": "parent"}, "content_type": "application/json"}

    class Child(Parent):
        @classmethod
        @SecurityBlueprint.create(leaf="login")
        def login(cls, request):
            return {"status": 200, "body": {"who": "child"}, "content_type": "application/json"}

    descriptors = Child.register()

    login_descriptors = [
        descriptor for descriptor in descriptors
        if descriptor.path == "/auth/custom/login"
    ]

    if len(login_descriptors) != 1:
        errmsg = "Expected one descriptor for the overridden route, got {}".format(
            len(login_descriptors)
        )
        raise AssertionError(errmsg)

    response = login_descriptors[0].handler(HeaderRequest())
    if response["body"]["who"] != "child":
        errmsg = "Expected the subclass handler to win, got {!r}".format(response["body"])
        raise AssertionError(errmsg)

    return


def test_overridden_handler_registers_with_router_without_conflict():
    """
        Verify that a blueprint with an overridden handler can be added to
        a router; two descriptors for one route would be refused.
    """
    class Parent(SecurityBlueprint):
        base_path = "/auth/custom"

        @classmethod
        @SecurityBlueprint.create(leaf="login")
        def login(cls, request):
            return {"status": 200, "body": {"who": "parent"}, "content_type": "application/json"}

    class Child(Parent):
        @classmethod
        @SecurityBlueprint.create(leaf="login")
        def login(cls, request):
            return {"status": 200, "body": {"who": "child"}, "content_type": "application/json"}

    router = Router()
    Child.register(router=router)

    dispatcher = Dispatcher(router=router, pipeline=MiddlewarePipeline())
    response = dispatcher.dispatch(Request(method="POST", path="/auth/custom/login"))

    if response.status_code != 200 or b"child" not in response.body:
        errmsg = "Expected the subclass handler's response, got {} {!r}".format(
            response.status_code, response.body
        )
        raise AssertionError(errmsg)

    return


def test_descriptor_carries_request_and_response_schema():
    """
        Verify that the schemas given to the endpoint decorator reach the
        descriptor where the OpenAPI generator reads them.
    """
    descriptors = _fresh_session_blueprint().register()

    login = [d for d in descriptors if d.path == "/auth/session/login"][0]
    rest_extras = login.extras.get("rest", {})

    if rest_extras.get("request_schema") is not SessionLoginRequest:
        errmsg = "Expected the request schema on the descriptor, got {!r}".format(rest_extras)
        raise AssertionError(errmsg)

    if rest_extras.get("response_schema") is not SessionInfo:
        errmsg = "Expected the response schema on the descriptor, got {!r}".format(rest_extras)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Registration With the Authentication Middleware
# =============================================================================

def test_exclude_from_auth_lets_login_through_the_middleware():
    """
        Verify that integrate(exclude_from_auth=True) really excludes the
        blueprint's endpoints: an unauthenticated login request reaches
        the application.
    """
    middleware, app = _create_protecting_middleware()
    blueprint = _fresh_session_blueprint()

    if _request_reaches_app(middleware, app, "/auth/session/login"):
        errmsg = "Expected the login path to be protected before integration"
        raise AssertionError(errmsg)

    blueprint.integrate(middleware=middleware, exclude_from_auth=True)

    for path in ("/auth/session/login", "/auth/session/logout", "/auth/session"):
        if not _request_reaches_app(middleware, app, path):
            errmsg = "Expected {!r} to be excluded from authentication".format(path)
            raise AssertionError(errmsg)

    return


def test_exclude_from_auth_does_not_exclude_unrelated_paths():
    """
        Verify that only the blueprint's own endpoints are excluded.
    """
    middleware, app = _create_protecting_middleware()
    _fresh_session_blueprint().integrate(middleware=middleware, exclude_from_auth=True)

    if _request_reaches_app(middleware, app, "/auth/session/login/extra"):
        errmsg = "Expected a path that is not an endpoint to stay protected"
        raise AssertionError(errmsg)

    return


def test_exclude_from_auth_covers_paths_with_route_parameters():
    """
        Verify that an endpoint path with a route parameter is excluded
        for every value of the parameter.
    """
    class FreshKeys(APIKeyBlueprint):
        pass

    FreshKeys.base_path = "/auth/keys"

    middleware, app = _create_protecting_middleware()
    FreshKeys.integrate(middleware=middleware, exclude_from_auth=True)

    if not _request_reaches_app(middleware, app, "/auth/keys/abc123", method="GET"):
        errmsg = "Expected /auth/keys/<key_id> to be excluded from authentication"
        raise AssertionError(errmsg)

    return


def test_optional_auth_registers_every_endpoint_path():
    """
        Verify that integrate(optional_auth=True) makes authentication
        optional for the blueprint's endpoints.
    """
    middleware, app = _create_protecting_middleware()
    _fresh_session_blueprint().integrate(middleware=middleware, optional_auth=True)

    if not _request_reaches_app(middleware, app, "/auth/session/login"):
        errmsg = "Expected the login path to be reachable without credentials"
        raise AssertionError(errmsg)

    return


def test_access_policy_is_registered_for_every_endpoint_path():
    """
        Verify that the blueprint's access policy applies to each endpoint
        path, not only to the base path.
    """
    middleware, _ = _create_protecting_middleware()
    policy = AccessPolicy(roles=["admin"])

    _fresh_session_blueprint().integrate(middleware=middleware, access_policy=policy)

    for path in ("/auth/session/login", "/auth/session/logout", "/auth/session"):
        if middleware.get_policy_for_path(path) is not policy:
            errmsg = "Expected the access policy to apply to {!r}".format(path)
            raise AssertionError(errmsg)

    return


# =============================================================================
# Endpoint Wrapper
# =============================================================================

def _wrapped_handler(blueprint, path):
    """
        Get the handler the router would call for a path.
    """
    for descriptor in blueprint.register():
        if descriptor.path == path:
            return descriptor.handler

    errmsg = "No descriptor for {!r}".format(path)
    raise AssertionError(errmsg)


def _blueprint_with_handler(handler_body, **attributes):
    """
        Create a blueprint with one POST endpoint at /auth/probe/run.
    """
    class Probe(SecurityBlueprint):
        base_path = "/auth/probe"

        @classmethod
        @SecurityBlueprint.create(leaf="run")
        def run(cls, request):
            return handler_body(cls, request)

    for name, value in attributes.items():
        setattr(Probe, name, value)

    return Probe


def test_wrapper_turns_unexpected_error_into_generic_500():
    """
        Verify that an exception raised by a handler becomes the generic
        server_error response and does not leak the exception text.
    """
    def failing(cls, request):
        errmsg = "database password is hunter2"
        raise RuntimeError(errmsg)

    handler = _wrapped_handler(_blueprint_with_handler(failing), "/auth/probe/run")

    response = handler(HeaderRequest())

    if response["status"] != 500:
        errmsg = "Expected status 500, got {}".format(response["status"])
        raise AssertionError(errmsg)

    if response["body"].get("error") != "server_error":
        errmsg = "Expected error 'server_error', got {!r}".format(response["body"])
        raise AssertionError(errmsg)

    if "hunter2" in str(response["body"]):
        errmsg = "Expected the exception text to stay out of the response"
        raise AssertionError(errmsg)

    return


def test_wrapper_lets_http_exceptions_through():
    """
        Verify that an HTTPException raised by a handler reaches the
        dispatcher unchanged.
    """
    def not_found(cls, request):
        raise NotFound()

    handler = _wrapped_handler(_blueprint_with_handler(not_found), "/auth/probe/run")

    try:
        handler(HeaderRequest())
    except NotFound:
        return

    errmsg = "Expected NotFound to propagate through the wrapper"
    raise AssertionError(errmsg)


def test_wrapper_redacts_sensitive_values_from_error_bodies():
    """
        Verify that an error response body is sanitised before it leaves
        the blueprint.
    """
    def leaky(cls, request):
        return {
            "status": 400,
            "body": {"error": "invalid_request", "password": "hunter2"},
            "content_type": "application/json",
        }

    handler = _wrapped_handler(_blueprint_with_handler(leaky), "/auth/probe/run")

    response = handler(HeaderRequest())

    if response["body"].get("password") == "hunter2":
        errmsg = "Expected the password to be redacted from the error body"
        raise AssertionError(errmsg)

    return


def test_wrapper_adds_cors_headers_for_allowed_origin():
    """
        Verify that a response to a request from a configured origin
        carries the CORS headers.
    """
    def ok(cls, request):
        return {"status": 200, "body": {}, "content_type": "application/json"}

    blueprint = _blueprint_with_handler(ok, cors_origins=["https://app.example.com"])
    handler = _wrapped_handler(blueprint, "/auth/probe/run")

    response = handler(HeaderRequest(headers={"Origin": "https://app.example.com"}))

    allowed = response.get("headers", {}).get("Access-Control-Allow-Origin")
    if allowed != "https://app.example.com":
        errmsg = "Expected Access-Control-Allow-Origin for the allowed origin, got {!r}".format(allowed)
        raise AssertionError(errmsg)

    return


def test_wrapper_adds_no_cors_headers_for_other_origin():
    """
        Verify that an origin that is not configured gets no CORS headers.
    """
    def ok(cls, request):
        return {"status": 200, "body": {}, "content_type": "application/json"}

    blueprint = _blueprint_with_handler(ok, cors_origins=["https://app.example.com"])
    handler = _wrapped_handler(blueprint, "/auth/probe/run")

    response = handler(HeaderRequest(headers={"Origin": "https://evil.example.net"}))

    if "Access-Control-Allow-Origin" in response.get("headers", {}):
        errmsg = "Expected no CORS headers for an origin that is not allowed"
        raise AssertionError(errmsg)

    return


def test_wrapper_runs_handler_off_the_event_loop_thread():
    """
        Verify that a synchronous handler called from a running event loop
        is run on a worker thread, and that run_async inside it drives the
        coroutine on that application loop.
    """
    observed = {}

    async def store_call():
        observed["store_loop"] = asyncio.get_running_loop()
        return "stored"

    def blocking(cls, request):
        observed["handler_thread"] = threading.get_ident()
        observed["store_result"] = run_async(store_call())
        return {"status": 200, "body": {}, "content_type": "application/json"}

    handler = _wrapped_handler(_blueprint_with_handler(blocking), "/auth/probe/run")

    async def dispatch():
        observed["loop_thread"] = threading.get_ident()
        observed["application_loop"] = asyncio.get_running_loop()
        result = handler(HeaderRequest())
        if not asyncio.iscoroutine(result):
            errmsg = "Expected a coroutine when called from a running loop"
            raise AssertionError(errmsg)
        response = await result
        return response

    response = asyncio.run(dispatch())

    if response["status"] != 200:
        errmsg = "Expected status 200, got {}".format(response["status"])
        raise AssertionError(errmsg)

    if observed["handler_thread"] == observed["loop_thread"]:
        errmsg = "Expected the handler to run off the event loop thread"
        raise AssertionError(errmsg)

    if observed["store_loop"] is not observed["application_loop"]:
        errmsg = "Expected the store coroutine to run on the application loop"
        raise AssertionError(errmsg)

    if observed["store_result"] != "stored":
        errmsg = "Expected the coroutine result to reach the handler"
        raise AssertionError(errmsg)

    return


def test_run_async_uses_application_loop_under_async_dispatch():
    """
        Verify that a handler dispatched through Dispatcher.dispatch_async
        drives store coroutines on the loop that dispatched it, so a store
        bound to the application loop keeps working.
    """
    observed = {}

    async def store_call():
        observed["store_loop"] = asyncio.get_running_loop()

    def storing(cls, request):
        run_async(store_call())
        return {"status": 200, "body": {}, "content_type": "application/json"}

    blueprint = _blueprint_with_handler(storing)

    router = Router()
    blueprint.register(router=router)
    dispatcher = Dispatcher(router=router, pipeline=MiddlewarePipeline())

    async def dispatch():
        observed["application_loop"] = asyncio.get_running_loop()
        response = await dispatcher.dispatch_async(
            Request(method="POST", path="/auth/probe/run")
        )
        return response

    response = asyncio.run(dispatch())

    if response.status_code != 200:
        errmsg = "Expected status 200, got {}".format(response.status_code)
        raise AssertionError(errmsg)

    if observed.get("store_loop") is not observed["application_loop"]:
        errmsg = "Expected the store coroutine to run on the dispatching loop"
        raise AssertionError(errmsg)

    return


def test_wrapper_calls_handler_directly_without_event_loop():
    """
        Verify that without a running event loop (WSGI, tests) the wrapper
        returns the handler's response, not a coroutine.
    """
    def ok(cls, request):
        return {"status": 200, "body": {"ok": True}, "content_type": "application/json"}

    handler = _wrapped_handler(_blueprint_with_handler(ok), "/auth/probe/run")

    response = handler(HeaderRequest())

    if not isinstance(response, dict) or response["body"] != {"ok": True}:
        errmsg = "Expected the handler's response, got {!r}".format(response)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Request Helpers
# =============================================================================

def test_read_request_data_parses_form_encoded_body():
    """
        Verify that a form-encoded body is read into a dictionary.
    """
    request = Request(
        method="POST",
        path="/auth/token",
        headers={"Content-Type": "application/x-www-form-urlencoded; charset=utf-8"},
        body=b"grant_type=password&username=alice",
    )

    data = SecurityBlueprint.read_request_data(request)

    if data != {"grant_type": "password", "username": "alice"}:
        errmsg = "Expected the form fields, got {!r}".format(data)
        raise AssertionError(errmsg)

    return


def test_read_request_data_rejects_json_that_is_not_an_object():
    """
        Verify that a JSON array body yields None.
    """
    request = Request(
        method="POST",
        path="/auth/token",
        headers={"Content-Type": "application/json"},
        body=b"[]",
    )

    if SecurityBlueprint.read_request_data(request) is not None:
        errmsg = "Expected None for a JSON array body"
        raise AssertionError(errmsg)

    return


def test_read_request_data_rejects_invalid_json():
    """
        Verify that a body that is not valid JSON yields None instead of
        raising.
    """
    request = Request(
        method="POST",
        path="/auth/token",
        headers={"Content-Type": "application/json"},
        body=b"\xff\xfe not json",
    )

    if SecurityBlueprint.read_request_data(request) is not None:
        errmsg = "Expected None for an undecodable body"
        raise AssertionError(errmsg)

    return


def test_get_authenticated_principal_reads_scope_auth():
    """
        Verify that the principal is read from the authentication context
        the middleware stores on the request scope.
    """
    principal = Principal(identifier="alice")
    context = AuthenticationContext(principal=principal, scheme="Test")
    request = Request(method="GET", path="/", scope={"auth": context})

    if SecurityBlueprint.get_authenticated_principal(request) is not principal:
        errmsg = "Expected the principal from scope['auth']"
        raise AssertionError(errmsg)

    return


def test_get_authenticated_principal_is_none_without_context():
    """
        Verify that a request the middleware did not authenticate has no
        principal.
    """
    request = Request(method="GET", path="/", scope={"auth": None})

    if SecurityBlueprint.get_authenticated_principal(request) is not None:
        errmsg = "Expected None without an authentication context"
        raise AssertionError(errmsg)

    return


def test_resolve_public_base_url_honours_allowed_hosts():
    """
        Verify that a Host header outside allowed_hosts is not used to
        build URLs.
    """
    class Restricted(SecurityBlueprint):
        allowed_hosts = ["app.example.com"]

    class ServerRequest:
        scheme = "https"
        host = "10.0.0.5"
        port = 443

        def __init__(self, host_header):
            self.headers = {"Host": host_header}

    accepted = Restricted.resolve_public_base_url(ServerRequest("app.example.com"))
    if accepted != "https://app.example.com":
        errmsg = "Expected the allowed host to be used, got {!r}".format(accepted)
        raise AssertionError(errmsg)

    refused = Restricted.resolve_public_base_url(ServerRequest("evil.example.net"))
    if refused != "https://10.0.0.5":
        errmsg = "Expected the server address for a host that is not allowed, got {!r}".format(refused)
        raise AssertionError(errmsg)

    return


def test_split_scope_accepts_strings_and_collections():
    """
        Verify that scope values are split into unique tokens in order.
    """
    if split_scope("read write read") != ["read", "write"]:
        errmsg = "Expected ['read', 'write'], got {!r}".format(split_scope("read write read"))
        raise AssertionError(errmsg)

    if split_scope(["a", "b"]) != ["a", "b"]:
        errmsg = "Expected ['a', 'b'], got {!r}".format(split_scope(["a", "b"]))
        raise AssertionError(errmsg)

    if split_scope(None) != []:
        errmsg = "Expected [] for None, got {!r}".format(split_scope(None))
        raise AssertionError(errmsg)

    return


def test_restrict_scope_keeps_only_allowed_tokens():
    """
        Verify that a requested scope is reduced to the allowed part.
    """
    if restrict_scope("read admin", ["read", "write"]) != "read":
        errmsg = "Expected 'read', got {!r}".format(restrict_scope("read admin", ["read", "write"]))
        raise AssertionError(errmsg)

    if restrict_scope("admin", ["read"]) is not None:
        errmsg = "Expected None when nothing requested is allowed"
        raise AssertionError(errmsg)

    return


# =============================================================================
# In-Memory Fallback Stores
# =============================================================================

def test_expiring_memory_store_drops_entries_after_ttl():
    """
        Verify that an entry is gone once its time to live has passed.
    """
    store = ExpiringMemoryStore(ttl_seconds=0.05)
    store["code"] = {"client_id": "c1"}

    if "code" not in store:
        errmsg = "Expected the entry to be present before it expires"
        raise AssertionError(errmsg)

    time.sleep(0.1)

    if "code" in store or store.get("code") is not None:
        errmsg = "Expected the entry to be gone after its time to live"
        raise AssertionError(errmsg)

    return


def test_expiring_memory_store_is_bounded():
    """
        Verify that the store never holds more than max_entries entries
        and drops the oldest first.
    """
    store = ExpiringMemoryStore(max_entries=3)

    for index in range(5):
        store["key-{}".format(index)] = index

    if len(store) != 3:
        errmsg = "Expected 3 entries, got {}".format(len(store))
        raise AssertionError(errmsg)

    if "key-0" in store or "key-4" not in store:
        errmsg = "Expected the oldest entries to be dropped, got {!r}".format(list(store))
        raise AssertionError(errmsg)

    return


def test_expiring_memory_store_pop_returns_entry_once():
    """
        Verify that pop removes the entry, so a single-use value cannot be
        taken twice.
    """
    store = ExpiringMemoryStore()
    store["code"] = "value"

    first = store.pop("code", None)
    second = store.pop("code", None)

    if first != "value" or second is not None:
        errmsg = "Expected ('value', None), got ({!r}, {!r})".format(first, second)
        raise AssertionError(errmsg)

    return


def test_blueprint_subclasses_get_their_own_code_and_token_stores():
    """
        Verify that subclasses of a blueprint do not share the in-memory
        code and token stores with each other or with the parent.
    """
    class First(OAuth2Blueprint):
        pass

    class Second(OAuth2Blueprint):
        pass

    stores = [
        OAuth2Blueprint._memory_code_store,
        First._memory_code_store,
        Second._memory_code_store,
    ]

    if stores[0] is stores[1] or stores[1] is stores[2] or stores[0] is stores[2]:
        errmsg = "Expected each class to have its own authorization code store"
        raise AssertionError(errmsg)

    if First._memory_token_store is Second._memory_token_store:
        errmsg = "Expected each class to have its own token store"
        raise AssertionError(errmsg)

    return


def test_blueprint_subclass_starts_with_copy_of_client_registry():
    """
        Verify that a subclass inherits the clients registered on its
        parent at definition time but registers its own separately.
    """
    class Parent(OAuth2Blueprint):
        pass

    Parent._memory_client_store["shared"] = {"client_id": "shared"}

    class Child(Parent):
        pass

    Child._memory_client_store["mine"] = {"client_id": "mine"}

    if "shared" not in Child._memory_client_store:
        errmsg = "Expected the child to start with the parent's clients"
        raise AssertionError(errmsg)

    if "mine" in Parent._memory_client_store:
        errmsg = "Expected a client registered on the child to stay off the parent"
        raise AssertionError(errmsg)

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
