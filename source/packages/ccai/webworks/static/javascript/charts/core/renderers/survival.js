/*
 * survival.js
 *
 * Survival curve / Kaplan-Meier renderer.
 *
 * Registers: "survival", "kaplan-meier"
 *
 * JSON shape (ctx.raw):
 *   series: [{
 *     name,
 *     points: [{ x, y, censored?, ci_lower?, ci_upper?, at_risk? }]
 *   }]
 *
 *   x          — time: a number, or a date ("YYYY-MM-DD" is a local day)
 *   y          — survival probability, 0-1 (or 0-100: a series whose values
 *                go above 1 is read as percent)
 *   censored   — true marks a censored observation (a tick, no step)
 *   ci_lower   — lower confidence bound (shown with ci="true")
 *   ci_upper   — upper confidence bound
 *   at_risk    — number at risk (numbers-at-risk table, tooltips)
 *
 * The curve is a right-continuous step function: it holds each value until
 * the next event and continues to the last observation of the series,
 * censored ones included. Every event time is a focusable mark that reads
 * out S(t), the confidence interval and the number at risk.
 *
 * Options:
 *   ci                 shade the confidence band (stepped like the curve)
 *   at-risk            numbers-at-risk table under the plot
 *   mode="cumulative"  draw the cumulative incidence 1 - S(t) instead
 *
 * Events:
 *   mj-chart-point-click { series, x, y, censored, at_risk }
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber, formatDate, parseDate } from "../svgdraw.js";
import { linearScale, timeScale, niceTicks } from "../scales.js";
import { booleanOption } from "../chartoptions.js";


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


function _readSeries(rawSeries, timeAxis, cumulative) {
  /*
   * Parse the series into sorted points with probabilities in 0-1.
   *
   * :returns: [{ name, points: [{ source, t, y, lower, upper, atRisk,
   *     censored }] }] where `t` is a number (epoch ms on a time axis).
   */
  const result = []
  const list = Array.isArray(rawSeries) === true ? rawSeries : []
  for (let s = 0; s < list.length; s = s + 1) {
    const entry = list[s]
    if (entry === null || typeof entry !== "object") {
      continue
    }
    const source = Array.isArray(entry.points) === true ? entry.points : []
    const points = []
    let percent = false
    for (let p = 0; p < source.length; p = p + 1) {
      const y = source[p] !== null && typeof source[p] === "object" ? _number(source[p].y) : null
      if (y !== null && y > 1 + 1e-9) {
        percent = true
      }
    }
    const scaleDown = percent === true ? 100 : 1
    const toProbability = (value) => {
      if (value === null) {
        return null
      }
      const probability = Math.min(Math.max(value / scaleDown, 0), 1)
      return cumulative === true ? 1 - probability : probability
    }
    for (let p = 0; p < source.length; p = p + 1) {
      const point = source[p]
      if (point === null || typeof point !== "object") {
        continue
      }
      let t = null
      if (timeAxis === true) {
        const date = parseDate(point.x)
        t = date !== null ? date.getTime() : null
      } else {
        t = _number(point.x)
      }
      if (t === null) {
        continue
      }
      let lower = toProbability(_number(point.ci_lower))
      let upper = toProbability(_number(point.ci_upper))
      if (cumulative === true && lower !== null && upper !== null) {
        const swap = lower
        lower = Math.min(swap, upper)
        upper = Math.max(swap, upper)
      }
      points.push({
        source: point,
        t: t,
        y: toProbability(_number(point.y)),
        lower: lower,
        upper: upper,
        atRisk: _number(point.at_risk),
        censored: point.censored === true
      })
    }
    points.sort((a, b) => a.t - b.t)
    result.push({ name: entry.name !== undefined ? String(entry.name) : `Series ${s + 1}`, points: points })
  }
  return result
}


function _steps(points, start) {
  /*
   * The step function of a series: [{ t, y, lower, upper, point }], one
   * entry per event (a non-censored point with a value), starting at
   * `start` (1 for survival, 0 for cumulative incidence) when the series
   * does not begin with an event.
   */
  const steps = []
  for (let p = 0; p < points.length; p = p + 1) {
    const point = points[p]
    if (point.censored === true || point.y === null) {
      continue
    }
    steps.push({ t: point.t, y: point.y, lower: point.lower, upper: point.upper, point: point })
  }
  if (steps.length === 0 && points.length > 0) {
    steps.push({ t: points[0].t, y: start, lower: null, upper: null, point: null })
  } else if (steps.length > 0 && points.length > 0 && points[0].t < steps[0].t) {
    steps.unshift({ t: points[0].t, y: start, lower: null, upper: null, point: null })
  }
  return steps
}


function _valueAt(steps, t) {
  /*
   * S(t) of a step function: the value of the last step at or before t.
   */
  let value = steps.length > 0 ? steps[0].y : null
  for (let index = 0; index < steps.length; index = index + 1) {
    if (steps[index].t <= t) {
      value = steps[index].y
    }
  }
  return value
}


function _stepPath(steps, lastT, xScale, yScale, key) {
  /*
   * Path data of a right-continuous step function (key "y", "lower" or
   * "upper") from its first step to lastT. A step without that value
   * keeps the previous level.
   */
  let d = ""
  let level = null
  for (let index = 0; index < steps.length; index = index + 1) {
    const value = steps[index][key]
    const x = xScale(steps[index].t).toFixed(2)
    if (value === null || value === undefined) {
      if (level !== null) {
        d = d + ` H${x}`
      }
      continue
    }
    const y = yScale(value).toFixed(2)
    d = level === null ? `M${x},${y}` : d + ` H${x} V${y}`
    level = value
  }
  if (level !== null) {
    d = d + ` H${xScale(lastT).toFixed(2)}`
  }
  return d
}


function _bandPath(steps, lastT, xScale, yScale) {
  /*
   * Closed path of the confidence band: the stepped upper bound forward,
   * then the stepped lower bound back (H then V, the mirror of the forward
   * walk), both carried to lastT.
   */
  const usable = steps.filter((step) => step.lower !== null && step.upper !== null)
  if (usable.length === 0) {
    return ""
  }
  let d = `M${xScale(usable[0].t).toFixed(2)},${yScale(usable[0].upper).toFixed(2)}`
  for (let index = 1; index < usable.length; index = index + 1) {
    d = d + ` H${xScale(usable[index].t).toFixed(2)} V${yScale(usable[index].upper).toFixed(2)}`
  }
  d = d + ` H${xScale(lastT).toFixed(2)}`
  d = d + ` V${yScale(usable[usable.length - 1].lower).toFixed(2)}`
  for (let index = usable.length - 1; index >= 1; index = index - 1) {
    d = d + ` H${xScale(usable[index].t).toFixed(2)} V${yScale(usable[index - 1].lower).toFixed(2)}`
  }
  d = d + ` H${xScale(usable[0].t).toFixed(2)} Z`
  return d
}


function _attachActivation(element, handler) {
  /*
   * Click and Enter / Space activation of a focusable mark.
   */
  element.addEventListener("click", handler)
  element.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault()
      handler()
    }
  })
  return
}


export function render(ctx) {
  /*
   * Render a survival or Kaplan-Meier curve.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const raw = ctx.raw !== null && ctx.raw !== undefined ? ctx.raw : {}
  const showCI = booleanOption(ctx, "ci", false)
  const showAtRisk = booleanOption(ctx, "at-risk", false)
  const cumulative = ctx.attrs("mode", "") === "cumulative"
  const yName = cumulative === true ? "Cumulative incidence" : "Survival probability"
  const yShort = cumulative === true ? "1 - S(t)" : "S(t)"

  const root = svgEl("g", { part: "plot" }, [])

  /* A time axis when the x values are dates rather than numbers. */
  let anyX = false
  let allNumbers = true
  const rawSeries = Array.isArray(raw.series) === true ? raw.series : []
  for (let s = 0; s < rawSeries.length; s = s + 1) {
    const points = rawSeries[s] !== null && Array.isArray(rawSeries[s].points) === true ? rawSeries[s].points : []
    for (let p = 0; p < points.length; p = p + 1) {
      const x = points[p] !== null && typeof points[p] === "object" ? points[p].x : null
      if (x !== null && x !== undefined && x !== "") {
        anyX = true
        if (_number(x) === null) {
          allNumbers = false
        }
      }
    }
  }
  const timeAxis = anyX === true && allNumbers === false
  const series = _readSeries(rawSeries, timeAxis, cumulative)
  const timeText = (t) => (timeAxis === true ? formatDate(new Date(t)) : formatNumber(t))

  ctx.setTable({
    columns: ["Series", "Time", yShort, "CI lower", "CI upper", "At risk", "Censored"],
    rows: [].concat(...series.map((entry) => entry.points.map((point) => [
      entry.name, timeText(point.t), point.y !== null ? point.y : "",
      point.lower !== null ? point.lower : "", point.upper !== null ? point.upper : "",
      point.atRisk !== null ? point.atRisk : "", point.censored === true ? "yes" : ""
    ])))
  })
  ctx.setLegend(series.map((entry) => ({ label: entry.name, series: entry.name })))

  let xMin = Infinity
  let xMax = -Infinity
  for (let s = 0; s < series.length; s = s + 1) {
    for (let p = 0; p < series[s].points.length; p = p + 1) {
      xMin = Math.min(xMin, series[s].points[p].t)
      xMax = Math.max(xMax, series[s].points[p].t)
    }
  }
  if (xMin === Infinity) {
    return root
  }
  if (xMin === xMax) {
    xMax = xMin + (timeAxis === true ? 86400000 : 1)
  }

  let longestName = 0
  for (let s = 0; s < series.length; s = s + 1) {
    longestName = Math.max(longestName, series[s].name.length * 10 * CHAR_WIDTH)
  }
  const rowH = 14
  const atRiskH = showAtRisk === true ? 22 + series.length * rowH : 0
  const left = showAtRisk === true
    ? Math.min(Math.max(longestName + 34, 56), Math.max(ctx.width * 0.3, 56))
    : 56
  const margin = { top: 16, right: 20, bottom: 44 + atRiskH, left: left }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  const xScale = timeAxis === true
    ? timeScale([new Date(xMin), new Date(xMax)], [0, plotW])
    : linearScale([xMin, xMax], [0, plotW])
  const yScale = linearScale([0, 1], [plotH, 0])

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)
  const axis = svgEl("g", { "aria-hidden": "true" }, [])
  const curves = svgEl("g", { "aria-hidden": "true" }, [])
  const marks = svgEl("g", null, [])
  plot.appendChild(axis)
  plot.appendChild(curves)
  plot.appendChild(marks)

  const yTicks = niceTicks(0, 1, 5)
  for (let t = 0; t < yTicks.length; t = t + 1) {
    const y = yScale(yTicks[t])
    axis.appendChild(svgEl("line", {
      x1: 0, y1: y, x2: plotW, y2: y,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    axis.appendChild(svgEl("text", {
      x: -8, y: y + 4, "text-anchor": "end",
      "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
    }, formatNumber(yTicks[t], { maximumFractionDigits: 2 })))
  }

  let xTicks = []
  let xFormat = (value) => formatNumber(value)
  let tickCount = Math.max(4, Math.floor(plotW / 70))
  if (timeAxis === true) {
    xTicks = xScale.ticks(tickCount).map((date) => date.getTime())
    if (xTicks.length < 2) {
      /* A coarse calendar interval can miss a short domain: ask finer. */
      tickCount = tickCount * 2
      xTicks = xScale.ticks(tickCount).map((date) => date.getTime())
    }
    const format = xScale.tickFormat(tickCount)
    xFormat = (value) => format(new Date(value))
  } else {
    xTicks = niceTicks(xMin, xMax, tickCount)
  }
  for (let t = 0; t < xTicks.length; t = t + 1) {
    axis.appendChild(svgEl("text", {
      x: xScale(xTicks[t]), y: plotH + 16, "text-anchor": "middle",
      "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
    }, xFormat(xTicks[t])))
  }
  axis.appendChild(svgEl("text", {
    x: plotW / 2, y: plotH + 34, "text-anchor": "middle",
    "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
  }, "Time"))
  axis.appendChild(svgEl("text", {
    transform: `translate(-40,${plotH / 2}) rotate(-90)`, "text-anchor": "middle",
    "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
  }, yName))

  for (let s = 0; s < series.length; s = s + 1) {
    const entry = series[s]
    const color = ctx.colorFor(entry.name)
    if (entry.points.length === 0) {
      continue
    }
    const steps = _steps(entry.points, cumulative === true ? 0 : 1)
    const lastT = entry.points[entry.points.length - 1].t

    if (showCI === true) {
      const bandD = _bandPath(steps, lastT, xScale, yScale)
      if (bandD !== "") {
        curves.appendChild(svgEl("path", { d: bandD, fill: color, "fill-opacity": 0.15 }, []))
      }
    }
    const stepD = _stepPath(steps, lastT, xScale, yScale, "y")
    if (stepD !== "") {
      curves.appendChild(svgEl("path", {
        d: stepD, fill: "none", stroke: color, "stroke-width": 2
      }, []))
    }

    /* Event marks: focusable, read out S(t), the CI and the number at risk. */
    for (let index = 0; index < steps.length; index = index + 1) {
      const step = steps[index]
      if (step.point === null) {
        continue
      }
      let label = `${entry.name}: ${yShort} = ${formatNumber(step.y, { maximumFractionDigits: 3 })} at ${timeText(step.t)}`
      if (step.lower !== null && step.upper !== null) {
        label = label + `, CI ${formatNumber(step.lower, { maximumFractionDigits: 3 })}–` +
          `${formatNumber(step.upper, { maximumFractionDigits: 3 })}`
      }
      if (step.point.atRisk !== null) {
        label = label + `, ${formatNumber(step.point.atRisk)} at risk`
      }
      const hit = svgEl("circle", {
        cx: xScale(step.t), cy: yScale(step.y), r: 4,
        fill: color, "fill-opacity": 0, stroke: "none",
        part: "event", tabindex: "0", role: "img", "aria-label": label
      }, [])
      hit.appendChild(svgEl("title", null, label))
      const emitStep = step
      _attachActivation(hit, () => {
        ctx.emit("mj-chart-point-click", {
          series: entry.name, x: emitStep.point.source.x, y: emitStep.point.source.y,
          censored: false, at_risk: emitStep.point.atRisk
        })
      })
      marks.appendChild(hit)
    }

    /* Censored ticks sit on the curve at their time. */
    for (let p = 0; p < entry.points.length; p = p + 1) {
      const point = entry.points[p]
      if (point.censored !== true) {
        continue
      }
      const level = _valueAt(steps, point.t)
      if (level === null) {
        continue
      }
      const px = xScale(point.t)
      const py = yScale(level)
      const label = `${entry.name}: censored at ${timeText(point.t)}, ${yShort} = ` +
        `${formatNumber(level, { maximumFractionDigits: 3 })}`
      const tick = svgEl("line", {
        x1: px, y1: py - 6, x2: px, y2: py + 6,
        stroke: color, "stroke-width": 1.5,
        part: "censor-tick", tabindex: "0", role: "img", "aria-label": label
      }, [])
      tick.appendChild(svgEl("title", null, label))
      const emitPoint = point
      _attachActivation(tick, () => {
        ctx.emit("mj-chart-point-click", {
          series: entry.name, x: emitPoint.source.x, y: level, censored: true,
          at_risk: emitPoint.atRisk
        })
      })
      marks.appendChild(tick)
    }
  }

  /* Numbers-at-risk table under the x axis. */
  if (showAtRisk === true) {
    const tableTop = plotH + 52
    axis.appendChild(svgEl("text", {
      x: -margin.left + 4, y: tableTop, "font-size": 10, "font-weight": "bold",
      fill: "var(--mj-text, #14181f)"
    }, "Number at risk"))
    for (let s = 0; s < series.length; s = s + 1) {
      const entry = series[s]
      const rowY = tableTop + (s + 1) * rowH
      const maxChars = Math.max(Math.floor((margin.left - 34) / (10 * CHAR_WIDTH)), 2)
      const name = entry.name.length > maxChars ? entry.name.slice(0, maxChars - 1) + "…" : entry.name
      axis.appendChild(svgEl("rect", {
        x: -margin.left + 4, y: rowY - 8, width: 8, height: 8, fill: ctx.colorFor(entry.name)
      }, []))
      axis.appendChild(svgEl("text", {
        x: -18, y: rowY, "text-anchor": "end",
        "font-size": 10, fill: "var(--mj-text, #14181f)"
      }, name))
      for (let t = 0; t < xTicks.length; t = t + 1) {
        let atRisk = ""
        for (let p = entry.points.length - 1; p >= 0; p = p - 1) {
          if (entry.points[p].t <= xTicks[t] && entry.points[p].atRisk !== null) {
            atRisk = formatNumber(entry.points[p].atRisk)
            break
          }
        }
        axis.appendChild(svgEl("text", {
          x: xScale(xTicks[t]), y: rowY, "text-anchor": "middle",
          "font-size": 10, fill: "var(--mj-text-muted, #6b7280)"
        }, atRisk))
      }
    }
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


registerRenderer("survival", render)
registerRenderer("kaplan-meier", render)
