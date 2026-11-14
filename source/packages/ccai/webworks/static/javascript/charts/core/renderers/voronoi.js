/*
 * voronoi.js
 *
 * Voronoi diagram renderer — partitions the 2-D plot surface into
 * nearest-neighbour regions around seed points, by half-plane clipping
 * (Sutherland-Hodgman on perpendicular bisectors), without external
 * libraries.
 *
 * Cells are computed in DATA units (the Euclidean partition of the data
 * space) and then mapped to the screen, so they do not change when the
 * chart is resized. `aspect="equal"` (attribute, or raw.aspect) draws both
 * axes with one scale so the cells also look Euclidean on screen.
 *
 * Each cell is clipped only by the sites that can still reach it (sites
 * are tried nearest first; one farther than twice the cell's radius
 * cannot cut it), which keeps large inputs fast. Duplicate sites are
 * merged. The domain is padded so edge seeds and their labels stay inside.
 *
 * Registered types:
 *   "voronoi"
 *
 * ctx.raw shape:
 *   raw.series  [{name, points:[{x, y, label?}]}]
 *
 * Attribute `mode`: "filled" (default) | "overlay" (outlines only).
 *
 * Interaction: each cell emits `mj-chart-cell-click` { series, label, x, y }.
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber } from "../svgdraw.js";
import { linearScale, niceTicks } from "../scales.js";


/* ── half-plane polygon clipping (Sutherland-Hodgman on line bisectors) ─ */

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


function _voronoiCells(points, box) {
  /*
   * Compute Voronoi cells for 2-D points inside a bounding box.
   *
   * For each site the cell starts as the box and is clipped by the
   * perpendicular bisector to other sites, nearest first; a site farther
   * than twice the cell's current radius cannot cut the cell, so the
   * remaining sites are skipped.
   *
   * :param points: Array of {x, y} (distinct).
   * :param box: { x0, y0, x1, y1 }.
   * :returns: Array of polygons (arrays of {x,y}), one per input point.
   */
  const boundingBox = [
    { x: box.x0, y: box.y0 }, { x: box.x1, y: box.y0 },
    { x: box.x1, y: box.y1 }, { x: box.x0, y: box.y1 }
  ]
  const cells = []

  for (let i = 0; i < points.length; i = i + 1) {
    const si = points[i]
    let cell = boundingBox.slice()
    const others = []
    for (let j = 0; j < points.length; j = j + 1) {
      if (j !== i) {
        const dx = points[j].x - si.x
        const dy = points[j].y - si.y
        others.push({ index: j, distance: dx * dx + dy * dy })
      }
    }
    others.sort((a, b) => a.distance - b.distance)

    for (let k = 0; k < others.length; k = k + 1) {
      let reach = 0
      for (let v = 0; v < cell.length; v = v + 1) {
        const dx = cell[v].x - si.x
        const dy = cell[v].y - si.y
        reach = Math.max(reach, dx * dx + dy * dy)
      }
      /* distance^2 > (2 * radius)^2 = 4 * radius^2: no farther site matters. */
      if (others[k].distance > 4 * reach) {
        break
      }
      const sj = points[others[k].index]
      const mx = (si.x + sj.x) / 2
      const my = (si.y + sj.y) / 2
      const dx = sj.x - si.x
      const dy = sj.y - si.y
      cell = _clipPolygonByHalfPlane(cell, mx + dy, my - dx, mx - dy, my + dx)
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

function _paddedExtent(values) {
  /*
   * [min, max] widened by 6% each side (a single value gets +-1).
   */
  let low = Math.min(...values)
  let high = Math.max(...values)
  if (low === high) {
    low = low - 1
    high = high + 1
  }
  const pad = (high - low) * 0.06
  return [low - pad, high + pad]
}


export function render(ctx) {
  /*
   * Render a Voronoi diagram.
   *
   * :param ctx: The renderer context.
   * :returns: A <g> SVGElement.
   */
  const raw = ctx.raw !== null && ctx.raw !== undefined ? ctx.raw : {}
  const root = svgEl("g", { part: "plot" }, [])
  const series = ctx.model.series

  /* Sites: finite x / y, duplicates merged (labels joined). */
  const sites = []
  const byKey = new Map()
  for (let s = 0; s < series.length; s = s + 1) {
    const entry = series[s]
    const points = Array.isArray(entry.points) === true ? entry.points : []
    for (let p = 0; p < points.length; p = p + 1) {
      const point = points[p]
      if (point === null || typeof point !== "object" ||
          typeof point.x !== "number" || Number.isFinite(point.x) === false ||
          typeof point.y !== "number" || Number.isFinite(point.y) === false) {
        continue
      }
      const label = point.label !== undefined && point.label !== null ? String(point.label) : null
      const key = `${point.x}|${point.y}`
      if (byKey.has(key) === true) {
        const site = byKey.get(key)
        if (label !== null) {
          site.labels.push(label)
        }
        continue
      }
      const site = {
        dataX: point.x, dataY: point.y, labels: label !== null ? [label] : [],
        seriesName: entry.name, color: ctx.colorFor(entry.name)
      }
      byKey.set(key, site)
      sites.push(site)
    }
  }

  ctx.setTable({
    columns: ["Series", "Label", "X", "Y"],
    rows: sites.map((site) => [site.seriesName, site.labels.join(", "), site.dataX, site.dataY]),
    caption: ctx.label
  })

  if (sites.length === 0) {
    return root
  }

  const mode = ctx.attrs("mode", "filled")
  const equal = ctx.attrs("aspect", raw.aspect === "equal" ? "equal" : null) === "equal"
  const margin = { top: 12, right: 16, bottom: 32, left: 48 }
  const plotW = Math.max(ctx.width - margin.left - margin.right, 10)
  const plotH = Math.max(ctx.height - margin.top - margin.bottom, 10)

  let xDomain = _paddedExtent(sites.map((site) => site.dataX))
  let yDomain = _paddedExtent(sites.map((site) => site.dataY))
  if (equal === true) {
    /* One scale for both axes: widen the narrower domain to the box's ratio. */
    const unit = Math.max((xDomain[1] - xDomain[0]) / plotW, (yDomain[1] - yDomain[0]) / plotH)
    const xMid = (xDomain[0] + xDomain[1]) / 2
    const yMid = (yDomain[0] + yDomain[1]) / 2
    xDomain = [xMid - unit * plotW / 2, xMid + unit * plotW / 2]
    yDomain = [yMid - unit * plotH / 2, yMid + unit * plotH / 2]
  }
  const xScale = linearScale(xDomain, [0, plotW])
  const yScale = linearScale(yDomain, [plotH, 0])

  const plot = svgEl("g", { transform: `translate(${margin.left},${margin.top})` }, [])
  root.appendChild(plot)

  /* Axes (decoration). */
  const axes = svgEl("g", { "aria-hidden": "true" }, [])
  plot.appendChild(axes)
  const xTicks = niceTicks(xDomain[0], xDomain[1], Math.max(Math.min(Math.floor(plotW / 70), 6), 2))
  for (let t = 0; t < xTicks.length; t = t + 1) {
    const px = xScale(xTicks[t])
    axes.appendChild(svgEl("line", {
      x1: px, y1: 0, x2: px, y2: plotH, stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    axes.appendChild(svgEl("text", {
      x: px, y: plotH + 14, "text-anchor": "middle", "font-size": 11,
      fill: "var(--mj-text-muted, #5f6673)"
    }, formatNumber(xTicks[t])))
  }
  const yTicks = niceTicks(yDomain[0], yDomain[1], Math.max(Math.min(Math.floor(plotH / 40), 6), 2))
  for (let t = 0; t < yTicks.length; t = t + 1) {
    const py = yScale(yTicks[t])
    axes.appendChild(svgEl("line", {
      x1: 0, y1: py, x2: plotW, y2: py, stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 1
    }, []))
    axes.appendChild(svgEl("text", {
      x: -6, y: py + 4, "text-anchor": "end", "font-size": 11, fill: "var(--mj-text-muted, #5f6673)"
    }, formatNumber(yTicks[t])))
  }

  /* Cells in data units, drawn in pixels. */
  const cells = _voronoiCells(
    sites.map((site) => ({ x: site.dataX, y: site.dataY })),
    { x0: xDomain[0], y0: yDomain[0], x1: xDomain[1], y1: yDomain[1] }
  )
  const fillOpacity = mode === "overlay" ? "0" : "0.25"

  for (let i = 0; i < cells.length; i = i + 1) {
    const cell = cells[i]
    const site = sites[i]
    if (cell.length < 3) {
      continue
    }
    const pixels = cell.map((vertex) => ({ x: xScale(vertex.x), y: yScale(vertex.y) }))
    const name = site.labels.length > 0 ? site.labels.join(", ") : site.seriesName
    const label = `${site.seriesName}, ${name} (${formatNumber(site.dataX)}, ${formatNumber(site.dataY)})`
    const cellEl = svgEl("path", {
      d: _polygonPath(pixels), fill: site.color, "fill-opacity": fillOpacity,
      stroke: "var(--mj-border-strong, #878e9c)", "stroke-width": 1,
      part: "cell", tabindex: "0", role: "img", "aria-label": label
    }, [svgEl("title", null, label)])
    const captured = site
    const handler = () => {
      ctx.emit("mj-chart-cell-click", {
        series: captured.seriesName, label: captured.labels.join(", "), x: captured.dataX, y: captured.dataY
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

  /* Seeds and labels (flipped to the left near the right edge). */
  const seeds = svgEl("g", { "aria-hidden": "true", "pointer-events": "none" }, [])
  plot.appendChild(seeds)
  for (let i = 0; i < sites.length; i = i + 1) {
    const site = sites[i]
    const x = xScale(site.dataX)
    const y = yScale(site.dataY)
    seeds.appendChild(svgEl("circle", {
      cx: x.toFixed(2), cy: y.toFixed(2), r: 4, fill: site.color,
      stroke: "var(--mj-surface, #ffffff)", "stroke-width": 1.5
    }, []))
    if (site.labels.length > 0) {
      const text = site.labels.join(", ")
      const flip = x + 6 + text.length * 6 > plotW
      seeds.appendChild(svgEl("text", {
        x: (flip === true ? x - 6 : x + 6).toFixed(2), y: (y - 5).toFixed(2),
        "text-anchor": flip === true ? "end" : "start", "font-size": 10,
        fill: "var(--mj-text, #14181f)"
      }, text))
    }
  }

  return root
}


registerRenderer("voronoi", render)
