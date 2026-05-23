/*
 * spectrogram.js
 *
 * Frequency-over-time intensity grid renderer.
 *
 * Registered types:
 *   "spectrogram"  - time (x) vs frequency (y) colored-cell intensity grid
 *
 * Renderer contract: render(ctx) -> SVGElement  (a <g> within [0..width]x[0..height])
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, formatNumber } from "../svgdraw.js";
import { linearScale, logScale } from "../scales.js";


/* ── color palette ────────────────────────────────────────────── */

/*
 * 64-stop sequential color palette from near-black through blue to yellow-white
 * (spectral / inferno-like).  Quantizing to 64 stops lets the renderer merge
 * adjacent same-color cells cheaply.
 */
const PALETTE_SIZE = 64

function _buildPalette() {
  const palette = []
  for (let i = 0; i < PALETTE_SIZE; i = i + 1) {
    const t = i / (PALETTE_SIZE - 1)
    /* dark purple -> blue -> cyan -> yellow */
    const r = Math.round(Math.max(0, Math.min(255,
      t < 0.5 ? t * 2 * 100 : 100 + (t - 0.5) * 2 * 155)))
    const g = Math.round(Math.max(0, Math.min(255,
      t < 0.33 ? 0 : t < 0.67 ? (t - 0.33) * 3 * 200 : 200 + (t - 0.67) * 3 * 55)))
    const b = Math.round(Math.max(0, Math.min(255,
      t < 0.33 ? t * 3 * 200 : t < 0.67 ? 200 - (t - 0.33) * 3 * 200 : 0)))
    const hex = "#" +
      r.toString(16).padStart(2, "0") +
      g.toString(16).padStart(2, "0") +
      b.toString(16).padStart(2, "0")
    palette.push(hex)
  }
  return palette
}

const PALETTE = _buildPalette()


function _quantize(normalizedValue) {
  /*
   * Map normalised value [0,1] to a palette index.
   */
  const idx = Math.round(Math.max(0, Math.min(1, normalizedValue)) * (PALETTE_SIZE - 1))
  return idx
}


/* ── axes ─────────────────────────────────────────────────────── */

function _drawXAxis(plot, plotW, plotH, timeAxis, xScale) {
  const tickCount = 6
  const span = timeAxis.end - timeAxis.start
  const step = span / tickCount
  for (let i = 0; i <= tickCount; i = i + 1) {
    const t = timeAxis.start + i * step
    const px = xScale(t)
    plot.appendChild(svgEl("line", {
      x1: px, y1: 0, x2: px, y2: plotH,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    plot.appendChild(svgEl("text", {
      x: px, y: plotH + 14, "text-anchor": "middle",
      "font-size": 10, fill: "var(--mj-text-muted, #6b7280)"
    }, formatNumber(t)))
  }
  return
}

function _drawYAxis(plot, plotW, plotH, freqAxis, yScale) {
  const tickCount = 6
  const span = freqAxis.end - freqAxis.start
  const step = span / tickCount
  for (let i = 0; i <= tickCount; i = i + 1) {
    const f = freqAxis.start + i * step
    const py = yScale(f)
    plot.appendChild(svgEl("line", {
      x1: 0, y1: py, x2: plotW, y2: py,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    plot.appendChild(svgEl("text", {
      x: -6, y: py + 4, "text-anchor": "end",
      "font-size": 10, fill: "var(--mj-text-muted, #6b7280)"
    }, formatNumber(f)))
  }
  return
}


/* ── legend ───────────────────────────────────────────────────── */

function _drawLegend(plot, plotW, plotH, powerMin, powerMax, useLog) {
  const legendW = 12
  const legendH = plotH
  const legendX = plotW + 8

  for (let i = 0; i < PALETTE_SIZE; i = i + 1) {
    const y = legendH - (i / PALETTE_SIZE) * legendH
    const h = legendH / PALETTE_SIZE + 1
    plot.appendChild(svgEl("rect", {
      x: legendX, y: y - h, width: legendW, height: h,
      fill: PALETTE[i]
    }, []))
  }

  const ticks = [0, 0.25, 0.5, 0.75, 1.0]
  for (let i = 0; i < ticks.length; i = i + 1) {
    const py = legendH - ticks[i] * legendH
    const rawVal = powerMin + ticks[i] * (powerMax - powerMin)
    const label = useLog ? formatNumber(rawVal) + " dB" : formatNumber(rawVal)
    plot.appendChild(svgEl("text", {
      x: legendX + legendW + 4, y: py + 4,
      "font-size": 9, fill: "var(--mj-text-muted, #6b7280)"
    }, label))
  }
  return
}


/* ── main renderer ────────────────────────────────────────────── */

export function render(ctx) {
  /*
   * Render a spectrogram intensity grid.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const raw = ctx.raw
  const root = svgEl("g", { part: "plot" }, [])

  if (raw === null || raw === undefined) {
    return root
  }

  const timeAxis = (raw.timeAxis !== null && raw.timeAxis !== undefined)
    ? raw.timeAxis : { start: 0, end: 1, bins: 10 }
  const freqAxis = (raw.freqAxis !== null && raw.freqAxis !== undefined)
    ? raw.freqAxis : { start: 0, end: 1000, bins: 10 }
  const power = (raw.power !== null && raw.power !== undefined) ? raw.power : []

  if (power.length === 0) {
    return root
  }

  const useLog = raw.scale === "log"
  const freqBins = power.length
  const timeBins = power[0].length

  if (freqBins === 0 || timeBins === 0) {
    return root
  }

  const margin = { top: 16, right: 72, bottom: 44, left: 56 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  /* Power extent */
  let powerMin = Infinity
  let powerMax = -Infinity
  for (let f = 0; f < freqBins; f = f + 1) {
    for (let t = 0; t < timeBins; t = t + 1) {
      const val = power[f][t]
      if (typeof val !== "number") { continue }
      const mapped = useLog ? (val > 0 ? 10 * Math.log10(val) : -120) : val
      if (mapped < powerMin) { powerMin = mapped }
      if (mapped > powerMax) { powerMax = mapped }
    }
  }
  if (powerMin === Infinity) { powerMin = 0; powerMax = 1 }
  if (powerMin === powerMax) { powerMax = powerMin + 1 }

  const cellW = plotW / timeBins
  const cellH = plotH / freqBins

  const xScale = linearScale([timeAxis.start, timeAxis.end], [0, plotW])
  const yScale = linearScale([freqAxis.start, freqAxis.end], [plotH, 0])

  /* Labels */
  const meta = (raw.meta !== null && raw.meta !== undefined) ? raw.meta : null
  if (meta !== null) {
    if (meta.xLabel) {
      plot.appendChild(svgEl("text", {
        x: plotW / 2, y: plotH + 30, "text-anchor": "middle",
        "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
      }, escapeHtml(meta.xLabel)))
    }
    if (meta.yLabel) {
      plot.appendChild(svgEl("text", {
        transform: `rotate(-90) translate(${-plotH / 2}, -42)`,
        "text-anchor": "middle",
        "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
      }, escapeHtml(meta.yLabel)))
    }
  }

  _drawXAxis(plot, plotW, plotH, timeAxis, xScale)
  _drawYAxis(plot, plotW, plotH, freqAxis, yScale)

  /* Draw cells -- merge adjacent same-palette-index cells horizontally */
  for (let f = 0; f < freqBins; f = f + 1) {
    const py = plotH - (f + 1) * cellH   /* freq[0] = lowest = bottom */
    let runStart = 0
    let runIdx = -1

    for (let t = 0; t <= timeBins; t = t + 1) {
      let curIdx = -2  /* sentinel for end-of-row flush */
      if (t < timeBins) {
        const val = power[f][t]
        const mapped = useLog
          ? (typeof val === "number" && val > 0 ? 10 * Math.log10(val) : powerMin)
          : (typeof val === "number" ? val : powerMin)
        const norm = (mapped - powerMin) / (powerMax - powerMin)
        curIdx = _quantize(norm)
      }

      if (curIdx !== runIdx) {
        if (runIdx >= 0) {
          const rx = runStart * cellW
          const rw = (t - runStart) * cellW
          const freqVal = freqAxis.start + (f / freqBins) * (freqAxis.end - freqAxis.start)
          const timeVal = timeAxis.start + (runStart / timeBins) * (timeAxis.end - timeAxis.start)
          const label = escapeHtml(
            "t=" + formatNumber(timeVal) + " f=" + formatNumber(freqVal) +
            " p=" + PALETTE[runIdx]
          )
          const cell = svgEl("rect", {
            x: rx.toFixed(1), y: py.toFixed(1),
            width: Math.ceil(rw + 0.5).toFixed(1),
            height: Math.ceil(cellH + 0.5).toFixed(1),
            fill: PALETTE[runIdx],
            part: "cell",
            tabindex: "0",
            role: "img",
            "aria-label": label
          }, [])
          cell.appendChild(svgEl("title", null, label))
          const detail = {
            freqBin: f, timeStart: runStart,
            timeEnd: t - 1, paletteIdx: runIdx
          }
          const handler = () => { ctx.emit("mj-chart-spectrogram-click", detail) }
          cell.addEventListener("click", handler)
          cell.addEventListener("keydown", (event) => {
            if (event.key === "Enter" || event.key === " ") {
              event.preventDefault()
              handler()
            }
          })
          plot.appendChild(cell)
        }
        runStart = t
        runIdx = curIdx
      }
    }
  }

  _drawLegend(plot, plotW, plotH, powerMin, powerMax, useLog)

  return root
}


registerRenderer("spectrogram", render)
