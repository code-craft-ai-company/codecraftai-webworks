"""
    .. module:: testcomponents.harness
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Shared resources for the testcomponents functional site suite.

    The suite under :mod:`testcomponents.tests` drives the running testcomponents site
    through a browser. Everything the tests share -- starting the site, launching the
    browser, handing each test a fresh page, reading the component catalogs and
    generating one test per catalogued component -- lives here, outside the collected
    test tree, so the tree holds only originations and tests.

    Playwright is optional. When the package or its browser is missing, the resource
    factories raise :class:`ccai.errors.exceptions.SkipError`, so the whole suite
    collects and reports as skipped instead of failing to import.
"""
