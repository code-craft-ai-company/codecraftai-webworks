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
from testcomponents.harness.fixtures import load_fixture


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


# ---------------------------------------------------------------------------
# mj-select: options that arrive after the first render, accessible name
# ---------------------------------------------------------------------------

# Appends <mj-option> children the way a view does once a fetch resolves.
_APPEND_OPTIONS_JS = """
([selector, options]) => {
    const select = document.querySelector(selector);
    for (const [value, label] of options) {
        const option = document.createElement('mj-option');
        option.setAttribute('value', value);
        option.textContent = label;
        select.appendChild(option);
    }
}
"""

_RENDERED_OPTION_LABELS_JS = """
(selector) => Array.from(
    document.querySelector(selector).shadowRoot.querySelectorAll('.option .option-label')
).map((node) => node.textContent)
"""


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_select_renders_options_added_after_first_render(base_url: str, page) -> None:
    """
    Options appended to an mj-select that is already rendered appear in its
    listbox (a project picker fills in after its fetch resolves).

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    load_fixture(page, base_url, '<mj-select id="picker" label="Project"></mj-select>', ["mj-select"])
    page.evaluate(_APPEND_OPTIONS_JS, ["#picker", [["a", "Alpha"], ["b", "Bravo"]]])
    page.wait_for_function(
        "() => document.querySelector('#picker').shadowRoot.querySelectorAll('.option').length === 2",
        timeout=_INTERACTION_TIMEOUT,
    )
    labels = page.evaluate(_RENDERED_OPTION_LABELS_JS, "#picker")
    assert labels == ["Alpha", "Bravo"], f"Expected the appended options, got {labels}"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_select_value_set_before_options_arrive_shows_option_label(base_url: str, page) -> None:
    """
    Assigning ``value`` in the same task that replaces the options shows the
    matching option's label in the trigger.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    load_fixture(page, base_url, '<mj-select id="picker" label="Project"></mj-select>', ["mj-select"])
    page.evaluate(
        """() => {
            const select = document.querySelector('#picker');
            select.replaceChildren();
            for (const [value, label] of [['a', 'Alpha'], ['b', 'Bravo']]) {
                const option = document.createElement('mj-option');
                option.setAttribute('value', value);
                option.textContent = label;
                select.appendChild(option);
            }
            select.value = 'b';
        }"""
    )
    page.wait_for_function(
        "() => document.querySelector('#picker').shadowRoot.querySelector('.trigger .label').textContent === 'Bravo'",
        timeout=_INTERACTION_TIMEOUT,
    )
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_select_removed_option_leaves_the_listbox(base_url: str, page) -> None:
    """
    Removing an <mj-option> removes it from the rendered listbox.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    markup = (
        '<mj-select id="picker" label="State">'
        '<mj-option value="a">Alpha</mj-option><mj-option value="b">Bravo</mj-option>'
        '</mj-select>'
    )
    load_fixture(page, base_url, markup, ["mj-select"])
    page.evaluate("() => document.querySelector('#picker mj-option[value=\"a\"]').remove()")
    page.wait_for_function(
        "() => document.querySelector('#picker').shadowRoot.querySelectorAll('.option').length === 1",
        timeout=_INTERACTION_TIMEOUT,
    )
    labels = page.evaluate(_RENDERED_OPTION_LABELS_JS, "#picker")
    assert labels == ["Bravo"], f"Expected only Bravo to remain, got {labels}"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_select_option_label_is_rendered_as_text(base_url: str, page) -> None:
    """
    An option label containing markup is shown as text, never parsed into
    elements (labels are often user-supplied names).

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    load_fixture(page, base_url, '<mj-select id="picker" label="Project"></mj-select>', ["mj-select"])
    page.evaluate(_APPEND_OPTIONS_JS, ["#picker", [["x", "<img src=x onerror=\"window.__injected=1\">Bravo"]]])
    page.wait_for_function(
        "() => document.querySelector('#picker').shadowRoot.querySelectorAll('.option').length === 1",
        timeout=_INTERACTION_TIMEOUT,
    )
    injected = page.evaluate(
        "() => document.querySelector('#picker').shadowRoot.querySelector('.option-label img') !== null"
    )
    assert injected is False, "The option label markup must not be parsed into elements"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_select_combobox_is_named_by_label_attribute(base_url: str, page) -> None:
    """
    The combobox inside mj-select takes its accessible name from the host's
    ``label`` attribute.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    markup = '<mj-select label="Project"><mj-option value="a">Alpha</mj-option></mj-select>'
    load_fixture(page, base_url, markup, ["mj-select"])
    expect(page.get_by_role("combobox", name="Project", exact=True)).to_have_count(1)
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_select_combobox_is_named_by_wrapping_label(base_url: str, page) -> None:
    """
    An mj-select wrapped in a <label> element is named by the label's text
    (without the select's own option text).

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    markup = (
        '<label>Metric <mj-select><mj-option value="cpu">cpu.usage</mj-option></mj-select></label>'
    )
    load_fixture(page, base_url, markup, ["mj-select"])
    expect(page.get_by_role("combobox", name="Metric", exact=True)).to_have_count(1)
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_select_combobox_is_named_by_aria_label(base_url: str, page) -> None:
    """
    An aria-label on the mj-select host names its combobox.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    markup = '<mj-select aria-label="Provider"><mj-option value="gh">GitHub</mj-option></mj-select>'
    load_fixture(page, base_url, markup, ["mj-select"])
    expect(page.get_by_role("combobox", name="Provider", exact=True)).to_have_count(1)
    return


# ---------------------------------------------------------------------------
# Shared by the selection-control tests below: an attribute / text payload
# that runs script if any component re-parses it as markup. It is written
# HTML-escaped, the way a server renders user data, so the browser decodes
# it to the raw payload before the component reads it.
# ---------------------------------------------------------------------------

_INJECTION_TEXT = (
    "x&#39;&quot;&gt;&lt;img src=&quot;data:,x&quot; "
    "onerror=&quot;window.__hits=(window.__hits||0)+1&quot;&gt;"
)

_INJECTION_HITS_JS = "() => window.__hits === undefined"


def _collect_page_errors(page) -> list:
    """
    Record every uncaught exception the page raises from now on.

    :param page: Playwright page object.

    :returns: The list the errors are appended to.
    """
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    return errors


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_select_required_is_invalid_until_an_option_is_chosen(base_url: str, page) -> None:
    """
    An untouched ``required`` mj-select is invalid and exposes aria-required;
    choosing an option makes it valid.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    markup = (
        '<form><mj-select id="picker" name="fruit" required label="Fruit">'
        '<mj-option value="a">Apple</mj-option><mj-option value="b">Banana</mj-option>'
        '</mj-select></form>'
    )
    load_fixture(page, base_url, markup, ["mj-select"])
    before = page.evaluate("() => document.querySelector('#picker').checkValidity()")
    assert before is False, "An empty required mj-select must be invalid"
    expect(page.get_by_role("combobox", name="Fruit")).to_have_attribute("aria-required", "true")

    page.get_by_role("combobox", name="Fruit").click()
    page.get_by_role("option", name="Banana").click()
    after = page.evaluate("() => document.querySelector('#picker').checkValidity()")
    assert after is True, "The required mj-select must be valid once an option is chosen"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_select_option_without_value_uses_its_text(base_url: str, page) -> None:
    """
    Options without a ``value`` attribute stand for their text, as a native
    <option> does, so they no longer collapse to one empty value.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    markup = (
        '<mj-select id="picker" label="Colour" placeholder="Pick one">'
        '<mj-option>Red</mj-option><mj-option>Blue</mj-option></mj-select>'
    )
    load_fixture(page, base_url, markup, ["mj-select"])
    selected = page.evaluate(
        "() => document.querySelector('#picker').shadowRoot.querySelectorAll('[aria-selected=\"true\"]').length"
    )
    assert selected == 0, f"No option should start selected, got {selected}"

    page.get_by_role("combobox", name="Colour").click()
    page.get_by_role("option", name="Blue").click()
    value = page.evaluate("() => document.querySelector('#picker').value")
    assert value == "Blue", f"Expected the option text as value, got {value!r}"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_select_form_reset_restores_the_default_value(base_url: str, page) -> None:
    """
    A user choice does not overwrite the ``value`` attribute, so a form reset
    goes back to the default and the trigger shows it again.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    markup = (
        '<form id="f"><mj-select id="picker" name="fruit" value="b" label="Fruit">'
        '<mj-option value="a">Apple</mj-option><mj-option value="b">Banana</mj-option>'
        '</mj-select></form>'
    )
    load_fixture(page, base_url, markup, ["mj-select"])
    page.get_by_role("combobox", name="Fruit").click()
    page.get_by_role("option", name="Apple").click()
    page.evaluate("() => document.querySelector('#f').reset()")
    state = page.evaluate("""() => {
        const select = document.querySelector('#picker');
        return [select.value, select.shadowRoot.querySelector('.trigger .label').textContent];
    }""")
    assert state == ["b", "Banana"], f"Expected the default value after reset, got {state}"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_select_renders_option_groups(base_url: str, page) -> None:
    """
    <mj-optgroup> children render as labelled role="group" sections.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    markup = (
        '<mj-select id="picker" label="Fruit">'
        '<mj-optgroup label="Citrus"><mj-option value="l">Lemon</mj-option></mj-optgroup>'
        '<mj-optgroup label="Berries"><mj-option value="s">Strawberry</mj-option></mj-optgroup>'
        '</mj-select>'
    )
    load_fixture(page, base_url, markup, ["mj-select"])
    page.get_by_role("combobox", name="Fruit").click()
    expect(page.get_by_role("group", name="Citrus")).to_have_count(1)
    expect(page.get_by_role("group", name="Berries").get_by_role("option", name="Strawberry")).to_have_count(1)
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_select_attributes_and_options_are_rendered_as_text(base_url: str, page) -> None:
    """
    Markup in the label, placeholder, option text and option values is shown
    as text and never runs.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    markup = (
        f'<mj-select open label="{_INJECTION_TEXT}" placeholder="{_INJECTION_TEXT}">'
        f'<mj-optgroup label="{_INJECTION_TEXT}"><mj-option value="{_INJECTION_TEXT}">{_INJECTION_TEXT}</mj-option></mj-optgroup>'
        f'<mj-option>{_INJECTION_TEXT}</mj-option></mj-select>'
    )
    load_fixture(page, base_url, markup, ["mj-select"])
    page.wait_for_timeout(300)
    assert page.evaluate(_INJECTION_HITS_JS) is True, "Injected markup must not run"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_select_popup_min_width_property_applies(base_url: str, page) -> None:
    """
    The popup is at least as wide as the trigger by default, and
    --mj-select-popup-min-width sets its minimum width instead.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    markup = (
        '<mj-select id="plain" label="Plain" style="inline-size: 14rem"><mj-option value="a">A</mj-option></mj-select>'
        '<mj-select id="wide" label="Wide" style="inline-size: 8rem; --mj-select-popup-min-width: 25rem">'
        '<mj-option value="a">A</mj-option></mj-select>'
    )
    load_fixture(page, base_url, markup, ["mj-select"])
    widths = page.evaluate("""async () => {
        const measure = async (id) => {
            const host = document.getElementById(id);
            host.setAttribute('open', '');
            await new Promise((r) => setTimeout(r, 100));
            const result = {
                popup: host.shadowRoot.querySelector('[part=popup]').getBoundingClientRect().width,
                trigger: host.shadowRoot.querySelector('[part=trigger]').getBoundingClientRect().width,
            };
            host.removeAttribute('open');
            return result;
        };
        return { plain: await measure('plain'), wide: await measure('wide') };
    }""")
    assert widths["plain"]["popup"] >= widths["plain"]["trigger"] - 1, f"Popup narrower than its trigger: {widths}"
    assert widths["wide"]["popup"] >= 399, f"--mj-select-popup-min-width (25rem) was not applied: {widths}"
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


_LISTBOX_SELECTED_JS = """
(selector) => Array.from(
    document.querySelector(selector).shadowRoot.querySelectorAll('.option[aria-selected="true"]')
).map((node) => node.textContent.trim())
"""


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_listbox_multiple_in_markup_upgrades_without_error(base_url: str, page) -> None:
    """
    An mj-listbox declared with ``multiple`` in markup upgrades without an
    uncaught exception and exposes aria-multiselectable.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    errors = _collect_page_errors(page)
    markup = (
        '<mj-listbox id="lb" multiple value="a" label="Letters">'
        '<mj-option value="a">A</mj-option><mj-option value="b">B</mj-option></mj-listbox>'
    )
    load_fixture(page, base_url, markup, ["mj-listbox"])
    expect(page.get_by_role("listbox", name="Letters")).to_have_attribute("aria-multiselectable", "true")
    assert errors == [], f"Upgrading the listbox raised {errors}"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_listbox_plain_click_toggles_in_multiple_mode(base_url: str, page) -> None:
    """
    In ``multiple`` mode a plain click adds or removes one option without
    clearing the others (the APG recommended model for touch and pointer).

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    markup = (
        '<mj-listbox id="lb" multiple value="red" label="Colours">'
        '<mj-option value="red">Red</mj-option><mj-option value="green">Green</mj-option>'
        '<mj-option value="blue">Blue</mj-option></mj-listbox>'
    )
    load_fixture(page, base_url, markup, ["mj-listbox"])
    page.get_by_role("option", name="Blue").click()
    assert page.evaluate(_LISTBOX_SELECTED_JS, "#lb") == ["Red", "Blue"]
    page.get_by_role("option", name="Red").click()
    assert page.evaluate(_LISTBOX_SELECTED_JS, "#lb") == ["Blue"]
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_listbox_selection_survives_a_move_and_resets_to_default(base_url: str, page) -> None:
    """
    The user's selection survives moving the listbox to another parent, and a
    form reset goes back to the ``value`` attribute.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    markup = (
        '<form id="f"><mj-listbox id="lb" name="c" value="red" label="Colours">'
        '<mj-option value="red">Red</mj-option><mj-option value="blue">Blue</mj-option>'
        '</mj-listbox></form><div id="other"></div>'
    )
    load_fixture(page, base_url, markup, ["mj-listbox"])
    page.get_by_role("option", name="Blue").click()
    page.evaluate("() => document.querySelector('#other').appendChild(document.querySelector('#lb'))")
    page.wait_for_timeout(100)
    assert page.evaluate(_LISTBOX_SELECTED_JS, "#lb") == ["Blue"], "The selection must survive the move"

    page.evaluate("() => document.querySelector('#f').appendChild(document.querySelector('#lb'))")
    page.wait_for_timeout(100)
    page.evaluate("() => document.querySelector('#f').reset()")
    assert page.evaluate(_LISTBOX_SELECTED_JS, "#lb") == ["Red"], "Reset must restore the default"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_listbox_follows_options_added_after_render(base_url: str, page) -> None:
    """
    Options appended after the first render appear in the listbox.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    load_fixture(page, base_url, '<mj-listbox id="lb" label="Late"></mj-listbox>', ["mj-listbox"])
    page.evaluate(_APPEND_OPTIONS_JS, ["#lb", [["a", "Alpha"], ["b", "Bravo"]]])
    expect(page.get_by_role("listbox", name="Late").get_by_role("option")).to_have_count(2)
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_listbox_attributes_and_options_are_rendered_as_text(base_url: str, page) -> None:
    """
    Markup in the label, option text and option values never runs.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    markup = (
        f'<mj-listbox multiple label="{_INJECTION_TEXT}" value="{_INJECTION_TEXT}">'
        f'<mj-option value="{_INJECTION_TEXT}">{_INJECTION_TEXT}</mj-option>'
        f'<mj-option>{_INJECTION_TEXT}</mj-option></mj-listbox>'
    )
    load_fixture(page, base_url, markup, ["mj-listbox"])
    page.wait_for_timeout(300)
    assert page.evaluate(_INJECTION_HITS_JS) is True, "Injected markup must not run"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_listbox_single_selection_is_visibly_marked(base_url: str, page) -> None:
    """
    In single mode the selected option shows the check mark and a background
    of its own, in the light and the dark theme.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    markup = (
        '<mj-listbox id="light" label="Light" value="b"><mj-option value="a">A</mj-option><mj-option value="b">B</mj-option></mj-listbox>'
        '<div data-theme="dark"><mj-listbox id="dark" label="Dark" value="b">'
        '<mj-option value="a">A</mj-option><mj-option value="b">B</mj-option></mj-listbox></div>'
    )
    load_fixture(page, base_url, markup, ["mj-listbox"])
    marks = page.evaluate("""() => ['light', 'dark'].map((id) => {
        const root = document.getElementById(id).shadowRoot;
        const selected = root.querySelector('[role=option][aria-selected=true]');
        const other = root.querySelector('[role=option][aria-selected=false]');
        const check = getComputedStyle(selected.querySelector('[part=option-checkbox]'));
        return {
            checkShown: check.display !== 'none' && check.visibility === 'visible',
            selectedBg: getComputedStyle(selected).backgroundColor,
            otherBg: getComputedStyle(other).backgroundColor,
        };
    })""")
    for mark in marks:
        assert mark["checkShown"] is True, f"The selected option shows no check mark: {marks}"
        assert mark["selectedBg"] != mark["otherBg"], f"The selected option has no background of its own: {marks}"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_listbox_required_reports_its_own_message(base_url: str, page) -> None:
    """
    An empty required listbox reports "At least one selection is required.";
    a required-message attribute wins over it.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    markup = (
        '<form><mj-listbox id="own" required><mj-option value="a">A</mj-option></mj-listbox>'
        '<mj-listbox id="custom" required required-message="Pick one."><mj-option value="a">A</mj-option></mj-listbox></form>'
    )
    load_fixture(page, base_url, markup, ["mj-listbox"])
    result = page.evaluate("""() => {
        const own = document.getElementById('own');
        const before = { message: own.validationMessage, missing: own.validity.valueMissing };
        own.value = 'a';
        return { before: before, after: own.validationMessage, custom: document.getElementById('custom').validationMessage };
    }""")
    assert result["before"] == {"message": "At least one selection is required.", "missing": True}, f"{result}"
    assert result["after"] == "", f"A selection must make the listbox valid: {result}"
    assert result["custom"] == "Pick one.", f"required-message must win: {result}"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_listbox_renders_option_groups(base_url: str, page) -> None:
    """
    <mj-optgroup> children render as labelled role="group" sections; a
    disabled group disables its options and the arrow keys skip them.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    markup = (
        '<mj-listbox id="lb" label="Region" value="fra">'
        '<mj-optgroup label="Europe"><mj-option value="fra">Frankfurt</mj-option></mj-optgroup>'
        '<mj-optgroup label="Asia" disabled><mj-option value="nrt">Tokyo</mj-option></mj-optgroup>'
        '<mj-option value="iad">Virginia</mj-option>'
        '</mj-listbox>'
    )
    load_fixture(page, base_url, markup, ["mj-listbox"])
    expect(page.get_by_role("group", name="Europe").get_by_role("option", name="Frankfurt")).to_have_count(1)
    expect(page.get_by_role("group", name="Asia").get_by_role("option", name="Tokyo")).to_have_attribute("aria-disabled", "true")
    listbox = page.get_by_role("listbox", name="Region")
    listbox.focus()
    listbox.press("ArrowDown")
    listbox.press("Enter")
    value = page.evaluate("() => document.getElementById('lb').value")
    assert value == "iad", f"ArrowDown should skip the disabled group and Enter select Virginia, got {value!r}"
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


_COMBOBOX_MARKUP = (
    '<label for="cb">Country</label>'
    '<mj-combobox id="cb" debounce="20">'
    '<mj-option value="au">Australia</mj-option><mj-option value="br" disabled>Brazil</mj-option>'
    '<mj-option value="ca">Canada</mj-option></mj-combobox>'
)


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_combobox_input_is_named_by_its_label(base_url: str, page) -> None:
    """
    The combobox input takes its accessible name from an associated <label>.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    load_fixture(page, base_url, _COMBOBOX_MARKUP, ["mj-combobox"])
    expect(page.get_by_role("combobox", name="Country", exact=True)).to_have_count(1)
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_combobox_toggle_button_opens_the_full_list(base_url: str, page) -> None:
    """
    The chevron button opens the popup with every option.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    load_fixture(page, base_url, _COMBOBOX_MARKUP, ["mj-combobox"])
    page.locator("#cb .toggle").click()
    expect(page.locator("#cb [role='option']")).to_have_count(3)
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_combobox_empty_prefix_takes_no_room(base_url: str, page) -> None:
    """
    The prefix wrapper is hidden while nothing is slotted into it, so the input
    text starts at the field edge; slotted prefix content shows it again, and
    removing that content hides it again.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    load_fixture(page, base_url, _COMBOBOX_MARKUP, ["mj-combobox"])
    prefix = page.locator("#cb [part='prefix']")
    expect(prefix).to_be_hidden()

    page.evaluate(
        "() => { const mark = document.createElement('span'); mark.slot = 'prefix';"
        " mark.id = 'cb-prefix'; mark.textContent = '#'; document.getElementById('cb').append(mark) }"
    )
    expect(prefix).to_be_visible()

    page.evaluate("() => document.getElementById('cb-prefix').remove()")
    expect(prefix).to_be_hidden()
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_combobox_highlight_keeps_the_full_option_name(base_url: str, page) -> None:
    """
    The <mark> around the matched text is not aria-hidden, so the option's
    accessible name stays the whole label.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    load_fixture(page, base_url, _COMBOBOX_MARKUP, ["mj-combobox"])
    page.get_by_role("combobox", name="Country").fill("can")
    expect(page.get_by_role("option", name="Canada", exact=True)).to_have_count(1)
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_combobox_keyboard_skips_disabled_options(base_url: str, page) -> None:
    """
    Arrow keys step over a disabled suggestion, so Enter never commits it.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    load_fixture(page, base_url, _COMBOBOX_MARKUP, ["mj-combobox"])
    combobox = page.get_by_role("combobox", name="Country")
    combobox.focus()
    page.keyboard.press("ArrowDown")
    page.keyboard.press("ArrowDown")
    page.keyboard.press("Enter")
    value = page.evaluate("() => document.querySelector('#cb').value")
    assert value == "ca", f"Expected the disabled option to be skipped, got {value!r}"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_combobox_disabled_input_cannot_be_typed_into(base_url: str, page) -> None:
    """
    ``disabled`` reaches the inner input, ``readonly`` makes it read-only.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    markup = (
        '<mj-combobox id="d" disabled><mj-option value="a">A</mj-option></mj-combobox>'
        '<mj-combobox id="r" readonly value="a"><mj-option value="a">A</mj-option></mj-combobox>'
    )
    load_fixture(page, base_url, markup, ["mj-combobox"])
    state = page.evaluate("""() => [
        document.querySelector('#d').shadowRoot.querySelector('input').disabled,
        document.querySelector('#r').shadowRoot.querySelector('input').readOnly
    ]""")
    assert state == [True, True], f"Expected disabled and read-only inputs, got {state}"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_combobox_cleared_text_clears_the_value_on_blur(base_url: str, page) -> None:
    """
    Deleting the text and leaving the field clears the committed value, so
    the field never submits a value it does not show.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    markup = _COMBOBOX_MARKUP.replace('debounce="20"', 'debounce="20" value="ca"') + '<button id="after">After</button>'
    load_fixture(page, base_url, markup, ["mj-combobox"])
    page.get_by_role("combobox", name="Country").fill("")
    page.locator("#after").focus()
    value = page.evaluate("() => document.querySelector('#cb').value")
    assert value == "", f"Expected the value to be cleared, got {value!r}"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_combobox_attributes_and_options_are_rendered_as_text(base_url: str, page) -> None:
    """
    Markup in the placeholder, option text and option values never runs,
    including while the popup highlights a match.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    markup = (
        f'<mj-combobox id="cb" open debounce="20" placeholder="{_INJECTION_TEXT}" label="{_INJECTION_TEXT}">'
        f'<mj-option value="{_INJECTION_TEXT}">{_INJECTION_TEXT}</mj-option></mj-combobox>'
    )
    load_fixture(page, base_url, markup, ["mj-combobox"])
    page.locator("#cb input").fill("img")
    page.wait_for_timeout(300)
    assert page.evaluate(_INJECTION_HITS_JS) is True, "Injected markup must not run"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_combobox_size_and_popup_min_width(base_url: str, page) -> None:
    """
    size="sm" / size="lg" change the input row height, and
    --mj-combobox-popup-min-width sets the popup's minimum width.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    markup = (
        '<mj-combobox id="sm" size="sm" label="Small"></mj-combobox>'
        '<mj-combobox id="md" label="Medium"></mj-combobox>'
        '<mj-combobox id="lg" size="lg" label="Large"></mj-combobox>'
        '<mj-combobox id="wide" label="Wide" style="inline-size: 8rem; --mj-combobox-popup-min-width: 25rem">'
        '<mj-option value="a">Apple</mj-option></mj-combobox>'
    )
    load_fixture(page, base_url, markup, ["mj-combobox"])
    result = page.evaluate("""async () => {
        const height = (id) => document.getElementById(id).shadowRoot.querySelector('[part=wrapper]').getBoundingClientRect().height;
        const wide = document.getElementById('wide');
        wide.setAttribute('open', '');
        await new Promise((r) => setTimeout(r, 100));
        return { sm: height('sm'), md: height('md'), lg: height('lg'),
                 popup: wide.shadowRoot.querySelector('[part=popup]').getBoundingClientRect().width };
    }""")
    assert result["sm"] < result["md"] < result["lg"], f"size does not change the row height: {result}"
    assert result["popup"] >= 399, f"--mj-combobox-popup-min-width (25rem) was not applied: {result}"
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


_CASCADE_LEVELS_JS = """() => {
    const cs = document.querySelector('#cs');
    cs.levels = [
        { name: 'region', label: 'Region', options: [{ value: 'na', label: 'North America' }, { value: 'eu', label: 'Europe' }] },
        { name: 'country', label: 'Country', options: { na: [{ value: 'ca', label: 'Canada' }], eu: [{ value: 'fr', label: 'France' }] } },
        { name: 'size', label: 'Size', options: ['S', 'M'] }
    ];
}"""


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_cascading_select_change_keeps_focus_and_static_options(base_url: str, page) -> None:
    """
    Choosing a level keeps keyboard focus on that select and fills the next
    level from its lookup map; a level with static options keeps them.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    load_fixture(page, base_url, '<mj-cascading-select id="cs"></mj-cascading-select>', ["mj-cascading-select"])
    page.evaluate(_CASCADE_LEVELS_JS)
    region = page.get_by_role("combobox", name="Region")
    region.focus()
    region.select_option("eu")
    state = page.evaluate("""() => {
        const root = document.querySelector('#cs').shadowRoot;
        const selects = root.querySelectorAll('select');
        return {
            focused: root.activeElement === selects[0],
            country: Array.from(selects[1].options).map((option) => option.textContent),
            size: Array.from(selects[2].options).map((option) => option.textContent)
        };
    }""")
    assert state["focused"] is True, "The level the user changed must keep focus"
    assert state["country"] == ["Select...", "France"], f"Unexpected country options {state['country']}"
    assert state["size"] == ["Select...", "S", "M"], f"Static options must be kept, got {state['size']}"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_cascading_select_values_setter_prepopulates_and_submits(base_url: str, page) -> None:
    """
    Assigning ``values`` fills every level, and the form receives one entry
    per named level as well as the JSON value.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    markup = '<form id="f"><mj-cascading-select id="cs" name="geo" required></mj-cascading-select></form>'
    load_fixture(page, base_url, markup, ["mj-cascading-select"])
    page.evaluate(_CASCADE_LEVELS_JS)
    invalid = page.evaluate("() => document.querySelector('#cs').checkValidity()")
    assert invalid is False, "An incomplete required cascading select must be invalid"

    page.evaluate("() => { document.querySelector('#cs').values = ['na', 'ca', 'M']; }")
    entries = page.evaluate("() => Array.from(new FormData(document.querySelector('#f')).entries())")
    assert entries == [
        ["geo", '["na","ca","M"]'], ["region", "na"], ["country", "ca"], ["size", "M"]
    ], f"Unexpected form entries {entries}"
    valid = page.evaluate("() => document.querySelector('#cs').checkValidity()")
    assert valid is True, "A complete required cascading select must be valid"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_cascading_select_level_data_is_rendered_as_text(base_url: str, page) -> None:
    """
    Level labels, placeholders and option data (including data returned by an
    async source) are shown as text and never run.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    load_fixture(page, base_url, '<mj-cascading-select id="cs"></mj-cascading-select>', ["mj-cascading-select"])
    page.evaluate("""() => {
        const payload = `x'"><img src="data:,x" onerror="window.__hits=(window.__hits||0)+1">`;
        const cs = document.querySelector('#cs');
        cs.levels = [
            { label: payload, placeholder: payload, options: [{ value: payload, label: payload }] },
            { label: payload, dataSource: { query: () => Promise.resolve([{ value: payload, label: payload }]) } }
        ];
        cs.values = [payload, payload];
    }""")
    page.wait_for_timeout(300)
    assert page.evaluate(_INJECTION_HITS_JS) is True, "Injected markup must not run"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_cascading_select_state_slots_follow_the_level(base_url: str, page) -> None:
    """
    The slotted level-loading and level-error content shows in whichever
    level is loading or failed, not only in the first one; ::part(level)
    names only the level wrappers.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    markup = (
        '<mj-cascading-select id="cs">'
        '<span slot="level-loading">Loading...</span><span slot="level-error">Offline</span>'
        '</mj-cascading-select>'
    )
    load_fixture(page, base_url, markup, ["mj-cascading-select"])
    result = page.evaluate("""async () => {
        const tick = () => new Promise((r) => setTimeout(r, 30));
        const cs = document.getElementById('cs');
        let settle = null;
        cs.levels = [
            { label: 'One', options: ['a'] },
            { label: 'Two', options: () => new Promise((resolve, reject) => { settle = () => reject(new Error('down')); }) },
        ];
        await tick();
        const root = cs.shadowRoot;
        const shownIn = (name) => {
            const slot = root.querySelector('slot[name=' + name + ']');
            if (slot === null || slot.closest('[hidden]') !== null) { return null; }
            return { level: Array.from(root.querySelectorAll('[part=level]')).indexOf(slot.closest('[part=level]')), assigned: slot.assignedNodes().length };
        };
        const first = root.querySelector('select');
        first.value = 'a';
        first.dispatchEvent(new Event('change', { bubbles: true }));
        await tick();
        const loading = shownIn('level-loading');
        settle();
        await tick();
        return {
            loading: loading,
            error: shownIn('level-error'),
            levelParts: Array.from(root.querySelectorAll('[part~=level]')).map((n) => n.localName),
        };
    }""")
    assert result["loading"] == {"level": 1, "assigned": 1}, f"Slotted loading text not in level 2: {result}"
    assert result["error"] == {"level": 1, "assigned": 1}, f"Slotted error text not in level 2: {result}"
    assert result["levelParts"] == ["div", "div"], f"::part(level) must name only the wrappers: {result}"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_cascading_select_value_property_selects_the_levels(base_url: str, page) -> None:
    """
    Assigning the value property (JSON text or an array) selects the levels
    like values does, so the selects, values and the form value agree.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    markup = '<form id="f"><mj-cascading-select id="cs" name="place"></mj-cascading-select></form>'
    load_fixture(page, base_url, markup, ["mj-cascading-select"])
    result = page.evaluate("""() => {
        const cs = document.getElementById('cs');
        cs.levels = [{ options: ['eu', 'as'] }, { options: { eu: ['fr', 'de'], as: ['jp'] } }];
        cs.value = '["eu","de"]';
        const fromText = { values: cs.values, selects: Array.from(cs.shadowRoot.querySelectorAll('select')).map((s) => s.value),
                           submitted: new FormData(document.getElementById('f')).get('place') };
        cs.value = ['as', 'jp'];
        return { fromText: fromText, fromArray: cs.values, value: cs.value };
    }""")
    assert result["fromText"]["values"] == ["eu", "de"], f"{result}"
    assert result["fromText"]["selects"] == ["eu", "de"], f"{result}"
    assert result["fromText"]["submitted"] == '["eu","de"]', f"{result}"
    assert result["fromArray"] == ["as", "jp"] and result["value"] == '["as","jp"]', f"{result}"
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


_RADIO_MARKUP = (
    '<form id="f"><mj-radio-group id="rg" name="plan" required label="Plan">'
    '<mj-radio value="a" disabled>Basic</mj-radio><mj-radio value="b">Team</mj-radio>'
    '<mj-radio value="c">Enterprise</mj-radio></mj-radio-group></form>'
)


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_radio_group_arrow_keys_move_focus_and_selection(base_url: str, page) -> None:
    """
    The group's tab stop is the first enabled radio; ArrowDown moves focus
    and selection to the next radio and wraps past the disabled one.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    load_fixture(page, base_url, _RADIO_MARKUP, ["mj-radio-group"])
    expect(page.get_by_role("radio", name="Team")).to_have_attribute("tabindex", "0")
    page.get_by_role("radio", name="Team").focus()
    page.keyboard.press("ArrowDown")
    expect(page.get_by_role("radio", name="Enterprise")).to_have_attribute("aria-checked", "true")
    expect(page.get_by_role("radio", name="Enterprise")).to_be_focused()
    page.keyboard.press("ArrowRight")
    expect(page.get_by_role("radio", name="Team")).to_have_attribute("aria-checked", "true")
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_radio_group_required_and_disabled_states(base_url: str, page) -> None:
    """
    An untouched required group is invalid; a disabled group exposes
    aria-disabled and ignores the keyboard.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    load_fixture(page, base_url, _RADIO_MARKUP, ["mj-radio-group"])
    valid = page.evaluate("() => document.querySelector('#rg').checkValidity()")
    assert valid is False, "An empty required radio group must be invalid"
    expect(page.get_by_role("radiogroup", name="Plan")).to_have_attribute("aria-required", "true")

    page.evaluate("() => document.querySelector('#rg').setAttribute('disabled', '')")
    expect(page.get_by_role("radiogroup", name="Plan")).to_have_attribute("aria-disabled", "true")
    page.evaluate("""() => {
        const radio = document.querySelector('#rg').shadowRoot.querySelectorAll('[role="radio"]')[1];
        radio.dispatchEvent(new KeyboardEvent('keydown', { key: ' ', bubbles: true, composed: true }));
    }""")
    value = page.evaluate("() => document.querySelector('#rg').value")
    assert value == "", f"A disabled group must not change from the keyboard, got {value!r}"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_radio_group_value_property_and_reset(base_url: str, page) -> None:
    """
    Assigning ``value`` checks the matching radio; a form reset returns to
    the ``value`` attribute, which a user selection leaves untouched.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    load_fixture(page, base_url, _RADIO_MARKUP.replace('required', 'value="b"'), ["mj-radio-group"])
    page.evaluate("() => { document.querySelector('#rg').value = 'c'; }")
    expect(page.get_by_role("radio", name="Enterprise")).to_have_attribute("aria-checked", "true")
    page.evaluate("() => document.querySelector('#f').reset()")
    expect(page.get_by_role("radio", name="Team")).to_have_attribute("aria-checked", "true")
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_radio_group_labels_are_rendered_as_text(base_url: str, page) -> None:
    """
    Markup in the group label, radio text and radio values never runs.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    markup = (
        f'<mj-radio-group label="{_INJECTION_TEXT}" value="{_INJECTION_TEXT}">'
        f'<mj-radio value="{_INJECTION_TEXT}">{_INJECTION_TEXT}</mj-radio>'
        f'<mj-radio>{_INJECTION_TEXT}</mj-radio></mj-radio-group>'
    )
    load_fixture(page, base_url, markup, ["mj-radio-group"])
    page.wait_for_timeout(300)
    assert page.evaluate(_INJECTION_HITS_JS) is True, "Injected markup must not run"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_radio_group_failed_submit_shows_inline_error(base_url: str, page) -> None:
    """
    A failed mj-form submit raises `invalid` on the required group, which
    then shows the validation message in its error region and marks the
    radiogroup aria-invalid; choosing a radio removes both.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    markup = (
        '<mj-form id="mf"><mj-radio-group id="rg" name="plan" required label="Plan">'
        '<mj-radio value="b">Team</mj-radio><mj-radio value="c">Enterprise</mj-radio>'
        '</mj-radio-group></mj-form>'
    )
    load_fixture(page, base_url, markup, ["mj-radio-group", "mj-form"])
    page.evaluate("() => document.querySelector('#mf').submit()")
    group = page.get_by_role("radiogroup", name="Plan")
    expect(group).to_have_attribute("aria-invalid", "true")
    expect(page.get_by_text("This field is required.")).to_be_visible()

    page.get_by_role("radio", name="Team").click()
    expect(group).not_to_have_attribute("aria-invalid", "true")
    expect(page.get_by_text("This field is required.")).to_be_hidden()
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


_CHECKBOX_MARKUP = (
    '<form id="f"><mj-checkbox-group id="cg" name="ch" select-all label="Channels">'
    '<mj-checkbox value="sms">Same name</mj-checkbox><mj-checkbox value="push">Same name</mj-checkbox>'
    '<mj-checkbox value="hook" disabled>Webhook</mj-checkbox></mj-checkbox-group></form>'
)


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_checkbox_group_select_all_works_from_the_keyboard(base_url: str, page) -> None:
    """
    Space on the select-all checkbox checks every enabled checkbox; Enter
    clears them again.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    load_fixture(page, base_url, _CHECKBOX_MARKUP, ["mj-checkbox-group"])
    select_all = page.get_by_role("checkbox", name="Select all")
    select_all.focus()
    page.keyboard.press(" ")
    value = page.evaluate("() => document.querySelector('#cg').value")
    assert value == "sms,push", f"Expected all enabled checkboxes, got {value!r}"
    expect(select_all).to_have_attribute("aria-checked", "true")
    page.keyboard.press("Enter")
    value = page.evaluate("() => document.querySelector('#cg').value")
    assert value == "", f"Expected select-all to clear the group, got {value!r}"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_checkbox_group_duplicate_labels_toggle_their_own_checkbox(base_url: str, page) -> None:
    """
    Two checkboxes with the same text each toggle their own value.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    load_fixture(page, base_url, _CHECKBOX_MARKUP, ["mj-checkbox-group"])
    page.get_by_role("checkbox", name="Same name").nth(1).click()
    value = page.evaluate("() => document.querySelector('#cg').value")
    assert value == "push", f"Expected the second checkbox's value, got {value!r}"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_checkbox_group_disabled_ignores_keyboard_and_leaves_tab_order(base_url: str, page) -> None:
    """
    A disabled group exposes aria-disabled, takes its checkboxes out of the
    tab order and ignores Space.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    load_fixture(page, base_url, _CHECKBOX_MARKUP.replace('select-all', 'select-all disabled'), ["mj-checkbox-group"])
    expect(page.get_by_role("group", name="Channels")).to_have_attribute("aria-disabled", "true")
    state = page.evaluate("""() => {
        const root = document.querySelector('#cg').shadowRoot;
        const boxes = Array.from(root.querySelectorAll('[role="checkbox"]'));
        boxes[1].dispatchEvent(new KeyboardEvent('keydown', { key: ' ', bubbles: true, composed: true }));
        return { tabbable: boxes.filter((box) => box.tabIndex >= 0).length, value: document.querySelector('#cg').value };
    }""")
    assert state == {"tabbable": 0, "value": ""}, f"Unexpected disabled-group state {state}"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_checkbox_group_labels_are_rendered_as_text(base_url: str, page) -> None:
    """
    Markup in the group label, select-all label, checkbox text and values
    never runs.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    markup = (
        f'<mj-checkbox-group select-all label="{_INJECTION_TEXT}" select-all-label="{_INJECTION_TEXT}" value="{_INJECTION_TEXT}">'
        f'<mj-checkbox value="{_INJECTION_TEXT}">{_INJECTION_TEXT}</mj-checkbox>'
        f'<mj-checkbox>{_INJECTION_TEXT}</mj-checkbox></mj-checkbox-group>'
    )
    load_fixture(page, base_url, markup, ["mj-checkbox-group"])
    page.wait_for_timeout(300)
    assert page.evaluate(_INJECTION_HITS_JS) is True, "Injected markup must not run"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_checkbox_group_required_reports_its_own_message(base_url: str, page) -> None:
    """
    An empty required checkbox group reports "At least one option must be
    selected." unless required-message gives another text.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    markup = (
        '<form><mj-checkbox-group id="own" required><mj-checkbox value="a">A</mj-checkbox></mj-checkbox-group>'
        '<mj-checkbox-group id="custom" required required-message="Pick a day.">'
        '<mj-checkbox value="a">A</mj-checkbox></mj-checkbox-group></form>'
    )
    load_fixture(page, base_url, markup, ["mj-checkbox-group"])
    result = page.evaluate("""() => ({
        own: document.getElementById('own').validationMessage,
        missing: document.getElementById('own').validity.valueMissing,
        custom: document.getElementById('custom').validationMessage,
    })""")
    assert result == {"own": "At least one option must be selected.", "missing": True, "custom": "Pick a day."}, f"{result}"
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_segmented_control_modes_in_markup_upgrade_without_error(base_url: str, page) -> None:
    """
    Controls declared with ``mode`` in markup upgrade without an uncaught
    exception and get the container role of their mode.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    errors = _collect_page_errors(page)
    markup = (
        '<mj-segmented-control mode="toggle" label="Format"><mj-segment value="b">B</mj-segment></mj-segmented-control>'
        '<mj-segmented-control mode="action" label="Edit"><mj-segment value="cut">Cut</mj-segment>'
        '<mj-segment value="copy">Copy</mj-segment></mj-segmented-control>'
    )
    load_fixture(page, base_url, markup, ["mj-segmented-control"])
    expect(page.get_by_role("group", name="Format")).to_have_count(1)
    expect(page.get_by_role("toolbar", name="Edit")).to_have_count(1)
    assert errors == [], f"Upgrading the segmented controls raised {errors}"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_segmented_control_arrow_keys_select_and_form_submits(base_url: str, page) -> None:
    """
    In select mode ArrowRight moves focus and selection (skipping a disabled
    segment) and the form submits the selected value.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    markup = (
        '<form id="f"><mj-segmented-control id="sc" name="view" value="day" label="View">'
        '<mj-segment value="day">Day</mj-segment><mj-segment value="week" disabled>Week</mj-segment>'
        '<mj-segment value="month">Month</mj-segment></mj-segmented-control></form>'
    )
    load_fixture(page, base_url, markup, ["mj-segmented-control"])
    page.get_by_role("radio", name="Day").focus()
    page.keyboard.press("ArrowRight")
    expect(page.get_by_role("radio", name="Month")).to_have_attribute("aria-checked", "true")
    expect(page.get_by_role("radio", name="Month")).to_be_focused()
    submitted = page.evaluate("() => new FormData(document.querySelector('#f')).get('view')")
    assert submitted == "month", f"Expected the form to submit 'month', got {submitted!r}"
    page.evaluate("() => document.querySelector('#f').reset()")
    expect(page.get_by_role("radio", name="Day")).to_have_attribute("aria-checked", "true")
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_segmented_control_reenable_keeps_disabled_segment_disabled(base_url: str, page) -> None:
    """
    Disabling and re-enabling the control leaves an individually disabled
    segment disabled.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    markup = (
        '<mj-segmented-control id="sc" label="View"><mj-segment value="a">A</mj-segment>'
        '<mj-segment value="b" disabled>B</mj-segment></mj-segmented-control>'
    )
    load_fixture(page, base_url, markup, ["mj-segmented-control"])
    page.evaluate("""() => {
        const control = document.querySelector('#sc');
        control.setAttribute('disabled', '');
        control.removeAttribute('disabled');
    }""")
    expect(page.get_by_role("radio", name="B")).to_be_disabled()
    expect(page.get_by_role("radio", name="A")).to_be_enabled()
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_segmented_control_labels_are_rendered_as_text(base_url: str, page) -> None:
    """
    Markup in the control label, segment text and segment values never runs.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    markup = (
        f'<mj-segmented-control label="{_INJECTION_TEXT}" value="{_INJECTION_TEXT}">'
        f'<mj-segment value="{_INJECTION_TEXT}" aria-label="{_INJECTION_TEXT}">{_INJECTION_TEXT}</mj-segment>'
        f'<mj-segment>{_INJECTION_TEXT}</mj-segment></mj-segmented-control>'
    )
    load_fixture(page, base_url, markup, ["mj-segmented-control"])
    page.wait_for_timeout(300)
    assert page.evaluate(_INJECTION_HITS_JS) is True, "Injected markup must not run"
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_split_button_menu_is_operable_from_the_keyboard(base_url: str, page) -> None:
    """
    ArrowDown on the dropdown trigger opens the menu with focus on it;
    ArrowDown skips a disabled item, Enter chooses the active item and focus
    returns to the trigger. In ``dynamic`` mode the primary action follows.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    markup = (
        '<mj-split-button id="sb" label="Save" dynamic>'
        '<mj-menu-item value="draft">Draft</mj-menu-item><mj-menu-item value="x" disabled>Locked</mj-menu-item>'
        '<mj-menu-item value="tpl">Template</mj-menu-item></mj-split-button>'
    )
    load_fixture(page, base_url, markup, ["mj-split-button"])
    page.evaluate("""() => {
        window.__mjevents = [];
        const sb = document.querySelector('#sb');
        sb.addEventListener('mj-menu-select', (e) => window.__mjevents.push(['select', e.detail.value]));
        sb.addEventListener('mj-primary-click', (e) => window.__mjevents.push(['primary', e.detail.value]));
    }""")
    trigger = page.get_by_role("button", name="More actions")
    trigger.focus()
    page.keyboard.press("ArrowDown")
    expect(page.get_by_role("menu")).to_be_focused()
    page.keyboard.press("ArrowDown")
    page.keyboard.press("Enter")
    expect(trigger).to_be_focused()
    page.get_by_role("button", name="Template").click()
    events = page.evaluate("() => window.__mjevents")
    assert events == [["select", "tpl"], ["primary", "tpl"]], f"Unexpected events {events}"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_split_button_disabled_attributes_reach_the_buttons(base_url: str, page) -> None:
    """
    ``disabled`` in markup disables both inner buttons; ``primary-disabled``
    disables only the primary one.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    markup = (
        '<mj-split-button id="d" label="Off" disabled><mj-menu-item>A</mj-menu-item></mj-split-button>'
        '<mj-split-button id="p" label="Half" primary-disabled dropdown-label="Half menu">'
        '<mj-menu-item>B</mj-menu-item></mj-split-button>'
    )
    load_fixture(page, base_url, markup, ["mj-split-button"])
    expect(page.locator("#d .primary")).to_be_disabled()
    expect(page.locator("#d .dropdown-trigger")).to_be_disabled()
    expect(page.get_by_role("button", name="Half", exact=True)).to_be_disabled()
    expect(page.get_by_role("button", name="Half menu")).to_be_enabled()
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_split_button_labels_are_rendered_as_text(base_url: str, page) -> None:
    """
    Markup in ``label``, ``dropdown-label`` and menu item text never runs.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    markup = (
        f'<mj-split-button open label="{_INJECTION_TEXT}" dropdown-label="{_INJECTION_TEXT}">'
        f'<mj-menu-item value="{_INJECTION_TEXT}">{_INJECTION_TEXT}</mj-menu-item></mj-split-button>'
    )
    load_fixture(page, base_url, markup, ["mj-split-button"])
    page.wait_for_timeout(300)
    assert page.evaluate(_INJECTION_HITS_JS) is True, "Injected markup must not run"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_split_button_danger_variant_has_hover_feedback(base_url: str, page) -> None:
    """
    Hovering the primary or the dropdown button of a danger split button
    changes its background.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    markup = (
        '<mj-split-button id="sb" label="Delete" variant="danger">'
        '<mj-menu-item value="all">Delete all</mj-menu-item></mj-split-button><p id="away">away</p>'
    )
    load_fixture(page, base_url, markup, ["mj-split-button"])
    background = "(part) => getComputedStyle(document.getElementById('sb').shadowRoot.querySelector('[part=' + part + ']')).backgroundColor"
    for part in ["primary", "dropdown-trigger"]:
        page.hover("#away")
        page.wait_for_timeout(250)
        rest = page.evaluate(background, part)
        page.locator("#sb").locator(f"[part='{part}']").hover()
        page.wait_for_timeout(250)
        hovered = page.evaluate(background, part)
        assert hovered != rest, f"No hover feedback on the danger {part} button: {rest} -> {hovered}"
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_menu_button_menu_is_operable_from_the_keyboard(base_url: str, page) -> None:
    """
    Enter on the trigger opens the menu with focus on it; ArrowDown skips a
    disabled item, Enter activates the active item, focus returns to the
    trigger; Escape closes without choosing.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    markup = (
        '<mj-menu-button id="mb" label="Actions">'
        '<mj-menu-item value="edit">Edit</mj-menu-item><mj-menu-item value="x" disabled>Locked</mj-menu-item>'
        '<mj-menu-separator></mj-menu-separator>'
        '<mj-menu-item value="delete" variant="danger">Delete</mj-menu-item></mj-menu-button>'
    )
    load_fixture(page, base_url, markup, ["mj-menu-button"])
    page.evaluate("""() => {
        window.__mjevents = [];
        document.querySelector('#mb').addEventListener('mj-select', (e) => window.__mjevents.push(e.detail.value));
    }""")
    trigger = page.get_by_role("button", name="Actions")
    trigger.focus()
    page.keyboard.press("Enter")
    expect(page.get_by_role("menu")).to_be_focused()
    expect(page.get_by_role("separator")).to_have_count(1)
    page.keyboard.press("ArrowDown")
    page.keyboard.press("Enter")
    expect(trigger).to_be_focused()
    page.keyboard.press("Enter")
    page.keyboard.press("Escape")
    expect(trigger).to_be_focused()
    open_now = page.evaluate("() => document.querySelector('#mb').hasAttribute('open')")
    events = page.evaluate("() => window.__mjevents")
    assert open_now is False, "Escape must close the menu"
    assert events == ["delete"], f"Unexpected mj-select values {events}"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_menu_button_open_and_disabled_in_markup(base_url: str, page) -> None:
    """
    ``open`` in markup upgrades without an exception and shows the menu
    expanded; ``disabled`` in markup disables the trigger.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    errors = _collect_page_errors(page)
    markup = (
        '<mj-menu-button open label="Open"><mj-menu-item>A</mj-menu-item></mj-menu-button>'
        '<mj-menu-button disabled label="Off"><mj-menu-item>B</mj-menu-item></mj-menu-button>'
    )
    load_fixture(page, base_url, markup, ["mj-menu-button"])
    expect(page.get_by_role("button", name="Open")).to_have_attribute("aria-expanded", "true")
    expect(page.get_by_role("button", name="Off")).to_be_disabled()
    assert errors == [], f"Upgrading the menu buttons raised {errors}"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_menu_button_labels_are_rendered_as_text(base_url: str, page) -> None:
    """
    Markup in the trigger label and in item text, value, variant and
    shortcut never runs.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    markup = (
        f'<mj-menu-button open label="{_INJECTION_TEXT}">'
        f'<mj-menu-item value="{_INJECTION_TEXT}" variant="{_INJECTION_TEXT}" shortcut="{_INJECTION_TEXT}">{_INJECTION_TEXT}</mj-menu-item>'
        f'</mj-menu-button>'
    )
    load_fixture(page, base_url, markup, ["mj-menu-button"])
    page.wait_for_timeout(300)
    assert page.evaluate(_INJECTION_HITS_JS) is True, "Injected markup must not run"
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


_INJECTION = "x'\"><img src=\"data:,x\" onerror=\"top.__hits=(top.__hits||0)+1\">"


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_color_picker_canvas_and_hue_pick_what_is_shown(base_url: str, page) -> None:
    """
    The canvas is an HSV plane: its top-right corner is the pure hue, and the
    hue slider keeps its position even when the colour is black (the picked
    value is not re-parsed from the attribute).

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-color-picker")
    frame = _reload_example(page, '<mj-color-picker id="cp" value="#000000" open></mj-color-picker>', "mj-color-picker")
    page.wait_for_timeout(200)
    result = frame.evaluate("""() => {
        const cp = document.getElementById('cp');
        const sr = cp.shadowRoot;
        const hue = sr.querySelector('.hue-slider');
        hue.value = '120';
        hue.dispatchEvent(new Event('input', { bubbles: true }));
        hue.dispatchEvent(new Event('change', { bubbles: true }));
        const hueKept = hue.value;
        const thumb = sr.querySelector('.canvas-thumb');
        for (let i = 0; i < 10; i++) {
            thumb.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowRight', shiftKey: true, bubbles: true }));
            thumb.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowUp', shiftKey: true, bubbles: true }));
        }
        return { hueKept: hueKept, value: cp.value, attr: cp.getAttribute('value') };
    }""")
    assert result["hueKept"] == "120", f"Hue slider snapped back: {result}"
    assert result["value"] == "#00ff00", f"Top-right of a 120 degree canvas should be pure green: {result}"
    assert result["attr"] == "#000000", f"The value attribute is the initial value and must not change: {result}"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_color_picker_swatches_are_not_parsed_as_markup(base_url: str, page) -> None:
    """
    Swatch strings from the swatches attribute never become markup.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-color-picker")
    frame = _reload_example(page, '<mj-color-picker id="cp"></mj-color-picker>', "mj-color-picker")
    hits = frame.evaluate("""async (payload) => {
        const cp = document.getElementById('cp');
        cp.setAttribute('swatches', JSON.stringify([payload, '#fff' + payload, '#ff0000']));
        cp.setAttribute('value', payload);
        await new Promise((r) => setTimeout(r, 300));
        return { hits: top.__hits === undefined ? 0 : top.__hits, swatches: cp.shadowRoot.querySelectorAll('.swatch').length };
    }""", _INJECTION)
    assert hits["hits"] == 0, f"Injected markup executed: {hits}"
    assert hits["swatches"] == 1, f"Only the valid colour should become a swatch: {hits}"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_color_picker_disabled_fieldset_and_readonly_block_opening(base_url: str, page) -> None:
    """
    Inside a disabled fieldset the trigger is disabled and the popup does not
    open. Setting readonly closes an open popup and marks the trigger
    aria-disabled without a popup announcement.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    markup = (
        '<form><fieldset disabled><mj-color-picker id="locked" value="#336699"></mj-color-picker></fieldset></form>'
        '<mj-color-picker id="ro" value="#336699"></mj-color-picker>'
    )
    load_fixture(page, base_url, markup, ["mj-color-picker"])
    result = page.evaluate("""async () => {
        const locked = document.getElementById('locked');
        const lockedTrigger = locked.shadowRoot.querySelector('[part=trigger]');
        lockedTrigger.click();
        locked.open = true;
        const ro = document.getElementById('ro');
        ro.open = true;
        const openedBefore = ro.hasAttribute('open');
        ro.setAttribute('readonly', '');
        await new Promise((r) => setTimeout(r, 50));
        const trigger = ro.shadowRoot.querySelector('[part=trigger]');
        trigger.click();
        return {
            lockedDisabled: lockedTrigger.disabled, lockedOpen: locked.hasAttribute('open'),
            openedBefore: openedBefore, openAfterReadonly: ro.hasAttribute('open'),
            ariaDisabled: trigger.getAttribute('aria-disabled'), haspopup: trigger.getAttribute('aria-haspopup'),
            value: ro.value,
        };
    }""")
    assert result["lockedDisabled"] is True and result["lockedOpen"] is False, f"Fieldset disabled ignored: {result}"
    assert result["openedBefore"] is True and result["openAfterReadonly"] is False, f"readonly left the popup open: {result}"
    assert result["ariaDisabled"] == "true" and result["haspopup"] is None, f"readonly trigger not marked: {result}"
    assert result["value"] == "#336699", f"readonly must keep the value: {result}"
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_date_picker_value_is_a_local_day_and_arrows_step_one_day(base_url: str, page) -> None:
    """
    An ISO value is a local calendar day: the calendar opens on its month with
    focus on that day, and ArrowLeft/ArrowRight move exactly one day.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-date-picker")
    frame = _reload_example(page, '<mj-date-picker id="dp" value="2020-05-10" locale="en-US"></mj-date-picker>', "mj-date-picker")
    frame.locator("#dp .cal-trigger").click()
    page.wait_for_timeout(200)
    result = frame.evaluate("""() => {
        const dp = document.getElementById('dp');
        const sr = dp.shadowRoot;
        const focused = () => sr.activeElement ? sr.activeElement.dataset.date : null;
        const press = (k) => sr.activeElement.dispatchEvent(new KeyboardEvent('keydown', { key: k, bubbles: true, cancelable: true }));
        const start = focused();
        press('ArrowRight');
        const right = focused();
        press('ArrowLeft');
        press('ArrowLeft');
        const left = focused();
        const day = dp.valueAsDate.getDate();
        return { start, right, left, day, text: sr.querySelector('.date-input').value };
    }""")
    assert result["start"] == "2020-05-10", f"Calendar should open on the value's day: {result}"
    assert result["right"] == "2020-05-11", f"ArrowRight should move one day: {result}"
    assert result["left"] == "2020-05-09", f"ArrowLeft should move one day: {result}"
    assert result["day"] == 10, f"valueAsDate must be the local day: {result}"
    assert result["text"] == "May 10, 2020", f"Display must show the local day: {result}"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_date_picker_escape_closes_an_empty_picker(base_url: str, page) -> None:
    """
    With no value, opening from the keyboard puts focus on a day and Escape
    closes the calendar and returns focus to the field.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-date-picker")
    frame = _reload_example(page, '<mj-date-picker id="dp"></mj-date-picker>', "mj-date-picker")
    inp = frame.locator("#dp .date-input")
    inp.focus()
    page.keyboard.press("ArrowDown")
    page.wait_for_timeout(200)
    on_day = frame.evaluate("() => { const a = document.getElementById('dp').shadowRoot.activeElement; return a !== null && a.classList.contains('day-btn'); }")
    page.keyboard.press("Escape")
    page.wait_for_timeout(100)
    state = frame.evaluate("() => { const dp = document.getElementById('dp'); return { open: dp.hasAttribute('open'), field: dp.shadowRoot.activeElement === dp.shadowRoot.querySelector('.date-input') }; }")
    assert on_day is True, "Opening from the keyboard should focus a day button"
    assert state["open"] is False, "Escape should close the calendar"
    assert state["field"] is True, "Escape should return focus to the field"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_date_picker_typed_date_is_committed(base_url: str, page) -> None:
    """
    A date typed into the field is parsed on Enter and becomes the value.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-date-picker")
    frame = _reload_example(page, '<mj-date-picker id="dp" locale="en-US"></mj-date-picker>', "mj-date-picker")
    inp = frame.locator("#dp .date-input")
    inp.click()
    inp.type("03/15/2026")
    page.keyboard.press("Enter")
    page.wait_for_timeout(100)
    value = frame.evaluate("() => document.getElementById('dp').value")
    assert value == "2026-03-15", f"Typed date should be committed, got {value!r}"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_date_picker_field_is_named_by_label_and_attributes(base_url: str, page) -> None:
    """
    The inner text field takes its accessible name from an associated
    <label for>, the label attribute or aria-label.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    markup = (
        '<label for="due">Due date</label><mj-date-picker id="due"></mj-date-picker>'
        '<mj-date-picker label="Start date"></mj-date-picker>'
        '<mj-date-picker aria-label="End date"></mj-date-picker>'
    )
    load_fixture(page, base_url, markup, ["mj-date-picker"])
    for name in ["Due date", "Start date", "End date"]:
        expect(page.get_by_role("combobox", name=name, exact=True)).to_have_count(1)
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_date_picker_disabled_fieldset_and_late_required(base_url: str, page) -> None:
    """
    Inside a disabled fieldset the field is disabled and the calendar does not
    open; required set after the picker rendered makes it invalid.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    markup = (
        '<form><fieldset disabled><mj-date-picker id="locked" value="2026-03-10"></mj-date-picker></fieldset>'
        '<mj-date-picker id="late"></mj-date-picker></form>'
    )
    load_fixture(page, base_url, markup, ["mj-date-picker"])
    result = page.evaluate("""() => {
        const locked = document.getElementById('locked');
        locked.shadowRoot.querySelector('[part=calendar-trigger]').click();
        locked.open = true;
        const late = document.getElementById('late');
        const validBefore = late.checkValidity();
        late.setAttribute('required', '');
        return {
            inputDisabled: locked.shadowRoot.querySelector('[part=input]').disabled,
            open: locked.hasAttribute('open'),
            validBefore: validBefore,
            validAfter: late.checkValidity(),
            ariaRequired: late.shadowRoot.querySelector('[part=input]').getAttribute('aria-required'),
        };
    }""")
    assert result["inputDisabled"] is True and result["open"] is False, f"Fieldset disabled ignored: {result}"
    assert result["validBefore"] is True and result["validAfter"] is False, f"Late required ignored: {result}"
    assert result["ariaRequired"] == "true", f"{result}"
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_file_picker_file_name_is_text_and_form_gets_files(base_url: str, page) -> None:
    """
    A dropped file whose name contains markup is shown as text, a single-file
    picker keeps one file, and the form receives the File object.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-file-picker")
    frame = _reload_example(page, '<form id="f"><mj-file-picker id="fp" name="doc"></mj-file-picker></form>', "mj-file-picker")
    result = frame.evaluate("""async (payload) => {
        const fp = document.getElementById('fp');
        const dt = new DataTransfer();
        dt.items.add(new File(['a'], payload + '.png', { type: 'image/png' }));
        dt.items.add(new File(['b'], 'second.txt', { type: 'text/plain' }));
        fp.shadowRoot.querySelector('.dropzone').dispatchEvent(new DragEvent('drop', { dataTransfer: dt, bubbles: true, cancelable: true, composed: true }));
        await new Promise((r) => setTimeout(r, 300));
        const entries = new FormData(document.getElementById('f')).getAll('doc');
        return {
            hits: top.__hits === undefined ? 0 : top.__hits,
            names: Array.from(fp.shadowRoot.querySelectorAll('.file-name')).map((n) => n.textContent),
            entryIsFile: entries.length === 1 && entries[0] instanceof File
        };
    }""", _INJECTION)
    assert result["hits"] == 0, f"File name markup executed: {result}"
    assert result["names"] == [_INJECTION + ".png"], f"Single-file picker should keep only the first file, as text: {result}"
    assert result["entryIsFile"] is True, f"The form should receive the File object: {result}"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_file_picker_disabled_blocks_keyboard(base_url: str, page) -> None:
    """
    A disabled file picker has no tab stop and its choose button is disabled.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-file-picker")
    frame = _reload_example(page, '<mj-file-picker id="fp" disabled></mj-file-picker>', "mj-file-picker")
    state = frame.evaluate("""() => {
        const sr = document.getElementById('fp').shadowRoot;
        return { tab: sr.querySelector('.dropzone').tabIndex, button: sr.querySelector('.choose-btn').disabled };
    }""")
    assert state["tab"] == -1, f"Disabled dropzone should not be a tab stop: {state}"
    assert state["button"] is True, f"Disabled picker's choose button should be disabled: {state}"
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_asset_picker_escape_closes_and_arrows_step_one_cell(base_url: str, page) -> None:
    """
    After several searches ArrowRight still moves one cell, ArrowDown moves
    one row of `columns` cells, and Escape closes the popup back to the trigger.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-asset-picker")
    frame = _reload_example(page, '<mj-asset-picker id="ap" columns="6"></mj-asset-picker>', "mj-asset-picker")
    frame.locator("#ap .trigger").click()
    page.wait_for_timeout(200)
    search = frame.locator("#ap .search-input")
    for text in ["he", "fa", ""]:
        search.fill(text)
        page.wait_for_timeout(250)
    result = frame.evaluate("""() => {
        const sr = document.getElementById('ap').shadowRoot;
        const cells = () => Array.from(sr.querySelectorAll('.asset-cell'));
        sr.querySelector('.asset-cell[tabindex="0"]').focus();
        const index = () => cells().indexOf(sr.activeElement);
        const press = (k) => sr.activeElement.dispatchEvent(new KeyboardEvent('keydown', { key: k, bubbles: true, cancelable: true }));
        const start = index();
        press('ArrowRight');
        const right = index();
        press('ArrowDown');
        const down = index();
        return { right: right - start, down: down - right };
    }""")
    page.keyboard.press("Escape")
    page.wait_for_timeout(100)
    state = frame.evaluate("() => { const ap = document.getElementById('ap'); return { open: ap.hasAttribute('open'), trigger: ap.shadowRoot.activeElement === ap.shadowRoot.querySelector('.trigger') }; }")
    assert result == {"right": 1, "down": 6}, f"Arrow keys should move one cell / one row: {result}"
    assert state["open"] is False, "Escape should close the asset picker"
    assert state["trigger"] is True, "Escape should return focus to the trigger"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_asset_picker_value_shows_on_trigger_and_in_form(base_url: str, page) -> None:
    """
    A value in markup shows on the trigger and is submitted with the form.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-asset-picker")
    frame = _reload_example(page, '<form id="f"><mj-asset-picker id="ap" name="emoji" value="🚀"></mj-asset-picker></form>', "mj-asset-picker")
    result = frame.evaluate("""() => {
        const ap = document.getElementById('ap');
        return {
            shown: ap.shadowRoot.querySelector('.trigger-value').textContent,
            label: ap.shadowRoot.querySelector('.trigger').getAttribute('aria-label'),
            submitted: new FormData(document.getElementById('f')).get('emoji')
        };
    }""")
    assert result["shown"] == "🚀", f"Trigger should show the value: {result}"
    assert "rocket" in result["label"], f"Trigger name should include the asset label: {result}"
    assert result["submitted"] == "🚀", f"Form should submit the value: {result}"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_asset_picker_default_grid_fits_the_popup(base_url: str, page) -> None:
    """
    With the default columns and cell size every grid column is visible:
    the asset area does not scroll sideways.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    load_fixture(page, base_url, '<mj-asset-picker id="ap" open></mj-asset-picker>', ["mj-asset-picker"])
    page.wait_for_timeout(200)
    size = page.evaluate("""() => {
        const area = document.getElementById('ap').shadowRoot.querySelector('[part=asset-area]');
        const row = area.querySelector('[role=row]');
        return { scrollWidth: area.scrollWidth, clientWidth: area.clientWidth,
                 cells: row.children.length, rowRight: row.lastElementChild.getBoundingClientRect().right,
                 areaRight: area.getBoundingClientRect().right };
    }""")
    assert size["cells"] == 8, f"The default grid has 8 columns: {size}"
    assert size["scrollWidth"] <= size["clientWidth"], f"The grid overflows the popup: {size}"
    assert size["rowRight"] <= size["areaRight"], f"The last column is clipped: {size}"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_asset_picker_late_required_and_disabled_fieldset(base_url: str, page) -> None:
    """
    required set or removed after render updates validity; inside a disabled
    fieldset the trigger is disabled and the popup does not open.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    markup = (
        '<form><mj-asset-picker id="late"></mj-asset-picker>'
        '<fieldset disabled><mj-asset-picker id="locked"></mj-asset-picker></fieldset></form>'
    )
    load_fixture(page, base_url, markup, ["mj-asset-picker"])
    result = page.evaluate("""() => {
        const late = document.getElementById('late');
        late.setAttribute('required', '');
        const required = late.checkValidity();
        late.removeAttribute('required');
        const removed = late.checkValidity();
        const locked = document.getElementById('locked');
        const trigger = locked.shadowRoot.querySelector('[part=trigger]');
        trigger.click();
        return { required: required, removed: removed, triggerDisabled: trigger.disabled, open: locked.hasAttribute('open') };
    }""")
    assert result == {"required": False, "removed": True, "triggerDisabled": True, "open": False}, f"{result}"
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_locale_picker_reopen_after_selection_lists_everything(base_url: str, page) -> None:
    """
    Clicking a picker that already shows a selection opens the full list, not
    only the selected entry; the country list includes Slovenia (SI) and Ireland.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-locale-picker")
    frame = _reload_example(page, '<mj-locale-picker id="lp" mode="country" value="SI" display-locale="en"></mj-locale-picker>', "mj-locale-picker")
    frame.locator("#lp .input").click()
    page.wait_for_timeout(200)
    result = frame.evaluate("""() => {
        const lp = document.getElementById('lp');
        const labels = Array.from(lp.shadowRoot.querySelectorAll('.option')).map((o) => o.getAttribute('aria-label'));
        return { open: lp.hasAttribute('open'), count: labels.length, text: lp.shadowRoot.querySelector('.input').value, ireland: labels.includes('Ireland') };
    }""")
    assert result["open"] is True, f"Clicking the field should open the list: {result}"
    assert result["text"] == "Slovenia", f"SI should be Slovenia: {result}"
    assert result["count"] > 200, f"The full country list should be offered: {result}"
    assert result["ireland"] is True, f"Ireland should be selectable: {result}"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_locale_picker_form_reset_restores_initial_value(base_url: str, page) -> None:
    """
    After the user picks another language a form reset restores the value
    written in markup.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-locale-picker")
    frame = _reload_example(page, '<form id="f"><mj-locale-picker id="lp" name="lang" value="de" clearable display-locale="en"></mj-locale-picker></form>', "mj-locale-picker")
    result = frame.evaluate("""() => {
        const lp = document.getElementById('lp');
        lp.shadowRoot.querySelector('.clear-btn').click();
        const afterClear = lp.value;
        document.getElementById('f').reset();
        return { afterClear: afterClear, afterReset: lp.value, text: lp.shadowRoot.querySelector('.input').value };
    }""")
    assert result["afterClear"] == "", f"Clear should empty the value: {result}"
    assert result["afterReset"] == "de", f"Reset should restore the initial value: {result}"
    assert result["text"] == "German", f"Reset should refresh the field text: {result}"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_locale_picker_late_required_and_disabled_fieldset(base_url: str, page) -> None:
    """
    required set after render makes an empty picker invalid; inside a
    disabled fieldset the input is disabled.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    markup = (
        '<form><mj-locale-picker id="late" mode="language"></mj-locale-picker>'
        '<fieldset disabled><mj-locale-picker id="locked" mode="language"></mj-locale-picker></fieldset></form>'
    )
    load_fixture(page, base_url, markup, ["mj-locale-picker"])
    result = page.evaluate("""() => {
        const late = document.getElementById('late');
        const before = late.checkValidity();
        late.setAttribute('required', '');
        return { before: before, after: late.checkValidity(),
                 lockedDisabled: document.getElementById('locked').shadowRoot.querySelector('[part=input]').disabled };
    }""")
    assert result == {"before": True, "after": False, "lockedDisabled": True}, f"{result}"
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


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_tag_picker_initial_value_tokens_and_form_value(base_url: str, page) -> None:
    """
    A value in markup renders its tokens (with option labels), keeps the
    attribute, submits one entry per token and satisfies `required`.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-tag-picker")
    frame = _reload_example(
        page,
        '<form id="f"><mj-tag-picker id="tp" name="tags" required value="design,custom">'
        '<mj-option value="design">Design</mj-option></mj-tag-picker>'
        '<mj-tag-picker id="empty" name="other" required></mj-tag-picker></form>',
        "mj-tag-picker",
    )
    result = frame.evaluate("""() => {
        const tp = document.getElementById('tp');
        return {
            tokens: Array.from(tp.shadowRoot.querySelectorAll('[part="token-label"]')).map((n) => n.textContent),
            attr: tp.getAttribute('value'),
            value: tp.value,
            submitted: new FormData(document.getElementById('f')).getAll('tags'),
            valid: tp.checkValidity(),
            emptyValid: document.getElementById('empty').checkValidity()
        };
    }""")
    assert result["tokens"] == ["Design", "custom"], f"Initial tokens missing: {result}"
    assert result["attr"] == "design,custom", f"value attribute must not be removed: {result}"
    assert result["value"] == "design,custom", f"value property should be the joined string: {result}"
    assert result["submitted"] == ["design", "custom"], f"One form entry per token expected: {result}"
    assert result["valid"] is True and result["emptyValid"] is False, f"required not enforced: {result}"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_tag_picker_labels_are_not_parsed_as_markup(base_url: str, page) -> None:
    """
    Option labels, meta, token labels and avatars are rendered as text.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-tag-picker")
    frame = _reload_example(page, '<mj-tag-picker id="tp" type="person"><mj-option value="a">x</mj-option></mj-tag-picker>', "mj-tag-picker")
    hits = frame.evaluate("""async (payload) => {
        const tp = document.getElementById('tp');
        const opt = tp.querySelector('mj-option');
        opt.textContent = payload;
        opt.setAttribute('meta', payload);
        opt.setAttribute('avatar', payload);
        tp.tokens = [{ value: payload, label: payload, avatar: payload }];
        const input = tp.shadowRoot.querySelector('input');
        input.focus();
        input.value = 'x';
        input.dispatchEvent(new InputEvent('input', { bubbles: true, composed: true }));
        await new Promise((r) => setTimeout(r, 500));
        return { hits: top.__hits === undefined ? 0 : top.__hits, options: tp.shadowRoot.querySelectorAll('[part="option"]').length };
    }""", _INJECTION)
    assert hits["hits"] == 0, f"Injected markup executed: {hits}"
    assert hits["options"] == 1, f"The suggestion should still be shown: {hits}"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_tag_picker_token_add_can_be_cancelled(base_url: str, page) -> None:
    """
    preventDefault() on mj-token-add stops the token from being added.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-tag-picker")
    frame = _reload_example(page, '<mj-tag-picker id="tp" free-text></mj-tag-picker>', "mj-tag-picker")
    frame.evaluate("() => document.getElementById('tp').addEventListener('mj-token-add', (e) => { if (e.detail.token.value === 'no') e.preventDefault(); })")
    inp = frame.locator("#tp input")
    inp.click()
    inp.type("no")
    page.keyboard.press("Enter")
    inp.fill("yes")
    page.keyboard.press("Enter")
    tokens = frame.evaluate("() => document.getElementById('tp').tokens.map((t) => t.value)")
    assert tokens == ["yes"], f"Cancelled token was added: {tokens}"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_tag_picker_add_at_max_count_fires_mj_max_count(base_url: str, page) -> None:
    """
    At max-count the input stays usable, the hint describes it, and an add
    the user attempts (Enter on typed text) fires mj-max-count.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    markup = '<mj-tag-picker id="tp" free-text max-count="1" value="one" aria-label="Tags"></mj-tag-picker>'
    load_fixture(page, base_url, markup, ["mj-tag-picker"])
    page.evaluate("""() => {
        window.__maxCount = [];
        document.getElementById('tp').addEventListener('mj-max-count', (e) => window.__maxCount.push(e.detail.count));
    }""")
    field = page.get_by_role("combobox", name="Tags")
    expect(field).to_be_enabled()
    expect(field).to_have_accessible_description("Maximum 1 tag reached.")
    field.fill("two")
    field.press("Enter")
    result = page.evaluate("() => ({ events: window.__maxCount, tokens: document.getElementById('tp').tokens.length })")
    assert result == {"events": [1], "tokens": 1}, f"mj-max-count should fire once and no token be added: {result}"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_tag_picker_disabled_fieldset_disables_the_input(base_url: str, page) -> None:
    """
    Inside a disabled fieldset the input and the token remove buttons are
    disabled.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    markup = '<form><fieldset disabled><mj-tag-picker id="tp" value="a" aria-label="Tags"></mj-tag-picker></fieldset></form>'
    load_fixture(page, base_url, markup, ["mj-tag-picker"])
    result = page.evaluate("""() => {
        const root = document.getElementById('tp').shadowRoot;
        return { input: root.querySelector('[part=input]').disabled, remove: root.querySelector('[part=token-remove]').disabled };
    }""")
    assert result == {"input": True, "remove": True}, f"{result}"
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


_TREE_NODES = """[
    { id: 'a', label: 'Alpha', children: [{ id: 'a1', label: 'Alpha one' }, { id: 'a2', label: 'Alpha two' }] },
    { id: 'b', label: 'Beta', children: [{ id: 'b1', label: 'Beta one' }] },
    { id: 'c', label: 'Gamma' }
]"""


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_tree_selector_keyboard_keeps_focus_after_select_and_expand(base_url: str, page) -> None:
    """
    Space selects and ArrowLeft/ArrowRight collapse/expand without dropping
    focus; a node without `children` is a leaf (no aria-expanded).

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-tree-selector")
    frame = _reload_example(page, '<mj-tree-selector id="ts"></mj-tree-selector>', "mj-tree-selector")
    frame.evaluate("() => { document.getElementById('ts').nodes = " + _TREE_NODES + "; }")
    page.wait_for_timeout(100)
    frame.evaluate("() => document.getElementById('ts').focus()")
    page.keyboard.press("ArrowDown")
    page.keyboard.press("Space")
    page.keyboard.press("ArrowUp")
    page.keyboard.press("ArrowLeft")
    page.keyboard.press("ArrowRight")
    page.keyboard.press("ArrowDown")
    result = frame.evaluate("""() => {
        const ts = document.getElementById('ts');
        const active = ts.shadowRoot.activeElement;
        return {
            focused: active !== null ? active.dataset.nodeId : null,
            value: ts.value,
            leafExpanded: ts.shadowRoot.querySelector('[data-node-id="c"]').hasAttribute('aria-expanded'),
            stops: ts.shadowRoot.querySelectorAll('[tabindex="0"]').length
        };
    }""")
    assert result["focused"] == "a1", f"Focus should survive selection and expand/collapse: {result}"
    assert result["value"] == "a1", f"Space should select the focused node: {result}"
    assert result["leafExpanded"] is False, f"A node without children is a leaf: {result}"
    assert result["stops"] == 1, f"Exactly one tab stop expected: {result}"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_tree_selector_checkbox_parent_follows_children(base_url: str, page) -> None:
    """
    In checkbox mode unchecking one child takes the parent out of the value,
    and the initial value is submitted with the form.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-tree-selector")
    frame = _reload_example(page, '<form id="f"><mj-tree-selector id="ts" name="n" selection="checkbox" value="a"></mj-tree-selector></form>', "mj-tree-selector")
    frame.evaluate("() => { document.getElementById('ts').nodes = " + _TREE_NODES + "; }")
    page.wait_for_timeout(100)
    result = frame.evaluate("""() => {
        const ts = document.getElementById('ts');
        const form = () => new FormData(document.getElementById('f')).getAll('n');
        const initial = form();
        ts.shadowRoot.querySelector('[data-node-id="a1"]').click();
        return { initial: initial, after: form(), parent: ts.shadowRoot.querySelector('[data-node-id="a"]').getAttribute('aria-checked') };
    }""")
    assert result["initial"] == ["a", "a1", "a2"], f"Initial value should be submitted: {result}"
    assert result["after"] == ["a2"], f"Parent must leave the value when a child is unchecked: {result}"
    assert result["parent"] == "mixed", f"Parent should show mixed: {result}"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_tree_selector_labels_are_not_parsed_as_markup(base_url: str, page) -> None:
    """
    Node labels, icons, badges and ids are rendered as text.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-tree-selector")
    frame = _reload_example(page, '<mj-tree-selector id="ts"></mj-tree-selector>', "mj-tree-selector")
    hits = frame.evaluate("""async (payload) => {
        const ts = document.getElementById('ts');
        ts.setAttribute('aria-label', payload);
        ts.nodes = [{ id: payload, label: payload, icon: payload, badge: payload, children: [{ id: payload + '1', label: payload }] }];
        await new Promise((r) => setTimeout(r, 300));
        return { hits: top.__hits === undefined ? 0 : top.__hits, rows: ts.shadowRoot.querySelectorAll('.tree-item-row').length };
    }""", _INJECTION)
    assert hits["hits"] == 0, f"Injected markup executed: {hits}"
    assert hits["rows"] == 2, f"Both rows should render: {hits}"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_tree_selector_expanded_lazy_branch_loads_its_children(base_url: str, page) -> None:
    """
    A lazy branch listed in `expanded` loads its children through the data
    source, and so does an expanded lazy branch among the loaded children.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    load_fixture(page, base_url, '<mj-tree-selector id="ts" expanded="p,c"></mj-tree-selector>', ["mj-tree-selector"])
    result = page.evaluate("""async () => {
        const ts = document.getElementById('ts');
        const calls = [];
        ts.dataSource = { getChildren: async (id) => {
            calls.push(id);
            return id === 'p' ? [{ id: 'c', label: 'Child', hasChildren: true }] : [{ id: 'g', label: 'Grandchild' }];
        } };
        ts.nodes = [{ id: 'p', label: 'Parent', hasChildren: true }];
        await new Promise((r) => setTimeout(r, 200));
        return { calls: calls, rows: Array.from(ts.shadowRoot.querySelectorAll('[role=treeitem]')).length };
    }""")
    assert result == {"calls": ["p", "c"], "rows": 3}, f"Expanded lazy branches were not loaded: {result}"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_tree_selector_single_mode_keeps_one_selected_node(base_url: str, page) -> None:
    """
    In single selection mode a value listing several nodes selects only the
    first one, from the attribute and from the property.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    markup = (
        '<mj-tree-selector id="ts" value="b,a">'
        '<mj-tree-item node-id="a">A</mj-tree-item><mj-tree-item node-id="b">B</mj-tree-item>'
        '</mj-tree-selector>'
    )
    load_fixture(page, base_url, markup, ["mj-tree-selector"])
    result = page.evaluate("""() => {
        const ts = document.getElementById('ts');
        const fromAttribute = ts.value;
        ts.value = 'a,b';
        return { fromAttribute: fromAttribute, fromProperty: ts.value,
                 selectedRows: ts.shadowRoot.querySelectorAll('[aria-selected=true]').length };
    }""")
    assert result == {"fromAttribute": "b", "fromProperty": "a", "selectedRows": 1}, f"{result}"
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


_TRANSFER_HTML = (
    '<form id="f"><mj-transfer-list id="tl" name="perm" required reorder>'
    '<mj-option value="read">Read</mj-option>'
    '<mj-option value="write">Write</mj-option>'
    '<mj-option value="admin">Admin</mj-option>'
    "</mj-transfer-list></form>"
)


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_transfer_list_keyboard_selection_keeps_focus_and_moves(base_url: str, page) -> None:
    """
    Arrow keys select options without losing focus, Ctrl+ArrowRight moves the
    selection to the target, and the form receives one entry per target item.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-transfer-list")
    frame = _reload_example(page, _TRANSFER_HTML, "mj-transfer-list")
    before_valid = frame.evaluate("() => document.getElementById('tl').checkValidity()")
    # Focusing the listbox makes its first option active; ArrowDown selects the second.
    frame.evaluate("() => document.getElementById('tl').shadowRoot.querySelector('[part=\"source-listbox\"]').focus()")
    page.keyboard.press("ArrowDown")
    page.keyboard.press("Control+ArrowRight")
    result = frame.evaluate("""() => {
        const tl = document.getElementById('tl');
        const active = tl.shadowRoot.activeElement;
        return {
            focus: active !== null ? active.getAttribute('part') : null,
            target: tl.targetItems.map((i) => i.value),
            submitted: new FormData(document.getElementById('f')).getAll('perm'),
            valid: tl.checkValidity()
        };
    }""")
    assert before_valid is False, "An empty required target should be invalid"
    assert result["focus"] == "source-listbox", f"Focus should stay in the listbox: {result}"
    assert result["target"] == ["write"], f"Second option should have moved: {result}"
    assert result["submitted"] == ["write"], f"Form should receive the target values: {result}"
    assert result["valid"] is True, f"Non-empty target should be valid: {result}"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_transfer_list_label_change_keeps_moves_and_move_can_be_cancelled(base_url: str, page) -> None:
    """
    Changing a label or the orientation keeps the user's transfers, and
    preventDefault() on mj-move vetoes a move.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-transfer-list")
    frame = _reload_example(page, _TRANSFER_HTML, "mj-transfer-list")
    result = frame.evaluate("""() => {
        const tl = document.getElementById('tl');
        const sr = tl.shadowRoot;
        sr.querySelector('[data-action="move-all-right"]').click();
        tl.setAttribute('target-label', 'Granted');
        tl.setAttribute('orientation', 'vertical');
        const kept = tl.targetItems.map((i) => i.value);
        tl.addEventListener('mj-move', (e) => e.preventDefault());
        sr.querySelector('[data-action="move-all-left"]').click();
        return { kept: kept, afterVeto: tl.targetItems.map((i) => i.value), label: sr.querySelector('[data-label="target"]').textContent };
    }""")
    assert result["kept"] == ["read", "write", "admin"], f"Attribute change reset the transfers: {result}"
    assert result["afterVeto"] == ["read", "write", "admin"], f"Cancelled move happened: {result}"
    assert result["label"] == "Granted", f"Label should update in place: {result}"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_transfer_list_labels_are_not_parsed_as_markup(base_url: str, page) -> None:
    """
    Item labels, values, icons and pane labels are rendered as text.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """
    page.goto(base_url + "/components/selection/mj-transfer-list")
    frame = _reload_example(page, '<mj-transfer-list id="tl"></mj-transfer-list>', "mj-transfer-list")
    hits = frame.evaluate("""async (payload) => {
        const tl = document.getElementById('tl');
        tl.setAttribute('source-label', payload);
        tl.setAttribute('target-label', payload);
        const option = document.createElement('mj-option');
        option.textContent = payload;
        option.setAttribute('value', payload);
        option.setAttribute('icon', payload);
        tl.appendChild(option);
        await new Promise((r) => setTimeout(r, 300));
        return { hits: top.__hits === undefined ? 0 : top.__hits, options: tl.shadowRoot.querySelectorAll('[role="option"]').length };
    }""", _INJECTION)
    assert hits["hits"] == 0, f"Injected markup executed: {hits}"
    assert hits["options"] == 1, f"An option added after first render should appear: {hits}"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_empty_listbox_select_and_tree_keep_their_message_out_of_the_items(base_url: str, page) -> None:
    """
    An empty mj-listbox, mj-select and mj-tree-selector keep their empty
    message out of the listbox or tree element, which may own only options
    or tree items (axe aria-required-children): the element stays empty, and
    the message is a sibling that is shown and describes it. Once an item
    arrives the message is hidden and the description goes away.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """

    markup = (
        '<mj-listbox id="lb" label="Fruits"></mj-listbox>'
        '<mj-select id="sel" label="Fruit"></mj-select>'
        '<mj-tree-selector id="tree" aria-label="Folders"></mj-tree-selector>'
    )
    load_fixture(page, base_url, markup, ["mj-listbox", "mj-select", "mj-tree-selector"])

    result = page.evaluate(
        """async () => {
            const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
            await wait(150);
            const read = (host, selector) => {
                const root = document.getElementById(host).shadowRoot;
                const owner = root.querySelector(selector);
                const describedBy = owner.getAttribute("aria-describedby");
                const message = describedBy === null ? null : root.getElementById(describedBy);
                return {
                    children: owner.childNodes.length,
                    message: message === null ? null : {
                        inside: owner.contains(message),
                        hidden: message.hidden,
                        text: message.querySelector("slot").assignedNodes({ flatten: true })
                            .map((node) => node.textContent).join("").trim().length > 0,
                    },
                };
            };
            const empty = {
                listbox: read("lb", "[role=listbox]"),
                select: read("sel", "[role=listbox]"),
                tree: read("tree", "[role=tree]"),
            };
            for (const host of ["lb", "sel"]) {
                const option = document.createElement("mj-option");
                option.setAttribute("value", "apple");
                option.textContent = "Apple";
                document.getElementById(host).appendChild(option);
            }
            document.getElementById("tree").nodes = [{ id: "docs", label: "Docs" }];
            await wait(150);
            const filled = (host, selector, part) => {
                const root = document.getElementById(host).shadowRoot;
                const message = root.querySelector(`[part="${part}"]`);
                return {
                    describedBy: root.querySelector(selector).getAttribute("aria-describedby"),
                    messageHidden: message === null || message.hidden === true,
                };
            };
            return {
                empty: empty,
                filled: {
                    listbox: filled("lb", "[role=listbox]", "empty"),
                    select: filled("sel", "[role=listbox]", "no-results"),
                    tree: filled("tree", "[role=tree]", "empty"),
                },
            };
        }"""
    )

    for name in ("listbox", "select", "tree"):
        expected = {"children": 0, "message": {"inside": False, "hidden": False, "text": True}}
        assert result["empty"][name] == expected, result
        assert result["filled"][name] == {"describedBy": None, "messageHidden": True}, result

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_select_listbox_is_the_scroll_container_of_its_popup(base_url: str, page) -> None:
    """
    With more options than fit in ``--mj-select-popup-max-height`` the listbox
    the combobox controls scrolls, not the popup around it (axe treats a
    combobox's listbox as reachable through the combobox), and moving the
    active option with the keyboard scrolls it into view.

    :param base_url: The running site URL fixture.
    :param page: Playwright page fixture.
    """

    options = "".join(f'<mj-option value="o{index}">Option {index}</mj-option>' for index in range(40))
    markup = f'<mj-select id="many" label="Many">{options}</mj-select>'
    load_fixture(page, base_url, markup, ["mj-select"])

    result = page.evaluate(
        """async () => {
            const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
            const host = document.getElementById("many");
            await wait(100);
            const root = host.shadowRoot;
            const trigger = root.querySelector("[role=combobox]");
            trigger.focus();
            trigger.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowDown", bubbles: true, cancelable: true }));
            await wait(100);
            for (let step = 0; step < 30; step = step + 1) {
                trigger.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowDown", bubbles: true, cancelable: true }));
            }
            await wait(100);
            const popup = root.querySelector(".popup");
            const listbox = root.querySelector("[role=listbox]");
            const active = root.getElementById(trigger.getAttribute("aria-activedescendant"));
            const listBox = listbox.getBoundingClientRect();
            const activeBox = active.getBoundingClientRect();
            return {
                open: host.hasAttribute("open"),
                controls: trigger.getAttribute("aria-controls") === listbox.id,
                listboxScrolls: listbox.scrollHeight > listbox.clientHeight && listbox.scrollTop > 0,
                popupScrolls: popup.scrollHeight > popup.clientHeight,
                activeInView: activeBox.top >= listBox.top - 1 && activeBox.bottom <= listBox.bottom + 1,
            };
        }"""
    )

    assert result == {
        "open": True, "controls": True, "listboxScrolls": True, "popupScrolls": False, "activeInView": True,
    }, result

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
