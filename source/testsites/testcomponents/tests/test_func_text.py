"""
    .. module:: testcomponents.tests.test_func_text

    Functional Playwright tests for the 'text' component group.

    Covers all 23 components defined in catalog/text.py:
      mj-text-field, mj-search-input, mj-password-field, mj-typed-field,
      mj-number-field, mj-textarea, mj-rich-text-editor, mj-markdown-editor,
      mj-code-editor, mj-inline-edit, mj-masked-input, mj-token-input,
      mj-otp-input, mj-slider, mj-rating, mj-captcha, mj-form, mj-fieldset,
      mj-label, mj-help-text, mj-error-message, mj-validation-summary,
      mj-character-counter.
"""

import ccai.testbase as testbase

from testcomponents.harness.browsers import expect
from testcomponents.harness.factories import create_page


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_frame(page):
    """
        Wait for the playground preview iframe and return its Frame object.

        :param page: The Playwright Page instance.

        :returns: The Frame for the playground preview iframe.
    """

    handle = page.wait_for_selector("[data-testid=playground-preview]")
    frame = handle.content_frame()
    return frame


def _wait_for_tag(frame, tag: str, timeout: int = 15000) -> None:
    """
        Block until the custom element is registered in the preview frame.

        :param frame: The Frame to wait in.
        :param tag: The custom element tag name.
        :param timeout: Maximum milliseconds to wait.

        :returns: None
    """

    frame.wait_for_function(
        "t => customElements.get(t) !== undefined",
        arg=tag,
        timeout=timeout,
    )
    return


# True once a run after 'previousRun' has started and its preview reported
# ready (library loaded, elements upgraded, example scripts run).
_RUN_READY_JS = """(previousRun) => {
    const frame = document.getElementById('pg-frame');
    const sandbox = window.mjSandboxPage;
    return frame !== null && sandbox !== undefined && sandbox.state.run > previousRun
        && frame.getAttribute('data-ready-run') === String(sandbox.state.run);
}"""


def _load_html(page, html: str) -> None:
    """
        Write new HTML into the playground editor, click Run and wait until
        the preview of that run is ready.

        The example on show finishes loading first: its scripts can still be
        running (an example that submits its form moves focus into the
        preview). The editor must hold the new HTML before Run is clicked,
        and the checks that follow see the new preview, not the example it
        replaced.

        :param page: The Playwright Page instance.
        :param html: The HTML snippet to load.

        :returns: None
    """

    page.wait_for_function("() => window.mjSandboxPage !== undefined", timeout=20000)
    shown_run = page.evaluate("() => window.mjSandboxPage.state.run")
    page.wait_for_function(_RUN_READY_JS, arg=shown_run - 1, timeout=20000)

    editor = page.get_by_test_id("playground-editor")
    editor.fill(html)
    expect(editor).to_have_value(html)

    previous_run = page.evaluate("() => window.mjSandboxPage.state.run")
    page.get_by_test_id("playground-run").click()
    page.wait_for_function(_RUN_READY_JS, arg=previous_run, timeout=20000)
    return


def _install_event_collector(frame, tag: str, events: list) -> None:
    """
        Inject a JS event collector on the first matching element in the frame.

        :param frame: The Frame to install the collector in.
        :param tag: The custom element tag name to listen on.
        :param events: List of event names to collect.

        :returns: None
    """

    events_js = str(events)
    frame.evaluate(
        f"""() => {{
            window.__mjevents = [];
            const el = document.querySelector("{tag}");
            {events_js}.forEach(n => el.addEventListener(n, e => {{
                window.__mjevents.push({{ name: n, detail: e.detail }});
            }}));
        }}"""
    )
    return


def _get_events(frame) -> list:
    """
        Return the collected events from the frame.

        :param frame: The Frame to read events from.

        :returns: A list of {{ name, detail }} dicts.
    """

    result = frame.evaluate("() => window.__mjevents")
    return result


# ===========================================================================
# mj-text-field
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_text_field_renders(base_url, page):
    """
        Verify mj-text-field renders with a label and placeholder.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-text-field")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-text-field")

    el = frame.locator("mj-text-field")
    expect(el).to_be_visible()
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_text_field_typing_emits_mj_input(base_url, page):
    """
        Typing into mj-text-field fires mj-input events with the typed value.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-text-field")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-text-field")

    _install_event_collector(frame=frame, tag="mj-text-field", events=["mj-input"])

    inner = frame.locator("mj-text-field input")
    inner.fill("hello")

    events = _get_events(frame=frame)
    assert len(events) > 0
    input_events = [e for e in events if e["name"] == "mj-input"]
    assert len(input_events) > 0
    last = input_events[-1]
    assert last["detail"]["value"] == "hello"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_text_field_value_property(base_url, page):
    """
        The value property on mj-text-field reflects the current input value.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-text-field")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-text-field")

    inner = frame.locator("mj-text-field input")
    inner.fill("world")

    val = frame.evaluate("() => document.querySelector('mj-text-field').value")
    assert val == "world"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_text_field_clearable_shows_clear_button(base_url, page):
    """
        When clearable and a value is present, the clear button is visible.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-text-field")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-text-field")

    _load_html(
        page=page,
        html='<mj-text-field label="Name" clearable></mj-text-field>',
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-text-field")

    inner = frame.locator("mj-text-field input")
    inner.fill("test")

    clear_btn = frame.locator("mj-text-field [part='clear-button']")
    expect(clear_btn).not_to_have_attribute("hidden", "")
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_text_field_maxlength_shows_counter(base_url, page):
    """
        Setting maxlength on mj-text-field enables the character counter.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-text-field")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-text-field")

    _load_html(
        page=page,
        html='<mj-text-field label="Name" maxlength="20"></mj-text-field>',
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-text-field")

    counter = frame.locator("mj-text-field [part='counter']")
    expect(counter).not_to_have_attribute("hidden", "")
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_text_field_disabled_prevents_input(base_url, page):
    """
        A disabled mj-text-field has a disabled inner input.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-text-field")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-text-field")

    _load_html(
        page=page,
        html='<mj-text-field label="Name" disabled></mj-text-field>',
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-text-field")

    inner = frame.locator("mj-text-field input")
    expect(inner).to_be_disabled()
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_text_field_value_attribute_shown_and_submitted(base_url, page):
    """
        The value attribute is shown and submitted at first render, later
        attribute and property changes reach the input, and a form reset
        restores the attribute value.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-text-field")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-text-field")

    _load_html(
        page=page,
        html='<form id="probe"><mj-text-field name="who" value="Jane"></mj-text-field></form>',
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-text-field")
    frame.wait_for_function("() => document.getElementById('probe') !== null")

    result = frame.evaluate(
        """async () => {
            const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
            await wait(100);
            const form = document.getElementById("probe");
            const entries = () => Array.from(new FormData(form).entries());
            const field = form.querySelector("mj-text-field");
            const input = field.shadowRoot.querySelector("input");
            const result = { shown: input.value, submitted: entries() };
            field.setAttribute("value", "Carol");
            result.afterAttribute = input.value;
            field.value = "Bob";
            result.afterProperty = input.value;
            form.reset();
            result.afterReset = [input.value, field.value];
            return result;
        }"""
    )

    assert result["shown"] == "Jane", result
    assert result["submitted"] == [["who", "Jane"]], result
    assert result["afterAttribute"] == "Carol", result
    assert result["afterProperty"] == "Bob", result
    assert result["afterReset"] == ["Carol", "Carol"], result
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_text_field_constraints_affect_validity(base_url, page):
    """
        required, pattern and minlength set validity from the first render;
        error-message only replaces the text of a real error.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-text-field")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-text-field")

    _load_html(
        page=page,
        html=(
            '<form id="probe"><mj-text-field name="code" required pattern="[0-9]+" minlength="3"'
            ' error-message="Digits only"></mj-text-field></form>'
        ),
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-text-field")
    frame.wait_for_function("() => document.getElementById('probe') !== null")

    result = frame.evaluate(
        """async () => {
            const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
            await wait(100);
            const field = document.querySelector("mj-text-field");
            const input = field.shadowRoot.querySelector("input");
            const error = field.shadowRoot.querySelector(".error");
            const result = { untouched: field.checkValidity() };
            field.value = "abc";
            result.pattern = field.checkValidity();
            field.value = "12";
            result.short = field.checkValidity();
            field.value = "123";
            input.focus();
            input.blur();
            result.valid = [field.checkValidity(), error.hasAttribute("data-visible"), input.getAttribute("aria-invalid")];
            field.value = "x";
            input.focus();
            input.blur();
            result.invalidShown = [error.textContent, input.getAttribute("aria-invalid")];
            return result;
        }"""
    )

    assert result["untouched"] is False, result
    assert result["pattern"] is False, result
    assert result["short"] is False, result
    assert result["valid"] == [True, False, "false"], result
    assert result["invalidShown"] == ["Digits only", "true"], result
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_text_field_family_hides_empty_affix_wrappers(base_url, page):
    """
        The prefix / suffix wrappers of the text-field family take no room
        while their slot is empty, and appear when content is slotted later.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-text-field")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-text-field")

    _load_html(
        page=page,
        html=(
            '<mj-text-field id="plain" label="Plain"></mj-text-field>'
            '<mj-text-field id="with-prefix" label="Price"><span slot="prefix">$</span></mj-text-field>'
            '<mj-password-field id="pw" label="Password"></mj-password-field>'
            '<mj-typed-field id="typed" type="email" label="Email"></mj-typed-field>'
            '<mj-masked-input id="masked" mask="999" label="Code"></mj-masked-input>'
            '<mj-number-field id="number" label="Count" value="1"></mj-number-field>'
        ),
    )
    frame = _get_frame(page)
    for tag in ["mj-text-field", "mj-password-field", "mj-typed-field", "mj-masked-input", "mj-number-field"]:
        _wait_for_tag(frame=frame, tag=tag)
    frame.wait_for_function("() => document.getElementById('number') !== null && document.getElementById('number').shadowRoot !== null")

    result = frame.evaluate(
        """async () => {
            const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
            await wait(100);
            const affixes = (id) => Array.from(
                document.getElementById(id).shadowRoot.querySelectorAll("[part='prefix'], [part='suffix']")
            ).map((wrapper) => ({ part: wrapper.getAttribute("part"), width: wrapper.getBoundingClientRect().width }));
            const inputOffset = (id) => {
                const root = document.getElementById(id).shadowRoot;
                return root.querySelector("input").getBoundingClientRect().left - root.querySelector("[part='field']").getBoundingClientRect().left;
            };
            const result = {};
            for (const id of ["plain", "pw", "typed", "masked", "number"]) {
                result[id] = affixes(id);
            }
            result.withPrefix = affixes("with-prefix");
            result.plainOffset = inputOffset("plain");
            const suffix = document.createElement("span");
            suffix.slot = "suffix";
            suffix.textContent = "kg";
            document.getElementById("plain").append(suffix);
            await wait(50);
            result.afterSlotting = affixes("plain");
            return result;
        }"""
    )

    for field_id in ["plain", "pw", "typed", "masked", "number"]:
        for wrapper in result[field_id]:
            assert wrapper["width"] == 0, (field_id, result)
    assert result["withPrefix"][0]["part"] == "prefix" and result["withPrefix"][0]["width"] > 0, result
    assert result["withPrefix"][1]["width"] == 0, result
    assert result["plainOffset"] <= 2, result
    assert result["afterSlotting"][1]["part"] == "suffix" and result["afterSlotting"][1]["width"] > 0, result
    return


# ===========================================================================
# mj-search-input
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_search_input_renders(base_url, page):
    """
        Verify mj-search-input renders in the preview.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-search-input")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-search-input")

    el = frame.locator("mj-search-input")
    expect(el).to_be_visible()
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_search_input_emits_mj_input(base_url, page):
    """
        Typing into mj-search-input fires mj-input events.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-search-input")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-search-input")

    _install_event_collector(frame=frame, tag="mj-search-input", events=["mj-input"])

    inner = frame.locator("mj-search-input input")
    inner.fill("foo")

    events = _get_events(frame=frame)
    input_events = [e for e in events if e["name"] == "mj-input"]
    assert len(input_events) > 0
    last = input_events[-1]
    assert last["detail"]["value"] == "foo"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_search_input_emits_mj_search_on_enter(base_url, page):
    """
        Pressing Enter on mj-search-input fires an mj-search event.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-search-input")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-search-input")

    _install_event_collector(frame=frame, tag="mj-search-input", events=["mj-search"])

    inner = frame.locator("mj-search-input input")
    inner.fill("bar")
    inner.press("Enter")

    events = _get_events(frame=frame)
    search_events = [e for e in events if e["name"] == "mj-search"]
    assert len(search_events) > 0
    assert search_events[-1]["detail"]["value"] == "bar"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_search_input_value_attribute_and_reset(base_url, page):
    """
        The value attribute is shown and submitted (under the default name
        "q"), the property updates the input, and form reset restores it.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-search-input")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-search-input")

    _load_html(
        page=page,
        html='<form id="probe"><mj-search-input value="shoes"></mj-search-input></form>',
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-search-input")
    frame.wait_for_function("() => document.getElementById('probe') !== null")

    result = frame.evaluate(
        """async () => {
            const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
            await wait(100);
            const form = document.getElementById("probe");
            const entries = () => Array.from(new FormData(form).entries());
            const field = form.querySelector("mj-search-input");
            const input = field.shadowRoot.querySelector("input");
            const result = {
                shown: input.value,
                submitted: entries(),
                role: input.getAttribute("role"),
                expanded: input.getAttribute("aria-expanded")
            };
            field.value = "boots";
            result.afterProperty = input.value;
            form.reset();
            result.afterReset = input.value;
            return result;
        }"""
    )

    assert result["shown"] == "shoes", result
    assert result["submitted"] == [["q", "shoes"]], result
    assert result["role"] == "searchbox", result
    assert result["expanded"] is None, result
    assert result["afterProperty"] == "boots", result
    assert result["afterReset"] == "shoes", result
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_search_input_markup_attributes_are_escaped(base_url, page):
    """
        label and placeholder are applied as text, never parsed as markup.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-search-input")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-search-input")

    _load_html(
        page=page,
        html=(
            '<div id="probe"><mj-search-input'
            ' label=\'x"><img src="data:,x" onerror="window.__hits=1">\''
            ' placeholder=\'y"><b id="inj">b</b>\'></mj-search-input></div>'
        ),
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-search-input")
    frame.wait_for_function("() => document.getElementById('probe') !== null")

    result = frame.evaluate(
        """async () => {
            const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
            await wait(100);
            const field = document.querySelector("mj-search-input");
            return {
                hits: window.__hits === undefined ? null : window.__hits,
                injected: field.shadowRoot.querySelector("img, #inj") !== null,
                placeholder: field.shadowRoot.querySelector("input").placeholder
            };
        }"""
    )

    assert result["hits"] is None, result
    assert result["injected"] is False, result
    assert result["placeholder"] == 'y"><b id="inj">b</b>', result
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_search_input_required_and_maxlength_show_inline_error(base_url, page):
    """
        A required or too-long search input shows an inline error, marks the
        input aria-invalid and fires mj-invalid like the other text
        controls; fixing the value removes the error.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-search-input")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-search-input")

    _load_html(
        page=page,
        html=(
            '<form id="probe">'
            '<mj-search-input id="needed" name="q" label="Search" required></mj-search-input>'
            '<mj-search-input id="short" label="Short" maxlength="3" error-message="Three letters at most."></mj-search-input>'
            '</form>'
        ),
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-search-input")
    frame.wait_for_function("() => document.getElementById('short') !== null && document.getElementById('short').shadowRoot !== null")

    result = frame.evaluate(
        """async () => {
            const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
            await wait(50);
            const invalids = [];
            document.addEventListener("mj-invalid", (event) => invalids.push([event.target.id, event.detail.validationMessage]));
            const state = (id) => {
                const root = document.getElementById(id).shadowRoot;
                const error = root.querySelector("[part='error']");
                const input = root.querySelector("input");
                return {
                    shown: error.hasAttribute("data-visible"),
                    text: error.textContent,
                    ariaInvalid: input.getAttribute("aria-invalid"),
                    describedBy: (input.getAttribute("aria-describedby") || "").split(" ").includes(error.id)
                };
            };
            const result = { initially: state("needed") };
            const needed = document.getElementById("needed");
            result.valid = needed.reportValidity();
            result.afterReport = state("needed");
            needed.value = "tabs";
            result.afterFix = state("needed");
            const short = document.getElementById("short");
            short.value = "abcdef";
            result.shortValid = short.checkValidity();
            result.afterCheck = state("short");
            result.invalids = invalids;
            return result;
        }"""
    )

    assert result["initially"]["shown"] is False, result
    assert result["valid"] is False, result
    assert result["afterReport"]["shown"] is True and len(result["afterReport"]["text"]) > 0, result
    assert result["afterReport"]["ariaInvalid"] == "true" and result["afterReport"]["describedBy"] is True, result
    assert result["afterFix"]["shown"] is False and result["afterFix"]["ariaInvalid"] == "false", result
    assert result["shortValid"] is False, result
    assert result["afterCheck"]["shown"] is True and result["afterCheck"]["text"] == "Three letters at most.", result
    assert [entry[0] for entry in result["invalids"]] == ["needed", "short"], result
    return


# ===========================================================================
# mj-password-field
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_password_field_renders(base_url, page):
    """
        Verify mj-password-field renders with a password input type.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-password-field")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-password-field")

    inner = frame.locator("mj-password-field input")
    expect(inner).to_have_attribute("type", "password")
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_password_field_toggle_visibility(base_url, page):
    """
        Clicking the toggle button on mj-password-field changes input type to text
        and emits mj-visibility-change.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-password-field")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-password-field")

    _install_event_collector(
        frame=frame,
        tag="mj-password-field",
        events=["mj-visibility-change"],
    )

    toggle = frame.locator("mj-password-field [part='toggle-button']")
    toggle.click()

    inner = frame.locator("mj-password-field input")
    expect(inner).to_have_attribute("type", "text")

    events = _get_events(frame=frame)
    vis_events = [e for e in events if e["name"] == "mj-visibility-change"]
    assert len(vis_events) > 0
    assert vis_events[-1]["detail"]["visible"] is True
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_password_field_emits_mj_input(base_url, page):
    """
        Typing into mj-password-field fires mj-input with the current value.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-password-field")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-password-field")

    _install_event_collector(frame=frame, tag="mj-password-field", events=["mj-input"])

    inner = frame.locator("mj-password-field input")
    inner.fill("SecretP@ss1")

    events = _get_events(frame=frame)
    input_events = [e for e in events if e["name"] == "mj-input"]
    assert len(input_events) > 0
    assert input_events[-1]["detail"]["value"] == "SecretP@ss1"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_password_field_value_and_minlength(base_url, page):
    """
        A programmatic value reaches the input and the strength meter, and
        minlength is part of validity.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-password-field")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-password-field")

    _load_html(
        page=page,
        html='<form id="probe"><mj-password-field name="pw" minlength="8" required show-strength></mj-password-field></form>',
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-password-field")
    frame.wait_for_function("() => document.getElementById('probe') !== null")

    result = frame.evaluate(
        """async () => {
            const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
            await wait(100);
            const form = document.getElementById("probe");
            const entries = () => Array.from(new FormData(form).entries());
            const field = form.querySelector("mj-password-field");
            const input = field.shadowRoot.querySelector("input");
            const result = { untouched: field.checkValidity() };
            field.value = "abc";
            result.short = [field.checkValidity(), field.validity.customError];
            field.value = "Sup3r$ecretPW";
            result.strong = [input.value, field.strength, field.checkValidity(), entries()];
            return result;
        }"""
    )

    assert result["untouched"] is False, result
    assert result["short"] == [False, True], result
    assert result["strong"] == ["Sup3r$ecretPW", 4, True, [["pw", "Sup3r$ecretPW"]]], result
    return


# ===========================================================================
# mj-typed-field
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_typed_field_email_type(base_url, page):
    """
        mj-typed-field with type=email renders an email input.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-typed-field")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-typed-field")

    _load_html(
        page=page,
        html='<mj-typed-field type="email" label="Email" placeholder="you@example.com"></mj-typed-field>',
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-typed-field")

    inner = frame.locator("mj-typed-field input")
    expect(inner).to_have_attribute("type", "email")
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_typed_field_emits_mj_input(base_url, page):
    """
        Typing into mj-typed-field fires mj-input events.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-typed-field")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-typed-field")

    _load_html(
        page=page,
        html='<mj-typed-field type="email" label="Email" placeholder="you@example.com"></mj-typed-field>',
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-typed-field")

    _install_event_collector(frame=frame, tag="mj-typed-field", events=["mj-input"])

    inner = frame.locator("mj-typed-field input")
    inner.fill("test@test.com")

    events = _get_events(frame=frame)
    input_events = [e for e in events if e["name"] == "mj-input"]
    assert len(input_events) > 0
    assert input_events[-1]["detail"]["value"] == "test@test.com"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_typed_field_value_attribute_and_tel_validation(base_url, page):
    """
        The value attribute is shown and submitted, an unsupported type falls
        back to email, and type=tel values are validated.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-typed-field")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-typed-field")

    _load_html(
        page=page,
        html=(
            '<form id="probe">'
            '<mj-typed-field name="em" type="email" value="a@b.co"></mj-typed-field>'
            '<mj-typed-field name="ph" type="tel" value="abc"></mj-typed-field>'
            '<mj-typed-field name="x" type="password"></mj-typed-field>'
            '</form>'
        ),
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-typed-field")
    frame.wait_for_function("() => document.getElementById('probe') !== null")

    result = frame.evaluate(
        """async () => {
            const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
            await wait(100);
            const form = document.getElementById("probe");
            const entries = () => Array.from(new FormData(form).entries());
            const fields = form.querySelectorAll("mj-typed-field");
            const inputs = Array.from(fields).map((field) => field.shadowRoot.querySelector("input"));
            const result = {
                shown: inputs[0].value,
                submitted: entries(),
                fallbackType: inputs[2].type,
                telInvalid: fields[1].checkValidity()
            };
            fields[1].value = "+1 (555) 010-9999";
            result.telValid = fields[1].checkValidity();
            return result;
        }"""
    )

    assert result["shown"] == "a@b.co", result
    assert ["em", "a@b.co"] in result["submitted"], result
    assert result["fallbackType"] == "email", result
    assert result["telInvalid"] is False, result
    assert result["telValid"] is True, result
    return


# ===========================================================================
# mj-number-field
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_number_field_renders_with_spinners(base_url, page):
    """
        mj-number-field renders increment and decrement buttons by default.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-number-field")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-number-field")

    _load_html(
        page=page,
        html='<mj-number-field label="Qty" value="5" min="1" max="100" step="1"></mj-number-field>',
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-number-field")

    inc = frame.locator("mj-number-field [part='increment-button']")
    dec = frame.locator("mj-number-field [part='decrement-button']")
    expect(inc).to_be_visible()
    expect(dec).to_be_visible()
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_number_field_increment_emits_mj_increment(base_url, page):
    """
        Clicking the increment button fires an mj-increment event with a numeric value.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-number-field")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-number-field")

    _load_html(
        page=page,
        html='<mj-number-field label="Qty" min="0" max="100" step="1"></mj-number-field>',
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-number-field")

    _install_event_collector(frame=frame, tag="mj-number-field", events=["mj-increment"])

    inc = frame.locator("mj-number-field [part='increment-button']")
    inc.click()

    events = _get_events(frame=frame)
    inc_events = [e for e in events if e["name"] == "mj-increment"]
    assert len(inc_events) > 0
    assert isinstance(inc_events[-1]["detail"]["valueAsNumber"], (int, float))
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_number_field_value_as_number(base_url, page):
    """
        After incrementing, valueAsNumber on mj-number-field returns a numeric value.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-number-field")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-number-field")

    _load_html(
        page=page,
        html='<mj-number-field label="Qty" min="0" max="100" step="1"></mj-number-field>',
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-number-field")

    inc = frame.locator("mj-number-field [part='increment-button']")
    inc.click()
    inc.click()

    val = frame.evaluate("() => document.querySelector('mj-number-field').valueAsNumber")
    assert val == 2
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_number_field_value_attribute_grouping_and_clear(base_url, page):
    """
        The value attribute is shown and submitted; a value of 1000 or more
        survives focus and blur; emptying the field clears the value; steps
        of 0.1 do not accumulate floating-point error.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-number-field")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-number-field")

    _load_html(
        page=page,
        html=(
            '<form id="probe">'
            '<mj-number-field name="qty" value="999" locale="en-US"></mj-number-field>'
            '<mj-number-field name="f" step="0.1" value="0"></mj-number-field>'
            '</form>'
        ),
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-number-field")
    frame.wait_for_function("() => document.getElementById('probe') !== null")

    result = frame.evaluate(
        """async () => {
            const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
            await wait(100);
            const form = document.getElementById("probe");
            const entries = () => Array.from(new FormData(form).entries());
            const fields = form.querySelectorAll("mj-number-field");
            const field = fields[0];
            const input = field.shadowRoot.querySelector("input");
            const key = (target, name) => target.dispatchEvent(
                new KeyboardEvent("keydown", { key: name, bubbles: true, composed: true, cancelable: true })
            );
            const result = { shown: input.value, submitted: entries() };
            input.focus();
            key(input, "ArrowUp");
            input.blur();
            result.afterStep = [input.value, field.valueAsNumber];
            input.focus();
            input.blur();
            result.afterRefocus = field.valueAsNumber;
            input.focus();
            input.value = "";
            input.dispatchEvent(new InputEvent("input", { bubbles: true, composed: true }));
            input.blur();
            result.cleared = [field.value, Number.isNaN(field.valueAsNumber)];
            field.value = 5;
            result.property = [input.value, field.valueAsNumber];
            const floatInput = fields[1].shadowRoot.querySelector("input");
            floatInput.focus();
            key(floatInput, "ArrowUp");
            key(floatInput, "ArrowUp");
            key(floatInput, "ArrowUp");
            result.float = fields[1].value;
            return result;
        }"""
    )

    assert result["shown"] == "999", result
    assert ["qty", "999"] in result["submitted"], result
    assert result["afterStep"] == ["1,000", 1000], result
    assert result["afterRefocus"] == 1000, result
    assert result["cleared"] == ["", True], result
    assert result["property"] == ["5", 5], result
    assert result["float"] == "0.3", result
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_number_field_readonly_ignores_keys_and_spinner_click_steps(base_url, page):
    """
        Arrow keys do not change a readonly field; activating a spinner button
        without a pointer (keyboard / assistive technology) steps and emits
        mj-change.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-number-field")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-number-field")

    _load_html(
        page=page,
        html=(
            '<div id="probe">'
            '<mj-number-field id="ro" value="5" readonly></mj-number-field>'
            '<mj-number-field id="rw" value="5"></mj-number-field>'
            '</div>'
        ),
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-number-field")
    frame.wait_for_function("() => document.getElementById('probe') !== null")

    result = frame.evaluate(
        """async () => {
            const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
            await wait(100);
            const readonly = document.getElementById("ro");
            const editable = document.getElementById("rw");
            const readonlyInput = readonly.shadowRoot.querySelector("input");
            readonlyInput.focus();
            readonlyInput.dispatchEvent(
                new KeyboardEvent("keydown", { key: "ArrowUp", bubbles: true, composed: true, cancelable: true })
            );
            const changes = [];
            editable.addEventListener("mj-change", (event) => changes.push(event.detail.valueAsNumber));
            editable.shadowRoot.querySelector("[part='increment-button']").click();
            return { readonly: readonly.value, editable: editable.value, changes: changes };
        }"""
    )

    assert result["readonly"] == "5", result
    assert result["editable"] == "6", result
    assert result["changes"] == [6], result
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_number_field_spinner_position_stacked(base_url, page):
    """
        spinner-position="stacked" puts the increment button above the input
        and the decrement button below it; the default ("side") keeps both
        beside the input, as does an unknown value.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-number-field")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-number-field")

    _load_html(
        page=page,
        html=(
            '<mj-number-field id="side" label="Side" value="2"></mj-number-field>'
            '<mj-number-field id="stacked" label="Stacked" value="2" spinner-position="stacked"></mj-number-field>'
            '<mj-number-field id="odd" label="Unknown" value="2" spinner-position="diagonal"></mj-number-field>'
        ),
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-number-field")
    frame.wait_for_function("() => document.getElementById('odd') !== null && document.getElementById('odd').shadowRoot !== null")

    result = frame.evaluate(
        """async () => {
            const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
            await wait(50);
            const layout = (id) => {
                const root = document.getElementById(id).shadowRoot;
                const box = (selector) => root.querySelector(selector).getBoundingClientRect();
                const input = box("input");
                const inc = box("[part='increment-button']");
                const dec = box("[part='decrement-button']");
                return {
                    incAbove: inc.bottom <= input.top + 1,
                    decBelow: dec.top >= input.bottom - 1,
                    besideInput: inc.left >= input.right - 1 && dec.left >= input.right - 1
                };
            };
            const stacked = document.getElementById("stacked");
            const before = stacked.valueAsNumber;
            stacked.shadowRoot.querySelector("[part='increment-button']").click();
            return { side: layout("side"), stacked: layout("stacked"), odd: layout("odd"),
                     stepped: [before, stacked.valueAsNumber] };
        }"""
    )

    assert result["side"] == {"incAbove": False, "decBelow": False, "besideInput": True}, result
    assert result["stacked"]["incAbove"] is True and result["stacked"]["decBelow"] is True, result
    assert result["stacked"]["besideInput"] is False, result
    assert result["odd"]["besideInput"] is True, result
    assert result["stepped"] == [2, 3], result
    return


# ===========================================================================
# mj-textarea
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_textarea_renders(base_url, page):
    """
        Verify mj-textarea renders a visible textarea element.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-textarea")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-textarea")

    inner = frame.locator("mj-textarea textarea")
    expect(inner).to_be_visible()
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_textarea_emits_mj_input(base_url, page):
    """
        Typing into mj-textarea fires mj-input with value and charCount.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-textarea")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-textarea")

    _install_event_collector(frame=frame, tag="mj-textarea", events=["mj-input"])

    inner = frame.locator("mj-textarea textarea")
    inner.fill("hello world")

    events = _get_events(frame=frame)
    input_events = [e for e in events if e["name"] == "mj-input"]
    assert len(input_events) > 0
    last = input_events[-1]
    assert last["detail"]["value"] == "hello world"
    assert last["detail"]["charCount"] == 11
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_textarea_value_attribute_shown_and_submitted(base_url, page):
    """
        The value attribute is shown and submitted at first render and
        restored by a form reset.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-textarea")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-textarea")

    _load_html(
        page=page,
        html='<form id="probe"><mj-textarea name="notes" value="Existing notes"></mj-textarea></form>',
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-textarea")
    frame.wait_for_function("() => document.getElementById('probe') !== null")

    result = frame.evaluate(
        """async () => {
            const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
            await wait(100);
            const form = document.getElementById("probe");
            const entries = () => Array.from(new FormData(form).entries());
            const field = form.querySelector("mj-textarea");
            const textarea = field.shadowRoot.querySelector("textarea");
            const result = { shown: textarea.value, submitted: entries() };
            field.value = "Changed";
            form.reset();
            result.afterReset = textarea.value;
            return result;
        }"""
    )

    assert result["shown"] == "Existing notes", result
    assert result["submitted"] == [["notes", "Existing notes"]], result
    assert result["afterReset"] == "Existing notes", result
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_textarea_count_words(base_url, page):
    """
        When count-words is set, mj-input events include a wordCount.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-textarea")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-textarea")

    _load_html(
        page=page,
        html='<mj-textarea label="Bio" count-words maxlength="200"></mj-textarea>',
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-textarea")

    _install_event_collector(frame=frame, tag="mj-textarea", events=["mj-input"])

    inner = frame.locator("mj-textarea textarea")
    inner.fill("one two three")

    events = _get_events(frame=frame)
    input_events = [e for e in events if e["name"] == "mj-input"]
    assert len(input_events) > 0
    last = input_events[-1]
    assert last["detail"]["wordCount"] == 3
    return


# ===========================================================================
# mj-rich-text-editor
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_rich_text_editor_renders(base_url, page):
    """
        Verify mj-rich-text-editor renders with a toolbar.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-rich-text-editor")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-rich-text-editor")

    el = frame.locator("mj-rich-text-editor")
    expect(el).to_be_visible()
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_rich_text_editor_toolbar_buttons_present(base_url, page):
    """
        mj-rich-text-editor has toolbar buttons (tb-btn) rendered.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-rich-text-editor")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-rich-text-editor")

    buttons = frame.locator("mj-rich-text-editor .tb-btn")
    count = buttons.count()
    assert count > 0
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_rich_text_editor_typing_emits_mj_input(base_url, page):
    """
        Typing in the contenteditable area of mj-rich-text-editor fires mj-input.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-rich-text-editor")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-rich-text-editor")

    _install_event_collector(
        frame=frame,
        tag="mj-rich-text-editor",
        events=["mj-input"],
    )

    editor_area = frame.locator("mj-rich-text-editor [contenteditable]")
    editor_area.click()
    editor_area.type("Rich content here")

    # Give the debounce time to fire
    page.wait_for_timeout(600)

    events = _get_events(frame=frame)
    input_events = [e for e in events if e["name"] == "mj-input"]
    assert len(input_events) > 0
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_rich_text_editor_sanitizer_strips_scripts_and_attributes(base_url, page):
    """
        The default sanitizer never runs handlers, removes non-allow-listed attributes
        and javascript: URLs, and re-checks children hoisted out of a wrapper.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-rich-text-editor")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-rich-text-editor")

    result = frame.evaluate(
        """async () => {
            window.top.__rteHits = 0;
            const el = document.querySelector("mj-rich-text-editor");
            const vectors = [
                '<img src=x onerror="top.__rteHits++">',
                '<b onmouseover="top.__rteHits++" style="color:red">bold</b>',
                '<a href="javascript:top.__rteHits++">bad</a>',
                '<div><img src=x onerror="top.__rteHits++"></div>',
                '<span><iframe srcdoc="x"></iframe>text</span>',
                '<a href="https://example.com/" onclick="x()">ok</a>'
            ];
            const out = [];
            for (const vector of vectors) {
                el.value = vector;
                out.push(el.value);
            }
            await new Promise(r => setTimeout(r, 300));
            return { values: out, hits: window.top.__rteHits };
        }"""
    )

    assert result["hits"] == 0
    assert result["values"] == [
        "",
        "<b>bold</b>",
        "<a>bad</a>",
        "",
        "text",
        '<a href="https://example.com/">ok</a>',
    ]
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_rich_text_editor_value_attribute_and_change_on_blur(base_url, page):
    """
        The value attribute is shown at first render, and typing followed by blur
        emits mj-change.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-rich-text-editor")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-rich-text-editor")

    _load_html(
        page=page,
        html='<mj-rich-text-editor label="Body" value="<p>Hello</p>"></mj-rich-text-editor><input id="after">',
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-rich-text-editor")

    editor_area = frame.locator("mj-rich-text-editor [contenteditable]")
    expect(editor_area).to_have_text("Hello")

    _install_event_collector(frame=frame, tag="mj-rich-text-editor", events=["mj-change"])

    editor_area.click()
    editor_area.press("End")
    editor_area.type(" world")
    frame.locator("#after").focus()

    events = _get_events(frame=frame)
    change_events = [e for e in events if e["name"] == "mj-change"]
    assert len(change_events) == 1
    assert "world" in change_events[0]["detail"]["text"]
    return


# ===========================================================================
# mj-markdown-editor
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_markdown_editor_renders(base_url, page):
    """
        Verify mj-markdown-editor renders in the preview.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-markdown-editor")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-markdown-editor")

    el = frame.locator("mj-markdown-editor")
    expect(el).to_be_visible()
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_markdown_editor_emits_mj_input(base_url, page):
    """
        Typing in mj-markdown-editor fires mj-input with the markdown value.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-markdown-editor")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-markdown-editor")

    _install_event_collector(frame=frame, tag="mj-markdown-editor", events=["mj-input"])

    ta = frame.locator("mj-markdown-editor textarea")
    ta.fill("# Hello markdown")

    events = _get_events(frame=frame)
    input_events = [e for e in events if e["name"] == "mj-input"]
    assert len(input_events) > 0
    assert "Hello markdown" in input_events[-1]["detail"]["value"]
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_markdown_editor_view_change(base_url, page):
    """
        Clicking the Preview mode button on mj-markdown-editor emits mj-view-change.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-markdown-editor")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-markdown-editor")

    _install_event_collector(
        frame=frame,
        tag="mj-markdown-editor",
        events=["mj-view-change"],
    )

    # Click the "Preview" toolbar button (data-view="preview")
    preview_btn = frame.locator("mj-markdown-editor [data-view='preview']")
    preview_btn.click()

    events = _get_events(frame=frame)
    view_events = [e for e in events if e["name"] == "mj-view-change"]
    assert len(view_events) == 1
    assert view_events[-1]["detail"]["view"] == "preview"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_markdown_editor_preview_is_sanitized(base_url, page):
    """
        The preview renders the value attribute, drops javascript: links and quote
        breakouts, and renders block quotes and lists.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-markdown-editor")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-markdown-editor")

    _load_html(
        page=page,
        html='<mj-markdown-editor view="preview" value="seed"></mj-markdown-editor>',
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-markdown-editor")

    preview = frame.evaluate("() => document.querySelector('mj-markdown-editor').previewHtml")
    assert preview == "<p>seed</p>"

    preview = frame.evaluate(
        """() => {
            const el = document.querySelector("mj-markdown-editor");
            el.value = [
                "[a](javascript:alert(1)) [b](x\\" onmouseover=\\"alert(1)) snake_case_name",
                "",
                "> quoted",
                "",
                "1. one",
                "2. two"
            ].join("\\n");
            return el.previewHtml;
        }"""
    )

    # The quote breakout stays inert text: serialized text keeps the literal quote,
    # so the check is that no element carries the handler attribute.
    assert "javascript:" not in preview
    has_handler = frame.evaluate(
        """() => {
            const pane = document.querySelector("mj-markdown-editor").shadowRoot.querySelector(".preview-content");
            return Array.from(pane.querySelectorAll("*")).some(n => n.hasAttribute("onmouseover"));
        }"""
    )
    assert has_handler is False
    assert "snake_case_name" in preview
    assert "<blockquote><p>quoted</p></blockquote>" in preview
    assert "<ol><li>one</li><li>two</li></ol>" in preview
    return


# ===========================================================================
# mj-code-editor
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_code_editor_renders(base_url, page):
    """
        Verify mj-code-editor renders with a textarea.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-code-editor")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-code-editor")

    el = frame.locator("mj-code-editor")
    expect(el).to_be_visible()
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_code_editor_emits_mj_input(base_url, page):
    """
        Typing in mj-code-editor fires mj-input events with value and lineCount.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-code-editor")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-code-editor")

    _install_event_collector(frame=frame, tag="mj-code-editor", events=["mj-input"])

    ta = frame.locator("mj-code-editor textarea")
    ta.fill("const x = 1;\nconst y = 2;")

    events = _get_events(frame=frame)
    input_events = [e for e in events if e["name"] == "mj-input"]
    assert len(input_events) > 0
    last = input_events[-1]
    assert "const x" in last["detail"]["value"]
    assert last["detail"]["lineCount"] >= 2
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_code_editor_value_property(base_url, page):
    """
        The value property on mj-code-editor reflects the current content.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-code-editor")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-code-editor")

    ta = frame.locator("mj-code-editor textarea")
    ta.fill("console.log('test');")

    val = frame.evaluate("() => document.querySelector('mj-code-editor').value")
    assert "console.log" in val
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_code_editor_value_attribute_and_tab_indents_selection(base_url, page):
    """
        The value attribute fills the editor and gutter at first render; Tab with a
        multi-line selection indents every line, Shift+Tab outdents them again.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-code-editor")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-code-editor")

    _load_html(
        page=page,
        html='<mj-code-editor tab-size="2" value="a = 1&#10;b = 2&#10;c = 3"></mj-code-editor>',
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-code-editor")

    ta = frame.locator("mj-code-editor textarea")
    expect(ta).to_have_value("a = 1\nb = 2\nc = 3")
    expect(frame.locator("mj-code-editor .gutter-line")).to_have_count(3)

    # Select from inside line 1 to inside line 2.
    frame.evaluate("() => document.querySelector('mj-code-editor').shadowRoot.querySelector('textarea').setSelectionRange(2, 8)")
    ta.press("Tab")
    expect(ta).to_have_value("  a = 1\n  b = 2\nc = 3")
    assert frame.evaluate("() => document.querySelector('mj-code-editor').value") == "  a = 1\n  b = 2\nc = 3"

    ta.press("Shift+Tab")
    expect(ta).to_have_value("a = 1\nb = 2\nc = 3")
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_code_editor_highlight_classes_are_stylable(base_url, page):
    """
        The highlighter's classes can be styled: `highlightStyles` adopts CSS
        into the shadow root, and every token is exported as part `token`
        plus `token-<class>` for page CSS.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-code-editor")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-code-editor")

    _load_html(
        page=page,
        html=(
            '<style>#by-part::part(token-tok-k) { color: rgb(0, 128, 0); }</style>'
            '<mj-code-editor id="by-sheet" value="let a = 1"></mj-code-editor>'
            '<mj-code-editor id="by-part" value="let b = 2"></mj-code-editor>'
        ),
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-code-editor")
    frame.wait_for_function("() => document.getElementById('by-part') !== null && document.getElementById('by-part').shadowRoot !== null")

    result = frame.evaluate(
        """async () => {
            const highlight = (code) => code.replace(/\\b(let)\\b/g, '<span class="tok-k">$1</span>');
            const sheetEditor = document.getElementById("by-sheet");
            const partEditor = document.getElementById("by-part");
            sheetEditor.highlighter = highlight;
            partEditor.highlighter = highlight;
            sheetEditor.highlightStyles = ".tok-k { color: rgb(255, 0, 0); }";
            const token = (editor) => editor.shadowRoot.querySelector("[part~='highlight-layer'] .tok-k");
            const result = {
                sheetColor: getComputedStyle(token(sheetEditor)).color,
                part: token(partEditor).getAttribute("part"),
                partColor: getComputedStyle(token(partEditor)).color
            };
            sheetEditor.highlightStyles = null;
            result.afterClear = getComputedStyle(token(sheetEditor)).color;
            result.sheets = sheetEditor.shadowRoot.adoptedStyleSheets.length;
            return result;
        }"""
    )

    assert result["sheetColor"] == "rgb(255, 0, 0)", result
    assert result["part"] == "token token-tok-k", result
    assert result["partColor"] == "rgb(0, 128, 0)", result
    assert result["afterClear"] != "rgb(255, 0, 0)", result
    return


# ===========================================================================
# mj-inline-edit
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_inline_edit_renders_display_value(base_url, page):
    """
        mj-inline-edit shows the value attribute at first render, and a value set
        through the JS property afterwards.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-inline-edit")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-inline-edit")

    _load_html(
        page=page,
        html='<mj-inline-edit label="Title" trigger="click" value="Initial Title"></mj-inline-edit>',
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-inline-edit")

    display = frame.locator("mj-inline-edit .display-text")
    expect(display).to_have_text("Initial Title")
    assert frame.evaluate("() => document.querySelector('mj-inline-edit').value") == "Initial Title"

    frame.evaluate(
        "() => { document.querySelector('mj-inline-edit').value = 'My Title'; }"
    )

    el = frame.locator("mj-inline-edit")
    expect(el).to_be_visible()
    expect(display).to_have_text("My Title")
    val = frame.evaluate("() => document.querySelector('mj-inline-edit').value")
    assert val == "My Title"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_inline_edit_focus_elsewhere_cancels_without_stealing_focus(base_url, page):
    """
        Moving focus to another field cancels the edit and leaves focus on that field.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-inline-edit")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-inline-edit")

    _load_html(
        page=page,
        html='<mj-inline-edit value="Name" label="Name"></mj-inline-edit><input id="after">',
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-inline-edit")

    frame.locator("mj-inline-edit [part='edit-trigger']").click()
    assert frame.evaluate("() => document.querySelector('mj-inline-edit').editing") is True

    frame.locator("#after").focus()
    assert frame.evaluate("() => document.querySelector('mj-inline-edit').editing") is False
    assert frame.evaluate("() => document.activeElement.id") == "after"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_inline_edit_emits_mj_edit_start(base_url, page):
    """
        Clicking the edit button fires mj-edit-start.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-inline-edit")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-inline-edit")

    _load_html(
        page=page,
        html='<mj-inline-edit value="My Title" label="Title"></mj-inline-edit>',
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-inline-edit")

    _install_event_collector(
        frame=frame,
        tag="mj-inline-edit",
        events=["mj-edit-start"],
    )

    edit_btn = frame.locator("mj-inline-edit [part='edit-trigger']")
    edit_btn.click()

    events = _get_events(frame=frame)
    start_events = [e for e in events if e["name"] == "mj-edit-start"]
    assert len(start_events) > 0
    return


# ===========================================================================
# mj-masked-input
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_masked_input_renders(base_url, page):
    """
        Verify mj-masked-input renders with a mask applied.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-masked-input")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-masked-input")

    el = frame.locator("mj-masked-input")
    expect(el).to_be_visible()
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_masked_input_emits_mj_input_with_raw_value(base_url, page):
    """
        Typing digits into a date mask fires mj-input with rawValue.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-masked-input")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-masked-input")

    _load_html(
        page=page,
        html='<mj-masked-input label="DOB" mask="99/99/9999" show-mask></mj-masked-input>',
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-masked-input")

    _install_event_collector(
        frame=frame,
        tag="mj-masked-input",
        events=["mj-input"],
    )

    inner = frame.locator("mj-masked-input input")
    inner.click()
    inner.type("01")

    events = _get_events(frame=frame)
    input_events = [e for e in events if e["name"] == "mj-input"]
    assert len(input_events) > 0
    last = input_events[-1]
    assert "rawValue" in last["detail"]
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_masked_input_value_attribute_and_empty_value(base_url, page):
    """
        An unformatted value attribute is fitted to the mask; placeholder
        characters never reach value or rawValue; an emptied field submits
        ""; an incomplete value is invalid even when not required.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-masked-input")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-masked-input")

    _load_html(
        page=page,
        html=(
            '<form id="probe">'
            '<mj-masked-input name="ph" mask="(999) 999-9999" value="5551234567"></mj-masked-input>'
            '<mj-masked-input name="d" mask="99/99/9999"></mj-masked-input>'
            '</form>'
        ),
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-masked-input")
    frame.wait_for_function("() => document.getElementById('probe') !== null")

    result = frame.evaluate(
        """async () => {
            const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
            await wait(100);
            const form = document.getElementById("probe");
            const entries = () => Array.from(new FormData(form).entries());
            const fields = form.querySelectorAll("mj-masked-input");
            const phone = fields[0];
            const date = fields[1];
            const result = {
                shown: phone.shadowRoot.querySelector("input").value,
                raw: phone.rawValue,
                submitted: entries()
            };
            date.value = "1";
            result.partial = [date.value, date.rawValue, date.checkValidity()];
            date.value = "";
            result.empty = [date.value, date.checkValidity(), entries()[1]];
            return result;
        }"""
    )

    assert result["shown"] == "(555) 123-4567", result
    assert result["raw"] == "5551234567", result
    assert ["ph", "(555) 123-4567"] in result["submitted"], result
    assert result["partial"] == ["1", "1", False], result
    assert result["empty"] == ["", True, ["d", ""]], result
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_masked_input_select_all_backspace_clears(base_url, page):
    """
        Selecting everything and pressing Backspace clears the whole value.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-masked-input")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-masked-input")

    _load_html(
        page=page,
        html='<div id="probe"><mj-masked-input label="DOB" mask="99/99/9999" value="01022024"></mj-masked-input></div>',
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-masked-input")
    frame.wait_for_function("() => document.getElementById('probe') !== null")

    inner = frame.locator("mj-masked-input input")
    inner.click()
    inner.press("Control+a")
    inner.press("Backspace")

    value = frame.evaluate("() => document.querySelector('mj-masked-input').value")
    assert value == "", value
    return


# ===========================================================================
# mj-token-input
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_token_input_renders(base_url, page):
    """
        Verify mj-token-input renders in the preview.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-token-input")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-token-input")

    el = frame.locator("mj-token-input")
    expect(el).to_be_visible()
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_token_input_add_token_on_enter(base_url, page):
    """
        Typing a value and pressing Enter adds a token and emits mj-change.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-token-input")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-token-input")

    _load_html(
        page=page,
        html='<mj-token-input label="Tags" placeholder="Add a tag"></mj-token-input>',
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-token-input")

    _install_event_collector(
        frame=frame,
        tag="mj-token-input",
        events=["mj-change", "mj-token-add"],
    )

    inner = frame.locator("mj-token-input input")
    inner.fill("alpha")
    inner.press("Enter")

    events = _get_events(frame=frame)
    change_events = [e for e in events if e["name"] == "mj-change"]
    assert len(change_events) > 0
    assert "alpha" in change_events[-1]["detail"]["tokens"]
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_token_input_required_and_value_attribute(base_url, page):
    """
        Tokens from the value attribute are rendered and submitted; a
        required token input is invalid only while it has no tokens.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-token-input")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-token-input")

    _load_html(
        page=page,
        html='<form id="probe"><mj-token-input name="tags" value="red, green" required></mj-token-input></form>',
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-token-input")
    frame.wait_for_function("() => document.getElementById('probe') !== null")

    result = frame.evaluate(
        """async () => {
            const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
            await wait(100);
            const form = document.getElementById("probe");
            const entries = () => Array.from(new FormData(form).entries());
            const field = form.querySelector("mj-token-input");
            const chips = () => Array.from(field.shadowRoot.querySelectorAll(".chip-label")).map((chip) => chip.textContent);
            const result = { chips: chips(), submitted: entries(), valid: field.checkValidity() };
            field.tokens = [];
            result.empty = field.checkValidity();
            field.tokens = ["blue"];
            result.oneToken = field.checkValidity();
            form.reset();
            result.afterReset = chips();
            return result;
        }"""
    )

    assert result["chips"] == ["red", "green"], result
    assert result["submitted"] == [["tags", "red"], ["tags", "green"]], result
    assert result["valid"] is True, result
    assert result["empty"] is False, result
    assert result["oneToken"] is True, result
    assert result["afterReset"] == ["red", "green"], result
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_token_input_keyboard_removes_chip_and_keeps_focus(base_url, page):
    """
        Arrow Left moves focus to the last chip and Delete removes it,
        returning focus to the input.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-token-input")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-token-input")

    _load_html(
        page=page,
        html='<div id="probe"><mj-token-input label="Tags" value="alpha,beta"></mj-token-input></div>',
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-token-input")
    frame.wait_for_function("() => document.getElementById('probe') !== null")

    inner = frame.locator("mj-token-input input")
    inner.click()
    inner.press("ArrowLeft")
    selected = frame.evaluate(
        "() => document.querySelector('mj-token-input').shadowRoot.activeElement.getAttribute('aria-selected')"
    )
    assert selected == "true", selected

    page.keyboard.press("Delete")
    state = frame.evaluate(
        """() => {
            const field = document.querySelector("mj-token-input");
            const input = field.shadowRoot.querySelector("input");
            return { tokens: field.tokens, inputFocused: field.shadowRoot.activeElement === input };
        }"""
    )
    assert state["tokens"] == ["alpha"], state
    assert state["inputFocused"] is True, state
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_token_input_chips_hold_no_interactive_descendants(base_url, page):
    """
        A chip is an option of the chips listbox, so it holds no focusable
        or interactive element (axe nested-interactive): the remove "x" is
        an aria-hidden span that still removes its chip on click, Delete on
        the focused chip still removes it, and a disabled field marks its
        chips listbox aria-disabled.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-token-input")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-token-input")

    _load_html(
        page=page,
        html=(
            '<div id="probe"><mj-token-input id="tags" label="Tags" value="alpha,beta,gamma"></mj-token-input>'
            '<mj-token-input id="off" label="Off" value="x" disabled></mj-token-input></div>'
        ),
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-token-input")
    frame.wait_for_function(
        """() => {
            const field = document.getElementById('tags');
            return field !== null && field.shadowRoot !== null &&
                field.shadowRoot.querySelectorAll('[role=option]').length === 3;
        }""",
        timeout=10000,
    )

    structure = frame.evaluate(
        """() => {
            const root = document.getElementById("tags").shadowRoot;
            const chips = Array.from(root.querySelectorAll("[role=option]"));
            return {
                nested: chips.map((chip) => chip.querySelectorAll(
                    "button, input, select, textarea, a[href], [tabindex], [role=button]").length),
                removeHidden: chips.map((chip) => chip.querySelector("[part=token-remove]").getAttribute("aria-hidden")),
                offDisabled: document.getElementById("off").shadowRoot.querySelector("[role=listbox][part=tokens]").getAttribute("aria-disabled"),
                onDisabled: root.querySelector("[role=listbox][part=tokens]").getAttribute("aria-disabled")
            };
        }"""
    )
    assert structure["nested"] == [0, 0, 0], structure
    assert structure["removeHidden"] == ["true", "true", "true"], structure
    assert structure["offDisabled"] == "true" and structure["onDisabled"] is None, structure

    frame.locator("#tags").evaluate("(field) => field.shadowRoot.querySelector('[part=token-remove]').click()")
    after_click = frame.evaluate("() => document.getElementById('tags').tokens")
    assert after_click == ["beta", "gamma"], after_click

    inner = frame.locator("#tags input")
    inner.click()
    inner.press("ArrowLeft")
    page.keyboard.press("Delete")
    after_key = frame.evaluate("() => document.getElementById('tags').tokens")
    assert after_key == ["beta"], after_key

    return


# ===========================================================================
# mj-otp-input
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_otp_input_renders_segments(base_url, page):
    """
        mj-otp-input renders the correct number of segment inputs.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-otp-input")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-otp-input")

    _load_html(
        page=page,
        html='<mj-otp-input label="Code" length="6" inputtype="numeric"></mj-otp-input>',
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-otp-input")

    segments = frame.locator("mj-otp-input .segment")
    assert segments.count() == 6
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_otp_input_emits_mj_complete_on_fill(base_url, page):
    """
        Filling all OTP segments fires the mj-complete event.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-otp-input")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-otp-input")

    _load_html(
        page=page,
        html='<mj-otp-input label="Code" length="4" inputtype="numeric"></mj-otp-input>',
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-otp-input")

    _install_event_collector(
        frame=frame,
        tag="mj-otp-input",
        events=["mj-complete", "mj-input"],
    )

    first_seg = frame.locator("mj-otp-input .segment").first
    first_seg.click()
    first_seg.type("1234")

    events = _get_events(frame=frame)
    complete_events = [e for e in events if e["name"] == "mj-complete"]
    assert len(complete_events) > 0
    assert complete_events[-1]["detail"]["value"] == "1234"
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_otp_input_filters_typed_characters_and_value_before_connect(base_url, page):
    """
        Typed characters that do not match inputtype are rejected; a value
        assigned before the element is connected is shown.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-otp-input")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-otp-input")

    _load_html(
        page=page,
        html='<div id="probe"><mj-otp-input label="Code" length="4" inputtype="numeric"></mj-otp-input></div>',
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-otp-input")
    frame.wait_for_function("() => document.getElementById('probe') !== null")

    early = frame.evaluate(
        """async () => {
            const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
            const element = document.createElement("mj-otp-input");
            element.setAttribute("length", "4");
            element.value = "1234";
            document.getElementById("probe").appendChild(element);
            await wait(50);
            return Array.from(element.shadowRoot.querySelectorAll(".segment")).map((segment) => segment.value).join("");
        }"""
    )
    assert early == "1234", early

    first_seg = frame.locator("mj-otp-input .segment").first
    first_seg.click()
    first_seg.type("a1#2")

    value = frame.evaluate("() => document.querySelector('mj-otp-input').value")
    assert value == "12", value
    return


# ===========================================================================
# mj-slider
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_slider_renders(base_url, page):
    """
        Verify mj-slider renders with a thumb element.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-slider")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-slider")

    thumb = frame.locator("mj-slider [part~='thumb-a']")
    expect(thumb).to_be_visible()
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_slider_keyboard_emits_mj_change(base_url, page):
    """
        Arrow-key on mj-slider thumb fires mj-change event.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-slider")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-slider")

    _load_html(
        page=page,
        html='<mj-slider label="Volume" min="0" max="100" step="5" value="40"></mj-slider>',
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-slider")

    _install_event_collector(frame=frame, tag="mj-slider", events=["mj-change"])

    thumb = frame.locator("mj-slider [part~='thumb-a']")
    thumb.focus()
    thumb.press("ArrowRight")

    events = _get_events(frame=frame)
    change_events = [e for e in events if e["name"] == "mj-change"]
    assert len(change_events) > 0
    assert change_events[-1]["detail"]["value"] == 45
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_slider_value_attribute(base_url, page):
    """
        mj-slider reflects the value attribute on the thumb aria-valuenow.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-slider")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-slider")

    _load_html(
        page=page,
        html='<mj-slider label="Vol" min="0" max="100" value="60"></mj-slider>',
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-slider")

    thumb = frame.locator("mj-slider [part~='thumb-a']")
    expect(thumb).to_have_attribute("aria-valuenow", "60")
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_slider_range_submits_both_values_and_keeps_position(base_url, page):
    """
        Range mode submits both values; an unrelated attribute change does
        not reset a moved thumb; the value property moves the thumb.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-slider")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-slider")

    _load_html(
        page=page,
        html=(
            '<form id="probe">'
            '<mj-slider name-start="lo" name-end="hi" range value="20" value-end="80" label="Price"></mj-slider>'
            '<mj-slider name="vol" value="40" step="5" label="Volume"></mj-slider>'
            '</form>'
        ),
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-slider")
    frame.wait_for_function("() => document.getElementById('probe') !== null")

    result = frame.evaluate(
        """async () => {
            const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
            await wait(100);
            const form = document.getElementById("probe");
            const entries = () => Array.from(new FormData(form).entries());
            const single = form.querySelectorAll("mj-slider")[1];
            const thumb = single.shadowRoot.querySelector("[part~='thumb-a']");
            const result = { submitted: entries() };
            thumb.dispatchEvent(
                new KeyboardEvent("keydown", { key: "ArrowRight", bubbles: true, composed: true, cancelable: true })
            );
            single.setAttribute("label", "Loudness");
            result.afterLabel = [single.value, thumb.getAttribute("aria-valuenow")];
            single.value = 70;
            result.afterProperty = thumb.getAttribute("aria-valuenow");
            form.reset();
            result.afterReset = single.value;
            return result;
        }"""
    )

    assert result["submitted"] == [["lo", "20"], ["hi", "80"], ["vol", "40"]], result
    assert result["afterLabel"] == ["45", "45"], result
    assert result["afterProperty"] == "70", result
    assert result["afterReset"] == "40", result
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_slider_required_error_message_and_tick_labels(base_url, page):
    """
        A required slider left on min is valueMissing: reportValidity shows
        the error-message text, marks the thumb invalid and fires
        mj-invalid; moving the thumb clears it. tickLabels are drawn under
        the track and name the value of a thumb resting on them.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-slider")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-slider")

    _load_html(
        page=page,
        html=(
            '<mj-slider id="rate" label="Rate" min="0" max="10" required error-message="Pick a rating."></mj-slider>'
            '<mj-slider id="effort" label="Effort" min="1" max="5" value="3"></mj-slider>'
        ),
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-slider")
    frame.wait_for_function("() => document.getElementById('effort') !== null && document.getElementById('effort').shadowRoot !== null")

    result = frame.evaluate(
        """async () => {
            const rate = document.getElementById("rate");
            const invalids = [];
            rate.addEventListener("mj-invalid", (event) => invalids.push(event.detail.validationMessage));
            const thumb = rate.shadowRoot.querySelector("[part~='thumb-a']");
            const error = rate.shadowRoot.querySelector("[part='error']");
            const result = { valueMissing: rate.validity.valueMissing, shownBefore: error.hasAttribute("data-visible") };
            result.reported = rate.reportValidity();
            result.error = [error.hasAttribute("data-visible"), error.textContent, thumb.getAttribute("aria-invalid"),
                            (thumb.getAttribute("aria-describedby") || "").includes(error.id)];
            thumb.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowRight", bubbles: true, composed: true, cancelable: true }));
            result.afterMove = [rate.checkValidity(), error.hasAttribute("data-visible"), thumb.getAttribute("aria-invalid")];
            result.invalids = invalids;

            const effort = document.getElementById("effort");
            effort.tickLabels = [{ value: 1, label: "Trivial" }, { value: 3, label: "Moderate" },
                                 { value: 5, label: "Huge" }, { value: 9, label: "Outside" }];
            const labels = Array.from(effort.shadowRoot.querySelectorAll("[part='tick-label']"));
            result.labels = labels.map((label) => label.textContent);
            result.labelsShown = labels.every((label) => label.getBoundingClientRect().width > 0);
            const effortThumb = effort.shadowRoot.querySelector("[part~='thumb-a']");
            result.valueText = effortThumb.getAttribute("aria-valuetext");
            effortThumb.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowRight", bubbles: true, composed: true, cancelable: true }));
            result.unlabelledText = effortThumb.getAttribute("aria-valuetext");
            return result;
        }"""
    )

    assert result["valueMissing"] is True and result["shownBefore"] is False, result
    assert result["reported"] is False, result
    assert result["error"] == [True, "Pick a rating.", "true", True], result
    assert result["afterMove"] == [True, False, None], result
    assert result["invalids"] == ["Pick a rating."], result
    assert result["labels"] == ["Trivial", "Moderate", "Huge"], result
    assert result["labelsShown"] is True, result
    assert result["valueText"] == "Moderate", result
    assert result["unlabelledText"] == "4", result
    return


# ===========================================================================
# mj-rating
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_rating_renders_stars(base_url, page):
    """
        mj-rating renders the correct number of star items.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-rating")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-rating")

    _load_html(
        page=page,
        html='<mj-rating label="Rate it" max="5" value="3"></mj-rating>',
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-rating")

    items = frame.locator("mj-rating .item")
    assert items.count() == 5
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_rating_click_emits_mj_change(base_url, page):
    """
        Clicking a star in mj-rating fires mj-change with the new value.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-rating")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-rating")

    _load_html(
        page=page,
        html='<mj-rating label="Rate it" max="5" value="1"></mj-rating>',
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-rating")

    _install_event_collector(frame=frame, tag="mj-rating", events=["mj-change"])

    # Click the 4th star (index 3)
    fourth_star = frame.locator("mj-rating .item").nth(3)
    fourth_star.click()

    events = _get_events(frame=frame)
    change_events = [e for e in events if e["name"] == "mj-change"]
    assert len(change_events) > 0
    assert change_events[-1]["detail"]["value"] == 4
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_rating_initial_value_submitted_and_reset(base_url, page):
    """
        The initial value is submitted without interaction, a click does not
        overwrite the default, and a form reset restores it.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-rating")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-rating")

    _load_html(
        page=page,
        html='<form id="probe"><mj-rating name="score" value="3"></mj-rating></form>',
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-rating")
    frame.wait_for_function("() => document.getElementById('probe') !== null")

    result = frame.evaluate(
        """async () => {
            const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
            await wait(100);
            const form = document.getElementById("probe");
            const entries = () => Array.from(new FormData(form).entries());
            const rating = form.querySelector("mj-rating");
            const result = { submitted: entries() };
            rating.shadowRoot.querySelectorAll(".item")[4].click();
            result.afterClick = [rating.value, rating.getAttribute("value")];
            form.reset();
            result.afterReset = [rating.value, entries()];
            return result;
        }"""
    )

    assert result["submitted"] == [["score", "3"]], result
    assert result["afterClick"] == ["5", "3"], result
    assert result["afterReset"] == ["3", [["score", "3"]]], result
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_rating_keyboard_at_max_keeps_value_and_moves_focus(base_url, page):
    """
        ArrowRight or End at the maximum keeps the rating, and arrow keys move
        focus to the newly checked star.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-rating")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-rating")

    _load_html(
        page=page,
        html='<div id="probe"><mj-rating label="Rate it" max="5" value="5"></mj-rating></div>',
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-rating")
    frame.wait_for_function("() => document.getElementById('probe') !== null")

    rating = frame.locator("mj-rating")
    rating.evaluate("el => el.focus()")
    page.keyboard.press("ArrowRight")
    page.keyboard.press("End")
    assert rating.evaluate("el => el.value") == "5"

    page.keyboard.press("ArrowLeft")
    state = rating.evaluate(
        "el => [el.value, el.shadowRoot.activeElement.getAttribute('data-value')]"
    )
    assert state == ["4", "4"], state
    return


# ===========================================================================
# mj-captcha
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_captcha_renders(base_url, page):
    """
        Verify mj-captcha renders its container in the preview.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-captcha")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-captcha")

    el = frame.locator("mj-captcha")
    expect(el).to_be_visible()
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_captcha_fallback_slot(base_url, page):
    """
        The fallback slot content is accessible when no provider is configured.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-captcha")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-captcha")

    _load_html(
        page=page,
        html=(
            '<mj-captcha label="Verify" required>'
            '<p slot="fallback">Verification unavailable.</p>'
            '</mj-captcha>'
        ),
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-captcha")

    el = frame.locator("mj-captcha")
    expect(el).to_be_visible()
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_captcha_label_escaped_and_required_blocks_submit(base_url, page):
    """
        label and help-text are rendered as text; a required, unverified
        captcha is invalid from the first render and blocks the form submit.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-captcha")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-captcha")

    _load_html(
        page=page,
        html=(
            '<form id="probe" onsubmit="event.preventDefault(); window.__submits = (window.__submits || 0) + 1">'
            '<mj-captcha name="tok" required label=\'<img src="data:,x" onerror="window.__hits=1">\''
            ' help-text="<b>bold</b>"></mj-captcha>'
            '<button id="go">Go</button>'
            '</form>'
        ),
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-captcha")
    frame.wait_for_function("() => document.getElementById('probe') !== null")

    result = frame.evaluate(
        """async () => {
            const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
            await wait(100);
            const captcha = document.querySelector("mj-captcha");
            const result = {
                hits: window.__hits === undefined ? null : window.__hits,
                label: captcha.shadowRoot.querySelector(".label").textContent,
                injected: captcha.shadowRoot.querySelector("img, b") !== null,
                valid: captcha.checkValidity()
            };
            document.getElementById("go").click();
            await wait(50);
            result.submits = window.__submits === undefined ? 0 : window.__submits;
            return result;
        }"""
    )

    assert result["hits"] is None, result
    assert result["label"] == '<img src="data:,x" onerror="window.__hits=1">', result
    assert result["injected"] is False, result
    assert result["valid"] is False, result
    assert result["submits"] == 0, result
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_captcha_invisible_provider_executes_once_with_submitter(base_url, page):
    """
        An invisible provider's challenge runs once per submit and the form
        is re-submitted with the original submitter.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-captcha")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-captcha")

    _load_html(
        page=page,
        html=(
            '<form id="probe" onsubmit="event.preventDefault();'
            ' (window.__submitters = window.__submitters || []).push(event.submitter ? event.submitter.value : null)">'
            '<mj-captcha name="tok" provider="turnstile" required></mj-captcha>'
            '<button name="act" value="publish" id="go">Go</button>'
            '</form>'
        ),
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-captcha")
    frame.wait_for_function("() => document.getElementById('probe') !== null")

    result = frame.evaluate(
        """async () => {
            const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
            await wait(100);
            const captcha = document.querySelector("mj-captcha");
            let executions = 0;
            captcha.providerAdapter = {
                load: () => Promise.resolve(),
                execute: () => {
                    executions = executions + 1;
                    return Promise.resolve("token-1");
                },
                reset: () => {},
                destroy: () => {}
            };
            await wait(50);
            document.getElementById("go").click();
            await wait(100);
            return { executions: executions, submitters: window.__submitters || [], token: captcha.token };
        }"""
    )

    assert result["executions"] == 1, result
    assert result["submitters"] == ["publish"], result
    assert result["token"] == "token-1", result
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_captcha_provider_attribute_mounts_once(base_url, page):
    """
        A provider attribute in markup mounts the provider once at upgrade,
        so a missing adapter reports sdk-load-failure once.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-captcha")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-captcha")

    result = frame.evaluate(
        """async () => {
            const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
            const codes = [];
            const listener = (event) => codes.push(event.detail.code);
            document.addEventListener("mj-error", listener);
            const holder = document.createElement("div");
            holder.innerHTML = '<mj-captcha id="probe-captcha" provider="recaptcha-v2"></mj-captcha>';
            document.body.append(holder);
            await wait(100);
            const captcha = document.getElementById("probe-captcha");
            const afterUpgrade = codes.slice();
            captcha.setAttribute("provider", "hcaptcha");
            await wait(50);
            document.removeEventListener("mj-error", listener);
            return { afterUpgrade: afterUpgrade, afterChange: codes,
                     fallback: captcha.shadowRoot.querySelector("[part='fallback']").hasAttribute("data-visible") };
        }"""
    )

    assert result["afterUpgrade"] == ["sdk-load-failure"], result
    assert result["afterChange"] == ["sdk-load-failure", "sdk-load-failure"], result
    assert result["fallback"] is True, result
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_captcha_adapter_callbacks_report_a_solved_widget(base_url, page):
    """
        load() receives onVerify / onExpire / onError: a widget solved later
        verifies the captcha (no execute() needed), expiry clears it, errors
        are reported, and callbacks of a replaced adapter are ignored.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-captcha")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-captcha")

    _load_html(
        page=page,
        html='<form id="probe"><mj-captcha id="visible-captcha" name="tok" required></mj-captcha></form>',
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-captcha")
    frame.wait_for_function("() => document.getElementById('visible-captcha') !== null")

    result = frame.evaluate(
        """async () => {
            const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
            await wait(50);
            const captcha = document.getElementById("visible-captcha");
            const events = [];
            for (const name of ["mj-verified", "mj-expired", "mj-error"]) {
                captcha.addEventListener(name, (event) => events.push([name, event.detail.token || event.detail.code || ""]));
            }
            let first = null;
            captcha.providerAdapter = { load: (container, options) => { first = options; } };
            await wait(20);
            const keys = Object.keys(first).sort();
            const before = captcha.checkValidity();
            await wait(100);
            first.onVerify("tok-9");
            const solved = [captcha.verified, captcha.token, captcha.checkValidity(),
                            new FormData(document.getElementById("probe")).get("tok")];
            first.onExpire();
            const expired = [captcha.verified, captcha.token];
            first.onError(new Error("widget broke"));
            let second = null;
            captcha.providerAdapter = { load: (container, options) => { second = options; } };
            await wait(20);
            first.onVerify("stale");
            const afterStale = captcha.token;
            second.onVerify("fresh");
            return { keys: keys, before: before, solved: solved, expired: expired,
                     afterStale: afterStale, fresh: captcha.token, events: events };
        }"""
    )

    assert result["keys"] == ["onError", "onExpire", "onVerify", "siteKey", "size", "theme"], result
    assert result["before"] is False, result
    assert result["solved"] == [True, "tok-9", True, "tok-9"], result
    assert result["expired"] == [False, ""], result
    assert result["afterStale"] == "", result
    assert result["fresh"] == "fresh", result
    assert result["events"] == [["mj-verified", "tok-9"], ["mj-expired", ""], ["mj-error", "provider-error"],
                                ["mj-verified", "fresh"]], result
    return


# ===========================================================================
# mj-form
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_form_renders(base_url, page):
    """
        Verify mj-form renders with child controls.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-form")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-form")

    el = frame.locator("mj-form")
    expect(el).to_be_visible()
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_form_submit_emits_mj_submit(base_url, page):
    """
        Submitting an mj-form fires mj-submit with valid=True when fields are filled.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-form")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-form")

    _load_html(
        page=page,
        html=(
            '<mj-form id="demo-form">'
            '  <mj-text-field name="username" label="Username"></mj-text-field>'
            '  <button type="submit">Submit</button>'
            '</mj-form>'
        ),
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-form")
    frame.wait_for_function(
        "t => customElements.get(t) !== undefined",
        arg="mj-text-field",
        timeout=15000,
    )

    _install_form_value_collector(frame=frame)

    inner = frame.locator("mj-text-field input")
    inner.fill("admin")

    # A slotted native submit button submits the form and the value is collected.
    frame.locator("mj-form button[type='submit']").click()

    events = _get_events(frame=frame)
    submit_events = [e for e in events if e["name"] == "mj-submit"]
    assert len(submit_events) == 1
    assert submit_events[-1]["valid"] is True
    assert submit_events[-1]["value"] == {"username": ["admin"]}
    return


def _install_form_value_collector(frame) -> None:
    """
        Record the form's own mj-submit / mj-invalid / mj-reset events with a
        serialisable summary of their detail.

        :param frame: The Frame to install the collector in.

        :returns: None
    """

    frame.evaluate(
        """() => {
            window.__mjevents = [];
            const form = document.querySelector("mj-form");
            ["mj-submit", "mj-invalid", "mj-reset"].forEach(n => form.addEventListener(n, e => {
                if (e.target !== form) { return; }
                const detail = e.detail || {};
                const names = (detail.summary || []).map(s => s.name);
                window.__mjevents.push({ name: n, value: detail.value, valid: detail.valid, invalid: names });
            }));
        }"""
    )
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_form_documented_example_submits_with_mj_button_and_enter(base_url, page):
    """
        The documented mj-form example: an empty required form reports mj-invalid on
        mj-button submit; filled in, mj-button and Enter in a field submit the values.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-form")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-form")
    _wait_for_tag(frame=frame, tag="mj-button")
    _wait_for_tag(frame=frame, tag="mj-password-field")

    _install_form_value_collector(frame=frame)

    submit_button = frame.locator("mj-form mj-button button")
    submit_button.click()

    events = _get_events(frame=frame)
    assert [e["name"] for e in events] == ["mj-invalid"]
    assert events[0]["invalid"] == ["username", "password"]

    frame.locator("mj-text-field input").fill("alice")
    frame.locator("mj-password-field input").fill("secret")
    submit_button.click()

    frame.locator("mj-text-field input").press("Enter")

    events = _get_events(frame=frame)
    submit_events = [e for e in events if e["name"] == "mj-submit"]
    assert len(submit_events) == 2
    for event in submit_events:
        assert event["value"] == {"username": ["alice"], "password": ["secret"]}
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_form_reset_restores_slotted_controls(base_url, page):
    """
        A slotted reset button resets native and mj-* controls to their initial values
        and emits a single mj-reset.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-form")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-form")

    _load_html(
        page=page,
        html=(
            '<mj-form id="reset-form">'
            '  <input name="city" value="Austin">'
            '  <mj-text-field name="nick" value="ace"></mj-text-field>'
            '  <button type="reset">Reset</button>'
            '</mj-form>'
        ),
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-form")
    _wait_for_tag(frame=frame, tag="mj-text-field")

    _install_form_value_collector(frame=frame)

    frame.locator("input[name='city']").fill("Boston")
    frame.locator("mj-text-field input").fill("zed")
    frame.locator("mj-form button[type='reset']").click()

    events = _get_events(frame=frame)
    assert [e["name"] for e in events] == ["mj-reset"]

    value = frame.evaluate("() => document.querySelector('mj-form').value")
    assert value == {"city": ["Austin"], "nick": ["ace"]}
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_form_invalid_required_field_emits_mj_invalid(base_url, page):
    """
        Submitting mj-form with an untouched empty required field fires mj-invalid.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-form")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-form")

    _load_html(
        page=page,
        html=(
            '<mj-form id="req-form">'
            '  <mj-text-field name="email" label="Email" required></mj-text-field>'
            '</mj-form>'
        ),
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-form")
    frame.wait_for_function(
        "t => customElements.get(t) !== undefined",
        arg="mj-text-field",
        timeout=15000,
    )

    # The field is never focused: an untouched required control is invalid.
    _install_form_value_collector(frame=frame)

    frame.evaluate("() => document.querySelector('mj-form').submit()")

    events = _get_events(frame=frame)
    assert [e["name"] for e in events] == ["mj-invalid"]
    assert events[0]["invalid"] == ["email"]

    error_text = frame.locator("mj-text-field .error")
    expect(error_text).to_be_visible()
    return


# ===========================================================================
# mj-fieldset
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_fieldset_renders_legend(base_url, page):
    """
        mj-fieldset renders the legend text from the legend attribute.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-fieldset")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-fieldset")

    _load_html(
        page=page,
        html='<mj-fieldset legend="Personal Info" required></mj-fieldset>',
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-fieldset")

    legend_el = frame.locator("mj-fieldset .legend")
    expect(legend_el).to_contain_text("Personal Info")
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_fieldset_collapsible_toggle_emits_mj_toggle(base_url, page):
    """
        Clicking the legend button on a collapsible mj-fieldset emits mj-toggle.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-fieldset")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-fieldset")

    _load_html(
        page=page,
        html='<mj-fieldset legend="Details" collapsible open></mj-fieldset>',
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-fieldset")

    _install_event_collector(frame=frame, tag="mj-fieldset", events=["mj-toggle"])

    legend_btn = frame.locator("mj-fieldset .legend-btn")
    legend_btn.click()

    events = _get_events(frame=frame)
    toggle_events = [e for e in events if e["name"] == "mj-toggle"]
    assert len(toggle_events) > 0
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_fieldset_disabled_propagates_to_children(base_url, page):
    """
        A disabled mj-fieldset has the disabled attribute on its inner fieldset element.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-fieldset")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-fieldset")

    _load_html(
        page=page,
        html=(
            '<mj-fieldset legend="Section" disabled>'
            '  <input id="fs-native" name="a">'
            '  <mj-text-field id="fs-custom" name="b" label="B"></mj-text-field>'
            '</mj-fieldset>'
        ),
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-fieldset")
    _wait_for_tag(frame=frame, tag="mj-text-field")

    inner_fs = frame.locator("mj-fieldset fieldset")
    expect(inner_fs).to_have_attribute("disabled", "")

    # Slotted controls are not DOM descendants of the shadow fieldset, so the
    # component disables them itself, and re-enables them afterwards.
    expect(frame.locator("#fs-native")).to_be_disabled()
    expect(frame.locator("#fs-custom input")).to_be_disabled()

    frame.evaluate("() => { document.querySelector('mj-fieldset').disabled = false; }")
    expect(frame.locator("#fs-native")).to_be_enabled()
    expect(frame.locator("#fs-custom input")).to_be_enabled()
    return


# ===========================================================================
# mj-label
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_label_renders(base_url, page):
    """
        Verify mj-label renders visible label text.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-label")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-label")

    el = frame.locator("mj-label")
    expect(el).to_be_visible()
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_label_required_indicator(base_url, page):
    """
        mj-label with required attribute shows the required indicator.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-label")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-label")

    _load_html(
        page=page,
        html='<mj-label for="fld" required>Username</mj-label><input id="fld">',
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-label")

    indicator = frame.locator("mj-label .indicator")
    expect(indicator).to_be_visible()
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_label_emits_mj_click(base_url, page):
    """
        Clicking mj-label emits an mj-click event.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-label")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-label")

    _load_html(
        page=page,
        html='<mj-label for="tf">My Label</mj-label><input id="tf">',
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-label")

    _install_event_collector(frame=frame, tag="mj-label", events=["mj-click"])

    label_el = frame.locator("mj-label label")
    label_el.click()

    events = _get_events(frame=frame)
    click_events = [e for e in events if e["name"] == "mj-click"]
    assert len(click_events) > 0
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_label_focuses_and_names_mj_control(base_url, page):
    """
        Clicking mj-label focuses the mj-text-field it is for, and the field's inner
        input takes its accessible name from the label.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-label")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-label")
    _wait_for_tag(frame=frame, tag="mj-text-field")

    frame.locator("mj-label label").click()
    focused = frame.evaluate(
        """() => {
            const field = document.getElementById("username-field");
            const inner = field.shadowRoot.querySelector("input");
            return field.shadowRoot.activeElement === inner;
        }"""
    )
    assert focused is True

    expect(frame.get_by_role("textbox", name="Username")).to_have_count(1)
    return


# ===========================================================================
# mj-help-text
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_help_text_renders(base_url, page):
    """
        Verify mj-help-text renders its content.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-help-text")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-help-text")

    el = frame.locator("mj-help-text")
    expect(el).to_be_visible()
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_help_text_links_aria_describedby(base_url, page):
    """
        mj-help-text with a for attribute wires aria-describedby on the target.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-help-text")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-help-text")

    _load_html(
        page=page,
        html=(
            '<input id="my-input">'
            '<mj-help-text for="my-input">Enter your name.</mj-help-text>'
        ),
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-help-text")

    page.wait_for_timeout(300)

    input_el = frame.locator("#my-input")
    describedby = input_el.get_attribute("aria-describedby")
    assert describedby is not None
    assert len(describedby) > 0
    return


# ===========================================================================
# mj-error-message
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_error_message_hidden_by_default(base_url, page):
    """
        mj-error-message without visible attribute is not rendered in DOM.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-error-message")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-error-message")

    _load_html(
        page=page,
        html='<mj-error-message for="x" id="err1">Please fix this.</mj-error-message>',
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-error-message")

    el = frame.locator("mj-error-message")
    expect(el).to_be_hidden()
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_error_message_shows_and_emits_mj_show(base_url, page):
    """
        Adding visible attribute to mj-error-message makes it visible and emits mj-show.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-error-message")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-error-message")

    _load_html(
        page=page,
        html='<mj-error-message id="err2" message="Required field">Error here</mj-error-message>',
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-error-message")

    _install_event_collector(
        frame=frame,
        tag="mj-error-message",
        events=["mj-show"],
    )

    frame.evaluate(
        "() => document.querySelector('mj-error-message').setAttribute('visible', '')"
    )
    page.wait_for_timeout(400)

    events = _get_events(frame=frame)
    show_events = [e for e in events if e["name"] == "mj-show"]
    assert len(show_events) > 0
    return


# ===========================================================================
# mj-validation-summary
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_validation_summary_renders_hidden_by_default(base_url, page):
    """
        mj-validation-summary is hidden until a form fires mj-invalid.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-validation-summary")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-validation-summary")

    _load_html(
        page=page,
        html='<mj-validation-summary heading-text="{count} errors"></mj-validation-summary>',
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-validation-summary")

    el = frame.locator("mj-validation-summary")
    expect(el).to_be_hidden()
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_validation_summary_shows_on_mj_invalid(base_url, page):
    """
        mj-validation-summary becomes visible when set to visible with errors.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-validation-summary")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-validation-summary")

    _load_html(
        page=page,
        html=(
            '<mj-validation-summary always-render heading-text="{count} error(s)">'
            '</mj-validation-summary>'
        ),
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-validation-summary")

    # Set errors programmatically and show the summary
    frame.evaluate(
        """() => {
            const s = document.querySelector('mj-validation-summary');
            s.errors = [{ controlId: 'f1', label: 'Email', message: 'Required' }];
            s.setAttribute('visible', '');
        }"""
    )
    page.wait_for_timeout(300)

    summary = frame.locator("mj-validation-summary")
    expect(summary).to_be_visible()
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_validation_summary_click_below_after_fixing_last_field_submits(base_url, page):
    """
        In the documented example the summary sits above the fields and the
        buttons. Fixing the last field and clicking Save submits: the summary
        does not collapse (and move the button) during the press.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-validation-summary")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-validation-summary")
    frame.wait_for_function("() => window.mjSandbox !== undefined && window.mjSandbox.ready === true")
    frame.wait_for_function("() => document.querySelector('mj-validation-summary').hasAttribute('visible')")

    _install_form_value_collector(frame=frame)

    frame.locator("#profile-name input").fill("Ada Lovelace")
    frame.locator("#profile-email input").fill("ada@example.com")
    frame.locator("mj-button[type='submit'] button").click()
    page.wait_for_timeout(100)

    events = _get_events(frame=frame)
    assert [e["name"] for e in events] == ["mj-submit"], events
    assert events[0]["value"] == {"name": ["Ada Lovelace"], "email": ["ada@example.com"]}, events
    visible = frame.evaluate("() => document.querySelector('mj-validation-summary').hasAttribute('visible')")
    assert visible is False
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_validation_summary_reset_then_submit_keeps_new_errors(base_url, page):
    """
        form.reset(); form.submit() in one task ends with the new errors
        shown: the clear queued by the reset does not hide them.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-validation-summary")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-validation-summary")

    _load_html(
        page=page,
        html=(
            '<mj-form id="probe-form">'
            '<mj-validation-summary id="probe-summary" slot="summary"></mj-validation-summary>'
            '<mj-text-field id="probe-city" name="city" label="City" required></mj-text-field>'
            '</mj-form>'
        ),
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-form")
    frame.wait_for_function("() => document.getElementById('probe-summary') !== null")

    result = frame.evaluate(
        """async () => {
            const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
            await wait(50);
            const form = document.getElementById("probe-form");
            const summary = document.getElementById("probe-summary");
            const log = [];
            for (const name of ["mj-show", "mj-hide"]) {
                summary.addEventListener(name, () => log.push(name));
            }
            form.submit();
            form.reset();
            form.submit();
            await wait(50);
            return { log: log, visible: summary.hasAttribute("visible"), count: summary.count };
        }"""
    )

    assert result["visible"] is True, result
    assert result["count"] == 1, result
    assert result["log"][-1] == "mj-show", result
    return


# ===========================================================================
# mj-character-counter
# ===========================================================================

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_character_counter_renders(base_url, page):
    """
        Verify mj-character-counter renders in the preview.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-character-counter")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-character-counter")

    el = frame.locator("mj-character-counter")
    expect(el).to_be_visible()
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_character_counter_updates_on_input(base_url, page):
    """
        mj-character-counter updates its count display as the user types.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-character-counter")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-character-counter")

    _load_html(
        page=page,
        html=(
            '<textarea id="bio-fld"></textarea>'
            '<mj-character-counter for="bio-fld" max="100" mode="used" format="used/max"></mj-character-counter>'
        ),
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-character-counter")
    page.wait_for_timeout(300)

    ta = frame.locator("#bio-fld")
    ta.fill("hello")

    # Dispatch input event so counter picks it up
    frame.evaluate(
        "() => document.getElementById('bio-fld').dispatchEvent(new Event('input', { bubbles: true }))"
    )
    page.wait_for_timeout(200)

    count_el = frame.locator("mj-character-counter .count")
    count_text = count_el.text_content()
    assert count_text is not None
    assert len(count_text.strip()) > 0
    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_character_counter_emits_mj_count_change(base_url, page):
    """
        mj-character-counter emits mj-count-change when the linked input changes.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-character-counter")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-character-counter")

    _load_html(
        page=page,
        html=(
            '<textarea id="note-fld"></textarea>'
            '<mj-character-counter for="note-fld" max="50" mode="remaining"></mj-character-counter>'
        ),
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-character-counter")
    page.wait_for_timeout(300)

    _install_event_collector(
        frame=frame,
        tag="mj-character-counter",
        events=["mj-count-change"],
    )

    ta = frame.locator("#note-fld")
    ta.fill("test input")
    frame.evaluate(
        "() => document.getElementById('note-fld').dispatchEvent(new Event('input', { bubbles: true }))"
    )
    page.wait_for_timeout(200)

    events = _get_events(frame=frame)
    count_events = [e for e in events if e["name"] == "mj-count-change"]
    assert len(count_events) > 0
    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
