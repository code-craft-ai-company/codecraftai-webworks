"""
    Extension loader for discovering and loading extensions.

    This module provides the ExtensionLoader class which discovers
    extensions from directory paths and Python entry points, loads
    extension manifests, instantiates extension classes, filters
    manifests by name pattern, and supports lazy loading of extensions.
"""

import fnmatch
import importlib
import logging
import os

from pathlib import Path
from typing import Callable, Dict, List, Optional, TYPE_CHECKING

from automojo.webworks.extensibility.exceptions import ExtensionManifestError
from automojo.webworks.extensibility.manifest import ExtensionManifest

if TYPE_CHECKING:
    from automojo.webworks.extensibility.extension import Extension
    from automojo.webworks.extensibility.registry import ExtensionRegistry


logger = logging.getLogger("automojo.webworks.extensibility.loader")


MANIFEST_FILENAMES = ["extension.yaml", "extension.yml", "extension.json"]


class ExtensionLoader:
    """
        Discovers and loads extensions from various sources.

        The ExtensionLoader searches configured directory paths and
        Python entry points for extension manifests, validates them,
        and loads extension classes. It also supports lazy loading
        where factory functions are stored and extensions are only
        instantiated on first access.

        :param registry: The extension registry to register discovered extensions.
    """

    def __init__(self, registry: 'ExtensionRegistry'):
        """
            Initialize the extension loader.

            :param registry: The extension registry to register discovered extensions.
        """
        self._registry = registry
        self._lazy_extensions: Dict[str, Callable[[], 'Extension']] = {}
        return

    def discover_from_paths(self, paths: List[Path]) -> List[ExtensionManifest]:
        """
            Discover extensions from directory paths.

            Searches each path for manifest files named extension.yaml,
            extension.yml, or extension.json. Found manifests are parsed
            and validated. Invalid manifests are logged as warnings and
            skipped.

            :param paths: List of directory paths to search for extensions.

            :returns: A list of valid discovered extension manifests.
        """
        discovered = []

        for search_path in paths:
            dir_path = Path(search_path)

            if not dir_path.is_dir():
                logger.warning(
                    "Extension search path is not a directory: %s",
                    dir_path
                )
                continue

            # Search for manifest files in the directory itself
            for manifest_name in MANIFEST_FILENAMES:
                manifest_path = dir_path / manifest_name

                if manifest_path.is_file():
                    manifest = self._try_load_manifest(manifest_path)
                    if manifest is not None:
                        discovered.append(manifest)
                    break

            # Search subdirectories for manifest files
            if dir_path.is_dir():
                for entry in sorted(os.listdir(dir_path)):
                    sub_path = dir_path / entry

                    if not sub_path.is_dir():
                        continue

                    for manifest_name in MANIFEST_FILENAMES:
                        manifest_path = sub_path / manifest_name

                        if manifest_path.is_file():
                            manifest = self._try_load_manifest(manifest_path)
                            if manifest is not None:
                                discovered.append(manifest)
                            break

        return discovered

    def discover_from_entry_points(self, group: str = "automojo.extensions") -> List[ExtensionManifest]:
        """
            Discover extensions from Python entry points.

            Loads extensions registered under the specified entry point
            group. Each entry point should reference an Extension subclass.
            A manifest is constructed from the class metadata.

            :param group: The entry point group name to search.

            :returns: A list of discovered extension manifests.
        """
        discovered = []

        try:
            from importlib.metadata import entry_points as get_entry_points

            eps = get_entry_points()

            # Python 3.12+ returns a SelectableGroups, older returns dict
            if isinstance(eps, dict):
                group_eps = eps.get(group, [])
            else:
                group_eps = eps.select(group=group)

        except Exception as err:
            logger.warning(
                "Failed to load entry points for group '%s': %s",
                group, err
            )
            return discovered

        for ep in group_eps:
            try:
                ext_class = ep.load()

                ext_name = getattr(ext_class, "name", ep.name)
                ext_version = getattr(ext_class, "version", "0.0.0")
                ext_description = getattr(ext_class, "description", "")
                ext_deps = getattr(ext_class, "dependencies", [])
                ext_opt_deps = getattr(ext_class, "optional_dependencies", [])

                entry_point_str = "{}.{}".format(ext_class.__module__, ext_class.__name__)

                manifest = ExtensionManifest(
                    name=ext_name,
                    version=ext_version,
                    entry_point=entry_point_str,
                    description=ext_description,
                    dependencies=list(ext_deps),
                    optional_dependencies=list(ext_opt_deps),
                )

                discovered.append(manifest)

            except Exception as err:
                logger.warning(
                    "Failed to load entry point '%s' from group '%s': %s",
                    ep.name, group, err
                )

        return discovered

    def load_manifest(self, path: Path) -> ExtensionManifest:
        """
            Load an extension manifest from a file path.

            Parses the manifest file and validates it. If the manifest
            is invalid, raises ExtensionManifestError.

            :param path: Path to the manifest file.

            :returns: The parsed and validated extension manifest.

            :raises: ExtensionManifestError
        """
        file_path = Path(path)

        manifest = ExtensionManifest.from_file(file_path)

        errors = manifest.validate()
        if len(errors) > 0:
            error_list = "; ".join(errors)
            errmsg = "Manifest validation failed for '{}': {}".format(file_path, error_list)
            raise ExtensionManifestError(errmsg, path=file_path)

        return manifest

    def load_extension(self, manifest: ExtensionManifest) -> 'Extension':
        """
            Load an extension from its manifest.

            Imports the module specified by the manifest entry_point
            and instantiates the extension class.

            :param manifest: The extension manifest describing the extension.

            :returns: The loaded extension instance.

            :raises: ExtensionError
        """
        entry_point = manifest.entry_point

        # Split entry_point into module path and class name
        # e.g. "mypackage.mymodule.MyExtension" -> module="mypackage.mymodule", cls="MyExtension"
        last_dot_idx = entry_point.rfind(".")
        if last_dot_idx < 0:
            errmsg = "Invalid entry_point format '{}': expected 'module.ClassName'".format(entry_point)
            raise ExtensionManifestError(errmsg)

        module_path = entry_point[:last_dot_idx]
        class_name = entry_point[last_dot_idx + 1:]

        try:
            module = importlib.import_module(module_path)
        except ImportError as imperr:
            errmsg = "Failed to import module '{}' for extension '{}': {}".format(
                module_path, manifest.name, imperr
            )
            raise ExtensionManifestError(errmsg) from imperr

        ext_class = getattr(module, class_name, None)
        if ext_class is None:
            errmsg = "Class '{}' not found in module '{}' for extension '{}'".format(
                class_name, module_path, manifest.name
            )
            raise ExtensionManifestError(errmsg)

        try:
            instance = ext_class()
        except Exception as err:
            errmsg = "Failed to instantiate class '{}' for extension '{}': {}".format(
                class_name, manifest.name, err
            )
            raise ExtensionManifestError(errmsg) from err

        return instance

    def filter_by_pattern(
        self,
        manifests: List[ExtensionManifest],
        pattern: str
    ) -> List[ExtensionManifest]:
        """
            Filter manifests by name glob pattern.

            Uses fnmatch to match manifest names against the provided
            glob pattern.

            :param manifests: List of manifests to filter.
            :param pattern: Glob pattern to match against manifest names.

            :returns: A filtered list of manifests whose names match the pattern.
        """
        filtered = []

        for manifest in manifests:
            if fnmatch.fnmatch(manifest.name, pattern):
                filtered.append(manifest)

        return filtered

    def register_lazy(self, name: str, factory: Callable[[], 'Extension']) -> None:
        """
            Register a lazy-loaded extension.

            Stores a factory callable that will be invoked to create
            the extension instance on first access via get_lazy().

            :param name: The extension name.
            :param factory: A callable that returns an Extension instance.
        """
        self._lazy_extensions[name] = factory
        return

    def get_lazy(self, name: str) -> Optional['Extension']:
        """
            Get a lazy-loaded extension by name.

            If the extension has a registered factory and has not yet
            been instantiated, the factory is called and the resulting
            extension is registered with the registry. Subsequent calls
            return the already-loaded extension from the registry.

            :param name: The extension name.

            :returns: The extension instance, or None if not found.
        """
        # Check if already loaded in the registry
        existing = self._registry.get(name)
        if existing is not None:
            return existing

        # Check if we have a lazy factory for it
        factory = self._lazy_extensions.get(name, None)
        if factory is None:
            return None

        # Instantiate via factory
        try:
            extension = factory()
            self._registry.register(extension)

            # Remove from lazy dict since it is now loaded
            del self._lazy_extensions[name]

            rtnval = extension
        except Exception as err:
            logger.error(
                "Failed to lazy-load extension '%s': %s",
                name, err
            )
            rtnval = None

        return rtnval

    def has_lazy(self, name: str) -> bool:
        """
            Check if a lazy extension factory is registered for the given name.

            :param name: The extension name.

            :returns: True if a lazy factory exists for the name.
        """
        rtnval = name in self._lazy_extensions
        return rtnval

    def _try_load_manifest(self, path: Path) -> Optional[ExtensionManifest]:
        """
            Attempt to load and validate a manifest from a file path.

            If loading or validation fails, logs a warning and returns None.

            :param path: Path to the manifest file.

            :returns: The parsed manifest, or None if loading failed.
        """
        try:
            manifest = ExtensionManifest.from_file(path)

            errors = manifest.validate()
            if len(errors) > 0:
                error_list = "; ".join(errors)
                logger.warning(
                    "Skipping invalid manifest at '%s': %s",
                    path, error_list
                )
                return None

            return manifest

        except ExtensionManifestError as err:
            logger.warning(
                "Skipping manifest at '%s': %s",
                path, err
            )
            return None

        except Exception as err:
            logger.warning(
                "Unexpected error loading manifest at '%s': %s",
                path, err
            )
            return None
