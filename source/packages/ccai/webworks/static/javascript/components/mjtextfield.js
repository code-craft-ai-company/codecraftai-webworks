/*
 * mjtextfield.js
 *
 * <mj-text-field> -- foundational single-line text entry control.
 * Wraps a native <input type="text"> with label, help, error, prefix/suffix
 * slots, character counter, and clear button.
 *
 * Value model: `this._value` (owned by FormControlMixin) is the single source
 * of truth. The `value` attribute is the default value: it is applied when it
 * is first seen and whenever it changes, and a form reset returns to it. The
 * shadow <input> is rebuilt from `this._value` on every render, so a value
 * assigned before the element is connected, or held across a re-parent, is
 * always shown.
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

.field {
  display: flex;
  align-items: center;
  min-height: var(--mj-control-height-md);
  background: var(--mj-surface);
  border: 1px solid var(--mj-border-strong);
  border-radius: var(--mj-radius-md);
  transition: border-color var(--mj-motion-fast) var(--mj-motion-ease);
  overflow: hidden;
}
:host([size="sm"]) .field { min-height: var(--mj-control-height-sm); }
:host([size="lg"]) .field { min-height: var(--mj-control-height-lg); }

.field:focus-within {
  border-color: var(--mj-accent);
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
.field[data-invalid] { border-color: var(--mj-color-danger); }

.prefix, .suffix {
  display: flex;
  align-items: center;
  padding: 0 var(--mj-space-2);
  color: var(--mj-text-muted);
  flex-shrink: 0;
}
.prefix[hidden], .suffix[hidden] { display: none; }
::slotted([slot="prefix"]), ::slotted([slot="suffix"]) { display: inline-flex; }

input {
  flex: 1;
  min-width: 0;
  height: 100%;
  padding: 0 var(--mj-space-3);
  font: inherit;
  color: var(--mj-text);
  background: transparent;
  border: none;
  outline: none;
}
input::placeholder { color: var(--mj-text-muted); }
input:disabled { cursor: not-allowed; }

.clear-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 1.5rem;
  height: 1.5rem;
  margin-inline-end: var(--mj-space-1);
  padding: 0;
  background: transparent;
  border: none;
  border-radius: var(--mj-radius-sm);
  cursor: pointer;
  color: var(--mj-text-muted);
  font-size: 1rem;
  line-height: 1;
  flex-shrink: 0;
}
.clear-btn svg { width: 0.75rem; height: 0.75rem; }
.clear-btn:hover { color: var(--mj-text); }
.clear-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
}
.clear-btn[hidden] { display: none; }

:host([disabled]) .field, .field[data-disabled] { opacity: 0.55; pointer-events: none; }
:host([variant="filled"]) .field { background: var(--mj-bg-muted); border-color: transparent; border-bottom-color: var(--mj-border-strong); border-radius: var(--mj-radius-md) var(--mj-radius-md) 0 0; }
:host([variant="plain"]) .field { border-color: transparent; background: transparent; }

.below { display: flex; justify-content: space-between; gap: var(--mj-space-2); margin-top: var(--mj-space-1); }
.help, .error { font-size: var(--mj-font-size-sm); }
.help { color: var(--mj-text-muted); }
.error { color: var(--mj-color-danger); display: none; }
.error[data-visible] { display: block; }
.counter { font-size: var(--mj-font-size-xs); color: var(--mj-text-muted); text-align: end; flex-shrink: 0; }
.counter[hidden] { display: none; }
`;

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

/*
 * Test `value` against an HTML `pattern` attribute the way a native input
 * does: the whole value must match. A pattern that does not compile is
 * ignored, as the platform ignores it.
 */
function matchesPattern(pattern, value) {
  let expression = null
  let matches = true

  try {
    expression = new RegExp(`^(?:${pattern})$`, "v")
  } catch (unicodeSetsError) {
    try {
      expression = new RegExp(`^(?:${pattern})$`, "u")
    } catch (unicodeError) {
      expression = null
    }
  }

  if (expression !== null) {
    matches = expression.test(value)
  }

  return matches
}

export class MjTextField extends FormControlMixin(MjElement) {
  static tagName = "mj-text-field";
  static styles = STYLES;
  static watched = [
    "label", "placeholder", "help-text", "error-message", "value",
    "maxlength", "minlength", "pattern", "required", "disabled",
    "readonly", "clearable", "autocomplete", "inputmode", "variant", "size",
    "autofocus", "spellcheck", "aria-label", "aria-labelledby"
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

    this._autofocusDone = false

    this._inputId = nextId("mjtf-input")
    this._helpId = nextId("mjtf-help")
    this._errorId = nextId("mjtf-error")
    this._counterId = nextId("mjtf-counter")
  }

  render() {
    const markup = html`
      <label class="label" part="label" for="${this._inputId}"></label>
      <div class="field" part="field">
        <span class="prefix" part="prefix"><slot name="prefix"></slot></span>
        <input
          part="input"
          id="${this._inputId}"
          type="text"
          autocomplete="on"
        />
        <span class="suffix" part="suffix"><slot name="suffix"></slot></span>
        <button class="clear-btn" part="clear-button" type="button" hidden>
          <svg viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" aria-hidden="true">
            <path d="M2 2l8 8M10 2l-8 8"/>
          </svg>
        </button>
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
    this._input = this.$("input")
    this._labelEl = this.$(".label")
    this._helpEl = this.$(".help")
    this._errorEl = this.$(".error")
    this._counterEl = this.$(".counter")
    this._clearBtn = this.$(".clear-btn")
    this._fieldEl = this.$(".field")

    /* Empty prefix / suffix wrappers take no room (see _syncAffixes). */
    this._syncAffixes()
    const affixSlots = this.$all("[part='prefix'] slot, [part='suffix'] slot")
    for (let index = 0; index < affixSlots.length; index = index + 1) {
      this.listen(affixSlots[index], "slotchange", this._syncAffixes.bind(this))
    }

    this._clearBtn.setAttribute("aria-label", t("core.clear"))

    /*
     * The shadow DOM is new: rebuild it from the stored value. Registering
     * the value also makes an untouched control submit an (empty) entry, as
     * a native one does.
     */
    this._setFormValue(this._value)
    this._input.value = this._value
    this._syncAll()

    this.listen(this._input, "input", this._onInput.bind(this))
    this.listen(this._input, "change", this._onChange.bind(this))
    this.listen(this._input, "focus", this._onFocus.bind(this))
    this.listen(this._input, "blur", this._onBlur.bind(this))
    this.listen(this._clearBtn, "click", this._onClear.bind(this))
    this.listen(this, "invalid", this._onInvalid.bind(this))
    this.listen(this, "click", this._onHostClick.bind(this))
    return
  }


  /*
   * An affix wrapper is shown only while its slot has content: an empty one
   * would still take its padding and indent the input.
   */
  _syncAffixes() {
    const wrappers = this.$all("[part='prefix'], [part='suffix']")
    for (let index = 0; index < wrappers.length; index = index + 1) {
      const wrapper = wrappers[index]
      const slot = wrapper.querySelector("slot")
      const assigned = slot !== null ? slot.assignedNodes({ flatten: true }) : []
      wrapper.hidden = assigned.length === 0
    }
    return
  }

  onConnected() {
    /* Labels outside the shadow root can only be resolved once connected. */
    this._syncAccessibleName()

    if (this.hasAttribute("autofocus") === true && this._autofocusDone === false) {
      this._autofocusDone = true
      this._input.focus()
    }
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "value") {
      this._applyValueAttribute(newValue)
    }

    if (this._input === undefined || this._input === null) {
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
    const maxlength = this.getAttribute("maxlength")
    const minlength = this.getAttribute("minlength")
    const pattern = this.getAttribute("pattern")
    const autocomplete = this.getAttribute("autocomplete") || "on"
    const inputmode = this.getAttribute("inputmode") || "text"
    const spellcheck = this.getAttribute("spellcheck")
    const disabled = this._isDisabled()
    const readonly = this.hasAttribute("readonly")
    const required = this.hasAttribute("required")

    this._labelEl.textContent = label
    this._labelEl.toggleAttribute("data-required", required === true)
    this._fieldEl.toggleAttribute("data-disabled", disabled === true)

    this._input.placeholder = placeholder
    this._input.autocomplete = autocomplete
    this._input.inputMode = inputmode
    this._input.disabled = disabled
    this._input.readOnly = readonly
    this._input.required = required
    this._input.setAttribute("aria-required", required === true ? "true" : "false")

    if (spellcheck !== null) {
      this._input.spellcheck = spellcheck !== "false"
    } else {
      this._input.removeAttribute("spellcheck")
    }

    if (maxlength !== null) {
      this._input.setAttribute("maxlength", maxlength)
    } else {
      this._input.removeAttribute("maxlength")
    }
    if (minlength !== null) {
      this._input.setAttribute("minlength", minlength)
    } else {
      this._input.removeAttribute("minlength")
    }
    if (pattern !== null) {
      this._input.setAttribute("pattern", pattern)
    } else {
      this._input.removeAttribute("pattern")
    }

    this._helpEl.textContent = helpText
    this._syncAccessibleName()
    this._updateCounter()
    this._updateClearButton()

    /* required / minlength / pattern / error-message all feed validity. */
    this._refreshValidity()
    this._renderValidity(false)
    return
  }

  /*
   * Name the shadow input. The built-in <label for> covers the `label`
   * attribute; a name given to the host from outside is copied across.
   */
  _syncAccessibleName() {
    if (this._input === undefined || this._input === null) {
      return
    }

    const label = this.getAttribute("label") || ""
    const hostLabel = resolveHostLabel(this, this._internals)
    const explicit = this.hasAttribute("aria-label") === true || this.hasAttribute("aria-labelledby") === true

    if (hostLabel.length > 0 && (explicit === true || label.length === 0)) {
      this._input.setAttribute("aria-label", hostLabel)
    } else {
      this._input.removeAttribute("aria-label")
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
      this._input.setAttribute("aria-describedby", ids.join(" "))
    } else {
      this._input.removeAttribute("aria-describedby")
    }
    return
  }

  _updateCounter() {
    const maxlength = this.getAttribute("maxlength")
    if (maxlength === null) {
      this._counterEl.hidden = true
    } else {
      this._counterEl.hidden = false
      const current = this._input.value.length
      this._counterEl.textContent = `${current}/${maxlength}`
    }
    return
  }

  _updateClearButton() {
    const clearable = this.hasAttribute("clearable")
    const readonly = this.hasAttribute("readonly")
    const disabled = this._isDisabled()
    const hasValue = this._input.value.length > 0
    const showClear = clearable === true && hasValue === true && readonly === false && disabled === false
    this._clearBtn.hidden = showClear === false
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

    if (this._input !== undefined && this._input !== null) {
      if (this._input.value !== text) {
        this._input.value = text
      }
      this._updateCounter()
      this._updateClearButton()
      this._renderValidity(false)
    }
    return
  }

  _onInput(event) {
    const text = this._input.value
    this._setFormValue(text)
    this._updateCounter()
    this._updateClearButton()
    this._renderValidity(false)
    this.emit("mj-input", { value: text })
    return
  }

  _onChange(event) {
    const text = this._input.value
    if (text !== this._committedValue) {
      this._committedValue = text
      this.emit("mj-change", { value: text })
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
   * input as a native control would.
   */
  _onHostClick(event) {
    const path = event.composedPath()
    if (path.length > 0 && path[0] === this && this._isDisabled() === false) {
      this._input.focus()
    }
    return
  }

  _onClear(event) {
    const previous = this._input.value
    this._input.value = ""
    this._setFormValue("")
    this._committedValue = ""
    this._updateClearButton()
    this._updateCounter()
    this._renderValidity(false)
    this.emit("mj-clear", { previousValue: previous })
    this.emit("mj-input", { value: "" })
    this.emit("mj-change", { value: "" })
    this._input.focus()
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
      this._fieldEl.setAttribute("data-invalid", "")
      this._input.setAttribute("aria-invalid", "true")
      this._updateDescribedBy()
      if (announce === true) {
        this.emit("mj-invalid", { validationMessage: displayMessage })
      }
    } else {
      this._errorEl.textContent = ""
      this._errorEl.removeAttribute("data-visible")
      this._fieldEl.removeAttribute("data-invalid")
      this._input.setAttribute("aria-invalid", "false")
      this._updateDescribedBy()
    }
    return
  }

  /* Length and pattern constraints; `required` is handled by the mixin. */
  _customValidity() {
    let message = ""
    const text = this._value === null || this._value === undefined ? "" : String(this._value)

    if (text.length > 0) {
      const minlength = parseInt(this.getAttribute("minlength") || "", 10)
      const maxlength = parseInt(this.getAttribute("maxlength") || "", 10)
      const pattern = this.getAttribute("pattern")

      if (Number.isNaN(minlength) === false && text.length < minlength) {
        message = t("mj.textField.tooShort", { count: minlength, current: text.length })
      } else if (Number.isNaN(maxlength) === false && text.length > maxlength) {
        message = t("mj.textField.tooLong", { count: maxlength, current: text.length })
      } else if (pattern !== null && pattern.length > 0 && matchesPattern(pattern, text) === false) {
        message = t("mj.textField.patternMismatch")
      }
    }

    return message
  }

  _validationAnchor() {
    const anchor = this._input !== undefined ? this._input : null
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
    if (this._input !== undefined && this._input !== null) {
      this._syncAll()
    }
    return
  }

  reportValidity() {
    this._refreshValidity()
    const valid = super.reportValidity()
    return valid
  }

  get value() {
    return this._value
  }

  set value(next) {
    this._applyValue(next)
    return
  }

  focus(options) {
    if (this._input !== undefined && this._input !== null) {
      this._input.focus(options)
    }
    return
  }
}
