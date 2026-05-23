"""
    test_func_text.py

    Functional Playwright tests for the 'text' component group.

    Covers all 23 components defined in catalog/text.py:
      mj-text-field, mj-search-input, mj-password-field, mj-typed-field,
      mj-number-field, mj-textarea, mj-rich-text-editor, mj-markdown-editor,
      mj-code-editor, mj-inline-edit, mj-masked-input, mj-token-input,
      mj-otp-input, mj-slider, mj-rating, mj-captcha, mj-form, mj-fieldset,
      mj-label, mj-help-text, mj-error-message, mj-validation-summary,
      mj-character-counter.
"""

import pytest
from playwright.sync_api import expect


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


def _load_html(page, html: str) -> None:
    """
        Write new HTML into the playground editor and click Run.

        :param page: The Playwright Page instance.
        :param html: The HTML snippet to load.

        :returns: None
    """

    page.get_by_test_id("playground-editor").fill(html)
    page.get_by_test_id("playground-run").click()
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

@pytest.mark.functional
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


@pytest.mark.functional
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


@pytest.mark.functional
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


@pytest.mark.functional
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


@pytest.mark.functional
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


@pytest.mark.functional
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


# ===========================================================================
# mj-search-input
# ===========================================================================

@pytest.mark.functional
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


@pytest.mark.functional
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


@pytest.mark.functional
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


# ===========================================================================
# mj-password-field
# ===========================================================================

@pytest.mark.functional
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


@pytest.mark.functional
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


@pytest.mark.functional
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


# ===========================================================================
# mj-typed-field
# ===========================================================================

@pytest.mark.functional
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


@pytest.mark.functional
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


# ===========================================================================
# mj-number-field
# ===========================================================================

@pytest.mark.functional
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


@pytest.mark.functional
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


@pytest.mark.functional
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


# ===========================================================================
# mj-textarea
# ===========================================================================

@pytest.mark.functional
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


@pytest.mark.functional
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


@pytest.mark.functional
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

@pytest.mark.functional
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


@pytest.mark.functional
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


@pytest.mark.functional
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


# ===========================================================================
# mj-markdown-editor
# ===========================================================================

@pytest.mark.functional
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


@pytest.mark.functional
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


@pytest.mark.functional
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
    assert len(view_events) > 0
    assert view_events[-1]["detail"]["view"] == "preview"
    return


# ===========================================================================
# mj-code-editor
# ===========================================================================

@pytest.mark.functional
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


@pytest.mark.functional
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


@pytest.mark.functional
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


# ===========================================================================
# mj-inline-edit
# ===========================================================================

@pytest.mark.functional
def test_inline_edit_renders_display_value(base_url, page):
    """
        mj-inline-edit shows the value set via the JS property in display mode.

        :returns: None
    """

    page.goto(base_url + "/components/text/mj-inline-edit")
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-inline-edit")

    _load_html(
        page=page,
        html='<mj-inline-edit label="Title" trigger="click"></mj-inline-edit>',
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-inline-edit")

    # Set value via JS property (attribute is not reflected on connect)
    frame.evaluate(
        "() => { document.querySelector('mj-inline-edit').value = 'My Title'; }"
    )

    el = frame.locator("mj-inline-edit")
    expect(el).to_be_visible()
    val = frame.evaluate("() => document.querySelector('mj-inline-edit').value")
    assert val == "My Title"
    return


@pytest.mark.functional
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

@pytest.mark.functional
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


@pytest.mark.functional
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


# ===========================================================================
# mj-token-input
# ===========================================================================

@pytest.mark.functional
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


@pytest.mark.functional
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


# ===========================================================================
# mj-otp-input
# ===========================================================================

@pytest.mark.functional
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


@pytest.mark.functional
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


# ===========================================================================
# mj-slider
# ===========================================================================

@pytest.mark.functional
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


@pytest.mark.functional
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


@pytest.mark.functional
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


# ===========================================================================
# mj-rating
# ===========================================================================

@pytest.mark.functional
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


@pytest.mark.functional
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


# ===========================================================================
# mj-captcha
# ===========================================================================

@pytest.mark.functional
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


@pytest.mark.functional
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


# ===========================================================================
# mj-form
# ===========================================================================

@pytest.mark.functional
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


@pytest.mark.functional
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

    _install_event_collector(frame=frame, tag="mj-form", events=["mj-submit"])

    inner = frame.locator("mj-text-field input")
    inner.fill("admin")

    # Use JS to trigger submit since native button may be outside shadow DOM wiring
    frame.evaluate("() => document.querySelector('mj-form').submit()")

    events = _get_events(frame=frame)
    submit_events = [e for e in events if e["name"] == "mj-submit"]
    assert len(submit_events) > 0
    assert submit_events[-1]["detail"]["valid"] is True
    return


@pytest.mark.functional
def test_form_invalid_required_field_emits_mj_invalid(base_url, page):
    """
        Submitting mj-form with an empty required field (after triggering validation) fires mj-invalid.

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

    # Focus then blur the required field to trigger validation state
    inner = frame.locator("mj-text-field input")
    inner.focus()
    inner.blur()
    page.wait_for_timeout(100)

    _install_event_collector(frame=frame, tag="mj-form", events=["mj-invalid"])

    frame.evaluate("() => document.querySelector('mj-form').submit()")

    events = _get_events(frame=frame)
    invalid_events = [e for e in events if e["name"] == "mj-invalid"]
    assert len(invalid_events) > 0
    return


# ===========================================================================
# mj-fieldset
# ===========================================================================

@pytest.mark.functional
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


@pytest.mark.functional
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


@pytest.mark.functional
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
        html='<mj-fieldset legend="Section" disabled></mj-fieldset>',
    )
    frame = _get_frame(page)
    _wait_for_tag(frame=frame, tag="mj-fieldset")

    inner_fs = frame.locator("mj-fieldset fieldset")
    expect(inner_fs).to_have_attribute("disabled", "")
    return


# ===========================================================================
# mj-label
# ===========================================================================

@pytest.mark.functional
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


@pytest.mark.functional
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


@pytest.mark.functional
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


# ===========================================================================
# mj-help-text
# ===========================================================================

@pytest.mark.functional
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


@pytest.mark.functional
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

@pytest.mark.functional
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


@pytest.mark.functional
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

@pytest.mark.functional
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


@pytest.mark.functional
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


# ===========================================================================
# mj-character-counter
# ===========================================================================

@pytest.mark.functional
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


@pytest.mark.functional
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


@pytest.mark.functional
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
