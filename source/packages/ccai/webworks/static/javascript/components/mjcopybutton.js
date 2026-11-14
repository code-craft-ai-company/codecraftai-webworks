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
import { t } from "../core/intl.js";

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
:host([icon-only]) .label { display: none; }
:host([disabled]) .btn  { opacity: 0.55; cursor: not-allowed; }

/* Built-in icons, used when the matching icon slot is left empty. */
.default-icon { width: 1em; height: 1em; }

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

const ICON_ATTRIBUTES = `class="default-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"`;

const COPY_ICON_SVG = `<svg ${ICON_ATTRIBUTES}><rect x="5.5" y="5.5" width="8" height="8" rx="1.5"/><path d="M10.5 5.5v-2a1 1 0 0 0-1-1h-6a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2"/></svg>`;

const SUCCESS_ICON_SVG = `<svg ${ICON_ATTRIBUTES}><polyline points="3 8.5 6.5 12 13 4.5"/></svg>`;

const ERROR_ICON_SVG = `<svg ${ICON_ATTRIBUTES}><path d="M8 2.5 14 13H2Z"/><line x1="8" y1="6.5" x2="8" y2="9.5"/><line x1="8" y1="11.5" x2="8" y2="11.5"/></svg>`;

export class MjCopyButton extends MjElement {
  static tagName = "mj-copy-button";
  static styles = STYLES;
  static watched = ["value", "for", "variant", "size", "disabled", "icon-only", "label", "success-label", "error-label", "timeout"];

  constructor() {
    super()
    this._button = null
    this._labelSlot = null
    this._labelDefault = null
    this._labelStatus = null
    this._status = "idle"
    this._resetTimer = null
  }

  render() {
    /*
     * The label holds the default slot and, next to it, the `label` text that
     * is shown while nothing meaningful is slotted, for the idle state, and a
     * separate span for the success / error text. The `label` text is not the
     * slot's fallback content: whitespace between the tags is slotted too and
     * would suppress a fallback. No whitespace between them: the label's text
     * is read as a whole.
     */
    const markup = `
      <button class="btn" part="button" type="button">
        <span class="icon-copy" part="icon-copy" aria-hidden="true"><slot name="icon-copy">${COPY_ICON_SVG}</slot></span>
        <span class="icon-success" part="icon-success" aria-hidden="true"><slot name="icon-success">${SUCCESS_ICON_SVG}</slot></span>
        <span class="icon-error" part="icon-error" aria-hidden="true"><slot name="icon-error">${ERROR_ICON_SVG}</slot></span>
        <span class="label" part="label"><slot class="label-slot"></slot><span class="label-default"></span><span class="label-status"></span></span>
      </button>
    `
    return markup
  }

  afterRender() {
    this._button = this.$(".btn")
    this._labelSlot = this.$(".label-slot")
    this._labelDefault = this.$(".label-default")
    this._labelStatus = this.$(".label-status")
    this.listen(this._button, "click", this._onClick.bind(this))
    this.listen(this._labelSlot, "slotchange", this._syncAccessibility.bind(this))
    this._syncAccessibility()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._button === undefined || this._button === null) {
      return
    }
    this._syncAccessibility()
    return
  }

  _syncAccessibility() {
    if (this._button === undefined || this._button === null) {
      return
    }

    const disabled = this.hasAttribute("disabled")
    const idle = this._status === "idle"

    this._button.disabled = disabled

    /* Idle: the slotted label (or the `label` text). Otherwise: the status text. */
    const slotted = this._hasSlottedLabel()
    this._labelDefault.textContent = this._getIdleLabel()
    this._labelSlot.hidden = idle === false
    this._labelDefault.hidden = idle === false || slotted === true
    this._labelStatus.hidden = idle === true
    this._labelStatus.textContent = idle === true ? "" : this._getCurrentLabel()

    this._button.setAttribute("aria-label", this._getCurrentLabel())
    return
  }

  /*
   * True when the default slot holds a label: an element, or text that is
   * not only whitespace (the indentation between the tags does not count).
   */
  _hasSlottedLabel() {
    let found = false
    if (this._labelSlot !== null) {
      const nodes = this._labelSlot.assignedNodes({ flatten: true })
      for (let index = 0; index < nodes.length; index = index + 1) {
        const node = nodes[index]
        const isElement = node.nodeType === Node.ELEMENT_NODE
        const isText = node.nodeType === Node.TEXT_NODE && node.textContent.trim() !== ""
        if (isElement === true || isText === true) {
          found = true
          break
        }
      }
    }
    return found
  }

  /* Text of the nodes assigned to the default slot, trimmed. */
  _getSlottedText() {
    let text = ""
    if (this._labelSlot !== null) {
      const nodes = this._labelSlot.assignedNodes({ flatten: true })
      for (let index = 0; index < nodes.length; index = index + 1) {
        text = text + nodes[index].textContent
      }
    }
    text = text.trim()
    return text
  }

  /* The idle label: the `label` attribute, then the built-in default. */
  _getIdleLabel() {
    const label = this.getAttribute("label") || t("mj.copyButton.copy")
    return label
  }

  /*
   * The accessible name for the current status. While idle it is the
   * `label` attribute, then the slotted text, then the built-in default.
   */
  _getCurrentLabel() {
    if (this._status === "success") {
      const label = this.getAttribute("success-label") || t("mj.copyButton.copied")
      return label
    }
    if (this._status === "error") {
      const label = this.getAttribute("error-label") || t("mj.copyButton.failed")
      return label
    }

    let label = this.getAttribute("label")
    if (label === null || label === "") {
      label = this._getSlottedText()
    }
    if (label === "") {
      label = t("mj.copyButton.copy")
    }
    return label
  }

  /* The element named by `for`, looked up in the tree the button lives in. */
  _resolveSource() {
    let sourceEl = null

    const forId = this.getAttribute("for")
    if (forId !== null && forId.length > 0) {
      const root = this.getRootNode()
      if (typeof root.getElementById === "function") {
        sourceEl = root.getElementById(forId)
      }
      if (sourceEl === null) {
        sourceEl = document.getElementById(forId)
      }
    }

    return sourceEl
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

    const sourceEl = this._resolveSource()
    if (sourceEl === null) {
      console.warn("<mj-copy-button>: the `for` attribute does not resolve to an element.", this)
      return directValue
    }

    /*
     * Any control that exposes a string `value` (input, textarea, select,
     * mj-text-field, ...) is copied by value; other elements by their text.
     */
    if (typeof sourceEl.value === "string") {
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

    const clipboardAvailable =
      navigator.clipboard !== undefined &&
      navigator.clipboard !== null &&
      typeof navigator.clipboard.writeText === "function"

    if (clipboardAvailable === false) {
      /* Non-secure origins (plain http on a LAN host) have no async Clipboard API. */
      this._copyWithFallback(text, new Error("Clipboard API unavailable"))
      return
    }

    navigator.clipboard.writeText(text).then(() => {
      this._handleSuccess(text)
    }).catch((err) => {
      this._copyWithFallback(text, err)
    })
    return
  }

  /*
   * Copy through a temporary textarea and execCommand("copy"). Takes the
   * error path with `originalError` when that does not work either.
   */
  _copyWithFallback(text, originalError) {
    let copied = false

    const helper = document.createElement("textarea")
    helper.value = text
    helper.setAttribute("readonly", "")
    helper.setAttribute("aria-hidden", "true")
    helper.tabIndex = -1
    helper.style.position = "fixed"
    helper.style.insetBlockStart = "0"
    helper.style.insetInlineStart = "0"
    helper.style.opacity = "0"

    document.body.appendChild(helper)
    try {
      helper.select()
      copied = document.execCommand("copy") === true
    } catch (error) {
      copied = false
    }
    helper.remove()

    /* Selecting the helper moved focus; give it back to the button. */
    if (this._button !== null) {
      this._button.focus()
    }

    if (copied === true) {
      this._handleSuccess(text)
    } else {
      this._handleError(originalError)
    }
    return
  }

  _handleSuccess(text) {
    this._status = "success"
    this.dataset.status = "success"
    this._syncAccessibility()

    const successLabel = this.getAttribute("success-label") || t("mj.copyButton.copied")
    announce(successLabel, "polite")
    this.emit("mj-copy", { value: text })

    this._startResetTimer()
    return
  }

  _handleError(err) {
    this._status = "error"
    this.dataset.status = "error"
    this._syncAccessibility()

    const errorLabel = this.getAttribute("error-label") || t("mj.copyButton.failed")
    announce(errorLabel, "assertive")
    this.emit("mj-copy-error", { error: err })

    this._startResetTimer()
    return
  }

  _startResetTimer() {
    let timeoutMs = parseInt(this.getAttribute("timeout") || "2000", 10)
    if (Number.isFinite(timeoutMs) === false || timeoutMs < 0) {
      timeoutMs = 2000
    }

    if (this._resetTimer !== null) {
      clearTimeout(this._resetTimer)
    }
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

  /*
   * The confirmation timer cannot outlive the connection, so the status
   * returns to idle here; otherwise a button moved right after a copy would
   * show "Copied!" until it is clicked again.
   */
  onDisconnected() {
    if (this._resetTimer !== null) {
      clearTimeout(this._resetTimer)
      this._resetTimer = null
    }
    if (this._status !== "idle") {
      this._resetStatus()
    }
    return
  }

  /* ----- scriptable API ----- */

  get status() {
    return this._status
  }

  get sourceEl() {
    const found = this._resolveSource()
    return found
  }

  get disabled() {
    const value = this.hasAttribute("disabled")
    return value
  }

  set disabled(value) {
    this.reflectBoolean("disabled", Boolean(value))
    return
  }

  /*
   * Copies as a user click would (mj-copy or mj-copy-error).
   * HTMLElement.click() would only dispatch a click at the host, which never
   * reaches the inner button. Disabled / busy states are honoured by the
   * inner handler.
   */
  click() {
    if (this._button !== undefined && this._button !== null) {
      this._button.click()
    }
    return
  }

  focus(options) {
    if (this._button !== undefined && this._button !== null) {
      this._button.focus(options)
    }
    return
  }
}
