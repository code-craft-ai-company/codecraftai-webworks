"""
    .. module:: testcomponents.harness.browsers
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Optional Playwright access and the pacing controls for the site suite.

    Playwright and its browsers are not a dependency of this repository, yet the suite
    must collect and report cleanly on a machine without them. The import is attempted
    once here; the outcome is exposed so the resource factories can turn "not installed"
    into a skip with a clear reason rather than an import error at collection time.

    Test pacing is controlled by environment variables so the same suite can run fast
    in CI or slowly for visual observation:

      MJ_TEST_SLOWMO   Milliseconds Playwright pauses between every UI action (click,
                       type, etc.). 0 (default) = no pause.
      MJ_TEST_HEADED   When set to a truthy value (1/true/yes/on), runs the browser
                       headed (visible) instead of headless, so the slowed-down
                       actions can actually be watched.

    These apply to every UI test in the suite; no per-test changes are needed.
"""

import os

from typing import Any, Dict, Optional

from ccai.errors.exceptions import SkipError


SLOWMO_VARIABLE = "MJ_TEST_SLOWMO"
HEADED_VARIABLE = "MJ_TEST_HEADED"

TRUTHY_VALUES = ("1", "true", "yes", "on")

# Why Playwright could not be imported, or None when it is available.
PLAYWRIGHT_IMPORT_ERROR: Optional[str] = None

try:
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import expect
    from playwright.sync_api import sync_playwright
except ImportError as import_error:
    PLAYWRIGHT_IMPORT_ERROR = str(import_error)

    PlaywrightError = None
    sync_playwright = None

    def expect(*args: Any, **kwargs: Any) -> Any:
        """
            Stands in for :func:`playwright.sync_api.expect` when Playwright is not
            installed. The page factory skips every test before its body runs, so this
            is only reached by a test that calls ``expect`` without a page.

            :raises SkipError: Always.
        """
        raise SkipError(unavailable_reason())


def playwright_available() -> bool:
    """
        Report whether the Playwright package imported.

        :returns: True when :func:`sync_playwright` can be used.
    """

    available = PLAYWRIGHT_IMPORT_ERROR is None
    return available


def unavailable_reason() -> str:
    """
        Build the skip reason used when Playwright cannot be imported.

        :returns: A message naming the missing package and how to install it.
    """

    reason = (
        "Playwright is not installed ({}); install it with "
        "'pip install playwright' and 'playwright install chromium' to run "
        "the testcomponents site suite.".format(PLAYWRIGHT_IMPORT_ERROR)
    )
    return reason


def require_playwright() -> None:
    """
        Skip the calling scope when Playwright is not installed.

        :raises SkipError: When the Playwright package could not be imported.
    """

    if not playwright_available():
        raise SkipError(unavailable_reason())

    return


def env_truthy(name: str) -> bool:
    """
        Read a boolean environment variable.

        :param name: The environment variable name.

        :returns: True when the value is a recognized truthy string.
    """

    raw = os.environ.get(name, "")
    truthy = raw.strip().lower() in TRUTHY_VALUES
    return truthy


def env_int(name: str, default: int) -> int:
    """
        Read a non-negative integer environment variable, tolerating bad values.

        :param name: The environment variable name.
        :param default: The value to use when unset, unparsable or negative.

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


def slowmo_milliseconds() -> int:
    """
        The pause between UI actions requested through MJ_TEST_SLOWMO.

        :returns: The pause in milliseconds; 0 when unset.
    """

    milliseconds = env_int(SLOWMO_VARIABLE, 0)
    return milliseconds


def headed_requested() -> bool:
    """
        Whether MJ_TEST_HEADED asks for a visible browser.

        :returns: True when the browser should run headed.
    """

    headed = env_truthy(HEADED_VARIABLE)
    return headed


def browser_launch_arguments() -> Dict[str, Any]:
    """
        Build the browser launch arguments, honoring MJ_TEST_SLOWMO and
        MJ_TEST_HEADED for the whole suite; they map onto Playwright's
        ``slow_mo`` and ``headless`` launch options.

        :returns: Keyword arguments for ``BrowserType.launch``.
    """

    launch_arguments: Dict[str, Any] = {"headless": True}

    slowmo = slowmo_milliseconds()
    if slowmo > 0:
        launch_arguments["slow_mo"] = slowmo

    if headed_requested():
        launch_arguments["headless"] = False

    return launch_arguments
