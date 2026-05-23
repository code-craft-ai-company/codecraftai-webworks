"""
    buttons.py

    Catalog entries for the 'Buttons & Actions' component group.

    This module is the reference example for the per-group catalog files:
    every group module exposes a module-level ``COMPONENTS`` list of
    ComponentDoc instances describing and demonstrating its components.
"""

from testcomponents.catalog.componentdoc import ComponentDoc


COMPONENTS = [
    ComponentDoc(
        tag="mj-button",
        title="Button",
        group="buttons",
        summary="The primary action control in all its variants.",
        description=(
            "<p><code>&lt;mj-button&gt;</code> is the primary action "
            "control of the library. A single component covers every "
            "button role &mdash; primary, secondary, tertiary, link and "
            "icon-only &mdash; selected through the <code>variant</code> "
            "and <code>icon-only</code> attributes. Use it whenever the "
            "user triggers an action: submitting a form, opening a "
            "dialog, or running a command.</p>"
        ),
        how_to_use=(
            "<p>Place text (and optionally an icon in the "
            "<code>icon</code> slot) between the tags. Set "
            "<code>variant</code> to choose the emphasis, <code>size</code> "
            "for <code>sm</code>/<code>lg</code>, and <code>type</code> to "
            "<code>submit</code>/<code>reset</code> to drive an enclosing "
            "form. Add <code>loading</code> to show a busy spinner and "
            "<code>disabled</code> to block interaction. Listen for the "
            "<code>mj-click</code> event in script.</p>"
        ),
        example=(
            '<mj-button variant="primary">Save changes</mj-button>\n'
            '<mj-button variant="secondary">Cancel</mj-button>\n'
            '<mj-button variant="tertiary">Learn more</mj-button>\n'
            '<mj-button variant="link">A link button</mj-button>\n'
            '<mj-button variant="primary" loading>Saving&hellip;</mj-button>\n'
            "<mj-button disabled>Disabled</mj-button>"
        ),
        attributes=[
            ("variant", "primary | secondary | tertiary | link."),
            ("size", "sm | md | lg control sizing."),
            ("type", "button | submit | reset form behavior."),
            ("loading", "Boolean; shows a spinner and marks aria-busy."),
            ("disabled", "Boolean; blocks interaction."),
            ("icon-only", "Boolean; square icon button (needs label)."),
            ("block", "Boolean; full-width display."),
        ],
        events=[
            ("mj-click", "Fired on activation; cancelable."),
        ],
    ),
    ComponentDoc(
        tag="mj-fab",
        title="Floating Action Button",
        group="buttons",
        summary="A prominent, fixed-position primary action.",
        description=(
            "<p><code>&lt;mj-fab&gt;</code> is a circular, elevated button "
            "for the single most important action on a screen. It can be "
            "pinned to a screen corner and can expand into a speed-dial of "
            "related actions.</p>"
        ),
        how_to_use=(
            "<p>Provide an icon and a <code>label</code> for the "
            "accessible name. Use <code>position</code> to pin it to a "
            "corner and <code>speed-dial</code> to enable an expanding "
            "action menu. Listen for <code>mj-click</code>.</p>"
        ),
        example=(
            '<mj-fab label="Compose" position="bottom-end">'
            "<span slot=\"icon\">&#10010;</span></mj-fab>"
        ),
        attributes=[
            ("label", "Accessible name (required, icon-only control)."),
            ("position", "Corner to pin to, e.g. bottom-end."),
            ("size", "Control sizing."),
            ("speed-dial", "Boolean; enables an expanding action menu."),
            ("loading", "Boolean; busy state."),
        ],
        events=[
            ("mj-click", "Fired on activation."),
            ("mj-expanded", "Fired when the speed-dial opens or closes."),
        ],
    ),
    ComponentDoc(
        tag="mj-toggle-button",
        title="Toggle Button",
        group="buttons",
        summary="An on/off action button with a pressed state.",
        description=(
            "<p><code>&lt;mj-toggle-button&gt;</code> is a button that "
            "stays in an on or off state, exposed through "
            "<code>aria-pressed</code>. Use it for actions that flip a "
            "mode, such as bold text or muting audio &mdash; not for form "
            "values, where a checkbox belongs.</p>"
        ),
        how_to_use=(
            "<p>Set <code>pressed</code> for the initial state. The "
            "<code>mj-change</code> event is cancelable, so a handler can "
            "veto the toggle; <code>mj-pressed</code> reports the settled "
            "state.</p>"
        ),
        example=(
            "<mj-toggle-button>Bold</mj-toggle-button>\n"
            "<mj-toggle-button pressed>Muted</mj-toggle-button>"
        ),
        attributes=[
            ("pressed", "Boolean; the on/off state."),
            ("variant", "Visual emphasis."),
            ("size", "Control sizing."),
            ("disabled", "Boolean; blocks interaction."),
        ],
        events=[
            ("mj-change", "Cancelable; fired before the state settles."),
            ("mj-pressed", "Fired with the settled pressed state."),
        ],
    ),
    ComponentDoc(
        tag="mj-disclosure-button",
        title="Disclosure Button",
        group="buttons",
        summary="A button that shows or hides related content.",
        description=(
            "<p><code>&lt;mj-disclosure-button&gt;</code> toggles the "
            "visibility of an associated region, wiring "
            "<code>aria-expanded</code> and <code>aria-controls</code> for "
            "assistive technology. It is the trigger half of a disclosure "
            "pattern.</p>"
        ),
        how_to_use=(
            "<p>Point <code>controls</code> at the id of the region it "
            "toggles. Set <code>expanded</code> for the initial state and "
            "listen for <code>mj-change</code>.</p>"
        ),
        example=(
            '<mj-disclosure-button controls="more-info">'
            "More details</mj-disclosure-button>\n"
            '<div id="more-info">Extra content revealed by the button.</div>'
        ),
        attributes=[
            ("controls", "Id of the region this button toggles."),
            ("expanded", "Boolean; the open/closed state."),
            ("chevron", "Boolean; show a rotating chevron icon."),
        ],
        events=[
            ("mj-change", "Cancelable; fired before the state settles."),
            ("mj-expanded", "Fired with the settled expanded state."),
        ],
    ),
    ComponentDoc(
        tag="mj-copy-button",
        title="Copy Button",
        group="buttons",
        summary="Copies text to the clipboard with confirmation.",
        description=(
            "<p><code>&lt;mj-copy-button&gt;</code> writes a value to the "
            "clipboard and shows a transient confirmation. Use it beside "
            "code samples, share links, or any value the user copies "
            "often.</p>"
        ),
        how_to_use=(
            "<p>Set <code>value</code> to the literal text to copy, or "
            "<code>for</code> to the id of an element whose text content "
            "should be copied. Customize the feedback with "
            "<code>success-label</code>/<code>error-label</code>.</p>"
        ),
        example=(
            '<mj-copy-button value="npm install automojo-webworks">'
            "Copy install command</mj-copy-button>"
        ),
        attributes=[
            ("value", "Literal text to copy."),
            ("for", "Id of an element whose text is copied."),
            ("success-label", "Confirmation label after a copy."),
            ("timeout", "Milliseconds the confirmation is shown."),
        ],
        events=[
            ("mj-copy", "Fired after a successful copy."),
            ("mj-copy-error", "Fired when the copy fails."),
        ],
    ),
    ComponentDoc(
        tag="mj-share-button",
        title="Share Button",
        group="buttons",
        summary="Shares content via the Web Share API with a fallback menu.",
        description=(
            "<p><code>&lt;mj-share-button&gt;</code> invokes the native "
            "Web Share sheet where it is available and falls back to an "
            "inline menu (copy link, email) elsewhere.</p>"
        ),
        how_to_use=(
            "<p>Provide <code>share-url</code>, <code>share-title</code> "
            "and <code>share-text</code>. Set <code>force-menu</code> to "
            "always use the fallback menu. A user-dismissed share sheet is "
            "not treated as an error.</p>"
        ),
        example=(
            '<mj-share-button share-url="https://example.com"\n'
            '  share-title="Automojo WebWorks"\n'
            '  share-text="Check out this component library">'
            "Share</mj-share-button>"
        ),
        attributes=[
            ("share-url", "URL to share."),
            ("share-title", "Title for the shared content."),
            ("share-text", "Descriptive text for the shared content."),
            ("force-menu", "Boolean; always use the fallback menu."),
        ],
        events=[
            ("mj-share", "Fired after a successful share."),
            ("mj-share-error", "Fired when sharing fails."),
        ],
    ),
    ComponentDoc(
        tag="mj-favorite-button",
        title="Favorite Button",
        group="buttons",
        summary="A toggle for like / favorite / bookmark with optimistic UI.",
        description=(
            "<p><code>&lt;mj-favorite-button&gt;</code> is a toggle for "
            "like, favorite, or bookmark actions. It updates optimistically "
            "and can roll back if a save fails, and can show a running "
            "count.</p>"
        ),
        how_to_use=(
            "<p>Choose the icon set with <code>flavor</code> "
            "(<code>like</code>, <code>favorite</code>, "
            "<code>bookmark</code>). Set <code>pressed</code> for the "
            "initial state and <code>count</code> to show a tally. Call "
            "<code>rollback()</code> if a persistence call fails.</p>"
        ),
        example=(
            '<mj-favorite-button flavor="like" count="42">'
            "Like</mj-favorite-button>\n"
            '<mj-favorite-button flavor="bookmark" pressed>'
            "Bookmarked</mj-favorite-button>"
        ),
        attributes=[
            ("flavor", "like | favorite | bookmark icon set."),
            ("pressed", "Boolean; the on/off state."),
            ("count", "Numeric tally displayed beside the icon."),
            ("pending", "Boolean; blocks input during a save."),
        ],
        events=[
            ("mj-change", "Cancelable; fired before the state settles."),
            ("mj-pressed", "Fired with the settled pressed state."),
            ("mj-rollback", "Fired when an optimistic update is reverted."),
        ],
    ),
    ComponentDoc(
        tag="mj-download-button",
        title="Download Button",
        group="buttons",
        summary="A button-styled control that triggers an HTTP download.",
        description=(
            "<p><code>&lt;mj-download-button&gt;</code> renders a real "
            "<code>&lt;a download&gt;</code> internally so the browser "
            "handles the transfer, middle-click opens in a new tab, and "
            "the URL appears in the browser's download UI. Consumers can "
            "intercept the click by listening for the cancelable "
            "<code>mj-download-start</code> event and supplying their own "
            "(signed-URL, progress, ...) flow.</p>"
        ),
        how_to_use=(
            "<p>Set <code>href</code> to the resource URL and "
            "<code>filename</code> to the suggested local filename. "
            "<code>variant</code> and <code>size</code> mirror "
            "<code>mj-button</code>. Add <code>loading</code> while a "
            "deferred download is in flight.</p>"
        ),
        example=(
            '<mj-download-button href="/exports/report.csv" '
            'filename="report.csv" variant="primary">'
            "Download CSV</mj-download-button>"
        ),
        attributes=[
            ("href", "URL of the resource to download."),
            ("filename", "Suggested filename for the saved file."),
            ("variant", "primary | secondary | tertiary | link."),
            ("size", "sm | md | lg control sizing."),
            ("loading", "Boolean; shows a spinner and blocks activation."),
            ("disabled", "Boolean; blocks activation."),
            ("target", "Anchor target (e.g. _blank)."),
            ("rel", "Anchor rel value; defaulted to noopener noreferrer when target=_blank."),
        ],
        events=[
            ("mj-download-start", "Cancelable; fired on click with { href, filename }."),
        ],
    ),
    ComponentDoc(
        tag="mj-upload-button",
        title="Upload Button",
        group="buttons",
        summary="Button that triggers a file picker and accepts file drops.",
        description=(
            "<p><code>&lt;mj-upload-button&gt;</code> wraps a hidden "
            "<code>&lt;input type=file&gt;</code> styled as a button and "
            "also accepts drag-and-drop file drops on its host (or any "
            "ancestor selector named by <code>drop-target</code>). Picks "
            "and drops both fire one <code>mj-upload-select</code> event "
            "carrying the FileList plus the accepted / rejected "
            "partitions after <code>accept</code> and <code>max-size</code> "
            "filtering.</p>"
        ),
        how_to_use=(
            "<p>Set <code>accept</code> (MIME or extension list), "
            "<code>multiple</code>, and <code>max-size</code> (bytes) to "
            "shape the picker. Add <code>name</code> when the control is "
            "inside a <code>&lt;form&gt;</code> so the picked files are "
            "submitted alongside other fields. Listen for "
            "<code>mj-upload-select</code>.</p>"
        ),
        example=(
            '<mj-upload-button accept=".csv,text/csv" multiple>'
            "Choose CSV files</mj-upload-button>"
        ),
        attributes=[
            ("accept", "Comma-separated list of MIME types or file extensions."),
            ("multiple", "Boolean; allow selecting more than one file."),
            ("capture", "user | environment - mobile camera capture."),
            ("max-size", "Maximum size per file, in bytes."),
            ("name", "Form-field name when used inside <form>."),
            ("variant", "primary | secondary | tertiary."),
            ("size", "sm | md | lg control sizing."),
            ("loading", "Boolean; shows a spinner and blocks activation."),
            ("disabled", "Boolean; blocks activation."),
            ("drop-target", "CSS selector for an alternate drop surface."),
        ],
        events=[
            ("mj-upload-select", "Fired with { files, accepted, rejected, source } on every pick or drop."),
        ],
    ),
]
