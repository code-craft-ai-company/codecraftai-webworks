/*
 * loglog.js
 *
 * Log-log and semi-log line/scatter chart renderer.
 *
 * Registered types:
 *   "log-log"   - both axes logarithmic (power-law relationships)
 *   "semi-log"  - one axis logarithmic, one linear (exponential relationships)
 *
 * The `scale-x` and `scale-y` controller attributes select the per-axis scale:
 *   "log"    → logScale from scales.js
 *   "linear" → linearScale from scales.js (default)
 *
 * Renderer contract: render(ctx) -> SVGElement  (a <g> within [0..width]x[0..height])
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, formatNumber, linePath } from "../svgdraw.js";
import { linearScale, logScale, niceTicks } from "../scales.js";


/* ── axis tick label formatter ────────────────────────────────── */

function _superscript(exp) {
  /*
   * Format an integer exponent as Unicode superscript characters.
   */
  const map = {
    "-": "⁻", "0": "⁰", "1": "¹", "2": "²", "3": "³",
    "4": "⁴", "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹"
  }
  const s = String(exp)
  let result = ""
  for (let i = 0; i < s.length; i = i + 1) {
    result = result + (map[s[i]] || s[i])
  }
  return result
}


function _tickLabel(value, isLog) {
  /*
   * Format a tick label.  Log ticks are shown as 10^n when value is a
   * power of 10; other values fall back to numeric formatting.
   */
  if (isLog === false) {
    return formatNumber(value)
  }
  if (value <= 0) {
    return formatNumber(value)
  }
  const exp = Math.log10(value)
  const rounded = Math.round(exp)
  if (Math.abs(exp - rounded) < 0.01) {
    return "10" + _superscript(rounded)
  }
  return formatNumber(value)
}


/* ── domain from series ───────────────────────────────────────── */

function _seriesExtent(series, key, excludeNonPositive) {
  /*
   * Find [min, max] of `key` across all series points.
   * When excludeNonPositive is true, values ≤ 0 are skipped (required for log).
   */
  let lo = Infinity
  let hi = -Infinity
  for (let s = 0; s < series.length; s = s + 1) {
    const pts = series[s].points
    if (pts === null || pts === undefined) { continue }
    for (let p = 0; p < pts.length; p = p + 1) {
      const v = pts[p][key]
      if (typeof v !== "number") { continue }
      if (excludeNonPositive === true && v <= 0) { continue }
      if (v < lo) { lo = v }
      if (v > hi) { hi = v }
    }
  }
  if (lo === Infinity) { return [1, 10] }
  if (lo === hi) { return [lo * 0.5, hi * 2] }
  return [lo, hi]
}


/* ── build scale ──────────────────────────────────────────────── */

function _buildScale(kind, domain, range) {
  /*
   * Build a linear or log scale.
   */
  if (kind === "log") {
    const safeMin = domain[0] > 0 ? domain[0] : 1e-9
    const safeMax = domain[1] > 0 ? domain[1] : 1
    return logScale([safeMin, safeMax], range)
  }
  const lo = domain[0]
  const hi = domain[1]
  const pad = (hi - lo) * 0.05
  return linearScale([lo - pad, hi + pad], range)
}


/* ── axes ─────────────────────────────────────────────────────── */

function _drawAxes(plot, plotW, plotH, xScale, yScale, scaleX, scaleY, meta) {
  const xTicks = xScale.ticks(6)
  for (let i = 0; i < xTicks.length; i = i + 1) {
    const px = xScale(xTicks[i])
    plot.appendChild(svgEl("line", {
      x1: px, y1: 0, x2: px, y2: plotH,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    plot.appendChild(svgEl("text", {
      x: px, y: plotH + 14, "text-anchor": "middle",
      "font-size": 10, fill: "var(--mj-text-muted, #6b7280)"
    }, _tickLabel(xTicks[i], scaleX === "log")))
  }

  const yTicks = yScale.ticks(6)
  for (let i = 0; i < yTicks.length; i = i + 1) {
    const py = yScale(yTicks[i])
    plot.appendChild(svgEl("line", {
      x1: 0, y1: py, x2: plotW, y2: py,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    plot.appendChild(svgEl("text", {
      x: -6, y: py + 4, "text-anchor": "end",
      "font-size": 10, fill: "var(--mj-text-muted, #6b7280)"
    }, _tickLabel(yTicks[i], scaleY === "log")))
  }

  if (meta !== null && meta !== undefined) {
    if (meta.xLabel) {
      plot.appendChild(svgEl("text", {
        x: plotW / 2, y: plotH + 32, "text-anchor": "middle",
        "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
      }, escapeHtml(meta.xLabel)))
    }
    if (meta.yLabel) {
      plot.appendChild(svgEl("text", {
        transform: `rotate(-90) translate(${-plotH / 2}, -40)`,
        "text-anchor": "middle",
        "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
      }, escapeHtml(meta.yLabel)))
    }
  }
  return
}


/* ── main renderer ────────────────────────────────────────────── */

export function render(ctx) {
  /*
   * Render a log-log or semi-log line/scatter chart.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const raw = ctx.raw
  const root = svgEl("g", { part: "plot" }, [])

  if (raw === null || raw === undefined) {
    return root
  }

  const series = (raw.series !== null && raw.series !== undefined) ? raw.series : []
  if (series.length === 0) {
    return root
  }

  /* Determine which axes are logarithmic */
  const chartType = ctx.attrs("type", "log-log")
  let scaleX = ctx.attrs("scale-x", "auto")
  let scaleY = ctx.attrs("scale-y", "auto")

  if (scaleX === "auto") {
    scaleX = "log"  /* both axes log for log-log */
  }
  if (scaleY === "auto") {
    scaleY = chartType === "semi-log" ? "log" : "log"
  }
  /* For semi-log, caller typically sets scale-x="log" scale-y="linear" or vice-versa.
   * Fall back to (log, linear) if type is semi-log and no explicit attrs. */
  if (chartType === "semi-log" && ctx.attrs("scale-x", null) === null &&
      ctx.attrs("scale-y", null) === null) {
    scaleX = "linear"
    scaleY = "log"
  }

  const margin = { top: 16, right: 16, bottom: 46, left: 62 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  const xExtent = _seriesExtent(series, "x", scaleX === "log")
  const yExtent = _seriesExtent(series, "y", scaleY === "log")

  const xScale = _buildScale(scaleX, xExtent, [0, plotW])
  const yScale = _buildScale(scaleY, yExtent, [plotH, 0])

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  const meta = (raw.meta !== null && raw.meta !== undefined) ? raw.meta : null
  _drawAxes(plot, plotW, plotH, xScale, yScale, scaleX, scaleY, meta)

  /* Series */
  for (let s = 0; s < series.length; s = s + 1) {
    const ser = series[s]
    const pts = ser.points
    if (pts === null || pts === undefined || pts.length === 0) { continue }
    const color = ctx.colorFor(ser.name)

    /* Filter invalid (non-positive on log axes) */
    const validPts = pts.filter((p) => {
      const xOk = scaleX !== "log" || (typeof p.x === "number" && p.x > 0)
      const yOk = scaleY !== "log" || (typeof p.y === "number" && p.y > 0)
      return xOk && yOk && typeof p.x === "number" && typeof p.y === "number"
    })

    if (validPts.length === 0) { continue }

    const pixPts = validPts.map((p) => ({
      x: xScale(p.x),
      y: yScale(p.y)
    }))

    /* Line */
    const pathData = linePath(pixPts)
    if (pathData !== "") {
      plot.appendChild(svgEl("path", {
        d: pathData,
        fill: "none",
        stroke: color,
        "stroke-width": 2,
        part: "line"
      }, []))
    }

    /* Point markers */
    for (let p = 0; p < validPts.length; p = p + 1) {
      const pt = validPts[p]
      const px2 = pixPts[p]
      const label = escapeHtml(
        ser.name + " x=" + formatNumber(pt.x) + " y=" + formatNumber(pt.y)
      )
      const dot = svgEl("circle", {
        cx: px2.x.toFixed(1), cy: px2.y.toFixed(1), r: 4,
        fill: color,
        stroke: "var(--mj-surface, #fff)",
        "stroke-width": 1,
        part: "point",
        tabindex: "0",
        role: "img",
        "aria-label": label
      }, [])
      dot.appendChild(svgEl("title", null, label))
      const detail = { series: ser.name, x: pt.x, y: pt.y }
      const handler = () => { ctx.emit("mj-chart-loglog-click", detail) }
      dot.addEventListener("click", handler)
      dot.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault()
          handler()
        }
      })
      plot.appendChild(dot)
    }
  }

  /* Axis baselines */
  plot.appendChild(svgEl("line", {
    x1: 0, y1: 0, x2: 0, y2: plotH,
    stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
  }, []))
  plot.appendChild(svgEl("line", {
    x1: 0, y1: plotH, x2: plotW, y2: plotH,
    stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
  }, []))

  return root
}


registerRenderer("log-log", render)
registerRenderer("semi-log", render)
