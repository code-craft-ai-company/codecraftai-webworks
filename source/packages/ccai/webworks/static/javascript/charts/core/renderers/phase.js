/*
 * phase.js
 *
 * Phase diagram renderer — filled regions + boundary curves.
 *
 * Registered types:
 *   "phase-diagram" / "phase"  - stability / regime / state diagram with
 *                                named regions
 *
 * Data:
 *   {
 *     meta: { xLabel, yLabel },
 *     xScale: "linear" | "log",  yScale: "linear" | "log",
 *                       (also the `scale-x` / `scale-y` attributes)
 *     regions:       [{ name, color?, path: [[x, y], ...] }],
 *     boundaries:    [{ name, style: "solid"|"dashed"|"dotted",
 *                       curve?: "monotone-x", points: [[x, y], ...] }],
 *     specialPoints: [{ name, x, y }]
 *   }
 *   Regions are drawn back-to-front in array order; a region without a
 *   colour gets its own palette colour and appears in the legend. On a log
 *   axis a coordinate <= 0 is drawn at the axis floor. The axis domain
 *   covers regions, boundaries and special points.
 *
 * Events: mj-chart-phase-region-click { name, index },
 *         mj-chart-phase-boundary-click { name },
 *         mj-chart-phase-point-click { name, x, y }
 *
 * Renderer contract: render(ctx) -> SVGElement  (a <g> within [0..width]x[0..height])
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber, monotonePath } from "../svgdraw.js";
import { linearScale, logScale, positiveExtent } from "../scales.js";


/* ── helpers ──────────────────────────────────────────────────── */

function _isNumber(value) {
  /*
   * True for a finite number.
   */
  const numeric = typeof value === "number" && Number.isFinite(value) === true
  return numeric
}


function _pair(xy) {
  /*
   * An [x, y] pair of finite numbers, or null.
   */
  if (Array.isArray(xy) === true && _isNumber(xy[0]) === true && _isNumber(xy[1]) === true) {
    return [xy[0], xy[1]]
  }
  return null
}


function _pairs(list) {
  /*
   * The valid [x, y] pairs of a list ([] for anything else).
   */
  if (Array.isArray(list) === false) {
    return []
  }
  return list.map(_pair).filter((p) => p !== null)
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


function _tickText(value) {
  /*
   * A tick or range value with up to four significant digits, so small
   * values on a log axis (0.0001) are not rounded to 0.
   */
  const text = formatNumber(value, { maximumSignificantDigits: 4 })
  return text
}


/* ── axes ─────────────────────────────────────────────────────── */

function _drawAxes(plot, plotW, plotH, xScale, yScale, meta) {
  /*
   * Gridlines, tick labels and axis titles (hidden from assistive
   * technology).
   */
  const axes = svgEl("g", { "aria-hidden": "true", part: "axes" }, [])
  const xTicks = xScale.ticks(6)
  for (let i = 0; i < xTicks.length; i = i + 1) {
    const px = xScale(xTicks[i])
    axes.appendChild(svgEl("line", {
      x1: px, y1: 0, x2: px, y2: plotH,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    axes.appendChild(svgEl("text", {
      x: px, y: plotH + 14, "text-anchor": "middle",
      "font-size": 10, fill: "var(--mj-text-muted, #6b7280)"
    }, _tickText(xTicks[i])))
  }

  const yTicks = yScale.ticks(6)
  for (let i = 0; i < yTicks.length; i = i + 1) {
    const py = yScale(yTicks[i])
    axes.appendChild(svgEl("line", {
      x1: 0, y1: py, x2: plotW, y2: py,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    axes.appendChild(svgEl("text", {
      x: -6, y: py + 4, "text-anchor": "end",
      "font-size": 10, fill: "var(--mj-text-muted, #6b7280)"
    }, _tickText(yTicks[i])))
  }

  if (typeof meta.xLabel === "string" && meta.xLabel.length > 0) {
    axes.appendChild(svgEl("text", {
      x: plotW / 2, y: plotH + 32, "text-anchor": "middle",
      "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
    }, meta.xLabel))
  }
  if (typeof meta.yLabel === "string" && meta.yLabel.length > 0) {
    axes.appendChild(svgEl("text", {
      transform: `rotate(-90) translate(${-plotH / 2}, -46)`,
      "text-anchor": "middle",
      "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
    }, meta.yLabel))
  }
  plot.appendChild(axes)
  return
}


/* ── scales ───────────────────────────────────────────────────── */

function _axisScale(values, kind, range) {
  /*
   * A linear (padded 5%) or log scale over the values.
   */
  let scale = null
  if (kind === "log") {
    const ext = positiveExtent(values)
    scale = logScale(ext, range)
  } else {
    let min = Infinity
    let max = -Infinity
    for (let i = 0; i < values.length; i = i + 1) {
      min = Math.min(min, values[i])
      max = Math.max(max, values[i])
    }
    if (min === Infinity) {
      min = 0
      max = 1
    }
    const pad = (max - min) * 0.05
    scale = linearScale([min - pad, max + pad], range)
  }
  return scale
}


/* ── label placement ──────────────────────────────────────────── */

function _interiorPoint(pts) {
  /*
   * A point well inside a polygon (pixel coordinates): scan several
   * horizontal lines and take the middle of the widest inside interval.
   * Returns { x, y, width } or null.
   */
  let top = Infinity
  let bottom = -Infinity
  for (let i = 0; i < pts.length; i = i + 1) {
    top = Math.min(top, pts[i].y)
    bottom = Math.max(bottom, pts[i].y)
  }
  if (bottom - top < 1) {
    return null
  }
  let best = null
  const lines = 15
  for (let k = 1; k <= lines; k = k + 1) {
    const y = top + ((bottom - top) * k) / (lines + 1)
    const crossings = []
    for (let i = 0; i < pts.length; i = i + 1) {
      const p = pts[i]
      const q = pts[(i + 1) % pts.length]
      if ((p.y <= y && q.y > y) || (q.y <= y && p.y > y)) {
        crossings.push(p.x + ((y - p.y) / (q.y - p.y)) * (q.x - p.x))
      }
    }
    crossings.sort((a, b) => a - b)
    for (let c = 0; c + 1 < crossings.length; c = c + 2) {
      const width = crossings[c + 1] - crossings[c]
      /* Prefer wide intervals and, among them, the middle rows. */
      const weight = width * (1 - Math.abs(k - (lines + 1) / 2) / (lines + 1))
      if (best === null || weight > best.weight) {
        best = { x: (crossings[c] + crossings[c + 1]) / 2, y: y, width: width, weight: weight }
      }
    }
  }
  return best
}


/* ── main renderer ────────────────────────────────────────────── */

export function render(ctx) {
  /*
   * Render a phase diagram with filled regions and boundary curves.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const raw = ctx.raw !== null && ctx.raw !== undefined ? ctx.raw : {}
  const root = svgEl("g", { part: "plot" }, [])
  const meta = ctx.model.meta

  const regions = Array.isArray(raw.regions) === true
    ? raw.regions.filter((r) => r !== null && typeof r === "object") : []
  const boundaries = Array.isArray(raw.boundaries) === true
    ? raw.boundaries.filter((b) => b !== null && typeof b === "object") : []
  const specialPoints = Array.isArray(raw.specialPoints) === true
    ? raw.specialPoints.filter((p) => p !== null && typeof p === "object" &&
      _isNumber(p.x) === true && _isNumber(p.y) === true) : []

  if (regions.length === 0 && boundaries.length === 0 && specialPoints.length === 0) {
    return root
  }

  const margin = { top: 16, right: 16, bottom: 46, left: 62 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  /* Domain over every coordinate the chart draws. */
  const xs = []
  const ys = []
  const collect = (pair) => {
    xs.push(pair[0])
    ys.push(pair[1])
  }
  regions.forEach((r) => _pairs(r.path).forEach(collect))
  boundaries.forEach((b) => _pairs(b.points).forEach(collect))
  specialPoints.forEach((p) => collect([p.x, p.y]))

  const xKind = ctx.attrs("scale-x", raw.xScale === "log" ? "log" : "linear")
  const yKind = ctx.attrs("scale-y", raw.yScale === "log" ? "log" : "linear")
  const xScale = _axisScale(xs, xKind, [0, plotW])
  const yScale = _axisScale(ys, yKind, [plotH, 0])
  const toPx = (pair) => ({ x: xScale(pair[0]), y: yScale(pair[1]) })

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)
  _drawAxes(plot, plotW, plotH, xScale, yScale, meta)

  const tableRows = []
  const legend = []
  const rangeText = (values) => {
    if (values.length === 0) {
      return ""
    }
    return `${_tickText(Math.min(...values))} – ${_tickText(Math.max(...values))}`
  }

  /* Regions drawn back-to-front (array order) */
  const regionGroup = svgEl("g", { part: "regions" }, [])
  const regionLabels = svgEl("g", { "aria-hidden": "true", part: "region-labels" }, [])
  for (let r = 0; r < regions.length; r = r + 1) {
    const region = regions[r]
    const path = _pairs(region.path)
    if (path.length < 3) {
      continue
    }
    const pts = path.map(toPx)
    const name = typeof region.name === "string" && region.name.length > 0 ? region.name : `Region ${r + 1}`
    const fillColor = typeof region.color === "string" && region.color.length > 0
      ? region.color : ctx.colorFor(r)

    const poly = svgEl("polygon", {
      points: pts.map((p) => p.x.toFixed(1) + "," + p.y.toFixed(1)).join(" "),
      fill: fillColor,
      "fill-opacity": 0.35,
      stroke: fillColor,
      "stroke-width": 0.5,
      part: "region",
      tabindex: "0",
      role: "img",
      "aria-label": `Region ${name}`
    }, [svgEl("title", null, name)])
    _attachActivation(poly, ctx, "mj-chart-phase-region-click", { name: name, index: r })
    regionGroup.appendChild(poly)
    legend.push({ label: name, color: fillColor })
    tableRows.push(["Region", name, rangeText(path.map((p) => p[0])), rangeText(path.map((p) => p[1]))])

    /* Region name at an interior point, when it fits. */
    const spot = _interiorPoint(pts)
    if (spot !== null && spot.width > Math.min(name.length * 6, 40)) {
      regionLabels.appendChild(svgEl("text", {
        x: spot.x.toFixed(1), y: (spot.y + 4).toFixed(1),
        "text-anchor": "middle", "font-size": 11,
        fill: "var(--mj-text, #14181f)"
      }, name))
    }
  }
  plot.appendChild(regionGroup)

  /* Boundary curves */
  const boundaryGroup = svgEl("g", { part: "boundaries" }, [])
  for (let b = 0; b < boundaries.length; b = b + 1) {
    const boundary = boundaries[b]
    const points = _pairs(boundary.points)
    if (points.length < 2) {
      continue
    }
    const pixPts = points.map(toPx)
    let strokeDash = null
    if (boundary.style === "dashed") {
      strokeDash = "6,3"
    } else if (boundary.style === "dotted") {
      strokeDash = "2,3"
    }

    let pathData = ""
    if (boundary.curve === "monotone-x" && pixPts.length > 2) {
      const sorted = pixPts.slice().sort((p, q) => p.x - q.x)
      pathData = monotonePath(sorted)
    } else {
      pathData = pixPts.map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ")
    }

    const name = typeof boundary.name === "string" && boundary.name.length > 0
      ? boundary.name : `Boundary ${b + 1}`
    const pathEl = svgEl("path", {
      d: pathData,
      fill: "none",
      stroke: "var(--mj-text-muted, #5f6673)",
      "stroke-width": 1.75,
      "stroke-dasharray": strokeDash,
      part: "boundary",
      tabindex: "0",
      role: "img",
      "aria-label": name
    }, [svgEl("title", null, name)])
    _attachActivation(pathEl, ctx, "mj-chart-phase-boundary-click", { name: boundary.name })
    boundaryGroup.appendChild(pathEl)
    tableRows.push(["Boundary", name, rangeText(points.map((p) => p[0])), rangeText(points.map((p) => p[1]))])
  }
  plot.appendChild(boundaryGroup)
  plot.appendChild(regionLabels)

  /* Special points (triple point, critical point) */
  const pointGroup = svgEl("g", { part: "special-points" }, [])
  for (let sp = 0; sp < specialPoints.length; sp = sp + 1) {
    const pt = specialPoints[sp]
    const px = xScale(pt.x)
    const py = yScale(pt.y)
    const name = typeof pt.name === "string" && pt.name.length > 0 ? pt.name : "Point"
    const label = `${name} (${formatNumber(pt.x)}, ${formatNumber(pt.y)})`
    const dot = svgEl("circle", {
      cx: px.toFixed(1), cy: py.toFixed(1), r: 5,
      fill: "var(--mj-text, #14181f)",
      stroke: "var(--mj-surface, #fff)",
      "stroke-width": 1.5,
      part: "special-point",
      tabindex: "0",
      role: "img",
      "aria-label": label
    }, [svgEl("title", null, label)])
    _attachActivation(dot, ctx, "mj-chart-phase-point-click", { name: pt.name, x: pt.x, y: pt.y })
    pointGroup.appendChild(dot)
    /* Label to the left when the point is in the right part of the plot. */
    const onRight = px > plotW * 0.7
    pointGroup.appendChild(svgEl("text", {
      x: (px + (onRight === true ? -8 : 8)).toFixed(1), y: (py - 6).toFixed(1),
      "text-anchor": onRight === true ? "end" : "start",
      "font-size": 10,
      fill: "var(--mj-text, #14181f)",
      stroke: "var(--mj-surface, #ffffff)",
      "stroke-width": 3,
      "paint-order": "stroke",
      "aria-hidden": "true"
    }, name))
    tableRows.push(["Point", name, pt.x, pt.y])
  }
  plot.appendChild(pointGroup)

  ctx.setLegend(legend)
  ctx.setTable({
    columns: ["Kind", "Name", typeof meta.xLabel === "string" ? meta.xLabel : "x",
      typeof meta.yLabel === "string" ? meta.yLabel : "y"],
    rows: tableRows
  })
  return root
}


registerRenderer("phase-diagram", render)
registerRenderer("phase", render)
