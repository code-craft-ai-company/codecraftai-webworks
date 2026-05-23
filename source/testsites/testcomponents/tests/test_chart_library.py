"""
    test_chart_library.py

    Playwright tests for the comprehensive <mj-chart> chart library and
    its dedicated landing/gallery on /charts plus per-type playground
    pages at /chart-type/<type>.
"""

import sys

import pytest
from playwright.sync_api import expect


def _charts():
    """
        Resolve the chart-type catalog for parametrization.
    """

    sys.path  # forces conftest path setup to have run
    from testcomponents.charttypes import CHART_TYPE_CATALOG

    entries = []
    for doc in CHART_TYPE_CATALOG:
        entries.append(pytest.param(doc.type_key, doc.title, id=doc.type_key))
    return entries


def _sample_charts():
    """
        A small representative sample for the deeper render check.
    """

    sample = [
        "bar", "line", "area", "pie", "donut", "scatter", "bubble",
        "sankey", "treemap", "sunburst", "histogram", "boxplot",
        "heatmap", "choropleth", "gantt", "timeline", "polar",
        "radar", "ohlc", "candlestick", "gauge", "kpi", "funnel",
        "network", "calendar-heatmap", "sparkline", "step",
    ]
    return [pytest.param(t, id=t) for t in sample]


def test_chart_library_landing_lists_every_type(page, base_url):
    """
        The /charts page renders one card per catalogued chart type.
    """

    from testcomponents.charttypes import chart_type_count

    page.goto(base_url + "/charts")

    expect(page.get_by_test_id("chart-library-intro")).to_be_visible()
    cards = page.locator('[data-testid^="chart-type-card-"]')
    expect(cards).to_have_count(chart_type_count())

    return


@pytest.mark.parametrize("type_key, title", _charts())
def test_chart_type_page_loads(page, base_url, type_key, title):
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


@pytest.mark.parametrize("type_key", _sample_charts())
def test_chart_type_renders_svg(page, base_url, type_key):
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


def test_chart_library_card_navigates(page, base_url):
    """
        Clicking a chart-type card opens the chart-type playground.
    """

    page.goto(base_url + "/charts")
    page.get_by_test_id("chart-type-card-bar").click()
    expect(page).to_have_url(base_url + "/chart-type/bar")
    expect(page.get_by_test_id("chart-type-heading")).to_contain_text("Bar")

    return
