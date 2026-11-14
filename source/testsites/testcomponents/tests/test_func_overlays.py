"""
    .. module:: testcomponents.tests.test_func_overlays

    Functional Playwright tests for the 'overlays' component group.

    Covers: mj-dialog, mj-popover, mj-drawer, mj-lightbox, mj-overlay,
    mj-toast-region, mj-notification-center, mj-context-menu,
    mj-command-palette, mj-tour.

    Each test navigates to the component playground page, acquires the
    preview iframe, and exercises the real open/close API derived from
    the component JS source.
"""

import ccai.testbase as testbase

from testcomponents.harness.browsers import expect
from testcomponents.harness.factories import create_page


_GROUP = "overlays"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _preview_frame(page):
    """
        Return the Frame object for the playground preview iframe.

        :param page: The Playwright Page.

        :returns: The Frame inside the playground-preview iframe.
    """

    handle = page.wait_for_selector("[data-testid=playground-preview]")
    frame = handle.content_frame()
    return frame


def _open_component(page, base_url, tag):
    """
        Navigate to a component playground page and wait for the custom
        element to register inside the preview iframe.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
        :param tag: The component tag name.

        :returns: The preview Frame with the library loaded.
    """

    page.goto(base_url + f"/components/{_GROUP}/{tag}")
    frame = _preview_frame(page)
    frame.wait_for_function(
        "tag => customElements.get(tag) !== undefined",
        arg=tag,
        timeout=15000,
    )
    # The example's script runs as a module after the elements upgraded; wait
    # for it so it cannot overwrite what a test sets up (items, steps, ...).
    frame.wait_for_function(
        "() => window.mjSandbox !== undefined && window.mjSandbox.ready === true",
        timeout=15000,
    )
    return frame


def _open_example(page, base_url, tag, key):
    """
        Navigate to one gallery example of a component page and wait until
        its script has run in the preview iframe.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
        :param tag: The component tag name.
        :param key: The example key (the `?example=` deep link).

        :returns: The preview Frame with the example ready.
    """

    page.goto(base_url + f"/components/{_GROUP}/{tag}?example={key}")
    frame = _preview_frame(page)
    frame.wait_for_function(
        "tag => customElements.get(tag) !== undefined",
        arg=tag,
        timeout=15000,
    )
    frame.wait_for_function(
        "() => window.mjSandbox !== undefined && window.mjSandbox.ready === true",
        timeout=15000,
    )
    return frame


def _collect_events(frame, tag, event_names):
    """
        Install a listener on the first instance of ``tag`` that records
        each fired event name into ``window.__mjevents``.

        :param frame: The preview Frame.
        :param tag: The component tag name.
        :param event_names: Iterable of event name strings to record.
    """

    names_js = ", ".join(f'"{n}"' for n in event_names)
    frame.evaluate(
        f"""() => {{
            window.__mjevents = [];
            const el = document.querySelector('{tag}');
            [{names_js}].forEach(n =>
                el.addEventListener(n, () => window.__mjevents.push(n)));
        }}"""
    )
    return


def _get_events(frame):
    """
        Return the list of recorded event names from the frame.

        :param frame: The preview Frame.

        :returns: A list of event name strings.
    """

    events = frame.evaluate("() => window.__mjevents")
    return events


# ---------------------------------------------------------------------------
# mj-dialog
# ---------------------------------------------------------------------------

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_dialog_opens_and_has_role(page, base_url):
    """
        mj-dialog: the component renders a dialog with role=dialog and
        aria-modal=true when the open attribute is present.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-dialog")

    dialog_el = frame.locator("mj-dialog dialog").first
    expect(dialog_el).to_be_visible(timeout=5000)

    role = frame.evaluate(
        "() => document.querySelector('mj-dialog').shadowRoot"
        ".querySelector('dialog').getAttribute('role')"
    )
    assert role == "dialog"

    aria_modal = frame.evaluate(
        "() => document.querySelector('mj-dialog').shadowRoot"
        ".querySelector('dialog').getAttribute('aria-modal')"
    )
    assert aria_modal == "true"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_dialog_close_button_dismisses(page, base_url):
    """
        mj-dialog: clicking the built-in close button removes the open
        attribute and hides the native dialog element.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-dialog")

    _collect_events(frame=frame, tag="mj-dialog", event_names=["mj-dialog-close"])

    # Shadow DOM buttons inside fixed overlays are outside the iframe
    # viewport; click via JS to avoid the "outside viewport" restriction.
    frame.evaluate(
        "() => document.querySelector('mj-dialog').shadowRoot"
        ".querySelector('[data-action=\"close\"]').click()"
    )

    is_open = frame.evaluate(
        "() => document.querySelector('mj-dialog').hasAttribute('open')"
    )
    assert is_open is False

    events = _get_events(frame=frame)
    assert "mj-dialog-close" in events

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_dialog_escape_key_dismisses(page, base_url):
    """
        mj-dialog: dispatching Escape on the native dialog element closes
        the dialog and fires the mj-dialog-close event.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-dialog")

    _collect_events(frame=frame, tag="mj-dialog", event_names=["mj-dialog-close"])

    # The dialog is fixed-positioned inside the iframe; dispatch the
    # Escape event directly via JS to bypass the viewport restriction.
    frame.evaluate(
        "() => {"
        "  const dialog = document.querySelector('mj-dialog').shadowRoot"
        "    .querySelector('dialog');"
        "  dialog.dispatchEvent(new KeyboardEvent('keydown',"
        "    { key: 'Escape', bubbles: true, cancelable: true }));"
        "}"
    )

    is_open = frame.evaluate(
        "() => document.querySelector('mj-dialog').hasAttribute('open')"
    )
    assert is_open is False

    events = _get_events(frame=frame)
    assert "mj-dialog-close" in events

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_dialog_show_modal_api(page, base_url):
    """
        mj-dialog: calling showModal() on a closed dialog opens it and
        fires the mj-dialog-open event.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-dialog")

    # Close the dialog first so we can reopen it.
    frame.evaluate("() => document.querySelector('mj-dialog').close()")

    _collect_events(frame=frame, tag="mj-dialog", event_names=["mj-dialog-open"])

    frame.evaluate("() => document.querySelector('mj-dialog').showModal()")

    is_open = frame.evaluate(
        "() => document.querySelector('mj-dialog').hasAttribute('open')"
    )
    assert is_open is True

    events = _get_events(frame=frame)
    assert "mj-dialog-open" in events

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_dialog_close_api(page, base_url):
    """
        mj-dialog: calling close() programmatically removes the open
        attribute and fires mj-dialog-close.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-dialog")

    _collect_events(frame=frame, tag="mj-dialog", event_names=["mj-dialog-close"])

    frame.evaluate("() => document.querySelector('mj-dialog').close()")

    is_open = frame.evaluate(
        "() => document.querySelector('mj-dialog').hasAttribute('open')"
    )
    assert is_open is False

    events = _get_events(frame=frame)
    assert "mj-dialog-close" in events

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_dialog_closed_is_not_rendered(page, base_url):
    """
        mj-dialog: a closed dialog takes no space, does not intercept
        clicks and its buttons are not reachable.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-dialog")

    state = frame.evaluate(
        "async () => {"
        "  const d = document.querySelector('mj-dialog');"
        "  d.close();"
        "  await new Promise(r => setTimeout(r, 300));"
        "  const dialog = d.shadowRoot.querySelector('dialog');"
        "  const rect = dialog.getBoundingClientRect();"
        "  const hit = document.elementFromPoint(window.innerWidth / 2, window.innerHeight / 2);"
        "  return {"
        "    display: getComputedStyle(dialog).display,"
        "    width: rect.width, height: rect.height,"
        "    hitIsDialog: hit === d || (hit !== null && d.contains(hit))"
        "  };"
        "}"
    )

    assert state["display"] == "none"
    assert state["width"] == 0 and state["height"] == 0
    assert state["hitIsDialog"] is False

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_dialog_backdrop_click_closes(page, base_url):
    """
        mj-dialog: clicking the backdrop of a modal dialog closes it with
        reason 'backdrop' and emits mj-dialog-cancel; close-on-backdrop
        false keeps it open.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-dialog")

    _collect_events(frame=frame, tag="mj-dialog", event_names=["mj-dialog-close", "mj-dialog-cancel"])

    frame.wait_for_function(
        "() => document.querySelector('mj-dialog').shadowRoot.querySelector('dialog').open",
        timeout=5000,
    )

    # Press and release in the top-left corner: outside the dialog box,
    # on the native ::backdrop.
    frame.locator("mj-dialog dialog").first.click(position={"x": -5, "y": -5}, force=True)
    frame.wait_for_function(
        "() => document.querySelector('mj-dialog').hasAttribute('open') === false",
        timeout=5000,
    )

    events = _get_events(frame=frame)
    assert events == ["mj-dialog-cancel", "mj-dialog-close"]

    frame.evaluate(
        "() => { const d = document.querySelector('mj-dialog');"
        " d.setAttribute('close-on-backdrop', 'false'); d.showModal(); }"
    )
    frame.wait_for_function(
        "() => document.querySelector('mj-dialog').shadowRoot.querySelector('dialog').open",
        timeout=5000,
    )
    frame.locator("mj-dialog dialog").first.click(position={"x": -5, "y": -5}, force=True)
    frame.wait_for_timeout(200)
    assert frame.evaluate("() => document.querySelector('mj-dialog').hasAttribute('open')") is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_dialog_escape_closes_nested_popup_first(page, base_url):
    """
        mj-dialog: with a popover open inside the dialog, the first Escape
        closes only the popover and the second closes the dialog. The
        popover is placed next to its trigger (in the top layer), not offset
        by the dialog.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-dialog")

    frame.evaluate(
        "() => {"
        "  document.body.innerHTML = '<mj-dialog id=\"d\" label=\"Form\">"
        "<mj-popover id=\"p\" placement=\"bottom-start\"><button slot=\"trigger\" id=\"t\">More</button>"
        "<p>Details</p><button id=\"inside\">ok</button></mj-popover></mj-dialog>';"
        "}"
    )
    frame.wait_for_function("() => document.getElementById('d').nativeDialog !== null", timeout=5000)
    frame.evaluate("() => document.getElementById('d').showModal()")
    frame.evaluate("() => document.getElementById('t').click()")
    frame.wait_for_function("() => document.getElementById('p').hasAttribute('open')", timeout=5000)

    # Next to the trigger (below it, or above it after a flip) once the
    # dialog's entry animation has ended, and on top of the dialog.
    geometry_js = (
        "() => {"
        "  const p = document.getElementById('p');"
        "  const popup = p.popupEl.getBoundingClientRect();"
        "  const trigger = document.getElementById('t').getBoundingClientRect();"
        "  const below = Math.round(popup.top - trigger.bottom);"
        "  const above = Math.round(trigger.top - popup.bottom);"
        "  const hit = document.elementFromPoint(popup.left + popup.width / 2, popup.top + popup.height / 2);"
        "  return { dx: Math.round(popup.left - trigger.left),"
        "           gap: below >= 0 ? below : above,"
        "           visible: hit !== null && (hit === p || p.contains(hit)) };"
        "}"
    )
    frame.wait_for_function(
        "() => { const g = (" + geometry_js + ")();"
        " return Math.abs(g.dx) <= 1 && g.gap >= 0 && g.gap <= 12 && g.visible === true; }",
        timeout=5000,
    )
    geometry = frame.evaluate(geometry_js)
    assert abs(geometry["dx"]) <= 1
    assert 0 <= geometry["gap"] <= 12
    assert geometry["visible"] is True

    frame.locator("#inside").press("Escape")
    frame.wait_for_timeout(150)
    assert frame.evaluate("() => document.getElementById('p').hasAttribute('open')") is False
    assert frame.evaluate("() => document.getElementById('d').hasAttribute('open')") is True

    frame.locator("#t").press("Escape")
    frame.wait_for_function("() => document.getElementById('d').hasAttribute('open') === false", timeout=5000)

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_dialog_builtin_buttons_report_confirm_and_cancel_reasons(page, base_url):
    """
        mj-dialog: the built-in Confirm button closes with reason `confirm`
        and the built-in Cancel button with reason `cancel` (also on
        mj-dialog-cancel); only close() reports `api`. Both used to report
        `api`.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_example(page, base_url, tag="mj-dialog", key="variants")

    log = frame.evaluate(
        """async () => {
            const wait = (ms) => new Promise((done) => setTimeout(done, ms))
            const dialog = document.getElementById("confirm-dialog")
            const log = []
            for (const name of ["mj-dialog-before-close", "mj-dialog-cancel", "mj-dialog-close"]) {
              dialog.addEventListener(name, (event) => log.push(name + ":" + event.detail.reason))
            }
            dialog.showModal()
            await wait(50)
            dialog.shadowRoot.querySelector("[data-action=confirm]").click()
            await wait(50)
            dialog.showModal()
            await wait(50)
            dialog.shadowRoot.querySelector("[data-action=cancel]").click()
            await wait(50)
            dialog.showModal()
            await wait(50)
            dialog.close()
            return log
        }"""
    )

    assert log == [
        "mj-dialog-before-close:confirm", "mj-dialog-close:confirm",
        "mj-dialog-before-close:cancel", "mj-dialog-cancel:cancel", "mj-dialog-close:cancel",
        "mj-dialog-before-close:api", "mj-dialog-close:api",
    ], log

    return


# ---------------------------------------------------------------------------
# mj-popover
# ---------------------------------------------------------------------------

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_popover_visible_when_open(page, base_url):
    """
        mj-popover: the popup panel is visible when the open attribute is
        present (catalog example ships with open).

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-popover")

    popup = frame.locator("mj-popover [part=popup]").first
    expect(popup).to_be_visible(timeout=5000)

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_popover_close_button_dismisses(page, base_url):
    """
        mj-popover: clicking the close button removes the open attribute
        and fires mj-popover-close with reason `close-button`.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-popover")

    _collect_events(
        frame=frame,
        tag="mj-popover",
        event_names=["mj-popover-close"],
    )
    frame.evaluate(
        "() => { window.__reasons = [];"
        " document.querySelector('mj-popover').addEventListener('mj-popover-close',"
        " (event) => window.__reasons.push(event.detail.reason)); }"
    )

    # The popup is fixed-positioned inside the iframe and may be outside
    # the visible viewport; click via JS to bypass the viewport check.
    frame.evaluate(
        "() => document.querySelector('mj-popover').shadowRoot"
        ".querySelector('[data-action=\"close\"]').click()"
    )

    is_open = frame.evaluate(
        "() => document.querySelector('mj-popover').hasAttribute('open')"
    )
    assert is_open is False

    events = _get_events(frame=frame)
    assert "mj-popover-close" in events

    # The built-in close button has its own reason (it used to report `trigger`).
    reasons = frame.evaluate("() => window.__reasons")
    assert reasons == ["close-button"], reasons

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_popover_escape_key_closes(page, base_url):
    """
        mj-popover: dispatching Escape on the popup div closes the popover.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-popover")

    _collect_events(
        frame=frame,
        tag="mj-popover",
        event_names=["mj-popover-close"],
    )

    # The popup is fixed-positioned inside the iframe; dispatch Escape
    # directly via JS to bypass the viewport restriction.
    frame.evaluate(
        "() => {"
        "  const popup = document.querySelector('mj-popover').shadowRoot"
        "    .querySelector('.popup');"
        "  popup.dispatchEvent(new KeyboardEvent('keydown',"
        "    { key: 'Escape', bubbles: true, cancelable: true }));"
        "}"
    )

    is_open = frame.evaluate(
        "() => document.querySelector('mj-popover').hasAttribute('open')"
    )
    assert is_open is False

    events = _get_events(frame=frame)
    assert "mj-popover-close" in events

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_popover_show_and_close_api(page, base_url):
    """
        mj-popover: calling show() opens the popover; calling close()
        dismisses it; the open event fires on show().

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-popover")

    # Close first.
    frame.evaluate("() => document.querySelector('mj-popover').close()")

    _collect_events(
        frame=frame,
        tag="mj-popover",
        event_names=["mj-popover-open", "mj-popover-close"],
    )

    frame.evaluate("() => document.querySelector('mj-popover').show()")
    assert frame.evaluate(
        "() => document.querySelector('mj-popover').hasAttribute('open')"
    ) is True

    frame.evaluate("() => document.querySelector('mj-popover').close()")
    assert frame.evaluate(
        "() => document.querySelector('mj-popover').hasAttribute('open')"
    ) is False

    events = _get_events(frame=frame)
    assert "mj-popover-open" in events
    assert "mj-popover-close" in events

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_popover_opens_once_and_does_not_leak_dismiss(page, base_url):
    """
        mj-popover: opening from the trigger fires the open events once,
        and after the popover is closed an outside click emits nothing.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-popover")

    frame.evaluate("() => document.querySelector('mj-popover').close()")
    _collect_events(
        frame=frame,
        tag="mj-popover",
        event_names=["mj-popover-before-open", "mj-popover-open", "mj-popover-close"],
    )

    frame.evaluate("() => document.querySelector('mj-popover [slot=trigger]').click()")
    frame.evaluate("() => document.querySelector('mj-popover').close()")
    frame.evaluate(
        "() => { document.body.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, composed: true }));"
        " document.body.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, composed: true })); }"
    )

    events = _get_events(frame=frame)
    assert events == ["mj-popover-before-open", "mj-popover-open", "mj-popover-close"]

    return


# ---------------------------------------------------------------------------
# mj-drawer
# ---------------------------------------------------------------------------

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_drawer_panel_visible_when_open(page, base_url):
    """
        mj-drawer: the panel element is present and the host has the open
        attribute when the example loads.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-drawer")

    is_open = frame.evaluate(
        "() => document.querySelector('mj-drawer').hasAttribute('open')"
    )
    assert is_open is True

    panel = frame.locator("mj-drawer [part=panel]").first
    expect(panel).to_be_attached(timeout=5000)

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_drawer_has_dialog_role(page, base_url):
    """
        mj-drawer: in modal mode the panel has role=dialog and aria-modal=true.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-drawer")

    role = frame.evaluate(
        "() => document.querySelector('mj-drawer').shadowRoot"
        ".querySelector('.panel').getAttribute('role')"
    )
    assert role == "dialog"

    aria_modal = frame.evaluate(
        "() => document.querySelector('mj-drawer').shadowRoot"
        ".querySelector('.panel').getAttribute('aria-modal')"
    )
    assert aria_modal == "true"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_drawer_close_button_dismisses(page, base_url):
    """
        mj-drawer: clicking the built-in close button removes the open
        attribute and fires mj-drawer-close.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-drawer")

    _collect_events(frame=frame, tag="mj-drawer", event_names=["mj-drawer-close"])

    # The drawer panel is fixed-positioned inside the iframe and may be
    # outside the visible viewport; click via JS to bypass the restriction.
    frame.evaluate(
        "() => document.querySelector('mj-drawer').shadowRoot"
        ".querySelector('.close-btn').click()"
    )

    is_open = frame.evaluate(
        "() => document.querySelector('mj-drawer').hasAttribute('open')"
    )
    assert is_open is False

    events = _get_events(frame=frame)
    assert "mj-drawer-close" in events

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_drawer_escape_key_dismisses(page, base_url):
    """
        mj-drawer: dispatching Escape on the panel element closes the drawer.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-drawer")

    _collect_events(frame=frame, tag="mj-drawer", event_names=["mj-drawer-close"])

    # Dispatch a keydown event directly on the panel to avoid viewport issues.
    frame.evaluate(
        "() => {"
        "  const panel = document.querySelector('mj-drawer').shadowRoot"
        "    .querySelector('.panel');"
        "  panel.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));"
        "}"
    )

    is_open = frame.evaluate(
        "() => document.querySelector('mj-drawer').hasAttribute('open')"
    )
    assert is_open is False

    events = _get_events(frame=frame)
    assert "mj-drawer-close" in events

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_drawer_show_and_close_api(page, base_url):
    """
        mj-drawer: calling show() opens the drawer; close() dismisses it
        and fires the event.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-drawer")

    frame.evaluate("() => document.querySelector('mj-drawer').close()")
    assert frame.evaluate(
        "() => document.querySelector('mj-drawer').hasAttribute('open')"
    ) is False

    _collect_events(frame=frame, tag="mj-drawer", event_names=["mj-drawer-open"])

    frame.evaluate("() => document.querySelector('mj-drawer').show()")
    assert frame.evaluate(
        "() => document.querySelector('mj-drawer').hasAttribute('open')"
    ) is True

    events = _get_events(frame=frame)
    assert "mj-drawer-open" in events

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_drawer_closed_is_hidden_and_inert(page, base_url):
    """
        mj-drawer: a closed drawer is hidden and inert (its content cannot
        be focused), including in a right-to-left document; an open modal
        drawer makes the page behind it inert.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-drawer")

    state = frame.evaluate(
        "async () => {"
        "  document.documentElement.dir = 'rtl';"
        "  document.body.innerHTML = '<button id=\"bg\">bg</button>"
        "<mj-drawer id=\"dr\" label=\"Filters\"><a id=\"lnk\" href=\"#x\">Link</a></mj-drawer>';"
        "  await new Promise(r => setTimeout(r, 400));"
        "  const dr = document.getElementById('dr');"
        "  const panel = dr.panelEl;"
        "  const rect = panel.getBoundingClientRect();"
        "  document.getElementById('lnk').focus();"
        "  const closed = {"
        "    visibility: getComputedStyle(panel).visibility,"
        "    inert: panel.inert,"
        "    onScreen: rect.right > 0 && rect.left < window.innerWidth,"
        "    linkFocused: document.activeElement.id === 'lnk'"
        "  };"
        "  dr.show();"
        "  await new Promise(r => setTimeout(r, 400));"
        "  const open = { inert: panel.inert, bgInert: document.getElementById('bg').inert };"
        "  dr.close();"
        "  await new Promise(r => setTimeout(r, 50));"
        "  const after = { bgInert: document.getElementById('bg').inert };"
        "  document.documentElement.dir = '';"
        "  return { closed, open, after };"
        "}"
    )

    assert state["closed"] == {"visibility": "hidden", "inert": True, "onScreen": False, "linkFocused": False}
    assert state["open"] == {"inert": False, "bgInert": True}
    assert state["after"] == {"bgInert": False}

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_drawer_close_events_fire_once(page, base_url):
    """
        mj-drawer: each close fires mj-drawer-before-close and
        mj-drawer-close exactly once with the real reason; closing a closed
        drawer fires nothing.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-drawer")

    frame.evaluate(
        "() => {"
        "  window.__reasons = [];"
        "  const dr = document.querySelector('mj-drawer');"
        "  ['mj-drawer-before-close', 'mj-drawer-close'].forEach(n =>"
        "    dr.addEventListener(n, e => window.__reasons.push(n + ':' + e.detail.reason)));"
        "  dr.shadowRoot.querySelector('.close-btn').click();"
        "  dr.close();"
        "}"
    )

    reasons = frame.evaluate("() => window.__reasons")
    assert reasons == ["mj-drawer-before-close:close-button", "mj-drawer-close:close-button"]

    return


# ---------------------------------------------------------------------------
# mj-lightbox
# ---------------------------------------------------------------------------

def _lightbox_open_with_items(frame):
    """
        Assign items to the mj-lightbox and open it.

        The catalog example sets items via an inline <script>, but that
        script may not execute inside the playground iframe renderer.
        We assign items and call show() directly from the test.

        :param frame: The preview Frame.
    """

    frame.evaluate(
        "() => {"
        "  const lb = document.querySelector('mj-lightbox');"
        "  lb.items = ["
        "    { src: 'https://picsum.photos/seed/a/400/300', alt: 'Image 1', caption: 'Caption 1' },"
        "    { src: 'https://picsum.photos/seed/b/400/300', alt: 'Image 2', caption: 'Caption 2' }"
        "  ];"
        "  lb.show(0);"
        "}"
    )
    frame.wait_for_function(
        "() => document.querySelector('mj-lightbox').hasAttribute('open')",
        timeout=5000,
    )
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_lightbox_opens_with_open_attribute(page, base_url):
    """
        mj-lightbox: after assigning items and calling show(0) the
        backdrop is visible and the host has the open attribute.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-lightbox")

    _lightbox_open_with_items(frame=frame)

    is_open = frame.evaluate(
        "() => document.querySelector('mj-lightbox').hasAttribute('open')"
    )
    assert is_open is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_lightbox_has_dialog_role(page, base_url):
    """
        mj-lightbox: the backdrop div carries role=dialog and aria-modal=true.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-lightbox")

    _lightbox_open_with_items(frame=frame)

    role = frame.evaluate(
        "() => document.querySelector('mj-lightbox').shadowRoot"
        ".querySelector('.lb-backdrop').getAttribute('role')"
    )
    assert role == "dialog"

    aria_modal = frame.evaluate(
        "() => document.querySelector('mj-lightbox').shadowRoot"
        ".querySelector('.lb-backdrop').getAttribute('aria-modal')"
    )
    assert aria_modal == "true"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_lightbox_close_button_dismisses(page, base_url):
    """
        mj-lightbox: clicking the close button removes the open attribute
        and fires mj-lightbox-close.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-lightbox")

    _lightbox_open_with_items(frame=frame)

    _collect_events(frame=frame, tag="mj-lightbox", event_names=["mj-lightbox-close"])

    # The lightbox backdrop is fixed-positioned; click via JS to bypass viewport.
    frame.evaluate(
        "() => document.querySelector('mj-lightbox').shadowRoot"
        ".querySelector('[data-action=\"close\"]').click()"
    )

    is_open = frame.evaluate(
        "() => document.querySelector('mj-lightbox').hasAttribute('open')"
    )
    assert is_open is False

    events = _get_events(frame=frame)
    assert "mj-lightbox-close" in events

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_lightbox_escape_key_dismisses(page, base_url):
    """
        mj-lightbox: dispatching Escape on the backdrop closes the lightbox.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-lightbox")

    _lightbox_open_with_items(frame=frame)

    _collect_events(frame=frame, tag="mj-lightbox", event_names=["mj-lightbox-close"])

    # The backdrop is fixed-positioned; dispatch Escape directly via JS.
    frame.evaluate(
        "() => {"
        "  const backdrop = document.querySelector('mj-lightbox').shadowRoot"
        "    .querySelector('.lb-backdrop');"
        "  backdrop.dispatchEvent(new KeyboardEvent('keydown',"
        "    { key: 'Escape', bubbles: true, cancelable: true }));"
        "}"
    )

    is_open = frame.evaluate(
        "() => document.querySelector('mj-lightbox').hasAttribute('open')"
    )
    assert is_open is False

    events = _get_events(frame=frame)
    assert "mj-lightbox-close" in events

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_lightbox_navigate_next_fires_change(page, base_url):
    """
        mj-lightbox: clicking the next button navigates to item 1 and
        fires mj-lightbox-change.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-lightbox")

    _lightbox_open_with_items(frame=frame)

    _collect_events(frame=frame, tag="mj-lightbox", event_names=["mj-lightbox-change"])

    # Buttons inside the fixed-position lightbox backdrop are outside the
    # iframe's visible viewport; use JS click to bypass the restriction.
    frame.evaluate(
        "() => document.querySelector('mj-lightbox').shadowRoot"
        ".querySelector('[data-action=\"next\"]').click()"
    )

    events = _get_events(frame=frame)
    assert "mj-lightbox-change" in events

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_lightbox_items_assigned_before_upgrade_render(page, base_url):
    """
        mj-lightbox: items assigned by the example's inline script before
        the element upgraded are kept, so the declaratively opened viewer
        shows the first item; closing fires mj-lightbox-close once.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-lightbox")

    frame.wait_for_function(
        "() => document.querySelector('mj-lightbox').shadowRoot"
        ".querySelector('.lb-backdrop').hasAttribute('data-active')",
        timeout=5000,
    )

    state = frame.evaluate(
        "() => {"
        "  const lb = document.querySelector('mj-lightbox');"
        "  window.__closes = [];"
        "  lb.addEventListener('mj-lightbox-close', e => window.__closes.push(e.detail.reason));"
        "  const counter = lb.shadowRoot.querySelector('.counter').textContent;"
        "  lb.shadowRoot.querySelector('[data-action=\"close\"]').click();"
        "  return { items: lb.items.length, counter: counter, open: lb.hasAttribute('open') };"
        "}"
    )

    assert state["items"] == 2
    assert state["counter"] == "1 of 2"
    assert state["open"] is False
    assert frame.evaluate("() => window.__closes") == ["close-button"]

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_lightbox_backdrop_click_closes(page, base_url):
    """
        mj-lightbox: clicking the dark area around the image closes the
        viewer with reason 'backdrop'.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-lightbox")

    _lightbox_open_with_items(frame=frame)

    frame.evaluate(
        "() => {"
        "  window.__closes = [];"
        "  const lb = document.querySelector('mj-lightbox');"
        "  lb.addEventListener('mj-lightbox-close', e => window.__closes.push(e.detail.reason));"
        "}"
    )

    # The left edge of the viewport, beside the image and the nav button.
    frame.locator("mj-lightbox .viewport").click(position={"x": 4, "y": 4}, force=True)
    frame.wait_for_function(
        "() => document.querySelector('mj-lightbox').hasAttribute('open') === false",
        timeout=5000,
    )
    assert frame.evaluate("() => window.__closes") == ["backdrop"]

    return


# ---------------------------------------------------------------------------
# mj-overlay
# ---------------------------------------------------------------------------

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_overlay_visible_attribute_activates_backdrop(page, base_url):
    """
        mj-overlay: the backdrop div is present when the visible attribute
        is set on the host.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-overlay")

    is_visible = frame.evaluate(
        "() => document.querySelector('mj-overlay').hasAttribute('visible')"
    )
    assert is_visible is True

    backdrop = frame.locator("mj-overlay [part=backdrop]").first
    expect(backdrop).to_be_attached(timeout=5000)

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_overlay_show_and_hide_api(page, base_url):
    """
        mj-overlay: show() sets the visible attribute; hide() removes it,
        and each transition fires the corresponding event.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-overlay")

    _collect_events(
        frame=frame,
        tag="mj-overlay",
        event_names=["mj-overlay-visible", "mj-overlay-hidden"],
    )

    frame.evaluate("() => document.querySelector('mj-overlay').hide()")
    assert frame.evaluate(
        "() => document.querySelector('mj-overlay').hasAttribute('visible')"
    ) is False

    frame.evaluate("() => document.querySelector('mj-overlay').show()")
    assert frame.evaluate(
        "() => document.querySelector('mj-overlay').hasAttribute('visible')"
    ) is True

    # The events report the finished state, so they arrive once the
    # backdrop fade has ended; a toggle during a fade delivers the pending
    # event first, keeping the order.
    # The example's overlay may still be fading in when the collector is
    # installed: hide() then delivers that pending visible event first. Wait
    # for the visible event of the show() that follows the hide.
    frame.wait_for_function(
        "() => { const e = window.__mjevents; const h = e.indexOf('mj-overlay-hidden');"
        " return h >= 0 && e.indexOf('mj-overlay-visible', h + 1) > h; }",
        timeout=5000,
    )

    events = _get_events(frame=frame)
    hidden_at = events.index("mj-overlay-hidden")
    assert "mj-overlay-visible" in events[hidden_at + 1:]

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_overlay_inert_and_scroll_lock_follow_composer(page, base_url):
    """
        mj-overlay: an overlay that a composer configures and appends after
        setting ``visible`` still makes the background inert and locks
        scrolling, and both are released (with the page's own overflow
        value restored) when it is removed.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-overlay")

    state = frame.evaluate(
        "async () => {"
        "  document.body.innerHTML = '<p id=\"bg\">background</p>';"
        "  await new Promise(r => setTimeout(r, 50));"
        "  document.body.style.overflow = 'clip';"
        "  const first = document.createElement('mj-overlay');"
        "  first.setAttribute('visible', '');"
        "  document.body.appendChild(first);"
        "  const second = document.createElement('mj-overlay');"
        "  second.setAttribute('visible', '');"
        "  document.body.appendChild(second);"
        "  await new Promise(r => setTimeout(r, 50));"
        "  const bg = document.getElementById('bg');"
        "  const whileOpen = [bg.inert, document.body.style.overflow];"
        "  first.remove();"
        "  await new Promise(r => setTimeout(r, 50));"
        "  const afterFirst = [bg.inert, document.body.style.overflow];"
        "  second.remove();"
        "  await new Promise(r => setTimeout(r, 50));"
        "  const afterBoth = [bg.inert, document.body.style.overflow];"
        "  return { whileOpen, afterFirst, afterBoth };"
        "}"
    )

    assert state["whileOpen"] == [True, "hidden"]
    assert state["afterFirst"] == [True, "hidden"], "a second open overlay keeps the page inert"
    assert state["afterBoth"] == [False, "clip"]

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_overlay_click_fires_event(page, base_url):
    """
        mj-overlay: clicking the backdrop element fires the mj-overlay-click
        event.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-overlay")

    _collect_events(
        frame=frame,
        tag="mj-overlay",
        event_names=["mj-overlay-click"],
    )

    # Click the internal backdrop div inside the shadow root.
    frame.evaluate(
        "() => document.querySelector('mj-overlay').shadowRoot"
        ".querySelector('.backdrop').click()"
    )

    events = _get_events(frame=frame)
    assert "mj-overlay-click" in events

    return


# ---------------------------------------------------------------------------
# mj-toast-region
# ---------------------------------------------------------------------------

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_toast_region_add_shows_toast(page, base_url):
    """
        mj-toast-region: calling add() with a message shows a toast item
        in the region and fires mj-toast-show.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-toast-region")

    _collect_events(
        frame=frame,
        tag="mj-toast-region",
        event_names=["mj-toast-show"],
    )

    frame.evaluate(
        "() => document.querySelector('mj-toast-region').add("
        "{ message: 'Test toast', severity: 'info', duration: 0 })"
    )

    # Toast items are rendered inside the shadow root; use wait_for_function.
    frame.wait_for_function(
        "() => document.querySelector('mj-toast-region').shadowRoot"
        ".querySelectorAll('.toast-item').length > 0",
        timeout=5000,
    )

    events = _get_events(frame=frame)
    assert "mj-toast-show" in events

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_toast_region_dismiss_all(page, base_url):
    """
        mj-toast-region: dismissAll() removes all visible toasts.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-toast-region")

    # Add a persistent toast so we have something to dismiss.
    frame.evaluate(
        "() => document.querySelector('mj-toast-region').add("
        "{ message: 'Persistent', severity: 'success', duration: 0 })"
    )

    frame.wait_for_function(
        "() => document.querySelector('mj-toast-region').shadowRoot"
        ".querySelectorAll('.toast-item').length > 0",
        timeout=5000,
    )

    frame.evaluate(
        "() => document.querySelector('mj-toast-region').dismissAll()"
    )

    count = frame.evaluate(
        "() => document.querySelector('mj-toast-region').count"
    )
    assert count == 0

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_toast_region_severity_variants(page, base_url):
    """
        mj-toast-region: adding toasts of each severity sets the correct
        data-severity attribute on the rendered list item.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-toast-region")

    # Set max-visible to 4 so all severity toasts appear simultaneously,
    # then add toasts with duration=0 so they don't auto-dismiss.
    frame.evaluate(
        "() => {"
        "  const r = document.querySelector('mj-toast-region');"
        "  r.setAttribute('max-visible', '4');"
        "  ['info','success','warning','error'].forEach(s => "
        "    r.add({ message: s + ' toast', severity: s, duration: 0 }));"
        "}"
    )

    # Toast items are rendered inside the shadow root ol.region.
    frame.wait_for_function(
        "() => document.querySelector('mj-toast-region').shadowRoot"
        ".querySelectorAll('.toast-item').length >= 4",
        timeout=5000,
    )

    for severity in ("info", "success", "warning", "error"):
        found = frame.evaluate(
            f"() => document.querySelector('mj-toast-region').shadowRoot"
            f".querySelector('.toast-item[data-severity=\"{severity}\"]') !== null"
        )
        assert found is True, f"toast with severity={severity} not found"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_toast_region_message_is_text(page, base_url):
    """
        mj-toast-region: a message containing markup is shown as text and
        its event handlers never run.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-toast-region")

    payload = "x'\"><img src=\"data:,x\" onerror=\"top.__hits=(top.__hits||0)+1\">"
    text = frame.evaluate(
        "async (payload) => {"
        "  const region = document.querySelector('mj-toast-region');"
        "  region.add({ message: payload, title: payload, duration: 0 });"
        "  await new Promise(r => setTimeout(r, 300));"
        "  const item = region.shadowRoot.querySelector('.toast-item:last-child');"
        "  return { message: item.querySelector('.toast-message').textContent,"
        "           images: item.querySelectorAll('img').length };"
        "}",
        payload,
    )

    assert text == {"message": payload, "images": 0}
    assert frame.evaluate("() => top.__hits") is None

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_toast_region_dismiss_all_clears_queue(page, base_url):
    """
        mj-toast-region: dismissAll() removes the visible toasts and the
        queued ones; no queued toast is promoted onto the screen.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-toast-region")

    state = frame.evaluate(
        "async () => {"
        "  const region = document.querySelector('mj-toast-region');"
        "  region.dismissAll();"
        "  for (let i = 0; i < 8; i++) { region.add({ message: 'm' + i, duration: 0 }); }"
        "  const before = { visible: region.visible.length, queued: region.queue.length };"
        "  region.dismissAll();"
        "  await new Promise(r => setTimeout(r, 600));"
        "  return { before: before, count: region.count,"
        "           rendered: region.shadowRoot.querySelectorAll('.toast-item').length };"
        "}"
    )

    assert state["before"] == {"visible": 3, "queued": 5}
    assert state["count"] == 0
    assert state["rendered"] == 0

    return


# ---------------------------------------------------------------------------
# mj-notification-center
# ---------------------------------------------------------------------------

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_notification_center_add_item_shows_entry(page, base_url):
    """
        mj-notification-center: addItem() appends a notification to the
        list and the item is rendered in the shadow DOM.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-notification-center")

    # The catalog page loads with an empty list; add an item via the API.
    frame.evaluate(
        "() => document.querySelector('mj-notification-center').addItem({"
        "  id: 'test-1', title: 'Hello', body: 'World',"
        "  timestamp: new Date().toISOString()"
        "})"
    )

    frame.wait_for_function(
        "() => document.querySelector('mj-notification-center').shadowRoot"
        ".querySelectorAll('.nc-item').length > 0",
        timeout=5000,
    )

    count = frame.evaluate(
        "() => document.querySelector('mj-notification-center').shadowRoot"
        ".querySelectorAll('.nc-item').length"
    )
    assert count > 0

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_notification_center_unread_badge(page, base_url):
    """
        mj-notification-center: the unread badge count matches the number
        of items with read=false.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-notification-center")

    frame.evaluate(
        "() => document.querySelector('mj-notification-center').addItem({"
        "  id: 'badge-1', title: 'Unread', body: 'Message',"
        "  timestamp: new Date().toISOString()"
        "})"
    )

    frame.wait_for_function(
        "() => document.querySelector('mj-notification-center').shadowRoot"
        ".querySelectorAll('.nc-item').length > 0",
        timeout=5000,
    )

    unread_count = frame.evaluate(
        "() => document.querySelector('mj-notification-center').unreadCount"
    )
    badge_text = frame.evaluate(
        "() => document.querySelector('mj-notification-center').shadowRoot"
        ".querySelector('.nc-badge').textContent.trim()"
    )

    assert badge_text == str(unread_count)
    assert unread_count > 0

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_notification_center_mark_all_read(page, base_url):
    """
        mj-notification-center: clicking Mark all read fires
        mj-notification-mark-all-read and resets unread count to zero.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-notification-center")

    frame.evaluate(
        "() => document.querySelector('mj-notification-center').addItem({"
        "  id: 'mar-1', title: 'Unread item', body: 'Body',"
        "  timestamp: new Date().toISOString()"
        "})"
    )

    frame.wait_for_function(
        "() => document.querySelector('mj-notification-center').shadowRoot"
        ".querySelectorAll('.nc-item').length > 0",
        timeout=5000,
    )

    _collect_events(
        frame=frame,
        tag="mj-notification-center",
        event_names=["mj-notification-mark-all-read"],
    )

    frame.evaluate(
        "() => document.querySelector('mj-notification-center').shadowRoot"
        ".querySelector('[data-action=\"mark-all-read\"]').click()"
    )

    unread_count = frame.evaluate(
        "() => document.querySelector('mj-notification-center').unreadCount"
    )
    assert unread_count == 0

    events = _get_events(frame=frame)
    assert "mj-notification-mark-all-read" in events

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_notification_center_clear_all(page, base_url):
    """
        mj-notification-center: clicking Clear all removes all items and
        fires mj-notification-clear-all.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-notification-center")

    frame.evaluate(
        "() => document.querySelector('mj-notification-center').addItem({"
        "  id: 'ca-1', title: 'To clear', body: 'Body',"
        "  timestamp: new Date().toISOString()"
        "})"
    )

    frame.wait_for_function(
        "() => document.querySelector('mj-notification-center').shadowRoot"
        ".querySelectorAll('.nc-item').length > 0",
        timeout=5000,
    )

    _collect_events(
        frame=frame,
        tag="mj-notification-center",
        event_names=["mj-notification-clear-all"],
    )

    frame.evaluate(
        "() => document.querySelector('mj-notification-center').shadowRoot"
        ".querySelector('[data-action=\"clear-all\"]').click()"
    )

    item_count = frame.evaluate(
        "() => document.querySelector('mj-notification-center').items.length"
    )
    assert item_count == 0

    events = _get_events(frame=frame)
    assert "mj-notification-clear-all" in events

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_notification_center_item_text_is_not_markup(page, base_url):
    """
        mj-notification-center: title and body containing markup are shown
        as text; items without a `read` field count as unread.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-notification-center")

    payload = "x'\"><img src=\"data:,x\" onerror=\"top.__hits=(top.__hits||0)+1\">"
    state = frame.evaluate(
        "async (payload) => {"
        "  const nc = document.querySelector('mj-notification-center');"
        "  nc.items = [{ id: payload, title: payload, body: payload, timestamp: Date.now() }];"
        "  await new Promise(r => setTimeout(r, 200));"
        "  const item = nc.shadowRoot.querySelector('.nc-item');"
        "  return { title: item.querySelector('.nc-item-title').textContent,"
        "           images: nc.shadowRoot.querySelectorAll('.nc-list img').length,"
        "           unread: nc.unreadCount,"
        "           badge: nc.shadowRoot.querySelector('.nc-badge').textContent };"
        "}",
        payload,
    )

    assert state == {"title": payload, "images": 0, "unread": 1, "badge": "1"}
    assert frame.evaluate("() => top.__hits") is None

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_notification_center_keyboard_activation(page, base_url):
    """
        mj-notification-center: Enter on an item marks it read and keeps
        focus on it; Enter on its Dismiss button dismisses instead of
        selecting, and focus moves to the next item.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-notification-center")

    frame.evaluate(
        "() => {"
        "  const nc = document.querySelector('mj-notification-center');"
        "  window.__nc = [];"
        "  ['mj-notification-read', 'mj-notification-select', 'mj-notification-dismiss'].forEach(n =>"
        "    nc.addEventListener(n, e => window.__nc.push(n + ':' + e.detail.item.id)));"
        "  nc.items = ["
        "    { id: 'a', title: 'First', timestamp: Date.now() },"
        "    { id: 'b', title: 'Second', timestamp: Date.now() }"
        "  ];"
        "}"
    )

    frame.locator("mj-notification-center .nc-item").first.press("Enter")
    state = frame.evaluate(
        "() => {"
        "  const nc = document.querySelector('mj-notification-center');"
        "  const active = nc.shadowRoot.activeElement;"
        "  return { focused: active !== null && active.classList.contains('nc-item'),"
        "           unread: nc.unreadCount };"
        "}"
    )
    assert state == {"focused": True, "unread": 1}

    frame.locator("mj-notification-center .nc-item").first.locator(".nc-dismiss-btn").press("Enter")
    state = frame.evaluate(
        "() => {"
        "  const nc = document.querySelector('mj-notification-center');"
        "  const active = nc.shadowRoot.activeElement;"
        "  return { ids: nc.items.map(i => i.id),"
        "           focusedTab: active !== null ? active.tabIndex : null };"
        "}"
    )
    assert state == {"ids": ["b"], "focusedTab": 0}

    events = frame.evaluate("() => window.__nc")
    assert events == [
        "mj-notification-read:a", "mj-notification-select:a", "mj-notification-dismiss:a"
    ]

    return


# ---------------------------------------------------------------------------
# mj-context-menu
# ---------------------------------------------------------------------------

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_context_menu_opens_on_right_click(page, base_url):
    """
        mj-context-menu: right-clicking the slotted target opens the menu
        and fires mj-context-menu-open.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-context-menu")

    _collect_events(
        frame=frame,
        tag="mj-context-menu",
        event_names=["mj-context-menu-open"],
    )

    # Right-click the slotted target div.
    target = frame.locator("mj-context-menu div").first
    target.click(button="right")

    is_open = frame.evaluate(
        "() => document.querySelector('mj-context-menu').hasAttribute('open')"
    )
    assert is_open is True

    events = _get_events(frame=frame)
    assert "mj-context-menu-open" in events

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_context_menu_escape_closes(page, base_url):
    """
        mj-context-menu: pressing Escape while the menu is open closes it
        and fires mj-context-menu-close.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-context-menu")

    # Open it programmatically.
    frame.evaluate(
        "() => { const m = document.querySelector('mj-context-menu');"
        " m.items = [{ id: 'x', label: 'X' }]; m.show(50, 50); }"
    )

    _collect_events(
        frame=frame,
        tag="mj-context-menu",
        event_names=["mj-context-menu-close"],
    )

    frame.evaluate(
        "() => {"
        "  const menu = document.querySelector('mj-context-menu').shadowRoot"
        "    .querySelector('.menu');"
        "  menu.dispatchEvent(new KeyboardEvent('keydown',"
        "    { key: 'Escape', bubbles: true, cancelable: true }));"
        "}"
    )

    is_open = frame.evaluate(
        "() => document.querySelector('mj-context-menu').hasAttribute('open')"
    )
    assert is_open is False

    events = _get_events(frame=frame)
    assert "mj-context-menu-close" in events

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_context_menu_item_select_fires_event(page, base_url):
    """
        mj-context-menu: clicking a menu item fires mj-context-menu-select
        and closes the menu.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-context-menu")

    # Open with known items.
    frame.evaluate(
        "() => { const m = document.querySelector('mj-context-menu');"
        " m.items = [{ id: 'copy', label: 'Copy' }]; m.show(50, 50); }"
    )

    _collect_events(
        frame=frame,
        tag="mj-context-menu",
        event_names=["mj-context-menu-select"],
    )

    # The menu is fixed-positioned; click the first item via JS.
    frame.evaluate(
        "() => document.querySelector('mj-context-menu').shadowRoot"
        ".querySelector('.menu-item').click()"
    )

    events = _get_events(frame=frame)
    assert "mj-context-menu-select" in events

    is_open = frame.evaluate(
        "() => document.querySelector('mj-context-menu').hasAttribute('open')"
    )
    assert is_open is False

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_context_menu_show_close_api(page, base_url):
    """
        mj-context-menu: show(x, y) opens the menu; close() dismisses it.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-context-menu")

    frame.evaluate(
        "() => { const m = document.querySelector('mj-context-menu');"
        " m.items = [{ id: 'a', label: 'Action' }]; m.show(100, 100); }"
    )

    assert frame.evaluate(
        "() => document.querySelector('mj-context-menu').hasAttribute('open')"
    ) is True

    frame.evaluate("() => document.querySelector('mj-context-menu').close()")

    assert frame.evaluate(
        "() => document.querySelector('mj-context-menu').hasAttribute('open')"
    ) is False

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_context_menu_example_items_survive_upgrade(page, base_url):
    """
        mj-context-menu: the items the example assigns before the element
        upgrades are rendered on right-click, as text.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-context-menu")

    frame.locator("mj-context-menu div").first.click(button="right")

    labels = frame.evaluate(
        "() => Array.from(document.querySelector('mj-context-menu').shadowRoot"
        ".querySelectorAll('.menu-item .item-label')).map(l => l.textContent)"
    )
    assert labels == ["Copy", "Cut", "Paste", "Delete"]

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_context_menu_click_in_target_region_dismisses(page, base_url):
    """
        mj-context-menu: a left click elsewhere in the wrapped region closes
        the open menu (light dismiss), and the label attribute is text.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-context-menu")

    frame.locator("mj-context-menu div").first.click(button="right")
    assert frame.evaluate("() => document.querySelector('mj-context-menu').hasAttribute('open')") is True

    frame.evaluate(
        "() => document.querySelector('mj-context-menu div').dispatchEvent("
        "new PointerEvent('pointerdown', { bubbles: true, composed: true }))"
    )
    assert frame.evaluate("() => document.querySelector('mj-context-menu').hasAttribute('open')") is False

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_context_menu_submenu_and_radio_items(page, base_url):
    """
        mj-context-menu: ArrowRight opens a submenu and ArrowLeft returns to
        its parent item; choosing a radio item checks it and unchecks the
        others of its group.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-context-menu")

    frame.evaluate(
        "() => {"
        "  const m = document.querySelector('mj-context-menu');"
        "  m.items = ["
        "    { id: 'share', label: 'Share', submenu: [{ id: 'mail', label: 'Mail' }, { id: 'link', label: 'Link' }] },"
        "    { id: 'small', label: 'Small', type: 'radio', group: 'size', checked: true },"
        "    { id: 'large', label: 'Large', type: 'radio', group: 'size' }"
        "  ];"
        "  m.show(40, 40);"
        "}"
    )

    frame.locator("mj-context-menu .menu-item", has_text="Share").press("ArrowRight")
    opened = frame.evaluate(
        "() => {"
        "  const root = document.querySelector('mj-context-menu').shadowRoot;"
        "  return { menus: root.querySelectorAll('ul.menu').length,"
        "           focused: root.activeElement.textContent.trim(),"
        "           expanded: root.querySelector('.menu-item').getAttribute('aria-expanded') };"
        "}"
    )
    assert opened == {"menus": 2, "focused": "Mail", "expanded": "true"}

    frame.locator("mj-context-menu .submenu .menu-item", has_text="Mail").press("ArrowLeft")
    closed = frame.evaluate(
        "() => {"
        "  const root = document.querySelector('mj-context-menu').shadowRoot;"
        "  return { menus: root.querySelectorAll('ul.menu').length, focused: root.activeElement.textContent.trim() };"
        "}"
    )
    assert closed["menus"] == 1
    assert closed["focused"].startswith("Share")

    frame.evaluate(
        "() => Array.from(document.querySelector('mj-context-menu').shadowRoot"
        ".querySelectorAll('.menu-item')).find(i => i.textContent.includes('Large')).click()"
    )
    checked = frame.evaluate(
        "() => Array.from(document.querySelector('mj-context-menu').shadowRoot"
        ".querySelectorAll('[role=menuitemradio]')).map(i => i.getAttribute('aria-checked'))"
    )
    assert checked == ["false", "true"]

    return


# ---------------------------------------------------------------------------
# mj-command-palette
# ---------------------------------------------------------------------------

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_command_palette_opens_with_open_attribute(page, base_url):
    """
        mj-command-palette: the backdrop has role=dialog and aria-modal=true
        when the open attribute is present (catalog example ships with open).

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-command-palette")

    is_open = frame.evaluate(
        "() => document.querySelector('mj-command-palette').hasAttribute('open')"
    )
    assert is_open is True

    role = frame.evaluate(
        "() => document.querySelector('mj-command-palette').shadowRoot"
        ".querySelector('.cp-backdrop').getAttribute('role')"
    )
    assert role == "dialog"

    aria_modal = frame.evaluate(
        "() => document.querySelector('mj-command-palette').shadowRoot"
        ".querySelector('.cp-backdrop').getAttribute('aria-modal')"
    )
    assert aria_modal == "true"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_command_palette_escape_closes(page, base_url):
    """
        mj-command-palette: dispatching Escape on the backdrop closes the
        palette and fires mj-command-palette-close.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-command-palette")

    _collect_events(
        frame=frame,
        tag="mj-command-palette",
        event_names=["mj-command-palette-close"],
    )

    # The backdrop is fixed-positioned inside the iframe; dispatch the
    # Escape event directly to avoid the "outside viewport" restriction.
    frame.evaluate(
        "() => {"
        "  const backdrop = document.querySelector('mj-command-palette').shadowRoot"
        "    .querySelector('.cp-backdrop');"
        "  backdrop.dispatchEvent(new KeyboardEvent('keydown',"
        "    { key: 'Escape', bubbles: true, cancelable: true }));"
        "}"
    )

    is_open = frame.evaluate(
        "() => document.querySelector('mj-command-palette').hasAttribute('open')"
    )
    assert is_open is False

    events = _get_events(frame=frame)
    assert "mj-command-palette-close" in events

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_command_palette_search_filters_results(page, base_url):
    """
        mj-command-palette: dispatching input events on the search input
        triggers the debounced filter and fires mj-command-palette-query.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-command-palette")

    _collect_events(
        frame=frame,
        tag="mj-command-palette",
        event_names=["mj-command-palette-query"],
    )

    # The input is inside a fixed-position overlay; set its value via JS
    # and dispatch an input event so the component's listener fires.
    frame.evaluate(
        "() => {"
        "  const input = document.querySelector('mj-command-palette').shadowRoot"
        "    .querySelector('.cp-input');"
        "  input.value = 'New';"
        "  input.dispatchEvent(new Event('input', { bubbles: true }));"
        "}"
    )

    # Wait for the debounce delay (default 120ms) plus some margin.
    frame.wait_for_timeout(300)

    events = _get_events(frame=frame)
    assert "mj-command-palette-query" in events

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_command_palette_show_and_close_api(page, base_url):
    """
        mj-command-palette: calling close() removes the open attribute;
        calling show() restores it.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-command-palette")

    frame.evaluate("() => document.querySelector('mj-command-palette').close()")
    assert frame.evaluate(
        "() => document.querySelector('mj-command-palette').hasAttribute('open')"
    ) is False

    frame.evaluate("() => document.querySelector('mj-command-palette').show()")
    assert frame.evaluate(
        "() => document.querySelector('mj-command-palette').hasAttribute('open')"
    ) is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_command_palette_default_list_is_selectable(page, base_url):
    """
        mj-command-palette: the commands the example assigns before upgrade
        are listed when the palette opens; Enter on the default list selects
        the highlighted command and the palette closes once.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-command-palette")

    state = frame.evaluate(
        "() => {"
        "  const cp = document.querySelector('mj-command-palette');"
        "  window.__cp = [];"
        "  cp.addEventListener('mj-command-palette-select', e => window.__cp.push('select:' + e.detail.command.id));"
        "  cp.addEventListener('mj-command-palette-close', e => window.__cp.push('close:' + e.detail.reason));"
        "  const rows = Array.from(cp.shadowRoot.querySelectorAll('.cp-item-label')).map(l => l.textContent);"
        "  const icon = cp.shadowRoot.querySelector('.cp-item-icon').textContent;"
        "  const input = cp.shadowRoot.querySelector('.cp-input');"
        "  input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true, cancelable: true }));"
        "  return { rows: rows, icon: icon };"
        "}"
    )

    assert state["rows"] == ["New File", "Open File", "Save", "Preferences"]
    assert state["icon"] == "\U0001F4C4"
    assert frame.evaluate("() => window.__cp") == ["select:new-file", "close:select"]

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_command_palette_shortcut_matches_modifiers_exactly(page, base_url):
    """
        mj-command-palette: Ctrl+K opens the palette, Ctrl+Shift+K does not,
        and an empty global-shortcut attribute disables the shortcut.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-command-palette")

    state = frame.evaluate(
        "() => {"
        "  const cp = document.querySelector('mj-command-palette');"
        "  const press = (init) => document.body.dispatchEvent(new KeyboardEvent('keydown',"
        "    Object.assign({ bubbles: true, cancelable: true }, init)));"
        "  cp.close();"
        "  press({ key: 'K', ctrlKey: true, shiftKey: true });"
        "  const shifted = cp.hasAttribute('open');"
        "  press({ key: 'k', ctrlKey: true });"
        "  const plain = cp.hasAttribute('open');"
        "  cp.close();"
        "  cp.setAttribute('global-shortcut', '');"
        "  press({ key: 'k', ctrlKey: true });"
        "  const disabled = cp.hasAttribute('open');"
        "  return { shifted: shifted, plain: plain, disabled: disabled };"
        "}"
    )

    assert state == {"shifted": False, "plain": True, "disabled": False}

    return


# ---------------------------------------------------------------------------
# mj-tour
# ---------------------------------------------------------------------------

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_tour_starts_with_start_api(page, base_url):
    """
        mj-tour: calling start() sets the active attribute and fires
        mj-tour-start.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-tour")

    _collect_events(
        frame=frame,
        tag="mj-tour",
        event_names=["mj-tour-start"],
    )

    frame.evaluate(
        "() => {"
        "  const t = document.querySelector('mj-tour');"
        "  t.steps = ["
        "    { title: 'Step 1', body: 'First step.' },"
        "    { title: 'Step 2', body: 'Second step.' }"
        "  ];"
        "  t.start();"
        "}"
    )

    is_active = frame.evaluate(
        "() => document.querySelector('mj-tour').hasAttribute('active')"
    )
    assert is_active is True

    events = _get_events(frame=frame)
    assert "mj-tour-start" in events

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_tour_card_has_dialog_role(page, base_url):
    """
        mj-tour: the coach-mark card element carries role=dialog and
        aria-modal=true.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-tour")

    frame.evaluate(
        "() => {"
        "  const t = document.querySelector('mj-tour');"
        "  t.steps = [{ title: 'Hello', body: 'World' }];"
        "  t.start();"
        "}"
    )

    role = frame.evaluate(
        "() => document.querySelector('mj-tour').shadowRoot"
        ".querySelector('.card').getAttribute('role')"
    )
    assert role == "dialog"

    aria_modal = frame.evaluate(
        "() => document.querySelector('mj-tour').shadowRoot"
        ".querySelector('.card').getAttribute('aria-modal')"
    )
    assert aria_modal == "true"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_tour_next_advances_step(page, base_url):
    """
        mj-tour: clicking the Next button advances to step 1 and fires
        mj-tour-next.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-tour")

    _collect_events(
        frame=frame,
        tag="mj-tour",
        event_names=["mj-tour-next"],
    )

    frame.evaluate(
        "() => {"
        "  const t = document.querySelector('mj-tour');"
        "  t.steps = ["
        "    { title: 'Step 1', body: 'Body 1' },"
        "    { title: 'Step 2', body: 'Body 2' }"
        "  ];"
        "  t.start();"
        "}"
    )

    # The tour card is fixed-positioned inside the iframe; click via JS.
    frame.evaluate(
        "() => document.querySelector('mj-tour').shadowRoot"
        ".querySelector('[data-action=\"next\"]').click()"
    )

    current_step = frame.evaluate(
        "() => document.querySelector('mj-tour').getAttribute('current-step')"
    )
    assert current_step == "1"

    events = _get_events(frame=frame)
    assert "mj-tour-next" in events

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_tour_skip_button_dismisses(page, base_url):
    """
        mj-tour: clicking the skip button removes the active attribute and
        fires mj-tour-skip.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-tour")

    frame.evaluate(
        "() => {"
        "  const t = document.querySelector('mj-tour');"
        "  t.steps = [{ title: 'S1', body: 'B1' }];"
        "  t.start();"
        "}"
    )

    _collect_events(
        frame=frame,
        tag="mj-tour",
        event_names=["mj-tour-skip"],
    )

    # The tour card is fixed-positioned; click via JS to bypass viewport.
    frame.evaluate(
        "() => document.querySelector('mj-tour').shadowRoot"
        ".querySelector('[data-action=\"skip\"]').click()"
    )

    is_active = frame.evaluate(
        "() => document.querySelector('mj-tour').hasAttribute('active')"
    )
    assert is_active is False

    events = _get_events(frame=frame)
    assert "mj-tour-skip" in events

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_tour_escape_key_skips(page, base_url):
    """
        mj-tour: dispatching Escape on the card element skips the tour
        and removes the active attribute.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-tour")

    frame.evaluate(
        "() => {"
        "  const t = document.querySelector('mj-tour');"
        "  t.steps = [{ title: 'S1', body: 'B1' }];"
        "  t.start();"
        "}"
    )

    frame.evaluate(
        "() => {"
        "  const card = document.querySelector('mj-tour').shadowRoot"
        "    .querySelector('.card');"
        "  card.dispatchEvent(new KeyboardEvent('keydown',"
        "    { key: 'Escape', bubbles: true, cancelable: true }));"
        "}"
    )

    is_active = frame.evaluate(
        "() => document.querySelector('mj-tour').hasAttribute('active')"
    )
    assert is_active is False

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_tour_complete_fires_event(page, base_url):
    """
        mj-tour: clicking Done on the last step fires mj-tour-complete and
        removes the active attribute.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-tour")

    frame.evaluate(
        "() => {"
        "  const t = document.querySelector('mj-tour');"
        "  t.steps = [{ title: 'Only step', body: 'Last.' }];"
        "  t.start();"
        "}"
    )

    _collect_events(
        frame=frame,
        tag="mj-tour",
        event_names=["mj-tour-complete"],
    )

    # The tour card is fixed-positioned; click the Next/Done button via JS.
    frame.evaluate(
        "() => document.querySelector('mj-tour').shadowRoot"
        ".querySelector('[data-action=\"next\"]').click()"
    )

    is_active = frame.evaluate(
        "() => document.querySelector('mj-tour').hasAttribute('active')"
    )
    assert is_active is False

    events = _get_events(frame=frame)
    assert "mj-tour-complete" in events

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_tour_step_event_fires_once_per_step(page, base_url):
    """
        mj-tour: the steps the example assigns before upgrade are kept;
        start() and each Next fire mj-tour-step exactly once (no recursion
        through the current-step attribute), and the page behind the card
        is inert while the tour runs.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-tour")

    state = frame.evaluate(
        "async () => {"
        "  const t = document.querySelector('mj-tour');"
        "  const steps = [];"
        "  t.addEventListener('mj-tour-step', e => steps.push(e.detail.step));"
        "  const exampleSteps = t.steps.length;"
        "  t.start();"
        "  await new Promise(r => setTimeout(r, 100));"
        "  const button = document.getElementById('start-tour-btn');"
        "  const backgroundInert = button !== null ? button.inert : null;"
        "  t.shadowRoot.querySelector('[data-action=\"next\"]').click();"
        "  await new Promise(r => setTimeout(r, 100));"
        "  const transform = t.shadowRoot.querySelector('.card-wrapper').style.transform;"
        "  t.skip();"
        "  return { exampleSteps, steps, backgroundInert, transform,"
        "           afterSkipInert: button !== null ? button.inert : null };"
        "}"
    )

    assert state["exampleSteps"] == 3
    assert state["steps"] == [0, 1]
    assert state["backgroundInert"] is True
    assert state["transform"] == "", "the centring transform of step 0 must not stay on anchored steps"
    assert state["afterSkipInert"] is False

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_tour_suppressed_by_storage_shows_nothing(page, base_url):
    """
        mj-tour: when storage says the tour was dismissed, start() leaves no
        active attribute and no card on screen, and emits no start event.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-tour")

    state = frame.evaluate(
        "() => {"
        "  const t = document.querySelector('mj-tour');"
        "  const starts = [];"
        "  t.addEventListener('mj-tour-start', () => starts.push(1));"
        "  localStorage.setItem('mj-tour-test-suppressed', JSON.stringify({ dismissed: true }));"
        "  t.setAttribute('storage-key', 'mj-tour-test-suppressed');"
        "  t.start();"
        "  const card = t.shadowRoot.querySelector('.card-wrapper');"
        "  const result = { active: t.hasAttribute('active'), display: getComputedStyle(card).display,"
        "                   starts: starts.length };"
        "  localStorage.removeItem('mj-tour-test-suppressed');"
        "  return result;"
        "}"
    )

    assert state == {"active": False, "display": "none", "starts": 0}

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_tour_navigation_slot_focuses_slotted_forward_button(page, base_url):
    """
        mj-tour: with the `navigation` slot filled, each step focuses the last
        slotted control (the forward button), or the slotted control with
        `autofocus`. Focus used to stay on <body>.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_example(page, base_url, tag="mj-tour", key="custom")

    focus = frame.evaluate(
        """async () => {
            const wait = (ms) => new Promise((done) => setTimeout(done, ms))
            const focusedId = () => {
              let active = document.activeElement
              while (active !== null && active.shadowRoot && active.shadowRoot.activeElement) {
                active = active.shadowRoot.activeElement
              }
              return active === null ? null : (active.id || active.tagName)
            }
            const tour = document.getElementById("custom-tour")
            tour.start()
            await wait(300)
            const first = focusedId()
            tour.next()
            await wait(300)
            const second = focusedId()
            document.getElementById("custom-back").setAttribute("autofocus", "")
            tour.back()
            await wait(300)
            const third = focusedId()
            document.getElementById("custom-back").removeAttribute("autofocus")
            tour.skip()
            return [first, second, third]
        }"""
    )

    assert focus == ["custom-next", "custom-next", "custom-back"], focus

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_tour_scroll_lock_is_a_boolean_attribute_applied_live(page, base_url):
    """
        mj-tour: `scroll-lock` is a boolean attribute (present, any value but
        "false", locks page scrolling; it used to need the literal "true")
        and changes take effect while the tour runs.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-tour")

    states = frame.evaluate(
        """async () => {
            const wait = (ms) => new Promise((done) => setTimeout(done, ms))
            const overflow = () => getComputedStyle(document.documentElement).overflow
            const tour = document.querySelector("mj-tour")
            tour.steps = [{ title: "One", body: "First step." }]
            tour.setAttribute("scroll-lock", "")
            tour.start()
            await wait(100)
            const locked = overflow()
            tour.setAttribute("scroll-lock", "false")
            await wait(50)
            const unlocked = overflow()
            tour.setAttribute("scroll-lock", "")
            await wait(50)
            const relocked = overflow()
            tour.skip()
            await wait(50)
            return [locked, unlocked, relocked, overflow()]
        }"""
    )

    assert states[0] == "hidden", "scroll-lock=\"\" should lock scrolling: {}".format(states)
    assert states[1] != "hidden", "scroll-lock=\"false\" should release it while running: {}".format(states)
    assert states[2] == "hidden", "setting it again while running should lock: {}".format(states)
    assert states[3] != "hidden", "ending the tour releases the lock: {}".format(states)

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_tour_floating_variant_centres_every_card(page, base_url):
    """
        mj-tour: `variant="floating"` centres every card with the page dimmed
        evenly and ignores the steps' targets; removing it while the tour
        runs anchors the card to its target again. `variant` used to be
        watched but unused.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_example(page, base_url, tag="mj-tour", key="floating")

    state = frame.evaluate(
        """async () => {
            const wait = (ms) => new Promise((done) => setTimeout(done, ms))
            const tour = document.getElementById("floating-tour")
            const spotlight = tour.shadowRoot.querySelector(".spotlight")
            const card = tour.shadowRoot.querySelector(".card-wrapper")
            const centreOffset = () => {
              const box = card.getBoundingClientRect()
              return Math.round(Math.abs(box.left + box.width / 2 - window.innerWidth / 2))
            }
            tour.start()
            await wait(300)
            const floating = { centred: spotlight.hasAttribute("data-centred"), offset: centreOffset() }
            tour.removeAttribute("variant")
            await wait(300)
            const anchored = { centred: spotlight.hasAttribute("data-centred") }
            tour.skip()
            return { floating: floating, anchored: anchored }
        }"""
    )

    assert state["floating"]["centred"] is True, state
    assert state["floating"]["offset"] <= 1, "the floating card should be centred: {}".format(state)
    assert state["anchored"]["centred"] is False, "without variant the card is anchored again: {}".format(state)

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
