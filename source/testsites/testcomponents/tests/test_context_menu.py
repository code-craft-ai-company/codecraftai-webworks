"""
    test_context_menu.py

    Playwright tests for the popup context menu provided by the MjElement
    base class. Because the capability lives on the base class, every mj-*
    component inherits it -- these tests exercise it on components drawn
    from several different groups to confirm that.
"""

import pytest
from playwright.sync_api import expect


# Representative components from distinct groups; each extends MjElement,
# so each must inherit the context-menu capability.
_SAMPLE = [
    pytest.param("buttons", "mj-button", id="buttons/mj-button"),
    pytest.param("text", "mj-text-field", id="text/mj-text-field"),
    pytest.param("layout", "mj-card", id="layout/mj-card"),
    pytest.param("feedback", "mj-chip", id="feedback/mj-chip"),
    pytest.param("feedback", "mj-alert", id="feedback/mj-alert"),
]


def _open_component(page, base_url, group, tag):
    """
        Open a component page and return the playground preview Frame with
        the component library registered.

        :param page: The Playwright page.
        :param base_url: The site base URL.
        :param group: The component group key.
        :param tag: The component tag.

        :returns: The preview Frame.
    """

    page.goto(base_url + f"/components/{group}/{tag}")
    handle = page.wait_for_selector("[data-testid=playground-preview]")
    frame = handle.content_frame()
    frame.wait_for_function(
        "tag => customElements.get(tag) !== undefined",
        arg=tag,
        timeout=15000,
    )
    return frame


def _configure_menu(frame, tag):
    """
        Set a context menu on the first instance of `tag` in the frame and
        install an event collector for mj-context-select.

        :param frame: The preview Frame.
        :param tag: The component tag.
    """

    frame.evaluate(
        """tag => {
            const el = document.querySelector(tag);
            window.__ctxEvents = [];
            el.addEventListener('mj-context-select', function (event) {
                window.__ctxEvents.push(event.detail.value);
            });
            el.setContextMenu([
                { label: 'Duplicate', value: 'duplicate' },
                { label: 'Disabled item', value: 'nope', disabled: true },
                { separator: true },
                { label: 'Delete', value: 'delete' }
            ]);
        }""",
        tag,
    )
    return


@pytest.mark.parametrize("group, tag", _SAMPLE)
def test_context_menu_opens_on_right_click(page, base_url, group, tag):
    """
        Right-clicking a component that has a context menu configured opens
        the popup menu -- proving the capability is inherited from the base
        class by components across groups.

        :param group: The component group key.
        :param tag: The component tag.
    """

    frame = _open_component(page, base_url, group, tag)
    _configure_menu(frame, tag)

    frame.locator(tag).first.click(button="right")

    menu = frame.locator(".mj-ctx-menu")
    expect(menu).to_be_visible()
    expect(menu).to_have_attribute("role", "menu")
    expect(frame.locator(".mj-ctx-item")).to_have_count(3)

    return


@pytest.mark.parametrize("group, tag", _SAMPLE)
def test_context_menu_selection_emits_event(page, base_url, group, tag):
    """
        Choosing an item emits the mj-context-select event with the item's
        value and closes the menu.

        :param group: The component group key.
        :param tag: The component tag.
    """

    frame = _open_component(page, base_url, group, tag)
    _configure_menu(frame, tag)

    frame.locator(tag).first.click(button="right")
    expect(frame.locator(".mj-ctx-menu")).to_be_visible()

    frame.locator(".mj-ctx-item", has_text="Delete").click()

    events = frame.evaluate("() => window.__ctxEvents")
    assert events == ["delete"]
    expect(frame.locator(".mj-ctx-menu")).to_have_count(0)

    return


def test_context_menu_default_is_absent(page, base_url):
    """
        A component with no context menu configured does not open a popup
        on right-click (the capability is opt-in).
    """

    frame = _open_component(page, base_url, "buttons", "mj-button")

    frame.locator("mj-button").first.click(button="right")

    expect(frame.locator(".mj-ctx-menu")).to_have_count(0)

    return


def test_context_menu_disabled_item_does_not_select(page, base_url):
    """
        A disabled menu item cannot be chosen and does not emit an event.
    """

    frame = _open_component(page, base_url, "buttons", "mj-button")
    _configure_menu(frame, "mj-button")

    frame.locator("mj-button").first.click(button="right")
    # force=True: Playwright treats aria-disabled as non-actionable, but the
    # test must dispatch the click to prove the menu itself ignores it.
    frame.locator(".mj-ctx-item", has_text="Disabled item").click(force=True)

    events = frame.evaluate("() => window.__ctxEvents")
    assert events == []

    return


def test_context_menu_escape_closes(page, base_url):
    """
        Pressing Escape dismisses the context menu without selecting.
    """

    frame = _open_component(page, base_url, "buttons", "mj-button")
    _configure_menu(frame, "mj-button")

    frame.locator("mj-button").first.click(button="right")
    expect(frame.locator(".mj-ctx-menu")).to_be_visible()

    frame.locator(".mj-ctx-menu").press("Escape")

    expect(frame.locator(".mj-ctx-menu")).to_have_count(0)
    events = frame.evaluate("() => window.__ctxEvents")
    assert events == []

    return


def test_context_menu_keyboard_navigation_selects(page, base_url):
    """
        The context menu is operable from the keyboard: arrow keys move the
        active item and Enter chooses it.
    """

    frame = _open_component(page, base_url, "buttons", "mj-button")
    _configure_menu(frame, "mj-button")

    frame.locator("mj-button").first.click(button="right")
    menu = frame.locator(".mj-ctx-menu")
    expect(menu).to_be_visible()

    # First enabled item is focused; Down skips the disabled item to Delete.
    menu.press("ArrowDown")
    menu.press("Enter")

    events = frame.evaluate("() => window.__ctxEvents")
    assert events == ["delete"]

    return


def test_context_menu_via_attribute(page, base_url):
    """
        The context menu can also be configured declaratively through the
        `context-menu` attribute holding a JSON array.
    """

    frame = _open_component(page, base_url, "buttons", "mj-button")

    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-button');
            window.__ctxEvents = [];
            el.addEventListener('mj-context-select', function (event) {
                window.__ctxEvents.push(event.detail.value);
            });
            el.setAttribute(
                'context-menu',
                JSON.stringify([{ label: 'Inspect', value: 'inspect' }])
            );
        }"""
    )

    frame.locator("mj-button").first.click(button="right")
    expect(frame.locator(".mj-ctx-menu")).to_be_visible()
    frame.locator(".mj-ctx-item", has_text="Inspect").click()

    events = frame.evaluate("() => window.__ctxEvents")
    assert events == ["inspect"]

    return
