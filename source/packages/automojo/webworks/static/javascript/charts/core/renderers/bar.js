/*
 * bar.js
 *
 * Bar / column renderer -- the REFERENCE renderer, and the pattern every
 * other renderer follows.
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
 * It returns an <g> SVGElement drawn within [0..width] x [0..height].
 *
 * Consolidated catalog names: Bar, Column (orientation), Grouped/Stacked/
 * 100%-stacked bar (the `group` attribute), Sorted bar (`sort`).
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, formatNumber } from "../svgdraw.js";
import { linearScale, bandScale, niceTicks } from "../scales.js";


function _sortCategories(model, sortMode) {
  /*
   * Optionally sort categories by their first-series total.
   */
  if (sortMode !== "asc" && sortMode !== "desc") {
    return model.categories.slice()
  }
  const totals = model.categories.map((category, index) => {
    let sum = 0
    for (let s = 0; s < model.series.length; s = s + 1) {
      const value = model.series[s].values[index]
      sum = sum + (typeof value === "number" ? value : 0)
    }
    return { category: category, sum: sum, index: index }
  })
  totals.sort((a, b) => sortMode === "asc" ? a.sum - b.sum : b.sum - a.sum)
  const ordered = totals.map((entry) => entry.category)
  return ordered
}


export function render(ctx) {
  /*
   * Render a bar/column chart.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const model = ctx.model
  const horizontal = ctx.orientation === "horizontal"
  const group = ctx.attrs("group", "cluster")
  const sortMode = ctx.attrs("sort", "none")

  const root = svgEl("g", { part: "plot" }, [])

  const categories = _sortCategories(model, sortMode)
  const series = model.series
  if (categories.length === 0 || series.length === 0) {
    return root
  }

  /* Map original category index so values still line up after sorting. */
  const originalIndex = {}
  for (let index = 0; index < model.categories.length; index = index + 1) {
    originalIndex[model.categories[index]] = index
  }

  const margin = { top: 16, right: 16, bottom: 40, left: 52 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  /* Compute the value domain for the chosen stacking mode. */
  let valueMax = 0
  let valueMin = 0
  for (let c = 0; c < categories.length; c = c + 1) {
    const dataIndex = originalIndex[categories[c]]
    let stackPos = 0
    let stackNeg = 0
    for (let s = 0; s < series.length; s = s + 1) {
      const value = series[s].values[dataIndex]
      const numeric = typeof value === "number" ? value : 0
      if (group === "stack" || group === "stack100") {
        if (numeric >= 0) {
          stackPos = stackPos + numeric
        } else {
          stackNeg = stackNeg + numeric
        }
      } else {
        if (numeric > valueMax) {
          valueMax = numeric
        }
        if (numeric < valueMin) {
          valueMin = numeric
        }
      }
    }
    if (stackPos > valueMax) {
      valueMax = stackPos
    }
    if (stackNeg < valueMin) {
      valueMin = stackNeg
    }
  }
  if (group === "stack100") {
    valueMax = 100
    valueMin = 0
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
  const clustered = group === "cluster"
  const subWidth = clustered === true ? bandwidth / series.length : bandwidth

  /* Draw the bars. */
  for (let c = 0; c < categories.length; c = c + 1) {
    const category = categories[c]
    const dataIndex = originalIndex[category]
    const bandStart = cat(category)
    let stackPos = 0
    let stackNeg = 0

    for (let s = 0; s < series.length; s = s + 1) {
      const rawValue = series[s].values[dataIndex]
      const value = typeof rawValue === "number" ? rawValue : 0
      const color = ctx.colorFor(series[s].name)
      let rect = null

      if (clustered === true) {
        const offset = bandStart + s * subWidth
        if (horizontal === true) {
          const x = Math.min(zero, val(value))
          const w = Math.abs(val(value) - zero)
          rect = svgEl("rect", {
            x: x, y: offset, width: w, height: Math.max(subWidth - 1, 1),
            rx: 2, fill: color
          }, [])
        } else {
          const y = Math.min(zero, val(value))
          const h = Math.abs(val(value) - zero)
          rect = svgEl("rect", {
            x: offset, y: y, width: Math.max(subWidth - 1, 1), height: h,
            rx: 2, fill: color
          }, [])
        }
      } else {
        let base = 0
        let displayValue = value
        if (group === "stack100") {
          let total = 0
          for (let k = 0; k < series.length; k = k + 1) {
            const v = series[k].values[dataIndex]
            total = total + (typeof v === "number" ? Math.abs(v) : 0)
          }
          displayValue = total > 0 ? (Math.abs(value) / total) * 100 : 0
        }
        if (value >= 0) {
          base = stackPos
          stackPos = stackPos + displayValue
        } else {
          base = stackNeg
          stackNeg = stackNeg + displayValue
        }
        if (horizontal === true) {
          const x1 = val(base)
          const x2 = val(base + displayValue)
          rect = svgEl("rect", {
            x: Math.min(x1, x2), y: bandStart,
            width: Math.abs(x2 - x1), height: bandwidth, rx: 2, fill: color
          }, [])
        } else {
          const y1 = val(base)
          const y2 = val(base + displayValue)
          rect = svgEl("rect", {
            x: bandStart, y: Math.min(y1, y2),
            width: bandwidth, height: Math.abs(y2 - y1), rx: 2, fill: color
          }, [])
        }
      }

      if (rect !== null) {
        rect.setAttribute("part", "bar")
        rect.setAttribute("tabindex", "0")
        rect.setAttribute("role", "img")
        rect.setAttribute("aria-label",
          `${series[s].name}, ${category}: ${value}`)
        rect.appendChild(svgEl("title", null,
          `${series[s].name} - ${category}: ${value}`))
        const handler = () => {
          ctx.emit("mj-chart-bar-click", {
            series: series[s].name, category: category, value: value
          })
        }
        rect.addEventListener("click", handler)
        rect.addEventListener("keydown", (event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault()
            handler()
          }
        })
        plot.appendChild(rect)
      }
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


registerRenderer("bar", render);
registerRenderer("column", render);
