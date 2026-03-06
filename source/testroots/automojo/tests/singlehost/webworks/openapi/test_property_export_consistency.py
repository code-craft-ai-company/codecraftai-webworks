"""
    Property test for export format consistency in the OpenAPI generator.

    This module verifies Property 6: Export Format Consistency.

    For any OpenAPI specification, exporting to JSON and then parsing SHALL
    produce an equivalent dictionary to the original specification.

    **Validates: Requirements 10.1, 10.2, 10.6**
"""

import json
import os
import tempfile

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

_EXPORT_CONSISTENCY_CASES = [
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
        "endpoint with security schemes",
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
        "oauth2 security scheme",
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
        "mixed security and no-security endpoints",
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

def test_property_export_format_consistency():
    """
        **Validates: Requirements 10.1, 10.2, 10.6**

        Property 6: Export Format Consistency

        For any OpenAPI specification, exporting to JSON and then parsing
        SHALL produce an equivalent dictionary to the original specification.

        This test exercises the property across diverse configurations
        including various endpoint combinations, security schemes, servers,
        tags, and path parameter types. It also verifies that file-based
        export produces identical results and that output is deterministic.
    """
    total_cases = len(_EXPORT_CONSISTENCY_CASES)
    total_checks = 0

    for case_entry in _EXPORT_CONSISTENCY_CASES:
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
        # Property check 1: JSON round-trip produces equivalent dict
        # -----------------------------------------------------------------
        json_str = generator.generate_json()
        parsed_json = json.loads(json_str)

        if parsed_json != spec:
            errmsg = (
                f"[{case_desc}] JSON round-trip mismatch. "
                f"Original keys: {sorted(spec.keys())}, "
                f"Parsed keys: {sorted(parsed_json.keys())}"
            )
            raise AssertionError(errmsg)

        total_checks += 1

        # -----------------------------------------------------------------
        # Property check 2: JSON output is deterministic (sorted keys)
        # -----------------------------------------------------------------
        json_str_2 = generator.generate_json()

        if json_str != json_str_2:
            errmsg = (
                f"[{case_desc}] JSON output is not deterministic across calls"
            )
            raise AssertionError(errmsg)

        total_checks += 1

        # -----------------------------------------------------------------
        # Property check 3: File export produces same content as generate_json
        # -----------------------------------------------------------------
        temp_dir = tempfile.mkdtemp()
        json_file_path = os.path.join(temp_dir, "spec.json")

        try:
            generator.export(json_file_path)

            with open(json_file_path, "r", encoding="utf-8") as fh:
                file_content = fh.read()

            if file_content != json_str:
                errmsg = (
                    f"[{case_desc}] File export content does not match "
                    f"generate_json() output"
                )
                raise AssertionError(errmsg)

            total_checks += 1

            # Parse the file content and verify equivalence
            parsed_file = json.loads(file_content)

            if parsed_file != spec:
                errmsg = (
                    f"[{case_desc}] Parsed file content does not match "
                    f"original spec dict"
                )
                raise AssertionError(errmsg)

            total_checks += 1

        finally:
            if os.path.exists(json_file_path):
                os.remove(json_file_path)
            os.rmdir(temp_dir)

        # -----------------------------------------------------------------
        # Property check 4: YAML round-trip (if PyYAML available)
        # -----------------------------------------------------------------
        try:
            import yaml

            yaml_str = generator.generate_yaml()
            parsed_yaml = yaml.safe_load(yaml_str)

            if parsed_yaml != spec:
                errmsg = (
                    f"[{case_desc}] YAML round-trip mismatch. "
                    f"Original keys: {sorted(spec.keys())}, "
                    f"Parsed keys: {sorted(parsed_yaml.keys())}"
                )
                raise AssertionError(errmsg)

            total_checks += 1

            # YAML determinism check
            yaml_str_2 = generator.generate_yaml()

            if yaml_str != yaml_str_2:
                errmsg = (
                    f"[{case_desc}] YAML output is not deterministic"
                )
                raise AssertionError(errmsg)

            total_checks += 1

            # YAML file export check
            yaml_file_path = os.path.join(temp_dir, "spec.yaml")
            os.makedirs(temp_dir, exist_ok=True)

            try:
                generator.export(yaml_file_path)

                with open(yaml_file_path, "r", encoding="utf-8") as fh:
                    yaml_file_content = fh.read()

                parsed_yaml_file = yaml.safe_load(yaml_file_content)

                if parsed_yaml_file != spec:
                    errmsg = (
                        f"[{case_desc}] YAML file export round-trip mismatch"
                    )
                    raise AssertionError(errmsg)

                total_checks += 1

            finally:
                if os.path.exists(yaml_file_path):
                    os.remove(yaml_file_path)
                if os.path.exists(temp_dir):
                    os.rmdir(temp_dir)

        except ImportError:
            # PyYAML not available, skip YAML checks
            pass

    # Verify we tested a meaningful number of cases
    if total_cases < 10:
        errmsg = f"Expected at least 10 test cases, got {total_cases}"
        raise AssertionError(errmsg)

    if total_checks < 30:
        errmsg = f"Expected at least 30 checks, got {total_checks}"
        raise AssertionError(errmsg)

    return
