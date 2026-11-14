/*
 * mjbadge.js
 *
 * <mj-badge> -- count, dot, and status presence indicator. Overlays on
 * slotted content or renders inline. Status is never color-alone.
 *
 * Text alternative: the visible count bubble is decorative (aria-hidden); a
 * visually hidden text next to it carries the count, followed by the `label`
 * attribute when one is set ("7 unread messages"). A control that names
 * itself with aria-label can build its name with `getAriaLabel()`.
 *
 * The `color` attribute sets only the background. The text colour defaults
 * to the on-accent token; pair a light `color` with a matching
 * `--mj-badge-color`.
 */

import { MjElement } from "../core/mjelement.js";
import { t } from "../core/intl.js";

const STATUS_COLORS = {
  online:  "var(--mj-color-success)",
  away:    "var(--mj-color-warning)",
  busy:    "var(--mj-color-danger)",
  offline: "var(--mj-color-neutral-400)",
  dnd:     "var(--mj-color-danger)"
};

/* Keys of the status names, resolved through t() at use time. */
const STATUS_LABEL_KEYS = {
  online:  "mj.badge.online",
  away:    "mj.badge.away",
  busy:    "mj.badge.busy",
  offline: "mj.badge.offline",
  dnd:     "mj.badge.dnd"
};

/* Localized name of a known status, or "" for an unknown one. */
function getStatusLabel(status) {
  let label = ""
  if (Object.prototype.hasOwnProperty.call(STATUS_LABEL_KEYS, status) === true) {
    label = t(STATUS_LABEL_KEYS[status])
  }
  return label
}

const STYLES = `
:host { display: inline-block; position: relative; }
:host([placement="inline"]) { display: inline-flex; align-items: center; gap: var(--mj-space-1); }

.indicator {
  display: inline-flex; align-items: center; justify-content: center;
  min-width: var(--mj-badge-size, 1.25rem);
  height: var(--mj-badge-size, 1.25rem);
  padding-inline: var(--mj-space-1);
  background: var(--mj-badge-bg, var(--mj-color-danger));
  color: var(--mj-badge-color, var(--mj-text-on-accent));
  border: var(--mj-badge-border-width, 2px) solid var(--mj-badge-border-color, var(--mj-surface));
  border-radius: var(--mj-badge-border-radius, 9999px);
  font-size: var(--mj-badge-font-size, var(--mj-font-size-xs));
  font-weight: var(--mj-badge-font-weight, var(--mj-font-weight-bold));
  font-variant-numeric: tabular-nums;
  line-height: 1;
  white-space: nowrap;
  pointer-events: none;
}

/* overlaid placement */
:host(:not([placement="inline"])) .indicator {
  position: absolute;
  transform: translate(50%, -50%);
}
:host([placement="top-end"])      .indicator, :host(:not([placement])) .indicator { inset-block-start: 0; inset-inline-end: 0; }
:host([placement="top-start"])    .indicator { inset-block-start: 0; inset-inline-start: 0; transform: translate(-50%, -50%); }
:host([placement="bottom-end"])   .indicator { inset-block-end: 0; inset-inline-end: 0; transform: translate(50%, 50%); }
:host([placement="bottom-start"]) .indicator { inset-block-end: 0; inset-inline-start: 0; transform: translate(-50%, 50%); }

/* In right-to-left layouts the half-overlap points the other way. */
:host(:not([placement="inline"]):dir(rtl)) .indicator { transform: translate(-50%, -50%); }
:host([placement="top-start"]:dir(rtl))    .indicator { transform: translate(50%, -50%); }
:host([placement="bottom-end"]:dir(rtl))   .indicator { transform: translate(-50%, 50%); }
:host([placement="bottom-start"]:dir(rtl)) .indicator { transform: translate(50%, 50%); }

/* dot & status: smaller, no text */
:host([variant="dot"]) .indicator,
:host([variant="status"]) .indicator {
  width: var(--mj-badge-size, 0.625rem);
  height: var(--mj-badge-size, 0.625rem);
  min-width: unset; padding: 0;
}

/* hidden state */
.indicator[hidden] { display: none; }

/* pulse */
@keyframes mj-badge-pulse {
  0%   { box-shadow: 0 0 0 0 var(--mj-badge-pulse-color, var(--mj-color-danger)); }
  70%  { box-shadow: 0 0 0 6px rgba(0,0,0,0); }
  100% { box-shadow: 0 0 0 0 rgba(0,0,0,0); }
}
:host([pulse]) .indicator { animation: mj-badge-pulse 1.5s ease-in-out infinite; }
@media (prefers-reduced-motion: reduce) { :host([pulse]) .indicator { animation: none; } }
`;

export class MjBadge extends MjElement {
  static tagName = "mj-badge";
  static styles = STYLES;
  static watched = ["variant", "count", "max", "show-zero", "status", "label", "placement", "color", "pulse"];

  constructor() {
    super()
    this._indicator = null
    this._countText = null
    this._srText = null
    this._prevVisible = null
    this._prevOverflow = false

    /* True once the missing-label warning for a dot badge was logged. */
    this._warnedMissingLabel = false
  }

  render() {
    const markup = `
      <slot></slot>
      <span class="indicator" part="indicator" aria-hidden="true">
        <span class="count-text" part="count"></span>
      </span>
      <span class="sr-text mj-visually-hidden"></span>
    `
    return markup
  }

  afterRender() {
    this._indicator = this.$(".indicator")
    this._countText = this.$(".count-text")
    this._srText = this.$(".sr-text")
    this._syncIndicator()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._indicator === undefined || this._indicator === null) {
      return
    }
    this._syncIndicator()
    return
  }

  /* The count attribute as a non-negative integer (0 when absent or not a number). */
  _getCount() {
    const parsed = parseInt(this.getAttribute("count") || "0", 10)
    const count = Number.isFinite(parsed) === true && parsed > 0 ? parsed : 0
    return count
  }

  _getMax() {
    const parsed = parseInt(this.getAttribute("max") || "99", 10)
    const max = Number.isFinite(parsed) === true && parsed > 0 ? parsed : 99
    return max
  }

  _syncIndicator() {
    const indicator = this._indicator
    const countText = this._countText
    if (indicator === undefined || indicator === null) {
      return
    }

    const variant = this.getAttribute("variant") || "count"
    const label = this.getAttribute("label") || ""

    if (variant === "dot" || variant === "status") {
      this._syncDotStatus(indicator, variant, label)
    } else {
      this._syncCount(indicator, countText, label)
    }
    this._syncColor(indicator, variant)
    return
  }

  /*
   * The background override in effect: the `color` attribute, else the
   * colour of the status. With neither, the inline override is removed so
   * the stylesheet colour applies again.
   */
  _syncColor(indicator, variant) {
    const colorOverride = this.getAttribute("color") || ""

    let background = ""
    if (colorOverride.length > 0) {
      background = colorOverride
    } else if (variant === "status") {
      const statusVal = this.getAttribute("status") || ""
      background = STATUS_COLORS[statusVal] || "var(--mj-text-muted)"
    }

    if (background.length > 0) {
      indicator.style.setProperty("--mj-badge-bg", background)
    } else {
      indicator.style.removeProperty("--mj-badge-bg")
    }
    return
  }

  _syncCount(indicator, countText, label) {
    const count = this._getCount()
    const max = this._getMax()
    const showZero = this.hasAttribute("show-zero")

    const wasVisible = this._prevVisible
    const wasOverflow = this._prevOverflow

    const isVisible = count > 0 || showZero === true
    const isOverflow = count > max

    this._prevVisible = isVisible
    this._prevOverflow = isOverflow

    /* The bubble is decorative; the visually hidden text is the alternative. */
    indicator.removeAttribute("role")
    indicator.removeAttribute("aria-label")
    indicator.setAttribute("aria-hidden", "true")

    if (isVisible === false) {
      indicator.hidden = true
      countText.textContent = ""
      this._srText.textContent = ""
      if (wasVisible === true) {
        this.emit("mj-badge-hide", { count: count })
      }
      return
    }

    indicator.hidden = false

    const displayCount = isOverflow === true ? t("mj.badge.overflow", { max: max }) : String(count)
    countText.textContent = displayCount
    this._srText.textContent = label.length > 0 ? `${displayCount} ${label}` : displayCount

    if (isOverflow === true && wasOverflow === false) {
      this.emit("mj-badge-overflow", { count: count, max: max, displayCount: displayCount })
    }

    if (wasVisible === false || wasVisible === null) {
      this.emit("mj-badge-show", { count: count })
    }
    return
  }

  _syncDotStatus(indicator, variant, label) {
    indicator.hidden = false
    this._prevVisible = null
    this._prevOverflow = false
    if (this._countText !== null) {
      this._countText.textContent = ""
    }
    this._srText.textContent = ""

    if (label.length === 0 && variant === "dot" && this._warnedMissingLabel === false) {
      this._warnedMissingLabel = true
      console.warn("<mj-badge> variant=dot requires a label attribute for accessibility")
    }

    let resolvedLabel = label
    if (resolvedLabel.length === 0 && variant === "status") {
      const statusVal = this.getAttribute("status") || ""
      resolvedLabel = getStatusLabel(statusVal) || statusVal
    }

    if (resolvedLabel.length > 0) {
      indicator.setAttribute("role", "img")
      indicator.setAttribute("aria-label", resolvedLabel)
      indicator.removeAttribute("aria-hidden")
    } else {
      indicator.removeAttribute("role")
      indicator.removeAttribute("aria-label")
      indicator.setAttribute("aria-hidden", "true")
    }
    return
  }

  get count() {
    return this._getCount()
  }

  set count(value) {
    this.setAttribute("count", String(value))
    return
  }

  get displayCount() {
    const count = this._getCount()
    const max = this._getMax()
    const showZero = this.hasAttribute("show-zero")
    if (count === 0 && showZero === false) {
      return ""
    }
    if (count > max) {
      return t("mj.badge.overflow", { max: max })
    }
    return String(count)
  }

  /*
   * True when a count badge shows nothing (count 0 without show-zero). The
   * standard `hidden` property is left alone: it reflects the `hidden`
   * attribute as on any element.
   */
  get indicatorHidden() {
    const variant = this.getAttribute("variant") || "count"
    if (variant !== "count") {
      return false
    }
    return this.displayCount === ""
  }

  /*
   * Build an accessible name that includes the badge, for the control the
   * badge decorates. A "{count}" token in `template` is replaced by the
   * displayed count ("Notifications, {count} new"); without the token the
   * badge text is appended ("Inbox" becomes "Inbox, 7 unread messages").
   */
  getAriaLabel(template) {
    const base = template !== null && template !== undefined ? String(template) : ""
    const displayCount = this.displayCount
    const label = this.getAttribute("label") || ""

    let result = base
    if (base.indexOf("{count}") >= 0) {
      result = base.split("{count}").join(displayCount !== "" ? displayCount : "0")
    } else {
      const variant = this.getAttribute("variant") || "count"
      let badgeText = ""
      if (variant === "count") {
        if (displayCount !== "") {
          badgeText = label.length > 0 ? `${displayCount} ${label}` : displayCount
        }
      } else {
        badgeText = label.length > 0 ? label : getStatusLabel(this.getAttribute("status") || "")
      }
      if (badgeText.length > 0) {
        result = base.length > 0 ? `${base}, ${badgeText}` : badgeText
      }
    }
    return result
  }
}
