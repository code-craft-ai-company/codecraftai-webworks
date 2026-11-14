/*
 * iconarray.js
 *
 * Icon-array and waffle-pictograph renderers. A grid of discrete unit
 * symbols colours proportions without any continuous axis, making
 * part-to-whole relationships countable.
 *
 * Registered types:
 *   "icon-array"        – grid of unit icons, circle by default
 *   "waffle-pictograph" – the same grid with square icons by default
 *
 * ctx.raw shape:
 *   raw.total     total unit count (default: the sum of the counts)
 *   raw.series    [{name, count, icon?, color?}]
 *   raw.grid      { cols: N }   (default 10)
 *   raw.per_icon  units each icon stands for (default 1; chosen
 *                 automatically when the total needs more than 400 icons)
 *
 * Attributes: `icon` or `mode` ("circle" | "square" | "person") sets the
 * default icon; orientation "horizontal" (default) fills rows left to right,
 * "vertical" fills columns top to bottom.
 *
 * Icon counts are rounded with the largest-remainder method so they add up
 * to the drawn total; counts above the total are cut at the total and the
 * chart says so. Only `total` slots are outlined (no padding to a full last
 * row). The grid is centred and the legend (name, count, share) wraps.
 *
 * Interaction: each series is ONE focusable group (its icons inside); click
 * / Enter emits `mj-chart-icon-click` { series, count }.
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber } from "../svgdraw.js";

const MAX_ICONS = 400
const LEGEND_ROW = 16


function _personIcon(cx, cy, size, color) {
  /*
   * A person silhouette centred on (cx, cy): a head circle above a rounded
   * body, both centred on cx.
   */
  const group = svgEl("g", {}, [])
  const headR = size * 0.18
  group.appendChild(svgEl("circle", {
    cx: cx.toFixed(2), cy: (cy - size * 0.5 + headR).toFixed(2), r: headR.toFixed(2), fill: color
  }, []))
  const bodyW = size * 0.56
  const top = cy - size * 0.5 + headR * 2 + size * 0.04
  const bottom = cy + size * 0.5
  const left = cx - bodyW / 2
  const right = cx + bodyW / 2
  group.appendChild(svgEl("path", {
    d: `M${left.toFixed(2)},${bottom.toFixed(2)} L${left.toFixed(2)},${(top + bodyW * 0.3).toFixed(2)} ` +
      `Q${left.toFixed(2)},${top.toFixed(2)} ${cx.toFixed(2)},${top.toFixed(2)} ` +
      `Q${right.toFixed(2)},${top.toFixed(2)} ${right.toFixed(2)},${(top + bodyW * 0.3).toFixed(2)} ` +
      `L${right.toFixed(2)},${bottom.toFixed(2)} Z`,
    fill: color
  }, []))
  return group
}


function _icon(type, cx, cy, size, color) {
  /*
   * One unit icon.
   */
  if (type === "square") {
    return svgEl("rect", {
      x: (cx - size / 2).toFixed(2), y: (cy - size / 2).toFixed(2),
      width: size.toFixed(2), height: size.toFixed(2), rx: Math.min(2, size / 6).toFixed(2), fill: color
    }, [])
  }
  if (type === "person") {
    return _personIcon(cx, cy, size, color)
  }
  return svgEl("circle", { cx: cx.toFixed(2), cy: cy.toFixed(2), r: (size / 2).toFixed(2), fill: color }, [])
}


function _niceUnit(total) {
  /*
   * Units per icon so that the total needs at most MAX_ICONS icons:
   * 1, 2, 5, 10, 20, 50, ...
   */
  let unit = 1
  const steps = [1, 2, 5]
  let magnitude = 1
  let index = 0
  while (total / unit > MAX_ICONS) {
    index = index + 1
    if (index >= steps.length) {
      index = 0
      magnitude = magnitude * 10
    }
    unit = steps[index] * magnitude
  }
  return unit
}


function _largestRemainder(shares, slots) {
  /*
   * Whole icon counts for fractional shares that add up to `slots`.
   */
  const floors = shares.map((share) => Math.floor(share))
  let left = slots - floors.reduce((sum, value) => sum + value, 0)
  const order = shares.map((share, index) => ({ index: index, rest: share - Math.floor(share) }))
    .sort((a, b) => b.rest - a.rest)
  for (let k = 0; k < order.length && left > 0; k = k + 1) {
    floors[order[k].index] = floors[order[k].index] + 1
    left = left - 1
  }
  return floors
}


export function render(ctx) {
  /*
   * Render an icon array / waffle pictograph.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const raw = ctx.raw !== null && ctx.raw !== undefined ? ctx.raw : {}
  const root = svgEl("g", { part: "plot" }, [])
  const series = ctx.model.series.map((entry) => {
    const count = typeof entry.count === "number" && Number.isFinite(entry.count) === true
      ? Math.max(entry.count, 0)
      : 0
    return { name: entry.name, count: count, icon: entry.icon, color: ctx.colorFor(entry.name) }
  })

  const sum = series.reduce((total, entry) => total + entry.count, 0)
  const total = typeof raw.total === "number" && Number.isFinite(raw.total) === true && raw.total > 0
    ? raw.total
    : sum
  ctx.setTable({
    columns: ["Series", "Count", "Share of total (%)"],
    rows: series.map((entry) => [entry.name, entry.count, total > 0 ? entry.count / total * 100 : null]),
    caption: ctx.label
  })

  if (series.length === 0 || total <= 0) {
    return root
  }

  const perIcon = typeof raw.per_icon === "number" && Number.isFinite(raw.per_icon) === true &&
    raw.per_icon > 0 && total / raw.per_icon <= MAX_ICONS * 5
    ? raw.per_icon
    : _niceUnit(total)
  const slots = Math.max(Math.round(total / perIcon), 1)
  const overflow = sum > total

  /* Icons per series, reconciled with the slots (cut at the total). */
  let remaining = total
  const shares = series.map((entry) => {
    const kept = Math.min(entry.count, Math.max(remaining, 0))
    remaining = remaining - kept
    return kept / perIcon
  })
  const filled = Math.min(Math.round(shares.reduce((a, b) => a + b, 0)), slots)
  const iconCounts = _largestRemainder(shares, filled)

  const isWaffle = ctx.type === "waffle-pictograph"
  const attrIcon = ctx.attrs("icon", null) || ctx.attrs("mode", null)
  const defaultIcon = attrIcon === "square" || attrIcon === "person" || attrIcon === "circle"
    ? attrIcon
    : (isWaffle === true ? "square" : "circle")
  const byColumn = ctx.orientation === "vertical"

  const gridCols = raw.grid !== null && typeof raw.grid === "object" &&
    Number.isInteger(raw.grid.cols) === true && raw.grid.cols > 0 ? raw.grid.cols : 10
  const gridRows = Math.ceil(slots / gridCols)

  /* Legend entries, wrapped into rows. */
  const legendItems = series.map((entry) => {
    const share = formatNumber(entry.count / total * 100, { maximumFractionDigits: 1 })
    const text = `${entry.name}: ${formatNumber(entry.count)} (${share}%)`
    return { entry: entry, text: text, width: 14 + text.length * 6 + 14 }
  })
  const pad = 8
  const availableW = Math.max(ctx.width - pad * 2, 10)
  let legendRows = 1
  let cursor = 0
  legendItems.forEach((item) => {
    if (cursor > 0 && cursor + item.width > availableW) {
      legendRows = legendRows + 1
      cursor = 0
    }
    item.row = legendRows - 1
    item.x = cursor
    cursor = cursor + item.width
  })
  const noteH = overflow === true || perIcon > 1 ? 14 : 0
  const legendH = legendRows * LEGEND_ROW + noteH + 6
  const availableH = Math.max(ctx.height - pad * 2 - legendH, 10)
  const cell = Math.max(Math.min(availableW / gridCols, availableH / gridRows), 2)
  const gridW = cell * gridCols
  const gridH = cell * gridRows
  const originX = pad + (availableW - gridW) / 2
  const originY = pad
  const iconSize = cell * 0.8

  const slotCenter = (index) => {
    const col = byColumn === true ? Math.floor(index / gridRows) : index % gridCols
    const row = byColumn === true ? index % gridRows : Math.floor(index / gridCols)
    return { x: originX + col * cell + cell / 2, y: originY + row * cell + cell / 2 }
  }

  /* Outlines of the `slots` positions only. */
  const outline = svgEl("g", { "aria-hidden": "true" }, [])
  root.appendChild(outline)
  for (let index = 0; index < slots; index = index + 1) {
    const center = slotCenter(index)
    outline.appendChild(svgEl("rect", {
      x: (center.x - cell / 2).toFixed(2), y: (center.y - cell / 2).toFixed(2),
      width: cell.toFixed(2), height: cell.toFixed(2), fill: "none",
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 0.5
    }, []))
  }

  /* Icons, one focusable group per series. */
  let slot = 0
  for (let s = 0; s < series.length; s = s + 1) {
    const entry = series[s]
    const share = formatNumber(entry.count / total * 100, { maximumFractionDigits: 1 })
    const label = `${entry.name}: ${formatNumber(entry.count)} of ${formatNumber(total)} (${share}%)`
    const group = svgEl("g", { tabindex: "0", role: "img", "aria-label": label, part: "icon-series" }, [])
    group.appendChild(svgEl("title", null, label))
    const type = entry.icon === "square" || entry.icon === "person" || entry.icon === "circle"
      ? entry.icon
      : defaultIcon
    for (let k = 0; k < iconCounts[s] && slot < slots; k = k + 1) {
      const center = slotCenter(slot)
      const icon = _icon(type, center.x, center.y, iconSize, entry.color)
      icon.setAttribute("part", "icon")
      group.appendChild(icon)
      slot = slot + 1
    }
    const captured = entry
    const handler = () => {
      ctx.emit("mj-chart-icon-click", { series: captured.name, count: captured.count })
    }
    group.addEventListener("click", handler)
    group.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault()
        handler()
      }
    })
    root.appendChild(group)
  }

  /* Legend (wrapping) and notes. */
  const legend = svgEl("g", { "aria-hidden": "true", part: "legend" }, [])
  root.appendChild(legend)
  const legendTop = originY + gridH + 8
  const legendLeft = pad
  const rowWidths = new Array(legendRows).fill(0)
  legendItems.forEach((item) => {
    rowWidths[item.row] = Math.max(rowWidths[item.row], item.x + item.width - 14)
  })
  legendItems.forEach((item) => {
    const y = legendTop + item.row * LEGEND_ROW
    const rowLeft = pad + Math.max((availableW - rowWidths[item.row]) / 2, 0)
    legend.appendChild(svgEl("rect", {
      x: rowLeft + item.x, y: y, width: 10, height: 10, rx: 2, fill: item.entry.color
    }, []))
    legend.appendChild(svgEl("text", {
      x: rowLeft + item.x + 14, y: y + 9, "font-size": 11, fill: "var(--mj-text, #14181f)"
    }, item.text))
  })
  const notes = []
  if (perIcon > 1) {
    notes.push(`1 icon = ${formatNumber(perIcon)} units`)
  }
  if (overflow === true) {
    notes.push(`counts add up to ${formatNumber(sum)}, more than the total ${formatNumber(total)}`)
  }
  if (notes.length > 0) {
    legend.appendChild(svgEl("text", {
      x: legendLeft, y: legendTop + legendRows * LEGEND_ROW + 9, "font-size": 10,
      fill: "var(--mj-text-muted, #5f6673)"
    }, notes.join("; ")))
  }

  return root
}


registerRenderer("icon-array", render, { orientation: "horizontal" })
registerRenderer("waffle-pictograph", render, { orientation: "horizontal" })
