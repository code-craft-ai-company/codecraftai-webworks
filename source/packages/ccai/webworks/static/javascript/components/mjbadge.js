/*
 * mjbadge.js
 *
 * <mj-badge> -- count, dot, and status presence indicator. Overlays on
 * slotted content or renders inline. Status is never color-alone.
 */

import { MjElement } from "../core/mjelement.js";

const STATUS_COLORS = {
  online:  "var(--mj-color-success)",
  away:    "var(--mj-color-warning)",
  busy:    "var(--mj-color-danger)",
  offline: "var(--mj-color-neutral-400)",
  dnd:     "var(--mj-color-danger)"
};

const STATUS_LABELS = {
  online:  "Online",
  away:    "Away",
  busy:    "Busy",
  offline: "Offline",
  dnd:     "Do not disturb"
};

const STYLES = `
:host { display: inline-block; position: relative; }
:host([placement="inline"]) { display: inline-flex; align-items: center; gap: var(--mj-space-1); }

.indicator {
  display: inline-flex; align-items: center; justify-content: center;
  min-width: var(--mj-badge-size, 1.25rem);
  height: var(--mj-badge-size, 1.25rem);
  padding-inline: var(--mj-space-1);
  background: var(--mj-badge-bg, var(--mj-color-danger));
  color: var(--mj-badge-color, #fff);
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
    this._prevVisible = null
    this._prevOverflow = false
  }

  render() {
    const markup = `
      <slot></slot>
      <span class="indicator" part="indicator" aria-hidden="true">
        <span class="count-text" part="count"></span>
      </span>
    `
    return markup
  }

  afterRender() {
    this._indicator = this.$(".indicator")
    this._countText = this.$(".count-text")
    this._syncIndicator()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._indicator === undefined) {
      return
    }
    this._syncIndicator()
    return
  }

  _syncIndicator() {
    const indicator = this._indicator
    const countText = this._countText
    if (indicator === null) {
      return
    }

    const variant = this.getAttribute("variant") || "count"
    const label = this.getAttribute("label") || ""
    const colorOverride = this.getAttribute("color") || ""

    if (variant === "dot" || variant === "status") {
      this._syncDotStatus(indicator, variant, label, colorOverride)
    } else {
      this._syncCount(indicator, countText, label, colorOverride)
    }
    return
  }

  _syncCount(indicator, countText, label, colorOverride) {
    const raw = parseInt(this.getAttribute("count") || "0", 10)
    const count = raw < 0 ? 0 : Math.round(raw)
    const max = parseInt(this.getAttribute("max") || "99", 10)
    const showZero = this.hasAttribute("show-zero")

    const wasVisible = this._prevVisible
    const wasOverflow = this._prevOverflow

    const isVisible = count > 0 || showZero === true
    const isOverflow = count > max

    this._prevVisible = isVisible
    this._prevOverflow = isOverflow

    if (isVisible === false) {
      indicator.hidden = true
      if (wasVisible === true) {
        this.emit("mj-badge-hide", { count: count })
      }
      return
    }

    indicator.hidden = false
    indicator.setAttribute("aria-hidden", "true")

    if (isOverflow === true) {
      countText.textContent = `${max}+`
      if (wasOverflow === false) {
        this.emit("mj-badge-overflow", { count: count, max: max, displayCount: `${max}+` })
      }
    } else {
      countText.textContent = String(count)
    }

    if (colorOverride.length > 0) {
      indicator.style.setProperty("--mj-badge-bg", colorOverride)
    }

    if (wasVisible === false || wasVisible === null) {
      this.emit("mj-badge-show", { count: count })
    }
    return
  }

  _syncDotStatus(indicator, variant, label, colorOverride) {
    indicator.hidden = false
    const ct = this._countText
    if (ct !== null) {
      ct.textContent = ""
    }

    if (label.length === 0 && variant === "dot") {
      console.warn("<mj-badge> variant=dot requires a label attribute for accessibility")
    }

    if (label.length > 0) {
      indicator.setAttribute("role", "img")
      indicator.setAttribute("aria-label", label)
      indicator.removeAttribute("aria-hidden")
    } else {
      indicator.removeAttribute("role")
      indicator.setAttribute("aria-hidden", "true")
    }

    if (variant === "status") {
      const statusVal = this.getAttribute("status") || ""
      const statusColor = STATUS_COLORS[statusVal] || "var(--mj-text-muted)"
      const resolvedLabel = label.length > 0 ? label : (STATUS_LABELS[statusVal] || statusVal)
      indicator.style.setProperty("--mj-badge-bg", colorOverride.length > 0 ? colorOverride : statusColor)
      if (resolvedLabel.length > 0) {
        indicator.setAttribute("role", "img")
        indicator.setAttribute("aria-label", resolvedLabel)
        indicator.removeAttribute("aria-hidden")
      }
    } else if (colorOverride.length > 0) {
      indicator.style.setProperty("--mj-badge-bg", colorOverride)
    }
    return
  }

  get count() {
    return parseInt(this.getAttribute("count") || "0", 10)
  }

  set count(value) {
    this.setAttribute("count", String(value))
    return
  }

  get displayCount() {
    const count = this.count
    const max = parseInt(this.getAttribute("max") || "99", 10)
    const showZero = this.hasAttribute("show-zero")
    if (count === 0 && showZero === false) {
      return ""
    }
    if (count > max) {
      return `${max}+`
    }
    return String(count)
  }

  get hidden() {
    const variant = this.getAttribute("variant") || "count"
    if (variant !== "count") {
      return false
    }
    return this.displayCount === ""
  }
}

