/*
 * mjtextfield.js
 *
 * <mj-text-field> -- foundational single-line text entry control.
 * Wraps a native <input type="text"> with label, help, error, prefix/suffix
 * slots, character counter, and clear button.
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
.clear-btn:hover { color: var(--mj-text); }
.clear-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
}
.clear-btn[hidden] { display: none; }

:host([disabled]) .field { opacity: 0.55; pointer-events: none; }
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

export class MjTextField extends FormControlMixin(MjElement) {
  static tagName = "mj-text-field";
  static styles = STYLES;
  static watched = [
    "label", "placeholder", "help-text", "error-message", "value",
    "maxlength", "minlength", "pattern", "required", "disabled",
    "readonly", "clearable", "autocomplete", "inputmode", "variant", "size"
  ];

  constructor() {
    super();
    this._initFormControl();
    this._prevValue = "";
    this._inputId = nextId("mjtf-input");
    this._helpId = nextId("mjtf-help");
    this._errorId = nextId("mjtf-error");
    this._counterId = nextId("mjtf-counter");
  }

  render() {
    const markup = `
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
        <button class="clear-btn" part="clear-button" type="button" aria-label="Clear" hidden></button>
      </div>
      <div class="below">
        <span>
          <span class="help" part="help" id="${this._helpId}" role="status"></span>
          <span class="error" part="error" id="${this._errorId}" role="alert"></span>
        </span>
        <span class="counter" part="counter" id="${this._counterId}" role="status" aria-live="polite" hidden></span>
      </div>
    `;
    return markup;
  }

  afterRender() {
    this._input = this.$("input");
    this._labelEl = this.$(".label");
    this._helpEl = this.$(".help");
    this._errorEl = this.$(".error");
    this._counterEl = this.$(".counter");
    this._clearBtn = this.$(".clear-btn");
    this._fieldEl = this.$(".field");

    this._syncAll();

    this.listen(this._input, "input", this._onInput.bind(this));
    this.listen(this._input, "change", this._onChange.bind(this));
    this.listen(this._input, "blur", this._onBlur.bind(this));
    this.listen(this._clearBtn, "click", this._onClear.bind(this));
    return;
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._input === undefined) {
      return;
    }
    this._syncAll();
    return;
  }

  _syncAll() {
    const label = this.getAttribute("label") || "";
    const placeholder = this.getAttribute("placeholder") || "";
    const helpText = this.getAttribute("help-text") || "";
    const errorMsg = this.getAttribute("error-message") || "";
    const maxlength = this.getAttribute("maxlength");
    const minlength = this.getAttribute("minlength");
    const pattern = this.getAttribute("pattern");
    const autocomplete = this.getAttribute("autocomplete") || "on";
    const inputmode = this.getAttribute("inputmode") || "text";
    const disabled = this.hasAttribute("disabled");
    const readonly = this.hasAttribute("readonly");
    const required = this.hasAttribute("required");
    const clearable = this.hasAttribute("clearable");

    this._labelEl.textContent = label;
    this._input.placeholder = placeholder;
    this._input.autocomplete = autocomplete;
    this._input.inputMode = inputmode;
    this._input.disabled = disabled;
    this._input.readOnly = readonly;
    this._input.required = required;
    this._input.setAttribute("aria-required", required ? "true" : "false");

    if (maxlength !== null) {
      this._input.setAttribute("maxlength", maxlength);
    } else {
      this._input.removeAttribute("maxlength");
    }
    if (minlength !== null) {
      this._input.setAttribute("minlength", minlength);
    } else {
      this._input.removeAttribute("minlength");
    }
    if (pattern !== null) {
      this._input.setAttribute("pattern", pattern);
    } else {
      this._input.removeAttribute("pattern");
    }

    this._helpEl.textContent = helpText;
    this._errorEl.textContent = errorMsg;
    this._updateDescribedBy();
    this._updateCounter();

    const hasValue = this._input.value.length > 0;
    const showClear = clearable === true && hasValue && !readonly && !disabled;
    this._clearBtn.hidden = !showClear;
    return;
  }

  _updateDescribedBy() {
    const ids = [];
    if (this._helpEl.textContent.length > 0) {
      ids.push(this._helpId);
    }
    const hasError = this._errorEl.hasAttribute("data-visible");
    if (hasError) {
      ids.push(this._errorId);
    }
    if (ids.length > 0) {
      this._input.setAttribute("aria-describedby", ids.join(" "));
    } else {
      this._input.removeAttribute("aria-describedby");
    }
    return;
  }

  _updateCounter() {
    const maxlength = this.getAttribute("maxlength");
    if (maxlength === null) {
      this._counterEl.hidden = true;
      return;
    }
    this._counterEl.hidden = false;
    const current = this._input.value.length;
    this._counterEl.textContent = `${current}/${maxlength}`;
    return;
  }

  _onInput(event) {
    const val = this._input.value;
    this._setFormValue(val);
    this._updateCounter();
    const clearable = this.hasAttribute("clearable");
    const readonly = this.hasAttribute("readonly");
    const disabled = this.hasAttribute("disabled");
    this._clearBtn.hidden = !(clearable && val.length > 0 && !readonly && !disabled);
    this.emit("mj-input", { value: val });
    return;
  }

  _onChange(event) {
    const val = this._input.value;
    if (val !== this._prevValue) {
      this._prevValue = val;
      this.emit("mj-change", { value: val });
    }
    return;
  }

  _onBlur(event) {
    this._runValidation();
    return;
  }

  _onClear(event) {
    const prev = this._input.value;
    this._input.value = "";
    this._setFormValue("");
    this._clearBtn.hidden = true;
    this._updateCounter();
    this.emit("mj-clear", { previousValue: prev });
    this.emit("mj-change", { value: "" });
    this._input.focus();
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
    this._updateDescribedBy();
    return;
  }

  _validationAnchor() {
    return this._input;
  }

  onFormReset(initial) {
    if (this._input !== undefined) {
      this._input.value = initial;
      this._updateCounter();
      this._errorEl.removeAttribute("data-visible");
      this._fieldEl.removeAttribute("data-invalid");
      this._input.setAttribute("aria-invalid", "false");
    }
    return;
  }

  get value() {
    return this._value;
  }

  set value(next) {
    this._setFormValue(next);
    if (this._input !== undefined) {
      this._input.value = next;
      this._updateCounter();
    }
    return;
  }

  get disabled() {
    return this.hasAttribute("disabled");
  }

  set disabled(val) {
    this.reflectBoolean("disabled", val === true);
    return;
  }

  focus() {
    if (this._input !== undefined) {
      this._input.focus();
    }
    return;
  }
}
