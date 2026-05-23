/*
 * dothistogram.js
 *
 * Dot histogram (Wilkinson dot plot) renderer — stacked circles per bin
 * instead of bars.  Auto-switches to bar rendering when counts are too large
 * to draw individually.
 *
 * Registers: "dot-histogram"
 *
 * ctx.model.series data shape:
 *   series[]:
 *     - { name, samples: [n, …] }            renderer bins internally
 *     - { name, bins: [{x0, x1, count}] }    pre-binned
 *
 * Relevant ctx.attrs:
 *   bin-count   integer (Sturges default)
 *   dot-size    radius relative hint (default auto from bin width)
 *   group       "overlay" | (default side-by-side within bins)
 *   dot-limit   max dots per series before falling back to bars (default 200)
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber } from "../svgdraw.js";
import { linearScale, niceTicks } from "../scales.js";


/* ── bin helpers ─────────────────────────────────────────────────────────── */

function _sturgesBinCount(n) {
  const k = Math.ceil(Math.log2(Math.max(n, 1)) + 1)
  return Math.max(k, 2)
}


function _makeBins(samples, binCount) {
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
    if (bi >= binCount) { bi = binCount - 1 }
    bins[bi].count = bins[bi].count + 1
  }
  return bins
}


function _resolveSeries(series, binCountAttr) {
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
    resolved.push({ name: s.name, bins: bins })
  }
  return resolved
}


/* ── main render ─────────────────────────────────────────────────────────── */

export function render(ctx) {
  /*
   * Render a dot histogram.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const model = ctx.model
  const horizontal = ctx.orientation === "horizontal"
  const binCountRaw = parseInt(ctx.attrs("bin-count", "0"), 10) || 0
  const dotSizeAttr = parseFloat(ctx.attrs("dot-size", "0")) || 0
  const overlayMode = ctx.attrs("group", "") === "overlay"
  const dotLimit = parseInt(ctx.attrs("dot-limit", "200"), 10) || 200

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

  /* Global extents. */
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

  const margin = { top: 16, right: 16, bottom: 40, left: 52 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  /* Stacked count domain. */
  let maxStackCount = globalMaxCount
  if (overlayMode === false && resolvedSeries.length > 1) {
    /* Side-by-side: still one series per lane, max is per-series. */
    maxStackCount = globalMaxCount
  }

  const binScale = linearScale([globalMin, globalMax], horizontal ? [0, plotH] : [0, plotW])
  const countScale = horizontal
    ? linearScale([0, maxStackCount * 1.1], [0, plotW])
    : linearScale([0, maxStackCount * 1.1], [plotH, 0])

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  /* Count gridlines + labels. */
  const ticks = niceTicks(0, maxStackCount, 5)
  for (let ti = 0; ti < ticks.length; ti = ti + 1) {
    const tick = ticks[ti]
    if (horizontal === true) {
      const x = countScale(tick)
      plot.appendChild(svgEl("line", {
        x1: x, y1: 0, x2: x, y2: plotH,
        stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
      }, []))
      plot.appendChild(svgEl("text", {
        x: x, y: plotH + 16, "text-anchor": "middle",
        "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
      }, formatNumber(tick)))
    } else {
      const y = countScale(tick)
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

  /* Bin axis labels. */
  const binTicks = niceTicks(globalMin, globalMax, 6)
  for (let ti = 0; ti < binTicks.length; ti = ti + 1) {
    const tick = binTicks[ti]
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

  /* Baseline. */
  const zero = countScale(0)
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

  /* Check if total dots across all series exceeds limit — if so use bars. */
  let totalDots = 0
  for (let si = 0; si < resolvedSeries.length; si = si + 1) {
    for (let bi = 0; bi < resolvedSeries[si].bins.length; bi = bi + 1) {
      totalDots = totalDots + resolvedSeries[si].bins[bi].count
    }
  }
  const useBars = totalDots > dotLimit

  for (let si = 0; si < resolvedSeries.length; si = si + 1) {
    const rs = resolvedSeries[si]
    const color = ctx.colorFor(si)

    /* Compute per-bin pixel width/height to size dots. */
    for (let bi = 0; bi < rs.bins.length; bi = bi + 1) {
      const bin = rs.bins[bi]
      const binPxStart = binScale(bin.x0)
      const binPxEnd = binScale(bin.x1)
      const binPxW = Math.abs(binPxEnd - binPxStart)

      /* Lane within bin for multi-series side-by-side. */
      const laneCount = overlayMode === false && resolvedSeries.length > 1
        ? resolvedSeries.length : 1
      const laneW = binPxW / laneCount
      const laneOffset = overlayMode === false ? si * laneW : 0
      const r = dotSizeAttr > 0 ? dotSizeAttr : Math.max(Math.min(laneW / 2 - 1, 10), 2)

      if (useBars === true) {
        /* Fallback: draw a bar rect. */
        const barOpacity = overlayMode && resolvedSeries.length > 1 ? 0.65 : 1
        if (horizontal === true) {
          const barW = countScale(bin.count)
          const barY = Math.min(binPxStart, binPxEnd) + laneOffset
          const barH = laneW - 1
          const bar = svgEl("rect", {
            x: zero, y: barY, width: barW, height: barH,
            fill: color, opacity: barOpacity
          }, [])
          bar.setAttribute("part", "bar")
          bar.appendChild(svgEl("title", null,
            `${rs.name} [${formatNumber(bin.x0)}–${formatNumber(bin.x1)}]: ${bin.count}`))
          plot.appendChild(bar)
        } else {
          const barH = Math.abs(countScale(bin.count) - zero)
          const barX = Math.min(binPxStart, binPxEnd) + laneOffset
          const barW = laneW - 1
          const bar = svgEl("rect", {
            x: barX, y: countScale(bin.count),
            width: barW, height: barH,
            fill: color, opacity: barOpacity
          }, [])
          bar.setAttribute("part", "bar")
          bar.appendChild(svgEl("title", null,
            `${rs.name} [${formatNumber(bin.x0)}–${formatNumber(bin.x1)}]: ${bin.count}`))
          plot.appendChild(bar)
        }
        continue
      }

      /* Draw stacked dots. */
      const binMid = (binPxStart + binPxEnd) / 2 + (laneCount > 1 ? laneOffset - laneW * (laneCount - 1) / 2 : 0)

      for (let di = 0; di < bin.count; di = di + 1) {
        /* Stack up from the baseline. Each dot sits atop the previous. */
        const dotCenter = di + 0.5
        const cx = horizontal
          ? countScale(0) + (dotCenter) * (r * 2 + 1)
          : binMid
        const cy = horizontal
          ? binMid
          : countScale(0) - (dotCenter) * (r * 2 + 1)

        const dot = svgEl("circle", {
          cx: cx, cy: cy, r: r, fill: color, opacity: 0.85
        }, [])
        dot.setAttribute("part", "dot")
        dot.setAttribute("tabindex", "0")
        dot.setAttribute("role", "img")
        dot.setAttribute("aria-label",
          `${rs.name} [${formatNumber(bin.x0)}–${formatNumber(bin.x1)}] dot ${di + 1} of ${bin.count}`)
        dot.appendChild(svgEl("title", null,
          `${rs.name} [${formatNumber(bin.x0)}–${formatNumber(bin.x1)}]: ${bin.count}`))
        const handlerBin = bin
        const handlerRs = rs
        const clickHandler = () => {
          ctx.emit("mj-chart-dot-click", {
            series: handlerRs.name,
            x0: handlerBin.x0, x1: handlerBin.x1,
            count: handlerBin.count
          })
        }
        dot.addEventListener("click", clickHandler)
        dot.addEventListener("keydown", (event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault()
            clickHandler()
          }
        })
        plot.appendChild(dot)
      }
    }
  }

  return root
}


registerRenderer("dot-histogram", render)
