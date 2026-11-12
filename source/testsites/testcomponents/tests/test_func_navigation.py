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
def test_link_underline_covers_only_the_link_text(page, base_url):
    """
        An inline mj-link in running text renders no whitespace of its own
        inside the anchor (it used to show as underlined spaces around the
        text), and a standalone link without a prefix starts with its text
        (the empty prefix wrapper takes no flex gap).

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    markup = (
        '<p>See the <mj-link id="inline" href="#p">pricing page</mj-link> for details.</p>'
        '<mj-link id="standalone" variant="standalone" href="#s">All plans</mj-link>'
    )
    load_fixture(page, base_url, markup, ["mj-link"])

    result = page.evaluate(
        "function() {"
        "  function measure(id) {"
        "    var link = document.getElementById(id);"
        "    var anchor = link.shadowRoot.querySelector('a').getBoundingClientRect();"
        "    var range = document.createRange();"
        "    range.selectNodeContents(link);"
        "    var text = range.getBoundingClientRect();"
        "    return { anchorStart: Math.round(anchor.left), anchorWidth: Math.round(anchor.width),"
        "             textStart: Math.round(text.left), textWidth: Math.round(text.width) };"
        "  }"
        "  return { inline: measure('inline'), standalone: measure('standalone') };"
        "}"
    )
    inline = result["inline"]
    assert inline["anchorWidth"] == inline["textWidth"], "the inline anchor should be exactly as wide as its text: {}".format(inline)
    assert inline["anchorStart"] == inline["textStart"], "no space should precede the link text: {}".format(inline)
    standalone = result["standalone"]
    assert standalone["anchorStart"] == standalone["textStart"], "an empty prefix should take no room: {}".format(standalone)
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


_INJECTION_PAYLOAD = "x'\"><img src=\"data:,x\" onerror=\"top.__hits=(top.__hits||0)+1\">"


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_link_href_is_sanitised_and_never_parsed_as_markup(page, base_url):
    """
        An href carrying markup stays an attribute value, a javascript: URL is
        neutralised, a link without href has none, and removing `external`
        removes the new-tab target and rel.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    load_fixture(page, base_url, '<div id="host"></div>', ["mj-link"])
    result = page.evaluate(
        "function(payload) {"
        "  var host = document.getElementById('host');"
        "  var make = function(attrs) { var el = document.createElement('mj-link'); Object.keys(attrs).forEach(function(k) { el.setAttribute(k, attrs[k]); }); el.textContent = 'L'; host.appendChild(el); return el; };"
        "  var inner = function(el) { return el.shadowRoot.querySelector('a'); };"
        "  var injected = make({ href: payload });"
        "  var script = make({ href: 'javascript:alert(1)' });"
        "  var bare = make({});"
        "  var ext = make({ href: '/x', external: '' });"
        "  ext.removeAttribute('external');"
        "  return {"
        "    injectedHref: inner(injected).getAttribute('href') === payload,"
        "    images: injected.shadowRoot.querySelectorAll('img').length,"
        "    scriptHref: inner(script).getAttribute('href'),"
        "    bareHref: inner(bare).getAttribute('href'),"
        "    extTarget: inner(ext).getAttribute('target'), extRel: inner(ext).getAttribute('rel'),"
        "    hits: window.__hits === undefined"
        "  };"
        "}",
        _INJECTION_PAYLOAD,
    )
    assert result["injectedHref"] is True, "the href should be applied verbatim as an attribute"
    assert result["images"] == 0, "the href must not be parsed as markup"
    assert result["scriptHref"] == "#", "a javascript: URL must be neutralised"
    assert result["bareHref"] is None, "a link without href should not link to the current page"
    assert result["extTarget"] is None and result["extRel"] is None, "removing external should clear target and rel"
    assert result["hits"] is True, "no injected handler may run"
    return


# ===========================================================================
# mj-app-bar
# ===========================================================================

# The role="banner" elements an element is rendered inside (flat tree: through slots and shadow roots).
# Playwright scopes a chained locator by DOM containment, which does not follow slot assignment.
_BANNERS_AROUND = '''(id) => {
    const banners = [];
    let node = document.getElementById(id);
    while (node !== null && node !== undefined) {
        if (node instanceof Element && node.getAttribute("role") === "banner") {
            banners.push(node.localName + "." + node.className.split(" ")[0]);
        }
        if (node.assignedSlot) { node = node.assignedSlot }
        else if (node.parentNode instanceof ShadowRoot) { node = node.parentNode.host }
        else { node = node.parentNode instanceof Element ? node.parentNode : null }
    }
    return banners;
}'''

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_app_bar_renders_header_landmark(page, base_url):
    """
        mj-app-bar renders a <header role=banner> landmark that holds its
        brand, navigation and actions (it used to render a plain div, so a
        page built on it had no banner).

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    markup = (
        '<mj-app-bar id="bar"><span slot="brand" id="brand">MyApp</span>'
        '<a slot="navigation" href="#home" id="home">Home</a><button slot="actions" type="button" id="sign-in">Sign in</button></mj-app-bar>'
        '<main><p>Content</p></main>'
    )
    load_fixture(page, base_url, markup, ["mj-app-bar"])
    banner = page.get_by_role("banner")
    expect(banner).to_have_count(1)
    expect(banner.get_by_role("navigation")).to_have_count(1)
    around = [page.evaluate(_BANNERS_AROUND, element_id) for element_id in ("brand", "home", "sign-in")]
    assert around == [["header.root"], ["header.root"], ["header.root"]], around

    root = page.evaluate(
        "() => { const root = document.querySelector('#bar').shadowRoot.querySelector('[part=root]'); "
        "return [root.localName, root.getAttribute('role')]; }"
    )
    assert root == ["header", "banner"], root
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_app_bar_page_has_one_banner(page, base_url):
    """
        A page has one banner: of two top-level bars only the first connected
        one is the banner, a bar inside <main> or a <section> is never the
        banner (its header gets role="none"), and when the banner bar is
        removed the next top-level bar takes over.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    markup = (
        '<mj-app-bar id="first"><span slot="brand">First</span></mj-app-bar>'
        '<mj-app-bar id="second"><span slot="brand">Second</span></mj-app-bar>'
        '<main><mj-app-bar id="in-main"><span slot="brand">In main</span></mj-app-bar>'
        '<section aria-label="Demo"><mj-app-bar id="in-section"><span slot="brand">In section</span></mj-app-bar></section></main>'
    )
    load_fixture(page, base_url, markup, ["mj-app-bar"])
    roles = (
        "() => ['first', 'second', 'in-main', 'in-section'].map((id) => { const bar = document.getElementById(id); "
        "return bar === null ? null : bar.shadowRoot.querySelector('[part=root]').getAttribute('role'); })"
    )

    expect(page.get_by_role("banner")).to_have_count(1)
    assert page.evaluate(roles) == ["banner", "none", "none", "none"], page.evaluate(roles)

    page.evaluate("() => document.getElementById('first').remove()")
    page.wait_for_function("() => document.getElementById('second').shadowRoot.querySelector('[part=root]').getAttribute('role') === 'banner'",
                           timeout=5000)
    expect(page.get_by_role("banner")).to_have_count(1)
    assert page.evaluate(roles) == [None, "banner", "none", "none"], page.evaluate(roles)
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_app_bar_in_app_shell_is_the_single_banner(page, base_url):
    """
        Slotted straight into an mj-app-shell's app-bar region the bar is the
        page's banner (the shell adds none); wrapped in a plain element the
        shell's region is the banner and the bar inside it is a plain header,
        so there is never a second, nested banner.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    direct = (
        '<mj-app-shell style="height:300px;"><mj-app-bar slot="app-bar" id="bar"><span slot="brand" id="brand">App</span></mj-app-bar>'
        '<p>Main</p></mj-app-shell>'
    )
    load_fixture(page, base_url, direct, ["mj-app-bar", "mj-app-shell"])
    expect(page.get_by_role("banner")).to_have_count(1)
    page.wait_for_timeout(100)
    assert page.evaluate(_BANNERS_AROUND, "brand") == ["header.root"], page.evaluate(_BANNERS_AROUND, "brand")

    wrapped = (
        '<mj-app-shell style="height:300px;"><div slot="app-bar"><mj-app-bar id="bar"><span slot="brand" id="brand">App</span></mj-app-bar></div>'
        '<p>Main</p></mj-app-shell>'
    )
    load_fixture(page, base_url, wrapped, ["mj-app-bar", "mj-app-shell"])
    page.wait_for_function("() => document.querySelector('#bar').shadowRoot.querySelector('[part=root]').getAttribute('role') === 'none'",
                           timeout=5000)
    expect(page.get_by_role("banner")).to_have_count(1)
    assert page.evaluate(_BANNERS_AROUND, "brand") == ["div.app-bar"], page.evaluate(_BANNERS_AROUND, "brand")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_app_bar_drawer_shows_navigation_links_on_phones(page, base_url):
    """
        At phone width the drawer shows the links slotted into `navigation`
        (it used to open empty); closed, the drawer is not displayed, and open
        it is a modal dialog.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    page.set_viewport_size({"width": 390, "height": 800})
    markup = (
        '<mj-app-bar><span slot="brand">App</span>'
        '<a slot="navigation" href="#home">Home</a><a slot="navigation" href="#docs">Docs</a></mj-app-bar>'
    )
    load_fixture(page, base_url, markup, ["mj-app-bar"])
    home = page.get_by_role("link", name="Home")
    expect(home).to_be_hidden()

    page.locator("mj-app-bar").locator(".toggle").click()
    expect(home).to_be_visible()
    expect(page.get_by_role("dialog")).to_have_count(1)
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_app_bar_toggle_drives_enclosing_app_shell_nav(page, base_url):
    """
        Inside an mj-app-shell with navigation of its own, the app bar's
        toggle opens and closes the shell's nav (not its own drawer) and its
        aria-expanded follows the shell, including changes made by script.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    page.set_viewport_size({"width": 390, "height": 800})
    markup = (
        '<mj-app-shell id="shell" nav-mode="overlay" hide-nav-toggle>'
        '<mj-app-bar slot="app-bar" id="bar"><span slot="brand">App</span>'
        '<a slot="navigation" href="#home">Home</a></mj-app-bar>'
        '<nav slot="nav"><a href="#a">Section A</a></nav><p>Main</p></mj-app-shell>'
    )
    load_fixture(page, base_url, markup, ["mj-app-bar", "mj-app-shell"])
    toggle = page.locator("#bar").locator(".toggle")
    expect(toggle).to_have_attribute("aria-expanded", "false")

    toggle.click()
    expect(toggle).to_have_attribute("aria-expanded", "true")
    state = page.evaluate(
        "() => ({ shell: document.getElementById('shell').navOpen, bar: document.getElementById('bar').open })"
    )
    assert state == {"shell": True, "bar": False}

    page.evaluate("() => { document.getElementById('shell').navOpen = false }")
    expect(toggle).to_have_attribute("aria-expanded", "false")
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_app_bar_in_shell_offers_toggle_and_keeps_its_links_reachable(page, base_url):
    """
        Inside an mj-app-shell that owns the navigation and hides its own
        toggle (hide-nav-toggle) the bar's toggle is shown wherever the
        shell's nav can be toggled, also when the bar has no navigation of its
        own, and the bar's own links stay in the bar (they used to sit in a
        drawer that never opens). A static wide shell offers no toggle until
        its nav-mode makes the nav toggleable, and a shell that shows its own
        toggle gets no second one from the bar.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    page.set_viewport_size({"width": 1280, "height": 800})
    markup = (
        '<mj-app-shell id="shell" nav-mode="overlay" hide-nav-toggle>'
        '<mj-app-bar slot="app-bar" id="bar"><span slot="brand">App</span>'
        '<a slot="navigation" href="#docs">Docs</a><a slot="navigation" href="#help">Help</a></mj-app-bar>'
        '<nav slot="nav"><a href="#a">Section A</a></nav><p>Main</p></mj-app-shell>'
        '<mj-app-shell id="bare-shell" nav-mode="overlay" hide-nav-toggle>'
        '<mj-app-bar slot="app-bar" id="bare-bar"><span slot="brand">Bare</span></mj-app-bar>'
        '<nav slot="nav"><a href="#b">Section B</a></nav><p>Main</p></mj-app-shell>'
        '<mj-app-shell id="static-shell" nav-open hide-nav-toggle>'
        '<mj-app-bar slot="app-bar" id="static-bar"><span slot="brand">Static</span></mj-app-bar>'
        '<nav slot="nav"><a href="#c">Section C</a></nav><p>Main</p></mj-app-shell>'
        '<mj-app-shell id="own-toggle-shell" nav-mode="collapsible" nav-open>'
        '<mj-app-bar slot="app-bar" id="own-toggle-bar"><span slot="brand">Own</span>'
        '<a slot="navigation" href="#own">Own link</a></mj-app-bar>'
        '<nav slot="nav"><a href="#d">Section D</a></nav><p>Main</p></mj-app-shell>'
    )
    load_fixture(page, base_url, markup, ["mj-app-bar", "mj-app-shell"])

    expect(page.get_by_role("link", name="Docs")).to_be_visible()
    expect(page.get_by_role("link", name="Help")).to_be_visible()

    toggle = page.locator("#bar").locator(".toggle")
    expect(toggle).to_be_visible()
    toggle.click()
    expect(toggle).to_have_attribute("aria-expanded", "true")
    assert page.evaluate("() => document.getElementById('shell').navOpen") is True

    bare_toggle = page.locator("#bare-bar").locator(".toggle")
    expect(bare_toggle).to_be_visible()
    bare_toggle.click()
    assert page.evaluate("() => document.getElementById('bare-shell').navOpen") is True

    static_toggle = page.locator("#static-bar").locator(".toggle")
    expect(static_toggle).to_be_hidden()
    page.evaluate("() => document.getElementById('static-shell').setAttribute('nav-mode', 'collapsible')")
    expect(static_toggle).to_be_visible()

    expect(page.locator("#own-toggle-bar").locator(".toggle")).to_be_hidden()
    expect(page.get_by_role("link", name="Own link")).to_be_visible()
    page.evaluate("() => document.getElementById('own-toggle-shell').setAttribute('hide-nav-toggle', '')")
    expect(page.locator("#own-toggle-bar").locator(".toggle")).to_be_visible()
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_side_nav_collapsed_keeps_visible_toggle(page, base_url):
    """
        A collapsed collapsible nav keeps its toggle visible (it used to shrink
        to zero width with the toggle inside), its items leave the tab order,
        and the toggle expands it again.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    markup = (
        '<mj-side-nav mode="collapsible" persist-state="false" style="height:200px">'
        '<a href="#one">One</a><a href="#two">Two</a></mj-side-nav>'
    )
    load_fixture(page, base_url, markup, ["mj-side-nav"])
    toggle = page.locator("mj-side-nav").locator(".toggle-btn")
    expect(toggle).to_be_visible()
    expect(page.get_by_role("link", name="One")).to_be_hidden()

    toggle.click()
    expect(page.get_by_role("link", name="One")).to_be_visible()
    toggle.click()
    expect(toggle).to_be_visible()
    expect(toggle).to_have_attribute("aria-expanded", "false")
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_side_nav_header_keys_are_not_hijacked(page, base_url):
    """
        Home / End typed into a header search field stay in that field; the
        roving keys apply to the nav items only.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    markup = (
        '<mj-side-nav><input slot="header" id="search" value="query">'
        '<a href="#one">One</a><a href="#two">Two</a></mj-side-nav>'
    )
    load_fixture(page, base_url, markup, ["mj-side-nav"])
    page.locator("#search").focus()
    page.keyboard.press("End")
    focused_after_end = page.evaluate("() => document.activeElement.id")

    page.get_by_role("link", name="One").focus()
    page.keyboard.press("ArrowDown")
    focused_after_arrow = page.evaluate("() => document.activeElement.textContent")

    assert focused_after_end == "search", "End in the header field should not move focus"
    assert focused_after_arrow == "Two", "ArrowDown on an item should move to the next item"
    return


# ===========================================================================
# mj-breadcrumb
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_breadcrumb_nav_landmark(page, base_url):
    """
        mj-breadcrumb renders a <nav> landmark with an aria-label.

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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_breadcrumb_keeps_and_displays_slotted_links(page, base_url):
    """
        The catalog example keeps all four author links (they used to be
        deleted by a self-triggered rebuild), shows each one, renders one
        separator between each pair and marks the last crumb as the current
        page without a link.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    frame = _open_component(page=page, base_url=base_url, tag="mj-breadcrumb")
    frame.wait_for_function(
        "() => document.querySelector('mj-breadcrumb') !== null",
        timeout=5000,
    )

    result = frame.evaluate(
        "function() {"
        "  var bc = document.querySelector('mj-breadcrumb');"
        "  var anchors = Array.from(bc.querySelectorAll('a'));"
        "  return {"
        "    count: anchors.length,"
        "    shown: anchors.map(function(a) { return a.getBoundingClientRect().width > 0; }),"
        "    separators: bc.shadowRoot.querySelectorAll('.separator').length,"
        "    current: anchors.map(function(a) { return a.getAttribute('aria-current'); }),"
        "    lastHref: anchors[anchors.length - 1].getAttribute('href')"
        "  };"
        "}"
    )
    assert result["count"] == 4, "all four slotted links should remain"
    assert result["shown"] == [True, True, True, True], "every crumb should be displayed"
    assert result["separators"] == 3, "one separator between each pair of crumbs"
    assert result["current"] == [None, None, None, "page"], "only the last crumb is the current page"
    assert result["lastHref"] is None, "the current crumb should not be a link"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_breadcrumb_expand_reveals_hidden_items_and_moves_focus(page, base_url):
    """
        With max-visible the middle crumbs collapse behind the ellipsis;
        expanding reveals them and focuses the first revealed crumb, and a
        crumb click emits the cancelable mj-breadcrumb-navigate.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    markup = (
        '<mj-breadcrumb max-visible="2">'
        '<a href="/">Home</a><a href="/a">A</a><a href="/b">B</a><a href="/c">C</a>'
        '</mj-breadcrumb>'
    )
    load_fixture(page, base_url, markup, ["mj-breadcrumb"])
    page.get_by_role("button", name="Show 2 hidden breadcrumbs").click()

    result = page.evaluate(
        "function() {"
        "  var bc = document.querySelector('mj-breadcrumb');"
        "  var detail = null;"
        "  bc.addEventListener('mj-breadcrumb-navigate', function(e) { detail = e.detail.href; e.preventDefault(); });"
        "  var focused = document.activeElement.textContent;"
        "  var click = new MouseEvent('click', { bubbles: true, cancelable: true, composed: true });"
        "  bc.querySelector('a[href=\"/b\"]').dispatchEvent(click);"
        "  return {"
        "    focused: focused,"
        "    shown: Array.from(bc.querySelectorAll('a')).map(function(a) { return a.getBoundingClientRect().width > 0; }),"
        "    navigated: detail, prevented: click.defaultPrevented"
        "  };"
        "}"
    )
    assert result["focused"] == "A", "focus should move to the first revealed crumb"
    assert result["shown"] == [True, True, True, True], "all crumbs should show after expanding"
    assert result["navigated"] == "/b", "a crumb click should emit mj-breadcrumb-navigate"
    assert result["prevented"] is True, "canceling the event should stop the navigation"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_breadcrumb_max_visible_sets_the_number_of_visible_crumbs(page, base_url):
    """
        A collapsed trail shows `max-visible` crumbs: the first one and as
        many trailing crumbs as fit, at least `always-show-last` (it used to
        show only first + always-show-last).

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    markup = (
        '<mj-breadcrumb id="deep" max-visible="4" always-show-last="2">'
        '<a href="#1">Home</a><a href="#2">Electronics</a><a href="#3">Computers</a>'
        '<a href="#4">Laptops</a><a href="#5">Ultrabooks</a><a href="#6">Aero 14</a>'
        '</mj-breadcrumb>'
        '<mj-breadcrumb id="no-first" max-visible="2" always-show-first="false">'
        '<a href="#d">Drive</a><a href="#t">Team</a><a href="#g">Design</a><a href="#l">Logos</a>'
        '</mj-breadcrumb>'
        '<mj-breadcrumb id="guaranteed" max-visible="2" always-show-last="2">'
        '<a href="#a">A</a><a href="#b">B</a><a href="#c">C</a><a href="#e">E</a><a href="#f">F</a>'
        '</mj-breadcrumb>'
    )
    load_fixture(page, base_url, markup, ["mj-breadcrumb"])

    shown = page.evaluate(
        "function() {"
        "  var result = {};"
        "  document.querySelectorAll('mj-breadcrumb').forEach(function(trail) {"
        "    result[trail.id] = Array.from(trail.querySelectorAll('a'))"
        "      .filter(function(a) { return a.getBoundingClientRect().width > 0; })"
        "      .map(function(a) { return a.textContent; });"
        "  });"
        "  return result;"
        "}"
    )
    assert shown["deep"] == ["Home", "Laptops", "Ultrabooks", "Aero 14"], shown
    assert shown["no-first"] == ["Design", "Logos"], shown
    assert shown["guaranteed"] == ["A", "E", "F"], "first + always-show-last win over max-visible: {}".format(shown)
    expect(page.locator("#deep").get_by_role("button", name="Show 2 hidden breadcrumbs")).to_be_visible()
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


_TABS_STATE_JS = """
() => {
    const tabs = Array.from(document.querySelectorAll('mj-tabs [slot="tab"]'));
    const panels = Array.from(document.querySelector('mj-tabs').children).filter((c) => c.getAttribute('slot') !== 'tab');
    return {
        selected: tabs.map((t) => t.getAttribute('aria-selected')),
        shown: panels.map((p) => p.hidden === false),
        focused: tabs.indexOf(document.activeElement)
    };
}
"""


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_tabs_click_activates_tab(page, base_url):
    """
        Clicking a tab selects it and shows its panel.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    markup = (
        '<mj-tabs><button slot="tab">One</button><button slot="tab">Two</button>'
        '<div>Panel one</div><div>Panel two</div></mj-tabs>'
    )
    load_fixture(page, base_url, markup, ["mj-tabs"])
    page.get_by_role("tab", name="Two").click()

    state = page.evaluate(_TABS_STATE_JS)
    assert state["selected"] == ["false", "true"], "the clicked tab should be selected"
    assert state["shown"] == [False, True], "the clicked tab's panel should be shown"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_tabs_arrow_moves_focus_and_selection_one_step_skipping_disabled(page, base_url):
    """
        One ArrowRight moves focus and selection together to the next enabled
        tab; a disabled tab is skipped and cannot be selected by `selected`.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    markup = (
        '<mj-tabs><button slot="tab" id="a">A</button><button slot="tab" id="b">B</button>'
        '<button slot="tab" id="c" aria-disabled="true">C</button><button slot="tab" id="d">D</button>'
        '<div>PA</div><div>PB</div><div>PC</div><div>PD</div></mj-tabs>'
    )
    load_fixture(page, base_url, markup, ["mj-tabs"])
    page.locator("#a").focus()
    page.keyboard.press("ArrowRight")
    after_one = page.evaluate(_TABS_STATE_JS)
    page.keyboard.press("ArrowRight")
    after_two = page.evaluate(_TABS_STATE_JS)
    page.evaluate("() => document.querySelector('mj-tabs').setAttribute('selected', 'a')")
    after_attribute = page.evaluate(_TABS_STATE_JS)

    assert after_one["focused"] == 1, "one ArrowRight should focus the second tab"
    assert after_one["selected"] == ["false", "true", "false", "false"], "selection should follow focus"
    assert after_two["focused"] == 3, "the disabled tab should be skipped"
    assert after_two["selected"][3] == "true", "the tab after the disabled one should be selected"
    assert after_attribute["selected"][0] == "true", "setting selected should select that tab"
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_nav_stepper_hides_source_and_tracks_status_changes(page, base_url):
    """
        The slotted step elements are not displayed next to the rendered
        steps, a later status="error" re-renders that step, and a disabled step
        cannot be activated.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    markup = (
        '<mj-nav-stepper current="1" linear="false">'
        '<span>Account</span><span id="profile">Profile</span><span status="disabled">Payment</span>'
        '</mj-nav-stepper>'
    )
    load_fixture(page, base_url, markup, ["mj-nav-stepper"])
    page.evaluate("() => document.getElementById('profile').setAttribute('status', 'error')")

    result = page.evaluate(
        "function() {"
        "  var stepper = document.querySelector('mj-nav-stepper');"
        "  var steps = stepper.shadowRoot.querySelectorAll('li.step');"
        "  var buttons = stepper.shadowRoot.querySelectorAll('.step-btn');"
        "  return {"
        "    sourceShown: Array.from(stepper.children).some(function(c) { return c.getBoundingClientRect().width > 0; }),"
        "    statuses: Array.from(steps).map(function(s) { return s.dataset.status; }),"
        "    disabled: buttons[2].getAttribute('aria-disabled')"
        "  };"
        "}"
    )
    assert result["sourceShown"] is False, "slotted step sources should not be displayed"
    assert result["statuses"] == ["complete", "error", "disabled"], "unexpected statuses {}".format(result["statuses"])
    assert result["disabled"] == "true", "a disabled step should not be navigable"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_nav_stepper_current_past_last_step_fires_complete(page, base_url):
    """
        Moving `current` past the last step makes every step complete and
        emits mj-nav-stepper-complete once per transition (it used to fire
        only for status changes); a stepper that loads complete does not fire.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    markup = (
        '<mj-nav-stepper id="flow" current="1"><span>One</span><span>Two</span><span>Three</span></mj-nav-stepper>'
        '<mj-nav-stepper id="done" current="3"><span>One</span><span>Two</span><span>Three</span></mj-nav-stepper>'
    )
    load_fixture(page, base_url, markup, ["mj-nav-stepper"])

    result = page.evaluate(
        "async function() {"
        "  var wait = function(ms) { return new Promise(function(done) { setTimeout(done, ms); }); };"
        "  var flow = document.getElementById('flow');"
        "  var done = document.getElementById('done');"
        "  var fired = [];"
        "  flow.addEventListener('mj-nav-stepper-complete', function(e) { fired.push(e.detail); });"
        "  done.addEventListener('mj-nav-stepper-complete', function(e) { fired.push('done'); });"
        "  done.setAttribute('current', '4');"
        "  flow.setAttribute('current', '2');"
        "  var atLast = fired.length;"
        "  flow.setAttribute('current', '3');"
        "  flow.setAttribute('current', '5');"
        "  await wait(50);"
        "  return { atLast: atLast, fired: fired, completed: flow.completedCount,"
        "    statuses: Array.from(flow.shadowRoot.querySelectorAll('li.step')).map(function(s) { return s.dataset.status; }) };"
        "}"
    )
    assert result["atLast"] == 0, "the last step being current is not completion"
    assert result["fired"] == [{"completedCount": 3, "total": 3}], "complete should fire once: {}".format(result["fired"])
    assert result["completed"] == 3
    assert result["statuses"] == ["complete", "complete", "complete"]
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_wizard_page_loads_without_errors_or_focus_theft(page, base_url):
    """
        The catalog wizard page loads with no uncaught exception (the `current`
        attribute round trip used to recurse until the stack overflowed) and
        the wizard does not move focus on load.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    frame = _open_component(page=page, base_url=base_url, tag="mj-wizard")
    frame.wait_for_function(
        "() => document.querySelector('mj-wizard') !== null",
        timeout=5000,
    )
    page.wait_for_timeout(300)

    focused = frame.evaluate("() => document.activeElement.tagName")
    assert errors == [], "loading the wizard page raised: {}".format(errors)
    assert focused == "BODY", "the wizard should not take focus on load"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_wizard_validates_required_fields_and_follows_stepper_clicks(page, base_url):
    """
        In linear mode Next is blocked by an empty required input placed
        directly in the step; clicking a completed step in the embedded stepper
        goes back through mj-wizard-before-change with direction "jump".

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    markup = (
        '<mj-wizard label="Sign up">'
        '<section label="Account"><input id="email" required></section>'
        '<section label="Profile"><p>Profile</p></section>'
        '</mj-wizard>'
    )
    load_fixture(page, base_url, markup, ["mj-wizard"])

    result = page.evaluate(
        "function() {"
        "  var wizard = document.querySelector('mj-wizard');"
        "  var directions = [];"
        "  wizard.addEventListener('mj-wizard-before-change', function(e) { directions.push(e.detail.direction); });"
        "  var next = wizard.shadowRoot.querySelector('[data-action=\"next\"]');"
        "  next.click();"
        "  var blocked = wizard.getAttribute('current');"
        "  document.getElementById('email').value = 'a@b.co';"
        "  next.click();"
        "  var advanced = wizard.getAttribute('current');"
        "  var stepper = wizard.shadowRoot.querySelector('mj-nav-stepper');"
        "  stepper.shadowRoot.querySelectorAll('.step-btn')[0].click();"
        "  return { blocked: blocked, advanced: advanced, jumped: wizard.getAttribute('current'),"
        "           stepper: stepper.getAttribute('current'), directions: directions };"
        "}"
    )
    assert result["blocked"] == "0", "an empty required field should block Next"
    assert result["advanced"] == "1", "Next should advance once the step is valid"
    assert result["jumped"] == "0", "a stepper click should move the wizard"
    assert result["stepper"] == "0", "the stepper should follow the wizard"
    assert result["directions"] == ["next", "jump"], "unexpected directions {}".format(result["directions"])
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_wizard_side_stepper_puts_button_bar_under_the_content(page, base_url):
    """
        With stepper-position="side" the stepper is a column at the inline
        start and the button bar sits under the step content in the other
        column (it used to become a third column at the top).

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    markup = (
        '<mj-wizard stepper-position="side" label="Checkout">'
        '<section label="Cart"><p>Two items.</p></section>'
        '<section label="Payment"><p>Card.</p></section>'
        '</mj-wizard>'
    )
    load_fixture(page, base_url, markup, ["mj-wizard"])

    boxes = page.evaluate(
        "function() {"
        "  var root = document.querySelector('mj-wizard').shadowRoot;"
        "  function box(selector) {"
        "    var r = root.querySelector(selector).getBoundingClientRect();"
        "    return { left: Math.round(r.left), right: Math.round(r.right), top: Math.round(r.top), bottom: Math.round(r.bottom) };"
        "  }"
        "  return { stepper: box('.stepper-area'), content: box('.content'), bar: box('.nav-bar') };"
        "}"
    )
    stepper = boxes["stepper"]
    content = boxes["content"]
    bar = boxes["bar"]
    assert content["left"] >= stepper["right"], "the content should sit beside the stepper: {}".format(boxes)
    assert bar["left"] == content["left"] and bar["right"] == content["right"], "the button bar should span the content column: {}".format(boxes)
    assert bar["top"] >= content["bottom"], "the button bar should sit under the content: {}".format(boxes)
    assert stepper["bottom"] == bar["bottom"], "the stepper column should run the full height: {}".format(boxes)
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_pagination_keeps_keyboard_focus_after_page_change(page, base_url):
    """
        Activating Next from the keyboard rebuilds the pager but leaves focus
        on the new Next button, so it can be pressed again; the item range of
        the last page stops at the last item.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    markup = '<mj-pagination id="pager" page="1" total-items="97" page-size="10"></mj-pagination>'
    load_fixture(page, base_url, markup, ["mj-pagination"])
    page.get_by_role("button", name="Next", exact=True).focus()
    page.keyboard.press("Enter")
    page.keyboard.press("Enter")

    result = page.evaluate(
        "function() {"
        "  var pager = document.getElementById('pager');"
        "  var active = pager.shadowRoot.activeElement;"
        "  var focusedPart = active !== null ? active.getAttribute('part') : null;"
        "  pager.setAttribute('page', '10');"
        "  return { page: pager.getAttribute('page'), focused: focusedPart, range: pager.pageRange };"
        "}"
    )
    assert result["focused"] == "next", "focus should stay on the Next button"
    assert result["range"] == [90, 96], "the last page range should end at item 96"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_pagination_href_template_renders_safe_links(page, base_url):
    """
        With href-template the page controls are links; a script URL template
        is neutralised.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    markup = (
        '<mj-pagination id="links" page="2" total-pages="3" href-template="?page={page}"></mj-pagination>'
        '<mj-pagination id="bad" page="1" total-pages="2" href-template="javascript:alert({page})"></mj-pagination>'
    )
    load_fixture(page, base_url, markup, ["mj-pagination"])

    result = page.evaluate(
        "function() {"
        "  var hrefs = function(id) { return Array.from(document.getElementById(id).shadowRoot.querySelectorAll('a.page-btn')).map(function(a) { return a.getAttribute('href'); }); };"
        "  return { links: hrefs('links'), bad: hrefs('bad') };"
        "}"
    )
    assert result["links"] == ["?page=1", "?page=2", "?page=3"], "page links should follow the template"
    assert all(href == "#" for href in result["bad"]), "script URLs must not reach the links"
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


_INJECTION_SCAN_JS = """
(payload) => {
    const quoted = payload.replace(/&/g, '&amp;').replace(/"/g, '&quot;');
    const text = payload.replace(/&/g, '&amp;').replace(/</g, '&lt;');
    const label = (names) => names.map((name) => name + '="' + quoted + '"').join(' ');
    document.body.innerHTML = [
        '<mj-link ' + label(['href', 'target', 'rel', 'download']) + '>' + text + '</mj-link>',
        '<mj-app-bar ' + label(['nav-label']) + '><a slot="navigation" href="#">' + text + '</a></mj-app-bar>',
        '<mj-side-nav ' + label(['nav-label']) + '><a href="#">' + text + '</a></mj-side-nav>',
        '<mj-breadcrumb ' + label(['nav-label', 'separator']) + '><a href="#">' + text + '</a><a href="#">B</a></mj-breadcrumb>',
        '<mj-tabs ' + label(['tablist-label', 'selected']) + '><button slot="tab">' + text + '</button><div>' + text + '</div></mj-tabs>',
        '<mj-nav-stepper ' + label(['label']) + '><span>' + text + '</span></mj-nav-stepper>',
        '<mj-wizard ' + label(['label', 'next-label', 'back-label', 'submit-label']) + '><section ' + label(['label']) + '>S</section></mj-wizard>',
        '<mj-pagination total-pages="3" ' + label(['nav-label', 'href-template']) + '></mj-pagination>',
        '<div id="toc-target"><h2>' + text + '</h2></div><mj-toc target="#toc-target" ' + label(['nav-label', 'heading', 'title']) + '></mj-toc>',
        '<mj-skip-link ' + label(['target', 'label']) + '></mj-skip-link>',
        '<mj-footer-nav ' + label(['nav-label', 'copyright']) + '><nav><strong>' + text + '</strong></nav></mj-footer-nav>',
        '<button id="menu-trigger">' + text + '</button><mj-menu anchor="menu-trigger" ' + label(['label']) + ' open><div role="menuitem">' + text + '</div></mj-menu>',
        '<mj-tree-nav ' + label(['nav-label', 'current']) + '><li><a href="#">' + text + '</a></li></mj-tree-nav>'
    ].join('');
    return new Promise((resolve) => {
        setTimeout(() => {
            let images = 0;
            const visit = (root) => {
                for (const el of root.querySelectorAll('*')) {
                    if (el.shadowRoot) {
                        images = images + el.shadowRoot.querySelectorAll('img').length;
                        visit(el.shadowRoot);
                    }
                }
            };
            visit(document);
            resolve({ hits: window.__hits === undefined ? 0 : window.__hits, shadowImages: images });
        }, 500);
    });
}
"""


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_navigation_components_do_not_parse_attribute_or_text_as_markup(page, base_url):
    """
        Every navigation component keeps attribute values and slotted text
        that contain markup inert: no injected element appears in a shadow
        root and no injected handler runs.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    tags = ["mj-link", "mj-app-bar", "mj-side-nav", "mj-breadcrumb", "mj-tabs", "mj-nav-stepper",
            "mj-wizard", "mj-pagination", "mj-toc", "mj-skip-link", "mj-footer-nav", "mj-menu",
            "mj-tree-nav"]
    load_fixture(page, base_url, "", tags)
    result = page.evaluate(_INJECTION_SCAN_JS, _INJECTION_PAYLOAD)
    assert result["hits"] == 0, "an injected handler ran {} time(s)".format(result["hits"])
    assert result["shadowImages"] == 0, "markup from an attribute or text reached a shadow root"
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_toc_nests_subheadings_and_slugs_non_latin_text(page, base_url):
    """
        Sub-headings are rendered as nested lists, a non-Latin heading gets a
        non-empty id, and a generated id never repeats an id already in the
        document.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    markup = (
        '<p id="intro">Elsewhere</p>'
        '<div id="article"><h2>Введение</h2><h3>Detail</h3><h2>Intro</h2></div>'
        '<mj-toc target="#article"></mj-toc>'
    )
    load_fixture(page, base_url, markup, ["mj-toc"])

    result = page.evaluate(
        "function() {"
        "  var toc = document.querySelector('mj-toc');"
        "  var nested = toc.shadowRoot.querySelectorAll('.list > li > .nested-list > li > a.anchor');"
        "  return { ids: toc.sections.map(function(s) { return s.id; }), nested: nested.length };"
        "}"
    )
    assert result["nested"] == 1, "the h3 should be rendered in a nested list under its h2"
    assert result["ids"][0] == "введение", "a Cyrillic heading should keep its letters in the id"
    assert result["ids"][2] != "intro", "a generated id must not duplicate an existing document id"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_toc_example_scroll_regions_are_keyboard_reachable(page, base_url):
    """
        The catalog examples whose article is its own scroll box make that
        scroller a named tab stop (tabindex="0" and aria-label), so a
        keyboard user can scroll it (axe scrollable-region-focusable).

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    findings = {}
    for key in ("basic", "depth", "manual"):
        page.goto(base_url + "/components/navigation/mj-toc?example=" + key)
        handle = page.wait_for_selector("[data-testid=playground-preview]")
        frame = handle.content_frame()
        frame.wait_for_function(
            """() => {
                const toc = document.querySelector('mj-toc');
                return toc !== null && toc.shadowRoot !== null;
            }""",
            timeout=15000,
        )
        findings[key] = frame.evaluate(
            """() => Array.from(document.querySelectorAll('body *'))
                .filter((node) => {
                    const style = getComputedStyle(node);
                    const scrolls = style.overflowY === 'auto' || style.overflowY === 'scroll';
                    return scrolls === true && node.scrollHeight > node.clientHeight + 1;
                })
                .map((node) => ({ tabIndex: node.tabIndex, label: node.getAttribute('aria-label') || '' }))"""
        )

    for key, scrollers in findings.items():
        assert len(scrollers) >= 1, findings
        for scroller in scrollers:
            assert scroller["tabIndex"] == 0 and len(scroller["label"]) > 0, findings

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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_skip_link_bare_id_target_focuses_target(page, base_url):
    """
        A target written as a bare id gets a fragment href and activation
        focuses that element (not an element whose tag has the same name).

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    markup = (
        '<mj-skip-link target="main" variant="inline"></mj-skip-link>'
        '<main>Wrong</main><div id="main">Right</div>'
    )
    load_fixture(page, base_url, markup, ["mj-skip-link"])

    result = page.evaluate(
        "function() {"
        "  var anchor = document.querySelector('mj-skip-link').shadowRoot.querySelector('a');"
        "  var click = new MouseEvent('click', { bubbles: true, cancelable: true, composed: true });"
        "  anchor.dispatchEvent(click);"
        "  return { href: anchor.getAttribute('href'), focused: document.activeElement.id, prevented: click.defaultPrevented };"
        "}"
    )
    assert result["href"] == "#main", "a bare id target should become a fragment href"
    assert result["focused"] == "main", "activation should focus the element with that id"
    assert result["prevented"] is True, "the component handles the jump itself"
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_footer_nav_navigate_is_cancelable_and_names_group(page, base_url):
    """
        Canceling mj-footer-nav-navigate prevents the link's navigation, and the
        event names the group by its heading.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    markup = (
        '<mj-footer-nav copyright="Corp">'
        '<nav><strong>Product</strong><ul><li><a href="#features" id="features-link">Features</a></li></ul></nav>'
        '</mj-footer-nav>'
    )
    load_fixture(page, base_url, markup, ["mj-footer-nav"])

    result = page.evaluate(
        "function() {"
        "  var footer = document.querySelector('mj-footer-nav');"
        "  var group = null;"
        "  footer.addEventListener('mj-footer-nav-navigate', function(e) { group = e.detail.group; e.preventDefault(); });"
        "  var click = new MouseEvent('click', { bubbles: true, cancelable: true, composed: true });"
        "  document.getElementById('features-link').dispatchEvent(click);"
        "  return { group: group, prevented: click.defaultPrevented };"
        "}"
    )
    assert result["group"] == "Product", "the event should name the group by its heading"
    assert result["prevented"] is True, "canceling the event should prevent the link navigation"
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_menu_item_click_selects_and_closes_once(page, base_url):
    """
        A real pointer click on a slotted menu item emits mj-menu-select and
        closes the menu with a single mj-menu-close whose reason is "select".

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    markup = (
        '<button id="trig">Options</button>'
        '<mj-menu anchor="trig"><div role="menuitem">Edit</div><div role="menuitem">Delete</div></mj-menu>'
    )
    load_fixture(page, base_url, markup, ["mj-menu"])
    page.evaluate(
        "function() {"
        "  window.__menuEvents = [];"
        "  var menu = document.querySelector('mj-menu');"
        "  menu.addEventListener('mj-menu-select', function(e) { window.__menuEvents.push('select:' + e.detail.value); });"
        "  menu.addEventListener('mj-menu-close', function(e) { window.__menuEvents.push('close:' + e.detail.reason); });"
        "  menu.setAttribute('open', '');"
        "}"
    )
    page.get_by_role("menuitem", name="Delete").click()

    result = page.evaluate(
        "() => ({ events: window.__menuEvents, open: document.querySelector('mj-menu').hasAttribute('open') })"
    )
    assert result["events"] == ["select:Delete", "close:select"], (
        "click should select the item and close once: {}".format(result["events"])
    )
    assert result["open"] is False, "the menu should be closed after selection"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_menu_radio_selection_unchecks_siblings(page, base_url):
    """
        Choosing a menuitemradio unchecks the other radios of its group, and
        the open menu gives real focus to its first item.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    markup = (
        '<button id="trig">Size</button>'
        '<mj-menu anchor="trig" close-on-select="false">'
        '<div role="menuitemradio" aria-checked="true" id="small">Small</div>'
        '<div role="menuitemradio" aria-checked="false" id="large">Large</div>'
        '</mj-menu>'
    )
    load_fixture(page, base_url, markup, ["mj-menu"])
    page.evaluate("() => document.querySelector('mj-menu').setAttribute('open', '')")
    focused = page.evaluate("() => document.activeElement.id")
    page.locator("#large").click()

    result = page.evaluate(
        "() => [document.getElementById('small').getAttribute('aria-checked'),"
        " document.getElementById('large').getAttribute('aria-checked')]"
    )
    assert focused == "small", "opening the menu should focus its first item"
    assert result == ["false", "true"], "only the chosen radio should stay checked"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_menu_styles_items_nested_in_groups(page, base_url):
    """
        Items, captions and dividers inside a slotted role="group" wrapper get
        the same styles as direct children (they used to render as plain
        divs), including the check mark of a checked radio item.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    markup = (
        '<button id="trig">Sort</button>'
        '<mj-menu anchor="trig" open>'
        '<div role="menuitem" id="direct">Refresh</div>'
        '<div role="group" aria-label="Sort by">'
        '<div role="presentation" id="caption">Sort by</div>'
        '<div role="menuitemradio" aria-checked="true" id="nested">Name</div>'
        '<hr id="rule">'
        '</div>'
        '</mj-menu>'
    )
    load_fixture(page, base_url, markup, ["mj-menu"])

    styles = page.evaluate(
        "function() {"
        "  function pick(id) {"
        "    var cs = getComputedStyle(document.getElementById(id));"
        "    return { display: cs.display, minHeight: cs.minHeight, paddingInlineStart: cs.paddingInlineStart, fontSize: cs.fontSize };"
        "  }"
        "  return {"
        "    direct: pick('direct'), nested: pick('nested'),"
        "    mark: getComputedStyle(document.getElementById('nested'), '::before').content,"
        "    caption: getComputedStyle(document.getElementById('caption')).textTransform,"
        "    rule: getComputedStyle(document.getElementById('rule')).height"
        "  };"
        "}"
    )
    assert styles["nested"] == styles["direct"], "a nested item should look like a direct one: {}".format(styles)
    assert styles["nested"]["display"] == "flex", styles
    assert styles["mark"] == '"\u2022"', "a checked nested radio shows its mark: {}".format(styles["mark"])
    assert styles["caption"] == "uppercase", "a nested caption is styled as a caption"
    assert styles["rule"] == "1px", "a nested divider is a 1px rule"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_menu_canceled_select_keeps_checked_state(page, base_url):
    """
        mj-menu-select fires before a checkbox / radio item changes and
        reports the state it is about to get; canceling it leaves every
        aria-checked as it was (it used to flip before the event).

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    markup = (
        '<button id="trig">View</button>'
        '<mj-menu anchor="trig" close-on-select="false" open>'
        '<div role="menuitemcheckbox" aria-checked="false" id="wrap">Wrap lines</div>'
        '<div role="menuitemradio" aria-checked="true" id="small">Small</div>'
        '<div role="menuitemradio" aria-checked="false" id="large">Large</div>'
        '</mj-menu>'
    )
    load_fixture(page, base_url, markup, ["mj-menu"])

    result = page.evaluate(
        "function() {"
        "  var menu = document.querySelector('mj-menu');"
        "  var seen = [];"
        "  var cancel = true;"
        "  menu.addEventListener('mj-menu-select', function(e) {"
        "    seen.push([e.detail.item.id, e.detail.checked, e.detail.item.getAttribute('aria-checked')]);"
        "    if (cancel) { e.preventDefault(); }"
        "  });"
        "  function states() { return ['wrap', 'small', 'large'].map(function(id) { return document.getElementById(id).getAttribute('aria-checked'); }); }"
        "  document.getElementById('wrap').click();"
        "  document.getElementById('large').click();"
        "  var canceled = states();"
        "  cancel = false;"
        "  document.getElementById('wrap').click();"
        "  document.getElementById('large').click();"
        "  return { seen: seen, canceled: canceled, applied: states(), open: menu.open };"
        "}"
    )
    assert result["canceled"] == ["false", "true", "false"], "canceling should keep the checked state: {}".format(result)
    assert result["applied"] == ["true", "false", "true"], "an accepted selection applies: {}".format(result)
    assert result["seen"][0] == ["wrap", True, "false"], "the event reports the coming state before the change"
    assert result["seen"][1] == ["large", True, "false"]
    assert result["open"] is True
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_menu_without_items_shows_notice_text(page, base_url):
    """
        An open menu without items shows the empty notice with text (it used
        to be an empty box).

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    markup = '<button id="trig">Recent</button><mj-menu anchor="trig" open></mj-menu>'
    load_fixture(page, base_url, markup, ["mj-menu"])

    notice = page.locator("mj-menu").locator("[part=empty-notice]")
    expect(notice).to_be_visible()
    expect(notice).to_have_text("No options")
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
        Clicking a tree item moves real focus to that item and gives it the
        roving tab stop. (An aria-activedescendant on the shadow tree could not
        reference the light-DOM items, so the component uses roving tabindex.)

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

    # The item's link fills its row, so the click activates it; cancel the
    # navigation so the preview frame stays on the page under test.
    frame.evaluate(
        "() => document.querySelector('mj-tree-nav').addEventListener("
        "'mj-tree-nav-navigate', (e) => e.preventDefault())"
    )
    frame.locator("[role='treeitem']").first.click()

    result = frame.evaluate(
        "function() {"
        "  var items = Array.from(document.querySelectorAll('[role=\"treeitem\"]'));"
        "  var active = document.activeElement;"
        "  return {"
        "    focused: active !== null ? active.id : null,"
        "    stops: items.filter(function(item) { return item.tabIndex === 0; }).map(function(item) { return item.id; })"
        "  };"
        "}"
    )
    assert result["focused"] == first_item_id, "clicking a tree item should focus that item"
    assert result["stops"] == [first_item_id], "the clicked item should hold the only tab stop"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_tree_nav_collapsed_branch_is_hidden_and_keys_move_focus(page, base_url):
    """
        A collapsed branch's children are not displayed (the item styles reach
        the light-DOM items), ArrowDown / ArrowRight move real focus, and
        expanding shows the children.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    markup = (
        '<mj-tree-nav nav-label="Site">'
        '<li><a href="/home">Home</a></li>'
        '<li><a href="/products">Products</a><ul>'
        '<li><a href="/widgets">Widgets</a></li>'
        '</ul></li>'
        '</mj-tree-nav>'
    )
    load_fixture(page, base_url, markup, ["mj-tree-nav"])

    result = page.evaluate(
        "function() {"
        "  var tree = document.querySelector('mj-tree-nav');"
        "  var item = function(href) { return tree.querySelector('a[href=\"' + href + '\"]').closest('li'); };"
        "  var shown = function(href) { return item(href).getBoundingClientRect().height > 0; };"
        "  var key = function(name) { document.activeElement.dispatchEvent(new KeyboardEvent('keydown', { key: name, bubbles: true, composed: true, cancelable: true })); };"
        "  var before = shown('/widgets');"
        "  item('/home').focus();"
        "  key('ArrowDown');"
        "  var afterDown = document.activeElement === item('/products');"
        "  key('ArrowRight');"
        "  var expanded = shown('/widgets');"
        "  key('ArrowRight');"
        "  return { before: before, afterDown: afterDown, expanded: expanded, child: document.activeElement === item('/widgets') };"
        "}"
    )
    assert result["before"] is False, "children of a collapsed branch should not be displayed"
    assert result["afterDown"] is True, "ArrowDown should focus the next item"
    assert result["expanded"] is True, "ArrowRight should expand the branch"
    assert result["child"] is True, "ArrowRight on an open branch should focus its first child"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_tree_nav_current_resolves_within_tree_only(page, base_url):
    """
        `current` naming an id that belongs to an unrelated page element does
        not mark that element; removing `current` clears the mark.

        :param page: Playwright page fixture.
        :param base_url: Site base URL fixture.
    """

    markup = (
        '<section id="settings">Unrelated</section>'
        '<mj-tree-nav current="settings"><li><a href="settings">Settings</a></li></mj-tree-nav>'
    )
    load_fixture(page, base_url, markup, ["mj-tree-nav"])

    result = page.evaluate(
        "function() {"
        "  var tree = document.querySelector('mj-tree-nav');"
        "  var item = tree.querySelector('li');"
        "  var marked = item.getAttribute('aria-current');"
        "  var unrelated = document.getElementById('settings').getAttribute('aria-current');"
        "  tree.removeAttribute('current');"
        "  return { marked: marked, unrelated: unrelated, cleared: item.getAttribute('aria-current') };"
        "}"
    )
    assert result["marked"] == "page", "the tree item whose link matches current should be marked"
    assert result["unrelated"] is None, "an element outside the tree must not be marked"
    assert result["cleared"] is None, "removing current should clear aria-current"
    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
