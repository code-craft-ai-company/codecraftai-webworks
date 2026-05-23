/*
 * scales.js
 *
 * Scale constructors for the chart library. A scale maps a data DOMAIN to a
 * pixel RANGE (and back). All renderers use these so independently-placed
 * parts (plot, axes, grid) stay aligned: the controller owns the scale
 * objects and every part reads the same ones.
 *
 *   linearScale, logScale, timeScale, bandScale, pointScale,
 *   ordinalColorScale, sqrtScale, niceTicks
 */


function _clampDomain(min, max) {
  /*
   * Guard against a zero-width domain (which would divide by zero).
   */
  let lo = min
  let hi = max
  if (lo === hi) {
    lo = lo - 1
    hi = hi + 1
  }
  return [lo, hi]
}


export function linearScale(domain, range) {
  /*
   * Continuous linear scale.
   *
   * :param domain: [min, max] data values.
   * :param range: [start, end] pixel positions.
   * :returns: A scale function with .invert, .domain, .range, .ticks.
   */
  const cleaned = _clampDomain(domain[0], domain[1])
  const d0 = cleaned[0]
  const d1 = cleaned[1]
  const r0 = range[0]
  const r1 = range[1]

  const scale = (value) => {
    const fraction = (value - d0) / (d1 - d0)
    const pixel = r0 + fraction * (r1 - r0)
    return pixel
  }

  scale.invert = (pixel) => {
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


export function logScale(domain, range, base) {
  /*
   * Logarithmic scale for power-law / wide-range data. Domain values must
   * be positive.
   */
  const logBase = base || 10
  const logOf = (value) => Math.log(Math.max(value, 1e-9)) / Math.log(logBase)

  const d0 = logOf(domain[0] <= 0 ? 1e-9 : domain[0])
  const d1 = logOf(domain[1] <= 0 ? 1 : domain[1])
  const inner = linearScale([d0, d1], range)

  const scale = (value) => {
    const pixel = inner(logOf(value))
    return pixel
  }
  scale.invert = (pixel) => {
    const exponent = inner.invert(pixel)
    const value = Math.pow(logBase, exponent)
    return value
  }
  scale.domain = () => domain
  scale.range = () => range
  scale.kind = "log"
  scale.ticks = (count) => {
    const start = Math.floor(d0)
    const end = Math.ceil(d1)
    const ticks = []
    for (let exponent = start; exponent <= end; exponent = exponent + 1) {
      ticks.push(Math.pow(logBase, exponent))
    }
    return ticks
  }
  return scale
}


export function timeScale(domain, range) {
  /*
   * Time scale. Domain values are Date objects or epoch milliseconds.
   */
  const toMs = (value) => {
    const ms = value instanceof Date ? value.getTime() : Number(value)
    return ms
  }
  const inner = linearScale([toMs(domain[0]), toMs(domain[1])], range)

  const scale = (value) => {
    const pixel = inner(toMs(value))
    return pixel
  }
  scale.invert = (pixel) => {
    const ms = inner.invert(pixel)
    const date = new Date(ms)
    return date
  }
  scale.domain = () => domain
  scale.range = () => range
  scale.kind = "time"
  scale.ticks = (count) => {
    const lo = toMs(domain[0])
    const hi = toMs(domain[1])
    const steps = niceTicks(lo, hi, count || 6)
    const dates = steps.map((ms) => new Date(ms))
    return dates
  }
  return scale
}


export function bandScale(categories, range, padding) {
  /*
   * Discrete band scale -- maps each category to a band of pixels. Used for
   * the category axis of bar/column charts.
   *
   * :returns: A scale where scale(category) is the band start; .bandwidth()
   *           is the band width; .center(category) is the band midpoint.
   */
  const pad = padding === undefined ? 0.1 : padding
  const count = categories.length
  const r0 = range[0]
  const r1 = range[1]
  const span = r1 - r0

  const step = count > 0 ? span / count : span
  const bandwidth = step * (1 - pad)
  const offset = step * pad / 2

  const index = {}
  for (let position = 0; position < count; position = position + 1) {
    index[categories[position]] = position
  }

  const scale = (category) => {
    const position = index[category]
    if (position === undefined) {
      return r0
    }
    const pixel = r0 + position * step + offset
    return pixel
  }

  scale.bandwidth = () => bandwidth
  scale.step = () => step
  scale.center = (category) => {
    const start = scale(category)
    const middle = start + bandwidth / 2
    return middle
  }
  scale.domain = () => categories.slice()
  scale.range = () => [r0, r1]
  scale.kind = "band"
  scale.ticks = () => categories.slice()
  return scale
}


export function pointScale(categories, range) {
  /*
   * Discrete point scale -- maps each category to a single pixel position
   * (used for the x of a categorical line chart).
   */
  const count = categories.length
  const r0 = range[0]
  const r1 = range[1]
  const step = count > 1 ? (r1 - r0) / (count - 1) : 0

  const index = {}
  for (let position = 0; position < count; position = position + 1) {
    index[categories[position]] = position
  }

  const scale = (category) => {
    const position = index[category]
    if (position === undefined) {
      return r0
    }
    const pixel = count > 1 ? r0 + position * step : (r0 + r1) / 2
    return pixel
  }
  scale.domain = () => categories.slice()
  scale.range = () => [r0, r1]
  scale.kind = "point"
  scale.ticks = () => categories.slice()
  return scale
}


/* Default categorical color ramp -- resolves from design tokens at draw time
 * via var(); these are the token names, cycled across series. */
const COLOR_RAMP = [
  "var(--mj-color-accent-500, #2563eb)",
  "var(--mj-color-success, #15803d)",
  "var(--mj-color-warning, #b45309)",
  "var(--mj-color-danger, #b91c1c)",
  "var(--mj-color-accent-300, #80a8ff)",
  "var(--mj-color-accent-800, #122f78)",
  "var(--mj-color-neutral-500, #6b7280)",
  "var(--mj-color-info, #2563eb)"
];


export function ordinalColorScale(keys, ramp) {
  /*
   * Maps a set of discrete keys (series names) to colors from the ramp.
   */
  const palette = ramp || COLOR_RAMP
  const index = {}
  for (let position = 0; position < keys.length; position = position + 1) {
    index[keys[position]] = palette[position % palette.length]
  }
  const scale = (key) => {
    const color = index[key]
    if (color === undefined) {
      return palette[0]
    }
    return color
  }
  scale.domain = () => keys.slice()
  scale.kind = "color"
  return scale
}


export function sqrtScale(domain, range) {
  /*
   * Square-root scale -- used for bubble radii so AREA is proportional to
   * the value.
   */
  const cleaned = _clampDomain(domain[0], domain[1])
  const d0 = Math.sqrt(Math.max(cleaned[0], 0))
  const d1 = Math.sqrt(Math.max(cleaned[1], 0))
  const inner = linearScale([d0, d1], range)

  const scale = (value) => {
    const pixel = inner(Math.sqrt(Math.max(value, 0)))
    return pixel
  }
  scale.domain = () => domain
  scale.range = () => range
  scale.kind = "sqrt"
  return scale
}


export function niceTicks(min, max, count) {
  /*
   * Produce roughly `count` evenly-spaced "nice" tick values spanning
   * [min, max] (rounded to 1/2/5 x 10^n steps).
   *
   * :returns: An array of tick values.
   */
  const target = count > 0 ? count : 5
  const span = max - min
  if (span === 0) {
    return [min]
  }

  const rawStep = span / target
  const magnitude = Math.pow(10, Math.floor(Math.log10(Math.abs(rawStep))))
  const normalized = rawStep / magnitude

  let niceStep = magnitude
  if (normalized >= 5) {
    niceStep = 10 * magnitude
  } else if (normalized >= 2) {
    niceStep = 5 * magnitude
  } else if (normalized >= 1) {
    niceStep = 2 * magnitude
  }

  const start = Math.ceil(min / niceStep) * niceStep
  const ticks = []
  let value = start
  while (value <= max + niceStep * 1e-6) {
    ticks.push(Number(value.toFixed(10)))
    value = value + niceStep
  }
  return ticks
}
