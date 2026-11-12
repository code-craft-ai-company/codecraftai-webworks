/*
 * ridgeline.js
 *
 * Ridgeline (joy) plot renderer — vertically offset density curves, one
 * row per category.
 *
 * Registers: "ridgeline"
 *
 * ctx.model.series data shape:
 *   series[].groups[]: { category, samples: [n, …] }
 *   categories (optional): row order, top to bottom; derived from the
 *   groups when omitted. Non-finite samples are missing data.
 * With one series each row has its own colour; with several series every
 * row overlays one curve per series, coloured by series.
 *
 * Relevant ctx.attrs:
 *   mode       "density" (default) | "histogram" (stepped ridges)
 *   overlap    how far a full-height ridge reaches into the row above, in
 *              row heights (default 0.5; 0 = no overlap)
 *   bandwidth  KDE bandwidth in data units (Silverman's rule otherwise)
 *   bin-count  bins of histogram mode (default Sturges of the largest group)
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber, linePath, areaPath } from "../svgdraw.js";
import { linearScale } from "../scales.js";
import {
  sortNumbers, summarize, silvermanBandwidth, gaussianDensity, linspace, binEdges,
  countBins, isFiniteNumber, groupCategories, seriesGroups, hasGroupData, axisLayer,
  drawTicks, fitText, tickCount, activateOnKey, focusableMark, TEXT_COLOR, GRID_COLOR, fitDomain
} from "./diststats.js";

const KDE_POINTS = 81;
const KDE_TAIL_BANDWIDTHS = 3;


function _ridgeCurve(sorted, mode, bandwidthOverride, edges) {
  /*
   * The (x, amplitude) points of one ridge.
   *
   * :returns: { xs, ys, bandwidth } -- density mode evaluates the KDE on
   *     the group's own range (three bandwidths past its data); histogram
   *     mode gives a closed step outline over the shared bin edges.
   */
  if (mode === "histogram") {
    const bins = countBins(sorted, edges)
    const xs = []
    const ys = []
    for (let bi = 0; bi < bins.length; bi = bi + 1) {
      const height = sorted.length > 0 ? bins[bi].count / sorted.length : 0
      xs.push(bins[bi].x0, bins[bi].x1)
      ys.push(height, height)
    }
    return { xs: xs, ys: ys, bandwidth: null, bins: bins }
  }
  const bandwidth = bandwidthOverride > 0 ? bandwidthOverride : silvermanBandwidth(sorted)
  const xs = linspace(sorted[0] - KDE_TAIL_BANDWIDTHS * bandwidth,
    sorted[sorted.length - 1] + KDE_TAIL_BANDWIDTHS * bandwidth, KDE_POINTS)
  const ys = gaussianDensity(sorted, bandwidth, xs)
  return { xs: xs, ys: ys, bandwidth: bandwidth, bins: null }
}


export function render(ctx) {
  /*
   * Render a ridgeline plot.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const model = ctx.model
  const mode = ctx.attrs("mode", "density") === "histogram" ? "histogram" : "density"
  const overlapAttr = parseFloat(ctx.attrs("overlap", "0.5"))
  const overlap = isFiniteNumber(overlapAttr) === true ? Math.max(0, Math.min(overlapAttr, 3)) : 0.5
  const bandwidthAttr = parseFloat(ctx.attrs("bandwidth", ""))
  const bandwidthOverride = isFiniteNumber(bandwidthAttr) === true && bandwidthAttr > 0 ? bandwidthAttr : 0
  const binCountAttr = parseInt(ctx.attrs("bin-count", ""), 10)

  const root = svgEl("g", { part: "plot" }, [])
  const series = Array.isArray(model.series) === true ? model.series : []
  const categories = groupCategories(model)
  if (series.length === 0 || categories.length === 0) {
    return root
  }

  /* Every (category, series) pair with data. */
  const pooled = []
  let largestGroup = 0
  const groupsByRow = categories.map(() => [])
  for (let si = 0; si < series.length; si = si + 1) {
    const groups = seriesGroups(series[si])
    for (let gi = 0; gi < groups.length; gi = gi + 1) {
      const row = categories.findIndex((category) => String(category) === String(groups[gi].category))
      const sorted = sortNumbers(groups[gi].samples)
      if (row < 0 || sorted.length === 0) {
        continue
      }
      groupsByRow[row].push({ seriesIndex: si, sorted: sorted })
      largestGroup = Math.max(largestGroup, sorted.length)
      for (let vi = 0; vi < sorted.length; vi = vi + 1) {
        pooled.push(sorted[vi])
      }
    }
  }
  if (pooled.length === 0) {
    return root
  }

  const binCount = isFiniteNumber(binCountAttr) === true && binCountAttr > 0
    ? binCountAttr : Math.max(Math.ceil(Math.log2(largestGroup) + 1), 1)
  const edges = binEdges(pooled, { count: binCount })

  let valMin = Infinity
  let valMax = -Infinity
  let maxAmplitude = 0
  const ridges = []
  for (let row = 0; row < groupsByRow.length; row = row + 1) {
    for (let index = 0; index < groupsByRow[row].length; index = index + 1) {
      const entry = groupsByRow[row][index]
      const curve = _ridgeCurve(entry.sorted, mode, bandwidthOverride, edges)
      for (let pi = 0; pi < curve.xs.length; pi = pi + 1) {
        valMin = Math.min(valMin, curve.xs[pi])
        valMax = Math.max(valMax, curve.xs[pi])
        maxAmplitude = Math.max(maxAmplitude, curve.ys[pi])
      }
      ridges.push({ row: row, seriesIndex: entry.seriesIndex, sorted: entry.sorted, curve: curve })
    }
  }
  if (maxAmplitude <= 0) {
    maxAmplitude = 1
  }

  let longest = 0
  for (let ci = 0; ci < categories.length; ci = ci + 1) {
    longest = Math.max(longest, String(categories[ci]).length)
  }
  const labelRoom = Math.min(Math.max(longest * 6.4 + 14, 44), Math.max(ctx.width * 0.3, 44))
  const margin = { top: 12, right: 16, bottom: 32, left: labelRoom }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  /* Headroom: the top ridge may rise overlap row heights above its row. */
  const rowH = plotH / (categories.length + overlap)
  const amplitudeH = rowH * (1 + overlap)
  const baselineOf = (row) => (row + 1 + overlap) * rowH

  const valueCount = tickCount(plotW, 70)
  const domain = fitDomain(valMin, valMax, valueCount)
  const valScale = linearScale(domain, [0, plotW])

  const plot = svgEl("g", { transform: `translate(${margin.left},${margin.top})` }, [])
  root.appendChild(plot)
  const axes = axisLayer(plot)
  drawTicks(axes, valScale, { side: "bottom", extent: plotH, count: valueCount })

  for (let row = 0; row < categories.length; row = row + 1) {
    const baseline = baselineOf(row)
    axes.appendChild(svgEl("line", {
      x1: 0, y1: baseline, x2: plotW, y2: baseline, stroke: GRID_COLOR, "stroke-width": 1
    }, []))
    axes.appendChild(svgEl("text", {
      x: -8, y: baseline - 3, "text-anchor": "end", "font-size": 11, fill: TEXT_COLOR
    }, fitText(categories[row], margin.left - 12, 11)))
  }

  /* Top row first, so each lower ridge is drawn over the one above it. */
  const marks = svgEl("g", { part: "marks" }, [])
  plot.appendChild(marks)
  const singleSeries = series.length === 1
  for (let ri = 0; ri < ridges.length; ri = ri + 1) {
    const ridge = ridges[ri]
    const category = categories[ridge.row]
    const entry = series[ridge.seriesIndex]
    const color = singleSeries === true ? ctx.colorFor(`category:${String(category)}`) : ctx.colorFor(entry.name)
    const baseline = baselineOf(ridge.row)
    const points = ridge.curve.xs.map((x, index) => ({
      x: valScale(x),
      y: baseline - (ridge.curve.ys[index] / maxAmplitude) * amplitudeH
    }))
    const group = svgEl("g", { part: "ridge-group" }, [])
    group.appendChild(svgEl("path", {
      d: areaPath(points, baseline), fill: color, "fill-opacity": 0.55, stroke: "none"
    }, []))
    const line = svgEl("path", {
      d: linePath(points), fill: "none", stroke: color, "stroke-width": 1.5,
      "stroke-linejoin": "round", part: "ridge"
    }, [])
    const summary = summarize(ridge.sorted, 1.5)
    const seriesText = singleSeries === true ? "" : `${entry.name}, `
    focusableMark(line, `${seriesText}${category}: ${formatNumber(summary.count)} observations, ` +
      `median ${formatNumber(summary.median)}, range ${formatNumber(summary.min)}–${formatNumber(summary.max)}`)
    activateOnKey(line, () => {
      ctx.emit("mj-chart-ridge-click", { series: entry.name, category: category, median: summary.median })
    })
    group.appendChild(line)
    marks.appendChild(group)
    ridge.summary = summary
  }

  if (singleSeries === true) {
    /* The row labels name the colours; a one-entry series legend would not. */
    ctx.setLegend([])
  }
  ctx.setTable({
    columns: ["Series", "Category", "Count", "Min", "Q1", "Median", "Q3", "Max"],
    rows: ridges.map((ridge) => [
      series[ridge.seriesIndex].name, String(categories[ridge.row]), ridge.summary.count,
      ridge.summary.min, ridge.summary.q1, ridge.summary.median, ridge.summary.q3, ridge.summary.max
    ]),
    caption: "Distribution summary per row"
  })
  return root
}


registerRenderer("ridgeline", render, { isEmpty: (model) => hasGroupData(model, true) === false })
