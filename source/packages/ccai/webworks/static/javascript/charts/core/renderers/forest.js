/*
 * forest.js
 *
 * Forest plot (blobbogram) renderer — meta-analysis / subgroup effect sizes.
 *
 * Registers: "forest"
 *
 * JSON shape (ctx.raw):
 *   series: [{
 *     name,
 *     groups: [{ category, value, error_low, error_high, weight? }]
 *   }]
 *   pooled?: { value, ci_lower, ci_upper, label }
 *
 *   value       — point estimate
 *   error_low   — positive half-width below value (CI lower = value - error_low)
 *   error_high  — positive half-width above value (CI upper = value + error_high)
 *   weight      — optional study weight, drives square marker size
 *   pooled      — optional pooled estimate drawn as a diamond
 * Numeric strings are accepted; a row without a numeric value is skipped.
 * Rows are drawn in data order, one per entry (repeated labels are fine).
 *
 * Options:
 *   scale="log"   log x-scale for ratio measures (odds / hazard / risk
 *                 ratios); the no-effect line defaults to 1. A CI bound at
 *                 or below zero cannot be shown on a log axis: its whisker
 *                 runs to the axis edge and ends in an arrow.
 *   null-value    x position of the no-effect reference line (default 0,
 *                 or 1 on a log scale)
 *
 * Orientation: horizontal only (effect on x, studies on y).
 *
 * Events:
 *   mj-chart-study-click  { series, category, value, ci_lower, ci_upper, weight }
 *   mj-chart-pooled-click { value, ci_lower, ci_upper, label }
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber } from "../svgdraw.js";
import { linearScale, logScale, bandScale, niceDomain, niceTicks, positiveExtent } from "../scales.js";


const LABEL_FONT = 11;
const VALUE_FONT = 10;
const CHAR_WIDTH = 0.56;
const POOLED_ROW = 28;


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
  if (value === null || value === undefined || value === "" || typeof value === "boolean") {
    return null
  }
  const numeric = Number(value)
  const result = Number.isFinite(numeric) === true ? numeric : null
  return result
}


function _estimateText(value, low, high) {
  /*
   * "0.82 [0.74, 0.90]" (two to three decimals, as forest plots are read)
   */
  const options = { minimumFractionDigits: 2, maximumFractionDigits: 3 }
  const text = `${formatNumber(value, options)} [${formatNumber(low, options)}, ${formatNumber(high, options)}]`
  return text
}


function _attachActivation(element, handler) {
  /*
   * Click and Enter / Space activation of a focusable mark.
   */
  element.addEventListener("click", handler)
  element.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault()
      handler()
    }
  })
  return
}


export function render(ctx) {
  /*
   * Render a forest plot.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const raw = ctx.raw !== null && ctx.raw !== undefined ? ctx.raw : {}
  const isLog = ctx.attrs("scale", "linear") === "log"

  const root = svgEl("g", { part: "plot" }, [])

  /* Rows in data order: every series' groups, one row each. */
  const series = Array.isArray(raw.series) === true
    ? raw.series.filter((entry) => entry !== null && typeof entry === "object") : []
  const rows = []
  for (let s = 0; s < series.length; s = s + 1) {
    const groups = Array.isArray(series[s].groups) === true ? series[s].groups : []
    const name = series[s].name !== undefined ? String(series[s].name) : `Series ${s + 1}`
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
      const weight = _number(group.weight)
      rows.push({
        series: name,
        source: group,
        category: group.category !== undefined && group.category !== null ? String(group.category) : "",
        value: value,
        low: value - (errorLow !== null ? Math.abs(errorLow) : 0),
        high: value + (errorHigh !== null ? Math.abs(errorHigh) : 0),
        weight: weight !== null && weight > 0 ? weight : null
      })
    }
  }

  let pooled = null
  if (raw.pooled !== null && typeof raw.pooled === "object" && _number(raw.pooled.value) !== null) {
    const value = _number(raw.pooled.value)
    const low = _number(raw.pooled.ci_lower)
    const high = _number(raw.pooled.ci_upper)
    pooled = {
      value: value,
      low: low !== null ? low : value,
      high: high !== null ? high : value,
      label: raw.pooled.label !== undefined && raw.pooled.label !== null && raw.pooled.label !== ""
        ? String(raw.pooled.label) : "Pooled"
    }
  }

  const tableRows = rows.map((row) => [row.category, row.series, row.value, row.low, row.high,
    row.weight !== null ? row.weight : ""])
  if (pooled !== null) {
    tableRows.push([pooled.label, "", pooled.value, pooled.low, pooled.high, ""])
  }
  ctx.setTable({ columns: ["Study", "Series", "Estimate", "CI lower", "CI upper", "Weight"], rows: tableRows })
  ctx.setLegend(series.length > 1
    ? series.map((entry, index) => ({ label: entry.name !== undefined ? String(entry.name) : `Series ${index + 1}`, series: entry.name }))
    : [])

  if (rows.length === 0 && pooled === null) {
    return root
  }

  /* No-effect value. */
  const nullAttr = _number(ctx.attrs("null-value", null))
  let nullValue = nullAttr !== null ? nullAttr : (isLog === true ? 1 : 0)
  if (isLog === true && nullValue <= 0) {
    nullValue = 1
  }

  /* x domain from every bound; a log axis keeps the positive ones. */
  const bounds = [nullValue]
  for (let r = 0; r < rows.length; r = r + 1) {
    bounds.push(rows[r].low, rows[r].high, rows[r].value)
  }
  if (pooled !== null) {
    bounds.push(pooled.low, pooled.high, pooled.value)
  }
  let xScale = null
  let xTicks = []
  if (isLog === true) {
    const positive = positiveExtent(bounds)
    let lo = positive[0]
    let hi = positive[1]
    if (lo === hi) {
      lo = lo / 2
      hi = hi * 2
    }
    /* A little room either side, in ratio terms. */
    lo = lo / 1.15
    hi = hi * 1.15
    xScale = logScale([lo, hi], [0, 1])
  } else {
    let lo = Infinity
    let hi = -Infinity
    for (let b = 0; b < bounds.length; b = b + 1) {
      lo = Math.min(lo, bounds[b])
      hi = Math.max(hi, bounds[b])
    }
    if (lo === hi) {
      lo = lo - 1
      hi = hi + 1
    }
    /* Pad the data ends, not the no-effect line when it is an end. */
    const pad = (hi - lo) * 0.05
    const padLo = lo === nullValue ? lo : lo - pad
    const padHi = hi === nullValue ? hi : hi + pad
    xScale = linearScale(niceDomain(padLo, padHi, 5), [0, 1])
  }

  /* Margins from the labels and the estimate column. */
  let longestLabel = 0
  let longestValue = 0
  for (let r = 0; r < rows.length; r = r + 1) {
    longestLabel = Math.max(longestLabel, _textWidth(rows[r].category, LABEL_FONT))
    longestValue = Math.max(longestValue, _textWidth(_estimateText(rows[r].value, rows[r].low, rows[r].high), VALUE_FONT))
  }
  if (pooled !== null) {
    longestLabel = Math.max(longestLabel, _textWidth(pooled.label, LABEL_FONT) * 1.08)
    longestValue = Math.max(longestValue, _textWidth(_estimateText(pooled.value, pooled.low, pooled.high), VALUE_FONT) * 1.1)
  }
  const left = Math.min(Math.max(longestLabel + 16, 48), Math.max(ctx.width * 0.3, 48))
  const right = Math.min(Math.max(longestValue + 16, 40), Math.max(ctx.width * 0.25, 40))
  const margin = { top: 12, right: right, bottom: 32, left: left }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  const domain = xScale.domain()
  xScale = isLog === true ? logScale(domain, [0, plotW]) : linearScale(domain, [0, plotW])
  const tickCount = Math.max(4, Math.floor(plotW / 80))
  xTicks = isLog === true ? xScale.ticks(tickCount) : niceTicks(domain[0], domain[1], tickCount)
  if (isLog === true && xTicks.length < 4) {
    /* A ratio axis spanning less than a decade reads better with even steps. */
    xTicks = niceTicks(domain[0], domain[1], Math.min(tickCount, 6)).filter((tick) => tick > 0)
  }
  const xMinPx = 0
  const xMaxPx = plotW
  const toPx = (value) => {
    /* A bound the axis cannot show lands on the edge (flagged by caller). */
    const pixel = isLog === true && value <= 0 ? xMinPx : xScale(value)
    return Math.min(Math.max(pixel, xMinPx), xMaxPx)
  }

  const pooledRows = pooled !== null ? 1 : 0
  const studyH = Math.max(plotH - pooledRows * POOLED_ROW, 10)
  const cat = bandScale(rows.map((row, index) => index), [0, studyH], 0.3)
  const bandwidth = cat.bandwidth()

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)
  const axis = svgEl("g", { "aria-hidden": "true" }, [])
  const labels = svgEl("g", { "aria-hidden": "true" }, [])
  const marks = svgEl("g", null, [])
  plot.appendChild(axis)
  plot.appendChild(marks)
  plot.appendChild(labels)

  for (let t = 0; t < xTicks.length; t = t + 1) {
    const x = xScale(xTicks[t])
    axis.appendChild(svgEl("line", {
      x1: x, y1: 0, x2: x, y2: plotH,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    axis.appendChild(svgEl("text", {
      x: x, y: plotH + 16, "text-anchor": "middle",
      "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
    }, formatNumber(xTicks[t])))
  }
  const xNull = xScale(nullValue)
  axis.appendChild(svgEl("line", {
    x1: xNull, y1: 0, x2: xNull, y2: plotH,
    stroke: "var(--mj-text-muted, #6b7280)", "stroke-width": 1.5
  }, []))

  /* Square size from weight; never inverted on short rows. */
  let wMin = Infinity
  let wMax = -Infinity
  for (let r = 0; r < rows.length; r = r + 1) {
    const weight = rows[r].weight !== null ? rows[r].weight : 1
    wMin = Math.min(wMin, weight)
    wMax = Math.max(wMax, weight)
  }
  const wRange = wMax > wMin ? wMax - wMin : 1
  const maxHalf = Math.max(Math.min(bandwidth / 2 - 1, 10), 1)
  const minHalf = Math.min(3, maxHalf)
  const weightToHalf = (weight) => {
    const fraction = (weight - wMin) / wRange
    const half = rows.length > 0 && wMax > wMin ? minHalf + fraction * (maxHalf - minHalf) : Math.min(5, maxHalf)
    return half
  }

  for (let r = 0; r < rows.length; r = r + 1) {
    const row = rows[r]
    const bandMid = cat.centerAt(r)
    const color = ctx.colorFor(row.series)
    const lowCut = isLog === true && row.low <= 0
    const xPt = toPx(row.value)
    const xLo = toPx(row.low)
    const xHi = toPx(row.high)
    const halfSquare = weightToHalf(row.weight !== null ? row.weight : 1)
    const estimate = _estimateText(row.value, row.low, row.high)
    const label = `${row.category}: ${estimate}` + (row.weight !== null ? `, weight ${formatNumber(row.weight)}` : "")

    const group = svgEl("g", { part: "study", tabindex: "0", role: "img", "aria-label": label }, [])
    group.appendChild(svgEl("title", null, label))
    group.appendChild(svgEl("line", {
      x1: xLo, y1: bandMid, x2: xHi, y2: bandMid, stroke: color, "stroke-width": 1.5
    }, []))
    if (lowCut === true) {
      /* The bound is off a log axis: an arrow at the edge, no cap. */
      group.appendChild(svgEl("polygon", {
        points: `${xLo},${bandMid} ${xLo + 7},${bandMid - 4} ${xLo + 7},${bandMid + 4}`, fill: color
      }, []))
    } else {
      group.appendChild(svgEl("line", {
        x1: xLo, y1: bandMid - 4, x2: xLo, y2: bandMid + 4, stroke: color, "stroke-width": 1.5
      }, []))
    }
    group.appendChild(svgEl("line", {
      x1: xHi, y1: bandMid - 4, x2: xHi, y2: bandMid + 4, stroke: color, "stroke-width": 1.5
    }, []))
    group.appendChild(svgEl("rect", {
      x: xPt - halfSquare, y: bandMid - halfSquare,
      width: halfSquare * 2, height: halfSquare * 2, fill: color
    }, []))
    const emitRow = row
    _attachActivation(group, () => {
      ctx.emit("mj-chart-study-click", {
        series: emitRow.series,
        category: emitRow.category,
        value: emitRow.value,
        ci_lower: emitRow.low,
        ci_upper: emitRow.high,
        weight: emitRow.source.weight
      })
    })
    marks.appendChild(group)

    if (bandwidth >= 7) {
      const font = Math.min(LABEL_FONT, Math.max(bandwidth, 7))
      labels.appendChild(svgEl("text", {
        x: -8, y: bandMid + font * 0.35, "text-anchor": "end",
        "font-size": font, fill: "var(--mj-text, #14181f)"
      }, _fitText(row.category, margin.left - 12, font)))
      labels.appendChild(svgEl("text", {
        x: plotW + 8, y: bandMid + 3.5, "text-anchor": "start",
        "font-size": VALUE_FONT, fill: "var(--mj-text-muted, #6b7280)"
      }, _fitText(estimate, margin.right - 10, VALUE_FONT)))
    }
  }

  if (pooled !== null) {
    const diamondY = plotH - POOLED_ROW / 2
    const xPt = toPx(pooled.value)
    const xLo = toPx(pooled.low)
    const xHi = toPx(pooled.high)
    const diamondH = 8
    const estimate = _estimateText(pooled.value, pooled.low, pooled.high)
    const pooledLabel = `${pooled.label}: ${estimate}`

    axis.appendChild(svgEl("line", {
      x1: -margin.left, y1: plotH - POOLED_ROW, x2: plotW + margin.right, y2: plotH - POOLED_ROW,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    const diamond = svgEl("polygon", {
      points: `${xPt},${diamondY - diamondH} ${xHi},${diamondY} ${xPt},${diamondY + diamondH} ${xLo},${diamondY}`,
      fill: "var(--mj-text, #14181f)",
      part: "pooled", tabindex: "0", role: "img", "aria-label": pooledLabel
    }, [])
    diamond.appendChild(svgEl("title", null, pooledLabel))
    _attachActivation(diamond, () => {
      ctx.emit("mj-chart-pooled-click", {
        value: pooled.value, ci_lower: pooled.low, ci_upper: pooled.high, label: pooled.label
      })
    })
    marks.appendChild(diamond)
    labels.appendChild(svgEl("text", {
      x: -8, y: diamondY + 4, "text-anchor": "end",
      "font-size": LABEL_FONT, fill: "var(--mj-text, #14181f)", "font-weight": "bold"
    }, _fitText(pooled.label, margin.left - 12, LABEL_FONT * 1.08)))
    labels.appendChild(svgEl("text", {
      x: plotW + 8, y: diamondY + 3.5, "text-anchor": "start", "font-weight": "bold",
      "font-size": VALUE_FONT, fill: "var(--mj-text, #14181f)"
    }, _fitText(estimate, margin.right - 8, VALUE_FONT * 1.08)))
  }

  axis.appendChild(svgEl("line", {
    x1: 0, y1: plotH, x2: plotW, y2: plotH,
    stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
  }, []))

  return root
}


registerRenderer("forest", render, { orientation: "horizontal" })
