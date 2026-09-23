"""
    .. module:: testcomponents.tests.test_func_buttons

    Functional Playwright tests for every component in the 'buttons' group.

    Components covered:
      - mj-button         (click, disabled, loading, mj-click event)
      - mj-fab            (click, mj-click event, speed-dial toggle, mj-expanded)
      - mj-toggle-button  (pressed state, aria-pressed, mj-change, mj-pressed)
      - mj-disclosure-button (expanded state, aria-expanded, mj-change, mj-expanded)
      - mj-copy-button    (copy behavior, mj-copy event, disabled blocks)
      - mj-share-button   (force-menu fallback, menu open/close, aria-expanded)
      - mj-favorite-button (pressed/count, aria-pressed, mj-change, mj-pressed, rollback)

    Each test navigates to the component page, loads the preview iframe, and
    interacts with the rendered component.  All tests are independent.
"""

import ccai.testbase as testbase

from testcomponents.harness.factories import create_page


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_GROUP = "buttons"


def _open_component(page, base_url: str, tag: str):
    """
        Navigate to the component playground page and wait for the custom
        element to be registered inside the preview iframe.

        :param page: The Playwright page.
        :param base_url: The site base URL.
        :param tag: The component custom-element tag name.

        :returns: The preview Frame with the component registered.
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


def _load_example(page, base_url: str, tag: str, html: str):
    """
        Navigate to the component page, replace the playground editor with
        custom HTML, click Run, then re-acquire the preview frame.

        :param page: The Playwright page.
        :param base_url: The site base URL.
        :param tag: The custom-element tag name.
        :param html: The HTML snippet to load into the playground.

        :returns: The fresh preview Frame after Run.
    """

    page.goto(base_url + f"/components/{_GROUP}/{tag}")
    page.wait_for_selector("[data-testid=playground-preview]")
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


def _collect_events(frame, tag: str, event_names: list):
    """
        Inject a global event collector on the first matching element in the
        frame so subsequent interactions can be inspected.

        :param frame: The preview iframe Frame.
        :param tag: The custom-element tag name to attach listeners to.
        :param event_names: List of event names to listen for.
    """

    frame.evaluate(
        """([tag, names]) => {
            window.__mjevents = [];
            const el = document.querySelector(tag);
            names.forEach(n => el.addEventListener(n, e => window.__mjevents.push(n)));
        }""",
        [tag, event_names],
    )
    return


def _get_events(frame) -> list:
    """
        Return the list of captured event names collected since the last
        call to _collect_events.

        :param frame: The preview iframe Frame.

        :returns: Ordered list of event name strings that fired.
    """

    events = frame.evaluate("() => window.__mjevents")
    return events


# ===========================================================================
# mj-button
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_button_click_fires_mj_click(page, base_url):
    """
        Clicking an enabled mj-button fires the mj-click custom event.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = '<mj-button variant="primary">Click me</mj-button>'
    frame = _load_example(page, base_url, "mj-button", html)

    _collect_events(frame=frame, tag="mj-button", event_names=["mj-click"])
    frame.locator("mj-button").click()

    events = _get_events(frame=frame)
    assert "mj-click" in events

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_button_disabled_blocks_mj_click(page, base_url):
    """
        Clicking a disabled mj-button does NOT fire mj-click.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = "<mj-button disabled>Disabled</mj-button>"
    frame = _load_example(page, base_url, "mj-button", html)

    _collect_events(frame=frame, tag="mj-button", event_names=["mj-click"])

    # Use JS dispatch so we bypass the OS-level disabled check on the inner
    # <button>, but still exercise the component's own guard.
    frame.evaluate(
        "() => document.querySelector('mj-button').shadowRoot.querySelector('button').click()"
    )

    events = _get_events(frame=frame)
    assert "mj-click" not in events

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_button_loading_blocks_mj_click(page, base_url):
    """
        A mj-button in the loading state does NOT fire mj-click when its
        inner button is programmatically clicked.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = "<mj-button loading>Saving…</mj-button>"
    frame = _load_example(page, base_url, "mj-button", html)

    _collect_events(frame=frame, tag="mj-button", event_names=["mj-click"])

    frame.evaluate(
        "() => document.querySelector('mj-button').shadowRoot.querySelector('button').click()"
    )

    events = _get_events(frame=frame)
    assert "mj-click" not in events

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_button_loading_sets_aria_busy(page, base_url):
    """
        A mj-button with the loading attribute has aria-busy="true" on its
        inner button.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = "<mj-button loading>Saving…</mj-button>"
    frame = _load_example(page, base_url, "mj-button", html)

    aria_busy = frame.evaluate(
        "() => document.querySelector('mj-button').shadowRoot"
        ".querySelector('button').getAttribute('aria-busy')"
    )
    assert aria_busy == "true"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_button_inner_button_disabled_when_disabled_attr(page, base_url):
    """
        When mj-button carries the disabled attribute the inner <button> is
        also disabled.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = "<mj-button disabled>No</mj-button>"
    frame = _load_example(page, base_url, "mj-button", html)

    is_disabled = frame.evaluate(
        "() => document.querySelector('mj-button').shadowRoot"
        ".querySelector('button').disabled"
    )
    assert is_disabled is True

    return


# ===========================================================================
# mj-fab
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_fab_click_fires_mj_click(page, base_url):
    """
        Clicking a plain mj-fab (no speed-dial) fires the mj-click event.

        The inner shadow-DOM button is activated via JS because the FAB uses
        position:fixed which can cause the Playwright pointer to miss it.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = (
        '<mj-fab label="Compose">'
        '<span slot="icon">+</span>'
        "</mj-fab>"
    )
    frame = _load_example(page, base_url, "mj-fab", html)

    events = frame.evaluate(
        """() => {
            window.__mjevents = [];
            const el = document.querySelector('mj-fab');
            el.addEventListener('mj-click', () => window.__mjevents.push('mj-click'));
            el.shadowRoot.querySelector('button').click();
            return window.__mjevents;
        }"""
    )
    assert "mj-click" in events

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_fab_speed_dial_toggles_expanded(page, base_url):
    """
        Clicking a speed-dial mj-fab toggles the expanded attribute and
        fires mj-expanded.

        The inner shadow-DOM button is activated via JS because the FAB uses
        position:fixed which can cause the Playwright pointer to miss it.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = (
        '<mj-fab label="Actions" speed-dial>'
        '<span slot="icon">+</span>'
        "</mj-fab>"
    )
    frame = _load_example(page, base_url, "mj-fab", html)

    # Initially not expanded.
    expanded_before = frame.evaluate(
        "() => document.querySelector('mj-fab').hasAttribute('expanded')"
    )
    assert expanded_before is False

    result = frame.evaluate(
        """() => {
            window.__mjevents = [];
            const el = document.querySelector('mj-fab');
            el.addEventListener('mj-expanded', () => window.__mjevents.push('mj-expanded'));
            el.shadowRoot.querySelector('button').click();
            return { events: window.__mjevents, expanded: el.hasAttribute('expanded') };
        }"""
    )
    assert result["expanded"] is True
    assert "mj-expanded" in result["events"]

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_fab_speed_dial_aria_expanded(page, base_url):
    """
        The inner button of a speed-dial mj-fab reflects aria-expanded as
        the expanded state changes.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = (
        '<mj-fab label="Actions" speed-dial>'
        '<span slot="icon">+</span>'
        "</mj-fab>"
    )
    frame = _load_example(page, base_url, "mj-fab", html)

    aria_before = frame.evaluate(
        "() => document.querySelector('mj-fab').shadowRoot"
        ".querySelector('button').getAttribute('aria-expanded')"
    )
    assert aria_before == "false"

    # Click the inner button via JS to avoid fixed-position pointer issues.
    frame.evaluate(
        "() => document.querySelector('mj-fab').shadowRoot.querySelector('button').click()"
    )

    aria_after = frame.evaluate(
        "() => document.querySelector('mj-fab').shadowRoot"
        ".querySelector('button').getAttribute('aria-expanded')"
    )
    assert aria_after == "true"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_fab_speed_dial_collapse_on_second_click(page, base_url):
    """
        Clicking a speed-dial mj-fab a second time collapses it.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = (
        '<mj-fab label="Actions" speed-dial>'
        '<span slot="icon">+</span>'
        "</mj-fab>"
    )
    frame = _load_example(page, base_url, "mj-fab", html)

    frame.evaluate(
        "() => document.querySelector('mj-fab').shadowRoot.querySelector('button').click()"
    )
    frame.evaluate(
        "() => document.querySelector('mj-fab').shadowRoot.querySelector('button').click()"
    )

    expanded = frame.evaluate(
        "() => document.querySelector('mj-fab').hasAttribute('expanded')"
    )
    assert expanded is False

    return


# ===========================================================================
# mj-toggle-button
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_toggle_button_click_fires_mj_change_and_mj_pressed(page, base_url):
    """
        Clicking an mj-toggle-button fires mj-change followed by mj-pressed.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = "<mj-toggle-button>Bold</mj-toggle-button>"
    frame = _load_example(page, base_url, "mj-toggle-button", html)

    _collect_events(
        frame=frame,
        tag="mj-toggle-button",
        event_names=["mj-change", "mj-pressed"],
    )
    frame.locator("mj-toggle-button").click()

    events = _get_events(frame=frame)
    assert "mj-change" in events
    assert "mj-pressed" in events

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_toggle_button_pressed_attribute_reflects(page, base_url):
    """
        After clicking, the pressed attribute is set on the mj-toggle-button
        host element.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = "<mj-toggle-button>Bold</mj-toggle-button>"
    frame = _load_example(page, base_url, "mj-toggle-button", html)

    pressed_before = frame.evaluate(
        "() => document.querySelector('mj-toggle-button').hasAttribute('pressed')"
    )
    assert pressed_before is False

    frame.locator("mj-toggle-button").click()

    pressed_after = frame.evaluate(
        "() => document.querySelector('mj-toggle-button').hasAttribute('pressed')"
    )
    assert pressed_after is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_toggle_button_aria_pressed_reflects_state(page, base_url):
    """
        The inner button's aria-pressed attribute tracks the pressed state.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = "<mj-toggle-button>Mute</mj-toggle-button>"
    frame = _load_example(page, base_url, "mj-toggle-button", html)

    aria_before = frame.evaluate(
        "() => document.querySelector('mj-toggle-button').shadowRoot"
        ".querySelector('button').getAttribute('aria-pressed')"
    )
    assert aria_before == "false"

    frame.locator("mj-toggle-button").click()

    aria_after = frame.evaluate(
        "() => document.querySelector('mj-toggle-button').shadowRoot"
        ".querySelector('button').getAttribute('aria-pressed')"
    )
    assert aria_after == "true"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_toggle_button_initial_pressed_state(page, base_url):
    """
        A mj-toggle-button with the pressed attribute starts with
        aria-pressed="true".

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = "<mj-toggle-button pressed>Muted</mj-toggle-button>"
    frame = _load_example(page, base_url, "mj-toggle-button", html)

    aria_pressed = frame.evaluate(
        "() => document.querySelector('mj-toggle-button').shadowRoot"
        ".querySelector('button').getAttribute('aria-pressed')"
    )
    assert aria_pressed == "true"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_toggle_button_disabled_blocks_interaction(page, base_url):
    """
        A disabled mj-toggle-button does not fire mj-change or change its
        pressed state when clicked.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = "<mj-toggle-button disabled>Bold</mj-toggle-button>"
    frame = _load_example(page, base_url, "mj-toggle-button", html)

    _collect_events(
        frame=frame,
        tag="mj-toggle-button",
        event_names=["mj-change", "mj-pressed"],
    )

    frame.evaluate(
        "() => document.querySelector('mj-toggle-button').shadowRoot"
        ".querySelector('button').click()"
    )

    events = _get_events(frame=frame)
    assert "mj-change" not in events
    assert "mj-pressed" not in events

    return


# ===========================================================================
# mj-disclosure-button
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_disclosure_button_click_fires_mj_change_and_mj_expanded(page, base_url):
    """
        Clicking an mj-disclosure-button fires mj-change and mj-expanded.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = (
        '<mj-disclosure-button controls="panel1">More details</mj-disclosure-button>'
        '<div id="panel1">Content here.</div>'
    )
    frame = _load_example(page, base_url, "mj-disclosure-button", html)

    _collect_events(
        frame=frame,
        tag="mj-disclosure-button",
        event_names=["mj-change", "mj-expanded"],
    )
    frame.locator("mj-disclosure-button").click()

    events = _get_events(frame=frame)
    assert "mj-change" in events
    assert "mj-expanded" in events

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_disclosure_button_aria_expanded_toggles(page, base_url):
    """
        The inner button's aria-expanded reflects the expanded state after
        clicking.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = (
        '<mj-disclosure-button controls="panel2">Show more</mj-disclosure-button>'
        '<div id="panel2">Hidden content.</div>'
    )
    frame = _load_example(page, base_url, "mj-disclosure-button", html)

    aria_before = frame.evaluate(
        "() => document.querySelector('mj-disclosure-button').shadowRoot"
        ".querySelector('button').getAttribute('aria-expanded')"
    )
    assert aria_before == "false"

    frame.locator("mj-disclosure-button").click()

    aria_after = frame.evaluate(
        "() => document.querySelector('mj-disclosure-button').shadowRoot"
        ".querySelector('button').getAttribute('aria-expanded')"
    )
    assert aria_after == "true"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_disclosure_button_expanded_attribute_reflects(page, base_url):
    """
        After clicking, the expanded attribute is set on the host element.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = (
        '<mj-disclosure-button controls="panel3">Details</mj-disclosure-button>'
        '<div id="panel3">Details content.</div>'
    )
    frame = _load_example(page, base_url, "mj-disclosure-button", html)

    expanded_before = frame.evaluate(
        "() => document.querySelector('mj-disclosure-button').hasAttribute('expanded')"
    )
    assert expanded_before is False

    frame.locator("mj-disclosure-button").click()

    expanded_after = frame.evaluate(
        "() => document.querySelector('mj-disclosure-button').hasAttribute('expanded')"
    )
    assert expanded_after is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_disclosure_button_initial_expanded_state(page, base_url):
    """
        A mj-disclosure-button with the expanded attribute starts with
        aria-expanded="true".

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = (
        '<mj-disclosure-button controls="panel4" expanded>Less</mj-disclosure-button>'
        '<div id="panel4">Always visible.</div>'
    )
    frame = _load_example(page, base_url, "mj-disclosure-button", html)

    aria_expanded = frame.evaluate(
        "() => document.querySelector('mj-disclosure-button').shadowRoot"
        ".querySelector('button').getAttribute('aria-expanded')"
    )
    assert aria_expanded == "true"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_disclosure_button_disabled_blocks_interaction(page, base_url):
    """
        A disabled mj-disclosure-button does not toggle when its inner button
        is clicked.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = (
        '<mj-disclosure-button controls="panel5" disabled>Disabled</mj-disclosure-button>'
        '<div id="panel5">Content.</div>'
    )
    frame = _load_example(page, base_url, "mj-disclosure-button", html)

    _collect_events(
        frame=frame,
        tag="mj-disclosure-button",
        event_names=["mj-change", "mj-expanded"],
    )

    frame.evaluate(
        "() => document.querySelector('mj-disclosure-button').shadowRoot"
        ".querySelector('button').click()"
    )

    events = _get_events(frame=frame)
    assert "mj-change" not in events

    return


# ===========================================================================
# mj-copy-button
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_copy_button_click_fires_mj_copy(page, base_url):
    """
        Clicking an mj-copy-button with a value attribute fires mj-copy
        after a successful clipboard write.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = '<mj-copy-button value="hello world">Copy</mj-copy-button>'
    frame = _load_example(page, base_url, "mj-copy-button", html)

    # Grant clipboard permissions so writeText resolves.
    page.context.grant_permissions(permissions=["clipboard-read", "clipboard-write"])

    _collect_events(frame=frame, tag="mj-copy-button", event_names=["mj-copy", "mj-copy-error"])
    frame.locator("mj-copy-button").click()

    # Wait briefly for the async clipboard operation.
    frame.wait_for_timeout(500)

    events = _get_events(frame=frame)
    assert "mj-copy" in events

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_copy_button_success_sets_data_status(page, base_url):
    """
        After a successful copy the host element gains data-status="success".

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = '<mj-copy-button value="copied text">Copy</mj-copy-button>'
    frame = _load_example(page, base_url, "mj-copy-button", html)

    page.context.grant_permissions(permissions=["clipboard-read", "clipboard-write"])

    frame.locator("mj-copy-button").click()
    frame.wait_for_timeout(500)

    status = frame.evaluate(
        "() => document.querySelector('mj-copy-button').dataset.status"
    )
    assert status == "success"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_copy_button_disabled_blocks_copy(page, base_url):
    """
        A disabled mj-copy-button does not fire mj-copy when its inner
        button is programmatically clicked.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = "<mj-copy-button value=\"nope\" disabled>Copy</mj-copy-button>"
    frame = _load_example(page, base_url, "mj-copy-button", html)

    page.context.grant_permissions(permissions=["clipboard-read", "clipboard-write"])

    _collect_events(frame=frame, tag="mj-copy-button", event_names=["mj-copy"])

    frame.evaluate(
        "() => document.querySelector('mj-copy-button').shadowRoot"
        ".querySelector('button').click()"
    )
    frame.wait_for_timeout(300)

    events = _get_events(frame=frame)
    assert "mj-copy" not in events

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_copy_button_label_shown_in_button(page, base_url):
    """
        The label attribute text is rendered inside the mj-copy-button.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = '<mj-copy-button value="x" label="Copy install command">Copy install command</mj-copy-button>'
    frame = _load_example(page, base_url, "mj-copy-button", html)

    label_text = frame.evaluate(
        "() => document.querySelector('mj-copy-button').shadowRoot"
        ".querySelector('.label').textContent"
    )
    assert label_text == "Copy install command"

    return


# ===========================================================================
# mj-share-button
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_share_button_force_menu_opens_fallback(page, base_url):
    """
        With force-menu set the fallback menu appears on click.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = (
        '<mj-share-button force-menu share-url="https://example.com"'
        ' share-title="Test">Share</mj-share-button>'
    )
    frame = _load_example(page, base_url, "mj-share-button", html)

    menu_hidden_before = frame.evaluate(
        "() => document.querySelector('mj-share-button').shadowRoot"
        ".querySelector('.fallback-menu').hidden"
    )
    assert menu_hidden_before is True

    frame.locator("mj-share-button").click()

    menu_hidden_after = frame.evaluate(
        "() => document.querySelector('mj-share-button').shadowRoot"
        ".querySelector('.fallback-menu').hidden"
    )
    assert menu_hidden_after is False

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_share_button_force_menu_aria_expanded(page, base_url):
    """
        The inner button's aria-expanded reflects the open state of the
        fallback menu when force-menu is set.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = (
        '<mj-share-button force-menu share-url="https://example.com"'
        ' share-title="Test">Share</mj-share-button>'
    )
    frame = _load_example(page, base_url, "mj-share-button", html)

    aria_before = frame.evaluate(
        "() => document.querySelector('mj-share-button').shadowRoot"
        ".querySelector('button').getAttribute('aria-expanded')"
    )
    assert aria_before == "false"

    frame.locator("mj-share-button").click()

    aria_after = frame.evaluate(
        "() => document.querySelector('mj-share-button').shadowRoot"
        ".querySelector('button').getAttribute('aria-expanded')"
    )
    assert aria_after == "true"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_share_button_force_menu_second_click_closes(page, base_url):
    """
        A second click on the share button closes the fallback menu.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = (
        '<mj-share-button force-menu share-url="https://example.com"'
        ' share-title="Test">Share</mj-share-button>'
    )
    frame = _load_example(page, base_url, "mj-share-button", html)

    frame.locator("mj-share-button").click()
    frame.locator("mj-share-button").click()

    menu_hidden = frame.evaluate(
        "() => document.querySelector('mj-share-button').shadowRoot"
        ".querySelector('.fallback-menu').hidden"
    )
    assert menu_hidden is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_share_button_disabled_blocks_menu(page, base_url):
    """
        A disabled mj-share-button does not open the fallback menu when
        the inner button is clicked.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = (
        '<mj-share-button force-menu disabled share-url="https://example.com"'
        ' share-title="Test">Share</mj-share-button>'
    )
    frame = _load_example(page, base_url, "mj-share-button", html)

    frame.evaluate(
        "() => document.querySelector('mj-share-button').shadowRoot"
        ".querySelector('button').click()"
    )

    menu_hidden = frame.evaluate(
        "() => document.querySelector('mj-share-button').shadowRoot"
        ".querySelector('.fallback-menu').hidden"
    )
    assert menu_hidden is True

    return


# ===========================================================================
# mj-favorite-button
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_favorite_button_click_fires_mj_change_and_mj_pressed(page, base_url):
    """
        Clicking an mj-favorite-button fires mj-change and mj-pressed.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = '<mj-favorite-button flavor="like">Like</mj-favorite-button>'
    frame = _load_example(page, base_url, "mj-favorite-button", html)

    _collect_events(
        frame=frame,
        tag="mj-favorite-button",
        event_names=["mj-change", "mj-pressed"],
    )
    frame.locator("mj-favorite-button").click()

    events = _get_events(frame=frame)
    assert "mj-change" in events
    assert "mj-pressed" in events

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_favorite_button_pressed_attribute_reflects(page, base_url):
    """
        Clicking an mj-favorite-button sets the pressed attribute on the host.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = '<mj-favorite-button flavor="favorite">Favorite</mj-favorite-button>'
    frame = _load_example(page, base_url, "mj-favorite-button", html)

    pressed_before = frame.evaluate(
        "() => document.querySelector('mj-favorite-button').hasAttribute('pressed')"
    )
    assert pressed_before is False

    frame.locator("mj-favorite-button").click()

    pressed_after = frame.evaluate(
        "() => document.querySelector('mj-favorite-button').hasAttribute('pressed')"
    )
    assert pressed_after is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_favorite_button_aria_pressed_reflects_state(page, base_url):
    """
        The inner button's aria-pressed mirrors the optimistic pressed state.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = '<mj-favorite-button flavor="bookmark">Bookmark</mj-favorite-button>'
    frame = _load_example(page, base_url, "mj-favorite-button", html)

    aria_before = frame.evaluate(
        "() => document.querySelector('mj-favorite-button').shadowRoot"
        ".querySelector('button').getAttribute('aria-pressed')"
    )
    assert aria_before == "false"

    frame.locator("mj-favorite-button").click()

    aria_after = frame.evaluate(
        "() => document.querySelector('mj-favorite-button').shadowRoot"
        ".querySelector('button').getAttribute('aria-pressed')"
    )
    assert aria_after == "true"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_favorite_button_initial_pressed_state(page, base_url):
    """
        An mj-favorite-button with pressed starts with aria-pressed="true"
        and data-optimistic="true".

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = '<mj-favorite-button flavor="like" pressed>Unlike</mj-favorite-button>'
    frame = _load_example(page, base_url, "mj-favorite-button", html)

    aria_pressed = frame.evaluate(
        "() => document.querySelector('mj-favorite-button').shadowRoot"
        ".querySelector('button').getAttribute('aria-pressed')"
    )
    assert aria_pressed == "true"

    optimistic = frame.evaluate(
        "() => document.querySelector('mj-favorite-button').dataset.optimistic"
    )
    assert optimistic == "true"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_favorite_button_count_displayed(page, base_url):
    """
        When the count attribute is set the count element is visible and
        shows the correct number.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = '<mj-favorite-button flavor="like" count="42">Like</mj-favorite-button>'
    frame = _load_example(page, base_url, "mj-favorite-button", html)

    count_hidden = frame.evaluate(
        "() => document.querySelector('mj-favorite-button').shadowRoot"
        ".querySelector('.count').hidden"
    )
    assert count_hidden is False

    count_text = frame.evaluate(
        "() => document.querySelector('mj-favorite-button').shadowRoot"
        ".querySelector('.count').textContent"
    )
    assert count_text == "42"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_favorite_button_rollback_fires_mj_rollback(page, base_url):
    """
        Calling rollback() on an mj-favorite-button after a click fires
        mj-rollback and reverts the pressed state.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = '<mj-favorite-button flavor="like">Like</mj-favorite-button>'
    frame = _load_example(page, base_url, "mj-favorite-button", html)

    # Click to set optimistic pressed state.
    frame.locator("mj-favorite-button").click()

    _collect_events(frame=frame, tag="mj-favorite-button", event_names=["mj-rollback"])

    # Call rollback to revert.
    frame.evaluate("() => document.querySelector('mj-favorite-button').rollback()")

    events = _get_events(frame=frame)
    assert "mj-rollback" in events

    pressed_after_rollback = frame.evaluate(
        "() => document.querySelector('mj-favorite-button').hasAttribute('pressed')"
    )
    assert pressed_after_rollback is False

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_favorite_button_disabled_blocks_interaction(page, base_url):
    """
        A disabled mj-favorite-button does not toggle when its inner button
        is clicked.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = '<mj-favorite-button flavor="like" disabled>Like</mj-favorite-button>'
    frame = _load_example(page, base_url, "mj-favorite-button", html)

    _collect_events(
        frame=frame,
        tag="mj-favorite-button",
        event_names=["mj-change", "mj-pressed"],
    )

    frame.evaluate(
        "() => document.querySelector('mj-favorite-button').shadowRoot"
        ".querySelector('button').click()"
    )

    events = _get_events(frame=frame)
    assert "mj-change" not in events
    assert "mj-pressed" not in events

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_favorite_button_pending_blocks_interaction(page, base_url):
    """
        An mj-favorite-button in the pending state does not toggle when
        its inner button is clicked.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = '<mj-favorite-button flavor="like" pending>Like</mj-favorite-button>'
    frame = _load_example(page, base_url, "mj-favorite-button", html)

    _collect_events(
        frame=frame,
        tag="mj-favorite-button",
        event_names=["mj-change", "mj-pressed"],
    )

    frame.evaluate(
        "() => document.querySelector('mj-favorite-button').shadowRoot"
        ".querySelector('button').click()"
    )

    events = _get_events(frame=frame)
    assert "mj-change" not in events
    assert "mj-pressed" not in events

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
