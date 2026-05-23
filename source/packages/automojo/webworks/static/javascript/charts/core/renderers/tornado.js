/*
 * tornado.js
 *
 * Tornado / sensitivity renderer.
 *
 * Registers:
 *   "tornado" — paired horizontal bars diverging from a center baseline,
 *               rows sorted top-to-bottom by spread magnitude (widest first).
 *               style="butterfly" treats low/high as magnitudes rather than
 *               absolute values and mirrors bars symmetrically.
 *
 * ctx.raw shape:
 *   baseline: number          (central reference value)
 *   series: [{
 *     name: string,
 *     values: [{ label, low, high }]
 *   }]
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, formatNumber } from "../svgdraw.js";
import { linearScale, bandScale, niceTicks } from "../scales.js";


export function render(ctx) {
  /*
   * Render a tornado/sensitivity chart.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const raw = ctx.raw
  const baseline = (raw !== null && raw !== undefined && typeof raw.baseline === "number")
    ? raw.baseline : 0
  const seriesArr = (raw !== null && raw !== undefined && Array.isArray(raw.series))
    ? raw.series : []

  const isButterfly = ctx.attrs("style", "") === "butterfly"

  const root = svgEl("g", { part: "plot" }, [])

  /* Flatten all values from the first series (tornado uses one series). */
  const rawValues = []
  for (let s = 0; s < seriesArr.length; s = s + 1) {
    const series = seriesArr[s]
    if (Array.isArray(series.values) === false) {
      continue
    }
    for (let v = 0; v < series.values.length; v = v + 1) {
      rawValues.push(series.values[v])
    }
  }

  if (rawValues.length === 0) {
    return root
  }

  /* Normalise: if butterfly mode treat low/high as magnitudes from baseline. */
  const normValues = rawValues.map((entry) => {
    const low = typeof entry.low === "number" ? entry.low : 0
    const high = typeof entry.high === "number" ? entry.high : 0
    let normLow = low
    let normHigh = high
    if (isButterfly === true) {
      normLow = baseline - Math.abs(low)
      normHigh = baseline + Math.abs(high)
    }
    return { label: entry.label, low: normLow, high: normHigh }
  })

  /* Sort rows by spread magnitude descending (widest bar = top). */
  normValues.sort((a, b) => {
    const spreadA = Math.abs(a.high - a.low)
    const spreadB = Math.abs(b.high - b.low)
    return spreadB - spreadA
  })

  /* Compute value domain: encompass all low/high plus baseline. */
  let domainMin = baseline
  let domainMax = baseline
  for (let index = 0; index < normValues.length; index = index + 1) {
    const entry = normValues[index]
    if (entry.low < domainMin) {
      domainMin = entry.low
    }
    if (entry.high > domainMax) {
      domainMax = entry.high
    }
  }
  /* Pad domain a bit. */
  const domainPad = (domainMax - domainMin) * 0.05
  domainMin = domainMin - domainPad
  domainMax = domainMax + domainPad
  if (domainMin === domainMax) {
    domainMin = domainMin - 1
    domainMax = domainMax + 1
  }

  const labels = normValues.map((entry) => {
    const label = entry.label !== undefined ? String(entry.label) : ""
    return label
  })

  const margin = { top: 16, right: 16, bottom: 40, left: 120 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  const valScale = linearScale([domainMin, domainMax], [0, plotW])
  const rowScale = bandScale(labels, [0, plotH], 0.2)
  const bandwidth = rowScale.bandwidth()

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  /* Value axis ticks (bottom). */
  const ticks = niceTicks(domainMin, domainMax, 5)
  for (let t = 0; t < ticks.length; t = t + 1) {
    const tick = ticks[t]
    const x = valScale(tick)
    plot.appendChild(svgEl("line", {
      x1: x, y1: 0, x2: x, y2: plotH,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    plot.appendChild(svgEl("text", {
      x: x, y: plotH + 16, "text-anchor": "middle",
      "font-size": 10, fill: "var(--mj-text-muted, #6b7280)"
    }, formatNumber(tick)))
  }

  /* Baseline center line. */
  const baselineX = valScale(baseline)
  plot.appendChild(svgEl("line", {
    x1: baselineX, y1: 0, x2: baselineX, y2: plotH,
    stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
  }, []))

  /* Axis baseline. */
  plot.appendChild(svgEl("line", {
    x1: 0, y1: plotH, x2: plotW, y2: plotH,
    stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
  }, []))

  const lowColor = "var(--mj-chart-negative, var(--mj-color-danger, #b91c1c))"
  const highColor = "var(--mj-chart-positive, var(--mj-color-success, #15803d))"

  /* Draw rows. */
  for (let index = 0; index < normValues.length; index = index + 1) {
    const entry = normValues[index]
    const label = entry.label !== undefined ? String(entry.label) : ""
    const rowY = rowScale(label)
    const barH = Math.max(bandwidth, 4)

    /* Row label. */
    plot.appendChild(svgEl("text", {
      x: -8, y: rowY + barH / 2 + 4,
      "text-anchor": "end", "font-size": 11,
      fill: "var(--mj-text, #14181f)"
    }, escapeHtml(label)))

    /* Left bar: from low up to baseline. */
    const lowX = valScale(entry.low)
    const baseX = valScale(baseline)
    const leftBarX = Math.min(lowX, baseX)
    const leftBarW = Math.abs(baseX - lowX)

    if (leftBarW > 0) {
      const ariaLow = `${escapeHtml(label)} low: ${formatNumber(entry.low)}`
      const leftBar = svgEl("rect", {
        x: leftBarX, y: rowY, width: leftBarW, height: barH, rx: 2,
        fill: lowColor, "fill-opacity": 0.8, part: "bar"
      }, [])
      leftBar.setAttribute("tabindex", "0")
      leftBar.setAttribute("role", "img")
      leftBar.setAttribute("aria-label", ariaLow)
      leftBar.appendChild(svgEl("title", null, ariaLow))

      const emitEntry = entry
      const clickHandlerLow = () => {
        ctx.emit("mj-chart-bar-click", {
          label: emitEntry.label,
          side: "low",
          value: emitEntry.low,
          baseline: baseline
        })
      }
      leftBar.addEventListener("click", clickHandlerLow)
      leftBar.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault()
          clickHandlerLow()
        }
      })
      plot.appendChild(leftBar)
    }

    /* Right bar: from baseline up to high. */
    const highX = valScale(entry.high)
    const rightBarX = Math.min(baseX, highX)
    const rightBarW = Math.abs(highX - baseX)

    if (rightBarW > 0) {
      const ariaHigh = `${escapeHtml(label)} high: ${formatNumber(entry.high)}`
      const rightBar = svgEl("rect", {
        x: rightBarX, y: rowY, width: rightBarW, height: barH, rx: 2,
        fill: highColor, "fill-opacity": 0.8, part: "bar"
      }, [])
      rightBar.setAttribute("tabindex", "0")
      rightBar.setAttribute("role", "img")
      rightBar.setAttribute("aria-label", ariaHigh)
      rightBar.appendChild(svgEl("title", null, ariaHigh))

      const emitEntry = entry
      const clickHandlerHigh = () => {
        ctx.emit("mj-chart-bar-click", {
          label: emitEntry.label,
          side: "high",
          value: emitEntry.high,
          baseline: baseline
        })
      }
      rightBar.addEventListener("click", clickHandlerHigh)
      rightBar.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault()
          clickHandlerHigh()
        }
      })
      plot.appendChild(rightBar)
    }
  }

  return root
}


registerRenderer("tornado", render);
