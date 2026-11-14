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
 *   "log"    → logScale from scales.js, over whole decades
 *   "linear" → linearScale from scales.js, over a nice domain
 * log-log defaults both axes to log; semi-log defaults to a linear x and a
 * log y, and when only one attribute is set the other axis is the opposite
 * kind. Points that a log axis cannot show (<= 0) are gaps in the line and
 * are reported once per render with an mj-chart-error event
 * { message, severity: "warning", dropped }.
 *
 * Renderer contract: render(ctx) -> SVGElement  (a <g> within [0..width]x[0..height])
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber, linePath } from "../svgdraw.js";
import { linearScale, logScale, niceDomain } from "../scales.js";


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
  return formatNumber(value, { maximumSignificantDigits: 3 })
}


/* ── domain from series ───────────────────────────────────────── */

function _isNumber(value) {
  /*
   * True for a finite number.
   */
  const numeric = typeof value === "number" && Number.isFinite(value) === true
  return numeric
}


function _pointsOf(series) {
  /*
   * The point list of a normalized series ([] when it has none).
   */
  const points = Array.isArray(series.points) === true ? series.points : []
  return points
}


function _seriesExtent(series, key, excludeNonPositive) {
  /*
   * Find [min, max] of `key` across all series points, or null when no
   * point has a usable value. When excludeNonPositive is true, values <= 0
   * are skipped (they cannot be shown on a log axis).
   */
  let lo = Infinity
  let hi = -Infinity
  for (let s = 0; s < series.length; s = s + 1) {
    const pts = _pointsOf(series[s])
    for (let p = 0; p < pts.length; p = p + 1) {
      const v = pts[p] !== null && pts[p] !== undefined ? pts[p][key] : null
      if (_isNumber(v) === false) { continue }
      if (excludeNonPositive === true && v <= 0) { continue }
      lo = Math.min(lo, v)
      hi = Math.max(hi, v)
    }
  }
  if (lo === Infinity) {
    return null
  }
  return [lo, hi]
}


/* ── build scale ──────────────────────────────────────────────── */

function _buildScale(kind, domain, range) {
  /*
   * Build a log scale over whole decades, or a linear scale over a nice
   * domain.
   */
  if (kind === "log") {
    const ext = domain !== null ? domain : [1, 10]
    let low = Math.pow(10, Math.floor(Math.log10(ext[0]) + 1e-9))
    let high = Math.pow(10, Math.ceil(Math.log10(ext[1]) - 1e-9))
    if (high <= low) {
      low = low / 10
      high = high * 10
    }
    return logScale([low, high], range)
  }
  const ext = domain !== null ? domain : [0, 1]
  return linearScale(niceDomain(ext[0], ext[1], 6), range)
}


/* ── axes ─────────────────────────────────────────────────────── */

function _drawAxes(plot, plotW, plotH, xScale, yScale, scaleX, scaleY, meta) {
  /*
   * Gridlines (with 2..9 minor lines on narrow log axes), tick labels and
   * axis titles, hidden from assistive technology.
   */
  const axes = svgEl("g", { "aria-hidden": "true", part: "axes" }, [])

  const minorLines = (scale, vertical) => {
    const domain = scale.domain()
    const decades = Math.round(Math.log10(domain[1] / domain[0]))
    if (decades > 3) {
      return
    }
    for (let d = 0; d < decades; d = d + 1) {
      const base = domain[0] * Math.pow(10, d)
      for (let m = 2; m <= 9; m = m + 1) {
        const pos = scale(base * m)
        const ends = vertical === true
          ? { x1: pos, y1: 0, x2: pos, y2: plotH }
          : { x1: 0, y1: pos, x2: plotW, y2: pos }
        axes.appendChild(svgEl("line", {
          ...ends, stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 0.5
        }, []))
      }
    }
    return
  }
  if (scaleX === "log") {
    minorLines(xScale, true)
  }
  if (scaleY === "log") {
    minorLines(yScale, false)
  }

  const xTicks = xScale.ticks(6)
  for (let i = 0; i < xTicks.length; i = i + 1) {
    const px = xScale(xTicks[i])
    axes.appendChild(svgEl("line", {
      x1: px, y1: 0, x2: px, y2: plotH,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    axes.appendChild(svgEl("text", {
      x: px, y: plotH + 14, "text-anchor": "middle",
      "font-size": 10, fill: "var(--mj-text-muted, #6b7280)"
    }, _tickLabel(xTicks[i], scaleX === "log")))
  }

  const yTicks = yScale.ticks(6)
  for (let i = 0; i < yTicks.length; i = i + 1) {
    const py = yScale(yTicks[i])
    axes.appendChild(svgEl("line", {
      x1: 0, y1: py, x2: plotW, y2: py,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    axes.appendChild(svgEl("text", {
      x: -6, y: py + 4, "text-anchor": "end",
      "font-size": 10, fill: "var(--mj-text-muted, #6b7280)"
    }, _tickLabel(yTicks[i], scaleY === "log")))
  }

  if (typeof meta.xLabel === "string" && meta.xLabel.length > 0) {
    axes.appendChild(svgEl("text", {
      x: plotW / 2, y: plotH + 32, "text-anchor": "middle",
      "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
    }, meta.xLabel))
  }
  if (typeof meta.yLabel === "string" && meta.yLabel.length > 0) {
    axes.appendChild(svgEl("text", {
      transform: `rotate(-90) translate(${-plotH / 2}, -46)`,
      "text-anchor": "middle",
      "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
    }, meta.yLabel))
  }

  /* Axis baselines */
  axes.appendChild(svgEl("line", {
    x1: 0, y1: 0, x2: 0, y2: plotH,
    stroke: "var(--mj-border-strong, #878e9c)", "stroke-width": 1.25
  }, []))
  axes.appendChild(svgEl("line", {
    x1: 0, y1: plotH, x2: plotW, y2: plotH,
    stroke: "var(--mj-border-strong, #878e9c)", "stroke-width": 1.25
  }, []))
  plot.appendChild(axes)
  return
}


/* ── main renderer ────────────────────────────────────────────── */

function _axisKinds(ctx) {
  /*
   * The scale kind ("log" | "linear") of each axis. log-log defaults both
   * axes to log. semi-log defaults to a linear x and a log y; when only one
   * axis is set, the other axis gets the opposite kind.
   */
  const given = (name) => {
    const value = ctx.attrs(name, null)
    return value === "log" || value === "linear" ? value : null
  }
  const opposite = (kind) => (kind === "log" ? "linear" : "log")
  let scaleX = given("scale-x")
  let scaleY = given("scale-y")
  if (ctx.type === "semi-log") {
    if (scaleX === null && scaleY === null) {
      scaleX = "linear"
      scaleY = "log"
    } else if (scaleX === null) {
      scaleX = opposite(scaleY)
    } else if (scaleY === null) {
      scaleY = opposite(scaleX)
    }
  } else {
    scaleX = scaleX !== null ? scaleX : "log"
    scaleY = scaleY !== null ? scaleY : "log"
  }
  return { x: scaleX, y: scaleY }
}


export function render(ctx) {
  /*
   * Render a log-log or semi-log line/scatter chart.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const root = svgEl("g", { part: "plot" }, [])
  const series = ctx.model.series
  const meta = ctx.model.meta
  if (series.length === 0) {
    return root
  }

  const kinds = _axisKinds(ctx)
  const scaleX = kinds.x
  const scaleY = kinds.y

  const margin = { top: 16, right: 16, bottom: 46, left: 66 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  const xScale = _buildScale(scaleX, _seriesExtent(series, "x", scaleX === "log"), [0, plotW])
  const yScale = _buildScale(scaleY, _seriesExtent(series, "y", scaleY === "log"), [plotH, 0])

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)
  _drawAxes(plot, plotW, plotH, xScale, yScale, scaleX, scaleY, meta)

  let dropped = 0

  for (let s = 0; s < series.length; s = s + 1) {
    const ser = series[s]
    const pts = _pointsOf(ser)
    if (pts.length === 0) { continue }
    const color = ctx.colorFor(ser.name)
    const group = svgEl("g", { part: "series", "data-series": ser.name }, [])

    /*
     * A point that cannot be drawn (null, or <= 0 on a log axis) is a gap:
     * the line breaks there instead of bridging its neighbours.
     */
    const pixPts = pts.map((p) => {
      if (p === null || p === undefined || _isNumber(p.x) === false || _isNumber(p.y) === false) {
        return null
      }
      if ((scaleX === "log" && p.x <= 0) || (scaleY === "log" && p.y <= 0)) {
        dropped = dropped + 1
        return null
      }
      return { x: xScale(p.x), y: yScale(p.y) }
    })

    const pathData = linePath(pixPts)
    if (pathData !== "") {
      group.appendChild(svgEl("path", {
        d: pathData,
        fill: "none",
        stroke: color,
        "stroke-width": 2,
        part: "line"
      }, []))
    }

    for (let p = 0; p < pts.length; p = p + 1) {
      const px2 = pixPts[p]
      if (px2 === null) {
        continue
      }
      const pt = pts[p]
      const label = `${ser.name}: x ${formatNumber(pt.x)}, y ${formatNumber(pt.y)}`
      const dot = svgEl("circle", {
        cx: px2.x.toFixed(1), cy: px2.y.toFixed(1), r: 4,
        fill: color,
        stroke: "var(--mj-surface, #fff)",
        "stroke-width": 1,
        part: "point",
        tabindex: "0",
        role: "img",
        "aria-label": label
      }, [svgEl("title", null, label)])
      const detail = { series: ser.name, x: pt.x, y: pt.y }
      const handler = () => { ctx.emit("mj-chart-loglog-click", detail) }
      dot.addEventListener("click", handler)
      dot.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault()
          handler()
        }
      })
      group.appendChild(dot)
    }
    plot.appendChild(group)
  }

  if (dropped > 0) {
    /* The spec's warning: points a log axis cannot show were left out. */
    ctx.emit("mj-chart-error", {
      message: `${dropped} point(s) with a value <= 0 cannot be shown on a log axis and were not drawn`,
      severity: "warning",
      dropped: dropped
    })
  }
  return root
}


registerRenderer("log-log", render)
registerRenderer("semi-log", render)
