/*
 * mjtogglebutton.js
 *
 * <mj-toggle-button> -- a stateful button representing a binary on/off action.
 *
 * Exposes `aria-pressed` to communicate toggle state to assistive technology.
 * Fires a cancelable `mj-change` event before the state changes; fires `mj-pressed`
 * after the change is committed. Distinct from a checkbox (this is an action trigger)
 * and from <mj-disclosure-button> (this does not show/hide a content region).
 */

import { MjElement } from "../core/mjelement.js";

const STYLES = `
:host {
  display: inline-block;
  vertical-align: middle;
}
:host([block]) { display: block; }

.btn {
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

/* Sizes */
:host([size="sm"]) .btn { min-height: var(--mj-control-height-sm); padding: 0 var(--mj-space-3); font-size: var(--mj-font-size-sm); }
:host([size="lg"]) .btn { min-height: var(--mj-control-height-lg); padding: 0 var(--mj-space-5); font-size: var(--mj-font-size-lg); }

/* Icon-only */
:host([icon-only]) .btn { padding: 0; aspect-ratio: 1; }

/* States */
:host([disabled]) .btn,
:host([loading]) .btn { opacity: 0.55; cursor: not-allowed; }
:host([loading]) .btn { cursor: progress; }

.spinner {
  width: 1em; height: 1em;
  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: var(--mj-radius-circle);
  animation: mj-toggle-spin var(--mj-motion-slow) linear infinite;
}
:host(:not([loading])) .spinner { display: none; }
@keyframes mj-toggle-spin { to { transform: rotate(360deg); } }

/* Icon slot visibility tied to pressed state via host attribute */
.icon-on { display: none; }
:host([pressed]) .icon-off { display: none; }
:host([pressed]) .icon-on  { display: inline-flex; }

@media (prefers-reduced-motion: reduce) {
  .btn { transition: none; }
}
`;

export class MjToggleButton extends MjElement {
  static tagName = "mj-toggle-button";
  static styles = STYLES;
  static watched = ["pressed", "variant", "size", "loading", "icon-only", "label", "block"];

  constructor() {
    super()
    this._button = null
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
    this._button = this.$(".btn")
    this.listen(this._button, "click", this._onClick.bind(this))
    this._syncAccessibility()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._button !== null) {
      this._syncAccessibility()
    }
    return
  }

  _syncAccessibility() {
    const disabled = this.hasAttribute("disabled")
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
        console.warn("<mj-toggle-button>: icon-only is set but no label attribute is provided.")
        this._button.setAttribute("aria-label", "")
      }
    } else {
      this._button.removeAttribute("aria-label")
    }
    return
  }

  _onClick(event) {
    const blocked = this.hasAttribute("disabled") || this.hasAttribute("loading")
    if (blocked === true) {
      event.stopImmediatePropagation()
      event.preventDefault()
      return
    }

    const nextPressed = !this.pressed
    const proceed = this.emit("mj-change", { pressed: nextPressed, originalEvent: event }, { cancelable: true })
    if (proceed === false) {
      return
    }

    this.pressed = nextPressed
    this.emit("mj-pressed", { pressed: nextPressed })
    return
  }

  /* ----- scriptable API ----- */

  get pressed() {
    const value = this.hasAttribute("pressed")
    return value
  }

  set pressed(value) {
    this.reflectBoolean("pressed", value === true)
    return
  }

  get loading() {
    const value = this.hasAttribute("loading")
    return value
  }

  set loading(value) {
    this.reflectBoolean("loading", value === true)
    return
  }

  get disabled() {
    const value = this.hasAttribute("disabled")
    return value
  }

  set disabled(value) {
    this.reflectBoolean("disabled", value === true)
    return
  }

  focus() {
    this._button.focus()
    return
  }
}
