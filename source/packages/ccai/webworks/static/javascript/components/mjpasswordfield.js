/*
 * mjpasswordfield.js
 *
 * <mj-password-field> -- password entry with show/hide toggle,
 * optional caps-lock warning, and optional strength meter.
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
}
:host([size="sm"]) .field { min-height: var(--mj-control-height-sm); }
:host([size="lg"]) .field { min-height: var(--mj-control-height-lg); }
.field:focus-within {
  border-color: var(--mj-accent);
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: var(--mj-focus-ring-offset);
}
.field[data-invalid] { border-color: var(--mj-color-danger); }

.prefix-slot {
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

.toggle-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  margin-inline-end: var(--mj-space-1);
  padding: 0;
  background: transparent;
  border: none;
  border-radius: var(--mj-radius-sm);
  cursor: pointer;
  color: var(--mj-text-muted);
  flex-shrink: 0;
  font-size: 0.9rem;
}
.toggle-btn:hover { color: var(--mj-text); }
.toggle-btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
}
.toggle-btn[hidden] { display: none; }

.caps-hint {
  display: none;
  padding: var(--mj-space-2) var(--mj-space-3);
  margin-top: var(--mj-space-1);
  background: var(--mj-color-warning-surface);
  border-radius: var(--mj-radius-sm);
  font-size: var(--mj-font-size-sm);
  color: var(--mj-color-warning);
}
.caps-hint[data-visible] { display: block; }

.strength-wrap {
  margin-top: var(--mj-space-2);
}
.strength-wrap[hidden] { display: none; }

.strength-bar {
  height: 4px;
  background: var(--mj-bg-muted);
  border-radius: var(--mj-radius-pill);
  overflow: hidden;
}
.strength-fill {
  height: 100%;
  border-radius: var(--mj-radius-pill);
  width: 0%;
  transition: width var(--mj-motion-medium) var(--mj-motion-ease),
              background var(--mj-motion-medium) var(--mj-motion-ease);
}
@media (prefers-reduced-motion: reduce) {
  .strength-fill { transition: none; }
}
.strength-label {
  font-size: var(--mj-font-size-xs);
  color: var(--mj-text-muted);
  margin-top: var(--mj-space-1);
}

.below { margin-top: var(--mj-space-1); }
.help { font-size: var(--mj-font-size-sm); color: var(--mj-text-muted); }
.help:empty { display: none; }
.error { font-size: var(--mj-font-size-sm); color: var(--mj-color-danger); display: none; }
.error[data-visible] { display: block; }

:host([disabled]) .field { opacity: 0.55; pointer-events: none; }
`;

const STRENGTH_COLORS = ["", "#b91c1c", "#b45309", "#d97706", "#15803d"];
const STRENGTH_LABELS = ["", "Very weak", "Weak", "Fair", "Strong"];

export class MjPasswordField extends FormControlMixin(MjElement) {
  static tagName = "mj-password-field";
  static styles = STYLES;
  static watched = [
    "label", "placeholder", "help-text", "error-message", "value",
    "required", "disabled", "readonly", "minlength", "maxlength",
    "visible", "show-strength", "show-caps-hint", "size",
    "new-password", "current-password"
  ];

  constructor() {
    super();
    this._initFormControl();
    this._strength = 0;
    this._prevValue = "";
    this._inputId = nextId("mjpf-input");
    this._helpId = nextId("mjpf-help");
    this._errorId = nextId("mjpf-error");
    this._strengthMeterId = nextId("mjpf-meter");
  }

  render() {
    const markup = `
      <label class="label" part="label" for="${this._inputId}"></label>
      <div class="field" part="field">
        <span class="prefix-slot" part="prefix"><slot name="prefix"></slot></span>
        <input part="input" id="${this._inputId}" type="password" autocomplete="current-password" />
        <button class="toggle-btn" part="toggle-button" type="button" aria-pressed="false"></button>
      </div>
      <div class="caps-hint" part="caps-lock-hint" role="alert"></div>
      <div class="strength-wrap" part="strength-meter" hidden>
        <div class="strength-bar">
          <div class="strength-fill" part="strength-fill"
            role="meter" aria-valuemin="0" aria-valuemax="4" aria-valuenow="0"
            id="${this._strengthMeterId}"></div>
        </div>
        <div class="strength-label" part="strength-label"></div>
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
    this._toggleBtn = this.$(".toggle-btn");
    this._capsHint = this.$(".caps-hint");
    this._strengthWrap = this.$(".strength-wrap");
    this._strengthFill = this.$(".strength-fill");
    this._strengthLabelEl = this.$(".strength-label");
    this._helpEl = this.$(".help");
    this._errorEl = this.$(".error");
    this._fieldEl = this.$(".field");

    this._syncAll();

    this.listen(this._input, "input", this._onInput.bind(this));
    this.listen(this._input, "change", this._onChange.bind(this));
    this.listen(this._input, "blur", this._onBlur.bind(this));
    this.listen(this._input, "keydown", this._onKeydown.bind(this));
    this.listen(this._toggleBtn, "click", this._onToggle.bind(this));
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
    const disabled = this.hasAttribute("disabled");
    const readonly = this.hasAttribute("readonly");
    const required = this.hasAttribute("required");
    const visible = this.hasAttribute("visible");
    const showStrength = this.hasAttribute("show-strength");
    const maxlength = this.getAttribute("maxlength");
    const minlength = this.getAttribute("minlength");
    const newPassword = this.hasAttribute("new-password");
    const currentPassword = this.hasAttribute("current-password");

    this._labelEl.textContent = label;
    this._input.placeholder = placeholder;
    this._input.disabled = disabled;
    this._input.readOnly = readonly;
    this._input.required = required;
    this._input.setAttribute("aria-required", required ? "true" : "false");
    this._input.type = visible ? "text" : "password";

    let autocomplete = "current-password";
    if (newPassword === true && currentPassword === false) {
      autocomplete = "new-password";
    }
    this._input.autocomplete = autocomplete;

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

    this._toggleBtn.hidden = disabled || readonly;
    this._toggleBtn.setAttribute("aria-pressed", visible ? "true" : "false");
    this._toggleBtn.setAttribute("aria-label", visible ? "Hide password" : "Show password");
    this._toggleBtn.textContent = visible ? "🙈" : "👁";

    this._strengthWrap.hidden = !showStrength;
    this._helpEl.textContent = helpText;

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

  _onInput(event) {
    const val = this._input.value;
    this._setFormValue(val);
    this.emit("mj-input", { value: val });

    if (this.hasAttribute("show-strength")) {
      const newScore = this._calcStrength(val);
      if (newScore !== this._strength) {
        this._strength = newScore;
        this._renderStrength();
        this.emit("mj-strength-change", {
          score: newScore,
          label: STRENGTH_LABELS[newScore] || ""
        });
      }
    }
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

  _onKeydown(event) {
    if (this.hasAttribute("show-caps-hint")) {
      const capsOn = event.getModifierState("CapsLock");
      this._capsHint.textContent = capsOn ? "⚠ Caps Lock is on" : "";
      if (capsOn) {
        this._capsHint.setAttribute("data-visible", "");
      } else {
        this._capsHint.removeAttribute("data-visible");
      }
    }
    if (event.key === "Escape" && this.hasAttribute("visible")) {
      this.removeAttribute("visible");
      this._syncAll();
    }
    return;
  }

  _onToggle(event) {
    const wasVisible = this.hasAttribute("visible");
    this.reflectBoolean("visible", !wasVisible);
    this._syncAll();
    this.emit("mj-visibility-change", { visible: !wasVisible });
    this._input.focus();
    return;
  }

  _calcStrength(password) {
    if (password.length === 0) {
      return 0;
    }
    let score = 1;
    if (password.length >= 8) {
      score = score + 1;
    }
    if (/[A-Z]/.test(password) && /[a-z]/.test(password)) {
      score = score + 1;
    }
    if (/\d/.test(password) && /[^a-zA-Z0-9]/.test(password)) {
      score = Math.min(score + 1, 4);
    }
    return score;
  }

  _renderStrength() {
    const pct = (this._strength / 4) * 100;
    this._strengthFill.style.width = `${pct}%`;
    this._strengthFill.style.background = STRENGTH_COLORS[this._strength] || "";
    this._strengthFill.setAttribute("aria-valuenow", String(this._strength));
    this._strengthFill.setAttribute("aria-valuetext", STRENGTH_LABELS[this._strength] || "");
    this._strengthLabelEl.textContent = STRENGTH_LABELS[this._strength] || "";
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
      this._input.value = initial;
      this.removeAttribute("visible");
      this._strength = 0;
      this._renderStrength();
      this._errorEl.removeAttribute("data-visible");
      this._fieldEl.removeAttribute("data-invalid");
      this._input.setAttribute("aria-invalid", "false");
      this._syncAll();
    }
    return;
  }

  get strength() {
    return this._strength;
  }

  get strengthLabel() {
    return STRENGTH_LABELS[this._strength] || "";
  }

  get visible() {
    return this.hasAttribute("visible");
  }

  set visible(val) {
    this.reflectBoolean("visible", val === true);
    if (this._input !== undefined) {
      this._syncAll();
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
