"""
    Property test for specification validity in the OpenAPI generator.

    This module verifies Property 5: Specification Validity.

    For any generated OpenAPI specification, the output SHALL pass validation
    against the OpenAPI 3.0 structure without errors.

    **Validates: Requirements 9.1, 9.5**
"""

from typing import Any, Dict, List, Optional

from automojo.testbase.mocking import Mock

from automojo.webworks.openapi.configuration import OpenAPIInfo, ServerObject
from automojo.webworks.openapi.generator import OpenAPIGenerator
from automojo.webworks.openapi.securityschemes import (
    APIKeySecurityScheme,
    HTTPSecurityScheme,
    OAuth2SecurityScheme,
    OAuthFlow,
    OAuthFlows,
)
from automojo.webworks.openapi.validation import (
    OpenAPIValidator,
    SpecificationValidationError,
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
# Test Cases: Diverse specification configurations
# =============================================================================

# Each entry: (description, config)
# config keys: endpoints, security_schemes, servers, tags, tag_descriptions

_VALIDITY_TEST_CASES = [
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
                    "handler_name": "get_users",
                    "path": "/users",
                    "methods": ["GET"],
                    "tags": ["users"],
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
                    "handler_name": "list_items",
                    "path": "/items",
                    "methods": ["GET"],
                    "tags": ["items"],
                },
                {
                    "handler_name": "create_item",
                    "path": "/items",
                    "methods": ["POST"],
                    "tags": ["items"],
                },
                {
                    "handler_name": "get_item",
                    "path": "/items/{id:int}",
                    "methods": ["GET"],
                    "tags": ["items"],
                },
                {
                    "handler_name": "delete_item",
                    "path": "/items/{id:int}",
                    "methods": ["DELETE"],
                    "tags": ["items"],
                },
            ],
            "security_schemes": {},
            "servers": [],
            "tag_descriptions": {"items": "Item management"},
        },
    ),
    (
        "endpoints with HTTP bearer security",
        {
            "endpoints": [
                {
                    "handler_name": "get_profile",
                    "path": "/profile",
                    "methods": ["GET"],
                    "tags": ["profile"],
                    "require_auth": True,
                },
            ],
            "security_schemes": {
                "bearer_auth": HTTPSecurityScheme(
                    scheme="bearer", bearer_format="JWT"
                ),
            },
            "servers": [],
            "tag_descriptions": {},
        },
    ),
    (
        "endpoints with apiKey security",
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
                "api_key": APIKeySecurityScheme(
                    name="X-API-Key", in_="header"
                ),
            },
            "servers": [],
            "tag_descriptions": {},
        },
    ),
    (
        "endpoints with OAuth2 security and scopes",
        {
            "endpoints": [
                {
                    "handler_name": "admin_action",
                    "path": "/admin",
                    "methods": ["POST"],
                    "tags": ["admin"],
                    "require_auth": True,
                    "scopes": ["admin", "write"],
                },
            ],
            "security_schemes": {
                "oauth2": OAuth2SecurityScheme(
                    flows=OAuthFlows(
                        authorization_code=OAuthFlow(
                            scopes={
                                "admin": "Admin access",
                                "write": "Write access",
                            },
                            authorization_url="https://example.com/auth",
                            token_url="https://example.com/token",
                        )
                    )
                ),
            },
            "servers": [],
            "tag_descriptions": {},
        },
    ),
    (
        "multiple security schemes combined",
        {
            "endpoints": [
                {
                    "handler_name": "get_resource",
                    "path": "/resource",
                    "methods": ["GET"],
                    "tags": ["resources"],
                    "require_auth": True,
                    "scopes": ["read"],
                },
                {
                    "handler_name": "update_resource",
                    "path": "/resource/{id:int}",
                    "methods": ["PUT"],
                    "tags": ["resources"],
                    "require_auth": True,
                    "scopes": ["write"],
                },
            ],
            "security_schemes": {
                "bearer": HTTPSecurityScheme(scheme="bearer"),
                "oauth2": OAuth2SecurityScheme(
                    flows=OAuthFlows(
                        client_credentials=OAuthFlow(
                            scopes={"read": "Read", "write": "Write"},
                            token_url="https://example.com/token",
                        )
                    )
                ),
                "api_key": APIKeySecurityScheme(
                    name="X-Key", in_="header"
                ),
            },
            "servers": [],
            "tag_descriptions": {"resources": "Resource management"},
        },
    ),
    (
        "endpoints with servers configured",
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
        "multiple tags across endpoints",
        {
            "endpoints": [
                {
                    "handler_name": "get_users",
                    "path": "/users",
                    "methods": ["GET"],
                    "tags": ["users", "public"],
                },
                {
                    "handler_name": "get_orders",
                    "path": "/orders",
                    "methods": ["GET"],
                    "tags": ["orders"],
                },
                {
                    "handler_name": "get_products",
                    "path": "/products",
                    "methods": ["GET", "POST"],
                    "tags": ["products", "catalog"],
                },
            ],
            "security_schemes": {},
            "servers": [],
            "tag_descriptions": {
                "users": "User management",
                "orders": "Order processing",
                "products": "Product catalog",
            },
        },
    ),
    (
        "endpoints with path parameters of various types",
        {
            "endpoints": [
                {
                    "handler_name": "get_user",
                    "path": "/users/{user_id:int}",
                    "methods": ["GET"],
                    "tags": ["users"],
                },
                {
                    "handler_name": "get_post",
                    "path": "/users/{user_id:int}/posts/{slug:str}",
                    "methods": ["GET"],
                    "tags": ["posts"],
                },
            ],
            "security_schemes": {},
            "servers": [],
            "tag_descriptions": {},
        },
    ),
    (
        "mixed auth and public endpoints",
        {
            "endpoints": [
                {
                    "handler_name": "public_health",
                    "path": "/health",
                    "methods": ["GET"],
                    "tags": ["system"],
                },
                {
                    "handler_name": "protected_admin",
                    "path": "/admin/settings",
                    "methods": ["GET", "PUT"],
                    "tags": ["admin"],
                    "require_auth": True,
                },
                {
                    "handler_name": "public_docs",
                    "path": "/docs",
                    "methods": ["GET"],
                    "tags": ["system"],
                },
            ],
            "security_schemes": {
                "bearer": HTTPSecurityScheme(scheme="bearer"),
            },
            "servers": [
                ServerObject(url="https://api.example.com"),
            ],
            "tag_descriptions": {
                "system": "System endpoints",
                "admin": "Administration",
            },
        },
    ),
    (
        "endpoint with all HTTP methods",
        {
            "endpoints": [
                {
                    "handler_name": "handle_resource",
                    "path": "/resource/{id:int}",
                    "methods": ["GET", "POST", "PUT", "PATCH", "DELETE"],
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

def test_property_specification_validity():
    """
        **Validates: Requirements 9.1, 9.5**

        Property 5: Specification Validity

        For any generated OpenAPI specification, the output SHALL pass
        validation against the OpenAPI 3.0 structure without errors.

        This test exercises the property across diverse configurations
        including various endpoint combinations, security schemes, servers,
        tags, and path parameter types.
    """
    total_cases = len(_VALIDITY_TEST_CASES)
    total_checks = 0

    for case_entry in _VALIDITY_TEST_CASES:
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

        generator = OpenAPIGenerator(
            registry=registry,
            info=info,
            servers=servers,
            security_schemes=security_schemes,
            tag_descriptions=tag_descriptions,
        )

        spec = generator.generate()

        # -----------------------------------------------------------------
        # Property check 1: Spec must have required top-level fields
        # -----------------------------------------------------------------
        if "openapi" not in spec:
            errmsg = f"[{case_desc}] Generated spec missing 'openapi' field"
            raise AssertionError(errmsg)

        if "info" not in spec:
            errmsg = f"[{case_desc}] Generated spec missing 'info' field"
            raise AssertionError(errmsg)

        if "paths" not in spec:
            errmsg = f"[{case_desc}] Generated spec missing 'paths' field"
            raise AssertionError(errmsg)

        info_obj = spec["info"]
        if "title" not in info_obj:
            errmsg = f"[{case_desc}] Generated spec missing 'info.title'"
            raise AssertionError(errmsg)

        if "version" not in info_obj:
            errmsg = f"[{case_desc}] Generated spec missing 'info.version'"
            raise AssertionError(errmsg)

        total_checks += 1

        # -----------------------------------------------------------------
        # Property check 2: Spec must pass OpenAPIValidator without errors
        # -----------------------------------------------------------------
        validator = OpenAPIValidator(strict=False)
        try:
            issues = validator.validate(spec)
        except SpecificationValidationError as err:
            issue_details = []
            for issue in err.issues:
                detail = f"  {issue.severity}: {issue.path} - {issue.message}"
                issue_details.append(detail)
            details_str = "\n".join(issue_details)
            errmsg = (
                f"[{case_desc}] Generated spec failed validation with "
                f"{len(err.issues)} issue(s):\n{details_str}"
            )
            raise AssertionError(errmsg)

        total_checks += 1

        # -----------------------------------------------------------------
        # Property check 3: All $ref values must resolve
        # -----------------------------------------------------------------
        components = spec.get("components", {})
        defined_schemas = set(components.get("schemas", {}).keys())

        ref_values = _collect_all_refs(spec)
        for ref_path, ref_value in ref_values:
            if ref_value.startswith("#/components/schemas/"):
                schema_name = ref_value.replace("#/components/schemas/", "")
                if schema_name not in defined_schemas:
                    errmsg = (
                        f"[{case_desc}] $ref '{ref_value}' at '{ref_path}' "
                        f"references undefined schema. Defined: {defined_schemas}"
                    )
                    raise AssertionError(errmsg)

        total_checks += 1

        # -----------------------------------------------------------------
        # Property check 4: All security refs must resolve
        # -----------------------------------------------------------------
        defined_schemes = set(components.get("securitySchemes", {}).keys())
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
                                f"[{case_desc}] {method.upper()} {path_str} "
                                f"references undefined security scheme "
                                f"'{scheme_name}'. Defined: {defined_schemes}"
                            )
                            raise AssertionError(errmsg)

        total_checks += 1

    # Verify we tested a meaningful number of cases
    if total_cases < 10:
        errmsg = f"Expected at least 10 test cases, got {total_cases}"
        raise AssertionError(errmsg)

    if total_checks < 30:
        errmsg = f"Expected at least 30 checks, got {total_checks}"
        raise AssertionError(errmsg)

    return


def _collect_all_refs(obj, current_path=""):
    """
        Recursively collect all $ref values from a nested structure.

        :param obj: The current object being traversed.
        :param current_path: The JSON path to the current object.

        :returns: A list of (path, ref_value) tuples.
    """
    refs = []

    if isinstance(obj, dict):
        if "$ref" in obj:
            refs.append((current_path, obj["$ref"]))
        for key, value in obj.items():
            if key == "$ref":
                continue
            child_path = f"{current_path}.{key}" if current_path else key
            refs.extend(_collect_all_refs(value, child_path))
    elif isinstance(obj, list):
        for index, item in enumerate(obj):
            child_path = f"{current_path}[{index}]"
            refs.extend(_collect_all_refs(item, child_path))

    return refs
