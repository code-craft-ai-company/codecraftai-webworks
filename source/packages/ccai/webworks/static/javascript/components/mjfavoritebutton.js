/*
 * mjfavoritebutton.js
 *
 * <mj-favorite-button> -- a toggle button for marking content as liked,
 * favorited, or bookmarked.
 *
 * Builds on the toggle button pattern (aria-pressed) and adds optimistic UI
 * (visual state updates immediately on activation), an optional visible count
 * display, a rollback path for failed persistence operations, and a pending
 * state that blocks double-submission while an async operation is in flight.
 */

import { MjElement } from "../core/mjelement.js";
import { announce } from "../core/announcer.js";

const FLAVOR_DEFAULTS = {
  favorite: { labelOff: "Favorite",         labelOn: "Unfavorite" },
  like:     { labelOff: "Like",             labelOn: "Unlike" },
  bookmark: { labelOff: "Bookmark",         labelOn: "Remove bookmark" }
};

const STYLES = `
:host {
  display: inline-block;
  vertical-align: middle;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--mj-space-2);
  min-height: var(--mj-favorite-button-height, var(--mj-control-height-md));
  min-width: var(--mj-target-min);
  padding: 0 var(--mj-space-4);
  font: inherit;
  font-weight: var(--mj-font-weight-medium);
  line-height: 1;
  color: var(--mj-favorite-button-color-off, var(--mj-text-muted));
  background: var(--mj-favorite-button-bg-off, transparent);
  border: 1px solid transparent;
  border-radius: var(--mj-favorite-button-border-radius, var(--mj-radius-md));
  cursor: pointer;
  user-select: none;
  transition: background var(--mj-motion-fast) var(--mj-motion-ease),
              color var(--mj-motion-fast) var(--mj-motion-ease),
              transform var(--mj-favorite-button-animation-duration, var(--mj-motion-fast)) var(--mj-motion-ease);
}
.btn:hover { background: var(--mj-bg-muted); }
.btn:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-favorite-button-focus-ring-color, var(--mj-focus-ring));
  outline-offset: var(--mj-focus-ring-offset);
}
.btn[aria-pressed="true"] {
  color: var(--mj-favorite-button-color-on, var(--mj-color-danger));
  background: var(--mj-favorite-button-bg-on, transparent);
}

/* Sizes */
:host([size="sm"]) .btn { min-height: var(--mj-control-height-sm); padding: 0 var(--mj-space-3); font-size: var(--mj-font-size-sm); }
:host([size="lg"]) .btn { min-height: var(--mj-control-height-lg); padding: 0 var(--mj-space-5); font-size: var(--mj-font-size-lg); }

/* Variants */
:host([variant="primary"]) .btn { color: var(--mj-text-on-accent); background: var(--mj-accent); border-color: var(--mj-accent); }
:host([variant="secondary"]) .btn { background: var(--mj-surface); border-color: var(--mj-border-strong); }
:host([icon-only]) .btn { padding: 0; aspect-ratio: 1; }

/* States */
:host([disabled]) .btn  { opacity: 0.55; cursor: not-allowed; }
:host([pending]) .btn   { cursor: progress; }

/* Press animation */
@keyframes mj-fav-pop {
  0%   { transform: scale(1); }
  40%  { transform: scale(1.3); }
  70%  { transform: scale(0.9); }
  100% { transform: scale(1); }
}
:host([data-animating]) .btn { animation: mj-fav-pop var(--mj-favorite-button-animation-duration, 300ms) var(--mj-motion-ease); }

/* Pending spinner */
.spinner {
  width: 1em; height: 1em;
  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: var(--mj-radius-circle);
  animation: mj-fav-spin var(--mj-motion-slow) linear infinite;
}
:host(:not([pending])) .spinner { display: none; }
@keyframes mj-fav-spin { to { transform: rotate(360deg); } }

/* Icon slot visibility */
.icon-off { display: inline-flex; }
.icon-on  { display: none; }
:host([data-optimistic="true"]) .icon-off { display: none; }
:host([data-optimistic="true"]) .icon-on  { display: inline-flex; }

/* Count */
.count {
  font-size: var(--mj-favorite-button-count-font-size, var(--mj-font-size-sm));
  font-variant-numeric: tabular-nums;
  min-width: 2ch;
}
.count[hidden] { display: none; }

@media (prefers-reduced-motion: reduce) {
  .btn { transition: none; animation: none !important; }
  .spinner { animation: none; }
}
`;

export class MjFavoriteButton extends MjElement {
  static tagName = "mj-favorite-button";
  static styles = STYLES;
  static watched = ["pressed", "flavor", "count", "count-max", "label-off", "label-on", "variant", "size", "disabled", "pending", "icon-only"];

  constructor() {
    super()
    this._button = null
    this._countEl = null
    this._optimisticPressed = false
    this._previousPressed = false
  }

  render() {
    const markup = `
      <button class="btn" part="button" type="button" aria-pressed="false">
        <span class="spinner" part="spinner" aria-hidden="true"></span>
        <span class="icon-off" part="icon-off" aria-hidden="true"><slot name="icon-off"></slot></span>
        <span class="icon-on" part="icon-on" aria-hidden="true"><slot name="icon-on"></slot></span>
        <span class="label" part="label"><slot></slot></span>
        <span class="count" part="count" aria-live="polite" hidden></span>
      </button>
    `
    return markup
  }

  afterRender() {
    this._button = this.$(".btn")
    this._countEl = this.$(".count")
    this._optimisticPressed = this.hasAttribute("pressed")
    this.dataset.optimistic = this._optimisticPressed === true ? "true" : "false"
    this.listen(this._button, "click", this._onClick.bind(this))
    this._syncAccessibility()
    this._syncCount()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._button === null) {
      return
    }
    if (name === "pressed") {
      this._optimisticPressed = newValue !== null
      this.dataset.optimistic = this._optimisticPressed === true ? "true" : "false"
    }
    if (name === "count" || name === "count-max") {
      this._syncCount()
    }
    this._syncAccessibility()
    return
  }

  _syncAccessibility() {
    const disabled = this.hasAttribute("disabled")
    const pending = this.hasAttribute("pending")
    const inert = disabled === true || pending === true
    const iconOnly = this.hasAttribute("icon-only")
    const currentLabel = this._getCurrentLabel()

    this._button.disabled = inert
    this._button.setAttribute("aria-busy", pending === true ? "true" : "false")
    this._button.setAttribute("aria-pressed", this._optimisticPressed === true ? "true" : "false")
    this._button.setAttribute("aria-label", currentLabel)

    if (iconOnly === true) {
      if (currentLabel.length === 0) {
        console.warn("<mj-favorite-button>: icon-only is set but no label-off / label-on is provided.")
      }
    }
    return
  }

  _getCurrentLabel() {
    const flavor = this.getAttribute("flavor") || "favorite"
    const flavorDefaults = FLAVOR_DEFAULTS[flavor] || FLAVOR_DEFAULTS.favorite

    if (this._optimisticPressed === true) {
      const label = this.getAttribute("label-on") || flavorDefaults.labelOn
      const countValue = this.getAttribute("count")
      if (countValue !== null) {
        return `${label} (${this._formatCount(parseInt(countValue, 10))})`
      }
      return label
    }

    const label = this.getAttribute("label-off") || flavorDefaults.labelOff
    const countValue = this.getAttribute("count")
    if (countValue !== null) {
      return `${label} (${this._formatCount(parseInt(countValue, 10))})`
    }
    return label
  }

  _syncCount() {
    if (this._countEl === null) {
      return
    }
    const countAttr = this.getAttribute("count")
    if (countAttr === null) {
      this._countEl.hidden = true
      return
    }

    const raw = parseInt(countAttr, 10)
    const countValue = isNaN(raw) === true ? 0 : Math.max(0, Math.floor(raw))
    const displayText = this._formatCount(countValue)

    this._countEl.hidden = false
    if (this._countEl.textContent !== displayText) {
      this._countEl.textContent = displayText
      announce(displayText, "polite")
    }
    return
  }

  _formatCount(value) {
    const countMax = parseInt(this.getAttribute("count-max") || "9999", 10)
    const clamped = Math.max(0, value)
    if (clamped > countMax) {
      return `${countMax}+`
    }
    return String(clamped)
  }

  _onClick(event) {
    const blocked = this.hasAttribute("disabled") || this.hasAttribute("pending")
    if (blocked === true) {
      event.stopImmediatePropagation()
      event.preventDefault()
      return
    }

    this._previousPressed = this._optimisticPressed
    const nextPressed = !this._optimisticPressed

    const proceed = this.emit("mj-change", {
      pressed: nextPressed,
      previousPressed: this._previousPressed,
      originalEvent: event
    }, { cancelable: true })

    if (proceed === false) {
      return
    }

    this._optimisticPressed = nextPressed
    this.dataset.optimistic = nextPressed === true ? "true" : "false"
    this.reflectBoolean("pressed", nextPressed)
    this._syncAccessibility()

    if (nextPressed === true) {
      this._playPressAnimation()
    }

    this.emit("mj-pressed", { pressed: nextPressed })
    return
  }

  _playPressAnimation() {
    const motionOk = window.matchMedia("(prefers-reduced-motion: reduce)").matches === false
    if (motionOk === false) {
      return
    }
    this.dataset.animating = ""
    this._button.addEventListener("animationend", () => {
      delete this.dataset.animating
    }, { once: true })
    return
  }

  /* ----- scriptable API ----- */

  get pressed() {
    const value = this.hasAttribute("pressed")
    return value
  }

  set pressed(value) {
    this._optimisticPressed = value === true
    this.dataset.optimistic = this._optimisticPressed === true ? "true" : "false"
    this.reflectBoolean("pressed", value === true)
    return
  }

  get optimisticPressed() {
    return this._optimisticPressed
  }

  get pending() {
    const value = this.hasAttribute("pending")
    return value
  }

  set pending(value) {
    this.reflectBoolean("pending", value === true)
    return
  }

  get count() {
    const raw = this.getAttribute("count")
    if (raw === null) {
      return undefined
    }
    return parseInt(raw, 10)
  }

  set count(value) {
    if (value === undefined || value === null) {
      this.removeAttribute("count")
    } else {
      this.setAttribute("count", String(value))
    }
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

  rollback() {
    if (this._optimisticPressed === this._previousPressed) {
      console.info("<mj-favorite-button>: rollback() called but no optimistic update is pending.")
      return
    }
    const restoredPressed = this._previousPressed
    this._optimisticPressed = restoredPressed
    this.dataset.optimistic = restoredPressed === true ? "true" : "false"
    this.reflectBoolean("pressed", restoredPressed)
    this._syncAccessibility()
    this.emit("mj-rollback", { pressed: restoredPressed })
    return
  }

  focus() {
    this._button.focus()
    return
  }
}
