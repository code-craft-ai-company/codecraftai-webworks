/*
 * mjprogress.js
 *
 * <mj-progress> -- horizontal bar and circular ring progress indicators.
 * Supports determinate and indeterminate modes with full ARIA and
 * reduced-motion support.
 */

import { MjElement } from "../core/mjelement.js";

const RING_SIZE = 44;
const STROKE_WIDTH = 4;
const RADIUS = (RING_SIZE - STROKE_WIDTH) / 2;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

const STYLES = `
:host { display: inline-block; }
:host([variant="bar"]) { display: block; }

/* ---- bar ---- */
.bar-wrap { display: flex; flex-direction: column; gap: var(--mj-progress-label-gap, var(--mj-space-1)); }
.label-row { display: flex; justify-content: space-between; font-size: var(--mj-font-size-sm); color: var(--mj-text-muted); }
:host(:not([show-label])) .label-text { display: none; }
:host(:not([show-value])) .value-text  { display: none; }

.track {
  width: 100%;
  height: var(--mj-progress-height, 0.5rem);
  background: var(--mj-progress-track-color, var(--mj-border));
  border-radius: var(--mj-progress-border-radius, var(--mj-radius-pill));
  overflow: hidden;
}
.fill {
  height: 100%;
  background: var(--mj-progress-fill-color, var(--mj-accent));
  border-radius: inherit;
  width: 0%;
  transition: width var(--mj-motion-medium) var(--mj-motion-ease);
  transform-origin: inline-start center;
}

:host([indeterminate]) .fill {
  width: 40%;
  animation: mj-bar-slide var(--mj-progress-animation-duration, 1.4s) linear infinite;
}
@keyframes mj-bar-slide {
  0%   { transform: translateX(-120%); }
  100% { transform: translateX(300%); }
}
@media (prefers-reduced-motion: reduce) {
  :host([indeterminate]) .fill { animation: mj-bar-pulse var(--mj-progress-animation-duration, 1.4s) ease-in-out infinite; transform: none; width: 100%; }
  @keyframes mj-bar-pulse { 0%, 100% { opacity: 0.4; } 50% { opacity: 1; } }
  .fill { transition: none; }
}

/* ---- ring ---- */
.ring-wrap { display: inline-flex; flex-direction: column; align-items: center; gap: var(--mj-progress-label-gap, var(--mj-space-2)); }
.ring-svg {
  width: var(--mj-progress-ring-size, 3rem);
  height: var(--mj-progress-ring-size, 3rem);
  transform: rotate(-90deg);
}
.ring-track { fill: none; stroke: var(--mj-progress-track-color, var(--mj-border)); stroke-width: var(--mj-progress-ring-stroke-width, ${STROKE_WIDTH}); }
.ring-fill  {
  fill: none;
  stroke: var(--mj-progress-fill-color, var(--mj-accent));
  stroke-width: var(--mj-progress-ring-stroke-width, ${STROKE_WIDTH});
  stroke-linecap: round;
  stroke-dasharray: ${CIRCUMFERENCE};
  stroke-dashoffset: ${CIRCUMFERENCE};
  transition: stroke-dashoffset var(--mj-motion-medium) var(--mj-motion-ease);
}
.ring-center {
  position: absolute; inset: 0;
  display: flex; align-items: center; justify-content: center;
  overflow: hidden; font-size: var(--mj-font-size-sm);
}
.ring-outer { position: relative; width: var(--mj-progress-ring-size, 3rem); height: var(--mj-progress-ring-size, 3rem); }

:host([indeterminate]) .ring-svg {
  animation: mj-ring-spin var(--mj-progress-animation-duration, 1.2s) linear infinite;
}
:host([indeterminate]) .ring-fill {
  stroke-dashoffset: ${CIRCUMFERENCE * 0.25};
  transition: none;
}
@keyframes mj-ring-spin { to { transform: rotate(270deg); } }
@media (prefers-reduced-motion: reduce) {
  :host([indeterminate]) .ring-svg { animation: mj-ring-pulse 1.2s ease-in-out infinite; }
  @keyframes mj-ring-pulse { 0%, 100% { opacity: 0.4; } 50% { opacity: 1; } }
  .ring-fill { transition: none; }
}

/* sizes */
:host([size="sm"]) { --mj-progress-height: 0.25rem; --mj-progress-ring-size: 1.5rem; }
:host([size="lg"]) { --mj-progress-height: 0.75rem; --mj-progress-ring-size: 5rem; }
`;

export class MjProgress extends MjElement {
  static tagName = "mj-progress";
  static styles = STYLES;
  static watched = ["variant", "value", "max", "indeterminate", "size", "label", "show-label", "value-text", "show-value"];

  render() {
    const variant = this.getAttribute("variant") || "bar"
    const label = this.getAttribute("label") || ""
    const markup = variant === "ring" ? this._renderRing(label) : this._renderBar(label)
    return markup
  }

  _renderBar(label) {
    const markup = `
      <div class="bar-wrap">
        <div class="label-row">
          <span class="label-text" part="label"><slot name="label">${label}</slot></span>
          <span class="value-text" part="value-text"><slot name="value-text"></slot></span>
        </div>
        <div class="track" part="track">
          <div class="fill" part="fill" role="progressbar" aria-label="${label}" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0" tabindex="-1"></div>
        </div>
      </div>
    `
    return markup
  }

  _renderRing(label) {
    const markup = `
      <div class="ring-wrap">
        <div class="ring-outer">
          <svg class="ring-svg" part="ring" viewBox="0 0 ${RING_SIZE} ${RING_SIZE}" role="progressbar" aria-label="${label}" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0" tabindex="-1">
            <circle class="ring-track" part="ring-track" cx="${RING_SIZE / 2}" cy="${RING_SIZE / 2}" r="${RADIUS}"/>
            <circle class="ring-fill"  part="ring-fill"  cx="${RING_SIZE / 2}" cy="${RING_SIZE / 2}" r="${RADIUS}"/>
          </svg>
          <div class="ring-center" part="center"><slot name="center"></slot></div>
        </div>
        <span class="label-text" part="label"><slot name="label">${label}</slot></span>
      </div>
    `
    return markup
  }

  afterRender() {
    this._progressEl = this.$("[role='progressbar']")
    this._fillEl = this.$(".fill") || this.$(".ring-fill")
    this._syncState()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._progressEl === undefined) {
      return
    }

    const valueChanging = name === "value" || name === "max" || name === "indeterminate"
    if (valueChanging === true) {
      this._syncState()

      if (name === "value" || name === "max") {
        const value = this._resolvedValue()
        const max = this._resolvedMax()
        const pct = this.percentage
        this.emit("mj-progress-change", { value: value, max: max, percentage: pct })
        if (value >= max) {
          this.emit("mj-progress-complete", { value: value, max: max })
        }
      }
    }

    if (name === "label") {
      if (this._progressEl !== null) {
        this._progressEl.setAttribute("aria-label", newValue || "")
      }
    }
    return
  }

  _syncState() {
    const indeterminate = this.hasAttribute("indeterminate")
    const progressEl = this._progressEl
    if (progressEl === null) {
      return
    }

    if (indeterminate === true) {
      progressEl.removeAttribute("aria-valuenow")
      progressEl.removeAttribute("aria-valuemin")
      progressEl.removeAttribute("aria-valuemax")
      return
    }

    const value = this._resolvedValue()
    const max = this._resolvedMax()
    const pct = (value / max) * 100

    progressEl.setAttribute("aria-valuenow", String(Math.round(value)))
    progressEl.setAttribute("aria-valuemin", "0")
    progressEl.setAttribute("aria-valuemax", String(max))

    const valueText = this.getAttribute("value-text")
    if (valueText !== null && valueText.length > 0) {
      progressEl.setAttribute("aria-valuetext", valueText)
    }

    const variant = this.getAttribute("variant") || "bar"
    if (variant === "ring") {
      const offset = CIRCUMFERENCE - (pct / 100) * CIRCUMFERENCE
      const fillCircle = this.$(".ring-fill")
      if (fillCircle !== null) {
        fillCircle.style.strokeDashoffset = String(offset)
      }
    } else {
      const fillDiv = this.$(".fill")
      if (fillDiv !== null) {
        fillDiv.style.width = `${pct}%`
      }
    }
    return
  }

  _resolvedValue() {
    const raw = parseFloat(this.getAttribute("value") || "0")
    const max = this._resolvedMax()
    const clamped = Math.min(Math.max(raw, 0), max)
    return clamped
  }

  _resolvedMax() {
    const raw = parseFloat(this.getAttribute("max") || "100")
    if (raw <= 0) {
      console.error("<mj-progress> max must be > 0; defaulting to 100")
      return 100
    }
    return raw
  }

  get value() {
    return this._resolvedValue()
  }

  set value(v) {
    this.setAttribute("value", String(v))
    this.removeAttribute("indeterminate")
    return
  }

  get percentage() {
    const pct = Math.round((this._resolvedValue() / this._resolvedMax()) * 1000) / 10
    return pct
  }
}
