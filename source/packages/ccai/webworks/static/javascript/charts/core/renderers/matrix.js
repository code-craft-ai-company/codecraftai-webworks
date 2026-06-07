/*
 * matrix.js
 *
 * Categorical relationship matrix (bubble matrix / cross-tab / heat matrix).
 *
 * JSON shape (ctx.raw):
 *   x_categories[]   column labels
 *   y_categories[]   row labels
 *   cells[]          { x, y, value }
 *   mark             "circle" (default) | "square"
 *
 * Mark size: sqrt scale so area ∝ value (circle mode).
 * Mark color: sequential scale (square/color mode).
 *
 * Registers: "matrix"
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, formatNumber } from "../svgdraw.js";
import { sqrtScale, linearScale } from "../scales.js";


/* Sequential color tokens (same convention as cohort.js). */
const SEQ_TOKENS = [
  "var(--mj-chart-sequential-1, #eff6ff)",
  "var(--mj-chart-sequential-2, #bfdbfe)",
  "var(--mj-chart-sequential-3, #93c5fd)",
  "var(--mj-chart-sequential-4, #60a5fa)",
  "var(--mj-chart-sequential-5, #3b82f6)",
  "var(--mj-chart-sequential-6, #2563eb)",
  "var(--mj-chart-sequential-7, #1d4ed8)"
]


function _seqColor(rate) {
  /*
   * Map a 0–1 value to a sequential color token.
   *
   * :returns: A CSS color string.
   */
  const clamped = Math.max(0, Math.min(1, rate))
  const idx = Math.round(clamped * (SEQ_TOKENS.length - 1))
  const color = SEQ_TOKENS[idx]
  return color
}


export function render(ctx) {
  /*
   * Render a categorical matrix chart.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const raw = ctx.raw
  const xCats = (raw !== null && raw !== undefined && Array.isArray(raw.x_categories))
    ? raw.x_categories
    : []
  const yCats = (raw !== null && raw !== undefined && Array.isArray(raw.y_categories))
    ? raw.y_categories
    : []
  const cells = (raw !== null && raw !== undefined && Array.isArray(raw.cells))
    ? raw.cells
    : []
  const mark = (raw !== null && raw !== undefined)
    ? (raw.mark || "circle")
    : "circle"

  const root = svgEl("g", { part: "plot" }, [])

  if (xCats.length === 0 || yCats.length === 0 || cells.length === 0) {
    return root
  }

  /* Layout. */
  const marginLeft = 80
  const marginTop = 40
  const marginRight = 8
  const marginBottom = 8

  const plotW = Math.max(ctx.width - marginLeft - marginRight, 10)
  const plotH = Math.max(ctx.height - marginTop - marginBottom, 10)

  const cellW = plotW / xCats.length
  const cellH = plotH / yCats.length

  /* Build cell value index. */
  const cellMap = {}
  let maxVal = 0
  for (let ci = 0; ci < cells.length; ci = ci + 1) {
    const cell = cells[ci]
    const v = typeof cell.value === "number" ? cell.value : 0
    const key = `${cell.x}||${cell.y}`
    cellMap[key] = v
    if (v > maxVal) { maxVal = v }
  }
  if (maxVal === 0) { maxVal = 1 }

  /* Scales. */
  const maxRadius = Math.min(cellW, cellH) * 0.42
  const radiusScale = sqrtScale([0, maxVal], [0, maxRadius])

  const plot = svgEl("g", {
    transform: `translate(${marginLeft},${marginTop})`
  }, [])
  root.appendChild(plot)

  /* Column headers. */
  for (let xi = 0; xi < xCats.length; xi = xi + 1) {
    plot.appendChild(svgEl("text", {
      x: xi * cellW + cellW / 2,
      y: -8,
      "text-anchor": "middle",
      "font-size": 11,
      fill: "var(--mj-text, #14181f)"
    }, escapeHtml(String(xCats[xi]))))
  }

  /* Row labels. */
  for (let yi = 0; yi < yCats.length; yi = yi + 1) {
    plot.appendChild(svgEl("text", {
      x: -8,
      y: yi * cellH + cellH / 2 + 4,
      "text-anchor": "end",
      "font-size": 11,
      fill: "var(--mj-text, #14181f)"
    }, escapeHtml(String(yCats[yi]))))
  }

  /* Cell backgrounds. */
  for (let yi = 0; yi < yCats.length; yi = yi + 1) {
    for (let xi = 0; xi < xCats.length; xi = xi + 1) {
      plot.appendChild(svgEl("rect", {
        x: xi * cellW, y: yi * cellH,
        width: cellW - 1, height: cellH - 1,
        fill: (xi + yi) % 2 === 0
          ? "var(--mj-surface-subtle, #f8f9fb)"
          : "var(--mj-surface, #ffffff)"
      }, []))
    }
  }

  /* Marks. */
  for (let yi = 0; yi < yCats.length; yi = yi + 1) {
    for (let xi = 0; xi < xCats.length; xi = xi + 1) {
      const key = `${xCats[xi]}||${yCats[yi]}`
      const value = cellMap[key] !== undefined ? cellMap[key] : 0

      if (value <= 0) {
        continue
      }

      const cellCX = xi * cellW + cellW / 2
      const cellCY = yi * cellH + cellH / 2
      const ariaLabel = `${xCats[xi]}, ${yCats[yi]}: ${formatNumber(value)}`

      const markEl = svgEl("g", {
        tabindex: "0",
        role: "img",
        "aria-label": ariaLabel,
        part: "matrix-cell"
      }, [])

      if (mark === "square") {
        const rate = value / maxVal
        const fillColor = _seqColor(rate)
        const textFill = rate > 0.55
          ? "var(--mj-text-on-accent, #ffffff)"
          : "var(--mj-text, #14181f)"

        markEl.appendChild(svgEl("rect", {
          x: xi * cellW, y: yi * cellH,
          width: cellW - 1, height: cellH - 1,
          fill: fillColor
        }, []))

        if (cellH >= 14 && cellW >= 28) {
          markEl.appendChild(svgEl("text", {
            x: cellCX, y: cellCY + 4,
            "text-anchor": "middle",
            "font-size": Math.min(11, cellH * 0.45),
            fill: textFill
          }, formatNumber(value)))
        }
      } else {
        /* circle mode */
        const r = radiusScale(value)
        markEl.appendChild(svgEl("circle", {
          cx: cellCX, cy: cellCY, r: r,
          fill: "var(--mj-color-accent-500, #2563eb)",
          "fill-opacity": "0.7"
        }, []))
      }

      markEl.appendChild(svgEl("title", null, ariaLabel))

      const capturedX = xCats[xi]
      const capturedY = yCats[yi]
      const capturedV = value
      const handler = () => {
        ctx.emit("mj-chart-matrix-click", {
          x: capturedX,
          y: capturedY,
          value: capturedV
        })
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

  return root
}


registerRenderer("matrix", render)
