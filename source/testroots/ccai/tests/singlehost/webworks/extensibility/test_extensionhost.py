"""
    Tests for the ExtensionHost class.

    This module contains unit tests for the extension machinery an
    application owns: adding and loading extensions, starting them, firing
    the application lifecycle hooks once each, and stopping them.
"""

import json
import os
import shutil
import tempfile

from pathlib import Path
from typing import Any, List

from ccai.errors.exceptions import ConfigurationError, SemanticError

from ccai.webworks.endpoints.registry import EndpointRegistry
from ccai.webworks.extensibility.applicationcontext import ApplicationContext
from ccai.webworks.extensibility.datastructures import ExtensionState
from ccai.webworks.extensibility.extension import Extension
from ccai.webworks.extensibility.extensionhost import ExtensionHost
from ccai.webworks.extensibility.extensionsettings import ExtensionSettings
from ccai.webworks.routing.middlewareregistry import MiddlewareRegistry


_THIS_MODULE = "ccai.tests.singlehost.webworks.extensibility.test_extensionhost"


# =============================================================================
# Extensions used by the tests
# =============================================================================

class _HostEvents:
    """The events the test extensions record, in order."""
    log: List[str] = []


class _RecordingExtension(Extension):
    """An extension that records its lifecycle and its application hooks."""

    name = "recording"

    def initialize(self, context: Any) -> None:
        super().initialize(context)
        _HostEvents.log.append("{}.initialize".format(self.name))
        for hook_name in ("on_config_loaded", "on_app_init", "on_routes_registered", "on_app_ready", "on_app_shutdown"):
            context.register_hook(hook_name, self._make_recorder(hook_name))
        return

    def activate(self) -> None:
        super().activate()
        _HostEvents.log.append("{}.activate".format(self.name))
        return

    def shutdown(self) -> None:
        _HostEvents.log.append("{}.shutdown".format(self.name))
        return

    def _make_recorder(self, hook_name: str):
        def record(app_context: Any) -> None:
            _HostEvents.log.append("{}.{}".format(self.name, hook_name))
            return
        return record


class _ConfiguredExtension(_RecordingExtension):
    """An extension loaded from configuration by import string."""

    name = "configured"


class _NeedsMissingDependency(Extension):
    """An extension whose required dependency is not registered."""

    name = "needs-missing"
    dependencies = ["not-registered"]


class _ReservedName(Extension):
    """An extension named like a setting of the extensions section."""

    name = "paths"


class _Unnamed(Extension):
    """An extension without a name."""


# =============================================================================
# Helpers
# =============================================================================

def _make_host() -> ExtensionHost:
    """
        Create an ExtensionHost on a fresh application context and clear the
        event log.

        :returns: The host.
    """
    _HostEvents.log = []
    app_context = ApplicationContext(
        logger_name="hostapp",
        endpoint_registry=EndpointRegistry(),
        middleware_registry=MiddlewareRegistry()
    )
    rtnval = ExtensionHost(app_context=app_context)
    return rtnval


def _expect_error(error_type: Any, action: Any) -> Any:
    """
        Run an action that must raise.

        :param error_type: The expected exception type.
        :param action: A callable taking no arguments.

        :returns: The exception raised.
    """
    caught = None
    try:
        action()
    except error_type as err:
        caught = err

    if caught is None:
        raise AssertionError("Expected {}".format(error_type.__name__))

    return caught


# =============================================================================
# Adding and loading extensions
# =============================================================================

def test_add_extension_accepts_a_class_or_an_instance():
    """
        Test that a class is instantiated and an instance is registered as is.
    """
    host = _make_host()

    from_class = host.add_extension(_RecordingExtension)
    instance = _ConfiguredExtension()
    from_instance = host.add_extension(instance)

    if not isinstance(from_class, _RecordingExtension) or from_instance is not instance:
        raise AssertionError("Unexpected registered extensions {} / {}".format(from_class, from_instance))

    names = sorted(extension.name for extension in host.extension_registry.list())
    if names != ["configured", "recording"]:
        raise AssertionError("Unexpected registered names {}".format(names))

    if host.has_extensions() is not True:
        raise AssertionError("Expected the host to report extensions")

    return


def test_add_extension_refuses_misuse():
    """
        Test that something that is not an extension, an unnamed extension
        and a reserved name are refused.
    """
    host = _make_host()

    _expect_error(SemanticError, lambda: host.add_extension(object()))
    _expect_error(SemanticError, lambda: host.add_extension(_Unnamed))
    _expect_error(ConfigurationError, lambda: host.add_extension(_ReservedName))

    return


def test_add_extension_after_start_is_refused():
    """
        Test that extensions can not be added once they have been started.
    """
    host = _make_host()
    host.start()

    _expect_error(SemanticError, lambda: host.add_extension(_RecordingExtension))

    return


def test_load_configured_loads_import_strings_from_allowed_packages():
    """
        Test that an import string inside the allowed packages is loaded and registered.
    """
    host = _make_host()
    settings = ExtensionSettings(load=[_THIS_MODULE + ":_ConfiguredExtension"], allowed_packages=["ccai.tests"])

    names = host.load_configured(settings)

    if names != ["configured"] or not isinstance(host.extension_registry.get("configured"), _ConfiguredExtension):
        raise AssertionError("Expected the configured extension to be registered, got {}".format(names))

    return


def test_load_configured_with_empty_settings_loads_nothing():
    """
        Test that settings asking for nothing register nothing.
    """
    host = _make_host()

    names = host.load_configured(ExtensionSettings())

    if names != [] or host.has_extensions() is not False:
        raise AssertionError("Expected nothing to be loaded, got {}".format(names))

    return


def test_load_configured_refuses_a_disallowed_package():
    """
        Test that an import string outside the allowed packages is a
        configuration error and nothing is registered.
    """
    host = _make_host()
    settings = ExtensionSettings(load=[_THIS_MODULE + ":_ConfiguredExtension"], allowed_packages=["mycompany"])

    error = _expect_error(ConfigurationError, lambda: host.load_configured(settings))

    if "allowed extension packages" not in str(error):
        raise AssertionError("Expected the allow-list refusal in the message, got {}".format(error))

    if host.has_extensions() is not False:
        raise AssertionError("Expected nothing to be registered")

    return


def test_load_configured_refuses_an_unknown_extension_and_a_duplicate():
    """
        Test that a missing class and a name already registered are
        configuration errors.
    """
    host = _make_host()
    unknown = ExtensionSettings(load=[_THIS_MODULE + ":NoSuchExtension"], allowed_packages=["ccai.tests"])

    _expect_error(ConfigurationError, lambda: host.load_configured(unknown))

    host.add_extension(_ConfiguredExtension)
    duplicate = ExtensionSettings(load=[_THIS_MODULE + ":_ConfiguredExtension"], allowed_packages=["ccai.tests"])

    _expect_error(ConfigurationError, lambda: host.load_configured(duplicate))

    return


def test_load_configured_loads_manifests_from_paths():
    """
        Test that a manifest found in a configured directory is loaded, and
        that a disallowed entry point in a manifest is a configuration error.
    """
    temp_dir = tempfile.mkdtemp()

    try:
        extension_dir = os.path.join(temp_dir, "configured")
        os.makedirs(extension_dir)
        manifest = {"name": "configured", "version": "1.0.0", "entry_point": _THIS_MODULE + "._ConfiguredExtension"}
        with open(os.path.join(extension_dir, "extension.json"), "w") as manifest_file:
            json.dump(manifest, manifest_file)

        host = _make_host()
        names = host.load_configured(ExtensionSettings(paths=[Path(temp_dir)], allowed_packages=["ccai.tests"]))

        if names != ["configured"]:
            raise AssertionError("Expected the manifest's extension, got {}".format(names))

        refusing_host = _make_host()
        settings = ExtensionSettings(paths=[Path(temp_dir)], allowed_packages=["mycompany"])
        _expect_error(ConfigurationError, lambda: refusing_host.load_configured(settings))
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    return


# =============================================================================
# Starting, firing and stopping
# =============================================================================

def test_start_initializes_and_activates_once():
    """
        Test that start initializes and activates every extension, once.
    """
    host = _make_host()
    host.add_extension(_RecordingExtension)

    host.start()
    host.start()

    if _HostEvents.log != ["recording.initialize", "recording.activate"]:
        raise AssertionError("Unexpected events {}".format(_HostEvents.log))

    if host.extension_registry.get_state("recording") != ExtensionState.ACTIVE:
        raise AssertionError("Expected the extension to be ACTIVE")

    return


def test_start_with_a_missing_dependency_is_a_configuration_error():
    """
        Test that a missing required dependency ends the start.
    """
    host = _make_host()
    host.add_extension(_NeedsMissingDependency)

    _expect_error(ConfigurationError, host.start)

    return


def test_lifecycle_hooks_fire_in_order_and_ready_and_stop_once():
    """
        Test the application lifecycle hooks in order, on_app_ready and stop
        happening once each, and shutdown after on_app_shutdown.
    """
    host = _make_host()
    host.add_extension(_RecordingExtension)

    host.start()
    host.fire_config_loaded()
    host.fire_app_init()
    host.fire_routes_registered()
    host.fire_app_ready()
    host.fire_app_ready()
    host.stop()
    host.stop()
    host.fire_app_ready()

    expected = [
        "recording.initialize",
        "recording.activate",
        "recording.on_config_loaded",
        "recording.on_app_init",
        "recording.on_routes_registered",
        "recording.on_app_ready",
        "recording.on_app_shutdown",
        "recording.shutdown",
    ]
    if _HostEvents.log != expected:
        raise AssertionError("Expected {}, got {}".format(expected, _HostEvents.log))

    if host.ready_fired is not True or host.stopped is not True:
        raise AssertionError("Expected the ready and stopped flags to be set")

    return


def test_stop_before_start_does_nothing():
    """
        Test that extensions never started are not shut down.
    """
    host = _make_host()
    host.add_extension(_RecordingExtension)

    host.stop()

    if _HostEvents.log != []:
        raise AssertionError("Expected nothing to run, got {}".format(_HostEvents.log))

    return
