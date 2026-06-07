/*
 * mjmaskedinput.js
 *
 * <mj-masked-input> -- pattern-constrained text input with auto-caret
 * advancement, ghost overlay, and raw/formatted value exposure.
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
  position: relative;
  transition: border-color var(--mj-motion-fast) var(--mj-motion-ease);
  overflow: hidden;
  font-family: var(--mj-font-mono);
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

.input-wrap {
  flex: 1;
  position: relative;
  min-width: 0;
}

.mask-overlay {
  position: absolute;
  inset: 0;
  padding: 0 var(--mj-space-3);
  display: flex;
  align-items: center;
  pointer-events: none;
  color: var(--mj-text-muted);
  font-family: inherit;
  white-space: pre;
  overflow: hidden;
}
.mask-overlay[hidden] { display: none; }

input {
  position: relative;
  width: 100%;
  height: 100%;
  padding: 0 var(--mj-space-3);
  font: inherit;
  color: var(--mj-text);
  background: transparent;
  border: none;
  outline: none;
  font-family: inherit;
}
input::placeholder { color: var(--mj-text-muted); }
input:disabled { cursor: not-allowed; }

.below { margin-top: var(--mj-space-1); }
.help { font-size: var(--mj-font-size-sm); color: var(--mj-text-muted); }
.help:empty { display: none; }
.error { font-size: var(--mj-font-size-sm); color: var(--mj-color-danger); display: none; }
.error[data-visible] { display: block; }

:host([disabled]) .field { opacity: 0.55; pointer-events: none; }
`;

export class MjMaskedInput extends FormControlMixin(MjElement) {
  static tagName = "mj-masked-input";
  static styles = STYLES;
  static watched = [
    "mask", "label", "help-text", "error-message", "value",
    "placeholder-char", "mode", "show-mask",
    "required", "disabled", "readonly", "inputmode", "autocomplete", "size"
  ];

  constructor() {
    super();
    this._initFormControl();
    this._maskParts = [];
    this._prevValue = "";
    this._inputId = nextId("mjmi-input");
    this._helpId = nextId("mjmi-help");
    this._errorId = nextId("mjmi-error");
  }

  render() {
    const markup = `
      <label class="label" part="label" for="${this._inputId}"></label>
      <div class="field" part="field">
        <span class="prefix" part="prefix"><slot name="prefix"></slot></span>
        <div class="input-wrap">
          <span class="mask-overlay" part="mask-overlay" aria-hidden="true" hidden></span>
          <input part="input" id="${this._inputId}" type="text" autocomplete="off" />
        </div>
        <span class="suffix" part="suffix"><slot name="suffix"></slot></span>
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
    this._maskOverlay = this.$(".mask-overlay");
    this._helpEl = this.$(".help");
    this._errorEl = this.$(".error");
    this._fieldEl = this.$(".field");

    this._parseMask();
    this._syncAll();

    this.listen(this._input, "keydown", this._onKeydown.bind(this));
    this.listen(this._input, "input", this._onInputEvent.bind(this));
    this.listen(this._input, "paste", this._onPaste.bind(this));
    this.listen(this._input, "blur", this._onBlur.bind(this));
    return;
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._input === undefined) {
      return;
    }
    if (name === "mask") {
      this._parseMask();
    }
    this._syncAll();
    return;
  }

  _parseMask() {
    const mask = this.getAttribute("mask") || "";
    this._maskParts = [];
    for (let i = 0; i < mask.length; i = i + 1) {
      const ch = mask[i];
      if (ch === "9") {
        this._maskParts.push({ type: "digit", literal: null });
      } else if (ch === "a") {
        this._maskParts.push({ type: "letter", literal: null });
      } else if (ch === "*") {
        this._maskParts.push({ type: "alnum", literal: null });
      } else {
        this._maskParts.push({ type: "literal", literal: ch });
      }
    }
    if (this._maskParts.length === 0 && mask.length > 0) {
      console.warn("[mj-masked-input] mask contains no editable positions");
    }
    return;
  }

  _syncAll() {
    const label = this.getAttribute("label") || "";
    const helpText = this.getAttribute("help-text") || "";
    const disabled = this.hasAttribute("disabled");
    const readonly = this.hasAttribute("readonly");
    const required = this.hasAttribute("required");
    const inputmode = this.getAttribute("inputmode") || this._deriveInputmode();
    const autocomplete = this.getAttribute("autocomplete") || "off";
    const showMask = this.hasAttribute("show-mask");

    this._labelEl.textContent = label;
    this._input.disabled = disabled;
    this._input.readOnly = readonly;
    this._input.inputMode = inputmode;
    this._input.autocomplete = autocomplete;
    this._input.setAttribute("aria-required", required ? "true" : "false");
    this._input.setAttribute("maxlength", String(this._maskParts.length));

    this._helpEl.textContent = helpText;
    this._maskOverlay.hidden = !showMask;
    this._updateOverlay();

    const ids = [];
    if (helpText.length > 0) {
      ids.push(this._helpId);
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

  _deriveInputmode() {
    const allDigits = this._maskParts.every(p => p.type === "digit" || p.type === "literal");
    return allDigits ? "numeric" : "text";
  }

  _charMatchesMask(ch, type) {
    if (type === "digit") {
      return /\d/.test(ch);
    }
    if (type === "letter") {
      return /[a-zA-Z]/.test(ch);
    }
    if (type === "alnum") {
      return /[a-zA-Z0-9]/.test(ch);
    }
    return false;
  }

  _onKeydown(event) {
    const key = event.key;
    if (key === "Backspace") {
      event.preventDefault();
      this._handleBackspace();
      return;
    }
    if (key === "Delete") {
      event.preventDefault();
      this._handleDelete();
      return;
    }
    if (key.length === 1 && !event.ctrlKey && !event.metaKey) {
      event.preventDefault();
      this._handleChar(key);
      return;
    }
    return;
  }

  _onInputEvent(event) {
    const val = this._input.value;
    this._applyFormatted(val);
    return;
  }

  _onPaste(event) {
    event.preventDefault();
    const text = event.clipboardData !== null ? event.clipboardData.getData("text/plain") : "";
    this._insertPasted(text);
    return;
  }

  _onBlur(event) {
    const mode = this.getAttribute("mode") || "eager";
    if (mode === "lazy") {
      this._applyFormatted(this._input.value);
    }
    this._runValidation();
    if (this._input.value !== this._prevValue) {
      this._prevValue = this._input.value;
      this.emit("mj-change", { value: this._input.value, rawValue: this.rawValue, complete: this.complete });
    }
    return;
  }

  _handleChar(ch) {
    const pos = this._input.selectionStart;
    const cur = this._input.value;
    let insertPos = pos;

    while (insertPos < this._maskParts.length && this._maskParts[insertPos].type === "literal") {
      insertPos = insertPos + 1;
    }

    if (insertPos >= this._maskParts.length) {
      return;
    }

    const part = this._maskParts[insertPos];
    if (!this._charMatchesMask(ch, part.type)) {
      return;
    }

    const chars = cur.split("");
    while (chars.length <= insertPos) {
      const mp = this._maskParts[chars.length];
      chars.push(mp.type === "literal" ? mp.literal : (this.getAttribute("placeholder-char") || "_"));
    }
    chars[insertPos] = ch;

    let newPos = insertPos + 1;
    while (newPos < this._maskParts.length && this._maskParts[newPos].type === "literal") {
      if (chars.length <= newPos) {
        chars.push(this._maskParts[newPos].literal);
      }
      newPos = newPos + 1;
    }

    const formatted = this._buildFormatted(chars.join(""));
    this._input.value = formatted;
    this._input.setSelectionRange(newPos, newPos);
    this._commitFormatted(formatted);
    return;
  }

  _handleBackspace() {
    let pos = this._input.selectionStart;
    const cur = this._input.value;

    while (pos > 0 && this._maskParts[pos - 1] !== undefined && this._maskParts[pos - 1].type === "literal") {
      pos = pos - 1;
    }
    if (pos <= 0) {
      return;
    }
    pos = pos - 1;
    const chars = cur.split("");
    chars[pos] = this.getAttribute("placeholder-char") || "_";
    const formatted = this._buildFormatted(chars.join(""));
    this._input.value = formatted;
    this._input.setSelectionRange(pos, pos);
    this._commitFormatted(formatted);
    return;
  }

  _handleDelete() {
    const pos = this._input.selectionStart;
    if (pos >= this._maskParts.length) {
      return;
    }
    const cur = this._input.value;
    const chars = cur.split("");
    let delPos = pos;
    while (delPos < this._maskParts.length && this._maskParts[delPos].type === "literal") {
      delPos = delPos + 1;
    }
    if (delPos < chars.length) {
      chars[delPos] = this.getAttribute("placeholder-char") || "_";
    }
    const formatted = this._buildFormatted(chars.join(""));
    this._input.value = formatted;
    this._input.setSelectionRange(pos, pos);
    this._commitFormatted(formatted);
    return;
  }

  _insertPasted(text) {
    let pos = this._input.selectionStart;
    const chars = this._input.value.split("");
    let ci = 0;

    while (pos < this._maskParts.length && ci < text.length) {
      while (pos < this._maskParts.length && this._maskParts[pos].type === "literal") {
        pos = pos + 1;
      }
      if (pos >= this._maskParts.length) {
        break;
      }
      const part = this._maskParts[pos];
      const ch = text[ci];
      ci = ci + 1;
      if (this._charMatchesMask(ch, part.type)) {
        while (chars.length <= pos) {
          const mp = this._maskParts[chars.length];
          chars.push(mp.type === "literal" ? mp.literal : (this.getAttribute("placeholder-char") || "_"));
        }
        chars[pos] = ch;
        pos = pos + 1;
      }
    }

    const formatted = this._buildFormatted(chars.join(""));
    this._input.value = formatted;
    this._input.setSelectionRange(pos, pos);
    this._commitFormatted(formatted);
    return;
  }

  _buildFormatted(raw) {
    const placeholderChar = this.getAttribute("placeholder-char") || "_";
    const result = [];
    for (let i = 0; i < this._maskParts.length; i = i + 1) {
      const part = this._maskParts[i];
      if (part.type === "literal") {
        result.push(part.literal);
      } else {
        const ch = raw[i] || placeholderChar;
        result.push(ch);
      }
    }
    return result.join("").replace(new RegExp(`[${placeholderChar}]+$`), "");
  }

  _applyFormatted(raw) {
    const formatted = this._buildFormatted(raw);
    if (this._input.value !== formatted) {
      this._input.value = formatted;
    }
    this._commitFormatted(formatted);
    return;
  }

  _commitFormatted(formatted) {
    this._setFormValue(formatted);
    this._updateOverlay();
    const wasComplete = this.complete;
    this.emit("mj-input", { value: formatted, rawValue: this.rawValue, complete: wasComplete });
    if (wasComplete) {
      this.emit("mj-complete", { value: formatted, rawValue: this.rawValue });
    }
    return;
  }

  _updateOverlay() {
    if (!this.hasAttribute("show-mask")) {
      return;
    }
    const placeholderChar = this.getAttribute("placeholder-char") || "_";
    const current = this._input.value;
    let overlay = "";
    for (let i = 0; i < this._maskParts.length; i = i + 1) {
      const part = this._maskParts[i];
      if (part.type === "literal") {
        overlay = overlay + part.literal;
      } else if (i < current.length) {
        overlay = overlay + " ";
      } else {
        overlay = overlay + placeholderChar;
      }
    }
    this._maskOverlay.textContent = overlay;
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

  _customValidity() {
    const required = this.hasAttribute("required");
    if (!this.complete && required) {
      return "Please complete the required format.";
    }
    return "";
  }

  _validationAnchor() {
    return this._input;
  }

  onFormReset(initial) {
    if (this._input !== undefined) {
      this._applyFormatted(initial);
      this._errorEl.removeAttribute("data-visible");
      this._fieldEl.removeAttribute("data-invalid");
      this._input.setAttribute("aria-invalid", "false");
    }
    return;
  }

  get rawValue() {
    const val = this._input !== undefined ? this._input.value : "";
    let raw = "";
    for (let i = 0; i < this._maskParts.length; i = i + 1) {
      const part = this._maskParts[i];
      if (part.type !== "literal" && val[i] !== undefined) {
        raw = raw + val[i];
      }
    }
    return raw;
  }

  get complete() {
    const val = this._input !== undefined ? this._input.value : "";
    for (let i = 0; i < this._maskParts.length; i = i + 1) {
      const part = this._maskParts[i];
      if (part.type !== "literal") {
        const placeholderChar = this.getAttribute("placeholder-char") || "_";
        const ch = val[i] || "";
        if (ch === "" || ch === placeholderChar) {
          return false;
        }
      }
    }
    return this._maskParts.some(p => p.type !== "literal");
  }

  focus() {
    if (this._input !== undefined) {
      this._input.focus();
    }
    return;
  }
}
