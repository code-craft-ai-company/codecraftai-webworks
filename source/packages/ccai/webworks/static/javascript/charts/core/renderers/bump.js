/*
 * bump.js
 *
 * Bump / rank-over-time renderer.
 *
 * Registered types:
 *   "bump" — rank chart (rank on y-axis, inverted so rank 1 is at top)
 *
 * ctx.attrs recognised:
 *   x-scale   "category" (default) | "auto" | "time" | "linear" (line.js
 *             rules). Ranks are per period, so every x value gets its own
 *             evenly spaced slot by default -- "2020", "2021" are seasons,
 *             not instants on a time axis; set x-scale="auto" or "time" for
 *             a proportional time axis.
 *
 * Series data: series[].points [{x, y}] or series[].values [] where y is a
 * rank (1 = best). x values are years, quarters, dates or any ordered
 * category.
 *
 * Integer ranks spanning at most 30 places use an inverted axis with one
 * gridline per rank (rank 1 at the top). Any other y data (raw values,
 * fractions, wide ranges) uses a normal value axis with nice ticks. Series
 * are drawn as S-curves between their dots; a null rank (not ranked in that
 * period) breaks the line. Series that share a rank in a period have their
 * dots set slightly apart so each stays visible and clickable. Each series
 * is labelled next to its own last point, in the text colour with a leader
 * in the series colour; labels are nudged apart within the plot.
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber } from "../svgdraw.js";
import { niceTicks } from "../scales.js";
import { LABEL_FONT_SIZE, textWidth, truncateText, nudgeLabels } from "./bar.js";
import { trendSeries, trendFrame, sortedPixels, pointTargets } from "./line.js";

/* The most rank places that still get one gridline each. */
const RANK_GRID_LIMIT = 30;

/* Horizontal distance between the dots of tied series (px). */
const TIE_SPREAD = 7;

const LABEL_GAP = 14;


function _bumpSegment(p1, p2) {
  /*
   * A horizontal-tangent cubic Bezier (S-curve) from p1 to p2, without the
   * leading move.
   */
  const half = (p2.x - p1.x) / 2
  const data = `C${(p1.x + half).toFixed(2)},${p1.y.toFixed(2)} ` +
    `${(p2.x - half).toFixed(2)},${p2.y.toFixed(2)} ` +
    `${p2.x.toFixed(2)},${p2.y.toFixed(2)}`
  return data
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

  const list = trendSeries(model)
  let low = Infinity
  let high = -Infinity
  let integers = true
  for (let s = 0; s < list.length; s = s + 1) {
    for (let p = 0; p < list[s].points.length; p = p + 1) {
      const value = list[s].points[p].y
      if (value === null) {
        continue
      }
      low = Math.min(low, value)
      high = Math.max(high, value)
      integers = integers === true && Number.isInteger(value) === true
    }
  }
  if (low === Infinity) {
    return root
  }

  const ranked = integers === true && high - low <= RANK_GRID_LIMIT
  let frameOptions = null
  if (ranked === true) {
    const ranks = []
    for (let rank = low; rank <= high; rank = rank + 1) {
      ranks.push(rank)
    }
    frameOptions = {
      yDomain: [low - 0.5, high + 0.5], nice: false, invert: true,
      yTicks: ranks, yFormat: (value) => String(value)
    }
  } else {
    const span = high === low ? [low - 1, high + 1] : [low, high]
    frameOptions = { yDomain: span, yTicks: niceTicks(span[0], span[1], 5) }
  }

  /* The label column is as wide as the longest name (capped). */
  let labelWidth = 0
  for (let s = 0; s < list.length; s = s + 1) {
    labelWidth = Math.max(labelWidth, textWidth(list[s].name))
  }
  const labelColumn = Math.ceil(Math.min(labelWidth, ctx.width * 0.3) + 18)
  frameOptions.rightExtra = labelColumn
  frameOptions.xScale = "category"
  const frame = trendFrame(ctx, list, model, frameOptions)
  root.appendChild(frame.plot)

  /* Place every point; spread tied dots apart. */
  const placed = list.map((series) => sortedPixels(series, frame))
  const ties = new Map()
  for (let s = 0; s < placed.length; s = s + 1) {
    for (let p = 0; p < placed[s].length; p = p + 1) {
      const pixel = placed[s][p]
      pixel.baseX = pixel.x
      if (pixel.y === null) {
        continue
      }
      const key = `${pixel.x.toFixed(1)}|${pixel.value}`
      if (ties.has(key) === false) {
        ties.set(key, [])
      }
      ties.get(key).push(pixel)
    }
  }
  for (const group of ties.values()) {
    if (group.length < 2) {
      continue
    }
    for (let index = 0; index < group.length; index = index + 1) {
      group[index].x = group[index].x + (index - (group.length - 1) / 2) * TIE_SPREAD
    }
  }

  const lines = svgEl("g", { part: "lines" }, [])
  const dots = svgEl("g", { part: "dots" }, [])
  const labels = svgEl("g", { part: "labels", "aria-hidden": "true" }, [])
  frame.marks.appendChild(lines)
  frame.marks.appendChild(dots)
  frame.marks.appendChild(labels)

  const endLabels = []
  for (let s = 0; s < list.length; s = s + 1) {
    const name = list[s].name
    const color = ctx.colorFor(name)
    const pixels = placed[s]

    /* One sub-path per run of ranked periods. */
    let data = ""
    let previous = null
    for (let p = 0; p < pixels.length; p = p + 1) {
      const pixel = pixels[p]
      if (pixel.y === null) {
        previous = null
        continue
      }
      if (previous === null) {
        data = data + `M${pixel.x.toFixed(2)},${pixel.y.toFixed(2)} `
      } else {
        data = data + _bumpSegment(previous, pixel) + " "
      }
      previous = pixel
    }
    if (data !== "") {
      lines.appendChild(svgEl("path", {
        d: data.trim(), fill: "none", stroke: color,
        "stroke-width": 2.5, "stroke-linecap": "round", part: "bump-line", "data-series": name
      }, []))
    }

    const targets = []
    for (let p = 0; p < pixels.length; p = p + 1) {
      const pixel = pixels[p]
      if (pixel.y === null) {
        continue
      }
      dots.appendChild(svgEl("circle", {
        cx: pixel.x.toFixed(2), cy: pixel.y.toFixed(2), r: 5,
        fill: color, stroke: "var(--mj-surface, #fff)", "stroke-width": 1.5, part: "dot"
      }, []))
      const xLabel = frame.x.labelOf(pixel.point)
      const valueText = ranked === true ? `rank ${pixel.value}` : formatNumber(pixel.value)
      targets.push({
        x: pixel.x, y: pixel.y,
        label: `${name}, ${xLabel}: ${valueText}`,
        detail: { series: name, x: pixel.point.raw !== null ? pixel.point.raw : xLabel, rank: pixel.value }
      })
    }
    pointTargets(dots, targets, { ctx: ctx, eventName: "mj-chart-bump-click", width: frame.plotW, radius: 8 })

    const known = pixels.filter((pixel) => pixel.y !== null)
    if (known.length > 0) {
      const last = known[known.length - 1]
      endLabels.push({ x: last.x, baseX: last.baseX, y: last.y, anchorY: last.y, name: name, color: color })
    }
  }

  /* Labels next to each series' own last point, nudged per column. */
  const columns = new Map()
  for (let index = 0; index < endLabels.length; index = index + 1) {
    const key = endLabels[index].baseX.toFixed(0)
    if (columns.has(key) === false) {
      columns.set(key, [])
    }
    columns.get(key).push(endLabels[index])
  }
  for (const column of columns.values()) {
    nudgeLabels(column, LABEL_GAP, 4, frame.plotH - 4)
    const labelX = Math.max(...column.map((item) => item.x)) + 12
    for (let index = 0; index < column.length; index = index + 1) {
      const item = column[index]
      const room = frame.plotW + frame.margin.right - labelX - 4
      if (Math.abs(item.y - item.anchorY) > 2) {
        labels.appendChild(svgEl("line", {
          x1: (item.x + 6).toFixed(2), y1: item.anchorY.toFixed(2),
          x2: (labelX - 2).toFixed(2), y2: item.y.toFixed(2),
          stroke: item.color, "stroke-width": 1.5
        }, []))
      } else {
        labels.appendChild(svgEl("line", {
          x1: (item.x + 6).toFixed(2), y1: item.y.toFixed(2),
          x2: (labelX - 2).toFixed(2), y2: item.y.toFixed(2),
          stroke: item.color, "stroke-width": 2
        }, []))
      }
      labels.appendChild(svgEl("text", {
        x: labelX.toFixed(2), y: (item.y + 4).toFixed(2),
        "font-size": LABEL_FONT_SIZE, fill: "var(--mj-text, #14181f)"
      }, truncateText(item.name, Math.max(room, 24))))
    }
  }

  return root
}


registerRenderer("bump", render)
