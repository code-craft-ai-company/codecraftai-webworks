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
        When mj-button carries the disabled attribute the inner <button>
        reports aria-disabled="true" but is not natively disabled, so it
        stays focusable and discoverable (spec sections 10-11).

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = "<mj-button disabled>No</mj-button>"
    frame = _load_example(page, base_url, "mj-button", html)

    state = frame.evaluate(
        """() => {
            const inner = document.querySelector('mj-button').shadowRoot.querySelector('button');
            return { native: inner.disabled, aria: inner.getAttribute('aria-disabled') };
        }"""
    )
    assert state["native"] is False
    assert state["aria"] == "true"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_button_loading_keeps_focus(page, base_url):
    """
        Entering the loading state does not drop keyboard focus from the
        inner button, and activation is still blocked.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = '<mj-button variant="primary">Save</mj-button>'
    frame = _load_example(page, base_url, "mj-button", html)

    _collect_events(frame=frame, tag="mj-button", event_names=["mj-click"])

    state = frame.evaluate(
        """() => {
            const host = document.querySelector('mj-button');
            const inner = host.shadowRoot.querySelector('button');
            inner.focus();
            host.loading = true;
            inner.click();
            return {
                focused: host.shadowRoot.activeElement === inner,
                busy: inner.getAttribute('aria-busy'),
            };
        }"""
    )
    assert state["focused"] is True
    assert state["busy"] == "true"
    assert "mj-click" not in _get_events(frame=frame)

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_button_submit_sends_name_value_as_submitter(page, base_url):
    """
        A type="submit" mj-button submits its native form, is reported as the
        submitter, and contributes its own name/value to FormData; the other
        submit button's pair is not sent.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = (
        '<form id="f" onsubmit="return false">'
        '<input name="title" value="Report">'
        '<mj-button type="submit" name="op" value="save">Save</mj-button>'
        '<mj-button id="del" type="submit" name="op" value="delete">Delete</mj-button>'
        "</form>"
    )
    frame = _load_example(page, base_url, "mj-button", html)

    result = frame.evaluate(
        """() => {
            const form = document.getElementById('f');
            let seen = null;
            form.addEventListener('submit', (event) => {
                seen = {
                    submitter: event.submitter ? event.submitter.value : null,
                    data: Array.from(new FormData(form, event.submitter).entries()).map((e) => e.join('=')),
                };
            });
            document.getElementById('del').shadowRoot.querySelector('button').click();
            return { seen: seen, leftover: form.querySelectorAll('button').length };
        }"""
    )
    assert result["seen"] is not None
    assert result["seen"]["submitter"] == "delete"
    assert result["seen"]["data"] == ["title=Report", "op=delete"]
    assert result["leftover"] == 0

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_button_enter_in_text_field_submits_form(page, base_url):
    """
        Enter in a text input of a form with two text inputs submits the form
        through the default mj-button (HTML implicit submission), exactly once.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = (
        '<form id="f" onsubmit="return false">'
        '<input id="a" name="a"><input name="b">'
        '<mj-button type="submit" name="op" value="go">Go</mj-button>'
        "</form>"
    )
    frame = _load_example(page, base_url, "mj-button", html)

    frame.evaluate(
        """() => {
            window.__submits = [];
            const form = document.getElementById('f');
            form.addEventListener('submit', (event) => {
                window.__submits.push(event.submitter ? event.submitter.value : null);
            });
        }"""
    )
    frame.locator("#a").press("Enter")
    frame.wait_for_timeout(200)

    submits = frame.evaluate("() => window.__submits")
    assert submits == ["go"]

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_button_reset_and_fieldset_disabled(page, base_url):
    """
        type="reset" resets the native form; inside <fieldset disabled> the
        button neither fires mj-click nor submits.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = (
        '<form id="f" onsubmit="return false">'
        '<input id="a" name="a" value="initial">'
        '<mj-button id="r" type="reset">Reset</mj-button>'
        '<fieldset disabled><mj-button id="s" type="submit">Send</mj-button></fieldset>'
        "</form>"
    )
    frame = _load_example(page, base_url, "mj-button", html)

    result = frame.evaluate(
        """() => {
            const form = document.getElementById('f');
            const input = document.getElementById('a');
            let submits = 0;
            let clicks = 0;
            form.addEventListener('submit', () => { submits = submits + 1; });
            document.getElementById('s').addEventListener('mj-click', () => { clicks = clicks + 1; });
            input.value = 'changed';
            document.getElementById('r').shadowRoot.querySelector('button').click();
            document.getElementById('s').shadowRoot.querySelector('button').click();
            return { value: input.value, submits: submits, clicks: clicks };
        }"""
    )
    assert result["value"] == "initial"
    assert result["submits"] == 0
    assert result["clicks"] == 0

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_button_submit_request_event_contract(page, base_url):
    """
        Before acting on a native form the button dispatches a composed,
        bubbling, cancelable mj-submit-request with detail.submitter; a
        container that cancels it (as mj-form does) stops the native submit.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = (
        '<form id="f" onsubmit="return false">'
        '<div id="owner"><mj-button type="submit">Save</mj-button></div>'
        "</form>"
    )
    frame = _load_example(page, base_url, "mj-button", html)

    result = frame.evaluate(
        """() => {
            const button = document.querySelector('mj-button');
            let request = null;
            let submits = 0;
            document.getElementById('f').addEventListener('submit', () => { submits = submits + 1; });
            document.getElementById('owner').addEventListener('mj-submit-request', (event) => {
                request = {
                    composed: event.composed,
                    bubbles: event.bubbles,
                    cancelable: event.cancelable,
                    submitterIsButton: event.detail.submitter === button,
                };
                event.preventDefault();
            });
            button.click();
            return { request: request, submits: submits };
        }"""
    )
    assert result["request"] == {
        "composed": True,
        "bubbles": True,
        "cancelable": True,
        "submitterIsButton": True,
    }
    assert result["submits"] == 0

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_button_forwards_host_aria(page, base_url):
    """
        Host aria-label and ARIA state attributes reach the inner button, and
        later changes are mirrored.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = '<mj-button aria-label="Close" aria-expanded="false" aria-haspopup="menu">x</mj-button>'
    frame = _load_example(page, base_url, "mj-button", html)

    result = frame.evaluate(
        """() => {
            const host = document.querySelector('mj-button');
            const inner = host.shadowRoot.querySelector('button');
            const before = [inner.getAttribute('aria-label'), inner.getAttribute('aria-expanded'), inner.getAttribute('aria-haspopup')];
            host.setAttribute('aria-expanded', 'true');
            return { before: before, after: inner.getAttribute('aria-expanded') };
        }"""
    )
    assert result["before"] == ["Close", "false", "menu"]
    assert result["after"] == "true"

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
def test_mj_button_family_click_method_activates(page, base_url):
    """
        click() on the host of every button component activates its inner
        control, as it does for a native <button> (HTMLElement.click() used
        to dispatch a click at the host only, which did nothing), and a
        disabled host still ignores it.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = (
        '<mj-fab id="fab" label="Compose" style="position: static">+</mj-fab>'
        '<mj-toggle-button id="toggle">Bold</mj-toggle-button>'
        '<mj-disclosure-button id="disclosure" controls="panel">More</mj-disclosure-button>'
        '<div id="panel" hidden>Panel</div>'
        '<mj-favorite-button id="favorite"></mj-favorite-button>'
        '<mj-share-button id="share" force-menu share-url="https://example.test/a">Share</mj-share-button>'
        '<mj-download-button id="download" href="data:text/plain,x" filename="x.txt">Get</mj-download-button>'
        '<mj-toggle-button id="off" disabled>Off</mj-toggle-button>'
    )
    frame = _load_example(page, base_url, "mj-fab", html)
    frame.wait_for_function(
        "() => ['mj-toggle-button', 'mj-disclosure-button', 'mj-favorite-button', 'mj-share-button',"
        " 'mj-download-button'].every((tag) => customElements.get(tag) !== undefined)"
    )

    result = frame.evaluate(
        """() => {
            const seen = [];
            const watch = (id, type) => document.getElementById(id).addEventListener(type, (event) => {
                seen.push(id + ':' + type);
                if (type === 'mj-download-start') { event.preventDefault(); }
            });
            watch('fab', 'mj-click');
            watch('toggle', 'mj-pressed');
            watch('disclosure', 'mj-expanded');
            watch('favorite', 'mj-pressed');
            watch('share', 'mj-menu-open');
            watch('download', 'mj-download-start');
            watch('off', 'mj-pressed');
            for (const id of ['fab', 'toggle', 'disclosure', 'favorite', 'share', 'download', 'off']) {
                document.getElementById(id).click();
            }
            return {
                seen: seen,
                toggle: document.getElementById('toggle').pressed,
                panelHidden: document.getElementById('panel').hidden,
                favorite: document.getElementById('favorite').pressed,
                off: document.getElementById('off').pressed,
            };
        }"""
    )
    assert result["seen"] == [
        "fab:mj-click", "toggle:mj-pressed", "disclosure:mj-expanded", "favorite:mj-pressed",
        "share:mj-menu-open", "download:mj-download-start",
    ], result
    assert result["toggle"] is True, result
    assert result["panelHidden"] is False, result
    assert result["favorite"] is True, result
    assert result["off"] is False, result

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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_fab_speed_dial_menu_keyboard_and_select(page, base_url):
    """
        Opening a speed dial moves focus to the first action (role=menuitem),
        Arrow Down skips disabled actions, choosing an action emits mj-select
        and collapses the dial, and a property set to the current state
        emits no mj-expanded.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = (
        '<mj-fab label="Actions" speed-dial position="top-start">'
        '<span slot="icon">+</span>'
        '<button slot="speed-dial-item" value="one">One</button>'
        '<button slot="speed-dial-item" value="two" disabled>Two</button>'
        '<button slot="speed-dial-item" value="three">Three</button>'
        "</mj-fab>"
    )
    frame = _load_example(page, base_url, "mj-fab", html)

    result = frame.evaluate(
        """() => {
            const fab = document.querySelector('mj-fab');
            const events = [];
            fab.addEventListener('mj-expanded', (e) => events.push('expanded:' + e.detail.expanded));
            fab.addEventListener('mj-select', (e) => events.push('select:' + e.detail.value));
            fab.expanded = false;
            fab.shadowRoot.querySelector('button').click();
            const first = document.activeElement.value;
            document.activeElement.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowDown', bubbles: true, composed: true }));
            const second = document.activeElement.value;
            const roles = Array.from(fab.querySelectorAll('button')).map((b) => b.getAttribute('role'));
            const list = fab.shadowRoot.querySelector('.speed-dial-list').getBoundingClientRect();
            const trigger = fab.shadowRoot.querySelector('button').getBoundingClientRect();
            document.activeElement.click();
            return {
                first: first, second: second, roles: roles, events: events,
                expanded: fab.hasAttribute('expanded'), listBelow: list.top >= trigger.bottom,
            };
        }"""
    )
    assert result["first"] == "one"
    assert result["second"] == "three"
    assert result["roles"] == ["menuitem", "menuitem", "menuitem"]
    assert result["events"] == ["expanded:true", "select:three", "expanded:false"]
    assert result["expanded"] is False
    assert result["listBelow"] is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_fab_default_position_and_offsets(page, base_url):
    """
        A FAB without position is pinned to the bottom-end corner, and the
        offset-x / offset-y attributes move it.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = '<mj-fab label="Add" offset-y="80px"><span slot="icon">+</span></mj-fab>'
    frame = _load_example(page, base_url, "mj-fab", html)

    insets = frame.evaluate(
        """() => {
            const style = getComputedStyle(document.querySelector('mj-fab'));
            return [style.position, style.insetBlockEnd, style.insetInlineEnd];
        }"""
    )
    assert insets == ["fixed", "80px", "16px"]

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
def test_mj_toggle_button_form_value_follows_pressed_and_resets(page, base_url):
    """
        A named mj-toggle-button is form-associated with checkbox semantics:
        it submits its value only while pressed, and a form reset restores
        the pressed state it was connected with.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = (
        '<form id="f"><mj-toggle-button id="a" name="bold" value="yes" pressed>Bold</mj-toggle-button>'
        '<mj-toggle-button id="b" name="italic">Italic</mj-toggle-button></form>'
    )
    frame = _load_example(page, base_url, "mj-toggle-button", html)

    result = frame.evaluate("""() => {
        const form = document.getElementById("f");
        const entries = () => Array.from(new FormData(form).entries()).map((pair) => pair.join("="));
        const before = entries();
        document.getElementById("a").shadowRoot.querySelector("button").click();
        document.getElementById("b").shadowRoot.querySelector("button").click();
        const toggled = entries();
        form.reset();
        const afterReset = entries();
        return {
            associated: document.getElementById("a").form === form,
            before: before, toggled: toggled, afterReset: afterReset,
            pressedAfterReset: [document.getElementById("a").pressed, document.getElementById("b").pressed]
        };
    }""")

    assert result == {
        "associated": True,
        "before": ["bold=yes"],
        "toggled": ["italic=on"],
        "afterReset": ["bold=yes"],
        "pressedAfterReset": [True, False],
    }
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_toggle_button_change_fires_after_commit_and_not_when_vetoed(page, base_url):
    """
        The native change event fires after pressed is committed, and not at
        all when mj-change is cancelled.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = "<mj-toggle-button>Bold</mj-toggle-button>"
    frame = _load_example(page, base_url, "mj-toggle-button", html)

    result = frame.evaluate(
        """() => {
            const toggle = document.querySelector('mj-toggle-button');
            const inner = toggle.shadowRoot.querySelector('button');
            const log = [];
            toggle.addEventListener('change', () => log.push('change:' + toggle.pressed));
            inner.click();
            const veto = (e) => e.preventDefault();
            toggle.addEventListener('mj-change', veto);
            inner.click();
            return { log: log, pressed: toggle.pressed };
        }"""
    )
    assert result["log"] == ["change:true"]
    assert result["pressed"] is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_toggle_button_single_icon_shown_in_both_states(page, base_url):
    """
        A toggle button that fills only the icon-on slot shows that icon
        whether or not it is pressed.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = '<mj-toggle-button><span slot="icon-on">*</span>Star</mj-toggle-button>'
    frame = _load_example(page, base_url, "mj-toggle-button", html)

    visible = frame.evaluate(
        """() => {
            const toggle = document.querySelector('mj-toggle-button');
            const icon = toggle.shadowRoot.querySelector('.icon-on');
            const before = icon.hidden === false;
            toggle.pressed = true;
            const after = icon.hidden === false;
            return [before, after];
        }"""
    )
    assert visible == [True, True]

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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_disclosure_button_toggles_controlled_panel(page, base_url):
    """
        The panel named by controls is hidden while collapsed and shown when
        expanded, is linked through element reflection, and
        expanded="false" is read as collapsed.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = (
        '<mj-disclosure-button controls="panel" expanded="false">More</mj-disclosure-button>'
        '<div id="panel">Details</div>'
    )
    frame = _load_example(page, base_url, "mj-disclosure-button", html)

    result = frame.evaluate(
        """() => {
            const host = document.querySelector('mj-disclosure-button');
            const inner = host.shadowRoot.querySelector('button');
            const panel = document.getElementById('panel');
            const before = { hidden: panel.hidden, aria: inner.getAttribute('aria-expanded') };
            inner.click();
            const linked = inner.ariaControlsElements ? inner.ariaControlsElements[0] === panel : null;
            return { before: before, after: panel.hidden, linked: linked };
        }"""
    )
    assert result["before"] == {"hidden": True, "aria": "false"}
    assert result["after"] is False
    assert result["linked"] is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_disclosure_button_invalid_selector_does_not_throw(page, base_url):
    """
        A controls value that is neither an existing id nor a valid selector
        (for example "1panel") leaves the button working.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = '<mj-disclosure-button controls="1panel">More</mj-disclosure-button>'
    frame = _load_example(page, base_url, "mj-disclosure-button", html)

    expanded = frame.evaluate(
        """() => {
            const host = document.querySelector('mj-disclosure-button');
            host.shadowRoot.querySelector('button').click();
            return host.expanded;
        }"""
    )
    assert expanded is True

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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_copy_button_slotted_label_and_default_icon(page, base_url):
    """
        Slotted label text is rendered and names the button, and the
        built-in copy icon is shown when no icon is slotted.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = '<mj-copy-button value="npm i x">Copy install command</mj-copy-button>'
    frame = _load_example(page, base_url, "mj-copy-button", html)

    # innerText does not follow slots, so read what the label slot renders
    # (its assigned text) and check that the `label` text next to it is hidden.
    result = frame.evaluate(
        """() => {
            const host = document.querySelector('mj-copy-button');
            const inner = host.shadowRoot.querySelector('button');
            const slot = host.shadowRoot.querySelector('.label-slot');
            const fallback = host.shadowRoot.querySelector('.label-default');
            const icon = host.shadowRoot.querySelector('.icon-copy svg');
            const slotted = slot.assignedNodes().map((node) => node.textContent).join('').trim();
            return {
                text: slotted,
                slotShown: slot.checkVisibility(),
                fallbackShown: fallback.checkVisibility(),
                name: inner.getAttribute('aria-label'),
                iconWidth: icon ? icon.getBoundingClientRect().width : 0,
            };
        }"""
    )
    assert result["text"] == "Copy install command", result
    assert result["fallbackShown"] is False, result
    assert result["name"] == "Copy install command", result
    assert result["iconWidth"] > 0, result

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_copy_button_whitespace_content_shows_label(page, base_url):
    """
        Whitespace between the tags is not a label: the `label` text stays
        visible (it used to be slot fallback content, which the whitespace
        text node suppressed, leaving an empty button).

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = '<mj-copy-button value="#2563eb" label="Copy colour">\n   \n</mj-copy-button>'
    frame = _load_example(page, base_url, "mj-copy-button", html)

    result = frame.evaluate(
        """() => {
            const host = document.querySelector('mj-copy-button');
            const fallback = host.shadowRoot.querySelector('.label-default');
            return {
                shown: fallback.checkVisibility(),
                text: fallback.textContent,
                width: fallback.getBoundingClientRect().width,
                name: host.shadowRoot.querySelector('button').getAttribute('aria-label'),
            };
        }"""
    )
    assert result["shown"] is True, result
    assert result["text"] == "Copy colour", result
    assert result["width"] > 0, result
    assert result["name"] == "Copy colour", result

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_copy_button_for_reads_select_value(page, base_url):
    """
        for= pointing at a <select> copies its value, not its option text.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = (
        '<select id="src"><option value="v-1">Label One</option></select>'
        '<mj-copy-button for="src">Copy</mj-copy-button>'
    )
    frame = _load_example(page, base_url, "mj-copy-button", html)

    value = frame.evaluate("() => document.querySelector('mj-copy-button')._resolveValue()")
    assert value == "v-1"

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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_share_button_menu_keyboard_and_share_targets(page, base_url):
    """
        Opening the fallback menu focuses its first item, arrow keys rove
        through the items, and shareTargets are rendered as text items whose
        handler receives the shareData url.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = '<mj-share-button force-menu share-url="https://example.com/a">Share</mj-share-button>'
    frame = _load_example(page, base_url, "mj-share-button", html)

    result = frame.evaluate(
        """() => {
            const host = document.querySelector('mj-share-button');
            let handled = null;
            host.shareTargets = [{ label: '<b>Chat</b>', handler: (data) => { handled = data.url; } }];
            host.shareData = { url: 'https://override.example/x', title: 'T' };
            host.shadowRoot.querySelector('button.btn').click();
            const items = Array.from(host.shadowRoot.querySelectorAll('.menu-item'));
            const firstFocused = host.shadowRoot.activeElement === items[0];
            host.shadowRoot.activeElement.dispatchEvent(new KeyboardEvent('keydown', { key: 'End', bubbles: true, composed: true }));
            const lastFocused = host.shadowRoot.activeElement === items[items.length - 1];
            items[items.length - 1].click();
            return {
                labels: items.map((item) => item.textContent),
                firstFocused: firstFocused,
                lastFocused: lastFocused,
                handled: handled,
                bold: host.shadowRoot.querySelectorAll('b').length,
            };
        }"""
    )
    assert result["labels"] == ["Copy link", "Email", "<b>Chat</b>"]
    assert result["firstFocused"] is True
    assert result["lastFocused"] is True
    assert result["handled"] == "https://override.example/x"
    assert result["bold"] == 0

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_share_button_reopens_after_move(page, base_url):
    """
        A share button moved to another parent while its menu was open opens
        again with a single click.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = '<div id="a"><mj-share-button force-menu>Share</mj-share-button></div><div id="b"></div>'
    frame = _load_example(page, base_url, "mj-share-button", html)

    frame.evaluate(
        """() => {
            const host = document.querySelector('mj-share-button');
            host.shadowRoot.querySelector('button.btn').click();
            document.getElementById('b').appendChild(host);
        }"""
    )
    frame.wait_for_timeout(50)
    opened = frame.evaluate(
        """() => {
            const host = document.querySelector('mj-share-button');
            host.shadowRoot.querySelector('button.btn').click();
            return host.shadowRoot.querySelector('.fallback-menu').hidden === false;
        }"""
    )
    assert opened is True

    return


# ===========================================================================
# mj-download-button / mj-upload-button
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_download_button_rejects_javascript_href(page, base_url):
    """
        A javascript: href never reaches the inner anchor, while a normal URL
        does; loading sets aria-busy and aria-disabled on the anchor.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = (
        '<mj-download-button id="bad" href="javascript:alert(1)">Bad</mj-download-button>'
        '<mj-download-button id="good" href="/files/a.txt" filename="a.txt" loading>Good</mj-download-button>'
    )
    frame = _load_example(page, base_url, "mj-download-button", html)

    result = frame.evaluate(
        """() => {
            const bad = document.getElementById('bad').shadowRoot.querySelector('a');
            const good = document.getElementById('good').shadowRoot.querySelector('a');
            return {
                bad: bad.getAttribute('href'),
                good: good.getAttribute('href'),
                busy: good.getAttribute('aria-busy'),
                disabled: good.getAttribute('aria-disabled'),
            };
        }"""
    )
    assert result == {"bad": None, "good": "/files/a.txt", "busy": "true", "disabled": "true"}

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_upload_button_submits_only_accepted_files(page, base_url):
    """
        Rejected files are neither kept in files nor submitted, a
        single-file control keeps only the first dropped file, required makes
        an empty selection invalid, and form.reset() clears the selection.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = (
        '<form id="f"><mj-upload-button name="doc" accept=".txt" max-size="10" required>'
        "Upload</mj-upload-button></form>"
    )
    frame = _load_example(page, base_url, "mj-upload-button", html)

    result = frame.evaluate(
        """() => {
            const upload = document.querySelector('mj-upload-button');
            const form = document.getElementById('f');
            const file = (name, size) => new File([new Uint8Array(size)], name, { type: 'text/plain' });
            const drop = (files) => {
                const transfer = new DataTransfer();
                files.forEach((item) => transfer.items.add(item));
                upload.dispatchEvent(new DragEvent('drop', { bubbles: true, cancelable: true, dataTransfer: transfer }));
            };
            const entries = () => Array.from(new FormData(form).entries()).map(([key, value]) => key + '=' + value.name);
            const emptyValid = upload.checkValidity();
            drop([file('big.txt', 50)]);
            const afterRejected = { files: upload.files, data: entries() };
            drop([file('ok.txt', 5), file('second.txt', 5)]);
            const afterAccepted = { files: upload.files.map((item) => item.name), data: entries(), valid: upload.checkValidity() };
            form.reset();
            return { emptyValid: emptyValid, afterRejected: afterRejected, afterAccepted: afterAccepted, afterReset: entries() };
        }"""
    )
    assert result["emptyValid"] is False
    assert result["afterRejected"] == {"files": None, "data": []}
    assert result["afterAccepted"] == {"files": ["ok.txt"], "data": ["doc=ok.txt"], "valid": True}
    assert result["afterReset"] == []

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_upload_button_file_input_not_a_tab_stop(page, base_url):
    """
        The hidden native file input is out of the tab order and hidden from
        assistive technology.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = "<mj-upload-button>Upload</mj-upload-button>"
    frame = _load_example(page, base_url, "mj-upload-button", html)

    state = frame.evaluate(
        """() => {
            const input = document.querySelector('mj-upload-button').shadowRoot.querySelector('input');
            return [input.getAttribute('tabindex'), input.getAttribute('aria-hidden')];
        }"""
    )
    assert state == ["-1", "true"]

    return


_UPLOAD_DROP_HELPERS = """
    const file = (name, size, type) => new File([new Uint8Array(size)], name, { type: type || 'text/plain' });
    const drop = (upload, files) => {
        const transfer = new DataTransfer();
        files.forEach((item) => transfer.items.add(item));
        upload.dispatchEvent(new DragEvent('drop', { bubbles: true, cancelable: true, dataTransfer: transfer }));
    };
    const names = (upload) => upload.files === null ? null : upload.files.map((item) => item.name);
"""


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_upload_button_max_size_units_and_invalid_values(page, base_url):
    """
        max-size reads plain bytes and B / KB / MB / GB suffixes (1024-based,
        case-insensitive); an unreadable value is ignored (no limit) instead
        of rejecting every file.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = (
        '<mj-upload-button id="kb" max-size="2KB">KB</mj-upload-button>'
        '<mj-upload-button id="mb" max-size="1 mb">MB</mj-upload-button>'
        '<mj-upload-button id="bytes" max-size="100">Bytes</mj-upload-button>'
        '<mj-upload-button id="bad" max-size="abc">Bad</mj-upload-button>'
    )
    frame = _load_example(page, base_url, "mj-upload-button", html)

    result = frame.evaluate(
        "() => {" + _UPLOAD_DROP_HELPERS + """
            const byId = (id) => document.getElementById(id);
            const reasons = [];
            byId('kb').addEventListener('mj-upload-select', (event) => {
                event.detail.rejected.forEach((entry) => reasons.push(entry.reason));
            });
            drop(byId('kb'), [file('big.txt', 2049)]);
            drop(byId('kb'), [file('exact.txt', 2048)]);
            drop(byId('mb'), [file('half.txt', 512 * 1024)]);
            drop(byId('bytes'), [file('over.txt', 101)]);
            drop(byId('bad'), [file('any.txt', 5000)]);
            return {
                kb: names(byId('kb')), kbReasons: reasons, mb: names(byId('mb')),
                bytes: names(byId('bytes')), bad: names(byId('bad')),
            };
        }"""
    )
    assert result["kb"] == ["exact.txt"]
    assert result["kbReasons"] == ["max-size"]
    assert result["mb"] == ["half.txt"]
    assert result["bytes"] is None
    assert result["bad"] == ["any.txt"]

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_upload_button_all_rejected_keeps_selection(page, base_url):
    """
        A drop in which every file is rejected keeps the previous selection,
        form value, validity and summary; mj-upload-select still reports the
        rejection.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = (
        '<form id="f"><mj-upload-button name="doc" accept=".txt" required>'
        "Upload</mj-upload-button></form>"
    )
    frame = _load_example(page, base_url, "mj-upload-button", html)

    result = frame.evaluate(
        "() => {" + _UPLOAD_DROP_HELPERS + """
            const upload = document.querySelector('mj-upload-button');
            const form = document.getElementById('f');
            const details = [];
            upload.addEventListener('mj-upload-select', (event) => {
                details.push({ accepted: event.detail.accepted.length, rejected: event.detail.rejected.map((entry) => entry.reason) });
            });
            const entries = () => Array.from(new FormData(form).entries()).map(([key, value]) => key + '=' + value.name);
            drop(upload, [file('ok.txt', 5)]);
            drop(upload, [file('photo.png', 5, 'image/png')]);
            const summary = upload.shadowRoot.querySelector('.summary');
            return {
                files: names(upload), data: entries(), valid: upload.checkValidity(),
                summary: summary.hidden === true ? null : summary.textContent, details: details,
            };
        }"""
    )
    assert result["files"] == ["ok.txt"]
    assert result["data"] == ["doc=ok.txt"]
    assert result["valid"] is True
    assert result["summary"] == "ok.txt"
    assert result["details"] == [{"accepted": 1, "rejected": []}, {"accepted": 0, "rejected": ["accept"]}]

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_upload_button_host_events_once_and_no_aria_required(page, base_url):
    """
        A host click listener runs once per activation (the hidden input's
        click is not composed out), the inner input's native input event does
        not reach the host, and required does not put aria-required on the
        button (not allowed for the button role) while it still makes an
        empty selection invalid.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = '<mj-upload-button required name="doc">Upload</mj-upload-button>'
    frame = _load_example(page, base_url, "mj-upload-button", html)

    result = frame.evaluate(
        """() => {
            const upload = document.querySelector('mj-upload-button');
            const button = upload.shadowRoot.querySelector('button');
            const input = upload.shadowRoot.querySelector('input');
            let clicks = 0;
            let inputs = 0;
            upload.addEventListener('click', () => { clicks = clicks + 1; });
            upload.addEventListener('input', () => { inputs = inputs + 1; });
            let inputClicked = false;
            input.addEventListener('click', (event) => { inputClicked = true; event.preventDefault(); });
            button.click();
            input.dispatchEvent(new Event('input', { bubbles: true, composed: true }));
            return {
                clicks: clicks, inputs: inputs, inputClicked: inputClicked,
                ariaRequired: button.getAttribute('aria-required'),
                valueMissing: upload.validity.valueMissing,
            };
        }"""
    )
    assert result == {
        "clicks": 1, "inputs": 0, "inputClicked": True, "ariaRequired": None, "valueMissing": True,
    }

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_download_button_keeps_toolbar_tab_stop(page, base_url):
    """
        Inside mj-toolbar the roving tabindex the toolbar puts on the anchor
        survives attribute changes of the button (label, loading) and is put
        back after disabled is removed, so Tab still passes the toolbar in one
        step.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = (
        '<button id="before">Before</button>'
        '<mj-toolbar label="Actions"><mj-button id="first">First</mj-button>'
        '<mj-download-button id="dl" href="data:text/plain,x" filename="x.txt">Get</mj-download-button>'
        "</mj-toolbar>"
        '<button id="after">After</button>'
    )
    frame = _load_example(page, base_url, "mj-download-button", html)
    frame.wait_for_function(
        "() => document.getElementById('dl').shadowRoot.querySelector('a').getAttribute('tabindex') === '-1'",
        timeout=5000,
    )

    states = frame.evaluate(
        """() => {
            const button = document.getElementById('dl');
            const anchor = button.shadowRoot.querySelector('a');
            const seen = [];
            button.setAttribute('label', 'Get the file');
            seen.push(anchor.getAttribute('tabindex'));
            button.loading = true;
            seen.push(anchor.getAttribute('tabindex'));
            button.loading = false;
            button.disabled = true;
            seen.push(anchor.getAttribute('tabindex'));
            button.disabled = false;
            seen.push(anchor.getAttribute('tabindex'));
            return seen;
        }"""
    )
    assert states == ["-1", "-1", "-1", "-1"]

    frame.wait_for_timeout(200)
    frame.focus("#before")
    page.keyboard.press("Tab")
    first = frame.evaluate("() => document.activeElement.id")
    page.keyboard.press("Tab")
    second = frame.evaluate("() => document.activeElement.id")
    assert [first, second] == ["first", "after"]

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_download_button_without_href_is_focusable_link(page, base_url):
    """
        Without a usable href the anchor is still a link in the tab order
        (role link, tabindex 0) and Enter fires mj-download-start, so a
        listener-driven download works from the keyboard; once an href is set
        the native link takes over and the extra role and tabindex go away.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = (
        '<button id="before">Before</button>'
        '<mj-download-button id="gen" filename="report.json">Export</mj-download-button>'
    )
    frame = _load_example(page, base_url, "mj-download-button", html)

    frame.evaluate(
        """() => {
            window.__starts = [];
            document.getElementById('gen').addEventListener('mj-download-start', (event) => {
                event.preventDefault();
                window.__starts.push(event.detail);
            });
        }"""
    )
    frame.focus("#before")
    page.keyboard.press("Tab")
    focused = frame.evaluate("() => document.activeElement.id")
    page.keyboard.press("Enter")
    state = frame.evaluate(
        """() => {
            const button = document.getElementById('gen');
            const anchor = button.shadowRoot.querySelector('a');
            const before = { role: anchor.getAttribute('role'), tabindex: anchor.getAttribute('tabindex') };
            button.href = '/files/report.json';
            const after = { role: anchor.getAttribute('role'), tabindex: anchor.getAttribute('tabindex'), href: anchor.getAttribute('href') };
            return { before: before, after: after, starts: window.__starts };
        }"""
    )
    assert focused == "gen"
    assert state["starts"] == [{"href": "", "filename": "report.json"}]
    assert state["before"] == {"role": "link", "tabindex": "0"}
    assert state["after"] == {"role": None, "tabindex": None, "href": "/files/report.json"}

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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_favorite_button_rollback_after_commit_is_noop(page, base_url):
    """
        Once the persistence operation has finished (pending cleared),
        rollback() does not revert the committed state; a rollback before
        that does.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = "<mj-favorite-button>Favorite</mj-favorite-button>"
    frame = _load_example(page, base_url, "mj-favorite-button", html)

    frame.evaluate(
        """() => {
            const host = document.querySelector('mj-favorite-button');
            host.shadowRoot.querySelector('button').click();
            host.pending = true;
            host.pending = false;
        }"""
    )
    frame.wait_for_timeout(50)
    result = frame.evaluate(
        """() => {
            const host = document.querySelector('mj-favorite-button');
            host.rollback();
            const committed = host.pressed;
            host.shadowRoot.querySelector('button').click();
            host.rollback();
            return { committed: committed, rolledBack: host.pressed };
        }"""
    )
    assert result["committed"] is True
    assert result["rolledBack"] is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_mj_favorite_button_count_and_icons(page, base_url):
    """
        A non-numeric count reads as 0 (no NaN in the name), large counts use
        compact notation, nothing is announced at first render, and the
        flavor supplies a default icon.

        :param page: The Playwright page fixture.
        :param base_url: The base URL fixture.
    """

    html = '<mj-favorite-button flavor="like" count="abc">Like</mj-favorite-button>'
    frame = _load_example(page, base_url, "mj-favorite-button", html)

    result = frame.evaluate(
        """() => {
            const host = document.querySelector('mj-favorite-button');
            const inner = host.shadowRoot.querySelector('button');
            const before = inner.getAttribute('aria-label');
            const liveAtLoad = Array.from(document.querySelectorAll('.mj-live-region')).map((r) => r.textContent).join('');
            host.count = 1500;
            const icon = host.shadowRoot.querySelector('.icon-off svg');
            return {
                before: before,
                liveAtLoad: liveAtLoad,
                compact: host.shadowRoot.querySelector('.count').textContent,
                iconWidth: icon ? icon.getBoundingClientRect().width : 0,
            };
        }"""
    )
    assert result["before"] == "Like (0)"
    assert result["liveAtLoad"] == ""
    assert result["compact"] == "1.5K"
    assert result["iconWidth"] > 0

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
