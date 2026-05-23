/*
 * step.js
 *
 * Step / staircase renderer.
 *
 * Registered types:
 *   "step" — step-line chart
 *
 * ctx.attrs recognised:
 *   step-position   "before" | "after" | "middle" (default "after")
 *                   Controls where the vertical jump is placed relative to x.
 *   fill            "true" | "false" (default "false") — fill area to baseline.
 *   show-points     "true" | "false" (default "true") — change-point markers.
 *
 * Series data may use either:
 *   series[].points  [{x, y}, ...]
 *   series[].values  [...] aligned with model.categories
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, formatNumber, extent } from "../svgdraw.js";
import { linearScale, pointScale, niceTicks } from "../scales.js";


function _buildStepPath(pixelPoints, stepPosition, closeTo) {
  /*
   * Build a step path `d` string from an array of {x, y} pixel points.
   *
   * :param pixelPoints: Array of {x, y} (all non-null).
   * :param stepPosition: "before" | "after" | "middle".
   * :param closeTo: If not null, close the path to this y pixel value.
   * :returns: Path data string.
   */
  if (pixelPoints.length === 0) {
    return ""
  }

  let data = `M${pixelPoints[0].x.toFixed(2)},${pixelPoints[0].y.toFixed(2)}`

  for (let i = 1; i < pixelPoints.length; i = i + 1) {
    const prev = pixelPoints[i - 1]
    const curr = pixelPoints[i]

    if (stepPosition === "before") {
      /* Jump first, then go horizontal to next x. */
      data = data + ` V${curr.y.toFixed(2)} H${curr.x.toFixed(2)}`
    } else if (stepPosition === "middle") {
      /* Horizontal half-way, jump, then horizontal to next x. */
      const midX = (prev.x + curr.x) / 2
      data = data + ` H${midX.toFixed(2)} V${curr.y.toFixed(2)} H${curr.x.toFixed(2)}`
    } else {
      /* "after" — go horizontal first to next x, then jump. */
      data = data + ` H${curr.x.toFixed(2)} V${curr.y.toFixed(2)}`
    }
  }

  if (closeTo !== null && closeTo !== undefined) {
    const first = pixelPoints[0]
    const last = pixelPoints[pixelPoints.length - 1]
    data = data +
      ` V${closeTo.toFixed(2)} H${first.x.toFixed(2)} V${pixelPoints[0].y.toFixed(2)} Z`
  }

  return data
}


export function render(ctx) {
  /*
   * Render a step chart.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const model = ctx.model
  const root = svgEl("g", { part: "plot" }, [])

  const stepPosition = ctx.attrs("step-position", "after")
  const fillArea = ctx.attrs("fill", "false") === "true"
  const showPoints = ctx.attrs("show-points", "true") === "true"

  /* Normalise series to {name, xy:[{x,y}]}. */
  const normSeries = []
  for (let s = 0; s < model.series.length; s = s + 1) {
    const ser = model.series[s]
    const xy = []
    if (ser.points !== undefined && ser.points !== null && ser.points.length > 0) {
      for (let p = 0; p < ser.points.length; p = p + 1) {
        const pt = ser.points[p]
        xy.push({ x: String(pt.x), y: typeof pt.y === "number" ? pt.y : null })
      }
    } else if (ser.values !== undefined && ser.values !== null) {
      for (let v = 0; v < ser.values.length; v = v + 1) {
        const cat = model.categories[v] !== undefined
          ? String(model.categories[v]) : String(v)
        xy.push({ x: cat, y: typeof ser.values[v] === "number" ? ser.values[v] : null })
      }
    }
    normSeries.push({ name: ser.name, xy: xy })
  }

  if (normSeries.length === 0) {
    return root
  }

  /* Collect all x labels and y values. */
  const xLabelSet = []
  const xLabelSeen = {}
  const allY = []
  for (let s = 0; s < normSeries.length; s = s + 1) {
    const xy = normSeries[s].xy
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

  const yExt = extent(allY)
  let yMin = Math.min(0, yExt[0])
  let yMax = yExt[1]
  if (yMin === yMax) {
    yMax = yMin + 1
  }

  const margin = { top: 16, right: 16, bottom: 40, left: 52 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  const xScale = pointScale(xLabelSet, [0, plotW])
  const yScale = linearScale([yMin, yMax], [plotH, 0])

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  /* Gridlines + y-axis labels. */
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

  /* X-axis labels. */
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

  const baseline = yScale(0)

  /* Draw each series. */
  for (let s = 0; s < normSeries.length; s = s + 1) {
    const ser = normSeries[s]
    const color = ctx.colorFor(ser.name)
    const seriesGroup = svgEl("g", { part: "series" }, [])

    /* Build pixel-space point list, skipping nulls. */
    const pixelPoints = []
    for (let p = 0; p < ser.xy.length; p = p + 1) {
      const pt = ser.xy[p]
      if (pt.y === null) {
        continue
      }
      pixelPoints.push({ x: xScale(pt.x), y: yScale(pt.y), xLabel: pt.x, yVal: pt.y })
    }

    if (pixelPoints.length === 0) {
      continue
    }

    const closeTo = fillArea === true ? baseline : null
    const pathData = _buildStepPath(pixelPoints, stepPosition, closeTo)

    if (pathData !== "") {
      const pathEl = svgEl("path", {
        d: pathData,
        fill: fillArea === true ? color : "none",
        "fill-opacity": fillArea === true ? "0.25" : null,
        stroke: color,
        "stroke-width": 2,
        "stroke-linejoin": "miter"
      }, [])
      seriesGroup.appendChild(pathEl)
    }

    /* Change-point markers and interactive targets. */
    if (showPoints === true || true) {
      for (let p = 0; p < pixelPoints.length; p = p + 1) {
        const pt = pixelPoints[p]

        if (showPoints === true) {
          const dot = svgEl("circle", {
            cx: pt.x, cy: pt.y, r: 3,
            fill: color,
            stroke: "var(--mj-surface, #fff)",
            "stroke-width": 1.5
          }, [])
          seriesGroup.appendChild(dot)
        }

        const hit = svgEl("circle", {
          cx: pt.x, cy: pt.y, r: 6,
          fill: "transparent",
          tabindex: "0",
          role: "img",
          "aria-label": `${escapeHtml(ser.name)}, ${escapeHtml(pt.xLabel)}: ${formatNumber(pt.yVal)}`
        }, [])
        hit.appendChild(svgEl("title", null,
          `${ser.name} - ${pt.xLabel}: ${pt.yVal}`))
        const handler = (() => {
          const capturedSeries = ser.name
          const capturedX = pt.xLabel
          const capturedY = pt.yVal
          return () => {
            ctx.emit("mj-chart-step-click", {
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
    }

    plot.appendChild(seriesGroup)
  }

  return root
}


registerRenderer("step", render)
