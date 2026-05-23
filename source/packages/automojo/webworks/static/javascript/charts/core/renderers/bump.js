/*
 * bump.js
 *
 * Bump / rank-over-time renderer.
 *
 * Registered types:
 *   "bump" — rank chart (rank on y-axis, inverted so rank 1 is at top)
 *
 * ctx.attrs recognised:
 *   (none beyond the standard ctx fields)
 *
 * Series data: series[].points [{x, y}] where y is an integer rank (1 = best).
 * x values are years, quarters, or any ordered category.
 *
 * The rank axis is inverted (rank 1 at top). Series are drawn as smooth
 * S-curves between rank dots at each time position.
 * End-of-line labels are nudged apart to avoid overlap when two series
 * share the same final rank.
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, formatNumber, smoothPath } from "../svgdraw.js";
import { linearScale, pointScale, niceTicks } from "../scales.js";


function _getXY(ser, categories) {
  /*
   * Flatten a series to [{x (string), y (number)}].
   */
  const xy = []
  if (ser.points !== undefined && ser.points !== null && ser.points.length > 0) {
    for (let p = 0; p < ser.points.length; p = p + 1) {
      const pt = ser.points[p]
      xy.push({ x: String(pt.x), y: typeof pt.y === "number" ? pt.y : null })
    }
  } else if (ser.values !== undefined && ser.values !== null) {
    for (let v = 0; v < ser.values.length; v = v + 1) {
      const cat = categories[v] !== undefined ? String(categories[v]) : String(v)
      xy.push({ x: cat, y: typeof ser.values[v] === "number" ? ser.values[v] : null })
    }
  }
  return xy
}


function _bumpPath(p1, p2) {
  /*
   * Build a horizontal-monotone cubic Bezier (S-curve) from pixel point p1 to p2.
   * Control points are horizontally displaced by half the x distance, keeping
   * y tangents vertical — the classic bump-chart connector.
   *
   * :param p1: {x, y} start pixel point.
   * :param p2: {x, y} end pixel point.
   * :returns: Partial SVG path data string (no leading M).
   */
  const cx = (p2.x - p1.x) / 2
  const data = `C${(p1.x + cx).toFixed(2)},${p1.y.toFixed(2)} ` +
    `${(p2.x - cx).toFixed(2)},${p2.y.toFixed(2)} ` +
    `${p2.x.toFixed(2)},${p2.y.toFixed(2)}`
  return data
}


function _nudgeLabels(labelInfos, minGap) {
  /*
   * Simple greedy nudge to separate overlapping end labels on the y-axis.
   *
   * :param labelInfos: Array of {y, label, seriesName} sorted by y.
   * :param minGap: Minimum pixel gap between label centres.
   * :returns: Array of {y, label, seriesName} with y adjusted.
   */
  const sorted = labelInfos.slice().sort((a, b) => a.y - b.y)
  for (let i = 1; i < sorted.length; i = i + 1) {
    const prev = sorted[i - 1]
    const curr = sorted[i]
    if (curr.y - prev.y < minGap) {
      curr.y = prev.y + minGap
    }
  }
  return sorted
}


export function render(ctx) {
  /*
   * Render a bump (rank-over-time) chart.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const model = ctx.model
  const root = svgEl("g", { part: "plot" }, [])

  if (model.series.length === 0) {
    return root
  }

  /* Normalise all series. */
  const normSeries = []
  for (let s = 0; s < model.series.length; s = s + 1) {
    normSeries.push({
      name: model.series[s].name,
      xy: _getXY(model.series[s], model.categories)
    })
  }

  /* Collect ordered x labels. */
  const xLabelSet = []
  const xLabelSeen = {}
  for (let s = 0; s < normSeries.length; s = s + 1) {
    for (let p = 0; p < normSeries[s].xy.length; p = p + 1) {
      const label = normSeries[s].xy[p].x
      if (xLabelSeen[label] !== true) {
        xLabelSet.push(label)
        xLabelSeen[label] = true
      }
    }
  }

  if (xLabelSet.length === 0) {
    return root
  }

  /* Find the rank range across all series. */
  let rankMin = Infinity
  let rankMax = -Infinity
  for (let s = 0; s < normSeries.length; s = s + 1) {
    for (let p = 0; p < normSeries[s].xy.length; p = p + 1) {
      const y = normSeries[s].xy[p].y
      if (y === null) {
        continue
      }
      if (y < rankMin) {
        rankMin = y
      }
      if (y > rankMax) {
        rankMax = y
      }
    }
  }
  if (rankMin === Infinity) {
    return root
  }

  /* Invert the y domain so rank 1 appears at the top. */
  const yDomainLow = rankMin
  const yDomainHigh = rankMax

  const labelColW = 100  /* right-side labels */
  const margin = { top: 16, right: labelColW, bottom: 32, left: 40 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 40)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 40)

  /* Invert: map rankMax -> 0 (top), rankMin -> plotH (bottom). */
  const xScale = pointScale(xLabelSet, [0, plotW])
  const yScale = linearScale([yDomainHigh, yDomainLow], [plotH, 0])

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  /* Horizontal gridlines at each integer rank. */
  for (let rank = rankMin; rank <= rankMax; rank = rank + 1) {
    const y = yScale(rank)
    plot.appendChild(svgEl("line", {
      x1: 0, y1: y, x2: plotW, y2: y,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    /* Rank label on the left axis. */
    plot.appendChild(svgEl("text", {
      x: -8, y: y + 4, "text-anchor": "end",
      "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
    }, String(rank)))
  }

  /* X-axis category labels. */
  for (let i = 0; i < xLabelSet.length; i = i + 1) {
    const label = xLabelSet[i]
    const x = xScale(label)
    plot.appendChild(svgEl("text", {
      x: x, y: plotH + 16, "text-anchor": "middle",
      "font-size": 11, fill: "var(--mj-text, #14181f)"
    }, escapeHtml(label)))
  }

  /* Axis baseline. */
  plot.appendChild(svgEl("line", {
    x1: 0, y1: plotH, x2: plotW, y2: plotH,
    stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
  }, []))

  /* Collect end-label positions for collision avoidance. */
  const endLabels = []

  /* Draw each series. */
  for (let s = 0; s < normSeries.length; s = s + 1) {
    const ser = normSeries[s]
    const color = ctx.colorFor(ser.name)
    const seriesGroup = svgEl("g", { part: "series" }, [])

    /* Build pixel points; skip null ranks. */
    const pixelPts = []
    for (let p = 0; p < ser.xy.length; p = p + 1) {
      const pt = ser.xy[p]
      if (pt.y === null) {
        pixelPts.push(null)
        continue
      }
      pixelPts.push({
        x: xScale(pt.x), y: yScale(pt.y),
        xLabel: pt.x, yVal: pt.y
      })
    }

    /* Draw S-curve segments between consecutive non-null pixel points. */
    const validSegs = pixelPts.filter((pt) => pt !== null)
    if (validSegs.length >= 2) {
      let pathData = `M${validSegs[0].x.toFixed(2)},${validSegs[0].y.toFixed(2)}`
      for (let p = 1; p < validSegs.length; p = p + 1) {
        pathData = pathData + " " + _bumpPath(validSegs[p - 1], validSegs[p])
      }
      const pathEl = svgEl("path", {
        d: pathData,
        fill: "none",
        stroke: color,
        "stroke-width": 2.5,
        "stroke-linecap": "round"
      }, [])
      seriesGroup.appendChild(pathEl)
    } else if (validSegs.length === 1) {
      /* Single point: still draw a dot. */
    }

    /* Draw rank dots and interactive hit targets. */
    for (let p = 0; p < pixelPts.length; p = p + 1) {
      const pt = pixelPts[p]
      if (pt === null) {
        continue
      }

      const dot = svgEl("circle", {
        cx: pt.x.toFixed(2), cy: pt.y.toFixed(2), r: 5,
        fill: color,
        stroke: "var(--mj-surface, #fff)",
        "stroke-width": 1.5
      }, [])
      seriesGroup.appendChild(dot)

      const hit = svgEl("circle", {
        cx: pt.x.toFixed(2), cy: pt.y.toFixed(2), r: 8,
        fill: "transparent",
        tabindex: "0",
        role: "img",
        "aria-label": `${escapeHtml(ser.name)}, ${escapeHtml(pt.xLabel)}: rank ${pt.yVal}`
      }, [])
      hit.appendChild(svgEl("title", null,
        `${ser.name} - ${pt.xLabel}: rank ${pt.yVal}`))
      const handler = (() => {
        const capturedSeries = ser.name
        const capturedX = pt.xLabel
        const capturedY = pt.yVal
        return () => {
          ctx.emit("mj-chart-bump-click", {
            series: capturedSeries, x: capturedX, rank: capturedY
          })
        }
      })()
      hit.addEventListener("click", handler)
      hit.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault()
          handler()
        }
      })
      seriesGroup.appendChild(hit)
    }

    /* Collect the last valid point for end labelling. */
    const lastPt = validSegs.length > 0 ? validSegs[validSegs.length - 1] : null
    if (lastPt !== null) {
      endLabels.push({ y: lastPt.y, label: ser.name, color: color })
    }

    plot.appendChild(seriesGroup)
  }

  /* Draw end-of-line labels with nudge to avoid overlap. */
  const nudged = _nudgeLabels(endLabels, 14)
  for (let i = 0; i < nudged.length; i = i + 1) {
    const item = nudged[i]
    plot.appendChild(svgEl("text", {
      x: plotW + 8,
      y: item.y + 4,
      "font-size": 11,
      fill: item.color
    }, escapeHtml(item.label)))
  }

  return root
}


registerRenderer("bump", render)
