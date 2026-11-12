/*
 * mjtogglebutton.js
 *
 * <mj-toggle-button> -- a stateful button representing a binary on/off action.
 *
 * Exposes `aria-pressed` to communicate toggle state to assistive technology.
 * Fires a cancelable `mj-change` event before the state changes; once the change
 * is committed it fires the native-style `change` event and `mj-pressed`, so
 * `change` listeners read the new state and never run for a vetoed toggle.
 * Distinct from a checkbox (this is an action trigger) and from
 * <mj-disclosure-button> (this does not show/hide a content region).
 *
 * Form participation: the element is form-associated. With a `name` it
 * submits its `value` (default "on") while pressed and nothing while not
 * pressed, exactly like a checkbox; `required` makes an unpressed button
 * invalid. Form reset restores the pressed state it had when it was first
 * connected, and a disabled <fieldset> / form disables it.
 */

import { MjElement } from "../core/mjelement.js";
import { FormControlMixin } from "../core/forminternals.js";

const STYLES = `
:host {
  display: inline-block;
  vertical-align: middle;
}
:host([block]) { display: block; }

.btn {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--mj-space-2);
  min-height: var(--mj-toggle-button-height, var(--mj-control-height-md));
  min-width: var(--mj-target-min);
  padding: 0 var(--mj-toggle-button-padding-x, var(--mj-space-4));
  font: inherit;
  font-weight: var(--mj-font-weight-medium);
  line-height: 1;
  color: var(--mj-toggle-button-color, var(--mj-text));
  background: var(--mj-toggle-button-bg, var(--mj-surface));
  border: 1px solid var(--mj-toggle-button-border-color, var(--mj-border-strong));
  border-radius: var(--mj-toggle-button-border-radius, var(--mj-radius-md));
  cursor: pointer;
  user-select: none;
  transition: background var(--mj-motion-fast) var(--mj-motion-ease),
              color var(--mj-motion-fast) var(--mj-motion-ease),
              border-color var(--mj-motion-fast) var(--mj-motion-ease);
}
.btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-toggle-button-focus-ring-color, var(--mj-focus-ring));
  outline-offset: var(--mj-focus-ring-offset);
}
.btn:hover { background: var(--mj-bg-muted); }

.btn[aria-pressed="true"] {
  color: var(--mj-toggle-button-color-pressed, var(--mj-text-on-accent));
  background: var(--mj-toggle-button-bg-pressed, var(--mj-accent));
  border-color: var(--mj-toggle-button-border-color-pressed, var(--mj-accent));
}
.btn[aria-pressed="true"]:hover { background: var(--mj-accent-hover); border-color: var(--mj-accent-hover); }

/* Variants */
:host([variant="primary"]) .btn {
  color: var(--mj-text-on-accent);
  background: var(--mj-accent);
  border-color: var(--mj-accent);
}
:host([variant="tertiary"]) .btn { background: transparent; border-color: transparent; }
:host([variant="tertiary"]) .btn:hover { background: var(--mj-bg-muted); }

/*
 * Pressed state per variant. These follow the variant rules because a
 * variant rule out-specifies the generic pressed rule above.
 */
:host([variant="primary"]) .btn[aria-pressed="true"] {
  color: var(--mj-toggle-button-color-pressed, var(--mj-text-on-accent));
  background: var(--mj-toggle-button-bg-pressed, var(--mj-accent-active));
  border-color: var(--mj-toggle-button-border-color-pressed, var(--mj-accent-active));
  box-shadow: inset 0 0 0 2px var(--mj-toggle-button-color-pressed, var(--mj-text-on-accent));
}
:host([variant="tertiary"]) .btn[aria-pressed="true"] {
  color: var(--mj-toggle-button-color-pressed, var(--mj-accent));
  background: var(--mj-toggle-button-bg-pressed, var(--mj-bg-muted));
  border-color: var(--mj-toggle-button-border-color-pressed, var(--mj-accent));
}

/* Sizes */
:host([size="sm"]) .btn { min-height: var(--mj-control-height-sm); padding: 0 var(--mj-space-3); font-size: var(--mj-font-size-sm); }
:host([size="lg"]) .btn { min-height: var(--mj-control-height-lg); padding: 0 var(--mj-space-5); font-size: var(--mj-font-size-lg); }

/* Icon-only: the label stays in the accessibility tree but is not shown. */
:host([icon-only]) .btn { padding: 0; aspect-ratio: 1; }
:host([icon-only]) .label {
  position: absolute;
  width: 1px; height: 1px; margin: -1px; padding: 0; border: 0;
  overflow: hidden; clip: rect(0 0 0 0); clip-path: inset(50%); white-space: nowrap;
}

/* States */
:host([disabled]) .btn,
:host([loading]) .btn { opacity: 0.55; cursor: not-allowed; }
:host([loading]) .btn { cursor: progress; }

.spinner {
  width: 1em; height: 1em;
  border: 2px solid currentColor;
  border-inline-end-color: transparent;
  border-radius: var(--mj-radius-circle);
  animation: mj-toggle-spin var(--mj-motion-slow) linear infinite;
}
:host(:not([loading])) .spinner { display: none; }
@keyframes mj-toggle-spin { to { transform: rotate(360deg); } }

/*
 * Which state icon shows is decided in _syncIcons (it depends on which slots
 * are filled) and applied through the hidden attribute.
 */
.icon-on, .icon-off { display: inline-flex; }

@media (prefers-reduced-motion: reduce) {
  .btn { transition: none; }
}
`;

export class MjToggleButton extends FormControlMixin(MjElement) {
  static tagName = "mj-toggle-button";
  static styles = STYLES;
  static watched = ["pressed", "variant", "size", "loading", "icon-only", "label", "block", "value", "required"];

  constructor() {
    super()
    this._initFormControl()
    this._button = null

    /* The pressed state form reset returns to: the state at first connect. */
    this._defaultPressed = null

    /* True while an ancestor <fieldset disabled> (or form) disables the button. */
    this._formDisabled = false
    this._iconOff = null
    this._iconOn = null

    /* True once the missing-accessible-name warning was logged. */
    this._warnedMissingName = false
  }

  render() {
    const markup = `
      <button class="btn" part="button" type="button" aria-pressed="false">
        <span class="spinner" part="spinner" aria-hidden="true"></span>
        <span class="icon-off" part="icon-off"><slot name="icon-off"></slot></span>
        <span class="icon-on" part="icon-on"><slot name="icon-on"></slot></span>
        <span class="label" part="label"><slot></slot></span>
      </button>
    `
    return markup
  }

  afterRender() {
    if (this._defaultPressed === null) {
      this._defaultPressed = this.hasAttribute("pressed")
    }
    this._button = this.$(".btn")
    this._iconOff = this.$(".icon-off")
    this._iconOn = this.$(".icon-on")

    this.listen(this._button, "click", this._onClick.bind(this))
    this.listen(this.$("slot[name='icon-off']"), "slotchange", this._syncIcons.bind(this))
    this.listen(this.$("slot[name='icon-on']"), "slotchange", this._syncIcons.bind(this))

    this._syncAccessibility()
    this._syncIcons()
    this._publishFormValue()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (name === "pressed" || name === "value" || name === "required") {
      this._publishFormValue()
    }

    if (this._button === undefined || this._button === null) {
      return
    }

    this._syncAccessibility()
    if (name === "pressed") {
      this._syncIcons()
    }
    return
  }

  _syncAccessibility() {
    const disabled = this.hasAttribute("disabled") || this._formDisabled === true
    const loading = this.hasAttribute("loading")
    const inert = disabled === true || loading === true
    const pressed = this.hasAttribute("pressed")
    const iconOnly = this.hasAttribute("icon-only")

    this._button.disabled = inert
    this._button.setAttribute("aria-busy", loading === true ? "true" : "false")
    this._button.setAttribute("aria-pressed", pressed === true ? "true" : "false")

    if (iconOnly === true) {
      const accessibleName = this.getAttribute("label") || this.getAttribute("aria-label")
      if (accessibleName !== null && accessibleName.length > 0) {
        this._button.setAttribute("aria-label", accessibleName)
      } else {
        /*
         * The slotted label text is visually hidden but still names the
         * button; only a button with neither is reported, once.
         */
        this._button.removeAttribute("aria-label")
        const slottedText = this.textContent !== null ? this.textContent.trim() : ""
        if (slottedText === "" && this._warnedMissingName === false) {
          this._warnedMissingName = true
          console.warn("<mj-toggle-button>: icon-only is set but no label attribute is provided.")
        }
      }
    } else {
      this._button.removeAttribute("aria-label")
    }
    return
  }

  /*
   * Show the icon for the current state. A button that fills only one of the
   * two icon slots keeps that icon in both states.
   */
  _syncIcons() {
    if (this._iconOff === null || this._iconOn === null) {
      return
    }

    const pressed = this.hasAttribute("pressed")
    const hasOff = this.querySelector(":scope > [slot='icon-off']") !== null
    const hasOn = this.querySelector(":scope > [slot='icon-on']") !== null

    const showOff = hasOff === true && (pressed === false || hasOn === false)
    const showOn = hasOn === true && (pressed === true || hasOff === false)

    this._iconOff.hidden = showOff === false
    this._iconOn.hidden = showOn === false
    return
  }

  _onClick(event) {
    const blocked = this.hasAttribute("disabled") || this.hasAttribute("loading") || this._formDisabled === true
    if (blocked === true) {
      event.stopImmediatePropagation()
      event.preventDefault()
      return
    }

    const nextPressed = !this.pressed

    /*
     * `mj-change` is the cancelable request. It is dispatched directly, not
     * through emit(), because emit() would fire the native-style `change`
     * right away -- before the state changes and even for a vetoed toggle.
     */
    const request = new CustomEvent("mj-change", {
      detail: { pressed: nextPressed, originalEvent: event },
      bubbles: true,
      cancelable: true,
      composed: true
    })
    const proceed = this.dispatchEvent(request)
    if (proceed === false) {
      return
    }

    this.pressed = nextPressed
    this.dispatchEvent(new Event("change", { bubbles: true, composed: true }))
    this.emit("mj-pressed", { pressed: nextPressed })
    return
  }

  /* ----- form participation ----- */

  /* Checkbox semantics: the value while pressed, no entry while not. */
  _publishFormValue() {
    const submitted = this.hasAttribute("pressed") === true ? this.value : null
    this._setFormValue(submitted)
    return
  }

  formResetCallback() {
    const pressed = this._defaultPressed !== null ? this._defaultPressed : false
    this.pressed = pressed
    this._publishFormValue()
    return
  }

  formStateRestoreCallback(state) {
    this.pressed = state !== null && state !== undefined
    this._publishFormValue()
    return
  }

  onFormDisabled(disabled) {
    this._formDisabled = disabled === true
    if (this._button !== undefined && this._button !== null) {
      this._syncAccessibility()
    }
    return
  }

  /* ----- scriptable API ----- */

  /* The value submitted while pressed (the `value` attribute, default "on"). */
  get value() {
    const value = this.getAttribute("value")
    return value !== null ? value : "on"
  }

  set value(next) {
    this.setAttribute("value", String(next))
    return
  }

  get pressed() {
    const value = this.hasAttribute("pressed")
    return value
  }

  set pressed(value) {
    this.reflectBoolean("pressed", Boolean(value))
    return
  }

  get loading() {
    const value = this.hasAttribute("loading")
    return value
  }

  set loading(value) {
    this.reflectBoolean("loading", Boolean(value))
    return
  }

  get disabled() {
    const value = this.hasAttribute("disabled")
    return value
  }

  set disabled(value) {
    this.reflectBoolean("disabled", Boolean(value))
    return
  }

  /*
   * Toggles the button as a user click would (mj-change, change, mj-
   * pressed). HTMLElement.click() would only dispatch a click at the host,
   * which never reaches the inner button. Disabled / busy states are
   * honoured by the inner handler.
   */
  click() {
    if (this._button !== undefined && this._button !== null) {
      this._button.click()
    }
    return
  }

  focus(options) {
    if (this._button !== undefined && this._button !== null) {
      this._button.focus(options)
    }
    return
  }
}
