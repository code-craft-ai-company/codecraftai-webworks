/*
 * vectorfield.js
 *
 * Vector field (quiver) and streamline renderers.
 *
 * Registered types (dispatched on ctx.type):
 *   "vector-field" / "vectorfield"  - quiver plot: arrows showing direction
 *                                     and magnitude
 *   "streamline"                    - flow lines traced through a 2-D field
 *
 * Data:
 *   vector-field  { vectors: [{ x, y, u, v }, ...], normalize?, scale? }
 *                 or the structured grid { grid: { x: [...], y: [...],
 *                 u: [[...]], v: [[...]] } } (u[row][col] at (x[col], y[row])).
 *                 u is the x component and v the y component; the y axis
 *                 points up. Arrows are coloured by magnitude (sqrt scale)
 *                 and a colour bar explains the scale.
 *   streamline    { grid: {...as above...}, seeds?: [[x, y], ...],
 *                   maxSteps?, stepSize? }   or   { lines: [[[x, y], ...]] }
 *                 Lines are integrated with RK4 along the field direction in
 *                 both directions from every seed, a fixed arc length per
 *                 step (`stepSize` in data units, default a fifth of the
 *                 smallest grid cell), up to `maxSteps` steps each way.
 *                 Without seeds the domain is seeded on a regular lattice.
 *                 Points may be [x, y] pairs or { x, y } objects. With a grid,
 *                 each line is coloured by its mean speed.
 *
 * Events: mj-chart-vector-click { x, y, u, v, magnitude },
 *         mj-chart-streamline-click { index, seed, points, meanSpeed }
 *
 * Renderer contract: render(ctx) -> SVGElement  (a <g> within [0..width]x[0..height])
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber, smoothPath } from "../svgdraw.js";
import { linearScale, sqrtScale, niceTicks } from "../scales.js";

const MARGIN = { top: 16, right: 16, bottom: 44, left: 56 };
const LEGEND_WIDTH = 58;
const HEAD_SIZE = 6;

/* Sequential magnitude ramp from theme tokens (reads in both themes). */
const RAMP_STOPS = [
  "color-mix(in oklab, var(--mj-accent, #2563eb) 35%, var(--mj-surface, #ffffff))",
  "var(--mj-accent, #2563eb)",
  "color-mix(in oklab, var(--mj-accent, #2563eb) 45%, var(--mj-text, #14181f))"
];


/* ── helpers ──────────────────────────────────────────────────── */

function _isNumber(value) {
  /*
   * True for a finite number.
   */
  const numeric = typeof value === "number" && Number.isFinite(value) === true
  return numeric
}


function _rampColor(t) {
  /*
   * The ramp colour of a normalised value t in [0, 1].
   */
  const clamped = _isNumber(t) === true ? Math.max(0, Math.min(1, t)) : 0
  const scaled = clamped * (RAMP_STOPS.length - 1)
  const lo = Math.min(Math.floor(scaled), RAMP_STOPS.length - 2)
  const share = Math.round((scaled - lo) * 100)
  let color = RAMP_STOPS[lo]
  if (share >= 100) {
    color = RAMP_STOPS[lo + 1]
  } else if (share > 0) {
    color = `color-mix(in oklab, ${RAMP_STOPS[lo + 1]} ${share}%, ${RAMP_STOPS[lo]})`
  }
  return color
}


function _attachActivation(element, ctx, eventName, detail) {
  /*
   * Emit an interaction event on click and on Enter / Space.
   */
  const handler = () => { ctx.emit(eventName, detail) }
  element.addEventListener("click", handler)
  element.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault()
      handler()
    }
  })
  return
}


function _plotBox(ctx, withLegend) {
  /*
   * The plot area inside the margins (and the colour-bar column).
   */
  const legendSpace = withLegend === true && ctx.width > 300 ? LEGEND_WIDTH : 0
  const plotW = Math.max(ctx.width - MARGIN.left - MARGIN.right - legendSpace, 10)
  const plotH = Math.max(ctx.height - MARGIN.top - MARGIN.bottom, 10)
  const box = { plotW: plotW, plotH: plotH, legendSpace: legendSpace }
  return box
}


function _drawAxes(plot, plotW, plotH, xScale, yScale, meta) {
  /*
   * Gridlines, tick labels and axis titles (hidden from assistive
   * technology).
   */
  const axes = svgEl("g", { "aria-hidden": "true", part: "axes" }, [])
  const xTicks = xScale.ticks(5)
  for (let i = 0; i < xTicks.length; i = i + 1) {
    const px = xScale(xTicks[i])
    axes.appendChild(svgEl("line", {
      x1: px, y1: 0, x2: px, y2: plotH,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    axes.appendChild(svgEl("text", {
      x: px, y: plotH + 14, "text-anchor": "middle",
      "font-size": 10, fill: "var(--mj-text-muted, #6b7280)"
    }, formatNumber(xTicks[i])))
  }

  const yTicks = yScale.ticks(5)
  for (let i = 0; i < yTicks.length; i = i + 1) {
    const py = yScale(yTicks[i])
    axes.appendChild(svgEl("line", {
      x1: 0, y1: py, x2: plotW, y2: py,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    axes.appendChild(svgEl("text", {
      x: -6, y: py + 4, "text-anchor": "end",
      "font-size": 10, fill: "var(--mj-text-muted, #6b7280)"
    }, formatNumber(yTicks[i])))
  }

  if (meta !== null && meta !== undefined) {
    if (typeof meta.xLabel === "string" && meta.xLabel.length > 0) {
      axes.appendChild(svgEl("text", {
        x: plotW / 2, y: plotH + 32, "text-anchor": "middle",
        "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
      }, meta.xLabel))
    }
    if (typeof meta.yLabel === "string" && meta.yLabel.length > 0) {
      axes.appendChild(svgEl("text", {
        transform: `rotate(-90) translate(${-plotH / 2}, -40)`,
        "text-anchor": "middle",
        "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
      }, meta.yLabel))
    }
  }
  plot.appendChild(axes)
  return
}


function _drawColorBar(root, ctx, box, maxValue, title) {
  /*
   * A vertical colour bar for the magnitude ramp (sqrt-scaled values).
   */
  if (box.legendSpace === 0 || maxValue <= 0) {
    return
  }
  const barX = ctx.width - box.legendSpace + 10
  const barTop = MARGIN.top + 14
  const barH = Math.max(Math.min(box.plotH - 14, 160), 30)
  const steps = 20
  const legend = svgEl("g", { "aria-hidden": "true", part: "legend" }, [])
  for (let i = 0; i < steps; i = i + 1) {
    legend.appendChild(svgEl("rect", {
      x: barX, y: barTop + barH - ((i + 1) / steps) * barH,
      width: 10, height: barH / steps + 0.5,
      fill: _rampColor((i + 0.5) / steps)
    }, []))
  }
  /* The bar position is sqrt(value / max), matching the arrow colours. */
  const position = sqrtScale([0, maxValue], [barTop + barH, barTop])
  const ticks = niceTicks(0, maxValue, 4)
  for (let i = 0; i < ticks.length; i = i + 1) {
    if (ticks[i] > maxValue * 1.0001) {
      continue
    }
    legend.appendChild(svgEl("text", {
      x: barX + 14, y: position(ticks[i]) + 3,
      "font-size": 9, fill: "var(--mj-text-muted, #6b7280)"
    }, formatNumber(ticks[i])))
  }
  legend.appendChild(svgEl("text", {
    x: barX, y: barTop - 6, "font-size": 9, fill: "var(--mj-text-muted, #6b7280)"
  }, title))
  root.appendChild(legend)
  return
}


/* ── arrowhead ────────────────────────────────────────────────── */

function _arrowhead(x, y, angle, size, color) {
  /*
   * A <polygon> arrowhead whose tip is at (x, y), pointing along `angle`
   * (radians, screen coordinates: 0 = right, positive = clockwise /
   * downward, i.e. Math.atan2(dy, dx) of the screen direction).
   */
  const back = (offset) => ({
    x: x - Math.cos(angle + offset) * size,
    y: y - Math.sin(angle + offset) * size
  })
  const left = back(0.45)
  const right = back(-0.45)
  const pts = `${x.toFixed(1)},${y.toFixed(1)} ` +
    `${left.x.toFixed(1)},${left.y.toFixed(1)} ` +
    `${right.x.toFixed(1)},${right.y.toFixed(1)}`
  const poly = svgEl("polygon", {
    points: pts,
    fill: color
  }, [])
  return poly
}


/* ── field input ──────────────────────────────────────────────── */

function _numberList(value) {
  /*
   * The array when it is a non-empty list of finite numbers, else null.
   */
  if (Array.isArray(value) === false || value.length === 0) {
    return null
  }
  for (let index = 0; index < value.length; index = index + 1) {
    if (_isNumber(value[index]) === false) {
      return null
    }
  }
  return value
}


function _readGrid(rawGrid) {
  /*
   * Validate a structured grid { x, y, u, v }. Returns null when the shape
   * is unusable; missing or non-numeric u/v cells read as null.
   */
  if (rawGrid === null || typeof rawGrid !== "object") {
    return null
  }
  const xs = _numberList(rawGrid.x)
  const ys = _numberList(rawGrid.y)
  if (xs === null || ys === null || Array.isArray(rawGrid.u) === false ||
      Array.isArray(rawGrid.v) === false) {
    return null
  }
  const cellOf = (rows, row, col) => {
    const line = rows[row]
    const value = Array.isArray(line) === true ? line[col] : null
    return _isNumber(value) === true ? value : null
  }
  const grid = {
    x: xs,
    y: ys,
    u: (row, col) => cellOf(rawGrid.u, row, col),
    v: (row, col) => cellOf(rawGrid.v, row, col)
  }
  return grid
}


function _vectorsOf(raw) {
  /*
   * The drawable vectors: raw.vectors, else the expanded grid shorthand.
   */
  const list = []
  if (Array.isArray(raw.vectors) === true) {
    for (let i = 0; i < raw.vectors.length; i = i + 1) {
      const v = raw.vectors[i]
      if (v !== null && typeof v === "object" && _isNumber(v.x) === true &&
          _isNumber(v.y) === true && _isNumber(v.u) === true && _isNumber(v.v) === true) {
        list.push({ x: v.x, y: v.y, u: v.u, v: v.v })
      }
    }
    return list
  }
  const grid = _readGrid(raw.grid)
  if (grid !== null) {
    for (let row = 0; row < grid.y.length; row = row + 1) {
      for (let col = 0; col < grid.x.length; col = col + 1) {
        const u = grid.u(row, col)
        const v = grid.v(row, col)
        if (u !== null && v !== null) {
          list.push({ x: grid.x[col], y: grid.y[row], u: u, v: v })
        }
      }
    }
  }
  return list
}


function _spacing(values) {
  /*
   * The smallest positive gap between the distinct sorted values (0 when
   * there is a single distinct value).
   */
  const sorted = Array.from(new Set(values)).sort((a, b) => a - b)
  let gap = 0
  for (let i = 1; i < sorted.length; i = i + 1) {
    const step = sorted[i] - sorted[i - 1]
    if (step > 0 && (gap === 0 || step < gap)) {
      gap = step
    }
  }
  return gap
}


/* ── vector field (quiver) ────────────────────────────────────── */

function _renderVectorField(ctx) {
  /*
   * Render a quiver (arrow) vector field plot.
   */
  const raw = ctx.raw !== null && ctx.raw !== undefined ? ctx.raw : {}
  const root = svgEl("g", { part: "plot" }, [])

  const vectors = _vectorsOf(raw)
  if (vectors.length === 0) {
    return root
  }

  const box = _plotBox(ctx, true)
  const { plotW, plotH } = box

  let xMin = Infinity
  let xMax = -Infinity
  let yMin = Infinity
  let yMax = -Infinity
  let magMax = 0
  for (let i = 0; i < vectors.length; i = i + 1) {
    const v = vectors[i]
    xMin = Math.min(xMin, v.x)
    xMax = Math.max(xMax, v.x)
    yMin = Math.min(yMin, v.y)
    yMax = Math.max(yMax, v.y)
    magMax = Math.max(magMax, Math.hypot(v.u, v.v))
  }

  const normalize = raw.normalize === true
  const scaleFactor = _isNumber(raw.scale) === true && raw.scale > 0 ? raw.scale : 1.0

  /*
   * The longest arrow spans 0.85 x scale grid cells; the domain is padded
   * by a little more than that, so arrows on the boundary stay inside.
   */
  let dx = _spacing(vectors.map((v) => v.x))
  let dy = _spacing(vectors.map((v) => v.y))
  if (dx === 0) {
    dx = dy > 0 ? dy : 1
  }
  if (dy === 0) {
    dy = dx
  }
  const pad = Math.max(0.6, 0.9 * scaleFactor)
  const xScale = linearScale([xMin - dx * pad, xMax + dx * pad], [0, plotW])
  const yScale = linearScale([yMin - dy * pad, yMax + dy * pad], [plotH, 0])

  const plot = svgEl("g", {
    transform: `translate(${MARGIN.left},${MARGIN.top})`
  }, [])
  root.appendChild(plot)
  _drawAxes(plot, plotW, plotH, xScale, yScale, ctx.model.meta)

  const cellPx = Math.min(Math.abs(xScale(dx) - xScale(0)), Math.abs(yScale(0) - yScale(dy)))
  const arrowMax = Math.max(cellPx * 0.85 * scaleFactor, 6)
  const colorT = sqrtScale([0, magMax > 0 ? magMax : 1], [0, 1])

  const marks = svgEl("g", { part: "vectors" }, [])
  plot.appendChild(marks)
  const tableRows = []

  for (let i = 0; i < vectors.length; i = i + 1) {
    const v = vectors[i]
    const px = xScale(v.x)
    const py = yScale(v.y)
    const mag = Math.hypot(v.u, v.v)
    const color = _rampColor(colorT(mag))
    const label = `(${formatNumber(v.x)}, ${formatNumber(v.y)}): u ${formatNumber(v.u)}, ` +
      `v ${formatNumber(v.v)}, magnitude ${formatNumber(mag, { maximumFractionDigits: 3 })}`
    const g = svgEl("g", {
      part: "vector",
      tabindex: "0",
      role: "img",
      "aria-label": label
    }, [svgEl("title", null, label)])

    if (mag === 0 || magMax === 0) {
      /* A zero vector is a dot, so the sample is still visible. */
      g.appendChild(svgEl("circle", { cx: px, cy: py, r: 2, fill: color }, []))
    } else {
      const arrowLen = normalize === true ? arrowMax : (mag / magMax) * arrowMax
      /* Screen direction: u to the right, v up (the screen y axis points down). */
      const sx = v.u / mag
      const sy = -v.v / mag
      const ex = px + sx * arrowLen
      const ey = py + sy * arrowLen
      const head = Math.min(HEAD_SIZE, arrowLen * 0.6)
      g.appendChild(svgEl("line", {
        x1: px.toFixed(2), y1: py.toFixed(2),
        x2: (ex - sx * head * 0.6).toFixed(2), y2: (ey - sy * head * 0.6).toFixed(2),
        stroke: color, "stroke-width": 1.5, "stroke-linecap": "round"
      }, []))
      g.appendChild(_arrowhead(ex, ey, Math.atan2(sy, sx), head, color))
    }

    _attachActivation(g, ctx, "mj-chart-vector-click", { x: v.x, y: v.y, u: v.u, v: v.v, magnitude: mag })
    marks.appendChild(g)
    tableRows.push([v.x, v.y, v.u, v.v, mag])
  }

  _drawColorBar(root, ctx, box, magMax, "|v|")
  ctx.setTable({ columns: ["x", "y", "u", "v", "Magnitude"], rows: tableRows })
  return root
}


/* ── RK4 streamline integrator ────────────────────────────────── */

function _locate(values, value) {
  /*
   * The cell index i with values[i] <= value <= values[i + 1] of an
   * ascending axis, or -1 outside it.
   */
  const last = values.length - 1
  if (value < values[0] || value > values[last]) {
    return -1
  }
  let index = 0
  while (index < last - 1 && values[index + 1] < value) {
    index = index + 1
  }
  return index
}


function _bilinearInterp(grid, x, y) {
  /*
   * Bilinear interpolation of (u, v) at data-space (x, y). Returns { u, v }
   * or null when out of bounds or next to a missing cell.
   */
  const col = _locate(grid.x, x)
  const row = _locate(grid.y, y)
  if (col < 0 || row < 0 || grid.x.length < 2 || grid.y.length < 2) {
    return null
  }
  const corners = [
    [grid.u(row, col), grid.v(row, col)],
    [grid.u(row, col + 1), grid.v(row, col + 1)],
    [grid.u(row + 1, col), grid.v(row + 1, col)],
    [grid.u(row + 1, col + 1), grid.v(row + 1, col + 1)]
  ]
  for (let i = 0; i < corners.length; i = i + 1) {
    if (corners[i][0] === null || corners[i][1] === null) {
      return null
    }
  }
  const spanX = grid.x[col + 1] - grid.x[col]
  const spanY = grid.y[row + 1] - grid.y[row]
  const tx = spanX > 0 ? (x - grid.x[col]) / spanX : 0
  const ty = spanY > 0 ? (y - grid.y[row]) / spanY : 0
  const weights = [(1 - tx) * (1 - ty), tx * (1 - ty), (1 - tx) * ty, tx * ty]
  let u = 0
  let v = 0
  for (let i = 0; i < 4; i = i + 1) {
    u = u + corners[i][0] * weights[i]
    v = v + corners[i][1] * weights[i]
  }
  return { u: u, v: v }
}


function _direction(grid, x, y, sign) {
  /*
   * The unit field direction at (x, y) (times sign), its speed, or null.
   */
  const field = _bilinearInterp(grid, x, y)
  if (field === null) {
    return null
  }
  const speed = Math.hypot(field.u, field.v)
  if (speed < 1e-12) {
    return null
  }
  const result = { u: sign * field.u / speed, v: sign * field.v / speed, speed: speed }
  return result
}


function _traceOneWay(grid, x0, y0, maxSteps, stepSize, sign) {
  /*
   * RK4 along the normalised field from (x0, y0): each step advances a
   * fixed arc length. Stops at maxSteps, at the domain edge, at a
   * stagnation point, or when the line returns to its start (a closed
   * orbit). Returns { points: [[x, y], ...], speeds: [...] }.
   */
  const points = []
  const speeds = []
  let x = x0
  let y = y0
  const h = stepSize

  for (let step = 0; step < maxSteps; step = step + 1) {
    const k1 = _direction(grid, x, y, sign)
    if (k1 === null) { break }
    const k2 = _direction(grid, x + h * k1.u / 2, y + h * k1.v / 2, sign)
    if (k2 === null) { break }
    const k3 = _direction(grid, x + h * k2.u / 2, y + h * k2.v / 2, sign)
    if (k3 === null) { break }
    const k4 = _direction(grid, x + h * k3.u, y + h * k3.v, sign)
    if (k4 === null) { break }

    x = x + (h / 6) * (k1.u + 2 * k2.u + 2 * k3.u + k4.u)
    y = y + (h / 6) * (k1.v + 2 * k2.v + 2 * k3.v + k4.v)
    points.push([x, y])
    speeds.push(k1.speed)

    if (step > 8 && Math.hypot(x - x0, y - y0) < h * 0.75) {
      break
    }
  }
  return { points: points, speeds: speeds }
}


function _integrateStreamline(grid, x0, y0, maxSteps, stepSize) {
  /*
   * A streamline through (x0, y0), traced backward and forward.
   */
  const backward = _traceOneWay(grid, x0, y0, maxSteps, stepSize, -1)
  const forward = _traceOneWay(grid, x0, y0, maxSteps, stepSize, 1)
  const start = _bilinearInterp(grid, x0, y0)
  const points = backward.points.slice().reverse().concat([[x0, y0]], forward.points)
  const speeds = backward.speeds.concat(forward.speeds)
  if (start !== null) {
    speeds.push(Math.hypot(start.u, start.v))
  }
  let meanSpeed = 0
  for (let i = 0; i < speeds.length; i = i + 1) {
    meanSpeed = meanSpeed + speeds[i]
  }
  meanSpeed = speeds.length > 0 ? meanSpeed / speeds.length : 0
  return { points: points, meanSpeed: meanSpeed, seed: [x0, y0] }
}


function _pointXY(point) {
  /*
   * An [x, y] pair from an [x, y] array or an {x, y} object, or null.
   */
  let pair = null
  if (Array.isArray(point) === true && _isNumber(point[0]) === true && _isNumber(point[1]) === true) {
    pair = [point[0], point[1]]
  } else if (point !== null && typeof point === "object" && _isNumber(point.x) === true &&
      _isNumber(point.y) === true) {
    pair = [point.x, point.y]
  }
  return pair
}


function _autoSeeds(grid) {
  /*
   * A regular lattice of seeds inside the grid domain.
   */
  const seeds = []
  const x0 = grid.x[0]
  const x1 = grid.x[grid.x.length - 1]
  const y0 = grid.y[0]
  const y1 = grid.y[grid.y.length - 1]
  const across = 6
  const down = 5
  for (let j = 0; j < down; j = j + 1) {
    for (let i = 0; i < across; i = i + 1) {
      seeds.push([x0 + ((i + 0.5) / across) * (x1 - x0), y0 + ((j + 0.5) / down) * (y1 - y0)])
    }
  }
  return seeds
}


/* ── streamline renderer ──────────────────────────────────────── */

function _renderStreamline(ctx) {
  /*
   * Render streamlines for a 2-D vector field.
   */
  const raw = ctx.raw !== null && ctx.raw !== undefined ? ctx.raw : {}
  const root = svgEl("g", { part: "plot" }, [])

  const grid = _readGrid(raw.grid)
  let lines = []

  if (Array.isArray(raw.lines) === true && raw.lines.length > 0) {
    for (let l = 0; l < raw.lines.length; l = l + 1) {
      const source = Array.isArray(raw.lines[l]) === true ? raw.lines[l] : []
      const points = source.map(_pointXY).filter((p) => p !== null)
      if (points.length > 1) {
        lines.push({ points: points, meanSpeed: null, seed: points[0] })
      }
    }
  } else if (grid !== null && grid.x.length > 1 && grid.y.length > 1) {
    const cellX = _spacing(grid.x)
    const cellY = _spacing(grid.y)
    const cell = Math.min(cellX > 0 ? cellX : 1, cellY > 0 ? cellY : 1)
    const maxSteps = _isNumber(raw.maxSteps) === true && raw.maxSteps > 0
      ? Math.min(Math.round(raw.maxSteps), 5000) : 200
    const stepSize = _isNumber(raw.stepSize) === true && raw.stepSize > 0 ? raw.stepSize : cell / 5
    const givenSeeds = Array.isArray(raw.seeds) === true ? raw.seeds.map(_pointXY).filter((p) => p !== null) : []
    const seeds = givenSeeds.length > 0 ? givenSeeds : _autoSeeds(grid)
    for (let s = 0; s < seeds.length; s = s + 1) {
      const line = _integrateStreamline(grid, seeds[s][0], seeds[s][1], maxSteps, stepSize)
      if (line.points.length > 1) {
        lines.push(line)
      }
    }
  }

  if (lines.length === 0) {
    return root
  }

  /* The domain is the grid's when there is one, else the lines' extent. */
  let xMin = Infinity
  let xMax = -Infinity
  let yMin = Infinity
  let yMax = -Infinity
  if (grid !== null) {
    xMin = Math.min(...grid.x)
    xMax = Math.max(...grid.x)
    yMin = Math.min(...grid.y)
    yMax = Math.max(...grid.y)
  } else {
    for (let l = 0; l < lines.length; l = l + 1) {
      for (let p = 0; p < lines[l].points.length; p = p + 1) {
        xMin = Math.min(xMin, lines[l].points[p][0])
        xMax = Math.max(xMax, lines[l].points[p][0])
        yMin = Math.min(yMin, lines[l].points[p][1])
        yMax = Math.max(yMax, lines[l].points[p][1])
      }
    }
  }

  let speedMax = 0
  for (let l = 0; l < lines.length; l = l + 1) {
    if (lines[l].meanSpeed !== null) {
      speedMax = Math.max(speedMax, lines[l].meanSpeed)
    }
  }
  const colourBySpeed = speedMax > 0
  const box = _plotBox(ctx, colourBySpeed)
  const { plotW, plotH } = box

  const xScale = linearScale([xMin, xMax], [0, plotW])
  const yScale = linearScale([yMin, yMax], [plotH, 0])

  const plot = svgEl("g", {
    transform: `translate(${MARGIN.left},${MARGIN.top})`
  }, [])
  root.appendChild(plot)
  _drawAxes(plot, plotW, plotH, xScale, yScale, ctx.model.meta)

  const colorT = sqrtScale([0, speedMax > 0 ? speedMax : 1], [0, 1])
  const marks = svgEl("g", { part: "streamlines" }, [])
  plot.appendChild(marks)
  const tableRows = []

  for (let l = 0; l < lines.length; l = l + 1) {
    const line = lines[l]
    const pts = line.points.map((pt) => ({ x: xScale(pt[0]), y: yScale(pt[1]) }))
    const color = colourBySpeed === true ? _rampColor(colorT(line.meanSpeed)) : ctx.colorFor(0)
    const pathData = smoothPath(pts)
    if (pathData === "") {
      continue
    }
    const first = line.points[0]
    const last = line.points[line.points.length - 1]
    let label = `Streamline ${l + 1}: from (${formatNumber(first[0], { maximumFractionDigits: 2 })}, ` +
      `${formatNumber(first[1], { maximumFractionDigits: 2 })}) to ` +
      `(${formatNumber(last[0], { maximumFractionDigits: 2 })}, ${formatNumber(last[1], { maximumFractionDigits: 2 })})`
    if (line.meanSpeed !== null) {
      label = label + `, mean speed ${formatNumber(line.meanSpeed, { maximumFractionDigits: 3 })}`
    }
    const group = svgEl("g", {
      part: "streamline",
      tabindex: "0",
      role: "img",
      "aria-label": label
    }, [svgEl("title", null, label)])
    group.appendChild(svgEl("path", {
      d: pathData,
      fill: "none",
      stroke: color,
      "stroke-width": 1.6,
      "stroke-linecap": "round"
    }, []))

    /* Direction arrow at the middle of the line, along the local tangent. */
    const midIdx = Math.floor(pts.length / 2)
    if (midIdx > 0 && midIdx < pts.length) {
      const p0 = pts[midIdx - 1]
      const p1 = pts[midIdx]
      if (Math.hypot(p1.x - p0.x, p1.y - p0.y) > 0.01) {
        group.appendChild(_arrowhead(p1.x, p1.y, Math.atan2(p1.y - p0.y, p1.x - p0.x), HEAD_SIZE, color))
      }
    }
    _attachActivation(group, ctx, "mj-chart-streamline-click", {
      index: l, seed: line.seed, points: line.points.length, meanSpeed: line.meanSpeed
    })
    marks.appendChild(group)
    tableRows.push([`Streamline ${l + 1}`, line.seed[0], line.seed[1], first[0], first[1],
      last[0], last[1], line.meanSpeed === null ? "" : line.meanSpeed])
  }

  if (colourBySpeed === true) {
    _drawColorBar(root, ctx, box, speedMax, "speed")
  }
  ctx.setTable({
    columns: ["Line", "Seed x", "Seed y", "Start x", "Start y", "End x", "End y", "Mean speed"],
    rows: tableRows
  })
  return root
}


/* ── dispatch ─────────────────────────────────────────────────── */

export function render(ctx) {
  /*
   * Dispatch to the vector-field or streamline sub-renderer.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const chartType = typeof ctx.type === "string" ? ctx.type : ctx.attrs("type", "vector-field")
  let root = null
  if (chartType === "streamline") {
    root = _renderStreamline(ctx)
  } else {
    root = _renderVectorField(ctx)
  }
  return root
}


registerRenderer("vector-field", render, { legend: "none" })
registerRenderer("vectorfield", render, { legend: "none" })
registerRenderer("streamline", render, { legend: "none" })
