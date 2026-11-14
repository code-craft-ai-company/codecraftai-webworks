/*
 * slope.js
 *
 * Slope chart renderer -- shows the direction and magnitude of change for
 * multiple entities between exactly two time points or states. Both columns
 * share a single linear value scale so slopes are visually accurate.
 * Endpoint labels ("name value") are right-aligned on the left column and
 * left-aligned on the right column; the side gutters are as wide as the
 * longest label (shortened with an ellipsis past a third of the width).
 * Labels that would overlap are nudged apart, staying inside the plot, and
 * a nudged label is joined to its dot by a short leader. Label text uses
 * the text colour; the dot beside it carries the series colour.
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
 * More than two categories (or more than two values without categories) is
 * an error -- the chart shows the render error and emits mj-chart-error;
 * use a line chart for three or more periods.
 *
 * Registered type keys: "slope"
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber } from "../svgdraw.js";
import { linearScale, niceTicks } from "../scales.js";
import { LABEL_FONT_SIZE, textWidth, truncateText, numericValue, nudgeLabels, activate } from "./bar.js";

/* Minimum vertical px between adjacent endpoint labels. */
const LABEL_MIN_GAP = 13;
const LABEL_PAD = 10;
const DOT_R = 5;


export function render(ctx) {
  /*
   * Render a slope chart.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   * :raises: Error when the data has more than two periods.
   */
  const model = ctx.model
  const root = svgEl("g", { part: "plot" }, [])

  const categories = model.categories
  const series = model.series
  if (series.length === 0) {
    return root
  }

  let periods = categories.length
  if (periods === 0) {
    for (let s = 0; s < series.length; s = s + 1) {
      periods = Math.max(periods, series[s].values.length)
    }
  }
  if (periods > 2) {
    throw new Error(`a slope chart compares exactly two periods but the data has ${periods}; ` +
      "use a line chart for three or more")
  }

  const leftLabel = categories.length > 0 ? String(categories[0]) : ""
  const rightLabel = categories.length > 1 ? String(categories[1]) : ""

  const entries = series.map((entry) => ({
    name: entry.name,
    left: numericValue(entry.values[0]),
    right: numericValue(entry.values[1])
  }))

  /* Shared value domain across both columns. */
  let valueMin = Infinity
  let valueMax = -Infinity
  for (let index = 0; index < entries.length; index = index + 1) {
    for (const value of [entries[index].left, entries[index].right]) {
      if (value !== null) {
        valueMin = Math.min(valueMin, value)
        valueMax = Math.max(valueMax, value)
      }
    }
  }
  if (valueMin === Infinity) {
    valueMin = 0
    valueMax = 1
  }
  if (valueMax === valueMin) {
    valueMin = valueMin - 1
    valueMax = valueMax + 1
  }

  /* Gutters sized from the longest endpoint label. */
  const cap = ctx.width / 3
  let leftWidth = 0
  let rightWidth = 0
  for (let index = 0; index < entries.length; index = index + 1) {
    const entry = entries[index]
    if (entry.left !== null) {
      leftWidth = Math.max(leftWidth, textWidth(`${entry.name} ${formatNumber(entry.left)}`))
    }
    if (entry.right !== null) {
      rightWidth = Math.max(rightWidth, textWidth(`${formatNumber(entry.right)} ${entry.name}`))
    }
  }
  const headerHalf = Math.max(textWidth(leftLabel, 12, "600"), textWidth(rightLabel, 12, "600")) / 2
  const margin = {
    top: 32,
    right: Math.ceil(Math.max(Math.min(rightWidth, cap) + LABEL_PAD + 5, headerHalf + 4, 24)),
    bottom: 16,
    left: Math.ceil(Math.max(Math.min(leftWidth, cap) + LABEL_PAD + 5, headerHalf + 4, 24))
  }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  /* Pad the domain so the endpoint dots stay inside the plot. */
  const val = linearScale([valueMin, valueMax], [plotH - DOT_R - 1, DOT_R + 1])

  const plot = svgEl("g", { transform: `translate(${margin.left},${margin.top})` }, [])
  const chrome = svgEl("g", { "aria-hidden": "true", part: "axes" }, [])
  plot.appendChild(chrome)
  root.appendChild(plot)

  /* Light gridlines, then the two column axes and their headers. */
  const ticks = niceTicks(valueMin, valueMax, 5)
  for (let t = 0; t < ticks.length; t = t + 1) {
    const y = val(ticks[t])
    chrome.appendChild(svgEl("line", {
      x1: 0, y1: y, x2: plotW, y2: y, stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
  }
  for (const x of [0, plotW]) {
    chrome.appendChild(svgEl("line", {
      x1: x, y1: 0, x2: x, y2: plotH, stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
    }, []))
  }
  chrome.appendChild(svgEl("text", {
    x: 0, y: -12, "text-anchor": "middle", "font-size": 12, "font-weight": "600",
    fill: "var(--mj-text, #14181f)"
  }, truncateText(leftLabel, margin.left * 2 - 8, 12, "600")))
  chrome.appendChild(svgEl("text", {
    x: plotW, y: -12, "text-anchor": "middle", "font-size": 12, "font-weight": "600",
    fill: "var(--mj-text, #14181f)"
  }, truncateText(rightLabel, margin.right * 2 - 8, 12, "600")))

  /* Slope lines (focusable), then the dots on top. */
  const lines = svgEl("g", { part: "slopes" }, [])
  const dots = svgEl("g", { part: "dots", "aria-hidden": "true" }, [])
  plot.appendChild(lines)
  plot.appendChild(dots)

  const leftPositions = []
  const rightPositions = []
  for (let index = 0; index < entries.length; index = index + 1) {
    const entry = entries[index]
    const color = ctx.colorFor(entry.name)
    if (entry.left !== null) {
      leftPositions.push({ y: val(entry.left), anchorY: val(entry.left), entry: entry, color: color })
      dots.appendChild(svgEl("circle", { cx: 0, cy: val(entry.left), r: DOT_R, fill: color }, []))
    }
    if (entry.right !== null) {
      rightPositions.push({ y: val(entry.right), anchorY: val(entry.right), entry: entry, color: color })
      dots.appendChild(svgEl("circle", { cx: plotW, cy: val(entry.right), r: DOT_R, fill: color }, []))
    }
    if (entry.left === null || entry.right === null) {
      continue
    }

    const change = entry.right - entry.left
    const direction = change > 0 ? "up" : change < 0 ? "down" : "unchanged"
    const text = `${entry.name}: ${formatNumber(entry.left)} to ${formatNumber(entry.right)} (${direction})`
    const line = svgEl("line", {
      x1: 0, y1: val(entry.left), x2: plotW, y2: val(entry.right),
      stroke: color,
      "stroke-width": "var(--mj-chart-slope-width, 2)",
      "stroke-linecap": "round",
      part: "slope-line",
      tabindex: "0",
      role: "img",
      "aria-label": text
    }, [svgEl("title", null, text)])
    activate(line, () => {
      ctx.emit("mj-chart-slope-click", { series: entry.name, leftValue: entry.left, rightValue: entry.right })
    })
    lines.appendChild(line)
  }

  /* Endpoint labels, nudged apart inside the plot. */
  const labels = svgEl("g", { part: "labels", "aria-hidden": "true" }, [])
  plot.appendChild(labels)
  const sides = [
    { items: leftPositions, x: -LABEL_PAD, anchor: "end", room: margin.left - LABEL_PAD - 2, dotX: 0, sign: -1 },
    { items: rightPositions, x: plotW + LABEL_PAD, anchor: "start", room: margin.right - LABEL_PAD - 2, dotX: plotW, sign: 1 }
  ]
  for (let k = 0; k < sides.length; k = k + 1) {
    const side = sides[k]
    nudgeLabels(side.items, LABEL_MIN_GAP, 4, plotH - 4)
    for (let index = 0; index < side.items.length; index = index + 1) {
      const item = side.items[index]
      const value = side.sign < 0 ? item.entry.left : item.entry.right
      const full = side.sign < 0
        ? `${item.entry.name} ${formatNumber(value)}`
        : `${formatNumber(value)} ${item.entry.name}`
      if (Math.abs(item.y - item.anchorY) > 2) {
        labels.appendChild(svgEl("line", {
          x1: side.dotX + side.sign * (DOT_R + 1), y1: item.anchorY,
          x2: side.x - side.sign * 2, y2: item.y,
          stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1
        }, []))
      }
      labels.appendChild(svgEl("text", {
        x: side.x, y: item.y + 4, "text-anchor": side.anchor,
        "font-size": LABEL_FONT_SIZE, fill: "var(--mj-text, #14181f)"
      }, truncateText(full, side.room)))
    }
  }

  return root
}


registerRenderer("slope", render);
