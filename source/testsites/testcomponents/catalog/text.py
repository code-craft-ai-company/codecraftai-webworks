"""
    text.py

    Catalog entries for the 'Text & Form Controls' component group.

    This module exposes a module-level ``COMPONENTS`` list of ComponentDoc
    instances describing and demonstrating all text-entry, editor, form-
    structure, and form-utility components in the library. Every entry has
    an example gallery, typed attribute controls and reference tables
    written against the component source.
"""

import textwrap

from testcomponents.catalog.componentdoc import AttributeDoc
from testcomponents.catalog.componentdoc import ComponentDoc
from testcomponents.catalog.componentdoc import ComponentExample


def _code(text: str) -> str:
    """
        Normalise an indented triple-quoted markup, CSS or script block.

        :param text: The block as written in this module.

        :returns: The block dedented, without the leading and trailing blank lines.
    """

    result = textwrap.dedent(text).strip("\n") + "\n"
    return result


def _attr(name: str, description: str, kind: str = "string",
          values: "list | None" = None, default: "str | None" = None) -> AttributeDoc:
    """
        Build an AttributeDoc, passing every argument by keyword.

        :param name: Attribute name as written in markup.
        :param description: Plain-text description.
        :param kind: Control kind (boolean, enum, string, number, color, json).
        :param values: Enum values or string suggestions.
        :param default: The value the component behaves as when the attribute is absent.

        :returns: The AttributeDoc.
    """

    doc = AttributeDoc(name=name, description=description, kind=kind, values=values, default=default)
    return doc


# Attributes shared by the form-associated controls (FormControlMixin).
def _name_attr() -> AttributeDoc:
    return _attr("name", "Form entry name. The control submits its value under this name.")


def _required_message_attr() -> AttributeDoc:
    return _attr("required-message", "Replaces the built-in text shown for an empty required field. "
                 "Read when validity is next computed (not observed).")


def _size_attr() -> AttributeDoc:
    return _attr("size", "Control size. Absent is the medium size.", kind="enum", values=["sm", "lg"])


def _aria_label_attr() -> AttributeDoc:
    return _attr("aria-label", "Accessible name used when there is no visible `label`.")


# Reference rows shared by the form-associated controls.
_FORM_PROPERTIES = [
    ("form", "HTMLFormElement | null. The form that owns the control (read-only)."),
    ("validity", "ValidityState. The current constraint state (read-only)."),
    ("validationMessage", "string. The message for the current failed constraint (read-only)."),
    ("disabled", "boolean. Reflects the `disabled` attribute."),
]

_FORM_METHODS = [
    ("checkValidity() -> boolean", "Runs the constraints; fires `invalid` (and shows the inline error) when they fail."),
    ("reportValidity() -> boolean", "Like `checkValidity()`, and reveals the inline error."),
    ("focus(options)", "Moves focus to the inner control."),
]

_BRIDGED_EVENTS = [
    ("input", "Native event (no detail) dispatched after each `mj-input`, so plain listeners and frameworks see it."),
    ("change", "Native event (no detail) dispatched after each `mj-change`."),
]

# CSS used by several form examples.
_FORM_CSS = _code("""
    .demo-form { display: grid; gap: var(--mj-space-4); max-inline-size: 30rem; }
    .actions { display: flex; gap: var(--mj-space-2); flex-wrap: wrap; }
    .result { display: block; padding: var(--mj-space-3); border: 1px dashed var(--mj-border);
              border-radius: var(--mj-radius-md); color: var(--mj-text-muted);
              font-family: var(--mj-font-mono); font-size: var(--mj-font-size-sm); white-space: pre-wrap; }
    .field { display: grid; gap: var(--mj-space-1); }
    .native { font: inherit; padding: var(--mj-space-2) var(--mj-space-3); color: var(--mj-text);
              background: var(--mj-surface); border: 1px solid var(--mj-border-strong);
              border-radius: var(--mj-radius-md); }
    .check { display: flex; gap: var(--mj-space-2); align-items: center; }
""")

_STACK_CSS = _code("""
    .stack { display: grid; gap: var(--mj-space-4); max-inline-size: 30rem; }
""")

# Script lines that echo a native form's submit and reset into an <output>.
_NATIVE_FORM_SCRIPT = _code("""
    const form = document.getElementById("demo-form")
    const output = document.getElementById("demo-result")
    form.addEventListener("submit", (event) => {
      event.preventDefault()
      const entries = Array.from(new FormData(form).entries())
      output.textContent = JSON.stringify(entries, null, 1)
      mjSandbox.log("submit", { entries })
    })
    form.addEventListener("reset", () => {
      output.textContent = "Form reset: every control is back to its value attribute."
      mjSandbox.log("reset", {})
    })
""")


COMPONENTS = [
    ComponentDoc(
        tag="mj-text-field",
        title="Text Field",
        group="text",
        summary="The foundational single-line text entry control, with label, help, inline error, counter and clear button.",
        description=_code("""
            <p><code>&lt;mj-text-field&gt;</code> wraps a native <code>&lt;input type="text"&gt;</code> in a
            form-associated element (ElementInternals). It renders a label (with a <code>*</code> when
            required), help text, an inline error, <code>prefix</code>/<code>suffix</code> slots, an optional
            clear button and an <code>n/max</code> counter when <code>maxlength</code> is set.</p>
            <p><code>required</code>, <code>minlength</code> and <code>pattern</code> (matched against the whole
            value) set validity from the first render, so an untouched required field is invalid. The inline
            error appears after the first blur or a failed <code>checkValidity()</code> / submit, then follows
            typing live; a form reset hides it again. <code>error-message</code> only replaces the text of a
            real error, it never makes a valid field invalid.</p>
            <p>The <code>value</code> attribute is the default value: it is shown and submitted at first render,
            re-applied when it changes, and restored by a form reset. Setting the <code>value</code> property
            emits no events.</p>
        """),
        how_to_use=_code("""
            <p>Give the field a <code>name</code> and a <code>label</code>; add <code>placeholder</code> and
            <code>help-text</code> for guidance. Use <code>required</code>, <code>minlength</code>,
            <code>maxlength</code> and <code>pattern</code> for constraints, <code>required-message</code> and
            <code>error-message</code> to word the errors, <code>clearable</code> for a clear button.
            Listen for <code>mj-input</code> on every keystroke and <code>mj-change</code> on commit (blur or
            Enter); plain <code>input</code>/<code>change</code> events are bridged too. Put icons or affixes in
            the <code>prefix</code> and <code>suffix</code> slots.</p>
        """),
        example="",
        examples=[
            ComponentExample(
                key="basic",
                title="Basic usage",
                description="<p>A labelled field with help text, a clear button and a counter. Type to see "
                            "<code>mj-input</code>; blur to see <code>mj-change</code>.</p>",
                html=_code("""
                    <mj-text-field
                      name="full-name"
                      label="Full name"
                      placeholder="Jane Smith"
                      help-text="Enter your first and last name."
                      clearable
                      maxlength="80">
                    </mj-text-field>
                """),
            ),
            ComponentExample(
                key="variants",
                title="Variants and sizes",
                description="<p><code>variant</code> (outlined by default, <code>filled</code>, <code>plain</code>) "
                            "and <code>size</code> (<code>sm</code>, medium, <code>lg</code>). The controls drive "
                            "the first, filled field.</p>",
                html=_code("""
                    <div class="stack">
                      <mj-text-field variant="filled" label="Filled" placeholder="Filled variant"></mj-text-field>
                      <mj-text-field label="Outlined (default)" placeholder="Outlined variant"></mj-text-field>
                      <mj-text-field variant="plain" label="Plain" placeholder="Plain variant"></mj-text-field>
                      <mj-text-field size="sm" label="Small" value="Small field"></mj-text-field>
                      <mj-text-field size="lg" label="Large" value="Large field"></mj-text-field>
                    </div>
                """),
                css=_STACK_CSS,
            ),
            ComponentExample(
                key="states",
                title="Required, invalid, read-only, disabled",
                description="<p>The first field is required with a <code>pattern</code> and a custom "
                            "<code>error-message</code>; the script fills it with a bad value and calls "
                            "<code>reportValidity()</code>, so the error shows. Fix it to <code>ABC-123</code> "
                            "and the error goes away as you type.</p>",
                html=_code("""
                    <div class="stack">
                      <mj-text-field id="project-code" name="code" label="Project code" required
                        pattern="[A-Z]{3}-[0-9]{3}" placeholder="ABC-123"
                        help-text="Three capitals, a dash and three digits."
                        error-message="Use the format ABC-123."></mj-text-field>
                      <mj-text-field label="Workspace" value="Acme Corp" readonly
                        help-text="Read-only: focusable and selectable, not editable."></mj-text-field>
                      <mj-text-field label="Account ID" value="ACC-00042" disabled></mj-text-field>
                    </div>
                """),
                css=_STACK_CSS,
                script=_code("""
                    const field = document.getElementById("project-code")
                    field.value = "abc-12"
                    const valid = field.reportValidity()
                    mjSandbox.log("reportValidity()", { valid, message: field.validationMessage })
                """),
            ),
            ComponentExample(
                key="slots",
                title="Prefix and suffix",
                description="<p>Affix text and an icon in the <code>prefix</code> and <code>suffix</code> "
                            "slots. Toggle them in the Slots panel.</p>",
                html=_code("""
                    <div class="stack">
                      <mj-text-field label="Website" name="site" value="acme">
                        <span slot="prefix">https://</span>
                        <span slot="suffix">.example.com</span>
                      </mj-text-field>
                      <mj-text-field label="Search people" placeholder="Name or email" clearable>
                        <svg slot="prefix" viewBox="0 0 16 16" width="16" height="16" aria-hidden="true">
                          <circle cx="7" cy="7" r="5" fill="none" stroke="currentColor" stroke-width="1.5"/>
                          <path d="M11 11l3.5 3.5" stroke="currentColor" stroke-width="1.5"/>
                        </svg>
                      </mj-text-field>
                    </div>
                """),
                css=_STACK_CSS,
            ),
            ComponentExample(
                key="form",
                title="In a native form",
                description="<p>The fields submit under their <code>name</code>; an invalid field blocks the "
                            "submit. Submit shows the FormData entries, Reset restores the <code>value</code> "
                            "attributes.</p>",
                html=_code("""
                    <form id="demo-form" class="demo-form">
                      <mj-text-field name="username" label="Username" value="ada_l" required
                        minlength="3" maxlength="20" pattern="[a-z0-9_]+"
                        help-text="3-20 lowercase letters, digits or underscores."></mj-text-field>
                      <mj-text-field name="display-name" label="Display name" required
                        required-message="Tell us what to call you."></mj-text-field>
                      <div class="actions">
                        <button type="submit">Create account</button>
                        <button type="reset">Reset</button>
                      </div>
                      <output id="demo-result" class="result">Submit to see the form data.</output>
                    </form>
                """),
                css=_FORM_CSS,
                script=_NATIVE_FORM_SCRIPT,
            ),
            ComponentExample(
                key="events",
                title="Events",
                description="<p>The script types, commits, clears and validates the field; the Events panel "
                            "shows <code>mj-input</code>, <code>mj-change</code>, <code>mj-clear</code> and "
                            "<code>mj-invalid</code> with their details.</p>",
                html=_code("""
                    <mj-text-field id="events-field" label="Tag" clearable required minlength="2"
                      help-text="Watch the Events panel."></mj-text-field>
                """),
                script=_code("""
                    const field = document.getElementById("events-field")
                    const input = field.shadowRoot.querySelector("input")
                    input.focus()
                    for (const text of ["d", "de", "design"]) {
                      input.value = text
                      input.dispatchEvent(new InputEvent("input", { bubbles: true, composed: true }))
                    }
                    input.dispatchEvent(new Event("change", { bubbles: true }))
                    mjSandbox.log("typed and committed", { value: field.value })
                    field.shadowRoot.querySelector("[part='clear-button']").click()
                    mjSandbox.log("cleared", { value: field.value })
                    const valid = field.reportValidity()
                    mjSandbox.log("reportValidity()", { valid, message: field.validationMessage })
                """),
            ),
        ],
        attributes=[
            _attr("label", "Visible label text; a `*` is added when required."),
            _attr("placeholder", "Hint shown inside the empty input.", values=["Jane Smith", "Search"]),
            _attr("value", "Default value: shown and submitted at first render, re-applied when it changes, restored on form reset."),
            _name_attr(),
            _attr("help-text", "Guidance shown below the field."),
            _attr("error-message", "Replaces the text of a real validation error; never makes a valid field invalid."),
            _required_message_attr(),
            _attr("maxlength", "Maximum characters (the input stops accepting more); shows the `n/max` counter.", kind="number"),
            _attr("minlength", "Minimum characters for a non-empty value (tooShort error).", kind="number"),
            _attr("pattern", "Regular expression the whole non-empty value must match.", values=["[A-Za-z ]+", "[0-9]{5}"]),
            _attr("required", "The field must not be empty; an untouched empty field is invalid.", kind="boolean"),
            _attr("disabled", "Disables the field; it is not submitted.", kind="boolean"),
            _attr("readonly", "The value can be selected and is submitted, but not edited.", kind="boolean"),
            _attr("clearable", "Shows a clear button while there is a value (not when readonly or disabled).", kind="boolean"),
            _attr("autocomplete", "Autocomplete hint for the inner input.", values=["on", "off", "name", "email", "username"], default="on"),
            _attr("inputmode", "Virtual keyboard hint.", kind="enum",
                  values=["text", "email", "tel", "url", "numeric", "decimal", "search", "none"], default="text"),
            _attr("spellcheck", "`false` turns spell checking off; any other value turns it on; absent leaves the browser default.",
                  kind="enum", values=["true", "false"]),
            _attr("autofocus", "Focuses the input when the field first connects.", kind="boolean"),
            _attr("variant", "Visual style; absent is outlined.", kind="enum", values=["filled", "plain"]),
            _size_attr(),
            _aria_label_attr(),
        ],
        events=[
            ("mj-input", "Every keystroke.", "{ value: string }"),
            ("mj-change", "The value was committed (blur or Enter) and differs from the last commit.", "{ value: string }"),
            ("mj-clear", "The clear button was pressed; followed by `mj-input` and `mj-change` with an empty value.",
             "{ previousValue: string }"),
            ("mj-invalid", "On blur while invalid and on every failed check (`checkValidity()`, `reportValidity()`, form submit).",
             "{ validationMessage: string }"),
        ] + _BRIDGED_EVENTS,
        slots=[
            ("prefix", "Content before the input: an icon or affix text.",
             '<svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><circle cx="8" cy="8" r="5" fill="currentColor"/></svg>'),
            ("suffix", "Content after the input: a unit, a domain, a small button.", "<span>.example.com</span>"),
        ],
        properties=[
            ("value", "string. The current value; setting it emits no events and resets the change baseline."),
        ] + _FORM_PROPERTIES,
        methods=_FORM_METHODS,
        parts=[
            ("label", "The label element."),
            ("field", "The bordered box around prefix, input, suffix and clear button."),
            ("prefix", "Wrapper of the prefix slot."),
            ("input", "The native input."),
            ("suffix", "Wrapper of the suffix slot."),
            ("clear-button", "The clear button."),
            ("help", "Help text."),
            ("error", "Inline error message."),
            ("counter", "The `n/max` character counter."),
        ],
        css_properties=[],
    ),
    ComponentDoc(
        tag="mj-search-input",
        title="Search Input",
        group="text",
        summary="A search field with icon, clear and submit buttons, debounced queries and an optional suggestion popup.",
        description=_code("""
            <p><code>&lt;mj-search-input&gt;</code> is a pill-shaped field in a <code>role="search"</code> landmark
            around an <code>&lt;input type="search"&gt;</code>. It has a search-icon slot, a clear button that
            appears while there is a value, an optional submit button, a debounced
            <code>mj-query-change</code> event and a suggestion listbox.</p>
            <p>The component does no filtering: listen for <code>mj-query-change</code> and assign the
            <code>suggestions</code> property (strings, numbers or <code>{ value, label?, description? }</code>).
            While suggestions are used the input becomes an ARIA combobox. Enter, the submit button and picking a
            suggestion fire a cancelable <code>mj-search</code>; unless it is cancelled, the owning form is
            submitted with <code>requestSubmit()</code>. Without a <code>name</code> the value is submitted as
            <code>q</code>.</p>
            <p><code>required</code> and <code>maxlength</code> (for a value set by script; typing stops at the
            limit) are validated like in the other text controls: once focus leaves the component, or a check or
            submit fails, an inline error appears (text from <code>error-message</code> when set) and
            <code>mj-invalid</code> fires. There is no <code>mj-change</code> event.</p>
        """),
        how_to_use=_code("""
            <p>Set <code>label</code> (the accessible name of the landmark and input) and
            <code>placeholder</code>. Tune <code>debounce</code> and <code>min-chars</code>, fetch results on
            <code>mj-query-change</code>, set <code>loading</code> while waiting and assign
            <code>suggestions</code>. Handle <code>mj-search</code> (call <code>preventDefault()</code> to stop the
            form submit) and <code>mj-suggestion-select</code>. Arrow keys move through suggestions, Enter picks,
            Escape closes the popup.</p>
        """),
        example="",
        examples=[
            ComponentExample(
                key="basic",
                title="Basic usage",
                description="<p>Type and press Enter: <code>mj-input</code>, the debounced "
                            "<code>mj-query-change</code> and <code>mj-search</code> appear in Events.</p>",
                html=_code("""
                    <mj-search-input
                      label="Component search"
                      placeholder="Search components&hellip;"
                      debounce="300"
                      min-chars="2">
                    </mj-search-input>
                """),
            ),
            ComponentExample(
                key="suggestions",
                title="Suggestions",
                description="<p>The script answers <code>mj-query-change</code> after a short simulated fetch "
                            "(with <code>loading</code>) and assigns <code>suggestions</code>. It opens the popup "
                            "for the query <code>ta</code>; use the arrow keys and Enter to pick one.</p>",
                html=_code("""
                    <mj-search-input id="component-search" label="Component search"
                      placeholder="Try date, tab or text" debounce="200" show-submit-button>
                    </mj-search-input>
                """),
                script=_code("""
                    const search = document.getElementById("component-search")
                    const catalog = [
                      { value: "mj-date-picker", label: "Date Picker", description: "Calendar popup for one date" },
                      { value: "mj-tabs", label: "Tabs", description: "Switch between panels" },
                      { value: "mj-table", label: "Table", description: "Static tabular data" },
                      { value: "mj-text-field", label: "Text Field", description: "Single-line text entry" },
                      { value: "mj-textarea", label: "Textarea", description: "Multi-line text entry" },
                      { value: "mj-toast", label: "Toast", description: "Transient notification" },
                    ]
                    const lookup = (query) => catalog.filter((item) =>
                      item.label.toLowerCase().includes(query.toLowerCase()))
                    search.addEventListener("mj-query-change", (event) => {
                      const query = event.detail.value
                      if (query === "") {
                        search.suggestions = []
                        return
                      }
                      search.loading = true
                      setTimeout(() => {
                        search.loading = false
                        search.suggestions = lookup(query)
                      }, 250)
                    })
                    search.addEventListener("mj-suggestion-select", (event) => {
                      mjSandbox.log("picked", { value: event.detail.suggestion.value })
                    })
                    search.focus()
                    search.value = "ta"
                    search.suggestions = lookup("ta")
                """),
                height=420,
            ),
            ComponentExample(
                key="states",
                title="States",
                description="<p>Pre-filled, read-only, disabled, without a clear button, with help text, and "
                            "<code>loading</code> (which opens the popup with a loading message).</p>",
                html=_code("""
                    <div class="stack">
                      <mj-search-input label="Orders" value="INV-2041" help-text="Search by order or invoice number."></mj-search-input>
                      <mj-search-input label="Read-only search" value="status:open" readonly></mj-search-input>
                      <mj-search-input label="Disabled search" placeholder="Search is unavailable" disabled></mj-search-input>
                      <mj-search-input label="No clear button" value="kept" no-clear-button></mj-search-input>
                      <mj-search-input label="Loading" value="report" loading></mj-search-input>
                    </div>
                """),
                css=_STACK_CSS,
                height=520,
            ),
            ComponentExample(
                key="slots",
                title="Custom icons",
                description="<p>The <code>search-icon</code> and <code>submit-icon</code> slots replace the "
                            "magnifier and the arrow; <code>show-submit-button</code> shows the submit button.</p>",
                html=_code("""
                    <mj-search-input label="Find a file" placeholder="Find a file" show-submit-button submit-label="Find">
                      <svg slot="search-icon" viewBox="0 0 16 16" width="16" height="16" aria-hidden="true">
                        <path d="M3 2h6l4 4v8H3z" fill="none" stroke="currentColor" stroke-width="1.5"/>
                      </svg>
                      <span slot="submit-icon" aria-hidden="true">Go</span>
                    </mj-search-input>
                """),
            ),
            ComponentExample(
                key="form",
                title="In a form",
                description="<p>Enter or the submit button submits the form; without a <code>name</code> the "
                            "value is sent as <code>q</code>. The field is <code>required</code>: pressing Enter "
                            "while it is empty shows the inline error and <code>mj-invalid</code>. Tick the box "
                            "to cancel <code>mj-search</code> and keep the form from submitting.</p>",
                html=_code("""
                    <form id="demo-form" class="demo-form">
                      <mj-search-input label="Search the docs" placeholder="e.g. validation" show-submit-button required></mj-search-input>
                      <label><input type="checkbox" id="cancel-search"> Cancel <code>mj-search</code></label>
                      <output id="demo-result" class="result">Press Enter to submit.</output>
                    </form>
                """),
                css=_FORM_CSS,
                script=_code("""
                    const form = document.getElementById("demo-form")
                    const output = document.getElementById("demo-result")
                    const search = form.querySelector("mj-search-input")
                    search.addEventListener("mj-search", (event) => {
                      if (document.getElementById("cancel-search").checked) {
                        event.preventDefault()
                        output.textContent = "mj-search was cancelled; the form was not submitted."
                      }
                    })
                    form.addEventListener("submit", (event) => {
                      event.preventDefault()
                      const query = new URLSearchParams(new FormData(form)).toString()
                      output.textContent = "Submitted: ?" + query
                      mjSandbox.log("submit", { query })
                    })
                """),
            ),
        ],
        attributes=[
            _attr("label", "Accessible name of the search landmark and the input.", default="Search"),
            _attr("placeholder", "Hint text; absent shows the localized 'Search', an empty value shows none.",
                  values=["Search components...", "Search"]),
            _attr("value", "Default value: shown and submitted at first render, re-applied when it changes, restored on form reset."),
            _attr("name", "Form entry name.", default="q"),
            _attr("help-text", "Guidance shown below the field."),
            _attr("required", "The field must not be empty.", kind="boolean"),
            _attr("maxlength", "Maximum characters: typing stops there, a longer value set by script is invalid.", kind="number"),
            _attr("error-message", "Replaces the text of a real validation error."),
            _required_message_attr(),
            _attr("disabled", "Disables the field.", kind="boolean"),
            _attr("readonly", "The value cannot be edited.", kind="boolean"),
            _attr("show-submit-button", "Shows a submit button after the input.", kind="boolean"),
            _attr("submit-label", "Accessible label of the submit button.", default="Search"),
            _attr("no-clear-button", "Never shows the clear button.", kind="boolean"),
            _attr("loading", "Opens the popup with a loading message and marks it busy.", kind="boolean"),
            _attr("debounce", "Milliseconds to wait after typing before `mj-query-change`.", kind="number", default="300"),
            _attr("min-chars", "Minimum query length for `mj-query-change`; shorter queries close the popup.", kind="number", default="1"),
            _attr("autocomplete", "Autocomplete hint for the inner input.", values=["off", "on"], default="off"),
            _aria_label_attr(),
        ],
        events=[
            ("mj-input", "Every keystroke, and with an empty value on clear.", "{ value: string }"),
            ("mj-query-change", "Debounced query at or above `min-chars`; once with an empty value when the query is cleared or gets too short.",
             "{ value: string }"),
            ("mj-search", "Cancelable. Enter (no active suggestion), the submit button, or a picked suggestion. Not cancelled: the form is submitted.",
             "{ value: string }"),
            ("mj-suggestion-select", "A suggestion was picked (before `mj-search`).", "{ suggestion: string | number | object }"),
            ("mj-clear", "The clear button was pressed.", "{ previousValue: string }"),
            ("mj-invalid", "Focus left an invalid field, or a check / submit failed.", "{ validationMessage: string }"),
            ("input", "Native event (no detail) after each `mj-input`."),
        ],
        slots=[
            ("search-icon", "Replaces the magnifier icon.",
             '<svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><path d="M3 2h6l4 4v8H3z" fill="none" stroke="currentColor" stroke-width="1.5"/></svg>'),
            ("submit-icon", "Content of the submit button (shown with `show-submit-button`).", '<span aria-hidden="true">Go</span>'),
        ],
        properties=[
            ("value", "string. The current query; setting it emits no events."),
            ("suggestions", "Array of string | number | { value, label?, description? }. Setting a non-empty array opens the popup; `[]` closes it."),
            ("loading", "boolean. Reflects the `loading` attribute."),
        ] + _FORM_PROPERTIES,
        methods=[
            ("checkValidity() -> boolean", "Runs the `required` and `maxlength` constraints; fires `invalid` (and shows the inline error) when they fail."),
            ("reportValidity() -> boolean", "Like `checkValidity()`, and reveals the inline error."),
            ("focus(options)", "Focuses the input."),
        ],
        parts=[
            ("search", "The `role=search` landmark."),
            ("field", "The pill-shaped box."),
            ("search-icon", "Wrapper of the search icon."),
            ("input", "The native search input."),
            ("clear-button", "The clear button."),
            ("submit-button", "The submit button."),
            ("popup", "The suggestion listbox."),
            ("option", "One suggestion row."),
            ("loading", "The loading message in the popup."),
            ("help", "Help text."),
            ("error", "Inline error message."),
        ],
        css_properties=[],
    ),
    ComponentDoc(
        tag="mj-password-field",
        title="Password Field",
        group="text",
        summary="Password entry with a show/hide toggle, caps-lock hint and strength meter.",
        description=_code("""
            <p><code>&lt;mj-password-field&gt;</code> wraps a native password input with a visibility toggle
            (labelled 'Show password', its state reported with <code>aria-pressed</code>), an optional Caps Lock
            hint and an optional strength meter. Escape hides a visible password.</p>
            <p>The strength score runs from 0 (empty) to 4: one point for any input, one for 8+ characters, one
            for mixed case and one for a digit plus a symbol. It is tracked only while
            <code>show-strength</code> is set and reported by <code>mj-strength-change</code>.</p>
            <p><code>required</code>, <code>minlength</code> and <code>maxlength</code> are validated; the inline
            error shows after blur or a failed check. The field is form-associated; the <code>value</code>
            attribute is the default value and a reset hides the password again.</p>
        """),
        how_to_use=_code("""
            <p>Use <code>new-password</code> on sign-up and change-password forms (the autocomplete hint becomes
            <code>new-password</code>), otherwise the hint is <code>current-password</code>. Add
            <code>show-strength</code> for the meter and <code>show-caps-hint</code> for the Caps Lock warning;
            set <code>minlength</code> for the policy. Listen for <code>mj-strength-change</code> to show your own
            feedback and <code>mj-visibility-change</code> to track the toggle.</p>
        """),
        example="",
        examples=[
            ComponentExample(
                key="basic",
                title="Basic usage",
                description="<p>A new password with the strength meter, Caps Lock hint and an 8-character "
                            "minimum. Toggle the eye button; press Escape to hide again.</p>",
                html=_code("""
                    <mj-password-field
                      name="password"
                      label="Password"
                      placeholder="Enter a strong password"
                      help-text="At least 8 characters; mix cases, digits and symbols."
                      new-password
                      show-strength
                      show-caps-hint
                      minlength="8"
                      required>
                    </mj-password-field>
                """),
            ),
            ComponentExample(
                key="states",
                title="States and sizes",
                description="<p>Visible, read-only, disabled (both hide the toggle), small and large, and an "
                            "invalid field revealed by <code>reportValidity()</code> with a custom "
                            "<code>error-message</code>.</p>",
                html=_code("""
                    <div class="stack">
                      <mj-password-field id="short-password" label="Too short" value="abc" minlength="8"
                        error-message="Use 8 or more characters."></mj-password-field>
                      <mj-password-field label="Visible" value="correct horse" visible></mj-password-field>
                      <mj-password-field label="Read-only" value="s3cret!" readonly></mj-password-field>
                      <mj-password-field label="Disabled" value="s3cret!" disabled></mj-password-field>
                      <mj-password-field label="Small" size="sm"></mj-password-field>
                      <mj-password-field label="Large" size="lg"></mj-password-field>
                    </div>
                """),
                css=_STACK_CSS,
                script=_code("""
                    const field = document.getElementById("short-password")
                    mjSandbox.log("reportValidity()", { valid: field.reportValidity(), message: field.validationMessage })
                """),
            ),
            ComponentExample(
                key="slots",
                title="Prefix icon",
                description="<p>A lock icon in the <code>prefix</code> slot (the field has no suffix slot; "
                            "the toggle sits at the end).</p>",
                html=_code("""
                    <mj-password-field label="Current password" current-password>
                      <svg slot="prefix" viewBox="0 0 16 16" width="16" height="16" aria-hidden="true">
                        <rect x="3" y="7" width="10" height="7" rx="1" fill="none" stroke="currentColor" stroke-width="1.5"/>
                        <path d="M5 7V5a3 3 0 0 1 6 0v2" fill="none" stroke="currentColor" stroke-width="1.5"/>
                      </svg>
                    </mj-password-field>
                """),
            ),
            ComponentExample(
                key="form",
                title="Sign-in form",
                description="<p>A sign-in form: both fields are required and the password needs 8 characters. "
                            "Submit shows what would be sent (the password masked), Reset clears it and hides "
                            "a visible password.</p>",
                html=_code("""
                    <form id="demo-form" class="demo-form">
                      <mj-text-field name="email" label="Email" value="ada@example.com" required></mj-text-field>
                      <mj-password-field name="password" label="Password" current-password required minlength="8"></mj-password-field>
                      <div class="actions">
                        <button type="submit">Sign in</button>
                        <button type="reset">Reset</button>
                      </div>
                      <output id="demo-result" class="result">Submit to see the form data.</output>
                    </form>
                """),
                css=_FORM_CSS,
                script=_code("""
                    const form = document.getElementById("demo-form")
                    const output = document.getElementById("demo-result")
                    form.addEventListener("submit", (event) => {
                      event.preventDefault()
                      const data = new FormData(form)
                      const shown = { email: data.get("email"), password: "*".repeat(String(data.get("password")).length) }
                      output.textContent = JSON.stringify(shown)
                      mjSandbox.log("submit", shown)
                    })
                    form.addEventListener("reset", () => { output.textContent = "Form reset." })
                """),
            ),
            ComponentExample(
                key="events",
                title="Strength and visibility events",
                description="<p>The script sets ever stronger passwords (setting <code>value</code> updates the "
                            "meter and fires <code>mj-strength-change</code>), clicks the toggle and presses "
                            "Escape to hide it again.</p>",
                html=_code("""
                    <mj-password-field id="events-password" label="New password" new-password show-strength></mj-password-field>
                """),
                script=_code("""
                    const field = document.getElementById("events-password")
                    for (const candidate of ["a", "abcdefgh", "Abcdefgh", "Abcdefg1!"]) {
                      field.value = candidate
                      mjSandbox.log("value set", { length: candidate.length, strength: field.strength, label: field.strengthLabel })
                    }
                    field.shadowRoot.querySelector("[part='toggle-button']").click()
                    const input = field.shadowRoot.querySelector("input")
                    input.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true, composed: true }))
                    mjSandbox.log("after Escape", { visible: field.visible })
                """),
            ),
        ],
        attributes=[
            _attr("label", "Visible label text; a `*` is added when required."),
            _attr("placeholder", "Hint shown inside the empty input."),
            _attr("value", "Default value: shown and submitted at first render, re-applied when it changes, restored on form reset."),
            _name_attr(),
            _attr("help-text", "Guidance shown below the field."),
            _attr("error-message", "Replaces the text of a real validation error."),
            _required_message_attr(),
            _attr("required", "The field must not be empty.", kind="boolean"),
            _attr("minlength", "Minimum length of a non-empty password (validated).", kind="number"),
            _attr("maxlength", "Maximum length (the input stops accepting more; validated).", kind="number"),
            _attr("disabled", "Disables the field and hides the toggle.", kind="boolean"),
            _attr("readonly", "The value cannot be edited; hides the toggle.", kind="boolean"),
            _attr("visible", "Shows the password as plain text.", kind="boolean"),
            _attr("show-strength", "Shows the strength meter and tracks the score.", kind="boolean"),
            _attr("show-caps-hint", "Shows a warning while Caps Lock is on.", kind="boolean"),
            _attr("new-password", "Autocomplete hint `new-password` (unless `current-password` is also set).", kind="boolean"),
            _attr("current-password", "Autocomplete hint `current-password` (the default hint).", kind="boolean"),
            _size_attr(),
            _aria_label_attr(),
        ],
        events=[
            ("mj-input", "Every keystroke.", "{ value: string }"),
            ("mj-change", "The value was committed and differs from the last commit.", "{ value: string }"),
            ("mj-visibility-change", "The toggle was clicked or Escape hid the password.", "{ visible: boolean }"),
            ("mj-strength-change", "The score changed (only with `show-strength`); also on a `value` set and on form reset.",
             "{ score: 0 | 1 | 2 | 3 | 4, label: string }"),
            ("mj-invalid", "On blur while invalid and on every failed check.", "{ validationMessage: string }"),
        ] + _BRIDGED_EVENTS,
        slots=[
            ("prefix", "Content before the input, typically a lock icon.",
             '<svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><rect x="3" y="7" width="10" height="7" rx="1" fill="currentColor"/></svg>'),
        ],
        properties=[
            ("value", "string. The current password; setting it can fire `mj-strength-change`."),
            ("visible", "boolean. Reflects the `visible` attribute; setting it emits nothing."),
            ("strength", "number 0-4. The current score (read-only)."),
            ("strengthLabel", "string. The localized label of the score (read-only)."),
        ] + _FORM_PROPERTIES,
        methods=_FORM_METHODS,
        parts=[
            ("label", "The label element."),
            ("field", "The bordered box."),
            ("prefix", "Wrapper of the prefix slot."),
            ("input", "The native input."),
            ("toggle-button", "The show/hide button."),
            ("caps-lock-hint", "The Caps Lock warning."),
            ("strength-meter", "The meter track."),
            ("strength-fill", "The filled part of the meter (`role=meter`)."),
            ("strength-label", "The score label."),
            ("help", "Help text."),
            ("error", "Inline error message."),
        ],
        css_properties=[
            ("--mj-pwd-strength-height", "Meter height (default 4px)."),
            ("--mj-pwd-strength-color-1", "Score 1 colour (default var(--mj-color-danger))."),
            ("--mj-pwd-strength-color-2", "Score 2 colour (default var(--mj-color-warning))."),
            ("--mj-pwd-strength-color-3", "Score 3 colour (default a warning/success mix)."),
            ("--mj-pwd-strength-color-4", "Score 4 colour (default var(--mj-color-success))."),
        ],
    ),
    ComponentDoc(
        tag="mj-typed-field",
        title="Typed Field",
        group="text",
        summary="A text field for email, URL or telephone values with type-specific validation and a format hint.",
        description=_code("""
            <p><code>&lt;mj-typed-field&gt;</code> is a single-line field for <code>type="email"</code> (the
            default), <code>url</code> or <code>tel</code>. It sets the matching native type,
            <code>inputmode</code> and autocomplete hint, can show a format hint while focused, and validates the
            format itself: email with the HTML-standard rule (each address with <code>multiple</code>), URL by
            parsing it (a missing scheme gets its own message), telephone with a permissive phone rule of at least
            three digits. <code>pattern</code> replaces the telephone rule and adds a check for the other
            types.</p>
            <p>Changing <code>type</code> while the field has a value clears it and fires <code>mj-change</code>.
            The inline error shows after blur or a failed check; <code>mj-invalid</code> carries the
            <code>validityState</code>.</p>
        """),
        how_to_use=_code("""
            <p>Pick <code>type</code>, set <code>label</code> and <code>name</code>, and add
            <code>show-format-hint</code> (optionally with your own <code>format-hint</code>). Use
            <code>multiple</code> for a comma-separated list of emails. Combine with <code>required</code>,
            <code>minlength</code>, <code>maxlength</code> and <code>pattern</code>.</p>
        """),
        example="",
        examples=[
            ComponentExample(
                key="basic",
                title="Basic usage",
                description="<p>An email field with a format hint shown while it has focus. Type an invalid "
                            "address and blur to see the error.</p>",
                html=_code("""
                    <mj-typed-field
                      type="email"
                      name="email"
                      label="Work email"
                      placeholder="you@company.com"
                      show-format-hint
                      required>
                    </mj-typed-field>
                """),
            ),
            ComponentExample(
                key="types",
                title="Email, URL, telephone, multiple",
                description="<p>The three types with values, a custom <code>format-hint</code>, and "
                            "<code>multiple</code> emails.</p>",
                html=_code("""
                    <div class="stack">
                      <mj-typed-field type="url" label="Homepage" value="https://example.com" show-format-hint></mj-typed-field>
                      <mj-typed-field type="email" label="Contact" value="team@example.com"></mj-typed-field>
                      <mj-typed-field type="tel" label="Phone" value="+44 20 7946 0958" show-format-hint
                        format-hint="+44 20 0000 0000"></mj-typed-field>
                      <mj-typed-field type="email" label="CC (comma-separated)" multiple
                        value="ana@example.com, li@example.com"></mj-typed-field>
                    </div>
                """),
                css=_STACK_CSS,
            ),
            ComponentExample(
                key="states",
                title="Invalid, read-only, disabled",
                description="<p>The script calls <code>reportValidity()</code> on a URL without a scheme and a "
                            "phone number with letters, so their errors show; then a read-only and a disabled "
                            "field.</p>",
                html=_code("""
                    <div class="stack">
                      <mj-typed-field id="bad-url" type="url" label="Website" value="example.com"></mj-typed-field>
                      <mj-typed-field id="bad-tel" type="tel" label="Mobile" value="call me"></mj-typed-field>
                      <mj-typed-field type="email" label="Login (read-only)" value="ada@example.com" readonly></mj-typed-field>
                      <mj-typed-field type="url" label="Disabled" value="https://intranet.example" disabled></mj-typed-field>
                    </div>
                """),
                css=_STACK_CSS,
                script=_code("""
                    for (const id of ["bad-url", "bad-tel"]) {
                      const field = document.getElementById(id)
                      mjSandbox.log(id, { valid: field.reportValidity(), message: field.validationMessage })
                    }
                """),
            ),
            ComponentExample(
                key="slots",
                title="Prefix and suffix",
                description="<p>An icon in <code>prefix</code> and a small action in <code>suffix</code>.</p>",
                html=_code("""
                    <mj-typed-field type="url" label="Repository" value="https://git.example.com/acme/app">
                      <svg slot="prefix" viewBox="0 0 16 16" width="16" height="16" aria-hidden="true">
                        <circle cx="8" cy="8" r="6" fill="none" stroke="currentColor" stroke-width="1.5"/>
                        <path d="M2 8h12M8 2c2 2 2 10 0 12M8 2c-2 2-2 10 0 12" fill="none" stroke="currentColor"/>
                      </svg>
                      <button slot="suffix" type="button">Copy</button>
                    </mj-typed-field>
                """),
            ),
            ComponentExample(
                key="form",
                title="Contact form",
                description="<p>Email, URL and telephone in a native form. Invalid formats block the submit; "
                            "Submit shows the entries, Reset restores the defaults.</p>",
                html=_code("""
                    <form id="demo-form" class="demo-form">
                      <mj-typed-field type="email" name="email" label="Email" required></mj-typed-field>
                      <mj-typed-field type="url" name="website" label="Website" value="https://"></mj-typed-field>
                      <mj-typed-field type="tel" name="phone" label="Phone" pattern="\\+?[0-9 ]{7,15}"
                        help-text="Digits and spaces, optional leading +."></mj-typed-field>
                      <div class="actions">
                        <button type="submit">Send</button>
                        <button type="reset">Reset</button>
                      </div>
                      <output id="demo-result" class="result">Submit to see the form data.</output>
                    </form>
                """),
                css=_FORM_CSS,
                script=_NATIVE_FORM_SCRIPT,
            ),
            ComponentExample(
                key="events",
                title="Events",
                description="<p>The script reports an invalid email (<code>mj-invalid</code> with "
                            "<code>validityState</code>), then switches <code>type</code> to <code>tel</code>, "
                            "which clears the value and fires <code>mj-change</code>.</p>",
                html=_code("""
                    <mj-typed-field id="events-typed" type="email" label="Contact" value="not-an-email"></mj-typed-field>
                """),
                script=_code("""
                    const field = document.getElementById("events-typed")
                    field.reportValidity()
                    field.setAttribute("type", "tel")
                    mjSandbox.log("type is now tel", { value: field.value })
                """),
            ),
        ],
        attributes=[
            _attr("type", "Value type; anything else is treated as email. Changing it clears a non-empty value.",
                  kind="enum", values=["email", "url", "tel"], default="email"),
            _attr("label", "Visible label text; a `*` is added when required."),
            _attr("placeholder", "Hint shown inside the empty input."),
            _attr("value", "Default value: shown and submitted at first render, re-applied when it changes, restored on form reset."),
            _name_attr(),
            _attr("help-text", "Guidance shown below the field."),
            _attr("error-message", "Replaces the text of a real validation error."),
            _required_message_attr(),
            _attr("required", "The field must not be empty.", kind="boolean"),
            _attr("disabled", "Disables the field.", kind="boolean"),
            _attr("readonly", "The value cannot be edited.", kind="boolean"),
            _attr("multiple", "Email only: accepts comma-separated addresses and validates each.", kind="boolean"),
            _attr("minlength", "Minimum length of a non-empty value.", kind="number"),
            _attr("maxlength", "Maximum length (validated).", kind="number"),
            _attr("pattern", "Regular expression the whole value must match; for tel it replaces the built-in phone rule.",
                  values=["\\+?[0-9 ]{7,15}", "https://.*"]),
            _attr("autocomplete", "Overrides the type's default hint (email, url, tel).", values=["email", "url", "tel", "off"]),
            _attr("show-format-hint", "Shows the format hint while the input has focus.", kind="boolean"),
            _attr("format-hint", "Hint text; defaults to an example of the type (user@example.com, https://example.com, a phone number).",
                  values=["name@company.com", "https://", "+1 (555) 000-0000"]),
            _size_attr(),
            _aria_label_attr(),
        ],
        events=[
            ("mj-input", "Every keystroke.", "{ value: string }"),
            ("mj-change", "The value was committed and changed; also when a `type` change clears the value.", "{ value: string }"),
            ("mj-invalid", "On blur while invalid and on every failed check.",
             "{ validationMessage: string, validityState: ValidityState }"),
        ] + _BRIDGED_EVENTS,
        slots=[
            ("prefix", "Content before the input.",
             '<svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><circle cx="8" cy="8" r="5" fill="currentColor"/></svg>'),
            ("suffix", "Content after the input.", '<button type="button">Copy</button>'),
        ],
        properties=[
            ("value", "string. The current value; setting it emits no events."),
        ] + _FORM_PROPERTIES,
        methods=_FORM_METHODS,
        parts=[
            ("label", "The label element."),
            ("field", "The bordered box."),
            ("prefix", "Wrapper of the prefix slot."),
            ("input", "The native input."),
            ("suffix", "Wrapper of the suffix slot."),
            ("format-hint", "The format hint."),
            ("help", "Help text."),
            ("error", "Inline error message."),
        ],
        css_properties=[],
    ),
    ComponentDoc(
        tag="mj-number-field",
        title="Number Field",
        group="text",
        summary="Locale-aware numeric input with spinner buttons, keyboard stepping, currency and percent formats.",
        description=_code("""
            <p><code>&lt;mj-number-field&gt;</code> is a text input with <code>role="spinbutton"</code>. While
            focused it shows the plain number in the locale; on blur it shows the formatted text
            (<code>format="number"</code>, <code>currency</code> or <code>percent</code>, where 50 shows as 50%).
            Typed text is parsed with the locale's group and decimal marks; text that cannot be parsed stays on
            screen and makes the field invalid (badInput).</p>
            <p><code>value</code> is a plain decimal string such as <code>1234.5</code> (not a formatted one).
            User input is clamped to <code>min</code>/<code>max</code> on commit, stepping and Home/End;
            values set by script are validated instead (range underflow/overflow). Step mismatch is not
            validated. The spinner buttons are not tab stops: use ArrowUp/Down, PageUp/Down (10 steps) and
            Home/End.</p>
        """),
        how_to_use=_code("""
            <p>Set <code>min</code>, <code>max</code> and <code>step</code>, and <code>format</code> with
            <code>currency-code</code>, <code>fraction-digits</code> and <code>locale</code> as needed. Read
            <code>valueAsNumber</code> for the number and <code>formattedValue</code> for the display text.
            Listen for <code>mj-change</code> (commit, each step, Home/End) and <code>mj-increment</code> /
            <code>mj-decrement</code> for spinner clicks. Enter commits the typed text.</p>
        """),
        example="",
        examples=[
            ComponentExample(
                key="basic",
                title="Basic usage",
                description="<p>A quantity from 1 to 999. Use the spinners or ArrowUp/ArrowDown; type a value "
                            "and press Enter to commit it.</p>",
                html=_code("""
                    <mj-number-field
                      name="quantity"
                      label="Quantity"
                      value="10"
                      min="1"
                      max="999"
                      step="1"
                      help-text="Between 1 and 999.">
                    </mj-number-field>
                """),
            ),
            ComponentExample(
                key="formats",
                title="Currency, percent and locales",
                description="<p>Currency in euros with a German locale, a percentage, two fraction digits, a "
                            "field without spinners and one with <code>spinner-position=\"stacked\"</code>. Focus a "
                            "field to see the unformatted number.</p>",
                html=_code("""
                    <div class="stack">
                      <mj-number-field label="Price" format="currency" currency-code="EUR" locale="de-DE"
                        value="1234.5" step="0.5" fraction-digits="2"></mj-number-field>
                      <mj-number-field label="Discount" format="percent" value="15" min="0" max="100" step="5"></mj-number-field>
                      <mj-number-field label="Weight (kg)" value="72.25" step="0.25" fraction-digits="2"></mj-number-field>
                      <mj-number-field label="Year" value="2026" no-spinner min="1900" max="2100"></mj-number-field>
                      <mj-number-field label="Servings" value="4" min="1" max="12" spinner-position="stacked"></mj-number-field>
                    </div>
                """),
                css=_STACK_CSS,
            ),
            ComponentExample(
                key="states",
                title="States",
                description="<p>A required empty field and an out-of-range value revealed by "
                            "<code>reportValidity()</code>; read-only and disabled fields ignore keys and "
                            "spinners.</p>",
                html=_code("""
                    <div class="stack">
                      <mj-number-field id="seats" label="Seats" required min="1" max="8"></mj-number-field>
                      <mj-number-field id="age" label="Age" min="18" max="120"></mj-number-field>
                      <mj-number-field label="Read-only" value="42" readonly></mj-number-field>
                      <mj-number-field label="Disabled" value="7" disabled size="sm"></mj-number-field>
                    </div>
                """),
                css=_STACK_CSS,
                script=_code("""
                    const age = document.getElementById("age")
                    age.value = "12"
                    for (const field of [document.getElementById("seats"), age]) {
                      mjSandbox.log(field.id, { valid: field.reportValidity(), message: field.validationMessage })
                    }
                """),
            ),
            ComponentExample(
                key="slots",
                title="Prefix and suffix",
                description="<p>A unit in <code>suffix</code> and a symbol in <code>prefix</code>.</p>",
                html=_code("""
                    <div class="stack">
                      <mj-number-field label="Budget" value="2500" step="100" min="0">
                        <span slot="prefix">$</span>
                      </mj-number-field>
                      <mj-number-field label="Distance" value="12" min="0">
                        <span slot="suffix">km</span>
                      </mj-number-field>
                    </div>
                """),
                css=_STACK_CSS,
            ),
            ComponentExample(
                key="form",
                title="Order form",
                description="<p>Two number fields in a native form; values are submitted as plain numbers. "
                            "Submit shows the entries, Reset restores the defaults.</p>",
                html=_code("""
                    <form id="demo-form" class="demo-form">
                      <mj-number-field name="quantity" label="Quantity" value="2" min="1" max="20" required></mj-number-field>
                      <mj-number-field name="tip" label="Tip" format="percent" value="10" min="0" max="30" step="5"></mj-number-field>
                      <div class="actions">
                        <button type="submit">Order</button>
                        <button type="reset">Reset</button>
                      </div>
                      <output id="demo-result" class="result">Submit to see the form data.</output>
                    </form>
                """),
                css=_FORM_CSS,
                script=_NATIVE_FORM_SCRIPT,
            ),
            ComponentExample(
                key="events",
                title="Stepping events",
                description="<p>The script clicks the increment button twice, presses ArrowDown and Home "
                            "(<code>mj-increment</code>, <code>mj-decrement</code>, <code>mj-input</code>, "
                            "<code>mj-change</code>) and logs <code>valueAsNumber</code> and "
                            "<code>formattedValue</code>.</p>",
                html=_code("""
                    <mj-number-field id="events-number" label="Guests" value="4" min="1" max="12"></mj-number-field>
                """),
                script=_code("""
                    const field = document.getElementById("events-number")
                    const increment = field.shadowRoot.querySelector("[part='increment-button']")
                    increment.click()
                    increment.click()
                    const input = field.shadowRoot.querySelector("input")
                    input.focus()
                    for (const key of ["ArrowDown", "Home"]) {
                      input.dispatchEvent(new KeyboardEvent("keydown", { key, bubbles: true, composed: true }))
                    }
                    input.blur()
                    mjSandbox.log("now", { valueAsNumber: field.valueAsNumber, formattedValue: field.formattedValue })
                """),
            ),
        ],
        attributes=[
            _attr("label", "Visible label text; a `*` is added when required."),
            _attr("placeholder", "Hint shown inside the empty input."),
            _attr("value", "Default value as a plain decimal string (`1234.5`), not locale-formatted.", kind="number"),
            _name_attr(),
            _attr("help-text", "Guidance shown below the field."),
            _attr("error-message", "Replaces the text of a real validation error."),
            _required_message_attr(),
            _attr("min", "Lower bound: clamps user input, validates script values.", kind="number"),
            _attr("max", "Upper bound: clamps user input, validates script values.", kind="number"),
            _attr("step", "Step size for spinners and arrow keys (steps from `min`).", kind="number", default="1"),
            _attr("format", "Display format.", kind="enum", values=["number", "currency", "percent"], default="number"),
            _attr("currency-code", "ISO 4217 code for `format=currency`.", values=["USD", "EUR", "GBP", "JPY"], default="USD"),
            _attr("fraction-digits", "Fixed number of fraction digits (0-20).", kind="number"),
            _attr("locale", "BCP 47 locale for parsing and display; falls back to `<html lang>`, the browser, then en-US.",
                  values=["en-US", "de-DE", "fr-FR", "ja-JP"]),
            _attr("required", "The field must not be empty.", kind="boolean"),
            _attr("disabled", "Disables the field; keys and spinners do nothing.", kind="boolean"),
            _attr("readonly", "The value cannot be changed by typing, keys or spinners.", kind="boolean"),
            _attr("no-spinner", "Hides the spinner buttons.", kind="boolean"),
            _attr("spinner-position", "`side`: both buttons in a column beside the input; `stacked`: increment above "
                  "the input, decrement below it, both full width.", kind="enum", values=["side", "stacked"], default="side"),
            _size_attr(),
            _aria_label_attr(),
        ],
        events=[
            ("mj-input", "While typing (with the raw typed text) and after each change from a step or commit.",
             "{ value: string, valueAsNumber: number }"),
            ("mj-change", "Commit (blur or Enter), each step, Home/End - when the value differs from the last commit.",
             "{ value: string, valueAsNumber: number }"),
            ("mj-increment", "Each increment-button step (also when clamped at the limit).", "{ value: string, valueAsNumber: number }"),
            ("mj-decrement", "Each decrement-button step.", "{ value: string, valueAsNumber: number }"),
            ("mj-invalid", "On blur while invalid and on every failed check.", "{ validationMessage: string }"),
        ] + _BRIDGED_EVENTS,
        slots=[
            ("prefix", "Content before the input: a currency symbol or icon.", "<span>$</span>"),
            ("suffix", "Content after the input: a unit.", "<span>kg</span>"),
        ],
        properties=[
            ("value", "string. Plain decimal string, `\"\"` when empty; setting it emits no events."),
            ("valueAsNumber", "number. The value as a number (NaN when empty); accepts a number or string."),
            ("formattedValue", "string. The locale display text (read-only)."),
        ] + _FORM_PROPERTIES,
        methods=_FORM_METHODS,
        parts=[
            ("label", "The label element."),
            ("field", "The bordered box."),
            ("prefix", "Wrapper of the prefix slot."),
            ("input", "The spinbutton input."),
            ("suffix", "Wrapper of the suffix slot."),
            ("spinners", "The spinner buttons' wrapper (a column beside the input; layout only when stacked)."),
            ("increment-button", "The increment button."),
            ("decrement-button", "The decrement button."),
            ("help", "Help text."),
            ("error", "Inline error message."),
        ],
        css_properties=[],
    ),
    ComponentDoc(
        tag="mj-textarea",
        title="Textarea",
        group="text",
        summary="Multi-line text entry with auto-grow, row limits, a character/word counter and a footer slot.",
        description=_code("""
            <p><code>&lt;mj-textarea&gt;</code> wraps a native <code>&lt;textarea&gt;</code> with a label, help
            text, inline error and a <code>footer</code> slot. <code>maxlength</code> adds an <code>n/max</code>
            counter that turns to the warning colour at 90%; <code>count-words</code> adds a word count.</p>
            <p><code>rows</code> sets the initial height (default 3), <code>min-rows</code> (default 2) and
            <code>max-rows</code> bound it. With <code>auto-grow</code> the height follows the content up to
            <code>max-rows</code> and then scrolls; resizing is off. <code>required</code>,
            <code>minlength</code> and <code>maxlength</code> are validated; the <code>value</code> attribute is
            the default value and is restored on reset.</p>
        """),
        how_to_use=_code("""
            <p>Set <code>label</code>, <code>name</code> and <code>placeholder</code>. Add <code>maxlength</code>
            for the counter, <code>auto-grow</code> with <code>max-rows</code> for growing comment boxes, or
            <code>no-resize</code> for a fixed box. Listen for <code>mj-input</code> (with
            <code>charCount</code> and <code>wordCount</code>) and <code>mj-change</code>.</p>
        """),
        example="",
        examples=[
            ComponentExample(
                key="basic",
                title="Basic usage",
                description="<p>A description box with a 280-character counter and a word count.</p>",
                html=_code("""
                    <mj-textarea
                      name="description"
                      label="Description"
                      placeholder="Describe the issue in a few sentences."
                      help-text="Markdown is not supported here."
                      rows="4"
                      maxlength="280"
                      count-words>
                    </mj-textarea>
                """),
            ),
            ComponentExample(
                key="sizing",
                title="Auto-grow and fixed size",
                description="<p>The first box grows with its text from 2 to 6 rows and then scrolls; the second "
                            "is fixed at 3 rows without a resize handle; the third has the default resize "
                            "handle.</p>",
                html=_code("""
                    <div class="stack">
                      <mj-textarea label="Comment (auto-grow)" auto-grow min-rows="2" max-rows="6"
                        value="Line one&#10;Line two&#10;Line three&#10;Keep typing: the box grows to six rows, then scrolls."></mj-textarea>
                      <mj-textarea label="Fixed" rows="3" no-resize placeholder="Fixed height"></mj-textarea>
                      <mj-textarea label="Resizable" rows="3" placeholder="Drag the corner"></mj-textarea>
                    </div>
                """),
                css=_STACK_CSS,
            ),
            ComponentExample(
                key="states",
                title="States",
                description="<p>A required box with a <code>minlength</code> error revealed by "
                            "<code>reportValidity()</code>, a counter near its limit, read-only and disabled "
                            "boxes.</p>",
                html=_code("""
                    <div class="stack">
                      <mj-textarea id="feedback" label="Feedback" required minlength="20" value="Too short"
                        error-message="Please write at least 20 characters."></mj-textarea>
                      <mj-textarea label="Near the limit" maxlength="50"
                        value="This text is forty-six characters long, nearly."></mj-textarea>
                      <mj-textarea label="Read-only" readonly value="Approved by the review board on 3 March."></mj-textarea>
                      <mj-textarea label="Disabled" disabled value="Editing is locked."></mj-textarea>
                    </div>
                """),
                css=_STACK_CSS,
                script=_code("""
                    const field = document.getElementById("feedback")
                    mjSandbox.log("reportValidity()", { valid: field.reportValidity(), message: field.validationMessage })
                """),
            ),
            ComponentExample(
                key="slots",
                title="Footer slot",
                description="<p>Actions and a hint in the <code>footer</code> slot under the text.</p>",
                html=_code("""
                    <mj-textarea label="Reply" rows="3" placeholder="Write a reply" maxlength="500">
                      <div slot="footer" class="footer">
                        <button type="button">Attach file</button>
                        <span>Shift+Enter for a new paragraph</span>
                      </div>
                    </mj-textarea>
                """),
                css=_code("""
                    .footer { display: flex; gap: var(--mj-space-3); align-items: center;
                              color: var(--mj-text-muted); font-size: var(--mj-font-size-sm); }
                """),
            ),
            ComponentExample(
                key="form",
                title="In a form",
                description="<p>The textarea submits its text under <code>name</code>; the script fills it "
                            "once so <code>mj-input</code> appears in Events. Submit and Reset work as with a "
                            "native textarea.</p>",
                html=_code("""
                    <form id="demo-form" class="demo-form">
                      <mj-textarea name="bio" label="Bio" required maxlength="160" count-words
                        value="Engineer and amateur astronomer."></mj-textarea>
                      <div class="actions">
                        <button type="submit">Save profile</button>
                        <button type="reset">Reset</button>
                      </div>
                      <output id="demo-result" class="result">Submit to see the form data.</output>
                    </form>
                """),
                css=_FORM_CSS,
                script=_NATIVE_FORM_SCRIPT + _code("""
                    const bio = form.querySelector("mj-textarea")
                    const area = bio.shadowRoot.querySelector("textarea")
                    area.value = "Engineer, amateur astronomer and weekend baker."
                    area.dispatchEvent(new InputEvent("input", { bubbles: true, composed: true }))
                    mjSandbox.log("wordCount", { wordCount: bio.wordCount })
                """),
            ),
        ],
        attributes=[
            _attr("label", "Visible label text; a `*` is added when required."),
            _attr("placeholder", "Hint shown inside the empty textarea."),
            _attr("value", "Default value: shown and submitted at first render, re-applied when it changes, restored on form reset."),
            _name_attr(),
            _attr("help-text", "Guidance shown below the field."),
            _attr("error-message", "Replaces the text of a real validation error."),
            _required_message_attr(),
            _attr("rows", "Initial visible rows.", kind="number", default="3"),
            _attr("min-rows", "Minimum height in rows.", kind="number", default="2"),
            _attr("max-rows", "Maximum height in rows; with `auto-grow` the box scrolls beyond it.", kind="number"),
            _attr("auto-grow", "Height follows the content (up to `max-rows`); turns resizing off.", kind="boolean"),
            _attr("no-resize", "Removes the resize handle.", kind="boolean"),
            _attr("maxlength", "Maximum characters (enforced); shows the `n/max` counter, warning colour at 90%.", kind="number"),
            _attr("minlength", "Minimum characters for a non-empty value.", kind="number"),
            _attr("count-words", "Adds a word count to the counter.", kind="boolean"),
            _attr("required", "The field must not be empty.", kind="boolean"),
            _attr("disabled", "Disables the field.", kind="boolean"),
            _attr("readonly", "The text cannot be edited.", kind="boolean"),
            _attr("spellcheck", "`false` turns spell checking off.", kind="enum", values=["true", "false"], default="true"),
            _attr("autocomplete", "Autocomplete hint.", values=["on", "off"], default="on"),
            _attr("wrap", "Native wrap mode.", kind="enum", values=["soft", "hard", "off"], default="soft"),
            _attr("size", "Text size. Absent is the medium size.", kind="enum", values=["sm", "lg"]),
            _aria_label_attr(),
        ],
        events=[
            ("mj-input", "Every keystroke.", "{ value: string, charCount: number, wordCount: number }"),
            ("mj-change", "The value was committed (blur) and differs from the last commit.",
             "{ value: string, charCount: number, wordCount: number }"),
            ("mj-invalid", "On blur while invalid and on every failed check.", "{ validationMessage: string }"),
        ] + _BRIDGED_EVENTS,
        slots=[
            ("footer", "Content under the textarea: actions, hints.",
             '<div><button type="button">Attach file</button></div>'),
        ],
        properties=[
            ("value", "string. The current text; setting it emits no events."),
            ("wordCount", "number. Words in the current text (read-only)."),
        ] + _FORM_PROPERTIES,
        methods=_FORM_METHODS,
        parts=[
            ("label", "The label element."),
            ("wrapper", "The bordered box around textarea and footer."),
            ("textarea", "The native textarea."),
            ("help", "Help text."),
            ("error", "Inline error message."),
            ("counter", "The character / word counter."),
        ],
        css_properties=[],
    ),
    ComponentDoc(
        tag="mj-rich-text-editor",
        title="Rich Text Editor",
        group="text",
        summary="A contenteditable WYSIWYG editor with a formatting toolbar, sanitized HTML value and form participation.",
        description=_code("""
            <p><code>&lt;mj-rich-text-editor&gt;</code> edits HTML in a contenteditable region under a toolbar:
            bold, italic, underline, strikethrough; bulleted and numbered lists; heading 2, heading 3 and
            blockquote (applying an active block format again turns it back into a paragraph).
            <code>toolbar="minimal"</code> keeps only the text-style group; <code>readonly</code> hides the
            toolbar. Ctrl/Cmd+B, I and U run the text styles; the toolbar is one tab stop with arrow-key
            navigation.</p>
            <p>Every value that enters or leaves the editor is sanitized: by default only
            <code>b i u s em strong a ul ol li h1-h4 blockquote pre code br p</code> survive, and only
            <code>a[href, title]</code> keeps attributes (no <code>javascript:</code> URLs).
            <code>allowed-tags</code> narrows that list; a <code>sanitizer</code> function replaces it. Lines are
            stored as <code>&lt;p&gt;</code>; pasted HTML is sanitized and plain text is escaped.</p>
            <p><code>max-length</code> counts plain text, blocks typing beyond it, trims pastes and shows an
            <code>n/max</code> status bar. The <code>value</code> attribute sets the initial content until the
            user edits or a script sets <code>value</code>; the editor submits its HTML under
            <code>name</code>.</p>
        """),
        how_to_use=_code("""
            <p>Put the initial HTML in <code>value</code>, give the editor a <code>label</code> and a
            <code>name</code>. Use <code>toolbar="minimal"</code> for comment boxes, <code>allowed-tags</code> to
            restrict formatting, <code>max-length</code> for a limit. Read <code>value</code> (sanitized HTML)
            and <code>textContent</code> (plain text); listen for <code>mj-input</code> (debounced),
            <code>mj-change</code> (blur) and <code>mj-format</code>. Extra toolbar buttons go in the
            <code>toolbar-start</code> / <code>toolbar-end</code> slots.</p>
        """),
        example="",
        examples=[
            ComponentExample(
                key="basic",
                title="Basic usage",
                description="<p>Pre-filled content with the full toolbar. Select text and use the buttons or "
                            "Ctrl+B / Ctrl+I / Ctrl+U; watch <code>mj-format</code> and the debounced "
                            "<code>mj-input</code>.</p>",
                html=_code("""
                    <mj-rich-text-editor
                      name="announcement"
                      label="Announcement"
                      placeholder="Write your announcement&hellip;"
                      help-text="Formatting is kept; scripts and styles are removed."
                      value="<h2>Welcome aboard</h2><p>Your <b>first week</b> starts on Monday. Bring:</p><ul><li>Photo ID</li><li>Bank details</li></ul>">
                    </mj-rich-text-editor>
                """),
            ),
            ComponentExample(
                key="toolbar",
                title="Minimal toolbar, allowed tags, limit",
                description="<p><code>toolbar=\"minimal\"</code> shows only bold / italic / underline / "
                            "strike; <code>allowed-tags</code> keeps only <code>b i p</code> (the underline in the "
                            "value is dropped); <code>max-length</code> shows the counter and stops typing at "
                            "120 characters.</p>",
                html=_code("""
                    <mj-rich-text-editor label="Comment" toolbar="minimal" allowed-tags="b i p" max-length="120"
                      value="<p>Looks <b>good</b> to me, <u>ship it</u>.</p>">
                    </mj-rich-text-editor>
                """),
            ),
            ComponentExample(
                key="states",
                title="Read-only, disabled, required",
                description="<p>A read-only viewer (no toolbar), a disabled editor, and an empty required editor "
                            "whose <code>error-message</code> is revealed by <code>reportValidity()</code>.</p>",
                html=_code("""
                    <div class="stack">
                      <mj-rich-text-editor label="Policy (read-only)" readonly
                        value="<p>Expenses over <b>$500</b> need a manager's approval.</p>"></mj-rich-text-editor>
                      <mj-rich-text-editor label="Disabled" disabled value="<p>Locked while the review runs.</p>"></mj-rich-text-editor>
                      <mj-rich-text-editor id="summary-editor" label="Summary" required
                        error-message="Write a short summary before publishing."></mj-rich-text-editor>
                    </div>
                """),
                css=_STACK_CSS,
                script=_code("""
                    const editor = document.getElementById("summary-editor")
                    mjSandbox.log("reportValidity()", { valid: editor.reportValidity(), message: editor.validationMessage })
                """),
            ),
            ComponentExample(
                key="slots",
                title="Toolbar slots",
                description="<p>Your own buttons in <code>toolbar-start</code> and <code>toolbar-end</code>: "
                            "insert a signature, clear the content.</p>",
                html=_code("""
                    <mj-rich-text-editor id="slot-editor" label="Email body" value="<p>Hi team,</p>">
                      <button slot="toolbar-start" type="button" id="insert-signature">Signature</button>
                      <button slot="toolbar-end" type="button" id="clear-body">Clear</button>
                    </mj-rich-text-editor>
                """),
                script=_code("""
                    const editor = document.getElementById("slot-editor")
                    document.getElementById("insert-signature").addEventListener("click", () => {
                      editor.value = editor.value + "<p>-- <br>Ada Lovelace, Analytical Engines</p>"
                      mjSandbox.log("signature added", { html: editor.value })
                    })
                    document.getElementById("clear-body").addEventListener("click", () => {
                      editor.value = ""
                      mjSandbox.log("cleared", {})
                    })
                """),
            ),
            ComponentExample(
                key="form",
                title="In a form",
                description="<p>The editor submits its sanitized HTML under <code>name</code>; required blocks an "
                            "empty submit. Reset restores the <code>value</code> attribute.</p>",
                html=_code("""
                    <form id="demo-form" class="demo-form">
                      <mj-text-field name="title" label="Title" value="Release notes" required></mj-text-field>
                      <mj-rich-text-editor name="body" label="Body" required
                        value="<p>This release adds <b>dark mode</b>.</p>"></mj-rich-text-editor>
                      <div class="actions">
                        <button type="submit">Publish</button>
                        <button type="reset">Reset</button>
                      </div>
                      <output id="demo-result" class="result">Submit to see the form data.</output>
                    </form>
                """),
                css=_FORM_CSS,
                script=_NATIVE_FORM_SCRIPT,
            ),
            ComponentExample(
                key="events",
                title="Formatting, sanitizing and events",
                description="<p>The script selects the text and clicks Bold (<code>mj-format</code>), shows that "
                            "a value with a script and an <code>onclick</code> is sanitized, then installs a custom "
                            "<code>sanitizer</code> that keeps only paragraphs.</p>",
                html=_code("""
                    <mj-rich-text-editor id="events-editor" label="Notes" value="<p>Make this bold</p>"></mj-rich-text-editor>
                """),
                script=_code("""
                    const editor = document.getElementById("events-editor")
                    const area = editor.shadowRoot.querySelector("[contenteditable]")
                    area.focus()
                    const range = document.createRange()
                    range.selectNodeContents(area.querySelector("p"))
                    const selection = editor.shadowRoot.getSelection ? editor.shadowRoot.getSelection() : document.getSelection()
                    selection.removeAllRanges()
                    selection.addRange(range)
                    editor.shadowRoot.querySelector(".tb-btn[data-cmd='bold']").click()
                    mjSandbox.log("after bold", { html: editor.value })
                    editor.value = '<p onclick="alert(1)">Safe <a href="javascript:alert(1)">link</a><script>alert(1)<\\/script></p>'
                    mjSandbox.log("sanitized by default", { html: editor.value })
                    editor.sanitizer = (html) => {
                      const doc = new DOMParser().parseFromString(html, "text/html")
                      return Array.from(doc.body.querySelectorAll("p")).map((p) => "<p>" + p.textContent + "</p>").join("")
                    }
                    editor.value = "<h2>Heading</h2><p>Only <b>paragraph</b> text survives.</p>"
                    mjSandbox.log("custom sanitizer", { html: editor.value, text: editor.textContent })
                """),
            ),
        ],
        attributes=[
            _attr("label", "Visible label; clicking it focuses the editor."),
            _attr("placeholder", "Shown while the editor is empty."),
            _attr("value", "Initial HTML (sanitized). Applies until the user edits or a script sets `value`; restored on form reset."),
            _name_attr(),
            _attr("help-text", "Guidance shown below the editor."),
            _attr("error-message", "Replaces the text of a real validation error."),
            _required_message_attr(),
            _attr("toolbar", "Toolbar layout: `minimal` keeps only bold / italic / underline / strike.",
                  kind="enum", values=["full", "minimal"], default="full"),
            _attr("allowed-tags", "Comma or space separated tags; narrows the default allow-list (never widens it).",
                  values=["b i p", "b i u s p ul ol li", "p br"]),
            _attr("max-length", "Plain-text character limit: blocks typing past it, trims pastes, shows a counter.", kind="number"),
            _attr("required", "The editor must not be empty.", kind="boolean"),
            _attr("disabled", "Disables editing and the toolbar.", kind="boolean"),
            _attr("readonly", "Content is not editable and the toolbar is hidden.", kind="boolean"),
            _aria_label_attr(),
        ],
        events=[
            ("mj-input", "Content changed (debounced 150 ms, flushed on blur).", "{ html: string, text: string }"),
            ("mj-change", "Blur after the content changed.", "{ html: string, text: string }"),
            ("mj-format", "A toolbar button or shortcut ran a command.", "{ command: string, active: boolean }"),
            ("mj-invalid", "On blur while invalid and on every failed check.", "{ validationMessage: string }"),
        ] + _BRIDGED_EVENTS,
        slots=[
            ("toolbar-start", "Extra toolbar content (after the built-in groups).", '<button type="button">Signature</button>'),
            ("toolbar-end", "Extra toolbar content at the end.", '<button type="button">Clear</button>'),
        ],
        properties=[
            ("value", "string. Sanitized HTML; setting it sanitizes, replaces the content and emits no events."),
            ("htmlValue", "string. Same as `value` (read-only)."),
            ("textContent", "string. The plain text of the content (getter)."),
            ("sanitizer", "(html: string) => string. Replaces the default sanitizer; null restores it."),
        ] + _FORM_PROPERTIES,
        methods=[
            ("checkValidity() -> boolean", "Runs the constraints."),
            ("reportValidity() -> boolean", "Runs the constraints and shows the inline error."),
            ("showValidation() -> boolean", "Same as `reportValidity()`."),
            ("focus(options)", "Focuses the editable region."),
        ],
        parts=[
            ("label", "The label."),
            ("editor-wrap", "The bordered box around toolbar and editor."),
            ("toolbar", "The toolbar (`role=toolbar`)."),
            ("toolbar-group", "One group of buttons."),
            ("toolbar-button", "A toolbar button."),
            ("editor", "The contenteditable region."),
            ("status-bar", "The `n/max` counter shown with `max-length`."),
            ("help", "Help text."),
            ("error", "Inline error message."),
        ],
        css_properties=[],
    ),
    ComponentDoc(
        tag="mj-markdown-editor",
        title="Markdown Editor",
        group="text",
        summary="A Markdown textarea with a formatting toolbar and an edit / split / preview switcher with a sanitized preview.",
        description=_code("""
            <p><code>&lt;mj-markdown-editor&gt;</code> edits Markdown in a textarea and renders a live preview.
            A radio group switches between <code>edit</code>, <code>split</code> (side by side, fixed divider)
            and <code>preview</code>; the toolbar inserts bold, italic, link, headings, lists, quote and code
            syntax (Ctrl/Cmd+B, I, K) through the undo history.</p>
            <p>The built-in renderer handles headings, paragraphs, quotes, lists, fenced code, rules, emphasis,
            code spans and safe links. Its output is <strong>always</strong> sanitized: a custom
            <code>sanitizer</code> replaces the default allow-list, it never switches sanitizing off; a custom
            <code>renderer</code> can replace the Markdown parser. <code>readonly</code> forces the preview and
            hides the header, which makes a Markdown viewer. The <code>preview-empty</code> slot is shown while
            there is nothing to preview.</p>
            <p><code>required</code>, <code>minlength</code> and <code>maxlength</code> are validated; the
            editor submits the Markdown text under <code>name</code>.</p>
        """),
        how_to_use=_code("""
            <p>Set <code>value</code> (newlines as <code>&amp;#10;</code> in markup, or set the property),
            <code>label</code>, <code>name</code> and the starting <code>view</code>. The view switcher updates the
            <code>view</code> attribute and fires <code>mj-view-change</code>. Read <code>previewHtml</code> for
            the rendered HTML and <code>wordCount</code>; put your own buttons in <code>toolbar-start</code> and
            <code>toolbar-end</code>.</p>
        """),
        example="",
        examples=[
            ComponentExample(
                key="basic",
                title="Basic usage",
                description="<p>Split view with sample Markdown. Edit on the left; switch to Preview with the "
                            "view buttons (<code>mj-view-change</code>).</p>",
                html=_code("""
                    <mj-markdown-editor
                      name="notes"
                      label="Release notes"
                      view="split"
                      count-words
                      value="## Version 2.4&#10;&#10;This release adds **dark mode** and _faster_ search.&#10;&#10;- New theme switcher&#10;- Search results in under 100 ms&#10;&#10;See the [changelog](https://example.com/changelog).">
                    </mj-markdown-editor>
                """),
            ),
            ComponentExample(
                key="views",
                title="Edit, preview and read-only viewer",
                description="<p>An editor that opens in <code>preview</code>, and a <code>readonly</code> viewer "
                            "(preview only, no header).</p>",
                html=_code("""
                    <div class="stack">
                      <mj-markdown-editor label="Opens in preview" view="preview"
                        value="# Meeting notes&#10;&#10;1. Budget approved&#10;2. Launch moved to **May**"></mj-markdown-editor>
                      <mj-markdown-editor label="Viewer" readonly
                        value="> Read-only Markdown: the header and toolbar are hidden.&#10;&#10;Use it to display stored notes."></mj-markdown-editor>
                    </div>
                """),
                css=_STACK_CSS,
            ),
            ComponentExample(
                key="states",
                title="Limits and validation",
                description="<p><code>maxlength</code> with the counter and word count, a <code>minlength</code> "
                            "error revealed by <code>reportValidity()</code>, and a disabled editor.</p>",
                html=_code("""
                    <div class="stack">
                      <mj-markdown-editor label="Tweet-sized" maxlength="140" count-words value="Short **and** sweet."></mj-markdown-editor>
                      <mj-markdown-editor id="abstract" label="Abstract" minlength="40" required value="Too short."
                        error-message="The abstract needs at least 40 characters."></mj-markdown-editor>
                      <mj-markdown-editor label="Disabled" disabled value="Locked for review."></mj-markdown-editor>
                    </div>
                """),
                css=_STACK_CSS,
                script=_code("""
                    const editor = document.getElementById("abstract")
                    mjSandbox.log("reportValidity()", { valid: editor.reportValidity(), message: editor.validationMessage })
                """),
            ),
            ComponentExample(
                key="slots",
                title="Toolbar and preview-empty slots",
                description="<p>Buttons in <code>toolbar-start</code> / <code>toolbar-end</code> and a message in "
                            "<code>preview-empty</code>, shown while the editor is empty.</p>",
                html=_code("""
                    <mj-markdown-editor id="slot-md" label="Draft" view="split" placeholder="Start typing Markdown">
                      <button slot="toolbar-start" type="button" id="insert-template">Template</button>
                      <button slot="toolbar-end" type="button" id="clear-draft">Clear</button>
                      <p slot="preview-empty">Nothing to preview yet. Press Template to start.</p>
                    </mj-markdown-editor>
                """),
                script=_code("""
                    const editor = document.getElementById("slot-md")
                    document.getElementById("insert-template").addEventListener("click", () => {
                      editor.value = "## Summary\\n\\nWhat changed and why.\\n\\n## Testing\\n\\n- [ ] Unit tests"
                    })
                    document.getElementById("clear-draft").addEventListener("click", () => { editor.value = "" })
                """),
            ),
            ComponentExample(
                key="form",
                title="In a form",
                description="<p>The editor submits its Markdown under <code>name</code>. Submit shows the entries, "
                            "Reset restores the <code>value</code> attribute.</p>",
                html=_code("""
                    <form id="demo-form" class="demo-form">
                      <mj-markdown-editor name="readme" label="README" required value="# Project&#10;&#10;One-line description."></mj-markdown-editor>
                      <div class="actions">
                        <button type="submit">Save</button>
                        <button type="reset">Reset</button>
                      </div>
                      <output id="demo-result" class="result">Submit to see the form data.</output>
                    </form>
                """),
                css=_FORM_CSS,
                script=_NATIVE_FORM_SCRIPT,
            ),
            ComponentExample(
                key="events",
                title="Renderer, sanitizer and events",
                description="<p>The script switches to split view (<code>mj-view-change</code>), applies Bold from "
                            "the toolbar (<code>mj-input</code>), then installs a <code>renderer</code> that turns "
                            "<code>==text==</code> into <code>&lt;mark&gt;</code>: the default sanitizer drops "
                            "<code>mark</code> until a custom <code>sanitizer</code> allows it.</p>",
                html=_code("""
                    <mj-markdown-editor id="events-md" label="Highlights" value="Remember the ==deadline== on Friday."></mj-markdown-editor>
                """),
                script=_code("""
                    const editor = document.getElementById("events-md")
                    const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms))
                    editor.shadowRoot.querySelector(".mode-tab[data-view='split']").click()
                    const area = editor.shadowRoot.querySelector("textarea")
                    area.focus()
                    area.setSelectionRange(0, 8)
                    editor.shadowRoot.querySelector(".tb-btn[data-syntax='**{sel}**']").click()
                    await wait(300)
                    mjSandbox.log("built-in renderer", { previewHtml: editor.previewHtml })
                    const escape = (text) => text.replace(/&/g, "&amp;").replace(/</g, "&lt;")
                    editor.renderer = (markdown) => "<p>" + escape(markdown).replace(/==(.+?)==/g, "<mark>$1</mark>") + "</p>"
                    editor.value = editor.value
                    await wait(300)
                    mjSandbox.log("custom renderer, default sanitizer", { previewHtml: editor.previewHtml })
                    editor.sanitizer = (html) => {
                      const doc = new DOMParser().parseFromString(html, "text/html")
                      for (const element of Array.from(doc.body.querySelectorAll("*"))) {
                        if (["P", "MARK"].includes(element.tagName) === false) {
                          element.replaceWith(...element.childNodes)
                        }
                      }
                      return doc.body.innerHTML
                    }
                    editor.value = editor.value
                    await wait(300)
                    mjSandbox.log("custom sanitizer allows mark", { previewHtml: editor.previewHtml })
                """),
            ),
        ],
        attributes=[
            _attr("label", "Visible label of the textarea."),
            _attr("placeholder", "Hint shown in the empty textarea."),
            _attr("value", "Initial Markdown. Applies until the user edits or a script sets `value`; restored on form reset."),
            _name_attr(),
            _attr("help-text", "Guidance shown below the editor."),
            _attr("error-message", "Replaces the text of a real validation error."),
            _required_message_attr(),
            _attr("view", "Current view; the view switcher updates it. `readonly` forces preview.",
                  kind="enum", values=["edit", "split", "preview"], default="edit"),
            _attr("maxlength", "Maximum characters (enforced by the textarea); shown in the status bar.", kind="number"),
            _attr("minlength", "Minimum characters for a non-empty value.", kind="number"),
            _attr("count-words", "Adds a word count to the status bar.", kind="boolean"),
            _attr("required", "The editor must not be empty.", kind="boolean"),
            _attr("disabled", "Disables the textarea, toolbar and view switcher.", kind="boolean"),
            _attr("readonly", "Shows only the preview, without header or toolbar.", kind="boolean"),
            _aria_label_attr(),
        ],
        events=[
            ("mj-input", "Every edit.", "{ value: string, wordCount: number }"),
            ("mj-change", "Blur after the text changed.", "{ value: string, wordCount: number }"),
            ("mj-view-change", "The user picked a view (not fired for attribute changes).", "{ view: 'edit' | 'split' | 'preview' }"),
            ("mj-invalid", "On blur while invalid and on every failed check.", "{ validationMessage: string }"),
        ] + _BRIDGED_EVENTS,
        slots=[
            ("toolbar-start", "Extra toolbar content at the start (hidden in preview view).", '<button type="button">Template</button>'),
            ("toolbar-end", "Extra toolbar content at the end.", '<button type="button">Clear</button>'),
            ("preview-empty", "Shown in the preview while there is nothing to render.", "<p>Nothing to preview yet.</p>"),
        ],
        properties=[
            ("value", "string. The Markdown; setting it updates textarea, status and preview, and emits no events."),
            ("previewHtml", "string. The rendered, sanitized preview HTML (read-only)."),
            ("wordCount", "number. Words in the text (read-only)."),
            ("renderer", "(markdown: string) => string. Replaces the built-in Markdown renderer; null restores it."),
            ("sanitizer", "(html: string) => string. Replaces the default allow-list; the output is always sanitized; null restores it."),
        ] + _FORM_PROPERTIES,
        methods=[
            ("checkValidity() -> boolean", "Runs the constraints."),
            ("reportValidity() -> boolean", "Runs the constraints and shows the inline error."),
            ("showValidation() -> boolean", "Same as `reportValidity()`."),
            ("focus(options)", "Focuses the textarea (the preview view button in preview view)."),
        ],
        parts=[
            ("label", "The label."),
            ("outer", "The bordered box."),
            ("header", "View switcher and toolbar row."),
            ("mode-tabs", "The view radio group."),
            ("mode-tab", "One view button (`role=radio`)."),
            ("toolbar", "The syntax toolbar."),
            ("toolbar-button", "A toolbar button."),
            ("edit-pane", "The editing pane."),
            ("textarea", "The textarea."),
            ("divider", "The divider in split view."),
            ("preview-pane", "The preview pane."),
            ("preview-content", "The rendered HTML."),
            ("status-bar", "Character / word count."),
            ("help", "Help text."),
            ("error", "Inline error message."),
        ],
        css_properties=[],
    ),
    ComponentDoc(
        tag="mj-code-editor",
        title="Code Editor",
        group="text",
        summary="A monospace code textarea with line numbers, Tab indentation and a pluggable highlighter.",
        description=_code("""
            <p><code>&lt;mj-code-editor&gt;</code> is a plain <code>&lt;textarea&gt;</code> over a mirrored display
            layer, with a line-number gutter, Tab / Shift+Tab indentation of the caret or every selected line,
            soft wrap and form participation. Escape then Tab leaves the editor (Tab is not trapped when
            read-only or disabled).</p>
            <p>There is <strong>no built-in syntax highlighting</strong>: assign a <code>highlighter</code>
            function <code>(code, language) =&gt; html</code>. Its output is sanitized to
            <code>span b i em strong mark code br</code> with only <code>class</code> kept. The layer is in the
            shadow root, so style the classes either with <code>highlightStyles</code> (CSS text or a
            <code>CSSStyleSheet</code> adopted into the shadow root, so a class-based theme applies as written)
            or from the page with <code>::part()</code>: every highlighted element is exported as part
            <code>token</code> plus <code>token-&lt;class&gt;</code> for each class. <code>language</code> is
            only passed to the highlighter.</p>
            <p>The height is fixed (12.5rem by default, <code>--mj-code-editor-height</code>, or
            <code>rows</code>) and scrolls. <code>required</code>, <code>minlength</code> and
            <code>maxlength</code> are validated; the <code>value</code> attribute sets the initial code until it
            is edited.</p>
        """),
        how_to_use=_code("""
            <p>Put the code in <code>value</code> (newlines as <code>&amp;#10;</code>) or set the property. Set
            <code>tab-size</code> and <code>tab-inserts-spaces="false"</code> for real tabs,
            <code>word-wrap</code> for prose-like content, <code>line-numbers="false"</code> to hide the gutter.
            Put buttons in the <code>toolbar</code> slot. Read <code>lineCount</code>; listen for
            <code>mj-input</code> and <code>mj-change</code>.</p>
        """),
        example="",
        examples=[
            ComponentExample(
                key="basic",
                title="Basic usage",
                description="<p>Pre-filled JavaScript with line numbers. Press Tab to indent, Shift+Tab to "
                            "outdent; Escape then Tab moves on.</p>",
                html=_code("""
                    <mj-code-editor
                      name="snippet"
                      label="Snippet"
                      language="javascript"
                      rows="8"
                      value="function greet(name) {&#10;  // Say hello&#10;  return `Hello, ${name}!`&#10;}&#10;&#10;console.log(greet(&quot;world&quot;))">
                    </mj-code-editor>
                """),
            ),
            ComponentExample(
                key="highlighter",
                title="Highlighter function",
                description="<p>The script assigns a small <code>highlighter</code>: keywords in "
                            "<code>&lt;b&gt;</code>, comments in <code>&lt;i&gt;</code>, strings in "
                            "<code>&lt;mark&gt;</code>. Type and watch it re-highlight.</p>",
                html=_code("""
                    <mj-code-editor id="hl-editor" label="Highlighted" language="javascript" rows="7"
                      value="// Fetch the user and log the name&#10;const response = await fetch(&quot;/api/user&quot;)&#10;if (response.ok) {&#10;  const user = await response.json()&#10;  console.log(&quot;Hello&quot;, user.name)&#10;}"></mj-code-editor>
                """),
                script=_code(r"""
                    const editor = document.getElementById("hl-editor")
                    const KEYWORDS = /\b(const|let|var|function|return|if|else|await|async|for|while|new)\b/g
                    const escape = (text) => text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
                    editor.highlighter = (code, language) => code.split("\n").map((line) => {
                      const comment = line.indexOf("//")
                      const body = comment === -1 ? line : line.slice(0, comment)
                      const rest = comment === -1 ? "" : "<i>" + escape(line.slice(comment)) + "</i>"
                      const marked = escape(body)
                        .replace(/(&quot;|")([^"]*)"/g, "<mark>\"$2\"</mark>")
                        .replace(KEYWORDS, "<b>$1</b>")
                      return marked + rest
                    }).join("\n")
                    mjSandbox.log("highlighter installed", { language: editor.getAttribute("language"), lines: editor.lineCount })
                """),
            ),
            ComponentExample(
                key="token-styles",
                title="Styling token classes",
                description="<p>A highlighter that emits <code>&lt;span class=\"tok-…\"&gt;</code>. The first "
                            "editor colours them with <code>highlightStyles</code> (CSS text adopted into its "
                            "shadow root); the second with page CSS on the exported parts, "
                            "<code>mj-code-editor::part(token-tok-keyword)</code>.</p>",
                html=_code("""
                    <div class="stack">
                      <mj-code-editor id="styled-editor" label="highlightStyles" language="python" rows="4"
                        value="def area(radius):&#10;    # circle&#10;    return 3.14159 * radius ** 2"></mj-code-editor>
                      <mj-code-editor id="parts-editor" label="::part() from the page" language="python" rows="4"
                        value="for item in items:&#10;    # skip empties&#10;    if item: print(item)"></mj-code-editor>
                    </div>
                """),
                css=_code("""
                    .stack { display: grid; gap: var(--mj-space-4); max-inline-size: 36rem; }
                    #parts-editor::part(token-tok-keyword) { color: var(--mj-chart-series-1); font-weight: var(--mj-font-weight-bold); }
                    #parts-editor::part(token-tok-comment) { color: var(--mj-text-muted); font-style: italic; }
                """),
                script=_code(r"""
                    const KEYWORDS = /\b(def|return|for|in|if|else|import|from|while)\b/g
                    const escape = (text) => text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
                    const highlight = (code) => code.split("\n").map((line) => {
                      const hash = line.indexOf("#")
                      const body = hash === -1 ? line : line.slice(0, hash)
                      const comment = hash === -1 ? "" : '<span class="tok-comment">' + escape(line.slice(hash)) + "</span>"
                      return escape(body).replace(KEYWORDS, '<span class="tok-keyword">$1</span>') + comment
                    }).join("\n")
                    const styled = document.getElementById("styled-editor")
                    styled.highlighter = highlight
                    styled.highlightStyles = ".tok-keyword { color: var(--mj-chart-series-3); font-weight: var(--mj-font-weight-bold); } .tok-comment { color: var(--mj-color-success); }"
                    document.getElementById("parts-editor").highlighter = highlight
                """),
            ),
            ComponentExample(
                key="options",
                title="Wrap, tabs, gutter and sizes",
                description="<p><code>word-wrap</code> with a long line, real tabs (<code>tab-inserts-spaces="
                            "\"false\"</code>, <code>tab-size=\"8\"</code>), no gutter, and the small and large "
                            "sizes.</p>",
                html=_code("""
                    <div class="stack">
                      <mj-code-editor label="Word wrap" word-wrap rows="4"
                        value="A long line that wraps instead of scrolling sideways, because word-wrap is set on this editor."></mj-code-editor>
                      <mj-code-editor label="Makefile (tabs)" tab-inserts-spaces="false" tab-size="8" rows="4"
                        value="build:&#10;&#9;go build ./...&#10;test:&#10;&#9;go test ./..."></mj-code-editor>
                      <mj-code-editor label="No gutter" line-numbers="false" rows="3" value="SELECT id, name&#10;FROM users;"></mj-code-editor>
                      <mj-code-editor label="Small" size="sm" rows="2" value="small = True"></mj-code-editor>
                      <mj-code-editor label="Large" size="lg" rows="2" value="large = True"></mj-code-editor>
                    </div>
                """),
                css=_code("""
                    .stack { display: grid; gap: var(--mj-space-4); max-inline-size: 36rem; }
                """),
            ),
            ComponentExample(
                key="states",
                title="Read-only, disabled, required",
                description="<p>A read-only listing (Tab is not trapped), a disabled editor and an empty required "
                            "editor revealed by <code>reportValidity()</code>.</p>",
                html=_code("""
                    <div class="stack">
                      <mj-code-editor label="Read-only" readonly rows="3" value="{&#10;  &quot;version&quot;: 3&#10;}"></mj-code-editor>
                      <mj-code-editor label="Disabled" disabled rows="2" value="echo locked"></mj-code-editor>
                      <mj-code-editor id="query-editor" label="Query" required rows="3" placeholder="SELECT ..."
                        error-message="Enter a query to run."></mj-code-editor>
                    </div>
                """),
                css=_STACK_CSS,
                script=_code("""
                    const editor = document.getElementById("query-editor")
                    mjSandbox.log("reportValidity()", { valid: editor.reportValidity(), message: editor.validationMessage })
                """),
            ),
            ComponentExample(
                key="slots",
                title="Toolbar slot",
                description="<p>Buttons in the <code>toolbar</code> slot; Run logs the code and its "
                            "<code>lineCount</code>.</p>",
                html=_code("""
                    <mj-code-editor id="slot-code" label="Script" rows="5" value="print(&quot;hello&quot;)&#10;print(2 + 2)">
                      <div slot="toolbar" class="toolbar">
                        <button type="button" id="run-code">Run</button>
                        <button type="button" id="reset-code">Reset</button>
                      </div>
                    </mj-code-editor>
                """),
                css=_code("""
                    .toolbar { display: flex; gap: var(--mj-space-2); padding: var(--mj-space-1); }
                """),
                script=_code("""
                    const editor = document.getElementById("slot-code")
                    document.getElementById("run-code").addEventListener("click", () => {
                      mjSandbox.log("run", { code: editor.value, lineCount: editor.lineCount })
                    })
                    document.getElementById("reset-code").addEventListener("click", () => {
                      editor.value = 'print("hello")'
                    })
                """),
            ),
            ComponentExample(
                key="events",
                title="Indenting and events in a form",
                description="<p>The script selects two lines and presses Tab, Shift+Tab and Tab again (the value "
                            "and <code>lineCount</code> are logged); the editor submits its text under "
                            "<code>name</code> with the form.</p>",
                html=_code("""
                    <form id="demo-form" class="demo-form">
                      <mj-code-editor id="events-code" name="config" label="config.yaml" rows="5" required
                        value="server:&#10;port: 8080&#10;host: 0.0.0.0"></mj-code-editor>
                      <div class="actions">
                        <button type="submit">Save</button>
                        <button type="reset">Reset</button>
                      </div>
                      <output id="demo-result" class="result">Submit to see the form data.</output>
                    </form>
                """),
                css=_FORM_CSS,
                script=_NATIVE_FORM_SCRIPT + _code("""
                    const editor = document.getElementById("events-code")
                    const area = editor.shadowRoot.querySelector("textarea")
                    area.focus()
                    area.setSelectionRange(area.value.indexOf("port"), area.value.length)
                    area.dispatchEvent(new KeyboardEvent("keydown", { key: "Tab", bubbles: true, composed: true, cancelable: true }))
                    mjSandbox.log("Tab indented the selected lines", { value: editor.value, lineCount: editor.lineCount })
                    area.dispatchEvent(new KeyboardEvent("keydown", { key: "Tab", shiftKey: true, bubbles: true, composed: true, cancelable: true }))
                    mjSandbox.log("Shift+Tab outdented them", { value: editor.value })
                    area.dispatchEvent(new KeyboardEvent("keydown", { key: "Tab", bubbles: true, composed: true, cancelable: true }))
                    mjSandbox.log("Tab again: valid YAML", { value: editor.value })
                """),
            ),
        ],
        attributes=[
            _attr("label", "Visible label of the textarea."),
            _attr("placeholder", "Hint shown in the empty editor."),
            _attr("value", "Initial code (CRLF becomes LF). Applies until edited or set from script; restored on form reset."),
            _name_attr(),
            _attr("help-text", "Guidance shown below the editor."),
            _attr("error-message", "Replaces the text of a real validation error."),
            _required_message_attr(),
            _attr("language", "Language name passed to the `highlighter`; no effect without one.",
                  values=["plaintext", "javascript", "python", "json", "sql", "yaml"], default="plaintext"),
            _attr("line-numbers", "`false` hides the line-number gutter.", kind="boolean", default="true"),
            _attr("word-wrap", "Soft-wraps long lines (the gutter follows wrapped lines).", kind="boolean"),
            _attr("tab-size", "Columns per indent (1-16).", kind="number", default="4"),
            _attr("tab-inserts-spaces", "`false` makes Tab insert a tab character instead of spaces.", kind="boolean", default="true"),
            _attr("rows", "Visible lines; sets the editor height.", kind="number"),
            _attr("maxlength", "Maximum characters (enforced; validated).", kind="number"),
            _attr("minlength", "Minimum characters for a non-empty value.", kind="number"),
            _attr("required", "The editor must not be empty.", kind="boolean"),
            _attr("disabled", "Disables the editor.", kind="boolean"),
            _attr("readonly", "The code cannot be edited; Tab moves focus.", kind="boolean"),
            _attr("size", "Font size. Absent is the medium size.", kind="enum", values=["sm", "lg"]),
            _aria_label_attr(),
        ],
        events=[
            ("mj-input", "Every edit, including Tab indentation.", "{ value: string, lineCount: number }"),
            ("mj-change", "Blur after the code changed.", "{ value: string, lineCount: number }"),
            ("mj-invalid", "On blur while invalid and on every failed check.", "{ validationMessage: string }"),
        ] + _BRIDGED_EVENTS,
        slots=[
            ("toolbar", "Toolbar above the code; hidden while empty.",
             '<div><button type="button">Run</button> <button type="button">Format</button></div>'),
        ],
        properties=[
            ("value", "string. The code (LF line endings); setting it re-renders and emits no events."),
            ("lineCount", "number. Number of lines (read-only)."),
            ("highlighter", "(code: string, language: string) => string | null. Returns highlighted HTML; sanitized to inline tags with `class`."),
            ("highlightStyles", "string | CSSStyleSheet | null. CSS for the highlighter's classes, adopted into the shadow root (a sheet can be shared by many editors)."),
        ] + _FORM_PROPERTIES,
        methods=[
            ("checkValidity() -> boolean", "Runs the constraints."),
            ("reportValidity() -> boolean", "Runs the constraints and shows the inline error."),
            ("showValidation() -> boolean", "Same as `reportValidity()`."),
            ("focus(options)", "Focuses the textarea."),
        ],
        parts=[
            ("label", "The label."),
            ("outer", "The bordered box."),
            ("toolbar", "Wrapper of the toolbar slot."),
            ("container", "The scrolling code area."),
            ("gutter", "Line numbers."),
            ("highlight-layer", "The display layer behind the textarea."),
            ("token", "Every element of the highlighter output."),
            ("token-<class>", "A highlighted element with that class, e.g. `token-tok-keyword` for `class=\"tok-keyword\"`."),
            ("textarea", "The transparent textarea."),
            ("help", "Help text."),
            ("error", "Inline error message."),
        ],
        css_properties=[
            ("--mj-code-editor-height", "Editor height when `rows` is not set (default 12.5rem)."),
            ("--mj-code-editor-font-size", "Code font size (default var(--mj-font-size-sm); `size` switches it)."),
        ],
    ),
    ComponentDoc(
        tag="mj-inline-edit",
        title="Inline Edit",
        group="text",
        summary="Text that turns into an input in place, with Save / Cancel, validation and a cancelable change event.",
        description=_code("""
            <p><code>&lt;mj-inline-edit&gt;</code> shows a value as text with a pencil button. Clicking the text
            (<code>trigger="click"</code>, the default) or the pencil opens an input (a textarea with
            <code>multiline</code>) with Save and Cancel buttons (none with <code>compact</code>). Enter commits
            (Ctrl/Cmd+Enter in multiline), Escape cancels, and moving focus away <strong>cancels</strong> the
            edit. With <code>trigger="button"</code> only the pencil opens the editor; the pencil is the keyboard
            entry point in both modes.</p>
            <p>A commit is validated first (<code>required</code>, <code>minlength</code>,
            <code>maxlength</code>, <code>pattern</code> matched against the whole value) and then fires a
            cancelable <code>mj-change</code>: call <code>preventDefault()</code> to roll it back, e.g. when a
            save fails. <code>placeholder</code> is the text shown while the value is empty. The control is
            form-associated; the <code>value</code> attribute sets the initial value until the first commit.</p>
        """),
        how_to_use=_code("""
            <p>Set <code>value</code>, an accessible <code>label</code> (it is not displayed) and a
            <code>placeholder</code> for the empty state. Listen for <code>mj-change</code> to save, cancelling it
            to reject; <code>mj-edit-start</code> (cancelable) and <code>mj-edit-cancel</code> track the editing
            session. Replace the display with the <code>display</code> slot and the pencil with
            <code>edit-icon</code>.</p>
        """),
        example="",
        examples=[
            ComponentExample(
                key="basic",
                title="Basic usage",
                description="<p>Click the title (or Tab to the pencil and press Enter), edit, then Enter or Save. "
                            "Escape or clicking elsewhere cancels.</p>",
                html=_code("""
                    <mj-inline-edit
                      name="title"
                      label="Document title"
                      value="Quarterly planning"
                      placeholder="Untitled document"
                      required>
                    </mj-inline-edit>
                """),
            ),
            ComponentExample(
                key="variants",
                title="Multiline, compact, button trigger",
                description="<p>A multiline description (Ctrl+Enter saves), a compact field without buttons, a "
                            "field that only opens from the pencil, and an empty one showing its "
                            "<code>placeholder</code>.</p>",
                html=_code("""
                    <div class="stack">
                      <mj-inline-edit label="Description" multiline
                        value="Plan the roadmap for Q3. Ctrl+Enter saves this multiline field."></mj-inline-edit>
                      <mj-inline-edit label="Owner" compact value="Grace Hopper"></mj-inline-edit>
                      <mj-inline-edit label="Budget code" trigger="button" value="OPS-2026"></mj-inline-edit>
                      <mj-inline-edit label="Nickname" placeholder="Add a nickname"></mj-inline-edit>
                    </div>
                """),
                css=_STACK_CSS,
            ),
            ComponentExample(
                key="validation",
                title="Validation and states",
                description="<p>The first field needs a ticket key matching <code>[A-Z]+-[0-9]+</code>; try "
                            "saving <code>abc</code> to see the error. Read-only and disabled fields cannot be "
                            "opened.</p>",
                html=_code("""
                    <div class="stack">
                      <mj-inline-edit label="Ticket" value="WEB-101" required pattern="[A-Z]+-[0-9]+"
                        error-message="Use a key such as WEB-101."></mj-inline-edit>
                      <mj-inline-edit label="Short name" value="Ops" minlength="2" maxlength="12"></mj-inline-edit>
                      <mj-inline-edit label="Created by" value="system" readonly></mj-inline-edit>
                      <mj-inline-edit label="Archived" value="Legacy project" disabled></mj-inline-edit>
                    </div>
                """),
                css=_STACK_CSS,
            ),
            ComponentExample(
                key="slots",
                title="Display and edit-icon slots",
                description="<p>The <code>display</code> slot renders the value as a heading; the "
                            "<code>edit-icon</code> slot replaces the pencil.</p>",
                html=_code("""
                    <mj-inline-edit id="slot-edit" label="Page heading" value="Welcome to the handbook">
                      <h3 slot="display" id="slot-display">Welcome to the handbook</h3>
                      <svg slot="edit-icon" viewBox="0 0 16 16" width="14" height="14" aria-hidden="true">
                        <path d="M2 14l1-4 8-8 3 3-8 8z" fill="none" stroke="currentColor" stroke-width="1.5"/>
                      </svg>
                    </mj-inline-edit>
                """),
                css=_code("""
                    h3 { margin: 0; font-size: var(--mj-font-size-xl); }
                """),
                script=_code("""
                    const edit = document.getElementById("slot-edit")
                    edit.addEventListener("mj-change", (event) => {
                      document.getElementById("slot-display").textContent = event.detail.value
                    })
                """),
            ),
            ComponentExample(
                key="events",
                title="Async save with rejection",
                description="<p>The script opens the editor (<code>mj-edit-start</code>), saves a name that is "
                            "already taken (its <code>mj-change</code> is cancelled: the value rolls back and the "
                            "editor stays open), then saves a free one.</p>",
                html=_code("""
                    <mj-inline-edit id="events-edit" label="Project name" value="Apollo"></mj-inline-edit>
                    <p class="hint">Names already taken: Gemini, Mercury.</p>
                """),
                css=_code("""
                    .hint { color: var(--mj-text-muted); font-size: var(--mj-font-size-sm); }
                """),
                script=_code("""
                    const edit = document.getElementById("events-edit")
                    const taken = ["Gemini", "Mercury"]
                    edit.addEventListener("mj-change", (event) => {
                      if (taken.includes(event.detail.value)) {
                        event.preventDefault()
                        mjSandbox.log("rejected: name taken", { value: event.detail.value, keeps: event.detail.previousValue })
                      }
                    })
                    const save = (text) => {
                      edit.shadowRoot.querySelector("[part='edit-trigger']").click()
                      const input = edit.shadowRoot.querySelector(".edit-wrap input")
                      input.value = text
                      input.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true, composed: true, cancelable: true }))
                      mjSandbox.log("after save", { value: edit.value, editing: edit.editing })
                    }
                    save("Gemini")
                    save("Artemis")
                """),
            ),
        ],
        attributes=[
            _attr("value", "Initial value; applies until the first commit or a script sets `value`."),
            _attr("label", "Accessible name of the input and the pencil button (not displayed)."),
            _attr("placeholder", "Display text while the value is empty.", default="—"),
            _name_attr(),
            _attr("trigger", "`click` opens the editor from the text and the pencil; `button` only from the pencil.",
                  kind="enum", values=["click", "button"], default="click"),
            _attr("multiline", "Edits in a textarea; Ctrl/Cmd+Enter commits.", kind="boolean"),
            _attr("compact", "No Save / Cancel buttons.", kind="boolean"),
            _attr("required", "The value must not be empty (whitespace counts as empty).", kind="boolean"),
            _attr("minlength", "Minimum characters.", kind="number"),
            _attr("maxlength", "Maximum characters.", kind="number"),
            _attr("pattern", "Regular expression the whole non-empty value must match.", values=["[A-Z]+-[0-9]+"]),
            _attr("error-message", "Replaces every validation message."),
            _required_message_attr(),
            _attr("disabled", "Cannot be edited; an open edit is cancelled.", kind="boolean"),
            _attr("readonly", "Cannot be edited; an open edit is cancelled.", kind="boolean"),
            _attr("edit-label", "Prefix of the pencil button's accessible name.", default="Edit"),
            _attr("commit-label", "Save button text.", default="Save"),
            _attr("cancel-label", "Cancel button text.", default="Cancel"),
        ],
        events=[
            ("mj-edit-start", "Cancelable. The editor is about to open.", "{ value: string }"),
            ("mj-change", "Cancelable. A valid commit; the value is applied first, and if cancelled it is rolled back and the editor stays open.",
             "{ value: string, previousValue: string }"),
            ("mj-edit-cancel", "Escape, Cancel, focus moving away, or disabled/readonly during an edit.", "{ value: string }"),
            ("mj-invalid", "A commit was rejected by validation, or a form check failed.", "{ validationMessage: string }"),
            ("change", "Native event (no detail) after a successful `mj-change`."),
        ],
        slots=[
            ("display", "Replaces the displayed text (keep it in sync on `mj-change`).", "<strong>Custom display</strong>"),
            ("edit-icon", "Content of the pencil button.", '<span aria-hidden="true">Edit</span>'),
        ],
        properties=[
            ("value", "string. The committed value; setting it updates the display and emits no events."),
            ("editing", "boolean. True while the editor is open (read-only)."),
            ("pendingValue", "string. The text currently in the input (read-only)."),
        ] + _FORM_PROPERTIES,
        methods=[
            ("checkValidity() -> boolean", "Runs the constraints on the committed value."),
            ("reportValidity() -> boolean", "Runs the constraints and shows the error."),
            ("showValidation() -> boolean", "Same as `reportValidity()`."),
            ("focus(options)", "Focuses the open input, otherwise the pencil button."),
        ],
        parts=[
            ("display-wrap", "The display row."),
            ("display-text", "The displayed value."),
            ("edit-trigger", "The pencil button."),
            ("edit-wrap", "The editing row."),
            ("input", "The input or textarea (while editing)."),
            ("actions", "Save / Cancel button row."),
            ("commit-button", "The Save button."),
            ("cancel-button", "The Cancel button."),
            ("error", "Inline error message."),
        ],
        css_properties=[],
    ),
    ComponentDoc(
        tag="mj-masked-input",
        title="Masked Input",
        group="text",
        summary="A text field that formats input against a mask such as (999) 999-9999 as the user types.",
        description=_code("""
            <p><code>&lt;mj-masked-input&gt;</code> constrains typing to a mask: <code>9</code> is a digit,
            <code>a</code> a letter, <code>*</code> a letter or digit, and every other character a literal the
            component inserts itself. It intercepts typing, deleting, cutting and dropping; a paste over the
            whole content accepts formatted text; arrow keys, Home and End jump between editable positions.</p>
            <p><code>mode="eager"</code> (default) shows the literals that follow the last typed character;
            <code>mode="lazy"</code> shows only the typed characters while focused and adds the literals on
            blur. <code>show-mask</code> shows a ghost of the unfilled mask using <code>placeholder-char</code>.</p>
            <p><code>value</code> is the formatted text and <code>rawValue</code> the typed characters; neither
            ever contains placeholder characters. A non-empty but incomplete value is invalid
            (patternMismatch). The <code>value</code> attribute accepts formatted or raw text.</p>
        """),
        how_to_use=_code("""
            <p>Set <code>mask</code>, <code>label</code> and <code>name</code>; add <code>show-mask</code> to
            show the remaining format. Listen for <code>mj-complete</code> when every slot is filled and
            <code>mj-input</code> / <code>mj-change</code> with <code>value</code>, <code>rawValue</code> and
            <code>complete</code>.</p>
        """),
        example="",
        examples=[
            ComponentExample(
                key="basic",
                title="Basic usage",
                description="<p>A US phone number with the mask ghost. Type digits: the brackets, space and dash "
                            "appear by themselves.</p>",
                html=_code("""
                    <mj-masked-input
                      name="phone"
                      label="Phone number"
                      mask="(999) 999-9999"
                      show-mask
                      help-text="Digits only; formatting is added for you.">
                    </mj-masked-input>
                """),
            ),
            ComponentExample(
                key="masks",
                title="Mask characters",
                description="<p>Digits (<code>9</code>), letters (<code>a</code>) and either (<code>*</code>), "
                            "with values given as formatted or raw text.</p>",
                html=_code("""
                    <div class="stack">
                      <mj-masked-input label="Date" mask="99/99/9999" show-mask value="24122026"></mj-masked-input>
                      <mj-masked-input label="Canadian postcode" mask="a9a 9a9" show-mask value="K1A 0B1"></mj-masked-input>
                      <mj-masked-input label="Licence key" mask="****-****-****" show-mask placeholder-char="#"></mj-masked-input>
                      <mj-masked-input label="Card number" mask="9999 9999 9999 9999" placeholder="1234 5678 9012 3456"></mj-masked-input>
                    </div>
                """),
                css=_STACK_CSS,
            ),
            ComponentExample(
                key="modes",
                title="Eager and lazy modes",
                description="<p>Type the same digits in both: eager shows the next literal straight away, lazy "
                            "shows only your digits until you leave the field.</p>",
                html=_code("""
                    <div class="stack">
                      <mj-masked-input label="Eager (default)" mask="999-99-9999" mode="eager" show-mask></mj-masked-input>
                      <mj-masked-input label="Lazy" mask="999-99-9999" mode="lazy" show-mask></mj-masked-input>
                    </div>
                """),
                css=_STACK_CSS,
            ),
            ComponentExample(
                key="states",
                title="Invalid, read-only, disabled, sizes",
                description="<p>An incomplete required date revealed by <code>reportValidity()</code>, read-only "
                            "and disabled fields, and the small and large sizes.</p>",
                html=_code("""
                    <div class="stack">
                      <mj-masked-input id="expiry" label="Card expiry" mask="99/99" value="12" required show-mask
                        error-message="Enter the month and year, e.g. 08/27."></mj-masked-input>
                      <mj-masked-input label="Read-only" mask="(999) 999-9999" value="5551234567" readonly></mj-masked-input>
                      <mj-masked-input label="Disabled" mask="(999) 999-9999" value="5559876543" disabled></mj-masked-input>
                      <mj-masked-input label="Small" mask="99:99" size="sm" show-mask></mj-masked-input>
                      <mj-masked-input label="Large" mask="99:99" size="lg" show-mask></mj-masked-input>
                    </div>
                """),
                css=_STACK_CSS,
                script=_code("""
                    const field = document.getElementById("expiry")
                    mjSandbox.log("reportValidity()", { valid: field.reportValidity(), message: field.validationMessage })
                """),
            ),
            ComponentExample(
                key="slots",
                title="Prefix and suffix",
                description="<p>A country code in <code>prefix</code> and an icon in <code>suffix</code>.</p>",
                html=_code("""
                    <mj-masked-input label="Mobile" mask="999 999 9999" show-mask>
                      <span slot="prefix">+1</span>
                      <svg slot="suffix" viewBox="0 0 16 16" width="16" height="16" aria-hidden="true">
                        <rect x="4" y="1" width="8" height="14" rx="1.5" fill="none" stroke="currentColor" stroke-width="1.5"/>
                      </svg>
                    </mj-masked-input>
                """),
            ),
            ComponentExample(
                key="events",
                title="Typing events in a form",
                description="<p>The script types a phone number one digit at a time: <code>mj-input</code> per "
                            "digit, <code>mj-complete</code> when full. The form submits the formatted value.</p>",
                html=_code("""
                    <form id="demo-form" class="demo-form">
                      <mj-masked-input id="events-mask" name="phone" label="Phone" mask="(999) 999-9999" show-mask required></mj-masked-input>
                      <div class="actions">
                        <button type="submit">Save</button>
                        <button type="reset">Reset</button>
                      </div>
                      <output id="demo-result" class="result">Submit to see the form data.</output>
                    </form>
                """),
                css=_FORM_CSS,
                script=_NATIVE_FORM_SCRIPT + _code("""
                    const field = document.getElementById("events-mask")
                    const input = field.shadowRoot.querySelector("input")
                    input.focus()
                    for (const digit of "5550142233") {
                      input.dispatchEvent(new InputEvent("beforeinput", { inputType: "insertText", data: digit, bubbles: true, composed: true, cancelable: true }))
                    }
                    mjSandbox.log("typed", { value: field.value, rawValue: field.rawValue, complete: field.complete })
                """),
            ),
        ],
        attributes=[
            _attr("mask", "Format: `9` digit, `a` letter, `*` letter or digit, anything else a literal.",
                  values=["(999) 999-9999", "99/99/9999", "a9a 9a9", "****-****"]),
            _attr("label", "Visible label; a `*` is added when required."),
            _attr("value", "Default value as formatted or raw text; re-applied when it changes, restored on form reset."),
            _name_attr(),
            _attr("placeholder", "Input placeholder (not shown with `show-mask`)."),
            _attr("placeholder-char", "Character used for unfilled positions in the mask ghost.", default="_"),
            _attr("mode", "`eager` shows following literals at once; `lazy` only on blur.", kind="enum",
                  values=["eager", "lazy"], default="eager"),
            _attr("show-mask", "Shows the unfilled part of the mask as a ghost.", kind="boolean"),
            _attr("help-text", "Guidance shown below the field."),
            _attr("error-message", "Replaces the text of a real validation error."),
            _required_message_attr(),
            _attr("required", "The field must not be empty.", kind="boolean"),
            _attr("disabled", "Disables the field.", kind="boolean"),
            _attr("readonly", "The value cannot be edited.", kind="boolean"),
            _attr("inputmode", "Virtual keyboard hint; defaults to numeric for all-digit masks.", kind="enum",
                  values=["numeric", "text", "tel"]),
            _attr("autocomplete", "Autocomplete hint.", values=["off", "tel", "cc-number"], default="off"),
            _size_attr(),
            _aria_label_attr(),
        ],
        events=[
            ("mj-input", "A user change altered the value.", "{ value: string, rawValue: string, complete: boolean }"),
            ("mj-complete", "Every mask slot became filled.", "{ value: string, rawValue: string }"),
            ("mj-change", "Blur with a value different from the last commit.", "{ value: string, rawValue: string, complete: boolean }"),
            ("mj-invalid", "On blur while invalid and on every failed check.", "{ validationMessage: string }"),
        ] + _BRIDGED_EVENTS,
        slots=[
            ("prefix", "Content before the input.", "<span>+1</span>"),
            ("suffix", "Content after the input.",
             '<svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><circle cx="8" cy="8" r="5" fill="currentColor"/></svg>'),
        ],
        properties=[
            ("value", "string. Formatted value without placeholder characters; accepts formatted or raw text; emits no events."),
            ("rawValue", "string. Only the typed characters (read-only)."),
            ("complete", "boolean. Every slot is filled (read-only)."),
        ] + _FORM_PROPERTIES,
        methods=_FORM_METHODS,
        parts=[
            ("label", "The label."),
            ("field", "The bordered box."),
            ("prefix", "Wrapper of the prefix slot."),
            ("mask-overlay", "The mask ghost."),
            ("input", "The native input."),
            ("suffix", "Wrapper of the suffix slot."),
            ("help", "Help text."),
            ("error", "Inline error message."),
        ],
        css_properties=[],
    ),
    ComponentDoc(
        tag="mj-token-input",
        title="Token Input",
        group="text",
        summary="Free-form multi-value entry: text becomes removable chips on Enter or a delimiter, with optional suggestions.",
        description=_code("""
            <p><code>&lt;mj-token-input&gt;</code> turns typed text into chips. Enter, Tab or a delimiter
            (<code>,</code> by default) commits the text; pasting text with delimiters or newlines creates several
            tokens; by default leftover text is committed on blur (<code>commit-on-blur="false"</code> to stop).
            Backspace or ArrowLeft in the empty input moves into the chips; arrows move between chips and
            Delete/Backspace removes one.</p>
            <p>Suggestions are not filtered by the component: listen for the debounced
            <code>mj-query-change</code> and assign <code>suggestions</code>. <code>constrained</code> only accepts
            values from the current suggestions; <code>validateToken</code> can reject a value with a message
            (the text stays in the input). <code>max-tokens</code> hides the input at the limit; duplicates are
            refused unless <code>allow-duplicates</code>.</p>
            <p>Each token is submitted as its own FormData entry under <code>name</code>. The <code>value</code>
            attribute (comma-separated) gives the initial tokens and is restored on reset; the
            <code>value</code> property is the comma-joined list and <code>tokens</code> the array.</p>
        """),
        how_to_use=_code("""
            <p>Set <code>name</code>, <code>label</code> and initial tokens in <code>value</code>. Use
            <code>required</code> for at least one token. Listen for <code>mj-token-add</code> /
            <code>mj-token-remove</code> (both cancelable) and <code>mj-change</code> with the new
            <code>tokens</code>.</p>
        """),
        example="",
        examples=[
            ComponentExample(
                key="basic",
                title="Basic usage",
                description="<p>Two initial tokens. Type a skill and press Enter or a comma; Backspace in the "
                            "empty input moves to the last chip, Delete removes it.</p>",
                html=_code("""
                    <mj-token-input
                      name="skills"
                      label="Skills"
                      value="Design, Research"
                      placeholder="Add a skill and press Enter"
                      help-text="Separate skills with Enter or a comma.">
                    </mj-token-input>
                """),
            ),
            ComponentExample(
                key="suggestions",
                title="Suggestions, constrained",
                description="<p>The script answers <code>mj-query-change</code> with matching languages; "
                            "<code>constrained</code> only accepts values from the list. Type <code>ja</code>.</p>",
                html=_code("""
                    <mj-token-input id="language-tokens" label="Languages" constrained debounce="150"
                      placeholder="Type a language" value="Python"></mj-token-input>
                """),
                script=_code("""
                    const tokens = document.getElementById("language-tokens")
                    const languages = ["Go", "Java", "JavaScript", "Kotlin", "Python", "Rust", "Swift", "TypeScript"]
                    tokens.addEventListener("mj-query-change", (event) => {
                      const query = event.detail.value.toLowerCase()
                      tokens.suggestions = query === "" ? [] : languages.filter((name) => name.toLowerCase().includes(query))
                    })
                """),
                height=360,
            ),
            ComponentExample(
                key="validation",
                title="Validation and limits",
                description="<p>Emails only (<code>validateToken</code>; try <code>bob</code>), at most three "
                            "recipients (<code>max-tokens</code>), and a required field revealed by "
                            "<code>reportValidity()</code>.</p>",
                html=_code("""
                    <div class="stack">
                      <mj-token-input id="email-tokens" label="Invite (max 3)" max-tokens="3" value="ana@example.com"
                        placeholder="name@example.com"></mj-token-input>
                      <mj-token-input id="required-tokens" label="Labels" required
                        required-message="Add at least one label."></mj-token-input>
                      <mj-token-input label="Duplicates allowed" allow-duplicates value="red, red, blue"></mj-token-input>
                    </div>
                """),
                css=_STACK_CSS,
                script=_code("""
                    const emails = document.getElementById("email-tokens")
                    emails.validateToken = (value) => /^[^@\\s]+@[^@\\s]+\\.[a-z]{2,}$/i.test(value) || "Enter a valid email address."
                    const labels = document.getElementById("required-tokens")
                    mjSandbox.log("reportValidity()", { valid: labels.reportValidity(), message: labels.validationMessage })
                """),
            ),
            ComponentExample(
                key="states",
                title="Read-only, disabled, custom delimiters",
                description="<p>Read-only chips (no remove controls), a disabled field, and "
                            "<code>delimiters=\";\"</code>.</p>",
                html=_code("""
                    <div class="stack">
                      <mj-token-input label="Read-only" readonly value="alpha, beta, gamma"></mj-token-input>
                      <mj-token-input label="Disabled" disabled value="locked"></mj-token-input>
                      <mj-token-input label="Semicolon separated" delimiters=";" placeholder="one; two; three"></mj-token-input>
                    </div>
                """),
                css=_STACK_CSS,
            ),
            ComponentExample(
                key="form",
                title="In a form",
                description="<p>Each token is its own FormData entry under <code>name</code>. Submit shows the "
                            "entries; Reset restores the tokens from the <code>value</code> attribute.</p>",
                html=_code("""
                    <form id="demo-form" class="demo-form">
                      <mj-token-input name="tag" label="Tags" value="release, docs" required></mj-token-input>
                      <div class="actions">
                        <button type="submit">Save</button>
                        <button type="reset">Reset</button>
                      </div>
                      <output id="demo-result" class="result">Submit to see the form data.</output>
                    </form>
                """),
                css=_FORM_CSS,
                script=_NATIVE_FORM_SCRIPT,
            ),
            ComponentExample(
                key="events",
                title="Events",
                description="<p>The script types tokens followed by a comma (<code>mj-token-add</code>, "
                            "<code>mj-change</code>), has a listener cancel the token <code>spam</code>, and "
                            "removes a chip (<code>mj-token-remove</code>).</p>",
                html=_code("""
                    <mj-token-input id="events-tokens" label="Topics" value="news"></mj-token-input>
                """),
                script=_code("""
                    const field = document.getElementById("events-tokens")
                    field.addEventListener("mj-token-add", (event) => {
                      if (event.detail.value === "spam") {
                        event.preventDefault()
                        mjSandbox.log("token refused", { value: event.detail.value })
                      }
                    })
                    const input = field.shadowRoot.querySelector("input")
                    input.focus()
                    for (const text of ["sports,", "spam,", "science,"]) {
                      input.value = text
                      input.dispatchEvent(new InputEvent("input", { bubbles: true, composed: true }))
                    }
                    input.value = ""
                    field.shadowRoot.querySelector(".chip-remove").click()
                    mjSandbox.log("tokens", { tokens: field.tokens, value: field.value })
                """),
            ),
        ],
        attributes=[
            _attr("label", "Visible label; a `*` is added when required."),
            _attr("value", "Comma-separated initial tokens; re-applied when it changes, restored on form reset.",
                  values=["Design, Research", "red, green, blue"]),
            _attr("name", "Form entry name; each token is submitted as a separate entry. Without it nothing is submitted."),
            _attr("placeholder", "Hint shown in the empty input."),
            _attr("help-text", "Guidance shown below the field."),
            _attr("error-message", "Replaces the constraint message (not a `validateToken` rejection)."),
            _required_message_attr(),
            _attr("delimiters", "Characters that commit the typed text; pasted newlines always split.", values=[",", ";", ", "], default=","),
            _attr("max-tokens", "Maximum number of tokens; the input hides at the limit.", kind="number"),
            _attr("allow-duplicates", "Accepts the same token more than once.", kind="boolean"),
            _attr("required", "At least one token is needed.", kind="boolean"),
            _attr("disabled", "Disables the field.", kind="boolean"),
            _attr("readonly", "Hides the input and the remove controls.", kind="boolean"),
            _attr("trim", "`false` keeps surrounding whitespace.", kind="boolean", default="true"),
            _attr("loading", "Shows a loading message in the suggestion popup.", kind="boolean"),
            _attr("debounce", "Milliseconds before `mj-query-change`.", kind="number", default="300"),
            _attr("min-chars", "Minimum query length for `mj-query-change`.", kind="number", default="1"),
            _attr("constrained", "Only values present in the current `suggestions` are accepted.", kind="boolean"),
            _attr("commit-on-blur", "`false` keeps leftover text in the input on blur instead of committing it.",
                  kind="boolean", default="true"),
            _aria_label_attr(),
        ],
        events=[
            ("mj-token-add", "Cancelable. A token is about to be added; `tokens` is the list before the add.",
             "{ value: string, tokens: string[] }"),
            ("mj-token-remove", "Cancelable. A token is about to be removed; `tokens` is the list before the removal.",
             "{ value: string, tokens: string[] }"),
            ("mj-change", "After each add or remove.", "{ tokens: string[] }"),
            ("mj-input", "Every keystroke in the input.", "{ value: string }"),
            ("mj-query-change", "Debounced query for suggestions; once with an empty value when cleared.", "{ value: string }"),
            ("mj-suggestion-select", "A suggestion was picked.", "{ suggestion: string | number | object }"),
            ("mj-invalid", "A token was rejected (`validateToken`, `constrained`) or the required check failed.",
             "{ validationMessage: string, value?: string }"),
        ] + _BRIDGED_EVENTS,
        slots=[],
        properties=[
            ("tokens", "string[]. A copy of the tokens; setting an array replaces them (a non-array clears them)."),
            ("value", "string. The tokens joined with commas; accepts an array or a comma string."),
            ("suggestions", "Array of string | number | { value, label? }. Assign on `mj-query-change`; not filtered by the component."),
            ("validateToken", "(value: string) => true | string. Return true to accept, a message to reject."),
        ] + _FORM_PROPERTIES,
        methods=[
            ("checkValidity() -> boolean", "Refreshes and runs the constraints."),
            ("reportValidity() -> boolean", "Like `checkValidity()`, and shows the error."),
            ("focus(options)", "Focuses the input (the last chip when the input is hidden)."),
        ],
        parts=[
            ("label", "The label."),
            ("container", "The bordered box."),
            ("tokens", "The chip list (`role=listbox`)."),
            ("token", "One chip."),
            ("token-label", "Text of a chip."),
            ("token-remove", "The \u00d7 remove control of a chip: a pointer affordance hidden from assistive technology (an option may not contain a button); keyboard users press Delete / Backspace on the focused chip."),
            ("input", "The text input."),
            ("popup", "The suggestion listbox."),
            ("option", "One suggestion."),
            ("loading", "The loading message."),
            ("help", "Help text."),
            ("error", "Inline error message."),
        ],
        css_properties=[],
    ),
    ComponentDoc(
        tag="mj-otp-input",
        title="OTP Input",
        group="text",
        summary="Segmented one-time-code entry with auto-advance, paste and autofill distribution, and a completion event.",
        description=_code("""
            <p><code>&lt;mj-otp-input&gt;</code> renders <code>length</code> one-character inputs (6 by default, up
            to 12) in a labelled group. Typing advances to the next segment; Backspace clears and moves back;
            arrow keys, Home and End move between segments. A pasted or autofilled code is filtered and spread
            across the segments, so <code>autocomplete="one-time-code"</code> works.</p>
            <p><code>inputtype="numeric"</code> (default) and <code>password</code> accept digits only (password
            masks them); <code>alphanumeric</code> accepts A-Z and 0-9 and upper-cases letters. Other characters
            are refused whether typed or pasted. <code>group-at</code> inserts a separator (the
            <code>separator</code> slot) before that segment index.</p>
            <p><code>mj-complete</code> fires each time the code becomes complete; <code>mj-change</code> fires on a
            completed change and when focus leaves the group with a changed code. A required code is invalid
            while empty or partial; the error shows after focus leaves or a failed check.</p>
        """),
        how_to_use=_code("""
            <p>Set <code>length</code>, <code>inputtype</code>, <code>label</code> and <code>name</code>. Verify
            the code on <code>mj-complete</code> (or submit the form). Read <code>value</code> and
            <code>complete</code>; call <code>focus()</code> to put the caret in the first empty segment.</p>
        """),
        example="",
        examples=[
            ComponentExample(
                key="basic",
                title="Basic usage",
                description="<p>A six-digit code. Type or paste <code>123456</code>; <code>mj-complete</code> "
                            "fires when the last digit is entered.</p>",
                html=_code("""
                    <mj-otp-input
                      name="code"
                      label="Verification code"
                      length="6"
                      help-text="We sent a 6-digit code to your phone.">
                    </mj-otp-input>
                """),
            ),
            ComponentExample(
                key="variants",
                title="Types, grouping and sizes",
                description="<p>An 8-character alphanumeric code grouped 4 + 4, a masked PIN, and the small and "
                            "large sizes.</p>",
                html=_code("""
                    <div class="stack">
                      <mj-otp-input label="Recovery code" inputtype="alphanumeric" length="8" group-at="4"></mj-otp-input>
                      <mj-otp-input label="PIN" inputtype="password" length="4"></mj-otp-input>
                      <mj-otp-input label="Small" length="4" size="sm" value="1234"></mj-otp-input>
                      <mj-otp-input label="Large" length="4" size="lg" value="5678"></mj-otp-input>
                    </div>
                """),
                css=_STACK_CSS,
            ),
            ComponentExample(
                key="states",
                title="Invalid, read-only, disabled",
                description="<p>A required partial code revealed by <code>reportValidity()</code>, a read-only "
                            "code and a disabled one.</p>",
                html=_code("""
                    <div class="stack">
                      <mj-otp-input id="partial-code" label="Code" required value="12" error-message="Enter all six digits."></mj-otp-input>
                      <mj-otp-input label="Read-only" readonly value="482913"></mj-otp-input>
                      <mj-otp-input label="Disabled" disabled value="000000"></mj-otp-input>
                    </div>
                """),
                css=_STACK_CSS,
                script=_code("""
                    const field = document.getElementById("partial-code")
                    mjSandbox.log("reportValidity()", { valid: field.reportValidity(), message: field.validationMessage })
                """),
            ),
            ComponentExample(
                key="slots",
                title="Separator slot",
                description="<p><code>group-at=\"3\"</code> with a custom <code>separator</code>.</p>",
                html=_code("""
                    <mj-otp-input label="Authenticator code" length="6" group-at="3">
                      <span slot="separator" aria-hidden="true">&middot;</span>
                    </mj-otp-input>
                """),
            ),
            ComponentExample(
                key="events",
                title="Typing, completion and a form",
                description="<p>The script types a code digit by digit (<code>mj-input</code>, then "
                            "<code>mj-complete</code> and <code>mj-change</code>); the form submits it under "
                            "<code>name</code>, Reset clears it.</p>",
                html=_code("""
                    <form id="demo-form" class="demo-form">
                      <mj-otp-input id="events-otp" name="otp" label="Sign-in code" required></mj-otp-input>
                      <div class="actions">
                        <button type="submit">Verify</button>
                        <button type="reset">Reset</button>
                      </div>
                      <output id="demo-result" class="result">Submit to see the form data.</output>
                    </form>
                """),
                css=_FORM_CSS,
                script=_NATIVE_FORM_SCRIPT + _code("""
                    const otp = document.getElementById("events-otp")
                    const segments = otp.shadowRoot.querySelectorAll("[part='segment']")
                    Array.from("731905").forEach((digit, index) => {
                      const segment = segments[index]
                      segment.focus()
                      segment.value = digit
                      segment.dispatchEvent(new InputEvent("input", { inputType: "insertText", data: digit, bubbles: true, composed: true }))
                    })
                    mjSandbox.log("typed", { value: otp.value, complete: otp.complete })
                """),
            ),
        ],
        attributes=[
            _attr("label", "Visible label; names the group. A `*` is added when required."),
            _attr("value", "Default code; re-applied when it changes, restored on form reset."),
            _name_attr(),
            _attr("length", "Number of segments (1-12).", kind="number", default="6"),
            _attr("inputtype", "Accepted characters; `password` masks digits.", kind="enum",
                  values=["numeric", "alphanumeric", "password"], default="numeric"),
            _attr("group-at", "Inserts the separator before this segment index (0 = none).", kind="number", default="0"),
            _attr("help-text", "Guidance shown below the segments."),
            _attr("error-message", "Replaces the text of a real validation error."),
            _required_message_attr(),
            _attr("required", "The code must be complete (empty: valueMissing; partial: incomplete error).", kind="boolean"),
            _attr("disabled", "Disables every segment.", kind="boolean"),
            _attr("readonly", "Segments cannot be changed.", kind="boolean"),
            _attr("autocomplete", "Autocomplete hint on each segment.", values=["one-time-code", "off"], default="one-time-code"),
            _size_attr(),
            _aria_label_attr(),
        ],
        events=[
            ("mj-input", "Every user change (type, paste, autofill, delete).", "{ value: string, complete: boolean }"),
            ("mj-complete", "The code became complete (re-arms when it becomes incomplete).", "{ value: string }"),
            ("mj-change", "A completed code changed, or focus left the group with a changed code.", "{ value: string }"),
            ("mj-invalid", "Focus left the group, or a form check failed, while invalid.", "{ validationMessage: string }"),
        ] + _BRIDGED_EVENTS,
        slots=[
            ("separator", "Separator content shown at `group-at` (default an en dash).", '<span aria-hidden="true">&middot;</span>'),
        ],
        properties=[
            ("value", "string. The code; setting it fits it to the length and emits no events."),
            ("complete", "boolean. Every segment is filled (read-only)."),
        ] + _FORM_PROPERTIES,
        methods=[
            ("checkValidity() -> boolean", "Runs the constraints."),
            ("reportValidity() -> boolean", "Runs the constraints and shows the error."),
            ("focus(options)", "Focuses the first empty segment (the first one when the code is full)."),
        ],
        parts=[
            ("label", "The label."),
            ("group", "The segment group."),
            ("segment", "One input segment."),
            ("separator", "The separator."),
            ("help", "Help text."),
            ("error", "Inline error message."),
        ],
        css_properties=[],
    ),
    ComponentDoc(
        tag="mj-slider",
        title="Slider",
        group="text",
        summary="Single or dual-thumb range slider with keyboard control, ticks, value bubbles and vertical orientation.",
        description=_code("""
            <p><code>&lt;mj-slider&gt;</code> picks a number between <code>min</code> and <code>max</code> on a
            track. Each thumb is a <code>role="slider"</code> with arrow keys (one step), PageUp/PageDown (ten
            steps) and Home/End. <code>range</code> adds a second thumb for <code>value-end</code>; the thumbs
            cannot cross with the keyboard and swap roles when dragged past each other.</p>
            <p><code>ticks</code> draws a dot per step (up to 50); <code>show-value-label</code> shows a bubble
            while dragging and on keyboard focus; <code>orientation="vertical"</code> stands the slider up (its
            length is <code>--mj-slider-length</code>, minimum at the bottom). The <code>start-label</code> /
            <code>end-label</code> slots label the track ends.</p>
            <p>A single slider submits <code>name=value</code>. In range mode it submits
            <code>name-start</code> and <code>name-end</code> entries, or <code>name="a,b"</code> when only
            <code>name</code> is set. The value is never empty, so <code>required</code> means "moved off the
            default position": the slider is invalid (valueMissing) while the value equals <code>min</code>, and
            in range mode while the range still spans <code>min</code>..<code>max</code>. The inline error
            (text from <code>error-message</code> when set) and <code>mj-invalid</code> appear once focus leaves
            the slider or a check or submit fails.</p>
            <p>The <code>tickLabels</code> property (<code>[{ value, label }]</code>) writes text labels under
            the track; a thumb resting on a labelled value announces that label as its value text.</p>
        """),
        how_to_use=_code("""
            <p>Set <code>min</code>, <code>max</code>, <code>step</code> and <code>value</code> (and
            <code>value-end</code> with <code>range</code>). Listen for <code>mj-input</code> while dragging and
            <code>mj-change</code> on release or key press; read <code>valueAsNumber</code>,
            <code>valueStartAsNumber</code> and <code>valueEndAsNumber</code>.</p>
        """),
        example="",
        examples=[
            ComponentExample(
                key="basic",
                title="Basic usage",
                description="<p>A volume slider with end labels and a value bubble. Drag, or focus a thumb and "
                            "use the arrow keys.</p>",
                html=_code("""
                    <mj-slider name="volume" label="Volume" min="0" max="100" value="40" show-value-label
                      help-text="Arrow keys move by 1, Page Up/Down by 10.">
                      <span slot="start-label">Quiet</span>
                      <span slot="end-label">Loud</span>
                    </mj-slider>
                """),
            ),
            ComponentExample(
                key="range",
                title="Range (two thumbs)",
                description="<p>A price range from 200 to 800 in steps of 50, with ticks and value bubbles.</p>",
                html=_code("""
                    <mj-slider label="Price range" range min="0" max="1000" step="50" value="200" value-end="800"
                      ticks show-value-label name-start="price-min" name-end="price-max">
                      <span slot="start-label">$0</span>
                      <span slot="end-label">$1000</span>
                    </mj-slider>
                """),
            ),
            ComponentExample(
                key="vertical",
                title="Vertical and fractional steps",
                description="<p>A vertical slider 10rem long, and a horizontal one stepping by 0.5.</p>",
                html=_code("""
                    <div class="row">
                      <mj-slider label="Level" orientation="vertical" min="0" max="10" value="7" show-value-label></mj-slider>
                      <mj-slider label="Rating (0.5 steps)" min="0" max="5" step="0.5" value="3.5" ticks show-value-label></mj-slider>
                    </div>
                """),
                css=_code("""
                    .row { display: flex; gap: var(--mj-space-8); align-items: center; }
                    mj-slider[orientation="vertical"] { --mj-slider-length: 10rem; }
                    .row > mj-slider:last-child { flex: 1; }
                """),
            ),
            ComponentExample(
                key="states",
                title="Disabled, read-only and required",
                description="<p>Disabled thumbs leave the tab order; read-only thumbs stay focusable but do not "
                            "move. The required slider still sits on <code>min</code>: the script calls "
                            "<code>checkValidity()</code>, which shows the <code>error-message</code> text and "
                            "fires <code>mj-invalid</code>; move the thumb and the error goes away.</p>",
                html=_code("""
                    <div class="stack">
                      <mj-slider label="Disabled" value="30" disabled></mj-slider>
                      <mj-slider label="Read-only" value="60" readonly></mj-slider>
                      <mj-slider id="required-slider" label="Satisfaction (required)" min="0" max="10" required
                        error-message="Move the slider to rate your visit."></mj-slider>
                    </div>
                """),
                css=_STACK_CSS,
                script=_code("""
                    const slider = document.getElementById("required-slider")
                    mjSandbox.log("checkValidity", { valid: slider.checkValidity(), message: slider.validationMessage })
                """),
            ),
            ComponentExample(
                key="tick-labels",
                title="Tick labels",
                description="<p><code>tickLabels</code> names three positions of a 1-5 scale. The labels sit under "
                            "the track, and a thumb on a labelled value announces the label (its "
                            "<code>aria-valuetext</code>) instead of the number.</p>",
                html=_code("""
                    <mj-slider id="effort-slider" label="Effort" min="1" max="5" value="3" ticks show-value-label></mj-slider>
                """),
                script=_code("""
                    const slider = document.getElementById("effort-slider")
                    slider.tickLabels = [
                      { value: 1, label: "Trivial" },
                      { value: 3, label: "Moderate" },
                      { value: 5, label: "Huge" },
                    ]
                """),
            ),
            ComponentExample(
                key="form",
                title="Filters form",
                description="<p>A single and a range slider in a native form. Submit shows the entries "
                            "(<code>price-min</code> / <code>price-max</code> from the range), Reset restores the "
                            "attributes.</p>",
                html=_code("""
                    <form id="demo-form" class="demo-form">
                      <mj-slider name="distance" label="Max distance (km)" min="1" max="50" value="10" show-value-label></mj-slider>
                      <mj-slider label="Price" range min="0" max="500" step="10" value="50" value-end="300"
                        name-start="price-min" name-end="price-max" show-value-label></mj-slider>
                      <div class="actions">
                        <button type="submit">Apply filters</button>
                        <button type="reset">Reset</button>
                      </div>
                      <output id="demo-result" class="result">Submit to see the form data.</output>
                    </form>
                """),
                css=_FORM_CSS,
                script=_NATIVE_FORM_SCRIPT,
            ),
            ComponentExample(
                key="events",
                title="Keyboard events",
                description="<p>The script presses ArrowRight and PageDown on the first thumb and ArrowLeft and "
                            "End on the second thumb of a range slider (<code>mj-input</code> and "
                            "<code>mj-change</code> each time) and logs the numeric values.</p>",
                html=_code("""
                    <mj-slider id="events-slider" label="Working hours" range min="0" max="24" value="9" value-end="17" show-value-label></mj-slider>
                """),
                script=_code("""
                    const slider = document.getElementById("events-slider")
                    const press = (part, key) => {
                      const thumb = slider.shadowRoot.querySelector(`[part~='${part}']`)
                      thumb.focus()
                      thumb.dispatchEvent(new KeyboardEvent("keydown", { key, bubbles: true, composed: true, cancelable: true }))
                      mjSandbox.log(part + " " + key, { start: slider.valueStartAsNumber, end: slider.valueEndAsNumber })
                    }
                    press("thumb-a", "ArrowRight")
                    press("thumb-a", "PageDown")
                    press("thumb-b", "ArrowLeft")
                    press("thumb-b", "End")
                """),
            ),
        ],
        attributes=[
            _attr("label", "Visible label; clicking it focuses the first thumb."),
            _attr("value", "Value (lower value in range mode); restored on form reset.", kind="number"),
            _attr("value-end", "Upper value in range mode (defaults to `max`).", kind="number"),
            _attr("min", "Lower bound.", kind="number", default="0"),
            _attr("max", "Upper bound.", kind="number", default="100"),
            _attr("step", "Step size (must be greater than 0).", kind="number", default="1"),
            _attr("range", "Two thumbs: `value` to `value-end`.", kind="boolean"),
            _attr("orientation", "Absent is horizontal; `vertical` puts the minimum at the bottom and hides the end labels.",
                  kind="enum", values=["vertical"]),
            _attr("ticks", "Draws a dot per step (skipped above 50 steps).", kind="boolean"),
            _attr("show-value-label", "Shows a value bubble while dragging and on keyboard focus.", kind="boolean"),
            _attr("name", "Form entry name; in range mode it submits `a,b` unless `name-start` / `name-end` are set."),
            _attr("name-start", "Range mode: entry name of the lower value."),
            _attr("name-end", "Range mode: entry name of the upper value."),
            _attr("help-text", "Guidance shown below the slider."),
            _attr("required", "The value must be moved off `min` (range mode: the range must not span min..max).",
                  kind="boolean"),
            _attr("error-message", "Replaces the text of a real validation error."),
            _required_message_attr(),
            _attr("disabled", "Disables the slider.", kind="boolean"),
            _attr("readonly", "Thumbs stay focusable but cannot move.", kind="boolean"),
            _aria_label_attr(),
        ],
        events=[
            ("mj-input", "Each change while dragging or from a key press.", "{ value: number, valueEnd: number | undefined }"),
            ("mj-change", "Release after a drag that changed the value, and every key press that changed it.",
             "{ value: number, valueEnd: number | undefined }"),
            ("mj-invalid", "Focus left an invalid slider, or a check / submit failed.", "{ validationMessage: string }"),
        ] + _BRIDGED_EVENTS,
        slots=[
            ("start-label", "Label under the start of the track.", "<span>Min</span>"),
            ("end-label", "Label under the end of the track.", "<span>Max</span>"),
        ],
        properties=[
            ("value", "string. The (lower) value; setting it emits no events."),
            ("valueEnd", "string. The upper value in range mode."),
            ("valueAsNumber", "number. The (lower) value as a number; settable."),
            ("valueStartAsNumber", "number. The lower value (read-only)."),
            ("valueEndAsNumber", "number. The upper value (read-only)."),
            ("tickLabels", "Array<{ value: number, label: string }>. Text labels under the track (values outside min..max are skipped); also the value text of a thumb on that value."),
        ] + _FORM_PROPERTIES,
        methods=[
            ("focus(options)", "Focuses the first thumb."),
            ("checkValidity() -> boolean", "Runs the `required` check; fires `invalid` when it fails."),
            ("reportValidity() -> boolean", "Like `checkValidity()`, and shows the inline error."),
        ],
        parts=[
            ("label", "The label."),
            ("slider-wrap", "The area around the track."),
            ("track", "The track."),
            ("fill", "The filled segment."),
            ("ticks", "The tick row."),
            ("thumb", "Both thumbs (also `thumb-a` / `thumb-b`)."),
            ("thumb-a", "The first thumb."),
            ("thumb-b", "The second thumb (range mode)."),
            ("value-label", "A thumb's value bubble."),
            ("tick-labels", "The row of `tickLabels` text."),
            ("tick-label", "One tick label."),
            ("help", "Help text."),
            ("error", "Inline error message."),
        ],
        css_properties=[
            ("--mj-slider-track-height", "Track thickness (default 4px)."),
            ("--mj-slider-thumb-size", "Thumb diameter (default 20px)."),
            ("--mj-slider-tick-size", "Tick dot size (default 4px)."),
            ("--mj-slider-length", "Length of a vertical slider (default 200px)."),
        ],
    ),
    ComponentDoc(
        tag="mj-rating",
        title="Rating",
        group="text",
        summary="A star rating (or hearts, circles, diamonds) built as a radio group, with half steps and a value label.",
        description=_code("""
            <p><code>&lt;mj-rating&gt;</code> is a radio group of <code>max</code> icons (5 by default, up to 10).
            <code>icon</code> chooses stars, hearts, circles or diamonds; <code>icon-color</code> takes a token
            name such as <code>danger</code>, a custom property (<code>--brand</code>) or any CSS colour.
            <code>half-steps</code> splits each icon into two halves.</p>
            <p>It is a single tab stop: arrow keys change the rating, Home/End go to the first step and
            <code>max</code>, Delete/Backspace clear it (not when required); clicking the current rating clears
            it too. Hovering previews a value (<code>mj-hover</code>). <code>mj-change</code> fires after the
            rating updates and is cancelable: <code>preventDefault()</code> restores the previous rating.</p>
            <p>The <code>value</code> attribute is the default rating; it is submitted from the first render and
            restored on reset, but never rewritten by clicks: read the <code>value</code> property for the
            current rating. A required rating of 0 is invalid.</p>
        """),
        how_to_use=_code("""
            <p>Set <code>name</code>, <code>label</code>, <code>max</code> and the default <code>value</code>. Use
            <code>readonly</code> to display an average (it gets an aria-label like '4 out of 5 stars') and
            <code>value-label-format</code> for the visible label.</p>
        """),
        example="",
        examples=[
            ComponentExample(
                key="basic",
                title="Basic usage",
                description="<p>Click a star or use the arrow keys; click the current star again to clear it.</p>",
                html=_code("""
                    <mj-rating name="score" label="Your rating" value="3" show-value-label
                      help-text="Arrow keys change it; Delete clears it.">
                    </mj-rating>
                """),
            ),
            ComponentExample(
                key="icons",
                title="Icons, colours and sizes",
                description="<p>Hearts in the danger colour, circles with a custom property, diamonds in a CSS "
                            "colour, ten small stars and large stars.</p>",
                html=_code("""
                    <div class="stack">
                      <mj-rating label="Love it?" icon="heart" icon-color="danger" value="4"></mj-rating>
                      <mj-rating label="Difficulty" icon="circle" icon-color="--brand" value="2"></mj-rating>
                      <mj-rating label="Quality" icon="diamond" icon-color="#0e7490" value="5"></mj-rating>
                      <mj-rating label="Out of ten" max="10" size="sm" value="7" show-value-label></mj-rating>
                      <mj-rating label="Large" size="lg" value="4"></mj-rating>
                    </div>
                """),
                css=_STACK_CSS + _code("""
                    :root { --brand: var(--mj-accent); }
                """),
            ),
            ComponentExample(
                key="states",
                title="Half steps, read-only, disabled, required",
                description="<p>Half-star input, a read-only average with a custom label format, a disabled "
                            "rating, and a required rating with no value revealed by "
                            "<code>reportValidity()</code>.</p>",
                html=_code("""
                    <div class="stack">
                      <mj-rating label="Half steps" half-steps value="3.5" show-value-label></mj-rating>
                      <mj-rating label="Average" readonly value="4.3" show-value-label value-label-format="{value} / {max} (128 reviews)"></mj-rating>
                      <mj-rating label="Disabled" disabled value="2"></mj-rating>
                      <mj-rating id="required-rating" label="Rate your stay" required error-message="Please pick a rating."></mj-rating>
                    </div>
                """),
                css=_STACK_CSS,
                script=_code("""
                    const rating = document.getElementById("required-rating")
                    mjSandbox.log("reportValidity()", { valid: rating.reportValidity(), message: rating.validationMessage })
                """),
            ),
            ComponentExample(
                key="form",
                title="Review form",
                description="<p>A required rating in a native form: an unrated submit is blocked; Submit shows "
                            "the entries; Reset restores the default rating.</p>",
                html=_code("""
                    <form id="demo-form" class="demo-form">
                      <mj-rating name="stars" label="Overall" required></mj-rating>
                      <mj-rating name="value-for-money" label="Value for money" value="3"></mj-rating>
                      <div class="actions">
                        <button type="submit">Submit review</button>
                        <button type="reset">Reset</button>
                      </div>
                      <output id="demo-result" class="result">Submit to see the form data.</output>
                    </form>
                """),
                css=_FORM_CSS,
                script=_NATIVE_FORM_SCRIPT,
            ),
            ComponentExample(
                key="events",
                title="Cancelable change",
                description="<p>A listener refuses ratings below 2 by cancelling <code>mj-change</code>. The script "
                            "clicks 4 stars, then 1 star (refused), then presses ArrowLeft.</p>",
                html=_code("""
                    <mj-rating id="events-rating" label="Recommend us?" value="3" show-value-label></mj-rating>
                """),
                script=_code("""
                    const rating = document.getElementById("events-rating")
                    rating.addEventListener("mj-change", (event) => {
                      if (event.detail.value < 2) {
                        event.preventDefault()
                        mjSandbox.log("refused", { tried: event.detail.value, kept: event.detail.previousValue })
                      }
                    })
                    const item = (value) => rating.shadowRoot.querySelector(`[role='radio'][data-value='${value}']`)
                    item(4).click()
                    item(1).click()
                    item(4).dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowLeft", bubbles: true, composed: true, cancelable: true }))
                    mjSandbox.log("current", { value: rating.value, attribute: rating.getAttribute("value") })
                """),
            ),
        ],
        attributes=[
            _attr("label", "Visible label; names the radio group. A `*` is added when required."),
            _attr("value", "Default rating (0 to max); submitted from the first render, restored on reset, never rewritten.", kind="number", default="0"),
            _name_attr(),
            _attr("max", "Number of icons (1-10).", kind="number", default="5"),
            _attr("half-steps", "Allows half values (two radios per icon).", kind="boolean"),
            _attr("icon", "Icon shape.", kind="enum", values=["star", "heart", "circle", "diamond"], default="star"),
            _attr("icon-color", "Filled colour: a token name (`danger`), a custom property (`--brand`) or a CSS colour.",
                  values=["danger", "success", "accent", "--brand", "#0e7490"]),
            _attr("show-value-label", "Shows the value label next to the icons.", kind="boolean"),
            _attr("value-label-format", "Label format with `{value}` and `{max}` tokens.", values=["{value} out of {max}", "{value}/{max}"],
                  default="{value} out of {max}"),
            _attr("help-text", "Guidance shown below the rating."),
            _attr("error-message", "Replaces the text of a real validation error."),
            _required_message_attr(),
            _attr("required", "A rating of 0 is invalid; clearing is not allowed.", kind="boolean"),
            _attr("disabled", "No interaction, no tab stop.", kind="boolean"),
            _attr("readonly", "Display only (no tab stop); the group is labelled with the value.", kind="boolean"),
            _size_attr(),
            _aria_label_attr(),
        ],
        events=[
            ("mj-change", "Cancelable. The user changed the rating; it is already applied, cancelling restores the previous one.",
             "{ value: number, previousValue: number }"),
            ("mj-hover", "The pointer moved over a new value (mouse and pen only).", "{ hoverValue: number }"),
            ("mj-invalid", "Focus left the group, or a form check failed, while invalid.", "{ validationMessage: string }"),
            ("change", "Native event (no detail) after each `mj-change`."),
        ],
        slots=[],
        properties=[
            ("value", "string. The current rating, e.g. `3.5`; setting it clamps and emits no events."),
            ("valueAsNumber", "number. The current rating as a number; settable."),
        ] + _FORM_PROPERTIES,
        methods=[
            ("checkValidity() -> boolean", "Runs the required check."),
            ("reportValidity() -> boolean", "Runs it and shows the error."),
            ("focus(options)", "Focuses the radio that holds the tab stop."),
        ],
        parts=[
            ("label", "The label."),
            ("group", "The radio group."),
            ("item", "One radio (two per icon with half steps)."),
            ("star", "One icon cell."),
            ("icon-empty", "The empty glyph."),
            ("icon-filled", "The filled glyph."),
            ("value-label", "The value label."),
            ("help", "Help text."),
            ("error", "Inline error message."),
        ],
        css_properties=[
            ("--mj-rating-icon-size", "Icon size (default 1.5rem; sm 1.25rem, lg 2rem)."),
            ("--mj-rating-icon-gap", "Gap between icons (default var(--mj-space-1))."),
            ("--mj-rating-icon-color-empty", "Empty icon colour (default var(--mj-border-strong))."),
            ("--mj-rating-icon-color-filled", "Filled icon colour (default var(--mj-color-warning)); `icon-color` overrides it."),
            ("--mj-rating-icon-color-hover", "Hover preview colour (default the filled colour)."),
        ],
    ),
    ComponentDoc(
        tag="mj-captcha",
        title="CAPTCHA",
        group="text",
        summary="A form-associated host for a CAPTCHA provider widget, driven by a provider adapter you supply.",
        description=_code("""
            <p><code>&lt;mj-captcha&gt;</code> mounts a CAPTCHA widget through a <code>providerAdapter</code>
            object and takes part in the form with the verification token as its value. <strong>No provider
            adapters are built in</strong>: reCAPTCHA, Turnstile or hCaptcha need an adapter that loads the vendor
            SDK. An adapter is mounted as soon as it is assigned; a <code>provider</code> without an adapter shows
            the <code>fallback</code> slot and fires <code>mj-error</code> (<code>sdk-load-failure</code>).</p>
            <p>The adapter interface: <code>load(container, options)</code> renders the widget into the shadow
            container (a 10 s timeout shows the fallback). <code>options</code> holds <code>siteKey</code>,
            <code>theme</code>, <code>size</code> and three callbacks, the counterparts of the vendors'
            <code>callback</code> / <code>expired-callback</code> / <code>error-callback</code>:
            <code>onVerify(token)</code> when the user solves a visible widget (at any time),
            <code>onExpire()</code> and <code>onError(error)</code>. <code>execute()</code> runs the challenge on
            demand and resolves to a token within 5 s - after load with <code>auto-execute</code> and at submit
            time for invisible providers (an <code>onVerify</code> during that wait also completes it); optional
            <code>reset()</code> and <code>destroy()</code>. A non-empty token verifies the control
            (<code>mj-verified</code>); after <code>token-expiry</code> seconds it expires
            (<code>mj-expired</code>).</p>
            <p>With <code>provider="recaptcha-v3"</code> or <code>turnstile</code> the challenge is invisible: the
            form submit is held, <code>execute()</code> runs, and the form is re-submitted with the original
            submitter once verified. A required visible captcha blocks the submit until verified, even in a
            <code>novalidate</code> form.</p>
        """),
        how_to_use=_code("""
            <p>Write an adapter for your provider, assign it to <code>providerAdapter</code>, set
            <code>site-key</code>, <code>name</code> and <code>required</code>. Use the <code>fallback</code> slot
            for the unavailable state and <code>verified-message</code> for custom success text. Call
            <code>reset()</code> after a failed server check.</p>
        """),
        example="",
        examples=[
            ComponentExample(
                key="basic",
                title="Basic usage (mock adapter)",
                description="<p>A mock adapter renders a widget and, with <code>auto-execute</code>, resolves a "
                            "token after a short delay: the status turns to verified and <code>mj-verified</code> "
                            "is logged.</p>",
                html=_code("""
                    <mj-captcha id="demo-captcha" name="captcha-token" label="Security check" site-key="demo-site-key"
                      auto-execute help-text="This demo uses a mock provider adapter.">
                    </mj-captcha>
                """),
                script=_code("""
                    const captcha = document.getElementById("demo-captcha")
                    captcha.providerAdapter = {
                      load(container, options) {
                        const box = document.createElement("div")
                        box.style.cssText = "display:flex;align-items:center;gap:var(--mj-space-2);padding:var(--mj-space-3);" +
                          "border:1px solid var(--mj-border);border-radius:var(--mj-radius-md)"
                        box.textContent = "Mock widget for " + options.siteKey + " - checking..."
                        container.append(box)
                        this.box = box
                      },
                      execute() {
                        return new Promise((resolve) => setTimeout(() => {
                          this.box.textContent = "Mock widget: you look human."
                          resolve("tok_" + Math.random().toString(36).slice(2, 10))
                        }, 800))
                      },
                      reset() { this.box.textContent = "Mock widget: reset." },
                      destroy() {},
                    }
                    captcha.addEventListener("mj-verified", () => mjSandbox.log("verified", { token: captcha.token, verified: captcha.verified }))
                """),
            ),
            ComponentExample(
                key="invisible",
                title="Invisible provider on submit",
                description="<p><code>provider=\"turnstile\"</code> (set by the script after the adapter) is invisible: pressing Submit holds the form, runs "
                            "the adapter's <code>execute()</code> and re-submits once verified. The output shows the "
                            "token that was sent.</p>",
                html=_code("""
                    <form id="demo-form" class="demo-form">
                      <mj-text-field name="email" label="Email" value="ada@example.com"></mj-text-field>
                      <mj-captcha id="invisible-captcha" name="captcha-token" site-key="demo"></mj-captcha>
                      <div class="actions"><button type="submit">Subscribe</button></div>
                      <output id="demo-result" class="result">Press Subscribe.</output>
                    </form>
                """),
                css=_FORM_CSS,
                script=_NATIVE_FORM_SCRIPT + _code("""
                    const captcha = document.getElementById("invisible-captcha")
                    captcha.providerAdapter = {
                      load() {},
                      execute() {
                        mjSandbox.log("execute() called", {})
                        return new Promise((resolve) => setTimeout(() => resolve("invisible-token-42"), 600))
                      },
                    }
                    // Set after the adapter, so the first mount already has it.
                    captcha.setAttribute("provider", "turnstile")
                """),
            ),
            ComponentExample(
                key="fallback",
                title="Fallback and errors",
                description="<p>A <code>provider</code> without an adapter shows the <code>fallback</code> slot "
                            "(<code>mj-error</code> <code>sdk-load-failure</code>); an adapter whose "
                            "<code>load()</code> rejects reports <code>provider-error</code>.</p>",
                html=_code("""
                    <div class="stack">
                      <mj-captcha label="Unavailable provider" provider="recaptcha-v2">
                        <p slot="fallback">Verification could not load. Call us on 0800 000 000 to finish signing up.</p>
                      </mj-captcha>
                      <mj-captcha id="failing-captcha" label="Failing adapter" error-message="The security check failed to start."></mj-captcha>
                    </div>
                """),
                css=_STACK_CSS,
                script=_code("""
                    const captcha = document.getElementById("failing-captcha")
                    captcha.providerAdapter = { load() { return Promise.reject(new Error("network down")) } }
                """),
            ),
            ComponentExample(
                key="states",
                title="Verified message, expiry and reset",
                description="<p>A custom <code>verified-message</code>, a token that expires after 3 seconds "
                            "(<code>mj-expired</code>), and a Reset button calling <code>reset()</code> "
                            "(<code>mj-reset</code>) which re-runs the challenge.</p>",
                html=_code("""
                    <mj-captcha id="expiring-captcha" label="Short-lived token" token-expiry="3" auto-execute>
                      <span slot="verified-message">Thanks - you are verified for a few seconds.</span>
                    </mj-captcha>
                    <button type="button" id="captcha-reset">Reset</button>
                """),
                css=_code("""
                    #captcha-reset { margin-block-start: var(--mj-space-3); }
                """),
                script=_code("""
                    const captcha = document.getElementById("expiring-captcha")
                    const adapter = {
                      load(container) {
                        container.textContent = "Mock widget"
                      },
                      execute() { return Promise.resolve("short-token") },
                      reset() { mjSandbox.log("adapter.reset()", {}) },
                    }
                    captcha.providerAdapter = adapter
                    document.getElementById("captcha-reset").addEventListener("click", () => {
                      captcha.reset()
                      captcha.providerAdapter = adapter
                    })
                """),
            ),
            ComponentExample(
                key="form",
                title="Required in a form",
                description="<p>A required visible captcha blocks Submit (<code>mj-invalid</code>) until its widget "
                            "is solved: press 'I am human' in the mock widget (the adapter reports the token "
                            "through <code>options.onVerify</code>), then Submit.</p>",
                html=_code("""
                    <form id="demo-form" class="demo-form">
                      <mj-text-field name="name" label="Name" value="Ada"></mj-text-field>
                      <mj-captcha id="required-captcha" name="captcha-token" label="Verify" required></mj-captcha>
                      <div class="actions">
                        <button type="submit">Send</button>
                        <button type="reset">Reset</button>
                      </div>
                      <output id="demo-result" class="result">Submit to see the form data.</output>
                    </form>
                """),
                css=_FORM_CSS,
                script=_NATIVE_FORM_SCRIPT + _code("""
                    const captcha = document.getElementById("required-captcha")
                    captcha.providerAdapter = {
                      load(container, options) {
                        const button = document.createElement("button")
                        button.type = "button"
                        button.textContent = "I am human"
                        button.addEventListener("click", () => {
                          button.textContent = "Solved"
                          button.disabled = true
                          options.onVerify("human-token")
                        })
                        container.append(button)
                        this.button = button
                      },
                      reset() {
                        this.button.textContent = "I am human"
                        this.button.disabled = false
                      },
                    }
                """),
            ),
        ],
        attributes=[
            _attr("label", "Visible label above the widget."),
            _name_attr(),
            _attr("provider", "Provider name; `recaptcha-v3` and `turnstile` are invisible (run on submit). Without an adapter it shows the fallback.",
                  values=["recaptcha-v2", "recaptcha-v3", "turnstile", "hcaptcha"]),
            _attr("site-key", "Passed to the adapter's `load()` as `siteKey` (read at mount)."),
            _attr("theme", "Passed to `load()`; `auto` follows prefers-color-scheme (read at mount).", kind="enum",
                  values=["auto", "light", "dark"], default="auto"),
            _attr("size", "Passed to `load()` (read at mount); it does not make the widget invisible.",
                  values=["normal", "compact"], default="normal"),
            _attr("auto-execute", "Calls the adapter's `execute()` right after `load()` (read at mount); a widget the user solves later reports through `onVerify` instead.", kind="boolean"),
            _attr("token-expiry", "Seconds until a token expires; 0 or less never expires.", kind="number", default="120"),
            _attr("help-text", "Guidance shown below the widget."),
            _attr("error-message", "Replaces the error status and validation text."),
            _required_message_attr(),
            _attr("required", "A visible captcha must be verified before the form submits.", kind="boolean"),
            _attr("disabled", "Dims the widget; submits are not held.", kind="boolean"),
        ],
        events=[
            ("mj-verified", "A non-empty token was received.", "{ token: string }"),
            ("mj-expired", "The token expired after `token-expiry` seconds.", "{}"),
            ("mj-error", "Loading or executing failed.",
             "{ code: 'sdk-load-failure' | 'provider-error' | 'not-ready' | 'execute-failed', message: string }"),
            ("mj-reset", "Form reset, form restore or `reset()`.", "{}"),
            ("mj-invalid", "A required visible captcha blocked a submit, or a check failed.", "{ validationMessage: string }"),
        ],
        slots=[
            ("fallback", "Shown when the provider is unavailable.", "<p>Verification is unavailable. Please contact support.</p>"),
            ("verified-message", "Shown instead of the built-in 'Verification successful' status.", "<span>You are verified.</span>"),
        ],
        properties=[
            ("providerAdapter", "object | null. { load(container, { siteKey, theme, size, onVerify(token), onExpire(), onError(error) }), execute?(), reset?(), destroy?() }; assigning it (re)mounts the widget."),
            ("token", "string. The current token (read-only)."),
            ("verified", "boolean. True while a token is held (read-only)."),
            ("value", "string. The token form value."),
        ] + _FORM_PROPERTIES,
        methods=[
            ("reset()", "Clears the token and calls the adapter's `reset()`."),
            ("checkValidity() -> boolean", "Runs the required check (visible providers)."),
            ("reportValidity() -> boolean", "Runs it and shows the error."),
            ("focus(options)", "Focuses the first focusable element inside the widget."),
        ],
        parts=[
            ("label", "The label."),
            ("provider-container", "The container the adapter renders into."),
            ("status", "The status line (verifying, verified, expired, error)."),
            ("verified-message", "Wrapper of the verified-message slot."),
            ("fallback", "Wrapper of the fallback slot."),
            ("help", "Help text."),
            ("error", "Inline error message."),
        ],
        css_properties=[
            ("--mj-captcha-container-min-height", "Minimum height of the widget container (default 78px)."),
        ],
    ),
    ComponentDoc(
        tag="mj-form",
        title="Form",
        group="text",
        summary="A form wrapper that owns native and mj-* controls, validates them, and emits mj-submit, mj-invalid and mj-reset.",
        description=_code("""
            <p><code>&lt;mj-form&gt;</code> lays its content out in a column and owns every control inside it
            through a hidden light-DOM <code>&lt;form&gt;</code> (it adopts a direct child <code>&lt;form&gt;</code>
            if there is one): each native control and form-associated <code>mj-*</code> control gets a
            <code>form</code> attribute pointing at it, also when added later. So native submit and reset buttons,
            <code>&lt;mj-button type="submit"&gt;</code> / <code>type="reset"</code> and Enter in a single-line field
            all work, and <code>FormData</code> holds every control's value.</p>
            <p>On submit every control is validated (the browser's bubbles are never shown; each control renders
            its own inline error). If any is invalid, <code>mj-invalid</code> fires with the invalid controls and
            an <code>errors</code> list (<code>control, controlId, name, label, message</code>) and focus moves to
            the first invalid control, or to an <code>&lt;mj-validation-summary&gt;</code> inside the form (or
            pointing at it with <code>for</code>), which lists them. Otherwise the cancelable
            <code>mj-submit</code> fires with <code>formData</code>, a <code>value</code> map
            (<code>{ name: [values] }</code>) and the <code>submitter</code>; with an <code>action</code> (and not
            cancelled) the owner form is then submitted natively. <code>mj-reset</code> (cancelable) fires once
            and every control returns to its default value.</p>
            <p><code>validate="eager"</code> re-validates a control when it loses focus after the first submit
            attempt, <code>aggressive</code> also on every change. <code>loading</code> ignores submits, disables
            the submit buttons, sets <code>aria-busy</code> and announces <code>submitting-label</code>;
            <code>disabled</code> disables every control. With <code>aria-label</code> the form becomes a
            <code>role="form"</code> landmark.</p>
        """),
        how_to_use=_code("""
            <p>Put fields and buttons inside; give each control a <code>name</code>. Listen for
            <code>mj-submit</code> and send <code>event.detail.value</code> or <code>formData</code> yourself, or
            set <code>action</code> and <code>method</code> for a native post. Place an
            <code>&lt;mj-validation-summary slot="summary"&gt;</code> first to list errors, and
            <code>&lt;mj-error-message auto for="..."&gt;</code> next to native inputs. Set
            <code>loading</code> while a request is in flight. Use <code>submit()</code>,
            <code>requestSubmit(submitter)</code> and <code>reset()</code> from script; read <code>valid</code>,
            <code>value</code> and <code>elements</code>.</p>
            <p>The controls' own <code>mj-invalid</code> events (and <code>mj-reset</code> of controls such as
            <code>mj-captcha</code>) bubble through the form, so check <code>event.target === form</code> in a
            listener on the form.</p>
        """),
        example="",
        examples=[
            ComponentExample(
                key="basic",
                title="Basic usage",
                description="<p>A sign-in form with a validation summary above the fields. Press Sign in with "
                            "empty fields (<code>mj-invalid</code>, inline errors, the summary lists both fields), fill "
                            "them and press Sign in or Enter (<code>mj-submit</code> with the values), then Reset "
                            "(<code>mj-reset</code>).</p>",
                html=_code("""
                    <mj-form id="demo-form" validate="eager" aria-label="Sign in">
                      <mj-validation-summary slot="summary"></mj-validation-summary>
                      <mj-text-field name="username" label="Username" autocomplete="username" required></mj-text-field>
                      <mj-password-field name="password" label="Password" current-password required></mj-password-field>
                      <div class="actions">
                        <mj-button type="submit" variant="primary">Sign in</mj-button>
                        <button type="reset">Reset</button>
                      </div>
                    </mj-form>
                    <output id="demo-result" class="result">Submit, fix and reset the form; the result shows here.</output>
                """),
                css=_FORM_CSS + _code("""
                    mj-form { max-inline-size: 26rem; margin-block-end: var(--mj-space-4); }
                """),
                script=_code("""
                    const form = document.getElementById("demo-form")
                    const output = document.getElementById("demo-result")
                    form.addEventListener("mj-invalid", (event) => {
                      if (event.target !== form) { return }
                      output.textContent = "mj-invalid:\\n" + event.detail.errors.map((error) => "- " + error.label + ": " + error.message).join("\\n")
                    })
                    form.addEventListener("mj-submit", (event) => {
                      if (event.target !== form) { return }
                      output.textContent = "mj-submit value: " + JSON.stringify(event.detail.value)
                    })
                    form.addEventListener("mj-reset", (event) => {
                      if (event.target !== form) { return }
                      output.textContent = "mj-reset: every field is back to its default."
                    })
                """),
            ),
            ComponentExample(
                key="events",
                title="Submit, invalid, reset (scripted)",
                description="<p>The script drives a contact form: an empty submit (<code>mj-invalid</code>, summary "
                            "and inline errors), filling the fields and submitting (<code>mj-submit</code> with "
                            "<code>value</code>), a reset (<code>mj-reset</code>) and a final empty submit so the "
                            "errors stay on screen. <code>valid</code> and <code>value</code> are logged.</p>",
                html=_code("""
                    <mj-form id="contact-form" aria-label="Contact us">
                      <mj-validation-summary slot="summary"></mj-validation-summary>
                      <mj-text-field id="contact-name" name="name" label="Name" required></mj-text-field>
                      <mj-typed-field id="contact-email" type="email" name="email" label="Email" required></mj-typed-field>
                      <div class="field">
                        <mj-label for="contact-topic">Topic</mj-label>
                        <select id="contact-topic" name="topic" class="native">
                          <option>Sales</option>
                          <option>Support</option>
                        </select>
                      </div>
                      <mj-textarea id="contact-message" name="message" label="Message" required minlength="10"></mj-textarea>
                      <div class="actions">
                        <mj-button type="submit" variant="primary">Send</mj-button>
                        <mj-button type="reset">Reset</mj-button>
                      </div>
                    </mj-form>
                """),
                css=_FORM_CSS + _code("""
                    mj-form { max-inline-size: 30rem; }
                """),
                script=_code("""
                    const form = document.getElementById("contact-form")
                    form.submit()
                    mjSandbox.log("after empty submit", { valid: form.valid })
                    document.getElementById("contact-name").value = "Grace Hopper"
                    document.getElementById("contact-email").value = "grace@example.com"
                    document.getElementById("contact-topic").value = "Support"
                    document.getElementById("contact-message").value = "The compiler found a moth."
                    mjSandbox.log("filled", { valid: form.valid, value: form.value })
                    form.submit()
                    form.reset()
                    mjSandbox.log("after reset", { value: form.value })
                    form.submit()
                """),
            ),
            ComponentExample(
                key="mixed-controls",
                title="Native and mj-* controls, aggressive validation",
                description="<p>Native inputs, a select and a checkbox next to <code>mj-*</code> controls in one "
                            "form. <code>validate=\"aggressive\"</code>: after the first submit, every change "
                            "re-validates. The native inputs show their errors through "
                            "<code>&lt;mj-error-message auto&gt;</code>.</p>",
                html=_code("""
                    <mj-form id="order-form" validate="aggressive">
                      <div class="field">
                        <mj-label for="order-company" required>Company</mj-label>
                        <input id="order-company" name="company" class="native" required minlength="2">
                        <mj-error-message for="order-company" auto></mj-error-message>
                      </div>
                      <mj-number-field name="seats" label="Seats" value="5" min="1" max="50" required></mj-number-field>
                      <div class="field">
                        <mj-label for="order-plan">Plan</mj-label>
                        <select id="order-plan" name="plan" class="native">
                          <option value="team">Team</option>
                          <option value="business">Business</option>
                        </select>
                      </div>
                      <mj-rating name="priority" label="Priority" value="2" max="3"></mj-rating>
                      <label class="check"><input type="checkbox" id="order-terms" name="terms" value="accepted" required> I accept the terms</label>
                      <mj-error-message for="order-terms" auto>You must accept the terms.</mj-error-message>
                      <div class="actions">
                        <mj-button type="submit" variant="primary">Order</mj-button>
                        <mj-button type="reset">Reset</mj-button>
                      </div>
                    </mj-form>
                    <output id="demo-result" class="result">Submit to see the value map.</output>
                """),
                css=_FORM_CSS + _code("""
                    mj-form { max-inline-size: 30rem; margin-block-end: var(--mj-space-4); }
                """),
                script=_code("""
                    const form = document.getElementById("order-form")
                    const output = document.getElementById("demo-result")
                    form.addEventListener("mj-submit", (event) => { if (event.target !== form) { return } output.textContent = JSON.stringify(event.detail.value, null, 1) })
                    form.addEventListener("mj-invalid", (event) => { if (event.target !== form) { return } output.textContent = "Invalid: " + event.detail.summary.map((entry) => entry.name).join(", ") })
                    form.addEventListener("mj-reset", (event) => { if (event.target !== form) { return } output.textContent = "Reset." })
                """),
            ),
            ComponentExample(
                key="loading",
                title="Async submit with loading",
                description="<p>The <code>mj-submit</code> listener sets <code>loading</code> for 1.5 seconds "
                            "while a save is simulated: further submits are ignored, the submit button is disabled "
                            "and <code>submitting-label</code> is announced.</p>",
                html=_code("""
                    <mj-form id="profile-form" submitting-label="Saving your profile">
                      <mj-text-field name="display-name" label="Display name" value="Ada" required></mj-text-field>
                      <mj-typed-field type="url" name="website" label="Website" value="https://ada.example"></mj-typed-field>
                      <div class="actions">
                        <mj-button id="save-button" type="submit" variant="primary">Save</mj-button>
                      </div>
                    </mj-form>
                    <output id="demo-result" class="result">Press Save.</output>
                """),
                css=_FORM_CSS + _code("""
                    mj-form { max-inline-size: 26rem; margin-block-end: var(--mj-space-4); }
                """),
                script=_code("""
                    const form = document.getElementById("profile-form")
                    const button = document.getElementById("save-button")
                    const output = document.getElementById("demo-result")
                    form.addEventListener("mj-submit", (event) => {
                      if (event.target !== form) { return }
                      form.loading = true
                      button.setAttribute("loading", "")
                      output.textContent = "Saving " + JSON.stringify(event.detail.value) + " ..."
                      setTimeout(() => {
                        form.loading = false
                        button.removeAttribute("loading")
                        output.textContent = "Saved at " + new Date().toLocaleTimeString()
                        mjSandbox.log("saved", { loading: form.loading })
                      }, 1500)
                    })
                """),
            ),
            ComponentExample(
                key="disabled",
                title="Disabled form",
                description="<p><code>disabled</code> disables every control inside the form and restores them "
                            "when removed. Use the checkbox to toggle it.</p>",
                html=_code("""
                    <label class="check"><input type="checkbox" id="lock-form" checked> Lock the form</label>
                    <mj-form id="locked-form" disabled>
                      <mj-text-field name="city" label="City" value="Lisbon"></mj-text-field>
                      <div class="field">
                        <mj-label for="locked-notes">Notes</mj-label>
                        <textarea id="locked-notes" name="notes" class="native">Ring the bell twice.</textarea>
                      </div>
                      <div class="actions">
                        <mj-button type="submit" variant="primary">Save</mj-button>
                      </div>
                    </mj-form>
                """),
                css=_FORM_CSS + _code("""
                    mj-form { max-inline-size: 26rem; margin-block-start: var(--mj-space-3); }
                """),
                script=_code("""
                    const form = document.getElementById("locked-form")
                    document.getElementById("lock-form").addEventListener("change", (event) => {
                      form.toggleAttribute("disabled", event.target.checked)
                      mjSandbox.log("disabled", { disabled: form.hasAttribute("disabled") })
                    })
                """),
            ),
        ],
        attributes=[
            _attr("validate", "When controls are re-validated after the first submit attempt: only on submit, on blur (`eager`), or on blur and every change (`aggressive`).",
                  kind="enum", values=["submit", "eager", "aggressive"], default="submit"),
            _attr("novalidate", "Skips validation on submit (a `formnovalidate` submitter does the same).", kind="boolean"),
            _attr("action", "URL for a native submit after an uncancelled `mj-submit`; without it nothing is sent."),
            _attr("method", "HTTP method of the native submit (`dialog` also submits natively).", kind="enum",
                  values=["get", "post", "dialog"], default="post"),
            _attr("enctype", "Encoding of the native submit.", kind="enum",
                  values=["application/x-www-form-urlencoded", "multipart/form-data", "text/plain"]),
            _attr("target", "Browsing context of the native submit.", values=["_self", "_blank"]),
            _attr("autocomplete", "Autocomplete default for the controls.", kind="enum", values=["on", "off"]),
            _attr("loading", "Ignores submits, disables the submit buttons, sets aria-busy and announces `submitting-label`.", kind="boolean"),
            _attr("submitting-label", "Text announced while `loading`.", default="Submitting…"),
            _attr("disabled", "Disables every control in the form.", kind="boolean"),
            _attr("aria-label", "Accessible name; makes the form a `role=form` landmark."),
            _attr("aria-labelledby", "Id of the element naming the form; makes it a landmark."),
        ],
        events=[
            ("mj-submit", "Cancelable. Every control is valid (or validation was skipped). Not cancelled and `action` set: the native submit follows.",
             "{ formData: FormData, value: { [name]: string[] }, valid: true, submitter: Element | null }"),
            ("mj-invalid", "Submit found invalid controls; focus moves to the first one or to the validation summary.",
             "{ controls: Element[], summary: { name, message }[], errors: { control, controlId, name, label, message }[] }"),
            ("mj-reset", "Cancelable. The form is about to reset its controls (fired once).", "{}"),
        ],
        slots=[
            ("", "Fields, fieldsets and buttons, laid out in a column.",
             '<mj-text-field name="note" label="Note"></mj-text-field>'),
            ("summary", "Shown first: typically an `<mj-validation-summary>`.", "<mj-validation-summary></mj-validation-summary>"),
        ],
        properties=[
            ("value", "{ [name]: string[] }. Snapshot of the form data (read-only)."),
            ("valid", "boolean. Every control satisfies its constraints (read-only; shows no errors)."),
            ("elements", "HTMLFormControlsCollection | null. The owner form's controls (read-only)."),
            ("loading", "boolean. Reflects the `loading` attribute."),
            ("disabled", "boolean. Reflects the `disabled` attribute."),
        ],
        methods=[
            ("submit()", "Validates and submits exactly like a submit button (fires mj-invalid or mj-submit)."),
            ("requestSubmit(submitter)", "Same, with a submitter whose name/value is added to the data."),
            ("reset()", "Resets every control (fires mj-reset, which can cancel it)."),
        ],
        parts=[
            ("form", "The column that holds the summary and default slots."),
        ],
        css_properties=[
            ("--mj-form-gap", "Gap between the form's children (default var(--mj-space-4))."),
            ("--mj-form-max-width", "Maximum width of the column (default none)."),
        ],
    ),
    ComponentDoc(
        tag="mj-fieldset",
        title="Fieldset",
        group="text",
        summary="Groups related controls under a legend, with required/optional markers, collapsing and disabling.",
        description=_code("""
            <p><code>&lt;mj-fieldset&gt;</code> renders a native <code>&lt;fieldset&gt;</code> with a legend (the
            <code>legend</code> attribute or the <code>legend</code> slot), a <code>*</code> or '(optional)'
            marker, the controls and a <code>footer</code> slot.</p>
            <p><code>disabled</code> disables every slotted control, native and <code>mj-*</code> (also ones added
            later) and re-enables them when removed; disabled controls are left out of the form data.
            <code>collapsible</code> turns the legend into a toggle button (<code>aria-expanded</code>) that fires
            a cancelable <code>mj-toggle</code>; <code>open</code> shows the content, and collapsed content is
            inert. <code>invalid</code> gives the group the error border; <code>variant="borderless"</code>
            removes the frame.</p>
        """),
        how_to_use=_code("""
            <p>Wrap related fields (an address, a set of preferences) and set <code>legend</code>. Mark the
            group <code>required</code> or <code>optional</code>; set <code>invalid</code> from your validation
            (e.g. on <code>mj-invalid</code>). Use <code>collapsible open</code> for advanced settings and
            <code>disabled</code> to switch off a section. <code>controls</code> lists the controls inside.</p>
        """),
        example="",
        examples=[
            ComponentExample(
                key="basic",
                title="Basic usage",
                description="<p>A checkout form with two fieldsets. Submit it empty: the script marks the fieldset "
                            "with invalid fields <code>invalid</code>; fill it and submit (<code>mj-submit</code>), "
                            "or Reset (<code>mj-reset</code>) to clear the marks.</p>",
                html=_code("""
                    <mj-form id="checkout-form">
                      <mj-fieldset id="shipping-fieldset" legend="Shipping address" required>
                        <mj-text-field name="street" label="Street" required></mj-text-field>
                        <mj-text-field name="city" label="City" required></mj-text-field>
                        <mj-masked-input name="zip" label="ZIP code" mask="99999" required></mj-masked-input>
                        <span slot="footer" class="note">We ship to the continental US only.</span>
                      </mj-fieldset>
                      <mj-fieldset id="delivery-fieldset" legend="Delivery" optional collapsible open>
                        <mj-textarea name="instructions" label="Instructions" rows="2"></mj-textarea>
                        <label class="check"><input type="checkbox" name="gift" value="yes"> This is a gift</label>
                      </mj-fieldset>
                      <div class="actions">
                        <mj-button type="submit" variant="primary">Place order</mj-button>
                        <mj-button type="reset">Reset</mj-button>
                      </div>
                    </mj-form>
                    <output id="demo-result" class="result">Submit the form.</output>
                """),
                css=_FORM_CSS + _code("""
                    mj-form { max-inline-size: 32rem; margin-block-end: var(--mj-space-4); }
                    .note { color: var(--mj-text-muted); font-size: var(--mj-font-size-sm); }
                """),
                script=_code("""
                    const form = document.getElementById("checkout-form")
                    const output = document.getElementById("demo-result")
                    const fieldsets = Array.from(form.querySelectorAll("mj-fieldset"))
                    form.addEventListener("mj-invalid", (event) => {
                      if (event.target !== form) { return }
                      for (const fieldset of fieldsets) {
                        fieldset.invalid = event.detail.controls.some((control) => fieldset.contains(control))
                      }
                      output.textContent = "Invalid: " + event.detail.summary.map((entry) => entry.name).join(", ")
                    })
                    const clearMarks = () => { for (const fieldset of fieldsets) { fieldset.invalid = false } }
                    form.addEventListener("mj-submit", (event) => {
                      if (event.target !== form) { return }
                      clearMarks()
                      output.textContent = JSON.stringify(event.detail.value)
                    })
                    form.addEventListener("mj-reset", (event) => {
                      if (event.target !== form) { return }
                      clearMarks()
                      output.textContent = "Reset."
                    })
                """),
            ),
            ComponentExample(
                key="events",
                title="Validate, toggle, reset (scripted)",
                description="<p>The script submits the empty form (the fieldset turns <code>invalid</code>), fills "
                            "the fields and submits, collapses the optional group by clicking its legend "
                            "(<code>mj-toggle</code>) and resets.</p>",
                html=_code("""
                    <mj-form id="account-form">
                      <mj-fieldset id="account-fieldset" legend="Account" required>
                        <mj-typed-field id="account-email" type="email" name="email" label="Email" required></mj-typed-field>
                        <mj-password-field id="account-password" name="password" label="Password" new-password required minlength="8"></mj-password-field>
                      </mj-fieldset>
                      <mj-fieldset id="extras-fieldset" legend="Newsletter" optional collapsible open>
                        <label class="check"><input type="checkbox" name="news" value="weekly"> Weekly digest</label>
                      </mj-fieldset>
                      <div class="actions">
                        <mj-button type="submit" variant="primary">Create account</mj-button>
                        <mj-button type="reset">Reset</mj-button>
                      </div>
                    </mj-form>
                """),
                css=_FORM_CSS + _code("""
                    mj-form { max-inline-size: 30rem; }
                """),
                script=_code("""
                    const form = document.getElementById("account-form")
                    const account = document.getElementById("account-fieldset")
                    form.addEventListener("mj-invalid", (event) => {
                      if (event.target !== form) { return }
                      account.invalid = event.detail.controls.some((control) => account.contains(control))
                    })
                    form.addEventListener("mj-submit", (event) => { if (event.target !== form) { return } account.invalid = false })
                    form.addEventListener("mj-reset", (event) => { if (event.target !== form) { return } account.invalid = false })
                    form.submit()
                    mjSandbox.log("after empty submit", { invalid: account.invalid, controls: account.controls.length })
                    document.getElementById("account-email").value = "lin@example.com"
                    document.getElementById("account-password").value = "Sup3r-secret"
                    form.submit()
                    mjSandbox.log("after valid submit", { invalid: account.invalid })
                    const extras = document.getElementById("extras-fieldset")
                    extras.shadowRoot.querySelector(".legend-btn").click()
                    mjSandbox.log("newsletter group", { open: extras.open })
                    form.reset()
                """),
            ),
            ComponentExample(
                key="disabled",
                title="Disable a section",
                description="<p>'Same as shipping' disables the billing fieldset: its controls are disabled and "
                            "left out of the submitted value. Submit with the box ticked and unticked.</p>",
                html=_code("""
                    <mj-form id="billing-form">
                      <label class="check"><input type="checkbox" id="same-address" name="same-as-shipping" value="yes" checked> Billing address same as shipping</label>
                      <mj-fieldset id="billing-fieldset" legend="Billing address" disabled>
                        <mj-text-field name="billing-street" label="Street" value="1 Infinite Loop" required></mj-text-field>
                        <div class="field">
                          <mj-label for="billing-country">Country</mj-label>
                          <select id="billing-country" name="billing-country" class="native">
                            <option>United States</option>
                            <option>Canada</option>
                          </select>
                        </div>
                      </mj-fieldset>
                      <div class="actions">
                        <mj-button type="submit" variant="primary">Continue</mj-button>
                      </div>
                    </mj-form>
                    <output id="demo-result" class="result">Submit to see what is sent.</output>
                """),
                css=_FORM_CSS + _code("""
                    mj-form { max-inline-size: 30rem; margin-block-end: var(--mj-space-4); }
                """),
                script=_code("""
                    const form = document.getElementById("billing-form")
                    const billing = document.getElementById("billing-fieldset")
                    document.getElementById("same-address").addEventListener("change", (event) => {
                      billing.disabled = event.target.checked
                      mjSandbox.log("billing disabled", { disabled: billing.disabled, controls: billing.controls.map((control) => control.disabled) })
                    })
                    form.addEventListener("mj-submit", (event) => {
                      if (event.target !== form) { return }
                      document.getElementById("demo-result").textContent = JSON.stringify(event.detail.value)
                    })
                """),
            ),
            ComponentExample(
                key="variants",
                title="Variants and markers",
                description="<p>Required with a custom <code>required-label</code>, optional with a custom "
                            "<code>optional-label</code>, <code>invalid</code>, <code>borderless</code>, and a "
                            "collapsed group.</p>",
                html=_code("""
                    <div class="stack">
                      <mj-fieldset legend="Contact" required required-label="(required)">
                        <mj-text-field name="phone" label="Phone"></mj-text-field>
                      </mj-fieldset>
                      <mj-fieldset legend="Preferences" optional optional-label="(if you like)">
                        <label class="check"><input type="checkbox"> Dark mode</label>
                      </mj-fieldset>
                      <mj-fieldset legend="Payment" invalid>
                        <mj-masked-input label="Card" mask="9999 9999 9999 9999" value="4111"></mj-masked-input>
                      </mj-fieldset>
                      <mj-fieldset legend="Borderless group" variant="borderless">
                        <mj-text-field label="Nickname"></mj-text-field>
                      </mj-fieldset>
                      <mj-fieldset legend="Advanced (collapsed)" collapsible>
                        <mj-text-field label="API key"></mj-text-field>
                      </mj-fieldset>
                    </div>
                """),
                css=_FORM_CSS + _STACK_CSS,
            ),
            ComponentExample(
                key="slots",
                title="Legend and footer slots",
                description="<p>Rich legend content in the <code>legend</code> slot and a note in "
                            "<code>footer</code>.</p>",
                html=_code("""
                    <mj-fieldset required>
                      <span slot="legend" class="legend">
                        <svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true">
                          <path d="M8 1l7 13H1z" fill="none" stroke="currentColor" stroke-width="1.5"/>
                        </svg>
                        Emergency contact
                      </span>
                      <mj-text-field name="contact-name" label="Name"></mj-text-field>
                      <mj-typed-field type="tel" name="contact-phone" label="Phone"></mj-typed-field>
                      <p slot="footer" class="note">Only used if we cannot reach you.</p>
                    </mj-fieldset>
                """),
                css=_code("""
                    .legend { display: inline-flex; gap: var(--mj-space-1); align-items: center; }
                    .note { margin: 0; color: var(--mj-text-muted); font-size: var(--mj-font-size-sm); }
                    mj-fieldset { max-inline-size: 30rem; }
                """),
            ),
        ],
        attributes=[
            _attr("legend", "Legend text (plain text); the `legend` slot can add or replace content."),
            _attr("required", "Shows the required marker after the legend.", kind="boolean"),
            _attr("optional", "Shows the optional marker (ignored when required).", kind="boolean"),
            _attr("required-label", "Text of the required marker.", default="*"),
            _attr("optional-label", "Text of the optional marker.", default="(optional)"),
            _attr("invalid", "Error styling for the group.", kind="boolean"),
            _attr("disabled", "Disables every slotted control (and re-enables them when removed).", kind="boolean"),
            _attr("collapsible", "Makes the legend a toggle button.", kind="boolean"),
            _attr("open", "Expanded state of a collapsible fieldset; collapsed content is inert.", kind="boolean"),
            _attr("variant", "Absent is outlined; `borderless` removes the frame.", kind="enum", values=["borderless"]),
            _attr("name", "Name of the inner native fieldset."),
        ],
        events=[
            ("mj-toggle", "Cancelable. The legend button was clicked; `open` is the state about to be applied.", "{ open: boolean }"),
        ],
        slots=[
            ("", "The grouped controls.", '<mj-text-field label="Field"></mj-text-field>'),
            ("legend", "Extra or rich legend content (after the `legend` text).", "<strong>Legend</strong>"),
            ("footer", "Notes or actions under the controls.", "<span>Footer note</span>"),
        ],
        properties=[
            ("controls", "Element[]. The form controls inside, native and mj-* (read-only)."),
            ("disabled", "boolean. Reflects `disabled`."),
            ("invalid", "boolean. Reflects `invalid`."),
            ("open", "boolean. Reflects `open`; setting it does not fire mj-toggle."),
        ],
        methods=[],
        parts=[
            ("fieldset", "The native fieldset."),
            ("legend", "The legend."),
            ("legend-button", "The toggle button of a collapsible fieldset."),
            ("indicator", "The required / optional marker."),
            ("content", "Wrapper of the default slot."),
            ("footer", "Wrapper of the footer slot."),
        ],
        css_properties=[
            ("--mj-fieldset-border-color", "Frame colour (default var(--mj-border-strong))."),
            ("--mj-fieldset-invalid-border-color", "Frame colour when invalid (default var(--mj-color-danger))."),
            ("--mj-fieldset-border-radius", "Frame radius (default var(--mj-radius-md))."),
            ("--mj-fieldset-gap", "Gap between the controls (default var(--mj-space-4))."),
            ("--mj-fieldset-legend-color", "Legend colour (default var(--mj-text-muted))."),
            ("--mj-fieldset-legend-size", "Legend font size (default var(--mj-font-size-sm))."),
        ],
    ),
    ComponentDoc(
        tag="mj-label",
        title="Label",
        group="text",
        summary="A form label that names and focuses its control, native or mj-*, with required and optional markers.",
        description=_code("""
            <p><code>&lt;mj-label&gt;</code> labels the control named by <code>for</code> (an id) or the control
            wrapped inside it. It adds itself to the control's <code>aria-labelledby</code> - for
            <code>mj-*</code> controls on the inner input, through element reflection - so the control takes its
            accessible name from the label, and clicking the label focuses the control (and clicks checkboxes,
            radios and buttons). <code>&lt;mj-form&gt;</code> and its validation summary use the label text for
            error entries.</p>
            <p>The label is block-level and stacked above the control by default; <code>layout="inline"</code>
            puts it beside the control. <code>required</code> adds a <code>*</code> (hidden from assistive
            technology), <code>optional</code> an '(optional)' marker; <code>visually-hidden</code> keeps the name
            but hides the text. The <code>suffix</code> slot holds extras such as a help link.</p>
        """),
        how_to_use=_code("""
            <p>Write <code>&lt;mj-label for="email"&gt;Email&lt;/mj-label&gt;</code> before the control with
            <code>id="email"</code>, or wrap the control: <code>&lt;mj-label&gt;Subscribe &lt;input
            type="checkbox"&gt;&lt;/mj-label&gt;</code>. Use it instead of a control's own <code>label</code>
            attribute when you need markup in the label or a custom layout. Listen for <code>mj-click</code> if
            you need to react to label clicks.</p>
        """),
        example="",
        examples=[
            ComponentExample(
                key="basic",
                title="Basic usage",
                description="<p>A label for an <code>mj-text-field</code> in a small form. Click the label: focus "
                            "moves into the field, whose accessible name is 'Username'. Continue with an empty "
                            "field shows the error; Reset clears it.</p>",
                html=_code("""
                    <mj-form id="demo-form">
                      <div class="field">
                        <mj-label for="username-field" required>Username</mj-label>
                        <mj-text-field id="username-field" name="username" required
                          help-text="Click the label to focus the field."></mj-text-field>
                      </div>
                      <div class="actions">
                        <mj-button type="submit" variant="primary">Continue</mj-button>
                        <button type="reset">Reset</button>
                      </div>
                    </mj-form>
                    <output id="demo-result" class="result">Submit or reset the form.</output>
                """),
                css=_FORM_CSS + _code("""
                    mj-form { max-inline-size: 26rem; margin-block-end: var(--mj-space-4); }
                """),
                script=_code("""
                    const form = document.getElementById("demo-form")
                    const output = document.getElementById("demo-result")
                    form.addEventListener("mj-invalid", (event) => {
                      if (event.target !== form) { return }
                      output.textContent = event.detail.errors.map((error) => error.label + ": " + error.message).join("\\n")
                    })
                    form.addEventListener("mj-submit", (event) => { if (event.target !== form) { return } output.textContent = "Submitted " + JSON.stringify(event.detail.value) })
                    form.addEventListener("mj-reset", (event) => { if (event.target !== form) { return } output.textContent = "Reset." })
                """),
            ),
            ComponentExample(
                key="variants",
                title="Required, optional, disabled",
                description="<p>Markers with default and custom text, and a disabled label for a disabled "
                            "control.</p>",
                html=_code("""
                    <div class="stack">
                      <div class="field">
                        <mj-label for="v-email" required required-label="(required)">Email</mj-label>
                        <input id="v-email" type="email" class="native">
                      </div>
                      <div class="field">
                        <mj-label for="v-company" optional>Company</mj-label>
                        <input id="v-company" class="native">
                      </div>
                      <div class="field">
                        <mj-label for="v-ref" optional optional-label="(if you have one)">Referral code</mj-label>
                        <mj-text-field id="v-ref"></mj-text-field>
                      </div>
                      <div class="field">
                        <mj-label for="v-plan" disabled>Plan</mj-label>
                        <mj-text-field id="v-plan" value="Enterprise" disabled></mj-text-field>
                      </div>
                    </div>
                """),
                css=_FORM_CSS + _STACK_CSS,
            ),
            ComponentExample(
                key="layout",
                title="Inline layout and wrapping",
                description="<p><code>layout=\"inline\"</code> puts the label beside its control; a control "
                            "wrapped inside the label is associated without <code>for</code> (click the text to "
                            "toggle the checkbox).</p>",
                html=_code("""
                    <div class="stack">
                      <div><mj-label for="inline-qty" layout="inline">Quantity</mj-label><input id="inline-qty" type="number" value="3" class="native"></div>
                      <mj-label layout="inline">Email me updates <input type="checkbox" checked></mj-label>
                      <mj-label>Wrapped field <input class="native" placeholder="Associated implicitly"></mj-label>
                    </div>
                """),
                css=_FORM_CSS + _STACK_CSS,
            ),
            ComponentExample(
                key="slots",
                title="Suffix slot and visually hidden",
                description="<p>A 'Forgot?' link in the <code>suffix</code> slot, and a search field whose label is "
                            "<code>visually-hidden</code> but still names it.</p>",
                html=_code("""
                    <div class="stack">
                      <div class="field">
                        <mj-label for="s-password">Password <a slot="suffix" href="#forgot">Forgot?</a></mj-label>
                        <mj-password-field id="s-password"></mj-password-field>
                      </div>
                      <div class="field">
                        <mj-label for="s-search" visually-hidden>Search orders</mj-label>
                        <mj-search-input id="s-search" placeholder="Search orders"></mj-search-input>
                      </div>
                    </div>
                """),
                css=_FORM_CSS + _STACK_CSS,
            ),
            ComponentExample(
                key="events",
                title="Labels in a validated form (scripted)",
                description="<p>The script clicks a label (<code>mj-click</code>, focus moves), submits the empty "
                            "form: the summary entries use the label texts. Then it fills and submits, and "
                            "resets.</p>",
                html=_code("""
                    <mj-form id="label-form">
                      <mj-validation-summary slot="summary"></mj-validation-summary>
                      <div class="field">
                        <mj-label id="first-label" for="first-name" required>First name</mj-label>
                        <mj-text-field id="first-name" name="first" required></mj-text-field>
                      </div>
                      <div class="field">
                        <mj-label for="birth-date" required>Date of birth</mj-label>
                        <mj-masked-input id="birth-date" name="dob" mask="99/99/9999" show-mask required></mj-masked-input>
                      </div>
                      <div class="actions">
                        <mj-button type="submit" variant="primary">Save</mj-button>
                        <mj-button type="reset">Reset</mj-button>
                      </div>
                    </mj-form>
                """),
                css=_FORM_CSS + _code("""
                    mj-form { max-inline-size: 28rem; }
                """),
                script=_code("""
                    const form = document.getElementById("label-form")
                    document.getElementById("first-label").shadowRoot.querySelector("label").click()
                    mjSandbox.log("focused after label click", { field: document.activeElement.id })
                    form.submit()
                    document.getElementById("first-name").value = "Katherine"
                    document.getElementById("birth-date").value = "26081918"
                    form.submit()
                    form.reset()
                    form.submit()
                """),
            ),
        ],
        attributes=[
            _attr("for", "Id of the control to label; without it the first control inside the label is used."),
            _attr("required", "Shows the required marker.", kind="boolean"),
            _attr("optional", "Shows the optional marker (ignored when required).", kind="boolean"),
            _attr("required-label", "Text of the required marker.", default="*"),
            _attr("optional-label", "Text of the optional marker.", default="(optional)"),
            _attr("disabled", "Muted styling; clicks no longer move focus.", kind="boolean"),
            _attr("layout", "Absent is stacked (block-level); `inline` places the label beside the control.",
                  kind="enum", values=["inline"]),
            _attr("visually-hidden", "Hides the label visually; it still names the control.", kind="boolean"),
        ],
        events=[
            ("mj-click", "The label was clicked (before focus moves).", "{ control: Element | null }"),
        ],
        slots=[
            ("", "The label text (and optionally the wrapped control).", "Label text"),
            ("suffix", "Content after the label, such as a help link.", '<a href="#help">Help</a>'),
        ],
        properties=[
            ("control", "Element | null. The labelled control (read-only)."),
            ("htmlFor", "string. Reflects `for`."),
        ],
        methods=[],
        parts=[
            ("label", "The inner label element."),
            ("indicator", "The required / optional marker."),
            ("suffix", "Wrapper of the suffix slot."),
        ],
        css_properties=[
            ("--mj-label-color", "Text colour (default var(--mj-text))."),
            ("--mj-label-font-size", "Font size (default var(--mj-font-size-sm))."),
            ("--mj-label-font-weight", "Font weight (default var(--mj-font-weight-medium))."),
            ("--mj-label-gap", "Gap between text, marker and suffix (default var(--mj-space-1))."),
            ("--mj-label-margin", "Space below a stacked label (default var(--mj-space-1))."),
            ("--mj-label-inline-gap", "Space after an inline label (default var(--mj-space-2))."),
            ("--mj-label-required-color", "Required marker colour (default var(--mj-color-danger))."),
            ("--mj-label-disabled-color", "Text colour when disabled (default var(--mj-text-muted))."),
        ],
    ),
    ComponentDoc(
        tag="mj-help-text",
        title="Help Text",
        group="text",
        summary="Supplementary guidance for a form control, linked to it with aria-describedby.",
        description=_code("""
            <p><code>&lt;mj-help-text&gt;</code> shows muted guidance under (or beside) a control. With
            <code>for</code> it adds itself to the control's <code>aria-describedby</code> - for
            <code>mj-*</code> controls on the inner input, through element reflection - so screen readers read it
            with the field. It gives itself an id when it has none, waits for a control that appears later, and
            removes the reference while <code>hidden</code>.</p>
            <p><code>display="inline"</code> makes it an inline block for use next to a control;
            <code>disabled</code> dims it; the <code>icon</code> slot adds a leading icon.</p>
        """),
        how_to_use=_code("""
            <p>Place it after the control and set <code>for</code> to the control's id. Hide it with
            <code>hidden</code> while an error message is shown, so the two do not compete. For a single
            <code>mj-*</code> field the control's own <code>help-text</code> attribute is simpler; use
            <code>mj-help-text</code> for rich content, native controls or custom layouts.</p>
        """),
        example="",
        examples=[
            ComponentExample(
                key="basic",
                title="Basic usage",
                description="<p>Help text linked to a password field in a small form. Submit with a short password "
                            "to see the field's error next to the help; Reset clears it.</p>",
                html=_code("""
                    <mj-form id="demo-form">
                      <div class="field">
                        <mj-label for="new-password" required>New password</mj-label>
                        <mj-password-field id="new-password" name="password" new-password required minlength="10" show-strength></mj-password-field>
                        <mj-help-text for="new-password">Use 10 or more characters. A short phrase is easier to remember.</mj-help-text>
                      </div>
                      <div class="actions">
                        <mj-button type="submit" variant="primary">Change password</mj-button>
                        <button type="reset">Reset</button>
                      </div>
                    </mj-form>
                    <output id="demo-result" class="result">Submit or reset the form.</output>
                """),
                css=_FORM_CSS + _code("""
                    mj-form { max-inline-size: 28rem; margin-block-end: var(--mj-space-4); }
                """),
                script=_code("""
                    const form = document.getElementById("demo-form")
                    const output = document.getElementById("demo-result")
                    form.addEventListener("mj-invalid", (event) => { if (event.target !== form) { return } output.textContent = event.detail.errors.map((error) => error.label + ": " + error.message).join("\\n") })
                    form.addEventListener("mj-submit", (event) => { if (event.target !== form) { return } output.textContent = "Password changed." })
                    form.addEventListener("mj-reset", (event) => { if (event.target !== form) { return } output.textContent = "Reset." })
                """),
            ),
            ComponentExample(
                key="slots",
                title="Icon slot and inline display",
                description="<p>An info icon in the <code>icon</code> slot, and <code>display=\"inline\"</code> help "
                            "next to a checkbox.</p>",
                html=_code("""
                    <div class="stack">
                      <div class="field">
                        <mj-label for="vat-number">VAT number</mj-label>
                        <input id="vat-number" class="native" placeholder="GB123456789">
                        <mj-help-text for="vat-number">
                          <svg slot="icon" viewBox="0 0 16 16" width="14" height="14" aria-hidden="true">
                            <circle cx="8" cy="8" r="6.5" fill="none" stroke="currentColor" stroke-width="1.5"/>
                            <path d="M8 7v4M8 4.5v.5" stroke="currentColor" stroke-width="1.5"/>
                          </svg>
                          Found on your invoices; leave empty if you are not VAT registered.
                        </mj-help-text>
                      </div>
                      <label class="check"><input type="checkbox" id="remember-me"> Remember me
                        <mj-help-text for="remember-me" display="inline">(not on shared computers)</mj-help-text></label>
                    </div>
                """),
                css=_FORM_CSS + _STACK_CSS,
            ),
            ComponentExample(
                key="states",
                title="Hidden and disabled",
                description="<p>The button toggles <code>hidden</code> (the <code>aria-describedby</code> link is "
                            "removed and restored; see the log); the second help text is <code>disabled</code>.</p>",
                html=_code("""
                    <div class="stack">
                      <div class="field">
                        <mj-label for="h-input">Reference</mj-label>
                        <input id="h-input" class="native">
                        <mj-help-text id="toggle-help" for="h-input">Shown until you hide it.</mj-help-text>
                        <button type="button" id="toggle-help-button">Toggle help</button>
                      </div>
                      <div class="field">
                        <mj-label for="d-input" disabled>Locked</mj-label>
                        <input id="d-input" class="native" disabled value="N/A">
                        <mj-help-text for="d-input" disabled>This field is managed by your administrator.</mj-help-text>
                      </div>
                    </div>
                """),
                css=_FORM_CSS + _STACK_CSS,
                script=_code("""
                    const help = document.getElementById("toggle-help")
                    const input = document.getElementById("h-input")
                    const report = (label) => mjSandbox.log(label, { hidden: help.hidden, describedby: input.getAttribute("aria-describedby") })
                    report("initial")
                    document.getElementById("toggle-help-button").addEventListener("click", () => {
                      help.hidden = !help.hidden
                      report("toggled")
                    })
                """),
            ),
            ComponentExample(
                key="events",
                title="Help and errors in a form (scripted)",
                description="<p>The help text is hidden while the field's <code>mj-error-message</code> is shown. "
                            "The script submits an invalid value (<code>mj-invalid</code>, <code>mj-show</code>), "
                            "types a valid one (<code>mj-hide</code>), submits (<code>mj-submit</code>) and "
                            "resets.</p>",
                html=_code("""
                    <mj-form id="handle-form">
                      <div class="field">
                        <mj-label for="handle" required>Handle</mj-label>
                        <input id="handle" name="handle" class="native" required pattern="@[a-z0-9_]{3,15}" placeholder="@name">
                        <mj-help-text id="handle-help" for="handle">Starts with @, then 3-15 lowercase letters, digits or _.</mj-help-text>
                        <mj-error-message id="handle-error" for="handle" auto>That handle is not valid.</mj-error-message>
                      </div>
                      <div class="actions">
                        <mj-button type="submit" variant="primary">Claim handle</mj-button>
                        <mj-button type="reset">Reset</mj-button>
                      </div>
                    </mj-form>
                """),
                css=_FORM_CSS + _code("""
                    mj-form { max-inline-size: 28rem; }
                """),
                script=_code("""
                    const form = document.getElementById("handle-form")
                    const input = document.getElementById("handle")
                    const help = document.getElementById("handle-help")
                    const error = document.getElementById("handle-error")
                    error.addEventListener("mj-show", () => { help.hidden = true })
                    error.addEventListener("mj-hide", () => { help.hidden = false })
                    input.value = "Bad Handle"
                    form.submit()
                    mjSandbox.log("after invalid submit", { helpHidden: help.hidden, errorVisible: error.visible })
                    input.value = "@ada_l"
                    input.dispatchEvent(new Event("input", { bubbles: true }))
                    form.submit()
                    mjSandbox.log("after valid submit", { helpHidden: help.hidden, errorVisible: error.visible })
                    form.reset()
                """),
            ),
        ],
        attributes=[
            _attr("for", "Id of the described control; the help text is added to its aria-describedby."),
            _attr("display", "Absent is block; `inline` for use beside a control.", kind="enum", values=["inline"]),
            _attr("hidden", "Hides the help text and removes the aria-describedby reference.", kind="boolean"),
            _attr("disabled", "Dimmed styling to match a disabled control.", kind="boolean"),
        ],
        events=[],
        slots=[
            ("", "The help text.", "Helpful guidance for this field."),
            ("icon", "A leading icon.",
             '<svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true"><circle cx="8" cy="8" r="6" fill="currentColor"/></svg>'),
        ],
        properties=[
            ("control", "Element | null. The described control (read-only)."),
        ],
        methods=[],
        parts=[
            ("container", "The paragraph holding icon and text."),
            ("icon", "Wrapper of the icon slot."),
        ],
        css_properties=[
            ("--mj-help-text-color", "Text colour (default var(--mj-text-muted))."),
            ("--mj-help-text-font-size", "Font size (default var(--mj-font-size-xs))."),
            ("--mj-help-text-gap", "Gap between icon and text (default var(--mj-space-1))."),
            ("--mj-help-text-margin-top", "Space above the text (default var(--mj-space-1))."),
            ("--mj-help-text-disabled-color", "Text colour when disabled (default var(--mj-text-muted))."),
        ],
    ),
    ComponentDoc(
        tag="mj-error-message",
        title="Error Message",
        group="text",
        summary="An inline validation message for a control: shown with visible, or automatically from the control's validity.",
        description=_code("""
            <p><code>&lt;mj-error-message&gt;</code> is a <code>role="alert"</code> message tied to the control
            named by <code>for</code>. While <code>visible</code> it adds itself to the control's
            <code>aria-describedby</code> and sets <code>aria-invalid="true"</code> (for <code>mj-*</code> controls
            on the inner input, through element reflection), and fires <code>mj-show</code>; hiding it restores the
            control and fires <code>mj-hide</code>. Without <code>visible</code> it takes no space unless
            <code>always-render</code> reserves it.</p>
            <p>With <code>auto</code> it follows the control's validity: it shows when the control fires
            <code>invalid</code> (a failed <code>checkValidity()</code> or an <code>mj-form</code> submit) or is
            left invalid, and hides as soon as the control becomes valid; <code>mj-form</code> refreshes it on
            submit and reset. The text is the <code>message</code> attribute, else the element's own content,
            else (in <code>auto</code> mode) the control's <code>validationMessage</code>. Text changes while
            visible are applied after 300 ms so the alert is not re-read on every keystroke.</p>
        """),
        how_to_use=_code("""
            <p>Put it after the control and set <code>for</code>. Inside an <code>mj-form</code> add
            <code>auto</code> and you are done; elsewhere toggle <code>visible</code> (or the property) from your
            own validation. Use it for native inputs and custom checks; <code>mj-*</code> fields already render
            their own inline error.</p>
        """),
        example="",
        examples=[
            ComponentExample(
                key="basic",
                title="Basic usage",
                description="<p>A visible error for a native email input. The input gets "
                            "<code>aria-invalid=\"true\"</code> and is described by the message.</p>",
                html=_code("""
                    <div class="field">
                      <mj-label for="basic-email">Email</mj-label>
                      <input id="basic-email" type="email" class="native" value="ada@">
                      <mj-error-message for="basic-email" visible>Enter an email address like name@example.com.</mj-error-message>
                    </div>
                """),
                css=_FORM_CSS + _code("""
                    .field { max-inline-size: 26rem; }
                """),
            ),
            ComponentExample(
                key="auto",
                title="Automatic, in an mj-form",
                description="<p><code>auto</code> messages for native inputs. Submit the empty form: both errors "
                            "show (the first with its own text, the second with the browser's message); typing a "
                            "valid value hides one; Reset hides them all.</p>",
                html=_code("""
                    <mj-form id="signup-form">
                      <div class="field">
                        <mj-label for="signup-email" required>Work email</mj-label>
                        <input id="signup-email" name="email" type="email" class="native" required>
                        <mj-error-message for="signup-email" auto>Enter your work email address.</mj-error-message>
                      </div>
                      <div class="field">
                        <mj-label for="signup-team" required>Team size</mj-label>
                        <input id="signup-team" name="team" type="number" min="1" max="500" class="native" required>
                        <mj-error-message for="signup-team" auto></mj-error-message>
                      </div>
                      <div class="actions">
                        <mj-button type="submit" variant="primary">Start trial</mj-button>
                        <mj-button type="reset">Reset</mj-button>
                      </div>
                    </mj-form>
                    <output id="demo-result" class="result">Submit the form.</output>
                """),
                css=_FORM_CSS + _code("""
                    mj-form { max-inline-size: 28rem; margin-block-end: var(--mj-space-4); }
                """),
                script=_code("""
                    const form = document.getElementById("signup-form")
                    const output = document.getElementById("demo-result")
                    form.addEventListener("mj-invalid", (event) => { if (event.target !== form) { return } output.textContent = "Invalid: " + event.detail.summary.map((entry) => entry.name).join(", ") })
                    form.addEventListener("mj-submit", (event) => { if (event.target !== form) { return } output.textContent = "Submitted " + JSON.stringify(event.detail.value) })
                    form.addEventListener("mj-reset", (event) => { if (event.target !== form) { return } output.textContent = "Reset." })
                """),
            ),
            ComponentExample(
                key="slots",
                title="Message attribute and icon slot",
                description="<p>An icon in the <code>icon</code> slot; the second message comes from the "
                            "<code>message</code> attribute, which replaces the element's content.</p>",
                html=_code("""
                    <div class="stack">
                      <div class="field">
                        <mj-label for="icon-card">Card number</mj-label>
                        <input id="icon-card" class="native" value="4111 1111">
                        <mj-error-message for="icon-card" visible>
                          <svg slot="icon" viewBox="0 0 16 16" width="14" height="14" aria-hidden="true">
                            <circle cx="8" cy="8" r="6.5" fill="currentColor"/>
                            <path d="M8 4.5v4.5M8 11v.5" stroke="var(--mj-surface)" stroke-width="1.6"/>
                          </svg>
                          The card number is too short.
                        </mj-error-message>
                      </div>
                      <div class="field">
                        <mj-label for="attr-code">Coupon</mj-label>
                        <input id="attr-code" class="native" value="SPRING">
                        <mj-error-message for="attr-code" visible message="This coupon expired on 31 March.">Content replaced by message</mj-error-message>
                      </div>
                    </div>
                """),
                css=_FORM_CSS + _STACK_CSS,
            ),
            ComponentExample(
                key="always-render",
                title="Reserved space",
                description="<p><code>always-render</code> keeps the message's space while hidden, so the layout "
                            "does not jump. Toggle it with the checkbox.</p>",
                html=_code("""
                    <div class="field">
                      <mj-label for="ar-name">Name</mj-label>
                      <input id="ar-name" class="native" value="Ada">
                      <mj-error-message id="ar-error" for="ar-name" always-render>Names must be unique in your workspace.</mj-error-message>
                      <p class="below">This line does not move.</p>
                    </div>
                    <label class="check"><input type="checkbox" id="ar-toggle"> Show the error</label>
                """),
                css=_FORM_CSS + _code("""
                    .field { max-inline-size: 26rem; }
                    .below { margin: 0; color: var(--mj-text-muted); }
                """),
                script=_code("""
                    const error = document.getElementById("ar-error")
                    document.getElementById("ar-toggle").addEventListener("change", (event) => { error.visible = event.target.checked })
                """),
            ),
            ComponentExample(
                key="events",
                title="Custom check (scripted)",
                description="<p>A 'confirm password' check: the script compares the two inputs on every "
                            "<code>input</code>, toggles <code>visible</code> (<code>mj-show</code> / "
                            "<code>mj-hide</code>) and sets the native custom validity so the form refuses to "
                            "submit. It types a mismatch, then the matching value, and submits.</p>",
                html=_code("""
                    <mj-form id="confirm-form">
                      <div class="field">
                        <mj-label for="pw-1" required>Password</mj-label>
                        <input id="pw-1" name="password" type="password" class="native" required>
                      </div>
                      <div class="field">
                        <mj-label for="pw-2" required>Confirm password</mj-label>
                        <input id="pw-2" type="password" class="native" required>
                        <mj-error-message id="pw-error" for="pw-2">The passwords do not match.</mj-error-message>
                      </div>
                      <div class="actions">
                        <mj-button type="submit" variant="primary">Set password</mj-button>
                        <mj-button type="reset">Reset</mj-button>
                      </div>
                    </mj-form>
                """),
                css=_FORM_CSS + _code("""
                    mj-form { max-inline-size: 26rem; }
                """),
                script=_code("""
                    const form = document.getElementById("confirm-form")
                    const first = document.getElementById("pw-1")
                    const second = document.getElementById("pw-2")
                    const error = document.getElementById("pw-error")
                    const check = () => {
                      const mismatch = second.value !== "" && second.value !== first.value
                      second.setCustomValidity(mismatch ? "The passwords do not match." : "")
                      error.visible = mismatch
                    }
                    first.addEventListener("input", check)
                    second.addEventListener("input", check)
                    form.addEventListener("mj-reset", (event) => { if (event.target !== form) { return } error.visible = false })
                    const type = (input, text) => { input.value = text; input.dispatchEvent(new Event("input", { bubbles: true })) }
                    type(first, "orange-cat-42")
                    type(second, "orange-cat")
                    form.submit()
                    type(second, "orange-cat-42")
                    form.submit()
                """),
            ),
        ],
        attributes=[
            _attr("for", "Id of the control the message belongs to."),
            _attr("visible", "Shows the message and marks the control invalid.", kind="boolean"),
            _attr("auto", "Shows and hides the message from the control's validity (driven by mj-form on submit and reset).", kind="boolean"),
            _attr("message", "Message text; replaces the element's own content."),
            _attr("always-render", "Keeps the message's space while hidden.", kind="boolean"),
        ],
        events=[
            ("mj-show", "The message became visible.", "{ message: string }"),
            ("mj-hide", "The message was hidden.", "{}"),
        ],
        slots=[
            ("", "The message text (used unless `message` is set).", "Please fix this field."),
            ("icon", "A leading icon.",
             '<svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true"><circle cx="8" cy="8" r="6" fill="currentColor"/></svg>'),
        ],
        properties=[
            ("visible", "boolean. Reflects `visible`."),
            ("text", "string. The message currently shown (read-only)."),
            ("control", "Element | null. The associated control (read-only)."),
        ],
        methods=[
            ("refresh(show)", "In `auto` mode: hides the message when the control is valid, shows it when invalid and `show` is true (used by mj-form)."),
        ],
        parts=[
            ("container", "The alert container."),
            ("icon", "Wrapper of the icon slot."),
            ("message", "Text from `message` or the control's validation message."),
        ],
        css_properties=[
            ("--mj-error-color", "Text colour (default var(--mj-color-danger))."),
            ("--mj-error-font-size", "Font size (default var(--mj-font-size-xs))."),
            ("--mj-error-gap", "Gap between icon and text (default var(--mj-space-1))."),
            ("--mj-error-icon-size", "Icon size (default var(--mj-space-4))."),
            ("--mj-error-margin-top", "Space above the message (default var(--mj-space-1))."),
        ],
    ),
    ComponentDoc(
        tag="mj-validation-summary",
        title="Validation Summary",
        group="text",
        summary="An error list for a form: each entry links to its invalid control, and it clears as fields are fixed.",
        description=_code("""
            <p><code>&lt;mj-validation-summary&gt;</code> lists a form's errors in a <code>role="alert"</code>
            box. Inside an <code>&lt;mj-form&gt;</code> it connects to that form; elsewhere <code>for</code> names
            the form's id. On <code>mj-invalid</code> it shows one entry per invalid control
            ('Label: message'), becomes <code>visible</code>, fires <code>mj-show</code> and takes focus (unless
            <code>focus-on-show="false"</code>; the form then does not focus the first field). Entries are pruned
            as their controls become valid on change or blur; while a mouse button or finger is down the pruning
            waits until it is released, so a button below the summary does not move away from a click that
            blurred the last invalid field. A successful submit or a reset clears it (<code>mj-hide</code>),
            unless a submit in the same task reported new errors (<code>form.reset(); form.submit()</code> ends
            with the new errors shown).</p>
            <p>Each entry is a link: activating it scrolls to the control, focuses it and fires
            <code>mj-error-click</code>. The heading is plural-aware ('1 error prevented…', 'N errors
            prevented…'), or <code>heading-text</code> with a <code>{count}</code> token, at
            <code>heading-level</code> 1-6; a slotted <code>heading</code> replaces it. With <code>manual</code> the
            summary ignores the form and shows only the <code>errors</code> you assign, e.g. from a server
            response.</p>
        """),
        how_to_use=_code("""
            <p>Put <code>&lt;mj-validation-summary slot="summary"&gt;</code> first inside the <code>mj-form</code>.
            Give controls ids so entries can link to them. For server-side errors use <code>manual</code> and set
            <code>errors</code> to <code>[{ controlId, label, message }]</code> (or <code>control</code>); set it to
            <code>[]</code> to hide the summary.</p>
        """),
        example="",
        examples=[
            ComponentExample(
                key="basic",
                title="Basic usage",
                description="<p>The script submits the empty form once, so the summary lists both fields and takes "
                            "focus. Click an entry to jump to its field; fix a field and its entry disappears when "
                            "you leave it; Save (or Enter in a field) and Reset clear the summary.</p>",
                html=_code("""
                    <mj-form id="profile-form">
                      <mj-validation-summary slot="summary"></mj-validation-summary>
                      <mj-text-field id="profile-name" name="name" label="Full name" required></mj-text-field>
                      <mj-typed-field id="profile-email" type="email" name="email" label="Email" required></mj-typed-field>
                      <div class="actions">
                        <mj-button type="submit" variant="primary">Save profile</mj-button>
                        <mj-button type="reset">Reset</mj-button>
                      </div>
                    </mj-form>
                """),
                css=_FORM_CSS + _code("""
                    mj-form { max-inline-size: 28rem; }
                """),
                script=_code("""
                    document.getElementById("profile-form").submit()
                """),
            ),
            ComponentExample(
                key="external",
                title="Outside the form (for)",
                description="<p>The summary sits above the form and connects with <code>for</code>; it uses "
                            "<code>heading-text</code> with <code>{count}</code> and <code>heading-level=\"3\"</code>. "
                            "Press Pay with empty fields.</p>",
                html=_code("""
                    <mj-validation-summary for="payment-form" heading-level="3" heading-text="{count} problems with your payment"></mj-validation-summary>
                    <mj-form id="payment-form">
                      <mj-masked-input id="pay-card" name="card" label="Card number" mask="9999 9999 9999 9999" show-mask required></mj-masked-input>
                      <mj-masked-input id="pay-expiry" name="expiry" label="Expiry" mask="99/99" show-mask required></mj-masked-input>
                      <mj-masked-input id="pay-cvc" name="cvc" label="CVC" mask="999" required></mj-masked-input>
                      <div class="actions"><mj-button type="submit" variant="primary">Pay</mj-button></div>
                    </mj-form>
                """),
                css=_FORM_CSS + _code("""
                    mj-form, mj-validation-summary { max-inline-size: 28rem; margin-block-end: var(--mj-space-4); }
                """),
            ),
            ComponentExample(
                key="manual",
                title="Manual errors from a server",
                description="<p><code>manual</code>: the form's own events are ignored. On <code>mj-submit</code> "
                            "the script simulates a server reply and assigns <code>errors</code>; the script "
                            "submits once at load. Click the entry (<code>mj-error-click</code>).</p>",
                html=_code("""
                    <mj-form id="register-form">
                      <mj-validation-summary id="server-summary" slot="summary" manual heading-text="The server rejected the form"></mj-validation-summary>
                      <mj-text-field id="register-user" name="username" label="Username" value="admin" required></mj-text-field>
                      <mj-typed-field id="register-email" type="email" name="email" label="Email" value="admin@example.com"></mj-typed-field>
                      <div class="actions"><mj-button type="submit" variant="primary">Register</mj-button></div>
                    </mj-form>
                """),
                css=_FORM_CSS + _code("""
                    mj-form { max-inline-size: 28rem; }
                """),
                script=_code("""
                    const form = document.getElementById("register-form")
                    const summary = document.getElementById("server-summary")
                    form.addEventListener("mj-submit", (event) => {
                      if (event.target !== form) { return }
                      const taken = ["admin", "root"].includes(event.detail.value.username[0])
                      setTimeout(() => {
                        summary.errors = taken ? [
                          { controlId: "register-user", label: "Username", message: "is already taken" },
                          { controlId: "register-email", label: "Email", message: "is already registered" },
                        ] : []
                        mjSandbox.log("server reply", { count: summary.count })
                      }, 300)
                    })
                    summary.addEventListener("mj-error-click", (event) => mjSandbox.log("jump to", { controlId: event.detail.controlId }))
                    form.submit()
                """),
            ),
            ComponentExample(
                key="slots",
                title="Icon and heading slots",
                description="<p>A custom <code>icon</code> and <code>heading</code>, <code>focus-on-show=\"false\"</code> "
                            "(the form focuses the first field instead), and <code>always-render</code> so the box "
                            "keeps its space when empty. Press Send with empty fields.</p>",
                html=_code("""
                    <mj-form id="feedback-form">
                      <mj-validation-summary slot="summary" focus-on-show="false" always-render>
                        <svg slot="icon" viewBox="0 0 16 16" width="18" height="18" aria-hidden="true">
                          <path d="M8 1l7 13H1z" fill="currentColor"/>
                        </svg>
                        <strong slot="heading">Almost there - please check these fields</strong>
                      </mj-validation-summary>
                      <mj-rating id="feedback-rating" name="rating" label="Rating" required></mj-rating>
                      <mj-textarea id="feedback-text" name="comment" label="Comment" required minlength="10"></mj-textarea>
                      <div class="actions">
                        <mj-button type="submit" variant="primary">Send</mj-button>
                        <mj-button type="reset">Reset</mj-button>
                      </div>
                    </mj-form>
                """),
                css=_FORM_CSS + _code("""
                    mj-form { max-inline-size: 28rem; }
                    mj-validation-summary svg { color: var(--mj-color-danger); }
                """),
            ),
            ComponentExample(
                key="events",
                title="Show, prune, click and hide (scripted)",
                description="<p>The script submits the empty form (<code>mj-show</code>), fixes one field and "
                            "fires <code>change</code> (its entry is pruned), clicks the remaining link "
                            "(<code>mj-error-click</code>), fixes it and submits (<code>mj-hide</code>).</p>",
                html=_code("""
                    <mj-form id="events-form">
                      <mj-validation-summary id="events-summary" slot="summary"></mj-validation-summary>
                      <mj-text-field id="events-city" name="city" label="City" required></mj-text-field>
                      <mj-number-field id="events-guests" name="guests" label="Guests" min="1" max="10" required></mj-number-field>
                      <div class="actions"><mj-button type="submit" variant="primary">Book</mj-button></div>
                    </mj-form>
                """),
                css=_FORM_CSS + _code("""
                    mj-form { max-inline-size: 28rem; }
                """),
                script=_code("""
                    const form = document.getElementById("events-form")
                    const summary = document.getElementById("events-summary")
                    form.submit()
                    mjSandbox.log("after submit", { count: summary.count, visible: summary.hasAttribute("visible") })
                    const city = document.getElementById("events-city")
                    city.value = "Porto"
                    city.dispatchEvent(new Event("change", { bubbles: true }))
                    mjSandbox.log("after fixing city", { count: summary.count, entries: summary.errors.map((entry) => entry.label) })
                    summary.shadowRoot.querySelector(".error-link").click()
                    document.getElementById("events-guests").value = "2"
                    form.submit()
                    await new Promise((resolve) => setTimeout(resolve, 50))
                    mjSandbox.log("after valid submit", { count: summary.count, visible: summary.hasAttribute("visible") })
                """),
            ),
        ],
        attributes=[
            _attr("for", "Id of the mj-form to follow; optional inside an mj-form."),
            _attr("manual", "Ignores the form; shows only the `errors` you assign.", kind="boolean"),
            _attr("visible", "Set while there are errors (managed by the component).", kind="boolean"),
            _attr("heading-text", "Heading text; `{count}` is replaced by the number of errors.",
                  values=["{count} errors", "Please fix {count} fields"]),
            _attr("heading-level", "Level of the generated heading (1-6).", kind="enum", values=["1", "2", "3", "4", "5", "6"], default="2"),
            _attr("focus-on-show", "`false` keeps focus where it is when errors appear.", kind="boolean", default="true"),
            _attr("always-render", "Keeps the box's space while there are no errors.", kind="boolean"),
        ],
        events=[
            ("mj-show", "Errors were assigned and the summary is shown.", "{ errors: object[], count: number }"),
            ("mj-hide", "The last error went away.", "{}"),
            ("mj-error-click", "An entry was activated (the control is focused).",
             "{ controlId: string, label: string, message: string, control: Element | null }"),
        ],
        slots=[
            ("icon", "Icon before the heading.",
             '<svg viewBox="0 0 16 16" width="18" height="18" aria-hidden="true"><path d="M8 1l7 13H1z" fill="currentColor"/></svg>'),
            ("heading", "Replaces the generated heading.", "<strong>Please check these fields</strong>"),
        ],
        properties=[
            ("errors", "{ control?, controlId?, name?, label, message }[]. The entries; assigning shows, focuses or hides the summary."),
            ("count", "number. Number of entries (read-only)."),
        ],
        methods=[
            ("refresh()", "Drops the entries whose controls are now valid."),
        ],
        parts=[
            ("container", "The alert box."),
            ("heading", "The generated heading."),
            ("list", "The entry list."),
            ("item", "One entry."),
            ("link", "The link inside an entry."),
        ],
        css_properties=[
            ("--mj-summary-bg", "Background (default var(--mj-color-danger-surface))."),
            ("--mj-summary-border-color", "Border colour (default var(--mj-color-danger))."),
            ("--mj-summary-border-radius", "Corner radius (default var(--mj-radius-md))."),
            ("--mj-summary-padding", "Inner padding (default var(--mj-space-4))."),
            ("--mj-summary-gap", "Space below the heading (default var(--mj-space-2))."),
            ("--mj-summary-heading-color", "Heading colour (default var(--mj-color-danger))."),
            ("--mj-summary-link-color", "Entry link colour (default var(--mj-accent))."),
        ],
    ),
    ComponentDoc(
        tag="mj-character-counter",
        title="Character Counter",
        group="text",
        summary="A live character or word counter for any control, with warning and over-limit states and throttled announcements.",
        description=_code("""
            <p><code>&lt;mj-character-counter&gt;</code> counts the value of the control named by
            <code>for</code> - a native input or textarea, or an <code>mj-*</code> control (through its bridged
            <code>input</code> / <code>change</code> events) - and recounts after a form reset. It counts
            characters (code points) or, with <code>unit="words"</code>, words.</p>
            <p>With <code>max</code>, <code>mode="remaining"</code> (default) shows what is left (negative when
            over) and any other mode shows the count; <code>format="used/max"</code> shows 'count / max'. The host
            gets <code>data-state="warning"</code> at <code>warn-at</code> percent and <code>error</code> at
            <code>error-at</code> percent (100 by default) or over the limit; over the limit the counter also
            describes the control and sets <code>aria-invalid</code> on it. The visible number is silent; a polite
            live region announces the remaining count inside the <code>announce-at</code> zone every
            <code>announce-interval</code> characters. The counter does not block input or submission.</p>
        """),
        how_to_use=_code("""
            <p>Place it after the control and set <code>for</code> and <code>max</code>. Use it with controls that
            do not enforce the limit themselves (no native <code>maxlength</code>), so the over-limit state can be
            reached. Customise <code>remaining-label</code> / <code>exceeded-label</code> with a
            <code>{count}</code> token; call <code>sync()</code> after setting the control's value from script.</p>
        """),
        example="",
        examples=[
            ComponentExample(
                key="basic",
                title="Basic usage",
                description="<p>A remaining-characters counter for a bio field with a warning at 80%. Type past "
                            "160 characters to reach the over-limit state.</p>",
                html=_code("""
                    <mj-textarea id="bio-field" name="bio" label="Bio" rows="3"
                      value="Product designer in Lisbon. I like typography, trains and very strong coffee."></mj-textarea>
                    <mj-character-counter for="bio-field" max="160" warn-at="80"></mj-character-counter>
                """),
                css=_code("""
                    mj-textarea { max-inline-size: 30rem; }
                """),
            ),
            ComponentExample(
                key="modes",
                title="Modes, formats and units",
                description="<p>Remaining (default), the used count, 'used / max', and a word count.</p>",
                html=_code("""
                    <div class="stack">
                      <div class="field">
                        <mj-label for="m-1">Remaining</mj-label>
                        <input id="m-1" class="native" value="Short title">
                        <mj-character-counter for="m-1" max="60"></mj-character-counter>
                      </div>
                      <div class="field">
                        <mj-label for="m-2">Used</mj-label>
                        <input id="m-2" class="native" value="Short title">
                        <mj-character-counter for="m-2" max="60" mode="used"></mj-character-counter>
                      </div>
                      <div class="field">
                        <mj-label for="m-3">Used / max</mj-label>
                        <input id="m-3" class="native" value="Short title">
                        <mj-character-counter for="m-3" max="60" mode="used" format="used/max"></mj-character-counter>
                      </div>
                      <div class="field">
                        <mj-label for="m-4">Words (max 50)</mj-label>
                        <textarea id="m-4" class="native" rows="3">Summaries are limited by words rather than characters.</textarea>
                        <mj-character-counter for="m-4" max="50" unit="words" format="used/max" mode="used"></mj-character-counter>
                      </div>
                    </div>
                """),
                css=_FORM_CSS + _STACK_CSS,
            ),
            ComponentExample(
                key="states",
                title="Warning, over the limit, disabled",
                description="<p>A field in the warning band, one over its limit with a custom "
                            "<code>exceeded-label</code> (the field is marked invalid), and a disabled counter that "
                            "no longer follows typing.</p>",
                html=_code("""
                    <div class="stack">
                      <div class="field">
                        <mj-label for="st-1">Headline (warning)</mj-label>
                        <input id="st-1" class="native" value="Our biggest launch yet, now with more">
                        <mj-character-counter for="st-1" max="40" warn-at="75" remaining-label="{count} left"></mj-character-counter>
                      </div>
                      <div class="field">
                        <mj-label for="st-2">SMS (over)</mj-label>
                        <textarea id="st-2" class="native" rows="2">Your parcel is out for delivery today between 9am and 1pm, reply STOP to opt out.</textarea>
                        <mj-character-counter for="st-2" max="70" format="used/max" mode="used" exceeded-label="{count} characters too many"></mj-character-counter>
                      </div>
                      <div class="field">
                        <mj-label for="st-3">Disabled counter</mj-label>
                        <input id="st-3" class="native" value="Typing here is not counted">
                        <mj-character-counter for="st-3" max="40" disabled></mj-character-counter>
                      </div>
                    </div>
                """),
                css=_FORM_CSS + _STACK_CSS + _code("""
                    mj-character-counter[data-state="error"] { font-weight: var(--mj-font-weight-bold); }
                """),
            ),
            ComponentExample(
                key="events",
                title="Counting events in a form (scripted)",
                description="<p>The script types longer and longer text into a native textarea: "
                            "<code>mj-count-change</code> every time, <code>mj-warn</code> at 80%, "
                            "<code>mj-exceed</code> over the limit and <code>mj-recover</code> when back under. "
                            "Submit refuses an over-limit message; Reset recounts.</p>",
                html=_code("""
                    <form id="demo-form" class="demo-form">
                      <div class="field">
                        <mj-label for="tweet">Post</mj-label>
                        <textarea id="tweet" name="post" class="native" rows="3"></textarea>
                        <mj-character-counter id="tweet-counter" for="tweet" max="40" warn-at="80" format="used/max" mode="used"></mj-character-counter>
                      </div>
                      <div class="actions">
                        <button type="submit">Post</button>
                        <button type="reset">Reset</button>
                      </div>
                      <output id="demo-result" class="result">Submit to see the form data.</output>
                    </form>
                """),
                css=_FORM_CSS,
                script=_NATIVE_FORM_SCRIPT + _code("""
                    const counter = document.getElementById("tweet-counter")
                    const area = document.getElementById("tweet")
                    form.addEventListener("submit", (event) => {
                      if (counter.exceeded) {
                        event.preventDefault()
                        event.stopImmediatePropagation()
                        output.textContent = "Too long: " + counter.current + " / 40"
                      }
                    }, { capture: true })
                    for (const text of ["Hello", "Hello world, this is a test", "Hello world, this is a test post", "Hello world, this is a test post that is far too long", "Hello again"]) {
                      area.value = text
                      area.dispatchEvent(new Event("input", { bubbles: true }))
                    }
                    mjSandbox.log("state", { current: counter.current, remaining: counter.remaining, exceeded: counter.exceeded })
                """),
            ),
        ],
        attributes=[
            _attr("for", "Id of the control to count."),
            _attr("max", "Limit; without it there are no states, thresholds or announcements.", kind="number"),
            _attr("mode", "`remaining` shows max minus the count; any other value shows the count.", kind="enum",
                  values=["remaining", "used"], default="remaining"),
            _attr("format", "`used/max` shows 'count / max'; absent shows a single number.", kind="enum", values=["used/max"]),
            _attr("unit", "What is counted (any other unit counts characters and is only named in announcements).",
                  kind="enum", values=["characters", "words"], default="characters"),
            _attr("warn-at", "Percentage of max for the warning state (and `mj-warn`).", kind="number"),
            _attr("error-at", "Percentage of max for the error state.", kind="number", default="100"),
            _attr("announce-at", "Percentage of max where announcements start.", kind="number", default="90"),
            _attr("announce-interval", "Inside the announce zone, announce every this many remaining.", kind="number", default="10"),
            _attr("remaining-label", "Announcement under the limit; `{count}` is replaced.", values=["{count} left", "{count} characters remaining"]),
            _attr("exceeded-label", "Announcement over the limit; `{count}` is replaced.", values=["{count} too many", "{count} over the limit"]),
            _attr("disabled", "Stops following the control's input (dimmed).", kind="boolean"),
        ],
        events=[
            ("mj-count-change", "The count changed through user input, a form reset or `sync()`.",
             "{ current: number, remaining: number | null, exceeded: boolean, unit: string }"),
            ("mj-warn", "The count crossed `warn-at` upwards.", "{ current: number, remaining: number, threshold: number }"),
            ("mj-exceed", "The count went over `max`.", "{ current: number, max: number }"),
            ("mj-recover", "The count came back to `max` or below.", "{ current: number, max: number }"),
        ],
        slots=[],
        properties=[
            ("current", "number. The current count (read-only)."),
            ("remaining", "number | null. max minus the count; null without max (read-only)."),
            ("exceeded", "boolean. Over the limit (read-only)."),
            ("control", "Element | null. The counted control (read-only)."),
        ],
        methods=[
            ("sync()", "Recounts and fires the events; use it after setting the control's value from script."),
        ],
        parts=[
            ("counter", "The counter text."),
            ("count", "The number."),
            ("separator", "The ' / ' of `format=used/max`."),
            ("max", "The max of `format=used/max`."),
        ],
        css_properties=[
            ("--mj-counter-font-size", "Font size (default var(--mj-font-size-xs))."),
            ("--mj-counter-color", "Normal colour (default var(--mj-text-muted))."),
            ("--mj-counter-warn-color", "Warning colour (default var(--mj-color-warning))."),
            ("--mj-counter-error-color", "Error colour (default var(--mj-color-danger))."),
            ("--mj-counter-disabled-color", "Colour when disabled (default var(--mj-text-muted))."),
        ],
    ),
]
