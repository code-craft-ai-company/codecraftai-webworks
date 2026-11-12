/*
 * pmchartsupport.js
 *
 * Helpers shared by the project-management chart components (mj-branch-graph,
 * mj-burndown-chart, mj-cumulative-flow, mj-velocity-chart, mj-pipeline-chart,
 * mj-workflow-diagram, mj-release-calendar, mj-env-promotion-chart and
 * mj-build-status-board). mj-gantt-chart, mj-roadmap-chart,
 * mj-milestone-timeline and mj-dependency-graph wrap <mj-chart> types and use
 * only the styles, the detail panel and the text / date helpers (through
 * pmchartwrapper.js).
 *
 * This module is not a component and registers nothing. It holds the pieces
 * every one of those charts needs so each is written once:
 *   - calendar-date parsing (`YYYY-MM-DD` is a local calendar day) and
 *     formatting that never throws on an invalid date;
 *   - time-range resolution and tick generation on day / month boundaries;
 *   - the theme-aware series palette and band patterns;
 *   - a cycle-safe layered layout for the node / edge diagrams;
 *   - delegated mark interaction with a roving tabindex;
 *   - the non-modal detail panel (focus in, Escape, focus back);
 *   - width observation, declarative data loading and the empty state;
 *   - `PmChartElement`, the base class that ties those together.
 */

import { MjElement } from "../core/mjelement.js";
import { html } from "../core/html.js";
import { formatDate, t } from "../core/intl.js";
import { resolveChartData } from "../charts/core/jsonsource.js";

export const DAY_MS = 86400000;

const DATE_ONLY_PATTERN = /^(\d{4})-(\d{2})-(\d{2})$/;

/* Shown wherever a date is missing or cannot be parsed. */
export const DATE_PLACEHOLDER = "—";

/*
 * Series palette. Each entry reads a `--mj-chart-series-N` custom property
 * and falls back to a light / dark pair that keeps 3:1 against the surface
 * of the active theme (`light-dark()` follows the inherited `color-scheme`
 * that tokens.css sets per theme).
 */
export const SERIES_COLORS = [
  "var(--mj-chart-series-1, light-dark(#2563eb, #8ab4ff))",
  "var(--mj-chart-series-2, light-dark(#15803d, #4ade80))",
  "var(--mj-chart-series-3, light-dark(#b45309, #fbbf24))",
  "var(--mj-chart-series-4, light-dark(#b91c1c, #f98080))",
  "var(--mj-chart-series-5, light-dark(#7c3aed, #c4b5fd))",
  "var(--mj-chart-series-6, light-dark(#0e7490, #67e8f9))",
  "var(--mj-chart-series-7, light-dark(#c2410c, #fdba74))",
  "var(--mj-chart-series-8, light-dark(#be185d, #f9a8d4))"
];

/* Committed / secondary series: a muted fill that still has a visible edge. */
export const SECONDARY_SERIES_FILL = "var(--mj-chart-series-secondary, var(--mj-bg-muted))";
export const SECONDARY_SERIES_STROKE = "var(--mj-chart-series-secondary-border, var(--mj-border-strong))";

/*
 * Styles common to every chart in this family. A component's stylesheet is
 * this block followed by its own rules.
 */
export const PM_CHART_STYLES = `
:host {
  display: block;
  font-family: var(--mj-font-sans);
  font-size: var(--mj-font-size-sm);
  color: var(--mj-text);
  background: var(--mj-bg);
  border: 1px solid var(--mj-border);
  border-radius: var(--mj-radius-md);
  overflow: hidden;
}
.wrapper { display: flex; flex-direction: column; block-size: 100%; }
.toolbar { display: flex; align-items: center; gap: var(--mj-space-2); padding: var(--mj-space-2) var(--mj-space-3); border-block-end: 1px solid var(--mj-border); flex-wrap: wrap; }
.toolbar-title { font-size: var(--mj-font-size-sm); font-weight: var(--mj-font-weight-bold); }
.toolbar-spacer { flex: 1; }
.chart-button { font: inherit; font-size: var(--mj-font-size-xs); background: var(--mj-surface); border: 1px solid var(--mj-border-strong); border-radius: var(--mj-radius-sm); padding: 2px var(--mj-space-2); min-block-size: 24px; cursor: pointer; color: var(--mj-text); }
.chart-button:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); outline-offset: var(--mj-focus-ring-offset); }
.chart-frame { position: relative; flex: 1; min-block-size: 0; display: flex; flex-direction: column; }
.chart-scroll { flex: 1; min-block-size: 0; overflow: auto; }
svg { display: block; }
[data-mark] { cursor: pointer; }
[data-mark]:focus { outline: none; }
[data-mark]:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); outline-offset: 2px; }
.detail-panel { background: var(--mj-surface-raised); border: 1px solid var(--mj-border-strong); border-radius: var(--mj-radius-md); padding: var(--mj-space-3); box-shadow: var(--mj-elevation-2); }
.detail-panel:focus { outline: none; }
.detail-panel:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); outline-offset: calc(0px - var(--mj-focus-ring-width)); }
.detail-panel.is-floating { position: absolute; inset-block-start: var(--mj-space-3); inset-inline-end: var(--mj-space-3); min-inline-size: 200px; max-inline-size: calc(100% - 2 * var(--mj-space-3)); max-block-size: calc(100% - 2 * var(--mj-space-3)); overflow: auto; z-index: var(--mj-layer-docked); }
.detail-panel.is-inline { border-radius: 0; border-inline: none; border-block-end: none; box-shadow: none; }
.detail-head { display: flex; align-items: flex-start; gap: var(--mj-space-2); margin-block-end: var(--mj-space-2); }
.detail-head h3 { flex: 1; margin: 0; font-size: var(--mj-font-size-sm); overflow-wrap: anywhere; }
.detail-close { font: inherit; font-size: 1rem; line-height: 1; min-inline-size: 24px; min-block-size: 24px; background: none; border: none; border-radius: var(--mj-radius-sm); cursor: pointer; color: var(--mj-text-muted); }
.detail-close:focus-visible { outline: var(--mj-focus-ring-width) solid var(--mj-focus-ring); outline-offset: var(--mj-focus-ring-offset); }
.detail-content p { margin: 0 0 var(--mj-space-1); overflow-wrap: anywhere; }
.a11y-table-wrap, .a11y-list-wrap { padding: var(--mj-space-3); overflow-x: auto; }
.a11y-table-wrap table { border-collapse: collapse; inline-size: 100%; font-size: var(--mj-font-size-sm); }
.a11y-table-wrap caption { text-align: start; padding-block-end: var(--mj-space-1); color: var(--mj-text-muted); font-size: var(--mj-font-size-xs); }
.a11y-table-wrap th, .a11y-table-wrap td { border: 1px solid var(--mj-border); padding: var(--mj-space-1) var(--mj-space-2); text-align: start; }
.a11y-list-wrap ol { margin: 0; padding-inline-start: var(--mj-space-5); font-size: var(--mj-font-size-sm); }
.a11y-list-wrap dl { margin: 0; font-size: var(--mj-font-size-sm); }
.a11y-list-wrap dt { font-weight: var(--mj-font-weight-medium); margin-block-start: var(--mj-space-2); }
.a11y-list-wrap dd { margin-inline-start: var(--mj-space-4); color: var(--mj-text-muted); }
.empty-state { padding: var(--mj-space-5) var(--mj-space-3); text-align: center; color: var(--mj-text-muted); font-size: var(--mj-font-size-sm); }
.empty-state[data-state="error"] { color: var(--mj-color-danger); }
.legend { display: flex; flex-wrap: wrap; gap: var(--mj-space-3); padding: var(--mj-space-2) var(--mj-space-3); border-block-start: 1px solid var(--mj-border); font-size: var(--mj-font-size-xs); }
.legend-item { display: flex; align-items: center; gap: var(--mj-space-1); }
[hidden] { display: none !important; }
`;

/* ----- dates ----- */

/*
 * Parse a chart date. A `YYYY-MM-DD` string is a calendar day and becomes
 * local midnight of that day -- `new Date("2026-05-01")` would be UTC
 * midnight, which is the previous day west of UTC. Anything else goes
 * through the Date constructor. Returns null for a missing or invalid value.
 */
export function parseChartDate(value) {
  let parsed = null

  if (value instanceof Date) {
    parsed = new Date(value.getTime())
  } else if (typeof value === "number") {
    parsed = new Date(value)
  } else if (typeof value === "string" && value.trim().length > 0) {
    const text = value.trim()
    const match = text.match(DATE_ONLY_PATTERN)
    if (match !== null) {
      const year = Number(match[1])
      const monthIndex = Number(match[2]) - 1
      const day = Number(match[3])
      parsed = new Date(year, monthIndex, day)
      if (parsed.getMonth() !== monthIndex || parsed.getDate() !== day) {
        /* 2026-02-31 and friends roll over; treat them as invalid. */
        parsed = null
      }
    } else {
      parsed = new Date(text)
    }
  }

  if (parsed !== null && Number.isNaN(parsed.getTime()) === true) {
    parsed = null
  }

  return parsed
}

/* Epoch milliseconds for a chart date, or NaN when it cannot be parsed. */
export function chartTime(value) {
  const parsed = parseChartDate(value)
  const time = parsed !== null ? parsed.getTime() : Number.NaN
  return time
}

/* True when `value` names a calendar day rather than an instant. */
export function isDateOnly(value) {
  const dateOnly = typeof value === "string" && DATE_ONLY_PATTERN.test(value.trim()) === true
  return dateOnly
}

/*
 * The instant at which a span that ends on `value` is over. An end given as
 * a calendar day is inclusive, so the span runs to the start of the next
 * day; an end given as an instant is used as is.
 */
export function chartEndTime(value) {
  let time = chartTime(value)

  if (Number.isNaN(time) === false && isDateOnly(value) === true) {
    const day = new Date(time)
    const nextDay = new Date(day.getFullYear(), day.getMonth(), day.getDate() + 1)
    time = nextDay.getTime()
  }

  return time
}

/* `YYYY-MM-DD` for the local calendar day of `date`. */
export function localDateKey(date) {
  const year = String(date.getFullYear()).padStart(4, "0")
  const month = String(date.getMonth() + 1).padStart(2, "0")
  const day = String(date.getDate()).padStart(2, "0")
  const key = `${year}-${month}-${day}`
  return key
}

/* Local midnight of the day that contains `time`. */
export function startOfLocalDay(time) {
  const moment = new Date(time)
  const start = new Date(moment.getFullYear(), moment.getMonth(), moment.getDate())
  const startTime = start.getTime()
  return startTime
}

/*
 * Format a chart date. Never throws: a missing or invalid date yields
 * `fallback` (the placeholder dash by default).
 */
export function formatChartDate(value, options, fallback) {
  const parsed = parseChartDate(value)
  let formatted = fallback !== undefined ? fallback : DATE_PLACEHOLDER

  if (parsed !== null) {
    formatted = formatDate(parsed, options)
  }

  return formatted
}

/*
 * Resolve the time range of a chart.
 *
 * times      epoch values found in the data (NaN entries are ignored)
 * startAttr  the `start-date` attribute value or null
 * endAttr    the `end-date` attribute value or null
 * padMs      added on both sides when the range comes from the data
 *
 * Invalid attribute dates are ignored, reversed bounds are swapped and a
 * range without any extent is widened by a day on each side so it can be
 * scaled. Returns { min, max, hasData }.
 */
export function resolveTimeRange(times, startAttr, endAttr, padMs) {
  const valid = []
  for (let index = 0; index < times.length; index = index + 1) {
    if (Number.isNaN(times[index]) === false && times[index] !== null && times[index] !== undefined) {
      valid.push(times[index])
    }
  }

  const pad = padMs !== undefined ? padMs : 0
  const hasData = valid.length > 0
  const now = Date.now()

  let min = hasData === true ? Math.min(...valid) - pad : now - 15 * DAY_MS
  let max = hasData === true ? Math.max(...valid) + pad : now + 15 * DAY_MS

  const startTime = chartTime(startAttr)
  if (Number.isNaN(startTime) === false) {
    min = startTime
  }

  const endTime = isDateOnly(endAttr) === true ? chartEndTime(endAttr) : chartTime(endAttr)
  if (Number.isNaN(endTime) === false) {
    max = endTime
  }

  if (min > max) {
    const swapped = min
    min = max
    max = swapped
  }

  if (max - min < DAY_MS / 2) {
    min = min - DAY_MS
    max = max + DAY_MS
  }

  const range = { min: min, max: max, hasData: hasData }
  return range
}

function tickCandidates(unit) {
  const candidates = []

  if (unit === "day") {
    const steps = [1, 2, 5, 10, 20, 50, 100, 200, 500]
    for (let index = 0; index < steps.length; index = index + 1) {
      candidates.push({ kind: "day", step: steps[index] })
    }
  } else if (unit === "week") {
    const steps = [7, 14, 28, 56, 112, 224, 448]
    for (let index = 0; index < steps.length; index = index + 1) {
      candidates.push({ kind: "day", step: steps[index] })
    }
  } else if (unit === "month") {
    const steps = [1, 2, 3, 6, 12, 24, 60, 120]
    for (let index = 0; index < steps.length; index = index + 1) {
      candidates.push({ kind: "month", step: steps[index] })
    }
  } else if (unit === "quarter") {
    const steps = [3, 6, 12, 24, 60, 120]
    for (let index = 0; index < steps.length; index = index + 1) {
      candidates.push({ kind: "month", step: steps[index] })
    }
  } else {
    const daySteps = [1, 2, 7, 14]
    for (let index = 0; index < daySteps.length; index = index + 1) {
      candidates.push({ kind: "day", step: daySteps[index] })
    }
    const monthSteps = [1, 3, 6, 12, 24, 60, 120, 240, 600]
    for (let index = 0; index < monthSteps.length; index = index + 1) {
      candidates.push({ kind: "month", step: monthSteps[index] })
    }
  }

  return candidates
}

/*
 * Ticks for a time axis, placed on local day or month boundaries.
 *
 * maxCount  the most ticks the axis has room for (values below 1 count as 1)
 * unit      optional "day" | "week" | "month" | "quarter" to force the
 *           granularity (the step still grows when there is no room)
 *
 * Returns { times, labelOptions } where `labelOptions` suits `formatDate`.
 * There is always at least one tick.
 */
export function timeTicks(min, max, maxCount, unit) {
  const limit = Number.isFinite(maxCount) === true && maxCount >= 1 ? Math.floor(maxCount) : 1
  const candidates = tickCandidates(unit)
  const span = Math.max(0, max - min)

  let chosen = candidates[candidates.length - 1]
  for (let index = 0; index < candidates.length; index = index + 1) {
    const candidate = candidates[index]
    const approximateMs = candidate.kind === "day" ? candidate.step * DAY_MS : candidate.step * 30.44 * DAY_MS
    const count = Math.floor(span / approximateMs) + 1
    if (count <= limit) {
      chosen = candidate
      break
    }
  }

  const times = []
  const first = new Date(min)
  /* A hard stop so a degenerate range can never spin. */
  const guard = 2000

  if (chosen.kind === "day") {
    let cursor = new Date(first.getFullYear(), first.getMonth(), first.getDate())
    if (cursor.getTime() < min) {
      cursor = new Date(cursor.getFullYear(), cursor.getMonth(), cursor.getDate() + 1)
    }
    while (cursor.getTime() <= max && times.length < guard) {
      times.push(cursor.getTime())
      cursor = new Date(cursor.getFullYear(), cursor.getMonth(), cursor.getDate() + chosen.step)
    }
  } else {
    let monthIndex = first.getFullYear() * 12 + first.getMonth()
    let cursor = new Date(first.getFullYear(), first.getMonth(), 1)
    if (cursor.getTime() < min) {
      monthIndex = monthIndex + 1
    }
    /* Align quarter / half-year / year steps to the calendar. */
    const remainder = monthIndex % chosen.step
    if (remainder !== 0) {
      monthIndex = monthIndex + (chosen.step - remainder)
    }
    cursor = new Date(Math.floor(monthIndex / 12), monthIndex % 12, 1)
    while (cursor.getTime() <= max && times.length < guard) {
      times.push(cursor.getTime())
      monthIndex = monthIndex + chosen.step
      cursor = new Date(Math.floor(monthIndex / 12), monthIndex % 12, 1)
    }
  }

  if (times.length === 0) {
    times.push(min)
  }

  let labelOptions = { month: "short", day: "numeric" }
  if (chosen.kind === "month") {
    labelOptions = chosen.step >= 12 ? { year: "numeric" } : { month: "short", year: "numeric" }
  }

  const ticks = { times: times, labelOptions: labelOptions }
  return ticks
}

/* ----- text ----- */

/* Coerce a data field to a finite number; anything else becomes `fallback`. */
export function toNumber(value, fallback) {
  const defaultValue = fallback !== undefined ? fallback : 0
  let result = defaultValue

  if (typeof value === "number") {
    result = Number.isFinite(value) === true ? value : defaultValue
  } else if (typeof value === "string" && value.trim().length > 0) {
    const numeric = Number(value)
    result = Number.isFinite(numeric) === true ? numeric : defaultValue
  }

  return result
}

/* Coerce a data field to display text; null and undefined become "". */
export function toText(value) {
  const text = value !== null && value !== undefined ? String(value) : ""
  return text
}

/* Cut `value` to `maxChars` characters, ending in an ellipsis when cut. */
export function truncateLabel(value, maxChars) {
  const text = toText(value)
  let label = text

  if (text.length > maxChars) {
    label = `${text.slice(0, Math.max(1, maxChars - 1))}…`
  }

  return label
}

/*
 * Cut a label in the middle so a distinguishing suffix survives
 * ("Sprint 10" and "Sprint 11" must not both become "Sprint 1").
 */
export function truncateMiddle(value, maxChars) {
  const text = toText(value)
  let label = text

  if (text.length > maxChars && maxChars >= 3) {
    const tailLength = Math.floor((maxChars - 1) / 2)
    const headLength = maxChars - 1 - tailLength
    label = `${text.slice(0, headLength)}…${text.slice(text.length - tailLength)}`
  } else if (text.length > maxChars) {
    label = text.slice(text.length - maxChars)
  }

  return label
}

/* ----- palette ----- */

/* The palette color for series `index` (the palette repeats). */
export function seriesColor(index) {
  const color = SERIES_COLORS[index % SERIES_COLORS.length]
  return color
}

/*
 * Markup for an SVG <pattern> that fills a band of series `index`. Eight
 * distinct textures, drawn in the surface color over the series color, so a
 * band is identifiable without relying on hue. Past eight series the colors
 * repeat with the texture shifted by one, so the ninth series is the first
 * color with the second texture and stays distinguishable from the first.
 */
export function seriesPatternMarkup(patternId, index) {
  const color = seriesColor(index)
  /* Shift the texture by one on every lap of the palette. */
  const texture = (index + Math.floor(index / SERIES_COLORS.length)) % 8
  const ink = "var(--mj-surface)"
  let overlay = html``

  if (texture === 1) {
    overlay = html`<line x1="0" y1="8" x2="8" y2="0" stroke="${ink}" stroke-width="1.5" opacity="0.6"/>`
  } else if (texture === 2) {
    overlay = html`<circle cx="4" cy="4" r="1.6" fill="${ink}" opacity="0.7"/>`
  } else if (texture === 3) {
    overlay = html`<line x1="0" y1="4" x2="8" y2="4" stroke="${ink}" stroke-width="1.5" opacity="0.6"/>`
  } else if (texture === 4) {
    overlay = html`<line x1="4" y1="0" x2="4" y2="8" stroke="${ink}" stroke-width="1.5" opacity="0.6"/>`
  } else if (texture === 5) {
    overlay = html`<line x1="0" y1="0" x2="8" y2="8" stroke="${ink}" stroke-width="1.5" opacity="0.6"/>`
  } else if (texture === 6) {
    overlay = html`<path d="M0,4 L8,4 M4,0 L4,8" stroke="${ink}" stroke-width="1" opacity="0.6"/>`
  } else if (texture === 7) {
    overlay = html`<path d="M0,0 L8,8 M0,8 L8,0" stroke="${ink}" stroke-width="1" opacity="0.6"/>`
  }

  const markup = html`<pattern id="${patternId}" patternUnits="userSpaceOnUse" width="8" height="8"><rect width="8" height="8" fill="${color}" opacity="0.8"/>${overlay}</pattern>`
  return markup
}

/* ----- layered graph layout ----- */

/*
 * Lay out a directed graph in levels (columns), tolerating cycles.
 *
 * nodeIds  ids in display order (duplicates are ignored)
 * edges    [{ from, to }] -- an edge whose endpoint is not a known id is
 *          reported as "dangling" and takes no part in the layout
 * options  { nodeHeight, rowGap, dummyHeight, rootIds }
 *          rootIds: ids the depth-first search starts from (for example the
 *          start states of a workflow), before nodes without predecessors
 *
 * Method:
 *   1. A depth-first search marks every edge that closes a cycle as a back
 *      edge; the remaining edges form a DAG.
 *   2. Each node gets the level of its longest path from a root in that DAG,
 *      so a cycle no longer drags the nodes after it into one column.
 *   3. An edge that skips levels gets a placeholder slot in every level it
 *      passes, so it can be routed between the boxes instead of behind them.
 *   4. A few barycentre sweeps order each level to reduce crossings.
 *
 * Returns {
 *   levelCount, height, backEdgeCount,
 *   nodes:  Map(id -> { level, centerY }),
 *   routes: per edge, in edge order, { kind, waypoints } where kind is
 *           "forward" | "back" | "self" | "dangling" and waypoints are the
 *           { level, centerY } slots a forward edge passes between its ends
 * }
 * centerY is measured from the top of the tallest column.
 */
export function layoutLayeredGraph(nodeIds, edges, options) {
  const opts = options || {}
  const nodeHeight = opts.nodeHeight !== undefined ? opts.nodeHeight : 48
  const rowGap = opts.rowGap !== undefined ? opts.rowGap : 24
  const dummyHeight = opts.dummyHeight !== undefined ? opts.dummyHeight : 12
  const rootIds = Array.isArray(opts.rootIds) === true ? opts.rootIds : []

  const ids = []
  const adjacency = new Map()
  const inDegree = new Map()
  nodeIds.forEach((id) => {
    if (adjacency.has(id) === false) {
      ids.push(id)
      adjacency.set(id, [])
      inDegree.set(id, 0)
    }
  })

  const routes = edges.map((edge) => {
    const safe = edge !== null && typeof edge === "object" ? edge : {}
    let kind = "forward"
    if (adjacency.has(safe.from) === false || adjacency.has(safe.to) === false) {
      kind = "dangling"
    } else if (safe.from === safe.to) {
      kind = "self"
    }
    const route = { kind: kind, from: safe.from, to: safe.to, waypoints: [] }
    return route
  })
  routes.forEach((route, index) => {
    if (route.kind === "forward") {
      adjacency.get(route.from).push({ to: route.to, index: index })
      inDegree.set(route.to, inDegree.get(route.to) + 1)
    }
  })

  /* 1. Depth-first search (iterative): post-order and back edges. */
  const searchOrder = []
  rootIds.forEach((id) => {
    if (adjacency.has(id) === true) {
      searchOrder.push(id)
    }
  })
  ids.forEach((id) => {
    if (inDegree.get(id) === 0) {
      searchOrder.push(id)
    }
  })
  ids.forEach((id) => {
    searchOrder.push(id)
  })

  const WHITE = 0
  const GRAY = 1
  const BLACK = 2
  const color = new Map()
  ids.forEach((id) => {
    color.set(id, WHITE)
  })
  const postOrder = []
  let backEdgeCount = 0

  searchOrder.forEach((root) => {
    if (color.get(root) !== WHITE) {
      return
    }
    const stack = [{ id: root, next: 0 }]
    color.set(root, GRAY)
    while (stack.length > 0) {
      const frame = stack[stack.length - 1]
      const outgoing = adjacency.get(frame.id)
      if (frame.next < outgoing.length) {
        const edge = outgoing[frame.next]
        frame.next = frame.next + 1
        const targetColor = color.get(edge.to)
        if (targetColor === WHITE) {
          color.set(edge.to, GRAY)
          stack.push({ id: edge.to, next: 0 })
        } else if (targetColor === GRAY) {
          routes[edge.index].kind = "back"
          backEdgeCount = backEdgeCount + 1
        }
      } else {
        color.set(frame.id, BLACK)
        postOrder.push(frame.id)
        stack.pop()
      }
    }
  })

  /* 2. Longest-path levels over the forward edges, in topological order. */
  const level = new Map()
  ids.forEach((id) => {
    level.set(id, 0)
  })
  for (let position = postOrder.length - 1; position >= 0; position = position - 1) {
    const id = postOrder[position]
    adjacency.get(id).forEach((edge) => {
      if (routes[edge.index].kind === "forward") {
        level.set(edge.to, Math.max(level.get(edge.to), level.get(id) + 1))
      }
    })
  }

  let levelCount = 0
  ids.forEach((id) => {
    levelCount = Math.max(levelCount, level.get(id) + 1)
  })

  /* 3. Items per level: the nodes, plus a slot for every level an edge skips. */
  const layers = []
  for (let index = 0; index < levelCount; index = index + 1) {
    layers.push([])
  }
  const nodeItem = new Map()
  ids.forEach((id) => {
    const item = { id: id, isDummy: false, level: level.get(id), before: [], after: [], centerY: 0 }
    nodeItem.set(id, item)
    layers[item.level].push(item)
  })
  const routeItems = new Map()
  routes.forEach((route, index) => {
    if (route.kind !== "forward") {
      return
    }
    const chain = [nodeItem.get(route.from)]
    for (let step = level.get(route.from) + 1; step < level.get(route.to); step = step + 1) {
      const dummy = { id: null, isDummy: true, level: step, before: [], after: [], centerY: 0 }
      layers[step].push(dummy)
      chain.push(dummy)
    }
    chain.push(nodeItem.get(route.to))
    for (let link = 0; link < chain.length - 1; link = link + 1) {
      chain[link].after.push(chain[link + 1])
      chain[link + 1].before.push(chain[link])
    }
    routeItems.set(index, chain.slice(1, chain.length - 1))
  })

  /* 4. Barycentre ordering. */
  const reorder = (layer, neighboursOf) => {
    const position = new Map()
    layer.forEach((item, index) => {
      position.set(item, index)
    })
    const keyed = layer.map((item, index) => {
      const neighbours = neighboursOf(item)
      let weight = index
      if (neighbours.length > 0) {
        weight = neighbours.reduce((sum, neighbour) => sum + neighbour.order, 0) / neighbours.length
      }
      const entry = { item: item, weight: weight, index: index }
      return entry
    })
    keyed.sort((a, b) => {
      const order = a.weight === b.weight ? a.index - b.index : a.weight - b.weight
      return order
    })
    keyed.forEach((entry, index) => {
      layer[index] = entry.item
      entry.item.order = index
    })
  }
  layers.forEach((layer) => {
    layer.forEach((item, index) => {
      item.order = index
    })
  })
  for (let sweep = 0; sweep < 4; sweep = sweep + 1) {
    for (let index = 1; index < layers.length; index = index + 1) {
      reorder(layers[index], (item) => item.before)
    }
    for (let index = layers.length - 2; index >= 0; index = index - 1) {
      reorder(layers[index], (item) => item.after)
    }
  }

  /* Vertical positions: each column is centred on the tallest one. */
  const columnHeight = (layer) => {
    const total = layer.reduce((sum, item) => sum + (item.isDummy === true ? dummyHeight : nodeHeight), 0) + Math.max(0, layer.length - 1) * rowGap
    return total
  }
  const height = layers.reduce((tallest, layer) => Math.max(tallest, columnHeight(layer)), nodeHeight)
  layers.forEach((layer) => {
    let cursor = (height - columnHeight(layer)) / 2
    layer.forEach((item) => {
      const itemHeight = item.isDummy === true ? dummyHeight : nodeHeight
      item.centerY = cursor + itemHeight / 2
      cursor = cursor + itemHeight + rowGap
    })
  })

  const nodes = new Map()
  ids.forEach((id) => {
    const item = nodeItem.get(id)
    nodes.set(id, { level: item.level, centerY: item.centerY })
  })
  routes.forEach((route, index) => {
    if (routeItems.has(index) === true) {
      route.waypoints = routeItems.get(index).map((item) => ({ level: item.level, centerY: item.centerY }))
    }
  })

  const layout = { levelCount: Math.max(1, levelCount), height: height, backEdgeCount: backEdgeCount, nodes: nodes, routes: routes }
  return layout
}

/*
 * Path data for a left-to-right edge from (x1, y1) to (x2, y2) that passes
 * the given slots: `waypoints` are { left, right, y } spans the edge crosses
 * horizontally (the placeholder slots of a level-skipping edge).
 */
export function forwardEdgePath(x1, y1, x2, y2, waypoints) {
  const segments = [`M${x1},${y1}`]
  let fromX = x1
  let fromY = y1

  const curveTo = (toX, toY) => {
    const midX = (fromX + toX) / 2
    segments.push(`C${midX},${fromY} ${midX},${toY} ${toX},${toY}`)
    fromX = toX
    fromY = toY
  }

  waypoints.forEach((slot) => {
    curveTo(slot.left, slot.y)
    segments.push(`L${slot.right},${slot.y}`)
    fromX = slot.right
  })
  curveTo(x2, y2)

  const path = segments.join(" ")
  return path
}

/*
 * Path data for a polyline through `points` ([{ x, y }]) with its corners
 * rounded by `radius`. Used for return edges that run around the nodes.
 */
export function roundedPath(points, radius) {
  const segments = []

  points.forEach((point, index) => {
    if (index === 0) {
      segments.push(`M${point.x},${point.y}`)
      return
    }
    if (index === points.length - 1) {
      segments.push(`L${point.x},${point.y}`)
      return
    }
    const previous = points[index - 1]
    const next = points[index + 1]
    const inLength = Math.hypot(point.x - previous.x, point.y - previous.y)
    const outLength = Math.hypot(next.x - point.x, next.y - point.y)
    const corner = Math.min(radius, inLength / 2, outLength / 2)
    if (corner <= 0) {
      segments.push(`L${point.x},${point.y}`)
      return
    }
    const startX = point.x - ((point.x - previous.x) / inLength) * corner
    const startY = point.y - ((point.y - previous.y) / inLength) * corner
    const endX = point.x + ((next.x - point.x) / outLength) * corner
    const endY = point.y + ((next.y - point.y) / outLength) * corner
    segments.push(`L${startX},${startY} Q${point.x},${point.y} ${endX},${endY}`)
  })

  const path = segments.join(" ")
  return path
}

/* ----- DOM helpers ----- */

/*
 * Replace the children of `container` with `markup`, keeping keyboard focus
 * on the same mark: if a `[data-mark]` element inside the container had
 * focus, the element with the same key is focused again afterwards.
 */
export function replaceMarkup(container, markup) {
  const root = container.getRootNode()
  const active = root !== null && root.activeElement !== undefined ? root.activeElement : null
  let focusKey = null

  if (active !== null && container.contains(active) === true) {
    focusKey = active.getAttribute("data-mark")
  }

  container.innerHTML = String(markup)

  if (focusKey !== null) {
    const next = findMark(container, focusKey)
    if (next !== null) {
      next.focus({ preventScroll: true })
    }
  }

  return
}

/* The `[data-mark]` element with key `key` inside `container`, or null. */
export function findMark(container, key) {
  let found = null

  if (key !== null && key !== undefined) {
    const marks = container.querySelectorAll("[data-mark]")
    for (let index = 0; index < marks.length; index = index + 1) {
      if (marks[index].getAttribute("data-mark") === key) {
        found = marks[index]
        break
      }
    }
  }

  return found
}

/*
 * Give exactly one mark in `container` tabindex 0 (the one with `activeKey`,
 * or the first when that key is gone) and every other mark tabindex -1.
 * Returns the key that ended up in the tab order, or null without marks.
 */
export function syncRovingMarks(container, activeKey) {
  const marks = container.querySelectorAll("[data-mark]")
  let active = findMark(container, activeKey)

  if (active === null && marks.length > 0) {
    active = marks[0]
  }

  for (let index = 0; index < marks.length; index = index + 1) {
    marks[index].setAttribute("tabindex", marks[index] === active ? "0" : "-1")
  }

  const resolvedKey = active !== null ? active.getAttribute("data-mark") : null
  return resolvedKey
}

/*
 * Wire a container of `[data-mark]` elements once (delegated listeners, so
 * redrawing the marks registers nothing new):
 *   - click, Enter and Space activate the mark (`onActivate(mark, event)`);
 *     Space does not scroll the page;
 *   - arrow keys, Home and End move focus between marks (roving tabindex);
 *   - focusing a mark makes it the one tab stop.
 * `onFocusKey(key)` is told which mark holds the tab stop so the component
 * can keep it across redraws.
 */
export function wireMarks(host, container, onActivate, onFocusKey) {
  host.listen(container, "click", (event) => {
    const mark = event.target.closest("[data-mark]")
    if (mark !== null && container.contains(mark) === true) {
      onActivate(mark, event)
    }
  })

  host.listen(container, "keydown", (event) => {
    const mark = event.target.closest("[data-mark]")
    if (mark === null || container.contains(mark) === false) {
      return
    }

    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault()
      onActivate(mark, event)
      return
    }

    const marks = Array.from(container.querySelectorAll("[data-mark]"))
    const current = marks.indexOf(mark)
    let target = -1

    if (event.key === "ArrowRight" || event.key === "ArrowDown") {
      target = Math.min(marks.length - 1, current + 1)
    } else if (event.key === "ArrowLeft" || event.key === "ArrowUp") {
      target = Math.max(0, current - 1)
    } else if (event.key === "Home") {
      target = 0
    } else if (event.key === "End") {
      target = marks.length - 1
    }

    if (target >= 0) {
      event.preventDefault()
      marks[target].focus()
    }
  })

  host.listen(container, "focusin", (event) => {
    const mark = event.target.closest("[data-mark]")
    if (mark !== null && container.contains(mark) === true) {
      const key = syncRovingMarks(container, mark.getAttribute("data-mark"))
      if (typeof onFocusKey === "function") {
        onFocusKey(key)
      }
    }
  })

  return
}

/*
 * Reflect which mark is selected: the mark with `selectedKey` gets
 * aria-pressed="true" and data-selected, every other mark aria-pressed
 * "false". Pass null to clear. Marks that carry aria-expanded are skipped.
 */
export function markSelection(container, selectedKey) {
  const marks = container.querySelectorAll("[data-mark]")

  for (let index = 0; index < marks.length; index = index + 1) {
    const mark = marks[index]
    if (mark.hasAttribute("aria-expanded") === true) {
      /* A disclosure mark reports its own state; it is never "pressed". */
      continue
    }
    const selected = selectedKey !== null && mark.getAttribute("data-mark") === selectedKey
    mark.setAttribute("aria-pressed", selected === true ? "true" : "false")
    if (selected === true) {
      mark.setAttribute("data-selected", "true")
    } else {
      mark.removeAttribute("data-selected")
    }
  }

  return
}

/*
 * Markup for the detail panel shared by the charts: a labelled, non-modal
 * region with a heading, a Close button, a content block and a named slot.
 *
 * options: { headingId, part, slotName, placement: "floating" | "inline" }
 */
export function detailPanelMarkup(options) {
  const placementClass = options.placement === "inline" ? "is-inline" : "is-floating"
  const closeLabel = t("core.close")

  const markup = html`
    <div class="detail-panel ${placementClass}" part="${options.part}" role="region" aria-labelledby="${options.headingId}" tabindex="-1" hidden>
      <div class="detail-head">
        <h3 id="${options.headingId}"></h3>
        <button class="detail-close" type="button" aria-label="${closeLabel}">&#x2715;</button>
      </div>
      <div class="detail-content"></div>
      <slot name="${options.slotName}"></slot>
    </div>`
  return markup
}

/*
 * Behaviour of the detail panel. Opening shows the panel and moves focus
 * into it; the Close button, or Escape anywhere inside the component, hides
 * it and puts focus back on the mark that opened it. `onClosed()` runs after
 * every close so the component can clear its selection and emit its
 * deselect event.
 */
export class DetailPanel {
  constructor(host, panel, onClosed) {
    this.host = host
    this.panel = panel
    this.heading = panel.querySelector("h3")
    this.content = panel.querySelector(".detail-content")
    this.onClosed = onClosed

    /* Returns the element focus goes back to, looked up at close time. */
    this._findOpener = null

    host.listen(panel.querySelector(".detail-close"), "click", () => {
      this.close(true)
    })

    host.listen(host.shadowRoot, "keydown", (event) => {
      if (event.key === "Escape" && this.isOpen === true) {
        event.preventDefault()
        this.close(true)
      }
    })
  }

  get isOpen() {
    const open = this.panel.hidden === false
    return open
  }

  /*
   * Show the panel. `title` is plain text, `contentMarkup` the result of the
   * `html` tag, `findOpener` a function returning the element to refocus.
   */
  open(title, contentMarkup, findOpener) {
    this.heading.textContent = title
    this.content.innerHTML = String(contentMarkup)
    this._findOpener = typeof findOpener === "function" ? findOpener : null
    this.panel.hidden = false
    this.panel.focus({ preventScroll: true })
    if (typeof this.panel.scrollIntoView === "function") {
      this.panel.scrollIntoView({ block: "nearest", inline: "nearest" })
    }
    return
  }

  /*
   * Hide the panel. Returns true when it was open. Focus is restored only
   * when asked and only if it is still inside the panel, so closing from
   * script never steals focus from elsewhere on the page.
   */
  close(restoreFocus) {
    const wasOpen = this.isOpen

    if (wasOpen === true) {
      const root = this.host.shadowRoot
      const active = root.activeElement
      const focusInside = active !== null && this.panel.contains(active) === true

      this.panel.hidden = true

      if (restoreFocus === true && focusInside === true && this._findOpener !== null) {
        const opener = this._findOpener()
        if (opener !== null && opener !== undefined) {
          opener.focus({ preventScroll: true })
        }
      }
      this._findOpener = null
      this.onClosed()
    }

    return wasOpen
  }
}

/*
 * Keep a "show data table / list" button and the region it controls in step
 * with `expanded`.
 */
export function syncDisclosure(button, region, expanded) {
  if (button !== null && button !== undefined) {
    button.setAttribute("aria-expanded", expanded === true ? "true" : "false")
  }
  if (region !== null && region !== undefined) {
    region.hidden = expanded === false
  }
  return
}

/*
 * Call `onWidthChange(width)` whenever the inline size of `element` changes
 * to a new non-zero value (a hidden element reports 0 and is skipped, so a
 * chart drawn inside a closed tab is laid out when the tab opens). The
 * observer is disconnected on teardown.
 */
export function observeWidth(host, element, onWidthChange) {
  if (typeof ResizeObserver !== "function") {
    return
  }

  let lastWidth = element.clientWidth
  let frame = 0

  const observer = new ResizeObserver(() => {
    const width = element.clientWidth
    if (width === 0 || width === lastWidth) {
      return
    }
    lastWidth = width
    if (frame !== 0) {
      window.cancelAnimationFrame(frame)
    }
    frame = window.requestAnimationFrame(() => {
      frame = 0
      onWidthChange(width)
    })
  })
  observer.observe(element)

  host.onTeardown(() => {
    observer.disconnect()
    if (frame !== 0) {
      window.cancelAnimationFrame(frame)
      frame = 0
    }
  })

  return
}

/* ----- data source and empty state ----- */

/*
 * Markup for the empty / loading / error block. The `empty` slot lets a page
 * supply its own message; the default slot shows the element's own children
 * (for example a server-rendered fallback table) until data arrives.
 */
export function emptyStateMarkup() {
  const noDataText = t("mj.pmChart.noData")

  const markup = html`
    <div class="empty-state" part="empty-state" role="status">
      <span class="empty-message"><slot name="empty">${noDataText}</slot></span>
      <slot></slot>
    </div>`
  return markup
}

/*
 * Show or hide the empty-state block. `state` is "ready" (hidden), "empty",
 * "loading", "error" or "no-match" (the chart has data but the user's
 * filters exclude all of it); `message` replaces the default text for the
 * last three.
 *
 * While declared data (`src` / inline JSON) is loading or after it failed,
 * a redraw that finds no data (a resize, an attribute change, navigation)
 * keeps showing "loading" / the error instead of "empty": the state of the
 * last load lives in `host._declaredStatus` (see loadDeclaredData).
 */
export function setEmptyState(host, state, message) {
  const block = host.shadowRoot.querySelector(".empty-state")
  if (block === null) {
    return
  }

  const declared = host._declaredStatus !== undefined ? host._declaredStatus : null
  if (state === "empty" && declared !== null) {
    state = declared.state
    message = declared.message
  }

  const messageHost = block.querySelector(".empty-message")
  const emptySlot = block.querySelector("slot[name='empty']")
  let statusText = block.querySelector(".empty-status")

  block.hidden = state === "ready"
  block.setAttribute("data-state", state)

  if (state === "loading" || state === "error" || state === "no-match") {
    if (statusText === null) {
      statusText = document.createElement("span")
      statusText.className = "empty-status"
      messageHost.appendChild(statusText)
    }
    statusText.textContent = message
    emptySlot.hidden = true
  } else {
    if (statusText !== null) {
      statusText.remove()
    }
    emptySlot.hidden = false
  }

  return
}

/*
 * Load data declared in markup when no `data` property was assigned: a `src`
 * attribute (fetched as JSON) or an inline <script type="application/json">
 * child. The result is assigned to `host.data`; a failure shows the error
 * state and emits `mj-error` with { message }.
 */
export function loadDeclaredData(host) {
  const src = host.getAttribute("src")
  const hasSrc = src !== null && src.trim().length > 0
  const inline = host.querySelector("script[type='application/json']")

  host._declaredStatus = null
  if (hasSrc === false && inline === null) {
    return
  }

  /* Each load supersedes the previous one: a stale answer is dropped. */
  const ticket = {}
  host._declaredTicket = ticket

  if (hasSrc === true) {
    host._declaredStatus = { state: "loading", message: t("core.loading") }
    setEmptyState(host, "loading", t("core.loading"))
  }

  /*
   * Non-object data (inline JSON "tasks", a number) is rejected by
   * resolveChartData and shown as an error, never drawn as an empty chart.
   */
  resolveChartData(host, null).then((loaded) => {
    if (host._declaredTicket !== ticket) {
      return
    }
    host._declaredStatus = null
    /* A `data` assignment made while the request was in flight wins. */
    if (loaded !== null && loaded !== undefined && host.data === null) {
      host.data = loaded
    } else if (host.data === null) {
      setEmptyState(host, "empty")
    }
  }).catch((error) => {
    if (host._declaredTicket !== ticket) {
      return
    }
    const message = error !== null && error !== undefined && error.message !== undefined ? error.message : t("mj.pmChart.loadError")
    if (host.data === null) {
      host._declaredStatus = { state: "error", message: message }
      setEmptyState(host, "error", message)
    }
    host.emit("mj-error", { message: message })
  })

  return
}

/* ----- base class ----- */

/*
 * Base class of the project-management charts.
 *
 * A subclass implements `drawChart()` -- a full, idempotent draw from
 * `this._data` that also handles null and empty data -- and calls
 * `setupChart()` at the end of `afterRender()`. The base class then owns:
 *   - the `data` property (assignment redraws, then `onDataDrawn()`);
 *   - data declared in markup (`src` attribute or inline JSON child);
 *   - redrawing for the component's own watched attributes only, so a
 *     `theme`, `hidden` or `dock` change does not rebuild the chart;
 *   - the "show data table / list" disclosure, whose state survives a
 *     reconnect because it lives in a field that `render()` reads;
 *   - redrawing when the observed element changes width.
 */
export class PmChartElement extends MjElement {
  static get observedAttributes() {
    const combined = [...this.coreAttributes, ...this.watched, "src"]
    return combined
  }

  constructor() {
    super()

    this._data = null

    /* True while the data table / accessible list is disclosed. */
    this._alternativeShown = false

    /* Key of the mark that holds the roving tab stop. */
    this._activeMarkKey = null

    /* True once afterRender() has collected the shadow references. */
    this._chartReady = false

    this._alternativeButton = null
    this._alternativeRegion = null

    /* The `src` value whose data has been requested. */
    this._declaredSrc = null

    /* { state: "loading" | "error", message } of declared data, or null. */
    this._declaredStatus = null
    this._declaredTicket = null
  }

  get data() {
    return this._data
  }

  set data(value) {
    this._data = value !== undefined ? value : null
    if (this._data !== null) {
      /* Assigned data replaces a pending or failed declared load. */
      this._declaredStatus = null
      this._declaredTicket = null
    }

    if (this._chartReady === true) {
      this.onDataChanged()
      this.drawChart()
      if (this._data !== null) {
        this.onDataDrawn()
      }
    }
    return
  }

  /* ----- hooks for subclasses ----- */

  /* Draw everything from `this._data`; must cope with null and empty data. */
  drawChart() { return }

  /* New data was assigned: drop state that referred to the old data. */
  onDataChanged() { return }

  /* Data was assigned and drawn: emit `mj-data-load` and the like. */
  onDataDrawn() { return }

  /* A watched attribute changed after the first render. */
  onChartAttributeChanged(name, oldValue, newValue) {
    this.drawChart()
    return
  }

  /* ----- helpers for subclasses ----- */

  /*
   * Finish `afterRender()`.
   *
   * options.alternativeButton  the disclosure button, or null
   * options.alternativeRegion  the table / list wrapper it controls
   * options.resizeTarget       element whose width the chart is laid out to
   */
  setupChart(options) {
    const opts = options || {}

    this._alternativeButton = opts.alternativeButton || null
    this._alternativeRegion = opts.alternativeRegion || null

    if (this._alternativeButton !== null) {
      this.listen(this._alternativeButton, "click", () => {
        this._alternativeShown = this._alternativeShown === false
        syncDisclosure(this._alternativeButton, this._alternativeRegion, this._alternativeShown)
      })
      syncDisclosure(this._alternativeButton, this._alternativeRegion, this._alternativeShown)
    }

    if (opts.resizeTarget !== null && opts.resizeTarget !== undefined) {
      observeWidth(this, opts.resizeTarget, () => {
        this.drawChart()
      })
    }

    this._declaredSrc = this.getAttribute("src")
    this._chartReady = true
    this.drawChart()

    if (this._data !== null) {
      this.onDataDrawn()
    } else {
      loadDeclaredData(this)
    }
    return
  }

  /*
   * Put `markup` into the stable <svg> element (its children are replaced;
   * the element, its `part` and its listeners stay), size it, restore the
   * roving tab stop and reflect the selection.
   */
  renderSvg(svg, width, height, markup, selectedKey) {
    svg.setAttribute("width", String(width))
    svg.setAttribute("height", String(height))
    svg.setAttribute("viewBox", `0 0 ${width} ${height}`)
    replaceMarkup(svg, markup)
    this._activeMarkKey = syncRovingMarks(svg, this._activeMarkKey)
    markSelection(svg, selectedKey !== undefined ? selectedKey : null)
    return
  }

  /* True for a boolean-like attribute: present and not "false". */
  flag(name) {
    const enabled = this.hasAttribute(name) === true && this.getAttribute(name) !== "false"
    return enabled
  }

  /* True unless the attribute is set to "false" (default-on switches). */
  enabledUnlessFalse(name) {
    const enabled = this.getAttribute(name) !== "false"
    return enabled
  }

  onAttributeChanged(name, oldValue, newValue) {
    if (this._chartReady === false) {
      return
    }

    if (name === "src") {
      /* The value present at render time was already loaded by setupChart(). */
      if (newValue !== this._declaredSrc) {
        this._declaredSrc = newValue
        this._data = null
        this.onDataChanged()
        this.drawChart()
        loadDeclaredData(this)
      }
      return
    }

    const watched = this.constructor.watched
    if (watched.indexOf(name) >= 0 && oldValue !== newValue) {
      this.onChartAttributeChanged(name, oldValue, newValue)
    }
    return
  }
}
