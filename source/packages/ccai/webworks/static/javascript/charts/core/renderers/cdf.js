/*
 * cdf.js
 *
 * Cumulative distribution function (ECDF / CDF) renderer.
 *
 * Registers: "cdf"
 *
 * ctx.model.series data shapes:
 *   Raw samples (renderer computes ECDF):
 *     series[]: { name, samples: [n, …] }
 *   Pre-computed:
 *     series[]: { name, points: [{x, y}, …] }
 *
 * Relevant ctx.attrs:
 *   direction   "ascending" (default) | "descending" (survival function)
 *   scale       "probability" (default 0–1) | "percent" (0–100)
 *   smooth      "true" — use a smooth spline instead of step function
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber, linePath, smoothPath } from "../svgdraw.js";
import { linearScale, niceTicks } from "../scales.js";


/* ── ECDF computation ─────────────────────────────────────────────────────── */

function _buildEcdf(samples, direction, scaleMax) {
  /*
   * Build empirical CDF points from raw samples.
   *
   * :param direction: "ascending" or "descending".
   * :param scaleMax: 1 (probability) or 100 (percent).
   * :returns: Array of {x, y} sorted by x.
   */
  const sorted = samples.slice().sort((a, b) => a - b)
  const n = sorted.length
  const pts = []
  for (let i = 0; i < n; i = i + 1) {
    const cumProb = (i + 1) / n
    const y = direction === "descending"
      ? (1 - cumProb) * scaleMax
      : cumProb * scaleMax
    pts.push({ x: sorted[i], y: y })
  }
  return pts
}


/* ── main render ─────────────────────────────────────────────────────────── */

export function render(ctx) {
  /*
   * Render a cumulative distribution chart.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const model = ctx.model
  const horizontal = ctx.orientation === "horizontal"
  const direction = ctx.attrs("direction", "ascending")
  const scaleAttr = ctx.attrs("scale", "probability")
  const smoothAttr = ctx.attrs("smooth", "false") === "true"

  const scaleMax = scaleAttr === "percent" ? 100 : 1
  const yLabel = scaleAttr === "percent" ? "Cumulative %" : "Cumulative Probability"
  const yTickFmt = (v) => scaleAttr === "percent" ? `${formatNumber(v)}%` : formatNumber(v)

  const root = svgEl("g", { part: "plot" }, [])

  const series = model.series
  if (series === null || series === undefined || series.length === 0) {
    return root
  }

  /* Resolve per-series CDF points. */
  const resolvedSeries = []
  for (let si = 0; si < series.length; si = si + 1) {
    const s = series[si]
    let pts = null
    if (Array.isArray(s.points) === true && s.points.length > 0) {
      pts = s.points.slice().sort((a, b) => a.x - b.x)
      if (direction === "descending") {
        pts = pts.map((p) => ({ x: p.x, y: (scaleMax - p.y) }))
      }
      if (scaleAttr === "percent") {
        const needsScale = pts[pts.length - 1].y <= 1
        if (needsScale === true) {
          pts = pts.map((p) => ({ x: p.x, y: p.y * 100 }))
        }
      }
    } else if (Array.isArray(s.samples) === true && s.samples.length > 0) {
      pts = _buildEcdf(s.samples, direction, scaleMax)
    } else {
      continue
    }
    resolvedSeries.push({ name: s.name, pts: pts })
  }

  if (resolvedSeries.length === 0) {
    return root
  }

  /* Compute value (x) extent. */
  let xMin = Infinity
  let xMax = -Infinity
  for (let si = 0; si < resolvedSeries.length; si = si + 1) {
    const pts = resolvedSeries[si].pts
    for (let i = 0; i < pts.length; i = i + 1) {
      if (pts[i].x < xMin) { xMin = pts[i].x }
      if (pts[i].x > xMax) { xMax = pts[i].x }
    }
  }
  const xPad = (xMax - xMin) * 0.05 || 0.5
  xMin = xMin - xPad
  xMax = xMax + xPad

  const yMin = 0
  const yMax = scaleMax

  const margin = { top: 16, right: 16, bottom: 48, left: 56 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  /* Axes: horizontal orientation swaps x/y. */
  const xScale = horizontal
    ? linearScale([yMin, yMax], [0, plotW])     /* cumulative on x */
    : linearScale([xMin, xMax], [0, plotW])      /* value on x */
  const yScale = horizontal
    ? linearScale([xMin, xMax], [plotH, 0])      /* value on y */
    : linearScale([yMin, yMax], [plotH, 0])      /* cumulative on y */

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  /* X gridlines + labels. */
  const xTicks = horizontal
    ? niceTicks(yMin, yMax, 5)
    : niceTicks(xMin, xMax, 6)
  for (let ti = 0; ti < xTicks.length; ti = ti + 1) {
    const tick = xTicks[ti]
    const x = xScale(tick)
    plot.appendChild(svgEl("line", {
      x1: x, y1: 0, x2: x, y2: plotH,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    const label = horizontal ? yTickFmt(tick) : formatNumber(tick)
    plot.appendChild(svgEl("text", {
      x: x, y: plotH + 16, "text-anchor": "middle",
      "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
    }, label))
  }

  /* Y gridlines + labels. */
  const yTicks = horizontal
    ? niceTicks(xMin, xMax, 5)
    : niceTicks(yMin, yMax, 5)
  for (let ti = 0; ti < yTicks.length; ti = ti + 1) {
    const tick = yTicks[ti]
    const y = yScale(tick)
    plot.appendChild(svgEl("line", {
      x1: 0, y1: y, x2: plotW, y2: y,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    const label = horizontal ? formatNumber(tick) : yTickFmt(tick)
    plot.appendChild(svgEl("text", {
      x: -8, y: y + 4, "text-anchor": "end",
      "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
    }, label))
  }

  /* Axis baseline. */
  const baselineY = yScale(0)
  plot.appendChild(svgEl("line", {
    x1: 0, y1: baselineY, x2: plotW, y2: baselineY,
    stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
  }, []))

  /* Axis labels. */
  const xAxisLabel = horizontal ? yLabel : "Value"
  plot.appendChild(svgEl("text", {
    x: plotW / 2, y: plotH + 36, "text-anchor": "middle",
    "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
  }, xAxisLabel))

  const yAxisLabel = horizontal ? "Value" : yLabel
  const yLabelEl = svgEl("text", {
    x: 0, y: 0, "text-anchor": "middle",
    "font-size": 11, fill: "var(--mj-text-muted, #6b7280)",
    transform: `translate(${-margin.left + 12},${plotH / 2}) rotate(-90)`
  }, yAxisLabel)
  plot.appendChild(yLabelEl)

  /* Draw CDF lines. */
  for (let si = 0; si < resolvedSeries.length; si = si + 1) {
    const rs = resolvedSeries[si]
    const color = ctx.colorFor(si)
    const pts = rs.pts

    let svgPoints = null
    if (horizontal === true) {
      /* cumulative on x, value on y */
      svgPoints = pts.map((p) => ({ x: xScale(p.y), y: yScale(p.x) }))
    } else {
      /* value on x, cumulative on y */
      svgPoints = pts.map((p) => ({ x: xScale(p.x), y: yScale(p.y) }))
    }

    let pathD = ""

    if (smoothAttr === true) {
      pathD = smoothPath(svgPoints)
    } else {
      /* Step function: each CDF jump is a right-angle step. */
      const stepPoints = []
      for (let i = 0; i < svgPoints.length; i = i + 1) {
        if (i > 0) {
          /* Horizontal segment from previous y to current x, then vertical up. */
          stepPoints.push({ x: svgPoints[i].x, y: svgPoints[i - 1].y })
        }
        stepPoints.push(svgPoints[i])
      }
      pathD = linePath(stepPoints)
    }

    if (pathD !== "") {
      const line = svgEl("path", {
        d: pathD, fill: "none",
        stroke: color, "stroke-width": 2
      }, [])
      line.setAttribute("part", "cdf-line")
      line.setAttribute("tabindex", "0")
      line.setAttribute("role", "img")
      line.setAttribute("aria-label", `${rs.name} cumulative distribution`)
      line.appendChild(svgEl("title", null, `${rs.name} CDF`))
      const handlerSeries = rs
      const clickHandler = () => {
        ctx.emit("mj-chart-cdf-click", { series: handlerSeries.name })
      }
      line.addEventListener("click", clickHandler)
      line.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault()
          clickHandler()
        }
      })
      plot.appendChild(line)
    }

    /* Optional step markers — small circles at each data point. */
    for (let i = 0; i < svgPoints.length; i = i + 1) {
      const dot = svgEl("circle", {
        cx: svgPoints[i].x, cy: svgPoints[i].y, r: 3,
        fill: color, opacity: 0.7
      }, [])
      dot.setAttribute("part", "cdf-point")
      dot.setAttribute("tabindex", "0")
      dot.setAttribute("role", "img")
      dot.setAttribute("aria-label",
        `${rs.name}: value=${formatNumber(pts[i].x)}, cumulative=${yTickFmt(pts[i].y)}`)
      dot.appendChild(svgEl("title", null,
        `${rs.name}\nValue: ${formatNumber(pts[i].x)}\nCumulative: ${yTickFmt(pts[i].y)}`))
      const handlerPt = pts[i]
      const handlerRs = rs
      const ptClickHandler = () => {
        ctx.emit("mj-chart-cdf-point-click", {
          series: handlerRs.name, x: handlerPt.x, y: handlerPt.y
        })
      }
      dot.addEventListener("click", ptClickHandler)
      dot.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault()
          ptClickHandler()
        }
      })
      plot.appendChild(dot)
    }
  }

  return root
}


registerRenderer("cdf", render)
