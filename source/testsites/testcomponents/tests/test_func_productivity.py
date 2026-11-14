"""
    .. module:: testcomponents.tests.test_func_productivity

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

import ccai.testbase as testbase

from testcomponents.harness.browsers import expect
from testcomponents.harness.factories import create_page
from testcomponents.harness.fixtures import load_fixture


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

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


# Markup that tries to run script when it reaches innerHTML unescaped.
_INJECTION = """x'"><img src="data:,x" onerror="top.__hits=(top.__hits||0)+1">"""


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_toolbar_tab_stop_is_the_inner_control_of_mj_button(page, base_url: str) -> None:
    """
        The roving tab stop sits on the inner <button> of an <mj-button>, never
        on the host, and the arrow keys move it between the inner buttons.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-toolbar")
    frame.wait_for_function('''() => {
        const host = document.querySelector("mj-toolbar mj-button");
        return host && host.shadowRoot && host.shadowRoot.querySelector("button") !== null;
    }''', timeout=10000)

    stops = frame.evaluate('''() => {
        const hosts = Array.from(document.querySelectorAll("mj-toolbar mj-button"));
        return {
            hostTabindex: hosts.map(h => h.getAttribute("tabindex")),
            innerTabindex: hosts.map(h => h.shadowRoot.querySelector("button").tabIndex)
        };
    }''')
    assert stops["hostTabindex"] == [None, None, None], "Hosts must not be tab stops: {}".format(stops)
    assert stops["innerTabindex"] == [0, -1, -1], "One inner button should be the tab stop: {}".format(stops)

    frame.evaluate('() => document.querySelector("mj-toolbar mj-button").focus()')
    page.keyboard.press("ArrowRight")
    focused = frame.evaluate('''() => {
        const active = document.activeElement;
        return active && active.shadowRoot && active.shadowRoot.activeElement
            ? active.textContent.trim() + "/" + active.shadowRoot.activeElement.localName : null;
    }''')
    assert focused == "Italic/button", "ArrowRight should focus the next inner button, got {!r}".format(focused)

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_toolbar_overflow_moves_items_into_the_more_menu(page, base_url: str) -> None:
    """
        In a container too narrow for every item, the trailing items move into
        a popup opened by the "More actions" button, where they stay operable.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    markup = (
        '<div style="width:260px"><mj-toolbar id="tb" label="Edit">'
        '<button id="b1">Bold</button><button id="b2">Italic</button>'
        '<button id="b3">Underline</button><button id="b4">Strikethrough</button>'
        '<button id="b5">Clear formatting</button>'
        '</mj-toolbar></div>'
    )
    load_fixture(page, base_url, markup, ["mj-toolbar"])
    page.wait_for_function(
        "() => document.querySelector('#tb').overflowItems.length > 0",
        timeout=5000,
    )

    state = page.evaluate('''() => {
        const tb = document.querySelector("#tb");
        const more = tb.shadowRoot.querySelector("[part=overflow-button]");
        more.click();
        const panel = tb.shadowRoot.querySelector("[part=overflow-menu]");
        const last = document.querySelector("#b5");
        const rect = last.getBoundingClientRect();
        return {
            overflowed: tb.overflowItems.map(i => i.id),
            moreHidden: more.hidden,
            expanded: more.getAttribute("aria-expanded"),
            panelHidden: panel.hidden,
            lastVisible: rect.width > 0 && rect.height > 0
        };
    }''')
    assert "b5" in state["overflowed"], "The last item should overflow: {}".format(state)
    assert state["moreHidden"] is False and state["expanded"] == "true", state
    assert state["panelHidden"] is False and state["lastVisible"] is True, state

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_toolbar_arrow_keys_stay_in_a_text_field(page, base_url: str) -> None:
    """
        ArrowLeft inside a text field moves the caret; the toolbar only takes
        the key once the caret is at the edge.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    markup = (
        '<mj-toolbar id="tb" label="Search tools">'
        '<button id="b1">Go</button><input id="txt" type="text" value="abc">'
        '</mj-toolbar>'
    )
    load_fixture(page, base_url, markup, ["mj-toolbar"])
    page.evaluate("() => { const t = document.querySelector('#txt'); t.focus(); t.setSelectionRange(2, 2); }")
    page.keyboard.press("ArrowLeft")
    state = page.evaluate("() => [document.activeElement.id, document.querySelector('#txt').selectionStart]")
    assert state == ["txt", 1], "The caret should move inside the field, got {}".format(state)

    page.keyboard.press("ArrowLeft")
    page.keyboard.press("ArrowLeft")
    focused = page.evaluate("() => document.activeElement.id")
    assert focused == "b1", "At the start of the field ArrowLeft should leave it, got {!r}".format(focused)

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_toolbar_label_is_not_parsed_as_markup(page, base_url: str) -> None:
    """
        label, labelledby, orientation and overflow-button-label reach the
        shadow DOM as attribute values, never as markup.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    load_fixture(page, base_url, '<mj-toolbar id="tb"><button>One</button></mj-toolbar>', ["mj-toolbar"])
    result = page.evaluate('''(payload) => {
        const tb = document.querySelector("#tb");
        ["label", "labelledby", "orientation", "overflow-button-label", "variant"].forEach(n => tb.setAttribute(n, payload));
        tb.setAttribute("labelledby", "");
        return new Promise(resolve => setTimeout(() => resolve({
            hits: window.__hits === undefined ? 0 : window.__hits,
            images: tb.shadowRoot.querySelectorAll("img").length,
            label: tb.shadowRoot.querySelector("[role=toolbar]").getAttribute("aria-label") === payload
        }), 200));
    }''', _INJECTION)
    assert result == {"hits": 0, "images": 0, "label": True}, result

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_toolbar_shift_arrow_stays_in_a_text_field(page, base_url: str) -> None:
    """
        Shift+ArrowLeft with the caret at the start of a text field is the
        field's (selection) key: focus stays in the field; a plain ArrowLeft
        there still moves to the previous item.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    markup = ('<mj-toolbar label="Format"><button id="before" type="button">Bold</button>'
              '<input id="field" type="text" value="hello"></mj-toolbar>')
    load_fixture(page, base_url, markup, ["mj-toolbar"])
    page.locator("#field").focus()
    page.evaluate("() => document.querySelector('#field').setSelectionRange(0, 0)")

    page.keyboard.press("Shift+ArrowLeft")
    after_shift = page.evaluate("() => document.activeElement.id")
    page.keyboard.press("ArrowLeft")
    after_plain = page.evaluate("() => document.activeElement.id")
    assert [after_shift, after_plain] == ["field", "before"], [after_shift, after_plain]

    return


# ---------------------------------------------------------------------------
# mj-menubar
# ---------------------------------------------------------------------------

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_menubar_definition_markup_is_not_displayed(page, base_url: str) -> None:
    """
        The slotted menu definition is data: none of it is rendered as text in
        the bar, only the generated File / Edit items are.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-menubar")
    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-menubar");
        return el && el.shadowRoot && el.shadowRoot.querySelectorAll("[data-mj-menubar-btn]").length === 2;
    }''', timeout=10000)

    rendered = frame.evaluate('''() => {
        const el = document.querySelector("mj-menubar");
        return Array.from(el.querySelectorAll("*")).filter(n => n.getClientRects().length > 0).length;
    }''')
    assert rendered == 0, "{} definition elements are rendered in the bar".format(rendered)

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_menubar_arrow_keys_move_inside_an_open_menu(page, base_url: str) -> None:
    """
        ArrowDown opens the menu on its first item and moves on to the middle
        item; End and Home reach the last and first items.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-menubar")
    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-menubar");
        return el && el.shadowRoot && el.shadowRoot.querySelector("[data-mj-menubar-btn]") !== null;
    }''', timeout=10000)
    frame.evaluate('() => document.querySelector("mj-menubar").shadowRoot.querySelector("[data-mj-menubar-btn]").focus()')

    focused_item = '''() => {
        const active = document.querySelector("mj-menubar").shadowRoot.activeElement;
        return active ? active.textContent.trim() : null;
    }'''
    visited = []
    for key in ["ArrowDown", "ArrowDown", "End", "Home"]:
        page.keyboard.press(key)
        visited.append(frame.evaluate(focused_item))
    assert visited == ["New", "Open", "Save", "New"], "Unexpected focus path: {}".format(visited)

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_menubar_arrow_right_switches_the_open_menu(page, base_url: str) -> None:
    """
        With File open, ArrowRight closes it and opens Edit, so only one
        dropdown is ever visible.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-menubar")
    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-menubar");
        return el && el.shadowRoot && el.shadowRoot.querySelector("[data-mj-menubar-btn]") !== null;
    }''', timeout=10000)
    frame.evaluate('() => document.querySelector("mj-menubar").shadowRoot.querySelector("[data-mj-menubar-btn]").focus()')
    page.keyboard.press("ArrowDown")
    page.keyboard.press("ArrowRight")

    state = frame.evaluate('''() => {
        const root = document.querySelector("mj-menubar").shadowRoot;
        return {
            open: Array.from(root.querySelectorAll("[role=menu]")).filter(m => !m.hidden).map(m => m.getAttribute("aria-label")),
            focused: root.activeElement ? root.activeElement.textContent.trim() : null
        };
    }''')
    assert state == {"open": ["Edit"], "focused": "Cut"}, state

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_menubar_labels_are_not_parsed_as_markup(page, base_url: str) -> None:
    """
        The menubar label and the labels and values of the definition never
        become markup in the shadow DOM.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    load_fixture(page, base_url, '<mj-menubar id="mb"><div label="File"><span data-menu-item>New</span></div></mj-menubar>', ["mj-menubar"])
    result = page.evaluate('''(payload) => {
        const mb = document.querySelector("#mb");
        mb.setAttribute("label", payload);
        const menu = document.createElement("div");
        menu.setAttribute("label", payload);
        const item = document.createElement("span");
        item.setAttribute("data-menu-item", "");
        item.setAttribute("value", payload);
        item.textContent = payload;
        menu.appendChild(item);
        mb.appendChild(menu);
        return new Promise(resolve => setTimeout(() => {
            const buttons = mb.shadowRoot.querySelectorAll("[data-mj-menubar-btn]");
            buttons[buttons.length - 1].click();
            resolve({
                hits: window.__hits === undefined ? 0 : window.__hits,
                images: mb.shadowRoot.querySelectorAll("img").length,
                label: mb.shadowRoot.querySelector("[role=menubar]").getAttribute("aria-label") === payload
            });
        }, 200));
    }''', _INJECTION)
    assert result == {"hits": 0, "images": 0, "label": True}, result

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_menubar_li_separators_and_own_text_labels(page, base_url: str) -> None:
    """
        An <li role="separator"> and an <li data-menu-separator> become
        separators (not empty entries), and a menu without a label is named by
        its own text, not by the text of its entries.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    markup = (
        '<mj-menubar id="mb">'
        '<div>File <ul><li value="new">New</li><li role="separator"></li>'
        '<li data-menu-separator></li><li value="open">Open</li></ul></div>'
        '<div label="Edit"><span data-menu-item>Undo</span></div>'
        '</mj-menubar>'
    )
    load_fixture(page, base_url, markup, ["mj-menubar"])
    result = page.evaluate('''() => {
        const root = document.querySelector("#mb").shadowRoot;
        return {
            labels: Array.from(root.querySelectorAll(".menu-item-btn")).map(b => b.textContent),
            rows: Array.from(root.querySelector(".menu-dropdown").children).map(
                li => li.getAttribute("role") + ":" + li.textContent.trim())
        };
    }''')
    assert result["labels"] == ["File", "Edit"], result
    assert result["rows"] == ["none:New", "separator:", "separator:", "none:Open"], result

    return


# ---------------------------------------------------------------------------
# mj-status-bar
# ---------------------------------------------------------------------------

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_status_bar_root_is_not_a_live_region(page, base_url: str) -> None:
    """
        Only the hidden announcement region is live: the bar itself is a
        labelled group, so item text changes are not read out.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-status-bar")
    frame.wait_for_function('''() => {
        const el = document.querySelector("mj-status-bar");
        return el && el.shadowRoot && el.shadowRoot.querySelector("[part=root]") !== null;
    }''', timeout=10000)

    state = frame.evaluate('''() => {
        const root = document.querySelector("mj-status-bar").shadowRoot;
        const bar = root.querySelector("[part=root]");
        return {
            role: bar.getAttribute("role"),
            label: bar.getAttribute("aria-label"),
            liveRegions: root.querySelectorAll("[aria-live], [role=status]").length
        };
    }''')
    assert state == {"role": "group", "label": "Application status", "liveRegions": 1}, state

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_status_bar_items_are_the_slotted_elements(page, base_url: str) -> None:
    """
        ``items`` lists the author's start, centre and end items in order.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _load_example(page, base_url, "mj-status-bar")
    frame.wait_for_function('() => customElements.get("mj-status-bar") !== undefined', timeout=10000)
    items = frame.evaluate('() => document.querySelector("mj-status-bar").items.map(i => i.textContent.trim())')
    assert items == ["Ln 12, Col 8", "Ready", "Saved"], items

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_status_bar_interactive_item_works_from_the_keyboard(page, base_url: str) -> None:
    """
        A non-button item marked ``interactive`` becomes role="button" with a
        tab stop, and Enter fires mj-status-item-click.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    markup = '<mj-status-bar id="sb"><span slot="end" id="branch" interactive value="main">main</span></mj-status-bar>'
    load_fixture(page, base_url, markup, ["mj-status-bar"])
    page.evaluate('''() => {
        window.__clicks = [];
        document.querySelector("#sb").addEventListener("mj-status-item-click", e => window.__clicks.push(e.detail));
    }''')
    state = page.evaluate('() => { const i = document.querySelector("#branch"); return [i.getAttribute("role"), i.tabIndex]; }')
    assert state == ["button", 0], state

    page.keyboard.press("Tab")
    page.keyboard.press("Enter")
    clicks = page.evaluate("() => window.__clicks")
    assert clicks == [{"itemId": "branch", "value": "main"}], clicks

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_status_bar_interactive_item_added_inside_a_slotted_item(page, base_url: str) -> None:
    """
        An [interactive] element added later inside an item that is already
        slotted is made a button with a tab stop.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    load_fixture(page, base_url, '<mj-status-bar id="sb"><div id="group"><span>Ready</span></div></mj-status-bar>',
                 ["mj-status-bar"])
    result = page.evaluate('''() => new Promise((resolve) => {
        const item = document.createElement("span");
        item.setAttribute("interactive", "");
        item.textContent = "Ln 4, Col 2";
        document.querySelector("#group").appendChild(item);
        setTimeout(() => resolve([item.getAttribute("role"), item.getAttribute("tabindex")]), 50);
    })''')
    assert result == ["button", "0"], result

    return


# ---------------------------------------------------------------------------
# mj-app-shell
# ---------------------------------------------------------------------------

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_app_shell_landmark_structure(page, base_url: str) -> None:
    """
        The app shell's regions are exposed as one banner, one navigation
        landmark and one main landmark when the slotted content brings its own
        <nav> and <main> (the catalog example does), without nesting.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    markup = (
        '<mj-app-shell nav-open style="height:300px;">'
        '<div slot="app-bar">App Bar</div>'
        '<nav slot="nav" aria-label="Sections">Navigation</nav>'
        '<main slot="main">Main content area</main>'
        '<div slot="status-bar">Ready</div>'
        '</mj-app-shell>'
    )
    load_fixture(page, base_url, markup, ["mj-app-shell"])
    expect(page.get_by_role("banner")).to_have_count(1)
    expect(page.get_by_role("navigation")).to_have_count(1)
    expect(page.get_by_role("main")).to_have_count(1)
    expect(page.get_by_role("contentinfo")).to_have_count(1)

    return


# Shell markup whose regions hold plain (non-landmark) content.
_PLAIN_SHELL_MARKUP = (
    '<mj-app-shell id="shell" nav-open style="height:600px;">'
    '<div slot="app-bar"><button id="menu" type="button">Menu</button></div>'
    '<div slot="nav"><a id="first-link" href="#one">One</a><a href="#two">Two</a></div>'
    '<div slot="main"><h1>Main</h1><a id="content-link" href="#content">Content</a></div>'
    '</mj-app-shell>'
)


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_app_shell_wraps_plain_content_in_one_main(page, base_url: str) -> None:
    """
        Plain slotted content gets exactly one main landmark from the shell.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    load_fixture(page, base_url, _PLAIN_SHELL_MARKUP, ["mj-app-shell"])
    expect(page.get_by_role("main")).to_have_count(1)

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_app_shell_slotted_main_is_not_nested(page, base_url: str) -> None:
    """
        When the slotted main content is itself a <main>, the shell does not
        wrap it in a second main landmark.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    markup = '<mj-app-shell style="height:300px;"><main slot="main">Content</main></mj-app-shell>'
    load_fixture(page, base_url, markup, ["mj-app-shell"])
    expect(page.get_by_role("main")).to_have_count(1)

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_app_shell_empty_regions_expose_no_landmarks(page, base_url: str) -> None:
    """
        With nothing slotted into the inspector or status bar, the shell
        exposes no complementary or contentinfo landmark.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    load_fixture(page, base_url, _PLAIN_SHELL_MARKUP, ["mj-app-shell"])
    expect(page.get_by_role("complementary")).to_have_count(0)
    expect(page.get_by_role("contentinfo")).to_have_count(0)

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_app_shell_empty_dock_takes_no_space(page, base_url: str) -> None:
    """
        An empty dock rail is not rendered, so it takes no width beside the nav.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    load_fixture(page, base_url, _PLAIN_SHELL_MARKUP, ["mj-app-shell"])
    dock_width = page.evaluate(
        "() => document.querySelector('#shell').shadowRoot.querySelector('.dock').getBoundingClientRect().width"
    )
    assert dock_width == 0, "An empty dock should take no width, got {}".format(dock_width)

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_app_shell_narrow_viewport_starts_with_drawer_closed(page, base_url: str) -> None:
    """
        Below the nav breakpoint the shell becomes an overlay drawer and closes
        it, even when the markup asks for nav-open (the wide-layout state).

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    page.set_viewport_size({"width": 390, "height": 800})
    load_fixture(page, base_url, _PLAIN_SHELL_MARKUP, ["mj-app-shell"])
    page.wait_for_function(
        "() => document.querySelector('#shell').hasAttribute('narrow')",
        timeout=5000,
    )
    is_open = page.evaluate("() => document.querySelector('#shell').hasAttribute('nav-open')")
    assert is_open is False, "The overlay drawer should start closed"

    # The narrow layout is internal state: the author's nav-mode is left alone.
    nav_mode = page.evaluate("() => document.querySelector('#shell').getAttribute('nav-mode')")
    assert nav_mode is None, "nav-mode should not be rewritten, got {!r}".format(nav_mode)

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_app_shell_breakpoint_custom_property_moves_the_overlay_threshold(page, base_url: str) -> None:
    """
        --mj-shell-breakpoint-nav raises the overlay threshold: at 900px wide,
        a 1000px breakpoint puts the nav in overlay mode.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    page.set_viewport_size({"width": 900, "height": 800})
    markup = _PLAIN_SHELL_MARKUP.replace(
        'style="height:600px;"', 'style="height:600px; --mj-shell-breakpoint-nav: 1000px;"'
    )
    load_fixture(page, base_url, markup, ["mj-app-shell"])
    page.wait_for_function(
        "() => document.querySelector('#shell').hasAttribute('narrow')",
        timeout=5000,
    )

    return


def _open_overlay_drawer(page, base_url: str) -> None:
    """
        Load the plain shell at phone width and open its overlay drawer from
        the app-bar button, as a user would.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    page.set_viewport_size({"width": 390, "height": 800})
    load_fixture(page, base_url, _PLAIN_SHELL_MARKUP, ["mj-app-shell"])
    page.wait_for_function(
        "() => document.querySelector('#shell').hasAttribute('narrow')",
        timeout=5000,
    )
    page.evaluate(
        "() => document.querySelector('#menu').addEventListener('click', () => document.querySelector('#shell').toggleNav())"
    )
    page.locator("#menu").click()
    page.wait_for_function("() => document.querySelector('#shell').hasAttribute('nav-open')", timeout=5000)
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_app_shell_overlay_moves_focus_into_the_drawer(page, base_url: str) -> None:
    """
        Opening the overlay drawer moves focus to its first link.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    _open_overlay_drawer(page, base_url)
    focused = page.evaluate("() => document.activeElement.id")
    assert focused == "first-link", "Focus should move into the drawer, it is on {!r}".format(focused)

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_app_shell_overlay_keeps_tab_inside_the_drawer(page, base_url: str) -> None:
    """
        While the overlay drawer is open, Tab cycles through the drawer's links
        and never reaches the app bar or the main content.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    _open_overlay_drawer(page, base_url)
    visited = []
    for _ in range(5):
        page.keyboard.press("Tab")
        visited.append(page.evaluate("() => document.activeElement.textContent.trim()"))
    outside = [label for label in visited if label not in ("One", "Two")]
    assert outside == [], "Tab left the drawer: {}".format(visited)

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_app_shell_escape_closes_overlay_when_focus_is_elsewhere(page, base_url: str) -> None:
    """
        Escape closes the overlay drawer even when nothing inside it has
        focus.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    _open_overlay_drawer(page, base_url)
    page.evaluate("() => document.activeElement.blur()")
    page.keyboard.press("Escape")
    is_open = page.evaluate("() => document.querySelector('#shell').hasAttribute('nav-open')")
    assert is_open is False, "Escape should close the overlay drawer"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_app_shell_closing_overlay_returns_focus_to_the_opener(page, base_url: str) -> None:
    """
        Closing the overlay drawer with Escape returns focus to the control
        that opened it.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    _open_overlay_drawer(page, base_url)
    page.keyboard.press("Escape")
    focused = page.evaluate("() => document.activeElement.id")
    assert focused == "menu", "Focus should return to the opener, it is on {!r}".format(focused)

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


def _shell_active_region(page) -> str:
    """
        The id of the element focused inside the #shell shadow root, or "".

        :param page: The Playwright page.

        :returns: The id, or the empty string when focus is not in the shadow root.
    """

    focused = page.evaluate('''() => {
        const active = document.querySelector("#shell").shadowRoot.activeElement;
        return active ? active.id : "";
    }''')
    return focused


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_app_shell_f6_moves_focus_between_regions(page, base_url: str) -> None:
    """
        F6 moves focus from the region that holds it to the next region, and
        Shift+F6 back.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    page.set_viewport_size({"width": 1280, "height": 800})
    load_fixture(page, base_url, _PLAIN_SHELL_MARKUP, ["mj-app-shell"])
    page.locator("#menu").focus()

    page.keyboard.press("F6")
    first = _shell_active_region(page)
    page.keyboard.press("F6")
    second = _shell_active_region(page)
    page.keyboard.press("Shift+F6")
    back = _shell_active_region(page)
    assert [first, second, back] == ["mj-shell-nav", "mj-shell-main", "mj-shell-nav"], [first, second, back]

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_app_shell_nav_separator_resizes_and_persists(page, base_url: str) -> None:
    """
        The nav separator is a keyboard-operable role="separator": ArrowRight
        widens the nav by one step, the size is stored in localStorage and a
        newly loaded shell starts at that size.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    page.set_viewport_size({"width": 1280, "height": 800})
    load_fixture(page, base_url, _PLAIN_SHELL_MARKUP, ["mj-app-shell"])
    page.evaluate("() => localStorage.removeItem('mj-app-shell-nav-size')")

    nav_width = "() => Math.round(document.querySelector('#shell').shadowRoot.querySelector('[part=nav]').getBoundingClientRect().width)"
    before = page.evaluate(nav_width)
    handle = page.evaluate('''() => {
        const handle = document.querySelector("#shell").shadowRoot.querySelector(".nav-handle");
        handle.focus();
        return [handle.getAttribute("role"), handle.hidden, handle.getAttribute("aria-valuenow")];
    }''')
    assert handle == ["separator", False, str(before)], handle

    page.keyboard.press("ArrowRight")
    page.wait_for_timeout(400)
    after = page.evaluate(nav_width)
    stored = page.evaluate("() => localStorage.getItem('mj-app-shell-nav-size')")
    assert after == before + 16, "ArrowRight should widen the nav by 16px: {} -> {}".format(before, after)
    assert stored == str(after), "The new size should be persisted, got {!r}".format(stored)

    load_fixture(page, base_url, _PLAIN_SHELL_MARKUP, ["mj-app-shell"])
    page.wait_for_timeout(300)
    restored = page.evaluate(nav_width)
    assert restored == after, "The persisted size should be restored: {} != {}".format(restored, after)

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_app_shell_builtin_nav_toggle_opens_the_drawer_when_narrow(page, base_url: str) -> None:
    """
        Below the breakpoint the shell offers its own nav toggle; it opens the
        drawer, reports aria-expanded and points at the nav with aria-controls.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    page.set_viewport_size({"width": 390, "height": 800})
    load_fixture(page, base_url, _PLAIN_SHELL_MARKUP, ["mj-app-shell"])
    page.wait_for_function("() => document.querySelector('#shell').hasAttribute('narrow')", timeout=5000)

    toggle = page.locator("#shell [part=nav-toggle-button]")
    expect(toggle).to_be_visible()
    expect(toggle).to_have_attribute("aria-controls", "mj-shell-nav")
    expect(toggle).to_have_attribute("aria-expanded", "false")

    toggle.click()
    page.wait_for_function("() => document.querySelector('#shell').hasAttribute('nav-open')", timeout=5000)
    expect(toggle).to_have_attribute("aria-expanded", "true")
    focused = page.evaluate("() => document.activeElement.id")
    assert focused == "first-link", "Focus should move into the drawer, it is on {!r}".format(focused)

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_app_shell_skip_link_focuses_the_main_region(page, base_url: str) -> None:
    """
        The first Tab stop is the built-in skip link; activating it moves
        focus to the main region.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    page.set_viewport_size({"width": 1280, "height": 800})
    load_fixture(page, base_url, _PLAIN_SHELL_MARKUP, ["mj-app-shell"])
    page.keyboard.press("Tab")
    link = page.evaluate('''() => {
        const active = document.querySelector("#shell").shadowRoot.activeElement;
        return active ? active.getAttribute("part") : null;
    }''')
    assert link == "skip-link", "The first tab stop should be the skip link, got {!r}".format(link)

    page.keyboard.press("Enter")
    assert _shell_active_region(page) == "mj-shell-main"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_app_shell_closed_nav_is_out_of_the_tab_order(page, base_url: str) -> None:
    """
        Once the nav is closed in the wide layout, Tab never reaches its links.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    page.set_viewport_size({"width": 1280, "height": 800})
    load_fixture(page, base_url, _PLAIN_SHELL_MARKUP, ["mj-app-shell"])
    page.evaluate("() => { document.querySelector('#shell').navOpen = false; }")
    page.wait_for_timeout(500)

    visited = []
    for _ in range(6):
        page.keyboard.press("Tab")
        visited.append(page.evaluate("() => document.activeElement.id"))
    assert "first-link" not in visited, "Tab reached a link of the closed nav: {}".format(visited)

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_app_shell_inspector_is_a_drawer_when_narrow(page, base_url: str) -> None:
    """
        Below the breakpoint the inspector starts closed and opens as a drawer
        over the content instead of squeezing the main region.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    page.set_viewport_size({"width": 390, "height": 800})
    markup = _PLAIN_SHELL_MARKUP.replace(
        'nav-open', 'nav-open inspector-open'
    ).replace(
        '</mj-app-shell>', '<div slot="inspector"><button id="apply" type="button">Apply</button></div></mj-app-shell>'
    )
    load_fixture(page, base_url, markup, ["mj-app-shell"])
    page.wait_for_function("() => document.querySelector('#shell').hasAttribute('narrow')", timeout=5000)
    assert page.evaluate("() => document.querySelector('#shell').inspectorOpen") is False

    page.evaluate("() => { document.querySelector('#shell').inspectorOpen = true; }")
    page.wait_for_timeout(400)
    widths = page.evaluate('''() => {
        const root = document.querySelector("#shell").shadowRoot;
        const width = (part) => Math.round(root.querySelector("[part=" + part + "]").getBoundingClientRect().width);
        return {
            shell: Math.round(document.querySelector("#shell").getBoundingClientRect().width),
            main: width("main"), inspector: width("inspector"), focused: document.activeElement.id
        };
    }''')
    assert widths["main"] == widths["shell"], "The main region should keep the full width: {}".format(widths)
    assert widths["inspector"] <= widths["shell"] * 0.85 + 1, "The inspector should fit the viewport: {}".format(widths)
    assert widths["focused"] == "apply", "Focus should move into the inspector drawer: {}".format(widths)

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_app_shell_labels_are_not_parsed_as_markup(page, base_url: str) -> None:
    """
        The label, size and storage attributes never become markup.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    load_fixture(page, base_url, _PLAIN_SHELL_MARKUP, ["mj-app-shell"])
    result = page.evaluate('''(payload) => {
        const shell = document.querySelector("#shell");
        ["nav-label", "inspector-label", "status-bar-label", "storage-key", "nav-size",
         "inspector-size", "split-ratio", "nav-mode"].forEach(n => shell.setAttribute(n, payload));
        return new Promise(resolve => setTimeout(() => resolve({
            hits: window.__hits === undefined ? 0 : window.__hits,
            images: shell.shadowRoot.querySelectorAll("img").length
        }), 200));
    }''', _INJECTION)
    assert result == {"hits": 0, "images": 0}, result

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_app_shell_stored_size_wins_over_the_size_attribute(page, base_url: str) -> None:
    """
        A size stored by an earlier resize is restored even though nav-size is
        in the markup; changing nav-size afterwards applies it.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    page.set_viewport_size({"width": 1280, "height": 800})
    markup = _PLAIN_SHELL_MARKUP.replace('nav-open', 'nav-open nav-size="200" storage-key="fp049"')
    load_fixture(page, base_url, "<div></div>", ["mj-app-shell"])
    page.evaluate("() => localStorage.setItem('fp049-nav-size', '300')")
    load_fixture(page, base_url, markup, ["mj-app-shell"])

    nav_width = "() => Math.round(document.querySelector('#shell').shadowRoot.querySelector('[part=nav]').getBoundingClientRect().width)"
    page.wait_for_timeout(400)
    restored = page.evaluate(nav_width)
    page.evaluate("() => document.querySelector('#shell').setAttribute('nav-size', '220')")
    page.wait_for_timeout(400)
    changed = page.evaluate(nav_width)
    page.evaluate("() => localStorage.removeItem('fp049-nav-size')")
    assert [restored, changed] == [300, 220], [restored, changed]

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_app_shell_storage_key_change_switches_the_sizes(page, base_url: str) -> None:
    """
        Changing storage-key after render takes the sizes stored under the new
        prefix, and the next resize is stored there.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    page.set_viewport_size({"width": 1280, "height": 800})
    load_fixture(page, base_url, _PLAIN_SHELL_MARKUP.replace('nav-open', 'nav-open storage-key="fp050a"'),
                 ["mj-app-shell"])
    result = page.evaluate('''() => new Promise((resolve) => {
        localStorage.removeItem("fp050a-nav-size");
        localStorage.setItem("fp050b-nav-size", "280");
        const shell = document.querySelector("#shell");
        const nav = shell.shadowRoot.querySelector("[part=nav]");
        shell.setAttribute("storage-key", "fp050b");
        setTimeout(() => {
            const switched = Math.round(nav.getBoundingClientRect().width);
            const handle = shell.shadowRoot.querySelector(".nav-handle");
            handle.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowRight", bubbles: true }));
            setTimeout(() => {
                const stored = [localStorage.getItem("fp050a-nav-size"), localStorage.getItem("fp050b-nav-size")];
                localStorage.removeItem("fp050b-nav-size");
                resolve({ switched, stored });
            }, 400);
        }, 400);
    })''')
    assert result == {"switched": 280, "stored": [None, "296"]}, result

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_app_shell_slotted_skip_link_focuses_the_main_region(page, base_url: str) -> None:
    """
        A link slotted into skip-link is wired by the shell: Enter on it moves
        focus to the main region, with no script of the page's own. The
        built-in link carries no fragment that cannot resolve.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    page.set_viewport_size({"width": 1280, "height": 800})
    builtin = _PLAIN_SHELL_MARKUP.replace('id="shell"', 'id="other"')
    load_fixture(page, base_url, builtin, ["mj-app-shell"])
    link = page.evaluate('''() => {
        const link = document.querySelector("#other").shadowRoot.querySelector("[part=skip-link]");
        return [link.getAttribute("href"), link.getAttribute("role"), link.tabIndex];
    }''')
    assert link == [None, "link", 0], link

    markup = _PLAIN_SHELL_MARKUP.replace(
        '<div slot="app-bar">', '<a slot="skip-link" id="skip" href="#article">Skip to the article</a><div slot="app-bar">'
    ).replace('<div slot="main">', '<div slot="main" id="article">')
    load_fixture(page, base_url, markup, ["mj-app-shell"])
    page.keyboard.press("Tab")
    assert page.evaluate("() => document.activeElement.id") == "skip"
    page.keyboard.press("Enter")
    assert _shell_active_region(page) == "mj-shell-main"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_app_shell_f6_from_a_separator_moves_to_the_neighbour(page, base_url: str) -> None:
    """
        F6 from the nav separator moves to the main region (the region after
        it) and Shift+F6 to the nav (the region before it), not to the first
        or last region.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    page.set_viewport_size({"width": 1280, "height": 800})
    load_fixture(page, base_url, _PLAIN_SHELL_MARKUP, ["mj-app-shell"])
    focus_handle = "() => document.querySelector('#shell').shadowRoot.querySelector('.nav-handle').focus()"

    page.evaluate(focus_handle)
    page.keyboard.press("F6")
    forward = _shell_active_region(page)
    page.evaluate(focus_handle)
    page.keyboard.press("Shift+F6")
    backward = _shell_active_region(page)
    assert [forward, backward] == ["mj-shell-main", "mj-shell-nav"], [forward, backward]

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_app_shell_separators_are_inside_the_main_landmark(page, base_url: str) -> None:
    """
        The nav, split and inspector separators sit inside the one main
        landmark the shell supplies (they used to sit outside every landmark),
        each at the border it resizes, and dragging them with the mouse still
        resizes their regions and stores the sizes.

        The drag runs in the preview frame: in a load_fixture document
        (goto + set_content) Chromium does not grant pointer capture.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    page.set_viewport_size({"width": 1280, "height": 900})
    markup = _PLAIN_SHELL_MARKUP.replace('nav-open', 'nav-open inspector-open split storage-key="separator-test"').replace(
        '</mj-app-shell>', '<div slot="inspector"><p>Details</p></div></mj-app-shell>'
    )
    frame = _open_component(page, base_url, "mj-app-shell")
    frame.evaluate('''(markup) => {
        Object.keys(localStorage).filter((key) => key.startsWith("separator-test")).forEach((key) => localStorage.removeItem(key));
        document.body.innerHTML = markup;
    }''', markup)
    frame.wait_for_function("() => document.querySelector('#shell').shadowRoot.querySelector('.inspector-handle').hidden === false",
                            timeout=5000)
    expect(frame.get_by_role("main")).to_have_count(1)

    state = frame.evaluate('''() => {
        const root = document.querySelector("#shell").shadowRoot;
        const edge = (selector, side) => Math.round(root.querySelector(selector).getBoundingClientRect()[side]);
        return Array.from(root.querySelectorAll("[role=separator]")).map((handle) => {
            const main = handle.closest("[role=main]");
            return { cls: handle.classList[1], hidden: handle.hidden,
                     inMain: main !== null && main.classList.contains("workspace"),
                     x: Math.round(handle.getBoundingClientRect().left) };
        }).concat([{ navEnd: edge("[part=nav]", "right"), mainEnd: edge("[part=main]", "right"),
                     inspectorStart: edge("[part=inspector]", "left") }]);
    }''')
    handles = state[:-1]
    edges = state[-1]
    assert [(h["cls"], h["hidden"], h["inMain"]) for h in handles] == [
        ("nav-handle", False, True), ("pane-handle", False, True), ("inspector-handle", False, True)
    ], state
    assert handles[0]["x"] == edges["navEnd"], state
    assert handles[1]["x"] == edges["mainEnd"], state
    assert handles[2]["x"] == edges["inspectorStart"], state

    width = "(part) => Math.round(document.querySelector('#shell').shadowRoot.querySelector('[part=' + part + ']').getBoundingClientRect().width)"
    changes = []
    for selector, part, delta in ((".nav-handle", "nav", 40), (".inspector-handle", "inspector", -40),
                                  (".pane-handle", "split-secondary", 50)):
        before = frame.evaluate(width, part)
        box = frame.locator("#shell").locator(selector).bounding_box()
        start_x = box["x"] + 1
        start_y = box["y"] + box["height"] / 2
        page.mouse.move(start_x, start_y)
        page.mouse.down()
        page.mouse.move(start_x + delta / 2, start_y)
        page.mouse.move(start_x + delta, start_y)
        page.mouse.up()
        changes.append(frame.evaluate(width, part) - before)
    # The split stores a ratio rounded to 0.001, so the pane width may be a pixel off.
    assert changes[:2] == [40, 40] and abs(changes[2] + 50) <= 1, changes

    page.wait_for_timeout(400)
    stored = frame.evaluate('''() => ["nav-size", "inspector-size", "split-ratio"].map((name) =>
        localStorage.getItem("separator-test-" + name) !== null)''')
    assert stored == [True, True, True], stored

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_app_shell_narrow_inspector_drawer_stays_in_view(page, base_url: str) -> None:
    """
        In a 320px viewport an inspector wider than 85% of the shell opens at
        the inline end, fully inside the shell, and the shell is not scrolled
        sideways by focus moving into the drawer.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    page.set_viewport_size({"width": 320, "height": 700})
    markup = _PLAIN_SHELL_MARKUP.replace(
        'style="height:600px;"', 'style="height:600px; --mj-shell-inspector-width: 260px;"'
    ).replace(
        '</mj-app-shell>', '<div slot="inspector"><button id="apply" type="button">Apply</button></div></mj-app-shell>'
    )
    load_fixture(page, base_url, markup, ["mj-app-shell"])
    page.wait_for_function("() => document.querySelector('#shell').hasAttribute('narrow')", timeout=5000)
    page.evaluate("() => { document.querySelector('#shell').inspectorOpen = true; }")
    page.wait_for_timeout(1000)
    box = page.evaluate('''() => {
        const shell = document.querySelector("#shell");
        const outer = shell.getBoundingClientRect();
        const inner = shell.shadowRoot.querySelector("[part=inspector]").getBoundingClientRect();
        return { scroll: shell.scrollLeft, startGap: Math.round(inner.left - outer.left),
                 endGap: Math.round(outer.right - inner.right), focused: document.activeElement.id };
    }''')
    assert box["scroll"] == 0, box
    assert box["startGap"] > 0 and abs(box["endGap"]) <= 1, box
    assert box["focused"] == "apply", box

    return


# ---------------------------------------------------------------------------
# mj-search-results
# ---------------------------------------------------------------------------

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_search_results_untrusted_fields_are_inert(page, base_url: str) -> None:
    """
        Result fields, the unhighlighted snippet and the empty message are
        shown as text, and a javascript: URL is not used as the link.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    load_fixture(page, base_url, '<mj-search-results id="sr" total-count="1"></mj-search-results>', ["mj-search-results"])
    result = page.evaluate('''(payload) => {
        const sr = document.querySelector("#sr");
        sr.results = [{ id: payload, title: payload, url: "javascript:alert(1)", snippet: payload,
                        date: payload, category: payload }];
        const href = sr.shadowRoot.querySelector(".result-title").getAttribute("href");
        const snippet = sr.shadowRoot.querySelector(".result-snippet").textContent;
        sr.setAttribute("empty-message", payload);
        sr.setAttribute("empty-suggestion", payload);
        sr.results = [];
        return new Promise(resolve => setTimeout(() => resolve({
            hits: window.__hits === undefined ? 0 : window.__hits,
            images: sr.shadowRoot.querySelectorAll("img").length,
            href: href,
            snippetIsText: snippet === payload,
            emptyIsText: sr.shadowRoot.querySelector(".empty-state").textContent === payload + payload
        }), 200));
    }''', _INJECTION)
    assert result == {"hits": 0, "images": 0, "href": "#", "snippetIsText": True, "emptyIsText": True}, result

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_search_results_multi_term_highlight_keeps_the_text(page, base_url: str) -> None:
    """
        Highlighting several terms (including one that matches inside "mark"
        and "&amp;") wraps whole matches and leaves the snippet text intact.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    markup = '<mj-search-results id="sr" total-count="1" highlight-term="button a amp"></mj-search-results>'
    load_fixture(page, base_url, markup, ["mj-search-results"])
    result = page.evaluate('''() => {
        const sr = document.querySelector("#sr");
        const text = "What is a button? R&D <mark>";
        sr.results = [{ id: "1", title: "T", url: "/t", snippet: text }];
        const snippet = sr.shadowRoot.querySelector(".result-snippet");
        return {
            same: snippet.textContent === text,
            marks: Array.from(snippet.querySelectorAll("mark")).map(m => m.textContent)
        };
    }''')
    assert result["same"] is True, "The snippet text changed: {}".format(result)
    assert result["marks"] == ["a", "a", "button", "a"], result

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_search_results_page_change_queries_the_data_source(page, base_url: str) -> None:
    """
        With a dataSource, Next fetches the next page and keeps keyboard focus
        inside the component.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    load_fixture(page, base_url, '<mj-search-results id="sr" page-size="2"></mj-search-results>', ["mj-search-results"])
    page.evaluate('''() => {
        const all = [0, 1, 2, 3, 4].map(i => ({ id: i, title: "Item " + i, url: "/i" + i, snippet: "" }));
        document.querySelector("#sr").dataSource = {
            query: (q) => Promise.resolve({ items: all.slice(q.offset, q.offset + q.limit), total: 5 })
        };
    }''')
    titles = "Array.from(document.querySelector('#sr').shadowRoot.querySelectorAll('.result-title')).map(a => a.textContent)"
    page.wait_for_function("() => " + titles + ".length === 2", timeout=5000)

    page.locator("#sr [data-action=next]").click()
    page.wait_for_function("() => " + titles + "[0] === 'Item 2'", timeout=5000)
    focus_inside = page.evaluate("() => document.activeElement === document.querySelector('#sr')")
    assert focus_inside is True, "Focus should stay in the results after a page change"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_search_results_load_more_keeps_the_rows_and_pages_without_total(page, base_url: str) -> None:
    """
        With a dataSource that reports no total, Load more stays available
        after full pages, the loaded rows stay visible while the next batch
        loads (the button keeps focus, inert), a second click does not send a
        second request, and a short page ends paging.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    load_fixture(page, base_url, '<mj-search-results id="sr" load-mode="button" page-size="3"></mj-search-results>',
                 ["mj-search-results"])
    result = page.evaluate('''() => new Promise((resolve) => {
        const wait = (ms) => new Promise((done) => setTimeout(done, ms));
        const sr = document.querySelector("#sr");
        const all = Array.from({ length: 5 }, (_, i) => ({ id: i, title: "Item " + i, url: "/i" + i, snippet: "" }));
        const pending = [];
        let requests = 0;
        sr.dataSource = { query: (q) => new Promise((done) => {
            requests = requests + 1;
            pending.push(() => done({ items: all.slice(q.offset, q.offset + q.limit) }));
        }) };
        const root = sr.shadowRoot;
        const rows = () => root.querySelectorAll(".result-item").length;
        (async () => {
            await wait(30); pending.shift()(); await wait(30);
            const button = root.querySelector(".load-more-btn");
            const first = { rows: rows(), count: root.querySelector(".count-bar").textContent, hidden: button.hidden };
            button.focus(); button.click(); button.click(); await wait(30);
            const during = { rows: rows(), focused: root.activeElement === button,
                             disabled: button.getAttribute("aria-disabled"), requests };
            pending.shift()(); await wait(30);
            resolve({ first, during, last: { rows: rows(), hidden: button.hidden,
                      count: root.querySelector(".count-bar").textContent } });
        })();
    })''')
    assert result["first"] == {"rows": 3, "count": "3+ results", "hidden": False}, result
    assert result["during"] == {"rows": 3, "focused": True, "disabled": "true", "requests": 2}, result
    assert result["last"] == {"rows": 5, "hidden": True, "count": "5 results"}, result

    return


# ---------------------------------------------------------------------------
# mj-filter-panel
# ---------------------------------------------------------------------------

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_filter_panel_facet_data_is_inert(page, base_url: str) -> None:
    """
        Group labels, option labels and values, chips and the label attributes
        are shown as text.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    load_fixture(page, base_url, '<mj-filter-panel id="fp"></mj-filter-panel>', ["mj-filter-panel"])
    result = page.evaluate('''(payload) => {
        const fp = document.querySelector("#fp");
        ["label", "sort-label", "total-count"].forEach(n => fp.setAttribute(n, payload));
        fp.sortOptions = [{ value: payload, label: payload }];
        fp.filterConfig = [{ id: payload, label: payload, type: "checkbox", options: [{ value: payload, label: payload }] }];
        fp.value = { filters: { [payload]: [payload] } };
        return new Promise(resolve => setTimeout(() => resolve({
            hits: window.__hits === undefined ? 0 : window.__hits,
            images: fp.shadowRoot.querySelectorAll("img").length,
            chip: fp.shadowRoot.querySelector(".chip > span").textContent === payload + ": " + payload
        }), 200));
    }''', _INJECTION)
    assert result == {"hits": 0, "images": 0, "chip": True}, result

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_filter_panel_programmatic_radio_value_is_shown(page, base_url: str) -> None:
    """
        A radio selection set through ``value`` checks the radio, survives the
        removal of another group's chip, and chips show option labels.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    load_fixture(page, base_url, '<mj-filter-panel id="fp"></mj-filter-panel>', ["mj-filter-panel"])
    result = page.evaluate('''() => {
        const fp = document.querySelector("#fp");
        fp.filterConfig = [
            { id: "cat", label: "Category", options: [{ value: 42, label: "Electronics" }] },
            { id: "type", label: "Type", type: "radio",
              options: [{ value: "doc", label: "Document" }, { value: "img", label: "Image" }] }
        ];
        fp.value = { filters: { cat: [42], type: "doc" } };
        const root = fp.shadowRoot;
        const chips = Array.from(root.querySelectorAll(".chip > span")).map(c => c.textContent);
        root.querySelector(".chip-remove").click();
        const radio = root.querySelectorAll("input[type=radio]")[0];
        return { chips: chips, radioChecked: radio.checked, cat: fp.value.filters.cat };
    }''')
    assert result == {"chips": ["Category: Electronics", "Type: Document"], "radioChecked": True, "cat": []}, result

    return


# ---------------------------------------------------------------------------
# mj-query-builder
# ---------------------------------------------------------------------------

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_query_builder_readonly_disables_every_editing_control(page, base_url: str) -> None:
    """
        ``readonly`` set after render disables the combinators and the add and
        remove buttons as well as the rule controls.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    load_fixture(page, base_url, '<mj-query-builder id="qb"></mj-query-builder>', ["mj-query-builder"])
    enabled = page.evaluate('''() => {
        const qb = document.querySelector("#qb");
        qb.fieldSchema = [{ id: "name", label: "Name", type: "string" }];
        qb.value = { combinator: "AND", rules: [
            { field: "name", operator: "equals", value: "a" },
            { combinator: "OR", rules: [] }
        ] };
        qb.setAttribute("readonly", "");
        return Array.from(qb.shadowRoot.querySelectorAll("button, select, input"))
            .filter(e => e.disabled === false).map(e => e.getAttribute("part") || e.className);
    }''')
    assert enabled == [], "Controls still enabled in readonly mode: {}".format(enabled)

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_query_builder_rule_needs_a_value_and_submits_with_the_form(page, base_url: str) -> None:
    """
        A new rule is not shown as invalid; a rule without its value is
        invalid; the completed tree is submitted as JSON under ``name``.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    markup = '<form id="f"><mj-query-builder id="qb" name="query"></mj-query-builder></form>'
    load_fixture(page, base_url, markup, ["mj-query-builder"])
    result = page.evaluate('''() => {
        const qb = document.querySelector("#qb");
        const root = qb.shadowRoot;
        qb.fieldSchema = [{ id: "name", label: "Name", type: "string" }];
        root.querySelector("[part=add-rule]").click();
        const freshInvalid = root.querySelectorAll("[aria-invalid=true]").length;
        const choose = (part, value) => {
            const select = root.querySelector("[part=" + part + "]");
            select.value = value;
            select.dispatchEvent(new Event("change", { bubbles: true }));
        };
        choose("field-select", "name");
        choose("operator-select", "equals");
        const validWithoutValue = qb.checkValidity();
        const input = root.querySelector("input[part=value-input]");
        input.value = "Bob";
        input.dispatchEvent(new InputEvent("input", { bubbles: true, composed: true }));
        return {
            freshInvalid: freshInvalid,
            validWithoutValue: validWithoutValue,
            validWithValue: qb.checkValidity(),
            submitted: JSON.parse(new FormData(document.querySelector("#f")).get("query")).rules[0].value
        };
    }''')
    assert result == {"freshInvalid": 0, "validWithoutValue": False, "validWithValue": True, "submitted": "Bob"}, result

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_query_builder_change_event_carries_a_fresh_tree(page, base_url: str) -> None:
    """
        The builder copies an assigned value and each mj-query-change carries
        a new object, so the caller's data is never changed in place.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    load_fixture(page, base_url, '<mj-query-builder id="qb"></mj-query-builder>', ["mj-query-builder"])
    result = page.evaluate('''() => {
        const qb = document.querySelector("#qb");
        const mine = { combinator: "AND", rules: [] };
        qb.value = mine;
        const seen = [];
        qb.addEventListener("mj-query-change", e => seen.push(e.detail.value));
        qb.shadowRoot.querySelector("[part=add-rule]").click();
        qb.shadowRoot.querySelector("[part=add-rule]").click();
        return { mineRules: mine.rules.length, distinct: seen[0] !== seen[1], counts: seen.map(v => v.rules.length) };
    }''')
    assert result == {"mineRules": 0, "distinct": True, "counts": [1, 2]}, result

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_query_builder_required_is_value_missing_and_operator_map_is_a_copy(page, base_url: str) -> None:
    """
        An empty required builder reports valueMissing (not customError), and
        mutating the operatorMap it returns changes neither it nor another
        builder's defaults.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    markup = '<form><mj-query-builder id="qb" name="q" required></mj-query-builder></form><mj-query-builder id="other"></mj-query-builder>'
    load_fixture(page, base_url, markup, ["mj-query-builder"])
    result = page.evaluate('''() => {
        const qb = document.querySelector("#qb");
        const other = document.querySelector("#other");
        qb.operatorMap.string.push("hack");
        return {
            valueMissing: qb.validity.valueMissing,
            customError: qb.validity.customError,
            mine: qb.operatorMap.string.includes("hack"),
            others: other.operatorMap.string.includes("hack")
        };
    }''')
    assert result == {"valueMissing": True, "customError": False, "mine": False, "others": False}, result

    return


# ---------------------------------------------------------------------------
# mj-dropzone
# ---------------------------------------------------------------------------

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


# Markup that runs script if a component places a value into innerHTML unescaped.
_INJECTION_PAYLOAD = "x'\"><img src=\"data:,x\" onerror=\"top.__hits=(top.__hits||0)+1\">"


def _injection_hits(frame) -> int:
    """
        Return how many times the injection payload executed (0 when it never ran).

        :param frame: The preview Frame.

        :returns: The hit counter kept on the top window.
    """

    hits = frame.evaluate("() => window.top.__hits || 0")
    return hits


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_dropzone_submits_files_in_form_data(page, base_url: str) -> None:
    """
        Queued files reach the owning form's FormData as File objects under the name.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, "mj-dropzone")

    entries = frame.evaluate('''async () => {
        document.body.innerHTML = '<form><mj-dropzone name="docs"></mj-dropzone></form>';
        await new Promise(r => setTimeout(r, 200));
        const el = document.querySelector("mj-dropzone");
        el._processFiles([new File(["aa"], "a.txt"), new File(["bbb"], "b.txt")]);
        const data = new FormData(document.querySelector("form"));
        return data.getAll("docs").map(v => (v instanceof File) ? v.name + ":" + v.size : "string:" + v);
    }''')

    assert entries == ["a.txt:2", "b.txt:3"]

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_dropzone_required_and_reset(page, base_url: str) -> None:
    """
        A required dropzone is invalid while empty, valid with a file, and form.reset() empties it.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, "mj-dropzone")

    state = frame.evaluate('''async () => {
        document.body.innerHTML = '<form><mj-dropzone name="docs" required></mj-dropzone></form>';
        await new Promise(r => setTimeout(r, 200));
        const el = document.querySelector("mj-dropzone");
        const emptyValid = el.checkValidity();
        el._processFiles([new File(["a"], "a.txt")]);
        const filledValid = el.checkValidity();
        document.querySelector("form").reset();
        return { emptyValid, filledValid, afterReset: el.files.length,
                 rows: el.shadowRoot.querySelectorAll(".file-item").length };
    }''')

    assert state == {"emptyValid": False, "filledValid": True, "afterReset": 0, "rows": 0}

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_dropzone_values_are_not_markup(page, base_url: str) -> None:
    """
        File names, error text and attributes are shown as text, never parsed as HTML.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, "mj-dropzone")

    shown = frame.evaluate('''async (payload) => {
        document.body.innerHTML = '<mj-dropzone></mj-dropzone>';
        await new Promise(r => setTimeout(r, 200));
        const el = document.querySelector("mj-dropzone");
        for (const name of ["label", "browse-label", "drag-label", "accept"]) {
            el.setAttribute(name, payload);
        }
        el.removeAttribute("accept");
        el.setAttribute("max-size", "10");
        el._processFiles([new File(["a"], payload + ".txt"), new File(["x".repeat(50)], payload + ".big")]);
        el.updateFile(el.files[0].id, { status: "error", error: payload });
        await new Promise(r => setTimeout(r, 300));
        const root = el.shadowRoot;
        return {
            name: root.querySelector(".file-name").textContent === payload + ".txt",
            error: root.querySelector(".file-status-error").textContent === payload,
            rejected: root.querySelectorAll(".error-item").length,
            images: root.querySelectorAll("img").length
        };
    }''', _INJECTION_PAYLOAD)

    assert shown == {"name": True, "error": True, "rejected": 1, "images": 0}
    assert _injection_hits(frame) == 0

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_dropzone_single_mode_keeps_one_file(page, base_url: str) -> None:
    """
        With multiple="false" a multi-file drop keeps the first file and rejects the rest.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, "mj-dropzone")

    state = frame.evaluate('''async () => {
        document.body.innerHTML = '<mj-dropzone multiple="false"></mj-dropzone>';
        await new Promise(r => setTimeout(r, 200));
        const el = document.querySelector("mj-dropzone");
        let rejected = 0;
        el.addEventListener("mj-files-rejected", e => { rejected = e.detail.rejectedFiles.length; });
        el._processFiles([new File(["a"], "a.txt"), new File(["b"], "b.txt"), new File(["c"], "c.txt")]);
        return { files: el.files.map(f => f.file.name), rejected };
    }''')

    assert state == {"files": ["a.txt"], "rejected": 2}

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_dropzone_rejected_rows_have_their_own_part_and_follow_disabled(page, base_url: str) -> None:
    """
        A rejected-file row is part error-item (file-error is only the upload
        error text), and its dismiss button is disabled and inert while the
        zone is disabled.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    load_fixture(page, base_url, '<mj-dropzone id="dz" accept=".pdf"></mj-dropzone>', ["mj-dropzone"])
    result = page.evaluate('''() => {
        const dz = document.querySelector("#dz");
        dz._processFiles([new File(["x"], "notes.txt", { type: "text/plain" })]);
        dz.setAttribute("disabled", "");
        dz._processFiles([new File(["y"], "more.txt", { type: "text/plain" })]);
        const root = dz.shadowRoot;
        const buttons = Array.from(root.querySelectorAll(".error-dismiss-btn"));
        const parts = Array.from(root.querySelectorAll(".error-item")).map(row => row.getAttribute("part"));
        buttons[0].disabled = false;
        buttons[0].click();
        return { parts, fileErrorParts: root.querySelectorAll("[part~=file-error]").length,
                 disabled: buttons.map(b => b === buttons[0] ? true : b.disabled),
                 rowsAfterClick: root.querySelectorAll(".error-item").length };
    }''')
    assert result["fileErrorParts"] == 0, result
    assert result["parts"] and all(part == "error-item" for part in result["parts"]), result
    assert all(result["disabled"]), result
    assert result["rowsAfterClick"] == len(result["parts"]), result

    return


# ---------------------------------------------------------------------------
# mj-file-browser
# ---------------------------------------------------------------------------

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_file_browser_values_are_not_markup(page, base_url: str) -> None:
    """
        File names and metadata from the data source render as text in list, grid and preview.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, "mj-file-browser")

    shown = frame.evaluate('''async (payload) => {
        document.body.innerHTML = '<mj-file-browser style="height:300px"></mj-file-browser>';
        await new Promise(r => setTimeout(r, 200));
        const el = document.querySelector("mj-file-browser");
        el.setAttribute("label", payload);
        el.dataSource = { listDir() {
            return Promise.resolve([{ name: payload, type: payload, path: "/x", size: payload, modified: payload },
                                    { name: payload, type: "folder", path: "/f" }]);
        } };
        await new Promise(r => setTimeout(r, 200));
        const root = el.shadowRoot;
        root.querySelector("[data-index='0']").click();
        el.setAttribute("view", "grid");
        await new Promise(r => setTimeout(r, 300));
        return { images: root.querySelectorAll("img").length,
                 preview: root.querySelector(".preview-title").textContent === payload };
    }''', _INJECTION_PAYLOAD)

    assert shown == {"images": 0, "preview": True}
    assert _injection_hits(frame) == 0

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_file_browser_arrow_keys_move_focus_and_selection(page, base_url: str) -> None:
    """
        ArrowDown moves focus and selection to the next file; Ctrl+A selects all.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, "mj-file-browser")

    frame.evaluate('''async () => {
        document.body.innerHTML = '<mj-file-browser style="height:300px"></mj-file-browser>';
        await new Promise(r => setTimeout(r, 200));
        document.querySelector("mj-file-browser").dataSource = { listDir() {
            return [{ name: "a.txt", type: "text/plain", path: "/a.txt" },
                    { name: "b.txt", type: "text/plain", path: "/b.txt" },
                    { name: "c.txt", type: "text/plain", path: "/c.txt" }];
        } };
        await new Promise(r => setTimeout(r, 200));
        document.querySelector("mj-file-browser").shadowRoot.querySelector("[data-index='0']").focus();
    }''')

    page.keyboard.press("ArrowDown")
    page.keyboard.press("ArrowDown")
    after_arrows = frame.evaluate('''() => {
        const el = document.querySelector("mj-file-browser");
        return { focused: el.shadowRoot.activeElement.getAttribute("data-path"),
                 selected: el.selectedFiles.map(f => f.name) };
    }''')
    page.keyboard.press("Control+a")
    selected_all = frame.evaluate("() => document.querySelector('mj-file-browser').selectedFiles.length")

    assert after_arrows == {"focused": "/c.txt", "selected": ["c.txt"]}
    assert selected_all == 3

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_file_browser_folder_click_selects_and_tree_lists_folders(page, base_url: str) -> None:
    """
        A single click on a folder selects it (no navigation); the tree lists the folders.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, "mj-file-browser")

    state = frame.evaluate('''async () => {
        document.body.innerHTML = '<mj-file-browser style="height:300px"></mj-file-browser>';
        await new Promise(r => setTimeout(r, 200));
        const el = document.querySelector("mj-file-browser");
        el.dataSource = { listDir(path) {
            return path === "/" ? [{ name: "docs", type: "folder", path: "/docs" }, { name: "a.txt", type: "text/plain" }]
                                : [{ name: "inner.txt", type: "text/plain" }];
        } };
        await new Promise(r => setTimeout(r, 200));
        el.shadowRoot.querySelector("[data-index='0']").click();
        await new Promise(r => setTimeout(r, 100));
        const afterClick = { path: el.currentPath, selected: el.selectedFiles.map(f => f.name) };
        const tree = Array.from(el.shadowRoot.querySelectorAll("[role=treeitem]")).map(t => t.getAttribute("data-path"));
        el.shadowRoot.querySelector("[data-index='0']").dispatchEvent(new MouseEvent("dblclick", { bubbles: true }));
        await new Promise(r => setTimeout(r, 200));
        return { afterClick, tree, afterOpen: el.currentPath, selectionCleared: el.selectedFiles.length };
    }''')

    assert state["afterClick"] == {"path": "/", "selected": ["docs"]}
    assert state["tree"] == ["/", "/docs"]
    assert state["afterOpen"] == "/docs"
    assert state["selectionCleared"] == 0

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_file_browser_navigation_clears_the_previous_listing(page, base_url: str) -> None:
    """
        Entering a folder removes the previous folder's items at once and shows
        a loading state until the new listing arrives.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    load_fixture(page, base_url, '<mj-file-browser id="fb" style="height:300px"></mj-file-browser>', ["mj-file-browser"])
    result = page.evaluate('''() => new Promise((resolve) => {
        const wait = (ms) => new Promise((done) => setTimeout(done, ms));
        const fb = document.querySelector("#fb");
        const pending = {};
        fb.dataSource = { listDir: (path) => new Promise((done) => { pending[path] = done; }) };
        const pane = fb.shadowRoot.querySelector(".file-pane");
        (async () => {
            await wait(30);
            pending["/"]([{ name: "docs", type: "folder" }, { name: "a.txt", type: "text" }]);
            await wait(30);
            const before = pane.querySelectorAll("[data-index]").length;
            fb.currentPath = "/docs";
            await wait(30);
            const during = { items: pane.querySelectorAll("[data-index]").length, busy: pane.getAttribute("aria-busy") };
            pending["/docs"]([{ name: "guide.md", type: "text" }]);
            await wait(30);
            resolve({ before, during, after: pane.querySelectorAll("[data-index]").length });
        })();
    })''')
    assert result == {"before": 2, "during": {"items": 0, "busy": "true"}, "after": 1}, result

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_file_browser_hidden_items_leave_the_selection_and_shift_f6_from_outside(page, base_url: str) -> None:
    """
        Removing show-hidden drops hidden items from the selection (one
        mj-selection-change); Shift+F6 from outside the panes goes to the
        last pane.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    markup = '<mj-file-browser id="fb" show-hidden preview="none" style="height:300px"></mj-file-browser>'
    load_fixture(page, base_url, markup, ["mj-file-browser"])
    result = page.evaluate('''() => new Promise((resolve) => {
        const wait = (ms) => new Promise((done) => setTimeout(done, ms));
        const fb = document.querySelector("#fb");
        fb.dataSource = { listDir: () => [{ name: "a.txt", type: "text" }, { name: ".env", type: "text" }] };
        (async () => {
            await wait(50);
            const root = fb.shadowRoot;
            const rows = root.querySelectorAll(".file-pane [data-index]");
            rows[0].click();
            rows[1].dispatchEvent(new MouseEvent("click", { bubbles: true, composed: true, ctrlKey: true }));
            const events = [];
            fb.addEventListener("mj-selection-change", (e) => events.push(e.detail.selectedFiles.map(f => f.name)));
            fb.removeAttribute("show-hidden");
            await wait(30);
            root.querySelector(".breadcrumb-seg").focus();
            resolve({ selected: fb.selectedFiles.map(f => f.name), events });
        })();
    })''')
    page.keyboard.press("Shift+F6")
    pane = page.evaluate('''() => {
        const active = document.querySelector("#fb").shadowRoot.activeElement;
        return active && active.closest(".file-pane") ? "files" : active && active.closest(".tree-pane") ? "tree" : "other";
    }''')
    assert result == {"selected": ["a.txt"], "events": [["a.txt"]]}, result
    assert pane == "files", pane

    return


# ---------------------------------------------------------------------------
# mj-activity-feed
# ---------------------------------------------------------------------------

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_activity_feed_load_more_button_visible(page, base_url: str) -> None:
    """
        Without a data source the Load older activity button is hidden after
        items are set, and visible once the host sets hasMore = true.

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

    hidden_without_opt_in = frame.evaluate('''() => {
        const el = document.querySelector("mj-activity-feed");
        el.hasMore = false;
        const btn = el.shadowRoot.querySelector("[part=load-more]");
        const hidden = btn.hidden;
        el.hasMore = true;
        return hidden;
    }''')
    assert hidden_without_opt_in is True

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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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
    frame.evaluate('() => { document.querySelector("mj-activity-feed").hasMore = true; }')

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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_activity_feed_values_are_not_markup(page, base_url: str) -> None:
    """
        Actor, avatar, timestamp, label and empty-message values render as text.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, "mj-activity-feed")

    shown = frame.evaluate('''async (payload) => {
        document.body.innerHTML = '<mj-activity-feed></mj-activity-feed>';
        await new Promise(r => setTimeout(r, 200));
        const el = document.querySelector("mj-activity-feed");
        el.setAttribute("label", payload);
        el.setAttribute("empty-message", payload);
        await new Promise(r => setTimeout(r, 100));
        const emptyText = el.shadowRoot.querySelector(".empty-state").textContent === payload;
        el.items = [{ id: "1", actor: { name: payload, avatarUrl: payload }, action: payload,
                      body: payload, timestamp: payload }];
        await new Promise(r => setTimeout(r, 300));
        const root = el.shadowRoot;
        return { emptyText, actor: root.querySelector(".item-actor").textContent === payload,
                 time: root.querySelector("time").textContent === payload,
                 avatarImg: root.querySelectorAll("img[onerror]").length };
    }''', _INJECTION_PAYLOAD)

    assert shown == {"emptyText": True, "actor": True, "time": True, "avatarImg": 0}
    assert _injection_hits(frame) == 0

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_activity_feed_null_cursor_ends_paging(page, base_url: str) -> None:
    """
        A page that returns cursor null hides Load older and no further query is made.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, "mj-activity-feed")

    state = frame.evaluate('''async () => {
        document.body.innerHTML = '<mj-activity-feed></mj-activity-feed>';
        await new Promise(r => setTimeout(r, 200));
        const el = document.querySelector("mj-activity-feed");
        const cursors = [];
        el.dataSource = { query({ cursor }) {
            cursors.push(cursor);
            return Promise.resolve(cursor === null
                ? { items: [{ id: "a", action: "first" }], cursor: "p2" }
                : { items: [{ id: "b", action: "second" }], cursor: null });
        } };
        await new Promise(r => setTimeout(r, 100));
        const button = el.shadowRoot.querySelector("[part=load-more]");
        const visibleBefore = button.hidden === false;
        button.click();
        await new Promise(r => setTimeout(r, 100));
        button.click();
        await new Promise(r => setTimeout(r, 100));
        return { visibleBefore, hiddenAfter: button.hidden, cursors, items: el.items.map(i => i.id) };
    }''')

    assert state == {"visibleBefore": True, "hiddenAfter": True, "cursors": [None, "p2"], "items": ["a", "b"]}

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_activity_feed_page_down_moves_between_articles(page, base_url: str) -> None:
    """
        Articles are focusable and Page Down moves focus to the next article.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, "mj-activity-feed")

    frame.evaluate('''async () => {
        document.body.innerHTML = '<mj-activity-feed></mj-activity-feed>';
        await new Promise(r => setTimeout(r, 200));
        const el = document.querySelector("mj-activity-feed");
        el.items = [{ id: "1", action: "one" }, { id: "2", action: "two" }];
        el.shadowRoot.querySelector("article").focus();
    }''')
    page.keyboard.press("PageDown")

    position = frame.evaluate('''() => {
        const el = document.querySelector("mj-activity-feed");
        return el.shadowRoot.activeElement.getAttribute("aria-posinset");
    }''')
    assert position == "2"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_activity_feed_host_paging_waits_for_the_answer(page, base_url: str) -> None:
    """
        Without a data source, Load older is offered only after hasMore = true;
        repeated clicks emit mj-load-older once until the host assigns items.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    load_fixture(page, base_url, '<mj-activity-feed id="af"></mj-activity-feed>', ["mj-activity-feed"])
    result = page.evaluate('''() => {
        const feed = document.querySelector("#af");
        const button = feed.shadowRoot.querySelector("[part=load-more]");
        const emitted = [];
        feed.addEventListener("mj-load-older", () => emitted.push(1));
        feed.items = [{ id: 1, action: "one" }];
        const hiddenWithoutOptIn = button.hidden;
        feed.hasMore = true;
        button.click(); button.click(); button.click();
        const pending = { count: emitted.length, busy: feed.shadowRoot.querySelector("[role=feed]").getAttribute("aria-busy") };
        feed.items = feed.items.concat([{ id: 2, action: "two" }]);
        button.click();
        return { hiddenWithoutOptIn, pending, afterAnswer: emitted.length };
    }''')
    assert result == {"hiddenWithoutOptIn": True, "pending": {"count": 1, "busy": "true"}, "afterAnswer": 2}, result

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_activity_feed_feed_exposes_only_articles(page, base_url: str) -> None:
    """
        Day headings are hidden from assistive technology and describe the
        first article of their day; the empty state is outside role=feed.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    load_fixture(page, base_url, '<mj-activity-feed id="af" group-by="date"></mj-activity-feed>', ["mj-activity-feed"])
    result = page.evaluate('''() => {
        const feed = document.querySelector("#af");
        const root = feed.shadowRoot;
        const list = root.querySelector("[role=feed]");
        const empty = { inFeed: list.querySelector(".empty-state") !== null,
                        shown: root.querySelector(".empty-state").hidden === false };
        feed.items = [{ id: 1, action: "a", timestamp: "2026-11-10" }, { id: 2, action: "b", timestamp: "2026-11-10" },
                      { id: 3, action: "c", timestamp: "2026-11-08" }];
        const exposed = Array.from(list.children).filter(c => c.getAttribute("aria-hidden") !== "true").map(c => c.localName);
        const described = Array.from(list.querySelectorAll("article")).map(a => {
            const id = a.getAttribute("aria-describedby");
            return id === null ? null : root.getElementById(id).getAttribute("part");
        });
        return { empty, exposed, described };
    }''')
    assert result["empty"] == {"inFeed": False, "shown": True}, result
    assert result["exposed"] == ["article", "article", "article"], result
    assert result["described"] == ["group-heading", None, "group-heading"], result

    return


# ---------------------------------------------------------------------------
# mj-comments
# ---------------------------------------------------------------------------

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_comments_values_are_not_markup(page, base_url: str) -> None:
    """
        Author name, avatar, createdAt, reactions, label and empty-message render as text.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, "mj-comments")

    shown = frame.evaluate('''async (payload) => {
        document.body.innerHTML = '<mj-comments></mj-comments>';
        await new Promise(r => setTimeout(r, 200));
        const el = document.querySelector("mj-comments");
        el.setAttribute("label", payload);
        el.setAttribute("empty-message", payload);
        await new Promise(r => setTimeout(r, 100));
        const emptyText = el.shadowRoot.querySelector(".empty-state").textContent === payload;
        el.comments = [{ id: payload, authorId: payload, authorName: payload, authorAvatar: payload,
                         body: payload, createdAt: payload,
                         reactions: [{ emoji: payload, count: payload, userIds: [] }] }];
        await new Promise(r => setTimeout(r, 300));
        const root = el.shadowRoot;
        return { emptyText, author: root.querySelector(".comment-author").textContent === payload,
                 time: root.querySelector("time").textContent === payload,
                 avatarImg: root.querySelectorAll("img[onerror]").length };
    }''', _INJECTION_PAYLOAD)

    assert shown == {"emptyText": True, "author": True, "time": True, "avatarImg": 0}
    assert _injection_hits(frame) == 0

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_comments_show_more_reveals_loaded_replies(page, base_url: str) -> None:
    """
        "Show N more replies" reveals replies already in the data without a host round trip.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, "mj-comments")

    state = frame.evaluate('''async () => {
        document.body.innerHTML = '<mj-comments max-visible-replies="2"></mj-comments>';
        await new Promise(r => setTimeout(r, 200));
        const el = document.querySelector("mj-comments");
        const reply = (id) => ({ id, authorName: "R", body: id });
        el.comments = [{ id: "c1", authorName: "A", body: "top",
                         replies: [reply("r1"), reply("r2"), reply("r3"), reply("r4")] }];
        let loadEvents = 0;
        el.addEventListener("mj-load-replies", () => { loadEvents = loadEvents + 1; });
        const before = el.shadowRoot.querySelectorAll("article").length;
        el.shadowRoot.querySelector(".show-more-replies-btn").click();
        return { before, after: el.shadowRoot.querySelectorAll("article").length,
                 buttons: el.shadowRoot.querySelectorAll(".show-more-replies-btn").length, loadEvents };
    }''')

    assert state == {"before": 3, "after": 5, "buttons": 0, "loadEvents": 0}

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_comments_failed_post_keeps_text(page, base_url: str) -> None:
    """
        When dataSource.post() rejects, the composer keeps the text and shows an error.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, "mj-comments")

    state = frame.evaluate('''async () => {
        document.body.innerHTML = '<mj-comments></mj-comments>';
        await new Promise(r => setTimeout(r, 200));
        const el = document.querySelector("mj-comments");
        let posts = 0;
        el.dataSource = { post() { posts = posts + 1; return Promise.reject(new Error("offline")); } };
        const textarea = el.shadowRoot.querySelector(".top-composer .composer-textarea");
        textarea.value = "keep me";
        textarea.dispatchEvent(new Event("input", { bubbles: true }));
        const submit = el.shadowRoot.querySelector(".top-composer .composer-submit-btn");
        submit.click();
        submit.click();
        await new Promise(r => setTimeout(r, 100));
        const error = el.shadowRoot.querySelector(".top-composer .composer-error");
        return { text: textarea.value, errorShown: error.hidden === false, posts };
    }''')

    assert state == {"text": "keep me", "errorShown": True, "posts": 1}

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_comments_numeric_author_id_owns_comment(page, base_url: str) -> None:
    """
        A numeric authorId matches current-user-id, and deleted comments offer no actions.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, "mj-comments")

    state = frame.evaluate('''async () => {
        document.body.innerHTML = '<mj-comments current-user-id="42"></mj-comments>';
        await new Promise(r => setTimeout(r, 200));
        const el = document.querySelector("mj-comments");
        el.comments = [{ id: "c1", authorId: 42, authorName: "Me", body: "mine" },
                       { id: "c2", authorId: 42, authorName: "Me", body: "gone", deleted: true }];
        const root = el.shadowRoot;
        return {
            own: root.querySelectorAll("article[data-comment-id=c1] [data-action=edit]").length,
            deletedActions: root.querySelectorAll("article[data-comment-id=c2] .comment-actions").length,
            heading: root.querySelector(".count-heading").textContent
        };
    }''')

    assert state == {"own": 1, "deletedActions": 0, "heading": "1 comment"}

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_comments_readonly_reactions_are_counts_only(page, base_url: str) -> None:
    """
        Under readonly the reactions are plain counts: no buttons, no picker
        and no mj-comment-react.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    load_fixture(page, base_url, '<mj-comments id="cm" readonly current-user-id="u1"></mj-comments>', ["mj-comments"])
    result = page.evaluate('''() => {
        const cm = document.querySelector("#cm");
        const reacts = [];
        cm.addEventListener("mj-comment-react", (e) => reacts.push(e.detail));
        cm.comments = [{ id: "c1", authorId: "u2", authorName: "A", body: "Hi",
                         reactions: [{ emoji: "+1", count: 2, userIds: ["u1"] }] }];
        const root = cm.shadowRoot;
        root.querySelectorAll(".reaction-chip").forEach(chip => chip.click());
        return { chips: Array.from(root.querySelectorAll(".reaction-chip")).map(c => c.localName + ":" + c.textContent.trim()),
                 buttons: root.querySelectorAll(".reaction-bar button").length, reacts: reacts.length };
    }''')
    assert result == {"chips": ["span:+1 2"], "buttons": 0, "reacts": 0}, result

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_comments_replies_below_max_depth_are_shown_flattened(page, base_url: str) -> None:
    """
        A reply deeper than max-depth is shown in the deepest thread after the
        reply it answers, so the count heading matches what is shown.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    load_fixture(page, base_url, '<mj-comments id="cm" max-depth="1"></mj-comments>', ["mj-comments"])
    result = page.evaluate('''() => {
        const cm = document.querySelector("#cm");
        cm.comments = [{ id: "c1", authorName: "A", body: "top", replies: [
            { id: "r1", authorName: "B", body: "reply", replies: [{ id: "r1a", authorName: "C", body: "deep" }] },
            { id: "r2", authorName: "D", body: "second" }] }];
        const root = cm.shadowRoot;
        const thread = root.querySelector(".reply-thread");
        return { heading: root.querySelector(".count-heading").textContent,
                 thread: Array.from(thread.querySelectorAll("article")).map(a => a.getAttribute("data-comment-id")),
                 nested: thread.querySelectorAll(".reply-thread").length };
    }''')
    assert result == {"heading": "4 comments", "thread": ["r1", "r1a", "r2"], "nested": 0}, result

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_comments_add_comment_ignores_a_duplicate_id(page, base_url: str) -> None:
    """
        addComment() with an id that is already in the thread adds nothing.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    load_fixture(page, base_url, '<mj-comments id="cm"></mj-comments>', ["mj-comments"])
    result = page.evaluate('''() => {
        const cm = document.querySelector("#cm");
        cm.comments = [{ id: "c1", authorName: "A", body: "first", replies: [{ id: "r1", authorName: "B", body: "reply" }] }];
        cm.addComment({ id: "c1", authorName: "A", body: "again" });
        cm.addComment({ id: "r1", authorName: "B", body: "again" }, "c1");
        cm.addComment({ id: "c2", authorName: "C", body: "new" });
        return { top: cm.comments.map(c => c.id), replies: cm.comments[0].replies.length,
                 heading: cm.shadowRoot.querySelector(".count-heading").textContent };
    }''')
    assert result == {"top": ["c1", "c2"], "replies": 1, "heading": "3 comments"}, result

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_comments_feed_holds_only_articles(page, base_url: str) -> None:
    """
        The role="feed" list holds only the top-level comment articles: each
        reply thread sits inside the article of the comment it answers (it
        used to be a sibling of the articles in the feed). PageDown / PageUp
        still move between top-level comments, also from inside a reply, and
        focus restored after a re-render lands on the comment's own control,
        not on the same control of a reply nested in its article.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    load_fixture(page, base_url, '<mj-comments id="cm" current-user-id="u1"></mj-comments>', ["mj-comments"])
    structure = page.evaluate('''() => {
        const cm = document.querySelector("#cm");
        cm.comments = [
            { id: "c1", authorId: "u2", authorName: "A", body: "first",
              reactions: [{ emoji: "\\u{1F44D}", count: 1, userIds: ["u2"] }],
              replies: [{ id: "r1", authorId: "u1", authorName: "B", body: "reply",
                          reactions: [{ emoji: "\\u{1F44D}", count: 1, userIds: ["u3"] }],
                          replies: [{ id: "r1a", authorId: "u3", authorName: "C", body: "deeper" }] }] },
            { id: "c2", authorId: "u3", authorName: "D", body: "second" },
            { id: "c3", authorId: "u4", authorName: "E", body: "third" }
        ];
        const feed = cm.shadowRoot.querySelector("[role=feed]");
        return {
            children: Array.from(feed.children).map((child) => child.localName + ":" + child.getAttribute("data-comment-id")),
            threads: Array.from(feed.querySelectorAll(".reply-thread")).map((thread) =>
                thread.getAttribute("role") + ":" + thread.parentElement.getAttribute("data-comment-id") + ":" +
                Array.from(thread.children).filter((child) => child.localName === "article").map((child) => child.getAttribute("data-comment-id")).join(","))
        };
    }''')
    assert structure == {
        "children": ["article:c1", "article:c2", "article:c3"],
        "threads": ["group:c1:r1", "group:r1:r1a"],
    }, structure

    focused = "() => document.querySelector('#cm').shadowRoot.activeElement.getAttribute('data-comment-id')"
    page.evaluate("() => document.querySelector('#cm').shadowRoot.querySelector('article[data-comment-id=r1a]').focus()")
    page.keyboard.press("PageDown")
    after_down = page.evaluate(focused)
    page.keyboard.press("PageDown")
    after_second_down = page.evaluate(focused)
    page.keyboard.press("PageUp")
    page.keyboard.press("PageUp")
    after_up = page.evaluate(focused)
    assert [after_down, after_second_down, after_up] == ["c2", "c3", "c1"], [after_down, after_second_down, after_up]

    # c1's own chip has focus; the chip goes away on re-render, the reply's chip of the same emoji stays.
    restored = page.evaluate('''() => {
        const cm = document.querySelector("#cm");
        cm.shadowRoot.querySelector("article[data-comment-id=c1] [data-focus-key^='react:']").focus();
        cm.comments[0].reactions = [];
        cm.comments = cm.comments;
        const active = cm.shadowRoot.activeElement;
        return active.localName + ":" + active.getAttribute("data-comment-id");
    }''')
    assert restored == "article:c1", restored

    return


# ---------------------------------------------------------------------------
# mj-mention-input
# ---------------------------------------------------------------------------

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


def _prepare_mention_input(frame, markup: str) -> None:
    """
        Replace the frame content with `markup` and give its mj-mention-input a mention source.

        :param frame: The preview Frame.
        :param markup: Markup containing one mj-mention-input.
    """

    frame.evaluate('''async (markup) => {
        document.body.innerHTML = markup;
        await new Promise(r => setTimeout(r, 200));
        const el = document.querySelector("mj-mention-input");
        el.mentionSource = { suggest(trigger, query) {
            return Promise.resolve([{ id: 1, displayName: "Alice Martin" }, { id: 2, displayName: "Bob Lee" }]
                .filter(u => u.displayName.toLowerCase().includes(query.toLowerCase())));
        } };
        el.focus();
    }''', markup)
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mention_input_real_typing_opens_popup_and_inserts_token(page, base_url: str) -> None:
    """
        Keyboard typing (no injected Range) opens the popup; Enter inserts the highlighted mention.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, "mj-mention-input")
    _prepare_mention_input(frame, '<mj-mention-input label="Message"></mj-mention-input>')

    page.keyboard.type("hi @Al")
    frame.wait_for_function('''() => {
        const popup = document.querySelector("mj-mention-input").shadowRoot.querySelector("[role=listbox]");
        return popup.hidden === false && popup.querySelector("[role=option]") !== null;
    }''', timeout=5000)

    active = frame.evaluate('''() => {
        const root = document.querySelector("mj-mention-input").shadowRoot;
        const textbox = root.querySelector("[role=textbox]");
        const id = textbox.getAttribute("aria-activedescendant");
        return id !== null && root.getElementById(id).getAttribute("aria-selected") === "true";
    }''')
    assert active is True

    page.keyboard.press("Enter")
    state = frame.evaluate('''() => {
        const el = document.querySelector("mj-mention-input");
        return { value: el.value, mentions: el.mentions.map(m => m.id),
                 popupHidden: el.shadowRoot.querySelector("[role=listbox]").hidden };
    }''')
    assert state == {"value": "hi @Alice Martin ", "mentions": [1], "popupHidden": True}

    page.keyboard.press("Backspace")
    page.keyboard.press("Backspace")
    after_delete = frame.evaluate("() => document.querySelector('mj-mention-input').mentions.length")
    assert after_delete == 0

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mention_input_trigger_needs_word_start(page, base_url: str) -> None:
    """
        A trigger character inside a word (an e-mail address) does not open the popup.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, "mj-mention-input")
    _prepare_mention_input(frame, '<mj-mention-input></mj-mention-input>')

    page.keyboard.type("mail a@Al")
    frame.wait_for_timeout(500)
    hidden = frame.evaluate(
        "() => document.querySelector('mj-mention-input').shadowRoot.querySelector('[role=listbox]').hidden"
    )
    assert hidden is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mention_input_values_are_not_markup(page, base_url: str) -> None:
    """
        Suggestion fields, label and placeholder render as text.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, "mj-mention-input")
    frame.evaluate('''async (payload) => {
        document.body.innerHTML = '<mj-mention-input></mj-mention-input>';
        await new Promise(r => setTimeout(r, 200));
        const el = document.querySelector("mj-mention-input");
        el.setAttribute("label", payload);
        el.setAttribute("placeholder", payload);
        el.mentionSource = { suggest() {
            return Promise.resolve([{ id: payload, displayName: payload, subtitle: payload, avatarUrl: payload }]);
        } };
        el.focus();
    }''', _INJECTION_PAYLOAD)

    page.keyboard.type("@x")
    frame.wait_for_function('''() => {
        const popup = document.querySelector("mj-mention-input").shadowRoot.querySelector("[role=listbox]");
        return popup.hidden === false;
    }''', timeout=5000)
    frame.wait_for_timeout(300)

    label_ok = frame.evaluate('''(payload) => {
        const root = document.querySelector("mj-mention-input").shadowRoot;
        return root.querySelector(".mention-label").textContent === payload &&
               root.querySelector(".suggestion-name").textContent === payload;
    }''', _INJECTION_PAYLOAD)
    assert label_ok is True
    assert _injection_hits(frame) == 0

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mention_input_disabled_and_readonly_block_editing(page, base_url: str) -> None:
    """
        disabled and readonly turn editing off and expose aria-disabled / aria-readonly.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, "mj-mention-input")
    state = frame.evaluate('''async () => {
        document.body.innerHTML = '<mj-mention-input disabled></mj-mention-input><mj-mention-input readonly></mj-mention-input>';
        await new Promise(r => setTimeout(r, 200));
        const boxes = Array.from(document.querySelectorAll("mj-mention-input"))
            .map(el => el.shadowRoot.querySelector("[role=textbox]"));
        return { disabled: [boxes[0].getAttribute("contenteditable"), boxes[0].getAttribute("aria-disabled")],
                 readonly: [boxes[1].getAttribute("contenteditable"), boxes[1].getAttribute("aria-readonly")] };
    }''')

    assert state == {"disabled": ["false", "true"], "readonly": ["false", "true"]}

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mention_input_reconnect_keeps_content(page, base_url: str) -> None:
    """
        Moving the element to another parent keeps the typed text and its form value.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, "mj-mention-input")
    state = frame.evaluate('''async () => {
        document.body.innerHTML = '<form><mj-mention-input name="msg"></mj-mention-input></form><div id="other"></div>';
        await new Promise(r => setTimeout(r, 200));
        const el = document.querySelector("mj-mention-input");
        el.value = "kept text";
        document.getElementById("other").appendChild(el);
        await new Promise(r => setTimeout(r, 100));
        document.querySelector("form").appendChild(el);
        await new Promise(r => setTimeout(r, 100));
        return { value: el.value, shown: el.shadowRoot.querySelector("[role=textbox]").textContent,
                 form: new FormData(document.querySelector("form")).get("msg") };
    }''')

    assert state == {"value": "kept text", "shown": "kept text", "form": "kept text"}

    return


# ---------------------------------------------------------------------------
# mj-chat-composer
# ---------------------------------------------------------------------------

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_chat_composer_values_are_not_markup(page, base_url: str) -> None:
    """
        Attachment file names and placeholder/label/accept attributes render as text.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, "mj-chat-composer")
    shown = frame.evaluate('''async (payload) => {
        document.body.innerHTML = '<mj-chat-composer></mj-chat-composer>';
        await new Promise(r => setTimeout(r, 200));
        const el = document.querySelector("mj-chat-composer");
        for (const name of ["placeholder", "label", "accept"]) {
            el.setAttribute(name, payload);
        }
        el.removeAttribute("accept");
        el._addFiles([new File(["a"], payload + ".txt", { type: "text/plain" })]);
        await new Promise(r => setTimeout(r, 300));
        const root = el.shadowRoot;
        return { placeholder: root.querySelector("textarea").getAttribute("placeholder") === payload,
                 name: root.querySelector(".attachment-name").textContent === payload + ".txt",
                 images: root.querySelectorAll("img").length };
    }''', _INJECTION_PAYLOAD)

    assert shown == {"placeholder": True, "name": True, "images": 0}
    assert _injection_hits(frame) == 0

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_chat_composer_oversized_attachment_is_reported(page, base_url: str) -> None:
    """
        A file over max-attachment-size fires mj-attachment-reject and shows an error chip.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, "mj-chat-composer")
    state = frame.evaluate('''async () => {
        document.body.innerHTML = '<mj-chat-composer max-attachment-size="10"></mj-chat-composer>';
        await new Promise(r => setTimeout(r, 200));
        const el = document.querySelector("mj-chat-composer");
        let rejected = 0;
        el.addEventListener("mj-attachment-reject", e => { rejected = e.detail.rejectedFiles.length; });
        el._addFiles([new File(["x".repeat(50)], "big.bin")]);
        return { rejected, attachments: el.attachments.length,
                 errorChips: el.shadowRoot.querySelectorAll(".attachment-item.is-error").length };
    }''')

    assert state == {"rejected": 1, "attachments": 0, "errorChips": 1}

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_chat_composer_loading_and_max_length(page, base_url: str) -> None:
    """
        loading makes the textarea read-only and blocks send; max-length limits typing.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, "mj-chat-composer")
    frame.evaluate('''async () => {
        document.body.innerHTML = '<mj-chat-composer max-length="5"></mj-chat-composer>';
        await new Promise(r => setTimeout(r, 200));
        document.querySelector("mj-chat-composer").focus();
    }''')
    page.keyboard.type("abcdefgh")

    state = frame.evaluate('''() => {
        const el = document.querySelector("mj-chat-composer");
        const root = el.shadowRoot;
        const typed = root.querySelector("textarea").value;
        const counter = root.querySelector(".counter").textContent;
        let sends = 0;
        el.addEventListener("mj-send", () => { sends = sends + 1; });
        el.setAttribute("loading", "");
        root.querySelector(".send-btn").click();
        return { typed, counter, readOnly: root.querySelector("textarea").readOnly, sends };
    }''')

    assert state == {"typed": "abcde", "counter": "5 / 5", "readOnly": True, "sends": 0}

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_chat_composer_emoji_button_inserts_emoji(page, base_url: str) -> None:
    """
        The emoji button fires mj-emoji-request and its panel inserts the emoji at the caret.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, "mj-chat-composer")
    state = frame.evaluate('''async () => {
        document.body.innerHTML = '<mj-chat-composer></mj-chat-composer>';
        await new Promise(r => setTimeout(r, 200));
        const el = document.querySelector("mj-chat-composer");
        let requests = 0;
        el.addEventListener("mj-emoji-request", () => { requests = requests + 1; });
        el.value = "hi";
        el.shadowRoot.querySelector(".emoji-btn").click();
        const option = el.shadowRoot.querySelector(".emoji-option");
        const emoji = option.getAttribute("data-emoji");
        option.click();
        return { requests, inserted: el.value === "hi" + emoji,
                 panelHidden: el.shadowRoot.querySelector(".emoji-panel").hidden };
    }''')

    assert state == {"requests": 1, "inserted": True, "panelHidden": True}

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_chat_composer_is_a_form_landmark_only_with_a_label(page, base_url: str) -> None:
    """
        A composer is a named ``form`` landmark only when the page gives it a
        ``label``; without one its root has no role, so several composers do
        not repeat an unnamed landmark (axe landmark-unique). The textarea is
        named either way, and setting or removing ``label`` later follows.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, "mj-chat-composer")
    state = frame.evaluate('''async () => {
        const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
        document.body.innerHTML = '<mj-chat-composer id="plain"></mj-chat-composer>'
            + '<mj-chat-composer id="plain-2"></mj-chat-composer>'
            + '<mj-chat-composer id="named" label="Reply to Ana"></mj-chat-composer>';
        await wait(200);
        const read = (id) => {
            const root = document.getElementById(id).shadowRoot;
            const part = root.querySelector("[part=root]");
            return { role: part.getAttribute("role"), label: part.getAttribute("aria-label"),
                     textarea: root.querySelector("textarea").getAttribute("aria-label") };
        };
        const initial = { plain: read("plain"), named: read("named") };
        document.getElementById("plain").setAttribute("label", "New message");
        document.getElementById("named").removeAttribute("label");
        await wait(50);
        return { initial: initial, labelled: read("plain"), unlabelled: read("named") };
    }''')

    assert state["initial"]["plain"]["role"] is None, state
    assert state["initial"]["plain"]["label"] is None, state
    assert state["initial"]["plain"]["textarea"] == "Message composer", state
    assert state["initial"]["named"] == {"role": "form", "label": "Reply to Ana", "textarea": "Reply to Ana"}, state
    assert state["labelled"] == {"role": "form", "label": "New message", "textarea": "New message"}, state
    assert state["unlabelled"]["role"] is None, state
    assert state["unlabelled"]["label"] is None, state

    expect(frame.get_by_role("form")).to_have_count(1)

    return


# ---------------------------------------------------------------------------
# mj-chat-message
# ---------------------------------------------------------------------------

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_chat_message_body_html_is_sanitized(page, base_url: str) -> None:
    """
        bodyHtml keeps allow-listed markup, drops handlers, styles and script URLs, and never runs script.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, "mj-chat-message")
    result = frame.evaluate('''async () => {
        document.body.innerHTML = '<mj-chat-message></mj-chat-message>';
        await new Promise(r => setTimeout(r, 200));
        const el = document.querySelector("mj-chat-message");
        el.bodyHtml = '<img src=x onerror="top.__hits=(top.__hits||0)+1">' +
            '<svg onload="top.__hits=(top.__hits||0)+1"></svg>' +
            '<a href="javascript:top.__hits=1" style="position:fixed" target="_blank" id="x">bad</a>' +
            '<a href="https://example.com/" title="ok">good</a>' +
            '<p class="c" onclick="top.__hits=1"><strong>bold</strong></p>';
        await new Promise(r => setTimeout(r, 300));
        return el.shadowRoot.querySelector(".msg-html").innerHTML;
    }''')

    assert result == (
        '<a rel="noopener noreferrer">bad</a>'
        '<a href="https://example.com/" title="ok" rel="noopener noreferrer">good</a>'
        '<p><strong>bold</strong></p>'
    )
    assert _injection_hits(frame) == 0

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_chat_message_body_html_links_refuse_data_and_blob_urls(page, base_url: str) -> None:
    """
        The shared sanitizer (core/sanitize.js) gives message links the link
        context: data: (even an image) and blob: hrefs are dropped, unknown
        wrappers such as <div> are unwrapped, and allow-listed inline tags stay.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, "mj-chat-message")
    result = frame.evaluate('''async () => {
        document.body.innerHTML = '<mj-chat-message></mj-chat-message>';
        await new Promise(r => setTimeout(r, 200));
        const el = document.querySelector("mj-chat-message");
        el.bodyHtml = '<div>one</div><a href="data:image/png;base64,AA">img</a>' +
            '<a href="blob:https://example.com/1">blob</a><mark>m</mark>';
        await new Promise(r => setTimeout(r, 200));
        return el.shadowRoot.querySelector(".msg-html").innerHTML;
    }''')

    assert result == (
        'one<a rel="noopener noreferrer">img</a>'
        '<a rel="noopener noreferrer">blob</a><mark>m</mark>'
    )
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_chat_message_attributes_are_not_markup(page, base_url: str) -> None:
    """
        author-name, author-avatar, timestamp, status and reactions render as text.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, "mj-chat-message")
    shown = frame.evaluate('''async (payload) => {
        document.body.innerHTML = '<mj-chat-message variant="outgoing" allow-reactions></mj-chat-message>';
        await new Promise(r => setTimeout(r, 200));
        const el = document.querySelector("mj-chat-message");
        for (const name of ["author-name", "author-avatar", "timestamp", "status", "message-id"]) {
            el.setAttribute(name, payload);
        }
        el.reactions = [{ emoji: payload, count: payload, userIds: [] }];
        el.replyTo = { authorName: payload, preview: payload };
        await new Promise(r => setTimeout(r, 300));
        const root = el.shadowRoot;
        return { author: root.querySelector(".msg-author-name").textContent === payload,
                 time: root.querySelector("time").textContent === payload,
                 status: root.querySelector(".msg-status").getAttribute("aria-label"),
                 avatarImg: root.querySelectorAll("img[onerror]").length };
    }''', _INJECTION_PAYLOAD)

    assert shown == {"author": True, "time": True, "status": "Sent", "avatarImg": 0}
    assert _injection_hits(frame) == 0

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_chat_message_status_and_properties_update(page, base_url: str) -> None:
    """
        Status changes after render update the indicator; properties set before connect do not throw.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, "mj-chat-message")
    state = frame.evaluate('''async () => {
        const early = document.createElement("mj-chat-message");
        early.bodyHtml = "<b>early</b>";
        early.reactions = [{ emoji: "x", count: 1 }];
        early.replyTo = { authorName: "A", preview: "p" };
        early.currentUserId = "u1";
        document.body.innerHTML = '<mj-chat-message variant="outgoing" status="sent"></mj-chat-message>';
        document.body.appendChild(early);
        await new Promise(r => setTimeout(r, 200));
        const el = document.querySelector("mj-chat-message");
        el.setAttribute("status", "read");
        return { status: el.shadowRoot.querySelector(".msg-status").getAttribute("aria-label"),
                 earlyBody: early.shadowRoot.querySelector(".msg-html b") !== null };
    }''')

    assert state == {"status": "Read", "earlyBody": True}

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_chat_message_menu_keyboard(page, base_url: str) -> None:
    """
        The action menu supports ArrowDown and Escape, and Escape returns focus to the trigger.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, "mj-chat-message")
    frame.evaluate('''async () => {
        document.body.innerHTML = '<mj-chat-message allow-actions author-name="A"></mj-chat-message>';
        await new Promise(r => setTimeout(r, 200));
        const el = document.querySelector("mj-chat-message");
        el.shadowRoot.querySelector(".actions-trigger").click();
    }''')
    page.keyboard.press("ArrowDown")
    focused = frame.evaluate(
        "() => document.querySelector('mj-chat-message').shadowRoot.activeElement.textContent"
    )
    page.keyboard.press("Escape")
    after = frame.evaluate('''() => {
        const root = document.querySelector("mj-chat-message").shadowRoot;
        return { hidden: root.querySelector(".context-menu").hidden,
                 focus: root.activeElement.className };
    }''')

    assert focused == "Copy text"
    assert after == {"hidden": True, "focus": "actions-trigger"}

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_chat_message_author_id_is_reported_in_events(page, base_url: str) -> None:
    """
        author-id is exposed as authorId and carried in the message's events.

        :param page: The Playwright page.
        :param base_url: The site base URL.
    """

    markup = '<mj-chat-message id="msg" message-id="m1" author-id="u7" author-name="Ann" allow-actions>Hi</mj-chat-message>'
    load_fixture(page, base_url, markup, ["mj-chat-message"])
    result = page.evaluate('''() => {
        const msg = document.querySelector("#msg");
        const details = [];
        msg.addEventListener("mj-message-react", (e) => details.push(e.detail));
        msg.reactions = [{ emoji: "+1", count: 1, userIds: [] }];
        msg.shadowRoot.querySelector(".reaction-chip").click();
        return { authorId: msg.authorId, detail: details[0] };
    }''')
    assert result["authorId"] == "u7", result
    assert result["detail"] == {"messageId": "m1", "authorId": "u7", "emoji": "+1", "active": True}, result

    return
