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
 *
 * Accessible name: by default the name is stable (`label-off`, or the flavor
 * default such as "Favorite") and `aria-pressed` carries the state. When the
 * author supplies `label-on` the name itself changes with the state, so
 * `aria-pressed` is left out -- a screen reader never hears "Unfavorite,
 * pressed".
 *
 * Events: `mj-change` is the cancelable request fired before the state
 * changes; the native-style `change` and `mj-pressed` follow the committed
 * change.
 */

import { MjElement } from "../core/mjelement.js";
import { announce } from "../core/announcer.js";
import { formatNumber, t } from "../core/intl.js";

/* Keys of the default labels per flavor, resolved through t() at use time. */
const FLAVOR_DEFAULTS = {
  favorite: { labelOff: "mj.favoriteButton.favorite", labelOn: "mj.favoriteButton.unfavorite" },
  like:     { labelOff: "mj.favoriteButton.like",     labelOn: "mj.favoriteButton.unlike" },
  bookmark: { labelOff: "mj.favoriteButton.bookmark", labelOn: "mj.favoriteButton.removeBookmark" }
};

/* Counts from this value up are shown in compact notation (1.2K). */
const COMPACT_COUNT_THRESHOLD = 1000;

const ICON_ATTRIBUTES = `class="default-icon" viewBox="0 0 16 16" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"`;

const STAR_PATH = `<path d="M8 1.8l1.9 3.9 4.3.6-3.1 3 .7 4.3L8 11.6l-3.8 2 .7-4.3-3.1-3 4.3-.6z"/>`;
const HEART_PATH = `<path d="M8 13.7S2 10.2 2 6.1A3.1 3.1 0 0 1 8 4.9a3.1 3.1 0 0 1 6 1.2c0 4.1-6 7.6-6 7.6z"/>`;
const BOOKMARK_PATH = `<path d="M4 2.2h8a.6.6 0 0 1 .6.6v11L8 10.9l-4.6 2.9v-11a.6.6 0 0 1 .6-.6z"/>`;

/* Built-in icons per flavor: an outline for "off" and a filled shape for "on". */
const FLAVOR_ICONS = {
  favorite: {
    off: `<svg ${ICON_ATTRIBUTES} fill="none">${STAR_PATH}</svg>`,
    on: `<svg ${ICON_ATTRIBUTES} fill="currentColor">${STAR_PATH}</svg>`
  },
  like: {
    off: `<svg ${ICON_ATTRIBUTES} fill="none">${HEART_PATH}</svg>`,
    on: `<svg ${ICON_ATTRIBUTES} fill="currentColor">${HEART_PATH}</svg>`
  },
  bookmark: {
    off: `<svg ${ICON_ATTRIBUTES} fill="none">${BOOKMARK_PATH}</svg>`,
    on: `<svg ${ICON_ATTRIBUTES} fill="currentColor">${BOOKMARK_PATH}</svg>`
  }
};

const STYLES = `
:host {
  display: inline-block;
  vertical-align: middle;
}

.btn {
  position: relative;
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
.btn[data-pressed="true"] {
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

/* Icon-only: the label stays in the accessibility tree but is not shown. */
:host([icon-only]) .label {
  position: absolute;
  width: 1px; height: 1px; margin: -1px; padding: 0; border: 0;
  overflow: hidden; clip: rect(0 0 0 0); clip-path: inset(50%); white-space: nowrap;
}

/*
 * Pressed state of the primary variant. It follows the variant rule because
 * that rule out-specifies the generic pressed rule above.
 */
:host([variant="primary"]) .btn[data-pressed="true"] {
  color: var(--mj-favorite-button-color-on, var(--mj-text-on-accent));
  background: var(--mj-favorite-button-bg-on, var(--mj-accent-active));
  border-color: var(--mj-accent-active);
  box-shadow: inset 0 0 0 2px var(--mj-favorite-button-color-on, var(--mj-text-on-accent));
}

/* Built-in flavor icons, used when the icon slots are left empty. */
.default-icon { width: 1em; height: 1em; }

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
  border-inline-end-color: transparent;
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

    /* True from a user toggle until it is committed or rolled back. */
    this._optimisticPending = false

    /* True while this component itself writes the `pressed` attribute. */
    this._reflectingPressed = false

    /* True once the count has been shown; later changes are announced. */
    this._countShown = false
  }

  render() {
    const markup = `
      <button class="btn" part="button" type="button" aria-pressed="false">
        <span class="spinner" part="spinner" aria-hidden="true"></span>
        <span class="icon-off" part="icon-off" aria-hidden="true"><slot name="icon-off"><span class="default-off"></span></slot></span>
        <span class="icon-on" part="icon-on" aria-hidden="true"><slot name="icon-on"><span class="default-on"></span></slot></span>
        <span class="label" part="label"><slot></slot></span>
        <span class="count" part="count" hidden></span>
      </button>
    `
    return markup
  }

  afterRender() {
    this._button = this.$(".btn")
    this._countEl = this.$(".count")
    this._optimisticPressed = this.hasAttribute("pressed")
    this._optimisticPending = false
    this._countShown = false
    this.dataset.optimistic = this._optimisticPressed === true ? "true" : "false"
    this.listen(this._button, "click", this._onClick.bind(this))
    this._syncFlavorIcons()
    this._syncAccessibility()
    this._syncCount()
    this._countShown = true
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._button === undefined || this._button === null) {
      return
    }
    if (name === "pressed") {
      this._optimisticPressed = newValue !== null
      this.dataset.optimistic = this._optimisticPressed === true ? "true" : "false"
      if (this._reflectingPressed === false) {
        /* Set from outside: that state is authoritative, nothing to roll back. */
        this._optimisticPending = false
      }
    }
    if (name === "flavor") {
      this._syncFlavorIcons()
    }
    if (name === "pending" && newValue === null && oldValue !== null) {
      this._settleAfterPending()
    }
    if (name === "count" || name === "count-max") {
      this._syncCount()
    }
    this._syncAccessibility()
    return
  }

  /*
   * The persistence operation has finished. Unless it is rolled back in the
   * same task (`pending = false; rollback()`), the optimistic state is now
   * the committed state and a later rollback() must not revert it.
   */
  _settleAfterPending() {
    queueMicrotask(() => {
      if (this.hasAttribute("pending") === false) {
        this._optimisticPending = false
      }
    })
    return
  }

  /* Fill the icon slots' fallback content with the icons of the current flavor. */
  _syncFlavorIcons() {
    const flavor = this.getAttribute("flavor") || "favorite"
    const icons = FLAVOR_ICONS[flavor] || FLAVOR_ICONS.favorite

    const defaultOff = this.$(".default-off")
    const defaultOn = this.$(".default-on")
    if (defaultOff !== null && defaultOn !== null) {
      /* Constant markup from this module; nothing author-supplied. */
      defaultOff.innerHTML = icons.off
      defaultOn.innerHTML = icons.on
    }
    return
  }

  _syncAccessibility() {
    const disabled = this.hasAttribute("disabled")
    const pending = this.hasAttribute("pending")
    const inert = disabled === true || pending === true
    const currentLabel = this._getCurrentLabel()
    const pressedText = this._optimisticPressed === true ? "true" : "false"

    this._button.disabled = inert
    this._button.setAttribute("aria-busy", pending === true ? "true" : "false")
    this._button.setAttribute("data-pressed", pressedText)
    this._button.setAttribute("aria-label", currentLabel)

    /*
     * One mechanism conveys the state: aria-pressed with a stable name, or a
     * name that changes (author-supplied `label-on`) without aria-pressed.
     */
    if (this._hasChangingLabel() === true) {
      this._button.removeAttribute("aria-pressed")
    } else {
      this._button.setAttribute("aria-pressed", pressedText)
    }
    return
  }

  /* True when the author supplied a separate name for the pressed state. */
  _hasChangingLabel() {
    const labelOn = this.getAttribute("label-on")
    const changing = labelOn !== null && labelOn !== ""
    return changing
  }

  /* The count attribute as a non-negative integer, or null when absent. */
  _getCount() {
    let count = null
    const countAttr = this.getAttribute("count")
    if (countAttr !== null) {
      const parsed = parseInt(countAttr, 10)
      count = Number.isFinite(parsed) === true ? Math.max(0, parsed) : 0
    }
    return count
  }

  _getCurrentLabel() {
    const flavor = this.getAttribute("flavor") || "favorite"
    const flavorDefaults = FLAVOR_DEFAULTS[flavor] || FLAVOR_DEFAULTS.favorite

    let label = this.getAttribute("label-off") || t(flavorDefaults.labelOff)
    if (this._optimisticPressed === true && this._hasChangingLabel() === true) {
      label = this.getAttribute("label-on")
    }

    const count = this._getCount()
    if (count !== null) {
      label = `${label} (${this._formatCount(count)})`
    }
    return label
  }

  /*
   * Show the count. A change after the first display is announced once,
   * through the shared live region, together with the button's name so the
   * number has context.
   */
  _syncCount() {
    if (this._countEl === undefined || this._countEl === null) {
      return
    }

    const count = this._getCount()
    if (count === null) {
      this._countEl.hidden = true
      this._countEl.textContent = ""
      return
    }

    const displayText = this._formatCount(count)

    this._countEl.hidden = false
    if (this._countEl.textContent !== displayText) {
      this._countEl.textContent = displayText
      if (this._countShown === true) {
        announce(this._getCurrentLabel(), "polite")
      }
    }
    return
  }

  _formatCount(value) {
    let countMax = parseInt(this.getAttribute("count-max") || "9999", 10)
    if (Number.isFinite(countMax) === false) {
      countMax = 9999
    }

    const clamped = Number.isFinite(value) === true ? Math.max(0, value) : 0

    let text = ""
    if (clamped > countMax) {
      text = `${countMax}+`
    } else if (clamped >= COMPACT_COUNT_THRESHOLD) {
      text = formatNumber(clamped, { notation: "compact", maximumFractionDigits: 1 })
    } else {
      text = formatNumber(clamped)
    }
    return text
  }

  /* Write the `pressed` attribute as this component's own state change. */
  _reflectPressed(pressed) {
    this._reflectingPressed = true
    try {
      this.reflectBoolean("pressed", pressed)
    } finally {
      this._reflectingPressed = false
    }
    return
  }

  _onClick(event) {
    const blocked = this.hasAttribute("disabled") || this.hasAttribute("pending")
    if (blocked === true) {
      event.stopImmediatePropagation()
      event.preventDefault()
      return
    }

    const previousPressed = this._optimisticPressed
    const nextPressed = !this._optimisticPressed

    /*
     * `mj-change` is the cancelable request. It is dispatched directly, not
     * through emit(), because emit() would fire the native-style `change`
     * right away -- before the state changes and even for a vetoed toggle.
     */
    const request = new CustomEvent("mj-change", {
      detail: { pressed: nextPressed, previousPressed: previousPressed, originalEvent: event },
      bubbles: true,
      cancelable: true,
      composed: true
    })
    const proceed = this.dispatchEvent(request)
    if (proceed === false) {
      return
    }

    this._previousPressed = previousPressed
    this._optimisticPressed = nextPressed
    this._optimisticPending = true
    this.dataset.optimistic = nextPressed === true ? "true" : "false"
    this._reflectPressed(nextPressed)
    this._syncAccessibility()

    if (nextPressed === true) {
      this._playPressAnimation()
    }

    this.dispatchEvent(new Event("change", { bubbles: true, composed: true }))
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
    const pressed = Boolean(value)
    this._optimisticPressed = pressed
    this._optimisticPending = false
    this.dataset.optimistic = pressed === true ? "true" : "false"
    this.reflectBoolean("pressed", pressed)
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
    this.reflectBoolean("pending", Boolean(value))
    return
  }

  get count() {
    const value = this._getCount()
    if (value === null) {
      return undefined
    }
    return value
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
    this.reflectBoolean("disabled", Boolean(value))
    return
  }

  /*
   * Accept the optimistic state as final (the persistence operation
   * succeeded). After this, rollback() has nothing to revert. Clearing
   * `pending` does the same on its own.
   */
  commit() {
    this._optimisticPending = false
    return
  }

  /* Revert the last user toggle that has not been committed yet. */
  rollback() {
    if (this._optimisticPending === false) {
      console.info("<mj-favorite-button>: rollback() called but no optimistic update is pending.")
      return
    }
    const restoredPressed = this._previousPressed
    this._optimisticPending = false
    this._optimisticPressed = restoredPressed
    this.dataset.optimistic = restoredPressed === true ? "true" : "false"
    this._reflectPressed(restoredPressed)
    this._syncAccessibility()
    this.emit("mj-rollback", { pressed: restoredPressed })
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
