/*
 * calendarheatmap.js
 *
 * Calendar-heatmap renderer — days-of-year grid coloured by value,
 * laid out in the standard GitHub-style week-column × day-row grid.
 *
 * Registered types:
 *   "calendar-heatmap"
 *
 * ctx.raw shape:
 *   raw.years        [number]         years to render (default: current year)
 *   raw.data         [{date, value}]  date strings "YYYY-MM-DD"
 *   raw.domain       [min, max]       optional; auto-computed when absent
 *   raw.colorScale   "sequential" | "diverging"
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, formatNumber } from "../svgdraw.js";
import { linearScale } from "../scales.js";


/* ── colour helpers (mirrors heatmaptable.js) ─────────────────────────── */

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


/* ── date helpers ─────────────────────────────────────────────────────── */

function _dateKey(date) {
  /*
   * Produce a "YYYY-MM-DD" string from a Date.
   */
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, "0")
  const d = String(date.getDate()).padStart(2, "0")
  return `${y}-${m}-${d}`
}


function _firstMonday(year) {
  /*
   * Return the Monday on or before Jan 1 of `year` so the grid starts
   * at a full week boundary.
   */
  const jan1   = new Date(year, 0, 1)
  const dow    = jan1.getDay()            // 0=Sun … 6=Sat
  const offset = dow === 0 ? -6 : 1 - dow // shift back to Monday
  const monday = new Date(jan1)
  monday.setDate(jan1.getDate() + offset)
  return monday
}


const MONTH_ABBR = ["Jan","Feb","Mar","Apr","May","Jun",
                    "Jul","Aug","Sep","Oct","Nov","Dec"]
const DOW_ABBR   = ["M","T","W","T","F","S","S"]


/* ── renderer ─────────────────────────────────────────────────────────── */

export function render(ctx) {
  /*
   * Render a calendar heatmap.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const raw  = ctx.raw
  const root = svgEl("g", { part: "plot" }, [])

  /* Resolve years */
  let years = null
  if (raw !== null && raw !== undefined && Array.isArray(raw.years) === true) {
    years = raw.years
  } else {
    years = [new Date().getFullYear()]
  }

  /* Build value lookup */
  const valueMap = {}
  if (raw !== null && raw !== undefined && Array.isArray(raw.data) === true) {
    for (let i = 0; i < raw.data.length; i = i + 1) {
      const entry = raw.data[i]
      if (entry !== null && entry !== undefined && entry.date) {
        valueMap[String(entry.date)] = entry.value
      }
    }
  }

  /* Domain */
  let domainPair = null
  if (raw !== null && raw !== undefined && Array.isArray(raw.domain) === true) {
    domainPair = raw.domain
  } else {
    const vals = Object.values(valueMap).filter((v) => typeof v === "number")
    if (vals.length === 0) {
      domainPair = [0, 1]
    } else {
      const lo = Math.min(...vals)
      const hi = Math.max(...vals)
      domainPair = lo === hi ? [lo - 1, hi + 1] : [lo, hi]
    }
  }

  const colorScaleMode = (raw !== null && raw !== undefined && raw.colorScale)
    ? raw.colorScale
    : "sequential"
  const valScale = linearScale(domainPair, [0, 1])

  const horizontal = ctx.orientation !== "vertical"

  /* Layout: one year block stacked vertically */
  const margin   = { top: 8, right: 8, bottom: 8, left: 8 }
  const plotW    = Math.max(ctx.width  - margin.left - margin.right,  10)
  const plotH    = Math.max(ctx.height - margin.top  - margin.bottom, 10)

  /* cell size: fit 53 week-columns + day-of-week labels in plotW */
  const dowLabelW = 14
  const cellSize  = Math.max(
    Math.min(
      Math.floor((plotW - dowLabelW) / 53),
      Math.floor((plotH / years.length - 20) / 7)
    ),
    4
  )
  const yearBlockH = 7 * cellSize + 20   /* 7 rows + month-label row */

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  for (let yi = 0; yi < years.length; yi = yi + 1) {
    const year   = years[yi]
    const blockY = yi * yearBlockH + 14   /* 14px for month labels */

    /* Day-of-week labels */
    const dowLabels = ["Mon","","Wed","","Fri","","Sun"]
    for (let d = 0; d < 7; d = d + 1) {
      if (dowLabels[d] === "") {
        continue
      }
      plot.appendChild(svgEl("text", {
        x: dowLabelW - 2, y: blockY + d * cellSize + cellSize * 0.75,
        "text-anchor": "end",
        "font-size": 9,
        fill: "var(--mj-text-muted, #6b7280)"
      }, dowLabels[d]))
    }

    /* Iterate weeks */
    const startDate  = _firstMonday(year)
    const endDate    = new Date(year, 11, 31)
    let   currentDay = new Date(startDate)
    let   weekIndex  = 0
    let   lastMonth  = -1

    while (currentDay <= endDate || currentDay.getFullYear() < year) {
      const weekX = dowLabelW + weekIndex * cellSize

      /* Month label at week start */
      const firstDayOfWeek = new Date(currentDay)
      if (firstDayOfWeek.getFullYear() === year) {
        const month = firstDayOfWeek.getMonth()
        if (month !== lastMonth) {
          plot.appendChild(svgEl("text", {
            x: weekX, y: blockY - 2,
            "font-size": 9,
            fill: "var(--mj-text-muted, #6b7280)"
          }, MONTH_ABBR[month]))
          lastMonth = month
        }
      }

      /* 7 days in this week column */
      for (let d = 0; d < 7; d = d + 1) {
        const dayDate = new Date(currentDay)
        const dayY    = blockY + d * cellSize
        const key     = _dateKey(dayDate)
        const val     = valueMap[key]
        const inYear  = dayDate.getFullYear() === year

        let fillColor = "var(--mj-surface-raised, #f3f4f6)"
        if (inYear === true && typeof val === "number") {
          const t = valScale(val)
          if (colorScaleMode === "diverging") {
            fillColor = _divFill(t)
          } else {
            fillColor = _seqFill(t)
          }
        }

        const cellRect = svgEl("rect", {
          x: weekX, y: dayY,
          width: cellSize - 1, height: cellSize - 1,
          rx: 1,
          fill: fillColor
        }, [])

        if (inYear === true) {
          const displayVal = typeof val === "number" ? formatNumber(val) : "no data"
          const labelText  = `${key}: ${displayVal}`
          cellRect.setAttribute("part", "day")
          cellRect.setAttribute("tabindex", "0")
          cellRect.setAttribute("role", "img")
          cellRect.setAttribute("aria-label", labelText)
          cellRect.appendChild(svgEl("title", null, labelText))
          const capturedKey = key
          const capturedVal = val
          const handler = () => {
            ctx.emit("mj-chart-day-click", { date: capturedKey, value: capturedVal })
          }
          cellRect.addEventListener("click", handler)
          cellRect.addEventListener("keydown", (event) => {
            if (event.key === "Enter" || event.key === " ") {
              event.preventDefault()
              handler()
            }
          })
        } else {
          cellRect.setAttribute("opacity", "0.2")
        }

        plot.appendChild(cellRect)
        currentDay.setDate(currentDay.getDate() + 1)
      }

      weekIndex = weekIndex + 1
      if (weekIndex > 53) {
        break
      }
    }

    /* Year label on the left */
    plot.appendChild(svgEl("text", {
      x: dowLabelW, y: blockY - 2,
      "font-size": 9,
      fill: "var(--mj-text-muted, #6b7280)"
    }, ""))    /* month labels already cover the top; year label optional */
  }

  return root
}


registerRenderer("calendar-heatmap", render)
