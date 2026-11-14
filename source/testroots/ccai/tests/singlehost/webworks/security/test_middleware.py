"""
    Tests for the security middleware and default-deny enforcement.

    This module contains unit tests for the SecurityMiddleware class,
    default policy configuration, security completeness validation,
    and a property-based test for default-deny enforcement.
"""

import random

from ccai.webworks.security.accesspolicy import AccessPolicy
from ccai.webworks.security.authorizationengine import AuthorizationResult
from ccai.webworks.security.errors import SecurityCompletenessError
from ccai.webworks.security.middleware import (
    SecurityMiddleware,
    validate_security_completeness,
)
from ccai.webworks.security.policyattachment import attach_policy
from ccai.webworks.security.securitycontext import SecurityContext
from ccai.testbase.mocking import Mock


# =============================================================================
# Helper Functions
# =============================================================================

def _create_mock_auth_manager(context=None):
    """
        Create a mock Authentication_Manager that returns the given context.

        :param context: The Security_Context to return from authenticate().
            Defaults to a guest context.

        :returns: A Mock configured as an Authentication_Manager.
    """
    if context is None:
        context = SecurityContext.guest()

    mock_manager = Mock()
    mock_manager.configure(recursive=True)
    mock_manager.mock_context().mock_method("authenticate", return_value=context)

    return mock_manager


def _create_mock_authz_engine(allowed=True, reason=None):
    """
        Create a mock Authorization_Engine that returns the given result.

        :param allowed: Whether authorization is allowed.
        :param reason: The reason for the decision.

        :returns: A Mock configured as an Authorization_Engine.
    """
    result = AuthorizationResult(allowed=allowed, reason=reason)

    mock_engine = Mock()
    mock_engine.configure(recursive=True)
    mock_engine.mock_context().mock_method("evaluate", return_value=result)

    return mock_engine


def _create_mock_audit_logger():
    """
        Create a mock Audit_Logger.

        :returns: A Mock configured as an Audit_Logger.
    """
    mock_logger = Mock()
    mock_logger.configure(recursive=True)
    mock_logger.mock_context().mock_method("log_authentication")
    mock_logger.mock_context().mock_method("log_authorization")
    mock_logger.mock_context().mock_method("log_violation")

    return mock_logger


def _create_request(path="/test", constraints=None, headers=None):
    """
        Create a request dictionary for testing.

        :param path: The request path.
        :param constraints: The endpoint constraints dictionary.
        :param headers: The request headers dictionary.

        :returns: A request dictionary.
    """
    request = {
        "path": path,
        "headers": headers if headers is not None else {},
        "cookies": {},
        "query_params": {},
    }

    if constraints is not None:
        request["constraints"] = constraints

    return request


def _success_handler(request):
    """
        A simple next handler that returns a 200 response.

        :param request: The incoming request (unused).

        :returns: A response dictionary with status_code 200.
    """
    response = {"status_code": 200, "body": {"message": "OK"}}
    return response


# =============================================================================
# Unit Tests for SecurityMiddleware (Task 11.1)
# =============================================================================

def test_middleware_allows_authenticated_request_with_matching_policy():
    """
        Test that the middleware allows a request when the user is
        authenticated and satisfies the endpoint policy.
    """
    context = SecurityContext(
        user_id="user-1",
        roles=("admin",),
        scopes=("read",),
        provider="jwt",
    )

    policy = AccessPolicy(roles=("admin",), scopes=("read",))
    constraints = {}
    attach_policy(constraints, policy)

    auth_manager = _create_mock_auth_manager(context)
    authz_engine = _create_mock_authz_engine(allowed=True)
    audit_logger = _create_mock_audit_logger()

    middleware = SecurityMiddleware(
        auth_manager=auth_manager,
        authz_engine=authz_engine,
        audit_logger=audit_logger,
    )

    request = _create_request(path="/api/data", constraints=constraints)
    response = middleware(request, _success_handler)

    if response["status_code"] != 200:
        errmsg = f"Expected status_code 200, got {response['status_code']}"
        raise AssertionError(errmsg)

    return


def test_middleware_returns_401_for_unauthenticated_request():
    """
        Test that the middleware returns a 401 response when the user
        is not authenticated and the policy requires authentication.
    """
    guest_context = SecurityContext.guest()

    policy = AccessPolicy(require_auth=True)
    constraints = {}
    attach_policy(constraints, policy)

    auth_manager = _create_mock_auth_manager(guest_context)
    authz_engine = _create_mock_authz_engine(
        allowed=False, reason="Authentication is required"
    )
    audit_logger = _create_mock_audit_logger()

    middleware = SecurityMiddleware(
        auth_manager=auth_manager,
        authz_engine=authz_engine,
        audit_logger=audit_logger,
    )

    request = _create_request(path="/api/secure", constraints=constraints)
    response = middleware(request, _success_handler)

    if response["status_code"] != 401:
        errmsg = f"Expected status_code 401, got {response['status_code']}"
        raise AssertionError(errmsg)

    body = response["body"]
    if body["error"] != "AUTHENTICATION_REQUIRED":
        errmsg = f"Expected error AUTHENTICATION_REQUIRED, got {body['error']}"
        raise AssertionError(errmsg)

    headers = response.get("headers", {})
    if "WWW-Authenticate" not in headers:
        errmsg = "Expected WWW-Authenticate header in 401 response"
        raise AssertionError(errmsg)

    return


def test_middleware_returns_403_for_unauthorized_request():
    """
        Test that the middleware returns a 403 response when the user
        is authenticated but lacks the required permissions.
    """
    context = SecurityContext(
        user_id="user-1",
        roles=("viewer",),
        provider="jwt",
    )

    policy = AccessPolicy(roles=("admin",))
    constraints = {}
    attach_policy(constraints, policy)

    auth_manager = _create_mock_auth_manager(context)
    authz_engine = _create_mock_authz_engine(
        allowed=False, reason="Missing required role"
    )
    audit_logger = _create_mock_audit_logger()

    middleware = SecurityMiddleware(
        auth_manager=auth_manager,
        authz_engine=authz_engine,
        audit_logger=audit_logger,
    )

    request = _create_request(path="/api/admin", constraints=constraints)
    response = middleware(request, _success_handler)

    if response["status_code"] != 403:
        errmsg = f"Expected status_code 403, got {response['status_code']}"
        raise AssertionError(errmsg)

    body = response["body"]
    if body["error"] != "ACCESS_DENIED":
        errmsg = f"Expected error ACCESS_DENIED, got {body['error']}"
        raise AssertionError(errmsg)

    return


def test_middleware_uses_default_policy_when_no_explicit_policy():
    """
        Test that the middleware applies the default policy when the
        endpoint has no explicit policy attached.
    """
    context = SecurityContext(user_id="user-1", provider="jwt")

    default_policy = AccessPolicy(require_auth=True)

    auth_manager = _create_mock_auth_manager(context)
    authz_engine = _create_mock_authz_engine(allowed=True)
    audit_logger = _create_mock_audit_logger()

    middleware = SecurityMiddleware(
        auth_manager=auth_manager,
        authz_engine=authz_engine,
        audit_logger=audit_logger,
        default_policy=default_policy,
    )

    request = _create_request(path="/api/data")
    response = middleware(request, _success_handler)

    if response["status_code"] != 200:
        errmsg = f"Expected status_code 200, got {response['status_code']}"
        raise AssertionError(errmsg)

    return


def test_middleware_denies_when_no_policy_and_no_default():
    """
        Test that the middleware denies access when the endpoint has no
        explicit policy and no default policy is configured (default-deny).
    """
    guest_context = SecurityContext.guest()

    auth_manager = _create_mock_auth_manager(guest_context)
    authz_engine = _create_mock_authz_engine(
        allowed=False, reason="Authentication is required"
    )
    audit_logger = _create_mock_audit_logger()

    middleware = SecurityMiddleware(
        auth_manager=auth_manager,
        authz_engine=authz_engine,
        audit_logger=audit_logger,
    )

    request = _create_request(path="/api/unprotected")
    response = middleware(request, _success_handler)

    if response["status_code"] != 401:
        errmsg = f"Expected status_code 401, got {response['status_code']}"
        raise AssertionError(errmsg)

    return


def test_middleware_calls_next_handler_on_success():
    """
        Test that the middleware calls the next handler and returns its
        response when authorization succeeds.
    """
    context = SecurityContext(user_id="user-1", provider="jwt")

    call_tracker = {"called": False}

    def tracking_handler(req):
        call_tracker["called"] = True
        return {"status_code": 200, "body": {"data": "test"}}

    auth_manager = _create_mock_auth_manager(context)
    authz_engine = _create_mock_authz_engine(allowed=True)
    audit_logger = _create_mock_audit_logger()

    policy = AccessPolicy(require_auth=True)
    constraints = {}
    attach_policy(constraints, policy)

    middleware = SecurityMiddleware(
        auth_manager=auth_manager,
        authz_engine=authz_engine,
        audit_logger=audit_logger,
    )

    request = _create_request(path="/api/data", constraints=constraints)
    response = middleware(request, tracking_handler)

    if call_tracker["called"] is not True:
        errmsg = "Expected next handler to be called"
        raise AssertionError(errmsg)

    if response["body"]["data"] != "test":
        errmsg = f"Expected response body data 'test', got {response['body']['data']}"
        raise AssertionError(errmsg)

    return


def test_get_policy_for_endpoint_returns_attached_policy():
    """
        Test that get_policy_for_endpoint returns the attached policy
        when one is present in the constraints.
    """
    auth_manager = _create_mock_auth_manager()
    authz_engine = _create_mock_authz_engine()
    audit_logger = _create_mock_audit_logger()

    middleware = SecurityMiddleware(
        auth_manager=auth_manager,
        authz_engine=authz_engine,
        audit_logger=audit_logger,
    )

    policy = AccessPolicy(roles=("admin",), scopes=("write",))
    constraints = {}
    attach_policy(constraints, policy)

    result = middleware.get_policy_for_endpoint(constraints)

    if result is not policy:
        errmsg = "Expected get_policy_for_endpoint to return the attached policy"
        raise AssertionError(errmsg)

    return


def test_get_policy_for_endpoint_returns_default_when_no_attached():
    """
        Test that get_policy_for_endpoint returns the default policy
        when no policy is attached to the endpoint.
    """
    default_policy = AccessPolicy(require_auth=True, roles=("user",))

    auth_manager = _create_mock_auth_manager()
    authz_engine = _create_mock_authz_engine()
    audit_logger = _create_mock_audit_logger()

    middleware = SecurityMiddleware(
        auth_manager=auth_manager,
        authz_engine=authz_engine,
        audit_logger=audit_logger,
        default_policy=default_policy,
    )

    constraints = {}
    result = middleware.get_policy_for_endpoint(constraints)

    if result is not default_policy:
        errmsg = "Expected get_policy_for_endpoint to return the default policy"
        raise AssertionError(errmsg)

    return


def test_get_policy_for_endpoint_returns_deny_all_when_no_default():
    """
        Test that get_policy_for_endpoint returns a deny-all policy
        when no policy is attached and no default is configured.
    """
    auth_manager = _create_mock_auth_manager()
    authz_engine = _create_mock_authz_engine()
    audit_logger = _create_mock_audit_logger()

    middleware = SecurityMiddleware(
        auth_manager=auth_manager,
        authz_engine=authz_engine,
        audit_logger=audit_logger,
    )

    constraints = {}
    result = middleware.get_policy_for_endpoint(constraints)

    if result.require_auth is not True:
        errmsg = "Expected deny-all policy to require authentication"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Default Policy Configuration (Task 11.2)
# =============================================================================

def test_middleware_accepts_default_access_policy():
    """
        Test that the SecurityMiddleware accepts a default_access_policy
        setting at the application level.
    """
    default_policy = AccessPolicy(require_auth=True, roles=("user",))

    auth_manager = _create_mock_auth_manager()
    authz_engine = _create_mock_authz_engine()
    audit_logger = _create_mock_audit_logger()

    middleware = SecurityMiddleware(
        auth_manager=auth_manager,
        authz_engine=authz_engine,
        audit_logger=audit_logger,
        default_policy=default_policy,
    )

    if middleware._default_policy is not default_policy:
        errmsg = "Expected middleware to store the default policy"
        raise AssertionError(errmsg)

    return


def test_middleware_accepts_security_audit_mode():
    """
        Test that the SecurityMiddleware accepts a security_audit_mode
        setting for gradual migration.
    """
    auth_manager = _create_mock_auth_manager()
    authz_engine = _create_mock_authz_engine()
    audit_logger = _create_mock_audit_logger()

    middleware = SecurityMiddleware(
        auth_manager=auth_manager,
        authz_engine=authz_engine,
        audit_logger=audit_logger,
        security_audit_mode=True,
    )

    if middleware._security_audit_mode is not True:
        errmsg = "Expected middleware to store security_audit_mode as True"
        raise AssertionError(errmsg)

    return


def test_middleware_audit_mode_allows_unauthorized_request():
    """
        Test that in security_audit_mode, unauthorized requests are
        allowed to proceed with a warning logged.
    """
    context = SecurityContext(user_id="user-1", provider="jwt")

    auth_manager = _create_mock_auth_manager(context)
    authz_engine = _create_mock_authz_engine(
        allowed=False, reason="Missing required role"
    )
    audit_logger = _create_mock_audit_logger()

    middleware = SecurityMiddleware(
        auth_manager=auth_manager,
        authz_engine=authz_engine,
        audit_logger=audit_logger,
        security_audit_mode=True,
    )

    policy = AccessPolicy(roles=("admin",))
    constraints = {}
    attach_policy(constraints, policy)

    request = _create_request(path="/api/admin", constraints=constraints)
    response = middleware(request, _success_handler)

    # In audit mode, the request should be allowed through
    if response["status_code"] != 200:
        errmsg = (
            f"Expected status_code 200 in audit mode, "
            f"got {response['status_code']}"
        )
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Security Completeness Validation (Task 11.3)
# =============================================================================

def test_validate_completeness_passes_when_all_endpoints_have_policies():
    """
        Test that validate_security_completeness passes when all endpoints
        have explicit policies attached.
    """
    policy = AccessPolicy(require_auth=True)

    constraints_a = {}
    attach_policy(constraints_a, policy)

    constraints_b = {}
    attach_policy(constraints_b, policy)

    endpoints = [
        {"path": "/api/a", "constraints": constraints_a},
        {"path": "/api/b", "constraints": constraints_b},
    ]

    # Should not raise
    validate_security_completeness(endpoints)

    return


def test_validate_completeness_passes_when_default_policy_configured():
    """
        Test that validate_security_completeness passes when endpoints
        lack explicit policies but a default policy is configured.
    """
    default_policy = AccessPolicy(require_auth=True)

    endpoints = [
        {"path": "/api/a", "constraints": {}},
        {"path": "/api/b", "constraints": {}},
    ]

    # Should not raise because default_policy covers the endpoints
    validate_security_completeness(endpoints, default_policy=default_policy)

    return


def test_validate_completeness_raises_when_unprotected_endpoints():
    """
        Test that validate_security_completeness raises
        SecurityCompletenessError when endpoints lack policies and
        no default policy is configured.
    """
    endpoints = [
        {"path": "/api/a", "constraints": {}},
        {"path": "/api/b", "constraints": {}},
    ]

    caught = False
    caught_error = None

    try:
        validate_security_completeness(endpoints)
    except SecurityCompletenessError as exc:
        caught = True
        caught_error = exc

    if caught is not True:
        errmsg = "Expected SecurityCompletenessError to be raised"
        raise AssertionError(errmsg)

    if len(caught_error.unprotected_endpoints) != 2:
        errmsg = (
            f"Expected 2 unprotected endpoints, "
            f"got {len(caught_error.unprotected_endpoints)}"
        )
        raise AssertionError(errmsg)

    if "/api/a" not in caught_error.unprotected_endpoints:
        errmsg = "Expected /api/a in unprotected endpoints"
        raise AssertionError(errmsg)

    if "/api/b" not in caught_error.unprotected_endpoints:
        errmsg = "Expected /api/b in unprotected endpoints"
        raise AssertionError(errmsg)

    return


def test_validate_completeness_audit_mode_logs_warnings():
    """
        Test that validate_security_completeness logs warnings instead
        of raising errors when audit_mode is True.
    """
    endpoints = [
        {"path": "/api/a", "constraints": {}},
        {"path": "/api/b", "constraints": {}},
    ]

    # Should not raise in audit mode
    caught = False

    try:
        validate_security_completeness(endpoints, audit_mode=True)
    except SecurityCompletenessError:
        caught = True

    if caught is True:
        errmsg = (
            "Expected no SecurityCompletenessError in audit mode, "
            "but one was raised"
        )
        raise AssertionError(errmsg)

    return


def test_validate_completeness_mixed_endpoints():
    """
        Test that validate_security_completeness correctly identifies
        only the unprotected endpoints in a mixed set.
    """
    policy = AccessPolicy(require_auth=True)

    constraints_protected = {}
    attach_policy(constraints_protected, policy)

    endpoints = [
        {"path": "/api/protected", "constraints": constraints_protected},
        {"path": "/api/unprotected", "constraints": {}},
    ]

    caught = False
    caught_error = None

    try:
        validate_security_completeness(endpoints)
    except SecurityCompletenessError as exc:
        caught = True
        caught_error = exc

    if caught is not True:
        errmsg = "Expected SecurityCompletenessError to be raised"
        raise AssertionError(errmsg)

    if len(caught_error.unprotected_endpoints) != 1:
        errmsg = (
            f"Expected 1 unprotected endpoint, "
            f"got {len(caught_error.unprotected_endpoints)}"
        )
        raise AssertionError(errmsg)

    if caught_error.unprotected_endpoints[0] != "/api/unprotected":
        errmsg = (
            f"Expected /api/unprotected, "
            f"got {caught_error.unprotected_endpoints[0]}"
        )
        raise AssertionError(errmsg)

    return


def test_validate_completeness_empty_endpoints():
    """
        Test that validate_security_completeness passes with an empty
        endpoint list.
    """
    # Should not raise
    validate_security_completeness([])

    return


# =============================================================================
# Property-Based Tests (Task 11.4)
# =============================================================================

def _random_role_pool():
    """
        Generate a pool of role names to draw from during property testing.

        :returns: A list of role name strings.
    """
    pool = [
        "admin", "editor", "viewer", "moderator", "superadmin",
        "manager", "analyst", "operator", "auditor", "developer"
    ]
    return pool


def _random_scope_pool():
    """
        Generate a pool of scope names to draw from during property testing.

        :returns: A list of scope name strings.
    """
    pool = [
        "read", "write", "delete", "create", "update",
        "execute", "manage", "audit", "export", "import"
    ]
    return pool


def _random_access_policy(role_pool, scope_pool):
    """
        Generate a random AccessPolicy with random roles, scopes, and
        require_auth setting.

        :param role_pool: List of possible role names.
        :param scope_pool: List of possible scope names.

        :returns: A randomly configured AccessPolicy.
    """
    num_roles = random.randint(0, 4)
    roles = tuple(random.sample(role_pool, min(num_roles, len(role_pool))))

    num_scopes = random.randint(0, 4)
    scopes = tuple(random.sample(scope_pool, min(num_scopes, len(scope_pool))))

    require_auth = random.choice([True, False])

    policy = AccessPolicy(roles=roles, scopes=scopes, require_auth=require_auth)
    return policy


def test_property_default_deny_enforcement():
    """
        Property 9: Default-Deny Enforcement

        **Validates: Requirements 6.1, 6.2**

        For any endpoint without an explicit AccessPolicy:
        - The system SHALL apply the configured default_access_policy
        - If no default is configured, access SHALL be denied
        - The effective policy SHALL never be less restrictive than the default

        This test runs 100 iterations with randomly generated policies and
        endpoint configurations to verify the default-deny properties hold
        universally.
    """
    role_pool = _random_role_pool()
    scope_pool = _random_scope_pool()

    iterations = 100

    for iteration_idx in range(iterations):
        # Randomly decide if a default policy is configured
        has_default = random.choice([True, False])

        if has_default:
            default_policy = _random_access_policy(role_pool, scope_pool)
        else:
            default_policy = None

        # Randomly decide if the endpoint has an explicit policy
        has_explicit = random.choice([True, False])

        if has_explicit:
            explicit_policy = _random_access_policy(role_pool, scope_pool)
        else:
            explicit_policy = None

        # Build the constraints dict
        constraints = {}
        if explicit_policy is not None:
            attach_policy(constraints, explicit_policy)

        # Create the middleware
        auth_manager = _create_mock_auth_manager()
        authz_engine = _create_mock_authz_engine()
        audit_logger = _create_mock_audit_logger()

        middleware = SecurityMiddleware(
            auth_manager=auth_manager,
            authz_engine=authz_engine,
            audit_logger=audit_logger,
            default_policy=default_policy,
        )

        # Get the effective policy
        effective_policy = middleware.get_policy_for_endpoint(constraints)

        # Property 9a: When endpoint has an explicit policy, use it
        if explicit_policy is not None:
            if effective_policy is not explicit_policy:
                errmsg = (
                    f"Iteration {iteration_idx}: When endpoint has an "
                    f"explicit policy, get_policy_for_endpoint should "
                    f"return that policy"
                )
                raise AssertionError(errmsg)

        # Property 9b: When no explicit policy, apply default_access_policy
        if explicit_policy is None and default_policy is not None:
            if effective_policy is not default_policy:
                errmsg = (
                    f"Iteration {iteration_idx}: When no explicit policy "
                    f"and default is configured, get_policy_for_endpoint "
                    f"should return the default policy"
                )
                raise AssertionError(errmsg)

        # Property 9c: When no explicit and no default, deny access
        # The deny-all policy requires authentication, so unauthenticated
        # users will be denied
        if explicit_policy is None and default_policy is None:
            if effective_policy.require_auth is not True:
                errmsg = (
                    f"Iteration {iteration_idx}: When no explicit policy "
                    f"and no default is configured, the effective policy "
                    f"must require authentication (default-deny)"
                )
                raise AssertionError(errmsg)

        # Property 9d: Effective policy is never less restrictive than default
        # When a default is configured and no explicit policy exists,
        # the effective policy must be the default itself
        if explicit_policy is None and default_policy is not None:
            # The effective policy should be exactly the default
            if effective_policy.require_auth != default_policy.require_auth:
                errmsg = (
                    f"Iteration {iteration_idx}: Effective policy "
                    f"require_auth ({effective_policy.require_auth}) "
                    f"differs from default ({default_policy.require_auth})"
                )
                raise AssertionError(errmsg)

            if set(effective_policy.roles) != set(default_policy.roles):
                errmsg = (
                    f"Iteration {iteration_idx}: Effective policy roles "
                    f"({effective_policy.roles}) differ from default "
                    f"({default_policy.roles})"
                )
                raise AssertionError(errmsg)

            if set(effective_policy.scopes) != set(default_policy.scopes):
                errmsg = (
                    f"Iteration {iteration_idx}: Effective policy scopes "
                    f"({effective_policy.scopes}) differ from default "
                    f"({default_policy.scopes})"
                )
                raise AssertionError(errmsg)

    return


# =============================================================================
# Routing Request / Response integration
# =============================================================================

import asyncio
import base64
import hashlib
import hmac
import json
import time

from ccai.webworks.endpoints.constraints import EndpointConstraints
from ccai.webworks.endpoints.descriptor import EndpointDescriptor
from ccai.webworks.routing.dispatcher import Dispatcher
from ccai.webworks.routing.request import Request
from ccai.webworks.routing.response import Response
from ccai.webworks.routing.router import Router
from ccai.webworks.security.auditlogger import AuditLogger
from ccai.webworks.security.authenticationmanager import AuthenticationManager
from ccai.webworks.security.authenticationprovider import JWTAuthProvider
from ccai.webworks.security.authorizationengine import AuthorizationEngine
from ccai.webworks.security.policyattachment import get_attached_policy
from ccai.webworks.security.securitycontext import SECURITY_CONTEXT_SCOPE_KEY


PIPELINE_SECRET_KEY = "pipeline-test-secret-key-0123456789abcdef"


def _sign_token(payload: dict) -> str:
    """
        Create an HS256 token over ``payload`` signed with the test secret.
    """
    def encode(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

    header = encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode("utf-8"))
    body = encode(json.dumps(payload).encode("utf-8"))
    signing_input = "{}.{}".format(header, body).encode("ascii")
    signature = hmac.new(PIPELINE_SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()
    return "{}.{}.{}".format(header, body, encode(signature))


def _create_pipeline_dispatcher(policy=None, **middleware_options):
    """
        Create a dispatcher whose route pipeline holds a SecurityMiddleware
        backed by the real JWT provider, with one route at /reports.
    """
    auth_manager = AuthenticationManager()
    auth_manager.register_provider(JWTAuthProvider(secret_key=PIPELINE_SECRET_KEY))

    middleware = SecurityMiddleware(
        auth_manager=auth_manager,
        authz_engine=AuthorizationEngine(),
        audit_logger=AuditLogger(),
        **middleware_options
    )

    def handler(request):
        return {"user": request.scope[SECURITY_CONTEXT_SCOPE_KEY].user_id}

    descriptor = EndpointDescriptor(
        handler=handler,
        module="test",
        path="/reports",
        methods=["GET"],
        constraints=EndpointConstraints(access_policy=policy),
    )

    router = Router()
    router.add_endpoint(descriptor)

    dispatcher = Dispatcher(router)
    dispatcher.route_pipeline.add(middleware)

    return dispatcher


def _bearer_headers(roles):
    """
        Build request headers carrying a valid bearer token with ``roles``.
    """
    token = _sign_token({"sub": "user-1", "roles": roles, "exp": int(time.time()) + 600})
    return {"Authorization": "Bearer {}".format(token)}


def test_middleware_authenticates_routing_request_with_jwt_provider():
    """
        In the dispatcher pipeline the middleware authenticates a routing
        Request through a built-in provider and lets an authorized request
        reach the handler.
    """
    dispatcher = _create_pipeline_dispatcher(AccessPolicy(roles=("analyst",)))

    request = Request(method="GET", path="/reports", headers=_bearer_headers(["analyst"]))
    response = dispatcher.dispatch(request)

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.body!r}"
    assert b"user-1" in response.body, f"Unexpected body {response.body!r}"
    return


def test_middleware_returns_401_response_object_for_anonymous_routing_request():
    """
        An anonymous routing Request is refused with a routing Response the
        pipeline can send, not a dictionary.
    """
    dispatcher = _create_pipeline_dispatcher(AccessPolicy(roles=("analyst",)))

    response = dispatcher.dispatch(Request(method="GET", path="/reports"))

    assert isinstance(response, Response), f"Expected a Response, got {type(response).__name__}"
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    assert response.headers.get("WWW-Authenticate") == "Bearer", f"Unexpected headers {response.headers}"
    return


def test_middleware_returns_403_for_routing_request_without_role():
    """
        An authenticated routing Request without the required role is refused 403.
    """
    dispatcher = _create_pipeline_dispatcher(AccessPolicy(roles=("analyst",)))

    request = Request(method="GET", path="/reports", headers=_bearer_headers(["viewer"]))
    response = dispatcher.dispatch(request)

    assert response.status_code == 403, f"Expected 403, got {response.status_code}"
    return


def test_middleware_denies_endpoint_without_policy_by_default():
    """
        Default deny: an endpoint without a policy and no default policy
        configured requires authentication.
    """
    dispatcher = _create_pipeline_dispatcher(policy=None)

    anonymous = dispatcher.dispatch(Request(method="GET", path="/reports"))
    authenticated = dispatcher.dispatch(
        Request(method="GET", path="/reports", headers=_bearer_headers([])))

    assert anonymous.status_code == 401, f"Expected 401, got {anonymous.status_code}"
    assert authenticated.status_code == 200, f"Expected 200, got {authenticated.status_code}"
    return


def test_middleware_runs_in_async_dispatch():
    """
        The middleware works in dispatch_async through call_async.
    """
    dispatcher = _create_pipeline_dispatcher(AccessPolicy(roles=("analyst",)))

    request = Request(method="GET", path="/reports", headers=_bearer_headers(["analyst"]))
    response = asyncio.run(dispatcher.dispatch_async(request))

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    return


def test_get_attached_policy_reads_endpoint_constraints_object():
    """
        The policy of a real descriptor is stored on an EndpointConstraints
        object, not in a dictionary.
    """
    policy = AccessPolicy(roles=("analyst",))
    constraints = EndpointConstraints(access_policy=policy)

    assert get_attached_policy(constraints) is policy
    assert get_attached_policy(EndpointConstraints()) is None
    return


def test_validate_completeness_accepts_endpoint_descriptors():
    """
        The completeness check runs on the descriptors a router is built from.
    """
    def handler(request):
        return {}

    protected = EndpointDescriptor(
        handler=handler, module="test", path="/protected",
        constraints=EndpointConstraints(access_policy=AccessPolicy(require_auth=True)),
    )
    unprotected = EndpointDescriptor(handler=handler, module="test", path="/open")

    validate_security_completeness([protected])

    raised = None
    try:
        validate_security_completeness([protected, unprotected])
    except SecurityCompletenessError as exc:
        raised = exc

    assert raised is not None, "Expected SecurityCompletenessError for the unprotected endpoint"
    assert raised.unprotected_endpoints == ["/open"], f"Unexpected list {raised.unprotected_endpoints}"
    return
