/*
 * contour.js
 *
 * 2-D contour and surface renderers.
 *
 * Registered types:
 *   "contour"  - iso-value contour lines / filled contour bands (marching squares)
 *   "surface"  - shaded 2-D projection of a z=f(x,y) surface (isometric/oblique)
 *
 * Renderer contract: render(ctx) -> SVGElement  (a <g> within [0..width]x[0..height])
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, formatNumber } from "../svgdraw.js";
import { linearScale, niceTicks } from "../scales.js";


/* ── color ramp ───────────────────────────────────────────────── */

/*
 * Map a normalised value [0,1] to a sequential blue-to-red color token
 * gradient using CSS interpolation via opacity on layered tokens.
 */
function _sequentialColor(t) {
  /*
   * Return an interpolated sequential hex color for t in [0,1].
   * Uses a simple blue-white-red ramp readable on white backgrounds.
   */
  const stops = [
    [37,  99, 235],   /* --mj-color-accent-500 blue */
    [34, 197,  94],   /* green mid */
    [234, 179,   8],  /* yellow */
    [239,  68,  68]   /* red */
  ]
  const scaled = Math.max(0, Math.min(1, t)) * (stops.length - 1)
  const lo = Math.floor(scaled)
  const hi = Math.min(lo + 1, stops.length - 1)
  const frac = scaled - lo
  const r = Math.round(stops[lo][0] + frac * (stops[hi][0] - stops[lo][0]))
  const g = Math.round(stops[lo][1] + frac * (stops[hi][1] - stops[lo][1]))
  const b = Math.round(stops[lo][2] + frac * (stops[hi][2] - stops[lo][2]))
  const hex = "#" +
    r.toString(16).padStart(2, "0") +
    g.toString(16).padStart(2, "0") +
    b.toString(16).padStart(2, "0")
  return hex
}


/* ── marching squares ─────────────────────────────────────────── */

/*
 * Marching-squares edge interpolation.
 * Returns a pixel point on the edge between two grid corners.
 */
function _interpolate(ax, ay, az, bx, by, bz, level) {
  const t = (az === bz) ? 0.5 : (level - az) / (bz - az)
  return { x: ax + t * (bx - ax), y: ay + t * (by - ay) }
}


/*
 * Trace one isoline at `level` through the z grid.
 * Returns an array of { x, y } pixel-point arrays (one per line segment).
 */
function _marchingSquares(xVals, yVals, zGrid, level, xScale, yScale) {
  const rows = yVals.length
  const cols = xVals.length
  const segments = []

  for (let row = 0; row < rows - 1; row = row + 1) {
    for (let col = 0; col < cols - 1; col = col + 1) {
      /* Four corners: tl, tr, br, bl */
      const x0 = xScale(xVals[col])
      const x1 = xScale(xVals[col + 1])
      const y0 = yScale(yVals[row])
      const y1 = yScale(yVals[row + 1])
      const ztl = zGrid[row][col]
      const ztr = zGrid[row][col + 1]
      const zbr = zGrid[row + 1][col + 1]
      const zbl = zGrid[row + 1][col]

      /* Compute 4-bit case index */
      let idx = 0
      if (ztl >= level) { idx = idx | 8 }
      if (ztr >= level) { idx = idx | 4 }
      if (zbr >= level) { idx = idx | 2 }
      if (zbl >= level) { idx = idx | 1 }

      if (idx === 0 || idx === 15) {
        continue
      }

      /* Edge midpoints */
      const top    = _interpolate(x0, y0, ztl, x1, y0, ztr, level)
      const right  = _interpolate(x1, y0, ztr, x1, y1, zbr, level)
      const bottom = _interpolate(x0, y1, zbl, x1, y1, zbr, level)
      const left   = _interpolate(x0, y0, ztl, x0, y1, zbl, level)

      /* Lookup table: pairs of edges to connect */
      const table = {
        1:  [[left, bottom]],
        2:  [[bottom, right]],
        3:  [[left, right]],
        4:  [[top, right]],
        5:  [[left, top], [bottom, right]],
        6:  [[top, bottom]],
        7:  [[left, top]],
        8:  [[left, top]],
        9:  [[top, bottom]],
        10: [[left, bottom], [top, right]],
        11: [[top, right]],
        12: [[left, right]],
        13: [[bottom, right]],
        14: [[left, bottom]]
      }
      const pairs = table[idx]
      if (pairs === undefined) {
        continue
      }
      for (let p = 0; p < pairs.length; p = p + 1) {
        segments.push(pairs[p])
      }
    }
  }
  return segments
}


/* ── axes ─────────────────────────────────────────────────────── */

function _drawAxes(plot, plotW, plotH, xScale, yScale, meta) {
  const xTicks = xScale.ticks(5)
  for (let i = 0; i < xTicks.length; i = i + 1) {
    const px = xScale(xTicks[i])
    plot.appendChild(svgEl("line", {
      x1: px, y1: 0, x2: px, y2: plotH,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    plot.appendChild(svgEl("text", {
      x: px, y: plotH + 14, "text-anchor": "middle",
      "font-size": 10, fill: "var(--mj-text-muted, #6b7280)"
    }, formatNumber(xTicks[i])))
  }

  const yTicks = yScale.ticks(5)
  for (let i = 0; i < yTicks.length; i = i + 1) {
    const py = yScale(yTicks[i])
    plot.appendChild(svgEl("line", {
      x1: 0, y1: py, x2: plotW, y2: py,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    plot.appendChild(svgEl("text", {
      x: -6, y: py + 4, "text-anchor": "end",
      "font-size": 10, fill: "var(--mj-text-muted, #6b7280)"
    }, formatNumber(yTicks[i])))
  }

  /* Axis labels */
  if (meta !== null && meta !== undefined) {
    if (meta.xLabel) {
      plot.appendChild(svgEl("text", {
        x: plotW / 2, y: plotH + 30, "text-anchor": "middle",
        "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
      }, escapeHtml(meta.xLabel)))
    }
    if (meta.yLabel) {
      plot.appendChild(svgEl("text", {
        transform: `rotate(-90) translate(${-plotH / 2}, -36)`,
        "text-anchor": "middle",
        "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
      }, escapeHtml(meta.yLabel)))
    }
  }
  return
}


/* ── contour renderer ─────────────────────────────────────────── */

function _renderContour(ctx) {
  /*
   * Render a contour / filled-contour chart using marching squares.
   */
  const raw = ctx.raw
  const root = svgEl("g", { part: "plot" }, [])

  const grid = (raw !== null && raw !== undefined) ? raw.grid : null
  if (grid === null || grid === undefined ||
      grid.x === null || grid.y === null || grid.z === null) {
    return root
  }

  const xVals = grid.x
  const yVals = grid.y
  const zGrid = grid.z

  if (xVals.length < 2 || yVals.length < 2 || zGrid.length < 2) {
    return root
  }

  const margin = { top: 16, right: 16, bottom: 44, left: 56 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  const xScale = linearScale([xVals[0], xVals[xVals.length - 1]], [0, plotW])
  const yScale = linearScale([yVals[0], yVals[yVals.length - 1]], [plotH, 0])

  /* Find z extent */
  let zMin = Infinity
  let zMax = -Infinity
  for (let row = 0; row < zGrid.length; row = row + 1) {
    for (let col = 0; col < zGrid[row].length; col = col + 1) {
      const z = zGrid[row][col]
      if (typeof z !== "number") {
        continue
      }
      if (z < zMin) { zMin = z }
      if (z > zMax) { zMax = z }
    }
  }
  if (zMin === Infinity) {
    return root
  }
  if (zMin === zMax) {
    zMax = zMin + 1
  }

  /* Levels */
  const levels = (raw.levels !== null && raw.levels !== undefined && raw.levels.length > 0)
    ? raw.levels : niceTicks(zMin, zMax, 8)

  const doFill = raw.fill === true

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  _drawAxes(plot, plotW, plotH, xScale, yScale, raw.meta)

  /* Filled bands: draw a rect for each cell colored by cell-center z */
  if (doFill === true) {
    for (let row = 0; row < yVals.length - 1; row = row + 1) {
      for (let col = 0; col < xVals.length - 1; col = col + 1) {
        const ztl = zGrid[row][col]
        const ztr = zGrid[row][col + 1]
        const zbl = zGrid[row + 1][col]
        const zbr = zGrid[row + 1][col + 1]
        const zCenter = (ztl + ztr + zbl + zbr) / 4
        const t = (zCenter - zMin) / (zMax - zMin)
        const fillColor = _sequentialColor(t)
        const px0 = xScale(xVals[col])
        const px1 = xScale(xVals[col + 1])
        const py0 = yScale(yVals[row])
        const py1 = yScale(yVals[row + 1])
        const rx = Math.min(px0, px1)
        const ry = Math.min(py0, py1)
        const rw = Math.abs(px1 - px0)
        const rh = Math.abs(py1 - py0)
        const zLabel = escapeHtml("z=" + formatNumber(zCenter))
        const cell = svgEl("rect", {
          x: rx, y: ry, width: rw, height: rh,
          fill: fillColor,
          part: "contour-band",
          tabindex: "0",
          role: "img",
          "aria-label": zLabel
        }, [])
        cell.appendChild(svgEl("title", null, zLabel))
        plot.appendChild(cell)
      }
    }
  }

  /* Isolines */
  for (let lev = 0; lev < levels.length; lev = lev + 1) {
    const level = levels[lev]
    const t = (level - zMin) / (zMax - zMin)
    const strokeColor = doFill === true
      ? "var(--mj-surface, #fff)"
      : _sequentialColor(t)
    const segments = _marchingSquares(xVals, yVals, zGrid, level, xScale, yScale)
    const levelGroup = svgEl("g", { part: "isoline" }, [])

    for (let seg = 0; seg < segments.length; seg = seg + 1) {
      const p0 = segments[seg][0]
      const p1 = segments[seg][1]
      const line = svgEl("line", {
        x1: p0.x.toFixed(2), y1: p0.y.toFixed(2),
        x2: p1.x.toFixed(2), y2: p1.y.toFixed(2),
        stroke: strokeColor,
        "stroke-width": doFill === true ? 0.5 : 1.5
      }, [])
      levelGroup.appendChild(line)
    }
    plot.appendChild(levelGroup)

    /* Contour label on first segment */
    if (doFill === false && segments.length > 0) {
      const mid = segments[Math.floor(segments.length / 2)]
      const lx = (mid[0].x + mid[1].x) / 2
      const ly = (mid[0].y + mid[1].y) / 2
      plot.appendChild(svgEl("text", {
        x: lx, y: ly - 3,
        "text-anchor": "middle",
        "font-size": 9,
        fill: strokeColor
      }, formatNumber(level)))
    }
  }

  return root
}


/* ── surface renderer (2-D projection) ───────────────────────── */

function _renderSurface(ctx) {
  /*
   * Render a 2-D projected surface as shaded quadrilateral faces.
   * Uses a parallel-oblique or isometric projection.
   */
  const raw = ctx.raw
  const root = svgEl("g", { part: "plot" }, [])

  const grid = (raw !== null && raw !== undefined) ? raw.grid : null
  if (grid === null || grid === undefined) {
    return root
  }

  const xVals = grid.x
  const yVals = grid.y
  const zGrid = grid.z

  if (xVals === null || yVals === null || zGrid === null ||
      xVals.length < 2 || yVals.length < 2) {
    return root
  }

  const projection = (raw.projection === "oblique") ? "oblique" : "isometric"
  const style = (raw.style !== null && raw.style !== undefined)
    ? raw.style : "shaded"

  const margin = 30
  const drawW = ctx.width - margin * 2
  const drawH = ctx.height - margin * 2

  /* Find extents */
  let xMin = xVals[0]; let xMax = xVals[xVals.length - 1]
  let yMin = yVals[0]; let yMax = yVals[yVals.length - 1]
  let zMin = Infinity; let zMax = -Infinity
  for (let row = 0; row < zGrid.length; row = row + 1) {
    for (let col = 0; col < zGrid[row].length; col = col + 1) {
      const z = zGrid[row][col]
      if (typeof z !== "number") { continue }
      if (z < zMin) { zMin = z }
      if (z > zMax) { zMax = z }
    }
  }
  if (zMin === Infinity) { zMin = 0; zMax = 1 }
  if (zMin === zMax) { zMax = zMin + 1 }

  const xNorm = linearScale([xMin, xMax], [0, 1])
  const yNorm = linearScale([yMin, yMax], [0, 1])
  const zNorm = linearScale([zMin, zMax], [0, 1])

  /*
   * 3-D -> 2-D projection.
   * Isometric: x' = (x-y)*cos30, y' = (x+y)*sin30 - z
   * Oblique:   x' = x + y*0.5, y' = y*0.25 - z
   */
  const project = (nx, ny, nz) => {
    if (projection === "oblique") {
      const px = (nx + ny * 0.5) * drawW * 0.7 + margin
      const py = (1 - nz) * drawH * 0.6 + ny * drawH * 0.2 + margin
      return { x: px, y: py }
    }
    const cos30 = Math.cos(Math.PI / 6)
    const sin30 = Math.sin(Math.PI / 6)
    const px = ((nx - ny) * cos30) * drawW * 0.5 + ctx.width / 2
    const py = ((nx + ny) * sin30 - nz * 0.8) * drawH * 0.5 + ctx.height * 0.65
    return { x: px, y: py }
  }

  /* Build face list for painter's algorithm */
  const faces = []
  for (let row = 0; row < yVals.length - 1; row = row + 1) {
    for (let col = 0; col < xVals.length - 1; col = col + 1) {
      const z00 = typeof zGrid[row][col] === "number" ? zGrid[row][col] : 0
      const z10 = typeof zGrid[row][col + 1] === "number" ? zGrid[row][col + 1] : 0
      const z01 = typeof zGrid[row + 1][col] === "number" ? zGrid[row + 1][col] : 0
      const z11 = typeof zGrid[row + 1][col + 1] === "number" ? zGrid[row + 1][col + 1] : 0
      const zAvg = (z00 + z10 + z01 + z11) / 4

      const p00 = project(xNorm(xVals[col]),     yNorm(yVals[row]),     zNorm(z00))
      const p10 = project(xNorm(xVals[col + 1]), yNorm(yVals[row]),     zNorm(z10))
      const p11 = project(xNorm(xVals[col + 1]), yNorm(yVals[row + 1]), zNorm(z11))
      const p01 = project(xNorm(xVals[col]),     yNorm(yVals[row + 1]), zNorm(z01))

      faces.push({
        corners: [p00, p10, p11, p01],
        sortY: (p00.y + p10.y + p11.y + p01.y) / 4,
        zAvg: zAvg
      })
    }
  }

  /* Painter's sort: farthest (largest y) first */
  faces.sort((a, b) => b.sortY - a.sortY)

  const g = svgEl("g", { transform: `translate(0,0)` }, [])
  root.appendChild(g)

  for (let f = 0; f < faces.length; f = f + 1) {
    const face = faces[f]
    const t = zNorm(face.zAvg)
    const fillColor = _sequentialColor(t)
    const pts = face.corners
    const pointsStr = pts.map((p) => p.x.toFixed(1) + "," + p.y.toFixed(1)).join(" ")
    const zLabel = escapeHtml("z=" + formatNumber(face.zAvg))

    if (style === "shaded" || style === "both") {
      const poly = svgEl("polygon", {
        points: pointsStr,
        fill: fillColor,
        stroke: style === "both" ? "var(--mj-border, #e0e3e9)" : fillColor,
        "stroke-width": style === "both" ? 0.3 : 0,
        part: "surface-face",
        tabindex: "0",
        role: "img",
        "aria-label": zLabel
      }, [])
      poly.appendChild(svgEl("title", null, zLabel))
      const detail = { row: f, zAvg: face.zAvg }
      const handler = () => { ctx.emit("mj-chart-surface-click", detail) }
      poly.addEventListener("click", handler)
      poly.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault()
          handler()
        }
      })
      g.appendChild(poly)
    }

    if (style === "wireframe") {
      const poly = svgEl("polygon", {
        points: pointsStr,
        fill: "none",
        stroke: "var(--mj-border-strong, #c7ccd6)",
        "stroke-width": 0.5
      }, [])
      g.appendChild(poly)
    }
  }

  return root
}


/* ── dispatch ─────────────────────────────────────────────────── */

export function render(ctx) {
  /*
   * Dispatch to contour or surface sub-renderer.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const chartType = ctx.attrs("type", "contour")
  if (chartType === "surface") {
    return _renderSurface(ctx)
  }
  return _renderContour(ctx)
}


registerRenderer("contour", render)
registerRenderer("surface", render)
