"""
    Tests for the ExtensionLoader class.

    This module contains unit tests and property-based tests for the
    ExtensionLoader class including path discovery, entry point discovery,
    manifest loading, extension loading, pattern filtering, and lazy
    loading support.
"""

import json
import logging
import os
import random
import shutil
import string
import tempfile

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from automojo.webworks.extensibility.exceptions import ExtensionManifestError
from automojo.webworks.extensibility.extension import Extension
from automojo.webworks.extensibility.loader import ExtensionLoader
from automojo.webworks.extensibility.manifest import ExtensionManifest
from automojo.webworks.extensibility.registry import ExtensionRegistry


# =============================================================================
# Test Helpers
# =============================================================================

class _FakeAppContext:
    """
        A fake application context for testing purposes.

        Provides the duck-typed interface that ExtensionRegistry
        and ExtensionContext expect from the application context.
    """

    def __init__(
        self,
        config: Optional[Any] = None,
        endpoint_registry: Optional[Any] = None,
        url_node_map: Optional[Any] = None,
        middleware: Optional[List[Any]] = None,
        extension_registry: Optional[Any] = None
    ):
        self.config = config if config is not None else {}
        self.endpoint_registry = endpoint_registry
        self.url_node_map = url_node_map
        self.middleware = middleware if middleware is not None else []
        self.extension_registry = extension_registry
        self._loggers: Dict[str, logging.Logger] = {}
        return

    def get_logger(self, name: str) -> logging.Logger:
        """
            Get a logger by name.

            :param name: The logger name.

            :returns: A Logger instance.
        """
        if name not in self._loggers:
            self._loggers[name] = logging.getLogger(name)

        rtnval = self._loggers[name]
        return rtnval


class _TestExtension(Extension):
    """
        A concrete extension for testing load_extension().
    """

    name = "test-loader-ext"
    version = "1.0.0"
    description = "Test extension for loader"
    dependencies = []
    optional_dependencies = []


def _create_temp_dir() -> str:
    """
        Create a temporary directory for test use.

        :returns: The path to the created temporary directory.
    """
    temp_dir = tempfile.mkdtemp(prefix="ext_loader_test_")
    return temp_dir


def _write_yaml_manifest(directory: str, manifest_data: Dict[str, Any], filename: str = "extension.yaml") -> Path:
    """
        Write a YAML manifest file to the given directory.

        :param directory: The directory to write the manifest in.
        :param manifest_data: The manifest data dictionary.
        :param filename: The manifest filename.

        :returns: The path to the written manifest file.
    """
    file_path = Path(directory) / filename
    content = yaml.dump(manifest_data, default_flow_style=False, sort_keys=False)
    file_path.write_text(content, encoding="utf-8")
    return file_path


def _write_json_manifest(directory: str, manifest_data: Dict[str, Any], filename: str = "extension.json") -> Path:
    """
        Write a JSON manifest file to the given directory.

        :param directory: The directory to write the manifest in.
        :param manifest_data: The manifest data dictionary.
        :param filename: The manifest filename.

        :returns: The path to the written manifest file.
    """
    file_path = Path(directory) / filename
    content = json.dumps(manifest_data, indent=2)
    file_path.write_text(content, encoding="utf-8")
    return file_path


def _make_valid_manifest_data(name: str = "test-ext", version: str = "1.0.0") -> Dict[str, Any]:
    """
        Create a valid manifest data dictionary.

        :param name: The extension name.
        :param version: The extension version.

        :returns: A dictionary with valid manifest fields.
    """
    data = {
        "name": name,
        "version": version,
        "entry_point": "some.module.SomeClass",
    }
    return data


def _generate_random_string(min_length: int = 3, max_length: int = 15) -> str:
    """
        Generate a random string of lowercase alphanumeric characters.

        :param min_length: Minimum length of the generated string.
        :param max_length: Maximum length of the generated string.

        :returns: A random alphanumeric string.
    """
    length = random.randint(min_length, max_length)
    result = "".join(random.choices(string.ascii_lowercase + string.digits, k=length))
    return result


def _create_named_extension(name: str) -> Extension:
    """
        Create a concrete Extension instance with the given name.

        :param name: The extension name.

        :returns: An Extension instance.
    """
    ext_cls = type(
        "DynExtension_{}".format(name),
        (Extension,),
        {
            "name": name,
            "version": "1.0.0",
            "description": "Dynamic extension {}".format(name),
            "dependencies": [],
            "optional_dependencies": [],
        }
    )

    instance = ext_cls()
    return instance


# =============================================================================
# Unit Tests for ExtensionLoader __init__
# =============================================================================

def test_loader_init_creates_empty_lazy_dict():
    """
        Test that a new loader has an empty lazy extensions dict.
    """
    app_ctx = _FakeAppContext()
    registry = ExtensionRegistry(app_context=app_ctx)
    loader = ExtensionLoader(registry=registry)

    if len(loader._lazy_extensions) != 0:
        errmsg = "Expected empty _lazy_extensions dict, got {} items".format(
            len(loader._lazy_extensions)
        )
        raise AssertionError(errmsg)

    return


def test_loader_init_stores_registry_reference():
    """
        Test that the loader stores a reference to the registry.
    """
    app_ctx = _FakeAppContext()
    registry = ExtensionRegistry(app_context=app_ctx)
    loader = ExtensionLoader(registry=registry)

    if loader._registry is not registry:
        errmsg = "Expected loader._registry to be the same registry instance"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for discover_from_paths()
# =============================================================================

def test_discover_from_paths_finds_yaml_manifest():
    """
        Test that discover_from_paths() finds a YAML manifest in a directory.
    """
    temp_dir = _create_temp_dir()

    try:
        manifest_data = _make_valid_manifest_data(name="yaml-ext")
        _write_yaml_manifest(temp_dir, manifest_data)

        app_ctx = _FakeAppContext()
        registry = ExtensionRegistry(app_context=app_ctx)
        loader = ExtensionLoader(registry=registry)

        results = loader.discover_from_paths([Path(temp_dir)])

        if len(results) != 1:
            errmsg = "Expected 1 manifest, got {}".format(len(results))
            raise AssertionError(errmsg)

        if results[0].name != "yaml-ext":
            errmsg = "Expected manifest name 'yaml-ext', got '{}'".format(results[0].name)
            raise AssertionError(errmsg)

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    return


def test_discover_from_paths_finds_json_manifest():
    """
        Test that discover_from_paths() finds a JSON manifest in a directory.
    """
    temp_dir = _create_temp_dir()

    try:
        manifest_data = _make_valid_manifest_data(name="json-ext")
        _write_json_manifest(temp_dir, manifest_data)

        app_ctx = _FakeAppContext()
        registry = ExtensionRegistry(app_context=app_ctx)
        loader = ExtensionLoader(registry=registry)

        results = loader.discover_from_paths([Path(temp_dir)])

        if len(results) != 1:
            errmsg = "Expected 1 manifest, got {}".format(len(results))
            raise AssertionError(errmsg)

        if results[0].name != "json-ext":
            errmsg = "Expected manifest name 'json-ext', got '{}'".format(results[0].name)
            raise AssertionError(errmsg)

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    return


def test_discover_from_paths_finds_manifests_in_subdirectories():
    """
        Test that discover_from_paths() finds manifests in subdirectories.
    """
    temp_dir = _create_temp_dir()

    try:
        sub_dir = os.path.join(temp_dir, "my-extension")
        os.makedirs(sub_dir)

        manifest_data = _make_valid_manifest_data(name="sub-ext")
        _write_yaml_manifest(sub_dir, manifest_data)

        app_ctx = _FakeAppContext()
        registry = ExtensionRegistry(app_context=app_ctx)
        loader = ExtensionLoader(registry=registry)

        results = loader.discover_from_paths([Path(temp_dir)])

        if len(results) != 1:
            errmsg = "Expected 1 manifest, got {}".format(len(results))
            raise AssertionError(errmsg)

        if results[0].name != "sub-ext":
            errmsg = "Expected manifest name 'sub-ext', got '{}'".format(results[0].name)
            raise AssertionError(errmsg)

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    return


def test_discover_from_paths_skips_invalid_manifests():
    """
        Test that discover_from_paths() skips manifests with missing required fields.
    """
    temp_dir = _create_temp_dir()

    try:
        # Write an invalid manifest (missing entry_point)
        invalid_data = {"name": "bad-ext", "version": "1.0.0"}
        _write_yaml_manifest(temp_dir, invalid_data)

        app_ctx = _FakeAppContext()
        registry = ExtensionRegistry(app_context=app_ctx)
        loader = ExtensionLoader(registry=registry)

        results = loader.discover_from_paths([Path(temp_dir)])

        if len(results) != 0:
            errmsg = "Expected 0 manifests for invalid manifest, got {}".format(len(results))
            raise AssertionError(errmsg)

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    return


def test_discover_from_paths_skips_nonexistent_paths():
    """
        Test that discover_from_paths() skips paths that do not exist.
    """
    app_ctx = _FakeAppContext()
    registry = ExtensionRegistry(app_context=app_ctx)
    loader = ExtensionLoader(registry=registry)

    results = loader.discover_from_paths([Path("/nonexistent/path/12345")])

    if len(results) != 0:
        errmsg = "Expected 0 manifests for nonexistent path, got {}".format(len(results))
        raise AssertionError(errmsg)

    return


def test_discover_from_paths_returns_empty_for_empty_directory():
    """
        Test that discover_from_paths() returns empty list for directory with no manifests.
    """
    temp_dir = _create_temp_dir()

    try:
        app_ctx = _FakeAppContext()
        registry = ExtensionRegistry(app_context=app_ctx)
        loader = ExtensionLoader(registry=registry)

        results = loader.discover_from_paths([Path(temp_dir)])

        if len(results) != 0:
            errmsg = "Expected 0 manifests for empty directory, got {}".format(len(results))
            raise AssertionError(errmsg)

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    return


# =============================================================================
# Unit Tests for load_manifest()
# =============================================================================

def test_load_manifest_loads_valid_yaml():
    """
        Test that load_manifest() loads a valid YAML manifest.
    """
    temp_dir = _create_temp_dir()

    try:
        manifest_data = _make_valid_manifest_data(name="load-test")
        manifest_path = _write_yaml_manifest(temp_dir, manifest_data)

        app_ctx = _FakeAppContext()
        registry = ExtensionRegistry(app_context=app_ctx)
        loader = ExtensionLoader(registry=registry)

        manifest = loader.load_manifest(manifest_path)

        if manifest.name != "load-test":
            errmsg = "Expected manifest name 'load-test', got '{}'".format(manifest.name)
            raise AssertionError(errmsg)

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    return


def test_load_manifest_raises_for_invalid():
    """
        Test that load_manifest() raises ExtensionManifestError for invalid manifest.
    """
    temp_dir = _create_temp_dir()

    try:
        # Missing entry_point
        invalid_data = {"name": "bad", "version": "1.0.0"}
        manifest_path = _write_yaml_manifest(temp_dir, invalid_data)

        app_ctx = _FakeAppContext()
        registry = ExtensionRegistry(app_context=app_ctx)
        loader = ExtensionLoader(registry=registry)

        raised = False
        try:
            loader.load_manifest(manifest_path)
        except ExtensionManifestError:
            raised = True

        if raised is not True:
            errmsg = "Expected ExtensionManifestError for invalid manifest"
            raise AssertionError(errmsg)

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    return


def test_load_manifest_raises_for_nonexistent_file():
    """
        Test that load_manifest() raises ExtensionManifestError for missing file.
    """
    app_ctx = _FakeAppContext()
    registry = ExtensionRegistry(app_context=app_ctx)
    loader = ExtensionLoader(registry=registry)

    raised = False
    try:
        loader.load_manifest(Path("/nonexistent/manifest.yaml"))
    except ExtensionManifestError:
        raised = True

    if raised is not True:
        errmsg = "Expected ExtensionManifestError for nonexistent file"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for load_extension()
# =============================================================================

def test_load_extension_loads_valid_extension():
    """
        Test that load_extension() imports and instantiates an extension class.
    """
    app_ctx = _FakeAppContext()
    registry = ExtensionRegistry(app_context=app_ctx)
    loader = ExtensionLoader(registry=registry)

    manifest = ExtensionManifest(
        name="test-loader-ext",
        version="1.0.0",
        entry_point="automojo.tests.singlehost.webworks.extensibility.test_loader._TestExtension",
    )

    ext = loader.load_extension(manifest)

    if ext.name != "test-loader-ext":
        errmsg = "Expected extension name 'test-loader-ext', got '{}'".format(ext.name)
        raise AssertionError(errmsg)

    return


def test_load_extension_raises_for_bad_entry_point_format():
    """
        Test that load_extension() raises for entry_point without a dot.
    """
    app_ctx = _FakeAppContext()
    registry = ExtensionRegistry(app_context=app_ctx)
    loader = ExtensionLoader(registry=registry)

    manifest = ExtensionManifest(
        name="bad-ep",
        version="1.0.0",
        entry_point="NoDotsHere",
    )

    raised = False
    try:
        loader.load_extension(manifest)
    except ExtensionManifestError:
        raised = True

    if raised is not True:
        errmsg = "Expected ExtensionManifestError for bad entry_point format"
        raise AssertionError(errmsg)

    return


def test_load_extension_raises_for_missing_module():
    """
        Test that load_extension() raises for a non-importable module.
    """
    app_ctx = _FakeAppContext()
    registry = ExtensionRegistry(app_context=app_ctx)
    loader = ExtensionLoader(registry=registry)

    manifest = ExtensionManifest(
        name="missing-mod",
        version="1.0.0",
        entry_point="nonexistent.module.SomeClass",
    )

    raised = False
    try:
        loader.load_extension(manifest)
    except ExtensionManifestError:
        raised = True

    if raised is not True:
        errmsg = "Expected ExtensionManifestError for missing module"
        raise AssertionError(errmsg)

    return


def test_load_extension_raises_for_missing_class():
    """
        Test that load_extension() raises when class is not found in module.
    """
    app_ctx = _FakeAppContext()
    registry = ExtensionRegistry(app_context=app_ctx)
    loader = ExtensionLoader(registry=registry)

    manifest = ExtensionManifest(
        name="missing-cls",
        version="1.0.0",
        entry_point="automojo.tests.singlehost.webworks.extensibility.test_loader.NonExistentClass",
    )

    raised = False
    try:
        loader.load_extension(manifest)
    except ExtensionManifestError:
        raised = True

    if raised is not True:
        errmsg = "Expected ExtensionManifestError for missing class"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for filter_by_pattern()
# =============================================================================

def test_filter_by_pattern_matches_exact_name():
    """
        Test that filter_by_pattern() matches an exact name.
    """
    app_ctx = _FakeAppContext()
    registry = ExtensionRegistry(app_context=app_ctx)
    loader = ExtensionLoader(registry=registry)

    manifests = [
        ExtensionManifest(name="auth-ext", version="1.0.0", entry_point="a.b.C"),
        ExtensionManifest(name="db-ext", version="1.0.0", entry_point="d.e.F"),
    ]

    filtered = loader.filter_by_pattern(manifests, "auth-ext")

    if len(filtered) != 1:
        errmsg = "Expected 1 match, got {}".format(len(filtered))
        raise AssertionError(errmsg)

    if filtered[0].name != "auth-ext":
        errmsg = "Expected 'auth-ext', got '{}'".format(filtered[0].name)
        raise AssertionError(errmsg)

    return


def test_filter_by_pattern_matches_glob():
    """
        Test that filter_by_pattern() matches using glob wildcards.
    """
    app_ctx = _FakeAppContext()
    registry = ExtensionRegistry(app_context=app_ctx)
    loader = ExtensionLoader(registry=registry)

    manifests = [
        ExtensionManifest(name="auth-provider", version="1.0.0", entry_point="a.b.C"),
        ExtensionManifest(name="auth-validator", version="1.0.0", entry_point="d.e.F"),
        ExtensionManifest(name="db-connector", version="1.0.0", entry_point="g.h.I"),
    ]

    filtered = loader.filter_by_pattern(manifests, "auth-*")

    if len(filtered) != 2:
        errmsg = "Expected 2 matches for 'auth-*', got {}".format(len(filtered))
        raise AssertionError(errmsg)

    return


def test_filter_by_pattern_returns_empty_for_no_match():
    """
        Test that filter_by_pattern() returns empty list when nothing matches.
    """
    app_ctx = _FakeAppContext()
    registry = ExtensionRegistry(app_context=app_ctx)
    loader = ExtensionLoader(registry=registry)

    manifests = [
        ExtensionManifest(name="auth-ext", version="1.0.0", entry_point="a.b.C"),
    ]

    filtered = loader.filter_by_pattern(manifests, "db-*")

    if len(filtered) != 0:
        errmsg = "Expected 0 matches, got {}".format(len(filtered))
        raise AssertionError(errmsg)

    return


def test_filter_by_pattern_star_matches_all():
    """
        Test that filter_by_pattern() with '*' matches all manifests.
    """
    app_ctx = _FakeAppContext()
    registry = ExtensionRegistry(app_context=app_ctx)
    loader = ExtensionLoader(registry=registry)

    manifests = [
        ExtensionManifest(name="ext-a", version="1.0.0", entry_point="a.b.C"),
        ExtensionManifest(name="ext-b", version="1.0.0", entry_point="d.e.F"),
        ExtensionManifest(name="ext-c", version="1.0.0", entry_point="g.h.I"),
    ]

    filtered = loader.filter_by_pattern(manifests, "*")

    if len(filtered) != 3:
        errmsg = "Expected 3 matches for '*', got {}".format(len(filtered))
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for lazy loading
# =============================================================================

def test_lazy_register_and_get():
    """
        Test that register_lazy() and get_lazy() work together.
    """
    app_ctx = _FakeAppContext()
    registry = ExtensionRegistry(app_context=app_ctx)
    loader = ExtensionLoader(registry=registry)

    factory_called = [False]

    def factory() -> Extension:
        factory_called[0] = True
        ext = _create_named_extension("lazy-ext")
        return ext

    loader.register_lazy("lazy-ext", factory)

    if loader.has_lazy("lazy-ext") is not True:
        errmsg = "Expected has_lazy('lazy-ext') to be True"
        raise AssertionError(errmsg)

    # Factory should not be called yet
    if factory_called[0] is True:
        errmsg = "Expected factory not to be called before get_lazy()"
        raise AssertionError(errmsg)

    ext = loader.get_lazy("lazy-ext")

    if factory_called[0] is not True:
        errmsg = "Expected factory to be called after get_lazy()"
        raise AssertionError(errmsg)

    if ext is None:
        errmsg = "Expected get_lazy() to return an extension instance"
        raise AssertionError(errmsg)

    if ext.name != "lazy-ext":
        errmsg = "Expected extension name 'lazy-ext', got '{}'".format(ext.name)
        raise AssertionError(errmsg)

    # After loading, it should be in the registry
    from_registry = registry.get("lazy-ext")
    if from_registry is not ext:
        errmsg = "Expected extension to be registered in the registry after lazy load"
        raise AssertionError(errmsg)

    # Lazy dict should no longer have the entry
    if loader.has_lazy("lazy-ext") is True:
        errmsg = "Expected has_lazy('lazy-ext') to be False after loading"
        raise AssertionError(errmsg)

    return


def test_lazy_get_returns_none_for_unknown():
    """
        Test that get_lazy() returns None for an unknown extension.
    """
    app_ctx = _FakeAppContext()
    registry = ExtensionRegistry(app_context=app_ctx)
    loader = ExtensionLoader(registry=registry)

    result = loader.get_lazy("nonexistent")

    if result is not None:
        errmsg = "Expected get_lazy() to return None for unknown extension"
        raise AssertionError(errmsg)

    return


def test_lazy_get_returns_existing_from_registry():
    """
        Test that get_lazy() returns an already-registered extension from the registry.
    """
    app_ctx = _FakeAppContext()
    registry = ExtensionRegistry(app_context=app_ctx)
    loader = ExtensionLoader(registry=registry)

    ext = _create_named_extension("already-loaded")
    registry.register(ext)

    result = loader.get_lazy("already-loaded")

    if result is not ext:
        errmsg = "Expected get_lazy() to return the already-registered extension"
        raise AssertionError(errmsg)

    return


def test_lazy_get_handles_factory_error():
    """
        Test that get_lazy() returns None when the factory raises an error.
    """
    app_ctx = _FakeAppContext()
    registry = ExtensionRegistry(app_context=app_ctx)
    loader = ExtensionLoader(registry=registry)

    def bad_factory() -> Extension:
        raise RuntimeError("Factory failed")

    loader.register_lazy("bad-ext", bad_factory)

    result = loader.get_lazy("bad-ext")

    if result is not None:
        errmsg = "Expected get_lazy() to return None when factory fails"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Property-Based Tests
# =============================================================================

# Feature: extensibility, Property 11: Extension Discovery from Paths
# *For any* directory containing valid extension manifests, calling
# discover_from_paths() with that path SHALL find all valid extensions
# from that directory.
# **Validates: Requirements 3.1, 3.3**

def test_property_11_extension_discovery_from_paths():
    """
        Property 11: Extension Discovery from Paths

        For any directory containing valid extension manifests,
        calling discover_from_paths() with that path SHALL find
        all valid extensions from that directory.

        **Validates: Requirements 3.1, 3.3**
    """
    for iteration in range(100):
        temp_dir = _create_temp_dir()

        try:
            # Generate a random number of extensions (1-5)
            ext_count = random.randint(1, 5)
            expected_names = set()

            for ext_idx in range(ext_count):
                ext_name = "ext-{}-{}".format(
                    _generate_random_string(3, 10),
                    ext_idx
                )
                expected_names.add(ext_name)

                # Create a subdirectory for each extension
                sub_dir = os.path.join(temp_dir, ext_name)
                os.makedirs(sub_dir)

                manifest_data = _make_valid_manifest_data(
                    name=ext_name,
                    version="{}.{}.{}".format(
                        random.randint(0, 9),
                        random.randint(0, 9),
                        random.randint(0, 9)
                    )
                )

                # Randomly choose YAML or JSON format
                use_json = random.choice([True, False])
                if use_json:
                    _write_json_manifest(sub_dir, manifest_data)
                else:
                    _write_yaml_manifest(sub_dir, manifest_data)

            app_ctx = _FakeAppContext()
            registry = ExtensionRegistry(app_context=app_ctx)
            loader = ExtensionLoader(registry=registry)

            results = loader.discover_from_paths([Path(temp_dir)])

            discovered_names = set()
            for manifest in results:
                discovered_names.add(manifest.name)

            # Verify all expected extensions were discovered
            if discovered_names != expected_names:
                missing = expected_names - discovered_names
                extra = discovered_names - expected_names
                errmsg_lines = [
                    "Iteration {}: Discovery mismatch".format(iteration),
                ]
                if len(missing) > 0:
                    errmsg_lines.append("  Missing: {}".format(missing))
                if len(extra) > 0:
                    errmsg_lines.append("  Extra: {}".format(extra))
                errmsg = os.linesep.join(errmsg_lines)
                raise AssertionError(errmsg)

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    return
