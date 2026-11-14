/*
 * density.js
 *
 * 2D Density / Contour renderer. This module is the one "contour"
 * renderer of the library (contour.js keeps "surface").
 *
 * Registered chart types (ctx.type picks the default style):
 *   "density-2d" — filled density surface (style "fill" by default)
 *   "contour"    — iso-lines (style "contour" by default)
 *
 * Data shapes (either raw points or a pre-computed grid):
 *
 *   Raw points (a bivariate Gaussian KDE is computed here):
 *     series[].points: [{ x, y }, ...]       non-finite x / y are skipped
 *     density.bandwidth   "auto" (default: sigma_i * n^(-1/6) per axis,
 *                         the d = 2 normal-reference rule) | number
 *     density.resolution  grid nodes per axis (8–128, default 32)
 *   Pre-computed grid (KDE skipped):
 *     grid: { x: [...], y: [...], z: [[row0], [row1], ...] }  z[i][j] is the
 *     value at (x[j], y[i]); non-finite z values are holes
 *
 *   Options (either type):
 *     density.style     "fill" | "contour" | "both"
 *     density.levels    number of iso-levels (3–20, default 8) or an
 *                       array of level values
 *     levels            an array of level values (same as above)
 *     fill              true — contour type also fills the surface
 *     meta.xLabel / meta.yLabel   axis titles
 *
 * The KDE grid holds a true density (the kernel sum divided by n) and is
 * computed in data space, so it is cached per data object and options and
 * reused on resize. Iso-lines come from marching squares (saddles resolved
 * by the cell's centre value) and are joined into one <path> per level,
 * labelled with the level value. The surface is drawn edge to edge inside
 * the plot, one rect per run of equal colour per row.
 *
 * Relevant ctx.attrs (an attribute wins over the matching data option):
 *   density-style   "fill" | "contour" | "both"; overrides density.style
 *   max-points      points used for the KDE (default 2000; larger sets are
 *                   thinned evenly)
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber } from "../svgdraw.js";
import { linearScale } from "../scales.js";
import {
  isFiniteNumber, sampleStdDev, linspace, axisLayer, drawTicks, drawAxisTitle, drawBaseline,
  tickCount, sequentialColor, drawColorRamp, activateOnKey, focusableMark, TEXT_COLOR,
  SURFACE_COLOR, MUTED_TEXT_COLOR
} from "./diststats.js";

const RAMP_ROOM = 72;
const COLOR_STEPS = 16;

/* data object -> Map(signature -> grid) */
const GRID_CACHE = new WeakMap();


const DENSITY_STYLES = ["fill", "contour", "both"];


function _densityStyle(ctx, rawDensity, raw, isContour) {
  /*
   * The drawing style. The host attribute wins over the data (like every
   * other option attribute): `density-style`, else `density.style`, else
   * `fill: true` on a contour chart ("both"), else the type default.
   *
   * :param ctx: The renderer context.
   * :param rawDensity: The data's `density` options object.
   * :param raw: The raw data.
   * :param isContour: Whether the chart type is "contour".
   * :returns: "fill" | "contour" | "both".
   */
  let style = isContour === true ? "contour" : "fill"
  const fromAttr = String(ctx.attrs("density-style", "")).trim().toLowerCase()
  if (DENSITY_STYLES.indexOf(fromAttr) >= 0) {
    style = fromAttr
  } else if (DENSITY_STYLES.indexOf(rawDensity.style) >= 0) {
    style = rawDensity.style
  } else if (isContour === true && raw.fill === true) {
    style = "both"
  }
  return style
}


/* ── density grid ────────────────────────────────────────────────────────── */

function _bandwidth(values, n) {
  /*
   * Per-axis bandwidth of the bivariate normal-reference rule,
   * sigma * n^(-1/6); a magnitude-relative value when sigma is 0.
   */
  const sigma = sampleStdDev(values)
  if (sigma > 0) {
    return sigma * Math.pow(n, -1 / 6)
  }
  const magnitude = values.length > 0 ? Math.abs(values[0]) : 0
  return magnitude > 0 ? magnitude * 0.05 : 0.5
}


function _kdeGrid(points, resolution, bandwidthOption) {
  /*
   * A bivariate Gaussian KDE on a resolution x resolution grid.
   *
   * :returns: { x, y, z, hx, hy } with z[i][j] the density at (x[j], y[i]).
   */
  const n = points.length
  const xs = points.map((point) => point.x)
  const ys = points.map((point) => point.y)
  let hx = 0
  let hy = 0
  if (isFiniteNumber(Number(bandwidthOption)) === true && Number(bandwidthOption) > 0) {
    hx = Number(bandwidthOption)
    hy = Number(bandwidthOption)
  } else {
    hx = _bandwidth(xs, n)
    hy = _bandwidth(ys, n)
  }

  let xLow = Infinity
  let xHigh = -Infinity
  let yLow = Infinity
  let yHigh = -Infinity
  for (let index = 0; index < n; index = index + 1) {
    xLow = Math.min(xLow, xs[index])
    xHigh = Math.max(xHigh, xs[index])
    yLow = Math.min(yLow, ys[index])
    yHigh = Math.max(yHigh, ys[index])
  }
  /* Three bandwidths of margin so the outer iso-lines close. */
  const xGrid = linspace(xLow - 3 * hx, xHigh + 3 * hx, resolution)
  const yGrid = linspace(yLow - 3 * hy, yHigh + 3 * hy, resolution)
  const norm = 1 / (2 * Math.PI * hx * hy * n)

  /* The kernel is separable: precompute each point's x and y factors. */
  const z = []
  for (let row = 0; row < resolution; row = row + 1) {
    z.push(new Array(resolution).fill(0))
  }
  const xFactor = new Array(resolution)
  const yFactor = new Array(resolution)
  for (let index = 0; index < n; index = index + 1) {
    for (let col = 0; col < resolution; col = col + 1) {
      const u = (xGrid[col] - xs[index]) / hx
      xFactor[col] = Math.exp(-0.5 * u * u)
    }
    for (let row = 0; row < resolution; row = row + 1) {
      const v = (yGrid[row] - ys[index]) / hy
      yFactor[row] = Math.exp(-0.5 * v * v)
    }
    for (let row = 0; row < resolution; row = row + 1) {
      const factor = yFactor[row]
      if (factor < 1e-12) {
        continue
      }
      const line = z[row]
      for (let col = 0; col < resolution; col = col + 1) {
        line[col] = line[col] + factor * xFactor[col]
      }
    }
  }
  for (let row = 0; row < resolution; row = row + 1) {
    for (let col = 0; col < resolution; col = col + 1) {
      z[row][col] = z[row][col] * norm
    }
  }
  return { x: xGrid, y: yGrid, z: z, hx: hx, hy: hy }
}


function _gridFromData(grid) {
  /*
   * A validated pre-computed grid: ascending-or-not x / y arrays of finite
   * numbers (at least 2 each) and a z matrix of matching shape; other z
   * entries become holes (NaN).
   *
   * :returns: { x, y, z } or null when the shape is unusable.
   */
  if (grid === null || typeof grid !== "object" || Array.isArray(grid.x) === false ||
      Array.isArray(grid.y) === false || Array.isArray(grid.z) === false) {
    return null
  }
  const xs = grid.x.map((value) => Number(value))
  const ys = grid.y.map((value) => Number(value))
  if (xs.length < 2 || ys.length < 2 || xs.some((value) => isFiniteNumber(value) === false) ||
      ys.some((value) => isFiniteNumber(value) === false)) {
    return null
  }
  const z = []
  for (let row = 0; row < ys.length; row = row + 1) {
    const source = Array.isArray(grid.z[row]) === true ? grid.z[row] : []
    const line = []
    for (let col = 0; col < xs.length; col = col + 1) {
      line.push(isFiniteNumber(source[col]) === true ? source[col] : NaN)
    }
    z.push(line)
  }
  return { x: xs, y: ys, z: z, hx: null, hy: null }
}


function _collectPoints(series, maxPoints) {
  /*
   * Finite points of every visible series, thinned evenly to maxPoints.
   */
  const all = []
  for (let si = 0; si < series.length; si = si + 1) {
    const list = Array.isArray(series[si].points) === true ? series[si].points : []
    for (let pi = 0; pi < list.length; pi = pi + 1) {
      const point = list[pi]
      if (point !== null && typeof point === "object" &&
          isFiniteNumber(point.x) === true && isFiniteNumber(point.y) === true) {
        all.push(point)
      }
    }
  }
  if (all.length <= maxPoints) {
    return all
  }
  const thinned = []
  const step = all.length / maxPoints
  for (let index = 0; index < maxPoints; index = index + 1) {
    thinned.push(all[Math.floor(index * step)])
  }
  return thinned
}


/* ── marching squares ────────────────────────────────────────────────────── */

export function traceContours(grid, level) {
  /*
   * Iso-lines of `grid` at `level`, as polylines in data coordinates.
   *
   * Corner bits: top-left 8, top-right 4, bottom-right 2, bottom-left 1
   * ("top" = row i, "bottom" = row i + 1). A crossing point is identified
   * by its grid edge, so the segments of neighbouring cells join exactly.
   * Saddles (5, 10) are resolved by the mean of the four corners. Cells
   * with a hole (non-finite corner) are skipped.
   *
   * :returns: [{ points: [{x, y}], closed }]
   */
  const xs = grid.x
  const ys = grid.y
  const z = grid.z
  const segments = []

  const cross = (x0, y0, v0, x1, y1, v1) => {
    const t = v1 === v0 ? 0.5 : (level - v0) / (v1 - v0)
    return { x: x0 + (x1 - x0) * t, y: y0 + (y1 - y0) * t }
  }

  for (let row = 0; row + 1 < ys.length; row = row + 1) {
    for (let col = 0; col + 1 < xs.length; col = col + 1) {
      const tl = z[row][col]
      const tr = z[row][col + 1]
      const br = z[row + 1][col + 1]
      const bl = z[row + 1][col]
      if (Number.isNaN(tl) || Number.isNaN(tr) || Number.isNaN(br) || Number.isNaN(bl)) {
        continue
      }
      const bits = (tl >= level ? 8 : 0) | (tr >= level ? 4 : 0) | (br >= level ? 2 : 0) | (bl >= level ? 1 : 0)
      if (bits === 0 || bits === 15) {
        continue
      }
      const x0 = xs[col]
      const x1 = xs[col + 1]
      const y0 = ys[row]
      const y1 = ys[row + 1]
      const edges = {
        top: { key: `h${row}:${col}`, point: () => cross(x0, y0, tl, x1, y0, tr) },
        right: { key: `v${row}:${col + 1}`, point: () => cross(x1, y0, tr, x1, y1, br) },
        bottom: { key: `h${row + 1}:${col}`, point: () => cross(x0, y1, bl, x1, y1, br) },
        left: { key: `v${row}:${col}`, point: () => cross(x0, y0, tl, x0, y1, bl) }
      }
      const center = (tl + tr + br + bl) / 4
      let pairs = []
      if (bits === 1 || bits === 14) {
        pairs = [["left", "bottom"]]
      } else if (bits === 2 || bits === 13) {
        pairs = [["bottom", "right"]]
      } else if (bits === 3 || bits === 12) {
        pairs = [["left", "right"]]
      } else if (bits === 4 || bits === 11) {
        pairs = [["top", "right"]]
      } else if (bits === 6 || bits === 9) {
        pairs = [["top", "bottom"]]
      } else if (bits === 7 || bits === 8) {
        pairs = [["left", "top"]]
      } else if (bits === 5) {
        pairs = center >= level ? [["left", "top"], ["bottom", "right"]] : [["top", "right"], ["left", "bottom"]]
      } else if (bits === 10) {
        pairs = center >= level ? [["top", "right"], ["left", "bottom"]] : [["left", "top"], ["bottom", "right"]]
      }
      for (let pi = 0; pi < pairs.length; pi = pi + 1) {
        const a = edges[pairs[pi][0]]
        const b = edges[pairs[pi][1]]
        segments.push({ keyA: a.key, keyB: b.key, a: a.point(), b: b.point() })
      }
    }
  }

  /* Join segments that share a crossing point into polylines. */
  const byKey = new Map()
  for (let si = 0; si < segments.length; si = si + 1) {
    const keys = [segments[si].keyA, segments[si].keyB]
    for (let ki = 0; ki < 2; ki = ki + 1) {
      if (byKey.has(keys[ki]) === false) {
        byKey.set(keys[ki], [])
      }
      byKey.get(keys[ki]).push(si)
    }
  }
  const used = new Array(segments.length).fill(false)
  const nextFrom = (key) => {
    const list = byKey.get(key)
    for (let li = 0; li < list.length; li = li + 1) {
      if (used[list[li]] === false) {
        return list[li]
      }
    }
    return -1
  }

  const lines = []
  for (let si = 0; si < segments.length; si = si + 1) {
    if (used[si] === true) {
      continue
    }
    used[si] = true
    const startKey = segments[si].keyA
    const points = [segments[si].a, segments[si].b]
    let key = segments[si].keyB
    let next = nextFrom(key)
    while (next >= 0) {
      used[next] = true
      const segment = segments[next]
      const forward = segment.keyA === key
      points.push(forward === true ? segment.b : segment.a)
      key = forward === true ? segment.keyB : segment.keyA
      next = nextFrom(key)
    }
    const closed = key === startKey
    if (closed === false) {
      key = startKey
      next = nextFrom(key)
      while (next >= 0) {
        used[next] = true
        const segment = segments[next]
        const forward = segment.keyA === key
        points.unshift(forward === true ? segment.b : segment.a)
        key = forward === true ? segment.keyB : segment.keyA
        next = nextFrom(key)
      }
    }
    lines.push({ points: points, closed: closed })
  }
  return lines
}


/* ── main renderer ───────────────────────────────────────────────────────── */

function _levelsOf(raw, rawDensity, zMin, zMax) {
  /*
   * The iso-level values: an explicit array, else `count` levels evenly
   * inside (zMin, zMax).
   */
  const explicit = Array.isArray(raw.levels) === true ? raw.levels
    : (Array.isArray(rawDensity.levels) === true ? rawDensity.levels : null)
  if (explicit !== null) {
    const values = explicit.filter((value) => isFiniteNumber(value) === true && value > zMin && value < zMax)
    values.sort((a, b) => a - b)
    return values
  }
  const countValue = Number(rawDensity.levels)
  const count = isFiniteNumber(countValue) === true ? Math.max(3, Math.min(20, Math.round(countValue))) : 8
  const levels = []
  for (let index = 1; index <= count; index = index + 1) {
    levels.push(zMin + (index / (count + 1)) * (zMax - zMin))
  }
  return levels
}


export function render(ctx) {
  /*
   * Render a 2D density / contour chart.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const model = ctx.model
  const raw = ctx.raw !== null && ctx.raw !== undefined ? ctx.raw : {}
  const rawDensity = raw.density !== null && typeof raw.density === "object" ? raw.density : {}
  const isContour = ctx.type === "contour"
  const style = _densityStyle(ctx, rawDensity, raw, isContour)
  const doFill = style === "fill" || style === "both"
  const doContour = style === "contour" || style === "both"
  const resolution = Math.max(8, Math.min(128, Math.round(Number(rawDensity.resolution)) || 32))
  const maxAttr = parseInt(ctx.attrs("max-points", "2000"), 10)
  const maxPoints = isFiniteNumber(maxAttr) === true && maxAttr > 0 ? maxAttr : 2000

  const root = svgEl("g", { part: "plot" }, [])
  const series = Array.isArray(model.series) === true ? model.series : []

  /* Grid: given, or a cached KDE of the visible points. */
  let grid = _gridFromData(raw.grid)
  let pointCount = 0
  if (grid === null) {
    const points = _collectPoints(series, maxPoints)
    pointCount = points.length
    if (points.length === 0) {
      return root
    }
    const signature = `${resolution}|${rawDensity.bandwidth}|${maxPoints}|${series.map((entry) => entry.name).join("\u0000")}`
    let cache = GRID_CACHE.get(model.source)
    if (cache === undefined) {
      cache = new Map()
      GRID_CACHE.set(model.source, cache)
    }
    grid = cache.get(signature)
    if (grid === undefined) {
      grid = _kdeGrid(points, resolution, rawDensity.bandwidth)
      cache.set(signature, grid)
    }
  }

  let zMin = Infinity
  let zMax = -Infinity
  let peak = { x: grid.x[0], y: grid.y[0] }
  for (let row = 0; row < grid.z.length; row = row + 1) {
    for (let col = 0; col < grid.z[row].length; col = col + 1) {
      const value = grid.z[row][col]
      if (Number.isNaN(value) === true) {
        continue
      }
      zMin = Math.min(zMin, value)
      if (value > zMax) {
        zMax = value
        peak = { x: grid.x[col], y: grid.y[row] }
      }
    }
  }
  if (zMin === Infinity) {
    return root
  }
  const zSpan = zMax - zMin
  const isKde = grid.hx !== null && grid.hx !== undefined
  const valueName = isKde === true ? "density" : "z"

  const meta = model.meta !== null && model.meta !== undefined ? model.meta : {}
  const xTitle = typeof meta.xLabel === "string" ? meta.xLabel : ""
  const yTitle = typeof meta.yLabel === "string" ? meta.yLabel : ""
  const margin = {
    top: 16, right: RAMP_ROOM,
    bottom: xTitle.length > 0 ? 50 : 36,
    left: yTitle.length > 0 ? 70 : 56
  }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)
  const xDomain = [Math.min(grid.x[0], grid.x[grid.x.length - 1]), Math.max(grid.x[0], grid.x[grid.x.length - 1])]
  const yDomain = [Math.min(grid.y[0], grid.y[grid.y.length - 1]), Math.max(grid.y[0], grid.y[grid.y.length - 1])]
  const xScale = linearScale(xDomain, [0, plotW])
  const yScale = linearScale(yDomain, [plotH, 0])

  const plot = svgEl("g", { transform: `translate(${margin.left},${margin.top})` }, [])
  root.appendChild(plot)
  const axes = axisLayer(plot)
  drawTicks(axes, xScale, { side: "bottom", extent: plotH, count: tickCount(plotW, 70), grid: doFill === false })
  drawTicks(axes, yScale, { side: "left", extent: plotW, count: tickCount(plotH, 40), grid: doFill === false })
  drawAxisTitle(axes, xTitle, "bottom", plotW, plotH, 38)
  drawAxisTitle(axes, yTitle, "left", plotW, plotH, 54)

  const clipId = `density-clip-${Math.random().toString(36).slice(2, 10)}`
  const defs = svgEl("defs", null, [])
  const clip = svgEl("clipPath", { id: clipId }, [])
  clip.appendChild(svgEl("rect", { x: 0, y: 0, width: plotW, height: plotH }, []))
  defs.appendChild(clip)
  plot.appendChild(defs)
  const marks = svgEl("g", { part: "marks", "clip-path": `url(#${clipId})` }, [])
  plot.appendChild(marks)

  const fractionOf = (value) => zSpan > 0 ? (value - zMin) / zSpan : 1

  /* ── Fill: edge-to-edge cells, one rect per run of equal colour ── */
  if (doFill === true) {
    const surface = svgEl("g", { part: "density-surface", "aria-hidden": "true" }, [])
    const edgesOf = (values) => {
      const edges = [values[0]]
      for (let index = 0; index + 1 < values.length; index = index + 1) {
        edges.push((values[index] + values[index + 1]) / 2)
      }
      edges.push(values[values.length - 1])
      return edges
    }
    const xEdges = edgesOf(grid.x)
    const yEdges = edgesOf(grid.y)
    for (let row = 0; row < grid.y.length; row = row + 1) {
      const top = yScale(yEdges[row])
      const bottom = yScale(yEdges[row + 1])
      let runStart = 0
      let runStep = null
      for (let col = 0; col <= grid.x.length; col = col + 1) {
        let step = null
        if (col < grid.x.length && Number.isNaN(grid.z[row][col]) === false) {
          const fraction = fractionOf(grid.z[row][col])
          /* Near-zero density stays the plot background. */
          step = isKde === true && fraction < 0.5 / COLOR_STEPS ? null : Math.round(fraction * (COLOR_STEPS - 1))
        }
        if (col === grid.x.length || step !== runStep) {
          if (runStep !== null) {
            const left = xScale(xEdges[runStart])
            const right = xScale(xEdges[col])
            surface.appendChild(svgEl("rect", {
              x: Math.min(left, right).toFixed(2), y: Math.min(top, bottom).toFixed(2),
              width: Math.abs(right - left).toFixed(2), height: Math.abs(bottom - top).toFixed(2),
              fill: sequentialColor(runStep / (COLOR_STEPS - 1)), "shape-rendering": "crispEdges"
            }, []))
          }
          runStart = col
          runStep = step
        }
      }
    }
    marks.appendChild(surface)
  }

  /* ── Contours: one joined path per level, labelled ── */
  const levels = doContour === true ? _levelsOf(raw, rawDensity, zMin, zMax) : []
  const levelRows = []
  const labelBoxes = []
  for (let li = 0; li < levels.length; li = li + 1) {
    const level = levels[li]
    const lines = traceContours(grid, level)
    if (lines.length === 0) {
      continue
    }
    const fraction = fractionOf(level)
    const stroke = doFill === true ? TEXT_COLOR : sequentialColor(0.35 + fraction * 0.65)
    let data = ""
    let longest = null
    let longestLength = 0
    for (let index = 0; index < lines.length; index = index + 1) {
      const pixels = lines[index].points.map((point) => ({ x: xScale(point.x), y: yScale(point.y) }))
      let length = 0
      for (let pi = 0; pi < pixels.length; pi = pi + 1) {
        data = data + `${pi === 0 ? "M" : "L"}${pixels[pi].x.toFixed(2)},${pixels[pi].y.toFixed(2)} `
        if (pi > 0) {
          length = length + Math.hypot(pixels[pi].x - pixels[pi - 1].x, pixels[pi].y - pixels[pi - 1].y)
        }
      }
      if (lines[index].closed === true) {
        data = data + "Z "
      }
      if (length > longestLength) {
        longestLength = length
        longest = pixels
      }
    }
    const levelText = formatNumber(level, { maximumSignificantDigits: 3 })
    const path = svgEl("path", {
      d: data.trim(), fill: "none", stroke: stroke, "stroke-width": doFill === true ? 1 : 1.5,
      "stroke-opacity": doFill === true ? 0.55 : 1, "stroke-linejoin": "round", part: "contour"
    }, [])
    focusableMark(path, `Contour at ${valueName} ${levelText}: ${lines.length} line(s)`)
    const handlerLevel = level
    activateOnKey(path, () => {
      ctx.emit("mj-chart-contour-click", { level: handlerLevel, index: li, lines: lines.length })
    })
    marks.appendChild(path)
    levelRows.push([li + 1, level, lines.length])

    /* Label at the middle of the longest line, when there is room. */
    if (longest !== null && longestLength > 60) {
      const anchor = longest[Math.floor(longest.length / 2)]
      const box = { x0: anchor.x - 18, x1: anchor.x + 18, y0: anchor.y - 8, y1: anchor.y + 6 }
      const overlaps = labelBoxes.some((other) => box.x0 < other.x1 && box.x1 > other.x0 && box.y0 < other.y1 && box.y1 > other.y0)
      if (overlaps === false) {
        labelBoxes.push(box)
        marks.appendChild(svgEl("text", {
          x: anchor.x, y: anchor.y + 3, "text-anchor": "middle", "font-size": 9,
          fill: TEXT_COLOR, stroke: SURFACE_COLOR, "stroke-width": 3, "paint-order": "stroke",
          "pointer-events": "none", "aria-hidden": "true", part: "contour-label"
        }, levelText))
      }
    }
  }

  /* Pointer / keyboard access to the surface values. */
  if (doFill === true) {
    const overlay = svgEl("rect", {
      x: 0, y: 0, width: plotW, height: plotH, fill: "transparent", part: "density-hit"
    }, [])
    focusableMark(overlay, `${isKde === true ? "Density" : "Value"} surface: peak ${valueName} ` +
      `${formatNumber(zMax, { maximumSignificantDigits: 3 })} at x ${formatNumber(peak.x, { maximumSignificantDigits: 3 })}, ` +
      `y ${formatNumber(peak.y, { maximumSignificantDigits: 3 })}`)
    const valueAt = (x, y) => {
      let col = 0
      let row = 0
      for (let index = 1; index < grid.x.length; index = index + 1) {
        if (Math.abs(grid.x[index] - x) < Math.abs(grid.x[col] - x)) {
          col = index
        }
      }
      for (let index = 1; index < grid.y.length; index = index + 1) {
        if (Math.abs(grid.y[index] - y) < Math.abs(grid.y[row] - y)) {
          row = index
        }
      }
      return grid.z[row][col]
    }
    overlay.addEventListener("click", (event) => {
      const box = overlay.getBoundingClientRect()
      const fx = box.width > 0 ? (event.clientX - box.left) / box.width : 0.5
      const fy = box.height > 0 ? (event.clientY - box.top) / box.height : 0.5
      const x = xDomain[0] + fx * (xDomain[1] - xDomain[0])
      const y = yDomain[1] - fy * (yDomain[1] - yDomain[0])
      ctx.emit("mj-chart-density-click", { x: x, y: y, density: valueAt(x, y) })
    })
    overlay.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault()
        ctx.emit("mj-chart-density-click", { x: peak.x, y: peak.y, density: zMax })
      }
    })
    plot.appendChild(overlay)
  }

  drawBaseline(axes, 0, plotH, plotW, plotH)
  drawBaseline(axes, 0, 0, 0, plotH)

  /* Colour bar (fill) or level key (contour lines only). */
  const rampLength = Math.min(plotH, 180)
  const rampLabels = [
    { fraction: 0, text: isKde === true ? "0" : formatNumber(zMin, { maximumSignificantDigits: 2 }) },
    { fraction: 1, text: formatNumber(zMax, { maximumSignificantDigits: 2 }) }
  ]
  drawColorRamp(axes, {
    x: plotW + 12, y: (plotH - rampLength) / 2 + 16, length: rampLength - 16, thickness: 10, vertical: true,
    colorAt: (fraction) => doFill === true ? sequentialColor(fraction) : sequentialColor(0.35 + fraction * 0.65),
    labels: rampLabels, title: valueName
  })
  if (pointCount > 0 && isKde === true) {
    axes.appendChild(svgEl("text", {
      x: plotW, y: -4, "text-anchor": "end", "font-size": 10, fill: MUTED_TEXT_COLOR
    }, `KDE of ${formatNumber(pointCount)} points`))
  }

  ctx.setLegend([])
  if (doContour === true) {
    ctx.setTable({
      columns: ["Level", isKde === true ? "Density" : "Value", "Lines"],
      rows: levelRows,
      caption: "Contour levels"
    })
  } else if (isKde === false) {
    const rows = []
    for (let row = 0; row < grid.y.length; row = row + 1) {
      for (let col = 0; col < grid.x.length; col = col + 1) {
        rows.push([grid.x[col], grid.y[row], Number.isNaN(grid.z[row][col]) === true ? "" : grid.z[row][col]])
      }
    }
    ctx.setTable({ columns: ["X", "Y", "Value"], rows: rows, caption: "Grid values" })
  }
  return root
}


function _isEmpty(model) {
  /*
   * True when there is neither a usable grid nor a finite point.
   */
  const raw = model.source !== null && model.source !== undefined ? model.source : {}
  if (_gridFromData(raw.grid) !== null) {
    return false
  }
  return _collectPoints(Array.isArray(model.allSeries) === true ? model.allSeries : [], 1).length === 0
}


registerRenderer("density-2d", render, { isEmpty: _isEmpty })
registerRenderer("contour", render, { isEmpty: _isEmpty })
