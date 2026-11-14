/*
 * spectrogram.js
 *
 * Frequency-over-time intensity grid renderer.
 *
 * Registered types:
 *   "spectrogram"  - time (x) vs frequency (y) colored-cell intensity grid
 *
 * Data:
 *   {
 *     timeAxis: { start, end, bins },        (start/end default to 0 / bins)
 *     freqAxis: { start, end, bins, logScale? },
 *     power:    [[...time bins...], ...],    (power[freqBin][timeBin])
 *     scale:    "linear" | "log",            ("log" maps power to 10*log10 dB)
 *     colormap: "sequential" | "grayscale",
 *     range:    [min, max]                   (optional colour range, in the
 *                                             displayed unit: dB for "log")
 *   }
 *   Row 0 of `power` is the lowest frequency. A null or non-numeric cell is
 *   a gap. With scale "log", cells <= 0 have no dB value: they are drawn at
 *   the floor of the scale and do not stretch it; data that is already in
 *   dB (no positive cell) is shown as given.
 *
 * Interaction: the grid is one focusable mark. The pointer position names
 * the cell under it (tooltip), Arrow keys move a cell cursor, and click /
 * Enter / Space emit mj-chart-spectrogram-click
 *   { timeBin, freqBin, time, frequency, power, value }.
 * Colours are quantised to 64 shades and equal neighbours in a row are
 * merged into one <rect>, which keeps large spectrograms light.
 *
 * Renderer contract: render(ctx) -> SVGElement  (a <g> within [0..width]x[0..height])
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber } from "../svgdraw.js";
import { linearScale, logScale, niceTicks } from "../scales.js";

const PALETTE_SIZE = 64;

/* Sequential ramps built from theme tokens, low to high. */
const COLORMAPS = {
  sequential: [
    "color-mix(in oklab, var(--mj-accent, #2563eb) 10%, var(--mj-surface, #ffffff))",
    "color-mix(in oklab, var(--mj-accent, #2563eb) 55%, var(--mj-surface, #ffffff))",
    "var(--mj-accent, #2563eb)",
    "color-mix(in oklab, var(--mj-accent, #2563eb) 45%, var(--mj-text, #14181f))"
  ],
  grayscale: [
    "color-mix(in oklab, var(--mj-text, #14181f) 6%, var(--mj-surface, #ffffff))",
    "color-mix(in oklab, var(--mj-text, #14181f) 50%, var(--mj-surface, #ffffff))",
    "var(--mj-text, #14181f)"
  ]
};

const MAX_TABLE_COLUMNS = 24;

/* Grids with more cells than this are painted as one raster image. */
const RASTER_THRESHOLD = 6000;


/* ── helpers ──────────────────────────────────────────────────── */

function _isNumber(value) {
  /*
   * True for a finite number.
   */
  const numeric = typeof value === "number" && Number.isFinite(value) === true
  return numeric
}


function _buildPalette(stops) {
  /*
   * PALETTE_SIZE colour strings interpolated along the ramp stops.
   */
  const palette = []
  for (let i = 0; i < PALETTE_SIZE; i = i + 1) {
    const t = i / (PALETTE_SIZE - 1)
    const scaled = t * (stops.length - 1)
    const lo = Math.min(Math.floor(scaled), stops.length - 2)
    const share = Math.round((scaled - lo) * 100)
    let color = stops[lo]
    if (share >= 100) {
      color = stops[lo + 1]
    } else if (share > 0) {
      color = `color-mix(in oklab, ${stops[lo + 1]} ${share}%, ${stops[lo]})`
    }
    palette.push(color)
  }
  return palette
}

const PALETTES = {
  sequential: _buildPalette(COLORMAPS.sequential),
  grayscale: _buildPalette(COLORMAPS.grayscale)
};


function _readAxis(axis, bins) {
  /*
   * An axis { start, end, bins, logScale } with defaults: start 0, end the
   * bin count, so a missing start or end never yields NaN.
   */
  const source = axis !== null && typeof axis === "object" ? axis : {}
  const start = _isNumber(source.start) === true ? source.start : 0
  let end = _isNumber(source.end) === true ? source.end : start + bins
  if (end === start) {
    end = start + 1
  }
  const result = { start: start, end: end, bins: bins, logScale: source.logScale === true }
  return result
}


/* Blob URLs of the raster images, keyed by URL, so stale ones are released. */
const RASTER_URLS = new Map();


function _releaseRasterUrls() {
  /*
   * Revoke the blob URL of every raster image no longer in the document.
   */
  const urls = Array.from(RASTER_URLS.keys())
  for (let index = 0; index < urls.length; index = index + 1) {
    const image = RASTER_URLS.get(urls[index])
    if (image.isConnected === false) {
      URL.revokeObjectURL(urls[index])
      RASTER_URLS.delete(urls[index])
    }
  }
  return
}


export function paintRaster(image, holder, palette, layout) {
  /*
   * Paint a large grid into a canvas and show it as the image's data URL.
   *
   * The palette holds theme-token colours, which only resolve once the
   * drawing is in the document, so the paint runs in a microtask after the
   * render (before the frame is painted): a probe element inside the
   * chart resolves each palette colour through the chart's own theme. The
   * image is shown as a blob URL once the canvas is encoded.
   *
   * Exported for the other raster layers of the library (geo-heatmap).
   *
   * :param image: The SVG <image> that shows the raster.
   * :param holder: An element of the drawing that holds the image.
   * :param palette: CSS colour strings (theme tokens allowed).
   * :param layout: { columns, rows, indexAt(column, row) -> palette index,
   *     or -1 for a transparent pixel }
   */
  let attempts = 0
  const paint = () => {
    if (holder.isConnected === false) {
      attempts = attempts + 1
      if (attempts < 30) {
        requestAnimationFrame(paint)
      }
      return
    }
    const probe = svgEl("rect", { width: 0, height: 0 }, [])
    holder.appendChild(probe)
    const resolved = []
    for (let i = 0; i < palette.length; i = i + 1) {
      probe.setAttribute("fill", palette[i])
      resolved.push(getComputedStyle(probe).fill)
    }
    probe.remove()

    const canvas = document.createElement("canvas")
    canvas.width = layout.columns
    canvas.height = layout.rows
    const context = canvas.getContext("2d")
    if (context === null) {
      return
    }
    for (let y = 0; y < layout.rows; y = y + 1) {
      for (let x = 0; x < layout.columns; x = x + 1) {
        const index = layout.indexAt(x, y)
        if (index < 0) {
          continue
        }
        context.fillStyle = resolved[index]
        context.fillRect(x, y, 1, 1)
      }
    }
    /*
     * A blob URL (not a data URL) keeps the attribute short; the URLs of
     * images that have left the document are released here.
     */
    canvas.toBlob((blob) => {
      if (blob === null) {
        return
      }
      _releaseRasterUrls()
      const url = URL.createObjectURL(blob)
      RASTER_URLS.set(url, image)
      image.setAttribute("href", url)
    })
    return
  }
  Promise.resolve().then(paint)
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
  const raw = ctx.raw !== null && ctx.raw !== undefined ? ctx.raw : {}
  const root = svgEl("g", { part: "plot" }, [])

  /* Rows: a missing or non-array row is a row of gaps; ragged rows pad. */
  const power = Array.isArray(raw.power) === true ? raw.power : []
  const freqBins = power.length
  let timeBins = 0
  for (let f = 0; f < freqBins; f = f + 1) {
    if (Array.isArray(power[f]) === true) {
      timeBins = Math.max(timeBins, power[f].length)
    }
  }
  if (freqBins === 0 || timeBins === 0) {
    return root
  }
  const cellAt = (f, t) => {
    const row = power[f]
    const value = Array.isArray(row) === true ? row[t] : null
    return _isNumber(value) === true ? value : null
  }

  const timeAxis = _readAxis(raw.timeAxis, timeBins)
  const freqAxis = _readAxis(raw.freqAxis, freqBins)
  const palette = raw.colormap === "grayscale" ? PALETTES.grayscale : PALETTES.sequential

  /* Display values: dB for scale "log" when the data has positive power. */
  let anyPositive = false
  for (let f = 0; f < freqBins && anyPositive === false; f = f + 1) {
    for (let t = 0; t < timeBins; t = t + 1) {
      const value = cellAt(f, t)
      if (value !== null && value > 0) {
        anyPositive = true
        break
      }
    }
  }
  const toDb = raw.scale === "log" && anyPositive === true
  const unit = raw.scale === "log" ? " dB" : ""
  const displayOf = (value) => {
    if (value === null) {
      return null
    }
    if (toDb === true) {
      return value > 0 ? 10 * Math.log10(value) : null
    }
    return value
  }

  let powerMin = Infinity
  let powerMax = -Infinity
  for (let f = 0; f < freqBins; f = f + 1) {
    for (let t = 0; t < timeBins; t = t + 1) {
      const shown = displayOf(cellAt(f, t))
      if (shown !== null) {
        powerMin = Math.min(powerMin, shown)
        powerMax = Math.max(powerMax, shown)
      }
    }
  }
  if (Array.isArray(raw.range) === true && _isNumber(raw.range[0]) === true &&
      _isNumber(raw.range[1]) === true && raw.range[0] !== raw.range[1]) {
    powerMin = Math.min(raw.range[0], raw.range[1])
    powerMax = Math.max(raw.range[0], raw.range[1])
  }
  if (powerMin === Infinity) {
    powerMin = 0
    powerMax = 1
  }
  if (powerMin === powerMax) {
    powerMin = powerMin - 0.5
    powerMax = powerMax + 0.5
  }
  const paletteIndexOf = (value) => {
    /* A cell without a display value (<= 0 on a dB scale) sits at the floor. */
    const shown = displayOf(value)
    const norm = shown === null ? 0 : (shown - powerMin) / (powerMax - powerMin)
    return Math.round(Math.max(0, Math.min(1, norm)) * (PALETTE_SIZE - 1))
  }

  const legendSpace = ctx.width > 300 ? 72 : 44
  const margin = { top: 16, right: legendSpace, bottom: 44, left: 60 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  const xScale = linearScale([timeAxis.start, timeAxis.end], [0, plotW])
  const binWidth = (freqAxis.end - freqAxis.start) / freqBins
  let yScale = null
  if (freqAxis.logScale === true) {
    const low = freqAxis.start > 0 ? freqAxis.start : Math.abs(binWidth) / 2
    yScale = logScale([low, freqAxis.end], [plotH, 0])
  } else {
    yScale = linearScale([freqAxis.start, freqAxis.end], [plotH, 0])
  }
  const timeOfBin = (t) => timeAxis.start + (t / timeBins) * (timeAxis.end - timeAxis.start)
  const freqEdge = (f) => freqAxis.start + f * binWidth
  const rowTop = (f) => Math.min(yScale(freqEdge(f)), yScale(freqEdge(f + 1)))
  const rowBottom = (f) => Math.max(yScale(freqEdge(f)), yScale(freqEdge(f + 1)))

  /*
   * Cells: a small grid is drawn as rects (equal quantised neighbours in a
   * row merged into one); a large one is painted into a raster image, one
   * canvas pixel per time bin, so the element count stays bounded.
   */
  const cells = svgEl("g", { part: "cells", "aria-hidden": "true" }, [])
  if (timeBins * freqBins > RASTER_THRESHOLD) {
    const image = svgEl("image", {
      x: 0, y: 0, width: plotW, height: plotH,
      preserveAspectRatio: "none",
      style: "image-rendering: pixelated",
      part: "raster"
    }, [])
    cells.appendChild(image)
    const rasterRows = Math.max(Math.min(Math.round(plotH), 2048), 1)
    const pixelHeight = plotH / rasterRows
    /* The frequency bin of each raster row (log axes have uneven rows). */
    const binOfRow = []
    for (let y = 0; y < rasterRows; y = y + 1) {
      const centre = (y + 0.5) * pixelHeight
      let bin = -1
      for (let f = 0; f < freqBins; f = f + 1) {
        if (centre >= rowTop(f) && centre < rowBottom(f)) {
          bin = f
          break
        }
      }
      binOfRow.push(bin)
    }
    paintRaster(image, cells, palette, {
      columns: timeBins,
      rows: rasterRows,
      indexAt: (t, y) => {
        const f = binOfRow[y]
        const value = f < 0 ? null : cellAt(f, t)
        return value === null ? -1 : paletteIndexOf(value)
      }
    })
  } else {
    for (let f = 0; f < freqBins; f = f + 1) {
      const top = rowTop(f)
      const height = Math.max(rowBottom(f) - top, 0.5)
      let runStart = 0
      let runIdx = -1
      for (let t = 0; t <= timeBins; t = t + 1) {
        let curIdx = -1
        if (t < timeBins) {
          const value = cellAt(f, t)
          curIdx = value === null ? -1 : paletteIndexOf(value)
        }
        if (curIdx !== runIdx || t === timeBins) {
          if (runIdx >= 0) {
            const x0 = xScale(timeOfBin(runStart))
            const x1 = xScale(timeOfBin(t))
            cells.appendChild(svgEl("rect", {
              x: x0.toFixed(2), y: top.toFixed(2),
              width: (x1 - x0 + 0.4).toFixed(2),
              height: (height + 0.4).toFixed(2),
              fill: palette[runIdx],
              part: "cell"
            }, []))
          }
          runStart = t
          runIdx = curIdx
        }
      }
    }
  }
  plot.appendChild(cells)

  /* Axes */
  const axes = svgEl("g", { "aria-hidden": "true", part: "axes" }, [])
  const xTicks = niceTicks(timeAxis.start, timeAxis.end, Math.max(Math.floor(plotW / 90), 2))
  for (let i = 0; i < xTicks.length; i = i + 1) {
    const px = xScale(xTicks[i])
    axes.appendChild(svgEl("line", {
      x1: px, y1: plotH, x2: px, y2: plotH + 4,
      stroke: "var(--mj-border-strong, #878e9c)", "stroke-width": 1
    }, []))
    axes.appendChild(svgEl("text", {
      x: px, y: plotH + 15, "text-anchor": "middle",
      "font-size": 10, fill: "var(--mj-text-muted, #6b7280)"
    }, formatNumber(xTicks[i])))
  }
  const yTicks = freqAxis.logScale === true
    ? yScale.ticks(5)
    : niceTicks(freqAxis.start, freqAxis.end, Math.max(Math.floor(plotH / 40), 2))
  for (let i = 0; i < yTicks.length; i = i + 1) {
    const py = yScale(yTicks[i])
    if (py < -0.5 || py > plotH + 0.5) {
      continue
    }
    axes.appendChild(svgEl("line", {
      x1: -4, y1: py, x2: 0, y2: py,
      stroke: "var(--mj-border-strong, #878e9c)", "stroke-width": 1
    }, []))
    axes.appendChild(svgEl("text", {
      x: -7, y: py + 4, "text-anchor": "end",
      "font-size": 10, fill: "var(--mj-text-muted, #6b7280)"
    }, formatNumber(yTicks[i])))
  }
  const meta = ctx.model.meta
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
  plot.appendChild(axes)

  /* Colour bar with nice ticks. */
  const legend = svgEl("g", { "aria-hidden": "true", part: "legend" }, [])
  const legendX = plotW + 10
  for (let i = 0; i < PALETTE_SIZE; i = i + 1) {
    const h = plotH / PALETTE_SIZE
    legend.appendChild(svgEl("rect", {
      x: legendX, y: plotH - (i + 1) * h, width: 12, height: h + 0.5,
      fill: palette[i]
    }, []))
  }
  const barScale = linearScale([powerMin, powerMax], [plotH, 0])
  const barTicks = niceTicks(powerMin, powerMax, 5)
  for (let i = 0; i < barTicks.length; i = i + 1) {
    const py = barScale(barTicks[i])
    if (py < -0.5 || py > plotH + 0.5) {
      continue
    }
    legend.appendChild(svgEl("text", {
      x: legendX + 16, y: py + 3,
      "font-size": 9, fill: "var(--mj-text-muted, #6b7280)"
    }, formatNumber(barTicks[i]) + unit))
  }
  plot.appendChild(legend)

  /* One focusable mark over the grid, with a cell cursor. */
  const describe = (f, t) => {
    const value = cellAt(f, t)
    const shown = displayOf(value)
    const t0 = timeOfBin(t)
    const t1 = timeOfBin(t + 1)
    let text = `t ${formatNumber(t0, { maximumFractionDigits: 3 })}–${formatNumber(t1, { maximumFractionDigits: 3 })}, ` +
      `f ${formatNumber(freqEdge(f), { maximumFractionDigits: 1 })}–${formatNumber(freqEdge(f + 1), { maximumFractionDigits: 1 })}: `
    if (value === null) {
      text = text + "no data"
    } else if (toDb === true) {
      text = text + `power ${formatNumber(value, { maximumSignificantDigits: 4 })}` +
        (shown !== null ? ` (${formatNumber(shown, { maximumFractionDigits: 1 })} dB)` : " (no dB value)")
    } else {
      text = text + `${formatNumber(value, { maximumSignificantDigits: 4 })}${unit}`
    }
    return text
  }
  const summary = `${ctx.label}: ${timeBins} time bins by ${freqBins} frequency bins, ` +
    `${formatNumber(powerMin, { maximumFractionDigits: 1 })} to ${formatNumber(powerMax, { maximumFractionDigits: 1 })}${unit}. ` +
    "Use the arrow keys to read cells."
  const tooltip = svgEl("title", null, summary)
  const surface = svgEl("rect", {
    x: 0, y: 0, width: plotW, height: plotH,
    fill: "transparent",
    part: "grid-surface",
    tabindex: "0",
    role: "img",
    "aria-label": summary
  }, [tooltip])
  const cursor = svgEl("rect", {
    x: 0, y: 0, width: 0, height: 0, fill: "none",
    stroke: "var(--mj-text, #14181f)", "stroke-width": 1.5,
    visibility: "hidden", "pointer-events": "none", part: "cursor"
  }, [])

  const state = { f: freqBins - 1, t: 0 }
  const showCursor = () => {
    const x0 = xScale(timeOfBin(state.t))
    const x1 = xScale(timeOfBin(state.t + 1))
    cursor.setAttribute("x", x0.toFixed(2))
    cursor.setAttribute("y", rowTop(state.f).toFixed(2))
    cursor.setAttribute("width", Math.max(x1 - x0, 1).toFixed(2))
    cursor.setAttribute("height", Math.max(rowBottom(state.f) - rowTop(state.f), 1).toFixed(2))
    cursor.setAttribute("visibility", "visible")
    const text = describe(state.f, state.t)
    surface.setAttribute("aria-label", text)
    tooltip.textContent = text
    return
  }
  const cellFromEvent = (event) => {
    const matrix = surface.getScreenCTM()
    if (matrix === null) {
      return null
    }
    const local = new DOMPoint(event.clientX, event.clientY).matrixTransform(matrix.inverse())
    const time = xScale.invert(local.x)
    const t = Math.floor(((time - timeAxis.start) / (timeAxis.end - timeAxis.start)) * timeBins)
    let f = -1
    for (let row = 0; row < freqBins; row = row + 1) {
      if (local.y >= rowTop(row) - 0.01 && local.y <= rowBottom(row) + 0.01) {
        f = row
        break
      }
    }
    if (t < 0 || t >= timeBins || f < 0) {
      return null
    }
    return { f: f, t: t }
  }
  const emitCell = () => {
    const value = cellAt(state.f, state.t)
    ctx.emit("mj-chart-spectrogram-click", {
      timeBin: state.t,
      freqBin: state.f,
      time: timeOfBin(state.t),
      frequency: freqEdge(state.f),
      power: value,
      value: displayOf(value)
    })
    return
  }

  surface.addEventListener("pointermove", (event) => {
    const cell = cellFromEvent(event)
    if (cell !== null) {
      tooltip.textContent = describe(cell.f, cell.t)
    }
  })
  surface.addEventListener("click", (event) => {
    const cell = cellFromEvent(event)
    if (cell !== null) {
      state.f = cell.f
      state.t = cell.t
      showCursor()
      emitCell()
    }
  })
  surface.addEventListener("focus", () => { showCursor() })
  surface.addEventListener("blur", () => { cursor.setAttribute("visibility", "hidden") })
  surface.addEventListener("keydown", (event) => {
    let handled = true
    if (event.key === "ArrowRight") {
      state.t = Math.min(state.t + 1, timeBins - 1)
    } else if (event.key === "ArrowLeft") {
      state.t = Math.max(state.t - 1, 0)
    } else if (event.key === "ArrowUp") {
      state.f = Math.min(state.f + 1, freqBins - 1)
    } else if (event.key === "ArrowDown") {
      state.f = Math.max(state.f - 1, 0)
    } else if (event.key === "Home") {
      state.t = 0
    } else if (event.key === "End") {
      state.t = timeBins - 1
    } else if (event.key === "Enter" || event.key === " ") {
      emitCell()
    } else {
      handled = false
    }
    if (handled === true) {
      event.preventDefault()
      showCursor()
    }
  })
  plot.appendChild(surface)
  plot.appendChild(cursor)

  /* Accessible table: the grid when narrow, else a per-frequency summary. */
  const valueCell = (value) => (value === null ? "" : value)
  if (timeBins <= MAX_TABLE_COLUMNS) {
    const columns = ["Frequency"]
    for (let t = 0; t < timeBins; t = t + 1) {
      columns.push(`t ${formatNumber(timeOfBin(t), { maximumFractionDigits: 3 })}`)
    }
    const rows = []
    for (let f = freqBins - 1; f >= 0; f = f - 1) {
      const record = [formatNumber(freqEdge(f), { maximumFractionDigits: 1 })]
      for (let t = 0; t < timeBins; t = t + 1) {
        record.push(valueCell(cellAt(f, t)))
      }
      rows.push(record)
    }
    ctx.setTable({ columns: columns, rows: rows, caption: "Power by frequency (rows) and time (columns)" })
  } else {
    const rows = []
    for (let f = freqBins - 1; f >= 0; f = f - 1) {
      let min = null
      let max = null
      let sum = 0
      let count = 0
      let peakTime = null
      for (let t = 0; t < timeBins; t = t + 1) {
        const value = cellAt(f, t)
        if (value === null) {
          continue
        }
        if (min === null || value < min) {
          min = value
        }
        if (max === null || value > max) {
          max = value
          peakTime = timeOfBin(t)
        }
        sum = sum + value
        count = count + 1
      }
      rows.push([formatNumber(freqEdge(f), { maximumFractionDigits: 1 }), valueCell(min),
        count > 0 ? sum / count : "", valueCell(max), valueCell(peakTime)])
    }
    ctx.setTable({
      columns: ["Frequency", "Min power", "Mean power", "Max power", "Time of max"],
      rows: rows,
      caption: "Power per frequency bin"
    })
  }
  return root
}


registerRenderer("spectrogram", render, { legend: "none" })
