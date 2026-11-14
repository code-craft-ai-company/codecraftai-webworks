/*
 * kanban.js
 *
 * Kanban board renderer.
 *
 * Registers:
 *   "kanban" — WIP columns with item cards. Each column header shows the
 *              item count (and "count / limit" when the column has a WIP
 *              limit); a column over its limit is tinted, marked "over
 *              limit" and gets a dashed limit line under the last card
 *              within the limit. Cards carry a priority-colour stripe.
 *
 * ctx.raw shape:
 *   columns: [{ name, wip-limit?, items: [{ id, label, assignee?, priority? }] }]
 *
 * Layout:
 *   orientation="horizontal" (default) — columns side by side.
 *   orientation="vertical"             — columns stacked as rows with the
 *                                        cards flowing across (used
 *                                        automatically on narrow charts
 *                                        when no orientation is set).
 *   variant="count"                    — a bar per column of its item count
 *                                        with the WIP limit marked.
 * Cards that do not fit are summarised by a focusable "+N more" mark; every
 * card is listed in the data table.
 *
 * Events:
 *   mj-chart-card-click      { column, id, label }
 *   mj-chart-overflow-click  { column, hidden, items }
 *   mj-chart-column-click    { column, count, wipLimit }   (count variant)
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber } from "../svgdraw.js";
import { bandScale, linearScale, niceDomain, niceTicks } from "../scales.js";


/* Priority -> stripe colour (semantic, explained by the legend). */
const PRIORITY_COLORS = {
  "critical": "var(--mj-color-danger, #b91c1c)",
  "high":     "var(--mj-color-warning, #b45309)",
  "medium":   "var(--mj-accent, #2563eb)",
  "low":      "var(--mj-text-muted, #6b7280)"
};

const PRIORITY_LABELS = {
  "critical": "Critical",
  "high":     "High",
  "medium":   "Medium",
  "low":      "Low"
};

const OVER_COLOR = "var(--mj-color-danger, #b91c1c)";
const CARD_MAX_H = 48;
const CARD_MIN_H = 34;
const CARD_GAP = 6;
const CARD_STRIPE_W = 4;
const HEADER_H = 28;
const COL_PADDING = 8;
const LANE_CARD_W = 150;
const NARROW_WIDTH = 480;
const CHAR_WIDTH = 0.56;


function _textWidth(text, fontSize) {
  /*
   * Approximate rendered width of a label.
   */
  const width = String(text).length * fontSize * CHAR_WIDTH
  return width
}


function _fitText(text, maxWidth, fontSize) {
  /*
   * Shorten a label with an ellipsis so it fits a width ("" if hopeless).
   */
  const value = String(text)
  let fitted = value
  if (_textWidth(value, fontSize) > maxWidth) {
    const maxChars = Math.floor(maxWidth / (fontSize * CHAR_WIDTH)) - 1
    fitted = maxChars >= 2 ? value.slice(0, maxChars) + "…" : ""
  }
  return fitted
}


function _readColumns(rawColumns) {
  /*
   * Normalise the columns.
   *
   * :returns: [{ name, items, wipLimit, over }]
   */
  const list = Array.isArray(rawColumns) === true ? rawColumns : []
  const columns = []
  for (let c = 0; c < list.length; c = c + 1) {
    const col = list[c]
    if (col === null || typeof col !== "object") {
      continue
    }
    const items = Array.isArray(col.items) === true
      ? col.items.filter((item) => item !== null && typeof item === "object") : []
    const limitValue = Number(col["wip-limit"])
    const wipLimit = col["wip-limit"] !== null && col["wip-limit"] !== undefined &&
      col["wip-limit"] !== "" && Number.isFinite(limitValue) === true && limitValue >= 0
      ? limitValue : null
    columns.push({
      name: col.name !== undefined && col.name !== null ? String(col.name) : `Column ${c + 1}`,
      items: items,
      wipLimit: wipLimit,
      over: wipLimit !== null && items.length > wipLimit
    })
  }
  return columns
}


function _attachActivation(element, handler) {
  /*
   * Click and Enter / Space activation of a focusable mark.
   */
  element.addEventListener("click", handler)
  element.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault()
      handler()
    }
  })
  return
}


function _itemFacts(item) {
  /*
   * Display fields of one card.
   */
  const priority = item.priority !== undefined && item.priority !== null
    ? String(item.priority).toLowerCase() : ""
  const facts = {
    id: item.id !== undefined && item.id !== null ? String(item.id) : "",
    label: item.label !== undefined && item.label !== null ? String(item.label) : "",
    assignee: item.assignee !== undefined && item.assignee !== null ? String(item.assignee) : "",
    priority: priority,
    stripe: PRIORITY_COLORS[priority] !== undefined ? PRIORITY_COLORS[priority] : "var(--mj-border-strong, #c7ccd6)"
  }
  return facts
}


function _drawCard(item, columnName, box, clipId, ctx, priorities) {
  /*
   * One focusable card; its text is clipped to the card.
   */
  const facts = _itemFacts(item)
  if (PRIORITY_COLORS[facts.priority] !== undefined && priorities.indexOf(facts.priority) < 0) {
    priorities.push(facts.priority)
  }
  const ariaLabel = [
    facts.id, facts.label, facts.priority !== "" ? `priority ${facts.priority}` : "",
    facts.assignee !== "" ? `assignee ${facts.assignee}` : ""
  ].filter((part) => part !== "").join(", ")

  const card = svgEl("g", { part: "card", tabindex: "0", role: "img", "aria-label": ariaLabel }, [])
  card.appendChild(svgEl("title", null, ariaLabel))

  const clip = svgEl("clipPath", { id: clipId }, [
    svgEl("rect", { x: box.x, y: box.y, width: box.w, height: box.h, rx: 3 }, [])
  ])
  card.appendChild(clip)
  card.appendChild(svgEl("rect", {
    x: box.x, y: box.y, width: box.w, height: box.h, rx: 3,
    fill: "var(--mj-surface, #ffffff)",
    stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
  }, []))
  card.appendChild(svgEl("rect", {
    x: box.x, y: box.y, width: CARD_STRIPE_W, height: box.h,
    fill: facts.stripe, "clip-path": `url(#${clipId})`
  }, []))

  const textX = box.x + CARD_STRIPE_W + 6
  const textW = box.w - CARD_STRIPE_W - 10
  const text = svgEl("g", { "clip-path": `url(#${clipId})`, "aria-hidden": "true" }, [])
  text.appendChild(svgEl("text", {
    x: textX, y: box.y + Math.min(16, box.h * 0.42), "font-size": 11, fill: "var(--mj-text, #14181f)"
  }, _fitText(facts.label, textW, 11)))

  /* Id on the left and assignee on the right of the second line. */
  const secondY = box.y + Math.min(box.h - 7, 31)
  const idText = _fitText(facts.id, textW * 0.45, 9)
  if (idText !== "") {
    text.appendChild(svgEl("text", {
      x: textX, y: secondY, "font-size": 9, fill: "var(--mj-text-muted, #6b7280)"
    }, idText))
  }
  if (facts.assignee !== "") {
    const room = idText !== "" ? textW - _textWidth(idText, 9) - 8 : textW
    const assigneeText = _fitText(facts.assignee, room, 9)
    if (assigneeText !== "") {
      text.appendChild(svgEl("text", {
        x: box.x + box.w - 5, y: secondY, "text-anchor": "end",
        "font-size": 9, fill: "var(--mj-text-muted, #6b7280)"
      }, assigneeText))
    }
  }
  card.appendChild(text)

  _attachActivation(card, () => {
    ctx.emit("mj-chart-card-click", { column: columnName, id: item.id, label: item.label })
  })
  return card
}


function _drawOverflow(column, hidden, x, y, width, ctx) {
  /*
   * The focusable "+N more" mark for cards that do not fit.
   */
  const names = column.items.slice(column.items.length - hidden)
    .map((item) => _itemFacts(item).label).filter((label) => label !== "")
  const ariaLabel = `${hidden} more in ${column.name}: ${names.join(", ")}`
  const mark = svgEl("g", { part: "overflow", tabindex: "0", role: "img", "aria-label": ariaLabel }, [])
  mark.appendChild(svgEl("title", null, ariaLabel))
  mark.appendChild(svgEl("rect", {
    x: x, y: y - 12, width: width, height: 16, rx: 8,
    fill: "var(--mj-bg-muted, #eef0f3)"
  }, []))
  mark.appendChild(svgEl("text", {
    x: x + width / 2, y: y, "text-anchor": "middle", "font-size": 10,
    fill: "var(--mj-text, #14181f)"
  }, `+${hidden} more`))
  _attachActivation(mark, () => {
    ctx.emit("mj-chart-overflow-click", {
      column: column.name,
      hidden: hidden,
      items: column.items.slice(column.items.length - hidden)
    })
  })
  return mark
}


function _headerText(column) {
  /*
   * "Review 2 / 2" or "Backlog 3"; "over limit" when the limit is exceeded.
   */
  const count = column.wipLimit !== null
    ? `${column.items.length} / ${formatNumber(column.wipLimit)}`
    : String(column.items.length)
  const text = { name: column.name, count: column.over === true ? `${count} over limit` : count }
  return text
}


function _drawColumns(ctx, columns, plot, plotW, plotH, priorities) {
  /*
   * Columns side by side (the default layout).
   */
  const colScale = bandScale(columns.map((col, index) => index), [0, plotW], 0.05)
  const colW = colScale.bandwidth()
  const decor = svgEl("g", { "aria-hidden": "true" }, [])
  const marks = svgEl("g", null, [])
  const overlay = svgEl("g", { "aria-hidden": "true" }, [])
  plot.appendChild(decor)
  plot.appendChild(marks)
  plot.appendChild(overlay)

  for (let c = 0; c < columns.length; c = c + 1) {
    const column = columns[c]
    const colX = colScale.at(c)
    const header = _headerText(column)

    decor.appendChild(svgEl("rect", {
      x: colX, y: 0, width: colW, height: plotH, rx: 4,
      fill: column.over === true ? "var(--mj-color-danger-surface, #fdecec)" : "var(--mj-bg-subtle, #f8f9fb)",
      stroke: column.over === true ? OVER_COLOR : "var(--mj-border, #e0e3e9)",
      "stroke-width": column.over === true ? 1.5 : 1
    }, []))
    decor.appendChild(svgEl("rect", {
      x: colX, y: 0, width: colW, height: HEADER_H, rx: 4,
      fill: "var(--mj-bg-muted, #eef0f3)"
    }, []))
    const countW = _textWidth(header.count, 10) + 10
    decor.appendChild(svgEl("text", {
      x: colX + 8, y: HEADER_H / 2 + 4, "font-size": 12, "font-weight": "bold",
      fill: "var(--mj-text, #14181f)"
    }, _fitText(header.name, colW - countW - 16, 12)))
    decor.appendChild(svgEl("text", {
      x: colX + colW - 8, y: HEADER_H / 2 + 4, "text-anchor": "end", "font-size": 10,
      "font-weight": column.over === true ? "bold" : "normal",
      fill: column.over === true ? OVER_COLOR : "var(--mj-text-muted, #6b7280)"
    }, _fitText(header.count, Math.max(colW - 40, 20), 10)))

    /* Cards shrink to fit before any are hidden. */
    const available = plotH - HEADER_H - COL_PADDING * 2
    const count = column.items.length
    let cardH = CARD_MAX_H
    if (count > 0) {
      cardH = Math.min(Math.max((available + CARD_GAP) / count - CARD_GAP, CARD_MIN_H), CARD_MAX_H)
    }
    let fits = Math.max(Math.floor((available + CARD_GAP) / (cardH + CARD_GAP)), 0)
    if (fits < count) {
      fits = Math.max(Math.floor((available - 20 + CARD_GAP) / (cardH + CARD_GAP)), 0)
    }
    const shown = Math.min(fits, count)
    const cardW = colW - COL_PADDING * 2

    for (let i = 0; i < shown; i = i + 1) {
      const box = { x: colX + COL_PADDING, y: HEADER_H + COL_PADDING + i * (cardH + CARD_GAP), w: cardW, h: cardH }
      marks.appendChild(_drawCard(column.items[i], column.name, box, `mj-kanban-clip-${c}-${i}`, ctx, priorities))
    }
    if (shown < count) {
      const y = HEADER_H + COL_PADDING + shown * (cardH + CARD_GAP) + 12
      marks.appendChild(_drawOverflow(column, count - shown, colX + COL_PADDING, y, cardW, ctx))
    }

    /* WIP limit line, drawn over the cards under the last allowed one. */
    if (column.over === true && column.wipLimit > 0 && column.wipLimit <= shown) {
      const wipY = HEADER_H + COL_PADDING + column.wipLimit * (cardH + CARD_GAP) - CARD_GAP / 2
      overlay.appendChild(svgEl("line", {
        x1: colX + 2, y1: wipY, x2: colX + colW - 2, y2: wipY,
        stroke: OVER_COLOR, "stroke-width": 2, "stroke-dasharray": "5 3"
      }, []))
    }
  }
  return
}


function _drawLanes(ctx, columns, plot, plotW, plotH, priorities) {
  /*
   * Columns stacked as rows; cards flow left to right (narrow charts).
   */
  const laneScale = bandScale(columns.map((col, index) => index), [0, plotH], 0.08)
  const laneH = laneScale.bandwidth()
  const decor = svgEl("g", { "aria-hidden": "true" }, [])
  const marks = svgEl("g", null, [])
  plot.appendChild(decor)
  plot.appendChild(marks)
  const titleH = 20

  for (let c = 0; c < columns.length; c = c + 1) {
    const column = columns[c]
    const laneY = laneScale.at(c)
    const header = _headerText(column)
    decor.appendChild(svgEl("rect", {
      x: 0, y: laneY, width: plotW, height: laneH, rx: 4,
      fill: column.over === true ? "var(--mj-color-danger-surface, #fdecec)" : "var(--mj-bg-subtle, #f8f9fb)",
      stroke: column.over === true ? OVER_COLOR : "var(--mj-border, #e0e3e9)",
      "stroke-width": column.over === true ? 1.5 : 1
    }, []))
    decor.appendChild(svgEl("text", {
      x: 8, y: laneY + 14, "font-size": 11, "font-weight": "bold", fill: "var(--mj-text, #14181f)"
    }, _fitText(`${header.name}  ${header.count}`, plotW - 16, 11)))

    const cardH = Math.min(Math.max(laneH - titleH - 6, 0), CARD_MAX_H)
    if (cardH < 24) {
      continue
    }
    const cardW = Math.min(LANE_CARD_W, plotW - 16)
    const count = column.items.length
    let fits = Math.max(Math.floor((plotW - 16 + CARD_GAP) / (cardW + CARD_GAP)), 0)
    if (fits < count) {
      fits = Math.max(Math.floor((plotW - 16 - 70 + CARD_GAP) / (cardW + CARD_GAP)), 0)
    }
    const shown = Math.min(fits, count)
    for (let i = 0; i < shown; i = i + 1) {
      const box = { x: 8 + i * (cardW + CARD_GAP), y: laneY + titleH, w: cardW, h: cardH }
      marks.appendChild(_drawCard(column.items[i], column.name, box, `mj-kanban-clip-${c}-${i}`, ctx, priorities))
    }
    if (shown < count) {
      const x = 8 + shown * (cardW + CARD_GAP)
      marks.appendChild(_drawOverflow(column, count - shown, x, laneY + titleH + cardH / 2 + 4, 64, ctx))
    }
  }
  return
}


function _drawCounts(ctx, columns, plot, plotW, plotH) {
  /*
   * Count-only variant: a bar per column with its WIP limit marked.
   */
  let maxCount = 1
  for (let c = 0; c < columns.length; c = c + 1) {
    maxCount = Math.max(maxCount, columns[c].items.length,
      columns[c].wipLimit !== null ? columns[c].wipLimit : 0)
  }
  const domain = niceDomain(0, maxCount, 5)
  const valueScale = linearScale(domain, [plotH, 0])
  const colScale = bandScale(columns.map((col, index) => index), [0, plotW], 0.3)
  const bandwidth = colScale.bandwidth()
  const axis = svgEl("g", { "aria-hidden": "true" }, [])
  const marks = svgEl("g", null, [])
  const overlay = svgEl("g", { "aria-hidden": "true" }, [])
  plot.appendChild(axis)
  plot.appendChild(marks)
  plot.appendChild(overlay)

  const ticks = niceTicks(domain[0], domain[1], 5)
  for (let t = 0; t < ticks.length; t = t + 1) {
    const y = valueScale(ticks[t])
    axis.appendChild(svgEl("line", {
      x1: 0, y1: y, x2: plotW, y2: y, stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    axis.appendChild(svgEl("text", {
      x: -8, y: y + 4, "text-anchor": "end", "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
    }, formatNumber(ticks[t])))
  }

  for (let c = 0; c < columns.length; c = c + 1) {
    const column = columns[c]
    const x = colScale.at(c)
    const y = valueScale(column.items.length)
    const color = column.over === true ? OVER_COLOR : ctx.colorFor(0)
    const ariaLabel = `${column.name}: ${column.items.length} items` +
      (column.wipLimit !== null ? `, WIP limit ${formatNumber(column.wipLimit)}` : "") +
      (column.over === true ? ", over limit" : "")
    const bar = svgEl("rect", {
      x: x, y: y, width: bandwidth, height: Math.max(plotH - y, 0), rx: 2,
      fill: color, part: "bar", tabindex: "0", role: "img", "aria-label": ariaLabel
    }, [])
    bar.appendChild(svgEl("title", null, ariaLabel))
    const emitColumn = column
    _attachActivation(bar, () => {
      ctx.emit("mj-chart-column-click", {
        column: emitColumn.name, count: emitColumn.items.length, wipLimit: emitColumn.wipLimit
      })
    })
    marks.appendChild(bar)
    axis.appendChild(svgEl("text", {
      x: x + bandwidth / 2, y: y - 4, "text-anchor": "middle", "font-size": 11,
      fill: "var(--mj-text, #14181f)"
    }, String(column.items.length)))
    axis.appendChild(svgEl("text", {
      x: x + bandwidth / 2, y: plotH + 16, "text-anchor": "middle", "font-size": 11,
      fill: "var(--mj-text, #14181f)"
    }, _fitText(column.name, colScale.step() - 4, 11)))
    if (column.wipLimit !== null) {
      const limitY = valueScale(column.wipLimit)
      overlay.appendChild(svgEl("line", {
        x1: x - 4, y1: limitY, x2: x + bandwidth + 4, y2: limitY,
        stroke: "var(--mj-text, #14181f)", "stroke-width": 2, "stroke-dasharray": "5 3"
      }, []))
    }
  }
  axis.appendChild(svgEl("line", {
    x1: 0, y1: plotH, x2: plotW, y2: plotH, stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
  }, []))
  return
}


export function render(ctx) {
  /*
   * Render a Kanban board chart.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const raw = ctx.raw
  const columns = _readColumns(raw !== null && raw !== undefined ? raw.columns : null)

  const root = svgEl("g", { part: "plot" }, [])

  /* Accessible table: one row per card. */
  const tableRows = []
  for (let c = 0; c < columns.length; c = c + 1) {
    const column = columns[c]
    const limitText = column.wipLimit !== null
      ? `${column.items.length} / ${formatNumber(column.wipLimit)}${column.over === true ? " (over limit)" : ""}`
      : String(column.items.length)
    if (column.items.length === 0) {
      tableRows.push([column.name, limitText, "", "", "", ""])
    }
    for (let i = 0; i < column.items.length; i = i + 1) {
      const facts = _itemFacts(column.items[i])
      tableRows.push([column.name, limitText, facts.id, facts.label, facts.priority, facts.assignee])
    }
  }
  ctx.setTable({ columns: ["Column", "Items / WIP limit", "Id", "Card", "Priority", "Assignee"], rows: tableRows })

  if (columns.length === 0) {
    return root
  }

  const variant = ctx.attrs("style", "")
  const explicitOrientation = ctx.attrs("orientation", null)
  const vertical = ctx.orientation === "vertical" ||
    (explicitOrientation === null && ctx.width < NARROW_WIDTH && columns.length > 2)

  const countOnly = variant === "count"
  const margin = countOnly === true
    ? { top: 16, right: 16, bottom: 28, left: 40 }
    : { top: 8, right: 8, bottom: 8, left: 8 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  const priorities = []
  if (countOnly === true) {
    _drawCounts(ctx, columns, plot, plotW, plotH)
  } else if (vertical === true) {
    _drawLanes(ctx, columns, plot, plotW, plotH, priorities)
  } else {
    _drawColumns(ctx, columns, plot, plotW, plotH, priorities)
  }

  /* Legend: the priority stripes in use (over-limit columns say so in text). */
  const legend = []
  const order = Object.keys(PRIORITY_COLORS)
  for (let p = 0; p < order.length; p = p + 1) {
    if (priorities.indexOf(order[p]) >= 0) {
      legend.push({ label: `${PRIORITY_LABELS[order[p]]} priority`, color: PRIORITY_COLORS[order[p]] })
    }
  }
  ctx.setLegend(legend)

  return root
}


registerRenderer("kanban", render, { orientation: "horizontal", minHeight: 320 });
