/*
 * ternary.js
 *
 * Three-axis triangular composition plot renderer.
 *
 * Registered types:
 *   "ternary"  - ternary diagram (a+b+c = 100%)
 *
 * Renderer contract: render(ctx) -> SVGElement  (a <g> within [0..width]x[0..height])
 *
 * Ternary-to-Cartesian:
 *   Given (a, b, c) with a+b+c = 100:
 *     x_norm = b/100 + (c/100)/2        (b is left-axis, c drives inward)
 *     y_norm = (c/100) * sqrt(3)/2
 *   Bottom-left vertex = 100% a, bottom-right = 100% b, top = 100% c.
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, formatNumber } from "../svgdraw.js";


/* ── ternary coordinate transform ────────────────────────────── */

function _ternaryToXY(a, b, c, tx, ty, side) {
  /*
   * Convert ternary (a, b, c) to pixel (x, y).
   *
   * :param tx: Left x of the bounding triangle in pixels.
   * :param ty: Top y of the bounding triangle in pixels.
   * :param side: Side length of the equilateral triangle in pixels.
   * :returns: { x, y }
   */
  const total = a + b + c
  const na = total > 0 ? a / total : 0
  const nb = total > 0 ? b / total : 0
  const nc = total > 0 ? c / total : 0

  /* Bottom-left = A vertex, bottom-right = B vertex, top = C vertex */
  const ax = tx
  const ay = ty + side * Math.sqrt(3) / 2
  const bx = tx + side
  const by = ay
  const cx2 = tx + side / 2
  const cy2 = ty

  const px = na * ax + nb * bx + nc * cx2
  const py = na * ay + nb * by + nc * cy2
  return { x: px, y: py }
}


/* ── gridlines ────────────────────────────────────────────────── */

function _drawGrid(plot, tx, ty, side, steps) {
  /*
   * Draw gridlines parallel to each side at equal-percentage intervals.
   */
  const height = side * Math.sqrt(3) / 2

  for (let i = 1; i < steps; i = i + 1) {
    const t = i / steps

    /* Lines parallel to A-B (bottom) — constant C percentage */
    const c = t
    const p1 = _ternaryToXY(1 - c, 0, c, tx, ty, side)
    const p2 = _ternaryToXY(0, 1 - c, c, tx, ty, side)
    plot.appendChild(svgEl("line", {
      x1: p1.x.toFixed(1), y1: p1.y.toFixed(1),
      x2: p2.x.toFixed(1), y2: p2.y.toFixed(1),
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 0.8
    }, []))

    /* Lines parallel to A-C (left) — constant B percentage */
    const b = t
    const p3 = _ternaryToXY(1 - b, b, 0, tx, ty, side)
    const p4 = _ternaryToXY(0, b, 1 - b, tx, ty, side)
    plot.appendChild(svgEl("line", {
      x1: p3.x.toFixed(1), y1: p3.y.toFixed(1),
      x2: p4.x.toFixed(1), y2: p4.y.toFixed(1),
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 0.8
    }, []))

    /* Lines parallel to B-C (right) — constant A percentage */
    const a = t
    const p5 = _ternaryToXY(a, 1 - a, 0, tx, ty, side)
    const p6 = _ternaryToXY(a, 0, 1 - a, tx, ty, side)
    plot.appendChild(svgEl("line", {
      x1: p5.x.toFixed(1), y1: p5.y.toFixed(1),
      x2: p6.x.toFixed(1), y2: p6.y.toFixed(1),
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 0.8
    }, []))
  }
  return
}


/* ── tick labels ──────────────────────────────────────────────── */

function _drawTicks(plot, tx, ty, side, steps) {
  const height = side * Math.sqrt(3) / 2

  for (let i = 0; i <= steps; i = i + 1) {
    const pct = Math.round((i / steps) * 100)
    const t = i / steps

    /* A-axis ticks (bottom-left edge) */
    const pa = _ternaryToXY(t, 0, 1 - t, tx, ty, side)
    plot.appendChild(svgEl("text", {
      x: (pa.x - 14).toFixed(1), y: (pa.y + 4).toFixed(1),
      "text-anchor": "end", "font-size": 9,
      fill: "var(--mj-text-muted, #6b7280)"
    }, String(100 - pct)))

    /* B-axis ticks (bottom edge) */
    const pb = _ternaryToXY(1 - t, t, 0, tx, ty, side)
    plot.appendChild(svgEl("text", {
      x: pb.x.toFixed(1), y: (pb.y + 16).toFixed(1),
      "text-anchor": "middle", "font-size": 9,
      fill: "var(--mj-text-muted, #6b7280)"
    }, String(pct)))

    /* C-axis ticks (right edge) */
    const pc = _ternaryToXY(0, 1 - t, t, tx, ty, side)
    plot.appendChild(svgEl("text", {
      x: (pc.x + 10).toFixed(1), y: (pc.y + 4).toFixed(1),
      "text-anchor": "start", "font-size": 9,
      fill: "var(--mj-text-muted, #6b7280)"
    }, String(pct)))
  }
  return
}


/* ── main renderer ────────────────────────────────────────────── */

export function render(ctx) {
  /*
   * Render a ternary composition diagram.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const raw = ctx.raw
  const root = svgEl("g", { part: "plot" }, [])

  if (raw === null || raw === undefined) {
    return root
  }

  const meta = (raw.meta !== null && raw.meta !== undefined) ? raw.meta : {}
  const aLabel = meta.aLabel || "A"
  const bLabel = meta.bLabel || "B"
  const cLabel = meta.cLabel || "C"

  /* Fit equilateral triangle into available space with margin */
  const margin = 50
  const availW = ctx.width - margin * 2
  const availH = ctx.height - margin * 2
  /* side such that height = side * sqrt(3)/2 fits in availH */
  const sideFromH = availH / (Math.sqrt(3) / 2)
  const side = Math.min(availW, sideFromH)
  const triH = side * Math.sqrt(3) / 2

  /* Center the triangle */
  const tx = (ctx.width - side) / 2
  const ty = (ctx.height - triH) / 2

  const bx = tx
  const by = ty + triH
  const cx2 = tx + side
  const cy2 = by
  const apx = tx + side / 2
  const apy = ty

  /* Triangle border */
  const triPts = `${bx.toFixed(1)},${by.toFixed(1)} ` +
    `${cx2.toFixed(1)},${cy2.toFixed(1)} ` +
    `${apx.toFixed(1)},${apy.toFixed(1)}`
  root.appendChild(svgEl("polygon", {
    points: triPts,
    fill: "none",
    stroke: "var(--mj-border-strong, #c7ccd6)",
    "stroke-width": 1.5
  }, []))

  /* Grid */
  _drawGrid(root, tx, ty, side, 5)
  _drawTicks(root, tx, ty, side, 5)

  /* Vertex labels */
  root.appendChild(svgEl("text", {
    x: bx - 16, y: by + 6,
    "text-anchor": "end", "font-size": 12, "font-weight": "600",
    fill: "var(--mj-text, #14181f)"
  }, escapeHtml(aLabel)))

  root.appendChild(svgEl("text", {
    x: cx2 + 16, y: cy2 + 6,
    "text-anchor": "start", "font-size": 12, "font-weight": "600",
    fill: "var(--mj-text, #14181f)"
  }, escapeHtml(bLabel)))

  root.appendChild(svgEl("text", {
    x: apx, y: apy - 10,
    "text-anchor": "middle", "font-size": 12, "font-weight": "600",
    fill: "var(--mj-text, #14181f)"
  }, escapeHtml(cLabel)))

  /* Region overlays */
  const regions = (raw.regions !== null && raw.regions !== undefined) ? raw.regions : []
  for (let r = 0; r < regions.length; r = r + 1) {
    const region = regions[r]
    const vertices = region.vertices
    if (vertices === null || vertices === undefined || vertices.length < 3) {
      continue
    }
    const pts = vertices.map((v) => {
      const p = _ternaryToXY(v.a, v.b, v.c, tx, ty, side)
      return p.x.toFixed(1) + "," + p.y.toFixed(1)
    }).join(" ")
    const fillColor = region.color || "var(--mj-color-accent-300, #80a8ff)"
    const rLabel = escapeHtml(region.name || "Region")
    const poly = svgEl("polygon", {
      points: pts,
      fill: fillColor,
      "fill-opacity": 0.3,
      stroke: fillColor,
      "stroke-width": 1,
      part: "region",
      "aria-label": rLabel
    }, [])
    poly.appendChild(svgEl("title", null, rLabel))
    root.appendChild(poly)
    /* Region name label at centroid */
    const cx3 = vertices.reduce((s, v) => s + v.a, 0) / vertices.length
    const cy3 = vertices.reduce((s, v) => s + v.b, 0) / vertices.length
    const cz = vertices.reduce((s, v) => s + v.c, 0) / vertices.length
    const lp = _ternaryToXY(cx3, cy3, cz, tx, ty, side)
    root.appendChild(svgEl("text", {
      x: lp.x.toFixed(1), y: lp.y.toFixed(1),
      "text-anchor": "middle", "font-size": 9,
      fill: "var(--mj-text, #14181f)"
    }, escapeHtml(region.name || "")))
  }

  /* Data series */
  const series = (raw.series !== null && raw.series !== undefined) ? raw.series : []
  const connect = ctx.attrs("connect", "false") === "true"

  for (let s = 0; s < series.length; s = s + 1) {
    const ser = series[s]
    const pts = ser.points
    if (pts === null || pts === undefined || pts.length === 0) {
      continue
    }
    const color = ctx.colorFor(ser.name)
    const pixPts = pts.map((p) => _ternaryToXY(p.a, p.b, p.c, tx, ty, side))

    if (connect === true && pixPts.length > 1) {
      let pathData = "M" + pixPts[0].x.toFixed(1) + "," + pixPts[0].y.toFixed(1)
      for (let p = 1; p < pixPts.length; p = p + 1) {
        pathData = pathData + " L" + pixPts[p].x.toFixed(1) + "," + pixPts[p].y.toFixed(1)
      }
      root.appendChild(svgEl("path", {
        d: pathData,
        fill: "none",
        stroke: color,
        "stroke-width": 1.5
      }, []))
    }

    for (let p = 0; p < pts.length; p = p + 1) {
      const pt = pts[p]
      const px2 = pixPts[p]
      const label = escapeHtml(
        ser.name + " a=" + formatNumber(pt.a) +
        " b=" + formatNumber(pt.b) +
        " c=" + formatNumber(pt.c)
      )
      const dot = svgEl("circle", {
        cx: px2.x.toFixed(1), cy: px2.y.toFixed(1), r: 5,
        fill: color,
        stroke: "var(--mj-surface, #fff)",
        "stroke-width": 1,
        part: "point",
        tabindex: "0",
        role: "img",
        "aria-label": label
      }, [])
      dot.appendChild(svgEl("title", null, label))
      const detail = { series: ser.name, a: pt.a, b: pt.b, c: pt.c }
      const handler = () => { ctx.emit("mj-chart-ternary-click", detail) }
      dot.addEventListener("click", handler)
      dot.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault()
          handler()
        }
      })
      root.appendChild(dot)
    }
  }

  return root
}


registerRenderer("ternary", render)
