/*
 * flowmap.js
 *
 * Geographic flow/route/density/contour/cartogram renderers.
 *
 * Registered types:
 *   "flow-map"    — directed arc flows between geographic nodes
 *   "route-map"   — fixed-path polylines over a base map
 *   "geo-heatmap" — kernel-density colour surface (contour or raster)
 *   "isoline"     — contour lines / filled contour bands from a grid
 *   "cartogram"   — value-distorted region map (Dorling or naive scaling)
 *
 * Renderer contract: export function render(ctx) -> SVGElement
 *   ctx.model       normalized model { meta, categories, series, raw }
 *   ctx.raw         raw data object (geographic fields live here)
 *   ctx.width       drawing surface width  (px)
 *   ctx.height      drawing surface height (px)
 *   ctx.orientation n/a for maps
 *   ctx.attrs       (name, fallback) -> controller attribute value
 *   ctx.colorFor    (seriesIndex | seriesName) -> CSS color
 *   ctx.emit        (eventName, detail) -> dispatch an interaction event
 *
 * Geographic data shapes (from ctx.raw):
 *   flow-map:
 *     raw.nodes  [{id, lon, lat, label?}]
 *     raw.links  [{source, target, value?}]
 *     raw.geojson  GeoJSON FeatureCollection (base map, optional)
 *
 *   route-map:
 *     raw.series  [{name, routes:[{id, waypoints:[{lon,lat}]}]}]
 *     raw.geojson  GeoJSON FeatureCollection (base map, optional)
 *
 *   geo-heatmap:
 *     raw.series  [{name, points:[{lon,lat,weight?}]}]
 *     raw.geojson  GeoJSON FeatureCollection (base map, optional)
 *
 *   isoline:
 *     raw.series  [{name, grid:{lon-min,lon-max,lat-min,lat-max,cols,rows,values[]}, levels:[]}]
 *     raw.geojson  GeoJSON FeatureCollection (base map, optional)
 *
 *   cartogram:
 *     raw.regions  [{id, value, color?}]
 *     raw.geojson  GeoJSON FeatureCollection of polygons (required for distortion)
 *
 * GeoJSON polygons are projected with an equirectangular projection computed
 * from the bounding box of all coordinates in the FeatureCollection.
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, formatNumber } from "../svgdraw.js";
import { linearScale, sqrtScale, niceTicks } from "../scales.js";


/* ─── constants ─────────────────────────────────────────────────────────────── */

const MARGIN = 12
const LEGEND_W = 110
const LEGEND_SWATCH_SIZE = 12
const BASE_MAP_FILL = "var(--mj-surface-2, #f3f4f6)"
const BASE_MAP_STROKE = "var(--mj-border, #e0e3e9)"
const NO_DATA_FILL = "var(--mj-chart-geo-no-data, #e5e7eb)"
const REGION_STROKE = "var(--mj-border, #e0e3e9)"

/* Sequential heatmap ramp: transparent → accent colours */
const HEAT_RAMP = [
  "rgba(37,99,235,0.0)",
  "rgba(37,99,235,0.15)",
  "rgba(37,99,235,0.35)",
  "rgba(59,130,246,0.55)",
  "rgba(239,68,68,0.70)",
  "rgba(239,68,68,0.90)"
]

/* Sequential ramp for isolines / cartogram fills. */
const SEQ_RAMP = [
  "var(--mj-color-accent-100, #dbeafe)",
  "var(--mj-color-accent-200, #bfdbfe)",
  "var(--mj-color-accent-300, #80a8ff)",
  "var(--mj-color-accent-400, #3b82f6)",
  "var(--mj-color-accent-500, #2563eb)",
  "var(--mj-color-accent-800, #122f78)"
]


/* ─── shared projection helpers ─────────────────────────────────────────────── */

function _geoJsonBounds(geojson) {
  /*
   * Compute [lonMin, lonMax, latMin, latMax] over all coordinates in a
   * GeoJSON FeatureCollection.
   */
  let lonMin = Infinity
  let lonMax = -Infinity
  let latMin = Infinity
  let latMax = -Infinity

  const visitCoords = (coords) => {
    if (coords === null || coords === undefined) { return }
    if (typeof coords[0] === "number") {
      const lon = coords[0]
      const lat = coords[1]
      if (lon < lonMin) { lonMin = lon }
      if (lon > lonMax) { lonMax = lon }
      if (lat < latMin) { latMin = lat }
      if (lat > latMax) { latMax = lat }
      return
    }
    for (let i = 0; i < coords.length; i = i + 1) {
      visitCoords(coords[i])
    }
  }

  const features = (geojson && geojson.features) ? geojson.features : []
  for (let fi = 0; fi < features.length; fi = fi + 1) {
    const geometry = features[fi].geometry
    if (geometry === null || geometry === undefined) { continue }
    visitCoords(geometry.coordinates)
  }
  if (lonMin === Infinity) { return [-180, 180, -90, 90] }
  return [lonMin, lonMax, latMin, latMax]
}


function _makeProjection(geojson, drawW, drawH) {
  /*
   * Build an equirectangular projection for the given GeoJSON, fitting
   * uniformly within [0..drawW] x [0..drawH].
   *
   * :returns: A function (lon, lat) -> {x, y}.
   */
  const bounds = _geoJsonBounds(geojson)
  const lonMin = bounds[0]; const lonMax = bounds[1]
  const latMin = bounds[2]; const latMax = bounds[3]
  const lonSpan = (lonMax - lonMin) || 1
  const latSpan = (latMax - latMin) || 1
  const scaleX = drawW / lonSpan
  const scaleY = drawH / latSpan
  const scale = Math.min(scaleX, scaleY) * 0.94
  const cx = drawW / 2
  const cy = drawH / 2
  const midLon = (lonMin + lonMax) / 2
  const midLat = (latMin + latMax) / 2

  const project = (lon, lat) => {
    const x = cx + (lon - midLon) * scale
    const y = cy - (lat - midLat) * scale
    return { x: x, y: y }
  }
  return project
}


function _pointsProjection(lons, lats, drawW, drawH) {
  /*
   * Build a projection fitted to an explicit set of lon/lat bounds.
   *
   * :param lons: Array of longitudes.
   * :param lats: Array of latitudes.
   */
  let lonMin = Infinity; let lonMax = -Infinity
  let latMin = Infinity; let latMax = -Infinity
  for (let i = 0; i < lons.length; i = i + 1) {
    if (lons[i] < lonMin) { lonMin = lons[i] }
    if (lons[i] > lonMax) { lonMax = lons[i] }
  }
  for (let i = 0; i < lats.length; i = i + 1) {
    if (lats[i] < latMin) { latMin = lats[i] }
    if (lats[i] > latMax) { latMax = lats[i] }
  }
  if (lonMin === Infinity) { lonMin = -180; lonMax = 180; latMin = -90; latMax = 90 }

  const lonPad = Math.max((lonMax - lonMin) * 0.12, 1)
  const latPad = Math.max((latMax - latMin) * 0.12, 1)

  const fakeGeoJson = {
    features: [{
      geometry: {
        coordinates: [[
          [lonMin - lonPad, latMin - latPad],
          [lonMax + lonPad, latMin - latPad],
          [lonMax + lonPad, latMax + latPad],
          [lonMin - lonPad, latMax + latPad]
        ]]
      }
    }]
  }
  return _makeProjection(fakeGeoJson, drawW, drawH)
}


/* ─── base map layer ────────────────────────────────────────────────────────── */

function _drawBaseMap(plot, geojson, project) {
  /*
   * Draw GeoJSON polygon features as a grey base map layer.
   */
  if (geojson === null || geojson === undefined) { return }
  const features = geojson.features || []
  for (let fi = 0; fi < features.length; fi = fi + 1) {
    const geometry = features[fi].geometry
    if (geometry === null || geometry === undefined) { continue }
    const data = _featureToPathData(features[fi], project)
    if (data === "") { continue }
    plot.appendChild(svgEl("path", {
      d: data,
      fill: BASE_MAP_FILL,
      stroke: BASE_MAP_STROKE,
      "stroke-width": 0.5,
      "stroke-linejoin": "round"
    }, []))
  }
}


function _ringToPathSegment(ring, project) {
  let data = ""
  for (let i = 0; i < ring.length; i = i + 1) {
    const pt = project(ring[i][0], ring[i][1])
    data = data + `${i === 0 ? "M" : "L"}${pt.x.toFixed(2)},${pt.y.toFixed(2)} `
  }
  return data + "Z"
}


function _featureToPathData(feature, project) {
  const geometry = feature.geometry
  if (geometry === null || geometry === undefined) { return "" }
  const segments = []
  if (geometry.type === "Polygon") {
    for (let ri = 0; ri < geometry.coordinates.length; ri = ri + 1) {
      segments.push(_ringToPathSegment(geometry.coordinates[ri], project))
    }
  } else if (geometry.type === "MultiPolygon") {
    for (let pi = 0; pi < geometry.coordinates.length; pi = pi + 1) {
      for (let ri = 0; ri < geometry.coordinates[pi].length; ri = ri + 1) {
        segments.push(_ringToPathSegment(geometry.coordinates[pi][ri], project))
      }
    }
  }
  return segments.join(" ")
}


/* ─── interaction helper ────────────────────────────────────────────────────── */

function _makeInteractive(element, eventName, detail, emit) {
  /*
   * Attach accessibility attributes and keyboard/click interaction.
   */
  element.setAttribute("tabindex", "0")
  element.setAttribute("role", "img")
  const handler = () => { emit(eventName, detail) }
  element.addEventListener("click", handler)
  element.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault()
      handler()
    }
  })
}


/* ─── legend ────────────────────────────────────────────────────────────────── */

function _appendSeriesLegend(parent, seriesNames, colors, x, y) {
  const rowH = LEGEND_SWATCH_SIZE + 4
  for (let i = 0; i < seriesNames.length; i = i + 1) {
    const sy = y + i * rowH
    parent.appendChild(svgEl("rect", {
      x: x, y: sy,
      width: LEGEND_SWATCH_SIZE, height: LEGEND_SWATCH_SIZE,
      fill: colors[i], rx: 2
    }, []))
    parent.appendChild(svgEl("text", {
      x: x + LEGEND_SWATCH_SIZE + 4,
      y: sy + LEGEND_SWATCH_SIZE - 2,
      "font-size": 10,
      fill: "var(--mj-text-muted, #6b7280)"
    }, escapeHtml(seriesNames[i])))
  }
}


function _appendRampLegend(parent, labelMin, labelMax, ramp, x, y) {
  const steps = 6
  const swatchH = LEGEND_SWATCH_SIZE + 2
  const palette = ramp || HEAT_RAMP
  for (let step = 0; step < steps; step = step + 1) {
    const t = (steps - 1 - step) / (steps - 1)
    const colorIndex = Math.min(Math.floor(t * (palette.length - 1)), palette.length - 1)
    const color = palette[colorIndex]
    const sy = y + step * swatchH
    parent.appendChild(svgEl("rect", {
      x: x, y: sy,
      width: LEGEND_SWATCH_SIZE, height: LEGEND_SWATCH_SIZE,
      fill: color,
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 0.5
    }, []))
    if (step === 0 || step === steps - 1) {
      const labelVal = step === 0 ? labelMax : labelMin
      parent.appendChild(svgEl("text", {
        x: x + LEGEND_SWATCH_SIZE + 4,
        y: sy + LEGEND_SWATCH_SIZE - 2,
        "font-size": 10,
        fill: "var(--mj-text-muted, #6b7280)"
      }, formatNumber(labelVal)))
    }
  }
}


/* ─── flow-map renderer ─────────────────────────────────────────────────────── */

function _cubicArcPath(x1, y1, x2, y2, curvature) {
  /*
   * Build a cubic-Bézier arc from (x1, y1) to (x2, y2).  The control points
   * are offset perpendicular to the midpoint by `curvature` fraction of the
   * chord length, choosing a consistent side.
   *
   * :param curvature: Signed perpendicular offset fraction (e.g. 0.3).
   * :returns: SVG path data string.
   */
  const mx = (x1 + x2) / 2
  const my = (y1 + y2) / 2
  const dx = x2 - x1
  const dy = y2 - y1
  const len = Math.sqrt(dx * dx + dy * dy) || 1
  const nx = -dy / len
  const ny = dx / len
  const offset = len * curvature
  const cx1 = mx + nx * offset
  const cy1 = my + ny * offset
  const data = `M${x1.toFixed(2)},${y1.toFixed(2)} C${cx1.toFixed(2)},${cy1.toFixed(2)} ${cx1.toFixed(2)},${cy1.toFixed(2)} ${x2.toFixed(2)},${y2.toFixed(2)}`
  return data
}


function _arrowheadPoints(tx, ty, sx, sy, size) {
  /*
   * Compute SVG polygon points for a small arrowhead pointing from (sx,sy)
   * toward (tx,ty).
   *
   * :returns: SVG polygon points string.
   */
  const dx = tx - sx
  const dy = ty - sy
  const len = Math.sqrt(dx * dx + dy * dy) || 1
  const ux = dx / len
  const uy = dy / len
  const px = -uy
  const py = ux
  const bx = tx - ux * size
  const by = ty - uy * size
  const p1x = bx + px * size * 0.4
  const p1y = by + py * size * 0.4
  const p2x = bx - px * size * 0.4
  const p2y = by - py * size * 0.4
  return `${tx.toFixed(2)},${ty.toFixed(2)} ${p1x.toFixed(2)},${p1y.toFixed(2)} ${p2x.toFixed(2)},${p2y.toFixed(2)}`
}


function _renderFlowMap(ctx) {
  /*
   * Render a flow-map: curved arcs between geographic node pairs, optionally
   * tapered by value.
   *
   * :param ctx: Renderer context.
   * :returns: A <g> SVGElement.
   */
  const raw = ctx.raw
  const root = svgEl("g", { part: "plot" }, [])

  const nodes = (raw && Array.isArray(raw.nodes)) ? raw.nodes : []
  const links = (raw && Array.isArray(raw.links)) ? raw.links : []
  const geojson = (raw && raw.geojson) ? raw.geojson : null

  if (nodes.length === 0 && links.length === 0) {
    return root
  }

  const drawW = Math.max(ctx.width - MARGIN * 2 - LEGEND_W, 10)
  const drawH = Math.max(ctx.height - MARGIN * 2, 10)

  /* Project from node lon/lat bounds when no base map geojson. */
  let project = null
  if (geojson !== null) {
    project = _makeProjection(geojson, drawW, drawH)
  } else {
    const lons = nodes.map((n) => n.lon || 0)
    const lats = nodes.map((n) => n.lat || 0)
    project = _pointsProjection(lons, lats, drawW, drawH)
  }

  const plot = svgEl("g", { transform: `translate(${MARGIN},${MARGIN})` }, [])
  root.appendChild(plot)

  _drawBaseMap(plot, geojson, project)

  /* Build node pixel-position lookup. */
  const nodePos = {}
  for (let ni = 0; ni < nodes.length; ni = ni + 1) {
    const node = nodes[ni]
    const pt = project(node.lon || 0, node.lat || 0)
    nodePos[node.id] = { x: pt.x, y: pt.y, label: node.label || node.id }
  }

  /* Value scale for stroke width. */
  const arcMode = ctx.attrs("arc", "curve")
  const taperMode = ctx.attrs("taper", "true")

  let valMin = Infinity
  let valMax = -Infinity
  for (let li = 0; li < links.length; li = li + 1) {
    const v = links[li].value
    if (typeof v === "number") {
      if (v < valMin) { valMin = v }
      if (v > valMax) { valMax = v }
    }
  }
  if (valMin === Infinity) { valMin = 1; valMax = 1 }
  if (valMin === valMax) { valMax = valMin + 1 }
  const strokeScale = linearScale([valMin, valMax], [1, 6])

  /* Draw arcs. */
  for (let li = 0; li < links.length; li = li + 1) {
    const link = links[li]
    const src = nodePos[link.source]
    const tgt = nodePos[link.target]
    if (src === undefined || tgt === undefined) { continue }

    const value = typeof link.value === "number" ? link.value : 1
    const strokeW = taperMode === "true" ? strokeScale(value) : 2
    const color = ctx.colorFor(0)
    const tooltipText = `${src.label} → ${tgt.label}: ${formatNumber(value)}`

    let pathData = ""
    if (arcMode === "straight") {
      pathData = `M${src.x.toFixed(2)},${src.y.toFixed(2)} L${tgt.x.toFixed(2)},${tgt.y.toFixed(2)}`
    } else {
      /* Alternate curvature sign per link index to spread bidirectional pairs. */
      const curvature = (li % 2 === 0) ? 0.3 : -0.3
      pathData = _cubicArcPath(src.x, src.y, tgt.x, tgt.y, curvature)
    }

    const arc = svgEl("path", {
      d: pathData,
      fill: "none",
      stroke: color,
      "stroke-width": strokeW,
      "stroke-opacity": 0.65,
      "stroke-linecap": "round",
      part: "flow",
      "aria-label": tooltipText,
      cursor: "pointer"
    }, [svgEl("title", null, tooltipText)])

    _makeInteractive(arc, "mj-chart-select", {
      source: link.source, target: link.target, value: value
    }, ctx.emit)
    plot.appendChild(arc)

    /* Arrowhead near destination. */
    const arrowPts = _arrowheadPoints(tgt.x, tgt.y, src.x, src.y, 6)
    plot.appendChild(svgEl("polygon", {
      points: arrowPts,
      fill: color,
      "fill-opacity": 0.75
    }, []))
  }

  /* Node circles. */
  for (let ni = 0; ni < nodes.length; ni = ni + 1) {
    const node = nodes[ni]
    const pos = nodePos[node.id]
    if (pos === undefined) { continue }

    const circle = svgEl("circle", {
      cx: pos.x, cy: pos.y, r: 4,
      fill: ctx.colorFor(0),
      stroke: "var(--mj-surface, #ffffff)", "stroke-width": 1.5,
      part: "node",
      "aria-label": pos.label,
      cursor: "pointer"
    }, [svgEl("title", null, pos.label)])

    _makeInteractive(circle, "mj-chart-select", {
      id: node.id, label: pos.label
    }, ctx.emit)
    plot.appendChild(circle)

    if (ctx.attrs("show-labels", "false") === "true") {
      plot.appendChild(svgEl("text", {
        x: pos.x, y: pos.y - 6,
        "text-anchor": "middle",
        "font-size": 9,
        fill: "var(--mj-text, #14181f)"
      }, escapeHtml(pos.label)))
    }
  }

  /* Legend. */
  _appendRampLegend(plot, valMin, valMax, null, drawW + 4, 0)

  return root
}


/* ─── route-map renderer ────────────────────────────────────────────────────── */

function _renderRouteMap(ctx) {
  /*
   * Render a route-map: ordered polylines along waypoint sequences.
   *
   * :param ctx: Renderer context.
   * :returns: A <g> SVGElement.
   */
  const raw = ctx.raw
  const root = svgEl("g", { part: "plot" }, [])

  const seriesData = (raw && Array.isArray(raw.series)) ? raw.series : []
  const geojson = (raw && raw.geojson) ? raw.geojson : null

  if (seriesData.length === 0) {
    return root
  }

  const drawW = Math.max(ctx.width - MARGIN * 2 - LEGEND_W, 10)
  const drawH = Math.max(ctx.height - MARGIN * 2, 10)

  /* Collect all waypoint coords to build projection when no geojson. */
  const allLons = []
  const allLats = []
  for (let si = 0; si < seriesData.length; si = si + 1) {
    const routes = seriesData[si].routes || []
    for (let ri = 0; ri < routes.length; ri = ri + 1) {
      const waypoints = routes[ri].waypoints || []
      for (let wi = 0; wi < waypoints.length; wi = wi + 1) {
        allLons.push(waypoints[wi].lon)
        allLats.push(waypoints[wi].lat)
      }
    }
  }

  const project = geojson !== null
    ? _makeProjection(geojson, drawW, drawH)
    : _pointsProjection(allLons, allLats, drawW, drawH)

  const plot = svgEl("g", { transform: `translate(${MARGIN},${MARGIN})` }, [])
  root.appendChild(plot)

  _drawBaseMap(plot, geojson, project)

  const showStops = ctx.attrs("show-stops", "false") === "true"
  const styleAttr = ctx.attrs("style", "polyline")

  const seriesNames = []
  const seriesColors = []

  for (let si = 0; si < seriesData.length; si = si + 1) {
    const series = seriesData[si]
    const color = ctx.colorFor(si)
    seriesNames.push(series.name || `Route ${si + 1}`)
    seriesColors.push(color)

    const routes = series.routes || []
    for (let ri = 0; ri < routes.length; ri = ri + 1) {
      const route = routes[ri]
      const waypoints = route.waypoints || []
      if (waypoints.length < 2) { continue }

      const projected = waypoints.map((wp) => project(wp.lon, wp.lat))

      let pathData = ""
      if (styleAttr === "great-circle") {
        /* Simple great-circle interpolation: subdivide each segment. */
        const gcPoints = []
        for (let wi = 0; wi < waypoints.length - 1; wi = wi + 1) {
          const lon1 = waypoints[wi].lon
          const lat1 = waypoints[wi].lat
          const lon2 = waypoints[wi + 1].lon
          const lat2 = waypoints[wi + 1].lat
          const steps = 12
          for (let step = 0; step <= steps; step = step + 1) {
            const t = step / steps
            const lon = lon1 + (lon2 - lon1) * t
            const lat = lat1 + (lat2 - lat1) * t
            gcPoints.push(project(lon, lat))
          }
        }
        let gcData = ""
        for (let pi = 0; pi < gcPoints.length; pi = pi + 1) {
          gcData = gcData + `${pi === 0 ? "M" : "L"}${gcPoints[pi].x.toFixed(2)},${gcPoints[pi].y.toFixed(2)} `
        }
        pathData = gcData.trim()
      } else {
        let polyData = ""
        for (let pi = 0; pi < projected.length; pi = pi + 1) {
          polyData = polyData + `${pi === 0 ? "M" : "L"}${projected[pi].x.toFixed(2)},${projected[pi].y.toFixed(2)} `
        }
        pathData = polyData.trim()
      }

      const routeLabel = route.id || `${series.name || "Route"} ${ri + 1}`
      const tooltipText = routeLabel

      const routePath = svgEl("path", {
        d: pathData,
        fill: "none",
        stroke: color,
        "stroke-width": 2,
        "stroke-opacity": 0.8,
        "stroke-linecap": "round",
        "stroke-linejoin": "round",
        part: "route",
        "aria-label": tooltipText,
        cursor: "pointer"
      }, [svgEl("title", null, tooltipText)])

      _makeInteractive(routePath, "mj-chart-select", {
        id: route.id, series: series.name
      }, ctx.emit)
      plot.appendChild(routePath)

      /* Stop markers at waypoints. */
      if (showStops === true) {
        for (let wi = 0; wi < projected.length; wi = wi + 1) {
          const wp = waypoints[wi]
          const stopLabel = wp.label || `Stop ${wi + 1}`
          const circle = svgEl("circle", {
            cx: projected[wi].x, cy: projected[wi].y, r: 3,
            fill: color,
            stroke: "var(--mj-surface, #ffffff)", "stroke-width": 1,
            part: "stop",
            "aria-label": stopLabel,
            cursor: "pointer"
          }, [svgEl("title", null, stopLabel)])

          _makeInteractive(circle, "mj-chart-select", {
            routeId: route.id, waypointIndex: wi, label: stopLabel
          }, ctx.emit)
          plot.appendChild(circle)
        }
      }
    }
  }

  /* Legend. */
  _appendSeriesLegend(plot, seriesNames, seriesColors, drawW + 4, 0)

  return root
}


/* ─── geo-heatmap renderer ──────────────────────────────────────────────────── */

function _gaussianKernel(distance, bandwidth) {
  /*
   * Evaluate a Gaussian kernel.
   *
   * :param distance: Distance from the centre (pixels).
   * :param bandwidth: Kernel bandwidth (pixels).
   * :returns: Kernel weight.
   */
  const z = distance / bandwidth
  const weight = Math.exp(-0.5 * z * z)
  return weight
}


function _renderGeoHeatmap(ctx) {
  /*
   * Render a geographic heatmap via a canvas-rasterised Gaussian kernel
   * density estimate.  Falls back to contour bands when OffscreenCanvas is
   * unavailable.
   *
   * :param ctx: Renderer context.
   * :returns: A <g> SVGElement.
   */
  const raw = ctx.raw
  const root = svgEl("g", { part: "plot" }, [])

  const seriesData = (raw && Array.isArray(raw.series)) ? raw.series : []
  const geojson = (raw && raw.geojson) ? raw.geojson : null

  if (seriesData.length === 0) {
    return root
  }

  const drawW = Math.max(ctx.width - MARGIN * 2 - LEGEND_W, 10)
  const drawH = Math.max(ctx.height - MARGIN * 2, 10)

  /* Collect all point coords. */
  const allLons = []
  const allLats = []
  for (let si = 0; si < seriesData.length; si = si + 1) {
    const pts = seriesData[si].points || []
    for (let pi = 0; pi < pts.length; pi = pi + 1) {
      allLons.push(pts[pi].lon)
      allLats.push(pts[pi].lat)
    }
  }

  const project = geojson !== null
    ? _makeProjection(geojson, drawW, drawH)
    : _pointsProjection(allLons, allLats, drawW, drawH)

  const plot = svgEl("g", { transform: `translate(${MARGIN},${MARGIN})` }, [])
  root.appendChild(plot)

  _drawBaseMap(plot, geojson, project)

  const bwAttr = Number(ctx.attrs("bandwidth", "30"))
  const kernelBw = bwAttr > 0 ? bwAttr : 30
  const renderMode = ctx.attrs("render-mode", "raster")

  /* Collect projected points with weights. */
  const points = []
  for (let si = 0; si < seriesData.length; si = si + 1) {
    const pts = seriesData[si].points || []
    for (let pi = 0; pi < pts.length; pi = pi + 1) {
      const pt = pts[pi]
      const projected = project(pt.lon, pt.lat)
      const weight = typeof pt.weight === "number" ? pt.weight : 1
      points.push({ x: projected.x, y: projected.y, weight: weight })
    }
  }

  if (points.length === 0) {
    return root
  }

  /* Build pixel density grid (low resolution for performance). */
  const gridCols = Math.max(Math.round(drawW / 4), 2)
  const gridRows = Math.max(Math.round(drawH / 4), 2)
  const cellW = drawW / gridCols
  const cellH = drawH / gridRows
  const density = new Float32Array(gridCols * gridRows)

  for (let pi = 0; pi < points.length; pi = pi + 1) {
    const point = points[pi]
    const colCenter = Math.floor(point.x / cellW)
    const rowCenter = Math.floor(point.y / cellH)
    const searchR = Math.ceil(kernelBw / Math.min(cellW, cellH)) + 1

    const colStart = Math.max(colCenter - searchR, 0)
    const colEnd = Math.min(colCenter + searchR, gridCols - 1)
    const rowStart = Math.max(rowCenter - searchR, 0)
    const rowEnd = Math.min(rowCenter + searchR, gridRows - 1)

    for (let row = rowStart; row <= rowEnd; row = row + 1) {
      for (let col = colStart; col <= colEnd; col = col + 1) {
        const cellX = (col + 0.5) * cellW
        const cellY = (row + 0.5) * cellH
        const dx = cellX - point.x
        const dy = cellY - point.y
        const dist = Math.sqrt(dx * dx + dy * dy)
        const kv = _gaussianKernel(dist, kernelBw)
        density[row * gridCols + col] = density[row * gridCols + col] + kv * point.weight
      }
    }
  }

  let densityMax = 0
  for (let i = 0; i < density.length; i = i + 1) {
    if (density[i] > densityMax) { densityMax = density[i] }
  }
  if (densityMax === 0) { densityMax = 1 }

  if (renderMode === "raster" && typeof OffscreenCanvas !== "undefined") {
    /* Raster path: write RGBA data to an OffscreenCanvas and embed as SVG <image>. */
    const canvas = new OffscreenCanvas(gridCols, gridRows)
    const imageCtx = canvas.getContext("2d")
    const imageData = imageCtx.createImageData(gridCols, gridRows)
    const rampColors = [
      [37, 99, 235, 0],
      [37, 99, 235, 38],
      [37, 99, 235, 89],
      [59, 130, 246, 140],
      [239, 68, 68, 178],
      [239, 68, 68, 230]
    ]

    for (let i = 0; i < density.length; i = i + 1) {
      const t = density[i] / densityMax
      const fi = t * (rampColors.length - 1)
      const lo = Math.floor(fi)
      const hi = Math.min(lo + 1, rampColors.length - 1)
      const blend = fi - lo
      const r = Math.round(rampColors[lo][0] * (1 - blend) + rampColors[hi][0] * blend)
      const g = Math.round(rampColors[lo][1] * (1 - blend) + rampColors[hi][1] * blend)
      const b = Math.round(rampColors[lo][2] * (1 - blend) + rampColors[hi][2] * blend)
      const a = Math.round(rampColors[lo][3] * (1 - blend) + rampColors[hi][3] * blend)
      const base = i * 4
      imageData.data[base] = r
      imageData.data[base + 1] = g
      imageData.data[base + 2] = b
      imageData.data[base + 3] = a
    }
    imageCtx.putImageData(imageData, 0, 0)

    const blob = canvas.convertToBlob({ type: "image/png" })
    blob.then((b) => {
      const reader = new FileReader()
      reader.onload = () => {
        const img = svgEl("image", {
          x: 0, y: 0, width: drawW, height: drawH,
          href: reader.result,
          "image-rendering": "pixelated"
        }, [])
        plot.insertBefore(img, plot.firstChild ? plot.firstChild.nextSibling : null)
      }
      reader.readAsDataURL(b)
    })
  } else {
    /* Contour fallback: draw SVG rect cells with alpha fill. */
    for (let row = 0; row < gridRows; row = row + 1) {
      for (let col = 0; col < gridCols; col = col + 1) {
        const t = density[row * gridCols + col] / densityMax
        if (t < 0.05) { continue }
        const alpha = t * 0.75
        plot.appendChild(svgEl("rect", {
          x: col * cellW, y: row * cellH,
          width: cellW + 0.5, height: cellH + 0.5,
          fill: `rgba(37,99,235,${alpha.toFixed(3)})`,
          "stroke-width": 0
        }, []))
      }
    }
  }

  /* Legend. */
  _appendRampLegend(plot, 0, 1, HEAT_RAMP, drawW + 4, 0)

  return root
}


/* ─── isoline renderer ──────────────────────────────────────────────────────── */

function _marchingSquares(grid, cols, rows, level) {
  /*
   * Trace contour segments at `level` through a scalar grid using the
   * marching-squares algorithm.
   *
   * :param grid:  Float32Array of length cols*rows, row-major.
   * :param cols:  Grid width.
   * :param rows:  Grid height.
   * :param level: The iso-value.
   * :returns: Array of polylines, each a [{x, y}] array in grid-cell space.
   */
  const segments = []

  const lerp = (a, b, t) => a + (b - a) * t
  const isoX = (val1, val2, x1, x2) => {
    if (Math.abs(val2 - val1) < 1e-12) { return (x1 + x2) / 2 }
    return lerp(x1, x2, (level - val1) / (val2 - val1))
  }

  const at = (col, row) => grid[row * cols + col]

  for (let row = 0; row < rows - 1; row = row + 1) {
    for (let col = 0; col < cols - 1; col = col + 1) {
      const v00 = at(col, row)
      const v10 = at(col + 1, row)
      const v01 = at(col, row + 1)
      const v11 = at(col + 1, row + 1)

      const idx = ((v00 >= level) ? 1 : 0) |
                  ((v10 >= level) ? 2 : 0) |
                  ((v11 >= level) ? 4 : 0) |
                  ((v01 >= level) ? 8 : 0)

      if (idx === 0 || idx === 15) { continue }

      /* Midpoints on each cell edge. */
      const top    = { x: isoX(v00, v10, col, col + 1), y: row }
      const right  = { x: col + 1, y: isoX(v10, v11, row, row + 1) }
      const bottom = { x: isoX(v01, v11, col, col + 1), y: row + 1 }
      const left   = { x: col, y: isoX(v00, v01, row, row + 1) }

      /* Lookup table: each entry is pairs of edge points for segments. */
      const table = {
        1:  [[top,    left]],
        2:  [[top,    right]],
        3:  [[left,   right]],
        4:  [[bottom, right]],
        5:  [[top,    right], [bottom, left]],
        6:  [[top,    bottom]],
        7:  [[left,   bottom]],
        8:  [[bottom, left]],
        9:  [[top,    bottom]],
        10: [[top,    left], [bottom, right]],
        11: [[bottom, right]],
        12: [[left,   right]],
        13: [[top,    right]],
        14: [[top,    left]],
      }

      const segs = table[idx]
      if (segs === undefined) { continue }
      for (let si = 0; si < segs.length; si = si + 1) {
        segments.push([segs[si][0], segs[si][1]])
      }
    }
  }
  return segments
}


function _renderIsoline(ctx) {
  /*
   * Render an isoline / contour map from a scalar grid or pre-computed GeoJSON.
   *
   * :param ctx: Renderer context.
   * :returns: A <g> SVGElement.
   */
  const raw = ctx.raw
  const root = svgEl("g", { part: "plot" }, [])

  const seriesData = (raw && Array.isArray(raw.series)) ? raw.series : []
  const geojson = (raw && raw.geojson) ? raw.geojson : null

  if (seriesData.length === 0) {
    return root
  }

  const drawW = Math.max(ctx.width - MARGIN * 2 - LEGEND_W, 10)
  const drawH = Math.max(ctx.height - MARGIN * 2, 10)

  const project = geojson !== null
    ? _makeProjection(geojson, drawW, drawH)
    : null

  const plot = svgEl("g", { transform: `translate(${MARGIN},${MARGIN})` }, [])
  root.appendChild(plot)

  _drawBaseMap(plot, geojson, project || ((lon, lat) => ({ x: lon, y: lat })))

  const styleAttr = ctx.attrs("style", "lines")
  const seriesNames = []
  const seriesColors = []

  for (let si = 0; si < seriesData.length; si = si + 1) {
    const series = seriesData[si]
    const gridDef = series.grid
    const levels = Array.isArray(series.levels) ? series.levels : []
    const color = ctx.colorFor(si)
    seriesNames.push(series.name || `Series ${si + 1}`)
    seriesColors.push(color)

    if (gridDef === undefined || gridDef === null) { continue }
    if (levels.length === 0) { continue }

    const lonMin = gridDef["lon-min"] || 0
    const lonMax = gridDef["lon-max"] || 1
    const latMin = gridDef["lat-min"] || 0
    const latMax = gridDef["lat-max"] || 1
    const cols = gridDef.cols || 2
    const rows = gridDef.rows || 2
    const values = Array.isArray(gridDef.values) ? gridDef.values : []

    if (values.length < cols * rows) { continue }

    /* Build Float32Array grid. */
    const grid = new Float32Array(cols * rows)
    for (let i = 0; i < cols * rows; i = i + 1) {
      const v = values[i]
      grid[i] = typeof v === "number" ? v : 0
    }

    /* Map grid-cell coordinates to pixel (lon/lat then project). */
    const cellProject = (gridX, gridY) => {
      const lon = lonMin + (gridX / (cols - 1)) * (lonMax - lonMin)
      const lat = latMin + (gridY / (rows - 1)) * (latMax - latMin)
      if (project !== null) {
        return project(lon, lat)
      }
      /* No base map: use pixel space directly. */
      const x = (lon - lonMin) / (lonMax - lonMin) * drawW
      const y = (1 - (lat - latMin) / (latMax - latMin)) * drawH
      return { x: x, y: y }
    }

    /* Compute contour level color scale. */
    const levelCount = levels.length
    const levelScale = linearScale([0, levelCount - 1], [0, 1])

    for (let li = 0; li < levels.length; li = li + 1) {
      const level = levels[li]
      const segments = _marchingSquares(grid, cols, rows, level)
      const t = levelCount > 1 ? levelScale(li) : 1
      const colorIndex = Math.min(Math.floor(t * (SEQ_RAMP.length - 1)), SEQ_RAMP.length - 1)
      const levelColor = styleAttr === "filled" ? SEQ_RAMP[colorIndex] : color
      const levelOpacity = styleAttr === "filled" ? 0.55 : 0.9

      for (let segi = 0; segi < segments.length; segi = segi + 1) {
        const seg = segments[segi]
        const p1 = cellProject(seg[0].x, seg[0].y)
        const p2 = cellProject(seg[1].x, seg[1].y)

        const line = svgEl("line", {
          x1: p1.x.toFixed(2), y1: p1.y.toFixed(2),
          x2: p2.x.toFixed(2), y2: p2.y.toFixed(2),
          stroke: levelColor,
          "stroke-width": styleAttr === "filled" ? 0.5 : 1.2,
          "stroke-opacity": levelOpacity
        }, [])
        plot.appendChild(line)
      }

      /* Level label: place at the first segment midpoint. */
      if (segments.length > 0) {
        const seg0 = segments[0]
        const pm1 = cellProject(seg0[0].x, seg0[0].y)
        const pm2 = cellProject(seg0[1].x, seg0[1].y)
        const mx = (pm1.x + pm2.x) / 2
        const my = (pm1.y + pm2.y) / 2
        const dx = pm2.x - pm1.x
        const dy = pm2.y - pm1.y
        const angle = Math.atan2(dy, dx) * 180 / Math.PI

        plot.appendChild(svgEl("text", {
          x: mx, y: my,
          transform: `rotate(${angle.toFixed(1)},${mx.toFixed(1)},${my.toFixed(1)})`,
          "text-anchor": "middle",
          "font-size": 8,
          fill: levelColor,
          "paint-order": "stroke",
          stroke: "var(--mj-surface, #ffffff)",
          "stroke-width": 2
        }, formatNumber(level)))
      }
    }
  }

  /* Legend. */
  _appendSeriesLegend(plot, seriesNames, seriesColors, drawW + 4, 0)

  return root
}


/* ─── cartogram renderer ────────────────────────────────────────────────────── */

function _featureCentroid(feature) {
  /*
   * Compute the approximate centroid of a GeoJSON Polygon or MultiPolygon
   * feature by averaging the outer ring coordinates.
   *
   * :returns: { lon, lat } in geographic coordinates.
   */
  const geometry = feature.geometry
  if (geometry === null || geometry === undefined) {
    return { lon: 0, lat: 0 }
  }

  let ring = null
  if (geometry.type === "Polygon" && geometry.coordinates.length > 0) {
    ring = geometry.coordinates[0]
  } else if (geometry.type === "MultiPolygon" && geometry.coordinates.length > 0 &&
             geometry.coordinates[0].length > 0) {
    ring = geometry.coordinates[0][0]
  }
  if (ring === null || ring.length === 0) {
    return { lon: 0, lat: 0 }
  }

  let lonSum = 0
  let latSum = 0
  for (let i = 0; i < ring.length; i = i + 1) {
    lonSum = lonSum + ring[i][0]
    latSum = latSum + ring[i][1]
  }
  return { lon: lonSum / ring.length, lat: latSum / ring.length }
}


function _renderCartogram(ctx) {
  /*
   * Render a cartogram.  Supports:
   *   - "dorling" style: sqrt-scaled circles at feature centroids.
   *   - Default: naive area-scaled choropleth (draws the GeoJSON polygon
   *     scaled by sqrt(value/totalValue) around the centroid; a full iterative
   *     algorithm requires a Worker and is deferred to future work).
   *
   * :param ctx: Renderer context.
   * :returns: A <g> SVGElement.
   */
  const raw = ctx.raw
  const root = svgEl("g", { part: "plot" }, [])

  const regions = (raw && Array.isArray(raw.regions)) ? raw.regions : []
  const geojson = (raw && raw.geojson) ? raw.geojson : null

  if (regions.length === 0) {
    return root
  }

  const styleAttr = ctx.attrs("style", "default")

  const drawW = Math.max(ctx.width - MARGIN * 2 - LEGEND_W, 10)
  const drawH = Math.max(ctx.height - MARGIN * 2, 10)

  const effectiveGeoJson = geojson !== null ? geojson : {
    features: [{
      geometry: {
        coordinates: [[[-180, -90], [180, -90], [180, 90], [-180, 90]]]
      }
    }]
  }
  const project = _makeProjection(effectiveGeoJson, drawW, drawH)

  const plot = svgEl("g", { transform: `translate(${MARGIN},${MARGIN})` }, [])
  root.appendChild(plot)

  /* Build value lookup. */
  const valueMap = {}
  let valMin = Infinity
  let valMax = -Infinity
  let valTotal = 0
  for (let i = 0; i < regions.length; i = i + 1) {
    const region = regions[i]
    if (typeof region.value === "number") {
      valueMap[region.id] = region.value
      valTotal = valTotal + region.value
      if (region.value < valMin) { valMin = region.value }
      if (region.value > valMax) { valMax = region.value }
    }
  }
  if (valMin === Infinity) { valMin = 0; valMax = 1; valTotal = 1 }
  if (valMin === valMax) { valMax = valMin + 1 }

  const radiusScale = sqrtScale([valMin, valMax], [
    Number(ctx.attrs("min-radius", "4")),
    Number(ctx.attrs("max-radius", "36"))
  ])
  const valScale = linearScale([valMin, valMax], [0, 1])

  if (styleAttr === "dorling") {
    /* Dorling cartogram: sqrt-scaled circles at feature centroids. */
    const features = geojson !== null ? (geojson.features || []) : []

    /* Build centroid lookup from GeoJSON, or fallback to region lon/lat. */
    const centroidMap = {}
    for (let fi = 0; fi < features.length; fi = fi + 1) {
      const feature = features[fi]
      const featureId = (feature.properties && feature.properties.id !== undefined)
        ? String(feature.properties.id) : String(fi)
      const centroid = _featureCentroid(feature)
      const projected = project(centroid.lon, centroid.lat)
      centroidMap[featureId] = projected
    }

    /* Sort regions largest-first (painter's order). */
    const sortedRegions = regions.slice()
    sortedRegions.sort((a, b) => {
      const va = typeof a.value === "number" ? a.value : 0
      const vb = typeof b.value === "number" ? b.value : 0
      return vb - va
    })

    for (let i = 0; i < sortedRegions.length; i = i + 1) {
      const region = sortedRegions[i]
      const value = typeof region.value === "number" ? region.value : 0
      const pos = centroidMap[region.id]
      if (pos === undefined) {
        /* Fallback: use lon/lat if attached to region. */
        if (region.lat === undefined || region.lon === undefined) { continue }
        const fallbackPos = project(region.lon, region.lat)
        centroidMap[region.id] = fallbackPos
      }
      const centre = centroidMap[region.id]
      if (centre === undefined) { continue }

      const radius = radiusScale(Math.max(value, valMin))
      const fill = region.color || ctx.colorFor(0)
      const label = region.label || region.id
      const tooltipText = `${label}: ${formatNumber(value)}`

      const circle = svgEl("circle", {
        cx: centre.x, cy: centre.y, r: radius,
        fill: fill, "fill-opacity": 0.75,
        stroke: REGION_STROKE, "stroke-width": 0.75,
        part: "region",
        "aria-label": tooltipText,
        cursor: "pointer"
      }, [svgEl("title", null, tooltipText)])

      _makeInteractive(circle, "mj-chart-select", {
        id: region.id, label: label, value: value
      }, ctx.emit)
      plot.appendChild(circle)

      const fontSize = Math.min(radius * 0.55, 11)
      if (fontSize >= 7) {
        plot.appendChild(svgEl("text", {
          x: centre.x, y: centre.y + fontSize * 0.35,
          "text-anchor": "middle",
          "font-size": fontSize,
          fill: "var(--mj-text, #14181f)",
          "pointer-events": "none"
        }, escapeHtml(label)))
      }
    }

  } else {
    /* Default cartogram: draw base map polygons scaled naively by sqrt(value).
     * Each polygon is translated to its centroid, scaled, then translated back. */
    const features = geojson !== null ? (geojson.features || []) : []

    const SEQ_RAMP_LOCAL = [
      "var(--mj-color-accent-100, #dbeafe)",
      "var(--mj-color-accent-300, #80a8ff)",
      "var(--mj-color-accent-500, #2563eb)",
      "var(--mj-color-accent-800, #122f78)"
    ]

    for (let fi = 0; fi < features.length; fi = fi + 1) {
      const feature = features[fi]
      const featureId = (feature.properties && feature.properties.id !== undefined)
        ? String(feature.properties.id) : String(fi)

      const value = valueMap[featureId]
      const hasValue = value !== undefined
      const valueSafe = hasValue ? value : valMin

      /* Scale factor: regions with value at domain mid scale to 1.0. */
      const targetArea = valueSafe / Math.max(valTotal / features.length, 1)
      const scaleFactor = Math.min(Math.sqrt(Math.max(targetArea, 0.1)), 2.5)

      const centroid = _featureCentroid(feature)
      const projCentroid = project(centroid.lon, centroid.lat)
      const cx = projCentroid.x
      const cy = projCentroid.y

      const pathData = _featureToPathData(feature, project)
      if (pathData === "") { continue }

      const t = hasValue ? valScale(value) : 0
      const colorIndex = Math.min(
        Math.floor(t * (SEQ_RAMP_LOCAL.length - 1)),
        SEQ_RAMP_LOCAL.length - 1
      )
      const fill = hasValue ? SEQ_RAMP_LOCAL[colorIndex] : NO_DATA_FILL

      const label = (feature.properties && feature.properties.name)
        ? feature.properties.name : featureId
      const tooltipText = hasValue ? `${label}: ${formatNumber(value)}` : label

      const path = svgEl("path", {
        d: pathData,
        transform: `translate(${cx},${cy}) scale(${scaleFactor.toFixed(3)}) translate(${-cx},${-cy})`,
        fill: fill,
        stroke: REGION_STROKE,
        "stroke-width": 0.75,
        "stroke-linejoin": "round",
        part: "region",
        "aria-label": tooltipText,
        cursor: "pointer"
      }, [svgEl("title", null, tooltipText)])

      _makeInteractive(path, "mj-chart-select", {
        id: featureId, label: label, value: value
      }, ctx.emit)
      plot.appendChild(path)
    }
  }

  /* Legend. */
  _appendRampLegend(plot, valMin, valMax, SEQ_RAMP, drawW + 4, 0)

  return root
}


/* ─── dispatch & registration ───────────────────────────────────────────────── */

export function render(ctx) {
  /*
   * Top-level flow/route/density/contour/cartogram renderer dispatcher.
   *
   * Delegates to the appropriate sub-renderer based on ctx.model.meta.type
   * (falling back to ctx.attrs("type", "flow-map")).
   *
   * :param ctx: Renderer context.
   * :returns: A <g> SVGElement.
   */
  const chartType = (ctx.model && ctx.model.meta && ctx.model.meta.type)
    ? ctx.model.meta.type
    : ctx.attrs("type", "flow-map")

  if (chartType === "route-map") {
    const root = _renderRouteMap(ctx)
    return root
  }

  if (chartType === "geo-heatmap") {
    const root = _renderGeoHeatmap(ctx)
    return root
  }

  if (chartType === "isoline") {
    const root = _renderIsoline(ctx)
    return root
  }

  if (chartType === "cartogram") {
    const root = _renderCartogram(ctx)
    return root
  }

  /* Default: flow-map */
  const root = _renderFlowMap(ctx)
  return root
}


registerRenderer("flow-map", render)
registerRenderer("route-map", render)
registerRenderer("geo-heatmap", render)
registerRenderer("isoline", render)
registerRenderer("cartogram", render)
