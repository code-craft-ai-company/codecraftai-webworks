/*
 * beeswarm.js
 *
 * Beeswarm plot renderer — individual observations as non-overlapping
 * dots along one value axis; the cross axis carries no meaning. Uses the
 * same placement routine as the swarm type (diststats.placeSwarm).
 *
 * Registered types:
 *   "beeswarm"
 *
 * Data shape:
 *   series[]   [{ name, points: [{ x?, y?, label? }] }] -- `x` values for a
 *              horizontal swarm (picked automatically when the data has
 *              only x), `y` values for a vertical one; non-finite values
 *              are missing data
 *   radius     dot radius in px (default 4; the `radius` attribute wins)
 *   padding    gap between dots in px (default 1; `padding` attribute wins)
 *
 * Relevant ctx.attrs:
 *   radius, padding   as above
 *   mode              "beeswarm" (default) | "strip" (no collision avoidance)
 *   show-median       boolean, default on (show-median="false" hides it) — a dashed median line per
 *                     series
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber } from "../svgdraw.js";
import { linearScale } from "../scales.js";
import {
  isFiniteNumber, sortNumbers, quantileSorted, placeSwarm, swarmRadius, axisLayer, drawTicks,
  tickCount, activateOnKey, focusableMark, fitDomain
} from "./diststats.js";
import { booleanOption } from "../chartoptions.js";

const MIN_RADIUS = 1.5;


function _numberOption(ctx, name, rawValue, fallback) {
  /*
   * A positive number from the host attribute, else from the data, else
   * the fallback.
   */
  const fromAttr = parseFloat(ctx.attrs(name, ""))
  if (isFiniteNumber(fromAttr) === true && fromAttr >= 0) {
    return fromAttr
  }
  if (isFiniteNumber(rawValue) === true && rawValue >= 0) {
    return rawValue
  }
  return fallback
}


function _axisOf(ctx, series) {
  /*
   * True for a horizontal swarm (values on x). An explicit orientation
   * wins; otherwise the axis the data carries values for.
   */
  if (ctx.orientation === "horizontal") {
    return true
  }
  let sawX = false
  let sawY = false
  for (let si = 0; si < series.length; si = si + 1) {
    const points = Array.isArray(series[si].points) === true ? series[si].points : []
    for (let pi = 0; pi < points.length; pi = pi + 1) {
      const point = points[pi]
      if (point === null || typeof point !== "object") {
        continue
      }
      if (isFiniteNumber(point.x) === true) {
        sawX = true
      }
      if (isFiniteNumber(point.y) === true) {
        sawY = true
      }
    }
  }
  return sawX === true && sawY === false
}


export function render(ctx) {
  /*
   * Render a beeswarm plot.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const raw = ctx.raw !== null && ctx.raw !== undefined ? ctx.raw : {}
  const root = svgEl("g", { part: "plot" }, [])
  const series = Array.isArray(ctx.model.series) === true ? ctx.model.series : []
  if (series.length === 0) {
    return root
  }

  const horizontal = _axisOf(ctx, series)
  const mode = ctx.attrs("mode", "beeswarm")
  const showMedian = booleanOption(ctx, "show-median", true)
  const radius = Math.max(_numberOption(ctx, "radius", raw.radius, 4), MIN_RADIUS)
  const padding = _numberOption(ctx, "padding", raw.padding, 1)

  /* Every dot with a finite value on the value axis. */
  const dots = []
  for (let si = 0; si < series.length; si = si + 1) {
    const points = Array.isArray(series[si].points) === true ? series[si].points : []
    for (let pi = 0; pi < points.length; pi = pi + 1) {
      const point = points[pi]
      if (point === null || typeof point !== "object") {
        continue
      }
      const value = horizontal === true ? point.x : point.y
      if (isFiniteNumber(value) === false) {
        continue
      }
      const label = point.label !== null && point.label !== undefined ? String(point.label) : ""
      dots.push({ seriesIndex: si, value: value, label: label })
    }
  }
  if (dots.length === 0) {
    return root
  }

  const margin = { top: 16, right: 16, bottom: 36, left: 52 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)
  let low = Infinity
  let high = -Infinity
  for (let di = 0; di < dots.length; di = di + 1) {
    low = Math.min(low, dots[di].value)
    high = Math.max(high, dots[di].value)
  }
  const valueLength = horizontal === true ? plotW : plotH
  const valueCount = tickCount(valueLength, horizontal === true ? 70 : 40)
  const pad = (high - low) * 0.04
  const domain = fitDomain(low - pad, high + pad, valueCount)
  const valueScale = horizontal === true
    ? linearScale(domain, [0, plotW])
    : linearScale(domain, [plotH, 0])
  const crossLength = horizontal === true ? plotH : plotW
  const center = crossLength / 2

  const plot = svgEl("g", { transform: `translate(${margin.left},${margin.top})` }, [])
  root.appendChild(plot)
  const axes = axisLayer(plot)
  if (horizontal === true) {
    drawTicks(axes, valueScale, { side: "bottom", extent: plotH, count: valueCount })
  } else {
    drawTicks(axes, valueScale, { side: "left", extent: plotW, count: valueCount })
  }

  /* Placement. */
  const positions = dots.map((dot) => valueScale(dot.value))
  let dotRadius = radius
  let offsets = null
  if (mode === "strip") {
    offsets = positions.map(() => 0)
  } else {
    const maxOffset = Math.max(center - radius, 0)
    dotRadius = swarmRadius(positions, radius, padding, maxOffset, MIN_RADIUS)
    offsets = placeSwarm(positions, dotRadius * 2 + padding, Math.max(center - dotRadius, 0)).offsets
  }

  /* Median per series (the mean of the two middle values for even n). */
  if (showMedian === true) {
    for (let si = 0; si < series.length; si = si + 1) {
      const values = sortNumbers(dots.filter((dot) => dot.seriesIndex === si).map((dot) => dot.value))
      if (values.length === 0) {
        continue
      }
      const pixel = valueScale(quantileSorted(values, 0.5))
      const color = ctx.colorFor(series[si].name)
      axes.appendChild(svgEl("line", {
        x1: horizontal === true ? pixel : 4, y1: horizontal === true ? 4 : pixel,
        x2: horizontal === true ? pixel : plotW - 4, y2: horizontal === true ? plotH - 4 : pixel,
        stroke: color, "stroke-width": 1.5, "stroke-dasharray": "4 3", part: "median-line"
      }, []))
    }
  }

  const marks = svgEl("g", { part: "marks" }, [])
  plot.appendChild(marks)
  const rows = []
  for (let di = 0; di < dots.length; di = di + 1) {
    const dot = dots[di]
    const name = series[dot.seriesIndex].name
    const along = positions[di]
    const across = center + offsets[di]
    const circle = svgEl("circle", {
      cx: horizontal === true ? along : across,
      cy: horizontal === true ? across : along,
      r: dotRadius, fill: ctx.colorFor(name), "fill-opacity": 0.85
    }, [])
    circle.setAttribute("part", "dot")
    const labelText = dot.label.length > 0 && dot.label !== name ? `${dot.label} — ` : ""
    focusableMark(circle, `${labelText}${name}: ${formatNumber(dot.value)}`)
    activateOnKey(circle, () => {
      ctx.emit("mj-chart-dot-click", { series: name, value: dot.value, label: dot.label })
    })
    marks.appendChild(circle)
    rows.push([name, dot.label, dot.value])
  }

  ctx.setTable({ columns: ["Series", "Label", "Value"], rows: rows, caption: "Observations" })
  return root
}


function _isEmpty(model) {
  /*
   * True when no series point has a finite x or y.
   */
  const series = Array.isArray(model.allSeries) === true ? model.allSeries : []
  for (let si = 0; si < series.length; si = si + 1) {
    const points = Array.isArray(series[si].points) === true ? series[si].points : []
    for (let pi = 0; pi < points.length; pi = pi + 1) {
      const point = points[pi]
      if (point !== null && typeof point === "object" &&
          (isFiniteNumber(point.x) === true || isFiniteNumber(point.y) === true)) {
        return false
      }
    }
  }
  return true
}


registerRenderer("beeswarm", render, { isEmpty: _isEmpty })
