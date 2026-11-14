/*
 * calendarheatmap.js
 *
 * Calendar-heatmap renderer — the days of one or more years in a
 * GitHub-style grid (week columns x weekday rows), coloured by value.
 *
 * Registered types:
 *   "calendar-heatmap"
 *
 * ctx.raw shape:
 *   raw.years        [number]         years to render; default: every year
 *                                     from the earliest to the latest date
 *                                     in the data (the current year when
 *                                     there is none). "2025" works too.
 *   raw.data         [{date, value}]  date: "YYYY-MM-DD" (a LOCAL calendar
 *                                     day), an ISO timestamp, a Date or
 *                                     epoch ms; values of the same day add up
 *   raw.domain       [min, max]       optional; auto-computed when absent
 *   raw.colorScale   "sequential" | "diverging" (around raw.midpoint, 0)
 *   raw.weekStart    1 = Monday (default) | 0 = Sunday
 *
 * Days without a value are drawn in a muted fill that differs from the page
 * in both themes, so the calendar grid stays readable; days outside the
 * year are not drawn. Each year block is labelled with its year, weekday and
 * month labels follow the library locale, and a colour key ("less ... more"
 * with the domain ends) is drawn under the grid.
 *
 * Orientation: "horizontal" (default; weeks run left to right) or
 * "vertical" (weeks run top to bottom, weekdays across).
 *
 * Interaction: days that have a value are focusable marks; click / Enter
 * emits `mj-chart-day-click` { date: "YYYY-MM-DD", value }.
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber, formatDate, parseDate } from "../svgdraw.js";
import {
  sequentialFill, divergingFill, divergingPosition, EMPTY_CELL_FILL
} from "./heatmaptable.js";

const DAY_MS = 24 * 60 * 60 * 1000
const GUTTER = 30
const HEADER = 14
const LEGEND_H = 18
const BLOCK_GAP = 10
const MAX_CELL = 22


function _dateKey(date) {
  /*
   * "YYYY-MM-DD" of a local calendar day.
   */
  const y = String(date.getFullYear()).padStart(4, "0")
  const m = String(date.getMonth() + 1).padStart(2, "0")
  const d = String(date.getDate()).padStart(2, "0")
  return `${y}-${m}-${d}`
}


function _readValues(raw) {
  /*
   * Aggregate the data by local day.
   *
   * :returns: Map "YYYY-MM-DD" -> value (sum of the day's numeric values).
   */
  const values = new Map()
  const list = Array.isArray(raw.data) === true ? raw.data : []
  for (let index = 0; index < list.length; index = index + 1) {
    const entry = list[index]
    if (entry === null || typeof entry !== "object") {
      continue
    }
    const date = parseDate(entry.date)
    const value = typeof entry.value === "number" ? entry.value : Number(entry.value)
    if (date === null || entry.value === null || Number.isFinite(value) === false) {
      continue
    }
    const key = _dateKey(date)
    values.set(key, (values.has(key) === true ? values.get(key) : 0) + value)
  }
  return values
}


function _readYears(raw, values) {
  /*
   * The years to draw, ascending and unique.
   */
  let years = []
  if (Array.isArray(raw.years) === true) {
    years = raw.years.map((year) => Number(year))
      .filter((year) => Number.isInteger(year) === true && year > 0 && year < 10000)
  }
  if (years.length === 0) {
    const found = Array.from(values.keys()).map((key) => Number(key.slice(0, 4)))
    if (found.length > 0) {
      const first = Math.min(...found)
      const last = Math.max(...found)
      for (let year = first; year <= last && years.length < 20; year = year + 1) {
        years.push(year)
      }
    } else {
      years = [new Date().getFullYear()]
    }
  }
  years = Array.from(new Set(years)).sort((a, b) => a - b)
  return years
}


export function render(ctx) {
  /*
   * Render a calendar heatmap.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const raw = ctx.raw !== null && ctx.raw !== undefined ? ctx.raw : {}
  const root = svgEl("g", { part: "plot" }, [])

  const values = _readValues(raw)
  const years = _readYears(raw, values)
  const weekStart = raw.weekStart === 0 ? 0 : 1
  const diverging = raw.colorScale === "diverging" || ctx.attrs("style", null) === "diverging"
  const midpoint = typeof raw.midpoint === "number" && Number.isFinite(raw.midpoint) === true
    ? raw.midpoint
    : 0

  /* Values inside the drawn years. */
  const shown = []
  values.forEach((value, key) => {
    if (years.indexOf(Number(key.slice(0, 4))) >= 0) {
      shown.push([key, value])
    }
  })
  shown.sort((a, b) => (a[0] < b[0] ? -1 : 1))
  ctx.setTable({
    columns: ["Date", "Value"],
    rows: shown.map((entry) => [formatDate(entry[0], { dateStyle: "medium" }), entry[1]]),
    caption: ctx.label
  })

  let domain = null
  if (Array.isArray(raw.domain) === true && raw.domain.length === 2 &&
      Number.isFinite(raw.domain[0]) === true && Number.isFinite(raw.domain[1]) === true) {
    domain = [Math.min(raw.domain[0], raw.domain[1]), Math.max(raw.domain[0], raw.domain[1])]
  } else if (shown.length > 0) {
    const numbers = shown.map((entry) => entry[1])
    domain = [Math.min(...numbers), Math.max(...numbers)]
  } else {
    domain = [0, 1]
  }
  const fillOf = (value) => {
    if (diverging === true) {
      return divergingFill(divergingPosition(value, domain, midpoint))
    }
    const span = domain[1] - domain[0]
    return sequentialFill(span > 0 ? (value - domain[0]) / span : 1)
  }

  /* Weeks per block: the most any drawn year needs (53 or 54). */
  const offsetOf = (date) => (date.getDay() - weekStart + 7) % 7
  let weeks = 53
  for (let index = 0; index < years.length; index = index + 1) {
    const jan1 = new Date(years[index], 0, 1)
    const days = Math.round((new Date(years[index] + 1, 0, 1) - jan1) / DAY_MS)
    weeks = Math.max(weeks, Math.ceil((offsetOf(jan1) + days) / 7))
  }

  const vertical = ctx.orientation === "vertical"
  const pad = 4
  const availableW = Math.max(ctx.width - pad * 2, 20)
  const availableH = Math.max(ctx.height - pad * 2 - LEGEND_H, 20)
  const blocks = years.length
  let cell = 0
  if (vertical === false) {
    cell = Math.min(
      (availableW - GUTTER) / weeks,
      (availableH - blocks * HEADER - (blocks - 1) * BLOCK_GAP) / (blocks * 7)
    )
  } else {
    cell = Math.min(
      (availableW - blocks * GUTTER - (blocks - 1) * BLOCK_GAP) / (blocks * 7),
      (availableH - HEADER) / weeks
    )
  }
  cell = Math.max(Math.min(cell, MAX_CELL), 3)
  const gap = cell >= 8 ? 1.5 : 0.5

  /* Position of (week, weekday) in block `b`, as the cell's top-left. */
  const blockW = vertical === true ? GUTTER + 7 * cell : GUTTER + weeks * cell
  const blockH = vertical === true ? HEADER + weeks * cell : HEADER + 7 * cell
  /* Centre the blocks (and the key under them) vertically in the box. */
  const usedH = (vertical === true ? blockH : blocks * blockH + (blocks - 1) * BLOCK_GAP) + LEGEND_H
  const top = pad + Math.max((ctx.height - pad * 2 - usedH) / 2, 0)
  const originOf = (b) => (vertical === true
    ? { x: pad + b * (blockW + BLOCK_GAP), y: top }
    : { x: pad, y: top + b * (blockH + BLOCK_GAP) })
  const cellAt = (b, week, weekday) => {
    const origin = originOf(b)
    return vertical === true
      ? { x: origin.x + GUTTER + weekday * cell, y: origin.y + HEADER + week * cell }
      : { x: origin.x + GUTTER + week * cell, y: origin.y + HEADER + weekday * cell }
  }

  const decor = svgEl("g", { "aria-hidden": "true" }, [])
  root.appendChild(decor)
  const cells = svgEl("g", { part: "days" }, [])
  root.appendChild(cells)
  const muted = "var(--mj-text-muted, #5f6673)"
  const labelSize = Math.max(Math.min(cell * 0.85, 10), 7)

  for (let b = 0; b < years.length; b = b + 1) {
    const year = years[b]
    const origin = originOf(b)
    const jan1 = new Date(year, 0, 1)
    const firstOffset = offsetOf(jan1)

    /* Year label in the corner of the block. */
    decor.appendChild(svgEl("text", {
      x: origin.x, y: origin.y + 10, "font-size": 10, "font-weight": "600",
      fill: "var(--mj-text, #14181f)", part: "year-label"
    }, String(year)))

    /* Weekday labels: every other day. */
    for (let weekday = 0; weekday < 7; weekday = weekday + 2) {
      const sample = new Date(2024, 0, 7 + weekStart + weekday)
      const text = formatDate(sample, { weekday: "short" })
      const spot = cellAt(b, 0, weekday)
      decor.appendChild(vertical === true
        ? svgEl("text", {
          x: spot.x + cell / 2, y: origin.y + HEADER - 3, "text-anchor": "middle",
          "font-size": labelSize, fill: muted
        }, text.slice(0, 2))
        : svgEl("text", {
          x: origin.x + GUTTER - 3, y: spot.y + cell * 0.75, "text-anchor": "end",
          "font-size": labelSize, fill: muted
        }, text))
    }

    /* Days. */
    let day = new Date(year, 0, 1)
    let index = 0
    while (day.getFullYear() === year && index < 366) {
      const slot = firstOffset + index
      const week = Math.floor(slot / 7)
      const weekday = slot % 7
      const spot = cellAt(b, week, weekday)
      const key = _dateKey(day)
      const value = values.get(key)

      if (day.getDate() === 1) {
        const monthText = formatDate(day, { month: "short" })
        decor.appendChild(vertical === true
          ? svgEl("text", {
            x: origin.x + GUTTER - 3, y: spot.y + cell * 0.75, "text-anchor": "end",
            "font-size": labelSize, fill: muted
          }, monthText)
          : svgEl("text", {
            x: spot.x, y: origin.y + HEADER - 3, "font-size": labelSize, fill: muted
          }, monthText))
      }

      const hasValue = value !== undefined
      const label = `${formatDate(day, { dateStyle: "medium" })}: ` +
        `${hasValue === true ? formatNumber(value) : "no data"}`
      const rect = svgEl("rect", {
        x: spot.x.toFixed(2), y: spot.y.toFixed(2),
        width: Math.max(cell - gap, 1).toFixed(2), height: Math.max(cell - gap, 1).toFixed(2),
        rx: Math.min(2, cell / 5).toFixed(2),
        fill: hasValue === true ? fillOf(value) : EMPTY_CELL_FILL,
        part: hasValue === true ? "day" : "day empty"
      }, [svgEl("title", null, label)])
      if (hasValue === true) {
        rect.setAttribute("tabindex", "0")
        rect.setAttribute("role", "img")
        rect.setAttribute("aria-label", label)
        const capturedKey = key
        const capturedValue = value
        const handler = () => {
          ctx.emit("mj-chart-day-click", { date: capturedKey, value: capturedValue })
        }
        rect.addEventListener("click", handler)
        rect.addEventListener("keydown", (event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault()
            handler()
          }
        })
      }
      cells.appendChild(rect)

      index = index + 1
      day = new Date(year, 0, 1 + index)
    }
  }

  /* Colour key: less [ramp] more, with the domain ends. */
  const totalW = vertical === true ? blocks * blockW + (blocks - 1) * BLOCK_GAP : blockW
  const totalH = vertical === true ? blockH : blocks * blockH + (blocks - 1) * BLOCK_GAP
  const keyY = top + totalH + 6
  const swatch = Math.max(Math.min(cell, 10), 6)
  const steps = 5
  const rampW = steps * (swatch + 2)
  const highText = formatNumber(domain[1])
  const lowText = formatNumber(domain[0])
  const keyRight = Math.min(pad + totalW, ctx.width - pad)
  const rampX = keyRight - rampW - highText.length * 5.5 - 6
  const key = svgEl("g", { "aria-hidden": "true", part: "legend" }, [])
  decor.appendChild(key)
  key.appendChild(svgEl("text", {
    x: rampX - 4, y: keyY + swatch - 1, "text-anchor": "end", "font-size": 9, fill: muted
  }, lowText))
  for (let s = 0; s < steps; s = s + 1) {
    const t = s / (steps - 1)
    const fill = diverging === true
      ? divergingFill(divergingPosition(domain[0] + (domain[1] - domain[0]) * t, domain, midpoint))
      : sequentialFill(t)
    key.appendChild(svgEl("rect", {
      x: rampX + s * (swatch + 2), y: keyY, width: swatch, height: swatch, rx: 1.5, fill: fill
    }, []))
  }
  key.appendChild(svgEl("text", {
    x: rampX + rampW + 2, y: keyY + swatch - 1, "font-size": 9, fill: muted
  }, highText))
  key.appendChild(svgEl("rect", {
    x: pad + GUTTER, y: keyY, width: swatch, height: swatch, rx: 1.5, fill: EMPTY_CELL_FILL
  }, []))
  key.appendChild(svgEl("text", {
    x: pad + GUTTER + swatch + 4, y: keyY + swatch - 1, "font-size": 9, fill: muted
  }, "no data"))

  return root
}


registerRenderer("calendar-heatmap", render, { orientation: "horizontal", legend: "none" })
