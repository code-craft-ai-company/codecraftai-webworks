/*
 * resource.js
 *
 * Resource allocation renderer.
 *
 * Registers:
 *   "resource-allocation" — resources on the vertical axis, time on the
 *                           horizontal axis; allocation bars per task stacked
 *                           within each resource row; over-allocation is
 *                           highlighted. style="heatmap" collapses each row to
 *                           a single heat-color band.
 *
 * ctx.raw shape:
 *   resources: [{
 *     id, label, capacity?,
 *     allocations: [{ task, start, end, load }]
 *   }]
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, formatDate } from "../svgdraw.js";
import { timeScale, bandScale } from "../scales.js";


function _heatColor(load, capacity) {
  /*
   * Return an --mj-* token CSS color representing utilization level.
   * load / capacity gives a fraction; > 1.0 = over-allocated.
   */
  const fraction = capacity > 0 ? load / capacity : 0
  if (fraction > 1.0) {
    return "var(--mj-color-danger, #b91c1c)"
  }
  if (fraction >= 0.9) {
    return "var(--mj-color-warning, #b45309)"
  }
  if (fraction >= 0.5) {
    return "var(--mj-color-accent-500, #2563eb)"
  }
  return "var(--mj-color-success, #15803d)"
}


function _timeTicks(dateMin, dateMax, plotW) {
  /*
   * Produce date tick positions, capped to roughly 1 per 70px.
   */
  const spanMs = dateMax.getTime() - dateMin.getTime()
  const spanDays = spanMs / 86400000
  let dates = []

  if (spanDays <= 30) {
    let current = new Date(dateMin)
    current.setHours(0, 0, 0, 0)
    while (current <= dateMax) {
      dates.push(new Date(current))
      current.setDate(current.getDate() + 1)
    }
  } else if (spanDays <= 180) {
    let current = new Date(dateMin)
    current.setHours(0, 0, 0, 0)
    const dow = current.getDay()
    const toMonday = dow === 0 ? 1 : (8 - dow) % 7
    current.setDate(current.getDate() + toMonday)
    while (current <= dateMax) {
      dates.push(new Date(current))
      current.setDate(current.getDate() + 7)
    }
  } else {
    let current = new Date(dateMin.getFullYear(), dateMin.getMonth(), 1)
    while (current <= dateMax) {
      dates.push(new Date(current))
      current.setMonth(current.getMonth() + 1)
    }
  }

  const maxTicks = Math.max(2, Math.floor(plotW / 70))
  if (dates.length > maxTicks) {
    const step = Math.ceil(dates.length / maxTicks)
    dates = dates.filter((_, index) => index % step === 0)
  }
  return dates
}


function _formatTick(date, spanDays) {
  if (spanDays <= 180) {
    return formatDate(date, { month: "short", day: "numeric" })
  }
  return formatDate(date, { year: "numeric", month: "short" })
}


export function render(ctx) {
  /*
   * Render a resource-allocation chart.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const raw = ctx.raw
  const resources = (raw !== null && raw !== undefined && Array.isArray(raw.resources))
    ? raw.resources : []

  const isHeatmap = ctx.attrs("style", "") === "heatmap"

  const root = svgEl("g", { part: "plot" }, [])

  if (resources.length === 0) {
    return root
  }

  /* Date domain from all allocations. */
  let dateMin = null
  let dateMax = null
  for (let r = 0; r < resources.length; r = r + 1) {
    const res = resources[r]
    const allocs = Array.isArray(res.allocations) ? res.allocations : []
    for (let a = 0; a < allocs.length; a = a + 1) {
      const alloc = allocs[a]
      const start = new Date(alloc.start)
      const end = new Date(alloc.end)
      if (dateMin === null || start < dateMin) {
        dateMin = start
      }
      if (dateMax === null || end > dateMax) {
        dateMax = end
      }
    }
  }
  if (dateMin === null) {
    dateMin = new Date()
  }
  if (dateMax === null) {
    dateMax = new Date(dateMin.getTime() + 30 * 86400000)
  }
  if (dateMin.getTime() === dateMax.getTime()) {
    dateMax = new Date(dateMin.getTime() + 30 * 86400000)
  }
  const pad = (dateMax.getTime() - dateMin.getTime()) * 0.02
  dateMin = new Date(dateMin.getTime() - pad)
  dateMax = new Date(dateMax.getTime() + pad)

  const rowKeys = resources.map((res, index) => {
    const key = res.id !== undefined ? String(res.id) : String(index)
    return key
  })

  const margin = { top: 36, right: 16, bottom: 16, left: 100 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  const timeScaleFn = timeScale([dateMin, dateMax], [0, plotW])
  const rowScaleFn = bandScale(rowKeys, [0, plotH], 0.15)
  const bandwidth = rowScaleFn.bandwidth()

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  /* Time-axis ticks along the top. */
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

  plot.appendChild(svgEl("line", {
    x1: 0, y1: 0, x2: plotW, y2: 0,
    stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
  }, []))

  /* Resource rows. */
  for (let r = 0; r < resources.length; r = r + 1) {
    const res = resources[r]
    const key = rowKeys[r]
    const rowY = rowScaleFn(key)
    const capacity = typeof res.capacity === "number" ? res.capacity : 1.0
    const allocs = Array.isArray(res.allocations) ? res.allocations : []
    const resLabel = res.label !== undefined ? String(res.label) : key

    /* Alternating row stripe. */
    if (r % 2 === 0) {
      plot.appendChild(svgEl("rect", {
        x: 0, y: rowY, width: plotW,
        height: rowScaleFn.step(),
        fill: "var(--mj-surface-alt, #f8f9fb)", "fill-opacity": 0.5
      }, []))
    }

    /* Resource label. */
    plot.appendChild(svgEl("text", {
      x: -8, y: rowY + bandwidth / 2 + 4,
      "text-anchor": "end", "font-size": 11,
      fill: "var(--mj-text, #14181f)"
    }, escapeHtml(resLabel)))

    /* Capacity ceiling line. */
    const ceilY = rowY + bandwidth * (1 - capacity)
    plot.appendChild(svgEl("line", {
      x1: 0, y1: ceilY, x2: plotW, y2: ceilY,
      stroke: "var(--mj-border, #e0e3e9)",
      "stroke-width": 1, "stroke-dasharray": "4 2"
    }, []))

    if (isHeatmap === true) {
      /* Heatmap: single color band per time slot, color encodes total load. */
      /* Build a simple daily aggregation over the visible range. */
      const spanDays2 = Math.ceil(spanMs / 86400000)
      const dayW = Math.max(plotW / Math.max(spanDays2, 1), 1)
      const msPerDay = 86400000

      /* Aggregate allocations into day buckets. */
      const dayLoads = {}
      for (let a = 0; a < allocs.length; a = a + 1) {
        const alloc = allocs[a]
        const start = new Date(alloc.start)
        const end = new Date(alloc.end)
        const load = typeof alloc.load === "number" ? alloc.load : 0
        let current = new Date(start)
        current.setHours(0, 0, 0, 0)
        while (current <= end) {
          const dayKey = current.getTime()
          if (dayLoads[dayKey] === undefined) {
            dayLoads[dayKey] = 0
          }
          dayLoads[dayKey] = dayLoads[dayKey] + load
          current.setDate(current.getDate() + 1)
        }
      }

      const dayKeys = Object.keys(dayLoads)
      for (let d = 0; d < dayKeys.length; d = d + 1) {
        const dayMs = parseInt(dayKeys[d], 10)
        const dayDate = new Date(dayMs)
        const totalLoad = dayLoads[dayMs]
        const x = timeScaleFn(dayDate)
        const color = _heatColor(totalLoad, capacity)
        const heatLabel = `${escapeHtml(resLabel)}: load ${totalLoad.toFixed(1)} on ${formatDate(dayDate)}`
        const heatRect = svgEl("rect", {
          x: x, y: rowY, width: dayW, height: bandwidth,
          fill: color, "fill-opacity": 0.7, part: "allocation"
        }, [])
        heatRect.setAttribute("tabindex", "0")
        heatRect.setAttribute("role", "img")
        heatRect.setAttribute("aria-label", heatLabel)
        heatRect.appendChild(svgEl("title", null, heatLabel))
        plot.appendChild(heatRect)
      }
    } else {
      /* Bar mode: stacked allocation bars within the row. */
      /* Sort allocs by start date so stacking is deterministic. */
      const sortedAllocs = allocs.slice().sort((a, b) => {
        return new Date(a.start).getTime() - new Date(b.start).getTime()
      })

      for (let a = 0; a < sortedAllocs.length; a = a + 1) {
        const alloc = sortedAllocs[a]
        const start = new Date(alloc.start)
        const end = new Date(alloc.end)
        const load = typeof alloc.load === "number" ? alloc.load : 0
        const x1 = timeScaleFn(start)
        const x2 = timeScaleFn(end)
        const barW = Math.max(x2 - x1, 2)

        /* Bar height is proportional to load within the bandwidth. */
        const barH = Math.max(bandwidth * Math.min(load, 1), 2)
        const barY = rowY + (bandwidth - barH)
        const overload = load > capacity

        const color = overload
          ? "var(--mj-color-danger, #b91c1c)"
          : ctx.colorFor(a)
        const taskName = alloc.task !== undefined ? String(alloc.task) : ""
        const ariaLabel = `${escapeHtml(resLabel)}: ${escapeHtml(taskName)} ` +
          `${formatDate(start)}–${formatDate(end)}, load ${(load * 100).toFixed(0)}%` +
          (overload ? " (over-allocated)" : "")

        const bar = svgEl("rect", {
          x: x1, y: barY, width: barW, height: barH, rx: 2,
          fill: color, "fill-opacity": 0.8, part: "allocation"
        }, [])
        bar.setAttribute("tabindex", "0")
        bar.setAttribute("role", "img")
        bar.setAttribute("aria-label", ariaLabel)
        bar.appendChild(svgEl("title", null, ariaLabel))

        const emitAlloc = alloc
        const emitRes = res
        const clickHandler = () => {
          ctx.emit("mj-chart-allocation-click", {
            resource: emitRes.id,
            task: emitAlloc.task,
            start: emitAlloc.start,
            end: emitAlloc.end,
            load: emitAlloc.load
          })
        }
        bar.addEventListener("click", clickHandler)
        bar.addEventListener("keydown", (event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault()
            clickHandler()
          }
        })
        plot.appendChild(bar)

        /* Task label inside bar if wide enough. */
        if (barW > 40 && taskName !== "") {
          plot.appendChild(svgEl("text", {
            x: x1 + 4, y: barY + barH / 2 + 4,
            "font-size": 9,
            fill: "var(--mj-text-on-accent, #ffffff)",
            "pointer-events": "none"
          }, escapeHtml(taskName.length > 20 ? taskName.slice(0, 18) + "…" : taskName)))
        }
      }
    }
  }

  return root
}


registerRenderer("resource-allocation", render);
