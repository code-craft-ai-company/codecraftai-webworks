/*
 * vectorfield.js
 *
 * Vector field (quiver) and streamline renderers.
 *
 * Registered types:
 *   "vector-field"  - quiver plot: arrows showing direction + magnitude
 *   "streamline"    - flow-lines traced through a 2-D vector field
 *
 * Renderer contract: render(ctx) -> SVGElement  (a <g> within [0..width]x[0..height])
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, formatNumber, linePath, smoothPath } from "../svgdraw.js";
import { linearScale, sqrtScale, niceTicks } from "../scales.js";


/* ── color helpers ────────────────────────────────────────────── */

function _magnitudeColor(mag, magMax) {
  /*
   * Map a magnitude value to a blue-to-red sequential color.
   */
  const t = magMax > 0 ? Math.min(mag / magMax, 1) : 0
  const r = Math.round(37  + t * (239 - 37))
  const g = Math.round(99  + t * (68  - 99))
  const b = Math.round(235 + t * (68  - 235))
  const hex = "#" +
    r.toString(16).padStart(2, "0") +
    g.toString(16).padStart(2, "0") +
    b.toString(16).padStart(2, "0")
  return hex
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


/* ── arrowhead ────────────────────────────────────────────────── */

function _arrowhead(x, y, angle, size, color) {
  /*
   * Return a <polygon> arrowhead centered at (x, y) pointing in `angle` radians.
   */
  const tip = { x: x + Math.cos(angle) * size, y: y + Math.sin(angle) * size }
  const left = {
    x: x + Math.cos(angle + Math.PI * 0.8) * size * 0.5,
    y: y + Math.sin(angle + Math.PI * 0.8) * size * 0.5
  }
  const right = {
    x: x + Math.cos(angle - Math.PI * 0.8) * size * 0.5,
    y: y + Math.sin(angle - Math.PI * 0.8) * size * 0.5
  }
  const pts = `${tip.x.toFixed(1)},${tip.y.toFixed(1)} ` +
    `${left.x.toFixed(1)},${left.y.toFixed(1)} ` +
    `${right.x.toFixed(1)},${right.y.toFixed(1)}`
  const poly = svgEl("polygon", {
    points: pts,
    fill: color
  }, [])
  return poly
}


/* ── vector field (quiver) ────────────────────────────────────── */

function _renderVectorField(ctx) {
  /*
   * Render a quiver (arrow) vector field plot.
   */
  const raw = ctx.raw
  const root = svgEl("g", { part: "plot" }, [])

  const vectors = (raw !== null && raw !== undefined && raw.vectors !== null)
    ? raw.vectors : []
  if (vectors.length === 0) {
    return root
  }

  const margin = { top: 16, right: 16, bottom: 44, left: 56 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  /* Domain extents */
  let xMin = Infinity; let xMax = -Infinity
  let yMin = Infinity; let yMax = -Infinity
  let magMax = 0

  for (let i = 0; i < vectors.length; i = i + 1) {
    const v = vectors[i]
    if (v.x < xMin) { xMin = v.x }
    if (v.x > xMax) { xMax = v.x }
    if (v.y < yMin) { yMin = v.y }
    if (v.y > yMax) { yMax = v.y }
    const mag = Math.sqrt(v.u * v.u + v.v * v.v)
    if (mag > magMax) { magMax = mag }
  }
  if (xMin === Infinity) { xMin = 0; xMax = 1 }
  if (yMin === Infinity) { yMin = 0; yMax = 1 }
  if (xMin === xMax) { xMax = xMin + 1 }
  if (yMin === yMax) { yMax = yMin + 1 }

  const xScale = linearScale([xMin, xMax], [0, plotW])
  const yScale = linearScale([yMin, yMax], [plotH, 0])

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  const meta = (raw.meta !== null && raw.meta !== undefined) ? raw.meta : null
  _drawAxes(plot, plotW, plotH, xScale, yScale, meta)

  const normalize = raw.normalize === true
  const scaleAttr = typeof raw.scale === "number" ? raw.scale : 1.0

  /* Cell size estimate for clamping */
  const cellEst = Math.min(plotW, plotH) / Math.max(Math.sqrt(vectors.length), 1)
  const arrowMax = cellEst * 0.8 * scaleAttr

  for (let i = 0; i < vectors.length; i = i + 1) {
    const v = vectors[i]
    const px = xScale(v.x)
    const py = yScale(v.y)
    const mag = Math.sqrt(v.u * v.u + v.v * v.v)
    if (mag === 0) {
      continue
    }

    const arrowLen = normalize ? arrowMax : Math.min(mag / magMax * arrowMax, arrowMax)
    const angle = Math.atan2(v.u, -v.v) /* SVG y-down; field v is up-positive */
    const color = _magnitudeColor(mag, magMax)

    const ex = px + Math.sin(angle) * arrowLen
    const ey = py - Math.cos(angle) * arrowLen

    const shaft = svgEl("line", {
      x1: px.toFixed(2), y1: py.toFixed(2),
      x2: ex.toFixed(2), y2: ey.toFixed(2),
      stroke: color, "stroke-width": 1.5
    }, [])
    const head = _arrowhead(ex, ey, angle, 5, color)

    const label = escapeHtml(
      "(" + formatNumber(v.x) + ", " + formatNumber(v.y) + ") " +
      "u=" + formatNumber(v.u) + " v=" + formatNumber(v.v)
    )
    const g = svgEl("g", {
      part: "vector",
      tabindex: "0",
      role: "img",
      "aria-label": label
    }, [])
    g.appendChild(svgEl("title", null, label))
    g.appendChild(shaft)
    g.appendChild(head)

    const detail = { x: v.x, y: v.y, u: v.u, v: v.v, magnitude: mag }
    const handler = () => { ctx.emit("mj-chart-vector-click", detail) }
    g.addEventListener("click", handler)
    g.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault()
        handler()
      }
    })
    plot.appendChild(g)
  }

  return root
}


/* ── RK4 streamline integrator ────────────────────────────────── */

function _bilinearInterp(gridX, gridY, uGrid, vGrid, x, y) {
  /*
   * Bilinear interpolation of (u, v) at data-space (x, y).
   * Returns { u, v } or null when out of bounds.
   */
  const cols = gridX.length
  const rows = gridY.length
  if (x < gridX[0] || x > gridX[cols - 1] || y < gridY[0] || y > gridY[rows - 1]) {
    return null
  }

  let col = 0
  while (col < cols - 2 && gridX[col + 1] < x) { col = col + 1 }
  let row = 0
  while (row < rows - 2 && gridY[row + 1] < y) { row = row + 1 }

  const tx = (gridX[col + 1] - gridX[col]) > 0
    ? (x - gridX[col]) / (gridX[col + 1] - gridX[col]) : 0
  const ty = (gridY[row + 1] - gridY[row]) > 0
    ? (y - gridY[row]) / (gridY[row + 1] - gridY[row]) : 0

  const u = uGrid[row][col] * (1 - tx) * (1 - ty) +
    uGrid[row][col + 1] * tx * (1 - ty) +
    uGrid[row + 1][col] * (1 - tx) * ty +
    uGrid[row + 1][col + 1] * tx * ty
  const v = vGrid[row][col] * (1 - tx) * (1 - ty) +
    vGrid[row][col + 1] * tx * (1 - ty) +
    vGrid[row + 1][col] * (1 - tx) * ty +
    vGrid[row + 1][col + 1] * tx * ty

  return { u: u, v: v }
}


function _integrateStreamline(gridX, gridY, uGrid, vGrid, x0, y0, maxSteps, stepSize) {
  /*
   * RK4 integration of a streamline from (x0, y0).
   * Returns an array of [x, y] data-space points.
   */
  const points = [[x0, y0]]
  let x = x0
  let y = y0

  for (let step = 0; step < maxSteps; step = step + 1) {
    const k1 = _bilinearInterp(gridX, gridY, uGrid, vGrid, x, y)
    if (k1 === null) { break }

    const k2 = _bilinearInterp(gridX, gridY, uGrid, vGrid,
      x + stepSize * k1.u / 2, y + stepSize * k1.v / 2)
    if (k2 === null) { break }

    const k3 = _bilinearInterp(gridX, gridY, uGrid, vGrid,
      x + stepSize * k2.u / 2, y + stepSize * k2.v / 2)
    if (k3 === null) { break }

    const k4 = _bilinearInterp(gridX, gridY, uGrid, vGrid,
      x + stepSize * k3.u, y + stepSize * k3.v)
    if (k4 === null) { break }

    const dx = (stepSize / 6) * (k1.u + 2 * k2.u + 2 * k3.u + k4.u)
    const dy = (stepSize / 6) * (k1.v + 2 * k2.v + 2 * k3.v + k4.v)

    const speed = Math.sqrt(dx * dx + dy * dy)
    if (speed < 1e-12) { break }

    x = x + dx
    y = y + dy
    points.push([x, y])
  }
  return points
}


/* ── streamline renderer ──────────────────────────────────────── */

function _renderStreamline(ctx) {
  /*
   * Render streamlines for a 2-D vector field.
   */
  const raw = ctx.raw
  const root = svgEl("g", { part: "plot" }, [])

  if (raw === null || raw === undefined) {
    return root
  }

  const margin = { top: 16, right: 16, bottom: 44, left: 56 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  /* Accept pre-computed lines or integrate from grid + seeds */
  let lines = null

  if (raw.lines !== null && raw.lines !== undefined && raw.lines.length > 0) {
    lines = raw.lines
  } else if (raw.grid !== null && raw.grid !== undefined) {
    const grid = raw.grid
    const seeds = (raw.seeds !== null && raw.seeds !== undefined)
      ? raw.seeds : []
    const maxSteps = typeof raw.maxSteps === "number" ? raw.maxSteps : 200
    const stepSize = typeof raw.stepSize === "number" ? raw.stepSize : 0.01

    lines = []
    for (let s = 0; s < seeds.length; s = s + 1) {
      const line = _integrateStreamline(
        grid.x, grid.y, grid.u, grid.v,
        seeds[s][0], seeds[s][1],
        maxSteps, stepSize
      )
      if (line.length > 1) {
        lines.push(line)
      }
    }
  }

  if (lines === null || lines.length === 0) {
    return root
  }

  /* Compute domain from first line set or grid */
  let xMin = Infinity; let xMax = -Infinity
  let yMin = Infinity; let yMax = -Infinity
  for (let l = 0; l < lines.length; l = l + 1) {
    for (let p = 0; p < lines[l].length; p = p + 1) {
      const lx = lines[l][p][0]
      const ly = lines[l][p][1]
      if (lx < xMin) { xMin = lx }
      if (lx > xMax) { xMax = lx }
      if (ly < yMin) { yMin = ly }
      if (ly > yMax) { yMax = ly }
    }
  }
  if (xMin === Infinity) { xMin = 0; xMax = 1; yMin = 0; yMax = 1 }
  if (xMin === xMax) { xMax = xMin + 1 }
  if (yMin === yMax) { yMax = yMin + 1 }

  const xScale = linearScale([xMin, xMax], [0, plotW])
  const yScale = linearScale([yMin, yMax], [plotH, 0])

  const meta = (raw.meta !== null && raw.meta !== undefined) ? raw.meta : null
  _drawAxes(plot, plotW, plotH, xScale, yScale, meta)

  for (let l = 0; l < lines.length; l = l + 1) {
    const pts = lines[l].map((pt) => ({ x: xScale(pt[0]), y: yScale(pt[1]) }))
    const color = ctx.colorFor(l)
    const pathData = smoothPath(pts)
    if (pathData === "") {
      continue
    }
    const pathEl = svgEl("path", {
      d: pathData,
      fill: "none",
      stroke: color,
      "stroke-width": 1.5,
      part: "streamline"
    }, [])
    plot.appendChild(pathEl)

    /* Direction arrow tick at midpoint */
    const midIdx = Math.floor(pts.length / 2)
    if (midIdx > 0 && midIdx < pts.length) {
      const p0 = pts[midIdx - 1]
      const p1 = pts[midIdx]
      const angle = Math.atan2(p1.y - p0.y, p1.x - p0.x)
      const head = _arrowhead(p1.x, p1.y, angle + Math.PI / 2, 5, color)
      plot.appendChild(head)
    }
  }

  return root
}


/* ── arrowhead (reused by streamline) ────────────────────────── */

/* Already defined above as a module-level function */


/* ── dispatch ─────────────────────────────────────────────────── */

export function render(ctx) {
  /*
   * Dispatch to vector-field or streamline sub-renderer.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const chartType = ctx.attrs("type", "vector-field")
  if (chartType === "streamline") {
    return _renderStreamline(ctx)
  }
  return _renderVectorField(ctx)
}


registerRenderer("vector-field", render)
registerRenderer("streamline", render)
