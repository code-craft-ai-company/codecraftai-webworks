/*
 * forest.js
 *
 * Forest plot (blobbogram) renderer — meta-analysis / subgroup effect sizes.
 *
 * Registers: "forest"
 *
 * JSON shape (ctx.raw):
 *   series: [{
 *     name,
 *     groups: [{ category, value, error_low, error_high, weight? }]
 *   }]
 *   pooled?: { value, ci_lower, ci_upper, label }
 *
 *   value       — point estimate
 *   error_low   — positive half-width below value (CI lower = value - error_low)
 *   error_high  — positive half-width above value (CI upper = value + error_high)
 *   weight      — optional study weight, drives square marker size
 *   pooled      — optional pooled estimate drawn as a diamond
 *
 * ctx.attrs("scale", "linear")   — "log" applies log x-scale
 * ctx.attrs("null-value", "0")   — x position of the null-effect reference line
 *   (auto-set to 1 for log scale when the attribute is absent)
 *
 * Orientation: horizontal only (effect on x, studies on y).
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, formatNumber } from "../svgdraw.js";
import { linearScale, logScale, bandScale, niceTicks } from "../scales.js";


export function render(ctx) {
  /*
   * Render a forest plot.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const raw = ctx.raw
  const scaleType = ctx.attrs("scale", "linear")

  const root = svgEl("g", { part: "plot" }, [])

  if (raw === null || raw === undefined) {
    return root
  }

  const series = Array.isArray(raw.series) ? raw.series : []
  const pooled = (raw.pooled !== null && raw.pooled !== undefined) ? raw.pooled : null

  if (series.length === 0) {
    return root
  }

  /* Collect rows: flatten all series groups into a single category list. */
  const rows = []
  for (let s = 0; s < series.length; s = s + 1) {
    const groups = Array.isArray(series[s].groups) ? series[s].groups : []
    for (let g = 0; g < groups.length; g = g + 1) {
      rows.push({ series: series[s].name, group: groups[g] })
    }
  }

  if (rows.length === 0) {
    return root
  }

  /* Collect categories for band scale (top to bottom). */
  const categories = rows.map((row) => row.group.category)

  /* x domain: include all CI bounds. */
  let xMin = Infinity
  let xMax = -Infinity
  for (let r = 0; r < rows.length; r = r + 1) {
    const gr = rows[r].group
    const lo = gr.value - (gr.error_low || 0)
    const hi = gr.value + (gr.error_high || 0)
    if (lo < xMin) {
      xMin = lo
    }
    if (hi > xMax) {
      xMax = hi
    }
  }
  if (pooled !== null) {
    if (pooled.ci_lower < xMin) {
      xMin = pooled.ci_lower
    }
    if (pooled.ci_upper > xMax) {
      xMax = pooled.ci_upper
    }
  }
  if (xMin === Infinity || xMin === xMax) {
    xMin = 0
    xMax = 1
  }

  /* Determine null-effect reference value. */
  const nullAttrRaw = ctx.attrs("null-value", null)
  let nullValue = 0
  if (nullAttrRaw !== null && nullAttrRaw !== undefined && nullAttrRaw !== "") {
    nullValue = parseFloat(nullAttrRaw)
  } else if (scaleType === "log") {
    nullValue = 1
  }

  /* Ensure null value is within domain. */
  if (nullValue < xMin) {
    xMin = nullValue
  }
  if (nullValue > xMax) {
    xMax = nullValue
  }

  /* Longest label determines left margin. */
  const maxLabelLen = Math.max(...categories.map((cat) => String(cat).length))
  const labelMargin = Math.min(Math.max(maxLabelLen * 7, 60), 200)

  const margin = { top: 16, right: 80, bottom: 40, left: labelMargin }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)

  /* Leave bottom padding if pooled diamond is present. */
  const pooledRows = pooled !== null ? 1 : 0
  const totalRows = categories.length + pooledRows
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  const cat = bandScale(categories, [0, plotH - (pooledRows * 28)], 0.3)
  const xScale = scaleType === "log"
    ? logScale([Math.max(xMin, 1e-9), xMax], [0, plotW])
    : linearScale([xMin, xMax], [0, plotW])

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  /* X-axis gridlines + tick labels. */
  const xTicks = scaleType === "log"
    ? xScale.ticks(5)
    : niceTicks(xMin, xMax, 5)
  for (let t = 0; t < xTicks.length; t = t + 1) {
    const tick = xTicks[t]
    const x = xScale(tick)
    plot.appendChild(svgEl("line", {
      x1: x, y1: 0, x2: x, y2: plotH,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    plot.appendChild(svgEl("text", {
      x: x, y: plotH + 16, "text-anchor": "middle",
      "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
    }, formatNumber(tick)))
  }

  /* Null-effect reference line. */
  const xNull = xScale(nullValue)
  plot.appendChild(svgEl("line", {
    x1: xNull, y1: 0, x2: xNull, y2: plotH,
    stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
  }, []))

  /* Weight scale: map weight → half-side of square marker. */
  const weights = rows.map((row) => row.group.weight || 1)
  const wMin = Math.min(...weights)
  const wMax = Math.max(...weights)
  const wRange = wMax > wMin ? wMax - wMin : 1
  const minHalf = 3
  const maxHalf = Math.min(cat.bandwidth() / 2 - 1, 10)

  const weightToHalf = (w) => {
    const frac = (w - wMin) / wRange
    const half = minHalf + frac * (maxHalf - minHalf)
    return half
  }

  /* Draw each study row. */
  for (let r = 0; r < rows.length; r = r + 1) {
    const row = rows[r]
    const gr = row.group
    const bandStart = cat(gr.category)
    const bandMid = bandStart + cat.bandwidth() / 2
    const color = ctx.colorFor(row.series)

    const cilo = gr.value - (gr.error_low || 0)
    const cihi = gr.value + (gr.error_high || 0)
    const xPt = xScale(gr.value)
    const xLo = xScale(cilo)
    const xHi = xScale(cihi)
    const halfSquare = weightToHalf(gr.weight || 1)

    const label = `${escapeHtml(gr.category)}: ${formatNumber(gr.value)} ` +
      `[${formatNumber(cilo)}, ${formatNumber(cihi)}]`

    const group = svgEl("g", {
      part: "study",
      tabindex: "0",
      role: "img",
      "aria-label": label
    }, [])
    group.appendChild(svgEl("title", null, label))

    /* CI whisker line. */
    group.appendChild(svgEl("line", {
      x1: xLo, y1: bandMid, x2: xHi, y2: bandMid,
      stroke: color, "stroke-width": 1.5
    }, []))
    /* CI cap left. */
    group.appendChild(svgEl("line", {
      x1: xLo, y1: bandMid - 4, x2: xLo, y2: bandMid + 4,
      stroke: color, "stroke-width": 1.5
    }, []))
    /* CI cap right. */
    group.appendChild(svgEl("line", {
      x1: xHi, y1: bandMid - 4, x2: xHi, y2: bandMid + 4,
      stroke: color, "stroke-width": 1.5
    }, []))
    /* Square marker at point estimate. */
    group.appendChild(svgEl("rect", {
      x: xPt - halfSquare, y: bandMid - halfSquare,
      width: halfSquare * 2, height: halfSquare * 2,
      fill: color
    }, []))

    const handler = () => {
      ctx.emit("mj-chart-study-click", {
        series: row.series,
        category: gr.category,
        value: gr.value,
        ci_lower: cilo,
        ci_upper: cihi,
        weight: gr.weight
      })
    }
    group.addEventListener("click", handler)
    group.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault()
        handler()
      }
    })
    plot.appendChild(group)

    /* Study label (left of plot). */
    plot.appendChild(svgEl("text", {
      x: -8, y: bandMid + 4, "text-anchor": "end",
      "font-size": 11, fill: "var(--mj-text, #14181f)"
    }, escapeHtml(gr.category)))

    /* Value label (right of plot). */
    const valueText = `${formatNumber(gr.value)} ` +
      `[${formatNumber(cilo)}, ${formatNumber(cihi)}]`
    plot.appendChild(svgEl("text", {
      x: plotW + 8, y: bandMid + 4, "text-anchor": "start",
      "font-size": 10, fill: "var(--mj-text-muted, #6b7280)"
    }, valueText))
  }

  /* Pooled estimate diamond. */
  if (pooled !== null) {
    const diamondY = plotH - 20
    const xPt = xScale(pooled.value)
    const xLo = xScale(pooled.ci_lower)
    const xHi = xScale(pooled.ci_upper)
    const diamondH = 10

    const diamondPts =
      `${xPt},${diamondY - diamondH} ` +
      `${xHi},${diamondY} ` +
      `${xPt},${diamondY + diamondH} ` +
      `${xLo},${diamondY}`

    const pooledLabel = pooled.label
      ? String(pooled.label)
      : `Pooled: ${formatNumber(pooled.value)} [${formatNumber(pooled.ci_lower)}, ${formatNumber(pooled.ci_upper)}]`

    const diamond = svgEl("polygon", {
      points: diamondPts,
      fill: "var(--mj-color-neutral-500, #6b7280)",
      part: "pooled",
      tabindex: "0",
      role: "img",
      "aria-label": pooledLabel
    }, [])
    diamond.appendChild(svgEl("title", null, pooledLabel))

    const handler = () => {
      ctx.emit("mj-chart-pooled-click", {
        value: pooled.value,
        ci_lower: pooled.ci_lower,
        ci_upper: pooled.ci_upper,
        label: pooled.label
      })
    }
    diamond.addEventListener("click", handler)
    diamond.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault()
        handler()
      }
    })
    plot.appendChild(diamond)

    plot.appendChild(svgEl("text", {
      x: -8, y: diamondY + 4, "text-anchor": "end",
      "font-size": 11, fill: "var(--mj-text, #14181f)", "font-weight": "bold"
    }, escapeHtml(pooledLabel)))
  }

  /* Axis baselines. */
  plot.appendChild(svgEl("line", {
    x1: 0, y1: plotH, x2: plotW, y2: plotH,
    stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
  }, []))
  plot.appendChild(svgEl("line", {
    x1: 0, y1: 0, x2: 0, y2: plotH,
    stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
  }, []))

  return root
}


registerRenderer("forest", render)
