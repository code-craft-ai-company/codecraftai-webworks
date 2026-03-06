"""
    Property test for security scheme consistency in the OpenAPI generator.

    This module verifies Property 4: Security Scheme Consistency.

    For any endpoint with an access_policy, the generated operation SHALL
    reference security schemes that exist in the components/securitySchemes
    section.

    **Validates: Requirements 4.1, 4.2, 4.3**
"""

from typing import Any, Dict, List, Optional

from automojo.testbase.mocking import Mock

from automojo.webworks.openapi.configuration import OpenAPIInfo
from automojo.webworks.openapi.generator import OpenAPIGenerator
from automojo.webworks.openapi.securityschemes import (
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
# Test Cases: Diverse security configurations
# =============================================================================

# Each entry: (description, security_schemes, endpoints)
# endpoints: list of (handler_name, path, methods, require_auth, scopes)

_SECURITY_TEST_CASES = [
    (
        "single HTTP bearer scheme with auth required",
        {"bearer_auth": HTTPSecurityScheme(scheme="bearer", bearer_format="JWT")},
        [
            ("get_users", "/users", ["GET"], True, []),
        ],
    ),
    (
        "single apiKey scheme with auth required",
        {"api_key": APIKeySecurityScheme(name="X-API-Key", in_="header")},
        [
            ("create_item", "/items", ["POST"], True, []),
        ],
    ),
    (
        "single OAuth2 scheme with scopes",
        {
            "oauth2": OAuth2SecurityScheme(
                flows=OAuthFlows(
                    authorization_code=OAuthFlow(
                        scopes={"read": "Read access", "write": "Write access"},
                        authorization_url="https://example.com/auth",
                        token_url="https://example.com/token",
                    )
                )
            ),
        },
        [
            ("update_user", "/users/{id:int}", ["PUT"], True, ["read", "write"]),
        ],
    ),
    (
        "multiple schemes: bearer + apiKey",
        {
            "bearer": HTTPSecurityScheme(scheme="bearer"),
            "api_key": APIKeySecurityScheme(name="Authorization", in_="header"),
        },
        [
            ("get_data", "/data", ["GET"], True, []),
            ("post_data", "/data", ["POST"], True, []),
        ],
    ),
    (
        "mixed schemes: OAuth2 + apiKey with scopes",
        {
            "oauth2": OAuth2SecurityScheme(
                flows=OAuthFlows(
                    client_credentials=OAuthFlow(
                        scopes={"admin": "Admin access"},
                        token_url="https://example.com/token",
                    )
                )
            ),
            "api_key": APIKeySecurityScheme(name="X-API-Key", in_="query"),
        },
        [
            ("admin_action", "/admin", ["POST"], True, ["admin"]),
        ],
    ),
    (
        "auth required endpoint alongside public endpoint",
        {"bearer": HTTPSecurityScheme(scheme="bearer")},
        [
            ("get_protected", "/protected", ["GET"], True, []),
            ("get_public", "/public", ["GET"], False, []),
        ],
    ),
    (
        "multiple endpoints with different scopes on OAuth2",
        {
            "oauth2": OAuth2SecurityScheme(
                flows=OAuthFlows(
                    authorization_code=OAuthFlow(
                        scopes={
                            "read": "Read",
                            "write": "Write",
                            "admin": "Admin",
                        },
                        authorization_url="https://example.com/auth",
                        token_url="https://example.com/token",
                    )
                )
            ),
        },
        [
            ("list_items", "/items", ["GET"], True, ["read"]),
            ("create_item", "/items", ["POST"], True, ["write"]),
            ("delete_item", "/items/{id:int}", ["DELETE"], True, ["admin"]),
        ],
    ),
    (
        "HTTP basic auth scheme",
        {"basic": HTTPSecurityScheme(scheme="basic")},
        [
            ("login", "/auth/login", ["POST"], True, []),
        ],
    ),
    (
        "apiKey in cookie",
        {"session": APIKeySecurityScheme(name="session_id", in_="cookie")},
        [
            ("get_profile", "/profile", ["GET"], True, []),
        ],
    ),
    (
        "three schemes: bearer + OAuth2 + apiKey",
        {
            "bearer": HTTPSecurityScheme(scheme="bearer", bearer_format="JWT"),
            "oauth2": OAuth2SecurityScheme(
                flows=OAuthFlows(
                    implicit=OAuthFlow(
                        scopes={"read": "Read"},
                        authorization_url="https://example.com/auth",
                    )
                )
            ),
            "api_key": APIKeySecurityScheme(name="X-Key", in_="header"),
        },
        [
            ("complex_endpoint", "/complex", ["GET", "POST", "PUT"], True, ["read"]),
        ],
    ),
    (
        "all endpoints public - no security references expected",
        {"bearer": HTTPSecurityScheme(scheme="bearer")},
        [
            ("health", "/health", ["GET"], False, []),
            ("status", "/status", ["GET"], False, []),
        ],
    ),
    (
        "OAuth2 with empty scopes",
        {
            "oauth2": OAuth2SecurityScheme(
                flows=OAuthFlows(
                    password=OAuthFlow(
                        scopes={},
                        token_url="https://example.com/token",
                    )
                )
            ),
        },
        [
            ("get_resource", "/resource", ["GET"], True, []),
        ],
    ),
]


# =============================================================================
# Property Test
# =============================================================================

def test_property_security_scheme_consistency():
    """
        **Validates: Requirements 4.1, 4.2, 4.3**

        Property 4: Security Scheme Consistency

        For any endpoint with an access_policy, the generated operation SHALL
        reference security schemes that exist in the components/securitySchemes
        section.

        This test exercises the property across diverse security configurations
        including apiKey, HTTP bearer, OAuth2 schemes, and combinations thereof.
    """
    total_cases = len(_SECURITY_TEST_CASES)
    total_checks = 0

    for case_entry in _SECURITY_TEST_CASES:
        case_desc = case_entry[0]
        security_schemes = case_entry[1]
        endpoints = case_entry[2]

        # Build descriptors for this case
        descriptors = []
        for ep in endpoints:
            ep_handler = ep[0]
            ep_path = ep[1]
            ep_methods = ep[2]
            ep_require_auth = ep[3]
            ep_scopes = ep[4]

            access_policy = _create_mock_access_policy(
                require_auth=ep_require_auth,
                scopes=ep_scopes,
            )
            constraints = _create_mock_constraints(access_policy=access_policy)
            desc = _create_mock_descriptor(
                handler_name=ep_handler,
                path=ep_path,
                methods=ep_methods,
                constraints=constraints,
            )
            descriptors.append(desc)

        registry = _create_mock_registry(descriptors)
        info = _create_default_info()
        generator = OpenAPIGenerator(
            registry=registry,
            info=info,
            security_schemes=security_schemes,
        )

        spec = generator.generate()
        components = spec.get("components", {})
        defined_schemes = set(components.get("securitySchemes", {}).keys())

        # -----------------------------------------------------------------
        # Check: All security schemes referenced in operations exist in
        # components/securitySchemes
        # -----------------------------------------------------------------
        paths = spec.get("paths", {})
        for path_str, path_item in paths.items():
            for method, operation in path_item.items():
                security_reqs = operation.get("security")
                if security_reqs is None:
                    continue

                for req_obj in security_reqs:
                    for scheme_name in req_obj:
                        if scheme_name not in defined_schemes:
                            errmsg = (
                                f"[{case_desc}] operation {method.upper()} "
                                f"{path_str} references security scheme "
                                f"'{scheme_name}' which is not defined in "
                                f"components/securitySchemes. Defined: "
                                f"{defined_schemes}"
                            )
                            raise AssertionError(errmsg)

                        total_checks += 1

        # -----------------------------------------------------------------
        # Check: All configured security schemes appear in components
        # -----------------------------------------------------------------
        for scheme_name in security_schemes:
            if scheme_name not in defined_schemes:
                errmsg = (
                    f"[{case_desc}] configured security scheme "
                    f"'{scheme_name}' not found in components/"
                    f"securitySchemes. Defined: {defined_schemes}"
                )
                raise AssertionError(errmsg)

    # Verify we tested a meaningful number of cases
    if total_cases < 10:
        errmsg = f"Expected at least 10 test cases, got {total_cases}"
        raise AssertionError(errmsg)

    if total_checks < 10:
        errmsg = f"Expected at least 10 security reference checks, got {total_checks}"
        raise AssertionError(errmsg)

    return
