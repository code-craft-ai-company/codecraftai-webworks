"""
    text.py

    Catalog entries for the 'Text & Form Controls' component group.

    This module exposes a module-level ``COMPONENTS`` list of ComponentDoc
    instances describing and demonstrating all text-entry, editor, form-
    structure, and form-utility components in the library.
"""

from testcomponents.catalog.componentdoc import ComponentDoc


COMPONENTS = [
    ComponentDoc(
        tag="mj-text-field",
        title="Text Field",
        group="text",
        summary="The foundational single-line text entry control.",
        description=(
            "<p><code>&lt;mj-text-field&gt;</code> wraps a native "
            "<code>&lt;input type=\"text\"&gt;</code> with a label, "
            "help text, inline error message, prefix/suffix slots, "
            "optional clear button, and a live character counter. It "
            "participates in forms via the ElementInternals API and "
            "validates on blur.</p>"
        ),
        how_to_use=(
            "<p>Set <code>label</code> for the visible label and "
            "<code>placeholder</code> for hint text. Use "
            "<code>help-text</code> for supplementary guidance and "
            "<code>error-message</code> to override constraint-validation "
            "messages. Add <code>clearable</code> to show a clear button "
            "when the field has a value. Set <code>maxlength</code> to "
            "enable the character counter. Listen for <code>mj-input</code> "
            "on every keystroke or <code>mj-change</code> on commit.</p>"
        ),
        example=(
            '<mj-text-field\n'
            '  label="Full name"\n'
            '  placeholder="Jane Smith"\n'
            '  help-text="Enter your first and last name."\n'
            '  clearable\n'
            '  maxlength="80">\n'
            '</mj-text-field>'
        ),
        attributes=[
            ("label", "Visible label text."),
            ("placeholder", "Placeholder hint inside the input."),
            ("value", "Current field value."),
            ("help-text", "Supplementary guidance shown below the field."),
            ("error-message", "Override error text shown on invalid state."),
            ("maxlength", "Maximum character count; enables counter."),
            ("minlength", "Minimum character count for validation."),
            ("pattern", "Regex pattern for constraint validation."),
            ("required", "Boolean; marks the field as required."),
            ("disabled", "Boolean; disables the field."),
            ("readonly", "Boolean; makes the field read-only."),
            ("clearable", "Boolean; shows a clear button when value is non-empty."),
            ("autocomplete", "Autocomplete hint (default: on)."),
            ("inputmode", "Virtual keyboard hint, e.g. email, tel."),
            ("variant", "outlined (default) | filled | plain."),
            ("size", "sm | md | lg control sizing."),
        ],
        events=[
            ("mj-input", "Fired on every keystroke with { value }."),
            ("mj-change", "Fired when the value changes on commit with { value }."),
            ("mj-clear", "Fired when the clear button is pressed with { previousValue }."),
            ("mj-invalid", "Fired on validation failure with { validationMessage }."),
        ],
    ),
    ComponentDoc(
        tag="mj-search-input",
        title="Search Input",
        group="text",
        summary="A search field with a leading icon, clear button, and suggestion popup.",
        description=(
            "<p><code>&lt;mj-search-input&gt;</code> is a pill-shaped "
            "search field that wraps an <code>&lt;input type=\"search\"&gt;</code>. "
            "It provides a search icon slot, an auto-hide clear button, "
            "an optional submit button, debounced query-change events, and "
            "a keyboard-navigable ARIA listbox for autocomplete suggestions.</p>"
        ),
        how_to_use=(
            "<p>Set <code>placeholder</code> and optionally <code>label</code> "
            "(used as the accessible <code>role=\"search\"</code> label). "
            "Listen for <code>mj-query-change</code> to fetch suggestions and "
            "assign them to the <code>suggestions</code> property "
            "(array of <code>{ value, label }</code> objects). "
            "Listen for <code>mj-search</code> when the user submits. "
            "Set <code>show-submit-button</code> to show an explicit submit "
            "arrow, and <code>loading</code> while results are fetching.</p>"
        ),
        example=(
            '<mj-search-input\n'
            '  placeholder="Search components&hellip;"\n'
            '  label="Component search"\n'
            '  debounce="300"\n'
            '  min-chars="2">\n'
            '</mj-search-input>'
        ),
        attributes=[
            ("label", "Accessible label for the search landmark."),
            ("placeholder", "Placeholder hint text."),
            ("value", "Current field value."),
            ("help-text", "Guidance shown below the field."),
            ("disabled", "Boolean; disables the field."),
            ("readonly", "Boolean; makes the field read-only."),
            ("required", "Boolean; marks the field as required."),
            ("show-submit-button", "Boolean; shows a submit arrow button."),
            ("no-clear-button", "Boolean; hides the clear button."),
            ("loading", "Boolean; shows a loading indicator in the suggestion popup."),
            ("debounce", "Milliseconds to debounce mj-query-change (default: 300)."),
            ("min-chars", "Minimum characters before mj-query-change fires (default: 1)."),
        ],
        events=[
            ("mj-input", "Fired on every keystroke with { value }."),
            ("mj-query-change", "Debounced; fired when the query meets min-chars with { value }."),
            ("mj-search", "Cancelable; fired on Enter or submit button click with { value }."),
            ("mj-suggestion-select", "Fired when a suggestion is selected with { suggestion }."),
            ("mj-clear", "Fired when the clear button is pressed with { previousValue }."),
        ],
    ),
    ComponentDoc(
        tag="mj-password-field",
        title="Password Field",
        group="text",
        summary="Password entry with show/hide toggle, caps-lock warning, and strength meter.",
        description=(
            "<p><code>&lt;mj-password-field&gt;</code> wraps a native "
            "password input with a visibility-toggle button, an optional "
            "caps-lock hint, and an optional visual strength meter. The "
            "strength score (1&ndash;4) is calculated client-side and "
            "emitted so consumers can display custom feedback. It "
            "participates in forms with full constraint validation support.</p>"
        ),
        how_to_use=(
            "<p>Use <code>new-password</code> or <code>current-password</code> "
            "to set the correct <code>autocomplete</code> hint. Add "
            "<code>show-strength</code> to render the built-in strength bar "
            "and <code>show-caps-hint</code> to display a warning when Caps "
            "Lock is detected. Listen for <code>mj-strength-change</code> "
            "to react to score changes.</p>"
        ),
        example=(
            '<mj-password-field\n'
            '  label="Password"\n'
            '  placeholder="Enter a strong password"\n'
            '  new-password\n'
            '  show-strength\n'
            '  show-caps-hint\n'
            '  minlength="8"\n'
            '  required>\n'
            '</mj-password-field>'
        ),
        attributes=[
            ("label", "Visible label text."),
            ("placeholder", "Placeholder hint text."),
            ("value", "Current field value."),
            ("help-text", "Guidance shown below the field."),
            ("error-message", "Override error text."),
            ("required", "Boolean; marks the field as required."),
            ("disabled", "Boolean; disables the field."),
            ("readonly", "Boolean; makes the field read-only."),
            ("minlength", "Minimum password length."),
            ("maxlength", "Maximum password length."),
            ("visible", "Boolean; toggles plain-text display."),
            ("show-strength", "Boolean; renders the strength meter."),
            ("show-caps-hint", "Boolean; shows a Caps Lock warning."),
            ("new-password", "Boolean; sets autocomplete to new-password."),
            ("current-password", "Boolean; sets autocomplete to current-password."),
            ("size", "sm | md | lg control sizing."),
        ],
        events=[
            ("mj-input", "Fired on every keystroke with { value }."),
            ("mj-change", "Fired on commit with { value }."),
            ("mj-visibility-change", "Fired when show/hide is toggled with { visible }."),
            ("mj-strength-change", "Fired when the strength score changes with { score, label }."),
            ("mj-invalid", "Fired on validation failure with { validationMessage }."),
        ],
    ),
    ComponentDoc(
        tag="mj-typed-field",
        title="Typed Field",
        group="text",
        summary="A text field for email, URL, or telephone inputs with type-appropriate validation.",
        description=(
            "<p><code>&lt;mj-typed-field&gt;</code> is a single-line "
            "text field for semantically typed values: email, URL, or "
            "telephone. It sets the correct <code>type</code>, "
            "<code>inputmode</code>, and <code>autocomplete</code> "
            "automatically, displays a format hint on focus, and provides "
            "friendly type-mismatch validation messages.</p>"
        ),
        how_to_use=(
            "<p>Set <code>type</code> to <code>email</code>, "
            "<code>url</code>, or <code>tel</code>. Add "
            "<code>show-format-hint</code> to display a format example "
            "when the field is focused. Use <code>multiple</code> with "
            "<code>type=\"email\"</code> to accept comma-separated "
            "addresses.</p>"
        ),
        example=(
            '<mj-typed-field\n'
            '  type="email"\n'
            '  label="Email address"\n'
            '  placeholder="you@example.com"\n'
            '  show-format-hint\n'
            '  required>\n'
            '</mj-typed-field>\n'
            '<mj-typed-field\n'
            '  type="tel"\n'
            '  label="Phone number"\n'
            '  placeholder="+1 (555) 000-0000">\n'
            '</mj-typed-field>'
        ),
        attributes=[
            ("type", "email | url | tel — the input type."),
            ("label", "Visible label text."),
            ("placeholder", "Placeholder hint text."),
            ("value", "Current field value."),
            ("help-text", "Guidance shown below the field."),
            ("error-message", "Override error text."),
            ("required", "Boolean; marks the field as required."),
            ("disabled", "Boolean; disables the field."),
            ("readonly", "Boolean; makes the field read-only."),
            ("multiple", "Boolean; allows multiple email addresses (type=email only)."),
            ("maxlength", "Maximum character count."),
            ("minlength", "Minimum character count."),
            ("autocomplete", "Override the derived autocomplete value."),
            ("show-format-hint", "Boolean; shows the format hint on focus."),
            ("format-hint", "Custom format hint text (overrides the built-in default)."),
            ("size", "sm | md | lg control sizing."),
        ],
        events=[
            ("mj-input", "Fired on every keystroke with { value }."),
            ("mj-change", "Fired on commit with { value }."),
            ("mj-invalid", "Fired on validation failure with { validationMessage, validityState }."),
        ],
    ),
    ComponentDoc(
        tag="mj-number-field",
        title="Number Field",
        group="text",
        summary="Numeric input with locale-aware display, spinner buttons, and hold-to-repeat.",
        description=(
            "<p><code>&lt;mj-number-field&gt;</code> is a numeric "
            "spinbutton that formats the displayed value using "
            "<code>Intl.NumberFormat</code> (number, currency, or "
            "percent). Increment/decrement spinner buttons support "
            "hold-to-repeat. Keyboard shortcuts (Arrow keys, "
            "Page Up/Down, Home, End) adjust the value by step multiples. "
            "The raw number is exposed via <code>valueAsNumber</code>.</p>"
        ),
        how_to_use=(
            "<p>Set <code>min</code>, <code>max</code>, and <code>step</code> "
            "to constrain the value. Use <code>format=\"currency\"</code> with "
            "<code>currency-code</code> for monetary fields, or "
            "<code>format=\"percent\"</code> for percentage fields. Add "
            "<code>no-spinner</code> to hide the built-in buttons. "
            "The <code>locale</code> attribute overrides automatic locale "
            "detection.</p>"
        ),
        example=(
            '<mj-number-field\n'
            '  label="Quantity"\n'
            '  min="1"\n'
            '  max="100"\n'
            '  step="1"\n'
            '  value="10"\n'
            '  help-text="Choose between 1 and 100.">\n'
            '</mj-number-field>\n'
            '<mj-number-field\n'
            '  label="Price"\n'
            '  format="currency"\n'
            '  currency-code="USD"\n'
            '  fraction-digits="2"\n'
            '  min="0">\n'
            '</mj-number-field>'
        ),
        attributes=[
            ("label", "Visible label text."),
            ("placeholder", "Placeholder hint text."),
            ("value", "Current value (as a string number)."),
            ("help-text", "Guidance shown below the field."),
            ("error-message", "Override error text."),
            ("min", "Minimum allowed value."),
            ("max", "Maximum allowed value."),
            ("step", "Step size for increment/decrement (default: 1)."),
            ("format", "number | currency | percent display format."),
            ("currency-code", "ISO 4217 currency code used when format=currency."),
            ("fraction-digits", "Fixed number of decimal digits to display."),
            ("locale", "BCP 47 locale tag to override auto-detected locale."),
            ("required", "Boolean; marks the field as required."),
            ("disabled", "Boolean; disables the field."),
            ("readonly", "Boolean; makes the field read-only."),
            ("no-spinner", "Boolean; hides the increment/decrement buttons."),
            ("size", "sm | md | lg control sizing."),
        ],
        events=[
            ("mj-input", "Fired on every keystroke with { value, valueAsNumber }."),
            ("mj-change", "Fired on blur/commit with { value, valueAsNumber }."),
            ("mj-increment", "Fired when the increment button is pressed with { value, valueAsNumber }."),
            ("mj-decrement", "Fired when the decrement button is pressed with { value, valueAsNumber }."),
            ("mj-invalid", "Fired on validation failure with { validationMessage }."),
        ],
    ),
    ComponentDoc(
        tag="mj-textarea",
        title="Textarea",
        group="text",
        summary="Multi-line text entry with optional auto-grow and character/word counter.",
        description=(
            "<p><code>&lt;mj-textarea&gt;</code> wraps a native "
            "<code>&lt;textarea&gt;</code> with a label, help text, "
            "error message, footer slot, and a live counter. When "
            "<code>auto-grow</code> is set the height expands with the "
            "content up to an optional <code>max-rows</code> limit. The "
            "counter displays characters used (against <code>maxlength</code>) "
            "and/or a word count when <code>count-words</code> is set.</p>"
        ),
        how_to_use=(
            "<p>Set <code>rows</code> for the initial height. Add "
            "<code>auto-grow</code> to let the field expand, and pair "
            "<code>min-rows</code>/<code>max-rows</code> to bound it. "
            "Use <code>count-words</code> to track word count. A "
            "<code>footer</code> slot is available inside the border "
            "for inline controls such as formatting buttons.</p>"
        ),
        example=(
            '<mj-textarea\n'
            '  label="Description"\n'
            '  placeholder="Describe your component&hellip;"\n'
            '  rows="4"\n'
            '  auto-grow\n'
            '  maxlength="500"\n'
            '  count-words\n'
            '  help-text="Plain text only.">\n'
            '</mj-textarea>'
        ),
        attributes=[
            ("label", "Visible label text."),
            ("placeholder", "Placeholder hint text."),
            ("value", "Current textarea value."),
            ("help-text", "Guidance shown below the field."),
            ("error-message", "Override error text."),
            ("rows", "Initial visible row count (default: 3)."),
            ("min-rows", "Minimum height in rows when auto-grow is active."),
            ("max-rows", "Maximum height in rows when auto-grow is active."),
            ("auto-grow", "Boolean; height grows with content."),
            ("no-resize", "Boolean; disables the resize handle."),
            ("maxlength", "Maximum character count; enables counter."),
            ("minlength", "Minimum character count for validation."),
            ("count-words", "Boolean; shows a word count in the counter."),
            ("required", "Boolean; marks the field as required."),
            ("disabled", "Boolean; disables the field."),
            ("readonly", "Boolean; makes the field read-only."),
            ("spellcheck", "Set to false to disable browser spell-check."),
            ("autocomplete", "Autocomplete hint (default: on)."),
            ("wrap", "soft | hard line-wrap behaviour."),
            ("size", "sm | md | lg font size variant."),
        ],
        events=[
            ("mj-input", "Fired on every keystroke with { value, charCount, wordCount }."),
            ("mj-change", "Fired on commit with { value, charCount, wordCount }."),
            ("mj-invalid", "Fired on validation failure with { validationMessage }."),
        ],
    ),
    ComponentDoc(
        tag="mj-rich-text-editor",
        title="Rich Text Editor",
        group="text",
        summary="WYSIWYG editor with an accessible toolbar, HTML output, and form participation.",
        description=(
            "<p><code>&lt;mj-rich-text-editor&gt;</code> is a "
            "contenteditable WYSIWYG editor with a grouped toolbar "
            "covering bold, italic, underline, strikethrough, lists, "
            "headings, and blockquote. Pasted HTML is sanitized to an "
            "allow-list of safe tags. The component participates in forms "
            "with its HTML value. A custom <code>sanitizer</code> function "
            "can be injected for stricter control.</p>"
        ),
        how_to_use=(
            "<p>Use <code>placeholder</code> for ghost text when the editor "
            "is empty. Set <code>toolbar=\"full\"</code> (default) or "
            "<code>toolbar=\"inline\"</code> to control toolbar visibility. "
            "Add <code>readonly</code> to hide the toolbar and make the "
            "content non-editable. Listen for <code>mj-change</code> on "
            "blur or <code>mj-input</code> (debounced) for live updates. "
            "Assign the <code>sanitizer</code> property to a custom "
            "function to override HTML filtering.</p>"
        ),
        example=(
            '<mj-rich-text-editor\n'
            '  label="Post body"\n'
            '  placeholder="Write something&hellip;"\n'
            '  help-text="Supports bold, italic, lists, and headings.">\n'
            '</mj-rich-text-editor>'
        ),
        attributes=[
            ("label", "Visible label text."),
            ("placeholder", "Ghost text shown when the editor is empty."),
            ("value", "HTML content (get/set via property)."),
            ("help-text", "Guidance shown below the editor."),
            ("error-message", "Override error text."),
            ("toolbar", "full (default) | inline toolbar mode."),
            ("required", "Boolean; marks the field as required."),
            ("disabled", "Boolean; disables editing."),
            ("readonly", "Boolean; hides the toolbar and locks content."),
            ("max-length", "Maximum plain-text character count for validation."),
        ],
        events=[
            ("mj-input", "Debounced; fired during editing with { html, text }."),
            ("mj-change", "Fired on blur when value changes with { html, text }."),
            ("mj-format", "Fired after a toolbar command with { command, active }."),
            ("mj-invalid", "Fired on validation failure with { validationMessage }."),
        ],
    ),
    ComponentDoc(
        tag="mj-markdown-editor",
        title="Markdown Editor",
        group="text",
        summary="Markdown authoring with Edit, Split, and Preview modes and a formatting toolbar.",
        description=(
            "<p><code>&lt;mj-markdown-editor&gt;</code> is a two-pane "
            "Markdown editor with three view modes: Edit, Split, and "
            "Preview. The toolbar inserts Markdown syntax around selected "
            "text. The built-in renderer converts Markdown to HTML; a "
            "custom <code>renderer</code> function can be injected for "
            "full-featured parsing (e.g. marked.js). A "
            "<code>sanitizer</code> function can also be provided. The "
            "form value is the raw Markdown string.</p>"
        ),
        how_to_use=(
            "<p>Set <code>view</code> to <code>edit</code>, "
            "<code>split</code>, or <code>preview</code> to control the "
            "initial mode. Add <code>count-words</code> to show word "
            "statistics in the status bar. Assign the <code>renderer</code> "
            "property to inject a Markdown parsing library. Listen for "
            "<code>mj-view-change</code> when the user switches modes.</p>"
        ),
        example=(
            '<mj-markdown-editor\n'
            '  label="Article content"\n'
            '  placeholder="# Hello world"\n'
            '  view="split"\n'
            '  count-words\n'
            '  maxlength="5000">\n'
            '</mj-markdown-editor>'
        ),
        attributes=[
            ("label", "Visible label text."),
            ("placeholder", "Placeholder in the edit pane."),
            ("value", "Raw Markdown string (get/set via property)."),
            ("help-text", "Guidance shown below the editor."),
            ("error-message", "Override error text."),
            ("view", "edit | split | preview — initial view mode."),
            ("required", "Boolean; marks the field as required."),
            ("disabled", "Boolean; disables editing."),
            ("readonly", "Boolean; forces preview-only mode."),
            ("maxlength", "Maximum character count."),
            ("minlength", "Minimum character count."),
            ("count-words", "Boolean; shows word count in the status bar."),
        ],
        events=[
            ("mj-input", "Fired on every keystroke with { value, wordCount }."),
            ("mj-change", "Fired on commit with { value, wordCount }."),
            ("mj-view-change", "Fired when the view mode changes with { view }."),
            ("mj-invalid", "Fired on validation failure with { validationMessage }."),
        ],
    ),
    ComponentDoc(
        tag="mj-code-editor",
        title="Code Editor",
        group="text",
        summary="Syntax-highlighted code authoring with line numbers, Tab handling, and form participation.",
        description=(
            "<p><code>&lt;mj-code-editor&gt;</code> is a code authoring "
            "component that layers a transparent <code>&lt;textarea&gt;</code> "
            "over a highlight layer. Line numbers are rendered in a gutter. "
            "Tab inserts spaces (or a tab character when "
            "<code>tab-inserts-spaces=\"false\"</code>); Escape exits Tab "
            "trapping. A pluggable <code>highlighter</code> function enables "
            "syntax highlighting via an external library.</p>"
        ),
        how_to_use=(
            "<p>Set <code>language</code> to the token expected by your "
            "highlighter (e.g. <code>javascript</code>). Assign the "
            "<code>highlighter</code> property to a function "
            "<code>(code, lang) =&gt; html</code>. Add "
            "<code>word-wrap</code> to enable soft-wrap. A "
            "<code>toolbar</code> slot is available for custom controls "
            "above the editing area.</p>"
        ),
        example=(
            '<mj-code-editor\n'
            '  label="JavaScript snippet"\n'
            '  language="javascript"\n'
            '  tab-size="2"\n'
            '  line-numbers>\n'
            '</mj-code-editor>'
        ),
        attributes=[
            ("label", "Visible label text."),
            ("placeholder", "Placeholder hint text."),
            ("value", "Current code content (get/set via property)."),
            ("help-text", "Guidance shown below the editor."),
            ("error-message", "Override error text."),
            ("language", "Language identifier passed to the highlighter."),
            ("line-numbers", "Boolean; show line-number gutter (default: true)."),
            ("word-wrap", "Boolean; enable soft line-wrap."),
            ("tab-size", "Number of spaces per Tab (default: 4)."),
            ("tab-inserts-spaces", "Boolean; false inserts a literal tab character."),
            ("required", "Boolean; marks the field as required."),
            ("disabled", "Boolean; disables the editor."),
            ("readonly", "Boolean; makes the editor read-only."),
            ("maxlength", "Maximum character count."),
            ("minlength", "Minimum character count."),
            ("size", "sm | md | lg font size variant."),
        ],
        events=[
            ("mj-input", "Fired on every change with { value, lineCount }."),
            ("mj-change", "Fired on commit with { value, lineCount }."),
            ("mj-invalid", "Fired on validation failure with { validationMessage }."),
        ],
    ),
    ComponentDoc(
        tag="mj-inline-edit",
        title="Inline Edit",
        group="text",
        summary="Click-to-edit inline text with explicit Save and Cancel actions.",
        description=(
            "<p><code>&lt;mj-inline-edit&gt;</code> shows a read-only "
            "display value that can be clicked (or activated by an edit "
            "button) to enter an edit mode with an input field and "
            "Save/Cancel buttons. Validation runs at commit time. "
            "A <code>compact</code> mode omits the action buttons; "
            "Enter commits and Escape cancels. The <code>multiline</code> "
            "attribute switches the edit field to a textarea.</p>"
        ),
        how_to_use=(
            "<p>Set <code>value</code> for the initial text. Use "
            "<code>trigger=\"click\"</code> (default) to allow clicking "
            "directly on the displayed text, or rely solely on the edit "
            "button. Listen for the cancelable <code>mj-change</code> "
            "event to persist the new value. Listen for "
            "<code>mj-edit-start</code> to intercept and cancel entering "
            "edit mode.</p>"
        ),
        example=(
            '<mj-inline-edit\n'
            '  value="Click to edit this title"\n'
            '  label="Title"\n'
            '  trigger="click"\n'
            '  maxlength="100">\n'
            '</mj-inline-edit>'
        ),
        attributes=[
            ("value", "The current text value."),
            ("label", "Accessible label for the edit input."),
            ("trigger", "click — also allow clicking the displayed text to edit."),
            ("multiline", "Boolean; use a textarea instead of a single-line input."),
            ("compact", "Boolean; omit Save/Cancel buttons (Enter/Escape only)."),
            ("required", "Boolean; empty value not permitted on commit."),
            ("maxlength", "Maximum character count."),
            ("minlength", "Minimum character count."),
            ("pattern", "Regex pattern checked on commit."),
            ("disabled", "Boolean; prevents editing."),
            ("readonly", "Boolean; prevents editing."),
            ("error-message", "Custom error text for validation failure."),
            ("edit-label", "Accessible label for the edit trigger button."),
            ("commit-label", "Label for the Save/commit button (default: Save)."),
            ("cancel-label", "Label for the Cancel button (default: Cancel)."),
        ],
        events=[
            ("mj-edit-start", "Cancelable; fired before entering edit mode."),
            ("mj-change", "Cancelable; fired when committing a new value with { value, previousValue }."),
            ("mj-edit-cancel", "Fired when editing is cancelled with { value }."),
            ("mj-invalid", "Fired when commit validation fails with { validationMessage }."),
        ],
    ),
    ComponentDoc(
        tag="mj-masked-input",
        title="Masked Input",
        group="text",
        summary="Pattern-constrained text input with auto-caret advancement and ghost overlay.",
        description=(
            "<p><code>&lt;mj-masked-input&gt;</code> enforces a fixed "
            "input mask defined by a pattern string where "
            "<code>9</code> matches a digit, <code>a</code> matches a "
            "letter, <code>*</code> matches any alphanumeric character, "
            "and any other character is treated as a literal separator. "
            "The caret advances automatically past literals. A "
            "<code>show-mask</code> ghost overlay displays remaining "
            "placeholder characters. Both a formatted value and a raw "
            "value (literals stripped) are exposed.</p>"
        ),
        how_to_use=(
            "<p>Set <code>mask</code> to define the pattern, e.g. "
            "<code>99/99/9999</code> for a date or "
            "<code>(999) 999-9999</code> for a phone number. Add "
            "<code>show-mask</code> to display the ghost overlay. "
            "Listen for <code>mj-complete</code> when all editable "
            "positions are filled. Read <code>rawValue</code> for the "
            "value without literal separators.</p>"
        ),
        example=(
            '<mj-masked-input\n'
            '  label="Date of birth"\n'
            '  mask="99/99/9999"\n'
            '  show-mask\n'
            '  placeholder-char="_"\n'
            '  help-text="MM/DD/YYYY">\n'
            '</mj-masked-input>'
        ),
        attributes=[
            ("mask", "Mask pattern string (9=digit, a=letter, *=alnum, others are literals)."),
            ("label", "Visible label text."),
            ("value", "Current formatted value."),
            ("help-text", "Guidance shown below the field."),
            ("error-message", "Override error text."),
            ("placeholder-char", "Character used for unfilled editable positions (default: _)."),
            ("mode", "eager (default) | lazy — when formatting is applied."),
            ("show-mask", "Boolean; shows the ghost mask overlay."),
            ("required", "Boolean; marks the field as required."),
            ("disabled", "Boolean; disables the field."),
            ("readonly", "Boolean; makes the field read-only."),
            ("inputmode", "Virtual keyboard hint (auto-derived when not set)."),
            ("autocomplete", "Autocomplete hint (default: off)."),
            ("size", "sm | md | lg control sizing."),
        ],
        events=[
            ("mj-input", "Fired on every change with { value, rawValue, complete }."),
            ("mj-complete", "Fired when all editable positions are filled with { value, rawValue }."),
            ("mj-change", "Fired on blur when value changes with { value, rawValue, complete }."),
            ("mj-invalid", "Fired on validation failure with { validationMessage }."),
        ],
    ),
    ComponentDoc(
        tag="mj-token-input",
        title="Token Input",
        group="text",
        summary="Multi-value chip/tag input with optional suggestions and delimiter-based commit.",
        description=(
            "<p><code>&lt;mj-token-input&gt;</code> lets users enter "
            "multiple values as removable chips/tags. Tokens are committed "
            "when the user types a delimiter character (default: comma or "
            "Enter) or presses Tab. Backspace on an empty field selects "
            "then removes the last token. An optional ARIA listbox popup "
            "provides suggestions. A custom <code>validateToken</code> "
            "function can reject individual values.</p>"
        ),
        how_to_use=(
            "<p>Set <code>placeholder</code> for the text input hint. "
            "Use <code>max-tokens</code> to cap the token count. "
            "Assign the <code>suggestions</code> property to an array of "
            "<code>{ value, label }</code> objects to populate the popup. "
            "Listen for <code>mj-query-change</code> to fetch async "
            "suggestions. Use <code>allow-duplicates</code> to permit "
            "repeated values.</p>"
        ),
        example=(
            '<mj-token-input\n'
            '  label="Tags"\n'
            '  placeholder="Add a tag&hellip;"\n'
            '  max-tokens="10"\n'
            '  help-text="Press Enter or comma to add a tag.">\n'
            '</mj-token-input>'
        ),
        attributes=[
            ("label", "Visible label text."),
            ("placeholder", "Placeholder hint for the text input."),
            ("help-text", "Guidance shown below the field."),
            ("error-message", "Override error text."),
            ("delimiters", "Characters that trigger token commit (default: , and newline)."),
            ("max-tokens", "Maximum number of tokens allowed."),
            ("allow-duplicates", "Boolean; permits the same value more than once."),
            ("required", "Boolean; at least one token required."),
            ("disabled", "Boolean; disables the field."),
            ("readonly", "Boolean; makes the field read-only."),
            ("trim", "Boolean; trims whitespace from token values (default: true)."),
            ("loading", "Boolean; shows loading state in the suggestion popup."),
            ("debounce", "Milliseconds to debounce mj-query-change (default: 300)."),
            ("min-chars", "Minimum characters before mj-query-change fires (default: 1)."),
        ],
        events=[
            ("mj-input", "Fired on every keystroke with { value }."),
            ("mj-token-add", "Cancelable; fired before a token is added with { value, tokens }."),
            ("mj-token-remove", "Cancelable; fired before a token is removed with { value, tokens }."),
            ("mj-change", "Fired after the token list changes with { tokens }."),
            ("mj-query-change", "Debounced; fired for async suggestion loading with { value }."),
            ("mj-suggestion-select", "Fired when a suggestion is chosen with { suggestion }."),
            ("mj-invalid", "Fired on validation failure with { validationMessage }."),
        ],
    ),
    ComponentDoc(
        tag="mj-otp-input",
        title="OTP Input",
        group="text",
        summary="Segmented verification-code input with auto-advance and paste-to-fill.",
        description=(
            "<p><code>&lt;mj-otp-input&gt;</code> renders a row of "
            "individual character inputs for one-time passwords or "
            "verification codes. Typing auto-advances the caret to the "
            "next segment. Paste distributes characters across segments "
            "automatically. The form value is the concatenated code "
            "string. An optional separator can be shown between groups "
            "of digits via the <code>group-at</code> attribute and a "
            "<code>separator</code> slot.</p>"
        ),
        how_to_use=(
            "<p>Set <code>length</code> (default: 6) for the number of "
            "segments. Use <code>inputtype=\"alphanumeric\"</code> for "
            "codes with letters. Set <code>group-at</code> to insert a "
            "separator after that many digits (e.g. 3 for XXX&ndash;XXX). "
            "Listen for <code>mj-complete</code> to trigger verification "
            "as soon as all segments are filled.</p>"
        ),
        example=(
            '<mj-otp-input\n'
            '  label="Verification code"\n'
            '  length="6"\n'
            '  inputtype="numeric"\n'
            '  group-at="3"\n'
            '  required>\n'
            '</mj-otp-input>'
        ),
        attributes=[
            ("label", "Visible label and group aria-label."),
            ("help-text", "Guidance shown below the input."),
            ("error-message", "Override error text."),
            ("length", "Number of segments (default: 6)."),
            ("inputtype", "numeric (default) | alphanumeric | password."),
            ("required", "Boolean; all segments must be filled."),
            ("disabled", "Boolean; disables all segments."),
            ("readonly", "Boolean; makes all segments read-only."),
            ("autocomplete", "Autocomplete hint (default: one-time-code)."),
            ("group-at", "Insert a separator before this segment index."),
            ("size", "sm | md | lg segment sizing."),
        ],
        events=[
            ("mj-input", "Fired on every segment change with { value, complete }."),
            ("mj-complete", "Fired once when all segments are filled with { value }."),
            ("mj-change", "Fired when the full code changes with { value }."),
            ("mj-invalid", "Fired on validation failure with { validationMessage }."),
        ],
    ),
    ComponentDoc(
        tag="mj-slider",
        title="Slider",
        group="text",
        summary="Single or dual-thumb range slider with tick marks, value labels, and keyboard support.",
        description=(
            "<p><code>&lt;mj-slider&gt;</code> is a draggable "
            "range-slider control. In single-thumb mode it exposes one "
            "value; in <code>range</code> mode two thumbs define a "
            "start/end interval. Tick marks can be rendered along the "
            "track. The component follows the ARIA slider pattern and "
            "supports full keyboard control (Arrow keys, Page Up/Down, "
            "Home, End).</p>"
        ),
        how_to_use=(
            "<p>Set <code>min</code>, <code>max</code>, and "
            "<code>step</code> to define the domain. Add "
            "<code>range</code> and set <code>value-end</code> to enable "
            "dual-thumb mode. Add <code>ticks</code> to render tick marks "
            "at each step. Add <code>show-value-label</code> to display "
            "the current value above the thumb while dragging. Use the "
            "<code>start-label</code> and <code>end-label</code> slots "
            "for track end labels.</p>"
        ),
        example=(
            '<mj-slider\n'
            '  label="Volume"\n'
            '  min="0"\n'
            '  max="100"\n'
            '  step="5"\n'
            '  value="40"\n'
            '  ticks\n'
            '  show-value-label>\n'
            '  <span slot="start-label">0</span>\n'
            '  <span slot="end-label">100</span>\n'
            '</mj-slider>'
        ),
        attributes=[
            ("label", "Visible label and ARIA label for the thumb(s)."),
            ("help-text", "Guidance shown below the slider."),
            ("error-message", "Override error text."),
            ("value", "Current value of the primary (or only) thumb."),
            ("value-end", "Current value of the second thumb (range mode)."),
            ("min", "Minimum value (default: 0)."),
            ("max", "Maximum value (default: 100)."),
            ("step", "Step size (default: 1)."),
            ("range", "Boolean; enables dual-thumb range selection."),
            ("orientation", "horizontal (default) | vertical."),
            ("disabled", "Boolean; disables the slider."),
            ("readonly", "Boolean; makes the slider read-only."),
            ("required", "Boolean; marks the field as required."),
            ("ticks", "Boolean; renders tick marks at each step."),
            ("show-value-label", "Boolean; shows the value above the active thumb."),
        ],
        events=[
            ("mj-input", "Fired continuously while dragging with { value, valueEnd }."),
            ("mj-change", "Fired on pointer-up or keyboard change with { value, valueEnd }."),
            ("mj-invalid", "Fired on validation failure with { validationMessage }."),
        ],
    ),
    ComponentDoc(
        tag="mj-rating",
        title="Rating",
        group="text",
        summary="Star (or custom icon) rating input using the radiogroup ARIA pattern.",
        description=(
            "<p><code>&lt;mj-rating&gt;</code> renders a row of "
            "star icons that act as a radio group for numeric ratings. "
            "Hover previews highlight stars. The <code>half-steps</code> "
            "attribute enables 0.5-step granularity. A value label can "
            "be shown alongside the stars. The rating can be made "
            "read-only for display purposes. The icon character is "
            "configurable via the <code>icon</code> attribute.</p>"
        ),
        how_to_use=(
            "<p>Set <code>max</code> for the scale size (default: 5) and "
            "<code>value</code> for the initial rating. Add "
            "<code>show-value-label</code> to display the numeric value "
            "beside the stars. Use <code>value-label-format</code> to "
            "customise the label text (e.g. <code>{value} / {max}</code>). "
            "Clicking an already-selected star clears the rating unless "
            "<code>required</code> is set.</p>"
        ),
        example=(
            '<mj-rating\n'
            '  label="Your rating"\n'
            '  max="5"\n'
            '  value="3"\n'
            '  show-value-label\n'
            '  value-label-format="{value} out of {max} stars">\n'
            '</mj-rating>'
        ),
        attributes=[
            ("label", "Visible label and aria-label for the radio group."),
            ("help-text", "Guidance shown below the rating."),
            ("error-message", "Override error text."),
            ("value", "Current rating value (numeric string)."),
            ("max", "Maximum rating (default: 5, capped at 10)."),
            ("required", "Boolean; a non-zero rating is required."),
            ("disabled", "Boolean; disables the rating."),
            ("readonly", "Boolean; display-only mode."),
            ("half-steps", "Boolean; enables 0.5-step granularity."),
            ("show-value-label", "Boolean; shows the numeric value beside the stars."),
            ("value-label-format", "Template string using {value} and {max} placeholders."),
            ("icon", "Icon name used in ARIA labels (default: star)."),
            ("size", "sm | md | lg icon sizing."),
        ],
        events=[
            ("mj-change", "Cancelable; fired when the rating changes with { value, previousValue }."),
            ("mj-hover", "Fired during hover preview with { hoverValue }."),
            ("mj-invalid", "Fired on validation failure with { validationMessage }."),
        ],
    ),
    ComponentDoc(
        tag="mj-captcha",
        title="CAPTCHA",
        group="text",
        summary="Pluggable CAPTCHA integration with provider adapter pattern and form participation.",
        description=(
            "<p><code>&lt;mj-captcha&gt;</code> integrates third-party "
            "CAPTCHA providers (e.g. reCAPTCHA v2/v3, Cloudflare Turnstile) "
            "via a pluggable adapter pattern. The component mounts the "
            "provider widget, manages its token lifecycle (including "
            "auto-expiry), and submits the token as a form value. "
            "Invisible providers intercept form submission and execute "
            "the challenge automatically. A <code>fallback</code> slot "
            "is shown if the SDK fails to load.</p>"
        ),
        how_to_use=(
            "<p>Assign a provider adapter to the "
            "<code>providerAdapter</code> property that implements "
            "<code>{ load, execute, reset, destroy }</code>. Set "
            "<code>provider</code> and <code>site-key</code> when "
            "using the built-in adapter hook. Use "
            "<code>theme=\"auto\"</code> (default) to follow the OS "
            "color scheme. Listen for <code>mj-verified</code> to "
            "receive the token and <code>mj-expired</code> to prompt "
            "re-verification.</p>"
        ),
        example=(
            '<mj-captcha\n'
            '  label="Security verification"\n'
            '  help-text="Complete the check below to continue."\n'
            '  required>\n'
            '  <p slot="fallback">Verification unavailable. Please try again later.</p>\n'
            '</mj-captcha>'
        ),
        attributes=[
            ("label", "Visible label text."),
            ("help-text", "Guidance shown below the widget."),
            ("error-message", "Override error text."),
            ("provider", "Provider identifier, e.g. recaptcha-v2, turnstile."),
            ("site-key", "Public site key for the provider."),
            ("theme", "auto (default) | light | dark — widget theme."),
            ("size", "normal | compact — widget size hint."),
            ("required", "Boolean; form is invalid without a verified token."),
            ("disabled", "Boolean; disables the widget container."),
            ("auto-execute", "Boolean; execute automatically on load (invisible providers)."),
            ("token-expiry", "Seconds before the token is considered expired (default: 120)."),
        ],
        events=[
            ("mj-verified", "Fired when verification succeeds with { token }."),
            ("mj-expired", "Fired when the token expires."),
            ("mj-error", "Fired on provider errors with { code, message }."),
            ("mj-reset", "Fired when the widget is reset."),
            ("mj-invalid", "Fired on form-validation failure with { validationMessage }."),
        ],
    ),
    ComponentDoc(
        tag="mj-form",
        title="Form",
        group="text",
        summary="Form orchestrator that coordinates submission, validation, and reset across all child controls.",
        description=(
            "<p><code>&lt;mj-form&gt;</code> wraps a native "
            "<code>&lt;form&gt;</code> and acts as the authoritative "
            "submission orchestrator for its subtree. On submit it "
            "collects all <code>mj-*</code> form-associated controls, "
            "runs <code>checkValidity()</code> on each, aggregates "
            "errors into a validation summary, and emits a structured "
            "<code>mj-submit</code> event with <code>FormData</code> "
            "and a plain-object value map. A <code>validate</code> mode "
            "controls when re-validation occurs after the first submit.</p>"
        ),
        how_to_use=(
            "<p>Place <code>mj-*</code> controls and native inputs "
            "inside the component. Use <code>action</code> and "
            "<code>method</code> for native form submission. Listen for "
            "<code>mj-submit</code> to handle the data client-side "
            "and set <code>loading</code> while the request is in "
            "flight. Place an <code>&lt;mj-validation-summary&gt;</code> "
            "in the <code>summary</code> slot to display aggregated "
            "errors. Use <code>validate=\"eager\"</code> to re-validate "
            "on blur after the first submit attempt.</p>"
        ),
        example=(
            '<mj-form id="demo-form" validate="eager">\n'
            '  <mj-text-field name="username" label="Username" required></mj-text-field>\n'
            '  <mj-password-field name="password" label="Password" required></mj-password-field>\n'
            '  <mj-button type="submit" variant="primary">Sign in</mj-button>\n'
            '</mj-form>'
        ),
        attributes=[
            ("action", "Form action URL for native submission."),
            ("method", "get | post — HTTP method (default: post)."),
            ("enctype", "Form encoding type."),
            ("novalidate", "Boolean; skips constraint validation on submit."),
            ("validate", "submit (default) | eager | aggressive — re-validation trigger."),
            ("loading", "Boolean; blocks additional submit attempts while true."),
            ("autocomplete", "Autocomplete hint for the form (default: on)."),
        ],
        events=[
            ("mj-submit", "Cancelable; fired on valid submission with { formData, value, valid }."),
            ("mj-invalid", "Fired when the form has invalid controls with { controls, summary }."),
            ("mj-reset", "Cancelable; fired before resetting the form."),
        ],
    ),
    ComponentDoc(
        tag="mj-fieldset",
        title="Fieldset",
        group="text",
        summary="Groups related form controls under a common legend with optional collapsible support.",
        description=(
            "<p><code>&lt;mj-fieldset&gt;</code> maps to a native "
            "<code>&lt;fieldset&gt;</code>/<code>&lt;legend&gt;</code> "
            "pair for group semantics and inherited disabled propagation. "
            "It adds collapsible animation (CSS grid row transition), "
            "required/optional badges, an invalid state, and a "
            "<code>borderless</code> variant. A <code>footer</code> "
            "slot accommodates per-group action rows.</p>"
        ),
        how_to_use=(
            "<p>Set the <code>legend</code> attribute for the group "
            "title. Add <code>collapsible</code> and optionally "
            "<code>open</code> to make the section collapsible. Use "
            "<code>required</code> or <code>optional</code> to show "
            "the corresponding badge in the legend. Set "
            "<code>invalid</code> to apply the danger border. Listen "
            "for the cancelable <code>mj-toggle</code> event to veto "
            "collapse.</p>"
        ),
        example=(
            '<mj-fieldset legend="Personal information" required>\n'
            '  <mj-text-field name="first-name" label="First name" required></mj-text-field>\n'
            '  <mj-text-field name="last-name" label="Last name" required></mj-text-field>\n'
            '</mj-fieldset>\n'
            '<mj-fieldset legend="Optional details" collapsible optional>\n'
            '  <mj-text-field name="bio" label="Bio"></mj-text-field>\n'
            '</mj-fieldset>'
        ),
        attributes=[
            ("legend", "Legend text rendered inside the fieldset."),
            ("disabled", "Boolean; disables all controls inside the fieldset."),
            ("required", "Boolean; shows a required indicator in the legend."),
            ("optional", "Boolean; shows an optional badge in the legend (when not required)."),
            ("invalid", "Boolean; applies an error border."),
            ("collapsible", "Boolean; makes the content collapsible."),
            ("open", "Boolean; the open state when collapsible is set."),
            ("variant", "outlined (default) | borderless."),
            ("name", "Name attribute forwarded to the inner fieldset."),
        ],
        events=[
            ("mj-toggle", "Cancelable; fired before the open state changes with { open }."),
        ],
    ),
    ComponentDoc(
        tag="mj-label",
        title="Label",
        group="text",
        summary="Accessible form label with required/optional indicators and a suffix slot.",
        description=(
            "<p><code>&lt;mj-label&gt;</code> renders a native "
            "<code>&lt;label&gt;</code> element and wires it to a "
            "form control via the <code>for</code> attribute. It "
            "displays optional required (<code>*</code>) or optional "
            "(<code>(optional)</code>) indicator badges. A "
            "<code>suffix</code> slot holds inline help-icon triggers. "
            "The <code>visually-hidden</code> attribute hides the label "
            "visually while keeping it accessible.</p>"
        ),
        how_to_use=(
            "<p>Set <code>for</code> to the <code>id</code> of the "
            "target control. Place the label text in the default slot. "
            "Use <code>required</code> or <code>optional</code> to add "
            "the appropriate badge. Place a help icon button in the "
            "<code>suffix</code> slot if needed. Use "
            "<code>layout=\"inline\"</code> to arrange the label and "
            "its target side-by-side.</p>"
        ),
        example=(
            '<mj-label for="username-field" required>Username</mj-label>\n'
            '<mj-text-field id="username-field" name="username" required></mj-text-field>'
        ),
        attributes=[
            ("for", "ID of the associated form control."),
            ("required", "Boolean; shows the required indicator."),
            ("optional", "Boolean; shows the optional badge (when not required)."),
            ("disabled", "Boolean; applies muted/faded styling."),
            ("layout", "inline — arrange label and control side-by-side."),
            ("visually-hidden", "Boolean; hides the label visually."),
            ("required-label", "Override text for the required indicator (default: *)."),
            ("optional-label", "Override text for the optional badge (default: (optional))."),
        ],
        events=[
            ("mj-click", "Fired when the label is clicked with { control }."),
        ],
    ),
    ComponentDoc(
        tag="mj-help-text",
        title="Help Text",
        group="text",
        summary="Supplementary guidance for a form control, linked via aria-describedby.",
        description=(
            "<p><code>&lt;mj-help-text&gt;</code> displays supplementary "
            "guidance below a form control and automatically manages "
            "<code>aria-describedby</code> on the associated control. "
            "When the component is hidden the id is removed from "
            "<code>aria-describedby</code> so it is not announced. "
            "An <code>icon</code> slot allows a leading informational "
            "icon. The component is entirely passive — it emits no "
            "events.</p>"
        ),
        how_to_use=(
            "<p>Set <code>for</code> to the <code>id</code> of the "
            "target control to wire up <code>aria-describedby</code> "
            "automatically. Place the guidance text in the default slot. "
            "Optionally place an icon element in the <code>icon</code> "
            "slot. Use <code>display=\"inline\"</code> for inline-flex "
            "layout.</p>"
        ),
        example=(
            '<mj-text-field id="email-field" label="Email" name="email"></mj-text-field>\n'
            '<mj-help-text for="email-field">We will never share your email address.</mj-help-text>'
        ),
        attributes=[
            ("for", "ID of the associated form control."),
            ("hidden", "Boolean; hides the element and removes it from aria-describedby."),
            ("disabled", "Boolean; applies muted/faded styling."),
            ("display", "block (default) | inline layout mode."),
        ],
        events=[],
    ),
    ComponentDoc(
        tag="mj-error-message",
        title="Error Message",
        group="text",
        summary="Field-level validation error with assertive live-region announcement.",
        description=(
            "<p><code>&lt;mj-error-message&gt;</code> displays a "
            "field-level validation error and automatically sets "
            "<code>aria-describedby</code> and "
            "<code>aria-invalid=\"true\"</code> on the associated "
            "control when visible. The container uses "
            "<code>role=\"alert\"</code> for assertive announcement. "
            "Live-region updates are debounced at 300&nbsp;ms to avoid "
            "spamming screen readers. The <code>always-render</code> "
            "attribute keeps the element in the DOM but visually hidden "
            "when not visible, preserving layout space.</p>"
        ),
        how_to_use=(
            "<p>Set <code>for</code> to the <code>id</code> of the "
            "target control and toggle <code>visible</code> to show or "
            "hide the error. Place the error text in the default slot or "
            "set the <code>message</code> attribute for scripted updates. "
            "Add an icon element to the <code>icon</code> slot for a "
            "leading error icon. Listen for <code>mj-show</code> and "
            "<code>mj-hide</code> to drive animations.</p>"
        ),
        example=(
            '<mj-text-field id="url-field" label="Website URL" name="url" type="url"></mj-text-field>\n'
            '<mj-error-message for="url-field" id="url-error">Please enter a valid URL.</mj-error-message>'
        ),
        attributes=[
            ("for", "ID of the associated form control."),
            ("visible", "Boolean; shows the error message."),
            ("always-render", "Boolean; keeps the element in the DOM but visually hidden."),
            ("message", "Error text (alternative to slot content, useful for scripted updates)."),
        ],
        events=[
            ("mj-show", "Fired when the error becomes visible with { message }."),
            ("mj-hide", "Fired when the error is hidden."),
        ],
    ),
    ComponentDoc(
        tag="mj-validation-summary",
        title="Validation Summary",
        group="text",
        summary="Aggregates form errors into a keyboard-reachable list with links to invalid controls.",
        description=(
            "<p><code>&lt;mj-validation-summary&gt;</code> collects "
            "field-level validation errors from an associated "
            "<code>&lt;mj-form&gt;</code> and renders them as a "
            "prominent error box. Each item is a link that scrolls "
            "and moves focus to the invalid control. The summary "
            "receives focus automatically on show. When the form "
            "submits successfully the summary is cleared.</p>"
        ),
        how_to_use=(
            "<p>Place <code>&lt;mj-validation-summary&gt;</code> in the "
            "<code>summary</code> slot of <code>&lt;mj-form&gt;</code> "
            "and set <code>for</code> to the form's <code>id</code> to "
            "wire the event listeners automatically. Customise the "
            "heading level with <code>heading-level</code> and the "
            "heading template with <code>heading-text</code> "
            "(use <code>{count}</code> as a placeholder). Set "
            "<code>manual</code> to populate errors programmatically "
            "via the <code>errors</code> property.</p>"
        ),
        example=(
            '<mj-form id="signup-form">\n'
            '  <mj-validation-summary\n'
            '    slot="summary"\n'
            '    for="signup-form"\n'
            '    heading-text="{count} error(s) found">\n'
            '  </mj-validation-summary>\n'
            '  <mj-text-field name="email" label="Email" required></mj-text-field>\n'
            '  <mj-button type="submit" variant="primary">Submit</mj-button>\n'
            '</mj-form>'
        ),
        attributes=[
            ("for", "ID of the associated mj-form element."),
            ("visible", "Boolean; controls visibility (set automatically by the form)."),
            ("always-render", "Boolean; keeps element in DOM when hidden."),
            ("heading-level", "Heading element level for the error count (default: 2)."),
            ("heading-text", "Heading template; use {count} as a placeholder."),
            ("manual", "Boolean; disables automatic form event wiring."),
            ("focus-on-show", "Boolean; focus the summary container when shown (default: true)."),
        ],
        events=[
            ("mj-show", "Fired when the summary becomes visible with { errors, count }."),
            ("mj-hide", "Fired when the summary is cleared."),
            ("mj-error-click", "Fired when an error link is clicked with { controlId, label, message }."),
        ],
    ),
    ComponentDoc(
        tag="mj-character-counter",
        title="Character Counter",
        group="text",
        summary="Live character or word counter for a text input, with threshold announcements.",
        description=(
            "<p><code>&lt;mj-character-counter&gt;</code> attaches to "
            "any text control via the <code>for</code> attribute and "
            "displays the current character (or word) count. When a "
            "<code>max</code> is set the display can show "
            "remaining characters or a <code>used/max</code> fraction. "
            "Color state transitions from normal to warning to error at "
            "configurable thresholds. Polite live-region announcements "
            "fire at the <code>announce-at</code> percentage threshold "
            "and on limit-exceed/recover.</p>"
        ),
        how_to_use=(
            "<p>Set <code>for</code> to the <code>id</code> of the "
            "input and <code>max</code> for the character budget. Use "
            "<code>mode=\"remaining\"</code> (default) to count down, "
            "or <code>mode=\"used\"</code> to count up. Set "
            "<code>format=\"used/max\"</code> for the "
            "<em>12/200</em> style. Use <code>unit=\"words\"</code> "
            "to count words instead. Tune <code>warn-at</code> and "
            "<code>error-at</code> (as usage percentages) to control "
            "color thresholds.</p>"
        ),
        example=(
            '<mj-textarea id="bio-field" label="Bio" maxlength="200" name="bio"></mj-textarea>\n'
            '<mj-character-counter\n'
            '  for="bio-field"\n'
            '  max="200"\n'
            '  mode="remaining"\n'
            '  format="used/max"\n'
            '  warn-at="80"\n'
            '  announce-at="90">\n'
            '</mj-character-counter>'
        ),
        attributes=[
            ("for", "ID of the associated input or textarea."),
            ("max", "Maximum character (or word) count budget."),
            ("mode", "remaining (default) | used — direction of counting."),
            ("unit", "characters (default) | words — what is being counted."),
            ("format", "compact (default) | used/max — display format."),
            ("warn-at", "Usage percentage at which warning color activates."),
            ("error-at", "Usage percentage at which error color activates (default: 100)."),
            ("announce-at", "Usage percentage at which live-region announcements begin (default: 90)."),
            ("announce-interval", "Announce every N remaining units within the announce-at zone (default: 10)."),
            ("disabled", "Boolean; pauses counting."),
        ],
        events=[
            ("mj-count-change", "Fired on every count update with { current, remaining, exceeded, unit }."),
            ("mj-warn", "Fired when the warn-at threshold is first crossed with { current, remaining, threshold }."),
            ("mj-exceed", "Fired when max is exceeded with { current, max }."),
            ("mj-recover", "Fired when the count drops back under max with { current, max }."),
        ],
    ),
]
