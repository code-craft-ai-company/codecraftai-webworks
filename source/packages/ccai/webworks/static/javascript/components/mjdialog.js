/*
 * mjdialog.js
 *
 * <mj-dialog> -- modal and non-modal dialog built on the native <dialog>
 * element. A modal dialog opens with showModal(): the browser puts it in the
 * top layer, makes the rest of the page inert and paints the ::backdrop
 * scrim. The component adds focus placement and wrapping, ordered Escape
 * handling, backdrop-click dismissal, scroll lock (through <mj-overlay>),
 * ARIA semantics for the dialog/alertdialog variants, and the confirmation
 * and prompt sub-variants.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { html } from "../core/html.js";
import { t } from "../core/intl.js";
import { trapFocus, getFocusable, deepActiveElement } from "../core/focustrap.js";
import { pushLayer, removeLayer, claimEscape, noteTopLayerChange } from "../core/overlay.js";

const STYLES = `
:host {
  display: contents;
}

dialog {
  position: fixed;
  inset: 0;
  margin: auto;
  padding: 0;
  width: min(var(--mj-dialog-width, 32rem), calc(100vw - var(--mj-space-6)));
  max-height: calc(100dvh - var(--mj-space-8));
  display: flex;
  flex-direction: column;
  background: var(--mj-surface);
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-dialog-radius, var(--mj-radius-lg));
  box-shadow: var(--mj-dialog-shadow, var(--mj-elevation-3));
  color: var(--mj-text);
  z-index: var(--mj-layer-modal);
  overflow: visible;
}

/*
 * A closed dialog must not exist for layout, hit testing, focus or
 * assistive technology. (An author "display" would otherwise override the
 * browser's own dialog:not([open]) rule.)
 */
dialog:not([open]) {
  display: none;
}

/*
 * The open dialog keeps NO transform once the entry animation has ended: a
 * transformed dialog would become the containing block of position: fixed
 * popups (select, date picker, tooltip) opened inside it.
 */
dialog[open] {
  animation: mj-dialog-in var(--mj-motion-medium) var(--mj-motion-ease);
}

dialog::backdrop {
  background: var(--mj-overlay-scrim, rgba(20, 24, 31, 0.55));
  animation: mj-dialog-fade var(--mj-motion-medium) var(--mj-motion-ease);
}

@keyframes mj-dialog-in {
  from { opacity: 0; transform: scale(0.95); }
  to   { opacity: 1; transform: none; }
}

@keyframes mj-dialog-fade {
  from { opacity: 0; }
  to   { opacity: 1; }
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--mj-space-4) var(--mj-dialog-padding, var(--mj-space-6));
  border-bottom: 1px solid var(--mj-border);
  flex-shrink: 0;
}

.title {
  font-size: var(--mj-font-size-lg);
  font-weight: var(--mj-font-weight-bold);
  margin: 0;
  flex: 1;
}

.close-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  padding: 0;
  background: transparent;
  border: none;
  border-radius: var(--mj-radius-md);
  cursor: pointer;
  color: var(--mj-text-muted);
  flex-shrink: 0;
  font-size: var(--mj-font-size-lg);
  line-height: 1;
}

.close-btn:hover { background: var(--mj-bg-muted); color: var(--mj-text); }
.close-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

:host([no-close-button]) .close-btn { display: none; }

.body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: var(--mj-dialog-padding, var(--mj-space-6));
}

.footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--mj-space-3);
  padding: var(--mj-space-4) var(--mj-dialog-padding, var(--mj-space-6));
  border-top: 1px solid var(--mj-border);
  flex-shrink: 0;
}

.footer[hidden] { display: none; }

.prompt-input {
  width: 100%;
  padding: var(--mj-space-2) var(--mj-space-3);
  font: inherit;
  font-size: var(--mj-font-size-md);
  border: 1px solid var(--mj-border-strong);
  border-radius: var(--mj-radius-md);
  background: var(--mj-surface);
  color: var(--mj-text);
  margin-top: var(--mj-space-3);
  box-sizing: border-box;
}

.prompt-input[hidden] { display: none; }

.prompt-input:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

.action-btn {
  padding: var(--mj-space-2) var(--mj-space-5);
  font: inherit;
  font-weight: var(--mj-font-weight-medium);
  border-radius: var(--mj-radius-md);
  border: 1px solid var(--mj-border-strong);
  cursor: pointer;
  background: var(--mj-surface);
  color: var(--mj-text);
}

.action-btn[hidden] { display: none; }

.action-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}

.action-btn.primary {
  background: var(--mj-accent);
  border-color: var(--mj-accent);
  color: var(--mj-text-on-accent);
}

.action-btn.primary:hover { background: var(--mj-accent-hover); border-color: var(--mj-accent-hover); }

@media (prefers-reduced-motion: reduce) {
  dialog[open], dialog::backdrop { animation: none; }
}
`;

export class MjDialog extends MjElement {
  static tagName = "mj-dialog";
  static styles = STYLES;
  static watched = [
    "open", "variant", "modal", "label", "no-close-button",
    "close-label", "confirm-label", "cancel-label", "prompt-label"
  ];

  constructor() {
    super()
    this._dialog = null
    this._overlay = null
    this._layer = null
    this._trapDispose = null
    this._titleId = nextId("mj-dialog-title")
    this._promptInput = null
    this._footer = null
    this._closeBtn = null
    this._cancelBtn = null
    this._confirmBtn = null

    /* True from a successful open until the close has completed. */
    this._isOpen = false

    /* How the dialog is currently open: true after showModal(). */
    this._openedModal = false

    /* True while a pointer press that began on the backdrop is in progress. */
    this._backdropPress = false

    /* True for the rest of the task after Escape was pressed in the dialog. */
    this._escapeKeySeen = false

    this.returnFocusEl = null
  }

  render() {
    const markup = html`
      <dialog part="dialog" role="dialog">
        <div class="header" part="header">
          <slot name="header">
            <span id="${this._titleId}" class="title" part="title"><slot name="title"></slot></span>
            <button class="close-btn" part="close-button" type="button" data-action="close"><slot name="close-icon">&#x2715;</slot></button>
          </slot>
        </div>
        <div class="body" part="body">
          <slot></slot>
          <input class="prompt-input" part="prompt-input" type="text" hidden />
        </div>
        <div class="footer" part="footer">
          <slot name="footer">
            <button class="action-btn" part="cancel-button" type="button" data-action="cancel" hidden></button>
            <button class="action-btn primary" part="confirm-button" type="button" data-action="confirm" hidden></button>
          </slot>
        </div>
      </dialog>
    `
    return markup
  }

  afterRender() {
    this._dialog = this.$("dialog")
    this._promptInput = this.$(".prompt-input")
    this._footer = this.$(".footer")
    this._closeBtn = this.$(".close-btn")
    this._cancelBtn = this.$("[data-action='cancel']")
    this._confirmBtn = this.$("[data-action='confirm']")

    this.listen(this._dialog, "keydown", this._onKeydownCapture.bind(this), true)
    this.listen(this._dialog, "keydown", this._onKeydown.bind(this))
    this.listen(this._dialog, "click", this._onDialogClick.bind(this))
    this.listen(this._dialog, "pointerdown", this._onDialogPointerdown.bind(this))
    this.listen(this._dialog, "cancel", this._onNativeCancel.bind(this))
    this.listen(this._dialog, "close", this._onNativeClose.bind(this))

    const footerSlot = this.$("slot[name='footer']")
    this.listen(footerSlot, "slotchange", this._syncFooter.bind(this))

    this._applyLabels()
    this._applyVariant()

    if (this.hasAttribute("open") === true) {
      this._openDialog()
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._dialog === undefined || this._dialog === null) {
      return
    }

    if (name === "open") {
      if (newValue !== null) {
        this._openDialog()
      } else if (this._isOpen === true) {
        const closed = this._closeDialog("api", false)
        if (closed === false) {
          /* The close was vetoed: the attribute must keep matching reality. */
          this.setAttribute("open", "")
        }
      }
    } else if (name === "variant") {
      this._applyVariant()
    } else if (name === "modal") {
      this._applyModalMode()
    } else if (name === "label" || name === "close-label" || name === "confirm-label" ||
               name === "cancel-label" || name === "prompt-label") {
      this._applyLabels()
    }
    return
  }

  onDisconnected() {
    /* Removed while open: release everything without events or refocus. */
    if (this._isOpen === true) {
      this._leaveOpenState()
      this._isOpen = false
    }
    return
  }

  _variant() {
    const variant = this.getAttribute("variant") || "dialog"
    return variant
  }

  /* ----- attribute-driven rendering ----- */

  _applyLabels() {
    const label = this.getAttribute("label") || ""
    if (label.length > 0) {
      this._dialog.setAttribute("aria-label", label)
      this._dialog.removeAttribute("aria-labelledby")
    } else {
      this._dialog.removeAttribute("aria-label")
      this._dialog.setAttribute("aria-labelledby", this._titleId)
    }

    this._closeBtn.setAttribute("aria-label", this.getAttribute("close-label") || t("mj.dialog.close"))
    this._cancelBtn.textContent = this.getAttribute("cancel-label") || t("mj.dialog.cancel")
    this._confirmBtn.textContent = this.getAttribute("confirm-label") || t("mj.dialog.confirm")
    this._promptInput.setAttribute("aria-label", this.getAttribute("prompt-label") || t("mj.dialog.promptLabel"))
    return
  }

  _applyVariant() {
    const variant = this._variant()
    const isAlert = variant === "alertdialog" || variant === "confirmation" || variant === "prompt"
    const hasActions = variant === "confirmation" || variant === "prompt"

    this._dialog.setAttribute("role", isAlert === true ? "alertdialog" : "dialog")
    this._cancelBtn.hidden = hasActions === false
    this._confirmBtn.hidden = hasActions === false
    this._promptInput.hidden = variant !== "prompt"
    this._syncFooter()
    return
  }

  /* The footer bar shows only when it has built-in or slotted actions. */
  _syncFooter() {
    const variant = this._variant()
    const hasActions = variant === "confirmation" || variant === "prompt"
    const footerSlot = this.$("slot[name='footer']")
    const hasSlotted = footerSlot !== null && footerSlot.assignedNodes().length > 0
    this._footer.hidden = hasActions === false && hasSlotted === false
    return
  }

  /* `modal` changed while open: switch between showModal() and show(). */
  _applyModalMode() {
    if (this._isOpen === false) {
      return
    }
    const wantsModal = this.getAttribute("modal") !== "false"
    if (wantsModal !== this._openedModal) {
      this._leaveOpenState()
      this._enterOpenState()
    }
    return
  }

  /* ----- open / close ----- */

  _openDialog() {
    if (this._dialog === null || this._isOpen === true || this.isConnected === false) {
      return
    }

    if (this.returnFocusEl === null) {
      this.returnFocusEl = this._resolveReturnFocus()
    }

    this._isOpen = true
    this._enterOpenState()

    this.emit("mj-dialog-open", { variant: this._variant() })
    return
  }

  _resolveReturnFocus() {
    let target = null

    const returnId = this.getAttribute("return-focus-id")
    if (returnId !== null && returnId.length > 0) {
      target = document.getElementById(returnId)
    }
    if (target === null) {
      target = deepActiveElement()
    }
    return target
  }

  /*
   * Where focus goes on open: an element the author marked `autofocus`,
   * the prompt input, the primary action of an alert/confirmation dialog,
   * and otherwise (null) the first focusable element in the dialog.
   */
  _initialFocusTarget() {
    const variant = this._variant()
    let target = this.querySelector("[autofocus]")

    if (target === null && variant === "prompt") {
      target = this._promptInput
    }

    const wantsAction = variant === "confirmation" || variant === "alertdialog"
    if (target === null && wantsAction === true) {
      /* The built-in Confirm button, or the last (primary) slotted action. */
      const actions = getFocusable(this._footer)
      if (actions.includes(this._confirmBtn) === true) {
        target = this._confirmBtn
      } else if (actions.length > 0) {
        target = actions[actions.length - 1]
      }
    }

    return target
  }

  _enterOpenState() {
    const modal = this.getAttribute("modal") !== "false"
    this._openedModal = modal

    const onEscape = () => {
      this._dismiss("escape")
    }

    if (modal === true) {
      this._showOverlay()
      this._dialog.showModal()
      noteTopLayerChange()

      /* Only a dialog that really is modal may say the page is unavailable. */
      this._dialog.setAttribute("aria-modal", "true")
      this._layer = pushLayer({ surface: this._dialog, modal: true, onEscape: onEscape })
      this._trapDispose = trapFocus(this._dialog, this._initialFocusTarget(), { contain: true })
    } else {
      /* Beside the page: Escape closes it only while focus is inside. */
      this._dialog.show()
      this._dialog.removeAttribute("aria-modal")
      this._layer = pushLayer({ surface: this._dialog, modal: false })

      const target = this._initialFocusTarget() || getFocusable(this._dialog)[0] || null
      if (target !== null) {
        target.focus()
      }
    }
    return
  }

  _leaveOpenState() {
    if (this._layer !== null) {
      removeLayer(this._layer)
      this._layer = null
    }

    if (this._trapDispose !== null) {
      /* Focus is restored by the caller, once nothing is inert any more. */
      this._trapDispose({ restoreFocus: false })
      this._trapDispose = null
    }

    if (this._dialog !== null) {
      if (this._dialog.open === true) {
        this._dialog.close()
      }
      this._dialog.removeAttribute("aria-modal")
    }

    this._hideOverlay()
    return
  }

  /*
   * Close the dialog. Returns true when it closed and false when it was not
   * open or a `mj-dialog-before-close` listener vetoed the close.
   * `dismissed` marks a close the user asked for without confirming, which
   * also emits `mj-dialog-cancel`.
   */
  _closeDialog(reason, dismissed) {
    if (this._dialog === null || this._isOpen === false) {
      return false
    }

    const proceed = this.emit(
      "mj-dialog-before-close",
      { reason: reason },
      { cancelable: true }
    )
    if (proceed === false) {
      return false
    }

    this._completeClose(reason, dismissed)
    return true
  }

  _completeClose(reason, dismissed) {
    this._isOpen = false
    this._leaveOpenState()

    if (this.hasAttribute("open") === true) {
      this.removeAttribute("open")
    }

    const restoreEl = this.returnFocusEl
    this.returnFocusEl = null
    if (restoreEl !== null && restoreEl.isConnected === true && typeof restoreEl.focus === "function") {
      restoreEl.focus()
    }

    if (dismissed === true) {
      this.emit("mj-dialog-cancel", { reason: reason })
    }

    this.emit("mj-dialog-close", {
      variant: this._variant(),
      reason: reason
    })
    return
  }

  /* Escape, the close button, the backdrop and Cancel all dismiss. */
  _dismiss(reason) {
    const closed = this._closeDialog(reason, true)
    return closed
  }

  /*
   * The backdrop is the native ::backdrop, so <mj-overlay> has nothing to
   * paint or block here; it only contributes the shared scroll lock.
   */
  _showOverlay() {
    if (this._overlay !== null) {
      return
    }
    const overlay = document.createElement("mj-overlay")
    overlay.setAttribute("variant", "transparent")
    overlay.setAttribute("inert-target", "none")
    overlay.setAttribute("visible", "")
    document.body.appendChild(overlay)
    this._overlay = overlay
    return
  }

  /*
   * retire() releases inert and the scroll lock at once (so focus can be
   * restored right after) and removes the element when its fade has ended.
   */
  _hideOverlay() {
    if (this._overlay === null) {
      return
    }
    const overlay = this._overlay
    this._overlay = null
    if (typeof overlay.retire === "function") {
      overlay.retire()
    } else {
      overlay.remove()
    }
    return
  }

  /* ----- events ----- */

  /*
   * Runs before any handler inside the dialog. It only records that this
   * Escape came from the keyboard, so the native `cancel` request that may
   * follow is not mistaken for a platform close gesture.
   */
  _onKeydownCapture(event) {
    if (event.key === "Escape") {
      this._escapeKeySeen = true
      window.setTimeout(() => {
        this._escapeKeySeen = false
      }, 0)
    }
    return
  }

  _onKeydown(event) {
    if (event.key === "Escape") {
      /*
       * One Escape closes one thing. If the key belongs to a popup open
       * inside the dialog, or to a layer above it, that one closes and the
       * dialog stays. Either way the native close request is suppressed.
       */
      const mine = claimEscape(event, this._layer)
      event.preventDefault()
      if (mine === true) {
        this._dismiss("escape")
      }
      return
    }

    if (event.key === "Enter" && this._variant() === "prompt") {
      const active = this.shadowRoot.activeElement
      if (active === this._promptInput) {
        event.preventDefault()
        this._confirmAction()
      }
    }
    return
  }

  /*
   * The browser asks to close the modal dialog (Escape that no key handler
   * consumed, the Android back gesture, a close watcher). Closing always
   * goes through the component so the veto, focus restore and events apply.
   */
  _onNativeCancel(event) {
    event.preventDefault()
    if (this._escapeKeySeen === false && this._isOpen === true) {
      this._dismiss("escape")
    }
    return
  }

  /*
   * The browser closed the dialog by itself (a close request that could not
   * be cancelled). Catch up: release the scroll lock, the focus trap and the
   * `open` attribute, and tell listeners.
   */
  _onNativeClose() {
    if (this._isOpen === true && this._dialog.open === false) {
      this._completeClose("escape", true)
    }
    return
  }

  _isOutsideDialogBox(event) {
    const rect = this._dialog.getBoundingClientRect()
    const outside = event.clientX < rect.left || event.clientX > rect.right ||
      event.clientY < rect.top || event.clientY > rect.bottom
    return outside
  }

  _onDialogPointerdown(event) {
    /* A press on ::backdrop is dispatched to the <dialog> element itself. */
    this._backdropPress = event.target === this._dialog && this._isOutsideDialogBox(event) === true
    return
  }

  _onDialogClick(event) {
    if (event.target === this._dialog) {
      /*
       * Backdrop click: the press began and ended outside the dialog box (a
       * text selection dragged out of the dialog must not close it).
       */
      const onBackdrop = this._backdropPress === true && this._isOutsideDialogBox(event) === true
      this._backdropPress = false
      if (onBackdrop === true && this._openedModal === true && this.getAttribute("close-on-backdrop") !== "false") {
        this._dismiss("backdrop")
      }
      return
    }

    /* Only the dialog's own buttons: slotted content keeps its attributes. */
    const btn = event.target.closest("[data-action]")
    if (btn === null || btn.getRootNode() !== this.shadowRoot) {
      return
    }
    const action = btn.getAttribute("data-action")
    if (action === "close") {
      this._dismiss("close-button")
    } else if (action === "confirm") {
      this._confirmAction()
    } else if (action === "cancel") {
      this._dismiss("cancel")
    }
    return
  }

  /*
   * The built-in Confirm button, or Enter in the prompt field: announce the
   * value, then close with reason `confirm` (the built-in Cancel button
   * closes with reason `cancel`; only close() and the `open` attribute use
   * `api`).
   */
  _confirmAction() {
    const variant = this._variant()
    let value = true
    if (variant === "prompt" && this._promptInput !== null) {
      value = this._promptInput.value
    }
    this.emit("mj-dialog-confirm", { value: value })
    this._closeDialog("confirm", false)
    return
  }

  /* Scriptable API */

  get open() {
    return this.hasAttribute("open")
  }

  set open(value) {
    this.reflectBoolean("open", value === true)
    return
  }

  get promptValue() {
    const value = this._promptInput !== null ? this._promptInput.value : ""
    return value
  }

  get nativeDialog() {
    return this._dialog
  }

  show() {
    this.setAttribute("modal", "false")
    this.setAttribute("open", "")
    return
  }

  showModal() {
    this.removeAttribute("modal")
    this.setAttribute("open", "")
    return
  }

  close() {
    this._closeDialog("api", false)
    return
  }
}
