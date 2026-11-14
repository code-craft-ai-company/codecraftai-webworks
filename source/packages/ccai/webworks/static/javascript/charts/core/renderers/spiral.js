/*
 * spiral.js
 *
 * Spiral chart renderer — maps time series data onto an Archimedean spiral
 * so that repeating cycles (day / week / year) align radially: every turn is
 * one cycle, and the same phase of every cycle (every Monday, every 9 am,
 * every March) lies on the same spoke.
 *
 * Registered types:
 *   "spiral"
 *
 * ctx.raw shape:
 *   raw.cycle   "week" (default) | "year" | "day"
 *   raw.series  [{name, points:[{t, value}]}]
 *               t: Date, epoch ms, ISO string or YYYY-MM-DD (a local day);
 *               points whose t is not a date are skipped; a null value is a
 *               gap in the line.
 *
 * Angle = the timestamp's phase within its cycle in the viewer's LOCAL time
 * zone: time of day (day), Monday-based day of week plus time of day
 * (week), day of the year with leap years and real month lengths (year).
 * The spoke labels sit at those phases (month spokes at each month's first
 * day). The turn is the number of cycles since the first point's cycle, so
 * less than a cycle of data covers only part of a turn.
 *
 * Radius = r0 + band * (turn + phase); the value adds an offset of up to
 * 70% of a band OUTWARD from that base spiral, measured from zero (so 0 is on
 * the base spiral, drawn as a thin guide), and the outermost turn plus its
 * offset stays inside the spoke labels.
 *
 * Attribute `mode`: "line" (default; a line plus a focusable point per
 * observation) | "bar" (a radial bar per observation, from the base spiral).
 *
 * Interaction: points / bars emit `mj-chart-bar-click` { series, t, value }
 * (bar mode) or `mj-chart-point-click` { series, t, value } (line mode).
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, linePath, formatNumber, formatDate, parseDate } from "../svgdraw.js";

const DAY_MS = 24 * 60 * 60 * 1000
const OFFSET_SHARE = 0.7
const LABEL_SPACE = 20
const MAX_POINT_MARKS = 600


function _dayOfYear(date) {
  /*
   * Zero-based local day of the year.
   */
  const start = new Date(date.getFullYear(), 0, 1)
  const days = Math.round((new Date(date.getFullYear(), date.getMonth(), date.getDate()) - start) / DAY_MS)
  return days
}


function _daysInYear(year) {
  /*
   * 365 or 366.
   */
  const leap = (year % 4 === 0 && year % 100 !== 0) || year % 400 === 0
  return leap === true ? 366 : 365
}


function _timeOfDay(date) {
  /*
   * Fraction of the local day that has passed.
   */
  const seconds = date.getHours() * 3600 + date.getMinutes() * 60 + date.getSeconds() +
    date.getMilliseconds() / 1000
  return seconds / 86400
}


function _cycleStart(date, cycle) {
  /*
   * Local start of the cycle containing a date.
   */
  if (cycle === "day") {
    return new Date(date.getFullYear(), date.getMonth(), date.getDate())
  }
  if (cycle === "year") {
    return new Date(date.getFullYear(), 0, 1)
  }
  const mondayOffset = (date.getDay() + 6) % 7
  return new Date(date.getFullYear(), date.getMonth(), date.getDate() - mondayOffset)
}


function _phase(date, cycle) {
  /*
   * Position of a date within its cycle, in [0, 1).
   */
  if (cycle === "day") {
    return _timeOfDay(date)
  }
  if (cycle === "year") {
    return (_dayOfYear(date) + _timeOfDay(date)) / _daysInYear(date.getFullYear())
  }
  return (((date.getDay() + 6) % 7) + _timeOfDay(date)) / 7
}


function _cycleIndex(date, first, cycle) {
  /*
   * Whole cycles between the first point's cycle and a date's cycle.
   */
  if (cycle === "year") {
    return date.getFullYear() - first.getFullYear()
  }
  const days = Math.round((_cycleStart(date, cycle) - _cycleStart(first, cycle)) / DAY_MS)
  return cycle === "day" ? days : Math.round(days / 7)
}


function _spokes(cycle) {
  /*
   * Spoke labels and their phases for a cycle, in the library locale.
   *
   * :returns: [{ phase, label }].
   */
  const spokes = []
  if (cycle === "day") {
    for (let hour = 0; hour < 24; hour = hour + 3) {
      spokes.push({ phase: hour / 24, label: formatDate(new Date(2024, 0, 1, hour), { hour: "numeric" }) })
    }
  } else if (cycle === "year") {
    /* A common (non-leap) year places the month starts. */
    for (let month = 0; month < 12; month = month + 1) {
      const first = new Date(2023, month, 1)
      spokes.push({ phase: _dayOfYear(first) / 365, label: formatDate(first, { month: "short" }) })
    }
  } else {
    /* 2024-01-01 is a Monday. */
    for (let day = 0; day < 7; day = day + 1) {
      spokes.push({ phase: day / 7, label: formatDate(new Date(2024, 0, 1 + day), { weekday: "short" }) })
    }
  }
  return spokes
}


export function render(ctx) {
  /*
   * Render a spiral chart.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const raw = ctx.raw !== null && ctx.raw !== undefined ? ctx.raw : {}
  const root = svgEl("g", { part: "plot" }, [])
  const series = ctx.model.series
  const cycle = raw.cycle === "day" || raw.cycle === "year" ? raw.cycle : "week"
  const mode = ctx.attrs("mode", "line") === "bar" ? "bar" : "line"

  /* Valid points per series, sorted by time. */
  const prepared = []
  let first = null
  let maxAbs = 0
  for (let s = 0; s < series.length; s = s + 1) {
    const list = Array.isArray(series[s].points) === true ? series[s].points : []
    const points = []
    for (let p = 0; p < list.length; p = p + 1) {
      const entry = list[p]
      if (entry === null || typeof entry !== "object") {
        continue
      }
      const date = parseDate(entry.t)
      if (date === null) {
        continue
      }
      const value = typeof entry.value === "number" && Number.isFinite(entry.value) === true
        ? entry.value
        : null
      points.push({ date: date, value: value, source: entry })
      if (first === null || date < first) {
        first = date
      }
      if (value !== null) {
        maxAbs = Math.max(maxAbs, Math.abs(value))
      }
    }
    points.sort((a, b) => a.date - b.date)
    prepared.push({ name: series[s].name, points: points })
  }

  const tableRows = []
  const dayCycle = cycle === "day"
  prepared.forEach((entry) => {
    entry.points.forEach((point) => {
      tableRows.push([
        formatDate(point.date, dayCycle === true ? { dateStyle: "medium", timeStyle: "short" } : undefined),
        entry.name,
        point.value
      ])
    })
  })
  ctx.setTable({ columns: ["Time", "Series", "Value"], rows: tableRows, caption: ctx.label })

  if (first === null) {
    return root
  }

  /* Turn + phase of every point. */
  let lastTurn = 0
  prepared.forEach((entry) => {
    entry.points.forEach((point) => {
      point.turn = _cycleIndex(point.date, first, cycle)
      point.phase = _phase(point.date, cycle)
      lastTurn = Math.max(lastTurn, point.turn)
    })
  })

  const cx = ctx.width / 2
  const cy = ctx.height / 2
  const maxR = Math.max(Math.min(cx, cy) - LABEL_SPACE, 10)
  const r0 = maxR * 0.12
  const turns = lastTurn + 1
  const band = (maxR - r0) / (turns + OFFSET_SHARE)
  const offsetMax = band * OFFSET_SHARE
  const offsetOf = (value) => (maxAbs > 0 && value !== null ? (value / maxAbs) * offsetMax : 0)
  const baseRadius = (progress) => r0 + band * progress

  const at = (progress, extra) => {
    const angle = progress * 2 * Math.PI - Math.PI / 2
    const radius = baseRadius(progress) + extra
    return { x: cx + radius * Math.cos(angle), y: cy + radius * Math.sin(angle) }
  }

  /* Spokes, labels and the base spiral (decoration). */
  const decor = svgEl("g", { "aria-hidden": "true" }, [])
  root.appendChild(decor)
  const spokes = _spokes(cycle)
  for (let k = 0; k < spokes.length; k = k + 1) {
    const angle = spokes[k].phase * 2 * Math.PI - Math.PI / 2
    decor.appendChild(svgEl("line", {
      x1: cx, y1: cy,
      x2: (cx + maxR * Math.cos(angle)).toFixed(2), y2: (cy + maxR * Math.sin(angle)).toFixed(2),
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 0.75
    }, []))
    decor.appendChild(svgEl("text", {
      x: (cx + (maxR + 10) * Math.cos(angle)).toFixed(2),
      y: (cy + (maxR + 10) * Math.sin(angle)).toFixed(2),
      "text-anchor": "middle", "dominant-baseline": "middle", "font-size": 9,
      fill: "var(--mj-text-muted, #5f6673)"
    }, spokes[k].label))
  }
  const guide = []
  const startProgress = 0
  const endProgress = turns
  const guideSteps = Math.max(Math.ceil((endProgress - startProgress) * 72), 2)
  for (let g = 0; g <= guideSteps; g = g + 1) {
    guide.push(at(startProgress + (endProgress - startProgress) * g / guideSteps, 0))
  }
  decor.appendChild(svgEl("path", {
    d: linePath(guide), fill: "none", stroke: "var(--mj-border-strong, #878e9c)",
    "stroke-width": 0.75, "stroke-opacity": 0.6, part: "spiral-guide"
  }, []))

  /* Series. */
  for (let s = 0; s < prepared.length; s = s + 1) {
    const entry = prepared[s]
    const color = ctx.colorFor(entry.name)
    const group = svgEl("g", { part: "series" }, [])
    root.appendChild(group)

    if (mode === "line") {
      const points = entry.points.map((point) => {
        return point.value === null ? null : at(point.turn + point.phase, offsetOf(point.value))
      })
      group.appendChild(svgEl("path", {
        d: linePath(points), fill: "none", stroke: color, "stroke-width": 2,
        "stroke-linecap": "round", "stroke-linejoin": "round", part: "line", "aria-hidden": "true"
      }, []))
    }

    const marks = entry.points.length <= MAX_POINT_MARKS
    for (let p = 0; p < entry.points.length; p = p + 1) {
      const point = entry.points[p]
      if (point.value === null) {
        continue
      }
      const progress = point.turn + point.phase
      const label = `${entry.name}, ${formatDate(point.date, dayCycle === true
        ? { dateStyle: "medium", timeStyle: "short" }
        : undefined)}: ${formatNumber(point.value)}`
      let mark = null
      if (mode === "bar") {
        if (point.value === 0) {
          continue
        }
        const from = at(progress, 0)
        const to = at(progress, offsetOf(point.value))
        mark = svgEl("line", {
          x1: from.x.toFixed(2), y1: from.y.toFixed(2), x2: to.x.toFixed(2), y2: to.y.toFixed(2),
          stroke: color, "stroke-width": Math.max(Math.min(band * 0.12, 4), 1.5),
          "stroke-linecap": "butt", part: "bar"
        }, [])
      } else if (marks === true) {
        const spot = at(progress, offsetOf(point.value))
        mark = svgEl("circle", {
          cx: spot.x.toFixed(2), cy: spot.y.toFixed(2), r: 2.5, fill: color, part: "point"
        }, [])
      }
      if (mark === null) {
        continue
      }
      mark.setAttribute("tabindex", "0")
      mark.setAttribute("role", "img")
      mark.setAttribute("aria-label", label)
      mark.appendChild(svgEl("title", null, label))
      const capturedName = entry.name
      const captured = point.source
      const eventName = mode === "bar" ? "mj-chart-bar-click" : "mj-chart-point-click"
      const handler = () => {
        ctx.emit(eventName, { series: capturedName, t: captured.t, value: captured.value })
      }
      mark.addEventListener("click", handler)
      mark.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault()
          handler()
        }
      })
      group.appendChild(mark)
    }
  }

  return root
}


registerRenderer("spiral", render)
