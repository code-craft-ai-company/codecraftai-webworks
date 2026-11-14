/*
 * mjnumberfield.js
 *
 * <mj-number-field> -- numeric / currency / percentage input with
 * locale-aware display formatting, increment/decrement spinner buttons,
 * and hold-to-repeat behavior.
 *
 * Value model: `this._rawNumber` is the number (NaN when the field is empty)
 * and `this._value` (owned by FormControlMixin) its plain decimal string, the
 * form value. The `value` attribute and property take that plain form
 * ("1234.5"), never a locale-formatted one. The shadow <input> shows the
 * locale-formatted number while it is not focused and an ungrouped editing
 * text in the same locale while it is, so what is displayed always parses
 * back to the same number.
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
  align-items: stretch;
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

.prefix-slot, .suffix-slot {
  display: flex;
  align-items: center;
  padding: 0 var(--mj-space-2);
  color: var(--mj-text-muted);
  flex-shrink: 0;
}
.prefix-slot[hidden], .suffix-slot[hidden] { display: none; }

input {
  flex: 1;
  min-width: 0;
  padding: 0 var(--mj-space-3);
  font: inherit;
  font-variant-numeric: tabular-nums;
  color: var(--mj-text);
  background: transparent;
  border: none;
  outline: none;
  text-align: end;
}
input::placeholder { color: var(--mj-text-muted); }

.spinners {
  display: flex;
  flex-direction: column;
  border-inline-start: 1px solid var(--mj-border);
  flex-shrink: 0;
}
.spinners[hidden] { display: none; }

.spin-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 var(--mj-space-2);
  background: var(--mj-bg-subtle);
  border: none;
  cursor: pointer;
  color: var(--mj-text-muted);
  line-height: 1;
  font-size: 0.6rem;
}
.spin-btn:hover { background: var(--mj-bg-muted); color: var(--mj-text); }
.spin-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: -1px;
}
.spin-btn[data-at-limit], .spin-btn:disabled { opacity: 0.4; pointer-events: none; }
.spin-btn + .spin-btn { border-block-start: 1px solid var(--mj-border); }

/*
 * spinner-position="stacked": the increment button spans the field above the
 * input row and the decrement button below it. The default ("side") keeps
 * both buttons in a column beside the input.
 */
.field[data-spinner-position="stacked"] {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  min-height: 0;
}
.field[data-spinner-position="stacked"] .spinners { display: contents; }
.field[data-spinner-position="stacked"] .spinners[hidden] { display: none; }
.field[data-spinner-position="stacked"] .prefix-slot { grid-row: 2; grid-column: 1; }
.field[data-spinner-position="stacked"] input {
  grid-row: 2;
  grid-column: 2;
  min-block-size: var(--mj-control-height-md);
  text-align: center;
}
.field[data-spinner-position="stacked"] .suffix-slot { grid-row: 2; grid-column: 3; }
.field[data-spinner-position="stacked"] .spin-btn {
  grid-column: 1 / -1;
  padding-block: var(--mj-space-1);
}
.field[data-spinner-position="stacked"] [part="increment-button"] {
  grid-row: 1;
  border-block-end: 1px solid var(--mj-border);
}
.field[data-spinner-position="stacked"] [part="decrement-button"] { grid-row: 3; }
:host([size="sm"]) .field[data-spinner-position="stacked"] input { min-block-size: var(--mj-control-height-sm); }
:host([size="lg"]) .field[data-spinner-position="stacked"] input { min-block-size: var(--mj-control-height-lg); }

.below { margin-top: var(--mj-space-1); }
.help { font-size: var(--mj-font-size-sm); color: var(--mj-text-muted); }
.help:empty { display: none; }
.error { font-size: var(--mj-font-size-sm); color: var(--mj-color-danger); display: none; }
.error[data-visible] { display: block; }

:host([disabled]) .field, .field[data-disabled] { opacity: 0.55; pointer-events: none; }
`;

/* Hold-to-repeat timing for the spinner buttons, in milliseconds. */
const HOLD_DELAY_MS = 600;
const HOLD_REPEAT_MS = 100;

/* Arrow keys step once; Page Up / Page Down step this many times. */
const PAGE_STEP_MULTIPLIER = 10;

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

/* Number of digits after the decimal point in the shortest form of `value`. */
function countDecimals(value) {
  let decimals = 0

  if (Number.isFinite(value) === true) {
    const text = String(value)
    const exponentIndex = text.indexOf("e-")
    if (exponentIndex >= 0) {
      const mantissa = text.slice(0, exponentIndex)
      const mantissaDot = mantissa.indexOf(".")
      const mantissaDecimals = mantissaDot >= 0 ? mantissa.length - mantissaDot - 1 : 0
      decimals = parseInt(text.slice(exponentIndex + 2), 10) + mantissaDecimals
    } else {
      const dot = text.indexOf(".")
      if (dot >= 0) {
        decimals = text.length - dot - 1
      }
    }
  }

  return Math.min(decimals, 20)
}

/* Round away binary floating-point noise (0.1 + 0.2 -> 0.3). */
function roundToDecimals(value, decimals) {
  const rounded = Number(value.toFixed(decimals))
  return rounded
}

/*
 * Parse the plain decimal form used by the `value` attribute and property
 * ("1234.5", "-3", "1e3"). Anything else, including the empty string, is NaN.
 */
function parsePlainNumber(value) {
  let parsed = NaN

  if (typeof value === "number") {
    parsed = Number.isFinite(value) === true ? value : NaN
  } else if (value !== null && value !== undefined) {
    const text = String(value).trim()
    if (text.length > 0) {
      const candidate = Number(text)
      parsed = Number.isFinite(candidate) === true ? candidate : NaN
    }
  }

  return parsed
}

export class MjNumberField extends FormControlMixin(MjElement) {
  static tagName = "mj-number-field";
  static styles = STYLES;
  static watched = [
    "label", "placeholder", "help-text", "error-message", "value",
    "min", "max", "step", "format", "currency-code", "fraction-digits",
    "required", "disabled", "readonly", "no-spinner", "spinner-position", "size", "locale",
    "aria-label", "aria-labelledby"
  ];

  constructor() {
    super()
    this._initFormControl()

    this._rawNumber = NaN

    /* True while the input has focus and shows the editing text. */
    this._editing = false

    /* True when the user left text in the field that is not a number. */
    this._badInput = false

    this._holdTimer = null
    this._holdInterval = null

    /* Form value at the last mj-change, to suppress no-op change events. */
    this._committedValue = ""

    /* The `value` attribute text most recently applied to the control. */
    this._appliedValueAttribute = null

    /* True while an ancestor <fieldset disabled> disables the control. */
    this._formDisabled = false

    /* Errors are shown once the user has left the field or a submit failed. */
    this._showErrors = false

    this._inputId = nextId("mjnf-input")
    this._helpId = nextId("mjnf-help")
    this._errorId = nextId("mjnf-error")
    this._incId = nextId("mjnf-inc")
    this._decId = nextId("mjnf-dec")
  }

  render() {
    const markup = html`
      <label class="label" part="label" for="${this._inputId}"></label>
      <div class="field" part="field">
        <span class="prefix-slot" part="prefix"><slot name="prefix"></slot></span>
        <input
          part="input"
          id="${this._inputId}"
          type="text"
          inputmode="decimal"
          role="spinbutton"
          autocomplete="off"
        />
        <span class="suffix-slot" part="suffix"><slot name="suffix"></slot></span>
        <div class="spinners" part="spinners">
          <button class="spin-btn" part="increment-button" id="${this._incId}" type="button" tabindex="-1" aria-label="${t("mj.numberField.increase")}" aria-controls="${this._inputId}"><span aria-hidden="true">▲</span></button>
          <button class="spin-btn" part="decrement-button" id="${this._decId}" type="button" tabindex="-1" aria-label="${t("mj.numberField.decrease")}" aria-controls="${this._inputId}"><span aria-hidden="true">▼</span></button>
        </div>
      </div>
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
    this._spinners = this.$(".spinners")
    this._incBtn = this.$("[part='increment-button']")
    this._decBtn = this.$("[part='decrement-button']")
    this._helpEl = this.$(".help")
    this._errorEl = this.$(".error")
    this._fieldEl = this.$(".field")

    /* Empty prefix / suffix wrappers take no room (see _syncAffixes). */
    this._syncAffixes()
    const affixSlots = this.$all("[part='prefix'] slot, [part='suffix'] slot")
    for (let index = 0; index < affixSlots.length; index = index + 1) {
      this.listen(affixSlots[index], "slotchange", this._syncAffixes.bind(this))
    }

    /* The shadow DOM is new: nothing in it has focus or bad input yet. */
    this._editing = false
    this._badInput = false

    /* An untouched control still submits its value, as a native one does. */
    this._setFormValue(this._value)
    this._syncAll()

    this.listen(this._input, "focus", this._onFocus.bind(this))
    this.listen(this._input, "blur", this._onBlur.bind(this))
    this.listen(this._input, "input", this._onInput.bind(this))
    this.listen(this._input, "keydown", this._onKeydown.bind(this))

    const buttons = [this._incBtn, this._decBtn]
    for (let index = 0; index < buttons.length; index = index + 1) {
      const button = buttons[index]
      const direction = button === this._incBtn ? 1 : -1
      this.listen(button, "pointerdown", (event) => this._onSpinPointerdown(event, direction))
      this.listen(button, "click", (event) => this._onSpinClick(event, direction))
      this.listen(button, "mousedown", this._onSpinMousedown.bind(this))
      this.listen(button, "pointerup", this._stopHold.bind(this))
      this.listen(button, "pointerleave", this._stopHold.bind(this))
      this.listen(button, "pointercancel", this._stopHold.bind(this))
    }

    this.listen(this, "invalid", this._onInvalid.bind(this))
    this.listen(this, "click", this._onHostClick.bind(this))

    /* A held spinner must not keep stepping a removed element. */
    this.onTeardown(() => {
      this._stopHold()
    })
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

    this._syncAll()
    return
  }

  /* The control is disabled by its own attribute or by a disabled fieldset. */
  _isDisabled() {
    const disabled = this.hasAttribute("disabled") === true || this._formDisabled === true
    return disabled
  }

  _getLocale() {
    let locale = this.getAttribute("locale") || ""
    if (locale.length === 0) {
      locale = document.documentElement.lang || ""
    }
    if (locale.length === 0) {
      locale = navigator.language || "en-US"
    }
    return locale
  }

  /* Build a formatter, falling back to en-US for an unknown locale tag. */
  _createFormatter(options) {
    let formatter = null
    try {
      formatter = new Intl.NumberFormat(this._getLocale(), options)
    } catch (error) {
      formatter = new Intl.NumberFormat("en-US", options)
    }
    return formatter
  }

  /*
   * The display formatter. `percentDecimals` is the number of decimals to
   * keep in percent format, which would otherwise round to whole numbers.
   */
  _getFormatter(percentDecimals) {
    const format = this.getAttribute("format") || "number"
    const fractionDigits = this.getAttribute("fraction-digits")
    const options = {}

    if (format === "currency") {
      options.style = "currency"
      options.currency = this.getAttribute("currency-code") || "USD"
    } else if (format === "percent") {
      options.style = "percent"
      options.maximumFractionDigits = percentDecimals !== undefined ? percentDecimals : 0
    }
    if (fractionDigits !== null) {
      const digits = parseInt(fractionDigits, 10)
      if (Number.isNaN(digits) === false && digits >= 0 && digits <= 20) {
        options.minimumFractionDigits = digits
        options.maximumFractionDigits = digits
      }
    }

    let formatter = null
    try {
      formatter = this._createFormatter(options)
    } catch (error) {
      /* An invalid currency code must not break the field. */
      formatter = this._createFormatter({})
    }
    return formatter
  }

  /* Locale-formatted text shown while the field does not have focus. */
  _formatDisplay(number) {
    let text = ""
    if (Number.isNaN(number) === false) {
      const format = this.getAttribute("format") || "number"
      const displayNumber = format === "percent" ? number / 100 : number
      text = this._getFormatter(countDecimals(number)).format(displayNumber)
    }
    return text
  }

  /*
   * Text shown while the field has focus: the number in the field's locale
   * without grouping, currency or percent decoration, so the caret behaves
   * predictably and `_parseInput` reads back exactly the same number.
   */
  _formatEditing(number) {
    let text = ""
    if (Number.isNaN(number) === false) {
      const formatter = this._createFormatter({ useGrouping: false, maximumFractionDigits: 20 })
      text = formatter.format(number)
    }
    return text
  }

  /* The group and decimal symbols, and the affixes, of the display format. */
  _getNumberSymbols() {
    const symbols = { group: ",", decimal: ".", minus: "-", affixes: [] }

    /* Separators come from a plain decimal format of the same locale. */
    const plainParts = this._createFormatter({}).formatToParts(-1234567.8)
    for (let index = 0; index < plainParts.length; index = index + 1) {
      const part = plainParts[index]
      if (part.type === "group") {
        symbols.group = part.value
      } else if (part.type === "decimal") {
        symbols.decimal = part.value
      } else if (part.type === "minusSign") {
        symbols.minus = part.value
      }
    }

    /* Currency symbols, percent signs and literals of the display format. */
    const displayParts = this._getFormatter().formatToParts(-1234567.8)
    for (let index = 0; index < displayParts.length; index = index + 1) {
      const part = displayParts[index]
      const isAffix = part.type === "currency" || part.type === "percentSign" ||
        part.type === "literal" || part.type === "unit"
      if (isAffix === true && part.value.trim().length > 0) {
        symbols.affixes.push(part.value.trim())
      }
    }
    return symbols
  }

  /*
   * Parse text typed or pasted by the user using the locale's real group
   * and decimal symbols. Group separators (and spaces) are dropped, the
   * decimal symbol becomes ".", currency / percent decoration is ignored.
   * A "." or "," that is not the locale's group symbol is accepted as a
   * decimal separator. Returns NaN for empty or unparseable text.
   */
  _parseInput(text) {
    const symbols = this._getNumberSymbols()
    let remaining = String(text).trim()

    for (let index = 0; index < symbols.affixes.length; index = index + 1) {
      remaining = remaining.split(symbols.affixes[index]).join("")
    }
    remaining = remaining.replace(/%/g, "").trim()

    let digits = ""
    let negative = false
    let seenDecimal = false
    let valid = remaining.length > 0

    for (let index = 0; index < remaining.length && valid === true; index = index + 1) {
      const character = remaining[index]
      const isSpace = /\s/.test(character) === true || character === " " || character === " "
      const isMinus = character === "-" || character === "−" || character === symbols.minus
      const isDecimal = character === symbols.decimal ||
        ((character === "." || character === ",") && character !== symbols.group)

      if (character >= "0" && character <= "9") {
        digits = digits + character
      } else if (isDecimal === true) {
        if (seenDecimal === true) {
          valid = false
        } else {
          seenDecimal = true
          digits = digits + "."
        }
      } else if (character === symbols.group || isSpace === true || character === "'" || character === "’") {
        /* Grouping only: carries no value. */
      } else if (isMinus === true) {
        if (digits.length > 0 || negative === true) {
          valid = false
        } else {
          negative = true
        }
      } else if (character === "+") {
        if (digits.length > 0) {
          valid = false
        }
      } else {
        valid = false
      }
    }

    let number = NaN
    if (valid === true && /[0-9]/.test(digits) === true) {
      number = parseFloat(digits)
      if (negative === true) {
        number = -number
      }
    }
    return number
  }

  _getMin() {
    const min = parsePlainNumber(this.getAttribute("min"))
    return min
  }

  _getMax() {
    const max = parsePlainNumber(this.getAttribute("max"))
    return max
  }

  _clamp(number) {
    const min = this._getMin()
    const max = this._getMax()
    let result = number
    if (Number.isNaN(min) === false) {
      result = Math.max(result, min)
    }
    if (Number.isNaN(max) === false) {
      result = Math.min(result, max)
    }
    return result
  }

  _getStep() {
    let step = parsePlainNumber(this.getAttribute("step"))
    if (Number.isNaN(step) === true || step <= 0) {
      step = 1
    }
    return step
  }

  _syncAll() {
    const label = this.getAttribute("label") || ""
    const placeholder = this.getAttribute("placeholder") || ""
    const helpText = this.getAttribute("help-text") || ""
    const disabled = this._isDisabled()
    const readonly = this.hasAttribute("readonly")
    const required = this.hasAttribute("required")
    const noSpinner = this.hasAttribute("no-spinner")
    const min = this._getMin()
    const max = this._getMax()

    this._labelEl.textContent = label
    this._labelEl.toggleAttribute("data-required", required === true)
    this._fieldEl.toggleAttribute("data-disabled", disabled === true)

    this._input.placeholder = placeholder
    this._input.disabled = disabled
    this._input.readOnly = readonly
    this._input.setAttribute("aria-required", required === true ? "true" : "false")
    this._helpEl.textContent = helpText

    if (Number.isNaN(min) === false) {
      this._input.setAttribute("aria-valuemin", String(min))
    } else {
      this._input.removeAttribute("aria-valuemin")
    }
    if (Number.isNaN(max) === false) {
      this._input.setAttribute("aria-valuemax", String(max))
    } else {
      this._input.removeAttribute("aria-valuemax")
    }

    this._spinners.hidden = noSpinner
    /* "side" (default) or "stacked"; any other value lays out as "side". */
    const spinnerPosition = this.getAttribute("spinner-position") === "stacked" ? "stacked" : "side"
    this._fieldEl.setAttribute("data-spinner-position", spinnerPosition)

    this._syncAccessibleName()
    this._renderNumber()

    /* required / min / max / error-message all feed validity. */
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

  /*
   * Redraw everything derived from `_rawNumber`: the input text (unless the
   * user's unparseable text is being kept for correction), the spinbutton
   * ARIA values and the spinner limits.
   */
  _renderNumber() {
    const number = this._rawNumber

    if (this._badInput === false) {
      const text = this._editing === true ? this._formatEditing(number) : this._formatDisplay(number)
      if (this._input.value !== text) {
        this._input.value = text
      }
    }

    if (Number.isNaN(number) === true) {
      this._input.removeAttribute("aria-valuenow")
      this._input.removeAttribute("aria-valuetext")
    } else {
      this._input.setAttribute("aria-valuenow", String(number))
      this._input.setAttribute("aria-valuetext", this._formatDisplay(number))
    }

    this._updateSpinnerStates()
    return
  }

  _updateSpinnerStates() {
    const min = this._getMin()
    const max = this._getMax()
    const number = this._rawNumber
    const blocked = this._isDisabled() === true || this.hasAttribute("readonly") === true

    const atMin = Number.isNaN(number) === false && Number.isNaN(min) === false && number <= min
    const atMax = Number.isNaN(number) === false && Number.isNaN(max) === false && number >= max

    this._decBtn.toggleAttribute("data-at-limit", atMin === true)
    this._decBtn.setAttribute("aria-disabled", atMin === true || blocked === true ? "true" : "false")
    this._incBtn.toggleAttribute("data-at-limit", atMax === true)
    this._incBtn.setAttribute("aria-disabled", atMax === true || blocked === true ? "true" : "false")

    this._decBtn.disabled = this._isDisabled()
    this._incBtn.disabled = this._isDisabled()
    return
  }

  /* Store a number as the control's value and redraw. NaN means empty. */
  _setNumber(number) {
    this._rawNumber = number
    const formValue = Number.isNaN(number) === true ? "" : String(number)
    this._setFormValue(formValue)

    if (this._input !== undefined && this._input !== null) {
      this._renderNumber()
      this._renderValidity(false)
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
    const number = parsePlainNumber(next)
    this._badInput = false
    this._setNumber(number)
    this._committedValue = this._value
    return
  }

  /*
   * A value change made by the user (typing, keys, spinner): store it and
   * emit `mj-input` and `mj-change` when the value actually changed.
   */
  _commitUserNumber(number) {
    const previous = this._value
    this._badInput = false
    this._setNumber(number)

    if (this._value !== previous) {
      this.emit("mj-input", { value: this._value, valueAsNumber: this._rawNumber })
    }
    if (this._value !== this._committedValue) {
      this._committedValue = this._value
      this.emit("mj-change", { value: this._value, valueAsNumber: this._rawNumber })
    }
    return
  }

  /*
   * Read the text in the input as the user's final answer: a number is
   * clamped and stored, an empty field clears the value, and anything else
   * is kept on screen and reported as invalid.
   */
  _commitText() {
    const text = this._input.value
    const number = this._parseInput(text)

    if (Number.isNaN(number) === false) {
      this._commitUserNumber(this._clamp(number))
    } else if (text.trim().length === 0) {
      this._commitUserNumber(NaN)
    } else {
      this._badInput = true
      this._setNumber(NaN)
      if (this._committedValue !== "") {
        this._committedValue = ""
        this.emit("mj-change", { value: "", valueAsNumber: NaN })
      }
    }
    return
  }

  _onFocus(event) {
    /* A label placed after the field in the document exists by now. */
    this._syncAccessibleName()

    this._editing = true
    this._renderNumber()
    return
  }

  _onBlur(event) {
    this._commitText()
    this._editing = false
    this._renderNumber()

    this._showErrors = true
    this._refreshValidity()
    this._renderValidity(true)
    return
  }

  /*
   * While typing, the form value follows every parseable keystroke so a
   * submit made without leaving the field sends what is on screen. The text
   * itself is not reformatted until the field is left.
   */
  _onInput(event) {
    const text = this._input.value
    const number = this._parseInput(text)

    this._badInput = false
    this._rawNumber = number
    this._setFormValue(Number.isNaN(number) === true ? "" : String(number))

    if (Number.isNaN(number) === true) {
      this._input.removeAttribute("aria-valuenow")
      this._input.removeAttribute("aria-valuetext")
    } else {
      this._input.setAttribute("aria-valuenow", String(number))
      this._input.setAttribute("aria-valuetext", this._formatDisplay(number))
    }
    this._updateSpinnerStates()
    this._renderValidity(false)

    this.emit("mj-input", { value: text, valueAsNumber: number })
    return
  }

  _onKeydown(event) {
    if (this._isDisabled() === true || this.hasAttribute("readonly") === true) {
      return
    }

    const key = event.key

    if (key === "ArrowUp") {
      event.preventDefault()
      this._stepBy(1, 1)
    } else if (key === "ArrowDown") {
      event.preventDefault()
      this._stepBy(-1, 1)
    } else if (key === "PageUp") {
      event.preventDefault()
      this._stepBy(1, PAGE_STEP_MULTIPLIER)
    } else if (key === "PageDown") {
      event.preventDefault()
      this._stepBy(-1, PAGE_STEP_MULTIPLIER)
    } else if (key === "Home") {
      const min = this._getMin()
      if (Number.isNaN(min) === false) {
        event.preventDefault()
        this._commitUserNumber(min)
      }
    } else if (key === "End") {
      const max = this._getMax()
      if (Number.isNaN(max) === false) {
        event.preventDefault()
        this._commitUserNumber(max)
      }
    } else if (key === "Enter") {
      /* Commit in place; keyboard focus stays in the field. */
      this._commitText()
      this._showErrors = true
      this._refreshValidity()
      this._renderValidity(true)
    }
    return
  }

  /*
   * Move the value `multiplier` steps up (direction 1) or down (-1) on the
   * grid that starts at `min` (or 0). A value between two grid points moves
   * to the next point in that direction. The result is rounded to the
   * precision of `step` so 0.1 + 0.2 is stored as 0.3, then clamped.
   */
  _stepBy(direction, multiplier) {
    const step = this._getStep()
    const min = this._getMin()
    const base = Number.isNaN(min) === false ? min : 0
    const precision = Math.max(countDecimals(step), countDecimals(base))

    let next = 0
    if (Number.isNaN(this._rawNumber) === true) {
      /* An empty field counts from zero. */
      next = direction * multiplier * step
    } else {
      const position = (this._rawNumber - base) / step
      const nearest = Math.round(position)
      const onGrid = Math.abs(position - nearest) < 1e-9

      let nextPosition = nearest + direction * multiplier
      if (onGrid === false && direction > 0) {
        nextPosition = Math.ceil(position) + (multiplier - 1)
      } else if (onGrid === false) {
        nextPosition = Math.floor(position) - (multiplier - 1)
      }
      next = base + nextPosition * step
    }

    next = this._clamp(roundToDecimals(next, precision))
    this._commitUserNumber(next)
    return
  }

  /* One spinner step plus its `mj-increment` / `mj-decrement` event. */
  _spin(direction) {
    this._stepBy(direction, 1)
    const eventName = direction > 0 ? "mj-increment" : "mj-decrement"
    this.emit(eventName, { value: this._value, valueAsNumber: this._rawNumber })
    return
  }

  _canSpin() {
    const allowed = this._isDisabled() === false && this.hasAttribute("readonly") === false
    return allowed
  }

  /* Keep focus where it is: pressing a spinner must not blur the input. */
  _onSpinMousedown(event) {
    event.preventDefault()
    return
  }

  _onSpinPointerdown(event, direction) {
    /* Primary button / touch / pen contact only. */
    if (event.button !== 0 || this._canSpin() === false) {
      return
    }

    this._stopHold()
    this._spin(direction)

    this._holdTimer = setTimeout(() => {
      this._holdTimer = null
      this._holdInterval = setInterval(() => {
        this._spin(direction)
      }, HOLD_REPEAT_MS)
    }, HOLD_DELAY_MS)
    return
  }

  /*
   * Keyboard, assistive-technology and scripted activation arrive as a click
   * with `detail` 0. A pointer click (`detail` >= 1) has already stepped on
   * pointerdown.
   */
  _onSpinClick(event, direction) {
    if (event.detail !== 0) {
      return
    }
    if (this._canSpin() === true) {
      this._spin(direction)
    }
    return
  }

  _stopHold() {
    if (this._holdTimer !== null) {
      clearTimeout(this._holdTimer)
      this._holdTimer = null
    }
    if (this._holdInterval !== null) {
      clearInterval(this._holdInterval)
      this._holdInterval = null
    }
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

  /*
   * Unparseable text and range constraints. Unparseable text is reported
   * before the mixin's `required` check so the user is told what is wrong
   * with what they typed rather than that the field is empty.
   */
  _refreshValidity() {
    if (this._badInput === true && this._internals !== null && this._internals !== undefined) {
      const anchor = this._validationAnchor()
      const flags = { badInput: true }
      const message = t("mj.numberField.badInput")
      if (anchor !== null && anchor !== undefined) {
        this._internals.setValidity(flags, message, anchor)
      } else {
        this._internals.setValidity(flags, message)
      }
      return
    }
    super._refreshValidity()
    return
  }

  _customValidity() {
    let message = ""
    const number = this._rawNumber

    if (Number.isNaN(number) === false) {
      const min = this._getMin()
      const max = this._getMax()
      if (Number.isNaN(min) === false && number < min) {
        message = t("mj.numberField.rangeUnderflow", { min: this._formatDisplay(min) })
      } else if (Number.isNaN(max) === false && number > max) {
        message = t("mj.numberField.rangeOverflow", { max: this._formatDisplay(max) })
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
      this._stopHold()
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

  get valueAsNumber() {
    return this._rawNumber
  }

  set valueAsNumber(next) {
    this._applyValue(next)
    return
  }

  get formattedValue() {
    return this._formatDisplay(this._rawNumber)
  }

  focus(options) {
    if (this._input !== undefined && this._input !== null) {
      this._input.focus(options)
    }
    return
  }
}
