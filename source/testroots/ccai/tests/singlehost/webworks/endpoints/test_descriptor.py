"""
    Tests for the EndpointDescriptor dataclass.
    
    This module contains unit tests for the endpoint descriptor dataclass.
"""

from ccai.webworks.endpoints.descriptor import EndpointDescriptor
from ccai.webworks.endpoints.constraints import EndpointConstraints
from ccai.webworks.endpoints.accesspolicy import AccessPolicy
from ccai.webworks.endpoints.ratelimit import RateLimit
from ccai.webworks.endpoints.doc import Doc


# =============================================================================
# Helper Functions for Testing
# =============================================================================

def sample_handler():
    """Sample handler function for testing."""
    return "response"


def another_handler():
    """Another sample handler function for testing."""
    return "another response"


# =============================================================================
# Unit Tests for EndpointDescriptor - Basic Construction
# =============================================================================

def test_endpoint_descriptor_minimal():
    """
        Test that EndpointDescriptor can be created with minimal values.
    """
    descriptor = EndpointDescriptor(
        handler=sample_handler,
        module="test_module"
    )
    
    if descriptor.handler is not sample_handler:
        errmsg = f"Expected handler to be sample_handler, got {descriptor.handler}"
        raise AssertionError(errmsg)
    
    if descriptor.module != "test_module":
        errmsg = f"Expected module 'test_module', got {descriptor.module}"
        raise AssertionError(errmsg)
    
    if descriptor.leaf is not None:
        errmsg = f"Expected leaf to be None, got {descriptor.leaf}"
        raise AssertionError(errmsg)
    
    if descriptor.path is not None:
        errmsg = f"Expected path to be None, got {descriptor.path}"
        raise AssertionError(errmsg)
    
    if descriptor.methods != ["GET"]:
        errmsg = f"Expected methods ['GET'], got {descriptor.methods}"
        raise AssertionError(errmsg)
    
    return


def test_endpoint_descriptor_with_all_fields():
    """
        Test that EndpointDescriptor can be created with all fields.
    """
    policy = AccessPolicy(roles=["admin"], scopes=["read"])
    limit = RateLimit(requests=100, window=60)
    constraints = EndpointConstraints(
        access_policy=policy,
        rate_limit=limit,
        scopes=["api:read"],
        roles=["admin"]
    )
    doc = Doc(summary="Test endpoint", description="A test endpoint")
    
    descriptor = EndpointDescriptor(
        handler=sample_handler,
        module="test_module",
        leaf="status",
        path="/api/v1/status",
        methods=["GET", "POST"],
        version="v1",
        tags=["api", "status"],
        constraints=constraints,
        doc=doc,
        extras={"rest": {"request_schema": {"type": "object"}}}
    )
    
    if descriptor.leaf != "status":
        errmsg = f"Expected leaf 'status', got {descriptor.leaf}"
        raise AssertionError(errmsg)
    
    if descriptor.path != "/api/v1/status":
        errmsg = f"Expected path '/api/v1/status', got {descriptor.path}"
        raise AssertionError(errmsg)
    
    if descriptor.methods != ["GET", "POST"]:
        errmsg = f"Expected methods ['GET', 'POST'], got {descriptor.methods}"
        raise AssertionError(errmsg)
    
    if descriptor.version != "v1":
        errmsg = f"Expected version 'v1', got {descriptor.version}"
        raise AssertionError(errmsg)
    
    if descriptor.tags != ["api", "status"]:
        errmsg = f"Expected tags ['api', 'status'], got {descriptor.tags}"
        raise AssertionError(errmsg)
    
    if descriptor.constraints is not constraints:
        errmsg = f"Expected constraints to be {constraints}, got {descriptor.constraints}"
        raise AssertionError(errmsg)
    
    if descriptor.doc is not doc:
        errmsg = f"Expected doc to be {doc}, got {descriptor.doc}"
        raise AssertionError(errmsg)
    
    if "rest" not in descriptor.extras:
        errmsg = f"Expected 'rest' in extras, got {descriptor.extras}"
        raise AssertionError(errmsg)
    
    return


def test_endpoint_descriptor_default_constraints():
    """
        Test that EndpointDescriptor has default empty constraints.
    """
    descriptor = EndpointDescriptor(
        handler=sample_handler,
        module="test_module"
    )
    
    if descriptor.constraints.access_policy is not None:
        errmsg = f"Expected access_policy to be None, got {descriptor.constraints.access_policy}"
        raise AssertionError(errmsg)
    
    if descriptor.constraints.rate_limit is not None:
        errmsg = f"Expected rate_limit to be None, got {descriptor.constraints.rate_limit}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for EndpointDescriptor - to_openapi_path method
# =============================================================================

def test_to_openapi_path_basic():
    """
        Test that to_openapi_path generates basic OpenAPI path item.
    """
    descriptor = EndpointDescriptor(
        handler=sample_handler,
        module="test_module",
        leaf="status",
        methods=["GET"]
    )
    
    path_item = descriptor.to_openapi_path()
    
    if "get" not in path_item:
        errmsg = f"Expected 'get' in path_item, got {path_item.keys()}"
        raise AssertionError(errmsg)
    
    if "operationId" not in path_item["get"]:
        errmsg = f"Expected 'operationId' in operation, got {path_item['get'].keys()}"
        raise AssertionError(errmsg)
    
    if "responses" not in path_item["get"]:
        errmsg = f"Expected 'responses' in operation, got {path_item['get'].keys()}"
        raise AssertionError(errmsg)
    
    return


def test_to_openapi_path_multiple_methods():
    """
        Test that to_openapi_path handles multiple HTTP methods.
    """
    descriptor = EndpointDescriptor(
        handler=sample_handler,
        module="test_module",
        leaf="resource",
        methods=["GET", "POST", "DELETE"]
    )
    
    path_item = descriptor.to_openapi_path()
    
    if "get" not in path_item:
        errmsg = f"Expected 'get' in path_item, got {path_item.keys()}"
        raise AssertionError(errmsg)
    
    if "post" not in path_item:
        errmsg = f"Expected 'post' in path_item, got {path_item.keys()}"
        raise AssertionError(errmsg)
    
    if "delete" not in path_item:
        errmsg = f"Expected 'delete' in path_item, got {path_item.keys()}"
        raise AssertionError(errmsg)
    
    return


def test_to_openapi_path_with_doc():
    """
        Test that to_openapi_path includes documentation fields.
    """
    doc = Doc(
        summary="Get status",
        description="Returns the current status",
        deprecated=True,
        external_docs="https://example.com/docs"
    )
    
    descriptor = EndpointDescriptor(
        handler=sample_handler,
        module="test_module",
        leaf="status",
        methods=["GET"],
        doc=doc
    )
    
    path_item = descriptor.to_openapi_path()
    operation = path_item["get"]
    
    if operation.get("summary") != "Get status":
        errmsg = f"Expected summary 'Get status', got {operation.get('summary')}"
        raise AssertionError(errmsg)
    
    if operation.get("description") != "Returns the current status":
        errmsg = f"Expected description 'Returns the current status', got {operation.get('description')}"
        raise AssertionError(errmsg)
    
    if operation.get("deprecated") is not True:
        errmsg = f"Expected deprecated True, got {operation.get('deprecated')}"
        raise AssertionError(errmsg)
    
    if "externalDocs" not in operation:
        errmsg = f"Expected 'externalDocs' in operation, got {operation.keys()}"
        raise AssertionError(errmsg)
    
    return


def test_to_openapi_path_with_tags():
    """
        Test that to_openapi_path includes tags.
    """
    descriptor = EndpointDescriptor(
        handler=sample_handler,
        module="test_module",
        leaf="status",
        methods=["GET"],
        tags=["api", "status"]
    )
    
    path_item = descriptor.to_openapi_path()
    operation = path_item["get"]
    
    if operation.get("tags") != ["api", "status"]:
        errmsg = f"Expected tags ['api', 'status'], got {operation.get('tags')}"
        raise AssertionError(errmsg)
    
    return


def test_to_openapi_path_with_security():
    """
        Test that to_openapi_path includes security requirements.
    """
    policy = AccessPolicy(roles=["admin"], scopes=["read", "write"], require_auth=True)
    constraints = EndpointConstraints(access_policy=policy)
    
    descriptor = EndpointDescriptor(
        handler=sample_handler,
        module="test_module",
        leaf="admin",
        methods=["GET"],
        constraints=constraints
    )
    
    path_item = descriptor.to_openapi_path()
    operation = path_item["get"]
    
    if "security" not in operation:
        errmsg = f"Expected 'security' in operation, got {operation.keys()}"
        raise AssertionError(errmsg)
    
    security = operation["security"]
    if len(security) == 0:
        errmsg = "Expected at least one security requirement"
        raise AssertionError(errmsg)
    
    return


def test_to_openapi_path_with_rest_extras():
    """
        Test that to_openapi_path includes REST-specific extras.
    """
    descriptor = EndpointDescriptor(
        handler=sample_handler,
        module="test_module",
        leaf="users",
        methods=["POST"],
        extras={
            "rest": {
                "request_schema": {"type": "object", "properties": {"name": {"type": "string"}}},
                "response_schema": {"type": "object", "properties": {"id": {"type": "integer"}}}
            }
        }
    )
    
    path_item = descriptor.to_openapi_path()
    operation = path_item["post"]
    
    if "requestBody" not in operation:
        errmsg = f"Expected 'requestBody' in operation, got {operation.keys()}"
        raise AssertionError(errmsg)
    
    if "content" not in operation["responses"]["200"]:
        errmsg = f"Expected 'content' in 200 response, got {operation['responses']['200'].keys()}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for EndpointDescriptor - to_security_row method
# =============================================================================

def test_to_security_row_basic():
    """
        Test that to_security_row generates basic security row.
    """
    descriptor = EndpointDescriptor(
        handler=sample_handler,
        module="test_module",
        leaf="status",
        methods=["GET"]
    )
    
    row = descriptor.to_security_row()
    
    if row["path"] != "/status":
        errmsg = f"Expected path '/status', got {row['path']}"
        raise AssertionError(errmsg)
    
    if row["methods"] != "GET":
        errmsg = f"Expected methods 'GET', got {row['methods']}"
        raise AssertionError(errmsg)
    
    if "sample_handler" not in row["handler"]:
        errmsg = f"Expected 'sample_handler' in handler, got {row['handler']}"
        raise AssertionError(errmsg)
    
    return


def test_to_security_row_with_path():
    """
        Test that to_security_row uses path when available.
    """
    descriptor = EndpointDescriptor(
        handler=sample_handler,
        module="test_module",
        path="/api/v1/status",
        methods=["GET"]
    )
    
    row = descriptor.to_security_row()
    
    if row["path"] != "/api/v1/status":
        errmsg = f"Expected path '/api/v1/status', got {row['path']}"
        raise AssertionError(errmsg)
    
    return


def test_to_security_row_with_access_policy():
    """
        Test that to_security_row includes access policy information.
    """
    policy = AccessPolicy(roles=["admin"], scopes=["read"], require_auth=True)
    constraints = EndpointConstraints(access_policy=policy)
    
    descriptor = EndpointDescriptor(
        handler=sample_handler,
        module="test_module",
        leaf="admin",
        methods=["GET"],
        constraints=constraints
    )
    
    row = descriptor.to_security_row()
    
    if "auth_required" not in row["access_policy"]:
        errmsg = f"Expected 'auth_required' in access_policy, got {row['access_policy']}"
        raise AssertionError(errmsg)
    
    if "admin" not in row["roles"]:
        errmsg = f"Expected 'admin' in roles, got {row['roles']}"
        raise AssertionError(errmsg)
    
    if "read" not in row["scopes"]:
        errmsg = f"Expected 'read' in scopes, got {row['scopes']}"
        raise AssertionError(errmsg)
    
    return


def test_to_security_row_with_rate_limit():
    """
        Test that to_security_row includes rate limit information.
    """
    limit = RateLimit(requests=100, window=60)
    constraints = EndpointConstraints(rate_limit=limit)
    
    descriptor = EndpointDescriptor(
        handler=sample_handler,
        module="test_module",
        leaf="api",
        methods=["GET"],
        constraints=constraints
    )
    
    row = descriptor.to_security_row()
    
    if row["rate_limit"] != "100/60s":
        errmsg = f"Expected rate_limit '100/60s', got {row['rate_limit']}"
        raise AssertionError(errmsg)
    
    return


def test_to_security_row_with_doc_summary():
    """
        Test that to_security_row includes doc summary.
    """
    doc = Doc(summary="Get status")
    
    descriptor = EndpointDescriptor(
        handler=sample_handler,
        module="test_module",
        leaf="status",
        methods=["GET"],
        doc=doc
    )
    
    row = descriptor.to_security_row()
    
    if row["summary"] != "Get status":
        errmsg = f"Expected summary 'Get status', got {row['summary']}"
        raise AssertionError(errmsg)
    
    return


def test_to_security_row_multiple_methods():
    """
        Test that to_security_row formats multiple methods.
    """
    descriptor = EndpointDescriptor(
        handler=sample_handler,
        module="test_module",
        leaf="resource",
        methods=["GET", "POST", "DELETE"]
    )
    
    row = descriptor.to_security_row()
    
    if row["methods"] != "GET,POST,DELETE":
        errmsg = f"Expected methods 'GET,POST,DELETE', got {row['methods']}"
        raise AssertionError(errmsg)
    
    return


def test_to_security_row_no_constraints():
    """
        Test that to_security_row handles no constraints.
    """
    descriptor = EndpointDescriptor(
        handler=sample_handler,
        module="test_module",
        leaf="public",
        methods=["GET"]
    )
    
    row = descriptor.to_security_row()
    
    if row["access_policy"] != "none":
        errmsg = f"Expected access_policy 'none', got {row['access_policy']}"
        raise AssertionError(errmsg)
    
    if row["rate_limit"] != "none":
        errmsg = f"Expected rate_limit 'none', got {row['rate_limit']}"
        raise AssertionError(errmsg)
    
    return
