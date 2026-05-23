/*
 * line.js
 *
 * Line / multi-line renderer.
 *
 * Registered types:
 *   "line"      — single-series or multi-series line chart
 *   "multiline" — alias for "line"; any number of series
 *
 * ctx.attrs recognised:
 *   curve          "linear" | "monotone" (default "linear") — path interpolation
 *   show-points    "true" | "false" (default "false") — dot markers on data points
 *
 * Series data may use either:
 *   series[].points  [{x, y}, ...]  (categorical or time x values)
 *   series[].values  [...]          (index-aligned with model.categories)
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, formatNumber, linePath, smoothPath, extent } from "../svgdraw.js";
import { linearScale, pointScale, niceTicks } from "../scales.js";


function _collectXY(series, categories) {
  /*
   * Normalise each series to an array of {x (category string), y (number)}
   * regardless of whether the model uses points or values+categories.
   *
   * :param series: The series array from the model.
   * :param categories: The model categories array (may be empty).
   * :returns: Array of {name, xy:[{x,y}]} objects.
   */
  const result = []
  for (let s = 0; s < series.length; s = s + 1) {
    const ser = series[s]
    const xy = []
    if (ser.points !== undefined && ser.points !== null && ser.points.length > 0) {
      for (let p = 0; p < ser.points.length; p = p + 1) {
        const point = ser.points[p]
        const yNum = typeof point.y === "number" ? point.y : null
        xy.push({ x: String(point.x), y: yNum })
      }
    } else if (ser.values !== undefined && ser.values !== null) {
      for (let v = 0; v < ser.values.length; v = v + 1) {
        const cat = categories[v] !== undefined ? String(categories[v]) : String(v)
        const yNum = typeof ser.values[v] === "number" ? ser.values[v] : null
        xy.push({ x: cat, y: yNum })
      }
    }
    result.push({ name: ser.name, xy: xy })
  }
  return result
}


export function render(ctx) {
  /*
   * Render a line chart (single or multi-series).
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const model = ctx.model
  const root = svgEl("g", { part: "plot" }, [])

  const seriesData = _collectXY(model.series, model.categories)
  if (seriesData.length === 0) {
    return root
  }

  /* Gather all x labels and all y values across every series. */
  const xLabelSet = []
  const xLabelSeen = {}
  const allY = []
  for (let s = 0; s < seriesData.length; s = s + 1) {
    const xy = seriesData[s].xy
    for (let p = 0; p < xy.length; p = p + 1) {
      const label = xy[p].x
      if (xLabelSeen[label] !== true) {
        xLabelSet.push(label)
        xLabelSeen[label] = true
      }
      if (xy[p].y !== null) {
        allY.push(xy[p].y)
      }
    }
  }

  if (xLabelSet.length === 0 || allY.length === 0) {
    return root
  }

  const curveMode = ctx.attrs("curve", "linear")
  const showPoints = ctx.attrs("show-points", "false") === "true"

  const margin = { top: 16, right: 16, bottom: 40, left: 52 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  const yExtent = extent(allY)
  let yMin = yExtent[0]
  let yMax = yExtent[1]
  if (yMin === yMax) {
    yMin = yMin - 1
    yMax = yMax + 1
  }

  const xScale = pointScale(xLabelSet, [0, plotW])
  const yScale = linearScale([yMin, yMax], [plotH, 0])

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  /* Horizontal gridlines + y-axis tick labels. */
  const ticks = niceTicks(yMin, yMax, 5)
  for (let t = 0; t < ticks.length; t = t + 1) {
    const tick = ticks[t]
    const y = yScale(tick)
    plot.appendChild(svgEl("line", {
      x1: 0, y1: y, x2: plotW, y2: y,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    plot.appendChild(svgEl("text", {
      x: -8, y: y + 4, "text-anchor": "end",
      "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
    }, formatNumber(tick)))
  }

  /* X-axis category labels — sample to avoid overlap. */
  const labelStep = Math.max(1, Math.ceil(xLabelSet.length / 10))
  for (let i = 0; i < xLabelSet.length; i = i + labelStep) {
    const label = xLabelSet[i]
    const x = xScale(label)
    plot.appendChild(svgEl("text", {
      x: x, y: plotH + 16, "text-anchor": "middle",
      "font-size": 11, fill: "var(--mj-text, #14181f)"
    }, escapeHtml(label)))
  }

  /* Axis baseline. */
  plot.appendChild(svgEl("line", {
    x1: 0, y1: plotH, x2: plotW, y2: plotH,
    stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
  }, []))

  /* Draw each series. */
  for (let s = 0; s < seriesData.length; s = s + 1) {
    const ser = seriesData[s]
    const color = ctx.colorFor(ser.name)
    const seriesGroup = svgEl("g", { part: "series" }, [])

    /* Map xy to pixel points. */
    const pixelPoints = []
    for (let p = 0; p < ser.xy.length; p = p + 1) {
      const point = ser.xy[p]
      if (point.y === null) {
        pixelPoints.push(null)
        continue
      }
      const px = xScale(point.x)
      const py = yScale(point.y)
      pixelPoints.push({ x: px, y: py })
    }

    const pathData = curveMode === "monotone"
      ? smoothPath(pixelPoints)
      : linePath(pixelPoints)

    if (pathData !== "") {
      const pathEl = svgEl("path", {
        d: pathData,
        fill: "none",
        stroke: color,
        "stroke-width": 2,
        "stroke-linejoin": "round",
        "stroke-linecap": "round"
      }, [])
      seriesGroup.appendChild(pathEl)
    }

    /* Optional dot markers and interactive hit targets. */
    for (let p = 0; p < ser.xy.length; p = p + 1) {
      const point = ser.xy[p]
      if (point.y === null) {
        continue
      }
      const px = xScale(point.x)
      const py = yScale(point.y)

      if (showPoints === true) {
        const dot = svgEl("circle", {
          cx: px, cy: py, r: 3,
          fill: color,
          stroke: "var(--mj-surface, #fff)",
          "stroke-width": 1.5
        }, [])
        seriesGroup.appendChild(dot)
      }

      /* Invisible wider hit circle for interaction. */
      const hit = svgEl("circle", {
        cx: px, cy: py, r: 6,
        fill: "transparent",
        tabindex: "0",
        role: "img",
        "aria-label": `${escapeHtml(ser.name)}, ${escapeHtml(point.x)}: ${formatNumber(point.y)}`
      }, [])
      hit.appendChild(svgEl("title", null,
        `${ser.name} - ${point.x}: ${point.y}`))
      const handler = (() => {
        const capturedSeries = ser.name
        const capturedX = point.x
        const capturedY = point.y
        return () => {
          ctx.emit("mj-chart-line-click", {
            series: capturedSeries, x: capturedX, y: capturedY
          })
        }
      })()
      hit.addEventListener("click", handler)
      hit.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault()
          handler()
        }
      })
      seriesGroup.appendChild(hit)
    }

    plot.appendChild(seriesGroup)
  }

  return root
}


registerRenderer("line", render)
registerRenderer("multiline", render)
