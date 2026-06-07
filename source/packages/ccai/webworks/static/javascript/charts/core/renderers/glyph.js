/*
 * glyph.js
 *
 * Glyph chart renderer — tiles miniature multi-variable star/radar
 * polygons (one glyph per series/observation) in a grid.
 *
 * Registered types:
 *   "glyph"
 *
 * ctx.raw shape:
 *   raw.axes      [string]                  axis names (variables)
 *   raw.series    [{name, values:[0..1]}]   one entry per observation
 *   raw.glyphType "star" | "radar" | "bar-glyph"
 *   raw.grid      {cols: N}
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, formatNumber } from "../svgdraw.js";
import { linearScale } from "../scales.js";
import { extent } from "../svgdraw.js";


/* ── per-axis normalisation ──────────────────────────────────────────── */

function _buildAxisScales(raw) {
  /*
   * Build a per-axis linear scale from [data-min, data-max] → [0, 1].
   * Falls back to [0, 1] identity when all values are equal.
   *
   * :returns: Array of scale functions, one per axis.
   */
  const axes   = (raw !== null && raw !== undefined && Array.isArray(raw.axes))
    ? raw.axes
    : []
  const series = (raw !== null && raw !== undefined && Array.isArray(raw.series))
    ? raw.series
    : []
  const scales = []

  for (let a = 0; a < axes.length; a = a + 1) {
    const vals = []
    for (let s = 0; s < series.length; s = s + 1) {
      const v = series[s].values && series[s].values[a]
      if (typeof v === "number") {
        vals.push(v)
      }
    }
    const ext = extent(vals.length > 0 ? vals : [0, 1])
    const lo  = ext[0]
    const hi  = ext[1] === ext[0] ? ext[0] + 1 : ext[1]
    scales.push(linearScale([lo, hi], [0, 1]))
  }

  return scales
}


/* ── single glyph drawing ────────────────────────────────────────────── */

function _drawStarGlyph(cx, cy, r, normValues, axisCount, glyphType, color) {
  /*
   * Draw one star / radar glyph centred at (cx, cy) with outer radius r.
   *
   * :returns: SVGElement.
   */
  const group = svgEl("g", {}, [])

  /* Axis spokes */
  for (let a = 0; a < axisCount; a = a + 1) {
    const angle  = (a / axisCount) * 2 * Math.PI - Math.PI / 2
    const spokeX = cx + r * Math.cos(angle)
    const spokeY = cy + r * Math.sin(angle)
    const spoke = svgEl("line", {
      x1: cx, y1: cy, x2: spokeX, y2: spokeY,
      stroke: "var(--mj-border, #e0e3e9)",
      "stroke-width": 0.5,
      "pointer-events": "none"
    }, [])
    spoke.setAttribute("aria-hidden", "true")
    group.appendChild(spoke)
  }

  if (glyphType === "bar-glyph") {
    /* Radial bars: line from centre outward proportional to value */
    for (let a = 0; a < axisCount; a = a + 1) {
      const angle  = (a / axisCount) * 2 * Math.PI - Math.PI / 2
      const v      = normValues[a] !== undefined ? normValues[a] : 0
      const barR   = v * r
      const barX   = cx + barR * Math.cos(angle)
      const barY   = cy + barR * Math.sin(angle)
      group.appendChild(svgEl("line", {
        x1: cx, y1: cy, x2: barX, y2: barY,
        stroke: color,
        "stroke-width": 3,
        "stroke-linecap": "round",
        "pointer-events": "none"
      }, []))
    }
  } else {
    /* Star / radar polygon */
    const points = []
    for (let a = 0; a < axisCount; a = a + 1) {
      const angle  = (a / axisCount) * 2 * Math.PI - Math.PI / 2
      const v      = normValues[a] !== undefined ? normValues[a] : 0
      const px     = cx + v * r * Math.cos(angle)
      const py     = cy + v * r * Math.sin(angle)
      points.push(`${px.toFixed(2)},${py.toFixed(2)}`)
    }
    const polyEl = svgEl("polygon", {
      points: points.join(" "),
      fill: color,
      "fill-opacity": glyphType === "radar" ? "0.25" : "0",
      stroke: color,
      "stroke-width": 1.5,
      "stroke-linejoin": "round",
      "pointer-events": "none"
    }, [])
    group.appendChild(polyEl)

    /* Axis value dots */
    for (let a = 0; a < axisCount; a = a + 1) {
      const angle  = (a / axisCount) * 2 * Math.PI - Math.PI / 2
      const v      = normValues[a] !== undefined ? normValues[a] : 0
      const px     = cx + v * r * Math.cos(angle)
      const py     = cy + v * r * Math.sin(angle)
      const dotEl  = svgEl("circle", {
        cx: px, cy: py, r: 2,
        fill: color,
        "pointer-events": "none"
      }, [])
      dotEl.setAttribute("aria-hidden", "true")
      group.appendChild(dotEl)
    }
  }

  return group
}


/* ── renderer ─────────────────────────────────────────────────────────── */

export function render(ctx) {
  /*
   * Render a glyph chart (tiled star/radar/bar-glyph observations).
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const raw  = ctx.raw
  const root = svgEl("g", { part: "plot" }, [])

  const axes   = (raw !== null && raw !== undefined && Array.isArray(raw.axes))
    ? raw.axes
    : []
  const series = (raw !== null && raw !== undefined && Array.isArray(raw.series))
    ? raw.series
    : []

  if (axes.length === 0 || series.length === 0) {
    return root
  }

  const glyphType = (raw !== null && raw !== undefined && raw.glyphType)
    ? raw.glyphType
    : ctx.attrs("mode", "radar")
  const gridCols  = (raw !== null && raw !== undefined && raw.grid && raw.grid.cols)
    ? raw.grid.cols
    : Math.ceil(Math.sqrt(series.length))
  const gridRows  = Math.ceil(series.length / gridCols)

  const margin = { top: 8, right: 8, bottom: 8, left: 8 }
  const plotW  = Math.max(ctx.width  - margin.left - margin.right,  10)
  const plotH  = Math.max(ctx.height - margin.top  - margin.bottom, 10)

  const cellW   = plotW / gridCols
  const cellH   = plotH / gridRows
  const glyphR  = Math.min(cellW, cellH) * 0.35
  const labelH  = 14

  const axisScales = _buildAxisScales(raw)

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  for (let s = 0; s < series.length; s = s + 1) {
    const ser    = series[s]
    const col    = s % gridCols
    const row    = Math.floor(s / gridCols)
    const cx     = col * cellW + cellW / 2
    const cy     = row * cellH + cellH / 2 - labelH / 2
    const color  = ctx.colorFor(ser.name)

    /* Normalise values through per-axis scales */
    const normValues = []
    for (let a = 0; a < axes.length; a = a + 1) {
      const raw_v = ser.values && typeof ser.values[a] === "number" ? ser.values[a] : 0
      const norm  = axisScales[a] ? axisScales[a](raw_v) : raw_v
      normValues.push(Math.max(0, Math.min(1, norm)))
    }

    /* Glyph group */
    const glyphG = _drawStarGlyph(cx, cy, glyphR, normValues, axes.length, glyphType, color)

    /* Make the whole glyph interactive */
    const valSummary = axes.map((ax, ai) =>
      `${ax}: ${formatNumber(ser.values && ser.values[ai])}`
    ).join(", ")
    glyphG.setAttribute("part", "glyph")
    glyphG.setAttribute("tabindex", "0")
    glyphG.setAttribute("role", "img")
    glyphG.setAttribute("aria-label", `${ser.name} — ${valSummary}`)
    glyphG.appendChild(svgEl("title", null, `${ser.name}: ${valSummary}`))

    /* Transparent hit-box */
    const hitBox = svgEl("circle", {
      cx: cx, cy: cy, r: glyphR,
      fill: "transparent",
      stroke: "none"
    }, [])
    const capturedName   = ser.name
    const capturedValues = ser.values
    const handler = () => {
      ctx.emit("mj-chart-glyph-click", {
        series: capturedName, values: capturedValues
      })
    }
    hitBox.addEventListener("click", handler)
    glyphG.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault()
        handler()
      }
    })
    glyphG.appendChild(hitBox)
    plot.appendChild(glyphG)

    /* Axis labels around the glyph (first glyph only to reduce clutter) */
    if (s === 0) {
      for (let a = 0; a < axes.length; a = a + 1) {
        const angle  = (a / axes.length) * 2 * Math.PI - Math.PI / 2
        const labelR = glyphR + 10
        const lx     = cx + labelR * Math.cos(angle)
        const ly     = cy + labelR * Math.sin(angle)
        plot.appendChild(svgEl("text", {
          x: lx, y: ly,
          "text-anchor": "middle",
          "dominant-baseline": "middle",
          "font-size": 8,
          fill: "var(--mj-text-muted, #6b7280)",
          "pointer-events": "none"
        }, escapeHtml(axes[a])))
      }
    }

    /* Observation label below glyph */
    plot.appendChild(svgEl("text", {
      x: cx, y: cy + glyphR + labelH,
      "text-anchor": "middle",
      "font-size": 10,
      fill: "var(--mj-text, #14181f)",
      "pointer-events": "none"
    }, escapeHtml(ser.name)))
  }

  return root
}


registerRenderer("glyph", render)
