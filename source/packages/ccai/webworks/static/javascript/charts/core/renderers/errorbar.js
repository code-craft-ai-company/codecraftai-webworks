/*
 * errorbar.js
 *
 * Error bar / confidence-interval renderer.
 *
 * Registers:
 *   "errorbar"            — categories on x (vertical by default), a dot (or
 *                           a bar from zero) at each value with whiskers.
 *   "confidence-interval" — horizontal by default; intervals only (dots, no
 *                           bars) and a reference line at the null value
 *                           (`null-value`, default 0), which is always shown.
 *
 * JSON shape (ctx.model.series[].groups):
 *   { category, value, error_low, error_high, bar? }
 *
 *   value       — central estimate
 *   error_low   — positive half-width below value
 *   error_high  — positive half-width above value
 *   bar         — (optional boolean, errorbar only) draw the value as a bar
 *                 from zero; the value axis then always includes zero
 * Numeric strings are accepted; a point without a numeric value is skipped
 * and a missing error counts as zero.
 *
 * Options:
 *   cap-width   width of the whisker end-caps in px (default 8)
 *   null-value  reference value (confidence-interval; default 0); on
 *               errorbar a reference line is drawn only when it is given
 *
 * Events:
 *   mj-chart-errorbar-click { series, category, value, low, high }
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber } from "../svgdraw.js";
import { linearScale, bandScale, niceDomain, niceTicks } from "../scales.js";


const LABEL_FONT = 11;
const CHAR_WIDTH = 0.56;


function _textWidth(text, fontSize) {
  /*
   * Approximate rendered width of a label.
   */
  const width = String(text).length * fontSize * CHAR_WIDTH
  return width
}


function _fitText(text, maxWidth, fontSize) {
  /*
   * Shorten a label with an ellipsis so it fits a width ("" if hopeless).
   */
  const value = String(text)
  let fitted = value
  if (_textWidth(value, fontSize) > maxWidth) {
    const maxChars = Math.floor(maxWidth / (fontSize * CHAR_WIDTH)) - 1
    fitted = maxChars >= 2 ? value.slice(0, maxChars) + "…" : ""
  }
  return fitted
}


function _number(value) {
  /*
   * A finite number from a number or numeric string, else null.
   */
  if (value === null || value === undefined || value === "") {
    return null
  }
  const numeric = Number(value)
  const result = Number.isFinite(numeric) === true ? numeric : null
  return result
}


function _readPoints(series, allowBars) {
  /*
   * Flatten the series groups into drawable points.
   *
   * :returns: { points: [{ series, seriesIndex, category, value, low, high,
   *     bar }], categories: [category, ...] in first-seen order }
   */
  const points = []
  const categories = []
  const seen = new Set()
  for (let s = 0; s < series.length; s = s + 1) {
    const groups = Array.isArray(series[s].groups) === true ? series[s].groups : []
    for (let g = 0; g < groups.length; g = g + 1) {
      const group = groups[g]
      if (group === null || typeof group !== "object") {
        continue
      }
      const value = _number(group.value)
      if (value === null) {
        continue
      }
      const errorLow = _number(group.error_low)
      const errorHigh = _number(group.error_high)
      const category = group.category !== undefined && group.category !== null
        ? String(group.category) : ""
      if (seen.has(category) === false) {
        seen.add(category)
        categories.push(category)
      }
      points.push({
        series: series[s].name,
        seriesIndex: s,
        category: category,
        value: value,
        low: value - (errorLow !== null ? Math.abs(errorLow) : 0),
        high: value + (errorHigh !== null ? Math.abs(errorHigh) : 0),
        bar: allowBars === true && group.bar === true
      })
    }
  }
  const result = { points: points, categories: categories }
  return result
}


export function render(ctx) {
  /*
   * Render an error-bar or confidence-interval chart.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const model = ctx.model
  const isInterval = ctx.type === "confidence-interval"
  const horizontal = ctx.orientation === "horizontal"
  const capValue = _number(ctx.attrs("cap-width", null))
  const capWidth = capValue !== null ? Math.max(capValue, 0) : 8
  const nullAttr = _number(ctx.attrs("null-value", null))
  const referenceValue = nullAttr !== null ? nullAttr : (isInterval === true ? 0 : null)

  const root = svgEl("g", { part: "plot" }, [])

  const series = (model !== null && model !== undefined && Array.isArray(model.series) === true)
    ? model.series
    : []
  const parsed = _readPoints(series, isInterval === false)
  const points = parsed.points
  const categories = parsed.categories

  ctx.setTable({
    columns: ["Category", "Series", "Value", "Lower", "Upper"],
    rows: points.map((point) => [point.category, point.series, point.value, point.low, point.high])
  })
  ctx.setLegend(series.map((entry) => ({ label: entry.name, series: entry.name })))

  if (points.length === 0) {
    return root
  }

  /* Value domain: every whisker, zero for bars, the reference value. */
  let valueMin = Infinity
  let valueMax = -Infinity
  let anyBar = false
  for (let p = 0; p < points.length; p = p + 1) {
    valueMin = Math.min(valueMin, points[p].low, points[p].value)
    valueMax = Math.max(valueMax, points[p].high, points[p].value)
    if (points[p].bar === true) {
      anyBar = true
    }
  }
  if (anyBar === true) {
    valueMin = Math.min(valueMin, 0)
    valueMax = Math.max(valueMax, 0)
  }
  if (referenceValue !== null) {
    valueMin = Math.min(valueMin, referenceValue)
    valueMax = Math.max(valueMax, referenceValue)
  }
  if (valueMin === valueMax) {
    valueMin = valueMin - 1
    valueMax = valueMax + 1
  }
  /*
   * Pad so the outermost caps do not sit on the plot edge; an end that is
   * zero under bars or the reference value itself is not padded.
   */
  const pad = (valueMax - valueMin) * 0.05
  const isAnchor = (value) => {
    const anchored = (anyBar === true && value === 0) || (referenceValue !== null && value === referenceValue)
    return anchored
  }
  const padMin = isAnchor(valueMin) === true ? valueMin : valueMin - pad
  const padMax = isAnchor(valueMax) === true ? valueMax : valueMax + pad
  const domain = niceDomain(padMin, padMax, 5)

  /* Margins from the labels. */
  let longestCategory = 0
  for (let c = 0; c < categories.length; c = c + 1) {
    longestCategory = Math.max(longestCategory, _textWidth(categories[c], LABEL_FONT))
  }
  const ticks = niceTicks(domain[0], domain[1], 5)
  let longestTick = 0
  for (let t = 0; t < ticks.length; t = t + 1) {
    longestTick = Math.max(longestTick, _textWidth(formatNumber(ticks[t]), LABEL_FONT))
  }
  const margin = horizontal === true
    ? { top: 12, right: 20, bottom: 32, left: Math.min(Math.max(longestCategory + 16, 48), Math.max(ctx.width * 0.35, 48)) }
    : { top: 16, right: 16, bottom: 32, left: Math.max(longestTick + 16, 40) }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  const cat = bandScale(categories, horizontal === true ? [0, plotH] : [0, plotW], 0.2)
  const val = horizontal === true
    ? linearScale(domain, [0, plotW])
    : linearScale(domain, [plotH, 0])

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)
  const axis = svgEl("g", { "aria-hidden": "true" }, [])
  const marks = svgEl("g", null, [])
  plot.appendChild(axis)
  plot.appendChild(marks)

  for (let t = 0; t < ticks.length; t = t + 1) {
    const position = val(ticks[t])
    if (horizontal === true) {
      axis.appendChild(svgEl("line", {
        x1: position, y1: 0, x2: position, y2: plotH,
        stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
      }, []))
      axis.appendChild(svgEl("text", {
        x: position, y: plotH + 16, "text-anchor": "middle",
        "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
      }, formatNumber(ticks[t])))
    } else {
      axis.appendChild(svgEl("line", {
        x1: 0, y1: position, x2: plotW, y2: position,
        stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
      }, []))
      axis.appendChild(svgEl("text", {
        x: -8, y: position + 4, "text-anchor": "end",
        "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
      }, formatNumber(ticks[t])))
    }
  }

  /* Reference line: the null value, else zero when it is in view. */
  const lineValue = referenceValue !== null
    ? referenceValue
    : (domain[0] <= 0 && domain[1] >= 0 ? 0 : null)
  if (lineValue !== null) {
    const position = val(lineValue)
    axis.appendChild(svgEl("line", horizontal === true
      ? { x1: position, y1: 0, x2: position, y2: plotH }
      : { x1: 0, y1: position, x2: plotW, y2: position }, []))
    axis.lastChild.setAttribute("stroke", "var(--mj-text-muted, #6b7280)")
    axis.lastChild.setAttribute("stroke-width", "1.5")
    if (referenceValue !== null) {
      axis.lastChild.setAttribute("stroke-dasharray", "5 3")
    }
  }

  /* Category labels, shortened to their band. */
  const bandwidth = cat.bandwidth()
  for (let c = 0; c < categories.length; c = c + 1) {
    const middle = cat.centerAt(c)
    if (horizontal === true) {
      axis.appendChild(svgEl("text", {
        x: -8, y: middle + 4, "text-anchor": "end",
        "font-size": LABEL_FONT, fill: "var(--mj-text, #14181f)"
      }, _fitText(categories[c], margin.left - 12, LABEL_FONT)))
    } else {
      axis.appendChild(svgEl("text", {
        x: middle, y: plotH + 18, "text-anchor": "middle",
        "font-size": LABEL_FONT, fill: "var(--mj-text, #14181f)"
      }, _fitText(categories[c], cat.step() - 4, LABEL_FONT)))
    }
  }

  const subWidth = bandwidth / Math.max(series.length, 1)
  const halfCap = Math.min(capWidth, subWidth) / 2
  const zeroPx = val(Math.min(Math.max(0, domain[0]), domain[1]))

  for (let p = 0; p < points.length; p = p + 1) {
    const point = points[p]
    const color = ctx.colorFor(point.series)
    const center = cat(point.category) + point.seriesIndex * subWidth + subWidth / 2
    const valuePx = val(point.value)
    const lowPx = val(point.low)
    const highPx = val(point.high)

    const label = `${point.series}, ${point.category}: ${formatNumber(point.value)} ` +
      `[${formatNumber(point.low)}, ${formatNumber(point.high)}]`
    const group = svgEl("g", {
      part: "errorbar", tabindex: "0", role: "img", "aria-label": label
    }, [])
    group.appendChild(svgEl("title", null, label))

    /* Coordinates in (along value, across category) order, then mapped. */
    const line = (v1, c1, v2, c2) => {
      const attrs = horizontal === true
        ? { x1: v1, y1: c1, x2: v2, y2: c2 }
        : { x1: c1, y1: v1, x2: c2, y2: v2 }
      attrs.stroke = color
      attrs["stroke-width"] = 1.5
      return svgEl("line", attrs, [])
    }

    if (point.bar === true) {
      const thickness = Math.max(subWidth - 2, 1)
      const start = Math.min(zeroPx, valuePx)
      const length = Math.abs(valuePx - zeroPx)
      group.appendChild(svgEl("rect", horizontal === true
        ? { x: start, y: center - thickness / 2, width: length, height: thickness }
        : { x: center - thickness / 2, y: start, width: thickness, height: length }, []))
      group.lastChild.setAttribute("rx", "2")
      group.lastChild.setAttribute("fill", color)
      group.lastChild.setAttribute("fill-opacity", "0.6")
    }
    group.appendChild(line(lowPx, center, highPx, center))
    if (halfCap > 0) {
      group.appendChild(line(lowPx, center - halfCap, lowPx, center + halfCap))
      group.appendChild(line(highPx, center - halfCap, highPx, center + halfCap))
    }
    if (point.bar === false) {
      group.appendChild(svgEl("circle", horizontal === true
        ? { cx: valuePx, cy: center, r: 4.5, fill: color }
        : { cx: center, cy: valuePx, r: 4.5, fill: color }, []))
    }

    const emitPoint = point
    const handler = () => {
      ctx.emit("mj-chart-errorbar-click", {
        series: emitPoint.series,
        category: emitPoint.category,
        value: emitPoint.value,
        low: emitPoint.low,
        high: emitPoint.high
      })
    }
    group.addEventListener("click", handler)
    group.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault()
        handler()
      }
    })
    marks.appendChild(group)
  }

  return root
}


registerRenderer("errorbar", render)
registerRenderer("confidence-interval", render, { orientation: "horizontal" })
