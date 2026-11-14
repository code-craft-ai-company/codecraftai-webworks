/*
 * waffle.js
 *
 * Waffle (unit grid) renderer.
 *
 * Registers: "waffle"
 *
 * ctx.model.categories        -- category labels
 * ctx.model.series[0].values  -- amount per category (value i belongs to
 *                                category i; values past the categories are
 *                                ignored). When the values sum to cols*rows
 *                                each value is a cell count; otherwise the
 *                                cells are shared out proportionally with the
 *                                largest-remainder method, so the grid is
 *                                always exactly full.
 * ctx.model.meta.grid         -- optional { cols, rows }; default 10x10
 *
 * Cells are square and laid out in reading order (left to right, top to
 * bottom), coloured per category (ctx.colorFor(categoryIndex)). A key beside
 * the grid (below it when the plot is narrow) names each category with its
 * share; the legend lists the same entries. Each category's cells form one
 * focusable group, and hovering or focusing a group highlights its cells.
 *
 * Null and non-numeric values are gaps (no cells); negative values are
 * invalid: they get no cells and the chart emits `mj-chart-error`.
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber } from "../svgdraw.js";


const MARGIN = 12;
const MAX_CELLS = 2500;
const MAX_SIDE = 100;
const MAX_CELL = 32;
const KEY_FONT = 12;
const KEY_LINE = 20;
const KEY_SWATCH = 12;
const DIMMED_OPACITY = "0.25";


function _textWidth(text, fontSize) {
  /*
   * Estimate the rendered width of a label.
   */
  const width = String(text).length * fontSize * 0.58
  return width
}


function _fitText(text, maxWidth, fontSize) {
  /*
   * Shorten a label with an ellipsis so it fits a width.
   */
  const label = String(text)
  if (_textWidth(label, fontSize) <= maxWidth) {
    return label
  }
  const characters = Math.floor(maxWidth / (fontSize * 0.58)) - 1
  if (characters < 2) {
    return ""
  }
  const fitted = label.slice(0, characters) + "…"
  return fitted
}


function _gridSize(meta) {
  /*
   * The grid's columns and rows from meta.grid (whole numbers, default 10),
   * capped so a typo cannot ask for millions of cells.
   */
  const grid = meta !== null && meta !== undefined && meta.grid !== null && typeof meta.grid === "object"
    ? meta.grid
    : {}
  let cols = typeof grid.cols === "number" && Number.isFinite(grid.cols) === true && grid.cols >= 1
    ? Math.floor(grid.cols)
    : 10
  let rows = typeof grid.rows === "number" && Number.isFinite(grid.rows) === true && grid.rows >= 1
    ? Math.floor(grid.rows)
    : 10
  cols = Math.min(cols, MAX_SIDE)
  rows = Math.min(rows, MAX_SIDE, Math.max(Math.floor(MAX_CELLS / cols), 1))
  const size = { cols: cols, rows: rows }
  return size
}


function _allocateCells(amounts, totalCells) {
  /*
   * Share the grid's cells out over the categories by largest remainder.
   *
   * :param amounts: Non-negative amount per category.
   * :param totalCells: Number of cells in the grid.
   * :returns: Cell count per category (sums to totalCells when any amount
   *     is positive, else all zero).
   */
  let sum = 0
  for (let index = 0; index < amounts.length; index = index + 1) {
    sum = sum + amounts[index]
  }
  const counts = amounts.map(() => 0)
  if (sum <= 0) {
    return counts
  }

  const shares = []
  let assigned = 0
  for (let index = 0; index < amounts.length; index = index + 1) {
    const exact = (amounts[index] / sum) * totalCells
    const floored = Math.floor(exact)
    counts[index] = floored
    assigned = assigned + floored
    shares.push({ index: index, remainder: exact - floored })
  }

  shares.sort((a, b) => b.remainder - a.remainder || a.index - b.index)
  const remaining = Math.min(totalCells - assigned, shares.length)
  for (let step = 0; step < remaining; step = step + 1) {
    counts[shares[step].index] = counts[shares[step].index] + 1
  }
  return counts
}


export function render(ctx) {
  /*
   * Render a waffle chart.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const model = ctx.model
  const root = svgEl("g", { part: "plot" }, [])

  const categories = model.categories
  const series = model.series
  if (categories.length === 0 || series.length === 0) {
    return root
  }

  const values = series[0].values
  const size = _gridSize(model.meta)
  const totalCells = size.cols * size.rows

  /* One amount per category; gaps and invalid values count as none. */
  const amounts = []
  const negatives = []
  let total = 0
  for (let index = 0; index < categories.length; index = index + 1) {
    const value = values[index]
    let amount = 0
    if (typeof value === "number" && Number.isFinite(value) === true) {
      if (value < 0) {
        negatives.push(String(categories[index]))
      } else {
        amount = value
      }
    }
    amounts.push(amount)
    total = total + amount
  }
  if (negatives.length > 0) {
    ctx.emit("mj-chart-error", {
      message: `waffle: negative values are not drawn (${negatives.join(", ")})`
    })
  }
  if (total <= 0) {
    return root
  }

  const counts = _allocateCells(amounts, totalCells)
  const groups = []
  for (let index = 0; index < categories.length; index = index + 1) {
    if (counts[index] === 0 && amounts[index] === 0) {
      continue
    }
    groups.push({
      index: index,
      label: String(categories[index]),
      value: amounts[index],
      fraction: amounts[index] / total,
      share: `${formatNumber((amounts[index] / total) * 100, { maximumFractionDigits: 1 })}%`,
      cells: counts[index],
      color: ctx.colorFor(index)
    })
  }

  ctx.setLegend(groups.map((group) => {
    return { label: group.label, color: group.color }
  }))
  ctx.setTable({
    columns: ["Category", String(series[0].name || "Value"), "Share", "Cells"],
    rows: groups.map((group) => {
      return [group.label, group.value, group.share, group.cells]
    })
  })

  /* Key placement: beside the grid when that leaves it big enough. */
  let keyWidth = 0
  for (let index = 0; index < groups.length; index = index + 1) {
    const text = `${groups[index].label} ${groups[index].share}`
    keyWidth = Math.max(keyWidth, KEY_SWATCH + 8 + _textWidth(text, KEY_FONT))
  }
  const availW = Math.max(ctx.width - MARGIN * 2, size.cols)
  const availH = Math.max(ctx.height - MARGIN * 2, size.rows)
  const keyBeside = Math.min(keyWidth, availW * 0.4)
  const besideCell = Math.min((availW - keyBeside - 24) / size.cols, availH / size.rows)
  const keyBelowH = groups.length * KEY_LINE
  const belowCell = Math.min(availW / size.cols, (availH - keyBelowH - 8) / size.rows)
  const keyOnSide = besideCell >= belowCell || besideCell >= 12

  const cell = Math.min(Math.max(keyOnSide === true ? besideCell : belowCell, 2), MAX_CELL)
  const gridW = cell * size.cols
  const gridH = cell * size.rows
  const blockW = keyOnSide === true ? gridW + 24 + keyBeside : Math.max(gridW, keyBeside)
  const blockH = keyOnSide === true ? Math.max(gridH, keyBelowH) : gridH + 8 + keyBelowH
  const originX = MARGIN + Math.max((availW - blockW) / 2, 0)
  const originY = MARGIN + Math.max((availH - blockH) / 2, 0)
  const gridX = keyOnSide === true ? originX : originX + Math.max((blockW - gridW) / 2, 0)
  const gap = Math.min(Math.max(cell * 0.12, 1), 3)
  const side = Math.max(cell - gap, 1)

  const grid = svgEl("g", { part: "grid", transform: `translate(${gridX.toFixed(2)},${originY.toFixed(2)})` }, [])
  root.appendChild(grid)

  /* Highlight one category's cells while it is hovered or focused. */
  const groupElements = []
  const highlight = (active) => {
    for (let index = 0; index < groupElements.length; index = index + 1) {
      const element = groupElements[index]
      if (active === null || element === active) {
        element.removeAttribute("fill-opacity")
      } else {
        element.setAttribute("fill-opacity", DIMMED_OPACITY)
      }
    }
  }

  let cellIndex = 0
  for (let groupIndex = 0; groupIndex < groups.length; groupIndex = groupIndex + 1) {
    const group = groups[groupIndex]
    const share = group.share
    const description = `${group.label}: ${formatNumber(group.value)} (${share}, ${group.cells} of ${totalCells} cells)`

    const element = svgEl("g", {
      part: "category",
      fill: group.color,
      tabindex: "0",
      role: "img",
      "aria-label": description
    }, [svgEl("title", null, description)])

    for (let count = 0; count < group.cells; count = count + 1) {
      const col = cellIndex % size.cols
      const row = Math.floor(cellIndex / size.cols)
      element.appendChild(svgEl("rect", {
        x: (col * cell + gap / 2).toFixed(2),
        y: (row * cell + gap / 2).toFixed(2),
        width: side.toFixed(2),
        height: side.toFixed(2),
        rx: (side * 0.15).toFixed(2),
        part: "cell"
      }, []))
      cellIndex = cellIndex + 1
    }

    const handler = () => {
      ctx.emit("mj-chart-cell-click", {
        category: group.label,
        value: group.value,
        fraction: group.fraction
      })
    }
    element.addEventListener("click", handler)
    element.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault()
        handler()
      }
    })
    element.addEventListener("pointerenter", () => highlight(element))
    element.addEventListener("pointerleave", () => highlight(null))
    element.addEventListener("focus", () => highlight(element))
    element.addEventListener("blur", () => highlight(null))

    groupElements.push(element)
    grid.appendChild(element)
  }

  /* Key: swatch, name and share per category. */
  const keyX = keyOnSide === true ? originX + gridW + 24 : originX + Math.max((blockW - keyBeside) / 2, 0)
  const keyY = keyOnSide === true
    ? originY + Math.max((gridH - keyBelowH) / 2, 0)
    : originY + gridH + 8
  const key = svgEl("g", { "aria-hidden": "true", transform: `translate(${keyX.toFixed(2)},${keyY.toFixed(2)})` }, [])
  root.appendChild(key)
  for (let groupIndex = 0; groupIndex < groups.length; groupIndex = groupIndex + 1) {
    const group = groups[groupIndex]
    const y = groupIndex * KEY_LINE + KEY_LINE / 2
    const share = group.share
    const room = keyBeside - KEY_SWATCH - 8 - _textWidth(` ${share}`, KEY_FONT)
    key.appendChild(svgEl("rect", {
      x: 0, y: (y - KEY_SWATCH / 2).toFixed(2),
      width: KEY_SWATCH, height: KEY_SWATCH, rx: 2,
      fill: group.color
    }, []))
    key.appendChild(svgEl("text", {
      x: KEY_SWATCH + 8, y: y.toFixed(2),
      "dominant-baseline": "middle",
      "font-size": KEY_FONT,
      fill: "var(--mj-text, #14181f)"
    }, [
      `${_fitText(group.label, room, KEY_FONT)} `,
      svgEl("tspan", { "font-weight": "600" }, share)
    ]))
  }

  return root
}


function _isEmpty(model) {
  /*
   * Nothing to draw: no category has a positive amount.
   */
  if (model.series.length === 0 || model.categories.length === 0) {
    return true
  }
  const values = model.series[0].values
  for (let index = 0; index < model.categories.length; index = index + 1) {
    const value = values[index]
    if (typeof value === "number" && Number.isFinite(value) === true && value > 0) {
      return false
    }
  }
  return true
}


registerRenderer("waffle", render, { legend: "categories", isEmpty: _isEmpty });
