/*
 * hexbin.js
 *
 * Hexagonal-binning renderer.
 *
 * Registered chart types:
 *   "hexbin" — aggregates dense scatter points into hexagonal bins
 *
 * Data shape:
 *   series[].points: [{ x, y, value? }, ...]   points of every series are
 *                                              merged; non-finite x / y skipped
 *   hexbin.radius   hexagon circumradius in px (default 20)
 *   hexbin.bins     alternatively, the number of hexagon columns across the
 *                   plot: the grid then scales with the chart, so a resize
 *                   does not regroup the points
 *   hexbin.stat     "count" (default) | "sum" | "mean" of `value`
 *   meta.xLabel / meta.yLabel   axis titles
 *
 * Attributes (an attribute wins over the matching data option, like every
 * other renderer option):
 *   radius        hexagon circumradius in px; overrides hexbin.radius and
 *                 hexbin.bins
 *   stat          "count" | "sum" | "mean"; overrides hexbin.stat
 *   encoding      "color" (default) | "size"
 *   show-labels   boolean -- print the statistic inside each hexagon
 *
 * Encoding:
 *   Default: fill colour on a sequential ramp that starts at zero (counts)
 *   so even a single-point bin is clearly visible; a colour bar on the
 *   right reads it back. encoding="size": hexagon AREA is proportional to
 *   the statistic, drawn over a faint full-size cell.
 *
 * Hexagons are flat-topped, in axial coordinates (q, r), each point going
 * to its nearest centre by cube rounding. Labels and events report the
 * bin centre in DATA units.
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber } from "../svgdraw.js";
import { linearScale } from "../scales.js";
import {
  isFiniteNumber, axisLayer, drawTicks, drawAxisTitle, drawBaseline, tickCount, sequentialColor,
  drawColorRamp, activateOnKey, focusableMark, TEXT_COLOR, SURFACE_COLOR
} from "./diststats.js";
import { booleanOption } from "../chartoptions.js";

const DEFAULT_RADIUS = 20;
const MIN_RADIUS = 4;
const RAMP_ROOM = 64;
const STATS = ["count", "sum", "mean"];


function _statName(ctx, rawHex) {
  /*
   * The bin statistic: the `stat` attribute, else hexbin.stat, else count.
   */
  let stat = "count"
  const fromAttr = String(ctx.attrs("stat", "")).trim().toLowerCase()
  if (STATS.indexOf(fromAttr) >= 0) {
    stat = fromAttr
  } else if (STATS.indexOf(rawHex.stat) >= 0) {
    stat = rawHex.stat
  }
  return stat
}


function _binRadius(ctx, rawHex, plotW) {
  /*
   * The hexagon circumradius in px: the `radius` attribute, else
   * hexbin.bins columns across the plot, else hexbin.radius, else the
   * default; never below MIN_RADIUS.
   */
  let radius = DEFAULT_RADIUS
  const attrRadius = parseFloat(ctx.attrs("radius", ""))
  const columns = Number(rawHex.bins)
  const dataRadius = Number(rawHex.radius)
  if (isFiniteNumber(attrRadius) === true && attrRadius > 0) {
    radius = attrRadius
  } else if (isFiniteNumber(columns) === true && columns >= 1) {
    radius = plotW / (columns * 1.5)
  } else if (isFiniteNumber(dataRadius) === true && dataRadius > 0) {
    radius = dataRadius
  }
  radius = Math.max(radius, MIN_RADIUS)
  return radius
}


function _hexPoints(cx, cy, r) {
  /*
   * The six corners of a flat-topped regular hexagon.
   */
  const points = []
  for (let index = 0; index < 6; index = index + 1) {
    const angle = (Math.PI / 3) * index
    points.push(`${(cx + r * Math.cos(angle)).toFixed(2)},${(cy + r * Math.sin(angle)).toFixed(2)}`)
  }
  return points.join(" ")
}


function _hexBin(points, xScale, yScale, radius) {
  /*
   * Group points by flat-topped hexagon (axial coordinates, cube rounding).
   *
   * :returns: Map "q,r" -> { cx, cy, pts } with the centre in plot pixels.
   */
  const bins = new Map()
  for (let index = 0; index < points.length; index = index + 1) {
    const point = points[index]
    const px = xScale(point.x)
    const py = yScale(point.y)
    const q = (2 / 3) * px / radius
    const r = ((-1 / 3) * px + (Math.sqrt(3) / 3) * py) / radius
    const s = -q - r
    let rq = Math.round(q)
    let rr = Math.round(r)
    const rs = Math.round(s)
    const dq = Math.abs(rq - q)
    const dr = Math.abs(rr - r)
    const ds = Math.abs(rs - s)
    if (dq > dr && dq > ds) {
      rq = -rr - rs
    } else if (dr > ds) {
      rr = -rq - rs
    }
    const key = `${rq},${rr}`
    if (bins.has(key) === false) {
      bins.set(key, {
        cx: radius * 1.5 * rq,
        cy: radius * (Math.sqrt(3) * rr + (Math.sqrt(3) / 2) * rq),
        pts: []
      })
    }
    bins.get(key).pts.push(point)
  }
  return bins
}


function _aggregate(points, stat) {
  /*
   * The bin statistic: count, or sum / mean of the finite `value`s.
   */
  if (stat !== "sum" && stat !== "mean") {
    return points.length
  }
  let total = 0
  let count = 0
  for (let index = 0; index < points.length; index = index + 1) {
    if (isFiniteNumber(points[index].value) === true) {
      total = total + points[index].value
      count = count + 1
    }
  }
  if (stat === "sum") {
    return total
  }
  return count > 0 ? total / count : null
}


export function render(ctx) {
  /*
   * Render a hexbin chart.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const model = ctx.model
  const rawHex = ctx.raw !== null && ctx.raw !== undefined && ctx.raw.hexbin !== null &&
    typeof ctx.raw.hexbin === "object" ? ctx.raw.hexbin : {}
  const statName = _statName(ctx, rawHex)
  const encoding = ctx.attrs("encoding", "color") === "size" ? "size" : "color"
  const showLabels = booleanOption(ctx, "show-labels", false)

  const root = svgEl("g", { part: "plot" }, [])
  const series = Array.isArray(model.series) === true ? model.series : []
  const points = []
  for (let si = 0; si < series.length; si = si + 1) {
    const list = Array.isArray(series[si].points) === true ? series[si].points : []
    for (let pi = 0; pi < list.length; pi = pi + 1) {
      const point = list[pi]
      if (point !== null && typeof point === "object" &&
          isFiniteNumber(point.x) === true && isFiniteNumber(point.y) === true) {
        points.push(point)
      }
    }
  }
  if (points.length === 0) {
    return root
  }

  const meta = model.meta !== null && model.meta !== undefined ? model.meta : {}
  const xTitle = typeof meta.xLabel === "string" ? meta.xLabel : ""
  const yTitle = typeof meta.yLabel === "string" ? meta.yLabel : ""
  const margin = {
    top: 16, right: encoding === "color" ? RAMP_ROOM : 16,
    bottom: xTitle.length > 0 ? 50 : 36,
    left: yTitle.length > 0 ? 70 : 56
  }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)
  const radius = _binRadius(ctx, rawHex, plotW)

  let xLow = Infinity
  let xHigh = -Infinity
  let yLow = Infinity
  let yHigh = -Infinity
  for (let pi = 0; pi < points.length; pi = pi + 1) {
    xLow = Math.min(xLow, points[pi].x)
    xHigh = Math.max(xHigh, points[pi].x)
    yLow = Math.min(yLow, points[pi].y)
    yHigh = Math.max(yHigh, points[pi].y)
  }
  const xPad = (xHigh - xLow) * 0.05 || Math.max(Math.abs(xLow) * 0.1, 1)
  const yPad = (yHigh - yLow) * 0.05 || Math.max(Math.abs(yLow) * 0.1, 1)
  const xScale = linearScale([xLow - xPad, xHigh + xPad], [0, plotW])
  const yScale = linearScale([yLow - yPad, yHigh + yPad], [plotH, 0])

  const plot = svgEl("g", { transform: `translate(${margin.left},${margin.top})` }, [])
  root.appendChild(plot)
  const axes = axisLayer(plot)
  drawTicks(axes, xScale, { side: "bottom", extent: plotH, count: tickCount(plotW, 70) })
  drawTicks(axes, yScale, { side: "left", extent: plotW, count: tickCount(plotH, 40) })
  drawAxisTitle(axes, xTitle, "bottom", plotW, plotH, 38)
  drawAxisTitle(axes, yTitle, "left", plotW, plotH, 54)

  /* Clip hexagons to the plot area. */
  const clipId = `hexbin-clip-${Math.random().toString(36).slice(2, 10)}`
  const defs = svgEl("defs", null, [])
  const clip = svgEl("clipPath", { id: clipId }, [])
  clip.appendChild(svgEl("rect", { x: 0, y: 0, width: plotW, height: plotH }, []))
  defs.appendChild(clip)
  plot.appendChild(defs)
  const marks = svgEl("g", { part: "marks", "clip-path": `url(#${clipId})` }, [])
  plot.appendChild(marks)

  const bins = []
  _hexBin(points, xScale, yScale, radius).forEach((bin) => {
    const value = _aggregate(bin.pts, statName)
    if (value !== null) {
      bins.push({ cx: bin.cx, cy: bin.cy, value: value, count: bin.pts.length })
    }
  })
  let statLow = Infinity
  let statHigh = -Infinity
  for (let bi = 0; bi < bins.length; bi = bi + 1) {
    statLow = Math.min(statLow, bins[bi].value)
    statHigh = Math.max(statHigh, bins[bi].value)
  }
  /* Ramps start at zero for non-negative statistics. */
  const rampLow = statLow >= 0 ? 0 : statLow
  const rampHigh = statHigh > rampLow ? statHigh : rampLow + 1
  const fractionOf = (value) => (value - rampLow) / (rampHigh - rampLow)
  const xStep = (xScale.domain()[1] - xScale.domain()[0]) / plotW
  const yStep = (yScale.domain()[1] - yScale.domain()[0]) / plotH
  const rows = []

  for (let bi = 0; bi < bins.length; bi = bi + 1) {
    const bin = bins[bi]
    const fraction = Math.max(0, Math.min(1, fractionOf(bin.value)))
    const dataX = xScale.invert(bin.cx)
    const dataY = yScale.invert(bin.cy)
    let drawRadius = radius
    let fill = sequentialColor(fraction)
    if (encoding === "size") {
      marks.appendChild(svgEl("polygon", {
        points: _hexPoints(bin.cx, bin.cy, radius), fill: sequentialColor(0),
        "fill-opacity": 0.35, stroke: SURFACE_COLOR, "stroke-width": 0.5
      }, []))
      drawRadius = Math.max(radius * Math.sqrt(fraction), 1.5)
      fill = sequentialColor(1)
    }
    const hex = svgEl("polygon", {
      points: _hexPoints(bin.cx, bin.cy, drawRadius), fill: fill,
      stroke: SURFACE_COLOR, "stroke-width": 0.75, part: "hexbin"
    }, [])
    const statText = statName === "count" ? `${formatNumber(bin.count)} point${bin.count === 1 ? "" : "s"}`
      : `${statName} ${formatNumber(bin.value)} (${formatNumber(bin.count)} points)`
    focusableMark(hex, `Bin at x ${formatNumber(dataX, { maximumSignificantDigits: 3 })}, ` +
      `y ${formatNumber(dataY, { maximumSignificantDigits: 3 })}: ${statText}`)
    const halfWidth = radius * xStep
    const halfHeight = radius * Math.sqrt(3) / 2 * yStep
    activateOnKey(hex, () => {
      ctx.emit("mj-chart-hexbin-click", {
        x: dataX, y: dataY,
        x0: dataX - halfWidth, x1: dataX + halfWidth,
        y0: dataY - halfHeight, y1: dataY + halfHeight,
        stat: statName, value: bin.value, count: bin.count,
        cx: bin.cx, cy: bin.cy
      })
    })
    marks.appendChild(hex)
    rows.push([dataX, dataY, bin.count, bin.value])

    if (showLabels === true && drawRadius > 10) {
      marks.appendChild(svgEl("text", {
        x: bin.cx, y: bin.cy + 4, "text-anchor": "middle",
        "font-size": Math.max(8, Math.min(11, drawRadius * 0.5)), "font-weight": 600,
        fill: TEXT_COLOR, stroke: SURFACE_COLOR, "stroke-width": 2.5, "stroke-opacity": 0.6,
        "paint-order": "stroke", "pointer-events": "none", "aria-hidden": "true"
      }, formatNumber(bin.value, { maximumSignificantDigits: 3 })))
    }
  }

  drawBaseline(axes, 0, plotH, plotW, plotH)
  drawBaseline(axes, 0, 0, 0, plotH)
  if (encoding === "color") {
    const rampLength = Math.min(plotH, 180)
    drawColorRamp(axes, {
      x: plotW + 12, y: (plotH - rampLength) / 2, length: rampLength, thickness: 10, vertical: true,
      colorAt: (fraction) => sequentialColor(fraction),
      labels: [
        { fraction: 0, text: formatNumber(rampLow, { maximumSignificantDigits: 3 }) },
        { fraction: 1, text: formatNumber(rampHigh, { maximumSignificantDigits: 3 }) }
      ]
    })
  }

  ctx.setLegend([])
  ctx.setTable({
    columns: ["Bin x", "Bin y", "Points", statName === "count" ? "Count" : statName],
    rows: rows,
    caption: "Hexagonal bins"
  })
  return root
}


registerRenderer("hexbin", render)
