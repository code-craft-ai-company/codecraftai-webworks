/*
 * violin.js
 *
 * Violin plot renderer — mirrored KDE silhouette per group.
 *
 * Registers: "violin"
 *
 * ctx.model.series data shape:
 *   series[].groups[]: { category, samples: [n, …] }
 *
 * Relevant ctx.attrs:
 *   show-box     "true" — embed a miniature box plot inside each violin
 *   show-points  "true" — overlay raw sample points
 *   half         "true" — render right half only (half-violin)
 *   bandwidth    KDE bandwidth override
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber, smoothPath } from "../svgdraw.js";
import { linearScale, bandScale, niceTicks } from "../scales.js";


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
  /*
   * Evaluate KDE density at each eval point.
   * :returns: Array of density values parallel to evalPoints.
   */
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


function _quantile(sorted, p) {
  const n = sorted.length
  if (n === 0) { return 0 }
  if (n === 1) { return sorted[0] }
  const index = p * (n - 1)
  const lo = Math.floor(index)
  const hi = Math.ceil(index)
  const frac = index - lo
  return sorted[lo] * (1 - frac) + sorted[hi] * frac
}


/* ── violin drawing ──────────────────────────────────────────────────────── */

function _drawViolin(plot, samples, bandCenter, halfWidth, valScale, ctx, seriesIndex, horizontal, halfViolin, evalPoints, densities, maxDensity) {
  /*
   * Draw one violin shape (mirrored KDE path) centered on bandCenter.
   */
  const color = ctx.colorFor(seriesIndex)
  const densityScale = maxDensity > 0 ? halfWidth / maxDensity : 1

  /* Build left (negative offset) and right (positive offset) sides. */
  const rightPoints = []
  const leftPoints = []

  for (let i = 0; i < evalPoints.length; i = i + 1) {
    const v = evalPoints[i]
    const d = densities[i] * densityScale

    if (horizontal === true) {
      const y = valScale(v)
      rightPoints.push({ x: bandCenter + d, y: y })
      leftPoints.push({ x: bandCenter - d, y: y })
    } else {
      const y = valScale(v)
      rightPoints.push({ x: bandCenter + d, y: y })
      leftPoints.push({ x: bandCenter - d, y: y })
    }
  }

  /* Combine: right side top-to-bottom, left side reversed (bottom-to-top). */
  let allPoints = null
  if (halfViolin === true) {
    /* Right half only. */
    const topAnchor = rightPoints[0]
    const botAnchor = rightPoints[rightPoints.length - 1]
    allPoints = [
      { x: bandCenter, y: topAnchor.y },
      ...rightPoints,
      { x: bandCenter, y: botAnchor.y }
    ]
  } else {
    allPoints = [
      ...rightPoints,
      ...leftPoints.slice().reverse()
    ]
  }

  /* Close path. */
  const pathD = smoothPath(allPoints) + " Z"
  const violinPath = svgEl("path", {
    d: pathD, fill: color, opacity: 0.55,
    stroke: color, "stroke-width": 1.5
  }, [])
  violinPath.setAttribute("part", "violin")
  plot.appendChild(violinPath)
  return
}


function _drawMiniBox(plot, samples, bandCenter, halfWidth, valScale, horizontal) {
  /*
   * Draw a miniature box plot (IQR rect + median line + whiskers) inside violin.
   */
  const sorted = samples.slice().sort((a, b) => a - b)
  const q1 = _quantile(sorted, 0.25)
  const median = _quantile(sorted, 0.5)
  const q3 = _quantile(sorted, 0.75)
  const iqr = q3 - q1
  const wLo = q1 - 1.5 * iqr
  const wHi = q3 + 1.5 * iqr
  const inliers = sorted.filter((v) => v >= wLo && v <= wHi)
  const wMin = inliers.length > 0 ? inliers[0] : q1
  const wMax = inliers.length > 0 ? inliers[inliers.length - 1] : q3

  const boxHalf = halfWidth * 0.25
  const iqrColor = "var(--mj-text, #14181f)"

  if (horizontal === true) {
    plot.appendChild(svgEl("rect", {
      x: valScale(q1), y: bandCenter - boxHalf,
      width: Math.abs(valScale(q3) - valScale(q1)), height: boxHalf * 2,
      fill: "var(--mj-bg, #ffffff)", stroke: iqrColor, "stroke-width": 1.5, rx: 1
    }, []))
    plot.appendChild(svgEl("line", {
      x1: valScale(median), y1: bandCenter - boxHalf,
      x2: valScale(median), y2: bandCenter + boxHalf,
      stroke: iqrColor, "stroke-width": 2
    }, []))
    plot.appendChild(svgEl("line", {
      x1: valScale(wMin), y1: bandCenter,
      x2: valScale(q1), y2: bandCenter,
      stroke: iqrColor, "stroke-width": 1
    }, []))
    plot.appendChild(svgEl("line", {
      x1: valScale(q3), y1: bandCenter,
      x2: valScale(wMax), y2: bandCenter,
      stroke: iqrColor, "stroke-width": 1
    }, []))
  } else {
    plot.appendChild(svgEl("rect", {
      x: bandCenter - boxHalf, y: Math.min(valScale(q1), valScale(q3)),
      width: boxHalf * 2, height: Math.abs(valScale(q3) - valScale(q1)),
      fill: "var(--mj-bg, #ffffff)", stroke: iqrColor, "stroke-width": 1.5, rx: 1
    }, []))
    plot.appendChild(svgEl("line", {
      x1: bandCenter - boxHalf, y1: valScale(median),
      x2: bandCenter + boxHalf, y2: valScale(median),
      stroke: iqrColor, "stroke-width": 2
    }, []))
    plot.appendChild(svgEl("line", {
      x1: bandCenter, y1: valScale(wMin),
      x2: bandCenter, y2: valScale(q1),
      stroke: iqrColor, "stroke-width": 1
    }, []))
    plot.appendChild(svgEl("line", {
      x1: bandCenter, y1: valScale(q3),
      x2: bandCenter, y2: valScale(wMax),
      stroke: iqrColor, "stroke-width": 1
    }, []))
  }
  return
}


/* ── main render ─────────────────────────────────────────────────────────── */

export function render(ctx) {
  /*
   * Render a violin plot.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const model = ctx.model
  const horizontal = ctx.orientation === "horizontal"
  const showBox = ctx.attrs("show-box", "false") === "true"
  const showPoints = ctx.attrs("show-points", "false") === "true"
  const halfViolin = ctx.attrs("half", "false") === "true"
  const bwOverride = parseFloat(ctx.attrs("bandwidth", "0")) || 0

  const root = svgEl("g", { part: "plot" }, [])

  const series = model.series
  const categories = model.categories
  if (series === null || series === undefined || series.length === 0) {
    return root
  }
  if (categories === null || categories === undefined || categories.length === 0) {
    return root
  }

  /* Compute global value extent across all series+groups. */
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
  const pad = (valMax - valMin) * 0.1 || 1
  valMin = valMin - pad
  valMax = valMax + pad

  const evalCount = 60
  const evalPoints = []
  for (let i = 0; i <= evalCount; i = i + 1) {
    evalPoints.push(valMin + (valMax - valMin) * (i / evalCount))
  }

  /* Pre-compute per-group KDE and find global max density for scale. */
  let globalMaxDensity = 0
  const kdeCache = []
  for (let si = 0; si < series.length; si = si + 1) {
    const groups = series[si].groups || []
    const seriesKde = []
    for (let gi = 0; gi < groups.length; gi = gi + 1) {
      const samples = groups[gi].samples || []
      if (samples.length < 2) {
        seriesKde.push(null)
        continue
      }
      const bw = bwOverride > 0 ? bwOverride : _silvermanBw(samples)
      const densities = _kde(samples, bw, evalPoints)
      const localMax = Math.max(...densities)
      if (localMax > globalMaxDensity) { globalMaxDensity = localMax }
      seriesKde.push(densities)
    }
    kdeCache.push(seriesKde)
  }
  if (globalMaxDensity === 0) { globalMaxDensity = 1 }

  const margin = { top: 16, right: 16, bottom: 40, left: 52 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  const cat = bandScale(categories, [0, horizontal ? plotH : plotW], 0.15)
  const val = horizontal
    ? linearScale([valMin, valMax], [0, plotW])
    : linearScale([valMin, valMax], [plotH, 0])

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  /* Value axis gridlines. */
  const ticks = niceTicks(valMin, valMax, 5)
  for (let ti = 0; ti < ticks.length; ti = ti + 1) {
    const tick = ticks[ti]
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

  /* Category labels. */
  for (let ci = 0; ci < categories.length; ci = ci + 1) {
    const category = categories[ci]
    const bandCenter = cat(category) + cat.bandwidth() / 2
    if (horizontal === true) {
      plot.appendChild(svgEl("text", {
        x: -8, y: bandCenter + 4, "text-anchor": "end",
        "font-size": 11, fill: "var(--mj-text, #14181f)"
      }, String(category)))
    } else {
      plot.appendChild(svgEl("text", {
        x: bandCenter, y: plotH + 18, "text-anchor": "middle",
        "font-size": 11, fill: "var(--mj-text, #14181f)"
      }, String(category)))
    }
  }

  const bandwidth = cat.bandwidth()
  const clusterWidth = series.length > 1 ? bandwidth / series.length : bandwidth
  const halfWidthPx = clusterWidth * 0.45

  for (let si = 0; si < series.length; si = si + 1) {
    const s = series[si]
    const groups = s.groups || []
    const clusterOffset = series.length > 1 ? si * clusterWidth : 0

    for (let gi = 0; gi < groups.length; gi = gi + 1) {
      const group = groups[gi]
      const densities = kdeCache[si][gi]
      if (densities === null) { continue }

      const bandStart = cat(group.category)
      const bandCenter = bandStart + clusterOffset + clusterWidth / 2

      _drawViolin(plot, group.samples, bandCenter, halfWidthPx, val, ctx, si,
        horizontal, halfViolin, evalPoints, densities, globalMaxDensity)

      if (showBox === true) {
        _drawMiniBox(plot, group.samples, bandCenter, halfWidthPx, val, horizontal)
      }

      if (showPoints === true) {
        const samples = group.samples || []
        const color = ctx.colorFor(si)
        for (let pi = 0; pi < samples.length; pi = pi + 1) {
          const seed = Math.sin(pi * 9301 + 49297) * 0.5 + 0.5
          const jitter = (seed - 0.5) * halfWidthPx * 0.4
          const px = horizontal ? val(samples[pi]) : bandCenter + jitter
          const py = horizontal ? bandCenter + jitter : val(samples[pi])
          const dot = svgEl("circle", {
            cx: px, cy: py, r: 2.5,
            fill: color, opacity: 0.6
          }, [])
          plot.appendChild(dot)
        }
      }

      /* Interactive overlay. */
      const hitX = horizontal ? val(valMin) : bandStart + clusterOffset
      const hitY = horizontal ? bandStart + clusterOffset : val(valMax)
      const hitW = horizontal ? Math.abs(val(valMax) - val(valMin)) : clusterWidth
      const hitH = horizontal ? clusterWidth : Math.abs(val(valMax) - val(valMin))
      const hitRect = svgEl("rect", {
        x: hitX, y: hitY, width: hitW, height: hitH, fill: "transparent"
      }, [])
      hitRect.setAttribute("part", "violin-hit")
      hitRect.setAttribute("tabindex", "0")
      hitRect.setAttribute("role", "img")
      hitRect.setAttribute("aria-label", `${s.name}, ${group.category} violin`)
      hitRect.appendChild(svgEl("title", null, `${s.name} — ${group.category}`))
      const handlerGroup = group
      const handlerSeries = s
      const clickHandler = () => {
        ctx.emit("mj-chart-violin-click", {
          series: handlerSeries.name, category: handlerGroup.category
        })
      }
      hitRect.addEventListener("click", clickHandler)
      hitRect.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault()
          clickHandler()
        }
      })
      plot.appendChild(hitRect)
    }
  }

  return root
}


registerRenderer("violin", render)
