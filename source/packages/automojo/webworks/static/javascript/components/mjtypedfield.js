/*
 * mjtypedfield.js
 *
 * <mj-typed-field> -- typed text field for email, URL, and telephone inputs
 * with type-appropriate inputmode, autocomplete, and validation messages.
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

:host([disabled]) .field { opacity: 0.55; pointer-events: none; }
`;

const TYPE_CONFIG = {
  email: { inputmode: "email", autocomplete: "email", hint: "user@example.com" },
  url:   { inputmode: "url",   autocomplete: "url",   hint: "https://example.com" },
  tel:   { inputmode: "tel",   autocomplete: "tel",   hint: "+1 (555) 000-0000" }
};

const TYPE_MISMATCH_MSGS = {
  email: "Please enter a valid email address.",
  url:   "Please enter a valid URL (e.g., https://example.com).",
  tel:   "Please enter a valid telephone number."
};

export class MjTypedField extends FormControlMixin(MjElement) {
  static tagName = "mj-typed-field";
  static styles = STYLES;
  static watched = [
    "type", "label", "placeholder", "help-text", "error-message", "value",
    "required", "disabled", "readonly", "multiple", "maxlength", "minlength",
    "autocomplete", "show-format-hint", "format-hint", "size"
  ];

  constructor() {
    super();
    this._initFormControl();
    this._prevValue = "";
    this._prevType = null;
    this._inputId = nextId("mjtf2-input");
    this._helpId = nextId("mjtf2-help");
    this._errorId = nextId("mjtf2-error");
    this._hintId = nextId("mjtf2-hint");
  }

  render() {
    const markup = `
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
    `;
    return markup;
  }

  afterRender() {
    this._input = this.$("input");
    this._labelEl = this.$(".label");
    this._formatHint = this.$(".format-hint");
    this._helpEl = this.$(".help");
    this._errorEl = this.$(".error");
    this._fieldEl = this.$(".field");

    this._syncAll();

    this.listen(this._input, "input", this._onInput.bind(this));
    this.listen(this._input, "change", this._onChange.bind(this));
    this.listen(this._input, "blur", this._onBlur.bind(this));
    this.listen(this._input, "focus", this._onFocus.bind(this));
    return;
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._input === undefined) {
      return;
    }
    if (name === "type" && oldValue !== newValue && this._prevType !== null) {
      this._input.value = "";
      this._setFormValue("");
      this.emit("mj-change", { value: "" });
    }
    this._syncAll();
    return;
  }

  _syncAll() {
    const type = this.getAttribute("type") || "email";
    const config = TYPE_CONFIG[type] || TYPE_CONFIG.email;
    const label = this.getAttribute("label") || "";
    const placeholder = this.getAttribute("placeholder") || "";
    const helpText = this.getAttribute("help-text") || "";
    const disabled = this.hasAttribute("disabled");
    const readonly = this.hasAttribute("readonly");
    const required = this.hasAttribute("required");
    const multiple = this.hasAttribute("multiple") && type === "email";
    const maxlength = this.getAttribute("maxlength");
    const minlength = this.getAttribute("minlength");
    const autocomplete = this.getAttribute("autocomplete") || config.autocomplete;
    const formatHintText = this.getAttribute("format-hint") || config.hint;
    const showFormatHint = this.hasAttribute("show-format-hint");

    this._prevType = type;

    this._input.type = type;
    this._input.inputMode = config.inputmode;
    this._input.autocomplete = autocomplete;
    this._input.placeholder = placeholder;
    this._input.disabled = disabled;
    this._input.readOnly = readonly;
    this._input.required = required;
    this._input.multiple = multiple;
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

    this._labelEl.textContent = label;
    this._helpEl.textContent = helpText;
    this._formatHint.textContent = formatHintText;

    if (!showFormatHint) {
      this._formatHint.removeAttribute("data-visible");
    }

    this._updateDescribedBy(false);
    return;
  }

  _updateDescribedBy(hintVisible) {
    const ids = [];
    if (this._helpEl.textContent.length > 0) {
      ids.push(this._helpId);
    }
    if (hintVisible && this.hasAttribute("show-format-hint")) {
      ids.push(this._hintId);
    }
    if (this._errorEl.hasAttribute("data-visible")) {
      ids.push(this._errorId);
    }
    if (ids.length > 0) {
      this._input.setAttribute("aria-describedby", ids.join(" "));
    } else {
      this._input.removeAttribute("aria-describedby");
    }
    return;
  }

  _onFocus(event) {
    if (this.hasAttribute("show-format-hint")) {
      this._formatHint.setAttribute("data-visible", "");
      this._updateDescribedBy(true);
    }
    return;
  }

  _onInput(event) {
    const val = this._input.value;
    this._setFormValue(val);
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
    if (this.hasAttribute("show-format-hint")) {
      this._formatHint.removeAttribute("data-visible");
      this._updateDescribedBy(false);
    }
    this._runValidation();
    return;
  }

  _runValidation() {
    this._refreshValidity();
    const type = this.getAttribute("type") || "email";
    let msg = this.validationMessage;

    if (this._internals !== null && this._internals.validity.typeMismatch) {
      msg = TYPE_MISMATCH_MSGS[type] || msg;
    }

    const overrideMsg = this.getAttribute("error-message") || "";
    const displayMsg = overrideMsg.length > 0 ? overrideMsg : msg;

    if (displayMsg.length > 0) {
      this._errorEl.textContent = displayMsg;
      this._errorEl.setAttribute("data-visible", "");
      this._fieldEl.setAttribute("data-invalid", "");
      this._input.setAttribute("aria-invalid", "true");
      this.emit("mj-invalid", {
        validationMessage: displayMsg,
        validityState: this._internals !== null ? this._internals.validity : null
      });
    } else {
      this._errorEl.removeAttribute("data-visible");
      this._fieldEl.removeAttribute("data-invalid");
      this._input.setAttribute("aria-invalid", "false");
    }
    this._updateDescribedBy(false);
    return;
  }

  _customValidity() {
    const type = this.getAttribute("type") || "email";
    if (this._input !== undefined && this._input.validity.typeMismatch) {
      return TYPE_MISMATCH_MSGS[type] || "";
    }
    return "";
  }

  _validationAnchor() {
    return this._input;
  }

  onFormReset(initial) {
    if (this._input !== undefined) {
      this._input.value = initial;
      this._errorEl.removeAttribute("data-visible");
      this._fieldEl.removeAttribute("data-invalid");
      this._input.setAttribute("aria-invalid", "false");
    }
    return;
  }

  focus() {
    if (this._input !== undefined) {
      this._input.focus();
    }
    return;
  }
}
