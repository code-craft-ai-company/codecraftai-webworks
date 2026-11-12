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
 * A dimension without a `domain` uses the nice-rounded extent of its
 * observed values. Lines are clipped to the plot, so a value outside a
 * given domain leaves the plot at the axis edge; a missing (null) value
 * breaks the line. Series come from the model, so unnamed series are
 * "Series N" and hidden series are not drawn.
 *
 * Attributes:
 *   curved       boolean (default false) -- cubic-bezier vs. straight lines
 *   color-by     dimension name -- colour lines by their value on that
 *                dimension with a sequential ramp; a gradient key replaces
 *                the series key
 *
 * Up to 200 observations are focusable marks with a label listing their
 * values; denser data is drawn as plain lines (the accessible table lists
 * every observation) at reduced opacity.
 *
 * Registered type keys: "parallel"
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber } from "../svgdraw.js";
import { linearScale, niceTicks, niceDomain, seriesColor } from "../scales.js";
import {
  textWidth, truncateText, numericValue, nextClipId, inlineLegend, activate
} from "./bar.js";
import { booleanOption } from "../chartoptions.js";

const TICK_COUNT = 5;
const TICK_LEN = 5;
const TICK_FONT_SIZE = 10;
const TITLE_FONT_SIZE = 11;
const FOCUSABLE_LIMIT = 200;
const DENSE_OPACITY = "var(--mj-chart-parallel-opacity, 0.4)";


function _dimensions(raw) {
  /*
   * The dimension descriptors, each with a display title.
   */
  const list = raw !== null && raw !== undefined && Array.isArray(raw.dimensions) === true ? raw.dimensions : []
  const dimensions = list.map((entry, index) => {
    const dimension = entry !== null && typeof entry === "object" ? entry : {}
    const name = dimension.name !== undefined && dimension.name !== null ? String(dimension.name) : `Dimension ${index + 1}`
    const unit = dimension.unit !== undefined && dimension.unit !== null && String(dimension.unit) !== ""
      ? ` (${dimension.unit})` : ""
    return { name: name, title: `${name}${unit}`, domain: dimension.domain }
  })
  return dimensions
}


function _observations(entry) {
  /*
   * The observation rows of a series, with every cell a number or null.
   */
  const rows = Array.isArray(entry.observations) === true ? entry.observations : []
  const cleaned = []
  for (let index = 0; index < rows.length; index = index + 1) {
    if (Array.isArray(rows[index]) === true) {
      cleaned.push(rows[index].map((value) => numericValue(value)))
    }
  }
  return cleaned
}


function _domainOf(dimension, index, seriesRows) {
  /*
   * A dimension's domain: the given [min, max], else its data extent.
   */
  const given = dimension.domain
  if (Array.isArray(given) === true && given.length >= 2) {
    const low = numericValue(given[0])
    const high = numericValue(given[1])
    if (low !== null && high !== null && low !== high) {
      return [low, high]
    }
  }
  let low = Infinity
  let high = -Infinity
  for (let s = 0; s < seriesRows.length; s = s + 1) {
    for (let o = 0; o < seriesRows[s].length; o = o + 1) {
      const value = seriesRows[s][o][index]
      if (value !== null && value !== undefined) {
        low = Math.min(low, value)
        high = Math.max(high, value)
      }
    }
  }
  if (low === Infinity) {
    return [0, 1]
  }
  if (low === high) {
    return [low - 1, high + 1]
  }
  return niceDomain(low, high, TICK_COUNT)
}


function _observationPath(row, axisXs, scales, curved) {
  /*
   * Path data of one observation; a null value breaks the line.
   */
  let data = ""
  let previous = null
  for (let d = 0; d < axisXs.length; d = d + 1) {
    const value = row[d]
    if (value === null || value === undefined) {
      previous = null
      continue
    }
    const point = { x: axisXs[d], y: scales[d](value) }
    if (previous === null) {
      data = data + `M${point.x.toFixed(2)},${point.y.toFixed(2)} `
    } else if (curved === true) {
      const third = (point.x - previous.x) / 3
      data = data + `C${(previous.x + third).toFixed(2)},${previous.y.toFixed(2)} ` +
        `${(point.x - third).toFixed(2)},${point.y.toFixed(2)} ${point.x.toFixed(2)},${point.y.toFixed(2)} `
    } else {
      data = data + `L${point.x.toFixed(2)},${point.y.toFixed(2)} `
    }
    previous = point
  }
  return data.trim()
}


function _rampColor(fraction) {
  /*
   * Sequential colour: palette slot 1 mixed from the surface (low) to full
   * strength (high).
   */
  const clamped = Math.min(Math.max(fraction, 0), 1)
  const strength = Math.round(35 + clamped * 65)
  const color = `color-mix(in oklab, ${seriesColor(0)} ${strength}%, var(--mj-surface, #ffffff))`
  return color
}


export function parallelTable(ctx) {
  /*
   * The accessible table: one row per observation.
   */
  const dimensions = _dimensions(ctx.raw)
  const rows = []
  for (let s = 0; s < ctx.model.series.length; s = s + 1) {
    const entry = ctx.model.series[s]
    const observations = _observations(entry)
    for (let o = 0; o < observations.length; o = o + 1) {
      const row = [entry.name]
      for (let d = 0; d < dimensions.length; d = d + 1) {
        row.push(observations[o][d] !== null && observations[o][d] !== undefined ? observations[o][d] : "")
      }
      rows.push(row)
    }
  }
  return { columns: ["Series"].concat(dimensions.map((dimension) => dimension.title)), rows: rows }
}


export function render(ctx) {
  /*
   * Render a parallel coordinates plot.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const root = svgEl("g", { part: "plot" }, [])

  const dimensions = _dimensions(ctx.raw)
  const series = ctx.model.series
  if (dimensions.length === 0 || series.length === 0) {
    return root
  }
  ctx.setTable(parallelTable(ctx))

  const curved = booleanOption(ctx, "curved", false)
  const colorByName = String(ctx.attrs("color-by", "")).trim()
  const colorByIndex = colorByName !== "" ? dimensions.findIndex((dimension) => dimension.name === colorByName) : -1

  const seriesRows = series.map((entry) => _observations(entry))
  const domains = dimensions.map((dimension, index) => _domainOf(dimension, index, seriesRows))
  const tickSets = domains.map((domain) => niceTicks(domain[0], domain[1], TICK_COUNT))

  /* Key: the series, or a gradient for color-by. */
  let legendEntries = []
  if (colorByIndex >= 0) {
    const domain = domains[colorByIndex]
    legendEntries = [
      { label: `${dimensions[colorByIndex].title} ${formatNumber(domain[0])}`, color: _rampColor(0) },
      { label: formatNumber(domain[1]), color: _rampColor(1) }
    ]
  } else if (series.length > 1 && ctx.hasLegendPart !== true) {
    /* A bound <mj-chart-legend> lists the series itself (as toggles). */
    legendEntries = series.map((entry) => ({ label: entry.name, color: ctx.colorFor(entry.name) }))
  }
  if (colorByIndex >= 0) {
    ctx.setLegend(legendEntries)
  }
  const legend = colorByIndex >= 0 ? { height: 16 } : inlineLegend(legendEntries, 0, 0, Math.max(ctx.width - 24, 40))
  const legendHeight = legendEntries.length > 0 ? legend.height + 10 : 0

  /* Side margins from the outer titles and the outer axes' tick labels. */
  const widestTicks = (index) => Math.max(0, ...tickSets[index].map((tick) => textWidth(formatNumber(tick), TICK_FONT_SIZE)))
  const last = dimensions.length - 1
  const titleHalf = (index) => Math.min(textWidth(dimensions[index].title, TITLE_FONT_SIZE, "600"), ctx.width * 0.3) / 2
  const margin = {
    top: 30,
    right: Math.ceil(Math.max(titleHalf(last) + 2, widestTicks(last) + TICK_LEN + 8, 16)),
    bottom: 12 + legendHeight,
    left: Math.ceil(Math.max(titleHalf(0) + 2, widestTicks(0) + TICK_LEN + 8, 16))
  }
  if (dimensions.length === 1) {
    margin.left = Math.round(ctx.width / 2)
    margin.right = 0
  }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  const axisXs = dimensions.map((dimension, index) => dimensions.length > 1 ? (plotW * index) / last : 0)
  const scales = domains.map((domain) => linearScale(domain, [plotH, 0]))
  const spacing = dimensions.length > 1 ? plotW / last : plotW

  const plot = svgEl("g", { transform: `translate(${margin.left},${margin.top})` }, [])
  root.appendChild(plot)

  /* Observations first so axes render on top; clipped to the plot. */
  const clipId = nextClipId("mj-parallel-clip")
  plot.appendChild(svgEl("defs", null, [svgEl("clipPath", { id: clipId }, [
    svgEl("rect", { x: -2, y: -2, width: plotW + 4, height: plotH + 4 }, [])
  ])]))
  const lines = svgEl("g", { part: "observations", "clip-path": `url(#${clipId})` }, [])
  plot.appendChild(lines)

  let total = 0
  for (let s = 0; s < seriesRows.length; s = s + 1) {
    total = total + seriesRows[s].length
  }
  const dense = total > FOCUSABLE_LIMIT
  const opacity = dense === true ? DENSE_OPACITY : "0.75"
  const colorScale = colorByIndex >= 0 ? linearScale(domains[colorByIndex], [0, 1]) : null

  for (let s = 0; s < series.length; s = s + 1) {
    const name = series[s].name
    const baseColor = ctx.colorFor(name)
    const rows = seriesRows[s]
    for (let o = 0; o < rows.length; o = o + 1) {
      const row = rows[o]
      const data = _observationPath(row, axisXs, scales, curved)
      if (data === "") {
        continue
      }
      let color = baseColor
      if (colorScale !== null && row[colorByIndex] !== null && row[colorByIndex] !== undefined) {
        color = _rampColor(colorScale(row[colorByIndex]))
      }
      const path = svgEl("path", {
        d: data,
        fill: "none",
        stroke: color,
        "stroke-width": "var(--mj-chart-parallel-line-width, 1.5)",
        "stroke-opacity": opacity,
        "stroke-linecap": "round",
        "stroke-linejoin": "round",
        part: "observation",
        "data-series": name
      }, [])
      if (dense === false) {
        const summary = dimensions.map((dimension, d) => {
          const value = row[d]
          return `${dimension.name} ${value !== null && value !== undefined ? formatNumber(value) : "no value"}`
        }).join(", ")
        const text = `${name}: ${summary}`
        path.setAttribute("tabindex", "0")
        path.setAttribute("role", "img")
        path.setAttribute("aria-label", text)
        path.appendChild(svgEl("title", null, text))
        activate(path, () => {
          ctx.emit("mj-chart-parallel-click", { series: name, observation: row })
        })
      } else {
        path.setAttribute("pointer-events", "none")
      }
      lines.appendChild(path)
    }
  }

  /* Axes: line, ticks, labels (haloed, beside the axis), title above. */
  const chrome = svgEl("g", { "aria-hidden": "true", part: "axes" }, [])
  plot.appendChild(chrome)
  for (let d = 0; d < dimensions.length; d = d + 1) {
    const x = axisXs[d]
    chrome.appendChild(svgEl("line", {
      x1: x, y1: 0, x2: x, y2: plotH, stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
    }, []))

    const ticks = tickSets[d]
    const first = d === 0 && dimensions.length > 1
    for (let t = 0; t < ticks.length; t = t + 1) {
      const y = scales[d](ticks[t])
      chrome.appendChild(svgEl("line", {
        x1: x - TICK_LEN / 2, y1: y, x2: x + TICK_LEN / 2, y2: y,
        stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1
      }, []))
      chrome.appendChild(svgEl("text", {
        x: first === true ? x - TICK_LEN - 3 : x + TICK_LEN + 3,
        y: y + 3,
        "text-anchor": first === true ? "end" : "start",
        "font-size": TICK_FONT_SIZE,
        fill: "var(--mj-text-muted, #5f6673)",
        stroke: "var(--mj-surface, #ffffff)",
        "stroke-width": 3,
        "stroke-linejoin": "round",
        "paint-order": "stroke"
      }, formatNumber(ticks[t])))
    }

    /* Titles may not run into their neighbours or off the drawing. */
    let room = spacing - 8
    if (d === 0) {
      room = Math.min(room, margin.left * 2)
    }
    if (d === last) {
      room = Math.min(room, margin.right * 2)
    }
    chrome.appendChild(svgEl("text", {
      x: x, y: -12, "text-anchor": "middle",
      "font-size": TITLE_FONT_SIZE, "font-weight": "600", fill: "var(--mj-text, #14181f)"
    }, truncateText(dimensions[d].title, Math.max(room, 30), TITLE_FONT_SIZE, "600")))
  }

  /* Key below the plot. */
  if (legendEntries.length > 0) {
    const keyY = margin.top + plotH + 12
    if (colorByIndex >= 0) {
      const gradientId = nextClipId("mj-parallel-ramp")
      const stops = [0, 0.25, 0.5, 0.75, 1].map((offset) => svgEl("stop", {
        offset: `${offset * 100}%`, "stop-color": _rampColor(offset)
      }, []))
      const low = `${dimensions[colorByIndex].title} ${formatNumber(domains[colorByIndex][0])}`
      const lowWidth = textWidth(low)
      const group = svgEl("g", { "aria-hidden": "true", part: "legend" }, [
        svgEl("defs", null, [svgEl("linearGradient", { id: gradientId, x1: 0, x2: 1, y1: 0, y2: 0 }, stops)]),
        svgEl("text", { x: 12, y: keyY + 10, "font-size": 11, fill: "var(--mj-text, #14181f)" }, low),
        svgEl("rect", { x: 18 + lowWidth, y: keyY + 1, width: 120, height: 10, rx: 2, fill: `url(#${gradientId})` }, []),
        svgEl("text", { x: 24 + lowWidth + 120, y: keyY + 10, "font-size": 11, fill: "var(--mj-text, #14181f)" },
          formatNumber(domains[colorByIndex][1]))
      ])
      root.appendChild(group)
    } else {
      legend.group.setAttribute("transform", `translate(12,${keyY})`)
      root.appendChild(legend.group)
    }
  }

  return root
}


registerRenderer("parallel", render, { table: parallelTable });
