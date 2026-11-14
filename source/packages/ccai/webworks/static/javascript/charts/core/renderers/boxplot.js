/*
 * boxplot.js
 *
 * Box-and-whisker plot renderer.
 *
 * Registers: "boxplot"
 *
 * ctx.model.series data shape:
 *   series[].groups[]:
 *     - { category, samples: [n, …] }   renderer computes the five-number
 *                                       summary (non-finite samples are
 *                                       missing data and ignored)
 *     - { category, min, q1, median, q3, max, outliers?: [n, …], n? }
 *                                       pre-computed; min / max are the
 *                                       whisker ends, `n` enables notches
 *   categories (optional): display order; derived from the groups when
 *   omitted. Several series are drawn side by side within each category.
 *
 * Relevant ctx.attrs:
 *   notched     boolean — notch the box at the median's 95% confidence
 *               interval, median ± 1.57 · IQR / √n (McGill et al. 1978)
 *   iqr-mult    IQR multiplier of the whisker fences (default 1.5)
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber } from "../svgdraw.js";
import { linearScale, bandScale } from "../scales.js";
import {
  summarize, finiteValues, isFiniteNumber, groupCategories, seriesGroups, hasGroupData,
  axisLayer, drawTicks, drawCategoryLabels, tickCount, activateOnKey, focusableMark,
  TEXT_COLOR, fitDomain
} from "./diststats.js";
import { booleanOption } from "../chartoptions.js";


/* ── statistics ──────────────────────────────────────────────────────────── */

export function resolveBoxStats(group, iqrMult) {
  /*
   * The summary of one group, from samples or pre-computed fields.
   *
   * :returns: { count, q1, median, q3, whiskerLow, whiskerHigh, outliers }
   *     or null when the group has neither usable samples nor numeric q1 /
   *     median / q3. `count` is null when unknown.
   */
  if (isFiniteNumber(group.median) === true && isFiniteNumber(group.q1) === true &&
      isFiniteNumber(group.q3) === true) {
    const low = isFiniteNumber(group.min) === true ? group.min : group.q1
    const high = isFiniteNumber(group.max) === true ? group.max : group.q3
    const count = isFiniteNumber(group.n) === true && group.n > 0 ? group.n : null
    return {
      count: count,
      q1: group.q1,
      median: group.median,
      q3: group.q3,
      whiskerLow: low,
      whiskerHigh: high,
      outliers: finiteValues(group.outliers)
    }
  }
  const summary = summarize(group.samples, iqrMult)
  return summary
}


function _notchHalf(stats) {
  /*
   * Half the width of the median's notch interval, in data units, or 0
   * when the sample count is unknown.
   */
  if (stats.count === null || stats.count === undefined || stats.count < 1) {
    return 0
  }
  const half = 1.57 * (stats.q3 - stats.q1) / Math.sqrt(stats.count)
  return half
}


/* ── drawing ─────────────────────────────────────────────────────────────── */

function _boxPath(stats, valScale, bandLow, bandHigh, horizontal, notched) {
  /*
   * Outline of the IQR box; with a notch the sides step INWARD to a
   * quarter of the box width at the median and back out at the limits of
   * the confidence interval (clamped to the box).
   */
  const q1 = valScale(stats.q1)
  const q3 = valScale(stats.q3)
  const half = notched === true ? _notchHalf(stats) : 0
  if (half <= 0) {
    if (horizontal === true) {
      return `M${q1},${bandLow} L${q3},${bandLow} L${q3},${bandHigh} L${q1},${bandHigh} Z`
    }
    return `M${bandLow},${q3} L${bandHigh},${q3} L${bandHigh},${q1} L${bandLow},${q1} Z`
  }

  const indent = (bandHigh - bandLow) * 0.25
  const ciLow = valScale(Math.max(stats.median - half, stats.q1))
  const ciHigh = valScale(Math.min(stats.median + half, stats.q3))
  const median = valScale(stats.median)
  if (horizontal === true) {
    return `M${q1},${bandLow} L${ciLow},${bandLow} L${median},${bandLow + indent} ` +
      `L${ciHigh},${bandLow} L${q3},${bandLow} L${q3},${bandHigh} L${ciHigh},${bandHigh} ` +
      `L${median},${bandHigh - indent} L${ciLow},${bandHigh} L${q1},${bandHigh} Z`
  }
  return `M${bandLow},${q3} L${bandHigh},${q3} L${bandHigh},${ciHigh} ` +
    `L${bandHigh - indent},${median} L${bandHigh},${ciLow} L${bandHigh},${q1} ` +
    `L${bandLow},${q1} L${bandLow},${ciLow} L${bandLow + indent},${median} L${bandLow},${ciHigh} Z`
}


function _segment(group, horizontal, along1, along2, across1, across2, attrs) {
  /*
   * A line from value position along1 to along2 at cross position across1
   * to across2, oriented for the chart.
   */
  const line = horizontal === true
    ? svgEl("line", { x1: along1, y1: across1, x2: along2, y2: across2 })
    : svgEl("line", { x1: across1, y1: along1, x2: across2, y2: along2 })
  const keys = Object.keys(attrs)
  for (let index = 0; index < keys.length; index = index + 1) {
    line.setAttribute(keys[index], String(attrs[keys[index]]))
  }
  group.appendChild(line)
  return
}


function _drawBox(marks, stats, center, boxHalf, valScale, ctx, horizontal, notched, seriesName, category) {
  /*
   * One box-and-whisker glyph plus its focusable hit area.
   */
  const color = ctx.colorFor(seriesName)
  const group = svgEl("g", { part: "box" }, [])
  const bandLow = center - boxHalf
  const bandHigh = center + boxHalf
  const capHalf = boxHalf * 0.5
  const stroke = { stroke: color, "stroke-width": 1.5 }

  /* Whiskers and caps. */
  _segment(group, horizontal, valScale(stats.whiskerLow), valScale(stats.q1), center, center, stroke)
  _segment(group, horizontal, valScale(stats.q3), valScale(stats.whiskerHigh), center, center, stroke)
  _segment(group, horizontal, valScale(stats.whiskerLow), valScale(stats.whiskerLow),
    center - capHalf, center + capHalf, stroke)
  _segment(group, horizontal, valScale(stats.whiskerHigh), valScale(stats.whiskerHigh),
    center - capHalf, center + capHalf, stroke)

  /* IQR box. */
  const isNotched = notched === true && _notchHalf(stats) > 0
  group.appendChild(svgEl("path", {
    d: _boxPath(stats, valScale, bandLow, bandHigh, horizontal, isNotched),
    fill: color, "fill-opacity": 0.3, stroke: color, "stroke-width": 1.5,
    "stroke-linejoin": "round", part: "box-body"
  }, []))

  /* Median. */
  const inset = isNotched === true ? boxHalf * 0.5 : 0
  _segment(group, horizontal, valScale(stats.median), valScale(stats.median),
    bandLow + inset, bandHigh - inset, { stroke: TEXT_COLOR, "stroke-width": 2.5, part: "median" })

  /* Outliers. */
  for (let oi = 0; oi < stats.outliers.length; oi = oi + 1) {
    const position = valScale(stats.outliers[oi])
    group.appendChild(svgEl("circle", {
      cx: horizontal === true ? position : center,
      cy: horizontal === true ? center : position,
      r: 3, fill: "none", stroke: color, "stroke-width": 1.5, part: "outlier"
    }, []))
  }

  /* Hit area over the whole glyph (whiskers and outliers included). */
  let low = Math.min(stats.whiskerLow, stats.q1)
  let high = Math.max(stats.whiskerHigh, stats.q3)
  for (let oi = 0; oi < stats.outliers.length; oi = oi + 1) {
    low = Math.min(low, stats.outliers[oi])
    high = Math.max(high, stats.outliers[oi])
  }
  const p0 = valScale(low)
  const p1 = valScale(high)
  const hit = horizontal === true
    ? svgEl("rect", { x: Math.min(p0, p1) - 4, y: bandLow, width: Math.abs(p1 - p0) + 8, height: boxHalf * 2 })
    : svgEl("rect", { x: bandLow, y: Math.min(p0, p1) - 4, width: boxHalf * 2, height: Math.abs(p1 - p0) + 8 })
  hit.setAttribute("fill", "transparent")
  hit.setAttribute("part", "boxplot-hit")
  const countText = stats.count !== null ? `, n ${formatNumber(stats.count)}` : ""
  const outlierText = stats.outliers.length > 0 ? `, ${stats.outliers.length} outlier(s)` : ""
  focusableMark(hit, `${seriesName}, ${category}: median ${formatNumber(stats.median)}, ` +
    `quartiles ${formatNumber(stats.q1)}–${formatNumber(stats.q3)}, ` +
    `whiskers ${formatNumber(stats.whiskerLow)}–${formatNumber(stats.whiskerHigh)}${outlierText}${countText}`)
  activateOnKey(hit, () => {
    ctx.emit("mj-chart-boxplot-click", { series: seriesName, category: category, stats: stats })
  })
  group.appendChild(hit)
  marks.appendChild(group)
  return
}


/* ── main render ─────────────────────────────────────────────────────────── */

export function render(ctx) {
  /*
   * Render a box plot.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const model = ctx.model
  const horizontal = ctx.orientation === "horizontal"
  const notched = booleanOption(ctx, "notched", false)
  const iqrAttr = parseFloat(ctx.attrs("iqr-mult", "1.5"))
  const iqrMult = isFiniteNumber(iqrAttr) === true && iqrAttr > 0 ? iqrAttr : 1.5

  const root = svgEl("g", { part: "plot" }, [])
  const series = Array.isArray(model.series) === true ? model.series : []
  const categories = groupCategories(model)
  if (series.length === 0 || categories.length === 0) {
    return root
  }

  /* Resolve every group once; the value domain covers whiskers and outliers. */
  const boxes = []
  let valMin = Infinity
  let valMax = -Infinity
  for (let si = 0; si < series.length; si = si + 1) {
    const groups = seriesGroups(series[si])
    for (let gi = 0; gi < groups.length; gi = gi + 1) {
      const stats = resolveBoxStats(groups[gi], iqrMult)
      if (stats === null) {
        continue
      }
      boxes.push({ seriesIndex: si, category: groups[gi].category, stats: stats })
      const values = [stats.whiskerLow, stats.whiskerHigh, stats.q1, stats.q3].concat(stats.outliers)
      for (let vi = 0; vi < values.length; vi = vi + 1) {
        valMin = Math.min(valMin, values[vi])
        valMax = Math.max(valMax, values[vi])
      }
    }
  }
  if (boxes.length === 0) {
    return root
  }

  const margin = { top: 16, right: 16, bottom: 40, left: horizontal === true ? 96 : 56 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)
  const valueLength = horizontal === true ? plotW : plotH
  const valueCount = tickCount(valueLength, horizontal === true ? 70 : 40)
  const pad = (valMax - valMin) * 0.05
  const domain = fitDomain(valMin - pad, valMax + pad, valueCount)

  const cat = bandScale(categories, [0, horizontal === true ? plotH : plotW], 0.2)
  const val = horizontal === true
    ? linearScale(domain, [0, plotW])
    : linearScale(domain, [plotH, 0])

  const plot = svgEl("g", { transform: `translate(${margin.left},${margin.top})` }, [])
  root.appendChild(plot)
  const axes = axisLayer(plot)
  if (horizontal === true) {
    drawTicks(axes, val, { side: "bottom", extent: plotH, count: valueCount })
  } else {
    drawTicks(axes, val, { side: "left", extent: plotW, count: valueCount })
  }
  const labels = categories.map((category, index) => ({ text: category, center: cat.centerAt(index) }))
  drawCategoryLabels(axes, labels, horizontal === true ? "left" : "bottom",
    horizontal === true ? 0 : plotH, horizontal === true ? margin.left - 12 : cat.step())

  const marks = svgEl("g", { part: "marks" }, [])
  plot.appendChild(marks)
  const bandwidth = cat.bandwidth()
  const clusterWidth = bandwidth / series.length
  const boxHalf = Math.max(clusterWidth * 0.35, 1)

  for (let bi = 0; bi < boxes.length; bi = bi + 1) {
    const box = boxes[bi]
    const position = cat.indexOf(box.category)
    if (position < 0) {
      continue
    }
    const center = cat.at(position) + box.seriesIndex * clusterWidth + clusterWidth / 2
    _drawBox(marks, box.stats, center, boxHalf, val, ctx, horizontal, notched,
      series[box.seriesIndex].name, box.category)
  }

  ctx.setTable({
    columns: ["Series", "Category", "Count", "Lower whisker", "Q1", "Median", "Q3", "Upper whisker", "Outliers"],
    rows: boxes.map((box) => [
      series[box.seriesIndex].name, String(box.category),
      box.stats.count !== null ? box.stats.count : "",
      box.stats.whiskerLow, box.stats.q1, box.stats.median, box.stats.q3, box.stats.whiskerHigh,
      box.stats.outliers.map((value) => formatNumber(value)).join(", ")
    ]),
    caption: "Five-number summary per group"
  })
  return root
}


registerRenderer("boxplot", render, { isEmpty: (model) => hasGroupData(model) === false })
