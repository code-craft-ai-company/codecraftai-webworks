/*
 * ternary.js
 *
 * Three-axis triangular composition plot renderer.
 *
 * Registered types:
 *   "ternary"  - ternary diagram (a+b+c = 100%)
 *
 * Data:
 *   { meta: { aLabel, bLabel, cLabel },
 *     series: [{ name, points: [{ a, b, c }, ...] }],
 *     regions?: [{ name, color?, vertices: [{ a, b, c }, ...] }],
 *     connect?: true }                (or the `connect="true"` attribute)
 *   Components are normalised by their total. A point whose components are
 *   not all finite and non-negative, or whose total is not positive, is
 *   skipped. Each edge is labelled with the component that is constant
 *   along the gridlines that meet it: A on the left edge (0 at the C
 *   vertex, 100 at the A vertex), B on the bottom edge, C on the right edge.
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
import { svgEl, formatNumber } from "../svgdraw.js";
import { booleanOption } from "../chartoptions.js";


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
  /*
   * Percentage labels along the three edges.
   */
  for (let i = 0; i <= steps; i = i + 1) {
    const pct = Math.round((i / steps) * 100)
    const t = i / steps

    /* A-axis ticks (left edge): the point where a = pct is labelled pct. */
    const pa = _ternaryToXY(t, 0, 1 - t, tx, ty, side)
    plot.appendChild(svgEl("text", {
      x: (pa.x - 8).toFixed(1), y: (pa.y + 3).toFixed(1),
      "text-anchor": "end", "font-size": 9,
      fill: "var(--mj-text-muted, #6b7280)"
    }, String(pct)))

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
      x: (pc.x + 8).toFixed(1), y: (pc.y + 3).toFixed(1),
      "text-anchor": "start", "font-size": 9,
      fill: "var(--mj-text-muted, #6b7280)"
    }, String(pct)))
  }
  return
}


/* ── main renderer ────────────────────────────────────────────── */

function _composition(point) {
  /*
   * The (a, b, c) of a point when it can be plotted: every component a
   * finite, non-negative number and a positive total. Otherwise null.
   */
  if (point === null || typeof point !== "object") {
    return null
  }
  const parts = [point.a, point.b, point.c]
  for (let i = 0; i < parts.length; i = i + 1) {
    if (typeof parts[i] !== "number" || Number.isFinite(parts[i]) === false || parts[i] < 0) {
      return null
    }
  }
  const total = parts[0] + parts[1] + parts[2]
  if (total <= 0) {
    return null
  }
  return { a: parts[0], b: parts[1], c: parts[2], total: total }
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


export function render(ctx) {
  /*
   * Render a ternary composition diagram.
   *
   * :param ctx: The renderer context.
   * :returns: An <g> SVGElement.
   */
  const raw = ctx.raw !== null && ctx.raw !== undefined ? ctx.raw : {}
  const root = svgEl("g", { part: "plot" }, [])

  const meta = ctx.model.meta
  const textOf = (value, fallback) => (typeof value === "string" && value.length > 0 ? value : fallback)
  const aLabel = textOf(meta.aLabel, "A")
  const bLabel = textOf(meta.bLabel, "B")
  const cLabel = textOf(meta.cLabel, "C")

  /*
   * Fit the triangle: the side margins hold the edge tick labels plus the
   * wider of the bottom vertex labels (about 7px per character at 12px).
   */
  const labelWidth = Math.max(aLabel.length, bLabel.length) * 7
  const sideMargin = Math.min(Math.max(30, labelWidth * 0.6 + 26), ctx.width / 4)
  const topMargin = 28
  const bottomMargin = 40
  const availW = Math.max(ctx.width - sideMargin * 2, 20)
  const availH = Math.max(ctx.height - topMargin - bottomMargin, 20)
  const side = Math.min(availW, availH / (Math.sqrt(3) / 2))
  const triH = side * Math.sqrt(3) / 2

  const tx = (ctx.width - side) / 2
  const ty = topMargin + (availH - triH) / 2

  const bx = tx
  const by = ty + triH
  const cx2 = tx + side
  const cy2 = by
  const apx = tx + side / 2
  const apy = ty

  /* Frame, grid, ticks and vertex labels (decoration). */
  const decor = svgEl("g", { "aria-hidden": "true", part: "grid" }, [])
  _drawGrid(decor, tx, ty, side, 5)
  decor.appendChild(svgEl("polygon", {
    points: `${bx.toFixed(1)},${by.toFixed(1)} ${cx2.toFixed(1)},${cy2.toFixed(1)} ${apx.toFixed(1)},${apy.toFixed(1)}`,
    fill: "none",
    stroke: "var(--mj-border-strong, #878e9c)",
    "stroke-width": 1.5
  }, []))
  _drawTicks(decor, tx, ty, side, 5)

  /* Vertex labels sit outside the tick-label band. */
  decor.appendChild(svgEl("text", {
    x: bx - 4, y: by + 32,
    "text-anchor": "end", "font-size": 12, "font-weight": "600",
    fill: "var(--mj-text, #14181f)"
  }, aLabel))
  decor.appendChild(svgEl("text", {
    x: cx2 + 4, y: cy2 + 32,
    "text-anchor": "start", "font-size": 12, "font-weight": "600",
    fill: "var(--mj-text, #14181f)"
  }, bLabel))
  decor.appendChild(svgEl("text", {
    x: apx, y: apy - 12,
    "text-anchor": "middle", "font-size": 12, "font-weight": "600",
    fill: "var(--mj-text, #14181f)"
  }, cLabel))
  root.appendChild(decor)

  const tableRows = []

  /* Region overlays */
  const regions = Array.isArray(raw.regions) === true ? raw.regions : []
  const regionGroup = svgEl("g", { part: "regions" }, [])
  for (let r = 0; r < regions.length; r = r + 1) {
    const region = regions[r]
    if (region === null || typeof region !== "object" || Array.isArray(region.vertices) === false) {
      continue
    }
    const vertices = region.vertices.map(_composition).filter((v) => v !== null)
    if (vertices.length < 3) {
      continue
    }
    const pts = vertices.map((v) => {
      const p = _ternaryToXY(v.a, v.b, v.c, tx, ty, side)
      return p.x.toFixed(1) + "," + p.y.toFixed(1)
    }).join(" ")
    const name = textOf(region.name, `Region ${r + 1}`)
    const fillColor = typeof region.color === "string" && region.color.length > 0
      ? region.color : ctx.colorFor(`region:${name}`)
    const poly = svgEl("polygon", {
      points: pts,
      fill: fillColor,
      "fill-opacity": 0.25,
      stroke: fillColor,
      "stroke-width": 1,
      part: "region",
      role: "img",
      "aria-label": `Region ${name}`
    }, [svgEl("title", null, name)])
    regionGroup.appendChild(poly)

    /* Region name at the mean composition of its vertices. */
    const mean = { a: 0, b: 0, c: 0 }
    for (let v = 0; v < vertices.length; v = v + 1) {
      mean.a = mean.a + vertices[v].a / vertices[v].total
      mean.b = mean.b + vertices[v].b / vertices[v].total
      mean.c = mean.c + vertices[v].c / vertices[v].total
    }
    const lp = _ternaryToXY(mean.a, mean.b, mean.c, tx, ty, side)
    regionGroup.appendChild(svgEl("text", {
      x: lp.x.toFixed(1), y: lp.y.toFixed(1),
      "text-anchor": "middle", "font-size": 9,
      fill: "var(--mj-text, #14181f)",
      "aria-hidden": "true"
    }, typeof region.name === "string" ? region.name : ""))
  }
  root.appendChild(regionGroup)

  /* Data series */
  const series = ctx.model.series
  const connect = booleanOption(ctx, "connect", raw.connect === true)
  const percent = (value, total) => formatNumber((value / total) * 100, { maximumFractionDigits: 1 })

  for (let s = 0; s < series.length; s = s + 1) {
    const ser = series[s]
    const pts = Array.isArray(ser.points) === true ? ser.points : []
    if (pts.length === 0) {
      continue
    }
    const color = ctx.colorFor(ser.name)
    const group = svgEl("g", { part: "series", "data-series": ser.name }, [])
    const parts = pts.map(_composition)
    const pixPts = parts.map((p) => (p === null ? null : _ternaryToXY(p.a, p.b, p.c, tx, ty, side)))

    if (connect === true) {
      /* A skipped point breaks the path. */
      let pathData = ""
      let pen = false
      for (let p = 0; p < pixPts.length; p = p + 1) {
        if (pixPts[p] === null) {
          pen = false
          continue
        }
        pathData = pathData + `${pen === true ? "L" : "M"}${pixPts[p].x.toFixed(1)},${pixPts[p].y.toFixed(1)} `
        pen = true
      }
      if (pathData.length > 0) {
        group.appendChild(svgEl("path", {
          d: pathData.trim(),
          fill: "none",
          stroke: color,
          "stroke-width": 1.5
        }, []))
      }
    }

    for (let p = 0; p < pts.length; p = p + 1) {
      const part = parts[p]
      const px2 = pixPts[p]
      if (part === null || px2 === null) {
        continue
      }
      const label = `${ser.name}: ${aLabel} ${percent(part.a, part.total)}%, ` +
        `${bLabel} ${percent(part.b, part.total)}%, ${cLabel} ${percent(part.c, part.total)}%`
      const dot = svgEl("circle", {
        cx: px2.x.toFixed(1), cy: px2.y.toFixed(1), r: 5,
        fill: color,
        stroke: "var(--mj-surface, #fff)",
        "stroke-width": 1,
        part: "point",
        tabindex: "0",
        role: "img",
        "aria-label": label
      }, [svgEl("title", null, label)])
      _attachActivation(dot, ctx, "mj-chart-ternary-click", { series: ser.name, a: part.a, b: part.b, c: part.c })
      group.appendChild(dot)
      tableRows.push([ser.name, (part.a / part.total) * 100, (part.b / part.total) * 100,
        (part.c / part.total) * 100])
    }
    root.appendChild(group)
  }

  ctx.setTable({
    columns: ["Series", `${aLabel} (%)`, `${bLabel} (%)`, `${cLabel} (%)`],
    rows: tableRows
  })
  return root
}


registerRenderer("ternary", render)
