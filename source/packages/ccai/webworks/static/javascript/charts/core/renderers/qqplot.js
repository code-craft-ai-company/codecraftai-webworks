/*
 * qqplot.js
 *
 * Q-Q plot renderer — sample quantiles against the quantiles of a
 * theoretical distribution (or of a second sample), with a reference line.
 *
 * Registers: "qq", "qqplot" (the spec's key)
 *
 * ctx.model.series data shapes:
 *   One or more samples against a theoretical distribution:
 *     series[]: { name, samples: [n, …], theoretical?: "normal" | "uniform" |
 *                 "exponential" | "lognormal" }
 *   Two empirical samples (used when exactly two series carry samples and
 *   no `theoretical` attribute is set):
 *     series[0]: { name, samples: [...] }   x axis
 *     series[1]: { name, samples: [...] }   y axis
 * Non-finite samples are missing data and ignored. The fitted parameters
 * come from the sample: mean / sd (normal), mean (exponential), mean / sd
 * of log x (lognormal, positive samples only), min / max (uniform).
 * Plotting positions are (i - 0.5) / n.
 *
 * Relevant ctx.attrs:
 *   theoretical   "normal" (default) | "uniform" | "exponential" | "lognormal"
 *   reference     "identity" (default: y = x) | "quartile" (the line through
 *                 the first and third quartile pairs, robust to outliers)
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber } from "../svgdraw.js";
import { linearScale } from "../scales.js";
import {
  sortNumbers, quantileSorted, meanOf, sampleStdDev, normalQuantile, hasSeriesSamples,
  axisLayer, drawTicks, drawAxisTitle, fitText, tickCount, activateOnKey, focusableMark,
  MUTED_TEXT_COLOR, fitDomain
} from "./diststats.js";

const DISTRIBUTIONS = ["normal", "uniform", "exponential", "lognormal"];


export function theoreticalQuantiles(probabilities, distribution, sorted) {
  /*
   * Quantiles of the distribution fitted to `sorted` at each probability.
   *
   * :returns: An array parallel to `probabilities`.
   */
  const result = []
  if (distribution === "uniform") {
    const low = sorted[0]
    const high = sorted[sorted.length - 1]
    for (let index = 0; index < probabilities.length; index = index + 1) {
      result.push(low + probabilities[index] * (high - low))
    }
    return result
  }
  if (distribution === "exponential") {
    const mean = meanOf(sorted)
    const scale = mean > 0 ? mean : 1
    for (let index = 0; index < probabilities.length; index = index + 1) {
      result.push(-Math.log(1 - probabilities[index]) * scale)
    }
    return result
  }
  if (distribution === "lognormal") {
    const logs = sorted.map((value) => Math.log(value))
    const mu = meanOf(logs)
    const sigma = logs.length > 1 ? sampleStdDev(logs) : 1
    for (let index = 0; index < probabilities.length; index = index + 1) {
      result.push(Math.exp(mu + sigma * normalQuantile(probabilities[index])))
    }
    return result
  }
  const mean = meanOf(sorted)
  const deviation = sorted.length > 1 ? sampleStdDev(sorted) : 1
  for (let index = 0; index < probabilities.length; index = index + 1) {
    result.push(mean + deviation * normalQuantile(probabilities[index]))
  }
  return result
}


function _pairsAgainst(entry, sorted, distribution, seriesIndex) {
  /*
   * (theoretical, observed) pairs of one sample.
   */
  const n = sorted.length
  const probabilities = []
  for (let index = 0; index < n; index = index + 1) {
    probabilities.push((index + 0.5) / n)
  }
  const theoretical = theoreticalQuantiles(probabilities, distribution, sorted)
  const pairs = []
  for (let index = 0; index < n; index = index + 1) {
    pairs.push({ x: theoretical[index], y: sorted[index], seriesIndex: seriesIndex, p: probabilities[index] })
  }
  return pairs
}


export function render(ctx) {
  /*
   * Render a Q-Q plot.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const model = ctx.model
  const theoreticalAttr = ctx.attrs("theoretical", null)
  const reference = ctx.attrs("reference", "identity") === "quartile" ? "quartile" : "identity"

  const root = svgEl("g", { part: "plot" }, [])
  const series = Array.isArray(model.series) === true ? model.series : []
  const withSamples = []
  for (let si = 0; si < series.length; si = si + 1) {
    const sorted = sortNumbers(series[si].samples)
    if (sorted.length > 0) {
      withSamples.push({ index: si, entry: series[si], sorted: sorted })
    }
  }
  if (withSamples.length === 0) {
    return root
  }

  const notes = []
  const twoSample = withSamples.length === 2 && theoreticalAttr === null
  let pairs = []
  let xTitle = ""
  let yTitle = "Sample quantiles"

  if (twoSample === true) {
    /* Quantiles of both samples at the larger sample's plotting positions. */
    const first = withSamples[0]
    const second = withSamples[1]
    const n = Math.max(first.sorted.length, second.sorted.length)
    for (let index = 0; index < n; index = index + 1) {
      const p = (index + 0.5) / n
      const position = (value) => (value * n - 0.5) / Math.max(n - 1, 1)
      pairs.push({
        x: quantileSorted(first.sorted, position(p)),
        y: quantileSorted(second.sorted, position(p)),
        seriesIndex: second.index,
        p: p
      })
    }
    xTitle = `${first.entry.name} quantiles`
    yTitle = `${second.entry.name} quantiles`
  } else {
    const shown = new Set()
    for (let wi = 0; wi < withSamples.length; wi = wi + 1) {
      const item = withSamples[wi]
      let distribution = item.entry.theoretical || theoreticalAttr || "normal"
      if (DISTRIBUTIONS.indexOf(distribution) < 0) {
        notes.push(`Unknown distribution "${distribution}": compared with normal`)
        distribution = "normal"
      }
      let sorted = item.sorted
      if (distribution === "lognormal") {
        const positive = sorted.filter((value) => value > 0)
        if (positive.length < sorted.length) {
          notes.push(`${item.entry.name}: ${sorted.length - positive.length} non-positive value(s) left out (lognormal)`)
        }
        sorted = positive
      }
      if (sorted.length === 0) {
        continue
      }
      shown.add(distribution)
      pairs = pairs.concat(_pairsAgainst(item.entry, sorted, distribution, item.index))
    }
    const names = Array.from(shown)
    xTitle = names.length === 1 ? `Theoretical quantiles (${names[0]})` : "Theoretical quantiles"
  }
  if (pairs.length === 0) {
    return root
  }

  let low = Infinity
  let high = -Infinity
  for (let index = 0; index < pairs.length; index = index + 1) {
    low = Math.min(low, pairs[index].x, pairs[index].y)
    high = Math.max(high, pairs[index].x, pairs[index].y)
  }

  const shownNotes = notes.slice(0, 2)
  const margin = { top: 16 + 12 * shownNotes.length, right: 20, bottom: 50, left: 64 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)
  const pad = (high - low) * 0.05
  const domain = fitDomain(low - pad, high + pad, 5)
  const xScale = linearScale(domain, [0, plotW])
  const yScale = linearScale(domain, [plotH, 0])

  const plot = svgEl("g", { transform: `translate(${margin.left},${margin.top})` }, [])
  root.appendChild(plot)
  const axes = axisLayer(plot)
  drawTicks(axes, xScale, { side: "bottom", extent: plotH, count: tickCount(plotW, 70) })
  drawTicks(axes, yScale, { side: "left", extent: plotW, count: tickCount(plotH, 40) })
  drawAxisTitle(axes, xTitle, "bottom", plotW, plotH, 38)
  drawAxisTitle(axes, yTitle, "left", plotW, plotH, 50)

  /* Reference line: y = x, or through the quartile pairs. */
  let slope = 1
  let intercept = 0
  if (reference === "quartile") {
    const sortedPairs = pairs.slice().sort((a, b) => a.p - b.p)
    const q1 = sortedPairs[Math.floor((sortedPairs.length - 1) * 0.25)]
    const q3 = sortedPairs[Math.ceil((sortedPairs.length - 1) * 0.75)]
    if (q3.x !== q1.x) {
      slope = (q3.y - q1.y) / (q3.x - q1.x)
      intercept = q1.y - slope * q1.x
    }
  }
  axes.appendChild(svgEl("line", {
    x1: xScale(domain[0]), y1: yScale(slope * domain[0] + intercept),
    x2: xScale(domain[1]), y2: yScale(slope * domain[1] + intercept),
    stroke: MUTED_TEXT_COLOR, "stroke-width": 1.5, "stroke-dasharray": "6 3",
    part: "reference-line"
  }, []))

  const marks = svgEl("g", { part: "marks" }, [])
  plot.appendChild(marks)
  const rows = []
  for (let index = 0; index < pairs.length; index = index + 1) {
    const pair = pairs[index]
    const entry = series[pair.seriesIndex]
    const color = ctx.colorFor(entry.name)
    const dot = svgEl("circle", {
      cx: xScale(pair.x), cy: yScale(pair.y), r: 3.5, fill: color, "fill-opacity": 0.8
    }, [])
    dot.setAttribute("part", "qq-point")
    focusableMark(dot, `${entry.name}: theoretical ${formatNumber(pair.x, { maximumSignificantDigits: 4 })}, ` +
      `observed ${formatNumber(pair.y, { maximumSignificantDigits: 4 })}`)
    const handlerPair = pair
    activateOnKey(dot, () => {
      ctx.emit("mj-chart-qq-click", { series: entry.name, theoretical: handlerPair.x, observed: handlerPair.y })
    })
    marks.appendChild(dot)
    rows.push([entry.name, pair.p, pair.x, pair.y])
  }

  for (let ni = 0; ni < shownNotes.length; ni = ni + 1) {
    plot.appendChild(svgEl("text", {
      x: 0, y: -margin.top + 11 + ni * 12, "font-size": 10, fill: MUTED_TEXT_COLOR, part: "note"
    }, fitText(shownNotes[ni], plotW, 10)))
  }

  ctx.setTable({
    columns: ["Series", "Probability", twoSample === true ? xTitle : "Theoretical quantile", "Sample quantile"],
    rows: rows,
    caption: "Quantile pairs"
  })
  return root
}


const OPTIONS = { isEmpty: (model) => hasSeriesSamples(model) === false }

registerRenderer("qq", render, OPTIONS)
registerRenderer("qqplot", render, OPTIONS)
