"""
    Property test for path parameter extraction in the OpenAPI generator.

    This module verifies Property 2: Path Parameter Extraction.

    For any EndpointDescriptor with path parameters (e.g., /users/{id:int}),
    the generated OpenAPI path SHALL contain corresponding parameter objects
    with correct names and types.

    **Validates: Requirements 3.1, 3.2**
"""

from ccai.testbase.mocking import Mock

from ccai.webworks.openapi.configuration import OpenAPIInfo
from ccai.webworks.openapi.generator import (
    OpenAPIGenerator,
    extract_path_parameters,
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


def _create_mock_constraints():
    """
        Create a mock EndpointConstraints object with no access policy.
    """
    mock_constraints = Mock()
    mock_constraints.configure(recursive=True)
    ctx = mock_constraints.mock_context()
    ctx.set_attribute("access_policy", None)
    return mock_constraints



def _create_mock_descriptor(handler_name, path, methods=None):
    """
        Create a mock EndpointDescriptor with the given path and methods.
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
    ctx.set_attribute("tags", [])
    ctx.set_attribute("doc", None)
    ctx.set_attribute("extras", {"endpoint_type": "rest"})
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
# Test Cases: Diverse path patterns with expected parameter extractions
# =============================================================================

# Each entry: (description, path, expected_openapi_path, expected_params)
# expected_params is a list of (name, expected_schema) tuples

_PATH_TEST_CASES = [
    (
        "single int parameter",
        "/users/{id:int}",
        "/users/{id}",
        [("id", {"type": "integer"})],
    ),
    (
        "single str parameter",
        "/items/{slug:str}",
        "/items/{slug}",
        [("slug", {"type": "string"})],
    ),
    (
        "single float parameter",
        "/measurements/{value:float}",
        "/measurements/{value}",
        [("value", {"type": "number"})],
    ),
    (
        "single bool parameter",
        "/flags/{active:bool}",
        "/flags/{active}",
        [("active", {"type": "boolean"})],
    ),
    (
        "single uuid parameter",
        "/resources/{resource_id:uuid}",
        "/resources/{resource_id}",
        [("resource_id", {"type": "string", "format": "uuid"})],
    ),
    (
        "parameter without type annotation defaults to string",
        "/items/{name}",
        "/items/{name}",
        [("name", {"type": "string"})],
    ),
    (
        "no parameters at all",
        "/health",
        "/health",
        [],
    ),
    (
        "multiple parameters of different types",
        "/orgs/{org_id:int}/users/{user_id:uuid}",
        "/orgs/{org_id}/users/{user_id}",
        [
            ("org_id", {"type": "integer"}),
            ("user_id", {"type": "string", "format": "uuid"}),
        ],
    ),
    (
        "three parameters in nested path",
        "/api/{version:str}/projects/{project_id:int}/tasks/{task_id:int}",
        "/api/{version}/projects/{project_id}/tasks/{task_id}",
        [
            ("version", {"type": "string"}),
            ("project_id", {"type": "integer"}),
            ("task_id", {"type": "integer"}),
        ],
    ),
    (
        "mixed typed and untyped parameters",
        "/teams/{team_id:int}/members/{member_name}",
        "/teams/{team_id}/members/{member_name}",
        [
            ("team_id", {"type": "integer"}),
            ("member_name", {"type": "string"}),
        ],
    ),
    (
        "root path with no segments",
        "/",
        "/",
        [],
    ),
    (
        "deeply nested path with single parameter",
        "/api/v1/admin/settings/{key:str}",
        "/api/v1/admin/settings/{key}",
        [("key", {"type": "string"})],
    ),
    (
        "two uuid parameters",
        "/workspaces/{ws_id:uuid}/documents/{doc_id:uuid}",
        "/workspaces/{ws_id}/documents/{doc_id}",
        [
            ("ws_id", {"type": "string", "format": "uuid"}),
            ("doc_id", {"type": "string", "format": "uuid"}),
        ],
    ),
]


# =============================================================================
# Property Test
# =============================================================================

def test_property_path_parameter_extraction():
    """
        **Validates: Requirements 3.1, 3.2**

        Property 2: Path Parameter Extraction

        For any EndpointDescriptor with path parameters (e.g., /users/{id:int}),
        the generated OpenAPI path SHALL contain corresponding parameter objects
        with correct names and types.

        This test exercises the property across diverse path patterns including
        single parameters, multiple parameters, different types (int, str, float,
        bool, uuid), no parameters, and nested paths.
    """
    total_cases = len(_PATH_TEST_CASES)
    total_param_checks = 0

    for case_desc, raw_path, expected_openapi_path, expected_params in _PATH_TEST_CASES:

        # -----------------------------------------------------------------
        # Step 1: Verify strip_path_type_annotations produces correct path
        # -----------------------------------------------------------------
        stripped = strip_path_type_annotations(raw_path)
        if stripped != expected_openapi_path:
            errmsg = (
                f"[{case_desc}] strip_path_type_annotations('{raw_path}') "
                f"returned '{stripped}', expected '{expected_openapi_path}'"
            )
            raise AssertionError(errmsg)

        # -----------------------------------------------------------------
        # Step 2: Verify extract_path_parameters returns correct params
        # -----------------------------------------------------------------
        extracted = extract_path_parameters(raw_path)

        if len(extracted) != len(expected_params):
            errmsg = (
                f"[{case_desc}] extract_path_parameters('{raw_path}') "
                f"returned {len(extracted)} params, expected {len(expected_params)}"
            )
            raise AssertionError(errmsg)

        for idx, (exp_name, exp_schema) in enumerate(expected_params):
            param = extracted[idx]

            if param["name"] != exp_name:
                errmsg = (
                    f"[{case_desc}] param[{idx}] name is '{param['name']}', "
                    f"expected '{exp_name}'"
                )
                raise AssertionError(errmsg)

            if param["in"] != "path":
                errmsg = (
                    f"[{case_desc}] param[{idx}] 'in' is '{param['in']}', "
                    f"expected 'path'"
                )
                raise AssertionError(errmsg)

            if param["required"] is not True:
                errmsg = (
                    f"[{case_desc}] param[{idx}] 'required' is "
                    f"{param['required']}, expected True"
                )
                raise AssertionError(errmsg)

            if param["schema"] != exp_schema:
                errmsg = (
                    f"[{case_desc}] param[{idx}] schema is {param['schema']}, "
                    f"expected {exp_schema}"
                )
                raise AssertionError(errmsg)

            total_param_checks += 1

        # -----------------------------------------------------------------
        # Step 3: Verify full generator produces correct path and params
        # -----------------------------------------------------------------
        descriptor = _create_mock_descriptor(
            handler_name=f"handle_{case_desc.replace(' ', '_')}",
            path=raw_path,
            methods=["GET"],
        )
        registry = _create_mock_registry([descriptor])
        info = _create_default_info()
        generator = OpenAPIGenerator(registry=registry, info=info)

        spec = generator.generate()
        paths = spec["paths"]

        # The generated spec should contain the stripped path
        if expected_openapi_path not in paths:
            errmsg = (
                f"[{case_desc}] generated spec paths {list(paths.keys())} "
                f"does not contain expected path '{expected_openapi_path}'"
            )
            raise AssertionError(errmsg)

        operation = paths[expected_openapi_path].get("get")
        if operation is None:
            errmsg = (
                f"[{case_desc}] no 'get' operation found at path "
                f"'{expected_openapi_path}'"
            )
            raise AssertionError(errmsg)

        op_params = operation.get("parameters", [])
        path_params = [p for p in op_params if p.get("in") == "path"]

        if len(path_params) != len(expected_params):
            errmsg = (
                f"[{case_desc}] operation has {len(path_params)} path params, "
                f"expected {len(expected_params)}"
            )
            raise AssertionError(errmsg)

        for idx, (exp_name, exp_schema) in enumerate(expected_params):
            op_param = path_params[idx]

            if op_param["name"] != exp_name:
                errmsg = (
                    f"[{case_desc}] operation param[{idx}] name is "
                    f"'{op_param['name']}', expected '{exp_name}'"
                )
                raise AssertionError(errmsg)

            if op_param["schema"] != exp_schema:
                errmsg = (
                    f"[{case_desc}] operation param[{idx}] schema is "
                    f"{op_param['schema']}, expected {exp_schema}"
                )
                raise AssertionError(errmsg)

    # Verify we tested a meaningful number of cases
    if total_cases < 10:
        errmsg = f"Expected at least 10 test cases, got {total_cases}"
        raise AssertionError(errmsg)

    if total_param_checks < 15:
        errmsg = (
            f"Expected at least 15 parameter checks, got {total_param_checks}"
        )
        raise AssertionError(errmsg)

    return
