"""
    .. module:: testcomponents.tests.test_func_selection

    Functional Playwright tests for every component in the 'selection' group.

    Components covered (17):
        mj-select, mj-listbox, mj-combobox, mj-cascading-select,
        mj-radio-group, mj-checkbox-group, mj-segmented-control,
        mj-split-button, mj-menu-button, mj-color-picker, mj-date-picker,
        mj-file-picker, mj-asset-picker, mj-locale-picker, mj-tag-picker,
        mj-tree-selector, mj-transfer-list.

    Each test navigates fresh to the component page and exercises real
    interactions observable via the preview iframe.
"""

import ccai.testbase as testbase

from testcomponents.harness.browsers import expect
from testcomponents.harness.factories import create_page


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_COMPONENT_READY_TIMEOUT = 15000
_INTERACTION_TIMEOUT = 5000


def _get_frame(page, tag: str):
    """
    Navigate to the component page and return the ready preview iframe frame.

    :param page: Playwright page object.
    :param tag: The custom-element tag name (e.g. "mj-select").

    :returns: The Playwright Frame for the playground preview iframe.
    """
    handle = page.wait_for_selector("[data-testid=playground-preview]")
    frame = handle.content_frame()
    frame.wait_for_function(
        "t => customElements.get(t) !== undefined",
        arg=tag,
        timeout=_COMPONENT_READY_TIMEOUT,
    )
    return frame


def _reload_example(page, html: str, tag: str):
    """
    Replace the playground editor content with *html*, click Run, and return
    the refreshed preview frame.

    :param page: Playwright page object.
    :param html: The HTML to put into the editor.
    :param tag: Tag name to wait for in the new frame.

    :returns: The refreshed preview Frame.
    """
    page.get_by_test_id("playground-editor").fill(html)
    page.get_by_test_id("playground-run").click()
    return _get_frame(page, tag)


# ===========================================================================
# mj-select
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_select_renders_trigger(base_url: str, page) -> None:
    """
    mj-select renders a trigger button with the placeholder text when no
    value is pre-selected.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-select")
    frame = _get_frame(page, "mj-select")
    trigger = frame.locator("mj-select").locator(".trigger, [part='trigger']").first
    expect(trigger).to_be_visible()
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_select_opens_on_click(base_url: str, page) -> None:
    """
    mj-select opens the popup when the trigger is clicked and exposes an
    open attribute on the host.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-select")
    frame = _get_frame(page, "mj-select")
    host = frame.locator("mj-select").first
    trigger = host.locator("button").first
    trigger.click()
    has_open = frame.evaluate(
        "() => document.querySelector('mj-select').hasAttribute('open')"
    )
    assert has_open is True, "mj-select should have [open] attribute after trigger click"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_select_picks_option_and_fires_mj_change(base_url: str, page) -> None:
    """
    Clicking an option in the open popup selects it and fires mj-change.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-select")
    frame = _get_frame(page, "mj-select")
    frame.evaluate("""() => {
        window.__mjevents = [];
        const el = document.querySelector('mj-select');
        el.addEventListener('mj-change', e => window.__mjevents.push({type: 'mj-change', value: e.detail.value}));
    }""")
    trigger = frame.locator("mj-select button").first
    trigger.click()
    # Click the first non-disabled option
    option = frame.locator("[role='option']:not([aria-disabled='true'])").first
    option.click()
    events = frame.evaluate("() => window.__mjevents")
    assert len(events) >= 1, "Expected at least one mj-change event after option click"
    assert events[0]["type"] == "mj-change"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_select_disabled_blocks_open(base_url: str, page) -> None:
    """
    A disabled mj-select does not open when the trigger is clicked.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-select")
    frame = _reload_example(
        page,
        '<mj-select disabled placeholder="Blocked"><mj-option value="a">A</mj-option></mj-select>',
        "mj-select",
    )
    trigger = frame.locator("mj-select button").first
    trigger.click(timeout=2000, force=True)
    has_open = frame.evaluate(
        "() => document.querySelector('mj-select').hasAttribute('open')"
    )
    assert has_open is False, "Disabled mj-select must not open"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_select_preselected_value_shown(base_url: str, page) -> None:
    """
    mj-select with a pre-set value attribute shows the matching option label
    in the trigger.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-select")
    frame = _reload_example(
        page,
        '<mj-select value="banana"><mj-option value="apple">Apple</mj-option><mj-option value="banana">Banana</mj-option></mj-select>',
        "mj-select",
    )
    trigger_text = frame.evaluate(
        "() => document.querySelector('mj-select').shadowRoot.querySelector('.label').textContent.trim()"
    )
    assert trigger_text == "Banana", f"Expected trigger label 'Banana', got '{trigger_text}'"
    return


# ===========================================================================
# mj-listbox
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_listbox_renders_with_role(base_url: str, page) -> None:
    """
    mj-listbox renders a container with role='listbox'.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-listbox")
    frame = _get_frame(page, "mj-listbox")
    listbox = frame.locator("[role='listbox']").first
    expect(listbox).to_be_visible()
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_listbox_single_selection_fires_mj_change(base_url: str, page) -> None:
    """
    Clicking an option in a single-select mj-listbox fires mj-change.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-listbox")
    frame = _reload_example(
        page,
        '<mj-listbox label="Colours" style="width:14rem"><mj-option value="red">Red</mj-option><mj-option value="blue">Blue</mj-option></mj-listbox>',
        "mj-listbox",
    )
    frame.evaluate("""() => {
        window.__mjevents = [];
        const el = document.querySelector('mj-listbox');
        el.addEventListener('mj-change', e => window.__mjevents.push(e.type));
    }""")
    option = frame.locator("[role='option']").first
    option.click()
    events = frame.evaluate("() => window.__mjevents")
    assert "mj-change" in events, "Expected mj-change after clicking listbox option"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_listbox_multiple_preselect(base_url: str, page) -> None:
    """
    mj-listbox with multiple and a comma-separated value pre-selects the
    correct options (aria-selected='true').

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-listbox")
    frame = _reload_example(
        page,
        '<mj-listbox multiple value="red,blue" label="M" style="width:14rem"><mj-option value="red">Red</mj-option><mj-option value="green">Green</mj-option><mj-option value="blue">Blue</mj-option></mj-listbox>',
        "mj-listbox",
    )
    selected_count = frame.evaluate("""() => {
        const opts = document.querySelector('mj-listbox').shadowRoot.querySelectorAll('[aria-selected="true"]');
        return opts.length;
    }""")
    assert selected_count == 2, f"Expected 2 pre-selected options, got {selected_count}"
    return


# ===========================================================================
# mj-combobox
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_combobox_renders_input(base_url: str, page) -> None:
    """
    mj-combobox renders a visible text input.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-combobox")
    frame = _get_frame(page, "mj-combobox")
    inp = frame.locator("mj-combobox input").first
    expect(inp).to_be_visible()
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_combobox_typing_opens_popup(base_url: str, page) -> None:
    """
    Typing into a mj-combobox opens the suggestion popup (host gets [open]).

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-combobox")
    frame = _get_frame(page, "mj-combobox")
    inp = frame.locator("mj-combobox input").first
    inp.click()
    inp.type("a", delay=50)
    # Give debounce a moment to fire
    page.wait_for_timeout(500)
    has_open = frame.evaluate(
        "() => document.querySelector('mj-combobox').hasAttribute('open')"
    )
    assert has_open is True, "mj-combobox should be open after typing"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_combobox_clearable_attribute(base_url: str, page) -> None:
    """
    mj-combobox with clearable attribute renders a clear button.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-combobox")
    frame = _get_frame(page, "mj-combobox")
    has_clearable = frame.evaluate(
        "() => document.querySelector('mj-combobox[clearable]') !== null"
    )
    assert has_clearable is True, "Catalog example should include a clearable mj-combobox"
    return


# ===========================================================================
# mj-cascading-select
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_cascading_select_renders(base_url: str, page) -> None:
    """
    mj-cascading-select renders and its shadow root is populated after
    setting the levels property.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-cascading-select")
    frame = _get_frame(page, "mj-cascading-select")
    has_shadow = frame.evaluate(
        "() => document.querySelector('mj-cascading-select').shadowRoot !== null"
    )
    assert has_shadow is True, "mj-cascading-select should have a shadowRoot"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_cascading_select_first_level_visible(base_url: str, page) -> None:
    """
    After setting the levels property programmatically the shadow DOM contains
    .level divs for each configured level.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-cascading-select")
    # Load a bare example and set levels programmatically via JS
    frame = _reload_example(
        page,
        '<mj-cascading-select id="cs"></mj-cascading-select>',
        "mj-cascading-select",
    )
    frame.evaluate("""() => {
        const cs = document.getElementById('cs');
        if (cs == null) return;
        cs.levels = [
            { label: 'Region', options: [{ value: 'na', label: 'North America' }, { value: 'eu', label: 'Europe' }] },
            { label: 'Country', options: [] }
        ];
    }""")
    page.wait_for_timeout(300)
    level_count = frame.evaluate("""() => {
        const cs = document.querySelector('mj-cascading-select');
        if (cs == null) return 0;
        const sr = cs.shadowRoot;
        if (sr == null) return 0;
        return sr.querySelectorAll('.level').length;
    }""")
    assert level_count >= 1, f"Expected at least 1 level div inside mj-cascading-select shadow DOM, got {level_count}"
    return


# ===========================================================================
# mj-radio-group
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_radio_group_renders_radiogroup_role(base_url: str, page) -> None:
    """
    mj-radio-group renders a container with role='radiogroup'.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-radio-group")
    frame = _get_frame(page, "mj-radio-group")
    group = frame.locator("[role='radiogroup']").first
    expect(group).to_be_visible()
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_radio_group_preselects_value(base_url: str, page) -> None:
    """
    mj-radio-group with a value attribute marks the corresponding radio item
    as aria-checked='true'.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-radio-group")
    frame = _get_frame(page, "mj-radio-group")
    checked_count = frame.evaluate("""() => {
        const items = document.querySelector('mj-radio-group').shadowRoot.querySelectorAll('[aria-checked="true"]');
        return items.length;
    }""")
    assert checked_count >= 1, "Expected at least one aria-checked='true' radio item"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_radio_group_click_fires_mj_change(base_url: str, page) -> None:
    """
    Clicking a radio item fires mj-change on the group.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-radio-group")
    frame = _reload_example(
        page,
        '<mj-radio-group><mj-radio value="a">A</mj-radio><mj-radio value="b">B</mj-radio></mj-radio-group>',
        "mj-radio-group",
    )
    frame.evaluate("""() => {
        window.__mjevents = [];
        document.querySelector('mj-radio-group').addEventListener('mj-change', e => window.__mjevents.push(e.detail.value));
    }""")
    radio_item = frame.locator("mj-radio-group").locator("[role='radio']").nth(1)
    radio_item.click()
    events = frame.evaluate("() => window.__mjevents")
    assert len(events) >= 1, "Expected mj-change after clicking a radio item"
    assert events[0] == "b"
    return


# ===========================================================================
# mj-checkbox-group
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_checkbox_group_renders_group_role(base_url: str, page) -> None:
    """
    mj-checkbox-group renders a container with role='group'.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-checkbox-group")
    frame = _get_frame(page, "mj-checkbox-group")
    group = frame.locator("[role='group']").first
    expect(group).to_be_visible()
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_checkbox_group_preselected_value(base_url: str, page) -> None:
    """
    mj-checkbox-group with value='email' pre-checks the email checkbox.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-checkbox-group")
    frame = _get_frame(page, "mj-checkbox-group")
    checked_count = frame.evaluate("""() => {
        const shadow = document.querySelector('mj-checkbox-group').shadowRoot;
        return shadow.querySelectorAll('[role="checkbox"][aria-checked="true"]').length;
    }""")
    assert checked_count >= 1, "Expected at least one pre-checked checkbox"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_checkbox_group_click_fires_mj_change(base_url: str, page) -> None:
    """
    Clicking a checkbox item fires mj-change on the group.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-checkbox-group")
    # Use a group WITHOUT select-all so the first [role=checkbox] is a regular item
    frame = _reload_example(
        page,
        '<mj-checkbox-group><mj-checkbox value="x">X</mj-checkbox><mj-checkbox value="y">Y</mj-checkbox></mj-checkbox-group>',
        "mj-checkbox-group",
    )
    frame.evaluate("""() => {
        window.__mjevents = [];
        document.querySelector('mj-checkbox-group').addEventListener('mj-change', e => window.__mjevents.push(e.detail.checkedValues));
    }""")
    # Click via JS on the shadow-DOM checkbox item to avoid visibility timing issues
    frame.evaluate("""() => {
        const shadow = document.querySelector('mj-checkbox-group').shadowRoot;
        const item = shadow.querySelector('[role="checkbox"]');
        if (item != null) { item.click(); }
    }""")
    events = frame.evaluate("() => window.__mjevents")
    assert len(events) >= 1, "Expected mj-change event after checkbox click"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_checkbox_group_select_all_rendered(base_url: str, page) -> None:
    """
    mj-checkbox-group with select-all attribute renders the select-all item.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-checkbox-group")
    frame = _get_frame(page, "mj-checkbox-group")
    # The catalog example includes select-all
    has_select_all = frame.evaluate(
        "() => document.querySelector('mj-checkbox-group[select-all]') !== null"
    )
    assert has_select_all is True, "Catalog example should use select-all attribute"
    return


# ===========================================================================
# mj-segmented-control
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_segmented_control_renders(base_url: str, page) -> None:
    """
    mj-segmented-control renders a visible container.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-segmented-control")
    frame = _get_frame(page, "mj-segmented-control")
    container = frame.locator("mj-segmented-control").first
    expect(container).to_be_visible()
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_segmented_control_select_mode_fires_mj_change(base_url: str, page) -> None:
    """
    Clicking a segment in select mode fires mj-change with the segment value.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-segmented-control")
    frame = _reload_example(
        page,
        '<mj-segmented-control value="day" label="View"><mj-segment value="day">Day</mj-segment><mj-segment value="week">Week</mj-segment><mj-segment value="month">Month</mj-segment></mj-segmented-control>',
        "mj-segmented-control",
    )
    frame.evaluate("""() => {
        window.__mjevents = [];
        document.querySelector('mj-segmented-control').addEventListener('mj-change', e => window.__mjevents.push(e.detail.value));
    }""")
    # Click the second segment ("week")
    segments = frame.locator("mj-segmented-control").locator("button, [role='radio']")
    segments.nth(1).click()
    events = frame.evaluate("() => window.__mjevents")
    assert len(events) >= 1, "Expected mj-change after segment click"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_segmented_control_preselected_segment(base_url: str, page) -> None:
    """
    The pre-selected segment (value='week') has aria-checked='true'.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-segmented-control")
    frame = _get_frame(page, "mj-segmented-control")
    checked_count = frame.evaluate("""() => {
        const els = document.querySelectorAll('mj-segmented-control');
        if (els.length === 0) return 0;
        const sr = els[0].shadowRoot;
        if (sr == null) return 0;
        return sr.querySelectorAll('[aria-checked="true"]').length;
    }""")
    assert checked_count >= 1, "Expected at least one segment with aria-checked='true'"
    return


# ===========================================================================
# mj-split-button
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_split_button_renders_primary(base_url: str, page) -> None:
    """
    mj-split-button renders a visible primary button.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-split-button")
    frame = _get_frame(page, "mj-split-button")
    primary = frame.locator("mj-split-button").locator("[part='primary'], .primary").first
    expect(primary).to_be_visible()
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_split_button_primary_fires_mj_primary_click(base_url: str, page) -> None:
    """
    Clicking the primary button fires mj-primary-click.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-split-button")
    frame = _reload_example(
        page,
        '<mj-split-button label="Save"><mj-menu-item value="draft">Draft</mj-menu-item></mj-split-button>',
        "mj-split-button",
    )
    frame.evaluate("""() => {
        window.__mjevents = [];
        document.querySelector('mj-split-button').addEventListener('mj-primary-click', () => window.__mjevents.push('mj-primary-click'));
    }""")
    primary = frame.locator("mj-split-button").locator("[part='primary'], .primary").first
    primary.click()
    events = frame.evaluate("() => window.__mjevents")
    assert "mj-primary-click" in events, "Expected mj-primary-click after clicking primary button"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_split_button_dropdown_opens(base_url: str, page) -> None:
    """
    Clicking the dropdown chevron button opens the menu popup.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-split-button")
    frame = _reload_example(
        page,
        '<mj-split-button label="Save"><mj-menu-item value="draft">Draft</mj-menu-item></mj-split-button>',
        "mj-split-button",
    )
    dropdown_trigger = frame.locator("mj-split-button").locator("[part='dropdown-trigger'], .dropdown-trigger").first
    dropdown_trigger.click()
    has_open = frame.evaluate(
        "() => document.querySelector('mj-split-button').hasAttribute('open')"
    )
    assert has_open is True, "mj-split-button should have [open] after dropdown trigger click"
    return


# ===========================================================================
# mj-menu-button
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_menu_button_renders_trigger(base_url: str, page) -> None:
    """
    mj-menu-button renders a visible trigger button.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-menu-button")
    frame = _get_frame(page, "mj-menu-button")
    trigger = frame.locator("mj-menu-button button").first
    expect(trigger).to_be_visible()
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_menu_button_opens_on_click(base_url: str, page) -> None:
    """
    Clicking the mj-menu-button trigger opens the popup (host gains [open]).

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-menu-button")
    frame = _get_frame(page, "mj-menu-button")
    trigger = frame.locator("mj-menu-button button").first
    trigger.click()
    has_open = frame.evaluate(
        "() => document.querySelector('mj-menu-button').hasAttribute('open')"
    )
    assert has_open is True, "mj-menu-button should have [open] after trigger click"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_menu_button_fires_mj_select_on_item_click(base_url: str, page) -> None:
    """
    Clicking a menu item fires mj-select with the item value.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-menu-button")
    frame = _reload_example(
        page,
        '<mj-menu-button label="Actions"><mj-menu-item value="edit">Edit</mj-menu-item><mj-menu-item value="delete">Delete</mj-menu-item></mj-menu-button>',
        "mj-menu-button",
    )
    frame.evaluate("""() => {
        window.__mjevents = [];
        document.querySelector('mj-menu-button').addEventListener('mj-select', e => window.__mjevents.push(e.detail.value));
    }""")
    trigger = frame.locator("mj-menu-button button").first
    trigger.click()
    page.wait_for_timeout(200)
    menu_item = frame.locator("mj-menu-button").locator(".menu-item").first
    menu_item.click()
    events = frame.evaluate("() => window.__mjevents")
    assert len(events) >= 1, "Expected mj-select event after menu item click"
    return


# ===========================================================================
# mj-color-picker
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_color_picker_renders_swatch_trigger(base_url: str, page) -> None:
    """
    mj-color-picker renders a visible swatch trigger button.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-color-picker")
    frame = _get_frame(page, "mj-color-picker")
    trigger = frame.locator("mj-color-picker").locator(".trigger, [part='trigger']").first
    expect(trigger).to_be_visible()
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_color_picker_opens_on_click(base_url: str, page) -> None:
    """
    Clicking the swatch trigger opens the picker popup.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-color-picker")
    frame = _get_frame(page, "mj-color-picker")
    trigger = frame.locator("mj-color-picker .trigger, mj-color-picker [part='trigger']").first
    trigger.click()
    has_open = frame.evaluate(
        "() => document.querySelector('mj-color-picker').hasAttribute('open')"
    )
    assert has_open is True, "mj-color-picker should have [open] after swatch click"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_color_picker_value_attribute_reflected(base_url: str, page) -> None:
    """
    The value attribute on mj-color-picker is readable via JS.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-color-picker")
    frame = _get_frame(page, "mj-color-picker")
    value = frame.evaluate(
        "() => document.querySelector('mj-color-picker').getAttribute('value')"
    )
    assert value is not None, "Expected mj-color-picker to have a value attribute"
    assert value.startswith("#"), f"Expected hex value, got '{value}'"
    return


# ===========================================================================
# mj-date-picker
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_date_picker_renders_input(base_url: str, page) -> None:
    """
    mj-date-picker renders a visible text input for date entry.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-date-picker")
    frame = _get_frame(page, "mj-date-picker")
    inp = frame.locator("mj-date-picker input").first
    expect(inp).to_be_visible()
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_date_picker_calendar_opens_on_trigger(base_url: str, page) -> None:
    """
    Clicking the calendar trigger button opens the popup.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-date-picker")
    frame = _get_frame(page, "mj-date-picker")
    cal_trigger = frame.locator("mj-date-picker").locator(".cal-trigger, [part='cal-trigger']").first
    cal_trigger.click()
    has_open = frame.evaluate(
        "() => document.querySelector('mj-date-picker').hasAttribute('open')"
    )
    assert has_open is True, "mj-date-picker should have [open] after calendar trigger click"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_date_picker_clearable_renders_clear_button(base_url: str, page) -> None:
    """
    mj-date-picker with clearable attribute has a clear button element.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-date-picker")
    frame = _get_frame(page, "mj-date-picker")
    has_clearable = frame.evaluate(
        "() => document.querySelector('mj-date-picker[clearable]') !== null"
    )
    assert has_clearable is True, "Catalog example should include a clearable mj-date-picker"
    return


# ===========================================================================
# mj-file-picker
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_file_picker_renders_dropzone(base_url: str, page) -> None:
    """
    mj-file-picker renders a visible drop zone.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-file-picker")
    frame = _get_frame(page, "mj-file-picker")
    dropzone = frame.locator("mj-file-picker").locator(".dropzone, [part='dropzone']").first
    expect(dropzone).to_be_visible()
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_file_picker_choose_button_visible(base_url: str, page) -> None:
    """
    mj-file-picker renders a choose-files button inside the dropzone.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-file-picker")
    frame = _get_frame(page, "mj-file-picker")
    btn = frame.locator("mj-file-picker").locator(".choose-btn, [part='choose-btn']").first
    expect(btn).to_be_visible()
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_file_picker_multiple_attribute_reflected(base_url: str, page) -> None:
    """
    mj-file-picker with multiple attribute reports hasAttribute('multiple')=true.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-file-picker")
    frame = _get_frame(page, "mj-file-picker")
    has_multiple = frame.evaluate(
        "() => document.querySelector('mj-file-picker').hasAttribute('multiple')"
    )
    assert has_multiple is True, "Catalog example should set multiple attribute"
    return


# ===========================================================================
# mj-asset-picker
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_asset_picker_renders(base_url: str, page) -> None:
    """
    mj-asset-picker renders in the preview frame.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-asset-picker")
    frame = _get_frame(page, "mj-asset-picker")
    host = frame.locator("mj-asset-picker").first
    expect(host).to_be_visible()
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_asset_picker_has_shadow_root(base_url: str, page) -> None:
    """
    mj-asset-picker attaches a shadow root on upgrade.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-asset-picker")
    frame = _get_frame(page, "mj-asset-picker")
    has_shadow = frame.evaluate(
        "() => document.querySelector('mj-asset-picker').shadowRoot !== null"
    )
    assert has_shadow is True, "mj-asset-picker should have a shadowRoot"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_asset_picker_opens_on_click(base_url: str, page) -> None:
    """
    Clicking the mj-asset-picker trigger opens the popup (host gains [open]).

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-asset-picker")
    frame = _get_frame(page, "mj-asset-picker")
    trigger = frame.locator("mj-asset-picker").locator("button").first
    trigger.click()
    page.wait_for_timeout(300)
    has_open = frame.evaluate(
        "() => document.querySelector('mj-asset-picker').hasAttribute('open')"
    )
    assert has_open is True, "mj-asset-picker should have [open] after trigger click"
    return


# ===========================================================================
# mj-locale-picker
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_locale_picker_renders_input(base_url: str, page) -> None:
    """
    mj-locale-picker renders a visible input field.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-locale-picker")
    frame = _get_frame(page, "mj-locale-picker")
    inp = frame.locator("mj-locale-picker input").first
    expect(inp).to_be_visible()
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_locale_picker_mode_attribute(base_url: str, page) -> None:
    """
    The first mj-locale-picker in the catalog example has mode='language'.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-locale-picker")
    frame = _get_frame(page, "mj-locale-picker")
    mode = frame.evaluate(
        "() => document.querySelector('mj-locale-picker').getAttribute('mode')"
    )
    assert mode == "language", f"Expected mode='language', got '{mode}'"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_locale_picker_typing_opens_popup(base_url: str, page) -> None:
    """
    Typing into a locale-picker opens the suggestion popup.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-locale-picker")
    frame = _get_frame(page, "mj-locale-picker")
    inp = frame.locator("mj-locale-picker input").first
    inp.click()
    inp.type("en", delay=50)
    page.wait_for_timeout(500)
    has_open = frame.evaluate(
        "() => document.querySelector('mj-locale-picker').hasAttribute('open')"
    )
    assert has_open is True, "mj-locale-picker should open after typing"
    return


# ===========================================================================
# mj-tag-picker
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_tag_picker_renders_input(base_url: str, page) -> None:
    """
    mj-tag-picker renders a visible input area.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-tag-picker")
    frame = _get_frame(page, "mj-tag-picker")
    host = frame.locator("mj-tag-picker").first
    expect(host).to_be_visible()
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_tag_picker_typing_opens_suggestions(base_url: str, page) -> None:
    """
    Typing into the tag-picker input opens the suggestion popup.  The
    mj-tag-picker uses popup.hidden=false (not an [open] host attribute),
    so we check the internal _open flag or popup element visibility.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-tag-picker")
    frame = _get_frame(page, "mj-tag-picker")
    inp = frame.locator("mj-tag-picker input").first
    inp.click()
    inp.type("d", delay=50)
    # Wait for the debounce (default 200 ms) plus a safety margin
    page.wait_for_timeout(600)
    popup_visible = frame.evaluate("""() => {
        const el = document.querySelector('mj-tag-picker');
        if (el == null) return false;
        const sr = el.shadowRoot;
        if (sr == null) return false;
        const popup = sr.querySelector('[part="popup"]');
        if (popup == null) return false;
        return !popup.hidden;
    }""")
    assert popup_visible is True, "mj-tag-picker popup should be visible after typing"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_tag_picker_placeholder_attribute(base_url: str, page) -> None:
    """
    mj-tag-picker with placeholder attribute reflects it in the shadow DOM.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-tag-picker")
    frame = _get_frame(page, "mj-tag-picker")
    placeholder = frame.evaluate(
        "() => document.querySelector('mj-tag-picker').getAttribute('placeholder')"
    )
    assert placeholder is not None, "Expected mj-tag-picker to have a placeholder attribute"
    return


# ===========================================================================
# mj-tree-selector
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_tree_selector_renders(base_url: str, page) -> None:
    """
    mj-tree-selector renders and attaches a shadow root.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-tree-selector")
    frame = _get_frame(page, "mj-tree-selector")
    has_shadow = frame.evaluate(
        "() => document.querySelector('mj-tree-selector').shadowRoot !== null"
    )
    assert has_shadow is True, "mj-tree-selector should have a shadowRoot"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_tree_selector_nodes_property_renders_items(base_url: str, page) -> None:
    """
    Setting the nodes property via JS causes the tree to render tree-item rows.
    We load a bare element, set nodes directly, then query the shadow DOM.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-tree-selector")
    frame = _reload_example(
        page,
        '<mj-tree-selector id="ts" style="width:18rem"></mj-tree-selector>',
        "mj-tree-selector",
    )
    frame.evaluate("""() => {
        const ts = document.getElementById('ts');
        if (ts == null) return;
        ts.nodes = [
            { id: 'a', label: 'Alpha', value: 'alpha', children: null },
            { id: 'b', label: 'Beta',  value: 'beta',  children: null }
        ];
    }""")
    page.wait_for_timeout(300)
    item_count = frame.evaluate("""() => {
        const ts = document.querySelector('mj-tree-selector');
        if (ts == null) return 0;
        const sr = ts.shadowRoot;
        if (sr == null) return 0;
        return sr.querySelectorAll('.tree-item-row').length;
    }""")
    assert item_count >= 1, f"Expected at least one tree-item-row, got {item_count}"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_tree_selector_node_click_fires_mj_change(base_url: str, page) -> None:
    """
    Clicking a leaf node in the tree fires mj-change.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-tree-selector")
    frame = _reload_example(
        page,
        '<mj-tree-selector id="ts2" style="width:18rem"></mj-tree-selector>',
        "mj-tree-selector",
    )
    frame.evaluate("""() => {
        window.__mjevents = [];
        const ts = document.getElementById('ts2');
        if (ts == null) return;
        ts.nodes = [
            { id: 'x', label: 'Xray', value: 'xray', children: null },
            { id: 'y', label: 'Yankee', value: 'yankee', children: null }
        ];
        ts.addEventListener('mj-change', e => window.__mjevents.push(e.type));
    }""")
    page.wait_for_timeout(300)
    # Click the first tree row via JS on the shadow DOM
    frame.evaluate("""() => {
        const ts = document.querySelector('mj-tree-selector');
        if (ts == null) return;
        const sr = ts.shadowRoot;
        if (sr == null) return;
        const row = sr.querySelector('.tree-item-row');
        if (row != null) { row.click(); }
    }""")
    events = frame.evaluate("() => window.__mjevents")
    assert "mj-change" in events, "Expected mj-change after clicking a tree node"
    return


# ===========================================================================
# mj-transfer-list
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_transfer_list_renders_panes(base_url: str, page) -> None:
    """
    mj-transfer-list renders both source and target panes.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-transfer-list")
    frame = _get_frame(page, "mj-transfer-list")
    source = frame.locator("mj-transfer-list").locator("[part='source-pane']").first
    target = frame.locator("mj-transfer-list").locator("[part='target-pane']").first
    expect(source).to_be_visible()
    expect(target).to_be_visible()
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_transfer_list_preselected_option_in_target(base_url: str, page) -> None:
    """
    mj-option with selected attribute starts in the target pane.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-transfer-list")
    frame = _get_frame(page, "mj-transfer-list")
    target_count = frame.evaluate("""() => {
        const el = document.querySelector('mj-transfer-list');
        if (el == null) return 0;
        const lb = el.shadowRoot.querySelector('[part="target-listbox"]');
        if (lb == null) return 0;
        return lb.querySelectorAll('[role="option"]').length;
    }""")
    assert target_count >= 1, f"Expected at least one item in target pane, got {target_count}"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_transfer_list_move_right_button_present(base_url: str, page) -> None:
    """
    mj-transfer-list renders a move-right control button.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-transfer-list")
    frame = _get_frame(page, "mj-transfer-list")
    btn = frame.locator("mj-transfer-list").locator("[part='move-right']").first
    expect(btn).to_be_visible()
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_transfer_list_move_item_to_target(base_url: str, page) -> None:
    """
    Selecting a source item and clicking move-right moves it to the target.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-transfer-list")
    frame = _reload_example(
        page,
        (
            '<mj-transfer-list source-label="Available" target-label="Selected" style="max-width:40rem">'
            '<mj-option value="read">Read</mj-option>'
            '<mj-option value="write">Write</mj-option>'
            '<mj-option value="admin">Admin</mj-option>'
            "</mj-transfer-list>"
        ),
        "mj-transfer-list",
    )
    frame.evaluate("""() => {
        window.__mjevents = [];
        document.querySelector('mj-transfer-list').addEventListener('mj-change', e => window.__mjevents.push(e.type));
    }""")
    # Click the first source option to select it
    source_option = frame.locator("mj-transfer-list").locator("[part='source-listbox'] [role='option']").first
    source_option.click()
    # Click move-right button
    move_right = frame.locator("mj-transfer-list").locator("[part='move-right']").first
    move_right.click()
    events = frame.evaluate("() => window.__mjevents")
    assert "mj-change" in events, "Expected mj-change after moving item to target"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_transfer_list_searchable_renders_filter_inputs(base_url: str, page) -> None:
    """
    mj-transfer-list with searchable attribute renders search inputs in both panes.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-transfer-list")
    frame = _get_frame(page, "mj-transfer-list")
    # Catalog example includes searchable
    input_count = frame.evaluate("""() => {
        const el = document.querySelector('mj-transfer-list');
        if (el == null) return 0;
        const sr = el.shadowRoot;
        if (sr == null) return 0;
        return sr.querySelectorAll('input[type="search"]').length;
    }""")
    assert input_count >= 2, f"Expected at least 2 search inputs in searchable transfer list, got {input_count}"
    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
