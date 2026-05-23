/*
 * svgdraw.js
 *
 * SVG drawing helpers shared by every chart renderer: an SVG-element
 * builder, path/line/area generators, arc math, number/date formatting,
 * and HTML escaping. Renderers stay declarative by composing these.
 */

const SVG_NS = "http://www.w3.org/2000/svg";


export function svgEl(name, attrs, children) {
  /*
   * Build an SVG element.
   *
   * :param name: The SVG tag name.
   * :param attrs: Attribute map (null values are skipped).
   * :param children: Optional array of child nodes or a text string.
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

  if (typeof children === "string") {
    element.textContent = children
  } else if (Array.isArray(children) === true) {
    for (let index = 0; index < children.length; index = index + 1) {
      const child = children[index]
      if (child !== null && child !== undefined) {
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


export function linePath(points) {
  /*
   * Build an SVG path `d` for a polyline through [{x,y}, ...] points.
   * Points whose value is null break the line into segments.
   *
   * :returns: A path data string.
   */
  let data = ""
  let penDown = false

  for (let index = 0; index < points.length; index = index + 1) {
    const point = points[index]
    if (point === null || point === undefined ||
        point.x === null || point.y === null ||
        Number.isNaN(point.x) === true || Number.isNaN(point.y) === true) {
      penDown = false
      continue
    }
    const command = penDown === false ? "M" : "L"
    data = data + `${command}${point.x.toFixed(2)},${point.y.toFixed(2)} `
    penDown = true
  }
  return data.trim()
}


export function smoothPath(points) {
  /*
   * Build a smoothed (Catmull-Rom -> cubic Bezier) path through points.
   *
   * :returns: A path data string.
   */
  const valid = points.filter((point) => {
    const ok = point !== null && point !== undefined &&
      Number.isNaN(point.x) === false && Number.isNaN(point.y) === false
    return ok
  })
  if (valid.length < 3) {
    return linePath(valid)
  }

  let data = `M${valid[0].x.toFixed(2)},${valid[0].y.toFixed(2)} `
  for (let index = 0; index < valid.length - 1; index = index + 1) {
    const p0 = valid[index === 0 ? 0 : index - 1]
    const p1 = valid[index]
    const p2 = valid[index + 1]
    const p3 = valid[index + 2 < valid.length ? index + 2 : index + 1]

    const c1x = p1.x + (p2.x - p0.x) / 6
    const c1y = p1.y + (p2.y - p0.y) / 6
    const c2x = p2.x - (p3.x - p1.x) / 6
    const c2y = p2.y - (p3.y - p1.y) / 6

    data = data + `C${c1x.toFixed(2)},${c1y.toFixed(2)} ` +
      `${c2x.toFixed(2)},${c2y.toFixed(2)} ` +
      `${p2.x.toFixed(2)},${p2.y.toFixed(2)} `
  }
  return data.trim()
}


export function areaPath(topPoints, baseline) {
  /*
   * Build a filled-area path: a line across topPoints, closed down to a
   * flat `baseline` y.
   *
   * :returns: A path data string.
   */
  const top = linePath(topPoints)
  if (top === "") {
    return ""
  }
  const first = topPoints.find((p) => p !== null && p !== undefined)
  const last = [...topPoints].reverse().find((p) => p !== null && p !== undefined)
  const close = `L${last.x.toFixed(2)},${baseline.toFixed(2)} ` +
    `L${first.x.toFixed(2)},${baseline.toFixed(2)} Z`
  const data = `${top} ${close}`
  return data
}


export function arcPath(cx, cy, innerRadius, outerRadius, startAngle, endAngle) {
  /*
   * Build a donut/pie wedge path between two angles (radians, 0 = up,
   * clockwise).
   *
   * :returns: A path data string.
   */
  const pointAt = (radius, angle) => {
    const x = cx + radius * Math.sin(angle)
    const y = cy - radius * Math.cos(angle)
    return { x: x, y: y }
  }

  const largeArc = (endAngle - startAngle) > Math.PI ? 1 : 0
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


export function formatNumber(value, options) {
  /*
   * Locale-aware number formatting.
   */
  if (value === null || value === undefined || Number.isNaN(value) === true) {
    return ""
  }
  const formatter = new Intl.NumberFormat(undefined, options || {})
  const text = formatter.format(value)
  return text
}


export function formatDate(value, options) {
  /*
   * Locale-aware date formatting.
   */
  const date = value instanceof Date ? value : new Date(value)
  const formatter = new Intl.DateTimeFormat(undefined, options || { dateStyle: "medium" })
  const text = formatter.format(date)
  return text
}


export function escapeHtml(value) {
  /*
   * Escape a string for safe insertion into HTML/SVG text.
   */
  const text = String(value === null || value === undefined ? "" : value)
  const escaped = text
    .split("&").join("&amp;")
    .split("<").join("&lt;")
    .split(">").join("&gt;")
    .split('"').join("&quot;")
  return escaped
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
