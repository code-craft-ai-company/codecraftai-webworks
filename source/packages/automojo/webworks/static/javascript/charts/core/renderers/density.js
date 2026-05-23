/*
 * density.js
 *
 * 2D Density / Contour renderer.
 *
 * Registered chart types:
 *   "density-2d" — filled color-surface KDE heatmap (style="fill"|"both")
 *   "contour"    — iso-contour line plot (style="contour"|"both")
 *
 * Data shapes (either raw points or a pre-computed grid):
 *
 *   Raw points (KDE computed here):
 *     model.series[].points: [{ x, y }, ...]
 *     ctx.raw.density?.bandwidth  "auto" | number
 *     ctx.raw.density?.resolution number (grid cells per axis, default 32)
 *     ctx.raw.density?.style      "fill" | "contour" | "both"
 *
 *   Pre-computed grid (KDE skipped):
 *     ctx.raw.grid: { x: [...], y: [...], z: [[row0], [row1], ...] }
 *     ctx.raw.density?.style      same
 *     ctx.raw.density?.levels     number of iso-contour levels (default 10)
 *
 * The KDE uses a simple 2D Gaussian kernel (Silverman bandwidth rule).
 * Marching squares traces iso-contour paths.
 * Large point sets are downsampled to max-points (default 2000) before KDE.
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber, extent } from "../svgdraw.js";
import { linearScale, niceTicks } from "../scales.js";


/* ── KDE helpers ─────────────────────────────────────────────────────────── */

function _silverman(values) {
  /*
   * Silverman's rule of thumb for 1D bandwidth.
   *
   * :param values: Numeric array.
   * :returns: Bandwidth estimate.
   */
  const n = values.length
  if (n < 2) {
    return 1
  }
  let mean = 0
  for (let i = 0; i < n; i = i + 1) {
    mean = mean + values[i]
  }
  mean = mean / n
  let variance = 0
  for (let i = 0; i < n; i = i + 1) {
    const diff = values[i] - mean
    variance = variance + diff * diff
  }
  const std = Math.sqrt(variance / n)
  const bw = 1.06 * std * Math.pow(n, -0.2)
  return bw > 0 ? bw : 1
}


function _gaussianKernel(dx, dy, hx, hy) {
  /*
   * 2D Gaussian kernel value.
   *
   * :param dx: Delta x.
   * :param dy: Delta y.
   * :param hx: Bandwidth x.
   * :param hy: Bandwidth y.
   * :returns: Kernel density contribution.
   */
  const ux = dx / hx
  const uy = dy / hy
  const value = Math.exp(-0.5 * (ux * ux + uy * uy)) / (2 * Math.PI * hx * hy)
  return value
}


function _computeKde(points, xGrid, yGrid, hx, hy) {
  /*
   * Compute a 2D KDE on a regular grid.
   *
   * :param points: Array of {x, y}.
   * :param xGrid: Array of x grid coordinates (length = cols).
   * :param yGrid: Array of y grid coordinates (length = rows).
   * :param hx: Bandwidth in x.
   * :param hy: Bandwidth in y.
   * :returns: 2D array z[row][col].
   */
  const rows = yGrid.length
  const cols = xGrid.length
  const z = []
  for (let r = 0; r < rows; r = r + 1) {
    const row = new Float64Array(cols)
    z.push(row)
  }
  for (let p = 0; p < points.length; p = p + 1) {
    const px = points[p].x
    const py = points[p].y
    for (let r = 0; r < rows; r = r + 1) {
      for (let c = 0; c < cols; c = c + 1) {
        z[r][c] = z[r][c] + _gaussianKernel(xGrid[c] - px, yGrid[r] - py, hx, hy)
      }
    }
  }
  return z
}


function _linspace(lo, hi, n) {
  /*
   * Generate n evenly-spaced values from lo to hi inclusive.
   *
   * :returns: Array of numbers.
   */
  const arr = []
  const step = n > 1 ? (hi - lo) / (n - 1) : 0
  for (let i = 0; i < n; i = i + 1) {
    arr.push(lo + i * step)
  }
  return arr
}


/* ── Marching squares ────────────────────────────────────────────────────── */

function _marchingSquares(z, xGrid, yGrid, level) {
  /*
   * Trace iso-contour paths at a given level using marching squares.
   *
   * :param z: 2D array z[row][col].
   * :param xGrid: x grid coordinates.
   * :param yGrid: y grid coordinates.
   * :param level: The iso-value to trace.
   * :returns: Array of path-data strings.
   */
  const rows = z.length
  const cols = z[0].length
  const paths = []

  const lerp = (a, b, va, vb, lv) => {
    /* Linear interpolate position between two grid points. */
    const span = vb - va
    if (Math.abs(span) < 1e-12) {
      return (a + b) / 2
    }
    return a + (b - a) * (lv - va) / span
  }

  for (let r = 0; r < rows - 1; r = r + 1) {
    for (let c = 0; c < cols - 1; c = c + 1) {
      const v00 = z[r][c]
      const v10 = z[r][c + 1]
      const v01 = z[r + 1][c]
      const v11 = z[r + 1][c + 1]

      const x0 = xGrid[c]
      const x1 = xGrid[c + 1]
      const y0 = yGrid[r]
      const y1 = yGrid[r + 1]

      /* Encode which corners are above the level. */
      const bits =
        (v00 >= level ? 8 : 0) |
        (v10 >= level ? 4 : 0) |
        (v11 >= level ? 2 : 0) |
        (v01 >= level ? 1 : 0)

      if (bits === 0 || bits === 15) {
        continue
      }

      /* Edge midpoints. */
      const mTop = { x: lerp(x0, x1, v00, v10, level), y: y0 }
      const mRight = { x: x1, y: lerp(y0, y1, v10, v11, level) }
      const mBottom = { x: lerp(x0, x1, v01, v11, level), y: y1 }
      const mLeft = { x: x0, y: lerp(y0, y1, v00, v01, level) }

      const segments = {
        1: [mLeft, mBottom],
        2: [mBottom, mRight],
        3: [mLeft, mRight],
        4: [mRight, mTop],
        5: [mLeft, mTop, mRight, mBottom],
        6: [mBottom, mTop],
        7: [mLeft, mTop],
        8: [mTop, mLeft],
        9: [mTop, mBottom],
        10: [mRight, mBottom, mTop, mLeft],
        11: [mRight, mTop],
        12: [mRight, mLeft],
        13: [mBottom, mLeft],
        14: [mBottom, mLeft],
        15: []
      }

      const seg = segments[bits]
      if (seg === null || seg === undefined || seg.length < 2) {
        continue
      }
      /* Emit line segments in pairs. */
      for (let i = 0; i + 1 < seg.length; i = i + 2) {
        const a = seg[i]
        const b = seg[i + 1]
        const pathStr = `M${a.x.toFixed(2)},${a.y.toFixed(2)} ` +
          `L${b.x.toFixed(2)},${b.y.toFixed(2)}`
        paths.push(pathStr)
      }
    }
  }
  return paths
}


/* ── Color helpers ───────────────────────────────────────────────────────── */

const DENSITY_RAMP = [
  "var(--mj-chart-heat-1, #eff6ff)",
  "var(--mj-chart-heat-2, #bfdbfe)",
  "var(--mj-chart-heat-3, #93c5fd)",
  "var(--mj-chart-heat-4, #60a5fa)",
  "var(--mj-chart-heat-5, #3b82f6)",
  "var(--mj-chart-heat-6, #2563eb)",
  "var(--mj-chart-heat-7, #1d4ed8)",
  "var(--mj-chart-heat-8, #1e40af)"
]

const CONTOUR_COLORS = [
  "var(--mj-color-accent-300, #80a8ff)",
  "var(--mj-color-accent-500, #2563eb)",
  "var(--mj-color-accent-800, #122f78)"
]


function _densityColor(fraction) {
  /*
   * Map a [0,1] fraction to a sequential density color.
   *
   * :param fraction: Value in [0, 1].
   * :returns: CSS color string.
   */
  const index = Math.min(
    DENSITY_RAMP.length - 1,
    Math.floor(fraction * DENSITY_RAMP.length)
  )
  return DENSITY_RAMP[index]
}


/* ── Main renderer ───────────────────────────────────────────────────────── */

export function render(ctx) {
  /*
   * Render a 2D density / contour chart.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const model = ctx.model
  const rawDensity = (ctx.raw !== null && ctx.raw !== undefined)
    ? ctx.raw.density || {}
    : {}
  const rawGrid = (ctx.raw !== null && ctx.raw !== undefined)
    ? ctx.raw.grid || null
    : null

  const style = rawDensity.style || ctx.attrs("density-style", "fill")
  const doFill = style === "fill" || style === "both"
  const doContour = style === "contour" || style === "both"
  const resolution = Math.max(8, Math.min(128, Number(rawDensity.resolution) || 32))
  const levelCount = Math.max(3, Math.min(20, Number(rawDensity.levels) || 10))
  const maxPoints = Number(ctx.attrs("max-points", "2000"))

  const root = svgEl("g", { part: "plot" }, [])

  const margin = { top: 16, right: 16, bottom: 44, left: 56 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  /* ── Collect / validate point data ── */
  const series = model.series
  let rawPoints = []
  if (series !== null && series !== undefined) {
    for (let s = 0; s < series.length; s = s + 1) {
      const pts = series[s].points
      if (pts === null || pts === undefined) {
        continue
      }
      for (let p = 0; p < pts.length; p = p + 1) {
        const pt = pts[p]
        const validX = typeof pt.x === "number" && Number.isNaN(pt.x) === false
        const validY = typeof pt.y === "number" && Number.isNaN(pt.y) === false
        if (validX === true && validY === true) {
          rawPoints.push(pt)
        }
      }
    }
  }

  /* Require either raw points or a pre-computed grid. */
  const hasGrid = rawGrid !== null && rawGrid !== undefined &&
    Array.isArray(rawGrid.z) && rawGrid.z.length > 0
  const hasPoints = rawPoints.length > 0

  if (hasGrid === false && hasPoints === false) {
    return root
  }

  /* ── Build or use the z grid ── */
  let xGrid = []
  let yGrid = []
  let zGrid = []
  let xDomain = [0, 1]
  let yDomain = [0, 1]

  if (hasGrid === true) {
    xGrid = rawGrid.x
    yGrid = rawGrid.y
    zGrid = rawGrid.z
    xDomain = extent(xGrid)
    yDomain = extent(yGrid)
  } else {
    /* Downsample if needed. */
    let pts = rawPoints
    if (pts.length > maxPoints) {
      const step = Math.ceil(pts.length / maxPoints)
      const sampled = []
      for (let i = 0; i < pts.length; i = i + step) {
        sampled.push(pts[i])
      }
      pts = sampled
    }

    xDomain = extent(pts.map((pt) => pt.x))
    yDomain = extent(pts.map((pt) => pt.y))

    const xPad = (xDomain[1] - xDomain[0]) * 0.1 || 1
    const yPad = (yDomain[1] - yDomain[0]) * 0.1 || 1
    const xLo = xDomain[0] - xPad
    const xHi = xDomain[1] + xPad
    const yLo = yDomain[0] - yPad
    const yHi = yDomain[1] + yPad

    xGrid = _linspace(xLo, xHi, resolution)
    yGrid = _linspace(yLo, yHi, resolution)

    /* Bandwidth. */
    let hx = 0
    let hy = 0
    if (rawDensity.bandwidth === "auto" ||
        rawDensity.bandwidth === null ||
        rawDensity.bandwidth === undefined) {
      hx = _silverman(pts.map((pt) => pt.x))
      hy = _silverman(pts.map((pt) => pt.y))
    } else {
      const bw = Number(rawDensity.bandwidth)
      hx = bw
      hy = bw
    }

    zGrid = _computeKde(pts, xGrid, yGrid, hx, hy)
    xDomain = [xLo, xHi]
    yDomain = [yLo, yHi]
  }

  /* Pixel scales. */
  const xScale = linearScale(xDomain, [0, plotW])
  const yScale = linearScale(yDomain, [plotH, 0])

  /* Z domain for color mapping. */
  let zMin = Infinity
  let zMax = -Infinity
  for (let r = 0; r < zGrid.length; r = r + 1) {
    for (let c = 0; c < zGrid[r].length; c = c + 1) {
      const v = zGrid[r][c]
      if (v < zMin) {
        zMin = v
      }
      if (v > zMax) {
        zMax = v
      }
    }
  }
  if (zMin === Infinity || zMax === -Infinity) {
    return root
  }
  const zSpan = zMax - zMin || 1

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  /* ── Fill: rasterized grid cells ── */
  if (doFill === true) {
    const cellPxW = plotW / (xGrid.length - 1 || 1)
    const cellPxH = plotH / (yGrid.length - 1 || 1)
    for (let r = 0; r < zGrid.length; r = r + 1) {
      for (let c = 0; c < zGrid[r].length; c = c + 1) {
        const fraction = (zGrid[r][c] - zMin) / zSpan
        if (fraction < 0.01) {
          continue
        }
        const px = xScale(xGrid[c])
        const py = yScale(yGrid[r])
        const fillColor = _densityColor(fraction)
        plot.appendChild(svgEl("rect", {
          x: (px - cellPxW / 2).toFixed(2),
          y: (py - cellPxH / 2).toFixed(2),
          width: Math.ceil(cellPxW) + 1,
          height: Math.ceil(cellPxH) + 1,
          fill: fillColor,
          opacity: (0.3 + fraction * 0.7).toFixed(3)
        }, []))
      }
    }
  }

  /* ── Contour: marching squares iso-lines ── */
  if (doContour === true) {
    /* Build iso-levels evenly spaced across the z range. */
    const isoValues = []
    for (let l = 1; l <= levelCount; l = l + 1) {
      isoValues.push(zMin + (l / (levelCount + 1)) * zSpan)
    }

    /* Map to pixel space: recast grids. */
    const xGridPx = xGrid.map((x) => xScale(x))
    const yGridPx = yGrid.map((y) => yScale(y))

    for (let l = 0; l < isoValues.length; l = l + 1) {
      const isoLevel = isoValues[l]
      const paths = _marchingSquares(zGrid, xGridPx, yGridPx, isoLevel)
      const fraction = l / (isoValues.length - 1 || 1)
      const colorIndex = Math.min(
        CONTOUR_COLORS.length - 1,
        Math.floor(fraction * CONTOUR_COLORS.length)
      )
      const lineColor = CONTOUR_COLORS[colorIndex]
      const opacity = (0.5 + fraction * 0.5).toFixed(2)

      for (let p = 0; p < paths.length; p = p + 1) {
        plot.appendChild(svgEl("path", {
          d: paths[p],
          fill: "none",
          stroke: lineColor,
          "stroke-width": 1.5,
          opacity: opacity
        }, []))
      }
    }
  }

  /* ── Axes ── */
  const xTicks = niceTicks(xDomain[0], xDomain[1], 5)
  for (let t = 0; t < xTicks.length; t = t + 1) {
    const tick = xTicks[t]
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

  const yTicks = niceTicks(yDomain[0], yDomain[1], 5)
  for (let t = 0; t < yTicks.length; t = t + 1) {
    const tick = yTicks[t]
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

  /* Axis baselines. */
  plot.appendChild(svgEl("line", {
    x1: 0, y1: plotH, x2: plotW, y2: plotH,
    stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
  }, []))
  plot.appendChild(svgEl("line", {
    x1: 0, y1: 0, x2: 0, y2: plotH,
    stroke: "var(--mj-border-strong, #c7ccd6)", "stroke-width": 1.5
  }, []))

  return root
}


registerRenderer("density-2d", render)
registerRenderer("contour", render)
