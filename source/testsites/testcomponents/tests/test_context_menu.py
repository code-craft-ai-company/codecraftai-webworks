"""
    .. module:: testcomponents.tests.test_context_menu
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: The popup context menu and the other behaviour every mj-* component inherits.

    Tests for the popup context menu provided by the MjElement base class.
    Because the capability lives on the base class, every mj-* component
    inherits it -- these tests exercise it on components drawn from several
    different groups to confirm that.

    The tests at the end cover the rest of the shared core that every
    component inherits: the native-named event bridge of ``MjElement.emit``,
    rendering again after a locale change, label activation of
    form-associated controls and the live regions of ``announce()`` while a
    modal dialog is open.
"""

import ccai.testbase as testbase

from testcomponents.harness.browsers import expect
from testcomponents.harness.factories import create_page


# Representative components from distinct groups; each extends MjElement,
# so each must inherit the context-menu capability.
_SAMPLE = [
    ("buttons", "mj-button"),
    ("text", "mj-text-field"),
    ("layout", "mj-card"),
    ("feedback", "mj-chip"),
    ("feedback", "mj-alert"),
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


@testbase.attach.parameter(create_page, identifier="page")
@testbase.parametrize("group,tag", _SAMPLE)
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


@testbase.attach.parameter(create_page, identifier="page")
@testbase.parametrize("group,tag", _SAMPLE)
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


@testbase.attach.parameter(create_page, identifier="page")
def test_context_menu_default_is_absent(page, base_url):
    """
        A component with no context menu configured does not open a popup
        on right-click (the capability is opt-in).
    """

    frame = _open_component(page, base_url, "buttons", "mj-button")

    frame.locator("mj-button").first.click(button="right")

    expect(frame.locator(".mj-ctx-menu")).to_have_count(0)

    return


@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.attach.parameter(create_page, identifier="page")
def test_context_menu_home_end_single_active(page, base_url):
    """
        Home and End move the highlight to the first / last enabled item and
        exactly one item is highlighted afterwards; the menu has an
        accessible name even without `context-menu-label`.
    """

    frame = _open_component(page, base_url, "buttons", "mj-button")
    _configure_menu(frame, "mj-button")

    frame.locator("mj-button").first.click(button="right")
    menu = frame.locator(".mj-ctx-menu")
    expect(menu).to_be_visible()
    expect(menu).to_have_attribute("aria-label", "Context menu")

    menu.press("End")
    expect(frame.locator(".mj-ctx-active")).to_have_count(1)
    expect(frame.locator(".mj-ctx-active")).to_have_text("Delete")

    menu.press("Home")
    expect(frame.locator(".mj-ctx-active")).to_have_count(1)
    expect(frame.locator(".mj-ctx-active")).to_have_text("Duplicate")

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_context_menu_nested_component_wins(page, base_url):
    """
        When a component with a context menu sits inside another one that
        has a menu too, right-clicking the inner component opens only the
        inner menu.
    """

    frame = _open_component(page, base_url, "layout", "mj-card")

    frame.evaluate(
        """() => {
            const card = document.querySelector('mj-card');
            const inner = document.createElement('mj-button');
            inner.id = 'inner-button';
            inner.textContent = 'Inner';
            card.appendChild(inner);
            card.setContextMenu([{ label: 'Outer item', value: 'outer' }]);
            inner.setContextMenu([{ label: 'Inner item', value: 'inner' }]);
        }"""
    )

    frame.locator("#inner-button").click(button="right")

    expect(frame.locator(".mj-ctx-menu")).to_have_count(1)
    expect(frame.locator(".mj-ctx-item")).to_have_text(["Inner item"])

    return


@testbase.attach.parameter(create_page, identifier="page")
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


@testbase.attach.parameter(create_page, identifier="page")
def test_context_menu_stays_open_when_viewport_resizes(page, base_url):
    """
        A viewport resize keeps the menu open and inside the viewport. The
        preview frame grows to fit the open menu, so a menu that closed on
        resize was dismissed right after a real right-click (FP-040).
    """

    frame = _open_component(page, base_url, "buttons", "mj-button")
    _configure_menu(frame, "mj-button")

    frame.locator("mj-button").first.click(button="right")
    menu = frame.locator(".mj-ctx-menu")
    expect(menu).to_be_visible()

    page.evaluate("() => { document.getElementById('pg-frame').style.width = '240px'; }")
    frame.wait_for_function("() => window.innerWidth <= 240", timeout=5000)
    page.wait_for_timeout(200)

    expect(menu).to_be_visible()
    inside = frame.evaluate(
        """() => {
            const rect = document.querySelector('.mj-ctx-menu').getBoundingClientRect();
            return rect.left >= 0 && rect.right <= window.innerWidth;
        }"""
    )
    assert inside is True

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_bridged_native_event_not_fired_when_cancelled(page, base_url):
    """
        `emit("mj-change", ..., { cancelable: true })` fires the bridged
        native `change` only when no listener cancelled the mj-change
        (FP-067).
    """

    frame = _open_component(page, base_url, "buttons", "mj-button")

    counts = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-button');
            const seen = { change: 0 };
            let refuse = true;
            el.addEventListener('change', () => { seen.change = seen.change + 1; });
            el.addEventListener('mj-change', (event) => { if (refuse === true) { event.preventDefault(); } });
            const refused = el.emit('mj-change', { value: 1 }, { cancelable: true });
            const changesAfterRefusal = seen.change;
            refuse = false;
            const accepted = el.emit('mj-change', { value: 2 }, { cancelable: true });
            return { refused: refused, changesAfterRefusal: changesAfterRefusal, accepted: accepted, changes: seen.change };
        }"""
    )
    assert counts == {"refused": False, "changesAfterRefusal": 0, "accepted": True, "changes": 1}, counts

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_locale_change_renders_components_again(page, base_url):
    """
        `registerStrings` / `setLocale` render connected components again, so
        text read through `t()` follows the change (WW-0884), and state held
        in the component's fields survives.
    """

    frame = _open_component(page, base_url, "buttons", "mj-button")

    result = frame.evaluate(
        """async () => {
            const library = await import('/static/javascript/index.js');
            const field = document.createElement('mj-search-input');
            field.setAttribute('label', 'Find');
            document.body.appendChild(field);
            field.value = 'dock';
            const placeholder = () => field.shadowRoot.querySelector('input').placeholder;
            const before = placeholder();
            const events = [];
            document.addEventListener('mj-locale-change', (event) => { events.push(event.detail.locale); });
            library.registerStrings({ 'core.search': 'Suchen' });
            await new Promise((resolve) => setTimeout(resolve, 50));
            const after = placeholder();
            library.setLocale('de-DE');
            await new Promise((resolve) => setTimeout(resolve, 50));
            return { before: before, after: after, value: field.value, events: events };
        }"""
    )
    assert result["before"] == "Search", result
    assert result["after"] == "Suchen", result
    assert result["value"] == "dock", result
    assert len(result["events"]) == 2 and result["events"][1] == "de-DE", result

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_label_click_focuses_form_control(page, base_url):
    """
        Clicking a `<label for>` of a form-associated component moves focus
        into the component, as it does for a native control (WW-0882).
    """

    frame = _open_component(page, base_url, "buttons", "mj-button")

    frame.evaluate(
        """() => {
            document.body.insertAdjacentHTML('beforeend',
                '<label for="picked-colour" id="colour-label">Colour</label>' +
                '<mj-color-picker id="picked-colour"></mj-color-picker>');
        }"""
    )
    frame.wait_for_function(
        "() => document.getElementById('picked-colour').shadowRoot.querySelector('button, input') !== null",
        timeout=5000,
    )

    frame.locator("#colour-label").click()

    focused = frame.evaluate(
        """() => {
            const host = document.getElementById('picked-colour');
            return document.activeElement === host && host.shadowRoot.activeElement !== null;
        }"""
    )
    assert focused is True

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_announce_reaches_open_modal_dialog(page, base_url):
    """
        While a modal dialog is open everything outside it is inert, so
        `announce()` places its live regions inside the dialog (WW-0888).
    """

    frame = _open_component(page, base_url, "buttons", "mj-button")

    result = frame.evaluate(
        """async () => {
            const library = await import('/static/javascript/index.js');
            document.body.insertAdjacentHTML('beforeend', '<mj-dialog id="modal" label="Settings"><p>Body</p></mj-dialog>');
            const dialog = document.getElementById('modal');
            dialog.showModal();
            await new Promise((resolve) => setTimeout(resolve, 100));
            library.announce('Saved');
            await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
            const insideDialog = (node) => {
                let current = node;
                while (current !== null && current !== undefined) {
                    if (current === dialog) { return true; }
                    current = current.parentNode instanceof ShadowRoot ? current.parentNode.host : current.parentNode;
                }
                return false;
            };
            const regions = Array.from(dialog.shadowRoot.querySelectorAll('.mj-live-region'))
                .concat(Array.from(document.querySelectorAll('.mj-live-region')));
            const polite = regions.find((region) => region.getAttribute('aria-live') === 'polite');
            return { found: polite !== undefined, inside: polite !== undefined && insideDialog(polite), text: polite !== undefined ? polite.textContent : null };
        }"""
    )
    assert result == {"found": True, "inside": True, "text": "Saved"}, result

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
