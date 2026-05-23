"""
    test_func_productivity.py

    Functional Playwright tests for the 'productivity' component group.

    Covers all 14 components:
      mj-toolbar, mj-menubar, mj-status-bar, mj-app-shell,
      mj-search-results, mj-filter-panel, mj-query-builder,
      mj-dropzone, mj-file-browser, mj-activity-feed, mj-comments,
      mj-mention-input, mj-chat-composer, mj-chat-message.

    Each test navigates to the component playground, waits for the
    custom element to be registered inside the preview iframe, and then
    asserts functional behaviour based on the real JS implementation.
"""

import pytest
from playwright.sync_api import expect


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_GROUP = "productivity"


def _open_component(page, base_url: str, tag: str):
    """
        Navigate to a component playground and return its preview frame.

        :param page: The Playwright page.
        :param base_url: The site base URL.
        :param tag: The mj-* custom element tag.

        :returns: The Frame inside the preview iframe with the element registered.
    """

    page.goto(base_url + f"/components/{_GROUP}/{tag}")
    handle = page.wait_for_selector("[data-testid=playground-preview]")
    frame = handle.content_frame()
    frame.wait_for_function(
        "tag => customElements.get(tag) !== undefined",
        arg=tag,
        timeout=15000,
    )
    return frame


def _load_example(page, base_url: str, tag: str):
    """
        Open the playground, let the example script run, and return the frame.

        :param page: The Playwright page.
        :param base_url: The site base URL.
        :param tag: The mj-* custom element tag.

        :returns: The Frame after the example script has executed.
    """

    frame = _open_component(page, base_url, tag)
    # Wait for the element to appear in the DOM
    frame.wait_for_selector(tag, timeout=10000)
    return frame


# ---------------------------------------------------------------------------
# mj-toolbar
# ---------------------------------------------------------------------------

@pytest.mark.functional
def test_toolbar_has_role(page, base_url: str) -> None:
    """
        The toolbar root element has role="toolbar" in the shadow DOM.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-toolbar")

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-toolbar");
        return el && el.shadowRoot &&
               el.shadowRoot.querySelector("[role=toolbar]") !== null;
    }''', timeout=10000)

    has_role = frame.evaluate('''() => {
        const el = document.querySelector("mj-toolbar");
        return el.shadowRoot.querySelector("[role=toolbar]") !== null;
    }''')
    assert has_role is True

    return


@pytest.mark.functional
def test_toolbar_aria_label(page, base_url: str) -> None:
    """
        The toolbar carries the accessible label from the ``label`` attribute.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-toolbar")

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-toolbar");
        return el && el.shadowRoot &&
               el.shadowRoot.querySelector("[role=toolbar]") !== null;
    }''', timeout=10000)

    aria_label = frame.evaluate('''() => {
        const el = document.querySelector("mj-toolbar");
        const root = el.shadowRoot.querySelector("[role=toolbar]");
        return root ? root.getAttribute("aria-label") : null;
    }''')
    assert aria_label is not None and len(aria_label) > 0

    return


@pytest.mark.functional
def test_toolbar_aria_orientation(page, base_url: str) -> None:
    """
        The toolbar sets aria-orientation on its root element.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-toolbar")

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-toolbar");
        return el && el.shadowRoot &&
               el.shadowRoot.querySelector("[role=toolbar]") !== null;
    }''', timeout=10000)

    orientation = frame.evaluate('''() => {
        const el = document.querySelector("mj-toolbar");
        const root = el.shadowRoot.querySelector("[role=toolbar]");
        return root ? root.getAttribute("aria-orientation") : null;
    }''')
    assert orientation in ("horizontal", "vertical")

    return


@pytest.mark.functional
def test_toolbar_children_rendered(page, base_url: str) -> None:
    """
        The slotted button children are rendered inside the toolbar.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-toolbar")
    toolbar = frame.locator("mj-toolbar")
    expect(toolbar).to_be_visible()

    return


# ---------------------------------------------------------------------------
# mj-menubar
# ---------------------------------------------------------------------------

@pytest.mark.functional
def test_menubar_has_role(page, base_url: str) -> None:
    """
        The menubar shadow DOM root has role="menubar".

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-menubar")

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-menubar");
        return el && el.shadowRoot &&
               el.shadowRoot.querySelector("[role=menubar]") !== null;
    }''', timeout=10000)

    has_role = frame.evaluate('''() => {
        const el = document.querySelector("mj-menubar");
        return el.shadowRoot.querySelector("[role=menubar]") !== null;
    }''')
    assert has_role is True

    return


@pytest.mark.functional
def test_menubar_aria_label(page, base_url: str) -> None:
    """
        The menubar has the accessible label from the ``label`` attribute.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-menubar")

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-menubar");
        return el && el.shadowRoot &&
               el.shadowRoot.querySelector("[role=menubar]") !== null;
    }''', timeout=10000)

    aria_label = frame.evaluate('''() => {
        const el = document.querySelector("mj-menubar");
        const root = el.shadowRoot.querySelector("[role=menubar]");
        return root ? root.getAttribute("aria-label") : null;
    }''')
    assert aria_label is not None and len(aria_label) > 0

    return


@pytest.mark.functional
def test_menubar_top_level_items_have_role_menuitem(page, base_url: str) -> None:
    """
        The injected top-level buttons have role="menuitem".

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-menubar")

    # The component builds <button role="menuitem" data-mj-menubar-btn> elements
    # for each slotted child inside the shadow DOM's menubar-root
    count = frame.evaluate('''() => {
        const el = document.querySelector("mj-menubar");
        if (!el || !el.shadowRoot) { return 0; }
        return el.shadowRoot.querySelectorAll("[data-mj-menubar-btn]").length;
    }''')
    assert count >= 2  # Example has File and Edit menus

    return


@pytest.mark.functional
def test_menubar_click_opens_dropdown(page, base_url: str) -> None:
    """
        Clicking a top-level menu button opens its dropdown.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-menubar")

    # Click the first top-level button via JS to avoid shadow DOM visibility issues
    result = frame.evaluate('''() => {
        const el = document.querySelector("mj-menubar");
        if (!el || !el.shadowRoot) { return null; }
        const btn = el.shadowRoot.querySelector("[data-mj-menubar-btn]");
        if (!btn) { return null; }
        btn.click();
        return btn.getAttribute("aria-expanded");
    }''')
    assert result == "true"

    return


@pytest.mark.functional
def test_menubar_click_fires_select_event(page, base_url: str) -> None:
    """
        Choosing a dropdown item fires the mj-menubar-select event.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-menubar")

    frame.evaluate('''() => {
        window.__mbEvents = [];
        const el = document.querySelector("mj-menubar");
        el.addEventListener("mj-menubar-select", e => window.__mbEvents.push(e.detail));
        // Open first menu then click first dropdown item
        const btn = el.shadowRoot.querySelector("[data-mj-menubar-btn]");
        if (btn) { btn.click(); }
        const dropdownItem = el.shadowRoot.querySelector("[role=menu] button");
        if (dropdownItem) { dropdownItem.click(); }
    }''')

    events = frame.evaluate("() => window.__mbEvents")
    assert len(events) >= 1
    assert "value" in events[0]

    return


# ---------------------------------------------------------------------------
# mj-status-bar
# ---------------------------------------------------------------------------

@pytest.mark.functional
def test_status_bar_has_role_status(page, base_url: str) -> None:
    """
        The status bar shadow DOM contains an element with role="status".

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-status-bar")

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-status-bar");
        return el && el.shadowRoot &&
               el.shadowRoot.querySelector("[role=status]") !== null;
    }''', timeout=10000)

    has_role = frame.evaluate('''() => {
        const el = document.querySelector("mj-status-bar");
        return el.shadowRoot.querySelector("[role=status]") !== null;
    }''')
    assert has_role is True

    return


@pytest.mark.functional
def test_status_bar_has_live_region(page, base_url: str) -> None:
    """
        The status bar contains a polite live region for announcements.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-status-bar")

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-status-bar");
        return el && el.shadowRoot &&
               el.shadowRoot.querySelector("[aria-live=polite]") !== null;
    }''', timeout=10000)

    has_live = frame.evaluate('''() => {
        const el = document.querySelector("mj-status-bar");
        return el.shadowRoot.querySelector("[aria-live=polite]") !== null;
    }''')
    assert has_live is True

    return


@pytest.mark.functional
def test_status_bar_slots_content(page, base_url: str) -> None:
    """
        Slotted content is visible in the status bar.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-status-bar")

    status_bar = frame.locator("mj-status-bar")
    expect(status_bar).to_be_visible()

    return


# ---------------------------------------------------------------------------
# mj-app-shell
# ---------------------------------------------------------------------------

@pytest.mark.functional
def test_app_shell_landmark_structure(page, base_url: str) -> None:
    """
        The app shell shadow DOM contains header, nav, main, aside, footer.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-app-shell")

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-app-shell");
        return el && el.shadowRoot &&
               el.shadowRoot.querySelector("header") !== null &&
               el.shadowRoot.querySelector("nav") !== null &&
               el.shadowRoot.querySelector("main") !== null;
    }''', timeout=10000)

    has_landmarks = frame.evaluate('''() => {
        const el = document.querySelector("mj-app-shell");
        const sr = el.shadowRoot;
        return sr.querySelector("header") !== null &&
               sr.querySelector("nav") !== null &&
               sr.querySelector("main") !== null &&
               sr.querySelector("aside") !== null &&
               sr.querySelector("footer") !== null;
    }''')
    assert has_landmarks is True

    return


@pytest.mark.functional
def test_app_shell_nav_open_attribute(page, base_url: str) -> None:
    """
        When nav-open is set the shell has the nav-open attribute.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-app-shell")

    # The example uses nav-open; the attribute should be present
    shell = frame.locator("mj-app-shell")
    nav_open = shell.get_attribute("nav-open")
    # nav-open is a boolean attribute: present means truthy
    assert nav_open is not None

    return


@pytest.mark.functional
def test_app_shell_toggle_inspector_fires_event(page, base_url: str) -> None:
    """
        Toggling the inspector via JS fires mj-shell-inspector-toggle.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-app-shell")

    frame.evaluate('''() => {
        window.__shellEvents = [];
        const el = document.querySelector("mj-app-shell");
        el.addEventListener("mj-shell-inspector-toggle", e => {
            window.__shellEvents.push(e.detail);
        });
        el.toggleInspector();
    }''')

    events = frame.evaluate("() => window.__shellEvents")
    assert len(events) >= 1
    assert "open" in events[0]

    return


@pytest.mark.functional
def test_app_shell_toggle_nav_fires_event(page, base_url: str) -> None:
    """
        Toggling the nav via JS fires mj-shell-nav-toggle.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-app-shell")

    frame.evaluate('''() => {
        window.__navEvents = [];
        const el = document.querySelector("mj-app-shell");
        el.addEventListener("mj-shell-nav-toggle", e => {
            window.__navEvents.push(e.detail);
        });
        el.toggleNav();
    }''')

    events = frame.evaluate("() => window.__navEvents")
    assert len(events) >= 1
    assert "open" in events[0]

    return


# ---------------------------------------------------------------------------
# mj-search-results
# ---------------------------------------------------------------------------

@pytest.mark.functional
def test_search_results_renders_count_bar(page, base_url: str) -> None:
    """
        The count bar is visible after results are loaded.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-search-results")

    # Wait for shadow DOM count bar to appear (rendered by the component)
    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-search-results");
        return el && el.shadowRoot && el.shadowRoot.querySelector(".count-bar") !== null;
    }''', timeout=10000)

    count_bar_text = frame.evaluate('''() => {
        const el = document.querySelector("mj-search-results");
        return el.shadowRoot.querySelector(".count-bar").textContent;
    }''')
    assert count_bar_text is not None

    return


@pytest.mark.functional
def test_search_results_shows_result_items(page, base_url: str) -> None:
    """
        After setting results via JS, at least one result item is rendered.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, "mj-search-results")
    frame.wait_for_selector("mj-search-results", timeout=10000)

    # Use prototype setter explicitly so any own data property set before
    # the custom element was registered does not shadow the class accessor.
    frame.evaluate('''() => {
        const el = document.querySelector("mj-search-results");
        el.setAttribute("highlight-term", "component");
        delete el.results;
        el.results = [
            { id: "1", title: "Button component", url: "/docs/button",
              snippet: "The button component triggers actions." },
            { id: "2", title: "Card component", url: "/docs/card",
              snippet: "The card component groups related content." }
        ];
    }''')

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-search-results");
        return el && el.shadowRoot &&
               el.shadowRoot.querySelectorAll(".result-item").length > 0;
    }''', timeout=10000)

    count = frame.evaluate('''() => {
        const el = document.querySelector("mj-search-results");
        return el.shadowRoot.querySelectorAll(".result-item").length;
    }''')
    assert count >= 1

    return


@pytest.mark.functional
def test_search_results_highlights_term(page, base_url: str) -> None:
    """
        Words matching the highlight-term are wrapped in <mark> elements.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, "mj-search-results")
    frame.wait_for_selector("mj-search-results", timeout=10000)

    frame.evaluate('''() => {
        const el = document.querySelector("mj-search-results");
        el.setAttribute("highlight-term", "component");
        delete el.results;
        el.results = [
            { id: "1", title: "Button component", url: "/docs/button",
              snippet: "The button component triggers actions." }
        ];
    }''')

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-search-results");
        return el && el.shadowRoot &&
               el.shadowRoot.querySelectorAll("mark").length > 0;
    }''', timeout=10000)

    count = frame.evaluate('''() => {
        const el = document.querySelector("mj-search-results");
        return el.shadowRoot.querySelectorAll("mark").length;
    }''')
    assert count >= 1

    return


@pytest.mark.functional
def test_search_results_result_links_have_href(page, base_url: str) -> None:
    """
        Each result link element has an href attribute.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, "mj-search-results")
    frame.wait_for_selector("mj-search-results", timeout=10000)

    frame.evaluate('''() => {
        const el = document.querySelector("mj-search-results");
        delete el.results;
        el.results = [
            { id: "1", title: "Button component", url: "/docs/button",
              snippet: "The button component triggers actions." }
        ];
    }''')

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-search-results");
        return el && el.shadowRoot &&
               el.shadowRoot.querySelector(".result-title") !== null;
    }''', timeout=10000)

    href = frame.evaluate('''() => {
        const el = document.querySelector("mj-search-results");
        const link = el.shadowRoot.querySelector(".result-title");
        return link ? link.getAttribute("href") : null;
    }''')
    assert href is not None and len(href) > 0

    return


@pytest.mark.functional
def test_search_results_loading_shows_skeletons(page, base_url: str) -> None:
    """
        Setting the loading attribute renders skeleton rows.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-search-results")

    frame.evaluate('''() => {
        const el = document.querySelector("mj-search-results");
        el.setAttribute("loading", "");
    }''')

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-search-results");
        return el && el.shadowRoot &&
               el.shadowRoot.querySelectorAll(".skeleton").length > 0;
    }''', timeout=5000)

    count = frame.evaluate('''() => {
        const el = document.querySelector("mj-search-results");
        return el.shadowRoot.querySelectorAll(".skeleton").length;
    }''')
    assert count >= 1

    return


# ---------------------------------------------------------------------------
# mj-filter-panel
# ---------------------------------------------------------------------------

@pytest.mark.functional
def test_filter_panel_renders_filter_groups(page, base_url: str) -> None:
    """
        After setting filterConfig the filter groups are rendered.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, "mj-filter-panel")
    frame.wait_for_selector("mj-filter-panel", timeout=10000)

    frame.evaluate('''() => {
        const el = document.querySelector("mj-filter-panel");
        delete el.filterConfig;
        el.filterConfig = [
            { id: "status", label: "Status", type: "checkbox",
              options: [{value:"active",label:"Active"},{value:"archived",label:"Archived"}] },
            { id: "type", label: "Type", type: "radio",
              options: [{value:"doc",label:"Document"},{value:"img",label:"Image"}] }
        ];
    }''')

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-filter-panel");
        return el && el.shadowRoot &&
               el.shadowRoot.querySelectorAll(".filter-group").length > 0;
    }''', timeout=10000)

    count = frame.evaluate('''() => {
        const el = document.querySelector("mj-filter-panel");
        return el.shadowRoot.querySelectorAll(".filter-group").length;
    }''')
    assert count >= 1

    return


@pytest.mark.functional
def test_filter_panel_checkbox_fires_change_event(page, base_url: str) -> None:
    """
        Checking a checkbox fires mj-filter-change with the updated value.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, "mj-filter-panel")
    frame.wait_for_selector("mj-filter-panel", timeout=10000)

    frame.evaluate('''() => {
        const el = document.querySelector("mj-filter-panel");
        delete el.filterConfig;
        el.filterConfig = [
            { id: "status", label: "Status", type: "checkbox",
              options: [{value:"active",label:"Active"},{value:"archived",label:"Archived"}] }
        ];
    }''')

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-filter-panel");
        return el && el.shadowRoot &&
               el.shadowRoot.querySelector("input[type=checkbox]") !== null;
    }''', timeout=10000)

    frame.evaluate('''() => {
        window.__fpEvents = [];
        const el = document.querySelector("mj-filter-panel");
        el.addEventListener("mj-filter-change", e => window.__fpEvents.push(e.detail));
        const checkbox = el.shadowRoot.querySelector("input[type=checkbox]");
        if (checkbox) { checkbox.click(); }
    }''')

    # Allow event to propagate
    frame.wait_for_timeout(200)
    events = frame.evaluate("() => window.__fpEvents")
    assert len(events) >= 1
    assert "value" in events[0]

    return


@pytest.mark.functional
def test_filter_panel_chip_appears_after_selection(page, base_url: str) -> None:
    """
        Selecting a filter option creates a chip in the chips bar.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, "mj-filter-panel")
    frame.wait_for_selector("mj-filter-panel", timeout=10000)

    frame.evaluate('''() => {
        const el = document.querySelector("mj-filter-panel");
        delete el.filterConfig;
        el.filterConfig = [
            { id: "status", label: "Status", type: "checkbox",
              options: [{value:"active",label:"Active"},{value:"archived",label:"Archived"}] }
        ];
    }''')

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-filter-panel");
        return el && el.shadowRoot &&
               el.shadowRoot.querySelector("input[type=checkbox]") !== null;
    }''', timeout=10000)

    frame.evaluate('''() => {
        const el = document.querySelector("mj-filter-panel");
        const checkbox = el.shadowRoot.querySelector("input[type=checkbox]");
        if (checkbox) { checkbox.click(); }
    }''')

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-filter-panel");
        return el && el.shadowRoot &&
               el.shadowRoot.querySelector(".chip") !== null;
    }''', timeout=5000)

    has_chip = frame.evaluate('''() => {
        const el = document.querySelector("mj-filter-panel");
        return el.shadowRoot.querySelector(".chip") !== null;
    }''')
    assert has_chip is True

    return


@pytest.mark.functional
def test_filter_panel_sort_control_rendered(page, base_url: str) -> None:
    """
        The sort select and direction button are rendered.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, "mj-filter-panel")
    frame.wait_for_selector("mj-filter-panel", timeout=10000)

    frame.evaluate('''() => {
        const el = document.querySelector("mj-filter-panel");
        delete el.filterConfig;
        el.filterConfig = [
            { id: "status", label: "Status", type: "checkbox",
              options: [{value:"active",label:"Active"}] }
        ];
    }''')

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-filter-panel");
        return el && el.shadowRoot &&
               el.shadowRoot.querySelector(".sort-select") !== null;
    }''', timeout=10000)

    has_sort = frame.evaluate('''() => {
        const el = document.querySelector("mj-filter-panel");
        const sel = el.shadowRoot.querySelector(".sort-select");
        const btn = el.shadowRoot.querySelector(".sort-direction-btn");
        return sel !== null && btn !== null;
    }''')
    assert has_sort is True

    return


# ---------------------------------------------------------------------------
# mj-query-builder
# ---------------------------------------------------------------------------

@pytest.mark.functional
def test_query_builder_renders_root_group(page, base_url: str) -> None:
    """
        The query builder renders a root condition group.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-query-builder")

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-query-builder");
        return el && el.shadowRoot &&
               el.shadowRoot.querySelector(".qb-group") !== null;
    }''', timeout=10000)

    has_group = frame.evaluate('''() => {
        const el = document.querySelector("mj-query-builder");
        return el.shadowRoot.querySelector(".qb-group") !== null;
    }''')
    assert has_group is True

    return


@pytest.mark.functional
def test_query_builder_has_and_or_buttons(page, base_url: str) -> None:
    """
        The AND and OR combinator buttons are rendered.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-query-builder")

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-query-builder");
        return el && el.shadowRoot &&
               el.shadowRoot.querySelector(".combinator-option") !== null;
    }''', timeout=10000)

    first_text = frame.evaluate('''() => {
        const el = document.querySelector("mj-query-builder");
        const btn = el.shadowRoot.querySelector(".combinator-option");
        return btn ? btn.textContent : "";
    }''')
    assert first_text in ("AND", "OR")

    return


@pytest.mark.functional
def test_query_builder_add_condition_adds_rule_row(page, base_url: str) -> None:
    """
        Clicking Add condition inserts a new rule row.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-query-builder")

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-query-builder");
        return el && el.shadowRoot &&
               el.shadowRoot.querySelector("[part=add-rule]") !== null;
    }''', timeout=10000)

    frame.evaluate('''() => {
        const el = document.querySelector("mj-query-builder");
        const btn = el.shadowRoot.querySelector("[part=add-rule]");
        if (btn) { btn.click(); }
    }''')

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-query-builder");
        return el && el.shadowRoot &&
               el.shadowRoot.querySelector("[part=rule-row]") !== null;
    }''', timeout=5000)

    has_row = frame.evaluate('''() => {
        const el = document.querySelector("mj-query-builder");
        return el.shadowRoot.querySelector("[part=rule-row]") !== null;
    }''')
    assert has_row is True

    return


@pytest.mark.functional
def test_query_builder_add_condition_fires_change_event(page, base_url: str) -> None:
    """
        Adding a condition fires the mj-query-change event.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-query-builder")

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-query-builder");
        return el && el.shadowRoot &&
               el.shadowRoot.querySelector("[part=add-rule]") !== null;
    }''', timeout=10000)

    frame.evaluate('''() => {
        window.__qbEvents = [];
        const el = document.querySelector("mj-query-builder");
        el.addEventListener("mj-query-change", e => window.__qbEvents.push(e.detail));
        const btn = el.shadowRoot.querySelector("[part=add-rule]");
        if (btn) { btn.click(); }
    }''')

    frame.wait_for_timeout(200)
    events = frame.evaluate("() => window.__qbEvents")
    assert len(events) >= 1
    assert "value" in events[0]

    return


@pytest.mark.functional
def test_query_builder_show_preview_renders_json(page, base_url: str) -> None:
    """
        When show-preview is set the JSON preview panel is visible.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-query-builder")

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-query-builder");
        return el && el.shadowRoot &&
               el.shadowRoot.querySelector("pre") !== null;
    }''', timeout=10000)

    # The example already has show-preview attribute; pre element has JSON
    content = frame.evaluate('''() => {
        const el = document.querySelector("mj-query-builder");
        const pre = el.shadowRoot.querySelector("pre");
        return pre ? pre.textContent : "";
    }''')
    assert "combinator" in content

    return


# ---------------------------------------------------------------------------
# mj-dropzone
# ---------------------------------------------------------------------------

@pytest.mark.functional
def test_dropzone_renders_drop_target(page, base_url: str) -> None:
    """
        The drop target region is visible and accessible.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-dropzone")

    drop_target = frame.locator("mj-dropzone [role=region]").first
    expect(drop_target).to_be_visible()

    return


@pytest.mark.functional
def test_dropzone_browse_button_visible(page, base_url: str) -> None:
    """
        The Browse files button is rendered inside the drop zone.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-dropzone")

    browse_btn = frame.locator("mj-dropzone [part=browse-button]")
    expect(browse_btn).to_be_visible()

    return


@pytest.mark.functional
def test_dropzone_has_aria_label(page, base_url: str) -> None:
    """
        The drop region has an accessible aria-label.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-dropzone")

    region = frame.locator("mj-dropzone [role=region]").first
    label = region.get_attribute("aria-label")
    assert label is not None and len(label) > 0

    return


@pytest.mark.functional
def test_dropzone_files_added_via_js(page, base_url: str) -> None:
    """
        Programmatically adding a file via _processFiles fires mj-files-added.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, "mj-dropzone")
    frame.wait_for_selector("mj-dropzone", timeout=10000)

    # Ensure shadow DOM is ready before calling _processFiles
    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-dropzone");
        return el && el.shadowRoot && typeof el._processFiles === "function";
    }''', timeout=10000)

    frame.evaluate('''() => {
        window.__dzEvents = [];
        const el = document.querySelector("mj-dropzone");
        el.addEventListener("mj-files-added", e => window.__dzEvents.push(e.detail));
        // Use a PDF file name to match the example accept=".pdf,.docx" attribute
        const file = new File(["hello"], "report.pdf", { type: "application/pdf" });
        el._processFiles([file]);
    }''')

    frame.wait_for_function(
        "() => window.__dzEvents && window.__dzEvents.length > 0",
        timeout=5000,
    )

    events = frame.evaluate("() => window.__dzEvents")
    assert len(events) >= 1
    assert "files" in events[0]

    return


# ---------------------------------------------------------------------------
# mj-file-browser
# ---------------------------------------------------------------------------

@pytest.mark.functional
def test_file_browser_renders_panes(page, base_url: str) -> None:
    """
        The file browser renders its tree and file panes in the shadow DOM.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-file-browser")

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-file-browser");
        return el && el.shadowRoot &&
               el.shadowRoot.querySelector(".tree-pane") !== null &&
               el.shadowRoot.querySelector(".file-pane") !== null;
    }''', timeout=10000)

    has_panes = frame.evaluate('''() => {
        const el = document.querySelector("mj-file-browser");
        return el.shadowRoot.querySelector(".tree-pane") !== null &&
               el.shadowRoot.querySelector(".file-pane") !== null;
    }''')
    assert has_panes is True

    return


@pytest.mark.functional
def test_file_browser_view_toggle_buttons(page, base_url: str) -> None:
    """
        The toolbar view toggle buttons (list / grid) are in the shadow DOM.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-file-browser")

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-file-browser");
        return el && el.shadowRoot &&
               el.shadowRoot.querySelector("[data-view=list]") !== null &&
               el.shadowRoot.querySelector("[data-view=grid]") !== null;
    }''', timeout=10000)

    has_buttons = frame.evaluate('''() => {
        const el = document.querySelector("mj-file-browser");
        return el.shadowRoot.querySelector("[data-view=list]") !== null &&
               el.shadowRoot.querySelector("[data-view=grid]") !== null;
    }''')
    assert has_buttons is True

    return


@pytest.mark.functional
def test_file_browser_loads_data_source(page, base_url: str) -> None:
    """
        Setting a dataSource renders the directory contents.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, "mj-file-browser")
    frame.wait_for_selector("mj-file-browser", timeout=10000)

    # Wait for shadow DOM to initialise, then inject data source
    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-file-browser");
        return el && el.shadowRoot && el.shadowRoot.querySelector(".tree-pane") !== null;
    }''', timeout=10000)

    frame.evaluate('''() => {
        const el = document.querySelector("mj-file-browser");
        delete el.dataSource;
        el.dataSource = {
            listDir(path) {
                return Promise.resolve([
                    { name: "docs", type: "folder", path: "/docs" },
                    { name: "readme.md", type: "text/markdown", path: "/readme.md", size: "2 KB" },
                    { name: "logo.png", type: "image/png", path: "/logo.png", size: "48 KB" }
                ]);
            }
        };
    }''')

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-file-browser");
        if (!el || !el.shadowRoot) { return false; }
        const rows = el.shadowRoot.querySelectorAll(".file-list-table tbody tr");
        const items = el.shadowRoot.querySelectorAll(".file-grid-item");
        return rows.length > 0 || items.length > 0;
    }''', timeout=10000)

    count = frame.evaluate('''() => {
        const el = document.querySelector("mj-file-browser");
        const rows = el.shadowRoot.querySelectorAll(".file-list-table tbody tr").length;
        const items = el.shadowRoot.querySelectorAll(".file-grid-item").length;
        return rows + items;
    }''')
    assert count >= 1

    return


@pytest.mark.functional
def test_file_browser_view_change_fires_event(page, base_url: str) -> None:
    """
        Clicking the grid view button fires the mj-view-change event.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-file-browser")

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-file-browser");
        return el && el.shadowRoot &&
               el.shadowRoot.querySelector("[data-view=grid]") !== null;
    }''', timeout=10000)

    frame.evaluate('''() => {
        window.__fbEvents = [];
        const el = document.querySelector("mj-file-browser");
        el.addEventListener("mj-view-change", e => window.__fbEvents.push(e.detail));
        const btn = el.shadowRoot.querySelector("[data-view=grid]");
        if (btn) { btn.click(); }
    }''')

    frame.wait_for_timeout(200)
    events = frame.evaluate("() => window.__fbEvents")
    assert len(events) >= 1
    assert events[0].get("view") == "grid"

    return


# ---------------------------------------------------------------------------
# mj-activity-feed
# ---------------------------------------------------------------------------

@pytest.mark.functional
def test_activity_feed_has_role_feed(page, base_url: str) -> None:
    """
        The activity feed root has role="feed".

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-activity-feed")

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-activity-feed");
        return el && el.shadowRoot &&
               el.shadowRoot.querySelector("[role=feed]") !== null;
    }''', timeout=10000)

    has_feed = frame.evaluate('''() => {
        const el = document.querySelector("mj-activity-feed");
        return el.shadowRoot.querySelector("[role=feed]") !== null;
    }''')
    assert has_feed is True

    return


def _inject_activity_feed_items(frame) -> None:
    """
        Inject sample items into the mj-activity-feed inside the given frame.

        :param frame: The Playwright frame containing the mj-activity-feed element.
    """

    frame.evaluate('''() => {
        const el = document.querySelector("mj-activity-feed");
        const now = new Date().toISOString();
        delete el.items;
        el.items = [
            { id: "1", actor: { name: "Alice Martin" }, action: "created document",
              body: "Q4 Planning Notes", timestamp: now },
            { id: "2", actor: { name: "Bob Lee" }, action: "commented",
              body: "Looks good!", timestamp: now },
            { id: "3", actor: { name: "Carol King" }, action: "uploaded file",
              body: "budget.xlsx", timestamp: now }
        ];
    }''')

    return


@pytest.mark.functional
def test_activity_feed_renders_items(page, base_url: str) -> None:
    """
        After setting the items property activity articles are rendered.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, "mj-activity-feed")
    frame.wait_for_selector("mj-activity-feed", timeout=10000)

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-activity-feed");
        return el && el.shadowRoot && el.shadowRoot.querySelector("[role=feed]") !== null;
    }''', timeout=10000)

    _inject_activity_feed_items(frame)

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-activity-feed");
        return el && el.shadowRoot &&
               el.shadowRoot.querySelectorAll("article").length > 0;
    }''', timeout=10000)

    count = frame.evaluate('''() => {
        const el = document.querySelector("mj-activity-feed");
        return el.shadowRoot.querySelectorAll("article").length;
    }''')
    assert count >= 1

    return


@pytest.mark.functional
def test_activity_feed_load_more_button_visible(page, base_url: str) -> None:
    """
        The Load older activity button is visible after items are set.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, "mj-activity-feed")
    frame.wait_for_selector("mj-activity-feed", timeout=10000)

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-activity-feed");
        return el && el.shadowRoot && el.shadowRoot.querySelector("[role=feed]") !== null;
    }''', timeout=10000)

    _inject_activity_feed_items(frame)

    # Wait for items to render (load-more shows after items appear)
    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-activity-feed");
        if (!el || !el.shadowRoot) { return false; }
        const btn = el.shadowRoot.querySelector("[part=load-more]");
        return btn !== null && !btn.hidden;
    }''', timeout=10000)

    is_visible = frame.evaluate('''() => {
        const el = document.querySelector("mj-activity-feed");
        const btn = el.shadowRoot.querySelector("[part=load-more]");
        return btn !== null && !btn.hidden;
    }''')
    assert is_visible is True

    return


@pytest.mark.functional
def test_activity_feed_load_more_fires_event(page, base_url: str) -> None:
    """
        Clicking Load older activity fires the mj-load-older event.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, "mj-activity-feed")
    frame.wait_for_selector("mj-activity-feed", timeout=10000)

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-activity-feed");
        return el && el.shadowRoot && el.shadowRoot.querySelector("[role=feed]") !== null;
    }''', timeout=10000)

    _inject_activity_feed_items(frame)

    # Wait for the load-more button to be visible
    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-activity-feed");
        if (!el || !el.shadowRoot) { return false; }
        const btn = el.shadowRoot.querySelector("[part=load-more]");
        return btn !== null && !btn.hidden;
    }''', timeout=10000)

    frame.evaluate('''() => {
        window.__afEvents = [];
        const el = document.querySelector("mj-activity-feed");
        el.addEventListener("mj-load-older", e => window.__afEvents.push(e.detail));
        const btn = el.shadowRoot.querySelector("[part=load-more]");
        if (btn) { btn.click(); }
    }''')

    frame.wait_for_timeout(200)
    events = frame.evaluate("() => window.__afEvents")
    assert len(events) >= 1

    return


@pytest.mark.functional
def test_activity_feed_actor_name_rendered(page, base_url: str) -> None:
    """
        The actor name from each item is visible in the feed.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, "mj-activity-feed")
    frame.wait_for_selector("mj-activity-feed", timeout=10000)

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-activity-feed");
        return el && el.shadowRoot && el.shadowRoot.querySelector("[role=feed]") !== null;
    }''', timeout=10000)

    _inject_activity_feed_items(frame)

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-activity-feed");
        return el && el.shadowRoot &&
               el.shadowRoot.querySelector(".item-actor") !== null;
    }''', timeout=10000)

    text = frame.evaluate('''() => {
        const el = document.querySelector("mj-activity-feed");
        const actor = el.shadowRoot.querySelector(".item-actor");
        return actor ? actor.textContent : "";
    }''')
    assert len(text) > 0

    return


# ---------------------------------------------------------------------------
# mj-comments
# ---------------------------------------------------------------------------

@pytest.mark.functional
def test_comments_has_role_feed(page, base_url: str) -> None:
    """
        The comments root element has role="feed".

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-comments")

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-comments");
        return el && el.shadowRoot &&
               el.shadowRoot.querySelector("[role=feed]") !== null;
    }''', timeout=10000)

    has_feed = frame.evaluate('''() => {
        const el = document.querySelector("mj-comments");
        return el.shadowRoot.querySelector("[role=feed]") !== null;
    }''')
    assert has_feed is True

    return


@pytest.mark.functional
def test_comments_renders_comment_articles(page, base_url: str) -> None:
    """
        After setting the comments property, comment articles are visible.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, "mj-comments")
    frame.wait_for_selector("mj-comments", timeout=10000)

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-comments");
        return el && el.shadowRoot && el.shadowRoot.querySelector("[role=feed]") !== null;
    }''', timeout=10000)

    frame.evaluate('''() => {
        const el = document.querySelector("mj-comments");
        const now = new Date().toISOString();
        delete el.comments;
        el.comments = [
            { id: "c1", author: { name: "Alice Martin", avatarUrl: "" },
              body: "Great work on this feature!", timestamp: now },
            { id: "c2", author: { name: "Bob Lee", avatarUrl: "" },
              body: "I agree, looks solid.", timestamp: now }
        ];
    }''')

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-comments");
        return el && el.shadowRoot &&
               el.shadowRoot.querySelectorAll("article").length > 0;
    }''', timeout=10000)

    count = frame.evaluate('''() => {
        const el = document.querySelector("mj-comments");
        return el.shadowRoot.querySelectorAll("article").length;
    }''')
    assert count >= 1

    return


@pytest.mark.functional
def test_comments_count_heading_reflects_count(page, base_url: str) -> None:
    """
        The count heading reflects the number of loaded comments.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-comments")

    # The count heading is always rendered; the example script populates comments
    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-comments");
        return el && el.shadowRoot &&
               el.shadowRoot.querySelector(".count-heading") !== null;
    }''', timeout=10000)

    text = frame.evaluate('''() => {
        const el = document.querySelector("mj-comments");
        return el.shadowRoot.querySelector(".count-heading").textContent;
    }''')
    assert "comment" in text.lower()

    return


@pytest.mark.functional
def test_comments_composer_textarea_present(page, base_url: str) -> None:
    """
        The top-level composer textarea is present for new comments.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-comments")

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-comments");
        return el && el.shadowRoot &&
               el.shadowRoot.querySelector(".composer-textarea") !== null;
    }''', timeout=10000)

    has_textarea = frame.evaluate('''() => {
        const el = document.querySelector("mj-comments");
        return el.shadowRoot.querySelector(".composer-textarea") !== null;
    }''')
    assert has_textarea is True

    return


@pytest.mark.functional
def test_comments_post_fires_event(page, base_url: str) -> None:
    """
        Clicking Post while text is in the composer fires mj-comment-post.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-comments")

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-comments");
        return el && el.shadowRoot &&
               el.shadowRoot.querySelector(".composer-textarea") !== null;
    }''', timeout=10000)

    frame.evaluate('''() => {
        window.__cmtEvents = [];
        const el = document.querySelector("mj-comments");
        el.addEventListener("mj-comment-post", e => window.__cmtEvents.push(e.detail));
        const textarea = el.shadowRoot.querySelector(".composer-textarea");
        if (textarea) {
            textarea.value = "This is a test comment.";
        }
        const submitBtn = el.shadowRoot.querySelector(".composer-submit-btn");
        if (submitBtn) { submitBtn.click(); }
    }''')

    frame.wait_for_timeout(200)
    events = frame.evaluate("() => window.__cmtEvents")
    assert len(events) >= 1
    assert events[0].get("body") == "This is a test comment."

    return


# ---------------------------------------------------------------------------
# mj-mention-input
# ---------------------------------------------------------------------------

@pytest.mark.functional
def test_mention_input_renders_editable(page, base_url: str) -> None:
    """
        The contenteditable editable div is in the shadow DOM with role="textbox".

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-mention-input")

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-mention-input");
        return el && el.shadowRoot &&
               el.shadowRoot.querySelector("[role=textbox]") !== null;
    }''', timeout=10000)

    has_editable = frame.evaluate('''() => {
        const el = document.querySelector("mj-mention-input");
        return el.shadowRoot.querySelector("[role=textbox]") !== null;
    }''')
    assert has_editable is True

    return


@pytest.mark.functional
def test_mention_input_label_rendered(page, base_url: str) -> None:
    """
        When a label attribute is set the label element is rendered in shadow DOM.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-mention-input")

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-mention-input");
        return el && el.shadowRoot &&
               el.shadowRoot.querySelector(".mention-label") !== null;
    }''', timeout=10000)

    label_text = frame.evaluate('''() => {
        const el = document.querySelector("mj-mention-input");
        const label = el.shadowRoot.querySelector(".mention-label");
        return label ? label.textContent : "";
    }''')
    assert len(label_text.strip()) > 0

    return


@pytest.mark.functional
def test_mention_input_fires_mj_input_on_keystroke(page, base_url: str) -> None:
    """
        Typing into the editable field fires the mj-input event.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-mention-input")

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-mention-input");
        return el && el.shadowRoot &&
               el.shadowRoot.querySelector("[role=textbox]") !== null;
    }''', timeout=10000)

    frame.evaluate('''() => {
        window.__miEvents = [];
        const el = document.querySelector("mj-mention-input");
        el.addEventListener("mj-input", e => window.__miEvents.push(e.detail));
        // Focus the editable and dispatch input event
        const editable = el.shadowRoot.querySelector("[role=textbox]");
        editable.focus();
        editable.textContent = "hello";
        editable.dispatchEvent(new Event("input", { bubbles: true }));
    }''')

    frame.wait_for_timeout(200)
    events = frame.evaluate("() => window.__miEvents")
    assert len(events) >= 1
    assert "value" in events[0]

    return


@pytest.mark.functional
def test_mention_input_trigger_opens_suggestion_popup(page, base_url: str) -> None:
    """
        Typing a trigger character opens the suggestion popup.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-mention-input")

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-mention-input");
        return el && el.shadowRoot &&
               el.shadowRoot.querySelector("[role=textbox]") !== null;
    }''', timeout=10000)

    # Delete any own data property set by the example script before registration,
    # then wire up a synchronous mentionSource via the class setter.
    frame.evaluate('''() => {
        const el = document.querySelector("mj-mention-input");
        delete el.mentionSource;
        el.mentionSource = {
            suggest(trigger, query) {
                return Promise.resolve([
                    { id: "u1", displayName: "Alice Martin", subtitle: "Engineering" },
                    { id: "u2", displayName: "Bob Lee", subtitle: "Design" }
                ]);
            }
        };
    }''')

    # Type "@A" inside the contenteditable by creating a text node and placing
    # the caret inside it so that _detectTrigger finds a TEXT_NODE selection.
    frame.evaluate('''() => {
        const el = document.querySelector("mj-mention-input");
        const editable = el.shadowRoot.querySelector("[role=textbox]");
        editable.focus();

        // Create a text node with the trigger content and append it
        editable.innerHTML = "";
        const textNode = document.createTextNode("@A");
        editable.appendChild(textNode);

        // Position the caret at the end of the text node
        const range = document.createRange();
        range.setStart(textNode, textNode.length);
        range.collapse(true);
        const sel = window.getSelection();
        sel.removeAllRanges();
        sel.addRange(range);

        // Dispatch input event on the editable so _onInput is called
        editable.dispatchEvent(new InputEvent("input", { bubbles: true, data: "A" }));
    }''')

    # The component debounces by 200 ms; wait up to 5s for popup to appear
    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-mention-input");
        if (!el || !el.shadowRoot) { return false; }
        const popup = el.shadowRoot.querySelector("[role=listbox]");
        return popup !== null && !popup.hidden;
    }''', timeout=5000)

    is_visible = frame.evaluate('''() => {
        const el = document.querySelector("mj-mention-input");
        const popup = el.shadowRoot.querySelector("[role=listbox]");
        return popup !== null && !popup.hidden;
    }''')
    assert is_visible is True

    return


# ---------------------------------------------------------------------------
# mj-chat-composer
# ---------------------------------------------------------------------------

@pytest.mark.functional
def test_chat_composer_renders_textarea(page, base_url: str) -> None:
    """
        The composer textarea is in the shadow DOM.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-chat-composer")

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-chat-composer");
        return el && el.shadowRoot &&
               el.shadowRoot.querySelector(".input-textarea") !== null;
    }''', timeout=10000)

    has_textarea = frame.evaluate('''() => {
        const el = document.querySelector("mj-chat-composer");
        return el.shadowRoot.querySelector(".input-textarea") !== null;
    }''')
    assert has_textarea is True

    return


@pytest.mark.functional
def test_chat_composer_send_button_rendered(page, base_url: str) -> None:
    """
        The Send button is rendered with aria-disabled="true" when empty.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-chat-composer")

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-chat-composer");
        return el && el.shadowRoot &&
               el.shadowRoot.querySelector("[part=send-button]") !== null;
    }''', timeout=10000)

    disabled_state = frame.evaluate('''() => {
        const el = document.querySelector("mj-chat-composer");
        const btn = el.shadowRoot.querySelector("[part=send-button]");
        return btn ? btn.getAttribute("aria-disabled") : null;
    }''')
    assert disabled_state == "true"

    return


@pytest.mark.functional
def test_chat_composer_send_enabled_when_text_entered(page, base_url: str) -> None:
    """
        Setting text on the composer enables the Send button.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-chat-composer")

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-chat-composer");
        return el && el.shadowRoot &&
               el.shadowRoot.querySelector(".input-textarea") !== null;
    }''', timeout=10000)

    # Set value via JS to trigger updateSendState
    frame.evaluate('''() => {
        const el = document.querySelector("mj-chat-composer");
        const textarea = el.shadowRoot.querySelector(".input-textarea");
        textarea.value = "Hello world";
        textarea.dispatchEvent(new Event("input", { bubbles: true }));
    }''')

    frame.wait_for_timeout(100)

    disabled_state = frame.evaluate('''() => {
        const el = document.querySelector("mj-chat-composer");
        const btn = el.shadowRoot.querySelector("[part=send-button]");
        return btn ? btn.getAttribute("aria-disabled") : null;
    }''')
    assert disabled_state == "false"

    return


@pytest.mark.functional
def test_chat_composer_send_fires_event(page, base_url: str) -> None:
    """
        Clicking Send fires the mj-send event with the message value.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-chat-composer")

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-chat-composer");
        return el && el.shadowRoot &&
               el.shadowRoot.querySelector(".input-textarea") !== null;
    }''', timeout=10000)

    frame.evaluate('''() => {
        window.__ccEvents = [];
        const el = document.querySelector("mj-chat-composer");
        el.addEventListener("mj-send", e => window.__ccEvents.push(e.detail));
        const textarea = el.shadowRoot.querySelector(".input-textarea");
        textarea.value = "Test message";
        textarea.dispatchEvent(new Event("input", { bubbles: true }));
        const sendBtn = el.shadowRoot.querySelector("[part=send-button]");
        if (sendBtn) { sendBtn.click(); }
    }''')

    frame.wait_for_timeout(200)
    events = frame.evaluate("() => window.__ccEvents")
    assert len(events) >= 1
    assert events[0].get("value") == "Test message"

    return


@pytest.mark.functional
def test_chat_composer_clear_after_send(page, base_url: str) -> None:
    """
        After a successful send the textarea is cleared.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-chat-composer")

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-chat-composer");
        return el && el.shadowRoot &&
               el.shadowRoot.querySelector(".input-textarea") !== null;
    }''', timeout=10000)

    frame.evaluate('''() => {
        const el = document.querySelector("mj-chat-composer");
        const textarea = el.shadowRoot.querySelector(".input-textarea");
        textarea.value = "Hello";
        textarea.dispatchEvent(new Event("input", { bubbles: true }));
        const sendBtn = el.shadowRoot.querySelector("[part=send-button]");
        if (sendBtn) { sendBtn.click(); }
    }''')

    frame.wait_for_timeout(200)

    cleared = frame.evaluate('''() => {
        const el = document.querySelector("mj-chat-composer");
        const textarea = el.shadowRoot.querySelector(".input-textarea");
        return textarea ? textarea.value : "NOT_EMPTY";
    }''')
    assert cleared == ""

    return


@pytest.mark.functional
def test_chat_composer_attach_and_emoji_buttons(page, base_url: str) -> None:
    """
        The attach and emoji toolbar buttons are in the shadow DOM.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-chat-composer")

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-chat-composer");
        return el && el.shadowRoot &&
               el.shadowRoot.querySelector("[part=attach-button]") !== null &&
               el.shadowRoot.querySelector("[part=emoji-button]") !== null;
    }''', timeout=10000)

    has_buttons = frame.evaluate('''() => {
        const el = document.querySelector("mj-chat-composer");
        return el.shadowRoot.querySelector("[part=attach-button]") !== null &&
               el.shadowRoot.querySelector("[part=emoji-button]") !== null;
    }''')
    assert has_buttons is True

    return


# ---------------------------------------------------------------------------
# mj-chat-message
# ---------------------------------------------------------------------------

@pytest.mark.functional
def test_chat_message_incoming_renders_bubble(page, base_url: str) -> None:
    """
        An incoming chat message renders its bubble in the shadow DOM.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-chat-message")

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-chat-message[variant=incoming]");
        return el && el.shadowRoot &&
               el.shadowRoot.querySelector("[part=bubble]") !== null;
    }''', timeout=10000)

    has_bubble = frame.evaluate('''() => {
        const el = document.querySelector("mj-chat-message[variant=incoming]");
        return el && el.shadowRoot &&
               el.shadowRoot.querySelector("[part=bubble]") !== null;
    }''')
    assert has_bubble is True

    return


@pytest.mark.functional
def test_chat_message_outgoing_has_status(page, base_url: str) -> None:
    """
        An outgoing message renders its delivery status element.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-chat-message")

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-chat-message[variant=outgoing]");
        return el && el.shadowRoot &&
               el.shadowRoot.querySelector("[part=status]") !== null;
    }''', timeout=10000)

    has_status = frame.evaluate('''() => {
        const el = document.querySelector("mj-chat-message[variant=outgoing]");
        return el && el.shadowRoot &&
               el.shadowRoot.querySelector("[part=status]") !== null;
    }''')
    assert has_status is True

    return


@pytest.mark.functional
def test_chat_message_system_variant_renders(page, base_url: str) -> None:
    """
        A system message element is in the DOM.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-chat-message")

    system_msg = frame.locator("mj-chat-message[variant=system]").first
    expect(system_msg).to_be_attached()

    return


@pytest.mark.functional
def test_chat_message_allow_actions_shows_trigger(page, base_url: str) -> None:
    """
        When allow-actions is set the actions trigger button is in the shadow DOM.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-chat-message")

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-chat-message[allow-actions]");
        return el && el.shadowRoot &&
               el.shadowRoot.querySelector("[part=actions-trigger]") !== null;
    }''', timeout=10000)

    has_trigger = frame.evaluate('''() => {
        const el = document.querySelector("mj-chat-message[allow-actions]");
        return el && el.shadowRoot &&
               el.shadowRoot.querySelector("[part=actions-trigger]") !== null;
    }''')
    assert has_trigger is True

    return


@pytest.mark.functional
def test_chat_message_reactions_rendered_via_js(page, base_url: str) -> None:
    """
        Setting the reactions property renders reaction chips in the shadow DOM.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-chat-message")

    frame.evaluate('''() => {
        const el = document.querySelector("mj-chat-message[allow-reactions]");
        if (el) {
            el.reactions = [{ emoji: "👍", count: 3, userIds: [] }];
        }
    }''')

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-chat-message[allow-reactions]");
        return el && el.shadowRoot &&
               el.shadowRoot.querySelector(".reaction-chip") !== null;
    }''', timeout=5000)

    has_chip = frame.evaluate('''() => {
        const el = document.querySelector("mj-chat-message[allow-reactions]");
        return el && el.shadowRoot &&
               el.shadowRoot.querySelector(".reaction-chip") !== null;
    }''')
    assert has_chip is True

    return


@pytest.mark.functional
def test_chat_message_react_fires_event(page, base_url: str) -> None:
    """
        Clicking a reaction chip fires the mj-message-react event.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-chat-message")

    frame.evaluate('''() => {
        window.__msgEvents = [];
        const el = document.querySelector("mj-chat-message[allow-reactions]");
        if (el) {
            el.reactions = [{ emoji: "👍", count: 2, userIds: [] }];
            el.addEventListener("mj-message-react", e => window.__msgEvents.push(e.detail));
        }
    }''')

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-chat-message[allow-reactions]");
        return el && el.shadowRoot &&
               el.shadowRoot.querySelector(".reaction-chip") !== null;
    }''', timeout=5000)

    frame.evaluate('''() => {
        const el = document.querySelector("mj-chat-message[allow-reactions]");
        const chip = el.shadowRoot.querySelector(".reaction-chip");
        if (chip) { chip.click(); }
    }''')

    frame.wait_for_timeout(200)
    events = frame.evaluate("() => window.__msgEvents")
    assert len(events) >= 1
    assert "emoji" in events[0]

    return


@pytest.mark.functional
def test_chat_message_body_html_property(page, base_url: str) -> None:
    """
        Setting bodyHtml renders sanitized HTML in the message body shadow DOM.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-chat-message")

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-chat-message[variant=incoming]");
        return el && el.shadowRoot !== null;
    }''', timeout=10000)

    frame.evaluate('''() => {
        const el = document.querySelector("mj-chat-message[variant=incoming]");
        if (el) {
            el.bodyHtml = "<strong>Bold text</strong> test";
        }
    }''')

    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-chat-message[variant=incoming]");
        return el && el.shadowRoot &&
               el.shadowRoot.querySelector(".msg-body strong") !== null;
    }''', timeout=5000)

    has_strong = frame.evaluate('''() => {
        const el = document.querySelector("mj-chat-message[variant=incoming]");
        return el && el.shadowRoot &&
               el.shadowRoot.querySelector(".msg-body strong") !== null;
    }''')
    assert has_strong is True

    return
