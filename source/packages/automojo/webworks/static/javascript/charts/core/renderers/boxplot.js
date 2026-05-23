/*
 * boxplot.js
 *
 * Box-and-whisker plot renderer.
 *
 * Registers: "boxplot"
 *
 * ctx.model.series data shape:
 *   series[].groups[]:
 *     - { category, samples: [n, …] }           renderer computes five-number summary
 *     - { category, min, q1, median, q3, max, outliers?: [n, …] }  pre-computed
 *
 * Relevant ctx.attrs:
 *   notched       "true" — draw notched box
 *   iqr-mult      IQR multiplier for whisker extent (default 1.5)
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber, extent } from "../svgdraw.js";
import { linearScale, bandScale, niceTicks } from "../scales.js";


/* ── statistics helpers ───────────────────────────────────────────────────── */

function _quantile(sorted, p) {
  /*
   * Linear interpolation quantile from a sorted array.
   */
  const n = sorted.length
  if (n === 0) { return 0 }
  if (n === 1) { return sorted[0] }
  const index = p * (n - 1)
  const lo = Math.floor(index)
  const hi = Math.ceil(index)
  const frac = index - lo
  const value = sorted[lo] * (1 - frac) + sorted[hi] * frac
  return value
}


function _fiveNumber(samples, iqrMult) {
  /*
   * Compute five-number summary + outliers from raw samples.
   *
   * :returns: { min, q1, median, q3, max, outliers }
   */
  const sorted = samples.slice().sort((a, b) => a - b)
  const q1 = _quantile(sorted, 0.25)
  const median = _quantile(sorted, 0.5)
  const q3 = _quantile(sorted, 0.75)
  const iqr = q3 - q1
  const fence = iqrMult * iqr
  const whiskerLo = q1 - fence
  const whiskerHi = q3 + fence

  const inliers = sorted.filter((v) => v >= whiskerLo && v <= whiskerHi)
  const outliers = sorted.filter((v) => v < whiskerLo || v > whiskerHi)
  const wMin = inliers.length > 0 ? inliers[0] : q1
  const wMax = inliers.length > 0 ? inliers[inliers.length - 1] : q3

  return { min: wMin, q1: q1, median: median, q3: q3, max: wMax, outliers: outliers }
}


function _resolveGroup(group, iqrMult) {
  /*
   * Return a five-number summary object regardless of whether the group
   * has raw samples or pre-computed stats.
   */
  if (typeof group.median === "number") {
    return {
      min: group.min,
      q1: group.q1,
      median: group.median,
      q3: group.q3,
      max: group.max,
      outliers: group.outliers || []
    }
  }
  if (Array.isArray(group.samples) && group.samples.length > 0) {
    return _fiveNumber(group.samples, iqrMult)
  }
  return null
}


/* ── drawing helpers ─────────────────────────────────────────────────────── */

function _drawBox(plot, stats, bandCenter, boxHalf, valScale, ctx, horizontal, notched, seriesName, category) {
  /*
   * Draw a single box-and-whisker glyph.
   */
  const q1px = valScale(stats.q1)
  const q3px = valScale(stats.q3)
  const medpx = valScale(stats.median)
  const minpx = valScale(stats.min)
  const maxpx = valScale(stats.max)

  const color = ctx.colorFor(seriesName)
  const bandL = bandCenter - boxHalf
  const bandR = bandCenter + boxHalf
  const whiskerHalf = boxHalf * 0.4

  if (horizontal === true) {
    /* IQR box */
    const boxX = Math.min(q1px, q3px)
    const boxW = Math.abs(q3px - q1px)
    const boxY = bandL
    const boxH = boxHalf * 2

    if (notched === true) {
      const notchSize = Math.min(boxHalf * 0.4, 8)
      const notchX = medpx
      const d = `M${boxX},${boxY} L${notchX - notchSize},${boxY} ` +
        `L${notchX},${boxY + notchSize} L${notchX + notchSize},${boxY} ` +
        `L${boxX + boxW},${boxY} L${boxX + boxW},${boxY + boxH} ` +
        `L${notchX + notchSize},${boxY + boxH} L${notchX},${boxY + boxH - notchSize} ` +
        `L${notchX - notchSize},${boxY + boxH} L${boxX},${boxY + boxH} Z`
      const boxPath = svgEl("path", {
        d: d, fill: color, opacity: 0.6,
        stroke: color, "stroke-width": 1.5
      }, [])
      plot.appendChild(boxPath)
    } else {
      const box = svgEl("rect", {
        x: boxX, y: boxY, width: boxW, height: boxH,
        fill: color, opacity: 0.6,
        stroke: color, "stroke-width": 1.5, rx: 2
      }, [])
      plot.appendChild(box)
    }

    /* Median line */
    plot.appendChild(svgEl("line", {
      x1: medpx, y1: bandL, x2: medpx, y2: bandR,
      stroke: "var(--mj-text, #14181f)", "stroke-width": 2.5
    }, []))

    /* Whiskers */
    plot.appendChild(svgEl("line", {
      x1: minpx, y1: bandCenter, x2: q1px, y2: bandCenter,
      stroke: color, "stroke-width": 1.5
    }, []))
    plot.appendChild(svgEl("line", {
      x1: q3px, y1: bandCenter, x2: maxpx, y2: bandCenter,
      stroke: color, "stroke-width": 1.5
    }, []))
    plot.appendChild(svgEl("line", {
      x1: minpx, y1: bandCenter - whiskerHalf,
      x2: minpx, y2: bandCenter + whiskerHalf,
      stroke: color, "stroke-width": 1.5
    }, []))
    plot.appendChild(svgEl("line", {
      x1: maxpx, y1: bandCenter - whiskerHalf,
      x2: maxpx, y2: bandCenter + whiskerHalf,
      stroke: color, "stroke-width": 1.5
    }, []))

    /* Outliers */
    for (let oi = 0; oi < stats.outliers.length; oi = oi + 1) {
      const ox = valScale(stats.outliers[oi])
      const dot = svgEl("circle", {
        cx: ox, cy: bandCenter, r: 3,
        fill: "none", stroke: color, "stroke-width": 1.5, opacity: 0.8
      }, [])
      plot.appendChild(dot)
    }

  } else {
    /* IQR box */
    const boxY = Math.min(q1px, q3px)
    const boxH = Math.abs(q3px - q1px)
    const boxX = bandL
    const boxW = boxHalf * 2

    if (notched === true) {
      const notchSize = Math.min(boxHalf * 0.4, 8)
      const notchY = medpx
      const d = `M${boxX},${boxY} L${boxX + boxW},${boxY} ` +
        `L${boxX + boxW},${notchY - notchSize} ` +
        `L${boxX + boxW + notchSize},${notchY} ` +
        `L${boxX + boxW},${notchY + notchSize} ` +
        `L${boxX + boxW},${boxY + boxH} ` +
        `L${boxX},${boxY + boxH} ` +
        `L${boxX},${notchY + notchSize} ` +
        `L${boxX - notchSize},${notchY} ` +
        `L${boxX},${notchY - notchSize} Z`
      const boxPath = svgEl("path", {
        d: d, fill: color, opacity: 0.6,
        stroke: color, "stroke-width": 1.5
      }, [])
      plot.appendChild(boxPath)
    } else {
      const box = svgEl("rect", {
        x: boxX, y: boxY, width: boxW, height: boxH,
        fill: color, opacity: 0.6,
        stroke: color, "stroke-width": 1.5, rx: 2
      }, [])
      plot.appendChild(box)
    }

    /* Median line */
    plot.appendChild(svgEl("line", {
      x1: bandL, y1: medpx, x2: bandR, y2: medpx,
      stroke: "var(--mj-text, #14181f)", "stroke-width": 2.5
    }, []))

    /* Whiskers */
    plot.appendChild(svgEl("line", {
      x1: bandCenter, y1: maxpx, x2: bandCenter, y2: q3px,
      stroke: color, "stroke-width": 1.5
    }, []))
    plot.appendChild(svgEl("line", {
      x1: bandCenter, y1: q1px, x2: bandCenter, y2: minpx,
      stroke: color, "stroke-width": 1.5
    }, []))
    plot.appendChild(svgEl("line", {
      x1: bandCenter - whiskerHalf, y1: minpx,
      x2: bandCenter + whiskerHalf, y2: minpx,
      stroke: color, "stroke-width": 1.5
    }, []))
    plot.appendChild(svgEl("line", {
      x1: bandCenter - whiskerHalf, y1: maxpx,
      x2: bandCenter + whiskerHalf, y2: maxpx,
      stroke: color, "stroke-width": 1.5
    }, []))

    /* Outliers */
    for (let oi = 0; oi < stats.outliers.length; oi = oi + 1) {
      const oy = valScale(stats.outliers[oi])
      const dot = svgEl("circle", {
        cx: bandCenter, cy: oy, r: 3,
        fill: "none", stroke: color, "stroke-width": 1.5, opacity: 0.8
      }, [])
      plot.appendChild(dot)
    }
  }

  /* Interactive overlay rect for accessibility. */
  let hitX = 0, hitY = 0, hitW = 0, hitH = 0
  if (horizontal === true) {
    hitX = Math.min(minpx, maxpx)
    hitY = bandL
    hitW = Math.abs(maxpx - minpx)
    hitH = boxHalf * 2
  } else {
    hitX = bandL
    hitY = Math.min(minpx, maxpx)
    hitW = boxHalf * 2
    hitH = Math.abs(maxpx - minpx)
  }
  const hitRect = svgEl("rect", {
    x: hitX, y: hitY, width: hitW, height: hitH,
    fill: "transparent"
  }, [])
  hitRect.setAttribute("part", "boxplot-hit")
  hitRect.setAttribute("tabindex", "0")
  hitRect.setAttribute("role", "img")
  hitRect.setAttribute("aria-label",
    `${seriesName}, ${category}: median=${formatNumber(stats.median)} ` +
    `IQR=[${formatNumber(stats.q1)}–${formatNumber(stats.q3)}]`)
  hitRect.appendChild(svgEl("title", null,
    `${seriesName} — ${category}\nMin: ${formatNumber(stats.min)}\n` +
    `Q1: ${formatNumber(stats.q1)}\nMedian: ${formatNumber(stats.median)}\n` +
    `Q3: ${formatNumber(stats.q3)}\nMax: ${formatNumber(stats.max)}`))
  const handlerStats = stats
  const clickHandler = () => {
    ctx.emit("mj-chart-boxplot-click", {
      series: seriesName, category: category, stats: handlerStats
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
  return
}


/* ── main render ──────────────────────────────────────────────────────────── */

export function render(ctx) {
  /*
   * Render a box plot.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const model = ctx.model
  const horizontal = ctx.orientation === "horizontal"
  const notched = ctx.attrs("notched", "false") === "true"
  const iqrMult = parseFloat(ctx.attrs("iqr-mult", "1.5")) || 1.5

  const root = svgEl("g", { part: "plot" }, [])

  const series = model.series
  const categories = model.categories
  if (series === null || series === undefined || series.length === 0) {
    return root
  }
  if (categories === null || categories === undefined || categories.length === 0) {
    return root
  }

  /* Collect all resolved stats to compute value domain. */
  const allStats = []
  for (let si = 0; si < series.length; si = si + 1) {
    const groups = series[si].groups || []
    for (let gi = 0; gi < groups.length; gi = gi + 1) {
      const stats = _resolveGroup(groups[gi], iqrMult)
      if (stats !== null) {
        allStats.push(stats)
      }
    }
  }
  if (allStats.length === 0) {
    return root
  }

  let valMin = Infinity
  let valMax = -Infinity
  for (let i = 0; i < allStats.length; i = i + 1) {
    const s = allStats[i]
    if (s.min < valMin) { valMin = s.min }
    if (s.max > valMax) { valMax = s.max }
    for (let oi = 0; oi < s.outliers.length; oi = oi + 1) {
      if (s.outliers[oi] < valMin) { valMin = s.outliers[oi] }
      if (s.outliers[oi] > valMax) { valMax = s.outliers[oi] }
    }
  }
  const padding = (valMax - valMin) * 0.1 || 1
  valMin = valMin - padding
  valMax = valMax + padding

  const margin = { top: 16, right: 16, bottom: 40, left: 52 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  const cat = bandScale(categories, [0, horizontal ? plotH : plotW], 0.2)
  const val = horizontal
    ? linearScale([valMin, valMax], [0, plotW])
    : linearScale([valMin, valMax], [plotH, 0])

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  /* Value gridlines + tick labels. */
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

  const bandwidth = cat.bandwidth()
  const clusterWidth = series.length > 1 ? bandwidth / series.length : bandwidth
  const boxHalf = clusterWidth * 0.35

  for (let si = 0; si < series.length; si = si + 1) {
    const s = series[si]
    const groups = s.groups || []
    const clusterOffset = series.length > 1 ? si * clusterWidth : 0

    for (let gi = 0; gi < groups.length; gi = gi + 1) {
      const group = groups[gi]
      const stats = _resolveGroup(group, iqrMult)
      if (stats === null) {
        continue
      }
      const bandStart = cat(group.category)
      const bandMid = bandStart + clusterOffset + clusterWidth / 2

      _drawBox(plot, stats, bandMid, boxHalf, val, ctx, horizontal,
        notched, s.name, group.category)
    }

    /* Category labels along category axis. */
    for (let ci = 0; ci < categories.length; ci = ci + 1) {
      const category = categories[ci]
      const bandCenter = cat(category) + bandwidth / 2
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
    break /* Category labels only once */
  }

  return root
}


registerRenderer("boxplot", render)
