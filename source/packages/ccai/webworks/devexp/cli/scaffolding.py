"""
    Project scaffolding commands for the webworks CLI.

    This module provides the :class:`NewProjectCommand` that creates new
    project directories with a standard structure based on configurable
    templates. The command supports ``minimal``, ``api``, and ``webapp``
    templates, each generating a different set of boilerplate files and
    directories.

    Templates define the files and directories created for each project
    type. The ``minimal`` template creates a simple project with a single
    endpoint. The ``api`` template adds blueprints, models, and tests
    directories. The ``webapp`` template further adds templates and static
    asset directories.
"""

import os

from typing import Any, Dict, TYPE_CHECKING

from ccai.webworks.devexp.cli.command import CLICommand
from ccai.webworks.devexp.cli.exitcodes import EXIT_ERROR
from ccai.webworks.devexp.cli.exitcodes import EXIT_SUCCESS

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace


# =============================================================================
# Project Templates
# =============================================================================

PROJECT_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "minimal": {
        "description": "Minimal project with single endpoint",
        "files": ["app.py", "config.py"],
    },
    "api": {
        "description": "REST API project with blueprints",
        "files": ["app.py", "config.py", "blueprints/", "models/", "tests/"],
    },
    "webapp": {
        "description": "Full web application with templates",
        "files": ["app.py", "config.py", "blueprints/", "models/", "templates/", "static/", "tests/"],
    },
}


# =============================================================================
# Boilerplate File Content
# =============================================================================

APP_TEMPLATE_MINIMAL = '''"""
    Application entry point for {project_name}.
"""

from ccai.webworks.asgi.application import ASGIApplication


app = ASGIApplication()


@app.route("/")
def index():
    """
        Default index endpoint.

        :returns: A welcome message dictionary.
    """
    rtnval = {{"message": "Welcome to {project_name}"}}
    return rtnval
'''

APP_TEMPLATE_API = '''"""
    Application entry point for {project_name}.
"""

from ccai.webworks.asgi.application import ASGIApplication


app = ASGIApplication()


@app.route("/")
def index():
    """
        Default index endpoint.

        :returns: A welcome message dictionary.
    """
    rtnval = {{"message": "Welcome to {project_name}"}}
    return rtnval


@app.route("/api/health")
def health():
    """
        Health check endpoint.

        :returns: A status dictionary.
    """
    rtnval = {{"status": "ok"}}
    return rtnval
'''

APP_TEMPLATE_WEBAPP = '''"""
    Application entry point for {project_name}.
"""

from ccai.webworks.asgi.application import ASGIApplication


app = ASGIApplication()


@app.route("/")
def index():
    """
        Default index endpoint.

        :returns: A welcome message dictionary.
    """
    rtnval = {{"message": "Welcome to {project_name}"}}
    return rtnval


@app.route("/api/health")
def health():
    """
        Health check endpoint.

        :returns: A status dictionary.
    """
    rtnval = {{"status": "ok"}}
    return rtnval
'''

CONFIG_TEMPLATE = '''"""
    Configuration for {project_name}.
"""


DEFAULT_CONFIG = {{
    "app_name": "{project_name}",
    "debug": True,
    "host": "127.0.0.1",
    "port": 8000,
}}
'''

APP_TEMPLATES = {
    "minimal": APP_TEMPLATE_MINIMAL,
    "api": APP_TEMPLATE_API,
    "webapp": APP_TEMPLATE_WEBAPP,
}


# =============================================================================
# Helper Functions
# =============================================================================

def create_project_structure(project_path: str, template_name: str) -> list:
    """
        Create the project directory structure based on the selected template.

        Creates the project root directory and all files and subdirectories
        defined by the template. Boilerplate content is written to ``app.py``
        and ``config.py`` files. Directories listed in the template (entries
        ending with ``/``) are created with an empty ``__init__.py`` file.

        :param project_path: The absolute or relative path to the project
            root directory to create.
        :param template_name: The name of the template to use. Must be a
            key in :data:`PROJECT_TEMPLATES`.

        :returns: A list of file paths that were created, relative to the
            project root.

        :raises: ValueError, OSError
    """
    if template_name not in PROJECT_TEMPLATES:
        errmsg = "Unknown template '{}'. Available templates: {}".format(
            template_name, ", ".join(sorted(PROJECT_TEMPLATES.keys()))
        )
        raise ValueError(errmsg)

    template = PROJECT_TEMPLATES[template_name]
    project_name = os.path.basename(project_path)

    os.makedirs(project_path, exist_ok=False)

    created_files = []

    for entry in template["files"]:
        is_directory = entry.endswith("/")

        if is_directory:
            dir_name = entry.rstrip("/")
            dir_path = os.path.join(project_path, dir_name)
            os.makedirs(dir_path, exist_ok=True)

            init_path = os.path.join(dir_path, "__init__.py")
            with open(init_path, "w") as init_file:
                init_file.write("")

            created_files.append(os.path.join(dir_name, "__init__.py"))
        else:
            file_path = os.path.join(project_path, entry)

            if entry == "app.py":
                app_content = APP_TEMPLATES.get(template_name, APP_TEMPLATE_MINIMAL)
                content = app_content.format(project_name=project_name)
            elif entry == "config.py":
                content = CONFIG_TEMPLATE.format(project_name=project_name)
            else:
                content = ""

            with open(file_path, "w") as out_file:
                out_file.write(content)

            created_files.append(entry)

    return created_files


# =============================================================================
# NewProjectCommand
# =============================================================================

class NewProjectCommand(CLICommand):
    """
        CLI command for creating a new project with standard structure.

        The ``new`` command creates a project directory populated with
        boilerplate files based on the selected template. The default
        template is ``minimal`` which creates a simple project with a
        single endpoint and configuration file.

        Usage::

            webworks new my-project
            webworks new my-project --template api
            webworks new my-project --template webapp
    """

    name = "new"
    help = "Create a new project with standard structure."

    def add_arguments(self, parser: "ArgumentParser") -> None:
        """
            Add the project-name positional argument and --template option.

            :param parser: The argument parser to add arguments to.
        """
        parser.add_argument(
            "project_name",
            type=str,
            help="Name of the project to create."
        )

        template_choices = sorted(PROJECT_TEMPLATES.keys())
        parser.add_argument(
            "--template",
            type=str,
            choices=template_choices,
            default="minimal",
            help="Project template to use. Default: minimal."
        )

        return

    def execute(self, args: "Namespace", config: Dict[str, Any]) -> int:
        """
            Execute the new project command.

            Creates the project directory and populates it with files
            based on the selected template. If the project directory
            already exists, an error message is printed and the command
            returns ``EXIT_ERROR``.

            :param args: Parsed command-line arguments containing
                ``project_name`` and ``template``.
            :param config: Loaded configuration dictionary.

            :returns: Exit code where 0 indicates success.
        """
        project_name = args.project_name
        template_name = args.template

        project_path = os.path.join(os.getcwd(), project_name)

        if os.path.exists(project_path):
            errmsg = "Error: Directory '{}' already exists.".format(project_name)
            print(errmsg)
            return EXIT_ERROR

        try:
            created_files = create_project_structure(project_path, template_name)
        except (ValueError, OSError) as err:
            errmsg = "Error: {}".format(str(err))
            print(errmsg)
            return EXIT_ERROR

        print("Created project '{}' with template '{}'.".format(project_name, template_name))

        for file_entry in created_files:
            print("  {}".format(file_entry))

        return EXIT_SUCCESS
