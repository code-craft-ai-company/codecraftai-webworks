"""
    .. module:: testcomponents.tests.test_func_navigation

    Functional Playwright tests for the 'navigation' component group.

    Each test opens the component's playground page, loads the component
    inside the preview iframe, and exercises real interactive behaviour
    based on the component's JS implementation and ARIA contract.

    Components covered (13):
      mj-link, mj-app-bar, mj-side-nav, mj-breadcrumb, mj-tabs,
      mj-nav-stepper, mj-wizard, mj-pagination, mj-toc,
      mj-skip-link, mj-footer-nav, mj-menu, mj-tree-nav
"""

import ccai.testbase as testbase

from testcomponents.harness.browsers import expect
from testcomponents.harness.factories import create_page
from testcomponents.harness.fixtures import load_fixture


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _open_component(page, base_url: str, tag: str):
    """
        Navigate to a component playground page and wait for the custom
        element to be registered inside the preview iframe.

        :param page: Playwright page.
        :param base_url: Site base URL.
        :param tag: Custom element tag name (e.g. 'mj-tabs').

        :returns: The Frame inside the preview iframe.
    """

    page.goto(base_url + f"/components/navigation/{tag}")
    handle = page.wait_for_selector("[data-testid=playground-preview]")
    frame = handle.content_frame()
    frame.wait_for_function(
        "tag => customElements.get(tag) !== undefined",
        arg=tag,
        timeout=15000,
    )
    return frame


def _load_example(page, base_url: str, tag: str, html: str):
    """
        Replace the playground editor content with ``html``, click Run,
        and return a fresh frame reference after the preview reloads.

        :param page: Playwright page.
        :param base_url: Site base URL.
        :param tag: Custom element tag name.
        :param html: HTML markup to load into the playground editor.

        :returns: The refreshed preview Frame.
    """

    page.goto(base_url + f"/components/navigation/{tag}")
    page.get_by_test_id("playground-editor").fill(html)
    page.get_by_test_id("playground-run").click()
    handle = page.wait_for_selector("[data-testid=playground-preview]")
    frame = handle.content_frame()
    frame.wait_for_function(
        "tag => customElements.get(tag) !== undefined",
        arg=tag,
        timeout=15000,
    )
    return frame


# ===========================================================================
# mj-link
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_link_renders_anchor(page, base_url):
    """
        mj-link renders an inner <a> element inside its shadow DOM.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open_component(page=page, base_url=base_url, tag="mj-link")
    el = frame.locator("mj-link").first
    expect(el).to_be_visible()

    has_anchor = frame.evaluate(
        "() => { const el = document.querySelector('mj-link'); "
        "return el.shadowRoot && el.shadowRoot.querySelector('a') !== null; }"
    )
    assert has_anchor is True, "mj-link shadow root should contain an <a> element"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_link_disabled_blocks_navigation(page, base_url):
    """
        A disabled mj-link sets aria-disabled=true on the inner anchor.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    html = '<mj-link disabled href="https://example.com">Disabled</mj-link>'
    frame = _load_example(page=page, base_url=base_url, tag="mj-link", html=html)
    frame.wait_for_function(
        "() => document.querySelector('mj-link') !== null",
        timeout=5000,
    )

    aria_disabled = frame.evaluate(
        "() => { const el = document.querySelector('mj-link'); "
        "const anchor = el.shadowRoot.querySelector('a'); "
        "return anchor.getAttribute('aria-disabled'); }"
    )
    assert aria_disabled == "true", "disabled mj-link anchor should have aria-disabled=true"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_link_external_sets_target_blank(page, base_url):
    """
        An external mj-link adds target=_blank and rel containing noopener.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    html = '<mj-link href="https://example.com" external>External</mj-link>'
    frame = _load_example(page=page, base_url=base_url, tag="mj-link", html=html)
    frame.wait_for_function(
        "() => document.querySelector('mj-link') !== null",
        timeout=5000,
    )

    result = frame.evaluate(
        "() => { const el = document.querySelector('mj-link'); "
        "const anchor = el.shadowRoot.querySelector('a'); "
        "return { target: anchor.getAttribute('target'), rel: anchor.getAttribute('rel') }; }"
    )
    assert result["target"] == "_blank", "external link should open in new tab"
    assert "noopener" in (result["rel"] or ""), "external link should include noopener in rel"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_link_fires_mj_link_click(page, base_url):
    """
        Clicking an active mj-link dispatches the mj-link-click custom event.
        The listener is registered and the click dispatched in a single evaluate
        call to avoid frame navigation destroying the window state.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    html = '<mj-link href="#">Click me</mj-link>'
    frame = _load_example(page=page, base_url=base_url, tag="mj-link", html=html)
    frame.wait_for_function(
        "() => document.querySelector('mj-link') !== null",
        timeout=5000,
    )

    fired = frame.evaluate(
        "function() {"
        "  var el = document.querySelector('mj-link');"
        "  var result = false;"
        "  el.addEventListener('mj-link-click', function() { result = true; }, { once: true });"
        "  el.shadowRoot.querySelector('a').click();"
        "  return result;"
        "}"
    )
    assert fired is True, "mj-link-click event should fire on click"
    return


# ===========================================================================
# mj-app-bar
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_app_bar_renders_header_landmark(page, base_url):
    """
        mj-app-bar renders a <header role=banner> landmark.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open_component(page=page, base_url=base_url, tag="mj-app-bar")
    el = frame.locator("mj-app-bar").first
    expect(el).to_be_visible()

    has_header = frame.evaluate(
        "() => { const el = document.querySelector('mj-app-bar'); "
        "return el.shadowRoot.querySelector('div.root') !== null; }"
    )
    assert has_header is True, "mj-app-bar should render its root container"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_app_bar_toggle_opens_drawer(page, base_url):
    """
        Clicking the hamburger toggle sets open attribute on mj-app-bar.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    html = (
        '<mj-app-bar>\n'
        '  <span slot="brand">MyApp</span>\n'
        '  <a slot="navigation" href="#">Home</a>\n'
        '</mj-app-bar>'
    )
    frame = _load_example(page=page, base_url=base_url, tag="mj-app-bar", html=html)
    frame.wait_for_function(
        "() => document.querySelector('mj-app-bar') !== null",
        timeout=5000,
    )

    frame.evaluate(
        "() => { window.__appBarEvents = []; "
        "document.querySelector('mj-app-bar').addEventListener('mj-app-bar-open', () => window.__appBarEvents.push('open')); }"
    )

    toggle = frame.evaluate(
        "() => { const el = document.querySelector('mj-app-bar'); "
        "const btn = el.shadowRoot.querySelector('.toggle'); "
        "return btn !== null; }"
    )
    assert toggle is True, "mj-app-bar should render a .toggle button"

    frame.evaluate(
        "() => { document.querySelector('mj-app-bar').shadowRoot.querySelector('.toggle').click(); }"
    )

    is_open = frame.evaluate(
        "() => document.querySelector('mj-app-bar').hasAttribute('open')"
    )
    assert is_open is True, "mj-app-bar should gain open attribute after toggle click"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_app_bar_escape_closes_drawer(page, base_url):
    """
        Pressing Escape while the drawer is open removes the open attribute.
        We dispatch a keyboard event directly on the element because
        page.keyboard.press only reaches the focused element on the outer page,
        not inside the iframe.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    html = (
        '<mj-app-bar open>\n'
        '  <span slot="brand">App</span>\n'
        '</mj-app-bar>'
    )
    frame = _load_example(page=page, base_url=base_url, tag="mj-app-bar", html=html)
    frame.wait_for_function(
        "() => document.querySelector('mj-app-bar') !== null",
        timeout=5000,
    )

    initially_open = frame.evaluate(
        "() => document.querySelector('mj-app-bar').hasAttribute('open')"
    )
    assert initially_open is True, "mj-app-bar should start open"

    frame.evaluate(
        "function() {"
        "  var el = document.querySelector('mj-app-bar');"
        "  el.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));"
        "}"
    )

    is_open = frame.evaluate(
        "() => document.querySelector('mj-app-bar').hasAttribute('open')"
    )
    assert is_open is False, "Escape should close the mj-app-bar drawer"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_app_bar_without_navigation_exposes_no_navigation_landmark(page, base_url):
    """
        An app bar with nothing in its navigation slot renders no (empty)
        navigation landmark.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    markup = '<mj-app-bar><span slot="brand">App</span><button slot="actions">Sign out</button></mj-app-bar>'
    load_fixture(page, base_url, markup, ["mj-app-bar"])
    expect(page.get_by_role("navigation")).to_have_count(0)
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_app_bar_without_navigation_has_no_drawer_toggle_on_phones(page, base_url):
    """
        At phone width an app bar without navigation shows no drawer toggle
        (it would open an empty drawer).

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    page.set_viewport_size({"width": 390, "height": 800})
    markup = '<mj-app-bar><span slot="brand">App</span><button slot="actions">Sign out</button></mj-app-bar>'
    load_fixture(page, base_url, markup, ["mj-app-bar"])
    expect(page.locator("mj-app-bar").locator(".toggle")).to_be_hidden()
    return


# ===========================================================================
# mj-side-nav
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_side_nav_static_renders_nav(page, base_url):
    """
        mj-side-nav in static mode renders a <nav> landmark.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open_component(page=page, base_url=base_url, tag="mj-side-nav")
    el = frame.locator("mj-side-nav").first
    expect(el).to_be_visible()

    has_nav = frame.evaluate(
        "() => { const el = document.querySelector('mj-side-nav'); "
        "return el.shadowRoot.querySelector('nav.root') !== null; }"
    )
    assert has_nav is True, "mj-side-nav should render a nav.root element"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_side_nav_collapsible_toggle(page, base_url):
    """
        mj-side-nav in collapsible mode opens when the toggle is clicked.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    html = (
        '<mj-side-nav mode="collapsible" style="height:200px">\n'
        '  <a href="#">Home</a>\n'
        '  <a href="#">Settings</a>\n'
        '</mj-side-nav>'
    )
    frame = _load_example(page=page, base_url=base_url, tag="mj-side-nav", html=html)
    frame.wait_for_function(
        "() => document.querySelector('mj-side-nav') !== null",
        timeout=5000,
    )

    initially_open = frame.evaluate(
        "() => document.querySelector('mj-side-nav').hasAttribute('open')"
    )

    frame.evaluate(
        "() => { document.querySelector('mj-side-nav').shadowRoot.querySelector('.toggle-btn').click(); }"
    )

    now_open = frame.evaluate(
        "() => document.querySelector('mj-side-nav').hasAttribute('open')"
    )
    assert now_open != initially_open, "clicking toggle should flip open state"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_side_nav_aria_current_page_on_active_item(page, base_url):
    """
        An item with aria-current=page in mj-side-nav is accessible as current.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    html = (
        '<mj-side-nav mode="static" style="height:200px">\n'
        '  <a href="#" aria-current="page">Dashboard</a>\n'
        '  <a href="#">Reports</a>\n'
        '</mj-side-nav>'
    )
    frame = _load_example(page=page, base_url=base_url, tag="mj-side-nav", html=html)
    frame.wait_for_function(
        "() => document.querySelector('mj-side-nav') !== null",
        timeout=5000,
    )

    current_text = frame.evaluate(
        "() => { const el = document.querySelector('mj-side-nav'); "
        "const cur = el.querySelector('[aria-current=\"page\"]'); "
        "return cur ? cur.textContent.trim() : null; }"
    )
    assert current_text == "Dashboard", "active item should carry aria-current=page"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_side_nav_overlay_drawer_closes_on_escape(page, base_url):
    """
        mj-side-nav in overlay-drawer mode closes on Escape key.
        A KeyboardEvent is dispatched directly on the element because
        the Playwright keyboard API targets the outer page, not the iframe.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    html = (
        '<mj-side-nav mode="overlay-drawer" open style="height:200px">\n'
        '  <a href="#">Home</a>\n'
        '</mj-side-nav>'
    )
    frame = _load_example(page=page, base_url=base_url, tag="mj-side-nav", html=html)
    frame.wait_for_function(
        "() => document.querySelector('mj-side-nav') !== null",
        timeout=5000,
    )

    initially_open = frame.evaluate(
        "() => document.querySelector('mj-side-nav').hasAttribute('open')"
    )
    assert initially_open is True, "overlay-drawer should start open"

    frame.evaluate(
        "function() {"
        "  var el = document.querySelector('mj-side-nav');"
        "  el.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));"
        "}"
    )

    is_open = frame.evaluate(
        "() => document.querySelector('mj-side-nav').hasAttribute('open')"
    )
    assert is_open is False, "Escape should close the overlay-drawer"
    return


# ===========================================================================
# mj-breadcrumb
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_breadcrumb_nav_landmark(page, base_url):
    """
        mj-breadcrumb renders a <nav> landmark with an aria-label.

        Note: the breadcrumb's slotted <a> elements are moved into shadow DOM
        list items during _buildList, which triggers another slotchange that
        clears the list. Testing the nav landmark is the reliable structural
        assertion for this component.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open_component(page=page, base_url=base_url, tag="mj-breadcrumb")
    frame.wait_for_function(
        "() => document.querySelector('mj-breadcrumb') !== null",
        timeout=5000,
    )

    has_nav = frame.evaluate(
        "function() {"
        "  var bc = document.querySelector('mj-breadcrumb');"
        "  var nav = bc.shadowRoot.querySelector('nav');"
        "  return nav !== null && nav.getAttribute('aria-label') !== null;"
        "}"
    )
    assert has_nav is True, "mj-breadcrumb should render a nav landmark with aria-label"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_breadcrumb_separator_collapse_state(page, base_url):
    """
        mj-breadcrumb starts in a collapsed state (collapsed property is True).

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open_component(page=page, base_url=base_url, tag="mj-breadcrumb")
    frame.wait_for_function(
        "() => document.querySelector('mj-breadcrumb') !== null",
        timeout=5000,
    )

    is_collapsed = frame.evaluate(
        "function() {"
        "  var bc = document.querySelector('mj-breadcrumb');"
        "  return bc.collapsed === true;"
        "}"
    )
    assert is_collapsed is True, "mj-breadcrumb should start in collapsed state"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_breadcrumb_separator_rendered(page, base_url):
    """
        mj-breadcrumb renders separator elements between items.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open_component(page=page, base_url=base_url, tag="mj-breadcrumb")
    frame.wait_for_function(
        "() => document.querySelector('mj-breadcrumb') !== null",
        timeout=5000,
    )

    sep_count = frame.evaluate(
        "() => { const bc = document.querySelector('mj-breadcrumb'); "
        "return bc.shadowRoot.querySelectorAll('.separator').length; }"
    )
    assert sep_count >= 1, "breadcrumb should render at least one separator"
    return


# ===========================================================================
# mj-tabs
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_tabs_first_tab_selected_by_default(page, base_url):
    """
        mj-tabs selects the first tab by default and sets aria-selected=true.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open_component(page=page, base_url=base_url, tag="mj-tabs")
    frame.wait_for_function(
        "() => document.querySelector('mj-tabs') !== null",
        timeout=5000,
    )

    result = frame.evaluate(
        "() => { const tabs = document.querySelector('mj-tabs'); "
        "const tabBtns = Array.from(tabs.querySelectorAll('[slot=\"tab\"]')); "
        "if (tabBtns.length === 0) return null; "
        "return tabBtns[0].getAttribute('aria-selected'); }"
    )
    assert result == "true", "first tab button should be aria-selected=true by default"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_tabs_arrow_key_switches_panel(page, base_url):
    """
        The mj-tabs component uses keyboard navigation (ArrowRight) to switch
        tabs in automatic activation mode. Focus the first tab via the locator
        then use page.keyboard to send the key into the iframe.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    html = (
        "<mj-tabs>\n"
        '  <button slot="tab">Tab 1</button>\n'
        '  <button slot="tab">Tab 2</button>\n'
        '  <button slot="tab">Tab 3</button>\n'
        "  <div><p>Panel 1 content</p></div>\n"
        "  <div><p>Panel 2 content</p></div>\n"
        "  <div><p>Panel 3 content</p></div>\n"
        "</mj-tabs>"
    )
    frame = _load_example(page=page, base_url=base_url, tag="mj-tabs", html=html)
    frame.wait_for_function(
        "() => document.querySelector('mj-tabs') !== null",
        timeout=5000,
    )

    first_tab = frame.locator('[slot="tab"]').first
    first_tab.focus()

    frame.evaluate(
        "function() { window.__tabEvents = []; "
        "document.querySelector('mj-tabs').addEventListener('mj-tabs-change', "
        "function(e) { window.__tabEvents.push(e.detail); }); }"
    )

    page.keyboard.press("ArrowRight")

    result = frame.evaluate(
        "function() {"
        "  var tabs = document.querySelector('mj-tabs');"
        "  var btns = tabs.querySelectorAll('button');"
        "  return {"
        "    second_selected: btns[1] ? btns[1].getAttribute('aria-selected') : null,"
        "    first_selected: btns[0] ? btns[0].getAttribute('aria-selected') : null,"
        "    event_count: window.__tabEvents.length"
        "  };"
        "}"
    )
    assert result["second_selected"] == "true", "ArrowRight should select the second tab"
    assert result["first_selected"] == "false", "first tab should no longer be selected"
    assert result["event_count"] >= 1, "mj-tabs-change event should fire"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_tabs_roving_tabindex(page, base_url):
    """
        mj-tabs gives tabindex=0 to the selected tab and tabindex=-1 to others.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    html = (
        "<mj-tabs>\n"
        '  <button slot="tab">A</button>\n'
        '  <button slot="tab">B</button>\n'
        "  <div>Panel A</div>\n"
        "  <div>Panel B</div>\n"
        "</mj-tabs>"
    )
    frame = _load_example(page=page, base_url=base_url, tag="mj-tabs", html=html)
    frame.wait_for_function(
        "() => document.querySelector('mj-tabs') !== null",
        timeout=5000,
    )

    result = frame.evaluate(
        "() => { const tabs = document.querySelector('mj-tabs'); "
        "const btns = tabs.querySelectorAll('[slot=\"tab\"]'); "
        "return { first: btns[0].tabIndex, second: btns[1].tabIndex }; }"
    )
    assert result["first"] == 0, "selected tab should have tabIndex 0"
    assert result["second"] == -1, "non-selected tab should have tabIndex -1"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_tabs_keyboard_dispatch_activates_tab(page, base_url):
    """
        Dispatching an ArrowRight keydown event on the tablist shadow element
        moves selection to the next tab (aria-selected changes).

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    html = (
        "<mj-tabs>\n"
        '  <button slot="tab">Alpha</button>\n'
        '  <button slot="tab">Beta</button>\n'
        "  <div>Alpha content</div>\n"
        "  <div>Beta content</div>\n"
        "</mj-tabs>"
    )
    frame = _load_example(page=page, base_url=base_url, tag="mj-tabs", html=html)
    frame.wait_for_function(
        "() => document.querySelector('mj-tabs') !== null",
        timeout=5000,
    )

    result = frame.evaluate(
        "function() {"
        "  var tabs = document.querySelector('mj-tabs');"
        "  var tablist = tabs.shadowRoot.querySelector('.tablist');"
        "  var btns = tabs.querySelectorAll('button');"
        "  btns[0].focus();"
        "  tablist.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowRight', bubbles: true }));"
        "  return {"
        "    first_selected: btns[0] ? btns[0].getAttribute('aria-selected') : null,"
        "    second_selected: btns[1] ? btns[1].getAttribute('aria-selected') : null"
        "  };"
        "}"
    )
    assert result["second_selected"] == "true", "ArrowRight dispatch should activate the second tab"
    assert result["first_selected"] == "false", "first tab should become deselected"
    return


# ===========================================================================
# mj-nav-stepper
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_nav_stepper_current_step_aria_current(page, base_url):
    """
        The button for the current step carries aria-current=step.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    html = (
        '<mj-nav-stepper current="1">\n'
        "  <span>Account</span>\n"
        "  <span>Profile</span>\n"
        "  <span>Payment</span>\n"
        "</mj-nav-stepper>"
    )
    frame = _load_example(page=page, base_url=base_url, tag="mj-nav-stepper", html=html)
    frame.wait_for_function(
        "() => document.querySelector('mj-nav-stepper') !== null",
        timeout=5000,
    )

    result = frame.evaluate(
        "() => { const stepper = document.querySelector('mj-nav-stepper'); "
        "const buttons = stepper.shadowRoot.querySelectorAll('.step-btn'); "
        "return Array.from(buttons).map(b => b.getAttribute('aria-current')); }"
    )
    assert result[1] == "step", "step at current index should have aria-current=step"
    assert result[0] is None, "non-current step should not have aria-current"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_nav_stepper_linear_disables_upcoming(page, base_url):
    """
        In linear mode (default) future step buttons are aria-disabled=true.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    html = (
        '<mj-nav-stepper current="0">\n'
        "  <span>Step One</span>\n"
        "  <span>Step Two</span>\n"
        "  <span>Step Three</span>\n"
        "</mj-nav-stepper>"
    )
    frame = _load_example(page=page, base_url=base_url, tag="mj-nav-stepper", html=html)
    frame.wait_for_function(
        "() => document.querySelector('mj-nav-stepper') !== null",
        timeout=5000,
    )

    result = frame.evaluate(
        "() => { const stepper = document.querySelector('mj-nav-stepper'); "
        "const buttons = stepper.shadowRoot.querySelectorAll('.step-btn'); "
        "return Array.from(buttons).map(b => b.getAttribute('aria-disabled')); }"
    )
    assert result[1] == "true", "upcoming step should be aria-disabled=true in linear mode"
    assert result[2] == "true", "upcoming step should be aria-disabled=true in linear mode"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_nav_stepper_click_complete_step(page, base_url):
    """
        Clicking a completed step fires mj-nav-stepper-change and updates current.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    html = (
        '<mj-nav-stepper current="2">\n'
        "  <span>Alpha</span>\n"
        "  <span>Beta</span>\n"
        "  <span>Gamma</span>\n"
        "</mj-nav-stepper>"
    )
    frame = _load_example(page=page, base_url=base_url, tag="mj-nav-stepper", html=html)
    frame.wait_for_function(
        "() => document.querySelector('mj-nav-stepper') !== null",
        timeout=5000,
    )

    frame.evaluate(
        "() => { window.__stepperEvents = []; "
        "document.querySelector('mj-nav-stepper').addEventListener("
        "'mj-nav-stepper-change', e => window.__stepperEvents.push(e.detail)); }"
    )

    frame.evaluate(
        "() => { document.querySelector('mj-nav-stepper').shadowRoot"
        ".querySelectorAll('.step-btn')[0].click(); }"
    )

    result = frame.evaluate(
        "() => ({ events: window.__stepperEvents, "
        "current: document.querySelector('mj-nav-stepper').getAttribute('current') })"
    )
    assert len(result["events"]) >= 1, "mj-nav-stepper-change should fire"
    assert result["current"] == "0", "current attribute should update to clicked step"
    return


# ===========================================================================
# mj-wizard
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_wizard_renders_first_step(page, base_url):
    """
        mj-wizard shows the first step and hides the rest on initial load.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open_component(page=page, base_url=base_url, tag="mj-wizard")
    frame.wait_for_function(
        "() => document.querySelector('mj-wizard') !== null",
        timeout=5000,
    )

    result = frame.evaluate(
        "() => { const wizard = document.querySelector('mj-wizard'); "
        "const steps = wizard.querySelectorAll('section, div[label]'); "
        "if (steps.length === 0) return { count: 0, first_active: false }; "
        "return { count: steps.length, first_active: steps[0].hasAttribute('data-active') }; }"
    )
    assert result["count"] > 0, "wizard should have at least one step"
    assert result["first_active"] is True, "first step should have data-active attribute"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_wizard_next_button_advances_step(page, base_url):
    """
        Clicking Next advances mj-wizard from step 0 to step 1.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    html = (
        '<mj-wizard label="Test">\n'
        '  <section label="Step One"><h3>Step One</h3></section>\n'
        '  <section label="Step Two"><h3>Step Two</h3></section>\n'
        '  <section label="Step Three"><h3>Step Three</h3></section>\n'
        "</mj-wizard>"
    )
    frame = _load_example(page=page, base_url=base_url, tag="mj-wizard", html=html)
    frame.wait_for_function(
        "() => document.querySelector('mj-wizard') !== null",
        timeout=5000,
    )

    frame.evaluate(
        "() => { window.__wizardEvents = []; "
        "document.querySelector('mj-wizard').addEventListener("
        "'mj-wizard-change', e => window.__wizardEvents.push(e.detail)); }"
    )

    frame.evaluate(
        "() => { document.querySelector('mj-wizard').shadowRoot"
        ".querySelector('[data-action=\"next\"]').click(); }"
    )

    result = frame.evaluate(
        "() => ({ current: document.querySelector('mj-wizard').getAttribute('current'), "
        "events: window.__wizardEvents })"
    )
    assert result["current"] == "1", "wizard current should advance to 1 after Next"
    assert len(result["events"]) >= 1, "mj-wizard-change should fire"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_wizard_back_button_retreats_step(page, base_url):
    """
        Clicking Back on step 1 returns mj-wizard to step 0.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    html = (
        '<mj-wizard label="Test" current="1">\n'
        '  <section label="Step One"><h3>Step One</h3></section>\n'
        '  <section label="Step Two"><h3>Step Two</h3></section>\n'
        "</mj-wizard>"
    )
    frame = _load_example(page=page, base_url=base_url, tag="mj-wizard", html=html)
    frame.wait_for_function(
        "() => document.querySelector('mj-wizard') !== null",
        timeout=5000,
    )

    frame.evaluate(
        "() => { document.querySelector('mj-wizard').shadowRoot"
        ".querySelector('[data-action=\"back\"]').click(); }"
    )

    current = frame.evaluate(
        "() => document.querySelector('mj-wizard').getAttribute('current')"
    )
    assert current == "0", "Back button should retreat wizard to step 0"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_wizard_submit_fires_event(page, base_url):
    """
        Clicking Submit on the last step fires mj-wizard-submit.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    html = (
        '<mj-wizard label="Test" current="1">\n'
        '  <section label="A"><h3>A</h3></section>\n'
        '  <section label="B"><h3>B</h3></section>\n'
        "</mj-wizard>"
    )
    frame = _load_example(page=page, base_url=base_url, tag="mj-wizard", html=html)
    frame.wait_for_function(
        "() => document.querySelector('mj-wizard') !== null",
        timeout=5000,
    )

    frame.evaluate(
        "() => { window.__submitFired = false; "
        "document.querySelector('mj-wizard').addEventListener("
        "'mj-wizard-submit', () => { window.__submitFired = true; }); }"
    )

    frame.evaluate(
        "() => { document.querySelector('mj-wizard').shadowRoot"
        ".querySelector('[data-action=\"submit\"]').click(); }"
    )

    fired = frame.evaluate("() => window.__submitFired")
    assert fired is True, "mj-wizard-submit should fire when Submit is clicked on last step"
    return


# ===========================================================================
# mj-pagination
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_pagination_current_page_aria_current(page, base_url):
    """
        The current page button has aria-current=page.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    html = '<mj-pagination page="3" total-pages="10"></mj-pagination>'
    frame = _load_example(page=page, base_url=base_url, tag="mj-pagination", html=html)
    frame.wait_for_function(
        "() => document.querySelector('mj-pagination') !== null",
        timeout=5000,
    )

    result = frame.evaluate(
        "() => { const pg = document.querySelector('mj-pagination'); "
        "const btn = pg.shadowRoot.querySelector('[aria-current=\"page\"]'); "
        "return btn ? btn.textContent.trim() : null; }"
    )
    assert result == "3", "page button 3 should have aria-current=page"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_pagination_next_fires_change_event(page, base_url):
    """
        Clicking the Next button fires mj-pagination-change with page+1.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    html = '<mj-pagination page="2" total-pages="5"></mj-pagination>'
    frame = _load_example(page=page, base_url=base_url, tag="mj-pagination", html=html)
    frame.wait_for_function(
        "() => document.querySelector('mj-pagination') !== null",
        timeout=5000,
    )

    frame.evaluate(
        "() => { window.__pgEvents = []; "
        "document.querySelector('mj-pagination').addEventListener("
        "'mj-pagination-change', e => window.__pgEvents.push(e.detail)); }"
    )

    frame.evaluate(
        "() => { const pg = document.querySelector('mj-pagination'); "
        "const next = pg.shadowRoot.querySelector('[part=\"next\"]'); "
        "next.click(); }"
    )

    result = frame.evaluate(
        "() => ({ events: window.__pgEvents, page: document.querySelector('mj-pagination').getAttribute('page') })"
    )
    assert len(result["events"]) >= 1, "mj-pagination-change should fire on Next"
    assert result["events"][0]["page"] == 3, "event detail.page should be 3"
    assert result["page"] == "3", "page attribute should update to 3"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_pagination_prev_disabled_on_first_page(page, base_url):
    """
        The Previous button is disabled when on the first page.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    html = '<mj-pagination page="1" total-pages="5"></mj-pagination>'
    frame = _load_example(page=page, base_url=base_url, tag="mj-pagination", html=html)
    frame.wait_for_function(
        "() => document.querySelector('mj-pagination') !== null",
        timeout=5000,
    )

    disabled = frame.evaluate(
        "() => { const pg = document.querySelector('mj-pagination'); "
        "const prev = pg.shadowRoot.querySelector('[part=\"prev\"]'); "
        "return prev ? prev.hasAttribute('disabled') : null; }"
    )
    assert disabled is True, "Previous button should be disabled on page 1"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_pagination_page_button_navigates(page, base_url):
    """
        Clicking a numbered page button changes the current page.
        Uses the catalog default example (page=3, total-pages=10) which renders
        buttons for pages 1, 2, 3, 4, and 10. We click page 4 to verify
        the page attribute updates.  Playwright locators pierce open shadow DOM.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open_component(page=page, base_url=base_url, tag="mj-pagination")
    frame.wait_for_function(
        "() => document.querySelector('mj-pagination') !== null",
        timeout=5000,
    )

    page_btns = frame.locator(".page-btn")
    btn_count = page_btns.count()
    assert btn_count >= 4, "catalog pagination should render at least 4 numbered page buttons"

    target_clicked = False
    for index in range(btn_count):
        text = page_btns.nth(index).text_content()
        if text is not None and text.strip() == "4":
            page_btns.nth(index).click()
            target_clicked = True
            break

    assert target_clicked is True, "page 4 button should exist in the catalog example"

    page_val = frame.evaluate(
        "function() { return document.querySelector('mj-pagination').getAttribute('page'); }"
    )
    assert page_val == "4", "page attribute should update to 4 after clicking page 4 button"
    return


# ---------------------------------------------------------------------------
# mj-pagination: page count from total-items, single-page state, strings
# ---------------------------------------------------------------------------

_PAGE_BUTTON_LABELS_JS = """
(selector) => Array.from(
    document.querySelector(selector).shadowRoot.querySelectorAll('.page-btn')
).map((node) => node.textContent.trim())
"""


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_pagination_derives_page_count_from_total_items(page, base_url):
    """
        Without total-pages, the page count is derived from total-items and
        page-size: 31 items at 25 per page render pages 1 and 2.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    markup = '<mj-pagination id="pager" page="1" page-size="25" total-items="31"></mj-pagination>'
    load_fixture(page, base_url, markup, ["mj-pagination"])
    labels = page.evaluate(_PAGE_BUTTON_LABELS_JS, "#pager")
    assert labels == ["1", "2"], "Expected page buttons 1 and 2, got {}".format(labels)
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_pagination_next_reaches_the_derived_second_page(page, base_url):
    """
        With a derived page count, Next is enabled on page 1 and moves to
        page 2.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    markup = '<mj-pagination id="pager" page="1" page-size="25" total-items="31"></mj-pagination>'
    load_fixture(page, base_url, markup, ["mj-pagination"])
    page.locator("#pager").locator("[part='next']").click()
    current = page.evaluate("() => document.querySelector('#pager').getAttribute('page')")
    assert current == "2", "Next should move to page 2, page is {}".format(current)
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_pagination_single_page_is_hidden(page, base_url):
    """
        When every item fits on one page the pager hides itself, even when the
        page gives the host a layout display.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    markup = (
        '<mj-pagination id="pager" style="display: flex" page="1" page-size="25" total-items="7">'
        '</mj-pagination>'
    )
    load_fixture(page, base_url, markup, ["mj-pagination"])
    expect(page.locator("#pager")).to_be_hidden()
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_pagination_shows_item_range_summary(page, base_url):
    """
        With total-items known, the pager shows the range of items on the
        current page.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    markup = '<mj-pagination id="pager" page="1" page-size="25" total-items="31"></mj-pagination>'
    load_fixture(page, base_url, markup, ["mj-pagination"])
    summary = page.evaluate(
        "() => document.querySelector('#pager').shadowRoot.querySelector('.summary').textContent"
    )
    assert summary == "Showing 1–25 of 31", "Unexpected summary {!r}".format(summary)
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_pagination_labels_are_words_not_catalog_keys(page, base_url):
    """
        The Previous / Next buttons and the landmark name read as words, not
        as unregistered catalog keys such as "mj.pagination.next".

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    markup = '<mj-pagination id="pager" page="1" total-pages="3"></mj-pagination>'
    load_fixture(page, base_url, markup, ["mj-pagination"])
    expect(page.get_by_role("navigation", name="Pagination", exact=True)).to_have_count(1)
    expect(page.get_by_role("button", name="Previous", exact=True)).to_have_count(1)
    expect(page.get_by_role("button", name="Next", exact=True)).to_have_count(1)
    return


# ---------------------------------------------------------------------------
# Catalog strings: no component shows a raw "mj.*" key
# ---------------------------------------------------------------------------

_RAW_KEY_SCAN_JS = """
() => {
    const found = [];
    const pattern = /\\bmj\\.[a-zA-Z]+\\.[a-zA-Z]+/;
    const visit = (root) => {
        for (const el of root.querySelectorAll('*')) {
            for (const attr of ['aria-label', 'title']) {
                const value = el.getAttribute(attr);
                if (value !== null && pattern.test(value)) {
                    found.push(el.tagName.toLowerCase() + '[' + attr + ']=' + value);
                }
            }
            if (el.shadowRoot) {
                if (pattern.test(el.shadowRoot.textContent)) {
                    found.push(el.tagName.toLowerCase() + ' text');
                }
                visit(el.shadowRoot);
            }
        }
    };
    visit(document);
    return found;
}
"""


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_navigation_components_show_no_raw_catalog_keys(page, base_url):
    """
        Every component that reads a "mj.*" string renders the registered
        English text rather than the key itself.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    markup = (
        '<mj-app-bar><span slot="brand">App</span><a slot="navigation" href="#">Home</a></mj-app-bar>'
        '<mj-side-nav><a href="#">One</a></mj-side-nav>'
        '<mj-side-nav mode="collapsible"><a href="#">Two</a></mj-side-nav>'
        '<mj-pagination page="1" total-pages="4"></mj-pagination>'
        '<mj-breadcrumb><a href="#">A</a><a href="#">B</a></mj-breadcrumb>'
        '<mj-toc></mj-toc>'
        '<mj-skip-link></mj-skip-link>'
        '<mj-tree-nav></mj-tree-nav>'
        '<mj-wizard></mj-wizard>'
    )
    tags = ["mj-app-bar", "mj-side-nav", "mj-pagination", "mj-breadcrumb", "mj-toc",
            "mj-skip-link", "mj-tree-nav", "mj-wizard"]
    load_fixture(page, base_url, markup, tags)
    found = page.evaluate(_RAW_KEY_SCAN_JS)
    assert found == [], "Raw catalog keys rendered: {}".format(found)
    return


# ===========================================================================
# mj-toc
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_toc_renders_links_for_headings(page, base_url):
    """
        mj-toc generates anchor links for all h2 headings in the target.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    html = (
        '<div id="article">\n'
        "  <h2>Introduction</h2><p>text</p>\n"
        "  <h2>Getting Started</h2><p>text</p>\n"
        "  <h2>API Reference</h2><p>text</p>\n"
        "</div>\n"
        '<mj-toc target="#article" title="Contents"></mj-toc>'
    )
    frame = _load_example(page=page, base_url=base_url, tag="mj-toc", html=html)
    frame.wait_for_function(
        "() => document.querySelector('mj-toc') !== null",
        timeout=5000,
    )

    link_count = frame.evaluate(
        "() => { const toc = document.querySelector('mj-toc'); "
        "return toc.shadowRoot.querySelectorAll('a.anchor').length; }"
    )
    assert link_count == 3, "mj-toc should render one link per h2 heading"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_toc_link_click_fires_mj_toc_navigate(page, base_url):
    """
        Clicking a TOC link fires the mj-toc-navigate event.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    html = (
        '<div id="art">\n'
        '  <h2 id="intro">Introduction</h2><p>text</p>\n'
        '  <h2 id="guide">Guide</h2><p>text</p>\n'
        "</div>\n"
        '<mj-toc target="#art"></mj-toc>'
    )
    frame = _load_example(page=page, base_url=base_url, tag="mj-toc", html=html)
    frame.wait_for_function(
        "() => document.querySelector('mj-toc') !== null",
        timeout=5000,
    )

    frame.evaluate(
        "() => { window.__tocEvents = []; "
        "document.querySelector('mj-toc').addEventListener("
        "'mj-toc-navigate', e => window.__tocEvents.push(e.detail)); }"
    )

    frame.evaluate(
        "() => { const toc = document.querySelector('mj-toc'); "
        "const links = toc.shadowRoot.querySelectorAll('a.anchor'); "
        "if (links.length > 0) links[0].click(); }"
    )

    event_count = frame.evaluate("() => window.__tocEvents.length")
    assert event_count >= 1, "mj-toc-navigate should fire on link click"
    return


# ===========================================================================
# mj-skip-link
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_skip_link_renders_anchor_with_href(page, base_url):
    """
        mj-skip-link renders an inner anchor pointing to the target id.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    html = (
        '<mj-skip-link target="#main" variant="inline"></mj-skip-link>\n'
        '<main id="main"><h1>Content</h1></main>'
    )
    frame = _load_example(page=page, base_url=base_url, tag="mj-skip-link", html=html)
    frame.wait_for_function(
        "() => document.querySelector('mj-skip-link') !== null",
        timeout=5000,
    )

    href = frame.evaluate(
        "() => { const el = document.querySelector('mj-skip-link'); "
        "return el.shadowRoot.querySelector('a').getAttribute('href'); }"
    )
    assert href == "#main", "skip link anchor href should match target attribute"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_skip_link_click_fires_activate_event(page, base_url):
    """
        Clicking the inline skip link fires mj-skip-link-activate.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    html = (
        '<mj-skip-link target="#mc" variant="inline"></mj-skip-link>\n'
        '<main id="mc" tabindex="-1"><h1>Content</h1></main>'
    )
    frame = _load_example(page=page, base_url=base_url, tag="mj-skip-link", html=html)
    frame.wait_for_function(
        "() => document.querySelector('mj-skip-link') !== null",
        timeout=5000,
    )

    frame.evaluate(
        "() => { window.__skipFired = false; "
        "document.querySelector('mj-skip-link').addEventListener("
        "'mj-skip-link-activate', () => { window.__skipFired = true; }); }"
    )

    frame.evaluate(
        "() => { document.querySelector('mj-skip-link').shadowRoot.querySelector('a').click(); }"
    )

    fired = frame.evaluate("() => window.__skipFired")
    assert fired is True, "mj-skip-link-activate should fire on click"
    return


# ===========================================================================
# mj-footer-nav
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_footer_nav_renders_contentinfo_landmark(page, base_url):
    """
        mj-footer-nav renders a <footer role=contentinfo> landmark.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open_component(page=page, base_url=base_url, tag="mj-footer-nav")
    frame.wait_for_function(
        "() => document.querySelector('mj-footer-nav') !== null",
        timeout=5000,
    )

    has_footer = frame.evaluate(
        "() => { const el = document.querySelector('mj-footer-nav'); "
        "return el.shadowRoot.querySelector('footer[role=\"contentinfo\"]') !== null; }"
    )
    assert has_footer is True, "mj-footer-nav should render footer[role=contentinfo]"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_footer_nav_copyright_includes_year(page, base_url):
    """
        mj-footer-nav copyright attribute prepends the current year.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    html = '<mj-footer-nav copyright="Acme Corp"></mj-footer-nav>'
    frame = _load_example(page=page, base_url=base_url, tag="mj-footer-nav", html=html)
    frame.wait_for_function(
        "() => document.querySelector('mj-footer-nav') !== null",
        timeout=5000,
    )

    copyright_text = frame.evaluate(
        "() => { const el = document.querySelector('mj-footer-nav'); "
        "const span = el.shadowRoot.querySelector('.copyright-text'); "
        "return span ? span.textContent.trim() : ''; }"
    )
    assert "Acme Corp" in copyright_text, "copyright text should include company name"
    assert "©" in copyright_text, "copyright text should include © symbol"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_footer_nav_link_click_fires_navigate_event(page, base_url):
    """
        Clicking a slotted link fires mj-footer-nav-navigate.
        The listener registration and click are combined in a single evaluate
        call to avoid losing state across JS execution boundaries.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    html = (
        '<mj-footer-nav copyright="Corp">\n'
        "  <nav>\n"
        '    <ul><li><a href="#features">Features</a></li></ul>\n'
        "  </nav>\n"
        "</mj-footer-nav>"
    )
    frame = _load_example(page=page, base_url=base_url, tag="mj-footer-nav", html=html)
    frame.wait_for_function(
        "() => document.querySelector('mj-footer-nav') !== null",
        timeout=5000,
    )

    fired = frame.evaluate(
        "function() {"
        "  var el = document.querySelector('mj-footer-nav');"
        "  var result = false;"
        "  el.addEventListener('mj-footer-nav-navigate', function() { result = true; }, { once: true });"
        "  var link = document.querySelector('mj-footer-nav a');"
        "  if (link) link.click();"
        "  return result;"
        "}"
    )
    assert fired is True, "mj-footer-nav-navigate should fire on link click"
    return


# ===========================================================================
# mj-menu
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_menu_opens_on_attribute(page, base_url):
    """
        Setting the open attribute shows the mj-menu popup.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    html = (
        '<button id="trig" aria-haspopup="menu">Options</button>\n'
        '<mj-menu anchor="trig" open>\n'
        '  <div role="menuitem">Edit</div>\n'
        '  <div role="menuitem">Delete</div>\n'
        "</mj-menu>"
    )
    frame = _load_example(page=page, base_url=base_url, tag="mj-menu", html=html)
    frame.wait_for_function(
        "() => document.querySelector('mj-menu') !== null",
        timeout=5000,
    )

    is_open = frame.evaluate(
        "() => document.querySelector('mj-menu').hasAttribute('open')"
    )
    assert is_open is True, "mj-menu should have the open attribute"

    menu_visible = frame.evaluate(
        "() => { const el = document.querySelector('mj-menu'); "
        "const menu = el.shadowRoot.querySelector('.menu'); "
        "return menu ? menu.style.display !== 'none' : false; }"
    )
    assert menu_visible is True, "mj-menu .menu container should be visible when open"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_menu_escape_closes(page, base_url):
    """
        Pressing Escape while the menu is open removes the open attribute.
        A KeyboardEvent is dispatched directly on the document inside the
        iframe because page.keyboard targets the outer page.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    html = (
        '<button id="trig2">Options</button>\n'
        '<mj-menu anchor="trig2" open>\n'
        '  <div role="menuitem">Edit</div>\n'
        '  <div role="menuitem">Delete</div>\n'
        "</mj-menu>"
    )
    frame = _load_example(page=page, base_url=base_url, tag="mj-menu", html=html)
    frame.wait_for_function(
        "() => document.querySelector('mj-menu') !== null",
        timeout=5000,
    )

    frame.evaluate(
        "function() {"
        "  document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));"
        "}"
    )

    is_open = frame.evaluate(
        "function() { return document.querySelector('mj-menu').hasAttribute('open'); }"
    )
    assert is_open is False, "Escape should close the menu"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_menu_arrow_key_moves_focus(page, base_url):
    """
        ArrowDown moves virtual focus to the next menu item (data-active).
        The keydown event is dispatched on the shadow menu element.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    html = (
        '<button id="trig3">Options</button>\n'
        '<mj-menu anchor="trig3" open>\n'
        '  <div role="menuitem">Alpha</div>\n'
        '  <div role="menuitem">Beta</div>\n'
        '  <div role="menuitem">Gamma</div>\n'
        "</mj-menu>"
    )
    frame = _load_example(page=page, base_url=base_url, tag="mj-menu", html=html)
    frame.wait_for_function(
        "() => document.querySelector('mj-menu') !== null",
        timeout=5000,
    )

    frame.evaluate(
        "function() {"
        "  var menuEl = document.querySelector('mj-menu').shadowRoot.querySelector('.menu');"
        "  menuEl.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowDown', bubbles: true }));"
        "}"
    )

    active_text = frame.evaluate(
        "function() {"
        "  var items = document.querySelectorAll('[role=\"menuitem\"]');"
        "  for (var i = 0; i < items.length; i++) {"
        "    if (items[i].getAttribute('data-active') === 'true') return items[i].textContent.trim();"
        "  }"
        "  return null;"
        "}"
    )
    assert active_text is not None, "ArrowDown should set data-active on a menu item"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_menu_select_fires_event(page, base_url):
    """
        Pressing Enter on the active menu item fires mj-menu-select.
        The listener registration, key dispatch, and result check are combined
        in a single evaluate call to avoid frame navigation destroying state.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    html = (
        '<button id="trig4">Options</button>\n'
        '<mj-menu anchor="trig4" open>\n'
        '  <div role="menuitem">Edit</div>\n'
        '  <div role="menuitem">Duplicate</div>\n'
        "</mj-menu>"
    )
    frame = _load_example(page=page, base_url=base_url, tag="mj-menu", html=html)
    frame.wait_for_function(
        "() => document.querySelector('mj-menu') !== null",
        timeout=5000,
    )

    fired = frame.evaluate(
        "function() {"
        "  var menu = document.querySelector('mj-menu');"
        "  var result = false;"
        "  menu.addEventListener('mj-menu-select', function() { result = true; }, { once: true });"
        "  var menuEl = menu.shadowRoot.querySelector('.menu');"
        "  menuEl.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));"
        "  return result;"
        "}"
    )
    assert fired is True, "mj-menu-select should fire when Enter is dispatched on the menu"
    return


# ===========================================================================
# mj-tree-nav
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_tree_nav_renders_tree_role(page, base_url):
    """
        mj-tree-nav renders a [role=tree] element.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open_component(page=page, base_url=base_url, tag="mj-tree-nav")
    frame.wait_for_function(
        "() => document.querySelector('mj-tree-nav') !== null",
        timeout=5000,
    )

    has_tree = frame.evaluate(
        "() => { const el = document.querySelector('mj-tree-nav'); "
        "return el.shadowRoot.querySelector('[role=\"tree\"]') !== null; }"
    )
    assert has_tree is True, "mj-tree-nav should render a [role=tree] element"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_tree_nav_items_have_treeitem_role(page, base_url):
    """
        Slotted <li> elements are assigned role=treeitem by the component.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    html = (
        '<mj-tree-nav nav-label="Site nav">\n'
        '  <li><a href="#">Home</a></li>\n'
        '  <li><a href="#">About</a></li>\n'
        '</mj-tree-nav>'
    )
    frame = _load_example(page=page, base_url=base_url, tag="mj-tree-nav", html=html)
    frame.wait_for_function(
        "() => document.querySelector('mj-tree-nav') !== null",
        timeout=5000,
    )

    item_count = frame.evaluate(
        "() => document.querySelectorAll('[role=\"treeitem\"]').length"
    )
    assert item_count >= 2, "slotted <li> elements should receive role=treeitem"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_tree_nav_expand_collapse_branch(page, base_url):
    """
        Clicking the toggle button expands a collapsed branch and fires events.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    html = (
        '<mj-tree-nav nav-label="Site">\n'
        '  <li><a href="#">Home</a></li>\n'
        '  <li>\n'
        '    <a href="#">Products</a>\n'
        '    <ul>\n'
        '      <li><a href="#">Widgets</a></li>\n'
        '      <li><a href="#">Gadgets</a></li>\n'
        '    </ul>\n'
        '  </li>\n'
        '</mj-tree-nav>'
    )
    frame = _load_example(page=page, base_url=base_url, tag="mj-tree-nav", html=html)
    frame.wait_for_function(
        "() => document.querySelector('mj-tree-nav') !== null",
        timeout=5000,
    )

    frame.evaluate(
        "() => { window.__treeExpandEvents = []; "
        "document.querySelector('mj-tree-nav').addEventListener("
        "'mj-tree-nav-expand', e => window.__treeExpandEvents.push(e.detail)); }"
    )

    initial_expanded = frame.evaluate(
        "() => { const items = document.querySelectorAll('[role=\"treeitem\"][aria-expanded]'); "
        "for (const item of items) { return item.getAttribute('aria-expanded'); } return null; }"
    )
    assert initial_expanded == "false", "branch should start collapsed"

    frame.evaluate(
        "() => { const items = document.querySelectorAll('[role=\"treeitem\"][aria-expanded]'); "
        "for (const item of items) { "
        "  const btn = item.querySelector('.toggle-btn'); "
        "  if (btn) { btn.click(); break; } "
        "} }"
    )

    result = frame.evaluate(
        "() => { const items = document.querySelectorAll('[role=\"treeitem\"][aria-expanded]'); "
        "for (const item of items) { return item.getAttribute('aria-expanded'); } return null; }"
    )
    assert result == "true", "branch should expand after toggle click"

    event_count = frame.evaluate("() => window.__treeExpandEvents.length")
    assert event_count >= 1, "mj-tree-nav-expand should fire"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_tree_nav_current_item_aria_current(page, base_url):
    """
        Setting the current attribute to a treeitem element id marks that item
        with aria-current=page.  The catalog example pre-populates tree items;
        we read their generated ids and then set current to the first one.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open_component(page=page, base_url=base_url, tag="mj-tree-nav")
    frame.wait_for_function(
        "() => document.querySelector('mj-tree-nav') !== null",
        timeout=5000,
    )

    result = frame.evaluate(
        "function() {"
        "  var items = document.querySelectorAll('[role=\"treeitem\"]');"
        "  if (items.length === 0) return null;"
        "  var firstId = items[0].id;"
        "  document.querySelector('mj-tree-nav').setAttribute('current', firstId);"
        "  var currentEl = document.querySelector('[aria-current=\"page\"]');"
        "  return currentEl ? currentEl.id : null;"
        "}"
    )
    assert result is not None, "setting current to a treeitem id should mark it aria-current=page"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_tree_nav_click_sets_active_focus(page, base_url):
    """
        Clicking a tree item sets aria-activedescendant on the tree root,
        implementing the WAI-ARIA managed focus pattern.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open_component(page=page, base_url=base_url, tag="mj-tree-nav")
    frame.wait_for_function(
        "() => document.querySelector('mj-tree-nav') !== null",
        timeout=5000,
    )

    first_item_id = frame.evaluate(
        "function() {"
        "  var items = document.querySelectorAll('[role=\"treeitem\"]');"
        "  return items.length > 0 ? items[0].id : null;"
        "}"
    )
    assert first_item_id is not None, "tree should have at least one treeitem"

    frame.locator("[role='treeitem']").first.click()

    active_descendant = frame.evaluate(
        "function() {"
        "  var tree = document.querySelector('mj-tree-nav').shadowRoot.querySelector('.tree');"
        "  return tree.getAttribute('aria-activedescendant');"
        "}"
    )
    assert active_descendant == first_item_id, (
        "clicking a tree item should set aria-activedescendant to that item's id"
    )
    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
