/*
 * streamgraph.js
 *
 * Streamgraph renderer — flowing symmetric stacked area.
 *
 * Registered types:
 *   "streamgraph" — streamgraph (wiggle/silhouette/zero baseline)
 *
 * ctx.attrs recognised:
 *   baseline   "wiggle" | "silhouette" | "zero" (default "wiggle")
 *              wiggle    — ThemeRiver: minimises weighted slope of stream
 *              silhouette — centred stack (symmetric around y=0)
 *              zero      — bottom-aligned (equivalent to stacked area)
 *
 * The y-axis is hidden because y positions are layout artefacts.
 * Series data: series[].points [{x, y}] or series[].values [].
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, formatNumber, smoothPath, linePath } from "../svgdraw.js";
import { linearScale, pointScale, niceTicks } from "../scales.js";


function _getXY(ser, categories) {
  /*
   * Flatten a series to [{x, y}].
   */
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
  return xy
}


function _computeBaselines(normSeries, xLabels, baseline) {
  /*
   * Compute stacked y0/y1 pairs for every series at every x label.
   *
   * :param normSeries: [{name, xy:[{x,y}]}] — must all share the same xLabels.
   * :param xLabels: Ordered x labels array.
   * :param baseline: "wiggle" | "silhouette" | "zero".
   * :returns: [{name, bands:[{x, y0, y1}]}]
   */
  const n = normSeries.length
  const m = xLabels.length

  /* Build a 2-D array values[seriesIdx][xIdx]. */
  const values = []
  for (let s = 0; s < n; s = s + 1) {
    const row = []
    const xyMap = {}
    for (let p = 0; p < normSeries[s].xy.length; p = p + 1) {
      xyMap[normSeries[s].xy[p].x] = normSeries[s].xy[p].y
    }
    for (let i = 0; i < m; i = i + 1) {
      const val = xyMap[xLabels[i]]
      row.push(val !== undefined ? val : 0)
    }
    values.push(row)
  }

  /* Totals per x position. */
  const totals = []
  for (let i = 0; i < m; i = i + 1) {
    let sum = 0
    for (let s = 0; s < n; s = s + 1) {
      sum = sum + values[s][i]
    }
    totals.push(sum)
  }

  /* Compute raw (zero-baseline) stacks first. */
  const stacksY0 = []
  const stacksY1 = []
  for (let s = 0; s < n; s = s + 1) {
    stacksY0.push(new Array(m).fill(0))
    stacksY1.push(new Array(m).fill(0))
  }
  for (let i = 0; i < m; i = i + 1) {
    let acc = 0
    for (let s = 0; s < n; s = s + 1) {
      stacksY0[s][i] = acc
      acc = acc + values[s][i]
      stacksY1[s][i] = acc
    }
  }

  /* Compute displacement for the chosen baseline. */
  const displacement = new Array(m).fill(0)
  if (baseline === "silhouette") {
    for (let i = 0; i < m; i = i + 1) {
      displacement[i] = -totals[i] / 2
    }
  } else if (baseline === "wiggle") {
    /* Weighted slope minimisation (Lee & Favre 2010 simplified). */
    for (let i = 0; i < m; i = i + 1) {
      let sum = 0
      for (let s = 0; s < n; s = s + 1) {
        sum = sum + (n - s - 0.5) * values[s][i]
      }
      displacement[i] = totals[i] > 0 ? -sum / totals[i] : 0
    }
  }

  /* Apply displacement and build result. */
  const result = []
  for (let s = 0; s < n; s = s + 1) {
    const bands = []
    for (let i = 0; i < m; i = i + 1) {
      bands.push({
        x: xLabels[i],
        y0: stacksY0[s][i] + displacement[i],
        y1: stacksY1[s][i] + displacement[i]
      })
    }
    result.push({ name: normSeries[s].name, bands: bands })
  }
  return result
}


function _streamPath(bands, xScale, yScale, curveMode) {
  /*
   * Build a closed path for a single stream band.
   *
   * :param bands: Array of {x, y0, y1}.
   * :param xScale: Pixel x scale.
   * :param yScale: Pixel y scale.
   * :param curveMode: "monotone" | "linear".
   * :returns: Path data string.
   */
  const topPts = []
  const botPts = []
  for (let i = 0; i < bands.length; i = i + 1) {
    topPts.push({ x: xScale(bands[i].x), y: yScale(bands[i].y1) })
    botPts.push({ x: xScale(bands[i].x), y: yScale(bands[i].y0) })
  }

  const topPath = curveMode === "monotone" ? smoothPath(topPts) : linePath(topPts)
  if (topPath === "") {
    return ""
  }

  /* Build the bottom edge as a CONTINUATION of the top path, not a new
   * subpath: replace the leading M command with L so fill produces a
   * filled band, not two thin edges. */
  const botReversed = botPts.slice().reverse()
  const botRaw = curveMode === "monotone"
    ? smoothPath(botReversed)
    : linePath(botReversed)
  const botPath = botRaw.replace(/^M/, "L")

  const data = `${topPath} ${botPath} Z`
  return data
}


export function render(ctx) {
  /*
   * Render a streamgraph.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const model = ctx.model
  const root = svgEl("g", { part: "plot" }, [])

  if (model.series.length === 0) {
    return root
  }

  const baselineMode = ctx.attrs("baseline", "wiggle")
  const curveMode = ctx.attrs("curve", "monotone")

  /* Normalise series. */
  const normSeries = []
  for (let s = 0; s < model.series.length; s = s + 1) {
    normSeries.push({
      name: model.series[s].name,
      xy: _getXY(model.series[s], model.categories)
    })
  }

  /* Collect ordered x labels. */
  const xLabelSet = []
  const xLabelSeen = {}
  for (let s = 0; s < normSeries.length; s = s + 1) {
    for (let p = 0; p < normSeries[s].xy.length; p = p + 1) {
      const label = normSeries[s].xy[p].x
      if (xLabelSeen[label] !== true) {
        xLabelSet.push(label)
        xLabelSeen[label] = true
      }
    }
  }

  if (xLabelSet.length === 0) {
    return root
  }

  /* Compute stacked bands. */
  const stackedBands = _computeBaselines(normSeries, xLabelSet, baselineMode)

  /* Find the y domain of all band y0/y1 values. */
  let yMin = Infinity
  let yMax = -Infinity
  for (let s = 0; s < stackedBands.length; s = s + 1) {
    const bands = stackedBands[s].bands
    for (let b = 0; b < bands.length; b = b + 1) {
      if (bands[b].y0 < yMin) {
        yMin = bands[b].y0
      }
      if (bands[b].y1 > yMax) {
        yMax = bands[b].y1
      }
    }
  }
  if (yMin === Infinity) {
    yMin = 0
  }
  if (yMax === -Infinity) {
    yMax = 1
  }
  if (yMin === yMax) {
    yMax = yMin + 1
  }

  /* Layout. */
  const margin = { top: 16, right: 16, bottom: 32, left: 16 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  const xScale = pointScale(xLabelSet, [0, plotW])
  const yScale = linearScale([yMin, yMax], [plotH, 0])

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  /* Draw streams. */
  for (let s = 0; s < stackedBands.length; s = s + 1) {
    const ser = stackedBands[s]
    const color = ctx.colorFor(normSeries[s].name)
    const pathData = _streamPath(ser.bands, xScale, yScale, curveMode)

    if (pathData === "") {
      continue
    }

    const streamEl = svgEl("path", {
      d: pathData,
      fill: color,
      "fill-opacity": "0.82",
      stroke: "var(--mj-surface, #fff)",
      "stroke-width": 0.5,
      part: "stream",
      tabindex: "0",
      role: "img",
      "aria-label": escapeHtml(normSeries[s].name)
    }, [])
    streamEl.appendChild(svgEl("title", null, normSeries[s].name))
    const capturedName = normSeries[s].name
    const handler = () => {
      ctx.emit("mj-chart-stream-click", { series: capturedName })
    }
    streamEl.addEventListener("click", handler)
    streamEl.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault()
        handler()
      }
    })
    plot.appendChild(streamEl)

    /* Inline label: place at the x midpoint, y midpoint of middle band. */
    const mid = Math.floor(ser.bands.length / 2)
    if (mid < ser.bands.length) {
      const midBand = ser.bands[mid]
      const labelX = xScale(midBand.x)
      const labelY = yScale((midBand.y0 + midBand.y1) / 2) + 4
      const bandHeight = Math.abs(yScale(midBand.y0) - yScale(midBand.y1))
      if (bandHeight > 14) {
        plot.appendChild(svgEl("text", {
          x: labelX, y: labelY, "text-anchor": "middle",
          "font-size": 11, fill: "var(--mj-text, #14181f)",
          "pointer-events": "none"
        }, escapeHtml(normSeries[s].name)))
      }
    }
  }

  /* X-axis labels. */
  const labelStep = Math.max(1, Math.ceil(xLabelSet.length / 10))
  for (let i = 0; i < xLabelSet.length; i = i + labelStep) {
    const label = xLabelSet[i]
    const x = xScale(label)
    plot.appendChild(svgEl("text", {
      x: x, y: plotH + 14, "text-anchor": "middle",
      "font-size": 10, fill: "var(--mj-text-muted, #6b7280)"
    }, escapeHtml(label)))
  }

  /* Axis baseline. */
  plot.appendChild(svgEl("line", {
    x1: 0, y1: plotH, x2: plotW, y2: plotH,
    stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1
  }, []))

  return root
}


registerRenderer("streamgraph", render)
