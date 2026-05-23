/*
 * gantt.js
 *
 * Gantt / Roadmap renderer.
 *
 * Registers:
 *   "gantt"   — project tasks as horizontal bars over a time axis, with
 *               optional progress fills, swimlane group headers, and
 *               dependency arrows.
 *   "roadmap" — swimlane variant: broader bars, quarter-level ticks, no
 *               dependency arrows, status-colour coding.
 *
 * ctx.raw shape:
 *   tasks: [{ id, label, start, end, progress?, assignee?, group?, depends?,
 *             status? }]
 *
 * Quarter strings (YYYY-Qn) in start/end are normalised to the first/last day
 * of that quarter before the time scale receives them.
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, formatDate } from "../svgdraw.js";
import { timeScale, bandScale } from "../scales.js";


/* Status → CSS color token for roadmap bars. */
const STATUS_COLORS = {
  "completed":   "var(--mj-color-success, #15803d)",
  "in-progress": "var(--mj-color-accent-500, #2563eb)",
  "planned":     "var(--mj-color-neutral-500, #6b7280)",
  "at-risk":     "var(--mj-color-danger, #b91c1c)"
};


function _parseDate(value) {
  /*
   * Parse an ISO date string or YYYY-Qn quarter string into a Date.
   * Returns a Date object.
   */
  if (value === null || value === undefined) {
    return new Date()
  }
  const quarterMatch = String(value).match(/^(\d{4})-Q([1-4])$/)
  if (quarterMatch !== null) {
    const year = parseInt(quarterMatch[1], 10)
    const quarter = parseInt(quarterMatch[2], 10)
    const month = (quarter - 1) * 3
    const date = new Date(year, month, 1)
    return date
  }
  const date = new Date(value)
  return date
}


function _parseEndDate(value) {
  /*
   * Parse an end date; quarter strings expand to the last day of the quarter.
   */
  if (value === null || value === undefined) {
    return new Date()
  }
  const quarterMatch = String(value).match(/^(\d{4})-Q([1-4])$/)
  if (quarterMatch !== null) {
    const year = parseInt(quarterMatch[1], 10)
    const quarter = parseInt(quarterMatch[2], 10)
    const lastMonth = quarter * 3
    const date = new Date(year, lastMonth, 0)
    return date
  }
  const date = new Date(value)
  return date
}


function _timeTicks(dateMin, dateMax, plotW) {
  /*
   * Produce date tick positions based on the date range and available width.
   * Returns an array of Date objects.
   */
  const spanMs = dateMax.getTime() - dateMin.getTime()
  const spanDays = spanMs / 86400000

  let dates = []

  if (spanDays <= 30) {
    /* Daily ticks */
    let current = new Date(dateMin)
    current.setHours(0, 0, 0, 0)
    while (current <= dateMax) {
      dates.push(new Date(current))
      current.setDate(current.getDate() + 1)
    }
  } else if (spanDays <= 180) {
    /* Weekly ticks — start on Monday */
    let current = new Date(dateMin)
    current.setHours(0, 0, 0, 0)
    const dow = current.getDay()
    const toMonday = dow === 0 ? 1 : (8 - dow) % 7
    current.setDate(current.getDate() + toMonday)
    while (current <= dateMax) {
      dates.push(new Date(current))
      current.setDate(current.getDate() + 7)
    }
  } else if (spanDays <= 730) {
    /* Monthly ticks */
    let current = new Date(dateMin.getFullYear(), dateMin.getMonth(), 1)
    while (current <= dateMax) {
      dates.push(new Date(current))
      current.setMonth(current.getMonth() + 1)
    }
  } else {
    /* Quarterly ticks */
    const startQuarter = Math.floor(dateMin.getMonth() / 3)
    let current = new Date(dateMin.getFullYear(), startQuarter * 3, 1)
    while (current <= dateMax) {
      dates.push(new Date(current))
      current.setMonth(current.getMonth() + 3)
    }
  }

  /* Limit density to ~1 tick per 60px */
  const maxTicks = Math.max(2, Math.floor(plotW / 60))
  if (dates.length > maxTicks) {
    const step = Math.ceil(dates.length / maxTicks)
    dates = dates.filter((_, index) => index % step === 0)
  }

  return dates
}


function _formatTick(date, spanDays) {
  /*
   * Format a time-axis tick label based on span granularity.
   */
  if (spanDays <= 30) {
    return formatDate(date, { month: "short", day: "numeric" })
  }
  if (spanDays <= 180) {
    return formatDate(date, { month: "short", day: "numeric" })
  }
  if (spanDays <= 730) {
    return formatDate(date, { year: "numeric", month: "short" })
  }
  const quarter = Math.floor(date.getMonth() / 3) + 1
  return `${date.getFullYear()} Q${quarter}`
}


export function render(ctx) {
  /*
   * Render a gantt or roadmap chart.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const raw = ctx.raw
  const tasks = (raw !== null && raw !== undefined && Array.isArray(raw.tasks))
    ? raw.tasks : []

  const isRoadmap = ctx.attrs("style", "") === "roadmap"

  const root = svgEl("g", { part: "plot" }, [])

  if (tasks.length === 0) {
    return root
  }

  /* Collect all unique group names to build swimlane row keys. */
  const rowKeys = []
  const seenKeys = {}
  for (let index = 0; index < tasks.length; index = index + 1) {
    const task = tasks[index]
    const key = task.id !== undefined ? String(task.id) : String(index)
    if (seenKeys[key] === undefined) {
      rowKeys.push(key)
      seenKeys[key] = true
    }
  }

  const taskById = {}
  for (let index = 0; index < tasks.length; index = index + 1) {
    const task = tasks[index]
    const key = task.id !== undefined ? String(task.id) : String(index)
    taskById[key] = task
  }

  /* Date domain. */
  let dateMin = null
  let dateMax = null
  for (let index = 0; index < tasks.length; index = index + 1) {
    const task = tasks[index]
    const start = _parseDate(task.start)
    const end = _parseEndDate(task.end)
    if (dateMin === null || start < dateMin) {
      dateMin = start
    }
    if (dateMax === null || end > dateMax) {
      dateMax = end
    }
  }
  if (dateMin === null) {
    dateMin = new Date()
  }
  if (dateMax === null) {
    dateMax = new Date(dateMin.getTime() + 30 * 86400000)
  }
  /* Pad domain slightly. */
  const padMs = (dateMax.getTime() - dateMin.getTime()) * 0.02
  dateMin = new Date(dateMin.getTime() - padMs)
  dateMax = new Date(dateMax.getTime() + padMs)

  const margin = { top: 40, right: 16, bottom: 16, left: 120 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  const timeScaleFn = timeScale([dateMin, dateMax], [0, plotW])
  const rowScaleFn = bandScale(rowKeys, [0, plotH], 0.15)
  const bandwidth = rowScaleFn.bandwidth()

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  /* Time-axis gridlines and tick labels (along the top). */
  const spanMs = dateMax.getTime() - dateMin.getTime()
  const spanDays = spanMs / 86400000
  const ticks = _timeTicks(dateMin, dateMax, plotW)

  for (let t = 0; t < ticks.length; t = t + 1) {
    const tick = ticks[t]
    const x = timeScaleFn(tick)
    plot.appendChild(svgEl("line", {
      x1: x, y1: 0, x2: x, y2: plotH,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    plot.appendChild(svgEl("text", {
      x: x, y: -8, "text-anchor": "middle",
      "font-size": 10, fill: "var(--mj-text-muted, #6b7280)"
    }, _formatTick(tick, spanDays)))
  }

  /* Axis baseline. */
  plot.appendChild(svgEl("line", {
    x1: 0, y1: 0, x2: plotW, y2: 0,
    stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
  }, []))

  /* Collect bar positions for dependency arrow routing. */
  const barPositions = {}

  /* Draw task rows. */
  for (let index = 0; index < tasks.length; index = index + 1) {
    const task = tasks[index]
    const key = task.id !== undefined ? String(task.id) : String(index)
    const rowY = rowScaleFn(key)
    const start = _parseDate(task.start)
    const end = _parseEndDate(task.end)
    const x1 = timeScaleFn(start)
    const x2 = timeScaleFn(end)
    const barW = Math.max(x2 - x1, 2)
    const barH = Math.max(bandwidth, 4)
    const barY = rowY + (bandwidth - barH) / 2

    /* Determine bar color. */
    let barColor = ctx.colorFor(index)
    if (isRoadmap === true && task.status !== undefined) {
      const statusColor = STATUS_COLORS[task.status]
      if (statusColor !== undefined) {
        barColor = statusColor
      }
    }

    const rx = isRoadmap === true ? 6 : 3

    /* Row background stripe for alternating rows. */
    if (index % 2 === 0) {
      plot.appendChild(svgEl("rect", {
        x: 0, y: rowY, width: plotW, height: bandwidth + rowScaleFn.step() - bandwidth,
        fill: "var(--mj-surface-alt, #f8f9fb)", "fill-opacity": 0.5
      }, []))
    }

    /* Row label. */
    const labelText = task.label !== undefined ? String(task.label) : key
    plot.appendChild(svgEl("text", {
      x: -8, y: rowY + bandwidth / 2 + 4,
      "text-anchor": "end", "font-size": 11,
      fill: "var(--mj-text, #14181f)"
    }, escapeHtml(labelText)))

    /* Task bar. */
    const rect = svgEl("rect", {
      x: x1, y: barY, width: barW, height: barH, rx: rx,
      fill: barColor, part: "bar"
    }, [])
    rect.setAttribute("tabindex", "0")
    rect.setAttribute("role", "img")
    const ariaLabel = `${escapeHtml(labelText)}: ${formatDate(start)} to ${formatDate(end)}`
    rect.setAttribute("aria-label", ariaLabel)
    rect.appendChild(svgEl("title", null, ariaLabel))

    const emitTask = task
    const clickHandler = () => {
      ctx.emit("mj-chart-bar-click", {
        id: emitTask.id,
        label: emitTask.label,
        start: emitTask.start,
        end: emitTask.end
      })
    }
    rect.addEventListener("click", clickHandler)
    rect.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault()
        clickHandler()
      }
    })
    plot.appendChild(rect)

    /* Progress fill. */
    if (isRoadmap === false && typeof task.progress === "number" && task.progress > 0) {
      const progressW = barW * Math.min(task.progress, 1)
      plot.appendChild(svgEl("rect", {
        x: x1, y: barY, width: progressW, height: barH, rx: rx,
        fill: "var(--mj-color-success, #15803d)", "fill-opacity": 0.7
      }, []))
    }

    /* Group header label (swimlane separator). */
    if (task.group !== undefined && task.group !== null) {
      const prevTask = index > 0 ? tasks[index - 1] : null
      const prevGroup = prevTask !== null ? prevTask.group : null
      if (prevGroup !== task.group) {
        plot.appendChild(svgEl("text", {
          x: -margin.left + 4, y: rowY + bandwidth / 2 + 4,
          "font-size": 10, "font-weight": "bold",
          fill: "var(--mj-text-muted, #6b7280)"
        }, escapeHtml(String(task.group))))
        plot.appendChild(svgEl("line", {
          x1: -margin.left, y1: rowY - 2,
          x2: plotW, y2: rowY - 2,
          stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
        }, []))
      }
    }

    /* Record bar center-right and center-left for arrows. */
    barPositions[key] = {
      rightX: x2,
      leftX: x1,
      midY: rowY + bandwidth / 2
    }
  }

  /* Dependency arrows (gantt only, not roadmap). */
  if (isRoadmap === false) {
    /* Define arrowhead marker. */
    const defs = svgEl("defs", null, [])
    const marker = svgEl("marker", {
      id: "mj-gantt-arrow",
      markerWidth: 8, markerHeight: 8,
      refX: 6, refY: 3,
      orient: "auto"
    }, [])
    marker.appendChild(svgEl("path", {
      d: "M0,0 L0,6 L8,3 Z",
      fill: "var(--mj-border-strong, #c7ccd6)"
    }, []))
    defs.appendChild(marker)
    plot.appendChild(defs)

    for (let index = 0; index < tasks.length; index = index + 1) {
      const task = tasks[index]
      if (task.depends === undefined || task.depends === null) {
        continue
      }
      if (Array.isArray(task.depends) === false) {
        continue
      }
      const toKey = task.id !== undefined ? String(task.id) : String(index)
      const toPos = barPositions[toKey]
      if (toPos === undefined) {
        continue
      }

      for (let d = 0; d < task.depends.length; d = d + 1) {
        const fromKey = String(task.depends[d])
        const fromPos = barPositions[fromKey]
        if (fromPos === undefined) {
          continue
        }
        const x1Arrow = fromPos.rightX + 2
        const y1Arrow = fromPos.midY
        const x2Arrow = toPos.leftX - 2
        const y2Arrow = toPos.midY
        const midX = (x1Arrow + x2Arrow) / 2
        const pathD = `M${x1Arrow.toFixed(1)},${y1Arrow.toFixed(1)} ` +
          `L${midX.toFixed(1)},${y1Arrow.toFixed(1)} ` +
          `L${midX.toFixed(1)},${y2Arrow.toFixed(1)} ` +
          `L${x2Arrow.toFixed(1)},${y2Arrow.toFixed(1)}`
        plot.appendChild(svgEl("path", {
          d: pathD,
          stroke: "var(--mj-border-strong, #c7ccd6)",
          "stroke-width": 1.5,
          fill: "none",
          "marker-end": "url(#mj-gantt-arrow)"
        }, []))
      }
    }
  }

  return root
}


registerRenderer("gantt", render);
registerRenderer("roadmap", render);
