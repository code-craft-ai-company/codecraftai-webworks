/*
 * mjtextarea.js
 *
 * <mj-textarea> -- multi-line text entry with optional auto-grow,
 * configurable min/max rows, and character/word counter.
 *
 * Value model: `this._value` (owned by FormControlMixin) is the single source
 * of truth; the `value` attribute is the default value and the shadow
 * <textarea> is rebuilt from `this._value` on every render.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { FormControlMixin } from "../core/forminternals.js";
import { html } from "../core/html.js";
import { t } from "../core/intl.js";

const STYLES = `
:host {
  display: block;
  font-family: var(--mj-font-sans);
  font-size: var(--mj-font-size-md);
}

.label {
  display: block;
  margin-bottom: var(--mj-space-1);
  font-size: var(--mj-font-size-sm);
  font-weight: var(--mj-font-weight-medium);
  color: var(--mj-text);
}
.label:empty { display: none; }
.label[data-required]::after {
  content: " *";
  color: var(--mj-color-danger);
}

.wrapper {
  display: block;
  background: var(--mj-surface);
  border: 1px solid var(--mj-border-strong);
  border-radius: var(--mj-radius-md);
  transition: border-color var(--mj-motion-fast) var(--mj-motion-ease);
}
.wrapper:focus-within {
  border-color: var(--mj-accent);
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
.wrapper[data-invalid] { border-color: var(--mj-color-danger); }

textarea {
  display: block;
  width: 100%;
  box-sizing: border-box;
  padding: var(--mj-space-2) var(--mj-space-3);
  font: inherit;
  font-size: var(--mj-font-size-md);
  color: var(--mj-text);
  background: transparent;
  border: none;
  outline: none;
  resize: vertical;
  line-height: var(--mj-line-height);
}
:host([size="sm"]) textarea { font-size: var(--mj-font-size-sm); }
:host([size="lg"]) textarea { font-size: var(--mj-font-size-lg); }
textarea::placeholder { color: var(--mj-text-muted); }
textarea[data-no-resize] { resize: none; }
textarea[data-auto-grow] { resize: none; }

.footer-slot { padding: 0 var(--mj-space-3) var(--mj-space-2); }

.below {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--mj-space-2);
  margin-top: var(--mj-space-1);
}
.help { font-size: var(--mj-font-size-sm); color: var(--mj-text-muted); }
.help:empty { display: none; }
.error { font-size: var(--mj-font-size-sm); color: var(--mj-color-danger); display: none; }
.error[data-visible] { display: block; }
.counter { font-size: var(--mj-font-size-xs); color: var(--mj-text-muted); text-align: end; flex-shrink: 0; }
.counter[hidden] { display: none; }
.counter[data-near-limit] { color: var(--mj-color-warning); }

:host([disabled]) .wrapper, .wrapper[data-disabled] { opacity: 0.55; pointer-events: none; }
`;

/* Line height assumed when the computed value is the keyword `normal`. */
const FALLBACK_LINE_HEIGHT_PX = 20;

/* The counter turns to its warning colour at this share of `maxlength`. */
const NEAR_LIMIT_RATIO = 0.9;

/*
 * The accessible name the page gave the host: `aria-labelledby`, then
 * `aria-label`, then an associated <label for> / wrapping <label>, then an
 * <mj-label for>. The shadow control cannot see any of these across the
 * shadow boundary, so the component copies the text onto it.
 */
function resolveHostLabel(host, internals) {
  let name = ""
  const root = host.getRootNode()

  const labelledBy = host.getAttribute("aria-labelledby") || ""
  if (labelledBy.trim().length > 0 && typeof root.getElementById === "function") {
    const parts = []
    const ids = labelledBy.trim().split(/\s+/)
    for (let index = 0; index < ids.length; index = index + 1) {
      const labelNode = root.getElementById(ids[index])
      if (labelNode !== null) {
        parts.push(labelNode.textContent.trim())
      }
    }
    name = parts.join(" ").trim()
  }

  if (name.length === 0) {
    name = (host.getAttribute("aria-label") || "").trim()
  }

  if (name.length === 0 && internals !== null && internals !== undefined && internals.labels !== undefined) {
    const parts = []
    for (let index = 0; index < internals.labels.length; index = index + 1) {
      parts.push(internals.labels[index].textContent.trim())
    }
    name = parts.join(" ").trim()
  }

  if (name.length === 0 && host.id.length > 0 && typeof root.querySelector === "function") {
    const mjLabel = root.querySelector(`mj-label[for="${CSS.escape(host.id)}"]`)
    if (mjLabel !== null) {
      name = mjLabel.textContent.trim()
    }
  }

  return name
}

function countWords(text) {
  const words = text.match(/\S+/g)
  const count = words !== null ? words.length : 0
  return count
}

export class MjTextarea extends FormControlMixin(MjElement) {
  static tagName = "mj-textarea";
  static styles = STYLES;
  static watched = [
    "label", "placeholder", "help-text", "error-message", "value",
    "rows", "min-rows", "max-rows", "auto-grow", "no-resize",
    "maxlength", "minlength", "count-words", "required", "disabled",
    "readonly", "spellcheck", "autocomplete", "wrap", "size",
    "aria-label", "aria-labelledby"
  ];

  constructor() {
    super()
    this._initFormControl()

    /* Value at the last mj-change, used to suppress no-op change events. */
    this._committedValue = ""

    /* The `value` attribute text most recently applied to the control. */
    this._appliedValueAttribute = null

    /* True while an ancestor <fieldset disabled> disables the control. */
    this._formDisabled = false

    /* Errors are shown once the user has left the field or a submit failed. */
    this._showErrors = false

    this._textareaId = nextId("mjta-ta")
    this._helpId = nextId("mjta-help")
    this._errorId = nextId("mjta-error")
    this._counterId = nextId("mjta-counter")
  }

  render() {
    const markup = html`
      <label class="label" part="label" for="${this._textareaId}"></label>
      <div class="wrapper" part="wrapper">
        <textarea
          part="textarea"
          id="${this._textareaId}"
          rows="3"
        ></textarea>
        <div class="footer-slot"><slot name="footer"></slot></div>
      </div>
      <div class="below">
        <span>
          <span class="help" part="help" id="${this._helpId}"></span>
          <span class="error" part="error" id="${this._errorId}" role="alert"></span>
        </span>
        <span class="counter" part="counter" id="${this._counterId}" role="status" aria-live="polite" hidden></span>
      </div>
    `
    return markup
  }

  afterRender() {
    this._ta = this.$("textarea")
    this._labelEl = this.$(".label")
    this._wrapEl = this.$(".wrapper")
    this._helpEl = this.$(".help")
    this._errorEl = this.$(".error")
    this._counterEl = this.$(".counter")

    /*
     * The shadow DOM is new: rebuild it from the stored value. Registering
     * the value also makes an untouched control submit an (empty) entry, as
     * a native one does.
     */
    this._setFormValue(this._value)
    this._ta.value = this._value
    this._syncAll()

    this.listen(this._ta, "input", this._onInput.bind(this))
    this.listen(this._ta, "change", this._onChange.bind(this))
    this.listen(this._ta, "focus", this._onFocus.bind(this))
    this.listen(this._ta, "blur", this._onBlur.bind(this))
    this.listen(this, "invalid", this._onInvalid.bind(this))
    this.listen(this, "click", this._onHostClick.bind(this))
    return
  }

  onConnected() {
    /* Labels outside the shadow root can only be resolved once connected. */
    this._syncAccessibleName()

    /* Sizes can only be measured once the element is in the document. */
    this._syncHeights()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "value") {
      this._applyValueAttribute(newValue)
    }

    if (this._ta === undefined || this._ta === null) {
      return
    }

    this._syncAll()
    return
  }

  /* The control is disabled by its own attribute or by a disabled fieldset. */
  _isDisabled() {
    const disabled = this.hasAttribute("disabled") === true || this._formDisabled === true
    return disabled
  }

  _syncAll() {
    const label = this.getAttribute("label") || ""
    const placeholder = this.getAttribute("placeholder") || ""
    const helpText = this.getAttribute("help-text") || ""
    const rows = parseInt(this.getAttribute("rows") || "3", 10)
    const disabled = this._isDisabled()
    const readonly = this.hasAttribute("readonly")
    const required = this.hasAttribute("required")
    const autoGrow = this.hasAttribute("auto-grow")
    const noResize = this.hasAttribute("no-resize")
    const maxlength = this.getAttribute("maxlength")
    const minlength = this.getAttribute("minlength")
    const spellcheck = this.getAttribute("spellcheck") !== "false"
    const autocomplete = this.getAttribute("autocomplete") || "on"
    const wrap = this.getAttribute("wrap") || "soft"

    this._labelEl.textContent = label
    this._labelEl.toggleAttribute("data-required", required === true)
    this._wrapEl.toggleAttribute("data-disabled", disabled === true)

    this._ta.placeholder = placeholder
    this._ta.rows = Number.isNaN(rows) === true || rows < 1 ? 3 : rows
    this._ta.disabled = disabled
    this._ta.readOnly = readonly
    this._ta.required = required
    this._ta.spellcheck = spellcheck
    this._ta.autocomplete = autocomplete
    this._ta.wrap = wrap
    this._ta.setAttribute("aria-required", required === true ? "true" : "false")

    if (maxlength !== null) {
      this._ta.setAttribute("maxlength", maxlength)
    } else {
      this._ta.removeAttribute("maxlength")
    }
    if (minlength !== null) {
      this._ta.setAttribute("minlength", minlength)
    } else {
      this._ta.removeAttribute("minlength")
    }

    this._ta.toggleAttribute("data-auto-grow", autoGrow === true)
    this._ta.toggleAttribute("data-no-resize", noResize === true && autoGrow === false)

    this._helpEl.textContent = helpText
    this._syncAccessibleName()
    this._updateCounter()
    this._syncHeights()

    /* required / minlength / maxlength / error-message feed validity. */
    this._refreshValidity()
    this._renderValidity(false)
    return
  }

  /*
   * Name the shadow textarea. The built-in <label for> covers the `label`
   * attribute; a name given to the host from outside is copied across.
   */
  _syncAccessibleName() {
    if (this._ta === undefined || this._ta === null) {
      return
    }

    const label = this.getAttribute("label") || ""
    const hostLabel = resolveHostLabel(this, this._internals)
    const explicit = this.hasAttribute("aria-label") === true || this.hasAttribute("aria-labelledby") === true

    if (hostLabel.length > 0 && (explicit === true || label.length === 0)) {
      this._ta.setAttribute("aria-label", hostLabel)
    } else {
      this._ta.removeAttribute("aria-label")
    }
    return
  }

  _updateDescribedBy() {
    const ids = []
    if (this._helpEl.textContent.length > 0) {
      ids.push(this._helpId)
    }
    if (this._errorEl.hasAttribute("data-visible") === true) {
      ids.push(this._errorId)
    }
    if (ids.length > 0) {
      this._ta.setAttribute("aria-describedby", ids.join(" "))
    } else {
      this._ta.removeAttribute("aria-describedby")
    }
    return
  }

  _updateCounter() {
    const maxlength = this.getAttribute("maxlength")
    const showWords = this.hasAttribute("count-words")
    const text = this._ta.value
    const maximum = maxlength !== null ? parseInt(maxlength, 10) : NaN
    const hasMaximum = Number.isNaN(maximum) === false

    if (hasMaximum === false && showWords === false) {
      this._counterEl.hidden = true
      this._counterEl.removeAttribute("data-near-limit")
      return
    }

    this._counterEl.hidden = false

    const parts = []
    if (hasMaximum === true) {
      parts.push(`${text.length}/${maximum}`)
    }
    if (showWords === true) {
      parts.push(t("mj.textarea.wordCount", { count: countWords(text) }))
    }
    this._counterEl.textContent = parts.join(" • ")

    const nearLimit = hasMaximum === true && text.length >= maximum * NEAR_LIMIT_RATIO
    this._counterEl.toggleAttribute("data-near-limit", nearLimit === true)
    return
  }

  /*
   * Height in pixels of `rows` lines of text including the textarea's own
   * vertical padding (the textarea is border-box sized).
   */
  _rowsToPixels(rows) {
    const style = getComputedStyle(this._ta)
    const lineHeight = parseFloat(style.lineHeight) || FALLBACK_LINE_HEIGHT_PX
    const paddingTop = parseFloat(style.paddingTop) || 0
    const paddingBottom = parseFloat(style.paddingBottom) || 0
    const pixels = rows * lineHeight + paddingTop + paddingBottom
    return pixels
  }

  /* Apply min-rows / max-rows and, with auto-grow, fit the content. */
  _syncHeights() {
    if (this._ta === undefined || this._ta === null || this.isConnected === false) {
      return
    }

    const minRows = parseInt(this.getAttribute("min-rows") || "2", 10)
    const maxRows = parseInt(this.getAttribute("max-rows") || "", 10)

    if (Number.isNaN(minRows) === false && minRows > 0) {
      this._ta.style.minHeight = `${this._rowsToPixels(minRows)}px`
    } else {
      this._ta.style.minHeight = ""
    }

    if (Number.isNaN(maxRows) === false && maxRows > 0) {
      this._ta.style.maxHeight = `${this._rowsToPixels(maxRows)}px`
    } else {
      this._ta.style.maxHeight = ""
    }

    this._autoGrow()
    return
  }

  /*
   * Fit the height to the content. Up to `max-rows` the textarea grows and
   * never scrolls; beyond it the height stops at the cap and the textarea
   * scrolls so no text is cut off.
   */
  _autoGrow() {
    if (this.hasAttribute("auto-grow") === false) {
      this._ta.style.height = ""
      this._ta.style.overflowY = ""
      return
    }

    this._ta.style.height = "auto"
    const contentHeight = this._ta.scrollHeight
    const maxHeight = parseFloat(this._ta.style.maxHeight)
    const capped = Number.isNaN(maxHeight) === false && contentHeight > maxHeight

    this._ta.style.height = `${capped === true ? maxHeight : contentHeight}px`
    this._ta.style.overflowY = capped === true ? "auto" : "hidden"
    return
  }

  /*
   * Apply the `value` attribute. The attribute is delivered once before the
   * first render and again after it (see MjElement), so the text already
   * applied is remembered and a repeat delivery does not overwrite what the
   * user or a script has entered since.
   */
  _applyValueAttribute(attributeValue) {
    if (attributeValue === this._appliedValueAttribute) {
      return
    }
    this._appliedValueAttribute = attributeValue
    this._applyValue(attributeValue)
    return
  }

  /* The single entry point for every programmatic value change. */
  _applyValue(next) {
    const text = next === null || next === undefined ? "" : String(next)

    this._setFormValue(text)
    this._committedValue = text

    if (this._ta !== undefined && this._ta !== null) {
      if (this._ta.value !== text) {
        this._ta.value = text
      }
      this._updateCounter()
      this._syncHeights()
      this._renderValidity(false)
    }
    return
  }

  _onInput(event) {
    const text = this._ta.value
    this._setFormValue(text)
    this._autoGrow()
    this._updateCounter()
    this._renderValidity(false)
    this.emit("mj-input", { value: text, charCount: text.length, wordCount: countWords(text) })
    return
  }

  _onChange(event) {
    const text = this._ta.value
    if (text !== this._committedValue) {
      this._committedValue = text
      this.emit("mj-change", { value: text, charCount: text.length, wordCount: countWords(text) })
    }
    return
  }

  _onFocus(event) {
    /* A label placed after the field in the document exists by now. */
    this._syncAccessibleName()
    return
  }

  _onBlur(event) {
    this._showErrors = true
    this._refreshValidity()
    this._renderValidity(true)
    return
  }

  /* A failed checkValidity() / reportValidity() / form submit. */
  _onInvalid(event) {
    this._showErrors = true
    this._renderValidity(true)
    return
  }

  /*
   * Activating an associated <label> clicks the host; move focus to the
   * textarea as a native control would.
   */
  _onHostClick(event) {
    const path = event.composedPath()
    if (path.length > 0 && path[0] === this && this._isDisabled() === false) {
      this._ta.focus()
    }
    return
  }

  /*
   * Show or hide the inline error from the current validity. `error-message`
   * replaces the built-in text but never makes a valid field look invalid.
   * `announce` is true when the user (blur) or a submit attempt triggered
   * the check; only then is `mj-invalid` emitted.
   */
  _renderValidity(announce) {
    const message = this.validationMessage
    const invalid = message.length > 0 && this._showErrors === true

    if (invalid === true) {
      const override = this.getAttribute("error-message") || ""
      const displayMessage = override.length > 0 ? override : message
      this._errorEl.textContent = displayMessage
      this._errorEl.setAttribute("data-visible", "")
      this._wrapEl.setAttribute("data-invalid", "")
      this._ta.setAttribute("aria-invalid", "true")
      this._updateDescribedBy()
      if (announce === true) {
        this.emit("mj-invalid", { validationMessage: displayMessage })
      }
    } else {
      this._errorEl.textContent = ""
      this._errorEl.removeAttribute("data-visible")
      this._wrapEl.removeAttribute("data-invalid")
      this._ta.setAttribute("aria-invalid", "false")
      this._updateDescribedBy()
    }
    return
  }

  /* Length constraints; `required` is handled by the mixin. */
  _customValidity() {
    let message = ""
    const text = this._value === null || this._value === undefined ? "" : String(this._value)

    if (text.length > 0) {
      const minlength = parseInt(this.getAttribute("minlength") || "", 10)
      const maxlength = parseInt(this.getAttribute("maxlength") || "", 10)

      if (Number.isNaN(minlength) === false && text.length < minlength) {
        message = t("mj.textarea.tooShort", { count: minlength, current: text.length })
      } else if (Number.isNaN(maxlength) === false && text.length > maxlength) {
        message = t("mj.textarea.tooLong", { count: maxlength, current: text.length })
      }
    }

    return message
  }

  _validationAnchor() {
    const anchor = this._ta !== undefined ? this._ta : null
    return anchor
  }

  onFormReset(initial) {
    this._showErrors = false
    this._applyValue(initial)
    return
  }

  onFormRestore(state) {
    const restored = typeof state === "string" ? state : ""
    this._applyValue(restored)
    return
  }

  onFormDisabled(disabled) {
    this._formDisabled = disabled === true
    if (this._ta !== undefined && this._ta !== null) {
      this._syncAll()
    }
    return
  }

  reportValidity() {
    this._refreshValidity()
    const valid = super.reportValidity()
    return valid
  }

  get wordCount() {
    const text = this._value === null || this._value === undefined ? "" : String(this._value)
    const count = countWords(text)
    return count
  }

  get value() {
    return this._value
  }

  set value(next) {
    this._applyValue(next)
    return
  }

  focus(options) {
    if (this._ta !== undefined && this._ta !== null) {
      this._ta.focus(options)
    }
    return
  }
}
