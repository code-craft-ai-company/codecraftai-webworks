/*
 * ohlc.js
 *
 * OHLC / Candlestick renderer.
 *
 * Registers: "ohlc", "candlestick"
 *
 * ctx.raw.candles: [{ t, o, h, l, c, v }]
 *   t — Date, epoch ms or ISO string ("YYYY-MM-DD" is a local day)
 *   o — open price
 *   h — high price
 *   l — low price
 *   c — close price
 *   v — volume (optional, not drawn here; see the "volume" type)
 * Numeric strings are accepted. A candle without a usable date is skipped;
 * one without usable prices keeps its slot but draws nothing.
 *
 * Drawing follows the type key: "ohlc" draws a vertical high-low line with
 * an open tick (left) and a close tick (right); "candlestick" draws a body
 * from open to close with wicks. The host's `variant` attribute
 * ("ohlc" | "candle") overrides it. Rising candles (close >= open) are
 * hollow, falling ones are filled, so direction is not shown by colour
 * alone.
 *
 * Candles sit in equal trading-session slots (no weekend gaps). The volume
 * renderer uses the same slots and margins, so a price chart and a volume
 * chart of the same data stacked at the same width line up. When there are
 * more candles than 3px slots, consecutive candles are merged (first open,
 * highest high, lowest low, last close, summed volume).
 *
 * Events:
 *   mj-chart-candle-click { t, o, h, l, c, direction, count }
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber, formatDate, parseDate } from "../svgdraw.js";
import { linearScale, niceTicks } from "../scales.js";


export const SESSION_MARGIN = { top: 16, right: 16, bottom: 32, left: 64 };
export const UP_COLOR = "var(--mj-color-success, #15803d)";
export const DOWN_COLOR = "var(--mj-color-danger, #b91c1c)";

const MIN_SLOT_PX = 3;
const MAX_BODY_PX = 24;
const DAY_MS = 86400000;


function _number(value) {
  /*
   * A finite number from a number or numeric string, else null.
   */
  if (value === null || value === undefined || value === "") {
    return null
  }
  const numeric = Number(value)
  const result = Number.isFinite(numeric) === true ? numeric : null
  return result
}


function _candleDate(value) {
  /*
   * A candle timestamp: Date, epoch ms (number or numeric string) or a
   * date string.
   */
  const numeric = typeof value === "string" && /^\d{10,}$/.test(value.trim()) ? Number(value) : null
  const date = numeric !== null ? new Date(numeric) : parseDate(value)
  return date
}


export function readCandles(raw) {
  /*
   * Parse raw.candles into session slots.
   *
   * :returns: [{ source, date, endDate, priced, o, h, l, c, v, count }]
   *     sorted by date; a value is null when missing or not numeric and
   *     `priced` is true when all four prices are usable.
   */
  const list = raw !== null && raw !== undefined && Array.isArray(raw.candles) === true
    ? raw.candles : []
  const sessions = []
  for (let index = 0; index < list.length; index = index + 1) {
    const candle = list[index]
    if (candle === null || typeof candle !== "object") {
      continue
    }
    const date = _candleDate(candle.t)
    if (date === null) {
      continue
    }
    const o = _number(candle.o)
    const c = _number(candle.c)
    let h = _number(candle.h)
    let l = _number(candle.l)
    const priced = o !== null && h !== null && l !== null && c !== null
    if (priced === true) {
      /* A high below the body or a low above it is widened to the body. */
      h = Math.max(h, o, c, l)
      l = Math.min(l, o, c, h)
    }
    sessions.push({
      source: candle, date: date, endDate: date, priced: priced,
      o: o, h: h, l: l, c: c, v: _number(candle.v), count: 1
    })
  }
  sessions.sort((a, b) => a.date.getTime() - b.date.getTime())
  return sessions
}


export function aggregateSessions(sessions, plotW) {
  /*
   * Merge consecutive sessions so that every slot is at least MIN_SLOT_PX
   * wide.
   *
   * :returns: The sessions themselves when they fit, else merged sessions.
   */
  const maxSlots = Math.max(Math.floor(plotW / MIN_SLOT_PX), 1)
  if (sessions.length <= maxSlots) {
    return sessions
  }
  const size = Math.ceil(sessions.length / maxSlots)
  const merged = []
  for (let start = 0; start < sessions.length; start = start + size) {
    const bucket = sessions.slice(start, start + size)
    const priced = bucket.filter((entry) => entry.priced === true)
    const opened = bucket.filter((entry) => entry.o !== null && entry.c !== null)
    let volume = null
    for (let b = 0; b < bucket.length; b = b + 1) {
      if (bucket[b].v !== null) {
        volume = (volume !== null ? volume : 0) + bucket[b].v
      }
    }
    merged.push({
      source: bucket[0].source,
      date: bucket[0].date,
      endDate: bucket[bucket.length - 1].date,
      priced: priced.length > 0,
      o: opened.length > 0 ? opened[0].o : null,
      h: priced.length > 0 ? priced.reduce((high, entry) => Math.max(high, entry.h), -Infinity) : null,
      l: priced.length > 0 ? priced.reduce((low, entry) => Math.min(low, entry.l), Infinity) : null,
      c: opened.length > 0 ? opened[opened.length - 1].c : null,
      v: volume,
      count: bucket.length
    })
  }
  return merged
}


export function sessionDateFormat(sessions) {
  /*
   * Date options suited to the time span of the sessions: times within a
   * day or two, month and day within a year, month and year beyond.
   */
  let options = { month: "short", day: "numeric" }
  if (sessions.length > 1) {
    const span = sessions[sessions.length - 1].date.getTime() - sessions[0].date.getTime()
    if (span < 2 * DAY_MS) {
      options = { hour: "2-digit", minute: "2-digit" }
    } else if (span > 300 * DAY_MS) {
      options = { month: "short", year: "numeric" }
    }
  }
  return options
}


export function sessionText(session) {
  /*
   * The date (or date range of a merged slot) of a session for tooltips.
   */
  const timed = session.date.getHours() !== 0 || session.date.getMinutes() !== 0
  const options = timed === true ? { dateStyle: "medium", timeStyle: "short" } : { dateStyle: "medium" }
  let text = formatDate(session.date, options)
  if (session.count > 1) {
    text = `${text} – ${formatDate(session.endDate, options)} (${session.count} sessions)`
  }
  return text
}


export function drawSessionAxis(group, sessions, slotW, plotW, plotH) {
  /*
   * Time labels under the plot: about one per 70px, placed on slot centres.
   */
  const options = sessionDateFormat(sessions)
  const maxLabels = Math.max(Math.floor(plotW / 70), 1)
  const every = Math.max(1, Math.ceil(sessions.length / maxLabels))
  for (let index = 0; index < sessions.length; index = index + every) {
    const cx = (index + 0.5) * slotW
    group.appendChild(svgEl("line", {
      x1: cx, y1: plotH, x2: cx, y2: plotH + 4,
      stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1
    }, []))
    group.appendChild(svgEl("text", {
      x: cx, y: plotH + 16, "text-anchor": "middle",
      "font-size": 10, fill: "var(--mj-text-muted, #6b7280)"
    }, formatDate(sessions[index].date, options)))
  }
  return
}


function _sessionsTable(sessions) {
  /*
   * The accessible table of the (unmerged) sessions.
   */
  const table = {
    columns: ["Date", "Open", "High", "Low", "Close", "Volume"],
    rows: sessions.map((entry) => [
      sessionText(entry),
      entry.o !== null ? entry.o : "", entry.h !== null ? entry.h : "",
      entry.l !== null ? entry.l : "", entry.c !== null ? entry.c : "",
      entry.v !== null ? entry.v : ""
    ])
  }
  return table
}


export function render(ctx) {
  /*
   * Render an OHLC or candlestick chart.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const variant = ctx.attrs("style", "")
  let tickMode = ctx.type === "ohlc"
  if (variant === "ohlc") {
    tickMode = true
  } else if (variant === "candle" || variant === "candlestick") {
    tickMode = false
  }

  const root = svgEl("g", { part: "plot" }, [])

  const allSessions = readCandles(ctx.raw)
  ctx.setTable(_sessionsTable(allSessions))
  ctx.setLegend([
    { label: tickMode === true ? "Close ≥ open" : "Close ≥ open (hollow)", color: UP_COLOR },
    { label: tickMode === true ? "Close < open" : "Close < open (filled)", color: DOWN_COLOR }
  ])

  const margin = SESSION_MARGIN
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)
  const sessions = aggregateSessions(allSessions, plotW)

  /* Price domain. */
  let priceMin = Infinity
  let priceMax = -Infinity
  for (let index = 0; index < sessions.length; index = index + 1) {
    if (sessions[index].priced === false) {
      continue
    }
    priceMin = Math.min(priceMin, sessions[index].l)
    priceMax = Math.max(priceMax, sessions[index].h)
  }
  if (priceMin === Infinity) {
    return root
  }
  const pricePad = priceMax > priceMin ? (priceMax - priceMin) * 0.05 : Math.max(Math.abs(priceMax) * 0.05, 1)
  priceMin = priceMin - pricePad
  priceMax = priceMax + pricePad

  const priceScale = linearScale([priceMin, priceMax], [plotH, 0])
  const slotW = plotW / sessions.length
  const bodyW = Math.min(Math.max(slotW * 0.6, 1), MAX_BODY_PX)
  const halfBody = bodyW / 2
  const strokeW = slotW < 4 ? 1 : 1.5

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)
  const axis = svgEl("g", { "aria-hidden": "true" }, [])
  const marks = svgEl("g", null, [])
  plot.appendChild(axis)
  plot.appendChild(marks)

  const ticks = niceTicks(priceMin, priceMax, 5)
  for (let t = 0; t < ticks.length; t = t + 1) {
    const y = priceScale(ticks[t])
    axis.appendChild(svgEl("line", {
      x1: 0, y1: y, x2: plotW, y2: y,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    axis.appendChild(svgEl("text", {
      x: -8, y: y + 4, "text-anchor": "end",
      "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
    }, formatNumber(ticks[t])))
  }
  drawSessionAxis(axis, sessions, slotW, plotW, plotH)
  axis.appendChild(svgEl("line", {
    x1: 0, y1: plotH, x2: plotW, y2: plotH,
    stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
  }, []))
  axis.appendChild(svgEl("line", {
    x1: 0, y1: 0, x2: 0, y2: plotH,
    stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
  }, []))

  for (let index = 0; index < sessions.length; index = index + 1) {
    const session = sessions[index]
    if (session.priced === false) {
      continue
    }
    const cx = (index + 0.5) * slotW
    const yHigh = priceScale(session.h)
    const yLow = priceScale(session.l)
    const yOpen = priceScale(session.o)
    const yClose = priceScale(session.c)

    const rising = session.c >= session.o
    const color = rising === true ? UP_COLOR : DOWN_COLOR
    const direction = rising === true ? "rising" : "falling"
    const label = `${sessionText(session)}, ${direction}: open ${formatNumber(session.o)}, ` +
      `high ${formatNumber(session.h)}, low ${formatNumber(session.l)}, close ${formatNumber(session.c)}`

    const group = svgEl("g", {
      part: "candle", tabindex: "0", role: "img", "aria-label": label
    }, [])
    group.appendChild(svgEl("title", null, label))

    if (tickMode === true) {
      group.appendChild(svgEl("line", {
        x1: cx, y1: yHigh, x2: cx, y2: yLow, stroke: color, "stroke-width": strokeW
      }, []))
      group.appendChild(svgEl("line", {
        x1: cx - halfBody, y1: yOpen, x2: cx, y2: yOpen, stroke: color, "stroke-width": strokeW
      }, []))
      group.appendChild(svgEl("line", {
        x1: cx, y1: yClose, x2: cx + halfBody, y2: yClose, stroke: color, "stroke-width": strokeW
      }, []))
    } else {
      const bodyTop = Math.min(yOpen, yClose)
      const bodyBot = Math.max(yOpen, yClose)
      group.appendChild(svgEl("line", {
        x1: cx, y1: yHigh, x2: cx, y2: bodyTop, stroke: color, "stroke-width": strokeW
      }, []))
      group.appendChild(svgEl("line", {
        x1: cx, y1: bodyBot, x2: cx, y2: yLow, stroke: color, "stroke-width": strokeW
      }, []))
      group.appendChild(svgEl("rect", {
        x: cx - halfBody, y: bodyTop,
        width: bodyW, height: Math.max(bodyBot - bodyTop, 1),
        fill: rising === true ? "var(--mj-surface, #ffffff)" : color,
        stroke: color, "stroke-width": strokeW
      }, []))
    }

    const emitSession = session
    const handler = () => {
      ctx.emit("mj-chart-candle-click", {
        t: emitSession.source.t, o: emitSession.o, h: emitSession.h, l: emitSession.l,
        c: emitSession.c, direction: direction, count: emitSession.count
      })
    }
    group.addEventListener("click", handler)
    group.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault()
        handler()
      }
    })
    marks.appendChild(group)
  }

  return root
}


registerRenderer("ohlc", render)
registerRenderer("candlestick", render)
