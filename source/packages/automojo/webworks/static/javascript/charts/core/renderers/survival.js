/*
 * survival.js
 *
 * Survival curve / Kaplan-Meier renderer.
 *
 * Registers: "survival", "kaplan-meier"
 *
 * JSON shape (ctx.raw):
 *   series: [{
 *     name,
 *     points: [{ x, y, censored?, ci_lower?, ci_upper?, at_risk? }]
 *   }]
 *
 *   x          — time
 *   y          — survival probability (0–1)
 *   censored   — true marks a censored observation (tick, not a step drop)
 *   ci_lower   — lower confidence bound (requires ctx.attrs("ci","false")="true")
 *   ci_upper   — upper confidence bound
 *   at_risk    — number at risk (used for numbers-at-risk table)
 *
 * ctx.attrs("ci", "false")       — show confidence bands
 * ctx.attrs("at-risk", "false")  — show numbers-at-risk table below plot
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber } from "../svgdraw.js";
import { linearScale, niceTicks } from "../scales.js";


function _buildStepPath(points, xScale, yScale) {
  /*
   * Build an SVG path `d` for a Kaplan-Meier step function.
   * Each non-censored point drops vertically then moves horizontally.
   *
   * :param points: Array of { x, y, censored }.
   * :param xScale: x pixel scale function.
   * :param yScale: y pixel scale function.
   * :returns: A path data string.
   */
  const realPts = points.filter((pt) => pt.censored !== true)
  if (realPts.length === 0) {
    return ""
  }

  let d = `M${xScale(Number(realPts[0].x)).toFixed(2)},${yScale(Number(realPts[0].y)).toFixed(2)}`
  for (let index = 1; index < realPts.length; index = index + 1) {
    const prev = realPts[index - 1]
    const curr = realPts[index]
    const px = xScale(Number(curr.x)).toFixed(2)
    const py = yScale(Number(curr.y)).toFixed(2)
    const prevY = yScale(Number(prev.y)).toFixed(2)
    /* Horizontal to new x at old y, then vertical to new y. */
    d = d + ` H${px} V${py}`
  }
  /* Extend horizontally to plot edge from last point. */
  const last = realPts[realPts.length - 1]
  d = d + ` H${xScale(Number(last.x)).toFixed(2)}`

  return d
}


export function render(ctx) {
  /*
   * Render a survival or Kaplan-Meier curve.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const raw = ctx.raw
  const showCI = ctx.attrs("ci", "false") === "true"
  const showAtRisk = ctx.attrs("at-risk", "false") === "true"

  const root = svgEl("g", { part: "plot" }, [])

  if (raw === null || raw === undefined) {
    return root
  }

  const series = Array.isArray(raw.series) ? raw.series : []
  if (series.length === 0) {
    return root
  }

  /* Collect time extents across all series. */
  let xMin = Infinity
  let xMax = -Infinity
  for (let s = 0; s < series.length; s = s + 1) {
    const points = Array.isArray(series[s].points) ? series[s].points : []
    for (let p = 0; p < points.length; p = p + 1) {
      const xv = Number(points[p].x)
      if (xv < xMin) {
        xMin = xv
      }
      if (xv > xMax) {
        xMax = xv
      }
    }
  }
  if (xMin === Infinity) {
    return root
  }
  if (xMin === xMax) {
    xMax = xMin + 1
  }

  const atRiskRowH = (showAtRisk === true) ? series.length * 16 + 8 : 0
  const margin = { top: 16, right: 16, bottom: 40 + atRiskRowH, left: 60 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  const xScale = linearScale([xMin, xMax], [0, plotW])
  const yScale = linearScale([0, 1], [plotH, 0])

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  /* Y-axis gridlines + tick labels (0–1). */
  const yTicks = niceTicks(0, 1, 5)
  for (let t = 0; t < yTicks.length; t = t + 1) {
    const tick = yTicks[t]
    const y = yScale(tick)
    plot.appendChild(svgEl("line", {
      x1: 0, y1: y, x2: plotW, y2: y,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    plot.appendChild(svgEl("text", {
      x: -8, y: y + 4, "text-anchor": "end",
      "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
    }, formatNumber(tick, { maximumFractionDigits: 2 })))
  }

  /* X-axis tick labels. */
  const xTicks = niceTicks(xMin, xMax, 6)
  for (let t = 0; t < xTicks.length; t = t + 1) {
    const tick = xTicks[t]
    const x = xScale(tick)
    plot.appendChild(svgEl("text", {
      x: x, y: plotH + 16, "text-anchor": "middle",
      "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
    }, formatNumber(tick)))
  }

  /* Draw each series. */
  for (let s = 0; s < series.length; s = s + 1) {
    const serie = series[s]
    const points = Array.isArray(serie.points) ? serie.points : []
    const color = ctx.colorFor(serie.name)

    if (points.length === 0) {
      continue
    }

    /* Confidence band. */
    if (showCI === true) {
      const ciPoints = points.filter((pt) => {
        return pt.ci_lower !== undefined && pt.ci_upper !== undefined &&
          pt.censored !== true
      })
      if (ciPoints.length >= 2) {
        const upperPts = ciPoints.map((pt) => {
          return {
            x: xScale(Number(pt.x)),
            y: yScale(Number(pt.ci_upper))
          }
        })
        const lowerPts = ciPoints.map((pt) => {
          return {
            x: xScale(Number(pt.x)),
            y: yScale(Number(pt.ci_lower))
          }
        })
        /* Build closed area polygon from upper + reversed lower path. */
        let ciD = `M${upperPts[0].x.toFixed(2)},${upperPts[0].y.toFixed(2)}`
        for (let p = 1; p < upperPts.length; p = p + 1) {
          ciD = ciD + ` H${upperPts[p].x.toFixed(2)} V${upperPts[p].y.toFixed(2)}`
        }
        for (let p = lowerPts.length - 1; p >= 0; p = p - 1) {
          ciD = ciD + ` L${lowerPts[p].x.toFixed(2)},${lowerPts[p].y.toFixed(2)}`
        }
        ciD = ciD + " Z"
        plot.appendChild(svgEl("path", {
          d: ciD, fill: color, opacity: 0.15
        }, []))
      }
    }

    /* Step-function line. */
    const stepD = _buildStepPath(points, xScale, yScale)
    if (stepD !== "") {
      plot.appendChild(svgEl("path", {
        d: stepD, fill: "none",
        stroke: color, "stroke-width": 2
      }, []))
    }

    /* Censored tick marks. */
    for (let p = 0; p < points.length; p = p + 1) {
      const pt = points[p]
      if (pt.censored !== true) {
        continue
      }
      const px = xScale(Number(pt.x))
      const py = yScale(Number(pt.y))
      const label = `${serie.name}: censored at x=${formatNumber(pt.x)}, S(t)=${formatNumber(pt.y)}`
      const tick = svgEl("line", {
        x1: px, y1: py - 6, x2: px, y2: py + 6,
        stroke: color, "stroke-width": 1.5,
        part: "censor-tick",
        tabindex: "0",
        role: "img",
        "aria-label": label
      }, [])
      tick.appendChild(svgEl("title", null, label))

      const handler = () => {
        ctx.emit("mj-chart-point-click", {
          series: serie.name,
          x: pt.x,
          y: pt.y,
          censored: true
        })
      }
      tick.addEventListener("click", handler)
      tick.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault()
          handler()
        }
      })
      plot.appendChild(tick)
    }
  }

  /* Numbers-at-risk table. */
  if (showAtRisk === true) {
    const tableY = plotH + 32
    const atRiskTicks = xTicks

    for (let s = 0; s < series.length; s = s + 1) {
      const serie = series[s]
      const points = Array.isArray(serie.points) ? serie.points : []
      const color = ctx.colorFor(serie.name)
      const rowY = tableY + s * 16

      plot.appendChild(svgEl("text", {
        x: -8, y: rowY, "text-anchor": "end",
        "font-size": 10, fill: color
      }, String(serie.name)))

      for (let t = 0; t < atRiskTicks.length; t = t + 1) {
        const tickX = atRiskTicks[t]
        /* Find the at_risk value for the closest time point <= tickX. */
        let atRiskVal = ""
        for (let p = points.length - 1; p >= 0; p = p - 1) {
          if (Number(points[p].x) <= tickX && points[p].at_risk !== undefined) {
            atRiskVal = String(points[p].at_risk)
            break
          }
        }
        plot.appendChild(svgEl("text", {
          x: xScale(tickX), y: rowY, "text-anchor": "middle",
          "font-size": 10, fill: "var(--mj-text-muted, #6b7280)"
        }, atRiskVal))
      }
    }
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


registerRenderer("survival", render)
registerRenderer("kaplan-meier", render)
