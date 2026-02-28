"""
    Code generation commands for the webworks CLI.

    This module provides the :class:`GenerateEndpointCommand` and
    :class:`GenerateBlueprintCommand` that generate boilerplate Python
    files for endpoints and blueprints respectively. Both commands
    support a ``--dry-run`` option to preview generated files without
    writing them to disk and an ``--output-dir`` option to specify the
    target directory.

    Generated file names follow the repository naming conventions using
    snake_case. The commands convert the provided name to snake_case
    before creating the output file.
"""

import os
import re

from typing import Any, Dict, TYPE_CHECKING

from automojo.webworks.devexp.cli.command import CLICommand
from automojo.webworks.devexp.cli.exitcodes import EXIT_ERROR
from automojo.webworks.devexp.cli.exitcodes import EXIT_SUCCESS

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace


# =============================================================================
# Boilerplate Templates
# =============================================================================

ENDPOINT_TEMPLATE = '''"""
    Endpoint definition for {endpoint_name}.

    This module defines the ``{endpoint_name}`` endpoint which handles
    incoming HTTP requests and returns appropriate responses.
"""


def {function_name}(request):
    """
        Handle requests to the {endpoint_name} endpoint.

        :param request: The incoming HTTP request object.

        :returns: A dictionary containing the response data.
    """
    rtnval = {{"endpoint": "{endpoint_name}", "status": "ok"}}
    return rtnval
'''

BLUEPRINT_TEMPLATE = '''"""
    Blueprint definition for {blueprint_name}.

    This module defines the ``{blueprint_name}`` blueprint which groups
    related endpoints under a common URL prefix and namespace.
"""


class {class_name}Blueprint:
    """
        Blueprint for the {blueprint_name} feature.

        This blueprint organizes related endpoints and middleware
        under the ``/{url_prefix}`` URL prefix.
    """

    name = "{blueprint_name}"
    url_prefix = "/{url_prefix}"

    def __init__(self):
        """
            Initialize the {class_name}Blueprint instance.
        """
        self._routes = []
        return

    @property
    def routes(self):
        """
            The list of registered routes for this blueprint.

            :returns: A list of route definitions.
        """
        return list(self._routes)

    def register(self, app):
        """
            Register this blueprint with the application.

            :param app: The application instance to register with.
        """
        return
'''


# =============================================================================
# Helper Functions
# =============================================================================

def to_snake_case(name: str) -> str:
    """
        Convert a name string to snake_case.

        Handles conversion from camelCase, PascalCase, kebab-case,
        and names with spaces. Consecutive uppercase letters are
        treated as acronyms and kept together.

        :param name: The name string to convert.

        :returns: The snake_case version of the name.
    """
    # Replace hyphens and spaces with underscores
    result = name.replace("-", "_").replace(" ", "_")

    # Insert underscores before uppercase letters that follow lowercase
    result = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", result)

    # Insert underscores between consecutive uppercase and following lowercase
    result = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", result)

    # Convert to lowercase
    result = result.lower()

    # Collapse multiple underscores
    result = re.sub(r"_+", "_", result)

    # Strip leading and trailing underscores
    result = result.strip("_")

    return result


def to_pascal_case(name: str) -> str:
    """
        Convert a name string to PascalCase.

        Handles conversion from snake_case, kebab-case, and names
        with spaces.

        :param name: The name string to convert.

        :returns: The PascalCase version of the name.
    """
    # Split on underscores, hyphens, and spaces
    parts = re.split(r"[_\-\s]+", name)

    # Capitalize each part and join
    result = "".join(part.capitalize() for part in parts if len(part) > 0)

    return result


def generate_endpoint_content(name: str) -> str:
    """
        Generate the content for an endpoint file.

        :param name: The endpoint name as provided by the user.

        :returns: The generated Python source code for the endpoint.
    """
    snake_name = to_snake_case(name)

    content = ENDPOINT_TEMPLATE.format(
        endpoint_name=snake_name,
        function_name=snake_name
    )

    return content


def generate_blueprint_content(name: str) -> str:
    """
        Generate the content for a blueprint file.

        :param name: The blueprint name as provided by the user.

        :returns: The generated Python source code for the blueprint.
    """
    snake_name = to_snake_case(name)
    pascal_name = to_pascal_case(name)
    url_prefix = snake_name.replace("_", "-")

    content = BLUEPRINT_TEMPLATE.format(
        blueprint_name=snake_name,
        class_name=pascal_name,
        url_prefix=url_prefix
    )

    return content


def write_generated_file(file_path: str, content: str, dry_run: bool) -> int:
    """
        Write generated content to a file or preview it in dry-run mode.

        When ``dry_run`` is True, the file path and content are printed
        to standard output without writing to disk. When ``dry_run`` is
        False, the content is written to the specified file path.

        :param file_path: The absolute path to the output file.
        :param content: The generated file content.
        :param dry_run: If True, preview only without writing.

        :returns: Exit code where 0 indicates success.
    """
    if dry_run is True:
        print("Dry run: would create '{}'".format(file_path))
        print("")
        print(content)
        return EXIT_SUCCESS

    output_dir = os.path.dirname(file_path)

    if len(output_dir) > 0:
        os.makedirs(output_dir, exist_ok=True)

    if os.path.exists(file_path):
        errmsg = "Error: File '{}' already exists.".format(file_path)
        print(errmsg)
        return EXIT_ERROR

    with open(file_path, "w") as out_file:
        out_file.write(content)

    print("Created '{}'.".format(file_path))

    return EXIT_SUCCESS


# =============================================================================
# GenerateEndpointCommand
# =============================================================================

class GenerateEndpointCommand(CLICommand):
    """
        CLI command for generating an endpoint file with boilerplate code.

        The ``endpoint`` command creates a Python file containing a
        basic endpoint function definition. The generated file follows
        the repository naming conventions using snake_case for the
        file name and function name.

        Usage::

            webworks generate endpoint user-profile
            webworks generate endpoint user-profile --output-dir src/endpoints
            webworks generate endpoint user-profile --dry-run
    """

    name = "endpoint"
    help = "Generate an endpoint file with boilerplate code."

    def add_arguments(self, parser: "ArgumentParser") -> None:
        """
            Add the name positional argument and optional flags.

            :param parser: The argument parser to add arguments to.
        """
        parser.add_argument(
            "name",
            type=str,
            help="Name of the endpoint to generate."
        )

        parser.add_argument(
            "--output-dir",
            type=str,
            default=".",
            help="Directory to write the generated file. Default: current directory."
        )

        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Preview generated file without writing to disk."
        )

        return

    def execute(self, args: "Namespace", config: Dict[str, Any]) -> int:
        """
            Execute the generate endpoint command.

            Generates a Python file containing endpoint boilerplate
            code. The file name is derived from the provided name
            converted to snake_case.

            :param args: Parsed command-line arguments containing
                ``name``, ``output_dir``, and ``dry_run``.
            :param config: Loaded configuration dictionary.

            :returns: Exit code where 0 indicates success.
        """
        name = args.name
        output_dir = args.output_dir
        dry_run = args.dry_run

        snake_name = to_snake_case(name)
        file_name = "{}.py".format(snake_name)
        file_path = os.path.join(output_dir, file_name)

        content = generate_endpoint_content(name)
        exit_code = write_generated_file(file_path, content, dry_run)

        return exit_code


# =============================================================================
# GenerateBlueprintCommand
# =============================================================================

class GenerateBlueprintCommand(CLICommand):
    """
        CLI command for generating a blueprint file with standard structure.

        The ``blueprint`` command creates a Python file containing a
        blueprint class definition with standard structure including
        route registration and URL prefix configuration.

        Usage::

            webworks generate blueprint user-management
            webworks generate blueprint user-management --output-dir src/blueprints
            webworks generate blueprint user-management --dry-run
    """

    name = "blueprint"
    help = "Generate a blueprint file with standard structure."

    def add_arguments(self, parser: "ArgumentParser") -> None:
        """
            Add the name positional argument and optional flags.

            :param parser: The argument parser to add arguments to.
        """
        parser.add_argument(
            "name",
            type=str,
            help="Name of the blueprint to generate."
        )

        parser.add_argument(
            "--output-dir",
            type=str,
            default=".",
            help="Directory to write the generated file. Default: current directory."
        )

        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Preview generated file without writing to disk."
        )

        return

    def execute(self, args: "Namespace", config: Dict[str, Any]) -> int:
        """
            Execute the generate blueprint command.

            Generates a Python file containing blueprint boilerplate
            code with a class definition, route list, and registration
            method. The file name is derived from the provided name
            converted to snake_case.

            :param args: Parsed command-line arguments containing
                ``name``, ``output_dir``, and ``dry_run``.
            :param config: Loaded configuration dictionary.

            :returns: Exit code where 0 indicates success.
        """
        name = args.name
        output_dir = args.output_dir
        dry_run = args.dry_run

        snake_name = to_snake_case(name)
        file_name = "{}.py".format(snake_name)
        file_path = os.path.join(output_dir, file_name)

        content = generate_blueprint_content(name)
        exit_code = write_generated_file(file_path, content, dry_run)

        return exit_code
