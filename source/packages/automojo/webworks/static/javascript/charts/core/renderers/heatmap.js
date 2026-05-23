/*
 * heatmap.js
 *
 * Heatmap / Correlation-matrix renderer.
 *
 * Registered chart types:
 *   "heatmap"            — generic intensity grid (x=categories, y=series rows)
 *   "correlation-matrix" — symmetric pairwise correlation grid with a
 *                          diverging color scale centered at 0
 *
 * Data shape (same for both types):
 *   model.categories        — column labels (x axis)
 *   model.series[i].name    — row label (y axis)
 *   model.series[i].values  — one numeric value per category
 *
 * Diverging scale is used automatically when type="correlation-matrix" or
 * when the controller carries scale="diverging".
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, formatNumber, extent } from "../svgdraw.js";
import { bandScale, linearScale } from "../scales.js";


/* Sequential single-hue ramp (light → dark) via design tokens. */
const HEAT_RAMP = [
  "var(--mj-chart-heat-1, #eff6ff)",
  "var(--mj-chart-heat-2, #bfdbfe)",
  "var(--mj-chart-heat-3, #93c5fd)",
  "var(--mj-chart-heat-4, #60a5fa)",
  "var(--mj-chart-heat-5, #3b82f6)",
  "var(--mj-chart-heat-6, #2563eb)",
  "var(--mj-chart-heat-7, #1d4ed8)",
  "var(--mj-chart-heat-8, #1e40af)"
]

/* Diverging ramp (negative = red, neutral = white, positive = blue). */
const DIV_NEG = [
  "var(--mj-chart-div-neg-5, #7f1d1d)",
  "var(--mj-chart-div-neg-4, #b91c1c)",
  "var(--mj-chart-div-neg-3, #ef4444)",
  "var(--mj-chart-div-neg-2, #fca5a5)",
  "var(--mj-chart-div-neg-1, #fee2e2)"
]
const DIV_MID = "var(--mj-chart-div-mid, #f8fafc)"
const DIV_POS = [
  "var(--mj-chart-div-pos-1, #dbeafe)",
  "var(--mj-chart-div-pos-2, #93c5fd)",
  "var(--mj-chart-div-pos-3, #3b82f6)",
  "var(--mj-chart-div-pos-4, #1d4ed8)",
  "var(--mj-chart-div-pos-5, #1e3a8a)"
]


function _seqColor(value, min, max) {
  /*
   * Map a value in [min, max] to a sequential heat-ramp color.
   *
   * :param value: The numeric cell value.
   * :param min: Domain minimum.
   * :param max: Domain maximum.
   * :returns: A CSS color string.
   */
  const span = max - min
  if (span === 0) {
    return HEAT_RAMP[0]
  }
  const fraction = Math.max(0, Math.min(1, (value - min) / span))
  const index = Math.min(
    HEAT_RAMP.length - 1,
    Math.floor(fraction * HEAT_RAMP.length)
  )
  return HEAT_RAMP[index]
}


function _divColor(value) {
  /*
   * Map a correlation value in [-1, 1] to a diverging color.
   *
   * :param value: The correlation coefficient.
   * :returns: A CSS color string.
   */
  const clamped = Math.max(-1, Math.min(1, value))
  if (Math.abs(clamped) < 0.02) {
    return DIV_MID
  }
  if (clamped < 0) {
    const fraction = Math.min(1, Math.abs(clamped))
    const index = Math.min(
      DIV_NEG.length - 1,
      Math.floor(fraction * DIV_NEG.length)
    )
    return DIV_NEG[index]
  }
  const fraction = Math.min(1, clamped)
  const index = Math.min(
    DIV_POS.length - 1,
    Math.floor(fraction * DIV_POS.length)
  )
  return DIV_POS[index]
}


export function render(ctx) {
  /*
   * Render a heatmap or correlation-matrix chart.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const model = ctx.model
  const chartType = ctx.attrs("type", "heatmap")
  const isCorrelation = chartType === "correlation-matrix" ||
    ctx.attrs("value-source", "") === "correlation"
  const scaleMode = ctx.attrs("scale", isCorrelation ? "diverging" : "sequential")
  const isDiverging = scaleMode === "diverging" || isCorrelation === true
  const showLabels = ctx.attrs("show-labels", "false") === "true"
  const gap = Number(ctx.attrs("gap", "1"))
  const cornerRadius = Number(ctx.attrs("corner-radius", "2"))
  const triangleMode = ctx.attrs("triangle", "full")
  const markMode = ctx.attrs("mark", "rect")

  const root = svgEl("g", { part: "plot" }, [])

  const categories = model.categories
  const series = model.series
  if (categories === null || categories === undefined || categories.length === 0) {
    return root
  }
  if (series === null || series === undefined || series.length === 0) {
    return root
  }

  const margin = { top: 16, right: 16, bottom: 72, left: 80 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  /* Band scales for x (categories) and y (series rows). */
  const xScale = bandScale(categories, [0, plotW], 0)
  const rowNames = series.map((ser) => ser.name)
  const yScale = bandScale(rowNames, [0, plotH], 0)

  const cellW = xScale.bandwidth()
  const cellH = yScale.bandwidth()

  /* Compute domain for sequential scale. */
  let allValues = []
  for (let s = 0; s < series.length; s = s + 1) {
    const vals = series[s].values
    if (vals === null || vals === undefined) {
      continue
    }
    for (let v = 0; v < vals.length; v = v + 1) {
      const val = vals[v]
      if (typeof val === "number" && Number.isNaN(val) === false) {
        allValues.push(val)
      }
    }
  }
  const valueDomain = extent(allValues)

  /* Circle size scale for mark="circle" mode. */
  const maxCircleR = Math.min(cellW, cellH) / 2 - gap

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  /* Draw cells. */
  for (let s = 0; s < series.length; s = s + 1) {
    const ser = series[s]
    const vals = ser.values
    if (vals === null || vals === undefined) {
      continue
    }
    const rowY = yScale(ser.name)

    for (let c = 0; c < categories.length; c = c + 1) {
      /* Respect triangle mode for correlation matrices. */
      if (triangleMode === "upper" && s > c) {
        continue
      }
      if (triangleMode === "lower" && s < c) {
        continue
      }

      const value = vals[c]
      if (value === null || value === undefined || Number.isNaN(value) === true) {
        continue
      }

      const colX = xScale(categories[c])
      const fillColor = isDiverging === true
        ? _divColor(value)
        : _seqColor(value, valueDomain[0], valueDomain[1])

      let cellEl = null

      if (markMode === "circle") {
        /* Circle whose area encodes |value|. */
        const absVal = Math.abs(value)
        const domainMax = isDiverging === true ? 1 : valueDomain[1]
        const fraction = domainMax !== 0 ? Math.min(1, absVal / domainMax) : 0
        const r = Math.max(2, maxCircleR * fraction)
        cellEl = svgEl("circle", {
          cx: colX + cellW / 2,
          cy: rowY + cellH / 2,
          r: r,
          fill: fillColor
        }, [])
      } else {
        cellEl = svgEl("rect", {
          x: colX + gap / 2,
          y: rowY + gap / 2,
          width: Math.max(cellW - gap, 1),
          height: Math.max(cellH - gap, 1),
          rx: cornerRadius,
          fill: fillColor
        }, [])
      }

      cellEl.setAttribute("part", "cell")
      cellEl.setAttribute("tabindex", "0")
      cellEl.setAttribute("role", "img")
      const ariaLabel = `${escapeHtml(ser.name)}, ${escapeHtml(categories[c])}: ${formatNumber(value)}`
      cellEl.setAttribute("aria-label", ariaLabel)
      cellEl.appendChild(svgEl("title", null,
        `${ser.name} × ${categories[c]}: ${formatNumber(value)}`))

      const handler = () => {
        ctx.emit("mj-chart-cell-click", {
          row: ser.name,
          col: categories[c],
          value: value
        })
      }
      cellEl.addEventListener("click", handler)
      cellEl.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault()
          handler()
        }
      })
      plot.appendChild(cellEl)

      /* Optional value label inside cell. */
      if (showLabels === true) {
        const labelText = isDiverging === true
          ? value.toFixed(2)
          : formatNumber(value)
        const textColor = Math.abs(value) > (isDiverging ? 0.5 : (valueDomain[1] * 0.6))
          ? "var(--mj-text-on-strong, #ffffff)"
          : "var(--mj-text, #14181f)"
        plot.appendChild(svgEl("text", {
          x: colX + cellW / 2,
          y: rowY + cellH / 2 + 4,
          "text-anchor": "middle",
          "font-size": Math.max(9, Math.min(12, cellH * 0.35)),
          fill: textColor,
          "pointer-events": "none"
        }, escapeHtml(labelText)))
      }
    }
  }

  /* X-axis category labels. */
  for (let c = 0; c < categories.length; c = c + 1) {
    const colX = xScale(categories[c])
    plot.appendChild(svgEl("text", {
      x: colX + cellW / 2,
      y: plotH + 16,
      "text-anchor": "middle",
      "font-size": 11,
      fill: "var(--mj-text, #14181f)"
    }, escapeHtml(categories[c])))
  }

  /* Y-axis row labels. */
  for (let s = 0; s < series.length; s = s + 1) {
    const rowY = yScale(series[s].name)
    plot.appendChild(svgEl("text", {
      x: -8,
      y: rowY + cellH / 2 + 4,
      "text-anchor": "end",
      "font-size": 11,
      fill: "var(--mj-text, #14181f)"
    }, escapeHtml(series[s].name)))
  }

  return root
}


registerRenderer("heatmap", render)
registerRenderer("correlation-matrix", render)
