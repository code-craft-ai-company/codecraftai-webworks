/*
 * control.js
 *
 * Control chart / run chart renderer.
 *
 * Registers:
 *   "control-chart" — process values over time with control limits. A point
 *                     beyond the outermost UCL / LCL (or flagged ooc: true)
 *                     is drawn as a red diamond.
 *   "run-chart"     — process values with their median (computed from the
 *                     data); control limits are ignored. A shift -- six or
 *                     more consecutive points on one side of the median -- is
 *                     marked with rings.
 *
 * JSON shape (ctx.raw):
 *   series: [{ name, points: [{ x, y, ooc? }] }]
 *   control_limits: { ucl, lcl, cl, label? } or an array of such sets
 *                   (sigma zones); each limit is drawn when it is a number
 *   reference_lines: [{ label, value }]   optional horizontal annotations
 *
 *   x  a number (sequence, timestamp), a date ("YYYY-MM-DD" is a local day,
 *      ISO date-times) or a category label ("Mon") -- the axis follows
 *   y  a number; null or a non-number is a gap in the line
 *
 * Options:
 *   limits="auto"  (control-chart) compute CL = mean and UCL / LCL =
 *                  CL +/- 2.66 x average moving range (individuals chart)
 *                  from the first series instead of using control_limits.
 *                  A control chart whose data has no control_limits gets
 *                  these computed limits too.
 *
 * Events:
 *   mj-chart-point-click { series, x, y, ooc, shift }
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber, formatDate, linePath, parseDate } from "../svgdraw.js";
import { linearScale, pointScale, timeScale, niceDomain, niceTicks } from "../scales.js";


const LIMIT_COLOR = "var(--mj-color-danger, #b91c1c)";
const SHIFT_RUN = 6;
const CHAR_WIDTH = 0.56;


function _number(value) {
  /*
   * A finite number from a number or numeric string, else null.
   */
  if (value === null || value === undefined || value === "" || typeof value === "boolean") {
    return null
  }
  const numeric = Number(value)
  const result = Number.isFinite(numeric) === true ? numeric : null
  return result
}


function _xKind(series) {
  /*
   * How the x values read: "number", "time" or "category".
   */
  let allNumbers = true
  let allDates = true
  let any = false
  for (let s = 0; s < series.length; s = s + 1) {
    const points = Array.isArray(series[s].points) === true ? series[s].points : []
    for (let p = 0; p < points.length; p = p + 1) {
      const x = points[p] !== null && typeof points[p] === "object" ? points[p].x : null
      if (x === null || x === undefined || x === "") {
        continue
      }
      any = true
      if (_number(x) === null) {
        allNumbers = false
      }
      if (x instanceof Date === false && (typeof x !== "string" || parseDate(x) === null)) {
        allDates = false
      }
    }
  }
  let kind = "category"
  if (any === false || allNumbers === true) {
    kind = "number"
  } else if (allDates === true) {
    kind = "time"
  }
  return kind
}


function _limitSets(raw, isRunChart) {
  /*
   * The control-limit sets of the data: [{ ucl, lcl, cl, label }] with
   * null for a missing or non-numeric limit.
   */
  const sets = []
  if (isRunChart === true || raw.control_limits === null || raw.control_limits === undefined) {
    return sets
  }
  const list = Array.isArray(raw.control_limits) === true ? raw.control_limits : [raw.control_limits]
  for (let index = 0; index < list.length; index = index + 1) {
    const entry = list[index]
    if (entry === null || typeof entry !== "object") {
      continue
    }
    const set = {
      ucl: _number(entry.ucl),
      lcl: _number(entry.lcl),
      cl: _number(entry.cl),
      label: typeof entry.label === "string" ? entry.label : ""
    }
    if (set.ucl !== null || set.lcl !== null || set.cl !== null) {
      sets.push(set)
    }
  }
  return sets
}


function _autoLimits(values) {
  /*
   * Individuals-chart limits: CL = mean, UCL / LCL = CL +/- 2.66 x the
   * average moving range of consecutive values.
   */
  if (values.length < 2) {
    return null
  }
  let sum = 0
  let rangeSum = 0
  for (let index = 0; index < values.length; index = index + 1) {
    sum = sum + values[index]
    if (index > 0) {
      rangeSum = rangeSum + Math.abs(values[index] - values[index - 1])
    }
  }
  const mean = sum / values.length
  const averageRange = rangeSum / (values.length - 1)
  const limits = {
    ucl: mean + 2.66 * averageRange,
    lcl: mean - 2.66 * averageRange,
    cl: mean,
    label: ""
  }
  return limits
}


function _median(values) {
  /*
   * The median of a list of numbers (null when empty).
   */
  if (values.length === 0) {
    return null
  }
  const sorted = values.slice().sort((a, b) => a - b)
  const middle = Math.floor(sorted.length / 2)
  const median = sorted.length % 2 === 1 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2
  return median
}


function _markShifts(points, median) {
  /*
   * Flag every point in a run of SHIFT_RUN or more consecutive points on
   * one side of the median (points on the median neither break nor extend
   * a run).
   */
  let run = []
  let side = 0
  const flush = () => {
    if (run.length >= SHIFT_RUN) {
      for (let k = 0; k < run.length; k = k + 1) {
        run[k].shift = true
      }
    }
    return
  }
  for (let index = 0; index < points.length; index = index + 1) {
    const point = points[index]
    if (point.y === null || point.y === median) {
      continue
    }
    const pointSide = point.y > median ? 1 : -1
    if (pointSide !== side) {
      flush()
      run = []
      side = pointSide
    }
    run.push(point)
  }
  flush()
  return
}


export function render(ctx) {
  /*
   * Render a control chart or run chart.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const raw = ctx.raw !== null && ctx.raw !== undefined ? ctx.raw : {}
  const isRunChart = ctx.type === "run-chart"
  const root = svgEl("g", { part: "plot" }, [])

  const series = Array.isArray(raw.series) === true
    ? raw.series.filter((entry) => entry !== null && typeof entry === "object") : []
  const refLines = (Array.isArray(raw.reference_lines) === true ? raw.reference_lines : [])
    .filter((entry) => entry !== null && typeof entry === "object" && _number(entry.value) !== null)

  /* Parse the points; x keeps its kind, y is a number or null (a gap). */
  const kind = _xKind(series)
  const categories = []
  const categorySeen = new Set()
  const parsed = []
  for (let s = 0; s < series.length; s = s + 1) {
    const source = Array.isArray(series[s].points) === true ? series[s].points : []
    const points = []
    for (let p = 0; p < source.length; p = p + 1) {
      const point = source[p]
      if (point === null || typeof point !== "object") {
        continue
      }
      let x = null
      if (kind === "number") {
        x = _number(point.x)
      } else if (kind === "time") {
        x = parseDate(point.x)
      } else if (point.x !== null && point.x !== undefined && point.x !== "") {
        x = String(point.x)
        if (categorySeen.has(x) === false) {
          categorySeen.add(x)
          categories.push(x)
        }
      }
      if (x === null) {
        continue
      }
      points.push({ source: point, x: x, y: _number(point.y), ooc: false, shift: false })
    }
    if (kind !== "category") {
      points.sort((a, b) => (kind === "time" ? a.x.getTime() - b.x.getTime() : a.x - b.x))
    }
    parsed.push({ name: series[s].name !== undefined ? String(series[s].name) : `Series ${s + 1}`, points: points })
  }

  /* Limits: the data's, or computed from the first series. */
  const firstValues = parsed.length > 0
    ? parsed[0].points.filter((point) => point.y !== null).map((point) => point.y) : []
  let limitSets = _limitSets(raw, isRunChart)
  const wantsAuto = ctx.attrs("limits", "") === "auto" ||
    raw.control_limits === undefined || raw.control_limits === null
  if (isRunChart === false && wantsAuto === true) {
    const computed = _autoLimits(firstValues)
    if (computed !== null) {
      limitSets = [computed]
    }
  }
  let upper = null
  let lower = null
  for (let l = 0; l < limitSets.length; l = l + 1) {
    if (limitSets[l].ucl !== null) {
      upper = upper === null ? limitSets[l].ucl : Math.max(upper, limitSets[l].ucl)
    }
    if (limitSets[l].lcl !== null) {
      lower = lower === null ? limitSets[l].lcl : Math.min(lower, limitSets[l].lcl)
    }
  }
  const median = isRunChart === true ? _median(firstValues) : null

  /* Flags: beyond the outermost limits, or a shift around the median. */
  let anyOoc = false
  let anyShift = false
  for (let s = 0; s < parsed.length; s = s + 1) {
    for (let p = 0; p < parsed[s].points.length; p = p + 1) {
      const point = parsed[s].points[p]
      const beyond = point.y !== null &&
        ((upper !== null && point.y > upper) || (lower !== null && point.y < lower))
      point.ooc = isRunChart === false && (point.source.ooc === true || beyond === true) && point.y !== null
      if (point.ooc === true) {
        anyOoc = true
      }
    }
    if (median !== null) {
      _markShifts(parsed[s].points, median)
      anyShift = anyShift || parsed[s].points.some((point) => point.shift === true)
    }
  }

  const xText = (x) => {
    let text = String(x)
    if (kind === "time") {
      text = formatDate(x)
    } else if (kind === "number") {
      text = formatNumber(x)
    }
    return text
  }

  ctx.setTable({
    columns: ["Series", "X", "Y", "Status"],
    rows: [].concat(...parsed.map((entry) => entry.points.map((point) => [
      entry.name, xText(point.x), point.y !== null ? point.y : "",
      point.ooc === true ? "out of control" : (point.shift === true ? "shift" : "")
    ])))
  })
  const legend = parsed.map((entry) => ({ label: entry.name, series: entry.name }))
  if (anyOoc === true) {
    legend.push({ label: "Out of control", color: LIMIT_COLOR })
  }
  ctx.setLegend(legend)

  /* Domains. */
  let xMin = Infinity
  let xMax = -Infinity
  let yMin = Infinity
  let yMax = -Infinity
  let pointCount = 0
  for (let s = 0; s < parsed.length; s = s + 1) {
    for (let p = 0; p < parsed[s].points.length; p = p + 1) {
      const point = parsed[s].points[p]
      pointCount = pointCount + 1
      if (kind !== "category") {
        const xValue = kind === "time" ? point.x.getTime() : point.x
        xMin = Math.min(xMin, xValue)
        xMax = Math.max(xMax, xValue)
      }
      if (point.y !== null) {
        yMin = Math.min(yMin, point.y)
        yMax = Math.max(yMax, point.y)
      }
    }
  }
  if (pointCount === 0) {
    return root
  }
  const extras = []
  for (let l = 0; l < limitSets.length; l = l + 1) {
    extras.push(limitSets[l].ucl, limitSets[l].lcl, limitSets[l].cl)
  }
  for (let r = 0; r < refLines.length; r = r + 1) {
    extras.push(_number(refLines[r].value))
  }
  extras.push(median)
  for (let e = 0; e < extras.length; e = e + 1) {
    if (extras[e] !== null) {
      yMin = Math.min(yMin, extras[e])
      yMax = Math.max(yMax, extras[e])
    }
  }
  if (yMin === Infinity) {
    yMin = 0
    yMax = 1
  }
  if (yMin === yMax) {
    yMin = yMin - 1
    yMax = yMax + 1
  }
  const yPad = (yMax - yMin) * 0.05
  const yDomain = niceDomain(yMin - yPad, yMax + yPad, 5)

  const hasRightLabels = limitSets.length > 0 || median !== null
  const margin = { top: 16, right: hasRightLabels === true ? 52 : 16, bottom: 32, left: 52 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  let xScale = null
  if (kind === "category") {
    const inset = categories.length > 1 ? Math.min(plotW / categories.length / 2, 24) : 0
    xScale = pointScale(categories, [inset, plotW - inset])
  } else {
    if (xMin === xMax) {
      const widen = kind === "time" ? 86400000 : 1
      xMin = xMin - widen
      xMax = xMax + widen
    }
    xScale = kind === "time"
      ? timeScale([new Date(xMin), new Date(xMax)], [0, plotW])
      : linearScale([xMin, xMax], [0, plotW])
  }
  const yScale = linearScale(yDomain, [plotH, 0])

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)
  const axis = svgEl("g", { "aria-hidden": "true" }, [])
  const lines = svgEl("g", { "aria-hidden": "true" }, [])
  const marks = svgEl("g", null, [])
  plot.appendChild(axis)
  plot.appendChild(lines)
  plot.appendChild(marks)

  const yTicks = niceTicks(yDomain[0], yDomain[1], 5)
  for (let t = 0; t < yTicks.length; t = t + 1) {
    const y = yScale(yTicks[t])
    axis.appendChild(svgEl("line", {
      x1: 0, y1: y, x2: plotW, y2: y,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    axis.appendChild(svgEl("text", {
      x: -8, y: y + 4, "text-anchor": "end",
      "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
    }, formatNumber(yTicks[t])))
  }

  /* X ticks for the kind of x. */
  const xLabels = []
  if (kind === "category") {
    const maxLabels = Math.max(Math.floor(plotW / 48), 1)
    const every = Math.max(Math.ceil(categories.length / maxLabels), 1)
    for (let c = 0; c < categories.length; c = c + every) {
      xLabels.push({ x: xScale.at(c), text: categories[c] })
    }
  } else if (kind === "time") {
    /* Never more ticks than points, so daily data gets day ticks. */
    let count = Math.max(2, Math.min(Math.floor(plotW / 90), pointCount))
    let ticks = xScale.ticks(count)
    if (ticks.length < 2) {
      /* A coarse calendar interval can miss a short domain: ask finer. */
      count = count * 2
      ticks = xScale.ticks(count)
    }
    const format = xScale.tickFormat(count)
    for (let t = 0; t < ticks.length; t = t + 1) {
      xLabels.push({ x: xScale(ticks[t]), text: format(ticks[t]) })
    }
  } else {
    const ticks = niceTicks(xMin, xMax, Math.max(4, Math.floor(plotW / 70)))
    for (let t = 0; t < ticks.length; t = t + 1) {
      xLabels.push({ x: xScale(ticks[t]), text: formatNumber(ticks[t]) })
    }
  }
  for (let t = 0; t < xLabels.length; t = t + 1) {
    axis.appendChild(svgEl("text", {
      x: xLabels[t].x, y: plotH + 16, "text-anchor": "middle",
      "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
    }, xLabels[t].text))
  }

  /* Control limits: each limit on its own, band only between a pair. */
  const rightLabel = (y, text, color) => {
    const maxChars = Math.max(Math.floor((margin.right - 6) / (10 * CHAR_WIDTH)), 1)
    lines.appendChild(svgEl("text", {
      x: plotW + 4, y: y + 4, "font-size": 10, fill: color
    }, text.length > maxChars ? text.slice(0, maxChars) : text))
    return
  }
  for (let l = 0; l < limitSets.length; l = l + 1) {
    const set = limitSets[l]
    const suffix = set.label !== "" ? ` ${set.label}` : ""
    if (set.ucl !== null && set.lcl !== null) {
      const top = yScale(set.ucl)
      const bottom = yScale(set.lcl)
      lines.appendChild(svgEl("rect", {
        x: 0, y: Math.min(top, bottom), width: plotW, height: Math.abs(bottom - top),
        fill: "var(--mj-accent, #2563eb)", "fill-opacity": 0.05
      }, []))
    }
    const limitLines = [
      { value: set.ucl, name: `UCL${suffix}`, dashed: true },
      { value: set.lcl, name: `LCL${suffix}`, dashed: true },
      { value: set.cl, name: `CL${suffix}`, dashed: false }
    ]
    for (let k = 0; k < limitLines.length; k = k + 1) {
      if (limitLines[k].value === null) {
        continue
      }
      const y = yScale(limitLines[k].value)
      lines.appendChild(svgEl("line", {
        x1: 0, y1: y, x2: plotW, y2: y,
        stroke: limitLines[k].dashed === true ? LIMIT_COLOR : "var(--mj-text-muted, #6b7280)",
        "stroke-width": 1.5, "stroke-dasharray": limitLines[k].dashed === true ? "4 2" : null
      }, []))
      rightLabel(y, limitLines[k].name, "var(--mj-text-muted, #6b7280)")
    }
  }
  if (median !== null) {
    const y = yScale(median)
    lines.appendChild(svgEl("line", {
      x1: 0, y1: y, x2: plotW, y2: y,
      stroke: "var(--mj-text-muted, #6b7280)", "stroke-width": 1.5, "stroke-dasharray": "6 3"
    }, []))
    rightLabel(y, "Median", "var(--mj-text-muted, #6b7280)")
  }
  for (let r = 0; r < refLines.length; r = r + 1) {
    const y = yScale(_number(refLines[r].value))
    lines.appendChild(svgEl("line", {
      x1: 0, y1: y, x2: plotW, y2: y,
      stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5,
      "stroke-dasharray": "6 3"
    }, []))
    lines.appendChild(svgEl("text", {
      x: 4, y: y - 4, "font-size": 10, fill: "var(--mj-text-muted, #6b7280)"
    }, refLines[r].label !== undefined && refLines[r].label !== null ? String(refLines[r].label) : ""))
  }

  const xPixel = (point) => {
    let pixel = 0
    if (kind === "category") {
      pixel = xScale.at(xScale.indexOf(point.x))
    } else {
      pixel = xScale(point.x)
    }
    return pixel
  }

  for (let s = 0; s < parsed.length; s = s + 1) {
    const entry = parsed[s]
    const color = ctx.colorFor(entry.name)
    const pathD = linePath(entry.points.map((point) => ({
      x: xPixel(point), y: point.y !== null ? yScale(point.y) : null
    })))
    if (pathD !== "") {
      lines.appendChild(svgEl("path", {
        d: pathD, fill: "none", stroke: color, "stroke-width": 2
      }, []))
    }

    for (let p = 0; p < entry.points.length; p = p + 1) {
      const point = entry.points[p]
      if (point.y === null) {
        continue
      }
      const px = xPixel(point)
      const py = yScale(point.y)
      let label = `${entry.name}, ${xText(point.x)}: ${formatNumber(point.y)}`
      if (point.ooc === true) {
        label = label + " (out of control)"
      } else if (point.shift === true) {
        label = label + ` (shift: ${SHIFT_RUN}+ points on one side of the median)`
      }

      let mark = null
      if (point.ooc === true) {
        mark = svgEl("polygon", {
          points: `${px},${py - 6} ${px + 6},${py} ${px},${py + 6} ${px - 6},${py}`,
          fill: LIMIT_COLOR, stroke: "var(--mj-surface, #ffffff)", "stroke-width": 1
        }, [])
      } else {
        mark = svgEl("circle", {
          cx: px, cy: py, r: point.shift === true ? 5 : 3.5,
          fill: point.shift === true ? "var(--mj-surface, #ffffff)" : color,
          stroke: color, "stroke-width": point.shift === true ? 2 : 0
        }, [])
      }
      mark.setAttribute("part", "point")
      mark.setAttribute("tabindex", "0")
      mark.setAttribute("role", "img")
      mark.setAttribute("aria-label", label)
      mark.appendChild(svgEl("title", null, label))

      const emitPoint = point
      const handler = () => {
        ctx.emit("mj-chart-point-click", {
          series: entry.name,
          x: emitPoint.source.x,
          y: emitPoint.y,
          ooc: emitPoint.ooc,
          shift: emitPoint.shift
        })
      }
      mark.addEventListener("click", handler)
      mark.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault()
          handler()
        }
      })
      marks.appendChild(mark)
    }
  }
  if (anyShift === true) {
    legend.push({ label: `Shift (${SHIFT_RUN}+ on one side of the median)`, color: "var(--mj-text-muted, #6b7280)" })
    ctx.setLegend(legend)
  }

  axis.appendChild(svgEl("line", {
    x1: 0, y1: plotH, x2: plotW, y2: plotH,
    stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
  }, []))
  axis.appendChild(svgEl("line", {
    x1: 0, y1: 0, x2: 0, y2: plotH,
    stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
  }, []))

  return root
}


registerRenderer("control-chart", render)
registerRenderer("run-chart", render)
