/*
 * histogram.js
 *
 * Histogram / Density / Frequency-Polygon renderer.
 *
 * Registers: "histogram", "density", "frequency-polygon"
 *
 * ctx.raw / ctx.model.series data shapes:
 *   - samples: [n, …]            renderer bins/KDE-smooths internally
 *   - bins: [{x0, x1, count}]   pre-binned; renderer uses as-is
 *
 * Relevant ctx.attrs:
 *   bin-count   number of bins for Sturges auto-computation (fallback: auto)
 *   group       "overlay" | "stack" (default "overlay")
 *   normalize   "density" — y-axis is probability density
 *   smooth      "kde" — render as KDE curve (density type forces this)
 *   display     "polygon" — frequency-polygon line through midpoints
 *   bandwidth   KDE bandwidth override (Silverman rule used otherwise)
 *   fill        "area" | "none" for density/polygon modes
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber, smoothPath, areaPath, linePath, extent } from "../svgdraw.js";
import { linearScale, niceTicks } from "../scales.js";


/* ── helpers ──────────────────────────────────────────────────────────────── */

function _sturgesBinCount(n) {
  /*
   * Sturges' rule: k = ceil(log2(n) + 1).
   */
  const k = Math.ceil(Math.log2(Math.max(n, 1)) + 1)
  return Math.max(k, 2)
}


function _makeBins(samples, binCount) {
  /*
   * Partition sorted samples into equal-width bins.
   *
   * :returns: Array of {x0, x1, count}.
   */
  const sorted = samples.slice().sort((a, b) => a - b)
  const dataMin = sorted[0]
  const dataMax = sorted[sorted.length - 1]
  const binW = dataMax === dataMin ? 1 : (dataMax - dataMin) / binCount
  const bins = []
  for (let index = 0; index < binCount; index = index + 1) {
    const x0 = dataMin + index * binW
    const x1 = index === binCount - 1 ? dataMax + 1e-9 : dataMin + (index + 1) * binW
    bins.push({ x0: x0, x1: x1, count: 0 })
  }
  for (let si = 0; si < sorted.length; si = si + 1) {
    const value = sorted[si]
    let bi = Math.floor((value - dataMin) / binW)
    if (bi >= binCount) {
      bi = binCount - 1
    }
    bins[bi].count = bins[bi].count + 1
  }
  return bins
}


function _silvermanBandwidth(samples) {
  /*
   * Silverman's rule-of-thumb KDE bandwidth.
   */
  const n = samples.length
  if (n < 2) {
    return 1
  }
  let mean = 0
  for (let i = 0; i < n; i = i + 1) {
    mean = mean + samples[i]
  }
  mean = mean / n
  let variance = 0
  for (let i = 0; i < n; i = i + 1) {
    const diff = samples[i] - mean
    variance = variance + diff * diff
  }
  const std = Math.sqrt(variance / (n - 1))
  const sorted = samples.slice().sort((a, b) => a - b)
  const q1 = sorted[Math.floor(n * 0.25)]
  const q3 = sorted[Math.floor(n * 0.75)]
  const iqr = q3 - q1
  const spread = Math.min(std, iqr / 1.34)
  const bw = 0.9 * spread * Math.pow(n, -0.2)
  return bw > 0 ? bw : 1
}


function _gaussianKernel(u) {
  /*
   * Standard Gaussian kernel: k(u) = exp(-0.5 * u^2) / sqrt(2π).
   */
  const value = Math.exp(-0.5 * u * u) / Math.sqrt(2 * Math.PI)
  return value
}


function _kdePoints(samples, bandwidth, evalPoints) {
  /*
   * Evaluate KDE at each point in evalPoints.
   *
   * :returns: Array of {x, density}.
   */
  const n = samples.length
  const points = []
  for (let ei = 0; ei < evalPoints.length; ei = ei + 1) {
    const x = evalPoints[ei]
    let sum = 0
    for (let si = 0; si < n; si = si + 1) {
      sum = sum + _gaussianKernel((x - samples[si]) / bandwidth)
    }
    const density = sum / (n * bandwidth)
    points.push({ x: x, density: density })
  }
  return points
}


function _resolveSeries(series, binCountAttr) {
  /*
   * For each series item, produce a resolved bins array.
   * Handles both samples-based and pre-binned inputs.
   *
   * :returns: Array of { name, bins, color }.
   */
  const resolved = []
  for (let si = 0; si < series.length; si = si + 1) {
    const s = series[si]
    let bins = null
    if (Array.isArray(s.bins) === true && s.bins.length > 0) {
      bins = s.bins
    } else if (Array.isArray(s.samples) === true && s.samples.length > 0) {
      const k = binCountAttr > 0 ? binCountAttr : _sturgesBinCount(s.samples.length)
      bins = _makeBins(s.samples, k)
    } else {
      bins = []
    }
    resolved.push({ name: s.name, bins: bins, samples: s.samples || null, color: s.color || null })
  }
  return resolved
}


/* ── axis / grid helpers ─────────────────────────────────────────────────── */

function _drawValueAxis(plot, valScale, plotW, plotH, horizontal) {
  /*
   * Draw gridlines and tick labels for the value (count/density) axis.
   */
  const ticks = niceTicks(valScale.domain()[0], valScale.domain()[1], 5)
  for (let ti = 0; ti < ticks.length; ti = ti + 1) {
    const tick = ticks[ti]
    if (horizontal === true) {
      const x = valScale(tick)
      plot.appendChild(svgEl("line", {
        x1: x, y1: 0, x2: x, y2: plotH,
        stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
      }, []))
      plot.appendChild(svgEl("text", {
        x: x, y: plotH + 16, "text-anchor": "middle",
        "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
      }, formatNumber(tick)))
    } else {
      const y = valScale(tick)
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
  return
}


function _drawBinAxis(plot, binMin, binMax, plotW, plotH, horizontal, binScale) {
  /*
   * Draw a few representative tick labels along the bin (range) axis.
   */
  const ticks = niceTicks(binMin, binMax, 6)
  for (let ti = 0; ti < ticks.length; ti = ti + 1) {
    const tick = ticks[ti]
    const px = binScale(tick)
    if (horizontal === true) {
      plot.appendChild(svgEl("text", {
        x: -8, y: px + 4, "text-anchor": "end",
        "font-size": 11, fill: "var(--mj-text, #14181f)"
      }, formatNumber(tick)))
    } else {
      plot.appendChild(svgEl("text", {
        x: px, y: plotH + 18, "text-anchor": "middle",
        "font-size": 11, fill: "var(--mj-text, #14181f)"
      }, formatNumber(tick)))
    }
  }
  return
}


/* ── bar-mode render ─────────────────────────────────────────────────────── */

function _renderBars(plot, resolvedSeries, binScale, valScale, zero, ctx, horizontal, stackMode) {
  /*
   * Draw histogram bars (rect per bin, per series).
   */
  const allBinKeys = new Set()
  for (let si = 0; si < resolvedSeries.length; si = si + 1) {
    const series = resolvedSeries[si]
    for (let bi = 0; bi < series.bins.length; bi = bi + 1) {
      allBinKeys.add(series.bins[bi].x0)
    }
  }

  /* For stack mode, accumulate previous series heights per bin. */
  const stackBase = {}
  allBinKeys.forEach((key) => { stackBase[key] = 0 })

  for (let si = 0; si < resolvedSeries.length; si = si + 1) {
    const series = resolvedSeries[si]
    const color = ctx.colorFor(si)
    const isOverlay = !stackMode
    const opacity = isOverlay && resolvedSeries.length > 1 ? 0.65 : 1

    for (let bi = 0; bi < series.bins.length; bi = bi + 1) {
      const bin = series.bins[bi]
      const baseCount = stackMode ? stackBase[bin.x0] || 0 : 0
      const topCount = baseCount + bin.count

      const pxStart = binScale(bin.x0)
      const pxEnd = binScale(bin.x1)
      const barW = Math.max(Math.abs(pxEnd - pxStart) - 1, 1)

      let rect = null
      if (horizontal === true) {
        const x1 = valScale(baseCount)
        const x2 = valScale(topCount)
        const w = Math.abs(x2 - x1)
        const y = Math.min(pxStart, pxEnd)
        rect = svgEl("rect", {
          x: Math.min(x1, x2), y: y,
          width: w, height: barW,
          fill: color, opacity: opacity
        }, [])
      } else {
        const y1 = valScale(topCount)
        const y2 = valScale(baseCount)
        const h = Math.abs(y2 - y1)
        const x = Math.min(pxStart, pxEnd)
        rect = svgEl("rect", {
          x: x, y: Math.min(y1, y2),
          width: barW, height: h,
          fill: color, opacity: opacity
        }, [])
      }

      rect.setAttribute("part", "bar")
      rect.setAttribute("tabindex", "0")
      rect.setAttribute("role", "img")
      rect.setAttribute("aria-label",
        `${series.name} [${formatNumber(bin.x0)}–${formatNumber(bin.x1)}]: ${bin.count}`)
      rect.appendChild(svgEl("title", null,
        `${series.name} [${formatNumber(bin.x0)}–${formatNumber(bin.x1)}]: ${bin.count}`))
      const handlerBin = bin
      const handlerSeries = series
      const handler = () => {
        ctx.emit("mj-chart-bar-click", {
          series: handlerSeries.name,
          x0: handlerBin.x0, x1: handlerBin.x1,
          count: handlerBin.count
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

      if (stackMode === true) {
        stackBase[bin.x0] = topCount
      }
    }
  }
  return
}


/* ── KDE / density render ────────────────────────────────────────────────── */

function _renderKDE(plot, resolvedSeries, binMin, binMax, valMax, binScale, valScale, ctx, horizontal, fillMode, bwOverride) {
  /*
   * Draw smoothed KDE curves (filled area or line only).
   */
  const evalCount = 80
  const evalPoints = []
  for (let i = 0; i <= evalCount; i = i + 1) {
    evalPoints.push(binMin + (binMax - binMin) * (i / evalCount))
  }

  const baseline = valScale(0)

  for (let si = 0; si < resolvedSeries.length; si = si + 1) {
    const series = resolvedSeries[si]
    const samples = series.samples
    if (samples === null || samples.length === 0) {
      continue
    }
    const color = ctx.colorFor(si)
    const bw = bwOverride > 0 ? bwOverride : _silvermanBandwidth(samples)
    const kdeData = _kdePoints(samples, bw, evalPoints)

    const points = kdeData.map((d) => {
      if (horizontal === true) {
        return { x: valScale(d.density), y: binScale(d.x) }
      }
      return { x: binScale(d.x), y: valScale(d.density) }
    })

    if (fillMode !== "none") {
      const pathD = areaPath(points, baseline)
      if (pathD !== "") {
        const area = svgEl("path", {
          d: pathD, fill: color, opacity: 0.3,
          stroke: "none"
        }, [])
        plot.appendChild(area)
      }
    }

    const pathD = smoothPath(points)
    if (pathD !== "") {
      const line = svgEl("path", {
        d: pathD, fill: "none",
        stroke: color, "stroke-width": 2
      }, [])
      line.setAttribute("part", "density-line")
      line.setAttribute("tabindex", "0")
      line.setAttribute("role", "img")
      line.setAttribute("aria-label", `${series.name} density curve`)
      line.appendChild(svgEl("title", null, `${series.name} density`))
      const handlerSeries = series
      const clickHandler = () => {
        ctx.emit("mj-chart-density-click", { series: handlerSeries.name })
      }
      line.addEventListener("click", clickHandler)
      line.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault()
          clickHandler()
        }
      })
      plot.appendChild(line)
    }
  }
  return
}


/* ── frequency-polygon render ────────────────────────────────────────────── */

function _renderPolygon(plot, resolvedSeries, binMin, binMax, binScale, valScale, ctx, horizontal, fillMode) {
  /*
   * Draw frequency-polygon lines through bin midpoints.
   */
  const baseline = valScale(0)

  for (let si = 0; si < resolvedSeries.length; si = si + 1) {
    const series = resolvedSeries[si]
    if (series.bins.length === 0) {
      continue
    }
    const color = ctx.colorFor(si)

    /* Anchor points at (x0 of first bin, 0) and (x1 of last bin, 0). */
    const firstBin = series.bins[0]
    const lastBin = series.bins[series.bins.length - 1]

    const midPoints = []
    if (horizontal === true) {
      midPoints.push({ x: valScale(0), y: binScale(firstBin.x0) })
      for (let bi = 0; bi < series.bins.length; bi = bi + 1) {
        const bin = series.bins[bi]
        const midY = binScale((bin.x0 + bin.x1) / 2)
        midPoints.push({ x: valScale(bin.count), y: midY })
      }
      midPoints.push({ x: valScale(0), y: binScale(lastBin.x1) })
    } else {
      midPoints.push({ x: binScale(firstBin.x0), y: baseline })
      for (let bi = 0; bi < series.bins.length; bi = bi + 1) {
        const bin = series.bins[bi]
        const midX = binScale((bin.x0 + bin.x1) / 2)
        midPoints.push({ x: midX, y: valScale(bin.count) })
      }
      midPoints.push({ x: binScale(lastBin.x1), y: baseline })
    }

    if (fillMode !== "none") {
      const pathD = areaPath(midPoints.slice(1, -1), baseline)
      if (pathD !== "") {
        plot.appendChild(svgEl("path", {
          d: pathD, fill: color, opacity: 0.3, stroke: "none"
        }, []))
      }
    }

    const pathD = linePath(midPoints)
    if (pathD !== "") {
      const line = svgEl("path", {
        d: pathD, fill: "none",
        stroke: color, "stroke-width": 2
      }, [])
      line.setAttribute("part", "polygon-line")
      line.setAttribute("tabindex", "0")
      line.setAttribute("role", "img")
      line.setAttribute("aria-label", `${series.name} frequency polygon`)
      line.appendChild(svgEl("title", null, `${series.name} frequency polygon`))
      const handlerSeries = series
      const clickHandler = () => {
        ctx.emit("mj-chart-polygon-click", { series: handlerSeries.name })
      }
      line.addEventListener("click", clickHandler)
      line.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault()
          clickHandler()
        }
      })
      plot.appendChild(line)
    }

    /* Midpoint circles. */
    for (let bi = 0; bi < series.bins.length; bi = bi + 1) {
      const bin = series.bins[bi]
      const midRaw = (bin.x0 + bin.x1) / 2
      const cx = horizontal ? valScale(bin.count) : binScale(midRaw)
      const cy = horizontal ? binScale(midRaw) : valScale(bin.count)
      const dot = svgEl("circle", {
        cx: cx, cy: cy, r: 3, fill: color
      }, [])
      plot.appendChild(dot)
    }
  }
  return
}


/* ── main render ─────────────────────────────────────────────────────────── */

export function render(ctx) {
  /*
   * Render a histogram, density plot, or frequency polygon.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const model = ctx.model
  const horizontal = ctx.orientation === "horizontal"
  const group = ctx.attrs("group", "overlay")
  const normalize = ctx.attrs("normalize", "")
  const smooth = ctx.attrs("smooth", "")
  const display = ctx.attrs("display", "bar")
  const fillAttr = ctx.attrs("fill", "area")
  const bwOverride = parseFloat(ctx.attrs("bandwidth", "0")) || 0
  const binCountRaw = parseInt(ctx.attrs("bin-count", "0"), 10) || 0

  /* Type key "density" implies KDE, "frequency-polygon" implies polygon. */
  const isDensity = normalize === "density" || smooth === "kde"
  const isPolygon = display === "polygon"

  const root = svgEl("g", { part: "plot" }, [])

  const series = model.series
  if (series === null || series === undefined || series.length === 0) {
    return root
  }

  const resolvedSeries = _resolveSeries(series, binCountRaw)
  const hasData = resolvedSeries.some((s) => s.bins.length > 0)
  if (hasData === false) {
    return root
  }

  /* Global bin extent across all series. */
  let globalMin = Infinity
  let globalMax = -Infinity
  let globalMaxCount = 0
  for (let si = 0; si < resolvedSeries.length; si = si + 1) {
    const rs = resolvedSeries[si]
    for (let bi = 0; bi < rs.bins.length; bi = bi + 1) {
      const bin = rs.bins[bi]
      if (bin.x0 < globalMin) { globalMin = bin.x0 }
      if (bin.x1 > globalMax) { globalMax = bin.x1 }
      if (bin.count > globalMaxCount) { globalMaxCount = bin.count }
    }
  }

  /* For stacked histogram compute total height per bin position. */
  let stackedMax = 0
  if (group === "stack") {
    const totals = {}
    for (let si = 0; si < resolvedSeries.length; si = si + 1) {
      for (let bi = 0; bi < resolvedSeries[si].bins.length; bi = bi + 1) {
        const bin = resolvedSeries[si].bins[bi]
        totals[bin.x0] = (totals[bin.x0] || 0) + bin.count
      }
    }
    const vals = Object.values(totals)
    stackedMax = vals.length > 0 ? Math.max(...vals) : globalMaxCount
  }

  const effectiveMaxCount = group === "stack" ? stackedMax : globalMaxCount
  const valDomainMax = effectiveMaxCount === 0 ? 1 : effectiveMaxCount

  /* For KDE, compute a density-domain max. */
  let kdeMax = 0
  if (isDensity === true) {
    for (let si = 0; si < resolvedSeries.length; si = si + 1) {
      const rs = resolvedSeries[si]
      if (rs.samples !== null && rs.samples.length > 0) {
        const bw = bwOverride > 0 ? bwOverride : _silvermanBandwidth(rs.samples)
        const evalPoints = []
        const steps = 40
        for (let i = 0; i <= steps; i = i + 1) {
          evalPoints.push(globalMin + (globalMax - globalMin) * (i / steps))
        }
        const pts = _kdePoints(rs.samples, bw, evalPoints)
        for (let pi = 0; pi < pts.length; pi = pi + 1) {
          if (pts[pi].density > kdeMax) { kdeMax = pts[pi].density }
        }
      }
    }
    if (kdeMax === 0) { kdeMax = 1 }
  }

  const margin = { top: 16, right: 16, bottom: 40, left: 52 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  const binScale = linearScale([globalMin, globalMax], horizontal ? [0, plotH] : [0, plotW])
  const valDomainTop = isDensity ? kdeMax * 1.1 : valDomainMax * 1.1
  const valScale = horizontal
    ? linearScale([0, valDomainTop], [0, plotW])
    : linearScale([0, valDomainTop], [plotH, 0])

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  _drawValueAxis(plot, valScale, plotW, plotH, horizontal)
  _drawBinAxis(plot, globalMin, globalMax, plotW, plotH, horizontal, binScale)

  const zero = valScale(0)

  if (isDensity === true) {
    _renderKDE(plot, resolvedSeries, globalMin, globalMax, kdeMax,
      binScale, valScale, ctx, horizontal, fillAttr, bwOverride)
  } else if (isPolygon === true) {
    _renderPolygon(plot, resolvedSeries, globalMin, globalMax,
      binScale, valScale, ctx, horizontal, fillAttr)
  } else {
    _renderBars(plot, resolvedSeries, binScale, valScale, zero, ctx, horizontal, group === "stack")
  }

  /* Baseline. */
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


registerRenderer("histogram", render)
registerRenderer("density", render)
registerRenderer("frequency-polygon", render)
