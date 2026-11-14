"""
    Project scaffolding commands for the webworks CLI.

    This module provides the :class:`NewProjectCommand` that creates new
    project directories with a standard structure based on configurable
    templates. The command supports ``minimal``, ``api``, and ``webapp``
    templates, each generating a different set of boilerplate files and
    directories.

    Every template generates a working application built the way the
    framework's own sample sites are: ``app.py`` establishes a web
    application persona, collects the endpoint handlers declared with
    ``Endpoint.attach_at`` and exposes the ASGI application as ``app``.
    The ``minimal`` template has a single endpoint. The ``api`` template
    adds a health endpoint, a ``RestBlueprint``, a model and a test. The
    ``webapp`` template further adds an HTML page rendered from
    ``templates/`` and assets served from ``static/``.

    A generated project is served from its own directory::

        cd my-project
        webworks serve --reload
"""

import os
import re

from typing import Any, Dict, List, TYPE_CHECKING

from ccai.webworks.devexp.cli.command import CLICommand
from ccai.webworks.devexp.cli.exitcodes import EXIT_ERROR
from ccai.webworks.devexp.cli.exitcodes import EXIT_SUCCESS

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace


# =============================================================================
# Boilerplate File Content
# =============================================================================

PROJECT_NAME_MARKER = "@@PROJECT_NAME@@"
"""Marker replaced by the project name as it was given on the command line."""

APP_NAME_MARKER = "@@APP_NAME@@"
"""Marker replaced by the one-word application name derived from the project name."""

CONFIG_TEMPLATE = '''"""
    Configuration for @@PROJECT_NAME@@.
"""

import os


# One-word name of the application; used for its persona, logger and log files.
APP_NAME = "@@APP_NAME@@"

# Directory where the application keeps its settings and log files.
PRESENCE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".presence")

# Address the development server binds to when app.py is run directly.
HOST = "127.0.0.1"
PORT = 8000
'''

_APP_HEADER = '''"""
    Application entry point for @@PROJECT_NAME@@.

    This module establishes the web application persona, declares which
    endpoints belong to the application and exposes the ASGI application
    as the module-level ``app`` variable, ready to be served by any ASGI
    server. From this directory::

        webworks serve --reload
"""

from ccai.webworks.webapplication import establish_webapp_persona
from ccai.webworks.wellknown import ThisWebApplicationSingleton

import config

'''

_APP_PERSONA = '''
webapp = establish_webapp_persona(
    name=config.APP_NAME,
    logger_name=config.APP_NAME,
    log_basename=config.APP_NAME,
    presence_dir=config.PRESENCE_DIR,
)

# Declare which endpoints belong to this application. The decorators in
# the imported modules only mark the handlers; collecting them here is
# what registers them.
'''

_APP_FOOTER = '''
webapp.startup()

# The ASGI application instance for serving
app = ThisWebApplicationSingleton().asgi_app


def run_development_server(
    host: str = config.HOST,
    port: int = config.PORT,
    debug: bool = True,
    reload: bool = True,
) -> None:
    """
        Start the application with the ASGI development server.

        :param host: The host address to bind to.
        :param port: The port number to bind to.
        :param debug: Whether to enable debug mode with verbose error pages.
        :param reload: Whether to restart the server when source files change.
    """

    from ccai.webworks.devexp.server.devserver import DevelopmentServer

    server = DevelopmentServer(app=app, debug=debug, reload=reload)

    server.serve_forever(host=host, port=port)

    return


if __name__ == "__main__":
    run_development_server()
'''

APP_TEMPLATE_MINIMAL = (
    _APP_HEADER
    + "from endpoints import handlers\n\n"
    + _APP_PERSONA
    + "webapp.registry.collect_from(handlers)\n"
    + _APP_FOOTER
)

APP_TEMPLATE_API = (
    _APP_HEADER
    + "from blueprints import items\n"
    + "from endpoints import handlers\n\n"
    + _APP_PERSONA
    + "webapp.registry.collect_from(handlers, items)\n"
    + _APP_FOOTER
)

APP_TEMPLATE_WEBAPP = (
    _APP_HEADER
    + "from blueprints import items\n"
    + "from endpoints import handlers\n"
    + "from endpoints import pages\n\n"
    + _APP_PERSONA
    + "webapp.registry.collect_from(handlers, items, pages)\n"
    + _APP_FOOTER
)

APP_TEMPLATES = {
    "minimal": APP_TEMPLATE_MINIMAL,
    "api": APP_TEMPLATE_API,
    "webapp": APP_TEMPLATE_WEBAPP,
}

ENDPOINTS_INIT_TEMPLATE = '''"""
    Endpoint handlers of @@PROJECT_NAME@@.
"""
'''

HANDLERS_TEMPLATE_MINIMAL = '''"""
    Endpoint handlers for @@PROJECT_NAME@@.

    Each handler is marked with the ``Endpoint.attach_at`` decorator and
    becomes a route when app.py collects this module.
"""

from ccai.webworks.endpoints.endpoint import Endpoint
from ccai.webworks.routing.request import Request
from ccai.webworks.routing.response import JSONResponse


@Endpoint.attach_at(path="/", methods=["GET"])
def index(request: Request) -> JSONResponse:
    """
        Handle GET requests to the root path.

        :param request: The incoming HTTP request.

        :returns: A JSONResponse containing a welcome message.
    """

    content = {"message": "Welcome to @@PROJECT_NAME@@"}
    response = JSONResponse(content=content, status_code=200)

    return response
'''

_HEALTH_HANDLER = '''

@Endpoint.attach_at(path="/api/health", methods=["GET"])
def health(request: Request) -> JSONResponse:
    """
        Handle GET requests to the health check path.

        :param request: The incoming HTTP request.

        :returns: A JSONResponse containing the health status.
    """

    content = {"status": "ok"}
    response = JSONResponse(content=content, status_code=200)

    return response
'''

HANDLERS_TEMPLATE_API = HANDLERS_TEMPLATE_MINIMAL + _HEALTH_HANDLER

HANDLERS_TEMPLATE_WEBAPP = '''"""
    API endpoint handlers for @@PROJECT_NAME@@.

    Each handler is marked with the ``Endpoint.attach_at`` decorator and
    becomes a route when app.py collects this module. The HTML pages and
    static assets are served by the ``pages`` module.
"""

from ccai.webworks.endpoints.endpoint import Endpoint
from ccai.webworks.routing.request import Request
from ccai.webworks.routing.response import JSONResponse
''' + _HEALTH_HANDLER

PAGES_TEMPLATE = '''"""
    HTML pages and static assets of @@PROJECT_NAME@@.

    The index page is rendered from ``templates/index.html`` with the
    standard library's ``string.Template``; every value is HTML-escaped
    before it is substituted. Assets under ``static/`` are served at
    ``/static/``. To use Jinja2 or Mako templates instead, install the
    matching extra (``codecraftai-webworks[jinja2]`` or ``[mako]``) and see
    ``ccai.webworks.templating``.
"""

import html
import mimetypes
import os
import string

from ccai.webworks.endpoints.endpoint import Endpoint
from ccai.webworks.routing.request import Request
from ccai.webworks.routing.response import HTMLResponse
from ccai.webworks.routing.response import Response


_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_TEMPLATES_ROOT = os.path.join(_PROJECT_ROOT, "templates")

_STATIC_ROOT = os.path.realpath(os.path.join(_PROJECT_ROOT, "static"))


def render_page(template_name: str, **values: str) -> str:
    """
        Render a template from the templates directory.

        :param template_name: The file name of the template.
        :param values: The values to substitute; each is HTML-escaped.

        :returns: The rendered HTML.
    """

    template_path = os.path.join(_TEMPLATES_ROOT, template_name)

    with open(template_path, "r", encoding="utf-8") as template_file:
        template = string.Template(template_file.read())

    escaped = {}
    for key, value in values.items():
        escaped[key] = html.escape(str(value))

    content = template.safe_substitute(escaped)

    return content


@Endpoint.attach_at(path="/", methods=["GET"])
def index(request: Request) -> HTMLResponse:
    """
        Handle GET requests to the root path.

        :param request: The incoming HTTP request.

        :returns: An HTMLResponse containing the index page.
    """

    content = render_page("index.html", title="@@PROJECT_NAME@@")
    response = HTMLResponse(content=content, status_code=200)

    return response


@Endpoint.attach_at(path="/static/{assetpath:path}", methods=["GET"])
def serve_static(request: Request) -> Response:
    """
        Serve a static asset from the static directory.

        The requested path is resolved beneath the static root and a
        traversal guard rejects any path that escapes that directory.

        :param request: The incoming HTTP request.

        :returns: A Response with the asset bytes, or a 404 Response.
    """

    relative = request.path_params.get("assetpath", "")

    candidate = os.path.realpath(os.path.join(_STATIC_ROOT, relative))

    within_root = candidate.startswith(_STATIC_ROOT + os.sep)
    if within_root is False or os.path.isfile(candidate) is False:
        not_found = Response(status_code=404, body=b"Not found")
        return not_found

    with open(candidate, "rb") as asset_file:
        data = asset_file.read()

    content_type, _encoding = mimetypes.guess_type(candidate)
    if content_type is None:
        content_type = "application/octet-stream"

    headers = {
        "Content-Type": content_type,
        "Cache-Control": "no-cache",
    }
    response = Response(status_code=200, headers=headers, body=data)

    return response
'''

BLUEPRINTS_INIT_TEMPLATE = '''"""
    Blueprints of @@PROJECT_NAME@@.

    A blueprint groups related endpoints under a shared base path.
"""
'''

ITEMS_BLUEPRINT_TEMPLATE = '''"""
    Items blueprint for @@PROJECT_NAME@@.

    ``ItemsBlueprint`` groups the item endpoints under ``/api/items``.
"""

from ccai.webworks.endpoints.doc import Doc
from ccai.webworks.endpoints.restblueprint import RestBlueprint
from ccai.webworks.routing.request import Request
from ccai.webworks.routing.response import JSONResponse

from models.item import ITEMS


class ItemsBlueprint(RestBlueprint):
    """
        Endpoints for the item records.
    """

    base_path = "/api/items"
    methods = ["GET"]
    tags = ["items"]

    @staticmethod
    @RestBlueprint.attach_at(
        leaf="list",
        methods=["GET"],
        doc=Doc(
            summary="List Items",
            description="Retrieve a list of all available items.",
        ),
    )
    def list_items(request: Request) -> JSONResponse:
        """
            Handle GET requests to the items list path.

            :param request: The incoming HTTP request.

            :returns: A JSONResponse containing all items.
        """

        content = {"items": [item.to_dict() for item in ITEMS]}
        response = JSONResponse(content=content, status_code=200)

        return response
'''

MODELS_INIT_TEMPLATE = '''"""
    Data models of @@PROJECT_NAME@@.
"""
'''

ITEM_MODEL_TEMPLATE = '''"""
    Item model for @@PROJECT_NAME@@.
"""

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class Item:
    """
        A single item record.

        :param id: The identifier of the item.
        :param name: The display name of the item.
    """

    id: int
    name: str

    def to_dict(self) -> Dict[str, Any]:
        """
            Convert the item to a dictionary for a JSON response.

            :returns: A dictionary representation of the item.
        """
        rtnval = {"id": self.id, "name": self.name}
        return rtnval


# Sample records. Replace with a real data source.
ITEMS = [
    Item(id=1, name="Widget"),
    Item(id=2, name="Gadget"),
]
'''

TESTS_INIT_TEMPLATE = '''"""
    Tests of @@PROJECT_NAME@@.
"""
'''

TEST_APP_TEMPLATE = '''"""
    Tests for the endpoints of @@PROJECT_NAME@@.

    The tests call the application in-process through the framework's
    test client; no server is started. Run them from the project
    directory so that ``app`` is importable.
"""

from ccai.webworks.devexp.testing.testclient import TestClient

import app as application


def test_health_reports_ok():
    """
        The health endpoint answers 200 with a status of "ok".
    """
    client = TestClient(application.app)

    response = client.get("/api/health")

    if response.status_code != 200:
        errmsg = "Expected status 200, got {}".format(response.status_code)
        raise AssertionError(errmsg)

    if response.json != {"status": "ok"}:
        errmsg = "Unexpected health payload: {}".format(response.json)
        raise AssertionError(errmsg)

    return


def test_items_are_listed():
    """
        The items blueprint lists the sample items.
    """
    client = TestClient(application.app)

    response = client.get("/api/items/list")

    if response.status_code != 200:
        errmsg = "Expected status 200, got {}".format(response.status_code)
        raise AssertionError(errmsg)

    if len(response.json["items"]) == 0:
        errmsg = "Expected at least one item."
        raise AssertionError(errmsg)

    return
'''

INDEX_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>$title</title>
    <link rel="stylesheet" href="/static/site.css">
</head>
<body>
    <main>
        <h1>$title</h1>
        <p>This page is rendered from <code>templates/index.html</code>.</p>
        <ul>
            <li><a href="/api/health">GET /api/health</a></li>
            <li><a href="/api/items/list">GET /api/items/list</a></li>
        </ul>
    </main>
</body>
</html>
"""

SITE_CSS_TEMPLATE = """body {
    font-family: sans-serif;
    margin: 0;
    color: #222;
    background-color: #fafafa;
}

main {
    max-width: 640px;
    margin: 2rem auto;
    padding: 0 1rem;
}

a {
    color: #0066cc;
}
"""

GITIGNORE_TEMPLATE = """.presence/
__pycache__/
*.pyc
"""

_MINIMAL_FILES: Dict[str, str] = {
    "app.py": APP_TEMPLATE_MINIMAL,
    "config.py": CONFIG_TEMPLATE,
    ".gitignore": GITIGNORE_TEMPLATE,
    "endpoints/__init__.py": ENDPOINTS_INIT_TEMPLATE,
    "endpoints/handlers.py": HANDLERS_TEMPLATE_MINIMAL,
}

_API_FILES: Dict[str, str] = {
    "app.py": APP_TEMPLATE_API,
    "config.py": CONFIG_TEMPLATE,
    ".gitignore": GITIGNORE_TEMPLATE,
    "endpoints/__init__.py": ENDPOINTS_INIT_TEMPLATE,
    "endpoints/handlers.py": HANDLERS_TEMPLATE_API,
    "blueprints/__init__.py": BLUEPRINTS_INIT_TEMPLATE,
    "blueprints/items.py": ITEMS_BLUEPRINT_TEMPLATE,
    "models/__init__.py": MODELS_INIT_TEMPLATE,
    "models/item.py": ITEM_MODEL_TEMPLATE,
    "tests/__init__.py": TESTS_INIT_TEMPLATE,
    "tests/test_app.py": TEST_APP_TEMPLATE,
}

_WEBAPP_FILES: Dict[str, str] = dict(_API_FILES)
_WEBAPP_FILES.update({
    "app.py": APP_TEMPLATE_WEBAPP,
    "endpoints/handlers.py": HANDLERS_TEMPLATE_WEBAPP,
    "endpoints/pages.py": PAGES_TEMPLATE,
    "templates/index.html": INDEX_HTML_TEMPLATE,
    "static/site.css": SITE_CSS_TEMPLATE,
})

PROJECT_FILE_CONTENTS: Dict[str, Dict[str, str]] = {
    "minimal": _MINIMAL_FILES,
    "api": _API_FILES,
    "webapp": _WEBAPP_FILES,
}
"""The files each template generates, keyed by path relative to the project root."""


# =============================================================================
# Project Templates
# =============================================================================

PROJECT_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "minimal": {
        "description": "Minimal project with single endpoint",
        "files": ["app.py", "config.py", "endpoints/"],
    },
    "api": {
        "description": "REST API project with blueprints",
        "files": ["app.py", "config.py", "endpoints/", "blueprints/", "models/", "tests/"],
    },
    "webapp": {
        "description": "Full web application with templates",
        "files": ["app.py", "config.py", "endpoints/", "blueprints/", "models/", "templates/", "static/", "tests/"],
    },
}
"""The top-level entries of each template; entries ending with ``/`` are directories."""

_PROJECT_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._\-]*$")
"""Project names are written into string literals and HTML, so the alphabet is restricted."""


# =============================================================================
# Helper Functions
# =============================================================================

def derive_app_name(project_name: str) -> str:
    """
        Derive the one-word application name from a project name.

        The persona name is used for the logger and the log files, so it is
        reduced to lowercase letters and digits. ``my-cool-app`` becomes
        ``mycoolapp``.

        :param project_name: The project name as given by the user.

        :returns: The application name; ``webapp`` when the project name
            contains no letters or digits.
    """
    app_name = re.sub(r"[^A-Za-z0-9]", "", project_name).lower()

    if len(app_name) == 0:
        app_name = "webapp"

    return app_name


def create_project_structure(project_path: str, template_name: str) -> list:
    """
        Create the project directory structure based on the selected template.

        Creates the project root directory and all files defined by the
        template in :data:`PROJECT_FILE_CONTENTS`, with the project name
        substituted into their content. Only directories of Python modules
        receive an ``__init__.py``; ``templates/`` and ``static/`` hold
        assets and are not packages.

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

    file_contents = PROJECT_FILE_CONTENTS[template_name]
    project_name = os.path.basename(os.path.normpath(project_path))
    app_name = derive_app_name(project_name)

    # The project name is written into Python string literals and HTML, so
    # it must not be able to end a literal or start a tag.
    if _PROJECT_NAME_PATTERN.match(project_name) is None:
        errmsg = (
            "Invalid project name '{}'. Use letters, digits, spaces, dots, "
            "hyphens and underscores, starting with a letter or digit.".format(project_name)
        )
        raise ValueError(errmsg)

    os.makedirs(project_path, exist_ok=False)

    created_files: List[str] = []

    for relative_path in file_contents:
        content = file_contents[relative_path]
        content = content.replace(PROJECT_NAME_MARKER, project_name)
        content = content.replace(APP_NAME_MARKER, app_name)

        path_parts = relative_path.split("/")
        file_path = os.path.join(project_path, *path_parts)

        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as out_file:
            out_file.write(content)

        created_files.append(os.path.join(*path_parts))

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

        print("")
        print("Next steps:")
        print("  cd {}".format(project_name))
        print("  webworks serve --reload")

        return EXIT_SUCCESS
