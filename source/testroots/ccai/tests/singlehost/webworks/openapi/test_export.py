"""
    Tests for the export functionality of the OpenAPI_Generator class.

    This module contains unit tests covering JSON export, YAML export (when
    PyYAML is available), file export, and format inference from file extensions.

    **Validates: Requirements 1.5, 10.1, 10.2, 10.6**
"""

import json
import os
import tempfile

from ccai.testbase.mocking import Mock

from ccai.webworks.openapi.configuration import OpenAPIInfo, ServerObject
from ccai.webworks.openapi.generator import OpenAPIGenerator


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


def _create_generator_with_endpoint():
    """
        Create an OpenAPI_Generator with a single endpoint for testing.
    """
    doc = _create_mock_doc(summary="Get users", description="Retrieve all users")
    descriptor = _create_mock_descriptor(
        handler_name="get_users",
        path="/users",
        methods=["GET"],
        tags=["users"],
        doc=doc,
    )
    registry = _create_mock_registry([descriptor])
    info = _create_default_info()
    servers = [ServerObject(url="https://api.example.com")]

    generator = OpenAPIGenerator(
        registry=registry,
        info=info,
        servers=servers,
    )
    return generator


# =============================================================================
# Task 8.1: JSON Export Tests
# =============================================================================

def test_generate_json_returns_string():
    """
        Verify that generate_json returns a string.
    """
    generator = _create_generator_with_endpoint()
    result = generator.generate_json()

    if not isinstance(result, str):
        errmsg = f"Expected str, got {type(result).__name__}"
        raise AssertionError(errmsg)

    return


def test_generate_json_is_valid_json():
    """
        Verify that generate_json returns valid JSON that can be parsed.
    """
    generator = _create_generator_with_endpoint()
    json_str = generator.generate_json()

    parsed = json.loads(json_str)

    if not isinstance(parsed, dict):
        errmsg = f"Expected dict after parsing, got {type(parsed).__name__}"
        raise AssertionError(errmsg)

    return


def test_generate_json_contains_openapi_version():
    """
        Verify that the JSON output contains the openapi version field.
    """
    generator = _create_generator_with_endpoint()
    json_str = generator.generate_json()
    parsed = json.loads(json_str)

    if "openapi" not in parsed:
        errmsg = "JSON output missing 'openapi' field"
        raise AssertionError(errmsg)

    return


def test_generate_json_default_indent():
    """
        Verify that generate_json uses 2-space indentation by default.
    """
    generator = _create_generator_with_endpoint()
    json_str = generator.generate_json()

    # With indent=2, we expect lines indented with 2 spaces
    lines = json_str.split("\n")
    indented_lines = [line for line in lines if line.startswith("  ") and not line.startswith("    ")]

    if len(indented_lines) == 0:
        errmsg = "Expected 2-space indented lines in JSON output"
        raise AssertionError(errmsg)

    return


def test_generate_json_custom_indent():
    """
        Verify that generate_json respects a custom indent parameter.
    """
    generator = _create_generator_with_endpoint()
    json_str = generator.generate_json(indent=4)

    lines = json_str.split("\n")
    indented_lines = [line for line in lines if line.startswith("    ") and not line.startswith("        ")]

    if len(indented_lines) == 0:
        errmsg = "Expected 4-space indented lines in JSON output"
        raise AssertionError(errmsg)

    return


def test_generate_json_deterministic_ordering():
    """
        Verify that generate_json produces deterministic output with sorted keys.
    """
    generator = _create_generator_with_endpoint()
    json_str_1 = generator.generate_json()
    json_str_2 = generator.generate_json()

    if json_str_1 != json_str_2:
        errmsg = "JSON output is not deterministic across calls"
        raise AssertionError(errmsg)

    return


def test_generate_json_roundtrip_matches_generate():
    """
        Verify that parsing the JSON output produces a dict equivalent
        to the original generate() output.
    """
    generator = _create_generator_with_endpoint()
    spec = generator.generate()
    json_str = generator.generate_json()
    parsed = json.loads(json_str)

    if parsed != spec:
        errmsg = "Parsed JSON does not match original spec dict"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Task 8.2: YAML Export Tests
# =============================================================================

def test_generate_yaml_returns_string():
    """
        Verify that generate_yaml returns a string when PyYAML is available.
    """
    try:
        import yaml  # noqa: F401
    except ImportError:
        # Skip test if PyYAML is not installed
        return

    generator = _create_generator_with_endpoint()
    result = generator.generate_yaml()

    if not isinstance(result, str):
        errmsg = f"Expected str, got {type(result).__name__}"
        raise AssertionError(errmsg)

    return


def test_generate_yaml_roundtrip_matches_generate():
    """
        Verify that parsing the YAML output produces a dict equivalent
        to the original generate() output.
    """
    try:
        import yaml
    except ImportError:
        # Skip test if PyYAML is not installed
        return

    generator = _create_generator_with_endpoint()
    spec = generator.generate()
    yaml_str = generator.generate_yaml()
    parsed = yaml.safe_load(yaml_str)

    if parsed != spec:
        errmsg = "Parsed YAML does not match original spec dict"
        raise AssertionError(errmsg)

    return


def test_generate_yaml_deterministic_ordering():
    """
        Verify that generate_yaml produces deterministic output.
    """
    try:
        import yaml  # noqa: F401
    except ImportError:
        return

    generator = _create_generator_with_endpoint()
    yaml_str_1 = generator.generate_yaml()
    yaml_str_2 = generator.generate_yaml()

    if yaml_str_1 != yaml_str_2:
        errmsg = "YAML output is not deterministic across calls"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Task 8.3: File Export Tests
# =============================================================================

def test_export_json_file():
    """
        Verify that export writes a valid JSON file when path ends with .json.
    """
    generator = _create_generator_with_endpoint()
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, "spec.json")

    try:
        generator.export(file_path)

        if not os.path.exists(file_path):
            errmsg = f"Expected file to exist at {file_path}"
            raise AssertionError(errmsg)

        with open(file_path, "r", encoding="utf-8") as fh:
            content = fh.read()

        parsed = json.loads(content)

        if "openapi" not in parsed:
            errmsg = "Exported JSON file missing 'openapi' field"
            raise AssertionError(errmsg)
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
        os.rmdir(temp_dir)

    return


def test_export_yaml_file():
    """
        Verify that export writes a valid YAML file when path ends with .yaml.
    """
    try:
        import yaml
    except ImportError:
        return

    generator = _create_generator_with_endpoint()
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, "spec.yaml")

    try:
        generator.export(file_path)

        if not os.path.exists(file_path):
            errmsg = f"Expected file to exist at {file_path}"
            raise AssertionError(errmsg)

        with open(file_path, "r", encoding="utf-8") as fh:
            content = fh.read()

        parsed = yaml.safe_load(content)

        if "openapi" not in parsed:
            errmsg = "Exported YAML file missing 'openapi' field"
            raise AssertionError(errmsg)
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
        os.rmdir(temp_dir)

    return


def test_export_yml_extension():
    """
        Verify that export infers YAML format from .yml extension.
    """
    try:
        import yaml
    except ImportError:
        return

    generator = _create_generator_with_endpoint()
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, "spec.yml")

    try:
        generator.export(file_path)

        if not os.path.exists(file_path):
            errmsg = f"Expected file to exist at {file_path}"
            raise AssertionError(errmsg)

        with open(file_path, "r", encoding="utf-8") as fh:
            content = fh.read()

        parsed = yaml.safe_load(content)

        if "openapi" not in parsed:
            errmsg = "Exported YML file missing 'openapi' field"
            raise AssertionError(errmsg)
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
        os.rmdir(temp_dir)

    return


def test_export_explicit_format_overrides_extension():
    """
        Verify that an explicit format parameter overrides the file extension.
    """
    generator = _create_generator_with_endpoint()
    temp_dir = tempfile.mkdtemp()
    # File has .txt extension but we explicitly request JSON
    file_path = os.path.join(temp_dir, "spec.txt")

    try:
        generator.export(file_path, format="json")

        if not os.path.exists(file_path):
            errmsg = f"Expected file to exist at {file_path}"
            raise AssertionError(errmsg)

        with open(file_path, "r", encoding="utf-8") as fh:
            content = fh.read()

        parsed = json.loads(content)

        if "openapi" not in parsed:
            errmsg = "Exported file missing 'openapi' field"
            raise AssertionError(errmsg)
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
        os.rmdir(temp_dir)

    return


def test_export_unknown_extension_raises_error():
    """
        Verify that export raises ValueError for unknown file extensions
        when no explicit format is provided.
    """
    generator = _create_generator_with_endpoint()

    try:
        generator.export("/tmp/spec.txt")
        errmsg = "Expected ValueError for unknown extension"
        raise AssertionError(errmsg)
    except ValueError:
        pass

    return


def test_export_unsupported_format_raises_error():
    """
        Verify that export raises ValueError for unsupported format values.
    """
    generator = _create_generator_with_endpoint()

    try:
        generator.export("/tmp/spec.json", format="xml")
        errmsg = "Expected ValueError for unsupported format"
        raise AssertionError(errmsg)
    except ValueError:
        pass

    return


def test_export_json_content_matches_generate_json():
    """
        Verify that the content written by export matches generate_json output.
    """
    generator = _create_generator_with_endpoint()
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, "spec.json")

    try:
        generator.export(file_path)

        with open(file_path, "r", encoding="utf-8") as fh:
            file_content = fh.read()

        expected = generator.generate_json()

        if file_content != expected:
            errmsg = "File content does not match generate_json() output"
            raise AssertionError(errmsg)
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
        os.rmdir(temp_dir)

    return
