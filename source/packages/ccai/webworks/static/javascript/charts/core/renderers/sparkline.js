/*
 * sparkline.js
 *
 * Sparkline renderer — compact, minimal-chrome inline trend.
 *
 * Registered types:
 *   "sparkline" — line or bar sparkline
 *
 * ctx.attrs recognised:
 *   sparkline-variant  "line" | "bar" (default "line")
 *   show-markers       "true" | "false" (default "true") — first/last/min/max dots
 *   show-last-value    "true" | "false" (default "false") — trailing text label
 *
 * No axes or legends are drawn; the chart fills the entire surface.
 * Series data may use:
 *   series[].points  [{x, y}, ...]
 *   series[].values  [...]
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber, linePath, extent } from "../svgdraw.js";
import { linearScale, pointScale } from "../scales.js";


function _getValues(ser, categories) {
  /*
   * Extract a flat y-value array from a series.
   *
   * :param ser: A single series object.
   * :param categories: Model categories (used as x labels for values).
   * :returns: Array of {x, y} where x is a string label.
   */
  const xy = []
  if (ser.points !== undefined && ser.points !== null && ser.points.length > 0) {
    for (let p = 0; p < ser.points.length; p = p + 1) {
      const pt = ser.points[p]
      xy.push({ x: String(pt.x), y: typeof pt.y === "number" ? pt.y : null })
    }
  } else if (ser.values !== undefined && ser.values !== null) {
    for (let v = 0; v < ser.values.length; v = v + 1) {
      const cat = categories[v] !== undefined ? String(categories[v]) : String(v)
      xy.push({ x: cat, y: typeof ser.values[v] === "number" ? ser.values[v] : null })
    }
  }
  return xy
}


export function render(ctx) {
  /*
   * Render a sparkline chart.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const model = ctx.model
  const root = svgEl("g", { part: "plot" }, [])

  const variant = ctx.attrs("sparkline-variant", "line")
  const showMarkers = ctx.attrs("show-markers", "true") === "true"
  const showLastValue = ctx.attrs("show-last-value", "false") === "true"

  if (model.series.length === 0) {
    return root
  }

  /* Use the first series only — sparklines are single-series by convention. */
  const ser = model.series[0]
  const color = ctx.colorFor(ser.name)
  const xy = _getValues(ser, model.categories)
  const validXY = xy.filter((pt) => pt.y !== null)
  if (validXY.length === 0) {
    return root
  }

  /* Small margin: just enough for last-value label if requested. */
  const labelW = showLastValue === true ? 36 : 2
  const margin = { top: 2, right: labelW, bottom: 2, left: 2 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 4)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 4)

  const yVals = validXY.map((pt) => pt.y)
  const yExt = extent(yVals)
  let yMin = yExt[0]
  let yMax = yExt[1]
  if (yMin === yMax) {
    yMin = yMin - 1
    yMax = yMax + 1
  }

  const xLabels = xy.map((pt) => pt.x)
  const xScale = pointScale(xLabels, [0, plotW])
  const yScale = linearScale([yMin, yMax], [plotH, 0])

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  if (variant === "bar") {
    /* Bar sparkline: one <rect> per point. */
    const barCount = xLabels.length
    const barW = Math.max(plotW / barCount - 1, 1)
    const baseline = yScale(0)

    for (let p = 0; p < xy.length; p = p + 1) {
      const pt = xy[p]
      if (pt.y === null) {
        continue
      }
      const px = xScale(pt.x) - barW / 2
      const py = yScale(pt.y)
      const bh = Math.abs(py - baseline)

      const barEl = svgEl("rect", {
        x: px.toFixed(2),
        y: Math.min(py, baseline).toFixed(2),
        width: barW.toFixed(2),
        height: Math.max(bh, 1).toFixed(2),
        fill: color,
        part: "spark-bar",
        tabindex: "0",
        role: "img",
        "aria-label": `${pt.x}: ${formatNumber(pt.y)}`
      }, [])
      barEl.appendChild(svgEl("title", null, `${pt.x}: ${pt.y}`))
      const handler = (() => {
        const capturedX = pt.x
        const capturedY = pt.y
        return () => {
          ctx.emit("mj-chart-sparkline-click", { x: capturedX, y: capturedY })
        }
      })()
      barEl.addEventListener("click", handler)
      barEl.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault()
          handler()
        }
      })
      plot.appendChild(barEl)
    }
  } else {
    /* Line sparkline: one polyline + optional markers. */
    const pixelPoints = []
    for (let p = 0; p < xy.length; p = p + 1) {
      const pt = xy[p]
      if (pt.y === null) {
        pixelPoints.push(null)
        continue
      }
      pixelPoints.push({ x: xScale(pt.x), y: yScale(pt.y) })
    }

    const pathData = linePath(pixelPoints)
    if (pathData !== "") {
      plot.appendChild(svgEl("path", {
        d: pathData,
        fill: "none",
        stroke: color,
        "stroke-width": 1.5,
        "stroke-linejoin": "round",
        "stroke-linecap": "round"
      }, []))
    }

    if (showMarkers === true) {
      /* Find first, last, min, max indices among valid points. */
      let minIdx = 0
      let maxIdx = 0
      let minVal = yVals[0]
      let maxVal = yVals[0]
      for (let v = 1; v < yVals.length; v = v + 1) {
        if (yVals[v] < minVal) {
          minVal = yVals[v]
          minIdx = v
        }
        if (yVals[v] > maxVal) {
          maxVal = yVals[v]
          maxIdx = v
        }
      }

      const markerIndices = new Set([
        0,
        validXY.length - 1,
        minIdx,
        maxIdx
      ])

      for (const idx of markerIndices) {
        const pt = validXY[idx]
        if (pt === undefined) {
          continue
        }
        const px = xScale(pt.x)
        const py = yScale(pt.y)
        const dot = svgEl("circle", {
          cx: px.toFixed(2), cy: py.toFixed(2), r: 2.5,
          fill: color,
          stroke: "var(--mj-surface, #fff)",
          "stroke-width": 1,
          part: "spark-marker",
          tabindex: "0",
          role: "img",
          "aria-label": `${pt.x}: ${formatNumber(pt.y)}`
        }, [])
        dot.appendChild(svgEl("title", null, `${pt.x}: ${pt.y}`))
        const handler = (() => {
          const capturedX = pt.x
          const capturedY = pt.y
          return () => {
            ctx.emit("mj-chart-sparkline-click", { x: capturedX, y: capturedY })
          }
        })()
        dot.addEventListener("click", handler)
        dot.addEventListener("keydown", (event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault()
            handler()
          }
        })
        plot.appendChild(dot)
      }
    }
  }

  /* Optional last-value text label. */
  if (showLastValue === true && validXY.length > 0) {
    const lastPt = validXY[validXY.length - 1]
    const lastY = yScale(lastPt.y)
    plot.appendChild(svgEl("text", {
      x: plotW + 4,
      y: lastY + 4,
      "font-size": 10,
      fill: "var(--mj-text-muted, #6b7280)"
    }, formatNumber(lastPt.y)))
  }

  return root
}


registerRenderer("sparkline", render)
