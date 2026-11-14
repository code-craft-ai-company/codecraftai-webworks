"""
    Tests for the ExtensionSettings class.

    This module contains unit tests for reading the ``extensions`` section
    of an application's configuration.
"""

import shutil
import tempfile

from pathlib import Path
from typing import Any

from ccai.errors.exceptions import ConfigurationError

from ccai.webworks.extensibility.extensionsettings import ExtensionSettings


class _FlatConfig:
    """
        A configuration with dot-notation keys, the shape of the
        ConfigRegistry a web application loads.
    """

    def __init__(self, values: dict):
        self._values = dict(values)
        return

    def get(self, key: str, default: Any = None) -> Any:
        rtnval = self._values.get(key, default)
        return rtnval


def _expect_configuration_error(config: Any) -> ConfigurationError:
    """
        Read settings that must be refused.

        :param config: The configuration.

        :returns: The ConfigurationError raised.
    """
    caught = None
    try:
        ExtensionSettings.from_config(config)
    except ConfigurationError as err:
        caught = err

    if caught is None:
        raise AssertionError("Expected ConfigurationError for {!r}".format(config))

    return caught


def test_no_extensions_section_loads_nothing():
    """
        Test that a configuration without an extensions section gives empty
        settings, for both configuration shapes and for no configuration.
    """
    for config in (None, {}, _FlatConfig({"server.port": 8000})):
        settings = ExtensionSettings.from_config(config)

        if settings.requests_loading() is not False:
            raise AssertionError("Expected nothing to be loaded for {!r}".format(config))

    return


def test_settings_are_read_from_dot_notation_keys():
    """
        Test that the settings are read from extensions.<setting> keys.
    """
    temp_dir = tempfile.mkdtemp()

    try:
        config = _FlatConfig({
            "extensions.load": ["mycompany.audit:AuditExtension"],
            "extensions.entry_points": ["metrics"],
            "extensions.paths": [temp_dir],
            "extensions.allowed_packages": ["mycompany"],
        })

        settings = ExtensionSettings.from_config(config)

        if settings.load != ["mycompany.audit:AuditExtension"]:
            raise AssertionError("Unexpected load {}".format(settings.load))

        if settings.entry_points != ["metrics"]:
            raise AssertionError("Unexpected entry_points {}".format(settings.entry_points))

        if settings.paths != [Path(temp_dir)]:
            raise AssertionError("Unexpected paths {}".format(settings.paths))

        if settings.allowed_packages != ["mycompany"]:
            raise AssertionError("Unexpected allowed_packages {}".format(settings.allowed_packages))

        if settings.requests_loading() is not True:
            raise AssertionError("Expected the settings to request loading")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    return


def test_settings_are_read_from_a_nested_dictionary():
    """
        Test that a nested dictionary configuration is read as well.
    """
    config = {"extensions": {"load": ["mycompany.audit:AuditExtension"], "allowed_packages": ["mycompany"]}}

    settings = ExtensionSettings.from_config(config)

    if settings.load != ["mycompany.audit:AuditExtension"] or settings.allowed_packages != ["mycompany"]:
        raise AssertionError("Unexpected settings {} / {}".format(settings.load, settings.allowed_packages))

    return


def test_loading_without_allowed_packages_is_a_configuration_error():
    """
        Test that extensions can not be loaded without an allow-list.
    """
    error = _expect_configuration_error(_FlatConfig({"extensions.load": ["mycompany.audit:AuditExtension"]}))

    if "allowed_packages" not in str(error):
        raise AssertionError("Expected the message to name allowed_packages, got {}".format(error))

    return


def test_malformed_settings_are_configuration_errors():
    """
        Test that a value that is not a list of non-empty strings, and a
        manifest path that is relative or missing, are refused.
    """
    _expect_configuration_error(_FlatConfig({"extensions.load": "mycompany.audit:AuditExtension"}))
    _expect_configuration_error(_FlatConfig({"extensions.load": [""], "extensions.allowed_packages": ["x"]}))
    _expect_configuration_error(_FlatConfig({"extensions.allowed_packages": [42]}))
    _expect_configuration_error(_FlatConfig({"extensions.paths": ["relative/dir"], "extensions.allowed_packages": ["x"]}))
    _expect_configuration_error(_FlatConfig({
        "extensions.paths": ["/nonexistent/webworks/extension/dir"],
        "extensions.allowed_packages": ["x"],
    }))

    return
