/*
 * mjgauge.js
 *
 * <mj-gauge> -- single-value arc or linear meter with threshold bands
 * (color + pattern encoding), native <meter> for semantics, animated fill,
 * and Intl.NumberFormat value label.
 */

import { MjElement } from "../core/mjelement.js";
import { formatNumber } from "../core/intl.js";

const STYLES = `
:host { display: inline-block; }

.container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--mj-space-2);
  font-family: var(--mj-font-sans);
}

.title {
  font-size: var(--mj-gauge-title-font-size, var(--mj-font-size-sm));
  color: var(--mj-gauge-title-color, var(--mj-text-muted));
  font-weight: var(--mj-font-weight-medium);
  text-align: center;
}
.title:empty { display: none; }

.gauge-svg {
  display: block;
  overflow: visible;
}

.value-label {
  font-size: var(--mj-gauge-value-font-size, var(--mj-font-size-xl));
  font-weight: var(--mj-font-weight-bold);
  color: var(--mj-text);
  text-align: center;
  line-height: 1;
}

.minmax {
  display: flex;
  justify-content: space-between;
  width: 100%;
  font-size: var(--mj-font-size-xs);
  color: var(--mj-text-muted);
}

.linear-wrap {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: var(--mj-space-1);
}
.linear-track {
  width: 100%;
  height: var(--mj-gauge-track-width, 0.75rem);
  background: var(--mj-gauge-track-color, var(--mj-bg-muted));
  border-radius: var(--mj-radius-pill);
  position: relative;
  overflow: hidden;
}
.linear-fill {
  height: 100%;
  border-radius: var(--mj-radius-pill);
  background: var(--mj-gauge-fill-color, var(--mj-accent));
  transition: width var(--mj-gauge-transition-duration, var(--mj-motion-medium)) var(--mj-motion-ease);
}
@media (prefers-reduced-motion: reduce) {
  .linear-fill { transition: none; }
}

.sr-meter {
  position: absolute;
  width: 1px; height: 1px;
  overflow: hidden; clip: rect(0 0 0 0); clip-path: inset(50%);
  white-space: nowrap; margin: -1px;
}

.arc-fill {
  transition: stroke-dashoffset var(--mj-gauge-transition-duration, var(--mj-motion-medium)) var(--mj-motion-ease);
}
@media (prefers-reduced-motion: reduce) {
  .arc-fill { transition: none; }
}
`;

export class MjGauge extends MjElement {
  static tagName = "mj-gauge";
  static styles = STYLES;
  static watched = ["value", "min", "max", "low", "high", "optimum", "unit",
    "title", "shape", "show-needle", "show-min-max", "arc-degrees",
    "animated", "precision", "locale"];

  constructor() {
    super()
    this._thresholds = []
    this._prevValue = null
    this._containerEl = null
    this._svgEl = null
    this._linearFillEl = null
    this._meterEl = null
    this._valueLabelEl = null
    this._titleEl = null
  }

  render() {
    const markup = `
      <div class="container" part="container">
        <div class="title" part="title"></div>
        <div class="gauge-body"></div>
        <div class="value-label" part="value-label"></div>
        <meter class="sr-meter" min="0" max="100" value="0"></meter>
      </div>
    `
    return markup
  }

  afterRender() {
    this._containerEl = this.$(".container")
    this._titleEl = this.$(".title")
    this._gaugeBody = this.$(".gauge-body")
    this._valueLabelEl = this.$(".value-label")
    this._meterEl = this.$(".sr-meter")

    this._buildGauge()
    this._wireClick()
    return
  }

  _wireClick() {
    this.listen(this._containerEl, "click", () => {
      const v = this._value()
      const min = this._min()
      const max = this._max()
      const threshold = this._findThreshold(v)
      this.emit("mj-gauge-click", {
        value: v,
        min: min,
        max: max,
        threshold: threshold !== null ? threshold.label : null
      })
    })
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._gaugeBody === null || this._gaugeBody === undefined) { return }
    const prev = this._value()
    this._buildGauge()
    const next = this._value()

    if (name === "value" && oldValue !== newValue) {
      const threshold = this._findThreshold(next)
      this.emit("mj-gauge-value-change", {
        value: next,
        previousValue: prev,
        threshold: threshold !== null ? threshold.label : null
      })
    }
    return
  }

  _value() { return parseFloat(this.getAttribute("value") || "0") }
  _min() { return parseFloat(this.getAttribute("min") || "0") }
  _max() { return parseFloat(this.getAttribute("max") || "100") }

  _buildGauge() {
    const shape = this.getAttribute("shape") || "arc"
    const title = this.getAttribute("title") || ""
    this._titleEl.textContent = title

    const v = this._value()
    const min = this._min()
    const max = this._max()
    const unit = this.getAttribute("unit") || ""
    const precision = parseInt(this.getAttribute("precision") || "0", 10)
    const locale = this.getAttribute("locale") || undefined

    const pct = max > min ? Math.max(0, Math.min(1, (v - min) / (max - min))) : 0
    const fillColor = this._fillColor(v)

    const formatted = formatNumber(v, { maximumFractionDigits: precision, minimumFractionDigits: precision, ...(locale !== undefined ? {} : {}) })
    this._valueLabelEl.textContent = `${formatted}${unit}`

    this._syncMeter(v, min, max)

    if (shape === "linear") {
      this._buildLinear(pct, min, max, fillColor)
    } else {
      this._buildArc(pct, fillColor)
    }
    return
  }

  _buildArc(pct, fillColor) {
    const arcDeg = Math.max(90, Math.min(360, parseFloat(this.getAttribute("arc-degrees") || "240")))
    const size = 120
    const cx = size / 2
    const cy = size / 2
    const r = 48
    const strokeW = 12
    const startAngle = (180 + (360 - arcDeg) / 2) * (Math.PI / 180)
    const endAngle = startAngle + arcDeg * (Math.PI / 180)
    const circumference = arcDeg / 360 * 2 * Math.PI * r
    const offset = circumference * (1 - pct)

    const describeArc = (from, to) => {
      const x1 = cx + r * Math.cos(from)
      const y1 = cy + r * Math.sin(from)
      const x2 = cx + r * Math.cos(to)
      const y2 = cy + r * Math.sin(to)
      const large = (to - from) > Math.PI ? 1 : 0
      return `M${x1.toFixed(2)},${y1.toFixed(2)} A${r},${r} 0 ${large} 1 ${x2.toFixed(2)},${y2.toFixed(2)}`
    }

    const trackPath = describeArc(startAngle, endAngle)
    const showNeedle = this.hasAttribute("show-needle")
    const needleAngle = startAngle + pct * arcDeg * (Math.PI / 180)
    const nx = cx + (r - 6) * Math.cos(needleAngle)
    const ny = cy + (r - 6) * Math.sin(needleAngle)

    const svgMarkup = `
      <svg class="gauge-svg" part="track" viewBox="0 0 ${size} ${size}"
        width="${size}" height="${size}" aria-hidden="true">
        <defs>
          <pattern id="mj-g-stripe" width="4" height="4" patternUnits="userSpaceOnUse">
            <line x1="0" y1="4" x2="4" y2="0" stroke="${fillColor}" stroke-width="1" opacity="0.5"/>
          </pattern>
        </defs>
        <path d="${trackPath}" fill="none"
          stroke="var(--mj-gauge-track-color, var(--mj-bg-muted))"
          stroke-width="${strokeW}" stroke-linecap="round"/>
        <path class="arc-fill" part="fill" d="${trackPath}" fill="none"
          stroke="${fillColor}" stroke-width="${strokeW}" stroke-linecap="round"
          stroke-dasharray="${circumference.toFixed(2)}"
          stroke-dashoffset="${offset.toFixed(2)}"/>
        ${showNeedle ? `<line class="needle" part="needle"
          x1="${cx}" y1="${cy}"
          x2="${nx.toFixed(2)}" y2="${ny.toFixed(2)}"
          stroke="var(--mj-gauge-needle-color, var(--mj-text))"
          stroke-width="2" stroke-linecap="round"/>
          <circle cx="${cx}" cy="${cy}" r="4"
            fill="var(--mj-gauge-needle-color, var(--mj-text))"/>` : ""}
      </svg>`

    this._gaugeBody.innerHTML = svgMarkup
    return
  }

  _buildLinear(pct, min, max, fillColor) {
    const showMinMax = this.hasAttribute("show-min-max") || this.getAttribute("show-min-max") !== "false"
    const unit = this.getAttribute("unit") || ""

    const linearMarkup = `
      <div class="linear-wrap">
        <div class="linear-track" part="track" aria-hidden="true">
          <div class="linear-fill" part="fill"
            style="width:${(pct * 100).toFixed(2)}%;background:${fillColor}"></div>
        </div>
        ${showMinMax ? `<div class="minmax" part="threshold-markers">
          <span part="min-label">${min}${unit}</span>
          <span part="max-label">${max}${unit}</span>
        </div>` : ""}
      </div>`

    this._gaugeBody.innerHTML = linearMarkup
    return
  }

  _fillColor(v) {
    if (this._thresholds.length > 0) {
      const sorted = [...this._thresholds].sort((a, b) => b.value - a.value)
      for (let i = 0; i < sorted.length; i = i + 1) {
        if (v >= sorted[i].value) {
          return sorted[i].color || "var(--mj-gauge-fill-color, var(--mj-accent))"
        }
      }
    }
    return "var(--mj-gauge-fill-color, var(--mj-accent))"
  }

  _findThreshold(v) {
    if (this._thresholds.length === 0) { return null }
    const sorted = [...this._thresholds].sort((a, b) => b.value - a.value)
    for (let i = 0; i < sorted.length; i = i + 1) {
      if (v >= sorted[i].value) { return sorted[i] }
    }
    return null
  }

  _syncMeter(v, min, max) {
    this._meterEl.setAttribute("min", String(min))
    this._meterEl.setAttribute("max", String(max))
    this._meterEl.setAttribute("value", String(v))

    const low = this.getAttribute("low")
    const high = this.getAttribute("high")
    const optimum = this.getAttribute("optimum")
    if (low !== null && low.length > 0) { this._meterEl.setAttribute("low", low) }
    if (high !== null && high.length > 0) { this._meterEl.setAttribute("high", high) }
    if (optimum !== null && optimum.length > 0) { this._meterEl.setAttribute("optimum", optimum) }

    const title = this.getAttribute("title") || "Gauge"
    this._meterEl.setAttribute("aria-label", title)
    return
  }

  /* ----- scriptable API ----- */

  get thresholds() { return this._thresholds }
  set thresholds(v) {
    this._thresholds = Array.isArray(v) ? v : []
    if (this._gaugeBody !== null) { this._buildGauge() }
  }

  get formattedValue() {
    const v = this._value()
    const precision = parseInt(this.getAttribute("precision") || "0", 10)
    const unit = this.getAttribute("unit") || ""
    const formatted = formatNumber(v, { maximumFractionDigits: precision, minimumFractionDigits: precision })
    return `${formatted}${unit}`
  }
}
