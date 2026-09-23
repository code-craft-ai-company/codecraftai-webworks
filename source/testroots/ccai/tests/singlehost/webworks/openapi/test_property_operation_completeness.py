"""
    Property test for operation completeness in the OpenAPI generator.

    This module verifies Property 3: Operation Completeness.

    For any EndpointDescriptor with multiple HTTP methods, the generated
    OpenAPI specification SHALL contain a separate operation object for each
    method, all with correct operationId, summary, description, and tags.

    **Validates: Requirements 3.3, 3.4, 3.5, 3.6**
"""

from ccai.testbase.mocking import Mock

from ccai.webworks.openapi.configuration import OpenAPIInfo
from ccai.webworks.openapi.generator import (
    OpenAPIGenerator,
    strip_path_type_annotations,
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


def _create_mock_doc(summary=None, description=None, deprecated=False):
    """
        Create a mock Doc object with the given attributes.
    """
    mock_doc = Mock()
    mock_doc.configure(recursive=True)
    ctx = mock_doc.mock_context()
    ctx.set_attribute("summary", summary)
    ctx.set_attribute("description", description)
    ctx.set_attribute("deprecated", deprecated)
    ctx.set_attribute("external_docs", None)
    return mock_doc



def _create_mock_constraints():
    """
        Create a mock EndpointConstraints object with no access policy.
    """
    mock_constraints = Mock()
    mock_constraints.configure(recursive=True)
    ctx = mock_constraints.mock_context()
    ctx.set_attribute("access_policy", None)
    return mock_constraints


def _create_mock_descriptor(
    handler_name="test_handler",
    path="/test",
    methods=None,
    tags=None,
    doc=None,
    extras=None,
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
    ctx.set_attribute("constraints", _create_mock_constraints())
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
# Test Cases: Diverse method and doc configurations
# =============================================================================

# Each entry: (description, handler_name, path, methods, tags, doc_config)
# doc_config is None or a dict with summary, description, deprecated keys

_OPERATION_TEST_CASES = [
    (
        "single GET method with no doc",
        "list_items",
        "/items",
        ["GET"],
        [],
        None,
    ),
    (
        "single POST method with summary",
        "create_user",
        "/users",
        ["POST"],
        [],
        {"summary": "Create a new user", "description": None},
    ),
    (
        "GET and POST methods with summary and description",
        "manage_orders",
        "/orders",
        ["GET", "POST"],
        ["orders"],
        {"summary": "Manage orders", "description": "CRUD operations for orders"},
    ),
    (
        "GET PUT DELETE methods with tags",
        "handle_product",
        "/products/{id:int}",
        ["GET", "PUT", "DELETE"],
        ["products", "catalog"],
        {"summary": "Product operations", "description": None},
    ),
    (
        "all common methods",
        "resource_handler",
        "/resources",
        ["GET", "POST", "PUT", "PATCH", "DELETE"],
        ["resources"],
        {"summary": "Resource CRUD", "description": "Full resource management"},
    ),
    (
        "single DELETE with no tags and no doc",
        "remove_item",
        "/items/{id:int}",
        ["DELETE"],
        [],
        None,
    ),
    (
        "GET and PATCH with description only",
        "update_profile",
        "/profile",
        ["GET", "PATCH"],
        ["profile", "user"],
        {"summary": None, "description": "Profile management endpoint"},
    ),
    (
        "POST with multiple tags",
        "upload_file",
        "/files/upload",
        ["POST"],
        ["files", "uploads", "storage"],
        {"summary": "Upload a file", "description": "Handles file uploads"},
    ),
    (
        "GET POST PUT with deprecated doc",
        "legacy_endpoint",
        "/legacy/data",
        ["GET", "POST", "PUT"],
        ["legacy"],
        {"summary": "Legacy data", "description": "Deprecated endpoint", "deprecated": True},
    ),
    (
        "HEAD and OPTIONS methods",
        "check_resource",
        "/status",
        ["HEAD", "OPTIONS"],
        [],
        {"summary": "Check resource availability", "description": None},
    ),
    (
        "single GET with all doc fields",
        "get_dashboard",
        "/dashboard",
        ["GET"],
        ["admin", "dashboard"],
        {"summary": "Get dashboard", "description": "Returns the admin dashboard data"},
    ),
    (
        "GET and DELETE with empty tags",
        "manage_session",
        "/sessions/{session_id:uuid}",
        ["GET", "DELETE"],
        [],
        {"summary": "Session management", "description": None},
    ),
]


# =============================================================================
# Property Test
# =============================================================================

def test_property_operation_completeness():
    """
        **Validates: Requirements 3.3, 3.4, 3.5, 3.6**

        Property 3: Operation Completeness

        For any EndpointDescriptor with multiple HTTP methods, the generated
        OpenAPI specification SHALL contain a separate operation object for
        each method, all with correct operationId, summary, description,
        and tags.

        This test exercises the property across diverse method combinations
        and documentation configurations.
    """
    total_cases = len(_OPERATION_TEST_CASES)
    total_operation_checks = 0

    for case_entry in _OPERATION_TEST_CASES:
        case_desc = case_entry[0]
        handler_name = case_entry[1]
        path = case_entry[2]
        methods = case_entry[3]
        tags = case_entry[4]
        doc_config = case_entry[5]

        # Build the doc mock if doc_config is provided
        doc = None
        if doc_config is not None:
            deprecated = doc_config.get("deprecated", False)
            doc = _create_mock_doc(
                summary=doc_config.get("summary"),
                description=doc_config.get("description"),
                deprecated=deprecated,
            )

        descriptor = _create_mock_descriptor(
            handler_name=handler_name,
            path=path,
            methods=methods,
            tags=tags,
            doc=doc,
        )
        registry = _create_mock_registry([descriptor])
        info = _create_default_info()
        generator = OpenAPIGenerator(registry=registry, info=info)

        spec = generator.generate()
        paths = spec["paths"]

        # The path should exist in the spec with type annotations stripped
        expected_path = strip_path_type_annotations(path)

        if expected_path not in paths:
            errmsg = (
                f"[{case_desc}] expected path '{expected_path}' not found "
                f"in spec paths: {list(paths.keys())}"
            )
            raise AssertionError(errmsg)

        path_item = paths[expected_path]

        # -----------------------------------------------------------------
        # Check 1: Every method has a corresponding operation
        # -----------------------------------------------------------------
        for method in methods:
            method_lower = method.lower()

            if method_lower not in path_item:
                errmsg = (
                    f"[{case_desc}] method '{method_lower}' not found in "
                    f"path item. Available: {list(path_item.keys())}"
                )
                raise AssertionError(errmsg)

            operation = path_item[method_lower]

            # ---------------------------------------------------------
            # Check 2: operationId matches handler name (Req 3.4)
            # ---------------------------------------------------------
            op_id = operation.get("operationId")
            if op_id != handler_name:
                errmsg = (
                    f"[{case_desc}][{method_lower}] operationId is "
                    f"'{op_id}', expected '{handler_name}'"
                )
                raise AssertionError(errmsg)

            # ---------------------------------------------------------
            # Check 3: summary from doc attribute (Req 3.5)
            # ---------------------------------------------------------
            if doc_config is not None and doc_config.get("summary") is not None:
                expected_summary = doc_config["summary"]
                actual_summary = operation.get("summary")
                if actual_summary != expected_summary:
                    errmsg = (
                        f"[{case_desc}][{method_lower}] summary is "
                        f"'{actual_summary}', expected '{expected_summary}'"
                    )
                    raise AssertionError(errmsg)
            else:
                # When no doc or no summary, summary should be absent
                if "summary" in operation:
                    errmsg = (
                        f"[{case_desc}][{method_lower}] unexpected summary "
                        f"'{operation['summary']}' when no summary configured"
                    )
                    raise AssertionError(errmsg)

            # ---------------------------------------------------------
            # Check 4: description from doc attribute (Req 3.5)
            # ---------------------------------------------------------
            if doc_config is not None and doc_config.get("description") is not None:
                expected_desc = doc_config["description"]
                actual_desc = operation.get("description")
                if actual_desc != expected_desc:
                    errmsg = (
                        f"[{case_desc}][{method_lower}] description is "
                        f"'{actual_desc}', expected '{expected_desc}'"
                    )
                    raise AssertionError(errmsg)
            else:
                if "description" in operation:
                    errmsg = (
                        f"[{case_desc}][{method_lower}] unexpected description "
                        f"when no description configured"
                    )
                    raise AssertionError(errmsg)

            # ---------------------------------------------------------
            # Check 5: tags from endpoint tags (Req 3.6)
            # ---------------------------------------------------------
            if len(tags) > 0:
                actual_tags = operation.get("tags", [])
                if actual_tags != tags:
                    errmsg = (
                        f"[{case_desc}][{method_lower}] tags are "
                        f"{actual_tags}, expected {tags}"
                    )
                    raise AssertionError(errmsg)
            else:
                # When no tags, tags key should be absent or empty
                actual_tags = operation.get("tags")
                if actual_tags is not None and len(actual_tags) > 0:
                    errmsg = (
                        f"[{case_desc}][{method_lower}] unexpected tags "
                        f"{actual_tags} when no tags configured"
                    )
                    raise AssertionError(errmsg)

            # ---------------------------------------------------------
            # Check 6: deprecated flag when set (Req 3.5)
            # ---------------------------------------------------------
            if doc_config is not None and doc_config.get("deprecated", False):
                if operation.get("deprecated") is not True:
                    errmsg = (
                        f"[{case_desc}][{method_lower}] deprecated should "
                        f"be True but got {operation.get('deprecated')}"
                    )
                    raise AssertionError(errmsg)

            # ---------------------------------------------------------
            # Check 7: responses section exists (basic completeness)
            # ---------------------------------------------------------
            if "responses" not in operation:
                errmsg = (
                    f"[{case_desc}][{method_lower}] operation is missing "
                    f"'responses' section"
                )
                raise AssertionError(errmsg)

            total_operation_checks += 1

        # -----------------------------------------------------------------
        # Check 8: No extra methods beyond what was specified
        # -----------------------------------------------------------------
        expected_methods = set(m.lower() for m in methods)
        actual_methods = set(path_item.keys())
        extra_methods = actual_methods - expected_methods
        if len(extra_methods) > 0:
            errmsg = (
                f"[{case_desc}] path item has extra methods "
                f"{extra_methods} beyond expected {expected_methods}"
            )
            raise AssertionError(errmsg)

    # Verify we tested a meaningful number of cases and operations
    if total_cases < 10:
        errmsg = f"Expected at least 10 test cases, got {total_cases}"
        raise AssertionError(errmsg)

    if total_operation_checks < 20:
        errmsg = (
            f"Expected at least 20 operation checks, got "
            f"{total_operation_checks}"
        )
        raise AssertionError(errmsg)

    return
