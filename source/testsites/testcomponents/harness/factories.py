"""
    .. module:: testcomponents.harness.factories
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Resource factories for the testcomponents functional site suite.

    Three resources make up the harness:

      * :func:`create_browser_session` -- one Playwright driver and browser for the
        whole run (Session lifespan). Skips the run when Playwright or its browser is
        unavailable.
      * :func:`create_site` -- the testcomponents site, started in a subprocess on a
        free port for the whole run (Session lifespan). Yields its base URL.
      * :func:`create_page` -- a fresh browser context and page for one test (Test
        lifespan), so no test sees another's state.

    The Session resources are originated in :mod:`testcomponents.tests`; the page is
    attached to each test with ``@testbase.attach.parameter``.
"""

import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

from typing import Any, Dict, Generator

import ccai.testbase as testbase

from ccai.errors.exceptions import SkipError

from testcomponents.harness import browsers


# ---- Path resolution -----------------------------------------------------

_HARNESS_DIR = os.path.dirname(os.path.abspath(__file__))
_TESTCOMPONENTS_DIR = os.path.dirname(_HARNESS_DIR)
_TESTSITES_DIR = os.path.dirname(_TESTCOMPONENTS_DIR)
_SOURCE_DIR = os.path.dirname(_TESTSITES_DIR)
_REPO_ROOT = os.path.dirname(_SOURCE_DIR)
_PACKAGES_DIR = os.path.join(_SOURCE_DIR, "packages")

# The launch code the site subprocess runs. The port is filled in per run.
SITE_LAUNCH_CODE = (
    "import testcomponents.app as application\n"
    "application.run_development_server("
    "host='127.0.0.1', port={port}, debug=False, reload=False)\n"
)

SITE_START_TIMEOUT = 30.0
SITE_STOP_TIMEOUT = 10.0
SITE_POLL_INTERVAL = 0.4


class BrowserSession:
    """
        Owns the Playwright driver and the one browser launched for a test run.

        Both handles must outlive every test and be released together at the end
        of the run, which is why they travel as one resource.
    """

    def __init__(self, driver: Any, browser: Any, launch_arguments: Dict[str, Any]):
        """
            :param driver: The started Playwright driver (``sync_playwright().start()``).
            :param browser: The launched browser.
            :param launch_arguments: The arguments the browser was launched with.
        """

        self._driver = driver
        self._browser = browser
        self._launch_arguments = launch_arguments
        return

    @property
    def browser(self) -> Any:
        """
            The launched browser.

            :returns: The Playwright ``Browser``.
        """

        return self._browser

    @property
    def launch_arguments(self) -> Dict[str, Any]:
        """
            The arguments the browser was launched with, for diagnostics.

            :returns: A copy of the launch keyword arguments.
        """

        return dict(self._launch_arguments)

    def new_page(self) -> Any:
        """
            Open a page in a fresh, isolated browser context.

            :returns: The new ``Page``; close its ``context`` to release it.
        """

        context = self._browser.new_context()
        page = context.new_page()
        return page

    def close(self) -> None:
        """
            Close the browser and stop the driver.

            :returns: ``None``
        """

        self._browser.close()
        self._driver.stop()
        return


@testbase.register.resource_factory()
def create_browser_session() -> Generator[BrowserSession, None, None]:
    """
        Launch one Chromium browser for the whole run, honoring MJ_TEST_SLOWMO and
        MJ_TEST_HEADED, and close it when the run ends.

        :returns: A generator yielding the :class:`BrowserSession`.

        :raises SkipError: When Playwright is not installed, or its Chromium browser
            is not installed (``playwright install chromium``).
    """

    browsers.require_playwright()

    launch_arguments = browsers.browser_launch_arguments()

    driver = browsers.sync_playwright().start()
    try:
        browser = driver.chromium.launch(**launch_arguments)
    except browsers.PlaywrightError as launch_error:
        driver.stop()
        reason = (
            "Playwright could not launch Chromium; install the browser with "
            "'playwright install chromium'. Launch error: {}".format(launch_error)
        )
        raise SkipError(reason) from launch_error

    session = BrowserSession(driver, browser, launch_arguments)
    try:
        yield session
    finally:
        session.close()

    return


def find_free_port() -> int:
    """
        Find an unused TCP port on the loopback interface.

        :returns: An available port number.
    """

    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
    probe.close()
    return port


def wait_until_serving(url: str, timeout: float = SITE_START_TIMEOUT) -> bool:
    """
        Poll a URL until it responds 200 or the timeout elapses.

        :param url: The URL to poll.
        :param timeout: Maximum seconds to wait.

        :returns: True when the server responded, False on timeout.
    """

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status == 200:
                    return True
        except (urllib.error.URLError, ConnectionError, OSError):
            time.sleep(SITE_POLL_INTERVAL)

    return False


def site_environment() -> Dict[str, str]:
    """
        Build the environment for the site subprocess, with the testsites and
        packages trees ahead of any inherited PYTHONPATH.

        :returns: The environment mapping for :class:`subprocess.Popen`.
    """

    environment = os.environ.copy()

    python_path_parts = [_TESTSITES_DIR, _PACKAGES_DIR]
    existing = environment.get("PYTHONPATH", "")
    if existing != "":
        python_path_parts.append(existing)
    environment["PYTHONPATH"] = os.pathsep.join(python_path_parts)

    return environment


@testbase.register.resource_factory()
def create_site() -> Generator[str, None, None]:
    """
        Start the testcomponents site in a subprocess on a free port for the whole
        run, and stop it when the run ends.

        :returns: A generator yielding the site's base URL, e.g. ``http://127.0.0.1:41234``.

        :raises RuntimeError: When the site does not answer within
            :data:`SITE_START_TIMEOUT` seconds; the subprocess output is included.
    """

    port = find_free_port()
    site_url = "http://127.0.0.1:{}".format(port)

    process = subprocess.Popen(
        [sys.executable, "-c", SITE_LAUNCH_CODE.format(port=port)],
        cwd=_REPO_ROOT,
        env=site_environment(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    ready = wait_until_serving(site_url + "/", timeout=SITE_START_TIMEOUT)
    if ready is False:
        process.terminate()
        captured = b""
        if process.stdout is not None:
            captured = process.stdout.read()
        raise RuntimeError(
            "testcomponents site did not start on {}.\n{}".format(
                site_url, captured.decode("utf-8", "replace"))
        )

    try:
        yield site_url
    finally:
        process.terminate()
        try:
            process.wait(timeout=SITE_STOP_TIMEOUT)
        except subprocess.TimeoutExpired:
            process.kill()

    return


@testbase.register.resource_factory()
def create_page(browser_session: BrowserSession) -> Generator[Any, None, None]:
    """
        Open a page in a fresh browser context for one test and close the context
        afterwards. Each test therefore starts with no cookies, storage or open
        pages from the tests before it.

        :param browser_session: The run's :class:`BrowserSession`, injected from the
            Session-scoped ``browser_session`` origination.

        :returns: A generator yielding the Playwright ``Page``.
    """

    page = browser_session.new_page()
    try:
        yield page
    finally:
        page.context.close()

    return
