"""
    Extension loader for discovering and loading extensions.

    This module provides the ExtensionLoader class which discovers
    extensions from directory paths and Python entry points, loads
    extension manifests, instantiates extension classes, filters
    manifests by name pattern, and supports lazy loading of extensions.
"""

import fnmatch
import importlib
import inspect
import logging
import os

from pathlib import Path
from typing import Callable, Dict, List, Optional, TYPE_CHECKING

from ccai.webworks.extensibility.exceptions import ExtensionLoadError
from ccai.webworks.extensibility.exceptions import ExtensionManifestError
from ccai.webworks.extensibility.extension import Extension
from ccai.webworks.extensibility.manifest import ExtensionManifest

if TYPE_CHECKING:
    from ccai.webworks.extensibility.registry import ExtensionRegistry


logger = logging.getLogger("ccai.webworks.extensibility.loader")


MANIFEST_FILENAMES = ["extension.yaml", "extension.yml", "extension.json"]

#: The entry point group installed extensions are published under.
EXTENSION_ENTRY_POINT_GROUP = "ccai.extensions"


class ExtensionLoader:
    """
        Discovers and loads extensions from various sources.

        The ExtensionLoader searches configured directory paths and
        Python entry points for extension manifests, validates them,
        and loads extension classes. It also supports lazy loading
        where factory functions are stored and extensions are only
        instantiated on first access.

        A manifest names the class to load, and loading it imports a module
        and calls what the manifest names. The loader therefore only
        instantiates a class that derives from Extension, and it can be
        given the list of packages extensions may live in: with
        ``allowed_packages`` set, a manifest whose entry point is outside
        those packages is refused before anything is imported.

        :param registry: The extension registry to register discovered extensions.
        :param allowed_packages: The packages an extension's entry point may
            be in (a package allows its subpackages and modules too). When
            None, the module named by a manifest is imported wherever it is.
    """

    def __init__(self, registry: 'ExtensionRegistry', allowed_packages: Optional[List[str]] = None):
        """
            Initialize the extension loader.

            :param registry: The extension registry to register discovered extensions.
            :param allowed_packages: The packages an extension's entry point
                may be in, or None to allow any module.
        """
        self._registry = registry
        self._lazy_extensions: Dict[str, Callable[[], 'Extension']] = {}

        self._allowed_packages: Optional[List[str]] = None
        if allowed_packages is not None:
            self._allowed_packages = list(allowed_packages)

        return

    @property
    def allowed_packages(self) -> Optional[List[str]]:
        """
            Get the packages an extension's entry point may be in.

            :returns: The package names, or None when any module is allowed.
        """
        rtnval = None
        if self._allowed_packages is not None:
            rtnval = list(self._allowed_packages)
        return rtnval

    def _is_allowed_module(self, module_path: str) -> bool:
        """
            Check that a module may be imported for an extension.

            :param module_path: The dotted module path of an entry point.

            :returns: True if no packages are configured, or the module is
                      one of the configured packages or inside one.
        """
        if self._allowed_packages is None:
            return True

        for package_name in self._allowed_packages:
            if module_path == package_name:
                return True
            if module_path.startswith(package_name + "."):
                return True

        return False

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

    def discover_from_entry_points(self, group: str = "ccai.extensions") -> List[ExtensionManifest]:
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
            and instantiates the extension class, which must derive from
            Extension. The manifest is attached to the instance.

            Every way this can fail is reported as ExtensionManifestError:
            an entry point outside the allowed packages, a module that
            cannot be imported or raises while it is imported, a missing
            class, an entry point that is not an Extension subclass, and a
            constructor that raises.

            :param manifest: The extension manifest describing the extension.

            :returns: The loaded extension instance.

            :raises: ExtensionManifestError
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

        # Refuse a module outside the configured extension packages before
        # importing it: importing runs the module's code.
        if self._is_allowed_module(module_path) is False:
            errmsg = "The entry_point '{}' of extension '{}' is not in one of the allowed extension packages: {}".format(
                entry_point, manifest.name, ", ".join(self._allowed_packages)
            )
            raise ExtensionManifestError(errmsg)

        # Every failure of the import is contained, not only ImportError: a
        # module can raise anything while it is executed, including
        # SystemExit, and one broken extension must not stop the others
        # (or the process) from loading.
        try:
            module = importlib.import_module(module_path)
        except (Exception, SystemExit) as imperr:
            errmsg = "Failed to import module '{}' for extension '{}': {}: {}".format(
                module_path, manifest.name, type(imperr).__name__, imperr
            )
            raise ExtensionManifestError(errmsg) from imperr

        ext_class = getattr(module, class_name, None)
        if ext_class is None:
            errmsg = "Class '{}' not found in module '{}' for extension '{}'".format(
                class_name, module_path, manifest.name
            )
            raise ExtensionManifestError(errmsg)

        # Only an Extension subclass is ever called. A manifest that names
        # some other callable (a function such as sys.exit, or a class that
        # is not an extension) is refused without calling it.
        is_extension_class = inspect.isclass(ext_class) and issubclass(ext_class, Extension)
        if is_extension_class is False:
            errmsg = "The entry_point '{}' of extension '{}' is not a class deriving from Extension".format(
                entry_point, manifest.name
            )
            raise ExtensionManifestError(errmsg)

        try:
            instance = ext_class()
        except (Exception, SystemExit) as err:
            errmsg = "Failed to instantiate class '{}' for extension '{}': {}: {}".format(
                class_name, manifest.name, type(err).__name__, err
            )
            raise ExtensionManifestError(errmsg) from err

        # The manifest stays with the instance: the registry reads its
        # configuration schema when it initializes the extension.
        instance.attach_manifest(manifest)

        return instance

    def load_from_import_string(self, import_string: str) -> 'Extension':
        """
            Load one extension named by an import string.

            The string names the module and the Extension subclass, either
            as ``"package.module:ClassName"`` (the entry point notation) or
            as ``"package.module.ClassName"`` (the manifest notation). The
            module is checked against the allowed packages before it is
            imported, and only a class deriving from Extension is
            instantiated (without arguments).

            :param import_string: The import string of the extension class.

            :returns: The extension instance.

            :raises ExtensionLoadError: If the string is malformed, the
                module is outside the allowed packages or cannot be
                imported, the name is not an Extension subclass, or the
                class cannot be instantiated.
        """
        module_path, class_name = self._split_import_string(import_string)

        ext_class = self._import_extension_class(module_path, class_name, import_string)
        rtnval = self._instantiate_extension_class(ext_class, import_string)

        return rtnval

    def load_from_entry_point(self, name: str, group: str = EXTENSION_ENTRY_POINT_GROUP) -> 'Extension':
        """
            Load one extension published as a Python entry point.

            Only the entry point with the given name is looked at -- other
            installed extensions are never imported. Its module is checked
            against the allowed packages before it is imported.

            :param name: The entry point name.
            :param group: The entry point group.

            :returns: The extension instance.

            :raises ExtensionLoadError: If no entry point (or more than one)
                has the name, or the entry point fails like an import string
                does (see :meth:`load_from_import_string`).
        """
        from importlib.metadata import entry_points as get_entry_points

        reference = "{}:{}".format(group, name)

        matching = list(get_entry_points().select(group=group, name=name))

        if len(matching) != 1:
            errmsg = "Expected exactly one entry point named '{}' in group '{}', found {}".format(
                name, group, len(matching)
            )
            raise ExtensionLoadError(errmsg, reference=reference)

        entry = matching[0]

        module_path = entry.module
        attribute = entry.attr
        if attribute is None or attribute == "" or "." in attribute:
            errmsg = "The entry point '{}' ({}) must name a class in a module as 'module:ClassName'".format(
                reference, entry.value
            )
            raise ExtensionLoadError(errmsg, reference=reference)

        ext_class = self._import_extension_class(module_path, attribute, reference)
        rtnval = self._instantiate_extension_class(ext_class, reference)

        return rtnval

    def _split_import_string(self, import_string: str) -> 'tuple':
        """
            Split an import string into its module path and class name.

            :param import_string: ``"module:ClassName"`` or ``"module.ClassName"``.

            :returns: The ``(module_path, class_name)`` pair.

            :raises ExtensionLoadError: If the string names no module and class.
        """
        if not isinstance(import_string, str):
            errmsg = "An extension import string must be a string, got {!r}".format(import_string)
            raise ExtensionLoadError(errmsg, reference=repr(import_string))

        if ":" in import_string:
            module_path, _, class_name = import_string.partition(":")
        else:
            module_path, _, class_name = import_string.rpartition(".")

        if module_path == "" or class_name == "" or ":" in class_name:
            errmsg = "Invalid extension import string '{}': expected 'package.module:ClassName'".format(
                import_string
            )
            raise ExtensionLoadError(errmsg, reference=import_string)

        rtnval = (module_path, class_name)
        return rtnval

    def _import_extension_class(self, module_path: str, class_name: str, reference: str) -> type:
        """
            Import a module and return the Extension subclass it defines.

            The module is refused before it is imported when it is outside
            the allowed packages: importing runs the module's code.

            :param module_path: The dotted module path.
            :param class_name: The name of the class in the module.
            :param reference: The import string or entry point, for messages.

            :returns: The Extension subclass.

            :raises ExtensionLoadError: If the module is not allowed or
                cannot be imported, or the name is not an Extension subclass.
        """
        if self._is_allowed_module(module_path) is False:
            errmsg = "The extension '{}' is not in one of the allowed extension packages: {}".format(
                reference, ", ".join(self._allowed_packages)
            )
            raise ExtensionLoadError(errmsg, reference=reference)

        # A module can raise anything while it is executed, SystemExit
        # included; it is reported as a load failure of this extension.
        try:
            module = importlib.import_module(module_path)
        except (Exception, SystemExit) as imperr:
            errmsg = "Failed to import module '{}' for extension '{}': {}: {}".format(
                module_path, reference, type(imperr).__name__, imperr
            )
            raise ExtensionLoadError(errmsg, reference=reference) from imperr

        ext_class = getattr(module, class_name, None)

        is_extension_class = inspect.isclass(ext_class) and issubclass(ext_class, Extension)
        if is_extension_class is False:
            errmsg = "'{}' does not name a class deriving from Extension".format(reference)
            raise ExtensionLoadError(errmsg, reference=reference)

        return ext_class

    def _instantiate_extension_class(self, ext_class: type, reference: str) -> 'Extension':
        """
            Instantiate an Extension subclass without arguments.

            :param ext_class: The Extension subclass.
            :param reference: The import string or entry point, for messages.

            :returns: The extension instance.

            :raises ExtensionLoadError: If the constructor raises.
        """
        try:
            instance = ext_class()
        except (Exception, SystemExit) as err:
            errmsg = "Failed to instantiate the extension class of '{}': {}: {}".format(
                reference, type(err).__name__, err
            )
            raise ExtensionLoadError(errmsg, reference=reference) from err

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
