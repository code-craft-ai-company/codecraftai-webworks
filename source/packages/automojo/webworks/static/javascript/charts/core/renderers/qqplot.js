/*
 * qqplot.js
 *
 * Q-Q plot renderer — quantile vs quantile scatter with a 45° reference line.
 *
 * Registers: "qq"
 *
 * ctx.model.series data shapes:
 *   Single sample vs theoretical:
 *     series[0]: { name, samples: [n, …], theoretical?: "normal"|"uniform"|"exponential"|"lognormal" }
 *   Two empirical samples:
 *     series[0]: { name, samples: [...] }
 *     series[1]: { name, samples: [...] }
 *
 * Relevant ctx.attrs:
 *   theoretical   "normal" (default) | "uniform" | "exponential" | "lognormal"
 *                 Ignored when two series are provided.
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber, linePath } from "../svgdraw.js";
import { linearScale, niceTicks } from "../scales.js";


/* ── quantile / theoretical helpers ─────────────────────────────────────── */

function _quantile(sorted, p) {
  /*
   * Linear interpolation quantile from a sorted array.
   */
  const n = sorted.length
  if (n === 0) { return 0 }
  if (n === 1) { return sorted[0] }
  const index = p * (n - 1)
  const lo = Math.floor(index)
  const hi = Math.ceil(index)
  const frac = index - lo
  return sorted[lo] * (1 - frac) + sorted[hi] * frac
}


function _normalPPF(p) {
  /*
   * Rational approximation to the normal percent-point function (probit).
   * Abramowitz & Stegun 26.2.17 approximation.
   */
  if (p <= 0) { return -6 }
  if (p >= 1) { return 6 }
  const a = [0, -3.969683028665376e+01, 2.209460984245205e+02,
    -2.759285104469687e+02, 1.383577518672690e+02,
    -3.066479806614716e+01, 2.506628277459239e+00]
  const b = [0, -5.447609879822406e+01, 1.615858368580409e+02,
    -1.556989798598866e+02, 6.680131188771972e+01, -1.328068155288572e+01]
  const c = [-7.784894002430293e-03, -3.223964580411365e-01,
    -2.400758277161838e+00, -2.549732539343734e+00,
    4.374664141464968e+00, 2.938163982698783e+00]
  const d = [7.784695709041462e-03, 3.224671290700398e-01,
    2.445134137142996e+00, 3.754408661907416e+00]

  const pLow = 0.02425
  const pHigh = 1 - pLow
  let q = 0
  if (p < pLow) {
    q = Math.sqrt(-2 * Math.log(p))
    const num = (((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]
    const den = ((d[0] * q + d[1]) * q + d[2]) * q + d[3]
    return (num / den) * q + c[5]
  }
  if (p <= pHigh) {
    q = p - 0.5
    const r = q * q
    const num = (((((a[1] * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * r + a[6]) * q
    const den = (((((b[1] * r + b[2]) * r + b[3]) * r + b[4]) * r + b[5]) * r + 1)
    return num / den
  }
  q = Math.sqrt(-2 * Math.log(1 - p))
  const num = (((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]
  const den = ((d[0] * q + d[1]) * q + d[2]) * q + d[3]
  return -(num / den) * q - c[5]
}


function _theoreticalQuantiles(probabilities, dist, samples) {
  /*
   * Map probabilities to theoretical quantiles for the given distribution.
   * For distributions with parameters derived from samples (normal, lognormal)
   * we fit mean/std to the data.
   *
   * :returns: Array of theoretical quantile values.
   */
  const n = probabilities.length
  const result = []

  if (dist === "uniform") {
    const lo = Math.min(...samples)
    const hi = Math.max(...samples)
    for (let i = 0; i < n; i = i + 1) {
      result.push(lo + probabilities[i] * (hi - lo))
    }
    return result
  }

  if (dist === "exponential") {
    /* Fit rate = 1/mean. */
    let mean = 0
    for (let i = 0; i < samples.length; i = i + 1) { mean = mean + samples[i] }
    mean = mean / samples.length
    const rate = mean > 0 ? 1 / mean : 1
    for (let i = 0; i < n; i = i + 1) {
      const p = Math.max(probabilities[i], 1e-9)
      result.push(-Math.log(1 - p) / rate)
    }
    return result
  }

  if (dist === "lognormal") {
    /* Fit mu/sigma of log(X). */
    const logSamples = samples.filter((v) => v > 0).map((v) => Math.log(v))
    let mu = 0
    for (let i = 0; i < logSamples.length; i = i + 1) { mu = mu + logSamples[i] }
    mu = mu / logSamples.length
    let sig2 = 0
    for (let i = 0; i < logSamples.length; i = i + 1) {
      const d = logSamples[i] - mu
      sig2 = sig2 + d * d
    }
    const sigma = logSamples.length > 1 ? Math.sqrt(sig2 / (logSamples.length - 1)) : 1
    for (let i = 0; i < n; i = i + 1) {
      result.push(Math.exp(mu + sigma * _normalPPF(probabilities[i])))
    }
    return result
  }

  /* Default: normal. */
  let mean = 0
  for (let i = 0; i < samples.length; i = i + 1) { mean = mean + samples[i] }
  mean = mean / samples.length
  let variance = 0
  for (let i = 0; i < samples.length; i = i + 1) {
    const d = samples[i] - mean
    variance = variance + d * d
  }
  const std = samples.length > 1 ? Math.sqrt(variance / (samples.length - 1)) : 1

  for (let i = 0; i < n; i = i + 1) {
    result.push(mean + std * _normalPPF(probabilities[i]))
  }
  return result
}


/* ── main render ─────────────────────────────────────────────────────────── */

export function render(ctx) {
  /*
   * Render a Q-Q plot.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const model = ctx.model
  const theoreticalAttr = ctx.attrs("theoretical", "normal")

  const root = svgEl("g", { part: "plot" }, [])

  const series = model.series
  if (series === null || series === undefined || series.length === 0) {
    return root
  }

  /* Determine mode: two-sample empirical vs one-sample vs theoretical. */
  const twoSample = series.length >= 2 &&
    Array.isArray(series[1].samples) && series[1].samples.length > 0

  /* ── Build QQ point pairs ── */
  let qqPairs = []   /* array of { theor, obs, seriesIndex } */

  if (twoSample === true) {
    /* Align by interpolating shorter onto the longer's probability points. */
    const s0 = series[0].samples.slice().sort((a, b) => a - b)
    const s1 = series[1].samples.slice().sort((a, b) => a - b)
    const n = Math.max(s0.length, s1.length)
    for (let i = 0; i < n; i = i + 1) {
      const p = (i + 0.5) / n
      const q0 = _quantile(s0, p)
      const q1 = _quantile(s1, p)
      qqPairs.push({ theor: q0, obs: q1, seriesIndex: 0 })
    }
  } else {
    for (let si = 0; si < series.length; si = si + 1) {
      const s = series[si]
      if (Array.isArray(s.samples) === false || s.samples.length === 0) { continue }
      const sorted = s.samples.slice().sort((a, b) => a - b)
      const n = sorted.length
      const probs = []
      for (let i = 0; i < n; i = i + 1) {
        probs.push((i + 0.5) / n)
      }
      const dist = s.theoretical || theoreticalAttr
      const theorQs = _theoreticalQuantiles(probs, dist, sorted)
      for (let i = 0; i < n; i = i + 1) {
        qqPairs.push({ theor: theorQs[i], obs: sorted[i], seriesIndex: si })
      }
    }
  }

  if (qqPairs.length === 0) {
    return root
  }

  /* Compute axis extents with symmetric domain expansion for diagonal. */
  let xMin = Infinity, xMax = -Infinity
  let yMin = Infinity, yMax = -Infinity
  for (let i = 0; i < qqPairs.length; i = i + 1) {
    const p = qqPairs[i]
    if (p.theor < xMin) { xMin = p.theor }
    if (p.theor > xMax) { xMax = p.theor }
    if (p.obs < yMin) { yMin = p.obs }
    if (p.obs > yMax) { yMax = p.obs }
  }
  const domainMin = Math.min(xMin, yMin)
  const domainMax = Math.max(xMax, yMax)
  const domainPad = (domainMax - domainMin) * 0.08 || 0.5
  const axisDomainMin = domainMin - domainPad
  const axisDomainMax = domainMax + domainPad

  const margin = { top: 16, right: 24, bottom: 48, left: 56 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  const xScale = linearScale([axisDomainMin, axisDomainMax], [0, plotW])
  const yScale = linearScale([axisDomainMin, axisDomainMax], [plotH, 0])

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  /* Gridlines + tick labels. */
  const xTicks = niceTicks(axisDomainMin, axisDomainMax, 5)
  for (let ti = 0; ti < xTicks.length; ti = ti + 1) {
    const tick = xTicks[ti]
    const x = xScale(tick)
    plot.appendChild(svgEl("line", {
      x1: x, y1: 0, x2: x, y2: plotH,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    plot.appendChild(svgEl("text", {
      x: x, y: plotH + 16, "text-anchor": "middle",
      "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
    }, formatNumber(tick)))
  }

  const yTicks = niceTicks(axisDomainMin, axisDomainMax, 5)
  for (let ti = 0; ti < yTicks.length; ti = ti + 1) {
    const tick = yTicks[ti]
    const y = yScale(tick)
    plot.appendChild(svgEl("line", {
      x1: 0, y1: y, x2: plotW, y2: y,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    plot.appendChild(svgEl("text", {
      x: -8, y: y + 4, "text-anchor": "end",
      "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
    }, formatNumber(tick)))
  }

  /* 45° reference line (y = x). */
  const diagX0 = xScale(axisDomainMin)
  const diagY0 = yScale(axisDomainMin)
  const diagX1 = xScale(axisDomainMax)
  const diagY1 = yScale(axisDomainMax)
  plot.appendChild(svgEl("line", {
    x1: diagX0, y1: diagY0, x2: diagX1, y2: diagY1,
    stroke: "var(--mj-text-muted, #6b7280)",
    "stroke-width": 1.5, "stroke-dasharray": "6 3"
  }, []))

  /* X-axis label. */
  const xLabel = twoSample ? series[0].name : "Theoretical Quantiles"
  plot.appendChild(svgEl("text", {
    x: plotW / 2, y: plotH + 36, "text-anchor": "middle",
    "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
  }, xLabel))

  /* Y-axis label. */
  const yLabel = twoSample ? series[1].name : "Sample Quantiles"
  const yLabelEl = svgEl("text", {
    x: 0, y: 0, "text-anchor": "middle",
    "font-size": 11, fill: "var(--mj-text-muted, #6b7280)",
    transform: `translate(${-margin.left + 12},${plotH / 2}) rotate(-90)`
  }, yLabel)
  plot.appendChild(yLabelEl)

  /* Scatter points. */
  for (let i = 0; i < qqPairs.length; i = i + 1) {
    const pair = qqPairs[i]
    const color = ctx.colorFor(pair.seriesIndex)
    const cx = xScale(pair.theor)
    const cy = yScale(pair.obs)

    const dot = svgEl("circle", {
      cx: cx, cy: cy, r: 4,
      fill: color, opacity: 0.75
    }, [])
    dot.setAttribute("part", "qq-point")
    dot.setAttribute("tabindex", "0")
    dot.setAttribute("role", "img")
    dot.setAttribute("aria-label",
      `theoretical: ${formatNumber(pair.theor)}, observed: ${formatNumber(pair.obs)}`)
    dot.appendChild(svgEl("title", null,
      `theoretical: ${formatNumber(pair.theor)}\nobserved: ${formatNumber(pair.obs)}`))
    const handlerPair = pair
    const handlerSeries = series[pair.seriesIndex]
    const clickHandler = () => {
      ctx.emit("mj-chart-qq-click", {
        series: handlerSeries.name,
        theoretical: handlerPair.theor,
        observed: handlerPair.obs
      })
    }
    dot.addEventListener("click", clickHandler)
    dot.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault()
        clickHandler()
      }
    })
    plot.appendChild(dot)
  }

  return root
}


registerRenderer("qq", render)
