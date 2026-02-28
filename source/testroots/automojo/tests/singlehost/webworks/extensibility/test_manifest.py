"""
    Tests for the ExtensionManifest dataclass.

    This module contains unit tests for the ExtensionManifest including
    dataclass field defaults, YAML/JSON parsing and serialization,
    file loading, and validation.
"""

import json
import os
import random
import string
import tempfile

from pathlib import Path

import yaml

from automojo.webworks.extensibility.exceptions import ExtensionManifestError
from automojo.webworks.extensibility.manifest import ExtensionManifest


# =============================================================================
# Helper Data
# =============================================================================

MINIMAL_MANIFEST_DICT = {
    "name": "test-extension",
    "version": "1.0.0",
    "entry_point": "my_package.extensions.TestExtension",
}

FULL_MANIFEST_DICT = {
    "name": "full-extension",
    "version": "2.1.0",
    "entry_point": "my_package.extensions.FullExtension",
    "description": "A fully specified extension",
    "author": "Test Author",
    "license": "MIT",
    "homepage": "https://example.com/full-extension",
    "dependencies": ["core-ext", "auth-ext"],
    "optional_dependencies": ["logging-ext"],
    "framework_dependencies": ["asgi"],
    "provides_extension_points": ["my.point.a"],
    "consumes_extension_points": ["other.point.b"],
    "config_schema": {"type": "object", "properties": {"timeout": {"type": "integer"}}},
}


# =============================================================================
# Unit Tests for ExtensionManifest Dataclass Fields
# =============================================================================

def test_manifest_stores_required_fields():
    """
        Test that ExtensionManifest stores name, version, and entry_point.
    """
    manifest = ExtensionManifest(
        name="my-ext",
        version="1.0.0",
        entry_point="pkg.MyExt"
    )

    if manifest.name != "my-ext":
        errmsg = "Expected name 'my-ext', got '{}'".format(manifest.name)
        raise AssertionError(errmsg)

    if manifest.version != "1.0.0":
        errmsg = "Expected version '1.0.0', got '{}'".format(manifest.version)
        raise AssertionError(errmsg)

    if manifest.entry_point != "pkg.MyExt":
        errmsg = "Expected entry_point 'pkg.MyExt', got '{}'".format(manifest.entry_point)
        raise AssertionError(errmsg)

    return


def test_manifest_default_description_is_empty():
    """
        Test that ExtensionManifest defaults description to empty string.
    """
    manifest = ExtensionManifest(
        name="my-ext",
        version="1.0.0",
        entry_point="pkg.MyExt"
    )

    if manifest.description != "":
        errmsg = "Expected empty description, got '{}'".format(manifest.description)
        raise AssertionError(errmsg)

    return


def test_manifest_default_author_is_empty():
    """
        Test that ExtensionManifest defaults author to empty string.
    """
    manifest = ExtensionManifest(
        name="my-ext",
        version="1.0.0",
        entry_point="pkg.MyExt"
    )

    if manifest.author != "":
        errmsg = "Expected empty author, got '{}'".format(manifest.author)
        raise AssertionError(errmsg)

    return


def test_manifest_default_dependencies_is_empty_list():
    """
        Test that ExtensionManifest defaults dependencies to empty list.
    """
    manifest = ExtensionManifest(
        name="my-ext",
        version="1.0.0",
        entry_point="pkg.MyExt"
    )

    if len(manifest.dependencies) != 0:
        errmsg = "Expected empty dependencies, got {}".format(manifest.dependencies)
        raise AssertionError(errmsg)

    return


def test_manifest_default_config_schema_is_none():
    """
        Test that ExtensionManifest defaults config_schema to None.
    """
    manifest = ExtensionManifest(
        name="my-ext",
        version="1.0.0",
        entry_point="pkg.MyExt"
    )

    if manifest.config_schema is not None:
        errmsg = "Expected config_schema None, got {}".format(manifest.config_schema)
        raise AssertionError(errmsg)

    return


def test_manifest_stores_all_optional_fields():
    """
        Test that ExtensionManifest stores all optional fields when provided.
    """
    schema = {"type": "object"}
    manifest = ExtensionManifest(
        name="full-ext",
        version="2.0.0",
        entry_point="pkg.FullExt",
        description="A full extension",
        author="Author Name",
        license="MIT",
        homepage="https://example.com",
        dependencies=["dep-a"],
        optional_dependencies=["opt-b"],
        framework_dependencies=["asgi"],
        provides_extension_points=["my.point"],
        consumes_extension_points=["other.point"],
        config_schema=schema,
    )

    if manifest.description != "A full extension":
        errmsg = "Expected description 'A full extension', got '{}'".format(manifest.description)
        raise AssertionError(errmsg)

    if manifest.author != "Author Name":
        errmsg = "Expected author 'Author Name', got '{}'".format(manifest.author)
        raise AssertionError(errmsg)

    if manifest.license != "MIT":
        errmsg = "Expected license 'MIT', got '{}'".format(manifest.license)
        raise AssertionError(errmsg)

    if manifest.homepage != "https://example.com":
        errmsg = "Expected homepage 'https://example.com', got '{}'".format(manifest.homepage)
        raise AssertionError(errmsg)

    if manifest.dependencies != ["dep-a"]:
        errmsg = "Expected dependencies ['dep-a'], got {}".format(manifest.dependencies)
        raise AssertionError(errmsg)

    if manifest.optional_dependencies != ["opt-b"]:
        errmsg = "Expected optional_dependencies ['opt-b'], got {}".format(manifest.optional_dependencies)
        raise AssertionError(errmsg)

    if manifest.framework_dependencies != ["asgi"]:
        errmsg = "Expected framework_dependencies ['asgi'], got {}".format(manifest.framework_dependencies)
        raise AssertionError(errmsg)

    if manifest.provides_extension_points != ["my.point"]:
        errmsg = "Expected provides_extension_points ['my.point'], got {}".format(manifest.provides_extension_points)
        raise AssertionError(errmsg)

    if manifest.consumes_extension_points != ["other.point"]:
        errmsg = "Expected consumes_extension_points ['other.point'], got {}".format(manifest.consumes_extension_points)
        raise AssertionError(errmsg)

    if manifest.config_schema is not schema:
        errmsg = "Expected config_schema to be the same dict instance"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for from_yaml()
# =============================================================================

def test_from_yaml_parses_minimal_manifest():
    """
        Test that from_yaml parses a minimal YAML manifest with required fields.
    """
    content = yaml.dump(MINIMAL_MANIFEST_DICT)
    manifest = ExtensionManifest.from_yaml(content)

    if manifest.name != "test-extension":
        errmsg = "Expected name 'test-extension', got '{}'".format(manifest.name)
        raise AssertionError(errmsg)

    if manifest.version != "1.0.0":
        errmsg = "Expected version '1.0.0', got '{}'".format(manifest.version)
        raise AssertionError(errmsg)

    if manifest.entry_point != "my_package.extensions.TestExtension":
        errmsg = "Expected entry_point 'my_package.extensions.TestExtension', got '{}'".format(manifest.entry_point)
        raise AssertionError(errmsg)

    return


def test_from_yaml_parses_full_manifest():
    """
        Test that from_yaml parses a full YAML manifest with all fields.
    """
    content = yaml.dump(FULL_MANIFEST_DICT)
    manifest = ExtensionManifest.from_yaml(content)

    if manifest.description != "A fully specified extension":
        errmsg = "Expected description 'A fully specified extension', got '{}'".format(manifest.description)
        raise AssertionError(errmsg)

    if manifest.dependencies != ["core-ext", "auth-ext"]:
        errmsg = "Expected dependencies ['core-ext', 'auth-ext'], got {}".format(manifest.dependencies)
        raise AssertionError(errmsg)

    if manifest.config_schema is None:
        errmsg = "Expected config_schema to not be None"
        raise AssertionError(errmsg)

    return


def test_from_yaml_raises_on_missing_required_fields():
    """
        Test that from_yaml raises ExtensionManifestError when required fields are missing.
    """
    content = yaml.dump({"description": "no required fields"})

    caught_error = False
    try:
        ExtensionManifest.from_yaml(content)
    except ExtensionManifestError:
        caught_error = True

    if caught_error is not True:
        errmsg = "Expected ExtensionManifestError for missing required fields"
        raise AssertionError(errmsg)

    return


def test_from_yaml_raises_on_invalid_yaml():
    """
        Test that from_yaml raises ExtensionManifestError on malformed YAML.
    """
    content = "{{invalid: yaml: content"

    caught_error = False
    try:
        ExtensionManifest.from_yaml(content)
    except ExtensionManifestError:
        caught_error = True

    if caught_error is not True:
        errmsg = "Expected ExtensionManifestError for invalid YAML"
        raise AssertionError(errmsg)

    return


def test_from_yaml_raises_on_non_mapping_content():
    """
        Test that from_yaml raises ExtensionManifestError when content is not a mapping.
    """
    content = "- item1\n- item2\n"

    caught_error = False
    try:
        ExtensionManifest.from_yaml(content)
    except ExtensionManifestError:
        caught_error = True

    if caught_error is not True:
        errmsg = "Expected ExtensionManifestError for non-mapping YAML"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for from_json()
# =============================================================================

def test_from_json_parses_minimal_manifest():
    """
        Test that from_json parses a minimal JSON manifest with required fields.
    """
    content = json.dumps(MINIMAL_MANIFEST_DICT)
    manifest = ExtensionManifest.from_json(content)

    if manifest.name != "test-extension":
        errmsg = "Expected name 'test-extension', got '{}'".format(manifest.name)
        raise AssertionError(errmsg)

    if manifest.version != "1.0.0":
        errmsg = "Expected version '1.0.0', got '{}'".format(manifest.version)
        raise AssertionError(errmsg)

    return


def test_from_json_parses_full_manifest():
    """
        Test that from_json parses a full JSON manifest with all fields.
    """
    content = json.dumps(FULL_MANIFEST_DICT)
    manifest = ExtensionManifest.from_json(content)

    if manifest.author != "Test Author":
        errmsg = "Expected author 'Test Author', got '{}'".format(manifest.author)
        raise AssertionError(errmsg)

    if manifest.license != "MIT":
        errmsg = "Expected license 'MIT', got '{}'".format(manifest.license)
        raise AssertionError(errmsg)

    return


def test_from_json_raises_on_missing_required_fields():
    """
        Test that from_json raises ExtensionManifestError when required fields are missing.
    """
    content = json.dumps({"description": "no required fields"})

    caught_error = False
    try:
        ExtensionManifest.from_json(content)
    except ExtensionManifestError:
        caught_error = True

    if caught_error is not True:
        errmsg = "Expected ExtensionManifestError for missing required fields"
        raise AssertionError(errmsg)

    return


def test_from_json_raises_on_invalid_json():
    """
        Test that from_json raises ExtensionManifestError on malformed JSON.
    """
    content = "{not valid json"

    caught_error = False
    try:
        ExtensionManifest.from_json(content)
    except ExtensionManifestError:
        caught_error = True

    if caught_error is not True:
        errmsg = "Expected ExtensionManifestError for invalid JSON"
        raise AssertionError(errmsg)

    return


def test_from_json_raises_on_non_object_content():
    """
        Test that from_json raises ExtensionManifestError when content is not an object.
    """
    content = json.dumps([1, 2, 3])

    caught_error = False
    try:
        ExtensionManifest.from_json(content)
    except ExtensionManifestError:
        caught_error = True

    if caught_error is not True:
        errmsg = "Expected ExtensionManifestError for non-object JSON"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for from_file()
# =============================================================================

def test_from_file_loads_yaml_manifest():
    """
        Test that from_file loads a .yaml manifest file.
    """
    content = yaml.dump(MINIMAL_MANIFEST_DICT)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        manifest = ExtensionManifest.from_file(tmp_path)

        if manifest.name != "test-extension":
            errmsg = "Expected name 'test-extension', got '{}'".format(manifest.name)
            raise AssertionError(errmsg)
    finally:
        tmp_path.unlink()

    return


def test_from_file_loads_yml_manifest():
    """
        Test that from_file loads a .yml manifest file.
    """
    content = yaml.dump(MINIMAL_MANIFEST_DICT)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False, encoding="utf-8") as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        manifest = ExtensionManifest.from_file(tmp_path)

        if manifest.name != "test-extension":
            errmsg = "Expected name 'test-extension', got '{}'".format(manifest.name)
            raise AssertionError(errmsg)
    finally:
        tmp_path.unlink()

    return


def test_from_file_loads_json_manifest():
    """
        Test that from_file loads a .json manifest file.
    """
    content = json.dumps(MINIMAL_MANIFEST_DICT)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        manifest = ExtensionManifest.from_file(tmp_path)

        if manifest.name != "test-extension":
            errmsg = "Expected name 'test-extension', got '{}'".format(manifest.name)
            raise AssertionError(errmsg)
    finally:
        tmp_path.unlink()

    return


def test_from_file_raises_on_nonexistent_file():
    """
        Test that from_file raises ExtensionManifestError for a missing file.
    """
    fake_path = Path("/tmp/nonexistent_manifest_file_12345.yaml")

    caught_error = False
    try:
        ExtensionManifest.from_file(fake_path)
    except ExtensionManifestError:
        caught_error = True

    if caught_error is not True:
        errmsg = "Expected ExtensionManifestError for nonexistent file"
        raise AssertionError(errmsg)

    return


def test_from_file_raises_on_unsupported_extension():
    """
        Test that from_file raises ExtensionManifestError for unsupported file extensions.
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False, encoding="utf-8") as tmp:
        tmp.write("name = 'test'")
        tmp_path = Path(tmp.name)

    try:
        caught_error = False
        try:
            ExtensionManifest.from_file(tmp_path)
        except ExtensionManifestError:
            caught_error = True

        if caught_error is not True:
            errmsg = "Expected ExtensionManifestError for unsupported file extension"
            raise AssertionError(errmsg)
    finally:
        tmp_path.unlink()

    return


# =============================================================================
# Unit Tests for to_yaml() and to_json()
# =============================================================================

def test_to_yaml_produces_parseable_yaml():
    """
        Test that to_yaml produces valid YAML that can be parsed back.
    """
    manifest = ExtensionManifest(
        name="round-trip-ext",
        version="1.0.0",
        entry_point="pkg.RoundTrip"
    )

    yaml_content = manifest.to_yaml()
    parsed = yaml.safe_load(yaml_content)

    if parsed["name"] != "round-trip-ext":
        errmsg = "Expected parsed name 'round-trip-ext', got '{}'".format(parsed["name"])
        raise AssertionError(errmsg)

    return


def test_to_json_produces_parseable_json():
    """
        Test that to_json produces valid JSON that can be parsed back.
    """
    manifest = ExtensionManifest(
        name="round-trip-ext",
        version="1.0.0",
        entry_point="pkg.RoundTrip"
    )

    json_content = manifest.to_json()
    parsed = json.loads(json_content)

    if parsed["name"] != "round-trip-ext":
        errmsg = "Expected parsed name 'round-trip-ext', got '{}'".format(parsed["name"])
        raise AssertionError(errmsg)

    return


def test_yaml_round_trip_preserves_all_fields():
    """
        Test that serializing to YAML and parsing back preserves all fields.
    """
    original = ExtensionManifest(
        name="full-ext",
        version="2.0.0",
        entry_point="pkg.FullExt",
        description="A full extension",
        author="Author",
        license="MIT",
        homepage="https://example.com",
        dependencies=["dep-a", "dep-b"],
        optional_dependencies=["opt-c"],
        framework_dependencies=["asgi"],
        provides_extension_points=["my.point"],
        consumes_extension_points=["other.point"],
        config_schema={"type": "object"},
    )

    yaml_content = original.to_yaml()
    restored = ExtensionManifest.from_yaml(yaml_content)

    if restored.name != original.name:
        errmsg = "Name mismatch after YAML round-trip: '{}' != '{}'".format(restored.name, original.name)
        raise AssertionError(errmsg)

    if restored.version != original.version:
        errmsg = "Version mismatch after YAML round-trip"
        raise AssertionError(errmsg)

    if restored.entry_point != original.entry_point:
        errmsg = "Entry point mismatch after YAML round-trip"
        raise AssertionError(errmsg)

    if restored.description != original.description:
        errmsg = "Description mismatch after YAML round-trip"
        raise AssertionError(errmsg)

    if restored.dependencies != original.dependencies:
        errmsg = "Dependencies mismatch after YAML round-trip"
        raise AssertionError(errmsg)

    if restored.config_schema != original.config_schema:
        errmsg = "Config schema mismatch after YAML round-trip"
        raise AssertionError(errmsg)

    return


def test_json_round_trip_preserves_all_fields():
    """
        Test that serializing to JSON and parsing back preserves all fields.
    """
    original = ExtensionManifest(
        name="full-ext",
        version="2.0.0",
        entry_point="pkg.FullExt",
        description="A full extension",
        author="Author",
        license="MIT",
        homepage="https://example.com",
        dependencies=["dep-a", "dep-b"],
        optional_dependencies=["opt-c"],
        framework_dependencies=["asgi"],
        provides_extension_points=["my.point"],
        consumes_extension_points=["other.point"],
        config_schema={"type": "object"},
    )

    json_content = original.to_json()
    restored = ExtensionManifest.from_json(json_content)

    if restored.name != original.name:
        errmsg = "Name mismatch after JSON round-trip: '{}' != '{}'".format(restored.name, original.name)
        raise AssertionError(errmsg)

    if restored.version != original.version:
        errmsg = "Version mismatch after JSON round-trip"
        raise AssertionError(errmsg)

    if restored.entry_point != original.entry_point:
        errmsg = "Entry point mismatch after JSON round-trip"
        raise AssertionError(errmsg)

    if restored.description != original.description:
        errmsg = "Description mismatch after JSON round-trip"
        raise AssertionError(errmsg)

    if restored.dependencies != original.dependencies:
        errmsg = "Dependencies mismatch after JSON round-trip"
        raise AssertionError(errmsg)

    if restored.config_schema != original.config_schema:
        errmsg = "Config schema mismatch after JSON round-trip"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for validate()
# =============================================================================

def test_validate_returns_empty_for_valid_manifest():
    """
        Test that validate returns an empty list for a valid manifest.
    """
    manifest = ExtensionManifest(
        name="valid-ext",
        version="1.0.0",
        entry_point="pkg.ValidExt"
    )

    errors = manifest.validate()

    if len(errors) != 0:
        errmsg = "Expected no validation errors, got {}".format(errors)
        raise AssertionError(errmsg)

    return


def test_validate_detects_empty_name():
    """
        Test that validate detects an empty name field.
    """
    manifest = ExtensionManifest(
        name="",
        version="1.0.0",
        entry_point="pkg.MyExt"
    )

    errors = manifest.validate()

    found_name_error = False
    for err in errors:
        if "name" in err:
            found_name_error = True

    if found_name_error is not True:
        errmsg = "Expected validation error for empty name, got {}".format(errors)
        raise AssertionError(errmsg)

    return


def test_validate_detects_empty_version():
    """
        Test that validate detects an empty version field.
    """
    manifest = ExtensionManifest(
        name="my-ext",
        version="",
        entry_point="pkg.MyExt"
    )

    errors = manifest.validate()

    found_version_error = False
    for err in errors:
        if "version" in err:
            found_version_error = True

    if found_version_error is not True:
        errmsg = "Expected validation error for empty version, got {}".format(errors)
        raise AssertionError(errmsg)

    return


def test_validate_detects_empty_entry_point():
    """
        Test that validate detects an empty entry_point field.
    """
    manifest = ExtensionManifest(
        name="my-ext",
        version="1.0.0",
        entry_point=""
    )

    errors = manifest.validate()

    found_entry_point_error = False
    for err in errors:
        if "entry_point" in err:
            found_entry_point_error = True

    if found_entry_point_error is not True:
        errmsg = "Expected validation error for empty entry_point, got {}".format(errors)
        raise AssertionError(errmsg)

    return


def test_validate_detects_whitespace_only_fields():
    """
        Test that validate detects fields that contain only whitespace.
    """
    manifest = ExtensionManifest(
        name="   ",
        version="  ",
        entry_point="  "
    )

    errors = manifest.validate()

    if len(errors) != 3:
        errmsg = "Expected 3 validation errors for whitespace-only fields, got {}".format(len(errors))
        raise AssertionError(errmsg)

    return


# =============================================================================
# Random Data Generators for Property Tests
# =============================================================================

def _generate_random_string(min_length: int = 1, max_length: int = 20) -> str:
    """
        Generate a random string of alphanumeric characters.

        :param min_length: Minimum length of the generated string.
        :param max_length: Maximum length of the generated string.

        :returns: A random alphanumeric string.
    """
    length = random.randint(min_length, max_length)
    result = "".join(random.choices(string.ascii_lowercase + string.digits, k=length))
    return result


def _generate_random_version() -> str:
    """
        Generate a random semantic version string.

        :returns: A version string in major.minor.patch format.
    """
    major = random.randint(0, 99)
    minor = random.randint(0, 99)
    patch = random.randint(0, 99)
    result = "{}.{}.{}".format(major, minor, patch)
    return result


def _generate_random_dep_list(max_count: int = 5) -> list:
    """
        Generate a random list of dependency names.

        :param max_count: Maximum number of dependencies to generate.

        :returns: A list of random dependency name strings.
    """
    count = random.randint(0, max_count)
    deps = [_generate_random_string(3, 15) for _ in range(count)]
    return deps


def _generate_random_manifest() -> ExtensionManifest:
    """
        Generate a random ExtensionManifest with random values for all fields.

        Required fields always get non-empty values. Optional fields are
        randomly populated or left at defaults.

        :returns: A randomly populated ExtensionManifest instance.
    """
    name = _generate_random_string(3, 20)
    version = _generate_random_version()
    entry_point = _generate_random_string(3, 15) + "." + _generate_random_string(3, 15)

    description = _generate_random_string(5, 40) if random.random() > 0.3 else ""
    author = _generate_random_string(3, 20) if random.random() > 0.3 else ""
    license_val = _generate_random_string(2, 10) if random.random() > 0.3 else ""
    homepage = "https://" + _generate_random_string(5, 15) + ".com" if random.random() > 0.3 else ""

    dependencies = _generate_random_dep_list(4) if random.random() > 0.3 else []
    optional_dependencies = _generate_random_dep_list(3) if random.random() > 0.3 else []
    framework_dependencies = _generate_random_dep_list(2) if random.random() > 0.3 else []
    provides_extension_points = _generate_random_dep_list(3) if random.random() > 0.3 else []
    consumes_extension_points = _generate_random_dep_list(3) if random.random() > 0.3 else []

    config_schema = None
    if random.random() > 0.3:
        config_schema = {"type": "object", "properties": {}}
        prop_count = random.randint(1, 3)
        for _ in range(prop_count):
            prop_name = _generate_random_string(3, 10)
            prop_type = random.choice(["string", "integer", "boolean"])
            config_schema["properties"][prop_name] = {"type": prop_type}

    manifest = ExtensionManifest(
        name=name,
        version=version,
        entry_point=entry_point,
        description=description,
        author=author,
        license=license_val,
        homepage=homepage,
        dependencies=dependencies,
        optional_dependencies=optional_dependencies,
        framework_dependencies=framework_dependencies,
        provides_extension_points=provides_extension_points,
        consumes_extension_points=consumes_extension_points,
        config_schema=config_schema,
    )

    return manifest


# =============================================================================
# Property-Based Tests
# =============================================================================

# Feature: extensibility, Property 12: Manifest Format Round-Trip
# *For any* valid ExtensionManifest, serializing to YAML and parsing back,
# or serializing to JSON and parsing back, SHALL produce an equivalent manifest.
# **Validates: Requirements 4.1**

def test_property_12_manifest_yaml_round_trip():
    """
        Property 12: Manifest Format Round-Trip (YAML)

        For any valid ExtensionManifest, serializing to YAML via to_yaml()
        and parsing back via from_yaml() SHALL produce an equivalent manifest
        with matching values for all fields.

        **Validates: Requirements 4.1**
    """
    for iteration in range(100):
        original = _generate_random_manifest()

        yaml_content = original.to_yaml()
        restored = ExtensionManifest.from_yaml(yaml_content)

        if restored.name != original.name:
            errmsg = "Iteration {}: name mismatch after YAML round-trip: '{}' != '{}'".format(
                iteration, restored.name, original.name
            )
            raise AssertionError(errmsg)

        if restored.version != original.version:
            errmsg = "Iteration {}: version mismatch after YAML round-trip: '{}' != '{}'".format(
                iteration, restored.version, original.version
            )
            raise AssertionError(errmsg)

        if restored.entry_point != original.entry_point:
            errmsg = "Iteration {}: entry_point mismatch after YAML round-trip: '{}' != '{}'".format(
                iteration, restored.entry_point, original.entry_point
            )
            raise AssertionError(errmsg)

        if restored.description != original.description:
            errmsg = "Iteration {}: description mismatch after YAML round-trip: '{}' != '{}'".format(
                iteration, restored.description, original.description
            )
            raise AssertionError(errmsg)

        if restored.author != original.author:
            errmsg = "Iteration {}: author mismatch after YAML round-trip: '{}' != '{}'".format(
                iteration, restored.author, original.author
            )
            raise AssertionError(errmsg)

        if restored.license != original.license:
            errmsg = "Iteration {}: license mismatch after YAML round-trip: '{}' != '{}'".format(
                iteration, restored.license, original.license
            )
            raise AssertionError(errmsg)

        if restored.homepage != original.homepage:
            errmsg = "Iteration {}: homepage mismatch after YAML round-trip: '{}' != '{}'".format(
                iteration, restored.homepage, original.homepage
            )
            raise AssertionError(errmsg)

        if restored.dependencies != original.dependencies:
            errmsg = "Iteration {}: dependencies mismatch after YAML round-trip: {} != {}".format(
                iteration, restored.dependencies, original.dependencies
            )
            raise AssertionError(errmsg)

        if restored.optional_dependencies != original.optional_dependencies:
            errmsg = "Iteration {}: optional_dependencies mismatch after YAML round-trip: {} != {}".format(
                iteration, restored.optional_dependencies, original.optional_dependencies
            )
            raise AssertionError(errmsg)

        if restored.framework_dependencies != original.framework_dependencies:
            errmsg = "Iteration {}: framework_dependencies mismatch after YAML round-trip: {} != {}".format(
                iteration, restored.framework_dependencies, original.framework_dependencies
            )
            raise AssertionError(errmsg)

        if restored.provides_extension_points != original.provides_extension_points:
            errmsg = "Iteration {}: provides_extension_points mismatch after YAML round-trip: {} != {}".format(
                iteration, restored.provides_extension_points, original.provides_extension_points
            )
            raise AssertionError(errmsg)

        if restored.consumes_extension_points != original.consumes_extension_points:
            errmsg = "Iteration {}: consumes_extension_points mismatch after YAML round-trip: {} != {}".format(
                iteration, restored.consumes_extension_points, original.consumes_extension_points
            )
            raise AssertionError(errmsg)

        if restored.config_schema != original.config_schema:
            errmsg = "Iteration {}: config_schema mismatch after YAML round-trip: {} != {}".format(
                iteration, restored.config_schema, original.config_schema
            )
            raise AssertionError(errmsg)

    return


def test_property_12_manifest_json_round_trip():
    """
        Property 12: Manifest Format Round-Trip (JSON)

        For any valid ExtensionManifest, serializing to JSON via to_json()
        and parsing back via from_json() SHALL produce an equivalent manifest
        with matching values for all fields.

        **Validates: Requirements 4.1**
    """
    for iteration in range(100):
        original = _generate_random_manifest()

        json_content = original.to_json()
        restored = ExtensionManifest.from_json(json_content)

        if restored.name != original.name:
            errmsg = "Iteration {}: name mismatch after JSON round-trip: '{}' != '{}'".format(
                iteration, restored.name, original.name
            )
            raise AssertionError(errmsg)

        if restored.version != original.version:
            errmsg = "Iteration {}: version mismatch after JSON round-trip: '{}' != '{}'".format(
                iteration, restored.version, original.version
            )
            raise AssertionError(errmsg)

        if restored.entry_point != original.entry_point:
            errmsg = "Iteration {}: entry_point mismatch after JSON round-trip: '{}' != '{}'".format(
                iteration, restored.entry_point, original.entry_point
            )
            raise AssertionError(errmsg)

        if restored.description != original.description:
            errmsg = "Iteration {}: description mismatch after JSON round-trip: '{}' != '{}'".format(
                iteration, restored.description, original.description
            )
            raise AssertionError(errmsg)

        if restored.author != original.author:
            errmsg = "Iteration {}: author mismatch after JSON round-trip: '{}' != '{}'".format(
                iteration, restored.author, original.author
            )
            raise AssertionError(errmsg)

        if restored.license != original.license:
            errmsg = "Iteration {}: license mismatch after JSON round-trip: '{}' != '{}'".format(
                iteration, restored.license, original.license
            )
            raise AssertionError(errmsg)

        if restored.homepage != original.homepage:
            errmsg = "Iteration {}: homepage mismatch after JSON round-trip: '{}' != '{}'".format(
                iteration, restored.homepage, original.homepage
            )
            raise AssertionError(errmsg)

        if restored.dependencies != original.dependencies:
            errmsg = "Iteration {}: dependencies mismatch after JSON round-trip: {} != {}".format(
                iteration, restored.dependencies, original.dependencies
            )
            raise AssertionError(errmsg)

        if restored.optional_dependencies != original.optional_dependencies:
            errmsg = "Iteration {}: optional_dependencies mismatch after JSON round-trip: {} != {}".format(
                iteration, restored.optional_dependencies, original.optional_dependencies
            )
            raise AssertionError(errmsg)

        if restored.framework_dependencies != original.framework_dependencies:
            errmsg = "Iteration {}: framework_dependencies mismatch after JSON round-trip: {} != {}".format(
                iteration, restored.framework_dependencies, original.framework_dependencies
            )
            raise AssertionError(errmsg)

        if restored.provides_extension_points != original.provides_extension_points:
            errmsg = "Iteration {}: provides_extension_points mismatch after JSON round-trip: {} != {}".format(
                iteration, restored.provides_extension_points, original.provides_extension_points
            )
            raise AssertionError(errmsg)

        if restored.consumes_extension_points != original.consumes_extension_points:
            errmsg = "Iteration {}: consumes_extension_points mismatch after JSON round-trip: {} != {}".format(
                iteration, restored.consumes_extension_points, original.consumes_extension_points
            )
            raise AssertionError(errmsg)

        if restored.config_schema != original.config_schema:
            errmsg = "Iteration {}: config_schema mismatch after JSON round-trip: {} != {}".format(
                iteration, restored.config_schema, original.config_schema
            )
            raise AssertionError(errmsg)

    return


# Feature: extensibility, Property 13: Manifest Required Fields Validation
# *For any* manifest missing required fields (name, version, entry_point),
# parsing SHALL raise ExtensionManifestError.
# **Validates: Requirements 4.2, 4.9, 4.10**

def test_property_13_manifest_missing_required_fields_yaml():
    """
        Property 13: Manifest Required Fields Validation (YAML parsing)

        For any manifest dict missing one or more required fields
        (name, version, entry_point), parsing via from_yaml() SHALL
        raise ExtensionManifestError.

        **Validates: Requirements 4.2, 4.9, 4.10**
    """
    required_fields = ["name", "version", "entry_point"]

    for iteration in range(100):
        # Build a complete manifest dict
        full_dict = {
            "name": _generate_random_string(3, 15),
            "version": _generate_random_version(),
            "entry_point": _generate_random_string(3, 15) + "." + _generate_random_string(3, 15),
            "description": _generate_random_string(5, 30),
        }

        # Choose a random non-empty subset of required fields to remove
        num_to_remove = random.randint(1, len(required_fields))
        fields_to_remove = random.sample(required_fields, num_to_remove)

        for field_name in fields_to_remove:
            del full_dict[field_name]

        yaml_content = yaml.dump(full_dict)

        caught_error = False
        try:
            ExtensionManifest.from_yaml(yaml_content)
        except ExtensionManifestError:
            caught_error = True

        if caught_error is not True:
            errmsg = "Iteration {}: Expected ExtensionManifestError when missing fields {} from YAML".format(
                iteration, fields_to_remove
            )
            raise AssertionError(errmsg)

    return


def test_property_13_manifest_missing_required_fields_json():
    """
        Property 13: Manifest Required Fields Validation (JSON parsing)

        For any manifest dict missing one or more required fields
        (name, version, entry_point), parsing via from_json() SHALL
        raise ExtensionManifestError.

        **Validates: Requirements 4.2, 4.9, 4.10**
    """
    required_fields = ["name", "version", "entry_point"]

    for iteration in range(100):
        # Build a complete manifest dict
        full_dict = {
            "name": _generate_random_string(3, 15),
            "version": _generate_random_version(),
            "entry_point": _generate_random_string(3, 15) + "." + _generate_random_string(3, 15),
            "description": _generate_random_string(5, 30),
        }

        # Choose a random non-empty subset of required fields to remove
        num_to_remove = random.randint(1, len(required_fields))
        fields_to_remove = random.sample(required_fields, num_to_remove)

        for field_name in fields_to_remove:
            del full_dict[field_name]

        json_content = json.dumps(full_dict)

        caught_error = False
        try:
            ExtensionManifest.from_json(json_content)
        except ExtensionManifestError:
            caught_error = True

        if caught_error is not True:
            errmsg = "Iteration {}: Expected ExtensionManifestError when missing fields {} from JSON".format(
                iteration, fields_to_remove
            )
            raise AssertionError(errmsg)

    return


def test_property_13_manifest_validate_detects_empty_required_fields():
    """
        Property 13: Manifest Required Fields Validation (validate method)

        For any manifest with empty required fields (name, version, entry_point),
        calling validate() SHALL return errors for each empty required field.

        **Validates: Requirements 4.2, 4.9, 4.10**
    """
    required_fields = ["name", "version", "entry_point"]

    for iteration in range(100):
        # Choose a random non-empty subset of required fields to leave empty
        num_empty = random.randint(1, len(required_fields))
        fields_to_empty = random.sample(required_fields, num_empty)

        name = "" if "name" in fields_to_empty else _generate_random_string(3, 15)
        version = "" if "version" in fields_to_empty else _generate_random_version()
        entry_point = "" if "entry_point" in fields_to_empty else _generate_random_string(3, 15) + ".Ext"

        manifest = ExtensionManifest(
            name=name,
            version=version,
            entry_point=entry_point,
        )

        errors = manifest.validate()

        if len(errors) != num_empty:
            errmsg = "Iteration {}: Expected {} validation errors for empty fields {}, got {} errors: {}".format(
                iteration, num_empty, fields_to_empty, len(errors), errors
            )
            raise AssertionError(errmsg)

        for field_name in fields_to_empty:
            found = False
            for err in errors:
                if field_name in err:
                    found = True
            if found is not True:
                errmsg = "Iteration {}: Expected validation error mentioning '{}', got {}".format(
                    iteration, field_name, errors
                )
                raise AssertionError(errmsg)

    return
