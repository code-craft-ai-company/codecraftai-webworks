"""
    Extension manifest for describing extension metadata.

    This module defines the ExtensionManifest dataclass which represents
    the metadata describing an extension's capabilities, dependencies,
    and configuration. Manifests can be loaded from YAML or JSON files
    and serialized back to those formats.
"""

import json
import os

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from ccai.webworks.extensibility.exceptions import ExtensionManifestError


REQUIRED_MANIFEST_FIELDS = ["name", "version", "entry_point"]


@dataclass
class ExtensionManifest:
    """
        Metadata describing an extension.

        The manifest contains all information needed by the framework
        to discover, load, and configure an extension including its
        identity, dependencies, extension points, and configuration schema.

        :param name: The unique name identifying the extension.
        :param version: The version string for the extension.
        :param entry_point: The Python import path to the extension class.
        :param description: A human-readable description of the extension.
        :param author: The author or maintainer of the extension.
        :param license: The license under which the extension is distributed.
        :param homepage: A URL to the extension's homepage or repository.
        :param dependencies: List of required extension names.
        :param optional_dependencies: List of optional extension names.
        :param framework_dependencies: List of required framework features.
        :param provides_extension_points: List of extension point names this extension provides.
        :param consumes_extension_points: List of extension point names this extension consumes.
        :param config_schema: JSON Schema dict describing the extension's configuration.
    """

    name: str
    version: str
    entry_point: str
    description: str = ""
    author: str = ""
    license: str = ""
    homepage: str = ""
    dependencies: List[str] = field(default_factory=list)
    optional_dependencies: List[str] = field(default_factory=list)
    framework_dependencies: List[str] = field(default_factory=list)
    provides_extension_points: List[str] = field(default_factory=list)
    consumes_extension_points: List[str] = field(default_factory=list)
    config_schema: Optional[Dict[str, Any]] = None

    @classmethod
    def from_yaml(cls, content: str) -> 'ExtensionManifest':
        """
            Parse manifest from YAML content string.

            :param content: A string containing YAML-formatted manifest data.

            :returns: An ExtensionManifest populated from the parsed YAML.

            :raises: ExtensionManifestError
        """
        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError as yerr:
            errmsg = "Failed to parse YAML manifest content: {}".format(yerr)
            raise ExtensionManifestError(errmsg) from yerr

        if data is None or not isinstance(data, dict):
            errmsg = "YAML manifest content must be a mapping"
            raise ExtensionManifestError(errmsg)

        manifest = cls._from_dict(data)
        return manifest

    @classmethod
    def from_json(cls, content: str) -> 'ExtensionManifest':
        """
            Parse manifest from JSON content string.

            :param content: A string containing JSON-formatted manifest data.

            :returns: An ExtensionManifest populated from the parsed JSON.

            :raises: ExtensionManifestError
        """
        try:
            data = json.loads(content)
        except json.JSONDecodeError as jerr:
            errmsg = "Failed to parse JSON manifest content: {}".format(jerr)
            raise ExtensionManifestError(errmsg) from jerr

        if not isinstance(data, dict):
            errmsg = "JSON manifest content must be an object"
            raise ExtensionManifestError(errmsg)

        manifest = cls._from_dict(data)
        return manifest

    @classmethod
    def from_file(cls, path: Path) -> 'ExtensionManifest':
        """
            Load manifest from a file, auto-detecting format from extension.

            Supported file extensions are .yaml, .yml for YAML format
            and .json for JSON format.

            :param path: The file path to load the manifest from.

            :returns: An ExtensionManifest populated from the file contents.

            :raises: ExtensionManifestError
        """
        file_path = Path(path)

        if not file_path.exists():
            errmsg = "Manifest file not found: {}".format(file_path)
            raise ExtensionManifestError(errmsg, path=file_path)

        suffix = file_path.suffix.lower()

        try:
            content = file_path.read_text(encoding="utf-8")
        except OSError as oserr:
            errmsg = "Failed to read manifest file '{}': {}".format(file_path, oserr)
            raise ExtensionManifestError(errmsg, path=file_path) from oserr

        if suffix in (".yaml", ".yml"):
            manifest = cls.from_yaml(content)
        elif suffix == ".json":
            manifest = cls.from_json(content)
        else:
            errmsg = "Unsupported manifest file format '{}'. Expected .yaml, .yml, or .json".format(suffix)
            raise ExtensionManifestError(errmsg, path=file_path)

        return manifest

    def to_yaml(self) -> str:
        """
            Serialize manifest to a YAML-formatted string.

            :returns: A YAML string representation of the manifest.
        """
        data = self._to_dict()
        content = yaml.dump(data, default_flow_style=False, sort_keys=False)
        return content

    def to_json(self) -> str:
        """
            Serialize manifest to a JSON-formatted string.

            :returns: A JSON string representation of the manifest.
        """
        data = self._to_dict()
        content = json.dumps(data, indent=2, sort_keys=False)
        return content

    def validate(self) -> List[str]:
        """
            Validate the manifest and return a list of validation errors.

            Checks that all required fields are present and non-empty.

            :returns: A list of validation error message strings. Empty if valid.
        """
        errors = []

        for field_name in REQUIRED_MANIFEST_FIELDS:
            value = getattr(self, field_name, None)
            if value is None or (isinstance(value, str) and len(value.strip()) == 0):
                errmsg = "Required field '{}' is missing or empty".format(field_name)
                errors.append(errmsg)

        return errors

    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> 'ExtensionManifest':
        """
            Create an ExtensionManifest from a dictionary of values.

            Missing required fields will result in an ExtensionManifestError.

            :param data: A dictionary containing manifest field values.

            :returns: An ExtensionManifest populated from the dictionary.

            :raises: ExtensionManifestError
        """
        missing_fields = []
        for field_name in REQUIRED_MANIFEST_FIELDS:
            if field_name not in data:
                missing_fields.append(field_name)

        if len(missing_fields) > 0:
            errmsg = "Manifest is missing required fields: {}".format(", ".join(missing_fields))
            raise ExtensionManifestError(errmsg)

        manifest = cls(
            name=str(data["name"]),
            version=str(data["version"]),
            entry_point=str(data["entry_point"]),
            description=str(data.get("description", "")),
            author=str(data.get("author", "")),
            license=str(data.get("license", "")),
            homepage=str(data.get("homepage", "")),
            dependencies=list(data.get("dependencies", [])),
            optional_dependencies=list(data.get("optional_dependencies", [])),
            framework_dependencies=list(data.get("framework_dependencies", [])),
            provides_extension_points=list(data.get("provides_extension_points", [])),
            consumes_extension_points=list(data.get("consumes_extension_points", [])),
            config_schema=data.get("config_schema", None),
        )

        return manifest

    def _to_dict(self) -> Dict[str, Any]:
        """
            Convert the manifest to a dictionary representation.

            Only includes optional fields that have non-default values
            to keep the serialized output clean.

            :returns: A dictionary of manifest field values.
        """
        data = {
            "name": self.name,
            "version": self.version,
            "entry_point": self.entry_point,
        }

        if len(self.description) > 0:
            data["description"] = self.description

        if len(self.author) > 0:
            data["author"] = self.author

        if len(self.license) > 0:
            data["license"] = self.license

        if len(self.homepage) > 0:
            data["homepage"] = self.homepage

        if len(self.dependencies) > 0:
            data["dependencies"] = self.dependencies

        if len(self.optional_dependencies) > 0:
            data["optional_dependencies"] = self.optional_dependencies

        if len(self.framework_dependencies) > 0:
            data["framework_dependencies"] = self.framework_dependencies

        if len(self.provides_extension_points) > 0:
            data["provides_extension_points"] = self.provides_extension_points

        if len(self.consumes_extension_points) > 0:
            data["consumes_extension_points"] = self.consumes_extension_points

        if self.config_schema is not None:
            data["config_schema"] = self.config_schema

        return data
