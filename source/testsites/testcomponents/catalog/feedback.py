"""
    feedback.py

    Catalog entries for the 'Feedback' component group.

    Each entry in COMPONENTS describes and demonstrates one feedback
    component -- alert, toast, progress, badge, chip and tooltip -- with an
    example gallery, typed attribute controls, events with their detail
    shape, slots with sample content, and the property / method / part /
    custom-property tables, all checked against the component sources in
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
    "check": '<path d="M3 8.5 6.5 12 13 4.5"/>',
    "clock": '<circle cx="8" cy="8" r="6"/><path d="M8 4.5V8l2.5 1.5"/>',
    "cloud": '<path d="M4.5 12.5a3 3 0 0 1-.4-6A4 4 0 0 1 12 6a2.8 2.8 0 0 1 .5 5.5z"/>',
    "code": '<path d="M5.5 4.5 2 8l3.5 3.5M10.5 4.5 14 8l-3.5 3.5"/>',
    "sparkle": '<path d="M8 2v3M8 11v3M2 8h3M11 8h3M4 4l2 2M10 10l2 2M12 4l-2 2M6 10l-2 2"/>',
    "tag": '<path d="M2.5 2.5h5l6 6-5 5-6-6z"/><circle cx="5.5" cy="5.5" r="1"/>',
    "trash": '<path d="M3 4.5h10M6.5 4.5V3h3v1.5M4.5 4.5l.5 8.5h6l.5-8.5"/>',
    "user": '<circle cx="8" cy="5.5" r="2.5"/><path d="M3 13.5a5 5 0 0 1 10 0"/>',
}

_ICON_TOKEN = re.compile(r"\[\[([a-z-]+)(?:\|([a-z-]+))?\]\]")


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

_SEVERITIES = ["info", "success", "warning", "error"]


# ---------------------------------------------------------------------------
# mj-alert
# ---------------------------------------------------------------------------

_ALERT = ComponentDoc(
    tag="mj-alert",
    title="Alert",
    group="feedback",
    summary="Contextual inline, banner or callout message in four severities, with title, icon and action slots.",
    description=(
        "<p><code>&lt;mj-alert&gt;</code> shows a contextual message in one of four severities "
        "&mdash; <code>info</code> (default), <code>success</code>, <code>warning</code> and "
        "<code>error</code> &mdash; which set the colours, the icon and the role "
        "(<code>alert</code> for error, <code>status</code> otherwise). A visually hidden prefix "
        "(\"Warning: \") names the severity so the meaning is not carried by colour alone.</p>"
        "<p>Variants: <code>inline</code> (default, bordered box), <code>banner</code> "
        "(full-width, flush edges, a <code>region</code> landmark named by <code>label</code>, "
        "else <code>heading</code>, else the severity) and <code>callout</code> (accent stripe "
        "at the start edge).</p>"
        "<p>Announcements: the message is spoken through the shared live region when the alert "
        "is inserted into an already loaded page and each time it is re-opened, never for an "
        "alert that is part of the initial page or is merely moved.</p>"
        "<p><code>open</code> is true unless it is exactly <code>\"false\"</code>. The dismiss "
        "button (<code>dismissible</code>, or Escape on it) fires the cancelable "
        "<code>mj-alert-dismiss</code>; unless cancelled it moves focus (to "
        "<code>return-focus</code>, else the next or previous focusable element), sets "
        "<code>open=\"false\"</code> and removes the element 400 ms later unless it was "
        "re-opened.</p>"
    ),
    how_to_use=(
        "<p>Put the message between the tags and choose <code>severity</code> and "
        "<code>variant</code>. Give a headline with <code>heading</code> or the "
        "<code>title</code> slot, buttons in the <code>actions</code> slot and a custom icon in "
        "the <code>icon</code> slot (or a built-in one with <code>icon</code>). To hide and show "
        "an alert without losing it, cancel <code>mj-alert-dismiss</code> and set "
        "<code>open</code> yourself.</p>"
    ),
    example="",
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>The four severities: plain info, success with a <code>heading</code>, a "
                "<code>dismissible</code> warning, and an error callout.</p>"
            ),
            html=_code("""
                <div class="stack">
                  <mj-alert severity="info">Your session will expire in 5 minutes.</mj-alert>
                  <mj-alert severity="success" heading="Saved">Your changes have been saved.</mj-alert>
                  <mj-alert severity="warning" dismissible>Low disk space on the primary volume.</mj-alert>
                  <mj-alert severity="error" variant="callout" heading="Upload failed">The file exceeds the 10 MB limit.</mj-alert>
                </div>
            """),
            css=_ROW_CSS,
        ),
        ComponentExample(
            key="variants",
            title="Variants",
            description=(
                "<p>A <code>banner</code> (a region landmark named by <code>label</code>), the "
                "default <code>inline</code> box, a <code>callout</code>, and an alert without "
                "icon (<code>no-icon</code>).</p>"
            ),
            html=_code("""
                <div class="stack">
                  <mj-alert variant="banner" severity="warning" label="Maintenance notice" dismissible>Scheduled maintenance on Saturday from 02:00 to 04:00 UTC.</mj-alert>
                  <mj-alert severity="info">Inline is the default variant: a rounded, bordered box.</mj-alert>
                  <mj-alert variant="callout" severity="success" heading="Tip">Callouts mark a passage with a stripe at the start edge.</mj-alert>
                  <mj-alert severity="info" no-icon>This alert has no icon.</mj-alert>
                </div>
            """),
            css=_ROW_CSS,
        ),
        ComponentExample(
            key="slots",
            title="Title, icon and actions slots",
            description=(
                "<p>A warning with a slotted <code>title</code>, <code>actions</code> and a custom "
                "<code>dismiss-label</code>; an info alert with a custom <code>icon</code>; and a "
                "built-in icon chosen with <code>icon=\"success\"</code>.</p>"
            ),
            html=_code("""
                <div class="stack">
                  <mj-alert severity="warning" dismissible dismiss-label="Dismiss the billing warning">
                    <span slot="title">Payment method expiring</span>
                    Your card ending in 4242 expires next month.
                    <div slot="actions">
                      <button type="button">Update card</button>
                      <button type="button">Remind me later</button>
                    </div>
                  </mj-alert>
                  <mj-alert severity="info">
                    [[sparkle|icon]]
                    <span slot="title">New: keyboard shortcuts</span>
                    Press <kbd>?</kbd> anywhere to see them.
                  </mj-alert>
                  <mj-alert severity="info" icon="success">Backups run every night; the last one completed at 02:14.</mj-alert>
                </div>
            """),
            css=_ROW_CSS,
        ),
        ComponentExample(
            key="events",
            title="Open, close and dismiss",
            description=(
                "<p>The dismiss handler cancels the removal and sets <code>open</code> instead, "
                "so <b>Toggle open</b> can bring the alert back. The script closes and re-opens "
                "it once: Events shows <code>mj-alert-close</code> and "
                "<code>mj-alert-open</code>.</p>"
            ),
            html=_code("""
                <div class="stack">
                  <mj-alert id="cookie-alert" severity="info" heading="Cookies" dismissible>We use cookies to remember your preferences.</mj-alert>
                  <div class="row"><button type="button" id="toggle-open">Toggle open</button></div>
                </div>
            """),
            css=_ROW_CSS,
            script=_code("""
                const alert = document.getElementById("cookie-alert")
                const toggle = document.getElementById("toggle-open")

                alert.addEventListener("mj-alert-dismiss", (event) => {
                  // Keep the element (it would be removed 400 ms after closing).
                  event.preventDefault()
                  toggle.focus()
                  alert.open = false
                })
                toggle.addEventListener("click", () => { alert.open = !alert.open })

                alert.open = false
                alert.open = true
            """),
        ),
        ComponentExample(
            key="custom-styling",
            title="Custom styling",
            description=(
                "<p>The <code>--mj-alert-*</code> custom properties set on the element override "
                "the severity colours: a brand-coloured callout and a compact, square alert.</p>"
            ),
            html=_code("""
                <div class="stack">
                  <mj-alert class="brand" variant="callout" severity="info" heading="New: pinned reports">Pin any report to keep it at the top of your dashboard.</mj-alert>
                  <mj-alert class="compact" severity="warning">Two reviewers are still pending.</mj-alert>
                </div>
            """),
            css=_ROW_CSS + "\n" + _code("""
                .brand {
                  --mj-alert-bg: color-mix(in oklab, var(--mj-accent) 12%, var(--mj-surface));
                  --mj-alert-border-color: var(--mj-accent);
                  --mj-alert-icon-color: var(--mj-accent);
                  --mj-alert-callout-accent-width: 6px;
                }
                .compact {
                  --mj-alert-border-radius: 0;
                  --mj-alert-padding-block: var(--mj-space-1);
                  --mj-alert-padding-inline: var(--mj-space-2);
                  --mj-alert-gap: var(--mj-space-2);
                }
            """),
        ),
    ],
    attributes=[
        AttributeDoc(name="severity", description="Colours, icon and role (error uses role=alert).",
                     kind="enum", values=_SEVERITIES, default="info"),
        AttributeDoc(name="variant", description="Visual placement style.",
                     kind="enum", values=["inline", "banner", "callout"], default="inline"),
        AttributeDoc(name="heading", description="Bold headline (the title slot replaces it).", kind="string"),
        AttributeDoc(name="dismissible", description="Shows the dismiss button.", kind="boolean"),
        AttributeDoc(name="dismiss-label", description="Accessible name of the dismiss button.",
                     kind="string", default="Close"),
        AttributeDoc(name="no-icon", description="Hides the icon.", kind="boolean"),
        AttributeDoc(name="icon", description="Built-in icon to show instead of the severity icon.",
                     kind="enum", values=_SEVERITIES),
        AttributeDoc(name="open", description="Visible unless set to `false`; changes fire mj-alert-open / mj-alert-close.",
                     kind="boolean", default="true"),
        AttributeDoc(name="label", description="Name of the banner region (variant=banner).", kind="string"),
        AttributeDoc(name="return-focus", description="Id of the element that gets focus when a focused alert is dismissed.",
                     kind="string"),
    ],
    events=[
        ("mj-alert-dismiss", "The dismiss button (or Escape on it) was activated. Cancelable: keeps the alert.",
         "{ severity: string, variant: string }"),
        ("mj-alert-open", "The alert became visible again.", "{ severity: string | null, variant: string | null }"),
        ("mj-alert-close", "The alert was hidden (open=\"false\").", "{ severity: string | null, variant: string | null }"),
    ],
    slots=[
        ("", "The message.", "Your report is ready to download."),
        ("title", "Headline; replaces `heading`.", "<strong>Heads up</strong>"),
        ("icon", "Custom icon; replaces the built-in one.", _svg("sparkle")),
        ("actions", "Action buttons below the message.",
         '<div><button type="button">Retry</button> <button type="button">Details</button></div>'),
    ],
    properties=[
        ("open", "boolean. False only when the attribute is \"false\"; setting it writes open=\"true\" / \"false\"."),
        ("severity", "string. Reflects the `severity` attribute (default \"info\")."),
    ],
    parts=[
        ("region", "Outer wrapper; the banner landmark."),
        ("container", "The coloured box (carries the role)."),
        ("icon", "Icon wrapper."),
        ("content", "Text column (title, body, actions)."),
        ("title", "Headline row."),
        ("body", "Wrapper of the default slot."),
        ("actions", "Actions row."),
        ("dismiss", "The dismiss button."),
    ],
    css_properties=[
        ("--mj-alert-bg", "Background; overrides the severity colour (default the severity's surface token, e.g. var(--mj-color-warning-surface))."),
        ("--mj-alert-border-color", "Border and callout stripe colour; overrides the severity colour (default the severity token, e.g. var(--mj-color-warning))."),
        ("--mj-alert-icon-color", "Icon colour; overrides the severity colour (default the severity token)."),
        ("--mj-alert-color", "Text colour (default var(--mj-text))."),
        ("--mj-alert-border-radius", "Corner radius of inline alerts (default var(--mj-radius-md))."),
        ("--mj-alert-padding-block", "Block padding (default var(--mj-space-3))."),
        ("--mj-alert-padding-inline", "Inline padding (default var(--mj-space-4))."),
        ("--mj-alert-gap", "Gap between icon, text and dismiss button (default var(--mj-space-3))."),
        ("--mj-alert-callout-accent-width", "Stripe width of the callout variant (default 4px)."),
    ],
)


# ---------------------------------------------------------------------------
# mj-toast
# ---------------------------------------------------------------------------

_TOAST = ComponentDoc(
    tag="mj-toast",
    title="Toast",
    group="feedback",
    summary="Transient, non-modal notification with severity, actions and an auto-dismiss countdown.",
    description=(
        "<p><code>&lt;mj-toast&gt;</code> is a brief notification. It is visible while it has "
        "<code>open</code>; opening it announces its text (assertively for "
        "<code>error</code>) and fires <code>mj-toast-open</code>.</p>"
        "<p>Placement: inside <code>&lt;mj-toast-region&gt;</code> the region lays toasts out "
        "and stacks them. A standalone toast is a fixed overlay at the viewport edge named by "
        "<code>placement</code> (default <code>bottom-end</code>); "
        "<code>placement=\"inline\"</code> keeps it in the normal flow. Standalone toasts do "
        "not stack: several open ones overlap.</p>"
        "<p><code>auto-dismiss</code> (ms, at least 1000) starts a countdown with a progress bar "
        "when the toast opens, including toasts declared open in markup. Pointer or focus "
        "inside the toast pauses both the timer and the bar. Dismissal &mdash; the close "
        "button, Escape inside the toast, an action, the timer or <code>dismiss()</code> "
        "&mdash; fires the cancelable <code>mj-toast-dismiss</code>; unless cancelled "
        "<code>open</code> is removed and the element is removed 350 ms later. Activating a "
        "control in the <code>actions</code> slot fires <code>mj-toast-action</code> with its "
        "<code>value</code>, then dismisses.</p>"
    ),
    how_to_use=(
        "<p>Put the message between the tags, set <code>severity</code> and "
        "<code>heading</code> (or the <code>title</code> slot), and add <code>open</code>. To "
        "raise toasts from script create the element, append it and set "
        "<code>open = true</code>; prefer an <code>&lt;mj-toast-region&gt;</code> when several "
        "can be visible. Keep <code>auto-dismiss</code> off for toasts with actions people must "
        "reach.</p>"
    ),
    example="",
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>A standalone success toast: a fixed overlay at the bottom-end corner of the "
                "preview. Close it with its button (it is then removed; Reset brings it "
                "back).</p>"
            ),
            html=_code("""
                <mj-toast id="upload-toast" open severity="success" heading="File uploaded">report_q4.xlsx was uploaded successfully.</mj-toast>
            """),
            height=200,
        ),
        ComponentExample(
            key="severities",
            title="Severities (inline)",
            description=(
                "<p>The four severities with <code>placement=\"inline\"</code> so they stay in the "
                "flow, and one with <code>no-icon</code>.</p>"
            ),
            html=_code("""
                <div class="stack">
                  <mj-toast open placement="inline" severity="info" heading="Sync scheduled">Your files will sync at 18:00.</mj-toast>
                  <mj-toast open placement="inline" severity="success" heading="Payment received">Invoice INV-1042 was paid.</mj-toast>
                  <mj-toast open placement="inline" severity="warning" heading="Storage almost full">You have used 92% of your quota.</mj-toast>
                  <mj-toast open placement="inline" severity="error" heading="Connection lost">Retrying&hellip;</mj-toast>
                  <mj-toast open placement="inline" severity="info" no-icon>A toast without icon.</mj-toast>
                </div>
            """),
            css=_ROW_CSS,
        ),
        ComponentExample(
            key="slots",
            title="Title, icon and actions",
            description=(
                "<p>A slotted <code>icon</code> and <code>title</code> and two actions. Choosing "
                "<b>Undo</b> or <b>View archive</b> fires <code>mj-toast-action</code> with the "
                "button's <code>value</code> and dismisses the toast.</p>"
            ),
            html=_code("""
                <mj-toast id="undo-toast" open placement="inline" severity="info">
                  [[archive|icon]]
                  <span slot="title">Conversation archived</span>
                  "Weekly sync" was moved to the archive.
                  <div slot="actions">
                    <button type="button" value="undo">Undo</button>
                    <button type="button" value="view">View archive</button>
                  </div>
                </mj-toast>
                <p id="action-status" class="note"></p>
            """),
            css=_ROW_CSS,
            script=_code("""
                const toast = document.getElementById("undo-toast")
                const status = document.getElementById("action-status")
                toast.addEventListener("mj-toast-action", (event) => {
                  status.textContent = "Action chosen: " + event.detail.action
                })
            """),
        ),
        ComponentExample(
            key="auto-dismiss",
            title="Auto-dismiss and raising toasts",
            description=(
                "<p>The first toast dismisses itself after 5 s (hover or focus it to pause the "
                "bar). <b>Raise a toast</b> appends new ones with a 4 s countdown; the script "
                "raises one on load. Events shows <code>mj-toast-open</code> and "
                "<code>mj-toast-dismiss</code> with <code>reason: 'auto'</code>.</p>"
            ),
            html=_code("""
                <div class="stack" id="toast-stack">
                  <div class="row"><button type="button" id="raise-toast">Raise a toast</button></div>
                  <mj-toast id="draft-toast" open placement="inline" severity="success" auto-dismiss="5000" heading="Draft saved">Hover or focus this toast to pause its countdown.</mj-toast>
                </div>
            """),
            css=_ROW_CSS,
            script=_code("""
                const stack = document.getElementById("toast-stack")
                let raised = 0

                document.getElementById("raise-toast").addEventListener("click", () => {
                  raised = raised + 1
                  const toast = document.createElement("mj-toast")
                  toast.setAttribute("placement", "inline")
                  toast.setAttribute("severity", "info")
                  toast.setAttribute("auto-dismiss", "4000")
                  toast.setAttribute("heading", "Notification " + raised)
                  toast.textContent = "Raised from script; it dismisses itself after 4 seconds."
                  stack.appendChild(toast)
                  toast.open = true
                })
                stack.addEventListener("mj-toast-dismiss", (event) => {
                  mjSandbox.log("dismissed", { heading: event.target.getAttribute("heading"), reason: event.detail.reason })
                })

                document.getElementById("raise-toast").click()
            """),
        ),
        ComponentExample(
            key="placement",
            title="Placement",
            description=(
                "<p>Pick a <code>placement</code> to move the standalone toast around the preview. "
                "Its dismissal is cancelled and turned into <code>open = false</code>, so "
                "<b>Show toast</b> can open it again.</p>"
            ),
            html=_code("""
                <div class="row">
                  <label>Placement
                    <select id="placement-select">
                      <option>top-start</option><option>top</option><option selected>top-end</option>
                      <option>bottom-start</option><option>bottom</option><option>bottom-end</option>
                    </select>
                  </label>
                  <button type="button" id="show-toast">Show toast</button>
                </div>
                <mj-toast id="placed-toast" open placement="top-end" severity="info" heading="Placement">Change the placement, close the toast, then show it again.</mj-toast>
            """),
            css=_ROW_CSS + "\nbody { padding-block-start: 7rem; }",
            script=_code("""
                const toast = document.getElementById("placed-toast")
                document.getElementById("placement-select").addEventListener("change", (event) => {
                  toast.setAttribute("placement", event.target.value)
                })
                document.getElementById("show-toast").addEventListener("click", () => { toast.open = true })
                toast.addEventListener("mj-toast-dismiss", (event) => {
                  // Keep the element so it can be shown again.
                  event.preventDefault()
                  toast.open = false
                })
            """),
            height=320,
        ),
    ],
    attributes=[
        AttributeDoc(name="open", description="Visible while present; adding it announces the toast and starts the countdown.",
                     kind="boolean"),
        AttributeDoc(name="severity", description="Icon colour and announcement politeness (error is assertive).",
                     kind="enum", values=_SEVERITIES, default="info"),
        AttributeDoc(name="heading", description="Bold headline (the title slot replaces it).", kind="string"),
        AttributeDoc(name="auto-dismiss", description="Countdown in ms before automatic dismissal (minimum 1000; absent or 0: stays).",
                     kind="number"),
        AttributeDoc(name="no-icon", description="Hides the icon.", kind="boolean"),
        AttributeDoc(
            name="placement",
            description="Viewport edge of a standalone toast; `inline` keeps it in the flow. Ignored inside mj-toast-region.",
            kind="enum",
            values=["bottom-end", "bottom-start", "bottom", "top-end", "top-start", "top", "inline"],
            default="bottom-end",
        ),
    ],
    events=[
        ("mj-toast-open", "The toast opened (also for toasts declared open).", "{ severity: string }"),
        ("mj-toast-dismiss", "The toast is about to be dismissed. Cancelable: keeps it open.",
         "{ severity: string, reason: 'user' | 'auto' | 'api' }"),
        ("mj-toast-action", "A control in the actions slot was activated (the toast then dismisses).",
         "{ severity: string, action: string | null }"),
    ],
    slots=[
        ("", "The message.", "Your export is ready."),
        ("title", "Headline; replaces `heading`.", "<strong>Export finished</strong>"),
        ("icon", "Custom icon; replaces the severity icon.", _svg("cloud")),
        ("actions", "Action controls; their `value` is reported by mj-toast-action.",
         '<div><button type="button" value="open">Open</button></div>'),
    ],
    properties=[
        ("open", "boolean. Reflects the `open` attribute."),
        ("remainingTime", "number. Read-only; ms left in the countdown (Infinity when not counting)."),
    ],
    methods=[
        ("dismiss()", "Dismisses an open toast (mj-toast-dismiss with reason 'api')."),
        ("pauseTimer()", "Pauses the countdown and its bar (as hover / focus do)."),
        ("resumeTimer()", "Resumes a paused countdown."),
    ],
    parts=[
        ("container", "The toast card."),
        ("icon", "Icon wrapper."),
        ("content", "Text column (title, body, actions)."),
        ("title", "Headline row."),
        ("body", "Wrapper of the default slot."),
        ("actions", "Actions row."),
        ("dismiss", "The close button."),
        ("progress", "Countdown bar track."),
    ],
    css_properties=[
        ("--mj-toast-bg", "Background (default var(--mj-surface-raised))."),
        ("--mj-toast-color", "Text colour (default var(--mj-text))."),
        ("--mj-toast-border-color", "Border colour (default var(--mj-border))."),
        ("--mj-toast-border-radius", "Corner radius (default var(--mj-radius-lg))."),
        ("--mj-toast-shadow", "Shadow (default var(--mj-elevation-3))."),
        ("--mj-toast-min-width", "Minimum width (default 18rem)."),
        ("--mj-toast-max-width", "Maximum width (default 28rem)."),
        ("--mj-toast-padding-block", "Block padding (default var(--mj-space-3))."),
        ("--mj-toast-padding-inline", "Inline padding (default var(--mj-space-4))."),
        ("--mj-toast-progress-color", "Countdown bar colour (default var(--mj-accent))."),
        ("--mj-toast-animation-duration", "Enter animation (default var(--mj-motion-medium))."),
        ("--mj-toast-offset-x", "Inline edge distance of a standalone toast (default var(--mj-space-4))."),
        ("--mj-toast-offset-y", "Block edge distance of a standalone toast (default var(--mj-space-4))."),
        ("--mj-toast-z-index", "Stacking order of a standalone toast (default var(--mj-layer-toast))."),
    ],
)


# ---------------------------------------------------------------------------
# mj-progress
# ---------------------------------------------------------------------------

_PROGRESS = ComponentDoc(
    tag="mj-progress",
    title="Progress",
    group="feedback",
    summary="Full-width bar or circular ring progress indicator, determinate or indeterminate.",
    description=(
        "<p><code>&lt;mj-progress&gt;</code> shows how far an operation has got. The default "
        "<code>bar</code> variant is a block that fills its container; <code>ring</code> is an "
        "inline circle. Determinate mode draws <code>value</code> against <code>max</code> "
        "(default 100; the value is clamped to 0&ndash;max); <code>indeterminate</code> animates "
        "without a known end and drops the ARIA value attributes. Animations respect "
        "<code>prefers-reduced-motion</code> and the bar sweep follows the text direction.</p>"
        "<p>The inner element has <code>role=\"progressbar\"</code>. Its accessible name comes "
        "from <code>aria-labelledby</code>, <code>aria-label</code>, <code>label</code> or the "
        "slotted label text, in that order; a progress without any is reported in the console. "
        "<code>value-text</code> sets <code>aria-valuetext</code>.</p>"
        "<p><code>show-label</code> displays the label; <code>show-value</code> displays "
        "<code>value-text</code>, else the percentage (in the ring's centre for the ring). The "
        "<code>value-text</code> and <code>center</code> slots replace that visible value "
        "without changing <code>aria-valuetext</code>.</p>"
    ),
    how_to_use=(
        "<p>Always give a <code>label</code>. Update <code>value</code> as work progresses "
        "(setting the property also clears <code>indeterminate</code>) and listen for "
        "<code>mj-progress-complete</code>. Use <code>value-text</code> for a meaningful "
        "spoken value such as \"3 of 5 files\".</p>"
    ),
    example="",
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>A full-width bar at 65% with its label and percentage shown. Change "
                "<code>value</code>, <code>variant</code> or <code>size</code> in Controls.</p>"
            ),
            html=_code("""
                <mj-progress value="65" label="Uploading report.pdf" show-label show-value></mj-progress>
            """),
        ),
        ComponentExample(
            key="variants",
            title="Bar and ring",
            description="<p>Determinate and indeterminate bars, then determinate and indeterminate rings.</p>",
            html=_code("""
                <div class="stack">
                  <mj-progress value="40" label="Bar, determinate" show-label show-value></mj-progress>
                  <mj-progress indeterminate label="Bar, indeterminate" show-label></mj-progress>
                  <div class="row">
                    <mj-progress variant="ring" value="72" label="Ring" show-label show-value></mj-progress>
                    <mj-progress variant="ring" indeterminate label="Ring, indeterminate" show-label></mj-progress>
                  </div>
                </div>
            """),
            css=_ROW_CSS + "\n.row { gap: var(--mj-space-6); }",
        ),
        ComponentExample(
            key="sizes",
            title="Sizes and custom styling",
            description=(
                "<p><code>sm</code>, <code>md</code> and <code>lg</code> for bars and rings, and a "
                "bar recoloured with <code>--mj-progress-fill-color</code> and "
                "<code>--mj-progress-height</code>.</p>"
            ),
            html=_code("""
                <div class="stack">
                  <mj-progress size="sm" value="30" label="Small bar" show-label></mj-progress>
                  <mj-progress value="50" label="Medium bar" show-label></mj-progress>
                  <mj-progress size="lg" value="70" label="Large bar" show-label></mj-progress>
                  <div class="row">
                    <mj-progress variant="ring" size="sm" value="30" label="Small ring"></mj-progress>
                    <mj-progress variant="ring" value="50" label="Medium ring" show-value></mj-progress>
                    <mj-progress variant="ring" size="lg" value="70" label="Large ring" show-value></mj-progress>
                  </div>
                  <mj-progress class="healthy" value="88" label="Disk health" show-label show-value></mj-progress>
                </div>
            """),
            css=_ROW_CSS + "\n.healthy { --mj-progress-fill-color: var(--mj-color-success); --mj-progress-height: 0.625rem; }",
        ),
        ComponentExample(
            key="slots",
            title="Label, value-text and center slots",
            description=(
                "<p>A rich <code>label</code> slot with <code>value-text</code> and a custom "
                "<code>max</code>; a slotted <code>value-text</code>; and a ring with content in "
                "its <code>center</code> slot.</p>"
            ),
            html=_code("""
                <div class="stack">
                  <mj-progress value="3" max="5" value-text="3 of 5 files" show-label show-value>
                    <span slot="label"><b>Importing</b> contacts.csv</span>
                  </mj-progress>
                  <mj-progress value="2" max="5" label="Setup steps" show-label show-value>
                    <span slot="value-text">Step 2 of 5</span>
                  </mj-progress>
                  <mj-progress variant="ring" size="lg" value="80" label="Storage used" show-label>
                    <span slot="center">8 GB</span>
                  </mj-progress>
                </div>
            """),
            css=_ROW_CSS,
        ),
        ComponentExample(
            key="events",
            title="Live updates and events",
            description=(
                "<p>The script raises <code>value</code> by 10 every 300 ms until it reaches "
                "<code>max</code>: Events shows <code>mj-progress-change</code> and finally "
                "<code>mj-progress-complete</code>. <b>Restart</b> runs it again.</p>"
            ),
            html=_code("""
                <div class="stack">
                  <mj-progress id="video-progress" value="0" label="Uploading video.mp4" show-label show-value></mj-progress>
                  <div class="row"><button type="button" id="restart-upload">Restart</button></div>
                </div>
            """),
            css=_ROW_CSS,
            script=_code("""
                const progress = document.getElementById("video-progress")
                let timer = null

                const run = () => {
                  clearInterval(timer)
                  progress.value = 0
                  timer = setInterval(() => {
                    progress.value = Math.min(100, progress.value + 10)
                    if (progress.value >= 100) {
                      clearInterval(timer)
                    }
                  }, 300)
                }
                progress.addEventListener("mj-progress-complete", (event) => {
                  mjSandbox.log("upload complete", { percentage: progress.percentage })
                })
                document.getElementById("restart-upload").addEventListener("click", run)

                run()
            """),
        ),
    ],
    attributes=[
        AttributeDoc(name="variant", description="Shape: a block-level bar or an inline ring.",
                     kind="enum", values=["bar", "ring"], default="bar"),
        AttributeDoc(name="value", description="Current value, clamped to 0..max.", kind="number", default="0"),
        AttributeDoc(name="max", description="Maximum value (must be > 0).", kind="number", default="100"),
        AttributeDoc(name="indeterminate", description="Animated state without a known end.", kind="boolean"),
        AttributeDoc(name="label", description="Accessible name and visible label text.", kind="string"),
        AttributeDoc(name="show-label", description="Shows the label.", kind="boolean"),
        AttributeDoc(name="show-value", description="Shows value-text, else the percentage.", kind="boolean"),
        AttributeDoc(name="value-text", description="Human-readable value: aria-valuetext and the visible value.",
                     kind="string"),
        AttributeDoc(name="size", description="Bar height / ring diameter.",
                     kind="enum", values=["sm", "md", "lg"], default="md"),
    ],
    events=[
        ("mj-progress-change", "value or max changed.", "{ value: number, max: number, percentage: number }"),
        ("mj-progress-complete", "A change made value reach max.", "{ value: number, max: number }"),
    ],
    slots=[
        ("label", "Visible label (also the accessible name when `label` is absent).", "<span><b>Exporting</b> data</span>"),
        ("value-text", "Bar only: replaces the visible value (not aria-valuetext).", "<span>2 of 4</span>"),
        ("center", "Ring only: content in the middle of the ring.", "<span>50%</span>"),
    ],
    properties=[
        ("value", "number. The clamped value; setting it also removes `indeterminate`."),
        ("percentage", "number. Read-only; value / max in percent, one decimal."),
    ],
    parts=[
        ("label", "Label wrapper (bar and ring)."),
        ("value-text", "Visible value (bar row, or ring centre)."),
        ("track", "Bar track."),
        ("fill", "Bar fill (role=progressbar)."),
        ("ring", "Ring SVG (role=progressbar)."),
        ("ring-track", "Ring background circle."),
        ("ring-fill", "Ring progress circle."),
        ("center", "Ring centre wrapper."),
    ],
    css_properties=[
        ("--mj-progress-fill-color", "Fill colour (default var(--mj-accent))."),
        ("--mj-progress-track-color", "Track colour (default var(--mj-border))."),
        ("--mj-progress-height", "Bar height (default 0.5rem; sm 0.25rem, lg 0.75rem)."),
        ("--mj-progress-border-radius", "Bar radius (default var(--mj-radius-pill))."),
        ("--mj-progress-ring-size", "Ring diameter (default 3rem; sm 1.5rem, lg 5rem)."),
        ("--mj-progress-ring-stroke-width", "Ring stroke width (default 4)."),
        ("--mj-progress-label-gap", "Gap between label and track / ring (default var(--mj-space-1) bar, var(--mj-space-2) ring)."),
        ("--mj-progress-animation-duration", "Indeterminate cycle (default 1.4s bar, 1.2s ring)."),
    ],
)


# ---------------------------------------------------------------------------
# mj-badge
# ---------------------------------------------------------------------------

_AVATAR_CSS = _code("""
    .avatar {
      display: inline-grid; place-items: center;
      inline-size: 2.5rem; block-size: 2.5rem;
      border-radius: var(--mj-radius-circle);
      background: var(--mj-bg-muted); color: var(--mj-text);
      font-weight: var(--mj-font-weight-medium);
    }
""")

_BADGE = ComponentDoc(
    tag="mj-badge",
    title="Badge",
    group="feedback",
    summary="Count, dot or presence-status indicator overlaid on, or placed beside, its content.",
    description=(
        "<p><code>&lt;mj-badge&gt;</code> decorates the element in its default slot with a "
        "small indicator, overlaid on a corner (<code>placement</code>, default "
        "<code>top-end</code>) or inline after it.</p>"
        "<p>Variants: <code>count</code> (default) shows a number, capped as "
        "<code>max+</code>, and hides at 0 unless <code>show-zero</code>; <code>dot</code> is a "
        "plain dot that needs a <code>label</code>; <code>status</code> is a presence dot "
        "coloured by <code>status</code> and named after it (\"Online\") unless "
        "<code>label</code> is given.</p>"
        "<p>Text alternative: the count bubble itself is decorative; a visually hidden text "
        "carries the count followed by <code>label</code> (\"7 unread messages\"). A control "
        "that names itself with <code>aria-label</code> can include the badge with "
        "<code>getAriaLabel()</code>. <code>color</code> overrides the background only; pair a "
        "light colour with <code>--mj-badge-color</code>.</p>"
    ),
    how_to_use=(
        "<p>Wrap the element to badge. For counts set <code>count</code>, optional "
        "<code>max</code>, and a <code>label</code> describing the count. For dots give a "
        "<code>label</code>; for presence set <code>variant=\"status\"</code> and "
        "<code>status</code>. Change <code>count</code> from script and listen for "
        "<code>mj-badge-show</code> / <code>-hide</code> / <code>-overflow</code>.</p>"
    ),
    example="",
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>A count of 7 on an Inbox button (read as \"7 unread messages\") and a "
                "pulsing count capped at <code>max=\"99\"</code>.</p>"
            ),
            html=_code("""
                <div class="row">
                  <mj-badge count="7" label="unread messages"><button type="button">Inbox</button></mj-badge>
                  <mj-badge count="120" max="99" pulse label="notifications"><button type="button">Notifications</button></mj-badge>
                </div>
            """),
            css=_ROW_CSS + "\n.row { gap: var(--mj-space-6); padding: var(--mj-space-2); }",
        ),
        ComponentExample(
            key="variants",
            title="Count, dot and status",
            description=(
                "<p>A count, a labelled <code>dot</code>, and the five <code>status</code> values "
                "on avatars (bottom-end placement).</p>"
            ),
            html=_code("""
                <div class="row">
                  <mj-badge count="3" label="new messages"><span class="avatar">AL</span></mj-badge>
                  <mj-badge variant="dot" label="New activity"><span class="avatar">GH</span></mj-badge>
                  <mj-badge variant="status" status="online" placement="bottom-end"><span class="avatar">AL</span></mj-badge>
                  <mj-badge variant="status" status="away" placement="bottom-end"><span class="avatar">MK</span></mj-badge>
                  <mj-badge variant="status" status="busy" placement="bottom-end"><span class="avatar">JS</span></mj-badge>
                  <mj-badge variant="status" status="dnd" placement="bottom-end" label="Do not disturb until 15:00"><span class="avatar">RT</span></mj-badge>
                  <mj-badge variant="status" status="offline" placement="bottom-end"><span class="avatar">PV</span></mj-badge>
                </div>
            """),
            css=_ROW_CSS + "\n.row { gap: var(--mj-space-5); padding: var(--mj-space-2); }\n" + _AVATAR_CSS,
        ),
        ComponentExample(
            key="placement",
            title="Placement",
            description="<p>The four corners and <code>inline</code> (after the content, in the flow).</p>",
            html=_code("""
                <div class="row">
                  <mj-badge count="4" placement="top-end"><span class="box">top-end</span></mj-badge>
                  <mj-badge count="4" placement="top-start"><span class="box">top-start</span></mj-badge>
                  <mj-badge count="4" placement="bottom-end"><span class="box">bottom-end</span></mj-badge>
                  <mj-badge count="4" placement="bottom-start"><span class="box">bottom-start</span></mj-badge>
                  <mj-badge count="12" placement="inline" label="open issues">Issues</mj-badge>
                </div>
            """),
            css=_ROW_CSS + "\n.row { gap: var(--mj-space-6); padding: var(--mj-space-3); }\n.box { display: inline-block; padding: var(--mj-space-2) var(--mj-space-3); border: 1px solid var(--mj-border); border-radius: var(--mj-radius-md); }",
        ),
        ComponentExample(
            key="events",
            title="Changing counts",
            description=(
                "<p>A cart badge with <code>max=\"9\"</code>. The buttons change "
                "<code>count</code>; the cart button's name is rebuilt with "
                "<code>getAriaLabel()</code>. The script adds ten items and removes them again: "
                "Events shows <code>mj-badge-show</code>, <code>mj-badge-overflow</code> and "
                "<code>mj-badge-hide</code>.</p>"
            ),
            html=_code("""
                <div class="row">
                  <mj-badge id="cart-badge" count="0" max="9" label="items in cart"><button type="button" id="cart">Cart</button></mj-badge>
                  <button type="button" id="add-item">Add item</button>
                  <button type="button" id="remove-item">Remove item</button>
                  <label><input type="checkbox" id="show-zero"> show-zero</label>
                </div>
                <p id="cart-name" class="note"></p>
            """),
            css=_ROW_CSS + "\n.row { padding: var(--mj-space-2); }",
            script=_code("""
                const badge = document.getElementById("cart-badge")
                const cart = document.getElementById("cart")
                const name = document.getElementById("cart-name")
                const sync = () => {
                  cart.setAttribute("aria-label", badge.getAriaLabel("Cart"))
                  name.textContent = "Accessible name: " + cart.getAttribute("aria-label")
                }

                document.getElementById("add-item").addEventListener("click", () => { badge.count = badge.count + 1; sync() })
                document.getElementById("remove-item").addEventListener("click", () => { badge.count = Math.max(0, badge.count - 1); sync() })
                document.getElementById("show-zero").addEventListener("change", (event) => {
                  badge.toggleAttribute("show-zero", event.target.checked)
                  sync()
                })

                for (let index = 0; index < 10; index = index + 1) {
                  badge.count = badge.count + 1
                }
                mjSandbox.log("after adding", { count: badge.count, displayCount: badge.displayCount })
                badge.count = 0
                mjSandbox.log("after clearing", { indicatorHidden: badge.indicatorHidden })
                badge.count = 2
                sync()
            """),
        ),
        ComponentExample(
            key="custom-styling",
            title="Colours and sizes",
            description=(
                "<p><code>color</code> sets the background (tokens work); "
                "<code>--mj-badge-color</code>, <code>--mj-badge-size</code> and "
                "<code>--mj-badge-font-size</code> adjust the text colour and size.</p>"
            ),
            html=_code("""
                <div class="row">
                  <mj-badge count="5" color="var(--mj-color-success)" label="completed tasks"><button type="button">Tasks</button></mj-badge>
                  <mj-badge count="2" color="var(--mj-color-warning-surface)" class="on-light" label="drafts"><button type="button">Drafts</button></mj-badge>
                  <mj-badge count="18" class="large" label="mentions"><button type="button">Mentions</button></mj-badge>
                  <mj-badge variant="dot" color="var(--mj-accent)" label="Unread updates"><button type="button">Updates</button></mj-badge>
                </div>
            """),
            css=_ROW_CSS + "\n.row { gap: var(--mj-space-6); padding: var(--mj-space-3); }\n.on-light { --mj-badge-color: var(--mj-text); }\n.large { --mj-badge-size: 1.75rem; --mj-badge-font-size: var(--mj-font-size-sm); }",
        ),
    ],
    attributes=[
        AttributeDoc(name="variant", description="Indicator type.", kind="enum",
                     values=["count", "dot", "status"], default="count"),
        AttributeDoc(name="count", description="Number shown by the count variant (hidden at 0).", kind="number", default="0"),
        AttributeDoc(name="max", description="Counts above it show as `max+`.", kind="number", default="99"),
        AttributeDoc(name="show-zero", description="Shows a count of 0.", kind="boolean"),
        AttributeDoc(name="status", description="Presence of the status variant (sets colour and default name).",
                     kind="enum", values=["online", "away", "busy", "offline", "dnd"]),
        AttributeDoc(name="label", description="Text after the count (\"unread messages\"), or the name of a dot / status.",
                     kind="string"),
        AttributeDoc(name="placement", description="Corner of the overlay, or inline after the content.",
                     kind="enum", values=["top-end", "top-start", "bottom-end", "bottom-start", "inline"],
                     default="top-end"),
        AttributeDoc(name="color", description="Background colour override (wins over the status colour).", kind="color"),
        AttributeDoc(name="pulse", description="Pulsing ring animation (off with reduced motion).", kind="boolean"),
    ],
    events=[
        ("mj-badge-show", "A count badge became visible (also on first render).", "{ count: number }"),
        ("mj-badge-hide", "A visible count badge was hidden (count 0 without show-zero).", "{ count: number }"),
        ("mj-badge-overflow", "The count went above max.", "{ count: number, max: number, displayCount: string }"),
    ],
    slots=[
        ("", "The badged content.", '<button type="button">Messages</button>'),
    ],
    properties=[
        ("count", "number. The count (0 when absent or invalid); setting it writes the attribute."),
        ("displayCount", "string. Read-only; the shown text (\"\" when hidden, \"99+\" when capped)."),
        ("indicatorHidden", "boolean. Read-only; true when a count badge shows nothing. (`hidden` is the standard property.)"),
    ],
    methods=[
        ("getAriaLabel(template) -> string", "Name for the decorated control: replaces {count} in template, else appends the badge text (\"Inbox, 7 unread messages\")."),
    ],
    parts=[
        ("indicator", "The bubble / dot."),
        ("count", "The count text inside the bubble."),
    ],
    css_properties=[
        ("--mj-badge-bg", "Bubble background (default var(--mj-color-danger)); `color` and `status` override it."),
        ("--mj-badge-color", "Count text colour (default var(--mj-text-on-accent))."),
        ("--mj-badge-size", "Bubble height (default 1.25rem) or dot size (default 0.625rem)."),
        ("--mj-badge-font-size", "Count font size (default var(--mj-font-size-xs))."),
        ("--mj-badge-font-weight", "Count font weight (default var(--mj-font-weight-bold))."),
        ("--mj-badge-border-width", "Ring around the bubble (default 2px)."),
        ("--mj-badge-border-color", "Ring colour (default var(--mj-surface))."),
        ("--mj-badge-border-radius", "Bubble radius (default 9999px)."),
        ("--mj-badge-pulse-color", "Pulse colour (default var(--mj-color-danger))."),
    ],
)


# ---------------------------------------------------------------------------
# mj-chip
# ---------------------------------------------------------------------------

_CHIP = ComponentDoc(
    tag="mj-chip",
    title="Chip",
    group="feedback",
    summary="Compact pill for tags, filters and removable tokens.",
    description=(
        "<p><code>&lt;mj-chip&gt;</code> is a pill for tags, filters and token inputs, in three "
        "modes. <code>static</code> (default) only displays. <code>selectable</code> is a "
        "checkbox (<code>role=\"checkbox\"</code>, <code>aria-checked</code>) toggled by click, "
        "Enter or Space, with a check mark while <code>selected</code>. <code>removable</code> "
        "adds a remove button (named \"Remove &lt;label&gt;\" or <code>remove-label</code>) "
        "activated by click, Backspace or Delete.</p>"
        "<p>Selecting fires the cancelable <code>mj-chip-select</code>, then "
        "<code>mj-chip-change</code>. Removing fires the cancelable <code>mj-chip-remove</code>; "
        "unless cancelled the chip moves focus to the next usable chip, else the previous one, "
        "else the element named by <code>return-focus</code>, and removes itself.</p>"
        "<p><code>disabled</code> blocks interaction and takes a selectable chip out of the tab "
        "order. <code>color</code> sets the background only.</p>"
    ),
    how_to_use=(
        "<p>Put the label between the tags and choose <code>mode</code>. Give each chip a "
        "<code>value</code> and listen for <code>mj-chip-change</code> (filters) or "
        "<code>mj-chip-remove</code> (tokens). Set <code>return-focus</code> on removable "
        "tokens to send focus back to their input when the last one goes.</p>"
    ),
    example="",
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description="<p>Static, removable, selectable (one selected) and disabled chips.</p>",
            html=_code("""
                <div class="row">
                  <mj-chip>Python</mj-chip>
                  <mj-chip mode="removable" value="typescript">TypeScript</mj-chip>
                  <mj-chip mode="selectable" selected value="dark-mode">Dark mode</mj-chip>
                  <mj-chip mode="selectable" value="notifications">Notifications</mj-chip>
                  <mj-chip disabled>Disabled</mj-chip>
                </div>
            """),
            css=_ROW_CSS + "\n.row { gap: var(--mj-space-2); }",
        ),
        ComponentExample(
            key="sizes",
            title="Sizes and colours",
            description=(
                "<p><code>sm</code>, <code>md</code> and <code>lg</code>, then status chips "
                "coloured with <code>color</code> set to surface tokens.</p>"
            ),
            html=_code("""
                <div class="stack">
                  <div class="row">
                    <mj-chip size="sm">Small</mj-chip>
                    <mj-chip>Medium</mj-chip>
                    <mj-chip size="lg">Large</mj-chip>
                  </div>
                  <div class="row">
                    <mj-chip color="var(--mj-color-success-surface)">Shipped</mj-chip>
                    <mj-chip color="var(--mj-color-warning-surface)">Pending</mj-chip>
                    <mj-chip color="var(--mj-color-danger-surface)">Overdue</mj-chip>
                    <mj-chip color="var(--mj-color-info-surface)" mode="removable">Draft</mj-chip>
                  </div>
                </div>
            """),
            css=_ROW_CSS + "\n.row { gap: var(--mj-space-2); }",
        ),
        ComponentExample(
            key="with-icons",
            title="Leading icons",
            description="<p>The <code>leading-icon</code> slot on static, selectable and removable chips.</p>",
            html=_code("""
                <div class="row">
                  <mj-chip>[[tag|leading-icon]]Release 2.4</mj-chip>
                  <mj-chip mode="selectable" selected value="python">[[code|leading-icon]]Python</mj-chip>
                  <mj-chip mode="removable" value="ada">[[user|leading-icon]]Ada Lovelace</mj-chip>
                  <mj-chip mode="selectable" value="recent">[[clock|leading-icon]]Recent</mj-chip>
                </div>
            """),
            css=_ROW_CSS + "\n.row { gap: var(--mj-space-2); }",
        ),
        ComponentExample(
            key="filters",
            title="Filter group with a limit",
            description=(
                "<p>Selectable filters with at most two selected: the "
                "<code>mj-chip-select</code> handler cancels a third. The script clicks three "
                "chips; the last one is vetoed.</p>"
            ),
            html=_code("""
                <div class="row" role="group" aria-label="Filter by language" id="language-filters">
                  <mj-chip mode="selectable" value="python">Python</mj-chip>
                  <mj-chip mode="selectable" value="rust">Rust</mj-chip>
                  <mj-chip mode="selectable" value="go">Go</mj-chip>
                  <mj-chip mode="selectable" value="typescript">TypeScript</mj-chip>
                </div>
                <p id="filter-status" class="note"></p>
            """),
            css=_ROW_CSS + "\n.row { gap: var(--mj-space-2); }",
            script=_code("""
                const group = document.getElementById("language-filters")
                const status = document.getElementById("filter-status")
                const chips = Array.from(group.querySelectorAll("mj-chip"))
                const selected = () => chips.filter((chip) => chip.selected).map((chip) => chip.getAttribute("value"))
                const show = () => { status.textContent = "Selected: " + (selected().join(", ") || "none") }

                group.addEventListener("mj-chip-select", (event) => {
                  if (event.detail.selected === true && selected().length >= 2) {
                    event.preventDefault()
                    mjSandbox.log("selection vetoed", { value: event.detail.value, limit: 2 })
                  }
                })
                group.addEventListener("mj-chip-change", show)
                show()

                // Simulate clicks on three chips; the third exceeds the limit.
                for (const chip of chips.slice(0, 3)) {
                  chip.click()
                }
            """),
        ),
        ComponentExample(
            key="tokens",
            title="Removable tokens",
            description=(
                "<p>Type a name and press Enter to add a token. Remove tokens with their button "
                "or Backspace / Delete on it; focus moves to the next token, else the previous "
                "one, and to the input named by <code>return-focus</code> only when no other token is "
                "left. <b>Owner</b> cannot be removed. The script removes one token and tries to "
                "remove Owner.</p>"
            ),
            html=_code("""
                <div class="tokens" id="recipients">
                  <mj-chip mode="removable" value="owner" return-focus="recipient-input" data-locked>Owner</mj-chip>
                  <mj-chip mode="removable" value="grace" return-focus="recipient-input">Grace Hopper</mj-chip>
                  <mj-chip mode="removable" value="alan" return-focus="recipient-input">Alan Turing</mj-chip>
                  <input id="recipient-input" placeholder="Add a recipient" aria-label="Add a recipient">
                </div>
            """),
            css=_code("""
                .tokens {
                  display: flex; flex-wrap: wrap; align-items: center; gap: var(--mj-space-2);
                  padding: var(--mj-space-2); border: 1px solid var(--mj-border-strong); border-radius: var(--mj-radius-md);
                }
                .tokens input { flex: 1; min-inline-size: 8rem; border: none; background: transparent; color: var(--mj-text); font: inherit; }
            """),
            script=_code("""
                const box = document.getElementById("recipients")
                const input = document.getElementById("recipient-input")

                box.addEventListener("mj-chip-remove", (event) => {
                  if (event.target.hasAttribute("data-locked") === true) {
                    event.preventDefault()
                    mjSandbox.log("removal vetoed", { value: event.detail.value })
                  }
                })
                input.addEventListener("keydown", (event) => {
                  const text = input.value.trim()
                  if (event.key === "Enter" && text !== "") {
                    const chip = document.createElement("mj-chip")
                    chip.setAttribute("mode", "removable")
                    chip.setAttribute("value", text.toLowerCase())
                    chip.setAttribute("return-focus", "recipient-input")
                    chip.textContent = text
                    box.insertBefore(chip, input)
                    input.value = ""
                  }
                })

                box.querySelector('[value="alan"]').shadowRoot.querySelector(".remove").click()
                box.querySelector('[value="owner"]').shadowRoot.querySelector(".remove").click()
            """),
        ),
    ],
    attributes=[
        AttributeDoc(name="mode", description="Interaction style.", kind="enum",
                     values=["static", "removable", "selectable"], default="static"),
        AttributeDoc(name="selected", description="On state of a selectable chip.", kind="boolean"),
        AttributeDoc(name="value", description="Data value reported by the events.", kind="string"),
        AttributeDoc(name="disabled", description="Blocks interaction; a selectable chip leaves the tab order.",
                     kind="boolean"),
        AttributeDoc(name="size", description="Font size and padding.", kind="enum",
                     values=["sm", "md", "lg"], default="md"),
        AttributeDoc(name="remove-label", description="Accessible name of the remove button (default \"Remove <label>\").",
                     kind="string"),
        AttributeDoc(name="color", description="Background colour override.", kind="color"),
        AttributeDoc(name="return-focus", description="Id of the element focused after removal when no other chip can take focus.",
                     kind="string"),
    ],
    events=[
        ("mj-chip-select", "A selectable chip is about to toggle. Cancelable.", "{ value: string, selected: boolean }"),
        ("mj-chip-change", "A selectable chip toggled.", "{ value: string, selected: boolean }"),
        ("mj-chip-remove", "A removable chip is about to remove itself. Cancelable.", "{ value: string, labelText: string }"),
    ],
    slots=[
        ("", "The chip label.", "Design"),
        ("leading-icon", "Icon before the label.", _svg("tag")),
    ],
    properties=[
        ("selected", "boolean. Reflects `selected`; setting it fires no events."),
        ("labelText", "string. Read-only; the trimmed slotted label text."),
    ],
    methods=[
        ("click()", "Toggles a selectable chip as a user click would (mj-chip-select, then mj-chip-change); static and removable chips ignore it."),
    ],
    parts=[
        ("chip", "The pill (role=checkbox in selectable mode)."),
        ("leading-icon", "Wrapper of the leading-icon slot."),
        ("check", "Check mark of a selected chip."),
        ("label", "Wrapper of the default slot."),
        ("remove", "The remove button."),
    ],
    css_properties=[
        ("--mj-chip-bg", "Background (default var(--mj-bg-muted)); set by `color`."),
        ("--mj-chip-color", "Text colour (default var(--mj-text))."),
        ("--mj-chip-border-color", "Border colour (default var(--mj-border))."),
        ("--mj-chip-border-width", "Border width (default 1px)."),
        ("--mj-chip-border-radius", "Corner radius (default 9999px)."),
        ("--mj-chip-padding-block", "Block padding of md (default var(--mj-space-1))."),
        ("--mj-chip-padding-inline", "Inline padding of md (default var(--mj-space-3))."),
        ("--mj-chip-gap", "Gap between icon, label and button (default var(--mj-space-1))."),
        ("--mj-chip-selected-bg", "Background while selected (default var(--mj-accent))."),
        ("--mj-chip-selected-color", "Text colour while selected (default var(--mj-text-on-accent))."),
        ("--mj-chip-remove-size", "Remove button size (default 1.125rem)."),
        ("--mj-chip-disabled-opacity", "Opacity while disabled (default 0.45)."),
        ("--mj-chip-focus-ring-color", "Focus ring of the remove button (default var(--mj-focus-ring))."),
    ],
)


# ---------------------------------------------------------------------------
# mj-tooltip
# ---------------------------------------------------------------------------

_STAGE_CSS = _code("""
    .stage { display: flex; flex-wrap: wrap; justify-content: center; align-items: center; gap: var(--mj-space-6); padding: var(--mj-space-8) var(--mj-space-4); }
""")

_TOOLTIP = ComponentDoc(
    tag="mj-tooltip",
    title="Tooltip",
    group="feedback",
    summary="Short hint shown on hover or focus of its trigger, positioned beside it with an arrow.",
    description=(
        "<p><code>&lt;mj-tooltip&gt;</code> shows a short hint next to the element in its "
        "<code>trigger</code> slot when it is hovered or focused (<code>trigger</code> limits "
        "this to <code>hover</code> or <code>focus</code>), after <code>show-delay</code>, and "
        "hides it <code>hide-delay</code> after the pointer or focus leaves. The popup itself is "
        "hoverable, Escape closes it wherever focus is (without also closing a surrounding "
        "dialog), and scrolling or resizing re-anchors it.</p>"
        "<p><code>placement</code> takes <code>top</code> (default), <code>bottom</code>, "
        "<code>start</code> / <code>end</code> (follow the text direction) and "
        "<code>left</code> / <code>right</code> (physical sides), optionally with an "
        "<code>-start</code> / <code>-end</code> alignment. The popup flips to the opposite side "
        "when it does not fit, and the arrow follows the side it ended on.</p>"
        "<p>The text is the default slot, else the <code>content</code> attribute. It is also "
        "mirrored into a hidden light-DOM child (<code>slot=\"mj-tooltip-description\"</code>) "
        "that the trigger references through <code>aria-describedby</code>, so the description "
        "is available whenever the trigger has focus. <code>disabled</code> suppresses the "
        "tooltip only; the trigger stays fully interactive.</p>"
    ),
    how_to_use=(
        "<p>Slot one focusable element with <code>slot=\"trigger\"</code> and give the text in "
        "<code>content</code> (plain text) or between the tags (rich content); whitespace "
        "around the trigger does not count as content. Keep tooltips "
        "short and never put essential information or interactive controls in them. Use "
        "<code>open</code> to show one from script.</p>"
    ),
    example="",
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description="<p>Hover or focus the button: the hint appears above it after 300 ms.</p>",
            html=_code("""
                <div class="stage">
                  <mj-tooltip content="Copy to clipboard">
                    <button slot="trigger" type="button">Copy</button>
                  </mj-tooltip>
                </div>
            """),
            css=_STAGE_CSS,
        ),
        ComponentExample(
            key="placements",
            title="Placements",
            description=(
                "<p>Eight <code>open</code> tooltips around a grid, one per placement. Switch the "
                "preview to RTL: <code>start</code> / <code>end</code> swap sides, "
                "<code>left</code> / <code>right</code> would not.</p>"
            ),
            html=_code("""
                <div class="compass">
                  <mj-tooltip open placement="top-start" content="top-start"><button slot="trigger" type="button">top-start</button></mj-tooltip>
                  <mj-tooltip open placement="top" content="top"><button slot="trigger" type="button">top</button></mj-tooltip>
                  <mj-tooltip open placement="top-end" content="top-end"><button slot="trigger" type="button">top-end</button></mj-tooltip>
                  <mj-tooltip open placement="start" content="start"><button slot="trigger" type="button">start</button></mj-tooltip>
                  <span></span>
                  <mj-tooltip open placement="end" content="end"><button slot="trigger" type="button">end</button></mj-tooltip>
                  <mj-tooltip open placement="bottom-start" content="bottom-start"><button slot="trigger" type="button">bottom-start</button></mj-tooltip>
                  <mj-tooltip open placement="bottom" content="bottom"><button slot="trigger" type="button">bottom</button></mj-tooltip>
                  <mj-tooltip open placement="bottom-end" content="bottom-end"><button slot="trigger" type="button">bottom-end</button></mj-tooltip>
                </div>
            """),
            css=_code("""
                .compass {
                  display: grid; grid-template-columns: repeat(3, max-content); justify-content: center;
                  justify-items: center; align-items: center; gap: var(--mj-space-6) 7rem;
                  padding: 4rem var(--mj-space-4);
                }
                .compass button { min-inline-size: 7.5rem; }
            """),
            height=340,
        ),
        ComponentExample(
            key="rich-content",
            title="Rich content and options",
            description=(
                "<p>Rich slotted content with <code>max-width=\"220\"</code> and "
                "<code>placement=\"bottom\"</code> (open), and a tooltip without arrow "
                "(<code>arrow=\"false\"</code>) at <code>offset=\"16\"</code>.</p>"
            ),
            html=_code("""
                <div class="stage">
                  <mj-tooltip open placement="bottom" max-width="220" show-delay="0">
                    <button slot="trigger" type="button">Storage details</button>
                    <strong>8.2 GB of 10 GB used.</strong> Files in the trash count toward your quota.
                  </mj-tooltip>
                  <mj-tooltip content="No arrow, 16 px away" arrow="false" offset="16" placement="bottom" show-delay="0"><button slot="trigger" type="button">No arrow</button></mj-tooltip>
                </div>
            """),
            css=_STAGE_CSS + "\n.stage { padding-block-end: 7rem; align-items: start; }",
            height=260,
        ),
        ComponentExample(
            key="triggers",
            title="Triggers, delays and disabled",
            description=(
                "<p><code>trigger=\"focus\"</code> on a text field (Tab into it), "
                "<code>trigger=\"hover\"</code> with <code>show-delay=\"0\"</code> and "
                "<code>hide-delay=\"800\"</code>, and a <code>disabled</code> tooltip whose button "
                "still works (its click is logged).</p>"
            ),
            html=_code("""
                <div class="stage">
                  <mj-tooltip trigger="focus" content="Use 8 or more characters" placement="top"><input slot="trigger" type="password" aria-label="New password" placeholder="New password"></mj-tooltip>
                  <mj-tooltip trigger="hover" show-delay="0" hide-delay="800" content="Lingers for 800 ms"><button slot="trigger" type="button">Hover only</button></mj-tooltip>
                  <mj-tooltip disabled content="You will not see this"><button slot="trigger" type="button" id="still-works">Disabled tooltip</button></mj-tooltip>
                </div>
            """),
            css=_STAGE_CSS,
            script=_code("""
                document.getElementById("still-works").addEventListener("click", () => {
                  mjSandbox.log("trigger clicked", { tooltipDisabled: true })
                })
            """),
        ),
        ComponentExample(
            key="events",
            title="Programmatic open and events",
            description=(
                "<p>While <b>Pin the tooltip</b> is checked the <code>mj-tooltip-hide</code> "
                "handler keeps it open. The script opens it with <code>open = true</code>, then "
                "presses Escape: Events shows <code>mj-tooltip-show</code> (trigger api) and "
                "<code>mj-tooltip-hide</code> (trigger escape).</p>"
            ),
            html=_code("""
                <div class="stage">
                  <mj-tooltip id="help-tip" content="Shortcuts: Ctrl+K opens search"><button slot="trigger" type="button">Keyboard help</button></mj-tooltip>
                  <label><input type="checkbox" id="pin-tip"> Pin the tooltip</label>
                </div>
            """),
            css=_STAGE_CSS,
            script=_code("""
                const tip = document.getElementById("help-tip")
                const pin = document.getElementById("pin-tip")

                tip.addEventListener("mj-tooltip-hide", (event) => {
                  if (pin.checked === true) {
                    event.preventDefault()
                    mjSandbox.log("hide vetoed", { trigger: event.detail.trigger })
                  }
                })

                tip.open = true
                mjSandbox.log("opened", { open: tip.open, trigger: tip.triggerElement.textContent })
                document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true, cancelable: true }))
            """),
        ),
    ],
    attributes=[
        AttributeDoc(name="content", description="Plain-text tooltip (slotted content wins).", kind="string"),
        AttributeDoc(
            name="placement",
            description="Preferred side and alignment; start / end follow the direction, left / right are physical.",
            kind="enum",
            values=["top", "top-start", "top-end", "bottom", "bottom-start", "bottom-end", "start", "end", "left", "right"],
            default="top",
        ),
        AttributeDoc(name="trigger", description="Space-separated activation triggers.", kind="string",
                     values=["hover focus", "hover", "focus"], default="hover focus"),
        AttributeDoc(name="show-delay", description="Milliseconds before showing.", kind="number", default="300"),
        AttributeDoc(name="hide-delay", description="Milliseconds before hiding.", kind="number", default="100"),
        AttributeDoc(name="open", description="Shows the tooltip; reflects the open state.", kind="boolean"),
        AttributeDoc(name="disabled", description="Suppresses the tooltip; the trigger stays interactive.", kind="boolean"),
        AttributeDoc(name="arrow", description="Set to `false` to hide the arrow.", kind="boolean", default="true"),
        AttributeDoc(name="max-width", description="Maximum popup width in px (default 17.5rem).", kind="number"),
        AttributeDoc(name="offset", description="Distance from the trigger in px.", kind="number", default="8"),
    ],
    events=[
        ("mj-tooltip-show", "The tooltip is about to show. Cancelable.", "{ trigger: 'hover' | 'focus' | 'api' }"),
        ("mj-tooltip-hide", "The tooltip is about to hide. Cancelable: keeps it open.",
         "{ trigger: 'hover' | 'focus' | 'api' | 'escape' }"),
    ],
    slots=[
        ("trigger", "The element that shows the tooltip (the first slotted element).",
         '<button type="button">Help</button>'),
        ("", "Rich tooltip content; replaces `content`.", "<span><strong>Tip:</strong> press ? for shortcuts</span>"),
    ],
    properties=[
        ("open", "boolean. Showing state; setting it shows or hides (with events)."),
        ("triggerElement", "Element | null. Read-only; the slotted trigger."),
    ],
    parts=[
        ("trigger", "Wrapper of the trigger slot (display: contents)."),
        ("popup", "The tooltip box (role=tooltip)."),
        ("content", "Wrapper of the content."),
        ("arrow", "The arrow."),
    ],
    css_properties=[
        ("--mj-tooltip-bg", "Background, also of the arrow (default var(--mj-color-neutral-800))."),
        ("--mj-tooltip-color", "Text colour (default var(--mj-color-neutral-50))."),
        ("--mj-tooltip-border-color", "Border colour (default transparent)."),
        ("--mj-tooltip-border-radius", "Corner radius (default var(--mj-radius-sm))."),
        ("--mj-tooltip-shadow", "Shadow (default var(--mj-elevation-2))."),
        ("--mj-tooltip-font-size", "Font size (default var(--mj-font-size-sm))."),
        ("--mj-tooltip-max-width", "Maximum width (default 17.5rem; the max-width attribute wins)."),
        ("--mj-tooltip-padding-block", "Block padding (default var(--mj-space-1))."),
        ("--mj-tooltip-padding-inline", "Inline padding (default var(--mj-space-2))."),
        ("--mj-tooltip-arrow-size", "Arrow size (default 6px)."),
        ("--mj-tooltip-animation-duration", "Enter animation (default var(--mj-motion-fast))."),
        ("--mj-tooltip-z-index", "Stacking order (default var(--mj-layer-tooltip))."),
    ],
)


COMPONENTS = [
    _ALERT,
    _TOAST,
    _PROGRESS,
    _BADGE,
    _CHIP,
    _TOOLTIP,
]
