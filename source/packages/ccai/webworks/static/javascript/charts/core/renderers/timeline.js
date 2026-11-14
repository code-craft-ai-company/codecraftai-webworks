/*
 * timeline.js
 *
 * Timeline / Milestone renderer.
 *
 * Registers:
 *   "timeline"  — events as circle markers along a time spine.
 *   "milestone" — the same layout with diamond markers for key dates.
 * The host's `variant` attribute ("timeline" | "milestone") overrides the
 * marker shape of the type.
 *
 * ctx.raw shape:
 *   events: [{ id, label, date, group?, icon?, description?, status?, kind? }]
 *   phases?: [{ label, start, end }]
 *
 *   date         Date, epoch ms or ISO string ("YYYY-MM-DD" = local day);
 *                events without a usable date (or outside the start-date /
 *                end-date window) are listed in the data table but not drawn
 *   group        one lane per distinct group (multi-lane layout)
 *   status       completed | active | planned | at-risk (planned markers
 *                are hollow, so status is not shown by colour alone)
 *   kind         release (diamond) | freeze (triangle) | tag | milestone
 *                (circle): the marker shape, and its colour when the event
 *                has no status
 *   icon         a short glyph shown before the label
 *   description  shown in the marker's tooltip and the data table
 *   phases       background bands (end date inclusive)
 *
 * Layout: horizontal by default (time runs left to right, labels are placed
 * above and below each spine in tiers so they do not overlap; a label with
 * no free slot is left to the tooltip). orientation="vertical" runs time
 * down the page with labels to the right of each spine.
 *
 * Options:
 *   variant     "timeline" | "milestone": the default marker shape
 *   today       "false" hides the today line (drawn when today is in range)
 *   start-date  fixes the start of the time axis
 *   end-date    fixes the end of the time axis (a YYYY-MM-DD end is
 *               inclusive)
 *   dim-past    draws events more than a day before today faded and adds
 *               past / today / upcoming to each marker's accessible name
 *   density     "compact": smaller, shorter labels
 *
 * Events:
 *   mj-chart-event-click { id, label, date, group, status, kind, index }
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatDate, parseDate } from "../svgdraw.js";
import { timeScale, seriesColor } from "../scales.js";
import { booleanOption } from "../chartoptions.js";


/* Status -> semantic marker colour (a status, not a data series). */
const STATUS_COLORS = {
  "completed": "var(--mj-color-success, #15803d)",
  "active":    "var(--mj-accent, #2563eb)",
  "planned":   "var(--mj-text-muted, #6b7280)",
  "at-risk":   "var(--mj-color-danger, #b91c1c)"
};

const STATUS_LABELS = {
  "completed": "Completed",
  "active":    "Active",
  "planned":   "Planned",
  "at-risk":   "At risk"
};

/* Kind -> marker shape and semantic colour (a kind, not a data series). */
const KIND_SHAPES = {
  "release":   "diamond",
  "freeze":    "triangle",
  "milestone": "circle",
  "tag":       "circle"
};

const KIND_COLORS = {
  "release":   "var(--mj-color-success, #15803d)",
  "freeze":    "var(--mj-color-warning, #b45309)",
  "milestone": "var(--mj-accent, #2563eb)",
  "tag":       "var(--mj-color-info, #0e7490)"
};

const KIND_LABELS = {
  "release":   "Release",
  "freeze":    "Freeze",
  "milestone": "Milestone",
  "tag":       "Tag"
};

const TODAY_COLOR = "var(--mj-accent, #2563eb)";
const PAST_OPACITY = 0.55;

const MARKER_R = 7;
const DIAMOND_SIZE = 9;
const LABEL_FONT = 11;
const LABEL_FONT_COMPACT = 10;
const TIER_GAP = 5;
const CHAR_WIDTH = 0.56;
const DAY_MS = 86400000;


function _dayInfo(value, isEnd) {
  /*
   * A window bound: a Date, or null. A `YYYY-MM-DD` end is inclusive (the
   * instant returned is the start of the next day).
   */
  let date = parseDate(value)
  if (date !== null && isEnd === true && typeof value === "string" &&
      /^\d{4}-\d{2}-\d{2}$/.test(value.trim()) === true) {
    date = new Date(date.getFullYear(), date.getMonth(), date.getDate() + 1)
  }
  return date
}


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


function _readEvents(rawEvents) {
  /*
   * Parse the events.
   *
   * :returns: { all, dated } -- `all` in data order (for the table),
   *     `dated` (usable date only) sorted by date, then data order.
   */
  const all = []
  const list = Array.isArray(rawEvents) === true ? rawEvents : []
  for (let index = 0; index < list.length; index = index + 1) {
    const event = list[index]
    if (event === null || typeof event !== "object") {
      continue
    }
    const icon = typeof event.icon === "string" && event.icon.trim().length > 0 &&
      event.icon.trim().length <= 4 ? event.icon.trim() : ""
    const label = event.label !== undefined && event.label !== null ? String(event.label) : ""
    all.push({
      event: event,
      index: index,
      date: parseDate(event.date),
      label: label,
      shown: icon !== "" ? `${icon} ${label}` : label,
      lane: event.group !== undefined && event.group !== null && event.group !== ""
        ? String(event.group) : null,
      status: event.status !== undefined && event.status !== null ? String(event.status) : "",
      kind: event.kind !== undefined && event.kind !== null ? String(event.kind) : "",
      description: event.description !== undefined && event.description !== null
        ? String(event.description) : "",
      state: ""
    })
  }
  const dated = all.filter((entry) => entry.date !== null)
  dated.sort((a, b) => {
    const difference = a.date.getTime() - b.date.getTime()
    return difference !== 0 ? difference : a.index - b.index
  })
  const result = { all: all, dated: dated }
  return result
}


function _drawMarker(entry, x, y, color, isMilestone, ctx) {
  /*
   * The focusable marker of one event. The shape follows the event's kind,
   * else the type (diamond for milestone, circle for timeline).
   */
  const hollow = entry.status === "planned"
  const statusText = STATUS_LABELS[entry.status] !== undefined
    ? STATUS_LABELS[entry.status] : entry.status
  let title = `${entry.label}: ${formatDate(entry.date)}`
  if (entry.kind !== "") {
    title = title + `, ${KIND_LABELS[entry.kind] !== undefined ? KIND_LABELS[entry.kind] : entry.kind}`
  }
  if (entry.lane !== null) {
    title = title + `, ${entry.lane}`
  }
  if (statusText !== "") {
    title = title + `, ${statusText}`
  }
  if (entry.state !== "") {
    title = title + `, ${entry.state}`
  }
  if (entry.description !== "") {
    title = title + `. ${entry.description}`
  }

  let shape = isMilestone === true ? "diamond" : "circle"
  if (KIND_SHAPES[entry.kind] !== undefined) {
    shape = KIND_SHAPES[entry.kind]
  }
  const common = {
    fill: hollow === true ? "var(--mj-surface, #ffffff)" : color,
    stroke: hollow === true ? color : "var(--mj-surface, #ffffff)",
    "stroke-width": hollow === true ? 2 : 1.5,
    opacity: entry.state === "past" ? PAST_OPACITY : null,
    part: "marker", tabindex: "0", role: "img", "aria-label": title,
    "data-mark": `event:${entry.index}`
  }
  let marker = null
  if (shape === "diamond") {
    marker = svgEl("polygon", {
      points: `${x},${y - DIAMOND_SIZE} ${x + DIAMOND_SIZE},${y} ${x},${y + DIAMOND_SIZE} ${x - DIAMOND_SIZE},${y}`,
      ...common
    }, [])
  } else if (shape === "triangle") {
    marker = svgEl("polygon", {
      points: `${x},${y - DIAMOND_SIZE} ${x + DIAMOND_SIZE},${y + DIAMOND_SIZE * 0.6} ${x - DIAMOND_SIZE},${y + DIAMOND_SIZE * 0.6}`,
      ...common
    }, [])
  } else {
    marker = svgEl("circle", { cx: x, cy: y, r: MARKER_R, ...common }, [])
  }
  marker.appendChild(svgEl("title", null, title))

  const emitEntry = entry
  const clickHandler = () => {
    ctx.emit("mj-chart-event-click", {
      id: emitEntry.event.id,
      label: emitEntry.event.label,
      date: emitEntry.event.date,
      group: emitEntry.event.group,
      status: emitEntry.event.status,
      kind: emitEntry.event.kind,
      index: emitEntry.index
    })
  }
  marker.addEventListener("click", clickHandler)
  marker.addEventListener("keydown", (keyEvent) => {
    if (keyEvent.key === "Enter" || keyEvent.key === " ") {
      keyEvent.preventDefault()
      clickHandler()
    }
  })
  return marker
}


function _layoutHorizontalLane(entries, scale, laneTop, laneH, plotW, layers, colorOf, isMilestone, ctx) {
  /*
   * One horizontal lane: a spine across the lane's middle, markers on it,
   * labels in tiers above and below. A label goes on its preferred side
   * (alternating in date order) in the first tier where it does not overlap
   * an earlier label, else the other side; with no free slot it is left to
   * the tooltip.
   */
  const spineY = laneTop + laneH / 2
  layers.decor.appendChild(svgEl("line", {
    x1: 0, y1: spineY, x2: plotW, y2: spineY,
    stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 2
  }, []))

  const font = layers.labelFont
  const tierH = font + TIER_GAP
  const tiers = Math.max(Math.floor((laneH / 2 - MARKER_R - 6) / tierH), 0)
  const placed = { above: [], below: [] }
  for (let t = 0; t < tiers; t = t + 1) {
    placed.above.push([])
    placed.below.push([])
  }
  const maxLabelW = Math.max(Math.min(plotW / 3, layers.maxLabelW), 40)

  let previousX = -Infinity
  for (let e = 0; e < entries.length; e = e + 1) {
    const entry = entries[e]
    /* Events on (nearly) the same date are nudged apart so none hides another. */
    const x = Math.max(scale(entry.date), previousX + MARKER_R * 2 - 2)
    previousX = x
    const color = colorOf(entry)

    const text = _fitText(entry.shown, maxLabelW, font)
    const width = _textWidth(text, font)
    const centre = Math.min(Math.max(x, width / 2), plotW - width / 2)
    const left = centre - width / 2 - 4
    const right = centre + width / 2 + 4

    const preferred = e % 2 === 0 ? "above" : "below"
    const sides = preferred === "above" ? ["above", "below"] : ["below", "above"]
    let slot = null
    for (let t = 0; t < tiers && slot === null && text !== ""; t = t + 1) {
      for (let s = 0; s < sides.length && slot === null; s = s + 1) {
        const taken = placed[sides[s]][t]
        let free = true
        for (let k = 0; k < taken.length; k = k + 1) {
          if (left < taken[k][1] && right > taken[k][0]) {
            free = false
            break
          }
        }
        if (free === true) {
          slot = { side: sides[s], tier: t }
          taken.push([left, right])
        }
      }
    }

    if (slot !== null) {
      const offset = MARKER_R + 6 + slot.tier * tierH
      const baseline = slot.side === "above"
        ? spineY - offset
        : spineY + offset + font * 0.8
      const stemEnd = slot.side === "above"
        ? baseline + 2
        : baseline - font * 0.8 - 2
      layers.decor.appendChild(svgEl("line", {
        x1: x, y1: spineY, x2: x, y2: stemEnd,
        stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
      }, []))
      layers.labels.appendChild(svgEl("text", {
        x: centre, y: baseline, "text-anchor": "middle",
        "font-size": font, fill: "var(--mj-text, #14181f)", part: "marker-label",
        opacity: entry.state === "past" ? PAST_OPACITY + 0.2 : null
      }, text))
    }
    layers.marks.appendChild(_drawMarker(entry, x, spineY, color, isMilestone, ctx))
  }
  return
}


function _layoutVerticalLane(entries, scale, laneLeft, laneW, plotH, layers, colorOf, isMilestone, ctx) {
  /*
   * One vertical lane: a spine down the lane's left side and labels to the
   * right. A label that would overlap the previous one moves down and gets
   * a leader line; one that would leave the plot is left to the tooltip.
   */
  const spineX = laneLeft + MARKER_R + 6
  layers.decor.appendChild(svgEl("line", {
    x1: spineX, y1: 0, x2: spineX, y2: plotH,
    stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 2
  }, []))

  const font = layers.labelFont
  const labelX = spineX + MARKER_R + 8
  const maxLabelW = Math.min(laneW - (labelX - laneLeft) - 6, layers.maxLabelW * 1.5)
  let nextFree = -Infinity

  let previousY = -Infinity
  for (let e = 0; e < entries.length; e = e + 1) {
    const entry = entries[e]
    /* Events on (nearly) the same date are nudged apart so none hides another. */
    const y = Math.max(scale(entry.date), previousY + MARKER_R * 2 - 2)
    previousY = y
    const color = colorOf(entry)
    const text = _fitText(entry.shown, maxLabelW, font)
    const wanted = y + font * 0.35
    const baseline = Math.max(wanted, nextFree)

    if (text !== "" && baseline <= plotH + font) {
      if (baseline - wanted > 2) {
        layers.decor.appendChild(svgEl("polyline", {
          points: `${spineX + MARKER_R},${y} ${labelX - 4},${baseline - font * 0.35}`,
          fill: "none", stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
        }, []))
      }
      layers.labels.appendChild(svgEl("text", {
        x: labelX, y: baseline, "font-size": font, fill: "var(--mj-text, #14181f)", part: "marker-label",
        opacity: entry.state === "past" ? PAST_OPACITY + 0.2 : null
      }, text))
      nextFree = baseline + font + 3
    }
    layers.marks.appendChild(_drawMarker(entry, spineX, y, color, isMilestone, ctx))
  }
  return
}


export function render(ctx) {
  /*
   * Render a timeline or milestone chart.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const raw = ctx.raw !== null && ctx.raw !== undefined ? ctx.raw : {}
  const parsed = _readEvents(raw.events)

  const variant = ctx.attrs("style", "")
  let isMilestone = ctx.type === "milestone"
  if (variant === "milestone") {
    isMilestone = true
  } else if (variant === "timeline") {
    isMilestone = false
  }
  const vertical = ctx.orientation === "vertical"
  const compact = ctx.attrs("density", "normal") === "compact"
  const dimPast = booleanOption(ctx, "dim-past", false)
  const nowMs = Date.now()

  const root = svgEl("g", { part: "plot" }, [])

  /* Past / today / upcoming, when asked for. */
  if (dimPast === true) {
    for (let e = 0; e < parsed.dated.length; e = e + 1) {
      const entry = parsed.dated[e]
      const time = entry.date.getTime()
      entry.state = time < nowMs - DAY_MS ? "past" : (time <= nowMs + DAY_MS ? "today" : "upcoming")
    }
  }

  const hasKinds = parsed.all.some((entry) => entry.kind !== "")
  const columns = ["Event", "Date", "Group", "Status"]
  if (hasKinds === true) {
    columns.push("Kind")
  }
  columns.push("Description")
  ctx.setTable({
    columns: columns,
    rows: parsed.all.map((entry) => {
      const row = [
        entry.label, entry.date !== null ? formatDate(entry.date) : "",
        entry.lane !== null ? entry.lane : "", entry.status
      ]
      if (hasKinds === true) {
        row.push(entry.kind)
      }
      row.push(entry.description)
      return row
    })
  })

  /* The window: the start-date / end-date options, else the data, padded. */
  const fixedStart = _dayInfo(ctx.attrs("start-date", null), false)
  const fixedEnd = _dayInfo(ctx.attrs("end-date", null), true)
  const events = parsed.dated.filter((entry) => {
    const time = entry.date.getTime()
    const afterStart = fixedStart === null || time >= fixedStart.getTime()
    const beforeEnd = fixedEnd === null || time <= fixedEnd.getTime()
    return afterStart === true && beforeEnd === true
  })
  if (events.length === 0 && (fixedStart === null || fixedEnd === null)) {
    return root
  }

  /* Lanes in order of first appearance; ungrouped events share one lane. */
  const laneNames = []
  const laneEvents = new Map()
  for (let e = 0; e < events.length; e = e + 1) {
    const name = events[e].lane !== null ? events[e].lane : ""
    if (laneEvents.has(name) === false) {
      laneEvents.set(name, [])
      laneNames.push(name)
    }
    laneEvents.get(name).push(events[e])
  }
  if (laneNames.length === 0) {
    laneNames.push("")
    laneEvents.set("", [])
  }
  const multiLane = laneNames.length > 1 || (laneNames.length === 1 && laneNames[0] !== "")

  /* Time domain, padded so the end markers and labels stay inside. */
  let startMs = events.length > 0 ? events[0].date.getTime() : fixedStart.getTime()
  let endMs = events.length > 0 ? events[events.length - 1].date.getTime() : fixedEnd.getTime()
  if (startMs === endMs) {
    startMs = startMs - DAY_MS
    endMs = endMs + DAY_MS
  }
  const pad = (endMs - startMs) * 0.05
  let domainStart = new Date(startMs - pad)
  let domainEnd = new Date(endMs + pad)
  if (fixedStart !== null) {
    domainStart = fixedStart
  }
  if (fixedEnd !== null) {
    domainEnd = fixedEnd
  }
  if (domainEnd.getTime() <= domainStart.getTime()) {
    domainEnd = new Date(domainStart.getTime() + DAY_MS)
  }
  const domain = [domainStart, domainEnd]

  /* Colours: status when the event has one, else its kind, else its lane. */
  const statusesSeen = []
  const kindsSeen = []
  const colorOf = (entry) => {
    if (STATUS_COLORS[entry.status] !== undefined) {
      if (statusesSeen.indexOf(entry.status) < 0) {
        statusesSeen.push(entry.status)
      }
      return STATUS_COLORS[entry.status]
    }
    if (KIND_COLORS[entry.kind] !== undefined) {
      if (kindsSeen.indexOf(entry.kind) < 0) {
        kindsSeen.push(entry.kind)
      }
      return KIND_COLORS[entry.kind]
    }
    const color = multiLane === true ? ctx.colorFor(entry.lane !== null ? entry.lane : "") : ctx.colorFor(0)
    return color
  }

  const labelFont = compact === true ? LABEL_FONT_COMPACT : LABEL_FONT
  let longestLane = 0
  for (let l = 0; l < laneNames.length; l = l + 1) {
    longestLane = Math.max(longestLane, _textWidth(laneNames[l], LABEL_FONT))
  }

  let margin = null
  if (vertical === true) {
    margin = { top: multiLane === true ? 28 : 12, right: 16, bottom: 12, left: 76 }
  } else {
    const gutter = multiLane === true ? Math.min(longestLane + 16, Math.max(ctx.width * 0.25, 60)) : 16
    margin = { top: 8, right: 16, bottom: 28, left: gutter }
  }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)
  const layers = {
    bands: svgEl("g", { "aria-hidden": "true" }, []),
    axis: svgEl("g", { "aria-hidden": "true" }, []),
    decor: svgEl("g", { "aria-hidden": "true" }, []),
    labels: svgEl("g", { "aria-hidden": "true" }, []),
    marks: svgEl("g", null, []),
    labelFont: labelFont,
    maxLabelW: compact === true ? 12 * labelFont * CHAR_WIDTH : 180
  }
  plot.appendChild(layers.bands)
  plot.appendChild(layers.axis)
  plot.appendChild(layers.decor)
  plot.appendChild(layers.labels)
  plot.appendChild(layers.marks)

  const scale = timeScale(domain, vertical === true ? [0, plotH] : [0, plotW])
  const along = vertical === true ? plotH : plotW
  let tickCount = vertical === true
    ? Math.max(2, Math.floor(plotH / 48))
    : Math.max(2, Math.floor(plotW / 90))
  let tickDates = scale.ticks(tickCount)
  if (tickDates.length < 2) {
    /* A coarse calendar interval can miss a short domain: ask finer. */
    tickCount = tickCount * 2
    tickDates = scale.ticks(tickCount)
  }
  const tickFormat = scale.tickFormat(tickCount)

  /* Phase bands behind everything, coloured by position. */
  const phases = Array.isArray(raw.phases) === true ? raw.phases : []
  for (let p = 0; p < phases.length; p = p + 1) {
    const phase = phases[p]
    if (phase === null || typeof phase !== "object") {
      continue
    }
    const phaseStart = _dayInfo(phase.start, false)
    const phaseEnd = _dayInfo(phase.end, true)
    if (phaseStart === null || phaseEnd === null) {
      continue
    }
    const from = Math.max(scale(phaseStart), 0)
    const to = Math.min(scale(phaseEnd), along)
    if (to <= from) {
      continue
    }
    const box = vertical === true
      ? { x: 0, y: from, width: plotW, height: to - from }
      : { x: from, y: 0, width: to - from, height: plotH }
    const band = svgEl("rect", {
      ...box, fill: seriesColor(p), "fill-opacity": 0.12, part: "phase-band"
    }, [])
    const phaseName = phase.label !== undefined && phase.label !== null ? String(phase.label) : ""
    if (phaseName !== "") {
      band.appendChild(svgEl("title", null, phaseName))
    }
    layers.bands.appendChild(band)
  }

  if (vertical === true) {
    for (let t = 0; t < tickDates.length; t = t + 1) {
      const y = scale(tickDates[t])
      layers.axis.appendChild(svgEl("line", {
        x1: -4, y1: y, x2: plotW, y2: y,
        stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
      }, []))
      layers.axis.appendChild(svgEl("text", {
        x: -8, y: y + 3.5, "text-anchor": "end",
        "font-size": 10, fill: "var(--mj-text-muted, #6b7280)", part: "time-axis"
      }, tickFormat(tickDates[t])))
    }
  } else {
    for (let t = 0; t < tickDates.length; t = t + 1) {
      const x = scale(tickDates[t])
      layers.axis.appendChild(svgEl("line", {
        x1: x, y1: plotH, x2: x, y2: plotH + 4,
        stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1
      }, []))
      const anchor = x < 24 ? "start" : (x > plotW - 24 ? "end" : "middle")
      layers.axis.appendChild(svgEl("text", {
        x: x, y: plotH + 16, "text-anchor": anchor,
        "font-size": 10, fill: "var(--mj-text-muted, #6b7280)", part: "time-axis"
      }, tickFormat(tickDates[t])))
    }
    layers.axis.appendChild(svgEl("line", {
      x1: 0, y1: plotH, x2: plotW, y2: plotH,
      stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1, part: "time-axis"
    }, []))
  }

  /* Today: a dashed line across the lanes, when today is in range. */
  if (booleanOption(ctx, "today", true) === true) {
    const position = scale(new Date(nowMs))
    if (position >= 0 && position <= along) {
      const line = vertical === true
        ? { x1: -4, y1: position, x2: plotW, y2: position }
        : { x1: position, y1: 0, x2: position, y2: plotH }
      layers.axis.appendChild(svgEl("line", {
        ...line, stroke: TODAY_COLOR, "stroke-width": 1.5, "stroke-dasharray": "4 3", part: "today-marker"
      }, []))
      const flip = vertical === false && position + 36 > plotW
      const labelAt = vertical === true
        ? { x: plotW - 2, y: position - 3, "text-anchor": "end" }
        : { x: flip === true ? position - 3 : position + 3, y: 9, "text-anchor": flip === true ? "end" : "start" }
      layers.axis.appendChild(svgEl("text", {
        ...labelAt, "font-size": 9, fill: TODAY_COLOR, part: "today-label"
      }, "Today"))
    }
  }

  /* Lanes share the cross axis equally, whatever the chart's size. */
  const laneCount = laneNames.length
  for (let l = 0; l < laneCount; l = l + 1) {
    const name = laneNames[l]
    const entries = laneEvents.get(name)
    if (vertical === true) {
      const laneW = plotW / laneCount
      const laneLeft = l * laneW
      if (multiLane === true) {
        layers.labels.appendChild(svgEl("text", {
          x: laneLeft + 4, y: -12, "font-size": LABEL_FONT, "font-weight": "bold",
          fill: "var(--mj-text, #14181f)"
        }, _fitText(name, laneW - 8, LABEL_FONT)))
      }
      _layoutVerticalLane(entries, scale, laneLeft, laneW, plotH, layers, colorOf, isMilestone, ctx)
    } else {
      const laneH = plotH / laneCount
      const laneTop = l * laneH
      if (multiLane === true) {
        layers.labels.appendChild(svgEl("text", {
          x: -8, y: laneTop + laneH / 2 + 4, "text-anchor": "end",
          "font-size": LABEL_FONT, "font-weight": "bold", fill: "var(--mj-text, #14181f)"
        }, _fitText(name, margin.left - 12, LABEL_FONT)))
        if (l > 0) {
          layers.decor.appendChild(svgEl("line", {
            x1: -margin.left, y1: laneTop, x2: plotW, y2: laneTop,
            stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
          }, []))
        }
      }
      _layoutHorizontalLane(entries, scale, laneTop, laneH, plotW, layers, colorOf, isMilestone, ctx)
    }
  }

  /* Legend: statuses, else kinds, else lanes that the colours stand for. */
  const legend = []
  if (statusesSeen.length > 0) {
    const order = Object.keys(STATUS_COLORS)
    for (let s = 0; s < order.length; s = s + 1) {
      if (statusesSeen.indexOf(order[s]) >= 0) {
        legend.push({ label: STATUS_LABELS[order[s]], color: STATUS_COLORS[order[s]] })
      }
    }
  } else if (kindsSeen.length > 0) {
    const order = Object.keys(KIND_COLORS)
    for (let k = 0; k < order.length; k = k + 1) {
      if (kindsSeen.indexOf(order[k]) >= 0) {
        legend.push({ label: KIND_LABELS[order[k]], color: KIND_COLORS[order[k]] })
      }
    }
  } else if (multiLane === true) {
    for (let l = 0; l < laneNames.length; l = l + 1) {
      legend.push({ label: laneNames[l] !== "" ? laneNames[l] : "Other", color: ctx.colorFor(laneNames[l]) })
    }
  }
  ctx.setLegend(legend)

  return root
}


registerRenderer("timeline", render, { orientation: "horizontal" });
registerRenderer("milestone", render, { orientation: "horizontal" });
