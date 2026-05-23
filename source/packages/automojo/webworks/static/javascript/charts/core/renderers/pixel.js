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
 *   raw.valueMeasure  label for the value
 *   raw.colorScale    "sequential" | "diverging"
 *   raw.domain        [min, max]
 *   raw.bins          [{x, y, value}]   x/y are 0-based integer indices
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber, escapeHtml } from "../svgdraw.js";
import { linearScale, niceTicks } from "../scales.js";


/* ── colour helpers ─────────────────────────────────────────────────── */

const SEQ_LOW  = "var(--mj-color-accent-100, #dbeafe)"
const SEQ_HIGH = "var(--mj-color-accent-700, #1d4ed8)"
const DIV_LOW  = "var(--mj-color-danger,  #b91c1c)"
const DIV_MID  = "var(--mj-surface,       #ffffff)"
const DIV_HIGH = "var(--mj-color-success, #15803d)"

function _seqFill(t) {
  const opacity = Math.max(0, Math.min(1, t))
  return `color-mix(in srgb, ${SEQ_HIGH} ${(opacity * 100).toFixed(1)}%, ${SEQ_LOW})`
}

function _divFill(t) {
  if (t <= 0.5) {
    const opacity = (0.5 - t) * 2
    return `color-mix(in srgb, ${DIV_LOW} ${(opacity * 100).toFixed(1)}%, ${DIV_MID})`
  }
  const opacity = (t - 0.5) * 2
  return `color-mix(in srgb, ${DIV_HIGH} ${(opacity * 100).toFixed(1)}%, ${DIV_MID})`
}


/* ── renderer ──────────────────────────────────────────────────────── */

export function render(ctx) {
  /*
   * Render a pixel chart.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const raw  = ctx.raw
  const root = svgEl("g", { part: "plot" }, [])

  const bins = (raw !== null && raw !== undefined && Array.isArray(raw.bins))
    ? raw.bins
    : []

  if (bins.length === 0) {
    return root
  }

  /* Determine grid dimensions from data */
  let xMax = 0
  let yMax = 0
  for (let i = 0; i < bins.length; i = i + 1) {
    const bin = bins[i]
    if (typeof bin.x === "number" && bin.x > xMax) {
      xMax = bin.x
    }
    if (typeof bin.y === "number" && bin.y > yMax) {
      yMax = bin.y
    }
  }
  const xBins = xMax + 1
  const yBins = yMax + 1

  /* Domain */
  let domainPair = null
  if (raw !== null && raw !== undefined && Array.isArray(raw.domain) === true) {
    domainPair = raw.domain
  } else {
    let lo = Infinity
    let hi = -Infinity
    for (let i = 0; i < bins.length; i = i + 1) {
      const v = bins[i].value
      if (typeof v !== "number") {
        continue
      }
      if (v < lo) {
        lo = v
      }
      if (v > hi) {
        hi = v
      }
    }
    domainPair = lo === Infinity ? [0, 1] : lo === hi ? [lo - 1, hi + 1] : [lo, hi]
  }

  const colorScaleMode = (raw !== null && raw !== undefined && raw.colorScale)
    ? raw.colorScale
    : "sequential"
  const valScale = linearScale(domainPair, [0, 1])

  const horizontal = ctx.orientation !== "vertical"

  const margin = { top: 16, right: 16, bottom: 40, left: 52 }
  const plotW  = Math.max(ctx.width  - margin.left - margin.right,  10)
  const plotH  = Math.max(ctx.height - margin.top  - margin.bottom, 10)

  const cellW  = plotW / xBins
  const cellH  = plotH / yBins

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  /* X axis labels */
  const xDim = raw !== null && raw !== undefined ? (raw.xDimension || "X") : "X"
  const yDim = raw !== null && raw !== undefined ? (raw.yDimension || "Y") : "Y"

  const xTickStep = Math.max(1, Math.floor(xBins / 10))
  for (let xi = 0; xi < xBins; xi = xi + xTickStep) {
    const px = xi * cellW + cellW / 2
    plot.appendChild(svgEl("text", {
      x: px, y: plotH + 14,
      "text-anchor": "middle",
      "font-size": 9,
      fill: "var(--mj-text-muted, #6b7280)"
    }, String(xi)))
  }

  const yTickStep = Math.max(1, Math.floor(yBins / 8))
  for (let yi = 0; yi < yBins; yi = yi + yTickStep) {
    const py = yi * cellH + cellH / 2
    plot.appendChild(svgEl("text", {
      x: -4, y: py + 3,
      "text-anchor": "end",
      "font-size": 9,
      fill: "var(--mj-text-muted, #6b7280)"
    }, String(yi)))
  }

  /* Axis labels */
  plot.appendChild(svgEl("text", {
    x: plotW / 2, y: plotH + 30,
    "text-anchor": "middle",
    "font-size": 11,
    fill: "var(--mj-text-muted, #6b7280)"
  }, escapeHtml(xDim)))

  plot.appendChild(svgEl("text", {
    x: -40, y: plotH / 2,
    "text-anchor": "middle",
    "font-size": 11,
    fill: "var(--mj-text-muted, #6b7280)",
    transform: `rotate(-90, -40, ${plotH / 2})`
  }, escapeHtml(yDim)))

  /* Build bins lookup for fast access */
  const binMap = {}
  for (let i = 0; i < bins.length; i = i + 1) {
    const bin = bins[i]
    const key = `${bin.x},${bin.y}`
    binMap[key] = bin.value
  }

  /* Draw pixel cells row by row */
  for (let yi = 0; yi < yBins; yi = yi + 1) {
    const rowG = svgEl("g", { "data-row": yi }, [])
    for (let xi = 0; xi < xBins; xi = xi + 1) {
      const key    = `${xi},${yi}`
      const val    = binMap[key]
      let   fillColor = "var(--mj-surface-raised, #f3f4f6)"

      if (typeof val === "number") {
        const t = valScale(val)
        if (colorScaleMode === "diverging") {
          fillColor = _divFill(t)
        } else {
          fillColor = _seqFill(t)
        }
      }

      const cellRect = svgEl("rect", {
        x: xi * cellW, y: yi * cellH,
        width: Math.max(cellW - 0.5, 1),
        height: Math.max(cellH - 0.5, 1),
        fill: fillColor
      }, [])

      if (typeof val === "number") {
        const labelText = `(${xi}, ${yi}): ${formatNumber(val)}`
        cellRect.setAttribute("part", "pixel")
        cellRect.setAttribute("tabindex", "0")
        cellRect.setAttribute("role", "img")
        cellRect.setAttribute("aria-label", labelText)
        cellRect.appendChild(svgEl("title", null, labelText))
        const capturedX = xi
        const capturedY = yi
        const capturedVal = val
        const handler = () => {
          ctx.emit("mj-chart-pixel-click", {
            x: capturedX, y: capturedY, value: capturedVal
          })
        }
        cellRect.addEventListener("click", handler)
        cellRect.addEventListener("keydown", (event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault()
            handler()
          }
        })
      }

      rowG.appendChild(cellRect)
    }
    plot.appendChild(rowG)
  }

  return root
}


registerRenderer("pixel", render)
