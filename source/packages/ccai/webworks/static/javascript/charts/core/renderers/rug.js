/*
 * rug.js
 *
 * Rug plot renderer — one tick mark per observation along a value axis.
 *
 * Registers: "rug" (default orientation "horizontal": values run along x
 * and each series is a thin strip stacked below the previous one;
 * orientation="vertical" puts the values on y with one column per series)
 *
 * ctx.model.series data shape:
 *   series[]: { name, samples: [n, …] }   non-finite samples are missing
 *                                         data and ignored
 *
 * Relevant ctx.attrs:
 *   tick-height   length of each tick in px (default: 70% of the strip)
 *   opacity       per-tick opacity (default: lower for denser data)
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber } from "../svgdraw.js";
import { linearScale } from "../scales.js";
import {
  finiteValues, sortNumbers, quantileSorted, isFiniteNumber, hasSeriesSamples, axisLayer,
  drawTicks, drawBaseline, fitText, tickCount, activateOnKey, focusableMark, TEXT_COLOR, fitDomain
} from "./diststats.js";

/* Thickness of one series strip, at most. */
const STRIP_MAX = 36;


export function render(ctx) {
  /*
   * Render a rug plot.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const model = ctx.model
  const horizontal = ctx.orientation !== "vertical"
  const tickAttr = parseFloat(ctx.attrs("tick-height", ""))
  const opacityAttr = parseFloat(ctx.attrs("opacity", ""))

  const root = svgEl("g", { part: "plot" }, [])
  const allSeries = Array.isArray(model.series) === true ? model.series : []
  const rugs = []
  let valMin = Infinity
  let valMax = -Infinity
  let total = 0
  for (let si = 0; si < allSeries.length; si = si + 1) {
    const samples = finiteValues(allSeries[si].samples)
    if (samples.length === 0) {
      continue
    }
    rugs.push({ name: allSeries[si].name, samples: samples })
    total = total + samples.length
    for (let vi = 0; vi < samples.length; vi = vi + 1) {
      valMin = Math.min(valMin, samples[vi])
      valMax = Math.max(valMax, samples[vi])
    }
  }
  if (rugs.length === 0) {
    return root
  }

  const autoOpacity = total > 200 ? 0.35 : (total > 50 ? 0.55 : 0.8)
  const tickOpacity = isFiniteNumber(opacityAttr) === true && opacityAttr > 0 && opacityAttr <= 1
    ? opacityAttr : autoOpacity

  /* Series names sit beside their strip, so leave room for the longest. */
  let longest = 0
  for (let ri = 0; ri < rugs.length; ri = ri + 1) {
    longest = Math.max(longest, String(rugs[ri].name).length)
  }
  const nameRoom = Math.min(Math.max(longest * 6.4 + 12, 40), Math.max(ctx.width * 0.3, 40))
  const margin = horizontal === true
    ? { top: 12, right: 16, bottom: 28, left: nameRoom }
    : { top: 12, right: 16, bottom: 28, left: 56 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)
  /*
   * Horizontal: strips of at most STRIP_MAX px stacked from the top.
   * Vertical: the columns share the plot width (one slot per series, the
   * ticks centred in their slot and at most STRIP_MAX px long), so the
   * series names under them have the room of a whole slot.
   */
  const stripSize = horizontal === true
    ? Math.max(Math.min(plotH / rugs.length, STRIP_MAX), 6)
    : Math.max(plotW / rugs.length, 6)
  const autoLength = Math.min(stripSize * 0.7, STRIP_MAX * 0.7)
  const tickLength = isFiniteNumber(tickAttr) === true && tickAttr > 0
    ? Math.min(tickAttr, stripSize) : autoLength
  const block = horizontal === true ? stripSize * rugs.length : plotW

  const valueLength = horizontal === true ? plotW : plotH
  const valueCount = tickCount(valueLength, horizontal === true ? 70 : 40)
  const pad = (valMax - valMin) * 0.03
  const domain = fitDomain(valMin - pad, valMax + pad, valueCount)
  const valScale = horizontal === true
    ? linearScale(domain, [0, plotW])
    : linearScale(domain, [plotH, 0])

  const plot = svgEl("g", { transform: `translate(${margin.left},${margin.top})` }, [])
  root.appendChild(plot)
  const axes = axisLayer(plot)
  if (horizontal === true) {
    drawTicks(axes, valScale, { side: "bottom", extent: block, at: block, count: valueCount, grid: false })
    drawBaseline(axes, 0, block, plotW, block)
  } else {
    drawTicks(axes, valScale, { side: "left", extent: block, count: valueCount, grid: false })
    drawBaseline(axes, 0, 0, 0, plotH)
  }

  const marks = svgEl("g", { part: "marks" }, [])
  plot.appendChild(marks)
  const rows = []

  for (let ri = 0; ri < rugs.length; ri = ri + 1) {
    const rug = rugs[ri]
    const color = ctx.colorFor(rug.name)
    const stripStart = ri * stripSize
    const tickStart = stripStart + (stripSize - tickLength) / 2
    const group = svgEl("g", { part: "rug" }, [])

    /* Series name beside (horizontal) or under (vertical) its strip. */
    if (rugs.length > 1 || horizontal === true) {
      if (horizontal === true) {
        axes.appendChild(svgEl("text", {
          x: -8, y: stripStart + stripSize / 2 + 4, "text-anchor": "end",
          "font-size": 11, fill: TEXT_COLOR
        }, fitText(rug.name, margin.left - 12, 11)))
      } else {
        axes.appendChild(svgEl("text", {
          x: stripStart + stripSize / 2, y: plotH + 16, "text-anchor": "middle",
          "font-size": 11, fill: TEXT_COLOR
        }, fitText(rug.name, Math.max(stripSize - 8, 24), 11)))
      }
    }

    for (let vi = 0; vi < rug.samples.length; vi = vi + 1) {
      const value = rug.samples[vi]
      const along = valScale(value)
      const tick = horizontal === true
        ? svgEl("line", { x1: along, y1: tickStart, x2: along, y2: tickStart + tickLength })
        : svgEl("line", { x1: tickStart, y1: along, x2: tickStart + tickLength, y2: along })
      tick.setAttribute("stroke", color)
      tick.setAttribute("stroke-width", "1.5")
      tick.setAttribute("stroke-opacity", String(tickOpacity))
      tick.setAttribute("part", "rug-tick")
      focusableMark(tick, `${rug.name}: ${formatNumber(value)}`)
      activateOnKey(tick, () => {
        ctx.emit("mj-chart-rug-click", { series: rug.name, value: value })
      })
      group.appendChild(tick)
    }
    marks.appendChild(group)

    const sorted = sortNumbers(rug.samples)
    rows.push([rug.name, sorted.length, sorted[0], quantileSorted(sorted, 0.25),
      quantileSorted(sorted, 0.5), quantileSorted(sorted, 0.75), sorted[sorted.length - 1]])
  }

  ctx.setTable({
    columns: ["Series", "Count", "Min", "Q1", "Median", "Q3", "Max"],
    rows: rows,
    caption: "Observations per series"
  })
  return root
}


registerRenderer("rug", render, {
  orientation: "horizontal",
  minHeight: 140,
  isEmpty: (model) => hasSeriesSamples(model) === false
})
