/*
 * mjprogress.js
 *
 * <mj-progress> -- horizontal bar and circular ring progress indicators.
 * Supports determinate and indeterminate modes with full ARIA and
 * reduced-motion support.
 */

import { MjElement } from "../core/mjelement.js";
import { html } from "../core/html.js";
import { formatNumber } from "../core/intl.js";

const RING_SIZE = 44;
const STROKE_WIDTH = 4;
const RADIUS = (RING_SIZE - STROKE_WIDTH) / 2;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

const STYLES = `
/* The bar is the default variant and fills its container; only the ring is inline. */
:host { display: block; }
:host([variant="ring"]) { display: inline-block; }

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
}

:host([indeterminate]) .fill {
  width: 40%;
  animation: mj-bar-slide var(--mj-progress-animation-duration, 1.4s) linear infinite;
}
@keyframes mj-bar-slide {
  0%   { transform: translateX(-120%); }
  100% { transform: translateX(300%); }
}
/* The sweep follows the reading direction. */
@media (prefers-reduced-motion: no-preference) {
  :host([indeterminate]:dir(rtl)) .fill { animation-name: mj-bar-slide-rtl; }
}
@keyframes mj-bar-slide-rtl {
  0%   { transform: translateX(120%); }
  100% { transform: translateX(-300%); }
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
  static watched = [
    "variant", "value", "max", "indeterminate", "size", "label", "show-label", "value-text", "show-value",
    "aria-label", "aria-labelledby"
  ];

  constructor() {
    super()
    this._progressEl = null
    this._fillEl = null
    this._valueDefault = null
    this._labelSlot = null

    /* Variant the shadow DOM was built for. */
    this._renderedVariant = null

    /* Value and max last reported through mj-progress-change. */
    this._reportedValue = null
    this._reportedMax = null

    /* True once the missing-accessible-name warning was logged. */
    this._warnedMissingName = false
  }

  _getVariant() {
    const variant = this.getAttribute("variant") === "ring" ? "ring" : "bar"
    return variant
  }

  render() {
    const label = this.getAttribute("label") || ""
    const markup = this._getVariant() === "ring" ? this._renderRing(label) : this._renderBar(label)
    return markup
  }

  /*
   * The accessible name and the ARIA value attributes are not part of the
   * markup; _syncName and _syncState set them on the rendered element.
   */
  _renderBar(label) {
    const markup = html`
      <div class="bar-wrap">
        <div class="label-row">
          <span class="label-text" part="label"><slot name="label">${label}</slot></span>
          <span class="value-text" part="value-text"><slot name="value-text"><span class="value-default"></span></slot></span>
        </div>
        <div class="track" part="track">
          <div class="fill" part="fill" role="progressbar" tabindex="-1"></div>
        </div>
      </div>
    `
    return markup
  }

  _renderRing(label) {
    const markup = html`
      <div class="ring-wrap">
        <div class="ring-outer">
          <svg class="ring-svg" part="ring" viewBox="0 0 ${RING_SIZE} ${RING_SIZE}" role="progressbar" tabindex="-1">
            <circle class="ring-track" part="ring-track" cx="${RING_SIZE / 2}" cy="${RING_SIZE / 2}" r="${RADIUS}"/>
            <circle class="ring-fill"  part="ring-fill"  cx="${RING_SIZE / 2}" cy="${RING_SIZE / 2}" r="${RADIUS}"/>
          </svg>
          <div class="ring-center" part="center"><slot name="center"><span class="value-text" part="value-text"><span class="value-default"></span></span></slot></div>
        </div>
        <span class="label-text" part="label"><slot name="label">${label}</slot></span>
      </div>
    `
    return markup
  }

  afterRender() {
    this._renderedVariant = this._getVariant()
    this._progressEl = this.$("[role='progressbar']")
    this._fillEl = this.$(".fill") || this.$(".ring-fill")
    this._valueDefault = this.$(".value-default")
    this._labelSlot = this.$("slot[name='label']")

    this.listen(this._labelSlot, "slotchange", this._syncName.bind(this))

    this._reportedValue = this._resolvedValue()
    this._reportedMax = this._resolvedMax()
    this._syncName()
    this._syncState()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._progressEl === undefined || this._progressEl === null) {
      return
    }

    if (name === "variant" && this._getVariant() !== this._renderedVariant) {
      /* Bar and ring are different templates: build the other one. */
      this.shadowRoot.innerHTML = String(this.render())
      this.afterRender()
      return
    }

    if (name === "label") {
      if (this._labelSlot !== null) {
        this._labelSlot.textContent = newValue || ""
      }
    }

    if (name === "label" || name === "aria-label" || name === "aria-labelledby") {
      this._syncName()
    }

    const stateChanging =
      name === "value" || name === "max" || name === "indeterminate" || name === "value-text"
    if (stateChanging === true) {
      this._syncState()
    }

    if (name === "value" || name === "max") {
      this._reportChange()
    }
    return
  }

  /*
   * Report a value or max that differs from the last reported pair. A
   * repeated or replayed attribute change reports nothing.
   */
  _reportChange() {
    const value = this._resolvedValue()
    const max = this._resolvedMax()
    if (value === this._reportedValue && max === this._reportedMax) {
      return
    }
    this._reportedValue = value
    this._reportedMax = max

    this.emit("mj-progress-change", { value: value, max: max, percentage: this.percentage })
    if (value >= max) {
      this.emit("mj-progress-complete", { value: value, max: max })
    }
    return
  }

  /*
   * Name the progressbar from the host aria-labelledby / aria-label, then
   * the `label` attribute, then the slotted label text. With none of them
   * the attribute is left off and the missing name is reported once.
   */
  _syncName() {
    const progressEl = this._progressEl
    if (progressEl === undefined || progressEl === null) {
      return
    }

    const labelledBy = this.getAttribute("aria-labelledby")
    const labelElements = []
    if (labelledBy !== null) {
      const root = this.getRootNode()
      const ids = labelledBy.split(/\s+/)
      for (let index = 0; index < ids.length; index = index + 1) {
        const id = ids[index]
        const element = id !== "" && typeof root.getElementById === "function" ? root.getElementById(id) : null
        if (element !== null) {
          labelElements.push(element)
        }
      }
    }
    if ("ariaLabelledByElements" in progressEl) {
      progressEl.ariaLabelledByElements = labelElements.length > 0 ? labelElements : null
    }

    let name = this.getAttribute("aria-label")
    if (name === null || name.trim() === "") {
      name = this.getAttribute("label")
    }
    if (name === null || name.trim() === "") {
      name = ""
      const nodes = this._labelSlot !== null ? this._labelSlot.assignedNodes({ flatten: true }) : []
      for (let index = 0; index < nodes.length; index = index + 1) {
        name = name + nodes[index].textContent
      }
    }
    name = name.trim()

    if (name.length > 0) {
      progressEl.setAttribute("aria-label", name)
    } else {
      progressEl.removeAttribute("aria-label")
      if (labelElements.length === 0 && this._warnedMissingName === false) {
        this._warnedMissingName = true
        console.warn("<mj-progress>: set `label` (or aria-label / aria-labelledby) so the progressbar has an accessible name.", this)
      }
    }
    return
  }

  _syncState() {
    const indeterminate = this.hasAttribute("indeterminate")
    const progressEl = this._progressEl
    if (progressEl === undefined || progressEl === null) {
      return
    }

    const fillCircle = this.$(".ring-fill")
    const fillDiv = this.$(".fill")

    if (indeterminate === true) {
      progressEl.removeAttribute("aria-valuenow")
      progressEl.removeAttribute("aria-valuemin")
      progressEl.removeAttribute("aria-valuemax")
      progressEl.removeAttribute("aria-valuetext")

      /* The inline size of the determinate state would beat the indeterminate rules. */
      if (fillCircle !== null) {
        fillCircle.style.removeProperty("stroke-dashoffset")
      }
      if (fillDiv !== null) {
        fillDiv.style.removeProperty("width")
      }
      if (this._valueDefault !== null) {
        this._valueDefault.textContent = ""
      }
      return
    }

    const value = this._resolvedValue()
    const max = this._resolvedMax()
    const pct = (value / max) * 100

    progressEl.setAttribute("aria-valuenow", String(Math.round(value)))
    progressEl.setAttribute("aria-valuemin", "0")
    progressEl.setAttribute("aria-valuemax", String(max))

    const valueText = this.getAttribute("value-text")
    const hasValueText = valueText !== null && valueText.length > 0
    if (hasValueText === true) {
      progressEl.setAttribute("aria-valuetext", valueText)
    } else {
      progressEl.removeAttribute("aria-valuetext")
    }

    /* Visible value (shown with show-value): the value text, else the percentage. */
    if (this._valueDefault !== null) {
      this._valueDefault.textContent = hasValueText === true
        ? valueText
        : formatNumber(pct / 100, { style: "percent", maximumFractionDigits: 0 })
    }

    if (fillCircle !== null) {
      const offset = CIRCUMFERENCE - (pct / 100) * CIRCUMFERENCE
      fillCircle.style.strokeDashoffset = String(offset)
    }
    if (fillDiv !== null) {
      fillDiv.style.width = `${pct}%`
    }
    return
  }

  _resolvedValue() {
    const parsed = parseFloat(this.getAttribute("value") || "0")
    const max = this._resolvedMax()
    const numeric = Number.isFinite(parsed) === true ? parsed : 0
    const clamped = Math.min(Math.max(numeric, 0), max)
    return clamped
  }

  _resolvedMax() {
    const parsed = parseFloat(this.getAttribute("max") || "100")
    if (Number.isFinite(parsed) === false || parsed <= 0) {
      /* Reported once per invalid value; this is read on every sync. */
      const invalid = this.getAttribute("max")
      if (this._reportedInvalidMax !== invalid) {
        this._reportedInvalidMax = invalid
        console.error("<mj-progress> max must be > 0; defaulting to 100")
      }
      return 100
    }
    return parsed
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
