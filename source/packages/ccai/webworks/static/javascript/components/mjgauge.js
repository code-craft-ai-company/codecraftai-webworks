/*
 * mjgauge.js
 *
 * <mj-gauge> -- single-value arc or linear meter with threshold bands
 * (color + pattern encoding), native <meter> for semantics, animated fill,
 * and Intl.NumberFormat value label.
 *
 * The visual gauge is built with createElement / setAttribute / textContent
 * only -- `unit`, `title` and the threshold colours are untrusted and never
 * reach `innerHTML`. The structure (track, bands, fill, needle, labels) is
 * rebuilt only when the shape or the scale changes; a value change updates
 * the existing fill in place so the CSS transition has a state to animate
 * from.
 *
 * thresholds: [{ value, color, label, pattern }] -- `value` is where a band
 * starts; it runs to the next threshold (or `max`). `pattern` is one of
 * "stripes", "dots", "crosshatch", "stripes-reverse" or "solid"; bands
 * without one cycle through the first four so neighbours never share a
 * pattern.
 */

import { MjElement, nextId } from "../core/mjelement.js";
import { getLocale, t } from "../core/intl.js";

const SVG_NS = "http://www.w3.org/2000/svg";

/* Arc geometry in SVG user units. */
const ARC_SIZE = 120;
const ARC_CENTER = 60;
const ARC_RADIUS = 48;
const ARC_STROKE = 12;
const NEEDLE_HUB_RADIUS = 4;

/* The fill path is normalised to this length so the dash maths is a percentage. */
const PATH_LENGTH = 100;

const BAND_PATTERNS = ["stripes", "dots", "crosshatch", "stripes-reverse"];
const KNOWN_PATTERNS = ["stripes", "dots", "crosshatch", "stripes-reverse", "solid"];

/* Key of the accessible name used when the gauge has no `title`; resolved through t() at use time. */
const DEFAULT_TITLE_KEY = "mj.gauge.label";

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
.title[hidden] { display: none; }

.gauge-body {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: var(--mj-space-1);
  inline-size: var(--mj-gauge-size, 7.5rem);
}
.gauge-body.linear {
  inline-size: 100%;
  min-inline-size: var(--mj-gauge-size, 10rem);
}

.gauge-svg {
  display: block;
  inline-size: 100%;
  block-size: auto;
  overflow: visible;
}

.arc-track {
  fill: none;
  stroke: var(--mj-gauge-track-color, var(--mj-bg-muted));
  stroke-linecap: round;
}
.arc-band {
  fill: none;
  stroke-linecap: butt;
}
.arc-band-tint { opacity: 0.3; }
.arc-fill {
  fill: none;
  stroke: var(--mj-gauge-fill-color, var(--mj-accent));
  stroke-linecap: round;
  transition:
    stroke-dashoffset var(--mj-gauge-transition-duration, var(--mj-motion-medium)) var(--mj-motion-ease),
    stroke var(--mj-gauge-transition-duration, var(--mj-motion-medium)) var(--mj-motion-ease);
}
.arc-fill-pattern {
  fill: none;
  stroke-linecap: butt;
  transition: stroke-dashoffset var(--mj-gauge-transition-duration, var(--mj-motion-medium)) var(--mj-motion-ease);
}
.pattern-mark {
  stroke: var(--_mark-color, currentColor);
  fill: none;
}
.pattern-mark.filled {
  stroke: none;
  fill: var(--_mark-color, currentColor);
}
.fill-pattern-mark { --_mark-color: var(--mj-surface); opacity: 0.55; }

.needle {
  transform-origin: ${ARC_CENTER}px ${ARC_CENTER}px;
  transition: transform var(--mj-gauge-transition-duration, var(--mj-motion-medium)) var(--mj-motion-ease);
}
.needle line {
  stroke: var(--mj-gauge-needle-color, var(--mj-text));
  stroke-width: 2;
  stroke-linecap: round;
}
.needle circle { fill: var(--mj-gauge-needle-color, var(--mj-text)); }

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
  inline-size: 100%;
  font-size: var(--mj-font-size-xs);
  color: var(--mj-text-muted);
}

.linear-track {
  inline-size: 100%;
  block-size: var(--mj-gauge-track-width, 0.75rem);
  background: var(--mj-gauge-track-color, var(--mj-bg-muted));
  border-radius: var(--mj-radius-pill);
  position: relative;
  overflow: hidden;
}
.linear-band {
  position: absolute;
  inset-block: 0;
  color: var(--_band-color, var(--mj-text-muted));
}
.linear-band::before {
  content: "";
  position: absolute;
  inset: 0;
  background: currentColor;
  opacity: 0.3;
}
.linear-band::after,
.linear-fill::after {
  content: "";
  position: absolute;
  inset: 0;
}
.linear-fill {
  position: relative;
  block-size: 100%;
  border-radius: var(--mj-radius-pill);
  background: var(--mj-gauge-fill-color, var(--mj-accent));
  color: var(--mj-surface);
  overflow: hidden;
  transition:
    inline-size var(--mj-gauge-transition-duration, var(--mj-motion-medium)) var(--mj-motion-ease),
    background-color var(--mj-gauge-transition-duration, var(--mj-motion-medium)) var(--mj-motion-ease);
}
.linear-fill::after { opacity: 0.55; }

[data-pattern="stripes"]::after {
  background-image: repeating-linear-gradient(45deg, currentColor 0 1.5px, transparent 1.5px 6px);
}
[data-pattern="stripes-reverse"]::after {
  background-image: repeating-linear-gradient(-45deg, currentColor 0 1.5px, transparent 1.5px 6px);
}
[data-pattern="dots"]::after {
  background-image: radial-gradient(circle, currentColor 1.2px, transparent 1.6px);
  background-size: 6px 6px;
}
[data-pattern="crosshatch"]::after {
  background-image:
    repeating-linear-gradient(45deg, currentColor 0 1px, transparent 1px 6px),
    repeating-linear-gradient(-45deg, currentColor 0 1px, transparent 1px 6px);
}
.linear-band[data-pattern="solid"]::before { opacity: 0.6; }

.container.no-motion .arc-fill,
.container.no-motion .arc-fill-pattern,
.container.no-motion .needle,
.container.no-motion .linear-fill { transition: none; }

@media (prefers-reduced-motion: reduce) {
  .arc-fill, .arc-fill-pattern, .needle, .linear-fill { transition: none; }
}

.sr-meter {
  position: absolute;
  inline-size: 1px; block-size: 1px;
  overflow: hidden; clip: rect(0 0 0 0); clip-path: inset(50%);
  white-space: nowrap; margin: -1px;
}
`;

function createSvg(name, attributes) {
  const element = document.createElementNS(SVG_NS, name)
  const names = Object.keys(attributes || {})
  for (let index = 0; index < names.length; index = index + 1) {
    element.setAttribute(names[index], String(attributes[names[index]]))
  }
  return element
}

function toRadians(degrees) {
  const radians = degrees * (Math.PI / 180)
  return radians
}

/*
 * SVG path for a clockwise arc between two angles (degrees, measured
 * clockwise from the positive x axis because the SVG y axis points down).
 * A full turn has identical end points, which SVG draws as nothing, so it is
 * split into two half arcs.
 */
function describeArc(fromDegrees, toDegrees) {
  const pointAt = (degrees) => {
    const x = ARC_CENTER + ARC_RADIUS * Math.cos(toRadians(degrees))
    const y = ARC_CENTER + ARC_RADIUS * Math.sin(toRadians(degrees))
    return `${x.toFixed(2)},${y.toFixed(2)}`
  }

  const sweep = toDegrees - fromDegrees
  let path = ""

  if (sweep >= 359.99) {
    const middle = fromDegrees + sweep / 2
    path = `M${pointAt(fromDegrees)} A${ARC_RADIUS},${ARC_RADIUS} 0 0 1 ${pointAt(middle)} ` +
      `A${ARC_RADIUS},${ARC_RADIUS} 0 0 1 ${pointAt(toDegrees)}`
  } else {
    const largeArc = sweep > 180 ? 1 : 0
    path = `M${pointAt(fromDegrees)} A${ARC_RADIUS},${ARC_RADIUS} 0 ${largeArc} 1 ${pointAt(toDegrees)}`
  }

  return path
}

/* Build a 6x6 SVG <pattern> whose marks are painted in --_mark-color. */
function createPattern(id, patternName, markClass) {
  const pattern = createSvg("pattern", { id: id, width: 6, height: 6, patternUnits: "userSpaceOnUse" })
  let mark = null

  if (patternName === "dots") {
    mark = createSvg("circle", { cx: 3, cy: 3, r: 1.3, class: `pattern-mark filled ${markClass}` })
  } else if (patternName === "crosshatch") {
    mark = createSvg("path", { d: "M0,0 L6,6 M6,0 L0,6", "stroke-width": 1, class: `pattern-mark ${markClass}` })
  } else if (patternName === "stripes-reverse") {
    mark = createSvg("path", { d: "M-1,5 L1,7 M0,0 L6,6 M5,-1 L7,1", "stroke-width": 1.5, class: `pattern-mark ${markClass}` })
  } else if (patternName === "solid") {
    mark = createSvg("rect", { x: 0, y: 0, width: 6, height: 6, class: `pattern-mark filled ${markClass}` })
  } else {
    mark = createSvg("path", { d: "M-1,1 L1,-1 M0,6 L6,0 M5,7 L7,5", "stroke-width": 1.5, class: `pattern-mark ${markClass}` })
  }

  pattern.appendChild(mark)
  return pattern
}

export class MjGauge extends MjElement {
  static tagName = "mj-gauge";
  static styles = STYLES;
  static watched = ["value", "min", "max", "low", "high", "optimum", "unit",
    "title", "shape", "show-needle", "show-min-max", "arc-degrees",
    "animated", "precision", "locale"];

  constructor() {
    super()
    this._thresholds = []

    /* The value last drawn; null until the first draw. */
    this._lastValue = null

    /* The last invalid `locale` value that was reported, so it is logged once. */
    this._warnedLocale = null

    /* Signature of the structure currently in the gauge body. */
    this._structureKey = null

    this._containerEl = null
    this._gaugeBody = null
    this._meterEl = null
    this._valueLabelEl = null
    this._valueTextEl = null
    this._titleEl = null
    this._titleTextEl = null
    this._titleSlot = null

    /* Nodes of the current structure that a value change updates in place. */
    this._fillEl = null
    this._fillPatternEl = null
    this._fillPatternDefs = null
    this._needleEl = null
    this._minLabelEl = null
    this._maxLabelEl = null
    this._arcStart = 0
    this._arcSweep = 0
  }

  render() {
    const markup = `
      <div class="container" part="container">
        <div class="title" part="title" hidden><slot name="title"><span class="title-text"></span></slot></div>
        <div class="gauge-body" aria-hidden="true"></div>
        <div class="value-label" part="value-label"><slot name="value-label"><span class="value-text"></span></slot></div>
        <meter class="sr-meter" min="0" max="100" value="0"></meter>
      </div>
    `
    return markup
  }

  afterRender() {
    this._containerEl = this.$(".container")
    this._titleEl = this.$(".title")
    this._titleTextEl = this.$(".title-text")
    this._titleSlot = this.$("slot[name='title']")
    this._gaugeBody = this.$(".gauge-body")
    this._valueLabelEl = this.$(".value-label")
    this._valueTextEl = this.$(".value-text")
    this._meterEl = this.$(".sr-meter")

    /* The shadow DOM is new, so the structure has to be built again. */
    this._structureKey = null
    this._lastValue = null

    this.listen(this._titleSlot, "slotchange", () => { this._syncTitle() })

    this._buildGauge()
    this._wireClick()
    return
  }

  _wireClick() {
    this.listen(this._containerEl, "click", () => {
      const value = this._value()
      const threshold = this._findThreshold(value)
      this.emit("mj-gauge-click", {
        value: value,
        min: this._min(),
        max: this._max(),
        threshold: threshold !== null ? this._thresholdLabel(threshold) : null
      })
    })
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._gaugeBody === null || this._gaugeBody === undefined) {
      return
    }

    /*
     * `previousValue` is the value that was on screen before this change.
     * Comparing against it (and not against the attribute strings) keeps the
     * handler idempotent: a change that is delivered twice, or that does not
     * alter the number, emits nothing the second time.
     */
    const previous = this._lastValue
    this._buildGauge()
    const next = this._value()

    if (name === "value" && previous !== null && previous !== next) {
      const threshold = this._findThreshold(next)
      this.emit("mj-gauge-value-change", {
        value: next,
        previousValue: previous,
        threshold: threshold !== null ? this._thresholdLabel(threshold) : null
      })
    }
    return
  }

  _number(name, fallback) {
    const parsed = parseFloat(this.getAttribute(name) || "")
    const value = Number.isFinite(parsed) === true ? parsed : fallback
    return value
  }

  _value() {
    const value = this._number("value", 0)
    return value
  }

  _min() {
    const value = this._number("min", 0)
    return value
  }

  _max() {
    const value = this._number("max", 100)
    return value
  }

  _arcDegrees() {
    const requested = this._number("arc-degrees", 240)
    const clamped = Math.max(90, Math.min(360, requested))
    return clamped
  }

  /* Position of `value` on the scale as a fraction between 0 and 1. */
  _fraction(value) {
    const min = this._min()
    const max = this._max()
    let fraction = 0
    if (max > min) {
      fraction = Math.max(0, Math.min(1, (value - min) / (max - min)))
    }
    return fraction
  }

  /* Thresholds with a usable numeric value, ascending. */
  _sortedThresholds() {
    const usable = []
    for (let index = 0; index < this._thresholds.length; index = index + 1) {
      const threshold = this._thresholds[index]
      if (threshold !== null && typeof threshold === "object" && Number.isFinite(Number(threshold.value)) === true) {
        usable.push(threshold)
      }
    }
    usable.sort((a, b) => Number(a.value) - Number(b.value))
    return usable
  }

  /* The band `value` falls in: the highest threshold at or below it. */
  _findThreshold(value) {
    const sorted = this._sortedThresholds()
    let found = null
    for (let index = 0; index < sorted.length; index = index + 1) {
      if (value >= Number(sorted[index].value)) {
        found = sorted[index]
      }
    }
    return found
  }

  _thresholdLabel(threshold) {
    const label = threshold.label !== undefined && threshold.label !== null ? String(threshold.label) : null
    return label
  }

  /* Pattern name for the band at `index` in the sorted threshold list. */
  _bandPattern(threshold, index) {
    const requested = typeof threshold.pattern === "string" ? threshold.pattern : ""
    const pattern = KNOWN_PATTERNS.indexOf(requested) >= 0
      ? requested
      : BAND_PATTERNS[index % BAND_PATTERNS.length]
    return pattern
  }

  _formatter(options) {
    const locale = this.getAttribute("locale") || ""
    let formatter = null
    if (locale.length > 0) {
      try {
        formatter = new Intl.NumberFormat(locale, options)
      } catch (error) {
        if (this._warnedLocale !== locale) {
          console.warn(`<mj-gauge>: locale "${locale}" is not a valid BCP 47 tag; using the default locale.`)
          this._warnedLocale = locale
        }
      }
    }
    if (formatter === null) {
      formatter = new Intl.NumberFormat(getLocale(), options)
    }
    return formatter
  }

  _formatValue(value) {
    const requested = parseInt(this.getAttribute("precision") || "0", 10)
    const precision = Number.isFinite(requested) === true ? Math.max(0, Math.min(20, requested)) : 0
    const formatter = this._formatter({ maximumFractionDigits: precision, minimumFractionDigits: precision })
    const unit = this.getAttribute("unit") || ""
    const formatted = `${formatter.format(value)}${unit}`
    return formatted
  }

  _formatBound(value) {
    const formatter = this._formatter({ maximumFractionDigits: 20 })
    const unit = this.getAttribute("unit") || ""
    const formatted = `${formatter.format(value)}${unit}`
    return formatted
  }

  _syncTitle() {
    const title = this.getAttribute("title") || ""
    this._titleTextEl.textContent = title

    const slotted = this._titleSlot.assignedNodes({ flatten: true })
    /* The fallback <span> counts as assigned content when nothing is slotted. */
    const hasSlotted = slotted.length > 0 && slotted[0] !== this._titleTextEl
    this._titleEl.hidden = hasSlotted === false && title.length === 0
    return
  }

  /*
   * Bring the whole gauge in line with the attributes and thresholds.
   * Rebuilds the structure only when its signature changed, then updates
   * the labels, the meter and the fill.
   */
  _buildGauge() {
    const shape = this.getAttribute("shape") === "linear" ? "linear" : "arc"
    const min = this._min()
    const max = this._max()
    const value = this._value()

    if (max <= min) {
      console.error("<mj-gauge>: `max` must be greater than `min`; the gauge renders an empty track.")
    }

    this._syncTitle()
    this._containerEl.classList.toggle("no-motion", this.getAttribute("animated") === "false")

    const showMinMax = this.getAttribute("show-min-max") !== "false"
    const showNeedle = this.hasAttribute("show-needle") === true && this.getAttribute("show-needle") !== "false"
    const structureKey = [
      shape, min, max, this._arcDegrees(), showNeedle, showMinMax, this._thresholdSignature()
    ].join("|")

    if (structureKey !== this._structureKey) {
      this._structureKey = structureKey
      this._gaugeBody.textContent = ""
      this._gaugeBody.classList.toggle("linear", shape === "linear")
      this._fillEl = null
      this._fillPatternEl = null
      this._fillPatternDefs = null
      this._needleEl = null
      this._minLabelEl = null
      this._maxLabelEl = null

      if (shape === "linear") {
        this._buildLinear()
      } else {
        this._buildArc(showNeedle)
      }
      if (showMinMax === true) {
        this._buildMinMax()
      }
    }

    this._valueTextEl.textContent = this._formatValue(value)
    if (this._minLabelEl !== null) {
      this._minLabelEl.textContent = this._formatBound(min)
      this._maxLabelEl.textContent = this._formatBound(max)
    }

    this._syncMeter(value, min, max)
    this._updateFill(shape, value)
    this._lastValue = value
    return
  }

  /* Changes whenever a threshold boundary, colour or pattern changes. */
  _thresholdSignature() {
    const sorted = this._sortedThresholds()
    const parts = []
    for (let index = 0; index < sorted.length; index = index + 1) {
      const threshold = sorted[index]
      parts.push(`${Number(threshold.value)}:${String(threshold.color)}:${this._bandPattern(threshold, index)}`)
    }
    const signature = parts.join(",")
    return signature
  }

  /*
   * Bands as [{ from, to, color, pattern }] fractions of the scale. A band
   * starts at its threshold and ends where the next one starts.
   */
  _bands() {
    const sorted = this._sortedThresholds()
    const bands = []
    for (let index = 0; index < sorted.length; index = index + 1) {
      const threshold = sorted[index]
      const from = this._fraction(Number(threshold.value))
      const to = index + 1 < sorted.length ? this._fraction(Number(sorted[index + 1].value)) : 1
      if (to > from) {
        bands.push({
          from: from,
          to: to,
          color: typeof threshold.color === "string" ? threshold.color : "",
          pattern: this._bandPattern(threshold, index)
        })
      }
    }
    return bands
  }

  _buildArc(showNeedle) {
    const arcDegrees = this._arcDegrees()

    /* The opening is centred at the bottom (90 degrees in SVG space). */
    const startDegrees = 90 + (360 - arcDegrees) / 2
    this._arcStart = startDegrees
    this._arcSweep = arcDegrees

    /* Crop the viewBox to the drawn arc so a dome does not reserve empty space below it. */
    const endpointY = ARC_CENTER + ARC_RADIUS * Math.sin(toRadians(startDegrees))
    const lowestArcY = arcDegrees >= 359.99 ? ARC_CENTER + ARC_RADIUS : Math.max(endpointY, ARC_CENTER)
    const lowestY = Math.max(lowestArcY + ARC_STROKE / 2, ARC_CENTER + NEEDLE_HUB_RADIUS)
    const viewHeight = Math.min(ARC_SIZE, Math.ceil(lowestY + 2))

    const svg = createSvg("svg", {
      class: "gauge-svg",
      viewBox: `0 0 ${ARC_SIZE} ${viewHeight}`,
      focusable: "false"
    })

    const defs = createSvg("defs", {})
    svg.appendChild(defs)

    const trackPath = describeArc(startDegrees, startDegrees + arcDegrees)
    svg.appendChild(createSvg("path", {
      class: "arc-track", part: "track", d: trackPath, "stroke-width": ARC_STROKE
    }))

    const bands = this._bands()
    if (bands.length > 0) {
      const bandGroup = createSvg("g", { class: "arc-bands", part: "threshold-markers" })
      for (let index = 0; index < bands.length; index = index + 1) {
        const band = bands[index]
        const bandPath = describeArc(
          startDegrees + band.from * arcDegrees,
          startDegrees + band.to * arcDegrees
        )

        const tint = createSvg("path", {
          class: "arc-band arc-band-tint", d: bandPath, "stroke-width": ARC_STROKE
        })
        tint.style.stroke = band.color

        const patternId = nextId("mj-gauge-band")
        const pattern = createPattern(patternId, band.pattern, "band-pattern-mark")
        pattern.style.setProperty("--_mark-color", band.color)
        defs.appendChild(pattern)

        const marks = createSvg("path", {
          class: "arc-band", d: bandPath, "stroke-width": ARC_STROKE, stroke: `url(#${patternId})`
        })

        bandGroup.appendChild(tint)
        bandGroup.appendChild(marks)
      }
      svg.appendChild(bandGroup)
    }

    const fill = createSvg("path", {
      class: "arc-fill", part: "fill", d: trackPath, "stroke-width": ARC_STROKE,
      pathLength: PATH_LENGTH, "stroke-dasharray": `${PATH_LENGTH} ${PATH_LENGTH}`
    })
    svg.appendChild(fill)
    this._fillEl = fill

    /* The pattern of the active band, drawn over the solid fill. */
    const fillPattern = createSvg("path", {
      class: "arc-fill-pattern", d: trackPath, "stroke-width": ARC_STROKE,
      pathLength: PATH_LENGTH, "stroke-dasharray": `${PATH_LENGTH} ${PATH_LENGTH}`
    })
    svg.appendChild(fillPattern)
    this._fillPatternEl = fillPattern
    this._fillPatternDefs = defs

    if (showNeedle === true) {
      const needle = createSvg("g", { class: "needle", part: "needle" })
      needle.appendChild(createSvg("line", {
        x1: ARC_CENTER, y1: ARC_CENTER, x2: ARC_CENTER + ARC_RADIUS - 6, y2: ARC_CENTER
      }))
      needle.appendChild(createSvg("circle", { cx: ARC_CENTER, cy: ARC_CENTER, r: NEEDLE_HUB_RADIUS }))
      svg.appendChild(needle)
      this._needleEl = needle
    }

    this._gaugeBody.appendChild(svg)
    return
  }

  _buildLinear() {
    const track = document.createElement("div")
    track.className = "linear-track"
    track.setAttribute("part", "track")

    const bands = this._bands()
    for (let index = 0; index < bands.length; index = index + 1) {
      const band = bands[index]
      const bandEl = document.createElement("div")
      bandEl.className = "linear-band"
      bandEl.setAttribute("part", "threshold-markers")
      bandEl.setAttribute("data-pattern", band.pattern)
      bandEl.style.insetInlineStart = `${(band.from * 100).toFixed(2)}%`
      bandEl.style.inlineSize = `${((band.to - band.from) * 100).toFixed(2)}%`
      bandEl.style.setProperty("--_band-color", band.color)
      track.appendChild(bandEl)
    }

    const fill = document.createElement("div")
    fill.className = "linear-fill"
    fill.setAttribute("part", "fill")
    track.appendChild(fill)
    this._fillEl = fill

    this._gaugeBody.appendChild(track)
    return
  }

  _buildMinMax() {
    const row = document.createElement("div")
    row.className = "minmax"
    row.setAttribute("part", "min-max")

    const minLabel = document.createElement("span")
    minLabel.setAttribute("part", "min-label")
    const maxLabel = document.createElement("span")
    maxLabel.setAttribute("part", "max-label")

    row.appendChild(minLabel)
    row.appendChild(maxLabel)
    this._gaugeBody.appendChild(row)

    this._minLabelEl = minLabel
    this._maxLabelEl = maxLabel
    return
  }

  /*
   * Move the existing fill (and needle) to `value` and give it the colour
   * and pattern of the band the value falls in.
   */
  _updateFill(shape, value) {
    if (this._fillEl === null) {
      return
    }

    const fraction = this._fraction(value)
    const sorted = this._sortedThresholds()
    const active = this._findThreshold(value)
    const activeColor = active !== null && typeof active.color === "string" ? active.color : ""
    const activePattern = active !== null ? this._bandPattern(active, sorted.indexOf(active)) : ""

    if (shape === "linear") {
      this._fillEl.style.width = `${(fraction * 100).toFixed(2)}%`
      this._fillEl.style.backgroundColor = ""
      if (activeColor.length > 0) {
        this._fillEl.style.backgroundColor = activeColor
      }
      if (activePattern.length > 0 && activePattern !== "solid") {
        this._fillEl.setAttribute("data-pattern", activePattern)
      } else {
        this._fillEl.removeAttribute("data-pattern")
      }
      return
    }

    const offset = PATH_LENGTH * (1 - fraction)
    this._fillEl.setAttribute("stroke-dashoffset", offset.toFixed(2))
    /* A zero-length dash still paints its round cap, so hide the fill at zero. */
    this._fillEl.style.visibility = fraction > 0 ? "visible" : "hidden"
    this._fillEl.style.stroke = ""
    if (activeColor.length > 0) {
      this._fillEl.style.stroke = activeColor
    }

    if (activePattern.length > 0 && activePattern !== "solid" && fraction > 0) {
      const previous = this._fillPatternDefs.querySelector(".fill-pattern")
      if (previous !== null) {
        previous.remove()
      }
      const patternId = nextId("mj-gauge-fill")
      const pattern = createPattern(patternId, activePattern, "fill-pattern-mark")
      pattern.classList.add("fill-pattern")
      this._fillPatternDefs.appendChild(pattern)
      this._fillPatternEl.setAttribute("stroke", `url(#${patternId})`)
      this._fillPatternEl.setAttribute("stroke-dashoffset", offset.toFixed(2))
      this._fillPatternEl.style.visibility = "visible"
    } else {
      this._fillPatternEl.style.visibility = "hidden"
    }

    if (this._needleEl !== null) {
      const needleDegrees = this._arcStart + fraction * this._arcSweep
      this._needleEl.style.transform = `rotate(${needleDegrees.toFixed(2)}deg)`
    }
    return
  }

  _syncMeter(value, min, max) {
    this._meterEl.setAttribute("min", String(min))
    this._meterEl.setAttribute("max", String(max))
    this._meterEl.setAttribute("value", String(value))

    const mirrored = ["low", "high", "optimum"]
    for (let index = 0; index < mirrored.length; index = index + 1) {
      const name = mirrored[index]
      const attribute = this.getAttribute(name)
      if (attribute !== null && attribute.length > 0) {
        this._meterEl.setAttribute(name, attribute)
      } else {
        this._meterEl.removeAttribute(name)
      }
    }

    const title = this.getAttribute("title") || t(DEFAULT_TITLE_KEY)
    this._meterEl.setAttribute("aria-label", title)

    /* The band label is the text equivalent of the fill colour and pattern. */
    const threshold = this._findThreshold(value)
    const bandLabel = threshold !== null ? this._thresholdLabel(threshold) : null
    const valueText = bandLabel !== null && bandLabel.length > 0
      ? `${this._formatValue(value)}, ${bandLabel}`
      : this._formatValue(value)
    this._meterEl.setAttribute("aria-valuetext", valueText)
    return
  }

  /* ----- scriptable API ----- */

  get thresholds() {
    return this._thresholds
  }

  set thresholds(value) {
    this._thresholds = Array.isArray(value) === true ? value : []
    if (this._gaugeBody !== null && this._gaugeBody !== undefined) {
      this._buildGauge()
    }
    return
  }

  get formattedValue() {
    const formatted = this._formatValue(this._value())
    return formatted
  }
}
