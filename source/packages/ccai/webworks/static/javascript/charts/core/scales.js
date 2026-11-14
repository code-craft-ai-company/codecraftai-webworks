/*
 * scales.js
 *
 * Scale constructors for the chart library. A scale maps a data DOMAIN to a
 * pixel RANGE (and back). All renderers use these so independently-placed
 * parts (plot, axes, grid) stay aligned: the controller owns the scale
 * objects and every part reads the same ones.
 *
 *   linearScale, logScale, timeScale, bandScale, pointScale, sqrtScale,
 *   ordinalColorScale, seriesColor,
 *   niceTicks, niceDomain, positiveExtent, timeTicks, timeTickFormat
 *
 * Every scale accepts a zero-width or non-finite domain (it is widened so
 * nothing divides by zero) and a range that runs in either direction
 * ([0, 300] or [300, 0]).
 */

import { getLocale } from "../../core/intl.js";
import { parseDate } from "./svgdraw.js";

/* A tick generator never returns more than this many values. */
const TICK_LIMIT = 1000;

const SECOND_MS = 1000;
const MINUTE_MS = 60 * SECOND_MS;
const HOUR_MS = 60 * MINUTE_MS;
const DAY_MS = 24 * HOUR_MS;

/* Calendar tick intervals, shortest first; `ms` is the approximate length. */
const TIME_INTERVALS = [
  { unit: "second", step: 1, ms: SECOND_MS },
  { unit: "second", step: 5, ms: 5 * SECOND_MS },
  { unit: "second", step: 15, ms: 15 * SECOND_MS },
  { unit: "second", step: 30, ms: 30 * SECOND_MS },
  { unit: "minute", step: 1, ms: MINUTE_MS },
  { unit: "minute", step: 5, ms: 5 * MINUTE_MS },
  { unit: "minute", step: 15, ms: 15 * MINUTE_MS },
  { unit: "minute", step: 30, ms: 30 * MINUTE_MS },
  { unit: "hour", step: 1, ms: HOUR_MS },
  { unit: "hour", step: 3, ms: 3 * HOUR_MS },
  { unit: "hour", step: 6, ms: 6 * HOUR_MS },
  { unit: "hour", step: 12, ms: 12 * HOUR_MS },
  { unit: "day", step: 1, ms: DAY_MS },
  { unit: "day", step: 2, ms: 2 * DAY_MS },
  { unit: "week", step: 1, ms: 7 * DAY_MS },
  { unit: "month", step: 1, ms: 30 * DAY_MS },
  { unit: "month", step: 3, ms: 91 * DAY_MS },
  { unit: "month", step: 6, ms: 182 * DAY_MS },
  { unit: "year", step: 1, ms: 365 * DAY_MS }
];

/* Intl.DateTimeFormat options that suit a tick of each calendar unit. */
const TIME_FORMATS = {
  millisecond: { hour: "2-digit", minute: "2-digit", second: "2-digit", fractionalSecondDigits: 3 },
  second: { hour: "2-digit", minute: "2-digit", second: "2-digit" },
  minute: { hour: "2-digit", minute: "2-digit" },
  hour: { hour: "2-digit", minute: "2-digit" },
  day: { month: "short", day: "numeric" },
  week: { month: "short", day: "numeric" },
  month: { month: "short", year: "numeric" },
  year: { year: "numeric" }
};


function _finiteOr(value, fallback) {
  /*
   * Coerce a value to a finite number, or return the fallback.
   */
  const numeric = typeof value === "number" ? value : Number(value)
  if (value === null || value === undefined || Number.isFinite(numeric) === false) {
    return fallback
  }
  return numeric
}


function _clampDomain(min, max) {
  /*
   * Make a [min, max] domain safe to divide by: a non-finite end falls back
   * to [0, 1] and a zero-width domain is widened around its value. The
   * direction of a descending domain is kept.
   */
  let lo = _finiteOr(min, NaN)
  let hi = _finiteOr(max, NaN)

  if (Number.isNaN(lo) === true && Number.isNaN(hi) === true) {
    lo = 0
    hi = 1
  } else if (Number.isNaN(lo) === true) {
    lo = hi
  } else if (Number.isNaN(hi) === true) {
    hi = lo
  }

  if (lo === hi) {
    /* Pad by one unit, or by enough to register at a large magnitude. */
    const pad = Math.max(1, Math.abs(lo) * 1e-6)
    lo = lo - pad
    hi = hi + pad
  }
  return [lo, hi]
}


function _cleanRange(range) {
  /*
   * Read a [start, end] pixel range; a missing or non-finite end is 0.
   */
  const list = Array.isArray(range) === true ? range : []
  const cleaned = [_finiteOr(list[0], 0), _finiteOr(list[1], 0)]
  return cleaned
}


export function linearScale(domain, range) {
  /*
   * Continuous linear scale.
   *
   * :param domain: [min, max] data values (either direction).
   * :param range: [start, end] pixel positions (either direction).
   * :returns: A scale function with .invert, .domain, .range, .ticks.
   */
  const cleaned = _clampDomain(domain[0], domain[1])
  const d0 = cleaned[0]
  const d1 = cleaned[1]
  const pixels = _cleanRange(range)
  const r0 = pixels[0]
  const r1 = pixels[1]

  const scale = (value) => {
    const fraction = (value - d0) / (d1 - d0)
    const pixel = r0 + fraction * (r1 - r0)
    return pixel
  }

  scale.invert = (pixel) => {
    if (r1 === r0) {
      return d0
    }
    const fraction = (pixel - r0) / (r1 - r0)
    const value = d0 + fraction * (d1 - d0)
    return value
  }

  scale.domain = () => [d0, d1]
  scale.range = () => [r0, r1]
  scale.kind = "linear"
  scale.ticks = (count) => niceTicks(d0, d1, count || 6)
  return scale
}


export function positiveExtent(values) {
  /*
   * [min, max] of the strictly positive numbers in an array -- the domain a
   * log scale can show. Zero, negative, null and NaN entries are ignored.
   *
   * :returns: [min, max], or [1, 10] when there is no positive value.
   */
  let min = Infinity
  let max = -Infinity
  const list = Array.isArray(values) === true ? values : []
  for (let index = 0; index < list.length; index = index + 1) {
    const value = list[index]
    if (typeof value !== "number" || Number.isFinite(value) === false || value <= 0) {
      continue
    }
    if (value < min) {
      min = value
    }
    if (value > max) {
      max = value
    }
  }
  if (min === Infinity) {
    return [1, 10]
  }
  return [min, max]
}


export function logScale(domain, range, base) {
  /*
   * Logarithmic scale for power-law / wide-range data.
   *
   * A log axis cannot show zero or negative values. A non-positive domain
   * end is replaced by a value three decades away from the other end (or
   * the domain becomes [1, base] when neither end is positive), and a
   * non-positive value passed to the scale is drawn at the lower end of
   * the axis. Use positiveExtent(values) to build the domain from data.
   *
   * :param domain: [min, max] data values.
   * :param range: [start, end] pixel positions.
   * :param base: The log base (default 10).
   */
  const logBase = typeof base === "number" && base > 0 && base !== 1 ? base : 10
  const decades = Math.pow(logBase, 3)

  let lo = _finiteOr(domain[0], 0)
  let hi = _finiteOr(domain[1], 0)
  if (lo <= 0 && hi <= 0) {
    lo = 1
    hi = logBase
  } else if (lo <= 0) {
    lo = hi / decades
  } else if (hi <= 0) {
    hi = lo / decades
  }

  const floor = Math.min(lo, hi)
  const logOf = (value) => {
    const usable = typeof value === "number" && value > 0 ? value : floor
    return Math.log(usable) / Math.log(logBase)
  }

  const inner = linearScale([logOf(lo), logOf(hi)], range)

  const scale = (value) => {
    const pixel = inner(logOf(value))
    return pixel
  }
  scale.invert = (pixel) => {
    const exponent = inner.invert(pixel)
    const value = Math.pow(logBase, exponent)
    return value
  }
  scale.domain = () => [lo, hi]
  scale.range = () => inner.range()
  scale.kind = "log"
  scale.ticks = (count) => {
    const min = Math.min(lo, hi)
    const max = Math.max(lo, hi)
    const tolerance = 1e-9
    const inDomain = (value) => value >= min * (1 - tolerance) && value <= max * (1 + tolerance)

    const start = Math.floor(logOf(min) + tolerance)
    const end = Math.ceil(logOf(max) - tolerance)
    const span = Math.min(end - start, TICK_LIMIT)

    const powers = []
    for (let offset = 0; offset <= span; offset = offset + 1) {
      const power = Math.pow(logBase, start + offset)
      if (inDomain(power) === true) {
        powers.push(power)
      }
    }

    let ticks = powers
    if (powers.length < 3 && logBase === 10) {
      /* A narrow domain also gets the 2x and 5x steps of each decade. */
      ticks = []
      for (let offset = -1; offset <= span; offset = offset + 1) {
        const power = Math.pow(logBase, start + offset)
        const steps = [power, 2 * power, 5 * power]
        for (let s = 0; s < steps.length; s = s + 1) {
          if (inDomain(steps[s]) === true) {
            ticks.push(steps[s])
          }
        }
      }
    }
    if (ticks.length < 2) {
      /* Less than one step wide: fall back to evenly spaced values. */
      ticks = niceTicks(min, max, count || 5)
    }
    if (lo > hi) {
      ticks = ticks.slice().reverse()
    }
    return ticks
  }
  return scale
}


function _floorTime(date, unit, step) {
  /*
   * The latest local calendar boundary of `unit` x `step` at or before a
   * date: the start of the second / minute / hour / day / week (Monday) /
   * month / year block that contains it.
   */
  const year = date.getFullYear()
  const month = date.getMonth()
  const day = date.getDate()
  let floored = null

  if (unit === "year") {
    floored = new Date(Math.floor(year / step) * step, 0, 1)
  } else if (unit === "month") {
    floored = new Date(year, Math.floor(month / step) * step, 1)
  } else if (unit === "week") {
    const sinceMonday = (date.getDay() + 6) % 7
    floored = new Date(year, month, day - sinceMonday)
  } else if (unit === "day") {
    floored = new Date(year, month, day)
  } else if (unit === "hour") {
    floored = new Date(year, month, day, Math.floor(date.getHours() / step) * step)
  } else if (unit === "minute") {
    floored = new Date(year, month, day, date.getHours(),
      Math.floor(date.getMinutes() / step) * step)
  } else {
    floored = new Date(year, month, day, date.getHours(), date.getMinutes(),
      Math.floor(date.getSeconds() / step) * step)
  }
  return floored
}


function _advanceTime(date, unit, step) {
  /*
   * A date moved forward by `step` calendar units, in local time so day
   * and month ticks stay on their boundaries across a DST change.
   */
  const next = new Date(date.getTime())
  if (unit === "year") {
    next.setFullYear(next.getFullYear() + step)
  } else if (unit === "month") {
    next.setMonth(next.getMonth() + step)
  } else if (unit === "week") {
    next.setDate(next.getDate() + 7 * step)
  } else if (unit === "day") {
    next.setDate(next.getDate() + step)
  } else if (unit === "hour") {
    next.setTime(next.getTime() + step * HOUR_MS)
  } else if (unit === "minute") {
    next.setTime(next.getTime() + step * MINUTE_MS)
  } else {
    next.setTime(next.getTime() + step * SECOND_MS)
  }
  return next
}


function _timeInterval(startMs, endMs, count) {
  /*
   * Choose the calendar interval that gives about `count` ticks between
   * two instants.
   *
   * :returns: { unit, step }. The unit is "millisecond" for a span shorter
   *     than the shortest calendar interval.
   */
  const target = count > 0 ? count : 6
  const span = Math.abs(endMs - startMs)
  const ideal = span / target

  if (ideal < SECOND_MS / 2) {
    return { unit: "millisecond", step: 1 }
  }

  let chosen = null
  for (let index = 0; index < TIME_INTERVALS.length; index = index + 1) {
    if (TIME_INTERVALS[index].ms >= ideal) {
      chosen = TIME_INTERVALS[index]
      break
    }
  }
  if (chosen !== null) {
    return { unit: chosen.unit, step: chosen.step }
  }

  /* Longer than a year per tick: a 1 / 2 / 5 x 10^n number of years. */
  const years = ideal / (365 * DAY_MS)
  const magnitude = Math.pow(10, Math.floor(Math.log10(years)))
  const normalized = years / magnitude
  let yearStep = 10 * magnitude
  if (normalized <= 1) {
    yearStep = magnitude
  } else if (normalized <= 2) {
    yearStep = 2 * magnitude
  } else if (normalized <= 5) {
    yearStep = 5 * magnitude
  }
  return { unit: "year", step: Math.max(1, Math.round(yearStep)) }
}


export function timeTicks(start, end, count) {
  /*
   * Calendar-aligned tick dates between two instants: whole seconds,
   * minutes, hours, days, weeks, months or years in local time, whichever
   * gives about `count` ticks.
   *
   * :param start: A Date, epoch milliseconds or date string.
   * :param end: A Date, epoch milliseconds or date string.
   * :param count: The approximate number of ticks wanted (default 6).
   * :returns: An array of Date objects in ascending order; empty when
   *     either end is not a date.
   */
  const startDate = parseDate(start)
  const endDate = parseDate(end)
  if (startDate === null || endDate === null) {
    return []
  }

  const lo = Math.min(startDate.getTime(), endDate.getTime())
  const hi = Math.max(startDate.getTime(), endDate.getTime())
  const interval = _timeInterval(lo, hi, count)

  if (interval.unit === "millisecond") {
    const steps = niceTicks(lo, hi, count || 6)
    return steps.map((ms) => new Date(ms))
  }

  let ticks = []
  let cursor = _floorTime(new Date(lo), interval.unit, interval.step)
  let guard = 0
  while (cursor.getTime() <= hi && guard < TICK_LIMIT) {
    if (cursor.getTime() >= lo) {
      ticks.push(cursor)
    }
    cursor = _advanceTime(cursor, interval.unit, interval.step)
    guard = guard + 1
  }

  /*
   * A short span can fall between two calendar boundaries (13:00-14:30 on
   * a 3-hour step): the axis still gets its two ends.
   */
  if (ticks.length < 2) {
    const ends = lo === hi ? [lo] : [lo, hi]
    const merged = ticks.map((date) => date.getTime())
    for (let index = 0; index < ends.length; index = index + 1) {
      if (merged.indexOf(ends[index]) < 0) {
        merged.push(ends[index])
      }
    }
    merged.sort((a, b) => a - b)
    ticks = merged.map((ms) => new Date(ms))
  }
  return ticks
}


export function timeTickFormat(start, end, count) {
  /*
   * A label formatter that suits the ticks timeTicks returns for the same
   * arguments: years as "2026", months as "Jan 2026", days as "Jan 5",
   * times as "14:30".
   *
   * :returns: A function (date) -> string in the library locale.
   */
  const startDate = parseDate(start)
  const endDate = parseDate(end)
  let unit = "day"
  if (startDate !== null && endDate !== null) {
    unit = _timeInterval(startDate.getTime(), endDate.getTime(), count).unit
  }

  let formatter = null
  try {
    formatter = new Intl.DateTimeFormat(getLocale(), TIME_FORMATS[unit])
  } catch (error) {
    formatter = new Intl.DateTimeFormat(undefined, TIME_FORMATS[unit])
  }

  const format = (value) => {
    const date = parseDate(value)
    const text = date !== null ? formatter.format(date) : ""
    return text
  }
  return format
}


export function timeScale(domain, range) {
  /*
   * Time scale. Domain values (and the values passed to the scale) are
   * Date objects, epoch milliseconds or date strings; a bare `YYYY-MM-DD`
   * string is a local calendar day (see parseDate in svgdraw.js).
   *
   * :returns: A scale with .invert (-> Date), .domain, .range, .ticks
   *     (calendar-aligned Dates) and .tickFormat (-> label function).
   */
  const toMs = (value) => {
    const date = parseDate(value)
    const ms = date !== null ? date.getTime() : NaN
    return ms
  }

  const inner = linearScale([toMs(domain[0]), toMs(domain[1])], range)
  const bounds = inner.domain()

  const scale = (value) => {
    const pixel = inner(toMs(value))
    return pixel
  }
  scale.invert = (pixel) => {
    const ms = inner.invert(pixel)
    const date = new Date(ms)
    return date
  }
  scale.domain = () => [new Date(bounds[0]), new Date(bounds[1])]
  scale.range = () => inner.range()
  scale.kind = "time"
  scale.ticks = (count) => timeTicks(bounds[0], bounds[1], count || 6)
  scale.tickFormat = (count) => timeTickFormat(bounds[0], bounds[1], count || 6)
  return scale
}


function _positionIndex(categories) {
  /*
   * Look-up from a category to its first position. Lookups go through a
   * Map (so "constructor" or "__proto__" are ordinary labels) by the exact
   * value first and by its text second, so 1 and "1" still find each other.
   */
  const exact = new Map()
  const byText = new Map()
  for (let position = 0; position < categories.length; position = position + 1) {
    const category = categories[position]
    if (exact.has(category) === false) {
      exact.set(category, position)
    }
    const text = String(category)
    if (byText.has(text) === false) {
      byText.set(text, position)
    }
  }

  const positionOf = (category) => {
    let position = exact.get(category)
    if (position === undefined) {
      position = byText.get(String(category))
    }
    return position
  }
  return positionOf
}


export function bandScale(categories, range, padding) {
  /*
   * Discrete band scale -- maps each category to a band of pixels. Used for
   * the category axis of bar/column charts.
   *
   * The range may run in either direction; a band is always described by
   * its lower pixel edge and a non-negative bandwidth. Two categories with
   * the same label share the first one's band when looked up by label, so a
   * renderer that may receive duplicates positions by index with
   * .at(index) / .centerAt(index).
   *
   * :returns: A scale where scale(category) is the band start; .bandwidth()
   *           is the band width; .center(category) is the band midpoint.
   */
  const list = Array.isArray(categories) === true ? categories : []
  const rawPad = padding === undefined || padding === null ? 0.1 : _finiteOr(padding, 0.1)
  const pad = Math.min(Math.max(rawPad, 0), 1)
  const count = list.length
  const pixels = _cleanRange(range)
  const r0 = pixels[0]
  const r1 = pixels[1]
  const descending = r1 < r0
  const span = Math.abs(r1 - r0)

  const step = count > 0 ? span / count : span
  const bandwidth = step * (1 - pad)
  const offset = step * pad / 2

  const positionOf = _positionIndex(list)

  const at = (position) => {
    const pixel = descending === true
      ? r0 - (position + 1) * step + offset
      : r0 + position * step + offset
    return pixel
  }

  const scale = (category) => {
    const position = positionOf(category)
    if (position === undefined) {
      return r0
    }
    return at(position)
  }

  scale.at = at
  scale.centerAt = (position) => at(position) + bandwidth / 2
  scale.indexOf = (category) => {
    const position = positionOf(category)
    return position === undefined ? -1 : position
  }
  scale.bandwidth = () => bandwidth
  scale.step = () => step
  scale.center = (category) => {
    const start = scale(category)
    const middle = start + bandwidth / 2
    return middle
  }
  scale.domain = () => list.slice()
  scale.range = () => [r0, r1]
  scale.kind = "band"
  scale.ticks = () => list.slice()
  return scale
}


export function pointScale(categories, range) {
  /*
   * Discrete point scale -- maps each category to a single pixel position
   * (used for the x of a categorical line chart). Duplicate labels resolve
   * to the first one by label; position by index with .at(index).
   */
  const list = Array.isArray(categories) === true ? categories : []
  const count = list.length
  const pixels = _cleanRange(range)
  const r0 = pixels[0]
  const r1 = pixels[1]
  const step = count > 1 ? (r1 - r0) / (count - 1) : 0

  const positionOf = _positionIndex(list)

  const at = (position) => {
    const pixel = count > 1 ? r0 + position * step : (r0 + r1) / 2
    return pixel
  }

  const scale = (category) => {
    const position = positionOf(category)
    if (position === undefined) {
      return r0
    }
    return at(position)
  }
  scale.at = at
  scale.indexOf = (category) => {
    const position = positionOf(category)
    return position === undefined ? -1 : position
  }
  scale.step = () => step
  scale.domain = () => list.slice()
  scale.range = () => [r0, r1]
  scale.kind = "point"
  scale.ticks = () => list.slice()
  return scale
}


/*
 * Categorical series palette.
 *
 * Each slot reads a `--mj-chart-series-N` custom property, so a theme (or a
 * single chart) can override it, and falls back to a light / dark pair.
 * `light-dark()` follows the inherited `color-scheme` that tokens.css sets
 * per theme, so the fallback switches with the theme without any selector.
 *
 * The eight hues are in a fixed order chosen so neighbours stay apart for
 * colour-vision deficiencies; every step keeps 3:1 against its surface
 * (#ffffff light, #232934 dark). Do not reorder them, and do not reuse the
 * status colours (success / warning / danger) as series.
 */
export const SERIES_PALETTE = [
  { token: "--mj-chart-series-1", light: "#2a78d6", dark: "#3987e5" },
  { token: "--mj-chart-series-2", light: "#eb6834", dark: "#d95926" },
  { token: "--mj-chart-series-3", light: "#199e70", dark: "#199e70" },
  { token: "--mj-chart-series-4", light: "#c98500", dark: "#c98500" },
  { token: "--mj-chart-series-5", light: "#d55181", dark: "#d55181" },
  { token: "--mj-chart-series-6", light: "#008300", dark: "#008a00" },
  { token: "--mj-chart-series-7", light: "#6250d6", dark: "#9085e9" },
  { token: "--mj-chart-series-8", light: "#e34948", dark: "#e66767" }
];

/*
 * Past the last palette slot the hues repeat with a lightness shift: the
 * second pass is mixed toward the text colour, the third toward the
 * surface. `keep` is the percentage of the palette colour that remains.
 */
const PALETTE_SHIFTS = [
  null,
  { keep: 62, toward: "--mj-text", light: "#14181f", dark: "#f7f8fa" },
  { keep: 58, toward: "--mj-surface", light: "#ffffff", dark: "#232934" }
];


function _supportsColor(value) {
  /*
   * True when the browser accepts a CSS colour value.
   */
  let supported = false
  if (typeof CSS !== "undefined" && typeof CSS.supports === "function") {
    supported = CSS.supports("color", value)
  }
  return supported
}

const SUPPORTS_LIGHT_DARK = _supportsColor("light-dark(#000000, #ffffff)");
const SUPPORTS_COLOR_MIX = _supportsColor("color-mix(in oklab, #000000 50%, #ffffff)");


function _themedColor(token, light, dark) {
  /*
   * A CSS colour that reads a custom property and falls back to a light /
   * dark pair (the light value alone where light-dark() is unsupported).
   */
  const fallback = SUPPORTS_LIGHT_DARK === true ? `light-dark(${light}, ${dark})` : light
  const color = `var(${token}, ${fallback})`
  return color
}


export function seriesColor(slot) {
  /*
   * The categorical colour of a palette slot.
   *
   * :param slot: A zero-based slot number; any integer is valid. Slots past
   *     the palette repeat its hues with a lightness shift, so the first
   *     24 slots are distinct colours.
   * :returns: A CSS colour string for an SVG paint attribute or a style.
   */
  const numeric = _finiteOr(slot, 0)
  const index = Math.abs(Math.trunc(numeric))
  const size = SERIES_PALETTE.length
  const entry = SERIES_PALETTE[index % size]
  const base = _themedColor(entry.token, entry.light, entry.dark)

  const pass = Math.floor(index / size) % PALETTE_SHIFTS.length
  const shift = PALETTE_SHIFTS[pass]
  if (shift === null || SUPPORTS_COLOR_MIX === false) {
    return base
  }

  const toward = _themedColor(shift.toward, shift.light, shift.dark)
  const color = `color-mix(in oklab, ${base} ${shift.keep}%, ${toward})`
  return color
}


export function ordinalColorScale(keys, ramp) {
  /*
   * Maps a set of discrete keys (series names) to colors.
   *
   * :param keys: The known keys, in palette order.
   * :param ramp: Optional array of CSS colours to use instead of the
   *     series palette (cycled when there are more keys than colours).
   * :returns: A scale (key) -> colour. A key that is not in `keys` gets
   *     the next free slot the first time it is asked for and keeps it, so
   *     every key has its own colour. .slotOf(key) and .colorAt(slot) are
   *     also available.
   */
  const list = Array.isArray(keys) === true ? keys : []
  const palette = Array.isArray(ramp) === true && ramp.length > 0 ? ramp : null

  const colorAt = (slot) => {
    const color = palette !== null ? palette[slot % palette.length] : seriesColor(slot)
    return color
  }

  const slots = new Map()
  for (let position = 0; position < list.length; position = position + 1) {
    const text = String(list[position])
    if (slots.has(text) === false) {
      slots.set(text, position)
    }
  }
  let nextSlot = list.length

  const slotOf = (key) => {
    const text = String(key)
    let slot = slots.get(text)
    if (slot === undefined) {
      slot = nextSlot
      nextSlot = nextSlot + 1
      slots.set(text, slot)
    }
    return slot
  }

  const scale = (key) => {
    const color = colorAt(slotOf(key))
    return color
  }
  scale.slotOf = slotOf
  scale.colorAt = colorAt
  scale.domain = () => list.slice()
  scale.kind = "color"
  return scale
}


export function sqrtScale(domain, range) {
  /*
   * Square-root scale -- used for bubble radii so AREA is proportional to
   * the value. Negative values are treated as zero.
   */
  const cleaned = _clampDomain(domain[0], domain[1])
  const d0 = Math.sqrt(Math.max(cleaned[0], 0))
  const d1 = Math.sqrt(Math.max(cleaned[1], 0))
  const inner = linearScale([d0, d1], range)

  const scale = (value) => {
    const pixel = inner(Math.sqrt(Math.max(value, 0)))
    return pixel
  }
  scale.invert = (pixel) => {
    const root = inner.invert(pixel)
    const value = root * root
    return value
  }
  scale.domain = () => [domain[0], domain[1]]
  scale.range = () => inner.range()
  scale.kind = "sqrt"
  return scale
}


function _niceStep(span, count) {
  /*
   * The 1 / 2 / 5 x 10^n step that divides a span into about `count` parts:
   * the raw step rounded to the NEAREST rung of the ladder (below 1.5 -> 1,
   * below 3 -> 2, below 7 -> 5, else 10), so niceTicks(0, 1, 5) gives the
   * six ticks 0, 0.2, ... 1 rather than three.
   */
  const rawStep = span / count
  const magnitude = Math.pow(10, Math.floor(Math.log10(Math.abs(rawStep))))
  const normalized = rawStep / magnitude

  let niceStep = 10 * magnitude
  if (normalized < 1.5) {
    niceStep = magnitude
  } else if (normalized < 3) {
    niceStep = 2 * magnitude
  } else if (normalized < 7) {
    niceStep = 5 * magnitude
  }
  return niceStep
}


function _roundToStep(value, step) {
  /*
   * Remove floating-point noise from a tick value, keeping two more
   * decimals than the step needs.
   */
  const decimals = Math.min(Math.max(2 - Math.floor(Math.log10(step)), 0), 100)
  const rounded = Number(value.toFixed(decimals))
  return rounded
}


export function niceTicks(min, max, count) {
  /*
   * Produce roughly `count` evenly-spaced "nice" tick values spanning
   * [min, max] (rounded to 1/2/5 x 10^n steps).
   *
   * :param min: One end of the domain.
   * :param max: The other end; when it is below `min` the ticks are
   *     returned in descending order.
   * :returns: An array of tick values; empty when an end is not finite.
   */
  const first = _finiteOr(min, NaN)
  const second = _finiteOr(max, NaN)
  if (Number.isNaN(first) === true || Number.isNaN(second) === true) {
    return []
  }

  const target = count > 0 ? count : 5
  const lo = Math.min(first, second)
  const hi = Math.max(first, second)
  if (lo === hi) {
    return [lo]
  }

  const niceStep = _niceStep(hi - lo, target)
  if (Number.isFinite(niceStep) === false || niceStep <= 0 || lo + niceStep === lo) {
    /* The step is below what a float can add at this magnitude. */
    return first <= second ? [lo, hi] : [hi, lo]
  }

  /* Ticks are start + i * step, never an accumulated sum, and are capped. */
  const firstIndex = Math.ceil(lo / niceStep - 1e-9)
  const lastIndex = Math.floor(hi / niceStep + 1e-6)
  const total = Math.min(lastIndex - firstIndex + 1, TICK_LIMIT)

  const ticks = []
  for (let offset = 0; offset < total; offset = offset + 1) {
    ticks.push(_roundToStep((firstIndex + offset) * niceStep, niceStep))
  }
  if (first > second) {
    ticks.reverse()
  }
  return ticks
}


export function niceDomain(min, max, count) {
  /*
   * Widen [min, max] outward to the tick boundaries niceTicks would use,
   * so the first and last ticks sit on the ends of the axis and the
   * largest value is not above the top tick.
   *
   * :returns: [low, high] in the direction of the arguments.
   */
  const cleaned = _clampDomain(min, max)
  const descending = cleaned[0] > cleaned[1]
  const lo = Math.min(cleaned[0], cleaned[1])
  const hi = Math.max(cleaned[0], cleaned[1])

  const target = count > 0 ? count : 5
  const niceStep = _niceStep(hi - lo, target)
  if (Number.isFinite(niceStep) === false || niceStep <= 0 || lo + niceStep === lo) {
    return descending === true ? [hi, lo] : [lo, hi]
  }

  const low = _roundToStep(Math.floor(lo / niceStep + 1e-9) * niceStep, niceStep)
  const high = _roundToStep(Math.ceil(hi / niceStep - 1e-9) * niceStep, niceStep)
  const domain = descending === true ? [high, low] : [low, high]
  return domain
}
