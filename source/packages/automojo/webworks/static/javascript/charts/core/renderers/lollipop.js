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
 * Registered type keys: "lollipop"
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, formatNumber } from "../svgdraw.js";
import { linearScale, bandScale, niceTicks } from "../scales.js";


export function render(ctx) {
  /*
   * Render a lollipop chart.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const model = ctx.model
  const horizontal = ctx.orientation === "horizontal"
  const markerSizeAttr = ctx.attrs("marker-size", "8")
  const defaultMarkerSize = parseFloat(markerSizeAttr) || 8

  const root = svgEl("g", { part: "plot" }, [])

  const categories = model.categories
  const series = model.series
  if (categories.length === 0 || series.length === 0) {
    return root
  }

  const margin = { top: 16, right: 16, bottom: 40, left: 52 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  /* Compute the value domain across all series. */
  let valueMin = 0
  let valueMax = 0
  for (let s = 0; s < series.length; s = s + 1) {
    for (let c = 0; c < series[s].values.length; c = c + 1) {
      const value = series[s].values[c]
      if (typeof value !== "number") {
        continue
      }
      if (value < valueMin) {
        valueMin = value
      }
      if (value > valueMax) {
        valueMax = value
      }
    }
  }
  if (valueMax === valueMin) {
    valueMax = valueMin + 1
  }

  /* Scales: category band along one axis, value linear along the other. */
  const cat = bandScale(categories, [0, horizontal ? plotH : plotW], 0.2)
  const val = horizontal
    ? linearScale([valueMin, valueMax], [0, plotW])
    : linearScale([valueMin, valueMax], [plotH, 0])

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  /* Value gridlines + tick labels. */
  const ticks = niceTicks(valueMin, valueMax, 5)
  for (let t = 0; t < ticks.length; t = t + 1) {
    const tick = ticks[t]
    if (horizontal === true) {
      const x = val(tick)
      plot.appendChild(svgEl("line", {
        x1: x, y1: 0, x2: x, y2: plotH,
        stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
      }, []))
      plot.appendChild(svgEl("text", {
        x: x, y: plotH + 16, "text-anchor": "middle",
        "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
      }, formatNumber(tick)))
    } else {
      const y = val(tick)
      plot.appendChild(svgEl("line", {
        x1: 0, y1: y, x2: plotW, y2: y,
        stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
      }, []))
      plot.appendChild(svgEl("text", {
        x: -8, y: y + 4, "text-anchor": "end",
        "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
      }, formatNumber(tick)))
    }
  }

  const zero = val(0)
  const bandwidth = cat.bandwidth()
  const subWidth = series.length > 1 ? bandwidth / series.length : bandwidth

  /* Draw stems and dot heads. */
  for (let c = 0; c < categories.length; c = c + 1) {
    const category = categories[c]
    const bandStart = cat(category)

    for (let s = 0; s < series.length; s = s + 1) {
      const rawValue = series[s].values[c]
      const value = typeof rawValue === "number" ? rawValue : 0
      const color = ctx.colorFor(series[s].name)
      const markerSize = series[s].markerSize || defaultMarkerSize

      /* Centre of this lollipop within the category band. */
      const offset = series.length > 1
        ? bandStart + s * subWidth + subWidth / 2
        : bandStart + bandwidth / 2

      let stemX1, stemY1, stemX2, stemY2, dotCx, dotCy

      if (horizontal === true) {
        const valX = val(value)
        stemX1 = zero
        stemY1 = offset
        stemX2 = valX
        stemY2 = offset
        dotCx = valX
        dotCy = offset
      } else {
        const valY = val(value)
        stemX1 = offset
        stemY1 = zero
        stemX2 = offset
        stemY2 = valY
        dotCx = offset
        dotCy = valY
      }

      /* Stem. */
      plot.appendChild(svgEl("line", {
        x1: stemX1, y1: stemY1, x2: stemX2, y2: stemY2,
        stroke: color,
        "stroke-width": "var(--mj-chart-stem-width, 2)",
        "stroke-linecap": "round"
      }, []))

      /* Dot head. */
      const dot = svgEl("circle", {
        cx: dotCx, cy: dotCy, r: markerSize,
        fill: color,
        part: "dot",
        tabindex: "0",
        role: "img",
        "aria-label": `${series[s].name}, ${category}: ${value}`
      }, [])

      dot.appendChild(svgEl("title", null,
        `${series[s].name} - ${category}: ${value}`))

      const handler = () => {
        ctx.emit("mj-chart-lollipop-click", {
          series: series[s].name, category: category, value: value
        })
      }
      dot.addEventListener("click", handler)
      dot.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault()
          handler()
        }
      })
      plot.appendChild(dot)
    }

    /* Category label. */
    if (horizontal === true) {
      plot.appendChild(svgEl("text", {
        x: -8, y: bandStart + bandwidth / 2 + 4, "text-anchor": "end",
        "font-size": 11, fill: "var(--mj-text, #14181f)"
      }, escapeHtml(category)))
    } else {
      plot.appendChild(svgEl("text", {
        x: bandStart + bandwidth / 2, y: plotH + 18, "text-anchor": "middle",
        "font-size": 11, fill: "var(--mj-text, #14181f)"
      }, escapeHtml(category)))
    }
  }

  /* Axis baseline at zero. */
  if (horizontal === true) {
    plot.appendChild(svgEl("line", {
      x1: zero, y1: 0, x2: zero, y2: plotH,
      stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
    }, []))
  } else {
    plot.appendChild(svgEl("line", {
      x1: 0, y1: zero, x2: plotW, y2: zero,
      stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
    }, []))
  }

  return root
}


registerRenderer("lollipop", render);
