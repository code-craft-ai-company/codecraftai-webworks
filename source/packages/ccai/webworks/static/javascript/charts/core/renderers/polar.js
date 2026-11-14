/*
 * polar.js
 *
 * Radial bar / area chart family renderer.
 *
 * Registered types (dispatched on ctx.type):
 *   "polar"        - continuous polar line/area chart (angle + radius)
 *   "wind-rose"    - directional frequency chart with stacked wedge petals
 *                    (petal LENGTH encodes the stacked value)
 *   "nightingale"  - polar area (coxcomb) chart, sector AREA encodes value
 *   "coxcomb"      - alias for nightingale
 *
 * Data:
 *   polar        { series: [{ name, points: [{theta, r}, ...] }],
 *                  thetaUnit: "degrees" | "radians", rMin?, rMax?, fill? }
 *                Line mode (default) is an open path; it closes only when the
 *                points span a full turn. Area mode (`fill: true` in the data
 *                or the `fill="true"` attribute) is a closed filled region.
 *                Without rMin the radial axis starts at min(0, data minimum);
 *                values below rMin are drawn at the centre.
 *   wind-rose    { directions: ["N", ...], series: [{ name, values: [...] }] }
 *   nightingale  { categories: [...], series: [{ name, values: [...] }] }
 *
 * Null or non-numeric values are gaps (a broken line / no wedge), never zero.
 *
 * Renderer contract: render(ctx) -> SVGElement  (a <g> within [0..width]x[0..height])
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber, arcPath, polarPoint } from "../svgdraw.js";
import { linearScale, sqrtScale, niceTicks } from "../scales.js";
import { booleanOption } from "../chartoptions.js";

const FULL_TURN = Math.PI * 2;

/* Space kept around the rings for the angular labels. */
const RING_MARGIN = 34;


/* ── helpers ──────────────────────────────────────────────────── */

function _isNumber(value) {
  /*
   * True for a finite number.
   */
  const numeric = typeof value === "number" && Number.isFinite(value) === true
  return numeric
}


function _toRadians(theta, unit) {
  /*
   * Convert theta to radians.  unit is "degrees" (default) or "radians".
   */
  const radians = unit === "radians" ? theta : theta * (Math.PI / 180)
  return radians
}


function _decorGroup() {
  /*
   * A group for grid lines and tick labels, hidden from assistive
   * technology so a screen reader reads the marks, not every tick.
   */
  const group = svgEl("g", { "aria-hidden": "true", part: "grid" }, [])
  return group
}


function _drawRings(group, cx, cy, ringRadii) {
  /*
   * Draw concentric grid rings at the given pixel radii.
   */
  for (let i = 0; i < ringRadii.length; i = i + 1) {
    const r = ringRadii[i]
    if (_isNumber(r) === false || r <= 0.5) {
      continue
    }
    group.appendChild(svgEl("circle", {
      cx: cx, cy: cy, r: r,
      fill: "none",
      stroke: "var(--mj-border, #e0e3e9)",
      "stroke-width": 1
    }, []))
  }
  return
}


function _drawSpokes(group, cx, cy, maxR, angles) {
  /*
   * Draw spoke gridlines from the centre at the given angles (radians,
   * 0 = up, clockwise).
   */
  for (let s = 0; s < angles.length; s = s + 1) {
    const end = polarPoint(cx, cy, maxR, angles[s])
    group.appendChild(svgEl("line", {
      x1: cx, y1: cy, x2: end.x, y2: end.y,
      stroke: "var(--mj-border, #e0e3e9)",
      "stroke-width": 1
    }, []))
  }
  return
}


function _drawRadialLabels(group, cx, cy, labelAngle, rScale, rTicks) {
  /*
   * Draw radial (r-axis) tick labels along one spoke. Only a tick that
   * sits at the centre (pixel radius 0) is left out, so negative and dB
   * scales are labelled too. The labels get a surface-coloured halo so
   * they stay readable where they cross a mark.
   */
  for (let i = 0; i < rTicks.length; i = i + 1) {
    const tick = rTicks[i]
    const rPx = rScale(tick)
    if (_isNumber(rPx) === false || rPx < 1) {
      continue
    }
    const pos = polarPoint(cx, cy, rPx, labelAngle)
    group.appendChild(svgEl("text", {
      x: pos.x + 3, y: pos.y - 2,
      "font-size": 9,
      fill: "var(--mj-text-muted, #6b7280)",
      stroke: "var(--mj-surface, #ffffff)",
      "stroke-width": 3,
      "stroke-linejoin": "round",
      "paint-order": "stroke"
    }, formatNumber(tick)))
  }
  return
}


function _angleLabel(index, count, unit) {
  /*
   * Text of an angular label at position index of count equal steps:
   * degrees ("45°") or multiples of π for radians ("π/4").
   */
  if (unit !== "radians") {
    const degrees = Math.round((index / count) * 3600) / 10
    return `${formatNumber(degrees)}°`
  }

  /* Reduce index * 2 / count to a fraction of π. */
  let numerator = index * 2
  let denominator = count
  const gcd = (a, b) => (b === 0 ? a : gcd(b, a % b))
  const divisor = numerator === 0 ? denominator : gcd(numerator, denominator)
  numerator = numerator / divisor
  denominator = denominator / divisor

  let text = "0"
  if (index !== 0) {
    const head = numerator === 1 ? "π" : `${numerator}π`
    text = denominator === 1 ? head : `${head}/${denominator}`
  }
  return text
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


function _layout(ctx) {
  /*
   * Centre and outer radius of the polar plot.
   */
  const cx = ctx.width / 2
  const cy = ctx.height / 2
  const maxR = Math.max(Math.min(cx, cy) - RING_MARGIN, 8)
  const layout = { cx: cx, cy: cy, maxR: maxR }
  return layout
}


/* ── polar (line / area) ───────────────────────────────────────── */

function _polarPointsOf(series) {
  /*
   * The point list of a normalized series ([] when it has none).
   */
  const points = Array.isArray(series.points) === true ? series.points : []
  return points
}


function _spansFullTurn(points, thetaUnit) {
  /*
   * True when the drawable points of a series cover a full turn, so the
   * line may close back onto its first point.
   */
  let min = Infinity
  let max = -Infinity
  let count = 0
  for (let p = 0; p < points.length; p = p + 1) {
    const point = points[p]
    if (point === null || point === undefined || _isNumber(point.theta) === false ||
        _isNumber(point.r) === false) {
      continue
    }
    const angle = _toRadians(point.theta, thetaUnit)
    min = Math.min(min, angle)
    max = Math.max(max, angle)
    count = count + 1
  }
  if (count < 3) {
    return false
  }
  /* The gap between the last and the first point is at most one average step. */
  const step = (max - min) / (count - 1)
  const spans = max - min + step >= FULL_TURN - 1e-6
  return spans
}


function _renderPolar(ctx) {
  /*
   * Render a polar line or area chart.
   */
  const raw = ctx.raw
  const root = svgEl("g", { part: "plot" }, [])
  const series = ctx.model.series

  const thetaUnit = raw.thetaUnit === "radians" ? "radians" : "degrees"
  const fillArea = booleanOption(ctx, "fill", raw.fill === true)

  /* Radial domain: [min(0, data min), data max] unless given. */
  let dataMin = Infinity
  let dataMax = -Infinity
  for (let s = 0; s < series.length; s = s + 1) {
    const pts = _polarPointsOf(series[s])
    for (let p = 0; p < pts.length; p = p + 1) {
      const r = pts[p] !== null && pts[p] !== undefined ? pts[p].r : null
      if (_isNumber(r) === true) {
        dataMin = Math.min(dataMin, r)
        dataMax = Math.max(dataMax, r)
      }
    }
  }
  if (dataMin === Infinity) {
    dataMin = 0
    dataMax = 1
  }
  const rMin = _isNumber(raw.rMin) === true ? raw.rMin : Math.min(0, dataMin)
  let rMax = _isNumber(raw.rMax) === true ? raw.rMax : Math.max(dataMax, rMin)
  if (rMax <= rMin) {
    rMax = rMin + 1
  }

  const { cx, cy, maxR } = _layout(ctx)
  const rTicks = niceTicks(rMin, rMax, 4).filter((t) => t >= rMin && t <= rMax)
  const rScale = linearScale([rMin, rMax], [0, maxR])
  /* Values below the axis start are drawn at the centre, never mirrored. */
  const radiusOf = (r) => Math.min(Math.max(rScale(r), 0), maxR * 1.25)

  const grid = _decorGroup()
  _drawRings(grid, cx, cy, rTicks.map((t) => rScale(t)).concat([maxR]))
  const spokeAngles = []
  for (let s = 0; s < 8; s = s + 1) {
    spokeAngles.push((s / 8) * FULL_TURN)
  }
  _drawSpokes(grid, cx, cy, maxR, spokeAngles)

  /* Angular labels around the perimeter, in the data's unit. */
  const labelR = maxR + 14
  for (let i = 0; i < 8; i = i + 1) {
    const angle = (i / 8) * FULL_TURN
    const pos = polarPoint(cx, cy, labelR, angle)
    grid.appendChild(svgEl("text", {
      x: pos.x, y: pos.y + 4,
      "text-anchor": "middle",
      "font-size": 10,
      fill: "var(--mj-text-muted, #6b7280)"
    }, _angleLabel(i, 8, thetaUnit)))
  }
  root.appendChild(grid)

  const tableRows = []

  for (let s = 0; s < series.length; s = s + 1) {
    const ser = series[s]
    const pts = _polarPointsOf(ser)
    if (pts.length === 0) {
      continue
    }
    const color = ctx.colorFor(ser.name)
    const group = svgEl("g", { part: "series", "data-series": ser.name }, [])

    /* Pixel points; a null / non-numeric point is a gap. */
    const pixPts = []
    for (let p = 0; p < pts.length; p = p + 1) {
      const pt = pts[p]
      if (pt === null || pt === undefined || _isNumber(pt.theta) === false ||
          _isNumber(pt.r) === false) {
        pixPts.push(null)
        continue
      }
      const theta = _toRadians(pt.theta, thetaUnit)
      pixPts.push(polarPoint(cx, cy, radiusOf(pt.r), theta))
    }

    const closed = fillArea === true || _spansFullTurn(pts, thetaUnit) === true
    let pathData = ""
    let pen = false
    let firstOfRun = null
    let runs = 0
    for (let p = 0; p < pixPts.length; p = p + 1) {
      const px = pixPts[p]
      if (px === null) {
        pen = false
        continue
      }
      pathData = pathData + `${pen === true ? "L" : "M"}${px.x.toFixed(2)},${px.y.toFixed(2)} `
      if (pen === false) {
        runs = runs + 1
        if (firstOfRun === null) {
          firstOfRun = px
        }
      }
      pen = true
    }
    /* Close the loop (only a gap-free closed series joins its ends). */
    if (closed === true && runs === 1 && firstOfRun !== null) {
      pathData = pathData + "Z"
    }

    if (pathData.length > 0) {
      if (fillArea === true) {
        group.appendChild(svgEl("path", {
          d: pathData.trim(),
          fill: color,
          "fill-opacity": 0.2,
          stroke: color,
          "stroke-width": 1.5,
          "stroke-linejoin": "round"
        }, []))
      } else {
        group.appendChild(svgEl("path", {
          d: pathData.trim(),
          fill: "none",
          stroke: color,
          "stroke-width": 2,
          "stroke-linejoin": "round"
        }, []))
      }
    }

    /* Interactive marks per data point */
    for (let p = 0; p < pts.length; p = p + 1) {
      const pt = pts[p]
      const px = pixPts[p]
      if (px === null) {
        continue
      }
      const thetaText = thetaUnit === "radians"
        ? `${formatNumber(pt.theta, { maximumFractionDigits: 3 })} rad`
        : `${formatNumber(pt.theta)}°`
      const label = `${ser.name}: θ ${thetaText}, r ${formatNumber(pt.r)}`
      const dot = svgEl("circle", {
        cx: px.x, cy: px.y, r: 4,
        fill: color,
        stroke: "var(--mj-surface, #fff)",
        "stroke-width": 1,
        part: "point",
        tabindex: "0",
        role: "img",
        "aria-label": label
      }, [svgEl("title", null, label)])
      _attachActivation(dot, ctx, "mj-chart-polar-click", { series: ser.name, theta: pt.theta, r: pt.r })
      group.appendChild(dot)
      tableRows.push([ser.name, pt.theta, pt.r])
    }
    root.appendChild(group)
  }

  /* Radial labels last, on the 22.5° bisector, so they stay on top. */
  const labels = _decorGroup()
  _drawRadialLabels(labels, cx, cy, Math.PI / 8, rScale, rTicks)
  root.appendChild(labels)

  ctx.setTable({
    columns: ["Series", thetaUnit === "radians" ? "θ (rad)" : "θ (°)", "r"],
    rows: tableRows
  })
  return root
}


/* ── shared sector layout (wind-rose, nightingale) ─────────────── */

function _sectorValue(series, index) {
  /*
   * The value of a series at a sector, or null when it is missing.
   */
  const values = Array.isArray(series.values) === true ? series.values : []
  const value = values[index]
  return _isNumber(value) === true ? value : null
}


function _renderSectors(ctx, options) {
  /*
   * Render stacked wedges, one sector per label.
   *
   * :param options: { labels, centred, areaEncoded, part, eventName,
   *     labelKey } -- `centred` puts the sector centre on its angle
   *     (wind-rose, north up); otherwise the sector starts there.
   */
  const root = svgEl("g", { part: "plot" }, [])
  const labels = options.labels
  const series = ctx.model.series

  if (labels.length === 0 || series.length === 0) {
    return root
  }

  const { cx, cy, maxR } = _layout(ctx)
  const count = labels.length
  const angleStep = FULL_TURN / count
  const offset = options.centred === true ? -angleStep / 2 : 0

  /* Largest stacked (positive) total. */
  let vMax = 0
  for (let c = 0; c < count; c = c + 1) {
    let stack = 0
    for (let s = 0; s < series.length; s = s + 1) {
      const v = _sectorValue(series[s], c)
      if (v !== null && v > 0) {
        stack = stack + v
      }
    }
    vMax = Math.max(vMax, stack)
  }
  if (vMax <= 0) {
    vMax = 1
  }

  const rTicks = niceTicks(0, vMax, 4).filter((t) => t > 0 && t <= vMax * 1.0001)
  const rScale = options.areaEncoded === true
    ? sqrtScale([0, vMax], [0, maxR])
    : linearScale([0, vMax], [0, maxR])

  const grid = _decorGroup()
  _drawRings(grid, cx, cy, rTicks.map((t) => rScale(t)).concat([maxR]))
  const spokes = []
  for (let c = 0; c < count && count > 1; c = c + 1) {
    spokes.push(offset + c * angleStep)
  }
  _drawSpokes(grid, cx, cy, maxR, spokes)
  root.appendChild(grid)

  const tableRows = []
  const wedges = svgEl("g", { part: "sectors" }, [])

  for (let c = 0; c < count; c = c + 1) {
    const startAngle = offset + c * angleStep
    const endAngle = startAngle + angleStep
    const row = [String(labels[c])]

    let stackBase = 0
    for (let s = 0; s < series.length; s = s + 1) {
      const value = _sectorValue(series[s], c)
      row.push(value === null ? "" : value)
      if (value === null || value <= 0) {
        continue
      }
      const innerR = rScale(stackBase)
      const outerR = rScale(stackBase + value)
      const color = ctx.colorFor(series[s].name)
      const label = `${labels[c]}, ${series[s].name}: ${formatNumber(value)}`
      const wedge = svgEl("path", {
        d: arcPath(cx, cy, innerR, outerR, startAngle, endAngle),
        fill: color,
        "fill-opacity": 0.85,
        stroke: "var(--mj-surface, #fff)",
        "stroke-width": 0.5,
        part: options.part,
        tabindex: "0",
        role: "img",
        "aria-label": label
      }, [svgEl("title", null, label)])
      const detail = { series: series[s].name, value: value }
      detail[options.labelKey] = labels[c]
      _attachActivation(wedge, ctx, options.eventName, detail)
      wedges.appendChild(wedge)
      stackBase = stackBase + value
    }
    tableRows.push(row)
  }
  root.appendChild(wedges)

  /* Sector labels and radial tick labels on top of the wedges. */
  const top = _decorGroup()
  for (let c = 0; c < count; c = c + 1) {
    const midAngle = offset + c * angleStep + angleStep / 2
    const pos = polarPoint(cx, cy, maxR + 14, midAngle)
    top.appendChild(svgEl("text", {
      x: pos.x, y: pos.y + 4,
      "text-anchor": "middle",
      "font-size": 10,
      fill: "var(--mj-text, #14181f)"
    }, String(labels[c])))
  }
  /*
   * Radial labels along the sector boundary nearest north (so they stack
   * vertically), or the 22.5° bisector for one sector. Ticks closer than
   * 11px to the previous label (sqrt scales crowd at the rim) are skipped.
   */
  const labelAngle = count > 1 ? offset + angleStep * Math.round(-offset / angleStep) : Math.PI / 8
  let lastPx = -Infinity
  const spaced = rTicks.filter((tick) => {
    const px = rScale(tick)
    const keep = px - lastPx >= 11
    if (keep === true) {
      lastPx = px
    }
    return keep
  })
  _drawRadialLabels(top, cx, cy, labelAngle, rScale, spaced)
  root.appendChild(top)

  const columns = [options.labelHeader]
  for (let s = 0; s < series.length; s = s + 1) {
    columns.push(series[s].name)
  }
  ctx.setTable({ columns: columns, rows: tableRows })
  return root
}


/* ── wind-rose ────────────────────────────────────────────────── */

function _renderWindRose(ctx) {
  /*
   * Render a directional wind-rose chart with stacked wedge petals. Index
   * 0 is north (up); petals are centred on their direction.
   */
  const directions = Array.isArray(ctx.raw.directions) === true ? ctx.raw.directions : []
  const root = _renderSectors(ctx, {
    labels: directions,
    centred: true,
    areaEncoded: false,
    part: "petal",
    eventName: "mj-chart-windrose-click",
    labelKey: "direction",
    labelHeader: "Direction"
  })
  return root
}


/* ── nightingale / coxcomb ────────────────────────────────────── */

function _renderNightingale(ctx) {
  /*
   * Render a Nightingale rose (polar area / coxcomb) chart. Area encodes
   * value via a sqrt scale.
   */
  const root = _renderSectors(ctx, {
    labels: ctx.model.categories,
    centred: false,
    areaEncoded: true,
    part: "sector",
    eventName: "mj-chart-nightingale-click",
    labelKey: "category",
    labelHeader: "Category"
  })
  return root
}


/* ── dispatch ─────────────────────────────────────────────────── */

export function render(ctx) {
  /*
   * Dispatch to the polar-family sub-renderer of ctx.type.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const chartType = typeof ctx.type === "string" ? ctx.type : ctx.attrs("type", "polar")

  let root = null
  if (chartType === "wind-rose") {
    root = _renderWindRose(ctx)
  } else if (chartType === "nightingale" || chartType === "coxcomb") {
    root = _renderNightingale(ctx)
  } else {
    root = _renderPolar(ctx)
  }
  return root
}


registerRenderer("polar", render)
registerRenderer("wind-rose", render)
registerRenderer("nightingale", render)
registerRenderer("coxcomb", render)
