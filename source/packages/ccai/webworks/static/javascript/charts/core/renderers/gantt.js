/*
 * gantt.js
 *
 * Gantt / Roadmap renderer.
 *
 * Registers:
 *   "gantt"   — project tasks as horizontal bars over a time axis, one row
 *               per task, with progress fills, collapsible group header
 *               rows, finish-to-start dependency arrows, milestone markers,
 *               phase bands and a today line.
 *   "roadmap" — strategic view: one lane per group in which bars that do
 *               not overlap share a row (overlapping ones stack), calendar
 *               period columns (quarters, months or half-years) or named
 *               bucket columns, status colours and icons, markers, phases
 *               and a today line.
 *
 * The drawing follows the type key; the host's `variant` attribute
 * (variant="roadmap" | "gantt") overrides it. <mj-gantt-chart> and
 * <mj-roadmap-chart> are these two types with their own data shapes.
 *
 * ctx.raw shape:
 *   tasks:    [{ id, label, start, end, progress?, assignee?, group?,
 *                depends?, status?, milestone?, bucket?, description? }]
 *   groups?:  [{ id, label }]          order and names of the groups (gantt
 *                                      header rows / roadmap lanes); a task
 *                                      names its group by id or label
 *   markers?: [{ label, date }]        milestone lines
 *   phases?:  [{ label, start, end }]  background bands
 *   buckets?: [{ id, label }]          roadmap columns in mode="bucket"; a
 *                                      task names its column in `bucket`
 *
 * Dates:
 *   "YYYY-MM-DD"  a local calendar day. An END date is inclusive: a task
 *                 from 2025-06-09 to 2025-06-13 covers five whole days.
 *   "YYYY-MM"     a calendar month (the end covers the whole month).
 *   "YYYY-Qn"     a quarter (the end covers the whole quarter).
 *   other         an ISO date-time or epoch milliseconds, used as given.
 * A task with no usable dates keeps its row and is marked "No dates"; a task
 * with only a start runs to the edge of the chart (open-ended, dashed); a
 * task with `milestone: true`, a zero-length span or only an end is a
 * diamond.
 *
 * Options:
 *   variant            "gantt" | "roadmap"  overrides the type's drawing
 *   today              "false" hides the today marker (shown when today is
 *                      in range)
 *   start-date         fixes the start of the time axis (a date as above)
 *   end-date           fixes the end of the time axis (inclusive)
 *   density            "compact" draws shorter rows / thinner bars
 *   gantt only:
 *   scale              "day" | "week" | "month" | "quarter": tick unit (the
 *                      step still grows when there is no room)
 *   show-progress      "false" hides the progress fills
 *   show-dependencies  "false" hides the dependency arrows
 *   row-height         minimum row height in px (default 32, compact 24)
 *   collapsed-groups   JSON array (or comma list) of collapsed group ids;
 *                      activating a group header updates it
 *   roadmap only:
 *   mode               "calendar" (default) places bars by date; "bucket"
 *                      places them in the `buckets` columns by `bucket`
 *   scale              "quarter" (default) | "month" | "half-year" columns
 *
 * The chart asks for the height its rows need (ctx.setContentHeight), so a
 * chart without a fixed height grows with its rows.
 *
 * Events:
 *   mj-chart-bar-click     { id, label, start, end, index }
 *   mj-chart-marker-click  { label, date, index }
 *   mj-chart-group-toggle  { group, collapsed, collapsedGroups }
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatDate, parseDate } from "../svgdraw.js";
import { timeScale, timeTicks, timeTickFormat, seriesColor } from "../scales.js";
import { booleanOption } from "../chartoptions.js";


/* Status -> semantic colour of a bar (a status, not a data series). */
const STATUS_COLORS = {
  "planned":     "var(--mj-text-muted, #6b7280)",
  "in-progress": "var(--mj-accent, #2563eb)",
  "active":      "var(--mj-accent, #2563eb)",
  "completed":   "var(--mj-color-success, #15803d)",
  "done":        "var(--mj-color-success, #15803d)",
  "at-risk":     "var(--mj-color-warning, #b45309)",
  "blocked":     "var(--mj-color-danger, #b91c1c)"
};

const STATUS_LABELS = {
  "planned":     "Planned",
  "in-progress": "In progress",
  "active":      "Active",
  "completed":   "Completed",
  "done":        "Done",
  "at-risk":     "At risk",
  "blocked":     "Blocked"
};

/* A glyph per status, so the status is not told by colour alone. */
const STATUS_ICONS = {
  "planned":     "○",
  "in-progress": "◎",
  "active":      "◎",
  "completed":   "✓",
  "done":        "✓",
  "at-risk":     "⚠",
  "blocked":     "⊘"
};

const MARKER_COLOR = "var(--mj-color-warning, #b45309)";
const TODAY_COLOR = "var(--mj-accent, #2563eb)";

const QUARTER_PATTERN = /^(\d{4})-Q([1-4])$/i;
const MONTH_PATTERN = /^(\d{4})-(\d{2})$/;
const DAY_PATTERN = /^(\d{4})-(\d{2})-(\d{2})$/;

const LABEL_FONT = 11;
const CHAR_WIDTH = 0.56;
const DAY_MS = 86400000;

/* Gantt geometry. */
const GANTT_MARGIN = { top: 32, right: 16, bottom: 14 };
const ROW_HEIGHT = 32;
const ROW_HEIGHT_COMPACT = 24;
const MAX_ROW_STRETCH = 1.5;
const EDGE_ARROW = 10;

/* Roadmap geometry. */
const ROADMAP_HEADER = 36;
const ROADMAP_BAR = 32;
const ROADMAP_BAR_COMPACT = 24;
const ROADMAP_BAR_GAP = 6;
const ROADMAP_LANE_PAD = 8;
const ROADMAP_FOOTER_ROW = 16;
const ROADMAP_MIN_BAR = 28;
const ROADMAP_MAX_COLUMNS = 240;
const UNASSIGNED_LANE = "\u0000unassigned";


export function estimateTextWidth(text, fontSize) {
  /*
   * Approximate rendered width of a label in the chart's sans-serif font.
   *
   * :param text: The label text.
   * :param fontSize: The font size in pixels.
   * :returns: The estimated width in pixels.
   */
  const width = String(text).length * fontSize * CHAR_WIDTH
  return width
}


export function fitText(text, maxWidth, fontSize) {
  /*
   * Shorten a label with an ellipsis so it fits a width.
   *
   * :param text: The label text.
   * :param maxWidth: The width available in pixels.
   * :param fontSize: The font size in pixels.
   * :returns: The text, a shortened copy ending in an ellipsis, or "" when
   *     not even two characters fit.
   */
  const value = String(text)
  let fitted = value
  if (estimateTextWidth(value, fontSize) > maxWidth) {
    const maxChars = Math.floor(maxWidth / (fontSize * CHAR_WIDTH)) - 1
    fitted = maxChars >= 2 ? value.slice(0, maxChars) + "…" : ""
  }
  return fitted
}


export function parseScheduleDate(value, edge) {
  /*
   * Read a schedule date.
   *
   * :param value: A Date, epoch ms, "YYYY-MM-DD", "YYYY-MM", "YYYY-Qn" or
   *     an ISO date-time string.
   * :param edge: "start" or "end". A calendar day, month or quarter given
   *     as an END is inclusive, so the instant returned is the start of the
   *     NEXT day / month / quarter.
   * :returns: { date, dayOnly } where `date` is a Date (or null when the
   *     value is missing or not a date) and `dayOnly` is true for calendar
   *     forms (so the inclusive end can be shown as the day it names).
   */
  const isEnd = edge === "end"
  let date = null
  let dayOnly = false

  if (value !== null && value !== undefined && value !== "") {
    const text = typeof value === "string" ? value.trim() : null
    const quarter = text !== null ? QUARTER_PATTERN.exec(text) : null
    const month = text !== null ? MONTH_PATTERN.exec(text) : null
    const day = text !== null ? DAY_PATTERN.exec(text) : null

    if (quarter !== null) {
      const year = Number(quarter[1])
      const firstMonth = (Number(quarter[2]) - 1) * 3
      date = new Date(year, isEnd === true ? firstMonth + 3 : firstMonth, 1)
      dayOnly = true
    } else if (month !== null) {
      const year = Number(month[1])
      const monthIndex = Number(month[2]) - 1
      if (monthIndex >= 0 && monthIndex <= 11) {
        date = new Date(year, isEnd === true ? monthIndex + 1 : monthIndex, 1)
        dayOnly = true
      }
    } else if (day !== null) {
      const parsed = parseDate(text)
      if (parsed !== null) {
        date = isEnd === true
          ? new Date(parsed.getFullYear(), parsed.getMonth(), parsed.getDate() + 1)
          : parsed
        dayOnly = true
      }
    } else if (typeof value === "string" || typeof value === "number" || value instanceof Date) {
      date = parseDate(value)
    }
  }

  if (date !== null && Number.isNaN(date.getTime()) === true) {
    date = null
  }
  const result = { date: date, dayOnly: dayOnly }
  return result
}


export function lastIncludedDay(endInfo) {
  /*
   * The date to show for an end bound: the last included day of a calendar
   * end (the instant is the start of the next day), else the instant.
   */
  let shown = endInfo.date
  if (shown !== null && endInfo.dayOnly === true) {
    shown = new Date(shown.getFullYear(), shown.getMonth(), shown.getDate() - 1)
  }
  return shown
}


/* ---------- data ---------- */

function _text(value) {
  /*
   * A data field as display text ("" for null / undefined).
   */
  const text = value !== null && value !== undefined ? String(value) : ""
  return text
}


function _taskKey(task, index) {
  /*
   * The id a task is referenced by in `depends`.
   */
  const key = task.id !== undefined && task.id !== null ? String(task.id) : String(index)
  return key
}


function _taskLabel(task, index) {
  /*
   * The name shown for a task: its label, else its id.
   */
  const label = task.label !== undefined && task.label !== null && String(task.label) !== ""
    ? String(task.label) : _taskKey(task, index)
  return label
}


function _taskStatus(task) {
  /*
   * The status key of a task ("" without one), lower-cased for the colour
   * and icon lookups.
   */
  const status = task.status !== undefined && task.status !== null ? String(task.status) : ""
  return status
}


function _statusText(status) {
  /*
   * The display text of a status: the known label, else the value as given.
   */
  const known = Object.prototype.hasOwnProperty.call(STATUS_LABELS, status) === true
  const text = known === true ? STATUS_LABELS[status] : status
  return text
}


function _taskTiming(task) {
  /*
   * Parse a task's start and end into the instants drawn.
   *
   * :returns: { start, end, shownEnd, kind } where kind is "bar", "open"
   *     (a start and no end: runs to the edge of the chart), "point"
   *     (`milestone: true`, a zero-length span or an end only) or "none"
   *     (no usable date). `end` is null for an open task.
   */
  const startInfo = parseScheduleDate(task.start, "start")
  const endInfo = parseScheduleDate(task.end, "end")
  const flagged = task.milestone === true || task.type === "milestone"
  let start = startInfo.date
  let end = endInfo.date
  let shownEnd = lastIncludedDay(endInfo)
  let kind = "none"

  if (start !== null && end !== null) {
    kind = end.getTime() > start.getTime() ? "bar" : "point"
    if (kind === "point") {
      end = start
      shownEnd = start
    }
  } else if (start !== null && flagged === true) {
    kind = "point"
    end = start
    shownEnd = start
  } else if (start !== null) {
    kind = "open"
    end = null
    shownEnd = null
  } else if (end !== null) {
    kind = "point"
    start = shownEnd
    end = shownEnd
  }
  const timing = { start: start, end: end, shownEnd: shownEnd, kind: kind }
  return timing
}


function _readGroups(raw, tasks) {
  /*
   * The groups in drawing order. With declared `groups`: those, in their
   * order (empty ones included), and a task naming any other group is
   * ungrouped. Without: the groups the tasks name, in order of first
   * appearance.
   *
   * :returns: { keys: [string], labels: Map(key -> label), declared: bool,
   *     keyOf(task) -> string | null }. A task names its group by id or by
   *     label; keyOf is null for an ungrouped task.
   */
  const keys = []
  const labels = new Map()
  const aliases = new Map()
  const declaredList = Array.isArray(raw.groups) === true ? raw.groups : []

  for (let index = 0; index < declaredList.length; index = index + 1) {
    const group = declaredList[index]
    if (group === null || typeof group !== "object") {
      continue
    }
    const hasId = group.id !== undefined && group.id !== null && String(group.id) !== ""
    const label = group.label !== undefined && group.label !== null ? String(group.label) : ""
    const key = hasId === true ? String(group.id) : label
    if (key === "" || labels.has(key) === true) {
      continue
    }
    keys.push(key)
    labels.set(key, label !== "" ? label : key)
    if (label !== "" && aliases.has(label) === false) {
      aliases.set(label, key)
    }
  }
  const declared = keys.length > 0

  const keyOf = (task) => {
    const named = task.group !== undefined && task.group !== null && task.group !== ""
      ? String(task.group) : null
    let key = named
    if (named !== null && labels.has(named) === false && aliases.has(named) === true) {
      key = aliases.get(named)
    }
    if (key !== null && declared === true && labels.has(key) === false) {
      key = null
    }
    return key
  }

  for (let index = 0; index < tasks.length && declared === false; index = index + 1) {
    const task = tasks[index]
    if (task === null || typeof task !== "object") {
      continue
    }
    const key = keyOf(task)
    if (key !== null && labels.has(key) === false) {
      keys.push(key)
      labels.set(key, key)
    }
  }

  const info = { keys: keys, labels: labels, declared: declared, keyOf: keyOf }
  return info
}


function _parseCollapsed(value) {
  /*
   * The collapsed group ids of the `collapsed-groups` option: a JSON array
   * or a comma-separated list.
   */
  const collapsed = new Set()
  if (value === null || value === undefined || String(value).trim() === "") {
    return collapsed
  }
  const text = String(value).trim()
  let entries = null
  if (text.startsWith("[") === true) {
    try {
      const parsed = JSON.parse(text)
      entries = Array.isArray(parsed) === true ? parsed : null
    } catch (error) {
      entries = null
    }
  }
  if (entries === null) {
    entries = text.split(",")
  }
  for (let index = 0; index < entries.length; index = index + 1) {
    const entry = _text(entries[index]).trim()
    if (entry !== "") {
      collapsed.add(entry)
    }
  }
  return collapsed
}


function _readMarkers(raw) {
  /*
   * The markers with a usable date: [{ label, date, index, source }].
   */
  const list = Array.isArray(raw.markers) === true ? raw.markers : []
  const markers = []
  for (let index = 0; index < list.length; index = index + 1) {
    const marker = list[index]
    if (marker === null || typeof marker !== "object") {
      continue
    }
    const info = parseScheduleDate(marker.date, "start")
    if (info.date === null) {
      continue
    }
    markers.push({ label: _text(marker.label), date: info.date, index: index, source: marker })
  }
  return markers
}


function _readPhases(raw) {
  /*
   * The phases with a usable range: [{ label, start, end, index }]; the end
   * is inclusive like a task's.
   */
  const list = Array.isArray(raw.phases) === true ? raw.phases : []
  const phases = []
  for (let index = 0; index < list.length; index = index + 1) {
    const phase = list[index]
    if (phase === null || typeof phase !== "object") {
      continue
    }
    const start = parseScheduleDate(phase.start, "start").date
    const end = parseScheduleDate(phase.end, "end").date
    if (start === null || end === null || end.getTime() <= start.getTime()) {
      continue
    }
    phases.push({ label: _text(phase.label), start: start, end: end, index: index })
  }
  return phases
}


function _numberOption(ctx, name, fallback, low, high) {
  /*
   * A numeric option attribute, clamped to [low, high]; the fallback when
   * the attribute is absent or not a number.
   */
  const value = Number.parseFloat(ctx.attrs(name, ""))
  let result = fallback
  if (Number.isFinite(value) === true) {
    result = Math.min(Math.max(value, low), high)
  }
  return result
}


function _timeDomain(ctx, timings, padFraction) {
  /*
   * The time domain of the dated tasks, fixed by the start-date / end-date
   * options where they are given.
   *
   * :param timings: Iterable of task timings.
   * :param padFraction: Padding added on each data-derived side.
   * :returns: { min, max } as Dates, or null when nothing is dated and no
   *     window is given.
   */
  let dateMin = null
  let dateMax = null
  for (const timing of timings) {
    if (timing.kind === "none") {
      continue
    }
    const last = timing.end !== null ? timing.end : timing.start
    if (dateMin === null || timing.start.getTime() < dateMin.getTime()) {
      dateMin = timing.start
    }
    if (dateMax === null || last.getTime() > dateMax.getTime()) {
      dateMax = last
    }
  }

  const fixedStart = parseScheduleDate(ctx.attrs("start-date", null), "start").date
  const fixedEnd = parseScheduleDate(ctx.attrs("end-date", null), "end").date
  if (dateMin === null && fixedStart === null && fixedEnd === null) {
    return null
  }
  if (dateMin === null) {
    dateMin = fixedStart !== null ? fixedStart : new Date(fixedEnd.getTime() - 30 * DAY_MS)
    dateMax = fixedEnd !== null ? fixedEnd : new Date(fixedStart.getTime() + 30 * DAY_MS)
  }

  if (dateMax.getTime() - dateMin.getTime() < DAY_MS) {
    dateMin = new Date(dateMin.getTime() - DAY_MS)
    dateMax = new Date(dateMax.getTime() + DAY_MS)
  }
  const padMs = (dateMax.getTime() - dateMin.getTime()) * padFraction
  let min = fixedStart !== null ? fixedStart : new Date(dateMin.getTime() - padMs)
  let max = fixedEnd !== null ? fixedEnd : new Date(dateMax.getTime() + padMs)
  if (max.getTime() <= min.getTime()) {
    /* A window that ends before it starts: read it the other way round. */
    const swapped = min
    min = new Date(max.getTime() - DAY_MS)
    max = new Date(swapped.getTime() + DAY_MS)
  }
  const domain = { min: min, max: max }
  return domain
}


function _unitTicks(dateMin, dateMax, unit, plotW) {
  /*
   * Ticks on day / week / month / quarter boundaries for the `scale`
   * option. The step grows (1, 2, 5, ... units) until the labels have room.
   *
   * :returns: { ticks: [Date], format: (Date) -> string }.
   */
  const monthsPer = unit === "quarter" ? 3 : (unit === "month" ? 1 : 0)
  const daysPer = unit === "week" ? 7 : 1
  const steps = [1, 2, 3, 4, 6, 12, 24, 52, 104]
  const minSpacing = 64
  let ticks = []

  for (let s = 0; s < steps.length; s = s + 1) {
    const step = steps[s]
    const candidate = []
    let cursor = null
    if (monthsPer > 0) {
      const months = monthsPer * step
      let monthIndex = dateMin.getFullYear() * 12 + dateMin.getMonth()
      monthIndex = monthIndex - (((monthIndex % months) + months) % months)
      cursor = new Date(Math.floor(monthIndex / 12), monthIndex % 12, 1)
      while (cursor.getTime() <= dateMax.getTime() && candidate.length < 1000) {
        if (cursor.getTime() >= dateMin.getTime()) {
          candidate.push(cursor)
        }
        monthIndex = monthIndex + months
        cursor = new Date(Math.floor(monthIndex / 12), monthIndex % 12, 1)
      }
    } else {
      cursor = new Date(dateMin.getFullYear(), dateMin.getMonth(), dateMin.getDate())
      if (unit === "week") {
        /* Weeks start on Monday. */
        const shift = (cursor.getDay() + 6) % 7
        cursor = new Date(cursor.getFullYear(), cursor.getMonth(), cursor.getDate() - shift)
      }
      while (cursor.getTime() <= dateMax.getTime() && candidate.length < 1000) {
        if (cursor.getTime() >= dateMin.getTime()) {
          candidate.push(cursor)
        }
        cursor = new Date(cursor.getFullYear(), cursor.getMonth(), cursor.getDate() + daysPer * step)
      }
    }
    ticks = candidate
    if (candidate.length <= 1 || plotW / candidate.length >= minSpacing) {
      break
    }
  }

  let options = { month: "short", day: "numeric" }
  if (unit === "month") {
    options = { month: "short", year: "numeric" }
  }
  const format = (date) => {
    let text = formatDate(date, options)
    if (unit === "quarter") {
      text = `Q${Math.floor(date.getMonth() / 3) + 1} ${date.getFullYear()}`
    }
    return text
  }
  const result = { ticks: ticks, format: format }
  return result
}


function _onActivate(element, handler) {
  /*
   * Run `handler(event)` on click and on Enter / Space.
   */
  element.addEventListener("click", (event) => {
    handler(event)
  })
  element.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault()
      handler(event)
    }
  })
  return
}


function _diamondPoints(x, y, size) {
  /*
   * SVG polygon points of a diamond centred on (x, y).
   */
  const points = `${x},${y - size} ${x + size},${y} ${x},${y + size} ${x - size},${y}`
  return points
}


/* ---------- overlays shared by both drawings ---------- */

function _drawPhaseBands(layer, phases, scale, plotW, top, height) {
  /*
   * Phase bands behind the bars, coloured by position.
   *
   * :returns: The bands drawn: [{ x1, x2, label, index }].
   */
  const drawn = []
  for (let p = 0; p < phases.length; p = p + 1) {
    const phase = phases[p]
    const x1 = Math.max(scale(phase.start), 0)
    const x2 = Math.min(scale(phase.end), plotW)
    if (x2 <= x1) {
      continue
    }
    const band = svgEl("rect", {
      x: x1, y: top, width: x2 - x1, height: Math.max(height, 0),
      fill: seriesColor(phase.index), "fill-opacity": 0.1, part: "phase-band"
    }, [])
    if (phase.label !== "") {
      band.appendChild(svgEl("title", null, phase.label))
    }
    layer.appendChild(band)
    drawn.push({ x1: x1, x2: x2, label: phase.label, index: phase.index })
  }
  return drawn
}


function _drawMarkers(layer, markers, scale, plotW, top, bottom, ctx) {
  /*
   * Milestone markers: a dashed line over the plot with a diamond on the
   * axis and the name beside it. Each marker is a focusable mark that
   * emits mj-chart-marker-click.
   */
  for (let m = 0; m < markers.length; m = m + 1) {
    const marker = markers[m]
    const x = scale(marker.date)
    if (x < -0.5 || x > plotW + 0.5) {
      continue
    }
    const dateText = formatDate(marker.date)
    const name = marker.label !== "" ? marker.label : dateText
    const ariaLabel = `Milestone ${name}, ${dateText}`
    const group = svgEl("g", {
      part: "milestone-marker", tabindex: "0", role: "img", "aria-label": ariaLabel,
      "data-mark": `marker:${marker.index}`
    }, [svgEl("title", null, ariaLabel)])
    group.appendChild(svgEl("line", {
      x1: x, y1: top, x2: x, y2: bottom,
      stroke: MARKER_COLOR, "stroke-width": 1.5, "stroke-dasharray": "5 3"
    }, []))
    group.appendChild(svgEl("polygon", {
      points: _diamondPoints(x, top, 6),
      fill: MARKER_COLOR, stroke: "var(--mj-surface, #ffffff)", "stroke-width": 1
    }, []))
    const text = fitText(marker.label, 160, 10)
    if (text !== "") {
      const flip = x + 10 + estimateTextWidth(text, 10) > plotW
      group.appendChild(svgEl("text", {
        x: flip === true ? x - 9 : x + 9, y: top + 14,
        "text-anchor": flip === true ? "end" : "start",
        "font-size": 10, fill: "var(--mj-text, #14181f)",
        stroke: "var(--mj-surface, #ffffff)", "stroke-width": 3, "paint-order": "stroke",
        "aria-hidden": "true"
      }, text))
    }
    layer.appendChild(group)

    const emitMarker = marker
    _onActivate(group, () => {
      ctx.emit("mj-chart-marker-click", {
        label: emitMarker.source.label,
        date: emitMarker.source.date,
        index: emitMarker.index
      })
    })
  }
  return
}


function _todayInRange(ctx, scale, plotW) {
  /*
   * The x of today when the today option is on and today is in the domain,
   * else null.
   */
  let x = null
  if (booleanOption(ctx, "today", true) === true) {
    const candidate = scale(new Date())
    if (candidate >= 0 && candidate <= plotW) {
      x = candidate
    }
  }
  return x
}


/* ---------- gantt ---------- */

function _buildGanttRows(tasks, groups, collapsed) {
  /*
   * Order the tasks into rows: tasks without a group first, then each group
   * under a header row of its own (its tasks left out while collapsed).
   *
   * :returns: [{ kind: "header", group, label, count, collapsed, number }
   *     | { kind: "task", task, index, grouped }]
   */
  const byGroup = new Map()
  const rows = []
  for (let g = 0; g < groups.keys.length; g = g + 1) {
    byGroup.set(groups.keys[g], [])
  }
  for (let index = 0; index < tasks.length; index = index + 1) {
    const task = tasks[index]
    if (task === null || typeof task !== "object") {
      continue
    }
    const key = groups.keyOf(task)
    if (key === null) {
      rows.push({ kind: "task", task: task, index: index, grouped: false })
    } else {
      byGroup.get(key).push({ kind: "task", task: task, index: index, grouped: true })
    }
  }

  for (let g = 0; g < groups.keys.length; g = g + 1) {
    const key = groups.keys[g]
    const members = byGroup.get(key)
    const isCollapsed = collapsed.has(key)
    rows.push({
      kind: "header", group: key, label: groups.labels.get(key), count: members.length,
      collapsed: isCollapsed, number: g
    })
    if (isCollapsed === false) {
      for (let m = 0; m < members.length; m = m + 1) {
        rows.push(members[m])
      }
    }
  }
  return rows
}


function _dependencyPath(fromPos, toPos, rowStep) {
  /*
   * Route a finish-to-start dependency from the end of the predecessor into
   * the left end of the successor. The line leaves the predecessor through
   * its lower (or upper) edge just before its end, so the space to the right
   * of the bar stays free, and always enters the successor from the left so
   * the arrowhead points at it. When the successor starts before the
   * predecessor has ended (overlap, zero lag) the line runs back through
   * the gap between the rows first.
   */
  const direction = toPos.midY >= fromPos.midY ? 1 : -1
  const exitX = Math.max(fromPos.rightX - 6, fromPos.leftX + 2)
  const exitY = fromPos.midY + direction * fromPos.halfH
  const endX = toPos.leftX - 2
  const endY = toPos.midY
  let pathD = ""

  if (endX >= exitX + 8) {
    pathD = `M${exitX.toFixed(1)},${exitY.toFixed(1)} V${endY.toFixed(1)} H${endX.toFixed(1)}`
  } else {
    const gapY = fromPos.midY + direction * rowStep / 2
    const inX = endX - 10
    pathD = `M${exitX.toFixed(1)},${exitY.toFixed(1)} V${gapY.toFixed(1)} ` +
      `H${inX.toFixed(1)} V${endY.toFixed(1)} H${endX.toFixed(1)}`
  }
  return pathD
}


function _progressOf(task) {
  /*
   * The progress of a task in 0..1, or null without a numeric progress.
   */
  const progress = typeof task.progress === "number" && Number.isFinite(task.progress) === true
    ? Math.min(Math.max(task.progress, 0), 1) : null
  return progress
}


function _ganttTable(orderedRows, timings, groups) {
  /*
   * The accessible table: one row per task (collapsed ones included), in
   * row order.
   */
  const tableRows = []
  for (let r = 0; r < orderedRows.length; r = r + 1) {
    const row = orderedRows[r]
    if (row.kind !== "task") {
      continue
    }
    const task = row.task
    const timing = timings.get(row.index)
    const progress = _progressOf(task)
    const groupKey = groups.keyOf(task)
    let endText = timing.shownEnd !== null ? formatDate(timing.shownEnd) : ""
    if (timing.kind === "open") {
      endText = "Open-ended"
    }
    tableRows.push([
      _taskLabel(task, row.index),
      groupKey !== null ? groups.labels.get(groupKey) : "",
      timing.start !== null ? formatDate(timing.start) : "",
      endText,
      progress !== null ? `${Math.round(progress * 100)}%` : "",
      _statusText(_taskStatus(task)),
      _text(task.assignee),
      Array.isArray(task.depends) === true ? task.depends.map((dep) => String(dep)).join(", ") : ""
    ])
  }
  const table = {
    columns: ["Task", "Group", "Start", "End", "Progress", "Status", "Assignee", "Depends on"],
    rows: tableRows
  }
  return table
}


function _toggleGroup(event, groupKey, collapsed, ctx) {
  /*
   * Collapse or expand a group: the new set goes into the host's
   * `collapsed-groups` attribute (which re-renders the chart) and
   * mj-chart-group-toggle reports it.
   */
  const next = new Set(collapsed)
  const collapse = next.has(groupKey) === false
  if (collapse === true) {
    next.add(groupKey)
  } else {
    next.delete(groupKey)
  }
  const list = Array.from(next)

  const root = event.currentTarget.getRootNode()
  const host = root !== null && root.host !== undefined ? root.host : null
  if (host !== null) {
    if (list.length > 0) {
      host.setAttribute("collapsed-groups", JSON.stringify(list))
    } else {
      host.removeAttribute("collapsed-groups")
    }
  }
  ctx.emit("mj-chart-group-toggle", { group: groupKey, collapsed: collapse, collapsedGroups: list })
  return
}


function _renderGantt(ctx, raw, root) {
  /*
   * Draw the gantt: one row per task, header rows per group.
   */
  const tasks = Array.isArray(raw.tasks) === true ? raw.tasks : []
  const groups = _readGroups(raw, tasks)
  const collapsed = _parseCollapsed(ctx.attrs("collapsed-groups", null))
  const compact = ctx.attrs("density", "normal") === "compact"
  const rowMin = _numberOption(ctx, "row-height", compact === true ? ROW_HEIGHT_COMPACT : ROW_HEIGHT, 12, 200)
  const showProgress = booleanOption(ctx, "show-progress", true)
  const showDependencies = booleanOption(ctx, "show-dependencies", true)

  const allRows = _buildGanttRows(tasks, groups, new Set())
  const rows = _buildGanttRows(tasks, groups, collapsed)

  /* Dates of every task (collapsed ones too, so collapsing never rescales). */
  const timings = new Map()
  for (let r = 0; r < allRows.length; r = r + 1) {
    if (allRows[r].kind === "task") {
      timings.set(allRows[r].index, _taskTiming(allRows[r].task))
    }
  }
  ctx.setTable(_ganttTable(allRows, timings, groups))
  if (rows.length === 0) {
    return
  }

  const margin = {
    top: GANTT_MARGIN.top, right: GANTT_MARGIN.right, bottom: GANTT_MARGIN.bottom, left: 64
  }
  ctx.setContentHeight(margin.top + rows.length * rowMin + margin.bottom)

  /* Label gutter sized from the longest label (at most 40% of the width). */
  let longest = 0
  for (let r = 0; r < rows.length; r = r + 1) {
    const row = rows[r]
    const text = row.kind === "header" ? `▾ ${row.label}` : _taskLabel(row.task, row.index)
    longest = Math.max(longest, estimateTextWidth(text, LABEL_FONT) + (row.grouped === true ? 12 : 0))
  }
  margin.left = Math.min(Math.max(longest + 20, 64), Math.max(ctx.width * 0.4, 64))

  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)
  const rowStep = Math.max(Math.min(plotH / rows.length, rowMin * MAX_ROW_STRETCH), 4)
  const gridH = rowStep * rows.length
  const barInset = Math.max(rowStep * 0.2, 2)
  const barH = Math.max(rowStep - barInset * 2, 2)
  const labelFont = Math.max(Math.min(LABEL_FONT, rowStep * 0.6), 6)
  const rowTop = (r) => r * rowStep
  const rowMid = (r) => r * rowStep + rowStep / 2

  const plot = svgEl("g", { transform: `translate(${margin.left},${margin.top})` }, [])
  root.appendChild(plot)
  const backdrop = svgEl("g", { "aria-hidden": "true" }, [])
  const axis = svgEl("g", { "aria-hidden": "true" }, [])
  const arrows = svgEl("g", { "aria-hidden": "true" }, [])
  const marks = svgEl("g", null, [])
  const labels = svgEl("g", { "aria-hidden": "true" }, [])
  const overlays = svgEl("g", null, [])
  plot.appendChild(backdrop)
  plot.appendChild(axis)
  plot.appendChild(arrows)
  plot.appendChild(marks)
  plot.appendChild(labels)
  plot.appendChild(overlays)

  /* Row stripes and task labels; group headers are marks of their own. */
  let taskRowNumber = 0
  for (let r = 0; r < rows.length; r = r + 1) {
    const row = rows[r]
    if (row.kind === "header") {
      continue
    }
    if (taskRowNumber % 2 === 0) {
      backdrop.appendChild(svgEl("rect", {
        x: 0, y: rowTop(r), width: plotW, height: rowStep, fill: "var(--mj-bg-subtle, #f8f9fb)"
      }, []))
    }
    taskRowNumber = taskRowNumber + 1
    const indent = row.grouped === true ? 12 : 0
    labels.appendChild(svgEl("text", {
      x: -margin.left + 8 + indent, y: rowMid(r) + labelFont * 0.35,
      "font-size": labelFont, fill: "var(--mj-text, #14181f)", part: "task-label task-list-panel"
    }, fitText(_taskLabel(row.task, row.index), margin.left - 14 - indent, labelFont)))
  }

  const domain = _timeDomain(ctx, timings.values(), 0.02)
  const scale = domain !== null ? timeScale([domain.min, domain.max], [0, plotW]) : null

  if (scale !== null) {
    _drawPhaseBands(backdrop, _readPhases(raw), scale, plotW, 0, gridH)

    /* Time axis along the top: gridlines on calendar boundaries. */
    const unit = ctx.attrs("scale", null)
    let ticks = []
    let tickFormat = null
    if (unit === "day" || unit === "week" || unit === "month" || unit === "quarter") {
      const unitTicks = _unitTicks(domain.min, domain.max, unit, plotW)
      ticks = unitTicks.ticks
      tickFormat = unitTicks.format
    } else {
      let tickCount = Math.max(2, Math.floor(plotW / 80))
      ticks = timeTicks(domain.min, domain.max, tickCount)
      if (ticks.length < 2) {
        /* A coarse calendar interval can miss a short domain: ask finer. */
        tickCount = tickCount * 2
        ticks = timeTicks(domain.min, domain.max, tickCount)
      }
      tickFormat = timeTickFormat(domain.min, domain.max, tickCount)
    }
    for (let t = 0; t < ticks.length; t = t + 1) {
      const x = scale(ticks[t])
      axis.appendChild(svgEl("line", {
        x1: x, y1: -4, x2: x, y2: gridH, stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
      }, []))
      const anchor = x < 24 ? "start" : (x > plotW - 24 ? "end" : "middle")
      axis.appendChild(svgEl("text", {
        x: x, y: -10, "text-anchor": anchor, "font-size": 10,
        fill: "var(--mj-text-muted, #6b7280)", part: "time-axis"
      }, tickFormat(ticks[t])))
    }
  }
  axis.appendChild(svgEl("line", {
    x1: 0, y1: 0, x2: plotW, y2: 0, stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
  }, []))

  /* Group headers and bars, in row order (the tab order follows the rows). */
  const barPositions = new Map()
  const rx = Math.min(3, barH / 2)
  for (let r = 0; r < rows.length; r = r + 1) {
    const row = rows[r]
    const mid = rowMid(r)

    if (row.kind === "header") {
      const state = row.collapsed === true ? "collapsed" : "expanded"
      const ariaLabel = `${row.label}, group of ${row.count} task${row.count === 1 ? "" : "s"}, ${state}`
      const header = svgEl("g", {
        part: "group-row", tabindex: "0", role: "button",
        "aria-expanded": row.collapsed === true ? "false" : "true",
        "aria-label": ariaLabel, "data-mark": `group:${row.number}`
      }, [svgEl("title", null, row.label)])
      header.appendChild(svgEl("rect", {
        x: -margin.left, y: rowTop(r), width: plotW + margin.left, height: rowStep,
        fill: "var(--mj-bg-muted, #eef0f3)"
      }, []))
      header.appendChild(svgEl("text", {
        x: -margin.left + 6, y: mid + labelFont * 0.35, "font-size": labelFont, "font-weight": "bold",
        fill: "var(--mj-text, #14181f)", "aria-hidden": "true"
      }, `${row.collapsed === true ? "▸" : "▾"} ${fitText(row.label, plotW + margin.left - 24, labelFont)}`))
      const groupKey = row.group
      _onActivate(header, (event) => {
        _toggleGroup(event, groupKey, collapsed, ctx)
      })
      marks.appendChild(header)
      continue
    }

    const task = row.task
    const key = _taskKey(task, row.index)
    const label = _taskLabel(task, row.index)
    const timing = timings.get(row.index)
    const barY = rowTop(r) + barInset
    const status = _taskStatus(task)
    const progress = _progressOf(task)
    const groupKey = groups.keyOf(task)
    const barColor = groups.keys.length > 0 && groupKey !== null ? ctx.colorFor(groupKey) : ctx.colorFor(0)

    let ariaLabel = `${label}: no dates`
    if (timing.kind !== "none") {
      ariaLabel = `${label}: ${formatDate(timing.start)}`
      if (timing.kind === "bar") {
        ariaLabel = ariaLabel + ` to ${formatDate(timing.shownEnd)}`
      } else if (timing.kind === "open") {
        ariaLabel = ariaLabel + " (no end date)"
      }
    }
    if (progress !== null) {
      ariaLabel = ariaLabel + `, ${Math.round(progress * 100)}% complete`
    }
    if (status !== "") {
      ariaLabel = ariaLabel + `, ${_statusText(status)}`
    }
    if (_text(task.assignee) !== "") {
      ariaLabel = ariaLabel + `, ${_text(task.assignee)}`
    }

    /* One interactive group holds the bar and its progress fill. */
    const taskGroup = svgEl("g", {
      part: "bar task-bar", tabindex: "0", role: "img", "aria-label": ariaLabel,
      "data-mark": `task:${row.index}`
    }, [svgEl("title", null, ariaLabel)])

    let leftEdge = 0
    let rightEdge = 0
    if (scale === null || timing.kind === "none") {
      /* No usable dates: the row stays selectable and says why. */
      taskGroup.appendChild(svgEl("rect", {
        x: 4, y: barY, width: 72, height: barH, rx: rx, fill: "none",
        stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-dasharray": "3 3"
      }, []))
      taskGroup.appendChild(svgEl("text", {
        x: 10, y: mid + 3.5, "font-size": 10, "font-style": "italic",
        fill: "var(--mj-text-muted, #6b7280)", "aria-hidden": "true"
      }, "No dates"))
      leftEdge = 4
      rightEdge = 76
    } else {
      const rawX1 = scale(timing.start)
      const rawX2 = timing.kind === "open" ? plotW : scale(timing.end)
      if (rawX2 < 0 || rawX1 > plotW) {
        /* Entirely outside the window: an arrow at the edge it lies beyond. */
        const before = rawX2 < 0
        const tipX = before === true ? 2 : plotW - 2
        const baseX = before === true ? 2 + EDGE_ARROW : plotW - 2 - EDGE_ARROW
        taskGroup.appendChild(svgEl("polygon", {
          points: `${tipX},${mid} ${baseX},${mid - 6} ${baseX},${mid + 6}`,
          fill: "var(--mj-text-muted, #6b7280)"
        }, []))
        leftEdge = Math.min(tipX, baseX)
        rightEdge = Math.max(tipX, baseX)
      } else if (timing.kind === "point") {
        const size = Math.max(Math.min(barH / 2 + 1, 8), 3)
        const x = Math.min(Math.max(rawX1, size), plotW - size)
        taskGroup.appendChild(svgEl("polygon", {
          points: _diamondPoints(x, mid, size),
          fill: barColor, stroke: "var(--mj-surface, #ffffff)", "stroke-width": 1
        }, []))
        leftEdge = x - size
        rightEdge = x + size
      } else {
        const x1 = Math.max(rawX1, 0)
        const x2 = Math.min(Math.max(rawX2, rawX1 + 2), plotW)
        const barW = Math.max(x2 - x1, 2)
        const open = timing.kind === "open"
        const filled = showProgress === true && progress !== null
        taskGroup.appendChild(svgEl("rect", {
          x: x1, y: barY, width: barW, height: barH, rx: rx,
          fill: barColor, "fill-opacity": filled === true || open === true ? 0.4 : 0.9,
          stroke: barColor, "stroke-width": 1, "stroke-dasharray": open === true ? "5 3" : null
        }, []))
        if (filled === true && progress > 0) {
          const fullWidth = Math.max(rawX2 - rawX1, 2)
          const fillRight = Math.min(x2, rawX1 + fullWidth * progress)
          if (fillRight > x1) {
            taskGroup.appendChild(svgEl("rect", {
              x: x1, y: barY, width: fillRight - x1, height: barH, rx: rx,
              fill: barColor, "pointer-events": "none", part: "bar-fill task-bar-fill"
            }, []))
          }
        }
        leftEdge = x1
        rightEdge = x1 + barW
      }
    }

    const emitTask = task
    const emitIndex = row.index
    _onActivate(taskGroup, () => {
      ctx.emit("mj-chart-bar-click", {
        id: emitTask.id, label: emitTask.label, start: emitTask.start, end: emitTask.end,
        index: emitIndex
      })
    })
    marks.appendChild(taskGroup)

    /* Assignee beside the bar when there is room. */
    if (_text(task.assignee) !== "" && labelFont >= 8 && timing.kind !== "open") {
      const assignee = _text(task.assignee)
      if (rightEdge + estimateTextWidth(assignee, 10) + 6 <= plotW) {
        labels.appendChild(svgEl("text", {
          x: rightEdge + 4, y: mid + 3.5, "font-size": 10, fill: "var(--mj-text-muted, #6b7280)"
        }, assignee))
      }
    }

    if (timing.kind !== "none") {
      barPositions.set(key, { rightX: rightEdge, leftX: leftEdge, midY: mid, halfH: barH / 2 })
    }
  }

  /* Dependency arrows between visible rows. */
  if (showDependencies === true) {
    const marker = svgEl("marker", {
      id: "mj-gantt-arrow", markerWidth: 8, markerHeight: 8, refX: 7, refY: 3,
      orient: "auto", markerUnits: "userSpaceOnUse"
    }, [svgEl("path", { d: "M0,0 L0,6 L8,3 Z", fill: "var(--mj-text-muted, #6b7280)" }, [])])
    arrows.appendChild(svgEl("defs", null, [marker]))

    for (let r = 0; r < rows.length; r = r + 1) {
      const row = rows[r]
      if (row.kind !== "task" || Array.isArray(row.task.depends) === false) {
        continue
      }
      const toKey = _taskKey(row.task, row.index)
      const toPos = barPositions.get(toKey)
      if (toPos === undefined) {
        continue
      }
      for (let d = 0; d < row.task.depends.length; d = d + 1) {
        const fromKey = String(row.task.depends[d])
        const fromPos = barPositions.get(fromKey)
        if (fromPos === undefined || fromKey === toKey) {
          continue
        }
        arrows.appendChild(svgEl("path", {
          d: _dependencyPath(fromPos, toPos, rowStep),
          stroke: "var(--mj-text-muted, #6b7280)", "stroke-width": 1.25, fill: "none",
          part: "dependency dependency-arrow", "marker-end": "url(#mj-gantt-arrow)"
        }, []))
      }
    }
  }

  if (scale !== null) {
    _drawMarkers(overlays, _readMarkers(raw), scale, plotW, 0, gridH, ctx)

    const todayX = _todayInRange(ctx, scale, plotW)
    if (todayX !== null) {
      const today = svgEl("g", { "aria-hidden": "true" }, [])
      today.appendChild(svgEl("line", {
        x1: todayX, y1: 0, x2: todayX, y2: gridH,
        stroke: TODAY_COLOR, "stroke-width": 1.5, "stroke-dasharray": "3 3", part: "today-marker"
      }, []))
      const flip = todayX + 36 > plotW
      today.appendChild(svgEl("text", {
        x: flip === true ? todayX - 3 : todayX + 3, y: gridH + 11,
        "text-anchor": flip === true ? "end" : "start",
        "font-size": 9, fill: "var(--mj-text-muted, #6b7280)", part: "today-label"
      }, "Today"))
      overlays.appendChild(today)
    }
  } else {
    labels.appendChild(svgEl("text", {
      x: plotW / 2, y: Math.min(gridH, plotH) / 2, "text-anchor": "middle", "font-size": 12,
      fill: "var(--mj-text-muted, #6b7280)"
    }, "No task has a usable start or end date"))
  }

  /* Legend: what the bar colours stand for. */
  const legend = []
  for (let g = 0; g < groups.keys.length; g = g + 1) {
    legend.push({ label: groups.labels.get(groups.keys[g]), color: ctx.colorFor(groups.keys[g]) })
  }
  ctx.setLegend(legend)
  return
}


/* ---------- roadmap ---------- */

function _calendarColumns(dateMin, dateMax, scaleName) {
  /*
   * Period columns covering dateMin .. dateMax: the period holding dateMin
   * through the period holding the instant before dateMax.
   *
   * :returns: [{ id, label, start, end }] with Date bounds.
   */
  const monthsPer = scaleName === "month" ? 1 : (scaleName === "half-year" ? 6 : 3)
  const columns = []
  let monthIndex = dateMin.getFullYear() * 12 + dateMin.getMonth()
  monthIndex = monthIndex - (monthIndex % monthsPer)
  const lastInstant = dateMax.getTime() - 1

  let start = new Date(Math.floor(monthIndex / 12), monthIndex % 12, 1)
  while ((start.getTime() <= lastInstant || columns.length === 0) && columns.length < ROADMAP_MAX_COLUMNS) {
    const nextIndex = monthIndex + monthsPer
    const end = new Date(Math.floor(nextIndex / 12), nextIndex % 12, 1)
    const year = start.getFullYear()
    const month = start.getMonth()
    let label = ""
    let id = ""
    if (monthsPer === 3) {
      id = `${year}-Q${Math.floor(month / 3) + 1}`
      label = `Q${Math.floor(month / 3) + 1} ${year}`
    } else if (monthsPer === 1) {
      id = `${year}-${String(month + 1).padStart(2, "0")}`
      label = formatDate(start, { month: "short", year: "numeric" })
    } else {
      id = `${year}-H${month < 6 ? 1 : 2}`
      label = `H${month < 6 ? 1 : 2} ${year}`
    }
    columns.push({ id: id, label: label, start: start, end: end })
    monthIndex = nextIndex
    start = end
  }
  return columns
}


function _readBuckets(raw) {
  /*
   * The bucket columns: [{ id, label }].
   */
  const list = Array.isArray(raw.buckets) === true ? raw.buckets : []
  const buckets = []
  const seen = new Set()
  for (let index = 0; index < list.length; index = index + 1) {
    const bucket = list[index]
    if (bucket === null || typeof bucket !== "object") {
      continue
    }
    const label = _text(bucket.label)
    const id = bucket.id !== undefined && bucket.id !== null && String(bucket.id) !== "" ? String(bucket.id) : label
    if (id === "" || seen.has(id) === true) {
      continue
    }
    seen.add(id)
    buckets.push({ id: id, label: label !== "" ? label : id })
  }
  return buckets
}


function _packLane(members) {
  /*
   * Stack the bars of one lane: each bar takes the first sub-row whose last
   * bar ends before it starts.
   *
   * :param members: [{ x1, x2, ... }] (written: `subRow`).
   * :returns: The number of sub-rows (at least 1).
   */
  const ordered = members.slice().sort((a, b) => (a.x1 - b.x1) || (a.index - b.index))
  const rowEnds = []
  for (let m = 0; m < ordered.length; m = m + 1) {
    const member = ordered[m]
    let row = rowEnds.findIndex((end) => end + 4 <= member.x1)
    if (row < 0) {
      row = rowEnds.length
      rowEnds.push(0)
    }
    rowEnds[row] = member.x2
    member.subRow = row
  }
  return Math.max(rowEnds.length, 1)
}


function _renderRoadmap(ctx, raw, root) {
  /*
   * Draw the roadmap: lanes of packed bars under period or bucket columns.
   */
  const tasks = Array.isArray(raw.tasks) === true ? raw.tasks : []
  const groups = _readGroups(raw, tasks)
  const compact = ctx.attrs("density", "normal") === "compact"
  const barH = compact === true ? ROADMAP_BAR_COMPACT : ROADMAP_BAR
  const buckets = _readBuckets(raw)
  const bucketMode = ctx.attrs("mode", "calendar") === "bucket" && buckets.length > 0
  const scaleName = ctx.attrs("scale", "quarter")

  /* Lanes: the groups; tasks without a known group share one lane. */
  const lanes = []
  const laneOf = new Map()
  for (let g = 0; g < groups.keys.length; g = g + 1) {
    laneOf.set(groups.keys[g], lanes.length)
    lanes.push({ key: groups.keys[g], label: groups.labels.get(groups.keys[g]), members: [] })
  }
  const entries = []
  for (let index = 0; index < tasks.length; index = index + 1) {
    const task = tasks[index]
    if (task === null || typeof task !== "object") {
      continue
    }
    const timing = _taskTiming(task)
    entries.push({ task: task, index: index, timing: timing, span: null, x1: 0, x2: 0, subRow: 0 })
  }

  /* Columns and the span of each entry in plot fractions (0..1). */
  let columns = []
  let domain = null
  if (bucketMode === true) {
    columns = buckets.map((bucket) => ({ id: bucket.id, label: bucket.label, start: null, end: null }))
    for (let e = 0; e < entries.length; e = e + 1) {
      const name = _text(entries[e].task.bucket)
      const position = columns.findIndex((column) => column.id === name)
      if (position >= 0) {
        entries[e].span = {
          from: position / columns.length, to: (position + 1) / columns.length,
          text: columns[position].label
        }
      }
    }
  } else {
    domain = _timeDomain(ctx, entries.map((entry) => entry.timing), 0)
    if (domain !== null) {
      columns = _calendarColumns(domain.min, domain.max, scaleName)
      const first = columns[0].start.getTime()
      const last = columns[columns.length - 1].end.getTime()
      const toFraction = (date) => (date.getTime() - first) / (last - first)
      for (let e = 0; e < entries.length; e = e + 1) {
        const timing = entries[e].timing
        if (timing.kind === "none") {
          continue
        }
        const end = timing.end !== null ? timing.end : new Date(last)
        if (end.getTime() <= first || timing.start.getTime() >= last ||
            end.getTime() <= domain.min.getTime() || timing.start.getTime() >= domain.max.getTime()) {
          continue
        }
        let text = formatDate(timing.start)
        if (timing.kind === "bar") {
          text = `${formatDate(timing.start)} to ${formatDate(timing.shownEnd)}`
        } else if (timing.kind === "open") {
          text = `from ${formatDate(timing.start)}`
        }
        entries[e].span = {
          from: Math.max(toFraction(timing.start), 0), to: Math.min(toFraction(end), 1), text: text
        }
      }
    }
  }

  /* Placed entries go to their lane; an unknown group goes to "Unassigned". */
  let unplaced = 0
  for (let e = 0; e < entries.length; e = e + 1) {
    const entry = entries[e]
    if (entry.span === null) {
      unplaced = unplaced + 1
      continue
    }
    const key = groups.keyOf(entry.task)
    let laneIndex = key !== null && laneOf.has(key) === true ? laneOf.get(key) : -1
    if (laneIndex < 0) {
      if (laneOf.has(UNASSIGNED_LANE) === false) {
        laneOf.set(UNASSIGNED_LANE, lanes.length)
        lanes.push({ key: UNASSIGNED_LANE, label: groups.keys.length > 0 ? "Unassigned" : "", members: [] })
      }
      laneIndex = laneOf.get(UNASSIGNED_LANE)
    }
    lanes[laneIndex].members.push(entry)
  }

  /* The accessible table lists every task, placed or not. */
  ctx.setTable({
    columns: ["Initiative", "Group", "Timeframe", "Status", "Progress", "Description"],
    rows: entries.map((entry) => {
      const key = groups.keyOf(entry.task)
      const progress = _progressOf(entry.task)
      return [
        _taskLabel(entry.task, entry.index),
        key !== null ? groups.labels.get(key) : "",
        entry.span !== null ? entry.span.text : "Not placed",
        _statusText(_taskStatus(entry.task)),
        progress !== null ? `${Math.round(progress * 100)}%` : "",
        _text(entry.task.description)
      ]
    })
  })
  ctx.setLegend([])
  if (columns.length === 0 || lanes.length === 0) {
    const reason = bucketMode === true ? "No item names one of the buckets" : "No item has a usable start or end date"
    root.appendChild(svgEl("text", {
      x: ctx.width / 2, y: Math.min(ctx.height, 120) / 2, "text-anchor": "middle", "font-size": 12,
      fill: "var(--mj-text-muted, #6b7280)", part: "unplaced-note"
    }, reason))
    return
  }

  /* Width: the lane-label gutter and the columns share the chart width. */
  let longest = 0
  for (let l = 0; l < lanes.length; l = l + 1) {
    longest = Math.max(longest, estimateTextWidth(lanes[l].label, 12))
  }
  const gutter = lanes.some((lane) => lane.label !== "") === true
    ? Math.min(Math.max(longest + 20, 72), Math.max(ctx.width * 0.28, 72)) : 8
  const plotW = Math.max(ctx.width - gutter - 8, 10)
  const columnW = plotW / columns.length

  for (let l = 0; l < lanes.length; l = l + 1) {
    for (let m = 0; m < lanes[l].members.length; m = m + 1) {
      const member = lanes[l].members[m]
      const x1 = member.span.from * plotW + 3
      const x2 = member.span.to * plotW - 3
      member.x1 = Math.min(x1, plotW - ROADMAP_MIN_BAR)
      member.x2 = Math.max(x2, member.x1 + ROADMAP_MIN_BAR)
    }
    lanes[l].rows = _packLane(lanes[l].members)
    lanes[l].height = ROADMAP_LANE_PAD * 2 + lanes[l].rows * barH + (lanes[l].rows - 1) * ROADMAP_BAR_GAP
  }
  const lanesHeight = lanes.reduce((sum, lane) => sum + lane.height, 0)
  const lanesBottom = ROADMAP_HEADER + lanesHeight

  /* Calendar overlays need a scale over the column range. */
  let scale = null
  let phaseBands = []
  let todayX = null
  const phases = bucketMode === false ? _readPhases(raw) : []
  if (bucketMode === false) {
    scale = timeScale([columns[0].start, columns[columns.length - 1].end], [0, plotW])
    todayX = _todayInRange(ctx, scale, plotW)
  }
  const namedPhase = phases.some((phase) => phase.label !== "")
  const phaseRowH = namedPhase === true ? ROADMAP_FOOTER_ROW : 0
  const todayRowH = todayX !== null ? ROADMAP_FOOTER_ROW : 0
  const noteRowH = unplaced > 0 ? ROADMAP_FOOTER_ROW + 4 : 0
  const totalHeight = lanesBottom + phaseRowH + todayRowH + noteRowH + 4
  ctx.setContentHeight(totalHeight)

  const plot = svgEl("g", { transform: `translate(${gutter},0)` }, [])
  root.appendChild(plot)
  const backdrop = svgEl("g", { "aria-hidden": "true" }, [])
  const marks = svgEl("g", null, [])
  const overlays = svgEl("g", null, [])
  plot.appendChild(backdrop)
  plot.appendChild(marks)
  plot.appendChild(overlays)

  /* Lane label column and column headers. */
  backdrop.appendChild(svgEl("rect", {
    x: -gutter, y: 0, width: gutter, height: lanesBottom, fill: "var(--mj-bg-subtle, #f8f9fb)"
  }, []))
  for (let c = 0; c < columns.length; c = c + 1) {
    const x = c * columnW
    backdrop.appendChild(svgEl("rect", {
      x: x, y: 0, width: columnW, height: ROADMAP_HEADER, fill: "var(--mj-bg-muted, #eef0f3)"
    }, []))
    backdrop.appendChild(svgEl("line", {
      x1: x, y1: 0, x2: x, y2: lanesBottom + phaseRowH, stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    backdrop.appendChild(svgEl("text", {
      x: x + columnW / 2, y: ROADMAP_HEADER / 2 + 4, "text-anchor": "middle", "font-size": 12,
      "font-weight": 500, fill: "var(--mj-text, #14181f)", part: "column-header"
    }, [svgEl("title", null, columns[c].label), fitText(columns[c].label, columnW - 8, 12)]))
  }

  phaseBands = _drawPhaseBands(backdrop, phases, scale, plotW, ROADMAP_HEADER, lanesHeight + phaseRowH)
  for (let p = 0; p < phaseBands.length; p = p + 1) {
    const band = phaseBands[p]
    if (band.label === "") {
      continue
    }
    const text = fitText(band.label, band.x2 - band.x1 - 8, 10)
    if (text !== "") {
      backdrop.appendChild(svgEl("text", {
        x: band.x1 + 4, y: lanesBottom + phaseRowH - 4, "font-size": 10,
        fill: "var(--mj-text-muted, #6b7280)", part: "phase-label"
      }, [svgEl("title", null, band.label), text]))
    }
  }

  /* Lanes and their bars. */
  const statusesSeen = []
  let laneTop = ROADMAP_HEADER
  for (let l = 0; l < lanes.length; l = l + 1) {
    const lane = lanes[l]
    backdrop.appendChild(svgEl("line", {
      x1: -gutter, y1: laneTop, x2: plotW, y2: laneTop, stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    if (lane.label !== "") {
      backdrop.appendChild(svgEl("text", {
        x: -gutter + 8, y: laneTop + lane.height / 2 + 4, "font-size": 12,
        fill: "var(--mj-text, #14181f)", part: "swimlane-label"
      }, [svgEl("title", null, lane.label), fitText(lane.label, gutter - 16, 12)]))
    }

    const ordered = lane.members.slice().sort((a, b) => a.index - b.index)
    for (let m = 0; m < ordered.length; m = m + 1) {
      const entry = ordered[m]
      const task = entry.task
      const label = _taskLabel(task, entry.index)
      const statusKey = _taskStatus(task).toLowerCase()
      const known = Object.prototype.hasOwnProperty.call(STATUS_COLORS, statusKey) === true
      const color = known === true ? STATUS_COLORS[statusKey] : STATUS_COLORS.planned
      const icon = known === true ? STATUS_ICONS[statusKey] : STATUS_ICONS.planned
      if (known === true && statusesSeen.indexOf(statusKey) < 0) {
        statusesSeen.push(statusKey)
      }
      const barY = laneTop + ROADMAP_LANE_PAD + entry.subRow * (barH + ROADMAP_BAR_GAP)
      const barW = entry.x2 - entry.x1
      const statusText = _statusText(_taskStatus(task))
      const ariaLabel = `${label}, ${statusText !== "" ? statusText : "Planned"}, ${entry.span.text}`

      const bar = svgEl("g", {
        part: "bar initiative-bar", tabindex: "0", role: "img", "aria-label": ariaLabel,
        "data-mark": `task:${entry.index}`
      }, [svgEl("title", null, _text(task.description) !== "" ? `${ariaLabel}. ${_text(task.description)}` : ariaLabel)])
      bar.appendChild(svgEl("rect", {
        x: entry.x1, y: barY, width: barW, height: barH, rx: 4,
        fill: "var(--mj-surface, #ffffff)", stroke: color, "stroke-width": 1.5
      }, []))
      bar.appendChild(svgEl("rect", {
        x: entry.x1, y: barY, width: barW, height: barH, rx: 4, fill: color, "fill-opacity": 0.16,
        "pointer-events": "none"
      }, []))
      bar.appendChild(svgEl("text", {
        x: entry.x1 + 6, y: barY + barH / 2 + 4, "font-size": 12, fill: color, "aria-hidden": "true"
      }, icon))
      const text = fitText(label, barW - 26, 11)
      if (text !== "") {
        bar.appendChild(svgEl("text", {
          x: entry.x1 + 20, y: barY + barH / 2 + 4, "font-size": 11, fill: "var(--mj-text, #14181f)",
          part: "initiative-label", "aria-hidden": "true"
        }, text))
      }
      const emitIndex = entry.index
      _onActivate(bar, () => {
        ctx.emit("mj-chart-bar-click", {
          id: task.id, label: task.label, start: task.start, end: task.end, index: emitIndex
        })
      })
      marks.appendChild(bar)
    }
    laneTop = laneTop + lane.height
  }
  backdrop.appendChild(svgEl("line", {
    x1: -gutter, y1: lanesBottom, x2: plotW, y2: lanesBottom, stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
  }, []))

  /* Calendar overlays above the bars: markers and today. */
  if (scale !== null) {
    _drawMarkers(overlays, _readMarkers(raw), scale, plotW, ROADMAP_HEADER, lanesBottom, ctx)
    if (todayX !== null) {
      const today = svgEl("g", { "aria-hidden": "true" }, [])
      const labelY = lanesBottom + phaseRowH + todayRowH - 4
      today.appendChild(svgEl("line", {
        x1: todayX, y1: ROADMAP_HEADER, x2: todayX, y2: lanesBottom + phaseRowH + todayRowH,
        stroke: TODAY_COLOR, "stroke-width": 1.5, "stroke-dasharray": "3 3", part: "today-marker"
      }, []))
      const flip = todayX + 40 > plotW
      today.appendChild(svgEl("text", {
        x: flip === true ? todayX - 4 : todayX + 4, y: labelY,
        "text-anchor": flip === true ? "end" : "start",
        "font-size": 10, fill: TODAY_COLOR, part: "today-label"
      }, "Today"))
      overlays.appendChild(today)
    }
  }

  /* Say so when some tasks could not be placed, so chart and table agree. */
  if (unplaced > 0) {
    const reason = bucketMode === true ? "their bucket is not one of the columns"
      : "they have no dates inside the range"
    const count = entries.length
    const note = `${unplaced} of ${count} item${count === 1 ? " is" : "s are"} not shown because ${reason}; ` +
      "the data table lists them."
    overlays.appendChild(svgEl("text", {
      x: -gutter + 8, y: totalHeight - 8, "font-size": 11, fill: "var(--mj-text-muted, #6b7280)",
      part: "unplaced-note"
    }, fitText(note, plotW + gutter - 16, 11)))
  }

  const legend = []
  const order = Object.keys(STATUS_COLORS)
  for (let s = 0; s < order.length; s = s + 1) {
    if (statusesSeen.indexOf(order[s]) >= 0) {
      legend.push({ label: `${STATUS_ICONS[order[s]]} ${STATUS_LABELS[order[s]]}`, color: STATUS_COLORS[order[s]] })
    }
  }
  ctx.setLegend(legend)
  return
}


export function render(ctx) {
  /*
   * Render a gantt or roadmap chart.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const raw = ctx.raw !== null && ctx.raw !== undefined ? ctx.raw : {}
  const variant = ctx.attrs("style", "")
  let isRoadmap = ctx.type === "roadmap"
  if (variant === "roadmap") {
    isRoadmap = true
  } else if (variant === "gantt") {
    isRoadmap = false
  }

  const root = svgEl("g", { part: "plot" }, [])
  if (isRoadmap === true) {
    _renderRoadmap(ctx, raw, root)
  } else {
    _renderGantt(ctx, raw, root)
  }
  return root
}


function _ganttIsEmpty(model) {
  /*
   * Gantt: nothing to draw without tasks.
   */
  const raw = model.raw !== null && model.raw !== undefined ? model.raw : {}
  const empty = Array.isArray(raw.tasks) === false || raw.tasks.length === 0
  return empty
}


function _roadmapIsEmpty(model) {
  /*
   * Roadmap: nothing to draw without tasks and without declared groups.
   */
  const raw = model.raw !== null && model.raw !== undefined ? model.raw : {}
  const noGroups = Array.isArray(raw.groups) === false || raw.groups.length === 0
  const empty = _ganttIsEmpty(model) === true && noGroups === true
  return empty
}


registerRenderer("gantt", render, { orientation: "horizontal", minHeight: 120, isEmpty: _ganttIsEmpty });
registerRenderer("roadmap", render, { orientation: "horizontal", minHeight: 120, isEmpty: _roadmapIsEmpty });
