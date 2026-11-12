/*
 * line.js
 *
 * Line / multi-line renderer. It also exports the trend toolkit the other
 * time-series renderers share (area, step, sparkline, horizon, streamgraph,
 * bump): reading series as x / y points, choosing the x scale, laying out
 * the plot and its axes, building curves and placing focusable targets.
 *
 * Registered types:
 *   "line"      — single-series or multi-series line chart
 *   "multiline" — alias for "line"; any number of series
 *
 * ctx.attrs recognised:
 *   curve          "linear" (default) | "monotone" | "step" — path
 *                  interpolation; monotone never overshoots the data, step
 *                  holds each value until the next x; other values: linear
 *   show-points    boolean (default false) — dot markers on every point;
 *                  a point without a neighbour always gets a marker
 *   x-scale        "auto" (default) | "time" | "linear" | "category"
 *
 * Series data may use either:
 *   series[].points  [{x, y}, ...]  (time, numeric or categorical x)
 *   series[].values  [...]          (index-aligned with model.categories)
 *
 * X scale (x-scale="auto"): ISO dates ("2025", "2025-01", "2025-01-15",
 * "2025-01-15T10:30Z") and epoch milliseconds use a time scale, other
 * numbers a linear scale, anything else a categorical point scale. Points
 * are drawn in x order whatever their order in the data. Categorical x
 * follows model.categories, then the order the series give; a label
 * repeated inside one series is a new position. A null y is a gap.
 */

import { registerRenderer } from "../renderregistry.js";
import {
  svgEl, formatNumber, formatDate, parseDate, linePath, monotonePath
} from "../svgdraw.js";
import { linearScale, timeScale, pointScale, niceTicks, niceDomain } from "../scales.js";
import {
  LABEL_FONT_SIZE, textWidth, truncateText, numericValue,
  tickFormatter, activate
} from "./bar.js";
import { booleanOption } from "../chartoptions.js";

/* Epoch milliseconds at or above this (March 1973) read as instants. */
const EPOCH_MS_FLOOR = 1e11;

const ISO_DATE_PATTERN =
  /^(\d{4})(?:-(\d{2})(?:-(\d{2})(?:[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?)?)?)?$/;

/* Separates a label from its occurrence count in a categorical key. */
const KEY_SEPARATOR = "\u0000";


function _timeValue(raw) {
  /*
   * Epoch milliseconds of an x value, or null when it is not a date.
   * "YYYY" and "YYYY-MM" are the first local day of that year / month.
   */
  if (raw instanceof Date) {
    const time = raw.getTime()
    return Number.isFinite(time) === true ? time : null
  }
  if (typeof raw === "number") {
    return Number.isFinite(raw) === true ? raw : null
  }
  if (typeof raw !== "string") {
    return null
  }
  const text = raw.trim()
  const match = ISO_DATE_PATTERN.exec(text)
  if (match === null) {
    return null
  }
  let date = null
  if (match[2] === undefined) {
    date = new Date(Number(match[1]), 0, 1)
  } else if (match[3] === undefined) {
    date = new Date(Number(match[1]), Number(match[2]) - 1, 1)
  } else {
    date = parseDate(text)
  }
  const time = date !== null ? date.getTime() : NaN
  return Number.isFinite(time) === true ? time : null
}


export function trendSeries(model) {
  /*
   * Read every visible series as a list of points.
   *
   * :param model: The chart model.
   * :returns: [{ name, points: [{ raw, y, index }] }] where `raw` is the x
   *     value as given (null for values without a category), `y` a number
   *     or null (a gap) and `index` the point's position in the data.
   */
  const result = []
  for (let s = 0; s < model.series.length; s = s + 1) {
    const entry = model.series[s]
    const points = []
    if (entry.points.length > 0) {
      for (let p = 0; p < entry.points.length; p = p + 1) {
        const point = entry.points[p]
        if (point === null || typeof point !== "object") {
          continue
        }
        const raw = point.x !== undefined ? point.x : null
        points.push({ raw: raw, y: numericValue(point.y), index: p, valued: false })
      }
    } else {
      for (let v = 0; v < entry.values.length; v = v + 1) {
        const category = model.categories[v]
        const raw = category !== undefined ? category : null
        points.push({ raw: raw, y: numericValue(entry.values[v]), index: v, valued: true })
      }
    }
    result.push({ name: entry.name, points: points })
  }
  return result
}


function _xKind(ctx, list, defaultScale) {
  /*
   * Decide the x scale: "time", "linear" or "category" (see the header).
   *
   * :param ctx: The renderer context.
   * :param list: Output of trendSeries.
   * :param defaultScale: The x-scale used when the attribute is absent
   *     ("auto" unless the renderer says otherwise; bump uses "category").
   */
  const fallback = typeof defaultScale === "string" ? defaultScale : "auto"
  const forced = String(ctx.attrs("x-scale", fallback)).trim().toLowerCase()

  let total = 0
  let numbers = 0
  let instants = 0
  let dates = 0
  for (let s = 0; s < list.length; s = s + 1) {
    const points = list[s].points
    for (let p = 0; p < points.length; p = p + 1) {
      const raw = points[p].raw
      if (raw === null || raw === undefined) {
        continue
      }
      total = total + 1
      if (typeof raw === "number" && Number.isFinite(raw) === true) {
        numbers = numbers + 1
        if (Math.abs(raw) >= EPOCH_MS_FLOOR) {
          instants = instants + 1
        }
      } else if (_timeValue(raw) !== null) {
        dates = dates + 1
      }
    }
  }

  let kind = "category"
  if (total === 0) {
    kind = "category"
  } else if (forced === "category" || forced === "point" || forced === "band") {
    kind = "category"
  } else if (forced === "time") {
    kind = numbers + dates === total ? "time" : "category"
  } else if (forced === "linear") {
    kind = numbers === total ? "linear" : "category"
  } else if (numbers === total) {
    kind = instants === total ? "time" : "linear"
  } else if (dates === total) {
    kind = "time"
  }
  return kind
}


function _categoryKeys(list, model) {
  /*
   * Give every categorical point a key and order the keys: the model's
   * categories first, then each series' labels merged in after the label
   * that precedes them in that series. The n-th occurrence of a label in a
   * series is its own key, so repeated labels do not fold the line back.
   *
   * :returns: { order: [key], labels: Map key -> text, keyOf: Map point -> key }
   */
  const order = []
  const labels = new Map()
  const keyOf = new Map()

  const valuesMode = list.length > 0 && list.every((entry) => entry.points.every((pt) => pt.valued === true))
  if (valuesMode === true) {
    /* values + categories: position by index, so duplicates keep their slot. */
    let longest = model.categories.length
    for (let s = 0; s < list.length; s = s + 1) {
      longest = Math.max(longest, list[s].points.length)
      for (let p = 0; p < list[s].points.length; p = p + 1) {
        keyOf.set(list[s].points[p], `#${list[s].points[p].index}`)
      }
    }
    for (let index = 0; index < longest; index = index + 1) {
      const category = model.categories[index]
      order.push(`#${index}`)
      labels.set(`#${index}`, category !== undefined && category !== null ? String(category) : String(index + 1))
    }
    return { order: order, labels: labels, keyOf: keyOf }
  }

  const position = new Map()
  const reindex = () => {
    position.clear()
    for (let index = 0; index < order.length; index = index + 1) {
      position.set(order[index], index)
    }
  }
  const counts = new Map()
  for (let index = 0; index < model.categories.length; index = index + 1) {
    const label = String(model.categories[index])
    const seen = counts.has(label) === true ? counts.get(label) : 0
    counts.set(label, seen + 1)
    const key = `${label}${KEY_SEPARATOR}${seen}`
    order.push(key)
    labels.set(key, label)
  }
  reindex()

  for (let s = 0; s < list.length; s = s + 1) {
    const seriesCounts = new Map()
    let cursor = -1
    const points = list[s].points
    for (let p = 0; p < points.length; p = p + 1) {
      const point = points[p]
      const label = point.raw === null || point.raw === undefined ? String(point.index + 1) : String(point.raw)
      const seen = seriesCounts.has(label) === true ? seriesCounts.get(label) : 0
      seriesCounts.set(label, seen + 1)
      const key = `${label}${KEY_SEPARATOR}${seen}`
      keyOf.set(point, key)
      if (position.has(key) === true) {
        cursor = position.get(key)
        continue
      }
      const at = cursor + 1
      order.splice(at, 0, key)
      labels.set(key, label)
      if (at === order.length - 1) {
        position.set(key, at)
      } else {
        reindex()
      }
      cursor = at
    }
  }
  return { order: order, labels: labels, keyOf: keyOf }
}


export function resolveXAxis(ctx, list, model, range, options) {
  /*
   * Build the x axis of a trend chart.
   *
   * :param ctx: The renderer context.
   * :param list: Output of trendSeries.
   * :param model: The chart model.
   * :param range: [start, end] pixels.
   * :param options: { extendEnd: true to add one median step after the
   *     last x (a step chart's final tread); xScale: the x-scale used
   *     when the attribute is absent (default "auto") }.
   * :returns: {
   *     kind:      "time" | "linear" | "category",
   *     position:  (point) -> px, or null for a point that cannot be placed,
   *     keyOf:     (point) -> a key shared by points at the same x,
   *     keys:      every key in x order, as [{ key, px, label }],
   *     end:       the px of the domain end (the extended end if any),
   *     ticks:     (count) -> [{ px, label }] axis labels,
   *     labelOf:   (point) -> readable x text for labels and events
   *   }
   */
  const settings = options !== null && options !== undefined ? options : {}
  const kind = _xKind(ctx, list, settings.xScale)
  const start = range[0]
  const finish = range[1]

  if (kind === "category") {
    const keys = _categoryKeys(list, model)
    const slots = keys.order.length + (settings.extendEnd === true ? 1 : 0)
    const slotNames = keys.order.slice()
    if (settings.extendEnd === true) {
      slotNames.push(`${KEY_SEPARATOR}end`)
    }
    const scale = pointScale(slotNames, [start, finish])
    const indexOf = new Map()
    for (let index = 0; index < keys.order.length; index = index + 1) {
      indexOf.set(keys.order[index], index)
    }
    const keyFor = (point) => {
      const key = keys.keyOf.get(point)
      return key !== undefined ? key : null
    }
    const position = (point) => {
      const key = keyFor(point)
      return key !== null && indexOf.has(key) === true ? scale.at(indexOf.get(key)) : null
    }
    const sortedKeys = keys.order.map((key, index) => ({ key: key, px: scale.at(index), label: keys.labels.get(key) }))
    const ticks = () => {
      let widest = 0
      for (let index = 0; index < sortedKeys.length; index = index + 1) {
        widest = Math.max(widest, textWidth(sortedKeys[index].label))
      }
      const step = slots > 1 ? Math.abs(scale.step()) : Math.abs(finish - start)
      const every = Math.max(1, Math.ceil((Math.min(widest, 120) + 10) / Math.max(step, 1)))
      const shown = []
      for (let index = 0; index < sortedKeys.length; index = index + every) {
        shown.push({
          px: sortedKeys[index].px,
          label: truncateText(sortedKeys[index].label, step * every - 6)
        })
      }
      return shown
    }
    const axis = {
      kind: kind,
      position: position,
      keyOf: keyFor,
      keys: sortedKeys,
      end: settings.extendEnd === true ? scale.at(slots - 1) : finish,
      ticks: ticks,
      labelOf: (point) => {
        const key = keyFor(point)
        return key !== null ? keys.labels.get(key) : ""
      }
    }
    return axis
  }

  /* Continuous x: time or linear. */
  const valueOf = (point) => {
    if (point.raw === null || point.raw === undefined) {
      return null
    }
    return kind === "time" ? _timeValue(point.raw) : numericValue(point.raw)
  }
  const distinct = new Map()
  for (let s = 0; s < list.length; s = s + 1) {
    for (let p = 0; p < list[s].points.length; p = p + 1) {
      const value = valueOf(list[s].points[p])
      if (value !== null && distinct.has(value) === false) {
        distinct.set(value, list[s].points[p])
      }
    }
  }
  const values = Array.from(distinct.keys()).sort((a, b) => a - b)
  let low = values.length > 0 ? values[0] : 0
  let high = values.length > 0 ? values[values.length - 1] : 1
  if (settings.extendEnd === true && values.length > 1) {
    const gaps = []
    for (let index = 1; index < values.length; index = index + 1) {
      gaps.push(values[index] - values[index - 1])
    }
    gaps.sort((a, b) => a - b)
    high = high + gaps[Math.floor(gaps.length / 2)]
  }
  if (low === high) {
    /* One x value: centre it. */
    const pad = kind === "time" ? 12 * 3600 * 1000 : Math.max(1, Math.abs(low) * 0.1)
    low = low - pad
    high = high + pad
  }

  const scale = kind === "time" ? timeScale([low, high], [start, finish]) : linearScale([low, high], [start, finish])
  const pixelOf = (value) => scale(kind === "time" ? new Date(value) : value)
  const position = (point) => {
    const value = valueOf(point)
    return value !== null ? pixelOf(value) : null
  }

  const describe = (value, point) => {
    if (point !== undefined && point !== null && typeof point.raw === "string") {
      return point.raw
    }
    if (kind === "time") {
      const date = new Date(value)
      const midnight = date.getHours() === 0 && date.getMinutes() === 0 && date.getSeconds() === 0
      return formatDate(date, midnight === true ? { dateStyle: "medium" } : { dateStyle: "medium", timeStyle: "short" })
    }
    return formatNumber(value)
  }

  const ticks = (count) => {
    const wanted = Math.max(2, count)
    let tickValues = []
    let format = null
    if (kind === "time") {
      tickValues = scale.ticks(wanted).map((date) => date.getTime())
      const formatter = scale.tickFormat(wanted)
      format = (value) => formatter(new Date(value))
    } else {
      tickValues = niceTicks(low, high, wanted)
      format = (value) => formatNumber(value)
    }
    const shown = tickValues.map((value) => ({ px: pixelOf(value), label: format(value) }))
    return shown
  }

  const axis = {
    kind: kind,
    position: position,
    keyOf: (point) => valueOf(point),
    keys: values.map((value) => ({ key: value, px: pixelOf(value), label: describe(value, distinct.get(value)) })),
    end: pixelOf(high),
    ticks: ticks,
    labelOf: (point) => {
      const value = valueOf(point)
      return value !== null ? describe(value, point) : ""
    }
  }
  return axis
}


function _fits(ticks, fontSize) {
  /*
   * True when no two neighbouring tick labels overlap.
   */
  for (let index = 1; index < ticks.length; index = index + 1) {
    const room = Math.abs(ticks[index].px - ticks[index - 1].px)
    const needed = (textWidth(ticks[index].label, fontSize) + textWidth(ticks[index - 1].label, fontSize)) / 2 + 8
    if (needed > room) {
      return false
    }
  }
  return true
}


export function axisTicks(axis, plotW, fontSize) {
  /*
   * The x-axis labels: calendar / nice ticks with fewer ticks until their
   * labels do not overlap. When that leaves fewer than two labels (a few
   * yearly points can round to a single 5-year tick) finer intervals are
   * tried, and failing that the data's own x positions are labelled,
   * thinned to fit.
   *
   * :param axis: An axis from resolveXAxis.
   * :param plotW: The plot width in px.
   * :param fontSize: The label font size.
   * :returns: [{ px, label }].
   */
  if (axis.kind === "category") {
    return axis.ticks(0)
  }
  let count = Math.max(2, Math.floor(plotW / 90))
  let ticks = axis.ticks(count)
  while (count > 2 && _fits(ticks, fontSize) === false) {
    count = count - 1
    ticks = axis.ticks(count)
  }
  /* A coarse interval can leave a single tick: ask for finer ones. */
  for (let finer = count + 1; ticks.length < 2 && finer <= count + 6; finer = finer + 1) {
    const candidate = axis.ticks(finer)
    if (candidate.length >= 2 && _fits(candidate, fontSize) === true) {
      ticks = candidate
    }
  }
  if (ticks.length < 2 && axis.keys.length > 1) {
    for (let every = 1; every <= axis.keys.length; every = every + 1) {
      const sampled = axis.keys.filter((key, index) => index % every === 0)
      if (_fits(sampled, fontSize) === true) {
        ticks = sampled.map((key) => ({ px: key.px, label: key.label }))
        break
      }
    }
  }
  return ticks
}


export function trendFrame(ctx, list, model, options) {
  /*
   * Lay out a trend chart: a value axis on the left sized from its measured
   * tick labels, an x axis along the bottom whose labels never leave the
   * drawing, gridlines and labels in an aria-hidden group.
   *
   * :param ctx: The renderer context.
   * :param list: Output of trendSeries.
   * :param model: The chart model.
   * :param options: {
   *     yDomain:    [min, max] value range,
   *     nice:       false to keep yDomain exactly (default true),
   *     yTicks:     explicit tick values (optional),
   *     yFormat:    tick label function (optional),
   *     percent:    true for a percentage axis,
   *     invert:     true to put the domain minimum at the top (ranks),
   *     showYAxis:  false to draw no value labels (streamgraph),
   *     extendEnd:  see resolveXAxis,
   *     xScale:     see resolveXAxis,
   *     bottomExtra / rightExtra: px reserved below / right of the plot
   *   }
   * :returns: { plot, chrome, marks, x, y, plotW, plotH, margin }
   */
  const showYAxis = options.showYAxis !== false
  let domain = options.yDomain
  if (options.nice !== false) {
    domain = niceDomain(domain[0], domain[1], 5)
  }
  const rough = Array.isArray(options.yTicks) === true ? options.yTicks : niceTicks(domain[0], domain[1], 5)
  const format = typeof options.yFormat === "function" ? options.yFormat : tickFormatter(rough, options.percent === true)

  let tickWidth = 0
  for (let index = 0; index < rough.length; index = index + 1) {
    tickWidth = Math.max(tickWidth, textWidth(format(rough[index])))
  }

  const margin = { top: 12, right: 16, bottom: 26, left: 16 }
  if (showYAxis === true) {
    margin.left = Math.round(Math.max(28, tickWidth + 14))
  }
  margin.right = margin.right + (typeof options.rightExtra === "number" ? options.rightExtra : 0)
  margin.bottom = margin.bottom + (typeof options.bottomExtra === "number" ? options.bottomExtra : 0)

  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  const x = resolveXAxis(ctx, list, model, [0, plotW], {
    extendEnd: options.extendEnd === true, xScale: options.xScale
  })
  const y = options.invert === true
    ? linearScale(domain, [0, plotH])
    : linearScale(domain, [plotH, 0])

  const plot = svgEl("g", { transform: `translate(${margin.left},${margin.top})` }, [])
  const chrome = svgEl("g", { "aria-hidden": "true", part: "axes" }, [])
  const marks = svgEl("g", { part: "marks" }, [])
  plot.appendChild(chrome)
  plot.appendChild(marks)

  /* Value gridlines + labels, thinned to the plot height. */
  let yTicks = rough
  if (Array.isArray(options.yTicks) === false) {
    const count = Math.max(2, Math.min(6, Math.floor(plotH / (LABEL_FONT_SIZE * 2.6))))
    yTicks = niceTicks(domain[0], domain[1], count)
  } else {
    const every = Math.max(1, Math.ceil(rough.length / Math.max(1, Math.floor(plotH / (LABEL_FONT_SIZE + 4)))))
    yTicks = rough.filter((tick, index) => index % every === 0)
  }
  for (let index = 0; index < yTicks.length; index = index + 1) {
    const position = y(yTicks[index])
    chrome.appendChild(svgEl("line", {
      x1: 0, y1: position, x2: plotW, y2: position,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    if (showYAxis === true) {
      chrome.appendChild(svgEl("text", {
        x: -8, y: position + 4, "text-anchor": "end",
        "font-size": LABEL_FONT_SIZE, fill: "var(--mj-text-muted, #5f6673)"
      }, format(yTicks[index])))
    }
  }

  /* X labels, kept inside the drawing. */
  const xTicks = axisTicks(x, plotW, LABEL_FONT_SIZE)
  for (let index = 0; index < xTicks.length; index = index + 1) {
    const half = textWidth(xTicks[index].label) / 2
    const lowest = -margin.left + half + 2
    const highest = plotW + margin.right - half - 2
    const center = Math.min(Math.max(xTicks[index].px, lowest), Math.max(highest, lowest))
    chrome.appendChild(svgEl("text", {
      x: center, y: plotH + 16, "text-anchor": "middle",
      "font-size": LABEL_FONT_SIZE, fill: "var(--mj-text, #14181f)"
    }, xTicks[index].label))
  }

  /* Axis baseline. */
  chrome.appendChild(svgEl("line", {
    x1: 0, y1: plotH, x2: plotW, y2: plotH,
    stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
  }, []))

  const frame = {
    plot: plot, chrome: chrome, marks: marks, x: x, y: y,
    plotW: plotW, plotH: plotH, margin: margin
  }
  return frame
}


export function sortedPixels(series, frame, valueOf) {
  /*
   * Place a series' points in x order.
   *
   * :param series: One entry of trendSeries.
   * :param frame: A trend frame (x, y scales).
   * :param valueOf: Optional (point) -> the y value to plot (default
   *     point.y); null marks a gap.
   * :returns: [{ x, y, point, value }] sorted by x; `y` is null for a gap.
   *     Points whose x cannot be placed are left out.
   */
  const placed = []
  for (let p = 0; p < series.points.length; p = p + 1) {
    const point = series.points[p]
    const px = frame.x.position(point)
    if (px === null || Number.isFinite(px) === false) {
      continue
    }
    const value = typeof valueOf === "function" ? valueOf(point) : point.y
    const py = value === null ? null : frame.y(value)
    placed.push({ x: px, y: py, point: point, value: value, order: p })
  }
  placed.sort((a, b) => (a.x - b.x) || (a.order - b.order))
  return placed
}


export function curveMode(ctx, fallback) {
  /*
   * Read the `curve` attribute: "linear", "monotone" or "step"; any other
   * value is "linear".
   */
  const value = String(ctx.attrs("curve", fallback)).trim().toLowerCase()
  const mode = value === "monotone" || value === "step" ? value : "linear"
  return mode
}


function _stepPoints(points) {
  /*
   * Expand points into a step-after polyline: each value holds until the
   * next x. A gap (null) still breaks the line.
   */
  const expanded = []
  for (let index = 0; index < points.length; index = index + 1) {
    const point = points[index]
    const previous = index > 0 ? points[index - 1] : null
    if (point !== null && previous !== null && previous.y !== null && point.y !== null) {
      expanded.push({ x: point.x, y: previous.y })
    }
    expanded.push(point.y === null ? null : point)
  }
  return expanded
}


export function curvePath(points, mode) {
  /*
   * Path data through [{x, y}] (y null = gap) in the chosen curve mode.
   */
  const usable = points.map((point) => point === null || point.y === null ? null : { x: point.x, y: point.y })
  let data = ""
  if (mode === "monotone") {
    data = monotonePath(usable)
  } else if (mode === "step") {
    data = linePath(_stepPoints(points.map((point) => point === null ? { x: 0, y: null } : point)))
  } else {
    data = linePath(usable)
  }
  return data
}


export function bandPath(top, bottom, mode) {
  /*
   * A filled band between two edges, closed separately for every run of
   * points where both edges exist. Both edges use the same curve, so the
   * top of one stacked layer and the bottom of the next coincide.
   *
   * :param top: [{x, y}] (y null = gap), in x order.
   * :param bottom: An index-aligned array like `top`, or a number (a flat
   *     baseline in px).
   * :param mode: "linear" | "monotone" | "step".
   * :returns: Path data.
   */
  const flat = typeof bottom === "number"
  let data = ""
  let run = []

  const flush = () => {
    if (run.length === 0) {
      return
    }
    const upper = run.map((index) => top[index])
    const topData = curvePath(upper, mode)
    let lowerData = ""
    if (flat === true) {
      lowerData = `L${upper[upper.length - 1].x.toFixed(2)},${bottom.toFixed(2)} ` +
        `L${upper[0].x.toFixed(2)},${bottom.toFixed(2)}`
    } else {
      const lower = run.map((index) => bottom[index]).reverse()
      let reversed = ""
      if (mode === "step") {
        /* The reverse of a step-after edge is a step-before edge. */
        const forward = curvePath(run.map((index) => bottom[index]), mode)
        reversed = _reversePolyline(forward)
      } else {
        reversed = curvePath(lower, mode)
      }
      lowerData = reversed.replace(/^M/, "L")
    }
    data = data + `${topData} ${lowerData} Z `
    run = []
  }

  for (let index = 0; index < top.length; index = index + 1) {
    const upper = top[index]
    const lower = flat === true ? bottom : bottom[index]
    const lowerOk = flat === true ? true : lower !== null && lower !== undefined && lower.y !== null
    if (upper === null || upper.y === null || lowerOk === false) {
      flush()
      continue
    }
    run.push(index)
  }
  flush()
  return data.trim()
}


function _reversePolyline(data) {
  /*
   * Reverse a single-run M/L polyline path.
   */
  const coordinates = data.replace(/[ML]/g, " ").trim().split(/\s+/)
  coordinates.reverse()
  const reversed = coordinates.map((pair, index) => `${index === 0 ? "M" : "L"}${pair}`).join(" ")
  return reversed
}


export function loneIndices(pixels) {
  /*
   * Indices of points that have no drawn neighbour, so a line through them
   * would paint nothing.
   */
  const lone = []
  for (let index = 0; index < pixels.length; index = index + 1) {
    if (pixels[index].y === null) {
      continue
    }
    const before = index > 0 ? pixels[index - 1].y : null
    const after = index < pixels.length - 1 ? pixels[index + 1].y : null
    if (before === null && after === null) {
      lone.push(index)
    }
  }
  return lone
}


export function pointTargets(parent, targets, options) {
  /*
   * Append focusable, labelled hit circles for data points. Large series are
   * decimated to about one target per `spacing` px so a 5000-point series
   * does not produce 5000 tab stops and DOM nodes (the accessible table
   * lists every value).
   *
   * :param parent: The <g> to append into.
   * :param targets: [{ x, y, label, detail }].
   * :param options: { ctx, eventName, width (plot width), radius,
   *     spacing (default 6) }.
   */
  const spacing = typeof options.spacing === "number" ? options.spacing : 6
  const limit = Math.max(24, Math.floor(options.width / spacing))
  const stride = targets.length > limit ? Math.ceil(targets.length / limit) : 1
  const radius = typeof options.radius === "number" ? options.radius : 6

  for (let index = 0; index < targets.length; index = index + 1) {
    if (index % stride !== 0 && index !== targets.length - 1) {
      continue
    }
    const target = targets[index]
    const hit = svgEl("circle", {
      cx: target.x.toFixed(2), cy: target.y.toFixed(2), r: radius,
      fill: "transparent",
      part: "hit",
      tabindex: "0",
      role: "img",
      "aria-label": target.label
    }, [svgEl("title", null, target.label)])
    activate(hit, () => {
      options.ctx.emit(options.eventName, target.detail)
    })
    parent.appendChild(hit)
  }
  return
}


export function render(ctx) {
  /*
   * Render a line chart (single or multi-series).
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const model = ctx.model
  const root = svgEl("g", { part: "plot" }, [])

  const list = trendSeries(model)
  const allY = []
  for (let s = 0; s < list.length; s = s + 1) {
    for (let p = 0; p < list[s].points.length; p = p + 1) {
      if (list[s].points[p].y !== null) {
        allY.push(list[s].points[p].y)
      }
    }
  }
  if (allY.length === 0) {
    return root
  }

  const mode = curveMode(ctx, "linear")
  const showPoints = booleanOption(ctx, "show-points", false)

  let yMin = Math.min(...allY)
  let yMax = Math.max(...allY)
  if (yMin === yMax) {
    yMin = yMin - 1
    yMax = yMax + 1
  }

  const frame = trendFrame(ctx, list, model, { yDomain: [yMin, yMax] })
  root.appendChild(frame.plot)

  for (let s = 0; s < list.length; s = s + 1) {
    const series = list[s]
    const color = ctx.colorFor(series.name)
    const group = svgEl("g", { part: "series", "data-series": series.name }, [])
    const pixels = sortedPixels(series, frame)

    const data = curvePath(pixels, mode)
    if (data !== "") {
      group.appendChild(svgEl("path", {
        part: "line",
        "data-series": series.name,
        d: data,
        fill: "none",
        stroke: color,
        "stroke-width": 2,
        "stroke-linejoin": "round",
        "stroke-linecap": "round"
      }, []))
    }

    /* Markers: every point with show-points, else the isolated ones. */
    const lone = new Set(loneIndices(pixels))
    for (let index = 0; index < pixels.length; index = index + 1) {
      const pixel = pixels[index]
      if (pixel.y === null || (showPoints === false && lone.has(index) === false)) {
        continue
      }
      group.appendChild(svgEl("circle", {
        part: "dot",
        "data-series": series.name,
        cx: pixel.x.toFixed(2), cy: pixel.y.toFixed(2), r: 3,
        fill: color,
        stroke: "var(--mj-surface, #fff)",
        "stroke-width": 1.5
      }, []))
    }

    const targets = []
    for (let index = 0; index < pixels.length; index = index + 1) {
      const pixel = pixels[index]
      if (pixel.y === null) {
        continue
      }
      const xLabel = frame.x.labelOf(pixel.point)
      targets.push({
        x: pixel.x, y: pixel.y,
        label: `${series.name}, ${xLabel}: ${formatNumber(pixel.value)}`,
        detail: { series: series.name, x: pixel.point.raw !== null ? pixel.point.raw : xLabel, y: pixel.value }
      })
    }
    pointTargets(group, targets, { ctx: ctx, eventName: "mj-chart-line-click", width: frame.plotW })

    frame.marks.appendChild(group)
  }

  return root
}


registerRenderer("line", render)
registerRenderer("multiline", render)
