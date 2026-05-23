/*
 * parallel.js
 *
 * Parallel coordinates plot renderer -- compares many numeric dimensions for
 * multiple observations simultaneously. Each dimension has its own independent
 * vertical linear scale sharing the same pixel range. Observations are drawn
 * as polylines crossing all axes left-to-right.
 *
 * A renderer is `render(ctx) -> SVGElement`:
 *   ctx.model       normalized model { meta, categories, series, raw }
 *   ctx.raw         the raw data object (carries `dimensions` field)
 *   ctx.width       drawing surface width (px)
 *   ctx.height      drawing surface height (px)
 *   ctx.orientation n/a -- axes are always vertical
 *   ctx.attrs       (name, fallback) -> controller attribute value
 *   ctx.colorFor    (seriesIndex | seriesName) -> CSS color
 *   ctx.emit        (eventName, detail) -> dispatch an interaction event
 * It returns a <g> SVGElement drawn within [0..width] x [0..height].
 *
 * JSON shape (ctx.raw):
 *   {
 *     "dimensions": [
 *       { "name": "Height", "domain": [0, 200], "unit": "cm" },
 *       ...
 *     ],
 *     "series": [
 *       { "name": "Group A", "color": "optional",
 *         "observations": [[172, 68, 34, 82], [165, 55, 29, 91]] }
 *     ]
 *   }
 *
 * Attributes:
 *   curved       "true" | "false" (default) -- cubic-bezier vs. straight lines
 *   color-by     dimension name -- color lines by value on that dimension
 *
 * Registered type keys: "parallel"
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, formatNumber } from "../svgdraw.js";
import { linearScale, niceTicks } from "../scales.js";


const TICK_COUNT = 5
const TICK_LEN = 5
const AXIS_LABEL_PAD = 16
const PARALLEL_OPACITY_DEFAULT = "var(--mj-chart-parallel-opacity, 0.5)"


function _buildDimScales(dimensions, plotH) {
  /*
   * Build one linear scale per dimension, mapping domain value -> pixel y.
   *
   * :param dimensions: Array of dimension descriptors from raw data.
   * :param plotH: Available plot height in pixels.
   * :returns: Array of linear scale functions.
   */
  const scales = []
  for (let d = 0; d < dimensions.length; d = d + 1) {
    const dim = dimensions[d]
    const domain = Array.isArray(dim.domain) && dim.domain.length >= 2
      ? dim.domain
      : [0, 1]
    const scale = linearScale([domain[0], domain[1]], [plotH, 0])
    scales.push(scale)
  }
  return scales
}


function _observationPath(observations, axisXs, scales, curved) {
  /*
   * Build an SVG path d-string for one observation row.
   *
   * :param observations: Array of numeric values (one per dimension).
   * :param axisXs: Array of x-pixel positions for each axis.
   * :param scales: Array of linear scales (one per dimension).
   * :param curved: Boolean -- use cubic bezier curves if true.
   * :returns: SVG path data string, or empty string on no valid points.
   */
  const points = []
  for (let d = 0; d < observations.length && d < axisXs.length; d = d + 1) {
    const value = observations[d]
    if (typeof value !== "number") {
      continue
    }
    points.push({ x: axisXs[d], y: scales[d](value), dimIndex: d })
  }

  if (points.length === 0) {
    return ""
  }
  if (points.length === 1) {
    return `M${points[0].x.toFixed(2)},${points[0].y.toFixed(2)}`
  }

  let data = `M${points[0].x.toFixed(2)},${points[0].y.toFixed(2)}`

  for (let i = 1; i < points.length; i = i + 1) {
    const prev = points[i - 1]
    const curr = points[i]

    if (curved === true) {
      /* Control points at 1/3 and 2/3 of the horizontal span. */
      const cpX = (curr.x - prev.x) / 3
      const c1x = prev.x + cpX
      const c2x = curr.x - cpX
      data = data + ` C${c1x.toFixed(2)},${prev.y.toFixed(2)} ` +
        `${c2x.toFixed(2)},${curr.y.toFixed(2)} ` +
        `${curr.x.toFixed(2)},${curr.y.toFixed(2)}`
    } else {
      data = data + ` L${curr.x.toFixed(2)},${curr.y.toFixed(2)}`
    }
  }

  return data
}


export function render(ctx) {
  /*
   * Render a parallel coordinates plot.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const raw = ctx.raw
  const root = svgEl("g", { part: "plot" }, [])

  const dimensions = (raw && Array.isArray(raw.dimensions)) ? raw.dimensions : []
  const series = (raw && Array.isArray(raw.series)) ? raw.series : []

  if (dimensions.length === 0 || series.length === 0) {
    return root
  }

  const curved = ctx.attrs("curved", "false") === "true"
  const colorByDim = ctx.attrs("color-by", "")

  /* Find the color-by dimension index if specified. */
  let colorByIndex = -1
  if (colorByDim !== "") {
    for (let d = 0; d < dimensions.length; d = d + 1) {
      if (dimensions[d].name === colorByDim) {
        colorByIndex = d
        break
      }
    }
  }

  const margin = { top: 40, right: 24, bottom: 24, left: 24 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  /* Axis x-positions: evenly spaced. */
  const dimCount = dimensions.length
  const axisXs = []
  for (let d = 0; d < dimCount; d = d + 1) {
    const x = dimCount > 1
      ? (plotW * d) / (dimCount - 1)
      : plotW / 2
    axisXs.push(x)
  }

  const dimScales = _buildDimScales(dimensions, plotH)

  /* Build color-by scale if needed. */
  let colorByScale = null
  if (colorByIndex >= 0) {
    const dim = dimensions[colorByIndex]
    const domain = Array.isArray(dim.domain) && dim.domain.length >= 2
      ? dim.domain
      : [0, 1]
    /* Hue interpolation from token accent to danger across the domain. */
    colorByScale = linearScale([domain[0], domain[1]], [0, 1])
  }

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  /* Count total observations to set line opacity. */
  let totalObs = 0
  for (let s = 0; s < series.length; s = s + 1) {
    const obs = Array.isArray(series[s].observations) ? series[s].observations : []
    totalObs = totalObs + obs.length
  }
  const lineOpacity = totalObs > 500 ? PARALLEL_OPACITY_DEFAULT : "0.7"

  /* Draw observations (polylines) first so axes render on top. */
  for (let s = 0; s < series.length; s = s + 1) {
    const observations = Array.isArray(series[s].observations)
      ? series[s].observations
      : []
    const baseColor = ctx.colorFor(series[s].name)

    for (let o = 0; o < observations.length; o = o + 1) {
      const obs = observations[o]
      const pathD = _observationPath(obs, axisXs, dimScales, curved)
      if (pathD === "") {
        continue
      }

      let lineColor = baseColor
      if (colorByIndex >= 0 && colorByScale !== null &&
          typeof obs[colorByIndex] === "number") {
        /* Simple blue-to-red interpolation via hsl when color-by is active. */
        const fraction = colorByScale(obs[colorByIndex])
        const hue = Math.round(240 - fraction * 240)
        lineColor = `hsl(${hue}, 70%, 50%)`
      }

      const seriesName = series[s].name
      const obsSummary = obs.map((v, i) => {
        const dimName = dimensions[i] ? dimensions[i].name : i
        return `${dimName}:${formatNumber(v)}`
      }).join(", ")

      const path = svgEl("path", {
        d: pathD,
        fill: "none",
        stroke: lineColor,
        "stroke-width": "var(--mj-chart-parallel-line-width, 1.5)",
        "stroke-opacity": lineOpacity,
        "stroke-linecap": "round",
        "stroke-linejoin": "round",
        part: "observation",
        tabindex: "0",
        role: "img",
        "aria-label": `${seriesName}: ${obsSummary}`
      }, [])

      path.appendChild(svgEl("title", null, `${seriesName}: ${obsSummary}`))

      const handler = () => {
        ctx.emit("mj-chart-parallel-click", {
          series: seriesName, observation: obs
        })
      }
      path.addEventListener("click", handler)
      path.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault()
          handler()
        }
      })
      plot.appendChild(path)
    }
  }

  /* Draw axes (vertical lines + tick labels + dimension labels). */
  for (let d = 0; d < dimCount; d = d + 1) {
    const x = axisXs[d]
    const dim = dimensions[d]
    const scale = dimScales[d]
    const domain = scale.domain()

    /* Axis line. */
    plot.appendChild(svgEl("line", {
      x1: x, y1: 0, x2: x, y2: plotH,
      stroke: "var(--mj-border-strong, #c7ccd6)",
      "stroke-width": 1.5
    }, []))

    /* Tick marks and labels. */
    const ticks = niceTicks(domain[0], domain[1], TICK_COUNT)
    for (let t = 0; t < ticks.length; t = t + 1) {
      const tick = ticks[t]
      const y = scale(tick)
      const tickLabel = formatNumber(tick)
      const anchor = d === 0 ? "end" : d === dimCount - 1 ? "start" : "middle"
      const labelX = d === 0 ? x - TICK_LEN - 3
        : d === dimCount - 1 ? x + TICK_LEN + 3
        : x + TICK_LEN + 3

      plot.appendChild(svgEl("line", {
        x1: x - TICK_LEN / 2, y1: y,
        x2: x + TICK_LEN / 2, y2: y,
        stroke: "var(--mj-border-strong, #c7ccd6)",
        "stroke-width": 1
      }, []))
      plot.appendChild(svgEl("text", {
        x: labelX, y: y + 4,
        "text-anchor": anchor,
        "font-size": 10, fill: "var(--mj-text-muted, #6b7280)"
      }, tickLabel))
    }

    /* Dimension label above the axis. */
    const unitSuffix = dim.unit ? ` (${dim.unit})` : ""
    plot.appendChild(svgEl("text", {
      x: x, y: -AXIS_LABEL_PAD + 4,
      "text-anchor": "middle",
      "font-size": 11, "font-weight": "600",
      fill: "var(--mj-text, #14181f)"
    }, escapeHtml(dim.name + unitSuffix)))
  }

  /* Legend -- one entry per series. */
  if (series.length > 1) {
    const legendY = margin.top + plotH + 12
    let legendX = margin.left
    for (let s = 0; s < series.length; s = s + 1) {
      const color = ctx.colorFor(series[s].name)
      root.appendChild(svgEl("rect", {
        x: legendX, y: legendY, width: 10, height: 10,
        fill: color, rx: 2
      }, []))
      root.appendChild(svgEl("text", {
        x: legendX + 14, y: legendY + 9,
        "font-size": 11, fill: "var(--mj-text, #14181f)"
      }, escapeHtml(series[s].name)))
      legendX = legendX + 14 + series[s].name.length * 7 + 12
    }
  }

  return root
}


registerRenderer("parallel", render);
