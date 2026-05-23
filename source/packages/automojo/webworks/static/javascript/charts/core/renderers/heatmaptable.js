/*
 * heatmaptable.js
 *
 * Heatmap-table, bar-in-cell, and conditional-format-table renderers.
 * Each draws a value grid as pure SVG: <rect> cells with intensity fill,
 * in-cell bar marks, or rules-based highlight fills.
 *
 * Registered types:
 *   "heatmap-table"          – per-cell intensity fill (sequential/diverging)
 *   "bar-in-cell"            – horizontal bar inside each numeric cell
 *   "conditional-format-table" – rules-based highlight fill + icon glyph
 *
 * ctx.raw shape (shared envelope):
 *   raw.columns   [{key, label, type, render?, domain?}]
 *   raw.rows      [{[key]: value, ...}]
 *   raw.domain    [min, max]    (optional – auto-computed when absent)
 *   raw.colorScale "sequential" | "diverging"  (heatmap-table)
 *   raw.rules     [{column, op, value, style:{fill, icon}}] (cf-table)
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, formatNumber } from "../svgdraw.js";
import { linearScale } from "../scales.js";


/* ── colour helpers ────────────────────────────────────────────────────── */

const SEQ_LOW  = "var(--mj-color-accent-100, #dbeafe)"
const SEQ_HIGH = "var(--mj-color-accent-700, #1d4ed8)"
const DIV_LOW  = "var(--mj-color-danger,  #b91c1c)"
const DIV_MID  = "var(--mj-surface,       #ffffff)"
const DIV_HIGH = "var(--mj-color-success, #15803d)"


function _lerp(t, lo, hi) {
  /*
   * Linear interpolation between two hex/rgb colour strings – we use opacity
   * on a solid token background instead of true colour blending, since CSS
   * custom properties cannot be decomposed at JS runtime. We map `t` to an
   * opacity level and tint with the appropriate end-stop colour.
   *
   * :returns: An rgba() string.
   */
  const opacity = Math.max(0, Math.min(1, t))
  return opacity
}


function _seqFill(t) {
  /*
   * Sequential fill: white (t=0) → accent-700 (t=1) via opacity on accent-700.
   */
  const opacity = Math.max(0, Math.min(1, t))
  return `color-mix(in srgb, ${SEQ_HIGH} ${(opacity * 100).toFixed(1)}%, ${SEQ_LOW})`
}


function _divFill(t) {
  /*
   * Diverging fill: danger (t=0) → white (t=0.5) → success (t=1).
   */
  if (t <= 0.5) {
    const opacity = (0.5 - t) * 2
    return `color-mix(in srgb, ${DIV_LOW} ${(opacity * 100).toFixed(1)}%, ${DIV_MID})`
  }
  const opacity = (t - 0.5) * 2
  return `color-mix(in srgb, ${DIV_HIGH} ${(opacity * 100).toFixed(1)}%, ${DIV_MID})`
}


/* ── shared layout helpers ─────────────────────────────────────────────── */

const MARGIN = { top: 24, right: 8, bottom: 8, left: 8 }
const HEADER_H = 28
const ROW_H    = 28
const MIN_COL_W = 60


function _buildColumns(raw) {
  /*
   * Derive column descriptors from raw data.
   *
   * :returns: Array of column objects with key, label, type.
   */
  let columns = null
  if (raw !== null && raw !== undefined && Array.isArray(raw.columns) === true) {
    columns = raw.columns
  } else {
    columns = []
  }
  return columns
}


function _buildRows(raw) {
  /*
   * Derive row array from raw data.
   *
   * :returns: Array of row objects.
   */
  let rows = null
  if (raw !== null && raw !== undefined && Array.isArray(raw.rows) === true) {
    rows = raw.rows
  } else {
    rows = []
  }
  return rows
}


function _computeDomain(rows, columns) {
  /*
   * Auto-compute numeric domain across all numeric cells.
   *
   * :returns: [min, max].
   */
  let min = Infinity
  let max = -Infinity
  for (let r = 0; r < rows.length; r = r + 1) {
    for (let c = 0; c < columns.length; c = c + 1) {
      const col = columns[c]
      if (col.type !== "number") {
        continue
      }
      const v = rows[r][col.key]
      if (typeof v !== "number") {
        continue
      }
      if (v < min) {
        min = v
      }
      if (v > max) {
        max = v
      }
    }
  }
  if (min === Infinity) {
    return [0, 1]
  }
  if (min === max) {
    return [min - 1, max + 1]
  }
  return [min, max]
}


function _colWidths(columns, plotW) {
  /*
   * Distribute available width across columns, honouring minimum.
   *
   * :returns: Array of pixel widths, one per column.
   */
  const count = columns.length
  if (count === 0) {
    return []
  }
  const even = Math.max(plotW / count, MIN_COL_W)
  const widths = columns.map(() => even)
  return widths
}


/* ── icon paths ────────────────────────────────────────────────────────── */

function _iconPath(icon, cx, cy, size) {
  /*
   * Return a <path> SVG element for a named icon centred at (cx,cy).
   * Supported: "warning", "check", "info", "cross".
   *
   * :returns: SVGElement or null.
   */
  const s = size / 2
  let d = null
  if (icon === "warning") {
    d = `M${cx},${cy - s} L${cx + s},${cy + s} L${cx - s},${cy + s} Z`
  } else if (icon === "check") {
    d = `M${cx - s},${cy} L${cx - s * 0.2},${cy + s} L${cx + s},${cy - s}`
  } else if (icon === "cross") {
    d = `M${cx - s},${cy - s} L${cx + s},${cy + s} M${cx + s},${cy - s} L${cx - s},${cy + s}`
  } else if (icon === "info") {
    d = `M${cx},${cy - s} L${cx},${cy + s} M${cx},${cy - s * 1.5} L${cx},${cy - s * 1.1}`
  }
  if (d === null) {
    return null
  }
  const el = svgEl("path", {
    d: d,
    fill: "none",
    stroke: "var(--mj-text, #14181f)",
    "stroke-width": 1.5,
    "stroke-linecap": "round",
    "stroke-linejoin": "round"
  }, [])
  return el
}


/* ── heatmap-table renderer ─────────────────────────────────────────────── */

export function renderHeatmapTable(ctx) {
  /*
   * Render a heatmap table: value grid with per-cell intensity fill.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const raw = ctx.raw
  const root = svgEl("g", { part: "plot" }, [])

  const columns = _buildColumns(raw)
  const rows    = _buildRows(raw)

  if (columns.length === 0 || rows.length === 0) {
    return root
  }

  const colorScaleMode = (raw !== null && raw !== undefined && raw.colorScale)
    ? raw.colorScale
    : "sequential"

  let domainPair = null
  if (raw !== null && raw !== undefined && Array.isArray(raw.domain) === true) {
    domainPair = raw.domain
  } else {
    domainPair = _computeDomain(rows, columns)
  }

  const valScale = linearScale(domainPair, [0, 1])

  const plotW = Math.max(ctx.width  - MARGIN.left - MARGIN.right,  10)
  const colW  = _colWidths(columns, plotW)

  const plot = svgEl("g", {
    transform: `translate(${MARGIN.left},${MARGIN.top})`
  }, [])
  root.appendChild(plot)

  /* Column headers */
  let xCursor = 0
  for (let c = 0; c < columns.length; c = c + 1) {
    const col = columns[c]
    const cw  = colW[c]
    plot.appendChild(svgEl("rect", {
      x: xCursor, y: 0, width: cw, height: HEADER_H,
      fill: "var(--mj-surface-raised, #f3f4f6)",
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    plot.appendChild(svgEl("text", {
      x: xCursor + cw / 2, y: HEADER_H / 2 + 4,
      "text-anchor": "middle",
      "font-size": 11,
      "font-weight": "600",
      fill: "var(--mj-text, #14181f)"
    }, escapeHtml(col.label || col.key)))
    xCursor = xCursor + cw
  }

  /* Data rows */
  for (let r = 0; r < rows.length; r = r + 1) {
    const rowY = HEADER_H + r * ROW_H
    xCursor = 0

    for (let c = 0; c < columns.length; c = c + 1) {
      const col   = columns[c]
      const cw    = colW[c]
      const rawVal = rows[r][col.key]
      const isNum  = typeof rawVal === "number"

      /* Cell background */
      let fillColor = "var(--mj-surface, #ffffff)"
      if (isNum === true) {
        const t = valScale(rawVal)
        if (colorScaleMode === "diverging") {
          fillColor = _divFill(t)
        } else {
          fillColor = _seqFill(t)
        }
      }

      const cellRect = svgEl("rect", {
        x: xCursor, y: rowY, width: cw, height: ROW_H,
        fill: fillColor,
        stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
      }, [])
      const label = isNum ? formatNumber(rawVal) : escapeHtml(String(rawVal ?? ""))
      cellRect.setAttribute("part", "cell")
      cellRect.setAttribute("tabindex", "0")
      cellRect.setAttribute("role", "img")
      cellRect.setAttribute("aria-label", `${col.label || col.key}: ${label}`)
      cellRect.appendChild(svgEl("title", null, `${col.label || col.key}: ${label}`))
      const cellRow = r
      const cellCol = c
      const cellVal = rawVal
      const handler = () => {
        ctx.emit("mj-chart-cell-click", {
          row: cellRow, column: col.key, value: cellVal
        })
      }
      cellRect.addEventListener("click", handler)
      cellRect.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault()
          handler()
        }
      })
      plot.appendChild(cellRect)

      /* Value label */
      plot.appendChild(svgEl("text", {
        x: xCursor + cw / 2,
        y: rowY + ROW_H / 2 + 4,
        "text-anchor": "middle",
        "font-size": 10,
        fill: "var(--mj-text, #14181f)",
        "pointer-events": "none"
      }, label))

      xCursor = xCursor + cw
    }
  }

  return root
}


/* ── bar-in-cell renderer ───────────────────────────────────────────────── */

export function renderBarInCell(ctx) {
  /*
   * Render a bar-in-cell table: miniature horizontal bars inside numeric cells.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const raw = ctx.raw
  const root = svgEl("g", { part: "plot" }, [])

  const columns = _buildColumns(raw)
  const rows    = _buildRows(raw)

  if (columns.length === 0 || rows.length === 0) {
    return root
  }

  const plotW = Math.max(ctx.width - MARGIN.left - MARGIN.right, 10)
  const colW  = _colWidths(columns, plotW)

  const plot = svgEl("g", {
    transform: `translate(${MARGIN.left},${MARGIN.top})`
  }, [])
  root.appendChild(plot)

  /* Per-column domain pre-pass */
  const colDomains = {}
  for (let c = 0; c < columns.length; c = c + 1) {
    const col = columns[c]
    if (col.type !== "number") {
      continue
    }
    if (Array.isArray(col.domain) === true) {
      colDomains[col.key] = col.domain
      continue
    }
    /* Auto from rows */
    let lo = Infinity
    let hi = -Infinity
    for (let r = 0; r < rows.length; r = r + 1) {
      const v = rows[r][col.key]
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
    if (lo === Infinity) {
      colDomains[col.key] = [0, 1]
    } else if (lo === hi) {
      colDomains[col.key] = [lo - 1, hi + 1]
    } else {
      colDomains[col.key] = [lo, hi]
    }
  }

  /* Column headers */
  let xCursor = 0
  for (let c = 0; c < columns.length; c = c + 1) {
    const col = columns[c]
    const cw  = colW[c]
    plot.appendChild(svgEl("rect", {
      x: xCursor, y: 0, width: cw, height: HEADER_H,
      fill: "var(--mj-surface-raised, #f3f4f6)",
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    plot.appendChild(svgEl("text", {
      x: xCursor + cw / 2, y: HEADER_H / 2 + 4,
      "text-anchor": "middle",
      "font-size": 11,
      "font-weight": "600",
      fill: "var(--mj-text, #14181f)"
    }, escapeHtml(col.label || col.key)))
    xCursor = xCursor + cw
  }

  /* Data rows */
  for (let r = 0; r < rows.length; r = r + 1) {
    const rowY = HEADER_H + r * ROW_H
    xCursor = 0

    for (let c = 0; c < columns.length; c = c + 1) {
      const col    = columns[c]
      const cw     = colW[c]
      const rawVal = rows[r][col.key]
      const isNum  = typeof rawVal === "number"
      const isBar  = isNum === true && col.render === "bar"

      /* Cell background */
      const cellRect = svgEl("rect", {
        x: xCursor, y: rowY, width: cw, height: ROW_H,
        fill: "var(--mj-surface, #ffffff)",
        stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
      }, [])
      const label = isNum ? formatNumber(rawVal) : escapeHtml(String(rawVal ?? ""))
      cellRect.setAttribute("part", "cell")
      cellRect.setAttribute("tabindex", "0")
      cellRect.setAttribute("role", "img")
      cellRect.setAttribute("aria-label", `${col.label || col.key}: ${label}`)
      cellRect.appendChild(svgEl("title", null, `${col.label || col.key}: ${label}`))
      const cellRow = r
      const colKey  = col.key
      const cellVal = rawVal
      const handler = () => {
        ctx.emit("mj-chart-cell-click", {
          row: cellRow, column: colKey, value: cellVal
        })
      }
      cellRect.addEventListener("click", handler)
      cellRect.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault()
          handler()
        }
      })
      plot.appendChild(cellRect)

      if (isBar === true) {
        /* Bar track */
        const trackPad = 4
        const trackY   = rowY + trackPad
        const trackH   = ROW_H - trackPad * 2
        const trackW   = cw - trackPad * 2

        plot.appendChild(svgEl("rect", {
          x: xCursor + trackPad, y: trackY,
          width: trackW, height: trackH,
          fill: "var(--mj-surface-raised, #f3f4f6)",
          rx: 2,
          "pointer-events": "none"
        }, []))

        const dom  = colDomains[col.key] || [0, 1]
        const scale = linearScale(dom, [0, trackW])
        const zero  = Math.max(0, Math.min(trackW, scale(0)))
        const px    = Math.max(0, Math.min(trackW, scale(rawVal)))
        const barX  = xCursor + trackPad + Math.min(zero, px)
        const barW  = Math.abs(px - zero)

        plot.appendChild(svgEl("rect", {
          x: barX, y: trackY,
          width: Math.max(barW, 1), height: trackH,
          fill: "var(--mj-color-accent-500, #2563eb)",
          rx: 2,
          "pointer-events": "none"
        }, []))
      } else {
        /* Plain text label */
        plot.appendChild(svgEl("text", {
          x: xCursor + cw / 2,
          y: rowY + ROW_H / 2 + 4,
          "text-anchor": "middle",
          "font-size": 10,
          fill: "var(--mj-text, #14181f)",
          "pointer-events": "none"
        }, label))
      }

      xCursor = xCursor + cw
    }
  }

  return root
}


/* ── conditional-format-table renderer ─────────────────────────────────── */

function _evalRule(rule, value) {
  /*
   * Evaluate a single conditional-format rule against a value.
   *
   * :returns: true when the rule matches.
   */
  if (typeof value !== "number") {
    return false
  }
  const op  = rule.op
  const ref = rule.value
  if (op === "lt")  { return value < ref }
  if (op === "lte") { return value <= ref }
  if (op === "gt")  { return value > ref }
  if (op === "gte") { return value >= ref }
  if (op === "eq")  { return value === ref }
  if (op === "neq") { return value !== ref }
  return false
}


export function renderConditionalFormatTable(ctx) {
  /*
   * Render a conditional-format table with rules-based cell highlights.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const raw  = ctx.raw
  const root = svgEl("g", { part: "plot" }, [])

  const columns = _buildColumns(raw)
  const rows    = _buildRows(raw)
  const rules   = (raw !== null && raw !== undefined && Array.isArray(raw.rules))
    ? raw.rules
    : []

  if (columns.length === 0 || rows.length === 0) {
    return root
  }

  const plotW = Math.max(ctx.width - MARGIN.left - MARGIN.right, 10)
  const colW  = _colWidths(columns, plotW)

  const plot = svgEl("g", {
    transform: `translate(${MARGIN.left},${MARGIN.top})`
  }, [])
  root.appendChild(plot)

  /* Column headers */
  let xCursor = 0
  for (let c = 0; c < columns.length; c = c + 1) {
    const col = columns[c]
    const cw  = colW[c]
    plot.appendChild(svgEl("rect", {
      x: xCursor, y: 0, width: cw, height: HEADER_H,
      fill: "var(--mj-surface-raised, #f3f4f6)",
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    plot.appendChild(svgEl("text", {
      x: xCursor + cw / 2, y: HEADER_H / 2 + 4,
      "text-anchor": "middle",
      "font-size": 11,
      "font-weight": "600",
      fill: "var(--mj-text, #14181f)"
    }, escapeHtml(col.label || col.key)))
    xCursor = xCursor + cw
  }

  /* Data rows */
  for (let r = 0; r < rows.length; r = r + 1) {
    const rowY = HEADER_H + r * ROW_H
    xCursor = 0

    for (let c = 0; c < columns.length; c = c + 1) {
      const col    = columns[c]
      const cw     = colW[c]
      const rawVal = rows[r][col.key]
      const isNum  = typeof rawVal === "number"
      const label  = isNum ? formatNumber(rawVal) : escapeHtml(String(rawVal ?? ""))

      /* Find first matching rule for this column */
      let matchedRule = null
      for (let ri = 0; ri < rules.length; ri = ri + 1) {
        const rule = rules[ri]
        if (rule.column !== col.key) {
          continue
        }
        if (_evalRule(rule, rawVal) === true) {
          matchedRule = rule
          break
        }
      }

      const fillColor = (matchedRule !== null && matchedRule.style && matchedRule.style.fill)
        ? matchedRule.style.fill
        : "var(--mj-surface, #ffffff)"

      const cellRect = svgEl("rect", {
        x: xCursor, y: rowY, width: cw, height: ROW_H,
        fill: fillColor,
        stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
      }, [])

      const ruleState = matchedRule !== null
        ? ` — rule: ${matchedRule.op} ${matchedRule.value}`
        : ""
      cellRect.setAttribute("part", "cell")
      cellRect.setAttribute("tabindex", "0")
      cellRect.setAttribute("role", "img")
      cellRect.setAttribute("aria-label",
        `${col.label || col.key}: ${label}${ruleState}`)
      cellRect.appendChild(svgEl("title", null,
        `${col.label || col.key}: ${label}${ruleState}`))

      const cellRow = r
      const colKey  = col.key
      const cellVal = rawVal
      const handler = () => {
        ctx.emit("mj-chart-cell-click", {
          row: cellRow, column: colKey, value: cellVal
        })
      }
      cellRect.addEventListener("click", handler)
      cellRect.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault()
          handler()
        }
      })
      plot.appendChild(cellRect)

      /* Value text */
      plot.appendChild(svgEl("text", {
        x: xCursor + cw / 2,
        y: rowY + ROW_H / 2 + 4,
        "text-anchor": "middle",
        "font-size": 10,
        fill: "var(--mj-text, #14181f)",
        "pointer-events": "none"
      }, label))

      /* Rule icon */
      if (matchedRule !== null && matchedRule.style && matchedRule.style.icon) {
        const iconEl = _iconPath(
          matchedRule.style.icon,
          xCursor + cw - 12,
          rowY + ROW_H / 2,
          10
        )
        if (iconEl !== null) {
          iconEl.setAttribute("aria-hidden", "true")
          plot.appendChild(iconEl)
        }
      }

      xCursor = xCursor + cw
    }
  }

  return root
}


registerRenderer("heatmap-table",            renderHeatmapTable)
registerRenderer("bar-in-cell",              renderBarInCell)
registerRenderer("conditional-format-table", renderConditionalFormatTable)
