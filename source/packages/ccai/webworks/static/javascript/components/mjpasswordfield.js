/*
 * mjpasswordfield.js
 *
 * <mj-password-field> -- password entry with show/hide toggle,
 * optional caps-lock warning, and optional strength meter.
 *
 * Value model: `this._value` (owned by FormControlMixin) is the single source
 * of truth; the `value` attribute is the default value and the shadow <input>
 * and strength meter are rebuilt from `this._value` on every render.
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
.prefix-slot[hidden] { display: none; }

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
.toggle-btn svg { width: 1.1rem; height: 1.1rem; }
.toggle-btn .icon-hide { display: none; }
.toggle-btn[aria-pressed="true"] .icon-show { display: none; }
.toggle-btn[aria-pressed="true"] .icon-hide { display: block; }

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
  height: var(--mj-pwd-strength-height, 4px);
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
.strength-fill[data-score="1"] { background: var(--mj-pwd-strength-color-1, var(--mj-color-danger)); }
.strength-fill[data-score="2"] { background: var(--mj-pwd-strength-color-2, var(--mj-color-warning)); }
.strength-fill[data-score="3"] { background: var(--mj-pwd-strength-color-3, color-mix(in srgb, var(--mj-color-warning) 50%, var(--mj-color-success))); }
.strength-fill[data-score="4"] { background: var(--mj-pwd-strength-color-4, var(--mj-color-success)); }
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

:host([disabled]) .field, .field[data-disabled] { opacity: 0.55; pointer-events: none; }
`;

/* Strength label keys by score; score 0 has no label. */
const STRENGTH_LABEL_KEYS = [
  "",
  "mj.passwordField.strength.veryWeak",
  "mj.passwordField.strength.weak",
  "mj.passwordField.strength.fair",
  "mj.passwordField.strength.strong"
];

/* The localized label for a strength score, or "" when it has none. */
function strengthLabel(score) {
  const key = STRENGTH_LABEL_KEYS[score] || ""
  const label = key.length > 0 ? t(key) : ""
  return label
}

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

/* Built-in strength heuristic: 0 (empty) to 4 (strong). Runs locally only. */
function calculateStrength(password) {
  let score = 0

  if (password.length > 0) {
    score = 1
    if (password.length >= 8) {
      score = score + 1
    }
    if (/[A-Z]/.test(password) === true && /[a-z]/.test(password) === true) {
      score = score + 1
    }
    if (/\d/.test(password) === true && /[^a-zA-Z0-9]/.test(password) === true) {
      score = Math.min(score + 1, 4)
    }
  }

  return score
}

export class MjPasswordField extends FormControlMixin(MjElement) {
  static tagName = "mj-password-field";
  static styles = STYLES;
  static watched = [
    "label", "placeholder", "help-text", "error-message", "value",
    "required", "disabled", "readonly", "minlength", "maxlength",
    "visible", "show-strength", "show-caps-hint", "size",
    "new-password", "current-password", "aria-label", "aria-labelledby"
  ];

  constructor() {
    super()
    this._initFormControl()

    this._strength = 0

    /* Value at the last mj-change, used to suppress no-op change events. */
    this._committedValue = ""

    /* The `value` attribute text most recently applied to the control. */
    this._appliedValueAttribute = null

    /* True while an ancestor <fieldset disabled> disables the control. */
    this._formDisabled = false

    /* Errors are shown once the user has left the field or a submit failed. */
    this._showErrors = false

    this._inputId = nextId("mjpf-input")
    this._helpId = nextId("mjpf-help")
    this._errorId = nextId("mjpf-error")
    this._strengthMeterId = nextId("mjpf-meter")
  }

  render() {
    const markup = html`
      <label class="label" part="label" for="${this._inputId}"></label>
      <div class="field" part="field">
        <span class="prefix-slot" part="prefix"><slot name="prefix"></slot></span>
        <input part="input" id="${this._inputId}" type="password" autocomplete="current-password" />
        <button class="toggle-btn" part="toggle-button" type="button" aria-pressed="false" aria-label="${t("mj.passwordField.showPassword")}">
          <svg class="icon-show" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M1.5 10S4.5 4 10 4s8.5 6 8.5 6-3 6-8.5 6S1.5 10 1.5 10z"/><circle cx="10" cy="10" r="2.5"/>
          </svg>
          <svg class="icon-hide" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M1.5 10S4.5 4 10 4s8.5 6 8.5 6-3 6-8.5 6S1.5 10 1.5 10z"/><circle cx="10" cy="10" r="2.5"/><path d="M3 3l14 14"/>
          </svg>
        </button>
      </div>
      <div class="caps-hint" part="caps-lock-hint" role="alert"></div>
      <div class="strength-wrap" part="strength-meter" hidden>
        <div class="strength-bar">
          <div class="strength-fill" part="strength-fill"
            role="meter" aria-label="${t("mj.passwordField.strengthMeter")}"
            aria-valuemin="0" aria-valuemax="4" aria-valuenow="0"
            id="${this._strengthMeterId}"></div>
        </div>
        <div class="strength-label" part="strength-label" role="status" aria-live="polite"></div>
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
    this._toggleBtn = this.$(".toggle-btn")
    this._capsHint = this.$(".caps-hint")
    this._strengthWrap = this.$(".strength-wrap")
    this._strengthFill = this.$(".strength-fill")
    this._strengthLabelEl = this.$(".strength-label")
    this._helpEl = this.$(".help")
    this._errorEl = this.$(".error")
    this._fieldEl = this.$(".field")

    /* Empty prefix / suffix wrappers take no room (see _syncAffixes). */
    this._syncAffixes()
    const affixSlots = this.$all("[part='prefix'] slot, [part='suffix'] slot")
    for (let index = 0; index < affixSlots.length; index = index + 1) {
      this.listen(affixSlots[index], "slotchange", this._syncAffixes.bind(this))
    }

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
    this.listen(this._input, "keydown", this._onKeydown.bind(this))
    this.listen(this._input, "keyup", this._onModifierProbe.bind(this))
    this.listen(this._input, "mousedown", this._onModifierProbe.bind(this))
    this.listen(this._toggleBtn, "click", this._onToggle.bind(this))
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
    const disabled = this._isDisabled()
    const readonly = this.hasAttribute("readonly")
    const required = this.hasAttribute("required")
    const visible = this.hasAttribute("visible")
    const showStrength = this.hasAttribute("show-strength")
    const maxlength = this.getAttribute("maxlength")
    const minlength = this.getAttribute("minlength")
    const newPassword = this.hasAttribute("new-password")
    const currentPassword = this.hasAttribute("current-password")

    this._labelEl.textContent = label
    this._labelEl.toggleAttribute("data-required", required === true)
    this._fieldEl.toggleAttribute("data-disabled", disabled === true)

    this._input.placeholder = placeholder
    this._input.disabled = disabled
    this._input.readOnly = readonly
    this._input.required = required
    this._input.setAttribute("aria-required", required === true ? "true" : "false")
    this._input.type = visible === true ? "text" : "password"

    let autocomplete = "current-password"
    if (newPassword === true && currentPassword === false) {
      autocomplete = "new-password"
    }
    this._input.autocomplete = autocomplete

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

    /*
     * A toggle button keeps one name and reports its state through
     * aria-pressed; swapping the name as well would announce
     * "Hide password, pressed", the opposite of what activating it does.
     */
    this._toggleBtn.hidden = disabled === true || readonly === true
    this._toggleBtn.setAttribute("aria-pressed", visible === true ? "true" : "false")

    if (this.hasAttribute("show-caps-hint") === false) {
      this._setCapsHint(false)
    }

    this._strengthWrap.hidden = showStrength === false
    this._helpEl.textContent = helpText

    this._syncAccessibleName()
    this._syncStrength(false)

    /* required / minlength / maxlength / error-message all feed validity. */
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
    this._applyValue(attributeValue, false)
    return
  }

  /*
   * The single entry point for every programmatic value change. `notify` is
   * false when the change comes from the `value` attribute: an attribute
   * handler updates state but does not emit events.
   */
  _applyValue(next, notify) {
    const text = next === null || next === undefined ? "" : String(next)

    this._setFormValue(text)
    this._committedValue = text

    if (this._input !== undefined && this._input !== null) {
      if (this._input.value !== text) {
        this._input.value = text
      }
      this._syncStrength(notify === true)
      this._renderValidity(false)
    }
    return
  }

  /*
   * Recompute the strength score from the current value and redraw the
   * meter. The score is tracked only while `show-strength` is set; `notify`
   * is true when the value itself changed, and only then is
   * `mj-strength-change` emitted.
   */
  _syncStrength(notify) {
    const tracked = this.hasAttribute("show-strength")
    const text = this._value === null || this._value === undefined ? "" : String(this._value)
    const score = tracked === true ? calculateStrength(text) : 0
    const changed = score !== this._strength

    this._strength = score
    this._renderStrength()

    if (changed === true && notify === true) {
      this.emit("mj-strength-change", {
        score: score,
        label: strengthLabel(score)
      })
    }
    return
  }

  _renderStrength() {
    const percent = (this._strength / 4) * 100
    const label = strengthLabel(this._strength)

    this._strengthFill.style.width = `${percent}%`
    this._strengthFill.setAttribute("data-score", String(this._strength))
    this._strengthFill.setAttribute("aria-valuenow", String(this._strength))
    if (label.length > 0) {
      this._strengthFill.setAttribute("aria-valuetext", label)
    } else {
      this._strengthFill.removeAttribute("aria-valuetext")
    }
    if (this._strengthLabelEl.textContent !== label) {
      this._strengthLabelEl.textContent = label
    }
    return
  }

  _setCapsHint(capsOn) {
    if (capsOn === true) {
      if (this._capsHint.hasAttribute("data-visible") === false) {
        this._capsHint.textContent = t("mj.passwordField.capsLock")
        this._capsHint.setAttribute("data-visible", "")
      }
    } else {
      this._capsHint.textContent = ""
      this._capsHint.removeAttribute("data-visible")
    }
    return
  }

  /*
   * Caps Lock can only be read from a keyboard or mouse event, so the hint
   * is refreshed on every key press/release and on the click that focuses
   * the field, and removed when focus leaves.
   */
  _onModifierProbe(event) {
    if (this.hasAttribute("show-caps-hint") === true && typeof event.getModifierState === "function") {
      this._setCapsHint(event.getModifierState("CapsLock") === true)
    }
    return
  }

  _onInput(event) {
    const text = this._input.value
    this._setFormValue(text)
    this._renderValidity(false)
    this.emit("mj-input", { value: text })
    this._syncStrength(true)
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
    this._setCapsHint(false)
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

  _onKeydown(event) {
    this._onModifierProbe(event)

    if (event.key === "Escape" && this.hasAttribute("visible") === true) {
      /* Consumed here: an enclosing dialog must not close as well. */
      event.preventDefault()
      event.stopPropagation()
      this._setVisible(false)
    }
    return
  }

  _onToggle(event) {
    const wasVisible = this.hasAttribute("visible")
    this._setVisible(wasVisible === false)
    this._input.focus()
    return
  }

  /* User-driven reveal / hide: reflect, redraw and notify. */
  _setVisible(visible) {
    const wasVisible = this.hasAttribute("visible")
    if (wasVisible !== visible) {
      this.reflectBoolean("visible", visible)
      this._syncAll()
      this.emit("mj-visibility-change", { visible: visible })
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

  /* Length constraints; `required` is handled by the mixin. */
  _customValidity() {
    let message = ""
    const text = this._value === null || this._value === undefined ? "" : String(this._value)

    if (text.length > 0) {
      const minlength = parseInt(this.getAttribute("minlength") || "", 10)
      const maxlength = parseInt(this.getAttribute("maxlength") || "", 10)

      if (Number.isNaN(minlength) === false && text.length < minlength) {
        message = t("mj.passwordField.tooShort", { count: minlength })
      } else if (Number.isNaN(maxlength) === false && text.length > maxlength) {
        message = t("mj.passwordField.tooLong", { count: maxlength })
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
    this.removeAttribute("visible")
    this._applyValue(initial, true)
    return
  }

  onFormRestore(state) {
    const restored = typeof state === "string" ? state : ""
    this._applyValue(restored, true)
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
    this._applyValue(next, true)
    return
  }

  get strength() {
    return this._strength
  }

  get strengthLabel() {
    return strengthLabel(this._strength)
  }

  get visible() {
    return this.hasAttribute("visible")
  }

  set visible(value) {
    this.reflectBoolean("visible", value === true)
    return
  }

  focus(options) {
    if (this._input !== undefined && this._input !== null) {
      this._input.focus(options)
    }
    return
  }
}
