"""
    Tests for the testcomponents application wiring.

    This module tests that ``source/testsites/testcomponents/app.py`` registers
    every endpoint the site serves: the landing page and static routes from
    the ``handlers`` module, and the group index and per-component test page
    routes of every component group blueprint.

    The site is imported in a child process. Importing it establishes a webapp
    persona, which is process-global, and the helloworld and blueprintdemo
    wiring tests already share this process's persona; probing testcomponents
    in its own interpreter keeps it from replacing theirs.
"""

import json
import os
import subprocess
import sys

from typing import Dict, List


# Locate the testsites and packages source directories so the child process
# can import the testcomponents package and the webworks package.
_this_dir = os.path.dirname(os.path.abspath(__file__))
_source_dir = os.path.normpath(os.path.join(_this_dir, os.pardir, os.pardir, os.pardir,
    os.pardir, os.pardir, os.pardir, os.pardir))
_testsites_dir = os.path.join(_source_dir, "testsites")
_packages_dir = os.path.join(_source_dir, "packages")

# Every component group served by a RestBlueprint in
# testcomponents/endpoints/blueprints.
COMPONENT_GROUPS = [
    "selection",
    "text",
    "buttons",
    "navigation",
    "layout",
    "feedback",
    "overlays",
    "data",
    "media",
    "productivity",
    "charts",
]

# Routes served by the top-level handlers module.
HANDLER_PATHS = [
    "/",
    "/charts",
    "/static/mj-components.js",
]

# The child process prints its result on a line starting with this marker,
# so log output from the site's startup cannot be mistaken for it.
_RESULT_MARKER = "ALLOWED_METHODS="

_PROBE_CODE = (
    "import json\n"
    "import sys\n"
    "import testcomponents.app as application\n"
    "paths = json.loads(sys.argv[1])\n"
    "allowed = {}\n"
    "for path in paths:\n"
    "    allowed[path] = application.router.get_allowed_methods(path)\n"
    f"print({_RESULT_MARKER!r} + json.dumps(allowed))\n"
)

PROBE_TIMEOUT = 120


def _probe_allowed_methods(paths: List[str]) -> Dict[str, List[str]]:
    """
        Import the testcomponents site in a child process and ask its router
        which methods each path allows.

        :param paths: The request paths to probe.

        :returns: A mapping of each path to the methods its router allows.

        :raises AssertionError: If the child process fails or prints no result.
    """
    env = dict(os.environ)
    python_path_entries = [_testsites_dir, _packages_dir]
    existing_python_path = env.get("PYTHONPATH")
    if existing_python_path is not None and len(existing_python_path) > 0:
        python_path_entries.append(existing_python_path)
    env["PYTHONPATH"] = os.pathsep.join(python_path_entries)

    completed = subprocess.run(
        [sys.executable, "-c", _PROBE_CODE, json.dumps(paths)],
        env=env,
        capture_output=True,
        text=True,
        timeout=PROBE_TIMEOUT,
    )

    result_line = None
    for line in completed.stdout.splitlines():
        if line.startswith(_RESULT_MARKER):
            result_line = line
            break

    if completed.returncode != 0 or result_line is None:
        errmsg_lines = [
            "Importing testcomponents.app in a child process did not report the router's routes.",
            f"RETURN CODE: {completed.returncode}",
            "STDOUT:",
            completed.stdout,
            "STDERR:",
            completed.stderr,
        ]
        errmsg = os.linesep.join(errmsg_lines)
        raise AssertionError(errmsg)

    allowed = json.loads(result_line[len(_RESULT_MARKER):])
    return allowed


def test_router_serves_group_blueprint_routes():
    """
        Test that every component group blueprint's index and component test
        page routes are registered with GET, alongside the handlers routes.
    """

    expected_paths = list(HANDLER_PATHS)
    for group in COMPONENT_GROUPS:
        expected_paths.append(f"/components/{group}")
        expected_paths.append(f"/components/{group}/mj-probe")

    allowed = _probe_allowed_methods(expected_paths)

    missing_paths = []
    for path in expected_paths:
        path_methods = allowed.get(path, [])
        if "GET" not in path_methods:
            missing_paths.append(f"    {path}: {path_methods}")

    if len(missing_paths) > 0:
        errmsg_lines = [
            "The testcomponents router does not serve GET for these paths:",
        ]
        errmsg_lines.extend(missing_paths)
        errmsg_lines.append("The group blueprint modules must be collected by app.py alongside 'handlers'.")
        errmsg = os.linesep.join(errmsg_lines)
        raise AssertionError(errmsg)

    return
