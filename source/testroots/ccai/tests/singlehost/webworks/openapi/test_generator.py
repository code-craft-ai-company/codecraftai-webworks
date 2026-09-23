"""
    Tests for the OpenAPI_Generator class in the OpenAPI generator module.

    This module contains unit tests covering the generator skeleton initialization,
    path building from endpoint descriptors, path parameter extraction, operation
    building, query parameter handling, request body building, and response building.
"""

from dataclasses import dataclass

from ccai.testbase.mocking import Mock

from ccai.webworks.openapi.configuration import OpenAPIInfo, ServerObject
from ccai.webworks.openapi.generator import (
    OpenAPIGenerator,
    extract_path_parameters,
    strip_path_type_annotations,
)
from ccai.webworks.openapi.securityschemes import (
    APIKeySecurityScheme,
    HTTPSecurityScheme,
    OAuth2SecurityScheme,
    OAuthFlow,
    OAuthFlows,
)


# =============================================================================
# Test Dataclasses for Schema Conversion
# =============================================================================

@dataclass
class UserCreate:
    """
        A simple dataclass for testing request body schema conversion.
    """
    name: str
    email: str


@dataclass
class UserResponse:
    """
        A simple dataclass for testing response schema conversion.
    """
    id: int
    name: str
    email: str


@dataclass
class ValidationError:
    """
        A custom error dataclass for testing error_map schema conversion.
    """
    code: str
    message: str
    field: str


# =============================================================================
# Helper Functions
# =============================================================================

def _create_mock_doc(summary=None, description=None, deprecated=False, external_docs=None):
    """
        Create a mock Doc object with the given attributes.
    """
    mock_doc = Mock()
    mock_doc.configure(recursive=True)
    ctx = mock_doc.mock_context()
    ctx.set_attribute("summary", summary)
    ctx.set_attribute("description", description)
    ctx.set_attribute("deprecated", deprecated)
    ctx.set_attribute("external_docs", external_docs)
    return mock_doc


def _create_mock_constraints(access_policy=None):
    """
        Create a mock EndpointConstraints object.
    """
    mock_constraints = Mock()
    mock_constraints.configure(recursive=True)
    ctx = mock_constraints.mock_context()
    ctx.set_attribute("access_policy", access_policy)
    ctx.set_attribute("rate_limit", None)
    ctx.set_attribute("scopes", [])
    ctx.set_attribute("roles", [])
    return mock_constraints


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


class _HandlerStub:
    """
        A simple stub that provides a __name__ attribute for mock handlers.
    """

    def __init__(self, name):
        self.__name__ = name

    def __call__(self):
        pass


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

        By default the descriptor is marked as a REST endpoint
        (``endpoint_type="rest"`` in extras) so the OpenAPI generator
        includes it when ``rest_only=True``.
    """
    mock = Mock()
    mock.configure(recursive=True)
    ctx = mock.mock_context()

    handler = _HandlerStub(handler_name)

    # Ensure endpoint_type is set to "rest" by default so the generator
    # includes the descriptor when rest_only=True.
    resolved_extras = extras or {}
    if "endpoint_type" not in resolved_extras:
        resolved_extras = dict(resolved_extras)
        resolved_extras["endpoint_type"] = "rest"

    ctx.set_attribute("handler", handler)
    ctx.set_attribute("module", "test_module")
    ctx.set_attribute("path", path)
    ctx.set_attribute("leaf", None)
    ctx.set_attribute("methods", methods or ["GET"])
    ctx.set_attribute("tags", tags or [])
    ctx.set_attribute("doc", doc)
    ctx.set_attribute("extras", resolved_extras)
    ctx.set_attribute("constraints", constraints or _create_mock_constraints())
    ctx.set_attribute("version", None)

    return mock


def _create_mock_registry(descriptors=None):
    """
        Create a mock EndpointRegistry that returns the given descriptors.
    """
    mock_registry = Mock()
    mock_registry.configure(recursive=True)
    mock_registry.mock_context().mock_method("collect", return_value=descriptors or [])
    return mock_registry


def _create_default_info():
    """
        Create a default OpenAPIInfo for testing.
    """
    return OpenAPIInfo(title="Test API", version="1.0.0")


# =============================================================================
# Task 4.1: OpenAPI_Generator Class Skeleton Tests
# =============================================================================

def test_generator_initializes_with_required_params():
    """
        Test that the generator initializes with registry and info.
    """
    registry = _create_mock_registry()
    info = _create_default_info()

    generator = OpenAPIGenerator(registry=registry, info=info)

    if generator.registry is not registry:
        errmsg = "Expected registry to be stored on the generator"
        raise AssertionError(errmsg)

    if generator.info is not info:
        errmsg = "Expected info to be stored on the generator"
        raise AssertionError(errmsg)

    return


def test_generator_initializes_with_optional_params():
    """
        Test that the generator accepts optional servers and security_schemes.
    """
    registry = _create_mock_registry()
    info = _create_default_info()
    servers = [ServerObject(url="https://api.example.com")]
    security_schemes = {"bearer": HTTPSecurityScheme()}

    generator = OpenAPIGenerator(
        registry=registry,
        info=info,
        servers=servers,
        security_schemes=security_schemes,
    )

    if len(generator.servers) != 1:
        errmsg = f"Expected 1 server, got {len(generator.servers)}"
        raise AssertionError(errmsg)

    if "bearer" not in generator.security_schemes:
        errmsg = "Expected 'bearer' in security_schemes"
        raise AssertionError(errmsg)

    return


def test_generator_has_schema_converter():
    """
        Test that the generator creates a Schema_Converter instance.
    """
    registry = _create_mock_registry()
    info = _create_default_info()

    generator = OpenAPIGenerator(registry=registry, info=info)

    if generator._schema_converter is None:
        errmsg = "Expected _schema_converter to be initialized"
        raise AssertionError(errmsg)

    return


def test_generator_defaults_empty_lists():
    """
        Test that optional list/dict params default to empty.
    """
    registry = _create_mock_registry()
    info = _create_default_info()

    generator = OpenAPIGenerator(registry=registry, info=info)

    if len(generator.servers) != 0:
        errmsg = f"Expected empty servers, got {generator.servers}"
        raise AssertionError(errmsg)

    if len(generator.security_schemes) != 0:
        errmsg = f"Expected empty security_schemes, got {generator.security_schemes}"
        raise AssertionError(errmsg)

    if len(generator.tag_descriptions) != 0:
        errmsg = f"Expected empty tag_descriptions, got {generator.tag_descriptions}"
        raise AssertionError(errmsg)

    return


def test_generate_returns_openapi_version():
    """
        Test that generate() produces a spec with openapi version 3.0.3.
    """
    registry = _create_mock_registry()
    info = _create_default_info()
    generator = OpenAPIGenerator(registry=registry, info=info)

    spec = generator.generate()

    if spec.get("openapi") != "3.0.3":
        errmsg = f"Expected openapi '3.0.3', got {spec.get('openapi')!r}"
        raise AssertionError(errmsg)

    return


def test_generate_includes_info():
    """
        Test that generate() includes the info object.
    """
    registry = _create_mock_registry()
    info = OpenAPIInfo(title="My API", version="2.0.0", description="A test API")
    generator = OpenAPIGenerator(registry=registry, info=info)

    spec = generator.generate()

    if spec["info"]["title"] != "My API":
        errmsg = f"Expected title 'My API', got {spec['info']['title']!r}"
        raise AssertionError(errmsg)

    if spec["info"]["version"] != "2.0.0":
        errmsg = f"Expected version '2.0.0', got {spec['info']['version']!r}"
        raise AssertionError(errmsg)

    return


def test_generate_includes_servers():
    """
        Test that generate() includes servers when provided.
    """
    registry = _create_mock_registry()
    info = _create_default_info()
    servers = [ServerObject(url="https://api.example.com", description="Production")]
    generator = OpenAPIGenerator(registry=registry, info=info, servers=servers)

    spec = generator.generate()

    if "servers" not in spec:
        errmsg = "Expected 'servers' in spec"
        raise AssertionError(errmsg)

    if len(spec["servers"]) != 1:
        errmsg = f"Expected 1 server, got {len(spec['servers'])}"
        raise AssertionError(errmsg)

    if spec["servers"][0]["url"] != "https://api.example.com":
        errmsg = f"Expected server url, got {spec['servers'][0]['url']!r}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Task 4.2: Path Building Tests
# =============================================================================

def test_strip_path_type_annotations_simple():
    """
        Test stripping type annotations from a simple path.
    """
    result = strip_path_type_annotations("/users/{id:int}")

    if result != "/users/{id}":
        errmsg = f"Expected '/users/{{id}}', got {result!r}"
        raise AssertionError(errmsg)

    return


def test_strip_path_type_annotations_multiple():
    """
        Test stripping type annotations from a path with multiple params.
    """
    result = strip_path_type_annotations("/users/{user_id:int}/posts/{post_id:int}")

    expected = "/users/{user_id}/posts/{post_id}"
    if result != expected:
        errmsg = f"Expected {expected!r}, got {result!r}"
        raise AssertionError(errmsg)

    return


def test_strip_path_type_annotations_no_type():
    """
        Test that paths without type annotations are unchanged.
    """
    result = strip_path_type_annotations("/users/{id}")

    if result != "/users/{id}":
        errmsg = f"Expected '/users/{{id}}', got {result!r}"
        raise AssertionError(errmsg)

    return


def test_strip_path_type_annotations_no_params():
    """
        Test that paths without parameters are unchanged.
    """
    result = strip_path_type_annotations("/users")

    if result != "/users":
        errmsg = f"Expected '/users', got {result!r}"
        raise AssertionError(errmsg)

    return


def test_extract_path_parameters_int():
    """
        Test extracting an integer path parameter.
    """
    params = extract_path_parameters("/users/{id:int}")

    if len(params) != 1:
        errmsg = f"Expected 1 parameter, got {len(params)}"
        raise AssertionError(errmsg)

    param = params[0]
    if param["name"] != "id":
        errmsg = f"Expected name 'id', got {param['name']!r}"
        raise AssertionError(errmsg)

    if param["in"] != "path":
        errmsg = f"Expected in 'path', got {param['in']!r}"
        raise AssertionError(errmsg)

    if param["required"] is not True:
        errmsg = f"Expected required True, got {param['required']!r}"
        raise AssertionError(errmsg)

    if param["schema"]["type"] != "integer":
        errmsg = f"Expected schema type 'integer', got {param['schema']['type']!r}"
        raise AssertionError(errmsg)

    return


def test_extract_path_parameters_str():
    """
        Test extracting a string path parameter.
    """
    params = extract_path_parameters("/items/{slug:str}")

    if len(params) != 1:
        errmsg = f"Expected 1 parameter, got {len(params)}"
        raise AssertionError(errmsg)

    if params[0]["schema"]["type"] != "string":
        errmsg = f"Expected schema type 'string', got {params[0]['schema']['type']!r}"
        raise AssertionError(errmsg)

    return


def test_extract_path_parameters_no_type_defaults_string():
    """
        Test that a path parameter without type annotation defaults to string.
    """
    params = extract_path_parameters("/items/{id}")

    if len(params) != 1:
        errmsg = f"Expected 1 parameter, got {len(params)}"
        raise AssertionError(errmsg)

    if params[0]["schema"]["type"] != "string":
        errmsg = f"Expected schema type 'string', got {params[0]['schema']['type']!r}"
        raise AssertionError(errmsg)

    return


def test_extract_path_parameters_multiple():
    """
        Test extracting multiple path parameters.
    """
    params = extract_path_parameters("/users/{user_id:int}/posts/{post_id:int}")

    if len(params) != 2:
        errmsg = f"Expected 2 parameters, got {len(params)}"
        raise AssertionError(errmsg)

    names = [p["name"] for p in params]
    if "user_id" not in names:
        errmsg = f"Expected 'user_id' in parameter names, got {names}"
        raise AssertionError(errmsg)

    if "post_id" not in names:
        errmsg = f"Expected 'post_id' in parameter names, got {names}"
        raise AssertionError(errmsg)

    return


def test_extract_path_parameters_empty():
    """
        Test extracting parameters from a path with no parameters.
    """
    params = extract_path_parameters("/users")

    if len(params) != 0:
        errmsg = f"Expected 0 parameters, got {len(params)}"
        raise AssertionError(errmsg)

    return


def test_build_paths_groups_by_path():
    """
        Test that _build_paths groups operations by OpenAPI path.
    """
    desc = _create_mock_descriptor(
        handler_name="get_user",
        path="/users/{id:int}",
        methods=["GET"],
    )
    registry = _create_mock_registry(descriptors=[desc])
    info = _create_default_info()
    generator = OpenAPIGenerator(registry=registry, info=info)

    spec = generator.generate()
    paths = spec["paths"]

    if "/users/{id}" not in paths:
        errmsg = f"Expected '/users/{{id}}' in paths, got {list(paths.keys())}"
        raise AssertionError(errmsg)

    if "get" not in paths["/users/{id}"]:
        errmsg = f"Expected 'get' in path item, got {list(paths['/users/{id}'].keys())}"
        raise AssertionError(errmsg)

    return


def test_build_paths_multiple_methods():
    """
        Test that _build_paths creates operations for each HTTP method.
    """
    desc = _create_mock_descriptor(
        handler_name="manage_user",
        path="/users/{id:int}",
        methods=["GET", "PUT", "DELETE"],
    )
    registry = _create_mock_registry(descriptors=[desc])
    info = _create_default_info()
    generator = OpenAPIGenerator(registry=registry, info=info)

    spec = generator.generate()
    path_item = spec["paths"]["/users/{id}"]

    for method in ["get", "put", "delete"]:
        if method not in path_item:
            errmsg = f"Expected '{method}' in path item, got {list(path_item.keys())}"
            raise AssertionError(errmsg)

    return


def test_build_paths_uses_leaf_when_no_path():
    """
        Test that _build_paths falls back to leaf when path is None.
    """
    desc = _create_mock_descriptor(handler_name="get_status", path=None)
    desc.mock_context().set_attribute("leaf", "status")

    registry = _create_mock_registry(descriptors=[desc])
    info = _create_default_info()
    generator = OpenAPIGenerator(registry=registry, info=info)

    spec = generator.generate()
    paths = spec["paths"]

    if "/status" not in paths:
        errmsg = f"Expected '/status' in paths, got {list(paths.keys())}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Task 4.4: Operation Building Tests
# =============================================================================

def test_operation_id_from_handler_name():
    """
        Test that operationId is derived from the handler function name.
    """
    desc = _create_mock_descriptor(handler_name="list_users", path="/users")
    registry = _create_mock_registry(descriptors=[desc])
    info = _create_default_info()
    generator = OpenAPIGenerator(registry=registry, info=info)

    spec = generator.generate()
    operation = spec["paths"]["/users"]["get"]

    if operation["operationId"] != "list_users":
        errmsg = f"Expected operationId 'list_users', got {operation['operationId']!r}"
        raise AssertionError(errmsg)

    return


def test_operation_includes_summary_from_doc():
    """
        Test that the operation includes summary from the doc attribute.
    """
    doc = _create_mock_doc(summary="List all users")
    desc = _create_mock_descriptor(handler_name="list_users", path="/users", doc=doc)
    registry = _create_mock_registry(descriptors=[desc])
    info = _create_default_info()
    generator = OpenAPIGenerator(registry=registry, info=info)

    spec = generator.generate()
    operation = spec["paths"]["/users"]["get"]

    if operation.get("summary") != "List all users":
        errmsg = f"Expected summary 'List all users', got {operation.get('summary')!r}"
        raise AssertionError(errmsg)

    return


def test_operation_includes_description_from_doc():
    """
        Test that the operation includes description from the doc attribute.
    """
    doc = _create_mock_doc(description="Returns a paginated list of users")
    desc = _create_mock_descriptor(handler_name="list_users", path="/users", doc=doc)
    registry = _create_mock_registry(descriptors=[desc])
    info = _create_default_info()
    generator = OpenAPIGenerator(registry=registry, info=info)

    spec = generator.generate()
    operation = spec["paths"]["/users"]["get"]

    if operation.get("description") != "Returns a paginated list of users":
        errmsg = f"Expected description, got {operation.get('description')!r}"
        raise AssertionError(errmsg)

    return


def test_operation_includes_deprecated_from_doc():
    """
        Test that the operation includes deprecated flag from the doc attribute.
    """
    doc = _create_mock_doc(deprecated=True)
    desc = _create_mock_descriptor(handler_name="old_endpoint", path="/old", doc=doc)
    registry = _create_mock_registry(descriptors=[desc])
    info = _create_default_info()
    generator = OpenAPIGenerator(registry=registry, info=info)

    spec = generator.generate()
    operation = spec["paths"]["/old"]["get"]

    if operation.get("deprecated") is not True:
        errmsg = f"Expected deprecated True, got {operation.get('deprecated')!r}"
        raise AssertionError(errmsg)

    return


def test_operation_includes_tags():
    """
        Test that the operation includes tags from the endpoint.
    """
    desc = _create_mock_descriptor(
        handler_name="list_users",
        path="/users",
        tags=["users", "admin"],
    )
    registry = _create_mock_registry(descriptors=[desc])
    info = _create_default_info()
    generator = OpenAPIGenerator(registry=registry, info=info)

    spec = generator.generate()
    operation = spec["paths"]["/users"]["get"]

    if "tags" not in operation:
        errmsg = "Expected 'tags' in operation"
        raise AssertionError(errmsg)

    if "users" not in operation["tags"]:
        errmsg = f"Expected 'users' in tags, got {operation['tags']}"
        raise AssertionError(errmsg)

    if "admin" not in operation["tags"]:
        errmsg = f"Expected 'admin' in tags, got {operation['tags']}"
        raise AssertionError(errmsg)

    return


def test_operation_no_doc_omits_summary():
    """
        Test that when doc is None, summary and description are omitted.
    """
    desc = _create_mock_descriptor(handler_name="list_users", path="/users", doc=None)
    registry = _create_mock_registry(descriptors=[desc])
    info = _create_default_info()
    generator = OpenAPIGenerator(registry=registry, info=info)

    spec = generator.generate()
    operation = spec["paths"]["/users"]["get"]

    if "summary" in operation:
        errmsg = f"Expected no 'summary' when doc is None, got {operation['summary']!r}"
        raise AssertionError(errmsg)

    if "description" in operation:
        errmsg = f"Expected no 'description' when doc is None, got {operation['description']!r}"
        raise AssertionError(errmsg)

    return


def test_operation_empty_tags_omits_tags():
    """
        Test that when tags is empty, the tags field is omitted.
    """
    desc = _create_mock_descriptor(handler_name="list_users", path="/users", tags=[])
    registry = _create_mock_registry(descriptors=[desc])
    info = _create_default_info()
    generator = OpenAPIGenerator(registry=registry, info=info)

    spec = generator.generate()
    operation = spec["paths"]["/users"]["get"]

    if "tags" in operation:
        errmsg = f"Expected no 'tags' when tags is empty, got {operation['tags']}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Task 4.5: Query Parameter Handling Tests
# =============================================================================

def test_query_parameters_from_extras():
    """
        Test that query parameters are extracted from extras["rest"]["query_params"].
    """
    extras = {
        "rest": {
            "query_params": {
                "page": int,
                "limit": int,
                "search": str,
            },
        },
    }
    desc = _create_mock_descriptor(
        handler_name="list_users",
        path="/users",
        extras=extras,
    )
    registry = _create_mock_registry(descriptors=[desc])
    info = _create_default_info()
    generator = OpenAPIGenerator(registry=registry, info=info)

    spec = generator.generate()
    operation = spec["paths"]["/users"]["get"]
    params = operation.get("parameters", [])

    query_params = [p for p in params if p["in"] == "query"]

    if len(query_params) != 3:
        errmsg = f"Expected 3 query parameters, got {len(query_params)}"
        raise AssertionError(errmsg)

    param_names = [p["name"] for p in query_params]
    for expected_name in ["page", "limit", "search"]:
        if expected_name not in param_names:
            errmsg = f"Expected '{expected_name}' in query param names, got {param_names}"
            raise AssertionError(errmsg)

    return


def test_query_parameter_types():
    """
        Test that query parameter types are correctly converted.
    """
    extras = {
        "rest": {
            "query_params": {
                "page": int,
                "active": bool,
            },
        },
    }
    desc = _create_mock_descriptor(
        handler_name="list_users",
        path="/users",
        extras=extras,
    )
    registry = _create_mock_registry(descriptors=[desc])
    info = _create_default_info()
    generator = OpenAPIGenerator(registry=registry, info=info)

    spec = generator.generate()
    operation = spec["paths"]["/users"]["get"]
    params = operation.get("parameters", [])

    query_params = {p["name"]: p for p in params if p["in"] == "query"}

    if query_params["page"]["schema"]["type"] != "integer":
        errmsg = f"Expected 'page' schema type 'integer', got {query_params['page']['schema']}"
        raise AssertionError(errmsg)

    if query_params["active"]["schema"]["type"] != "boolean":
        errmsg = f"Expected 'active' schema type 'boolean', got {query_params['active']['schema']}"
        raise AssertionError(errmsg)

    return


def test_query_parameters_not_required():
    """
        Test that query parameters are marked as not required.
    """
    extras = {
        "rest": {
            "query_params": {"page": int},
        },
    }
    desc = _create_mock_descriptor(
        handler_name="list_users",
        path="/users",
        extras=extras,
    )
    registry = _create_mock_registry(descriptors=[desc])
    info = _create_default_info()
    generator = OpenAPIGenerator(registry=registry, info=info)

    spec = generator.generate()
    operation = spec["paths"]["/users"]["get"]
    params = operation.get("parameters", [])

    query_params = [p for p in params if p["in"] == "query"]

    if query_params[0]["required"] is not False:
        errmsg = f"Expected query param required=False, got {query_params[0]['required']!r}"
        raise AssertionError(errmsg)

    return


def test_path_and_query_parameters_combined():
    """
        Test that path and query parameters are combined in the parameters list.
    """
    extras = {
        "rest": {
            "query_params": {"include_posts": bool},
        },
    }
    desc = _create_mock_descriptor(
        handler_name="get_user",
        path="/users/{id:int}",
        extras=extras,
    )
    registry = _create_mock_registry(descriptors=[desc])
    info = _create_default_info()
    generator = OpenAPIGenerator(registry=registry, info=info)

    spec = generator.generate()
    operation = spec["paths"]["/users/{id}"]["get"]
    params = operation.get("parameters", [])

    path_params = [p for p in params if p["in"] == "path"]
    query_params = [p for p in params if p["in"] == "query"]

    if len(path_params) != 1:
        errmsg = f"Expected 1 path parameter, got {len(path_params)}"
        raise AssertionError(errmsg)

    if len(query_params) != 1:
        errmsg = f"Expected 1 query parameter, got {len(query_params)}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Task 4.6: Request Body Building Tests
# =============================================================================

def test_request_body_from_request_schema():
    """
        Test that requestBody is built from extras["rest"]["request_schema"].
    """
    extras = {
        "rest": {
            "request_schema": UserCreate,
        },
    }
    desc = _create_mock_descriptor(
        handler_name="create_user",
        path="/users",
        methods=["POST"],
        extras=extras,
    )
    registry = _create_mock_registry(descriptors=[desc])
    info = _create_default_info()
    generator = OpenAPIGenerator(registry=registry, info=info)

    spec = generator.generate()
    operation = spec["paths"]["/users"]["post"]

    if "requestBody" not in operation:
        errmsg = "Expected 'requestBody' in operation"
        raise AssertionError(errmsg)

    request_body = operation["requestBody"]

    if request_body.get("required") is not True:
        errmsg = f"Expected requestBody required=True, got {request_body.get('required')!r}"
        raise AssertionError(errmsg)

    content = request_body.get("content", {})
    if "application/json" not in content:
        errmsg = f"Expected 'application/json' in content, got {list(content.keys())}"
        raise AssertionError(errmsg)

    schema = content["application/json"]["schema"]
    if "$ref" not in schema:
        errmsg = f"Expected $ref in schema, got {schema}"
        raise AssertionError(errmsg)

    if "UserCreate" not in schema["$ref"]:
        errmsg = f"Expected 'UserCreate' in $ref, got {schema['$ref']!r}"
        raise AssertionError(errmsg)

    return


def test_no_request_body_when_no_schema():
    """
        Test that requestBody is omitted when no request_schema is defined.
    """
    desc = _create_mock_descriptor(handler_name="list_users", path="/users")
    registry = _create_mock_registry(descriptors=[desc])
    info = _create_default_info()
    generator = OpenAPIGenerator(registry=registry, info=info)

    spec = generator.generate()
    operation = spec["paths"]["/users"]["get"]

    if "requestBody" in operation:
        errmsg = f"Expected no 'requestBody', got {operation['requestBody']}"
        raise AssertionError(errmsg)

    return


def test_request_body_schema_registered_in_components():
    """
        Test that the request schema type is registered in components/schemas.
    """
    extras = {
        "rest": {
            "request_schema": UserCreate,
        },
    }
    desc = _create_mock_descriptor(
        handler_name="create_user",
        path="/users",
        methods=["POST"],
        extras=extras,
    )
    registry = _create_mock_registry(descriptors=[desc])
    info = _create_default_info()
    generator = OpenAPIGenerator(registry=registry, info=info)

    spec = generator.generate()
    schemas = spec["components"]["schemas"]

    if "UserCreate" not in schemas:
        errmsg = f"Expected 'UserCreate' in component schemas, got {list(schemas.keys())}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Task 4.7: Response Building Tests
# =============================================================================

def test_success_response_from_response_schema():
    """
        Test that the 200 response is built from extras["rest"]["response_schema"].
    """
    extras = {
        "rest": {
            "response_schema": UserResponse,
        },
    }
    desc = _create_mock_descriptor(
        handler_name="get_user",
        path="/users/{id:int}",
        extras=extras,
    )
    registry = _create_mock_registry(descriptors=[desc])
    info = _create_default_info()
    generator = OpenAPIGenerator(registry=registry, info=info)

    spec = generator.generate()
    operation = spec["paths"]["/users/{id}"]["get"]
    responses = operation["responses"]

    if "200" not in responses:
        errmsg = f"Expected '200' in responses, got {list(responses.keys())}"
        raise AssertionError(errmsg)

    success = responses["200"]
    content = success.get("content", {})

    if "application/json" not in content:
        errmsg = f"Expected 'application/json' in content, got {list(content.keys())}"
        raise AssertionError(errmsg)

    schema = content["application/json"]["schema"]
    if "$ref" not in schema:
        errmsg = f"Expected $ref in schema, got {schema}"
        raise AssertionError(errmsg)

    if "UserResponse" not in schema["$ref"]:
        errmsg = f"Expected 'UserResponse' in $ref, got {schema['$ref']!r}"
        raise AssertionError(errmsg)

    return


def test_success_response_without_schema():
    """
        Test that the 200 response has description only when no response_schema.
    """
    desc = _create_mock_descriptor(handler_name="delete_user", path="/users/{id:int}", methods=["DELETE"])
    registry = _create_mock_registry(descriptors=[desc])
    info = _create_default_info()
    generator = OpenAPIGenerator(registry=registry, info=info)

    spec = generator.generate()
    operation = spec["paths"]["/users/{id}"]["delete"]
    responses = operation["responses"]

    success = responses["200"]
    if "content" in success:
        errmsg = f"Expected no 'content' in 200 response, got {success['content']}"
        raise AssertionError(errmsg)

    if success.get("description") != "Successful response":
        errmsg = f"Expected description 'Successful response', got {success.get('description')!r}"
        raise AssertionError(errmsg)

    return


def test_standard_error_responses_included():
    """
        Test that standard error responses (400, 401, 403, 404, 500) are included.
    """
    desc = _create_mock_descriptor(handler_name="get_user", path="/users/{id:int}")
    registry = _create_mock_registry(descriptors=[desc])
    info = _create_default_info()
    generator = OpenAPIGenerator(registry=registry, info=info)

    spec = generator.generate()
    operation = spec["paths"]["/users/{id}"]["get"]
    responses = operation["responses"]

    for status_code in ["400", "401", "403", "404", "500"]:
        if status_code not in responses:
            errmsg = f"Expected '{status_code}' in responses, got {list(responses.keys())}"
            raise AssertionError(errmsg)

    return


def test_standard_error_responses_reference_rest_error():
    """
        Test that standard error responses reference the RESTError schema.
    """
    desc = _create_mock_descriptor(handler_name="get_user", path="/users/{id:int}")
    registry = _create_mock_registry(descriptors=[desc])
    info = _create_default_info()
    generator = OpenAPIGenerator(registry=registry, info=info)

    spec = generator.generate()
    operation = spec["paths"]["/users/{id}"]["get"]
    responses = operation["responses"]

    for status_code in ["400", "401", "403", "404", "500"]:
        response = responses[status_code]
        content = response.get("content", {})
        json_content = content.get("application/json", {})
        schema = json_content.get("schema", {})

        expected_ref = "#/components/schemas/RESTError"
        if schema.get("$ref") != expected_ref:
            errmsg = f"Expected $ref '{expected_ref}' for {status_code}, got {schema}"
            raise AssertionError(errmsg)

    return


def test_rest_error_schema_in_components():
    """
        Test that the RESTError schema is included in components/schemas.
    """
    desc = _create_mock_descriptor(handler_name="get_user", path="/users")
    registry = _create_mock_registry(descriptors=[desc])
    info = _create_default_info()
    generator = OpenAPIGenerator(registry=registry, info=info)

    spec = generator.generate()
    schemas = spec["components"]["schemas"]

    if "RESTError" not in schemas:
        errmsg = f"Expected 'RESTError' in component schemas, got {list(schemas.keys())}"
        raise AssertionError(errmsg)

    rest_error = schemas["RESTError"]
    if rest_error.get("type") != "object":
        errmsg = f"Expected RESTError type 'object', got {rest_error.get('type')!r}"
        raise AssertionError(errmsg)

    if "error" not in rest_error.get("properties", {}):
        errmsg = "Expected 'error' in RESTError properties"
        raise AssertionError(errmsg)

    if "message" not in rest_error.get("properties", {}):
        errmsg = "Expected 'message' in RESTError properties"
        raise AssertionError(errmsg)

    return


def test_custom_error_responses_from_error_map():
    """
        Test that custom error responses from error_map are included.
    """
    extras = {
        "rest": {
            "error_map": {
                422: ValidationError,
            },
        },
    }
    desc = _create_mock_descriptor(
        handler_name="create_user",
        path="/users",
        methods=["POST"],
        extras=extras,
    )
    registry = _create_mock_registry(descriptors=[desc])
    info = _create_default_info()
    generator = OpenAPIGenerator(registry=registry, info=info)

    spec = generator.generate()
    operation = spec["paths"]["/users"]["post"]
    responses = operation["responses"]

    if "422" not in responses:
        errmsg = f"Expected '422' in responses, got {list(responses.keys())}"
        raise AssertionError(errmsg)

    response_422 = responses["422"]
    content = response_422.get("content", {})

    if "application/json" not in content:
        errmsg = f"Expected 'application/json' in 422 content, got {list(content.keys())}"
        raise AssertionError(errmsg)

    schema = content["application/json"]["schema"]
    if "$ref" not in schema:
        errmsg = f"Expected $ref in 422 schema, got {schema}"
        raise AssertionError(errmsg)

    if "ValidationError" not in schema["$ref"]:
        errmsg = f"Expected 'ValidationError' in $ref, got {schema['$ref']!r}"
        raise AssertionError(errmsg)

    return


def test_custom_error_overrides_standard():
    """
        Test that a custom error_map entry for a standard code overrides it.
    """
    extras = {
        "rest": {
            "error_map": {
                400: ValidationError,
            },
        },
    }
    desc = _create_mock_descriptor(
        handler_name="create_user",
        path="/users",
        methods=["POST"],
        extras=extras,
    )
    registry = _create_mock_registry(descriptors=[desc])
    info = _create_default_info()
    generator = OpenAPIGenerator(registry=registry, info=info)

    spec = generator.generate()
    operation = spec["paths"]["/users"]["post"]
    responses = operation["responses"]

    response_400 = responses["400"]
    content = response_400.get("content", {})
    schema = content.get("application/json", {}).get("schema", {})

    # The custom error_map should override the standard 400 response
    if "$ref" not in schema:
        errmsg = f"Expected $ref in 400 schema, got {schema}"
        raise AssertionError(errmsg)

    if "ValidationError" not in schema["$ref"]:
        errmsg = f"Expected 'ValidationError' in $ref for 400, got {schema['$ref']!r}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Tag Collection Tests
# =============================================================================

def test_tags_collected_from_descriptors():
    """
        Test that tags are collected from all descriptors.
    """
    desc1 = _create_mock_descriptor(handler_name="list_users", path="/users", tags=["users"])
    desc2 = _create_mock_descriptor(handler_name="list_posts", path="/posts", tags=["posts"])
    registry = _create_mock_registry(descriptors=[desc1, desc2])
    info = _create_default_info()
    generator = OpenAPIGenerator(registry=registry, info=info)

    spec = generator.generate()
    tags = spec.get("tags", [])

    tag_names = [t["name"] for t in tags]
    if "users" not in tag_names:
        errmsg = f"Expected 'users' in tags, got {tag_names}"
        raise AssertionError(errmsg)

    if "posts" not in tag_names:
        errmsg = f"Expected 'posts' in tags, got {tag_names}"
        raise AssertionError(errmsg)

    return


def test_tag_descriptions_from_config():
    """
        Test that tag descriptions come from tag_descriptions config.
    """
    desc = _create_mock_descriptor(handler_name="list_users", path="/users", tags=["users"])
    registry = _create_mock_registry(descriptors=[desc])
    info = _create_default_info()
    generator = OpenAPIGenerator(
        registry=registry,
        info=info,
        tag_descriptions={"users": "User management endpoints"},
    )

    spec = generator.generate()
    tags = spec.get("tags", [])

    users_tag = [t for t in tags if t["name"] == "users"]
    if len(users_tag) != 1:
        errmsg = f"Expected 1 'users' tag, got {len(users_tag)}"
        raise AssertionError(errmsg)

    if users_tag[0].get("description") != "User management endpoints":
        errmsg = f"Expected description, got {users_tag[0].get('description')!r}"
        raise AssertionError(errmsg)

    return


def test_duplicate_tags_collected_once():
    """
        Test that duplicate tags are only collected once.
    """
    desc1 = _create_mock_descriptor(handler_name="list_users", path="/users", tags=["users"])
    desc2 = _create_mock_descriptor(handler_name="get_user", path="/users/{id:int}", tags=["users"])
    registry = _create_mock_registry(descriptors=[desc1, desc2])
    info = _create_default_info()
    generator = OpenAPIGenerator(registry=registry, info=info)

    spec = generator.generate()
    tags = spec.get("tags", [])

    users_tags = [t for t in tags if t["name"] == "users"]
    if len(users_tags) != 1:
        errmsg = f"Expected exactly 1 'users' tag, got {len(users_tags)}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Components Building Tests
# =============================================================================

def test_components_includes_security_schemes():
    """
        Test that components includes security schemes when provided.
    """
    registry = _create_mock_registry()
    info = _create_default_info()
    security_schemes = {"bearer": HTTPSecurityScheme(scheme="bearer")}
    generator = OpenAPIGenerator(
        registry=registry,
        info=info,
        security_schemes=security_schemes,
    )

    spec = generator.generate()
    components = spec.get("components", {})

    if "securitySchemes" not in components:
        errmsg = "Expected 'securitySchemes' in components"
        raise AssertionError(errmsg)

    if "bearer" not in components["securitySchemes"]:
        errmsg = f"Expected 'bearer' in securitySchemes, got {list(components['securitySchemes'].keys())}"
        raise AssertionError(errmsg)

    bearer = components["securitySchemes"]["bearer"]
    if bearer.get("type") != "http":
        errmsg = f"Expected type 'http', got {bearer.get('type')!r}"
        raise AssertionError(errmsg)

    return


def test_refresh_clears_cache():
    """
        Test that refresh() clears the cached specification.
    """
    registry = _create_mock_registry()
    info = _create_default_info()
    generator = OpenAPIGenerator(registry=registry, info=info)

    generator.generate()

    if generator._cache is None:
        errmsg = "Expected cache to be populated after generate()"
        raise AssertionError(errmsg)

    generator.refresh()

    if generator._cache is not None:
        errmsg = "Expected cache to be None after refresh()"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Task 5.1: Security Extraction from access_policy Tests
# =============================================================================

def test_security_with_require_auth_references_all_schemes():
    """
        Test that when require_auth is True, all configured security schemes
        are referenced in the operation security array.
    """
    access_policy = _create_mock_access_policy(require_auth=True, scopes=[])
    constraints = _create_mock_constraints(access_policy=access_policy)
    desc = _create_mock_descriptor(
        handler_name="get_users",
        path="/users",
        constraints=constraints,
    )
    registry = _create_mock_registry(descriptors=[desc])
    info = _create_default_info()

    bearer_scheme = HTTPSecurityScheme(scheme="bearer")
    api_key_scheme = APIKeySecurityScheme(name="X-API-Key", in_="header")

    generator = OpenAPIGenerator(
        registry=registry,
        info=info,
        security_schemes={"bearer_auth": bearer_scheme, "api_key": api_key_scheme},
    )

    spec = generator.generate()
    operation = spec["paths"]["/users"]["get"]
    security = operation.get("security", [])

    scheme_names = []
    for req in security:
        for name in req:
            scheme_names.append(name)

    if "bearer_auth" not in scheme_names:
        errmsg = f"Expected 'bearer_auth' in security references, got {scheme_names}"
        raise AssertionError(errmsg)

    if "api_key" not in scheme_names:
        errmsg = f"Expected 'api_key' in security references, got {scheme_names}"
        raise AssertionError(errmsg)

    return


def test_security_no_auth_returns_none():
    """
        Test that when require_auth is False, no security is set.
    """
    access_policy = _create_mock_access_policy(require_auth=False)
    constraints = _create_mock_constraints(access_policy=access_policy)
    desc = _create_mock_descriptor(
        handler_name="public_endpoint",
        path="/public",
        constraints=constraints,
    )
    registry = _create_mock_registry(descriptors=[desc])
    info = _create_default_info()
    generator = OpenAPIGenerator(registry=registry, info=info)

    spec = generator.generate()
    operation = spec["paths"]["/public"]["get"]

    if "security" in operation:
        errmsg = f"Expected no 'security' key when require_auth is False, got {operation['security']}"
        raise AssertionError(errmsg)

    return


def test_security_no_access_policy_returns_none():
    """
        Test that when access_policy is None, no security is set.
    """
    constraints = _create_mock_constraints(access_policy=None)
    desc = _create_mock_descriptor(
        handler_name="open_endpoint",
        path="/open",
        constraints=constraints,
    )
    registry = _create_mock_registry(descriptors=[desc])
    info = _create_default_info()
    generator = OpenAPIGenerator(registry=registry, info=info)

    spec = generator.generate()
    operation = spec["paths"]["/open"]["get"]

    if "security" in operation:
        errmsg = f"Expected no 'security' key when access_policy is None, got {operation['security']}"
        raise AssertionError(errmsg)

    return


def test_security_fallback_to_generic_oauth2():
    """
        Test that when no security_schemes are configured, falls back to
        a generic 'oauth2' reference.
    """
    access_policy = _create_mock_access_policy(require_auth=True, scopes=["read"])
    constraints = _create_mock_constraints(access_policy=access_policy)
    desc = _create_mock_descriptor(
        handler_name="get_data",
        path="/data",
        constraints=constraints,
    )
    registry = _create_mock_registry(descriptors=[desc])
    info = _create_default_info()
    generator = OpenAPIGenerator(registry=registry, info=info)

    spec = generator.generate()
    operation = spec["paths"]["/data"]["get"]
    security = operation.get("security", [])

    if len(security) != 1:
        errmsg = f"Expected 1 security requirement, got {len(security)}"
        raise AssertionError(errmsg)

    if "oauth2" not in security[0]:
        errmsg = f"Expected 'oauth2' fallback, got {security[0]}"
        raise AssertionError(errmsg)

    if security[0]["oauth2"] != ["read"]:
        errmsg = f"Expected scopes ['read'], got {security[0]['oauth2']}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Task 5.2: Security Schemes Building Tests
# =============================================================================

def test_components_includes_apikey_scheme():
    """
        Test that components includes apiKey security scheme when provided.
    """
    registry = _create_mock_registry()
    info = _create_default_info()
    api_key = APIKeySecurityScheme(name="X-API-Key", in_="header")
    generator = OpenAPIGenerator(
        registry=registry,
        info=info,
        security_schemes={"api_key": api_key},
    )

    spec = generator.generate()
    schemes = spec["components"]["securitySchemes"]

    if "api_key" not in schemes:
        errmsg = f"Expected 'api_key' in securitySchemes, got {list(schemes.keys())}"
        raise AssertionError(errmsg)

    if schemes["api_key"]["type"] != "apiKey":
        errmsg = f"Expected type 'apiKey', got {schemes['api_key']['type']!r}"
        raise AssertionError(errmsg)

    if schemes["api_key"]["in"] != "header":
        errmsg = f"Expected in 'header', got {schemes['api_key']['in']!r}"
        raise AssertionError(errmsg)

    return


def test_components_includes_oauth2_scheme():
    """
        Test that components includes OAuth2 security scheme when provided.
    """
    registry = _create_mock_registry()
    info = _create_default_info()
    flows = OAuthFlows(
        authorization_code=OAuthFlow(
            scopes={"read": "Read access"},
            authorization_url="https://example.com/auth",
            token_url="https://example.com/token",
        )
    )
    oauth2 = OAuth2SecurityScheme(flows=flows)
    generator = OpenAPIGenerator(
        registry=registry,
        info=info,
        security_schemes={"oauth2": oauth2},
    )

    spec = generator.generate()
    schemes = spec["components"]["securitySchemes"]

    if "oauth2" not in schemes:
        errmsg = f"Expected 'oauth2' in securitySchemes, got {list(schemes.keys())}"
        raise AssertionError(errmsg)

    if schemes["oauth2"]["type"] != "oauth2":
        errmsg = f"Expected type 'oauth2', got {schemes['oauth2']['type']!r}"
        raise AssertionError(errmsg)

    if "flows" not in schemes["oauth2"]:
        errmsg = "Expected 'flows' in oauth2 scheme"
        raise AssertionError(errmsg)

    return


def test_components_includes_multiple_schemes():
    """
        Test that components includes all configured security schemes.
    """
    registry = _create_mock_registry()
    info = _create_default_info()
    bearer = HTTPSecurityScheme(scheme="bearer", bearer_format="JWT")
    api_key = APIKeySecurityScheme(name="X-API-Key", in_="header")
    generator = OpenAPIGenerator(
        registry=registry,
        info=info,
        security_schemes={"bearer": bearer, "api_key": api_key},
    )

    spec = generator.generate()
    schemes = spec["components"]["securitySchemes"]

    if len(schemes) != 2:
        errmsg = f"Expected 2 security schemes, got {len(schemes)}: {list(schemes.keys())}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Task 5.3: Scope Handling for OAuth2 Tests
# =============================================================================

def test_security_oauth2_includes_scopes():
    """
        Test that OAuth2 security requirements include scopes from access_policy.
    """
    access_policy = _create_mock_access_policy(
        require_auth=True,
        scopes=["read", "write"],
    )
    constraints = _create_mock_constraints(access_policy=access_policy)
    desc = _create_mock_descriptor(
        handler_name="update_user",
        path="/users/{id:int}",
        methods=["PUT"],
        constraints=constraints,
    )
    registry = _create_mock_registry(descriptors=[desc])
    info = _create_default_info()

    flows = OAuthFlows(
        authorization_code=OAuthFlow(
            scopes={"read": "Read", "write": "Write"},
            authorization_url="https://example.com/auth",
            token_url="https://example.com/token",
        )
    )
    oauth2 = OAuth2SecurityScheme(flows=flows)
    generator = OpenAPIGenerator(
        registry=registry,
        info=info,
        security_schemes={"oauth2": oauth2},
    )

    spec = generator.generate()
    operation = spec["paths"]["/users/{id}"]["put"]
    security = operation.get("security", [])

    oauth2_req = None
    for req in security:
        if "oauth2" in req:
            oauth2_req = req
            break

    if oauth2_req is None:
        errmsg = f"Expected 'oauth2' in security requirements, got {security}"
        raise AssertionError(errmsg)

    if oauth2_req["oauth2"] != ["read", "write"]:
        errmsg = f"Expected scopes ['read', 'write'], got {oauth2_req['oauth2']}"
        raise AssertionError(errmsg)

    return


def test_security_non_oauth2_uses_empty_scopes():
    """
        Test that non-OAuth2 schemes use empty scope arrays.
    """
    access_policy = _create_mock_access_policy(
        require_auth=True,
        scopes=["read"],
    )
    constraints = _create_mock_constraints(access_policy=access_policy)
    desc = _create_mock_descriptor(
        handler_name="get_data",
        path="/data",
        constraints=constraints,
    )
    registry = _create_mock_registry(descriptors=[desc])
    info = _create_default_info()

    bearer = HTTPSecurityScheme(scheme="bearer")
    generator = OpenAPIGenerator(
        registry=registry,
        info=info,
        security_schemes={"bearer": bearer},
    )

    spec = generator.generate()
    operation = spec["paths"]["/data"]["get"]
    security = operation.get("security", [])

    bearer_req = None
    for req in security:
        if "bearer" in req:
            bearer_req = req
            break

    if bearer_req is None:
        errmsg = f"Expected 'bearer' in security requirements, got {security}"
        raise AssertionError(errmsg)

    if bearer_req["bearer"] != []:
        errmsg = f"Expected empty scopes for HTTP scheme, got {bearer_req['bearer']}"
        raise AssertionError(errmsg)

    return


def test_security_mixed_schemes_scope_handling():
    """
        Test that mixed scheme types handle scopes correctly:
        OAuth2 gets scopes, non-OAuth2 gets empty arrays.
    """
    access_policy = _create_mock_access_policy(
        require_auth=True,
        scopes=["admin"],
    )
    constraints = _create_mock_constraints(access_policy=access_policy)
    desc = _create_mock_descriptor(
        handler_name="admin_action",
        path="/admin",
        constraints=constraints,
    )
    registry = _create_mock_registry(descriptors=[desc])
    info = _create_default_info()

    flows = OAuthFlows(
        client_credentials=OAuthFlow(
            scopes={"admin": "Admin access"},
            token_url="https://example.com/token",
        )
    )
    oauth2 = OAuth2SecurityScheme(flows=flows)
    api_key = APIKeySecurityScheme(name="X-API-Key", in_="header")

    generator = OpenAPIGenerator(
        registry=registry,
        info=info,
        security_schemes={"oauth2": oauth2, "api_key": api_key},
    )

    spec = generator.generate()
    operation = spec["paths"]["/admin"]["get"]
    security = operation.get("security", [])

    oauth2_scopes = None
    api_key_scopes = None
    for req in security:
        if "oauth2" in req:
            oauth2_scopes = req["oauth2"]
        if "api_key" in req:
            api_key_scopes = req["api_key"]

    if oauth2_scopes != ["admin"]:
        errmsg = f"Expected OAuth2 scopes ['admin'], got {oauth2_scopes}"
        raise AssertionError(errmsg)

    if api_key_scopes != []:
        errmsg = f"Expected empty scopes for apiKey, got {api_key_scopes}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Task 5.5: Tag Collection and Building Tests
# =============================================================================

def test_tags_with_descriptions_from_config():
    """
        Test that tag_descriptions configuration provides descriptions for tags.
    """
    desc1 = _create_mock_descriptor(handler_name="list_users", path="/users", tags=["users"])
    desc2 = _create_mock_descriptor(handler_name="list_orders", path="/orders", tags=["orders"])
    registry = _create_mock_registry(descriptors=[desc1, desc2])
    info = _create_default_info()
    generator = OpenAPIGenerator(
        registry=registry,
        info=info,
        tag_descriptions={
            "users": "User management",
            "orders": "Order management",
        },
    )

    spec = generator.generate()
    tags = spec.get("tags", [])

    for tag in tags:
        if tag["name"] == "users" and tag.get("description") != "User management":
            errmsg = f"Expected 'User management' description for users tag, got {tag.get('description')!r}"
            raise AssertionError(errmsg)
        if tag["name"] == "orders" and tag.get("description") != "Order management":
            errmsg = f"Expected 'Order management' description for orders tag, got {tag.get('description')!r}"
            raise AssertionError(errmsg)

    return


def test_tags_without_descriptions_omit_description():
    """
        Test that tags without configured descriptions omit the description field.
    """
    desc = _create_mock_descriptor(handler_name="list_items", path="/items", tags=["items"])
    registry = _create_mock_registry(descriptors=[desc])
    info = _create_default_info()
    generator = OpenAPIGenerator(registry=registry, info=info)

    spec = generator.generate()
    tags = spec.get("tags", [])

    items_tag = [t for t in tags if t["name"] == "items"]
    if len(items_tag) != 1:
        errmsg = f"Expected 1 'items' tag, got {len(items_tag)}"
        raise AssertionError(errmsg)

    if "description" in items_tag[0]:
        errmsg = f"Expected no description for 'items' tag, got {items_tag[0]['description']!r}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Task 5.6: Automatic Tag Derivation from Path Tests
# =============================================================================

def test_derive_tags_from_path_enabled():
    """
        Test that tags are derived from path when derive_tags_from_path is True
        and endpoint has no explicit tags.
    """
    desc = _create_mock_descriptor(handler_name="list_users", path="/users", tags=[])
    registry = _create_mock_registry(descriptors=[desc])
    info = _create_default_info()
    generator = OpenAPIGenerator(
        registry=registry,
        info=info,
        derive_tags_from_path=True,
    )

    spec = generator.generate()
    operation = spec["paths"]["/users"]["get"]

    actual_tags = operation.get("tags", [])
    if actual_tags != ["users"]:
        errmsg = f"Expected derived tags ['users'], got {actual_tags}"
        raise AssertionError(errmsg)

    tags = spec.get("tags", [])
    tag_names = [t["name"] for t in tags]
    if "users" not in tag_names:
        errmsg = f"Expected 'users' in collected tags, got {tag_names}"
        raise AssertionError(errmsg)

    return


def test_derive_tags_from_path_with_parameters():
    """
        Test that tag derivation skips parameter segments.
    """
    desc = _create_mock_descriptor(handler_name="get_user", path="/users/{id:int}", tags=[])
    registry = _create_mock_registry(descriptors=[desc])
    info = _create_default_info()
    generator = OpenAPIGenerator(
        registry=registry,
        info=info,
        derive_tags_from_path=True,
    )

    spec = generator.generate()
    operation = spec["paths"]["/users/{id}"]["get"]

    actual_tags = operation.get("tags", [])
    if actual_tags != ["users"]:
        errmsg = f"Expected derived tags ['users'], got {actual_tags}"
        raise AssertionError(errmsg)

    return


def test_derive_tags_disabled_by_default():
    """
        Test that tag derivation is disabled by default.
    """
    desc = _create_mock_descriptor(handler_name="list_users", path="/users", tags=[])
    registry = _create_mock_registry(descriptors=[desc])
    info = _create_default_info()
    generator = OpenAPIGenerator(registry=registry, info=info)

    spec = generator.generate()
    operation = spec["paths"]["/users"]["get"]

    if "tags" in operation:
        errmsg = f"Expected no tags when derive_tags_from_path is disabled, got {operation['tags']}"
        raise AssertionError(errmsg)

    return


def test_derive_tags_does_not_override_explicit_tags():
    """
        Test that explicit tags are preserved when derive_tags_from_path is enabled.
    """
    desc = _create_mock_descriptor(
        handler_name="list_users",
        path="/users",
        tags=["people"],
    )
    registry = _create_mock_registry(descriptors=[desc])
    info = _create_default_info()
    generator = OpenAPIGenerator(
        registry=registry,
        info=info,
        derive_tags_from_path=True,
    )

    spec = generator.generate()
    operation = spec["paths"]["/users"]["get"]

    actual_tags = operation.get("tags", [])
    if actual_tags != ["people"]:
        errmsg = f"Expected explicit tags ['people'], got {actual_tags}"
        raise AssertionError(errmsg)

    return


def test_derive_tags_with_descriptions():
    """
        Test that derived tags can have descriptions from tag_descriptions config.
    """
    desc = _create_mock_descriptor(handler_name="list_users", path="/users", tags=[])
    registry = _create_mock_registry(descriptors=[desc])
    info = _create_default_info()
    generator = OpenAPIGenerator(
        registry=registry,
        info=info,
        derive_tags_from_path=True,
        tag_descriptions={"users": "User endpoints"},
    )

    spec = generator.generate()
    tags = spec.get("tags", [])

    users_tag = [t for t in tags if t["name"] == "users"]
    if len(users_tag) != 1:
        errmsg = f"Expected 1 'users' tag, got {len(users_tag)}"
        raise AssertionError(errmsg)

    if users_tag[0].get("description") != "User endpoints":
        errmsg = f"Expected description 'User endpoints', got {users_tag[0].get('description')!r}"
        raise AssertionError(errmsg)

    return
