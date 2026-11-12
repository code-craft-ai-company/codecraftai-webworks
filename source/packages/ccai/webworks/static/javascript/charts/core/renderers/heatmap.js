/*
 * heatmap.js
 *
 * Heatmap / Correlation-matrix renderer.
 *
 * Registered chart types (ctx.type picks the colour scale):
 *   "heatmap"            — intensity grid (x = categories, y = series rows)
 *                          on a sequential ramp over the value domain
 *   "correlation-matrix" — pairwise correlations on a diverging ramp fixed
 *                          to [-1, 1] (blue positive, red negative)
 *
 * Data shape (same for both types):
 *   categories              column labels (x axis)
 *   series[i].name          row label (y axis)
 *   series[i].values        one value per category; null / non-numeric
 *                           cells are missing and left empty
 *
 * Ramps are mixed from the chart palette and the surface colour, so they
 * follow the theme; value labels use var(--mj-text) on every step. A
 * colour bar on the right maps colours back to values.
 *
 * Relevant ctx.attrs:
 *   scale          "sequential" (heatmap default) | "diverging"
 *   midpoint       centre of the diverging scale (default 0); the ramp
 *                  reaches full colour at the largest |value − midpoint|
 *   value-source   "correlation" — treat a heatmap as a correlation matrix
 *   show-labels    boolean — print the value inside each cell
 *   gap            px between cells (default 1)
 *   corner-radius  cell corner radius in px (default 2)
 *   triangle       "full" (default) | "upper" | "lower"
 *   mark           "rect" (default) | "circle" (circle AREA encodes |value|)
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber } from "../svgdraw.js";
import { bandScale } from "../scales.js";
import {
  isFiniteNumber, axisLayer, fitText, sequentialColor, divergingColor, drawColorRamp,
  activateOnKey, focusableMark, TEXT_COLOR, SURFACE_COLOR
} from "./diststats.js";
import { booleanOption } from "../chartoptions.js";

const RAMP_ROOM = 64;


function _numberAttr(ctx, name, fallback) {
  /*
   * A finite number attribute, else the fallback.
   */
  const value = parseFloat(ctx.attrs(name, ""))
  return isFiniteNumber(value) === true ? value : fallback
}


export function render(ctx) {
  /*
   * Render a heatmap or correlation-matrix chart.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const model = ctx.model
  const isCorrelation = ctx.type === "correlation-matrix" ||
    ctx.attrs("value-source", "") === "correlation"
  const isDiverging = isCorrelation === true || ctx.attrs("scale", "sequential") === "diverging"
  const midpoint = isCorrelation === true ? 0 : _numberAttr(ctx, "midpoint", 0)
  const showLabels = booleanOption(ctx, "show-labels", false)
  const gap = Math.max(_numberAttr(ctx, "gap", 1), 0)
  const cornerRadius = Math.max(_numberAttr(ctx, "corner-radius", 2), 0)
  const triangleMode = ctx.attrs("triangle", "full")
  const markMode = ctx.attrs("mark", "rect")

  const root = svgEl("g", { part: "plot" }, [])
  const categories = Array.isArray(model.categories) === true ? model.categories : []
  const series = Array.isArray(model.series) === true ? model.series : []
  if (categories.length === 0 || series.length === 0) {
    return root
  }

  /* Value domain over the finite cells. */
  let low = Infinity
  let high = -Infinity
  for (let si = 0; si < series.length; si = si + 1) {
    const values = Array.isArray(series[si].values) === true ? series[si].values : []
    for (let ci = 0; ci < categories.length; ci = ci + 1) {
      if (isFiniteNumber(values[ci]) === true) {
        low = Math.min(low, values[ci])
        high = Math.max(high, values[ci])
      }
    }
  }
  if (low === Infinity) {
    return root
  }
  const reach = isCorrelation === true ? 1 : Math.max(Math.abs(high - midpoint), Math.abs(low - midpoint), 1e-12)
  const colorOf = (value) => {
    if (isDiverging === true) {
      return divergingColor((value - midpoint) / reach)
    }
    return sequentialColor(high > low ? (value - low) / (high - low) : 1)
  }

  /* Margins from the label lengths (capped). */
  let rowLongest = 0
  for (let si = 0; si < series.length; si = si + 1) {
    rowLongest = Math.max(rowLongest, String(series[si].name).length)
  }
  let colLongest = 0
  for (let ci = 0; ci < categories.length; ci = ci + 1) {
    colLongest = Math.max(colLongest, String(categories[ci]).length)
  }
  const left = Math.min(Math.max(rowLongest * 6.4 + 14, 40), Math.max(ctx.width * 0.28, 40))
  const right = RAMP_ROOM
  const roughCell = (ctx.width - left - right) / categories.length
  const rotate = colLongest * 6.4 > roughCell - 4
  const bottom = rotate === true ? Math.min(Math.max(colLongest * 4.6 + 20, 32), Math.max(ctx.height * 0.3, 32)) : 28
  const margin = { top: 12, right: right, bottom: bottom, left: left }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  const xScale = bandScale(categories, [0, plotW], 0)
  const yScale = bandScale(series.map((entry) => entry.name), [0, plotH], 0)
  const cellW = xScale.bandwidth()
  const cellH = yScale.step()
  const maxCircleR = Math.max(Math.min(cellW, cellH) / 2 - gap, 1)

  const plot = svgEl("g", { transform: `translate(${margin.left},${margin.top})` }, [])
  root.appendChild(plot)
  const axes = axisLayer(plot)
  const marks = svgEl("g", { part: "marks" }, [])
  plot.appendChild(marks)

  for (let si = 0; si < series.length; si = si + 1) {
    const entry = series[si]
    const values = Array.isArray(entry.values) === true ? entry.values : []
    const rowY = si * cellH

    for (let ci = 0; ci < categories.length; ci = ci + 1) {
      if (triangleMode === "upper" && si > ci) {
        continue
      }
      if (triangleMode === "lower" && si < ci) {
        continue
      }
      const value = values[ci]
      if (isFiniteNumber(value) === false) {
        continue
      }
      const colX = xScale.at(ci)
      const fill = colorOf(value)
      let cell = null
      if (markMode === "circle") {
        /* Circle AREA encodes |value| (radius grows with the square root). */
        const magnitude = isDiverging === true ? Math.abs(value - midpoint) / reach
          : (high > 0 ? Math.abs(value) / Math.max(Math.abs(high), Math.abs(low)) : 0)
        const r = Math.max(maxCircleR * Math.sqrt(Math.min(magnitude, 1)), 1.5)
        cell = svgEl("circle", { cx: colX + cellW / 2, cy: rowY + cellH / 2, r: r, fill: fill }, [])
      } else {
        cell = svgEl("rect", {
          x: colX + gap / 2, y: rowY + gap / 2,
          width: Math.max(cellW - gap, 1), height: Math.max(cellH - gap, 1),
          rx: Math.min(cornerRadius, cellW / 4, cellH / 4), fill: fill
        }, [])
      }
      cell.setAttribute("part", "cell")
      const category = categories[ci]
      focusableMark(cell, `${entry.name}, ${category}: ${formatNumber(value)}`)
      activateOnKey(cell, () => {
        ctx.emit("mj-chart-cell-click", { row: entry.name, col: category, value: value })
      })
      marks.appendChild(cell)

      if (showLabels === true && cellH >= 12) {
        /* Full precision when it fits, one decimal when not, else no label. */
        const fontSize = Math.max(9, Math.min(12, cellH * 0.35))
        let text = isCorrelation === true
          ? formatNumber(value, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
          : formatNumber(value)
        if (text.length * fontSize * 0.6 > cellW - 4) {
          text = formatNumber(value, { maximumFractionDigits: 1 })
        }
        if (text.length * fontSize * 0.6 > cellW - 4) {
          continue
        }
        marks.appendChild(svgEl("text", {
          x: colX + cellW / 2, y: rowY + cellH / 2 + 4, "text-anchor": "middle",
          "font-size": fontSize, "font-weight": 600,
          fill: TEXT_COLOR, stroke: SURFACE_COLOR, "stroke-width": 2.5, "stroke-opacity": 0.6,
          "paint-order": "stroke", "pointer-events": "none", "aria-hidden": "true", part: "cell-label"
        }, text))
      }
    }
  }

  /* Column labels: straight when they fit, rotated otherwise. */
  for (let ci = 0; ci < categories.length; ci = ci + 1) {
    const center = xScale.at(ci) + cellW / 2
    const full = String(categories[ci])
    if (rotate === true) {
      const room = (margin.bottom - 12) / 0.64
      axes.appendChild(svgEl("text", {
        x: 0, y: 0, "text-anchor": "end", "font-size": 11, fill: TEXT_COLOR,
        transform: `translate(${center + 4},${plotH + 12}) rotate(-40)`
      }, fitText(full, room, 11)))
    } else {
      axes.appendChild(svgEl("text", {
        x: center, y: plotH + 16, "text-anchor": "middle", "font-size": 11, fill: TEXT_COLOR
      }, fitText(full, cellW - 2, 11)))
    }
  }
  for (let si = 0; si < series.length; si = si + 1) {
    axes.appendChild(svgEl("text", {
      x: -8, y: si * cellH + cellH / 2 + 4, "text-anchor": "end", "font-size": 11, fill: TEXT_COLOR
    }, fitText(series[si].name, margin.left - 12, 11)))
  }

  /* Colour bar. */
  const rampLength = Math.min(plotH, 180)
  const rampLabels = isDiverging === true
    ? [
      { fraction: 0, text: formatNumber(midpoint - reach, { maximumSignificantDigits: 3 }) },
      { fraction: 0.5, text: formatNumber(midpoint, { maximumSignificantDigits: 3 }) },
      { fraction: 1, text: formatNumber(midpoint + reach, { maximumSignificantDigits: 3 }) }
    ]
    : [
      { fraction: 0, text: formatNumber(low, { maximumSignificantDigits: 3 }) },
      { fraction: 1, text: formatNumber(high, { maximumSignificantDigits: 3 }) }
    ]
  if (isDiverging === false && high > low) {
    rampLabels.splice(1, 0, { fraction: 0.5, text: formatNumber((low + high) / 2, { maximumSignificantDigits: 3 }) })
  }
  drawColorRamp(axes, {
    x: plotW + 12, y: (plotH - rampLength) / 2, length: rampLength, thickness: 10, vertical: true,
    colorAt: (fraction) => isDiverging === true ? divergingColor(fraction * 2 - 1) : sequentialColor(fraction),
    labels: rampLabels
  })

  /* The colour bar explains the colours; rows are not series toggles here. */
  ctx.setLegend([])
  return root
}


registerRenderer("heatmap", render)
registerRenderer("correlation-matrix", render)
