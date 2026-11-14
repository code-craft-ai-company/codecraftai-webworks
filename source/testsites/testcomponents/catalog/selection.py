"""
    selection.py

    Catalog entries for the 'Selection & Pickers' component group.

    Each ComponentDoc describes one selection or picker component: its tag, purpose,
    typed attributes, events, slots, properties, methods, parts and custom properties,
    and a gallery of live examples (ComponentExample) that exercise the component's real
    attribute names, child elements and behaviour on its sandbox page.
"""

from testcomponents.catalog.componentdoc import AttributeDoc
from testcomponents.catalog.componentdoc import ComponentDoc
from testcomponents.catalog.componentdoc import ComponentExample


COMPONENTS = [
    ComponentDoc(
        tag="mj-select",
        title="Select",
        group="selection",
        summary=(
            "Single-choice dropdown built from &lt;mj-option&gt; children, with option groups, "
            "typeahead and form participation."
        ),
        description=(
            "<p><code>&lt;mj-select&gt;</code> is a styled, accessible replacement for the native "
            "<code>&lt;select&gt;</code>. It renders a trigger button (<code>role=\"combobox\"</code>) "
            "that opens a floating listbox built from the <code>&lt;mj-option&gt;</code> descendants "
            "of the element. <code>&lt;mj-option&gt;</code> and <code>&lt;mj-optgroup&gt;</code> are "
            "plain markup the select reads (they are not custom elements and are not slotted): each "
            "option shows its <code>label</code> attribute or its text as plain text, and its value is "
            "its <code>value</code> attribute or, without one, its text. Options inside an "
            "<code>&lt;mj-optgroup label=\"...\"&gt;</code> are shown under a group heading; a "
            "<code>disabled</code> group disables its options.</p>"
            "<p>A MutationObserver follows the options, so options added, removed or relabelled after "
            "the first render (for example once a fetch resolves) appear without re-creating the "
            "element, and a <code>value</code> set before its option exists shows the label once the "
            "option arrives.</p>"
            "<p>The <code>value</code> attribute is the <em>default</em> value, the one a form reset "
            "restores; the live value is the <code>value</code> property. A user selection changes "
            "the property and the submitted form value and fires <code>mj-change</code>; it never "
            "rewrites the attribute. Picking the option that is already selected only closes the "
            "popup.</p>"
            "<p>Keyboard: Enter, Space, ArrowDown or ArrowUp open the list; ArrowDown / ArrowUp move "
            "over enabled options, Home / End jump to the first / last enabled option, Enter or Space "
            "select, Escape closes and returns focus to the trigger, Tab closes. Typing letters "
            "(also on the closed trigger) jumps to the first option starting with them.</p>"
        ),
        how_to_use=(
            "<p>Put <code>&lt;mj-option value=\"...\"&gt;</code> elements (optionally inside "
            "<code>&lt;mj-optgroup label=\"...\"&gt;</code>) between the tags. Name the control with "
            "<code>label</code>, <code>aria-label</code>, <code>aria-labelledby</code> or an "
            "associated <code>&lt;label&gt;</code> (wrapping or <code>for=</code>). Use "
            "<code>value</code> for the initial selection and <code>placeholder</code> for the empty "
            "trigger text. In a form give it a <code>name</code>; <code>required</code> makes it "
            "invalid until an option is chosen. Read the live value from <code>.value</code> or from "
            "<code>mj-change</code> (<code>{ value, previousValue, option }</code>). Options with "
            "rich content are shown as plain text.</p>"
        ),
        example="",
        attributes=[
            AttributeDoc(name="value", description="Default (initial) value; form reset restores it. User selections do not rewrite it.",
                         kind="string", values=["apple", "banana", "cherry"]),
            AttributeDoc(name="placeholder", description="Trigger text while no option matches the value.",
                         kind="string", values=["Choose a fruit", "Select..."]),
            AttributeDoc(name="label", description="Accessible name of the combobox; wins over `aria-label`, `aria-labelledby` and a `<label>`.",
                         kind="string", values=["Fruit"]),
            AttributeDoc(name="aria-label", description="Accessible name when `label` is absent.", kind="string"),
            AttributeDoc(name="aria-labelledby", description="Ids of elements whose text names the combobox (when `label` and `aria-label` are absent).",
                         kind="string"),
            AttributeDoc(name="name", description="Form field name the value is submitted under.", kind="string"),
            AttributeDoc(name="open", description="Shows the popup. Setting it directly skips the cancelable `mj-open` event; the component removes it when it closes.",
                         kind="boolean"),
            AttributeDoc(name="disabled", description="Disables the trigger (also when an ancestor `<fieldset disabled>`); closes an open popup.",
                         kind="boolean"),
            AttributeDoc(name="readonly", description="The value is shown but the popup does not open.", kind="boolean"),
            AttributeDoc(name="required", description="Invalid (valueMissing) while the value is empty; sets `aria-required`.",
                         kind="boolean"),
            AttributeDoc(name="required-message", description="Validation message used instead of the default when `required` fails.",
                         kind="string", values=["Please choose a fruit."]),
            AttributeDoc(name="invalid", description="Forces the invalid styling and `aria-invalid`.", kind="boolean"),
            AttributeDoc(name="size", description="Trigger height and font size.", kind="enum",
                         values=["sm", "md", "lg"], default="md"),
            AttributeDoc(name="block", description="Display as a block that fills the inline size of its container.",
                         kind="boolean"),
        ],
        events=[
            ("mj-change", "The user selected a different option (not fired for `value` assignments or re-selecting the current option).",
             "{ value: string, previousValue: string, option: Element | null }"),
            ("change", "Plain `Event` fired right after every `mj-change`, for native-style listeners.", ""),
            ("mj-open", "Cancelable; fired before the popup opens from a click, a key or `open = true`. `preventDefault()` keeps it closed.",
             "{}"),
            ("mj-close", "The popup closed (selection, Escape, Tab, outside click, `open = false`, disabling).", "{}"),
        ],
        examples=[
            ComponentExample(
                key="basic",
                title="Basic usage",
                description=(
                    "<p>A named select with a placeholder and a disabled option. Click the trigger or "
                    "focus it and press ArrowDown; picking an option logs <code>mj-change</code>.</p>"
                ),
                html=(
                    '<mj-select label="Fruit" placeholder="Choose a fruit">\n'
                    '  <mj-option value="apple">Apple</mj-option>\n'
                    '  <mj-option value="banana">Banana</mj-option>\n'
                    '  <mj-option value="cherry">Cherry</mj-option>\n'
                    '  <mj-option value="mango">Mango</mj-option>\n'
                    '  <mj-option value="durian" disabled>Durian (out of season)</mj-option>\n'
                    '</mj-select>'
                ),
                css="body { padding: var(--mj-space-4); }",
                height=320,
            ),
            ComponentExample(
                key="option-groups",
                title="Option groups",
                description=(
                    "<p>Options grouped with <code>&lt;mj-optgroup&gt;</code>; the last group is "
                    "<code>disabled</code>. The initial value comes from the <code>value</code> "
                    "attribute and the visible <code>&lt;label for&gt;</code> names the control. The "
                    "popup is open on load.</p>"
                ),
                html=(
                    '<label for="tz">Time zone</label>\n'
                    '<mj-select id="tz" value="europe/paris" open>\n'
                    '  <mj-optgroup label="Europe">\n'
                    '    <mj-option value="europe/london">London (UTC+0)</mj-option>\n'
                    '    <mj-option value="europe/paris">Paris (UTC+1)</mj-option>\n'
                    '    <mj-option value="europe/helsinki">Helsinki (UTC+2)</mj-option>\n'
                    '  </mj-optgroup>\n'
                    '  <mj-optgroup label="Americas">\n'
                    '    <mj-option value="america/new-york">New York (UTC-5)</mj-option>\n'
                    '    <mj-option value="america/chicago">Chicago (UTC-6)</mj-option>\n'
                    '    <mj-option value="america/los-angeles">Los Angeles (UTC-8)</mj-option>\n'
                    '  </mj-optgroup>\n'
                    '  <mj-optgroup label="Asia (coming soon)" disabled>\n'
                    '    <mj-option value="asia/tokyo">Tokyo (UTC+9)</mj-option>\n'
                    '  </mj-optgroup>\n'
                    '</mj-select>'
                ),
                css=(
                    "body { padding: var(--mj-space-4); }\n"
                    "label { display: block; margin-block-end: var(--mj-space-1); }\n"
                    "mj-select { inline-size: 18rem; }\n"
                ),
                height=460,
            ),
            ComponentExample(
                key="states",
                title="Sizes and states",
                description=(
                    "<p>The three <code>size</code> values, a preselected value, and the "
                    "<code>disabled</code>, <code>readonly</code> and <code>invalid</code> states. The "
                    "last one is <code>block</code> and fills the row.</p>"
                ),
                html=(
                    '<div class="grid">\n'
                    '  <div class="field"><label for="st-sm">Small</label>\n'
                    '    <mj-select id="st-sm" size="sm" value="m">\n'
                    '      <mj-option value="s">S</mj-option><mj-option value="m">M</mj-option><mj-option value="l">L</mj-option>\n'
                    '    </mj-select></div>\n'
                    '  <div class="field"><label for="st-md">Medium (default)</label>\n'
                    '    <mj-select id="st-md" value="m">\n'
                    '      <mj-option value="s">S</mj-option><mj-option value="m">M</mj-option><mj-option value="l">L</mj-option>\n'
                    '    </mj-select></div>\n'
                    '  <div class="field"><label for="st-lg">Large</label>\n'
                    '    <mj-select id="st-lg" size="lg" value="m">\n'
                    '      <mj-option value="s">S</mj-option><mj-option value="m">M</mj-option><mj-option value="l">L</mj-option>\n'
                    '    </mj-select></div>\n'
                    '  <div class="field"><label for="st-disabled">Disabled</label>\n'
                    '    <mj-select id="st-disabled" disabled value="eu">\n'
                    '      <mj-option value="eu">Europe</mj-option><mj-option value="us">United States</mj-option>\n'
                    '    </mj-select></div>\n'
                    '  <div class="field"><label for="st-readonly">Read-only</label>\n'
                    '    <mj-select id="st-readonly" readonly value="us">\n'
                    '      <mj-option value="eu">Europe</mj-option><mj-option value="us">United States</mj-option>\n'
                    '    </mj-select></div>\n'
                    '  <div class="field"><label for="st-invalid">Invalid</label>\n'
                    '    <mj-select id="st-invalid" invalid placeholder="Pick a region">\n'
                    '      <mj-option value="eu">Europe</mj-option><mj-option value="us">United States</mj-option>\n'
                    '    </mj-select></div>\n'
                    '</div>\n'
                    '<div class="field"><label for="st-block">Block</label>\n'
                    '  <mj-select id="st-block" block placeholder="Fills the available inline size">\n'
                    '    <mj-option value="a">Annual plan</mj-option><mj-option value="m">Monthly plan</mj-option>\n'
                    '  </mj-select></div>'
                ),
                css=(
                    "body { padding: var(--mj-space-4); }\n"
                    ".grid { display: flex; flex-wrap: wrap; gap: var(--mj-space-4); align-items: end;\n"
                    "  margin-block-end: var(--mj-space-4); }\n"
                    ".field { display: flex; flex-direction: column; gap: var(--mj-space-1);\n"
                    "  min-inline-size: 9rem; }\n"
                ),
                height=320,
            ),
            ComponentExample(
                key="form",
                title="Form participation",
                description=(
                    "<p>Two selects in a <code>&lt;form&gt;</code>. <em>Size</em> is "
                    "<code>required</code> with a custom <code>required-message</code>: Order without "
                    "choosing one and the browser blocks the submit. Submitting logs the "
                    "<code>FormData</code>; Reset restores each <code>value</code> attribute.</p>"
                ),
                html=(
                    '<form id="order-form">\n'
                    '  <label for="order-size">Pizza size</label>\n'
                    '  <mj-select id="order-size" name="size" required required-message="Pick a size to continue." placeholder="Select a size">\n'
                    '    <mj-option value="s">Small (25 cm)</mj-option>\n'
                    '    <mj-option value="m">Medium (30 cm)</mj-option>\n'
                    '    <mj-option value="l">Large (35 cm)</mj-option>\n'
                    '  </mj-select>\n'
                    '  <label for="order-crust">Crust</label>\n'
                    '  <mj-select id="order-crust" name="crust" value="classic">\n'
                    '    <mj-option value="classic">Classic</mj-option>\n'
                    '    <mj-option value="thin">Thin and crispy</mj-option>\n'
                    '    <mj-option value="stuffed">Cheese-stuffed</mj-option>\n'
                    '  </mj-select>\n'
                    '  <div class="actions">\n'
                    '    <button type="submit">Order</button>\n'
                    '    <button type="reset">Reset</button>\n'
                    '  </div>\n'
                    '  <output id="order-out">Nothing submitted yet.</output>\n'
                    '</form>'
                ),
                css=(
                    "body { padding: var(--mj-space-4); }\n"
                    "form { display: grid; gap: var(--mj-space-2); max-inline-size: 18rem; }\n"
                    ".actions { display: flex; gap: var(--mj-space-2); margin-block-start: var(--mj-space-2); }\n"
                    "output { color: var(--mj-text-muted); font-size: var(--mj-font-size-sm); }\n"
                ),
                script=(
                    'const form = document.getElementById("order-form")\n'
                    'const out = document.getElementById("order-out")\n'
                    'const size = document.getElementById("order-size")\n'
                    'form.addEventListener("submit", (event) => {\n'
                    '  event.preventDefault()\n'
                    '  const data = Object.fromEntries(new FormData(form))\n'
                    '  out.textContent = "Submitted: " + JSON.stringify(data)\n'
                    '  mjSandbox.log("submit", data)\n'
                    '})\n'
                    'form.addEventListener("reset", () => {\n'
                    '  out.textContent = "Reset to the default values."\n'
                    '  mjSandbox.log("reset", {})\n'
                    '})\n'
                    '// validity is read without checkValidity(), which would mark the field as user-invalid\n'
                    'mjSandbox.log("initial validity", { valid: size.validity.valid, message: size.validationMessage })\n'
                ),
                height=380,
            ),
            ComponentExample(
                key="events",
                title="Dynamic options and events",
                description=(
                    "<p>The options arrive 500 ms after load (as from a fetch); the script then sets "
                    "<code>value</code> (no event), opens the list with <code>open = true</code> "
                    "(<code>mj-open</code>) and presses ArrowDown and Enter on the trigger, which logs "
                    "<code>mj-change</code> and <code>mj-close</code>. Use the button to add more "
                    "options.</p>"
                ),
                html=(
                    '<mj-select id="demo-project" label="Project" placeholder="Loading projects...">\n'
                    '</mj-select>\n'
                    '<button type="button" id="add-project">Add a project</button>'
                ),
                css=(
                    "body { padding: var(--mj-space-4); display: flex; gap: var(--mj-space-3); align-items: center; }\n"
                    "mj-select { inline-size: 16rem; }\n"
                ),
                script=(
                    'const select = document.getElementById("demo-project")\n'
                    'const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms))\n'
                    'const addOption = (value, label) => {\n'
                    '  const option = document.createElement("mj-option")\n'
                    '  option.setAttribute("value", value)\n'
                    '  option.textContent = label\n'
                    '  select.append(option)\n'
                    '}\n'
                    'const extra = [["delta", "Delta rollout"], ["echo", "Echo analytics"], ["foxtrot", "Foxtrot billing"]]\n'
                    'document.getElementById("add-project").addEventListener("click", (event) => {\n'
                    '  const next = extra.shift()\n'
                    '  if (next !== undefined) {\n'
                    '    addOption(next[0], next[1])\n'
                    '    mjSandbox.log("option added", { value: next[0], count: select.options.length })\n'
                    '  }\n'
                    '  event.target.disabled = extra.length === 0\n'
                    '})\n'
                    '\n'
                    'await wait(500)\n'
                    'addOption("atlas", "Atlas website")\n'
                    'addOption("borealis", "Borealis mobile app")\n'
                    'addOption("cosmos", "Cosmos data platform")\n'
                    'select.setAttribute("placeholder", "Choose a project")\n'
                    'await wait(0)\n'
                    'select.value = "atlas"\n'
                    'mjSandbox.log("value set", { value: select.value, label: select.selectedOption.textContent })\n'
                    'select.open = true\n'
                    'await wait(300)\n'
                    'const trigger = select.shadowRoot.querySelector("[part=trigger]")\n'
                    'const press = (key) => trigger.dispatchEvent(new KeyboardEvent("keydown", { key: key, bubbles: true }))\n'
                    'press("ArrowDown")\n'
                    'press("Enter")\n'
                ),
                height=320,
            ),
            ComponentExample(
                key="empty",
                title="No options",
                description=(
                    "<p>A select without options shows a status row in its popup: the "
                    "<code>no-results</code> slot replaces the default text \"No options\". The first "
                    "select is open on load; open the second to see the default text.</p>"
                ),
                html=(
                    '<mj-select label="Saved report" placeholder="No saved reports" open>\n'
                    '  <span slot="no-results">You have not saved any reports yet.</span>\n'
                    '</mj-select>\n'
                    '<mj-select label="Archived report" placeholder="Nothing archived"></mj-select>'
                ),
                css=(
                    "body { padding: var(--mj-space-4); display: flex; gap: var(--mj-space-6, 2rem); align-items: start; }\n"
                    "mj-select { inline-size: 16rem; }\n"
                ),
                height=240,
            ),
        ],
        slots=[
            ("no-results", "Text of the status row shown in the popup while the select has no options (default \"No options\"). Only visible when there are no options.",
             "<span>Nothing to choose from yet.</span>"),
        ],
        properties=[
            ("value", "string. The live value; assigning it updates the trigger and the selected option (also for an option that arrives later) and the form value, without `mj-change`."),
            ("open", "boolean. Whether the popup is open; `true` opens it like a click (respects disabled/readonly and `mj-open`), `false` closes it."),
            ("options", "Element[], read-only. Every `<mj-option>` of the select in document order."),
            ("selectedOption", "Element | null, read-only. The `<mj-option>` that carries the current value."),
            ("disabled", "boolean. Reflects the `disabled` attribute."),
            ("form", "HTMLFormElement | null, read-only. The owning form."),
            ("validity", "ValidityState, read-only. `valueMissing` while `required` and empty."),
            ("validationMessage", "string, read-only. The current validation message."),
        ],
        methods=[
            ("focus()", "Focuses the trigger button."),
            ("checkValidity() -> boolean", "Runs constraint validation; an invalid result fires `invalid` and shows the invalid styling."),
            ("reportValidity() -> boolean", "Like `checkValidity()` and also shows the browser's validation message at the trigger."),
        ],
        parts=[
            ("trigger", "The combobox button."),
            ("selected-label", "The text inside the trigger (selected label or placeholder)."),
            ("chevron", "The arrow icon of the trigger."),
            ("popup", "The floating panel."),
            ("listbox", "The `role=listbox` container inside the popup."),
            ("option", "One option row."),
            ("option-label", "The text of an option row."),
            ("optgroup", "The `role=group` container of an `<mj-optgroup>`."),
            ("optgroup-label", "The heading of an option group."),
            ("no-results", "The status row shown when there are no options."),
        ],
        css_properties=[
            ("--mj-select-border-radius", "Corner radius of the trigger and the popup (default `--mj-radius-md`)."),
            ("--mj-select-popup-min-width", "Minimum popup width (default: the trigger's width)."),
            ("--mj-select-popup-max-height", "Maximum height of the option list before it scrolls (default 18rem)."),
            ("--mj-select-option-padding", "Padding of option rows (default `--mj-space-2` `--mj-space-3`)."),
        ],
    ),
    ComponentDoc(
        tag="mj-listbox",
        title="Listbox",
        group="selection",
        summary="Always-visible scrollable list with single or multiple selection and form participation.",
        description=(
            "<p><code>&lt;mj-listbox&gt;</code> renders a permanently visible, scrollable list "
            "(<code>role=\"listbox\"</code>) built from the <code>&lt;mj-option&gt;</code> "
            "descendants of the element. Unlike <code>&lt;mj-select&gt;</code> there is no trigger "
            "or popup. <code>&lt;mj-option&gt;</code> is plain markup the listbox reads (it is not "
            "slotted): each option shows its <code>label</code> attribute or its text as plain text "
            "and stands for its <code>value</code> attribute or, without one, its text; "
            "<code>disabled</code> options are skipped. A MutationObserver follows the options, so "
            "options added, removed or relabelled later appear without re-creating the element. "
            "Options inside <code>&lt;mj-optgroup label=\"...\"&gt;</code> are listed under that "
            "heading in a <code>role=\"group\"</code>; a <code>disabled</code> group disables its "
            "options. A selected option is tinted with the accent colour and shows a check mark in "
            "both modes.</p>"
            "<p>Single mode: a click, Enter or Space selects the active option. "
            "<code>multiple</code> mode shows a check mark per option: a plain click or Space toggles "
            "one option and makes it the range anchor, Shift+click / Shift+Space and "
            "Shift+ArrowUp/Down select the range from the anchor, Ctrl/Cmd+A selects every enabled "
            "option (or clears them all when all are selected). ArrowUp/Down, Home and End move the "
            "active option (firing <code>mj-option-focus</code>); typing a letter jumps to the next "
            "option starting with it.</p>"
            "<p>The <code>value</code> attribute is the <em>default</em> selection (a comma-separated "
            "list in multiple mode) that a form reset restores; the live selection is the "
            "<code>value</code> / <code>selectedValues</code> properties and survives moving the "
            "element in the DOM. The form value is the comma-joined selection.</p>"
        ),
        how_to_use=(
            "<p>Put <code>&lt;mj-option value=\"...\"&gt;</code> elements between the tags and name "
            "the list with <code>label</code>, <code>aria-label</code>, <code>aria-labelledby</code> "
            "or an associated <code>&lt;label&gt;</code>. Add <code>multiple</code> for "
            "multi-select and <code>value=\"a,b\"</code> to preselect. Give it a <code>name</code> "
            "inside a form; <code>required</code> makes an empty selection invalid (message \"At "
            "least one selection is required.\" unless <code>required-message</code> gives one). Listen for "
            "<code>mj-change</code> (<code>{ value, values, previousValues }</code>); assigning "
            "<code>.value</code> changes the selection without an event. Set the list height with "
            "<code>--mj-listbox-min-height</code> / <code>--mj-listbox-max-height</code>.</p>"
        ),
        example="",
        attributes=[
            AttributeDoc(name="value", description="Default selection: one value, or a comma-separated list with `multiple`. Form reset restores it.",
                         kind="string", values=["green", "red,blue"]),
            AttributeDoc(name="multiple", description="Multi-select with check marks, range selection and Ctrl/Cmd+A. Switching it resets the selection to the `value` attribute.",
                         kind="boolean"),
            AttributeDoc(name="label", description="Accessible name of the list; wins over `aria-label`, `aria-labelledby` and a `<label>`.",
                         kind="string", values=["Favourite colour"]),
            AttributeDoc(name="aria-label", description="Accessible name when `label` is absent.", kind="string"),
            AttributeDoc(name="aria-labelledby", description="Ids of elements whose text names the list (when `label` and `aria-label` are absent).",
                         kind="string"),
            AttributeDoc(name="name", description="Form field name; the comma-joined selection is submitted under it.",
                         kind="string"),
            AttributeDoc(name="disabled", description="Dims the list, removes it from the tab order and ignores input (also from an ancestor `<fieldset disabled>`).",
                         kind="boolean"),
            AttributeDoc(name="readonly", description="The selection cannot change; the active option still moves.",
                         kind="boolean"),
            AttributeDoc(name="required", description="Invalid (valueMissing) while nothing is selected; sets `aria-required`.",
                         kind="boolean"),
            AttributeDoc(name="required-message", description="Validation message used instead of the default (\"At least one selection is required.\") when `required` fails.",
                         kind="string", values=["Choose at least one colour."]),
            AttributeDoc(name="invalid", description="Forces the invalid border and `aria-invalid`.", kind="boolean"),
            AttributeDoc(name="size", description="Option row height and font size.", kind="enum",
                         values=["sm", "md", "lg"], default="md"),
        ],
        events=[
            ("mj-change", "The user changed the selection (click, key, range, Ctrl/Cmd+A). Not fired for `value` assignments.",
             "{ value: string, values: string[], previousValues: string[] }"),
            ("change", "Plain `Event` fired right after every `mj-change`, for native-style listeners.", ""),
            ("mj-option-focus", "The active option moved by keyboard (arrows, Home/End, typeahead) without a selection change.",
             "{ option: { id: string, value: string, label: string, disabled: boolean, index: number, el: Element } }"),
        ],
        examples=[
            ComponentExample(
                key="basic",
                title="Basic usage",
                description=(
                    "<p>A single-select list with a preselected value and a disabled option. Click an "
                    "option, or focus the list and use the arrow keys and Enter.</p>"
                ),
                html=(
                    '<mj-listbox label="Favourite colour" value="green">\n'
                    '  <mj-option value="red">Red</mj-option>\n'
                    '  <mj-option value="green">Green</mj-option>\n'
                    '  <mj-option value="blue">Blue</mj-option>\n'
                    '  <mj-option value="yellow">Yellow</mj-option>\n'
                    '  <mj-option value="purple" disabled>Purple (sold out)</mj-option>\n'
                    '</mj-listbox>'
                ),
                css="body { padding: var(--mj-space-4); }\nmj-listbox { inline-size: 16rem; }\n",
            ),
            ComponentExample(
                key="multiple",
                title="Multiple selection",
                description=(
                    "<p><code>multiple</code> with two preselected values. A click or Space toggles one "
                    "option, Shift+click or Shift+Arrow selects a range, Ctrl/Cmd+A selects all (press "
                    "it again to clear). The current selection is shown below the list.</p>"
                ),
                html=(
                    '<mj-listbox id="perms" multiple label="Permissions" value="view,comment">\n'
                    '  <mj-option value="view">View files</mj-option>\n'
                    '  <mj-option value="comment">Comment</mj-option>\n'
                    '  <mj-option value="edit">Edit</mj-option>\n'
                    '  <mj-option value="share">Share with others</mj-option>\n'
                    '  <mj-option value="export">Export</mj-option>\n'
                    '  <mj-option value="delete" disabled>Delete (owners only)</mj-option>\n'
                    '</mj-listbox>\n'
                    '<p class="hint">Selected: <output id="perms-out">view, comment</output></p>'
                ),
                css=(
                    "body { padding: var(--mj-space-4); }\n"
                    "mj-listbox { inline-size: 18rem; }\n"
                    ".hint { color: var(--mj-text-muted); font-size: var(--mj-font-size-sm); }\n"
                ),
                script=(
                    'const list = document.getElementById("perms")\n'
                    'const out = document.getElementById("perms-out")\n'
                    'list.addEventListener("mj-change", (event) => {\n'
                    '  out.textContent = event.detail.values.join(", ") || "(none)"\n'
                    '})\n'
                ),
            ),
            ComponentExample(
                key="states",
                title="Sizes and states",
                description=(
                    "<p><code>size=\"sm\"</code> and <code>size=\"lg\"</code> rows, and the "
                    "<code>disabled</code>, <code>readonly</code> (multiple) and <code>invalid</code> "
                    "states. The lists are named by <code>&lt;label for&gt;</code>.</p>"
                ),
                html=(
                    '<div class="grid">\n'
                    '  <div class="field"><label for="lb-sm">Small rows</label>\n'
                    '    <mj-listbox id="lb-sm" size="sm" value="b">\n'
                    '      <mj-option value="a">Alpha</mj-option><mj-option value="b">Bravo</mj-option><mj-option value="c">Charlie</mj-option>\n'
                    '    </mj-listbox></div>\n'
                    '  <div class="field"><label for="lb-lg">Large rows</label>\n'
                    '    <mj-listbox id="lb-lg" size="lg" value="b">\n'
                    '      <mj-option value="a">Alpha</mj-option><mj-option value="b">Bravo</mj-option><mj-option value="c">Charlie</mj-option>\n'
                    '    </mj-listbox></div>\n'
                    '  <div class="field"><label for="lb-disabled">Disabled</label>\n'
                    '    <mj-listbox id="lb-disabled" disabled value="a">\n'
                    '      <mj-option value="a">Alpha</mj-option><mj-option value="b">Bravo</mj-option><mj-option value="c">Charlie</mj-option>\n'
                    '    </mj-listbox></div>\n'
                    '  <div class="field"><label for="lb-readonly">Read-only (multiple)</label>\n'
                    '    <mj-listbox id="lb-readonly" readonly multiple value="a,c">\n'
                    '      <mj-option value="a">Alpha</mj-option><mj-option value="b">Bravo</mj-option><mj-option value="c">Charlie</mj-option>\n'
                    '    </mj-listbox></div>\n'
                    '  <div class="field"><label for="lb-invalid">Invalid</label>\n'
                    '    <mj-listbox id="lb-invalid" invalid>\n'
                    '      <mj-option value="a">Alpha</mj-option><mj-option value="b">Bravo</mj-option><mj-option value="c">Charlie</mj-option>\n'
                    '    </mj-listbox></div>\n'
                    '</div>'
                ),
                css=(
                    "body { padding: var(--mj-space-4); }\n"
                    ".grid { display: flex; flex-wrap: wrap; gap: var(--mj-space-4); }\n"
                    ".field { display: flex; flex-direction: column; gap: var(--mj-space-1); inline-size: 11rem; }\n"
                ),
            ),
            ComponentExample(
                key="groups",
                title="Option groups",
                description=(
                    "<p>Options inside <code>&lt;mj-optgroup label=\"...\"&gt;</code> are listed under "
                    "the group heading (a <code>role=\"group\"</code> named by it); the "
                    "<code>disabled</code> group disables all of its options. Arrow keys move across "
                    "the groups and skip the disabled ones.</p>"
                ),
                html=(
                    '<mj-listbox id="demo-regions" label="Data centre" value="fra">\n'
                    '  <mj-optgroup label="Europe">\n'
                    '    <mj-option value="fra">Frankfurt</mj-option>\n'
                    '    <mj-option value="dub">Dublin</mj-option>\n'
                    '  </mj-optgroup>\n'
                    '  <mj-optgroup label="Americas">\n'
                    '    <mj-option value="iad">Virginia</mj-option>\n'
                    '    <mj-option value="gru">S&atilde;o Paulo</mj-option>\n'
                    '  </mj-optgroup>\n'
                    '  <mj-optgroup label="Asia (coming soon)" disabled>\n'
                    '    <mj-option value="nrt">Tokyo</mj-option>\n'
                    '  </mj-optgroup>\n'
                    '</mj-listbox>'
                ),
                css=(
                    "body { padding: var(--mj-space-4); }\n"
                    "mj-listbox { inline-size: 16rem; --mj-listbox-max-height: 20rem; }\n"
                ),
            ),
            ComponentExample(
                key="form",
                title="Form participation",
                description=(
                    "<p><em>Topics</em> is <code>multiple</code> and <code>required</code> with a "
                    "<code>required-message</code>: Subscribe with nothing selected and the browser "
                    "blocks the submit. Submitting logs the <code>FormData</code> (the multiple "
                    "selection is one comma-joined entry); Reset restores the <code>value</code> "
                    "attributes.</p>"
                ),
                html=(
                    '<form id="newsletter">\n'
                    '  <label for="topics">Topics</label>\n'
                    '  <mj-listbox id="topics" name="topics" multiple required required-message="Choose at least one topic.">\n'
                    '    <mj-option value="releases">Product releases</mj-option>\n'
                    '    <mj-option value="security">Security advisories</mj-option>\n'
                    '    <mj-option value="events">Events and webinars</mj-option>\n'
                    '    <mj-option value="tips">Tips and tutorials</mj-option>\n'
                    '  </mj-listbox>\n'
                    '  <label for="frequency">Frequency</label>\n'
                    '  <mj-listbox id="frequency" name="frequency" value="weekly" size="sm">\n'
                    '    <mj-option value="daily">Daily</mj-option>\n'
                    '    <mj-option value="weekly">Weekly</mj-option>\n'
                    '    <mj-option value="monthly">Monthly</mj-option>\n'
                    '  </mj-listbox>\n'
                    '  <div class="actions">\n'
                    '    <button type="submit">Subscribe</button>\n'
                    '    <button type="reset">Reset</button>\n'
                    '  </div>\n'
                    '  <output id="newsletter-out">Nothing submitted yet.</output>\n'
                    '</form>'
                ),
                css=(
                    "body { padding: var(--mj-space-4); }\n"
                    "form { display: grid; gap: var(--mj-space-2); max-inline-size: 20rem; }\n"
                    "#frequency { --mj-listbox-min-height: 0; }\n"
                    ".actions { display: flex; gap: var(--mj-space-2); }\n"
                    "output { color: var(--mj-text-muted); font-size: var(--mj-font-size-sm); }\n"
                ),
                script=(
                    'const form = document.getElementById("newsletter")\n'
                    'const out = document.getElementById("newsletter-out")\n'
                    'form.addEventListener("submit", (event) => {\n'
                    '  event.preventDefault()\n'
                    '  const data = Object.fromEntries(new FormData(form))\n'
                    '  out.textContent = "Submitted: " + JSON.stringify(data)\n'
                    '  mjSandbox.log("submit", data)\n'
                    '})\n'
                    'form.addEventListener("reset", () => {\n'
                    '  out.textContent = "Reset to the default selection."\n'
                    '  mjSandbox.log("reset", {})\n'
                    '})\n'
                ),
            ),
            ComponentExample(
                key="events",
                title="Keyboard, properties and events",
                description=(
                    "<p>On load the script presses ArrowDown (<code>mj-option-focus</code>), Space "
                    "(toggle, <code>mj-change</code>) and Shift+ArrowDown (range, "
                    "<code>mj-change</code>) on the list. <em>Add option</em> appends an "
                    "<code>&lt;mj-option&gt;</code> (the list follows it); <em>Select all</em> assigns "
                    "<code>value</code>, which changes the selection without an event.</p>"
                ),
                html=(
                    '<mj-listbox id="demo-labels" multiple label="Issue labels">\n'
                    '  <mj-option value="bug">Bug</mj-option>\n'
                    '  <mj-option value="docs">Documentation</mj-option>\n'
                    '  <mj-option value="feature">Feature request</mj-option>\n'
                    '  <mj-option value="question">Question</mj-option>\n'
                    '</mj-listbox>\n'
                    '<div class="actions">\n'
                    '  <button type="button" id="add-label">Add option</button>\n'
                    '  <button type="button" id="all-labels">Select all</button>\n'
                    '</div>'
                ),
                css=(
                    "body { padding: var(--mj-space-4); }\n"
                    "mj-listbox { inline-size: 18rem; }\n"
                    ".actions { display: flex; gap: var(--mj-space-2); margin-block-start: var(--mj-space-3); }\n"
                ),
                script=(
                    'const list = document.getElementById("demo-labels")\n'
                    'const extra = [["a11y", "Accessibility"], ["perf", "Performance"], ["security", "Security"]]\n'
                    'document.getElementById("add-label").addEventListener("click", (event) => {\n'
                    '  const next = extra.shift()\n'
                    '  if (next !== undefined) {\n'
                    '    const option = document.createElement("mj-option")\n'
                    '    option.setAttribute("value", next[0])\n'
                    '    option.textContent = next[1]\n'
                    '    list.append(option)\n'
                    '    mjSandbox.log("option added", { value: next[0], count: list.options.length })\n'
                    '  }\n'
                    '  event.target.disabled = extra.length === 0\n'
                    '})\n'
                    'document.getElementById("all-labels").addEventListener("click", () => {\n'
                    '  list.value = list.options.map((option) => option.getAttribute("value")).join(",")\n'
                    '  mjSandbox.log("value set", { selectedValues: list.selectedValues })\n'
                    '})\n'
                    '\n'
                    'const box = list.shadowRoot.querySelector("[part=listbox]")\n'
                    'const press = (key, shiftKey) => box.dispatchEvent(new KeyboardEvent("keydown", { key: key, shiftKey: shiftKey === true, bubbles: true }))\n'
                    'press("ArrowDown")\n'
                    'press(" ")\n'
                    'press("ArrowDown", true)\n'
                ),
            ),
            ComponentExample(
                key="empty",
                title="Empty list",
                description=(
                    "<p>Without options the list shows a status row: the <code>empty</code> slot "
                    "replaces the default text \"No options\" (second list). Toggle the slot in the "
                    "Slots panel.</p>"
                ),
                html=(
                    '<mj-listbox label="Attachments">\n'
                    '  <span slot="empty">No files attached yet.</span>\n'
                    '</mj-listbox>\n'
                    '<mj-listbox label="Search results"></mj-listbox>'
                ),
                css=(
                    "body { padding: var(--mj-space-4); display: flex; flex-wrap: wrap; gap: var(--mj-space-4); }\n"
                    "mj-listbox { inline-size: 16rem; }\n"
                ),
            ),
        ],
        slots=[
            ("empty", "Text of the status row shown while the list has no options (default \"No options\").",
             "<span>Nothing here yet.</span>"),
        ],
        properties=[
            ("value", "string. The live selection, comma-joined; assigning it (comma-separated with `multiple`) replaces the selection without `mj-change`."),
            ("selectedValues", "string[], read-only. The selected values in selection order."),
            ("options", "Element[], read-only. Every `<mj-option>` of the list in document order."),
            ("form", "HTMLFormElement | null, read-only. The owning form."),
            ("validity", "ValidityState, read-only. `valueMissing` while `required` and nothing is selected."),
            ("validationMessage", "string, read-only. The current validation message (`required-message`, else \"At least one selection is required.\")."),
        ],
        methods=[
            ("focus()", "Focuses the list."),
            ("checkValidity() -> boolean", "Runs constraint validation; an invalid result fires `invalid` and shows the invalid border."),
            ("reportValidity() -> boolean", "Like `checkValidity()` and also shows the browser's validation message."),
        ],
        parts=[
            ("listbox", "The scrollable `role=listbox` container."),
            ("option", "One option row."),
            ("option-checkbox", "The check mark of an option (shown while the option is selected, in both modes)."),
            ("option-label", "The text of an option row."),
            ("optgroup", "The `role=group` container of an `<mj-optgroup>`."),
            ("optgroup-label", "The heading of an option group."),
            ("empty", "The status row shown when there are no options."),
        ],
        css_properties=[
            ("--mj-listbox-min-height", "Minimum list height (default 8rem)."),
            ("--mj-listbox-max-height", "Maximum list height before it scrolls (default 24rem)."),
            ("--mj-listbox-border-radius", "Corner radius of the list (default `--mj-radius-md`)."),
            ("--mj-listbox-option-padding", "Padding of option rows (default `--mj-space-2` `--mj-space-3`; `size` sm uses its own)."),
            ("--mj-listbox-option-height", "Minimum option row height (default `--mj-control-height-md`; `size` sm/lg override it)."),
            ("--mj-listbox-selected-bg", "Background of a selected option (default the accent at 16% opacity)."),
        ],
    ),
    ComponentDoc(
        tag="mj-combobox",
        title="Combobox",
        group="selection",
        summary=(
            "Text input with a filtered suggestion popup: local &lt;mj-option&gt;s or an async source, "
            "free text, clear button and form participation."
        ),
        description=(
            "<p><code>&lt;mj-combobox&gt;</code> combines a text input (<code>role=\"combobox\"</code>) "
            "with a floating listbox of suggestions. Suggestions come from one of three sources:</p>"
            "<ul>"
            "<li>the <code>&lt;mj-option&gt;</code> descendants of the element (plain markup, not "
            "slotted), filtered by label as the user types, with the typed part highlighted. A "
            "MutationObserver follows them, so a consumer can also replace them in response to "
            "<code>mj-filter</code>;</li>"
            "<li>the <code>dataSource</code> property: an object whose <code>query(text)</code> returns "
            "(a promise of) an array of <code>{ value, label, disabled }</code> items or "
            "<code>{ items: [...] }</code>;</li>"
            "<li>the <code>src</code> attribute: a URL fetched with <code>?q=&lt;text&gt;</code> "
            "appended that returns the same JSON.</li>"
            "</ul>"
            "<p>Async sources are queried after the <code>debounce</code> delay once "
            "<code>min-chars</code> characters are typed (and when the popup opens); stale responses are "
            "dropped and a superseded fetch is aborted. While loading the popup shows the "
            "<code>loading</code> row, a failure shows the <code>error</code> row and fires "
            "<code>mj-error</code>. A <code>filterFn</code> replaces the built-in label filter.</p>"
            "<p>Committing: clicking a suggestion or Enter on the active one commits it. When focus "
            "leaves the control (or Enter is pressed while typing) the text is reconciled: an exact "
            "label match (case-insensitive) commits that option, <code>free-text</code> commits the "
            "typed text as the value, anything else reverts to the committed value, and empty text "
            "clears the value. Escape reverts the text and closes the popup.</p>"
            "<p>Keyboard: ArrowDown opens and moves (skipping disabled rows), ArrowUp moves up, "
            "Home/End jump while a row is active, Alt+ArrowDown / Alt+ArrowUp open / close, Enter "
            "commits, Escape reverts. The chevron button toggles the full list; the clear button "
            "(<code>clearable</code>) empties the value.</p>"
            "<p>The <code>value</code> attribute is the <em>default</em> value that a form reset "
            "restores; the live value is the <code>value</code> property.</p>"
        ),
        how_to_use=(
            "<p>Put <code>&lt;mj-option value=\"...\"&gt;</code> elements between the tags, or assign "
            "<code>dataSource</code> (or set <code>src</code>) for server-side suggestions. Name the "
            "input with <code>label</code>, <code>aria-label</code>, <code>aria-labelledby</code> or "
            "an associated <code>&lt;label&gt;</code>. Add <code>clearable</code> for a clear button "
            "and <code>free-text</code> to accept values that are not in the list. In a form give it a "
            "<code>name</code>; <code>required</code> makes an empty value invalid. Listen for "
            "<code>mj-change</code> (<code>{ value, previousValue, option }</code>), which also fires "
            "when the clear button or a free-text / blur commit changes the value.</p>"
        ),
        example="",
        attributes=[
            AttributeDoc(name="value", description="Default (initial) value; the input shows its option label. Form reset restores it.",
                         kind="string", values=["ca", "jp"]),
            AttributeDoc(name="placeholder", description="Placeholder text of the input.", kind="string",
                         values=["Search a country"]),
            AttributeDoc(name="label", description="Accessible name of the input and listbox; wins over `aria-label`, `aria-labelledby` and a `<label>`.",
                         kind="string", values=["Country"]),
            AttributeDoc(name="aria-label", description="Accessible name when `label` is absent.", kind="string"),
            AttributeDoc(name="aria-labelledby", description="Ids of elements whose text names the input (when `label` and `aria-label` are absent).",
                         kind="string"),
            AttributeDoc(name="name", description="Form field name the value is submitted under.", kind="string"),
            AttributeDoc(name="clearable", description="Shows a clear button while there is a value or text.", kind="boolean"),
            AttributeDoc(name="free-text", description="Text that matches no option is committed as the value on blur or Enter.",
                         kind="boolean"),
            AttributeDoc(name="open", description="Shows the popup with the current suggestions. Setting it directly skips the cancelable `mj-open` event.",
                         kind="boolean"),
            AttributeDoc(name="disabled", description="Disables the input and buttons (also from an ancestor `<fieldset disabled>`).",
                         kind="boolean"),
            AttributeDoc(name="readonly", description="The input is read-only and the popup does not open.", kind="boolean"),
            AttributeDoc(name="required", description="Invalid (valueMissing) while the value is empty; sets `aria-required`.",
                         kind="boolean"),
            AttributeDoc(name="required-message", description="Validation message used instead of the default when `required` fails.",
                         kind="string", values=["Please choose a country."]),
            AttributeDoc(name="invalid", description="Forces the invalid border and `aria-invalid`.", kind="boolean"),
            AttributeDoc(name="debounce", description="Milliseconds between the last keystroke and filtering / the async query.",
                         kind="number", default="300"),
            AttributeDoc(name="min-chars", description="Characters needed before typing opens the suggestions; fewer closes the popup.",
                         kind="number", default="1"),
            AttributeDoc(name="src", description="URL of a JSON suggestion endpoint, queried with `?q=<text>`; returns `[{ value, label, disabled }]` or `{ items: [...] }`.",
                         kind="string"),
            AttributeDoc(name="block", description="Display as a block that fills the inline size of its container.",
                         kind="boolean"),
            AttributeDoc(name="size", description="Height and font size of the input row and the suggestion rows.", kind="enum",
                         values=["sm", "md", "lg"], default="md"),
        ],
        events=[
            ("mj-change", "The committed value changed: suggestion picked, exact or free-text commit, cleared text on blur, clear button. Not fired for `value` assignments.",
             "{ value: string, previousValue: string, option: Element | null }"),
            ("change", "Plain `Event` fired right after every `mj-change`, for native-style listeners.", ""),
            ("mj-input", "The user typed in the input (every keystroke); also re-fired as a plain `input` event.",
             "{ inputValue: string }"),
            ("mj-filter", "The suggestions for the typed text were shown (after the debounce) or an async query answered.",
             "{ query: string, results: (Element | object)[] }"),
            ("mj-clear", "The clear button emptied the value.", "{}"),
            ("mj-open", "Cancelable; fired before the popup opens. `preventDefault()` keeps it closed.", "{}"),
            ("mj-close", "The popup closed.", "{}"),
            ("mj-error", "The `dataSource` query or the `src` fetch failed.", "{ error: Error }"),
        ],
        examples=[
            ComponentExample(
                key="basic",
                title="Basic usage",
                description=(
                    "<p>Type to filter the countries (the match is highlighted), use the chevron to "
                    "show the full list, and <code>clearable</code> to empty the value. Canada is "
                    "disabled.</p>"
                ),
                html=(
                    '<mj-combobox label="Country" placeholder="Search a country" clearable>\n'
                    '  <mj-option value="au">Australia</mj-option>\n'
                    '  <mj-option value="br">Brazil</mj-option>\n'
                    '  <mj-option value="ca" disabled>Canada</mj-option>\n'
                    '  <mj-option value="de">Germany</mj-option>\n'
                    '  <mj-option value="jp">Japan</mj-option>\n'
                    '  <mj-option value="nz">New Zealand</mj-option>\n'
                    '  <mj-option value="us">United States</mj-option>\n'
                    '</mj-combobox>'
                ),
                css="body { padding: var(--mj-space-4); }\nmj-combobox { inline-size: 18rem; }\n",
                height=360,
            ),
            ComponentExample(
                key="free-text",
                title="Free text and prefix",
                description=(
                    "<p><code>free-text</code> accepts any tag: type a new one and press Enter or Tab "
                    "away, and <code>mj-change</code> carries the typed text with "
                    "<code>option: null</code>. The search icon is in the <code>prefix</code> slot and "
                    "the initial value comes from the <code>value</code> attribute.</p>"
                ),
                html=(
                    '<mj-combobox label="Tag" free-text clearable value="design" placeholder="Type any tag">\n'
                    '  <svg slot="prefix" viewBox="0 0 16 16" width="16" height="16" aria-hidden="true">\n'
                    '    <circle cx="7" cy="7" r="4.5" fill="none" stroke="currentColor" stroke-width="1.5"/>\n'
                    '    <path d="m10.5 10.5 3 3" stroke="currentColor" stroke-width="1.5"/>\n'
                    '  </svg>\n'
                    '  <mj-option value="design">Design</mj-option>\n'
                    '  <mj-option value="engineering">Engineering</mj-option>\n'
                    '  <mj-option value="marketing">Marketing</mj-option>\n'
                    '  <mj-option value="research">Research</mj-option>\n'
                    '</mj-combobox>\n'
                    '<button type="button">Next field</button>'
                ),
                css=(
                    "body { padding: var(--mj-space-4); display: flex; gap: var(--mj-space-3); align-items: center; }\n"
                    "mj-combobox { inline-size: 18rem; }\n"
                ),
                height=300,
            ),
            ComponentExample(
                key="states",
                title="States",
                description=(
                    "<p><code>disabled</code> and <code>readonly</code> (both with a value: the input "
                    "cannot be edited and the popup does not open), <code>invalid</code>, "
                    "<code>size=\"sm\"</code> / <code>size=\"lg\"</code>, and a "
                    "<code>block</code> combobox that fills the row.</p>"
                ),
                html=(
                    '<div class="grid">\n'
                    '  <div class="field"><label for="cb-small">Small</label>\n'
                    '    <mj-combobox id="cb-small" size="sm" value="jp">\n'
                    '      <mj-option value="jp">Japan</mj-option><mj-option value="kr">South Korea</mj-option>\n'
                    '    </mj-combobox></div>\n'
                    '  <div class="field"><label for="cb-large">Large</label>\n'
                    '    <mj-combobox id="cb-large" size="lg" value="kr">\n'
                    '      <mj-option value="jp">Japan</mj-option><mj-option value="kr">South Korea</mj-option>\n'
                    '    </mj-combobox></div>\n'
                    '  <div class="field"><label for="cb-disabled">Disabled</label>\n'
                    '    <mj-combobox id="cb-disabled" disabled value="jp">\n'
                    '      <mj-option value="jp">Japan</mj-option><mj-option value="kr">South Korea</mj-option>\n'
                    '    </mj-combobox></div>\n'
                    '  <div class="field"><label for="cb-readonly">Read-only</label>\n'
                    '    <mj-combobox id="cb-readonly" readonly clearable value="kr">\n'
                    '      <mj-option value="jp">Japan</mj-option><mj-option value="kr">South Korea</mj-option>\n'
                    '    </mj-combobox></div>\n'
                    '  <div class="field"><label for="cb-invalid">Invalid</label>\n'
                    '    <mj-combobox id="cb-invalid" invalid placeholder="Required country">\n'
                    '      <mj-option value="jp">Japan</mj-option><mj-option value="kr">South Korea</mj-option>\n'
                    '    </mj-combobox></div>\n'
                    '</div>\n'
                    '<div class="field"><label for="cb-block">Block</label>\n'
                    '  <mj-combobox id="cb-block" block placeholder="Fills the available inline size">\n'
                    '    <mj-option value="jp">Japan</mj-option><mj-option value="kr">South Korea</mj-option>\n'
                    '  </mj-combobox></div>'
                ),
                css=(
                    "body { padding: var(--mj-space-4); }\n"
                    ".grid { display: flex; flex-wrap: wrap; gap: var(--mj-space-4); margin-block-end: var(--mj-space-4); }\n"
                    ".field { display: flex; flex-direction: column; gap: var(--mj-space-1); }\n"
                ),
                height=300,
            ),
            ComponentExample(
                key="async",
                title="Async data source",
                description=(
                    "<p>The first combobox gets its suggestions from a <code>dataSource</code> that "
                    "answers after 600 ms: type two letters (<code>min-chars=\"2\"</code>, "
                    "<code>debounce=\"250\"</code>) to see the <code>loading</code> row, then the results "
                    "and <code>mj-filter</code>; a query with no match shows the <code>no-results</code> "
                    "row. The second one's source always fails: open it to see the <code>error</code> "
                    "row and <code>mj-error</code>.</p>"
                ),
                html=(
                    '<div class="field"><label for="city">City</label>\n'
                    '  <mj-combobox id="city" min-chars="2" debounce="250" clearable placeholder="Type two letters">\n'
                    '    <span slot="loading">Searching cities...</span>\n'
                    '    <span slot="no-results">No city matches that text.</span>\n'
                    '  </mj-combobox></div>\n'
                    '<div class="field"><label for="broken">Airport (service down)</label>\n'
                    '  <mj-combobox id="broken" placeholder="Open me">\n'
                    '    <span slot="error">The airport service is unavailable. Try again later.</span>\n'
                    '  </mj-combobox></div>'
                ),
                css=(
                    "body { padding: var(--mj-space-4); display: flex; flex-wrap: wrap; gap: var(--mj-space-4); }\n"
                    ".field { display: flex; flex-direction: column; gap: var(--mj-space-1); }\n"
                    "mj-combobox { inline-size: 16rem; }\n"
                ),
                script=(
                    'const CITIES = [\n'
                    '  "Amsterdam", "Athens", "Barcelona", "Berlin", "Brussels", "Budapest", "Copenhagen",\n'
                    '  "Dublin", "Lisbon", "London", "Madrid", "Milan", "Oslo", "Paris", "Prague", "Rome",\n'
                    '  "Stockholm", "Vienna", "Warsaw", "Zurich"\n'
                    ']\n'
                    'const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms))\n'
                    '\n'
                    'document.getElementById("city").dataSource = {\n'
                    '  async query(text) {\n'
                    '    await wait(600)\n'
                    '    const needle = text.toLowerCase()\n'
                    '    const matches = CITIES.filter((city) => city.toLowerCase().includes(needle))\n'
                    '    return { items: matches.map((city) => ({ value: city.toLowerCase(), label: city })) }\n'
                    '  }\n'
                    '}\n'
                    '\n'
                    'document.getElementById("broken").dataSource = {\n'
                    '  async query(text) {\n'
                    '    await wait(400)\n'
                    '    throw new Error("Airport service unavailable (simulated)")\n'
                    '  }\n'
                    '}\n'
                ),
                height=340,
            ),
            ComponentExample(
                key="form",
                title="Form participation",
                description=(
                    "<p><em>Destination</em> is <code>required</code> with a "
                    "<code>required-message</code>; <em>Carrier</em> is <code>free-text</code> with a "
                    "default <code>value</code>. Ship logs the <code>FormData</code> (or the browser "
                    "blocks an empty destination); Reset restores the defaults.</p>"
                ),
                html=(
                    '<form id="shipping">\n'
                    '  <label for="ship-country">Destination</label>\n'
                    '  <mj-combobox id="ship-country" name="country" required required-message="Choose a destination country." clearable placeholder="Start typing a country">\n'
                    '    <mj-option value="fr">France</mj-option>\n'
                    '    <mj-option value="de">Germany</mj-option>\n'
                    '    <mj-option value="it">Italy</mj-option>\n'
                    '    <mj-option value="es">Spain</mj-option>\n'
                    '  </mj-combobox>\n'
                    '  <label for="ship-carrier">Carrier</label>\n'
                    '  <mj-combobox id="ship-carrier" name="carrier" free-text value="post">\n'
                    '    <mj-option value="post">National post</mj-option>\n'
                    '    <mj-option value="express">Express courier</mj-option>\n'
                    '  </mj-combobox>\n'
                    '  <div class="actions">\n'
                    '    <button type="submit">Ship</button>\n'
                    '    <button type="reset">Reset</button>\n'
                    '  </div>\n'
                    '  <output id="shipping-out">Nothing submitted yet.</output>\n'
                    '</form>'
                ),
                css=(
                    "body { padding: var(--mj-space-4); }\n"
                    "form { display: grid; gap: var(--mj-space-2); max-inline-size: 18rem; }\n"
                    ".actions { display: flex; gap: var(--mj-space-2); margin-block-start: var(--mj-space-2); }\n"
                    "output { color: var(--mj-text-muted); font-size: var(--mj-font-size-sm); }\n"
                ),
                script=(
                    'const form = document.getElementById("shipping")\n'
                    'const out = document.getElementById("shipping-out")\n'
                    'form.addEventListener("submit", (event) => {\n'
                    '  event.preventDefault()\n'
                    '  const data = Object.fromEntries(new FormData(form))\n'
                    '  out.textContent = "Submitted: " + JSON.stringify(data)\n'
                    '  mjSandbox.log("submit", data)\n'
                    '})\n'
                    'form.addEventListener("reset", () => {\n'
                    '  out.textContent = "Reset to the default values."\n'
                    '  mjSandbox.log("reset", {})\n'
                    '})\n'
                ),
                height=420,
            ),
            ComponentExample(
                key="events",
                title="Custom filter and events",
                description=(
                    "<p>A <code>filterFn</code> matches the start of any word. On load the script types "
                    "\"san\" (<code>mj-input</code>, then <code>mj-open</code> and "
                    "<code>mj-filter</code> after the 100 ms debounce) and presses ArrowDown and Enter, "
                    "which commits the first match (<code>mj-change</code>, <code>mj-close</code>).</p>"
                ),
                html=(
                    '<mj-combobox id="demo-city" label="Destination" debounce="100" clearable placeholder="Type the start of a word">\n'
                    '  <mj-option value="sfo">San Francisco</mj-option>\n'
                    '  <mj-option value="sjc">San Jose</mj-option>\n'
                    '  <mj-option value="sea">Seattle</mj-option>\n'
                    '  <mj-option value="sna">Santa Ana</mj-option>\n'
                    '  <mj-option value="lax">Los Angeles</mj-option>\n'
                    '  <mj-option value="pdx">Portland</mj-option>\n'
                    '</mj-combobox>'
                ),
                css="body { padding: var(--mj-space-4); }\nmj-combobox { inline-size: 18rem; }\n",
                script=(
                    'const combo = document.getElementById("demo-city")\n'
                    'combo.filterFn = (option, query) => {\n'
                    '  const needle = query.toLowerCase()\n'
                    '  return needle === "" || option.textContent.toLowerCase().split(/\\s+/).some((word) => word.startsWith(needle))\n'
                    '}\n'
                    'const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms))\n'
                    'const input = combo.shadowRoot.querySelector("[part=input]")\n'
                    'input.value = "san"\n'
                    'input.dispatchEvent(new Event("input", { bubbles: true, composed: true }))\n'
                    'await wait(300)\n'
                    'mjSandbox.log("shown", { options: combo.options.map((option) => option.textContent) })\n'
                    'const press = (key) => input.dispatchEvent(new KeyboardEvent("keydown", { key: key, bubbles: true }))\n'
                    'press("ArrowDown")\n'
                    'press("Enter")\n'
                    'mjSandbox.log("committed", { value: combo.value, inputValue: combo.inputValue })\n'
                ),
                height=320,
            ),
        ],
        slots=[
            ("prefix", "Content before the input, typically a search icon (decorative: it is aria-hidden).",
             '<svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><circle cx="7" cy="7" r="4.5" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="m10.5 10.5 3 3" stroke="currentColor" stroke-width="1.5"/></svg>'),
            ("no-results", "Text of the popup row shown when no suggestion matches (default \"No results\").",
             "<span>Nothing matches that text.</span>"),
            ("loading", "Text of the popup row shown while an async source is loading (default \"Loading\").",
             "<span>Searching...</span>"),
            ("error", "Text of the popup row shown when an async source failed (default \"Failed to load options\").",
             "<span>Could not load suggestions.</span>"),
        ],
        properties=[
            ("value", "string. The committed value; assigning it updates the input text and the form value without `mj-change`."),
            ("inputValue", "string, read-only. The text currently in the input (differs from the label while typing)."),
            ("options", "Element[], read-only. The `<mj-option>` elements behind the rows currently shown."),
            ("dataSource", "{ query(text) } | null. Async suggestion source; `query` returns (a promise of) `[{ value, label, disabled }]` or `{ items }`."),
            ("filterFn", "((subject, query) => boolean) | null. Replaces the built-in filter; `subject` is the `<mj-option>` or the raw async item, `query` is \"\" when opened without typing."),
            ("open", "boolean. Whether the popup is open; `true` opens it (respects disabled/readonly and `mj-open`), `false` closes it."),
            ("form", "HTMLFormElement | null, read-only. The owning form."),
            ("validity", "ValidityState, read-only. `valueMissing` while `required` and empty."),
            ("validationMessage", "string, read-only. The current validation message."),
        ],
        methods=[
            ("focus()", "Focuses the input."),
            ("checkValidity() -> boolean", "Runs constraint validation; an invalid result fires `invalid` and shows the invalid border."),
            ("reportValidity() -> boolean", "Like `checkValidity()` and also shows the browser's validation message at the input."),
        ],
        parts=[
            ("wrapper", "The bordered row holding prefix, input and buttons."),
            ("prefix", "The container of the `prefix` slot."),
            ("input", "The text input."),
            ("clear", "The clear button (`clearable`)."),
            ("toggle", "The chevron button that toggles the popup."),
            ("popup", "The floating panel."),
            ("listbox", "The `role=listbox` container inside the popup."),
            ("option", "One suggestion row."),
            ("option-label", "The text of a suggestion row."),
            ("option-match", "The highlighted `<mark>` around the typed text."),
            ("no-results", "The row shown when nothing matches."),
            ("loading", "The row shown while an async source loads."),
            ("error-inline", "The row shown when an async source failed."),
        ],
        css_properties=[
            ("--mj-combobox-border-radius", "Corner radius of the input row and the popup (default `--mj-radius-md`)."),
            ("--mj-combobox-input-height", "Minimum height of the input row (default `--mj-control-height-md`)."),
            ("--mj-combobox-popup-min-width", "Minimum popup width (default: the width of the input row)."),
            ("--mj-combobox-popup-max-height", "Maximum popup height before it scrolls (default 18rem)."),
            ("--mj-combobox-match-color", "Colour of the highlighted match (default `--mj-accent`)."),
        ],
    ),
    ComponentDoc(
        tag="mj-cascading-select",
        title="Cascading Select",
        group="selection",
        summary="Chain of dependent selects where each level's options depend on the previous choice.",
        description=(
            "<p><code>&lt;mj-cascading-select&gt;</code> renders an ordered row (or column) "
            "of native <code>&lt;select&gt;</code> controls configured by the "
            "<code>levels</code> property. A level stays disabled until the level before it "
            "has a value; choosing a value clears every later level and works out the "
            "options of the next one from the new parent value.</p>"
            "<p>A level's options come from, in order of precedence: <code>options</code> "
            "as a function <code>(parentValue, parentValues) =&gt; items</code> (it may "
            "return a promise); <code>options</code> as a lookup object keyed by the parent "
            "value; <code>src</code>, a URL whose <code>{parentValue}</code> token is "
            "replaced and fetched as JSON; <code>dataSource</code>, an object whose "
            "<code>query({ filter: parentValue })</code> resolves to the items or "
            "<code>{ items }</code>; or <code>options</code> as a plain array, used whatever "
            "the parent value is. Items are <code>{ value, label }</code> objects or plain "
            "strings. While an asynchronous source loads, the level shows a pulsing "
            "placeholder; when it fails, an error row with a <strong>Retry</strong> "
            "button.</p>"
            "<p>The element is form-associated: it submits the JSON array of level values "
            "under its <code>name</code>, plus one <code>name=value</code> entry for each "
            "level config that has a <code>name</code>. With <code>required</code> every "
            "level must have a value. The <code>value</code> attribute (a JSON array) is the "
            "default that a form reset restores; user choices never rewrite it. The "
            "<code>value</code> property reads the submitted JSON and, assigned, selects the "
            "levels like <code>values</code>.</p>"
        ),
        how_to_use=(
            "<p>Put the element in the markup and assign <code>levels</code> from script: an "
            "array of <code>{ label, placeholder, name, options, src, dataSource }</code> "
            "objects, one per level (only one options source per level is needed). Give "
            "the chain an accessible name with <code>label</code> (or "
            "<code>aria-label</code>); each select is named by its level's "
            "<code>label</code>.</p>"
            "<p>Pre-populate with the <code>value</code> attribute "
            "(<code>value='[\"europe\",\"fr\",\"Paris\"]'</code>) or the <code>values</code> "
            "property; levels are settled in order, waiting for asynchronous options, and "
            "a value missing from its level's options is dropped together with the later "
            "ones. Re-assigning <code>levels</code> keeps the values the new options still "
            "contain.</p>"
            "<p>Listen for <code>mj-change</code> (one level changed; emitted before the "
            "dependent levels start loading) and <code>mj-complete</code> (every level has "
            "a value). Asynchronous sources report <code>mj-level-load-start</code>, "
            "<code>mj-level-load-end</code> and <code>mj-level-error</code>.</p>"
        ),
        example="",
        attributes=[
            AttributeDoc(name="value",
                         description="Default values as a JSON array, one string per level, e.g. "
                                     "`[\"europe\",\"fr\",\"Paris\"]`. Applied when set and restored by a "
                                     "form reset; user choices do not rewrite it.",
                         kind="json"),
            AttributeDoc(name="name",
                         description="Form field name; the JSON array of level values is submitted "
                                     "under it.",
                         kind="string", values=["location", "destination"]),
            AttributeDoc(name="label",
                         description="Accessible name of the group of selects (`aria-label` works too).",
                         kind="string", values=["Location", "Ship to"]),
            AttributeDoc(name="disabled",
                         description="Disables every level. An ancestor `<fieldset disabled>` does the same.",
                         kind="boolean"),
            AttributeDoc(name="required",
                         description="Form validation fails until every level has a value.",
                         kind="boolean"),
            AttributeDoc(name="invalid",
                         description="Marks the first level without a value with the danger border "
                                     "(`aria-invalid`).",
                         kind="boolean"),
            AttributeDoc(name="orientation",
                         description="Lays the levels out in a wrapping row or a column.",
                         kind="enum", values=["horizontal", "vertical"], default="horizontal"),
            AttributeDoc(name="size",
                         description="Height and font size of the level selects.",
                         kind="enum", values=["sm", "md", "lg"], default="md"),
        ],
        events=[
            ("mj-change",
             "A level's value was changed by the user. Later levels are already cleared; it is "
             "emitted before their options start loading. Setting `values` or `value` does not emit it.",
             "{ levelIndex: number, value: string, values: string[] }"),
            ("change", "A plain `change` event (no detail, bubbles, composed) dispatched on the host right after every `mj-change`."),
            ("mj-complete",
             "Emitted after `mj-change` when the change left every level with a value.",
             "{ values: string[] }"),
            ("mj-level-load-start",
             "An asynchronous source (promise-returning `options`, `src` or `dataSource`) started "
             "loading a level.",
             "{ levelIndex: number, parentValue: string }"),
            ("mj-level-load-end",
             "A level's asynchronous options arrived and are shown.",
             "{ levelIndex: number, options: { value: string, label: string }[] }"),
            ("mj-level-error",
             "A level's asynchronous source failed; the level shows the error row and its Retry button.",
             "{ levelIndex: number, error: Error }"),
        ],
        slots=[
            ("level-loading",
             "Content of the loading placeholder, shown in whichever level is loading.",
             "<span>Loading options&hellip;</span>"),
            ("level-error",
             "Replaces the error text (default \"Failed to load options\") in front of the Retry "
             "button of whichever level failed.",
             "<span>The catalogue could not be reached.</span>"),
        ],
        properties=[
            ("levels",
             "Array<{ label?, placeholder?, name?, options?, src?, dataSource? }>. The level "
             "configuration (see About). Assigning it rebuilds the selects and keeps the values the "
             "new options still contain."),
            ("values",
             "string[]. One value per level (`\"\"` when empty). Assigning it pre-populates the chain "
             "level by level; values missing from their level's options are dropped. Emits no events."),
            ("value",
             "string. The JSON array that is submitted (`\"\"` while no levels are configured). "
             "Assigning JSON array text (or an array) selects the levels like `values` does; emits no events."),
            ("form", "HTMLFormElement | null, read-only. The owning form."),
            ("validity", "ValidityState, read-only. `customError` while `required` and a level is empty."),
            ("validationMessage", "string, read-only. \"All levels must be selected.\" while incomplete."),
        ],
        methods=[
            ("checkValidity() -> boolean", "Runs constraint validation; fires `invalid` on failure."),
            ("reportValidity() -> boolean",
             "Like `checkValidity()` and shows the browser bubble at the first empty level."),
        ],
        parts=[
            ("levels", "The role=\"group\" container of all levels (flex row or column)."),
            ("level", "Each level's wrapper (label, select, loading placeholder and error row)."),
            ("level-label", "The text label above a select."),
            ("level-select", "The native `<select>` of a level."),
            ("level-loading", "The pulsing placeholder shown while a level loads."),
            ("level-error", "The error row of a level whose load failed."),
            ("level-retry", "The Retry button in the error row."),
        ],
        css_properties=[
            ("--mj-cascading-select-gap", "Space between levels (default `--mj-space-3`)."),
            ("--mj-cascading-select-level-min-width", "Minimum width of a level (default 10rem)."),
            ("--mj-cascading-select-level-loading-height",
             "Height of the loading placeholder (default `--mj-control-height-md`)."),
        ],
        examples=[
            ComponentExample(
                key="basic",
                title="Continent, country, city",
                description=(
                    "<p>Three levels fed by a plain array and two lookup maps keyed by the parent "
                    "value. Pick a continent, a country and a city: <code>mj-change</code> appears "
                    "for each level and <code>mj-complete</code> after the city.</p>"
                ),
                html='<mj-cascading-select id="geo-picker" name="location" label="Location"></mj-cascading-select>',
                script=(
                    'const picker = document.getElementById("geo-picker")\n'
                    'picker.levels = [\n'
                    '  {\n'
                    '    label: "Continent",\n'
                    '    placeholder: "Choose a continent",\n'
                    '    options: [\n'
                    '      { value: "americas", label: "Americas" },\n'
                    '      { value: "europe", label: "Europe" },\n'
                    '      { value: "asia", label: "Asia" },\n'
                    '    ],\n'
                    '  },\n'
                    '  {\n'
                    '    label: "Country",\n'
                    '    placeholder: "Choose a country",\n'
                    '    options: {\n'
                    '      americas: [{ value: "us", label: "United States" }, { value: "ca", label: "Canada" }, { value: "br", label: "Brazil" }],\n'
                    '      europe: [{ value: "fr", label: "France" }, { value: "de", label: "Germany" }, { value: "it", label: "Italy" }],\n'
                    '      asia: [{ value: "jp", label: "Japan" }, { value: "in", label: "India" }, { value: "sg", label: "Singapore" }],\n'
                    '    },\n'
                    '  },\n'
                    '  {\n'
                    '    label: "City",\n'
                    '    placeholder: "Choose a city",\n'
                    '    options: {\n'
                    '      us: ["New York", "San Francisco", "Chicago"],\n'
                    '      ca: ["Toronto", "Vancouver", "Montreal"],\n'
                    '      br: ["São Paulo", "Rio de Janeiro"],\n'
                    '      fr: ["Paris", "Lyon", "Marseille"],\n'
                    '      de: ["Berlin", "Munich", "Hamburg"],\n'
                    '      it: ["Rome", "Milan", "Turin"],\n'
                    '      jp: ["Tokyo", "Osaka", "Kyoto"],\n'
                    '      in: ["Delhi", "Mumbai", "Bengaluru"],\n'
                    '      sg: ["Singapore"],\n'
                    '    },\n'
                    '  },\n'
                    ']\n'
                ),
            ),
            ComponentExample(
                key="preset",
                title="Preset values",
                description=(
                    "<p>The <code>value</code> attribute pre-selects Europe / Germany / Berlin. The "
                    "buttons assign the <code>values</code> property (no <code>mj-change</code>); "
                    "the log shows <code>values</code> and the submitted <code>value</code>.</p>"
                ),
                html=(
                    '<mj-cascading-select id="office" label="Office" value=\'["europe","de","Berlin"]\'></mj-cascading-select>\n'
                    '<div class="actions">\n'
                    '  <button type="button" id="to-tokyo">Tokyo office</button>\n'
                    '  <button type="button" id="to-invalid">Europe / Japan (invalid)</button>\n'
                    '  <button type="button" id="clear">Clear</button>\n'
                    '</div>'
                ),
                css=(
                    ".actions { display: flex; flex-wrap: wrap; gap: var(--mj-space-2); "
                    "margin-block-start: var(--mj-space-4); }\n"
                ),
                script=(
                    'const picker = document.getElementById("office")\n'
                    'picker.levels = [\n'
                    '  { label: "Region", options: [{ value: "europe", label: "Europe" }, { value: "asia", label: "Asia" }] },\n'
                    '  { label: "Country", options: {\n'
                    '    europe: [{ value: "de", label: "Germany" }, { value: "fr", label: "France" }],\n'
                    '    asia: [{ value: "jp", label: "Japan" }, { value: "sg", label: "Singapore" }],\n'
                    '  } },\n'
                    '  { label: "City", options: {\n'
                    '    de: ["Berlin", "Munich"], fr: ["Paris", "Lyon"], jp: ["Tokyo", "Osaka"], sg: ["Singapore"],\n'
                    '  } },\n'
                    ']\n'
                    'const report = (label) => mjSandbox.log(label, { values: picker.values, value: picker.value })\n'
                    'report("preset from the value attribute")\n'
                    'document.getElementById("to-tokyo").addEventListener("click", () => {\n'
                    '  picker.values = ["asia", "jp", "Tokyo"]\n'
                    '  report("values = [asia, jp, Tokyo]")\n'
                    '})\n'
                    'document.getElementById("to-invalid").addEventListener("click", () => {\n'
                    '  // "jp" is not a country of Europe: it and the city after it are dropped.\n'
                    '  picker.values = ["europe", "jp", "Tokyo"]\n'
                    '  report("values = [europe, jp, Tokyo]")\n'
                    '})\n'
                    'document.getElementById("clear").addEventListener("click", () => {\n'
                    '  picker.values = []\n'
                    '  report("values = []")\n'
                    '})\n'
                ),
            ),
            ComponentExample(
                key="loading-error",
                title="Async loading, error and retry",
                description=(
                    "<p>Level 1 uses a <code>dataSource</code> that fails on its first query: the "
                    "error row shows the slotted <code>level-error</code> text and a "
                    "<strong>Retry</strong> button. Retry loads it (the slotted "
                    "<code>level-loading</code> text shows meanwhile). Level 2 is a "
                    "promise-returning <code>options</code> function: pick a department and the same "
                    "slotted loading text shows in level 2. Level 3 is a plain array. Watch "
                    "the <code>mj-level-*</code> events.</p>"
                ),
                html=(
                    '<mj-cascading-select id="catalog-picker" label="Product filter">\n'
                    '  <span slot="level-loading" class="loading-text">Loading options&hellip;</span>\n'
                    '  <span slot="level-error">The catalogue could not be reached.</span>\n'
                    '</mj-cascading-select>'
                ),
                css=(
                    ".loading-text { display: block; padding: var(--mj-space-2) var(--mj-space-3); "
                    "color: var(--mj-text-muted); font-size: var(--mj-font-size-sm); }\n"
                ),
                script=(
                    'const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms))\n'
                    'const picker = document.getElementById("catalog-picker")\n'
                    'let queries = 0\n'
                    'const departments = {\n'
                    '  async query({ filter }) {\n'
                    '    queries = queries + 1\n'
                    '    await wait(800)\n'
                    '    if (queries === 1) {\n'
                    '      throw new Error("Service unavailable (simulated)")\n'
                    '    }\n'
                    '    return { items: [{ value: "audio", label: "Audio" }, { value: "cameras", label: "Cameras" }, { value: "garden", label: "Garden" }] }\n'
                    '  },\n'
                    '}\n'
                    'const categories = {\n'
                    '  audio: ["Headphones", "Speakers", "Turntables"],\n'
                    '  cameras: ["Mirrorless", "Compact", "Lenses"],\n'
                    '  garden: ["Tools", "Furniture", "Lighting"],\n'
                    '}\n'
                    'picker.levels = [\n'
                    '  { label: "Department", placeholder: "Any department", dataSource: departments },\n'
                    '  {\n'
                    '    label: "Category",\n'
                    '    placeholder: "Any category",\n'
                    '    options: async (parentValue) => {\n'
                    '      await wait(600)\n'
                    '      return categories[parentValue] || []\n'
                    '    },\n'
                    '  },\n'
                    '  { label: "Condition", options: ["New", "Refurbished", "Used"] },\n'
                    ']\n'
                ),
            ),
            ComponentExample(
                key="form",
                title="Form participation",
                description=(
                    "<p>Inside a <code>&lt;form&gt;</code> with <code>name</code>, "
                    "<code>required</code> and per-level <code>name</code>s. Submit logs the "
                    "FormData: the JSON array under <code>destination</code> plus one entry per "
                    "named level. Clear a level and submit to see the browser block it; "
                    "<strong>Reset</strong> restores the <code>value</code> attribute.</p>"
                ),
                html=(
                    '<form id="ship-form">\n'
                    '  <mj-cascading-select id="ship-to" name="destination" label="Ship to" required\n'
                    '    value=\'["europe","fr","Paris"]\'></mj-cascading-select>\n'
                    '  <div class="actions">\n'
                    '    <button type="submit">Submit</button>\n'
                    '    <button type="reset">Reset</button>\n'
                    '  </div>\n'
                    '</form>'
                ),
                css=(
                    ".actions { display: flex; gap: var(--mj-space-2); margin-block-start: var(--mj-space-4); }\n"
                ),
                script=(
                    'const form = document.getElementById("ship-form")\n'
                    'const picker = document.getElementById("ship-to")\n'
                    'picker.levels = [\n'
                    '  { name: "region", label: "Region", options: [{ value: "europe", label: "Europe" }, { value: "americas", label: "Americas" }] },\n'
                    '  { name: "country", label: "Country", options: {\n'
                    '    europe: [{ value: "fr", label: "France" }, { value: "de", label: "Germany" }],\n'
                    '    americas: [{ value: "us", label: "United States" }, { value: "ca", label: "Canada" }],\n'
                    '  } },\n'
                    '  { name: "city", label: "City", options: {\n'
                    '    fr: ["Paris", "Lyon"], de: ["Berlin", "Hamburg"], us: ["Boston", "Denver"], ca: ["Toronto", "Calgary"],\n'
                    '  } },\n'
                    ']\n'
                    'form.addEventListener("submit", (event) => {\n'
                    '  event.preventDefault()\n'
                    '  mjSandbox.log("submitted FormData", Object.fromEntries(new FormData(form)))\n'
                    '})\n'
                    'form.addEventListener("reset", () => {\n'
                    '  setTimeout(() => mjSandbox.log("after reset", { values: picker.values }), 0)\n'
                    '})\n'
                    'picker.addEventListener("invalid", () => {\n'
                    '  mjSandbox.log("invalid", { message: picker.validationMessage })\n'
                    '})\n'
                ),
            ),
            ComponentExample(
                key="variants",
                title="Orientation, sizes, disabled",
                description=(
                    "<p>A vertical chain with <code>size=\"lg\"</code> and a narrower "
                    "<code>--mj-cascading-select-level-min-width</code>, a horizontal "
                    "<code>size=\"sm\"</code> chain, and a <code>disabled</code> chain with preset "
                    "values.</p>"
                ),
                html=(
                    '<div class="stack">\n'
                    '  <mj-cascading-select id="vertical" orientation="vertical" size="lg" label="Vertical, large"></mj-cascading-select>\n'
                    '  <mj-cascading-select id="small" size="sm" label="Horizontal, small"></mj-cascading-select>\n'
                    '  <mj-cascading-select id="locked" disabled label="Disabled" value=\'["dairy","cheese"]\'></mj-cascading-select>\n'
                    '</div>'
                ),
                css=(
                    ".stack { display: grid; gap: var(--mj-space-6); }\n"
                    "#vertical { max-inline-size: 22rem; --mj-cascading-select-level-min-width: 12rem; }\n"
                ),
                script=(
                    'const levels = [\n'
                    '  { label: "Aisle", options: [{ value: "dairy", label: "Dairy" }, { value: "bakery", label: "Bakery" }] },\n'
                    '  { label: "Product", options: {\n'
                    '    dairy: [{ value: "milk", label: "Milk" }, { value: "cheese", label: "Cheese" }, { value: "yogurt", label: "Yogurt" }],\n'
                    '    bakery: [{ value: "bread", label: "Bread" }, { value: "bagels", label: "Bagels" }],\n'
                    '  } },\n'
                    ']\n'
                    'for (const picker of document.querySelectorAll("mj-cascading-select")) {\n'
                    '  picker.levels = levels\n'
                    '}\n'
                ),
            ),
            ComponentExample(
                key="events",
                title="Scripted walkthrough",
                description=(
                    "<p>The script plays a user's choices on the shadow selects (Europe, then Italy "
                    "once its countries have loaded, then Rome). The log shows "
                    "<code>mj-change</code> before <code>mj-level-load-start</code>, then "
                    "<code>mj-level-load-end</code> and finally <code>mj-complete</code>.</p>"
                ),
                html='<mj-cascading-select id="walkthrough" label="Destination"></mj-cascading-select>',
                script=(
                    'const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms))\n'
                    'const picker = document.getElementById("walkthrough")\n'
                    'picker.levels = [\n'
                    '  { label: "Continent", options: [{ value: "europe", label: "Europe" }, { value: "asia", label: "Asia" }] },\n'
                    '  {\n'
                    '    label: "Country",\n'
                    '    options: async (parentValue) => {\n'
                    '      await wait(500)\n'
                    '      const countries = { europe: [{ value: "it", label: "Italy" }, { value: "es", label: "Spain" }], asia: [{ value: "jp", label: "Japan" }] }\n'
                    '      return countries[parentValue] || []\n'
                    '    },\n'
                    '  },\n'
                    '  { label: "City", options: { it: ["Rome", "Florence"], es: ["Madrid", "Seville"], jp: ["Tokyo"] } },\n'
                    ']\n'
                    '\n'
                    '// What a user does: pick a value in a level select (they live in the shadow root).\n'
                    'const choose = (index, value) => {\n'
                    '  const select = picker.shadowRoot.querySelector(`select[data-level="${index}"]`)\n'
                    '  select.value = value\n'
                    '  select.dispatchEvent(new Event("change", { bubbles: true }))\n'
                    '}\n'
                    'const loaded = () => new Promise((resolve) => picker.addEventListener("mj-level-load-end", resolve, { once: true }))\n'
                    '\n'
                    'await wait(400)\n'
                    'const countriesLoaded = loaded()\n'
                    'choose(0, "europe")\n'
                    'await countriesLoaded\n'
                    'await wait(400)\n'
                    'choose(1, "it")\n'
                    'await wait(400)\n'
                    'choose(2, "Rome")\n'
                    'mjSandbox.log("done", { values: picker.values })\n'
                ),
            ),
        ],
    ),
    ComponentDoc(
        tag="mj-radio-group",
        title="Radio Group",
        group="selection",
        summary="Mutually exclusive radio button group with roving tabindex and form participation.",
        description=(
            "<p><code>&lt;mj-radio-group&gt;</code> turns its <code>&lt;mj-radio&gt;</code> "
            "descendants into an ARIA <code>radiogroup</code>: one row with "
            "<code>role=\"radio\"</code> per radio, of which at most one is checked. Each row's "
            "label is a copy of the radio's content and its description a copy of the "
            "radio's <code>slot=\"description\"</code> child. Radios added, removed or "
            "changed later are picked up automatically.</p>"
            "<p>Keyboard: Tab enters the group on the checked radio (or the first enabled "
            "one); the arrow keys of both axes (mirrored in RTL), Home and End move focus "
            "<em>and</em> selection, skipping disabled radios and wrapping round; Space checks "
            "the focused radio. <code>readonly</code> still lets focus move but nothing "
            "changes; <code>disabled</code> takes the group out of the tab order and ignores "
            "pointer and keyboard.</p>"
            "<p>The group is form-associated: it submits the checked value under its "
            "<code>name</code>, fails validation while <code>required</code> and empty, and "
            "after a failed submit shows the validation message (or the slotted "
            "<code>error</code> content) below the radios. The <code>value</code> attribute "
            "is the default a form reset restores; the live value is the <code>value</code> "
            "property.</p>"
        ),
        how_to_use=(
            "<p>Place <code>&lt;mj-radio value=\"...\"&gt;</code> children inside the tag "
            "(without <code>value</code> the label text is the value). Add "
            "<code>disabled</code> to a radio to make it unavailable and a "
            "<code>&lt;span slot=\"description\"&gt;</code> inside it for secondary text.</p>"
            "<p>Name the group with a <code>slot=\"label\"</code> element or the "
            "<code>label</code> / <code>aria-label</code> attribute, add hint text in "
            "<code>slot=\"help\"</code> and your own error text in <code>slot=\"error\"</code> "
            "(shown with <code>invalid</code> or after a failed validation). Use "
            "<code>orientation=\"horizontal\"</code> for a wrapping row and "
            "<code>variant=\"button\"</code> for bordered, button-like options.</p>"
            "<p>Listen for <code>mj-change</code>; it is not emitted for the radio that is "
            "already checked, nor when script assigns <code>value</code>.</p>"
        ),
        example="",
        attributes=[
            AttributeDoc(name="value",
                         description="Default value: checks the radio with this value; a form reset "
                                     "restores it. User choices do not rewrite the attribute.",
                         kind="string", values=["monthly", "quarterly", "annual"]),
            AttributeDoc(name="name", description="Form field name the checked value is submitted under.",
                         kind="string", values=["billing", "plan"]),
            AttributeDoc(name="label",
                         description="Accessible name of the group; wins over the `label` slot "
                                     "(`aria-label` works the same).",
                         kind="string", values=["Billing cycle"]),
            AttributeDoc(name="orientation",
                         description="Stacks the radios or lays them out in a wrapping row. Arrow keys of "
                                     "both axes work in either layout.",
                         kind="enum", values=["vertical", "horizontal"], default="vertical"),
            AttributeDoc(name="variant",
                         description="`button` draws each option as a bordered button without the circle.",
                         kind="enum", values=["default", "button"], default="default"),
            AttributeDoc(name="disabled",
                         description="Disables the whole group: no tab stop, pointer and keys ignored. An "
                                     "ancestor `<fieldset disabled>` does the same.",
                         kind="boolean"),
            AttributeDoc(name="readonly",
                         description="Focus can move through the radios but the selection cannot change.",
                         kind="boolean"),
            AttributeDoc(name="required",
                         description="Form validation fails (`valueMissing`) while no radio is checked.",
                         kind="boolean"),
            AttributeDoc(name="required-message",
                         description="Message used for the `required` failure instead of "
                                     "\"This field is required.\"",
                         kind="string", values=["Pick a plan to continue."]),
            AttributeDoc(name="invalid",
                         description="Outlines the group in the danger colour, shows the `error` slot and "
                                     "sets `aria-invalid`.",
                         kind="boolean"),
        ],
        events=[
            ("mj-change",
             "The user checked a different radio (click, Space, arrow keys, Home, End). Not emitted for "
             "the already-checked radio or for script assignments to `value`.",
             "{ value: string, previousValue: string, radio: Element }"),
            ("change", "A plain `change` event (no detail, bubbles, composed) dispatched on the host right after every `mj-change`."),
        ],
        slots=[
            ("label", "Visible group label; names the radiogroup unless `label` / `aria-label` is set.",
             "<span>Billing cycle</span>"),
            ("help", "Hint text below the radios; describes the group.",
             "<span>You can switch plans at any time.</span>"),
            ("error",
             "Error text below the radios, shown only with `invalid` or after a failed validation "
             "(default: the validation message).",
             "<span>Choose a billing cycle to continue.</span>"),
        ],
        properties=[
            ("value",
             "string. The checked value (`\"\"` when none). Assigning it checks the matching radio and "
             "updates the form value without emitting `mj-change`."),
            ("radios", "Element[], read-only. The `<mj-radio>` descendants, in document order."),
            ("selectedRadio", "Element | null, read-only. The checked `<mj-radio>`."),
            ("form", "HTMLFormElement | null, read-only. The owning form."),
            ("validity", "ValidityState, read-only. `valueMissing` while `required` and empty."),
            ("validationMessage", "string, read-only. The current validation message."),
        ],
        methods=[
            ("focus()", "Focuses the group's tab stop (the checked radio, else the first enabled one)."),
            ("checkValidity() -> boolean", "Runs constraint validation; fires `invalid` on failure."),
            ("reportValidity() -> boolean",
             "Like `checkValidity()`; a failure also shows the inline error."),
        ],
        parts=[
            ("group", "The role=\"radiogroup\" container."),
            ("group-label", "Wrapper of the `label` slot."),
            ("radios", "The container of the radio rows (flex column or row)."),
            ("radio", "One radio row (role=\"radio\"); `[aria-checked=\"true\"]` when checked."),
            ("radio-input", "The circle of a row (hidden in the button variant)."),
            ("radio-label", "The copied label content of a row."),
            ("radio-description", "The copied description of a row."),
            ("help", "Wrapper of the `help` slot."),
            ("error", "The error region (role=\"alert\")."),
        ],
        css_properties=[
            ("--mj-radio-group-gap",
             "Gap between rows (default `--mj-space-2`; horizontal default `--mj-space-2 --mj-space-4`)."),
            ("--mj-radio-label-gap", "Gap between circle and label (default `--mj-space-2`)."),
            ("--mj-radio-size", "Diameter of the circle (default 1rem)."),
            ("--mj-radio-border-color", "Border colour of an unchecked circle (default `--mj-border-strong`)."),
            ("--mj-radio-color", "Fill of the checked circle (default `--mj-accent`)."),
        ],
        examples=[
            ComponentExample(
                key="basic",
                title="Basic usage",
                description=(
                    "<p>A labelled group with a preset value, a radio description and help text. "
                    "Click a radio or use the arrow keys; <code>mj-change</code> appears in Events.</p>"
                ),
                html=(
                    '<mj-radio-group id="billing" name="billing" value="monthly">\n'
                    '  <span slot="label">Billing cycle</span>\n'
                    '  <mj-radio value="monthly">Monthly</mj-radio>\n'
                    '  <mj-radio value="quarterly">Quarterly</mj-radio>\n'
                    '  <mj-radio value="annual">Annual\n'
                    '    <span slot="description">Two months free when paid yearly</span>\n'
                    '  </mj-radio>\n'
                    '  <span slot="help">You can switch plans at any time.</span>\n'
                    '</mj-radio-group>'
                ),
            ),
            ComponentExample(
                key="variants",
                title="Horizontal and button variants",
                description=(
                    "<p>A horizontal <code>variant=\"button\"</code> size picker named by "
                    "<code>label</code>, a plain horizontal row, and vertical buttons with "
                    "descriptions restyled with <code>--mj-radio-*</code> properties.</p>"
                ),
                html=(
                    '<div class="stack">\n'
                    '  <mj-radio-group id="size" variant="button" orientation="horizontal" value="md" label="T-shirt size">\n'
                    '    <mj-radio value="sm">S</mj-radio>\n'
                    '    <mj-radio value="md">M</mj-radio>\n'
                    '    <mj-radio value="lg">L</mj-radio>\n'
                    '    <mj-radio value="xl">XL</mj-radio>\n'
                    '  </mj-radio-group>\n'
                    '  <mj-radio-group orientation="horizontal" value="card">\n'
                    '    <span slot="label">Payment method</span>\n'
                    '    <mj-radio value="card">Card</mj-radio>\n'
                    '    <mj-radio value="paypal">PayPal</mj-radio>\n'
                    '    <mj-radio value="invoice">Invoice</mj-radio>\n'
                    '  </mj-radio-group>\n'
                    '  <mj-radio-group id="delivery" class="branded" value="standard">\n'
                    '    <span slot="label">Delivery</span>\n'
                    '    <mj-radio value="standard">Standard<span slot="description">3-5 business days, free</span></mj-radio>\n'
                    '    <mj-radio value="express">Express<span slot="description">Next business day</span></mj-radio>\n'
                    '    <mj-radio value="pickup">Store pickup<span slot="description">Ready in two hours</span></mj-radio>\n'
                    '  </mj-radio-group>\n'
                    '</div>'
                ),
                css=(
                    ".stack { display: grid; gap: var(--mj-space-6); }\n"
                    ".branded {\n"
                    "  --mj-radio-size: 1.25rem;\n"
                    "  --mj-radio-color: var(--mj-color-success);\n"
                    "  --mj-radio-group-gap: var(--mj-space-3);\n"
                    "}\n"
                ),
            ),
            ComponentExample(
                key="states",
                title="Invalid, disabled and read-only",
                description=(
                    "<p>An <code>invalid</code> group showing its <code>error</code> slot with one "
                    "disabled radio (arrow keys skip it), a <code>disabled</code> group (no tab "
                    "stop, clicks ignored) and a <code>readonly</code> group (focus moves, the "
                    "selection does not).</p>"
                ),
                html=(
                    '<div class="stack">\n'
                    '  <mj-radio-group id="contact" invalid>\n'
                    '    <span slot="label">Preferred contact</span>\n'
                    '    <mj-radio value="email">Email</mj-radio>\n'
                    '    <mj-radio value="post" disabled>Post (unavailable)</mj-radio>\n'
                    '    <mj-radio value="phone">Phone</mj-radio>\n'
                    '    <span slot="error">Choose how we should contact you.</span>\n'
                    '  </mj-radio-group>\n'
                    '  <mj-radio-group disabled value="team">\n'
                    '    <span slot="label">Disabled group</span>\n'
                    '    <mj-radio value="starter">Starter</mj-radio>\n'
                    '    <mj-radio value="team">Team</mj-radio>\n'
                    '  </mj-radio-group>\n'
                    '  <mj-radio-group readonly value="annual">\n'
                    '    <span slot="label">Read-only group</span>\n'
                    '    <mj-radio value="monthly">Monthly</mj-radio>\n'
                    '    <mj-radio value="annual">Annual</mj-radio>\n'
                    '  </mj-radio-group>\n'
                    '</div>'
                ),
                css=".stack { display: grid; gap: var(--mj-space-6); }\n",
            ),
            ComponentExample(
                key="form",
                title="Required in a form",
                description=(
                    "<p>A <code>required</code> group with <code>name=\"plan\"</code> and a "
                    "<code>required-message</code>. Submit without a choice: the browser blocks "
                    "it and the message appears below the radios. Choose a plan and submit to log "
                    "the FormData; <strong>Reset</strong> clears it again.</p>"
                ),
                html=(
                    '<form id="plan-form">\n'
                    '  <mj-radio-group id="plan" name="plan" required required-message="Pick a plan to continue.">\n'
                    '    <span slot="label">Plan</span>\n'
                    '    <mj-radio value="starter">Starter<span slot="description">One project, community support</span></mj-radio>\n'
                    '    <mj-radio value="team">Team<span slot="description">Ten projects, email support</span></mj-radio>\n'
                    '    <mj-radio value="enterprise">Enterprise<span slot="description">Unlimited projects, SSO</span></mj-radio>\n'
                    '    <span slot="help">Required.</span>\n'
                    '  </mj-radio-group>\n'
                    '  <div class="actions">\n'
                    '    <button type="submit">Subscribe</button>\n'
                    '    <button type="reset">Reset</button>\n'
                    '  </div>\n'
                    '</form>'
                ),
                css=".actions { display: flex; gap: var(--mj-space-2); margin-block-start: var(--mj-space-4); }\n",
                script=(
                    'const form = document.getElementById("plan-form")\n'
                    'const group = document.getElementById("plan")\n'
                    'form.addEventListener("submit", (event) => {\n'
                    '  event.preventDefault()\n'
                    '  mjSandbox.log("submitted FormData", Object.fromEntries(new FormData(form)))\n'
                    '})\n'
                    'group.addEventListener("invalid", () => {\n'
                    '  mjSandbox.log("invalid", { message: group.validationMessage })\n'
                    '})\n'
                ),
            ),
            ComponentExample(
                key="events",
                title="Keyboard and scripting",
                description=(
                    "<p>The script assigns <code>value</code> (no event), then sends ArrowRight "
                    "and End to the focused row as a keyboard user would: two "
                    "<code>mj-change</code> events follow, each logged with "
                    "<code>selectedRadio</code>. Try Tab, the arrow keys, Home, End and Space "
                    "yourself.</p>"
                ),
                html=(
                    '<mj-radio-group id="theme" label="Theme" orientation="horizontal" value="system">\n'
                    '  <mj-radio value="light">Light</mj-radio>\n'
                    '  <mj-radio value="dark">Dark</mj-radio>\n'
                    '  <mj-radio value="contrast">High contrast</mj-radio>\n'
                    '  <mj-radio value="system">System</mj-radio>\n'
                    '</mj-radio-group>'
                ),
                script=(
                    'const group = document.getElementById("theme")\n'
                    'group.addEventListener("mj-change", () => {\n'
                    '  mjSandbox.log("selectedRadio", { text: group.selectedRadio.textContent, value: group.value })\n'
                    '})\n'
                    '\n'
                    'group.value = "light"\n'
                    'mjSandbox.log("value assigned by script (no mj-change)", { value: group.value })\n'
                    '\n'
                    '// The tab stop is the checked row; keys go to it as they would for a keyboard user.\n'
                    'const press = (key) => {\n'
                    '  const row = group.shadowRoot.querySelector(\'[role="radio"][tabindex="0"]\')\n'
                    '  row.dispatchEvent(new KeyboardEvent("keydown", { key: key, bubbles: true }))\n'
                    '}\n'
                    'press("ArrowRight")\n'
                    'press("End")\n'
                ),
            ),
            ComponentExample(
                key="dynamic",
                title="Built from data",
                description=(
                    "<p>The radios are created from an array in the script and the group follows. "
                    "<strong>Add a region</strong> appends another <code>&lt;mj-radio&gt;</code>; "
                    "<strong>Disable Frankfurt</strong> toggles a radio's <code>disabled</code> "
                    "attribute.</p>"
                ),
                html=(
                    '<mj-radio-group id="region" name="region" label="Data region"></mj-radio-group>\n'
                    '<div class="actions">\n'
                    '  <button type="button" id="add-region">Add a region</button>\n'
                    '  <button type="button" id="toggle-fra">Disable Frankfurt</button>\n'
                    '</div>'
                ),
                css=".actions { display: flex; gap: var(--mj-space-2); margin-block-start: var(--mj-space-4); }\n",
                script=(
                    'const group = document.getElementById("region")\n'
                    'const regions = [\n'
                    '  { value: "us-east", label: "Virginia", note: "US East" },\n'
                    '  { value: "eu-central", label: "Frankfurt", note: "EU Central" },\n'
                    '  { value: "ap-south", label: "Mumbai", note: "Asia Pacific" },\n'
                    ']\n'
                    'const addRadio = (region) => {\n'
                    '  const radio = document.createElement("mj-radio")\n'
                    '  radio.setAttribute("value", region.value)\n'
                    '  radio.append(region.label)\n'
                    '  const note = document.createElement("span")\n'
                    '  note.slot = "description"\n'
                    '  note.textContent = region.note\n'
                    '  radio.append(note)\n'
                    '  group.append(radio)\n'
                    '  return radio\n'
                    '}\n'
                    'regions.forEach(addRadio)\n'
                    'group.value = "eu-central"\n'
                    '\n'
                    'document.getElementById("add-region").addEventListener("click", () => {\n'
                    '  addRadio({ value: "sa-east-" + group.radios.length, label: "São Paulo", note: "South America" })\n'
                    '  mjSandbox.log("radios", { count: group.radios.length })\n'
                    '}, { once: true })\n'
                    'document.getElementById("toggle-fra").addEventListener("click", () => {\n'
                    '  const frankfurt = group.radios.find((radio) => radio.getAttribute("value") === "eu-central")\n'
                    '  frankfurt.toggleAttribute("disabled")\n'
                    '})\n'
                ),
            ),
        ],
    ),
    ComponentDoc(
        tag="mj-checkbox-group",
        title="Checkbox Group",
        group="selection",
        summary="Labeled group of independent boolean choices with optional select-all and form participation.",
        description=(
            "<p><code>&lt;mj-checkbox-group&gt;</code> turns its "
            "<code>&lt;mj-checkbox&gt;</code> descendants into a labelled group of "
            "<code>role=\"checkbox\"</code> rows; any number can be checked. Each row's label "
            "is a copy of the checkbox's content and its description a copy of its "
            "<code>slot=\"description\"</code> child. Checkboxes added, removed or changed "
            "later are picked up automatically.</p>"
            "<p>With <code>select-all</code> a tri-state parent checkbox appears above the "
            "rows: checked when every enabled checkbox is checked, mixed when some are. "
            "Activating it checks every enabled checkbox, or clears them when all were "
            "checked; disabled checkboxes keep their state. Each row is its own tab stop and "
            "toggles with Space or Enter.</p>"
            "<p>The group is form-associated: it submits the checked values as one "
            "comma-separated string under its <code>name</code> and fails validation while "
            "<code>required</code> and nothing is checked. The <code>value</code> attribute is "
            "the default a form reset restores; the live value is the <code>value</code> "
            "property.</p>"
        ),
        how_to_use=(
            "<p>Place <code>&lt;mj-checkbox value=\"...\"&gt;</code> children inside the tag "
            "(without <code>value</code> the label text is the value). Add "
            "<code>disabled</code> to a checkbox to lock it and a "
            "<code>&lt;span slot=\"description\"&gt;</code> inside it for secondary text. "
            "Pre-check with <code>value=\"email,sms\"</code>.</p>"
            "<p>Name the group with a <code>slot=\"label\"</code> element or the "
            "<code>label</code> / <code>aria-label</code> attribute; add <code>help</code> and "
            "<code>error</code> slot content as needed (the error shows with "
            "<code>invalid</code> or after a failed validation). Add <code>select-all</code> "
            "(and <code>select-all-label</code>) for the parent checkbox and "
            "<code>orientation=\"horizontal\"</code> for a wrapping row.</p>"
            "<p>Listen for <code>mj-change</code> on every user toggle; the select-all "
            "checkbox emits <code>mj-select-all</code> first. Assigning <code>value</code> from "
            "script emits nothing.</p>"
        ),
        example="",
        attributes=[
            AttributeDoc(name="value",
                         description="Default checked values, comma-separated; a form reset restores them. "
                                     "User toggles do not rewrite the attribute.",
                         kind="string", values=["email", "email,sms", "email,sms,push"]),
            AttributeDoc(name="name",
                         description="Form field name; the checked values are submitted as one "
                                     "comma-separated entry.",
                         kind="string", values=["channels"]),
            AttributeDoc(name="label",
                         description="Accessible name of the group; wins over the `label` slot "
                                     "(`aria-label` works the same).",
                         kind="string", values=["Notification channels"]),
            AttributeDoc(name="select-all",
                         description="Shows the tri-state select-all checkbox above the rows.",
                         kind="boolean"),
            AttributeDoc(name="select-all-label", description="Label of the select-all checkbox.",
                         kind="string", values=["All channels", "Select all"], default="Select all"),
            AttributeDoc(name="orientation", description="Stacks the checkboxes or lays them out in a wrapping row.",
                         kind="enum", values=["vertical", "horizontal"], default="vertical"),
            AttributeDoc(name="disabled",
                         description="Disables the whole group: rows leave the tab order, pointer and keys "
                                     "are ignored. An ancestor `<fieldset disabled>` does the same.",
                         kind="boolean"),
            AttributeDoc(name="readonly",
                         description="Rows stay focusable but cannot be toggled (`aria-readonly`).",
                         kind="boolean"),
            AttributeDoc(name="required",
                         description="Form validation fails (`valueMissing`) while nothing is checked.",
                         kind="boolean"),
            AttributeDoc(name="required-message",
                         description="Message used for the `required` failure instead of "
                                     "\"At least one option must be selected.\"",
                         kind="string", values=["Pick at least one day."]),
            AttributeDoc(name="invalid",
                         description="Outlines the group in the danger colour, shows the `error` slot and "
                                     "sets `aria-invalid`.",
                         kind="boolean"),
        ],
        events=[
            ("mj-change",
             "The user toggled a checkbox or the select-all checkbox (`changedCheckbox` is then null). "
             "Not emitted when script assigns `value`.",
             "{ value: string, checkedValues: string[], changedCheckbox: Element | null, checked: boolean }"),
            ("change", "A plain `change` event (no detail, bubbles, composed) dispatched on the host right after every `mj-change`."),
            ("mj-select-all",
             "The select-all checkbox was activated; emitted just before its `mj-change`. `checked` is "
             "true when it checked every enabled checkbox.",
             "{ checked: boolean }"),
        ],
        slots=[
            ("label", "Visible group label; names the group unless `label` / `aria-label` is set.",
             "<span>Notification channels</span>"),
            ("help", "Hint text below the checkboxes; describes the group.",
             "<span>We only send account and security notices.</span>"),
            ("error",
             "Error text below the checkboxes, shown only with `invalid` or after a failed validation "
             "(default: the validation message).",
             "<span>Choose at least one channel.</span>"),
        ],
        properties=[
            ("value",
             "string. The checked values, comma-separated. Assigning it replaces the checked set and "
             "the form value without emitting events."),
            ("checkedValues", "string[], read-only. The checked values."),
            ("selectAllState",
             "'none' | 'some' | 'all', read-only. How many enabled checkboxes are checked (disabled ones "
             "are not counted). After adding or changing `<mj-checkbox>` elements it is up to date once "
             "the rows are rebuilt, a microtask later."),
            ("checkboxes", "Element[], read-only. The `<mj-checkbox>` descendants, in document order."),
            ("form", "HTMLFormElement | null, read-only. The owning form."),
            ("validity", "ValidityState, read-only. `valueMissing` while `required` and nothing is checked."),
            ("validationMessage", "string, read-only. The current validation message (`required-message`, else \"At least one option must be selected.\")."),
        ],
        methods=[
            ("focus()", "Focuses the first focusable checkbox row (the select-all row is not considered)."),
            ("checkValidity() -> boolean", "Runs constraint validation; fires `invalid` on failure."),
            ("reportValidity() -> boolean",
             "Like `checkValidity()`; a failure also shows the inline error."),
        ],
        parts=[
            ("group", "The role=\"group\" container."),
            ("group-label", "Wrapper of the `label` slot."),
            ("select-all", "Wrapper of the select-all row (hidden without `select-all`)."),
            ("checkboxes", "The container of the checkbox rows (flex column or row)."),
            ("checkbox",
             "One row (role=\"checkbox\"), including the select-all row; `aria-checked` is true, false "
             "or mixed."),
            ("checkbox-input", "The box of a row."),
            ("checkbox-label", "The label of a row."),
            ("checkbox-description", "The copied description of a row."),
            ("help", "Wrapper of the `help` slot."),
            ("error", "The error region (role=\"alert\")."),
        ],
        css_properties=[
            ("--mj-checkbox-group-gap",
             "Gap between rows (default `--mj-space-2`; horizontal default `--mj-space-2 --mj-space-4`)."),
            ("--mj-checkbox-label-gap", "Gap between box and label (default `--mj-space-2`)."),
            ("--mj-checkbox-size", "Size of the box (default 1rem)."),
            ("--mj-checkbox-border-color", "Border colour of an unchecked box (default `--mj-border-strong`)."),
            ("--mj-checkbox-color", "Fill of a checked box (default `--mj-accent`)."),
            ("--mj-checkbox-indeterminate-color",
             "Fill of the mixed select-all box (default `--mj-accent`)."),
        ],
        examples=[
            ComponentExample(
                key="basic",
                title="Basic usage",
                description=(
                    "<p>A labelled group with <code>select-all</code>, one preset value, a disabled "
                    "checkbox with a description and help text. The select-all box starts mixed; "
                    "toggle rows with the mouse or Space / Enter and watch <code>mj-change</code>.</p>"
                ),
                html=(
                    '<mj-checkbox-group id="channels" name="channels" value="email" select-all>\n'
                    '  <span slot="label">Notification channels</span>\n'
                    '  <mj-checkbox value="email">Email</mj-checkbox>\n'
                    '  <mj-checkbox value="sms">SMS</mj-checkbox>\n'
                    '  <mj-checkbox value="push">Push notification</mj-checkbox>\n'
                    '  <mj-checkbox value="webhook" disabled>Webhook\n'
                    '    <span slot="description">Coming soon</span>\n'
                    '  </mj-checkbox>\n'
                    '  <span slot="help">We only send account and security notices.</span>\n'
                    '</mj-checkbox-group>'
                ),
            ),
            ComponentExample(
                key="variants",
                title="Horizontal and custom styling",
                description=(
                    "<p>A horizontal group with a custom <code>select-all-label</code>, and a "
                    "vertical group with descriptions restyled through the "
                    "<code>--mj-checkbox-*</code> properties.</p>"
                ),
                html=(
                    '<div class="stack">\n'
                    '  <mj-checkbox-group id="toppings" orientation="horizontal" select-all\n'
                    '    select-all-label="All toppings" value="mozzarella,basil">\n'
                    '    <span slot="label">Toppings</span>\n'
                    '    <mj-checkbox value="mozzarella">Mozzarella</mj-checkbox>\n'
                    '    <mj-checkbox value="tomato">Tomato</mj-checkbox>\n'
                    '    <mj-checkbox value="basil">Basil</mj-checkbox>\n'
                    '    <mj-checkbox value="olives">Olives</mj-checkbox>\n'
                    '    <mj-checkbox value="mushrooms">Mushrooms</mj-checkbox>\n'
                    '  </mj-checkbox-group>\n'
                    '  <mj-checkbox-group class="branded" value="terms">\n'
                    '    <span slot="label">Agreements</span>\n'
                    '    <mj-checkbox value="terms">I accept the terms of service\n'
                    '      <span slot="description">Required to create an account.</span>\n'
                    '    </mj-checkbox>\n'
                    '    <mj-checkbox value="news">Send me the monthly newsletter\n'
                    '      <span slot="description">One email a month; unsubscribe at any time.</span>\n'
                    '    </mj-checkbox>\n'
                    '  </mj-checkbox-group>\n'
                    '</div>'
                ),
                css=(
                    ".stack { display: grid; gap: var(--mj-space-6); }\n"
                    ".branded {\n"
                    "  --mj-checkbox-size: 1.25rem;\n"
                    "  --mj-checkbox-color: var(--mj-color-success);\n"
                    "  --mj-checkbox-group-gap: var(--mj-space-3);\n"
                    "}\n"
                ),
            ),
            ComponentExample(
                key="states",
                title="Invalid, disabled and read-only",
                description=(
                    "<p>An <code>invalid</code> group showing its <code>error</code> slot, a "
                    "<code>disabled</code> group (rows leave the tab order, clicks and keys are "
                    "ignored) and a <code>readonly</code> group (rows focusable, nothing "
                    "toggles).</p>"
                ),
                html=(
                    '<div class="stack">\n'
                    '  <mj-checkbox-group id="topics" invalid select-all>\n'
                    '    <span slot="label">Topics you follow</span>\n'
                    '    <mj-checkbox value="design">Design</mj-checkbox>\n'
                    '    <mj-checkbox value="engineering">Engineering</mj-checkbox>\n'
                    '    <mj-checkbox value="research">Research</mj-checkbox>\n'
                    '    <span slot="error">Choose at least one topic.</span>\n'
                    '  </mj-checkbox-group>\n'
                    '  <mj-checkbox-group disabled value="read">\n'
                    '    <span slot="label">Disabled group</span>\n'
                    '    <mj-checkbox value="read">Read</mj-checkbox>\n'
                    '    <mj-checkbox value="write">Write</mj-checkbox>\n'
                    '  </mj-checkbox-group>\n'
                    '  <mj-checkbox-group readonly value="read,write">\n'
                    '    <span slot="label">Read-only group</span>\n'
                    '    <mj-checkbox value="read">Read</mj-checkbox>\n'
                    '    <mj-checkbox value="write">Write</mj-checkbox>\n'
                    '    <mj-checkbox value="admin">Admin</mj-checkbox>\n'
                    '  </mj-checkbox-group>\n'
                    '</div>'
                ),
                css=".stack { display: grid; gap: var(--mj-space-6); }\n",
            ),
            ComponentExample(
                key="form",
                title="Required in a form",
                description=(
                    "<p>A <code>required</code> group with <code>name=\"days\"</code> and default "
                    "<code>value=\"mon,fri\"</code>. Submit logs the FormData (one comma-separated "
                    "entry). Uncheck everything and submit to see the inline error; "
                    "<strong>Reset</strong> restores Monday and Friday.</p>"
                ),
                html=(
                    '<form id="report-form">\n'
                    '  <mj-checkbox-group id="days" name="days" value="mon,fri" required\n'
                    '    required-message="Pick at least one day." orientation="horizontal">\n'
                    '    <span slot="label">Send the report on</span>\n'
                    '    <mj-checkbox value="mon">Mon</mj-checkbox>\n'
                    '    <mj-checkbox value="tue">Tue</mj-checkbox>\n'
                    '    <mj-checkbox value="wed">Wed</mj-checkbox>\n'
                    '    <mj-checkbox value="thu">Thu</mj-checkbox>\n'
                    '    <mj-checkbox value="fri">Fri</mj-checkbox>\n'
                    '  </mj-checkbox-group>\n'
                    '  <div class="actions">\n'
                    '    <button type="submit">Save schedule</button>\n'
                    '    <button type="reset">Reset</button>\n'
                    '  </div>\n'
                    '</form>'
                ),
                css=".actions { display: flex; gap: var(--mj-space-2); margin-block-start: var(--mj-space-4); }\n",
                script=(
                    'const form = document.getElementById("report-form")\n'
                    'const group = document.getElementById("days")\n'
                    'form.addEventListener("submit", (event) => {\n'
                    '  event.preventDefault()\n'
                    '  mjSandbox.log("submitted FormData", Object.fromEntries(new FormData(form)))\n'
                    '})\n'
                    'form.addEventListener("reset", () => {\n'
                    '  setTimeout(() => mjSandbox.log("after reset", { value: group.value }), 0)\n'
                    '})\n'
                    'group.addEventListener("invalid", () => {\n'
                    '  mjSandbox.log("invalid", { message: group.validationMessage })\n'
                    '})\n'
                ),
            ),
            ComponentExample(
                key="events",
                title="Events and scripting",
                description=(
                    "<p>The script assigns <code>value</code> (no event), clicks one row, then "
                    "presses Space on the select-all row twice: watch <code>mj-change</code>, "
                    "<code>mj-select-all</code> and the logged <code>selectAllState</code>.</p>"
                ),
                html=(
                    '<mj-checkbox-group id="exports" label="Export formats" select-all>\n'
                    '  <mj-checkbox value="csv">CSV</mj-checkbox>\n'
                    '  <mj-checkbox value="json">JSON</mj-checkbox>\n'
                    '  <mj-checkbox value="xlsx">Excel</mj-checkbox>\n'
                    '  <mj-checkbox value="pdf">PDF</mj-checkbox>\n'
                    '</mj-checkbox-group>'
                ),
                script=(
                    'const group = document.getElementById("exports")\n'
                    'const report = (label) => mjSandbox.log(label, { value: group.value, selectAllState: group.selectAllState })\n'
                    'group.addEventListener("mj-change", () => report("after mj-change"))\n'
                    '\n'
                    'group.value = "csv"\n'
                    'report("value assigned by script (no mj-change)")\n'
                    '\n'
                    '// The rows live in the shadow root; act on them as a user would.\n'
                    'const rows = group.shadowRoot.querySelectorAll(".checkbox-items [role=checkbox]")\n'
                    'rows[1].click()\n'
                    'const selectAll = group.shadowRoot.querySelector(".select-all-wrapper [role=checkbox]")\n'
                    'const space = () => selectAll.dispatchEvent(new KeyboardEvent("keydown", { key: " ", bubbles: true }))\n'
                    'space()\n'
                    'space()\n'
                ),
            ),
            ComponentExample(
                key="dynamic",
                title="Built from data",
                description=(
                    "<p>The checkboxes are created from an array (with descriptions and one "
                    "disabled entry) and the group follows; <strong>Add permission</strong> "
                    "appends one more and the select-all state updates.</p>"
                ),
                html=(
                    '<mj-checkbox-group id="permissions" name="permissions" label="Permissions"\n'
                    '  select-all select-all-label="All permissions"></mj-checkbox-group>\n'
                    '<div class="actions">\n'
                    '  <button type="button" id="add-permission">Add permission</button>\n'
                    '</div>'
                ),
                css=".actions { display: flex; gap: var(--mj-space-2); margin-block-start: var(--mj-space-4); }\n",
                script=(
                    'const group = document.getElementById("permissions")\n'
                    'const permissions = [\n'
                    '  { value: "view", label: "View projects", note: "Always granted", disabled: true },\n'
                    '  { value: "edit", label: "Edit projects", note: "Change content and settings" },\n'
                    '  { value: "invite", label: "Invite members", note: "Send invitations by email" },\n'
                    ']\n'
                    'const addCheckbox = (permission) => {\n'
                    '  const checkbox = document.createElement("mj-checkbox")\n'
                    '  checkbox.setAttribute("value", permission.value)\n'
                    '  checkbox.toggleAttribute("disabled", permission.disabled === true)\n'
                    '  checkbox.append(permission.label)\n'
                    '  const note = document.createElement("span")\n'
                    '  note.slot = "description"\n'
                    '  note.textContent = permission.note\n'
                    '  checkbox.append(note)\n'
                    '  group.append(checkbox)\n'
                    '}\n'
                    'permissions.forEach(addCheckbox)\n'
                    'group.value = "view,edit,invite"\n'
                    '\n'
                    'document.getElementById("add-permission").addEventListener("click", async () => {\n'
                    '  addCheckbox({ value: "billing", label: "Manage billing", note: "See invoices and change the plan" })\n'
                    '  // The rows are rebuilt by a MutationObserver: read the state once it has run.\n'
                    '  await Promise.resolve()\n'
                    '  mjSandbox.log("added", { checkboxes: group.checkboxes.length, selectAllState: group.selectAllState })\n'
                    '}, { once: true })\n'
                ),
            ),
        ],
    ),
    ComponentDoc(
        tag="mj-segmented-control",
        title="Segmented Control",
        group="selection",
        summary=(
            "Compact connected row of segments acting as a single choice, independent toggles or an "
            "action toolbar; form-associated in select and toggle modes."
        ),
        description=(
            "<p><code>&lt;mj-segmented-control&gt;</code> renders its <code>&lt;mj-segment&gt;</code> "
            "descendants as a connected row of buttons. <code>&lt;mj-segment&gt;</code> is plain markup "
            "the control reads (it is not a custom element and is not slotted): each segment becomes a "
            "<code>&lt;button part=\"segment\"&gt;</code> whose content is a copy of the segment's own "
            "nodes, so text, inline SVG icons and badges are kept. A segment's <code>value</code> "
            "attribute is its value (without one, its index); <code>disabled</code> disables just that "
            "segment; <code>aria-label</code> (or <code>label</code>) names an icon-only segment and "
            "<code>title</code> becomes its tooltip. A MutationObserver follows the segments, so adding, "
            "removing or editing them after the first render rebuilds the buttons.</p>"
            "<p>Modes:</p>"
            "<ul>"
            "<li><code>select</code> (default): <code>role=\"radiogroup\"</code>; exactly one segment "
            "is checked. One tab stop; ArrowLeft / ArrowRight / ArrowUp / ArrowDown, Home and End move "
            "focus and select the segment they land on (the inline arrows follow the writing direction "
            "in RTL). Re-selecting the checked segment emits nothing.</li>"
            "<li><code>toggle</code>: <code>role=\"group\"</code> of <code>aria-pressed</code> buttons; "
            "each segment is its own tab stop and toggles with click, Space or Enter. The value is a "
            "comma-separated list in the order the segments were pressed.</li>"
            "<li><code>action</code>: <code>role=\"toolbar\"</code> with one roving tab stop moved by "
            "the inline arrows, Home and End; activating a segment fires <code>mj-action</code> and holds "
            "no state.</li>"
            "</ul>"
            "<p>In select and toggle modes the control is form-associated: it submits its value under "
            "<code>name</code>, supports <code>required</code> (select and toggle: invalid while nothing "
            "is selected) and follows an ancestor <code>&lt;fieldset disabled&gt;</code>. The "
            "<code>value</code> attribute is the <em>default</em> selection that a form reset restores; "
            "user selections and assignments to the <code>value</code> property change the live value "
            "and the submitted value but never rewrite the attribute. An action toolbar submits "
            "nothing.</p>"
            "<p><code>size</code> changes the segment font size and padding; the control's minimum "
            "height comes from <code>--mj-segmented-height</code> and is the same for every size.</p>"
        ),
        how_to_use=(
            "<p>Put <code>&lt;mj-segment value=\"...\"&gt;</code> elements between the tags and name the "
            "group with <code>label</code> (or <code>aria-label</code>). Pick the behaviour with "
            "<code>mode</code>, the default selection with <code>value</code> (comma-separated in toggle "
            "mode) and full-width layout with <code>stretch</code>. Give icon-only segments an "
            "<code>aria-label</code>. Listen for <code>mj-change</code> "
            "(<code>{ value, values, segment, selected }</code>) in select and toggle modes, or "
            "<code>mj-action</code> (<code>{ value, segment }</code>) in action mode, and read the live "
            "value from <code>.value</code>. In a form add <code>name</code> (and <code>required</code> "
            "when a choice is mandatory).</p>"
        ),
        example="",
        attributes=[
            AttributeDoc(name="mode", description="Selection behaviour: one choice (radiogroup), independent toggles (aria-pressed buttons) or an action toolbar.",
                         kind="enum", values=["select", "toggle", "action"], default="select"),
            AttributeDoc(name="value", description="Default selection: one segment value (select) or a comma-separated list (toggle). Form reset restores it; user selections do not rewrite it.",
                         kind="string", values=["day", "week", "month", "day,week"]),
            AttributeDoc(name="label", description="Accessible name of the group (wins over `aria-label`).",
                         kind="string", values=["Calendar view"]),
            AttributeDoc(name="aria-label", description="Accessible name of the group when `label` is absent.",
                         kind="string"),
            AttributeDoc(name="name", description="Form field name the value is submitted under (select and toggle modes).",
                         kind="string", values=["view"]),
            AttributeDoc(name="required", description="Invalid (valueMissing) while nothing is selected; sets `aria-required` on the radiogroup in select mode.",
                         kind="boolean"),
            AttributeDoc(name="required-message", description="Validation message used instead of the default when `required` fails.",
                         kind="string", values=["Choose a view."]),
            AttributeDoc(name="disabled", description="Disables every segment (also applied by an ancestor `<fieldset disabled>`).",
                         kind="boolean"),
            AttributeDoc(name="stretch", description="Display as a block whose segments share the full inline size.",
                         kind="boolean"),
            AttributeDoc(name="size", description="Segment font size and inline padding (the minimum height does not change).",
                         kind="enum", values=["sm", "md", "lg"], default="md"),
        ],
        events=[
            ("mj-change", "Select and toggle modes: the user changed the selection (click, Space / Enter, arrow keys in select mode). Not fired for `value` assignments or re-selecting the checked segment.",
             "{ value: string (the segment's value), values: string[] (all selected values), segment: Element (the <mj-segment>), selected: boolean }"),
            ("change", "Plain `Event` fired right after every `mj-change`, for native-style listeners.", ""),
            ("mj-action", "Action mode: a segment was activated (click, Space or Enter).",
             "{ value: string, segment: Element (the <mj-segment>) }"),
        ],
        examples=[
            ComponentExample(
                key="basic",
                title="Basic usage",
                description=(
                    "<p>A select-mode control with <code>Week</code> preselected by the <code>value</code> "
                    "attribute. Click a segment, or focus the group and use the arrow keys, Home and End: "
                    "each change logs <code>mj-change</code>.</p>"
                ),
                html=(
                    '<mj-segmented-control value="week" label="Calendar view">\n'
                    '  <mj-segment value="day">Day</mj-segment>\n'
                    '  <mj-segment value="week">Week</mj-segment>\n'
                    '  <mj-segment value="month">Month</mj-segment>\n'
                    '  <mj-segment value="year">Year</mj-segment>\n'
                    '</mj-segmented-control>'
                ),
                css="body { padding: var(--mj-space-4); }",
            ),
            ComponentExample(
                key="toggle",
                title="Toggle mode with icons",
                description=(
                    "<p><code>mode=\"toggle\"</code>: each segment is pressed or released on its own and "
                    "the value is a comma-separated list. The segments are icon-only and named by their "
                    "<code>aria-label</code>; <code>title</code> gives the tooltip. The line below reads "
                    "<code>.value</code> and <code>selectedSegments</code> after every "
                    "<code>mj-change</code>.</p>"
                ),
                html=(
                    '<mj-segmented-control id="demo-format" mode="toggle" value="bold,underline" label="Text formatting">\n'
                    '  <mj-segment value="bold" aria-label="Bold" title="Bold (Ctrl+B)">\n'
                    '    <svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><path fill="currentColor" d="M4 2h4.5a3 3 0 0 1 2.1 5.1A3.2 3.2 0 0 1 9 14H4zm2 2v3h2.5a1.5 1.5 0 0 0 0-3zm0 5v3h3a1.5 1.5 0 0 0 0-3z"/></svg>\n'
                    '  </mj-segment>\n'
                    '  <mj-segment value="italic" aria-label="Italic" title="Italic (Ctrl+I)">\n'
                    '    <svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><path fill="currentColor" d="M6 2h7v2h-2.6l-2.2 8H11v2H4v-2h2.6l2.2-8H6z"/></svg>\n'
                    '  </mj-segment>\n'
                    '  <mj-segment value="underline" aria-label="Underline" title="Underline (Ctrl+U)">\n'
                    '    <svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><path fill="currentColor" d="M4 1h2v6a2 2 0 0 0 4 0V1h2v6a4 4 0 0 1-8 0zM3 13h10v2H3z"/></svg>\n'
                    '  </mj-segment>\n'
                    '  <mj-segment value="strike" aria-label="Strikethrough" title="Strikethrough">\n'
                    '    <svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><path fill="currentColor" d="M2 7h12v2H2zm6-6c2 0 3.5 1 3.9 2.5l-1.9.6C9.8 3.4 9.1 3 8 3 6.7 3 6 3.6 6 4.3c0 .5.3.9 1 1.2H4.5A2.8 2.8 0 0 1 4 4.3C4 2.4 5.7 1 8 1zm3.4 9c.4.5.6 1 .6 1.7 0 2-1.8 3.3-4.1 3.3-2.2 0-3.7-1.1-4.1-2.7l1.9-.6c.3.8 1 1.3 2.2 1.3 1.3 0 2.1-.6 2.1-1.3 0-.6-.4-1.2-1.4-1.7z"/></svg>\n'
                    '  </mj-segment>\n'
                    '</mj-segmented-control>\n'
                    '<p id="format-state" class="readout"></p>'
                ),
                css=(
                    "body { padding: var(--mj-space-4); }\n"
                    ".readout { margin-block-start: var(--mj-space-3); color: var(--mj-text-muted); }\n"
                ),
                script=(
                    'const control = document.getElementById("demo-format")\n'
                    'const state = document.getElementById("format-state")\n'
                    'const show = () => {\n'
                    '  const names = control.selectedSegments.map((segment) => segment.getAttribute("aria-label"))\n'
                    '  state.textContent = `value = "${control.value}" (pressed: ${names.join(", ") || "none"})`\n'
                    '}\n'
                    'control.addEventListener("mj-change", show)\n'
                    'show()\n'
                ),
            ),
            ComponentExample(
                key="action",
                title="Action toolbar",
                description=(
                    "<p><code>mode=\"action\"</code> makes a toolbar: segments hold no state and each "
                    "activation fires <code>mj-action</code> with the segment's <code>value</code>. Tab in "
                    "once, then move with ArrowLeft / ArrowRight (Paste is <code>disabled</code> and is "
                    "skipped).</p>"
                ),
                html=(
                    '<mj-segmented-control id="demo-actions" mode="action" label="Clipboard">\n'
                    '  <mj-segment value="cut">Cut</mj-segment>\n'
                    '  <mj-segment value="copy">Copy</mj-segment>\n'
                    '  <mj-segment value="paste" disabled>Paste</mj-segment>\n'
                    '  <mj-segment value="select-all">Select all</mj-segment>\n'
                    '</mj-segmented-control>\n'
                    '<p id="action-state" class="readout">No action yet.</p>'
                ),
                css=(
                    "body { padding: var(--mj-space-4); }\n"
                    ".readout { margin-block-start: var(--mj-space-3); color: var(--mj-text-muted); }\n"
                ),
                script=(
                    'const toolbar = document.getElementById("demo-actions")\n'
                    'const state = document.getElementById("action-state")\n'
                    'let count = 0\n'
                    'toolbar.addEventListener("mj-action", (event) => {\n'
                    '  count = count + 1\n'
                    '  state.textContent = `Action #${count}: ${event.detail.value}`\n'
                    '})\n'
                ),
            ),
            ComponentExample(
                key="sizes-and-states",
                title="Sizes, stretch and states",
                description=(
                    "<p>The first control has a <code>disabled</code> segment (skipped by the arrow keys). "
                    "Below it: <code>size=\"sm\"</code>, <code>size=\"lg\"</code> (font and padding "
                    "change, the height stays), a <code>stretch</code> control filling the row and a fully "
                    "<code>disabled</code> control.</p>"
                ),
                html=(
                    '<mj-segmented-control value="list" label="Layout">\n'
                    '  <mj-segment value="list">List</mj-segment>\n'
                    '  <mj-segment value="grid">Grid</mj-segment>\n'
                    '  <mj-segment value="board" disabled>Board (beta)</mj-segment>\n'
                    '  <mj-segment value="timeline">Timeline</mj-segment>\n'
                    '</mj-segmented-control>\n'
                    '\n'
                    '<mj-segmented-control size="sm" value="s" label="Small size">\n'
                    '  <mj-segment value="s">Small</mj-segment>\n'
                    '  <mj-segment value="m">Medium</mj-segment>\n'
                    '  <mj-segment value="l">Large</mj-segment>\n'
                    '</mj-segmented-control>\n'
                    '\n'
                    '<mj-segmented-control size="lg" value="l" label="Large size">\n'
                    '  <mj-segment value="s">Small</mj-segment>\n'
                    '  <mj-segment value="m">Medium</mj-segment>\n'
                    '  <mj-segment value="l">Large</mj-segment>\n'
                    '</mj-segmented-control>\n'
                    '\n'
                    '<mj-segmented-control stretch value="monthly" label="Billing period">\n'
                    '  <mj-segment value="monthly">Monthly</mj-segment>\n'
                    '  <mj-segment value="quarterly">Quarterly</mj-segment>\n'
                    '  <mj-segment value="yearly">Yearly (save 20%)</mj-segment>\n'
                    '</mj-segmented-control>\n'
                    '\n'
                    '<mj-segmented-control disabled value="on" label="Disabled control">\n'
                    '  <mj-segment value="on">On</mj-segment>\n'
                    '  <mj-segment value="off">Off</mj-segment>\n'
                    '</mj-segmented-control>'
                ),
                css=(
                    "body { padding: var(--mj-space-4); display: grid; gap: var(--mj-space-3); justify-items: start; }\n"
                    "mj-segmented-control[stretch] { justify-self: stretch; }\n"
                ),
            ),
            ComponentExample(
                key="form",
                title="Form participation",
                description=(
                    "<p>Three controls in a <code>&lt;form&gt;</code>: a select-mode <code>shipping</code> "
                    "with a default, a toggle-mode <code>extras</code> (submitted as one comma-separated "
                    "entry) and a <code>required</code> <code>billing</code> with no default. Submit with "
                    "Billing empty to see the validation message; Reset restores the <code>value</code> "
                    "attributes.</p>"
                ),
                html=(
                    '<form id="order-form">\n'
                    '  <p class="field-label">Shipping</p>\n'
                    '  <mj-segmented-control name="shipping" value="standard" label="Shipping">\n'
                    '    <mj-segment value="economy">Economy</mj-segment>\n'
                    '    <mj-segment value="standard">Standard</mj-segment>\n'
                    '    <mj-segment value="express">Express</mj-segment>\n'
                    '  </mj-segmented-control>\n'
                    '  <p class="field-label">Extras</p>\n'
                    '  <mj-segmented-control name="extras" mode="toggle" value="gift-wrap" label="Extras">\n'
                    '    <mj-segment value="gift-wrap">Gift wrap</mj-segment>\n'
                    '    <mj-segment value="insurance">Insurance</mj-segment>\n'
                    '    <mj-segment value="signature">Signature</mj-segment>\n'
                    '  </mj-segmented-control>\n'
                    '  <p class="field-label">Billing (required)</p>\n'
                    '  <mj-segmented-control id="billing" name="billing" required required-message="Choose a billing period." label="Billing">\n'
                    '    <mj-segment value="monthly">Monthly</mj-segment>\n'
                    '    <mj-segment value="yearly">Yearly</mj-segment>\n'
                    '  </mj-segmented-control>\n'
                    '  <div class="actions">\n'
                    '    <button type="submit">Submit</button>\n'
                    '    <button type="reset">Reset</button>\n'
                    '  </div>\n'
                    '  <output id="order-output">Not submitted yet.</output>\n'
                    '</form>'
                ),
                css=(
                    "body { padding: var(--mj-space-4); }\n"
                    "form { display: grid; gap: var(--mj-space-2); justify-items: start; }\n"
                    ".field-label { margin: var(--mj-space-2) 0 0; font-weight: var(--mj-font-weight-medium); }\n"
                    ".actions { display: flex; gap: var(--mj-space-2); margin-block-start: var(--mj-space-3); }\n"
                    "output { color: var(--mj-text-muted); font-family: var(--mj-font-mono, monospace); }\n"
                ),
                script=(
                    'const form = document.getElementById("order-form")\n'
                    'const output = document.getElementById("order-output")\n'
                    'form.addEventListener("submit", (event) => {\n'
                    '  event.preventDefault()\n'
                    '  const entries = Object.fromEntries(new FormData(form))\n'
                    '  output.textContent = JSON.stringify(entries)\n'
                    '  mjSandbox.log("submit", entries)\n'
                    '})\n'
                    'form.addEventListener("reset", () => {\n'
                    '  output.textContent = "Reset to the default values."\n'
                    '})\n'
                    'document.getElementById("billing").addEventListener("invalid", (event) => {\n'
                    '  mjSandbox.log("invalid", { name: "billing", message: event.target.validationMessage })\n'
                    '})\n'
                ),
            ),
            ComponentExample(
                key="events",
                title="Events and scripting",
                description=(
                    "<p>The script clicks the second segment and presses ArrowRight on it, so the Events "
                    "panel shows two <code>mj-change</code> events. It then assigns <code>value</code> "
                    "(no event) and logs <code>selectedSegment</code>; the line below follows every "
                    "change.</p>"
                ),
                html=(
                    '<mj-segmented-control id="demo-events" value="table" label="Report format">\n'
                    '  <mj-segment value="table">Table</mj-segment>\n'
                    '  <mj-segment value="chart">Chart</mj-segment>\n'
                    '  <mj-segment value="summary">Summary</mj-segment>\n'
                    '  <mj-segment value="raw">Raw data</mj-segment>\n'
                    '</mj-segmented-control>\n'
                    '<p id="events-state" class="readout"></p>'
                ),
                css=(
                    "body { padding: var(--mj-space-4); }\n"
                    ".readout { margin-block-start: var(--mj-space-3); color: var(--mj-text-muted); }\n"
                ),
                script=(
                    'const control = document.getElementById("demo-events")\n'
                    'const state = document.getElementById("events-state")\n'
                    'const show = () => {\n'
                    '  state.textContent = `value = "${control.value}" (${control.selectedSegment.textContent})`\n'
                    '}\n'
                    'control.addEventListener("mj-change", show)\n'
                    '\n'
                    'const buttons = control.shadowRoot.querySelectorAll(\'[part="segment"]\')\n'
                    'buttons[1].click()\n'
                    'buttons[1].focus()\n'
                    'buttons[1].dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowRight", bubbles: true, cancelable: true }))\n'
                    '\n'
                    'control.value = "raw"\n'
                    'show()\n'
                    'mjSandbox.log("value property set (no mj-change)", { value: control.value, selected: control.selectedSegment.textContent })\n'
                ),
            ),
        ],
        slots=[],
        properties=[
            ("value", "string. The live value: one segment value (select), a comma-separated list (toggle), always empty in action mode. Setting it changes the selection and the submitted value without emitting `mj-change` and leaves the `value` attribute alone."),
            ("segments", "Element[]. The `<mj-segment>` descendants (read-only)."),
            ("selectedSegment", "Element | null. Select mode: the checked `<mj-segment>`; null in other modes or when nothing is selected."),
            ("selectedSegments", "Element[]. The pressed `<mj-segment>` elements in toggle mode (the checked one in select mode, empty in action mode)."),
            ("form", "HTMLFormElement | null. The owning form."),
            ("validity", "ValidityState. Constraint-validation state (`valueMissing` when `required` and nothing is selected)."),
            ("validationMessage", "string. The current validation message."),
        ],
        methods=[
            ("focus()", "Focuses the segment that holds the tab stop (the checked one in select mode)."),
            ("checkValidity() -> boolean", "Runs constraint validation; fires `invalid` when it fails."),
            ("reportValidity() -> boolean", "As `checkValidity()`, and shows the browser's validation message."),
        ],
        parts=[
            ("container", "The row holding the segment buttons (carries the radiogroup / group / toolbar role)."),
            ("segment", "Each segment `<button>`; style the selected one with `::part(segment)[aria-checked=\"true\"]` or `[aria-pressed=\"true\"]`."),
            ("segment-label", "The copy of the segment's content inside each button."),
        ],
        css_properties=[
            ("--mj-segmented-height", "Minimum height of the control (default var(--mj-control-height-md)); `size` does not change it."),
            ("--mj-segmented-gap", "Gap between segments (default 2px)."),
            ("--mj-segmented-border-radius", "Corner radius of the track (default var(--mj-radius-md))."),
            ("--mj-segmented-segment-radius", "Corner radius of each segment (default var(--mj-radius-sm))."),
        ],
    ),
    ComponentDoc(
        tag="mj-split-button",
        title="Split Button",
        group="selection",
        summary=(
            "Primary action button paired with a dropdown trigger that opens a keyboard-operable menu "
            "of alternate actions."
        ),
        description=(
            "<p><code>&lt;mj-split-button&gt;</code> renders a primary button and, next to it, a chevron "
            "button (<code>aria-haspopup=\"menu\"</code>) that opens a <code>role=\"menu\"</code> popup. "
            "The menu is built from the <code>&lt;mj-menu-item&gt;</code> descendants of the element: "
            "plain markup the component reads (not a custom element, not slotted). Each item shows its "
            "text as plain text, its value is its <code>value</code> attribute or, without one, its text, "
            "and <code>disabled</code> disables it. A MutationObserver follows the items, so items added "
            "or changed later appear without re-creating the element; with no items the dropdown button "
            "is disabled. (Shortcut hints, separators, groups and checkable items are "
            "<code>&lt;mj-menu-button&gt;</code> features; the split button ignores them.)</p>"
            "<p>The primary button fires <code>mj-primary-click</code>; choosing an item fires "
            "<code>mj-menu-select</code>. With <code>dynamic</code>, the item chosen last becomes the "
            "primary action: the primary label shows its text, <code>activeItem</code> returns it, "
            "<code>mj-primary-click</code> carries its <code>value</code> and element, and a polite "
            "announcement tells screen-reader users the default changed. Without <code>dynamic</code> "
            "<code>mj-primary-click</code> carries <code>{ value: \"\", item: null }</code>.</p>"
            "<p>Keyboard: on the dropdown button, Enter, Space or ArrowDown open the menu on the first "
            "enabled item, ArrowUp on the last. Opening moves focus into the menu, which tracks the active "
            "item with <code>aria-activedescendant</code>: ArrowDown / ArrowUp, Home and End move over "
            "enabled items, Enter or Space choose, Escape closes and returns focus to the dropdown button, "
            "Tab closes and moves on. A click outside or focus leaving the menu closes it.</p>"
        ),
        how_to_use=(
            "<p>Set <code>label</code> for the primary button text and put "
            "<code>&lt;mj-menu-item value=\"...\"&gt;</code> elements between the tags. Use "
            "<code>variant</code> (<code>secondary</code>, <code>danger</code>) and <code>size</code> for "
            "the look, the <code>primary-icon</code> slot for a leading icon and "
            "<code>dropdown-label</code> to name the chevron button (default \"More actions\"). "
            "<code>disabled</code> turns both buttons off; <code>primary-disabled</code> only the primary "
            "one, so the alternatives stay reachable. Listen for <code>mj-primary-click</code> and "
            "<code>mj-menu-select</code> (<code>{ item, value }</code>); add <code>dynamic</code> when "
            "the last-picked action should become the default.</p>"
        ),
        example="",
        attributes=[
            AttributeDoc(name="label", description="Text and accessible name of the primary button (replaced by the active item's text in `dynamic` mode once an item was chosen).",
                         kind="string", values=["Save", "Export", "Deploy"]),
            AttributeDoc(name="variant", description="Colour scheme of both buttons.",
                         kind="enum", values=["primary", "secondary", "danger"], default="primary"),
            AttributeDoc(name="size", description="Height and font size of both buttons.",
                         kind="enum", values=["sm", "md", "lg"], default="md"),
            AttributeDoc(name="disabled", description="Disables the primary and the dropdown button and closes an open menu.",
                         kind="boolean"),
            AttributeDoc(name="primary-disabled", description="Disables only the primary button; the dropdown menu stays usable.",
                         kind="boolean"),
            AttributeDoc(name="open", description="Shows the menu. Setting it directly skips the cancelable `mj-open` event and does not move focus; the component removes it when the menu closes.",
                         kind="boolean"),
            AttributeDoc(name="dynamic", description="The item chosen last becomes the primary action (label, `activeItem`, `mj-primary-click` detail).",
                         kind="boolean"),
            AttributeDoc(name="dropdown-label", description="Accessible name of the dropdown button.",
                         kind="string", values=["More save options"], default="More actions"),
        ],
        events=[
            ("mj-primary-click", "The primary button was activated (not while `disabled` or `primary-disabled`).",
             "{ value: string (the active item's value in dynamic mode, else ''), item: Element | null (the active <mj-menu-item>) }"),
            ("mj-menu-select", "A menu item was chosen by click, Enter or Space; the menu then closes.",
             "{ item: Element (the <mj-menu-item>), value: string }"),
            ("mj-open", "Cancelable; fired before the menu opens from the dropdown button or `open = true`. `preventDefault()` keeps it closed.",
             "{}"),
            ("mj-close", "The menu closed (choice, Escape, Tab, outside click, focus leaving, `open = false`, disabling).",
             "{}"),
        ],
        examples=[
            ComponentExample(
                key="basic",
                title="Basic usage",
                description=(
                    "<p>Click <b>Save</b> to log <code>mj-primary-click</code>. Open the chevron (or focus "
                    "it and press ArrowDown) and choose an item to log <code>mj-menu-select</code>; the last "
                    "item is <code>disabled</code> and skipped by the arrow keys.</p>"
                ),
                html=(
                    '<mj-split-button label="Save">\n'
                    '  <mj-menu-item value="save-draft">Save as draft</mj-menu-item>\n'
                    '  <mj-menu-item value="save-template">Save as template</mj-menu-item>\n'
                    '  <mj-menu-item value="export">Export&hellip;</mj-menu-item>\n'
                    '  <mj-menu-item value="publish" disabled>Publish (needs review)</mj-menu-item>\n'
                    '</mj-split-button>'
                ),
                css="body { padding: var(--mj-space-4); }",
                height=260,
            ),
            ComponentExample(
                key="variants",
                title="Variants and icons",
                description=(
                    "<p><code>variant=\"primary\"</code> (default), <code>secondary</code> and "
                    "<code>danger</code>, each with a leading icon in the <code>primary-icon</code> slot. "
                    "Toggle the slot in the Slots panel to remove or restore the first icon.</p>"
                ),
                html=(
                    '<mj-split-button label="Save" dropdown-label="More save options">\n'
                    '  <svg slot="primary-icon" viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><path fill="currentColor" d="M2 2h9l3 3v9H2zm2 1v3h6V3zm1 6v4h6V9z"/></svg>\n'
                    '  <mj-menu-item value="save-as">Save as&hellip;</mj-menu-item>\n'
                    '  <mj-menu-item value="save-copy">Save a copy</mj-menu-item>\n'
                    '</mj-split-button>\n'
                    '\n'
                    '<mj-split-button label="Download" variant="secondary" dropdown-label="Other formats">\n'
                    '  <svg slot="primary-icon" viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><path fill="currentColor" d="M7 1h2v7.6l2.3-2.3 1.4 1.4L8 12.4 3.3 7.7l1.4-1.4L7 8.6zM2 13h12v2H2z"/></svg>\n'
                    '  <mj-menu-item value="csv">Download CSV</mj-menu-item>\n'
                    '  <mj-menu-item value="json">Download JSON</mj-menu-item>\n'
                    '</mj-split-button>\n'
                    '\n'
                    '<mj-split-button label="Delete" variant="danger" dropdown-label="More delete options">\n'
                    '  <svg slot="primary-icon" viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><path fill="currentColor" d="M6 1h4l1 1h3v2H2V2h3zM3 5h10l-1 10H4z"/></svg>\n'
                    '  <mj-menu-item value="delete-all">Delete all versions</mj-menu-item>\n'
                    '  <mj-menu-item value="move-trash">Move to trash</mj-menu-item>\n'
                    '</mj-split-button>'
                ),
                css="body { padding: var(--mj-space-4); display: flex; flex-wrap: wrap; gap: var(--mj-space-3); align-items: center; }",
                height=220,
            ),
            ComponentExample(
                key="sizes-and-states",
                title="Sizes and states",
                description=(
                    "<p>The first button is <code>primary-disabled</code>: <b>Merge</b> is off until checks "
                    "pass but the chevron still opens the alternatives. Below: <code>size=\"sm\"</code>, "
                    "default and <code>size=\"lg\"</code>, and a fully <code>disabled</code> button.</p>"
                ),
                html=(
                    '<mj-split-button label="Merge" primary-disabled dropdown-label="Other merge methods">\n'
                    '  <mj-menu-item value="squash">Squash and merge</mj-menu-item>\n'
                    '  <mj-menu-item value="rebase">Rebase and merge</mj-menu-item>\n'
                    '</mj-split-button>\n'
                    '\n'
                    '<div class="row">\n'
                    '  <mj-split-button label="Small" size="sm"><mj-menu-item>Option</mj-menu-item></mj-split-button>\n'
                    '  <mj-split-button label="Medium"><mj-menu-item>Option</mj-menu-item></mj-split-button>\n'
                    '  <mj-split-button label="Large" size="lg"><mj-menu-item>Option</mj-menu-item></mj-split-button>\n'
                    '</div>\n'
                    '\n'
                    '<mj-split-button label="Disabled" disabled><mj-menu-item>Option</mj-menu-item></mj-split-button>'
                ),
                css=(
                    "body { padding: var(--mj-space-4); display: grid; gap: var(--mj-space-3); justify-items: start; }\n"
                    ".row { display: flex; gap: var(--mj-space-3); align-items: center; }\n"
                ),
                height=240,
            ),
            ComponentExample(
                key="dynamic",
                title="Dynamic default action",
                description=(
                    "<p>With <code>dynamic</code> the format chosen last becomes the primary action. Pick "
                    "<b>Export as CSV</b> from the menu, then click the primary button: "
                    "<code>mj-primary-click</code> now carries <code>value: \"csv\"</code> and the item.</p>"
                ),
                html=(
                    '<mj-split-button id="demo-export" label="Export" dynamic dropdown-label="Choose export format">\n'
                    '  <mj-menu-item value="pdf">Export as PDF</mj-menu-item>\n'
                    '  <mj-menu-item value="csv">Export as CSV</mj-menu-item>\n'
                    '  <mj-menu-item value="xlsx">Export as Excel</mj-menu-item>\n'
                    '</mj-split-button>\n'
                    '<p id="export-state" class="readout">Primary action: default (no format chosen).</p>'
                ),
                css=(
                    "body { padding: var(--mj-space-4); }\n"
                    ".readout { margin-block-start: var(--mj-space-3); color: var(--mj-text-muted); }\n"
                ),
                script=(
                    'const button = document.getElementById("demo-export")\n'
                    'const state = document.getElementById("export-state")\n'
                    'button.addEventListener("mj-menu-select", (event) => {\n'
                    '  state.textContent = `Primary action is now: ${event.detail.value}`\n'
                    '})\n'
                    'button.addEventListener("mj-primary-click", (event) => {\n'
                    '  state.textContent = `Ran: ${event.detail.value || "default export"}`\n'
                    '})\n'
                ),
                height=240,
            ),
            ComponentExample(
                key="events",
                title="Keyboard and events",
                description=(
                    "<p>The script sets <code>open = true</code> (<code>mj-open</code>; focus moves into the "
                    "menu), presses ArrowDown and Enter (<code>mj-menu-select</code>, <code>mj-close</code>) "
                    "and clicks the primary button (<code>mj-primary-click</code> with the chosen value). "
                    "Tick <b>Lock the menu</b> to cancel <code>mj-open</code> with "
                    "<code>preventDefault()</code>.</p>"
                ),
                html=(
                    '<mj-split-button id="demo-keys" label="Send" dynamic dropdown-label="More send options">\n'
                    '  <mj-menu-item value="send-later">Schedule send</mj-menu-item>\n'
                    '  <mj-menu-item value="send-test">Send test email</mj-menu-item>\n'
                    '  <mj-menu-item value="send-segment">Send to a segment</mj-menu-item>\n'
                    '</mj-split-button>\n'
                    '<label class="lock"><input type="checkbox" id="lock-menu"> Lock the menu (cancel <code>mj-open</code>)</label>'
                ),
                css=(
                    "body { padding: var(--mj-space-4); }\n"
                    ".lock { display: flex; gap: var(--mj-space-2); align-items: center; margin-block-start: var(--mj-space-3); }\n"
                ),
                script=(
                    'const button = document.getElementById("demo-keys")\n'
                    'const lock = document.getElementById("lock-menu")\n'
                    'button.addEventListener("mj-open", (event) => {\n'
                    '  if (lock.checked) {\n'
                    '    event.preventDefault()\n'
                    '    mjSandbox.log("mj-open cancelled", {})\n'
                    '  }\n'
                    '})\n'
                    '\n'
                    'button.open = true\n'
                    'const menu = button.shadowRoot.querySelector(\'[part="menu"]\')\n'
                    'const press = (key) => menu.dispatchEvent(new KeyboardEvent("keydown", { key, bubbles: true, cancelable: true }))\n'
                    'press("ArrowDown")\n'
                    'press("Enter")\n'
                    '\n'
                    'button.shadowRoot.querySelector(\'[part="primary"]\').click()\n'
                    'mjSandbox.log("activeItem", { value: button.activeItem.getAttribute("value"), open: button.open })\n'
                ),
                height=240,
            ),
        ],
        slots=[
            ("primary-icon", "Leading icon inside the primary button.",
             '<svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><path fill="currentColor" d="M2 2h9l3 3v9H2zm2 1v3h6V3zm1 6v4h6V9z"/></svg>'),
        ],
        properties=[
            ("open", "boolean. Whether the menu is shown. Setting `true` opens it like the dropdown button (fires cancelable `mj-open`, focuses the menu); `false` closes it (`mj-close`)."),
            ("menuItems", "Element[]. The `<mj-menu-item>` descendants (read-only)."),
            ("activeItem", "Element | null. Dynamic mode: the `<mj-menu-item>` the primary button stands for. Assigning an item sets it (no event); null restores `label`."),
        ],
        methods=[],
        parts=[
            ("container", "The wrapper around both buttons (carries the outline)."),
            ("primary", "The primary `<button>`."),
            ("primary-label", "The primary button's text."),
            ("divider", "The line between the two buttons."),
            ("dropdown-trigger", "The chevron `<button>` that opens the menu."),
            ("dropdown-icon", "The chevron SVG (rotates while open)."),
            ("popup", "The floating panel holding the menu."),
            ("menu", "The `role=\"menu\"` element that takes focus while open."),
            ("menu-item", "Each menu row (`.focused` marks the active one, `aria-disabled` a disabled one)."),
            ("menu-item-label", "The text of each menu row."),
        ],
        css_properties=[
            ("--mj-split-button-height", "Minimum height of both buttons at the default size (default var(--mj-control-height-md)); `size=sm|lg` use the sm / lg control heights."),
            ("--mj-split-button-border-radius", "Outer corner radius (default var(--mj-radius-md))."),
            ("--mj-split-button-divider-color", "Colour of the divider (default a 30% mix of the on-accent text into the button colour; secondary uses var(--mj-border-strong))."),
            ("--mj-split-button-popup-min-width", "Minimum width of the menu popup (default 10rem)."),
        ],
    ),
    ComponentDoc(
        tag="mj-menu-button",
        title="Menu Button",
        group="selection",
        summary=(
            "Single trigger button that opens an actions menu with shortcut hints, separators, groups "
            "and checkable items (kebab, overflow, meatball menus)."
        ),
        description=(
            "<p><code>&lt;mj-menu-button&gt;</code> renders a trigger button "
            "(<code>aria-haspopup=\"menu\"</code>) that opens a <code>role=\"menu\"</code> popup. The "
            "menu mirrors the element's children, which are plain markup the component reads (not custom "
            "elements, not slotted):</p>"
            "<ul>"
            "<li><code>&lt;mj-menu-item&gt;</code>: an action row. Its text is the label (plain text), "
            "<code>value</code> the value (default: the text), <code>shortcut</code> a hint shown at the "
            "end of the row, <code>variant=\"danger\"</code> the destructive style and "
            "<code>disabled</code> disables it.</li>"
            "<li><code>&lt;mj-menu-item type=\"checkbox\"&gt;</code> / <code>type=\"radio\"</code>: a "
            "checkable row (<code>menuitemcheckbox</code> / <code>menuitemradio</code>) whose state is "
            "its <code>checked</code> attribute. Activating a checkbox flips it; a radio becomes the only "
            "checked radio among its siblings (for example within one group).</li>"
            "<li><code>&lt;mj-menu-separator&gt;</code>: a divider.</li>"
            "<li><code>&lt;mj-menu-group label=\"...\"&gt;</code>: a labelled <code>role=\"group\"</code> "
            "of rows.</li>"
            "</ul>"
            "<p>Other wrapper elements are looked through; elements with a <code>slot</code> attribute are "
            "skipped. A MutationObserver follows the children, so items added, removed or changed later "
            "(including <code>checked</code>) appear without re-creating the element; with no items the "
            "trigger is disabled. Submenus are not supported.</p>"
            "<p>The <code>label</code> attribute is both the visible trigger text and its accessible name. "
            "With <code>icon-only</code> the text is hidden (put an icon in the <code>trigger-icon</code> "
            "slot) and <code>label</code> or <code>aria-label</code> is required; without either the "
            "component logs a console error and falls back to the name \"Actions\".</p>"
            "<p>Keyboard: on the trigger, Enter, Space or ArrowDown open the menu on the first enabled "
            "item, ArrowUp on the last. Opening moves focus into the menu, which tracks the active item "
            "with <code>aria-activedescendant</code>: ArrowDown / ArrowUp, Home and End move over enabled "
            "items, Enter or Space activate, Escape closes and returns focus to the trigger, Tab closes "
            "and moves on. A click or focus outside closes it.</p>"
        ),
        how_to_use=(
            "<p>Set <code>label</code> for the trigger text and put <code>&lt;mj-menu-item "
            "value=\"...\"&gt;</code> elements (optionally <code>&lt;mj-menu-separator&gt;</code> and "
            "<code>&lt;mj-menu-group label&gt;</code>) between the tags. For a kebab menu add "
            "<code>icon-only</code> and an SVG with <code>slot=\"trigger-icon\"</code>, keeping "
            "<code>label</code> as the accessible name. Use <code>placement</code> to position the popup "
            "and <code>size</code> for the trigger. Listen for <code>mj-select</code> "
            "(<code>{ item, value }</code>, plus <code>checked</code> for checkable items).</p>"
        ),
        example="",
        attributes=[
            AttributeDoc(name="label", description="Visible trigger text and the trigger's accessible name (text hidden with `icon-only`).",
                         kind="string", values=["Row actions", "More options"]),
            AttributeDoc(name="aria-label", description="Accessible name of the trigger when `label` is absent (no visible text).",
                         kind="string"),
            AttributeDoc(name="icon-only", description="Square trigger showing only the `trigger-icon` slot; requires `label` or `aria-label`.",
                         kind="boolean"),
            AttributeDoc(name="disabled", description="Disables the trigger and closes an open menu.",
                         kind="boolean"),
            AttributeDoc(name="open", description="Shows the menu. Setting it directly skips the cancelable `mj-open` event and does not move focus; the component removes it when the menu closes.",
                         kind="boolean"),
            AttributeDoc(name="placement", description="Preferred popup side and alignment relative to the trigger (flips when there is no room).",
                         kind="enum", values=["bottom-start", "bottom", "bottom-end", "top-start", "top", "top-end",
                                              "start", "start-top", "start-bottom", "end", "end-top", "end-bottom"],
                         default="bottom-start"),
            AttributeDoc(name="size", description="Trigger height and font size.",
                         kind="enum", values=["sm", "md", "lg"], default="md"),
        ],
        events=[
            ("mj-select", "A menu item was activated by click, Enter or Space; the menu then closes. Checkable items update their `checked` attribute first.",
             "{ item: Element (the <mj-menu-item>), value: string, checked?: boolean (checkbox / radio items only) }"),
            ("mj-open", "Cancelable; fired before the menu opens from the trigger or `open = true`. `preventDefault()` keeps it closed.",
             "{}"),
            ("mj-close", "The menu closed (activation, Escape, Tab, outside click or focus, `open = false`, disabling).",
             "{}"),
        ],
        examples=[
            ComponentExample(
                key="basic",
                title="Basic usage",
                description=(
                    "<p>A labelled trigger with shortcut hints, a separator and a <code>danger</code> item. "
                    "Click the trigger (or focus it and press ArrowDown), then pick an item to log "
                    "<code>mj-select</code>.</p>"
                ),
                html=(
                    '<mj-menu-button label="Row actions">\n'
                    '  <mj-menu-item value="edit" shortcut="E">Edit</mj-menu-item>\n'
                    '  <mj-menu-item value="duplicate" shortcut="Ctrl+D">Duplicate</mj-menu-item>\n'
                    '  <mj-menu-item value="archive">Archive</mj-menu-item>\n'
                    '  <mj-menu-separator></mj-menu-separator>\n'
                    '  <mj-menu-item value="delete" variant="danger" shortcut="Del">Delete</mj-menu-item>\n'
                    '</mj-menu-button>'
                ),
                css="body { padding: var(--mj-space-4); }",
                height=300,
            ),
            ComponentExample(
                key="icon-only",
                title="Icon-only (kebab) trigger",
                description=(
                    "<p>A kebab menu at the end of a card header: <code>icon-only</code> with an SVG in the "
                    "<code>trigger-icon</code> slot, named by <code>label</code>, and "
                    "<code>placement=\"bottom-end\"</code> so the popup aligns with the trigger's end edge. "
                    "Next to it, an icon plus visible label.</p>"
                ),
                html=(
                    '<div class="card">\n'
                    '  <h3>Q3 revenue report</h3>\n'
                    '  <mj-menu-button icon-only label="More options for Q3 revenue report" placement="bottom-end">\n'
                    '    <svg slot="trigger-icon" viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><circle cx="8" cy="3" r="1.5" fill="currentColor"/><circle cx="8" cy="8" r="1.5" fill="currentColor"/><circle cx="8" cy="13" r="1.5" fill="currentColor"/></svg>\n'
                    '    <mj-menu-item value="rename">Rename</mj-menu-item>\n'
                    '    <mj-menu-item value="move">Move to folder&hellip;</mj-menu-item>\n'
                    '    <mj-menu-item value="download">Download</mj-menu-item>\n'
                    '    <mj-menu-separator></mj-menu-separator>\n'
                    '    <mj-menu-item value="delete" variant="danger">Delete</mj-menu-item>\n'
                    '  </mj-menu-button>\n'
                    '</div>\n'
                    '\n'
                    '<mj-menu-button label="Share">\n'
                    '  <svg slot="trigger-icon" viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><path fill="currentColor" d="M12 1a3 3 0 1 1-2.6 4.5L6 7.3a3 3 0 0 1 0 1.4l3.4 1.8a3 3 0 1 1-.9 1.8L5.1 10.5a3 3 0 1 1 0-5l3.4-1.8A3 3 0 0 1 12 1z"/></svg>\n'
                    '  <mj-menu-item value="copy-link">Copy link</mj-menu-item>\n'
                    '  <mj-menu-item value="email">Email</mj-menu-item>\n'
                    '</mj-menu-button>'
                ),
                css=(
                    "body { padding: var(--mj-space-4); display: grid; gap: var(--mj-space-4); justify-items: start; }\n"
                    ".card { display: flex; align-items: center; justify-content: space-between; gap: var(--mj-space-3);\n"
                    "  inline-size: min(24rem, 100%); padding: var(--mj-space-3) var(--mj-space-4);\n"
                    "  border: 1px solid var(--mj-border); border-radius: var(--mj-radius-md); background: var(--mj-surface); }\n"
                    ".card h3 { margin: 0; font-size: var(--mj-font-size-md); }\n"
                ),
                height=300,
            ),
            ComponentExample(
                key="checkable",
                title="Groups and checkable items",
                description=(
                    "<p>Labelled <code>&lt;mj-menu-group&gt;</code>s: checkbox items under <b>Show</b> and "
                    "radio items under <b>Zoom</b>, separated by <code>&lt;mj-menu-separator&gt;</code>. The "
                    "menu is open on load; each activation flips the <code>checked</code> attribute, logs "
                    "<code>mj-select</code> with <code>checked</code> and updates the summary.</p>"
                ),
                html=(
                    '<mj-menu-button id="demo-view" label="View" open>\n'
                    '  <mj-menu-group label="Show">\n'
                    '    <mj-menu-item type="checkbox" value="gridlines" checked>Gridlines</mj-menu-item>\n'
                    '    <mj-menu-item type="checkbox" value="ruler">Ruler</mj-menu-item>\n'
                    '    <mj-menu-item type="checkbox" value="comments" checked>Comments</mj-menu-item>\n'
                    '  </mj-menu-group>\n'
                    '  <mj-menu-separator></mj-menu-separator>\n'
                    '  <mj-menu-group label="Zoom">\n'
                    '    <mj-menu-item type="radio" value="75">75%</mj-menu-item>\n'
                    '    <mj-menu-item type="radio" value="100" checked>100%</mj-menu-item>\n'
                    '    <mj-menu-item type="radio" value="150">150%</mj-menu-item>\n'
                    '  </mj-menu-group>\n'
                    '</mj-menu-button>\n'
                    '<p id="view-state" class="readout"></p>'
                ),
                css=(
                    "body { padding: var(--mj-space-4); }\n"
                    ".readout { margin-block-start: var(--mj-space-3); color: var(--mj-text-muted); }\n"
                ),
                script=(
                    'const menu = document.getElementById("demo-view")\n'
                    'const state = document.getElementById("view-state")\n'
                    'const show = () => {\n'
                    '  const shown = [...menu.querySelectorAll(\'[type="checkbox"][checked]\')].map((item) => item.textContent)\n'
                    '  const zoom = menu.querySelector(\'[type="radio"][checked]\')\n'
                    '  state.textContent = `Showing: ${shown.join(", ") || "nothing"}; zoom ${zoom ? zoom.textContent : "unset"}`\n'
                    '}\n'
                    'menu.addEventListener("mj-select", show)\n'
                    'show()\n'
                ),
                height=420,
            ),
            ComponentExample(
                key="sizes-and-states",
                title="Sizes and states",
                description=(
                    "<p>The first menu has a <code>disabled</code> item that the arrow keys skip. Then "
                    "<code>size=\"sm\"</code>, default and <code>size=\"lg\"</code> triggers, a "
                    "<code>disabled</code> trigger and one with <code>placement=\"end-top\"</code>.</p>"
                ),
                html=(
                    '<mj-menu-button label="File">\n'
                    '  <mj-menu-item value="new" shortcut="Ctrl+N">New</mj-menu-item>\n'
                    '  <mj-menu-item value="open" shortcut="Ctrl+O">Open&hellip;</mj-menu-item>\n'
                    '  <mj-menu-item value="revert" disabled>Revert (no changes)</mj-menu-item>\n'
                    '  <mj-menu-item value="close">Close</mj-menu-item>\n'
                    '</mj-menu-button>\n'
                    '\n'
                    '<div class="row">\n'
                    '  <mj-menu-button label="Small" size="sm"><mj-menu-item>Option</mj-menu-item></mj-menu-button>\n'
                    '  <mj-menu-button label="Medium"><mj-menu-item>Option</mj-menu-item></mj-menu-button>\n'
                    '  <mj-menu-button label="Large" size="lg"><mj-menu-item>Option</mj-menu-item></mj-menu-button>\n'
                    '  <mj-menu-button label="Disabled" disabled><mj-menu-item>Option</mj-menu-item></mj-menu-button>\n'
                    '</div>\n'
                    '\n'
                    '<mj-menu-button label="Opens to the end" placement="end-top">\n'
                    '  <mj-menu-item>First</mj-menu-item>\n'
                    '  <mj-menu-item>Second</mj-menu-item>\n'
                    '</mj-menu-button>'
                ),
                css=(
                    "body { padding: var(--mj-space-4); display: grid; gap: var(--mj-space-3); justify-items: start; }\n"
                    ".row { display: flex; gap: var(--mj-space-3); align-items: center; }\n"
                ),
                height=320,
            ),
            ComponentExample(
                key="data-driven",
                title="Items added later",
                description=(
                    "<p>The menu starts empty, so its trigger is disabled. After a simulated fetch the script "
                    "appends <code>&lt;mj-menu-item&gt;</code> elements built from data; the MutationObserver "
                    "rebuilds the menu and enables the trigger.</p>"
                ),
                html=(
                    '<mj-menu-button id="demo-workspaces" label="Switch workspace"></mj-menu-button>\n'
                    '<p id="workspace-state" class="readout">Loading workspaces&hellip;</p>'
                ),
                css=(
                    "body { padding: var(--mj-space-4); }\n"
                    ".readout { margin-block-start: var(--mj-space-3); color: var(--mj-text-muted); }\n"
                ),
                script=(
                    'const menu = document.getElementById("demo-workspaces")\n'
                    'const state = document.getElementById("workspace-state")\n'
                    'const workspaces = [\n'
                    '  { id: "acme", name: "Acme Corp" },\n'
                    '  { id: "globex", name: "Globex" },\n'
                    '  { id: "initech", name: "Initech (read-only)", disabled: true },\n'
                    '  { id: "umbrella", name: "Umbrella Labs" },\n'
                    ']\n'
                    'await new Promise((resolve) => setTimeout(resolve, 500))\n'
                    'for (const workspace of workspaces) {\n'
                    '  const item = document.createElement("mj-menu-item")\n'
                    '  item.setAttribute("value", workspace.id)\n'
                    '  item.textContent = workspace.name\n'
                    '  item.toggleAttribute("disabled", workspace.disabled === true)\n'
                    '  menu.append(item)\n'
                    '}\n'
                    'state.textContent = `${menu.menuItems.length} workspaces loaded.`\n'
                    'menu.addEventListener("mj-select", (event) => {\n'
                    '  state.textContent = `Switched to ${event.detail.item.textContent}.`\n'
                    '})\n'
                ),
                height=280,
            ),
            ComponentExample(
                key="events",
                title="Keyboard and events",
                description=(
                    "<p>The script sets <code>open = true</code> (<code>mj-open</code>; focus moves into the "
                    "menu), presses ArrowDown twice, logs <code>focusedItem</code>, then presses Enter "
                    "(<code>mj-select</code>, <code>mj-close</code>; focus returns to the trigger). Try it "
                    "yourself: focus the trigger, press ArrowUp to open on the last item, Escape to "
                    "close.</p>"
                ),
                html=(
                    '<mj-menu-button id="demo-keys" label="Sort by">\n'
                    '  <mj-menu-item value="name">Name</mj-menu-item>\n'
                    '  <mj-menu-item value="modified">Date modified</mj-menu-item>\n'
                    '  <mj-menu-item value="size">Size</mj-menu-item>\n'
                    '  <mj-menu-item value="type">Type</mj-menu-item>\n'
                    '</mj-menu-button>'
                ),
                css="body { padding: var(--mj-space-4); }",
                script=(
                    'const button = document.getElementById("demo-keys")\n'
                    'button.open = true\n'
                    'const menu = button.shadowRoot.querySelector(\'[part="menu"]\')\n'
                    'const press = (key) => menu.dispatchEvent(new KeyboardEvent("keydown", { key, bubbles: true, cancelable: true }))\n'
                    'press("ArrowDown")\n'
                    'press("ArrowDown")\n'
                    'mjSandbox.log("focusedItem", { value: button.focusedItem.getAttribute("value") })\n'
                    'press("Enter")\n'
                    'mjSandbox.log("after Enter", { open: button.open })\n'
                ),
                height=280,
            ),
        ],
        slots=[
            ("trigger-icon", "Icon inside the trigger, before the label (the only content of an `icon-only` trigger).",
             '<svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><circle cx="8" cy="3" r="1.5" fill="currentColor"/><circle cx="8" cy="8" r="1.5" fill="currentColor"/><circle cx="8" cy="13" r="1.5" fill="currentColor"/></svg>'),
        ],
        properties=[
            ("open", "boolean. Whether the menu is shown. Setting `true` opens it like the trigger (fires cancelable `mj-open`, focuses the menu); `false` closes it (`mj-close`)."),
            ("menuItems", "Element[]. Every `<mj-menu-item>` descendant, including those inside groups (read-only)."),
            ("focusedItem", "Element | null. The `<mj-menu-item>` that is the menu's active descendant while open (read-only)."),
        ],
        methods=[
            ("focus()", "Focuses the trigger button."),
        ],
        parts=[
            ("trigger", "The trigger `<button>`."),
            ("trigger-label", "The trigger text (hidden when empty or `icon-only`)."),
            ("popup", "The floating panel holding the menu (scrolls past --mj-menu-popup-max-height)."),
            ("menu", "The `role=\"menu\"` element that takes focus while open."),
            ("menu-item", "Each item row (`.focused` marks the active one; `[data-variant=\"danger\"]`, `[aria-disabled=\"true\"]`, `[aria-checked]` mark variants and states)."),
            ("menu-item-label", "The text of each item row."),
            ("menu-item-shortcut", "The shortcut hint at the end of a row."),
            ("menu-separator", "A divider row."),
            ("menu-group", "A `role=\"group\"` wrapper for a `<mj-menu-group>`."),
            ("menu-group-label", "The heading of a group."),
        ],
        css_properties=[
            ("--mj-menu-button-trigger-size", "Minimum height and width of the trigger at the default size (default var(--mj-control-height-md))."),
            ("--mj-menu-border-radius", "Corner radius of the popup (default var(--mj-radius-md))."),
            ("--mj-menu-popup-min-width", "Minimum width of the popup (default 10rem)."),
            ("--mj-menu-popup-max-height", "Maximum height of the popup before it scrolls (default 24rem)."),
            ("--mj-menu-item-height", "Minimum height of an item row (default var(--mj-control-height-md))."),
            ("--mj-menu-item-padding", "Padding of an item row (default var(--mj-space-2) var(--mj-space-3))."),
            ("--mj-menu-separator-color", "Colour of separators (default var(--mj-border))."),
        ],
    ),
    ComponentDoc(
        tag="mj-color-picker",
        title="Color Picker",
        group="selection",
        summary=(
            "Colour chooser with a saturation/brightness canvas, hue and opacity sliders, a text field, "
            "an optional eyedropper and a swatch palette; popup or inline, form-associated."
        ),
        description=(
            "<p><code>&lt;mj-color-picker&gt;</code> shows a swatch button that opens a floating "
            "dialog (or, with <code>inline</code>, the same surface directly in the page). The dialog "
            "holds an HSV canvas (x = saturation, y = brightness, drawn for the current hue), a hue "
            "slider, an opacity slider, a text field that accepts any CSS colour (hex with or without "
            "<code>#</code>, <code>rgb()</code>, <code>hsl()</code>, colour names), an eyedropper "
            "button where the browser has the EyeDropper API, and a palette built from the "
            "<code>swatches</code> attribute. The colour is held as HSV plus alpha, so a value does not "
            "drift through a round trip.</p>"
            "<p>The value is written in the notation chosen by <code>format</code>: <code>hex</code> "
            "(<code>#rrggbb</code>, or <code>#rrggbbaa</code> when translucent), <code>rgb</code> "
            "(<code>rgb()</code> / <code>rgba()</code>) or <code>hsl</code> (<code>hsl()</code> / "
            "<code>hsla()</code>). <code>no-alpha</code> hides the opacity slider and forces full "
            "opacity. <code>swatches-only</code> reduces the dialog to the palette.</p>"
            "<p>A colour picker always has a value (like <code>&lt;input type=\"color\"&gt;</code>), "
            "so <code>required</code> does not apply to it.</p>"
            "<p>The <code>value</code> attribute is the <em>initial</em> colour, the one a form reset "
            "restores. Picking a colour changes the <code>value</code> property and the submitted form "
            "value and is never written back to the attribute. Dragging on the canvas or a slider fires "
            "<code>mj-input</code> on every step and <code>mj-change</code> when the drag ends; keyboard "
            "steps, swatch clicks, text entry and the eyedropper fire <code>mj-change</code> only.</p>"
            "<p>Keyboard: the trigger opens the dialog with Enter or Space; Tab stays inside the open "
            "dialog; on the canvas thumb the arrow keys change saturation (left / right) and brightness "
            "(up / down) by 1, or by 10 with Shift; the sliders use the native range keys; Escape "
            "closes and restores the colour the dialog opened with. A click outside closes it and keeps "
            "the colour.</p>"
        ),
        how_to_use=(
            "<p>Set <code>value</code> to the initial colour and give the control a <code>name</code> "
            "inside a form. Add <code>swatches</code> as a JSON array of colour strings for a palette "
            "(entries that are not colours are skipped). Choose the output notation with "
            "<code>format</code>, hide opacity with <code>no-alpha</code>, add <code>eyedropper</code> "
            "for a screen picker, or use <code>inline</code> to embed the surface without a trigger. "
            "Read the live colour from <code>.value</code> (or <code>hexValue</code>, "
            "<code>rgbValue</code>, <code>hslValue</code>, <code>color</code>) and listen for "
            "<code>mj-change</code> to react to a settled choice, <code>mj-input</code> for live "
            "dragging.</p>"
        ),
        example="",
        attributes=[
            AttributeDoc(name="value", description="Initial colour (any CSS colour); form reset restores it. User picks do not rewrite it. Unparseable text falls back to `#000000`.",
                         kind="color", default="#000000"),
            AttributeDoc(name="format", description="Notation of `value`, the form value and the text field.",
                         kind="enum", values=["hex", "rgb", "hsl"], default="hex"),
            AttributeDoc(name="swatches", description="JSON array of colour strings shown as a palette; invalid entries are skipped.",
                         kind="json"),
            AttributeDoc(name="no-alpha", description="Hides the opacity slider and keeps the colour fully opaque.",
                         kind="boolean"),
            AttributeDoc(name="swatches-only", description="Shows only the swatch palette in the dialog (no canvas, sliders or text field).",
                         kind="boolean"),
            AttributeDoc(name="eyedropper", description="Shows a Pick button that samples a colour from the screen (only where the browser has the EyeDropper API).",
                         kind="boolean"),
            AttributeDoc(name="inline", description="Renders the picker surface in the page, without a trigger or popup; `open` is ignored.",
                         kind="boolean"),
            AttributeDoc(name="open", description="Shows the popup. Setting it directly skips the cancelable `mj-open` event; the component removes it when it closes.",
                         kind="boolean"),
            AttributeDoc(name="disabled", description="Disables the trigger and blocks every edit; closes an open popup. An ancestor `<fieldset disabled>` does the same.",
                         kind="boolean"),
            AttributeDoc(name="readonly", description="The colour is shown and still submitted, but the popup does not open (an open one closes) and no edit is applied; the trigger stays focusable and is marked `aria-disabled`.",
                         kind="boolean"),
            AttributeDoc(name="invalid", description="Danger border on the trigger.", kind="boolean"),
            AttributeDoc(name="name", description="Form field name the formatted value is submitted under.",
                         kind="string", values=["accent"]),
        ],
        events=[
            ("mj-input", "Live update while the canvas, hue or opacity slider is dragged.",
             "{ value: string, color: { h: number, s: number, l: number, a: number } }"),
            ("mj-change", "The user settled on a colour: drag end, keyboard step, swatch, text entry, eyedropper, or Escape restoring the opening colour. Not fired for `value` assignments.",
             "{ value: string, color: { h: number, s: number, l: number, a: number } }"),
            ("change", "Plain `Event` (no detail) fired right after every `mj-change`, for native-style listeners.", ""),
            ("input", "Plain `Event` (no detail) fired right after every `mj-input`.", ""),
            ("mj-open", "Cancelable; fired before the popup opens from the trigger or `open = true`. `preventDefault()` keeps it closed.",
             "{}"),
            ("mj-close", "The popup closed (swatch pick, Escape, outside click, trigger, `open = false`).", "{}"),
        ],
        examples=[
            ComponentExample(
                key="basic",
                title="Basic usage",
                description=(
                    "<p>A popup picker with a palette and the opacity slider. Click the swatch, drag on "
                    "the canvas or a slider, or pick a swatch; the readout follows <code>mj-input</code> "
                    "and <code>mj-change</code>, which also appear in Events.</p>"
                ),
                html=(
                    '<div class="row">\n'
                    '  <mj-color-picker id="brand" value="#3b82f6"\n'
                    '    swatches=\'["#ef4444","#f97316","#eab308","#22c55e","#14b8a6","#3b82f6","#8b5cf6","#ec4899"]\'>\n'
                    '  </mj-color-picker>\n'
                    '  <span>Brand colour: <output id="brand-value">#3b82f6</output></span>\n'
                    '</div>'
                ),
                css=(
                    "body { padding: var(--mj-space-4); }\n"
                    ".row { display: flex; align-items: center; gap: var(--mj-space-3); }\n"
                    "output { font-family: var(--mj-font-mono); }\n"
                ),
                script=(
                    'const picker = document.getElementById("brand")\n'
                    'const readout = document.getElementById("brand-value")\n'
                    'const show = () => { readout.textContent = picker.value }\n'
                    'picker.addEventListener("mj-input", show)\n'
                    'picker.addEventListener("mj-change", show)\n'
                ),
                height=420,
            ),
            ComponentExample(
                key="inline",
                title="Inline, formats and properties",
                description=(
                    "<p>An <code>inline</code> picker with <code>format=\"hsl\"</code>, a translucent "
                    "initial value and the <code>eyedropper</code> button (shown only where the browser "
                    "supports it). The table shows <code>value</code>, <code>hexValue</code>, "
                    "<code>rgbValue</code>, <code>hslValue</code> and <code>color</code>; switch "
                    "<code>format</code> in Controls and drag again to see the notation change.</p>"
                ),
                html=(
                    '<div class="layout">\n'
                    '  <mj-color-picker id="inline-picker" inline format="hsl" eyedropper value="#0ea5e9cc"></mj-color-picker>\n'
                    '  <table>\n'
                    '    <tr><th>value</th><td id="out-value"></td></tr>\n'
                    '    <tr><th>hexValue</th><td id="out-hex"></td></tr>\n'
                    '    <tr><th>rgbValue</th><td id="out-rgb"></td></tr>\n'
                    '    <tr><th>hslValue</th><td id="out-hsl"></td></tr>\n'
                    '    <tr><th>color</th><td id="out-color"></td></tr>\n'
                    '  </table>\n'
                    '</div>'
                ),
                css=(
                    "body { padding: var(--mj-space-4); }\n"
                    ".layout { display: flex; flex-wrap: wrap; gap: var(--mj-space-4); align-items: flex-start; }\n"
                    "#inline-picker { inline-size: 16rem; }\n"
                    "th { text-align: start; padding-inline-end: var(--mj-space-3); color: var(--mj-text-muted); font-weight: normal; }\n"
                    "td { font-family: var(--mj-font-mono); font-size: var(--mj-font-size-sm); }\n"
                ),
                script=(
                    'const picker = document.getElementById("inline-picker")\n'
                    'const set = (id, text) => { document.getElementById(id).textContent = text }\n'
                    'const show = () => {\n'
                    '  set("out-value", picker.value)\n'
                    '  set("out-hex", picker.hexValue)\n'
                    '  set("out-rgb", picker.rgbValue)\n'
                    '  set("out-hsl", picker.hslValue)\n'
                    '  set("out-color", JSON.stringify(picker.color))\n'
                    '}\n'
                    'picker.addEventListener("mj-input", show)\n'
                    'picker.addEventListener("mj-change", show)\n'
                    'new MutationObserver(show).observe(picker, { attributes: true })\n'
                    'show()\n'
                ),
            ),
            ComponentExample(
                key="swatches-only",
                title="Swatch palette only",
                description=(
                    "<p><code>swatches-only</code> with <code>no-alpha</code>: the dialog (open on load) "
                    "is just the palette. The swatch matching the value is pressed; picking one fires "
                    "<code>mj-change</code> and closes the popup.</p>"
                ),
                html=(
                    '<div class="row">\n'
                    '  <mj-color-picker id="label-colour" swatches-only no-alpha open value="#22c55e"\n'
                    '    swatches=\'["#64748b","#ef4444","#f97316","#f59e0b","#84cc16","#22c55e","#14b8a6","#06b6d4","#3b82f6","#6366f1","#a855f7","#ec4899"]\'>\n'
                    '  </mj-color-picker>\n'
                    '  <span>Label colour</span>\n'
                    '</div>'
                ),
                css=(
                    "body { padding: var(--mj-space-4); }\n"
                    ".row { display: flex; align-items: center; gap: var(--mj-space-3); }\n"
                    "#label-colour { --mj-color-picker-popup-width: 11rem; --mj-color-picker-swatch-size: 2rem; }\n"
                ),
                height=260,
            ),
            ComponentExample(
                key="states",
                title="States",
                description=(
                    "<p><code>disabled</code> (trigger disabled), inside a <code>&lt;fieldset "
                    "disabled&gt;</code> (the same), <code>readonly</code> (shows the colour, "
                    "does not open), <code>invalid</code> (danger border) and <code>no-alpha</code> (no "
                    "opacity slider; a translucent value becomes opaque).</p>"
                ),
                html=(
                    '<div class="grid">\n'
                    '  <mj-color-picker value="#8b5cf6" disabled></mj-color-picker><span>disabled</span>\n'
                    '  <fieldset disabled><mj-color-picker value="#0ea5e9"></mj-color-picker></fieldset><span>in a disabled fieldset</span>\n'
                    '  <mj-color-picker value="#f97316" readonly></mj-color-picker><span>readonly</span>\n'
                    '  <mj-color-picker value="#ef4444" invalid></mj-color-picker><span>invalid</span>\n'
                    '  <mj-color-picker value="#14b8a680" no-alpha></mj-color-picker><span>no-alpha (value #14b8a680)</span>\n'
                    '</div>'
                ),
                css=(
                    "body { padding: var(--mj-space-4); }\n"
                    ".grid { display: grid; grid-template-columns: auto 1fr; gap: var(--mj-space-3); align-items: center; }\n"
                    "fieldset { border: 0; padding: 0; margin: 0; }\n"
                ),
                height=420,
            ),
            ComponentExample(
                key="form",
                title="Form participation",
                description=(
                    "<p>Two named pickers in a form, one with <code>format=\"rgb\"</code>. Save shows the "
                    "submitted <code>FormData</code>; Reset restores each <code>value</code> attribute "
                    "(the attribute never changes when you pick).</p>"
                ),
                html=(
                    '<form id="theme-form">\n'
                    '  <div class="row"><mj-color-picker name="accent" value="#16a34a"></mj-color-picker><span>Accent</span></div>\n'
                    '  <div class="row"><mj-color-picker name="highlight" format="rgb" value="rgb(250 204 21 / 0.6)"></mj-color-picker><span>Highlight</span></div>\n'
                    '  <div class="actions">\n'
                    '    <button type="submit">Save</button>\n'
                    '    <button type="reset">Reset</button>\n'
                    '  </div>\n'
                    '  <pre id="theme-output"></pre>\n'
                    '</form>'
                ),
                css=(
                    "body { padding: var(--mj-space-4); }\n"
                    ".row { display: flex; align-items: center; gap: var(--mj-space-3); margin-block-end: var(--mj-space-3); }\n"
                    ".actions { display: flex; gap: var(--mj-space-2); }\n"
                    "pre { font-family: var(--mj-font-mono); font-size: var(--mj-font-size-sm); }\n"
                ),
                script=(
                    'const form = document.getElementById("theme-form")\n'
                    'const output = document.getElementById("theme-output")\n'
                    'const show = (label) => {\n'
                    '  const data = Object.fromEntries(new FormData(form))\n'
                    '  output.textContent = label + ": " + JSON.stringify(data, null, 2)\n'
                    '  mjSandbox.log(label, data)\n'
                    '}\n'
                    'form.addEventListener("submit", (event) => {\n'
                    '  event.preventDefault()\n'
                    '  show("submitted")\n'
                    '})\n'
                    'form.addEventListener("reset", () => setTimeout(() => show("after reset"), 0))\n'
                    'show("initial")\n'
                ),
                height=440,
            ),
            ComponentExample(
                key="events",
                title="Events and properties",
                description=(
                    "<p>The script opens the picker with <code>open = true</code> "
                    "(<code>mj-open</code>), drags the hue slider (<code>mj-input</code>, then "
                    "<code>mj-change</code>), steps the canvas thumb with Shift+ArrowLeft "
                    "(<code>mj-change</code>) and clicks a swatch (<code>mj-change</code>, "
                    "<code>mj-close</code>). The log notes show <code>value</code> after each step.</p>"
                ),
                html=(
                    '<mj-color-picker id="events-picker" value="#3b82f6"\n'
                    '  swatches=\'["#ef4444","#22c55e","#3b82f6"]\'></mj-color-picker>'
                ),
                css="body { padding: var(--mj-space-4); }",
                script=(
                    'const picker = document.getElementById("events-picker")\n'
                    'const root = picker.shadowRoot\n'
                    'picker.open = true\n'
                    'const hue = root.querySelector("[part=hue-slider]")\n'
                    'hue.value = "200"\n'
                    'hue.dispatchEvent(new Event("input"))\n'
                    'hue.dispatchEvent(new Event("change"))\n'
                    'mjSandbox.log("after hue drag", { value: picker.value })\n'
                    'root.querySelector("[part=canvas-thumb]").dispatchEvent(\n'
                    '  new KeyboardEvent("keydown", { key: "ArrowLeft", shiftKey: true, bubbles: true }))\n'
                    'mjSandbox.log("after canvas key", { value: picker.value, color: picker.color })\n'
                    'root.querySelector("[part=swatch]").click()\n'
                    'mjSandbox.log("after swatch", { value: picker.value, open: picker.open })\n'
                ),
                height=420,
            ),
        ],
        properties=[
            ("value", "string. The current colour in the `format` notation; setting it applies a colour (invalid text gives `#000000`) without emitting events or changing the attribute."),
            ("hexValue", "string (read-only). `#rrggbb`, or `#rrggbbaa` when translucent."),
            ("rgbValue", "string (read-only). `rgb(r, g, b)` or `rgba(r, g, b, a)`."),
            ("hslValue", "string (read-only). `hsl(h, s%, l%)` or `hsla(h, s%, l%, a)`."),
            ("color", "object (read-only). `{ h, s, l, a }`: hue 0-360, saturation and lightness 0-100, alpha 0-1."),
            ("swatchList", "string[] (read-only). The strings parsed from the `swatches` attribute."),
            ("open", "boolean. Reflects `open`; setting `true` opens like the trigger (fires cancelable `mj-open`, ignored when disabled, readonly or inline), `false` closes."),
            ("form", "HTMLFormElement | null (read-only). The owning form."),
            ("validity", "ValidityState (read-only). Constraint-validation state."),
            ("validationMessage", "string (read-only). The current validation message."),
        ],
        methods=[
            ("focus(options?)", "Focuses the trigger, or the canvas thumb when `inline`."),
            ("checkValidity() -> boolean", "Runs constraint validation."),
            ("reportValidity() -> boolean", "Runs constraint validation and reports a failure to the user."),
        ],
        parts=[
            ("trigger", "The swatch button that opens the popup."),
            ("trigger-swatch", "The colour chip inside the trigger."),
            ("popup", "The dialog panel (also the inline surface)."),
            ("canvas", "The saturation/brightness area (wrapper of the canvas and thumb)."),
            ("canvas-bg", "The drawn HSV canvas."),
            ("canvas-thumb", "The draggable, focusable thumb on the canvas (role slider)."),
            ("preview", "The current-colour chip beside the hue slider."),
            ("hue-slider", "The hue range input."),
            ("alpha-slider", "The opacity range input."),
            ("format-inputs", "The colour text field."),
            ("eyedropper", "The Pick (EyeDropper) button."),
            ("swatch-grid", "The palette container."),
            ("swatch", "Each palette button (`aria-pressed` marks the current colour)."),
        ],
        css_properties=[
            ("--mj-color-picker-popup-width", "Width of the popup / inline surface (default 16rem)."),
            ("--mj-color-picker-border-radius", "Popup corner radius (default var(--mj-radius-md))."),
            ("--mj-color-picker-canvas-height", "Height of the saturation/brightness canvas (default 10rem)."),
            ("--mj-color-picker-thumb-size", "Size of the canvas and slider thumbs (default 1rem)."),
            ("--mj-color-picker-slider-height", "Height of the hue and opacity tracks (default 0.75rem)."),
            ("--mj-color-picker-swatch-size", "Size of each palette swatch (default 1.5rem)."),
            ("--mj-color-picker-swatch-gap", "Gap between swatches (default var(--mj-space-1))."),
        ],
    ),
    ComponentDoc(
        tag="mj-date-picker",
        title="Date Picker",
        group="selection",
        summary=(
            "Date, date-time, time or date-range field with typed entry, a keyboard-navigable calendar "
            "dialog, locale-aware display and form participation."
        ),
        description=(
            "<p><code>&lt;mj-date-picker&gt;</code> is a text field (a combobox) with a calendar "
            "button. The calendar dialog has year and month navigation, a day grid and, for the time "
            "modes, hour and minute fields with a Done button. Values are ISO 8601 strings that always "
            "denote <em>local</em> days and wall-clock times (never UTC):</p>"
            "<ul>"
            "<li><code>mode=\"date\"</code> (default): <code>YYYY-MM-DD</code></li>"
            "<li><code>mode=\"datetime\"</code>: <code>YYYY-MM-DDTHH:mm</code>; clicking a day keeps "
            "the dialog open so the time can be set; Done closes it.</li>"
            "<li><code>mode=\"time\"</code>: <code>HH:mm</code>; the dialog shows only the time fields.</li>"
            "<li><code>mode=\"range\"</code>: <code>YYYY-MM-DD/YYYY-MM-DD</code>; the first click "
            "picks one end, hovering previews the range, the second click commits it (in either "
            "order).</li>"
            "</ul>"
            "<p>The field shows the value formatted for <code>locale</code> (default: the browser's). "
            "The user can also type a date: ISO, the locale's numeric order (<code>03/15/2026</code> in "
            "en-US, <code>15.03.2026</code> in de-DE) or with a month name (<code>Mar 15, 2026</code>); "
            "a range as two dates separated by \" - \" or \" to \"; a time as <code>14:30</code> or "
            "<code>2:30 pm</code>. Text is parsed on Enter, ArrowDown or blur; text that is not a date "
            "(or is outside <code>min</code>/<code>max</code>) marks the field invalid and blocks form "
            "submission until corrected. The week starts on <code>first-day-of-week</code> or the "
            "locale's convention.</p>"
            "<p>The <code>value</code> attribute is the <em>initial</em> value, restored by a form "
            "reset; choices update the <code>value</code> property and the form value, not the "
            "attribute.</p>"
            "<p>Keyboard: in the field, ArrowDown opens the calendar and moves focus to the selected "
            "day (or today), Enter commits typed text and closes, Escape cancels. In the grid, arrows "
            "move by day / week, Home / End to the start / end of the week, PageUp / PageDown by month, "
            "Shift+PageUp / Shift+PageDown by year, Enter or Space picks the day, Tab cycles inside the "
            "dialog, Escape closes and restores the value the dialog opened with. Clicking the field "
            "opens the calendar but leaves focus in the field for typing.</p>"
        ),
        how_to_use=(
            "<p>Choose a <code>mode</code>, give an initial <code>value</code> in that mode's ISO "
            "format and, in a form, a <code>name</code> (add <code>required</code> to demand a value). "
            "Limit the selectable days with <code>min</code> / <code>max</code> "
            "(<code>YYYY-MM-DD</code>), add <code>clearable</code> for a clear button, set "
            "<code>locale</code> and <code>first-day-of-week</code> for display, and "
            "<code>block</code> to fill the row. Read <code>.value</code> (or "
            "<code>valueAsDate</code>, <code>startDate</code> / <code>endDate</code> for ranges) and "
            "listen for <code>mj-change</code>. Name the field with <code>label</code>, "
            "<code>aria-label</code>, <code>aria-labelledby</code> or an associated "
            "<code>&lt;label for&gt;</code>; the name is copied onto the inner text field.</p>"
        ),
        example="",
        attributes=[
            AttributeDoc(name="value", description="Initial value in the mode's ISO format; form reset restores it. Invalid text clears the picker.",
                         kind="string", values=["2026-03-15", "2026-03-15T14:30", "09:45", "2026-03-09/2026-03-13"]),
            AttributeDoc(name="mode", description="What is picked; changing it re-reads the value in the new format.",
                         kind="enum", values=["date", "datetime", "time", "range"], default="date"),
            AttributeDoc(name="min", description="Earliest selectable day (`YYYY-MM-DD`); earlier days are disabled and typed dates before it are rejected.",
                         kind="string", values=["2026-03-02"]),
            AttributeDoc(name="max", description="Latest selectable day (`YYYY-MM-DD`).",
                         kind="string", values=["2026-03-31"]),
            AttributeDoc(name="placeholder", description="Field placeholder (default `Select date`, or `Select time` in time mode).",
                         kind="string", values=["Select a date"]),
            AttributeDoc(name="locale", description="BCP 47 locale for the displayed text, month and weekday names, typed-date order and default week start.",
                         kind="string", values=["en-US", "en-GB", "de-DE", "fr-FR", "ja-JP"]),
            AttributeDoc(name="first-day-of-week", description="First grid column: 0 = Sunday ... 6 = Saturday. Absent: the locale's convention.",
                         kind="enum", values=["0", "1", "2", "3", "4", "5", "6"]),
            AttributeDoc(name="clearable", description="Shows a clear button while there is a value (not when disabled or readonly).",
                         kind="boolean"),
            AttributeDoc(name="open", description="Shows the calendar dialog. Setting it directly skips the cancelable `mj-open` event; the component removes it when it closes.",
                         kind="boolean"),
            AttributeDoc(name="label", description="Accessible name of the text field; wins over `aria-label`, `aria-labelledby` and a `<label>`.",
                         kind="string", values=["Due date"]),
            AttributeDoc(name="aria-label", description="Accessible name when `label` is absent.", kind="string"),
            AttributeDoc(name="aria-labelledby", description="Ids of elements whose text names the field (when `label` and `aria-label` are absent).",
                         kind="string"),
            AttributeDoc(name="disabled", description="Disables the field and buttons; closes an open dialog. An ancestor `<fieldset disabled>` does the same.",
                         kind="boolean"),
            AttributeDoc(name="readonly", description="The field cannot be edited, the calendar does not open and the clear button is hidden.",
                         kind="boolean"),
            AttributeDoc(name="required", description="Invalid (valueMissing) while the value is empty; sets `aria-required` on the field.", kind="boolean"),
            AttributeDoc(name="required-message", description="Validation message used instead of the default when `required` fails.",
                         kind="string", values=["Choose a check-in date."]),
            AttributeDoc(name="invalid", description="Forces the danger border.", kind="boolean"),
            AttributeDoc(name="block", description="Display as a block that fills the inline size of its container.",
                         kind="boolean"),
            AttributeDoc(name="name", description="Form field name the ISO value is submitted under.",
                         kind="string", values=["due"]),
        ],
        events=[
            ("mj-change", "The user changed the value (day click, range completed, time fields, Done, typed text, clear, Escape restoring). Not fired for `value` assignments. `date` is null in time and range modes; `startDate` / `endDate` only in range mode.",
             "{ value: string, date: Date | null, startDate: Date | null, endDate: Date | null }"),
            ("mj-input", "Every edit of the text field, before it is parsed.", "{ inputValue: string }"),
            ("mj-month-change", "The calendar page changed (header buttons, PageUp/PageDown, arrows across a month edge).",
             "{ month: number (1-12), year: number }"),
            ("change", "Plain `Event` (no detail) fired right after every `mj-change`, for native-style listeners.", ""),
            ("input", "Plain `Event` (no detail) fired right after every `mj-input`.", ""),
            ("mj-open", "Cancelable; fired before the dialog opens (field click, button, ArrowDown, `open = true`). `preventDefault()` keeps it closed.",
             "{}"),
            ("mj-close", "The dialog closed (pick, Done, Escape, Enter, outside click, focus leaving, button, `open = false`).", "{}"),
        ],
        examples=[
            ComponentExample(
                key="basic",
                title="Basic usage",
                description=(
                    "<p>A clearable date field (<code>locale=\"en-US\"</code>) named by a "
                    "<code>&lt;label for&gt;</code>. Click the field or the "
                    "calendar button and pick a day, or type <code>03/15/2026</code> and press Enter; "
                    "the readout shows <code>.value</code> after each <code>mj-change</code>.</p>"
                ),
                html=(
                    '<div class="field">\n'
                    '  <label class="caption" for="due">Due date</label>\n'
                    '  <mj-date-picker id="due" placeholder="Select a date" clearable locale="en-US"></mj-date-picker>\n'
                    '</div>\n'
                    '<p>value: <output id="due-value">(empty)</output></p>'
                ),
                css=(
                    "body { padding: var(--mj-space-4); }\n"
                    ".field { display: flex; flex-direction: column; gap: var(--mj-space-1); inline-size: 16rem; }\n"
                    ".caption { font-size: var(--mj-font-size-sm); color: var(--mj-text-muted); }\n"
                    "output { font-family: var(--mj-font-mono); }\n"
                ),
                script=(
                    'const picker = document.getElementById("due")\n'
                    'picker.addEventListener("mj-change", () => {\n'
                    '  document.getElementById("due-value").textContent = picker.value || "(empty)"\n'
                    '})\n'
                ),
                height=460,
            ),
            ComponentExample(
                key="range",
                title="Date range with min / max",
                description=(
                    "<p><code>mode=\"range\"</code> with a preset range and <code>min</code> / "
                    "<code>max</code> limiting the choice to March 2026 (other days are disabled). The "
                    "calendar is open on load: click a start day, hover to preview, click the end day.</p>"
                ),
                html=(
                    '<mj-date-picker id="stay" mode="range" value="2026-03-09/2026-03-13"\n'
                    '  min="2026-03-02" max="2026-03-31" locale="en-GB" clearable open></mj-date-picker>'
                ),
                css=(
                    "body { padding: var(--mj-space-4); }\n"
                    "#stay { inline-size: 22rem; }\n"
                ),
                height=460,
            ),
            ComponentExample(
                key="modes",
                title="Date-time and time modes",
                description=(
                    "<p><code>mode=\"datetime\"</code>: clicking a day keeps the dialog open; set hour and "
                    "minute and press Done. <code>mode=\"time\"</code>: the dialog shows only the time "
                    "fields; you can also type <code>2:30 pm</code> in the field.</p>"
                ),
                html=(
                    '<div class="grid">\n'
                    '  <span class="caption">Meeting starts</span>\n'
                    '  <mj-date-picker mode="datetime" value="2026-03-15T14:30" locale="en-US" clearable></mj-date-picker>\n'
                    '  <span class="caption">Daily reminder</span>\n'
                    '  <mj-date-picker mode="time" value="09:45" locale="en-US"></mj-date-picker>\n'
                    '</div>'
                ),
                css=(
                    "body { padding: var(--mj-space-4); }\n"
                    ".grid { display: grid; grid-template-columns: auto 18rem; gap: var(--mj-space-3); align-items: center; }\n"
                    ".caption { color: var(--mj-text-muted); }\n"
                ),
                height=520,
            ),
            ComponentExample(
                key="locale",
                title="Locale and week start",
                description=(
                    "<p><code>locale=\"de-DE\"</code> (open on load): German month and weekday names, "
                    "weeks starting on Monday; type <code>24.12.2026</code> or <code>24. Dezember "
                    "2026</code>. The second field is en-US with <code>first-day-of-week=\"1\"</code>.</p>"
                ),
                html=(
                    '<div class="grid">\n'
                    '  <mj-date-picker id="de-picker" locale="de-DE" value="2026-12-24" open></mj-date-picker>\n'
                    '  <mj-date-picker locale="en-US" first-day-of-week="1" value="2026-12-24"></mj-date-picker>\n'
                    '</div>'
                ),
                css=(
                    "body { padding: var(--mj-space-4); }\n"
                    ".grid { display: flex; flex-wrap: wrap; gap: var(--mj-space-4); align-items: flex-start; }\n"
                ),
                height=440,
            ),
            ComponentExample(
                key="form",
                title="Form and states",
                description=(
                    "<p>A <code>required</code> block picker with a custom <code>required-message</code>, "
                    "a <code>readonly</code> one, a <code>disabled</code> one and one inside a "
                    "<code>&lt;fieldset disabled&gt;</code> (neither is submitted nor opens), and one with "
                    "<code>invalid</code> styling. Book shows the submitted <code>FormData</code> (or the "
                    "validation message); Reset restores the <code>value</code> attributes.</p>"
                ),
                html=(
                    '<form id="booking">\n'
                    '  <span class="caption">Check-in (required)</span>\n'
                    '  <mj-date-picker name="checkin" required required-message="Choose a check-in date." block clearable locale="en-US"></mj-date-picker>\n'
                    '  <span class="caption">Booked on (readonly)</span>\n'
                    '  <mj-date-picker name="booked" value="2026-02-01" readonly clearable locale="en-US"></mj-date-picker>\n'
                    '  <span class="caption">Departure (disabled)</span>\n'
                    '  <mj-date-picker name="departure" value="2026-03-20" disabled locale="en-US"></mj-date-picker>\n'
                    '  <fieldset disabled>\n'
                    '    <legend class="caption">Transfer (fieldset disabled)</legend>\n'
                    '    <mj-date-picker name="transfer" value="2026-03-21" locale="en-US" label="Transfer date"></mj-date-picker>\n'
                    '  </fieldset>\n'
                    '  <span class="caption">Return (invalid)</span>\n'
                    '  <mj-date-picker name="return" value="2026-03-01" invalid locale="en-US"></mj-date-picker>\n'
                    '  <div class="actions">\n'
                    '    <button type="submit">Book</button>\n'
                    '    <button type="reset">Reset</button>\n'
                    '  </div>\n'
                    '  <pre id="booking-output"></pre>\n'
                    '</form>'
                ),
                css=(
                    "body { padding: var(--mj-space-4); }\n"
                    "#booking { display: flex; flex-direction: column; gap: var(--mj-space-2); max-inline-size: 22rem; }\n"
                    "fieldset { display: flex; flex-direction: column; gap: var(--mj-space-1); border: 0; padding: 0; margin: 0; }\n"
                    ".caption { font-size: var(--mj-font-size-sm); color: var(--mj-text-muted); margin-block-start: var(--mj-space-2); }\n"
                    ".actions { display: flex; gap: var(--mj-space-2); margin-block-start: var(--mj-space-3); }\n"
                    "pre { font-family: var(--mj-font-mono); font-size: var(--mj-font-size-sm); white-space: pre-wrap; }\n"
                ),
                script=(
                    'const form = document.getElementById("booking")\n'
                    'const output = document.getElementById("booking-output")\n'
                    'const checkin = form.querySelector("[name=checkin]")\n'
                    'form.addEventListener("submit", (event) => {\n'
                    '  event.preventDefault()\n'
                    '  const data = Object.fromEntries(new FormData(form))\n'
                    '  output.textContent = "submitted: " + JSON.stringify(data, null, 2)\n'
                    '  mjSandbox.log("submitted", data)\n'
                    '})\n'
                    'checkin.addEventListener("invalid", () => {\n'
                    '  output.textContent = "blocked: " + checkin.validationMessage\n'
                    '  mjSandbox.log("invalid", { message: checkin.validationMessage })\n'
                    '})\n'
                    'form.addEventListener("reset", () => setTimeout(() => {\n'
                    '  output.textContent = "after reset: " + JSON.stringify(Object.fromEntries(new FormData(form)))\n'
                    '}, 0))\n'
                ),
                height=620,
            ),
            ComponentExample(
                key="events",
                title="Events and properties",
                description=(
                    "<p>The script opens the picker with <code>open = true</code> "
                    "(<code>mj-open</code>), clicks the next-month button (<code>mj-month-change</code>) "
                    "and clicks 15 April (<code>mj-change</code>, then <code>mj-close</code>). The log "
                    "notes show <code>value</code>, <code>valueAsDate</code> and "
                    "<code>displayMonth</code>.</p>"
                ),
                html=(
                    '<mj-date-picker id="events-picker" value="2026-03-10" locale="en-US" clearable></mj-date-picker>'
                ),
                css="body { padding: var(--mj-space-4); }\n#events-picker { inline-size: 16rem; }\n",
                script=(
                    'const picker = document.getElementById("events-picker")\n'
                    'const root = picker.shadowRoot\n'
                    'picker.open = true\n'
                    'root.querySelector("[part=next]").click()\n'
                    'mjSandbox.log("calendar page", { displayMonth: picker.displayMonth.toDateString() })\n'
                    'root.querySelector(".day-btn[data-date=\'2026-04-15\']").click()\n'
                    'mjSandbox.log("picked", {\n'
                    '  value: picker.value,\n'
                    '  valueAsDate: picker.valueAsDate.toDateString(),\n'
                    '  attribute: picker.getAttribute("value"),\n'
                    '  open: picker.open\n'
                    '})\n'
                ),
                height=460,
            ),
        ],
        properties=[
            ("value", "string. The current ISO value for the mode (empty when none); setting it applies the value (invalid text clears) without emitting events or changing the attribute."),
            ("valueAsDate", "Date | null (read-only). The selected local day (with the time in datetime mode); null in time and range modes."),
            ("startDate", "Date | null (read-only). Range mode: the start day (also while only one end is chosen)."),
            ("endDate", "Date | null (read-only). Range mode: the end day."),
            ("displayMonth", "Date (read-only). The first day of the month the calendar shows."),
            ("open", "boolean. Reflects `open`; setting `true` opens like a field click (fires cancelable `mj-open`, ignored when disabled or readonly), `false` closes."),
            ("form", "HTMLFormElement | null (read-only). The owning form."),
            ("validity", "ValidityState (read-only). valueMissing for an empty required picker, customError while the typed text is not a valid date."),
            ("validationMessage", "string (read-only). The current validation message."),
        ],
        methods=[
            ("focus(options?)", "Focuses the text field."),
            ("checkValidity() -> boolean", "Runs constraint validation."),
            ("reportValidity() -> boolean", "Runs constraint validation and reports a failure to the user."),
        ],
        parts=[
            ("field", "The bordered row holding the input and buttons."),
            ("input", "The text field (role combobox)."),
            ("clear", "The clear button (with `clearable`)."),
            ("calendar-trigger", "The button that opens the dialog."),
            ("popup", "The dialog panel."),
            ("calendar-header", "The navigation row."),
            ("prev-year", "Previous-year button."),
            ("prev", "Previous-month button."),
            ("month-year", "The month and year heading."),
            ("next", "Next-month button."),
            ("next-year", "Next-year button."),
            ("day-grid", "The calendar grid (role grid)."),
            ("week-header", "Each weekday column header."),
            ("week-row", "Each row of days."),
            ("day-cell", "Each gridcell holding a day button."),
            ("time-panel", "The hour / minute fields and Done button (datetime and time modes)."),
        ],
        css_properties=[
            ("--mj-date-picker-popup-width", "Dialog width (default 20rem; time mode sizes to content)."),
            ("--mj-date-picker-cell-size", "Size of each day button (default 2.25rem)."),
            ("--mj-date-picker-selected-color", "Background of the selected day and range ends (default var(--mj-accent))."),
            ("--mj-date-picker-range-fill-color", "Background of the days inside a range (default var(--mj-bg-muted))."),
            ("--mj-date-picker-disabled-opacity", "Opacity of days outside min / max (default 0.4)."),
        ],
    ),
    ComponentDoc(
        tag="mj-file-picker",
        title="File Picker",
        group="selection",
        summary=(
            "Drop zone and choose button for files, with type / size / count validation, image previews, "
            "optional upload with progress and retry, and form submission of the File objects."
        ),
        description=(
            "<p><code>&lt;mj-file-picker&gt;</code> wraps a hidden native file input in a drop zone "
            "with a choose button (or, with <code>variant=\"button\"</code>, just the button). The drop "
            "zone itself is focusable: Enter or Space, or a click anywhere on it, opens the browser's "
            "file chooser. Chosen or dropped files are listed with a thumbnail (images) or file icon, "
            "name, size and a remove button.</p>"
            "<p>Each file is checked against <code>accept</code> (extensions, <code>type/*</code> or "
            "exact MIME types), <code>max-size</code> (bytes) and <code>max-files</code>. Rejected "
            "files fire <code>mj-file-error</code> and every message of the selection is shown under "
            "the list until the next selection. Files that pass fire the cancelable "
            "<code>mj-file-add</code>. Without <code>multiple</code> only the first valid file is kept "
            "and it replaces the current one.</p>"
            "<p>In a form the picker submits the <code>File</code> objects themselves, one entry per "
            "file under its <code>name</code>; <code>required</code> makes it invalid while empty; a "
            "form reset or a disabled <code>&lt;fieldset&gt;</code> clears / disables it.</p>"
            "<p>With <code>upload-url</code> every accepted file is POSTed at once as multipart form "
            "data (field = <code>name</code>, or <code>file</code>) with a progress bar; "
            "<code>uploadHeaders</code> adds request headers (for example a CSRF token) and "
            "<code>with-credentials</code> sends cookies cross-origin. Only a 2xx answer counts as "
            "success; a failed file shows Retry, also available as <code>retry(file)</code>.</p>"
        ),
        how_to_use=(
            "<p>Give it a <code>name</code> inside a form, add <code>multiple</code> for more than one "
            "file and restrict input with <code>accept</code>, <code>max-size</code> and "
            "<code>max-files</code>. Change the texts with <code>label</code> (button) and "
            "<code>dropzone-label</code>, and the content with the <code>icon</code> and "
            "<code>hint</code> slots. Read <code>files</code> or listen for <code>mj-change</code> "
            "(<code>{ files }</code>); call <code>preventDefault()</code> on <code>mj-file-add</code> to "
            "veto a file. For immediate upload set <code>upload-url</code> and follow "
            "<code>mj-upload-progress</code>, <code>mj-upload-success</code> and "
            "<code>mj-upload-error</code>.</p>"
        ),
        example="",
        attributes=[
            AttributeDoc(name="multiple", description="Allow several files; without it a new file replaces the current one.",
                         kind="boolean"),
            AttributeDoc(name="accept", description="Comma-separated extensions (`.pdf`), wildcards (`image/*`) or MIME types; also passed to the native chooser.",
                         kind="string", values=["image/*", ".pdf,.docx", ".csv,text/plain"]),
            AttributeDoc(name="max-size", description="Largest accepted file in bytes; 0 or absent = no limit.",
                         kind="number"),
            AttributeDoc(name="max-files", description="Most files kept (with `multiple`); 0 or absent = no limit.",
                         kind="number"),
            AttributeDoc(name="label", description="Text of the choose button.", kind="string",
                         values=["Upload images", "Attach file"], default="Choose files"),
            AttributeDoc(name="dropzone-label", description="Text shown above the button in the drop zone.", kind="string",
                         values=["Drop images here or"], default="Drag files here or"),
            AttributeDoc(name="variant", description="`button` shows only the choose button (no drop-zone frame, icon, label or hint). Absent: the drop zone.",
                         kind="enum", values=["button"]),
            AttributeDoc(name="name", description="Form field name; each File is submitted under it. Also the upload field name (default `file`).",
                         kind="string", values=["attachments"]),
            AttributeDoc(name="required", description="Invalid (valueMissing) while no file is selected.", kind="boolean"),
            AttributeDoc(name="required-message", description="Validation message used instead of the default when `required` fails.",
                         kind="string", values=["Attach at least one file."]),
            AttributeDoc(name="disabled", description="Disables the drop zone, buttons and drops (also inside a disabled `<fieldset>`).",
                         kind="boolean"),
            AttributeDoc(name="invalid", description="Danger border on the drop zone.", kind="boolean"),
            AttributeDoc(name="upload-url", description="POST endpoint; when set, accepted files upload immediately.",
                         kind="string"),
            AttributeDoc(name="with-credentials", description="Send cookies with cross-origin uploads (XHR `withCredentials`).",
                         kind="boolean"),
        ],
        events=[
            ("mj-change", "The selection changed (files added or removed). Not fired by a form reset.", "{ files: File[] }"),
            ("change", "Plain `Event` (no detail) fired right after every `mj-change`, for native-style listeners.", ""),
            ("mj-file-add", "Cancelable; a file passed validation and is about to be added. `preventDefault()` rejects it silently.",
             "{ file: File }"),
            ("mj-file-remove", "A file was removed with its remove button.", "{ file: File }"),
            ("mj-file-error", "A file failed validation and was not added.",
             "{ file: File, error: 'type' | 'size' | 'count' }"),
            ("mj-upload-progress", "Upload progress of one file.",
             "{ file: File, loaded: number, total: number, percent: number }"),
            ("mj-upload-success", "The server answered 2xx for a file.", "{ file: File, response: string }"),
            ("mj-upload-error", "A network error or non-2xx answer.", "{ file: File, error: Error }"),
            ("mj-drag-enter", "A drag entered the drop zone (once per drag).", "{}"),
            ("mj-drag-leave", "The drag left the drop zone without dropping.", "{}"),
        ],
        examples=[
            ComponentExample(
                key="basic",
                title="Basic usage",
                description=(
                    "<p>An image picker for up to five files with a hint. Click the drop zone or "
                    "<em>Upload images</em>, or drag images onto it; chosen files show a thumbnail and a "
                    "remove button, and <code>mj-change</code> appears in Events.</p>"
                ),
                html=(
                    '<mj-file-picker accept="image/*" multiple max-files="5" label="Upload images">\n'
                    '  <span slot="hint">PNG, JPG or GIF, up to 5 files</span>\n'
                    '</mj-file-picker>'
                ),
                css="body { padding: var(--mj-space-4); }",
            ),
            ComponentExample(
                key="validation",
                title="Validation",
                description=(
                    "<p><code>accept=\".pdf,.csv,text/plain\"</code>, <code>max-size=\"102400\"</code> "
                    "(100 KB) and <code>max-files=\"3\"</code>. The script drops six files: three are "
                    "added (<code>mj-file-add</code>), a PNG fails the type, a 300 KB PDF the size and "
                    "the sixth file the count (<code>mj-file-error</code>); all three messages are "
                    "shown.</p>"
                ),
                html=(
                    '<mj-file-picker id="docs" accept=".pdf,.csv,text/plain" max-size="102400" max-files="3" multiple\n'
                    '  label="Add documents" dropzone-label="Drop up to three documents or">\n'
                    '  <span slot="hint">PDF, CSV or plain text, 100 KB each</span>\n'
                    '</mj-file-picker>'
                ),
                css="body { padding: var(--mj-space-4); }",
                script=(
                    'const picker = document.getElementById("docs")\n'
                    'const bytes = (count) => new Uint8Array(count)\n'
                    'const transfer = new DataTransfer()\n'
                    'transfer.items.add(new File([bytes(20480)], "report.pdf", { type: "application/pdf" }))\n'
                    'transfer.items.add(new File(["Meeting notes"], "notes.txt", { type: "text/plain" }))\n'
                    'transfer.items.add(new File([bytes(2048)], "photo.png", { type: "image/png" }))\n'
                    'transfer.items.add(new File([bytes(307200)], "scan.pdf", { type: "application/pdf" }))\n'
                    'transfer.items.add(new File(["a,b\\n1,2"], "budget.csv", { type: "text/csv" }))\n'
                    'transfer.items.add(new File(["c,d\\n3,4"], "extra.csv", { type: "text/csv" }))\n'
                    'picker.shadowRoot.querySelector("[part=dropzone]").dispatchEvent(\n'
                    '  new DragEvent("drop", { dataTransfer: transfer, bubbles: true, cancelable: true, composed: true }))\n'
                    'mjSandbox.log("files", { names: picker.files.map((file) => file.name), value: picker.value })\n'
                ),
            ),
            ComponentExample(
                key="upload",
                title="Upload with progress and retry",
                description=(
                    "<p>With <code>upload-url</code> files upload as soon as they are added. So the example "
                    "runs offline, the script replaces <code>XMLHttpRequest</code> with a simulated server "
                    "(logging the <code>uploadHeaders</code> it receives): <em>logo.png</em> succeeds; "
                    "<em>flaky-scan.pdf</em> fails the first time and shows Retry, which succeeds. Watch "
                    "<code>mj-upload-progress</code>, <code>mj-upload-success</code> and "
                    "<code>mj-upload-error</code>.</p>"
                ),
                html=(
                    '<mj-file-picker id="uploader" name="attachment" multiple upload-url="/demo/upload"\n'
                    '  label="Upload files"></mj-file-picker>'
                ),
                css="body { padding: var(--mj-space-4); }",
                script=(
                    '// A stand-in for a real endpoint so the example works without a server.\n'
                    'const attempts = {}\n'
                    'class SimulatedUpload extends EventTarget {\n'
                    '  constructor() { super(); this.upload = new EventTarget(); this.status = 0; this.responseText = ""; this.headers = {}; this.timers = [] }\n'
                    '  open(method, url) { this.url = url }\n'
                    '  setRequestHeader(name, value) { this.headers[name] = value }\n'
                    '  abort() { this.timers.forEach(clearTimeout) }\n'
                    '  send(body) {\n'
                    '    const file = body.values().next().value\n'
                    '    attempts[file.name] = (attempts[file.name] || 0) + 1\n'
                    '    mjSandbox.log("server received", { url: this.url, file: file.name, attempt: attempts[file.name], headers: this.headers })\n'
                    '    const total = Math.max(file.size, 1)\n'
                    '    for (let step = 1; step <= 4; step = step + 1) {\n'
                    '      this.timers.push(setTimeout(() => {\n'
                    '        this.upload.dispatchEvent(new ProgressEvent("progress", { lengthComputable: true, loaded: total * step / 4, total: total }))\n'
                    '      }, step * 300))\n'
                    '    }\n'
                    '    this.timers.push(setTimeout(() => {\n'
                    '      const fails = file.name.startsWith("flaky") && attempts[file.name] === 1\n'
                    '      this.status = fails ? 503 : 201\n'
                    '      this.responseText = fails ? "busy" : JSON.stringify({ stored: file.name })\n'
                    '      this.dispatchEvent(new Event("load"))\n'
                    '    }, 1500))\n'
                    '  }\n'
                    '}\n'
                    'window.XMLHttpRequest = SimulatedUpload\n'
                    '\n'
                    'const picker = document.getElementById("uploader")\n'
                    'picker.uploadHeaders = { "X-CSRF-Token": "demo-token" }\n'
                    'picker.addEventListener("mj-upload-error", (event) => {\n'
                    '  mjSandbox.log("will retry", { file: event.detail.file.name })\n'
                    '  setTimeout(() => picker.retry(event.detail.file), 800)\n'
                    '})\n'
                    'const canvas = document.createElement("canvas")\n'
                    'canvas.width = 48\n'
                    'canvas.height = 48\n'
                    'const context = canvas.getContext("2d")\n'
                    'context.fillStyle = "#3b82f6"\n'
                    'context.fillRect(0, 0, 48, 48)\n'
                    'const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/png"))\n'
                    'const transfer = new DataTransfer()\n'
                    'transfer.items.add(new File([blob], "logo.png", { type: "image/png" }))\n'
                    'transfer.items.add(new File([new Uint8Array(40960)], "flaky-scan.pdf", { type: "application/pdf" }))\n'
                    'picker.shadowRoot.querySelector("[part=dropzone]").dispatchEvent(\n'
                    '  new DragEvent("drop", { dataTransfer: transfer, bubbles: true, cancelable: true, composed: true }))\n'
                ),
            ),
            ComponentExample(
                key="slots",
                title="Slots, labels and button variant",
                description=(
                    "<p>A drop zone with a custom <code>icon</code> slot, <code>dropzone-label</code>, "
                    "<code>label</code> and <code>hint</code> slot, then a single-file "
                    "<code>variant=\"button\"</code> picker (just the button). Toggle the slots in the "
                    "Slots panel.</p>"
                ),
                html=(
                    '<mj-file-picker accept=".pdf,.docx" dropzone-label="Drop your CV here or" label="Browse">\n'
                    '  <svg slot="icon" viewBox="0 0 24 24" width="32" height="32" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">\n'
                    '    <path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><path d="M14 3v6h6"/>\n'
                    '  </svg>\n'
                    '  <span slot="hint">PDF or Word document; a new file replaces the current one</span>\n'
                    '</mj-file-picker>\n'
                    '<p class="caption">Button variant</p>\n'
                    '<mj-file-picker variant="button" label="Attach file"></mj-file-picker>'
                ),
                css=(
                    "body { padding: var(--mj-space-4); }\n"
                    ".caption { color: var(--mj-text-muted); margin-block: var(--mj-space-4) var(--mj-space-2); }\n"
                ),
            ),
            ComponentExample(
                key="form",
                title="Form and states",
                description=(
                    "<p>A <code>required</code> picker with <code>required-message</code> in a form. "
                    "Submit lists the <code>File</code> entries of the <code>FormData</code> (or the "
                    "validation message); Reset clears the selection. Below: a picker inside a "
                    "<code>&lt;fieldset disabled&gt;</code> and one with <code>invalid</code> styling.</p>"
                ),
                html=(
                    '<form id="claim">\n'
                    '  <mj-file-picker name="receipts" multiple required required-message="Attach at least one receipt."\n'
                    '    label="Add receipts"></mj-file-picker>\n'
                    '  <div class="actions">\n'
                    '    <button type="submit">Submit claim</button>\n'
                    '    <button type="reset">Reset</button>\n'
                    '  </div>\n'
                    '  <pre id="claim-output"></pre>\n'
                    '  <fieldset disabled>\n'
                    '    <legend>Locked (fieldset disabled)</legend>\n'
                    '    <mj-file-picker name="locked" variant="button"></mj-file-picker>\n'
                    '  </fieldset>\n'
                    '</form>\n'
                    '<p class="caption">invalid</p>\n'
                    '<mj-file-picker invalid label="Choose a file"></mj-file-picker>'
                ),
                css=(
                    "body { padding: var(--mj-space-4); }\n"
                    ".actions { display: flex; gap: var(--mj-space-2); margin-block: var(--mj-space-3); }\n"
                    "fieldset { border: 1px solid var(--mj-border); border-radius: var(--mj-radius-md); }\n"
                    ".caption { color: var(--mj-text-muted); margin-block: var(--mj-space-4) var(--mj-space-2); }\n"
                    "pre { font-family: var(--mj-font-mono); font-size: var(--mj-font-size-sm); white-space: pre-wrap; }\n"
                ),
                script=(
                    'const form = document.getElementById("claim")\n'
                    'const output = document.getElementById("claim-output")\n'
                    'const picker = form.querySelector("[name=receipts]")\n'
                    'form.addEventListener("submit", (event) => {\n'
                    '  event.preventDefault()\n'
                    '  const entries = new FormData(form).getAll("receipts")\n'
                    '  const files = entries.map((file) => file.name + " (" + file.size + " bytes, File: " + (file instanceof File) + ")")\n'
                    '  output.textContent = "submitted receipts:\\n" + files.join("\\n")\n'
                    '  mjSandbox.log("submitted", { receipts: files })\n'
                    '})\n'
                    'picker.addEventListener("invalid", () => {\n'
                    '  output.textContent = "blocked: " + picker.validationMessage\n'
                    '})\n'
                    'form.addEventListener("reset", () => setTimeout(() => {\n'
                    '  output.textContent = "after reset: " + picker.files.length + " files"\n'
                    '}, 0))\n'
                ),
            ),
            ComponentExample(
                key="events",
                title="Events and vetoing files",
                description=(
                    "<p>The script vetoes duplicate names in <code>mj-file-add</code>, simulates a drag "
                    "(<code>mj-drag-enter</code>, <code>mj-drag-leave</code>), drops three files of which "
                    "one is a duplicate, then removes one with its remove button "
                    "(<code>mj-file-remove</code>, <code>mj-change</code>).</p>"
                ),
                html=(
                    '<mj-file-picker id="events-picker" multiple label="Choose files"></mj-file-picker>'
                ),
                css="body { padding: var(--mj-space-4); }",
                script=(
                    'const picker = document.getElementById("events-picker")\n'
                    'const zone = picker.shadowRoot.querySelector("[part=dropzone]")\n'
                    'picker.addEventListener("mj-file-add", (event) => {\n'
                    '  const name = event.detail.file.name\n'
                    '  if (picker.files.some((file) => file.name === name)) {\n'
                    '    event.preventDefault()\n'
                    '    mjSandbox.log("vetoed duplicate", { name: name })\n'
                    '  }\n'
                    '})\n'
                    'zone.dispatchEvent(new DragEvent("dragenter", { bubbles: true, composed: true }))\n'
                    'zone.dispatchEvent(new DragEvent("dragleave", { bubbles: true, composed: true }))\n'
                    'const drop = (names) => {\n'
                    '  const transfer = new DataTransfer()\n'
                    '  names.forEach((name) => transfer.items.add(new File(["Quarterly figures"], name, { type: "text/plain" })))\n'
                    '  zone.dispatchEvent(new DragEvent("drop", { dataTransfer: transfer, bubbles: true, cancelable: true, composed: true }))\n'
                    '}\n'
                    'drop(["q1.txt", "q2.txt"])\n'
                    'drop(["q2.txt", "q3.txt"])\n'
                    'picker.shadowRoot.querySelector("[part=file-remove]").click()\n'
                    'mjSandbox.log("files", { names: picker.files.map((file) => file.name), items: picker.fileItems.map((item) => item.status) })\n'
                ),
            ),
        ],
        slots=[
            ("icon", "Icon above the drop-zone label (default: a folder emoji). Hidden in the button variant.",
             '<svg viewBox="0 0 24 24" width="32" height="32" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M12 16V4m0 0-4 4m4-4 4 4"/><path d="M4 16v3a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-3"/></svg>'),
            ("hint", "Small helper text under the label, e.g. accepted types and limits. Hidden in the button variant.",
             "<span>PNG or JPG, up to 2 MB</span>"),
        ],
        properties=[
            ("files", "File[] (read-only). The selected files, in order."),
            ("fileItems", "object[] (read-only). A copy of the internal list: `{ id, file, status: 'ready' | 'uploading' | 'success' | 'error', progress, objectUrl, xhr }` per file."),
            ("value", "string. The selected file names joined with commas; like a native file input it can only be set to `\"\"`, which clears the selection (no events)."),
            ("uploadHeaders", "object. `{ name: value }` request headers sent with every upload, e.g. `{ \"X-CSRF-Token\": token }`."),
            ("form", "HTMLFormElement | null (read-only). The owning form."),
            ("validity", "ValidityState (read-only). valueMissing for an empty required picker."),
            ("validationMessage", "string (read-only). The current validation message."),
        ],
        methods=[
            ("retry(file)", "Uploads a file whose upload failed again (`file` is one of `files`; needs `upload-url`)."),
            ("focus(options?)", "Focuses the choose button."),
            ("checkValidity() -> boolean", "Runs constraint validation."),
            ("reportValidity() -> boolean", "Runs constraint validation and reports a failure to the user."),
        ],
        parts=[
            ("dropzone", "The drop area (focusable region; in the button variant just the button's container)."),
            ("dropzone-icon", "Wrapper of the `icon` slot."),
            ("dropzone-label", "The drop-zone text (`dropzone-label`)."),
            ("dropzone-hint", "Wrapper of the `hint` slot."),
            ("choose-button", "The button that opens the file chooser."),
            ("file-list", "The list of selected files."),
            ("file-item", "One file row."),
            ("file-preview", "The image thumbnail or the file icon of a row."),
            ("file-name", "The file name."),
            ("file-size", "The formatted file size."),
            ("file-status", "Upload status text (Uploading..., Uploaded, Upload failed)."),
            ("file-progress", "The upload progress bar (role progressbar)."),
            ("file-retry", "The Retry button of a failed upload."),
            ("file-remove", "The remove button of a row."),
            ("error", "The validation messages (role alert)."),
        ],
        css_properties=[
            ("--mj-file-picker-dropzone-min-height", "Minimum drop-zone height (default 8rem)."),
            ("--mj-file-picker-dropzone-border", "Drop-zone border (default 2px dashed var(--mj-border-strong))."),
            ("--mj-file-picker-dropzone-active-border", "Border while a drag is over it (default 2px dashed var(--mj-accent))."),
            ("--mj-file-picker-dropzone-active-bg", "Background while a drag is over it (default var(--mj-bg-subtle))."),
            ("--mj-file-picker-border-radius", "Drop-zone corner radius (default var(--mj-radius-md))."),
            ("--mj-file-picker-preview-size", "Size of the thumbnail / file icon (default 3rem)."),
        ],
    ),
    ComponentDoc(
        tag="mj-asset-picker",
        title="Asset Picker",
        group="selection",
        summary=(
            "Form-associated popup grid for choosing emoji, icons or any author-supplied visual assets, "
            "with search, category filters and keyboard navigation."
        ),
        description=(
            "<p><code>&lt;mj-asset-picker&gt;</code> is a trigger button that opens a dialog with a search "
            "field, a category bar and a grid of assets. Picking an asset shows it on the trigger (up to "
            "three, then <code>+N</code>), fires <code>mj-change</code> and, in single mode, closes the "
            "popup.</p>"
            "<p>An asset is <code>{ id, label, category?, keywords?, glyph?, src? }</code>. A cell shows "
            "<code>src</code> as an image when it is set (http(s), relative or raster <code>data:image/png|gif|"
            "jpeg|webp|avif|bmp</code> URLs; other schemes, including SVG data URLs, are dropped), otherwise "
            "<code>glyph</code>, otherwise the <code>id</code> itself &mdash; for an emoji the id is the "
            "character. Search matches the label, the id and the keywords; a category button filters the grid "
            "to that category and the first button (&#10033;) shows all of them.</p>"
            "<p>Where the assets come from: the <code>assets</code> property (an array), the "
            "<code>dataSource</code> property (an array, an object with <code>query(request)</code> resolving "
            "to an array or <code>{ items }</code>, or an object with <code>search(text)</code>, which is then "
            "also asked for every search), or, when neither is set and <code>type=\"emoji\"</code> (the "
            "default), a built-in starter set of 233 common emoji in 8 categories. The built-in set is not the "
            "full Unicode list; any other <code>type</code> starts empty.</p>"
            "<p>The picker is form-associated: it submits the selected id (comma-separated ids in "
            "<code>multiple</code> mode, as one entry) under <code>name</code>, supports <code>required</code> "
            "and is excluded from the form data while <code>disabled</code>. The <code>value</code> attribute "
            "is the <em>initial</em> selection, restored by form reset; picks change the <code>value</code> "
            "property and the form value, not the attribute.</p>"
            "<p>Recently picked assets are kept in <code>recentAssets</code> for the page's lifetime (at most "
            "<code>recents-count</code>); their ids are also written to <code>localStorage</code> under "
            "<code>mj-asset-picker-recents-&lt;type&gt;</code>, but the picker does not read them back or show "
            "a recents row.</p>"
        ),
        how_to_use=(
            "<p><strong>Built-in emoji:</strong> <code>&lt;mj-asset-picker name=\"reaction\"&gt;&lt;/mj-asset-"
            "picker&gt;</code>. Set <code>value=\"&#x1F680;\"</code> for an initial pick.</p>"
            "<p><strong>Your own assets:</strong> assign <code>picker.assets = [{ id, label, category, keywords, "
            "glyph | src }]</code>, or <code>picker.dataSource</code> for assets that load asynchronously or are "
            "searched on a server (<code>search(text)</code>). Assigning <code>dataSource = null</code> goes "
            "back to the built-in set.</p>"
            "<p><strong>Layout:</strong> <code>columns</code> (1&ndash;24, default 8) and <code>cell-size</code> "
            "(any CSS length) size the grid; the popup is as wide as the grid needs unless "
            "<code>--mj-asset-picker-popup-width</code> sets it, and as tall as "
            "<code>--mj-asset-picker-popup-height</code>. Put your "
            "own trigger content in the <code>trigger</code> slot (it replaces the selected-asset preview) and "
            "a custom empty-search message in <code>no-results</code>.</p>"
            "<p><strong>Keyboard:</strong> Enter/Space on the trigger opens the dialog with focus in the search "
            "field; Tab moves between search, categories and the grid (focus is trapped while open); in the grid "
            "the arrow keys move one cell or one row, Home/End go to the start/end of the row, Ctrl+Home/"
            "Ctrl+End to the first/last asset, Enter/Space picks; Escape closes and returns focus to the "
            "trigger. A click outside closes it too.</p>"
        ),
        example="",
        attributes=[
            AttributeDoc(
                name="type",
                description=(
                    "Built-in set used when neither `assets` nor `dataSource` is set: `emoji` (233 common emoji). "
                    "Any other value starts empty. Also names the recents storage key."
                ),
                kind="string",
                values=["emoji"],
                default="emoji",
            ),
            AttributeDoc(
                name="value",
                description=(
                    "Initial selection: an asset id, or comma-separated ids with `multiple` (without it only the "
                    "first id is kept). Restored by form reset; picks are not written back (read the `value` property)."
                ),
                kind="string",
                values=["\U0001F680", "\U0001F44D", "\U0001F44D,\U0001F389,\U0001F680"],
            ),
            AttributeDoc(
                name="multiple",
                description=(
                    "Clicking a cell toggles it and the popup stays open. Removing the attribute keeps only the "
                    "first selected asset."
                ),
                kind="boolean",
            ),
            AttributeDoc(
                name="columns",
                description="Cells per grid row, 1 to 24; arrow-key navigation follows it.",
                kind="number",
                default="8",
            ),
            AttributeDoc(
                name="cell-size",
                description="CSS length of each cell; overrides `--mj-asset-picker-cell-size`.",
                kind="string",
                values=["1.75rem", "2rem", "2.5rem", "3rem"],
                default="2rem",
            ),
            AttributeDoc(
                name="search-placeholder",
                description="Placeholder of the search field.",
                kind="string",
                values=["Search emoji", "Search icons"],
                default="Search",
            ),
            AttributeDoc(
                name="open",
                description=(
                    "Present while the popup is shown; set or remove it to open or close (no `mj-open` is fired "
                    "when you set it directly)."
                ),
                kind="boolean",
            ),
            AttributeDoc(
                name="disabled",
                description="Dims the trigger, blocks opening and picking, closes an open popup, and leaves the picker out of form data. An ancestor `<fieldset disabled>` does the same.",
                kind="boolean",
            ),
            AttributeDoc(
                name="name",
                description="Form field name; the selected id (comma-joined ids in multiple mode) is submitted as one entry.",
                kind="string",
            ),
            AttributeDoc(
                name="required",
                description="The form is invalid while nothing is selected (also when set or removed after the picker rendered).",
                kind="boolean",
            ),
            AttributeDoc(
                name="required-message",
                description="Validation message for an empty required picker (default: \"This field is required.\").",
                kind="string",
            ),
            AttributeDoc(
                name="recents-count",
                description="How many recently picked assets `recentAssets` keeps.",
                kind="number",
                default="18",
            ),
        ],
        events=[
            (
                "mj-change",
                "The user picked or (multiple mode) un-picked an asset; not fired for `value` changes made in code. A plain `change` event follows.",
                "{ value: string, asset: Asset | null, assets: Asset[] }",
            ),
            (
                "mj-search",
                "A search ran (150 ms after the user stopped typing in the search field).",
                "{ query: string, results: Asset[] }",
            ),
            (
                "mj-open",
                "Cancelable; the user (trigger click) or the `open` property is about to open the popup. `preventDefault()` keeps it closed.",
                "{}",
            ),
            (
                "mj-close",
                "The popup closed (pick in single mode, Escape, trigger click, outside click, `open = false`, or `disabled`).",
                "{}",
            ),
        ],
        examples=[
            ComponentExample(
                key="basic",
                title="Basic usage",
                description=(
                    "<p>The built-in emoji set. Click the trigger, browse with the category buttons or type in the "
                    "search field (try <em>heart</em>), and pick one: it appears on the trigger and "
                    "<code>mj-change</code> shows in Events. Use the arrow keys in the grid and Escape to close.</p>"
                ),
                html=(
                    '<mj-asset-picker id="demo-emoji" name="reaction" search-placeholder="Search emoji"></mj-asset-picker>\n'
                    '<span class="hint">Pick a reaction</span>'
                ),
                css=(
                    ".hint { margin-inline-start: var(--mj-space-2); color: var(--mj-text-muted); "
                    "font-size: var(--mj-font-size-sm); }"
                ),
                height=460,
            ),
            ComponentExample(
                key="multiple",
                title="Multiple, preset value, grid size",
                description=(
                    "<p><code>multiple</code> with three preset ids, a 6-column grid of 2.5rem cells, opened on load. "
                    "Clicking toggles a cell and the popup stays open; the trigger shows three assets and then "
                    "<code>+N</code>. Change <code>columns</code> or <code>cell-size</code> in Controls.</p>"
                ),
                html=(
                    '<mj-asset-picker id="demo-multi" multiple value="\U0001F44D,\U0001F389,\U0001F680" '
                    'columns="6" cell-size="2.5rem" open></mj-asset-picker>'
                ),
                height=500,
            ),
            ComponentExample(
                key="custom-assets",
                title="Custom assets and trigger slot",
                description=(
                    "<p>The script assigns <code>assets</code>: glyph icons in three categories with search "
                    "keywords (try <em>done</em> or <em>love</em>) plus PNG avatars shown through <code>src</code>. "
                    "The <code>trigger</code> slot replaces the built-in preview; the script updates it on "
                    "<code>mj-change</code>.</p>"
                ),
                html=(
                    '<mj-asset-picker id="demo-icons" name="icon" value="star" columns="6" cell-size="2.25rem"\n'
                    '                 search-placeholder="Search icons">\n'
                    '  <span slot="trigger" id="demo-icons-label">Choose an icon</span>\n'
                    '</mj-asset-picker>'
                ),
                css=(
                    "#demo-icons::part(asset-cell) { font-size: 1.1rem; color: var(--mj-accent); }"
                ),
                script=(
                    'const picker = document.getElementById("demo-icons")\n'
                    'const label = document.getElementById("demo-icons-label")\n'
                    'const teal = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAIAAABvFaqvAAAAT0lEQVR42mPgndJBFcQwahClBp35/REZkWkQmin4zWIgyRQ8Zo0aRIFBVIs1aqajQZZFqBPYeEzBZRYDGaZgNYuBPFMwzWIg2xQ0s4axQQB/eLzFNM/CMgAAAABJRU5ErkJggg=="\n'
                    'const violet = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAIAAABvFaqvAAAAT0lEQVR42mOosXpLFcQwahClBr19+Q8ZkWkQmin4zWIgyRQ8Zo0aRIFBVIs1aqajQZZFqBPYeEzBZRYDGaZgNYuBPFMwzWIg2xQ0s4axQQBkRItmWThwLQAAAABJRU5ErkJggg=="\n'
                    'picker.assets = [\n'
                    '  { id: "star", label: "Star", category: "Shapes", glyph: "\\u2605", keywords: ["favourite", "rating"] },\n'
                    '  { id: "heart", label: "Heart", category: "Shapes", glyph: "\\u2665", keywords: ["love", "like"] },\n'
                    '  { id: "diamond", label: "Diamond", category: "Shapes", glyph: "\\u25C6" },\n'
                    '  { id: "circle", label: "Circle", category: "Shapes", glyph: "\\u25CF" },\n'
                    '  { id: "square", label: "Square", category: "Shapes", glyph: "\\u25A0" },\n'
                    '  { id: "triangle", label: "Triangle", category: "Shapes", glyph: "\\u25B2" },\n'
                    '  { id: "up", label: "Arrow up", category: "Arrows", glyph: "\\u2191", keywords: ["increase"] },\n'
                    '  { id: "down", label: "Arrow down", category: "Arrows", glyph: "\\u2193", keywords: ["decrease"] },\n'
                    '  { id: "left", label: "Arrow left", category: "Arrows", glyph: "\\u2190", keywords: ["back"] },\n'
                    '  { id: "right", label: "Arrow right", category: "Arrows", glyph: "\\u2192", keywords: ["next"] },\n'
                    '  { id: "swap", label: "Swap", category: "Arrows", glyph: "\\u21C4" },\n'
                    '  { id: "refresh", label: "Refresh", category: "Arrows", glyph: "\\u21BB", keywords: ["reload"] },\n'
                    '  { id: "done", label: "Done", category: "Status", glyph: "\\u2713", keywords: ["complete", "check"] },\n'
                    '  { id: "failed", label: "Failed", category: "Status", glyph: "\\u2717", keywords: ["error"] },\n'
                    '  { id: "flag", label: "Flagged", category: "Status", glyph: "\\u2691" },\n'
                    '  { id: "todo", label: "To do", category: "Status", glyph: "\\u2610" },\n'
                    '  { id: "progress", label: "In progress", category: "Status", glyph: "\\u25D4" },\n'
                    '  { id: "teal", label: "Teal avatar", category: "Avatars", src: teal, keywords: ["person"] },\n'
                    '  { id: "violet", label: "Violet avatar", category: "Avatars", src: violet, keywords: ["person"] }\n'
                    ']\n'
                    'const show = () => {\n'
                    '  const asset = picker.selectedAssets[0]\n'
                    '  label.textContent = asset !== undefined ? (asset.glyph || "") + " " + asset.label : "Choose an icon"\n'
                    '}\n'
                    'picker.addEventListener("mj-change", show)\n'
                    'show()\n'
                ),
                height=460,
            ),
            ComponentExample(
                key="data-source",
                title="Searching data source and no-results slot",
                description=(
                    "<p><code>dataSource</code> is an object with an async <code>search(text)</code> (300 ms "
                    "simulated latency): it is asked for the full list once and again for every search. Assets "
                    "without a category hide the category bar. Search for <em>zzz</em> to see the "
                    "<code>no-results</code> slot; each request is logged in Events.</p>"
                ),
                html=(
                    '<mj-asset-picker id="demo-weather" columns="5" cell-size="2.5rem" search-placeholder="Search weather">\n'
                    '  <span slot="no-results">Nothing matches. Try <em>sun</em> or <em>rain</em>.</span>\n'
                    '</mj-asset-picker>'
                ),
                script=(
                    'const picker = document.getElementById("demo-weather")\n'
                    'const weather = [\n'
                    '  { id: "\\u2600\\uFE0F", label: "Sun", keywords: ["sunny", "clear"] },\n'
                    '  { id: "\\u{1F324}\\uFE0F", label: "Sun behind small cloud", keywords: ["sunny", "fair"] },\n'
                    '  { id: "\\u26C5", label: "Sun behind cloud", keywords: ["partly cloudy"] },\n'
                    '  { id: "\\u2601\\uFE0F", label: "Cloud", keywords: ["overcast"] },\n'
                    '  { id: "\\u{1F326}\\uFE0F", label: "Sun behind rain cloud", keywords: ["showers", "rain"] },\n'
                    '  { id: "\\u{1F327}\\uFE0F", label: "Cloud with rain", keywords: ["rain", "wet"] },\n'
                    '  { id: "\\u26C8\\uFE0F", label: "Cloud with lightning and rain", keywords: ["storm", "thunder"] },\n'
                    '  { id: "\\u{1F328}\\uFE0F", label: "Cloud with snow", keywords: ["snow", "cold"] },\n'
                    '  { id: "\\u2744\\uFE0F", label: "Snowflake", keywords: ["snow", "frost"] },\n'
                    '  { id: "\\u{1F32B}\\uFE0F", label: "Fog", keywords: ["mist"] },\n'
                    '  { id: "\\u{1F32C}\\uFE0F", label: "Wind face", keywords: ["windy", "gale"] },\n'
                    '  { id: "\\u{1F308}", label: "Rainbow", keywords: ["rain", "sun"] },\n'
                    '  { id: "\\u2614", label: "Umbrella with rain drops", keywords: ["rain"] },\n'
                    '  { id: "\\u{1F321}\\uFE0F", label: "Thermometer", keywords: ["temperature", "hot"] },\n'
                    '  { id: "\\u{1F32A}\\uFE0F", label: "Tornado", keywords: ["storm"] }\n'
                    ']\n'
                    'const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms))\n'
                    'picker.dataSource = {\n'
                    '  async search(text) {\n'
                    '    mjSandbox.log("search request", { text })\n'
                    '    await wait(300)\n'
                    '    const query = text.toLowerCase()\n'
                    '    return weather.filter((asset) => (asset.label + " " + asset.keywords.join(" ")).toLowerCase().includes(query))\n'
                    '  }\n'
                    '}\n'
                ),
                height=460,
            ),
            ComponentExample(
                key="form",
                title="Form, required and disabled",
                description=(
                    "<p>Three pickers in a form. <em>Topic icons</em> is <code>multiple</code> and "
                    "<code>required</code>: submitting before picking one is blocked by the browser. The disabled "
                    "picker is left out of the form data. Submit shows the entries (multiple ids are one "
                    "comma-joined entry); Reset restores the <code>value</code> attributes.</p>"
                ),
                html=(
                    '<form id="demo-form" class="demo-form">\n'
                    '  <div class="field"><span>Reaction</span>\n'
                    '    <mj-asset-picker id="demo-form-reaction" name="reaction" value="\U0001F44D"></mj-asset-picker></div>\n'
                    '  <div class="field"><span>Topic icons (required)</span>\n'
                    '    <mj-asset-picker name="icons" multiple required></mj-asset-picker></div>\n'
                    '  <div class="field"><span>Mood (disabled)</span>\n'
                    '    <mj-asset-picker name="mood" value="\U0001F634" disabled></mj-asset-picker></div>\n'
                    '  <div class="actions">\n'
                    '    <button type="submit">Submit</button>\n'
                    '    <button type="reset">Reset</button>\n'
                    '  </div>\n'
                    '  <output id="demo-form-output">Submit to see the form data.</output>\n'
                    '</form>'
                ),
                css=(
                    ".demo-form { display: grid; gap: var(--mj-space-3); max-inline-size: 28rem; }\n"
                    ".field { display: flex; align-items: center; justify-content: space-between; gap: var(--mj-space-3); }\n"
                    ".actions { display: flex; gap: var(--mj-space-2); }\n"
                    "output { font-family: var(--mj-font-mono); font-size: var(--mj-font-size-sm); color: var(--mj-text-muted); }"
                ),
                script=(
                    'const form = document.getElementById("demo-form")\n'
                    'const output = document.getElementById("demo-form-output")\n'
                    'form.addEventListener("submit", (event) => {\n'
                    '  event.preventDefault()\n'
                    '  const entries = Array.from(new FormData(form).entries())\n'
                    '  output.textContent = entries.map(([key, value]) => key + "=" + value).join("  ")\n'
                    '  mjSandbox.log("submit", Object.fromEntries(entries))\n'
                    '})\n'
                    'form.addEventListener("reset", () => {\n'
                    '  output.textContent = "Reset: the value attributes are restored."\n'
                    '})\n'
                ),
                height=520,
            ),
            ComponentExample(
                key="events",
                title="Events and the open property",
                description=(
                    "<p>The script opens the popup with <code>open = true</code> (<code>mj-open</code>), closes it "
                    "again (<code>mj-close</code>) and sets <code>value</code> in code (no event). Tick "
                    "<em>Lock</em> to cancel <code>mj-open</code> with <code>preventDefault()</code>; picks are "
                    "logged with the asset label.</p>"
                ),
                html=(
                    '<div class="row">\n'
                    '  <mj-asset-picker id="demo-events" columns="6"></mj-asset-picker>\n'
                    '  <label><input type="checkbox" id="demo-lock"> Lock (cancel <code>mj-open</code>)</label>\n'
                    '</div>'
                ),
                css=".row { display: flex; align-items: center; gap: var(--mj-space-3); }",
                script=(
                    'const picker = document.getElementById("demo-events")\n'
                    'const lock = document.getElementById("demo-lock")\n'
                    'picker.addEventListener("mj-open", (event) => {\n'
                    '  if (lock.checked) {\n'
                    '    event.preventDefault()\n'
                    '    mjSandbox.log("open cancelled", { locked: true })\n'
                    '  }\n'
                    '})\n'
                    'picker.addEventListener("mj-change", (event) => {\n'
                    '  const asset = event.detail.asset\n'
                    '  mjSandbox.log("picked", { value: event.detail.value, label: asset !== null ? asset.label : null })\n'
                    '})\n'
                    'picker.open = true\n'
                    'await new Promise((resolve) => setTimeout(resolve, 400))\n'
                    'picker.open = false\n'
                    'picker.value = "\\u{1F389}"\n'
                    'mjSandbox.log("value set in code", { value: picker.value, label: picker.selectedAssets[0].label })\n'
                ),
                height=460,
            ),
        ],
        slots=[
            (
                "trigger",
                "Content of the trigger button; replaces the built-in preview of the selected assets.",
                "<span>Choose&hellip;</span>",
            ),
            (
                "no-results",
                "Shown in the grid area when the search matches nothing (default: \"No results\").",
                "<span>No matching assets.</span>",
            ),
        ],
        properties=[
            ("value", "string. The selected id (comma-joined ids in multiple mode); setting it selects without firing `mj-change`."),
            ("open", "boolean. Setting `true` opens (fires the cancelable `mj-open`), `false` closes."),
            ("assets", "Asset[]. The full asset list (a copy). Assigning replaces it, including the built-in emoji, and clears `dataSource`."),
            (
                "dataSource",
                "Asset[] | { query(request) } | { search(text) } | null. Loads the assets asynchronously; `search(text)` is also used for every search. `null` restores the built-in set.",
            ),
            ("selectedAssets", "Asset[] (read-only). The selected assets that are in the current list."),
            ("recentAssets", "Asset[] (read-only). Assets picked since the page loaded, most recent first, at most `recents-count`."),
            ("form", "HTMLFormElement | null (read-only). The owning form."),
            ("validity", "ValidityState (read-only). `valueMissing` while `required` and empty."),
            ("validationMessage", "string (read-only). The current validation message."),
        ],
        methods=[
            ("focus(options)", "Focuses the trigger button."),
            ("checkValidity() -> boolean", "Runs constraint validation (fires `invalid` when it fails)."),
            ("reportValidity() -> boolean", "Like `checkValidity()` and shows the browser's message."),
        ],
        parts=[
            ("trigger", "The trigger button."),
            ("popup", "The dialog panel."),
            ("search", "The search input."),
            ("category-nav", "The category button column."),
            ("category-button", "One category button (the first one shows all)."),
            ("asset-area", "The scrolling area around the grid."),
            ("asset-grid", "The grid of rows."),
            ("asset-cell", "One asset button."),
            ("asset-image", "The image of an asset with `src` (in cells and category buttons)."),
            ("no-results", "The empty-search message container."),
        ],
        css_properties=[
            ("--mj-asset-picker-popup-width", "Popup width (default: wide enough for the category column and every grid column)."),
            ("--mj-asset-picker-popup-height", "Popup height (default 24rem)."),
            ("--mj-asset-picker-category-width", "Width of the category column (default 3rem)."),
            ("--mj-asset-picker-cell-size", "Cell size when `cell-size` is not set; also the category button height (default 2rem)."),
            ("--mj-asset-picker-font-size", "Glyph size in the cells (default 1.25rem)."),
            ("--mj-asset-picker-cell-radius", "Cell corner radius (default var(--mj-radius-sm))."),
            ("--mj-asset-picker-selected-bg", "Background of a selected cell (default var(--mj-bg-subtle))."),
        ],
    ),
    ComponentDoc(
        tag="mj-locale-picker",
        title="Locale Picker",
        group="selection",
        summary=(
            "Form-associated combobox for choosing a language, a country/region or a locale, with names from "
            "Intl.DisplayNames in any display language."
        ),
        description=(
            "<p><code>&lt;mj-locale-picker&gt;</code> is a filterable combobox over one of three built-in "
            "datasets, chosen with <code>mode</code>:</p>"
            "<ul>"
            "<li><code>language</code> (default): the ISO 639-1 language codes, value e.g. <code>fr</code>;</li>"
            "<li><code>country</code>: the ISO 3166-1 alpha-2 region codes, value e.g. <code>FR</code>, each "
            "with its flag emoji;</li>"
            "<li><code>locale</code>: about 190 common BCP 47 language-region locales, value e.g. "
            "<code>fr-CA</code>, with the region's flag.</li>"
            "</ul>"
            "<p>The code lists are built in; the names come from <code>Intl.DisplayNames</code> in the "
            "<code>display-locale</code> (default: the browser language), so codes the browser cannot name are "
            "left out (Chromium with English names offers about 130 languages, 249 regions and 156 "
            "locales). The list is sorted by display name. Language and locale options also show the native "
            "name (the language's name in itself) when it differs. Typing filters by native name, display name "
            "and code, ignoring case and accents (<em>francais</em> finds <em>fran&ccedil;ais</em>).</p>"
            "<p><code>allowed</code> / <code>excluded</code> (JSON arrays of codes, case-insensitive) narrow "
            "the list. The <code>dataSource</code> property replaces it with your own items "
            "<code>{ code, displayName?, nativeName?, flag? }</code>.</p>"
            "<p>The picker is form-associated: it submits the selected code under <code>name</code> and "
            "supports <code>required</code>. The <code>value</code> attribute is the <em>initial</em> selection, "
            "restored by form reset; choosing an option changes the <code>value</code> property, not the "
            "attribute. A code that is not in the dataset is kept and shown as typed.</p>"
        ),
        how_to_use=(
            "<p><code>&lt;mj-locale-picker name=\"language\" value=\"de\" clearable&gt;&lt;/mj-locale-picker"
            "&gt;</code>. Pick the dataset with <code>mode</code>, the language of the names with "
            "<code>display-locale</code>, and restrict it with <code>allowed='[\"en\",\"fr\"]'</code> or "
            "<code>excluded</code>.</p>"
            "<p>Option content: <code>show-code</code> adds the code, <code>show-flag=\"false\"</code> hides the "
            "flags (and keeps the globe in the field), <code>show-native-name=\"false\"</code> shows only the "
            "display name. Replace the leading globe/flag with the <code>trigger-icon</code> slot and the empty "
            "list message with <code>no-results</code>.</p>"
            "<p><strong>Pointer:</strong> clicking the field or the chevron opens the full list (also when a "
            "value is shown); the clear button (<code>clearable</code>) empties it. <strong>Keyboard:</strong> "
            "typing opens and filters; ArrowDown/ArrowUp (or Alt+ArrowDown) open and move, Home/End jump, Enter "
            "chooses the highlighted option (or the only match), Escape, Alt+ArrowUp and Tab close and put the "
            "chosen name back.</p>"
        ),
        example="",
        attributes=[
            AttributeDoc(
                name="mode",
                description="Built-in dataset; an unknown value behaves as `language`.",
                kind="enum",
                values=["language", "country", "locale"],
                default="language",
            ),
            AttributeDoc(
                name="value",
                description=(
                    "Initial code (matched case-insensitively). Restored by form reset; user choices are not "
                    "written back (read the `value` property)."
                ),
                kind="string",
                values=["en", "de", "fr", "FR", "JP", "fr-CA", "pt-BR"],
            ),
            AttributeDoc(
                name="display-locale",
                description="Locale of the option names (default: the browser language, then `en`).",
                kind="string",
                values=["en", "de", "fr", "ja", "ar", "zh"],
            ),
            AttributeDoc(
                name="allowed",
                description="JSON array of codes to offer; others are hidden. Case-insensitive; malformed JSON is ignored.",
                kind="json",
            ),
            AttributeDoc(
                name="excluded",
                description="JSON array of codes to hide. Case-insensitive; malformed JSON is ignored.",
                kind="json",
            ),
            AttributeDoc(
                name="placeholder",
                description="Field placeholder (default \"Select a language\" / \"Select a country\" / \"Select a locale\" by mode).",
                kind="string",
            ),
            AttributeDoc(
                name="clearable",
                description="Shows a clear button while a value is selected (not when disabled or readonly).",
                kind="boolean",
            ),
            AttributeDoc(
                name="show-flag",
                description="`false` hides the flags in the options and in the field (country and locale modes).",
                kind="boolean",
                default="true",
            ),
            AttributeDoc(
                name="show-native-name",
                description="`false` shows only the display name, not the language's own name above it.",
                kind="boolean",
                default="true",
            ),
            AttributeDoc(
                name="show-code",
                description="Shows the code at the end of each option (`show-code=\"false\"` also hides it).",
                kind="boolean",
            ),
            AttributeDoc(
                name="open",
                description="Present while the list is shown; set or remove it to open or close.",
                kind="boolean",
            ),
            AttributeDoc(
                name="disabled",
                description="Dims the field and blocks all interaction. An ancestor `<fieldset disabled>` does the same.",
                kind="boolean",
            ),
            AttributeDoc(
                name="readonly",
                description="Shows the value but blocks typing, opening and clearing.",
                kind="boolean",
            ),
            AttributeDoc(
                name="invalid",
                description="Danger border (styling only; validation comes from `required`).",
                kind="boolean",
            ),
            AttributeDoc(
                name="block",
                description="Full-width block display instead of inline-block.",
                kind="boolean",
            ),
            AttributeDoc(
                name="name",
                description="Form field name; the selected code is submitted.",
                kind="string",
            ),
            AttributeDoc(
                name="required",
                description="The form is invalid while no code is selected (also when set or removed after the picker rendered).",
                kind="boolean",
            ),
            AttributeDoc(
                name="required-message",
                description="Validation message for an empty required picker (default: \"This field is required.\").",
                kind="string",
            ),
            AttributeDoc(
                name="aria-label",
                description="Accessible name of the field (default: the placeholder).",
                kind="string",
            ),
        ],
        events=[
            (
                "mj-change",
                "The user chose another option or cleared the field; not fired for `value` set in code. A plain `change` event follows.",
                "{ value: string, previousValue: string, locale: { code, nativeName, displayName, flag } | null }",
            ),
            ("mj-input", "The user typed in the field. A plain `input` event follows.", "{ inputValue: string }"),
            ("mj-clear", "The clear button emptied the field (after `mj-change`).", "{}"),
            (
                "mj-open",
                "Cancelable; the list is about to open (user action or the `open` property). `preventDefault()` keeps it closed.",
                "{}",
            ),
            ("mj-close", "The list closed.", "{}"),
        ],
        examples=[
            ComponentExample(
                key="basic",
                title="Basic usage",
                description=(
                    "<p>A clearable language picker with English names. Click the field to see every language, "
                    "or type (<em>en</em>, <em>deutsch</em>, <em>francais</em>) to filter; choose one with the "
                    "mouse or the arrow keys and Enter.</p>"
                ),
                html=(
                    '<mj-locale-picker id="demo-language" mode="language" display-locale="en"\n'
                    '                  placeholder="Select a language" clearable></mj-locale-picker>'
                ),
                css="#demo-language { inline-size: 20rem; }",
                height=380,
            ),
            ComponentExample(
                key="modes",
                title="Datasets and display languages",
                description=(
                    "<p>The three <code>mode</code> datasets with an initial value and <code>show-code</code>, and "
                    "the same country picker with <code>display-locale=\"ja\"</code> and <code>\"de\"</code>: the "
                    "codes stay the same, the names follow the display locale.</p>"
                ),
                html=(
                    '<div class="grid">\n'
                    '  <span>Language</span>\n'
                    '  <mj-locale-picker id="demo-mode" mode="language" value="fr" display-locale="en" show-code\n'
                    '                    aria-label="Language"></mj-locale-picker>\n'
                    '  <span>Country / region</span>\n'
                    '  <mj-locale-picker mode="country" value="FR" display-locale="en" show-code\n'
                    '                    aria-label="Country"></mj-locale-picker>\n'
                    '  <span>Locale</span>\n'
                    '  <mj-locale-picker mode="locale" value="fr-CA" display-locale="en" show-code\n'
                    '                    aria-label="Locale"></mj-locale-picker>\n'
                    '  <span>Country, in Japanese</span>\n'
                    '  <mj-locale-picker mode="country" value="FR" display-locale="ja"\n'
                    '                    aria-label="Country (Japanese names)"></mj-locale-picker>\n'
                    '  <span>Country, in German</span>\n'
                    '  <mj-locale-picker mode="country" value="FR" display-locale="de"\n'
                    '                    aria-label="Country (German names)"></mj-locale-picker>\n'
                    '</div>'
                ),
                css=(
                    ".grid { display: grid; grid-template-columns: max-content 20rem; gap: var(--mj-space-3); "
                    "align-items: center; }\n"
                    ".grid > span { color: var(--mj-text-muted); font-size: var(--mj-font-size-sm); }"
                ),
                height=420,
            ),
            ComponentExample(
                key="filtering",
                title="Allowed, excluded and option content",
                description=(
                    "<p>The first picker offers only five languages (<code>allowed</code>, with codes); type "
                    "<em>japanese</em> to see the <code>no-results</code> slot. The second hides three countries "
                    "(<code>excluded</code>) and their flags (<code>show-flag=\"false\"</code>); the third shows "
                    "display names only (<code>show-native-name=\"false\"</code>).</p>"
                ),
                html=(
                    '<div class="grid">\n'
                    '  <span>Supported language</span>\n'
                    '  <mj-locale-picker id="demo-allowed" mode="language" display-locale="en" show-code\n'
                    '                    allowed=\'["en","fr","de","es","it"]\' aria-label="Supported language">\n'
                    '    <span slot="no-results">Only English, French, German, Spanish and Italian are supported.</span>\n'
                    '  </mj-locale-picker>\n'
                    '  <span>Shipping country</span>\n'
                    '  <mj-locale-picker mode="country" display-locale="en" excluded=\'["US","CA","MX"]\'\n'
                    '                    show-flag="false" placeholder="Outside North America"\n'
                    '                    aria-label="Shipping country"></mj-locale-picker>\n'
                    '  <span>Subtitle language</span>\n'
                    '  <mj-locale-picker mode="language" display-locale="en" show-native-name="false"\n'
                    '                    aria-label="Subtitle language"></mj-locale-picker>\n'
                    '</div>'
                ),
                css=(
                    ".grid { display: grid; grid-template-columns: max-content 22rem; gap: var(--mj-space-3); "
                    "align-items: center; }\n"
                    ".grid > span { color: var(--mj-text-muted); font-size: var(--mj-font-size-sm); }"
                ),
                height=420,
            ),
            ComponentExample(
                key="states",
                title="Disabled, readonly, invalid, custom icon",
                description=(
                    "<p><code>disabled</code> and <code>readonly</code> both show the value and cannot be opened "
                    "(readonly keeps full contrast); <code>invalid</code> draws the danger border; the last picker "
                    "puts its own icon in the <code>trigger-icon</code> slot instead of the globe/flag.</p>"
                ),
                html=(
                    '<div class="grid">\n'
                    '  <span>Disabled</span>\n'
                    '  <mj-locale-picker id="demo-disabled" mode="language" value="ja" display-locale="en" disabled\n'
                    '                    aria-label="Disabled language"></mj-locale-picker>\n'
                    '  <span>Readonly</span>\n'
                    '  <mj-locale-picker mode="locale" value="pt-BR" display-locale="en" readonly\n'
                    '                    aria-label="Account locale"></mj-locale-picker>\n'
                    '  <span>Invalid</span>\n'
                    '  <mj-locale-picker mode="country" display-locale="en" invalid placeholder="Country is required"\n'
                    '                    aria-label="Country"></mj-locale-picker>\n'
                    '  <span>Custom icon</span>\n'
                    '  <mj-locale-picker mode="language" display-locale="en" value="es" aria-label="Translate to">\n'
                    '    <svg slot="trigger-icon" viewBox="0 0 16 16" width="16" height="16" aria-hidden="true">\n'
                    '      <path fill="currentColor" d="M2 3h7v1.5H6.6c-.3 1.6-1 3-2 4.1.6.5 1.3.9 2 1.2l-.5 1.4c-.9-.4-1.7-.9-2.5-1.5-.8.6-1.7 1.1-2.7 1.4L.5 9.7c.8-.3 1.6-.7 2.2-1.2C2 7.6 1.5 6.6 1.2 5.5h1.5c.2.7.6 1.4 1 2 .6-.8 1.1-1.8 1.3-3H2V3zm9 3h1.6L16 15h-1.6l-.8-2.2h-3.6L9.2 15H7.6L11 6zm-.5 5.4h2.6L11.8 8l-1.3 3.4z"/>\n'
                    '    </svg>\n'
                    '  </mj-locale-picker>\n'
                    '</div>'
                ),
                css=(
                    ".grid { display: grid; grid-template-columns: max-content 20rem; gap: var(--mj-space-3); "
                    "align-items: center; }\n"
                    ".grid > span { color: var(--mj-text-muted); font-size: var(--mj-font-size-sm); }\n"
                    "svg[slot=\"trigger-icon\"] { color: var(--mj-accent); vertical-align: middle; }"
                ),
                height=380,
            ),
            ComponentExample(
                key="form",
                title="Form participation",
                description=(
                    "<p>Two required pickers in a form. Submitting with no country is blocked by the browser; a "
                    "valid submit shows the codes below and in Events. Clear the language, then Reset: the "
                    "<code>value</code> attribute (<code>de</code>) comes back.</p>"
                ),
                html=(
                    '<form id="demo-form" class="demo-form">\n'
                    '  <div class="field"><span>Interface language</span>\n'
                    '    <mj-locale-picker id="demo-form-language" name="language" value="de" display-locale="en"\n'
                    '                      clearable required aria-label="Interface language"></mj-locale-picker></div>\n'
                    '  <div class="field"><span>Country</span>\n'
                    '    <mj-locale-picker name="country" mode="country" display-locale="en" required\n'
                    '                      aria-label="Country"></mj-locale-picker></div>\n'
                    '  <div class="actions">\n'
                    '    <button type="submit">Submit</button>\n'
                    '    <button type="reset">Reset</button>\n'
                    '  </div>\n'
                    '  <output id="demo-form-output">Submit to see the form data.</output>\n'
                    '</form>'
                ),
                css=(
                    ".demo-form { display: grid; gap: var(--mj-space-3); max-inline-size: 32rem; }\n"
                    ".field { display: grid; grid-template-columns: 10rem 1fr; align-items: center; gap: var(--mj-space-3); }\n"
                    ".actions { display: flex; gap: var(--mj-space-2); }\n"
                    "output { font-family: var(--mj-font-mono); font-size: var(--mj-font-size-sm); color: var(--mj-text-muted); }"
                ),
                script=(
                    'const form = document.getElementById("demo-form")\n'
                    'const output = document.getElementById("demo-form-output")\n'
                    'form.addEventListener("submit", (event) => {\n'
                    '  event.preventDefault()\n'
                    '  const data = Object.fromEntries(new FormData(form).entries())\n'
                    '  output.textContent = JSON.stringify(data)\n'
                    '  mjSandbox.log("submit", data)\n'
                    '})\n'
                    'form.addEventListener("reset", () => {\n'
                    '  output.textContent = "Reset: the value attributes are restored."\n'
                    '})\n'
                ),
                height=420,
            ),
            ComponentExample(
                key="data-source",
                title="Custom dataset and events",
                description=(
                    "<p>The script assigns a <code>dataSource</code> whose <code>query()</code> resolves (after "
                    "250 ms) to the five content locales of a site, with custom names and flags, then opens the "
                    "list with <code>open = true</code> (<code>mj-open</code> in Events). Choosing one logs "
                    "<code>mj-change</code> with the item.</p>"
                ),
                html=(
                    '<mj-locale-picker id="demo-custom" value="en-GB" show-code\n'
                    '                  placeholder="Choose a content locale" aria-label="Content locale"></mj-locale-picker>'
                ),
                css="#demo-custom { inline-size: 22rem; }",
                script=(
                    'const picker = document.getElementById("demo-custom")\n'
                    'const locales = [\n'
                    '  { code: "en-GB", displayName: "English (UK)", nativeName: "English (UK)", flag: "\\u{1F1EC}\\u{1F1E7}" },\n'
                    '  { code: "en-US", displayName: "English (US)", nativeName: "English (US)", flag: "\\u{1F1FA}\\u{1F1F8}" },\n'
                    '  { code: "de-DE", displayName: "German", nativeName: "Deutsch", flag: "\\u{1F1E9}\\u{1F1EA}" },\n'
                    '  { code: "fr-CA", displayName: "French (Canada)", nativeName: "Fran\\u00E7ais (Canada)", flag: "\\u{1F1E8}\\u{1F1E6}" },\n'
                    '  { code: "es-419", displayName: "Spanish (Latin America)", nativeName: "Espa\\u00F1ol (Latinoam\\u00E9rica)", flag: "\\u{1F30E}" }\n'
                    ']\n'
                    'const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms))\n'
                    'picker.dataSource = {\n'
                    '  async query(request) {\n'
                    '    await wait(250)\n'
                    '    return { items: locales, total: locales.length }\n'
                    '  }\n'
                    '}\n'
                    'picker.addEventListener("mj-change", (event) => mjSandbox.log("chosen", event.detail.locale))\n'
                    'await wait(400)\n'
                    'picker.open = true\n'
                ),
                height=360,
            ),
        ],
        slots=[
            (
                "trigger-icon",
                "Replaces the leading globe / flag in the field.",
                '<svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><circle cx="8" cy="8" r="6" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M2 8h12M8 2c2 2 2 10 0 12M8 2c-2 2-2 10 0 12" fill="none" stroke="currentColor"/></svg>',
            ),
            (
                "no-results",
                "Shown when nothing matches the typed text (default: \"No results\").",
                "<span>No matching language.</span>",
            ),
        ],
        properties=[
            ("value", "string. The selected code; setting it selects without firing `mj-change`."),
            ("selectedLocale", "{ code, nativeName, displayName, flag } | null (read-only). The selected item, null for an unknown code."),
            ("inputValue", "string (read-only). The text currently in the field."),
            (
                "dataSource",
                "Item[] | { query(request) } | function(request) | null. Replaces the built-in dataset with `{ code, displayName?, nativeName?, flag? }` items (an array or `{ items }`); `allowed` / `excluded` still apply. `null` restores the built-in dataset.",
            ),
            ("open", "boolean. Setting `true` opens (fires the cancelable `mj-open`), `false` closes."),
            ("form", "HTMLFormElement | null (read-only). The owning form."),
            ("validity", "ValidityState (read-only). `valueMissing` while `required` and empty."),
            ("validationMessage", "string (read-only). The current validation message."),
        ],
        methods=[
            ("focus(options)", "Focuses the text field."),
            ("checkValidity() -> boolean", "Runs constraint validation (fires `invalid` when it fails)."),
            ("reportValidity() -> boolean", "Like `checkValidity()` and shows the browser's message."),
        ],
        parts=[
            ("field", "The bordered field row."),
            ("trigger-icon", "The leading icon holder (globe, flag or the slotted icon)."),
            ("input", "The text input (role combobox)."),
            ("clear", "The clear button."),
            ("toggle", "The chevron button."),
            ("popup", "The popup panel."),
            ("listbox", "The option list."),
            ("option", "One option row."),
            ("option-flag", "The flag in an option."),
            ("option-native-name", "The native name line (only when it differs from the display name)."),
            ("option-english-name", "The display-name line (in the `display-locale`, not necessarily English)."),
            ("option-code", "The code (with `show-code`)."),
            ("no-results", "The empty-list message container."),
        ],
        css_properties=[
            ("--mj-locale-picker-border-radius", "Field and popup corner radius (default var(--mj-radius-md))."),
            ("--mj-locale-picker-flag-size", "Flag / icon size (default 1.25rem)."),
            ("--mj-locale-picker-popup-max-height", "Popup maximum height (default 18rem)."),
            ("--mj-locale-picker-option-height", "Minimum option row height (default 2.5rem)."),
            ("--mj-locale-picker-code-color", "Colour of the code (default var(--mj-text-muted))."),
        ],
    ),
    ComponentDoc(
        tag="mj-tag-picker",
        title="Tag Picker",
        group="selection",
        summary=(
            "Form-associated multi-value input that collects removable tokens from suggestions or free text, "
            "with person avatars, limits and async sources."
        ),
        description=(
            "<p><code>&lt;mj-tag-picker&gt;</code> shows the chosen values as pill tokens followed by a text "
            "input. Typing (from <code>min-chars</code> characters, after <code>debounce</code> ms) or "
            "ArrowDown opens a suggestion list with the matching part highlighted; choosing a suggestion adds a "
            "token. Values already chosen are shown dimmed and cannot be chosen again unless "
            "<code>duplicate-values</code> is set.</p>"
            "<p>Suggestions come from, in order of precedence: the <code>dataSource</code> property, the "
            "<code>src</code> URL, or <code>&lt;mj-option&gt;</code> children (matched by label, "
            "case-insensitive). <code>&lt;mj-option value=\"...\" avatar=\"...\" meta=\"...\"&gt;Label&lt;/mj-"
            "option&gt;</code> children are read as data and are not rendered themselves; <code>meta</code> is "
            "shown beside the suggestion, <code>avatar</code> (an image URL) in person mode. "
            "<code>&lt;mj-option&gt;</code> is not a registered element, it is only read by the picker.</p>"
            "<p>With <code>free-text</code> the typed text becomes a token on Enter or on the "
            "<code>delimiter</code> key. With <code>type=\"person\"</code> tokens and suggestions show the avatar "
            "or the initials. <code>max-count</code> caps the tokens: at the limit the "
            "<code>max-count</code> hint appears below the field and describes the input, suggestions no "
            "longer open, and an add attempted there (Enter on typed text, a delimiter) fires "
            "<code>mj-max-count</code> instead. The input stays focusable, so Backspace still reaches the "
            "tokens.</p>"
            "<p>The picker is form-associated: it submits one <code>name=value</code> entry per token and "
            "supports <code>required</code>. The <code>value</code> attribute is the <em>initial</em> value "
            "(comma-separated; a value matching an option takes its label and avatar) and is restored by form "
            "reset; the <code>value</code> property is the current comma-joined string.</p>"
        ),
        how_to_use=(
            "<p><strong>Declarative:</strong> put <code>&lt;mj-option&gt;</code> children inside and an initial "
            "<code>value=\"design,research\"</code>. <strong>Remote:</strong> set <code>src=\"/api/tags\"</code> "
            "(the query is appended as <code>q=</code>; the response is a JSON array or <code>{ items }</code> of "
            "strings or <code>{ value, label, avatar?, meta? }</code>) or assign <code>dataSource</code> &mdash; "
            "an object with <code>query({ filter, query, offset, limit, signal })</code> (the core DataSource "
            "contract), the older <code>fetch({ query, signal })</code>, or a function. The previous request is "
            "aborted through <code>signal</code> when a new one starts; the <code>loading</code> slot shows "
            "meanwhile and a rejected request shows \"Failed to load suggestions.\"</p>"
            "<p>Read or replace the tokens with the <code>tokens</code> property (no event). Cancel "
            "<code>mj-token-add</code> to validate tokens before they are added.</p>"
            "<p><strong>Keyboard:</strong> ArrowDown opens / moves down, ArrowUp moves up, Home/End jump, Enter "
            "adds the highlighted suggestion (or the typed text with <code>free-text</code>), Escape closes and "
            "clears the text. Backspace in an empty input, or ArrowLeft at its start, moves to the last token's "
            "remove button; there ArrowLeft/ArrowRight move between tokens (and back to the input) and "
            "Backspace/Delete remove the token.</p>"
        ),
        example="",
        attributes=[
            AttributeDoc(
                name="value",
                description=(
                    "Initial tokens, comma-separated values. Restored by form reset; user changes are not written "
                    "back (read the `value` property)."
                ),
                kind="string",
                values=["design", "design,research"],
            ),
            AttributeDoc(
                name="placeholder",
                description="Input placeholder, shown only while there are no tokens.",
                kind="string",
            ),
            AttributeDoc(
                name="type",
                description="`person` shows an avatar image or initials on tokens and suggestions.",
                kind="enum",
                values=["tag", "person"],
                default="tag",
            ),
            AttributeDoc(
                name="free-text",
                description="Enter or the `delimiter` key turns the typed text into a token, also when no suggestion matches.",
                kind="boolean",
            ),
            AttributeDoc(
                name="delimiter",
                description="Key that commits a free-text token (a single character, e.g. `;` or a space). Empty disables it.",
                kind="string",
                values=[",", ";", " "],
                default=",",
            ),
            AttributeDoc(
                name="max-count",
                description="Maximum number of tokens (0 or absent: no limit). At the limit the max-count hint is shown, suggestions do not open and an add attempt fires `mj-max-count`.",
                kind="number",
            ),
            AttributeDoc(
                name="duplicate-values",
                description="Allows the same value to be added more than once.",
                kind="boolean",
            ),
            AttributeDoc(
                name="min-chars",
                description="Characters needed before typing opens suggestions (ArrowDown opens them regardless).",
                kind="number",
                default="1",
            ),
            AttributeDoc(
                name="debounce",
                description="Milliseconds between the last keystroke and the suggestion lookup.",
                kind="number",
                default="200",
            ),
            AttributeDoc(
                name="src",
                description="URL of a suggestion endpoint; the query is appended as `q=`. Ignored when `dataSource` is set.",
                kind="string",
            ),
            AttributeDoc(
                name="disabled",
                description="Dims the picker and blocks all interaction; tokens stay visible but cannot be removed. An ancestor `<fieldset disabled>` does the same.",
                kind="boolean",
            ),
            AttributeDoc(
                name="readonly",
                description="Shows the tokens without remove buttons and blocks typing and suggestions.",
                kind="boolean",
            ),
            AttributeDoc(
                name="invalid",
                description="Danger border (styling only; validation comes from `required`).",
                kind="boolean",
            ),
            AttributeDoc(
                name="name",
                description="Form field name; one entry per token value is submitted.",
                kind="string",
            ),
            AttributeDoc(
                name="required",
                description="The form is invalid while there are no tokens.",
                kind="boolean",
            ),
            AttributeDoc(
                name="required-message",
                description="Validation message for an empty required picker (default: \"This field is required.\").",
                kind="string",
            ),
            AttributeDoc(
                name="aria-label",
                description="Accessible name of the token group and the input.",
                kind="string",
                default="Tag picker",
            ),
        ],
        events=[
            (
                "mj-change",
                "The user added or removed a token (not fired for `value` / `tokens` set in code). A plain `change` event follows.",
                "{ tokens: { value, label, avatar }[], values: string[] }",
            ),
            ("mj-input", "The user typed in the input. A plain `input` event follows.", "{ inputValue: string }"),
            (
                "mj-token-add",
                "Cancelable; a token is about to be added. `preventDefault()` rejects it and keeps the typed text.",
                "{ token: { value: string, label: string, avatar: string | null } }",
            ),
            ("mj-token-remove", "The user removed a token (before `mj-change`).", "{ token: { value, label, avatar } }"),
            (
                "mj-max-count",
                "An add was refused because the limit is reached: Enter on typed text or a delimiter at the limit.",
                "{ count: number }",
            ),
            (
                "mj-open",
                "Cancelable; the suggestion list is about to open. `preventDefault()` keeps it closed.",
                "{}",
            ),
            ("mj-close", "The suggestion list closed.", "{}"),
        ],
        examples=[
            ComponentExample(
                key="basic",
                title="Basic usage",
                description=(
                    "<p>Suggestions from <code>&lt;mj-option&gt;</code> children. Type <em>d</em> (or press "
                    "ArrowDown) to open the list, choose with the mouse or the arrow keys and Enter, and remove a "
                    "token with its &times; or with Backspace.</p>"
                ),
                html=(
                    '<mj-tag-picker id="demo-tags" name="topics" placeholder="Add topics&hellip;" aria-label="Topics">\n'
                    '  <mj-option value="design">Design</mj-option>\n'
                    '  <mj-option value="development">Development</mj-option>\n'
                    '  <mj-option value="documentation">Documentation</mj-option>\n'
                    '  <mj-option value="marketing">Marketing</mj-option>\n'
                    '  <mj-option value="product">Product</mj-option>\n'
                    '  <mj-option value="research">Research</mj-option>\n'
                    '  <mj-option value="support">Support</mj-option>\n'
                    '</mj-tag-picker>'
                ),
                css="#demo-tags { max-inline-size: 28rem; }",
                height=340,
            ),
            ComponentExample(
                key="free-text",
                title="Initial value and free text",
                description=(
                    "<p><code>value=\"bug,needs-triage\"</code> renders two tokens (<em>bug</em> takes its option "
                    "label). With <code>free-text</code>, type any label and press Enter or comma. The second "
                    "picker commits on <code>;</code> and allows <code>duplicate-values</code>.</p>"
                ),
                html=(
                    '<div class="stack">\n'
                    '  <mj-tag-picker id="demo-free" free-text value="bug,needs-triage" aria-label="Labels"\n'
                    '                 placeholder="Type a label, then Enter or comma">\n'
                    '    <mj-option value="bug">Bug</mj-option>\n'
                    '    <mj-option value="enhancement">Enhancement</mj-option>\n'
                    '    <mj-option value="question">Question</mj-option>\n'
                    '    <mj-option value="documentation">Documentation</mj-option>\n'
                    '  </mj-tag-picker>\n'
                    '  <mj-tag-picker free-text delimiter=";" duplicate-values aria-label="Keywords"\n'
                    '                 placeholder="Keywords separated by ;"></mj-tag-picker>\n'
                    '</div>'
                ),
                css=".stack { display: grid; gap: var(--mj-space-4); max-inline-size: 28rem; }",
                height=320,
            ),
            ComponentExample(
                key="person",
                title="People with avatars",
                description=(
                    "<p><code>type=\"person\"</code>: options with an <code>avatar</code> show the image, the others "
                    "their initials; <code>meta</code> shows the team. Type <em>a</em> to see them all.</p>"
                ),
                html=(
                    '<mj-tag-picker id="demo-people" type="person" name="reviewers" value="ana"\n'
                    '               placeholder="Add reviewers&hellip;" aria-label="Reviewers">\n'
                    '  <mj-option value="ana" meta="Design"\n'
                    '    avatar="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAIAAABvFaqvAAAAT0lEQVR42mPgndJBFcQwahClBp35/REZkWkQmin4zWIgyRQ8Zo0aRIFBVIs1aqajQZZFqBPYeEzBZRYDGaZgNYuBPFMwzWIg2xQ0s4axQQB/eLzFNM/CMgAAAABJRU5ErkJggg==">Ana Souza</mj-option>\n'
                    '  <mj-option value="ben" meta="Engineering"\n'
                    '    avatar="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAIAAABvFaqvAAAAT0lEQVR42mOosXpLFcQwahClBr19+Q8ZkWkQmin4zWIgyRQ8Zo0aRIFBVIs1aqajQZZFqBPYeEzBZRYDGaZgNYuBPFMwzWIg2xQ0s4axQQBkRItmWThwLQAAAABJRU5ErkJggg==">Ben Okafor</mj-option>\n'
                    '  <mj-option value="chen" meta="Engineering">Chen Wei</mj-option>\n'
                    '  <mj-option value="dara" meta="Product"\n'
                    '    avatar="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAIAAABvFaqvAAAAT0lEQVR42mO4Wc5GFcQwahClBv37fBwZkWkQmin4zWIgyRQ8Zo0aRIFBVIs1aqajQZZFqBPYeEzBZRYDGaZgNYuBPFMwzWIg2xQ0s4axQQCRPwGPNAqNQQAAAABJRU5ErkJggg==">Dara Murphy</mj-option>\n'
                    '  <mj-option value="elif" meta="Research">Elif Yilmaz</mj-option>\n'
                    '  <mj-option value="farah" meta="Support"\n'
                    '    avatar="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAIAAABvFaqvAAAAT0lEQVR42mN4KOtBFcQwahClBv1/8gwZkWkQmin4zWIgyRQ8Zo0aRIFBVIs1aqajQZZFqBPYeEzBZRYDGaZgNYuBPFMwzWIg2xQ0s4axQQDJqPVZZi0u4AAAAABJRU5ErkJggg==">Farah Haddad</mj-option>\n'
                    '</mj-tag-picker>'
                ),
                css="#demo-people { max-inline-size: 30rem; }",
                height=380,
            ),
            ComponentExample(
                key="states",
                title="Limit, readonly, disabled, invalid",
                description=(
                    "<p>The first picker has <code>max-count=\"3\"</code> and two tokens: add one more and the "
                    "<code>max-count</code> slot text appears; type another skill and press Enter to see "
                    "<code>mj-max-count</code> in Events. Then a <code>readonly</code> "
                    "picker (no remove buttons), a <code>disabled</code> one and an <code>invalid</code> one.</p>"
                ),
                html=(
                    '<div class="grid">\n'
                    '  <span>Up to 3 skills</span>\n'
                    '  <mj-tag-picker id="demo-limit" max-count="3" value="css,html" placeholder="Add a skill"\n'
                    '                 aria-label="Skills">\n'
                    '    <mj-option value="css">CSS</mj-option>\n'
                    '    <mj-option value="html">HTML</mj-option>\n'
                    '    <mj-option value="javascript">JavaScript</mj-option>\n'
                    '    <mj-option value="python">Python</mj-option>\n'
                    '    <mj-option value="sql">SQL</mj-option>\n'
                    '    <span slot="max-count">Three skills is the limit; remove one to add another.</span>\n'
                    '  </mj-tag-picker>\n'
                    '  <span>Readonly</span>\n'
                    '  <mj-tag-picker readonly value="css,python" aria-label="Readonly skills">\n'
                    '    <mj-option value="css">CSS</mj-option>\n'
                    '    <mj-option value="python">Python</mj-option>\n'
                    '  </mj-tag-picker>\n'
                    '  <span>Disabled</span>\n'
                    '  <mj-tag-picker disabled value="sql" aria-label="Disabled skills">\n'
                    '    <mj-option value="sql">SQL</mj-option>\n'
                    '  </mj-tag-picker>\n'
                    '  <span>Invalid</span>\n'
                    '  <mj-tag-picker invalid placeholder="At least one skill" aria-label="Required skills"></mj-tag-picker>\n'
                    '</div>'
                ),
                css=(
                    ".grid { display: grid; grid-template-columns: max-content minmax(0, 24rem); gap: var(--mj-space-3); "
                    "align-items: center; }\n"
                    ".grid > span { color: var(--mj-text-muted); font-size: var(--mj-font-size-sm); }"
                ),
                height=380,
            ),
            ComponentExample(
                key="async",
                title="Async data source, loading and no-results slots",
                description=(
                    "<p>The script assigns a <code>dataSource</code> whose <code>query()</code> answers after "
                    "400 ms and honours the abort <code>signal</code>. With <code>min-chars=\"2\"</code> and "
                    "<code>debounce=\"300\"</code>, type <em>sa</em> or <em>par</em>: the <code>loading</code> slot "
                    "shows first; <em>xyz</em> shows the <code>no-results</code> slot. Each request is logged.</p>"
                ),
                html=(
                    '<mj-tag-picker id="demo-async" name="cities" min-chars="2" debounce="300"\n'
                    '               placeholder="Search cities (2+ letters)&hellip;" aria-label="Cities">\n'
                    '  <span slot="loading">Searching cities&hellip;</span>\n'
                    '  <span slot="no-results">No city matches. Try <em>san</em> or <em>par</em>.</span>\n'
                    '</mj-tag-picker>'
                ),
                css="#demo-async { max-inline-size: 28rem; }",
                script=(
                    'const picker = document.getElementById("demo-async")\n'
                    'const cities = [\n'
                    '  ["Paris", "France"], ["Parma", "Italy"], ["Porto", "Portugal"], ["Prague", "Czechia"],\n'
                    '  ["San Diego", "United States"], ["San Francisco", "United States"], ["Santiago", "Chile"],\n'
                    '  ["Sao Paulo", "Brazil"], ["Sapporo", "Japan"], ["Seoul", "South Korea"], ["Sydney", "Australia"],\n'
                    '  ["Lisbon", "Portugal"], ["Lima", "Peru"], ["Lagos", "Nigeria"], ["Nairobi", "Kenya"]\n'
                    ']\n'
                    'const wait = (ms, signal) => new Promise((resolve, reject) => {\n'
                    '  const timer = setTimeout(resolve, ms)\n'
                    '  signal.addEventListener("abort", () => { clearTimeout(timer); reject(signal.reason) })\n'
                    '})\n'
                    'picker.dataSource = {\n'
                    '  async query({ filter, signal }) {\n'
                    '    mjSandbox.log("query", { filter })\n'
                    '    await wait(400, signal)\n'
                    '    const text = filter.toLowerCase()\n'
                    '    const items = cities\n'
                    '      .filter(([name]) => name.toLowerCase().includes(text))\n'
                    '      .map(([name, country]) => ({ value: name.toLowerCase().replace(/ /g, "-"), label: name, meta: country }))\n'
                    '    return { items, total: items.length }\n'
                    '  }\n'
                    '}\n'
                ),
                height=360,
            ),
            ComponentExample(
                key="form-events",
                title="Form, validation and events",
                description=(
                    "<p>A required, free-text picker in a form. The script cancels <code>mj-token-add</code> for "
                    "labels that are not lower-case words with dashes, then simulates two entries: "
                    "<em>Needs Review</em> is rejected, <em>needs-review</em> is added (see Events). Submit lists one "
                    "entry per token; Reset restores <code>value=\"frontend\"</code>.</p>"
                ),
                html=(
                    '<form id="demo-form" class="demo-form">\n'
                    '  <mj-tag-picker id="demo-form-tags" name="labels" required free-text value="frontend"\n'
                    '                 placeholder="lower-case-labels, Enter to add" aria-label="Labels">\n'
                    '    <mj-option value="frontend">frontend</mj-option>\n'
                    '    <mj-option value="backend">backend</mj-option>\n'
                    '    <mj-option value="infrastructure">infrastructure</mj-option>\n'
                    '  </mj-tag-picker>\n'
                    '  <div class="actions">\n'
                    '    <button type="submit">Submit</button>\n'
                    '    <button type="reset">Reset</button>\n'
                    '  </div>\n'
                    '  <output id="demo-form-output">Submit to see the form data.</output>\n'
                    '</form>'
                ),
                css=(
                    ".demo-form { display: grid; gap: var(--mj-space-3); max-inline-size: 28rem; }\n"
                    ".actions { display: flex; gap: var(--mj-space-2); }\n"
                    "output { font-family: var(--mj-font-mono); font-size: var(--mj-font-size-sm); color: var(--mj-text-muted); }"
                ),
                script=(
                    'const form = document.getElementById("demo-form")\n'
                    'const picker = document.getElementById("demo-form-tags")\n'
                    'const output = document.getElementById("demo-form-output")\n'
                    'picker.addEventListener("mj-token-add", (event) => {\n'
                    '  if (/^[a-z0-9]+(-[a-z0-9]+)*$/.test(event.detail.token.value) === false) {\n'
                    '    event.preventDefault()\n'
                    '    mjSandbox.log("rejected", { value: event.detail.token.value })\n'
                    '  }\n'
                    '})\n'
                    'form.addEventListener("submit", (event) => {\n'
                    '  event.preventDefault()\n'
                    '  const labels = new FormData(form).getAll("labels")\n'
                    '  output.textContent = "labels = " + JSON.stringify(labels)\n'
                    '  mjSandbox.log("submit", { labels })\n'
                    '})\n'
                    'form.addEventListener("reset", () => {\n'
                    '  output.textContent = "Reset: the value attribute is restored."\n'
                    '})\n'
                    '\n'
                    '// Simulate the user typing a label and pressing Enter.\n'
                    'const enter = (text) => {\n'
                    '  picker.focus()\n'
                    '  picker.inputValue = text\n'
                    '  const input = picker.shadowRoot.querySelector("[part=input]")\n'
                    '  input.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true, composed: true }))\n'
                    '}\n'
                    'enter("Needs Review")\n'
                    'picker.inputValue = ""\n'
                    'enter("needs-review")\n'
                    'mjSandbox.log("value", { value: picker.value })\n'
                ),
                height=320,
            ),
        ],
        slots=[
            (
                "max-count",
                "Hint shown below the field while the `max-count` limit is reached (default: \"Maximum N tags reached.\").",
                "<span>That is the maximum.</span>",
            ),
            (
                "loading",
                "Shown in the popup while a `dataSource` / `src` request is pending (default: \"Loading...\").",
                "<span>Searching&hellip;</span>",
            ),
            (
                "no-results",
                "Shown in the popup when no suggestion matches (default: \"No results found.\").",
                "<span>No matching tags.</span>",
            ),
        ],
        properties=[
            ("value", "string. The token values joined with commas; setting it replaces the tokens (no event)."),
            ("tokens", "{ value, label, avatar, meta }[]. A copy of the tokens; assigning strings or objects replaces them (no event)."),
            ("inputValue", "string. The text in the input; setting it does not open suggestions or fire `mj-input`."),
            (
                "dataSource",
                "{ query(request) } | { fetch({ query, signal }) } | function(request) | null. Suggestion source; takes precedence over `src` and the options. A plain array is not accepted.",
            ),
            ("form", "HTMLFormElement | null (read-only). The owning form."),
            ("validity", "ValidityState (read-only). `valueMissing` while `required` and there are no tokens."),
            ("validationMessage", "string (read-only). The current validation message."),
        ],
        methods=[
            ("focus(options)", "Focuses the text input (the host when the input is disabled)."),
            ("checkValidity() -> boolean", "Runs constraint validation (fires `invalid` when it fails)."),
            ("reportValidity() -> boolean", "Like `checkValidity()` and shows the browser's message."),
        ],
        parts=[
            ("container", "The bordered field (role group)."),
            ("token-list", "Wrapper of the tokens (display: contents)."),
            ("token", "One token pill."),
            ("token-avatar", "Token avatar image or initials (person mode)."),
            ("token-label", "Token text."),
            ("token-remove", "Token remove button."),
            ("input", "The text input (role combobox)."),
            ("max-count", "The limit hint below the field."),
            ("popup", "The suggestion popup."),
            ("listbox", "The suggestion list."),
            ("option", "One suggestion."),
            ("option-avatar", "Suggestion avatar image or initials (person mode)."),
            ("option-label", "Suggestion text (the match is wrapped in `<mark>`)."),
            ("option-meta", "Secondary text of a suggestion."),
            ("loading", "The loading message container."),
            ("no-results", "The no-results / error message container."),
        ],
        css_properties=[
            ("--mj-tag-picker-token-gap", "Gap between tokens and the input (default var(--mj-space-1))."),
            ("--mj-tag-picker-min-height", "Minimum field height (default var(--mj-control-height-md))."),
            ("--mj-tag-picker-border-radius", "Field corner radius (default var(--mj-radius-md))."),
            ("--mj-tag-picker-token-bg", "Token background (default var(--mj-bg-muted))."),
            ("--mj-tag-picker-token-radius", "Token corner radius (default var(--mj-radius-pill))."),
            ("--mj-tag-picker-avatar-size", "Avatar size (default 1.25rem)."),
            ("--mj-tag-picker-popup-max-height", "Suggestion list maximum height (default 16rem)."),
        ],
    ),
    ComponentDoc(
        tag="mj-tree-selector",
        title="Tree Selector",
        group="selection",
        summary=(
            "Collapsible tree with single, multi, tri-state checkbox or no selection, "
            "lazy child loading and form participation."
        ),
        description=(
            "<p><code>&lt;mj-tree-selector&gt;</code> shows hierarchical data &mdash; folders, "
            "categories, permissions, org charts &mdash; as a collapsible ARIA tree. The data comes "
            "from nested <code>&lt;mj-tree-item&gt;</code> children (read as data, re-read when they "
            "change) or from the <code>nodes</code> property.</p>"
            "<p><code>selection</code> chooses the model: <code>single</code> (default), "
            "<code>multi</code> (Ctrl/Cmd+click toggles, Shift+click selects a range), "
            "<code>checkbox</code> (tri-state: a parent is checked, mixed or unchecked according to its "
            "leaves, and is part of the value only when fully checked) or <code>none</code> "
            "(navigation only; clicking a row expands it). Disabled nodes cannot be selected or checked "
            "and do not count towards a parent's state.</p>"
            "<p>Branches marked <code>hasChildren</code> load their children on first expand through "
            "<code>dataSource.getChildren(id)</code>; the <code>loading</code> slot is shown meanwhile. "
            "A lazy branch listed in <code>expanded</code> or a <code>default-expanded</code> id list loads "
            "the same way as soon as it is shown and the <code>dataSource</code> is set. "
            "The tree is form-associated: it submits one <code>name=value</code> entry per selected node "
            "and supports <code>required</code>, form reset and disabled fieldsets.</p>"
            "<p>The <code>value</code> attribute is the <em>initial</em> selection (restored by form "
            "reset); user changes are reported through the <code>value</code> property and "
            "<code>mj-change</code>, not written back to the attribute.</p>"
        ),
        how_to_use=(
            "<p><strong>Declarative:</strong> nest <code>&lt;mj-tree-item&gt;</code> elements. Their "
            "attributes: <code>node-id</code> (stable id; generated when absent), <code>label</code> "
            "(else the item's own text), <code>value</code> (submitted value; default the id), "
            "<code>icon</code> and <code>badge</code> (shown as text), <code>disabled</code>, and "
            "<code>has-children</code> (a lazy branch loaded through <code>dataSource</code>).</p>"
            "<p><strong>Data-driven:</strong> set <code>nodes</code> to "
            "<code>[{ id, label, value?, icon?, badge?, disabled?, children?, hasChildren? }]</code>. "
            "A node without <code>children</code> is a leaf unless <code>hasChildren</code> is true; "
            "<code>children: []</code> is a known-empty branch (it keeps a toggle).</p>"
            "<p><strong>Expansion:</strong> <code>default-expanded</code> (<code>root</code> by default, "
            "<code>all</code>, <code>none</code> or a comma-separated id list) applies until the user "
            "toggles a branch; <code>expanded</code> sets the expanded branches explicitly whenever it "
            "changes. <code>single-expand</code> collapses the siblings of a branch that opens. Calling "
            "<code>preventDefault()</code> on <code>mj-expand</code> keeps a branch closed.</p>"
            "<p><strong>Keyboard:</strong> ArrowUp/ArrowDown move between visible rows, Home/End jump to "
            "the first/last row, ArrowRight expands or moves to the first child, ArrowLeft collapses or "
            "moves to the parent, Space/Enter select (toggle in multi and checkbox mode; expand in "
            "<code>none</code> mode), <code>*</code> expands all siblings, and typing letters jumps to "
            "the next matching label. The tree has a single tab stop (roving tabindex).</p>"
        ),
        example="",
        attributes=[
            AttributeDoc(
                name="selection",
                description="Selection model; an unknown value behaves as `single`. Switching mode clears the selection.",
                kind="enum",
                values=["single", "multi", "checkbox", "none"],
                default="single",
            ),
            AttributeDoc(
                name="value",
                description=(
                    "Initial selection: comma-separated node ids or values (in single mode only the first one "
                    "listed is kept). In checkbox mode a parent id "
                    "checks all its leaves. Restored by form reset; user changes are not written back "
                    "(read the `value` property)."
                ),
                kind="string",
            ),
            AttributeDoc(
                name="default-expanded",
                description=(
                    "Branches open until the user toggles one: `root`, `all`, `none` or comma-separated ids. "
                    "`root` and `all` skip lazy (`hasChildren`) branches; a lazy branch named in an id list "
                    "loads its children through `dataSource`."
                ),
                kind="string",
                values=["root", "all", "none"],
                default="root",
            ),
            AttributeDoc(
                name="expanded",
                description="Comma-separated ids of the expanded branches; overrides `default-expanded` and re-applies whenever it changes. Lazy branches listed here load their children through `dataSource`.",
                kind="string",
            ),
            AttributeDoc(
                name="single-expand",
                description="Opening a branch collapses its siblings.",
                kind="boolean",
            ),
            AttributeDoc(
                name="disabled",
                description="Dims the tree and ignores pointer and keyboard input; no tab stop. A disabled fieldset has the same effect.",
                kind="boolean",
            ),
            AttributeDoc(
                name="required",
                description="The form is invalid while nothing is selected (ignored when `selection` is `none`).",
                kind="boolean",
            ),
            AttributeDoc(
                name="required-message",
                description="Validation message for an empty required tree (default: the localized \"required\" text).",
                kind="string",
            ),
            AttributeDoc(
                name="name",
                description="Form field name; one entry per selected node value is submitted.",
                kind="string",
            ),
            AttributeDoc(
                name="aria-label",
                description="Accessible name of the tree.",
                kind="string",
                default="Tree",
            ),
        ],
        events=[
            (
                "mj-change",
                "The user changed the selection (not fired for `value` changes made in code). A plain `change` event follows.",
                "{ values: string[], selectedNodes: TreeNode[] }",
            ),
            (
                "mj-expand",
                "Cancelable; a branch is about to open (user action). `preventDefault()` keeps it closed.",
                "{ nodeId: string, node: TreeNode }",
            ),
            (
                "mj-collapse",
                "The user closed a branch.",
                "{ nodeId: string, node: TreeNode }",
            ),
            (
                "mj-node-load-start",
                "A lazy branch started loading through `dataSource.getChildren()`.",
                "{ nodeId: string }",
            ),
            (
                "mj-node-load-end",
                "A lazy branch finished loading.",
                "{ nodeId: string, children: TreeNode[] }",
            ),
            (
                "mj-node-error",
                "`getChildren()` rejected; the branch becomes empty.",
                "{ nodeId: string, error: unknown }",
            ),
        ],
        examples=[
            ComponentExample(
                key="basic",
                title="Declarative tree",
                description=(
                    "<p>A file tree written as nested <code>&lt;mj-tree-item&gt;</code> elements with icons, "
                    "a badge and a disabled file. Root branches start open (<code>default-expanded=\"root\"</code>) "
                    "and <code>README.md</code> is preselected through <code>value</code>. Click rows, or focus "
                    "the tree and use the arrow keys; try the <code>selection</code> control.</p>"
                ),
                html=(
                    '<mj-tree-selector id="project-tree" aria-label="Project files" value="readme">\n'
                    '  <mj-tree-item node-id="src" icon="\U0001F4C1" badge="3">src\n'
                    '    <mj-tree-item node-id="components" icon="\U0001F4C1">components\n'
                    '      <mj-tree-item node-id="button" icon="\U0001F4C4">button.js</mj-tree-item>\n'
                    '      <mj-tree-item node-id="input" icon="\U0001F4C4">input.js</mj-tree-item>\n'
                    '    </mj-tree-item>\n'
                    '    <mj-tree-item node-id="index" icon="\U0001F4C4">index.js</mj-tree-item>\n'
                    '    <mj-tree-item node-id="legacy" icon="\U0001F4C4" disabled>legacy.js (read-only)</mj-tree-item>\n'
                    '  </mj-tree-item>\n'
                    '  <mj-tree-item node-id="docs" icon="\U0001F4C1">docs\n'
                    '    <mj-tree-item node-id="guide" icon="\U0001F4C4">guide.md</mj-tree-item>\n'
                    '    <mj-tree-item node-id="changelog" icon="\U0001F4C4">changelog.md</mj-tree-item>\n'
                    '  </mj-tree-item>\n'
                    '  <mj-tree-item node-id="readme" icon="\U0001F4C4">README.md</mj-tree-item>\n'
                    '</mj-tree-selector>'
                ),
                css="#project-tree { max-inline-size: 22rem; }\n",
            ),
            ComponentExample(
                key="multi",
                title="Multi-select from data",
                description=(
                    "<p><code>selection=\"multi\"</code> with nodes set through the <code>nodes</code> property and "
                    "<code>default-expanded=\"all\"</code>. Ctrl/Cmd+click toggles a row, Shift+click selects a "
                    "range; the line below lists <code>selectedNodes</code> after each <code>mj-change</code>.</p>"
                ),
                html=(
                    '<mj-tree-selector id="team-tree" selection="multi" default-expanded="all"\n'
                    '  value="design,qa" aria-label="Teams"></mj-tree-selector>\n'
                    '<p class="demo-status">Selected: <output id="team-output"></output></p>'
                ),
                css=(
                    "#team-tree { max-inline-size: 22rem; }\n"
                    ".demo-status { margin-block: var(--mj-space-3) 0; color: var(--mj-text-muted); }\n"
                ),
                script=(
                    'const tree = document.getElementById("team-tree")\n'
                    'tree.nodes = [\n'
                    '  { id: "eng", label: "Engineering", children: [\n'
                    '    { id: "platform", label: "Platform", badge: "12" },\n'
                    '    { id: "web", label: "Web", badge: "8" },\n'
                    '    { id: "qa", label: "Quality", badge: "5" },\n'
                    '  ] },\n'
                    '  { id: "product", label: "Product", children: [\n'
                    '    { id: "design", label: "Design", badge: "6" },\n'
                    '    { id: "research", label: "Research", badge: "3" },\n'
                    '  ] },\n'
                    '  { id: "sales", label: "Sales", badge: "9" },\n'
                    ']\n'
                    'const output = document.getElementById("team-output")\n'
                    'const show = () => {\n'
                    '  const labels = tree.selectedNodes.map((node) => node.label)\n'
                    '  output.textContent = labels.length > 0 ? labels.join(", ") : "nothing"\n'
                    '}\n'
                    'tree.addEventListener("mj-change", show)\n'
                    'show()\n'
                ),
            ),
            ComponentExample(
                key="checkbox-form",
                title="Checkbox tree in a form",
                description=(
                    "<p>Tri-state <code>selection=\"checkbox\"</code>: <code>value=\"content\"</code> checks every "
                    "leaf of Content, Users shows a mixed state, and the disabled leaf cannot be checked. The tree "
                    "is <code>required</code>: uncheck everything and press Submit to see validation; Reset restores "
                    "the <code>value</code> attribute.</p>"
                ),
                html=(
                    '<form id="permission-form" class="demo-form">\n'
                    '  <mj-tree-selector id="permission-tree" name="permissions" selection="checkbox"\n'
                    '    value="content,users.invite" required aria-label="Permissions"></mj-tree-selector>\n'
                    '  <div class="demo-actions">\n'
                    '    <button type="submit">Submit</button>\n'
                    '    <button type="reset">Reset</button>\n'
                    '  </div>\n'
                    '  <output id="permission-output">Not submitted yet.</output>\n'
                    '</form>'
                ),
                css=(
                    ".demo-form { display: grid; gap: var(--mj-space-3); max-inline-size: 24rem; }\n"
                    ".demo-actions { display: flex; gap: var(--mj-space-2); }\n"
                    "#permission-output { color: var(--mj-text-muted); font-size: var(--mj-font-size-sm); }\n"
                ),
                script=(
                    'const tree = document.getElementById("permission-tree")\n'
                    'tree.nodes = [\n'
                    '  { id: "content", label: "Content", children: [\n'
                    '    { id: "articles.read", label: "Read articles" },\n'
                    '    { id: "articles.write", label: "Write articles" },\n'
                    '    { id: "media.upload", label: "Upload media" },\n'
                    '  ] },\n'
                    '  { id: "users", label: "Users", children: [\n'
                    '    { id: "users.invite", label: "Invite users" },\n'
                    '    { id: "users.roles", label: "Change roles" },\n'
                    '    { id: "users.delete", label: "Delete users (owner only)", disabled: true },\n'
                    '  ] },\n'
                    '  { id: "billing", label: "View billing" },\n'
                    ']\n'
                    'const form = document.getElementById("permission-form")\n'
                    'const output = document.getElementById("permission-output")\n'
                    'form.addEventListener("submit", (event) => {\n'
                    '  event.preventDefault()\n'
                    '  const submitted = new FormData(form).getAll("permissions")\n'
                    '  output.textContent = "Submitted: " + submitted.join(", ")\n'
                    '  mjSandbox.log("submit", { permissions: submitted })\n'
                    '})\n'
                    'form.addEventListener("reset", () => { output.textContent = "Reset to the value attribute." })\n'
                ),
            ),
            ComponentExample(
                key="events",
                title="Lazy loading and events",
                description=(
                    "<p>Branches with <code>hasChildren</code> load through <code>dataSource.getChildren()</code> "
                    "(0.8 s delay, <code>loading</code> slot shown). The script opens Europe on start; "
                    "Antarctica fails (<code>mj-node-error</code>) and Archive is vetoed in <code>mj-expand</code>. "
                    "<code>single-expand</code> closes the sibling branch. Watch the Events panel.</p>"
                ),
                html=(
                    '<mj-tree-selector id="region-tree" single-expand default-expanded="none" aria-label="Regions">\n'
                    '  <span slot="loading">Fetching locations…</span>\n'
                    '</mj-tree-selector>'
                ),
                css="#region-tree { max-inline-size: 22rem; }\n",
                script=(
                    'const tree = document.getElementById("region-tree")\n'
                    'const places = {\n'
                    '  europe: [\n'
                    '    { id: "fr", label: "France", hasChildren: true },\n'
                    '    { id: "de", label: "Germany", hasChildren: true },\n'
                    '    { id: "pt", label: "Portugal" },\n'
                    '  ],\n'
                    '  asia: [{ id: "jp", label: "Japan" }, { id: "in", label: "India" }],\n'
                    '  fr: [{ id: "paris", label: "Paris" }, { id: "lyon", label: "Lyon" }],\n'
                    '  de: [{ id: "berlin", label: "Berlin" }, { id: "munich", label: "Munich" }],\n'
                    '}\n'
                    'tree.dataSource = {\n'
                    '  async getChildren(id) {\n'
                    '    await new Promise((resolve) => setTimeout(resolve, 800))\n'
                    '    if (id === "antarctica") {\n'
                    '      throw new Error("Region service unavailable")\n'
                    '    }\n'
                    '    return places[id] || []\n'
                    '  },\n'
                    '}\n'
                    'tree.nodes = [\n'
                    '  { id: "europe", label: "Europe", hasChildren: true },\n'
                    '  { id: "asia", label: "Asia", hasChildren: true },\n'
                    '  { id: "antarctica", label: "Antarctica (fails to load)", hasChildren: true },\n'
                    '  { id: "archive", label: "Archive (locked)", children: [{ id: "y2019", label: "2019" }] },\n'
                    ']\n'
                    'tree.addEventListener("mj-expand", (event) => {\n'
                    '  if (event.detail.nodeId === "archive") {\n'
                    '    event.preventDefault()\n'
                    '    mjSandbox.log("expand vetoed", { nodeId: "archive" })\n'
                    '  }\n'
                    '})\n'
                    'tree.addEventListener("mj-node-error", (event) => {\n'
                    '  mjSandbox.log("load failed", { nodeId: event.detail.nodeId, message: event.detail.error.message })\n'
                    '})\n'
                    '// Demo: open Europe as a user would, through its toggle part.\n'
                    'tree.shadowRoot.querySelector(\'[data-node-id="europe"] [part="item-toggle"]\').click()\n'
                ),
            ),
            ComponentExample(
                key="states",
                title="Empty, disabled and navigation-only",
                description=(
                    "<p>An empty tree shows its <code>empty</code> slot; a <code>disabled</code> tree keeps its "
                    "selection but ignores input; <code>selection=\"none\"</code> is a navigation tree where a "
                    "click or Enter expands the row.</p>"
                ),
                html=(
                    '<mj-tree-selector id="saved-tree" aria-label="Saved searches">\n'
                    '  <span slot="empty">No saved searches yet.</span>\n'
                    '</mj-tree-selector>\n'
                    '<h4>disabled</h4>\n'
                    '<mj-tree-selector disabled value="q3" aria-label="Reports">\n'
                    '  <mj-tree-item node-id="reports">Reports\n'
                    '    <mj-tree-item node-id="q3">Q3 summary</mj-tree-item>\n'
                    '    <mj-tree-item node-id="q4">Q4 forecast</mj-tree-item>\n'
                    '  </mj-tree-item>\n'
                    '</mj-tree-selector>\n'
                    '<h4>selection="none"</h4>\n'
                    '<mj-tree-selector selection="none" default-expanded="none" aria-label="Help topics">\n'
                    '  <mj-tree-item node-id="start">Getting started\n'
                    '    <mj-tree-item node-id="install">Installation</mj-tree-item>\n'
                    '    <mj-tree-item node-id="first-app">Your first app</mj-tree-item>\n'
                    '  </mj-tree-item>\n'
                    '  <mj-tree-item node-id="faq">FAQ</mj-tree-item>\n'
                    '</mj-tree-selector>'
                ),
                css=(
                    "mj-tree-selector { max-inline-size: 22rem; border: 1px solid var(--mj-border); "
                    "border-radius: var(--mj-radius-md); }\n"
                    "h4 { margin-block: var(--mj-space-4) var(--mj-space-2); font-size: var(--mj-font-size-sm); "
                    "color: var(--mj-text-muted); }\n"
                ),
            ),
            ComponentExample(
                key="custom-styling",
                title="Custom styling",
                description=(
                    "<p>Compact rows through the <code>--mj-tree-*</code> custom properties, a tinted selection and "
                    "styled badges via <code>::part(item-badge)</code>.</p>"
                ),
                html=(
                    '<mj-tree-selector id="styled-tree" value="inbox" aria-label="Mail folders">\n'
                    '  <mj-tree-item node-id="mail" icon="✉" badge="42">Mail\n'
                    '    <mj-tree-item node-id="inbox" badge="12">Inbox</mj-tree-item>\n'
                    '    <mj-tree-item node-id="sent">Sent</mj-tree-item>\n'
                    '    <mj-tree-item node-id="archive" badge="30">Archive</mj-tree-item>\n'
                    '  </mj-tree-item>\n'
                    '  <mj-tree-item node-id="spam" icon="⚠">Spam</mj-tree-item>\n'
                    '</mj-tree-selector>'
                ),
                css=(
                    "#styled-tree {\n"
                    "  max-inline-size: 18rem;\n"
                    "  --mj-tree-item-height: 1.6rem;\n"
                    "  --mj-tree-item-indent: 1rem;\n"
                    "  --mj-tree-item-gap: var(--mj-space-1);\n"
                    "  --mj-tree-selected-bg: color-mix(in srgb, var(--mj-accent) 18%, transparent);\n"
                    "  font-size: var(--mj-font-size-sm);\n"
                    "}\n"
                    "#styled-tree::part(item-badge) {\n"
                    "  background: var(--mj-accent);\n"
                    "  color: var(--mj-text-on-accent);\n"
                    "}\n"
                ),
            ),
        ],
        slots=[
            (
                "",
                "`<mj-tree-item>` children: read as the tree data (not projected). Changes are picked up automatically.",
                '<mj-tree-item node-id="sample">Sample folder\n'
                '  <mj-tree-item node-id="sample-a">First file</mj-tree-item>\n'
                '  <mj-tree-item node-id="sample-b">Second file</mj-tree-item>\n'
                '</mj-tree-item>',
            ),
            ("empty", "Shown when the tree has no nodes (default text: No items.).", "<span>Nothing here yet.</span>"),
            (
                "loading",
                "Shown under a lazy branch while `dataSource.getChildren()` runs (default text: Loading…).",
                "<span>Fetching…</span>",
            ),
        ],
        properties=[
            (
                "nodes",
                "TreeNode[]. The tree data `{ id, label, value?, icon?, badge?, disabled?, children?, hasChildren? }`; "
                "assigning replaces `<mj-tree-item>` children as the source. Lazy children are stored on the node objects.",
            ),
            (
                "value",
                "string. Selected node values joined with commas (checkbox mode: every fully checked node). "
                "Setting it (ids or values) selects those nodes without emitting `mj-change`.",
            ),
            ("selectedNodes", "TreeNode[], read-only. The selected (or fully checked) node objects."),
            ("expandedNodeIds", "Set<string>, read-only. A copy of the expanded branch ids."),
            (
                "dataSource",
                "{ getChildren(id): Promise<TreeNode[]> } | null. Loads the children of `hasChildren` branches on first expand.",
            ),
            ("form", "HTMLFormElement | null, read-only. The owning form."),
            ("validity", "ValidityState, read-only. `valueMissing` while required and empty."),
            ("validationMessage", "string, read-only. The current validation message."),
        ],
        methods=[
            ("focus(options?)", "Focuses the row that holds the tab stop (the tree itself when it is empty)."),
            ("checkValidity() -> boolean", "Runs constraint validation; fires `invalid` when it fails."),
            ("reportValidity() -> boolean", "Like `checkValidity()` and shows the browser's message."),
        ],
        parts=[
            ("tree", "The `role=tree` container (holds the rows or the empty state)."),
            ("tree-item", "Wrapper of one node: its row plus its children group."),
            ("item-toggle", "The expand/collapse chevron (hidden on leaves)."),
            ("item-checkbox", "The tri-state check box (checkbox mode only)."),
            ("item-icon", "The node's `icon` text."),
            ("item-label", "The node's label."),
            ("item-badge", "The node's `badge` pill."),
            ("item-children", "The `role=group` container of a branch's children."),
            ("item-loading", "The row shown while a lazy branch loads (holds the `loading` slot)."),
            ("empty", "The empty-state box (holds the `empty` slot)."),
        ],
        css_properties=[
            ("--mj-tree-item-height", "Row height (default 2rem)."),
            ("--mj-tree-item-indent", "Indent per level (default 1.25rem)."),
            ("--mj-tree-item-gap", "Gap between toggle, check box, icon, label and badge (default `--mj-space-2`)."),
            ("--mj-tree-selected-bg", "Background of selected rows (default `--mj-bg-muted`)."),
            ("--mj-tree-toggle-size", "Size of the expand toggle (default 1.25rem)."),
            ("--mj-tree-checkbox-size", "Size of the check box (default 1rem)."),
        ],
    ),
    ComponentDoc(
        tag="mj-transfer-list",
        title="Transfer List",
        group="selection",
        summary=(
            "Two listboxes with move buttons for choosing a subset of items, with filtering, "
            "reordering, a target limit and form participation."
        ),
        description=(
            "<p><code>&lt;mj-transfer-list&gt;</code> shows an available (source) pane and a selected "
            "(target) pane with buttons that move the highlighted items, or all enabled items, between "
            "them. Items come from <code>&lt;mj-option&gt;</code> children (an option with "
            "<code>selected</code> starts in the target; options added, removed or changed later are "
            "picked up without undoing the user's moves) or from the <code>items</code> property.</p>"
            "<p><code>searchable</code> adds a filter field to each pane, <code>reorder</code> adds up/down "
            "buttons for the target order, <code>max-target</code> caps the target, and "
            "<code>orientation=\"vertical\"</code> stacks the panes. Each move first fires a cancelable "
            "<code>mj-move</code>; calling <code>preventDefault()</code> vetoes it. Changing labels, "
            "orientation, <code>searchable</code> or <code>reorder</code> keeps the user's transfers.</p>"
            "<p>The element is form-associated: it submits one <code>name=value</code> entry per target item "
            "in display order, supports <code>required</code>, form reset (back to the initial sides) and "
            "disabled fieldsets. The <code>value</code> attribute is the <em>initial</em> target content; "
            "user moves are reported through the <code>value</code> property and <code>mj-change</code>, "
            "not written back to the attribute.</p>"
        ),
        how_to_use=(
            "<p>Add <code>&lt;mj-option value=\"...\"&gt;Label&lt;/mj-option&gt;</code> children. Option "
            "attributes: <code>value</code> (default: the text), <code>selected</code> (start in the target), "
            "<code>disabled</code> (cannot be selected or moved) and <code>icon</code> (text shown before the "
            "label). Or assign <code>items</code>: strings or "
            "<code>{ value, label?, icon?, disabled?, selected? }</code> objects.</p>"
            "<p>A <code>value</code> attribute (comma-separated, in order) overrides <code>selected</code>. "
            "Read the live state from <code>value</code>, <code>targetItems</code> and "
            "<code>sourceItems</code>. To replace the built-in buttons, put your own in the "
            "<code>controls</code> slot and call <code>moveSelected()</code> / <code>moveAll()</code>.</p>"
            "<p><strong>Mouse:</strong> click selects one item, Ctrl/Cmd+click toggles, Shift+click selects a "
            "range. <strong>Keyboard</strong> (in a pane): ArrowUp/ArrowDown/Home/End move and select, "
            "Shift+Arrow extends, Space/Enter toggle the active item, Ctrl/Cmd+A selects all, "
            "Ctrl/Cmd+ArrowRight (source) and Ctrl/Cmd+ArrowLeft (target) move the selection, and with "
            "<code>reorder</code> Ctrl/Cmd+ArrowUp/ArrowDown move the single selected target item.</p>"
        ),
        example="",
        attributes=[
            AttributeDoc(
                name="source-label",
                description="Heading and accessible name of the source pane.",
                kind="string",
                values=["Available", "Available permissions"],
                default="Available",
            ),
            AttributeDoc(
                name="target-label",
                description="Heading and accessible name of the target pane.",
                kind="string",
                values=["Selected", "Granted permissions"],
                default="Selected",
            ),
            AttributeDoc(
                name="searchable",
                description="Adds a filter field above each pane (matches labels, case-insensitive).",
                kind="boolean",
            ),
            AttributeDoc(
                name="reorder",
                description="Adds move-up / move-down buttons (and Ctrl+ArrowUp/ArrowDown) for one selected target item.",
                kind="boolean",
            ),
            AttributeDoc(
                name="orientation",
                description="`vertical` stacks the panes with the buttons in a row between them.",
                kind="enum",
                values=["horizontal", "vertical"],
                default="horizontal",
            ),
            AttributeDoc(
                name="max-target",
                description="Maximum number of target items; a move that would exceed it is refused whole and the add buttons disable at the limit. Absent or 0 = no limit.",
                kind="number",
            ),
            AttributeDoc(
                name="value",
                description=(
                    "Initial target content: comma-separated values, in order (overrides `selected` options). "
                    "Restored by form reset; moves are not written back (read the `value` property)."
                ),
                kind="string",
            ),
            AttributeDoc(
                name="name",
                description="Form field name; one entry per target item is submitted.",
                kind="string",
            ),
            AttributeDoc(
                name="disabled",
                description="Dims the list and ignores pointer and keyboard input; panes leave the tab order. A disabled fieldset has the same effect.",
                kind="boolean",
            ),
            AttributeDoc(
                name="required",
                description="The form is invalid while the target is empty.",
                kind="boolean",
            ),
            AttributeDoc(
                name="required-message",
                description="Validation message for an empty required target (default: the localized \"required\" text).",
                kind="string",
            ),
            AttributeDoc(
                name="invalid",
                description="Draws the target pane border in the danger colour (set it yourself, e.g. after a failed submit).",
                kind="boolean",
            ),
        ],
        events=[
            (
                "mj-change",
                "Items moved or the target was reordered by the user or by `moveSelected()` / `moveAll()` (not by `value` / `items` assignment). A plain `change` event follows.",
                "{ targetValues: string[], sourceValues: string[] }",
            ),
            (
                "mj-move",
                "Cancelable; fired before items move. `preventDefault()` vetoes the move.",
                "{ items: { value, label, icon, disabled }[], direction: 'to-target' | 'to-source' }",
            ),
            (
                "mj-reorder",
                "A target item moved up or down (`reorder`); followed by `mj-change`.",
                "{ item: { value, label, icon, disabled }, fromIndex: number, toIndex: number }",
            ),
        ],
        examples=[
            ComponentExample(
                key="basic",
                title="Basic usage",
                description=(
                    "<p>Permissions as <code>&lt;mj-option&gt;</code> children with custom pane labels and filter "
                    "fields; Admin starts in the target (<code>selected</code>). Select items and use the arrow "
                    "buttons, or focus a pane and press Ctrl+ArrowRight / Ctrl+ArrowLeft.</p>"
                ),
                html=(
                    '<mj-transfer-list\n'
                    '  source-label="Available permissions"\n'
                    '  target-label="Granted permissions"\n'
                    '  searchable\n'
                    '  style="max-inline-size: 40rem"\n'
                    '>\n'
                    '  <mj-option value="read">Read</mj-option>\n'
                    '  <mj-option value="write">Write</mj-option>\n'
                    '  <mj-option value="delete">Delete</mj-option>\n'
                    '  <mj-option value="admin" selected>Admin</mj-option>\n'
                    '  <mj-option value="audit">Audit log</mj-option>\n'
                    '  <mj-option value="billing" disabled>Billing (owner only)</mj-option>\n'
                    '</mj-transfer-list>'
                ),
            ),
            ComponentExample(
                key="reorder",
                title="Ordered target with a limit",
                description=(
                    "<p>Choose and order up to four table columns: <code>reorder</code> adds up/down buttons "
                    "(or Ctrl+ArrowUp/ArrowDown in the target), <code>max-target=\"4\"</code> disables adding at "
                    "the limit, and <code>value=\"name,email\"</code> sets the initial target and its order. "
                    "Reordering fires <code>mj-reorder</code>.</p>"
                ),
                html=(
                    '<mj-transfer-list id="column-list" reorder max-target="4" value="name,email"\n'
                    '  source-label="Hidden columns" target-label="Visible columns">\n'
                    '  <mj-option value="name">Name</mj-option>\n'
                    '  <mj-option value="email">Email</mj-option>\n'
                    '  <mj-option value="role">Role</mj-option>\n'
                    '  <mj-option value="team">Team</mj-option>\n'
                    '  <mj-option value="created">Created</mj-option>\n'
                    '  <mj-option value="last-login">Last login</mj-option>\n'
                    '</mj-transfer-list>\n'
                    '<p class="demo-status">Column order: <output id="column-output">name,email</output></p>'
                ),
                css=(
                    "#column-list { max-inline-size: 40rem; --mj-transfer-list-pane-height: 13rem; }\n"
                    ".demo-status { margin-block: var(--mj-space-3) 0; color: var(--mj-text-muted); }\n"
                ),
                script=(
                    'const list = document.getElementById("column-list")\n'
                    'const output = document.getElementById("column-output")\n'
                    'list.addEventListener("mj-change", () => { output.textContent = list.value || "(none)" })\n'
                ),
            ),
            ComponentExample(
                key="data-driven",
                title="Vertical, from data",
                description=(
                    "<p><code>orientation=\"vertical\"</code> stacks the panes. The items are assigned through the "
                    "<code>items</code> property: objects with <code>icon</code>, <code>disabled</code> (Stocks) and "
                    "<code>selected</code>, and a plain string.</p>"
                ),
                html=(
                    '<mj-transfer-list id="widget-list" orientation="vertical"\n'
                    '  source-label="Available widgets" target-label="On my dashboard"></mj-transfer-list>'
                ),
                css="#widget-list { max-inline-size: 26rem; --mj-transfer-list-pane-height: 9rem; }\n",
                script=(
                    'document.getElementById("widget-list").items = [\n'
                    '  { value: "clock", label: "Clock", icon: "⏰" },\n'
                    '  { value: "weather", label: "Weather", icon: "☀", selected: true },\n'
                    '  { value: "news", label: "Headlines", icon: "✉" },\n'
                    '  { value: "stocks", label: "Stocks (unavailable)", icon: "↗", disabled: true },\n'
                    '  { value: "calendar", label: "Calendar", icon: "☰", selected: true },\n'
                    '  "Notes",\n'
                    ']\n'
                ),
            ),
            ComponentExample(
                key="form",
                title="Form participation",
                description=(
                    "<p>Inside a form with <code>name=\"scopes\"</code> and <code>required</code>: move everything "
                    "back and press Save to see validation (the script sets <code>invalid</code> to show the error "
                    "border). Save lists the submitted entries; Reset returns every item to its initial side.</p>"
                ),
                html=(
                    '<form id="scope-form" class="demo-form">\n'
                    '  <mj-transfer-list id="scope-list" name="scopes" required\n'
                    '    required-message="Grant at least one scope."\n'
                    '    source-label="Available scopes" target-label="Granted scopes">\n'
                    '    <mj-option value="repo:read" selected>Read repositories</mj-option>\n'
                    '    <mj-option value="repo:write">Write repositories</mj-option>\n'
                    '    <mj-option value="issues">Issues</mj-option>\n'
                    '    <mj-option value="packages">Packages</mj-option>\n'
                    '    <mj-option value="admin:org" disabled>Organisation admin</mj-option>\n'
                    '  </mj-transfer-list>\n'
                    '  <div class="demo-actions">\n'
                    '    <button type="submit">Save</button>\n'
                    '    <button type="reset">Reset</button>\n'
                    '  </div>\n'
                    '  <output id="scope-output">Not submitted yet.</output>\n'
                    '</form>'
                ),
                css=(
                    ".demo-form { display: grid; gap: var(--mj-space-3); max-inline-size: 40rem; }\n"
                    ".demo-actions { display: flex; gap: var(--mj-space-2); }\n"
                    "#scope-output { color: var(--mj-text-muted); font-size: var(--mj-font-size-sm); }\n"
                ),
                script=(
                    'const form = document.getElementById("scope-form")\n'
                    'const list = document.getElementById("scope-list")\n'
                    'const output = document.getElementById("scope-output")\n'
                    'list.addEventListener("invalid", () => list.setAttribute("invalid", ""))\n'
                    'list.addEventListener("mj-change", () => list.toggleAttribute("invalid", !list.checkValidity()))\n'
                    'form.addEventListener("submit", (event) => {\n'
                    '  event.preventDefault()\n'
                    '  const submitted = new FormData(form).getAll("scopes")\n'
                    '  output.textContent = "Submitted: " + submitted.join(", ")\n'
                    '  mjSandbox.log("submit", { scopes: submitted })\n'
                    '})\n'
                    'form.addEventListener("reset", () => {\n'
                    '  list.removeAttribute("invalid")\n'
                    '  output.textContent = "Reset to the initial sides."\n'
                    '})\n'
                ),
            ),
            ComponentExample(
                key="events",
                title="Events and vetoing moves",
                description=(
                    "<p>The script listens for <code>mj-move</code> and vetoes any move of Production into the "
                    "target. On start it calls <code>moveAll(\"to-source\")</code> (allowed: <code>mj-move</code> "
                    "then <code>mj-change</code>) and <code>moveAll(\"to-target\")</code> (vetoed). Move QA by "
                    "hand to see an allowed move.</p>"
                ),
                html=(
                    '<mj-transfer-list id="deploy-list" source-label="Environments" target-label="Deploy to">\n'
                    '  <mj-option value="dev" selected>Development</mj-option>\n'
                    '  <mj-option value="staging" selected>Staging</mj-option>\n'
                    '  <mj-option value="qa">QA</mj-option>\n'
                    '  <mj-option value="prod">Production (needs approval)</mj-option>\n'
                    '</mj-transfer-list>'
                ),
                css="#deploy-list { max-inline-size: 40rem; --mj-transfer-list-pane-height: 10rem; }\n",
                script=(
                    'const list = document.getElementById("deploy-list")\n'
                    'list.addEventListener("mj-move", (event) => {\n'
                    '  const values = event.detail.items.map((item) => item.value)\n'
                    '  if (event.detail.direction === "to-target" && values.includes("prod")) {\n'
                    '    event.preventDefault()\n'
                    '    mjSandbox.log("move vetoed", { values, reason: "production needs approval" })\n'
                    '  }\n'
                    '})\n'
                    'list.moveAll("to-source")\n'
                    'list.moveAll("to-target")\n'
                ),
            ),
            ComponentExample(
                key="slots",
                title="Slots and custom controls",
                description=(
                    "<p>Custom pane headings (<code>source-header</code>, <code>target-header</code>), text buttons "
                    "in the <code>controls</code> slot that call <code>moveSelected()</code> / <code>moveAll()</code>, "
                    "and custom empty messages: everyone starts in the team, so <code>empty-source</code> shows. "
                    "Toggle the slots in the Slots panel.</p>"
                ),
                html=(
                    '<mj-transfer-list id="team-list" value="ana,ben,chloe">\n'
                    '  <strong slot="source-header">Bench</strong>\n'
                    '  <strong slot="target-header">Sprint team</strong>\n'
                    '  <div slot="controls" class="team-controls">\n'
                    '    <button type="button" data-move="selected" data-direction="to-target">Add</button>\n'
                    '    <button type="button" data-move="all" data-direction="to-target">Add all</button>\n'
                    '    <button type="button" data-move="selected" data-direction="to-source">Remove</button>\n'
                    '    <button type="button" data-move="all" data-direction="to-source">Remove all</button>\n'
                    '  </div>\n'
                    '  <span slot="empty-source">Everyone is on the team.</span>\n'
                    '  <span slot="empty-target">Nobody is assigned yet.</span>\n'
                    '  <mj-option value="ana">Ana Lima</mj-option>\n'
                    '  <mj-option value="ben">Ben Okafor</mj-option>\n'
                    '  <mj-option value="chloe">Chloe Martin</mj-option>\n'
                    '</mj-transfer-list>'
                ),
                css=(
                    "#team-list {\n"
                    "  max-inline-size: 44rem;\n"
                    "  --mj-transfer-list-controls-width: 7rem;\n"
                    "  --mj-transfer-list-pane-height: 9rem;\n"
                    "}\n"
                    ".team-controls { display: grid; gap: var(--mj-space-2); }\n"
                ),
                script=(
                    'const list = document.getElementById("team-list")\n'
                    'list.addEventListener("click", (event) => {\n'
                    '  const button = event.target.closest("button[data-move]")\n'
                    '  if (button === null) {\n'
                    '    return\n'
                    '  }\n'
                    '  if (button.dataset.move === "all") {\n'
                    '    list.moveAll(button.dataset.direction)\n'
                    '  } else {\n'
                    '    list.moveSelected(button.dataset.direction)\n'
                    '  }\n'
                    '})\n'
                ),
            ),
        ],
        slots=[
            (
                "",
                "`<mj-option>` children: read as the items (not projected). Options added or removed later are picked up.",
                '<mj-option value="sample-a">Sample item A</mj-option>\n'
                '<mj-option value="sample-b" selected>Sample item B</mj-option>',
            ),
            ("source-header", "Replaces the source pane label (the item count stays).", "<strong>Custom source heading</strong>"),
            ("target-header", "Replaces the target pane label (the item count stays).", "<strong>Custom target heading</strong>"),
            (
                "controls",
                "Replaces the built-in move buttons; wire your own to `moveSelected()` / `moveAll()`.",
                '<div><button type="button">Custom control</button></div>',
            ),
            ("empty-source", "Shown when the source pane has no (matching) items.", "<span>Nothing left to add.</span>"),
            ("empty-target", "Shown when the target pane has no (matching) items.", "<span>Nothing chosen yet.</span>"),
        ],
        properties=[
            (
                "items",
                "TransferItem[]. All items (source, then target). Assigning strings or `{ value, label?, icon?, "
                "disabled?, selected? }` objects replaces the pool and resets both panes (`selected: true` starts in "
                "the target; the `value` attribute, when present, still wins).",
            ),
            ("sourceItems", "{ value, label, icon, disabled }[], read-only. A copy of the source pane, in display order."),
            ("targetItems", "{ value, label, icon, disabled }[], read-only. A copy of the target pane, in display order."),
            ("allItems", "{ value, label, icon, disabled }[], read-only. Source items followed by target items."),
            (
                "value",
                "string. Target values joined with commas. Setting it puts exactly those items in the target, in "
                "that order, without emitting events.",
            ),
            ("form", "HTMLFormElement | null, read-only. The owning form."),
            ("validity", "ValidityState, read-only. `valueMissing` while required and the target is empty."),
            ("validationMessage", "string, read-only. The current validation message."),
        ],
        methods=[
            (
                "moveSelected(direction)",
                "Moves the highlighted items: `\"to-target\"` (default) or `\"to-source\"`. Fires `mj-move` and `mj-change`.",
            ),
            (
                "moveAll(direction)",
                "Moves every enabled item of the other pane: `\"to-target\"` (default) or `\"to-source\"`; refused whole when it would exceed `max-target`.",
            ),
            ("checkValidity() -> boolean", "Runs constraint validation; fires `invalid` when it fails."),
            ("reportValidity() -> boolean", "Like `checkValidity()` and shows the browser's message."),
        ],
        parts=[
            ("container", "The flex row (or column) holding both panes and the controls."),
            ("source-pane", "The source pane box."),
            ("source-header", "Source heading row (label or `source-header` slot, plus the count)."),
            ("source-search", "Source filter row (`searchable`)."),
            ("source-listbox", "The source `role=listbox`."),
            ("empty-source", "Source empty-state box."),
            ("controls", "The button column (or row when vertical)."),
            ("move-right", "Move selected to the target."),
            ("move-all-right", "Move all to the target."),
            ("move-left", "Move selected to the source."),
            ("move-all-left", "Move all to the source."),
            ("move-up", "Move the selected target item up (`reorder`)."),
            ("move-down", "Move the selected target item down (`reorder`)."),
            ("target-pane", "The target pane box."),
            ("target-header", "Target heading row."),
            ("target-search", "Target filter row (`searchable`)."),
            ("target-listbox", "The target `role=listbox`."),
            ("empty-target", "Target empty-state box."),
        ],
        css_properties=[
            ("--mj-transfer-list-gap", "Gap between panes and controls (default `--mj-space-4`)."),
            ("--mj-transfer-list-pane-min-width", "Minimum pane inline size (default 12rem)."),
            ("--mj-transfer-list-pane-height", "Height of each listbox (default 16rem)."),
            ("--mj-transfer-list-border-radius", "Pane corner radius (default `--mj-radius-md`)."),
            ("--mj-transfer-list-controls-width", "Width of the controls column, or its height when vertical (default 3rem)."),
            ("--mj-transfer-list-controls-gap", "Gap between the move buttons (default `--mj-space-2`)."),
        ],
    ),
]
