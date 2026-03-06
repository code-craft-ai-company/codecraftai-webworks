"""
.. module:: cli
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: CLI commands for OpenAPI specification generation, validation,
        and asset management.

.. moduleauthor:: Automation Mojo LLC

This module provides CLI commands for the OpenAPI tooling integrated with
the webworks CLI framework. It includes commands for generating OpenAPI
specifications in JSON or YAML format, validating specifications, and
updating vendored static assets for Swagger UI and ReDoc.

The commands are organized under an ``openapi`` command group and can be
invoked as::

    webworks openapi generate [--output PATH] [--format FORMAT] [--tags TAGS] [--paths PREFIX]
    webworks openapi validate [--strict]
    webworks openapi update-assets [--swagger-version VERSION] [--redoc-version VERSION]
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

import json
import sys

from typing import Any, Dict, List, Optional, TYPE_CHECKING

from automojo.webworks.devexp.cli.command import CLICommand
from automojo.webworks.devexp.cli.group import CLIGroup

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace
    from automojo.webworks.openapi.generator import OpenAPIGenerator


class GenerateCommand(CLICommand):
    """
        CLI command that generates an OpenAPI specification.

        Generates the OpenAPI specification from the configured generator
        and writes it to a file or to stdout. Supports JSON and YAML
        output formats and optional filtering by tags or path prefix.

        The command accepts the following arguments:

        - ``--output`` / ``-o``: Output file path. Use ``-`` for stdout (default).
        - ``--format`` / ``-f``: Output format, either ``json`` or ``yaml`` (default: ``json``).
        - ``--tags``: Comma-separated list of tags to filter endpoints by.
        - ``--paths``: Path prefix to filter endpoints by.
    """

    name: str = "generate"
    help: str = "Generate OpenAPI specification"

    def add_arguments(self, parser: "ArgumentParser") -> None:
        """
            Add generate-specific arguments to the argument parser.

            :param parser: The argument parser to add arguments to.
        """
        parser.add_argument(
            "--output", "-o",
            default="-",
            help="Output file path. Use '-' for stdout (default: -)."
        )
        parser.add_argument(
            "--format", "-f",
            default="json",
            choices=["json", "yaml"],
            help="Output format (default: json)."
        )
        parser.add_argument(
            "--tags",
            default=None,
            help="Filter by tags (comma-separated)."
        )
        parser.add_argument(
            "--paths",
            default=None,
            help="Filter by path prefix."
        )
        return

    def execute(self, args: "Namespace", config: Dict[str, Any]) -> int:
        """
            Execute the generate command.

            Retrieves the OpenAPI generator from the config dictionary,
            generates the specification, applies any requested filters,
            and writes the output to the specified destination.

            :param args: Parsed command-line arguments.
            :param config: Configuration dictionary. Must contain an
                ``openapi_generator`` key with an :class:`OpenAPI_Generator` instance.

            :returns: Exit code where 0 indicates success and non-zero indicates an error.
        """
        generator = config.get("openapi_generator")
        if generator is None:
            print("Error: No OpenAPI generator configured.", file=sys.stderr)
            return 1

        spec = generator.generate()

        if args.tags is not None:
            tag_list = [t.strip() for t in args.tags.split(",") if t.strip()]
            spec = _filter_spec_by_tags(spec, tag_list)

        if args.paths is not None:
            spec = _filter_spec_by_path_prefix(spec, args.paths)

        output_format = args.format

        if args.output == "-":
            if output_format == "json":
                output_text = json.dumps(spec, indent=2, sort_keys=True)
            else:
                output_text = _dump_yaml(spec)
                if output_text is None:
                    print("Error: PyYAML is required for YAML output.", file=sys.stderr)
                    return 1

            print(output_text)
            return 0

        # Write to file
        try:
            generator.export(args.output, format=output_format)
        except (ValueError, OSError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

        return 0


class ValidateCommand(CLICommand):
    """
        CLI command that validates an OpenAPI specification.

        Validates the generated OpenAPI specification without exporting it.
        Reports any validation issues found or confirms the specification
        is valid.

        The command accepts the following arguments:

        - ``--strict``: Enable strict validation mode that treats warnings as errors.
    """

    name: str = "validate"
    help: str = "Validate OpenAPI specification"

    def add_arguments(self, parser: "ArgumentParser") -> None:
        """
            Add validate-specific arguments to the argument parser.

            :param parser: The argument parser to add arguments to.
        """
        parser.add_argument(
            "--strict",
            action="store_true",
            default=False,
            help="Enable strict validation mode."
        )
        return

    def execute(self, args: "Namespace", config: Dict[str, Any]) -> int:
        """
            Execute the validate command.

            Retrieves the OpenAPI generator from the config dictionary,
            validates the specification, and prints the results.

            :param args: Parsed command-line arguments.
            :param config: Configuration dictionary. Must contain an
                ``openapi_generator`` key with an :class:`OpenAPI_Generator` instance.

            :returns: Exit code where 0 indicates the specification is valid
                and 1 indicates validation issues were found.
        """
        generator = config.get("openapi_generator")
        if generator is None:
            print("Error: No OpenAPI generator configured.", file=sys.stderr)
            return 1

        issues = generator.validate(strict=args.strict)

        if len(issues) == 0:
            print("OpenAPI specification is valid.")
            return 0

        print(f"Validation found {len(issues)} issue(s):")
        for issue in issues:
            print(f"  [{issue.severity}] {issue.path}: {issue.message}")

        return 1


class UpdateAssetsCommand(CLICommand):
    """
        CLI command that downloads and updates vendored static assets
        for Swagger UI and ReDoc.

        Downloads the latest (or specified) versions of Swagger UI and
        ReDoc distribution files from their official sources, places
        them in the static asset directory, and updates the manifest
        with version and checksum information.

        The command accepts the following arguments:

        - ``--swagger-version``: Specific Swagger UI version to download.
        - ``--redoc-version``: Specific ReDoc version to download.
    """

    name: str = "update-assets"
    help: str = "Download and update vendored Swagger UI and ReDoc assets"

    def add_arguments(self, parser: "ArgumentParser") -> None:
        """
            Add update-assets-specific arguments to the argument parser.

            :param parser: The argument parser to add arguments to.
        """
        parser.add_argument(
            "--swagger-version",
            default=None,
            help="Swagger UI version to download (default: latest)."
        )
        parser.add_argument(
            "--redoc-version",
            default=None,
            help="ReDoc version to download (default: latest)."
        )
        return

    def execute(self, args: "Namespace", config: Dict[str, Any]) -> int:
        """
            Execute the update-assets command.

            Downloads Swagger UI and ReDoc assets and prints a summary
            of the downloaded versions and file checksums.

            :param args: Parsed command-line arguments.
            :param config: Configuration dictionary.

            :returns: Exit code where 0 indicates success and non-zero
                indicates an error.
        """
        from automojo.webworks.openapi.assets import AssetUpdater

        updater = AssetUpdater()

        print("Updating Swagger UI assets...")
        try:
            swagger_result = updater.update_swagger_ui(version=args.swagger_version)
            swagger_version = swagger_result["version"]
            print("  Swagger UI version: {}".format(swagger_version))
            for fname, finfo in swagger_result["files"].items():
                print("  {} sha256: {}".format(fname, finfo["sha256"]))
        except Exception as exc:
            print("Error updating Swagger UI: {}".format(exc), file=sys.stderr)
            return 1

        print("")
        print("Updating ReDoc assets...")
        try:
            redoc_result = updater.update_redoc(version=args.redoc_version)
            redoc_version = redoc_result["version"]
            print("  ReDoc version: {}".format(redoc_version))
            for fname, finfo in redoc_result["files"].items():
                print("  {} sha256: {}".format(fname, finfo["sha256"]))
        except Exception as exc:
            print("Error updating ReDoc: {}".format(exc), file=sys.stderr)
            return 1

        print("")
        print("Asset update complete.")

        return 0


def create_openapi_group() -> CLIGroup:
    """
        Create the ``openapi`` CLI command group.

        Builds a :class:`CLIGroup` named ``openapi`` containing the
        :class:`GenerateCommand`, :class:`ValidateCommand`, and
        :class:`UpdateAssetsCommand` subcommands.

        :returns: A configured :class:`CLIGroup` instance.
    """
    group = CLIGroup(
        name="openapi",
        help="OpenAPI specification tools"
    )
    group.add_command(GenerateCommand())
    group.add_command(ValidateCommand())
    group.add_command(UpdateAssetsCommand())
    return group


# =============================================================================
# Private Helper Functions
# =============================================================================

def _filter_spec_by_tags(spec: Dict[str, Any], tags: List[str]) -> Dict[str, Any]:
    """
        Filter an OpenAPI specification to include only operations matching
        the given tags.

        Paths that have no remaining operations after filtering are removed
        from the result.

        :param spec: The OpenAPI specification dictionary.
        :param tags: A list of tag names to include.

        :returns: A new specification dictionary with only matching operations.
    """
    filtered_spec = dict(spec)
    original_paths = spec.get("paths", {})
    filtered_paths = {}

    http_methods = {"get", "post", "put", "patch", "delete", "head", "options", "trace"}

    for path_key, path_item in original_paths.items():
        filtered_item = {}

        for key, value in path_item.items():
            if key.lower() in http_methods:
                operation_tags = value.get("tags", [])
                if any(tag in operation_tags for tag in tags):
                    filtered_item[key] = value
            else:
                filtered_item[key] = value

        has_operations = any(k.lower() in http_methods for k in filtered_item)
        if has_operations:
            filtered_paths[path_key] = filtered_item

    filtered_spec["paths"] = filtered_paths
    return filtered_spec


def _filter_spec_by_path_prefix(spec: Dict[str, Any], prefix: str) -> Dict[str, Any]:
    """
        Filter an OpenAPI specification to include only paths matching
        the given prefix.

        :param spec: The OpenAPI specification dictionary.
        :param prefix: The path prefix to match against.

        :returns: A new specification dictionary with only matching paths.
    """
    filtered_spec = dict(spec)
    original_paths = spec.get("paths", {})
    filtered_paths = {}

    for path_key, path_item in original_paths.items():
        if path_key.startswith(prefix):
            filtered_paths[path_key] = path_item

    filtered_spec["paths"] = filtered_paths
    return filtered_spec


def _dump_yaml(spec: Dict[str, Any]) -> Optional[str]:
    """
        Serialize a specification dictionary to a YAML string.

        :param spec: The specification dictionary to serialize.

        :returns: A YAML string or None if PyYAML is not available.
    """
    try:
        import yaml
    except ImportError:
        return None

    yaml_str = yaml.dump(spec, default_flow_style=False, sort_keys=True)
    return yaml_str
