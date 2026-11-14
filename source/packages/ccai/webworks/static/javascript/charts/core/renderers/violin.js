/*
 * violin.js
 *
 * Violin plot renderer — mirrored kernel density silhouette per group.
 *
 * Registers: "violin"
 *
 * ctx.model.series data shape:
 *   series[].groups[]: { category, samples: [n, …] }
 *   categories (optional): display order; derived from the groups when
 *   omitted. Non-finite samples are missing data and ignored.
 *
 * Each group's density is evaluated on its own range (three bandwidths
 * past its data), so a tight group is not aliased by a coarse shared grid
 * and no outline runs along the whole axis.
 *
 * Relevant ctx.attrs:
 *   show-box      boolean — embed a miniature box plot inside each violin
 *   show-points   boolean — overlay the raw observations
 *   half          boolean — draw the right (or lower) half only
 *   bandwidth     KDE bandwidth in data units (Silverman's rule otherwise)
 *   violin-scale  "area" (default: every violin encloses the same area, so
 *                 widths compare densities) | "width" (every violin is as
 *                 wide as its band)
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber, linePath } from "../svgdraw.js";
import { linearScale, bandScale } from "../scales.js";
import {
  summarize, sortNumbers, silvermanBandwidth, gaussianDensity, linspace, isFiniteNumber,
  groupCategories, seriesGroups, hasGroupData, axisLayer, drawTicks, drawCategoryLabels,
  tickCount, activateOnKey, focusableMark, TEXT_COLOR, SURFACE_COLOR, fitDomain
} from "./diststats.js";
import { booleanOption } from "../chartoptions.js";

const KDE_POINTS = 81;
const KDE_TAIL_BANDWIDTHS = 3;


/* ── drawing ─────────────────────────────────────────────────────────────── */

function _orient(horizontal, along, across) {
  /*
   * A point at value pixel `along` and cross pixel `across`.
   */
  if (horizontal === true) {
    return { x: along, y: across }
  }
  return { x: across, y: along }
}


function _drawSilhouette(group, violin, center, halfWidth, densityScale, valScale, horizontal, halfViolin, color) {
  /*
   * The violin outline: densities mirrored around the band centre.
   */
  const upper = []
  const lower = []
  for (let index = 0; index < violin.xs.length; index = index + 1) {
    const along = valScale(violin.xs[index])
    const offset = Math.min(violin.ys[index] * densityScale, halfWidth)
    upper.push(_orient(horizontal, along, center + offset))
    lower.push(_orient(horizontal, along, center - offset))
  }
  let outline = null
  if (halfViolin === true) {
    const first = violin.xs[0]
    const last = violin.xs[violin.xs.length - 1]
    outline = [_orient(horizontal, valScale(first), center)].concat(upper,
      [_orient(horizontal, valScale(last), center)])
  } else {
    outline = upper.concat(lower.slice().reverse())
  }
  group.appendChild(svgEl("path", {
    d: linePath(outline) + " Z",
    fill: color, "fill-opacity": 0.45, stroke: color, "stroke-width": 1.5,
    "stroke-linejoin": "round", part: "violin"
  }, []))
  return
}


function _drawMiniBox(group, summary, center, halfWidth, valScale, horizontal) {
  /*
   * A miniature box plot (IQR box, median, whiskers) inside the violin.
   */
  const boxHalf = Math.max(halfWidth * 0.18, 2)
  const q1 = valScale(summary.q1)
  const q3 = valScale(summary.q3)
  const box = horizontal === true
    ? svgEl("rect", { x: Math.min(q1, q3), y: center - boxHalf, width: Math.abs(q3 - q1), height: boxHalf * 2 })
    : svgEl("rect", { x: center - boxHalf, y: Math.min(q1, q3), width: boxHalf * 2, height: Math.abs(q3 - q1) })
  box.setAttribute("fill", SURFACE_COLOR)
  box.setAttribute("stroke", TEXT_COLOR)
  box.setAttribute("stroke-width", "1.25")
  box.setAttribute("part", "violin-box")

  const whiskerLow = _orient(horizontal, valScale(summary.whiskerLow), center)
  const whiskerHigh = _orient(horizontal, valScale(summary.whiskerHigh), center)
  group.appendChild(svgEl("line", {
    x1: whiskerLow.x, y1: whiskerLow.y, x2: whiskerHigh.x, y2: whiskerHigh.y,
    stroke: TEXT_COLOR, "stroke-width": 1
  }, []))
  group.appendChild(box)
  const medianA = _orient(horizontal, valScale(summary.median), center - boxHalf)
  const medianB = _orient(horizontal, valScale(summary.median), center + boxHalf)
  group.appendChild(svgEl("line", {
    x1: medianA.x, y1: medianA.y, x2: medianB.x, y2: medianB.y,
    stroke: TEXT_COLOR, "stroke-width": 2, part: "violin-median"
  }, []))
  return
}


/* ── main render ─────────────────────────────────────────────────────────── */

export function render(ctx) {
  /*
   * Render a violin plot.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const model = ctx.model
  const horizontal = ctx.orientation === "horizontal"
  const showBox = booleanOption(ctx, "show-box", false)
  const showPoints = booleanOption(ctx, "show-points", false)
  const halfViolin = booleanOption(ctx, "half", false)
  const widthMode = ctx.attrs("violin-scale", "area") === "width" ? "width" : "area"
  const bandwidthAttr = parseFloat(ctx.attrs("bandwidth", ""))
  const bandwidthOverride = isFiniteNumber(bandwidthAttr) === true && bandwidthAttr > 0 ? bandwidthAttr : 0

  const root = svgEl("g", { part: "plot" }, [])
  const series = Array.isArray(model.series) === true ? model.series : []
  const categories = groupCategories(model)
  if (series.length === 0 || categories.length === 0) {
    return root
  }

  /* One density per group, each on its own range. */
  const violins = []
  let valMin = Infinity
  let valMax = -Infinity
  let maxDensity = 0
  for (let si = 0; si < series.length; si = si + 1) {
    const groups = seriesGroups(series[si])
    for (let gi = 0; gi < groups.length; gi = gi + 1) {
      const sorted = sortNumbers(groups[gi].samples)
      if (sorted.length === 0) {
        continue
      }
      const bandwidth = bandwidthOverride > 0 ? bandwidthOverride : silvermanBandwidth(sorted)
      const xs = linspace(sorted[0] - KDE_TAIL_BANDWIDTHS * bandwidth,
        sorted[sorted.length - 1] + KDE_TAIL_BANDWIDTHS * bandwidth, KDE_POINTS)
      const ys = gaussianDensity(sorted, bandwidth, xs)
      let peak = 0
      for (let index = 0; index < ys.length; index = index + 1) {
        peak = Math.max(peak, ys[index])
      }
      maxDensity = Math.max(maxDensity, peak)
      valMin = Math.min(valMin, xs[0])
      valMax = Math.max(valMax, xs[xs.length - 1])
      violins.push({
        seriesIndex: si, category: groups[gi].category, samples: sorted,
        bandwidth: bandwidth, xs: xs, ys: ys, peak: peak, summary: summarize(sorted, 1.5)
      })
    }
  }
  if (violins.length === 0) {
    return root
  }

  const margin = { top: 16, right: 16, bottom: 40, left: horizontal === true ? 96 : 56 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)
  const valueCount = tickCount(horizontal === true ? plotW : plotH, horizontal === true ? 70 : 40)
  const domain = fitDomain(valMin, valMax, valueCount)

  const cat = bandScale(categories, [0, horizontal === true ? plotH : plotW], 0.15)
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
  drawCategoryLabels(axes, categories.map((category, index) => ({ text: category, center: cat.centerAt(index) })),
    horizontal === true ? "left" : "bottom", horizontal === true ? 0 : plotH,
    horizontal === true ? margin.left - 12 : cat.step())

  const marks = svgEl("g", { part: "marks" }, [])
  plot.appendChild(marks)
  const clusterWidth = cat.bandwidth() / series.length
  const halfWidth = Math.max(clusterWidth * 0.46, 1)

  for (let vi = 0; vi < violins.length; vi = vi + 1) {
    const violin = violins[vi]
    const position = cat.indexOf(violin.category)
    if (position < 0) {
      continue
    }
    const entry = series[violin.seriesIndex]
    const color = ctx.colorFor(entry.name)
    const bandStart = cat.at(position) + violin.seriesIndex * clusterWidth
    const center = halfViolin === true ? bandStart + clusterWidth * 0.1 : bandStart + clusterWidth / 2
    const reach = halfViolin === true ? clusterWidth * 0.85 : halfWidth
    const peak = widthMode === "width" ? violin.peak : maxDensity
    const densityScale = peak > 0 ? reach / peak : 0
    const group = svgEl("g", { part: "violin-group" }, [])

    _drawSilhouette(group, violin, center, reach, densityScale, val, horizontal, halfViolin, color)
    if (showBox === true) {
      _drawMiniBox(group, violin.summary, center, reach, val, horizontal)
    } else {
      const medianA = _orient(horizontal, val(violin.summary.median), center - (halfViolin === true ? 0 : 4))
      const medianB = _orient(horizontal, val(violin.summary.median), center + 4)
      group.appendChild(svgEl("line", {
        x1: medianA.x, y1: medianA.y, x2: medianB.x, y2: medianB.y,
        stroke: TEXT_COLOR, "stroke-width": 2, part: "violin-median"
      }, []))
    }

    if (showPoints === true) {
      for (let pi = 0; pi < violin.samples.length; pi = pi + 1) {
        const seed = Math.sin((pi + 1) * 12.9898 + vi * 78.233) * 43758.5453
        const unit = seed - Math.floor(seed)
        const offset = halfViolin === true ? -(unit * 0.6 + 0.15) * clusterWidth * 0.1 - 3
          : (unit - 0.5) * reach * 0.5
        const point = _orient(horizontal, val(violin.samples[pi]), center + offset)
        group.appendChild(svgEl("circle", {
          cx: point.x, cy: point.y, r: 2.25, fill: color, "fill-opacity": 0.7, part: "violin-point"
        }, []))
      }
    }

    /* Focusable hit area over the silhouette's own extent. */
    const from = val(violin.xs[0])
    const to = val(violin.xs[violin.xs.length - 1])
    const crossStart = halfViolin === true ? center : center - reach
    const crossSize = halfViolin === true ? reach : reach * 2
    const hit = horizontal === true
      ? svgEl("rect", { x: Math.min(from, to), y: crossStart, width: Math.abs(to - from), height: crossSize })
      : svgEl("rect", { x: crossStart, y: Math.min(from, to), width: crossSize, height: Math.abs(to - from) })
    hit.setAttribute("fill", "transparent")
    hit.setAttribute("part", "violin-hit")
    const summary = violin.summary
    focusableMark(hit, `${entry.name}, ${violin.category}: ${formatNumber(summary.count)} observations, ` +
      `median ${formatNumber(summary.median)}, quartiles ${formatNumber(summary.q1)}–${formatNumber(summary.q3)}, ` +
      `range ${formatNumber(summary.min)}–${formatNumber(summary.max)}`)
    const handlerViolin = violin
    activateOnKey(hit, () => {
      ctx.emit("mj-chart-violin-click", {
        series: entry.name, category: handlerViolin.category,
        median: handlerViolin.summary.median, bandwidth: handlerViolin.bandwidth
      })
    })
    group.appendChild(hit)
    marks.appendChild(group)
  }

  ctx.setTable({
    columns: ["Series", "Category", "Count", "Min", "Q1", "Median", "Q3", "Max", "Bandwidth"],
    rows: violins.map((violin) => [
      series[violin.seriesIndex].name, String(violin.category), violin.summary.count,
      violin.summary.min, violin.summary.q1, violin.summary.median, violin.summary.q3,
      violin.summary.max, violin.bandwidth
    ]),
    caption: "Distribution summary per group"
  })
  return root
}


registerRenderer("violin", render, { isEmpty: (model) => hasGroupData(model, true) === false })
