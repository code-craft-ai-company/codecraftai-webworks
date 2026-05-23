/*
 * area.js
 *
 * Area / stacked-area / 100%-stacked-area renderer.
 *
 * Registered types:
 *   "area"         — single or multi-series filled area chart
 *   "stacked-area" — stacked area (alias; also triggered by stack="stack")
 *   "area100"      — 100% stacked area (alias; also triggered by stack="stack100")
 *
 * ctx.attrs recognised:
 *   stack          "none" | "stack" | "stack100" (default "none")
 *   curve          "linear" | "monotone" (default "linear")
 *
 * Series data may use either:
 *   series[].points  [{x, y}, ...]
 *   series[].values  [...] aligned with model.categories
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, formatNumber, linePath, smoothPath, extent } from "../svgdraw.js";
import { linearScale, pointScale, niceTicks } from "../scales.js";


function _normalise(series, categories) {
  /*
   * Convert each series to a flat {name, xy:[{x,y}]} structure.
   *
   * :param series: Model series array.
   * :param categories: Model categories array.
   * :returns: Normalised array.
   */
  const result = []
  for (let s = 0; s < series.length; s = s + 1) {
    const ser = series[s]
    const xy = []
    if (ser.points !== undefined && ser.points !== null && ser.points.length > 0) {
      for (let p = 0; p < ser.points.length; p = p + 1) {
        const pt = ser.points[p]
        xy.push({ x: String(pt.x), y: typeof pt.y === "number" ? pt.y : 0 })
      }
    } else if (ser.values !== undefined && ser.values !== null) {
      for (let v = 0; v < ser.values.length; v = v + 1) {
        const cat = categories[v] !== undefined ? String(categories[v]) : String(v)
        xy.push({ x: cat, y: typeof ser.values[v] === "number" ? ser.values[v] : 0 })
      }
    }
    result.push({ name: ser.name, xy: xy })
  }
  return result
}


function _stackedBands(normSeries, xLabels, mode) {
  /*
   * Compute stacked {x, y0, y1} bands for every series.
   *
   * :param normSeries: Output of _normalise.
   * :param xLabels: Ordered x label array.
   * :param mode: "stack" or "stack100".
   * :returns: Array of {name, bands:[{x, y0, y1}]}.
   */

  /* Build per-x totals for stack100 normalisation. */
  const totals = {}
  for (let s = 0; s < normSeries.length; s = s + 1) {
    const xy = normSeries[s].xy
    for (let p = 0; p < xy.length; p = p + 1) {
      const label = xy[p].x
      if (totals[label] === undefined) {
        totals[label] = 0
      }
      totals[label] = totals[label] + Math.abs(xy[p].y)
    }
  }

  const stacks = {}
  for (let i = 0; i < xLabels.length; i = i + 1) {
    stacks[xLabels[i]] = 0
  }

  const result = []
  for (let s = 0; s < normSeries.length; s = s + 1) {
    const ser = normSeries[s]
    const bands = []
    for (let p = 0; p < ser.xy.length; p = p + 1) {
      const label = ser.xy[p].x
      let rawY = ser.xy[p].y
      if (mode === "stack100") {
        const total = totals[label]
        rawY = total > 0 ? (rawY / total) * 100 : 0
      }
      const base = stacks[label] !== undefined ? stacks[label] : 0
      stacks[label] = base + rawY
      bands.push({ x: label, y0: base, y1: base + rawY })
    }
    result.push({ name: ser.name, bands: bands })
  }
  return result
}


function _bandPath(bands, xScale, yScale, curveMode) {
  /*
   * Build a closed area path from {x, y0, y1} band data.
   *
   * :param bands: Array of {x, y0, y1}.
   * :param xScale: Pixel x scale function.
   * :param yScale: Pixel y scale function.
   * :param curveMode: "linear" | "monotone".
   * :returns: Path data string.
   */
  const topPts = []
  const botPts = []
  for (let i = 0; i < bands.length; i = i + 1) {
    const b = bands[i]
    topPts.push({ x: xScale(b.x), y: yScale(b.y1) })
    botPts.push({ x: xScale(b.x), y: yScale(b.y0) })
  }

  const topPath = curveMode === "monotone" ? smoothPath(topPts) : linePath(topPts)
  if (topPath === "") {
    return ""
  }

  /* Close by tracing bottom in reverse. The bottom edge must continue
   * the same subpath (L commands), not start a new one (M), otherwise
   * fill creates two thin edges instead of a filled band. */
  const botReversed = botPts.slice().reverse()
  const botCommands = botReversed
    .map((point) => `L${point.x.toFixed(2)},${point.y.toFixed(2)}`)
    .join(" ")
  const data = `${topPath} ${botCommands} Z`
  return data
}


export function render(ctx) {
  /*
   * Render an area chart (plain, stacked, or 100%-stacked).
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const model = ctx.model
  const root = svgEl("g", { part: "plot" }, [])

  /* Resolve stack mode from both the type key and the explicit attr. */
  const typeKey = ctx.attrs("type", "area")
  let defaultStack = "none"
  if (typeKey === "stacked-area") {
    defaultStack = "stack"
  } else if (typeKey === "area100") {
    defaultStack = "stack100"
  }
  const stackMode = ctx.attrs("stack", defaultStack)
  const curveMode = ctx.attrs("curve", "linear")
  const fillOpacity = ctx.attrs("fill-opacity", "0.3")

  const normSeries = _normalise(model.series, model.categories)
  if (normSeries.length === 0) {
    return root
  }

  /* Collect ordered x labels. */
  const xLabelSet = []
  const xLabelSeen = {}
  for (let s = 0; s < normSeries.length; s = s + 1) {
    const xy = normSeries[s].xy
    for (let p = 0; p < xy.length; p = p + 1) {
      const label = xy[p].x
      if (xLabelSeen[label] !== true) {
        xLabelSet.push(label)
        xLabelSeen[label] = true
      }
    }
  }
  if (xLabelSet.length === 0) {
    return root
  }

  /* Determine y domain. */
  let yMin = 0
  let yMax = 0
  if (stackMode === "stack100") {
    yMax = 100
  } else if (stackMode === "stack") {
    const stacked = _stackedBands(normSeries, xLabelSet, "stack")
    for (let s = 0; s < stacked.length; s = s + 1) {
      const bands = stacked[s].bands
      for (let b = 0; b < bands.length; b = b + 1) {
        if (bands[b].y1 > yMax) {
          yMax = bands[b].y1
        }
      }
    }
  } else {
    const allY = []
    for (let s = 0; s < normSeries.length; s = s + 1) {
      for (let p = 0; p < normSeries[s].xy.length; p = p + 1) {
        allY.push(normSeries[s].xy[p].y)
      }
    }
    const ext = extent(allY)
    yMin = Math.min(0, ext[0])
    yMax = ext[1]
  }
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
    const tickLabel = stackMode === "stack100"
      ? `${formatNumber(tick)}%`
      : formatNumber(tick)
    plot.appendChild(svgEl("text", {
      x: -8, y: y + 4, "text-anchor": "end",
      "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
    }, tickLabel))
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

  /* Draw the areas. */
  if (stackMode === "stack" || stackMode === "stack100") {
    const stackedBands = _stackedBands(normSeries, xLabelSet, stackMode)
    for (let s = 0; s < stackedBands.length; s = s + 1) {
      const ser = stackedBands[s]
      const color = ctx.colorFor(normSeries[s].name)
      const pathData = _bandPath(ser.bands, xScale, yScale, curveMode)
      if (pathData === "") {
        continue
      }
      const areaEl = svgEl("path", {
        d: pathData,
        fill: color,
        "fill-opacity": fillOpacity,
        stroke: color,
        "stroke-width": 1.5,
        part: "area",
        tabindex: "0",
        role: "img",
        "aria-label": escapeHtml(normSeries[s].name)
      }, [])
      areaEl.appendChild(svgEl("title", null, normSeries[s].name))
      const capturedName = normSeries[s].name
      const handler = () => {
        ctx.emit("mj-chart-area-click", { series: capturedName })
      }
      areaEl.addEventListener("click", handler)
      areaEl.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault()
          handler()
        }
      })
      plot.appendChild(areaEl)
    }
  } else {
    /* Plain (unstacked) area — one area path per series closing to baseline. */
    for (let s = 0; s < normSeries.length; s = s + 1) {
      const ser = normSeries[s]
      const color = ctx.colorFor(ser.name)
      const topPts = []
      for (let p = 0; p < ser.xy.length; p = p + 1) {
        topPts.push({ x: xScale(ser.xy[p].x), y: yScale(ser.xy[p].y) })
      }
      const topPath = curveMode === "monotone" ? smoothPath(topPts) : linePath(topPts)
      if (topPath === "") {
        continue
      }
      const baseline = yScale(0)
      const first = topPts[0]
      const last = topPts[topPts.length - 1]
      const closePath = `L${last.x.toFixed(2)},${baseline.toFixed(2)} ` +
        `L${first.x.toFixed(2)},${baseline.toFixed(2)} Z`
      const pathData = `${topPath} ${closePath}`

      const areaEl = svgEl("path", {
        d: pathData,
        fill: color,
        "fill-opacity": fillOpacity,
        stroke: color,
        "stroke-width": 1.5,
        part: "area",
        tabindex: "0",
        role: "img",
        "aria-label": escapeHtml(ser.name)
      }, [])
      areaEl.appendChild(svgEl("title", null, ser.name))
      const capturedName = ser.name
      const handler = () => {
        ctx.emit("mj-chart-area-click", { series: capturedName })
      }
      areaEl.addEventListener("click", handler)
      areaEl.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault()
          handler()
        }
      })
      plot.appendChild(areaEl)
    }
  }

  return root
}


registerRenderer("area", render)
registerRenderer("stacked-area", render)
registerRenderer("area100", render)
