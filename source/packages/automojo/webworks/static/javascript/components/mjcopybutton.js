/*
 * mjcopybutton.js
 *
 * <mj-copy-button> -- copies text to the system clipboard using the async
 * Clipboard API, with transient visual and accessible confirmation of success
 * or failure.
 *
 * Text source resolution order: `value` attribute → textContent/value of the
 * element identified by `for` attribute → empty string (no-op with a warning).
 */

import { MjElement } from "../core/mjelement.js";
import { announce } from "../core/announcer.js";

const STYLES = `
:host {
  display: inline-block;
  vertical-align: middle;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--mj-space-2);
  min-height: var(--mj-copy-button-height, var(--mj-control-height-md));
  min-width: var(--mj-target-min);
  padding: 0 var(--mj-space-4);
  font: inherit;
  font-weight: var(--mj-font-weight-medium);
  line-height: 1;
  color: var(--mj-copy-button-color, var(--mj-text));
  background: var(--mj-copy-button-bg, transparent);
  border: 1px solid transparent;
  border-radius: var(--mj-copy-button-border-radius, var(--mj-radius-md));
  cursor: pointer;
  user-select: none;
  transition: background var(--mj-copy-button-transition, var(--mj-motion-fast)) var(--mj-motion-ease),
              color var(--mj-copy-button-transition, var(--mj-motion-fast)) var(--mj-motion-ease);
}
.btn:hover { background: var(--mj-bg-muted); }
.btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-copy-button-focus-ring-color, var(--mj-focus-ring));
  outline-offset: var(--mj-focus-ring-offset);
}

/* Variants */
:host([variant="primary"]) .btn { color: var(--mj-text-on-accent); background: var(--mj-accent); border-color: var(--mj-accent); }
:host([variant="primary"]) .btn:hover { background: var(--mj-accent-hover); border-color: var(--mj-accent-hover); }
:host([variant="secondary"]) .btn { background: var(--mj-surface); border-color: var(--mj-border-strong); }
:host([variant="secondary"]) .btn:hover { background: var(--mj-bg-muted); }

/* Status states */
:host([data-status="success"]) .btn { color: var(--mj-copy-button-color-success, var(--mj-color-success)); background: var(--mj-copy-button-bg-success, var(--mj-color-success-surface)); }
:host([data-status="error"]) .btn   { color: var(--mj-copy-button-color-error, var(--mj-color-danger));  background: var(--mj-copy-button-bg-error,   var(--mj-color-danger-surface)); }

/* Sizes */
:host([size="sm"]) .btn { min-height: var(--mj-control-height-sm); padding: 0 var(--mj-space-3); font-size: var(--mj-font-size-sm); }
:host([size="lg"]) .btn { min-height: var(--mj-control-height-lg); padding: 0 var(--mj-space-5); font-size: var(--mj-font-size-lg); }

:host([icon-only]) .btn { padding: 0; aspect-ratio: 1; }
:host([disabled]) .btn  { opacity: 0.55; cursor: not-allowed; }

/* Icon visibility by status */
.icon-copy    { display: inline-flex; }
.icon-success { display: none; }
.icon-error   { display: none; }
:host([data-status="success"]) .icon-copy    { display: none; }
:host([data-status="success"]) .icon-success { display: inline-flex; }
:host([data-status="error"])   .icon-copy    { display: none; }
:host([data-status="error"])   .icon-error   { display: inline-flex; }

@media (prefers-reduced-motion: reduce) {
  .btn { transition: none; }
}
`;

export class MjCopyButton extends MjElement {
  static tagName = "mj-copy-button";
  static styles = STYLES;
  static watched = ["value", "for", "variant", "size", "disabled", "icon-only", "label", "success-label", "error-label", "timeout"];

  constructor() {
    super()
    this._button = null
    this._labelEl = null
    this._status = "idle"
    this._resetTimer = null
  }

  render() {
    const markup = `
      <button class="btn" part="button" type="button">
        <span class="icon-copy" part="icon-copy" aria-hidden="true"><slot name="icon-copy"></slot></span>
        <span class="icon-success" part="icon-success" aria-hidden="true"><slot name="icon-success"></slot></span>
        <span class="icon-error" part="icon-error" aria-hidden="true"><slot name="icon-error"></slot></span>
        <span class="label" part="label"></span>
      </button>
    `
    return markup
  }

  afterRender() {
    this._button = this.$(".btn")
    this._labelEl = this.$(".label")
    this.listen(this._button, "click", this._onClick.bind(this))
    this._syncAccessibility()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._button !== null) {
      this._syncAccessibility()
    }
    return
  }

  _syncAccessibility() {
    const disabled = this.hasAttribute("disabled")
    const iconOnly = this.hasAttribute("icon-only")
    const currentLabel = this._getCurrentLabel()

    this._button.disabled = disabled

    if (this._labelEl !== null) {
      if (iconOnly === true) {
        this._labelEl.textContent = ""
        this._labelEl.style.display = "none"
      } else {
        this._labelEl.textContent = currentLabel
        this._labelEl.style.display = ""
      }
    }

    this._button.setAttribute("aria-label", currentLabel)
    return
  }

  _getCurrentLabel() {
    if (this._status === "success") {
      const label = this.getAttribute("success-label") || "Copied!"
      return label
    }
    if (this._status === "error") {
      const label = this.getAttribute("error-label") || "Copy failed"
      return label
    }
    const label = this.getAttribute("label") || "Copy"
    return label
  }

  _resolveValue() {
    const directValue = this.getAttribute("value")
    if (directValue !== null) {
      return directValue
    }

    const forId = this.getAttribute("for")
    if (forId === null || forId.length === 0) {
      console.warn("<mj-copy-button>: neither value nor for attribute is set; copy is a no-op.")
      return null
    }

    const sourceEl = document.getElementById(forId)
    if (sourceEl === null) {
      console.warn(`<mj-copy-button>: for="${forId}" does not resolve to a document element.`)
      return directValue
    }

    const isInput = sourceEl.tagName === "INPUT" || sourceEl.tagName === "TEXTAREA"
    if (isInput === true) {
      return sourceEl.value
    }
    return sourceEl.textContent
  }

  _onClick(event) {
    const blocked = this.hasAttribute("disabled")
    if (blocked === true) {
      event.stopImmediatePropagation()
      event.preventDefault()
      return
    }

    if (this._resetTimer !== null) {
      clearTimeout(this._resetTimer)
      this._resetTimer = null
    }

    const text = this._resolveValue()
    if (text === null) {
      return
    }

    if (navigator.clipboard === undefined || navigator.clipboard === null) {
      this._handleError(new Error("Clipboard API unavailable"))
      return
    }

    navigator.clipboard.writeText(text).then(() => {
      this._handleSuccess(text)
    }).catch((err) => {
      this._handleError(err)
    })
    return
  }

  _handleSuccess(text) {
    this._status = "success"
    this.dataset.status = "success"
    this._syncAccessibility()

    const successLabel = this.getAttribute("success-label") || "Copied!"
    announce(successLabel, "polite")
    this.emit("mj-copy", { value: text })

    const timeoutMs = parseInt(this.getAttribute("timeout") || "2000", 10)
    this._resetTimer = setTimeout(() => {
      this._resetStatus()
    }, timeoutMs)
    return
  }

  _handleError(err) {
    this._status = "error"
    this.dataset.status = "error"
    this._syncAccessibility()

    const errorLabel = this.getAttribute("error-label") || "Copy failed"
    announce(errorLabel, "assertive")
    this.emit("mj-copy-error", { error: err })

    const timeoutMs = parseInt(this.getAttribute("timeout") || "2000", 10)
    this._resetTimer = setTimeout(() => {
      this._resetStatus()
    }, timeoutMs)
    return
  }

  _resetStatus() {
    this._status = "idle"
    delete this.dataset.status
    this._resetTimer = null
    this._syncAccessibility()
    return
  }

  onDisconnected() {
    if (this._resetTimer !== null) {
      clearTimeout(this._resetTimer)
      this._resetTimer = null
    }
    return
  }

  /* ----- scriptable API ----- */

  get status() {
    return this._status
  }

  get sourceEl() {
    const forId = this.getAttribute("for")
    if (forId === null || forId.length === 0) {
      return null
    }
    const found = document.getElementById(forId)
    return found
  }

  get disabled() {
    const value = this.hasAttribute("disabled")
    return value
  }

  set disabled(value) {
    this.reflectBoolean("disabled", value === true)
    return
  }

  focus() {
    this._button.focus()
    return
  }
}
