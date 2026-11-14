/*
 * mjtypedfield.js
 *
 * <mj-typed-field> -- typed text field for email, URL, and telephone inputs
 * with type-appropriate inputmode, autocomplete, and validation messages.
 *
 * Value model: `this._value` (owned by FormControlMixin) is the single source
 * of truth; the `value` attribute is the default value and the shadow <input>
 * is rebuilt from `this._value` on every render.
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

input {
  flex: 1;
  min-width: 0;
  padding: 0 var(--mj-space-3);
  font: inherit;
  color: var(--mj-text);
  background: transparent;
  border: none;
  outline: none;
}
input::placeholder { color: var(--mj-text-muted); }

.format-hint {
  font-size: var(--mj-font-size-xs);
  color: var(--mj-text-muted);
  margin-top: var(--mj-space-1);
  display: none;
}
.format-hint[data-visible] { display: block; }

.below { margin-top: var(--mj-space-1); }
.help { font-size: var(--mj-font-size-sm); color: var(--mj-text-muted); }
.help:empty { display: none; }
.error { font-size: var(--mj-font-size-sm); color: var(--mj-color-danger); display: none; }
.error[data-visible] { display: block; }

:host([disabled]) .field, .field[data-disabled] { opacity: 0.55; pointer-events: none; }
`;

const DEFAULT_TYPE = "email";

const TYPE_CONFIG = {
  email: { inputmode: "email", autocomplete: "email", hint: "user@example.com" },
  url:   { inputmode: "url",   autocomplete: "url",   hint: "https://example.com" },
  tel:   { inputmode: "tel",   autocomplete: "tel",   hint: "+1 (555) 000-0000" }
};

/* Telephone hint for locales outside the North American Numbering Plan. */
const TEL_HINT_INTERNATIONAL = "+00 000 000 0000";

const TYPE_MISMATCH_KEYS = {
  email: "mj.typedField.invalidEmail",
  url:   "mj.typedField.invalidUrl",
  tel:   "mj.typedField.invalidTel"
};

/* The address grammar the HTML standard uses for <input type="email">. */
const EMAIL_PATTERN = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;

/*
 * Default telephone check: an optional leading "+", then digits with the
 * usual separators, and an optional extension. The `pattern` attribute
 * replaces it for sites that need a national format.
 */
const TEL_PATTERN = /^\+?[0-9\s().\-/]+(?:\s*(?:x|ext\.?)\s*[0-9]+)?$/i;
const TEL_MINIMUM_DIGITS = 3;

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

/* Only the three text-like types are supported; anything else is email. */
function normalizeType(type) {
  let normalized = DEFAULT_TYPE
  if (type !== null && type !== undefined) {
    const lowered = String(type).toLowerCase()
    if (TYPE_CONFIG[lowered] !== undefined) {
      normalized = lowered
    }
  }
  return normalized
}

function isValidEmail(text) {
  const valid = EMAIL_PATTERN.test(text)
  return valid
}

/* A URL is valid when it parses as an absolute URL, as for a native input. */
function isValidUrl(text) {
  let valid = false
  try {
    const parsed = new URL(text)
    valid = parsed.protocol.length > 1
  } catch (error) {
    valid = false
  }
  return valid
}

function isValidTel(text) {
  const digits = text.replace(/[^0-9]/g, "")
  const valid = TEL_PATTERN.test(text) === true && digits.length >= TEL_MINIMUM_DIGITS
  return valid
}

/*
 * Example telephone number for the page locale: the North American format
 * for US / Canada locales, a neutral international shape otherwise.
 */
function telephoneHint() {
  const locale = document.documentElement.lang || navigator.language || "en-US"
  const region = locale.split("-").length > 1 ? locale.split("-")[1].toUpperCase() : ""
  const northAmerican = region === "US" || region === "CA" || locale.toLowerCase() === "en"
  const hint = northAmerican === true ? TYPE_CONFIG.tel.hint : TEL_HINT_INTERNATIONAL
  return hint
}

export class MjTypedField extends FormControlMixin(MjElement) {
  static tagName = "mj-typed-field";
  static styles = STYLES;
  static watched = [
    "type", "label", "placeholder", "help-text", "error-message", "value",
    "required", "disabled", "readonly", "multiple", "maxlength", "minlength",
    "pattern", "autocomplete", "show-format-hint", "format-hint", "size",
    "aria-label", "aria-labelledby"
  ];

  constructor() {
    super()
    this._initFormControl()

    /* Value at the last mj-change, used to suppress no-op change events. */
    this._committedValue = ""

    /* The `value` attribute text most recently applied to the control. */
    this._appliedValueAttribute = null

    /* The type the shadow input currently has; null before first render. */
    this._activeType = null

    /* True while an ancestor <fieldset disabled> disables the control. */
    this._formDisabled = false

    /* Errors are shown once the user has left the field or a submit failed. */
    this._showErrors = false

    /* True while the format hint is displayed (the input has focus). */
    this._hintVisible = false

    /* The `multiple` misuse warning is logged once per element. */
    this._warnedMultiple = false

    this._inputId = nextId("mjtf2-input")
    this._helpId = nextId("mjtf2-help")
    this._errorId = nextId("mjtf2-error")
    this._hintId = nextId("mjtf2-hint")
  }

  render() {
    const markup = html`
      <label class="label" part="label" for="${this._inputId}"></label>
      <div class="field" part="field">
        <span class="prefix" part="prefix"><slot name="prefix"></slot></span>
        <input part="input" id="${this._inputId}" type="email" />
        <span class="suffix" part="suffix"><slot name="suffix"></slot></span>
      </div>
      <span class="format-hint" part="format-hint" id="${this._hintId}"></span>
      <div class="below">
        <span class="help" part="help" id="${this._helpId}"></span>
        <span class="error" part="error" id="${this._errorId}" role="alert"></span>
      </div>
    `
    return markup
  }

  afterRender() {
    this._input = this.$("input")
    this._labelEl = this.$(".label")
    this._formatHint = this.$(".format-hint")
    this._helpEl = this.$(".help")
    this._errorEl = this.$(".error")
    this._fieldEl = this.$(".field")

    /* Empty prefix / suffix wrappers take no room (see _syncAffixes). */
    this._syncAffixes()
    const affixSlots = this.$all("[part='prefix'] slot, [part='suffix'] slot")
    for (let index = 0; index < affixSlots.length; index = index + 1) {
      this.listen(affixSlots[index], "slotchange", this._syncAffixes.bind(this))
    }

    this._hintVisible = false

    /*
     * The shadow DOM is new: set the type first (a value is sanitised by the
     * input type), then rebuild the input from the stored value.
     */
    this._setFormValue(this._value)
    this._syncAll()
    this._input.value = this._value

    this.listen(this._input, "input", this._onInput.bind(this))
    this.listen(this._input, "change", this._onChange.bind(this))
    this.listen(this._input, "blur", this._onBlur.bind(this))
    this.listen(this._input, "focus", this._onFocus.bind(this))
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
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "value") {
      this._applyValueAttribute(newValue)
    }

    if (this._input === undefined || this._input === null) {
      return
    }

    if (name === "type") {
      /*
       * A runtime type change clears a value entered for the previous type
       * and tells the host (typedtextfield.md, edge cases). Comparing with
       * the type in effect keeps a repeated delivery from clearing again.
       */
      const nextType = normalizeType(newValue)
      const typeChanged = this._activeType !== null && nextType !== this._activeType
      const hadValue = this._value !== ""
      this._syncAll()
      if (typeChanged === true && hadValue === true) {
        this._applyValue("")
        this.emit("mj-change", { value: "" })
      }
      return
    }

    this._syncAll()
    return
  }

  _getType() {
    const type = normalizeType(this.getAttribute("type"))
    return type
  }

  /* The control is disabled by its own attribute or by a disabled fieldset. */
  _isDisabled() {
    const disabled = this.hasAttribute("disabled") === true || this._formDisabled === true
    return disabled
  }

  _syncAll() {
    const type = this._getType()
    const config = TYPE_CONFIG[type]
    const label = this.getAttribute("label") || ""
    const placeholder = this.getAttribute("placeholder") || ""
    const helpText = this.getAttribute("help-text") || ""
    const disabled = this._isDisabled()
    const readonly = this.hasAttribute("readonly")
    const required = this.hasAttribute("required")
    const multipleRequested = this.hasAttribute("multiple")
    const multiple = multipleRequested === true && type === "email"
    const maxlength = this.getAttribute("maxlength")
    const minlength = this.getAttribute("minlength")
    const autocomplete = this.getAttribute("autocomplete") || config.autocomplete
    const defaultHint = type === "tel" ? telephoneHint() : config.hint
    const formatHintText = this.getAttribute("format-hint") || defaultHint
    const showFormatHint = this.hasAttribute("show-format-hint")

    if (multipleRequested === true && type !== "email" && this._warnedMultiple === false) {
      this._warnedMultiple = true
      console.warn("[mj-typed-field] `multiple` is only supported for type=\"email\"; ignoring it")
    }

    this._activeType = type

    if (this._input.type !== type) {
      this._input.type = type
    }
    this._input.inputMode = config.inputmode
    this._input.autocomplete = autocomplete
    this._input.placeholder = placeholder
    this._input.disabled = disabled
    this._input.readOnly = readonly
    this._input.required = required
    this._input.multiple = multiple
    this._input.setAttribute("aria-required", required === true ? "true" : "false")

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

    this._labelEl.textContent = label
    this._labelEl.toggleAttribute("data-required", required === true)
    this._fieldEl.toggleAttribute("data-disabled", disabled === true)
    this._helpEl.textContent = helpText
    this._formatHint.textContent = formatHintText

    if (showFormatHint === false) {
      this._hintVisible = false
    }
    this._formatHint.toggleAttribute("data-visible", this._hintVisible === true)

    this._syncAccessibleName()

    /* required / type / length / pattern / error-message feed validity. */
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
    if (this._hintVisible === true) {
      ids.push(this._hintId)
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
      this._renderValidity(false)
    }
    return
  }

  _onFocus(event) {
    /* A label placed after the field in the document exists by now. */
    this._syncAccessibleName()

    if (this.hasAttribute("show-format-hint") === true) {
      this._hintVisible = true
      this._formatHint.setAttribute("data-visible", "")
      this._updateDescribedBy()
    }
    return
  }

  _onInput(event) {
    const text = this._input.value
    this._setFormValue(text)
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

  _onBlur(event) {
    this._hintVisible = false
    this._formatHint.removeAttribute("data-visible")

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
        this.emit("mj-invalid", {
          validationMessage: displayMessage,
          validityState: this.validity
        })
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

  /* True when `text` is well formed for the current type. */
  _matchesType(text) {
    const type = this._getType()
    let matches = true

    if (type === "email") {
      if (this.hasAttribute("multiple") === true) {
        const addresses = text.split(",")
        for (let index = 0; index < addresses.length; index = index + 1) {
          if (isValidEmail(addresses[index].trim()) === false) {
            matches = false
          }
        }
      } else {
        matches = isValidEmail(text)
      }
    } else if (type === "url") {
      matches = isValidUrl(text)
    } else {
      /* tel: browsers never flag a telephone value, so it is checked here. */
      const pattern = this.getAttribute("pattern")
      const hasPattern = pattern !== null && pattern.length > 0
      matches = hasPattern === true ? true : isValidTel(text)
    }

    return matches
  }

  /*
   * Type format, length and pattern constraints; `required` is handled by
   * the mixin.
   */
  _customValidity() {
    let message = ""
    const text = this._value === null || this._value === undefined ? "" : String(this._value)

    if (text.length > 0) {
      const type = this._getType()
      const minlength = parseInt(this.getAttribute("minlength") || "", 10)
      const maxlength = parseInt(this.getAttribute("maxlength") || "", 10)
      const pattern = this.getAttribute("pattern")

      if (this._matchesType(text) === false) {
        message = t(TYPE_MISMATCH_KEYS[type])
        if (type === "url" && /^[a-z][a-z0-9+.-]*:/i.test(text) === false) {
          message = t("mj.typedField.urlMissingScheme")
        }
      } else if (Number.isNaN(minlength) === false && text.length < minlength) {
        message = t("mj.typedField.tooShort", { count: minlength, current: text.length })
      } else if (Number.isNaN(maxlength) === false && text.length > maxlength) {
        message = t("mj.typedField.tooLong", { count: maxlength, current: text.length })
      } else if (pattern !== null && pattern.length > 0 && matchesPattern(pattern, text) === false) {
        message = type === "tel" ? t("mj.typedField.invalidTel") : t("mj.typedField.patternMismatch")
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
