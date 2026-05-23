/*
 * phase.js
 *
 * Phase diagram renderer — filled regions + boundary curves.
 *
 * Registered types:
 *   "phase-diagram"  - stability / regime / state diagram with named regions
 *
 * Renderer contract: render(ctx) -> SVGElement  (a <g> within [0..width]x[0..height])
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, formatNumber } from "../svgdraw.js";
import { linearScale, niceTicks } from "../scales.js";


/* ── axes ─────────────────────────────────────────────────────── */

function _drawAxes(plot, plotW, plotH, xScale, yScale, meta) {
  const xTicks = xScale.ticks(6)
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

  const yTicks = yScale.ticks(6)
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
        x: plotW / 2, y: plotH + 32, "text-anchor": "middle",
        "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
      }, escapeHtml(meta.xLabel)))
    }
    if (meta.yLabel) {
      plot.appendChild(svgEl("text", {
        transform: `rotate(-90) translate(${-plotH / 2}, -38)`,
        "text-anchor": "middle",
        "font-size": 11, fill: "var(--mj-text-muted, #6b7280)"
      }, escapeHtml(meta.yLabel)))
    }
  }
  return
}


/* ── domain from regions + boundaries ────────────────────────── */

function _computeDomain(regions, boundaries) {
  let xMin = Infinity; let xMax = -Infinity
  let yMin = Infinity; let yMax = -Infinity

  const processPoint = (xy) => {
    if (xy[0] < xMin) { xMin = xy[0] }
    if (xy[0] > xMax) { xMax = xy[0] }
    if (xy[1] < yMin) { yMin = xy[1] }
    if (xy[1] > yMax) { yMax = xy[1] }
  }

  for (let r = 0; r < regions.length; r = r + 1) {
    const path = regions[r].path
    if (path === null || path === undefined) { continue }
    for (let p = 0; p < path.length; p = p + 1) {
      processPoint(path[p])
    }
  }
  for (let b = 0; b < boundaries.length; b = b + 1) {
    const pts = boundaries[b].points
    if (pts === null || pts === undefined) { continue }
    for (let p = 0; p < pts.length; p = p + 1) {
      processPoint(pts[p])
    }
  }

  if (xMin === Infinity) { xMin = 0; xMax = 1; yMin = 0; yMax = 1 }
  if (xMin === xMax) { xMax = xMin + 1 }
  if (yMin === yMax) { yMax = yMin + 1 }
  return { xMin: xMin, xMax: xMax, yMin: yMin, yMax: yMax }
}


/* ── main renderer ────────────────────────────────────────────── */

export function render(ctx) {
  /*
   * Render a phase diagram with filled regions and boundary curves.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const raw = ctx.raw
  const root = svgEl("g", { part: "plot" }, [])

  if (raw === null || raw === undefined) {
    return root
  }

  const regions = (raw.regions !== null && raw.regions !== undefined) ? raw.regions : []
  const boundaries = (raw.boundaries !== null && raw.boundaries !== undefined)
    ? raw.boundaries : []

  if (regions.length === 0 && boundaries.length === 0) {
    return root
  }

  const margin = { top: 16, right: 16, bottom: 46, left: 58 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  const domain = _computeDomain(regions, boundaries)
  const xPad = (domain.xMax - domain.xMin) * 0.05
  const yPad = (domain.yMax - domain.yMin) * 0.05
  const xScale = linearScale(
    [domain.xMin - xPad, domain.xMax + xPad], [0, plotW]
  )
  const yScale = linearScale(
    [domain.yMin - yPad, domain.yMax + yPad], [plotH, 0]
  )

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  const meta = (raw.meta !== null && raw.meta !== undefined) ? raw.meta : null
  _drawAxes(plot, plotW, plotH, xScale, yScale, meta)

  /* Regions drawn back-to-front (array order) */
  for (let r = 0; r < regions.length; r = r + 1) {
    const region = regions[r]
    const path = region.path
    if (path === null || path === undefined || path.length < 3) {
      continue
    }

    const pts = path.map((xy) => ({
      x: xScale(xy[0]),
      y: yScale(xy[1])
    }))
    const pointsStr = pts.map((p) => p.x.toFixed(1) + "," + p.y.toFixed(1)).join(" ")
    const fillColor = region.color || ctx.colorFor(r)
    const rLabel = escapeHtml(region.name || ("Region " + (r + 1)))

    const poly = svgEl("polygon", {
      points: pointsStr,
      fill: fillColor,
      "fill-opacity": 0.35,
      stroke: fillColor,
      "stroke-width": 0.5,
      part: "region",
      "aria-label": rLabel
    }, [])
    poly.appendChild(svgEl("title", null, rLabel))
    plot.appendChild(poly)

    /* Region label at centroid */
    const cx = pts.reduce((s, p) => s + p.x, 0) / pts.length
    const cy2 = pts.reduce((s, p) => s + p.y, 0) / pts.length
    plot.appendChild(svgEl("text", {
      x: cx.toFixed(1), y: cy2.toFixed(1),
      "text-anchor": "middle", "font-size": 11,
      fill: "var(--mj-text, #14181f)"
    }, escapeHtml(region.name || "")))
  }

  /* Boundary curves */
  for (let b = 0; b < boundaries.length; b = b + 1) {
    const boundary = boundaries[b]
    const pts = boundary.points
    if (pts === null || pts === undefined || pts.length < 2) {
      continue
    }
    const pixPts = pts.map((xy) => ({
      x: xScale(xy[0]),
      y: yScale(xy[1])
    }))
    const style = boundary.style || "solid"
    let strokeDash = "none"
    if (style === "dashed") {
      strokeDash = "6,3"
    } else if (style === "dotted") {
      strokeDash = "2,3"
    }

    let pathData = "M" + pixPts[0].x.toFixed(1) + "," + pixPts[0].y.toFixed(1)
    for (let p = 1; p < pixPts.length; p = p + 1) {
      pathData = pathData + " L" + pixPts[p].x.toFixed(1) + "," + pixPts[p].y.toFixed(1)
    }

    const bLabel = escapeHtml(boundary.name || ("Boundary " + (b + 1)))
    const pathEl = svgEl("path", {
      d: pathData,
      fill: "none",
      stroke: "var(--mj-border-strong, #c7ccd6)",
      "stroke-width": 1.5,
      "stroke-dasharray": strokeDash,
      part: "boundary",
      tabindex: "0",
      role: "img",
      "aria-label": bLabel
    }, [])
    pathEl.appendChild(svgEl("title", null, bLabel))
    const detail = { name: boundary.name }
    const handler = () => { ctx.emit("mj-chart-phase-boundary-click", detail) }
    pathEl.addEventListener("click", handler)
    pathEl.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault()
        handler()
      }
    })
    plot.appendChild(pathEl)
  }

  /* Special points (triple point, critical point) */
  const specialPoints = (raw.specialPoints !== null && raw.specialPoints !== undefined)
    ? raw.specialPoints : []
  for (let sp = 0; sp < specialPoints.length; sp = sp + 1) {
    const pt = specialPoints[sp]
    const px = xScale(pt.x)
    const py = yScale(pt.y)
    const spLabel = escapeHtml(pt.name || "Point")
    const dot = svgEl("circle", {
      cx: px.toFixed(1), cy: py.toFixed(1), r: 5,
      fill: "var(--mj-color-danger, #b91c1c)",
      stroke: "var(--mj-surface, #fff)",
      "stroke-width": 1.5,
      part: "special-point",
      tabindex: "0",
      role: "img",
      "aria-label": spLabel
    }, [])
    dot.appendChild(svgEl("title", null, spLabel))
    const spDetail = { name: pt.name, x: pt.x, y: pt.y }
    const spHandler = () => { ctx.emit("mj-chart-phase-point-click", spDetail) }
    dot.addEventListener("click", spHandler)
    dot.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault()
        spHandler()
      }
    })
    plot.appendChild(dot)
    plot.appendChild(svgEl("text", {
      x: (px + 8).toFixed(1), y: (py - 6).toFixed(1),
      "font-size": 10,
      fill: "var(--mj-text, #14181f)"
    }, escapeHtml(pt.name || "")))
  }

  return root
}


registerRenderer("phase-diagram", render)
