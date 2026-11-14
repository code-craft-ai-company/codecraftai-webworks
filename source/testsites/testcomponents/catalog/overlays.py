"""
    overlays.py

    Catalog entries for the 'Overlays' component group.

    This module exposes a module-level ``COMPONENTS`` list of ComponentDoc
    instances describing and demonstrating every overlay and contextual-layer
    component in the mj-* library: mj-dialog, mj-popover, mj-drawer,
    mj-lightbox, mj-overlay, mj-toast-region, mj-notification-center,
    mj-context-menu, mj-command-palette and mj-tour.

    Every example has a visible trigger that opens the overlay again after it
    was closed, and the ``nested`` examples put popups (select, date picker,
    popover) inside a modal surface so stacking, top-layer rendering and the
    order in which Escape closes things can be tried.
"""

import textwrap

from testcomponents.catalog.componentdoc import AttributeDoc
from testcomponents.catalog.componentdoc import ComponentDoc
from testcomponents.catalog.componentdoc import ComponentExample


def _src(text: str) -> str:
    """
        Return example source text without the indentation it has in this module.

        :param text: An indented, triple-quoted block of HTML, CSS or JavaScript.

        :returns: The dedented text with one trailing newline.
    """

    source = textwrap.dedent(text).strip("\n") + "\n"
    return source


#: Buttons and rows shared by the examples. Plain <button> elements keep the
#: event log free of the mj-click events an <mj-button> trigger would add.
_BUTTON_CSS = _src("""
    .row {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: var(--mj-space-3);
    }
    .btn {
      font: inherit;
      min-block-size: var(--mj-control-height-md);
      padding-block: 0;
      padding-inline: var(--mj-space-4);
      border: 1px solid var(--mj-border-strong);
      border-radius: var(--mj-radius-md);
      background: var(--mj-surface);
      color: var(--mj-text);
      cursor: pointer;
    }
    .btn:hover { background: var(--mj-bg-muted); }
    .btn:focus-visible {
      outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
      outline-offset: var(--mj-focus-ring-offset);
    }
    .btn.primary {
      background: var(--mj-accent);
      border-color: var(--mj-accent);
      color: var(--mj-text-on-accent);
    }
    .btn.primary:hover { background: var(--mj-accent-hover); }
    .muted { color: var(--mj-text-muted); }
""")

#: Form fields inside dialogs, drawers and popovers.
_FIELD_CSS = _src("""
    .field {
      display: grid;
      gap: var(--mj-space-1);
      margin-block-start: var(--mj-space-4);
    }
    .field input,
    .field textarea {
      font: inherit;
      padding-block: var(--mj-space-2);
      padding-inline: var(--mj-space-3);
      border: 1px solid var(--mj-border-strong);
      border-radius: var(--mj-radius-md);
      background: var(--mj-surface);
      color: var(--mj-text);
    }
    .actions {
      display: flex;
      flex-wrap: wrap;
      justify-content: flex-end;
      gap: var(--mj-space-3);
    }
""")

#: Draws placeholder photos on a canvas (the lightbox and the notification
#: avatars accept data:image/png and data:image/jpeg URLs; no network needed).
_PHOTO_JS = _src("""
    // Draws a placeholder landscape and returns it as a JPEG data URL.
    function photo(title, top, bottom) {
      const canvas = document.createElement("canvas")
      canvas.width = 1200
      canvas.height = 800
      const ctx = canvas.getContext("2d")
      const sky = ctx.createLinearGradient(0, 0, 0, canvas.height)
      sky.addColorStop(0, top)
      sky.addColorStop(1, bottom)
      ctx.fillStyle = sky
      ctx.fillRect(0, 0, canvas.width, canvas.height)
      ctx.fillStyle = "rgba(255, 255, 255, 0.85)"
      ctx.beginPath()
      ctx.arc(900, 220, 90, 0, Math.PI * 2)
      ctx.fill()
      ctx.fillStyle = "rgba(0, 0, 0, 0.28)"
      ctx.beginPath()
      ctx.moveTo(0, 800)
      ctx.quadraticCurveTo(360, 420, 760, 600)
      ctx.quadraticCurveTo(1000, 700, 1200, 520)
      ctx.lineTo(1200, 800)
      ctx.closePath()
      ctx.fill()
      ctx.fillStyle = "#ffffff"
      ctx.font = "600 64px system-ui, sans-serif"
      ctx.fillText(title, 64, 120)
      return canvas.toDataURL("image/jpeg", 0.82)
    }
""")


# ---------------------------------------------------------------------------
# mj-dialog
# ---------------------------------------------------------------------------

_DIALOG = ComponentDoc(
    tag="mj-dialog",
    title="Dialog",
    group="overlays",
    summary="Modal and non-modal dialog built on the native &lt;dialog&gt; element.",
    description=(
        "<p><code>&lt;mj-dialog&gt;</code> shows a panel above the page for a task "
        "that needs the user's attention. A modal dialog opens with the native "
        "<code>showModal()</code>: the browser puts it in the top layer, makes the "
        "rest of the page inert and paints the native <code>::backdrop</code> "
        "scrim; the component adds focus placement and wrapping, scroll lock, "
        "backdrop-click dismissal and ordered Escape handling (a select, date "
        "picker or popover open inside the dialog closes first). A non-modal "
        "dialog (<code>modal=\"false\"</code> or <code>show()</code>) has no "
        "backdrop and leaves the page usable; Escape closes it only while focus "
        "is inside it.</p>"
        "<p>Four <code>variant</code>s: <code>dialog</code> (role dialog), "
        "<code>alertdialog</code> (role alertdialog, initial focus on the last "
        "footer action), <code>confirmation</code> (built-in Cancel / Confirm "
        "buttons) and <code>prompt</code> (adds a text field; <kbd>Enter</kbd> in "
        "it confirms). Every dismissal &mdash; Escape, the close button, a "
        "backdrop click or Cancel &mdash; emits <code>mj-dialog-cancel</code> "
        "before <code>mj-dialog-close</code>; a "
        "<code>mj-dialog-before-close</code> listener can veto any close.</p>"
    ),
    how_to_use=(
        "<p>Put the body between the tags, a heading in the <code>title</code> "
        "slot (it names the dialog) and your own buttons in the <code>footer</code> "
        "slot. Open it with <code>showModal()</code> (or the <code>open</code> "
        "attribute), <code>show()</code> for a non-modal dialog, and close it with "
        "<code>close()</code> or by removing <code>open</code>. Mark the field "
        "that should receive focus with <code>autofocus</code>. Use "
        "<code>label</code> only when there is no visible title (it replaces the "
        "title as the accessible name). <code>modal</code> and "
        "<code>close-on-backdrop</code> are on unless set to the literal "
        "<code>\"false\"</code>. Focus returns to the element that had it before "
        "opening, or to <code>return-focus-id</code>.</p>"
    ),
    example="",
    attributes=[
        AttributeDoc(name="open", kind="boolean",
                     description="Present while the dialog is open; adding it opens the dialog (modal unless `modal=\"false\"`), removing it closes it (reason `api`)."),
        AttributeDoc(name="variant", kind="enum",
                     values=["dialog", "alertdialog", "confirmation", "prompt"], default="dialog",
                     description="Role and built-in actions: `confirmation` adds Cancel / Confirm, `prompt` adds a text field as well; `alertdialog`, `confirmation` and `prompt` use role alertdialog."),
        AttributeDoc(name="modal", kind="boolean", default="true",
                     description="`false` opens it non-modally: no backdrop, the page stays usable. Changing it while open reopens the dialog in the new mode."),
        AttributeDoc(name="label", kind="string",
                     description="Accessible name; replaces the `title` slot as the name, so use it only when there is no visible title."),
        AttributeDoc(name="no-close-button", kind="boolean",
                     description="Hides the built-in close button in the header (Escape still closes)."),
        AttributeDoc(name="close-on-backdrop", kind="boolean", default="true",
                     description="`false` keeps a modal dialog open when its backdrop is clicked."),
        AttributeDoc(name="close-label", kind="string", default="Close dialog",
                     description="Accessible label of the close button."),
        AttributeDoc(name="confirm-label", kind="string", values=["OK", "Delete", "Save", "Create"],
                     default="Confirm", description="Text of the built-in Confirm button (confirmation / prompt)."),
        AttributeDoc(name="cancel-label", kind="string", values=["Cancel", "Keep editing"],
                     default="Cancel", description="Text of the built-in Cancel button (confirmation / prompt)."),
        AttributeDoc(name="prompt-label", kind="string", default="Enter value",
                     description="Accessible label of the prompt variant's text field."),
        AttributeDoc(name="return-focus-id", kind="string",
                     description="Id of the element that receives focus after closing (default: the element focused before opening). Read when the dialog opens."),
    ],
    events=[
        ("mj-dialog-open", "The dialog opened (any route: attribute, show(), showModal()).",
         "{ variant: string }"),
        ("mj-dialog-before-close", "Cancelable. About to close; preventDefault() keeps it open (the `open` attribute is restored).",
         "{ reason: 'close-button' | 'escape' | 'backdrop' | 'cancel' | 'confirm' | 'api' }"),
        ("mj-dialog-cancel", "The user dismissed the dialog without confirming: Escape, the close button, a backdrop click or the built-in Cancel button (reason `cancel`). Fires just before mj-dialog-close.",
         "{ reason: 'close-button' | 'escape' | 'backdrop' | 'cancel' }"),
        ("mj-dialog-confirm", "The built-in Confirm button (or Enter in the prompt field) was activated; the dialog then closes with reason `confirm`.",
         "{ value: true | string }  (the prompt text for variant prompt)"),
        ("mj-dialog-close", "The dialog closed, once per close. `api` is close(), or removing `open`.",
         "{ variant: string, reason: 'close-button' | 'escape' | 'backdrop' | 'cancel' | 'confirm' | 'api' }"),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>A modal dialog with a title, a form field marked "
                "<code>autofocus</code> and footer buttons. It starts open; close it "
                "with Escape, the &times; button, a backdrop click or Cancel, then "
                "reopen it with <strong>Edit profile</strong>. Watch the reasons in "
                "the event log.</p>"
            ),
            html=_src("""
                <button type="button" class="btn primary" id="open-profile">Edit profile</button>

                <mj-dialog id="demo-dialog" open>
                  <span slot="title">Edit profile</span>
                  <p>Your display name appears on comments and shared documents.</p>
                  <label class="field">Display name
                    <input id="display-name" type="text" value="Ada Lovelace" autocomplete="off" autofocus>
                  </label>
                  <div slot="footer" class="actions">
                    <button type="button" class="btn" id="profile-cancel">Cancel</button>
                    <button type="button" class="btn primary" id="profile-save">Save</button>
                  </div>
                </mj-dialog>
            """),
            css=_BUTTON_CSS + _FIELD_CSS,
            script=_src("""
                const dialog = document.getElementById("demo-dialog")
                const nameInput = document.getElementById("display-name")
                document.getElementById("open-profile").addEventListener("click", () => dialog.showModal())
                document.getElementById("profile-cancel").addEventListener("click", () => dialog.close())
                document.getElementById("profile-save").addEventListener("click", () => {
                  mjSandbox.log("saved", { displayName: nameInput.value })
                  dialog.close()
                })
            """),
            height=380,
        ),
        ComponentExample(
            key="variants",
            title="Confirmation, prompt, alert",
            description=(
                "<p>The built-in variants. <code>confirmation</code> and "
                "<code>prompt</code> bring their own Cancel / Confirm buttons "
                "(labels from <code>cancel-label</code> / <code>confirm-label</code>); "
                "press <kbd>Enter</kbd> in the prompt field to confirm. The "
                "<code>alertdialog</code> has no close button, ignores backdrop "
                "clicks and focuses its last action. Confirm values and the close "
                "reasons (<code>confirm</code> / <code>cancel</code>) appear in the "
                "event log.</p>"
            ),
            html=_src("""
                <div class="row">
                  <button type="button" class="btn" id="open-confirm">Delete file…</button>
                  <button type="button" class="btn" id="open-prompt">New folder…</button>
                  <button type="button" class="btn" id="open-alert">Session warning</button>
                </div>

                <mj-dialog id="confirm-dialog" variant="confirmation" confirm-label="Delete" cancel-label="Keep file">
                  <span slot="title">Delete “quarterly-report.pdf”?</span>
                  <p>The file moves to the bin and is removed for everyone it was shared with.</p>
                </mj-dialog>

                <mj-dialog id="prompt-dialog" variant="prompt" confirm-label="Create" prompt-label="Folder name">
                  <span slot="title">New folder</span>
                  <p>Choose a name for the folder.</p>
                </mj-dialog>

                <mj-dialog id="alert-dialog" variant="alertdialog" no-close-button close-on-backdrop="false">
                  <span slot="title">Your session is about to expire</span>
                  <p>You will be signed out in 2 minutes. Unsaved changes will be lost.</p>
                  <div slot="footer" class="actions">
                    <button type="button" class="btn" id="alert-sign-out">Sign out</button>
                    <button type="button" class="btn primary" id="alert-stay">Stay signed in</button>
                  </div>
                </mj-dialog>
            """),
            css=_BUTTON_CSS + _FIELD_CSS,
            script=_src("""
                const confirmDialog = document.getElementById("confirm-dialog")
                const promptDialog = document.getElementById("prompt-dialog")
                const alertDialog = document.getElementById("alert-dialog")

                document.getElementById("open-confirm").addEventListener("click", () => confirmDialog.showModal())
                document.getElementById("open-prompt").addEventListener("click", () => promptDialog.showModal())
                document.getElementById("open-alert").addEventListener("click", () => alertDialog.showModal())

                for (const button of alertDialog.querySelectorAll("button")) {
                  button.addEventListener("click", () => {
                    mjSandbox.log("alert action", { choice: button.textContent })
                    alertDialog.close()
                  })
                }
                promptDialog.addEventListener("mj-dialog-confirm", (event) => {
                  mjSandbox.log("folder created", { name: event.detail.value })
                })
            """),
            height=380,
        ),
        ComponentExample(
            key="non-modal",
            title="Non-modal",
            description=(
                "<p><code>modal=\"false\"</code> (or <code>show()</code>): no backdrop, "
                "no focus trap, and the page behind stays usable &mdash; the counter "
                "button keeps working while the notes are open. Escape closes the "
                "dialog only while focus is inside it.</p>"
            ),
            html=_src("""
                <div class="row">
                  <button type="button" class="btn primary" id="open-notes">Show meeting notes</button>
                  <button type="button" class="btn" id="page-counter">Page button: 0 clicks</button>
                </div>

                <mj-dialog id="notes-dialog" modal="false">
                  <span slot="title">Meeting notes</span>
                  <ul>
                    <li>Ship the beta to the pilot customers on Monday.</li>
                    <li>Priya owns the migration guide.</li>
                    <li>Next review: 18 November.</li>
                  </ul>
                </mj-dialog>
            """),
            css=_BUTTON_CSS + _src("""
                #notes-dialog { --mj-dialog-width: 22rem; }
            """),
            script=_src("""
                const notes = document.getElementById("notes-dialog")
                const counter = document.getElementById("page-counter")
                let clicks = 0
                document.getElementById("open-notes").addEventListener("click", () => notes.show())
                counter.addEventListener("click", () => {
                  clicks = clicks + 1
                  counter.textContent = "Page button: " + clicks + " clicks"
                })
            """),
            height=380,
        ),
        ComponentExample(
            key="events",
            title="Vetoing a close",
            description=(
                "<p>While <em>Unsaved changes</em> is ticked, a "
                "<code>mj-dialog-before-close</code> listener calls "
                "<code>preventDefault()</code>: Escape and the &times; button are "
                "refused (logged as <em>close vetoed</em>). "
                "<code>close-on-backdrop=\"false\"</code> ignores backdrop clicks. "
                "<strong>Save</strong> clears the flag and closes.</p>"
            ),
            html=_src("""
                <button type="button" class="btn primary" id="open-editor">Edit note</button>

                <mj-dialog id="editor-dialog" close-on-backdrop="false">
                  <span slot="title">Edit note</span>
                  <label class="field">Note
                    <textarea id="note-text" rows="4">Call the venue about the projector.</textarea>
                  </label>
                  <label class="field-inline"><input type="checkbox" id="note-dirty" checked> Unsaved changes (blocks closing)</label>
                  <div slot="footer" class="actions">
                    <button type="button" class="btn primary" id="note-save">Save</button>
                  </div>
                </mj-dialog>
            """),
            css=_BUTTON_CSS + _FIELD_CSS + _src("""
                .field-inline {
                  display: flex;
                  gap: var(--mj-space-2);
                  align-items: center;
                  margin-block-start: var(--mj-space-3);
                }
            """),
            script=_src("""
                const editor = document.getElementById("editor-dialog")
                const dirty = document.getElementById("note-dirty")
                document.getElementById("open-editor").addEventListener("click", () => {
                  dirty.checked = true
                  editor.showModal()
                })
                editor.addEventListener("mj-dialog-before-close", (event) => {
                  if (dirty.checked === true) {
                    event.preventDefault()
                    mjSandbox.log("close vetoed", { reason: event.detail.reason })
                  }
                })
                document.getElementById("note-save").addEventListener("click", () => {
                  dirty.checked = false
                  editor.close()
                })
                editor.showModal()
            """),
            height=400,
        ),
        ComponentExample(
            key="nested",
            title="Nested popups and stacking",
            description=(
                "<p>A select, a date picker and a popover inside a modal dialog: their "
                "popups render in the top layer above the dialog, next to their "
                "trigger. Press <kbd>Escape</kbd> with a popup open &mdash; only the "
                "popup closes; the next Escape closes the dialog. "
                "<strong>Discard…</strong> stacks a confirmation dialog on top.</p>"
            ),
            html=_src("""
                <button type="button" class="btn primary" id="open-task">New task</button>

                <mj-dialog id="task-dialog">
                  <span slot="title">New task</span>
                  <div class="task-form">
                    <mj-select id="task-team" label="Team" placeholder="Choose a team">
                      <mj-option value="design">Design</mj-option>
                      <mj-option value="platform">Platform</mj-option>
                      <mj-option value="support">Customer support</mj-option>
                      <mj-option value="marketing">Marketing</mj-option>
                    </mj-select>
                    <label for="task-due">Due date</label>
                    <mj-date-picker id="task-due"></mj-date-picker>
                    <mj-popover id="task-help" placement="bottom-start">
                      <button slot="trigger" type="button" class="btn">What do priorities mean?</button>
                      <span slot="header">Priorities</span>
                      <p><strong>P1</strong> blocks a release, <strong>P2</strong> is planned for this cycle, <strong>P3</strong> is backlog.</p>
                    </mj-popover>
                  </div>
                  <div slot="footer" class="actions">
                    <button type="button" class="btn" id="task-discard">Discard…</button>
                    <button type="button" class="btn primary" id="task-create">Create task</button>
                  </div>
                </mj-dialog>

                <mj-dialog id="discard-dialog" variant="confirmation" confirm-label="Discard" cancel-label="Keep editing">
                  <span slot="title">Discard this task?</span>
                  <p>The team and due date you chose will be lost.</p>
                </mj-dialog>
            """),
            css=_BUTTON_CSS + _FIELD_CSS + _src("""
                .task-form {
                  display: grid;
                  gap: var(--mj-space-3);
                  justify-items: start;
                }
            """),
            script=_src("""
                const taskDialog = document.getElementById("task-dialog")
                const discardDialog = document.getElementById("discard-dialog")
                const team = document.getElementById("task-team")
                const due = document.getElementById("task-due")
                document.getElementById("open-task").addEventListener("click", () => taskDialog.showModal())
                document.getElementById("task-discard").addEventListener("click", () => discardDialog.showModal())
                discardDialog.addEventListener("mj-dialog-confirm", () => taskDialog.close())
                document.getElementById("task-create").addEventListener("click", () => {
                  mjSandbox.log("task created", { team: team.value, due: due.value })
                  taskDialog.close()
                })
                taskDialog.showModal()
            """),
            height=520,
        ),
        ComponentExample(
            key="long-content",
            title="Custom header, long content",
            description=(
                "<p>The <code>header</code> slot replaces the title row (and the "
                "&times; button), so the dialog is named with <code>label</code>. "
                "When the panel is taller than the viewport the body scrolls while "
                "header and footer stay put (the preview grows to fit it; try a short "
                "browser window). Width and padding come from "
                "<code>--mj-dialog-width</code> and <code>--mj-dialog-padding</code>.</p>"
            ),
            html=_src("""
                <button type="button" class="btn" id="open-terms">Review terms of service</button>

                <mj-dialog id="terms-dialog" label="Terms of service">
                  <div slot="header" class="terms-header">
                    <strong>Terms of service</strong>
                    <span class="muted">Updated 1 November 2026</span>
                  </div>
                  <h3>1. Your account</h3>
                  <p>You are responsible for the activity on your account and for keeping your password secure. Tell us at once if you suspect unauthorised use.</p>
                  <h3>2. Your content</h3>
                  <p>You keep ownership of everything you upload. You grant us the limited licence we need to store, back up and display it to the people you share it with.</p>
                  <h3>3. Acceptable use</h3>
                  <p>Do not use the service to send spam, distribute malware, or infringe the rights of others. We may suspend accounts that put other customers at risk.</p>
                  <h3>4. Payment</h3>
                  <p>Paid plans renew automatically each month. You can cancel at any time; the plan stays active until the end of the period you paid for.</p>
                  <h3>5. Changes</h3>
                  <p>We will give you 30 days' notice of material changes to these terms by email and in the product.</p>
                  <div slot="footer" class="actions">
                    <button type="button" class="btn" id="terms-decline">Decline</button>
                    <button type="button" class="btn primary" id="terms-accept">Accept</button>
                  </div>
                </mj-dialog>
            """),
            css=_BUTTON_CSS + _FIELD_CSS + _src("""
                #terms-dialog {
                  --mj-dialog-width: 36rem;
                  --mj-dialog-padding: var(--mj-space-5);
                }
                .terms-header {
                  display: grid;
                  gap: var(--mj-space-1);
                }
                #terms-dialog h3 {
                  margin-block: var(--mj-space-4) var(--mj-space-1);
                  font-size: var(--mj-font-size-md);
                }
            """),
            script=_src("""
                const terms = document.getElementById("terms-dialog")
                document.getElementById("open-terms").addEventListener("click", () => terms.showModal())
                for (const id of ["terms-decline", "terms-accept"]) {
                  document.getElementById(id).addEventListener("click", () => {
                    mjSandbox.log("terms", { choice: id === "terms-accept" ? "accepted" : "declined" })
                    terms.close()
                  })
                }
                terms.showModal()
            """),
            height=480,
        ),
    ],
    slots=[
        ("", "Dialog body (scrolls when it is taller than the viewport).",
         "<p>Body text added by the slot inspector.</p>"),
        ("title", "Heading shown in the header; names the dialog unless `label` is set.",
         "<span>Rename file</span>"),
        ("header", "Replaces the whole header row, including the title and the close button.",
         '<div><strong>Custom header</strong></div>'),
        ("footer", "Action row; replaces the built-in Cancel / Confirm buttons. The footer is hidden while it is empty (variants dialog and alertdialog).",
         '<div class="actions"><button type="button" class="btn">Cancel</button><button type="button" class="btn primary">OK</button></div>'),
        ("close-icon", "Content of the close button (default ✕).",
         '<svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true"><path d="M3 3l10 10M13 3L3 13" stroke="currentColor" stroke-width="2"/></svg>'),
    ],
    properties=[
        ("open", "boolean. Reflects the `open` attribute; setting it opens or closes the dialog."),
        ("promptValue", "string (read-only). Current text of the prompt variant's field."),
        ("nativeDialog", "HTMLDialogElement (read-only). The native dialog inside the shadow root."),
        ("returnFocusEl", "Element | null. Where focus goes after closing; filled on open when still null, cleared after the close."),
    ],
    methods=[
        ("showModal()", "Opens the dialog as a modal (removes `modal`, sets `open`)."),
        ("show()", "Opens the dialog non-modally (sets `modal=\"false\"` and `open`)."),
        ("close()", "Closes the dialog with reason `api` (a before-close listener may veto it)."),
    ],
    parts=[
        ("dialog", "The native <dialog> panel."),
        ("header", "Title row."),
        ("title", "Wrapper of the title slot."),
        ("close-button", "The built-in close button."),
        ("body", "Scrolling content area."),
        ("prompt-input", "Text field of the prompt variant."),
        ("footer", "Action row."),
        ("cancel-button", "Built-in Cancel button (confirmation / prompt)."),
        ("confirm-button", "Built-in Confirm button (confirmation / prompt)."),
    ],
    css_properties=[
        ("--mj-dialog-width", "Panel inline size (default 32rem, never wider than the viewport minus a margin)."),
        ("--mj-dialog-padding", "Inline padding of header and footer and padding of the body (default var(--mj-space-6))."),
        ("--mj-dialog-radius", "Panel corner radius (default var(--mj-radius-lg))."),
        ("--mj-dialog-shadow", "Panel shadow (default var(--mj-elevation-3))."),
        ("--mj-overlay-scrim", "Colour of the modal ::backdrop (theme token, default rgba(20, 24, 31, 0.55))."),
    ],
)


# ---------------------------------------------------------------------------
# mj-popover
# ---------------------------------------------------------------------------

_POPOVER_PLACEMENTS = [
    "top", "top-start", "top-end",
    "bottom", "bottom-start", "bottom-end",
    "start", "start-top", "start-bottom",
    "end", "end-top", "end-bottom",
]

_POPOVER = ComponentDoc(
    tag="mj-popover",
    title="Popover",
    group="overlays",
    summary="Anchored, non-modal panel for rich contextual content, opened by click or by hover/focus.",
    description=(
        "<p><code>&lt;mj-popover&gt;</code> shows a floating panel (role dialog, "
        "non-modal) anchored to a trigger. The panel is rendered in the top "
        "layer, so it sits above dialogs and drawers and is never clipped by an "
        "<code>overflow</code> ancestor; it flips to the opposite side when there "
        "is no room and shifts to stay in the viewport. The trigger gets "
        "<code>aria-haspopup=\"dialog\"</code> and <code>aria-expanded</code>.</p>"
        "<p>With <code>variant=\"popover\"</code> (default) the trigger toggles it "
        "on click / Enter / Space and the first focusable element in the panel "
        "receives focus. With <code>variant=\"hovercard\"</code> it opens after "
        "<code>hover-delay</code> when the pointer rests on the trigger, and also "
        "when the trigger receives keyboard focus; it stays open while pointer or "
        "focus is in the trigger or the panel and leaves focus where it is. Light "
        "dismiss (default on) closes it on a press outside and on Escape wherever "
        "focus is; with <code>light-dismiss=\"false\"</code> Escape works only "
        "inside the panel or on the trigger.</p>"
    ),
    how_to_use=(
        "<p>Slot the trigger (<code>slot=\"trigger\"</code>; a native "
        "<code>&lt;button&gt;</code> is best) or point <code>trigger-id</code> at "
        "an element elsewhere in the page. The body goes between the tags; "
        "<code>header</code> and <code>footer</code> slots take no space while "
        "empty. The panel is named by <code>label</code>, else the header, else "
        "the trigger text. <code>placement</code> takes a side "
        "(<code>top</code>, <code>bottom</code>, <code>start</code>, "
        "<code>end</code> &mdash; start/end are logical and swap in RTL) and an "
        "optional alignment (<code>bottom-start</code>, <code>end-top</code> "
        "...); <code>computedPlacement</code> tells where it really went. Open "
        "and close from script with <code>show()</code> / <code>close()</code> "
        "or the <code>open</code> attribute.</p>"
    ),
    example="",
    attributes=[
        AttributeDoc(name="open", kind="boolean",
                     description="Present while open; adding it opens the popover, removing it closes it (reason `api`)."),
        AttributeDoc(name="variant", kind="enum", values=["popover", "hovercard"], default="popover",
                     description="`popover` toggles on click / Enter / Space; `hovercard` opens on hover (after `hover-delay`) and on keyboard focus of the trigger."),
        AttributeDoc(name="placement", kind="enum", values=_POPOVER_PLACEMENTS, default="bottom",
                     description="Preferred side and alignment relative to the trigger. start / end are logical (they swap in RTL); the side flips when there is no room."),
        AttributeDoc(name="offset", kind="number", default="8",
                     description="Gap in pixels between the trigger and the panel."),
        AttributeDoc(name="arrow", kind="boolean",
                     description="Shows an arrow pointing at the trigger (`arrow=\"false\"` hides it again)."),
        AttributeDoc(name="light-dismiss", kind="boolean", default="true",
                     description="`false` keeps it open on outside presses; Escape then closes it only from inside the panel or the trigger."),
        AttributeDoc(name="trigger-id", kind="string",
                     description="Id of an element elsewhere in the document to use as the trigger instead of the trigger slot."),
        AttributeDoc(name="hover-delay", kind="number", default="200",
                     description="Hovercard: milliseconds the pointer must rest on the trigger before it opens."),
        AttributeDoc(name="hover-out-delay", kind="number", default="300",
                     description="Hovercard: milliseconds before it closes after pointer and focus have left trigger and panel."),
        AttributeDoc(name="no-close-button", kind="boolean",
                     description="Hides the built-in close button."),
        AttributeDoc(name="label", kind="string",
                     description="Accessible name of the panel (default: the header slot, else the trigger text)."),
        AttributeDoc(name="close-label", kind="string", default="Close",
                     description="Accessible label of the close button."),
    ],
    events=[
        ("mj-popover-before-open", "Cancelable. About to open; preventDefault() keeps it closed (an `open` attribute that asked for it is removed).",
         "{ reason: 'trigger' | 'hover' | 'focus' | 'api' }"),
        ("mj-popover-open", "Opened, once per open.", "{ placement: string }"),
        ("mj-popover-placement-change", "The resolved placement changed while open (flip after scrolling or resizing).",
         "{ placement: string }"),
        ("mj-popover-before-close", "Cancelable. About to close; preventDefault() keeps it open.",
         "{ reason: 'trigger' | 'close-button' | 'light-dismiss' | 'escape' | 'hover' | 'api' }"),
        ("mj-popover-close", "Closed, once per close. The built-in close button reports reason `close-button`, a trigger click `trigger`.",
         "{ reason: 'trigger' | 'close-button' | 'light-dismiss' | 'escape' | 'hover' | 'api' }"),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>A click popover with header, body and footer. It starts open; "
                "close it with the &times; button, Escape, a click outside or the "
                "trigger, and reopen it with <strong>Storage details</strong>.</p>"
            ),
            html=_src("""
                <mj-popover id="demo-popover" placement="bottom" open>
                  <button slot="trigger" type="button" class="btn">Storage details</button>
                  <span slot="header">Storage</span>
                  <p>You are using <strong>7.4 GB</strong> of your 15 GB plan. Attachments in Mail count towards the total.</p>
                  <div slot="footer" class="actions">
                    <button type="button" class="btn" id="manage-storage">Manage storage</button>
                  </div>
                </mj-popover>
            """),
            css=_BUTTON_CSS + _FIELD_CSS + _src("""
                body { padding: var(--mj-space-4); }
            """),
            script=_src("""
                const popover = document.getElementById("demo-popover")
                document.getElementById("manage-storage").addEventListener("click", () => {
                  mjSandbox.log("manage storage", {})
                  popover.close()
                })
            """),
            height=280,
        ),
        ComponentExample(
            key="placements",
            title="Placements and arrow",
            description=(
                "<p>Four popovers with <code>arrow</code> on different sides and "
                "alignments. The first one is driven by the controls: try every "
                "<code>placement</code> and <code>offset</code>, then switch the "
                "preview to RTL &mdash; <code>start</code> / <code>end</code> swap "
                "sides.</p>"
            ),
            html=_src("""
                <div class="placement-grid">
                  <mj-popover placement="top" arrow>
                    <button slot="trigger" type="button" class="btn">Top</button>
                    <p>Placed above its trigger.</p>
                  </mj-popover>
                  <mj-popover placement="start" arrow>
                    <button slot="trigger" type="button" class="btn">Start</button>
                    <p>On the inline-start side.</p>
                  </mj-popover>
                  <mj-popover placement="end-top" arrow>
                    <button slot="trigger" type="button" class="btn">End, top-aligned</button>
                    <p>Beside the trigger, on the inline-end side.</p>
                  </mj-popover>
                  <mj-popover placement="bottom-start" arrow>
                    <button slot="trigger" type="button" class="btn">Bottom, start-aligned</button>
                    <p>Below, lined up with the trigger's start edge.</p>
                  </mj-popover>
                </div>
            """),
            css=_BUTTON_CSS + _src("""
                .placement-grid {
                  display: grid;
                  grid-template-columns: repeat(2, max-content);
                  justify-content: center;
                  gap: var(--mj-space-8);
                  padding-block: 7rem 10rem;
                }
                .placement-grid mj-popover { --mj-popover-width: 13rem; }
            """),
            script=_src("""
                document.querySelector("mj-popover").show()
            """),
            height=440,
        ),
        ComponentExample(
            key="hovercard",
            title="Hovercard",
            description=(
                "<p><code>variant=\"hovercard\"</code>: rest the pointer on "
                "<strong>@ada</strong> (opens after <code>hover-delay</code>) or Tab "
                "to it (opens on focus). It stays open while the pointer or focus is "
                "in the card, so its button can be reached; it closes "
                "<code>hover-out-delay</code> ms after both have left.</p>"
            ),
            html=_src("""
                <p class="comment">
                  Reviewed by
                  <mj-popover variant="hovercard" placement="top-start" hover-delay="300" hover-out-delay="250" no-close-button>
                    <button slot="trigger" type="button" class="mention">@ada</button>
                    <div class="profile">
                      <strong>Ada Lovelace</strong>
                      <span class="muted">Staff engineer · London · 14:05 local time</span>
                      <button type="button" class="btn" id="message-ada">Send message</button>
                    </div>
                  </mj-popover>
                  and merged into <code>main</code> on 3 November.
                </p>
            """),
            css=_BUTTON_CSS + _src("""
                .comment { margin-block-start: 8rem; padding-inline: var(--mj-space-4); }
                .mention {
                  font: inherit;
                  padding: 0;
                  border: 0;
                  background: none;
                  color: var(--mj-accent);
                  cursor: pointer;
                  text-decoration: underline;
                }
                .profile { display: grid; gap: var(--mj-space-2); justify-items: start; }
            """),
            script=_src("""
                document.getElementById("message-ada").addEventListener("click", () => {
                  mjSandbox.log("message", { to: "ada" })
                })
            """),
            height=300,
        ),
        ComponentExample(
            key="external-trigger",
            title="External trigger, no light dismiss",
            description=(
                "<p><code>trigger-id</code> wires a button outside the element. With "
                "<code>light-dismiss=\"false\"</code> clicks outside leave the filter "
                "panel open; Escape still closes it from inside the panel or the "
                "trigger. <strong>Apply</strong> updates the trigger text and closes "
                "it with <code>close()</code>.</p>"
            ),
            html=_src("""
                <div class="row toolbar">
                  <button type="button" class="btn" id="filter-button">Filters (0)</button>
                  <span class="muted" id="result-count">24 issues</span>
                </div>

                <mj-popover id="filter-popover" trigger-id="filter-button" placement="bottom-start" light-dismiss="false">
                  <span slot="header">Filter issues</span>
                  <fieldset class="checks">
                    <legend>Status</legend>
                    <label><input type="checkbox" value="open"> Open</label>
                    <label><input type="checkbox" value="review"> In review</label>
                    <label><input type="checkbox" value="done"> Done</label>
                  </fieldset>
                  <div slot="footer" class="actions">
                    <button type="button" class="btn" id="filter-clear">Clear</button>
                    <button type="button" class="btn primary" id="filter-apply">Apply</button>
                  </div>
                </mj-popover>
            """),
            css=_BUTTON_CSS + _FIELD_CSS + _src("""
                .toolbar { padding: var(--mj-space-4); }
                .checks { display: grid; gap: var(--mj-space-2); border: 0; padding: 0; margin: 0; }
            """),
            script=_src("""
                const popover = document.getElementById("filter-popover")
                const trigger = document.getElementById("filter-button")
                const boxes = popover.querySelectorAll("input[type=checkbox]")
                document.getElementById("filter-clear").addEventListener("click", () => {
                  for (const box of boxes) { box.checked = false }
                })
                document.getElementById("filter-apply").addEventListener("click", () => {
                  const chosen = Array.from(boxes).filter((box) => box.checked).map((box) => box.value)
                  trigger.textContent = "Filters (" + chosen.length + ")"
                  mjSandbox.log("filters applied", { status: chosen })
                  popover.close()
                })
            """),
            height=340,
        ),
        ComponentExample(
            key="nested",
            title="Select inside a popover",
            description=(
                "<p>An <code>&lt;mj-select&gt;</code> inside the popover. Open the "
                "select and press <kbd>Escape</kbd>: only its list closes; the next "
                "Escape closes the popover and focus returns to "
                "<strong>Share…</strong>. A click inside the select's list does not "
                "count as an outside click.</p>"
            ),
            html=_src("""
                <mj-popover id="share-popover" placement="bottom-start">
                  <button slot="trigger" type="button" class="btn">Share…</button>
                  <span slot="header">Share “Roadmap 2027”</span>
                  <div class="share-form">
                    <mj-select id="share-access" label="People with the link can" value="view">
                      <mj-option value="view">View</mj-option>
                      <mj-option value="comment">Comment</mj-option>
                      <mj-option value="edit">Edit</mj-option>
                    </mj-select>
                    <label><input type="checkbox" id="share-notify" checked> Notify people by email</label>
                  </div>
                  <div slot="footer" class="actions">
                    <button type="button" class="btn primary" id="share-done">Done</button>
                  </div>
                </mj-popover>
            """),
            css=_BUTTON_CSS + _FIELD_CSS + _src("""
                body { padding: var(--mj-space-4); }
                .share-form { display: grid; gap: var(--mj-space-3); }
            """),
            script=_src("""
                const popover = document.getElementById("share-popover")
                document.getElementById("share-done").addEventListener("click", () => {
                  mjSandbox.log("sharing", {
                    access: document.getElementById("share-access").value,
                    notify: document.getElementById("share-notify").checked
                  })
                  popover.close()
                })
                popover.show()
            """),
            height=360,
        ),
    ],
    slots=[
        ("trigger", "The element that opens the popover (its first slotted element). Ignored when `trigger-id` is set.",
         '<button type="button" class="btn">Open popover</button>'),
        ("", "Panel body.", "<p>Body text added by the slot inspector.</p>"),
        ("header", "Heading row of the panel; names the panel unless `label` is set. Hidden while empty.",
         "<span>Sample heading</span>"),
        ("footer", "Action row of the panel. Hidden while empty.",
         '<div class="actions"><button type="button" class="btn">Cancel</button><button type="button" class="btn primary">Apply</button></div>'),
    ],
    properties=[
        ("open", "boolean. Reflects the `open` attribute; setting it opens or closes."),
        ("triggerEl", "Element | null (read-only). The resolved trigger."),
        ("popupEl", "HTMLElement (read-only). The floating panel in the shadow root."),
        ("computedPlacement", "string | null (read-only). Placement in effect after flipping; null while closed."),
    ],
    methods=[
        ("show()", "Opens the popover (reason `api`)."),
        ("close()", "Closes the popover (reason `api`)."),
    ],
    parts=[
        ("popup", "The floating panel."),
        ("arrow", "The arrow (shown with the `arrow` attribute)."),
        ("header", "Header row."),
        ("body", "Body wrapper."),
        ("footer", "Footer row."),
        ("close-button", "The built-in close button."),
    ],
    css_properties=[
        ("--mj-popover-width", "Panel width (default 18rem)."),
        ("--mj-popover-padding", "Panel padding (default var(--mj-space-4))."),
        ("--mj-popover-radius", "Panel corner radius (default var(--mj-radius-md))."),
        ("--mj-popover-shadow", "Panel shadow (default var(--mj-elevation-3))."),
        ("--mj-popover-arrow-size", "Size of the arrow square (default 10px)."),
    ],
)


# ---------------------------------------------------------------------------
# mj-drawer
# ---------------------------------------------------------------------------

_DRAWER = ComponentDoc(
    tag="mj-drawer",
    title="Drawer",
    group="overlays",
    summary="Panel that slides in from a viewport edge, for navigation, filters or details.",
    description=(
        "<p><code>&lt;mj-drawer&gt;</code> slides a panel in from the "
        "<code>start</code>, <code>end</code> (default), <code>top</code> or "
        "<code>bottom</code> edge; start and end follow the writing direction. "
        "A modal drawer (default) is a dialog: it shows an "
        "<code>&lt;mj-overlay&gt;</code> backdrop, sits in the top layer, makes the "
        "page behind it inert, locks scrolling and traps focus. With "
        "<code>modal=\"false\"</code> it is a complementary region without "
        "backdrop or focus trap; it still overlays the page (there is no push "
        "mode) and Escape closes it only while focus is inside.</p>"
        "<p>A closed drawer is hidden and inert, so its content cannot be focused. "
        "Popups opened inside the panel (select, date picker, popover) render "
        "above it and Escape closes them first. The <code>bottom</code> edge shows "
        "a drag handle: dragging it down by more than 40% of the panel height "
        "(mouse, pen or touch) closes the sheet with reason <code>swipe</code>.</p>"
    ),
    how_to_use=(
        "<p>Put the content between the tags and a heading in the "
        "<code>title</code> slot (it names the panel); the <code>header</code> slot "
        "replaces the whole header including the close button, the "
        "<code>footer</code> slot adds a pinned action row. Open it with "
        "<code>show()</code> or the <code>open</code> attribute and close it with "
        "<code>close()</code>. Size the panel with <code>size</code> (any CSS "
        "length; width for start/end, height for top/bottom) or "
        "<code>--mj-drawer-size</code>, which wins over the attribute. Mark a field "
        "<code>autofocus</code> to focus it on open.</p>"
    ),
    example="",
    attributes=[
        AttributeDoc(name="open", kind="boolean",
                     description="Present while open; adding it slides the panel in, removing it closes it (reason `api`)."),
        AttributeDoc(name="edge", kind="enum", values=["start", "end", "top", "bottom"], default="end",
                     description="Edge the panel slides in from; start / end are logical and swap in RTL. `bottom` adds the drag handle."),
        AttributeDoc(name="modal", kind="boolean", default="true",
                     description="`false`: no backdrop, focus trap or inert page; role complementary instead of dialog."),
        AttributeDoc(name="size", kind="string", values=["16rem", "24rem", "50vw", "60dvh"],
                     description="Panel width (start / end) or height (top / bottom) as a CSS length (default 20rem). Overridden by `--mj-drawer-size`."),
        AttributeDoc(name="label", kind="string",
                     description="Accessible name of the panel; replaces the `title` slot as the name."),
        AttributeDoc(name="close-label", kind="string", default="Close",
                     description="Accessible label of the close button."),
        AttributeDoc(name="no-close-button", kind="boolean",
                     description="Hides the built-in close button."),
        AttributeDoc(name="close-on-backdrop", kind="boolean", default="true",
                     description="`false` keeps a modal drawer open when the backdrop is clicked."),
        AttributeDoc(name="swipe-to-dismiss", kind="boolean", default="true",
                     description="`false` disables drag-to-close on the bottom sheet's handle."),
        AttributeDoc(name="return-focus-id", kind="string",
                     description="Id of the element that receives focus after closing (default: the element focused before opening). Read on open."),
    ],
    events=[
        ("mj-drawer-open", "The drawer opened.", "{ edge: string }"),
        ("mj-drawer-before-close", "Cancelable. About to close; preventDefault() keeps it open.",
         "{ reason: 'close-button' | 'escape' | 'backdrop' | 'swipe' | 'api' }"),
        ("mj-drawer-close", "The drawer closed, once per close.",
         "{ edge: string, reason: 'close-button' | 'escape' | 'backdrop' | 'swipe' | 'api' }"),
        ("mj-drawer-swipe", "During a drag on the bottom sheet's handle.", "{ progress: number }  (0-1 of the panel height)"),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>A modal navigation drawer on the end edge, open on load. Close it "
                "with &times;, Escape, the backdrop or a link, and reopen it with "
                "<strong>Open navigation</strong>; while it is open the page behind "
                "is inert.</p>"
            ),
            html=_src("""
                <button type="button" class="btn primary" id="open-nav">Open navigation</button>

                <mj-drawer id="demo-drawer" open edge="end">
                  <span slot="title">Workspace</span>
                  <nav aria-label="Workspace">
                    <ul class="drawer-nav">
                      <li><a href="#inbox" aria-current="page">Inbox</a></li>
                      <li><a href="#projects">Projects</a></li>
                      <li><a href="#reports">Reports</a></li>
                      <li><a href="#settings">Settings</a></li>
                    </ul>
                  </nav>
                  <div slot="footer" class="actions">
                    <button type="button" class="btn" id="nav-sign-out">Sign out</button>
                  </div>
                </mj-drawer>
            """),
            css=_BUTTON_CSS + _FIELD_CSS + _src("""
                .drawer-nav { list-style: none; margin: 0; padding: 0; display: grid; gap: var(--mj-space-1); }
                .drawer-nav a {
                  display: block;
                  padding-block: var(--mj-space-2);
                  padding-inline: var(--mj-space-3);
                  border-radius: var(--mj-radius-md);
                  color: var(--mj-text);
                  text-decoration: none;
                }
                .drawer-nav a:hover { background: var(--mj-bg-muted); }
                .drawer-nav a[aria-current="page"] { background: var(--mj-bg-muted); font-weight: var(--mj-font-weight-medium); }
            """),
            script=_src("""
                const drawer = document.getElementById("demo-drawer")
                document.getElementById("open-nav").addEventListener("click", () => drawer.show())
                for (const link of drawer.querySelectorAll("nav a")) {
                  link.addEventListener("click", (event) => {
                    event.preventDefault()
                    mjSandbox.log("navigate", { to: link.getAttribute("href") })
                    drawer.close()
                  })
                }
                document.getElementById("nav-sign-out").addEventListener("click", () => drawer.close())
            """),
            height=420,
        ),
        ComponentExample(
            key="edges",
            title="Edges and size",
            description=(
                "<p>One drawer, four edges: each button sets <code>edge</code> and "
                "calls <code>show()</code>. <code>size=\"18rem\"</code> is the width "
                "on start / end and the height on top / bottom. Switch the preview to "
                "RTL to see start and end swap sides.</p>"
            ),
            html=_src("""
                <div class="row">
                  <button type="button" class="btn" data-edge="start">Start</button>
                  <button type="button" class="btn" data-edge="end">End</button>
                  <button type="button" class="btn" data-edge="top">Top</button>
                  <button type="button" class="btn" data-edge="bottom">Bottom</button>
                </div>

                <mj-drawer id="edge-drawer" edge="start" size="18rem">
                  <span slot="title" id="edge-title">Edge: start</span>
                  <p>The panel slides in from the chosen edge. Its size comes from the <code>size</code> attribute.</p>
                </mj-drawer>
            """),
            css=_BUTTON_CSS,
            script=_src("""
                const drawer = document.getElementById("edge-drawer")
                for (const button of document.querySelectorAll("[data-edge]")) {
                  button.addEventListener("click", () => {
                    drawer.setAttribute("edge", button.dataset.edge)
                    document.getElementById("edge-title").textContent = "Edge: " + button.dataset.edge
                    drawer.show()
                  })
                }
            """),
            height=420,
        ),
        ComponentExample(
            key="bottom-sheet",
            title="Bottom sheet with drag handle",
            description=(
                "<p><code>edge=\"bottom\"</code> renders the <code>drag-handle</code>. "
                "Drag the handle down (mouse works too): "
                "<code>mj-drawer-swipe</code> reports the progress, and letting go "
                "past 40% closes the sheet with reason <code>swipe</code>. The footer "
                "slot holds the Cancel action.</p>"
            ),
            html=_src("""
                <button type="button" class="btn primary" id="open-sheet">Share photo…</button>

                <mj-drawer id="share-sheet" edge="bottom" size="17rem" label="Share photo">
                  <div class="share-grid">
                    <button type="button" class="btn" data-target="link">Copy link</button>
                    <button type="button" class="btn" data-target="email">Email</button>
                    <button type="button" class="btn" data-target="messages">Messages</button>
                    <button type="button" class="btn" data-target="device">Save to device</button>
                  </div>
                  <div slot="footer" class="actions">
                    <button type="button" class="btn" id="sheet-cancel">Cancel</button>
                  </div>
                </mj-drawer>
            """),
            css=_BUTTON_CSS + _FIELD_CSS + _src("""
                .share-grid {
                  display: grid;
                  grid-template-columns: repeat(auto-fit, minmax(9rem, 1fr));
                  gap: var(--mj-space-3);
                }
            """),
            script=_src("""
                const sheet = document.getElementById("share-sheet")
                document.getElementById("open-sheet").addEventListener("click", () => sheet.show())
                document.getElementById("sheet-cancel").addEventListener("click", () => sheet.close())
                for (const button of sheet.querySelectorAll("[data-target]")) {
                  button.addEventListener("click", () => {
                    mjSandbox.log("share", { target: button.dataset.target })
                    sheet.close()
                  })
                }
                sheet.show()
            """),
            height=420,
        ),
        ComponentExample(
            key="non-modal",
            title="Non-modal side panel",
            description=(
                "<p><code>modal=\"false\"</code>: no backdrop, no focus trap, the page "
                "stays usable (the <em>Mark as done</em> button keeps working). The "
                "<code>header</code> slot replaces the built-in header with its own "
                "close button; Escape closes the panel only while focus is in it.</p>"
            ),
            html=_src("""
                <div class="issue">
                  <h3>Checkout fails for saved cards</h3>
                  <p class="muted">Reported by Grace Hopper · 2 hours ago</p>
                  <div class="row">
                    <button type="button" class="btn primary" id="toggle-details">Toggle details panel</button>
                    <button type="button" class="btn" id="mark-done">Mark as done</button>
                  </div>
                </div>

                <mj-drawer id="details-drawer" modal="false" size="16rem" label="Issue details">
                  <div slot="header" class="details-header">
                    <strong>Details</strong>
                    <button type="button" class="btn" id="details-close">Close</button>
                  </div>
                  <dl class="details">
                    <dt>Status</dt><dd id="issue-status">Open</dd>
                    <dt>Assignee</dt><dd>Linus Torvalds</dd>
                    <dt>Priority</dt><dd>P1</dd>
                    <dt>Labels</dt><dd>payments, regression</dd>
                  </dl>
                </mj-drawer>
            """),
            css=_BUTTON_CSS + _src("""
                .issue { padding: var(--mj-space-4); max-inline-size: 26rem; }
                .issue h3 { margin-block: 0 var(--mj-space-1); }
                .details-header {
                  display: flex;
                  justify-content: space-between;
                  align-items: center;
                  inline-size: 100%;
                }
                .details { display: grid; grid-template-columns: auto 1fr; gap: var(--mj-space-2) var(--mj-space-4); margin: 0; }
                .details dt { color: var(--mj-text-muted); }
                .details dd { margin: 0; }
            """),
            script=_src("""
                const drawer = document.getElementById("details-drawer")
                document.getElementById("toggle-details").addEventListener("click", () => {
                  if (drawer.open === true) {
                    drawer.close()
                  } else {
                    drawer.show()
                  }
                })
                document.getElementById("details-close").addEventListener("click", () => drawer.close())
                document.getElementById("mark-done").addEventListener("click", () => {
                  document.getElementById("issue-status").textContent = "Done"
                  mjSandbox.log("status", { status: "done" })
                })
                drawer.show()
            """),
            height=380,
        ),
        ComponentExample(
            key="nested",
            title="Popups inside a drawer",
            description=(
                "<p>A filter drawer with a select, a date picker and a help popover. "
                "Their popups open above the panel, next to their triggers. With a "
                "popup open, <kbd>Escape</kbd> closes only the popup; the next Escape "
                "closes the drawer.</p>"
            ),
            html=_src("""
                <button type="button" class="btn primary" id="open-filters">Filters</button>

                <mj-drawer id="filter-drawer" edge="start" size="20rem">
                  <span slot="title">Filter orders</span>
                  <div class="filter-form">
                    <mj-select id="filter-status" label="Status" placeholder="Any status">
                      <mj-option value="pending">Pending</mj-option>
                      <mj-option value="shipped">Shipped</mj-option>
                      <mj-option value="delivered">Delivered</mj-option>
                      <mj-option value="returned">Returned</mj-option>
                    </mj-select>
                    <label for="filter-from">Placed after</label>
                    <mj-date-picker id="filter-from"></mj-date-picker>
                    <mj-popover placement="bottom-start">
                      <button slot="trigger" type="button" class="btn">How do filters combine?</button>
                      <p>All filters must match. Leave a filter empty to ignore it.</p>
                    </mj-popover>
                  </div>
                  <div slot="footer" class="actions">
                    <button type="button" class="btn" id="filter-reset">Reset</button>
                    <button type="button" class="btn primary" id="filter-apply">Apply</button>
                  </div>
                </mj-drawer>
            """),
            css=_BUTTON_CSS + _FIELD_CSS + _src("""
                .filter-form { display: grid; gap: var(--mj-space-3); justify-items: start; }
            """),
            script=_src("""
                const drawer = document.getElementById("filter-drawer")
                const status = document.getElementById("filter-status")
                const from = document.getElementById("filter-from")
                document.getElementById("open-filters").addEventListener("click", () => drawer.show())
                document.getElementById("filter-reset").addEventListener("click", () => {
                  status.value = ""
                  from.value = ""
                })
                document.getElementById("filter-apply").addEventListener("click", () => {
                  mjSandbox.log("filters", { status: status.value, placedAfter: from.value })
                  drawer.close()
                })
                drawer.show()
            """),
            height=480,
        ),
    ],
    slots=[
        ("", "Panel body (scrolls).", "<p>Body text added by the slot inspector.</p>"),
        ("title", "Heading in the header; names the panel unless `label` is set.", "<span>Sample title</span>"),
        ("header", "Replaces the whole header, including the title and the close button.",
         "<div><strong>Custom header</strong></div>"),
        ("footer", "Pinned action row at the bottom of the panel; hidden while empty.",
         '<div class="actions"><button type="button" class="btn">Cancel</button><button type="button" class="btn primary">Apply</button></div>'),
        ("drag-handle", "Replaces the drag handle bar of the bottom sheet (edge bottom only).",
         '<span class="muted">drag to close</span>'),
    ],
    properties=[
        ("open", "boolean. Reflects the `open` attribute; setting it opens or closes."),
        ("panelEl", "HTMLElement (read-only). The sliding panel in the shadow root."),
        ("dragProgress", "number (read-only). 0-1 progress of an active drag on the bottom sheet's handle; 0 when not dragging."),
        ("returnFocusEl", "Element | null. Where focus goes after closing; filled on open when still null."),
    ],
    methods=[
        ("show()", "Opens the drawer (sets `open`)."),
        ("close()", "Closes the drawer with reason `api` (a before-close listener may veto it)."),
    ],
    parts=[
        ("panel", "The sliding panel."),
        ("drag-handle", "Drag handle row (bottom edge only)."),
        ("header", "Header row."),
        ("title", "Wrapper of the title slot."),
        ("close-button", "The built-in close button."),
        ("body", "Scrolling content area."),
        ("footer", "Footer row."),
    ],
    css_properties=[
        ("--mj-drawer-size", "Panel width (start / end) or height (top / bottom); wins over the `size` attribute (default 20rem, at most 90vw / 90dvh)."),
        ("--mj-drawer-padding", "Inline padding of header and footer and padding of the body (default var(--mj-space-5))."),
        ("--mj-drawer-radius", "Radius of the two inner corners (default var(--mj-radius-lg))."),
        ("--mj-drawer-shadow", "Panel shadow (default var(--mj-elevation-3))."),
    ],
)


# ---------------------------------------------------------------------------
# mj-lightbox
# ---------------------------------------------------------------------------

_THUMB_CSS = _src("""
    .thumbs {
      display: flex;
      flex-wrap: wrap;
      gap: var(--mj-space-3);
      padding: var(--mj-space-4);
    }
    .thumb {
      padding: 0;
      border: 1px solid var(--mj-border);
      border-radius: var(--mj-radius-md);
      background: var(--mj-bg-muted);
      cursor: zoom-in;
      overflow: hidden;
      inline-size: 9rem;
      aspect-ratio: 3 / 2;
    }
    .thumb img { display: block; inline-size: 100%; block-size: 100%; object-fit: cover; }
    .thumb:focus-visible {
      outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
      outline-offset: var(--mj-focus-ring-offset);
    }
""")

_LIGHTBOX = ComponentDoc(
    tag="mj-lightbox",
    title="Lightbox",
    group="overlays",
    summary="Full-screen modal viewer for images and videos with navigation, zoom and pan.",
    description=(
        "<p><code>&lt;mj-lightbox&gt;</code> shows one item of its "
        "<code>items</code> list in a full-viewport modal surface: focus is "
        "trapped, the page behind is inert and scroll-locked, and the viewer sits "
        "in the top layer. The toolbar has a counter, zoom out / in and close; "
        "previous / next buttons sit beside the media and the caption bar below "
        "it (with <code>show-caption</code>).</p>"
        "<p>Keyboard: <kbd>←</kbd> / <kbd>→</kbd> (swapped in RTL) and "
        "<kbd>↑</kbd> / <kbd>↓</kbd> navigate, <kbd>Home</kbd> / <kbd>End</kbd> "
        "jump to the first / last item, <kbd>+</kbd> / <kbd>-</kbd> zoom, "
        "<kbd>0</kbd> resets the zoom, and while zoomed the arrows pan. "
        "Double-click an image to toggle 2&times; zoom and drag it to pan; on touch "
        "a horizontal swipe navigates. Clicking the dark area around the media "
        "closes the viewer. Items with <code>type: \"video\"</code> (or all items "
        "with <code>variant=\"video\"</code>) are played in a "
        "<code>&lt;video controls&gt;</code>; zoom is off for videos. A source "
        "that fails to load shows a status message. Item sources go through "
        "<code>safeUrl</code>: http(s), relative URLs and "
        "<code>data:image/png|jpeg|gif|webp|avif|bmp</code> are accepted.</p>"
    ),
    how_to_use=(
        "<p>Assign <code>items</code> (<code>[{ src, alt, caption, type }]</code>) "
        "in script &mdash; the property also keeps a value assigned before the "
        "element upgraded &mdash; then call <code>show(index)</code> from your "
        "thumbnails. Setting <code>open</code> opens the viewer only once there are "
        "items (assigning items to an element that has <code>open</code> opens "
        "it). Put the thumbnails in the default slot; they stay in the page flow. "
        "<code>loop</code> (default on) wraps around; <code>current-index</code> "
        "reflects and sets the shown item.</p>"
    ),
    example="",
    attributes=[
        AttributeDoc(name="open", kind="boolean",
                     description="Present while open. Adding it opens the viewer when `items` is not empty; removing it closes (reason `api`)."),
        AttributeDoc(name="current-index", kind="number", default="0",
                     description="Zero-based index of the shown item (clamped to the list); updated on navigation."),
        AttributeDoc(name="loop", kind="boolean", default="true",
                     description="`false` stops at the first and last item (the previous / next buttons are disabled there)."),
        AttributeDoc(name="variant", kind="enum", values=["image", "video"], default="image",
                     description="Default media type for items without a `type` field."),
        AttributeDoc(name="show-caption", kind="boolean",
                     description="Shows the caption bar with the item's `caption`."),
        AttributeDoc(name="show-counter", kind="boolean", default="true",
                     description="`false` hides the \"1 of 6\" counter in the toolbar."),
        AttributeDoc(name="counter-format", kind="string", values=["{current} / {total}", "Photo {current} of {total}"],
                     description="Counter template with {current} and {total} (default \"{current} of {total}\")."),
        AttributeDoc(name="zoom-enabled", kind="boolean", default="true",
                     description="`false` hides the zoom buttons and disables zoom keys, double-click and pan."),
        AttributeDoc(name="max-zoom", kind="number", default="4",
                     description="Largest zoom factor (at least 1); zoom steps are 0.5."),
        AttributeDoc(name="label", kind="string", default="Media viewer",
                     description="Accessible name of the viewer."),
        AttributeDoc(name="close-label", kind="string", default="Close", description="Accessible label of the close button."),
        AttributeDoc(name="prev-label", kind="string", default="Previous", description="Accessible label of the previous button."),
        AttributeDoc(name="next-label", kind="string", default="Next", description="Accessible label of the next button."),
        AttributeDoc(name="zoom-in-label", kind="string", default="Zoom in", description="Accessible label of the zoom-in button."),
        AttributeDoc(name="zoom-out-label", kind="string", default="Zoom out", description="Accessible label of the zoom-out button."),
    ],
    events=[
        ("mj-lightbox-open", "The viewer opened.", "{ index: number, item: object }"),
        ("mj-lightbox-change", "Another item is shown (buttons, keys, swipe).",
         "{ index: number, previousIndex: number, item: object }"),
        ("mj-lightbox-zoom", "The zoom level changed.", "{ level: number }"),
        ("mj-lightbox-close", "The viewer closed, once per close.",
         "{ reason: 'close-button' | 'escape' | 'backdrop' | 'api' }"),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>Two photos with captions, open on load. Close it (Escape, "
                "&times; or a click on the dark area) and reopen it from a "
                "thumbnail &mdash; the thumbnails live in the default slot and call "
                "<code>show(index)</code>. The photos are drawn on a canvas, so no "
                "network is needed.</p>"
            ),
            html=_src("""
                <mj-lightbox id="demo-lightbox" open show-caption>
                  <div class="thumbs">
                    <button type="button" class="thumb" data-index="0"><img alt="Fishing boats in a calm harbour at sunrise"></button>
                    <button type="button" class="thumb" data-index="1"><img alt="Pine forest on a misty hillside"></button>
                  </div>
                </mj-lightbox>
            """),
            css=_THUMB_CSS,
            script=_PHOTO_JS + _src("""

                const lightbox = document.getElementById("demo-lightbox")
                const items = [
                  { src: photo("Harbour at dawn", "#f6b26b", "#3d6f9e"),
                    alt: "Fishing boats in a calm harbour at sunrise", caption: "Harbour at dawn, Porto" },
                  { src: photo("Pine forest", "#cfe2d4", "#274e13"),
                    alt: "Pine forest on a misty hillside", caption: "Pine forest, Black Forest" }
                ]
                lightbox.items = items
                for (const thumb of lightbox.querySelectorAll(".thumb")) {
                  const index = Number(thumb.dataset.index)
                  thumb.querySelector("img").src = items[index].src
                  thumb.addEventListener("click", () => lightbox.show(index))
                }
            """),
            height=480,
        ),
        ComponentExample(
            key="gallery",
            title="Gallery, no looping",
            description=(
                "<p>Six photos with <code>loop=\"false\"</code> (previous is disabled "
                "on the first photo, next on the last) and "
                "<code>counter-format=\"Photo {current} of {total}\"</code>. Use the "
                "arrow keys, <kbd>Home</kbd> and <kbd>End</kbd>; every move logs "
                "<code>mj-lightbox-change</code>.</p>"
            ),
            html=_src("""
                <mj-lightbox id="gallery-lightbox" loop="false" show-caption counter-format="Photo {current} of {total}" label="Trip photos">
                  <div class="thumbs">
                    <button type="button" class="thumb" data-index="0"><img alt="Harbour at dawn"></button>
                    <button type="button" class="thumb" data-index="1"><img alt="Pine forest"></button>
                    <button type="button" class="thumb" data-index="2"><img alt="Desert dunes"></button>
                    <button type="button" class="thumb" data-index="3"><img alt="Glacier lake"></button>
                    <button type="button" class="thumb" data-index="4"><img alt="Lavender field"></button>
                    <button type="button" class="thumb" data-index="5"><img alt="City at night"></button>
                  </div>
                </mj-lightbox>
            """),
            css=_THUMB_CSS,
            script=_PHOTO_JS + _src("""

                const lightbox = document.getElementById("gallery-lightbox")
                const items = [
                  { src: photo("Harbour at dawn", "#f6b26b", "#3d6f9e"), alt: "Harbour at dawn", caption: "Day 1 · Porto" },
                  { src: photo("Pine forest", "#cfe2d4", "#274e13"), alt: "Pine forest", caption: "Day 2 · Black Forest" },
                  { src: photo("Desert dunes", "#ffe599", "#b45f06"), alt: "Desert dunes", caption: "Day 4 · Merzouga" },
                  { src: photo("Glacier lake", "#d0e0e3", "#134f5c"), alt: "Glacier lake", caption: "Day 6 · Lake Louise" },
                  { src: photo("Lavender field", "#d9d2e9", "#674ea7"), alt: "Lavender field", caption: "Day 8 · Valensole" },
                  { src: photo("City at night", "#20124d", "#000000"), alt: "City at night", caption: "Day 9 · Tokyo" }
                ]
                lightbox.items = items
                for (const thumb of lightbox.querySelectorAll(".thumb")) {
                  const index = Number(thumb.dataset.index)
                  thumb.querySelector("img").src = items[index].src
                  thumb.addEventListener("click", () => lightbox.show(index))
                }
            """),
            height=480,
        ),
        ComponentExample(
            key="zoom",
            title="Zoom and pan",
            description=(
                "<p><code>max-zoom=\"3\"</code>: use the toolbar buttons, "
                "<kbd>+</kbd> / <kbd>-</kbd> / <kbd>0</kbd>, or double-click the "
                "image; drag or use the arrow keys to pan while zoomed. Each change "
                "logs <code>mj-lightbox-zoom</code>. Untick "
                "<code>zoom-enabled</code> in the controls to remove zooming.</p>"
            ),
            html=_src("""
                <mj-lightbox id="zoom-lightbox" max-zoom="3" show-caption>
                  <div class="thumbs">
                    <button type="button" class="thumb" data-index="0"><img alt="Site plan of the new library"></button>
                  </div>
                </mj-lightbox>
            """),
            css=_THUMB_CSS,
            script=_src("""
                // A detailed drawing, so zooming has something to show.
                function plan() {
                  const canvas = document.createElement("canvas")
                  canvas.width = 1200
                  canvas.height = 800
                  const ctx = canvas.getContext("2d")
                  ctx.fillStyle = "#f3f6fa"
                  ctx.fillRect(0, 0, 1200, 800)
                  ctx.strokeStyle = "#9fb3c8"
                  for (let x = 0; x <= 1200; x = x + 40) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, 800); ctx.stroke() }
                  for (let y = 0; y <= 800; y = y + 40) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(1200, y); ctx.stroke() }
                  ctx.fillStyle = "#3d6f9e"
                  ctx.fillRect(240, 200, 480, 320)
                  ctx.fillStyle = "#93c47d"
                  ctx.fillRect(760, 200, 200, 120)
                  ctx.fillStyle = "#ffffff"
                  ctx.font = "600 36px system-ui, sans-serif"
                  ctx.fillText("Reading room", 300, 370)
                  ctx.font = "14px system-ui, sans-serif"
                  ctx.fillText("Garden", 830, 265)
                  ctx.fillStyle = "#1c2733"
                  ctx.font = "12px system-ui, sans-serif"
                  ctx.fillText("Scale 1:200 - north is up - drawing 4 of 12", 24, 780)
                  return canvas.toDataURL("image/png")
                }

                const lightbox = document.getElementById("zoom-lightbox")
                const items = [{ src: plan(), alt: "Site plan of the new library", caption: "Site plan, ground floor" }]
                lightbox.items = items
                const thumb = lightbox.querySelector(".thumb")
                thumb.querySelector("img").src = items[0].src
                thumb.addEventListener("click", () => lightbox.show(0))
                lightbox.show(0)
            """),
            height=480,
        ),
        ComponentExample(
            key="states",
            title="Load error and single item",
            description=(
                "<p>A source that cannot be decoded shows the status message "
                "<em>This item could not be loaded.</em> With a single item the "
                "previous / next buttons are disabled. <code>show-counter=\"false\"</code> "
                "hides the counter.</p>"
            ),
            html=_src("""
                <div class="row demo-pad">
                  <button type="button" class="btn" id="open-broken">Open broken item</button>
                  <button type="button" class="btn" id="open-single">Open single item</button>
                </div>
                <mj-lightbox id="states-lightbox" show-caption show-counter="false"></mj-lightbox>
            """),
            css=_BUTTON_CSS + _src("""
                .demo-pad { padding: var(--mj-space-4); }
            """),
            script=_PHOTO_JS + _src("""

                const lightbox = document.getElementById("states-lightbox")
                const broken = [{ src: "data:image/png;base64,AAAA", alt: "Corrupt upload", caption: "upload-0042.png (corrupt)" }]
                const single = [{ src: photo("Lavender field", "#d9d2e9", "#674ea7"), alt: "Lavender field", caption: "The only photo in this album" }]
                document.getElementById("open-broken").addEventListener("click", () => {
                  lightbox.items = broken
                  lightbox.show(0)
                })
                document.getElementById("open-single").addEventListener("click", () => {
                  lightbox.items = single
                  lightbox.show(0)
                })
            """),
            height=480,
        ),
        ComponentExample(
            key="slots",
            title="Toolbar actions and icons",
            description=(
                "<p>The <code>toolbar-actions</code> slot adds a Download button that "
                "reads <code>currentItem</code>; <code>prev-icon</code> / "
                "<code>next-icon</code> replace the arrows; "
                "<code>--mj-lightbox-bg</code> tints the backdrop.</p>"
            ),
            html=_src("""
                <mj-lightbox id="slots-lightbox" show-caption>
                  <div class="thumbs">
                    <button type="button" class="thumb" data-index="0"><img alt="Glacier lake"></button>
                    <button type="button" class="thumb" data-index="1"><img alt="Desert dunes"></button>
                    <button type="button" class="thumb" data-index="2"><img alt="City at night"></button>
                  </div>
                  <button slot="toolbar-actions" type="button" class="toolbar-btn" id="download-photo">Download</button>
                  <svg slot="prev-icon" viewBox="0 0 24 24" width="28" height="28" aria-hidden="true"><path d="M15 5l-7 7 7 7" fill="none" stroke="currentColor" stroke-width="2.5"/></svg>
                  <svg slot="next-icon" viewBox="0 0 24 24" width="28" height="28" aria-hidden="true"><path d="M9 5l7 7-7 7" fill="none" stroke="currentColor" stroke-width="2.5"/></svg>
                </mj-lightbox>
            """),
            css=_THUMB_CSS + _src("""
                #slots-lightbox { --mj-lightbox-bg: rgba(19, 41, 61, 0.96); }
                .toolbar-btn {
                  font: inherit;
                  padding-block: var(--mj-space-1);
                  padding-inline: var(--mj-space-3);
                  border: 1px solid rgba(255, 255, 255, 0.5);
                  border-radius: var(--mj-radius-md);
                  background: transparent;
                  color: #ffffff;
                  cursor: pointer;
                }
            """),
            script=_PHOTO_JS + _src("""

                const lightbox = document.getElementById("slots-lightbox")
                const items = [
                  { src: photo("Glacier lake", "#d0e0e3", "#134f5c"), alt: "Glacier lake", caption: "Lake Louise" },
                  { src: photo("Desert dunes", "#ffe599", "#b45f06"), alt: "Desert dunes", caption: "Merzouga" },
                  { src: photo("City at night", "#20124d", "#000000"), alt: "City at night", caption: "Tokyo" }
                ]
                lightbox.items = items
                for (const thumb of lightbox.querySelectorAll(".thumb")) {
                  const index = Number(thumb.dataset.index)
                  thumb.querySelector("img").src = items[index].src
                  thumb.addEventListener("click", () => lightbox.show(index))
                }
                document.getElementById("download-photo").addEventListener("click", () => {
                  mjSandbox.log("download", { caption: lightbox.currentItem.caption })
                })
                lightbox.show(0)
            """),
            height=480,
        ),
    ],
    slots=[
        ("", "In-page content such as the thumbnails that open the viewer; it stays in the page flow.",
         '<div class="thumbs"><button type="button" class="thumb">Thumbnail</button></div>'),
        ("toolbar-actions", "Extra toolbar controls, placed before the zoom buttons.",
         '<button type="button">Share</button>'),
        ("prev-icon", "Content of the previous button (default ‹).", "<span>◀</span>"),
        ("next-icon", "Content of the next button (default ›).", "<span>▶</span>"),
        ("caption", "Replaces the caption text of every item with fixed content (needs show-caption).",
         "<span>All photos © 2026 Example Studio</span>"),
    ],
    properties=[
        ("items", "Array<{ src: string, alt?: string, caption?: string, type?: 'image' | 'video' }>. The media list; a copy is kept. Assigning while open re-renders; assigning [] closes."),
        ("open", "boolean. Reflects the `open` attribute."),
        ("currentItem", "object | null (read-only). The item at `current-index`."),
        ("zoomLevel", "number (read-only). Current zoom factor (1 = fit)."),
        ("isPanning", "boolean (read-only). True while a zoomed image is being dragged."),
    ],
    methods=[
        ("show(index?)", "Opens the viewer, optionally at `index`; warns and does nothing while `items` is empty."),
        ("close()", "Closes the viewer (reason `api`)."),
    ],
    parts=[
        ("dialog", "The full-viewport modal surface (role dialog)."),
        ("toolbar", "Top bar."),
        ("counter", "The \"1 of 6\" counter."),
        ("zoom-out", "Zoom-out button."),
        ("zoom-in", "Zoom-in button."),
        ("close-button", "Close button."),
        ("viewport", "Area around the media; a click on it closes the viewer."),
        ("prev-button", "Previous button."),
        ("next-button", "Next button."),
        ("zoom-container", "Wrapper that is scaled and translated when zoomed."),
        ("media", "The <img> or <video> element."),
        ("status", "Loading / error message."),
        ("caption-bar", "Caption bar below the media."),
    ],
    css_properties=[
        ("--mj-lightbox-bg", "Backdrop colour (default rgba(14, 18, 27, 0.95)). The viewer stays dark in both themes; these properties retheme it."),
        ("--mj-lightbox-color", "Text colour on the backdrop, including the caption (default rgba(255, 255, 255, 0.9))."),
        ("--mj-lightbox-muted-color", "Counter and loading / error text colour (default rgba(255, 255, 255, 0.8))."),
        ("--mj-lightbox-toolbar-bg", "Toolbar background (default rgba(0, 0, 0, 0.4))."),
        ("--mj-lightbox-caption-bg", "Caption bar background (default rgba(0, 0, 0, 0.5))."),
        ("--mj-lightbox-control-color", "Icon colour of the toolbar and previous / next buttons (default #fff)."),
        ("--mj-lightbox-control-bg", "Toolbar button background (default rgba(255, 255, 255, 0.1))."),
        ("--mj-lightbox-control-bg-hover", "Toolbar button background on hover (default rgba(255, 255, 255, 0.25))."),
        ("--mj-lightbox-nav-bg", "Previous / next button background (default rgba(0, 0, 0, 0.5))."),
        ("--mj-lightbox-nav-bg-hover", "Previous / next button background on hover (default rgba(0, 0, 0, 0.75))."),
    ],
)


# ---------------------------------------------------------------------------
# mj-overlay
# ---------------------------------------------------------------------------

_OVERLAY_PAGE_CSS = _src("""
    .page {
      display: grid;
      gap: var(--mj-space-3);
      padding: var(--mj-space-4);
      max-inline-size: 30rem;
    }
    .page h3 { margin: 0; }
""")

_OVERLAY = ComponentDoc(
    tag="mj-overlay",
    title="Overlay",
    group="overlays",
    summary="Backdrop primitive: dims or blocks the page, makes it inert and locks scrolling.",
    description=(
        "<p><code>&lt;mj-overlay&gt;</code> is the backdrop used by the modal "
        "components (drawer, lightbox, command palette, tour; the dialog uses it "
        "only for the scroll lock and paints the native <code>::backdrop</code>). "
        "While <code>visible</code> it paints a fixed full-viewport scrim, takes a "
        "reference-counted scroll lock on the document (the page's own "
        "<code>overflow</code> is restored when the last lock goes) and marks the "
        "background <code>inert</code>, also reference-counted so stacked overlays "
        "release it only when the last one goes.</p>"
        "<p>What becomes inert: the elements matching <code>inert-target</code>; "
        "nothing when it is <code>none</code>; otherwise every sibling along the "
        "path from the <code>surface</code> (the panel a composer shows above the "
        "backdrop) up to <code>&lt;body&gt;</code>; and without a surface every "
        "sibling of the overlay itself. Variants: <code>dim</code> paints the scrim; "
        "<code>block</code> is invisible but swallows pointer events; "
        "<code>transparent</code> is invisible and lets pointer events through. "
        "<code>mj-overlay-visible</code> / <code>mj-overlay-hidden</code> fire when "
        "the fade has finished.</p>"
    ),
    how_to_use=(
        "<p>Application code rarely needs it directly; it is the building block "
        "for a custom modal. Set <code>visible</code> (or call <code>show()</code> "
        "/ <code>hide()</code>), give your panel a higher <code>z-index</code> than "
        "the backdrop (or assign it to <code>surface</code> and add "
        "<code>top-layer</code>, which shows both in the top layer), point "
        "<code>inert-target</code> at the content behind it and implement light "
        "dismiss by listening for <code>mj-overlay-click</code>. "
        "<code>retire()</code> releases inert and scroll lock at once and removes "
        "the element after its fade.</p>"
    ),
    example="",
    attributes=[
        AttributeDoc(name="visible", kind="boolean",
                     description="Shows the backdrop and applies scroll lock and inert; removing it releases both."),
        AttributeDoc(name="variant", kind="enum", values=["dim", "block", "transparent"], default="dim",
                     description="`dim` paints the scrim; `block` is invisible but swallows pointer events; `transparent` is invisible and lets pointer events through."),
        AttributeDoc(name="scroll-lock", kind="boolean", default="true",
                     description="`false` leaves the page scrollable while visible."),
        AttributeDoc(name="inert-target", kind="string", values=["none", "#app", "main"],
                     description="CSS selector of the elements to make inert, or `none`. Default: the siblings along the surface's path to <body>, or the overlay's own siblings."),
        AttributeDoc(name="top-layer", kind="boolean",
                     description="Shows the backdrop and the `surface` element in the top layer (above every z-index) while visible."),
        AttributeDoc(name="z-index", kind="number",
                     description="Explicit z-index of the backdrop (default var(--mj-layer-overlay))."),
        AttributeDoc(name="animation", kind="boolean", default="true",
                     description="`false` removes the fade, so the visible / hidden events fire immediately."),
    ],
    events=[
        ("mj-overlay-click", "The backdrop was clicked (not for variant transparent). Cancelable: composers such as the drawer treat a cancelled click as a veto of their dismissal.",
         "{ target: Element }"),
        ("mj-overlay-visible", "The overlay became visible and its fade-in has ended.", "{}"),
        ("mj-overlay-hidden", "The overlay was hidden and its fade-out has ended.", "{}"),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>A visible dim overlay over some page content, which is inert "
                "meanwhile. Click the backdrop: the script hides the overlay on "
                "<code>mj-overlay-click</code>. <strong>Show overlay</strong> brings "
                "it back.</p>"
            ),
            html=_src("""
                <section class="page">
                  <h3>Quarterly report</h3>
                  <p>Revenue grew 12% on the previous quarter, driven by the new team plans.</p>
                  <div class="row">
                    <button type="button" class="btn primary" id="show-overlay">Show overlay</button>
                  </div>
                </section>
                <mj-overlay id="demo-overlay" visible></mj-overlay>
            """),
            css=_BUTTON_CSS + _OVERLAY_PAGE_CSS,
            script=_src("""
                const overlay = document.getElementById("demo-overlay")
                document.getElementById("show-overlay").addEventListener("click", () => overlay.show())
                overlay.addEventListener("mj-overlay-click", () => overlay.hide())
            """),
            height=260,
        ),
        ComponentExample(
            key="variants",
            title="Variants",
            description=(
                "<p>With <code>inert-target=\"none\"</code> the page stays "
                "interactive, so the pointer behaviour of each variant shows: "
                "<code>dim</code> and <code>block</code> catch the click (and hide "
                "on <code>mj-overlay-click</code>), <code>transparent</code> lets it "
                "through to the page &mdash; use <strong>Hide</strong> then. The "
                "counter counts clicks that reached the page.</p>"
            ),
            html=_src("""
                <section class="page">
                  <div class="row">
                    <button type="button" class="btn" data-variant="dim">dim</button>
                    <button type="button" class="btn" data-variant="block">block</button>
                    <button type="button" class="btn" data-variant="transparent">transparent</button>
                    <button type="button" class="btn" id="hide-overlay">Hide</button>
                  </div>
                  <button type="button" class="btn" id="page-target">Page button: 0 clicks</button>
                </section>
                <mj-overlay id="variant-overlay" inert-target="none"></mj-overlay>
            """),
            css=_BUTTON_CSS + _OVERLAY_PAGE_CSS,
            script=_src("""
                const overlay = document.getElementById("variant-overlay")
                const target = document.getElementById("page-target")
                let clicks = 0
                for (const button of document.querySelectorAll("[data-variant]")) {
                  button.addEventListener("click", () => {
                    overlay.setAttribute("variant", button.dataset.variant)
                    overlay.show()
                  })
                }
                document.getElementById("hide-overlay").addEventListener("click", () => overlay.hide())
                overlay.addEventListener("mj-overlay-click", () => overlay.hide())
                target.addEventListener("click", () => {
                  clicks = clicks + 1
                  target.textContent = "Page button: " + clicks + " clicks"
                })
            """),
            height=260,
        ),
        ComponentExample(
            key="custom-modal",
            title="Building a custom modal",
            description=(
                "<p>A hand-made modal: the overlay makes only <code>#app</code> "
                "inert (<code>inert-target=\"#app\"</code>), the panel sits above the "
                "backdrop by z-index, and the script closes on a backdrop click or "
                "Escape. <code>--mj-overlay-color</code> tints the scrim.</p>"
            ),
            html=_src("""
                <div id="app" class="page">
                  <h3>Invoices</h3>
                  <p>3 invoices are overdue.</p>
                  <div class="row"><button type="button" class="btn primary" id="open-custom">Send reminders…</button></div>
                </div>

                <mj-overlay id="custom-overlay" inert-target="#app"></mj-overlay>
                <div id="custom-panel" class="custom-panel" role="dialog" aria-modal="true" aria-labelledby="custom-title" hidden>
                  <h3 id="custom-title">Send 3 reminders?</h3>
                  <p>Each customer receives an email with a payment link.</p>
                  <div class="actions">
                    <button type="button" class="btn" id="custom-cancel">Cancel</button>
                    <button type="button" class="btn primary" id="custom-send">Send</button>
                  </div>
                </div>
            """),
            css=_BUTTON_CSS + _FIELD_CSS + _OVERLAY_PAGE_CSS + _src("""
                #custom-overlay { --mj-overlay-color: rgba(19, 41, 61, 0.6); }
                .custom-panel {
                  position: fixed;
                  inset-block-start: 50%;
                  inset-inline-start: 50%;
                  translate: -50% -50%;
                  z-index: var(--mj-layer-modal);
                  inline-size: min(22rem, calc(100vw - 2rem));
                  padding: var(--mj-space-5);
                  border: 1px solid var(--mj-border);
                  border-radius: var(--mj-radius-lg);
                  background: var(--mj-surface);
                  color: var(--mj-text);
                  box-shadow: var(--mj-elevation-3);
                }
                .custom-panel h3 { margin-block-start: 0; }
            """),
            script=_src("""
                const overlay = document.getElementById("custom-overlay")
                const panel = document.getElementById("custom-panel")
                const opener = document.getElementById("open-custom")
                function openPanel() {
                  overlay.show()
                  panel.hidden = false
                  document.getElementById("custom-send").focus()
                }
                function closePanel(reason) {
                  overlay.hide()
                  panel.hidden = true
                  opener.focus()
                  mjSandbox.log("custom modal closed", { reason: reason })
                }
                opener.addEventListener("click", openPanel)
                overlay.addEventListener("mj-overlay-click", () => closePanel("backdrop"))
                document.getElementById("custom-cancel").addEventListener("click", () => closePanel("cancel"))
                document.getElementById("custom-send").addEventListener("click", () => closePanel("send"))
                panel.addEventListener("keydown", (event) => {
                  if (event.key === "Escape") { closePanel("escape") }
                })
            """),
            height=300,
        ),
        ComponentExample(
            key="events",
            title="Scroll lock, inert and events",
            description=(
                "<p>Toggle <code>scroll-lock</code> and <code>animation</code> with "
                "the checkboxes, then show the overlay for 1.5 s. The log shows "
                "<code>mj-overlay-visible</code> / <code>mj-overlay-hidden</code> "
                "after each fade (immediately with animation off) and a snapshot of "
                "<code>lockCount</code>, <code>inertEls</code> and the document "
                "overflow while it is up.</p>"
            ),
            html=_src("""
                <section class="page" id="events-page">
                  <label><input type="checkbox" id="opt-scroll" checked> scroll-lock</label>
                  <label><input type="checkbox" id="opt-animation" checked> animation</label>
                  <div class="row"><button type="button" class="btn primary" id="flash-overlay">Show for 1.5 s</button></div>
                </section>
                <mj-overlay id="events-overlay" variant="block" inert-target="#events-page"></mj-overlay>
            """),
            css=_BUTTON_CSS + _OVERLAY_PAGE_CSS,
            script=_src("""
                const overlay = document.getElementById("events-overlay")
                document.getElementById("flash-overlay").addEventListener("click", () => {
                  overlay.setAttribute("scroll-lock", document.getElementById("opt-scroll").checked ? "true" : "false")
                  overlay.setAttribute("animation", document.getElementById("opt-animation").checked ? "true" : "false")
                  overlay.show()
                  mjSandbox.log("while visible", {
                    lockCount: overlay.lockCount,
                    inertEls: overlay.inertEls.map((element) => element.id || element.localName),
                    documentOverflow: document.documentElement.style.overflow || "(page default)"
                  })
                  window.setTimeout(() => overlay.hide(), 1500)
                })
            """),
            height=240,
        ),
    ],
    slots=[],
    properties=[
        ("visible", "boolean. Reflects the `visible` attribute."),
        ("surface", "Element | null. The panel a composer shows above the backdrop: it is exempt from inert and joins the top layer with `top-layer`."),
        ("lockCount", "number (read-only). How many visible overlays hold the shared scroll lock."),
        ("inertEls", "Element[] (read-only). The elements this overlay made inert."),
    ],
    methods=[
        ("show()", "Sets `visible`."),
        ("hide()", "Removes `visible`."),
        ("retire()", "Removes `visible` (releasing inert and the scroll lock at once) and removes the element when the fade has ended."),
    ],
    parts=[
        ("backdrop", "The fixed full-viewport scrim."),
    ],
    css_properties=[
        ("--mj-overlay-color", "Scrim colour of variant dim (default var(--mj-overlay-scrim))."),
        ("--mj-overlay-duration", "Fade duration (default var(--mj-motion-medium)); the visible / hidden events wait for it."),
        ("--mj-overlay-z-index", "Backdrop z-index when the `z-index` attribute is not set (default var(--mj-layer-overlay))."),
    ],
)


# ---------------------------------------------------------------------------
# mj-toast-region
# ---------------------------------------------------------------------------

_TOAST_PLACEMENTS = ["bottom-end", "bottom-start", "bottom-center", "top-end", "top-start", "top-center"]

_TOAST_REGION = ComponentDoc(
    tag="mj-toast-region",
    title="Toast Region",
    group="overlays",
    summary="Fixed-position region that shows, queues and auto-dismisses toast notifications.",
    description=(
        "<p><code>&lt;mj-toast-region&gt;</code> manages transient notifications. "
        "<code>add()</code> shows a toast at once while fewer than "
        "<code>max-visible</code> are on screen and queues it otherwise; queued "
        "toasts move up as visible ones leave. Each toast auto-dismisses after its "
        "<code>duration</code> (default 5000 ms, 8000 ms for errors; 0 keeps it "
        "until dismissed); the timers pause while the pointer is over the region "
        "or focus is inside it. <kbd>Escape</kbd> dismisses the focused toast.</p>"
        "<p>Messages and titles are set as text (never parsed as HTML). Each toast "
        "is announced through the shared live region &mdash; politely, or "
        "assertively for warnings and errors unless <code>polite</code> is set. "
        "The region shows in the top layer while it has toasts, and when a modal "
        "(dialog, drawer, ...) is open it moves into that modal surface, so its "
        "toasts stay visible and clickable above the modal. Nothing enforces a "
        "single region per page; one per page is the intended use.</p>"
    ),
    how_to_use=(
        "<p>Place one region near the end of <code>&lt;body&gt;</code> and call "
        "<code>add({ message, title, severity, duration, actions })</code> on it "
        "from script; it returns the toast id. <code>severity</code> is "
        "<code>info</code> (default), <code>success</code>, <code>warning</code> or "
        "<code>error</code>; <code>actions</code> is a list of "
        "<code>{ label, onClick, dismiss }</code> buttons (<code>dismiss: false</code> "
        "keeps the toast). <code>update(id, changes)</code> changes a toast in "
        "place (a new <code>duration</code> restarts its timer), "
        "<code>dismiss(id)</code> removes one and <code>dismissAll()</code> removes "
        "the visible and the queued ones. Code that cannot reach the region can "
        "dispatch a bubbling <code>mj-toast-request</code> event with the "
        "descriptor as detail on the region or on an element inside it.</p>"
    ),
    example="",
    attributes=[
        AttributeDoc(name="placement", kind="enum", values=_TOAST_PLACEMENTS, default="bottom-end",
                     description="Corner or edge of the viewport the toasts stack in (start / end follow the writing direction)."),
        AttributeDoc(name="max-visible", kind="number", default="3",
                     description="Toasts shown at once; further toasts wait in the queue."),
        AttributeDoc(name="region-label", kind="string", default="Notifications",
                     description="Accessible name of the region."),
        AttributeDoc(name="dismiss-label", kind="string", default="Dismiss notification",
                     description="Accessible label of each toast's close button."),
        AttributeDoc(name="polite", kind="boolean",
                     description="Announce warnings and errors politely as well (default: assertively)."),
        AttributeDoc(name="gap", kind="string", values=["0.5rem", "1rem"],
                     description="Space between toasts as a CSS length (default var(--mj-space-3))."),
        AttributeDoc(name="offset-x", kind="string", values=["0.5rem", "2rem"],
                     description="Distance from the inline edge of the viewport (default var(--mj-space-4))."),
        AttributeDoc(name="offset-y", kind="string", values=["0.5rem", "2rem"],
                     description="Distance from the top or bottom edge of the viewport (default var(--mj-space-4))."),
    ],
    events=[
        ("mj-toast-add", "add() accepted a toast (shown or queued).", "{ id: string, descriptor: object }"),
        ("mj-toast-show", "A toast became visible.", "{ id: string }"),
        ("mj-toast-action", "An action button of a toast was clicked.", "{ id: string, action: object }"),
        ("mj-toast-dismiss", "A toast was removed (visible or queued).",
         "{ id: string, reason: 'auto' | 'user' | 'api' }"),
        ("mj-toast-queue-empty", "The last visible or queued toast was removed.", "{}"),
        ("mj-toast-request", "Listened for, not emitted: dispatch it (bubbling) on the region or inside it with a descriptor as detail to add a toast.",
         "descriptor"),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>One button per severity. Toasts stack bottom-end, at most three "
                "at a time, and leave after 5 s (errors after 8 s); hover the region "
                "to pause the timers, focus a toast and press <kbd>Escape</kbd> to "
                "dismiss it.</p>"
            ),
            html=_src("""
                <div class="row demo-pad">
                  <button type="button" class="btn" data-severity="info">Info</button>
                  <button type="button" class="btn" data-severity="success">Success</button>
                  <button type="button" class="btn" data-severity="warning">Warning</button>
                  <button type="button" class="btn" data-severity="error">Error</button>
                </div>
                <mj-toast-region id="demo-toasts"></mj-toast-region>
            """),
            css=_BUTTON_CSS + _src("""
                .demo-pad { padding: var(--mj-space-4); }
            """),
            script=_src("""
                const region = document.getElementById("demo-toasts")
                const samples = {
                  info: { title: "Sync scheduled", message: "Your files will sync tonight at 02:00." },
                  success: { title: "Saved", message: "“Q3 roadmap” was saved to Projects." },
                  warning: { title: "Storage almost full", message: "You have used 92% of your 15 GB." },
                  error: { title: "Upload failed", message: "design-review.mov is larger than 2 GB." }
                }
                for (const button of document.querySelectorAll("[data-severity]")) {
                  button.addEventListener("click", () => {
                    const severity = button.dataset.severity
                    region.add(Object.assign({ severity: severity }, samples[severity]))
                  })
                }
            """),
            height=340,
        ),
        ComponentExample(
            key="placements",
            title="Placements and spacing",
            description=(
                "<p>Pick a <code>placement</code> and show a toast there. "
                "<code>offset-x</code>, <code>offset-y</code> and <code>gap</code> set "
                "the distances; switch the preview to RTL to see start and end "
                "swap.</p>"
            ),
            html=_src("""
                <div class="row demo-pad">
                  <label>Placement
                    <select id="placement-choice">
                      <option>top-start</option>
                      <option selected>top-center</option>
                      <option>top-end</option>
                      <option>bottom-start</option>
                      <option>bottom-center</option>
                      <option>bottom-end</option>
                    </select>
                  </label>
                  <button type="button" class="btn primary" id="placement-show">Show toast</button>
                </div>
                <mj-toast-region id="placement-toasts" placement="top-center" offset-x="1.5rem" offset-y="1.5rem" gap="0.5rem"></mj-toast-region>
            """),
            css=_BUTTON_CSS + _src("""
                .demo-pad { padding: var(--mj-space-4); padding-block-start: 6rem; }
            """),
            script=_src("""
                const region = document.getElementById("placement-toasts")
                const choice = document.getElementById("placement-choice")
                document.getElementById("placement-show").addEventListener("click", () => {
                  region.setAttribute("placement", choice.value)
                  region.add({ message: "Shown at " + choice.value + ".", duration: 4000 })
                })
            """),
            height=360,
        ),
        ComponentExample(
            key="queue",
            title="Queue and persistent toasts",
            description=(
                "<p><code>max-visible=\"2\"</code>: <strong>Add 5</strong> shows two "
                "persistent toasts (<code>duration: 0</code>) and queues three; close "
                "one and the next moves up. <strong>Dismiss all</strong> clears the "
                "visible and the queued toasts; <code>count</code>, "
                "<code>visible</code> and <code>queue</code> are shown below.</p>"
            ),
            html=_src("""
                <div class="row demo-pad">
                  <button type="button" class="btn primary" id="queue-add">Add 5</button>
                  <button type="button" class="btn" id="queue-clear">Dismiss all</button>
                  <output id="queue-status" class="muted">count 0 · visible 0 · queued 0</output>
                </div>
                <mj-toast-region id="queue-toasts" max-visible="2"></mj-toast-region>
            """),
            css=_BUTTON_CSS + _src("""
                .demo-pad { padding: var(--mj-space-4); }
            """),
            script=_src("""
                const region = document.getElementById("queue-toasts")
                const status = document.getElementById("queue-status")
                let batch = 0
                function report() {
                  status.textContent = "count " + region.count + " · visible " + region.visible.length + " · queued " + region.queue.length
                }
                document.getElementById("queue-add").addEventListener("click", () => {
                  batch = batch + 1
                  for (let index = 1; index <= 5; index = index + 1) {
                    region.add({ message: "Build " + batch + "." + index + " finished.", severity: "success", duration: 0 })
                  }
                  report()
                })
                document.getElementById("queue-clear").addEventListener("click", () => region.dismissAll())
                for (const name of ["mj-toast-show", "mj-toast-dismiss", "mj-toast-queue-empty"]) {
                  region.addEventListener(name, report)
                }
            """),
            height=320,
        ),
        ComponentExample(
            key="actions",
            title="Actions, update and requests",
            description=(
                "<p><strong>Archive</strong> shows a toast with an Undo action "
                "(<code>mj-toast-action</code>). <strong>Upload</strong> keeps one "
                "toast and changes it with <code>update(id, changes)</code> until it "
                "turns into a success that auto-dismisses. <strong>Request</strong> "
                "dispatches <code>mj-toast-request</code> instead of calling "
                "<code>add()</code>.</p>"
            ),
            html=_src("""
                <div class="row demo-pad">
                  <button type="button" class="btn" id="action-archive">Archive conversation</button>
                  <button type="button" class="btn" id="action-upload">Upload report.pdf</button>
                  <button type="button" class="btn" id="action-request">Request a toast by event</button>
                </div>
                <mj-toast-region id="action-toasts"></mj-toast-region>
            """),
            css=_BUTTON_CSS + _src("""
                .demo-pad { padding: var(--mj-space-4); }
            """),
            script=_src("""
                const region = document.getElementById("action-toasts")
                document.getElementById("action-archive").addEventListener("click", () => {
                  region.add({
                    message: "Conversation archived.",
                    duration: 8000,
                    actions: [{ label: "Undo", onClick: () => mjSandbox.log("undo archive", {}) }]
                  })
                })
                document.getElementById("action-upload").addEventListener("click", () => {
                  const id = region.add({ title: "Uploading report.pdf", message: "0%", duration: 0 })
                  let percent = 0
                  const timer = window.setInterval(() => {
                    percent = percent + 25
                    if (percent < 100) {
                      region.update(id, { message: percent + "%" })
                    } else {
                      window.clearInterval(timer)
                      region.update(id, { title: "Upload complete", message: "report.pdf is ready to share.", severity: "success", duration: 4000 })
                    }
                  }, 600)
                })
                document.getElementById("action-request").addEventListener("click", () => {
                  region.dispatchEvent(new CustomEvent("mj-toast-request", {
                    bubbles: true,
                    detail: { message: "Added through an mj-toast-request event.", severity: "info" }
                  }))
                })
            """),
            height=340,
        ),
        ComponentExample(
            key="over-modal",
            title="Toasts above a modal",
            description=(
                "<p>Open the modal dialog, then <strong>Save draft</strong> inside it: "
                "the region moves into the dialog's top-layer surface, so the toast is "
                "drawn above the backdrop and its close button can be clicked although "
                "the page behind is inert.</p>"
            ),
            html=_src("""
                <mj-toast-region id="modal-toasts"></mj-toast-region>
                <div class="demo-pad"><button type="button" class="btn primary" id="open-compose">Compose email</button></div>

                <mj-dialog id="compose-dialog">
                  <span slot="title">New message</span>
                  <label class="field">To <input type="email" value="team@example.com"></label>
                  <label class="field">Subject <input type="text" value="Launch checklist"></label>
                  <div slot="footer" class="actions">
                    <button type="button" class="btn" id="compose-draft">Save draft</button>
                    <button type="button" class="btn primary" id="compose-send">Send</button>
                  </div>
                </mj-dialog>
            """),
            css=_BUTTON_CSS + _FIELD_CSS + _src("""
                .demo-pad { padding: var(--mj-space-4); }
            """),
            script=_src("""
                const region = document.getElementById("modal-toasts")
                const dialog = document.getElementById("compose-dialog")
                document.getElementById("open-compose").addEventListener("click", () => dialog.showModal())
                document.getElementById("compose-draft").addEventListener("click", () => {
                  region.add({ message: "Draft saved.", severity: "success", duration: 0 })
                })
                document.getElementById("compose-send").addEventListener("click", () => {
                  dialog.close()
                  region.add({ message: "Message sent to team@example.com.", severity: "success" })
                })
                dialog.showModal()
            """),
            height=420,
        ),
    ],
    slots=[],
    properties=[
        ("visible", "object[] (read-only). Copy of the descriptors on screen, oldest first."),
        ("queue", "object[] (read-only). Copy of the descriptors waiting for a free slot."),
        ("count", "number (read-only). Visible plus queued toasts."),
    ],
    methods=[
        ("add(descriptor) -> string", "Shows or queues a toast and returns its id. Descriptor: { id?, message, title?, severity?: 'info' | 'success' | 'warning' | 'error', duration?: ms (0 = persistent), actions?: [{ label, onClick?, dismiss? }] }."),
        ("update(id, changes) -> boolean", "Merges `changes` into a visible or queued toast and re-renders it; a new `duration` restarts the timer."),
        ("dismiss(id) -> boolean", "Removes one visible or queued toast (reason `api`)."),
        ("dismissAll()", "Removes every visible and queued toast (reason `api`); no queued toast is promoted."),
    ],
    parts=[
        ("region", "The fixed region that holds the list."),
        ("toast", "Each toast (<li>, with data-severity)."),
        ("toast-close", "The close button of a toast."),
        ("toast-action", "An action button of a toast."),
    ],
    css_properties=[
        ("--mj-toast-region-gap", "Space between toasts; wins over the `gap` attribute (default var(--mj-space-3))."),
        ("--mj-toast-region-offset-x", "Inline distance from the viewport edge; wins over `offset-x` (default var(--mj-space-4))."),
        ("--mj-toast-region-offset-y", "Block distance from the viewport edge; wins over `offset-y` (default var(--mj-space-4))."),
        ("--mj-toast-max-width", "Maximum toast width (default 24rem)."),
    ],
)


# ---------------------------------------------------------------------------
# mj-notification-center
# ---------------------------------------------------------------------------

_NC_ITEMS_JS = _src("""
    const minutes = (count) => Date.now() - count * 60000
    const items = [
      { id: "deploy-241", title: "Deployment succeeded", body: "Production deploy v2.4.1 finished in 3 min.", timestamp: minutes(4) },
      { id: "comment-88", title: "New comment on PR #88", body: "Priya: Looks good, one nit on the migration.", timestamp: minutes(45) },
      { id: "invoice-11", title: "Invoice paid", body: "Acme Corp paid invoice INV-2026-011.", timestamp: minutes(60 * 26), read: true },
      { id: "security-3", title: "New sign-in", body: "Your account signed in from Lisbon, Portugal.", timestamp: minutes(60 * 24 * 5), read: true }
    ]
""")

_NOTIFICATION_CENTER = ComponentDoc(
    tag="mj-notification-center",
    title="Notification Center",
    group="overlays",
    summary="Persistent notification list with unread tracking, grouping and bulk actions.",
    description=(
        "<p><code>&lt;mj-notification-center&gt;</code> renders a scrollable list "
        "of notifications under a header with the title, an unread badge and the "
        "<em>Mark all read</em> / <em>Clear all</em> buttons. Items are grouped by "
        "day (Today / Yesterday / Older), by <code>category</code> or not at all; "
        "times are shown relative (\"5 minutes ago\"), formatted with "
        "<code>Intl</code>. Unread items have a dot; activating an item marks it "
        "read and emits <code>mj-notification-select</code> (and navigates to a "
        "safe <code>href</code>). Text is always set as text.</p>"
        "<p>The list is one tab stop: <kbd>↑</kbd> / <kbd>↓</kbd> (and "
        "<kbd>Home</kbd> / <kbd>End</kbd>) move between items, <kbd>Enter</kbd> or "
        "<kbd>Space</kbd> selects, <kbd>Delete</kbd> or <kbd>Backspace</kbd> "
        "dismisses and focus moves to the neighbour. The <code>loading</code> "
        "attribute shows skeleton rows. It renders inline; put it in an "
        "<code>&lt;mj-popover&gt;</code> or <code>&lt;mj-drawer&gt;</code> for a "
        "notification panel.</p>"
    ),
    how_to_use=(
        "<p>Assign <code>items</code> to show a saved list (a value set before the "
        "element upgraded is kept) and call <code>addItem({ id, title, body, "
        "timestamp, category, severity, href, avatarSrc, avatarAlt, read })</code> "
        "for new ones; they are added at the top, unread unless "
        "<code>read: true</code>, and an item beyond <code>max-items</code> evicts "
        "the oldest read one. Manage items with <code>markRead(id)</code>, "
        "<code>markAllRead()</code>, <code>dismiss(id)</code> (cancelable event), "
        "<code>remove(id)</code> (no event) and <code>clearAll()</code>. Hide the "
        "bulk buttons with <code>show-mark-all-read=\"false\"</code> / "
        "<code>show-clear-all=\"false\"</code>.</p>"
    ),
    example="",
    attributes=[
        AttributeDoc(name="label", kind="string", default="Notifications",
                     description="Heading text and accessible name of the list."),
        AttributeDoc(name="group-by", kind="enum", values=["date", "category", "none"], default="date",
                     description="Grouping: by day (Today / Yesterday / Older), by item `category` (\"Other\" when missing) or none."),
        AttributeDoc(name="empty-message", kind="string", default="No notifications",
                     description="Text shown when the list is empty (the `empty` slot replaces it)."),
        AttributeDoc(name="max-items", kind="number", default="100",
                     description="Items kept; beyond it the oldest read item is evicted (an unread one when all are unread)."),
        AttributeDoc(name="loading", kind="boolean",
                     description="Shows three skeleton rows instead of the list and sets aria-busy."),
        AttributeDoc(name="show-mark-all-read", kind="boolean", default="true",
                     description="`false` hides the Mark all read button."),
        AttributeDoc(name="show-clear-all", kind="boolean", default="true",
                     description="`false` hides the Clear all button."),
        AttributeDoc(name="mark-all-read-label", kind="string", default="Mark all read",
                     description="Text of the Mark all read button."),
        AttributeDoc(name="clear-all-label", kind="string", default="Clear all",
                     description="Text of the Clear all button."),
        AttributeDoc(name="dismiss-label", kind="string", default="Dismiss",
                     description="Accessible label prefix of each item's dismiss button."),
        AttributeDoc(name="unread-label", kind="string", default="Unread",
                     description="Prefix announced for unread items."),
        AttributeDoc(name="older-label", kind="string", default="Older",
                     description="Heading of the date group for items older than yesterday."),
    ],
    events=[
        ("mj-notification-select", "An item was activated (click, Enter, Space); fires after mj-notification-read.",
         "{ item: object }"),
        ("mj-notification-read", "An unread item was marked read (activation or markRead()).", "{ item: object }"),
        ("mj-notification-dismiss", "Cancelable. An item is about to be dismissed (its button, Delete / Backspace, dismiss()); preventDefault() keeps it.",
         "{ item: object }"),
        ("mj-notification-mark-all-read", "Every item was marked read.", "{ count: number }  (items that were unread)"),
        ("mj-notification-clear-all", "Cancelable. All items are about to be cleared; preventDefault() keeps them.",
         "{ count: number }"),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>Four notifications grouped by day, two unread. Click an item (or "
                "focus the list and use <kbd>↑</kbd> <kbd>↓</kbd> <kbd>Enter</kbd> "
                "<kbd>Delete</kbd>) and watch the badge. <strong>Simulate new "
                "notification</strong> calls <code>addItem()</code>.</p>"
            ),
            html=_src("""
                <div class="row demo-pad">
                  <button type="button" class="btn primary" id="add-notification">Simulate new notification</button>
                </div>
                <mj-notification-center id="demo-notifications"></mj-notification-center>
            """),
            css=_BUTTON_CSS + _src("""
                .demo-pad { padding: var(--mj-space-4); }
                mj-notification-center { margin-inline: var(--mj-space-4); }
            """),
            script=_NC_ITEMS_JS + _src("""

                const center = document.getElementById("demo-notifications")
                center.items = items
                let next = 1
                document.getElementById("add-notification").addEventListener("click", () => {
                  center.addItem({
                    id: "mention-" + next,
                    title: "You were mentioned",
                    body: "Grace mentioned you in “Release notes” (" + next + ").",
                    timestamp: Date.now()
                  })
                  next = next + 1
                })
            """),
        ),
        ComponentExample(
            key="categories",
            title="Grouped by category",
            description=(
                "<p><code>group-by=\"category\"</code> with per-item "
                "<code>severity</code> and <code>avatarSrc</code> (drawn on a canvas). "
                "Items without a category land under <em>Other</em>.</p>"
            ),
            html=_src("""
                <mj-notification-center id="category-notifications" group-by="category" label="Activity"></mj-notification-center>
            """),
            css=_src("""
                mj-notification-center { margin: var(--mj-space-4); }
            """),
            script=_src("""
                function avatar(initials, colour) {
                  const canvas = document.createElement("canvas")
                  canvas.width = 64
                  canvas.height = 64
                  const ctx = canvas.getContext("2d")
                  ctx.fillStyle = colour
                  ctx.beginPath()
                  ctx.arc(32, 32, 32, 0, Math.PI * 2)
                  ctx.fill()
                  ctx.fillStyle = "#ffffff"
                  ctx.font = "600 26px system-ui, sans-serif"
                  ctx.textAlign = "center"
                  ctx.textBaseline = "middle"
                  ctx.fillText(initials, 32, 34)
                  return canvas.toDataURL("image/png")
                }
                const now = Date.now()
                document.getElementById("category-notifications").items = [
                  { id: "c1", category: "Mentions", title: "Priya mentioned you", body: "Can you review the API section?",
                    timestamp: now - 120000, avatarSrc: avatar("PS", "#674ea7"), avatarAlt: "Priya Shah" },
                  { id: "c2", category: "Mentions", title: "Linus replied", body: "Fixed in the latest commit.",
                    timestamp: now - 3600000, avatarSrc: avatar("LT", "#3d6f9e"), avatarAlt: "Linus Torvalds", read: true },
                  { id: "c3", category: "Builds", title: "Build #1043 failed", body: "3 tests failed on main.",
                    timestamp: now - 900000, severity: "error" },
                  { id: "c4", category: "Builds", title: "Build #1044 passed", body: "All 812 tests passed.",
                    timestamp: now - 300000, severity: "success" },
                  { id: "c5", title: "Scheduled maintenance", body: "Saturday 02:00-03:00 UTC.", timestamp: now - 86400000 * 2 }
                ]
            """),
        ),
        ComponentExample(
            key="states",
            title="Loading and empty",
            description=(
                "<p><strong>Refresh</strong> sets <code>loading</code> (skeleton rows) "
                "for a second and then assigns the items; <strong>Clear all</strong> "
                "empties the list, which shows the <code>empty</code> slot.</p>"
            ),
            html=_src("""
                <div class="row demo-pad">
                  <button type="button" class="btn primary" id="states-refresh">Refresh</button>
                </div>
                <mj-notification-center id="states-notifications" loading>
                  <div slot="empty" class="empty-state">
                    <strong>You're all caught up</strong>
                    <span class="muted">New notifications will appear here.</span>
                  </div>
                </mj-notification-center>
            """),
            css=_BUTTON_CSS + _src("""
                .demo-pad { padding: var(--mj-space-4); }
                mj-notification-center { margin-inline: var(--mj-space-4); }
                .empty-state { display: grid; gap: var(--mj-space-1); justify-items: center; padding-block: var(--mj-space-4); }
            """),
            script=_NC_ITEMS_JS + _src("""

                const center = document.getElementById("states-notifications")
                function refresh() {
                  center.setAttribute("loading", "")
                  window.setTimeout(() => {
                    center.items = items.map((item) => Object.assign({}, item))
                    center.removeAttribute("loading")
                  }, 1000)
                }
                document.getElementById("states-refresh").addEventListener("click", refresh)
                refresh()
            """),
        ),
        ComponentExample(
            key="in-popover",
            title="Inside a popover",
            description=(
                "<p>The usual composition: a bell button opens an "
                "<code>&lt;mj-popover&gt;</code> holding the notification center; the "
                "button's count follows <code>unreadCount</code>. The "
                "<code>footer</code> slot links to the full history.</p>"
            ),
            html=_src("""
                <div class="row demo-pad top-bar">
                  <strong>Acme Console</strong>
                  <mj-popover id="bell-popover" placement="bottom-end" no-close-button label="Notifications">
                    <button slot="trigger" type="button" class="btn" id="bell-button">🔔 Notifications (2)</button>
                    <mj-notification-center id="bell-notifications">
                      <div slot="footer"><a href="#all-notifications" id="view-all">View all notifications</a></div>
                    </mj-notification-center>
                  </mj-popover>
                </div>
            """),
            css=_BUTTON_CSS + _src("""
                .top-bar { justify-content: space-between; padding: var(--mj-space-4); }
                #bell-popover { --mj-popover-width: auto; --mj-popover-padding: 0; }
            """),
            script=_NC_ITEMS_JS + _src("""

                const center = document.getElementById("bell-notifications")
                const bell = document.getElementById("bell-button")
                center.items = items
                function syncBell() {
                  bell.textContent = "🔔 Notifications (" + center.unreadCount + ")"
                }
                for (const name of ["mj-notification-read", "mj-notification-mark-all-read", "mj-notification-clear-all", "mj-notification-dismiss"]) {
                  center.addEventListener(name, () => window.setTimeout(syncBell, 0))
                }
                document.getElementById("view-all").addEventListener("click", (event) => {
                  event.preventDefault()
                  mjSandbox.log("view all", {})
                })
                document.getElementById("bell-popover").show()
            """),
            height=520,
        ),
        ComponentExample(
            key="events",
            title="Custom header, vetoes, max-items",
            description=(
                "<p>The <code>header</code> slot replaces title, badge and buttons "
                "with a custom header that calls <code>markAllRead()</code>. A "
                "<code>mj-notification-dismiss</code> listener refuses to dismiss "
                "pinned items, and <code>max-items=\"5\"</code> evicts the oldest read "
                "item when <strong>Add</strong> goes past five.</p>"
            ),
            html=_src("""
                <mj-notification-center id="events-notifications" max-items="5" group-by="none">
                  <div slot="header" class="custom-header">
                    <strong>Inbox</strong>
                    <button type="button" class="btn" id="custom-mark-read">Mark all read</button>
                    <button type="button" class="btn" id="custom-add">Add</button>
                  </div>
                </mj-notification-center>
            """),
            css=_BUTTON_CSS + _src("""
                mj-notification-center { margin: var(--mj-space-4); }
                .custom-header { display: flex; align-items: center; gap: var(--mj-space-2); inline-size: 100%; }
                .custom-header strong { flex: 1; }
            """),
            script=_src("""
                const center = document.getElementById("events-notifications")
                const now = Date.now()
                center.items = [
                  { id: "pinned-1", title: "📌 Pinned: on-call rota", body: "You are on call this week.", timestamp: now - 7200000, read: true, pinned: true },
                  { id: "e2", title: "Weekly digest", body: "12 new posts in #engineering.", timestamp: now - 3600000, read: true },
                  { id: "e3", title: "Reminder", body: "1:1 with Alex at 15:00.", timestamp: now - 600000 }
                ]
                let next = 4
                center.addEventListener("mj-notification-dismiss", (event) => {
                  if (event.detail.item.pinned === true) {
                    event.preventDefault()
                    mjSandbox.log("dismiss refused", { id: event.detail.item.id })
                  }
                })
                document.getElementById("custom-mark-read").addEventListener("click", () => center.markAllRead())
                document.getElementById("custom-add").addEventListener("click", () => {
                  center.addItem({ id: "e" + next, title: "Ticket #" + (400 + next) + " updated", body: "Status changed to In progress.", timestamp: Date.now() })
                  next = next + 1
                  mjSandbox.log("items", { count: center.items.length, ids: center.items.map((item) => item.id) })
                })
            """),
        ),
    ],
    slots=[
        ("header", "Replaces the whole header: title, unread badge and the two bulk buttons.",
         '<div class="custom-header"><strong>Custom header</strong></div>'),
        ("footer", "Row below the list (hidden while empty).",
         '<a href="#all">View all notifications</a>'),
        ("empty", "Content shown while the list is empty; replaces `empty-message`.",
         "<span>Nothing new. Enjoy the quiet.</span>"),
    ],
    properties=[
        ("items", "object[]. The notifications: { id, title, body?, timestamp?, read?, category?, severity?, href?, avatarSrc?, avatarAlt? }. Items are normalised (string id, boolean read) in place."),
        ("unreadCount", "number (read-only). Items with read false."),
        ("selectedItem", "object | null (read-only). The item last activated or focused."),
    ],
    methods=[
        ("addItem(descriptor)", "Adds an item at the top (unread unless read: true); a duplicate id is refused with a console error."),
        ("markRead(id) -> boolean", "Marks one item read; emits mj-notification-read."),
        ("markAllRead()", "Marks every item read; emits mj-notification-mark-all-read."),
        ("dismiss(id) -> boolean", "Removes one item after a cancelable mj-notification-dismiss."),
        ("remove(id) -> boolean", "Removes one item without an event."),
        ("clearAll()", "Removes every item after a cancelable mj-notification-clear-all."),
    ],
    parts=[
        ("header", "Header row."),
        ("title", "Heading text."),
        ("badge", "Unread count badge."),
        ("mark-all-read", "Mark all read button."),
        ("clear-all", "Clear all button."),
        ("list", "The list."),
        ("group-header", "A group heading row."),
        ("item", "A notification row."),
        ("item-unread", "Unread dot of a row."),
        ("item-avatar", "Avatar image of a row."),
        ("item-dismiss", "Dismiss button of a row."),
        ("empty", "Empty-state row."),
        ("skeleton", "A loading skeleton row."),
        ("footer", "Footer row."),
    ],
    css_properties=[
        ("--mj-nc-width", "Panel width (default 22rem)."),
        ("--mj-nc-max-height", "Maximum panel height; the list scrolls (default 80vh)."),
        ("--mj-nc-bg", "Panel background (default var(--mj-surface))."),
        ("--mj-nc-item-padding", "Padding of each row (default var(--mj-space-4))."),
        ("--mj-nc-unread-color", "Colour of the unread dot (default var(--mj-accent)); the badge always uses --mj-accent and hides at zero."),
    ],
)


# ---------------------------------------------------------------------------
# mj-context-menu
# ---------------------------------------------------------------------------

_TARGET_CSS = _src("""
    .menu-target {
      margin: var(--mj-space-4);
      padding: var(--mj-space-6);
      border: 2px dashed var(--mj-border-strong);
      border-radius: var(--mj-radius-lg);
      background: var(--mj-bg-subtle);
      color: var(--mj-text);
      user-select: none;
    }
    .menu-target:focus-visible {
      outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
      outline-offset: var(--mj-focus-ring-offset);
    }
""")

_CONTEXT_MENU = ComponentDoc(
    tag="mj-context-menu",
    title="Context Menu",
    group="overlays",
    summary="Actions menu opened by right-click, the ContextMenu key or Shift+F10 over a target.",
    description=(
        "<p><code>&lt;mj-context-menu&gt;</code> listens on its target &mdash; the "
        "first element in its default slot, or the element named by "
        "<code>target-id</code> &mdash; and opens a menu (role menu, in the top "
        "layer) at the pointer on right-click. From the keyboard, "
        "<kbd>ContextMenu</kbd> or <kbd>Shift+F10</kbd> on the focused target "
        "opens it below the target's start corner, so the target should be "
        "focusable. <code>show(x, y)</code> opens it at viewport coordinates; "
        "every open path emits <code>mj-context-menu-before-open</code> (cancelable) "
        "and <code>mj-context-menu-open</code>.</p>"
        "<p>Items come from the <code>items</code> property: plain actions, "
        "<code>checkbox</code> and <code>radio</code> items (grouped by "
        "<code>group</code>; both keep the menu open), <code>separator</code>s, "
        "<code>group</code> labels, icons, shortcut hints and nested "
        "<code>submenu</code>s. Keyboard: <kbd>↑</kbd> / <kbd>↓</kbd>, "
        "<kbd>Home</kbd> / <kbd>End</kbd>, type-ahead, <kbd>Enter</kbd> / "
        "<kbd>Space</kbd>, <kbd>→</kbd> opens and <kbd>←</kbd> closes a submenu "
        "(swapped in RTL), <kbd>Escape</kbd> closes one level, <kbd>Tab</kbd> "
        "closes the menu. A press outside, scrolling, resizing or leaving the "
        "window closes it (reason <code>light-dismiss</code>). Labels are set as "
        "text.</p>"
    ),
    how_to_use=(
        "<p>Wrap the target (give it <code>tabindex=\"0\"</code> when it is not "
        "focusable) or set <code>target-id</code>, assign <code>items</code> "
        "(<code>{ id, label, type?, group?, checked?, disabled?, icon?, shortcut?, "
        "submenu? }</code>) and handle <code>mj-context-menu-select</code>; checkbox "
        "and radio items report the new <code>checked</code> state and update "
        "their descriptor. Change <code>items</code> in a "
        "<code>mj-context-menu-before-open</code> listener to tailor the menu to "
        "what was clicked, or cancel the event to keep it closed. "
        "<code>variant</code> sets the default item type. Prefer "
        "<code>show(x, y)</code> over setting <code>open</code> directly, which "
        "reuses the last coordinates.</p>"
    ),
    example="",
    attributes=[
        AttributeDoc(name="open", kind="boolean",
                     description="Present while the menu is open; adding it opens at `openCoords` (or below the target), removing it closes (reason `api`)."),
        AttributeDoc(name="target-id", kind="string",
                     description="Id of an element elsewhere in the document to attach to instead of the slotted target."),
        AttributeDoc(name="label", kind="string", default="Actions",
                     description="Accessible name of the menu."),
        AttributeDoc(name="variant", kind="enum", values=["menu", "checkbox-group", "radio-group"], default="menu",
                     description="Default type of items without a `type`: plain items, checkboxes or radios."),
    ],
    events=[
        ("mj-context-menu-before-open", "Cancelable. About to open; preventDefault() keeps it closed. x / y are 0 for keyboard opening.",
         "{ x: number, y: number, reason: 'pointer' | 'keyboard' | 'api' }"),
        ("mj-context-menu-open", "The menu opened.", "{ x: number, y: number, targetEl: Element | null }"),
        ("mj-context-menu-select", "An item was activated; `checked` is the new state for checkbox / radio items.",
         "{ item: object, checked?: boolean }"),
        ("mj-context-menu-close", "The menu closed.", "{ reason: 'escape' | 'item-select' | 'light-dismiss' | 'api' }"),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>Right-click the file card, or focus it with <kbd>Tab</kbd> and "
                "press <kbd>Shift+F10</kbd>. The button below opens the same menu "
                "with <code>show(x, y)</code>. <em>Delete</em> is disabled; choices "
                "appear in the event log.</p>"
            ),
            html=_src("""
                <mj-context-menu id="demo-menu" label="File actions">
                  <div class="menu-target" tabindex="0">📄 budget-2027.xlsx · right-click or Shift+F10</div>
                </mj-context-menu>
                <div class="row demo-pad">
                  <button type="button" class="btn" id="menu-button">Open the menu from a button</button>
                </div>
            """),
            css=_BUTTON_CSS + _TARGET_CSS + _src("""
                .demo-pad { padding-inline: var(--mj-space-4); }
            """),
            script=_src("""
                const menu = document.getElementById("demo-menu")
                menu.items = [
                  { id: "copy", label: "Copy", shortcut: "Ctrl+C" },
                  { id: "cut", label: "Cut", shortcut: "Ctrl+X" },
                  { id: "paste", label: "Paste", shortcut: "Ctrl+V" },
                  { type: "separator" },
                  { id: "delete", label: "Delete", disabled: true }
                ]
                const button = document.getElementById("menu-button")
                button.addEventListener("click", () => {
                  const box = button.getBoundingClientRect()
                  menu.show(box.left, box.bottom + 4)
                })
            """),
            height=320,
        ),
        ComponentExample(
            key="checkable",
            title="Checkbox, radio, groups",
            description=(
                "<p>Checkbox items toggle and radio items pick one of their "
                "<code>group</code>; both keep the menu open and the preview follows "
                "the state. Group labels, icons and shortcut hints are part of the "
                "item descriptors.</p>"
            ),
            html=_src("""
                <mj-context-menu id="view-menu" label="View options">
                  <div class="menu-target doc-preview" tabindex="0" id="doc-preview">
                    <p>Right-click this document to change the view.</p>
                    <p class="comment-note">💬 2 comments</p>
                  </div>
                </mj-context-menu>
            """),
            css=_TARGET_CSS + _src("""
                .doc-preview.show-grid {
                  background-image: linear-gradient(var(--mj-border) 1px, transparent 1px);
                  background-size: 100% 1.5rem;
                }
                .doc-preview.hide-comments .comment-note { display: none; }
            """),
            script=_src("""
                const menu = document.getElementById("view-menu")
                const preview = document.getElementById("doc-preview")
                menu.items = [
                  { type: "group", label: "Show" },
                  { id: "grid", label: "Gridlines", type: "checkbox", checked: false },
                  { id: "comments", label: "Comments", type: "checkbox", checked: true },
                  { type: "separator" },
                  { type: "group", label: "Zoom" },
                  { id: "zoom-90", label: "90%", type: "radio", group: "zoom" },
                  { id: "zoom-100", label: "100%", type: "radio", group: "zoom", checked: true },
                  { id: "zoom-125", label: "125%", type: "radio", group: "zoom" },
                  { type: "separator" },
                  { id: "reset", label: "Reset view", icon: "↺", shortcut: "Ctrl+0" }
                ]
                menu.addEventListener("mj-context-menu-select", (event) => {
                  const item = event.detail.item
                  if (item.id === "grid") { preview.classList.toggle("show-grid", event.detail.checked) }
                  if (item.id === "comments") { preview.classList.toggle("hide-comments", event.detail.checked === false) }
                  if (item.group === "zoom") { preview.style.fontSize = item.label }
                  if (item.id === "reset") {
                    preview.className = "menu-target doc-preview"
                    preview.style.fontSize = ""
                  }
                })
            """),
            height=420,
        ),
        ComponentExample(
            key="submenu",
            title="Submenus and keyboard",
            description=(
                "<p><em>Share</em> and <em>Move to</em> have submenus: hover them or "
                "press <kbd>→</kbd>; <kbd>←</kbd> or <kbd>Escape</kbd> goes back one "
                "level. Type a letter to jump to an item (type-ahead).</p>"
            ),
            html=_src("""
                <mj-context-menu id="share-menu" label="Photo actions">
                  <div class="menu-target" tabindex="0">🖼️ IMG_2031.jpg · right-click or Shift+F10</div>
                </mj-context-menu>
            """),
            css=_TARGET_CSS,
            script=_src("""
                const menu = document.getElementById("share-menu")
                menu.items = [
                  { id: "open", label: "Open", shortcut: "Enter" },
                  { id: "share", label: "Share", icon: "↗", submenu: [
                    { id: "share-mail", label: "Mail" },
                    { id: "share-link", label: "Copy link" },
                    { id: "share-embed", label: "Embed code" }
                  ] },
                  { id: "move", label: "Move to", submenu: [
                    { id: "move-holiday", label: "Holiday 2026" },
                    { id: "move-family", label: "Family" },
                    { id: "move-archive", label: "Archive" }
                  ] },
                  { id: "rename", label: "Rename", shortcut: "F2" },
                  { type: "separator" },
                  { id: "trash", label: "Move to bin", shortcut: "Del" }
                ]
            """),
            height=360,
        ),
        ComponentExample(
            key="dynamic",
            title="target-id and per-row items",
            description=(
                "<p>One menu for a whole list via <code>target-id</code>. A "
                "<code>mj-context-menu-before-open</code> listener finds the row "
                "under the pointer (or the focused row for <kbd>Shift+F10</kbd>), "
                "rebuilds <code>items</code> for it &mdash; <em>Delete</em> is "
                "disabled for the locked file &mdash; and cancels the menu on the "
                "list header.</p>"
            ),
            html=_src("""
                <ul id="file-list" class="file-list">
                  <li class="file-head">Name · right-click a file</li>
                  <li tabindex="0" data-file="contract.pdf">📄 contract.pdf</li>
                  <li tabindex="0" data-file="logo.svg">🖼️ logo.svg</li>
                  <li tabindex="0" data-file="payroll.xlsx" data-locked>🔒 payroll.xlsx (locked)</li>
                </ul>
                <mj-context-menu id="file-menu" target-id="file-list" label="File actions"></mj-context-menu>
            """),
            css=_src("""
                .file-list {
                  list-style: none;
                  margin: var(--mj-space-4);
                  padding: 0;
                  border: 1px solid var(--mj-border);
                  border-radius: var(--mj-radius-md);
                  max-inline-size: 24rem;
                }
                .file-list li { padding-block: var(--mj-space-2); padding-inline: var(--mj-space-3); }
                .file-list li + li { border-block-start: 1px solid var(--mj-border); }
                .file-list .file-head { color: var(--mj-text-muted); font-size: var(--mj-font-size-sm); }
                .file-list li[tabindex]:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); }
            """),
            script=_src("""
                const menu = document.getElementById("file-menu")
                menu.addEventListener("mj-context-menu-before-open", (event) => {
                  const { x, y, reason } = event.detail
                  const hit = reason === "pointer" ? document.elementFromPoint(x, y) : document.activeElement
                  const row = hit !== null ? hit.closest("[data-file]") : null
                  if (row === null) {
                    event.preventDefault()
                    mjSandbox.log("menu refused", { reason: reason })
                    return
                  }
                  const locked = row.hasAttribute("data-locked")
                  menu.items = [
                    { type: "group", label: row.dataset.file },
                    { id: "open", label: "Open" },
                    { id: "download", label: "Download" },
                    { type: "separator" },
                    { id: "delete", label: locked ? "Delete (locked)" : "Delete", disabled: locked }
                  ]
                })
            """),
            height=320,
        ),
    ],
    slots=[
        ("", "The target: the first slotted element receives the contextmenu and keyboard listeners. Ignored when `target-id` is set.",
         '<div class="menu-target" tabindex="0">Right-click here</div>'),
    ],
    properties=[
        ("items", "object[]. Menu descriptors: { id, label, type?: 'item' | 'checkbox' | 'radio' | 'separator' | 'group', group?, checked?, disabled?, icon?, shortcut?, submenu?: object[] }. Re-rendered when set while open."),
        ("open", "boolean. Reflects the `open` attribute."),
        ("targetEl", "Element | null (read-only). The resolved target."),
        ("openCoords", "{ x: number, y: number } | null. Point the menu was last opened at (null for keyboard opening)."),
    ],
    methods=[
        ("show(x?, y?)", "Opens the menu at viewport coordinates, or below the target without them (reason `api`)."),
        ("close()", "Closes the menu (reason `api`)."),
    ],
    parts=[
        ("menu", "The top-level menu list."),
        ("submenu", "A submenu list (it also has part `menu`)."),
        ("item", "A menu item."),
        ("item-icon", "Icon of an item."),
        ("item-shortcut", "Shortcut hint of an item."),
        ("submenu-arrow", "Arrow of an item that has a submenu."),
        ("separator", "Separator line."),
        ("group-label", "Group label row."),
    ],
    css_properties=[
        ("--mj-context-menu-width", "Minimum menu width (default 12rem)."),
        ("--mj-context-menu-bg", "Menu background (default var(--mj-surface))."),
        ("--mj-context-menu-radius", "Corner radius (default var(--mj-radius-md))."),
        ("--mj-context-menu-shadow", "Shadow (default var(--mj-elevation-3))."),
        ("--mj-context-menu-padding", "Block padding of the list (default var(--mj-space-1))."),
        ("--mj-context-menu-item-height", "Item height (default 2.25rem)."),
        ("--mj-context-menu-z-index", "z-index when the top layer is not available (default var(--mj-layer-popover))."),
    ],
)


# ---------------------------------------------------------------------------
# mj-command-palette
# ---------------------------------------------------------------------------

_KBD_CSS = _src("""
    kbd {
      font-family: var(--mj-font-mono);
      font-size: var(--mj-font-size-xs);
      padding-inline: var(--mj-space-1);
      border: 1px solid var(--mj-border-strong);
      border-radius: var(--mj-radius-sm);
      background: var(--mj-bg-subtle);
    }
    .demo-pad { padding: var(--mj-space-4); }
""")

_COMMAND_PALETTE = ComponentDoc(
    tag="mj-command-palette",
    title="Command Palette",
    group="overlays",
    summary="Keyboard-first, searchable command launcher opened with a global shortcut.",
    description=(
        "<p><code>&lt;mj-command-palette&gt;</code> is a modal search box over a "
        "list of commands: focus is trapped, the page behind is inert and the "
        "palette sits in the top layer. It opens on the global shortcut "
        "(default <kbd>Ctrl+K</kbd> / <kbd>Cmd+K</kbd>; modifiers must match "
        "exactly, and a shortcut without Ctrl / Meta / Alt is ignored while the "
        "user types in a field), on <code>show()</code> or the <code>open</code> "
        "attribute; the shortcut does nothing while another modal is open.</p>"
        "<p>With an empty query it lists the recently used commands (stored in "
        "<code>localStorage</code> under <code>storage-key</code>) or else the "
        "first ten commands, and that list can be activated like any result. "
        "Typing filters (prefix, substring including <code>keywords</code>, then "
        "fuzzy match; recent commands rank higher; disabled commands are left "
        "out) after a <code>debounce</code>, or calls your async "
        "<code>filterFn</code>. <kbd>↑</kbd> / <kbd>↓</kbd> wrap, "
        "<kbd>PageUp</kbd> / <kbd>PageDown</kbd> move by five, <kbd>Enter</kbd> "
        "runs the highlighted command, <kbd>Escape</kbd> or a click on the "
        "backdrop closes. On selection the palette closes first and then calls "
        "<code>action(command)</code> or navigates to a safe <code>href</code>.</p>"
    ),
    how_to_use=(
        "<p>Place one element in the page and assign <code>commands</code>: "
        "<code>{ id, label, icon?, shortcut?, keywords?, group?, disabled?, "
        "action?, href? }</code>. <code>icon</code> is text (an emoji or symbol; "
        "character references are decoded) or a DOM node that is cloned; "
        "<code>shortcut</code> is a hint only. Without <code>action</code> / "
        "<code>href</code>, handle <code>mj-command-palette-select</code> (cancel it "
        "to keep the palette open). Set <code>global-shortcut</code> to a "
        "comma-separated list such as <code>Meta+k,Ctrl+k</code> or "
        "<code>/</code>; an empty value disables it.</p>"
    ),
    example="",
    attributes=[
        AttributeDoc(name="open", kind="boolean",
                     description="Present while open; adding it opens the palette with an empty query, removing it closes (reason `api`)."),
        AttributeDoc(name="placeholder", kind="string", default="Type a command…",
                     description="Placeholder of the search field."),
        AttributeDoc(name="label", kind="string", default="Command palette",
                     description="Accessible name of the dialog."),
        AttributeDoc(name="global-shortcut", kind="string", values=["Meta+k,Ctrl+k", "/", "Ctrl+Shift+p", ""],
                     default="Meta+k,Ctrl+k",
                     description="Comma-separated key combos that open the palette; modifiers (Ctrl, Meta / Cmd, Alt / Option, Shift) must match exactly. Empty disables the shortcut."),
        AttributeDoc(name="empty-message", kind="string", default="No matching commands",
                     description="Text shown when nothing matches (the `empty` slot replaces it)."),
        AttributeDoc(name="max-results", kind="number", default="20", description="Maximum results listed for a query."),
        AttributeDoc(name="max-recent", kind="number", default="5", description="Recently used commands remembered and listed."),
        AttributeDoc(name="debounce", kind="number", default="120",
                     description="Milliseconds after the last keystroke before filtering."),
        AttributeDoc(name="storage-key", kind="string", default="mj-command-palette-recent",
                     description="localStorage key of the recent list; give each palette its own key."),
        AttributeDoc(name="recent-label", kind="string", default="Recent",
                     description="Heading of the recent-commands group."),
    ],
    events=[
        ("mj-command-palette-open", "The palette opened.", "{}"),
        ("mj-command-palette-query", "The debounced query changed (typing only).", "{ query: string }"),
        ("mj-command-palette-results", "Results for a non-empty query were rendered.", "{ results: object[], query: string }"),
        ("mj-command-palette-select", "Cancelable. A command was chosen (Enter or click); preventDefault() keeps the palette open and skips action / href.",
         "{ command: object }"),
        ("mj-command-palette-close", "The palette closed; on a selection this fires before the command's action runs.",
         "{ reason: 'select' | 'escape' | 'backdrop' | 'api' }"),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>Four commands with icons and shortcut hints, open on load. Type to "
                "filter (try <em>fl</em> for a fuzzy match), use the arrows and "
                "<kbd>Enter</kbd>; the choice appears as "
                "<code>mj-command-palette-select</code>. Reopen it with the button or "
                "<kbd>Ctrl+K</kbd> (<kbd>Cmd+K</kbd>) inside the preview.</p>"
            ),
            html=_src("""
                <div class="row demo-pad">
                  <button type="button" class="btn primary" id="open-palette">Search commands</button>
                  <span class="muted">or press <kbd>Ctrl</kbd> + <kbd>K</kbd></span>
                </div>
                <mj-command-palette id="demo-palette" open placeholder="Search commands…"></mj-command-palette>
            """),
            css=_BUTTON_CSS + _KBD_CSS,
            script=_src("""
                const palette = document.getElementById("demo-palette")
                palette.commands = [
                  { id: "new-file", label: "New File", icon: "📄", shortcut: "Ctrl+N" },
                  { id: "open-file", label: "Open File", icon: "📂", shortcut: "Ctrl+O" },
                  { id: "save", label: "Save", icon: "💾", shortcut: "Ctrl+S" },
                  { id: "preferences", label: "Preferences", icon: "⚙️", keywords: ["settings", "options"] }
                ]
                document.getElementById("open-palette").addEventListener("click", () => palette.show())
            """),
            height=460,
        ),
        ComponentExample(
            key="actions",
            title="Actions, groups, recents",
            description=(
                "<p>Commands in <code>group</code>s with <code>action</code> functions "
                "(they run after the palette has closed), a <code>disabled</code> "
                "command and <code>keywords</code> (search <em>dark</em>). "
                "<em>Rename project…</em> opens a prompt dialog. Run a few commands and "
                "reopen: they are listed under <em>Recently used</em>, stored under "
                "<code>storage-key</code>.</p>"
            ),
            html=_src("""
                <div class="row demo-pad">
                  <button type="button" class="btn primary" id="open-actions">Open command palette</button>
                  <output id="action-status" class="muted">Theme: light · Project: Apollo</output>
                </div>
                <mj-command-palette id="actions-palette" storage-key="catalog-demo-palette-recent" recent-label="Recently used" max-recent="3"></mj-command-palette>

                <mj-dialog id="rename-dialog" variant="prompt" confirm-label="Rename" prompt-label="Project name">
                  <span slot="title">Rename project</span>
                </mj-dialog>
            """),
            css=_BUTTON_CSS + _KBD_CSS,
            script=_src("""
                const palette = document.getElementById("actions-palette")
                const status = document.getElementById("action-status")
                const rename = document.getElementById("rename-dialog")
                const state = { theme: "light", project: "Apollo" }
                const render = () => { status.textContent = "Theme: " + state.theme + " · Project: " + state.project }
                palette.commands = [
                  { id: "theme", group: "View", label: "Toggle theme", icon: "🌓", keywords: ["dark", "light"],
                    action: () => { state.theme = state.theme === "light" ? "dark" : "light"; render() } },
                  { id: "zoom-reset", group: "View", label: "Reset zoom", icon: "🔍", shortcut: "Ctrl+0",
                    action: () => mjSandbox.log("zoom reset", {}) },
                  { id: "rename", group: "Project", label: "Rename project…", icon: "✏️",
                    action: () => rename.showModal() },
                  { id: "publish", group: "Project", label: "Publish (needs review)", icon: "🚀", disabled: true },
                  { id: "invite", group: "Project", label: "Invite teammates", icon: "👥", keywords: ["share", "people"],
                    action: () => mjSandbox.log("invite", {}) }
                ]
                rename.addEventListener("mj-dialog-confirm", (event) => {
                  if (event.detail.value.trim().length > 0) {
                    state.project = event.detail.value.trim()
                    render()
                  }
                })
                document.getElementById("open-actions").addEventListener("click", () => palette.show())
            """),
            height=460,
        ),
        ComponentExample(
            key="shortcut",
            title="Custom shortcut",
            description=(
                "<p><code>global-shortcut=\"/\"</code>: press <kbd>/</kbd> anywhere in "
                "the preview to open the palette &mdash; except while typing in the "
                "text field, where a plain-key shortcut is ignored. "
                "<kbd>Ctrl+K</kbd> no longer opens it.</p>"
            ),
            html=_src("""
                <div class="demo-pad">
                  <p>Press <kbd>/</kbd> to search the docs.</p>
                  <label class="field">Typing here never opens the palette
                    <input type="text" value="a/b testing">
                  </label>
                </div>
                <mj-command-palette id="shortcut-palette" global-shortcut="/" placeholder="Search the docs…" label="Search documentation"></mj-command-palette>
            """),
            css=_BUTTON_CSS + _FIELD_CSS + _KBD_CSS,
            script=_src("""
                const palette = document.getElementById("shortcut-palette")
                palette.commands = [
                  { id: "install", label: "Installation", icon: "📦" },
                  { id: "routing", label: "Routing and dispatch", icon: "🧭", keywords: ["url", "path"] },
                  { id: "auth", label: "Authentication", icon: "🔐", keywords: ["login", "token"] },
                  { id: "templates", label: "Templating", icon: "🧩" }
                ]
            """),
            height=440,
        ),
        ComponentExample(
            key="async",
            title="Async search and slots",
            description=(
                "<p><code>filterFn</code> returns a Promise (a simulated directory "
                "search with 400 ms latency): the list shows <em>Loading</em> until it "
                "resolves, then <code>mj-command-palette-results</code> fires. Try a "
                "name that does not exist to see the <code>empty</code> slot; the "
                "<code>input-prefix</code> and <code>footer</code> slots are "
                "customised too.</p>"
            ),
            html=_src("""
                <div class="row demo-pad">
                  <button type="button" class="btn primary" id="open-people">Find a person</button>
                </div>
                <mj-command-palette id="people-palette" placeholder="Search people…" label="People search" debounce="200" max-results="5">
                  <span slot="input-prefix">👤</span>
                  <span slot="empty">Nobody found. Check the spelling or invite them.</span>
                  <span slot="footer" class="muted">Directory search · results from the people service</span>
                </mj-command-palette>
            """),
            css=_BUTTON_CSS + _KBD_CSS,
            script=_src("""
                const palette = document.getElementById("people-palette")
                const people = ["Ada Lovelace", "Alan Turing", "Barbara Liskov", "Edsger Dijkstra", "Grace Hopper",
                  "Katherine Johnson", "Linus Torvalds", "Margaret Hamilton", "Radia Perlman", "Tim Berners-Lee"]
                palette.commands = people.slice(0, 3).map((name) => ({ id: name, label: name, icon: "👤" }))
                palette.filterFn = (query) => new Promise((resolve) => {
                  const needle = query.toLowerCase()
                  window.setTimeout(() => {
                    resolve(people.filter((name) => name.toLowerCase().includes(needle))
                      .map((name) => ({ id: name, label: name, icon: "👤", group: "People" })))
                  }, 400)
                })
                document.getElementById("open-people").addEventListener("click", () => palette.show())
                palette.show()
            """),
            height=460,
        ),
    ],
    slots=[
        ("input-prefix", "Content before the search field (default 🔍).", "<span>⌘</span>"),
        ("footer", "Replaces the keyboard hints below the results.",
         '<span class="muted">Tip: type a question mark for help</span>'),
        ("empty", "Content shown when nothing matches; replaces `empty-message`.",
         "<span>No command found.</span>"),
    ],
    properties=[
        ("commands", "object[]. { id, label, icon?: string | Node, shortcut?, keywords?: string[], group?, disabled?, action?(command), href? }."),
        ("filterFn", "((query: string) => object[] | Promise<object[]>) | null. Replaces the built-in matching; stale answers are ignored."),
        ("open", "boolean. Reflects the `open` attribute."),
        ("query", "string (read-only). Current text of the search field."),
        ("results", "object[] (read-only). The commands currently listed."),
        ("activeItem", "object | null (read-only). The highlighted command."),
        ("recentIds", "Array<string | number> (read-only). Ids of the recently used commands, newest first."),
    ],
    methods=[
        ("show()", "Opens the palette with an empty query."),
        ("close()", "Closes the palette (reason `api`)."),
    ],
    parts=[
        ("backdrop", "The full-viewport modal surface (role dialog)."),
        ("dialog", "The palette panel."),
        ("input-wrapper", "Row with the prefix and the search field."),
        ("input-prefix", "Wrapper of the input-prefix slot."),
        ("input", "The search field (role combobox)."),
        ("results", "The result list (role listbox)."),
        ("group-header", "A group heading row."),
        ("item", "A result row (role option)."),
        ("item-icon", "Icon of a result."),
        ("item-label", "Label of a result."),
        ("item-shortcut", "Shortcut hint of a result."),
        ("empty", "The loading / no-results row."),
        ("footer", "Hint row below the results."),
    ],
    css_properties=[
        ("--mj-cp-width", "Panel width (default 38rem, never wider than the viewport minus a margin)."),
        ("--mj-cp-max-height", "Maximum height of the result list (default 60vh)."),
        ("--mj-cp-bg", "Panel background (default var(--mj-surface))."),
        ("--mj-cp-radius", "Panel radius (default var(--mj-radius-lg))."),
        ("--mj-cp-shadow", "Panel shadow (default var(--mj-elevation-3))."),
        ("--mj-cp-input-height", "Height of the search row (default 3.5rem)."),
        ("--mj-cp-item-height", "Height of a result row (default 2.5rem)."),
        ("--mj-cp-highlight-bg", "Background of the highlighted row (default var(--mj-bg-muted))."),
    ],
)


# ---------------------------------------------------------------------------
# mj-tour
# ---------------------------------------------------------------------------

_APP_CSS = _src("""
    .app-bar {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: var(--mj-space-3);
      padding: var(--mj-space-3) var(--mj-space-4);
      border-block-end: 1px solid var(--mj-border);
    }
    .app-bar .spacer { flex: 1; }
    .app-bar input {
      font: inherit;
      padding-block: var(--mj-space-1);
      padding-inline: var(--mj-space-3);
      border: 1px solid var(--mj-border-strong);
      border-radius: var(--mj-radius-md);
      background: var(--mj-surface);
      color: var(--mj-text);
    }
    .board {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(10rem, 1fr));
      gap: var(--mj-space-3);
      padding: var(--mj-space-4);
    }
    .card {
      padding: var(--mj-space-3);
      border: 1px solid var(--mj-border);
      border-radius: var(--mj-radius-md);
      background: var(--mj-surface);
    }
""")

_TOUR = ComponentDoc(
    tag="mj-tour",
    title="Tour",
    group="overlays",
    summary="Step-by-step coach marks that spotlight parts of the page.",
    description=(
        "<p><code>&lt;mj-tour&gt;</code> walks the user through a sequence of "
        "steps. Each step with a <code>targetId</code> scrolls that element into "
        "view, cuts a spotlight around it and anchors the card next to it; a step "
        "without a target shows the card centred, without a spotlight. A step whose "
        "target is not in the page is skipped (with a console warning). While the "
        "tour runs the page behind is inert, focus is trapped in the card and the "
        "card and spotlight are in the top layer; scrolling stays possible unless "
        "<code>scroll-lock</code> is set. <code>variant=\"floating\"</code> centres every card instead and "
        "dims the page evenly, ignoring the targets.</p>"
        "<p>Back / Next (Done on the last step) and the &times; (skip) button "
        "navigate, and each step focuses Next (Done); <kbd>→</kbd> / <kbd>←</kbd> (swapped in RTL) move between "
        "steps (→ does not finish the tour on the last step) and <kbd>Escape</kbd> "
        "skips. Completing or skipping is remembered in "
        "<code>localStorage</code> under <code>storage-key</code>; a remembered "
        "tour does not start again until <code>reset()</code>.</p>"
    ),
    how_to_use=(
        "<p>Add the element, assign <code>steps</code> "
        "(<code>{ title, body, targetId?, placement? }</code>; placement is a side "
        "<code>top</code>, <code>bottom</code>, <code>start</code> or "
        "<code>end</code> with an optional <code>-start</code> / <code>-end</code> "
        "alignment, default <code>bottom-start</code>) and call "
        "<code>start()</code> from a visible button, or set <code>active</code>. "
        "<code>next()</code>, <code>back()</code> and <code>skip()</code> drive it "
        "from script. The <code>step-title</code> and <code>step-body</code> slots "
        "replace the title and body of every step with fixed content; the "
        "<code>navigation</code> slot replaces Back / Next with your own buttons, "
        "which must call <code>back()</code> / <code>next()</code>; each step focuses the slotted button "
        "with <code>autofocus</code>, else the last one (put the forward button last).</p>"
    ),
    example="",
    attributes=[
        AttributeDoc(name="active", kind="boolean",
                     description="Present while the tour runs; adding it starts at `current-step` (unless storage says it was completed or skipped), removing it ends the tour without events."),
        AttributeDoc(name="current-step", kind="number", default="0",
                     description="Zero-based index of the shown step; reflects navigation and moves the tour when changed while it runs."),
        AttributeDoc(name="show-progress-dots", kind="boolean", default="true",
                     description="`false` hides the progress dots."),
        AttributeDoc(name="show-counter", kind="boolean", default="true",
                     description="`false` hides the step counter."),
        AttributeDoc(name="counter-format", kind="string", values=["{current} / {total}", "Tip {current} of {total}"],
                     description="Counter template with {current} and {total} (default \"Step {current} of {total}\")."),
        AttributeDoc(name="skip-label", kind="string", default="Skip tour", description="Accessible label of the × (skip) button."),
        AttributeDoc(name="back-label", kind="string", default="Back", description="Text of the Back button."),
        AttributeDoc(name="next-label", kind="string", default="Next", description="Text of the Next button."),
        AttributeDoc(name="done-label", kind="string", default="Done", description="Text of the Next button on the last step."),
        AttributeDoc(name="storage-key", kind="string",
                     description="localStorage key that remembers completion / skipping ({ dismissed, completed }); a remembered tour does not start."),
        AttributeDoc(name="spotlight-padding", kind="number", default="8",
                     description="Pixels of space between the target and the spotlight edge; the card keeps this plus 12px away."),
        AttributeDoc(name="spotlight", kind="boolean", default="true",
                     description="`false` hides the spotlight cut-out (the page is still inert)."),
        AttributeDoc(name="scroll-lock", kind="boolean",
                     description="Locks page scrolling while the tour runs (`scroll-lock=\"false\"` or no attribute: the page scrolls and the spotlight follows). Takes effect at once, also while the tour runs."),
        AttributeDoc(name="variant", kind="enum", values=["anchored", "floating"], default="anchored",
                     description="`anchored` places each card next to its step's target; `floating` centres every card, dims the page evenly and ignores `targetId` (no scrolling, no skipped steps)."),
    ],
    events=[
        ("mj-tour-start", "The tour started.", "{ totalSteps: number }"),
        ("mj-tour-step", "Cancelable. A step is about to be shown (also the first); preventDefault() stays on the current step.",
         "{ step: number, totalSteps: number, stepDef: object }"),
        ("mj-tour-next", "Moving forward (Next button, → key, next()); not fired by Done.",
         "{ step: number, totalSteps: number }  (the step being moved to)"),
        ("mj-tour-back", "Moving back (Back button, ← key, back()).", "{ step: number, totalSteps: number }"),
        ("mj-tour-skip", "The user skipped the tour (×, Escape, skip()).", "{ step: number }"),
        ("mj-tour-complete", "Done was activated on the last step (or next() there).", "{ totalSteps: number }"),
    ],
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p><strong>Start tour</strong> runs three steps: a centred welcome "
                "card, then the <em>New project</em> button and the search field with "
                "a spotlight. Use Next / Back, the arrow keys, or Escape to skip; the "
                "page behind is inert meanwhile. Start it again at any time.</p>"
            ),
            html=_src("""
                <button type="button" class="btn primary start-tour" id="start-tour-btn">Start tour</button>
                <header class="app-bar">
                  <strong>Projects</strong>
                  <button type="button" class="btn" id="tour-new">＋ New project</button>
                  <input id="tour-search" type="search" placeholder="Search projects" aria-label="Search projects">
                </header>
                <main class="board">
                  <div class="card">Website redesign</div>
                  <div class="card">Mobile app 2.0</div>
                  <div class="card">Customer survey</div>
                </main>
                <mj-tour id="demo-tour"></mj-tour>
            """),
            css=_BUTTON_CSS + _APP_CSS + _src("""
                .start-tour { margin: var(--mj-space-3) var(--mj-space-4) 0; }
            """),
            script=_src("""
                const tour = document.getElementById("demo-tour")
                tour.steps = [
                  { title: "Welcome to Projects", body: "This short tour shows where to start. It takes 20 seconds." },
                  { title: "Create a project", body: "Start a new project from a blank board or a template.", targetId: "tour-new", placement: "bottom-start" },
                  { title: "Find anything", body: "Search projects, cards and comments by keyword.", targetId: "tour-search", placement: "bottom" }
                ]
                document.getElementById("start-tour-btn").addEventListener("click", () => tour.start())
            """),
            height=420,
        ),
        ComponentExample(
            key="placements",
            title="Placements and spotlight",
            description=(
                "<p>Each step places the card on another side of its target "
                "(<code>bottom-end</code>, <code>top</code>, <code>end</code>, "
                "<code>start</code>); <code>spotlight-padding=\"4\"</code> hugs the "
                "targets and <code>scroll-lock</code> keeps the page still. "
                "Switch the preview to RTL: start and end swap.</p>"
            ),
            html=_src("""
                <div class="stage">
                  <div class="row"><button type="button" class="btn primary" id="start-placements">Start tour</button></div>
                  <div class="targets">
                    <div class="card" id="target-bottom">Files</div>
                    <div class="card" id="target-end">Calendar</div>
                    <div class="card" id="target-start">Settings</div>
                    <div class="card" id="target-top">Inbox</div>
                  </div>
                </div>
                <mj-tour id="placement-tour" spotlight-padding="4" scroll-lock></mj-tour>
            """),
            css=_BUTTON_CSS + _APP_CSS + _src("""
                .stage { padding: var(--mj-space-4); }
                .targets {
                  display: grid;
                  grid-template-columns: 9rem 1fr 9rem;
                  grid-template-areas: ". bottom ." "end . start" ". top .";
                  row-gap: 15rem;
                  padding-block: var(--mj-space-4);
                }
                #target-bottom { grid-area: bottom; justify-self: center; inline-size: 9rem; }
                #target-end { grid-area: end; }
                #target-start { grid-area: start; }
                #target-top { grid-area: top; justify-self: center; inline-size: 9rem; }
            """),
            script=_src("""
                const tour = document.getElementById("placement-tour")
                tour.steps = [
                  { title: "bottom-end", body: "Below, lined up with the target's end edge.", targetId: "target-bottom", placement: "bottom-end" },
                  { title: "top", body: "The card sits above the target.", targetId: "target-top", placement: "top" },
                  { title: "end", body: "Beside the target, on the inline-end side.", targetId: "target-end", placement: "end" },
                  { title: "start", body: "On the inline-start side.", targetId: "target-start", placement: "start" }
                ]
                document.getElementById("start-placements").addEventListener("click", () => tour.start())
            """),
            height=720,
        ),
        ComponentExample(
            key="storage",
            title="Remembered with storage-key",
            description=(
                "<p>With <code>storage-key</code> the tour remembers that it was "
                "completed or skipped: after that, <strong>Start</strong> does nothing "
                "(no <code>mj-tour-start</code>) until <strong>Reset</strong> calls "
                "<code>reset()</code>. The status line shows <code>isComplete</code> "
                "and <code>isDismissed</code>.</p>"
            ),
            html=_src("""
                <div class="demo-pad">
                  <div class="row">
                    <button type="button" class="btn primary" id="storage-start">Start</button>
                    <button type="button" class="btn" id="storage-reset">Reset</button>
                    <output id="storage-status" class="muted"></output>
                  </div>
                  <p id="storage-target" class="card">Billing settings moved here.</p>
                </div>
                <mj-tour id="storage-tour" storage-key="catalog-demo-tour-billing"></mj-tour>
            """),
            css=_BUTTON_CSS + _APP_CSS + _src("""
                .demo-pad { padding: var(--mj-space-4); }
                #storage-target { max-inline-size: 16rem; }
            """),
            script=_src("""
                const tour = document.getElementById("storage-tour")
                const status = document.getElementById("storage-status")
                tour.steps = [
                  { title: "Billing has moved", body: "Invoices and payment methods now live in Settings.", targetId: "storage-target", placement: "bottom-start" },
                  { title: "That's it", body: "Finish or skip, then press Start again." }
                ]
                function report() {
                  let stored = null
                  try { stored = localStorage.getItem("catalog-demo-tour-billing") } catch (error) { stored = "(storage blocked)" }
                  status.textContent = "isComplete " + tour.isComplete + " · isDismissed " + tour.isDismissed + " · stored " + stored
                }
                document.getElementById("storage-start").addEventListener("click", () => {
                  tour.start()
                  window.setTimeout(report, 0)
                })
                document.getElementById("storage-reset").addEventListener("click", () => {
                  tour.reset()
                  report()
                })
                tour.addEventListener("mj-tour-complete", report)
                tour.addEventListener("mj-tour-skip", report)
                report()
            """),
            height=380,
        ),
        ComponentExample(
            key="custom",
            title="Labels, counter and navigation slot",
            description=(
                "<p>Custom <code>next-label</code>, <code>done-label</code> and "
                "<code>counter-format</code>, no progress dots, and the "
                "<code>navigation</code> slot replacing Back / Next with buttons that "
                "call <code>back()</code> / <code>next()</code>; each step focuses the "
                "last of them (<em>Next tip</em>). Card width and "
                "spotlight colour come from <code>--mj-tour-card-width</code> and "
                "<code>--mj-tour-spotlight-color</code>.</p>"
            ),
            html=_src("""
                <header class="app-bar">
                  <strong>Mail</strong>
                  <button type="button" class="btn" id="custom-compose">Compose</button>
                  <button type="button" class="btn" id="custom-filters">Filters</button>
                  <span class="spacer"></span>
                  <button type="button" class="btn primary" id="start-custom">What's new?</button>
                </header>
                <mj-tour id="custom-tour" counter-format="Tip {current} / {total}" show-progress-dots="false" next-label="Show me" done-label="Got it">
                  <div slot="navigation" class="actions">
                    <button type="button" class="btn" id="custom-back">Previous tip</button>
                    <button type="button" class="btn primary" id="custom-next">Next tip</button>
                  </div>
                </mj-tour>
            """),
            css=_BUTTON_CSS + _FIELD_CSS + _APP_CSS + _src("""
                #custom-tour {
                  --mj-tour-card-width: 17rem;
                  --mj-tour-spotlight-color: rgba(19, 41, 61, 0.55);
                }
            """),
            script=_src("""
                const tour = document.getElementById("custom-tour")
                tour.steps = [
                  { title: "Write faster", body: "Compose now suggests recipients as you type.", targetId: "custom-compose", placement: "bottom-start" },
                  { title: "Smarter filters", body: "Filters can now match attachments and calendar invites.", targetId: "custom-filters", placement: "bottom" }
                ]
                document.getElementById("custom-back").addEventListener("click", () => tour.back())
                document.getElementById("custom-next").addEventListener("click", () => tour.next())
                document.getElementById("start-custom").addEventListener("click", () => tour.start())
            """),
            height=380,
        ),
        ComponentExample(
            key="floating",
            title="Floating variant",
            description=(
                "<p><code>variant=\"floating\"</code> centres every card and dims the "
                "page evenly: the steps' <code>targetId</code>s are ignored, so nothing "
                "scrolls and no step is skipped. Switch <code>variant</code> in Controls "
                "while the tour runs to re-anchor the card in place.</p>"
            ),
            html=_src("""
                <div class="demo-pad">
                  <div class="row"><button type="button" class="btn primary" id="start-floating">Start tour</button></div>
                  <div class="board">
                    <div class="card" id="floating-inbox">Inbox</div>
                    <div class="card" id="floating-archive">Archive</div>
                  </div>
                </div>
                <mj-tour id="floating-tour" variant="floating"></mj-tour>
            """),
            css=_BUTTON_CSS + _APP_CSS + _src("""
                .demo-pad { padding: var(--mj-space-4); }
            """),
            script=_src("""
                const tour = document.getElementById("floating-tour")
                tour.steps = [
                  { title: "Your inbox", body: "New messages arrive here.", targetId: "floating-inbox" },
                  { title: "The archive", body: "Archived messages stay searchable.", targetId: "floating-archive" }
                ]
                document.getElementById("start-floating").addEventListener("click", () => tour.start())
            """),
            height=420,
        ),
        ComponentExample(
            key="events",
            title="Events and missing targets",
            description=(
                "<p>Every tour event appears in the event log. "
                "Step 2 points at an element that does not exist, so the tour skips "
                "it (going forward and back). A <code>mj-tour-step</code> listener "
                "vetoes the last step until <em>Allow the last step</em> is ticked "
                "&mdash; tick it before starting.</p>"
            ),
            html=_src("""
                <div class="demo-pad">
                  <div class="row">
                    <button type="button" class="btn primary" id="start-events">Start tour</button>
                    <label><input type="checkbox" id="allow-last"> Allow the last step</label>
                  </div>
                  <div class="board">
                    <div class="card" id="events-a">Revenue</div>
                    <div class="card" id="events-c">Churn</div>
                  </div>
                </div>
                <mj-tour id="events-tour"></mj-tour>
            """),
            css=_BUTTON_CSS + _APP_CSS + _src("""
                .demo-pad { padding: var(--mj-space-4); }
            """),
            script=_src("""
                const tour = document.getElementById("events-tour")
                const allowLast = document.getElementById("allow-last")
                tour.steps = [
                  { title: "Revenue", body: "Monthly recurring revenue.", targetId: "events-a" },
                  { title: "Pipeline", body: "This target is missing, so the step is skipped.", targetId: "events-b" },
                  { title: "Churn", body: "Customers lost this month.", targetId: "events-c" },
                  { title: "All done", body: "Shown only when the checkbox was ticked." }
                ]
                tour.addEventListener("mj-tour-step", (event) => {
                  if (event.detail.step === 3 && allowLast.checked === false) {
                    event.preventDefault()
                    mjSandbox.log("step vetoed", { step: event.detail.step })
                  }
                })
                document.getElementById("start-events").addEventListener("click", () => tour.start())
            """),
            height=420,
        ),
    ],
    slots=[
        ("", "Light-DOM content of the element; it stays in the page flow and is not part of the card.",
         "<span>Sample content</span>"),
        ("step-title", "Replaces the title of every step with fixed content.", "<h3>Quick tour</h3>"),
        ("step-body", "Replaces the body text of every step with fixed content.",
         "<p>Use Next and Back to move between the highlighted areas.</p>"),
        ("navigation", "Replaces the Back / Next buttons; your buttons must call back() / next(). Each step focuses the slotted control with `autofocus`, else the last focusable one.",
         '<div class="actions"><button type="button" class="btn">Previous</button><button type="button" class="btn primary">Next</button></div>'),
    ],
    properties=[
        ("steps", "object[]. { title, body, targetId?, placement? }. Assigning while the tour runs re-renders it (an empty list ends it)."),
        ("active", "boolean. Reflects the `active` attribute."),
        ("totalSteps", "number (read-only). Number of steps."),
        ("isComplete", "boolean. True after the tour was completed (cleared by start() and reset())."),
        ("isDismissed", "boolean. True after the tour was skipped (cleared by start() and reset())."),
    ],
    methods=[
        ("start()", "Starts at the first step (does nothing while storage says completed / skipped); restarts at step 0 when already running."),
        ("next()", "Next step, or completes the tour on the last one."),
        ("back()", "Previous step."),
        ("skip()", "Ends the tour as skipped and remembers it under `storage-key`."),
        ("reset()", "Clears isComplete / isDismissed and the stored state."),
    ],
    parts=[
        ("spotlight", "The cut-out around the target."),
        ("popover", "Wrapper that positions the card."),
        ("card", "The coach-mark card (role dialog)."),
        ("title", "Step title."),
        ("skip-button", "The × (skip) button."),
        ("counter", "Step counter."),
        ("dots", "Progress dots row."),
        ("dot", "One progress dot (data-active marks the current step)."),
        ("body", "Step body."),
        ("navigation", "Navigation row."),
        ("back-button", "Back button."),
        ("next-button", "Next / Done button."),
    ],
    css_properties=[
        ("--mj-tour-card-width", "Card width (default 20rem)."),
        ("--mj-tour-card-padding", "Card padding (default var(--mj-space-5))."),
        ("--mj-tour-card-radius", "Card radius (default var(--mj-radius-lg))."),
        ("--mj-tour-card-shadow", "Card shadow (default var(--mj-elevation-3))."),
        ("--mj-tour-spotlight-color", "Colour of the dimmed area around the spotlight (default rgba(14, 18, 27, 0.7))."),
        ("--mj-tour-dot-size", "Progress dot size (default 8px)."),
        ("--mj-tour-dot-active-color", "Colour of the current dot (default var(--mj-accent))."),
    ],
)


COMPONENTS = [
    _DIALOG,
    _POPOVER,
    _DRAWER,
    _LIGHTBOX,
    _OVERLAY,
    _TOAST_REGION,
    _NOTIFICATION_CENTER,
    _CONTEXT_MENU,
    _COMMAND_PALETTE,
    _TOUR,
]
