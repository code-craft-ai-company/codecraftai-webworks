/*
 * scatter.js
 *
 * Scatter / Bubble / Connected-scatter / Residual renderer.
 *
 * Registered chart types (ctx.type picks the drawing):
 *   "scatter"           x/y marks (one shape per series when there are several)
 *   "bubble"            a third value as circle AREA: radius = maxR * sqrt(size / maxSize)
 *   "connected-scatter" points joined in data order (a null point breaks the path)
 *   "residual"          residuals (y) against fitted values (x), with a y-axis
 *                       centred on 0 and a dashed zero reference line
 *
 * Data shape:
 *   series[].points: [{ x, y, size?, label? }, ...]   non-finite x / y are skipped
 *   series[].shape:  "circle" | "square" | "triangle" | "diamond" (optional)
 *   meta.xLabel / meta.yLabel: axis titles (residual defaults: "Fitted values",
 *     "Residuals")
 *   residual.transform: "scale-location" plots sqrt(|residual|) (residual type)
 *
 * Marks are never moved off their data position: the axis domains are
 * widened so the largest mark fits inside the plot.
 *
 * Relevant ctx.attrs:
 *   min-radius   smallest bubble radius in px, a visibility floor (default 3)
 *   max-radius   radius of the largest bubble in px (default 40; capped at
 *                12% of the smaller chart dimension so small charts stay legible)
 *   trend        "linear" — a least-squares line per series
 *   show-labels  boolean — point labels (default: on for bubble and
 *                connected-scatter, off for scatter and residual)
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber, linePath } from "../svgdraw.js";
import { linearScale } from "../scales.js";
import {
  isFiniteNumber, axisLayer, drawTicks, drawAxisTitle, drawBaseline, tickCount,
  activateOnKey, focusableMark, fitText, MUTED_TEXT_COLOR, AXIS_COLOR
} from "./diststats.js";
import { booleanOption } from "../chartoptions.js";

const SHAPES = ["circle", "square", "triangle", "diamond"];
const POINT_RADIUS = 5;


function _pointShape(shape, cx, cy, r) {
  /*
   * An SVG mark of the given shape and enclosing radius.
   */
  if (shape === "square") {
    const half = r * 0.85
    return svgEl("rect", { x: cx - half, y: cy - half, width: half * 2, height: half * 2 }, [])
  }
  if (shape === "triangle") {
    const h = r * 1.6
    const w = r * 1.4
    const points = `${cx.toFixed(2)},${(cy - h * 0.6).toFixed(2)} ` +
      `${(cx - w / 2).toFixed(2)},${(cy + h * 0.4).toFixed(2)} ` +
      `${(cx + w / 2).toFixed(2)},${(cy + h * 0.4).toFixed(2)}`
    return svgEl("polygon", { points: points }, [])
  }
  if (shape === "diamond") {
    const d = r * 1.2
    const points = `${cx.toFixed(2)},${(cy - d).toFixed(2)} ${(cx + d).toFixed(2)},${cy.toFixed(2)} ` +
      `${cx.toFixed(2)},${(cy + d).toFixed(2)} ${(cx - d).toFixed(2)},${cy.toFixed(2)}`
    return svgEl("polygon", { points: points }, [])
  }
  return svgEl("circle", { cx: cx, cy: cy, r: r }, [])
}


function _paddedScale(low, high, pixels, padPx, reversed) {
  /*
   * A linear scale over [0, pixels] whose domain is [low, high] widened so
   * that the data ends sit `padPx` inside the plot edges.
   */
  const span = high - low
  const usable = Math.max(pixels - 2 * padPx, pixels * 0.2)
  const inset = (pixels - usable) / 2
  let lo = low
  let hi = high
  if (span > 0) {
    const perPixel = span / usable
    lo = low - inset * perPixel
    hi = high + inset * perPixel
  } else {
    const magnitude = Math.abs(low) > 0 ? Math.abs(low) * 0.1 : 1
    lo = low - magnitude
    hi = high + magnitude
  }
  const scale = reversed === true ? linearScale([lo, hi], [pixels, 0]) : linearScale([lo, hi], [0, pixels])
  return scale
}


function _leastSquares(points) {
  /*
   * Slope and intercept of the least-squares line through finite points,
   * or null with fewer than two distinct x values.
   */
  const n = points.length
  if (n < 2) {
    return null
  }
  let sx = 0
  let sy = 0
  for (let index = 0; index < n; index = index + 1) {
    sx = sx + points[index].x
    sy = sy + points[index].y
  }
  const mx = sx / n
  const my = sy / n
  let sxx = 0
  let sxy = 0
  for (let index = 0; index < n; index = index + 1) {
    sxx = sxx + (points[index].x - mx) * (points[index].x - mx)
    sxy = sxy + (points[index].x - mx) * (points[index].y - my)
  }
  if (sxx === 0) {
    return null
  }
  const slope = sxy / sxx
  return { slope: slope, intercept: my - slope * mx }
}


function _clipLine(fit, xDomain, yDomain) {
  /*
   * The x interval of y = slope * x + intercept that stays inside both
   * domains, or null when the line misses the plot.
   */
  let x0 = Math.min(xDomain[0], xDomain[1])
  let x1 = Math.max(xDomain[0], xDomain[1])
  const yLow = Math.min(yDomain[0], yDomain[1])
  const yHigh = Math.max(yDomain[0], yDomain[1])
  if (fit.slope !== 0) {
    const a = (yLow - fit.intercept) / fit.slope
    const b = (yHigh - fit.intercept) / fit.slope
    x0 = Math.max(x0, Math.min(a, b))
    x1 = Math.min(x1, Math.max(a, b))
  } else if (fit.intercept < yLow || fit.intercept > yHigh) {
    return null
  }
  if (x1 <= x0) {
    return null
  }
  return [x0, x1]
}


export function render(ctx) {
  /*
   * Render a scatter / bubble / connected-scatter / residual chart.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const model = ctx.model
  const type = ctx.type
  const isBubble = type === "bubble" || booleanOption(ctx, "bubble", false)
  const isConnected = type === "connected-scatter" || booleanOption(ctx, "connected", false)
  const isResidual = type === "residual" || booleanOption(ctx, "residual", false)
  const raw = ctx.raw !== null && ctx.raw !== undefined ? ctx.raw : {}
  const residualOptions = raw.residual !== null && typeof raw.residual === "object" ? raw.residual : {}
  const scaleLocation = isResidual === true && residualOptions.transform === "scale-location"
  const showLabels = booleanOption(ctx, "show-labels", isBubble === true || isConnected === true)
  const trend = ctx.attrs("trend", "") === "linear"
  const minRadiusAttr = parseFloat(ctx.attrs("min-radius", "3"))
  const maxRadiusAttr = parseFloat(ctx.attrs("max-radius", "40"))
  const minRadius = isFiniteNumber(minRadiusAttr) === true && minRadiusAttr >= 0 ? minRadiusAttr : 3
  const maxRadiusSetting = isFiniteNumber(maxRadiusAttr) === true && maxRadiusAttr > 0 ? maxRadiusAttr : 40

  const root = svgEl("g", { part: "plot" }, [])
  const series = Array.isArray(model.series) === true ? model.series : []

  /* Usable points per series (y transformed for scale-location). */
  const prepared = []
  let maxSize = 0
  let xLow = Infinity
  let xHigh = -Infinity
  let yLow = Infinity
  let yHigh = -Infinity
  for (let si = 0; si < series.length; si = si + 1) {
    const list = Array.isArray(series[si].points) === true ? series[si].points : []
    const points = []
    for (let pi = 0; pi < list.length; pi = pi + 1) {
      const point = list[pi]
      if (point === null || typeof point !== "object" ||
          isFiniteNumber(point.x) === false || isFiniteNumber(point.y) === false) {
        points.push(null)
        continue
      }
      const y = scaleLocation === true ? Math.sqrt(Math.abs(point.y)) : point.y
      const size = isFiniteNumber(point.size) === true && point.size > 0 ? point.size : 0
      maxSize = Math.max(maxSize, size)
      points.push({ x: point.x, y: y, size: size, source: point })
      xLow = Math.min(xLow, point.x)
      xHigh = Math.max(xHigh, point.x)
      yLow = Math.min(yLow, y)
      yHigh = Math.max(yHigh, y)
    }
    prepared.push({ entry: series[si], points: points })
  }
  if (xLow === Infinity) {
    return root
  }

  /* The largest bubble is capped to a share of the plot so it never fills a small chart. */
  const roomRadius = Math.max(Math.min(ctx.width, ctx.height) * 0.12, minRadius, 4)
  const maxRadius = Math.min(maxRadiusSetting, roomRadius)
  const radiusOf = (point) => {
    if (isBubble === false) {
      return POINT_RADIUS
    }
    const scaled = maxSize > 0 ? maxRadius * Math.sqrt(point.size / maxSize) : 0
    return Math.max(scaled, minRadius)
  }
  const largest = isBubble === true ? Math.max(maxRadius, minRadius) : POINT_RADIUS

  if (isResidual === true && scaleLocation === false) {
    const reach = Math.max(Math.abs(yLow), Math.abs(yHigh))
    yLow = -reach
    yHigh = reach
  }
  if (scaleLocation === true) {
    yLow = 0
  }

  const meta = model.meta !== null && model.meta !== undefined ? model.meta : {}
  let xTitle = typeof meta.xLabel === "string" ? meta.xLabel : ""
  let yTitle = typeof meta.yLabel === "string" ? meta.yLabel : ""
  if (isResidual === true) {
    xTitle = xTitle.length > 0 ? xTitle : "Fitted values"
    yTitle = yTitle.length > 0 ? yTitle : (scaleLocation === true ? "√|Residuals|" : "Residuals")
  }

  const margin = {
    top: 16, right: 20,
    bottom: xTitle.length > 0 ? 50 : 36,
    left: yTitle.length > 0 ? 70 : 56
  }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)
  const padX = Math.min(largest + plotW * 0.03, plotW * 0.4)
  const padY = Math.min(largest + plotH * 0.03, plotH * 0.4)
  const xScale = _paddedScale(xLow, xHigh, plotW, padX, false)
  const yScale = _paddedScale(yLow, yHigh, plotH, padY, true)

  const plot = svgEl("g", { transform: `translate(${margin.left},${margin.top})` }, [])
  root.appendChild(plot)
  const axes = axisLayer(plot)
  drawTicks(axes, xScale, { side: "bottom", extent: plotH, count: tickCount(plotW, 70) })
  drawTicks(axes, yScale, { side: "left", extent: plotW, count: tickCount(plotH, 40) })
  drawAxisTitle(axes, xTitle, "bottom", plotW, plotH, 38)
  drawAxisTitle(axes, yTitle, "left", plotW, plotH, 54)
  drawBaseline(axes, 0, plotH, plotW, plotH)
  drawBaseline(axes, 0, 0, 0, plotH)

  /* Zero reference line: always for residuals (inside the centred domain). */
  const zeroRequested = isResidual === true || residualOptions["zero-line"] === true
  if (zeroRequested === true && scaleLocation === false) {
    const y0 = yScale(0)
    if (y0 >= 0 && y0 <= plotH) {
      axes.appendChild(svgEl("line", {
        x1: 0, y1: y0, x2: plotW, y2: y0, stroke: AXIS_COLOR,
        "stroke-width": 1.5, "stroke-dasharray": "4,3", part: "zero-line"
      }, []))
    }
  }

  const marks = svgEl("g", { part: "marks" }, [])
  plot.appendChild(marks)
  /* Point labels go above every mark, so a large bubble never hides one. */
  const labels = svgEl("g", { part: "point-labels", "aria-hidden": "true" }, [])
  const rows = []
  for (let si = 0; si < prepared.length; si = si + 1) {
    const entry = prepared[si].entry
    const points = prepared[si].points
    const color = ctx.colorFor(entry.name)
    const shape = typeof entry.shape === "string" ? entry.shape
      : (prepared.length > 1 ? SHAPES[si % SHAPES.length] : "circle")
    const group = svgEl("g", { part: "series" }, [])

    if (isConnected === true) {
      const path = linePath(points.map((point) => point === null ? null : { x: xScale(point.x), y: yScale(point.y) }))
      if (path !== "") {
        group.appendChild(svgEl("path", {
          d: path, fill: "none", stroke: color, "stroke-width": 1.5,
          "stroke-linejoin": "round", "stroke-linecap": "round", "stroke-opacity": 0.7,
          part: "connector"
        }, []))
      }
    }

    if (trend === true) {
      const fit = _leastSquares(points.filter((point) => point !== null))
      const segment = fit !== null ? _clipLine(fit, xScale.domain(), yScale.domain()) : null
      if (segment !== null) {
        group.appendChild(svgEl("line", {
          x1: xScale(segment[0]), y1: yScale(fit.slope * segment[0] + fit.intercept),
          x2: xScale(segment[1]), y2: yScale(fit.slope * segment[1] + fit.intercept),
          stroke: color, "stroke-width": 1.5, "stroke-dasharray": "6 4", part: "trend-line"
        }, []))
      }
    }

    /* Larger bubbles first, so small ones stay visible on top. */
    const order = []
    for (let pi = 0; pi < points.length; pi = pi + 1) {
      if (points[pi] !== null) {
        order.push(pi)
      }
    }
    if (isBubble === true) {
      order.sort((a, b) => points[b].size - points[a].size)
    }

    for (let oi = 0; oi < order.length; oi = oi + 1) {
      const point = points[order[oi]]
      const source = point.source
      const cx = xScale(point.x)
      const cy = yScale(point.y)
      const r = radiusOf(point)
      const mark = _pointShape(shape, cx, cy, r)
      mark.setAttribute("fill", color)
      mark.setAttribute("fill-opacity", isBubble === true ? "0.6" : "0.8")
      mark.setAttribute("stroke", color)
      mark.setAttribute("stroke-width", "1")
      mark.setAttribute("part", "point")

      const hasLabel = source.label !== null && source.label !== undefined && String(source.label).length > 0
      const labelText = hasLabel === true ? String(source.label) : ""
      const sizeText = isBubble === true && isFiniteNumber(source.size) === true ? `, size ${formatNumber(source.size)}` : ""
      const yText = scaleLocation === true ? `residual ${formatNumber(source.y)}` : `y ${formatNumber(source.y)}`
      const prefix = hasLabel === true ? `${labelText} (${entry.name})` : entry.name
      focusableMark(mark, `${prefix}: x ${formatNumber(source.x)}, ${yText}${sizeText}`)

      const detail = { series: entry.name, x: source.x, y: source.y }
      if (source.size !== undefined) {
        detail.size = source.size
      }
      if (source.label !== undefined) {
        detail.label = source.label
      }
      activateOnKey(mark, () => {
        ctx.emit("mj-chart-point-click", detail)
      })
      group.appendChild(mark)

      if (showLabels === true && hasLabel === true) {
        const rightRoom = plotW - (cx + r + 3)
        const onLeft = rightRoom < labelText.length * 5.8 && cx - r - 3 > rightRoom
        labels.appendChild(svgEl("text", {
          x: onLeft === true ? cx - r - 3 : cx + r + 3, y: cy + 4,
          "text-anchor": onLeft === true ? "end" : "start",
          "font-size": 10, fill: MUTED_TEXT_COLOR, "pointer-events": "none",
          "aria-hidden": "true", part: "point-label"
        }, fitText(labelText, Math.max(onLeft === true ? cx - r - 3 : rightRoom, 24), 10)))
      }
      rows.push([entry.name, labelText, source.x, source.y].concat(isBubble === true ? [source.size] : []))
    }
    marks.appendChild(group)
  }

  plot.appendChild(labels)

  const columns = ["Series", "Label", xTitle.length > 0 ? xTitle : "X", isResidual === true ? "Residual" : (yTitle.length > 0 ? yTitle : "Y")]
  if (isBubble === true) {
    columns.push("Size")
  }
  ctx.setTable({ columns: columns, rows: rows, caption: "Points" })
  return root
}


registerRenderer("scatter", render)
registerRenderer("bubble", render)
registerRenderer("connected-scatter", render)
registerRenderer("residual", render)
