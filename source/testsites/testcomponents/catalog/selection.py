"""
    selection.py

    Catalog entries for the 'Selection & Pickers' component group.

    Each ComponentDoc describes one selection or picker component: its tag,
    purpose, key attributes, events, and a live HTML example that exercises
    the component's real attribute names and child elements.
"""

from testcomponents.catalog.componentdoc import ComponentDoc


COMPONENTS = [
    ComponentDoc(
        tag="mj-select",
        title="Select",
        group="selection",
        summary="Single-choice dropdown with rich option content and form participation.",
        description=(
            "<p><code>&lt;mj-select&gt;</code> is a styled, accessible "
            "replacement for the native <code>&lt;select&gt;</code> element. "
            "It renders a trigger button that opens a floating listbox "
            "populated from slotted <code>&lt;mj-option&gt;</code> children. "
            "It participates in HTML forms via ElementInternals and supports "
            "keyboard navigation, typeahead, and option groups.</p>"
        ),
        how_to_use=(
            "<p>Place <code>&lt;mj-option value=\"...\"&gt;</code> children "
            "inside the tag. Set <code>value</code> to pre-select an option "
            "and <code>placeholder</code> for the empty-state label. Use "
            "<code>disabled</code> to block interaction or <code>readonly</code> "
            "to prevent changes. Listen for <code>mj-change</code> to react "
            "to user selections.</p>"
        ),
        example=(
            '<mj-select placeholder="Choose a fruit">\n'
            '  <mj-option value="apple">Apple</mj-option>\n'
            '  <mj-option value="banana">Banana</mj-option>\n'
            '  <mj-option value="cherry">Cherry</mj-option>\n'
            '  <mj-option value="durian" disabled>Durian (unavailable)</mj-option>\n'
            "</mj-select>"
        ),
        attributes=[
            ("value", "Currently selected option value."),
            ("placeholder", "Label shown when no option is selected."),
            ("open", "Boolean; controls popup visibility."),
            ("disabled", "Boolean; blocks all interaction."),
            ("readonly", "Boolean; prevents selection changes."),
            ("invalid", "Boolean; applies danger border styling."),
            ("size", "sm | md | lg control height."),
            ("block", "Boolean; full-width display."),
        ],
        events=[
            ("mj-change", "Fired when the selected value changes; carries value and previousValue."),
            ("mj-open", "Cancelable; fired just before the popup opens."),
            ("mj-close", "Fired when the popup closes."),
        ],
    ),
    ComponentDoc(
        tag="mj-listbox",
        title="Listbox",
        group="selection",
        summary="Always-visible scrollable list with single or multiple selection.",
        description=(
            "<p><code>&lt;mj-listbox&gt;</code> renders a permanently-visible "
            "scrollable list of options. Unlike <code>&lt;mj-select&gt;</code> "
            "there is no trigger button; the list itself is always on the page. "
            "It supports single selection, multi-selection with "
            "Shift/Ctrl&ndash;click range or toggle, keyboard navigation, "
            "typeahead, and form participation.</p>"
        ),
        how_to_use=(
            "<p>Slot <code>&lt;mj-option&gt;</code> children inside the tag. "
            "Add <code>multiple</code> to enable multi-select and "
            "<code>value</code> (comma-separated for multi) to pre-select items. "
            "In multi mode a checkbox mark appears beside each option. "
            "Listen for <code>mj-change</code> to receive the array of "
            "selected values.</p>"
        ),
        example=(
            '<mj-listbox label="Favourite colours" style="width:16rem">\n'
            '  <mj-option value="red">Red</mj-option>\n'
            '  <mj-option value="green">Green</mj-option>\n'
            '  <mj-option value="blue">Blue</mj-option>\n'
            '  <mj-option value="yellow">Yellow</mj-option>\n'
            '  <mj-option value="purple">Purple</mj-option>\n'
            "</mj-listbox>\n\n"
            '<mj-listbox multiple value="red,blue" label="Multi-select" style="width:16rem;margin-top:1rem">\n'
            '  <mj-option value="red">Red</mj-option>\n'
            '  <mj-option value="green">Green</mj-option>\n'
            '  <mj-option value="blue">Blue</mj-option>\n'
            '  <mj-option value="yellow">Yellow</mj-option>\n'
            "</mj-listbox>"
        ),
        attributes=[
            ("value", "Selected value, or comma-separated values when multiple."),
            ("multiple", "Boolean; enables multi-select with checkmarks."),
            ("disabled", "Boolean; blocks all interaction."),
            ("readonly", "Boolean; prevents selection changes."),
            ("required", "Boolean; marks the field as required for form validation."),
            ("invalid", "Boolean; applies danger border styling."),
            ("size", "sm | md | lg option row height."),
            ("label", "Accessible aria-label for the listbox region."),
        ],
        events=[
            ("mj-change", "Fired on selection change; carries values and previousValues arrays."),
            ("mj-option-focus", "Fired when keyboard focus moves to an option."),
        ],
    ),
    ComponentDoc(
        tag="mj-combobox",
        title="Combobox",
        group="selection",
        summary="Filterable input with a popup suggestion list and optional free-text entry.",
        description=(
            "<p><code>&lt;mj-combobox&gt;</code> combines a text input with a "
            "floating listbox. As the user types, the visible options are "
            "filtered to matching entries. It supports a sync option list via "
            "slotted <code>&lt;mj-option&gt;</code> elements, debounced async "
            "filtering via the <code>mj-filter</code> event, free-text mode "
            "for arbitrary values, and a clear button.</p>"
        ),
        how_to_use=(
            "<p>Slot <code>&lt;mj-option&gt;</code> children for the suggestion "
            "list. Set <code>placeholder</code> for the input hint, "
            "<code>clearable</code> to show a clear button, and "
            "<code>free-text</code> to allow values not in the list. "
            "For async sources listen for <code>mj-filter</code> and inject "
            "new options dynamically. Listen for <code>mj-change</code> when "
            "a selection is committed.</p>"
        ),
        example=(
            '<mj-combobox placeholder="Search a country" clearable style="width:18rem">\n'
            '  <mj-option value="au">Australia</mj-option>\n'
            '  <mj-option value="br">Brazil</mj-option>\n'
            '  <mj-option value="ca">Canada</mj-option>\n'
            '  <mj-option value="de">Germany</mj-option>\n'
            '  <mj-option value="jp">Japan</mj-option>\n'
            '  <mj-option value="us">United States</mj-option>\n'
            "</mj-combobox>"
        ),
        attributes=[
            ("value", "Currently committed value."),
            ("placeholder", "Input placeholder text."),
            ("open", "Boolean; controls popup visibility."),
            ("clearable", "Boolean; shows a clear button when a value is present."),
            ("free-text", "Boolean; allows values outside the option list."),
            ("disabled", "Boolean; blocks all interaction."),
            ("readonly", "Boolean; prevents input."),
            ("invalid", "Boolean; applies danger border styling."),
            ("size", "sm | md | lg input height."),
            ("debounce", "Milliseconds to debounce the filter event (default 300)."),
            ("min-chars", "Minimum characters before filtering begins (default 1)."),
            ("block", "Boolean; full-width display."),
        ],
        events=[
            ("mj-change", "Fired when a suggestion is committed; carries value and previousValue."),
            ("mj-input", "Fired on every keystroke; carries inputValue."),
            ("mj-filter", "Fired after debounce; carries query for async data loading."),
            ("mj-clear", "Fired when the clear button is clicked."),
            ("mj-open", "Cancelable; fired just before the popup opens."),
            ("mj-close", "Fired when the popup closes."),
        ],
    ),
    ComponentDoc(
        tag="mj-cascading-select",
        title="Cascading Select",
        group="selection",
        summary="Chain of dependent selects where each level's options depend on the previous choice.",
        description=(
            "<p><code>&lt;mj-cascading-select&gt;</code> renders an ordered "
            "sequence of native select controls. Each level is disabled until "
            "the preceding level is chosen. Options for downstream levels can "
            "be provided statically via the <code>levels</code> property or "
            "loaded asynchronously via a <code>src</code> URL template or "
            "<code>dataSource</code> object set on the level config.</p>"
        ),
        how_to_use=(
            "<p>Set the <code>levels</code> property to an array of "
            "configuration objects: each with a <code>label</code>, optional "
            "static <code>options</code> array (<code>{value, label}</code>), "
            "and optionally a <code>src</code> URL containing "
            "<code>{parentValue}</code> to load options asynchronously. "
            "Listen for <code>mj-change</code> as the user progresses through "
            "levels and <code>mj-complete</code> when all levels are filled.</p>"
        ),
        example=(
            '<mj-cascading-select id="geo-picker"></mj-cascading-select>\n'
            "<script>\n"
            "  document.getElementById('geo-picker').levels = [\n"
            "    { label: 'Continent', options: [\n"
            "      { value: 'americas', label: 'Americas' },\n"
            "      { value: 'europe',   label: 'Europe' },\n"
            "      { value: 'asia',     label: 'Asia' }\n"
            "    ]},\n"
            "    { label: 'Country', options: [] },\n"
            "    { label: 'City',    options: [] }\n"
            "  ];\n"
            "</script>"
        ),
        attributes=[
            ("disabled", "Boolean; disables all levels."),
            ("required", "Boolean; all levels must be selected for form validity."),
            ("orientation", "horizontal (default) | vertical layout for the level controls."),
            ("size", "Passed through to individual level selects."),
        ],
        events=[
            ("mj-change", "Fired on each level change; carries levelIndex, value, and values array."),
            ("mj-complete", "Fired when every level has a non-empty selection; carries values array."),
            ("mj-level-load-start", "Fired when async option loading begins for a level."),
            ("mj-level-load-end", "Fired when async options arrive; carries levelIndex and options."),
            ("mj-level-error", "Fired on a fetch failure; carries levelIndex and error."),
        ],
    ),
    ComponentDoc(
        tag="mj-radio-group",
        title="Radio Group",
        group="selection",
        summary="Mutually exclusive radio button group with roving tabindex and form participation.",
        description=(
            "<p><code>&lt;mj-radio-group&gt;</code> wraps a set of "
            "<code>&lt;mj-radio&gt;</code> children in an ARIA "
            "<code>radiogroup</code> container. Only one option can be "
            "selected at a time. The group exposes <code>value</code> for "
            "form submission and supports a compact button-style variant via "
            "<code>variant=\"button\"</code>.</p>"
        ),
        how_to_use=(
            "<p>Place <code>&lt;mj-radio value=\"...\"&gt;</code> children "
            "inside the tag. Put the group label in a "
            "<code>&lt;span slot=\"label\"&gt;</code>. Set <code>value</code> "
            "to pre-select an option, <code>orientation</code> to "
            "<code>horizontal</code> for a row layout, and "
            "<code>variant=\"button\"</code> for a button-style appearance. "
            "Listen for <code>mj-change</code>.</p>"
        ),
        example=(
            '<mj-radio-group value="monthly">\n'
            '  <span slot="label">Billing cycle</span>\n'
            '  <mj-radio value="monthly">Monthly</mj-radio>\n'
            '  <mj-radio value="quarterly">Quarterly</mj-radio>\n'
            '  <mj-radio value="annual">Annual (save 20%)</mj-radio>\n'
            "</mj-radio-group>\n\n"
            '<mj-radio-group orientation="horizontal" variant="button" value="md" style="margin-top:1rem">\n'
            '  <span slot="label">Size</span>\n'
            '  <mj-radio value="sm">S</mj-radio>\n'
            '  <mj-radio value="md">M</mj-radio>\n'
            '  <mj-radio value="lg">L</mj-radio>\n'
            '  <mj-radio value="xl">XL</mj-radio>\n'
            "</mj-radio-group>"
        ),
        attributes=[
            ("value", "Currently selected radio value."),
            ("disabled", "Boolean; disables the entire group."),
            ("readonly", "Boolean; prevents changes."),
            ("invalid", "Boolean; outlines the group in danger colour."),
            ("orientation", "vertical (default) | horizontal layout."),
            ("variant", "default | button visual style for radio items."),
            ("label", "Accessible aria-label when no slot label is used."),
        ],
        events=[
            ("mj-change", "Fired on selection change; carries value, previousValue, and the radio element."),
        ],
    ),
    ComponentDoc(
        tag="mj-checkbox-group",
        title="Checkbox Group",
        group="selection",
        summary="Labeled group of independent boolean choices with optional select-all and form participation.",
        description=(
            "<p><code>&lt;mj-checkbox-group&gt;</code> wraps a set of "
            "<code>&lt;mj-checkbox&gt;</code> children in an ARIA group. "
            "Any number of options can be checked simultaneously. An optional "
            "<code>select-all</code> checkbox with tri-state (none / some / all) "
            "is rendered automatically when the attribute is present. "
            "The committed value is a comma-separated list of checked "
            "option values.</p>"
        ),
        how_to_use=(
            "<p>Place <code>&lt;mj-checkbox value=\"...\"&gt;</code> children "
            "inside the tag. Add <code>select-all</code> for a master checkbox "
            "and <code>select-all-label</code> to customise its label. "
            "Set <code>value</code> to a comma-separated string to pre-check "
            "items. Listen for <code>mj-change</code> to receive the full "
            "<code>checkedValues</code> array.</p>"
        ),
        example=(
            '<mj-checkbox-group value="email" select-all>\n'
            '  <span slot="label">Notification channels</span>\n'
            '  <mj-checkbox value="email">Email</mj-checkbox>\n'
            '  <mj-checkbox value="sms">SMS</mj-checkbox>\n'
            '  <mj-checkbox value="push">Push notification</mj-checkbox>\n'
            '  <mj-checkbox value="webhook" disabled>Webhook (coming soon)</mj-checkbox>\n'
            "</mj-checkbox-group>"
        ),
        attributes=[
            ("value", "Comma-separated list of currently checked values."),
            ("disabled", "Boolean; disables the entire group."),
            ("readonly", "Boolean; prevents changes."),
            ("invalid", "Boolean; outlines the group in danger colour."),
            ("select-all", "Boolean; shows a master tri-state checkbox."),
            ("select-all-label", "Label for the select-all checkbox (default: 'Select all')."),
            ("orientation", "vertical (default) | horizontal layout."),
            ("label", "Accessible aria-label when no slot label is used."),
        ],
        events=[
            ("mj-change", "Fired on any toggle; carries checkedValues array, changedCheckbox element, and checked boolean."),
            ("mj-select-all", "Fired when the select-all checkbox is toggled; carries checked boolean."),
        ],
    ),
    ComponentDoc(
        tag="mj-segmented-control",
        title="Segmented Control",
        group="selection",
        summary="Compact connected row of segments acting as radio-select, toggles, or an action toolbar.",
        description=(
            "<p><code>&lt;mj-segmented-control&gt;</code> renders a group of "
            "visually connected segments. In <code>mode=\"select\"</code> "
            "(default) it behaves like a radio group: exactly one segment is "
            "active at a time. In <code>mode=\"toggle\"</code> each segment "
            "can be independently pressed or released. In "
            "<code>mode=\"action\"</code> each segment fires an action event "
            "rather than holding state.</p>"
        ),
        how_to_use=(
            "<p>Slot <code>&lt;mj-segment value=\"...\"&gt;</code> children. "
            "Set <code>mode</code> to control the selection behaviour, "
            "<code>value</code> to pre-select segments "
            "(comma-separated for toggle mode), and <code>stretch</code> "
            "to fill the container width. Listen for <code>mj-change</code> "
            "or <code>mj-action</code> depending on the mode.</p>"
        ),
        example=(
            '<mj-segmented-control value="week" label="Calendar view">\n'
            '  <mj-segment value="day">Day</mj-segment>\n'
            '  <mj-segment value="week">Week</mj-segment>\n'
            '  <mj-segment value="month">Month</mj-segment>\n'
            "</mj-segmented-control>\n\n"
            '<mj-segmented-control mode="toggle" value="bold" label="Text formatting" style="margin-top:1rem">\n'
            '  <mj-segment value="bold">Bold</mj-segment>\n'
            '  <mj-segment value="italic">Italic</mj-segment>\n'
            '  <mj-segment value="underline">Underline</mj-segment>\n'
            "</mj-segmented-control>"
        ),
        attributes=[
            ("value", "Selected segment value, or comma-separated values in toggle mode."),
            ("mode", "select (default) | toggle | action."),
            ("disabled", "Boolean; disables all segments."),
            ("stretch", "Boolean; full-width layout."),
            ("size", "sm | md | lg segment height."),
            ("label", "Accessible aria-label for the container."),
        ],
        events=[
            ("mj-change", "Fired in select and toggle modes; carries value, values array, segment element, and selected boolean."),
            ("mj-action", "Fired in action mode when a segment is clicked; carries segment element."),
        ],
    ),
    ComponentDoc(
        tag="mj-split-button",
        title="Split Button",
        group="selection",
        summary="Primary action button paired with a dropdown trigger for alternate actions.",
        description=(
            "<p><code>&lt;mj-split-button&gt;</code> combines a main action "
            "button with a chevron dropdown that opens a menu of related "
            "actions. The primary button fires <code>mj-primary-click</code> "
            "while the dropdown emits <code>mj-menu-select</code> when an "
            "item is chosen. In <code>dynamic</code> mode the primary label "
            "updates to reflect the last selected menu action.</p>"
        ),
        how_to_use=(
            "<p>Set <code>label</code> for the primary button text. Slot "
            "<code>&lt;mj-menu-item value=\"...\"&gt;</code> children for the "
            "dropdown menu. Set <code>variant</code> to "
            "<code>secondary</code> or <code>danger</code> for alternate "
            "colour schemes and <code>dynamic</code> to have the primary "
            "label follow the last-picked menu item.</p>"
        ),
        example=(
            '<mj-split-button label="Save">\n'
            '  <mj-menu-item value="save-draft">Save as draft</mj-menu-item>\n'
            '  <mj-menu-item value="save-template">Save as template</mj-menu-item>\n'
            '  <mj-menu-item value="export">Export&hellip;</mj-menu-item>\n'
            "</mj-split-button>"
        ),
        attributes=[
            ("label", "Primary button label text."),
            ("variant", "primary (default) | secondary | danger colour scheme."),
            ("size", "sm | md | lg control height."),
            ("disabled", "Boolean; disables both the primary button and dropdown."),
            ("primary-disabled", "Boolean; disables only the primary button."),
            ("open", "Boolean; controls dropdown popup visibility."),
            ("dynamic", "Boolean; primary label adopts the last-chosen menu item label."),
            ("dropdown-label", "Accessible label for the dropdown trigger button."),
        ],
        events=[
            ("mj-primary-click", "Fired when the primary button is activated."),
            ("mj-menu-select", "Fired when a dropdown menu item is chosen; carries item element and value."),
            ("mj-open", "Cancelable; fired just before the popup opens."),
            ("mj-close", "Fired when the popup closes."),
        ],
    ),
    ComponentDoc(
        tag="mj-menu-button",
        title="Menu Button",
        group="selection",
        summary="Single trigger button that opens an actions menu (kebab, overflow, meatball).",
        description=(
            "<p><code>&lt;mj-menu-button&gt;</code> is a button that reveals "
            "a popup menu of actions when activated. It is the standard "
            "pattern for kebab / overflow / context menus. Each menu item "
            "can carry a keyboard shortcut hint and a <code>variant=\"danger\"</code> "
            "style for destructive actions. The trigger can be icon-only "
            "(square) or labelled.</p>"
        ),
        how_to_use=(
            "<p>Set <code>label</code> for the trigger's accessible name "
            "(required in icon-only mode). Slot "
            "<code>&lt;mj-menu-item value=\"...\"&gt;</code> children for the "
            "menu. Set <code>icon-only</code> for a square trigger. "
            "Use <code>placement</code> to control popup positioning. "
            "Listen for <code>mj-select</code>.</p>"
        ),
        example=(
            '<mj-menu-button label="Row actions">\n'
            '  <mj-menu-item value="edit">Edit</mj-menu-item>\n'
            '  <mj-menu-item value="duplicate">Duplicate</mj-menu-item>\n'
            '  <mj-menu-item value="archive">Archive</mj-menu-item>\n'
            '  <mj-menu-item value="delete" variant="danger">Delete</mj-menu-item>\n'
            "</mj-menu-button>"
        ),
        attributes=[
            ("label", "Accessible aria-label for the trigger button."),
            ("icon-only", "Boolean; square trigger with hidden text label."),
            ("disabled", "Boolean; disables the trigger."),
            ("open", "Boolean; controls popup visibility."),
            ("placement", "Popup placement string, e.g. bottom-start (default)."),
            ("size", "sm | md | lg trigger height."),
        ],
        events=[
            ("mj-select", "Fired when a menu item is activated; carries item element and value."),
            ("mj-open", "Cancelable; fired just before the popup opens."),
            ("mj-close", "Fired when the popup closes."),
        ],
    ),
    ComponentDoc(
        tag="mj-color-picker",
        title="Color Picker",
        group="selection",
        summary="Rich color chooser with hue/saturation/brightness canvas, sliders, hex input, and swatches.",
        description=(
            "<p><code>&lt;mj-color-picker&gt;</code> is a full-featured "
            "color selection control. Clicking the swatch trigger opens a "
            "floating dialog containing an HSB gradient canvas, a hue "
            "slider, an optional alpha slider, a hex text input, and a "
            "customisable swatch palette. Values are committed as CSS hex "
            "strings. It participates in HTML forms.</p>"
        ),
        how_to_use=(
            "<p>Set <code>value</code> to an initial hex colour such as "
            "<code>#3b82f6</code>. Add <code>no-alpha</code> to hide the "
            "opacity slider. Provide <code>swatches</code> as a JSON array "
            "of hex strings to show a palette row. Listen for "
            "<code>mj-change</code> to receive the new hex value after every "
            "interaction and <code>mj-input</code> for live updates while "
            "dragging.</p>"
        ),
        example=(
            '<mj-color-picker\n'
            '  value="#3b82f6"\n'
            '  swatches=\'["#ef4444","#f97316","#eab308","#22c55e","#3b82f6","#8b5cf6","#ec4899"]\'\n'
            '  no-alpha\n'
            '></mj-color-picker>'
        ),
        attributes=[
            ("value", "Current colour as a CSS hex string (e.g. #3b82f6)."),
            ("open", "Boolean; controls picker popup visibility."),
            ("disabled", "Boolean; blocks interaction."),
            ("invalid", "Boolean; applies danger border styling."),
            ("no-alpha", "Boolean; hides the opacity/alpha slider."),
            ("swatches", "JSON array of hex colour strings to show as quick-pick swatches."),
            ("format", "Output format hint (hex)."),
            ("swatches-only", "Boolean; shows only the swatch palette without the canvas controls."),
        ],
        events=[
            ("mj-change", "Fired when the colour is committed; carries value (hex) and color (HSL object)."),
            ("mj-input", "Fired during live dragging; carries value and color."),
            ("mj-open", "Cancelable; fired just before the picker popup opens."),
            ("mj-close", "Fired when the picker popup closes."),
        ],
    ),
    ComponentDoc(
        tag="mj-date-picker",
        title="Date Picker",
        group="selection",
        summary="Date, time, datetime, or date-range picker with calendar grid and accessible keyboard navigation.",
        description=(
            "<p><code>&lt;mj-date-picker&gt;</code> provides a text field "
            "with a calendar-trigger button. Clicking either opens a floating "
            "dialog containing a monthly grid, previous/next navigation, and "
            "an optional time panel. It supports <code>mode=\"date\"</code> "
            "(default), <code>mode=\"datetime\"</code>, "
            "<code>mode=\"time\"</code>, and <code>mode=\"range\"</code> for "
            "start/end selection. Values are ISO 8601 strings. It participates "
            "in HTML forms.</p>"
        ),
        how_to_use=(
            "<p>Set <code>value</code> to an ISO date string to pre-fill the "
            "field. Use <code>min</code> and <code>max</code> to constrain "
            "the selectable range. Add <code>clearable</code> for a clear "
            "button and <code>mode</code> to switch between date-only, "
            "datetime, or range mode. Listen for <code>mj-change</code> to "
            "receive the new ISO value.</p>"
        ),
        example=(
            '<mj-date-picker\n'
            '  placeholder="Select a date"\n'
            '  clearable\n'
            '  style="width:16rem"\n'
            '></mj-date-picker>\n\n'
            '<mj-date-picker\n'
            '  mode="range"\n'
            '  placeholder="Select date range"\n'
            '  style="width:22rem;margin-top:1rem"\n'
            '></mj-date-picker>'
        ),
        attributes=[
            ("value", "Selected date as an ISO 8601 string (YYYY-MM-DD or start/end for range)."),
            ("mode", "date (default) | datetime | time | range."),
            ("open", "Boolean; controls calendar popup visibility."),
            ("disabled", "Boolean; blocks all interaction."),
            ("readonly", "Boolean; prevents input."),
            ("invalid", "Boolean; applies danger border styling."),
            ("clearable", "Boolean; shows a clear button when a value is present."),
            ("min", "ISO date string; days before this date are disabled."),
            ("max", "ISO date string; days after this date are disabled."),
            ("placeholder", "Input placeholder text."),
            ("block", "Boolean; full-width display."),
        ],
        events=[
            ("mj-change", "Fired on date selection; carries value, date, startDate, and endDate."),
            ("mj-month-change", "Fired when the calendar month is navigated; carries month and year."),
            ("mj-open", "Cancelable; fired just before the calendar opens."),
            ("mj-close", "Fired when the calendar closes."),
        ],
    ),
    ComponentDoc(
        tag="mj-file-picker",
        title="File Picker",
        group="selection",
        summary="Drag-and-drop file input with validation, image previews, and optional auto-upload.",
        description=(
            "<p><code>&lt;mj-file-picker&gt;</code> replaces the native file "
            "input with a styled drop zone. Users can drag files onto the zone "
            "or click the choose-files button. Accepted files are shown in a "
            "list with name, size, optional image preview, and upload progress. "
            "It validates file type, maximum size, and maximum count, and can "
            "automatically POST files to a server URL. It participates in "
            "HTML forms.</p>"
        ),
        how_to_use=(
            "<p>Add <code>multiple</code> to allow more than one file. "
            "Use <code>accept</code> (same syntax as the native "
            "<code>accept</code> attribute) to restrict file types and "
            "<code>max-size</code> (bytes) / <code>max-files</code> to "
            "enforce limits. Set <code>upload-url</code> to trigger "
            "automatic XHR upload with progress tracking. Listen for "
            "<code>mj-change</code> for the current file list and "
            "<code>mj-upload-success</code> / <code>mj-upload-error</code> "
            "for upload outcomes.</p>"
        ),
        example=(
            '<mj-file-picker\n'
            '  accept="image/*"\n'
            '  multiple\n'
            '  max-files="5"\n'
            '  label="Upload images"\n'
            '></mj-file-picker>'
        ),
        attributes=[
            ("multiple", "Boolean; allows selecting more than one file."),
            ("accept", "Accepted file type(s) using MIME type or extension syntax (e.g. image/*, .pdf)."),
            ("max-size", "Maximum file size in bytes; larger files are rejected."),
            ("max-files", "Maximum number of files allowed."),
            ("disabled", "Boolean; blocks interaction."),
            ("required", "Boolean; at least one file required for form validity."),
            ("upload-url", "Server endpoint; files are posted automatically when set."),
            ("variant", "Visual variant for the drop zone."),
            ("label", "Label for the choose-files button (default: 'Choose files')."),
        ],
        events=[
            ("mj-change", "Fired when the file list changes; carries files array."),
            ("mj-file-add", "Cancelable; fired before a file is accepted; carries file."),
            ("mj-file-remove", "Fired when a file is removed; carries file."),
            ("mj-file-error", "Fired when a file fails validation; carries file and error type."),
            ("mj-upload-progress", "Fired during XHR upload; carries file, loaded, total, and percent."),
            ("mj-upload-success", "Fired on successful upload; carries file and response text."),
            ("mj-upload-error", "Fired on upload failure; carries file and error."),
            ("mj-drag-enter", "Fired when a drag enters the drop zone."),
            ("mj-drag-leave", "Fired when a drag leaves the drop zone."),
        ],
    ),
    ComponentDoc(
        tag="mj-asset-picker",
        title="Asset Picker",
        group="selection",
        summary="Searchable, categorized grid picker for emoji, icons, or custom visual assets.",
        description=(
            "<p><code>&lt;mj-asset-picker&gt;</code> is a popup grid chooser "
            "for visual assets such as emoji, icon libraries, or any "
            "author-supplied asset collection. The popup includes a search "
            "input, a category sidebar, and a keyboard-navigable asset grid. "
            "It ships with a built-in emoji dataset and can be fed a custom "
            "collection via the <code>dataSource</code> property. It supports "
            "single and multiple selection and tracks recents in "
            "<code>localStorage</code>.</p>"
        ),
        how_to_use=(
            "<p>Set <code>type</code> to <code>emoji</code> (default) or "
            "provide a custom dataset via the <code>dataSource</code> property. "
            "Add <code>multiple</code> to allow selecting several assets. "
            "Customise <code>columns</code> and <code>cell-size</code> to "
            "control the grid density. Listen for <code>mj-change</code> to "
            "receive the selected asset value(s).</p>"
        ),
        example=(
            '<mj-asset-picker type="emoji"></mj-asset-picker>'
        ),
        attributes=[
            ("value", "Selected asset id, or comma-separated ids in multiple mode."),
            ("open", "Boolean; controls popup visibility."),
            ("disabled", "Boolean; blocks interaction."),
            ("type", "Asset type hint; emoji (default) or a custom string."),
            ("multiple", "Boolean; allows selecting more than one asset."),
            ("columns", "Number of columns in the asset grid (default 8)."),
            ("cell-size", "CSS size for each grid cell (default 2rem)."),
            ("search-placeholder", "Placeholder text for the search input."),
        ],
        events=[
            ("mj-change", "Fired on selection; carries value, asset object, and assets array."),
            ("mj-search", "Fired after a search query; carries query and results."),
            ("mj-open", "Cancelable; fired just before the popup opens."),
            ("mj-close", "Fired when the popup closes."),
        ],
    ),
    ComponentDoc(
        tag="mj-locale-picker",
        title="Locale Picker",
        group="selection",
        summary="Specialised combobox for selecting a language, country, or locale using Intl display names.",
        description=(
            "<p><code>&lt;mj-locale-picker&gt;</code> is a filterable "
            "combobox pre-loaded with language or country data derived from "
            "the browser's <code>Intl</code> APIs. Each option shows the "
            "native name, the display name in the UI language, an optional "
            "country flag emoji, and an optional ISO code. It supports "
            "<code>mode=\"language\"</code>, <code>mode=\"country\"</code>, "
            "and <code>mode=\"locale\"</code>. It participates in HTML forms "
            "and emits the ISO language or country code as its value.</p>"
        ),
        how_to_use=(
            "<p>Set <code>mode</code> to choose the dataset. Restrict the "
            "list with <code>allowed</code> (JSON array of codes) or exclude "
            "entries with <code>excluded</code>. Add <code>clearable</code> "
            "for a clear button. Listen for <code>mj-change</code> to receive "
            "the selected ISO code and the full locale metadata object.</p>"
        ),
        example=(
            '<mj-locale-picker\n'
            '  mode="language"\n'
            '  placeholder="Select a language"\n'
            '  clearable\n'
            '  style="width:20rem"\n'
            '></mj-locale-picker>\n\n'
            '<mj-locale-picker\n'
            '  mode="country"\n'
            '  placeholder="Select a country"\n'
            '  style="width:20rem;margin-top:1rem"\n'
            '></mj-locale-picker>'
        ),
        attributes=[
            ("value", "Selected ISO language or country code."),
            ("mode", "language (default) | country | locale dataset."),
            ("open", "Boolean; controls popup visibility."),
            ("disabled", "Boolean; blocks all interaction."),
            ("invalid", "Boolean; applies danger border styling."),
            ("clearable", "Boolean; shows a clear button when a value is selected."),
            ("placeholder", "Input placeholder text."),
            ("allowed", "JSON array of ISO codes to include (whitelist)."),
            ("excluded", "JSON array of ISO codes to exclude (blacklist)."),
            ("show-flag", "Boolean (default true); shows flag emoji beside options."),
            ("show-native-name", "Boolean (default true); shows the native-language name."),
            ("show-code", "Boolean (default false); shows the ISO code beside option names."),
            ("block", "Boolean; full-width display."),
        ],
        events=[
            ("mj-change", "Fired on selection; carries value, previousValue, and locale metadata object."),
            ("mj-input", "Fired on each keystroke; carries inputValue."),
            ("mj-clear", "Fired when the clear button is clicked."),
            ("mj-open", "Cancelable; fired just before the popup opens."),
            ("mj-close", "Fired when the popup closes."),
        ],
    ),
    ComponentDoc(
        tag="mj-tag-picker",
        title="Tag Picker",
        group="selection",
        summary="Multi-value token input with suggestion popup, free-text entry, and person-avatar support.",
        description=(
            "<p><code>&lt;mj-tag-picker&gt;</code> is a tokenised multi-value "
            "input field. Selected values are displayed as removable pill "
            "tokens inside the input container. As the user types, a suggestion "
            "popup is shown. Suggestions can come from slotted "
            "<code>&lt;mj-option&gt;</code> elements, a <code>src</code> URL "
            "endpoint, or a programmatic <code>dataSource</code> object. "
            "In <code>type=\"person\"</code> mode each token and suggestion "
            "shows an avatar or initials badge.</p>"
        ),
        how_to_use=(
            "<p>Slot <code>&lt;mj-option value=\"...\"&gt;</code> children for "
            "a sync suggestion list, or set <code>src</code> to a search "
            "endpoint. Add <code>free-text</code> to allow arbitrary values "
            "and <code>max-count</code> to cap the number of tokens. "
            "Listen for <code>mj-change</code> to receive the current "
            "<code>tokens</code> and <code>values</code> arrays.</p>"
        ),
        example=(
            '<mj-tag-picker placeholder="Add tags&hellip;">\n'
            '  <mj-option value="design">Design</mj-option>\n'
            '  <mj-option value="engineering">Engineering</mj-option>\n'
            '  <mj-option value="marketing">Marketing</mj-option>\n'
            '  <mj-option value="product">Product</mj-option>\n'
            '  <mj-option value="research">Research</mj-option>\n'
            "</mj-tag-picker>"
        ),
        attributes=[
            ("value", "Comma-separated initial token values."),
            ("placeholder", "Input placeholder text."),
            ("type", "tag (default) | person — enables avatar display in person mode."),
            ("free-text", "Boolean; allows tokens that are not in the suggestion list."),
            ("max-count", "Maximum number of tokens; input is disabled once reached."),
            ("disabled", "Boolean; blocks all interaction."),
            ("readonly", "Boolean; hides remove buttons and prevents input."),
            ("required", "Boolean; at least one token required for form validity."),
            ("src", "URL endpoint for async suggestion fetching; query appended as ?q=."),
            ("debounce", "Milliseconds to debounce suggestion fetching (default 200)."),
            ("min-chars", "Minimum characters before suggestions are fetched (default 1)."),
            ("duplicate-values", "Boolean; allows adding the same value more than once."),
            ("delimiter", "Character that commits a free-text token (default comma)."),
        ],
        events=[
            ("mj-change", "Fired when tokens change; carries tokens array and values array."),
            ("mj-input", "Fired on each keystroke; carries inputValue."),
            ("mj-token-add", "Cancelable; fired before a token is committed; carries token object."),
            ("mj-token-remove", "Fired when a token is removed; carries token object."),
            ("mj-max-count", "Fired when the token limit is reached; carries count."),
            ("mj-open", "Cancelable; fired before the suggestion popup opens."),
            ("mj-close", "Fired when the suggestion popup closes."),
        ],
    ),
    ComponentDoc(
        tag="mj-tree-selector",
        title="Tree Selector",
        group="selection",
        summary="Hierarchical tree with single, multi, or checkbox selection and async child loading.",
        description=(
            "<p><code>&lt;mj-tree-selector&gt;</code> renders a collapsible "
            "tree structure for hierarchical data such as folder trees, "
            "category taxonomies, or org charts. It supports "
            "<code>selection=\"single\"</code>, "
            "<code>selection=\"multi\"</code> (Ctrl/Shift), and "
            "<code>selection=\"checkbox\"</code> with tri-state parent "
            "propagation. Child nodes can be loaded lazily via a "
            "<code>dataSource</code> with a <code>getChildren(id)</code> "
            "method. Light-DOM <code>&lt;mj-tree-item&gt;</code> elements "
            "or a programmatic <code>nodes</code> property feed the tree.</p>"
        ),
        how_to_use=(
            "<p>Set the <code>nodes</code> property to an array of node "
            "objects (<code>{id, label, value, children, hasChildren, "
            "icon, badge}</code>) or slot <code>&lt;mj-tree-item&gt;</code> "
            "children. Set <code>selection</code> to choose the selection "
            "model. Add <code>single-expand</code> to collapse siblings when "
            "a node is opened. Set a <code>dataSource</code> object for "
            "async child loading. Listen for <code>mj-change</code>.</p>"
        ),
        example=(
            '<mj-tree-selector id="file-tree" style="width:18rem"></mj-tree-selector>\n'
            "<script>\n"
            "  document.getElementById('file-tree').nodes = [\n"
            "    { id: 'src',  label: 'src',  value: 'src',  children: [\n"
            "      { id: 'components', label: 'components', value: 'components', children: [\n"
            "        { id: 'button',  label: 'button.js',  value: 'button.js',  children: null },\n"
            "        { id: 'input',   label: 'input.js',   value: 'input.js',   children: null }\n"
            "      ]},\n"
            "      { id: 'index',  label: 'index.js', value: 'index.js', children: null }\n"
            "    ]},\n"
            "    { id: 'tests', label: 'tests', value: 'tests', children: [] }\n"
            "  ];\n"
            "</script>"
        ),
        attributes=[
            ("value", "Comma-separated initially selected node ids."),
            ("selection", "single (default) | multi | checkbox | none."),
            ("disabled", "Boolean; blocks all interaction."),
            ("required", "Boolean; at least one selection required for form validity."),
            ("single-expand", "Boolean; collapses sibling nodes when one is expanded."),
            ("default-expanded", "root (default) — automatically expands root-level branch nodes."),
            ("name", "Form field name used with ElementInternals submission."),
        ],
        events=[
            ("mj-change", "Fired on selection change; carries values array and selectedNodes array."),
            ("mj-expand", "Cancelable; fired when a branch node is about to expand; carries nodeId and node."),
            ("mj-collapse", "Fired when a branch node is collapsed; carries nodeId and node."),
            ("mj-node-load-start", "Fired when async children start loading; carries nodeId."),
            ("mj-node-load-end", "Fired when async children are loaded; carries nodeId and children."),
            ("mj-node-error", "Fired on a child-load failure; carries nodeId and error."),
        ],
    ),
    ComponentDoc(
        tag="mj-transfer-list",
        title="Transfer List",
        group="selection",
        summary="Dual-pane list for moving items between available and selected pools with optional reorder.",
        description=(
            "<p><code>&lt;mj-transfer-list&gt;</code> renders two side-by-side "
            "listboxes &mdash; a source pane and a target pane &mdash; with "
            "arrow buttons to move selected items or all items between them. "
            "Items can be filtered within each pane when <code>searchable</code> "
            "is set, and the target order can be adjusted with up/down buttons "
            "when <code>reorder</code> is set. It participates in HTML forms "
            "with the target pane values as the submission data.</p>"
        ),
        how_to_use=(
            "<p>Slot <code>&lt;mj-option value=\"...\"&gt;</code> children; "
            "add <code>selected</code> to an option to place it in the target "
            "pane initially. Customise pane headings with "
            "<code>source-label</code> / <code>target-label</code>. Add "
            "<code>searchable</code> for filter inputs, <code>reorder</code> "
            "for up/down reorder buttons, and <code>max-target</code> to cap "
            "the target list size. Listen for <code>mj-change</code>.</p>"
        ),
        example=(
            '<mj-transfer-list\n'
            '  source-label="Available permissions"\n'
            '  target-label="Granted permissions"\n'
            '  searchable\n'
            '  style="max-width:40rem"\n'
            '>\n'
            '  <mj-option value="read">Read</mj-option>\n'
            '  <mj-option value="write">Write</mj-option>\n'
            '  <mj-option value="delete">Delete</mj-option>\n'
            '  <mj-option value="admin" selected>Admin</mj-option>\n'
            '  <mj-option value="audit">Audit log</mj-option>\n'
            "</mj-transfer-list>"
        ),
        attributes=[
            ("value", "Comma-separated values currently in the target pane."),
            ("disabled", "Boolean; blocks all interaction."),
            ("required", "Boolean; at least one target item required for form validity."),
            ("searchable", "Boolean; adds filter inputs to both panes."),
            ("reorder", "Boolean; adds up/down reorder buttons for the target pane."),
            ("orientation", "horizontal (default) | vertical pane layout."),
            ("source-label", "Heading for the source pane (default: 'Available')."),
            ("target-label", "Heading for the target pane (default: 'Selected')."),
            ("max-target", "Maximum number of items allowed in the target pane."),
            ("name", "Form field name used with ElementInternals submission."),
        ],
        events=[
            ("mj-change", "Fired when items move; carries targetValues and sourceValues arrays."),
            ("mj-move", "Cancelable; fired before items are moved; carries items array and direction."),
            ("mj-reorder", "Fired when a target item is reordered; carries item, fromIndex, and toIndex."),
        ],
    ),
]
