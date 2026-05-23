/*
 * mjotpinput.js
 *
 * <mj-otp-input> -- segmented verification code input with auto-advance,
 * paste-to-fill, and a single concatenated form value.
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

.group {
  display: flex;
  align-items: center;
  gap: var(--mj-space-2);
  flex-wrap: wrap;
}

.segment {
  width: 2.75rem;
  height: 3.5rem;
  padding: 0;
  text-align: center;
  font: inherit;
  font-size: var(--mj-font-size-xl);
  font-weight: var(--mj-font-weight-bold);
  color: var(--mj-text);
  background: var(--mj-surface);
  border: 2px solid var(--mj-border-strong);
  border-radius: var(--mj-radius-md);
  outline: none;
  transition: border-color var(--mj-motion-fast) var(--mj-motion-ease);
  caret-color: var(--mj-accent);
}
:host([size="sm"]) .segment { width: 2.25rem; height: 2.75rem; font-size: var(--mj-font-size-lg); }
:host([size="lg"]) .segment { width: 3.25rem; height: 4rem; font-size: var(--mj-font-size-2xl); }
.segment:focus {
  border-color: var(--mj-accent);
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
.segment[data-filled] { border-color: var(--mj-accent); }
.segment[data-invalid] { border-color: var(--mj-color-danger); }
.segment:disabled { opacity: 0.55; cursor: not-allowed; }

.separator {
  color: var(--mj-text-muted);
  font-weight: var(--mj-font-weight-bold);
  flex-shrink: 0;
}

.below { margin-top: var(--mj-space-1); }
.help { font-size: var(--mj-font-size-sm); color: var(--mj-text-muted); }
.help:empty { display: none; }
.error { font-size: var(--mj-font-size-sm); color: var(--mj-color-danger); display: none; }
.error[data-visible] { display: block; }

.announce { position: absolute; width:1px; height:1px; overflow:hidden; clip:rect(0,0,0,0); }
`;

export class MjOtpInput extends FormControlMixin(MjElement) {
  static tagName = "mj-otp-input";
  static styles = STYLES;
  static watched = [
    "label", "help-text", "error-message", "length", "inputtype",
    "required", "disabled", "readonly", "autocomplete", "group-at", "size"
  ];

  constructor() {
    super();
    this._initFormControl();
    this._wasFull = false;
    this._groupId = nextId("mjotp-group");
    this._helpId = nextId("mjotp-help");
    this._errorId = nextId("mjotp-error");
    this._announceId = nextId("mjotp-announce");
  }

  render() {
    const markup = `
      <label class="label" part="label"></label>
      <div class="group" part="group" role="group" id="${this._groupId}"></div>
      <span class="announce" id="${this._announceId}" aria-live="polite" role="status"></span>
      <div class="below">
        <span class="help" part="help" id="${this._helpId}"></span>
        <span class="error" part="error" id="${this._errorId}" role="alert"></span>
      </div>
    `;
    return markup;
  }

  afterRender() {
    this._labelEl = this.$(".label");
    this._groupEl = this.$(".group");
    this._helpEl = this.$(".help");
    this._errorEl = this.$(".error");
    this._announceEl = this.$(".announce");

    this._buildSegments();
    this._syncAll();
    return;
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._groupEl === undefined) {
      return;
    }
    if (name === "length" || name === "inputtype" || name === "group-at") {
      this._buildSegments();
    }
    this._syncAll();
    return;
  }

  _buildSegments() {
    this._groupEl.innerHTML = "";
    const length = parseInt(this.getAttribute("length") || "6", 10);
    const inputtype = this.getAttribute("inputtype") || "numeric";
    const groupAt = parseInt(this.getAttribute("group-at") || "0", 10);
    const autocomplete = this.getAttribute("autocomplete") || "one-time-code";
    const disabled = this.hasAttribute("disabled");
    const readonly = this.hasAttribute("readonly");
    const required = this.hasAttribute("required");

    let inputType = "text";
    let inputMode = "numeric";
    let pattern = "[0-9]";
    if (inputtype === "numeric") {
      inputType = "text";
      inputMode = "numeric";
      pattern = "[0-9]";
    } else if (inputtype === "alphanumeric") {
      inputType = "text";
      inputMode = "text";
      pattern = "[A-Za-z0-9]";
    } else if (inputtype === "password") {
      inputType = "password";
      inputMode = "numeric";
      pattern = "[0-9]";
    }

    const totalLabel = inputtype === "numeric" ? "Digit" : "Character";

    for (let i = 0; i < length; i = i + 1) {
      if (groupAt > 0 && i === groupAt) {
        const sep = document.createElement("span");
        sep.className = "separator";
        sep.setAttribute("part", "separator");
        sep.setAttribute("aria-hidden", "true");
        sep.innerHTML = "<slot name='separator'>–</slot>";
        this._groupEl.appendChild(sep);
      }

      const input = document.createElement("input");
      input.className = "segment";
      input.setAttribute("part", "segment");
      input.type = inputType;
      input.inputMode = inputMode;
      input.maxLength = 1;
      input.autocomplete = autocomplete;
      input.disabled = disabled;
      input.readOnly = readonly;
      input.setAttribute("aria-label", `${totalLabel} ${i + 1} of ${length}`);
      if (i === 0) {
        input.setAttribute("aria-required", required ? "true" : "false");
        if (this._helpEl.textContent.length > 0) {
          input.setAttribute("aria-describedby", this._helpId);
        }
      }

      input.addEventListener("keydown", (e) => this._onSegmentKeydown(e, i));
      input.addEventListener("input", (e) => this._onSegmentInput(e, i));
      input.addEventListener("paste", (e) => this._onSegmentPaste(e, i));
      input.addEventListener("focus", (e) => { input.select(); });

      this._groupEl.appendChild(input);
    }
    return;
  }

  _getSegments() {
    return Array.from(this._groupEl.querySelectorAll(".segment"));
  }

  _syncAll() {
    const label = this.getAttribute("label") || "";
    const helpText = this.getAttribute("help-text") || "";
    this._labelEl.textContent = label;
    this._helpEl.textContent = helpText;

    const groupEl = this.$("[role='group']");
    if (groupEl !== null) {
      groupEl.setAttribute("aria-label", label.length > 0 ? label : "Verification code");
    }
    return;
  }

  _onSegmentInput(event, idx) {
    const segments = this._getSegments();
    const seg = segments[idx];
    const val = seg.value;

    if (val.length > 1) {
      const code = val;
      seg.value = "";
      this._distributePaste(code, idx);
      return;
    }

    if (val.length === 1) {
      seg.setAttribute("data-filled", "");
      if (idx < segments.length - 1) {
        segments[idx + 1].focus();
      }
    } else {
      seg.removeAttribute("data-filled");
    }

    this._emitInput();
    return;
  }

  _onSegmentKeydown(event, idx) {
    const segments = this._getSegments();
    const seg = segments[idx];
    const key = event.key;

    if (key === "Backspace") {
      if (seg.value.length > 0) {
        seg.value = "";
        seg.removeAttribute("data-filled");
        this._emitInput();
      } else if (idx > 0) {
        segments[idx - 1].focus();
        segments[idx - 1].value = "";
        segments[idx - 1].removeAttribute("data-filled");
        this._emitInput();
      }
      event.preventDefault();
      return;
    }
    if (key === "Delete") {
      seg.value = "";
      seg.removeAttribute("data-filled");
      this._emitInput();
      event.preventDefault();
      return;
    }
    if (key === "ArrowRight" && idx < segments.length - 1) {
      segments[idx + 1].focus();
      event.preventDefault();
      return;
    }
    if (key === "ArrowLeft" && idx > 0) {
      segments[idx - 1].focus();
      event.preventDefault();
      return;
    }
    return;
  }

  _onSegmentPaste(event, idx) {
    event.preventDefault();
    const text = event.clipboardData !== null ? event.clipboardData.getData("text/plain") : "";
    this._distributePaste(text, idx);
    return;
  }

  _distributePaste(text, startIdx) {
    const segments = this._getSegments();
    const inputtype = this.getAttribute("inputtype") || "numeric";
    let cleaned = text;

    if (inputtype === "numeric" || inputtype === "password") {
      cleaned = text.replace(/\D/g, "");
    } else {
      cleaned = text.replace(/[^A-Za-z0-9]/g, "").toUpperCase();
    }

    const fromStart = cleaned.length === segments.length;
    const start = fromStart ? 0 : startIdx;

    for (let i = 0; i < cleaned.length; i = i + 1) {
      const pos = start + i;
      if (pos >= segments.length) {
        break;
      }
      segments[pos].value = cleaned[i];
      segments[pos].setAttribute("data-filled", "");
    }

    const lastFilled = Math.min(start + cleaned.length - 1, segments.length - 1);
    if (lastFilled >= 0) {
      segments[lastFilled].focus();
    }

    this._emitInput();
    return;
  }

  _emitInput() {
    const val = this._concatValue();
    const segments = this._getSegments();
    const complete = val.length === segments.length;

    this._setFormValue(val);
    this.emit("mj-input", { value: val, complete });

    if (complete && !this._wasFull) {
      this._wasFull = true;
      this._announceEl.textContent = "Code entered";
      this.emit("mj-complete", { value: val });
    } else if (!complete) {
      this._wasFull = false;
    }
    if (complete) {
      const segments2 = this._getSegments();
      this.emit("mj-change", { value: val });
      this._runValidation(false);
    }
    return;
  }

  _concatValue() {
    const segments = this._getSegments();
    return segments.map(s => s.value).join("");
  }

  _runValidation(reportInvalid) {
    this._refreshValidity();
    const msg = this.validationMessage;
    const overrideMsg = this.getAttribute("error-message") || "";
    const displayMsg = overrideMsg.length > 0 ? overrideMsg : msg;

    if (displayMsg.length > 0) {
      this._errorEl.textContent = displayMsg;
      this._errorEl.setAttribute("data-visible", "");
      this._getSegments().forEach(s => s.setAttribute("data-invalid", ""));
      this.emit("mj-invalid", { validationMessage: displayMsg });
    } else {
      this._errorEl.removeAttribute("data-visible");
      this._getSegments().forEach(s => s.removeAttribute("data-invalid"));
    }
    return;
  }

  _customValidity() {
    const required = this.hasAttribute("required");
    if (required) {
      const segments = this._getSegments();
      const allFilled = segments.every(s => s.value.length > 0);
      if (!allFilled) {
        return "Please complete the verification code.";
      }
    }
    return "";
  }

  _validationAnchor() {
    const segs = this._getSegments();
    return segs.length > 0 ? segs[0] : this;
  }

  onFormReset(initial) {
    const segments = this._getSegments();
    segments.forEach(s => {
      s.value = "";
      s.removeAttribute("data-filled");
      s.removeAttribute("data-invalid");
    });
    this._setFormValue("");
    this._wasFull = false;
    this._errorEl.removeAttribute("data-visible");
    return;
  }

  get value() {
    return this._concatValue();
  }

  set value(next) {
    const segments = this._getSegments();
    const str = String(next || "");
    for (let i = 0; i < segments.length; i = i + 1) {
      const ch = str[i] || "";
      segments[i].value = ch;
      if (ch.length > 0) {
        segments[i].setAttribute("data-filled", "");
      } else {
        segments[i].removeAttribute("data-filled");
      }
    }
    this._setFormValue(str.substring(0, segments.length));
    return;
  }

  get complete() {
    const val = this._concatValue();
    const segments = this._getSegments();
    return val.length === segments.length;
  }

  checkValidity() {
    this._refreshValidity();
    return this._internals !== null ? this._internals.checkValidity() : true;
  }

  reportValidity() {
    this._runValidation(true);
    return this._internals !== null ? this._internals.reportValidity() : true;
  }

  focus() {
    const segs = this._getSegments();
    if (segs.length > 0) {
      segs[0].focus();
    }
    return;
  }
}
