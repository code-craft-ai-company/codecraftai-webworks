"""
    test_func_overlays.py

    Functional Playwright tests for the 'overlays' component group.

    Covers: mj-dialog, mj-popover, mj-drawer, mj-lightbox, mj-overlay,
    mj-toast-region, mj-notification-center, mj-context-menu,
    mj-command-palette, mj-tour.

    Each test navigates to the component playground page, acquires the
    preview iframe, and exercises the real open/close API derived from
    the component JS source.
"""

import pytest
from playwright.sync_api import expect


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

@pytest.mark.functional
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


@pytest.mark.functional
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


@pytest.mark.functional
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


@pytest.mark.functional
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


@pytest.mark.functional
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


# ---------------------------------------------------------------------------
# mj-popover
# ---------------------------------------------------------------------------

@pytest.mark.functional
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


@pytest.mark.functional
def test_popover_close_button_dismisses(page, base_url):
    """
        mj-popover: clicking the close button removes the open attribute
        and fires mj-popover-close.

        :param page: The Playwright Page.
        :param base_url: The site base URL.
    """

    frame = _open_component(page, base_url, tag="mj-popover")

    _collect_events(
        frame=frame,
        tag="mj-popover",
        event_names=["mj-popover-close"],
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

    return


@pytest.mark.functional
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


@pytest.mark.functional
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


# ---------------------------------------------------------------------------
# mj-drawer
# ---------------------------------------------------------------------------

@pytest.mark.functional
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


@pytest.mark.functional
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


@pytest.mark.functional
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


@pytest.mark.functional
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


@pytest.mark.functional
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


@pytest.mark.functional
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


@pytest.mark.functional
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


@pytest.mark.functional
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


@pytest.mark.functional
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


@pytest.mark.functional
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


# ---------------------------------------------------------------------------
# mj-overlay
# ---------------------------------------------------------------------------

@pytest.mark.functional
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


@pytest.mark.functional
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

    events = _get_events(frame=frame)
    assert "mj-overlay-hidden" in events
    assert "mj-overlay-visible" in events

    return


@pytest.mark.functional
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

@pytest.mark.functional
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


@pytest.mark.functional
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


@pytest.mark.functional
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


# ---------------------------------------------------------------------------
# mj-notification-center
# ---------------------------------------------------------------------------

@pytest.mark.functional
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


@pytest.mark.functional
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


@pytest.mark.functional
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


@pytest.mark.functional
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


# ---------------------------------------------------------------------------
# mj-context-menu
# ---------------------------------------------------------------------------

@pytest.mark.functional
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


@pytest.mark.functional
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


@pytest.mark.functional
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


@pytest.mark.functional
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


# ---------------------------------------------------------------------------
# mj-command-palette
# ---------------------------------------------------------------------------

@pytest.mark.functional
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


@pytest.mark.functional
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


@pytest.mark.functional
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


@pytest.mark.functional
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


# ---------------------------------------------------------------------------
# mj-tour
# ---------------------------------------------------------------------------

@pytest.mark.functional
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


@pytest.mark.functional
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


@pytest.mark.functional
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


@pytest.mark.functional
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


@pytest.mark.functional
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


@pytest.mark.functional
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
