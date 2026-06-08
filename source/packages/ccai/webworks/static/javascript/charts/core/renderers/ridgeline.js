/*
 * ridgeline.js
 *
 * Ridgeline (joy) plot renderer — vertically offset density curves per group.
 *
 * Registers: "ridgeline"
 *
 * ctx.model.series data shape:
 *   series[].groups[]: { category, samples: [n, …] }
 *   categories: [string, …]  — display order (top-to-bottom)
 *
 * Relevant ctx.attrs:
 *   mode       "density" (default) | "histogram"
 *   overlap    fractional row-height overlap (default 0.5)
 *   bandwidth  KDE bandwidth override
 *   bin-count  bins for histogram mode
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber, smoothPath, linePath, areaPath } from "../svgdraw.js";
import { linearScale, niceTicks } from "../scales.js";


/* ── KDE helpers ─────────────────────────────────────────────────────────── */

function _silvermanBw(samples) {
  const n = samples.length
  if (n < 2) { return 1 }
  let mean = 0
  for (let i = 0; i < n; i = i + 1) { mean = mean + samples[i] }
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
  return Math.exp(-0.5 * u * u) / Math.sqrt(2 * Math.PI)
}


function _kde(samples, bw, evalPoints) {
  const n = samples.length
  const densities = []
  for (let ei = 0; ei < evalPoints.length; ei = ei + 1) {
    const x = evalPoints[ei]
    let sum = 0
    for (let si = 0; si < n; si = si + 1) {
      sum = sum + _gaussianKernel((x - samples[si]) / bw)
    }
    densities.push(sum / (n * bw))
  }
  return densities
}


/* ── histogram helpers ───────────────────────────────────────────────────── */

function _sturgesBinCount(n) {
  return Math.max(Math.ceil(Math.log2(Math.max(n, 1)) + 1), 2)
}


function _makeBins(samples, binCount, globalMin, globalMax) {
  const binW = globalMax === globalMin ? 1 : (globalMax - globalMin) / binCount
  const bins = []
  for (let i = 0; i < binCount; i = i + 1) {
    bins.push({ x0: globalMin + i * binW, x1: globalMin + (i + 1) * binW, count: 0 })
  }
  for (let si = 0; si < samples.length; si = si + 1) {
    const v = samples[si]
    let bi = Math.floor((v - globalMin) / binW)
    if (bi < 0) { bi = 0 }
    if (bi >= binCount) { bi = binCount - 1 }
    bins[bi].count = bins[bi].count + 1
  }
  return bins
}


/* ── main render ─────────────────────────────────────────────────────────── */

export function render(ctx) {
  /*
   * Render a ridgeline plot.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const model = ctx.model
  const mode = ctx.attrs("mode", "density")
  const overlap = parseFloat(ctx.attrs("overlap", "0.5")) || 0.5
  const bwOverride = parseFloat(ctx.attrs("bandwidth", "0")) || 0
  const binCountAttr = parseInt(ctx.attrs("bin-count", "0"), 10) || 0

  const root = svgEl("g", { part: "plot" }, [])

  const series = model.series
  const categories = model.categories
  if (series === null || series === undefined || series.length === 0) {
    return root
  }
  if (categories === null || categories === undefined || categories.length === 0) {
    return root
  }

  /* Collect all samples for global value extent. */
  let valMin = Infinity
  let valMax = -Infinity
  for (let si = 0; si < series.length; si = si + 1) {
    const groups = series[si].groups || []
    for (let gi = 0; gi < groups.length; gi = gi + 1) {
      const samples = groups[gi].samples || []
      for (let vi = 0; vi < samples.length; vi = vi + 1) {
        if (samples[vi] < valMin) { valMin = samples[vi] }
        if (samples[vi] > valMax) { valMax = samples[vi] }
      }
    }
  }
  if (valMin === Infinity) {
    return root
  }
  const valPad = (valMax - valMin) * 0.05 || 0.5
  valMin = valMin - valPad
  valMax = valMax + valPad

  /* Build shared eval points. */
  const evalCount = 60
  const evalPoints = []
  for (let i = 0; i <= evalCount; i = i + 1) {
    evalPoints.push(valMin + (valMax - valMin) * (i / evalCount))
  }

  const binCount = binCountAttr > 0 ? binCountAttr : _sturgesBinCount(30)

  /* Pre-compute per-group curves and find global max amplitude. */
  let globalMaxAmp = 0
  const groupCurves = []  /* parallel to categories */

  for (let ci = 0; ci < categories.length; ci = ci + 1) {
    const category = categories[ci]
    let samples = null

    /* Use first series that has this category. */
    outer: for (let si = 0; si < series.length; si = si + 1) {
      const groups = series[si].groups || []
      for (let gi = 0; gi < groups.length; gi = gi + 1) {
        if (groups[gi].category === category) {
          samples = groups[gi].samples || []
          break outer
        }
      }
    }

    if (samples === null || samples.length === 0) {
      groupCurves.push(null)
      continue
    }

    let amplitudes = null
    let curveEvalPoints = null

    if (mode === "histogram") {
      const bins = _makeBins(samples, binCount, valMin, valMax)
      const midPoints = bins.map((b) => (b.x0 + b.x1) / 2)
      amplitudes = bins.map((b) => b.count)
      curveEvalPoints = midPoints
    } else {
      const bw = bwOverride > 0 ? bwOverride : _silvermanBw(samples)
      amplitudes = _kde(samples, bw, evalPoints)
      curveEvalPoints = evalPoints
    }

    const localMax = Math.max(...amplitudes)
    if (localMax > globalMaxAmp) { globalMaxAmp = localMax }
    groupCurves.push({ points: curveEvalPoints, amplitudes: amplitudes, samples: samples })
  }

  if (globalMaxAmp === 0) { globalMaxAmp = 1 }

  const margin = { top: 16, right: 16, bottom: 40, left: 80 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  /* Row height: divide plotH by category count; overlap allows curves to spill into next row. */
  const rowH = plotH / Math.max(categories.length, 1)
  const amplitudeH = rowH * (1 + overlap)

  const valScale = linearScale([valMin, valMax], [0, plotW])

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  /* Value axis tick labels at the bottom. */
  const valTicks = niceTicks(valMin, valMax, 6)
  for (let ti = 0; ti < valTicks.length; ti = ti + 1) {
    const tick = valTicks[ti]
    const x = valScale(tick)
    plot.appendChild(svgEl("text", {
      x: x, y: plotH + 16, "text-anchor": "middle",
      "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
    }, formatNumber(tick)))
    plot.appendChild(svgEl("line", {
      x1: x, y1: 0, x2: x, y2: plotH,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1, opacity: 0.4
    }, []))
  }

  /* Draw each group row from bottom to top (last category = top of chart). */
  for (let ci = categories.length - 1; ci >= 0; ci = ci - 1) {
    const category = categories[ci]
    const curve = groupCurves[ci]

    /* Baseline pixel for this row — rows stack from top to bottom. */
    const rowBaseline = (ci + 1) * rowH
    const color = ctx.colorFor(ci)

    /* Row baseline line. */
    plot.appendChild(svgEl("line", {
      x1: 0, y1: rowBaseline, x2: plotW, y2: rowBaseline,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 0.5
    }, []))

    /* Group label. */
    plot.appendChild(svgEl("text", {
      x: -6, y: rowBaseline - 2, "text-anchor": "end",
      "font-size": 11, fill: "var(--mj-text, #14181f)"
    }, String(category)))

    if (curve === null) { continue }

    /* Amplitude scale: map 0..globalMaxAmp to rowBaseline..rowBaseline-amplitudeH. */
    const ampScale = (amp) => rowBaseline - (amp / globalMaxAmp) * amplitudeH

    const pathPoints = curve.points.map((x, i) => ({
      x: valScale(x),
      y: ampScale(curve.amplitudes[i])
    }))

    /* Fill area. */
    if (mode === "histogram") {
      /* Step polygon for histogram mode. */
      const stepPoints = []
      for (let i = 0; i < curve.points.length; i = i + 1) {
        const binHalf = i > 0
          ? (curve.points[i] - curve.points[i - 1]) / 2
          : (curve.points[1] - curve.points[0]) / 2
        stepPoints.push({ x: valScale(curve.points[i] - binHalf), y: ampScale(curve.amplitudes[i]) })
        stepPoints.push({ x: valScale(curve.points[i] + binHalf), y: ampScale(curve.amplitudes[i]) })
      }
      const fillD = areaPath(stepPoints, rowBaseline)
      if (fillD !== "") {
        plot.appendChild(svgEl("path", {
          d: fillD, fill: color, opacity: 0.5, stroke: "none"
        }, []))
      }
      const lineD = linePath(stepPoints)
      if (lineD !== "") {
        plot.appendChild(svgEl("path", {
          d: lineD, fill: "none", stroke: color, "stroke-width": 1.5
        }, []))
      }
    } else {
      const fillD = areaPath(pathPoints, rowBaseline)
      if (fillD !== "") {
        plot.appendChild(svgEl("path", {
          d: fillD, fill: color, opacity: 0.5, stroke: "none"
        }, []))
      }
      const lineD = smoothPath(pathPoints)
      if (lineD !== "") {
        const linePath = svgEl("path", {
          d: lineD, fill: "none", stroke: color, "stroke-width": 1.5
        }, [])
        linePath.setAttribute("part", "ridge")
        linePath.setAttribute("tabindex", "0")
        linePath.setAttribute("role", "img")
        linePath.setAttribute("aria-label", `${category} density ridge`)
        linePath.appendChild(svgEl("title", null, `${category}`))
        const handlerCategory = category
        const clickHandler = () => {
          ctx.emit("mj-chart-ridge-click", { category: handlerCategory })
        }
        linePath.addEventListener("click", clickHandler)
        linePath.addEventListener("keydown", (event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault()
            clickHandler()
          }
        })
        plot.appendChild(linePath)
      }
    }
  }

  return root
}


registerRenderer("ridgeline", render)
