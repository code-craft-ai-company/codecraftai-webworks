/*
 * diststats.js
 *
 * Shared statistics, layout and drawing helpers for the distribution and
 * relationship renderers (histogram, boxplot, violin, strip / swarm, rug,
 * dot-histogram, ridgeline, qq, cdf, scatter, heatmap, density-2d /
 * contour, hexbin, splom, beeswarm). This module registers no chart type.
 *
 * Statistics
 *   finiteValues, sortNumbers, quantileSorted, meanOf, sampleStdDev,
 *   summarize (five-number summary + Tukey fences), silvermanBandwidth,
 *   gaussianDensity, linspace, binEdges, countBins, normalQuantile
 *
 * Layout
 *   placeSwarm (collision-free 1-D dot placement, ties kept apart),
 *   swarmRadius (the dot radius a band can hold),
 *   groupCategories, collectGroupSamples, hasGroupData, hasSeriesSamples
 *
 * Drawing (all decoration is aria-hidden; marks are drawn by the callers)
 *   fitDomain, axisLayer, drawTicks, drawCategoryLabels, drawAxisTitle, drawBaseline,
 *   tickCount, fitText, sequentialColor, divergingColor, drawColorRamp,
 *   activateOnKey
 *
 * Every statistic ignores values that are not finite numbers: null,
 * undefined, NaN, Infinity and non-numeric text are missing data, never
 * zero.
 */

import { svgEl, formatNumber } from "../svgdraw.js";
import { niceTicks, niceDomain, seriesColor } from "../scales.js";

/* Text colours used for tick labels and axis titles. */
export const TEXT_COLOR = "var(--mj-text, #14181f)";
export const MUTED_TEXT_COLOR = "var(--mj-text-muted, #6b7280)";
export const GRID_COLOR = "var(--mj-border, #e0e3e9)";
export const AXIS_COLOR = "var(--mj-border-strong, #c7ccd6)";
export const SURFACE_COLOR = "var(--mj-surface, #ffffff)";

/* Average glyph advance of the 11px chart font, as a share of its size. */
const GLYPH_WIDTH_RATIO = 0.58;

/* Upper bound on generated bins, so a tiny bin-width cannot hang a render. */
const BIN_LIMIT = 500;

/* Ramps start at this share of the hue so the lowest step stays visible. */
const RAMP_FLOOR_PERCENT = 22;

/* Number of colour steps a ramp is quantised to. */
const RAMP_STEPS = 16;

/* Coefficients of Acklam's rational approximation to the normal quantile. */
const ACKLAM_A = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
  1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00];
const ACKLAM_B = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
  6.680131188771972e+01, -1.328068155288572e+01];
const ACKLAM_C = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
  -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00];
const ACKLAM_D = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
  3.754408661907416e+00];
const ACKLAM_P_LOW = 0.02425;


/* ── statistics ──────────────────────────────────────────────────────────── */

export function isFiniteNumber(value) {
  /*
   * True for a number that is not NaN or +/-Infinity.
   */
  const finite = typeof value === "number" && Number.isFinite(value) === true
  return finite
}


export function finiteValues(list) {
  /*
   * The finite numbers of a list, in their original order.
   *
   * :param list: Any value; a non-array gives an empty result.
   * :returns: A new array holding only finite numbers.
   */
  const values = []
  if (Array.isArray(list) === false) {
    return values
  }
  for (let index = 0; index < list.length; index = index + 1) {
    if (isFiniteNumber(list[index]) === true) {
      values.push(list[index])
    }
  }
  return values
}


export function sortNumbers(values) {
  /*
   * A sorted copy (ascending) of the finite numbers of a list.
   */
  const sorted = finiteValues(values)
  sorted.sort((a, b) => a - b)
  return sorted
}


export function quantileSorted(sorted, probability) {
  /*
   * Linear-interpolation quantile (Hyndman & Fan type 7, the default of R,
   * NumPy and Python's statistics.quantiles(method="inclusive")).
   *
   * :param sorted: Ascending finite numbers.
   * :param probability: A probability in [0, 1].
   * :returns: The quantile, or null for an empty list.
   */
  const n = sorted.length
  if (n === 0) {
    return null
  }
  if (n === 1) {
    return sorted[0]
  }
  const p = Math.max(0, Math.min(1, probability))
  const position = p * (n - 1)
  const lower = Math.floor(position)
  const upper = Math.ceil(position)
  const fraction = position - lower
  const value = sorted[lower] + (sorted[upper] - sorted[lower]) * fraction
  return value
}


export function meanOf(values) {
  /*
   * Arithmetic mean of finite numbers, or null when there are none.
   */
  if (values.length === 0) {
    return null
  }
  let total = 0
  for (let index = 0; index < values.length; index = index + 1) {
    total = total + values[index]
  }
  const mean = total / values.length
  return mean
}


export function sampleStdDev(values) {
  /*
   * Sample standard deviation (n - 1 denominator); 0 for fewer than two
   * values.
   */
  const n = values.length
  if (n < 2) {
    return 0
  }
  const mean = meanOf(values)
  let squares = 0
  for (let index = 0; index < n; index = index + 1) {
    const diff = values[index] - mean
    squares = squares + diff * diff
  }
  const deviation = Math.sqrt(squares / (n - 1))
  return deviation
}


export function summarize(values, iqrMultiplier) {
  /*
   * Five-number summary with Tukey fences.
   *
   * :param values: Samples (non-finite entries are ignored).
   * :param iqrMultiplier: Fence distance in IQRs (1.5 when not positive).
   * :returns: { count, min, max, q1, median, q3, mean, whiskerLow,
   *     whiskerHigh, outliers } where whiskerLow / whiskerHigh are the most
   *     extreme samples inside the fences; null when there is no sample.
   */
  const sorted = sortNumbers(values)
  if (sorted.length === 0) {
    return null
  }
  const multiplier = isFiniteNumber(iqrMultiplier) === true && iqrMultiplier > 0
    ? iqrMultiplier : 1.5

  const q1 = quantileSorted(sorted, 0.25)
  const median = quantileSorted(sorted, 0.5)
  const q3 = quantileSorted(sorted, 0.75)
  const fence = multiplier * (q3 - q1)
  const lowFence = q1 - fence
  const highFence = q3 + fence

  let whiskerLow = q1
  let whiskerHigh = q3
  const outliers = []
  for (let index = 0; index < sorted.length; index = index + 1) {
    const value = sorted[index]
    if (value < lowFence || value > highFence) {
      outliers.push(value)
    }
  }
  for (let index = 0; index < sorted.length; index = index + 1) {
    if (sorted[index] >= lowFence) {
      whiskerLow = Math.min(sorted[index], q1)
      break
    }
  }
  for (let index = sorted.length - 1; index >= 0; index = index - 1) {
    if (sorted[index] <= highFence) {
      whiskerHigh = Math.max(sorted[index], q3)
      break
    }
  }

  const summary = {
    count: sorted.length,
    min: sorted[0],
    max: sorted[sorted.length - 1],
    q1: q1,
    median: median,
    q3: q3,
    mean: meanOf(sorted),
    whiskerLow: whiskerLow,
    whiskerHigh: whiskerHigh,
    outliers: outliers
  }
  return summary
}


export function silvermanBandwidth(values) {
  /*
   * Silverman's rule-of-thumb bandwidth for a Gaussian KDE:
   * 0.9 * min(sd, IQR / 1.34) * n^(-1/5).
   *
   * When more than half the samples tie (IQR = 0) the standard deviation
   * alone is used; when every sample is equal a bandwidth relative to the
   * magnitude of the data is returned, so the result is never a constant
   * that ignores the data's scale.
   *
   * :returns: A positive bandwidth.
   */
  const sorted = sortNumbers(values)
  const n = sorted.length
  const deviation = sampleStdDev(sorted)
  const iqr = n > 0 ? quantileSorted(sorted, 0.75) - quantileSorted(sorted, 0.25) : 0

  let spread = 0
  if (deviation > 0 && iqr > 0) {
    spread = Math.min(deviation, iqr / 1.34)
  } else if (deviation > 0) {
    spread = deviation
  }

  let bandwidth = 0
  if (spread > 0) {
    bandwidth = 0.9 * spread * Math.pow(n, -0.2)
  } else {
    const magnitude = n > 0 ? Math.abs(sorted[0]) : 0
    bandwidth = magnitude > 0 ? magnitude * 0.05 : 0.5
  }
  return bandwidth
}


export function gaussianDensity(values, bandwidth, points) {
  /*
   * Gaussian kernel density estimate f(x) = 1 / (n h) * sum K((x - xi) / h).
   *
   * :param values: Finite samples.
   * :param bandwidth: The kernel bandwidth h (> 0).
   * :param points: The x positions to evaluate at.
   * :returns: An array of densities parallel to `points` (zeros when there
   *     is no sample).
   */
  const n = values.length
  const norm = 1 / (Math.sqrt(2 * Math.PI) * bandwidth * Math.max(n, 1))
  const densities = []
  for (let pi = 0; pi < points.length; pi = pi + 1) {
    const x = points[pi]
    let sum = 0
    for (let si = 0; si < n; si = si + 1) {
      const u = (x - values[si]) / bandwidth
      sum = sum + Math.exp(-0.5 * u * u)
    }
    densities.push(n > 0 ? sum * norm : 0)
  }
  return densities
}


export function linspace(low, high, count) {
  /*
   * `count` evenly spaced values from low to high inclusive.
   */
  const values = []
  const total = Math.max(Math.floor(count), 1)
  const step = total > 1 ? (high - low) / (total - 1) : 0
  for (let index = 0; index < total; index = index + 1) {
    values.push(low + index * step)
  }
  return values
}


function _binCountFor(sorted, method) {
  /*
   * The number of equal-width bins a rule asks for.
   *
   * :param method: "sturges" (default), "scott" or "fd" (Freedman-Diaconis).
   */
  const n = sorted.length
  const span = sorted[n - 1] - sorted[0]
  const sturges = Math.max(Math.ceil(Math.log2(Math.max(n, 1)) + 1), 1)

  let width = 0
  if (method === "scott") {
    width = 3.49 * sampleStdDev(sorted) * Math.pow(n, -1 / 3)
  } else if (method === "fd" || method === "freedman-diaconis") {
    const iqr = quantileSorted(sorted, 0.75) - quantileSorted(sorted, 0.25)
    width = 2 * iqr * Math.pow(n, -1 / 3)
  }

  let count = sturges
  if (width > 0 && span > 0) {
    count = Math.ceil(span / width)
  }
  return Math.max(Math.min(count, BIN_LIMIT), 1)
}


export function binEdges(values, options) {
  /*
   * Equal-width bin edges covering every finite value. All series of one
   * chart are binned with the same edges, so their bars line up and stack.
   *
   * :param values: The pooled samples of every series.
   * :param options: { count, width, method } -- an explicit positive bin
   *     width wins over a count, a count over the rule `method`.
   * :returns: Ascending edges (bin i is [edges[i], edges[i + 1]), the last
   *     bin also holds its upper edge); [] when there is no finite value.
   */
  const sorted = sortNumbers(values)
  if (sorted.length === 0) {
    return []
  }
  const given = options !== null && options !== undefined ? options : {}
  const low = sorted[0]
  const high = sorted[sorted.length - 1]

  if (low === high) {
    /* One bin centred on the single value. */
    const half = Math.abs(low) > 0 ? Math.abs(low) * 0.05 : 0.5
    return [low - half, low + half]
  }

  const edges = []
  if (isFiniteNumber(given.width) === true && given.width > 0) {
    /* Values on the width's grid (whole counts with width 1) get bins
     * centred on them, so a dot or bar sits over its value. */
    const onGrid = sorted.every((value) => Math.abs(value / given.width - Math.round(value / given.width)) < 1e-9)
    const start = onGrid === true ? low - given.width / 2 : Math.floor(low / given.width) * given.width
    let count = Math.ceil((high - start) / given.width)
    if (start + count * given.width <= high) {
      count = count + 1
    }
    count = Math.max(Math.min(count, BIN_LIMIT), 1)
    for (let index = 0; index <= count; index = index + 1) {
      edges.push(start + index * given.width)
    }
    return edges
  }

  let count = 0
  if (isFiniteNumber(given.count) === true && given.count >= 1) {
    count = Math.min(Math.floor(given.count), BIN_LIMIT)
  } else {
    count = _binCountFor(sorted, given.method)
  }
  const width = (high - low) / count
  for (let index = 0; index <= count; index = index + 1) {
    edges.push(index === count ? high : low + index * width)
  }
  return edges
}


export function countBins(values, edges) {
  /*
   * Count finite values into bins defined by ascending edges.
   *
   * :returns: [{ x0, x1, count }] -- values outside the edges are not
   *     counted; a value equal to the last edge goes into the last bin.
   */
  const bins = []
  for (let index = 0; index + 1 < edges.length; index = index + 1) {
    bins.push({ x0: edges[index], x1: edges[index + 1], count: 0 })
  }
  if (bins.length === 0) {
    return bins
  }
  const last = edges[edges.length - 1]
  for (let vi = 0; vi < values.length; vi = vi + 1) {
    const value = values[vi]
    if (isFiniteNumber(value) === false || value < edges[0] || value > last) {
      continue
    }
    /* Binary search for the bin whose lower edge is the last <= value. */
    let lo = 0
    let hi = bins.length - 1
    while (lo < hi) {
      const mid = Math.ceil((lo + hi) / 2)
      if (edges[mid] <= value) {
        lo = mid
      } else {
        hi = mid - 1
      }
    }
    bins[lo].count = bins[lo].count + 1
  }
  return bins
}


export function normalQuantile(probability) {
  /*
   * Standard normal quantile (probit), Acklam's algorithm (relative error
   * below 1.2e-9 over the open interval).
   *
   * :param probability: p in (0, 1).
   * :returns: z with P(Z <= z) = p; -Infinity / Infinity at 0 / 1, NaN
   *     outside [0, 1].
   */
  const p = probability
  if (isFiniteNumber(p) === false || p < 0 || p > 1) {
    return NaN
  }
  if (p === 0) {
    return -Infinity
  }
  if (p === 1) {
    return Infinity
  }

  let z = 0
  if (p < ACKLAM_P_LOW || p > 1 - ACKLAM_P_LOW) {
    const tail = p < ACKLAM_P_LOW ? p : 1 - p
    const q = Math.sqrt(-2 * Math.log(tail))
    const c = ACKLAM_C
    const d = ACKLAM_D
    const numerator = ((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]
    const denominator = (((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1
    z = numerator / denominator
    if (p > 1 - ACKLAM_P_LOW) {
      z = -z
    }
  } else {
    const q = p - 0.5
    const r = q * q
    const a = ACKLAM_A
    const b = ACKLAM_B
    const numerator = (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q
    const denominator = ((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1
    z = numerator / denominator
  }
  return z
}


export function validBins(list) {
  /*
   * The usable entries of a pre-binned series: finite x0 < x1 and a finite,
   * non-negative count; sorted by x0.
   */
  const bins = []
  if (Array.isArray(list) === false) {
    return bins
  }
  for (let index = 0; index < list.length; index = index + 1) {
    const bin = list[index]
    if (bin === null || typeof bin !== "object") {
      continue
    }
    const x0 = Number(bin.x0)
    const x1 = Number(bin.x1)
    const count = Number(bin.count)
    if (isFiniteNumber(x0) === false || isFiniteNumber(x1) === false ||
        isFiniteNumber(count) === false || x1 <= x0 || count < 0) {
      continue
    }
    bins.push({ x0: x0, x1: x1, count: count })
  }
  bins.sort((a, b) => a.x0 - b.x0)
  return bins
}


export function binSeries(series, options) {
  /*
   * Bin every series of a chart with one shared set of edges.
   *
   * :param series: The visible model series.
   * :param options: { count, width, method } (see binEdges).
   * :returns: { series: [{ name, samples, bins, total, preBinned }], edges }
   *     -- `samples` are the finite samples (null for a pre-binned series),
   *     `total` the number of observations.
   */
  const pooled = []
  for (let si = 0; si < series.length; si = si + 1) {
    const entry = series[si]
    if (validBins(entry.bins).length === 0) {
      const samples = finiteValues(entry.samples)
      for (let vi = 0; vi < samples.length; vi = vi + 1) {
        pooled.push(samples[vi])
      }
    }
  }
  const edges = binEdges(pooled, options)

  const resolved = []
  for (let si = 0; si < series.length; si = si + 1) {
    const entry = series[si]
    const given = validBins(entry.bins)
    let bins = []
    let samples = null
    if (given.length > 0) {
      bins = given
    } else {
      samples = finiteValues(entry.samples)
      bins = samples.length > 0 ? countBins(samples, edges) : []
    }
    let total = 0
    for (let bi = 0; bi < bins.length; bi = bi + 1) {
      total = total + bins[bi].count
    }
    resolved.push({
      name: entry.name,
      samples: samples,
      bins: bins,
      total: total,
      preBinned: given.length > 0
    })
  }
  const result = { series: resolved, edges: edges }
  return result
}


/* ── layout ──────────────────────────────────────────────────────────────── */

export function placeSwarm(positions, diameter, maxOffset) {
  /*
   * Collision-free dot placement along one axis (beeswarm / swarm).
   *
   * Dots are visited in order of position. Every dot already placed closer
   * than one diameter along the axis (a sliding window over the sorted
   * order) forbids an interval of offsets around its own; the new dot
   * takes the free offset nearest the centre line. Ties therefore stack
   * side by side, and the cost is O(n * w log w) for a window of w dots.
   *
   * :param positions: Pixel positions along the value axis, one per dot.
   * :param diameter: Minimum centre distance between two dots.
   * :param maxOffset: Largest allowed |offset| from the centre line.
   * :returns: { offsets, overflow } -- `offsets[i]` belongs to
   *     positions[i] (each tied value gets its own offset); `overflow`
   *     counts the dots that found no free slot within maxOffset and were
   *     spread over the band deterministically instead.
   */
  const count = positions.length
  const offsets = new Array(count).fill(0)
  const order = []
  for (let index = 0; index < count; index = index + 1) {
    order.push(index)
  }
  order.sort((a, b) => positions[a] - positions[b] || a - b)

  const limit = Math.max(maxOffset, 0)
  const placedPos = []
  const placedOff = []
  let windowStart = 0
  let overflow = 0

  for (let oi = 0; oi < order.length; oi = oi + 1) {
    const index = order[oi]
    const position = positions[index]
    while (windowStart < placedPos.length && placedPos[windowStart] <= position - diameter) {
      windowStart = windowStart + 1
    }

    /* Forbidden offset intervals, merged into disjoint runs. */
    const blocked = []
    for (let pj = windowStart; pj < placedPos.length; pj = pj + 1) {
      const dx = position - placedPos[pj]
      const reach = Math.sqrt(Math.max(diameter * diameter - dx * dx, 0))
      if (reach > 0) {
        blocked.push([placedOff[pj] - reach, placedOff[pj] + reach])
      }
    }
    blocked.sort((a, b) => a[0] - b[0])
    const runs = []
    for (let bi = 0; bi < blocked.length; bi = bi + 1) {
      const last = runs.length > 0 ? runs[runs.length - 1] : null
      if (last !== null && blocked[bi][0] < last[1]) {
        last[1] = Math.max(last[1], blocked[bi][1])
      } else {
        runs.push([blocked[bi][0], blocked[bi][1]])
      }
    }

    /* The free offset nearest 0: 0 itself, or an end of the run holding 0. */
    let chosen = 0
    for (let ri = 0; ri < runs.length; ri = ri + 1) {
      if (runs[ri][0] < 0 && runs[ri][1] > 0) {
        chosen = Math.abs(runs[ri][1]) <= Math.abs(runs[ri][0]) ? runs[ri][1] : runs[ri][0]
        break
      }
    }
    if (Math.abs(chosen) > limit + 1e-9) {
      /* Try the other end of the same run before giving up. */
      const run = runs.find((candidate) => candidate[0] < 0 && candidate[1] > 0)
      const other = run !== undefined ? (chosen === run[1] ? run[0] : run[1]) : chosen
      chosen = Math.abs(other) <= limit + 1e-9 ? other : null
    }

    if (chosen === null) {
      /* The band is full here: spread the rest over it, deterministically. */
      overflow = overflow + 1
      const seed = Math.sin((index + 1) * 12.9898) * 43758.5453
      const unit = seed - Math.floor(seed)
      chosen = (unit * 2 - 1) * limit
    }
    offsets[index] = chosen
    placedPos.push(position)
    placedOff.push(chosen)
  }

  const result = { offsets: offsets, overflow: overflow }
  return result
}


export function swarmRadius(positions, radius, padding, maxOffset, minRadius) {
  /*
   * The largest dot radius (at most `radius`, at least `minRadius`) whose
   * densest pile still fits the band: k dots lying within one diameter of
   * each other along the axis need about (k - 1) * 0.75 diameters across
   * it. One O(n log n) pass per candidate radius, no trial placements.
   *
   * :param padding: Gap between dots in px (diameter = 2 r + padding).
   * :returns: The radius to place with.
   */
  const sorted = positions.slice().sort((a, b) => a - b)
  const room = 2 * Math.max(maxOffset, 0)
  let size = radius
  while (size > minRadius) {
    const diameter = size * 2 + padding
    let densest = 0
    let start = 0
    for (let end = 0; end < sorted.length; end = end + 1) {
      while (sorted[end] - sorted[start] >= diameter) {
        start = start + 1
      }
      densest = Math.max(densest, end - start + 1)
    }
    if ((densest - 1) * diameter * 0.75 <= room) {
      break
    }
    size = Math.max(size * 0.85, minRadius)
  }
  return size
}


export function groupCategories(model) {
  /*
   * The category order of grouped data (series[].groups[].category): the
   * top-level `categories` when given, else every group category in order
   * of first appearance.
   */
  if (Array.isArray(model.categories) === true && model.categories.length > 0) {
    return model.categories.slice()
  }
  const seen = new Set()
  const categories = []
  const series = Array.isArray(model.series) === true ? model.series : []
  for (let si = 0; si < series.length; si = si + 1) {
    const groups = Array.isArray(series[si].groups) === true ? series[si].groups : []
    for (let gi = 0; gi < groups.length; gi = gi + 1) {
      const group = groups[gi]
      if (group === null || typeof group !== "object") {
        continue
      }
      const key = group.category === undefined || group.category === null
        ? "" : String(group.category)
      if (seen.has(key) === false) {
        seen.add(key)
        categories.push(group.category === undefined ? key : group.category)
      }
    }
  }
  return categories
}


export function seriesGroups(entry) {
  /*
   * The groups of one series that are objects, never null.
   */
  const groups = []
  const list = entry !== null && entry !== undefined && Array.isArray(entry.groups) === true
    ? entry.groups : []
  for (let index = 0; index < list.length; index = index + 1) {
    if (list[index] !== null && typeof list[index] === "object") {
      groups.push(list[index])
    }
  }
  return groups
}


export function hasGroupData(model, samplesOnly) {
  /*
   * True when any group of any series has a finite sample or (unless
   * `samplesOnly`) a numeric pre-computed median. Used as the registered
   * isEmpty test of the grouped types.
   */
  const series = Array.isArray(model.allSeries) === true ? model.allSeries : model.series
  for (let si = 0; si < series.length; si = si + 1) {
    const groups = seriesGroups(series[si])
    for (let gi = 0; gi < groups.length; gi = gi + 1) {
      if (samplesOnly !== true && isFiniteNumber(groups[gi].median) === true) {
        return true
      }
      if (finiteValues(groups[gi].samples).length > 0) {
        return true
      }
    }
  }
  return false
}


export function hasSeriesSamples(model) {
  /*
   * True when any series has a finite sample or a counted bin (used as the
   * registered isEmpty test of the samples / bins types).
   */
  const series = Array.isArray(model.allSeries) === true ? model.allSeries : model.series
  for (let si = 0; si < series.length; si = si + 1) {
    if (finiteValues(series[si].samples).length > 0) {
      return true
    }
    const bins = Array.isArray(series[si].bins) === true ? series[si].bins : []
    for (let bi = 0; bi < bins.length; bi = bi + 1) {
      const bin = bins[bi]
      if (bin !== null && typeof bin === "object" && isFiniteNumber(bin.x0) === true &&
          isFiniteNumber(bin.x1) === true && isFiniteNumber(bin.count) === true) {
        return true
      }
    }
  }
  return false
}


/* ── drawing ─────────────────────────────────────────────────────────────── */

export function fitDomain(low, high, count) {
  /*
   * An axis domain for [low, high]: widened to tick boundaries when that
   * costs little room, else the data range itself (a coarse step on a
   * narrow axis could otherwise waste most of the plot).
   *
   * :returns: [low, high] of the axis.
   */
  const nice = niceDomain(low, high, count)
  const span = high - low
  if (span > 0 && nice[1] - nice[0] > span * 1.3) {
    return [low, high]
  }
  return nice
}


export function axisLayer(parent) {
  /*
   * Append a group for axes, gridlines and tick labels. It is aria-hidden
   * so assistive technology reads the marks and the data table, not every
   * tick number.
   */
  const layer = svgEl("g", { part: "axis", "aria-hidden": "true" }, [])
  parent.appendChild(layer)
  return layer
}


export function tickCount(lengthPx, spacingPx) {
  /*
   * A tick count that keeps labels about `spacingPx` apart.
   */
  const spacing = spacingPx > 0 ? spacingPx : 60
  const count = Math.max(Math.min(Math.floor(lengthPx / spacing), 10), 2)
  return count
}


export function fitText(text, maxPx, fontSize) {
  /*
   * Shorten a label with an ellipsis so it fits about `maxPx` pixels.
   *
   * :returns: The label, or a shortened copy ending in "…".
   */
  const label = String(text === null || text === undefined ? "" : text)
  const size = fontSize > 0 ? fontSize : 11
  const capacity = Math.floor(Math.max(maxPx, 0) / (size * GLYPH_WIDTH_RATIO))
  if (label.length <= capacity) {
    return label
  }
  if (capacity <= 1) {
    return "…"
  }
  const shortened = label.slice(0, capacity - 1) + "…"
  return shortened
}


export function drawTicks(layer, scale, options) {
  /*
   * Gridlines and tick labels for a continuous scale.
   *
   * :param layer: The (aria-hidden) axis group.
   * :param scale: A linear scale.
   * :param options: {
   *     side:    "left" | "bottom"
   *     extent:  plot height (bottom) or width (left) -- gridline length
   *     at:      position of the axis line: y of a bottom axis (default
   *              extent of the other dimension), x of a left axis (0)
   *     count:   about how many ticks (default 5)
   *     ticks:   explicit tick values (overrides count)
   *     grid:    draw gridlines (default true)
   *     format:  value -> label (default formatNumber)
   *   }
   */
  const side = options.side === "bottom" ? "bottom" : "left"
  const domain = scale.domain()
  const wanted = options.count > 0 ? options.count : 5
  let ticks = Array.isArray(options.ticks) === true ? options.ticks : niceTicks(domain[0], domain[1], wanted)
  if (Array.isArray(options.ticks) === false && ticks.length < 3) {
    /* A step rounded up (e.g. 20 -> 50) can leave only two ticks. */
    ticks = niceTicks(domain[0], domain[1], wanted * 2)
  }
  const format = typeof options.format === "function" ? options.format : (value) => formatNumber(value)
  const grid = options.grid !== false
  const gridLength = options.extent
  const at = isFiniteNumber(options.at) === true ? options.at : (side === "bottom" ? gridLength : 0)
  const low = Math.min(domain[0], domain[1])
  const high = Math.max(domain[0], domain[1])
  const tolerance = (high - low) * 1e-9

  for (let ti = 0; ti < ticks.length; ti = ti + 1) {
    const tick = ticks[ti]
    if (tick < low - tolerance || tick > high + tolerance) {
      continue
    }
    const pixel = scale(tick)
    if (side === "bottom") {
      if (grid === true) {
        layer.appendChild(svgEl("line", {
          x1: pixel, y1: 0, x2: pixel, y2: gridLength,
          stroke: GRID_COLOR, "stroke-width": 1
        }, []))
      }
      layer.appendChild(svgEl("text", {
        x: pixel, y: at + 16, "text-anchor": "middle",
        "font-size": 11, fill: MUTED_TEXT_COLOR
      }, format(tick)))
    } else {
      if (grid === true) {
        layer.appendChild(svgEl("line", {
          x1: 0, y1: pixel, x2: gridLength, y2: pixel,
          stroke: GRID_COLOR, "stroke-width": 1
        }, []))
      }
      layer.appendChild(svgEl("text", {
        x: at - 8, y: pixel + 4, "text-anchor": "end",
        "font-size": 11, fill: MUTED_TEXT_COLOR
      }, format(tick)))
    }
  }
  return
}


export function drawCategoryLabels(layer, labels, side, at, maxPx) {
  /*
   * Category labels along a band axis, shortened to fit their band.
   *
   * :param labels: [{ text, center }] -- `center` is the band midpoint.
   * :param side: "left" (labels right-aligned left of x = at) or "bottom"
   *     (labels centred below y = at).
   * :param maxPx: The room each label has.
   */
  for (let index = 0; index < labels.length; index = index + 1) {
    const entry = labels[index]
    const full = String(entry.text === null || entry.text === undefined ? "" : entry.text)
    const shown = fitText(full, maxPx, 11)
    let text = null
    if (side === "bottom") {
      text = svgEl("text", {
        x: entry.center, y: at + 18, "text-anchor": "middle",
        "font-size": 11, fill: TEXT_COLOR
      }, shown)
    } else {
      text = svgEl("text", {
        x: at - 8, y: entry.center + 4, "text-anchor": "end",
        "font-size": 11, fill: TEXT_COLOR
      }, shown)
    }
    if (shown !== full) {
      text.appendChild(svgEl("title", null, full))
    }
    layer.appendChild(text)
  }
  return
}


export function drawAxisTitle(layer, text, side, plotW, plotH, offset) {
  /*
   * An axis title: centred under the plot ("bottom") or rotated along the
   * left edge ("left"). `offset` is the distance from the plot edge.
   */
  if (text === null || text === undefined || String(text).length === 0) {
    return
  }
  if (side === "bottom") {
    layer.appendChild(svgEl("text", {
      x: plotW / 2, y: plotH + offset, "text-anchor": "middle",
      "font-size": 11, fill: MUTED_TEXT_COLOR
    }, fitText(text, plotW, 11)))
  } else {
    layer.appendChild(svgEl("text", {
      x: 0, y: 0, "text-anchor": "middle",
      "font-size": 11, fill: MUTED_TEXT_COLOR,
      transform: `translate(${-offset},${plotH / 2}) rotate(-90)`
    }, fitText(text, plotH, 11)))
  }
  return
}


export function drawBaseline(layer, x1, y1, x2, y2) {
  /*
   * A strong axis line from (x1, y1) to (x2, y2).
   */
  layer.appendChild(svgEl("line", {
    x1: x1, y1: y1, x2: x2, y2: y2,
    stroke: AXIS_COLOR, "stroke-width": 1.5
  }, []))
  return
}


function _rampPercent(fraction) {
  /*
   * The share of the hue (in %) for a [0, 1] ramp position, quantised to
   * RAMP_STEPS steps starting at RAMP_FLOOR_PERCENT.
   */
  const clamped = Math.max(0, Math.min(1, isFiniteNumber(fraction) === true ? fraction : 0))
  const stepIndex = Math.round(clamped * (RAMP_STEPS - 1))
  const percent = RAMP_FLOOR_PERCENT + (100 - RAMP_FLOOR_PERCENT) * stepIndex / (RAMP_STEPS - 1)
  return Math.round(percent)
}


export function sequentialColor(fraction) {
  /*
   * A single-hue sequential ramp: the first series hue mixed with the
   * surface colour. It follows the theme (light surfaces give pale lows,
   * dark surfaces give dark lows) and the lowest step keeps enough hue to
   * stand out from the surface. Text on any step uses var(--mj-text).
   *
   * :param fraction: Ramp position in [0, 1].
   * :returns: A CSS colour for a fill / stroke attribute.
   */
  const percent = _rampPercent(fraction)
  const color = `color-mix(in oklab, ${seriesColor(0)} ${percent}%, ${SURFACE_COLOR})`
  return color
}


export function divergingColor(position) {
  /*
   * A two-hue diverging ramp: blue for positive, red for negative, the
   * surface tint at 0; the colour deepens with |position| on both sides.
   *
   * :param position: A signed position in [-1, 1].
   * :returns: A CSS colour.
   */
  const value = Math.max(-1, Math.min(1, isFiniteNumber(position) === true ? position : 0))
  const magnitude = Math.abs(value)
  if (magnitude < 0.5 / RAMP_STEPS) {
    return `color-mix(in oklab, ${TEXT_COLOR} 8%, ${SURFACE_COLOR})`
  }
  const hue = value < 0 ? seriesColor(7) : seriesColor(0)
  const color = `color-mix(in oklab, ${hue} ${_rampPercent(magnitude)}%, ${SURFACE_COLOR})`
  return color
}


export function drawColorRamp(layer, options) {
  /*
   * A colour-bar legend: stepped swatches with labelled ends (and middle).
   *
   * :param layer: The (aria-hidden) group to draw into.
   * :param options: {
   *     x, y:       top-left corner
   *     length:     extent along the ramp in px
   *     thickness:  swatch thickness in px (default 10)
   *     vertical:   true for a top (high) to bottom (low) ramp
   *     colorAt:    fraction in [0, 1] -> colour
   *     labels:     [{ fraction, text }]
   *     title:      optional caption drawn before the ramp
   *   }
   */
  const steps = RAMP_STEPS
  const thickness = options.thickness > 0 ? options.thickness : 10
  const length = Math.max(options.length, steps)
  const unit = length / steps
  const group = svgEl("g", { part: "color-ramp" }, [])

  for (let index = 0; index < steps; index = index + 1) {
    const fraction = steps > 1 ? index / (steps - 1) : 0
    if (options.vertical === true) {
      group.appendChild(svgEl("rect", {
        x: options.x, y: options.y + length - (index + 1) * unit,
        width: thickness, height: unit + 0.5,
        fill: options.colorAt(fraction)
      }, []))
    } else {
      group.appendChild(svgEl("rect", {
        x: options.x + index * unit, y: options.y,
        width: unit + 0.5, height: thickness,
        fill: options.colorAt(fraction)
      }, []))
    }
  }

  const labels = Array.isArray(options.labels) === true ? options.labels : []
  for (let index = 0; index < labels.length; index = index + 1) {
    const label = labels[index]
    if (options.vertical === true) {
      group.appendChild(svgEl("text", {
        x: options.x + thickness + 4, y: options.y + length * (1 - label.fraction) + 4,
        "text-anchor": "start", "font-size": 10, fill: MUTED_TEXT_COLOR
      }, label.text))
    } else {
      let anchor = "middle"
      if (label.fraction <= 0) {
        anchor = "start"
      } else if (label.fraction >= 1) {
        anchor = "end"
      }
      group.appendChild(svgEl("text", {
        x: options.x + length * label.fraction, y: options.y + thickness + 11,
        "text-anchor": anchor, "font-size": 10, fill: MUTED_TEXT_COLOR
      }, label.text))
    }
  }

  if (typeof options.title === "string" && options.title.length > 0) {
    group.appendChild(svgEl("text", {
      x: options.x, y: options.y - (options.vertical === true ? 10 : 4), "text-anchor": "start",
      "font-size": 10, fill: MUTED_TEXT_COLOR
    }, options.title))
  }
  layer.appendChild(group)
  return
}


export function activateOnKey(element, handler) {
  /*
   * Run `handler` on click and on Enter / Space, the activation keys of a
   * focusable mark. Arrow keys are left to the controller's roving focus.
   */
  element.addEventListener("click", handler)
  element.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault()
      handler()
    }
  })
  return
}


export function focusableMark(element, label) {
  /*
   * Make a mark one stop of the chart's roving focus: tabindex, role="img",
   * an accessible name and a native tooltip with the same text.
   */
  element.setAttribute("tabindex", "0")
  element.setAttribute("role", "img")
  element.setAttribute("aria-label", label)
  element.appendChild(svgEl("title", null, label))
  return element
}
