/*
 * histogram.js
 *
 * Histogram / Density / Frequency-Polygon renderer.
 *
 * Registers: "histogram", "density", "frequency-polygon"
 * The requested type (ctx.type) picks the drawing:
 *   histogram          bars (or a KDE curve with smooth="kde", or a polygon
 *                      with display="polygon")
 *   density            Gaussian kernel density curves, one per series
 *   frequency-polygon  a line through the bin midpoints, closed to zero at
 *                      both ends
 *
 * ctx.model.series data shapes:
 *   - samples: [n, …]            renderer bins / smooths internally; values
 *                                that are not finite numbers are missing data
 *   - bins: [{x0, x1, count}]    pre-binned; used as given (the density type
 *                                draws a curve through the bin densities)
 * Every samples series is counted into ONE shared set of bin edges computed
 * from the pooled range, so overlaid and stacked series line up.
 *
 * Relevant ctx.attrs:
 *   bin-count   number of bins (default: bin-method)
 *   bin-width   bin width in data units (wins over bin-count)
 *   bin-method  "sturges" (default) | "scott" | "fd" (Freedman-Diaconis)
 *   group       "overlay" | "stack" (default "overlay")
 *   normalize   "density" — bar / polygon heights are count / (n * width),
 *               so each series' area is 1
 *   smooth      "kde" — histogram type draws a KDE curve
 *   display     "polygon" — histogram type draws a frequency polygon
 *   bandwidth   KDE bandwidth in data units (Silverman's rule otherwise)
 *   fill        "area" (default) | "none" for density / polygon modes
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber, linePath, areaPath, monotonePath } from "../svgdraw.js";
import { linearScale, niceDomain, niceTicks } from "../scales.js";
import {
  finiteValues, sortNumbers, quantileSorted, silvermanBandwidth, gaussianDensity,
  linspace, binSeries, isFiniteNumber, hasSeriesSamples, axisLayer,
  drawTicks, drawAxisTitle, drawBaseline, tickCount, activateOnKey, focusableMark
} from "./diststats.js";

/* KDE evaluation points per curve. */
const KDE_POINTS = 161;

/* A KDE curve extends this many bandwidths past the data on each side. */
const KDE_TAIL_BANDWIDTHS = 3;


/* ── data preparation ────────────────────────────────────────────────────── */

function _binOptions(ctx) {
  /*
   * The binning options read from the host attributes.
   */
  const count = parseInt(ctx.attrs("bin-count", ""), 10)
  const width = parseFloat(ctx.attrs("bin-width", ""))
  const options = {
    count: isFiniteNumber(count) === true && count > 0 ? count : null,
    width: isFiniteNumber(width) === true && width > 0 ? width : null,
    method: ctx.attrs("bin-method", "sturges")
  }
  return options
}


function _binHeight(bin, total, normalized) {
  /*
   * The drawn height of a bin: its count, or count / (n * width).
   */
  if (normalized === false) {
    return bin.count
  }
  const width = bin.x1 - bin.x0
  const height = total > 0 && width > 0 ? bin.count / (total * width) : 0
  return height
}


function _densityCurve(entry, bandwidthOverride) {
  /*
   * The density curve of one series: a KDE of its samples extended three
   * bandwidths past the data, or (pre-binned input) the bin densities at
   * the bin midpoints, closed to zero half a bin beyond each end.
   *
   * :returns: { xs, ys, bandwidth } or null when the series has no data.
   */
  if (entry.samples !== null && entry.samples.length > 0) {
    const sorted = sortNumbers(entry.samples)
    const bandwidth = bandwidthOverride > 0 ? bandwidthOverride : silvermanBandwidth(sorted)
    const low = sorted[0] - KDE_TAIL_BANDWIDTHS * bandwidth
    const high = sorted[sorted.length - 1] + KDE_TAIL_BANDWIDTHS * bandwidth
    const xs = linspace(low, high, KDE_POINTS)
    const ys = gaussianDensity(sorted, bandwidth, xs)
    return { xs: xs, ys: ys, bandwidth: bandwidth }
  }
  if (entry.bins.length > 0 && entry.total > 0) {
    const first = entry.bins[0]
    const last = entry.bins[entry.bins.length - 1]
    const xs = [first.x0 - (first.x1 - first.x0) / 2]
    const ys = [0]
    for (let bi = 0; bi < entry.bins.length; bi = bi + 1) {
      const bin = entry.bins[bi]
      xs.push((bin.x0 + bin.x1) / 2)
      ys.push(_binHeight(bin, entry.total, true))
    }
    xs.push(last.x1 + (last.x1 - last.x0) / 2)
    ys.push(0)
    return { xs: xs, ys: ys, bandwidth: null }
  }
  return null
}


function _modeOf(ctx) {
  /*
   * The drawing mode: "bars", "kde" or "polygon".
   */
  if (ctx.type === "density") {
    return "kde"
  }
  if (ctx.type === "frequency-polygon") {
    return "polygon"
  }
  if (ctx.attrs("smooth", "") === "kde") {
    return "kde"
  }
  if (ctx.attrs("display", "bar") === "polygon") {
    return "polygon"
  }
  return "bars"
}


/* ── drawing ─────────────────────────────────────────────────────────────── */

function _toPixel(binScale, valScale, horizontal, x, height) {
  /*
   * A data point (bin position x, height) in pixels for the orientation.
   */
  if (horizontal === true) {
    return { x: valScale(height), y: binScale(x) }
  }
  return { x: binScale(x), y: valScale(height) }
}


function _closedArea(points, valScale, horizontal) {
  /*
   * Fill path under a curve, closed against the zero line of the value
   * axis (x = valScale(0) when horizontal, y = valScale(0) when vertical).
   */
  const zero = valScale(0)
  const lower = points.map((point) => {
    if (horizontal === true) {
      return { x: zero, y: point.y }
    }
    return { x: point.x, y: zero }
  })
  const data = areaPath(points, lower)
  return data
}


function _binLabel(name, bin, normalized, height) {
  /*
   * Accessible text of one bin.
   */
  const range = `${formatNumber(bin.x0)}–${formatNumber(bin.x1)}`
  const density = normalized === true ? `, density ${formatNumber(height, { maximumSignificantDigits: 3 })}` : ""
  const label = `${name}, ${range}: ${formatNumber(bin.count)}${density}`
  return label
}


function _drawBars(marks, resolved, binScale, valScale, ctx, horizontal, stacked, normalized) {
  /*
   * Histogram bars: one rect per non-empty bin and series. Overlaid series
   * are translucent; stacked series sit on the series below them.
   */
  const stackBase = new Map()
  const overlay = stacked === false && resolved.length > 1

  for (let si = 0; si < resolved.length; si = si + 1) {
    const entry = resolved[si]
    const color = ctx.colorFor(entry.name)
    const group = svgEl("g", { part: "series" }, [])

    for (let bi = 0; bi < entry.bins.length; bi = bi + 1) {
      const bin = entry.bins[bi]
      const height = _binHeight(bin, entry.total, normalized)
      const key = `${bin.x0}|${bin.x1}`
      const base = stacked === true && stackBase.has(key) === true ? stackBase.get(key) : 0
      if (stacked === true) {
        stackBase.set(key, base + height)
      }
      if (bin.count <= 0) {
        continue
      }

      const start = binScale(bin.x0)
      const end = binScale(bin.x1)
      const thickness = Math.max(Math.abs(end - start) - 1, 1)
      const from = valScale(base)
      const to = valScale(base + height)
      let rect = null
      if (horizontal === true) {
        rect = svgEl("rect", {
          x: Math.min(from, to), y: Math.min(start, end) + 0.5,
          width: Math.abs(to - from), height: thickness
        }, [])
      } else {
        rect = svgEl("rect", {
          x: Math.min(start, end) + 0.5, y: Math.min(from, to),
          width: thickness, height: Math.abs(to - from)
        }, [])
      }
      rect.setAttribute("fill", color)
      if (overlay === true) {
        rect.setAttribute("fill-opacity", "0.55")
      }
      rect.setAttribute("part", "bar")
      focusableMark(rect, _binLabel(entry.name, bin, normalized, height))
      const handlerBin = bin
      activateOnKey(rect, () => {
        ctx.emit("mj-chart-bar-click", {
          series: entry.name, x0: handlerBin.x0, x1: handlerBin.x1, count: handlerBin.count
        })
      })
      group.appendChild(rect)
    }
    marks.appendChild(group)
  }
  return
}


function _drawCurves(marks, curves, binScale, valScale, ctx, horizontal, fillMode) {
  /*
   * Density curves (filled area plus line), one per series.
   */
  for (let ci = 0; ci < curves.length; ci = ci + 1) {
    const curve = curves[ci]
    const color = ctx.colorFor(curve.name)
    const points = curve.xs.map((x, index) => _toPixel(binScale, valScale, horizontal, x, curve.ys[index]))
    const group = svgEl("g", { part: "series" }, [])

    if (fillMode !== "none") {
      group.appendChild(svgEl("path", {
        d: _closedArea(points, valScale, horizontal),
        fill: color, "fill-opacity": 0.25, stroke: "none", part: "density-area"
      }, []))
    }
    const line = svgEl("path", {
      d: curve.preBinned === true ? monotonePath(points) : linePath(points),
      fill: "none", stroke: color, "stroke-width": 2, "stroke-linejoin": "round"
    }, [])
    line.setAttribute("part", "density-line")
    let peakIndex = 0
    for (let index = 1; index < curve.ys.length; index = index + 1) {
      if (curve.ys[index] > curve.ys[peakIndex]) {
        peakIndex = index
      }
    }
    const bandwidthText = curve.bandwidth !== null
      ? `, bandwidth ${formatNumber(curve.bandwidth, { maximumSignificantDigits: 3 })}` : ""
    focusableMark(line, `${curve.name} density curve, peak at ` +
      `${formatNumber(curve.xs[peakIndex], { maximumSignificantDigits: 4 })}${bandwidthText}`)
    activateOnKey(line, () => {
      ctx.emit("mj-chart-density-click", { series: curve.name, bandwidth: curve.bandwidth })
    })
    group.appendChild(line)
    marks.appendChild(group)
  }
  return
}


function _drawPolygons(marks, resolved, binScale, valScale, ctx, horizontal, fillMode, normalized) {
  /*
   * Frequency polygons: a line through each bin midpoint, starting and
   * ending at zero half a bin beyond the outer bins, with a dot per bin.
   */
  for (let si = 0; si < resolved.length; si = si + 1) {
    const entry = resolved[si]
    if (entry.bins.length === 0) {
      continue
    }
    const color = ctx.colorFor(entry.name)
    const group = svgEl("g", { part: "series" }, [])
    const first = entry.bins[0]
    const last = entry.bins[entry.bins.length - 1]

    const points = [_toPixel(binScale, valScale, horizontal, first.x0 - (first.x1 - first.x0) / 2, 0)]
    for (let bi = 0; bi < entry.bins.length; bi = bi + 1) {
      const bin = entry.bins[bi]
      points.push(_toPixel(binScale, valScale, horizontal, (bin.x0 + bin.x1) / 2,
        _binHeight(bin, entry.total, normalized)))
    }
    points.push(_toPixel(binScale, valScale, horizontal, last.x1 + (last.x1 - last.x0) / 2, 0))

    if (fillMode !== "none") {
      group.appendChild(svgEl("path", {
        d: _closedArea(points, valScale, horizontal),
        fill: color, "fill-opacity": 0.2, stroke: "none", part: "polygon-area"
      }, []))
    }
    group.appendChild(svgEl("path", {
      d: linePath(points), fill: "none", stroke: color, "stroke-width": 2,
      "stroke-linejoin": "round", part: "polygon-line"
    }, []))

    for (let bi = 0; bi < entry.bins.length; bi = bi + 1) {
      const bin = entry.bins[bi]
      const height = _binHeight(bin, entry.total, normalized)
      const point = points[bi + 1]
      const dot = svgEl("circle", { cx: point.x, cy: point.y, r: 3.5, fill: color }, [])
      dot.setAttribute("part", "polygon-point")
      focusableMark(dot, _binLabel(entry.name, bin, normalized, height))
      const handlerBin = bin
      activateOnKey(dot, () => {
        ctx.emit("mj-chart-polygon-click", {
          series: entry.name, x0: handlerBin.x0, x1: handlerBin.x1, count: handlerBin.count
        })
      })
      group.appendChild(dot)
    }
    marks.appendChild(group)
  }
  return
}


/* ── accessible table ────────────────────────────────────────────────────── */

function _binTable(resolved, normalized, caption) {
  /*
   * One row per bin and series: [series, from, to, count (, density)].
   */
  const columns = ["Series", "From", "To", "Count"]
  if (normalized === true) {
    columns.push("Density")
  }
  const rows = []
  for (let si = 0; si < resolved.length; si = si + 1) {
    const entry = resolved[si]
    for (let bi = 0; bi < entry.bins.length; bi = bi + 1) {
      const bin = entry.bins[bi]
      const row = [entry.name, bin.x0, bin.x1, bin.count]
      if (normalized === true) {
        row.push(_binHeight(bin, entry.total, true))
      }
      rows.push(row)
    }
  }
  return { columns: columns, rows: rows, caption: caption }
}


function _densityTable(resolved, curves) {
  /*
   * One row per series: observations, quartiles, bandwidth, peak.
   */
  const rows = []
  for (let ci = 0; ci < curves.length; ci = ci + 1) {
    const curve = curves[ci]
    const entry = resolved[curve.index]
    const sorted = entry.samples !== null ? sortNumbers(entry.samples) : []
    let peakIndex = 0
    for (let index = 1; index < curve.ys.length; index = index + 1) {
      if (curve.ys[index] > curve.ys[peakIndex]) {
        peakIndex = index
      }
    }
    rows.push([
      entry.name,
      entry.total,
      sorted.length > 0 ? sorted[0] : "",
      sorted.length > 0 ? quantileSorted(sorted, 0.5) : "",
      sorted.length > 0 ? sorted[sorted.length - 1] : "",
      curve.bandwidth !== null ? curve.bandwidth : "",
      curve.xs[peakIndex]
    ])
  }
  return {
    columns: ["Series", "Observations", "Min", "Median", "Max", "Bandwidth", "Peak at"],
    rows: rows,
    caption: "Density estimate per series"
  }
}


/* ── main render ─────────────────────────────────────────────────────────── */

export function render(ctx) {
  /*
   * Render a histogram, density plot or frequency polygon (see header).
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const horizontal = ctx.orientation === "horizontal"
  const mode = _modeOf(ctx)
  const stacked = mode === "bars" && ctx.attrs("group", "overlay") === "stack"
  const normalized = mode !== "kde" && ctx.attrs("normalize", "") === "density"
  const fillMode = ctx.attrs("fill", "area")
  const bandwidthAttr = parseFloat(ctx.attrs("bandwidth", ""))
  const bandwidthOverride = isFiniteNumber(bandwidthAttr) === true && bandwidthAttr > 0 ? bandwidthAttr : 0

  const root = svgEl("g", { part: "plot" }, [])
  const series = Array.isArray(ctx.model.series) === true ? ctx.model.series : []
  const prepared = binSeries(series, _binOptions(ctx))
  const resolved = prepared.series.filter((entry) => entry.bins.length > 0)
  if (resolved.length === 0) {
    return root
  }

  /* Extent of the bin axis and of the value axis. */
  let binMin = Infinity
  let binMax = -Infinity
  let valueMax = 0
  const curves = []
  if (mode === "kde") {
    for (let si = 0; si < resolved.length; si = si + 1) {
      const curve = _densityCurve(resolved[si], bandwidthOverride)
      if (curve === null) {
        continue
      }
      curve.name = resolved[si].name
      curve.index = si
      curve.preBinned = resolved[si].preBinned
      curves.push(curve)
      binMin = Math.min(binMin, curve.xs[0])
      binMax = Math.max(binMax, curve.xs[curve.xs.length - 1])
      for (let index = 0; index < curve.ys.length; index = index + 1) {
        valueMax = Math.max(valueMax, curve.ys[index])
      }
    }
  } else {
    const stackTotals = new Map()
    for (let si = 0; si < resolved.length; si = si + 1) {
      const entry = resolved[si]
      for (let bi = 0; bi < entry.bins.length; bi = bi + 1) {
        const bin = entry.bins[bi]
        const height = _binHeight(bin, entry.total, normalized)
        let width = bin.x1 - bin.x0
        if (mode !== "polygon") {
          width = 0
        }
        binMin = Math.min(binMin, bin.x0 - width / 2)
        binMax = Math.max(binMax, bin.x1 + width / 2)
        if (stacked === true) {
          const key = `${bin.x0}|${bin.x1}`
          const total = (stackTotals.has(key) === true ? stackTotals.get(key) : 0) + height
          stackTotals.set(key, total)
          valueMax = Math.max(valueMax, total)
        } else {
          valueMax = Math.max(valueMax, height)
        }
      }
    }
  }
  if (binMin === Infinity) {
    return root
  }

  const countAxis = mode !== "kde" && normalized === false
  const margin = { top: 16, right: 20, bottom: 44, left: 64 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)
  const valueLength = horizontal === true ? plotW : plotH
  const binLength = horizontal === true ? plotH : plotW

  const valueTickCount = tickCount(valueLength, horizontal === true ? 70 : 40)
  let valueTop = niceDomain(0, valueMax > 0 ? valueMax : 1, valueTickCount)[1]
  if (countAxis === true) {
    valueTop = Math.max(Math.ceil(valueTop), 1)
  }
  let valueTicks = niceTicks(0, valueTop, valueTickCount)
  if (valueTicks.length < 3) {
    valueTicks = niceTicks(0, valueTop, valueTickCount * 2)
  }
  if (countAxis === true) {
    valueTicks = valueTicks.filter((tick) => Number.isInteger(tick) === true)
  }

  const binScale = linearScale([binMin, binMax], [0, binLength])
  const valScale = horizontal === true
    ? linearScale([0, valueTop], [0, plotW])
    : linearScale([0, valueTop], [plotH, 0])

  const plot = svgEl("g", { transform: `translate(${margin.left},${margin.top})` }, [])
  root.appendChild(plot)
  const axes = axisLayer(plot)

  const valueFormat = (value) => formatNumber(value, { maximumSignificantDigits: 3 })
  const binTicks = { count: tickCount(binLength, horizontal === true ? 36 : 70), grid: false }
  const valueTitle = countAxis === true ? "Count" : "Density"
  if (horizontal === true) {
    drawTicks(axes, valScale, { side: "bottom", extent: plotH, ticks: valueTicks, format: valueFormat })
    drawTicks(axes, binScale, { side: "left", extent: plotW, count: binTicks.count, grid: false })
    drawAxisTitle(axes, valueTitle, "bottom", plotW, plotH, 36)
  } else {
    drawTicks(axes, valScale, { side: "left", extent: plotW, ticks: valueTicks, format: valueFormat })
    drawTicks(axes, binScale, { side: "bottom", extent: plotH, count: binTicks.count, grid: false })
    drawAxisTitle(axes, valueTitle, "left", plotW, plotH, 50)
  }

  const marks = svgEl("g", { part: "marks" }, [])
  plot.appendChild(marks)

  if (mode === "kde") {
    _drawCurves(marks, curves, binScale, valScale, ctx, horizontal, fillMode)
    ctx.setTable(_densityTable(resolved, curves))
  } else if (mode === "polygon") {
    _drawPolygons(marks, resolved, binScale, valScale, ctx, horizontal, fillMode, normalized)
    ctx.setTable(_binTable(resolved, normalized, "Frequency per bin"))
  } else {
    _drawBars(marks, resolved, binScale, valScale, ctx, horizontal, stacked, normalized)
    ctx.setTable(_binTable(resolved, normalized, "Observations per bin"))
  }

  /* Zero line of the value axis. */
  const zero = valScale(0)
  if (horizontal === true) {
    drawBaseline(axes, zero, 0, zero, plotH)
  } else {
    drawBaseline(axes, 0, zero, plotW, zero)
  }
  return root
}


const OPTIONS = { isEmpty: (model) => hasSeriesSamples(model) === false }

registerRenderer("histogram", render, OPTIONS)
registerRenderer("density", render, OPTIONS)
registerRenderer("frequency-polygon", render, OPTIONS)
