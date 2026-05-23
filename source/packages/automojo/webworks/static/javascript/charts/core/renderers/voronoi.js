/*
 * voronoi.js
 *
 * Voronoi diagram renderer — partitions the 2-D plot surface into
 * nearest-neighbour regions around seed points.  Uses a simple
 * half-plane intersection (Fortune's algorithm approximation via
 * iterative half-plane clipping) implemented without external libraries.
 *
 * Registered types:
 *   "voronoi"
 *
 * ctx.raw shape:
 *   raw.series  [{name, points:[{x, y, label?}]}]
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, formatNumber } from "../svgdraw.js";
import { linearScale, niceTicks } from "../scales.js";
import { extent } from "../svgdraw.js";


/* ── half-plane polygon clipping (Sutherland-Hodgman on line bisectors) ─ */

function _dot(a, b) {
  return a.x * b.x + a.y * b.y
}

function _clipPolygonByHalfPlane(polygon, px1, py1, px2, py2) {
  /*
   * Clip `polygon` (array of {x,y}) against the half-plane to the left
   * of the directed line from (px1,py1) to (px2,py2).
   * Uses Sutherland-Hodgman.
   *
   * :returns: Clipped polygon array.
   */
  if (polygon.length === 0) {
    return polygon
  }

  const normal = { x: -(py2 - py1), y: px2 - px1 }
  const ref    = { x: px1, y: py1 }

  const inside = (p) => {
    const d = (p.x - ref.x) * normal.x + (p.y - ref.y) * normal.y
    return d >= 0
  }

  const intersect = (a, b) => {
    const da = (a.x - ref.x) * normal.x + (a.y - ref.y) * normal.y
    const db = (b.x - ref.x) * normal.x + (b.y - ref.y) * normal.y
    const t  = da / (da - db)
    return { x: a.x + t * (b.x - a.x), y: a.y + t * (b.y - a.y) }
  }

  const output = []
  for (let i = 0; i < polygon.length; i = i + 1) {
    const curr = polygon[i]
    const prev = polygon[(i + polygon.length - 1) % polygon.length]

    const currIn = inside(curr)
    const prevIn = inside(prev)

    if (currIn === true) {
      if (prevIn === false) {
        output.push(intersect(prev, curr))
      }
      output.push(curr)
    } else if (prevIn === true) {
      output.push(intersect(prev, curr))
    }
  }

  return output
}


function _voronoiCells(points, w, h) {
  /*
   * Compute Voronoi cells for a set of 2-D points within a [0,w]×[0,h]
   * bounding box via iterative half-plane clipping.
   *
   * For each seed point, the cell is the intersection of half-planes
   * defined by the perpendicular bisectors to every other seed point.
   *
   * :param points: Array of {x, y}.
   * :param w:      Plot width.
   * :param h:      Plot height.
   * :returns: Array of polygons (arrays of {x,y}), one per input point.
   */
  const boundingBox = [
    { x: 0, y: 0 }, { x: w, y: 0 }, { x: w, y: h }, { x: 0, y: h }
  ]

  const cells = []

  for (let i = 0; i < points.length; i = i + 1) {
    const si = points[i]
    let cell = boundingBox.slice()

    for (let j = 0; j < points.length; j = j + 1) {
      if (j === i) {
        continue
      }
      const sj = points[j]

      /* Perpendicular bisector of si and sj:
       * mid-point M, normal direction (sj - si).
       * Half-plane: all p where (p - M)·(sj - si) ≤ 0  (closer to si).
       * Expressed as directed line: from mid point perpendicular.
       */
      const mx = (si.x + sj.x) / 2
      const my = (si.y + sj.y) / 2
      const dx = sj.x - si.x
      const dy = sj.y - si.y

      /* Directed line: p1 = M + perp, p2 = M - perp (so left side = si side) */
      const px1 = mx + dy
      const py1 = my - dx
      const px2 = mx - dy
      const py2 = my + dx

      cell = _clipPolygonByHalfPlane(cell, px1, py1, px2, py2)
      if (cell.length === 0) {
        break
      }
    }

    cells.push(cell)
  }

  return cells
}


function _polygonPath(polygon) {
  /*
   * Convert a polygon (array of {x,y}) to an SVG path `d` string.
   */
  if (polygon.length === 0) {
    return ""
  }
  let d = `M${polygon[0].x.toFixed(2)},${polygon[0].y.toFixed(2)}`
  for (let i = 1; i < polygon.length; i = i + 1) {
    d = d + ` L${polygon[i].x.toFixed(2)},${polygon[i].y.toFixed(2)}`
  }
  d = d + " Z"
  return d
}


/* ── renderer ─────────────────────────────────────────────────────────── */

export function render(ctx) {
  /*
   * Render a Voronoi diagram.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const raw  = ctx.raw
  const root = svgEl("g", { part: "plot" }, [])

  const series = (raw !== null && raw !== undefined && Array.isArray(raw.series))
    ? raw.series
    : []

  if (series.length === 0) {
    return root
  }

  const mode   = ctx.attrs("mode", "filled")
  const margin = { top: 16, right: 16, bottom: 40, left: 52 }
  const plotW  = Math.max(ctx.width  - margin.left - margin.right,  10)
  const plotH  = Math.max(ctx.height - margin.top  - margin.bottom, 10)

  /* Collect all points and compute data-space extents */
  const allXValues = []
  const allYValues = []
  for (let s = 0; s < series.length; s = s + 1) {
    const pts = series[s].points || []
    for (let p = 0; p < pts.length; p = p + 1) {
      if (typeof pts[p].x === "number") {
        allXValues.push(pts[p].x)
      }
      if (typeof pts[p].y === "number") {
        allYValues.push(pts[p].y)
      }
    }
  }

  if (allXValues.length === 0) {
    return root
  }

  const xExt  = extent(allXValues)
  const yExt  = extent(allYValues)
  const xScale = linearScale(xExt, [0, plotW])
  const yScale = linearScale(yExt, [plotH, 0])

  const plot = svgEl("g", {
    transform: `translate(${margin.left},${margin.top})`
  }, [])
  root.appendChild(plot)

  /* Axes */
  const xTicks = niceTicks(xExt[0], xExt[1], 5)
  for (let t = 0; t < xTicks.length; t = t + 1) {
    const px = xScale(xTicks[t])
    plot.appendChild(svgEl("line", {
      x1: px, y1: 0, x2: px, y2: plotH,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    plot.appendChild(svgEl("text", {
      x: px, y: plotH + 14,
      "text-anchor": "middle",
      "font-size": 11,
      fill: "var(--mj-text-muted, #6b7280)"
    }, formatNumber(xTicks[t])))
  }

  const yTicks = niceTicks(yExt[0], yExt[1], 5)
  for (let t = 0; t < yTicks.length; t = t + 1) {
    const py = yScale(yTicks[t])
    plot.appendChild(svgEl("line", {
      x1: 0, y1: py, x2: plotW, y2: py,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    plot.appendChild(svgEl("text", {
      x: -6, y: py + 4,
      "text-anchor": "end",
      "font-size": 11,
      fill: "var(--mj-text-muted, #6b7280)"
    }, formatNumber(yTicks[t])))
  }

  /* Build flat point list with pixel coords and series info */
  const flatPoints = []
  for (let s = 0; s < series.length; s = s + 1) {
    const ser   = series[s]
    const pts   = ser.points || []
    const color = ctx.colorFor(ser.name)
    for (let p = 0; p < pts.length; p = p + 1) {
      const pt = pts[p]
      if (typeof pt.x !== "number" || typeof pt.y !== "number") {
        continue
      }
      flatPoints.push({
        x: xScale(pt.x),
        y: yScale(pt.y),
        dataX: pt.x,
        dataY: pt.y,
        label: pt.label || ser.name,
        seriesName: ser.name,
        color: color
      })
    }
  }

  if (flatPoints.length === 0) {
    return root
  }

  /* Compute Voronoi cells */
  const pixelPoints = flatPoints.map((fp) => ({ x: fp.x, y: fp.y }))
  const cells       = _voronoiCells(pixelPoints, plotW, plotH)

  const isOverlay = mode === "overlay"
  const fillOpacity = isOverlay ? "0" : "0.25"

  /* Draw cells */
  for (let i = 0; i < cells.length; i = i + 1) {
    const cell = cells[i]
    const pt   = flatPoints[i]
    if (cell.length < 3) {
      continue
    }

    const d       = _polygonPath(cell)
    const cellEl  = svgEl("path", {
      d: d,
      fill: pt.color,
      "fill-opacity": fillOpacity,
      stroke: "var(--mj-border-strong, #c7ccd6)",
      "stroke-width": 1
    }, [])

    cellEl.setAttribute("part", "cell")
    cellEl.setAttribute("tabindex", "0")
    cellEl.setAttribute("role", "img")
    cellEl.setAttribute("aria-label",
      `${pt.label} (${formatNumber(pt.dataX)}, ${formatNumber(pt.dataY)})`)
    cellEl.appendChild(svgEl("title", null,
      `${pt.label} (${formatNumber(pt.dataX)}, ${formatNumber(pt.dataY)})`))
    const capturedPt = pt
    const handler = () => {
      ctx.emit("mj-chart-cell-click", {
        series: capturedPt.seriesName,
        label: capturedPt.label,
        x: capturedPt.dataX,
        y: capturedPt.dataY
      })
    }
    cellEl.addEventListener("click", handler)
    cellEl.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault()
        handler()
      }
    })
    plot.appendChild(cellEl)
  }

  /* Seed point circles */
  for (let i = 0; i < flatPoints.length; i = i + 1) {
    const pt  = flatPoints[i]
    const dot = svgEl("circle", {
      cx: pt.x, cy: pt.y, r: 4,
      fill: pt.color,
      stroke: "var(--mj-surface, #ffffff)",
      "stroke-width": 1.5,
      "pointer-events": "none"
    }, [])
    dot.setAttribute("aria-hidden", "true")
    plot.appendChild(dot)

    /* Optional site label */
    if (pt.label !== null && pt.label !== undefined && pt.label !== pt.seriesName) {
      plot.appendChild(svgEl("text", {
        x: pt.x + 6, y: pt.y - 4,
        "font-size": 10,
        fill: "var(--mj-text, #14181f)",
        "pointer-events": "none"
      }, escapeHtml(pt.label)))
    }
  }

  return root
}


registerRenderer("voronoi", render)
