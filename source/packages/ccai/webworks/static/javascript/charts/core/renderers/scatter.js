/*
 * scatter.js
 *
 * Scatter / Bubble / Connected-scatter / Residual renderer.
 *
 * Registered chart types:
 *   "scatter"          — basic scatter plot (x/y circles)
 *   "bubble"           — scatter with a third size dimension (sqrt-scale radii)
 *   "connected-scatter"— scatter with a path joining points in data order
 *   "residual"         — scatter with a y=0 reference line
 *
 * ctx.model.series[].points: [{ x, y, size?, label? }, ...]
 * ctx.raw.residual?.zero-line  controls whether the zero line is forced on
 *   for the residual type (it is always drawn for "residual").
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, formatNumber, extent, linePath } from "../svgdraw.js";
import { linearScale, sqrtScale, niceTicks } from "../scales.js";


function _collectPoints(series) {
  /*
   * Flatten all series points into a single array for domain computation.
   *
   * :param series: The series array from the model.
   * :returns: All points across all series.
   */
  const all = []
  for (let s = 0; s < series.length; s = s + 1) {
    const pts = series[s].points
    if (pts === null || pts === undefined) {
      continue
    }
    for (let p = 0; p < pts.length; p = p + 1) {
      all.push(pts[p])
    }
  }
  return all
}


function _pointShape(shape, cx, cy, r) {
  /*
   * Build an SVG element for the given point shape.
   *
   * :param shape: "circle" | "square" | "triangle" | "diamond"
   * :param cx: Center x.
   * :param cy: Center y.
   * :param r: Enclosing radius.
   * :returns: An SVGElement.
   */
  if (shape === "square") {
    const half = r * 0.85
    return svgEl("rect", {
      x: cx - half, y: cy - half,
      width: half * 2, height: half * 2
    }, [])
  }
  if (shape === "triangle") {
    const h = r * 1.6
    const w = r * 1.4
    const points = `${cx},${(cy - h * 0.6).toFixed(2)} ` +
      `${(cx - w / 2).toFixed(2)},${(cy + h * 0.4).toFixed(2)} ` +
      `${(cx + w / 2).toFixed(2)},${(cy + h * 0.4).toFixed(2)}`
    return svgEl("polygon", { points: points }, [])
  }
  if (shape === "diamond") {
    const d = r * 1.2
    const points = `${cx},${cy - d} ${cx + d},${cy} ` +
      `${cx},${cy + d} ${cx - d},${cy}`
    return svgEl("polygon", { points: points }, [])
  }
  /* Default: circle */
  return svgEl("circle", { cx: cx, cy: cy, r: r }, [])
}


export function render(ctx) {
  /*
   * Render a scatter / bubble / connected-scatter / residual chart.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const model = ctx.model
  const chartType = ctx.attrs("type", "scatter")
  const isBubble = chartType === "bubble" || ctx.attrs("bubble", "false") === "true"
  const isConnected = chartType === "connected-scatter" ||
    ctx.attrs("connected", "false") === "true"
  const isResidual = chartType === "residual" ||
    ctx.attrs("residual", "false") === "true"

  const root = svgEl("g", { part: "plot" }, [])

  const series = model.series
  if (series === null || series === undefined || series.length === 0) {
    return root
  }

  const allPoints = _collectPoints(series)
  if (allPoints.length === 0) {
    return root
  }

  const margin = { top: 16, right: 16, bottom: 44, left: 56 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  /* Compute x / y domains. */
  const xVals = allPoints.map((pt) => pt.x)
  const yVals = allPoints.map((pt) => pt.y)
  const xDomain = extent(xVals)
  const yDomain = extent(yVals)

  /* Pad the domain slightly so points don't sit on the axis edge. */
  const xPad = (xDomain[1] - xDomain[0]) * 0.05 || 1
  const yPad = (yDomain[1] - yDomain[0]) * 0.05 || 1

  const xScale = linearScale(
    [xDomain[0] - xPad, xDomain[1] + xPad],
    [0, plotW]
  )
  const yScale = linearScale(
    [yDomain[0] - yPad, yDomain[1] + yPad],
    [plotH, 0]
  )

  /* Bubble size scale. */
  let sizeScale = null
  if (isBubble === true) {
    const sizeVals = allPoints
      .map((pt) => pt.size)
      .filter((s) => s !== null && s !== undefined && Number.isNaN(s) === false)
    const sizeDomain = extent(sizeVals)
    const minR = Number(ctx.attrs("min-radius", "4"))
    const maxR = Number(ctx.attrs("max-radius", "40"))
    sizeScale = sqrtScale([sizeDomain[0], sizeDomain[1]], [minR, maxR])
  }

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  /* Grid lines + tick labels (x axis). */
  const xTicks = niceTicks(xScale.domain()[0], xScale.domain()[1], 5)
  for (let t = 0; t < xTicks.length; t = t + 1) {
    const tick = xTicks[t]
    const x = xScale(tick)
    plot.appendChild(svgEl("line", {
      x1: x, y1: 0, x2: x, y2: plotH,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    plot.appendChild(svgEl("text", {
      x: x, y: plotH + 16, "text-anchor": "middle",
      "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
    }, formatNumber(tick)))
  }

  /* Grid lines + tick labels (y axis). */
  const yTicks = niceTicks(yScale.domain()[0], yScale.domain()[1], 5)
  for (let t = 0; t < yTicks.length; t = t + 1) {
    const tick = yTicks[t]
    const y = yScale(tick)
    plot.appendChild(svgEl("line", {
      x1: 0, y1: y, x2: plotW, y2: y,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    plot.appendChild(svgEl("text", {
      x: -8, y: y + 4, "text-anchor": "end",
      "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
    }, formatNumber(tick)))
  }

  /* Zero reference line for residual charts. */
  const showZeroLine = isResidual === true ||
    (ctx.raw !== null && ctx.raw !== undefined &&
     ctx.raw.residual !== null && ctx.raw.residual !== undefined &&
     ctx.raw.residual["zero-line"] === true)
  if (showZeroLine === true) {
    const y0 = yScale(0)
    if (y0 >= 0 && y0 <= plotH) {
      plot.appendChild(svgEl("line", {
        x1: 0, y1: y0, x2: plotW, y2: y0,
        stroke: "var(--mj-border-strong, #c7ccd6)",
        "stroke-width": 1.5,
        "stroke-dasharray": "4,3"
      }, []))
    }
  }

  /* Draw each series. */
  for (let s = 0; s < series.length; s = s + 1) {
    const ser = series[s]
    const pts = ser.points
    if (pts === null || pts === undefined || pts.length === 0) {
      continue
    }
    const color = ctx.colorFor(ser.name)
    const shape = ser.shape || "circle"
    const seriesGroup = svgEl("g", { part: "series" }, [])

    /* Connected-scatter: draw path first (beneath the points). */
    if (isConnected === true) {
      const screenPts = pts.map((pt) => {
        const validX = typeof pt.x === "number" && Number.isNaN(pt.x) === false
        const validY = typeof pt.y === "number" && Number.isNaN(pt.y) === false
        if (validX === false || validY === false) {
          return null
        }
        return { x: xScale(pt.x), y: yScale(pt.y) }
      })
      const pathData = linePath(screenPts)
      if (pathData !== "") {
        seriesGroup.appendChild(svgEl("path", {
          d: pathData,
          fill: "none",
          stroke: color,
          "stroke-width": 1.5,
          "stroke-linejoin": "round",
          "stroke-linecap": "round",
          opacity: 0.7
        }, []))
      }
    }

    /* Draw each point mark. */
    for (let p = 0; p < pts.length; p = p + 1) {
      const pt = pts[p]
      const validX = typeof pt.x === "number" && Number.isNaN(pt.x) === false
      const validY = typeof pt.y === "number" && Number.isNaN(pt.y) === false
      if (validX === false || validY === false) {
        continue
      }

      const cx = xScale(pt.x)
      const cy = yScale(pt.y)

      let r = 5
      if (isBubble === true && sizeScale !== null &&
          typeof pt.size === "number" && Number.isNaN(pt.size) === false) {
        r = sizeScale(pt.size)
      }

      /* Clamp to plot bounds (bubble). */
      const clampedCx = Math.max(r, Math.min(plotW - r, cx))
      const clampedCy = Math.max(r, Math.min(plotH - r, cy))

      const mark = _pointShape(shape, clampedCx, clampedCy, r)
      mark.setAttribute("fill", color)
      mark.setAttribute("fill-opacity", "0.75")
      mark.setAttribute("stroke", color)
      mark.setAttribute("stroke-width", "1")
      mark.setAttribute("part", "point")
      mark.setAttribute("tabindex", "0")
      mark.setAttribute("role", "img")

      const sizeInfo = (isBubble === true && typeof pt.size === "number")
        ? `, size: ${formatNumber(pt.size)}`
        : ""
      const labelInfo = pt.label ? ` (${pt.label})` : ""
      const ariaLabel = `${escapeHtml(ser.name)}: x=${formatNumber(pt.x)}, y=${formatNumber(pt.y)}${sizeInfo}${labelInfo}`
      mark.setAttribute("aria-label", ariaLabel)
      mark.appendChild(svgEl("title", null,
        `${ser.name} — x: ${formatNumber(pt.x)}, y: ${formatNumber(pt.y)}${sizeInfo}${labelInfo}`))

      const ptData = { series: ser.name, x: pt.x, y: pt.y }
      if (pt.size !== undefined) {
        ptData.size = pt.size
      }
      if (pt.label !== undefined) {
        ptData.label = pt.label
      }
      const handler = () => {
        ctx.emit("mj-chart-point-click", ptData)
      }
      mark.addEventListener("click", handler)
      mark.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault()
          handler()
        }
      })

      seriesGroup.appendChild(mark)

      /* Point label text for connected-scatter. */
      if (pt.label !== null && pt.label !== undefined &&
          (isConnected === true || isBubble === true)) {
        seriesGroup.appendChild(svgEl("text", {
          x: clampedCx + r + 3, y: clampedCy + 4,
          "font-size": 10,
          fill: "var(--mj-text-muted, #6b7280)",
          "pointer-events": "none"
        }, escapeHtml(String(pt.label))))
      }
    }

    plot.appendChild(seriesGroup)
  }

  /* Axis baselines. */
  plot.appendChild(svgEl("line", {
    x1: 0, y1: plotH, x2: plotW, y2: plotH,
    stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
  }, []))
  plot.appendChild(svgEl("line", {
    x1: 0, y1: 0, x2: 0, y2: plotH,
    stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
  }, []))

  return root
}


registerRenderer("scatter", render)
registerRenderer("bubble", render)
registerRenderer("connected-scatter", render)
registerRenderer("residual", render)
