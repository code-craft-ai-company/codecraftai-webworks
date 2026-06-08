/*
 * slope.js
 *
 * Slope chart renderer -- shows the direction and magnitude of change for
 * multiple entities between exactly two time points or states. Both columns
 * share a single linear value scale so slopes are visually accurate.
 * Endpoint labels are right-aligned on the left column and left-aligned on
 * the right column. Simple vertical nudging avoids label overlap.
 *
 * A renderer is `render(ctx) -> SVGElement`:
 *   ctx.model       normalized model { meta, categories, series, raw }
 *   ctx.raw         the raw data object
 *   ctx.width       drawing surface width (px)
 *   ctx.height      drawing surface height (px)
 *   ctx.orientation n/a -- always left-column to right-column
 *   ctx.attrs       (name, fallback) -> controller attribute value
 *   ctx.colorFor    (seriesIndex | seriesName) -> CSS color
 *   ctx.emit        (eventName, detail) -> dispatch an interaction event
 * It returns a <g> SVGElement drawn within [0..width] x [0..height].
 *
 * JSON shape:
 *   categories: exactly two entries (the two column headers)
 *   series: [{ "name": "Entity", "values": [leftVal, rightVal] }]
 *
 * Registered type keys: "slope"
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, formatNumber } from "../svgdraw.js";
import { linearScale, niceTicks } from "../scales.js";


const LABEL_MIN_GAP = 13  /* minimum vertical px between adjacent endpoint labels */


function _nudgeLabels(positions) {
  /*
   * Adjust an array of {y, label} objects upward/downward so that no two
   * labels are closer than LABEL_MIN_GAP pixels. Modifies positions in place.
   *
   * :param positions: Array of {y, label} objects sorted by y ascending.
   */
  for (let pass = 0; pass < positions.length; pass = pass + 1) {
    for (let i = 1; i < positions.length; i = i + 1) {
      const prev = positions[i - 1]
      const curr = positions[i]
      const gap = curr.y - prev.y
      if (gap < LABEL_MIN_GAP) {
        const shift = (LABEL_MIN_GAP - gap) / 2
        prev.y = prev.y - shift
        curr.y = curr.y + shift
      }
    }
  }
  return
}


export function render(ctx) {
  /*
   * Render a slope chart.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const model = ctx.model
  const root = svgEl("g", { part: "plot" }, [])

  const categories = model.categories
  const series = model.series

  if (series.length === 0) {
    return root
  }

  /* Use at most two columns even if more categories are given. */
  const leftLabel = categories.length > 0 ? categories[0] : ""
  const rightLabel = categories.length > 1 ? categories[1] : ""

  const margin = { top: 32, right: 80, bottom: 24, left: 80 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  /* Build shared value domain across all first and second values. */
  let valueMin = Infinity
  let valueMax = -Infinity
  for (let s = 0; s < series.length; s = s + 1) {
    const leftVal = series[s].values[0]
    const rightVal = series[s].values[1]
    if (typeof leftVal === "number") {
      if (leftVal < valueMin) {
        valueMin = leftVal
      }
      if (leftVal > valueMax) {
        valueMax = leftVal
      }
    }
    if (typeof rightVal === "number") {
      if (rightVal < valueMin) {
        valueMin = rightVal
      }
      if (rightVal > valueMax) {
        valueMax = rightVal
      }
    }
  }
  if (valueMin === Infinity) {
    valueMin = 0
  }
  if (valueMax === -Infinity) {
    valueMax = 1
  }
  if (valueMax === valueMin) {
    valueMax = valueMin + 1
  }

  /* Pad the domain slightly so endpoint dots are not clipped. */
  const pad = (valueMax - valueMin) * 0.05
  valueMin = valueMin - pad
  valueMax = valueMax + pad

  const val = linearScale([valueMin, valueMax], [plotH, 0])

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  /* Column axis lines. */
  plot.appendChild(svgEl("line", {
    x1: 0, y1: 0, x2: 0, y2: plotH,
    stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
  }, []))
  plot.appendChild(svgEl("line", {
    x1: plotW, y1: 0, x2: plotW, y2: plotH,
    stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
  }, []))

  /* Column header labels. */
  plot.appendChild(svgEl("text", {
    x: 0, y: -12, "text-anchor": "middle",
    "font-size": 12, "font-weight": "600",
    fill: "var(--mj-text, #14181f)"
  }, escapeHtml(leftLabel)))
  plot.appendChild(svgEl("text", {
    x: plotW, y: -12, "text-anchor": "middle",
    "font-size": 12, "font-weight": "600",
    fill: "var(--mj-text, #14181f)"
  }, escapeHtml(rightLabel)))

  /* Optional light horizontal gridlines. */
  const ticks = niceTicks(valueMin, valueMax, 5)
  for (let t = 0; t < ticks.length; t = t + 1) {
    const y = val(ticks[t])
    plot.appendChild(svgEl("line", {
      x1: 0, y1: y, x2: plotW, y2: y,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
  }

  /* Collect endpoint positions for label nudging. */
  const leftPositions = []
  const rightPositions = []
  for (let s = 0; s < series.length; s = s + 1) {
    const leftVal = series[s].values[0]
    const rightVal = series[s].values[1]
    if (typeof leftVal === "number") {
      leftPositions.push({ y: val(leftVal), label: series[s].name, value: leftVal, index: s })
    }
    if (typeof rightVal === "number") {
      rightPositions.push({ y: val(rightVal), label: series[s].name, value: rightVal, index: s })
    }
  }

  leftPositions.sort((a, b) => a.y - b.y)
  rightPositions.sort((a, b) => a.y - b.y)
  _nudgeLabels(leftPositions)
  _nudgeLabels(rightPositions)

  /* Draw slope lines. */
  for (let s = 0; s < series.length; s = s + 1) {
    const leftVal = series[s].values[0]
    const rightVal = series[s].values[1]
    if (typeof leftVal !== "number" || typeof rightVal !== "number") {
      continue
    }
    const y1 = val(leftVal)
    const y2 = val(rightVal)
    const color = ctx.colorFor(series[s].name)

    const line = svgEl("line", {
      x1: 0, y1: y1, x2: plotW, y2: y2,
      stroke: color,
      "stroke-width": "var(--mj-chart-slope-width, 2)",
      "stroke-linecap": "round",
      part: "slope-line",
      tabindex: "0",
      role: "img",
      "aria-label": `${series[s].name}: ${formatNumber(leftVal)} to ${formatNumber(rightVal)}`
    }, [])

    line.appendChild(svgEl("title", null,
      `${series[s].name}: ${formatNumber(leftVal)} → ${formatNumber(rightVal)}`))

    const handler = () => {
      ctx.emit("mj-chart-slope-click", {
        series: series[s].name,
        leftValue: leftVal,
        rightValue: rightVal
      })
    }
    line.addEventListener("click", handler)
    line.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault()
        handler()
      }
    })
    plot.appendChild(line)
  }

  /* Draw endpoint dots. */
  const DOT_R = 5
  for (let s = 0; s < series.length; s = s + 1) {
    const leftVal = series[s].values[0]
    const rightVal = series[s].values[1]
    const color = ctx.colorFor(series[s].name)

    if (typeof leftVal === "number") {
      plot.appendChild(svgEl("circle", {
        cx: 0, cy: val(leftVal), r: DOT_R,
        fill: color
      }, []))
    }
    if (typeof rightVal === "number") {
      plot.appendChild(svgEl("circle", {
        cx: plotW, cy: val(rightVal), r: DOT_R,
        fill: color
      }, []))
    }
  }

  /* Endpoint labels (nudged). */
  const LABEL_PAD = 10
  for (let i = 0; i < leftPositions.length; i = i + 1) {
    const pos = leftPositions[i]
    const color = ctx.colorFor(pos.label)
    plot.appendChild(svgEl("text", {
      x: -LABEL_PAD, y: pos.y + 4, "text-anchor": "end",
      "font-size": 11, fill: color
    }, `${escapeHtml(pos.label)} ${formatNumber(pos.value)}`))
  }
  for (let i = 0; i < rightPositions.length; i = i + 1) {
    const pos = rightPositions[i]
    const color = ctx.colorFor(pos.label)
    plot.appendChild(svgEl("text", {
      x: plotW + LABEL_PAD, y: pos.y + 4, "text-anchor": "start",
      "font-size": 11, fill: color
    }, `${formatNumber(pos.value)} ${escapeHtml(pos.label)}`))
  }

  return root
}


registerRenderer("slope", render);
