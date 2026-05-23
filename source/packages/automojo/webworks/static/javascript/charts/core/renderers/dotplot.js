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
 * Registered type keys: "dotplot"
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, formatNumber } from "../svgdraw.js";
import { linearScale, pointScale, niceTicks } from "../scales.js";


export function render(ctx) {
  /*
   * Render a dot plot or dumbbell chart.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const model = ctx.model
  const horizontal = ctx.orientation === "horizontal"

  /* showConnectors: honour controller attribute, or meta field on raw data. */
  const showConnectorsAttr = ctx.attrs("show-connectors", "false")
  const showConnectorsMeta = (model.raw && model.raw.meta &&
    model.raw.meta.showConnectors === true)
  const showConnectors = showConnectorsAttr === "true" || showConnectorsMeta === true

  const markerSizeAttr = ctx.attrs("marker-size", "6")
  const markerR = parseFloat(markerSizeAttr) || 6

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
  let valueMin = Infinity
  let valueMax = -Infinity
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
  if (valueMin === Infinity) {
    valueMin = 0
  }
  if (valueMax === -Infinity) {
    valueMax = 1
  }
  if (valueMax === valueMin) {
    valueMax = valueMin + 1
  }

  /* Point scale (not band) aligns dots to category midpoints. */
  const cat = pointScale(categories, [0, horizontal ? plotH : plotW])
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

  /* Draw connectors first so dots render on top. */
  if (showConnectors === true && series.length >= 2) {
    for (let c = 0; c < categories.length; c = c + 1) {
      const category = categories[c]
      const catPos = cat(category)

      for (let s = 0; s < series.length - 1; s = s + 1) {
        const rawA = series[s].values[c]
        const rawB = series[s + 1].values[c]
        if (typeof rawA !== "number" || typeof rawB !== "number") {
          continue
        }
        const posA = val(rawA)
        const posB = val(rawB)

        let x1, y1, x2, y2
        if (horizontal === true) {
          x1 = posA
          y1 = catPos
          x2 = posB
          y2 = catPos
        } else {
          x1 = catPos
          y1 = posA
          x2 = catPos
          y2 = posB
        }

        plot.appendChild(svgEl("line", {
          x1: x1, y1: y1, x2: x2, y2: y2,
          stroke: "var(--mj-chart-connector-stroke, #9ca3af)",
          "stroke-width": "var(--mj-chart-connector-stroke-width, 2)",
          "stroke-linecap": "round"
        }, []))
      }
    }
  }

  /* Dot shape cycle for non-color accessibility. */
  const SHAPES = ["circle", "square", "diamond", "triangle"]

  /* Draw dots per series. */
  for (let s = 0; s < series.length; s = s + 1) {
    const shape = SHAPES[s % SHAPES.length]
    const color = ctx.colorFor(series[s].name)

    for (let c = 0; c < categories.length; c = c + 1) {
      const category = categories[c]
      const catPos = cat(category)
      const rawValue = series[s].values[c]
      if (typeof rawValue !== "number") {
        continue
      }
      const valPos = val(rawValue)

      let dotCx, dotCy
      if (horizontal === true) {
        dotCx = valPos
        dotCy = catPos
      } else {
        dotCx = catPos
        dotCy = valPos
      }

      let mark = null
      if (shape === "circle") {
        mark = svgEl("circle", {
          cx: dotCx, cy: dotCy, r: markerR,
          fill: color
        }, [])
      } else if (shape === "square") {
        const half = markerR * 0.9
        mark = svgEl("rect", {
          x: dotCx - half, y: dotCy - half,
          width: half * 2, height: half * 2,
          fill: color
        }, [])
      } else if (shape === "diamond") {
        const r = markerR
        mark = svgEl("polygon", {
          points: `${dotCx},${dotCy - r} ${dotCx + r},${dotCy} ${dotCx},${dotCy + r} ${dotCx - r},${dotCy}`,
          fill: color
        }, [])
      } else {
        /* triangle */
        const r = markerR
        mark = svgEl("polygon", {
          points: `${dotCx},${dotCy - r} ${dotCx + r},${dotCy + r * 0.6} ${dotCx - r},${dotCy + r * 0.6}`,
          fill: color
        }, [])
      }

      mark.setAttribute("part", "dot")
      mark.setAttribute("tabindex", "0")
      mark.setAttribute("role", "img")
      mark.setAttribute("aria-label",
        `${series[s].name}, ${category}: ${rawValue}`)
      mark.appendChild(svgEl("title", null,
        `${series[s].name} - ${category}: ${rawValue}`))

      const handler = () => {
        ctx.emit("mj-chart-dotplot-click", {
          series: series[s].name, category: category, value: rawValue
        })
      }
      mark.addEventListener("click", handler)
      mark.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault()
          handler()
        }
      })
      plot.appendChild(mark)
    }
  }

  /* Category labels. */
  for (let c = 0; c < categories.length; c = c + 1) {
    const category = categories[c]
    const catPos = cat(category)

    if (horizontal === true) {
      plot.appendChild(svgEl("text", {
        x: -8, y: catPos + 4, "text-anchor": "end",
        "font-size": 11, fill: "var(--mj-text, #14181f)"
      }, escapeHtml(category)))
    } else {
      plot.appendChild(svgEl("text", {
        x: catPos, y: plotH + 18, "text-anchor": "middle",
        "font-size": 11, fill: "var(--mj-text, #14181f)"
      }, escapeHtml(category)))
    }
  }

  /* Axis baseline. */
  if (horizontal === true) {
    plot.appendChild(svgEl("line", {
      x1: 0, y1: 0, x2: 0, y2: plotH,
      stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
    }, []))
  } else {
    plot.appendChild(svgEl("line", {
      x1: 0, y1: plotH, x2: plotW, y2: plotH,
      stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
    }, []))
  }

  return root
}


registerRenderer("dotplot", render);
