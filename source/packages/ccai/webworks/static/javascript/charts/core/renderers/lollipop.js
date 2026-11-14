/*
 * lollipop.js
 *
 * Lollipop chart renderer -- a lower-ink alternative to bar charts where
 * each data point is represented by a thin stem (line from baseline to
 * value) and a circular dot head at the value position.
 *
 * A renderer is `render(ctx) -> SVGElement`:
 *   ctx.model       normalized model { meta, categories, series, raw }
 *   ctx.raw         the raw data object
 *   ctx.width       drawing surface width (px)
 *   ctx.height      drawing surface height (px)
 *   ctx.orientation "vertical" (columns) | "horizontal" (bars)
 *   ctx.attrs       (name, fallback) -> controller attribute value
 *   ctx.colorFor    (seriesIndex | seriesName) -> CSS color
 *   ctx.emit        (eventName, detail) -> dispatch an interaction event
 * It returns a <g> SVGElement drawn within [0..width] x [0..height].
 *
 * Attributes:
 *   marker-size   dot radius in px (default 8; a series may set markerSize)
 *   sort          "none" (default) | "asc" | "desc" -- order categories by
 *                 their total across the visible series (ranking form)
 *
 * Categories are positioned by index (duplicate labels keep their own
 * lollipop). A missing value (null, non-numeric text) draws nothing; a
 * numeric string such as "10" is read as a number. The value axis always
 * includes zero, the stems start there, and the category labels get as
 * much room as they need (long labels are shortened with an ellipsis).
 *
 * Registered type keys: "lollipop"
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber } from "../svgdraw.js";
import { categoryOrder, categoryValueFrame, zeroLine, numericValue, activate } from "./bar.js";


export function render(ctx) {
  /*
   * Render a lollipop chart.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const model = ctx.model
  const horizontal = ctx.orientation === "horizontal"
  const defaultMarkerSize = Math.min(Math.max(numericValue(ctx.attrs("marker-size", "8")) || 8, 1), 40)

  const root = svgEl("g", { part: "plot" }, [])

  const order = categoryOrder(model, ctx.attrs("sort", "none"))
  const series = model.series
  if (order.length === 0 || series.length === 0) {
    return root
  }

  /* The value domain across all series, always including zero. */
  let valueMin = 0
  let valueMax = 0
  for (let s = 0; s < series.length; s = s + 1) {
    for (let c = 0; c < order.length; c = c + 1) {
      const value = numericValue(series[s].values[order[c].index])
      if (value !== null) {
        valueMin = Math.min(valueMin, value)
        valueMax = Math.max(valueMax, value)
      }
    }
  }
  if (valueMax === valueMin) {
    valueMax = valueMin + 1
  }

  const frame = categoryValueFrame(ctx, {
    labels: order.map((entry) => entry.label),
    domain: [valueMin, valueMax],
    horizontal: horizontal,
    padding: 0.2,
    valueInset: 0
  })
  root.appendChild(frame.plot)

  const val = frame.val
  const zero = val(0)
  const bandwidth = frame.cat.bandwidth()
  const subWidth = series.length > 1 ? bandwidth / series.length : bandwidth

  /* Stems first, dots on top. */
  const stems = svgEl("g", { part: "stems", "aria-hidden": "true" }, [])
  const heads = svgEl("g", { part: "dots" }, [])
  frame.marks.appendChild(stems)
  frame.marks.appendChild(heads)

  for (let c = 0; c < order.length; c = c + 1) {
    const category = order[c].label
    const bandStart = frame.cat.at(c)

    for (let s = 0; s < series.length; s = s + 1) {
      const value = numericValue(series[s].values[order[c].index])
      if (value === null) {
        continue
      }
      const color = ctx.colorFor(series[s].name)
      const ownSize = numericValue(series[s].markerSize)
      const radius = Math.min(ownSize !== null && ownSize > 0 ? ownSize : defaultMarkerSize, Math.max(subWidth / 2, 2))

      /* Centre of this lollipop within the category band. */
      const offset = series.length > 1
        ? bandStart + s * subWidth + subWidth / 2
        : bandStart + bandwidth / 2
      const position = val(value)

      stems.appendChild(svgEl("line", {
        x1: horizontal === true ? zero : offset,
        y1: horizontal === true ? offset : zero,
        x2: horizontal === true ? position : offset,
        y2: horizontal === true ? offset : position,
        stroke: color,
        "stroke-width": "var(--mj-chart-stem-width, 2)",
        "stroke-linecap": "round"
      }, []))

      const text = `${series[s].name}, ${category}: ${formatNumber(value)}`
      const dot = svgEl("circle", {
        cx: horizontal === true ? position : offset,
        cy: horizontal === true ? offset : position,
        r: radius,
        fill: color,
        part: "dot",
        tabindex: "0",
        role: "img",
        "aria-label": text
      }, [svgEl("title", null, text)])

      const detail = { series: series[s].name, category: category, value: value }
      activate(dot, () => {
        ctx.emit("mj-chart-lollipop-click", detail)
      })
      heads.appendChild(dot)
    }
  }

  zeroLine(frame, horizontal)
  return root
}


registerRenderer("lollipop", render);
