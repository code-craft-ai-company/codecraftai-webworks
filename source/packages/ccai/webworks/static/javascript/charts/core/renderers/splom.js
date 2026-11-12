/*
 * splom.js
 *
 * Scatterplot Matrix (Pair Plot / SPLOM) renderer.
 *
 * Registered chart types:
 *   "splom" — N×N grid of scatter sub-plots for all variable pairs
 *
 * Data shape:
 *   variables           ordered numeric field names; when omitted, the
 *                       numeric fields of the first point are used
 *   series[]            each series is a group (e.g. species)
 *     .name             group label
 *     .points[]         records { var1, var2, ... }; non-finite values skipped
 *
 * Behaviour:
 *   - One linear scale per variable, shared along its row and column.
 *   - Tick labels run along the outer left and bottom edges for every row
 *     and column, whichever cells are drawn.
 *   - diagonal: "label" (default: the variable name) | "histogram" |
 *     "density" (a KDE curve per series)
 *   - triangle: "full" (default) | "lower" | "upper"; with a half matrix the
 *     other half shows Pearson's r of each pair (all groups pooled).
 *   - Colour and shape vary by series; every point is focusable (one tab
 *     stop with arrow-key movement, provided by the controller).
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber, linePath } from "../svgdraw.js";
import { linearScale, niceTicks } from "../scales.js";
import {
  isFiniteNumber, sortNumbers, silvermanBandwidth, gaussianDensity, linspace, binEdges,
  countBins, axisLayer, fitText, activateOnKey, focusableMark, TEXT_COLOR, MUTED_TEXT_COLOR,
  GRID_COLOR
} from "./diststats.js";

/* Per-series shapes so groups are distinguishable without colour alone. */
const SHAPES = ["circle", "square", "triangle", "diamond"];


function _miniPoint(shape, cx, cy, r) {
  /*
   * A small mark of the given shape.
   */
  if (shape === "square") {
    const half = r * 0.8
    return svgEl("rect", { x: cx - half, y: cy - half, width: half * 2, height: half * 2 }, [])
  }
  if (shape === "triangle") {
    const h = r * 1.5
    const w = r * 1.3
    const points = `${cx.toFixed(2)},${(cy - h * 0.6).toFixed(2)} ` +
      `${(cx - w / 2).toFixed(2)},${(cy + h * 0.4).toFixed(2)} ` +
      `${(cx + w / 2).toFixed(2)},${(cy + h * 0.4).toFixed(2)}`
    return svgEl("polygon", { points: points }, [])
  }
  if (shape === "diamond") {
    const points = `${cx.toFixed(2)},${(cy - r).toFixed(2)} ${(cx + r).toFixed(2)},${cy.toFixed(2)} ` +
      `${cx.toFixed(2)},${(cy + r).toFixed(2)} ${(cx - r).toFixed(2)},${cy.toFixed(2)}`
    return svgEl("polygon", { points: points }, [])
  }
  return svgEl("circle", { cx: cx, cy: cy, r: r }, [])
}


export function splomVariables(raw, series) {
  /*
   * The variables of the matrix: raw.variables, else the numeric fields
   * of the first point found.
   */
  if (raw !== null && raw !== undefined && Array.isArray(raw.variables) === true) {
    return raw.variables.map((name) => String(name))
  }
  for (let si = 0; si < series.length; si = si + 1) {
    const points = Array.isArray(series[si].points) === true ? series[si].points : []
    for (let pi = 0; pi < points.length; pi = pi + 1) {
      const point = points[pi]
      if (point !== null && typeof point === "object") {
        return Object.keys(point).filter((key) => isFiniteNumber(point[key]) === true)
      }
    }
  }
  return []
}


function _pearson(pairs) {
  /*
   * Pearson's correlation coefficient of [x, y] pairs, or null.
   */
  const n = pairs.length
  if (n < 3) {
    return null
  }
  let sx = 0
  let sy = 0
  for (let index = 0; index < n; index = index + 1) {
    sx = sx + pairs[index][0]
    sy = sy + pairs[index][1]
  }
  const mx = sx / n
  const my = sy / n
  let sxx = 0
  let syy = 0
  let sxy = 0
  for (let index = 0; index < n; index = index + 1) {
    const dx = pairs[index][0] - mx
    const dy = pairs[index][1] - my
    sxx = sxx + dx * dx
    syy = syy + dy * dy
    sxy = sxy + dx * dy
  }
  if (sxx === 0 || syy === 0) {
    return null
  }
  return sxy / Math.sqrt(sxx * syy)
}


function _drawDiagonal(group, mode, variable, scale, cellW, cellH, valuesBySeries, ctx, series) {
  /*
   * The diagonal cell: the variable name, plus a histogram (all groups
   * pooled) or one density curve per series.
   */
  if (mode === "histogram") {
    const pooled = []
    for (let si = 0; si < valuesBySeries.length; si = si + 1) {
      for (let vi = 0; vi < valuesBySeries[si].length; vi = vi + 1) {
        pooled.push(valuesBySeries[si][vi])
      }
    }
    const bins = countBins(pooled, binEdges(pooled, { count: 8 }))
    let maxCount = 1
    for (let bi = 0; bi < bins.length; bi = bi + 1) {
      maxCount = Math.max(maxCount, bins[bi].count)
    }
    for (let bi = 0; bi < bins.length; bi = bi + 1) {
      const x0 = scale(bins[bi].x0)
      const x1 = scale(bins[bi].x1)
      const height = (bins[bi].count / maxCount) * cellH * 0.7
      group.appendChild(svgEl("rect", {
        x: Math.min(x0, x1) + 0.5, y: cellH - height, width: Math.max(Math.abs(x1 - x0) - 1, 1),
        height: height, fill: MUTED_TEXT_COLOR, "fill-opacity": 0.35
      }, []))
    }
  } else if (mode === "density") {
    let peak = 0
    const curves = []
    for (let si = 0; si < valuesBySeries.length; si = si + 1) {
      const sorted = sortNumbers(valuesBySeries[si])
      if (sorted.length === 0) {
        curves.push(null)
        continue
      }
      const xs = linspace(scale.domain()[0], scale.domain()[1], 60)
      const ys = gaussianDensity(sorted, silvermanBandwidth(sorted), xs)
      for (let index = 0; index < ys.length; index = index + 1) {
        peak = Math.max(peak, ys[index])
      }
      curves.push({ xs: xs, ys: ys })
    }
    for (let si = 0; si < curves.length; si = si + 1) {
      if (curves[si] === null || peak <= 0) {
        continue
      }
      const curve = curves[si]
      const points = curve.xs.map((x, index) => ({ x: scale(x), y: cellH - (curve.ys[index] / peak) * cellH * 0.7 }))
      group.appendChild(svgEl("path", {
        d: linePath(points), fill: "none", stroke: ctx.colorFor(series[si].name), "stroke-width": 1.5
      }, []))
    }
  }
  group.appendChild(svgEl("text", {
    x: cellW / 2, y: mode === "label" ? cellH / 2 + 4 : 12, "text-anchor": "middle",
    "font-size": Math.max(9, Math.min(13, cellW * 0.12)), "font-weight": 600, fill: TEXT_COLOR
  }, fitText(variable, cellW - 4, Math.max(9, Math.min(13, cellW * 0.12)))))
  return
}


export function render(ctx) {
  /*
   * Render a scatterplot matrix.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const model = ctx.model
  const series = Array.isArray(model.series) === true ? model.series : []
  const variables = splomVariables(ctx.raw, series)
  const root = svgEl("g", { part: "plot" }, [])
  if (series.length === 0 || variables.length < 2) {
    return root
  }

  const diagonalAttr = ctx.attrs("diagonal", "label")
  const diagonal = diagonalAttr === "histogram" || diagonalAttr === "density" ? diagonalAttr : "label"
  const triangleMode = ctx.attrs("triangle", "full")
  const n = variables.length

  const margin = { top: 8, right: 8, bottom: 30, left: 44 }
  const totalW = Math.max(ctx.width - margin.left - margin.right, 10)
  const totalH = Math.max(ctx.height - margin.top - margin.bottom, 10)
  const cellW = totalW / n
  const cellH = totalH / n
  const innerPad = Math.min(4, cellW * 0.08, cellH * 0.08)
  const plotW = Math.max(cellW - innerPad * 2, 2)
  const plotH = Math.max(cellH - innerPad * 2, 2)

  /* One domain per variable over every series. */
  const domains = []
  const valuesBy = []
  for (let vi = 0; vi < n; vi = vi + 1) {
    const perSeries = []
    let low = Infinity
    let high = -Infinity
    for (let si = 0; si < series.length; si = si + 1) {
      const points = Array.isArray(series[si].points) === true ? series[si].points : []
      const values = []
      for (let pi = 0; pi < points.length; pi = pi + 1) {
        const point = points[pi]
        const value = point !== null && typeof point === "object" ? point[variables[vi]] : null
        if (isFiniteNumber(value) === true) {
          values.push(value)
          low = Math.min(low, value)
          high = Math.max(high, value)
        }
      }
      perSeries.push(values)
    }
    if (low === Infinity) {
      low = 0
      high = 1
    }
    const pad = (high - low) * 0.08 || Math.max(Math.abs(low) * 0.1, 0.5)
    domains.push([low - pad, high + pad])
    valuesBy.push(perSeries)
  }

  const outer = svgEl("g", { transform: `translate(${margin.left},${margin.top})` }, [])
  root.appendChild(outer)
  const axes = axisLayer(outer)
  const marks = svgEl("g", { part: "marks" }, [])
  outer.appendChild(marks)

  /* Outer ticks: y along the left edge per row, x along the bottom per column. */
  const tickFont = 8
  for (let vi = 0; vi < n; vi = vi + 1) {
    const yScale = linearScale(domains[vi], [vi * cellH + innerPad + plotH, vi * cellH + innerPad])
    const yTicks = niceTicks(domains[vi][0], domains[vi][1], cellH > 90 ? 3 : 2)
    for (let ti = 0; ti < yTicks.length; ti = ti + 1) {
      axes.appendChild(svgEl("text", {
        x: -4, y: yScale(yTicks[ti]) + 3, "text-anchor": "end", "font-size": tickFont, fill: MUTED_TEXT_COLOR
      }, formatNumber(yTicks[ti])))
    }
    const xScale = linearScale(domains[vi], [vi * cellW + innerPad, vi * cellW + innerPad + plotW])
    const xTicks = niceTicks(domains[vi][0], domains[vi][1], cellW > 110 ? 3 : 2)
    for (let ti = 0; ti < xTicks.length; ti = ti + 1) {
      axes.appendChild(svgEl("text", {
        x: xScale(xTicks[ti]), y: n * cellH + 11, "text-anchor": "middle", "font-size": tickFont, fill: MUTED_TEXT_COLOR
      }, formatNumber(xTicks[ti])))
    }
    if (diagonal !== "label") {
      axes.appendChild(svgEl("text", {
        x: vi * cellW + cellW / 2, y: n * cellH + 24, "text-anchor": "middle", "font-size": 9, fill: MUTED_TEXT_COLOR
      }, fitText(variables[vi], cellW - 4, 9)))
    }
  }

  const rows = []
  for (let row = 0; row < n; row = row + 1) {
    const yVar = variables[row]
    const yScale = linearScale(domains[row], [plotH, 0])
    for (let col = 0; col < n; col = col + 1) {
      const xVar = variables[col]
      const xScale = linearScale(domains[col], [0, plotW])
      const hidden = (triangleMode === "lower" && col > row) || (triangleMode === "upper" && col < row)
      const cell = svgEl("g", { transform: `translate(${col * cellW},${row * cellH})` }, [])
      const inner = svgEl("g", { transform: `translate(${innerPad},${innerPad})` }, [])

      if (row === col) {
        axes.appendChild(svgEl("rect", {
          x: col * cellW, y: row * cellH, width: cellW, height: cellH,
          fill: "var(--mj-bg-subtle, #f6f7f9)", stroke: GRID_COLOR, "stroke-width": 0.5
        }, []))
        const diagonalGroup = svgEl("g", {
          transform: `translate(${col * cellW + innerPad},${row * cellH + innerPad})`
        }, [])
        _drawDiagonal(diagonalGroup, diagonal, yVar, xScale, plotW, plotH, valuesBy[row], ctx, series)
        axes.appendChild(diagonalGroup)
        continue
      }

      axes.appendChild(svgEl("rect", {
        x: col * cellW + innerPad, y: row * cellH + innerPad, width: plotW, height: plotH,
        fill: "none", stroke: GRID_COLOR, "stroke-width": 0.5
      }, []))

      if (hidden === true) {
        /* The suppressed half shows the correlation of the pair. */
        const pairs = []
        for (let si = 0; si < series.length; si = si + 1) {
          const points = Array.isArray(series[si].points) === true ? series[si].points : []
          for (let pi = 0; pi < points.length; pi = pi + 1) {
            const point = points[pi]
            if (point !== null && typeof point === "object" &&
                isFiniteNumber(point[xVar]) === true && isFiniteNumber(point[yVar]) === true) {
              pairs.push([point[xVar], point[yVar]])
            }
          }
        }
        const r = _pearson(pairs)
        const text = r === null ? "r = –" : `r = ${formatNumber(r, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
        marks.appendChild(svgEl("text", {
          x: col * cellW + cellW / 2, y: row * cellH + cellH / 2 + 4, "text-anchor": "middle",
          "font-size": Math.max(9, Math.min(13, cellW * 0.11)), fill: TEXT_COLOR, part: "correlation",
          "aria-label": `Correlation of ${xVar} and ${yVar}: ${text}`
        }, text))
        continue
      }

      for (let si = 0; si < series.length; si = si + 1) {
        const entry = series[si]
        const points = Array.isArray(entry.points) === true ? entry.points : []
        const color = ctx.colorFor(entry.name)
        const shape = SHAPES[si % SHAPES.length]
        for (let pi = 0; pi < points.length; pi = pi + 1) {
          const point = points[pi]
          if (point === null || typeof point !== "object") {
            continue
          }
          const xValue = point[xVar]
          const yValue = point[yVar]
          if (isFiniteNumber(xValue) === false || isFiniteNumber(yValue) === false) {
            continue
          }
          const mark = _miniPoint(shape, xScale(xValue), yScale(yValue), Math.min(3, plotW / 20 + 1))
          mark.setAttribute("fill", color)
          mark.setAttribute("fill-opacity", "0.7")
          mark.setAttribute("stroke", color)
          mark.setAttribute("stroke-width", "0.5")
          mark.setAttribute("part", "point")
          focusableMark(mark, `${entry.name}: ${xVar} ${formatNumber(xValue)}, ${yVar} ${formatNumber(yValue)}`)
          activateOnKey(mark, () => {
            ctx.emit("mj-chart-point-click", { series: entry.name, xVar: xVar, yVar: yVar, x: xValue, y: yValue })
          })
          inner.appendChild(mark)
        }
      }
      cell.appendChild(inner)
      marks.appendChild(cell)
    }
  }

  for (let si = 0; si < series.length; si = si + 1) {
    const points = Array.isArray(series[si].points) === true ? series[si].points : []
    for (let pi = 0; pi < points.length; pi = pi + 1) {
      const point = points[pi]
      if (point === null || typeof point !== "object") {
        continue
      }
      rows.push([series[si].name].concat(variables.map((name) => isFiniteNumber(point[name]) === true ? point[name] : "")))
    }
  }
  ctx.setTable({ columns: ["Series"].concat(variables), rows: rows, caption: "Observations" })
  return root
}


function _isEmpty(model) {
  /*
   * True when there are fewer than two variables or no point.
   */
  const series = Array.isArray(model.allSeries) === true ? model.allSeries : []
  const variables = splomVariables(model.source, series)
  let points = 0
  for (let si = 0; si < series.length; si = si + 1) {
    points = points + (Array.isArray(series[si].points) === true ? series[si].points.length : 0)
  }
  return variables.length < 2 || points === 0
}


registerRenderer("splom", render, { isEmpty: _isEmpty })
