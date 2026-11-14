/*
 * strip.js
 *
 * Strip plot and swarm plot renderer.
 *
 * Registers: "strip", "swarm"
 *
 * ctx.model.series data shape:
 *   series[].groups[]: { category, samples: [n, …] }
 *   categories (optional): display order; derived from the groups when
 *   omitted. Non-finite samples are missing data and ignored.
 *
 * Relevant ctx.attrs:
 *   jitter   "random" | "none" | "swarm" -- the default is "swarm" for the
 *            swarm type and "random" (deterministic pseudo-random) for strip
 *   r        point radius in px (default 4)
 *
 * The swarm layout visits the dots in value order and gives each the
 * free offset nearest the centre line, testing only dots within one
 * diameter (a sliding window), and keeps every tied value apart. When a
 * band is too narrow for the densest pile the radius shrinks (down to
 * 1.5 px); dots that still find no room are spread over the band. Layouts are cached per group
 * and pixel geometry, so a re-render at the same size does not redo them.
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber } from "../svgdraw.js";
import { linearScale, bandScale } from "../scales.js";
import {
  finiteValues, isFiniteNumber, placeSwarm, swarmRadius, groupCategories, seriesGroups, hasGroupData,
  axisLayer, drawTicks, drawCategoryLabels, tickCount, activateOnKey, focusableMark, fitDomain
} from "./diststats.js";

/* group object -> { signature, layout } */
const SWARM_CACHE = new WeakMap();

const MIN_SWARM_RADIUS = 1.5;


function _jitterOffset(value, index) {
  /*
   * A deterministic pseudo-random offset in [-1, 1] from the sample value
   * and index, stable across re-renders.
   */
  const seed = Math.sin(value * 12.9898 + (index + 1) * 78.233) * 43758.5453
  const unit = seed - Math.floor(seed)
  return unit * 2 - 1
}


function _swarmLayout(group, samples, valScale, halfBand, radius, signature) {
  /*
   * Swarm offsets for one group, shrinking the radius when the band
   * overflows; cached per group and geometry.
   *
   * :returns: { offsets, radius, overflow }
   */
  const cached = SWARM_CACHE.get(group)
  if (cached !== undefined && cached.signature === signature) {
    return cached.layout
  }
  const positions = samples.map((value) => valScale(value))
  const size = swarmRadius(positions, radius, 1, halfBand, MIN_SWARM_RADIUS)
  const placed = placeSwarm(positions, size * 2 + 1, halfBand)
  const layout = { offsets: placed.offsets, radius: size, overflow: placed.overflow }
  SWARM_CACHE.set(group, { signature: signature, layout: layout })
  return layout
}


export function render(ctx) {
  /*
   * Render a strip plot or swarm plot.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const model = ctx.model
  const horizontal = ctx.orientation === "horizontal"
  const jitter = ctx.attrs("jitter", ctx.type === "swarm" ? "swarm" : "random")
  const radiusAttr = parseFloat(ctx.attrs("r", "4"))
  const radius = isFiniteNumber(radiusAttr) === true && radiusAttr > 0 ? radiusAttr : 4

  const root = svgEl("g", { part: "plot" }, [])
  const series = Array.isArray(model.series) === true ? model.series : []
  const categories = groupCategories(model)
  if (series.length === 0 || categories.length === 0) {
    return root
  }

  let valMin = Infinity
  let valMax = -Infinity
  const strips = []
  for (let si = 0; si < series.length; si = si + 1) {
    const groups = seriesGroups(series[si])
    for (let gi = 0; gi < groups.length; gi = gi + 1) {
      const samples = finiteValues(groups[gi].samples)
      if (samples.length === 0) {
        continue
      }
      strips.push({ seriesIndex: si, group: groups[gi], samples: samples })
      for (let vi = 0; vi < samples.length; vi = vi + 1) {
        valMin = Math.min(valMin, samples[vi])
        valMax = Math.max(valMax, samples[vi])
      }
    }
  }
  if (strips.length === 0) {
    return root
  }

  const margin = { top: 16, right: 16, bottom: 40, left: horizontal === true ? 96 : 56 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)
  const valueCount = tickCount(horizontal === true ? plotW : plotH, horizontal === true ? 70 : 40)
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
  drawCategoryLabels(axes, categories.map((category, index) => ({ text: category, center: cat.centerAt(index) })),
    horizontal === true ? "left" : "bottom", horizontal === true ? 0 : plotH,
    horizontal === true ? margin.left - 12 : cat.step())

  const marks = svgEl("g", { part: "marks" }, [])
  plot.appendChild(marks)
  const clusterWidth = cat.bandwidth() / series.length
  const halfBand = Math.max(clusterWidth / 2 - radius, 0)
  const rows = []

  for (let gi = 0; gi < strips.length; gi = gi + 1) {
    const strip = strips[gi]
    const position = cat.indexOf(strip.group.category)
    if (position < 0) {
      continue
    }
    const entry = series[strip.seriesIndex]
    const color = ctx.colorFor(entry.name)
    const center = cat.at(position) + strip.seriesIndex * clusterWidth + clusterWidth / 2
    const category = strip.group.category

    let offsets = null
    let dotRadius = radius
    if (jitter === "swarm") {
      const signature = `${plotW}x${plotH}|${domain[0]},${domain[1]}|${radius}|${halfBand}|${horizontal}|${strip.samples.length}`
      const layout = _swarmLayout(strip.group, strip.samples, val, halfBand, radius, signature)
      offsets = layout.offsets
      dotRadius = layout.radius
    } else {
      offsets = strip.samples.map((value, index) => {
        return jitter === "none" ? 0 : _jitterOffset(value, index) * halfBand * 0.8
      })
    }

    const group = svgEl("g", { part: "strip" }, [])
    for (let pi = 0; pi < strip.samples.length; pi = pi + 1) {
      const value = strip.samples[pi]
      const along = val(value)
      const across = center + offsets[pi]
      const dot = svgEl("circle", {
        cx: horizontal === true ? along : across,
        cy: horizontal === true ? across : along,
        r: dotRadius, fill: color, "fill-opacity": 0.75
      }, [])
      dot.setAttribute("part", "point")
      focusableMark(dot, `${entry.name}, ${category}: ${formatNumber(value)}`)
      activateOnKey(dot, () => {
        ctx.emit("mj-chart-point-click", { series: entry.name, category: category, value: value })
      })
      group.appendChild(dot)
      rows.push([entry.name, String(category), value])
    }
    marks.appendChild(group)
  }

  ctx.setTable({ columns: ["Series", "Category", "Value"], rows: rows, caption: "Observations" })
  return root
}


registerRenderer("strip", render, { isEmpty: (model) => hasGroupData(model, true) === false })
registerRenderer("swarm", render, { isEmpty: (model) => hasGroupData(model, true) === false })
