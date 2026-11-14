/*
 * matrix.js
 *
 * Categorical relationship matrix (bubble matrix / cross-tab / heat matrix).
 *
 * JSON shape (ctx.raw):
 *   x_categories[]   column labels (optional: derived from cells, in
 *                    first-seen order; cells naming a category that is not
 *                    listed add it at the end)
 *   y_categories[]   row labels (same rules)
 *   cells[]          { x, y, value }  (a repeated x/y pair adds up)
 *   mark             "circle" (default) | "square"
 *   meta.yLabel      optional name of the row categories (the corner
 *                    header of the accessible table; default "Row")
 *
 * Circle mode: area ∝ |value| (sqrt scale); negative values are drawn in the
 * second palette colour, positive ones in the first, and the legend names
 * both when the data has both signs. Square mode: cells are filled with a
 * sequential ramp (or, with negative values, a diverging ramp around 0) and
 * the value is printed when it fits. A zero is a real value (an empty
 * square / no bubble but a focusable cell); a cell missing from the data is
 * left blank.
 *
 * Interaction: each cell with a value emits `mj-chart-matrix-click`
 * { x, y, value }.
 *
 * Registers: "matrix"
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber } from "../svgdraw.js";
import { seriesColor } from "../scales.js";
import {
  sequentialFill, divergingFill, divergingPosition, labelColorFor, applyContrastText
} from "./heatmaptable.js";

const CHAR_WIDTH = 0.6


function _fit(text, maxWidth, fontSize) {
  /*
   * Shorten a label with an ellipsis to about maxWidth pixels.
   */
  const value = String(text)
  const capacity = Math.max(Math.floor(maxWidth / (fontSize * CHAR_WIDTH)), 1)
  if (value.length <= capacity) {
    return value
  }
  return value.slice(0, Math.max(capacity - 1, 1)) + "…"
}


function _categories(given, cells, field) {
  /*
   * The listed categories plus any a cell names that is not listed.
   */
  const list = []
  const seen = new Set()
  const add = (value) => {
    if (value === null || value === undefined) {
      return
    }
    const text = String(value)
    if (seen.has(text) === false) {
      seen.add(text)
      list.push(text)
    }
  }
  if (Array.isArray(given) === true) {
    given.forEach(add)
  }
  cells.forEach((cell) => add(cell[field]))
  return list
}


export function render(ctx) {
  /*
   * Render a categorical matrix chart.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const raw = ctx.raw !== null && ctx.raw !== undefined ? ctx.raw : {}
  const cells = (Array.isArray(raw.cells) === true ? raw.cells : [])
    .filter((cell) => cell !== null && typeof cell === "object")
  const xCats = _categories(raw.x_categories, cells, "x")
  const yCats = _categories(raw.y_categories, cells, "y")
  const mark = raw.mark === "square" ? "square" : "circle"
  const root = svgEl("g", { part: "plot" }, [])

  /* Values by "x||y" (repeats add up). */
  const values = new Map()
  let maxAbs = 0
  let low = 0
  let high = 0
  for (let index = 0; index < cells.length; index = index + 1) {
    const cell = cells[index]
    const value = typeof cell.value === "number" ? cell.value : Number(cell.value)
    if (cell.x === undefined || cell.y === undefined || cell.value === null ||
        Number.isFinite(value) === false) {
      continue
    }
    const key = `${String(cell.x)}||${String(cell.y)}`
    const total = (values.has(key) === true ? values.get(key) : 0) + value
    values.set(key, total)
  }
  values.forEach((value) => {
    maxAbs = Math.max(maxAbs, Math.abs(value))
    low = Math.min(low, value)
    high = Math.max(high, value)
  })
  const signed = low < 0

  /* The corner header names the row categories (never an empty header). */
  const meta = ctx.model !== null && ctx.model !== undefined && ctx.model.meta !== null &&
    typeof ctx.model.meta === "object" ? ctx.model.meta : {}
  const cornerHeader = typeof meta.yLabel === "string" && meta.yLabel.trim().length > 0
    ? meta.yLabel.trim()
    : "Row"
  ctx.setTable({
    columns: [cornerHeader].concat(xCats),
    rows: yCats.map((y) => [y].concat(xCats.map((x) => {
      const key = `${x}||${y}`
      return values.has(key) === true ? values.get(key) : null
    }))),
    caption: ctx.label
  })

  if (xCats.length === 0 || yCats.length === 0 || values.size === 0) {
    return root
  }

  /* Layout: gutters sized from the labels. */
  let longestY = 0
  yCats.forEach((label) => {
    longestY = Math.max(longestY, label.length * 11 * CHAR_WIDTH)
  })
  const marginLeft = Math.min(Math.max(longestY + 12, 32), ctx.width * 0.3)
  const marginTop = 24
  const plotW = Math.max(ctx.width - marginLeft - 8, 10)
  const plotH = Math.max(ctx.height - marginTop - 8, 10)
  const cellW = plotW / xCats.length
  const cellH = plotH / yCats.length
  const maxRadius = Math.min(cellW, cellH) * 0.44

  const plot = svgEl("g", { transform: `translate(${marginLeft},${marginTop})` }, [])
  root.appendChild(plot)
  const decor = svgEl("g", { "aria-hidden": "true" }, [])
  plot.appendChild(decor)

  const every = Math.max(1, Math.ceil(40 / cellW))
  for (let xi = 0; xi < xCats.length; xi = xi + every) {
    decor.appendChild(svgEl("text", {
      x: xi * cellW + cellW / 2, y: -8, "text-anchor": "middle", "font-size": 11,
      fill: "var(--mj-text, #14181f)"
    }, _fit(xCats[xi], cellW * every - 4, 11)))
  }
  for (let yi = 0; yi < yCats.length; yi = yi + 1) {
    decor.appendChild(svgEl("text", {
      x: -8, y: yi * cellH + cellH / 2 + 4, "text-anchor": "end", "font-size": 11,
      fill: "var(--mj-text, #14181f)"
    }, _fit(yCats[yi], marginLeft - 12, 11)))
    for (let xi = 0; xi < xCats.length; xi = xi + 1) {
      if ((xi + yi) % 2 === 0) {
        decor.appendChild(svgEl("rect", {
          x: xi * cellW, y: yi * cellH, width: Math.max(cellW - 1, 0.5), height: Math.max(cellH - 1, 0.5),
          fill: "var(--mj-bg-muted, #eef0f3)", "fill-opacity": 0.5
        }, []))
      }
    }
  }

  for (let yi = 0; yi < yCats.length; yi = yi + 1) {
    for (let xi = 0; xi < xCats.length; xi = xi + 1) {
      const key = `${xCats[xi]}||${yCats[yi]}`
      if (values.has(key) === false) {
        continue
      }
      const value = values.get(key)
      const cx = xi * cellW + cellW / 2
      const cy = yi * cellH + cellH / 2
      const ariaLabel = `${xCats[xi]}, ${yCats[yi]}: ${formatNumber(value)}`
      const markEl = svgEl("g", {
        tabindex: "0", role: "img", "aria-label": ariaLabel, part: "matrix-cell"
      }, [])

      if (mark === "square") {
        let fill = null
        let intensity = 0
        if (signed === true) {
          intensity = divergingPosition(value, [low, high], 0)
          fill = divergingFill(intensity)
        } else {
          intensity = high > 0 ? value / high : 0
          fill = sequentialFill(intensity)
        }
        markEl.appendChild(svgEl("rect", {
          x: xi * cellW, y: yi * cellH, width: Math.max(cellW - 1, 0.5), height: Math.max(cellH - 1, 0.5),
          fill: fill
        }, []))
        const text = formatNumber(value)
        if (cellH >= 14 && cellW >= text.length * 6.6 + 4) {
          const label = svgEl("text", {
            x: cx, y: cy + 4, "text-anchor": "middle", "font-size": Math.min(11, cellH * 0.45),
            fill: labelColorFor(intensity), "pointer-events": "none"
          }, text)
          applyContrastText(label, fill, intensity)
          markEl.appendChild(label)
        }
      } else {
        const radius = maxAbs > 0 ? Math.sqrt(Math.abs(value) / maxAbs) * maxRadius : 0
        /* An invisible hit area keeps small and zero values focusable / clickable. */
        markEl.appendChild(svgEl("rect", {
          x: xi * cellW, y: yi * cellH, width: cellW, height: cellH, fill: "transparent"
        }, []))
        markEl.appendChild(svgEl("circle", {
          cx: cx, cy: cy, r: radius.toFixed(2),
          fill: value < 0 ? seriesColor(1) : seriesColor(0), "fill-opacity": "0.8"
        }, []))
      }
      markEl.appendChild(svgEl("title", null, ariaLabel))

      const capturedX = xCats[xi]
      const capturedY = yCats[yi]
      const handler = () => {
        ctx.emit("mj-chart-matrix-click", { x: capturedX, y: capturedY, value: value })
      }
      markEl.addEventListener("click", handler)
      markEl.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault()
          handler()
        }
      })
      plot.appendChild(markEl)
    }
  }

  if (signed === true) {
    ctx.setLegend([
      { label: "Positive", color: mark === "square" ? divergingFill(1) : seriesColor(0) },
      { label: "Negative", color: mark === "square" ? divergingFill(-1) : seriesColor(1) }
    ])
  } else {
    ctx.setLegend([])
  }
  return root
}


registerRenderer("matrix", render, { legend: "none" })
