"""
    feedback.py

    Catalog entries for the 'Feedback' component group.

    Each entry in COMPONENTS describes and demonstrates one feedback
    component: alert, toast, progress, badge, chip, and tooltip.
"""

from testcomponents.catalog.componentdoc import ComponentDoc


COMPONENTS = [
    ComponentDoc(
        tag="mj-alert",
        title="Alert",
        group="feedback",
        summary="Contextual inline, banner, or callout feedback message.",
        description=(
            "<p><code>&lt;mj-alert&gt;</code> displays a contextual "
            "feedback message in one of four severity levels &mdash; "
            "<code>info</code>, <code>success</code>, <code>warning</code>, "
            "and <code>error</code>. Three placement variants are available: "
            "<code>inline</code> (default, rounded border), "
            "<code>banner</code> (full-width, flush edges), and "
            "<code>callout</code> (left-accent stripe). The component "
            "announces its content to screen readers via an ARIA live region "
            "and can optionally show a dismiss button.</p>"
        ),
        how_to_use=(
            "<p>Place message text between the tags. Use "
            "<code>severity</code> to set the intent and <code>variant</code> "
            "for the visual style. Supply a <code>heading</code> attribute or "
            "the <code>title</code> slot for a bold headline. Add "
            "<code>dismissible</code> to show a close button; listen for "
            "<code>mj-alert-dismiss</code> to veto or react. Use "
            "<code>open</code> / <code>open=\"false\"</code> to show or hide "
            "the alert programmatically.</p>"
        ),
        example=(
            '<mj-alert severity="info">Your session will expire in 5 minutes.</mj-alert>\n'
            '<mj-alert severity="success" heading="Saved!">Your changes have been saved.</mj-alert>\n'
            '<mj-alert severity="warning" dismissible>Low disk space on the primary volume.</mj-alert>\n'
            '<mj-alert severity="error" variant="callout" heading="Upload failed">'
            "The file exceeds the 10 MB limit.</mj-alert>"
        ),
        attributes=[
            ("severity", "info | success | warning | error; drives color, icon, and ARIA role."),
            ("variant", "inline | banner | callout; controls the visual placement style."),
            ("heading", "Optional bold headline rendered above the body slot."),
            ("dismissible", "Boolean; shows a close button that removes the element."),
            ("no-icon", "Boolean; hides the severity icon."),
            ("open", "open | open=\"false\"; controls visibility. Defaults to visible."),
        ],
        events=[
            ("mj-alert-dismiss", "Cancelable; fired when the dismiss button is activated."),
            ("mj-alert-open", "Fired when the alert transitions from hidden to visible."),
            ("mj-alert-close", "Fired when the alert is hidden via the open attribute."),
        ],
    ),
    ComponentDoc(
        tag="mj-toast",
        title="Toast",
        group="feedback",
        summary="Transient non-modal notification with optional auto-dismiss countdown.",
        description=(
            "<p><code>&lt;mj-toast&gt;</code> is a lightweight, self-contained "
            "notification that appears briefly and then disappears. Like "
            "<code>&lt;mj-alert&gt;</code> it supports four severity levels. "
            "Setting <code>auto-dismiss</code> to a millisecond value starts a "
            "countdown timer; a thin progress bar at the bottom of the card "
            "visualises the remaining time. The timer pauses while the pointer "
            "or keyboard focus is inside the toast (WCAG 2.2.1 compliant). "
            "Pressing Escape also dismisses it.</p>"
        ),
        how_to_use=(
            "<p>Add the <code>open</code> attribute to make the toast visible. "
            "Set <code>severity</code> and optionally <code>heading</code>. "
            "Use <code>auto-dismiss</code> with a duration in milliseconds "
            "(minimum 1000) for timed dismissal. Listen for "
            "<code>mj-toast-dismiss</code> &mdash; which is cancelable &mdash; "
            "to react or prevent removal.</p>"
        ),
        example=(
            '<mj-toast open severity="success" heading="File uploaded" auto-dismiss="4000">'
            "report_q4.xlsx was uploaded successfully.</mj-toast>\n"
            '<mj-toast open severity="error">Connection lost. Retrying&hellip;</mj-toast>'
        ),
        attributes=[
            ("open", "Boolean; presence makes the toast visible."),
            ("severity", "info | success | warning | error."),
            ("heading", "Optional bold headline above the body."),
            ("auto-dismiss", "Milliseconds before automatic dismissal; 0 disables."),
            ("no-icon", "Boolean; hides the severity icon."),
        ],
        events=[
            ("mj-toast-open", "Fired when the toast becomes visible."),
            ("mj-toast-dismiss", "Cancelable; fired on dismiss (auto or user). detail.reason: 'auto' | 'user'."),
        ],
    ),
    ComponentDoc(
        tag="mj-progress",
        title="Progress",
        group="feedback",
        summary="Horizontal bar or circular ring progress indicator with indeterminate support.",
        description=(
            "<p><code>&lt;mj-progress&gt;</code> communicates the completion "
            "state of an operation. Two visual variants are available: "
            "<code>bar</code> (default, full-width horizontal track) and "
            "<code>ring</code> (circular SVG). Both support determinate mode "
            "(a numeric <code>value</code> against <code>max</code>) and "
            "indeterminate mode (animated, no known end). Optional label and "
            "value-text slots provide visible annotations and feed "
            "<code>aria-valuetext</code> for screen readers. Animations "
            "respect <code>prefers-reduced-motion</code>.</p>"
        ),
        how_to_use=(
            "<p>Set <code>variant</code> to <code>bar</code> or "
            "<code>ring</code>. For determinate progress set "
            "<code>value</code> (0&ndash;<code>max</code>) and optionally "
            "<code>max</code> (default 100). Add <code>indeterminate</code> "
            "for in-progress states with no known completion percentage. Use "
            "<code>label</code> (or the <code>label</code> slot) and "
            "<code>show-label</code> to display a visible caption; add "
            "<code>show-value</code> to display the numeric value.</p>"
        ),
        example=(
            '<mj-progress value="65" label="Uploading" show-label show-value></mj-progress>\n'
            '<mj-progress indeterminate label="Loading" show-label></mj-progress>\n'
            '<mj-progress variant="ring" value="40" label="Sync" show-label></mj-progress>\n'
            '<mj-progress variant="ring" indeterminate label="Processing" show-label></mj-progress>'
        ),
        attributes=[
            ("variant", "bar | ring; selects the visual shape."),
            ("value", "Current numeric value (0 to max)."),
            ("max", "Maximum value; defaults to 100."),
            ("indeterminate", "Boolean; activates the animated indeterminate state."),
            ("label", "Accessible and visible label text."),
            ("show-label", "Boolean; renders the label text visibly."),
            ("value-text", "Human-readable value string for aria-valuetext."),
            ("show-value", "Boolean; renders the numeric value visibly."),
            ("size", "sm | md | lg; adjusts track height and ring diameter."),
        ],
        events=[
            ("mj-progress-change", "Fired when value or max changes. detail: {value, max, percentage}."),
            ("mj-progress-complete", "Fired when value reaches max."),
        ],
    ),
    ComponentDoc(
        tag="mj-badge",
        title="Badge",
        group="feedback",
        summary="Count, dot, or presence-status indicator overlaid on or beside content.",
        description=(
            "<p><code>&lt;mj-badge&gt;</code> is a small visual indicator "
            "that overlays slotted content or renders inline. Three variants "
            "cover the common use cases: <code>count</code> (a numeric pill, "
            "e.g., notification tally), <code>dot</code> (a colorable dot "
            "without text), and <code>status</code> (an ARIA-labelled "
            "presence dot using the <code>status</code> attribute). The "
            "indicator hides automatically when the count is zero unless "
            "<code>show-zero</code> is set. A <code>pulse</code> animation "
            "highlights newly arrived counts.</p>"
        ),
        how_to_use=(
            "<p>Place the element to badge inside the default slot. "
            "Set <code>variant</code> to <code>count</code>, <code>dot</code>, "
            "or <code>status</code>. For <code>count</code>, set "
            "<code>count</code> and optionally <code>max</code> to cap the "
            "displayed number. For <code>status</code>, set "
            "<code>status</code> to a known key "
            "(<code>online</code>, <code>away</code>, <code>busy</code>, "
            "<code>offline</code>, <code>dnd</code>) or supply a "
            "<code>color</code> override. Always provide a <code>label</code> "
            "for dot and status variants.</p>"
        ),
        example=(
            "<mj-badge count=\"7\">\n"
            "  <button type=\"button\">Inbox</button>\n"
            "</mj-badge>\n"
            "<mj-badge count=\"120\" max=\"99\" pulse>\n"
            "  <button type=\"button\">Notifications</button>\n"
            "</mj-badge>\n"
            "<mj-badge variant=\"status\" status=\"online\">\n"
            "  <img src=\"https://i.pravatar.cc/40\" alt=\"Avatar\" "
            "style=\"width:40px;height:40px;border-radius:50%\">\n"
            "</mj-badge>"
        ),
        attributes=[
            ("variant", "count | dot | status."),
            ("count", "Numeric count value (count variant)."),
            ("max", "Maximum displayed count; overflows as max+. Defaults to 99."),
            ("show-zero", "Boolean; show the badge even when count is 0."),
            ("status", "online | away | busy | offline | dnd (status variant)."),
            ("label", "Accessible label for dot and status variants."),
            ("placement", "top-end | top-start | bottom-end | bottom-start | inline."),
            ("color", "CSS color override for the indicator background."),
            ("pulse", "Boolean; adds a pulsing ring animation."),
        ],
        events=[
            ("mj-badge-show", "Fired when a hidden count badge becomes visible."),
            ("mj-badge-hide", "Fired when a visible count badge becomes hidden."),
            ("mj-badge-overflow", "Fired when the count exceeds max. detail: {count, max, displayCount}."),
        ],
    ),
    ComponentDoc(
        tag="mj-chip",
        title="Chip",
        group="feedback",
        summary="Compact pill for filters, tags, and removable token inputs.",
        description=(
            "<p><code>&lt;mj-chip&gt;</code> is a compact pill-shaped "
            "element used for filters, category tags, and token inputs. "
            "Three interaction modes are available: <code>static</code> "
            "(display only), <code>removable</code> (shows a dismiss "
            "button), and <code>selectable</code> (acts as a checkbox "
            "toggle). Selectable chips expose <code>aria-checked</code> and "
            "emit cancelable selection events, while removable chips emit a "
            "cancelable <code>mj-chip-remove</code> event before the element "
            "removes itself.</p>"
        ),
        how_to_use=(
            "<p>Place the chip label between the tags. Set <code>mode</code> "
            "to the desired interaction style. For selectable chips, set "
            "<code>selected</code> for the initial state and listen for "
            "<code>mj-chip-change</code>. For removable chips, listen for "
            "<code>mj-chip-remove</code>. Use <code>value</code> to attach a "
            "data value to the chip and <code>color</code> for a custom "
            "background. Optionally provide an icon in the "
            "<code>leading-icon</code> slot.</p>"
        ),
        example=(
            '<mj-chip>Python</mj-chip>\n'
            '<mj-chip mode="removable" value="typescript">TypeScript</mj-chip>\n'
            '<mj-chip mode="selectable" selected value="dark-mode">Dark mode</mj-chip>\n'
            '<mj-chip mode="selectable" value="notifications">Notifications</mj-chip>\n'
            '<mj-chip disabled>Disabled</mj-chip>'
        ),
        attributes=[
            ("mode", "static | removable | selectable; controls the interaction behavior."),
            ("selected", "Boolean; on/off state for selectable chips."),
            ("value", "Data value associated with the chip."),
            ("disabled", "Boolean; blocks all interaction."),
            ("size", "sm | md | lg."),
            ("remove-label", "Custom aria-label for the remove button (removable mode)."),
            ("color", "CSS color override for the chip background."),
        ],
        events=[
            ("mj-chip-select", "Cancelable; fired before a selectable chip toggles. detail: {value, selected}."),
            ("mj-chip-change", "Fired after a selectable chip settles. detail: {value, selected}."),
            ("mj-chip-remove", "Cancelable; fired before a removable chip removes itself. detail: {value, labelText}."),
        ],
    ),
    ComponentDoc(
        tag="mj-tooltip",
        title="Tooltip",
        group="feedback",
        summary="Hover/focus-triggered supplemental hint anchored to a trigger element.",
        description=(
            "<p><code>&lt;mj-tooltip&gt;</code> displays a short text hint "
            "near its trigger element on hover or focus. It is fully keyboard "
            "accessible and WCAG 1.4.13 compliant: the popup is hoverable, "
            "dismissible with Escape, and stays visible while pointer or "
            "focus remains inside it. Placement defaults to "
            "<code>top</code> but can be set to any of the eight standard "
            "positions. An optional arrow pointer can be shown or hidden.</p>"
        ),
        how_to_use=(
            "<p>Place the trigger element in the <code>trigger</code> slot. "
            "Supply the hint text via the <code>content</code> attribute or "
            "the default slot. Set <code>placement</code> to control which "
            "side the popup appears on. Adjust <code>show-delay</code> and "
            "<code>hide-delay</code> (milliseconds) to tune responsiveness. "
            "Add <code>disabled</code> to suppress the tooltip entirely. "
            "Use <code>trigger=\"focus\"</code> to restrict activation to "
            "keyboard focus only.</p>"
        ),
        example=(
            '<mj-tooltip content="Copy to clipboard" placement="top">\n'
            '  <button slot="trigger" type="button">Copy</button>\n'
            '</mj-tooltip>\n'
            '<mj-tooltip placement="right" show-delay="200">\n'
            '  <button slot="trigger" type="button">More info</button>\n'
            '  Rich <strong>HTML</strong> tooltip content\n'
            '</mj-tooltip>'
        ),
        attributes=[
            ("content", "Plain-text tooltip content (use default slot for HTML)."),
            ("placement", "top | bottom | start | end | top-start | top-end | bottom-start | bottom-end."),
            ("trigger", "Space-separated list of triggers: hover focus. Defaults to 'hover focus'."),
            ("show-delay", "Milliseconds to wait before showing. Defaults to 300."),
            ("hide-delay", "Milliseconds to wait before hiding. Defaults to 100."),
            ("open", "Boolean; forces the tooltip visible programmatically."),
            ("disabled", "Boolean; suppresses the tooltip entirely."),
            ("arrow", "Set to 'false' to hide the arrow pointer."),
            ("max-width", "Maximum popup width in pixels."),
        ],
        events=[
            ("mj-tooltip-show", "Cancelable; fired before the tooltip appears. detail: {trigger}."),
            ("mj-tooltip-hide", "Cancelable; fired before the tooltip disappears. detail: {trigger}."),
        ],
    ),
]
