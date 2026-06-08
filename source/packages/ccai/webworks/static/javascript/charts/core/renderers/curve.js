/*
 * curve.js
 *
 * Diagnostic-curve renderer — ROC, precision-recall, lift, and calibration.
 *
 * Registers: "roc", "precision-recall", "lift", "calibration"
 *
 * JSON shape (ctx.raw):
 *   series: [{ name, points: [{ x, y, n? }] }]
 *
 *   For calibration: n (optional) on each point drives dot size (sqrt scale).
 *
 * Each type key injects axis-label presets and a reference annotation:
 *   roc              — diagonal chance line (0,0)→(1,1), domain [0,1]×[0,1]
 *   precision-recall — horizontal baseline at y = raw.baseline_prevalence (if present)
 *   lift             — horizontal baseline at y = 1
 *   calibration      — diagonal perfect-calibration line, domain [0,1]×[0,1]
 *
 * ctx.attrs("shade-auc", "false")  — fill area under curve for ROC / PR
 * ctx.attrs("size-by", "")         — set to "n" to size calibration dots by n
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber, linePath, areaPath } from "../svgdraw.js";
import { linearScale, sqrtScale, niceTicks } from "../scales.js";


/* Per-type axis and reference-line configuration. */
const TYPE_CONFIG = {
  "roc": {
    xLabel: "False Positive Rate",
    yLabel: "True Positive Rate",
    xDomain: [0, 1],
    yDomain: [0, 1],
    referenceDiagonal: true,
    referenceHorizontal: null
  },
  "precision-recall": {
    xLabel: "Recall",
    yLabel: "Precision",
    xDomain: [0, 1],
    yDomain: [0, 1],
    referenceDiagonal: false,
    referenceHorizontal: "baseline_prevalence"
  },
  "lift": {
    xLabel: "% Population Contacted",
    yLabel: "Lift",
    xDomain: [0, 1],
    yDomain: null,
    referenceDiagonal: false,
    referenceHorizontal: 1
  },
  "calibration": {
    xLabel: "Mean Predicted Probability",
    yLabel: "Fraction of Positives",
    xDomain: [0, 1],
    yDomain: [0, 1],
    referenceDiagonal: true,
    referenceHorizontal: null
  }
}


export function render(ctx) {
  /*
   * Render a diagnostic curve chart.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const raw = ctx.raw
  const chartType = ctx.attrs("type", "roc")
  const shadeAuc = ctx.attrs("shade-auc", "false") === "true"
  const sizeBy = ctx.attrs("size-by", "")

  const root = svgEl("g", { part: "plot" }, [])

  if (raw === null || raw === undefined) {
    return root
  }

  const series = Array.isArray(raw.series) ? raw.series : []
  if (series.length === 0) {
    return root
  }

  const config = TYPE_CONFIG[chartType] || TYPE_CONFIG["roc"]

  /* Determine x and y domains. */
  let xMin = config.xDomain !== null ? config.xDomain[0] : Infinity
  let xMax = config.xDomain !== null ? config.xDomain[1] : -Infinity
  let yMin = config.yDomain !== null ? config.yDomain[0] : Infinity
  let yMax = config.yDomain !== null ? config.yDomain[1] : -Infinity

  /* Expand from data when domain is not fixed. */
  for (let s = 0; s < series.length; s = s + 1) {
    const points = Array.isArray(series[s].points) ? series[s].points : []
    for (let p = 0; p < points.length; p = p + 1) {
      const px = Number(points[p].x)
      const py = Number(points[p].y)
      if (config.xDomain === null) {
        if (px < xMin) {
          xMin = px
        }
        if (px > xMax) {
          xMax = px
        }
      }
      if (config.yDomain === null) {
        if (py < yMin) {
          yMin = py
        }
        if (py > yMax) {
          yMax = py
        }
      }
    }
  }
  if (xMin === Infinity || xMin === xMax) {
    xMin = 0
    xMax = 1
  }
  if (yMin === Infinity || yMin === yMax) {
    yMin = 0
    yMax = 1
  }

  /* For lift, ensure baseline = 1 is always visible. */
  if (chartType === "lift" && yMin > 1) {
    yMin = 0
  }

  const margin = { top: 16, right: 16, bottom: 48, left: 64 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  const xScale = linearScale([xMin, xMax], [0, plotW])
  const yScale = linearScale([yMin, yMax], [plotH, 0])

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  /* Grid + axis labels. */
  const yTicks = niceTicks(yMin, yMax, 5)
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
    }, formatNumber(tick)))
  }

  const xTicks = niceTicks(xMin, xMax, 5)
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

  /* Axis label text (x-axis). */
  plot.appendChild(svgEl("text", {
    x: plotW / 2, y: plotH + 36, "text-anchor": "middle",
    "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
  }, config.xLabel))

  /* Y-axis label (rotated). */
  plot.appendChild(svgEl("text", {
    transform: `translate(-44,${plotH / 2}) rotate(-90)`,
    "text-anchor": "middle",
    "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
  }, config.yLabel))

  /* Reference diagonal (ROC chance line / calibration perfect line). */
  if (config.referenceDiagonal === true) {
    const x0 = xScale(xMin)
    const y0 = yScale(yMin)
    const x1 = xScale(xMax)
    const y1 = yScale(yMax)
    plot.appendChild(svgEl("line", {
      x1: x0, y1: y0, x2: x1, y2: y1,
      stroke: "var(--mj-border-strong, #c7ccd6)",
      "stroke-width": 1.5,
      "stroke-dasharray": "4 3"
    }, []))
  }

  /* Horizontal reference line (lift=1, PR=prevalence). */
  let refHorizValue = null
  if (typeof config.referenceHorizontal === "number") {
    refHorizValue = config.referenceHorizontal
  } else if (typeof config.referenceHorizontal === "string") {
    const rawRef = raw[config.referenceHorizontal]
    if (rawRef !== undefined && rawRef !== null) {
      refHorizValue = Number(rawRef)
    }
  }
  if (refHorizValue !== null) {
    const yRef = yScale(refHorizValue)
    plot.appendChild(svgEl("line", {
      x1: 0, y1: yRef, x2: plotW, y2: yRef,
      stroke: "var(--mj-border-strong, #c7ccd6)",
      "stroke-width": 1.5,
      "stroke-dasharray": "4 3"
    }, []))
  }

  /* Calibration: optional dot size scale. */
  let nExtent = [0, 1]
  if (sizeBy === "n" && chartType === "calibration") {
    const allN = []
    for (let s = 0; s < series.length; s = s + 1) {
      const points = Array.isArray(series[s].points) ? series[s].points : []
      for (let p = 0; p < points.length; p = p + 1) {
        if (points[p].n !== undefined && points[p].n !== null) {
          allN.push(Number(points[p].n))
        }
      }
    }
    if (allN.length > 0) {
      nExtent = [Math.min(...allN), Math.max(...allN)]
    }
  }
  const nScale = sqrtScale(nExtent, [4, 14])

  /* Draw each series. */
  for (let s = 0; s < series.length; s = s + 1) {
    const serie = series[s]
    const points = Array.isArray(serie.points) ? serie.points : []
    const color = ctx.colorFor(serie.name)

    if (points.length === 0) {
      continue
    }

    const pathPts = points.map((pt) => {
      return { x: xScale(Number(pt.x)), y: yScale(Number(pt.y)) }
    })

    /* Optional AUC/area shading. */
    if (shadeAuc === true) {
      const areaD = areaPath(pathPts, plotH)
      if (areaD !== "") {
        plot.appendChild(svgEl("path", {
          d: areaD,
          fill: color, opacity: 0.15
        }, []))
      }
    }

    /* Curve line. */
    const pathD = linePath(pathPts)
    if (pathD !== "") {
      plot.appendChild(svgEl("path", {
        d: pathD, fill: "none",
        stroke: color, "stroke-width": 2
      }, []))
    }

    /* Points (dots). */
    for (let p = 0; p < points.length; p = p + 1) {
      const pt = points[p]
      const px = xScale(Number(pt.x))
      const py = yScale(Number(pt.y))
      const dotR = (sizeBy === "n" && pt.n !== undefined && pt.n !== null)
        ? nScale(Number(pt.n))
        : 4

      const label = `${serie.name}: (${formatNumber(pt.x)}, ${formatNumber(pt.y)})` +
        (pt.n !== undefined ? ` n=${pt.n}` : "")

      const circle = svgEl("circle", {
        cx: px, cy: py, r: dotR,
        fill: color,
        part: "point",
        tabindex: "0",
        role: "img",
        "aria-label": label
      }, [])
      circle.appendChild(svgEl("title", null, label))

      const handler = () => {
        ctx.emit("mj-chart-point-click", {
          series: serie.name,
          x: pt.x,
          y: pt.y
        })
      }
      circle.addEventListener("click", handler)
      circle.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault()
          handler()
        }
      })

      plot.appendChild(circle)
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


registerRenderer("roc", render)
registerRenderer("precision-recall", render)
registerRenderer("lift", render)
registerRenderer("calibration", render)
