/*
 * splom.js
 *
 * Scatterplot Matrix (Pair Plot / SPLOM) renderer.
 *
 * Registered chart types:
 *   "splom" — N×N grid of scatter sub-plots for all variable pairs
 *
 * Data shape:
 *   ctx.raw.variables   ordered list of numeric field names  (required)
 *   model.series[]      each series is a group (e.g. species)
 *     .name             group label
 *     .points[]         each point is a record { var1, var2, ... }
 *
 * Behavior:
 *   - One linear scale per variable (shared across its row / column).
 *   - Diagonal cells show the variable name (or "histogram" / "density" via
 *     ctx.attrs("diagonal")).
 *   - triangle attr controls which off-diagonal cells are drawn:
 *     "full" (default) | "lower" | "upper"
 *   - Axes (tick labels) drawn only on the outer left column (y) and
 *     outer bottom row (x) to avoid repetition.
 *   - Each scatter point is interactive (tabindex / aria / click → emit).
 *   - Color + shape vary by series.
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, formatNumber, extent } from "../svgdraw.js";
import { linearScale, niceTicks } from "../scales.js";


/* Per-series shapes so groups are distinguishable without color alone. */
const SHAPES = ["circle", "square", "triangle", "diamond"]


function _miniPoint(shape, cx, cy, r) {
  /*
   * Build a small mark element for a SPLOM scatter point.
   *
   * :param shape: "circle"|"square"|"triangle"|"diamond"
   * :param cx: Center x in sub-plot coordinates.
   * :param cy: Center y.
   * :param r: Mark radius.
   * :returns: SVGElement.
   */
  if (shape === "square") {
    const half = r * 0.8
    return svgEl("rect", {
      x: cx - half, y: cy - half,
      width: half * 2, height: half * 2
    }, [])
  }
  if (shape === "triangle") {
    const h = r * 1.5
    const w = r * 1.3
    const pts = `${cx},${(cy - h * 0.6).toFixed(2)} ` +
      `${(cx - w / 2).toFixed(2)},${(cy + h * 0.4).toFixed(2)} ` +
      `${(cx + w / 2).toFixed(2)},${(cy + h * 0.4).toFixed(2)}`
    return svgEl("polygon", { points: pts }, [])
  }
  if (shape === "diamond") {
    const d = r
    const pts = `${cx},${cy - d} ${cx + d},${cy} ` +
      `${cx},${cy + d} ${cx - d},${cy}`
    return svgEl("polygon", { points: pts }, [])
  }
  return svgEl("circle", { cx: cx, cy: cy, r: r }, [])
}


function _drawHistDiag(group, varName, xScale, cellW, cellH, allVarPoints) {
  /*
   * Draw a simple histogram on the diagonal cell for the given variable.
   *
   * :param group: SVG group to append into.
   * :param varName: Variable name (for display only, histogram data below).
   * :param xScale: Linear pixel scale for this variable.
   * :param cellW: Cell width in pixels.
   * :param cellH: Cell height in pixels.
   * :param allVarPoints: All numeric values for this variable across all series.
   */
  const binCount = 8
  const lo = xScale.domain()[0]
  const hi = xScale.domain()[1]
  const span = hi - lo || 1
  const binW = span / binCount
  const counts = new Array(binCount).fill(0)

  for (let i = 0; i < allVarPoints.length; i = i + 1) {
    const v = allVarPoints[i]
    const idx = Math.min(binCount - 1, Math.floor((v - lo) / binW))
    if (idx >= 0) {
      counts[idx] = counts[idx] + 1
    }
  }

  const maxCount = Math.max(...counts, 1)
  const barW = cellW / binCount

  for (let b = 0; b < binCount; b = b + 1) {
    const barH = (counts[b] / maxCount) * (cellH * 0.75)
    const bx = b * barW
    const by = cellH - barH
    group.appendChild(svgEl("rect", {
      x: bx + 0.5,
      y: by,
      width: Math.max(barW - 1, 1),
      height: barH,
      fill: "var(--mj-color-accent-300, #80a8ff)",
      opacity: 0.7
    }, []))
  }
}


export function render(ctx) {
  /*
   * Render a scatterplot matrix.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const model = ctx.model
  const rawVars = (ctx.raw !== null && ctx.raw !== undefined)
    ? ctx.raw.variables || null
    : null
  const variables = rawVars !== null ? rawVars : []

  const root = svgEl("g", { part: "plot" }, [])

  const series = model.series
  if (series === null || series === undefined || series.length === 0) {
    return root
  }
  if (variables.length < 2) {
    return root
  }

  const diagonal = ctx.attrs("diagonal", "label")
  const triangleMode = ctx.attrs("triangle", "full")
  const n = variables.length

  /* Leave margins for outer axis labels only. */
  const marginLeft = 52
  const marginTop = 8
  const marginRight = 8
  const marginBottom = 44

  const totalW = Math.max(ctx.width - marginLeft - marginRight, 10)
  const totalH = Math.max(ctx.height - marginTop - marginBottom, 10)

  const cellW = Math.floor(totalW / n)
  const cellH = Math.floor(totalH / n)
  const innerPad = 4   /* padding inside each sub-cell */

  const plotW = cellW - innerPad * 2
  const plotH = cellH - innerPad * 2

  /* Build one linear scale per variable, mapping over ALL series. */
  const varScales = {}
  const varAllValues = {}

  for (let v = 0; v < variables.length; v = v + 1) {
    const varName = variables[v]
    const vals = []
    for (let s = 0; s < series.length; s = s + 1) {
      const pts = series[s].points
      if (pts === null || pts === undefined) {
        continue
      }
      for (let p = 0; p < pts.length; p = p + 1) {
        const val = pts[p][varName]
        if (typeof val === "number" && Number.isNaN(val) === false) {
          vals.push(val)
        }
      }
    }
    varAllValues[varName] = vals
    const dom = extent(vals)
    const pad = (dom[1] - dom[0]) * 0.08 || 0.5
    varScales[varName] = linearScale([dom[0] - pad, dom[1] + pad], [0, plotW])
  }

  const outerGroup = svgEl("g", {
    transform: `translate(${marginLeft},${marginTop})`
  }, [])
  root.appendChild(outerGroup)

  /* Draw N×N grid. */
  for (let row = 0; row < n; row = row + 1) {
    const yVar = variables[row]
    const yScaleX = varScales[yVar]           /* reused as y via flip below */
    /* Flip the x-range scale to a y-range scale for the y axis. */
    const yDom = yScaleX.domain()
    const yScale = linearScale(yDom, [plotH, 0])

    for (let col = 0; col < n; col = col + 1) {
      /* Respect triangle mode. */
      if (triangleMode === "lower" && col > row) {
        continue
      }
      if (triangleMode === "upper" && col < row) {
        continue
      }

      const xVar = variables[col]
      const xScale = linearScale(varScales[xVar].domain(), [0, plotW])

      const cellOriginX = col * cellW
      const cellOriginY = row * cellH

      const cellGroup = svgEl("g", {
        transform: `translate(${cellOriginX},${cellOriginY})`
      }, [])

      /* Cell background. */
      cellGroup.appendChild(svgEl("rect", {
        x: 0, y: 0, width: cellW, height: cellH,
        fill: row === col
          ? "var(--mj-chart-heat-1, #eff6ff)"
          : "var(--mj-surface, #ffffff)",
        stroke: "var(--mj-border, #e0e3e9)",
        "stroke-width": 0.5
      }, []))

      const innerGroup = svgEl("g", {
        transform: `translate(${innerPad},${innerPad})`
      }, [])
      cellGroup.appendChild(innerGroup)

      /* ── Diagonal cell ── */
      if (row === col) {
        if (diagonal === "histogram") {
          _drawHistDiag(innerGroup, yVar, xScale, plotW, plotH, varAllValues[yVar])
        }
        /* Always draw variable name label. */
        innerGroup.appendChild(svgEl("text", {
          x: plotW / 2,
          y: plotH / 2 + (diagonal === "histogram" ? plotH * 0.42 : 4),
          "text-anchor": "middle",
          "font-size": Math.max(9, Math.min(13, plotW * 0.12)),
          "font-weight": "600",
          fill: "var(--mj-text, #14181f)"
        }, escapeHtml(yVar)))
        outerGroup.appendChild(cellGroup)
        continue
      }

      /* ── Outer axis tick labels ── */
      /* Y ticks only on the leftmost column. */
      if (col === 0) {
        const yTicks = niceTicks(yDom[0], yDom[1], 3)
        for (let t = 0; t < yTicks.length; t = t + 1) {
          const tick = yTicks[t]
          const ty = yScale(tick)
          innerGroup.appendChild(svgEl("text", {
            x: -innerPad - 2,
            y: ty + 3,
            "text-anchor": "end",
            "font-size": 8,
            fill: "var(--mj-text-muted, #6b7280)"
          }, formatNumber(tick)))
        }
      }
      /* X ticks only on the bottom row. */
      if (row === n - 1) {
        const xTicks = niceTicks(xScale.domain()[0], xScale.domain()[1], 3)
        for (let t = 0; t < xTicks.length; t = t + 1) {
          const tick = xTicks[t]
          const tx = xScale(tick)
          innerGroup.appendChild(svgEl("text", {
            x: tx,
            y: plotH + innerPad + 10,
            "text-anchor": "middle",
            "font-size": 8,
            fill: "var(--mj-text-muted, #6b7280)"
          }, formatNumber(tick)))
        }
      }

      /* ── Scatter points ── */
      for (let s = 0; s < series.length; s = s + 1) {
        const ser = series[s]
        const pts = ser.points
        if (pts === null || pts === undefined || pts.length === 0) {
          continue
        }
        const color = ctx.colorFor(ser.name)
        const shape = SHAPES[s % SHAPES.length]

        for (let p = 0; p < pts.length; p = p + 1) {
          const pt = pts[p]
          const xVal = pt[xVar]
          const yVal = pt[yVar]
          const validX = typeof xVal === "number" && Number.isNaN(xVal) === false
          const validY = typeof yVal === "number" && Number.isNaN(yVal) === false
          if (validX === false || validY === false) {
            continue
          }

          const px = xScale(xVal)
          const py = yScale(yVal)

          /* Skip out-of-bounds. */
          if (px < -2 || px > plotW + 2 || py < -2 || py > plotH + 2) {
            continue
          }

          const mark = _miniPoint(shape, px, py, 3)
          mark.setAttribute("fill", color)
          mark.setAttribute("fill-opacity", "0.7")
          mark.setAttribute("stroke", color)
          mark.setAttribute("stroke-width", "0.5")
          mark.setAttribute("part", "point")
          mark.setAttribute("tabindex", "0")
          mark.setAttribute("role", "img")
          const ariaLabel = `${escapeHtml(ser.name)}: ${escapeHtml(xVar)}=${formatNumber(xVal)}, ${escapeHtml(yVar)}=${formatNumber(yVal)}`
          mark.setAttribute("aria-label", ariaLabel)
          mark.appendChild(svgEl("title", null,
            `${ser.name} — ${xVar}: ${formatNumber(xVal)}, ${yVar}: ${formatNumber(yVal)}`))

          const ptX = xVal
          const ptY = yVal
          const serName = ser.name
          const handler = () => {
            ctx.emit("mj-chart-point-click", {
              series: serName,
              xVar: xVar,
              yVar: yVar,
              x: ptX,
              y: ptY
            })
          }
          mark.addEventListener("click", handler)
          mark.addEventListener("keydown", (event) => {
            if (event.key === "Enter" || event.key === " ") {
              event.preventDefault()
              handler()
            }
          })
          innerGroup.appendChild(mark)
        }
      }

      /* Sub-plot border. */
      innerGroup.appendChild(svgEl("rect", {
        x: 0, y: 0, width: plotW, height: plotH,
        fill: "none",
        stroke: "var(--mj-border, #e0e3e9)",
        "stroke-width": 0.5
      }, []))

      outerGroup.appendChild(cellGroup)
    }
  }

  /* Outer axis labels (variable names on left/bottom edges). */
  for (let v = 0; v < n; v = v + 1) {
    const varName = variables[v]
    /* Left edge: y-axis variable label per row. */
    outerGroup.appendChild(svgEl("text", {
      x: -marginLeft + 8,
      y: v * cellH + cellH / 2 + 4,
      "text-anchor": "start",
      "font-size": 9,
      fill: "var(--mj-text-muted, #6b7280)"
    }, escapeHtml(varName)))
    /* Bottom edge: x-axis variable label per column. */
    outerGroup.appendChild(svgEl("text", {
      x: v * cellW + cellW / 2,
      y: n * cellH + marginBottom - 4,
      "text-anchor": "middle",
      "font-size": 9,
      fill: "var(--mj-text-muted, #6b7280)"
    }, escapeHtml(varName)))
  }

  return root
}


registerRenderer("splom", render)
