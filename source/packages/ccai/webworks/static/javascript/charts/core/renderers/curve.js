/*
 * curve.js
 *
 * Diagnostic-curve renderer — ROC, precision-recall, lift, and calibration.
 *
 * Registers: "roc", "precision-recall", "lift", "calibration"
 *
 * JSON shape (ctx.raw):
 *   series: [{ name, points: [{ x, y, n? }] }]
 *   baseline_prevalence?: number   (precision-recall no-skill line)
 *
 * Each type key sets the axes and a reference annotation:
 *   roc              — FPR vs TPR, chance diagonal; legend shows the AUC
 *   precision-recall — recall vs precision, horizontal line at
 *                      baseline_prevalence; legend shows the area (AP)
 *   lift             — population fraction vs lift, horizontal line at 1;
 *                      mode="gains" draws a cumulative-gains chart instead
 *                      (fraction of positives captured, chance diagonal)
 *   calibration      — predicted vs observed, perfect-calibration diagonal
 * Rates may be fractions (0-1) or percentages (0-100): an axis whose data
 * goes above 1 (and not above 100) is read as percent. Marks are clipped to
 * the plot.
 *
 * Options:
 *   shade-auc              fill the area under the curve (roc, precision-recall)
 *   size-by="n"            size calibration dots by bucket count n
 *   show-histogram         calibration: bars of n along the bottom
 *   markers="true|false"   point markers; by default shown when a series has
 *                          at most 50 points. Without visible markers each
 *                          point keeps an invisible ("quiet") mark that
 *                          shows on hover / focus, so the curve can still
 *                          be reached by keyboard and clicked
 *   mode="gains"           lift: cumulative gains
 *
 * Events:
 *   mj-chart-point-click { series, x, y, n }
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber, linePath, areaPath } from "../svgdraw.js";
import { linearScale, sqrtScale, niceDomain, niceTicks } from "../scales.js";
import { autoBooleanOption, booleanOption } from "../chartoptions.js";


/* Per-type axis and reference-line configuration. */
const TYPE_CONFIG = {
  "roc": {
    xLabel: "False positive rate",
    yLabel: "True positive rate",
    unitY: true,
    diagonal: true,
    horizontal: null,
    area: "AUC"
  },
  "precision-recall": {
    xLabel: "Recall",
    yLabel: "Precision",
    unitY: true,
    diagonal: false,
    horizontal: "baseline_prevalence",
    area: "AP"
  },
  "lift": {
    xLabel: "Population contacted",
    yLabel: "Lift",
    unitY: false,
    diagonal: false,
    horizontal: 1,
    area: null
  },
  "gains": {
    xLabel: "Population contacted",
    yLabel: "Positives captured",
    unitY: true,
    diagonal: true,
    horizontal: null,
    area: null
  },
  "calibration": {
    xLabel: "Mean predicted probability",
    yLabel: "Fraction of positives",
    unitY: true,
    diagonal: true,
    horizontal: null,
    area: null
  }
};

const AUTO_MARKER_LIMIT = 50;


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


function _unitDomain(min, max) {
  /*
   * The domain of a rate axis: [0, 1] for fractions, [0, 100] for
   * percentages, widened to the data when it leaves that range.
   */
  let top = 1
  if (max > 1 + 1e-9) {
    top = max <= 100 + 1e-9 ? 100 : max
  }
  const domain = niceDomain(Math.min(min, 0), top, 5)
  return domain
}


function _area(points) {
  /*
   * Trapezoid area under a curve in data units, x sorted ascending.
   */
  const sorted = points.slice().sort((a, b) => a.x - b.x)
  let area = 0
  for (let index = 1; index < sorted.length; index = index + 1) {
    area = area + (sorted[index].x - sorted[index - 1].x) * (sorted[index].y + sorted[index - 1].y) / 2
  }
  return area
}


export function render(ctx) {
  /*
   * Render a diagnostic curve chart.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const raw = ctx.raw !== null && ctx.raw !== undefined ? ctx.raw : {}
  let chartType = TYPE_CONFIG[ctx.type] !== undefined ? ctx.type : "roc"
  if (chartType === "lift" && ctx.attrs("mode", "") === "gains") {
    chartType = "gains"
  }
  const config = TYPE_CONFIG[chartType]
  const shadeAuc = booleanOption(ctx, "shade-auc", false) && config.area !== null
  const sizeByN = ctx.attrs("size-by", "") === "n" && chartType === "calibration"
  const showHistogram = booleanOption(ctx, "show-histogram", false) && chartType === "calibration"
  const markerOption = autoBooleanOption(ctx, "markers")

  const root = svgEl("g", { part: "plot" }, [])

  /* Parse the points: x and y numbers, n optional. */
  const series = []
  const rawSeries = Array.isArray(raw.series) === true ? raw.series : []
  for (let s = 0; s < rawSeries.length; s = s + 1) {
    const entry = rawSeries[s]
    if (entry === null || typeof entry !== "object") {
      continue
    }
    const source = Array.isArray(entry.points) === true ? entry.points : []
    const points = []
    for (let p = 0; p < source.length; p = p + 1) {
      const point = source[p]
      if (point === null || typeof point !== "object") {
        continue
      }
      const x = _number(point.x)
      const y = _number(point.y)
      if (x === null || y === null) {
        continue
      }
      points.push({ source: point, x: x, y: y, n: _number(point.n) })
    }
    series.push({ name: entry.name !== undefined ? String(entry.name) : `Series ${s + 1}`, points: points })
  }

  ctx.setTable({
    columns: ["Series", config.xLabel, config.yLabel, "n"],
    rows: [].concat(...series.map((entry) => entry.points.map((point) => [
      entry.name, point.x, point.y, point.n !== null ? point.n : ""
    ])))
  })

  /* Domains, by loop (no spread into Math.min / Math.max). */
  let xMin = Infinity
  let xMax = -Infinity
  let yMin = Infinity
  let yMax = -Infinity
  let nMin = Infinity
  let nMax = -Infinity
  let pointCount = 0
  for (let s = 0; s < series.length; s = s + 1) {
    for (let p = 0; p < series[s].points.length; p = p + 1) {
      const point = series[s].points[p]
      pointCount = pointCount + 1
      xMin = Math.min(xMin, point.x)
      xMax = Math.max(xMax, point.x)
      yMin = Math.min(yMin, point.y)
      yMax = Math.max(yMax, point.y)
      if (point.n !== null) {
        nMin = Math.min(nMin, point.n)
        nMax = Math.max(nMax, point.n)
      }
    }
  }
  if (pointCount === 0) {
    ctx.setLegend(series.map((entry) => ({ label: entry.name, series: entry.name })))
    root.appendChild(svgEl("text", {
      x: ctx.width / 2, y: ctx.height / 2, "text-anchor": "middle", "font-size": 12,
      fill: "var(--mj-text-muted, #6b7280)"
    }, "No points with numeric x and y"))
    return root
  }

  const xDomain = _unitDomain(xMin, xMax)
  const percentX = xDomain[1] > 1
  let yDomain = null
  if (config.unitY === true) {
    yDomain = _unitDomain(yMin, yMax)
  } else {
    /* Lift: from 0, so the lift = 1 baseline is always above the axis. */
    yDomain = niceDomain(Math.min(yMin, 0), Math.max(yMax, 1) * 1.05, 5)
  }
  const percentY = config.unitY === true && yDomain[1] > 1

  /* Legend with the area under each curve. */
  const scaleArea = (percentX === true ? 100 : 1) * (percentY === true ? 100 : 1)
  ctx.setLegend(series.map((entry) => {
    let label = entry.name
    if (config.area !== null && entry.points.length > 1) {
      label = `${entry.name} (${config.area} ${formatNumber(_area(entry.points) / scaleArea, { maximumFractionDigits: 3 })})`
    }
    return { label: label, series: entry.name }
  }))

  const margin = { top: 16, right: 16, bottom: 44, left: 56 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  const xScale = linearScale(xDomain, [0, plotW])
  const yScale = linearScale(yDomain, [plotH, 0])

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)
  const axis = svgEl("g", { "aria-hidden": "true" }, [])
  const clipId = "mj-curve-plot-clip"
  const clip = svgEl("clipPath", { id: clipId }, [
    svgEl("rect", { x: -6, y: -6, width: plotW + 12, height: plotH + 12 }, [])
  ])
  const drawing = svgEl("g", { "clip-path": `url(#${clipId})`, "aria-hidden": "true" }, [])
  const marks = svgEl("g", { "clip-path": `url(#${clipId})` }, [])
  plot.appendChild(clip)
  plot.appendChild(axis)
  plot.appendChild(drawing)
  plot.appendChild(marks)

  const xTickFormat = (value) => {
    const text = chartType === "lift" || chartType === "gains"
      ? (percentX === true ? `${formatNumber(value)}%` : formatNumber(value, { style: "percent" }))
      : formatNumber(value)
    return text
  }
  const yTickFormat = (value) => {
    const text = chartType === "gains"
      ? (percentY === true ? `${formatNumber(value)}%` : formatNumber(value, { style: "percent" }))
      : formatNumber(value)
    return text
  }

  const yTicks = niceTicks(yDomain[0], yDomain[1], 5)
  for (let t = 0; t < yTicks.length; t = t + 1) {
    const y = yScale(yTicks[t])
    axis.appendChild(svgEl("line", {
      x1: 0, y1: y, x2: plotW, y2: y,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    axis.appendChild(svgEl("text", {
      x: -8, y: y + 4, "text-anchor": "end",
      "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
    }, yTickFormat(yTicks[t])))
  }
  const xTicks = niceTicks(xDomain[0], xDomain[1], Math.max(4, Math.min(Math.floor(plotW / 70), 10)))
  for (let t = 0; t < xTicks.length; t = t + 1) {
    const x = xScale(xTicks[t])
    axis.appendChild(svgEl("line", {
      x1: x, y1: 0, x2: x, y2: plotH,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    axis.appendChild(svgEl("text", {
      x: x, y: plotH + 16, "text-anchor": "middle",
      "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
    }, xTickFormat(xTicks[t])))
  }
  axis.appendChild(svgEl("text", {
    x: plotW / 2, y: plotH + 34, "text-anchor": "middle",
    "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
  }, config.xLabel))
  axis.appendChild(svgEl("text", {
    transform: `translate(-40,${plotH / 2}) rotate(-90)`,
    "text-anchor": "middle",
    "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
  }, config.yLabel))

  /* Reference: the y = x diagonal (both axes in the same unit) or a line. */
  if (config.diagonal === true) {
    const xFactor = percentX === true ? 100 : 1
    const yFactor = percentY === true ? 100 : 1
    const start = Math.max(xDomain[0] / xFactor, yDomain[0] / yFactor, 0)
    const end = Math.min(xDomain[1] / xFactor, yDomain[1] / yFactor)
    drawing.appendChild(svgEl("line", {
      x1: xScale(start * xFactor), y1: yScale(start * yFactor),
      x2: xScale(end * xFactor), y2: yScale(end * yFactor),
      stroke: "var(--mj-text-muted, #6b7280)", "stroke-width": 1.5, "stroke-dasharray": "4 3"
    }, []))
  }
  let reference = null
  if (typeof config.horizontal === "number") {
    reference = config.horizontal
  } else if (typeof config.horizontal === "string") {
    reference = _number(raw[config.horizontal])
    if (reference !== null && percentY === true && reference <= 1) {
      reference = reference * 100
    }
  }
  if (reference !== null) {
    const yRef = yScale(reference)
    drawing.appendChild(svgEl("line", {
      x1: 0, y1: yRef, x2: plotW, y2: yRef,
      stroke: "var(--mj-text-muted, #6b7280)", "stroke-width": 1.5, "stroke-dasharray": "4 3"
    }, []))
  }

  /* Calibration extras: dot size and the count histogram. */
  const hasN = nMax > -Infinity
  const nScale = sqrtScale([hasN === true ? Math.min(nMin, 0) : 0, hasN === true ? Math.max(nMax, 1) : 1], [3, 12])

  for (let s = 0; s < series.length; s = s + 1) {
    const entry = series[s]
    const color = ctx.colorFor(entry.name)
    if (entry.points.length === 0) {
      continue
    }
    const ordered = chartType === "precision-recall" || chartType === "calibration"
      ? entry.points.slice().sort((a, b) => a.x - b.x)
      : entry.points
    const pathPts = ordered.map((point) => ({ x: xScale(point.x), y: yScale(point.y) }))

    if (showHistogram === true && hasN === true) {
      const barW = Math.max(plotW / Math.max(entry.points.length, 1) * 0.5, 2)
      const maxBar = plotH * 0.2
      for (let p = 0; p < ordered.length; p = p + 1) {
        if (ordered[p].n === null) {
          continue
        }
        const height = maxBar * ordered[p].n / Math.max(nMax, 1)
        drawing.appendChild(svgEl("rect", {
          x: xScale(ordered[p].x) - barW / 2, y: plotH - height, width: barW, height: height,
          fill: color, "fill-opacity": 0.25
        }, []))
      }
    }

    if (shadeAuc === true) {
      const areaD = areaPath(pathPts, yScale(Math.max(yDomain[0], 0)))
      if (areaD !== "") {
        drawing.appendChild(svgEl("path", { d: areaD, fill: color, "fill-opacity": 0.15 }, []))
      }
    }

    const pathD = linePath(pathPts)
    if (pathD !== "") {
      drawing.appendChild(svgEl("path", {
        d: pathD, fill: "none", stroke: color, "stroke-width": 2
      }, []))
    }

    /*
     * Visible markers, or (markers off / too many points) quiet marks: the
     * same focusable, clickable circles drawn transparent until hovered or
     * focused, so every point stays reachable.
     */
    const showMarkers = markerOption === true ||
      (markerOption === "auto" && entry.points.length <= AUTO_MARKER_LIMIT)
    for (let p = 0; p < ordered.length; p = p + 1) {
      const point = ordered[p]
      const radius = sizeByN === true && point.n !== null ? nScale(point.n) : 3.5
      const label = `${entry.name}: ${config.xLabel} ${formatNumber(point.x)}, ` +
        `${config.yLabel} ${formatNumber(point.y)}` + (point.n !== null ? `, n = ${formatNumber(point.n)}` : "")
      let opacity = sizeByN === true ? 0.7 : 1
      if (showMarkers === false) {
        opacity = 0
      }
      const circle = svgEl("circle", {
        cx: pathPts[p].x, cy: pathPts[p].y, r: radius,
        fill: color, "fill-opacity": opacity,
        part: "point", tabindex: "0", role: "img", "aria-label": label
      }, [])
      if (showMarkers === false) {
        circle.setAttribute("data-quiet-mark", "")
      }
      circle.appendChild(svgEl("title", null, label))

      const emitPoint = point
      const handler = () => {
        ctx.emit("mj-chart-point-click", {
          series: entry.name, x: emitPoint.x, y: emitPoint.y, n: emitPoint.n
        })
      }
      circle.addEventListener("click", handler)
      circle.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault()
          handler()
        }
      })
      marks.appendChild(circle)
    }
  }

  axis.appendChild(svgEl("line", {
    x1: 0, y1: plotH, x2: plotW, y2: plotH,
    stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
  }, []))
  axis.appendChild(svgEl("line", {
    x1: 0, y1: 0, x2: 0, y2: plotH,
    stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
  }, []))

  return root
}


registerRenderer("roc", render)
registerRenderer("precision-recall", render)
registerRenderer("lift", render)
registerRenderer("calibration", render)
