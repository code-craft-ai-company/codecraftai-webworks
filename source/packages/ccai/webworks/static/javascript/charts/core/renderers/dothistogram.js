/*
 * dothistogram.js
 *
 * Dot histogram (Wilkinson dot plot) renderer — one dot per observation,
 * stacked per bin. Falls back to bars when a series has too many dots to
 * draw individually (the chart then says so).
 *
 * Registers: "dot-histogram", "dothistogram" (the spec's key)
 *
 * ctx.model.series data shape:
 *   series[]:
 *     - { name, samples: [n, …] }            binned with shared edges
 *     - { name, bins: [{x0, x1, count}] }    pre-binned
 *
 * Dot k of a bin (k = 0, 1, …) is centred on count k + 0.5 of the count
 * axis, so stacks and gridlines always agree, and the radius is the
 * largest that fits both the bin (lane) width and one count unit.
 *
 * Relevant ctx.attrs:
 *   bin-count   number of bins (default Sturges)
 *   bin-width   bin width in data units (wins over bin-count)
 *   dot-size    dot diameter as a share (0–1] of the largest that fits
 *               (default 1)
 *   group       "overlay" (series share the bin) | default: side by side
 *   dot-limit   max dots of any one series before bars are drawn
 *               (default 200)
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber } from "../svgdraw.js";
import { linearScale, niceDomain, niceTicks } from "../scales.js";
import {
  binSeries, isFiniteNumber, hasSeriesSamples, axisLayer, drawTicks, drawBaseline,
  drawAxisTitle, tickCount, activateOnKey, focusableMark, MUTED_TEXT_COLOR
} from "./diststats.js";

/* Below this radius dots are unreadable and bars are drawn instead. */
const MIN_DOT_RADIUS = 1.5;


function _binLabel(name, bin) {
  /*
   * Accessible text of a bin.
   */
  const label = `${name}, ${formatNumber(bin.x0)}–${formatNumber(bin.x1)}: ${formatNumber(bin.count)}`
  return label
}


export function render(ctx) {
  /*
   * Render a dot histogram.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const model = ctx.model
  const horizontal = ctx.orientation === "horizontal"
  const countAttr = parseInt(ctx.attrs("bin-count", ""), 10)
  const widthAttr = parseFloat(ctx.attrs("bin-width", ""))
  const sizeAttr = parseFloat(ctx.attrs("dot-size", ""))
  const dotShare = isFiniteNumber(sizeAttr) === true && sizeAttr > 0 && sizeAttr <= 1 ? sizeAttr : 1
  const overlay = ctx.attrs("group", "") === "overlay"
  const limitAttr = parseInt(ctx.attrs("dot-limit", "200"), 10)
  const dotLimit = isFiniteNumber(limitAttr) === true && limitAttr > 0 ? limitAttr : 200

  const root = svgEl("g", { part: "plot" }, [])
  const series = Array.isArray(model.series) === true ? model.series : []
  const prepared = binSeries(series, {
    count: isFiniteNumber(countAttr) === true && countAttr > 0 ? countAttr : null,
    width: isFiniteNumber(widthAttr) === true && widthAttr > 0 ? widthAttr : null,
    method: "sturges"
  })
  const resolved = prepared.series.filter((entry) => entry.bins.length > 0)
  if (resolved.length === 0) {
    return root
  }

  let binMin = Infinity
  let binMax = -Infinity
  let maxCount = 0
  let largestSeries = 0
  let narrowestBin = Infinity
  for (let si = 0; si < resolved.length; si = si + 1) {
    const entry = resolved[si]
    largestSeries = Math.max(largestSeries, entry.total)
    for (let bi = 0; bi < entry.bins.length; bi = bi + 1) {
      const bin = entry.bins[bi]
      binMin = Math.min(binMin, bin.x0)
      binMax = Math.max(binMax, bin.x1)
      maxCount = Math.max(maxCount, bin.count)
      narrowestBin = Math.min(narrowestBin, bin.x1 - bin.x0)
    }
  }

  const margin = { top: 16, right: 16, bottom: 44, left: 60 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)
  const binLength = horizontal === true ? plotH : plotW
  const countLength = horizontal === true ? plotW : plotH

  const countTicksWanted = tickCount(countLength, horizontal === true ? 70 : 40)
  const countTop = Math.max(Math.ceil(niceDomain(0, Math.max(maxCount, 1), countTicksWanted)[1]), 1)
  const binScale = linearScale([binMin, binMax], [0, binLength])
  const countScale = horizontal === true
    ? linearScale([0, countTop], [0, plotW])
    : linearScale([0, countTop], [plotH, 0])

  /* Largest radius that fits a lane of the narrowest bin and a count unit. */
  const lanes = overlay === false && resolved.length > 1 ? resolved.length : 1
  const laneWidth = Math.abs(binScale(binMin + narrowestBin) - binScale(binMin)) / lanes
  const unit = countLength / countTop
  const fitRadius = (Math.min(laneWidth, unit) / 2 - 0.5) * dotShare
  const useBars = largestSeries > dotLimit || fitRadius < MIN_DOT_RADIUS

  const plot = svgEl("g", { transform: `translate(${margin.left},${margin.top})` }, [])
  root.appendChild(plot)
  const axes = axisLayer(plot)
  let countTicks = niceTicks(0, countTop, countTicksWanted)
  if (countTicks.length < 3) {
    countTicks = niceTicks(0, countTop, countTicksWanted * 2)
  }
  countTicks = countTicks.filter((tick) => Number.isInteger(tick) === true)
  const binTickCount = tickCount(binLength, horizontal === true ? 36 : 70)
  if (horizontal === true) {
    drawTicks(axes, countScale, { side: "bottom", extent: plotH, ticks: countTicks })
    drawTicks(axes, binScale, { side: "left", extent: plotW, count: binTickCount, grid: false })
    drawAxisTitle(axes, "Count", "bottom", plotW, plotH, 36)
  } else {
    drawTicks(axes, countScale, { side: "left", extent: plotW, ticks: countTicks })
    drawTicks(axes, binScale, { side: "bottom", extent: plotH, count: binTickCount, grid: false })
    drawAxisTitle(axes, "Count", "left", plotW, plotH, 46)
  }

  const marks = svgEl("g", { part: "marks" }, [])
  plot.appendChild(marks)
  const rows = []

  for (let si = 0; si < resolved.length; si = si + 1) {
    const entry = resolved[si]
    const color = ctx.colorFor(entry.name)
    const group = svgEl("g", { part: "series" }, [])
    const lane = overlay === false && resolved.length > 1 ? si : 0

    for (let bi = 0; bi < entry.bins.length; bi = bi + 1) {
      const bin = entry.bins[bi]
      rows.push([entry.name, bin.x0, bin.x1, bin.count])
      if (bin.count <= 0) {
        continue
      }
      const start = Math.min(binScale(bin.x0), binScale(bin.x1))
      const binPx = Math.abs(binScale(bin.x1) - binScale(bin.x0))
      const lanePx = binPx / lanes
      const laneStart = start + lane * lanePx
      const label = _binLabel(entry.name, bin)
      const handlerBin = bin
      const handler = () => {
        ctx.emit("mj-chart-dot-click", {
          series: entry.name, x0: handlerBin.x0, x1: handlerBin.x1, count: handlerBin.count
        })
      }

      if (useBars === true) {
        const from = countScale(0)
        const to = countScale(bin.count)
        const bar = horizontal === true
          ? svgEl("rect", { x: Math.min(from, to), y: laneStart + 0.5, width: Math.abs(to - from), height: Math.max(lanePx - 1, 1) })
          : svgEl("rect", { x: laneStart + 0.5, y: Math.min(from, to), width: Math.max(lanePx - 1, 1), height: Math.abs(to - from) })
        bar.setAttribute("fill", color)
        if (overlay === true && resolved.length > 1) {
          bar.setAttribute("fill-opacity", "0.55")
        }
        bar.setAttribute("part", "bar")
        focusableMark(bar, label)
        activateOnKey(bar, handler)
        group.appendChild(bar)
        continue
      }

      /* One focusable stack per bin; its dots are its visual content. */
      const stack = svgEl("g", { part: "dot-stack" }, [])
      const laneCenter = laneStart + lanePx / 2
      for (let di = 0; di < bin.count; di = di + 1) {
        const along = countScale(di + 0.5)
        stack.appendChild(svgEl("circle", {
          cx: horizontal === true ? along : laneCenter,
          cy: horizontal === true ? laneCenter : along,
          r: fitRadius, fill: color, "fill-opacity": overlay === true && resolved.length > 1 ? 0.6 : 0.9,
          part: "dot"
        }, []))
      }
      focusableMark(stack, label)
      activateOnKey(stack, handler)
      group.appendChild(stack)
    }
    marks.appendChild(group)
  }

  const zero = countScale(0)
  if (horizontal === true) {
    drawBaseline(axes, zero, 0, zero, plotH)
  } else {
    drawBaseline(axes, 0, zero, plotW, zero)
  }

  if (useBars === true) {
    const reason = largestSeries > dotLimit
      ? `Shown as bars: a series has more than ${formatNumber(dotLimit)} observations`
      : "Shown as bars: too many observations per bin for dots at this size"
    plot.appendChild(svgEl("text", {
      x: plotW, y: -4, "text-anchor": "end", "font-size": 10,
      fill: MUTED_TEXT_COLOR, part: "fallback-note"
    }, reason))
  }

  ctx.setTable({ columns: ["Series", "From", "To", "Count"], rows: rows, caption: "Observations per bin" })
  return root
}


const OPTIONS = { isEmpty: (model) => hasSeriesSamples(model) === false }

registerRenderer("dot-histogram", render, OPTIONS)
registerRenderer("dothistogram", render, OPTIONS)
