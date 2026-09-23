"""
    Property test for cache consistency in the OpenAPI generator.

    This module verifies Property 7: Cache Consistency.

    For any cached specification, retrieving from cache SHALL return a
    specification equivalent to regenerating from the same endpoint
    registry state.

    **Validates: Requirements 12.1, 12.2**
"""

from ccai.testbase.mocking import Mock

from ccai.webworks.openapi.cache import CachedOpenAPIGenerator
from ccai.webworks.openapi.configuration import OpenAPIInfo, ServerObject
from ccai.webworks.openapi.generator import OpenAPIGenerator
from ccai.webworks.openapi.securityschemes import (
    APIKeySecurityScheme,
    HTTPSecurityScheme,
    OAuth2SecurityScheme,
    OAuthFlow,
    OAuthFlows,
)


# =============================================================================
# Helper Functions
# =============================================================================

class _HandlerStub:
    """
        A simple stub that provides a __name__ attribute for mock handlers.
    """

    def __init__(self, name):
        self.__name__ = name

    def __call__(self):
        pass


def _create_mock_doc(summary=None, description=None):
    """
        Create a mock Doc object with the given attributes.
    """
    mock_doc = Mock()
    mock_doc.configure(recursive=True)
    ctx = mock_doc.mock_context()
    ctx.set_attribute("summary", summary)
    ctx.set_attribute("description", description)
    ctx.set_attribute("deprecated", False)
    ctx.set_attribute("external_docs", None)
    return mock_doc


def _create_mock_access_policy(require_auth=True, scopes=None, roles=None):
    """
        Create a mock AccessPolicy object.
    """
    mock_policy = Mock()
    mock_policy.configure(recursive=True)
    ctx = mock_policy.mock_context()
    ctx.set_attribute("require_auth", require_auth)
    ctx.set_attribute("scopes", scopes or [])
    ctx.set_attribute("roles", roles or [])
    return mock_policy


def _create_mock_constraints(access_policy=None):
    """
        Create a mock EndpointConstraints object.
    """
    mock_constraints = Mock()
    mock_constraints.configure(recursive=True)
    ctx = mock_constraints.mock_context()
    ctx.set_attribute("access_policy", access_policy)
    return mock_constraints


def _create_mock_descriptor(
    handler_name="test_handler",
    path="/test",
    methods=None,
    tags=None,
    doc=None,
    extras=None,
    constraints=None,
):
    """
        Create a mock EndpointDescriptor with the given attributes.
    """
    mock = Mock()
    mock.configure(recursive=True)
    ctx = mock.mock_context()

    handler = _HandlerStub(handler_name)

    ctx.set_attribute("handler", handler)
    ctx.set_attribute("module", "test_module")
    ctx.set_attribute("path", path)
    ctx.set_attribute("leaf", None)
    ctx.set_attribute("methods", methods or ["GET"])
    ctx.set_attribute("tags", tags or [])
    ctx.set_attribute("doc", doc)
    resolved_extras = extras or {}
    if "endpoint_type" not in resolved_extras:
        resolved_extras = dict(resolved_extras)
        resolved_extras["endpoint_type"] = "rest"
    ctx.set_attribute("extras", resolved_extras)
    ctx.set_attribute("constraints", constraints or _create_mock_constraints())
    ctx.set_attribute("version", None)

    return mock


def _create_mock_registry(descriptors):
    """
        Create a mock EndpointRegistry that returns the given descriptors.
    """
    mock_registry = Mock()
    mock_registry.configure(recursive=True)
    mock_registry.mock_context().mock_method("collect", return_value=descriptors)
    return mock_registry


def _create_default_info():
    """
        Create a default OpenAPIInfo for testing.
    """
    return OpenAPIInfo(title="Test API", version="1.0.0")


# =============================================================================
# Test Cases: Diverse registry configurations
# =============================================================================

_CACHE_CONSISTENCY_CASES = [
    (
        "empty specification with no endpoints",
        {
            "endpoints": [],
            "security_schemes": {},
            "servers": [],
            "tag_descriptions": {},
        },
    ),
    (
        "single GET endpoint",
        {
            "endpoints": [
                {
                    "handler_name": "get_items",
                    "path": "/items",
                    "methods": ["GET"],
                    "tags": ["items"],
                },
            ],
            "security_schemes": {},
            "servers": [],
            "tag_descriptions": {},
        },
    ),
    (
        "multiple endpoints with different methods",
        {
            "endpoints": [
                {
                    "handler_name": "list_users",
                    "path": "/users",
                    "methods": ["GET"],
                    "tags": ["users"],
                },
                {
                    "handler_name": "create_user",
                    "path": "/users",
                    "methods": ["POST"],
                    "tags": ["users"],
                },
                {
                    "handler_name": "get_user",
                    "path": "/users/{id:int}",
                    "methods": ["GET"],
                    "tags": ["users"],
                },
            ],
            "security_schemes": {},
            "servers": [],
            "tag_descriptions": {"users": "User management endpoints"},
        },
    ),
    (
        "endpoint with path parameters",
        {
            "endpoints": [
                {
                    "handler_name": "get_item",
                    "path": "/items/{item_id:int}",
                    "methods": ["GET"],
                    "tags": ["items"],
                },
            ],
            "security_schemes": {},
            "servers": [ServerObject(url="https://api.example.com")],
            "tag_descriptions": {},
        },
    ),
    (
        "endpoint with bearer security",
        {
            "endpoints": [
                {
                    "handler_name": "get_secret",
                    "path": "/secret",
                    "methods": ["GET"],
                    "tags": ["admin"],
                    "require_auth": True,
                },
            ],
            "security_schemes": {
                "bearerAuth": HTTPSecurityScheme(scheme="bearer"),
            },
            "servers": [],
            "tag_descriptions": {},
        },
    ),
    (
        "multiple servers configured",
        {
            "endpoints": [
                {
                    "handler_name": "health_check",
                    "path": "/health",
                    "methods": ["GET"],
                    "tags": ["system"],
                },
            ],
            "security_schemes": {},
            "servers": [
                ServerObject(url="https://api.example.com", description="Production"),
                ServerObject(url="https://staging.example.com", description="Staging"),
            ],
            "tag_descriptions": {},
        },
    ),
    (
        "endpoint with multiple tags",
        {
            "endpoints": [
                {
                    "handler_name": "admin_users",
                    "path": "/admin/users",
                    "methods": ["GET", "POST"],
                    "tags": ["admin", "users"],
                },
            ],
            "security_schemes": {},
            "servers": [],
            "tag_descriptions": {
                "admin": "Administration endpoints",
                "users": "User management",
            },
        },
    ),
    (
        "api key security scheme",
        {
            "endpoints": [
                {
                    "handler_name": "get_data",
                    "path": "/data",
                    "methods": ["GET"],
                    "tags": ["data"],
                    "require_auth": True,
                },
            ],
            "security_schemes": {
                "apiKey": APIKeySecurityScheme(name="X-API-Key", in_="header"),
            },
            "servers": [],
            "tag_descriptions": {},
        },
    ),
    (
        "oauth2 security scheme with scopes",
        {
            "endpoints": [
                {
                    "handler_name": "get_profile",
                    "path": "/profile",
                    "methods": ["GET"],
                    "tags": ["profile"],
                    "require_auth": True,
                    "scopes": ["read:profile"],
                },
            ],
            "security_schemes": {
                "oauth2": OAuth2SecurityScheme(
                    flows=OAuthFlows(
                        authorization_code=OAuthFlow(
                            authorization_url="https://auth.example.com/authorize",
                            token_url="https://auth.example.com/token",
                            scopes={"read:profile": "Read profile data"},
                        ),
                    ),
                ),
            },
            "servers": [],
            "tag_descriptions": {},
        },
    ),
    (
        "deeply nested path parameters",
        {
            "endpoints": [
                {
                    "handler_name": "get_comment",
                    "path": "/users/{user_id:int}/posts/{post_id:int}/comments/{comment_id:int}",
                    "methods": ["GET"],
                    "tags": ["comments"],
                },
            ],
            "security_schemes": {},
            "servers": [],
            "tag_descriptions": {},
        },
    ),
    (
        "mixed security and public endpoints",
        {
            "endpoints": [
                {
                    "handler_name": "public_info",
                    "path": "/info",
                    "methods": ["GET"],
                    "tags": ["public"],
                },
                {
                    "handler_name": "private_data",
                    "path": "/private",
                    "methods": ["GET"],
                    "tags": ["private"],
                    "require_auth": True,
                },
            ],
            "security_schemes": {
                "bearerAuth": HTTPSecurityScheme(scheme="bearer"),
            },
            "servers": [],
            "tag_descriptions": {},
        },
    ),
    (
        "endpoint with all HTTP methods",
        {
            "endpoints": [
                {
                    "handler_name": "resource_handler",
                    "path": "/resources/{id:int}",
                    "methods": ["GET", "PUT", "PATCH", "DELETE"],
                    "tags": ["resources"],
                },
            ],
            "security_schemes": {},
            "servers": [],
            "tag_descriptions": {},
        },
    ),
]


# =============================================================================
# Property Test
# =============================================================================

def test_property_cache_consistency():
    """
        **Validates: Requirements 12.1, 12.2**

        Property 7: Cache Consistency

        For any cached specification, retrieving from cache SHALL return a
        specification equivalent to regenerating from the same endpoint
        registry state.

        This test exercises the property across diverse configurations
        including various endpoint combinations, security schemes, servers,
        tags, and path parameter types.  For each configuration it verifies
        that:

        1. The cached spec from CachedOpenAPIGenerator matches a freshly
           generated spec from a plain OpenAPI_Generator with the same
           registry state.
        2. Repeated calls to generate() on the cached generator return
           the same cached object.
        3. After refresh(), the regenerated spec is equivalent to a fresh
           generation from the same registry state.
    """
    total_cases = len(_CACHE_CONSISTENCY_CASES)
    total_checks = 0

    for case_entry in _CACHE_CONSISTENCY_CASES:
        case_desc = case_entry[0]
        config = case_entry[1]

        endpoints_config = config["endpoints"]
        security_schemes = config["security_schemes"]
        servers = config["servers"]
        tag_descriptions = config["tag_descriptions"]

        # Build descriptors for this case
        descriptors = []
        for ep_config in endpoints_config:
            handler_name = ep_config["handler_name"]
            path = ep_config["path"]
            methods = ep_config["methods"]
            tags = ep_config.get("tags", [])
            require_auth = ep_config.get("require_auth", False)
            scopes = ep_config.get("scopes", [])

            doc = _create_mock_doc(
                summary=f"Summary for {handler_name}",
                description=f"Description for {handler_name}",
            )

            constraints = None
            if require_auth:
                access_policy = _create_mock_access_policy(
                    require_auth=True,
                    scopes=scopes,
                )
                constraints = _create_mock_constraints(
                    access_policy=access_policy,
                )

            desc = _create_mock_descriptor(
                handler_name=handler_name,
                path=path,
                methods=methods,
                tags=tags,
                doc=doc,
                constraints=constraints,
            )
            descriptors.append(desc)

        registry = _create_mock_registry(descriptors)
        info = _create_default_info()

        # Build a plain generator for reference
        reference_generator = OpenAPIGenerator(
            registry=registry,
            info=info,
            servers=servers,
            security_schemes=security_schemes,
            tag_descriptions=tag_descriptions,
        )
        reference_spec = reference_generator.generate()

        # Build a cached generator with the same configuration
        cached_generator = CachedOpenAPIGenerator(
            registry=registry,
            info=info,
            servers=servers,
            security_schemes=security_schemes,
            tag_descriptions=tag_descriptions,
        )

        # -----------------------------------------------------------------
        # Check 1: First generate() matches reference
        # -----------------------------------------------------------------
        cached_spec = cached_generator.generate()

        if cached_spec != reference_spec:
            errmsg = (
                f"[{case_desc}] Cached generator first generate() does not "
                f"match reference generator output. "
                f"Cached keys: {sorted(cached_spec.keys())}, "
                f"Reference keys: {sorted(reference_spec.keys())}"
            )
            raise AssertionError(errmsg)

        total_checks += 1

        # -----------------------------------------------------------------
        # Check 2: Second generate() returns same cached object
        # -----------------------------------------------------------------
        cached_spec_2 = cached_generator.generate()

        if cached_spec is not cached_spec_2:
            errmsg = (
                f"[{case_desc}] Second generate() returned a different "
                f"object instead of the cached one"
            )
            raise AssertionError(errmsg)

        total_checks += 1

        # -----------------------------------------------------------------
        # Check 3: Cached spec still equals reference
        # -----------------------------------------------------------------
        if cached_spec_2 != reference_spec:
            errmsg = (
                f"[{case_desc}] Cached spec on second call does not match "
                f"reference spec"
            )
            raise AssertionError(errmsg)

        total_checks += 1

        # -----------------------------------------------------------------
        # Check 4: After refresh(), regenerated spec equals reference
        # -----------------------------------------------------------------
        cached_generator.refresh()
        refreshed_spec = cached_generator.generate()

        if refreshed_spec != reference_spec:
            errmsg = (
                f"[{case_desc}] Spec after refresh() does not match "
                f"reference spec"
            )
            raise AssertionError(errmsg)

        total_checks += 1

        # -----------------------------------------------------------------
        # Check 5: Refreshed spec is a new object (not the old cached one)
        # -----------------------------------------------------------------
        if refreshed_spec is cached_spec:
            errmsg = (
                f"[{case_desc}] Spec after refresh() is the same object "
                f"as the original cached spec"
            )
            raise AssertionError(errmsg)

        total_checks += 1

    # Verify we tested a meaningful number of cases
    if total_cases < 10:
        errmsg = f"Expected at least 10 test cases, got {total_cases}"
        raise AssertionError(errmsg)

    if total_checks < 50:
        errmsg = f"Expected at least 50 checks, got {total_checks}"
        raise AssertionError(errmsg)

    return
