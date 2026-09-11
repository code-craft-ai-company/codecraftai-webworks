"""
    .. module:: testcomponents.tests.test_chart_library
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: The comprehensive <mj-chart> chart library.

    Tests for the comprehensive <mj-chart> chart library and its dedicated
    landing/gallery on /charts plus per-type playground pages at
    /chart-type/<type>. The per-type sweeps are defined as individual
    module-level tests named ``<check>__<type>`` so a broken chart type is
    reported by name.
"""

import ccai.testbase as testbase

from testcomponents.charttypes import chart_type_count

from testcomponents.harness.browsers import expect
from testcomponents.harness.catalogs import SAMPLE_CHART_TYPES
from testcomponents.harness.catalogs import all_chart_types
from testcomponents.harness.catalogs import identifier_for
from testcomponents.harness.factories import create_page
from testcomponents.harness.generation import define_page_tests


# One case per catalogued chart type: (identifier, (type_key, title)).
_CHART_CASES = [
    (identifier_for(type_key), (type_key, title))
    for type_key, title in all_chart_types()
]

# A representative sample for the deeper render check: (identifier, (type_key,)).
_SAMPLE_CASES = [
    (identifier_for(type_key), (type_key,))
    for type_key in SAMPLE_CHART_TYPES
]


@testbase.attach.parameter(create_page, identifier="page")
def test_chart_library_landing_lists_every_type(page, base_url):
    """
        The /charts page renders one card per catalogued chart type.
    """

    page.goto(base_url + "/charts")

    expect(page.get_by_test_id("chart-library-intro")).to_be_visible()
    cards = page.locator('[data-testid^="chart-type-card-"]')
    expect(cards).to_have_count(chart_type_count())

    return


def _check_chart_type_page_loads(page, base_url, type_key, title):
    """
        Every catalogued chart type has its own playground page that
        loads and shows the chart heading and the playground.

        :param type_key: The chart `type` key.
        :param title: The chart title.
    """

    page.goto(base_url + f"/chart-type/{type_key}")

    heading = page.get_by_test_id("chart-type-heading")
    expect(heading).to_be_visible()
    expect(heading).to_contain_text(title)
    expect(page.get_by_test_id("playground-editor")).to_be_visible()
    expect(page.get_by_test_id("playground-preview")).to_be_attached()

    return


def _check_chart_type_renders_svg(page, base_url, type_key):
    """
        A representative sample of chart types draws an SVG with marks in
        the playground preview iframe.

        :param type_key: The chart `type` key.
    """

    page.goto(base_url + f"/chart-type/{type_key}")
    handle = page.wait_for_selector("[data-testid=playground-preview]")
    frame = handle.content_frame()
    frame.wait_for_function(
        "() => customElements.get('mj-chart') !== undefined",
        timeout=15000,
    )
    page.wait_for_timeout(1200)

    info = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-chart');
            if (el === null || el.shadowRoot === null) {
                return { marks: 0 };
            }
            const sr = el.shadowRoot;
            const marks = sr.querySelectorAll(
                'svg rect, svg path, svg circle, svg line, svg polygon, svg ellipse'
            ).length;
            return { marks: marks };
        }"""
    )

    assert info["marks"] > 1, (
        f"<mj-chart type='{type_key}'> did not draw any marks "
        f"(marks={info['marks']})"
    )

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_charts_page_has_chart_library_section(page, base_url):
    """
        The Chart Library section is present and labelled correctly.
    """

    page.goto(base_url + "/charts")
    intro = page.get_by_test_id("chart-library-intro")
    expect(intro).to_be_visible()
    expect(intro).to_contain_text("Chart Library")
    expect(intro).to_contain_text("chart types")

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_chart_library_card_navigates(page, base_url):
    """
        Clicking a chart-type card opens the chart-type playground.
    """

    page.goto(base_url + "/charts")
    page.get_by_test_id("chart-type-card-bar").click()
    expect(page).to_have_url(base_url + "/chart-type/bar")
    expect(page.get_by_test_id("chart-type-heading")).to_contain_text("Bar")

    return


define_page_tests(globals(), "test_chart_type_page_loads",
                  _check_chart_type_page_loads, _CHART_CASES)
define_page_tests(globals(), "test_chart_type_renders_svg",
                  _check_chart_type_renders_svg, _SAMPLE_CASES)


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
