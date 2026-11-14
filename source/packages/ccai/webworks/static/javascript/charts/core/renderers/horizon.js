/*
 * horizon.js
 *
 * Horizon chart renderer — banded, folded area chart for dense time-series.
 *
 * Registered types:
 *   "horizon" — horizon chart
 *
 * ctx.attrs recognised:
 *   horizon-bands   integer >= 1 (default 3, or the data's "horizon-bands")
 *                   — number of magnitude bands
 *   row-height      integer px — the largest row height; by default the
 *                   rows share the chart height. Rows never overflow it.
 *   diverging       boolean — fold negative values downward in a second
 *                   hue. Default: on when the data holds a negative value.
 *                   diverging="false" draws negative values as zero.
 *   x-scale         see line.js
 *
 * Time runs along x (line.js rules: dates use a time scale). Each series is
 * one row; band b shades the values between b and b+1 band steps, darker
 * for higher bands, so a row reads like an area chart folded into its
 * height. A band key above the rows gives the value range of each shade
 * (it is also published as the chart's legend). Hovering a row shows the x
 * and value under the pointer; each row is a focusable mark whose label
 * gives the series' range and last value. A null value is a gap.
 *
 * Series data: series[].points [{x, y}] or series[].values [] + categories.
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber, areaPath } from "../svgdraw.js";
import { linearScale, seriesColor } from "../scales.js";
import {
  LABEL_FONT_SIZE, textWidth, labelText, nextClipId, activate
} from "./bar.js";
import { booleanOption } from "../chartoptions.js";
import { trendSeries, resolveXAxis, sortedPixels, axisTicks } from "./line.js";

const AXIS_HEIGHT = 22;
const KEY_HEIGHT = 18;


function _bandColor(bandIndex, bandCount, positive) {
  /*
   * The fill of a band: the series hue mixed toward the surface, lightest
   * for the lowest band. Positive values use palette slot 1, negative
   * values slot 2, so both themes keep the contrast.
   */
  const strength = Math.round(30 + (bandIndex / Math.max(bandCount - 1, 1)) * 70)
  const base = seriesColor(positive === true ? 0 : 1)
  const color = `color-mix(in oklab, ${base} ${strength}%, var(--mj-surface, #ffffff))`
  return color
}


function _bandPaths(pixels, bandMax, bandCount, rowH, sign) {
  /*
   * The closed path of every band of one row.
   *
   * :param pixels: [{x, value}] in x order (value null = gap).
   * :param bandMax: The value at the top of the highest band (> 0).
   * :param bandCount: The number of bands.
   * :param rowH: Row height in px.
   * :param sign: 1 for the positive part, -1 for the negative part.
   * :returns: [{ bandIndex, data }].
   */
  const step = bandMax / bandCount
  const bands = []
  for (let b = 0; b < bandCount; b = b + 1) {
    const low = b * step
    const high = (b + 1) * step
    const yScale = linearScale([low, high], [rowH, 0])
    const points = pixels.map((pixel) => {
      if (pixel.value === null) {
        return null
      }
      const magnitude = Math.max(0, sign * pixel.value)
      if (magnitude <= low) {
        return { x: pixel.x, y: rowH }
      }
      return { x: pixel.x, y: yScale(Math.min(magnitude, high)) }
    })
    const data = areaPath(points, rowH)
    if (data !== "") {
      bands.push({ bandIndex: b, data: data })
    }
  }
  return bands
}


export function render(ctx) {
  /*
   * Render a horizon chart.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const model = ctx.model
  const root = svgEl("g", { part: "plot" }, [])

  const list = trendSeries(model)
  if (list.length === 0) {
    return root
  }

  const fromData = model.raw !== null && model.raw !== undefined && model.raw["horizon-bands"] !== undefined
    ? String(model.raw["horizon-bands"]) : "3"
  const bandCount = Math.min(Math.max(1, parseInt(ctx.attrs("horizon-bands", fromData), 10) || 3), 8)

  let bandMax = 0
  let hasNegative = false
  for (let s = 0; s < list.length; s = s + 1) {
    for (let p = 0; p < list[s].points.length; p = p + 1) {
      const value = list[s].points[p].y
      if (value !== null) {
        bandMax = Math.max(bandMax, Math.abs(value))
        hasNegative = hasNegative === true || value < 0
      }
    }
  }
  const diverging = booleanOption(ctx, "diverging", hasNegative)
  if (diverging === false) {
    /* Negative values are drawn as zero, so they do not size the bands. */
    bandMax = 0
    for (let s = 0; s < list.length; s = s + 1) {
      for (let p = 0; p < list[s].points.length; p = p + 1) {
        const value = list[s].points[p].y
        if (value !== null && value > bandMax) {
          bandMax = value
        }
      }
    }
  }

  /* Layout: label column, band key, rows that fit the height, time axis. */
  let labelWidth = 0
  for (let s = 0; s < list.length; s = s + 1) {
    labelWidth = Math.max(labelWidth, textWidth(list[s].name))
  }
  const labelColW = Math.ceil(Math.min(labelWidth, ctx.width * 0.3) + 16)
  const margin = { top: KEY_HEIGHT + 4, right: 16, bottom: AXIS_HEIGHT, left: labelColW }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 40)
  const available = Math.max(ctx.height - margin.top - margin.bottom, list.length * 8)
  const fitted = available / list.length
  const requested = parseInt(ctx.attrs("row-height", ""), 10)
  const rowH = Number.isFinite(requested) === true && requested > 0
    ? Math.max(8, Math.min(requested, fitted))
    : Math.max(8, fitted)
  const rowsH = rowH * list.length

  const xAxis = resolveXAxis(ctx, list, model, [0, plotW], null)
  const frame = { x: xAxis, y: (value) => value }

  const plot = svgEl("g", { transform: `translate(${margin.left},${margin.top})` }, [])
  const chrome = svgEl("g", { "aria-hidden": "true", part: "axes" }, [])
  root.appendChild(plot)
  plot.appendChild(chrome)

  /* Band key, also published as the legend. */
  const legend = []
  const step = bandMax > 0 ? bandMax / bandCount : 0
  if (step > 0) {
    const signs = diverging === true ? [1, -1] : [1]
    const format = (value) => formatNumber(value === 0 ? 0 : value, { maximumFractionDigits: 1 })
    for (let k = 0; k < signs.length; k = k + 1) {
      for (let b = 0; b < bandCount; b = b + 1) {
        const near = format(signs[k] * b * step)
        const far = format(signs[k] * (b + 1) * step)
        const label = signs[k] > 0 ? `${near} – ${far}` : `${far} – ${near}`
        legend.push({ label: label, color: _bandColor(b, bandCount, signs[k] > 0) })
      }
    }
    /* Left to right above the rows; entries that do not fit are left out. */
    let cursor = 0
    for (let index = 0; index < legend.length; index = index + 1) {
      const width = textWidth(legend[index].label, 10) + 22
      if (cursor + width > plotW + margin.right) {
        break
      }
      chrome.appendChild(svgEl("rect", {
        x: cursor, y: -KEY_HEIGHT, width: 10, height: 10, rx: 2, fill: legend[index].color
      }, []))
      chrome.appendChild(svgEl("text", {
        x: cursor + 13, y: -KEY_HEIGHT + 9, "font-size": 10, fill: "var(--mj-text-muted, #5f6673)"
      }, legend[index].label))
      cursor = cursor + width
    }
  }
  ctx.setLegend(legend)

  const readoutLine = svgEl("line", {
    x1: 0, y1: 0, x2: 0, y2: rowsH, stroke: "var(--mj-text, #14181f)", "stroke-width": 1,
    visibility: "hidden", "pointer-events": "none", "aria-hidden": "true"
  }, [])
  const readoutText = svgEl("text", {
    x: 0, y: 0, "font-size": 10, fill: "var(--mj-text, #14181f)",
    stroke: "var(--mj-surface, #ffffff)", "stroke-width": 3, "paint-order": "stroke",
    visibility: "hidden", "pointer-events": "none", "aria-hidden": "true"
  }, "")

  for (let s = 0; s < list.length; s = s + 1) {
    const series = list[s]
    const rowY = s * rowH
    const pixels = sortedPixels(series, frame)

    chrome.appendChild(svgEl("rect", {
      x: 0, y: rowY, width: plotW, height: rowH, fill: "var(--mj-bg-muted, #f1f3f6)"
    }, []))
    chrome.appendChild(labelText({
      x: -6, y: rowY + rowH / 2 + 4, "text-anchor": "end",
      "font-size": LABEL_FONT_SIZE, fill: "var(--mj-text, #14181f)"
    }, series.name, labelColW - 10))

    const clipId = nextClipId("mj-horizon-clip")
    const rowGroup = svgEl("g", {
      transform: `translate(0,${rowY})`, "clip-path": `url(#${clipId})`, part: "horizon-row"
    }, [
      svgEl("defs", null, [svgEl("clipPath", { id: clipId }, [
        svgEl("rect", { x: 0, y: 0, width: plotW, height: rowH }, [])
      ])])
    ])

    if (bandMax > 0) {
      const signs = diverging === true ? [1, -1] : [1]
      for (let k = 0; k < signs.length; k = k + 1) {
        const bands = _bandPaths(pixels, bandMax, bandCount, rowH, signs[k])
        for (let b = 0; b < bands.length; b = b + 1) {
          rowGroup.appendChild(svgEl("path", {
            d: bands[b].data,
            fill: _bandColor(bands[b].bandIndex, bandCount, signs[k] > 0),
            part: signs[k] > 0 ? "horizon-band" : "horizon-band-neg",
            "aria-hidden": "true"
          }, []))
        }
      }
    }

    const known = pixels.filter((pixel) => pixel.value !== null)
    let summary = `${series.name}: no values`
    if (known.length > 0) {
      const valuesOnly = known.map((pixel) => pixel.value)
      summary = `${series.name}: min ${formatNumber(Math.min(...valuesOnly))}, ` +
        `max ${formatNumber(Math.max(...valuesOnly))}, ` +
        `last ${formatNumber(valuesOnly[valuesOnly.length - 1])} (${xAxis.labelOf(known[known.length - 1].point)})`
    }
    const title = svgEl("title", null, summary)
    const hit = svgEl("rect", {
      x: 0, y: 0, width: plotW, height: rowH,
      fill: "transparent",
      tabindex: "0",
      role: "img",
      "aria-label": summary,
      part: "horizon-hit"
    }, [title])
    hit.addEventListener("pointermove", (event) => {
      if (known.length === 0) {
        return
      }
      const box = hit.getBoundingClientRect()
      const scale = box.width > 0 ? plotW / box.width : 1
      const localX = (event.clientX - box.left) * scale
      let nearest = known[0]
      for (let index = 1; index < known.length; index = index + 1) {
        if (Math.abs(known[index].x - localX) < Math.abs(nearest.x - localX)) {
          nearest = known[index]
        }
      }
      const text = `${xAxis.labelOf(nearest.point)}: ${formatNumber(nearest.value)}`
      title.textContent = `${series.name}, ${text}`
      readoutLine.setAttribute("x1", nearest.x.toFixed(2))
      readoutLine.setAttribute("x2", nearest.x.toFixed(2))
      readoutLine.setAttribute("visibility", "visible")
      const anchorEnd = nearest.x > plotW - 80
      readoutText.setAttribute("x", (nearest.x + (anchorEnd === true ? -4 : 4)).toFixed(2))
      readoutText.setAttribute("y", (rowY + Math.min(rowH - 3, 12)).toFixed(2))
      readoutText.setAttribute("text-anchor", anchorEnd === true ? "end" : "start")
      readoutText.textContent = text
      readoutText.setAttribute("visibility", "visible")
    })
    hit.addEventListener("pointerleave", () => {
      readoutLine.setAttribute("visibility", "hidden")
      readoutText.setAttribute("visibility", "hidden")
      title.textContent = summary
    })
    activate(hit, () => {
      ctx.emit("mj-chart-horizon-click", { series: series.name })
    })
    rowGroup.appendChild(hit)

    rowGroup.appendChild(svgEl("line", {
      x1: 0, y1: rowH - 0.5, x2: plotW, y2: rowH - 0.5,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 0.5, "aria-hidden": "true"
    }, []))
    plot.appendChild(rowGroup)
  }

  plot.appendChild(readoutLine)
  plot.appendChild(readoutText)

  /* Time axis below the rows, labels kept inside the drawing. */
  const ticks = axisTicks(xAxis, plotW, 10)
  for (let index = 0; index < ticks.length; index = index + 1) {
    const half = textWidth(ticks[index].label, 10) / 2
    const center = Math.min(Math.max(ticks[index].px, half - margin.left + 2), plotW + margin.right - half - 2)
    chrome.appendChild(svgEl("text", {
      x: center, y: rowsH + 14, "text-anchor": "middle",
      "font-size": 10, fill: "var(--mj-text-muted, #5f6673)"
    }, ticks[index].label))
  }
  chrome.appendChild(svgEl("line", {
    x1: 0, y1: rowsH, x2: plotW, y2: rowsH,
    stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1
  }, []))

  return root
}


registerRenderer("horizon", render)
