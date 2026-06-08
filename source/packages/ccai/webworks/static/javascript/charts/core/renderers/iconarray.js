/*
 * iconarray.js
 *
 * Icon-array and waffle-pictograph renderers.  A grid of discrete unit
 * symbols colours proportions without any continuous axis, making
 * part-to-whole relationships viscerally countable.
 *
 * Registered types:
 *   "icon-array"        – grid of circle / person / square unit icons
 *   "waffle-pictograph" – alias: same renderer, square icons default
 *
 * ctx.raw shape:
 *   raw.total    total unit count (default 100)
 *   raw.series   [{name, count, icon?, color?}]
 *   raw.grid     { cols: N }   (default 10)
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, formatNumber } from "../svgdraw.js";


/* ── person silhouette path (normalised to a 1×1 box) ────────────────── */

function _personPath(cx, cy, size) {
  /*
   * Build a simple person-silhouette path centred at (cx, cy).
   *
   * :returns: SVG `d` string.
   */
  const r  = size * 0.22
  const bw = size * 0.44
  const bh = size * 0.40
  const bx = cx - bw / 2
  const by = cy - size * 0.05
  const d = `M${cx},${cy - size * 0.5 + r} ` +
    `a${r},${r} 0 1 1 0,${r * 0.01} ` +
    `M${bx},${by + bh} ` +
    `Q${bx},${by} ${cx},${by} ` +
    `Q${bx + bw},${by} ${bx + bw},${by + bh} Z`
  return d
}


/* ── icon drawing ────────────────────────────────────────────────────── */

function _drawIcon(iconType, cx, cy, size, color, label, index, ctx) {
  /*
   * Draw a single icon at (cx, cy) with accessibility marks.
   *
   * :returns: SVGElement.
   */
  let el = null
  const halfSize = size / 2

  if (iconType === "square") {
    el = svgEl("rect", {
      x: cx - halfSize + 1, y: cy - halfSize + 1,
      width: size - 2, height: size - 2,
      rx: 2,
      fill: color
    }, [])
  } else if (iconType === "person") {
    el = svgEl("path", {
      d: _personPath(cx, cy, size - 2),
      fill: color,
      "stroke-width": 0
    }, [])
  } else {
    /* default: circle */
    el = svgEl("circle", {
      cx: cx, cy: cy,
      r: halfSize - 1,
      fill: color
    }, [])
  }

  el.setAttribute("part", "icon")
  el.setAttribute("tabindex", "0")
  el.setAttribute("role", "img")
  el.setAttribute("aria-label", `${label} unit ${index + 1}`)
  el.appendChild(svgEl("title", null, `${label}: unit ${index + 1}`))

  const handler = () => {
    ctx.emit("mj-chart-icon-click", { series: label, index: index })
  }
  el.addEventListener("click", handler)
  el.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault()
      handler()
    }
  })
  return el
}


/* ── shared renderer ─────────────────────────────────────────────────── */

export function render(ctx) {
  /*
   * Render an icon array / waffle pictograph.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const raw  = ctx.raw
  const root = svgEl("g", { part: "plot" }, [])

  const series = (raw !== null && raw !== undefined && Array.isArray(raw.series))
    ? raw.series
    : []

  if (series.length === 0) {
    return root
  }

  const total   = (raw !== null && raw !== undefined && typeof raw.total === "number")
    ? raw.total
    : 100
  const gridCols = (raw !== null && raw !== undefined && raw.grid && raw.grid.cols)
    ? raw.grid.cols
    : 10
  const gridRows = Math.ceil(total / gridCols)

  /* Default icon type: square for waffle-pictograph, circle for icon-array */
  const defaultIcon = ctx.attrs("icon", "circle")

  const margin = { top: 8, right: 8, bottom: 40, left: 8 }
  const plotW  = Math.max(ctx.width  - margin.left - margin.right,  10)
  const plotH  = Math.max(ctx.height - margin.top  - margin.bottom, 10)

  const cellSize = Math.min(plotW / gridCols, plotH / gridRows)

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  /* Background grid */
  for (let row = 0; row < gridRows; row = row + 1) {
    for (let col = 0; col < gridCols; col = col + 1) {
      const cx = col * cellSize + cellSize / 2
      const cy = row * cellSize + cellSize / 2
      const bg = svgEl("rect", {
        x: col * cellSize, y: row * cellSize,
        width: cellSize, height: cellSize,
        fill: "none",
        stroke: "var(--mj-border, #e0e3e9)",
        "stroke-width": 0.5
      }, [])
      bg.setAttribute("aria-hidden", "true")
      plot.appendChild(bg)
    }
  }

  /* Place icons series-by-series */
  let unitIndex = 0
  for (let s = 0; s < series.length; s = s + 1) {
    const ser   = series[s]
    const count = typeof ser.count === "number" ? ser.count : 0
    const color = ser.color
      ? ser.color
      : ctx.colorFor(ser.name)
    const iconType = ser.icon || defaultIcon

    for (let u = 0; u < count && unitIndex < total; u = u + 1) {
      const col = unitIndex % gridCols
      const row = Math.floor(unitIndex / gridCols)
      const cx  = col * cellSize + cellSize / 2
      const cy  = row * cellSize + cellSize / 2

      const el = _drawIcon(iconType, cx, cy, cellSize * 0.8, color, ser.name, u, ctx)
      plot.appendChild(el)
      unitIndex = unitIndex + 1
    }
  }

  /* Legend */
  let legendX = 0
  const legendY = gridRows * cellSize + 12
  for (let s = 0; s < series.length; s = s + 1) {
    const ser   = series[s]
    const color = ser.color ? ser.color : ctx.colorFor(ser.name)
    plot.appendChild(svgEl("rect", {
      x: legendX, y: legendY,
      width: 10, height: 10,
      fill: color, rx: 2
    }, []))
    const pctText = total > 0 ? ` (${formatNumber(ser.count / total * 100, { maximumFractionDigits: 1 })}%)` : ""
    const legendLabel = escapeHtml(ser.name) + pctText
    plot.appendChild(svgEl("text", {
      x: legendX + 14, y: legendY + 9,
      "font-size": 11,
      fill: "var(--mj-text-muted, #6b7280)"
    }, legendLabel))
    legendX = legendX + 14 + legendLabel.length * 6.5 + 12
  }

  return root
}


registerRenderer("icon-array",        render)
registerRenderer("waffle-pictograph", render)
