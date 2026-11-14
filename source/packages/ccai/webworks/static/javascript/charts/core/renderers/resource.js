/*
 * resource.js
 *
 * Resource allocation renderer.
 *
 * Registers:
 *   "resource-allocation" — resources on the vertical axis, time on the
 *       horizontal axis. Each resource row is swept into time segments;
 *       allocations that run at the same time are STACKED by load, and every
 *       period whose summed load exceeds the resource's capacity is flagged
 *       (red outline above the dashed capacity line). Bar height is load
 *       relative to max(capacity, peak load) of the row, so loads in any
 *       unit (fractions, hours) fit.
 *
 * ctx.raw shape:
 *   resources: [{
 *     id, label, capacity?,              capacity defaults to 1
 *     allocations: [{ task, start, end, load }]
 *   }]
 *
 * Dates follow the gantt rules: "YYYY-MM-DD" is a local calendar day and an
 * END day is inclusive; quarter and month strings are accepted. Allocations
 * without usable dates or load are listed in the data table but not drawn.
 *
 * Options:
 *   variant  "heatmap" — one band per resource whose colour shows the
 *            utilisation (summed load / capacity) of each period
 *
 * Events:
 *   mj-chart-allocation-click { resource, task, start, end, load }
 *       heatmap cells: { resource, start, end, load, utilization }
 *       over-capacity flags: { resource, start, end, load, overAllocated }
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatDate, formatNumber } from "../svgdraw.js";
import { timeScale, bandScale, timeTicks, timeTickFormat } from "../scales.js";
import { parseScheduleDate, lastIncludedDay, estimateTextWidth, fitText } from "./gantt.js";


const OVER_COLOR = "var(--mj-color-danger, #b91c1c)";
const LABEL_FONT = 11;
const DAY_MS = 86400000;

/* Utilisation bands of the heatmap variant: one hue, rising strength. */
const HEAT_BANDS = [
  { max: 0.5, label: "Under 50%", color: "color-mix(in oklab, var(--mj-accent, #2563eb) 28%, var(--mj-surface, #ffffff))" },
  { max: 0.9, label: "50\u201389%", color: "color-mix(in oklab, var(--mj-accent, #2563eb) 58%, var(--mj-surface, #ffffff))" },
  { max: 1.0, label: "90\u2013100%", color: "var(--mj-accent, #2563eb)" },
  { max: Infinity, label: "Over capacity", color: OVER_COLOR }
];


function _heatBand(fraction) {
  /*
   * The heatmap band of a utilisation fraction (summed load / capacity):
   * below 0.5, below 0.9, up to 1.0, above 1.0.
   */
  let band = HEAT_BANDS[HEAT_BANDS.length - 1]
  for (let index = 0; index < HEAT_BANDS.length; index = index + 1) {
    const limit = HEAT_BANDS[index].max
    const within = limit === 1.0 ? fraction <= limit + 1e-9 : fraction < limit - 1e-9
    if (within === true) {
      band = HEAT_BANDS[index]
      break
    }
  }
  return band
}


function _readAllocations(resource) {
  /*
   * Parse a resource's allocations.
   *
   * :returns: [{ alloc, index, task, start, end, shownEnd, load, drawable }]
   *     sorted by start (then data order) so stacking is deterministic.
   */
  const list = Array.isArray(resource.allocations) === true ? resource.allocations : []
  const parsed = []
  for (let index = 0; index < list.length; index = index + 1) {
    const alloc = list[index]
    if (alloc === null || typeof alloc !== "object") {
      continue
    }
    const startInfo = parseScheduleDate(alloc.start, "start")
    const endInfo = parseScheduleDate(alloc.end, "end")
    const load = Number(alloc.load)
    const drawable = startInfo.date !== null && endInfo.date !== null &&
      endInfo.date.getTime() > startInfo.date.getTime() &&
      Number.isFinite(load) === true && load > 0 &&
      alloc.load !== null && alloc.load !== ""
    parsed.push({
      alloc: alloc,
      index: index,
      task: alloc.task !== undefined && alloc.task !== null ? String(alloc.task) : "",
      start: startInfo.date,
      end: endInfo.date,
      shownEnd: lastIncludedDay(endInfo),
      load: Number.isFinite(load) === true ? load : null,
      drawable: drawable
    })
  }
  /* Earlier first; of two that start together the longer one lies lower. */
  parsed.sort((a, b) => {
    const aStart = a.start !== null ? a.start.getTime() : Infinity
    const bStart = b.start !== null ? b.start.getTime() : Infinity
    if (aStart !== bStart) {
      return aStart - bStart
    }
    const aEnd = a.end !== null ? a.end.getTime() : -Infinity
    const bEnd = b.end !== null ? b.end.getTime() : -Infinity
    return aEnd !== bEnd ? bEnd - aEnd : a.index - b.index
  })
  return parsed
}


function _sweep(allocations) {
  /*
   * Split a resource's drawable allocations into time segments in which the
   * set of active allocations does not change.
   *
   * :returns: [{ start, end, total, active: [{ entry, offset }] }] where
   *     `offset` is the summed load stacked below the entry.
   */
  const drawable = allocations.filter((entry) => entry.drawable === true)
  const boundarySet = new Set()
  for (let index = 0; index < drawable.length; index = index + 1) {
    boundarySet.add(drawable[index].start.getTime())
    boundarySet.add(drawable[index].end.getTime())
  }
  const boundaries = Array.from(boundarySet).sort((a, b) => a - b)

  const segments = []
  for (let b = 0; b + 1 < boundaries.length; b = b + 1) {
    const segStart = boundaries[b]
    const segEnd = boundaries[b + 1]
    const active = []
    let total = 0
    for (let index = 0; index < drawable.length; index = index + 1) {
      const entry = drawable[index]
      if (entry.start.getTime() <= segStart && entry.end.getTime() >= segEnd) {
        active.push({ entry: entry, offset: total })
        total = total + entry.load
      }
    }
    if (active.length > 0) {
      segments.push({ start: segStart, end: segEnd, total: total, active: active })
    }
  }
  return segments
}


function _mergeRuns(segments, sameRun) {
  /*
   * Merge consecutive, touching segments for which sameRun(previous,
   * current) holds.
   *
   * :returns: [{ start, end, first }] runs; `first` is the first segment.
   */
  const runs = []
  for (let index = 0; index < segments.length; index = index + 1) {
    const segment = segments[index]
    const last = runs.length > 0 ? runs[runs.length - 1] : null
    if (last !== null && last.end === segment.start && sameRun(last.lastSegment, segment) === true) {
      last.end = segment.end
      last.lastSegment = segment
      last.peak = Math.max(last.peak, segment.total)
    } else {
      runs.push({ start: segment.start, end: segment.end, first: segment, lastSegment: segment,
        peak: segment.total })
    }
  }
  return runs
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


function _periodText(startMs, endMs) {
  /*
   * "Apr 14, 2025 – Apr 25, 2025" for a [start, end) period of whole days.
   */
  const lastDay = new Date(endMs - 1)
  const text = `${formatDate(new Date(startMs))} – ${formatDate(lastDay)}`
  return text
}


export function render(ctx) {
  /*
   * Render a resource-allocation chart.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const raw = ctx.raw
  const resourceList = (raw !== null && raw !== undefined && Array.isArray(raw.resources))
    ? raw.resources.filter((res) => res !== null && typeof res === "object") : []

  const isHeatmap = ctx.attrs("style", "") === "heatmap"

  const root = svgEl("g", { part: "plot" }, [])

  if (resourceList.length === 0) {
    return root
  }

  /* Parse every resource and sweep it into segments. */
  const resources = []
  let dateMin = null
  let dateMax = null
  for (let r = 0; r < resourceList.length; r = r + 1) {
    const res = resourceList[r]
    const capacityValue = Number(res.capacity)
    const capacity = res.capacity !== null && res.capacity !== undefined &&
      Number.isFinite(capacityValue) === true && capacityValue > 0 ? capacityValue : 1
    const allocations = _readAllocations(res)
    const segments = _sweep(allocations)
    let peak = 0
    for (let s = 0; s < segments.length; s = s + 1) {
      peak = Math.max(peak, segments[s].total)
      if (dateMin === null || segments[s].start < dateMin) {
        dateMin = segments[s].start
      }
      if (dateMax === null || segments[s].end > dateMax) {
        dateMax = segments[s].end
      }
    }
    const label = res.label !== undefined && res.label !== null
      ? String(res.label)
      : (res.id !== undefined && res.id !== null ? String(res.id) : `Resource ${r + 1}`)
    resources.push({
      res: res, label: label, capacity: capacity, allocations: allocations,
      segments: segments, peak: peak, scaleMax: Math.max(capacity, peak)
    })
  }

  /* Accessible table: every allocation, then every over-capacity period. */
  const tableRows = []
  for (let r = 0; r < resources.length; r = r + 1) {
    const entry = resources[r]
    for (let a = 0; a < entry.allocations.length; a = a + 1) {
      const alloc = entry.allocations[a]
      tableRows.push([
        entry.label, alloc.task,
        alloc.start !== null ? formatDate(alloc.start) : "",
        alloc.shownEnd !== null ? formatDate(alloc.shownEnd) : "",
        alloc.load !== null ? alloc.load : "", entry.capacity
      ])
    }
    const overRuns = _mergeRuns(entry.segments.filter((seg) => seg.total > entry.capacity + 1e-9),
      () => true)
    for (let o = 0; o < overRuns.length; o = o + 1) {
      tableRows.push([
        entry.label, "Over capacity",
        formatDate(new Date(overRuns[o].start)), formatDate(new Date(overRuns[o].end - 1)),
        overRuns[o].peak, entry.capacity
      ])
    }
  }
  ctx.setTable({
    columns: ["Resource", "Task", "Start", "End", "Load", "Capacity"],
    rows: tableRows
  })

  if (dateMin === null) {
    dateMin = new Date().setHours(0, 0, 0, 0)
    dateMax = dateMin + 30 * DAY_MS
  }
  const padMs = (dateMax - dateMin) * 0.02
  const domainMin = new Date(dateMin - padMs)
  const domainMax = new Date(dateMax + padMs)

  let longest = 0
  for (let r = 0; r < resources.length; r = r + 1) {
    longest = Math.max(longest, estimateTextWidth(resources[r].label, LABEL_FONT))
  }
  const gutter = Math.min(Math.max(longest + 16, 60), Math.max(ctx.width * 0.35, 60))

  const margin = { top: 32, right: 16, bottom: 12, left: gutter }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  const timeScaleFn = timeScale([domainMin, domainMax], [0, plotW])
  const rowScaleFn = bandScale(resources.map((entry, index) => index), [0, plotH], 0.15)
  const bandwidth = rowScaleFn.bandwidth()
  const rowStep = rowScaleFn.step()

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)
  const backdrop = svgEl("g", { "aria-hidden": "true" }, [])
  const marks = svgEl("g", null, [])
  const overlay = svgEl("g", { "aria-hidden": "true" }, [])
  plot.appendChild(backdrop)
  plot.appendChild(marks)
  plot.appendChild(overlay)

  /* Time axis along the top. */
  let tickCount = Math.max(2, Math.floor(plotW / 80))
  let ticks = timeTicks(domainMin, domainMax, tickCount)
  if (ticks.length < 2) {
    /* A coarse calendar interval can miss a short domain: ask finer. */
    tickCount = tickCount * 2
    ticks = timeTicks(domainMin, domainMax, tickCount)
  }
  const tickFormat = timeTickFormat(domainMin, domainMax, tickCount)
  for (let t = 0; t < ticks.length; t = t + 1) {
    const x = timeScaleFn(ticks[t])
    backdrop.appendChild(svgEl("line", {
      x1: x, y1: -4, x2: x, y2: plotH,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    const anchor = x < 24 ? "start" : (x > plotW - 24 ? "end" : "middle")
    backdrop.appendChild(svgEl("text", {
      x: x, y: -10, "text-anchor": anchor,
      "font-size": 10, fill: "var(--mj-text-muted, #6b7280)"
    }, tickFormat(ticks[t])))
  }
  backdrop.appendChild(svgEl("line", {
    x1: 0, y1: 0, x2: plotW, y2: 0,
    stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
  }, []))

  let anyOver = false
  const heatSeen = []

  for (let r = 0; r < resources.length; r = r + 1) {
    const entry = resources[r]
    const rowY = rowScaleFn.at(r)
    const rowBottom = rowY + bandwidth
    const pxPerLoad = bandwidth / entry.scaleMax
    const resourceId = entry.res.id !== undefined ? entry.res.id : entry.label

    if (r % 2 === 0) {
      backdrop.appendChild(svgEl("rect", {
        x: 0, y: rowY - (rowStep - bandwidth) / 2, width: plotW, height: rowStep,
        fill: "var(--mj-bg-subtle, #f8f9fb)"
      }, []))
    }
    backdrop.appendChild(svgEl("text", {
      x: -8, y: rowY + bandwidth / 2 + 4,
      "text-anchor": "end", "font-size": LABEL_FONT,
      fill: "var(--mj-text, #14181f)"
    }, fitText(entry.label, margin.left - 12, LABEL_FONT)))

    if (isHeatmap === true) {
      /* One cell per run of equal utilisation. */
      const runs = _mergeRuns(entry.segments,
        (previous, current) => Math.abs(previous.total - current.total) < 1e-9)
      for (let h = 0; h < runs.length; h = h + 1) {
        const run = runs[h]
        const fraction = run.peak / entry.capacity
        const band = _heatBand(fraction)
        if (heatSeen.indexOf(band) < 0) {
          heatSeen.push(band)
        }
        const x1 = timeScaleFn(new Date(run.start))
        const x2 = timeScaleFn(new Date(run.end))
        const heatLabel = `${entry.label}: ${_periodText(run.start, run.end)}, load ` +
          `${formatNumber(run.peak)} (${Math.round(fraction * 100)}% of capacity)`
        const cell = svgEl("rect", {
          x: x1, y: rowY, width: Math.max(x2 - x1, 1), height: bandwidth,
          fill: band.color, part: "allocation",
          tabindex: "0", role: "img", "aria-label": heatLabel
        }, [])
        cell.appendChild(svgEl("title", null, heatLabel))
        const emitRun = run
        _attachActivation(cell, () => {
          ctx.emit("mj-chart-allocation-click", {
            resource: resourceId,
            start: new Date(emitRun.start),
            end: new Date(emitRun.end - 1),
            load: emitRun.peak,
            utilization: emitRun.peak / entry.capacity
          })
        })
        marks.appendChild(cell)
      }
      continue
    }

    /* Bar mode: each allocation is stacked on the ones running below it. */
    const pieces = new Map()
    for (let s = 0; s < entry.segments.length; s = s + 1) {
      const segment = entry.segments[s]
      for (let a = 0; a < segment.active.length; a = a + 1) {
        const slot = segment.active[a]
        if (pieces.has(slot.entry) === false) {
          pieces.set(slot.entry, [])
        }
        const list = pieces.get(slot.entry)
        const last = list.length > 0 ? list[list.length - 1] : null
        if (last !== null && last.end === segment.start && Math.abs(last.offset - slot.offset) < 1e-9) {
          last.end = segment.end
        } else {
          list.push({ start: segment.start, end: segment.end, offset: slot.offset })
        }
      }
    }

    for (let a = 0; a < entry.allocations.length; a = a + 1) {
      const alloc = entry.allocations[a]
      const list = pieces.get(alloc)
      if (list === undefined) {
        continue
      }
      const color = ctx.colorFor(alloc.task !== "" ? alloc.task : `Allocation ${alloc.index + 1}`)
      const share = Math.round(alloc.load / entry.capacity * 100)
      const ariaLabel = `${entry.label}: ${alloc.task} ${formatDate(alloc.start)} – ` +
        `${formatDate(alloc.shownEnd)}, load ${formatNumber(alloc.load)} (${share}% of capacity)`
      const group = svgEl("g", {
        part: "allocation", tabindex: "0", role: "img", "aria-label": ariaLabel
      }, [])
      group.appendChild(svgEl("title", null, ariaLabel))

      const barH = Math.max(alloc.load * pxPerLoad, 1)
      let widest = null
      for (let p = 0; p < list.length; p = p + 1) {
        const piece = list[p]
        const x1 = timeScaleFn(new Date(piece.start))
        const x2 = timeScaleFn(new Date(piece.end))
        const y = rowBottom - (piece.offset + alloc.load) * pxPerLoad
        group.appendChild(svgEl("rect", {
          x: x1, y: y, width: Math.max(x2 - x1, 1), height: barH,
          fill: color, "fill-opacity": 0.55, stroke: color, "stroke-width": 1
        }, []))
        if (widest === null || x2 - x1 > widest.width) {
          widest = { x: x1, y: y, width: x2 - x1 }
        }
      }
      const emitAlloc = alloc.alloc
      _attachActivation(group, () => {
        ctx.emit("mj-chart-allocation-click", {
          resource: resourceId,
          task: emitAlloc.task,
          start: emitAlloc.start,
          end: emitAlloc.end,
          load: emitAlloc.load
        })
      })
      marks.appendChild(group)

      /* Task label inside its widest piece, only when it fits. */
      if (widest !== null && alloc.task !== "" && barH >= 12) {
        const text = fitText(alloc.task, widest.width - 8, 9)
        if (text !== "") {
          overlay.appendChild(svgEl("text", {
            x: widest.x + 4, y: widest.y + barH / 2 + 3,
            "font-size": 9, fill: "var(--mj-text, #14181f)", "pointer-events": "none"
          }, text))
        }
      }
    }

    /* Capacity line and the periods where the summed load exceeds it. */
    const ceilY = rowBottom - entry.capacity * pxPerLoad
    overlay.appendChild(svgEl("line", {
      x1: 0, y1: ceilY, x2: plotW, y2: ceilY,
      stroke: "var(--mj-text-muted, #6b7280)",
      "stroke-width": 1, "stroke-dasharray": "4 3"
    }, []))

    const overRuns = _mergeRuns(entry.segments.filter((seg) => seg.total > entry.capacity + 1e-9),
      () => true)
    for (let o = 0; o < overRuns.length; o = o + 1) {
      anyOver = true
      const run = overRuns[o]
      const x1 = timeScaleFn(new Date(run.start))
      const x2 = timeScaleFn(new Date(run.end))
      const topY = rowBottom - run.peak * pxPerLoad
      const overLabel = `${entry.label}: over capacity ${_periodText(run.start, run.end)}, ` +
        `load ${formatNumber(run.peak)} of ${formatNumber(entry.capacity)} ` +
        `(${Math.round(run.peak / entry.capacity * 100)}%)`
      const flag = svgEl("rect", {
        x: x1, y: topY, width: Math.max(x2 - x1, 1), height: Math.max(ceilY - topY, 1),
        fill: OVER_COLOR, "fill-opacity": 0.3, stroke: OVER_COLOR, "stroke-width": 2,
        part: "over-allocation", tabindex: "0", role: "img", "aria-label": overLabel
      }, [])
      flag.appendChild(svgEl("title", null, overLabel))
      const emitRun = run
      _attachActivation(flag, () => {
        ctx.emit("mj-chart-allocation-click", {
          resource: resourceId,
          start: new Date(emitRun.start),
          end: new Date(emitRun.end - 1),
          load: emitRun.peak,
          overAllocated: true
        })
      })
      marks.appendChild(flag)
    }
  }

  /* Legend. */
  const legend = []
  if (isHeatmap === true) {
    for (let h = 0; h < HEAT_BANDS.length; h = h + 1) {
      if (heatSeen.indexOf(HEAT_BANDS[h]) >= 0) {
        legend.push({ label: HEAT_BANDS[h].label, color: HEAT_BANDS[h].color })
      }
    }
  } else {
    /* Tasks are named inside their bars (and in tooltips / the table). */
    if (anyOver === true) {
      legend.push({ label: "Over capacity", color: OVER_COLOR })
    }
  }
  ctx.setLegend(legend)

  return root
}


registerRenderer("resource-allocation", render, { orientation: "horizontal" });
