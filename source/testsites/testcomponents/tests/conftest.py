"""
    conftest.py

    Pytest + Playwright fixtures for the testcomponents site test suite.

    A single session-scoped fixture starts the testcomponents webworks
    site in a subprocess on a free port and tears it down at the end of
    the run. Tests use the Playwright ``page`` fixture (from the
    pytest-playwright plugin) together with the ``base_url`` fixture.

    Test pacing is controlled by environment variables so the same suite
    can run fast in CI or slowly for visual observation:

      MJ_TEST_SLOWMO   Milliseconds Playwright pauses between every UI
                       action (click, type, etc.). 0 (default) = no pause.
                       e.g. MJ_TEST_SLOWMO=400 pytest
      MJ_TEST_HEADED   When set to a truthy value (1/true/yes), runs the
                       browser headed (visible) instead of headless, so the
                       slowed-down actions can actually be watched.
                       e.g. MJ_TEST_HEADED=1 MJ_TEST_SLOWMO=400 pytest

    These apply to every UI test in the suite -- no per-test changes are
    needed. They are equivalent to Playwright's ``slow_mo`` launch option
    and the pytest-playwright ``--slowmo`` / ``--headed`` flags.
"""

import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

import pytest


# ---- Path resolution -----------------------------------------------------

_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
_TESTCOMPONENTS_DIR = os.path.dirname(_TESTS_DIR)
_TESTSITES_DIR = os.path.dirname(_TESTCOMPONENTS_DIR)
_SOURCE_DIR = os.path.dirname(_TESTSITES_DIR)
_REPO_ROOT = os.path.dirname(_SOURCE_DIR)
_PACKAGES_DIR = os.path.join(_SOURCE_DIR, "packages")

# Make the testcomponents package importable inside the test process so
# tests can read the component catalog for parametrization.
if _TESTSITES_DIR not in sys.path:
    sys.path.insert(0, _TESTSITES_DIR)
if _PACKAGES_DIR not in sys.path:
    sys.path.insert(0, _PACKAGES_DIR)


def _env_truthy(name: str) -> bool:
    """
        Read a boolean environment variable.

        :param name: The environment variable name.

        :returns: True when the value is a recognized truthy string.
    """

    raw = os.environ.get(name, "")
    truthy = raw.strip().lower() in ("1", "true", "yes", "on")
    return truthy


def _env_int(name: str, default: int) -> int:
    """
        Read an integer environment variable, tolerating bad values.

        :param name: The environment variable name.
        :param default: The value to use when unset or unparsable.

        :returns: The parsed integer, or the default.
    """

    raw = os.environ.get(name, "")
    if raw.strip() == "":
        return default

    try:
        value = int(raw)
    except ValueError:
        return default

    if value < 0:
        return default

    return value


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args: dict) -> dict:
    """
        Override the pytest-playwright browser launch arguments so the
        whole suite honors the MJ_TEST_SLOWMO and MJ_TEST_HEADED
        environment variables.

        :param browser_type_launch_args: The launch args from the plugin.

        :returns: The launch args, with slow_mo / headless applied.
    """

    launch_args = dict(browser_type_launch_args)

    slowmo_ms = _env_int("MJ_TEST_SLOWMO", 0)
    if slowmo_ms > 0:
        launch_args["slow_mo"] = slowmo_ms

    if _env_truthy("MJ_TEST_HEADED") is True:
        launch_args["headless"] = False

    return launch_args


def _find_free_port() -> int:
    """
        Find an unused TCP port on the loopback interface.

        :returns: An available port number.
    """

    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
    probe.close()
    return port


def _wait_until_serving(url: str, timeout: float = 30.0) -> bool:
    """
        Poll a URL until it responds or the timeout elapses.

        :param url: The URL to poll.
        :param timeout: Maximum seconds to wait.

        :returns: True when the server responded, False on timeout.
    """

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                status = response.status
                if status == 200:
                    return True
        except (urllib.error.URLError, ConnectionError, OSError):
            time.sleep(0.4)

    return False


@pytest.fixture(scope="session")
def base_url() -> str:
    """
        Start the testcomponents site in a subprocess and yield its URL.

        :returns: The base URL of the running site.
    """

    port = _find_free_port()

    environment = os.environ.copy()
    python_path_parts = [_TESTSITES_DIR, _PACKAGES_DIR]
    existing = environment.get("PYTHONPATH", "")
    if existing != "":
        python_path_parts.append(existing)
    environment["PYTHONPATH"] = os.pathsep.join(python_path_parts)

    launch_code = (
        "import testcomponents.app as application\n"
        "application.run_development_server("
        f"host='127.0.0.1', port={port}, debug=False, reload=False)\n"
    )

    process = subprocess.Popen(
        [sys.executable, "-c", launch_code],
        cwd=_REPO_ROOT,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    site_url = f"http://127.0.0.1:{port}"

    ready = _wait_until_serving(site_url + "/", timeout=30.0)
    if ready is False:
        process.terminate()
        captured = b""
        if process.stdout is not None:
            captured = process.stdout.read()
        raise RuntimeError(
            "testcomponents site did not start.\n" + captured.decode("utf-8", "replace")
        )

    yield site_url

    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()

    return


def all_components() -> "list[tuple[str, str, str]]":
    """
        Return every catalogued component as (group_key, tag, title).

        :returns: A list of (group, tag, title) tuples for parametrization.
    """

    from testcomponents.catalog import CATALOG

    entries = []
    for group_key in CATALOG:
        for doc in CATALOG[group_key]:
            entries.append((group_key, doc.tag, doc.title))

    return entries


def all_groups() -> "list[tuple[str, str]]":
    """
        Return every component group as (group_key, title).

        :returns: A list of (group_key, title) tuples for parametrization.
    """

    from testcomponents.catalog.groups import GROUP_ORDER

    groups = []
    for group in GROUP_ORDER:
        groups.append((group.key, group.title))

    return groups
