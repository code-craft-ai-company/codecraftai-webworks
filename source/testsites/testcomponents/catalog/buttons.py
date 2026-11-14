"""
    buttons.py

    Catalog entries for the 'Buttons & Actions' component group.

    Every group module exposes a module-level ``COMPONENTS`` list of
    ComponentDoc instances describing and demonstrating its components. Each
    entry here fills the full sandbox record: an example gallery, typed
    attribute controls, events with their detail shape, slots with sample
    content, and the property / method / part / custom-property tables, all
    checked against the component sources in
    ``static/javascript/components/mj<name>.js``.
"""

import re
import textwrap

from testcomponents.catalog.componentdoc import AttributeDoc
from testcomponents.catalog.componentdoc import ComponentDoc
from testcomponents.catalog.componentdoc import ComponentExample


#: Path data of the inline icons the examples use (16x16 grid, stroked with currentColor).
_ICON_PATHS = {
    "archive": '<rect x="2" y="3" width="12" height="3" rx="1"/><path d="M3 6v7h10V6M6.5 9h3"/>',
    "arrow-right": '<path d="M3 8h10M9 4l4 4-4 4"/>',
    "check-circle": '<circle cx="8" cy="8" r="6"/><path d="M5.5 8.2 7.2 10 10.5 6.2"/>',
    "clipboard": '<rect x="4" y="3" width="8" height="11" rx="1"/><path d="M6 3V2h4v1M6 7h4M6 10h4"/>',
    "download": '<path d="M8 2.5v8M4.5 7 8 10.5 11.5 7M3 13.5h10"/>',
    "eye": '<path d="M1.5 8S4 3.5 8 3.5 14.5 8 14.5 8 12 12.5 8 12.5 1.5 8 1.5 8z"/><circle cx="8" cy="8" r="2"/>',
    "eye-off": '<path d="M1.5 8S4 3.5 8 3.5 14.5 8 14.5 8 12 12.5 8 12.5 1.5 8 1.5 8z"/><path d="M2.5 2.5l11 11"/>',
    "filter": '<path d="M2 3h12l-4.5 5.5V13l-3-1.5v-3z"/>',
    "gear": '<circle cx="8" cy="8" r="2.2"/><path d="M8 1.5v2M8 12.5v2M1.5 8h2M12.5 8h2M3.4 3.4l1.4 1.4M11.2 11.2l1.4 1.4M3.4 12.6l1.4-1.4M11.2 4.8l1.4-1.4"/>',
    "help": '<circle cx="8" cy="8" r="6"/><path d="M6.3 6.2a1.8 1.8 0 0 1 3.4.8c0 1.2-1.7 1.5-1.7 2.6M8 11.5v.01"/>',
    "image": '<rect x="2" y="3" width="12" height="10" rx="1.5"/><circle cx="6" cy="6.5" r="1.2"/><path d="M2.5 12l3.5-3.5 2.5 2.5 2-2 3 3"/>',
    "link": '<path d="M6.5 9.5a2.5 2.5 0 0 0 3.5 0l2.5-2.5a2.5 2.5 0 0 0-3.5-3.5l-.8.8M9.5 6.5a2.5 2.5 0 0 0-3.5 0L3.5 9a2.5 2.5 0 0 0 3.5 3.5l.8-.8"/>',
    "mic": '<rect x="6" y="2" width="4" height="7.5" rx="2"/><path d="M3.5 8a4.5 4.5 0 0 0 9 0M8 12.5V14"/>',
    "mic-off": '<rect x="6" y="2" width="4" height="7.5" rx="2"/><path d="M3.5 8a4.5 4.5 0 0 0 9 0M8 12.5V14M2.5 2.5l11 11"/>',
    "more": '<circle cx="8" cy="3.5" r="1"/><circle cx="8" cy="8" r="1"/><circle cx="8" cy="12.5" r="1"/>',
    "pencil": '<path d="M11 2.5l2.5 2.5L6 12.5 3 13l.5-3z"/>',
    "pin": '<path d="M6 2h4l-.5 4 2.5 2.5H4L6.5 6zM8 8.5V14"/>',
    "plus": '<path d="M8 3v10M3 8h10"/>',
    "refresh": '<path d="M13 8a5 5 0 1 1-1.5-3.5M13 2.5v3h-3"/>',
    "search": '<circle cx="7" cy="7" r="4.5"/><path d="M10.5 10.5 14 14"/>',
    "send": '<path d="M2 8l12-5.5L9.5 14 7.5 9z"/>',
    "share": '<circle cx="12" cy="3.5" r="1.75"/><circle cx="4" cy="8" r="1.75"/><circle cx="12" cy="12.5" r="1.75"/><path d="M5.6 7.1l4.8-2.7M5.6 8.9l4.8 2.7"/>',
    "trash": '<path d="M3 4.5h10M6.5 4.5V3h3v1.5M4.5 4.5l.5 8.5h6l.5-8.5"/>',
    "upload": '<path d="M8 13.5v-8M4.5 9 8 5.5 11.5 9M3 2.5h10"/>',
    "user-check": '<circle cx="6.5" cy="5.5" r="2.5"/><path d="M2 13.5a4.5 4.5 0 0 1 9 0M10.5 8l1.5 1.5 3-3"/>',
    "user-plus": '<circle cx="6.5" cy="5.5" r="2.5"/><path d="M2 13.5a4.5 4.5 0 0 1 9 0M13 6v4M11 8h4"/>',
}

_ICON_TOKEN = re.compile(r"\[\[([a-z-]+)(?:\|([a-z-]+))?\]\]")

#: A small CSV file served as a data: URL, so the download examples work offline.
_CSV_HREF = (
    "data:text/csv;charset=utf-8,Region%2CQ3%20sales%0ANorth%2C1200%0ASouth%2C980%0AWest%2C1430%0A"
)


def _svg(name: str, slot: "str | None" = None) -> str:
    """
        Return the markup of an inline icon from ``_ICON_PATHS``.

        :param name: The icon key.
        :param slot: Optional slot name to put on the ``<svg>``.

        :returns: The ``<svg>`` markup.
    """

    slot_attr = ""
    if slot is not None:
        slot_attr = ' slot="{}"'.format(slot)
    markup = (
        '<svg{} viewBox="0 0 16 16" width="16" height="16" fill="none" stroke="currentColor" '
        'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
        "{}</svg>".format(slot_attr, _ICON_PATHS[name])
    )
    return markup


def _code(text: str) -> str:
    """
        Dedent a triple-quoted source block, strip its surrounding blank lines
        and expand ``[[icon]]`` / ``[[icon|slot]]`` tokens into inline SVG.

        :param text: The source block.

        :returns: The cleaned source.
    """

    cleaned = textwrap.dedent(text).strip("\n")
    cleaned = _ICON_TOKEN.sub(lambda match: _svg(match.group(1), match.group(2)), cleaned)
    return cleaned


#: Layout helpers shared by several examples.
_ROW_CSS = _code("""
    .row { display: flex; flex-wrap: wrap; align-items: center; gap: var(--mj-space-3); }
    .stack { display: grid; gap: var(--mj-space-3); }
    .note { margin-block: var(--mj-space-3) 0; color: var(--mj-text-muted); font-size: var(--mj-font-size-sm); }
""")


# ---------------------------------------------------------------------------
# mj-button
# ---------------------------------------------------------------------------

_BUTTON = ComponentDoc(
    tag="mj-button",
    title="Button",
    group="buttons",
    summary="The primary action control: variants, sizes, icons, busy state and form submission.",
    description=(
        "<p><code>&lt;mj-button&gt;</code> is the action control of the library. One component "
        "covers every button role &mdash; default, primary, secondary, tertiary, link and "
        "icon-only &mdash; through the <code>variant</code>, <code>size</code> and "
        "<code>icon-only</code> attributes. Without <code>variant</code> it uses the neutral "
        "default style (surface background, strong border).</p>"
        "<p><code>disabled</code> and <code>loading</code> block activation through "
        "<code>aria-disabled</code> / <code>aria-busy</code>: the inner button is never natively "
        "disabled, so it keeps focus and its tab stop. Entering and leaving the loading state is "
        "announced (<code>loading-label</code>, <code>done-label</code>).</p>"
        "<p>The element is form-associated. With <code>type=\"submit\"</code> or "
        "<code>\"reset\"</code> it first fires the cancelable <code>mj-submit-request</code> / "
        "<code>mj-reset-request</code>; when no container (such as <code>&lt;mj-form&gt;</code>) "
        "cancels it, the native form owner is submitted through <code>requestSubmit()</code> with "
        "this button as the submitter, so its <code>name</code> / <code>value</code> and "
        "<code>form*</code> overrides reach the request, or reset. Without a native form the "
        "closest <code>&lt;mj-form&gt;</code> is driven. Enter in a text field submits through "
        "the form's first submit button, as for native buttons, and "
        "<code>&lt;fieldset disabled&gt;</code> disables it.</p>"
        "<p>The host ARIA attributes <code>aria-expanded</code>, <code>aria-haspopup</code>, "
        "<code>aria-pressed</code>, <code>aria-current</code> and <code>aria-description</code> "
        "are copied to the inner button; <code>aria-controls</code>, <code>aria-describedby</code> "
        "and <code>aria-labelledby</code> are resolved to the referenced elements; "
        "<code>aria-label</code> names it when <code>label</code> is absent.</p>"
    ),
    how_to_use=(
        "<p>Put the text between the tags and an optional icon in the <code>icon</code> (leading) "
        "or <code>trailing-icon</code> slot. Choose the emphasis with <code>variant</code> and the "
        "size with <code>size</code>. For an icon-only button add <code>icon-only</code> and a "
        "<code>label</code>, which becomes the accessible name. Listen for <code>mj-click</code> "
        "(cancelable); inside a <code>&lt;form&gt;</code> use <code>type=\"submit\"</code> / "
        "<code>\"reset\"</code> with <code>name</code> and <code>value</code> to tell submit "
        "buttons apart. Set <code>loading</code> while an action runs; the button stays "
        "focusable.</p>"
    ),
    example="",
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>A primary and a secondary action. Click one and watch <code>mj-click</code> in "
                "Events; the Controls drive the first button.</p>"
            ),
            html=_code("""
                <div class="row">
                  <mj-button id="save-button" variant="primary">Save changes</mj-button>
                  <mj-button variant="secondary">Cancel</mj-button>
                </div>
            """),
            css=_ROW_CSS,
        ),
        ComponentExample(
            key="variants",
            title="Variants",
            description=(
                "<p>The default style (no <code>variant</code>) next to primary, secondary, "
                "tertiary and link. Switch the preview to Dark to compare the token colours.</p>"
            ),
            html=_code("""
                <div class="row">
                  <mj-button>Default</mj-button>
                  <mj-button variant="primary">Primary</mj-button>
                  <mj-button variant="secondary">Secondary</mj-button>
                  <mj-button variant="tertiary">Tertiary</mj-button>
                  <mj-button variant="link">Link</mj-button>
                </div>
            """),
            css=_ROW_CSS,
        ),
        ComponentExample(
            key="sizes",
            title="Sizes and block",
            description=(
                "<p><code>size=\"sm\"</code>, the default <code>md</code> and <code>lg</code>, "
                "and a <code>block</code> button on its own line (the host is block-level; the "
                "inner button keeps its content width).</p>"
            ),
            html=_code("""
                <div class="stack">
                  <div class="row">
                    <mj-button size="sm" variant="primary">Small</mj-button>
                    <mj-button variant="primary">Medium</mj-button>
                    <mj-button size="lg" variant="primary">Large</mj-button>
                  </div>
                  <mj-button block variant="secondary">Block button</mj-button>
                </div>
            """),
            css=_ROW_CSS,
        ),
        ComponentExample(
            key="with-icons",
            title="Icons and icon-only",
            description=(
                "<p>A leading <code>icon</code>, a <code>trailing-icon</code>, and two "
                "<code>icon-only</code> buttons named by their <code>label</code>. Toggle the "
                "slots in the Slots panel.</p>"
            ),
            html=_code("""
                <div class="row">
                  <mj-button variant="primary">[[plus|icon]]New project</mj-button>
                  <mj-button variant="secondary">Next step[[arrow-right|trailing-icon]]</mj-button>
                  <mj-button icon-only label="Edit profile">[[pencil|icon]]</mj-button>
                  <mj-button icon-only variant="tertiary" label="Delete draft">[[trash|icon]]</mj-button>
                </div>
            """),
            css=_ROW_CSS,
        ),
        ComponentExample(
            key="states",
            title="Loading, disabled and events",
            description=(
                "<p>The script clicks <b>Publish</b>: it turns <code>loading</code> for 1.5 s "
                "(announced as \"Publishing\" / \"Published\"). <b>Guarded</b> cancels its "
                "<code>mj-click</code>. The loading and disabled buttons ignore clicks but stay "
                "focusable.</p>"
            ),
            html=_code("""
                <div class="row">
                  <mj-button id="publish" variant="primary" loading-label="Publishing" done-label="Published">Publish</mj-button>
                  <mj-button variant="secondary" loading>Saving&hellip;</mj-button>
                  <mj-button disabled>Disabled</mj-button>
                  <mj-button id="guarded" variant="tertiary">Guarded</mj-button>
                </div>
            """),
            css=_ROW_CSS,
            script=_code("""
                const publish = document.getElementById("publish")
                publish.addEventListener("mj-click", () => {
                  publish.loading = true
                  mjSandbox.log("publish started", { loading: publish.loading })
                  setTimeout(() => {
                    publish.loading = false
                    mjSandbox.log("publish finished", { loading: publish.loading })
                  }, 1500)
                })

                document.getElementById("guarded").addEventListener("mj-click", (event) => {
                  event.preventDefault()
                  mjSandbox.log("mj-click cancelled", { defaultPrevented: event.defaultPrevented })
                })

                publish.click()
            """),
        ),
        ComponentExample(
            key="form",
            title="Form submit and reset",
            description=(
                "<p>Two submit buttons with <code>name=\"intent\"</code> and different "
                "<code>value</code>s, and a reset button. The script reads the submitted data "
                "with the submitter; Enter in the text field submits through the first submit "
                "button.</p>"
            ),
            html=_code("""
                <form id="invoice-form" class="stack">
                  <label>Invoice number <input name="invoice" value="INV-1042"></label>
                  <div class="row">
                    <mj-button type="submit" name="intent" value="save" variant="primary">Save</mj-button>
                    <mj-button type="submit" name="intent" value="send" variant="secondary">Save and send</mj-button>
                    <mj-button type="reset" variant="tertiary">Reset</mj-button>
                  </div>
                </form>
                <output id="form-result" class="note">Submit the form to see its data.</output>
            """),
            css=_ROW_CSS + "\nlabel { display: grid; gap: var(--mj-space-1); max-inline-size: 20rem; }",
            script=_code("""
                const form = document.getElementById("invoice-form")
                const result = document.getElementById("form-result")

                form.addEventListener("submit", (event) => {
                  event.preventDefault()
                  const data = Object.fromEntries(new FormData(form, event.submitter))
                  result.textContent = "Submitted: " + JSON.stringify(data)
                  mjSandbox.log("submit", data)
                })
                form.addEventListener("reset", () => {
                  result.textContent = "The form was reset."
                  mjSandbox.log("reset", {})
                })
            """),
        ),
    ],
    attributes=[
        AttributeDoc(
            name="variant",
            description="Visual emphasis. Without it the button uses the neutral default style.",
            kind="enum",
            values=["primary", "secondary", "tertiary", "link"],
        ),
        AttributeDoc(name="size", description="Control height, padding and font size.",
                     kind="enum", values=["sm", "md", "lg"], default="md"),
        AttributeDoc(
            name="type",
            description="`submit` / `reset` act on the form owner (see mj-submit-request); `button` does nothing on its own.",
            kind="enum",
            values=["button", "submit", "reset"],
            default="button",
        ),
        AttributeDoc(
            name="disabled",
            description="Blocks activation; sets aria-disabled on the inner button, which stays focusable.",
            kind="boolean",
        ),
        AttributeDoc(
            name="loading",
            description="Busy state: shows a spinner, sets aria-busy, blocks activation and announces the change.",
            kind="boolean",
        ),
        AttributeDoc(name="loading-label", description="Text announced when loading starts.",
                     kind="string", default="Loading"),
        AttributeDoc(name="done-label", description="Text announced when loading ends.",
                     kind="string", default="Done"),
        AttributeDoc(
            name="icon-only",
            description="Square button that shows only the icon; the slotted text stays as the accessible name unless `label` is set.",
            kind="boolean",
        ),
        AttributeDoc(
            name="label",
            description="Accessible name (wins over aria-label and the slotted text). Required for an icon-only button without text.",
            kind="string",
        ),
        AttributeDoc(name="block", description="Makes the host a block-level element on its own line.",
                     kind="boolean"),
        AttributeDoc(name="name", description="Name of the submitter pair sent with a type=submit button.",
                     kind="string"),
        AttributeDoc(name="value", description="Value of the submitter pair sent with a type=submit button.",
                     kind="string"),
        AttributeDoc(name="formaction", description="Overrides the form action for this submitter.",
                     kind="string"),
        AttributeDoc(name="formmethod", description="Overrides the form method for this submitter.",
                     kind="enum", values=["get", "post", "dialog"]),
        AttributeDoc(
            name="formenctype",
            description="Overrides the form encoding for this submitter.",
            kind="enum",
            values=["application/x-www-form-urlencoded", "multipart/form-data", "text/plain"],
        ),
        AttributeDoc(name="formnovalidate", description="Skips constraint validation for this submitter.",
                     kind="boolean"),
        AttributeDoc(name="formtarget", description="Overrides the form target for this submitter.",
                     kind="string", values=["_self", "_blank"]),
    ],
    events=[
        (
            "mj-click",
            "Fired on activation (never while disabled or loading). Cancelable: preventDefault() also stops the submit / reset request.",
            "{ source: MjButton, originalEvent: MouseEvent }",
        ),
        (
            "mj-submit-request",
            "type=submit, after mj-click. Cancelable: a container that calls preventDefault() (mj-form) handles the submit; otherwise the native form owner is submitted with this button as submitter, else the closest mj-form.",
            "{ submitter: MjButton }",
        ),
        (
            "mj-reset-request",
            "type=reset, after mj-click. Cancelable: a container that calls preventDefault() handles the reset; otherwise the form owner (or closest mj-form) is reset.",
            "{ submitter: MjButton }",
        ),
    ],
    slots=[
        ("", "The button text. Stays the accessible name in icon-only mode.", "Save draft"),
        ("icon", "Leading icon.", _svg("plus")),
        ("trailing-icon", "Icon after the text.", _svg("arrow-right")),
    ],
    properties=[
        ("loading", "boolean. Reflects the `loading` attribute."),
        ("disabled", "boolean. Reflects the `disabled` attribute."),
        ("form", "HTMLFormElement | null. Read-only; the native form owner."),
    ],
    methods=[
        ("click()", "Activates the button as a user click would (fires mj-click, then the form action)."),
        ("focus(options)", "Focuses the inner button."),
    ],
    parts=[
        ("button", "The inner native button."),
        ("spinner", "Busy spinner (shown while loading)."),
        ("icon", "The leading icon slot."),
        ("label", "Wrapper of the default slot."),
        ("trailing-icon", "The trailing icon slot."),
    ],
    css_properties=[
        ("--mj-button-bg", "Background; overrides the variant colour."),
        ("--mj-button-color", "Text colour; overrides the variant colour."),
        ("--mj-button-border-color", "Border colour; overrides the variant colour."),
        ("--mj-button-border-radius", "Corner radius (default var(--mj-radius-md))."),
        ("--mj-button-height", "Minimum height (default the control height of the size)."),
        ("--mj-button-min-width", "Minimum width (default var(--mj-target-min); auto for link)."),
        ("--mj-button-padding-x", "Inline padding (default var(--mj-space-4); 3 for sm, 5 for lg)."),
        ("--mj-button-padding-y", "Block padding (default 0)."),
        ("--mj-button-gap", "Gap between icon and text (default var(--mj-space-2))."),
        ("--mj-button-font-size", "Font size (default inherit; sm/lg use the size tokens)."),
        ("--mj-button-font-weight", "Font weight (default var(--mj-font-weight-medium))."),
        ("--mj-button-focus-ring-color", "Focus ring colour (default var(--mj-focus-ring))."),
    ],
)


# ---------------------------------------------------------------------------
# mj-fab
# ---------------------------------------------------------------------------

_FAB_ITEM_CSS = _code("""
    [slot="speed-dial-item"] {
      padding: var(--mj-space-2) var(--mj-space-4);
      font: inherit;
      color: var(--mj-text);
      background: var(--mj-surface-raised);
      border: 1px solid var(--mj-border);
      border-radius: var(--mj-radius-pill);
      box-shadow: var(--mj-elevation-2);
      white-space: nowrap;
      cursor: pointer;
    }
    [slot="speed-dial-item"]:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); }
""")

_FAB = ComponentDoc(
    tag="mj-fab",
    title="Floating Action Button",
    group="buttons",
    summary="A prominent button for the main action of a screen, pinned to a viewport corner, with an optional speed dial.",
    description=(
        "<p><code>&lt;mj-fab&gt;</code> is a circular, elevated button for the single most "
        "important action on a screen. It is <code>position: fixed</code>: pinned to the corner "
        "named by <code>position</code>, or to the bottom-end corner when neither "
        "<code>position</code> nor <code>anchor</code> is set. <code>offset-x</code> / "
        "<code>offset-y</code> move it away from the edges.</p>"
        "<p>Sizes <code>sm</code>, <code>md</code> and <code>lg</code> show only the icon; "
        "<code>extended</code> is a pill that also shows the slotted label text.</p>"
        "<p>With <code>speed-dial</code> the button opens a menu of related actions instead of "
        "firing <code>mj-click</code>. Actions are slotted with "
        "<code>slot=\"speed-dial-item\"</code>; each gets <code>role=\"menuitem\"</code>. "
        "Opening moves focus to the first action, Arrow keys / Home / End move between them, "
        "choosing one fires <code>mj-select</code> and closes the dial, and Escape, a click "
        "outside or moving focus away closes it.</p>"
    ),
    how_to_use=(
        "<p>Put an icon in the <code>icon</code> slot and give the button a <code>label</code> "
        "(its accessible name; the slotted text is used when <code>label</code> is absent). "
        "Listen for <code>mj-click</code>. For a speed dial add <code>speed-dial</code>, slot "
        "buttons with <code>slot=\"speed-dial-item\"</code> and a <code>value</code>, and "
        "listen for <code>mj-select</code>. Set <code>loading</code> while the action runs.</p>"
    ),
    example="",
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>A compose button pinned to the bottom-end corner of the preview over the page "
                "content. Click it and watch <code>mj-click</code>.</p>"
            ),
            html=_code("""
                <section class="page">
                  <h3>Inbox</h3>
                  <ul>
                    <li>Quarterly report draft</li>
                    <li>Team offsite agenda</li>
                    <li>Invoice INV-1042</li>
                  </ul>
                </section>
                <mj-fab id="compose" label="Compose message" position="bottom-end">[[pencil|icon]]</mj-fab>
            """),
            css=_code("""
                .page { padding-block-end: 6rem; }
                .page h3 { margin-block: 0 var(--mj-space-2); }
                mj-fab svg { width: 1.5rem; height: 1.5rem; }
            """),
            height=240,
        ),
        ComponentExample(
            key="positions",
            title="Positions and offsets",
            description=(
                "<p>One button per corner. The top-end one is moved in with "
                "<code>offset-x=\"2.5rem\"</code> / <code>offset-y=\"2.5rem\"</code>; the bottom-end "
                "one is <code>size=\"extended\"</code> and shows its text.</p>"
            ),
            html=_code("""
                <mj-fab label="Search" position="top-start" size="sm">[[search|icon]]</mj-fab>
                <mj-fab label="Settings" position="top-end" offset-x="2.5rem" offset-y="2.5rem">[[gear|icon]]</mj-fab>
                <mj-fab label="Help" position="bottom-start" size="lg">[[help|icon]]</mj-fab>
                <mj-fab position="bottom-end" size="extended">[[plus|icon]]New task</mj-fab>
            """),
            css="mj-fab svg { width: 1.25rem; height: 1.25rem; }",
            height=320,
        ),
        ComponentExample(
            key="sizes",
            title="Sizes",
            description=(
                "<p><code>sm</code>, <code>md</code> (default), <code>lg</code> and "
                "<code>extended</code>. The page CSS sets <code>position: static</code> on these "
                "hosts so they sit side by side instead of being pinned.</p>"
            ),
            html=_code("""
                <div class="row">
                  <mj-fab label="Add (small)" size="sm">[[plus|icon]]</mj-fab>
                  <mj-fab label="Add (medium)">[[plus|icon]]</mj-fab>
                  <mj-fab label="Add (large)" size="lg">[[plus|icon]]</mj-fab>
                  <mj-fab size="extended">[[plus|icon]]Create event</mj-fab>
                </div>
            """),
            css=_ROW_CSS + "\n.row mj-fab { position: static; }\nmj-fab svg { width: 1.25rem; height: 1.25rem; }",
        ),
        ComponentExample(
            key="speed-dial",
            title="Speed dial",
            description=(
                "<p>A speed dial with three slotted actions, opened by the script. Focus the "
                "button and press ArrowDown / ArrowUp to move into the actions, Enter to choose "
                "(fires <code>mj-select</code> with the action's <code>value</code> and closes "
                "the dial), Escape to close.</p>"
            ),
            html=_code("""
                <mj-fab id="create" label="Create" speed-dial position="bottom-end">
                  [[plus|icon]]
                  <button slot="speed-dial-item" type="button" value="document">New document</button>
                  <button slot="speed-dial-item" type="button" value="folder">New folder</button>
                  <button slot="speed-dial-item" type="button" value="upload">Upload file</button>
                </mj-fab>
                <p id="choice" class="note">Choose an action from the dial.</p>
            """),
            css=_ROW_CSS + "\n" + _FAB_ITEM_CSS + "\nmj-fab svg { width: 1.5rem; height: 1.5rem; }",
            script=_code("""
                const fab = document.getElementById("create")
                const choice = document.getElementById("choice")

                fab.addEventListener("mj-select", (event) => {
                  choice.textContent = "Chosen: " + event.detail.value
                })

                fab.expanded = true
            """),
            height=320,
        ),
        ComponentExample(
            key="states",
            title="Loading, disabled and events",
            description=(
                "<p>The script clicks <b>Sync now</b>, which turns <code>loading</code> for 1.5 s. "
                "The loading and disabled buttons ignore clicks. These hosts are also made "
                "static by the page CSS.</p>"
            ),
            html=_code("""
                <div class="row">
                  <mj-fab id="sync" label="Sync now">[[refresh|icon]]</mj-fab>
                  <mj-fab label="Uploading" loading>[[upload|icon]]</mj-fab>
                  <mj-fab label="Archive" disabled>[[archive|icon]]</mj-fab>
                </div>
            """),
            css=_ROW_CSS + "\n.row mj-fab { position: static; }\nmj-fab svg { width: 1.25rem; height: 1.25rem; }",
            script=_code("""
                const sync = document.getElementById("sync")
                sync.addEventListener("mj-click", () => {
                  sync.loading = true
                  mjSandbox.log("sync started", { loading: sync.loading })
                  setTimeout(() => {
                    sync.loading = false
                    mjSandbox.log("sync finished", { loading: sync.loading })
                  }, 1500)
                })

                // click() activates the inner button, as a user click would.
                sync.click()
            """),
        ),
    ],
    attributes=[
        AttributeDoc(
            name="label",
            description="Accessible name of the button and of the speed-dial menu. Falls back to the slotted text.",
            kind="string",
        ),
        AttributeDoc(
            name="position",
            description="Viewport corner the button is pinned to. Without position or anchor it is pinned bottom-end.",
            kind="enum",
            values=["bottom-end", "bottom-start", "top-end", "top-start"],
            default="bottom-end",
        ),
        AttributeDoc(name="offset-x", description="Inline distance from the edge, any CSS length.",
                     kind="string", values=["1rem", "2rem", "24px"], default="1rem"),
        AttributeDoc(name="offset-y", description="Block distance from the edge, any CSS length.",
                     kind="string", values=["1rem", "2rem", "24px"], default="1rem"),
        AttributeDoc(
            name="size",
            description="sm / md / lg are round icon buttons; extended is a pill that shows the slotted text.",
            kind="enum",
            values=["sm", "md", "lg", "extended"],
            default="md",
        ),
        AttributeDoc(name="speed-dial", description="Clicking opens the slotted speed-dial actions instead of firing mj-click.",
                     kind="boolean"),
        AttributeDoc(name="expanded", description="Open state of the speed dial (expanded=\"false\" is closed).",
                     kind="boolean"),
        AttributeDoc(name="loading", description="Busy state: spinner, aria-busy, activation blocked.",
                     kind="boolean"),
        AttributeDoc(name="disabled", description="Blocks activation (the inner button is disabled).",
                     kind="boolean"),
    ],
    events=[
        ("mj-click", "Fired on activation of a button without speed-dial.", "{ originalEvent: MouseEvent }"),
        ("mj-expanded", "The speed dial opened or closed, however it was changed.", "{ expanded: boolean }"),
        ("mj-select", "A speed-dial action was chosen; the dial closes and focus returns to the button.",
         "{ item: Element, value: string | null }"),
    ],
    slots=[
        ("icon", "The button icon.", _svg("plus")),
        ("", "Label text, shown only with size=\"extended\"; names the button when `label` is absent.", "New task"),
        (
            "speed-dial-item",
            "Speed-dial actions (role=menuitem is added; native controls get tabindex=-1).",
            '<button type="button" value="photo">Add photo</button>',
        ),
    ],
    properties=[
        ("expanded", "boolean. Open state of the speed dial; setting it fires mj-expanded."),
        ("loading", "boolean. Reflects the `loading` attribute."),
        ("disabled", "boolean. Reflects the `disabled` attribute."),
    ],
    methods=[
        ("click()", "Activates the inner button as a user click would: mj-click, or opens / closes the speed dial."),
        ("focus(options)", "Focuses the inner button."),
    ],
    parts=[
        ("button", "The round inner button."),
        ("spinner", "Busy spinner."),
        ("icon", "Icon wrapper."),
        ("label", "Label wrapper (shown with size=extended)."),
        ("speed-dial-list", "The speed-dial menu (role=menu)."),
    ],
    css_properties=[
        ("--mj-fab-size", "Width and height of md (default 3.5rem; sm 2.5rem and lg 4rem are fixed)."),
        ("--mj-fab-bg", "Background (default var(--mj-accent))."),
        ("--mj-fab-color", "Icon / text colour (default var(--mj-text-on-accent))."),
        ("--mj-fab-border-radius", "Corner radius (default var(--mj-radius-circle))."),
        ("--mj-fab-elevation", "Shadow (default var(--mj-elevation-3))."),
        ("--mj-fab-offset-x", "Inline edge distance (default 1rem; set by offset-x)."),
        ("--mj-fab-offset-y", "Block edge distance (default 1rem; set by offset-y)."),
        ("--mj-fab-z-index", "Stacking order (default var(--mj-layer-overlay))."),
        ("--mj-fab-speed-dial-gap", "Gap between speed-dial actions (default var(--mj-space-3))."),
        ("--mj-fab-focus-ring-color", "Focus ring colour (default var(--mj-focus-ring))."),
    ],
)


# ---------------------------------------------------------------------------
# mj-toggle-button
# ---------------------------------------------------------------------------

_TOGGLE = ComponentDoc(
    tag="mj-toggle-button",
    title="Toggle Button",
    group="buttons",
    summary="An on/off action button with a pressed state, optional state icons and form participation.",
    description=(
        "<p><code>&lt;mj-toggle-button&gt;</code> is a button that stays on or off, exposed "
        "through <code>aria-pressed</code>. Use it for actions that flip a mode, such as bold "
        "text or muting a microphone; it does not show or hide content (that is "
        "<code>&lt;mj-disclosure-button&gt;</code>).</p>"
        "<p>A click first fires the cancelable <code>mj-change</code> with the requested state. "
        "Unless it is cancelled the state is committed, then the native <code>change</code> "
        "and <code>mj-pressed</code> fire, so <code>change</code> listeners read the new state "
        "and never run for a vetoed toggle.</p>"
        "<p>The <code>icon-off</code> / <code>icon-on</code> slots show the icon of the current "
        "state; when only one of them is filled that icon is shown in both states.</p>"
        "<p>The element is form-associated, like a checkbox: with a <code>name</code> it submits "
        "its <code>value</code> (default <code>on</code>) while pressed and nothing while not "
        "pressed. <code>required</code> makes an unpressed button invalid, form reset restores "
        "the initial state, and <code>&lt;fieldset disabled&gt;</code> disables it.</p>"
    ),
    how_to_use=(
        "<p>Put the text between the tags and set <code>pressed</code> for the initial state. "
        "For an icon-only toggle add <code>icon-only</code>, a <code>label</code> and the state "
        "icons. Listen for <code>mj-pressed</code> (or <code>change</code>) to react, and for "
        "<code>mj-change</code> when the toggle may be refused (call "
        "<code>preventDefault()</code>).</p>"
    ),
    example="",
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>Two formatting toggles, the second initially <code>pressed</code>. Click them "
                "and watch <code>mj-change</code>, <code>change</code> and <code>mj-pressed</code>.</p>"
            ),
            html=_code("""
                <div class="row">
                  <mj-toggle-button id="bold">Bold</mj-toggle-button>
                  <mj-toggle-button pressed>Italic</mj-toggle-button>
                </div>
            """),
            css=_ROW_CSS,
        ),
        ComponentExample(
            key="variants",
            title="Variants and sizes",
            description=(
                "<p>The default outlined style, <code>primary</code> and <code>tertiary</code>, "
                "each off and on, then the three sizes.</p>"
            ),
            html=_code("""
                <div class="stack">
                  <div class="row">
                    <mj-toggle-button>Default</mj-toggle-button>
                    <mj-toggle-button pressed>Default, on</mj-toggle-button>
                    <mj-toggle-button variant="primary">Primary</mj-toggle-button>
                    <mj-toggle-button variant="primary" pressed>Primary, on</mj-toggle-button>
                    <mj-toggle-button variant="tertiary">Tertiary</mj-toggle-button>
                    <mj-toggle-button variant="tertiary" pressed>Tertiary, on</mj-toggle-button>
                  </div>
                  <div class="row">
                    <mj-toggle-button size="sm">Small</mj-toggle-button>
                    <mj-toggle-button>Medium</mj-toggle-button>
                    <mj-toggle-button size="lg">Large</mj-toggle-button>
                  </div>
                </div>
            """),
            css=_ROW_CSS,
        ),
        ComponentExample(
            key="with-icons",
            title="State icons and icon-only",
            description=(
                "<p>An icon-only mute toggle with <code>icon-off</code> / <code>icon-on</code>, a "
                "text toggle with state icons, and a pin toggle that fills only "
                "<code>icon-on</code> (shown in both states).</p>"
            ),
            html=_code("""
                <div class="row">
                  <mj-toggle-button icon-only label="Mute microphone">[[mic|icon-off]][[mic-off|icon-on]]</mj-toggle-button>
                  <mj-toggle-button>[[eye|icon-off]][[eye-off|icon-on]]Hide preview</mj-toggle-button>
                  <mj-toggle-button icon-only variant="tertiary" label="Pin note" pressed>[[pin|icon-on]]</mj-toggle-button>
                </div>
            """),
            css=_ROW_CSS,
        ),
        ComponentExample(
            key="states",
            title="Disabled and loading",
            description=(
                "<p><code>disabled</code> (off and on) and <code>loading</code> ignore clicks; "
                "<code>block</code> puts the toggle on its own line.</p>"
            ),
            html=_code("""
                <div class="stack">
                  <div class="row">
                    <mj-toggle-button disabled>Disabled</mj-toggle-button>
                    <mj-toggle-button disabled pressed>Disabled, on</mj-toggle-button>
                    <mj-toggle-button loading>Syncing</mj-toggle-button>
                  </div>
                  <mj-toggle-button block>Block toggle</mj-toggle-button>
                </div>
            """),
            css=_ROW_CSS,
        ),
        ComponentExample(
            key="events",
            title="Vetoing a toggle",
            description=(
                "<p>While <b>Lock formatting</b> is checked the <code>mj-change</code> handler "
                "cancels the toggle. The script clicks once unlocked and once locked: the log "
                "shows a committed toggle, then a vetoed one without <code>change</code>.</p>"
            ),
            html=_code("""
                <label class="lock"><input type="checkbox" id="lock"> Lock formatting</label>
                <div class="row">
                  <mj-toggle-button id="wrap">Word wrap</mj-toggle-button>
                  <span id="state" class="note"></span>
                </div>
            """),
            css=_ROW_CSS + "\n.lock { display: block; margin-block-end: var(--mj-space-3); }\n.row .note { margin: 0; }",
            script=_code("""
                const toggle = document.getElementById("wrap")
                const lock = document.getElementById("lock")
                const state = document.getElementById("state")
                const show = () => { state.textContent = "pressed = " + toggle.pressed }

                toggle.addEventListener("mj-change", (event) => {
                  if (lock.checked === true) {
                    event.preventDefault()
                    mjSandbox.log("toggle vetoed", { requested: event.detail.pressed })
                  }
                })
                toggle.addEventListener("change", () => {
                  mjSandbox.log("change (after commit)", { pressed: toggle.pressed })
                  show()
                })
                show()

                // Two clicks: one allowed, one vetoed.
                toggle.click()
                lock.checked = true
                toggle.click()
                lock.checked = false
            """),
        ),
        ComponentExample(
            key="form",
            title="Form participation",
            description=(
                "<p>Three named toggles in a form: pressed ones submit their <code>value</code>. "
                "<b>Push</b> is <code>required</code>, so the form does not submit until it is "
                "pressed. Reset restores the initial states; the checkbox disables the "
                "fieldset.</p>"
            ),
            html=_code("""
                <form id="prefs" class="stack">
                  <fieldset id="channels">
                    <legend>Notify me by</legend>
                    <div class="row">
                      <mj-toggle-button name="email" pressed>Email</mj-toggle-button>
                      <mj-toggle-button name="sms" value="yes">SMS</mj-toggle-button>
                      <mj-toggle-button name="push" value="yes" required>Push</mj-toggle-button>
                    </div>
                  </fieldset>
                  <div class="row">
                    <button type="submit">Save</button>
                    <button type="reset">Reset</button>
                    <label><input type="checkbox" id="disable-channels"> Disable the fieldset</label>
                  </div>
                </form>
                <output id="prefs-result" class="note">Save to see the submitted data.</output>
            """),
            css=_ROW_CSS + "\nfieldset { border: 1px solid var(--mj-border); border-radius: var(--mj-radius-md); }",
            script=_code("""
                const form = document.getElementById("prefs")
                const result = document.getElementById("prefs-result")

                form.addEventListener("submit", (event) => {
                  event.preventDefault()
                  const data = Object.fromEntries(new FormData(form))
                  result.textContent = "Submitted: " + JSON.stringify(data)
                  mjSandbox.log("submit", data)
                })
                document.getElementById("disable-channels").addEventListener("change", (event) => {
                  document.getElementById("channels").disabled = event.target.checked
                })
            """),
        ),
    ],
    attributes=[
        AttributeDoc(name="pressed", description="The on state; reflected by clicks.", kind="boolean"),
        AttributeDoc(name="variant", description="Emphasis. Without it the button is outlined.",
                     kind="enum", values=["primary", "tertiary"]),
        AttributeDoc(name="size", description="Control height, padding and font size.",
                     kind="enum", values=["sm", "md", "lg"], default="md"),
        AttributeDoc(name="disabled", description="Blocks interaction (the inner button is disabled).",
                     kind="boolean"),
        AttributeDoc(name="loading", description="Busy state: spinner, aria-busy, interaction blocked.",
                     kind="boolean"),
        AttributeDoc(name="icon-only", description="Square button showing only the state icon; the text stays as the accessible name.",
                     kind="boolean"),
        AttributeDoc(name="label", description="Accessible name in icon-only mode.", kind="string"),
        AttributeDoc(name="block", description="Makes the host a block-level element on its own line.",
                     kind="boolean"),
        AttributeDoc(name="name", description="Form field name; the value is submitted while pressed.",
                     kind="string"),
        AttributeDoc(name="value", description="Value submitted while pressed.", kind="string", default="on"),
        AttributeDoc(name="required", description="An unpressed button makes the form invalid.",
                     kind="boolean"),
    ],
    events=[
        ("mj-change", "Cancelable request fired before the state changes; preventDefault() keeps the old state.",
         "{ pressed: boolean, originalEvent: MouseEvent }"),
        ("change", "Native-style event after the new state is committed (not for a vetoed toggle).", ""),
        ("mj-pressed", "Fired after the new state is committed.", "{ pressed: boolean }"),
    ],
    slots=[
        ("", "The button text; stays the accessible name in icon-only mode.", "Bold"),
        ("icon-off", "Icon shown while not pressed (in both states when icon-on is empty).", _svg("mic")),
        ("icon-on", "Icon shown while pressed (in both states when icon-off is empty).", _svg("mic-off")),
    ],
    properties=[
        ("pressed", "boolean. The on state; setting it fires no events."),
        ("value", "string. Submitted value (the `value` attribute, default \"on\")."),
        ("loading", "boolean. Reflects the `loading` attribute."),
        ("disabled", "boolean. Reflects the `disabled` attribute."),
        ("form", "HTMLFormElement | null. Read-only; the form owner."),
        ("validity", "ValidityState. Read-only; `valueMissing` when required and not pressed."),
        ("validationMessage", "string. Read-only."),
    ],
    methods=[
        ("click()", "Toggles the button as a user click would (mj-change, change, mj-pressed)."),
        ("checkValidity() -> boolean", "Checks the required constraint."),
        ("reportValidity() -> boolean", "Checks and reports the required constraint."),
        ("focus(options)", "Focuses the inner button."),
    ],
    parts=[
        ("button", "The inner native button (carries aria-pressed)."),
        ("spinner", "Busy spinner."),
        ("icon-off", "Wrapper of the icon-off slot."),
        ("icon-on", "Wrapper of the icon-on slot."),
        ("label", "Wrapper of the default slot."),
    ],
    css_properties=[
        ("--mj-toggle-button-bg", "Background while off (default var(--mj-surface))."),
        ("--mj-toggle-button-color", "Text colour while off (default var(--mj-text))."),
        ("--mj-toggle-button-border-color", "Border colour while off (default var(--mj-border-strong))."),
        ("--mj-toggle-button-bg-pressed", "Background while pressed (default var(--mj-accent); primary uses accent-active, tertiary bg-muted)."),
        ("--mj-toggle-button-color-pressed", "Text colour while pressed (default var(--mj-text-on-accent); tertiary accent)."),
        ("--mj-toggle-button-border-color-pressed", "Border colour while pressed (default var(--mj-accent))."),
        ("--mj-toggle-button-border-radius", "Corner radius (default var(--mj-radius-md))."),
        ("--mj-toggle-button-height", "Minimum height of md (default var(--mj-control-height-md))."),
        ("--mj-toggle-button-padding-x", "Inline padding of md (default var(--mj-space-4))."),
        ("--mj-toggle-button-focus-ring-color", "Focus ring colour (default var(--mj-focus-ring))."),
    ],
)


# ---------------------------------------------------------------------------
# mj-disclosure-button
# ---------------------------------------------------------------------------

_PANEL_CSS = _code("""
    .panel {
      margin-block: var(--mj-space-2) var(--mj-space-3);
      padding: var(--mj-space-3) var(--mj-space-4);
      background: var(--mj-surface);
      border: 1px solid var(--mj-border);
      border-radius: var(--mj-radius-md);
    }
    .panel p { margin: 0; }
""")

_DISCLOSURE = ComponentDoc(
    tag="mj-disclosure-button",
    title="Disclosure Button",
    group="buttons",
    summary="A button that shows and hides a related panel, with aria-expanded and a rotating chevron.",
    description=(
        "<p><code>&lt;mj-disclosure-button&gt;</code> is the trigger of a disclosure pattern. "
        "It exposes <code>aria-expanded</code> and, through element reflection, relates its "
        "inner button to the panel named by <code>controls</code> (an id in the button's own "
        "tree, else a CSS selector; a panel added later is still found).</p>"
        "<p>The panel's <code>hidden</code> property follows <code>expanded</code>, so the "
        "button really shows and hides it. Add <code>manual</code> to leave the panel to the "
        "page (for animations, or a wrapper such as an accordion) and react to "
        "<code>mj-expanded</code> yourself.</p>"
        "<p>A click fires the cancelable <code>mj-change</code> first; unless it is cancelled "
        "the state is committed, then <code>change</code> and <code>mj-expanded</code> fire. "
        "A chevron that rotates with the state is shown unless <code>chevron=\"false\"</code>. "
        "Without a variant the button is transparent with the chevron at the end; it is "
        "content-sized unless the host gets a width (for example with <code>block</code>).</p>"
    ),
    how_to_use=(
        "<p>Put the panel's id in <code>controls</code> and the text between the tags; set "
        "<code>expanded</code> for an initially open panel. Listen for <code>mj-expanded</code> "
        "to react, or for <code>mj-change</code> to refuse a change. Use <code>block</code> for "
        "full-width FAQ-style rows and <code>icon-only</code> with a <code>label</code> for "
        "compact triggers.</p>"
    ),
    example="",
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>The button hides <code>#shipping-details</code> on load and shows it when "
                "expanded. Click it, or toggle <code>expanded</code> in Controls.</p>"
            ),
            html=_code("""
                <mj-disclosure-button controls="shipping-details">Shipping details</mj-disclosure-button>
                <div id="shipping-details" class="panel">
                  <p>Orders ship within two business days. Express delivery is available at checkout.</p>
                </div>
            """),
            css=_PANEL_CSS,
        ),
        ComponentExample(
            key="variants",
            title="Variants, sizes and icon",
            description=(
                "<p>The default transparent style, <code>primary</code>, <code>secondary</code> in "
                "<code>sm</code> and <code>lg</code>, one without chevron and one with a leading "
                "<code>icon</code>. Each opens its own panel below the row.</p>"
            ),
            html=_code("""
                <div class="row">
                  <mj-disclosure-button controls="panel-default">Default</mj-disclosure-button>
                  <mj-disclosure-button variant="primary" controls="panel-primary">Primary</mj-disclosure-button>
                  <mj-disclosure-button variant="secondary" size="sm" controls="panel-small">Secondary, small</mj-disclosure-button>
                  <mj-disclosure-button variant="secondary" size="lg" chevron="false" controls="panel-large">Large, no chevron</mj-disclosure-button>
                  <mj-disclosure-button variant="secondary" controls="panel-icon">[[filter|icon]]Filters</mj-disclosure-button>
                </div>
                <div id="panel-default" class="panel"><p>Panel of the default button.</p></div>
                <div id="panel-primary" class="panel"><p>Panel of the primary button.</p></div>
                <div id="panel-small" class="panel"><p>Panel of the small button.</p></div>
                <div id="panel-large" class="panel"><p>Panel of the large button.</p></div>
                <div id="panel-icon" class="panel"><p>Status, owner and due date filters.</p></div>
            """),
            css=_ROW_CSS + "\n" + _PANEL_CSS,
        ),
        ComponentExample(
            key="faq",
            title="FAQ list",
            description=(
                "<p>Full-width (<code>block</code>) rows: the first is <code>expanded</code> on "
                "load, the last is <code>disabled</code> and keeps its panel hidden.</p>"
            ),
            html=_code("""
                <div class="faq">
                  <mj-disclosure-button block expanded controls="faq-1">How do I reset my password?</mj-disclosure-button>
                  <div id="faq-1" class="panel"><p>Use <b>Forgot password</b> on the sign-in page; the link is valid for one hour.</p></div>
                  <mj-disclosure-button block controls="faq-2">Can I change my plan later?</mj-disclosure-button>
                  <div id="faq-2" class="panel"><p>Yes. Upgrades apply at once, downgrades at the end of the billing period.</p></div>
                  <mj-disclosure-button block disabled controls="faq-3">Enterprise billing (coming soon)</mj-disclosure-button>
                  <div id="faq-3" class="panel"><p>Invoiced billing for enterprise accounts.</p></div>
                </div>
            """),
            css=_PANEL_CSS + "\n.faq { max-inline-size: 36rem; border-block-start: 1px solid var(--mj-border); }\n.faq mj-disclosure-button { border-block-end: 1px solid var(--mj-border); }",
        ),
        ComponentExample(
            key="icon-only",
            title="Icon-only trigger",
            description=(
                "<p>A compact <code>icon-only</code> trigger named by its <code>label</code>, "
                "without chevron, that opens a list of project actions.</p>"
            ),
            html=_code("""
                <div class="toolbar">
                  <strong>Project Atlas</strong>
                  <mj-disclosure-button icon-only chevron="false" label="Project actions" controls="project-actions">[[more|icon]]</mj-disclosure-button>
                </div>
                <ul id="project-actions" class="panel">
                  <li>Rename project</li>
                  <li>Archive project</li>
                  <li>Export as CSV</li>
                </ul>
            """),
            css=_PANEL_CSS + "\n.toolbar { display: flex; align-items: center; gap: var(--mj-space-2); }\n.panel { max-inline-size: 16rem; padding-inline-start: var(--mj-space-6); }",
        ),
        ComponentExample(
            key="manual",
            title="Manual panel and veto",
            description=(
                "<p>With <code>manual</code> the page animates the panel itself on "
                "<code>mj-expanded</code>. While <b>Unsaved changes</b> is checked the "
                "<code>mj-change</code> handler refuses to collapse. The script expands it, then "
                "tries to collapse it (vetoed).</p>"
            ),
            html=_code("""
                <div class="row">
                  <mj-disclosure-button id="filters-toggle" manual variant="secondary" controls="filters">[[filter|icon]]Filters</mj-disclosure-button>
                  <label><input type="checkbox" id="unsaved" checked> Unsaved changes</label>
                </div>
                <div id="filters" class="collapsible">
                  <div class="panel">
                    <p>Status: open &middot; Owner: me &middot; Due: this week</p>
                  </div>
                </div>
            """),
            css=_ROW_CSS + "\n" + _PANEL_CSS + "\n" + _code("""
                .collapsible { display: grid; grid-template-rows: 0fr; transition: grid-template-rows var(--mj-motion-medium) var(--mj-motion-ease); }
                .collapsible > .panel { overflow: hidden; min-block-size: 0; }
                .collapsible.is-open { grid-template-rows: 1fr; }
                @media (prefers-reduced-motion: reduce) { .collapsible { transition: none; } }
            """),
            script=_code("""
                const toggle = document.getElementById("filters-toggle")
                const panel = document.getElementById("filters")
                const unsaved = document.getElementById("unsaved")

                toggle.addEventListener("mj-change", (event) => {
                  if (event.detail.expanded === false && unsaved.checked === true) {
                    event.preventDefault()
                    mjSandbox.log("collapse vetoed", { reason: "unsaved changes" })
                  }
                })
                toggle.addEventListener("mj-expanded", (event) => {
                  panel.classList.toggle("is-open", event.detail.expanded)
                })

                // Expand, then try to collapse (refused while "Unsaved changes" is checked).
                toggle.click()
                toggle.click()
            """),
        ),
    ],
    attributes=[
        AttributeDoc(name="controls", description="Id of the controlled panel (in the button's tree), or a CSS selector.",
                     kind="string"),
        AttributeDoc(name="expanded", description="Open state (expanded=\"false\" is closed); the panel's hidden follows it.",
                     kind="boolean"),
        AttributeDoc(name="manual", description="Leaves the panel's visibility to the page; only the state and events change.",
                     kind="boolean"),
        AttributeDoc(name="chevron", description="Set to `false` to hide the rotating chevron.",
                     kind="boolean", default="true"),
        AttributeDoc(name="variant", description="Emphasis. Without it the button is transparent with the chevron at the end.",
                     kind="enum", values=["primary", "secondary"]),
        AttributeDoc(name="size", description="Control height, padding and font size.",
                     kind="enum", values=["sm", "md", "lg"], default="md"),
        AttributeDoc(name="disabled", description="Blocks interaction (the inner button is disabled).",
                     kind="boolean"),
        AttributeDoc(name="icon-only", description="Square button showing only the icon (and chevron); the text stays as the accessible name.",
                     kind="boolean"),
        AttributeDoc(name="label", description="Accessible name in icon-only mode.", kind="string"),
        AttributeDoc(name="block", description="Makes the host block-level; the inner button then spans the line.",
                     kind="boolean"),
    ],
    events=[
        ("mj-change", "Cancelable request fired before the state changes; preventDefault() keeps it.",
         "{ expanded: boolean, originalEvent: MouseEvent }"),
        ("change", "Native-style event after the new state is committed (not for a vetoed change).", ""),
        ("mj-expanded", "Fired after the new state is committed.", "{ expanded: boolean }"),
    ],
    slots=[
        ("", "The button text; stays the accessible name in icon-only mode.", "More details"),
        ("icon", "Leading icon.", _svg("filter")),
    ],
    properties=[
        ("expanded", "boolean. Open state; setting it updates the panel but fires no events."),
        ("controls", "string | null. Reflects the `controls` attribute."),
        ("panelEl", "Element | null. Read-only; the resolved controlled panel."),
        ("disabled", "boolean. Reflects the `disabled` attribute."),
    ],
    methods=[
        ("click()", "Toggles the disclosure as a user click would (mj-change, change, mj-expanded)."),
        ("focus(options)", "Focuses the inner button."),
    ],
    parts=[
        ("button", "The inner native button (carries aria-expanded)."),
        ("icon", "Wrapper of the icon slot."),
        ("label", "Wrapper of the default slot."),
        ("chevron", "The rotating chevron."),
    ],
    css_properties=[
        ("--mj-disclosure-button-bg", "Background while collapsed (default transparent)."),
        ("--mj-disclosure-button-color", "Text colour while collapsed (default var(--mj-text))."),
        ("--mj-disclosure-button-bg-expanded", "Background while expanded (default var(--mj-bg-muted))."),
        ("--mj-disclosure-button-color-expanded", "Text colour while expanded (default var(--mj-text))."),
        ("--mj-disclosure-button-border-radius", "Corner radius (default var(--mj-radius-md))."),
        ("--mj-disclosure-button-height", "Minimum height of md (default var(--mj-control-height-md))."),
        ("--mj-disclosure-button-padding-x", "Inline padding of md (default var(--mj-space-4))."),
        ("--mj-disclosure-button-chevron-size", "Chevron size (default 1em)."),
        ("--mj-disclosure-button-chevron-transition", "Chevron rotation duration (default var(--mj-motion-medium))."),
        ("--mj-disclosure-button-focus-ring-color", "Focus ring colour (default var(--mj-focus-ring))."),
    ],
)


# ---------------------------------------------------------------------------
# mj-copy-button
# ---------------------------------------------------------------------------

_COPY = ComponentDoc(
    tag="mj-copy-button",
    title="Copy Button",
    group="buttons",
    summary="Copies a value or another element's text to the clipboard, with visible and announced confirmation.",
    description=(
        "<p><code>&lt;mj-copy-button&gt;</code> writes text to the clipboard and shows a "
        "transient success or error state (icon, text and colour), announced through the live "
        "region. The text is the <code>value</code> attribute, else the element named by "
        "<code>for</code>: a control with a string <code>value</code> (input, textarea, select, "
        "<code>mj-text-field</code>) is copied by value, any other element by its text "
        "content.</p>"
        "<p>The async Clipboard API is used where available (secure contexts). When it is "
        "missing or refuses, a hidden textarea with <code>execCommand(\"copy\")</code> is tried "
        "before the error state is shown. The state returns to idle after <code>timeout</code> "
        "ms.</p>"
        "<p>The default slot is the visible label; with nothing slotted the <code>label</code> "
        "attribute (default \"Copy\") is shown. Built-in copy, check and warning icons are the "
        "fallbacks of the three icon slots.</p>"
    ),
    how_to_use=(
        "<p>Set <code>value</code> to the literal text, or <code>for</code> to the id of the "
        "element to copy from. Put the label between the tags, or leave the element empty "
        "(whitespace does not count) to show <code>label</code>. Customize the "
        "feedback with <code>success-label</code>, <code>error-label</code> and "
        "<code>timeout</code>, and listen for <code>mj-copy</code> / <code>mj-copy-error</code>.</p>"
    ),
    example="",
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>Copies the install command. Click it: the button shows \"Copied!\" for two "
                "seconds and <code>mj-copy</code> appears in Events.</p>"
            ),
            html=_code("""
                <div class="snippet">
                  <code>pip install codecraftai-webworks</code>
                  <mj-copy-button value="pip install codecraftai-webworks">Copy command</mj-copy-button>
                </div>
            """),
            css=_code("""
                .snippet {
                  display: flex; align-items: center; justify-content: space-between; gap: var(--mj-space-3);
                  max-inline-size: 32rem; padding: var(--mj-space-2) var(--mj-space-3);
                  background: var(--mj-bg-muted); border: 1px solid var(--mj-border); border-radius: var(--mj-radius-md);
                }
            """),
        ),
        ComponentExample(
            key="for",
            title="Copy from another element",
            description=(
                "<p><code>for</code> copies the text of a <code>&lt;code&gt;</code> element and "
                "the current value of an input (edit it, then copy). The second button is "
                "<code>icon-only</code> with a <code>label</code>.</p>"
            ),
            html=_code("""
                <div class="stack">
                  <div class="field">
                    <span>API key</span>
                    <code id="api-key">ccai_live_3f9a2c7e51b84d06</code>
                    <mj-copy-button for="api-key" variant="secondary" size="sm">Copy key</mj-copy-button>
                  </div>
                  <div class="field">
                    <label for="invite-link">Invite link</label>
                    <input id="invite-link" value="https://app.example/invite/7KQ2">
                    <mj-copy-button for="invite-link" icon-only label="Copy invite link"></mj-copy-button>
                  </div>
                </div>
            """),
            css=_ROW_CSS + "\n.field { display: flex; flex-wrap: wrap; align-items: center; gap: var(--mj-space-2); }\n.field > :first-child { min-inline-size: 6rem; }",
        ),
        ComponentExample(
            key="custom",
            title="Labels, icons and variants",
            description=(
                "<p>A <code>primary</code> button labelled only by attributes "
                "(<code>label</code>, <code>success-label</code>, <code>timeout=\"4000\"</code>), "
                "one with custom <code>icon-copy</code> / <code>icon-success</code> icons, a small "
                "secondary one and a disabled one.</p>"
            ),
            html=_code("""
                <div class="row">
                  <mj-copy-button value="#2563eb" variant="primary" label="Copy colour" success-label="Colour copied" timeout="4000"></mj-copy-button>
                  <mj-copy-button value="ORDER-58213" variant="secondary" size="lg">[[clipboard|icon-copy]][[check-circle|icon-success]]Copy order number</mj-copy-button>
                  <mj-copy-button value="sm" variant="secondary" size="sm">Small</mj-copy-button>
                  <mj-copy-button value="never" disabled>Disabled</mj-copy-button>
                </div>
            """),
            css=_ROW_CSS,
        ),
        ComponentExample(
            key="error",
            title="Error state and events",
            description=(
                "<p>The script replaces the clipboard with one that refuses every write, then "
                "clicks the button: it shows <code>error-label</code>, fires "
                "<code>mj-copy-error</code> and returns to idle after <code>timeout</code>.</p>"
            ),
            html=_code("""
                <mj-copy-button id="token-copy" value="tok_9d1e" error-label="Clipboard blocked" timeout="3000">Copy token</mj-copy-button>
                <p id="copy-status" class="note"></p>
            """),
            css=_ROW_CSS,
            script=_code("""
                // Simulate a browser that refuses clipboard access (both the API and the fallback).
                Object.defineProperty(navigator, "clipboard", {
                  configurable: true,
                  value: { writeText: () => Promise.reject(new DOMException("Write permission denied.", "NotAllowedError")) }
                })
                document.execCommand = () => false

                const button = document.getElementById("token-copy")
                const status = document.getElementById("copy-status")
                button.addEventListener("mj-copy-error", (event) => {
                  status.textContent = "status = " + button.status + " (" + event.detail.error.message + ")"
                  mjSandbox.log("copy failed", { status: button.status, error: event.detail.error.name })
                })
                button.addEventListener("mj-copy", (event) => {
                  status.textContent = "Copied: " + event.detail.value
                })

                button.click()
            """),
        ),
    ],
    attributes=[
        AttributeDoc(name="value", description="Literal text to copy (wins over `for`).", kind="string"),
        AttributeDoc(name="for", description="Id of the element to copy from: its value when it has one, else its text.",
                     kind="string"),
        AttributeDoc(name="label", description="Idle text when nothing is slotted, and the accessible name.",
                     kind="string", default="Copy"),
        AttributeDoc(name="success-label", description="Text shown and announced after a copy.",
                     kind="string", default="Copied!"),
        AttributeDoc(name="error-label", description="Text shown and announced when copying fails.",
                     kind="string", default="Copy failed"),
        AttributeDoc(name="timeout", description="Milliseconds before the success / error state returns to idle.",
                     kind="number", default="2000"),
        AttributeDoc(name="variant", description="Emphasis. Without it the button is transparent.",
                     kind="enum", values=["primary", "secondary"]),
        AttributeDoc(name="size", description="Control height, padding and font size.",
                     kind="enum", values=["sm", "md", "lg"], default="md"),
        AttributeDoc(name="disabled", description="Blocks copying (the inner button is disabled).",
                     kind="boolean"),
        AttributeDoc(name="icon-only", description="Square button showing only the icon; the accessible name is kept.",
                     kind="boolean"),
    ],
    events=[
        ("mj-copy", "The text was copied.", "{ value: string }"),
        ("mj-copy-error", "Copying failed (Clipboard API and fallback).", "{ error: Error }"),
    ],
    slots=[
        ("", "The idle label; replaces the `label` text.", "Copy link"),
        ("icon-copy", "Idle icon (built-in copy icon when empty).", _svg("clipboard")),
        ("icon-success", "Icon of the success state (built-in check when empty).", _svg("check-circle")),
        ("icon-error", "Icon of the error state (built-in warning when empty).", _svg("help")),
    ],
    properties=[
        ("status", "'idle' | 'success' | 'error'. Read-only; also reflected as data-status on the host while not idle."),
        ("sourceEl", "Element | null. Read-only; the element named by `for`."),
        ("disabled", "boolean. Reflects the `disabled` attribute."),
    ],
    methods=[
        ("click()", "Copies as a user click would (mj-copy or mj-copy-error)."),
        ("focus(options)", "Focuses the inner button."),
    ],
    parts=[
        ("button", "The inner native button."),
        ("icon-copy", "Wrapper of the idle icon."),
        ("icon-success", "Wrapper of the success icon."),
        ("icon-error", "Wrapper of the error icon."),
        ("label", "Label wrapper (idle slot or status text)."),
    ],
    css_properties=[
        ("--mj-copy-button-bg", "Background (default transparent)."),
        ("--mj-copy-button-color", "Text colour (default var(--mj-text))."),
        ("--mj-copy-button-bg-success", "Background of the success state (default var(--mj-color-success-surface))."),
        ("--mj-copy-button-color-success", "Text colour of the success state (default var(--mj-color-success))."),
        ("--mj-copy-button-bg-error", "Background of the error state (default var(--mj-color-danger-surface))."),
        ("--mj-copy-button-color-error", "Text colour of the error state (default var(--mj-color-danger))."),
        ("--mj-copy-button-border-radius", "Corner radius (default var(--mj-radius-md))."),
        ("--mj-copy-button-height", "Minimum height of md (default var(--mj-control-height-md))."),
        ("--mj-copy-button-transition", "State transition duration (default var(--mj-motion-fast))."),
        ("--mj-copy-button-focus-ring-color", "Focus ring colour (default var(--mj-focus-ring))."),
    ],
)


# ---------------------------------------------------------------------------
# mj-share-button
# ---------------------------------------------------------------------------

_SHARE_ITEM_CSS = _code("""
    .extra-item {
      display: flex; inline-size: 100%;
      padding: var(--mj-space-2) var(--mj-space-3);
      font: inherit; font-size: var(--mj-font-size-sm);
      color: var(--mj-text); background: none; border: none; text-align: start; cursor: pointer;
    }
    .extra-item:hover { background: var(--mj-bg-muted); }
""")

_SHARE = ComponentDoc(
    tag="mj-share-button",
    title="Share Button",
    group="buttons",
    summary="Shares a link through the system share sheet, or a fallback menu with Copy link, Email and custom targets.",
    description=(
        "<p><code>&lt;mj-share-button&gt;</code> calls the Web Share API "
        "(<code>navigator.share</code>) where it exists and accepts the data; a share sheet "
        "the user dismisses is not an error. Elsewhere, or with <code>force-menu</code>, it "
        "opens a menu with <b>Copy link</b>, <b>Email</b>, one entry per "
        "<code>shareTargets</code> item and the slotted <code>menu-item</code> elements. The "
        "menu supports Arrow keys / Home / End, closes on Escape, Tab, a click outside or focus "
        "leaving, and returns focus to the button after a choice.</p>"
        "<p>The shared data is <code>shareData</code> when set, else <code>share-url</code> "
        "(default the page URL), <code>share-title</code> (default the document title) and "
        "<code>share-text</code>. A built-in share icon fills the <code>icon</code> slot when it "
        "is empty. Copy link uses the Clipboard API with an <code>execCommand</code> fallback; "
        "when both fail <code>mj-share-error</code> fires with "
        "<code>target: 'copy-link'</code>.</p>"
        "<p>Whether a desktop browser has a share sheet varies (Chromium on Linux has none), so "
        "use <code>force-menu</code> for a deterministic menu.</p>"
    ),
    how_to_use=(
        "<p>Set <code>share-url</code>, <code>share-title</code> and optionally "
        "<code>share-text</code>, and put the label between the tags. Add targets from script "
        "with <code>shareTargets = [{ label, href }]</code> or <code>{ label, handler(data, "
        "target) }</code>, or slot your own <code>&lt;button slot=\"menu-item\" "
        "role=\"menuitem\"&gt;</code>. Listen for <code>mj-share</code> (native sheet) and "
        "<code>mj-share-select</code> (menu entries).</p>"
    ),
    example="",
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>Shares an article: the system share sheet where the browser has one, "
                "otherwise the fallback menu. Click it and watch Events.</p>"
            ),
            html=_code("""
                <mj-share-button share-url="https://example.com/articles/designing-for-focus" share-title="Designing for focus" share-text="A short guide to visible focus states.">Share article</mj-share-button>
            """),
            height=200,
        ),
        ComponentExample(
            key="menu",
            title="Fallback menu with targets",
            description=(
                "<p><code>force-menu</code> with two <code>shareTargets</code> (a handler and a "
                "link) and a slotted <code>menu-item</code>. The script opens the menu; use the "
                "Arrow keys to move through it.</p>"
            ),
            html=_code("""
                <mj-share-button id="report-share" force-menu share-url="https://example.com/reports/q3" share-title="Q3 report" menu-label="Share the Q3 report">
                  Share report
                  <button slot="menu-item" type="button" role="menuitem" class="extra-item" id="qr-item">Show QR code</button>
                </mj-share-button>
            """),
            css=_SHARE_ITEM_CSS,
            script=_code("""
                const share = document.getElementById("report-share")
                share.shareTargets = [
                  { label: "Post to team chat", handler: (data) => mjSandbox.log("team chat handler", data) },
                  { label: "Open in a new tab", href: "https://example.com/reports/q3" }
                ]
                document.getElementById("qr-item").addEventListener("click", () => {
                  mjSandbox.log("slotted item clicked", { id: "qr-item" })
                })

                share.click()
            """),
            height=300,
        ),
        ComponentExample(
            key="variants",
            title="Variants, sizes and states",
            description=(
                "<p><code>primary</code> and <code>tertiary</code>, the three sizes, an "
                "<code>icon-only</code> button named by <code>label</code>, a custom "
                "<code>icon</code>, and the <code>loading</code> and <code>disabled</code> "
                "states.</p>"
            ),
            html=_code("""
                <div class="stack">
                  <div class="row">
                    <mj-share-button force-menu variant="primary" share-url="https://example.com/a">Share</mj-share-button>
                    <mj-share-button force-menu share-url="https://example.com/a">Default</mj-share-button>
                    <mj-share-button force-menu variant="tertiary" share-url="https://example.com/a">Tertiary</mj-share-button>
                    <mj-share-button force-menu icon-only label="Share this page" share-url="https://example.com/a"></mj-share-button>
                    <mj-share-button force-menu share-url="https://example.com/a">[[link|icon]]Copy or send</mj-share-button>
                  </div>
                  <div class="row">
                    <mj-share-button force-menu size="sm" share-url="https://example.com/a">Small</mj-share-button>
                    <mj-share-button force-menu size="lg" share-url="https://example.com/a">Large</mj-share-button>
                    <mj-share-button force-menu loading share-url="https://example.com/a">Sharing</mj-share-button>
                    <mj-share-button force-menu disabled share-url="https://example.com/a">Disabled</mj-share-button>
                  </div>
                </div>
            """),
            css=_ROW_CSS,
            height=260,
        ),
        ComponentExample(
            key="events",
            title="Share data and events",
            description=(
                "<p>The script sets <code>shareData</code> and a <code>shareTargets</code> handler, "
                "opens the menu and chooses that target: Events shows <code>mj-menu-open</code>, "
                "<code>mj-menu-close</code> and <code>mj-share-select</code>. Choosing <b>Copy "
                "link</b> yourself fires <code>mj-share-select</code>, or "
                "<code>mj-share-error</code> when the browser refuses the clipboard.</p>"
            ),
            html=_code("""
                <mj-share-button id="event-share" force-menu>Share invite</mj-share-button>
                <p id="share-status" class="note"></p>
            """),
            css=_ROW_CSS,
            script=_code("""
                const share = document.getElementById("event-share")
                const status = document.getElementById("share-status")
                share.shareData = { url: "https://example.com/invite/7KQ2", title: "Join the Atlas project" }

                share.addEventListener("mj-share-select", (event) => {
                  status.textContent = "Chosen: " + event.detail.target + " (" + event.detail.data.url + ")"
                })
                share.addEventListener("mj-share-error", (event) => {
                  status.textContent = "Could not copy the link (" + event.detail.target + ")"
                })

                share.shareTargets = [
                  { label: "Send to a teammate", handler: (data) => mjSandbox.log("handler called", { url: data.url }) }
                ]

                share.click()
                share.shadowRoot.querySelector(".target-item").click()
            """),
            height=220,
        ),
    ],
    attributes=[
        AttributeDoc(name="share-url", description="URL to share (default the page URL).", kind="string"),
        AttributeDoc(name="share-title", description="Title of the shared content (default document.title).", kind="string"),
        AttributeDoc(name="share-text", description="Optional descriptive text.", kind="string"),
        AttributeDoc(name="force-menu", description="Always use the fallback menu, even where a share sheet exists.",
                     kind="boolean"),
        AttributeDoc(name="label", description="Accessible name when icon-only or when no text is slotted.",
                     kind="string", default="Share"),
        AttributeDoc(name="menu-label", description="Accessible name of the fallback menu.",
                     kind="string", default="Share via"),
        AttributeDoc(name="variant", description="Emphasis. Without it the button is outlined.",
                     kind="enum", values=["primary", "tertiary"]),
        AttributeDoc(name="size", description="Control height, padding and font size.",
                     kind="enum", values=["sm", "md", "lg"], default="md"),
        AttributeDoc(name="loading", description="Busy state (also set while the native sheet is open); blocks activation.",
                     kind="boolean"),
        AttributeDoc(name="disabled", description="Blocks activation (the inner button is disabled).",
                     kind="boolean"),
        AttributeDoc(name="icon-only", description="Square button showing only the icon; named by `label`.",
                     kind="boolean"),
    ],
    events=[
        ("mj-share", "The native share sheet completed.", "{ method: 'native', data: ShareData }"),
        ("mj-share-error", "The native share failed (not a user dismissal), or Copy link could not copy.",
         "{ error: Error, target?: 'copy-link' }"),
        ("mj-share-select", "A menu entry was chosen: copy-link, email, or a shareTargets item.",
         "{ target: 'copy-link' | 'email' | string, item?: object, data: ShareData }"),
        ("mj-menu-open", "The fallback menu opened.", "{}"),
        ("mj-menu-close", "The fallback menu closed.", "{}"),
    ],
    slots=[
        ("", "The button text.", "Share"),
        ("icon", "Button icon (built-in share icon when empty).", _svg("link")),
        (
            "menu-item",
            "Extra menu entries after the built-in ones; give them role=menuitem and handle their click.",
            '<button type="button" role="menuitem">Copy as Markdown</button>',
        ),
    ],
    properties=[
        ("shareData", "ShareData | null. Overrides the share-* attributes when set."),
        ("shareTargets", "Array<{ label: string, href?: string, handler?: (data, target) => void }>. Extra menu entries; href opens in a new tab (unsafe schemes ignored)."),
        ("canShare", "boolean. Read-only; true when the native share sheet will be used."),
        ("loading", "boolean. Reflects the `loading` attribute."),
        ("disabled", "boolean. Reflects the `disabled` attribute."),
    ],
    methods=[
        ("click()", "Shares as a user click would: the share sheet, or the fallback menu."),
        ("focus(options)", "Focuses the inner button."),
    ],
    parts=[
        ("button", "The inner native button."),
        ("spinner", "Busy spinner."),
        ("icon", "Icon wrapper."),
        ("label", "Label wrapper."),
        ("fallback-menu", "The fallback menu list."),
        ("menu-item", "Each built-in and shareTargets menu entry."),
    ],
    css_properties=[
        ("--mj-share-button-bg", "Background (default var(--mj-surface))."),
        ("--mj-share-button-color", "Text colour (default var(--mj-text))."),
        ("--mj-share-button-border-color", "Border colour (default var(--mj-border-strong))."),
        ("--mj-share-button-border-radius", "Corner radius (default var(--mj-radius-md))."),
        ("--mj-share-button-height", "Minimum height of md (default var(--mj-control-height-md))."),
        ("--mj-share-button-menu-width", "Minimum menu width (default 12rem)."),
        ("--mj-share-button-focus-ring-color", "Focus ring colour (default var(--mj-focus-ring))."),
    ],
)


# ---------------------------------------------------------------------------
# mj-favorite-button
# ---------------------------------------------------------------------------

_FAVORITE = ComponentDoc(
    tag="mj-favorite-button",
    title="Favorite Button",
    group="buttons",
    summary="A like / favorite / bookmark toggle with built-in icons, a count, optimistic updates and rollback.",
    description=(
        "<p><code>&lt;mj-favorite-button&gt;</code> toggles a like, favorite or bookmark. "
        "<code>flavor</code> picks the built-in outline / filled icon pair (star, heart, "
        "bookmark) and the default accessible names; slotted <code>icon-off</code> / "
        "<code>icon-on</code> icons replace them.</p>"
        "<p>A click updates the state at once (optimistically): the cancelable "
        "<code>mj-change</code> fires first, then the state is committed and "
        "<code>change</code> and <code>mj-pressed</code> fire. While the save runs, set "
        "<code>pending</code> to block further clicks. If the save fails call "
        "<code>rollback()</code> (fires <code>mj-rollback</code>); clearing <code>pending</code> "
        "or calling <code>commit()</code> accepts the state, after which rollback does "
        "nothing.</p>"
        "<p><code>count</code> is shown next to the icon and in the accessible name. The "
        "component does not change it: update it from your handler. Counts from 1,000 use "
        "compact notation (1.2K) and counts above <code>count-max</code> (default 9999) show as "
        "<code>9999+</code>; a changed count is announced.</p>"
        "<p>Naming: by default the name stays the same (<code>label-off</code> or the flavor "
        "default, such as \"Like\") and <code>aria-pressed</code> carries the state. When "
        "<code>label-on</code> is given the name changes with the state instead and "
        "<code>aria-pressed</code> is omitted. The accessible name always comes from these "
        "attributes, not from the slotted text.</p>"
    ),
    how_to_use=(
        "<p>Set <code>flavor</code>, optional <code>pressed</code> and <code>count</code>, and "
        "an optional visible label between the tags. On <code>mj-pressed</code> adjust "
        "<code>count</code>, set <code>pending</code>, save, then clear <code>pending</code> "
        "(success) or call <code>rollback()</code> (failure).</p>"
    ),
    example="",
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>A like button with a count. The script adjusts <code>count</code> on "
                "<code>mj-pressed</code>, as an application would.</p>"
            ),
            html=_code("""
                <mj-favorite-button id="like" flavor="like" count="42"></mj-favorite-button>
            """),
            script=_code("""
                const like = document.getElementById("like")
                like.addEventListener("mj-pressed", (event) => {
                  like.count = like.count + (event.detail.pressed === true ? 1 : -1)
                })
            """),
        ),
        ComponentExample(
            key="flavors",
            title="Flavors",
            description=(
                "<p>The three flavors off and on, with visible text, and an "
                "<code>icon-only</code> bookmark named by its flavor default.</p>"
            ),
            html=_code("""
                <div class="row">
                  <mj-favorite-button flavor="favorite">Favorite</mj-favorite-button>
                  <mj-favorite-button flavor="favorite" pressed>Favorite</mj-favorite-button>
                  <mj-favorite-button flavor="like">Like</mj-favorite-button>
                  <mj-favorite-button flavor="like" pressed>Like</mj-favorite-button>
                  <mj-favorite-button flavor="bookmark">Bookmark</mj-favorite-button>
                  <mj-favorite-button flavor="bookmark" pressed>Bookmark</mj-favorite-button>
                  <mj-favorite-button flavor="bookmark" icon-only></mj-favorite-button>
                </div>
            """),
            css=_ROW_CSS,
        ),
        ComponentExample(
            key="counts",
            title="Count formatting",
            description=(
                "<p>0, 999, 1,234 (compact 1.2K), 98,765 with <code>count-max=\"99999\"</code> "
                "(98.8K), 12,000 above the default <code>count-max</code> (9999+) and 150 with "
                "<code>count-max=\"99\"</code> (99+).</p>"
            ),
            html=_code("""
                <div class="row">
                  <mj-favorite-button flavor="like" count="0"></mj-favorite-button>
                  <mj-favorite-button flavor="like" count="999"></mj-favorite-button>
                  <mj-favorite-button flavor="like" count="1234"></mj-favorite-button>
                  <mj-favorite-button flavor="like" count="98765" count-max="99999"></mj-favorite-button>
                  <mj-favorite-button flavor="like" count="12000"></mj-favorite-button>
                  <mj-favorite-button flavor="favorite" count="150" count-max="99"></mj-favorite-button>
                </div>
            """),
            css=_ROW_CSS,
        ),
        ComponentExample(
            key="custom",
            title="Custom icons, labels and variants",
            description=(
                "<p>A follow button with its own icons and <code>label-off</code> / "
                "<code>label-on</code> (the name changes, no <code>aria-pressed</code>); page CSS "
                "swaps the visible text on <code>[pressed]</code>. Then <code>primary</code>, the "
                "sizes and <code>disabled</code>.</p>"
            ),
            html=_code("""
                <div class="row">
                  <mj-favorite-button variant="secondary" label-off="Follow Ada" label-on="Unfollow Ada">[[user-plus|icon-off]][[user-check|icon-on]]<span class="when-off">Follow</span><span class="when-on">Following</span></mj-favorite-button>
                  <mj-favorite-button variant="primary" flavor="favorite" pressed>Starred</mj-favorite-button>
                  <mj-favorite-button size="sm" flavor="like">Small</mj-favorite-button>
                  <mj-favorite-button size="lg" flavor="like">Large</mj-favorite-button>
                  <mj-favorite-button disabled flavor="bookmark" count="3">Disabled</mj-favorite-button>
                </div>
            """),
            css=_ROW_CSS + "\nmj-favorite-button:not([pressed]) .when-on,\nmj-favorite-button[pressed] .when-off { display: none; }",
        ),
        ComponentExample(
            key="optimistic",
            title="Pending, commit and rollback",
            description=(
                "<p>Each click sets <code>pending</code> and simulates a 1.2 s save. With "
                "<b>Make the save fail</b> checked the handler calls <code>rollback()</code>. "
                "The script runs one successful and one failing save.</p>"
            ),
            html=_code("""
                <div class="row">
                  <mj-favorite-button id="save-article" flavor="bookmark" count="17">Save</mj-favorite-button>
                  <label><input type="checkbox" id="fail-save"> Make the save fail</label>
                </div>
                <p id="save-status" class="note" role="status"></p>
            """),
            css=_ROW_CSS,
            script=_code("""
                const button = document.getElementById("save-article")
                const fail = document.getElementById("fail-save")
                const status = document.getElementById("save-status")

                button.addEventListener("mj-pressed", (event) => {
                  const pressed = event.detail.pressed
                  button.count = button.count + (pressed === true ? 1 : -1)
                  button.pending = true
                  status.textContent = "Saving..."
                  setTimeout(() => {
                    if (fail.checked === true) {
                      button.pending = false
                      button.rollback()
                      button.count = button.count + (pressed === true ? -1 : 1)
                      status.textContent = "The save failed; the change was rolled back."
                    } else {
                      button.pending = false
                      status.textContent = pressed === true ? "Saved to your reading list." : "Removed from your reading list."
                    }
                  }, 1200)
                })
                button.addEventListener("mj-rollback", (event) => mjSandbox.log("rolled back", event.detail))

                // One successful save, then one that fails.
                button.click()
                setTimeout(() => { fail.checked = true; button.click() }, 1600)
                setTimeout(() => { fail.checked = false }, 3200)
            """),
        ),
    ],
    attributes=[
        AttributeDoc(name="flavor", description="Built-in icon pair and default names (Favorite / Like / Bookmark).",
                     kind="enum", values=["favorite", "like", "bookmark"], default="favorite"),
        AttributeDoc(name="pressed", description="The on state; updated by clicks and rollback().", kind="boolean"),
        AttributeDoc(name="count", description="Non-negative tally shown next to the icon and in the accessible name.",
                     kind="number"),
        AttributeDoc(name="count-max", description="Counts above it show as `<count-max>+`.",
                     kind="number", default="9999"),
        AttributeDoc(name="label-off", description="Accessible name (stable unless label-on is set).",
                     kind="string", values=["Favorite", "Like", "Bookmark"]),
        AttributeDoc(name="label-on", description="Name while pressed; when set the name changes and aria-pressed is omitted.",
                     kind="string", values=["Unfavorite", "Unlike", "Remove bookmark"]),
        AttributeDoc(name="pending", description="A save is in flight: spinner, aria-busy, clicks blocked; clearing it commits.",
                     kind="boolean"),
        AttributeDoc(name="variant", description="Emphasis. Without it the button is transparent.",
                     kind="enum", values=["primary", "secondary"]),
        AttributeDoc(name="size", description="Control height, padding and font size.",
                     kind="enum", values=["sm", "md", "lg"], default="md"),
        AttributeDoc(name="disabled", description="Blocks interaction (the inner button is disabled).", kind="boolean"),
        AttributeDoc(name="icon-only", description="Square button showing only the icon (and count).", kind="boolean"),
    ],
    events=[
        ("mj-change", "Cancelable request fired before the state changes.",
         "{ pressed: boolean, previousPressed: boolean, originalEvent: MouseEvent }"),
        ("change", "Native-style event after the optimistic state is committed.", ""),
        ("mj-pressed", "Fired after the optimistic state is committed.", "{ pressed: boolean }"),
        ("mj-rollback", "rollback() reverted the last uncommitted toggle.", "{ pressed: boolean }"),
    ],
    slots=[
        ("", "Optional visible label (the accessible name comes from label-off / label-on).", "Save"),
        ("icon-off", "Icon while not pressed (built-in flavor outline when empty).", _svg("user-plus")),
        ("icon-on", "Icon while pressed (built-in filled flavor icon when empty).", _svg("user-check")),
    ],
    properties=[
        ("pressed", "boolean. The committed state; setting it is authoritative (nothing to roll back)."),
        ("optimisticPressed", "boolean. Read-only; the state currently shown."),
        ("pending", "boolean. Reflects the `pending` attribute."),
        ("count", "number | undefined. The count; setting null removes it."),
        ("disabled", "boolean. Reflects the `disabled` attribute."),
    ],
    methods=[
        ("click()", "Toggles the button as a user click would (mj-change, change, mj-pressed)."),
        ("commit()", "Accepts the optimistic state; a later rollback() does nothing."),
        ("rollback()", "Reverts the last uncommitted user toggle and fires mj-rollback (logs and returns when nothing is pending)."),
        ("focus(options)", "Focuses the inner button."),
    ],
    parts=[
        ("button", "The inner native button."),
        ("spinner", "Pending spinner."),
        ("icon-off", "Wrapper of the off icon."),
        ("icon-on", "Wrapper of the on icon."),
        ("label", "Wrapper of the default slot."),
        ("count", "The visible count."),
    ],
    css_properties=[
        ("--mj-favorite-button-color-off", "Colour while off (default var(--mj-text-muted))."),
        ("--mj-favorite-button-color-on", "Colour while on (default var(--mj-color-danger); primary text-on-accent)."),
        ("--mj-favorite-button-bg-off", "Background while off (default transparent)."),
        ("--mj-favorite-button-bg-on", "Background while on (default transparent; primary accent-active)."),
        ("--mj-favorite-button-border-radius", "Corner radius (default var(--mj-radius-md))."),
        ("--mj-favorite-button-height", "Minimum height of md (default var(--mj-control-height-md))."),
        ("--mj-favorite-button-count-font-size", "Count font size (default var(--mj-font-size-sm))."),
        ("--mj-favorite-button-animation-duration", "Press pop animation (default 300ms)."),
        ("--mj-favorite-button-focus-ring-color", "Focus ring colour (default var(--mj-focus-ring))."),
    ],
)


# ---------------------------------------------------------------------------
# mj-download-button
# ---------------------------------------------------------------------------

_DOWNLOAD = ComponentDoc(
    tag="mj-download-button",
    title="Download Button",
    group="buttons",
    summary="A button-styled link that downloads a file, with an interceptable start event for custom flows.",
    description=(
        "<p><code>&lt;mj-download-button&gt;</code> renders a real <code>&lt;a download&gt;</code> "
        "so the browser handles the transfer, middle-click opens a new tab and the URL appears "
        "in the download UI. <code>filename</code> suggests the saved name.</p>"
        "<p>Only relative, http(s), blob:, mailto:, tel:, sms: and data: URLs reach the anchor; "
        "any other scheme (such as <code>javascript:</code>) is dropped with a console warning. "
        "Without a usable <code>href</code> the button is still a focusable link (Enter activates "
        "it) that only fires <code>mj-download-start</code>, so a listener can produce the file "
        "itself; with no such listener nothing is downloaded.</p>"
        "<p>Each click fires the cancelable <code>mj-download-start</code>. Call "
        "<code>preventDefault()</code> to run your own flow (signed URL, generated file, "
        "progress) instead of the plain download, and show <code>loading</code> meanwhile. "
        "<code>loading</code> keeps the button in the tab order with <code>aria-busy</code>; "
        "<code>disabled</code> removes it. Both set <code>aria-disabled</code> and swallow "
        "clicks. Inside <code>&lt;mj-toolbar&gt;</code> the toolbar's roving tab stop is kept "
        "when the button's attributes change.</p>"
    ),
    how_to_use=(
        "<p>Set <code>href</code> and <code>filename</code>, and put the text (and an optional "
        "icon) between the tags. <code>variant</code> and <code>size</code> mirror "
        "<code>&lt;mj-button&gt;</code>. For an icon-only button add <code>icon-only</code> and "
        "a <code>label</code>.</p>"
    ),
    example="",
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>Downloads a small CSV served as a <code>data:</code> URL as "
                "<code>q3-sales.csv</code>. <code>mj-download-start</code> appears in Events.</p>"
            ),
            html=(
                '<mj-download-button href="' + _CSV_HREF + '" filename="q3-sales.csv" variant="primary">'
                + _svg("download") + "Download CSV</mj-download-button>"
            ),
        ),
        ComponentExample(
            key="variants",
            title="Variants, sizes and block",
            description=(
                "<p>Default, <code>primary</code>, <code>tertiary</code> and <code>link</code>, "
                "the three sizes, and a <code>block</code> button.</p>"
            ),
            html=_code("""
                <div class="stack">
                  <div class="row">
                    <mj-download-button href="HREF" filename="report.csv">Default</mj-download-button>
                    <mj-download-button href="HREF" filename="report.csv" variant="primary">Primary</mj-download-button>
                    <mj-download-button href="HREF" filename="report.csv" variant="tertiary">Tertiary</mj-download-button>
                    <mj-download-button href="HREF" filename="report.csv" variant="link">Link</mj-download-button>
                  </div>
                  <div class="row">
                    <mj-download-button href="HREF" filename="report.csv" size="sm">Small</mj-download-button>
                    <mj-download-button href="HREF" filename="report.csv">Medium</mj-download-button>
                    <mj-download-button href="HREF" filename="report.csv" size="lg">Large</mj-download-button>
                  </div>
                  <mj-download-button href="HREF" filename="report.csv" block variant="primary">[[download]]Download the full report</mj-download-button>
                </div>
            """).replace("HREF", _CSV_HREF),
            css=_ROW_CSS,
        ),
        ComponentExample(
            key="states",
            title="Loading, disabled and icon-only",
            description=(
                "<p><code>loading</code> (spinner, still focusable), <code>disabled</code> (out of "
                "the tab order), an <code>icon-only</code> button named by <code>label</code>, and "
                "<code>target=\"_blank\"</code> (rel defaults to noopener noreferrer). The anchor "
                "always carries <code>download</code>, so the last one saves "
                "<code>index.js</code> rather than opening it.</p>"
            ),
            html=_code("""
                <div class="row">
                  <mj-download-button href="HREF" filename="report.csv" loading>Preparing&hellip;</mj-download-button>
                  <mj-download-button href="HREF" filename="report.csv" disabled>Disabled</mj-download-button>
                  <mj-download-button href="HREF" filename="report.csv" icon-only label="Download report">[[download]]</mj-download-button>
                  <mj-download-button href="/static/javascript/index.js" filename="index.js" target="_blank">Download index.js</mj-download-button>
                </div>
            """).replace("HREF", _CSV_HREF),
            css=_ROW_CSS,
        ),
        ComponentExample(
            key="events",
            title="Custom download flow",
            description=(
                "<p>The button has no <code>href</code>: the <code>mj-download-start</code> handler "
                "cancels the event, shows <code>loading</code>, generates a JSON file and saves it "
                "through a blob URL. Without an href the button is still a link in the tab order; "
                "Tab to it and press Enter, or click it, to save the file. The script runs the flow "
                "once on load without saving.</p>"
            ),
            html=_code("""
                <mj-download-button id="export" filename="invoices.json">[[download]]Export invoices</mj-download-button>
                <p id="export-status" class="note"></p>
            """),
            css=_ROW_CSS,
            script=_code("""
                const button = document.getElementById("export")
                const status = document.getElementById("export-status")
                let dryRun = false

                button.addEventListener("mj-download-start", (event) => {
                  event.preventDefault()
                  button.loading = true
                  status.textContent = "Generating " + event.detail.filename + "..."
                  const saveFile = dryRun === false
                  setTimeout(() => {
                    const rows = [{ id: "INV-1042", total: 1200 }, { id: "INV-1043", total: 980 }]
                    const blob = new Blob([JSON.stringify(rows, null, 2)], { type: "application/json" })
                    mjSandbox.log("generated", { filename: event.detail.filename, bytes: blob.size })
                    if (saveFile === true) {
                      const link = document.createElement("a")
                      link.href = URL.createObjectURL(blob)
                      link.download = event.detail.filename
                      link.click()
                      setTimeout(() => URL.revokeObjectURL(link.href), 1000)
                    }
                    button.loading = false
                    status.textContent = saveFile === true ? "Saved " + event.detail.filename + "." : "Ready (dry run, nothing saved)."
                  }, 800)
                })

                // Run the flow once without saving a file.
                dryRun = true
                button.click()
                dryRun = false
            """),
        ),
    ],
    attributes=[
        AttributeDoc(name="href", description="URL of the file; schemes other than http(s), relative, blob, mailto, tel, sms and data are ignored. Without a usable href the button stays a focusable link that only fires mj-download-start.",
                     kind="string"),
        AttributeDoc(name="filename", description="Suggested file name (the anchor always carries download).",
                     kind="string"),
        AttributeDoc(name="variant", description="Emphasis. Without it the button is outlined.",
                     kind="enum", values=["primary", "tertiary", "link"]),
        AttributeDoc(name="size", description="Control height, padding and font size.",
                     kind="enum", values=["sm", "md", "lg"], default="md"),
        AttributeDoc(name="loading", description="Busy: spinner, aria-busy, clicks swallowed; stays focusable.",
                     kind="boolean"),
        AttributeDoc(name="disabled", description="Clicks swallowed, aria-disabled, removed from the tab order.",
                     kind="boolean"),
        AttributeDoc(name="icon-only", description="Square button (put only an icon between the tags and set label).",
                     kind="boolean"),
        AttributeDoc(name="label", description="Accessible name (aria-label of the anchor).", kind="string"),
        AttributeDoc(name="block", description="Full-width button.", kind="boolean"),
        AttributeDoc(name="target", description="Anchor target.", kind="string", values=["_self", "_blank"]),
        AttributeDoc(name="rel", description="Anchor rel; defaults to `noopener noreferrer` with target=_blank.",
                     kind="string"),
    ],
    events=[
        ("mj-download-start", "Fired on every click that is not blocked. Cancelable: preventDefault() stops the browser download.",
         "{ href: string, filename: string }"),
    ],
    slots=[
        ("", "Button content: text and an optional inline icon.", _svg("download") + "Download"),
    ],
    properties=[
        ("href", "string. Reflects the `href` attribute (\"\" when absent)."),
        ("filename", "string. Reflects the `filename` attribute."),
        ("loading", "boolean. Reflects the `loading` attribute."),
        ("disabled", "boolean. Reflects the `disabled` attribute."),
    ],
    methods=[
        ("click()", "Starts the download as a user click would (mj-download-start first)."),
    ],
    parts=[
        ("button", "The inner anchor."),
        ("spinner", "Busy spinner."),
    ],
    css_properties=[
        ("--mj-download-button-bg", "Background (default var(--mj-surface))."),
        ("--mj-download-button-color", "Text colour (default var(--mj-text))."),
        ("--mj-download-button-border-color", "Border colour (default var(--mj-border-strong))."),
        ("--mj-download-button-border-radius", "Corner radius (default var(--mj-radius-md))."),
        ("--mj-download-button-height", "Minimum height of md (default var(--mj-control-height-md))."),
        ("--mj-download-button-font-weight", "Font weight (default var(--mj-font-weight-medium))."),
        ("--mj-download-button-focus-ring-color", "Focus ring colour (default var(--mj-focus-ring))."),
    ],
)


# ---------------------------------------------------------------------------
# mj-upload-button
# ---------------------------------------------------------------------------

_UPLOAD = ComponentDoc(
    tag="mj-upload-button",
    title="Upload Button",
    group="buttons",
    summary="A button that opens the file picker and accepts dropped files, with filtering and form participation.",
    description=(
        "<p><code>&lt;mj-upload-button&gt;</code> wraps a hidden <code>&lt;input type=file&gt;</code> "
        "(not a tab stop) behind a styled button and also accepts files dropped on the host, or "
        "on the element named by the <code>drop-target</code> selector. While files are dragged "
        "over the surface the host carries <code>drag-over</code>.</p>"
        "<p>Every pick or drop fires one <code>mj-upload-select</code> with the files it "
        "considered (every offered file with <code>multiple</code>; without it only the first "
        "one) and their partition after <code>accept</code> (extensions, MIME types, "
        "<code>type/*</code>) and <code>max-size</code> filtering. The accepted files become "
        "the selection: <code>files</code> returns them (an array, or null when none) and the "
        "name of the file, or the file count, is shown next to the button. A pick or drop in "
        "which every file is rejected keeps the previous selection.</p>"
        "<p>The element is form-associated: the accepted files are submitted under "
        "<code>name</code>, <code>required</code> makes an empty selection invalid, form reset "
        "clears the selection and <code>&lt;fieldset disabled&gt;</code> disables it.</p>"
    ),
    how_to_use=(
        "<p>Set <code>accept</code>, <code>multiple</code> and <code>max-size</code> (bytes, or "
        "with a <code>KB</code> / <code>MB</code> / <code>GB</code> suffix, 1024-based), put "
        "the text between the tags and listen for <code>mj-upload-select</code> to show "
        "rejected files. Add <code>name</code> inside a <code>&lt;form&gt;</code>. Call "
        "<code>clear()</code> to drop the selection.</p>"
    ),
    example="",
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>Accepts one or more CSV files. Pick or drop files on the button: the "
                "selection appears next to it and <code>mj-upload-select</code> in Events.</p>"
            ),
            html=_code("""
                <mj-upload-button accept=".csv,text/csv" multiple>[[upload]]Choose CSV files</mj-upload-button>
            """),
        ),
        ComponentExample(
            key="variants",
            title="Variants, sizes and states",
            description=(
                "<p><code>primary</code> and <code>tertiary</code>, the sizes, an "
                "<code>icon-only</code> button named by <code>label</code>, <code>loading</code>, "
                "<code>disabled</code> and a <code>block</code> button.</p>"
            ),
            html=_code("""
                <div class="stack">
                  <div class="row">
                    <mj-upload-button variant="primary">[[upload]]Upload</mj-upload-button>
                    <mj-upload-button>Default</mj-upload-button>
                    <mj-upload-button variant="tertiary">Tertiary</mj-upload-button>
                    <mj-upload-button icon-only label="Upload attachment">[[upload]]</mj-upload-button>
                  </div>
                  <div class="row">
                    <mj-upload-button size="sm">Small</mj-upload-button>
                    <mj-upload-button size="lg">Large</mj-upload-button>
                    <mj-upload-button loading>Uploading&hellip;</mj-upload-button>
                    <mj-upload-button disabled>Disabled</mj-upload-button>
                  </div>
                  <mj-upload-button block>Block upload button</mj-upload-button>
                </div>
            """),
            css=_ROW_CSS,
        ),
        ComponentExample(
            key="validation",
            title="Accept, max-size and events",
            description=(
                "<p>Images up to <code>max-size=\"200KB\"</code> (204,800 bytes). The script drops "
                "three files on the button: the PNG is accepted, the large JPEG is rejected for "
                "<code>max-size</code> and the CSV for <code>accept</code>. Then it drops one more "
                "oversized image: it is rejected and the PNG stays selected.</p>"
            ),
            html=_code("""
                <mj-upload-button id="photos" accept="image/*" multiple max-size="200KB" variant="primary">[[image]]Add photos</mj-upload-button>
                <p class="note">Images only, at most 200 KB each.</p>
                <ul id="upload-results" class="results"></ul>
            """),
            css=_ROW_CSS + "\n.results { margin: var(--mj-space-2) 0 0; padding-inline-start: var(--mj-space-5); }",
            script=_code("""
                const upload = document.getElementById("photos")
                const results = document.getElementById("upload-results")
                const addLine = (text) => {
                  const item = document.createElement("li")
                  item.textContent = text
                  results.appendChild(item)
                }

                let drops = 0
                upload.addEventListener("mj-upload-select", (event) => {
                  drops = drops + 1
                  addLine("Drop " + drops + ":")
                  for (const file of event.detail.accepted) {
                    addLine("Accepted: " + file.name + " (" + file.size + " bytes)")
                  }
                  for (const entry of event.detail.rejected) {
                    addLine("Rejected: " + entry.file.name + " (" + entry.reason + ")")
                  }
                  const kept = upload.files === null ? null : upload.files.map((file) => file.name)
                  mjSandbox.log("files property", { files: kept })
                })

                // Simulate dropping three files on the button.
                const transfer = new DataTransfer()
                transfer.items.add(new File(["x".repeat(1200)], "team.png", { type: "image/png" }))
                transfer.items.add(new File(["x".repeat(300000)], "poster.jpg", { type: "image/jpeg" }))
                transfer.items.add(new File(["name,total"], "totals.csv", { type: "text/csv" }))
                upload.dispatchEvent(new DragEvent("drop", { dataTransfer: transfer, bubbles: true, cancelable: true }))

                // A second drop where every file is rejected keeps the selection.
                const second = new DataTransfer()
                second.items.add(new File(["x".repeat(250000)], "banner.png", { type: "image/png" }))
                upload.dispatchEvent(new DragEvent("drop", { dataTransfer: second, bubbles: true, cancelable: true }))
            """),
        ),
        ComponentExample(
            key="drop-target",
            title="Drop target",
            description=(
                "<p><code>drop-target=\"#dropzone\"</code> makes the whole box the drop surface; "
                "page CSS highlights it while the button carries <code>drag-over</code>. Drag "
                "files from your desktop onto the box.</p>"
            ),
            html=_code("""
                <div id="dropzone" class="dropzone">
                  <p>Drop files anywhere in this box, or</p>
                  <mj-upload-button drop-target="#dropzone" multiple>Browse files</mj-upload-button>
                </div>
            """),
            css=_code("""
                .dropzone {
                  display: grid; justify-items: center; gap: var(--mj-space-2);
                  padding: var(--mj-space-6) var(--mj-space-4);
                  border: 2px dashed var(--mj-border-strong); border-radius: var(--mj-radius-lg);
                  color: var(--mj-text-muted); text-align: center;
                }
                .dropzone p { margin: 0; }
                .dropzone:has(mj-upload-button[drag-over]) { border-color: var(--mj-accent); background: var(--mj-bg-muted); }
            """),
        ),
        ComponentExample(
            key="form",
            title="Form participation",
            description=(
                "<p>A <code>required</code> upload named <code>resume</code> in a form. The script "
                "drops a file and submits; the submitted data lists the file. Reset clears the "
                "selection.</p>"
            ),
            html=_code("""
                <form id="apply" class="stack">
                  <label>Name <input name="applicant" value="Ada Lovelace"></label>
                  <mj-upload-button name="resume" accept=".pdf,.txt" required>[[upload]]Attach resume</mj-upload-button>
                  <div class="row">
                    <button type="submit">Apply</button>
                    <button type="reset">Reset</button>
                  </div>
                </form>
                <output id="apply-result" class="note"></output>
            """),
            css=_ROW_CSS + "\nlabel { display: grid; gap: var(--mj-space-1); max-inline-size: 20rem; }\n.stack { justify-items: start; }",
            script=_code("""
                const form = document.getElementById("apply")
                const result = document.getElementById("apply-result")
                const upload = form.querySelector("mj-upload-button")

                form.addEventListener("submit", (event) => {
                  event.preventDefault()
                  const entries = []
                  for (const [key, value] of new FormData(form)) {
                    entries.push(key + " = " + (value instanceof File ? value.name : value))
                  }
                  result.textContent = "Submitted: " + entries.join(", ")
                  mjSandbox.log("submit", { entries })
                })
                form.addEventListener("reset", () => {
                  // The reset event fires before the controls reset: read the selection afterwards.
                  setTimeout(() => {
                    const names = upload.files === null ? null : upload.files.map((file) => file.name)
                    result.textContent = "Reset: files = " + JSON.stringify(names)
                    mjSandbox.log("reset", { files: names })
                  })
                })

                const transfer = new DataTransfer()
                transfer.items.add(new File(["Experience: ..."], "resume.txt", { type: "text/plain" }))
                upload.dispatchEvent(new DragEvent("drop", { dataTransfer: transfer, bubbles: true, cancelable: true }))
                form.requestSubmit()
            """),
        ),
    ],
    attributes=[
        AttributeDoc(name="accept", description="Comma-separated extensions (.csv), MIME types (text/csv) or wildcards (image/*).",
                     kind="string", values=[".csv,text/csv", "image/*", ".pdf"]),
        AttributeDoc(name="multiple", description="Allow more than one file; otherwise only the first offered file is used.",
                     kind="boolean"),
        AttributeDoc(name="max-size", description="Maximum size per file: bytes, or a number with a B, KB, MB or GB suffix (1024-based, so 2MB = 2,097,152 bytes). 0, absent or unreadable (ignored with a console warning): no limit.",
                     kind="string", values=["200000", "200KB", "2MB"]),
        AttributeDoc(name="capture", description="Mobile camera capture hint passed to the input.",
                     kind="enum", values=["user", "environment"]),
        AttributeDoc(name="name", description="Form field name the accepted files are submitted under.", kind="string"),
        AttributeDoc(name="required", description="An empty selection makes the form invalid (valueMissing). Say so in the visible label: aria-required is not allowed on the inner button.", kind="boolean"),
        AttributeDoc(name="drop-target", description="CSS selector of another element that accepts drops (default the host).",
                     kind="string"),
        AttributeDoc(name="variant", description="Emphasis. Without it the button is outlined.",
                     kind="enum", values=["primary", "tertiary"]),
        AttributeDoc(name="size", description="Control height, padding and font size.",
                     kind="enum", values=["sm", "md", "lg"], default="md"),
        AttributeDoc(name="loading", description="Busy: spinner, aria-busy, picks and drops blocked.", kind="boolean"),
        AttributeDoc(name="disabled", description="Blocks picks and drops (inner button and input disabled).",
                     kind="boolean"),
        AttributeDoc(name="icon-only", description="Square button; the selection summary is hidden. Set label.",
                     kind="boolean"),
        AttributeDoc(name="label", description="Accessible name of the inner button.", kind="string"),
        AttributeDoc(name="block", description="Full-width button.", kind="boolean"),
    ],
    events=[
        (
            "mj-upload-select",
            "Fired on every pick or drop, after filtering; with no accepted file the selection is kept.",
            "{ files: File[], accepted: File[], rejected: { file: File, reason: 'accept' | 'max-size' }[], source: 'picker' | 'drop' }",
        ),
    ],
    slots=[
        ("", "Button content: text and an optional inline icon.", _svg("upload") + "Upload"),
    ],
    properties=[
        ("files", "File[] | null. Read-only; the accepted files of the current selection."),
        ("multiple", "boolean. Reflects the `multiple` attribute."),
        ("required", "boolean. Reflects the `required` attribute."),
        ("disabled", "boolean. Reflects the `disabled` attribute."),
        ("form", "HTMLFormElement | null. Read-only; the form owner."),
        ("validity", "ValidityState | null. Read-only."),
        ("validationMessage", "string. Read-only."),
    ],
    methods=[
        ("click()", "Opens the file picker as a user click would (browsers open it only during a user gesture)."),
        ("clear()", "Drops the selection and empties the form value (no event)."),
        ("checkValidity() -> boolean", "Checks the required constraint."),
        ("reportValidity() -> boolean", "Checks and reports the required constraint."),
    ],
    parts=[
        ("button", "The inner native button."),
        ("spinner", "Busy spinner."),
        ("summary", "Name of the selected file, or the file count."),
        ("file-input", "The visually hidden native file input."),
    ],
    css_properties=[
        ("--mj-upload-button-bg", "Background (default var(--mj-surface))."),
        ("--mj-upload-button-color", "Text colour (default var(--mj-text))."),
        ("--mj-upload-button-border-color", "Border colour (default var(--mj-border-strong))."),
        ("--mj-upload-button-border-radius", "Corner radius (default var(--mj-radius-md))."),
        ("--mj-upload-button-height", "Minimum height of md (default var(--mj-control-height-md))."),
        ("--mj-upload-button-font-weight", "Font weight (default var(--mj-font-weight-medium))."),
        ("--mj-upload-button-dragover-bg", "Background while files are dragged over (default var(--mj-bg-muted))."),
        ("--mj-upload-button-dragover-border-color", "Border colour while files are dragged over (default var(--mj-accent))."),
        ("--mj-upload-button-summary-color", "Summary text colour (default var(--mj-text-muted))."),
        ("--mj-upload-button-summary-font-size", "Summary font size (default var(--mj-font-size-sm))."),
        ("--mj-upload-button-focus-ring-color", "Focus ring colour (default var(--mj-focus-ring))."),
    ],
)


COMPONENTS = [
    _BUTTON,
    _FAB,
    _TOGGLE,
    _DISCLOSURE,
    _COPY,
    _SHARE,
    _FAVORITE,
    _DOWNLOAD,
    _UPLOAD,
]
