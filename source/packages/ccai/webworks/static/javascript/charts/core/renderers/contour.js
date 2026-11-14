/*
 * contour.js
 *
 * 3-D surface renderer (a shaded 2-D projection of z = f(x, y)).
 *
 * Registered types:
 *   "surface"  - shaded or wireframe projection of a height field
 *
 * The grid contour plot (`type="contour"`) is drawn by density.js, which
 * owns that type key; this file used to carry a second, unreachable
 * contour renderer and no longer registers it.
 *
 * Data:
 *   {
 *     grid: { x: [x0, x1, ...], y: [y0, y1, ...], z: [[z(row 0)], ...] },
 *     projection: "isometric" | "oblique",     (also the `projection` attribute)
 *     style: "shaded" | "wireframe" | "both",  (also the `variant` attribute)
 *     meta: { xLabel, yLabel, zLabel }
 *   }
 *   z[row][col] is the height at (x[col], y[row]). A cell that is not a
 *   finite number is a hole: the faces that touch it are not drawn.
 *
 * Drawing: faces are painted far to near (painter's algorithm on grid
 * depth), the projected bounding box is fitted inside the plot, the three
 * floor-level axis legs carry ticks and labels, and a colour bar explains
 * the height colours.
 *
 * Events: mj-chart-surface-click { row, col, x0, x1, y0, y1, corners, zAvg }
 *
 * Renderer contract: render(ctx) -> SVGElement  (a <g> within [0..width]x[0..height])
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber } from "../svgdraw.js";
import { linearScale, niceTicks } from "../scales.js";

const MARGIN = 24;
const LEGEND_WIDTH = 64;

/*
 * Sequential height ramp built from theme tokens: a faint accent tint over
 * the surface, the accent itself, then the accent mixed toward the text
 * colour, so the scale reads in the light and the dark theme.
 */
const RAMP_STOPS = [
  "color-mix(in oklab, var(--mj-accent, #2563eb) 14%, var(--mj-surface, #ffffff))",
  "color-mix(in oklab, var(--mj-accent, #2563eb) 55%, var(--mj-surface, #ffffff))",
  "var(--mj-accent, #2563eb)",
  "color-mix(in oklab, var(--mj-accent, #2563eb) 50%, var(--mj-text, #14181f))"
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


function _cell(zGrid, row, col) {
  /*
   * A height cell, or null when the row is missing or the value is a hole.
   */
  const line = zGrid[row]
  if (Array.isArray(line) === false) {
    return null
  }
  const value = line[col]
  return _isNumber(value) === true ? value : null
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


/* ── projection ───────────────────────────────────────────────── */

function _projector(projection) {
  /*
   * Unit-space projection of normalised (nx, ny, nz) in [0, 1]^3 to an
   * unscaled 2-D point, and the depth key used to paint far faces first
   * (a larger key is nearer the viewer).
   *
   *   isometric: x' = (nx - ny) cos30,  y' = (nx + ny) sin30 - 0.8 nz
   *              viewer at +x +y, so depth = nx + ny
   *   oblique:   x' = nx + 0.5 ny,      y' = 0.35 ny - 0.8 nz
   *              viewer in front (+y), slightly to the -x side
   */
  const cos30 = Math.cos(Math.PI / 6)
  const sin30 = Math.sin(Math.PI / 6)
  let result = null
  if (projection === "oblique") {
    result = {
      point: (nx, ny, nz) => ({ x: nx + ny * 0.5, y: ny * 0.35 - nz * 0.8 }),
      depth: (nx, ny) => ny - nx * 0.5
    }
  } else {
    result = {
      point: (nx, ny, nz) => ({ x: (nx - ny) * cos30, y: (nx + ny) * sin30 - nz * 0.8 }),
      depth: (nx, ny) => nx + ny
    }
  }
  return result
}


/* ── surface renderer ─────────────────────────────────────────── */

function _renderSurface(ctx) {
  /*
   * Render a projected surface as shaded quadrilateral faces with axes and
   * a height colour bar.
   */
  const raw = ctx.raw !== null && ctx.raw !== undefined ? ctx.raw : {}
  const root = svgEl("g", { part: "plot" }, [])
  const meta = ctx.model.meta

  const grid = raw.grid !== null && typeof raw.grid === "object" ? raw.grid : null
  const xVals = grid !== null ? _numberList(grid.x) : null
  const yVals = grid !== null ? _numberList(grid.y) : null
  const zGrid = grid !== null && Array.isArray(grid.z) === true ? grid.z : null
  if (xVals === null || yVals === null || zGrid === null ||
      xVals.length < 2 || yVals.length < 2) {
    return root
  }

  const projectionAttr = ctx.attrs("projection", null)
  const projectionName = projectionAttr !== null ? projectionAttr : raw.projection
  const projection = projectionName === "oblique" ? "oblique" : "isometric"
  const styleAttr = ctx.attrs("style", null)
  const styleName = styleAttr !== null ? styleAttr : raw.style
  const style = styleName === "wireframe" || styleName === "both" ? styleName : "shaded"

  /* Extents (holes ignored). */
  const xMin = Math.min(...xVals)
  const xMax = Math.max(...xVals)
  const yMin = Math.min(...yVals)
  const yMax = Math.max(...yVals)
  let zMin = Infinity
  let zMax = -Infinity
  for (let row = 0; row < yVals.length; row = row + 1) {
    for (let col = 0; col < xVals.length; col = col + 1) {
      const z = _cell(zGrid, row, col)
      if (z !== null) {
        zMin = Math.min(zMin, z)
        zMax = Math.max(zMax, z)
      }
    }
  }
  if (zMin === Infinity) {
    return root
  }
  if (zMin === zMax) {
    zMin = zMin - 0.5
    zMax = zMax + 0.5
  }

  const xNorm = linearScale([xMin, xMax], [0, 1])
  const yNorm = linearScale([yMin, yMax], [0, 1])
  const zNorm = linearScale([zMin, zMax], [0, 1])
  const projector = _projector(projection)

  /* Fit the projected bounding box of the whole cube inside the plot. */
  const corners = []
  for (const nx of [0, 1]) {
    for (const ny of [0, 1]) {
      for (const nz of [0, 1]) {
        corners.push(projector.point(nx, ny, nz))
      }
    }
  }
  const boxX0 = Math.min(...corners.map((p) => p.x))
  const boxX1 = Math.max(...corners.map((p) => p.x))
  const boxY0 = Math.min(...corners.map((p) => p.y))
  const boxY1 = Math.max(...corners.map((p) => p.y))

  const legendSpace = ctx.width > 260 ? LEGEND_WIDTH : 0
  const availW = Math.max(ctx.width - MARGIN * 2 - legendSpace - 40, 20)
  const availH = Math.max(ctx.height - MARGIN * 2 - 20, 20)
  const unit = Math.min(availW / (boxX1 - boxX0), availH / (boxY1 - boxY0))
  const offsetX = MARGIN + 30 + (availW - (boxX1 - boxX0) * unit) / 2 - boxX0 * unit
  const offsetY = MARGIN + (availH - (boxY1 - boxY0) * unit) / 2 - boxY0 * unit

  const project = (nx, ny, nz) => {
    const p = projector.point(nx, ny, nz)
    return { x: p.x * unit + offsetX, y: p.y * unit + offsetY }
  }

  /* Back walls and floor outline (decoration). */
  const decor = svgEl("g", { "aria-hidden": "true", part: "grid" }, [])
  const floor = [project(0, 0, 0), project(1, 0, 0), project(1, 1, 0), project(0, 1, 0)]
  decor.appendChild(svgEl("polygon", {
    points: floor.map((p) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" "),
    fill: "none",
    stroke: "var(--mj-border, #e0e3e9)",
    "stroke-width": 1
  }, []))
  root.appendChild(decor)

  /* Faces, with their grid position kept for events and the table. */
  const faces = []
  for (let row = 0; row < yVals.length - 1; row = row + 1) {
    for (let col = 0; col < xVals.length - 1; col = col + 1) {
      const z00 = _cell(zGrid, row, col)
      const z10 = _cell(zGrid, row, col + 1)
      const z11 = _cell(zGrid, row + 1, col + 1)
      const z01 = _cell(zGrid, row + 1, col)
      if (z00 === null || z10 === null || z11 === null || z01 === null) {
        continue
      }
      const nx0 = xNorm(xVals[col])
      const nx1 = xNorm(xVals[col + 1])
      const ny0 = yNorm(yVals[row])
      const ny1 = yNorm(yVals[row + 1])
      faces.push({
        row: row,
        col: col,
        corners: [
          project(nx0, ny0, zNorm(z00)),
          project(nx1, ny0, zNorm(z10)),
          project(nx1, ny1, zNorm(z11)),
          project(nx0, ny1, zNorm(z01))
        ],
        values: [z00, z10, z11, z01],
        depth: projector.depth((nx0 + nx1) / 2, (ny0 + ny1) / 2),
        zAvg: (z00 + z10 + z11 + z01) / 4
      })
    }
  }

  /* Painter's algorithm: the farthest faces first. */
  faces.sort((a, b) => a.depth - b.depth)

  const faceGroup = svgEl("g", { part: "surface" }, [])
  root.appendChild(faceGroup)

  for (let f = 0; f < faces.length; f = f + 1) {
    const face = faces[f]
    const pointsStr = face.corners.map((p) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ")
    const x0 = xVals[face.col]
    const x1 = xVals[face.col + 1]
    const y0 = yVals[face.row]
    const y1 = yVals[face.row + 1]
    const label = `x ${formatNumber(x0)}–${formatNumber(x1)}, ` +
      `y ${formatNumber(y0)}–${formatNumber(y1)}: z ${formatNumber(face.zAvg, { maximumFractionDigits: 3 })}`

    let fill = _rampColor(zNorm(face.zAvg))
    let stroke = fill
    let strokeWidth = 0.4
    if (style === "wireframe") {
      /* Hidden lines are removed by an opaque surface-coloured face. */
      fill = "var(--mj-surface, #ffffff)"
      stroke = "var(--mj-text-muted, #5f6673)"
      strokeWidth = 0.7
    } else if (style === "both") {
      stroke = "var(--mj-surface, #ffffff)"
      strokeWidth = 0.4
    }

    const poly = svgEl("polygon", {
      points: pointsStr,
      fill: fill,
      stroke: stroke,
      "stroke-width": strokeWidth,
      "stroke-linejoin": "round",
      part: "surface-face",
      tabindex: "0",
      role: "img",
      "aria-label": label
    }, [svgEl("title", null, label)])
    _attachActivation(poly, ctx, "mj-chart-surface-click", {
      row: face.row, col: face.col, x0: x0, x1: x1, y0: y0, y1: y1,
      corners: face.values.slice(), zAvg: face.zAvg
    })
    faceGroup.appendChild(poly)
  }

  /* Axis legs on the floor: x along the front-left edge, y along the
   * front-right edge, z up the left-most corner. */
  const axes = svgEl("g", { "aria-hidden": "true", part: "axes" }, [])
  const axisStroke = "var(--mj-border-strong, #878e9c)"
  const textFill = "var(--mj-text-muted, #5f6673)"

  const leg = (from, to, ticks, toNorm, labelOffset, anchor, title, titleOffset) => {
    axes.appendChild(svgEl("line", {
      x1: from.x, y1: from.y, x2: to.x, y2: to.y, stroke: axisStroke, "stroke-width": 1
    }, []))
    for (let i = 0; i < ticks.length; i = i + 1) {
      const t = toNorm(ticks[i])
      if (_isNumber(t) === false || t < -1e-6 || t > 1 + 1e-6) {
        continue
      }
      const px = from.x + (to.x - from.x) * t
      const py = from.y + (to.y - from.y) * t
      axes.appendChild(svgEl("line", {
        x1: px, y1: py, x2: px + labelOffset.x * 0.35, y2: py + labelOffset.y * 0.35,
        stroke: axisStroke, "stroke-width": 1
      }, []))
      axes.appendChild(svgEl("text", {
        x: px + labelOffset.x, y: py + labelOffset.y + 3,
        "text-anchor": anchor, "font-size": 9, fill: textFill
      }, formatNumber(ticks[i])))
    }
    if (typeof title === "string" && title.length > 0) {
      axes.appendChild(svgEl("text", {
        x: (from.x + to.x) / 2 + titleOffset.x, y: (from.y + to.y) / 2 + titleOffset.y,
        "text-anchor": anchor, "font-size": 10, fill: textFill
      }, title))
    }
    return
  }

  const metaText = (key) => (meta !== null && typeof meta[key] === "string" ? meta[key] : "")

  if (projection === "oblique") {
    leg(project(0, 1, 0), project(1, 1, 0), niceTicks(xMin, xMax, 5), xNorm,
      { x: 0, y: 14 }, "middle", metaText("xLabel"), { x: 0, y: 30 })
    leg(project(1, 1, 0), project(1, 0, 0), niceTicks(yMin, yMax, 4), (v) => 1 - yNorm(v),
      { x: 8, y: 4 }, "start", metaText("yLabel"), { x: 22, y: 14 })
  } else {
    leg(project(0, 1, 0), project(1, 1, 0), niceTicks(xMin, xMax, 5), xNorm,
      { x: -6, y: 12 }, "end", metaText("xLabel"), { x: -22, y: 28 })
    leg(project(1, 1, 0), project(1, 0, 0), niceTicks(yMin, yMax, 4), (v) => 1 - yNorm(v),
      { x: 6, y: 12 }, "start", metaText("yLabel"), { x: 22, y: 28 })
  }
  leg(project(0, 1, 0), project(0, 1, 1), niceTicks(zMin, zMax, 6), zNorm,
    { x: -8, y: 0 }, "end", "", { x: 0, y: 0 })
  const zTop = project(0, 1, 1)
  if (metaText("zLabel").length > 0) {
    axes.appendChild(svgEl("text", {
      x: zTop.x, y: zTop.y - 8, "text-anchor": "middle", "font-size": 10, fill: textFill
    }, metaText("zLabel")))
  }
  root.appendChild(axes)

  /* Height colour bar. */
  if (legendSpace > 0) {
    /* Just right of the drawn box, inside the chart. */
    const boxRight = boxX1 * unit + offsetX
    const barX = Math.min(boxRight + 28, ctx.width - legendSpace + 8)
    const barTop = MARGIN + 6
    const barH = Math.max(Math.min(ctx.height - MARGIN * 2 - 12, 180), 40)
    const steps = 24
    const legend = svgEl("g", { "aria-hidden": "true", part: "legend" }, [])
    for (let i = 0; i < steps; i = i + 1) {
      legend.appendChild(svgEl("rect", {
        x: barX, y: barTop + barH - ((i + 1) / steps) * barH,
        width: 12, height: barH / steps + 0.5,
        fill: _rampColor((i + 0.5) / steps)
      }, []))
    }
    const zScaleBar = linearScale([zMin, zMax], [barTop + barH, barTop])
    const zTicks = niceTicks(zMin, zMax, 6)
    for (let i = 0; i < zTicks.length; i = i + 1) {
      const y = zScaleBar(zTicks[i])
      if (y < barTop - 0.5 || y > barTop + barH + 0.5) {
        continue
      }
      legend.appendChild(svgEl("text", {
        x: barX + 16, y: y + 3, "font-size": 9, fill: textFill
      }, formatNumber(zTicks[i])))
    }
    if (metaText("zLabel").length > 0) {
      legend.appendChild(svgEl("text", {
        x: barX, y: barTop - 6, "font-size": 9, fill: textFill
      }, metaText("zLabel")))
    }
    root.appendChild(legend)
  }

  /* Accessible table: the grid itself, one row per y value. */
  const columns = [`y \\ x`]
  for (let col = 0; col < xVals.length; col = col + 1) {
    columns.push(formatNumber(xVals[col]))
  }
  const rows = []
  for (let row = 0; row < yVals.length; row = row + 1) {
    const record = [formatNumber(yVals[row])]
    for (let col = 0; col < xVals.length; col = col + 1) {
      const z = _cell(zGrid, row, col)
      record.push(z === null ? "" : z)
    }
    rows.push(record)
  }
  ctx.setTable({ columns: columns, rows: rows, caption: "Surface heights z by y (rows) and x (columns)" })
  return root
}


/* ── dispatch ─────────────────────────────────────────────────── */

export function render(ctx) {
  /*
   * Render the surface type.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const root = _renderSurface(ctx)
  return root
}


registerRenderer("surface", render, { legend: "none" })
