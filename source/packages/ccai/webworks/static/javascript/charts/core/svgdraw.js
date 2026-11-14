/*
 * svgdraw.js
 *
 * SVG drawing helpers shared by every chart renderer: an SVG-element
 * builder, path/line/area generators, arc math, and number/date formatting.
 * Renderers stay declarative by composing these.
 *
 * TEXT CONTRACT: everything handed to `svgEl` is plain text, never markup.
 * A string child becomes a text node and an attribute value goes through
 * `setAttribute`, so neither can inject elements and neither needs escaping.
 * Pass labels exactly as they appear in the data ("FP&A", "a < b"). Escaping
 * them first shows the entity text ("FP&amp;A") to the reader. Markup that is
 * assigned to `innerHTML` is built with core/html.js instead.
 */

import { getLocale } from "../../core/intl.js";

const SVG_NS = "http://www.w3.org/2000/svg";

const DATE_ONLY_PATTERN = /^(\d{4})-(\d{2})-(\d{2})$/;

const FULL_CIRCLE = Math.PI * 2;

/* Intl formatters are costly to construct; one per locale + options. */
const NUMBER_FORMATTERS = new Map();
const DATE_FORMATTERS = new Map();

const DEFAULT_DATE_OPTIONS = { dateStyle: "medium" };


export function svgEl(name, attrs, children) {
  /*
   * Build an SVG element.
   *
   * :param name: The SVG tag name.
   * :param attrs: Attribute map (null and undefined values are skipped).
   * :param children: Optional text (a string or number, inserted as a text
   *     node, never parsed as markup) or an array of child nodes; strings
   *     and numbers inside the array become text nodes too.
   * :returns: The created SVGElement.
   */
  const element = document.createElementNS(SVG_NS, name)

  if (attrs !== null && attrs !== undefined) {
    const keys = Object.keys(attrs)
    for (let index = 0; index < keys.length; index = index + 1) {
      const key = keys[index]
      const value = attrs[key]
      if (value !== null && value !== undefined) {
        element.setAttribute(key, String(value))
      }
    }
  }

  if (typeof children === "string" || typeof children === "number") {
    element.textContent = String(children)
  } else if (Array.isArray(children) === true) {
    for (let index = 0; index < children.length; index = index + 1) {
      const child = children[index]
      if (child === null || child === undefined) {
        continue
      }
      if (typeof child === "string" || typeof child === "number") {
        element.appendChild(document.createTextNode(String(child)))
      } else {
        element.appendChild(child)
      }
    }
  }

  return element
}


export function svgRoot(width, height) {
  /*
   * Build a root <svg> sized to a pixel box, with a matching viewBox.
   */
  const root = svgEl("svg", {
    width: "100%",
    height: "100%",
    viewBox: `0 0 ${width} ${height}`,
    preserveAspectRatio: "xMidYMid meet"
  }, [])
  return root
}


function _isDrawable(point) {
  /*
   * True when a point has finite numeric x and y. Null, undefined, NaN and
   * non-numeric coordinates mark a gap in the data.
   */
  const drawable = point !== null && point !== undefined &&
    typeof point.x === "number" && typeof point.y === "number" &&
    Number.isFinite(point.x) === true && Number.isFinite(point.y) === true
  return drawable
}


function _segments(points) {
  /*
   * Split a point list into runs of consecutive drawable points.
   *
   * :param points: [{x, y}, ...]; entries that are not drawable end a run.
   * :returns: An array of runs; each run is { start, points } where `start`
   *     is the index of its first point in the input.
   */
  const runs = []
  let current = null

  const list = Array.isArray(points) === true ? points : []
  for (let index = 0; index < list.length; index = index + 1) {
    const point = list[index]
    if (_isDrawable(point) === false) {
      current = null
      continue
    }
    if (current === null) {
      current = { start: index, points: [] }
      runs.push(current)
    }
    current.points.push(point)
  }
  return runs
}


function _polyline(points, firstCommand) {
  /*
   * Path data for straight segments through drawable points.
   */
  let data = ""
  for (let index = 0; index < points.length; index = index + 1) {
    const point = points[index]
    const command = index === 0 ? firstCommand : "L"
    data = data + `${command}${point.x.toFixed(2)},${point.y.toFixed(2)} `
  }
  return data
}


export function linePath(points) {
  /*
   * Build an SVG path `d` for a polyline through [{x,y}, ...] points.
   * Points that are null or have a null / NaN / non-numeric coordinate
   * break the line into segments.
   *
   * :returns: A path data string.
   */
  const runs = _segments(points)
  let data = ""
  for (let index = 0; index < runs.length; index = index + 1) {
    data = data + _polyline(runs[index].points, "M")
  }
  return data.trim()
}


function _catmullRom(points) {
  /*
   * Path data for a Catmull-Rom spline (as cubic Beziers) through one run
   * of at least three drawable points.
   */
  let data = `M${points[0].x.toFixed(2)},${points[0].y.toFixed(2)} `
  for (let index = 0; index < points.length - 1; index = index + 1) {
    const p0 = points[index === 0 ? 0 : index - 1]
    const p1 = points[index]
    const p2 = points[index + 1]
    const p3 = points[index + 2 < points.length ? index + 2 : index + 1]

    const c1x = p1.x + (p2.x - p0.x) / 6
    const c1y = p1.y + (p2.y - p0.y) / 6
    const c2x = p2.x - (p3.x - p1.x) / 6
    const c2y = p2.y - (p3.y - p1.y) / 6

    data = data + `C${c1x.toFixed(2)},${c1y.toFixed(2)} ` +
      `${c2x.toFixed(2)},${c2y.toFixed(2)} ` +
      `${p2.x.toFixed(2)},${p2.y.toFixed(2)} `
  }
  return data
}


export function smoothPath(points) {
  /*
   * Build a smoothed (Catmull-Rom -> cubic Bezier) path through points.
   * Like linePath, a null / NaN point ends the current segment, so missing
   * data shows as a gap instead of an invented curve. The curve may
   * overshoot the data between points; use monotonePath where that matters
   * (values that must not dip below zero).
   *
   * :returns: A path data string.
   */
  const runs = _segments(points)
  let data = ""
  for (let index = 0; index < runs.length; index = index + 1) {
    const run = runs[index].points
    if (run.length < 3) {
      data = data + _polyline(run, "M")
    } else {
      data = data + _catmullRom(run)
    }
  }
  return data.trim()
}


function _monotoneTangents(points) {
  /*
   * Fritsch-Carlson tangents for a run of points with increasing x: the
   * slopes that keep a cubic through the points monotone between them.
   */
  const count = points.length
  const secants = []
  for (let index = 0; index < count - 1; index = index + 1) {
    const dx = points[index + 1].x - points[index].x
    const dy = points[index + 1].y - points[index].y
    secants.push(dx !== 0 ? dy / dx : 0)
  }

  const tangents = []
  for (let index = 0; index < count; index = index + 1) {
    if (index === 0) {
      tangents.push(secants[0])
    } else if (index === count - 1) {
      tangents.push(secants[count - 2])
    } else if (secants[index - 1] * secants[index] <= 0) {
      tangents.push(0)
    } else {
      tangents.push((secants[index - 1] + secants[index]) / 2)
    }
  }

  for (let index = 0; index < count - 1; index = index + 1) {
    const secant = secants[index]
    if (secant === 0) {
      tangents[index] = 0
      tangents[index + 1] = 0
      continue
    }
    const a = tangents[index] / secant
    const b = tangents[index + 1] / secant
    const magnitude = a * a + b * b
    if (magnitude > 9) {
      const scale = 3 / Math.sqrt(magnitude)
      tangents[index] = scale * a * secant
      tangents[index + 1] = scale * b * secant
    }
  }
  return tangents
}


export function monotonePath(points) {
  /*
   * Build a smoothed path that never overshoots the data: between two
   * points the curve stays inside their y range (monotone cubic
   * interpolation in x). Points must be ordered by x; gaps break the path
   * exactly as in linePath.
   *
   * :returns: A path data string.
   */
  const runs = _segments(points)
  let data = ""

  for (let r = 0; r < runs.length; r = r + 1) {
    const run = runs[r].points
    if (run.length < 3) {
      data = data + _polyline(run, "M")
      continue
    }

    const tangents = _monotoneTangents(run)
    data = data + `M${run[0].x.toFixed(2)},${run[0].y.toFixed(2)} `
    for (let index = 0; index < run.length - 1; index = index + 1) {
      const p1 = run[index]
      const p2 = run[index + 1]
      const third = (p2.x - p1.x) / 3
      const c1y = p1.y + tangents[index] * third
      const c2y = p2.y - tangents[index + 1] * third
      data = data + `C${(p1.x + third).toFixed(2)},${c1y.toFixed(2)} ` +
        `${(p2.x - third).toFixed(2)},${c2y.toFixed(2)} ` +
        `${p2.x.toFixed(2)},${p2.y.toFixed(2)} `
    }
  }
  return data.trim()
}


export function areaPath(topPoints, baseline) {
  /*
   * Build a filled-area path: a line across topPoints, closed down to the
   * lower boundary. Every run of consecutive drawable points is closed on
   * its own, so a series with gaps fills as separate areas.
   *
   * :param topPoints: [{x, y}, ...] along the top edge.
   * :param baseline: Either a flat baseline y (a number), or an array of
   *     lower-boundary points index-aligned with topPoints (a stacked
   *     area passes the top edge of the layer beneath).
   * :returns: A path data string.
   */
  const list = Array.isArray(topPoints) === true ? topPoints : []
  const lower = Array.isArray(baseline) === true ? baseline : null
  const flat = typeof baseline === "number" && Number.isFinite(baseline) === true ? baseline : 0

  /* With a lower boundary a point is drawable only when both edges are. */
  let source = list
  if (lower !== null) {
    source = list.map((point, index) => {
      const usable = _isDrawable(point) === true && _isDrawable(lower[index]) === true
      return usable === true ? point : null
    })
  }

  const runs = _segments(source)
  let data = ""

  for (let r = 0; r < runs.length; r = r + 1) {
    const run = runs[r]
    const points = run.points
    data = data + _polyline(points, "M")

    if (lower !== null) {
      for (let index = points.length - 1; index >= 0; index = index - 1) {
        const under = lower[run.start + index]
        data = data + `L${under.x.toFixed(2)},${under.y.toFixed(2)} `
      }
    } else {
      const first = points[0]
      const last = points[points.length - 1]
      data = data + `L${last.x.toFixed(2)},${flat.toFixed(2)} ` +
        `L${first.x.toFixed(2)},${flat.toFixed(2)} `
    }
    data = data + "Z "
  }
  return data.trim()
}


export function arcPath(cx, cy, innerRadius, outerRadius, startAngle, endAngle) {
  /*
   * Build a donut/pie wedge path between two angles (radians, 0 = up,
   * clockwise). A sweep of a full turn or more draws the whole disc or
   * ring: an SVG arc whose end points coincide is not rendered, so the
   * full circle is built from two half arcs.
   *
   * :returns: A path data string.
   */
  const pointAt = (radius, angle) => {
    const x = cx + radius * Math.sin(angle)
    const y = cy - radius * Math.cos(angle)
    return { x: x, y: y }
  }

  const sweep = endAngle - startAngle

  if (sweep >= FULL_CIRCLE - 1e-9) {
    const outerTop = pointAt(outerRadius, startAngle)
    const outerBottom = pointAt(outerRadius, startAngle + Math.PI)
    let full = `M${outerTop.x.toFixed(2)},${outerTop.y.toFixed(2)} ` +
      `A${outerRadius},${outerRadius} 0 1 1 ` +
      `${outerBottom.x.toFixed(2)},${outerBottom.y.toFixed(2)} ` +
      `A${outerRadius},${outerRadius} 0 1 1 ` +
      `${outerTop.x.toFixed(2)},${outerTop.y.toFixed(2)} Z`

    if (innerRadius > 0) {
      /* The hole runs the other way round so the nonzero rule leaves it open. */
      const innerTop = pointAt(innerRadius, startAngle)
      const innerBottom = pointAt(innerRadius, startAngle + Math.PI)
      full = full + ` M${innerTop.x.toFixed(2)},${innerTop.y.toFixed(2)} ` +
        `A${innerRadius},${innerRadius} 0 1 0 ` +
        `${innerBottom.x.toFixed(2)},${innerBottom.y.toFixed(2)} ` +
        `A${innerRadius},${innerRadius} 0 1 0 ` +
        `${innerTop.x.toFixed(2)},${innerTop.y.toFixed(2)} Z`
    }
    return full
  }

  const largeArc = sweep > Math.PI ? 1 : 0
  const outerStart = pointAt(outerRadius, startAngle)
  const outerEnd = pointAt(outerRadius, endAngle)

  if (innerRadius <= 0) {
    const data = `M${cx},${cy} ` +
      `L${outerStart.x.toFixed(2)},${outerStart.y.toFixed(2)} ` +
      `A${outerRadius},${outerRadius} 0 ${largeArc} 1 ` +
      `${outerEnd.x.toFixed(2)},${outerEnd.y.toFixed(2)} Z`
    return data
  }

  const innerStart = pointAt(innerRadius, startAngle)
  const innerEnd = pointAt(innerRadius, endAngle)
  const data = `M${outerStart.x.toFixed(2)},${outerStart.y.toFixed(2)} ` +
    `A${outerRadius},${outerRadius} 0 ${largeArc} 1 ` +
    `${outerEnd.x.toFixed(2)},${outerEnd.y.toFixed(2)} ` +
    `L${innerEnd.x.toFixed(2)},${innerEnd.y.toFixed(2)} ` +
    `A${innerRadius},${innerRadius} 0 ${largeArc} 0 ` +
    `${innerStart.x.toFixed(2)},${innerStart.y.toFixed(2)} Z`
  return data
}


export function polarPoint(cx, cy, radius, angle) {
  /*
   * Convert a polar coordinate (radius, angle radians, 0 = up) to {x, y}.
   */
  const point = {
    x: cx + radius * Math.sin(angle),
    y: cy - radius * Math.cos(angle)
  }
  return point
}


function _formatterKey(locale, options) {
  /*
   * Cache key of an Intl formatter: the locale plus its options.
   */
  let optionsKey = ""
  try {
    optionsKey = JSON.stringify(options)
  } catch (error) {
    optionsKey = String(options)
  }
  const key = `${locale}|${optionsKey}`
  return key
}


export function formatNumber(value, options) {
  /*
   * Locale-aware number formatting in the library locale (core/intl.js
   * `setLocale`).
   *
   * :param value: The number to format. Null, undefined and NaN give an
   *     empty string; text that is not a number is returned unchanged.
   * :param options: Optional Intl.NumberFormat options.
   * :returns: The formatted text.
   */
  if (value === null || value === undefined || Number.isNaN(value) === true) {
    return ""
  }

  const numeric = typeof value === "number" ? value : Number(value)
  if (Number.isNaN(numeric) === true) {
    return String(value)
  }

  const locale = getLocale()
  const formatOptions = options !== null && options !== undefined ? options : {}
  const key = _formatterKey(locale, formatOptions)

  let formatter = NUMBER_FORMATTERS.get(key)
  if (formatter === undefined) {
    try {
      formatter = new Intl.NumberFormat(locale, formatOptions)
    } catch (error) {
      /* An unknown locale tag or option set falls back to the default. */
      formatter = new Intl.NumberFormat(undefined, {})
    }
    NUMBER_FORMATTERS.set(key, formatter)
  }

  const text = formatter.format(numeric)
  return text
}


export function parseDate(value) {
  /*
   * Read a date from the forms chart data carries.
   *
   * :param value: A Date, epoch milliseconds, or a date string. A bare
   *     `YYYY-MM-DD` string is a LOCAL calendar day (never midnight UTC,
   *     which shows as the previous day west of Greenwich); any other
   *     string is read by Date.parse (ISO 8601 with a time and offset).
   * :returns: A Date, or null when the value is not a date.
   */
  let date = null

  if (value instanceof Date) {
    date = value
  } else if (typeof value === "number") {
    date = new Date(value)
  } else if (typeof value === "string") {
    const text = value.trim()
    const dayOnly = DATE_ONLY_PATTERN.exec(text)
    if (dayOnly !== null) {
      date = new Date(Number(dayOnly[1]), Number(dayOnly[2]) - 1, Number(dayOnly[3]))
    } else if (text.length > 0) {
      date = new Date(Date.parse(text))
    }
  }

  if (date !== null && Number.isNaN(date.getTime()) === true) {
    date = null
  }
  return date
}


export function formatDate(value, options) {
  /*
   * Locale-aware date formatting in the library locale.
   *
   * :param value: A Date, epoch milliseconds or date string (see parseDate).
   * :param options: Optional Intl.DateTimeFormat options.
   * :returns: The formatted text, or an empty string for an invalid date.
   */
  const date = parseDate(value)
  if (date === null) {
    return ""
  }

  const locale = getLocale()
  const formatOptions = options !== null && options !== undefined ? options : DEFAULT_DATE_OPTIONS
  const key = _formatterKey(locale, formatOptions)

  let formatter = DATE_FORMATTERS.get(key)
  if (formatter === undefined) {
    try {
      formatter = new Intl.DateTimeFormat(locale, formatOptions)
    } catch (error) {
      formatter = new Intl.DateTimeFormat(undefined, DEFAULT_DATE_OPTIONS)
    }
    DATE_FORMATTERS.set(key, formatter)
  }

  const text = formatter.format(date)
  return text
}


export function escapeHtml(value) {
  /*
   * DEPRECATED pass-through, kept so existing renderer imports resolve.
   *
   * Text given to `svgEl` (a child string or an attribute value) is never
   * parsed as markup, so it must NOT be escaped: escaping made "FP&A"
   * display and announce as "FP&amp;A". This function therefore returns the
   * text unchanged -- it does not escape anything. Renderers should drop
   * the call and pass the label itself. Code that really builds markup for
   * `innerHTML` uses `escapeHtml` / `html` from core/html.js.
   *
   * :param value: Any value; null and undefined become "".
   * :returns: The value as plain text.
   */
  const text = String(value === null || value === undefined ? "" : value)
  return text
}


export function extent(values) {
  /*
   * Return [min, max] of a numeric array, ignoring null/NaN.
   *
   * :returns: [min, max], or [0, 1] when there is no numeric value.
   */
  let min = Infinity
  let max = -Infinity
  for (let index = 0; index < values.length; index = index + 1) {
    const value = values[index]
    if (value === null || value === undefined || Number.isNaN(value) === true) {
      continue
    }
    if (value < min) {
      min = value
    }
    if (value > max) {
      max = value
    }
  }
  if (min === Infinity || max === -Infinity) {
    return [0, 1]
  }
  return [min, max]
}
