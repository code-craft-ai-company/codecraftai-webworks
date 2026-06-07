/*
 * funnelplot.js
 *
 * Funnel plot renderer — publication-bias / small-study-effects scatter
 * with funnel boundary overlay.
 *
 * Registers: "funnel-plot"
 *
 * JSON shape (ctx.raw):
 *   series: [{ name, points: [{ x, y, label? }] }]
 *   funnel?: {
 *     summary_effect: number,
 *     pseudo_ci: [{ se, lower, upper }]
 *   }
 *
 *   x     — study effect estimate
 *   y     — standard error (precision); y-axis is INVERTED (0 at top)
 *   label — optional point label
 *
 *   funnel.summary_effect  — pooled effect; vertical reference line
 *   funnel.pseudo_ci       — pre-computed funnel bounds at each SE level
 *     se    — standard error level (y-axis position)
 *     lower — lower bound of funnel at this se
 *     upper — upper bound of funnel at this se
 *
 * ctx.attrs("contours", "false") — shade significance-level regions
 * ctx.attrs("labels", "false")   — render study point labels
 *
 * Note: y-axis is inverted — higher SE (less precise) at the bottom,
 * se = 0 (most precise) at the top.
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber, escapeHtml } from "../svgdraw.js";
import { linearScale, niceTicks } from "../scales.js";


export function render(ctx) {
  /*
   * Render a funnel plot.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const raw = ctx.raw
  const showContours = ctx.attrs("contours", "false") === "true"
  const showLabels = ctx.attrs("labels", "false") === "true"

  const root = svgEl("g", { part: "plot" }, [])

  if (raw === null || raw === undefined) {
    return root
  }

  const series = Array.isArray(raw.series) ? raw.series : []
  const funnel = (raw.funnel !== null && raw.funnel !== undefined) ? raw.funnel : null

  if (series.length === 0) {
    return root
  }

  /* Collect all x and y values. */
  let xMin = Infinity
  let xMax = -Infinity
  let yMin = 0
  let yMax = -Infinity

  for (let s = 0; s < series.length; s = s + 1) {
    const points = Array.isArray(series[s].points) ? series[s].points : []
    for (let p = 0; p < points.length; p = p + 1) {
      const px = Number(points[p].x)
      const py = Number(points[p].y)
      if (px < xMin) {
        xMin = px
      }
      if (px > xMax) {
        xMax = px
      }
      if (py > yMax) {
        yMax = py
      }
    }
  }

  /* Expand x domain to encompass funnel bounds. */
  if (funnel !== null && Array.isArray(funnel.pseudo_ci) === true) {
    for (let c = 0; c < funnel.pseudo_ci.length; c = c + 1) {
      const bound = funnel.pseudo_ci[c]
      if (bound.lower < xMin) {
        xMin = bound.lower
      }
      if (bound.upper > xMax) {
        xMax = bound.upper
      }
      if (Number(bound.se) > yMax) {
        yMax = Number(bound.se)
      }
    }
  }

  if (xMin === Infinity || xMin === xMax) {
    xMin = -1
    xMax = 1
  }
  if (yMax <= 0) {
    yMax = 1
  }

  /* Pad x domain slightly. */
  const xPad = (xMax - xMin) * 0.05
  xMin = xMin - xPad
  xMax = xMax + xPad

  const margin = { top: 16, right: 16, bottom: 40, left: 64 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  /* y-axis is inverted: SE=0 at top (y=0), max SE at bottom (y=plotH). */
  const xScale = linearScale([xMin, xMax], [0, plotW])
  const yScale = linearScale([0, yMax], [0, plotH])

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  /* Y-axis gridlines + tick labels (SE, 0 at top). */
  const yTicks = niceTicks(0, yMax, 5)
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

  /* X-axis gridlines + tick labels. */
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

  /* Axis labels. */
  plot.appendChild(svgEl("text", {
    x: plotW / 2, y: plotH + 34, "text-anchor": "middle",
    "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
  }, "Effect Estimate"))
  plot.appendChild(svgEl("text", {
    transform: `translate(-44,${plotH / 2}) rotate(-90)`,
    "text-anchor": "middle",
    "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
  }, "Standard Error"))

  /* Funnel boundary paths and optional contour shading. */
  if (funnel !== null && Array.isArray(funnel.pseudo_ci) === true) {
    const pseudo = funnel.pseudo_ci.slice()
    /* Sort by se ascending so paths render from top (se=0) downward. */
    pseudo.sort((a, b) => Number(a.se) - Number(b.se))

    if (pseudo.length >= 2) {
      /* Build the upper boundary line (lower bound → converges upward). */
      let lowerD = `M${xScale(pseudo[0].lower).toFixed(2)},${yScale(Number(pseudo[0].se)).toFixed(2)}`
      let upperD = `M${xScale(pseudo[0].upper).toFixed(2)},${yScale(Number(pseudo[0].se)).toFixed(2)}`
      for (let c = 1; c < pseudo.length; c = c + 1) {
        lowerD = lowerD +
          ` L${xScale(pseudo[c].lower).toFixed(2)},${yScale(Number(pseudo[c].se)).toFixed(2)}`
        upperD = upperD +
          ` L${xScale(pseudo[c].upper).toFixed(2)},${yScale(Number(pseudo[c].se)).toFixed(2)}`
      }

      /* Optional contour fill between funnel lines. */
      if (showContours === true) {
        /* Build closed funnel polygon. */
        let contourD = lowerD
        for (let c = pseudo.length - 1; c >= 0; c = c - 1) {
          contourD = contourD +
            ` L${xScale(pseudo[c].upper).toFixed(2)},${yScale(Number(pseudo[c].se)).toFixed(2)}`
        }
        contourD = contourD + " Z"
        plot.appendChild(svgEl("path", {
          d: contourD,
          fill: "var(--mj-color-accent-500, #2563eb)", opacity: 0.07
        }, []))
      }

      /* Funnel boundary strokes. */
      plot.appendChild(svgEl("path", {
        d: lowerD, fill: "none",
        stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5,
        "stroke-dasharray": "5 3"
      }, []))
      plot.appendChild(svgEl("path", {
        d: upperD, fill: "none",
        stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5,
        "stroke-dasharray": "5 3"
      }, []))
    }

    /* Vertical summary-effect reference line. */
    const xSummary = xScale(funnel.summary_effect)
    plot.appendChild(svgEl("line", {
      x1: xSummary, y1: 0, x2: xSummary, y2: plotH,
      stroke: "var(--mj-color-accent-500, #2563eb)", "stroke-width": 1.5
    }, []))
  }

  /* Draw study point scatter. */
  for (let s = 0; s < series.length; s = s + 1) {
    const serie = series[s]
    const points = Array.isArray(serie.points) ? serie.points : []
    const color = ctx.colorFor(serie.name)

    for (let p = 0; p < points.length; p = p + 1) {
      const pt = points[p]
      const px = xScale(Number(pt.x))
      const py = yScale(Number(pt.y))
      const ptLabel = pt.label ? String(pt.label) : ""
      const ariaLabel = ptLabel !== ""
        ? `${ptLabel}: effect=${formatNumber(pt.x)}, SE=${formatNumber(pt.y)}`
        : `effect=${formatNumber(pt.x)}, SE=${formatNumber(pt.y)}`

      const circle = svgEl("circle", {
        cx: px, cy: py, r: 5,
        fill: color,
        part: "study",
        tabindex: "0",
        role: "img",
        "aria-label": ariaLabel
      }, [])
      circle.appendChild(svgEl("title", null, ariaLabel))

      const handler = () => {
        ctx.emit("mj-chart-study-click", {
          series: serie.name,
          x: pt.x,
          y: pt.y,
          label: pt.label
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

      /* Optional point labels. */
      if (showLabels === true && ptLabel !== "") {
        plot.appendChild(svgEl("text", {
          x: px + 7, y: py + 4,
          "font-size": 9, fill: "var(--mj-text-muted, #6b7280)"
        }, escapeHtml(ptLabel)))
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


registerRenderer("funnel-plot", render)
