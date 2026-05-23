/*
 * mjnumberfield.js
 *
 * <mj-number-field> -- numeric / currency / percentage input with
 * locale-aware display formatting, increment/decrement spinner buttons,
 * and hold-to-repeat behavior.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { FormControlMixin } from "../core/forminternals.js";

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
.spin-btn[data-at-limit] { opacity: 0.4; pointer-events: none; }
.spin-btn + .spin-btn { border-top: 1px solid var(--mj-border); }

.below { margin-top: var(--mj-space-1); }
.help { font-size: var(--mj-font-size-sm); color: var(--mj-text-muted); }
.help:empty { display: none; }
.error { font-size: var(--mj-font-size-sm); color: var(--mj-color-danger); display: none; }
.error[data-visible] { display: block; }

:host([disabled]) .field { opacity: 0.55; pointer-events: none; }
`;

export class MjNumberField extends FormControlMixin(MjElement) {
  static tagName = "mj-number-field";
  static styles = STYLES;
  static watched = [
    "label", "placeholder", "help-text", "error-message", "value",
    "min", "max", "step", "format", "currency-code", "fraction-digits",
    "required", "disabled", "readonly", "no-spinner", "spinner-position", "size", "locale"
  ];

  constructor() {
    super();
    this._initFormControl();
    this._rawNumber = NaN;
    this._editing = false;
    this._holdTimer = null;
    this._holdInterval = null;
    this._prevValue = "";
    this._inputId = nextId("mjnf-input");
    this._helpId = nextId("mjnf-help");
    this._errorId = nextId("mjnf-error");
    this._incId = nextId("mjnf-inc");
    this._decId = nextId("mjnf-dec");
  }

  render() {
    const markup = `
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
          <button class="spin-btn" part="increment-button" id="${this._incId}" type="button" aria-label="Increase" aria-controls="${this._inputId}">▲</button>
          <button class="spin-btn" part="decrement-button" id="${this._decId}" type="button" aria-label="Decrease" aria-controls="${this._inputId}">▼</button>
        </div>
      </div>
      <div class="below">
        <span class="help" part="help" id="${this._helpId}"></span>
        <span class="error" part="error" id="${this._errorId}" role="alert"></span>
      </div>
    `;
    return markup;
  }

  afterRender() {
    this._input = this.$("input");
    this._labelEl = this.$(".label");
    this._spinners = this.$(".spinners");
    this._incBtn = this.$("[part='increment-button']");
    this._decBtn = this.$("[part='decrement-button']");
    this._helpEl = this.$(".help");
    this._errorEl = this.$(".error");
    this._fieldEl = this.$(".field");

    this._syncAll();

    this.listen(this._input, "focus", this._onFocus.bind(this));
    this.listen(this._input, "blur", this._onBlur.bind(this));
    this.listen(this._input, "input", this._onInput.bind(this));
    this.listen(this._input, "keydown", this._onKeydown.bind(this));
    this.listen(this._incBtn, "pointerdown", this._onIncStart.bind(this));
    this.listen(this._decBtn, "pointerdown", this._onDecStart.bind(this));
    this.listen(this._incBtn, "pointerup", this._onSpinEnd.bind(this));
    this.listen(this._decBtn, "pointerup", this._onSpinEnd.bind(this));
    this.listen(this._incBtn, "pointerleave", this._onSpinEnd.bind(this));
    this.listen(this._decBtn, "pointerleave", this._onSpinEnd.bind(this));
    return;
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._input === undefined) {
      return;
    }
    this._syncAll();
    return;
  }

  _getLocale() {
    const locale = this.getAttribute("locale") || "";
    if (locale.length > 0) {
      return locale;
    }
    const docLang = document.documentElement.lang;
    if (docLang.length > 0) {
      return docLang;
    }
    return navigator.language || "en-US";
  }

  _getFormatter() {
    const format = this.getAttribute("format") || "number";
    const locale = this._getLocale();
    const fractionDigits = this.getAttribute("fraction-digits");
    const options = {};

    if (format === "currency") {
      options.style = "currency";
      options.currency = this.getAttribute("currency-code") || "USD";
    } else if (format === "percent") {
      options.style = "percent";
    }
    if (fractionDigits !== null) {
      const fd = parseInt(fractionDigits, 10);
      options.minimumFractionDigits = fd;
      options.maximumFractionDigits = fd;
    }
    return new Intl.NumberFormat(locale, options);
  }

  _formatDisplay(num) {
    if (isNaN(num)) {
      return "";
    }
    const format = this.getAttribute("format") || "number";
    let displayNum = num;
    if (format === "percent") {
      displayNum = num / 100;
    }
    return this._getFormatter().format(displayNum);
  }

  _parseInput(str) {
    if (str.trim() === "") {
      return NaN;
    }
    const cleaned = str.replace(/[^0-9.,\-+]/g, "").replace(",", ".");
    const num = parseFloat(cleaned);
    return num;
  }

  _clamp(num) {
    const min = this.getAttribute("min");
    const max = this.getAttribute("max");
    let result = num;
    if (min !== null) {
      result = Math.max(result, parseFloat(min));
    }
    if (max !== null) {
      result = Math.min(result, parseFloat(max));
    }
    return result;
  }

  _getStep() {
    const step = parseFloat(this.getAttribute("step") || "1");
    if (step <= 0 || isNaN(step)) {
      return 1;
    }
    return step;
  }

  _syncAll() {
    const label = this.getAttribute("label") || "";
    const placeholder = this.getAttribute("placeholder") || "";
    const helpText = this.getAttribute("help-text") || "";
    const disabled = this.hasAttribute("disabled");
    const readonly = this.hasAttribute("readonly");
    const required = this.hasAttribute("required");
    const noSpinner = this.hasAttribute("no-spinner");
    const min = this.getAttribute("min");
    const max = this.getAttribute("max");

    this._labelEl.textContent = label;
    this._input.placeholder = placeholder;
    this._input.disabled = disabled;
    this._input.readOnly = readonly;
    this._input.setAttribute("aria-required", required ? "true" : "false");
    this._helpEl.textContent = helpText;

    if (min !== null) {
      this._input.setAttribute("aria-valuemin", min);
    } else {
      this._input.removeAttribute("aria-valuemin");
    }
    if (max !== null) {
      this._input.setAttribute("aria-valuemax", max);
    } else {
      this._input.removeAttribute("aria-valuemax");
    }

    this._spinners.hidden = noSpinner;

    if (!this._editing && !isNaN(this._rawNumber)) {
      this._input.value = this._formatDisplay(this._rawNumber);
    }

    this._updateSpinnerStates();
    return;
  }

  _updateSpinnerStates() {
    const min = this.getAttribute("min");
    const max = this.getAttribute("max");
    const num = this._rawNumber;

    if (!isNaN(num)) {
      if (min !== null && num <= parseFloat(min)) {
        this._decBtn.setAttribute("data-at-limit", "");
        this._decBtn.setAttribute("aria-disabled", "true");
      } else {
        this._decBtn.removeAttribute("data-at-limit");
        this._decBtn.setAttribute("aria-disabled", "false");
      }
      if (max !== null && num >= parseFloat(max)) {
        this._incBtn.setAttribute("data-at-limit", "");
        this._incBtn.setAttribute("aria-disabled", "true");
      } else {
        this._incBtn.removeAttribute("data-at-limit");
        this._incBtn.setAttribute("aria-disabled", "false");
      }
    }
    return;
  }

  _applyValue(num) {
    this._rawNumber = num;
    const strVal = isNaN(num) ? "" : String(num);
    this._setFormValue(strVal);
    this._input.setAttribute("aria-valuenow", isNaN(num) ? "" : String(num));
    this._input.setAttribute("aria-valuetext", this._formatDisplay(num));
    this._updateSpinnerStates();
    return;
  }

  _onFocus(event) {
    this._editing = true;
    if (!isNaN(this._rawNumber)) {
      this._input.value = String(this._rawNumber);
    }
    return;
  }

  _onBlur(event) {
    this._editing = false;
    const num = this._parseInput(this._input.value);

    if (!isNaN(num)) {
      const clamped = this._clamp(num);
      this._applyValue(clamped);
      this._input.value = this._formatDisplay(clamped);
      if (String(clamped) !== this._prevValue) {
        this._prevValue = String(clamped);
        this.emit("mj-change", { value: String(clamped), valueAsNumber: clamped });
      }
    } else if (this._input.value.trim() !== "") {
      this._input.value = "";
    }

    this._runValidation();
    return;
  }

  _onInput(event) {
    const num = this._parseInput(this._input.value);
    this.emit("mj-input", { value: this._input.value, valueAsNumber: num });
    return;
  }

  _onKeydown(event) {
    const step = this._getStep();
    const key = event.key;

    if (key === "ArrowUp") {
      event.preventDefault();
      this._step(step);
      return;
    }
    if (key === "ArrowDown") {
      event.preventDefault();
      this._step(-step);
      return;
    }
    if (key === "PageUp") {
      event.preventDefault();
      this._step(step * 10);
      return;
    }
    if (key === "PageDown") {
      event.preventDefault();
      this._step(-step * 10);
      return;
    }
    if (key === "Home") {
      const min = this.getAttribute("min");
      if (min !== null) {
        event.preventDefault();
        this._step(parseFloat(min) - this._rawNumber);
      }
      return;
    }
    if (key === "End") {
      const max = this.getAttribute("max");
      if (max !== null) {
        event.preventDefault();
        this._step(parseFloat(max) - this._rawNumber);
      }
      return;
    }
    if (key === "Enter") {
      this._input.blur();
      return;
    }
    return;
  }

  _step(delta) {
    const current = isNaN(this._rawNumber) ? 0 : this._rawNumber;
    const next = this._clamp(current + delta);
    this._applyValue(next);
    this._input.value = this._formatDisplay(next);
    return;
  }

  _onIncStart(event) {
    if (this.hasAttribute("disabled") || this.hasAttribute("readonly")) {
      return;
    }
    const step = this._getStep();
    this._step(step);
    this.emit("mj-increment", { value: String(this._rawNumber), valueAsNumber: this._rawNumber });
    this._holdTimer = setTimeout(() => {
      this._holdInterval = setInterval(() => {
        this._step(step);
        this.emit("mj-increment", { value: String(this._rawNumber), valueAsNumber: this._rawNumber });
      }, 100);
    }, 600);
    return;
  }

  _onDecStart(event) {
    if (this.hasAttribute("disabled") || this.hasAttribute("readonly")) {
      return;
    }
    const step = this._getStep();
    this._step(-step);
    this.emit("mj-decrement", { value: String(this._rawNumber), valueAsNumber: this._rawNumber });
    this._holdTimer = setTimeout(() => {
      this._holdInterval = setInterval(() => {
        this._step(-step);
        this.emit("mj-decrement", { value: String(this._rawNumber), valueAsNumber: this._rawNumber });
      }, 100);
    }, 600);
    return;
  }

  _onSpinEnd(event) {
    if (this._holdTimer !== null) {
      clearTimeout(this._holdTimer);
      this._holdTimer = null;
    }
    if (this._holdInterval !== null) {
      clearInterval(this._holdInterval);
      this._holdInterval = null;
    }
    return;
  }

  _runValidation() {
    this._refreshValidity();
    const msg = this.validationMessage;
    const overrideMsg = this.getAttribute("error-message") || "";
    const displayMsg = overrideMsg.length > 0 ? overrideMsg : msg;

    if (displayMsg.length > 0) {
      this._errorEl.textContent = displayMsg;
      this._errorEl.setAttribute("data-visible", "");
      this._fieldEl.setAttribute("data-invalid", "");
      this._input.setAttribute("aria-invalid", "true");
      this.emit("mj-invalid", { validationMessage: displayMsg });
    } else {
      this._errorEl.removeAttribute("data-visible");
      this._fieldEl.removeAttribute("data-invalid");
      this._input.setAttribute("aria-invalid", "false");
    }
    return;
  }

  _validationAnchor() {
    return this._input;
  }

  onFormReset(initial) {
    if (this._input !== undefined) {
      const num = this._parseInput(initial);
      this._rawNumber = isNaN(num) ? NaN : num;
      this._input.value = isNaN(num) ? "" : this._formatDisplay(num);
      this._errorEl.removeAttribute("data-visible");
      this._fieldEl.removeAttribute("data-invalid");
      this._input.setAttribute("aria-invalid", "false");
    }
    return;
  }

  get valueAsNumber() {
    return this._rawNumber;
  }

  get formattedValue() {
    return this._formatDisplay(this._rawNumber);
  }

  focus() {
    if (this._input !== undefined) {
      this._input.focus();
    }
    return;
  }
}
