/*
 * pixel.js
 *
 * Pixel chart renderer — dense discrete value grid where each cell
 * encodes one observation or aggregate bin via colour.
 *
 * Registered types:
 *   "pixel"
 *
 * ctx.raw shape:
 *   raw.xDimension    label for the x axis
 *   raw.yDimension    label for the y axis
 *   raw.valueMeasure  name of the encoded value (tooltips, table, key)
 *   raw.xCategories   optional labels of the x positions (index order)
 *   raw.yCategories   optional labels of the y positions
 *   raw.colorScale    "sequential" | "diverging" (around raw.midpoint, 0)
 *   raw.domain        [min, max]
 *   raw.bins          [{x, y, value}]  x / y: a 0-based integer index, or a
 *                     category label (looked up in x/yCategories; labels
 *                     not listed are added in first-seen order); a repeated
 *                     x/y pair adds up
 *
 * Only the supplied bins are drawn, over one background rect for the empty
 * grid, so a sparse grid stays cheap. Tick labels use the category labels
 * (or the indices), and a colour key names the value measure. One click /
 * keydown listener on the grid serves every cell; above 2,000 bins the
 * cells are not individually focusable (the accessible table lists them).
 *
 * Interaction: cells emit `mj-chart-pixel-click` { x, y, value } where x / y
 * are the category labels when categories are used, else the indices.
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber } from "../svgdraw.js";
import {
  sequentialFill, divergingFill, divergingPosition, EMPTY_CELL_FILL
} from "./heatmaptable.js";

const FOCUSABLE_LIMIT = 2000
const MAX_INDEX = 100000


function _axis(given) {
  /*
   * A category axis: { labels: [...], indexOf(value) -> index or null }.
   */
  const labels = Array.isArray(given) === true ? given.map((label) => String(label)) : []
  const positions = new Map()
  labels.forEach((label, index) => {
    if (positions.has(label) === false) {
      positions.set(label, index)
    }
  })
  const indexOf = (value) => {
    if (typeof value === "number" && Number.isFinite(value) === true) {
      const index = Math.floor(value)
      return index >= 0 && index <= MAX_INDEX ? index : null
    }
    if (typeof value === "string" && value.length > 0) {
      if (positions.has(value) === false) {
        positions.set(value, labels.length)
        labels.push(value)
      }
      return positions.get(value)
    }
    return null
  }
  return { labels: labels, indexOf: indexOf }
}


export function render(ctx) {
  /*
   * Render a pixel chart.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const raw = ctx.raw !== null && ctx.raw !== undefined ? ctx.raw : {}
  const root = svgEl("g", { part: "plot" }, [])
  const xAxis = _axis(raw.xCategories)
  const yAxis = _axis(raw.yCategories)
  const xDim = raw.xDimension !== undefined && raw.xDimension !== null ? String(raw.xDimension) : "X"
  const yDim = raw.yDimension !== undefined && raw.yDimension !== null ? String(raw.yDimension) : "Y"
  const measure = raw.valueMeasure !== undefined && raw.valueMeasure !== null
    ? String(raw.valueMeasure)
    : "Value"

  /* Bins by cell (repeats add up). */
  const cells = new Map()
  const list = Array.isArray(raw.bins) === true ? raw.bins : []
  for (let index = 0; index < list.length; index = index + 1) {
    const bin = list[index]
    if (bin === null || typeof bin !== "object") {
      continue
    }
    const value = typeof bin.value === "number" ? bin.value : Number(bin.value)
    const xi = xAxis.indexOf(bin.x)
    const yi = yAxis.indexOf(bin.y)
    if (xi === null || yi === null || bin.value === null || Number.isFinite(value) === false) {
      continue
    }
    const key = `${xi},${yi}`
    const previous = cells.get(key)
    cells.set(key, { x: xi, y: yi, value: (previous !== undefined ? previous.value : 0) + value })
  }
  const entries = Array.from(cells.values()).sort((a, b) => a.y - b.y || a.x - b.x)
  const labelX = (index) => (index < xAxis.labels.length ? xAxis.labels[index] : String(index))
  const labelY = (index) => (index < yAxis.labels.length ? yAxis.labels[index] : String(index))

  ctx.setTable({
    columns: [xDim, yDim, measure],
    rows: entries.map((entry) => [labelX(entry.x), labelY(entry.y), entry.value]),
    caption: ctx.label
  })

  if (entries.length === 0) {
    return root
  }

  let xBins = xAxis.labels.length
  let yBins = yAxis.labels.length
  let low = Infinity
  let high = -Infinity
  entries.forEach((entry) => {
    xBins = Math.max(xBins, entry.x + 1)
    yBins = Math.max(yBins, entry.y + 1)
    low = Math.min(low, entry.value)
    high = Math.max(high, entry.value)
  })
  let domain = [low, high]
  if (Array.isArray(raw.domain) === true && raw.domain.length === 2 &&
      Number.isFinite(raw.domain[0]) === true && Number.isFinite(raw.domain[1]) === true) {
    domain = [Math.min(raw.domain[0], raw.domain[1]), Math.max(raw.domain[0], raw.domain[1])]
  }
  const diverging = raw.colorScale === "diverging" || ctx.attrs("style", null) === "diverging"
  const midpoint = typeof raw.midpoint === "number" && Number.isFinite(raw.midpoint) === true ? raw.midpoint : 0
  const fillOf = (value) => {
    if (diverging === true) {
      return divergingFill(divergingPosition(value, domain, midpoint))
    }
    const span = domain[1] - domain[0]
    return sequentialFill(span > 0 ? (value - domain[0]) / span : 1)
  }

  let longestY = 0
  for (let yi = 0; yi < Math.min(yBins, 200); yi = yi + 1) {
    longestY = Math.max(longestY, labelY(yi).length * 9 * 0.6)
  }
  const margin = { top: 24, right: 12, bottom: 34, left: Math.min(Math.max(longestY + 24, 40), ctx.width * 0.3) }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)
  const cellW = plotW / xBins
  const cellH = plotH / yBins

  const plot = svgEl("g", { transform: `translate(${margin.left},${margin.top})` }, [])
  root.appendChild(plot)

  /* Decoration: empty grid, ticks, axis titles, colour key. */
  const decor = svgEl("g", { "aria-hidden": "true" }, [])
  plot.appendChild(decor)
  decor.appendChild(svgEl("rect", { x: 0, y: 0, width: plotW, height: plotH, fill: EMPTY_CELL_FILL }, []))
  const muted = "var(--mj-text-muted, #5f6673)"
  const xStep = Math.max(1, Math.ceil(xBins / Math.max(Math.floor(plotW / 36), 1)))
  for (let xi = 0; xi < xBins; xi = xi + xStep) {
    const text = labelX(xi)
    decor.appendChild(svgEl("text", {
      x: xi * cellW + cellW / 2, y: plotH + 12, "text-anchor": "middle", "font-size": 9, fill: muted
    }, text.length > 6 ? text.slice(0, 5) + "…" : text))
  }
  const yStep = Math.max(1, Math.ceil(yBins / Math.max(Math.floor(plotH / 14), 1)))
  for (let yi = 0; yi < yBins; yi = yi + yStep) {
    decor.appendChild(svgEl("text", {
      x: -4, y: yi * cellH + cellH / 2 + 3, "text-anchor": "end", "font-size": 9, fill: muted
    }, labelY(yi)))
  }
  decor.appendChild(svgEl("text", {
    x: plotW / 2, y: plotH + 28, "text-anchor": "middle", "font-size": 11, fill: muted
  }, xDim))
  decor.appendChild(svgEl("text", {
    x: -(margin.left - 10), y: plotH / 2, "text-anchor": "middle", "font-size": 11, fill: muted,
    transform: `rotate(-90, ${-(margin.left - 10)}, ${plotH / 2})`
  }, yDim))

  const keyW = Math.min(110, plotW * 0.35)
  const keyX = plotW - keyW - 24
  const steps = 6
  decor.appendChild(svgEl("text", {
    x: keyX - 6, y: -9, "text-anchor": "end", "font-size": 9, fill: muted
  }, `${measure}  ${formatNumber(domain[0])}`))
  for (let s = 0; s < steps; s = s + 1) {
    decor.appendChild(svgEl("rect", {
      x: keyX + s * keyW / steps, y: -17, width: keyW / steps, height: 9,
      fill: fillOf(domain[0] + (domain[1] - domain[0]) * s / (steps - 1))
    }, []))
  }
  decor.appendChild(svgEl("text", {
    x: keyX + keyW + 4, y: -9, "font-size": 9, fill: muted
  }, formatNumber(domain[1])))

  /* Cells: only the supplied bins. */
  const focusable = entries.length <= FOCUSABLE_LIMIT
  const grid = svgEl("g", { part: "pixels" }, [])
  plot.appendChild(grid)
  for (let index = 0; index < entries.length; index = index + 1) {
    const entry = entries[index]
    const label = `${xDim} ${labelX(entry.x)}, ${yDim} ${labelY(entry.y)}: ${formatNumber(entry.value)} ${measure}`
    const rect = svgEl("rect", {
      x: (entry.x * cellW).toFixed(2), y: (entry.y * cellH).toFixed(2),
      width: Math.max(cellW - 0.5, 0.5).toFixed(2), height: Math.max(cellH - 0.5, 0.5).toFixed(2),
      fill: fillOf(entry.value), part: "pixel", "data-index": index
    }, [svgEl("title", null, label)])
    if (focusable === true) {
      rect.setAttribute("tabindex", "0")
      rect.setAttribute("role", "img")
      rect.setAttribute("aria-label", label)
    }
    grid.appendChild(rect)
  }

  const useLabels = xAxis.labels.length > 0 || yAxis.labels.length > 0
  const emitFor = (target) => {
    const index = target !== null && target.getAttribute !== undefined
      ? Number(target.getAttribute("data-index"))
      : NaN
    if (Number.isInteger(index) === false || index < 0 || index >= entries.length) {
      return
    }
    const entry = entries[index]
    ctx.emit("mj-chart-pixel-click", {
      x: useLabels === true ? labelX(entry.x) : entry.x,
      y: useLabels === true ? labelY(entry.y) : entry.y,
      value: entry.value
    })
  }
  grid.addEventListener("click", (event) => {
    emitFor(event.target.closest("rect"))
  })
  grid.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault()
      emitFor(event.target.closest("rect"))
    }
  })

  return root
}


registerRenderer("pixel", render, { legend: "none" })
