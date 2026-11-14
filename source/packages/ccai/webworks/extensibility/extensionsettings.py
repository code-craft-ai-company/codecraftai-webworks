"""
    Extension settings of an application.

    This module defines the ExtensionSettings class, which reads the
    ``extensions`` section of an application's configuration: which
    extensions to load, where to look for extension manifests, and the
    packages extensions may be imported from.
"""

import os

from pathlib import Path
from typing import Any, List, Optional

from ccai.errors.exceptions import ConfigurationError

from ccai.webworks.extensibility.configuration import EXTENSIONS_CONFIG_SECTION


#: Setting naming the extensions to load, as import strings
#: (``"package.module:ClassName"``).
LOAD_SETTING = "load"

#: Setting naming extensions published as entry points in the
#: ``ccai.extensions`` group, by entry point name.
ENTRY_POINTS_SETTING = "entry_points"

#: Setting listing directories searched for extension manifests
#: (``extension.yaml`` / ``extension.yml`` / ``extension.json``), in the
#: directory itself and in the directories directly inside it.
PATHS_SETTING = "paths"

#: Setting listing the packages extensions may be imported from. Required
#: whenever anything is to be loaded.
ALLOWED_PACKAGES_SETTING = "allowed_packages"

#: The settings of the ``extensions`` section. Each extension's own
#: configuration lives under ``extensions.<extension name>``, so an
#: extension can not be named like one of them.
RESERVED_SETTING_NAMES = (
    LOAD_SETTING,
    ENTRY_POINTS_SETTING,
    PATHS_SETTING,
    ALLOWED_PACKAGES_SETTING,
)


class ExtensionSettings:
    """
        The ``extensions`` section of an application's configuration.

        Discovery is explicit. An application loads the extensions its code
        adds (``WebApplication.add_extension``) and the ones its
        configuration names, nothing else: no directory is scanned and no
        module is imported unless the configuration says so::

            extensions:
              load:                       # import strings
                - mycompany.audit.extension:AuditExtension
              entry_points:               # names in the "ccai.extensions" group
                - metrics
              paths:                      # directories holding extension manifests
                - /srv/myapp/extensions
              allowed_packages:           # required when anything is loaded
                - mycompany
              audit:                      # the "audit" extension's own settings
                level: full

        Every extension loaded from configuration must live in one of the
        ``allowed_packages`` (a package allows its subpackages); the loader
        refuses any other module before importing it.

        :param load: Import strings of extension classes.
        :param entry_points: Entry point names of extensions.
        :param paths: Directories searched for extension manifests.
        :param allowed_packages: Packages extensions may be imported from.
    """

    def __init__(
        self,
        load: Optional[List[str]] = None,
        entry_points: Optional[List[str]] = None,
        paths: Optional[List[Path]] = None,
        allowed_packages: Optional[List[str]] = None
    ):
        self._load: List[str] = list(load) if load is not None else []
        self._entry_points: List[str] = list(entry_points) if entry_points is not None else []
        self._paths: List[Path] = list(paths) if paths is not None else []
        self._allowed_packages: List[str] = list(allowed_packages) if allowed_packages is not None else []
        return

    @property
    def load(self) -> List[str]:
        """
            The import strings of the extensions to load.

            :returns: A copy of the list.
        """
        rtnval = list(self._load)
        return rtnval

    @property
    def entry_points(self) -> List[str]:
        """
            The entry point names of the extensions to load.

            :returns: A copy of the list.
        """
        rtnval = list(self._entry_points)
        return rtnval

    @property
    def paths(self) -> List[Path]:
        """
            The directories searched for extension manifests.

            :returns: A copy of the list.
        """
        rtnval = list(self._paths)
        return rtnval

    @property
    def allowed_packages(self) -> List[str]:
        """
            The packages extensions may be imported from.

            :returns: A copy of the list.
        """
        rtnval = list(self._allowed_packages)
        return rtnval

    def requests_loading(self) -> bool:
        """
            Whether the settings ask for any extension to be loaded.

            :returns: True when an import string, an entry point or a
                      manifest path is configured.
        """
        rtnval = len(self._load) > 0 or len(self._entry_points) > 0 or len(self._paths) > 0
        return rtnval

    @classmethod
    def from_config(cls, config: Any) -> "ExtensionSettings":
        """
            Read the extension settings from an application configuration.

            Two shapes are read: a configuration registry with dot-notation
            keys (``extensions.load``, ...), which is what a web application
            loads, and a nested dictionary (``{"extensions": {"load": ...}}``).
            A configuration without an ``extensions`` section gives empty
            settings: no extension is loaded.

            The settings are checked here, so a mistake ends the startup
            before anything is imported.

            :param config: The application configuration, or None.

            :returns: The extension settings.

            :raises ConfigurationError: If a setting is not a list of
                non-empty strings, a manifest path is not an existing
                absolute directory, or extensions are to be loaded and no
                ``allowed_packages`` are configured.
        """
        load = cls._read_string_list(config, LOAD_SETTING)
        entry_points = cls._read_string_list(config, ENTRY_POINTS_SETTING)
        path_strings = cls._read_string_list(config, PATHS_SETTING)
        allowed_packages = cls._read_string_list(config, ALLOWED_PACKAGES_SETTING)

        paths: List[Path] = []
        for path_string in path_strings:
            paths.append(cls._resolve_path(path_string))

        settings = cls(
            load=load,
            entry_points=entry_points,
            paths=paths,
            allowed_packages=allowed_packages
        )

        if settings.requests_loading() is True and len(allowed_packages) == 0:
            errmsg_lines = [
                "The configuration asks for extensions to be loaded, but '{}.{}' is not set.".format(
                    EXTENSIONS_CONFIG_SECTION, ALLOWED_PACKAGES_SETTING
                ),
                "Extensions are imported only from the packages listed there; list the "
                "package(s) the configured extensions live in.",
                "    {}.{}: {}".format(EXTENSIONS_CONFIG_SECTION, LOAD_SETTING, load),
                "    {}.{}: {}".format(EXTENSIONS_CONFIG_SECTION, ENTRY_POINTS_SETTING, entry_points),
                "    {}.{}: {}".format(EXTENSIONS_CONFIG_SECTION, PATHS_SETTING, path_strings),
            ]
            errmsg = os.linesep.join(errmsg_lines)
            raise ConfigurationError(errmsg)

        return settings

    @staticmethod
    def _read_setting(config: Any, setting_name: str) -> Any:
        """
            Read one setting of the ``extensions`` section.

            :param config: The application configuration, or None.
            :param setting_name: The setting's name inside the section.

            :returns: The value, or None when it is not set.
        """
        rtnval = None

        if config is None:
            return rtnval

        if isinstance(config, dict):
            section = config.get(EXTENSIONS_CONFIG_SECTION, None)
            if isinstance(section, dict):
                rtnval = section.get(setting_name, None)
        else:
            key = "{}.{}".format(EXTENSIONS_CONFIG_SECTION, setting_name)
            rtnval = config.get(key, None)

        return rtnval

    @classmethod
    def _read_string_list(cls, config: Any, setting_name: str) -> List[str]:
        """
            Read a setting that is a list of non-empty strings.

            :param config: The application configuration, or None.
            :param setting_name: The setting's name inside the section.

            :returns: The strings; an empty list when the setting is not set.

            :raises ConfigurationError: If the value is not a list of
                non-empty strings.
        """
        rtnval: List[str] = []

        value = cls._read_setting(config, setting_name)

        if value is None:
            return rtnval

        key = "{}.{}".format(EXTENSIONS_CONFIG_SECTION, setting_name)

        if not isinstance(value, (list, tuple)):
            errmsg = "The configuration value '{}' must be a list of strings, got {!r}.".format(key, value)
            raise ConfigurationError(errmsg)

        for item in value:
            if not isinstance(item, str) or item.strip() == "":
                errmsg = "The configuration value '{}' must be a list of non-empty strings, got the item {!r}.".format(
                    key, item
                )
                raise ConfigurationError(errmsg)
            rtnval.append(item.strip())

        return rtnval

    @staticmethod
    def _resolve_path(path_string: str) -> Path:
        """
            Resolve a configured manifest directory.

            ``~`` and environment variables are expanded. The result must be
            an absolute path to an existing directory: a relative path would
            depend on the working directory of the server process.

            :param path_string: The configured path.

            :returns: The directory path.

            :raises ConfigurationError: If the path is relative or is not an
                existing directory.
        """
        expanded = os.path.expandvars(os.path.expanduser(path_string))
        rtnval = Path(expanded)

        key = "{}.{}".format(EXTENSIONS_CONFIG_SECTION, PATHS_SETTING)

        if rtnval.is_absolute() is False:
            errmsg = "The extension manifest directory '{}' in '{}' must be an absolute path.".format(
                path_string, key
            )
            raise ConfigurationError(errmsg)

        if rtnval.is_dir() is False:
            errmsg = "The extension manifest directory '{}' in '{}' does not exist or is not a directory.".format(
                path_string, key
            )
            raise ConfigurationError(errmsg)

        return rtnval
