/*
 * errorbar.js
 *
 * Error bar / confidence-interval renderer.
 *
 * Registers: "errorbar", "confidence-interval"
 *
 * JSON shape (ctx.model.series[].groups):
 *   { category, value, error_low, error_high, bar? }
 *
 *   value       — central estimate
 *   error_low   — positive half-width below value
 *   error_high  — positive half-width above value
 *   bar         — (optional boolean) render value as a filled bar instead of a dot
 *
 * ctx.attrs("cap-width", 8)  — width of the whisker end-caps in px
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, formatNumber } from "../svgdraw.js";
import { linearScale, bandScale, niceTicks } from "../scales.js";


export function render(ctx) {
  /*
   * Render an error-bar or confidence-interval chart.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const model = ctx.model
  const horizontal = ctx.orientation === "horizontal"
  const capWidth = parseFloat(ctx.attrs("cap-width", 8)) || 8

  const root = svgEl("g", { part: "plot" }, [])

  const series = (model !== null && model !== undefined && Array.isArray(model.series) === true)
    ? model.series
    : []

  if (series.length === 0) {
    return root
  }

  /* Collect all categories across all series. */
  const catSet = []
  const catSeen = {}
  for (let s = 0; s < series.length; s = s + 1) {
    const groups = Array.isArray(series[s].groups) ? series[s].groups : []
    for (let g = 0; g < groups.length; g = g + 1) {
      const cat = groups[g].category
      if (catSeen[cat] !== true) {
        catSet.push(cat)
        catSeen[cat] = true
      }
    }
  }

  if (catSet.length === 0) {
    return root
  }

  /* Value domain: extend by error extents. */
  let valueMin = Infinity
  let valueMax = -Infinity
  for (let s = 0; s < series.length; s = s + 1) {
    const groups = Array.isArray(series[s].groups) ? series[s].groups : []
    for (let g = 0; g < groups.length; g = g + 1) {
      const pt = groups[g]
      const lo = pt.value - (pt.error_low || 0)
      const hi = pt.value + (pt.error_high || 0)
      if (lo < valueMin) {
        valueMin = lo
      }
      if (hi > valueMax) {
        valueMax = hi
      }
    }
  }
  if (valueMin === Infinity || valueMax === -Infinity) {
    valueMin = 0
    valueMax = 1
  }
  if (valueMin === valueMax) {
    valueMin = valueMin - 1
    valueMax = valueMax + 1
  }

  const margin = { top: 16, right: 16, bottom: 40, left: 60 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  const cat = bandScale(catSet, [0, horizontal ? plotH : plotW], 0.2)
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

  /* Zero reference line. */
  if (valueMin <= 0 && valueMax >= 0) {
    const zeroPos = val(0)
    if (horizontal === true) {
      plot.appendChild(svgEl("line", {
        x1: zeroPos, y1: 0, x2: zeroPos, y2: plotH,
        stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
      }, []))
    } else {
      plot.appendChild(svgEl("line", {
        x1: 0, y1: zeroPos, x2: plotW, y2: zeroPos,
        stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
      }, []))
    }
  }

  const bandwidth = cat.bandwidth()
  const subWidth = series.length > 0 ? bandwidth / series.length : bandwidth

  /* Draw marks. */
  for (let s = 0; s < series.length; s = s + 1) {
    const serie = series[s]
    const groups = Array.isArray(serie.groups) ? serie.groups : []
    const color = ctx.colorFor(serie.name)

    for (let g = 0; g < groups.length; g = g + 1) {
      const pt = groups[g]
      const bandStart = cat(pt.category)
      const center = bandStart + s * subWidth + subWidth / 2

      const valuePx = val(pt.value)
      const lowPx = val(pt.value - (pt.error_low || 0))
      const highPx = val(pt.value + (pt.error_high || 0))

      const label = `${serie.name}, ${pt.category}: ${formatNumber(pt.value)} ` +
        `[${formatNumber(pt.value - (pt.error_low || 0))}, ` +
        `${formatNumber(pt.value + (pt.error_high || 0))}]`

      const group = svgEl("g", {
        part: "errorbar",
        tabindex: "0",
        role: "img",
        "aria-label": label
      }, [])
      group.appendChild(svgEl("title", null, label))

      if (horizontal === true) {
        /* Whisker shaft. */
        group.appendChild(svgEl("line", {
          x1: lowPx, y1: center, x2: highPx, y2: center,
          stroke: color, "stroke-width": 1.5
        }, []))
        /* End caps. */
        const halfCap = capWidth / 2
        group.appendChild(svgEl("line", {
          x1: lowPx, y1: center - halfCap, x2: lowPx, y2: center + halfCap,
          stroke: color, "stroke-width": 1.5
        }, []))
        group.appendChild(svgEl("line", {
          x1: highPx, y1: center - halfCap, x2: highPx, y2: center + halfCap,
          stroke: color, "stroke-width": 1.5
        }, []))
        /* Centre mark: bar or circle. */
        if (pt.bar === true) {
          const barH = Math.max(subWidth - 2, 1)
          const barY = center - barH / 2
          const barX = Math.min(val(0), valuePx)
          const barW = Math.abs(valuePx - val(0))
          group.appendChild(svgEl("rect", {
            x: barX, y: barY, width: barW, height: barH,
            rx: 2, fill: color, opacity: 0.7
          }, []))
        } else {
          group.appendChild(svgEl("circle", {
            cx: valuePx, cy: center, r: 5,
            fill: color
          }, []))
        }
      } else {
        /* Whisker shaft. */
        group.appendChild(svgEl("line", {
          x1: center, y1: lowPx, x2: center, y2: highPx,
          stroke: color, "stroke-width": 1.5
        }, []))
        /* End caps. */
        const halfCap = capWidth / 2
        group.appendChild(svgEl("line", {
          x1: center - halfCap, y1: lowPx, x2: center + halfCap, y2: lowPx,
          stroke: color, "stroke-width": 1.5
        }, []))
        group.appendChild(svgEl("line", {
          x1: center - halfCap, y1: highPx, x2: center + halfCap, y2: highPx,
          stroke: color, "stroke-width": 1.5
        }, []))
        /* Centre mark: bar or circle. */
        if (pt.bar === true) {
          const barW = Math.max(subWidth - 2, 1)
          const barX = center - barW / 2
          const barTop = Math.min(val(0), valuePx)
          const barH = Math.abs(valuePx - val(0))
          group.appendChild(svgEl("rect", {
            x: barX, y: barTop, width: barW, height: barH,
            rx: 2, fill: color, opacity: 0.7
          }, []))
        } else {
          group.appendChild(svgEl("circle", {
            cx: center, cy: valuePx, r: 5,
            fill: color
          }, []))
        }
      }

      const handler = () => {
        ctx.emit("mj-chart-errorbar-click", {
          series: serie.name,
          category: pt.category,
          value: pt.value,
          low: pt.value - (pt.error_low || 0),
          high: pt.value + (pt.error_high || 0)
        })
      }
      group.addEventListener("click", handler)
      group.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault()
          handler()
        }
      })

      plot.appendChild(group)
    }
  }

  /* Category axis labels. */
  for (let c = 0; c < catSet.length; c = c + 1) {
    const category = catSet[c]
    const bandStart = cat(category)
    const bandMid = bandStart + bandwidth / 2
    if (horizontal === true) {
      plot.appendChild(svgEl("text", {
        x: -8, y: bandMid + 4, "text-anchor": "end",
        "font-size": 11, fill: "var(--mj-text, #14181f)"
      }, escapeHtml(category)))
    } else {
      plot.appendChild(svgEl("text", {
        x: bandMid, y: plotH + 18, "text-anchor": "middle",
        "font-size": 11, fill: "var(--mj-text, #14181f)"
      }, escapeHtml(category)))
    }
  }

  return root
}


registerRenderer("errorbar", render)
registerRenderer("confidence-interval", render)
