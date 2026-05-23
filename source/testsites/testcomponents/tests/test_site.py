"""
    test_site.py

    Site-level Playwright tests for the testcomponents site: the browse
    page, group index pages, navigation, theme switching, static assets,
    and not-found handling.
"""

import urllib.request

import pytest
from playwright.sync_api import expect

from conftest import all_groups


def test_browse_page_loads(page, base_url):
    """
        The browse page loads and shows its heading and component count.
    """

    page.goto(base_url + "/")

    heading = page.get_by_test_id("browse-heading")
    expect(heading).to_be_visible()

    count = page.get_by_test_id("component-count")
    expect(count).to_contain_text("139 components")

    return


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


def test_browse_page_lists_every_component(page, base_url):
    """
        The browse page renders a card for all 139 components.
    """

    page.goto(base_url + "/")

    cards = page.locator('[data-testid^="card-mj-"]')
    expect(cards).to_have_count(139)

    return


@pytest.mark.parametrize("group_key, title", all_groups())
def test_group_index_page_loads(page, base_url, group_key, title):
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


def test_group_link_navigates_from_browse(page, base_url):
    """
        Clicking a group link on the browse page navigates to that group.
    """

    page.goto(base_url + "/")
    page.get_by_test_id("group-link-buttons").click()

    expect(page).to_have_url(base_url + "/components/buttons")
    expect(page.get_by_test_id("group-heading")).to_be_visible()

    return


def test_component_card_navigates_to_test_page(page, base_url):
    """
        Clicking a component card opens that component's test page.
    """

    page.goto(base_url + "/components/buttons")
    page.get_by_test_id("card-mj-button").click()

    expect(page).to_have_url(base_url + "/components/buttons/mj-button")
    expect(page.get_by_test_id("component-heading")).to_be_visible()

    return


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


def test_brand_link_returns_home(page, base_url):
    """
        The header brand link returns to the browse page.
    """

    page.goto(base_url + "/components/buttons/mj-button")
    page.get_by_test_id("site-brand").click()

    expect(page).to_have_url(base_url + "/")
    expect(page.get_by_test_id("browse-heading")).to_be_visible()

    return


def test_unknown_component_returns_not_found(page, base_url):
    """
        Requesting an unknown component renders the not-found page.
    """

    response = page.goto(base_url + "/components/buttons/mj-does-not-exist")

    assert response is not None
    assert response.status == 404
    expect(page.get_by_test_id("not-found")).to_be_visible()

    return


@pytest.mark.parametrize(
    "asset_path, expected_type",
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
        assert response.status == 200
        content_type = response.headers.get("Content-Type", "")
        assert expected_type in content_type

    return


# --------------------------------------------------------------------------
# Charts landing page and the Components/Charts header toggle.
# --------------------------------------------------------------------------


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


def test_charts_page_lists_all_charts(page, base_url):
    """
        The Charts page lists every chart component -- the 13 of the
        `charts` group plus the 5 data-visualization components of `media`.
    """

    page.goto(base_url + "/charts")

    project = page.get_by_test_id("charts-cards-project").locator(".card")
    viz = page.get_by_test_id("charts-cards-viz").locator(".card")

    expect(project).to_have_count(13)
    expect(viz).to_have_count(5)

    return


@pytest.mark.parametrize(
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


@pytest.mark.parametrize(
    "path, active",
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
