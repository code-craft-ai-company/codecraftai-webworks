/*
 * dotplot.js
 *
 * Dot plot renderer (Cleveland dot plot) -- compares values across categories
 * using dot markers with maximum data-ink ratio. When two series are present
 * and the "show-connectors" attribute is set, the renderer draws a connector
 * line between dots in the same category, producing a Dumbbell chart.
 *
 * A renderer is `render(ctx) -> SVGElement`:
 *   ctx.model       normalized model { meta, categories, series, raw }
 *   ctx.raw         the raw data object
 *   ctx.width       drawing surface width (px)
 *   ctx.height      drawing surface height (px)
 *   ctx.orientation "vertical" | "horizontal"
 *   ctx.attrs       (name, fallback) -> controller attribute value
 *   ctx.colorFor    (seriesIndex | seriesName) -> CSS color
 *   ctx.emit        (eventName, detail) -> dispatch an interaction event
 * It returns a <g> SVGElement drawn within [0..width] x [0..height].
 *
 * Attributes:
 *   show-connectors  boolean (or meta.showConnectors) -- dumbbell connectors
 *                    between the dots of neighbouring series
 *   marker-size      marker radius in px (default 6)
 *   sort             "none" (default) | "asc" | "desc" -- order categories by
 *                    their total across the visible series
 *
 * Each category's dots sit at the centre of its band, so the first and last
 * categories keep a half band of room. The value axis spans the data (it
 * need not include zero) and is inset by the marker size so the extreme
 * dots never sit on the plot edge. Each series has its own marker shape as
 * well as its own colour. Missing values draw nothing.
 *
 * Registered type keys: "dotplot"
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber } from "../svgdraw.js";
import { categoryOrder, categoryValueFrame, numericValue, activate } from "./bar.js";
import { booleanOption } from "../chartoptions.js";

/* Dot shape cycle, so series differ by more than colour. */
const SHAPES = ["circle", "square", "diamond", "triangle"];


function _marker(shape, cx, cy, radius, color) {
  /*
   * Build one marker of the given shape centred on (cx, cy).
   */
  let mark = null
  if (shape === "circle") {
    mark = svgEl("circle", { cx: cx, cy: cy, r: radius, fill: color }, [])
  } else if (shape === "square") {
    const half = radius * 0.9
    mark = svgEl("rect", {
      x: cx - half, y: cy - half, width: half * 2, height: half * 2, fill: color
    }, [])
  } else if (shape === "diamond") {
    mark = svgEl("polygon", {
      points: `${cx},${cy - radius} ${cx + radius},${cy} ${cx},${cy + radius} ${cx - radius},${cy}`,
      fill: color
    }, [])
  } else {
    mark = svgEl("polygon", {
      points: `${cx},${cy - radius} ${cx + radius},${cy + radius * 0.6} ${cx - radius},${cy + radius * 0.6}`,
      fill: color
    }, [])
  }
  return mark
}


export function render(ctx) {
  /*
   * Render a dot plot or dumbbell chart.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const model = ctx.model
  const horizontal = ctx.orientation === "horizontal"

  /* showConnectors: the controller attribute, or the meta field. */
  const showConnectorsMeta = model.meta.showConnectors === true
  const showConnectors = booleanOption(ctx, "show-connectors", showConnectorsMeta)
  const markerR = Math.min(Math.max(numericValue(ctx.attrs("marker-size", "6")) || 6, 1), 30)

  const root = svgEl("g", { part: "plot" }, [])

  const order = categoryOrder(model, ctx.attrs("sort", "none"))
  const series = model.series
  if (order.length === 0 || series.length === 0) {
    return root
  }

  /* The value domain across all series. */
  let valueMin = Infinity
  let valueMax = -Infinity
  for (let s = 0; s < series.length; s = s + 1) {
    for (let c = 0; c < order.length; c = c + 1) {
      const value = numericValue(series[s].values[order[c].index])
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

  const frame = categoryValueFrame(ctx, {
    labels: order.map((entry) => entry.label),
    domain: [valueMin, valueMax],
    horizontal: horizontal,
    padding: 0,
    valueInset: markerR + 2
  })
  root.appendChild(frame.plot)
  const val = frame.val

  /* Axis line on the value-axis side. */
  frame.chrome.appendChild(svgEl("line", horizontal === true
    ? { x1: 0, y1: 0, x2: 0, y2: frame.plotH, stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5 }
    : { x1: 0, y1: frame.plotH, x2: frame.plotW, y2: frame.plotH, stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5 }, []))

  /* Connectors first so dots render on top. */
  if (showConnectors === true && series.length >= 2) {
    const connectors = svgEl("g", { part: "connectors", "aria-hidden": "true" }, [])
    for (let c = 0; c < order.length; c = c + 1) {
      const center = frame.cat.centerAt(c)
      for (let s = 0; s < series.length - 1; s = s + 1) {
        const first = numericValue(series[s].values[order[c].index])
        const second = numericValue(series[s + 1].values[order[c].index])
        if (first === null || second === null) {
          continue
        }
        const a = val(first)
        const b = val(second)
        connectors.appendChild(svgEl("line", {
          x1: horizontal === true ? a : center,
          y1: horizontal === true ? center : a,
          x2: horizontal === true ? b : center,
          y2: horizontal === true ? center : b,
          stroke: "var(--mj-chart-connector-stroke, var(--mj-border-strong, #c7ccd6))",
          "stroke-width": "var(--mj-chart-connector-stroke-width, 2)",
          "stroke-linecap": "round"
        }, []))
      }
    }
    frame.marks.appendChild(connectors)
  }

  /* Dots per series. */
  for (let s = 0; s < series.length; s = s + 1) {
    const shape = SHAPES[s % SHAPES.length]
    const color = ctx.colorFor(series[s].name)

    for (let c = 0; c < order.length; c = c + 1) {
      const value = numericValue(series[s].values[order[c].index])
      if (value === null) {
        continue
      }
      const category = order[c].label
      const center = frame.cat.centerAt(c)
      const position = val(value)
      const mark = _marker(shape, horizontal === true ? position : center,
        horizontal === true ? center : position, markerR, color)

      const text = `${series[s].name}, ${category}: ${formatNumber(value)}`
      mark.setAttribute("part", "dot")
      mark.setAttribute("tabindex", "0")
      mark.setAttribute("role", "img")
      mark.setAttribute("aria-label", text)
      mark.appendChild(svgEl("title", null, text))

      const detail = { series: series[s].name, category: category, value: value }
      activate(mark, () => {
        ctx.emit("mj-chart-dotplot-click", detail)
      })
      frame.marks.appendChild(mark)
    }
  }

  return root
}


registerRenderer("dotplot", render);
