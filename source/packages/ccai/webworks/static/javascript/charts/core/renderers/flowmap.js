/*
 * flowmap.js
 *
 * Geographic flow/route/density/contour/cartogram renderers. Geometry input,
 * projections, class colours and legends come from geomap.js; see its header
 * for the base-map geometry (`geojson` / `topology`), `feature-key` and
 * `projection` options, which apply here too.
 *
 * Registered types (dispatched on ctx.type):
 *   "flow-map"    — directed curved flows between geographic nodes
 *   "route-map"   — polylines along waypoint sequences over a base map
 *   "geo-heatmap" — Gaussian kernel-density surface over a base map
 *   "isoline"     — contour lines / filled contour bands from a lon/lat grid
 *   "cartogram"   — value-scaled region map (area or Dorling circles)
 *
 * Data shapes (ctx.raw):
 *   flow-map:    nodes [{id, lon|lng, lat, label?}], links [{source, target, value?}]
 *                Stroke width is proportional to value (from zero; attribute
 *                `taper="false"` draws equal widths). A→B and B→A bend to
 *                opposite sides; arrowheads follow the curve and stop at the
 *                node marker. `arc="straight"` draws straight flows.
 *   route-map:   series [{name, routes: [{id, waypoints: [{lon, lat, label?}]}]}]
 *                `variant="great-circle"` follows the geodesic (spherical
 *                interpolation) between waypoints; `show-stops="true"` marks
 *                each waypoint. Routes take the short way across the
 *                antimeridian.
 *   geo-heatmap: series [{name, points: [{lon, lat, weight?, id?, label?}]}];
 *                the `bandwidth` attribute is the kernel σ in pixels
 *                (default 30); the kernel reaches 3σ. Clicking the surface
 *                emits mj-chart-select { id, label, series, lon, lat, weight,
 *                density, distance } for the data point nearest the pointer
 *                (density: the surface there relative to the peak, 0-1;
 *                distance in px); Enter / Space report the hottest spot.
 *   isoline:     series [{name, levels?: [...], grid: {lon-min, lon-max,
 *                lat-min, lat-max, cols, rows, values: [...]}}]
 *                `values` is row-major, row 0 at lat-min. Without levels,
 *                nice levels are derived from the data. `variant="filled"`
 *                fills the bands between levels. A non-numeric value is a
 *                hole.
 *   cartogram:   regions [{id, value, label?, color?}] + geometry.
 *                Default (area): each region is shrunk about its centroid so
 *                its AREA is proportional to its value (the densest region
 *                keeps its size; a non-contiguous cartogram).
 *                `variant="dorling"`: circles with area proportional to value,
 *                separated by a collision-relaxation pass.
 *
 * Events: mj-chart-select { ... }, mj-chart-isoline-click { series, level }
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber } from "../svgdraw.js";
import { niceTicks } from "../scales.js";
import {
  isNumber, lonOf, makeInteractive, readFeatures, featureLines, geoFrame,
  geometryPath, isAreal, drawBaseMap, projectionName, classScale,
  appendClassLegend, appendSizeLegend, SEQ_RAMP, NO_DATA_FILL, REGION_STROKE
} from "./geomap.js";
import { paintRaster } from "./spectrogram.js";
import { booleanOption } from "../chartoptions.js";


/* ─── constants ─────────────────────────────────────────────────────────────── */

const MARGIN = 12
const LEGEND_W = 110
const NODE_RADIUS = 4

/* Heat ramp from theme tokens; alpha grows with density. */
const HEAT_STOPS = [
  "var(--mj-color-accent-300, #80a8ff)",
  "var(--mj-color-accent-500, #2563eb)",
  "var(--mj-chart-series-5, #d55181)",
  "var(--mj-chart-series-8, #e34948)"
]
const HEAT_LEVELS = 32


/* ─── shared helpers ────────────────────────────────────────────────────────── */

function _legendSpace(ctx) {
  /*
   * Width kept for an in-chart legend (none on very narrow charts).
   */
  const space = ctx.width >= 280 ? LEGEND_W : 0
  return space
}


function _frameFor(ctx, features, dataLines, drawW, drawH, dataPad) {
  /*
   * The projection frame: fitted to the base map when there is one, else
   * to the data with some padding (dataPad, default 12% of its size).
   */
  const lines = features.length > 0 ? featureLines(features) : dataLines
  const pad = typeof dataPad === "number" ? dataPad : 0.12
  const frame = geoFrame(lines, projectionName(ctx), drawW, drawH, features.length > 0 ? 0.02 : pad)
  return frame
}


function _rampColor(stops, t) {
  /*
   * A colour along a list of CSS colour stops, t in [0, 1].
   */
  const clamped = Math.max(0, Math.min(1, t))
  const scaled = clamped * (stops.length - 1)
  const lo = Math.min(Math.floor(scaled), stops.length - 2)
  const share = Math.round((scaled - lo) * 100)
  let color = stops[lo]
  if (share >= 100) {
    color = stops[lo + 1]
  } else if (share > 0) {
    color = `color-mix(in oklab, ${stops[lo + 1]} ${share}%, ${stops[lo]})`
  }
  return color
}


function _pathFromPoints(points, closed) {
  /*
   * Path data through pixel points; null entries break the path.
   */
  let data = ""
  let pen = false
  for (let i = 0; i < points.length; i = i + 1) {
    const p = points[i]
    if (p === null || p === undefined) {
      pen = false
      continue
    }
    data = data + `${pen === true ? "L" : "M"}${p.x.toFixed(2)},${p.y.toFixed(2)} `
    pen = true
  }
  if (closed === true && data.length > 0) {
    data = data + "Z"
  }
  return data.trim()
}


/* ─── flow-map renderer ─────────────────────────────────────────────────────── */

function _appendWidthLegend(parent, widthOf, maxValue, x, y, color) {
  /*
   * A legend of reference stroke widths for a value-proportional width.
   */
  const legend = svgEl("g", { part: "legend", "aria-hidden": "true" }, [])
  const roundDown = (v) => {
    const magnitude = Math.pow(10, Math.floor(Math.log10(v)))
    return Math.floor(v / magnitude) * magnitude
  }
  const values = []
  for (const share of [1, 0.5, 0.2]) {
    const v = roundDown(maxValue * share)
    if (v > 0 && values.indexOf(v) < 0) {
      values.push(v)
    }
  }
  for (let i = 0; i < values.length; i = i + 1) {
    const ly = y + 8 + i * 18
    legend.appendChild(svgEl("line", {
      x1: x, y1: ly, x2: x + 28, y2: ly,
      stroke: color, "stroke-width": widthOf(values[i]), "stroke-opacity": 0.7, "stroke-linecap": "round"
    }, []))
    legend.appendChild(svgEl("text", {
      x: x + 36, y: ly + 3, "font-size": 10, fill: "var(--mj-text-muted, #5f6673)"
    }, formatNumber(values[i])))
  }
  parent.appendChild(legend)
  return legend
}


function _renderFlowMap(ctx) {
  /*
   * Render a flow-map: curved, value-weighted arrows between nodes.
   *
   * :param ctx: Renderer context.
   * :returns: A <g> SVGElement.
   */
  const raw = ctx.raw !== null && ctx.raw !== undefined ? ctx.raw : {}
  const root = svgEl("g", { part: "plot" }, [])

  const nodes = (Array.isArray(raw.nodes) === true ? raw.nodes : [])
    .filter((n) => n !== null && typeof n === "object" && lonOf(n) !== null && isNumber(n.lat) === true)
  const links = (Array.isArray(raw.links) === true ? raw.links : [])
    .filter((l) => l !== null && typeof l === "object")
  if (nodes.length === 0) {
    return root
  }

  const legendAreaW = _legendSpace(ctx)
  const drawW = Math.max(ctx.width - MARGIN * 2 - legendAreaW, 10)
  const drawH = Math.max(ctx.height - MARGIN * 2, 10)
  const features = readFeatures(ctx)
  const frame = _frameFor(ctx, features, nodes.map((n) => [[lonOf(n), n.lat]]), drawW, drawH)

  const plot = svgEl("g", { transform: `translate(${MARGIN},${MARGIN})` }, [])
  root.appendChild(plot)
  drawBaseMap(plot, features, frame)

  const nodePos = new Map()
  for (let ni = 0; ni < nodes.length; ni = ni + 1) {
    const node = nodes[ni]
    const pt = frame.project(lonOf(node), node.lat)
    nodePos.set(String(node.id), { x: pt.x, y: pt.y, label: node.label !== undefined ? String(node.label) : String(node.id) })
  }

  let valMax = 0
  for (let li = 0; li < links.length; li = li + 1) {
    if (isNumber(links[li].value) === true && links[li].value > 0) {
      valMax = Math.max(valMax, links[li].value)
    }
  }
  const taper = booleanOption(ctx, "taper", true) && valMax > 0
  const maxWidth = 8
  const widthOf = (value) => (taper === true ? Math.max((maxWidth * value) / valMax, 0.75) : 2)
  const straight = ctx.attrs("arc", "curve") === "straight"
  const color = ctx.colorFor(0)

  const flows = svgEl("g", { part: "flows" }, [])
  plot.appendChild(flows)
  const pairCount = new Map()
  const tableRows = []

  for (let li = 0; li < links.length; li = li + 1) {
    const link = links[li]
    const src = nodePos.get(String(link.source))
    const tgt = nodePos.get(String(link.target))
    const value = isNumber(link.value) === true ? link.value : null
    tableRows.push([src !== undefined ? src.label : String(link.source),
      tgt !== undefined ? tgt.label : String(link.target), value === null ? "" : value])
    if (src === undefined || tgt === undefined || String(link.source) === String(link.target)) {
      continue
    }
    if (value !== null && value <= 0) {
      continue
    }
    const strokeW = widthOf(value !== null ? value : valMax)

    /*
     * One curvature sign for every flow: the perpendicular flips with the
     * direction, so A→B and B→A bend to opposite sides. Repeated flows of
     * one ordered pair bend further.
     */
    const pairKey = `${link.source}\u0000${link.target}`
    const repeat = pairCount.has(pairKey) === true ? pairCount.get(pairKey) : 0
    pairCount.set(pairKey, repeat + 1)
    const dx = tgt.x - src.x
    const dy = tgt.y - src.y
    const len = Math.hypot(dx, dy)
    if (len < 1) {
      continue
    }
    const curvature = straight === true ? 0 : 0.22 * (1 + 0.6 * repeat)
    const control = {
      x: (src.x + tgt.x) / 2 - (dy / len) * len * curvature,
      y: (src.y + tgt.y) / 2 + (dx / len) * len * curvature
    }

    /* The arrow follows the end tangent and stops at the node marker. */
    const tx = tgt.x - control.x
    const ty = tgt.y - control.y
    const tl = Math.hypot(tx, ty) || 1
    const ux = tx / tl
    const uy = ty / tl
    const headLength = 5 + strokeW * 1.2
    const tip = { x: tgt.x - ux * (NODE_RADIUS + 1.5), y: tgt.y - uy * (NODE_RADIUS + 1.5) }
    const base = { x: tip.x - ux * headLength, y: tip.y - uy * headLength }
    const halfWidth = Math.max(headLength * 0.45, strokeW * 0.9)

    const pathData = straight === true
      ? `M${src.x.toFixed(2)},${src.y.toFixed(2)} L${base.x.toFixed(2)},${base.y.toFixed(2)}`
      : `M${src.x.toFixed(2)},${src.y.toFixed(2)} Q${control.x.toFixed(2)},${control.y.toFixed(2)} ${base.x.toFixed(2)},${base.y.toFixed(2)}`
    const tooltipText = `${src.label} → ${tgt.label}${value !== null ? `: ${formatNumber(value)}` : ""}`

    const flow = svgEl("g", { part: "flow", "aria-label": tooltipText, cursor: "pointer" },
      [svgEl("title", null, tooltipText)])
    flow.appendChild(svgEl("path", {
      d: pathData, fill: "none", stroke: color, "stroke-width": strokeW,
      "stroke-opacity": 0.65, "stroke-linecap": "butt"
    }, []))
    flow.appendChild(svgEl("polygon", {
      points: `${tip.x.toFixed(2)},${tip.y.toFixed(2)} ` +
        `${(base.x - uy * halfWidth).toFixed(2)},${(base.y + ux * halfWidth).toFixed(2)} ` +
        `${(base.x + uy * halfWidth).toFixed(2)},${(base.y - ux * halfWidth).toFixed(2)}`,
      fill: color, "fill-opacity": 0.8
    }, []))
    makeInteractive(flow, "mj-chart-select", { source: link.source, target: link.target, value: value }, ctx.emit)
    flows.appendChild(flow)
  }

  /* Node markers on top of the flows. */
  const nodeGroup = svgEl("g", { part: "nodes" }, [])
  const labelGroup = svgEl("g", { "aria-hidden": "true", part: "labels" }, [])
  const showLabels = booleanOption(ctx, "show-labels", false)
  for (let ni = 0; ni < nodes.length; ni = ni + 1) {
    const node = nodes[ni]
    const pos = nodePos.get(String(node.id))
    const circle = svgEl("circle", {
      cx: pos.x, cy: pos.y, r: NODE_RADIUS,
      fill: "var(--mj-text, #14181f)",
      stroke: "var(--mj-surface, #ffffff)", "stroke-width": 1.5,
      part: "node", "aria-label": pos.label, cursor: "pointer"
    }, [svgEl("title", null, pos.label)])
    makeInteractive(circle, "mj-chart-select", { id: node.id, label: pos.label }, ctx.emit)
    nodeGroup.appendChild(circle)
    if (showLabels === true) {
      labelGroup.appendChild(svgEl("text", {
        x: pos.x, y: pos.y - 7, "text-anchor": "middle", "font-size": 9,
        fill: "var(--mj-text, #14181f)",
        stroke: "var(--mj-surface, #ffffff)", "stroke-width": 2.5, "paint-order": "stroke"
      }, pos.label))
    }
  }
  plot.appendChild(nodeGroup)
  plot.appendChild(labelGroup)

  if (taper === true && legendAreaW > 0) {
    _appendWidthLegend(plot, widthOf, valMax, Math.min(frame.bounds.x + frame.bounds.width + 16, drawW + 8), 0, color)
  }

  ctx.setTable({ columns: ["From", "To", "Value"], rows: tableRows })
  return root
}


/* ─── route-map renderer ────────────────────────────────────────────────────── */

function _greatCircle(a, b) {
  /*
   * Points along the great circle from a to b ([lon, lat] degrees), by
   * spherical linear interpolation, ends included.
   */
  const rad = Math.PI / 180
  const toVector = (p) => {
    const lon = p[0] * rad
    const lat = p[1] * rad
    return [Math.cos(lat) * Math.cos(lon), Math.cos(lat) * Math.sin(lon), Math.sin(lat)]
  }
  const va = toVector(a)
  const vb = toVector(b)
  const dot = Math.max(-1, Math.min(1, va[0] * vb[0] + va[1] * vb[1] + va[2] * vb[2]))
  const omega = Math.acos(dot)
  if (omega < 1e-6 || Math.PI - omega < 1e-6) {
    return [a, b]
  }
  const steps = Math.max(Math.ceil(omega / (2 * rad)), 2)
  const points = []
  for (let i = 0; i <= steps; i = i + 1) {
    const t = i / steps
    const wa = Math.sin((1 - t) * omega) / Math.sin(omega)
    const wb = Math.sin(t * omega) / Math.sin(omega)
    const x = wa * va[0] + wb * vb[0]
    const y = wa * va[1] + wb * vb[1]
    const z = wa * va[2] + wb * vb[2]
    points.push([Math.atan2(y, x) / rad, Math.atan2(z, Math.hypot(x, y)) / rad])
  }
  return points
}


function _renderRouteMap(ctx) {
  /*
   * Render a route-map: ordered polylines (or geodesics) along waypoints.
   *
   * :param ctx: Renderer context.
   * :returns: A <g> SVGElement.
   */
  const root = svgEl("g", { part: "plot" }, [])
  const series = ctx.model.series
  if (series.length === 0) {
    return root
  }
  const greatCircle = ctx.attrs("style", "polyline") === "great-circle"

  /* Each route as a coordinate line ([lon, lat] pairs). */
  const routes = []
  for (let si = 0; si < series.length; si = si + 1) {
    const list = Array.isArray(series[si].routes) === true ? series[si].routes : []
    for (let ri = 0; ri < list.length; ri = ri + 1) {
      const route = list[ri]
      const waypoints = route !== null && typeof route === "object" && Array.isArray(route.waypoints) === true
        ? route.waypoints.filter((w) => w !== null && typeof w === "object" && lonOf(w) !== null && isNumber(w.lat) === true)
        : []
      if (waypoints.length < 2) {
        continue
      }
      let line = waypoints.map((w) => [lonOf(w), w.lat])
      if (greatCircle === true) {
        let dense = []
        for (let wi = 0; wi < line.length - 1; wi = wi + 1) {
          const segment = _greatCircle(line[wi], line[wi + 1])
          dense = dense.concat(wi === 0 ? segment : segment.slice(1))
        }
        line = dense
      }
      routes.push({ series: series[si], route: route, waypoints: waypoints, line: line, index: ri })
    }
  }
  if (routes.length === 0) {
    return root
  }

  const drawW = Math.max(ctx.width - MARGIN * 2, 10)
  const drawH = Math.max(ctx.height - MARGIN * 2, 10)
  const features = readFeatures(ctx)
  const frame = _frameFor(ctx, features, routes.map((r) => r.line), drawW, drawH)

  const plot = svgEl("g", { transform: `translate(${MARGIN},${MARGIN})` }, [])
  root.appendChild(plot)
  drawBaseMap(plot, features, frame)

  const showStops = booleanOption(ctx, "show-stops", false)
  const routeGroup = svgEl("g", { part: "routes" }, [])
  plot.appendChild(routeGroup)
  const tableRows = []

  for (let i = 0; i < routes.length; i = i + 1) {
    const entry = routes[i]
    const color = ctx.colorFor(entry.series.name)
    /* projectLine keeps the route continuous across the antimeridian. */
    const projected = frame.projectLine(entry.line)
    const routeId = entry.route.id !== undefined ? String(entry.route.id) : `${entry.series.name} ${entry.index + 1}`
    const first = entry.waypoints[0]
    const last = entry.waypoints[entry.waypoints.length - 1]
    const endName = (w, fallback) => (w.label !== undefined ? String(w.label) : fallback)
    const tooltipText = `${entry.series.name}: ${routeId} (${endName(first, "start")} → ${endName(last, "end")})`

    const routePath = svgEl("path", {
      d: _pathFromPoints(projected, false),
      fill: "none", stroke: color, "stroke-width": 2, "stroke-opacity": 0.85,
      "stroke-linecap": "round", "stroke-linejoin": "round",
      part: "route", "aria-label": tooltipText, cursor: "pointer"
    }, [svgEl("title", null, tooltipText)])
    makeInteractive(routePath, "mj-chart-select", { id: entry.route.id, series: entry.series.name }, ctx.emit)
    routeGroup.appendChild(routePath)
    tableRows.push([entry.series.name, routeId, endName(first, ""), endName(last, ""), entry.waypoints.length])

    if (showStops === true) {
      const stops = frame.projectLine(entry.waypoints.map((w) => [lonOf(w), w.lat]))
      /* Align the stops with the drawn line (same side of the antimeridian). */
      const shift = projected[0] !== null && stops[0] !== null ? projected[0].x - stops[0].x : 0
      for (let wi = 0; wi < stops.length; wi = wi + 1) {
        const wp = entry.waypoints[wi]
        const stopLabel = wp.label !== undefined ? String(wp.label) : `Stop ${wi + 1}`
        const circle = svgEl("circle", {
          cx: stops[wi].x + shift, cy: stops[wi].y, r: 3,
          fill: color, stroke: "var(--mj-surface, #ffffff)", "stroke-width": 1,
          part: "stop", "aria-label": stopLabel, cursor: "pointer"
        }, [svgEl("title", null, stopLabel)])
        makeInteractive(circle, "mj-chart-select", { routeId: entry.route.id, waypointIndex: wi, label: stopLabel }, ctx.emit)
        routeGroup.appendChild(circle)
      }
    }
  }

  ctx.setTable({ columns: ["Series", "Route", "From", "To", "Waypoints"], rows: tableRows })
  return root
}


/* ─── geo-heatmap renderer ──────────────────────────────────────────────────── */

function _renderGeoHeatmap(ctx) {
  /*
   * Render a geographic heatmap: a Gaussian kernel density estimate on a
   * pixel grid, painted as a raster layer above the base map.
   *
   * :param ctx: Renderer context.
   * :returns: A <g> SVGElement.
   */
  const root = svgEl("g", { part: "plot" }, [])
  const series = ctx.model.series

  const samples = []
  for (let si = 0; si < series.length; si = si + 1) {
    const pts = Array.isArray(series[si].points) === true ? series[si].points : []
    for (let pi = 0; pi < pts.length; pi = pi + 1) {
      const pt = pts[pi]
      if (lonOf(pt) === null || isNumber(pt.lat) === false) {
        continue
      }
      const weight = isNumber(pt.weight) === true ? pt.weight : 1
      samples.push({
        series: series[si].name, lon: lonOf(pt), lat: pt.lat, weight: weight,
        id: pt.id !== undefined && pt.id !== null ? pt.id : null,
        label: pt.label !== undefined && pt.label !== null ? String(pt.label) : null
      })
    }
  }
  if (samples.length === 0) {
    return root
  }

  const legendAreaW = _legendSpace(ctx)
  const drawW = Math.max(ctx.width - MARGIN * 2 - legendAreaW, 10)
  const drawH = Math.max(ctx.height - MARGIN * 2, 10)
  const features = readFeatures(ctx)
  /* Room for the kernel tails around the outermost points. */
  const frame = _frameFor(ctx, features, samples.map((s) => [[s.lon, s.lat]]), drawW, drawH, 0.35)

  const plot = svgEl("g", { transform: `translate(${MARGIN},${MARGIN})` }, [])
  root.appendChild(plot)
  /* Base map in its own group; the heat layer is added after it. */
  drawBaseMap(plot, features, frame)

  const bwAttr = Number(ctx.attrs("bandwidth", "30"))
  const bandwidth = isNumber(bwAttr) === true && bwAttr > 0 ? bwAttr : 30

  const cell = 3
  const cols = Math.max(Math.round(drawW / cell), 2)
  const rows = Math.max(Math.round(drawH / cell), 2)
  const cellW = drawW / cols
  const cellH = drawH / rows
  const density = new Float32Array(cols * rows)
  const reach = Math.ceil((3 * bandwidth) / Math.min(cellW, cellH)) + 1

  for (let i = 0; i < samples.length; i = i + 1) {
    if (samples[i].weight <= 0) {
      continue
    }
    const p = frame.project(samples[i].lon, samples[i].lat)
    const colCenter = Math.floor(p.x / cellW)
    const rowCenter = Math.floor(p.y / cellH)
    for (let row = Math.max(rowCenter - reach, 0); row <= Math.min(rowCenter + reach, rows - 1); row = row + 1) {
      for (let col = Math.max(colCenter - reach, 0); col <= Math.min(colCenter + reach, cols - 1); col = col + 1) {
        const dx = (col + 0.5) * cellW - p.x
        const dy = (row + 0.5) * cellH - p.y
        const z2 = (dx * dx + dy * dy) / (bandwidth * bandwidth)
        if (z2 > 9) {
          continue
        }
        density[row * cols + col] = density[row * cols + col] + Math.exp(-0.5 * z2) * samples[i].weight
      }
    }
  }
  let densityMax = 0
  let peakCell = 0
  for (let i = 0; i < density.length; i = i + 1) {
    if (density[i] > densityMax) {
      densityMax = density[i]
      peakCell = i
    }
  }
  if (densityMax <= 0) {
    densityMax = 1
  }

  /* Palette: the heat ramp with alpha rising with density. */
  const palette = []
  for (let level = 0; level < HEAT_LEVELS; level = level + 1) {
    const t = level / (HEAT_LEVELS - 1)
    const alpha = Math.round(Math.min(1, 0.15 + t * 0.95) * 85)
    palette.push(`color-mix(in oklab, ${_rampColor(HEAT_STOPS, t)} ${alpha}%, transparent)`)
  }
  const heat = svgEl("g", { part: "heat", "aria-hidden": "true" }, [])
  const image = svgEl("image", {
    x: 0, y: 0, width: drawW, height: drawH, preserveAspectRatio: "none", part: "raster"
  }, [])
  heat.appendChild(image)
  plot.appendChild(heat)
  paintRaster(image, heat, palette, {
    columns: cols,
    rows: rows,
    indexAt: (col, row) => {
      const t = density[row * cols + col] / densityMax
      if (t < 0.015) {
        return -1
      }
      return Math.min(Math.round(t * (HEAT_LEVELS - 1)), HEAT_LEVELS - 1)
    }
  })

  /*
   * One summary mark for the surface. A click reports the relative density
   * under the pointer and the nearest data point; Enter / Space report the
   * hottest spot (mj-chart-select).
   */
  const summary = `${ctx.label}: density of ${samples.length} weighted points, kernel σ ${formatNumber(bandwidth)} px. ` +
    "Press Enter for the hottest spot."
  const surface = svgEl("rect", {
    x: 0, y: 0, width: drawW, height: drawH, fill: "transparent",
    part: "heat-surface", tabindex: "0", role: "img", "aria-label": summary
  }, [svgEl("title", null, summary)])
  const projected = samples.map((sample) => frame.project(sample.lon, sample.lat))
  const emitAt = (x, y) => {
    const col = Math.min(Math.max(Math.floor(x / cellW), 0), cols - 1)
    const row = Math.min(Math.max(Math.floor(y / cellH), 0), rows - 1)
    let nearest = 0
    let best = Infinity
    for (let i = 0; i < projected.length; i = i + 1) {
      const distance = Math.hypot(projected[i].x - x, projected[i].y - y)
      if (distance < best) {
        best = distance
        nearest = i
      }
    }
    const sample = samples[nearest]
    ctx.emit("mj-chart-select", {
      id: sample.id !== null ? sample.id : (sample.label !== null ? sample.label : null),
      label: sample.label,
      series: sample.series,
      lon: sample.lon,
      lat: sample.lat,
      weight: sample.weight,
      density: Math.round((density[row * cols + col] / densityMax) * 1000) / 1000,
      distance: Math.round(best)
    })
    return
  }
  surface.addEventListener("click", (event) => {
    const matrix = surface.getScreenCTM()
    if (matrix === null) {
      return
    }
    const local = new DOMPoint(event.clientX, event.clientY).matrixTransform(matrix.inverse())
    emitAt(local.x, local.y)
  })
  surface.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault()
      const peakCol = peakCell % cols
      const peakRow = Math.floor(peakCell / cols)
      emitAt((peakCol + 0.5) * cellW, (peakRow + 0.5) * cellH)
    }
  })
  plot.appendChild(surface)

  if (legendAreaW > 0) {
    const legend = svgEl("g", { part: "legend", "aria-hidden": "true" }, [])
    const lx = Math.min(frame.bounds.x + frame.bounds.width + 16, drawW + 8)
    const barH = Math.min(drawH - 20, 120)
    legend.appendChild(svgEl("text", {
      x: lx, y: 9, "font-size": 10, "font-weight": "600", fill: "var(--mj-text-muted, #5f6673)"
    }, "Density"))
    for (let i = 0; i < 16; i = i + 1) {
      legend.appendChild(svgEl("rect", {
        x: lx, y: 16 + barH - ((i + 1) / 16) * barH, width: 12, height: barH / 16 + 0.5,
        fill: palette[Math.round(((i + 0.5) / 16) * (HEAT_LEVELS - 1))]
      }, []))
    }
    legend.appendChild(svgEl("text", { x: lx + 16, y: 24, "font-size": 10, fill: "var(--mj-text-muted, #5f6673)" }, "high"))
    legend.appendChild(svgEl("text", { x: lx + 16, y: 16 + barH, "font-size": 10, fill: "var(--mj-text-muted, #5f6673)" }, "low"))
    plot.appendChild(legend)
  }

  ctx.setTable({
    columns: ["Series", "Latitude", "Longitude", "Weight"],
    rows: samples.map((s) => [s.series, s.lat, s.lon, s.weight])
  })
  return root
}


/* ─── isoline renderer ──────────────────────────────────────────────────────── */

function _contourSegments(at, cols, rows, level) {
  /*
   * Marching squares: the segments of the contour at `level`, in grid
   * coordinates (x = column, y = row). Cells with a hole are skipped.
   */
  const segments = []
  const cross = (v1, v2) => (Math.abs(v2 - v1) < 1e-12 ? 0.5 : (level - v1) / (v2 - v1))
  for (let row = 0; row < rows - 1; row = row + 1) {
    for (let col = 0; col < cols - 1; col = col + 1) {
      const v00 = at(col, row)
      const v10 = at(col + 1, row)
      const v01 = at(col, row + 1)
      const v11 = at(col + 1, row + 1)
      if (v00 === null || v10 === null || v01 === null || v11 === null) {
        continue
      }
      const idx = (v00 >= level ? 1 : 0) | (v10 >= level ? 2 : 0) | (v11 >= level ? 4 : 0) | (v01 >= level ? 8 : 0)
      if (idx === 0 || idx === 15) {
        continue
      }
      const top = { x: col + cross(v00, v10), y: row }
      const right = { x: col + 1, y: row + cross(v10, v11) }
      const bottom = { x: col + cross(v01, v11), y: row + 1 }
      const left = { x: col, y: row + cross(v00, v01) }
      const table = {
        1: [[top, left]], 2: [[top, right]], 3: [[left, right]], 4: [[right, bottom]],
        5: [[top, right], [bottom, left]], 6: [[top, bottom]], 7: [[left, bottom]],
        8: [[bottom, left]], 9: [[top, bottom]], 10: [[top, left], [right, bottom]],
        11: [[right, bottom]], 12: [[left, right]], 13: [[top, right]], 14: [[top, left]]
      }
      const pairs = table[idx]
      for (let p = 0; p < pairs.length; p = p + 1) {
        segments.push(pairs[p])
      }
    }
  }
  return segments
}


function _stitch(segments) {
  /*
   * Join segments that share end points into polylines.
   */
  const keyOf = (p) => `${p.x.toFixed(6)},${p.y.toFixed(6)}`
  const ends = new Map()
  const used = new Array(segments.length).fill(false)
  for (let i = 0; i < segments.length; i = i + 1) {
    for (const end of [0, 1]) {
      const key = keyOf(segments[i][end])
      if (ends.has(key) === false) {
        ends.set(key, [])
      }
      ends.get(key).push(i)
    }
  }
  const nextFrom = (point) => {
    const list = ends.get(keyOf(point))
    if (list === undefined) {
      return -1
    }
    for (let k = 0; k < list.length; k = k + 1) {
      if (used[list[k]] === false) {
        return list[k]
      }
    }
    return -1
  }
  const lines = []
  for (let i = 0; i < segments.length; i = i + 1) {
    if (used[i] === true) {
      continue
    }
    used[i] = true
    const line = [segments[i][0], segments[i][1]]
    /* Grow forward, then backward; each segment is used once (no loops). */
    for (const forward of [true, false]) {
      let guard = segments.length
      while (guard > 0) {
        guard = guard - 1
        const endPoint = forward === true ? line[line.length - 1] : line[0]
        const next = nextFrom(endPoint)
        if (next < 0) {
          break
        }
        used[next] = true
        const seg = segments[next]
        const other = keyOf(seg[0]) === keyOf(endPoint) ? seg[1] : seg[0]
        if (forward === true) {
          line.push(other)
        } else {
          line.unshift(other)
        }
      }
    }
    lines.push(line)
  }
  return lines
}


function _bandCellPolygon(corners, level) {
  /*
   * The part of one grid cell where the value is >= level: the corners that
   * are inside plus the crossing points on the edges, in order.
   *
   * :param corners: [{x, y, v}] in cell order (tl, tr, br, bl).
   */
  const polygon = []
  for (let i = 0; i < 4; i = i + 1) {
    const a = corners[i]
    const b = corners[(i + 1) % 4]
    if (a.v >= level) {
      polygon.push({ x: a.x, y: a.y })
    }
    if ((a.v >= level) !== (b.v >= level)) {
      const t = Math.abs(b.v - a.v) < 1e-12 ? 0.5 : (level - a.v) / (b.v - a.v)
      polygon.push({ x: a.x + (b.x - a.x) * t, y: a.y + (b.y - a.y) * t })
    }
  }
  return polygon
}


function _readIsoGrid(gridDef) {
  /*
   * Validate an isoline grid. Bounds of 0 are kept (only a missing bound
   * falls back). Returns null when the grid is unusable.
   */
  if (gridDef === null || typeof gridDef !== "object") {
    return null
  }
  const num = (value, fallback) => (isNumber(value) === true ? value : fallback)
  const cols = Math.round(num(gridDef.cols, 0))
  const rows = Math.round(num(gridDef.rows, 0))
  const values = Array.isArray(gridDef.values) === true ? gridDef.values : []
  if (cols < 2 || rows < 2 || values.length < cols * rows) {
    return null
  }
  const grid = {
    lonMin: num(gridDef["lon-min"], 0),
    lonMax: num(gridDef["lon-max"], 1),
    latMin: num(gridDef["lat-min"], 0),
    latMax: num(gridDef["lat-max"], 1),
    cols: cols,
    rows: rows,
    at: (col, row) => {
      const v = values[row * cols + col]
      return isNumber(v) === true ? v : null
    }
  }
  return grid
}


function _renderIsoline(ctx) {
  /*
   * Render contour lines (one path per level) or filled bands from a
   * lon/lat scalar grid.
   *
   * :param ctx: Renderer context.
   * :returns: A <g> SVGElement.
   */
  const root = svgEl("g", { part: "plot" }, [])
  const series = ctx.model.series

  const layers = []
  for (let si = 0; si < series.length; si = si + 1) {
    const grid = _readIsoGrid(series[si].grid)
    if (grid === null) {
      continue
    }
    let vMin = Infinity
    let vMax = -Infinity
    for (let row = 0; row < grid.rows; row = row + 1) {
      for (let col = 0; col < grid.cols; col = col + 1) {
        const v = grid.at(col, row)
        if (v !== null) {
          vMin = Math.min(vMin, v)
          vMax = Math.max(vMax, v)
        }
      }
    }
    if (vMin === Infinity) {
      continue
    }
    let levels = Array.isArray(series[si].levels) === true ? series[si].levels.filter((l) => isNumber(l) === true) : []
    if (levels.length === 0) {
      levels = niceTicks(vMin, vMax, 6).filter((l) => l > vMin && l < vMax)
    }
    levels = levels.slice().sort((a, b) => a - b)
    layers.push({ series: series[si], grid: grid, levels: levels, vMin: vMin, vMax: vMax })
  }
  if (layers.length === 0) {
    return root
  }

  const legendAreaW = _legendSpace(ctx)
  const drawW = Math.max(ctx.width - MARGIN * 2 - legendAreaW, 10)
  const drawH = Math.max(ctx.height - MARGIN * 2, 10)
  const features = readFeatures(ctx)
  const gridLines = layers.map((l) => [[l.grid.lonMin, l.grid.latMin], [l.grid.lonMax, l.grid.latMin],
    [l.grid.lonMax, l.grid.latMax], [l.grid.lonMin, l.grid.latMax]])
  const lines = features.length > 0 ? featureLines(features).concat(gridLines) : gridLines
  const frame = geoFrame(lines, projectionName(ctx), drawW, drawH, 0.02)

  const plot = svgEl("g", { transform: `translate(${MARGIN},${MARGIN})` }, [])
  root.appendChild(plot)
  drawBaseMap(plot, features, frame)

  const filled = ctx.attrs("style", "lines") === "filled"
  const tableRows = []
  const legendEntries = []

  for (let li = 0; li < layers.length; li = li + 1) {
    const layer = layers[li]
    const grid = layer.grid
    const levels = layer.levels
    const toPixel = (gx, gy) => frame.project(
      grid.lonMin + (gx / (grid.cols - 1)) * (grid.lonMax - grid.lonMin),
      grid.latMin + (gy / (grid.rows - 1)) * (grid.latMax - grid.latMin))
    /* Level colours spread over the readable part of the ramp. */
    const levelColor = (index) => SEQ_RAMP[Math.round(2 + (levels.length > 1 ? index / (levels.length - 1) : 1) * (SEQ_RAMP.length - 3))]
    const group = svgEl("g", { part: "isolines", "data-series": layer.series.name }, [])

    if (filled === true) {
      /* Stack the ">= level" regions from the lowest level up. */
      const bandColor = (index) => SEQ_RAMP[Math.round((levels.length > 1 ? index / (levels.length - 1) : 1) * (SEQ_RAMP.length - 2))]
      for (let lv = 0; lv < levels.length; lv = lv + 1) {
        let data = ""
        for (let row = 0; row < grid.rows - 1; row = row + 1) {
          for (let col = 0; col < grid.cols - 1; col = col + 1) {
            const corners = [[col, row], [col + 1, row], [col + 1, row + 1], [col, row + 1]]
              .map((c) => ({ x: c[0], y: c[1], v: grid.at(c[0], c[1]) }))
            if (corners.some((c) => c.v === null) === true) {
              continue
            }
            const polygon = _bandCellPolygon(corners, levels[lv])
            if (polygon.length >= 3) {
              data = data + _pathFromPoints(polygon.map((p) => toPixel(p.x, p.y)), true) + " "
            }
          }
        }
        if (data.length > 0) {
          const color = bandColor(lv)
          group.appendChild(svgEl("path", {
            d: data.trim(), fill: color, stroke: color, "stroke-width": 0.6, "stroke-linejoin": "round",
            "fill-opacity": 0.85, "aria-hidden": "true", part: "band"
          }, []))
        }
        legendEntries.push({ label: `≥ ${formatNumber(levels[lv])}`, color: bandColor(lv) })
      }
    }

    for (let lv = 0; lv < levels.length; lv = lv + 1) {
      const level = levels[lv]
      const polylines = _stitch(_contourSegments(grid.at, grid.cols, grid.rows, level))
      if (polylines.length === 0) {
        continue
      }
      const pixelLines = polylines.map((line) => line.map((p) => toPixel(p.x, p.y)))
      const color = filled === true ? "var(--mj-surface, #ffffff)" : levelColor(lv)
      const label = `${layer.series.name}: level ${formatNumber(level)}`
      const path = svgEl("path", {
        d: pixelLines.map((line) => _pathFromPoints(line, false)).join(" "),
        fill: "none", stroke: color, "stroke-width": filled === true ? 0.8 : 1.6,
        "stroke-linejoin": "round", "stroke-linecap": "round",
        part: "isoline", "aria-label": label, cursor: "pointer"
      }, [svgEl("title", null, label)])
      makeInteractive(path, "mj-chart-isoline-click", { series: layer.series.name, level: level }, ctx.emit)
      group.appendChild(path)
      if (filled === false) {
        legendEntries.push({ label: formatNumber(level), color: color })
      }

      /* One label per level, at the middle of its longest piece. */
      let longest = pixelLines[0]
      for (let k = 1; k < pixelLines.length; k = k + 1) {
        if (pixelLines[k].length > longest.length) {
          longest = pixelLines[k]
        }
      }
      if (longest.length >= 2) {
        const mid = Math.floor((longest.length - 1) / 2)
        const a = longest[mid]
        const b = longest[mid + 1]
        let angle = (Math.atan2(b.y - a.y, b.x - a.x) * 180) / Math.PI
        if (angle > 90) { angle = angle - 180 }
        if (angle < -90) { angle = angle + 180 }
        const mx = (a.x + b.x) / 2
        const my = (a.y + b.y) / 2
        group.appendChild(svgEl("text", {
          x: mx.toFixed(1), y: (my + 3).toFixed(1),
          transform: `rotate(${angle.toFixed(1)},${mx.toFixed(1)},${my.toFixed(1)})`,
          "text-anchor": "middle", "font-size": 9,
          fill: "var(--mj-text, #14181f)",
          stroke: "var(--mj-surface, #ffffff)", "stroke-width": 2.5, "paint-order": "stroke",
          "aria-hidden": "true"
        }, formatNumber(level)))
      }
    }
    plot.appendChild(group)

    for (let row = 0; row < grid.rows; row = row + 1) {
      for (let col = 0; col < grid.cols; col = col + 1) {
        const v = grid.at(col, row)
        tableRows.push([layer.series.name,
          grid.latMin + (row / (grid.rows - 1)) * (grid.latMax - grid.latMin),
          grid.lonMin + (col / (grid.cols - 1)) * (grid.lonMax - grid.lonMin),
          v === null ? "" : v])
      }
    }
  }

  if (legendAreaW > 0 && legendEntries.length > 0) {
    const legend = svgEl("g", { part: "legend", "aria-hidden": "true" }, [])
    const lx = Math.min(frame.bounds.x + frame.bounds.width + 16, drawW + 8)
    const shown = legendEntries.slice(-12).reverse()
    for (let i = 0; i < shown.length; i = i + 1) {
      const ly = i * 16
      if (filled === true) {
        legend.appendChild(svgEl("rect", { x: lx, y: ly, width: 12, height: 12, fill: shown[i].color }, []))
      } else {
        legend.appendChild(svgEl("line", { x1: lx, y1: ly + 6, x2: lx + 14, y2: ly + 6, stroke: shown[i].color, "stroke-width": 2 }, []))
      }
      legend.appendChild(svgEl("text", {
        x: lx + 18, y: ly + 10, "font-size": 10, fill: "var(--mj-text-muted, #5f6673)"
      }, shown[i].label))
    }
    plot.appendChild(legend)
  }

  ctx.setTable({ columns: ["Series", "Latitude", "Longitude", "Value"], rows: tableRows })
  return root
}


/* ─── cartogram renderer ────────────────────────────────────────────────────── */

function _ringArea(points) {
  /*
   * Signed shoelace area of a pixel ring.
   */
  let area = 0
  for (let i = 0; i < points.length; i = i + 1) {
    const a = points[i]
    const b = points[(i + 1) % points.length]
    area = area + a.x * b.y - b.x * a.y
  }
  return area / 2
}


function _featureShape(feature, frame) {
  /*
   * The projected area and the area-weighted centroid of the largest
   * polygon of a feature (pixel space).
   */
  const geometry = feature.geometry
  const polygons = geometry.type === "Polygon" ? [geometry.coordinates]
    : (geometry.type === "MultiPolygon" ? geometry.coordinates : [])
  let total = 0
  let best = null
  for (let p = 0; p < polygons.length; p = p + 1) {
    const rings = Array.isArray(polygons[p]) === true ? polygons[p] : []
    let area = 0
    let outer = null
    for (let r = 0; r < rings.length; r = r + 1) {
      const pts = frame.projectLine(rings[r]).filter((q) => q !== null)
      if (pts.length < 3) {
        continue
      }
      const ringArea = Math.abs(_ringArea(pts))
      area = r === 0 ? area + ringArea : area - ringArea
      if (r === 0) {
        outer = pts
      }
    }
    area = Math.max(area, 0)
    total = total + area
    if (outer !== null && (best === null || area > best.area)) {
      best = { area: area, ring: outer }
    }
  }
  let centroid = null
  if (best !== null) {
    let cx = 0
    let cy = 0
    let signed = 0
    const ring = best.ring
    for (let i = 0; i < ring.length; i = i + 1) {
      const a = ring[i]
      const b = ring[(i + 1) % ring.length]
      const cross = a.x * b.y - b.x * a.y
      signed = signed + cross
      cx = cx + (a.x + b.x) * cross
      cy = cy + (a.y + b.y) * cross
    }
    if (Math.abs(signed) > 1e-9) {
      centroid = { x: cx / (3 * signed), y: cy / (3 * signed) }
    } else {
      centroid = { x: ring.reduce((s, q) => s + q.x, 0) / ring.length, y: ring.reduce((s, q) => s + q.y, 0) / ring.length }
    }
  }
  return { area: total, centroid: centroid }
}


function _relaxCircles(circles, width, height) {
  /*
   * Separate overlapping circles (Dorling): repeated pairwise pushes plus
   * a weak pull back to each circle's home position, kept inside the box.
   */
  const iterations = 160
  for (let it = 0; it < iterations; it = it + 1) {
    let moved = false
    for (let i = 0; i < circles.length; i = i + 1) {
      for (let j = i + 1; j < circles.length; j = j + 1) {
        const a = circles[i]
        const b = circles[j]
        let dx = b.x - a.x
        let dy = b.y - a.y
        let distance = Math.hypot(dx, dy)
        const minimum = a.r + b.r + 1
        if (distance >= minimum) {
          continue
        }
        if (distance < 1e-6) {
          dx = 1
          dy = 0
          distance = 1
        }
        const push = (minimum - distance) / 2
        const share = b.r * b.r / (a.r * a.r + b.r * b.r)
        a.x = a.x - (dx / distance) * push * 2 * share
        a.y = a.y - (dy / distance) * push * 2 * share
        b.x = b.x + (dx / distance) * push * 2 * (1 - share)
        b.y = b.y + (dy / distance) * push * 2 * (1 - share)
        moved = true
      }
    }
    for (let i = 0; i < circles.length; i = i + 1) {
      const c = circles[i]
      c.x = c.x + (c.homeX - c.x) * 0.04
      c.y = c.y + (c.homeY - c.y) * 0.04
      c.x = Math.min(Math.max(c.x, c.r), width - c.r)
      c.y = Math.min(Math.max(c.y, c.r), height - c.r)
    }
    if (moved === false && it > 10) {
      break
    }
  }
  return circles
}


function _renderCartogram(ctx) {
  /*
   * Render a cartogram: area-scaled regions (default) or Dorling circles.
   *
   * :param ctx: Renderer context.
   * :returns: A <g> SVGElement.
   */
  const raw = ctx.raw !== null && ctx.raw !== undefined ? ctx.raw : {}
  const root = svgEl("g", { part: "plot" }, [])

  const regions = (Array.isArray(raw.regions) === true ? raw.regions : [])
    .filter((r) => r !== null && typeof r === "object" && r.id !== undefined && r.id !== null)
  const features = readFeatures(ctx).filter((f) => isAreal(f.geometry) === true)
  if (regions.length === 0 || features.length === 0) {
    return root
  }

  const dorling = ctx.attrs("style", "area") === "dorling"
  const legendAreaW = _legendSpace(ctx)
  const drawW = Math.max(ctx.width - MARGIN * 2 - legendAreaW, 10)
  const drawH = Math.max(ctx.height - MARGIN * 2, 10)
  const frame = geoFrame(featureLines(features), projectionName(ctx), drawW, drawH, 0.03)

  const plot = svgEl("g", { transform: `translate(${MARGIN},${MARGIN})` }, [])
  root.appendChild(plot)

  const lookup = new Map()
  let valueTotal = 0
  for (let i = 0; i < regions.length; i = i + 1) {
    const value = isNumber(regions[i].value) === true && regions[i].value >= 0 ? regions[i].value : null
    lookup.set(String(regions[i].id), { value: value, region: regions[i] })
    if (value !== null) {
      valueTotal = valueTotal + value
    }
  }

  const shapes = features.map((feature) => {
    const entry = lookup.get(feature.key)
    const shape = _featureShape(feature, frame)
    return {
      feature: feature,
      value: entry !== undefined ? entry.value : null,
      label: entry !== undefined && typeof entry.region.label === "string" ? entry.region.label : feature.name,
      color: entry !== undefined && typeof entry.region.color === "string" ? entry.region.color : null,
      area: shape.area,
      centroid: shape.centroid
    }
  })
  const areaTotal = shapes.reduce((s, sh) => s + sh.area, 0)
  const tableRows = shapes.map((sh) => [sh.label, sh.feature.key, sh.value === null ? "" : sh.value,
    sh.value !== null && valueTotal > 0 ? (sh.value / valueTotal) * 100 : "",
    areaTotal > 0 ? (sh.area / areaTotal) * 100 : ""])

  if (dorling === true) {
    /* Circles: total circle area about half the map's area. */
    const k = valueTotal > 0 ? Math.sqrt((0.5 * areaTotal) / (Math.PI * valueTotal)) : 0
    const radiusOf = (value) => k * Math.sqrt(Math.max(value, 0))
    const circles = shapes
      .filter((sh) => sh.value !== null && sh.value > 0 && sh.centroid !== null)
      .map((sh) => ({ shape: sh, r: radiusOf(sh.value), x: sh.centroid.x, y: sh.centroid.y,
        homeX: sh.centroid.x, homeY: sh.centroid.y }))
    _relaxCircles(circles, drawW, drawH)

    /* Faint outlines of the real regions for orientation. */
    drawBaseMap(plot, features, frame)
    const group = svgEl("g", { part: "regions" }, [])
    const labels = svgEl("g", { "aria-hidden": "true", part: "labels" }, [])
    circles.sort((a, b) => b.r - a.r)
    for (let i = 0; i < circles.length; i = i + 1) {
      const c = circles[i]
      const tooltipText = `${c.shape.label}: ${formatNumber(c.shape.value)}`
      const circle = svgEl("circle", {
        cx: c.x.toFixed(2), cy: c.y.toFixed(2), r: c.r.toFixed(2),
        fill: c.shape.color !== null ? c.shape.color : ctx.colorFor(0), "fill-opacity": 0.8,
        stroke: "var(--mj-surface, #ffffff)", "stroke-width": 1,
        part: "region", "aria-label": tooltipText, cursor: "pointer"
      }, [svgEl("title", null, tooltipText)])
      makeInteractive(circle, "mj-chart-select", { id: c.shape.feature.key, label: c.shape.label, value: c.shape.value }, ctx.emit)
      group.appendChild(circle)
      const fontSize = Math.min(c.r * 0.55, 11)
      if (fontSize >= 7 && c.shape.label.length * fontSize * 0.6 < c.r * 2) {
        labels.appendChild(svgEl("text", {
          x: c.x, y: c.y + fontSize * 0.35, "text-anchor": "middle", "font-size": fontSize,
          fill: "var(--mj-color-neutral-0, #ffffff)", "pointer-events": "none"
        }, c.shape.label))
      }
    }
    plot.appendChild(group)
    plot.appendChild(labels)
    if (legendAreaW > 0) {
      const maxValue = Math.max(...circles.map((c) => c.shape.value), 0)
      appendSizeLegend(plot, radiusOf, maxValue, Math.min(frame.bounds.x + frame.bounds.width + 16, drawW + 8), 0,
        typeof ctx.model.meta.valueLabel === "string" ? ctx.model.meta.valueLabel : "")
    }
  } else {
    /*
     * Area cartogram: scale = sqrt(density / densest density), so drawn
     * area = value / densest density -- proportional to value, and no
     * region grows past its own outline.
     */
    let densityMax = 0
    for (let i = 0; i < shapes.length; i = i + 1) {
      if (shapes[i].value !== null && shapes[i].area > 0) {
        densityMax = Math.max(densityMax, shapes[i].value / shapes[i].area)
      }
    }
    const scale = classScale(shapes.map((sh) => sh.value), { classes: raw.classes })
    const ghosts = svgEl("g", { part: "outlines", "aria-hidden": "true" }, [])
    const group = svgEl("g", { part: "regions" }, [])
    for (let i = 0; i < shapes.length; i = i + 1) {
      const sh = shapes[i]
      const pathData = geometryPath(sh.feature.geometry, frame)
      if (pathData === "") {
        continue
      }
      ghosts.appendChild(svgEl("path", {
        d: pathData, fill: "none", stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 0.75,
        "stroke-dasharray": "3,2"
      }, []))
      if (sh.value === null || sh.centroid === null || densityMax <= 0) {
        group.appendChild(svgEl("path", {
          d: pathData, fill: NO_DATA_FILL, stroke: REGION_STROKE, "stroke-width": 0.75,
          part: "region", "aria-label": `${sh.label}: no data`
        }, [svgEl("title", null, `${sh.label}: no data`)]))
        continue
      }
      const factor = Math.sqrt((sh.value / sh.area) / densityMax)
      const cx = sh.centroid.x
      const cy = sh.centroid.y
      const tooltipText = `${sh.label}: ${formatNumber(sh.value)}`
      const path = svgEl("path", {
        d: pathData,
        transform: `translate(${cx.toFixed(2)},${cy.toFixed(2)}) scale(${factor.toFixed(4)}) translate(${(-cx).toFixed(2)},${(-cy).toFixed(2)})`,
        fill: sh.color !== null ? sh.color : scale.colorOf(sh.value),
        stroke: REGION_STROKE, "stroke-width": 0.75 / Math.max(factor, 0.05), "stroke-linejoin": "round",
        part: "region", "aria-label": tooltipText, cursor: "pointer"
      }, [svgEl("title", null, tooltipText)])
      makeInteractive(path, "mj-chart-select", { id: sh.feature.key, label: sh.label, value: sh.value }, ctx.emit)
      group.appendChild(path)
    }
    plot.appendChild(ghosts)
    plot.appendChild(group)
    if (legendAreaW > 0) {
      appendClassLegend(plot, scale, Math.min(frame.bounds.x + frame.bounds.width + 16, drawW + 8), 0,
        typeof ctx.model.meta.valueLabel === "string" ? ctx.model.meta.valueLabel : "",
        shapes.some((sh) => sh.value === null))
    }
  }

  ctx.setTable({ columns: ["Region", "Id", "Value", "Share of total (%)", "Share of map area (%)"], rows: tableRows })
  return root
}


/* ─── dispatch & registration ───────────────────────────────────────────────── */

export function render(ctx) {
  /*
   * Flow/route/density/contour/cartogram dispatcher: the sub-renderer of
   * ctx.type.
   *
   * :param ctx: Renderer context.
   * :returns: A <g> SVGElement.
   */
  const chartType = typeof ctx.type === "string" ? ctx.type : ctx.attrs("type", "flow-map")
  let root = null
  if (chartType === "route-map") {
    root = _renderRouteMap(ctx)
  } else if (chartType === "geo-heatmap") {
    root = _renderGeoHeatmap(ctx)
  } else if (chartType === "isoline") {
    root = _renderIsoline(ctx)
  } else if (chartType === "cartogram") {
    root = _renderCartogram(ctx)
  } else {
    root = _renderFlowMap(ctx)
  }
  return root
}


registerRenderer("flow-map", render, { legend: "none" })
registerRenderer("route-map", render)
registerRenderer("geo-heatmap", render, { legend: "none" })
registerRenderer("isoline", render, { legend: "none" })
registerRenderer("cartogram", render, { legend: "none" })
