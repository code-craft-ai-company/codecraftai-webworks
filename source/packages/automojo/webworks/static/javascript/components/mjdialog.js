/*
 * mjdialog.js
 *
 * <mj-dialog> -- modal and non-modal dialog built on the native <dialog>
 * element. Provides focus trapping, backdrop via <mj-overlay>, ARIA semantics
 * for dialog/alertdialog variants, confirmation, and prompt sub-variants.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { trapFocus } from "../core/focustrap.js";

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
  overflow: hidden;
  opacity: 0;
  transform: scale(0.95);
  transition: opacity var(--mj-motion-medium) var(--mj-motion-ease),
              transform var(--mj-motion-medium) var(--mj-motion-ease);
}

dialog[open] {
  opacity: 1;
  transform: scale(1);
}

dialog::backdrop {
  display: none;
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

.footer:empty { display: none; }

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
  dialog { transition: none; }
}
`;

export class MjDialog extends MjElement {
  static tagName = "mj-dialog";
  static styles = STYLES;
  static watched = ["open", "variant", "modal", "label", "no-close-button"];

  constructor() {
    super()
    this._dialog = null
    this._overlay = null
    this._trapDispose = null
    this._titleId = nextId("mj-dialog-title")
    this._promptInput = null
    this.returnFocusEl = null
  }

  render() {
    const variant = this.getAttribute("variant") || "dialog"
    const isAlert = variant === "alertdialog" || variant === "confirmation" || variant === "prompt"
    const role = isAlert === true ? "alertdialog" : "dialog"
    const label = this.getAttribute("label") || ""
    const labelAttr = label.length > 0 ? `aria-label="${label}"` : `aria-labelledby="${this._titleId}"`
    const closeLabel = this.getAttribute("close-label") || "Close dialog"
    const confirmLabel = this.getAttribute("confirm-label") || "Confirm"
    const cancelLabel = this.getAttribute("cancel-label") || "Cancel"

    let footerHtml = ""
    if (variant === "confirmation" || variant === "prompt") {
      footerHtml = `
        <button class="action-btn" part="cancel-button" data-action="cancel">${cancelLabel}</button>
        <button class="action-btn primary" part="confirm-button" data-action="confirm">${confirmLabel}</button>
      `
    }

    let promptHtml = ""
    if (variant === "prompt") {
      promptHtml = `<input class="prompt-input" part="prompt-input" type="text" aria-label="Enter value" />`
    }

    const markup = `
      <dialog part="dialog" role="${role}" ${labelAttr} aria-modal="true">
        <div class="header" part="header">
          <slot name="header">
            <span id="${this._titleId}" class="title" part="title"><slot name="title"></slot></span>
            <button class="close-btn" part="close-button" aria-label="${closeLabel}" data-action="close">&#x2715;</button>
          </slot>
        </div>
        <div class="body" part="body">
          <slot></slot>
          ${promptHtml}
        </div>
        <div class="footer" part="footer">
          <slot name="footer">${footerHtml}</slot>
        </div>
      </dialog>
    `
    return markup
  }

  afterRender() {
    this._dialog = this.$("dialog")
    this._promptInput = this.$(".prompt-input")

    this.listen(this._dialog, "keydown", this._onKeydown.bind(this))
    this.listen(this._dialog, "click", this._onDialogClick.bind(this))

    if (this.hasAttribute("open") === true) {
      this._openDialog("api")
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "open" && this._dialog !== null) {
      if (newValue !== null) {
        this._openDialog("api")
      } else {
        this._closeDialog("api")
      }
    }
    return
  }

  onDisconnected() {
    this._cleanupTrap()
    this._hideOverlay()
    return
  }

  _openDialog(reason) {
    if (this._dialog === null) {
      return
    }
    if (this._dialog.open === true) {
      return
    }

    this.returnFocusEl = this.returnFocusEl || document.activeElement

    const isModal = this.getAttribute("modal") !== "false"
    if (isModal === true) {
      this._showOverlay()
      this._dialog.showModal()
    } else {
      this._dialog.show()
    }

    if (isModal === true) {
      this._trapDispose = trapFocus(this._dialog)
    } else {
      const focusTarget = this._dialog.querySelector("button, [tabindex]:not([tabindex='-1']), input")
      if (focusTarget !== null) {
        focusTarget.focus()
      }
    }

    this.emit("mj-dialog-open", { variant: this.getAttribute("variant") || "dialog" })
    return
  }

  _closeDialog(reason) {
    if (this._dialog === null) {
      return
    }
    if (this._dialog.open === false) {
      return
    }

    const beforeEvent = this.emit(
      "mj-dialog-before-close",
      { reason: reason },
      { cancelable: true }
    )
    if (beforeEvent === false) {
      return
    }

    this._cleanupTrap()
    this._dialog.close()
    this._hideOverlay()
    this.removeAttribute("open")

    const restoreEl = this.returnFocusEl
    this.returnFocusEl = null
    if (restoreEl !== null && typeof restoreEl.focus === "function") {
      restoreEl.focus()
    }

    this.emit("mj-dialog-close", {
      variant: this.getAttribute("variant") || "dialog",
      reason: reason
    })
    return
  }

  _cleanupTrap() {
    if (this._trapDispose !== null) {
      this._trapDispose()
      this._trapDispose = null
    }
    return
  }

  _showOverlay() {
    if (this._overlay !== null) {
      return
    }
    const overlay = document.createElement("mj-overlay")
    overlay.setAttribute("visible", "")
    overlay.setAttribute("inert-target", "body > *:not(mj-dialog):not(mj-overlay)")
    this.listen(overlay, "mj-overlay-click", this._onOverlayClick.bind(this))
    document.body.appendChild(overlay)
    this._overlay = overlay
    return
  }

  _hideOverlay() {
    if (this._overlay === null) {
      return
    }
    this._overlay.remove()
    this._overlay = null
    return
  }

  _onOverlayClick() {
    const closeOnBackdrop = this.getAttribute("close-on-backdrop") !== "false"
    if (closeOnBackdrop === true) {
      this._closeDialog("backdrop")
    }
    return
  }

  _onKeydown(event) {
    if (event.key === "Escape") {
      event.preventDefault()
      this._closeDialog("escape")
      return
    }
    if (event.key === "Enter" && this._promptInput !== null) {
      const active = this.shadowRoot.activeElement || document.activeElement
      if (active === this._promptInput) {
        this._confirmAction()
      }
    }
    return
  }

  _onDialogClick(event) {
    const btn = event.target.closest("[data-action]")
    if (btn === null) {
      return
    }
    const action = btn.getAttribute("data-action")
    if (action === "close") {
      this._closeDialog("close-button")
    } else if (action === "confirm") {
      this._confirmAction()
    } else if (action === "cancel") {
      this.emit("mj-dialog-cancel", {})
      this._closeDialog("api")
    }
    return
  }

  _confirmAction() {
    const variant = this.getAttribute("variant") || "dialog"
    let value = true
    if (variant === "prompt" && this._promptInput !== null) {
      value = this._promptInput.value
    }
    this.emit("mj-dialog-confirm", { value: value })
    this._closeDialog("api")
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
    this._closeDialog("api")
    return
  }
}
