/*
 * control.js
 *
 * Control chart / run chart renderer.
 *
 * Registers: "control-chart", "run-chart"
 *
 * JSON shape (ctx.raw):
 *   series: [{ name, points: [{ x, y, ooc? }] }]
 *   control_limits: { ucl, lcl, cl }   -- optional, omit for run charts
 *   reference_lines: [{ label, value }] -- optional horizontal annotations
 *
 *   ooc: true on a point flags it as out-of-control → colored danger red
 *
 * Orientation: vertical only (time/sequence on x, value on y).
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber, linePath } from "../svgdraw.js";
import { linearScale, niceTicks } from "../scales.js";


export function render(ctx) {
  /*
   * Render a control chart or run chart.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const raw = ctx.raw

  const root = svgEl("g", { part: "plot" }, [])

  if (raw === null || raw === undefined) {
    return root
  }

  const series = Array.isArray(raw.series) ? raw.series : []
  const limits = (raw.control_limits !== null && raw.control_limits !== undefined)
    ? raw.control_limits
    : null
  const refLines = Array.isArray(raw.reference_lines) ? raw.reference_lines : []

  if (series.length === 0) {
    return root
  }

  /* Collect all x and y values to determine domain. */
  const allX = []
  const allY = []
  for (let s = 0; s < series.length; s = s + 1) {
    const points = Array.isArray(series[s].points) ? series[s].points : []
    for (let p = 0; p < points.length; p = p + 1) {
      allX.push(Number(points[p].x))
      allY.push(Number(points[p].y))
    }
  }

  if (allX.length === 0) {
    return root
  }

  let xMin = Math.min(...allX)
  let xMax = Math.max(...allX)
  let yMin = Math.min(...allY)
  let yMax = Math.max(...allY)

  /* Expand y domain to contain control limits and reference lines. */
  if (limits !== null) {
    if (limits.ucl !== undefined && limits.ucl > yMax) {
      yMax = limits.ucl
    }
    if (limits.lcl !== undefined && limits.lcl < yMin) {
      yMin = limits.lcl
    }
  }
  for (let r = 0; r < refLines.length; r = r + 1) {
    const rv = Number(refLines[r].value)
    if (rv < yMin) {
      yMin = rv
    }
    if (rv > yMax) {
      yMax = rv
    }
  }

  if (xMin === xMax) {
    xMin = xMin - 1
    xMax = xMax + 1
  }
  if (yMin === yMax) {
    yMin = yMin - 1
    yMax = yMax + 1
  }

  const margin = { top: 16, right: 16, bottom: 40, left: 64 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  const xScale = linearScale([xMin, xMax], [0, plotW])
  const yScale = linearScale([yMin, yMax], [plotH, 0])

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  /* Y-axis gridlines + tick labels. */
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

  /* Control limits: filled band + UCL / CL / LCL lines. */
  if (limits !== null) {
    if (limits.ucl !== undefined && limits.lcl !== undefined) {
      const yUcl = yScale(limits.ucl)
      const yLcl = yScale(limits.lcl)
      plot.appendChild(svgEl("rect", {
        x: 0, y: yUcl,
        width: plotW, height: Math.max(yLcl - yUcl, 0),
        fill: "var(--mj-color-accent-500, #2563eb)", opacity: 0.06
      }, []))
      plot.appendChild(svgEl("line", {
        x1: 0, y1: yUcl, x2: plotW, y2: yUcl,
        stroke: "var(--mj-color-danger, #b91c1c)", "stroke-width": 1.5,
        "stroke-dasharray": "4 2"
      }, []))
      plot.appendChild(svgEl("text", {
        x: plotW + 4, y: yUcl + 4,
        "font-size": 10, fill: "var(--mj-color-danger, #b91c1c)"
      }, "UCL"))
      plot.appendChild(svgEl("line", {
        x1: 0, y1: yLcl, x2: plotW, y2: yLcl,
        stroke: "var(--mj-color-danger, #b91c1c)", "stroke-width": 1.5,
        "stroke-dasharray": "4 2"
      }, []))
      plot.appendChild(svgEl("text", {
        x: plotW + 4, y: yLcl + 4,
        "font-size": 10, fill: "var(--mj-color-danger, #b91c1c)"
      }, "LCL"))
    }
    if (limits.cl !== undefined) {
      const yCl = yScale(limits.cl)
      plot.appendChild(svgEl("line", {
        x1: 0, y1: yCl, x2: plotW, y2: yCl,
        stroke: "var(--mj-color-accent-500, #2563eb)", "stroke-width": 1.5
      }, []))
      plot.appendChild(svgEl("text", {
        x: plotW + 4, y: yCl + 4,
        "font-size": 10, fill: "var(--mj-color-accent-500, #2563eb)"
      }, "CL"))
    }
  }

  /* Reference lines (run chart median / other annotations). */
  for (let r = 0; r < refLines.length; r = r + 1) {
    const refLine = refLines[r]
    const y = yScale(Number(refLine.value))
    plot.appendChild(svgEl("line", {
      x1: 0, y1: y, x2: plotW, y2: y,
      stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5,
      "stroke-dasharray": "6 3"
    }, []))
    plot.appendChild(svgEl("text", {
      x: 4, y: y - 4,
      "font-size": 10, fill: "var(--mj-text-muted, #6b7280)"
    }, String(refLine.label || "")))
  }

  /* Draw each series: line + dots. */
  for (let s = 0; s < series.length; s = s + 1) {
    const serie = series[s]
    const points = Array.isArray(serie.points) ? serie.points : []
    const color = ctx.colorFor(serie.name)

    /* Build path points for the connecting line. */
    const pathPts = points.map((pt) => {
      return { x: xScale(Number(pt.x)), y: yScale(Number(pt.y)) }
    })
    const pathD = linePath(pathPts)
    if (pathD !== "") {
      plot.appendChild(svgEl("path", {
        d: pathD, fill: "none",
        stroke: color, "stroke-width": 2
      }, []))
    }

    /* Individual point circles. */
    for (let p = 0; p < points.length; p = p + 1) {
      const pt = points[p]
      const px = xScale(Number(pt.x))
      const py = yScale(Number(pt.y))
      const outOfControl = pt.ooc === true
      const dotColor = outOfControl
        ? "var(--mj-color-danger, #b91c1c)"
        : color

      const label = `${serie.name}, x=${formatNumber(pt.x)}: ${formatNumber(pt.y)}` +
        (outOfControl ? " (out of control)" : "")

      const circle = svgEl("circle", {
        cx: px, cy: py, r: 4,
        fill: dotColor,
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
          y: pt.y,
          ooc: outOfControl
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


registerRenderer("control-chart", render)
registerRenderer("run-chart", render)
