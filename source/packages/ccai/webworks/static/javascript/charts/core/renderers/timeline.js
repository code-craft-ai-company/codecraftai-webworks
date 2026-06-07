/*
 * timeline.js
 *
 * Timeline / Milestone renderer.
 *
 * Registers:
 *   "timeline"  — events plotted as circle markers along a time axis; labels
 *                 alternate above/below the spine to reduce overlap; multi-lane
 *                 layout supported via the event `group` field.
 *   "milestone" — diamond/flag markers; selected by style="milestone".
 *
 * ctx.raw shape:
 *   events: [{ id, label, date, group?, icon?, description?, status? }]
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, formatDate } from "../svgdraw.js";
import { timeScale } from "../scales.js";


/* Status → CSS color token for milestone markers. */
const STATUS_COLORS = {
  "completed": "var(--mj-color-success, #15803d)",
  "planned":   "var(--mj-color-neutral-500, #6b7280)",
  "at-risk":   "var(--mj-color-danger, #b91c1c)",
  "active":    "var(--mj-color-accent-500, #2563eb)"
};

const STEM_LENGTH = 32
const MARKER_R = 7
const DIAMOND_SIZE = 9
const LABEL_FONT = 11


function _markerColor(event, colorFor, index) {
  /*
   * Resolve the marker color for an event.
   */
  if (event.status !== undefined && STATUS_COLORS[event.status] !== undefined) {
    return STATUS_COLORS[event.status]
  }
  const color = colorFor(index)
  return color
}


function _drawDiamond(x, y, size) {
  /*
   * Return SVG points string for a diamond centered at (x, y).
   */
  const points = `${x},${y - size} ${x + size},${y} ${x},${y + size} ${x - size},${y}`
  return points
}


function _buildSingleLane(events, timeScaleFn, plotW, plotH, horizontal, isMilestone, ctx) {
  /*
   * Draw a single-lane timeline; labels alternate above/below the spine.
   * Returns a <g> with all event elements.
   */
  const group = svgEl("g", null, [])

  /* Spine position along the cross-axis. */
  const spinePos = plotH / 2

  /* Spine line. */
  group.appendChild(svgEl("line", {
    x1: 0, y1: spinePos, x2: plotW, y2: spinePos,
    stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 2
  }, []))

  for (let index = 0; index < events.length; index = index + 1) {
    const event = events[index]
    const date = new Date(event.date)
    const markerX = timeScaleFn(date)
    const markerY = spinePos

    /* Alternate label above / below spine. */
    const above = index % 2 === 0
    const stemEndY = above
      ? markerY - MARKER_R - STEM_LENGTH
      : markerY + MARKER_R + STEM_LENGTH
    const labelY = above
      ? stemEndY - 4
      : stemEndY + LABEL_FONT + 4

    const color = _markerColor(event, ctx.colorFor, index)
    const labelText = event.label !== undefined ? String(event.label) : ""
    const titleText = `${escapeHtml(labelText)}: ${formatDate(date)}`

    /* Stem. */
    group.appendChild(svgEl("line", {
      x1: markerX, y1: markerY,
      x2: markerX, y2: stemEndY,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))

    /* Marker shape. */
    let marker = null
    if (isMilestone === true) {
      marker = svgEl("polygon", {
        points: _drawDiamond(markerX, markerY, DIAMOND_SIZE),
        fill: color, part: "marker"
      }, [])
    } else {
      marker = svgEl("circle", {
        cx: markerX, cy: markerY, r: MARKER_R,
        fill: color, part: "marker"
      }, [])
    }

    marker.setAttribute("tabindex", "0")
    marker.setAttribute("role", "img")
    marker.setAttribute("aria-label", titleText)
    marker.appendChild(svgEl("title", null, titleText))

    const emitEvent = event
    const clickHandler = () => {
      ctx.emit("mj-chart-event-click", {
        id: emitEvent.id,
        label: emitEvent.label,
        date: emitEvent.date
      })
    }
    marker.addEventListener("click", clickHandler)
    marker.addEventListener("keydown", (keyEvent) => {
      if (keyEvent.key === "Enter" || keyEvent.key === " ") {
        keyEvent.preventDefault()
        clickHandler()
      }
    })
    group.appendChild(marker)

    /* Label. */
    group.appendChild(svgEl("text", {
      x: markerX, y: labelY,
      "text-anchor": "middle",
      "font-size": LABEL_FONT,
      fill: "var(--mj-text, #14181f)"
    }, escapeHtml(labelText)))
  }

  return group
}


function _buildMultiLane(events, timeScaleFn, plotW, horizontal, isMilestone, ctx) {
  /*
   * Draw a multi-lane timeline, one lane per unique group value.
   * Returns a <g> with all elements plus the required total height.
   */
  const laneOrder = []
  const laneMap = {}
  for (let index = 0; index < events.length; index = index + 1) {
    const event = events[index]
    const lane = event.group !== undefined ? String(event.group) : "default"
    if (laneMap[lane] === undefined) {
      laneOrder.push(lane)
      laneMap[lane] = []
    }
    laneMap[lane].push({ event: event, index: index })
  }

  const group = svgEl("g", null, [])
  const laneH = STEM_LENGTH * 2 + MARKER_R * 2 + LABEL_FONT * 2 + 16
  let currentY = 0

  for (let l = 0; l < laneOrder.length; l = l + 1) {
    const laneName = laneOrder[l]
    const laneEvents = laneMap[laneName]
    const spineY = currentY + laneH / 2

    /* Lane label. */
    group.appendChild(svgEl("text", {
      x: 0, y: currentY + LABEL_FONT,
      "font-size": LABEL_FONT, "font-weight": "bold",
      fill: "var(--mj-text-muted, #6b7280)"
    }, escapeHtml(laneName)))

    /* Spine. */
    group.appendChild(svgEl("line", {
      x1: 0, y1: spineY, x2: plotW, y2: spineY,
      stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
    }, []))

    for (let e = 0; e < laneEvents.length; e = e + 1) {
      const entry = laneEvents[e]
      const event = entry.event
      const index = entry.index
      const date = new Date(event.date)
      const markerX = timeScaleFn(date)
      const markerY = spineY
      const stemEndY = markerY - MARKER_R - STEM_LENGTH / 2
      const labelY = stemEndY - 4

      const color = _markerColor(event, ctx.colorFor, index)
      const labelText = event.label !== undefined ? String(event.label) : ""
      const titleText = `${escapeHtml(labelText)}: ${formatDate(date)}`

      group.appendChild(svgEl("line", {
        x1: markerX, y1: markerY,
        x2: markerX, y2: stemEndY,
        stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
      }, []))

      let marker = null
      if (isMilestone === true) {
        marker = svgEl("polygon", {
          points: _drawDiamond(markerX, markerY, DIAMOND_SIZE),
          fill: color, part: "marker"
        }, [])
      } else {
        marker = svgEl("circle", {
          cx: markerX, cy: markerY, r: MARKER_R,
          fill: color, part: "marker"
        }, [])
      }

      marker.setAttribute("tabindex", "0")
      marker.setAttribute("role", "img")
      marker.setAttribute("aria-label", titleText)
      marker.appendChild(svgEl("title", null, titleText))

      const emitEvent = event
      const clickHandler = () => {
        ctx.emit("mj-chart-event-click", {
          id: emitEvent.id,
          label: emitEvent.label,
          date: emitEvent.date
        })
      }
      marker.addEventListener("click", clickHandler)
      marker.addEventListener("keydown", (keyEvent) => {
        if (keyEvent.key === "Enter" || keyEvent.key === " ") {
          keyEvent.preventDefault()
          clickHandler()
        }
      })
      group.appendChild(marker)

      group.appendChild(svgEl("text", {
        x: markerX, y: labelY,
        "text-anchor": "middle",
        "font-size": LABEL_FONT,
        fill: "var(--mj-text, #14181f)"
      }, escapeHtml(labelText)))
    }

    currentY = currentY + laneH
    /* Lane separator. */
    group.appendChild(svgEl("line", {
      x1: 0, y1: currentY, x2: plotW, y2: currentY,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 0.5
    }, []))
  }

  return group
}


export function render(ctx) {
  /*
   * Render a timeline or milestone chart.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const raw = ctx.raw
  const events = (raw !== null && raw !== undefined && Array.isArray(raw.events))
    ? raw.events : []

  const isMilestone = ctx.attrs("style", "") === "milestone"
  const horizontal = ctx.orientation !== "vertical"

  const root = svgEl("g", { part: "plot" }, [])

  if (events.length === 0) {
    return root
  }

  /* Date domain from event dates. */
  let dateMin = null
  let dateMax = null
  for (let index = 0; index < events.length; index = index + 1) {
    const event = events[index]
    const date = new Date(event.date)
    if (dateMin === null || date < dateMin) {
      dateMin = date
    }
    if (dateMax === null || date > dateMax) {
      dateMax = date
    }
  }
  if (dateMin === null) {
    dateMin = new Date()
  }
  if (dateMax === null) {
    dateMax = new Date(dateMin.getTime() + 30 * 86400000)
  }
  if (dateMin.getTime() === dateMax.getTime()) {
    dateMin = new Date(dateMin.getTime() - 86400000)
    dateMax = new Date(dateMax.getTime() + 86400000)
  }
  const pad = (dateMax.getTime() - dateMin.getTime()) * 0.05
  dateMin = new Date(dateMin.getTime() - pad)
  dateMax = new Date(dateMax.getTime() + pad)

  const margin = { top: 12, right: 16, bottom: 32, left: 16 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  /* Check for multi-lane. */
  const hasGroups = events.some((event) => event.group !== undefined && event.group !== null)

  const timeScaleFn = timeScale([dateMin, dateMax], horizontal ? [0, plotW] : [0, plotH])

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  /* Time-axis tick labels along the bottom. */
  const spanMs = dateMax.getTime() - dateMin.getTime()
  const spanDays = spanMs / 86400000
  const tickCount = Math.max(2, Math.floor(plotW / 80))
  const tickDates = timeScaleFn.ticks(tickCount)

  for (let t = 0; t < tickDates.length; t = t + 1) {
    const tick = tickDates[t]
    const x = timeScaleFn(tick)
    plot.appendChild(svgEl("line", {
      x1: x, y1: plotH, x2: x, y2: plotH + 4,
      stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1
    }, []))
    plot.appendChild(svgEl("text", {
      x: x, y: plotH + 16, "text-anchor": "middle",
      "font-size": 10, fill: "var(--mj-text-muted, #6b7280)"
    }, formatDate(tick, spanDays <= 180
      ? { month: "short", day: "numeric" }
      : { year: "numeric", month: "short" })))
  }

  /* Axis spine along the bottom. */
  plot.appendChild(svgEl("line", {
    x1: 0, y1: plotH, x2: plotW, y2: plotH,
    stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
  }, []))

  /* Draw events. */
  let eventsGroup = null
  if (hasGroups === true) {
    eventsGroup = _buildMultiLane(events, timeScaleFn, plotW, horizontal, isMilestone, ctx)
  } else {
    eventsGroup = _buildSingleLane(events, timeScaleFn, plotW, plotH, horizontal, isMilestone, ctx)
  }
  plot.appendChild(eventsGroup)

  return root
}


registerRenderer("timeline", render);
registerRenderer("milestone", render);
