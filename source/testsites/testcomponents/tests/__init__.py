"""
    .. module:: testcomponents.tests
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Functional site suite for the testcomponents site.

    Browser tests covering the testcomponents site and the functionality of every
    one of the 139 ``mj-*`` web components. Run from the repository root with the
    virtual environment active::

        source .venv/bin/activate
        testbase testing run --root ./source/testsites/testcomponents \\
            --includes=testcomponents.tests --output=./.output/testcomponents-tests

    Only the deeper per-component interaction tests::

        testbase testing run --root ./source/testsites/testcomponents \\
            --includes=testcomponents.tests --include-marker-exp='+categories~=functional' \\
            --output=./.output/testcomponents-tests

    The suite needs Playwright and its Chromium browser (``pip install playwright``,
    ``playwright install chromium``). Without them every test is skipped with a
    reason naming the missing piece; nothing errors. MJ_TEST_SLOWMO and
    MJ_TEST_HEADED slow the browser down and make it visible, see
    :mod:`testcomponents.harness.browsers`.

    Resources: the browser and the site subprocess are created once per run here;
    each test attaches its own fresh ``page`` from
    :mod:`testcomponents.harness.factories`.
"""

import ccai.testbase as testbase

from ccai.testbase.resourcelifespan import ResourceLifespan

from testcomponents.harness.factories import create_browser_session
from testcomponents.harness.factories import create_site


# Session resources are created in origination order. The browser comes first so
# that a machine without Playwright skips the whole suite before a site subprocess
# is ever started.
testbase.originate.parameter(create_browser_session, identifier="browser_session",
                             life_span=ResourceLifespan.Session)
testbase.originate.parameter(create_site, identifier="base_url",
                             life_span=ResourceLifespan.Session)
