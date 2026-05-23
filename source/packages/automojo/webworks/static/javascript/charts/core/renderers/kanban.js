/*
 * kanban.js
 *
 * Kanban board renderer.
 *
 * Registers:
 *   "kanban" — WIP columns with item cards; each column shows a header, an
 *              optional WIP-limit indicator line, and stacked item cards with
 *              a priority-colour left stripe.
 *
 * ctx.raw shape:
 *   columns: [{ name, wip-limit?, items: [{ id, label, assignee?, priority? }] }]
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml } from "../svgdraw.js";
import { bandScale } from "../scales.js";


/* Priority → left-stripe color token. */
const PRIORITY_COLORS = {
  "critical": "var(--mj-color-danger, #b91c1c)",
  "high":     "var(--mj-color-warning, #b45309)",
  "medium":   "var(--mj-color-accent-500, #2563eb)",
  "low":      "var(--mj-color-neutral-500, #6b7280)"
};

const CARD_H = 48
const CARD_GAP = 6
const CARD_STRIPE_W = 4
const HEADER_H = 28
const COL_PADDING = 8


export function render(ctx) {
  /*
   * Render a Kanban board chart.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const raw = ctx.raw
  const columns = (raw !== null && raw !== undefined && Array.isArray(raw.columns))
    ? raw.columns : []

  const root = svgEl("g", { part: "plot" }, [])

  if (columns.length === 0) {
    return root
  }

  const margin = { top: 8, right: 8, bottom: 8, left: 8 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  const colNames = columns.map((col) => {
    const name = col.name !== undefined ? String(col.name) : ""
    return name
  })
  const colScale = bandScale(colNames, [0, plotW], 0.05)
  const colW = colScale.bandwidth()

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  for (let c = 0; c < columns.length; c = c + 1) {
    const col = columns[c]
    const colName = col.name !== undefined ? String(col.name) : ""
    const colX = colScale(colName)
    const items = Array.isArray(col.items) ? col.items : []
    const wipLimit = col["wip-limit"]

    /* Column background. */
    plot.appendChild(svgEl("rect", {
      x: colX, y: 0, width: colW, height: plotH, rx: 4,
      fill: "var(--mj-surface-alt, #f8f9fb)",
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))

    /* Column header. */
    const headerColor = ctx.colorFor(c)
    plot.appendChild(svgEl("rect", {
      x: colX, y: 0, width: colW, height: HEADER_H, rx: 4,
      fill: headerColor, "fill-opacity": 0.15
    }, []))
    plot.appendChild(svgEl("text", {
      x: colX + colW / 2, y: HEADER_H / 2 + 5,
      "text-anchor": "middle", "font-size": 12, "font-weight": "bold",
      fill: "var(--mj-text, #14181f)"
    }, escapeHtml(colName)))

    /* Item count badge. */
    const countText = String(items.length)
    const badgeX = colX + colW - 20
    const badgeY = HEADER_H / 2 - 8
    plot.appendChild(svgEl("rect", {
      x: badgeX, y: badgeY, width: 18, height: 16, rx: 8,
      fill: headerColor, "fill-opacity": 0.5
    }, []))
    plot.appendChild(svgEl("text", {
      x: badgeX + 9, y: badgeY + 11,
      "text-anchor": "middle", "font-size": 10,
      fill: "var(--mj-text, #14181f)"
    }, countText))

    /* WIP limit indicator. */
    if (wipLimit !== null && wipLimit !== undefined && typeof wipLimit === "number") {
      const wipY = HEADER_H + COL_PADDING + wipLimit * (CARD_H + CARD_GAP)
      const wipExceeded = items.length > wipLimit

      plot.appendChild(svgEl("line", {
        x1: colX + 2, y1: wipY, x2: colX + colW - 2, y2: wipY,
        stroke: wipExceeded
          ? "var(--mj-color-danger, #b91c1c)"
          : "var(--mj-color-warning, #b45309)",
        "stroke-width": 1.5,
        "stroke-dasharray": "4 2"
      }, []))

      if (wipExceeded === true) {
        const alertEl = svgEl("text", {
          x: colX + 4, y: wipY - 3,
          "font-size": 9,
          fill: "var(--mj-color-danger, #b91c1c)"
        }, `WIP limit: ${wipLimit}`)
        alertEl.setAttribute("role", "alert")
        alertEl.setAttribute("aria-label",
          `WIP limit exceeded: ${items.length} of ${wipLimit} allowed in ${escapeHtml(colName)}`)
        plot.appendChild(alertEl)
      }
    }

    /* Item cards. */
    for (let i = 0; i < items.length; i = i + 1) {
      const item = items[i]
      const cardX = colX + COL_PADDING
      const cardY = HEADER_H + COL_PADDING + i * (CARD_H + CARD_GAP)
      const cardW = colW - COL_PADDING * 2

      if (cardY + CARD_H > plotH - COL_PADDING) {
        /* Overflow indicator — more cards than visible. */
        plot.appendChild(svgEl("text", {
          x: colX + colW / 2,
          y: plotH - COL_PADDING,
          "text-anchor": "middle",
          "font-size": 10,
          fill: "var(--mj-text-muted, #6b7280)"
        }, `+${items.length - i} more`))
        break
      }

      const priority = item.priority !== undefined ? String(item.priority).toLowerCase() : ""
      const stripeColor = PRIORITY_COLORS[priority] !== undefined
        ? PRIORITY_COLORS[priority]
        : "var(--mj-color-neutral-500, #6b7280)"

      /* Card background. */
      const cardGroup = svgEl("g", { part: "card", tabindex: "0", role: "img" }, [])
      const itemLabel = item.label !== undefined ? String(item.label) : ""
      const itemId = item.id !== undefined ? String(item.id) : ""
      const assignee = item.assignee !== undefined && item.assignee !== null
        ? String(item.assignee) : ""
      const ariaLabel = [
        itemId, itemLabel, priority !== "" ? `priority: ${priority}` : "",
        assignee !== "" ? `assignee: ${assignee}` : ""
      ].filter((part) => part !== "").join(", ")
      cardGroup.setAttribute("aria-label", ariaLabel)
      cardGroup.appendChild(svgEl("title", null, ariaLabel))

      cardGroup.appendChild(svgEl("rect", {
        x: cardX, y: cardY, width: cardW, height: CARD_H, rx: 3,
        fill: "var(--mj-surface, #ffffff)",
        stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
      }, []))

      /* Priority stripe. */
      cardGroup.appendChild(svgEl("rect", {
        x: cardX, y: cardY,
        width: CARD_STRIPE_W, height: CARD_H, rx: 2,
        fill: stripeColor
      }, []))

      /* Item label. */
      const maxLabelW = cardW - CARD_STRIPE_W - 8
      cardGroup.appendChild(svgEl("text", {
        x: cardX + CARD_STRIPE_W + 6,
        y: cardY + 16,
        "font-size": 11,
        fill: "var(--mj-text, #14181f)",
        "clip-path": `inset(0 0 0 0)`
      }, escapeHtml(itemLabel.length > 30 ? itemLabel.slice(0, 28) + "…" : itemLabel)))

      /* Item ID. */
      if (itemId !== "") {
        cardGroup.appendChild(svgEl("text", {
          x: cardX + CARD_STRIPE_W + 6,
          y: cardY + 30,
          "font-size": 9,
          fill: "var(--mj-text-muted, #6b7280)"
        }, escapeHtml(itemId)))
      }

      /* Assignee. */
      if (assignee !== "") {
        cardGroup.appendChild(svgEl("text", {
          x: cardX + cardW - 4,
          y: cardY + 30,
          "text-anchor": "end",
          "font-size": 9,
          fill: "var(--mj-text-muted, #6b7280)"
        }, escapeHtml(assignee)))
      }

      const emitItem = item
      const emitColName = colName
      const clickHandler = () => {
        ctx.emit("mj-chart-card-click", {
          column: emitColName,
          id: emitItem.id,
          label: emitItem.label
        })
      }
      cardGroup.addEventListener("click", clickHandler)
      cardGroup.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault()
          clickHandler()
        }
      })

      plot.appendChild(cardGroup)
    }
  }

  return root
}


registerRenderer("kanban", render);
