/*
 * mjsparkline.js
 *
 * <mj-sparkline> -- compact inline SVG trend chart supporting line, area, bar,
 * and win/loss types. Built-in SVG renderer with no external dependencies.
 * Paired text or a `label` attribute provides the accessible equivalent.
 *
 * Geometry:
 *   - The value domain is the data range, widened to include the
 *     `reference-value` when one is set, and (bar type) the baseline, so a
 *     bar's length is proportional to its value.
 *   - The baseline of area and bar types is the `reference-value`, or zero
 *     when none is set, clamped into the plot. Bars and area segments are
 *     drawn between the value and that baseline.
 *   - Bars and win/loss columns use a band layout: the width is divided into
 *     one band per value and each column sits inside its band, so nothing is
 *     drawn outside the SVG box.
 *
 * The sparkline is a display component. Set the `interactive` attribute when
 * the host handles `mj-sparkline-click`: the marks then become focusable
 * buttons with a text label and react to Enter / Space as well as the mouse.
 */

import { MjElement } from "../core/mjelement.js";
import { getLocale, t } from "../core/intl.js";

const SVG_NS = "http://www.w3.org/2000/svg";

/* Vertical breathing room so strokes and caps are not cut at the box edge. */
const PLOT_PADDING = 2;

const STYLES = `
:host {
  display: inline-block;
  vertical-align: middle;
}

.container {
  display: inline-block;
  position: relative;
  line-height: 0;
}

svg {
  display: block;
  overflow: visible;
}

.line {
  fill: none;
  stroke: var(--mj-sparkline-color, var(--mj-accent));
  stroke-width: var(--mj-sparkline-stroke-width, 1.5px);
  stroke-linecap: round;
  stroke-linejoin: round;
}
.point {
  fill: var(--mj-sparkline-color, var(--mj-accent));
}
.area {
  fill: var(--mj-sparkline-color, var(--mj-accent));
  opacity: var(--mj-sparkline-area-opacity, 0.2);
}
.bar-pos {
  fill: var(--mj-sparkline-color, var(--mj-accent));
}
.bar-neg {
  fill: var(--mj-sparkline-negative-color, var(--mj-color-danger, #dc2626));
}
.bar-zero {
  fill: var(--mj-sparkline-neutral-color, var(--mj-text-muted));
}
.end-dot {
  fill: var(--mj-sparkline-color, var(--mj-accent));
}
.reference-line {
  stroke: var(--mj-sparkline-reference-color, var(--mj-border));
  stroke-width: 1;
  stroke-dasharray: var(--mj-sparkline-reference-dash, 3 2);
}

svg.interactive .mark { cursor: pointer; }
svg.interactive .mark:focus { outline: none; }
svg.interactive .mark:focus-visible {
  outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring);
  outline-offset: 1px;
}

.fallback {
  position: absolute;
  inline-size: 1px;
  block-size: 1px;
  overflow: hidden;
  clip-path: inset(50%);
  white-space: nowrap;
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

function formatCoordinate(value) {
  const text = value.toFixed(1)
  return text
}

/*
 * Path commands that continue from points[0] through the remaining points.
 * "monotone" uses Fritsch-Carlson monotone cubic interpolation, which never
 * overshoots the data; anything else draws straight segments.
 */
function continuePath(points, curve) {
  const commands = []

  if (curve !== "monotone" || points.length < 3) {
    for (let index = 1; index < points.length; index = index + 1) {
      commands.push(`L${formatCoordinate(points[index].x)},${formatCoordinate(points[index].y)}`)
    }
    return commands.join(" ")
  }

  const count = points.length
  const widths = []
  const slopes = []
  for (let index = 0; index < count - 1; index = index + 1) {
    const width = points[index + 1].x - points[index].x
    widths.push(width)
    slopes.push(width === 0 ? 0 : (points[index + 1].y - points[index].y) / width)
  }

  const tangents = [slopes[0]]
  for (let index = 1; index < count - 1; index = index + 1) {
    const sameDirection = slopes[index - 1] * slopes[index] > 0
    tangents.push(sameDirection === true ? (slopes[index - 1] + slopes[index]) / 2 : 0)
  }
  tangents.push(slopes[count - 2])

  for (let index = 0; index < count - 1; index = index + 1) {
    if (slopes[index] === 0) {
      tangents[index] = 0
      tangents[index + 1] = 0
    } else {
      const alpha = tangents[index] / slopes[index]
      const beta = tangents[index + 1] / slopes[index]
      const magnitude = alpha * alpha + beta * beta
      if (magnitude > 9) {
        const limit = 3 / Math.sqrt(magnitude)
        tangents[index] = limit * alpha * slopes[index]
        tangents[index + 1] = limit * beta * slopes[index]
      }
    }
  }

  for (let index = 0; index < count - 1; index = index + 1) {
    const from = points[index]
    const to = points[index + 1]
    const third = widths[index] / 3
    const control1 = `${formatCoordinate(from.x + third)},${formatCoordinate(from.y + tangents[index] * third)}`
    const control2 = `${formatCoordinate(to.x - third)},${formatCoordinate(to.y - tangents[index + 1] * third)}`
    commands.push(`C${control1} ${control2} ${formatCoordinate(to.x)},${formatCoordinate(to.y)}`)
  }

  return commands.join(" ")
}

export class MjSparkline extends MjElement {
  static tagName = "mj-sparkline";
  static styles = STYLES;
  static watched = ["values", "type", "width", "height", "show-end-dot",
    "reference-value", "curve", "label", "animated", "interactive", "locale"];

  constructor() {
    super()
    this._svgEl = null
    this._fallbackEl = null
  }

  render() {
    const markup = `
      <div class="container" part="container">
        <svg part="svg"></svg>
        <span class="fallback"><slot></slot></span>
      </div>
    `
    return markup
  }

  afterRender() {
    this._svgEl = this.$("svg")
    this._fallbackEl = this.$(".fallback")
    this._wireClicks()
    this._draw()
    return
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._svgEl === null || this._svgEl === undefined) { return }
    this._draw()
    return
  }

  _dimension(name, fallback) {
    const parsed = parseInt(this.getAttribute(name) || "", 10)
    const value = Number.isFinite(parsed) === true && parsed >= 0 ? parsed : fallback
    return value
  }

  _isInteractive() {
    const interactive = this.hasAttribute("interactive") === true && this.getAttribute("interactive") !== "false"
    return interactive
  }

  /*
   * Accessible wiring. With a `label` the SVG is the image and the default
   * slot text is hidden from assistive technology; without one the SVG is
   * hidden and the default slot text (visually hidden) is the alternative.
   * In interactive mode the SVG is a group so its button marks stay exposed.
   */
  _applyAccessibility() {
    const label = this.getAttribute("label") || ""
    const interactive = this._isInteractive()

    this._svgEl.classList.toggle("interactive", interactive)

    if (interactive === true) {
      this._svgEl.setAttribute("role", "group")
      this._svgEl.removeAttribute("aria-hidden")
    } else if (label.length > 0) {
      this._svgEl.setAttribute("role", "img")
      this._svgEl.removeAttribute("aria-hidden")
    } else {
      this._svgEl.setAttribute("aria-hidden", "true")
      this._svgEl.removeAttribute("role")
    }

    if (label.length > 0) {
      this._svgEl.setAttribute("aria-label", label)
      this._fallbackEl.setAttribute("aria-hidden", "true")
    } else {
      this._svgEl.removeAttribute("aria-label")
      this._fallbackEl.removeAttribute("aria-hidden")
    }
    return
  }

  _draw() {
    const width = this._dimension("width", 80)
    const height = this._dimension("height", 24)

    this._svgEl.setAttribute("viewBox", `0 0 ${width} ${height}`)
    this._svgEl.setAttribute("width", String(width))
    this._svgEl.setAttribute("height", String(height))
    this._applyAccessibility()

    const values = this.parsedValues
    const type = this.getAttribute("type") || "line"

    this._svgEl.textContent = ""

    const valid = values.filter((value) => Number.isNaN(value) === false)
    if (valid.length === 0) {
      const middle = height / 2
      this._svgEl.appendChild(createSvg("line", {
        x1: 0, y1: middle, x2: width, y2: middle, class: "line", part: "line"
      }))
      this.emit("mj-sparkline-render", { type: type, pointCount: 0 })
      return
    }

    const referenceValue = parseFloat(this.getAttribute("reference-value") || "")
    const hasReference = Number.isNaN(referenceValue) === false
    const baselineValue = hasReference === true ? referenceValue : 0

    /* Domain: the data, plus the reference value, plus (bars) the baseline. */
    let domainMin = Math.min(...valid)
    let domainMax = Math.max(...valid)
    if (hasReference === true || type === "bar") {
      domainMin = Math.min(domainMin, baselineValue)
      domainMax = Math.max(domainMax, baselineValue)
    }
    const range = domainMax - domainMin

    const plotTop = PLOT_PADDING
    const plotBottom = height - PLOT_PADDING
    const scaleY = (value) => {
      let y = height / 2
      if (range > 0) {
        y = plotTop + (plotBottom - plotTop) * (1 - (value - domainMin) / range)
      }
      return y
    }

    /* Zero (or the reference) when it is inside the domain, else the nearest plot edge. */
    let baselineY = scaleY(baselineValue)
    if (range === 0 && hasReference === false && type !== "bar") {
      baselineY = baselineValue <= domainMin ? plotBottom : plotTop
    }
    baselineY = Math.max(plotTop, Math.min(plotBottom, baselineY))

    const showEndDot = this.hasAttribute("show-end-dot") === true
    const dotRadius = parseFloat(getComputedStyle(this._svgEl).getPropertyValue("--mj-sparkline-end-dot-radius")) || 3

    /* Keep the line (and its end dot) inside the box horizontally. */
    const inset = showEndDot === true ? dotRadius : 1
    const scaleX = (index) => {
      const count = values.length
      const x = count > 1 ? inset + (index / (count - 1)) * (width - 2 * inset) : width / 2
      return x
    }

    if (type === "bar") {
      this._drawBars(values, width, scaleY, baselineY, baselineValue)
    } else if (type === "win-loss") {
      this._drawWinLoss(values, width, height)
    } else {
      this._drawLinePath(values, type === "area", scaleX, scaleY, baselineY)
    }

    if (hasReference === true) {
      const referenceY = formatCoordinate(scaleY(referenceValue))
      this._svgEl.appendChild(createSvg("line", {
        class: "reference-line", part: "reference-line",
        x1: 0, y1: referenceY, x2: width, y2: referenceY
      }))
    }

    if (showEndDot === true && type !== "bar" && type !== "win-loss") {
      const lastIndex = this._lastValidIndex(values)
      if (lastIndex >= 0) {
        const dot = createSvg("circle", {
          class: "end-dot mark", part: "end-dot",
          cx: formatCoordinate(scaleX(lastIndex)),
          cy: formatCoordinate(scaleY(values[lastIndex])),
          r: dotRadius,
          "data-idx": lastIndex
        })
        this._makeMarkAccessible(dot, lastIndex, values[lastIndex])
        this._svgEl.appendChild(dot)
      }
    }

    this._animateLine()

    this.emit("mj-sparkline-render", { type: type, pointCount: valid.length })
    return
  }

  _animateLine() {
    if (this.hasAttribute("animated") === false || this.getAttribute("animated") === "false") {
      return
    }
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches
    if (reduced === true) {
      return
    }

    const path = this._svgEl.querySelector("path.line")
    if (path !== null) {
      const length = typeof path.getTotalLength === "function" ? path.getTotalLength() : 300
      path.style.strokeDasharray = String(length)
      path.style.strokeDashoffset = String(length)
      path.style.transition = "stroke-dashoffset var(--mj-sparkline-transition, var(--mj-motion-medium)) var(--mj-motion-ease)"
      requestAnimationFrame(() => { path.style.strokeDashoffset = "0" })
    }
    return
  }

  _formatValue(value) {
    const locale = this.getAttribute("locale") || ""
    let formatted = String(value)
    try {
      formatted = new Intl.NumberFormat(locale.length > 0 ? locale : getLocale()).format(value)
    } catch (error) {
      formatted = new Intl.NumberFormat(getLocale()).format(value)
    }
    return formatted
  }

  /* In interactive mode a mark is a labelled button in the tab order. */
  _makeMarkAccessible(mark, index, value) {
    if (this._isInteractive() === true) {
      mark.setAttribute("role", "button")
      mark.setAttribute("tabindex", "0")
      mark.setAttribute("aria-label", t("mj.sparkline.pointLabel", { index: index + 1, value: this._formatValue(value) }))
    }
    return
  }

  _wireClicks() {
    const activate = (target) => {
      if (target === null || target === this._svgEl || typeof target.getAttribute !== "function") { return false }

      const index = parseInt(target.getAttribute("data-idx") || "", 10)
      if (Number.isNaN(index) === true) { return false }

      const values = this.parsedValues
      this.emit("mj-sparkline-click", { index: index, value: values[index] })
      return true
    }

    this.listen(this._svgEl, "click", (event) => {
      activate(event.target)
    })

    this.listen(this._svgEl, "keydown", (event) => {
      if (this._isInteractive() === false) { return }
      if (event.key !== "Enter" && event.key !== " ") { return }
      const handled = activate(event.target)
      if (handled === true) {
        event.preventDefault()
      }
    })
    return
  }

  /*
   * Runs of consecutive valid values. A NaN value ends the current run, so
   * no segment is drawn across a gap.
   */
  _segments(values, scaleX, scaleY) {
    const segments = []
    let current = []

    for (let index = 0; index < values.length; index = index + 1) {
      const value = values[index]
      if (Number.isNaN(value) === true) {
        if (current.length > 0) {
          segments.push(current)
          current = []
        }
      } else {
        current.push({ x: scaleX(index), y: scaleY(value), index: index })
      }
    }
    if (current.length > 0) {
      segments.push(current)
    }

    return segments
  }

  _drawLinePath(values, area, scaleX, scaleY, baselineY) {
    const curve = this.getAttribute("curve") || "linear"
    const segments = this._segments(values, scaleX, scaleY)
    const lineParts = []
    const areaParts = []
    const lonePoints = []

    for (let index = 0; index < segments.length; index = index + 1) {
      const points = segments[index]
      const first = points[0]
      const last = points[points.length - 1]

      if (points.length === 1) {
        /* A single point has no segment to stroke; it is drawn as a dot. */
        lonePoints.push(first)
        continue
      }

      const start = `${formatCoordinate(first.x)},${formatCoordinate(first.y)}`
      const rest = continuePath(points, curve)
      lineParts.push(`M${start} ${rest}`)

      if (area === true) {
        /* Each run is closed down to the baseline at its own first and last x. */
        const base = formatCoordinate(baselineY)
        areaParts.push(
          `M${formatCoordinate(first.x)},${base} L${start} ${rest} L${formatCoordinate(last.x)},${base} Z`
        )
      }
    }

    if (areaParts.length > 0) {
      this._svgEl.appendChild(createSvg("path", { class: "area", part: "area", d: areaParts.join(" ") }))
    }
    if (lineParts.length > 0) {
      this._svgEl.appendChild(createSvg("path", { class: "line", part: "line", d: lineParts.join(" ") }))
    }
    for (let index = 0; index < lonePoints.length; index = index + 1) {
      const point = lonePoints[index]
      this._svgEl.appendChild(createSvg("circle", {
        class: "point", part: "line",
        cx: formatCoordinate(point.x), cy: formatCoordinate(point.y), r: 2
      }))
    }
    return
  }

  /* Width of the gap between columns, from --mj-sparkline-bar-gap. */
  _barGap(bandWidth) {
    const declared = parseFloat(getComputedStyle(this._svgEl).getPropertyValue("--mj-sparkline-bar-gap"))
    const requested = Number.isNaN(declared) === true ? 1 : declared
    const gap = Math.max(0, Math.min(requested, bandWidth - 1))
    return gap
  }

  _drawBars(values, width, scaleY, baselineY, baselineValue) {
    const count = values.length
    const bandWidth = width / count
    const gap = this._barGap(bandWidth)

    for (let index = 0; index < count; index = index + 1) {
      const value = values[index]
      if (Number.isNaN(value) === true) { continue }

      /* A bar spans from its value to the baseline; a zero-length bar keeps one pixel. */
      const y = scaleY(value)
      const isPositive = value >= baselineValue
      const barHeight = Math.max(1, Math.abs(baselineY - y))
      const top = isPositive === true ? baselineY - barHeight : baselineY

      const bar = createSvg("rect", {
        class: `${isPositive === true ? "bar-pos" : "bar-neg"} mark`, part: "bar",
        x: formatCoordinate(index * bandWidth + gap / 2),
        y: formatCoordinate(top),
        width: formatCoordinate(Math.max(1, bandWidth - gap)),
        height: formatCoordinate(barHeight),
        rx: 1,
        "data-idx": index
      })
      this._makeMarkAccessible(bar, index, value)
      this._svgEl.appendChild(bar)
    }
    return
  }

  _drawWinLoss(values, width, height) {
    const count = values.length
    const bandWidth = width / count
    const gap = this._barGap(bandWidth)
    const columnHeight = Math.max(1, (height - 2 * PLOT_PADDING) / 2 - 1)
    const middle = height / 2

    for (let index = 0; index < count; index = index + 1) {
      const value = values[index]
      if (Number.isNaN(value) === true) { continue }

      /* Win above the axis, loss below it, and a draw as a neutral tick on it. */
      let className = "bar-zero"
      let y = middle - 1
      let markHeight = 2
      if (value > 0) {
        className = "bar-pos"
        y = middle - columnHeight - 1
        markHeight = columnHeight
      } else if (value < 0) {
        className = "bar-neg"
        y = middle + 1
        markHeight = columnHeight
      }

      const column = createSvg("rect", {
        class: `${className} mark`, part: "win-loss-col",
        x: formatCoordinate(index * bandWidth + gap / 2),
        y: formatCoordinate(y),
        width: formatCoordinate(Math.max(1, bandWidth - gap)),
        height: formatCoordinate(markHeight),
        rx: 1,
        "data-idx": index
      })
      this._makeMarkAccessible(column, index, value)
      this._svgEl.appendChild(column)
    }
    return
  }

  _lastValidIndex(values) {
    let found = -1
    for (let index = values.length - 1; index >= 0 && found < 0; index = index - 1) {
      if (Number.isNaN(values[index]) === false) {
        found = index
      }
    }
    return found
  }

  /* ----- scriptable API ----- */

  get parsedValues() {
    const raw = this.getAttribute("values") || ""
    if (raw.trim().length === 0) { return [] }
    const parts = raw.split(",")
    const numbers = parts.map((part) => parseFloat(part.trim()))
    return numbers
  }

  get min() {
    const valid = this.parsedValues.filter((value) => Number.isNaN(value) === false)
    if (valid.length === 0) { return 0 }
    return Math.min(...valid)
  }

  get max() {
    const valid = this.parsedValues.filter((value) => Number.isNaN(value) === false)
    if (valid.length === 0) { return 0 }
    return Math.max(...valid)
  }

  get last() {
    const valid = this.parsedValues.filter((value) => Number.isNaN(value) === false)
    if (valid.length === 0) { return NaN }
    return valid[valid.length - 1]
  }
}
