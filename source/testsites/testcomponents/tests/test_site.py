"""
    .. module:: testcomponents.tests.test_site
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Site-level tests for the testcomponents site.

    Site-level tests for the testcomponents site: the landing pages and their
    filters, group index pages, navigation (including previous / next links),
    theme switching, the counts in the header, static assets and their cache
    validators, the chart-part pages, and not-found handling.
"""

import urllib.error
import urllib.request

import ccai.testbase as testbase

from testcomponents.catalog import component_neighbours
from testcomponents.catalog import group_components
from testcomponents.catalog import total_component_count
from testcomponents.charttypes import CHART_PARTS
from testcomponents.charttypes import chart_type_count
from testcomponents.harness.browsers import expect
from testcomponents.harness.catalogs import all_groups
from testcomponents.harness.catalogs import identifier_for
from testcomponents.harness.factories import create_page
from testcomponents.harness.generation import define_page_tests


def _count_label(count: int, singular: str, plural: str) -> str:
    """
        Format a count the way the site does.

        :param count: The count.
        :param singular: The noun for one.
        :param plural: The noun for any other count.

        :returns: e.g. "143 components".
    """

    noun = singular if count == 1 else plural
    label = "{} {}".format(count, noun)
    return label


@testbase.attach.parameter(create_page, identifier="page")
def test_browse_page_loads(page, base_url):
    """
        The browse page loads and shows its heading and component count.
    """

    page.goto(base_url + "/")

    heading = page.get_by_test_id("browse-heading")
    expect(heading).to_be_visible()

    count = page.get_by_test_id("component-count")
    expect(count).to_have_text(_count_label(total_component_count(), "component", "components"))

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_browse_page_shows_all_groups(page, base_url):
    """
        The browse page renders a section for every component group.
    """

    page.goto(base_url + "/")

    groups = all_groups()
    for group_key, _title in groups:
        section = page.get_by_test_id(f"group-{group_key}")
        expect(section).to_be_visible()

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_browse_page_lists_every_component(page, base_url):
    """
        The browse page renders a card for every catalogued component.
    """

    page.goto(base_url + "/")

    cards = page.locator('[data-testid^="card-mj-"]')
    expect(cards).to_have_count(total_component_count())

    return


def _check_group_index_page_loads(page, base_url, group_key, title):
    """
        Each group index page loads and shows the group heading.

        :param group_key: The group key under test.
        :param title: The group title.
    """

    page.goto(base_url + f"/components/{group_key}")

    heading = page.get_by_test_id("group-heading")
    expect(heading).to_be_visible()
    expect(heading).to_have_text(title)

    cards = page.get_by_test_id("group-cards").locator(".card")
    count = cards.count()
    assert count > 0

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_group_link_navigates_from_browse(page, base_url):
    """
        Clicking a group link on the browse page navigates to that group.
    """

    page.goto(base_url + "/")
    page.get_by_test_id("group-link-buttons").click()

    expect(page).to_have_url(base_url + "/components/buttons")
    expect(page.get_by_test_id("group-heading")).to_be_visible()

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_component_card_navigates_to_test_page(page, base_url):
    """
        Clicking a component card opens that component's test page.
    """

    page.goto(base_url + "/components/buttons")
    page.get_by_test_id("card-mj-button").click()

    expect(page).to_have_url(base_url + "/components/buttons/mj-button")
    expect(page.get_by_test_id("component-heading")).to_be_visible()

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_theme_toggle_switches_theme(page, base_url):
    """
        The header theme toggle flips the document data-theme attribute.
    """

    page.goto(base_url + "/")

    root = page.locator("html")
    expect(root).to_have_attribute("data-theme", "light")

    page.get_by_test_id("theme-toggle").click()
    expect(root).to_have_attribute("data-theme", "dark")

    page.get_by_test_id("theme-toggle").click()
    expect(root).to_have_attribute("data-theme", "light")

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_brand_link_returns_home(page, base_url):
    """
        The header brand link returns to the browse page.
    """

    page.goto(base_url + "/components/buttons/mj-button")
    page.get_by_test_id("site-brand").click()

    expect(page).to_have_url(base_url + "/")
    expect(page.get_by_test_id("browse-heading")).to_be_visible()

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_unknown_component_returns_not_found(page, base_url):
    """
        Requesting an unknown component renders the not-found page.
    """

    response = page.goto(base_url + "/components/buttons/mj-does-not-exist")

    assert response is not None
    assert response.status == 404
    expect(page.get_by_test_id("not-found")).to_be_visible()

    return


@testbase.parametrize(
    "asset_path,expected_type",
    [
        ("/static/javascript/index.js", "text/javascript"),
        ("/static/styles/tokens.css", "text/css"),
        ("/static/javascript/components/mjbutton.js", "text/javascript"),
    ],
)
def test_static_asset_content_type(base_url, asset_path, expected_type):
    """
        Static assets respond 200 with the expected content type.

        :param asset_path: The asset path under /static.
        :param expected_type: The expected Content-Type prefix.
    """

    with urllib.request.urlopen(base_url + asset_path, timeout=10) as response:
        assert response.status == 200, asset_path
        content_type = response.headers.get("Content-Type", "")
        assert expected_type in content_type, (asset_path, content_type)

    return


# --------------------------------------------------------------------------
# Charts landing page and the Components/Charts header toggle.
# --------------------------------------------------------------------------


@testbase.attach.parameter(create_page, identifier="page")
def test_charts_page_loads(page, base_url):
    """
        The dedicated Charts landing page loads and shows its heading and
        both chart sections.
    """

    page.goto(base_url + "/charts")

    expect(page.get_by_test_id("charts-heading")).to_be_visible()
    expect(page.get_by_test_id("charts-section-project")).to_be_visible()
    expect(page.get_by_test_id("charts-section-viz")).to_be_visible()

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_charts_page_lists_all_charts(page, base_url):
    """
        The Charts page lists every chart component -- the whole `charts`
        group plus the 5 data-visualization components of `media` -- the
        chart parts, and every chart type.
    """

    page.goto(base_url + "/charts")

    project = page.get_by_test_id("charts-cards-project").locator(".card")
    viz = page.get_by_test_id("charts-cards-viz").locator(".card")
    parts = page.get_by_test_id("charts-cards-parts").locator(".card")
    chart_types = page.locator('[data-testid^="chart-type-card-"]')

    expect(project).to_have_count(len(group_components("charts")))
    expect(viz).to_have_count(5)
    expect(parts).to_have_count(len(CHART_PARTS))
    expect(chart_types).to_have_count(chart_type_count())

    return


@testbase.attach.parameter(create_page, identifier="page")
@testbase.parametrize(
    "path",
    [
        "/",
        "/charts",
        "/components/buttons",
        "/components/buttons/mj-button",
        "/components/charts/mj-velocity-chart",
    ],
)
def test_view_toggle_present_on_every_page(page, base_url, path):
    """
        The Components/Charts toggle appears in the header of every page.

        :param path: The page path under test.
    """

    page.goto(base_url + path)

    toggle = page.get_by_test_id("view-toggle")
    expect(toggle).to_be_visible()
    expect(page.get_by_test_id("view-link-components")).to_be_visible()
    expect(page.get_by_test_id("view-link-charts")).to_be_visible()

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_view_toggle_navigates_between_landing_pages(page, base_url):
    """
        The header toggle switches back and forth between the Components
        and Charts landing pages.
    """

    page.goto(base_url + "/")
    page.get_by_test_id("view-link-charts").click()
    expect(page).to_have_url(base_url + "/charts")
    expect(page.get_by_test_id("charts-heading")).to_be_visible()

    page.get_by_test_id("view-link-components").click()
    expect(page).to_have_url(base_url + "/")
    expect(page.get_by_test_id("browse-heading")).to_be_visible()

    return


@testbase.attach.parameter(create_page, identifier="page")
@testbase.parametrize(
    "path,active",
    [
        ("/", "components"),
        ("/charts", "charts"),
        ("/components/buttons/mj-button", "components"),
        ("/components/charts/mj-velocity-chart", "charts"),
        ("/components/media/mj-chart", "charts"),
    ],
)
def test_view_toggle_marks_active_view(page, base_url, path, active):
    """
        The toggle marks the link matching the current page as active --
        chart pages activate Charts, the rest activate Components.

        :param path: The page path under test.
        :param active: The expected active view, "components" or "charts".
    """

    page.goto(base_url + path)

    active_link = page.get_by_test_id(f"view-link-{active}")
    expect(active_link).to_have_attribute("aria-current", "page")

    return


# --------------------------------------------------------------------------
# Counts, filters, previous / next links.
# --------------------------------------------------------------------------


@testbase.attach.parameter(create_page, identifier="page")
@testbase.parametrize(
    "path",
    ["/", "/charts", "/components/buttons/mj-button", "/chart-type/bar", "/chart-part/mj-chart-legend"],
)
def test_header_counts_come_from_the_catalogs(page, base_url, path):
    """
        Every page shows the same component and chart-type counts, derived
        from the catalogs.

        :param path: The page path under test.
    """

    page.goto(base_url + path)

    expect(page.get_by_test_id("component-count")).to_have_text(
        _count_label(total_component_count(), "component", "components"))
    expect(page.get_by_test_id("chart-type-count")).to_have_text(
        _count_label(chart_type_count(), "chart type", "chart types"))

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_browse_filter_narrows_the_cards(page, base_url):
    """
        The browse page filter keeps the cards whose tag, title or summary
        match, hides groups without a match, shows an empty state, and is
        kept in the URL.
    """

    page.goto(base_url + "/")
    cards = page.locator('[data-testid^="card-mj-"]')
    visible_cards = page.locator('[data-testid^="card-mj-"]:visible')

    page.get_by_test_id("catalog-filter").fill("dialog")
    expect(page.get_by_test_id("card-mj-dialog")).to_be_visible()
    expect(page.get_by_test_id("card-mj-button")).to_be_hidden()
    shown = visible_cards.count()
    assert 0 < shown < total_component_count(), shown
    for index in range(shown):
        text = visible_cards.nth(index).get_attribute("data-search")
        assert "dialog" in text, text
    expect(page.get_by_test_id("group-buttons")).to_be_hidden()
    expect(page.get_by_test_id("filter-status")).to_contain_text("{} of".format(shown))
    expect(page).to_have_url(base_url + "/?q=dialog")

    page.get_by_test_id("catalog-filter").fill("no-such-component-xyz")
    expect(page.get_by_test_id("filter-empty")).to_be_visible()

    page.get_by_test_id("catalog-filter").fill("")
    expect(visible_cards).to_have_count(total_component_count())
    expect(page.get_by_test_id("filter-empty")).to_be_hidden()

    page.goto(base_url + "/?q=mj-button")
    expect(page.get_by_test_id("catalog-filter")).to_have_value("mj-button")
    expect(page.get_by_test_id("card-mj-button")).to_be_visible()
    assert cards.count() == total_component_count()

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_charts_filter_narrows_the_cards(page, base_url):
    """
        The Charts page filter covers the chart components, the chart parts
        and the chart types.
    """

    page.goto(base_url + "/charts")

    page.get_by_test_id("catalog-filter").fill("sankey")
    expect(page.get_by_test_id("chart-type-card-sankey")).to_be_visible()
    expect(page.get_by_test_id("chart-type-card-bar")).to_be_hidden()
    expect(page.get_by_test_id("charts-section-parts")).to_be_hidden()

    page.get_by_test_id("catalog-filter").fill("legend")
    expect(page.get_by_test_id("card-mj-chart-legend")).to_be_visible()
    expect(page.get_by_test_id("charts-section-parts")).to_be_visible()

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_component_pages_link_to_their_neighbours(page, base_url):
    """
        A component page links to the previous and next component of its
        group; the first has no previous link.
    """

    components = group_components("buttons")
    first = components[0]
    second = components[1]

    page.goto(base_url + "/components/buttons/" + first.tag)
    expect(page.get_by_test_id("page-prev")).to_have_count(0)
    expect(page.get_by_test_id("pager")).to_contain_text("1 of {}".format(len(components)))

    page.get_by_test_id("page-next").click()
    expect(page).to_have_url(base_url + "/components/buttons/" + second.tag)

    previous_doc, _next_doc = component_neighbours("buttons", second.tag)
    page.get_by_test_id("page-prev").click()
    expect(page).to_have_url(base_url + "/components/buttons/" + previous_doc.tag)

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_chart_type_pages_link_to_their_neighbours(page, base_url):
    """
        A chart-type page links to the next chart type of the gallery.
    """

    from testcomponents.charttypes import chart_type_neighbours

    _previous_doc, next_doc = chart_type_neighbours("bar")

    page.goto(base_url + "/chart-type/bar")
    page.get_by_test_id("page-next").click()
    expect(page).to_have_url(base_url + "/chart-type/" + next_doc.type_key)
    expect(page.get_by_test_id("chart-type-heading")).to_contain_text(next_doc.title)

    return


# --------------------------------------------------------------------------
# Chart parts.
# --------------------------------------------------------------------------


def _check_chart_part_page_loads(page, base_url, tag, title):
    """
        Each chart part page loads, documents the part, and its first example
        upgrades the part bound to a chart.

        :param tag: The chart part tag.
        :param title: The chart part title.
    """

    page.goto(base_url + "/chart-part/" + tag)

    expect(page.get_by_test_id("component-heading")).to_contain_text(title)
    expect(page.get_by_test_id("component-description")).to_be_visible()
    expect(page.get_by_test_id("attributes-table")).to_be_visible()

    frame = page.wait_for_selector("[data-testid=playground-preview]").content_frame()
    frame.wait_for_function(
        """tag => {
            const part = document.querySelector(tag);
            return part !== null && part.shadowRoot !== null && part.controller !== null
                && part.controller !== undefined;
        }""",
        arg=tag,
        timeout=15000,
    )

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_charts_page_links_to_chart_parts(page, base_url):
    """
        The Chart parts section of the Charts page opens a chart part page.
    """

    page.goto(base_url + "/charts")
    page.get_by_test_id("card-mj-chart-legend").click()

    expect(page).to_have_url(base_url + "/chart-part/mj-chart-legend")
    expect(page.get_by_test_id("view-link-charts")).to_have_attribute("aria-current", "page")

    return


# --------------------------------------------------------------------------
# Not found, escaping, static caching, library loading.
# --------------------------------------------------------------------------


def _fetch(url: str, headers: "dict[str, str] | None" = None):
    """
        GET a URL and return (status, headers, body text), for 2xx, 3xx and 4xx.

        :param url: The URL.
        :param headers: Request headers.

        :returns: The status code, the response headers and the decoded body.
    """

    request = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            status = response.status
            response_headers = response.headers
            body = response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as http_error:
        status = http_error.code
        response_headers = http_error.headers
        body = http_error.read().decode("utf-8", "replace")

    return status, response_headers, body


def test_unknown_chart_type_page_escapes_the_path(base_url):
    """
        The not-found page of an unknown chart type shows the requested key as
        text: markup in the path is escaped, never reflected as HTML.
    """

    status, _headers, body = _fetch(base_url + "/chart-type/%3Cimg%20src=x%20onerror=alert(1)%3E")

    assert status == 404, status
    assert "<img src=x" not in body
    assert "&lt;img src=x onerror=alert(1)&gt;" in body
    assert 'data-testid="not-found"' in body

    return


def test_chart_type_page_renders_events_and_plain_text_description():
    """
        A chart type's events are shown as an Events table like a component's,
        and its summary and description are plain text: entities are decoded,
        markup is escaped, `backticked` words become code and a blank line in
        the description starts a new paragraph.
    """

    from testcomponents import charttypes
    from testcomponents.charttypes.charttypedoc import ChartTypeDoc
    from testcomponents.rendering import render_chart_type_page

    doc = ChartTypeDoc(
        type_key="sandbox-render-check",
        title="Render check",
        category="comparison",
        summary="Bars &amp; `lines` <b>",
        description="Set `group=\"stack\"` &mdash; see <i>docs</i>.\n\nSecond paragraph.",
        example='<mj-chart type="bar" label="Render check"></mj-chart>',
        events=[
            ("mj-chart-select", "A bar was `selected`.", "{ index: number, value: number }"),
            ("mj-chart-render", "The chart finished rendering."),
        ],
    )
    assert doc.events[1] == ("mj-chart-render", "The chart finished rendering.", "")

    charttypes.BY_TYPE[doc.type_key] = doc
    try:
        document = render_chart_type_page(doc.type_key)
    finally:
        del charttypes.BY_TYPE[doc.type_key]

    assert 'Bars &amp; <code>lines</code> &lt;b&gt;' in document
    assert '<p>Set <code>group=&quot;stack&quot;</code> \u2014 see &lt;i&gt;docs&lt;/i&gt;.</p>' in document
    assert "<p>Second paragraph.</p>" in document
    assert "<i>docs</i>" not in document

    assert 'data-testid="events-table"' in document
    assert "<code>mj-chart-select</code>" in document
    assert "<code>{ index: number, value: number }</code>" in document
    assert "A bar was <code>selected</code>." in document

    return


def test_unknown_chart_part_returns_not_found(base_url):
    """
        An unknown chart part renders the not-found page.
    """

    status, _headers, body = _fetch(base_url + "/chart-part/mj-chart-nothing")

    assert status == 404, status
    assert 'data-testid="not-found"' in body

    return


def test_static_assets_answer_conditional_requests_with_304(base_url):
    """
        Static files carry an ETag and Last-Modified; a second request that
        presents either validator gets 304 Not Modified with no body, and a
        stale ETag gets the file again.
    """

    url = base_url + "/static/javascript/index.js"
    status, headers, body = _fetch(url)
    assert status == 200, status
    etag = headers.get("ETag")
    last_modified = headers.get("Last-Modified")
    assert etag is not None and last_modified is not None, dict(headers)
    assert "no-cache" not in headers.get("Cache-Control", "")
    assert len(body) > 0

    status, headers, body = _fetch(url, {"If-None-Match": etag})
    assert status == 304, status
    assert body == ""
    assert headers.get("ETag") == etag

    status, _headers, _body = _fetch(url, {"If-Modified-Since": last_modified})
    assert status == 304, status

    status, _headers, body = _fetch(url, {"If-None-Match": 'W/"stale-0"'})
    assert status == 200, status
    assert len(body) > 0

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_component_page_loads_the_library_once(page, base_url):
    """
        The page chrome does not load the component library: only the
        preview frame imports it (the Examples tab preview is built on
        demand), so a page view fetches index.js once.
    """

    requests = []
    page.on("request", lambda request: requests.append(request.url))

    page.goto(base_url + "/components/buttons/mj-button")
    frame = page.wait_for_selector("[data-testid=playground-preview]").content_frame()
    frame.wait_for_function("() => window.mjSandbox !== undefined && window.mjSandbox.ready === true",
                            timeout=20000)

    library_requests = []
    for url in requests:
        if url.endswith("/static/javascript/index.js"):
            library_requests.append(url)
    assert len(library_requests) == 1, library_requests

    outer_defines = page.evaluate("() => customElements.get('mj-button') !== undefined")
    assert outer_defines is False

    return


# One test per component group, named test_group_index_page_loads__<group>.
define_page_tests(globals(), "test_group_index_page_loads",
                  _check_group_index_page_loads,
                  [(identifier_for(group_key), (group_key, title))
                   for group_key, title in all_groups()])

# One test per chart part, named test_chart_part_page_loads__<tag>.
define_page_tests(globals(), "test_chart_part_page_loads",
                  _check_chart_part_page_loads,
                  [(identifier_for(doc.tag), (doc.tag, doc.title)) for doc in CHART_PARTS])


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
