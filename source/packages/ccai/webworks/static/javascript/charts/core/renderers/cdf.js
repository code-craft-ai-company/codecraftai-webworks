/*
 * cdf.js
 *
 * Cumulative distribution function (ECDF / CDF) renderer.
 *
 * Registers: "cdf"
 *
 * ctx.model.series data shapes:
 *   Raw samples (renderer computes the empirical CDF; non-finite samples
 *   are missing data):
 *     series[]: { name, samples: [n, …] }
 *   Pre-computed:
 *     series[]: { name, points: [{x, y}, …] }  y is the cumulative share,
 *     either in [0, 1] or in percent [0, 100]
 *
 * The ECDF is a right-continuous step function built in data space: 0 left
 * of the smallest sample, a riser of k / n at every distinct value (k tied
 * samples), and 1 to the right edge of the axis. It is then mapped to the
 * oriented axes, so a horizontal chart (cumulative share on x) shows the
 * same function.
 *
 * Relevant ctx.attrs:
 *   direction   "ascending" (default) | "descending" (survival, 1 − F)
 *   scale       "probability" (default 0–1) | "percent" (0–100)
 *   smooth      boolean — a monotone curve through the step corners
 *   markers     "auto" (default: shown when a series has at most 60
 *               distinct values) | "true" | "false"
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber, linePath, monotonePath } from "../svgdraw.js";
import { linearScale } from "../scales.js";
import {
  sortNumbers, isFiniteNumber, hasSeriesSamples, axisLayer, drawTicks, drawAxisTitle, drawBaseline,
  tickCount, activateOnKey, focusableMark, fitDomain
} from "./diststats.js";
import { autoBooleanOption, booleanOption } from "../chartoptions.js";

const AUTO_MARKER_LIMIT = 60;


/* ── data preparation ────────────────────────────────────────────────────── */

export function empiricalSteps(samples) {
  /*
   * The distinct values of a sample with their cumulative share.
   *
   * :returns: [{ value, share, count }] ascending; `share` = P(X <= value),
   *     `count` = number of samples equal to value.
   */
  const sorted = sortNumbers(samples)
  const n = sorted.length
  const steps = []
  for (let index = 0; index < n; index = index + 1) {
    const value = sorted[index]
    if (steps.length > 0 && steps[steps.length - 1].value === value) {
      const last = steps[steps.length - 1]
      last.count = last.count + 1
      last.share = (index + 1) / n
    } else {
      steps.push({ value: value, share: (index + 1) / n, count: 1 })
    }
  }
  return steps
}


function _pointSteps(points) {
  /*
   * Pre-computed points as steps: finite x / y only, sorted by x, y read
   * as a share (values above 1 are taken as percent).
   */
  const usable = []
  let maxShare = 0
  for (let index = 0; index < points.length; index = index + 1) {
    const point = points[index]
    if (point === null || typeof point !== "object" ||
        isFiniteNumber(point.x) === false || isFiniteNumber(point.y) === false) {
      continue
    }
    usable.push({ value: point.x, share: point.y, count: null })
    maxShare = Math.max(maxShare, point.y)
  }
  const divisor = maxShare > 1 ? 100 : 1
  for (let index = 0; index < usable.length; index = index + 1) {
    usable[index].share = Math.max(0, Math.min(1, usable[index].share / divisor))
  }
  usable.sort((a, b) => a.value - b.value)
  return usable
}


/* ── main render ─────────────────────────────────────────────────────────── */

export function render(ctx) {
  /*
   * Render a cumulative distribution chart.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const model = ctx.model
  const horizontal = ctx.orientation === "horizontal"
  const descending = ctx.attrs("direction", "ascending") === "descending"
  const percent = ctx.attrs("scale", "probability") === "percent"
  const smooth = booleanOption(ctx, "smooth", false)
  const markersAttr = autoBooleanOption(ctx, "markers")

  const scaleMax = percent === true ? 100 : 1
  const shareTitle = descending === true
    ? (percent === true ? "Share above (%)" : "Share above")
    : (percent === true ? "Cumulative %" : "Cumulative probability")
  const shareFormat = (value) => percent === true
    ? `${formatNumber(value, { maximumFractionDigits: 1 })}%`
    : formatNumber(value, { maximumFractionDigits: 3 })

  const root = svgEl("g", { part: "plot" }, [])
  const series = Array.isArray(model.series) === true ? model.series : []
  const resolved = []
  let valMin = Infinity
  let valMax = -Infinity
  for (let si = 0; si < series.length; si = si + 1) {
    const entry = series[si]
    let steps = []
    let fromSamples = false
    if (Array.isArray(entry.samples) === true && entry.samples.length > 0) {
      steps = empiricalSteps(entry.samples)
      fromSamples = true
    }
    if (steps.length === 0 && Array.isArray(entry.points) === true) {
      steps = _pointSteps(entry.points)
      fromSamples = false
    }
    if (steps.length === 0) {
      continue
    }
    valMin = Math.min(valMin, steps[0].value)
    valMax = Math.max(valMax, steps[steps.length - 1].value)
    resolved.push({ name: entry.name, steps: steps, fromSamples: fromSamples })
  }
  if (resolved.length === 0) {
    return root
  }

  const margin = { top: 16, right: 20, bottom: 50, left: 64 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)
  const valueLength = horizontal === true ? plotH : plotW
  const valueCount = tickCount(valueLength, horizontal === true ? 40 : 70)
  const pad = (valMax - valMin) * 0.05
  const valueDomain = fitDomain(valMin - pad, valMax + pad, valueCount)

  /* value scale and share scale, oriented. */
  const valScale = horizontal === true
    ? linearScale(valueDomain, [plotH, 0])
    : linearScale(valueDomain, [0, plotW])
  const shareScale = horizontal === true
    ? linearScale([0, scaleMax], [0, plotW])
    : linearScale([0, scaleMax], [plotH, 0])
  const toPixel = (value, share) => {
    const shown = (descending === true ? 1 - share : share) * scaleMax
    if (horizontal === true) {
      return { x: shareScale(shown), y: valScale(value) }
    }
    return { x: valScale(value), y: shareScale(shown) }
  }

  const plot = svgEl("g", { transform: `translate(${margin.left},${margin.top})` }, [])
  root.appendChild(plot)
  const axes = axisLayer(plot)
  if (horizontal === true) {
    drawTicks(axes, shareScale, { side: "bottom", extent: plotH, count: 5, format: shareFormat })
    drawTicks(axes, valScale, { side: "left", extent: plotW, count: valueCount })
    drawAxisTitle(axes, shareTitle, "bottom", plotW, plotH, 38)
    drawAxisTitle(axes, "Value", "left", plotW, plotH, 50)
  } else {
    drawTicks(axes, valScale, { side: "bottom", extent: plotH, count: valueCount })
    drawTicks(axes, shareScale, { side: "left", extent: plotW, count: 5, format: shareFormat })
    drawAxisTitle(axes, "Value", "bottom", plotW, plotH, 38)
    drawAxisTitle(axes, shareTitle, "left", plotW, plotH, 50)
  }
  drawBaseline(axes, 0, plotH, plotW, plotH)
  drawBaseline(axes, 0, 0, 0, plotH)

  const marks = svgEl("g", { part: "marks" }, [])
  plot.appendChild(marks)
  const rows = []

  for (let ri = 0; ri < resolved.length; ri = ri + 1) {
    const entry = resolved[ri]
    const color = ctx.colorFor(entry.name)
    const steps = entry.steps
    const group = svgEl("g", { part: "series" }, [])

    /* Corners of the step function in data space, edge to edge. */
    let data = ""
    if (smooth === true) {
      const corners = steps.map((step) => toPixel(step.value, step.share))
      data = monotonePath(corners)
    } else {
      const corners = []
      const startShare = entry.fromSamples === true ? 0 : steps[0].share
      corners.push(toPixel(valueDomain[0], startShare))
      let previous = startShare
      for (let si = 0; si < steps.length; si = si + 1) {
        corners.push(toPixel(steps[si].value, previous))
        corners.push(toPixel(steps[si].value, steps[si].share))
        previous = steps[si].share
      }
      corners.push(toPixel(valueDomain[1], previous))
      data = linePath(corners)
    }

    const showMarkers = markersAttr === true ||
      (markersAttr === "auto" && steps.length <= AUTO_MARKER_LIMIT)
    const line = svgEl("path", {
      d: data, fill: "none", stroke: color, "stroke-width": 2, "stroke-linejoin": "round"
    }, [])
    line.setAttribute("part", "cdf-line")
    const median = steps.find((step) => step.share >= 0.5)
    if (showMarkers === false) {
      focusableMark(line, `${entry.name} cumulative distribution, ${steps.length} distinct values, ` +
        `median ${formatNumber(median !== undefined ? median.value : steps[0].value)}`)
      activateOnKey(line, () => {
        ctx.emit("mj-chart-cdf-click", { series: entry.name })
      })
    }
    group.appendChild(line)

    for (let si = 0; si < steps.length; si = si + 1) {
      const step = steps[si]
      const shown = (descending === true ? 1 - step.share : step.share) * scaleMax
      rows.push([entry.name, step.value, shown])
      if (showMarkers === false) {
        continue
      }
      const point = toPixel(step.value, step.share)
      const dot = svgEl("circle", { cx: point.x, cy: point.y, r: 3, fill: color, "fill-opacity": 0.8 }, [])
      dot.setAttribute("part", "cdf-point")
      const tied = step.count !== null && step.count > 1 ? ` (${step.count} tied)` : ""
      focusableMark(dot, `${entry.name}: value ${formatNumber(step.value)}${tied}, ` +
        `${descending === true ? "share above" : "cumulative"} ${shareFormat(shown)}`)
      const handlerStep = step
      activateOnKey(dot, () => {
        ctx.emit("mj-chart-cdf-point-click", {
          series: entry.name, x: handlerStep.value, y: shown
        })
      })
      group.appendChild(dot)
    }
    marks.appendChild(group)
  }

  ctx.setTable({
    columns: ["Series", "Value", descending === true ? shareTitle : "Cumulative"],
    rows: rows,
    caption: "Cumulative share at each distinct value"
  })
  return root
}


function _hasData(model) {
  /*
   * True when a series has a finite sample or a finite pre-computed point.
   */
  if (hasSeriesSamples(model) === true) {
    return true
  }
  const series = Array.isArray(model.allSeries) === true ? model.allSeries : []
  for (let si = 0; si < series.length; si = si + 1) {
    if (_pointSteps(Array.isArray(series[si].points) === true ? series[si].points : []).length > 0) {
      return true
    }
  }
  return false
}


registerRenderer("cdf", render, { isEmpty: (model) => _hasData(model) === false })
