"""
    .. module:: testcomponents.harness.fixtures
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Bare fixture documents for component behavior tests.

    A fixture document links the design tokens and the base stylesheet and imports the
    library barrel (``/static/javascript/index.js``) exactly as a consuming application
    does, then holds only the markup a test needs. Tests that exercise a component's
    runtime behavior (dynamic content, accessibility wiring, responsive modes) use it
    instead of a catalog page, so nothing else on the page interferes.
"""

from typing import Any, Iterable


FIXTURE_READY_TIMEOUT = 15000

FIXTURE_DOCUMENT = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>mj-* fixture</title>
  <link rel="stylesheet" href="/static/styles/tokens.css">
  <link rel="stylesheet" href="/static/styles/base.css">
  <script type="module" src="/static/javascript/index.js"></script>
</head>
<body>
__MARKUP__
</body>
</html>
"""


def load_fixture(page: Any, base_url: str, markup: str, tags: Iterable[str]) -> Any:
    """
        Load a fixture document holding ``markup`` from the site's origin and wait until
        every tag in ``tags`` is registered.

        :param page: Playwright page.
        :param base_url: Site base URL; the fixture is served from its origin so the
            library and stylesheet URLs resolve.
        :param markup: HTML placed in the fixture's ``<body>``.
        :param tags: Custom element names to wait for.

        :returns: The page, for chaining.
    """

    page.goto(base_url + "/")
    page.set_content(FIXTURE_DOCUMENT.replace("__MARKUP__", markup))
    for tag in tags:
        page.wait_for_function(
            "tag => customElements.get(tag) !== undefined",
            arg=tag,
            timeout=FIXTURE_READY_TIMEOUT,
        )
    return page
