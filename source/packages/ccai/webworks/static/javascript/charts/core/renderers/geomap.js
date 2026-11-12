/*
 * geomap.js
 *
 * Geographic map renderers: choropleth fills, symbol/bubble/proportional-symbol
 * overlays, hex tile grid, and tile-grid maps. This module also exports the
 * shared geographic helpers (geometry input, projections, class colours,
 * legends) that flowmap.js uses.
 *
 * Registered types (dispatched on ctx.type):
 *   "choropleth"              — filled region map (value per region)
 *   "symbol-map"              — point symbols (fixed size unless size-scale="sqrt")
 *   "bubble-map"              — circles whose AREA is proportional to value
 *   "proportional-symbol-map" — symbols (per-series `symbol`) sized like bubble-map
 *   "hex-map"                 — equal-area hexagonal tile map
 *   "tile-grid-map"           — equal-area square tile map (plain column/row grid)
 *
 * Geometry (base maps and choropleth regions):
 *   raw.geojson   an inline GeoJSON FeatureCollection, Feature or geometry
 *   raw.topology  an inline TopoJSON Topology; `raw.topologyObject` names the
 *                 object to read (default: the first one)
 *   Polygon, MultiPolygon, LineString, MultiLineString, Point and MultiPoint
 *   features are drawn. A feature's id is properties[featureKey] when a key
 *   is given (`raw.featureKey` or the `feature-key` attribute), else the
 *   RFC 7946 `feature.id`, else `properties.id`. Geometry given as a URL
 *   string is not loaded by the renderer.
 *
 * Projection: `meta.projection` or the `projection` attribute —
 *   "equirectangular" (default; longitudes scaled by cos of the mid
 *   latitude), "mercator", "equal-area" (Equal Earth) or "natural-earth".
 *   The central meridian is chosen so data that crosses the antimeridian
 *   stays contiguous, and lines / rings take the short way across it.
 *
 * Data shapes (ctx.raw):
 *   choropleth:  regions [{id, value, label?}] + geometry; `classes` (2..9,
 *                default 5) equal-interval classes; `scheme: "diverging"`
 *                with `midpoint` (default 0) for signed data.
 *   symbol maps: series [{name, symbol?, points: [{id?, label?, lon|lng, lat, size?}]}]
 *                or markers [{lat, lng|lon, label?, value?}]; geometry optional.
 *                Bubble radius = max-radius x sqrt(value / largest value)
 *                (attributes min-radius, default 2, and max-radius, default 28);
 *                sizes <= 0 draw no symbol.
 *   hex / tile:  regions [{id, value, label?}] + layout {id: {q, r}}. Hex tiles
 *                use axial coordinates (`hex-orientation` "flat" | "pointy");
 *                square tiles put q in columns and r in rows. The `shape`
 *                attribute ("hex" | "square") overrides the type's shape.
 *
 * Events: mj-chart-select { id, label, value, ... }; a symbol point or
 * marker without an `id` reports its label as the id.
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, formatNumber } from "../svgdraw.js";
import { booleanOption } from "../chartoptions.js";


/* ─── constants ────────────────────────────────────────────────────────────── */

const MARGIN = 12
const LEGEND_W = 110
const LEGEND_SWATCH_SIZE = 12
const DEFAULT_CLASSES = 5

/*
 * Sequential ramp of nine theme-aware stops: the accent mixed into the
 * surface for low values (light in the light theme, dark in the dark
 * theme), the accent itself, then the accent mixed toward the text colour.
 * Low stops carry text in --mj-text and high stops in --mj-surface, so
 * labels keep their contrast in both themes.
 */
export const SEQ_RAMP = [
  "color-mix(in oklab, var(--mj-accent, #2563eb) 14%, var(--mj-surface, #ffffff))",
  "color-mix(in oklab, var(--mj-accent, #2563eb) 28%, var(--mj-surface, #ffffff))",
  "color-mix(in oklab, var(--mj-accent, #2563eb) 44%, var(--mj-surface, #ffffff))",
  "color-mix(in oklab, var(--mj-accent, #2563eb) 62%, var(--mj-surface, #ffffff))",
  "color-mix(in oklab, var(--mj-accent, #2563eb) 80%, var(--mj-surface, #ffffff))",
  "var(--mj-accent, #2563eb)",
  "color-mix(in oklab, var(--mj-accent, #2563eb) 82%, var(--mj-text, #14181f))",
  "color-mix(in oklab, var(--mj-accent, #2563eb) 64%, var(--mj-text, #14181f))",
  "color-mix(in oklab, var(--mj-accent, #2563eb) 48%, var(--mj-text, #14181f))"
]

/* Diverging ramp: series-2 hue below the midpoint, accent above. */
const DIVERGING_LOW = "var(--mj-chart-series-2, #eb6834)"
const DIVERGING_HIGH = "var(--mj-accent, #2563eb)"
const DIVERGING_MID = "color-mix(in oklab, var(--mj-text, #14181f) 6%, var(--mj-surface, #ffffff))"

const LOW_TEXT = "var(--mj-text, #14181f)"
const HIGH_TEXT = "var(--mj-surface, #ffffff)"

export const NO_DATA_FILL =
  "var(--mj-chart-geo-no-data, color-mix(in oklab, var(--mj-text, #14181f) 16%, var(--mj-surface, #ffffff)))"
export const REGION_STROKE = "var(--mj-surface, #ffffff)"
export const BASE_MAP_FILL =
  "var(--mj-chart-geo-land, color-mix(in oklab, var(--mj-text, #14181f) 7%, var(--mj-surface, #ffffff)))"
export const BASE_MAP_STROKE = "var(--mj-border, #e0e3e9)"


/* ─── small helpers ────────────────────────────────────────────────────────── */

export function isNumber(value) {
  /*
   * True for a finite number.
   */
  const numeric = typeof value === "number" && Number.isFinite(value) === true
  return numeric
}


function _wrap180(degrees) {
  /*
   * A longitude difference folded into [-180, 180).
   */
  const wrapped = ((((degrees + 180) % 360) + 360) % 360) - 180
  return wrapped
}


export function makeInteractive(element, eventName, detail, emit) {
  /*
   * Make an SVG mark focusable and announce it as an image; emit an event
   * on click and on Enter / Space.
   *
   * :param element:   The SVG element (already carrying its aria-label).
   * :param eventName: The event name to emit.
   * :param detail:    The event detail object.
   * :param emit:      The ctx.emit function.
   */
  element.setAttribute("tabindex", "0")
  element.setAttribute("role", "img")

  const handler = () => {
    emit(eventName, detail)
  }
  element.addEventListener("click", handler)
  element.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault()
      handler()
    }
  })
  return
}


export function lonOf(point) {
  /*
   * The longitude of a point given as lon or lng, or null.
   */
  if (point === null || typeof point !== "object") {
    return null
  }
  if (isNumber(point.lon) === true) {
    return point.lon
  }
  if (isNumber(point.lng) === true) {
    return point.lng
  }
  return null
}


/* ─── geometry input (GeoJSON / TopoJSON) ───────────────────────────────────── */

function _topologyFeatures(topology, objectName) {
  /*
   * Decode an inline TopoJSON Topology into GeoJSON features.
   *
   * :param topology: { type: "Topology", objects, arcs, transform? }.
   * :param objectName: The object to read, or null for the first one.
   * :returns: An array of GeoJSON Feature objects.
   */
  const objects = topology.objects !== null && typeof topology.objects === "object" ? topology.objects : {}
  const names = Object.keys(objects)
  const name = typeof objectName === "string" && objects[objectName] !== undefined ? objectName : names[0]
  if (name === undefined) {
    return []
  }
  const transform = topology.transform !== null && typeof topology.transform === "object" ? topology.transform : null
  const scale = transform !== null && Array.isArray(transform.scale) ? transform.scale : [1, 1]
  const translate = transform !== null && Array.isArray(transform.translate) ? transform.translate : [0, 0]
  const rawArcs = Array.isArray(topology.arcs) === true ? topology.arcs : []

  /* Quantized arcs are delta-encoded: accumulate, then scale. */
  const arcs = rawArcs.map((arc) => {
    const points = []
    let x = 0
    let y = 0
    const list = Array.isArray(arc) === true ? arc : []
    for (let i = 0; i < list.length; i = i + 1) {
      if (transform !== null) {
        x = x + list[i][0]
        y = y + list[i][1]
        points.push([x * scale[0] + translate[0], y * scale[1] + translate[1]])
      } else {
        points.push([list[i][0], list[i][1]])
      }
    }
    return points
  })
  const arcAt = (index) => {
    const arc = index >= 0 ? arcs[index] : arcs[~index]
    if (arc === undefined) {
      return []
    }
    return index >= 0 ? arc : arc.slice().reverse()
  }
  const line = (indexes) => {
    const points = []
    const list = Array.isArray(indexes) === true ? indexes : []
    for (let i = 0; i < list.length; i = i + 1) {
      const arc = arcAt(list[i])
      for (let p = i > 0 ? 1 : 0; p < arc.length; p = p + 1) {
        points.push(arc[p])
      }
    }
    return points
  }
  const position = (p) => (transform !== null
    ? [p[0] * scale[0] + translate[0], p[1] * scale[1] + translate[1]]
    : [p[0], p[1]])

  const features = []
  const convert = (geometry) => {
    if (geometry === null || typeof geometry !== "object") {
      return
    }
    let decoded = null
    const arcsOf = geometry.arcs
    if (geometry.type === "GeometryCollection") {
      const parts = Array.isArray(geometry.geometries) === true ? geometry.geometries : []
      parts.forEach(convert)
      return
    } else if (geometry.type === "Polygon") {
      decoded = { type: "Polygon", coordinates: (arcsOf || []).map(line) }
    } else if (geometry.type === "MultiPolygon") {
      decoded = { type: "MultiPolygon", coordinates: (arcsOf || []).map((polygon) => polygon.map(line)) }
    } else if (geometry.type === "LineString") {
      decoded = { type: "LineString", coordinates: line(arcsOf) }
    } else if (geometry.type === "MultiLineString") {
      decoded = { type: "MultiLineString", coordinates: (arcsOf || []).map(line) }
    } else if (geometry.type === "Point" && Array.isArray(geometry.coordinates) === true) {
      decoded = { type: "Point", coordinates: position(geometry.coordinates) }
    } else if (geometry.type === "MultiPoint" && Array.isArray(geometry.coordinates) === true) {
      decoded = { type: "MultiPoint", coordinates: geometry.coordinates.map(position) }
    }
    if (decoded !== null) {
      features.push({
        type: "Feature",
        id: geometry.id,
        properties: geometry.properties !== null && typeof geometry.properties === "object" ? geometry.properties : {},
        geometry: decoded
      })
    }
    return
  }
  convert(objects[name])
  return features
}


export function readFeatures(ctx) {
  /*
   * The map features of the data, each with a resolved `key` (its id as a
   * string) and `name`: from raw.geojson (FeatureCollection, Feature or a
   * bare geometry) or an inline raw.topology.
   *
   * :returns: [{ key, name, properties, geometry }]
   */
  const raw = ctx.raw !== null && ctx.raw !== undefined ? ctx.raw : {}
  let list = []
  const geojson = raw.geojson
  if (geojson !== null && typeof geojson === "object") {
    if (Array.isArray(geojson.features) === true) {
      list = geojson.features
    } else if (geojson.type === "Feature") {
      list = [geojson]
    } else if (typeof geojson.type === "string") {
      list = [{ type: "Feature", properties: {}, geometry: geojson }]
    }
  } else if (raw.topology !== null && typeof raw.topology === "object") {
    list = _topologyFeatures(raw.topology, raw.topologyObject)
  }

  const keyAttr = ctx.attrs("feature-key", null)
  const key = typeof keyAttr === "string" && keyAttr.length > 0
    ? keyAttr : (typeof raw.featureKey === "string" ? raw.featureKey : null)

  const features = []
  for (let index = 0; index < list.length; index = index + 1) {
    const feature = list[index]
    if (feature === null || typeof feature !== "object" || feature.geometry === null ||
        typeof feature.geometry !== "object") {
      continue
    }
    const properties = feature.properties !== null && typeof feature.properties === "object"
      ? feature.properties : {}
    let id = null
    if (key !== null && properties[key] !== undefined && properties[key] !== null) {
      id = properties[key]
    } else if (feature.id !== undefined && feature.id !== null) {
      id = feature.id
    } else if (properties.id !== undefined && properties.id !== null) {
      id = properties.id
    }
    const resolved = id !== null ? String(id) : String(index)
    const name = typeof properties.name === "string" && properties.name.length > 0 ? properties.name : resolved
    features.push({ key: resolved, name: name, properties: properties, geometry: feature.geometry })
  }
  return features
}


export function geometryLines(geometry) {
  /*
   * The coordinate lines of a geometry, for fitting a projection: rings
   * and line strings as arrays of [lon, lat], points as one-point lines.
   */
  const lines = []
  if (geometry === null || typeof geometry !== "object" || Array.isArray(geometry.coordinates) === false) {
    return lines
  }
  const coords = geometry.coordinates
  if (geometry.type === "Polygon" || geometry.type === "MultiLineString") {
    coords.forEach((ring) => lines.push(ring))
  } else if (geometry.type === "MultiPolygon") {
    coords.forEach((polygon) => polygon.forEach((ring) => lines.push(ring)))
  } else if (geometry.type === "LineString") {
    lines.push(coords)
  } else if (geometry.type === "Point") {
    lines.push([coords])
  } else if (geometry.type === "MultiPoint") {
    coords.forEach((p) => lines.push([p]))
  }
  return lines
}


/* ─── projections ───────────────────────────────────────────────────────────── */

const DEG = Math.PI / 180

/* Equal Earth constants (Šavrič, Patterson & Jenny 2018). */
const EE_A1 = 1.340264
const EE_A2 = -0.081106
const EE_A3 = 0.000893
const EE_A4 = 0.003796
const EE_M = Math.sqrt(3) / 2


function _rawProjection(name, standardLat) {
  /*
   * A raw projection (lon°, lat°) -> { x, y } with y pointing north.
   */
  if (name === "mercator") {
    return (lon, lat) => {
      const phi = Math.max(Math.min(lat, 85), -85) * DEG
      return { x: lon * DEG, y: Math.log(Math.tan(Math.PI / 4 + phi / 2)) }
    }
  }
  if (name === "equal-area") {
    return (lon, lat) => {
      const theta = Math.asin(EE_M * Math.sin(lat * DEG))
      const t2 = theta * theta
      const t6 = t2 * t2 * t2
      const x = (lon * DEG * Math.cos(theta)) /
        (EE_M * (EE_A1 + 3 * EE_A2 * t2 + t6 * (7 * EE_A3 + 9 * EE_A4 * t2)))
      const y = theta * (EE_A1 + EE_A2 * t2 + t6 * (EE_A3 + EE_A4 * t2))
      return { x: x, y: y }
    }
  }
  if (name === "natural-earth") {
    return (lon, lat) => {
      const phi = lat * DEG
      const phi2 = phi * phi
      const phi4 = phi2 * phi2
      const x = lon * DEG * (0.8707 - 0.131979 * phi2 + phi4 * (-0.013791 + phi4 * (0.003971 * phi2 - 0.001529 * phi4)))
      const y = phi * (1.007226 + phi2 * (0.015085 + phi4 * (-0.044475 + 0.028874 * phi2 - 0.005916 * phi4)))
      return { x: x, y: y }
    }
  }
  /* Equirectangular with a standard parallel: true shapes near it. */
  const factor = Math.cos(Math.max(Math.min(standardLat, 75), -75) * DEG)
  return (lon, lat) => ({ x: lon * DEG * factor, y: lat * DEG })
}


export function projectionName(ctx) {
  /*
   * The projection the chart asks for (attribute, else meta.projection).
   */
  const given = ctx.attrs("projection", null)
  const name = given !== null ? given : ctx.model.meta.projection
  const known = ["equirectangular", "mercator", "equal-area", "natural-earth"]
  return known.indexOf(name) >= 0 ? name : "equirectangular"
}


function _centralLongitude(lons) {
  /*
   * The central meridian of a set of longitudes: the middle of the
   * smallest arc that holds them all (the complement of the largest gap).
   */
  if (lons.length === 0) {
    return 0
  }
  const sorted = lons.map((lon) => _wrap180(lon)).sort((a, b) => a - b)
  let gap = sorted[0] + 360 - sorted[sorted.length - 1]
  let start = sorted[0]
  for (let i = 1; i < sorted.length; i = i + 1) {
    const step = sorted[i] - sorted[i - 1]
    if (step > gap) {
      gap = step
      start = sorted[i]
    }
  }
  const centre = _wrap180(start + (360 - gap) / 2)
  return centre
}


export function geoFrame(lines, name, width, height, padFraction) {
  /*
   * A projection fitted to coordinate lines, inside [0..width] x [0..height].
   *
   * :param lines: Arrays of [lon, lat] (rings, line strings, single points).
   * :param name: The projection name (see projectionName).
   * :param padFraction: Extra margin around the data, as a share of its size.
   * :returns: { project(lon, lat) -> {x, y}, projectLine([[lon, lat]]) ->
   *     [{x, y}] (continuous across the antimeridian), scale, bounds }.
   */
  const lons = []
  let latSum = 0
  let latMin = Infinity
  let latMax = -Infinity
  for (let l = 0; l < lines.length; l = l + 1) {
    const line = lines[l]
    for (let p = 0; p < line.length; p = p + 1) {
      const point = line[p]
      if (Array.isArray(point) === false || isNumber(point[0]) === false || isNumber(point[1]) === false) {
        continue
      }
      lons.push(point[0])
      latSum = latSum + point[1]
      latMin = Math.min(latMin, point[1])
      latMax = Math.max(latMax, point[1])
    }
  }
  const centre = _centralLongitude(lons)
  const standardLat = latMin === Infinity ? 0 : (latMin + latMax) / 2
  const rawProject = _rawProjection(name, standardLat)

  /* Continuous relative longitudes along a line (short way round). */
  const relativeLine = (line) => {
    const out = []
    let previousLon = null
    let previousRel = null
    for (let p = 0; p < line.length; p = p + 1) {
      const point = line[p]
      if (Array.isArray(point) === false || isNumber(point[0]) === false || isNumber(point[1]) === false) {
        out.push(null)
        continue
      }
      let rel = _wrap180(point[0] - centre)
      if (previousLon !== null) {
        rel = previousRel + _wrap180(point[0] - previousLon)
      }
      previousLon = point[0]
      previousRel = rel
      out.push([rel, point[1]])
    }
    return out
  }

  let x0 = Infinity
  let x1 = -Infinity
  let y0 = Infinity
  let y1 = -Infinity
  for (let l = 0; l < lines.length; l = l + 1) {
    const rel = relativeLine(lines[l])
    for (let p = 0; p < rel.length; p = p + 1) {
      if (rel[p] === null) {
        continue
      }
      const q = rawProject(rel[p][0], rel[p][1])
      x0 = Math.min(x0, q.x)
      x1 = Math.max(x1, q.x)
      y0 = Math.min(y0, q.y)
      y1 = Math.max(y1, q.y)
    }
  }
  if (x0 === Infinity) {
    const world = rawProject(180, 85)
    x0 = -world.x
    x1 = world.x
    y0 = -world.y
    y1 = world.y
  }
  /* A single point (or a line) still gets a sensible box: about 10°. */
  const minSpan = 10 * DEG
  if (x1 - x0 < minSpan) {
    const mid = (x0 + x1) / 2
    x0 = mid - minSpan / 2
    x1 = mid + minSpan / 2
  }
  if (y1 - y0 < minSpan) {
    const mid = (y0 + y1) / 2
    y0 = mid - minSpan / 2
    y1 = mid + minSpan / 2
  }
  const pad = typeof padFraction === "number" ? padFraction : 0.03
  const padX = (x1 - x0) * pad
  const padY = (y1 - y0) * pad
  x0 = x0 - padX
  x1 = x1 + padX
  y0 = y0 - padY
  y1 = y1 + padY

  const scale = Math.min(width / (x1 - x0), height / (y1 - y0))
  const offsetX = (width - (x1 - x0) * scale) / 2
  const offsetY = (height - (y1 - y0) * scale) / 2
  const toPixel = (q) => ({ x: offsetX + (q.x - x0) * scale, y: offsetY + (y1 - q.y) * scale })

  const frame = {
    scale: scale,
    centre: centre,
    project: (lon, lat) => toPixel(rawProject(_wrap180(lon - centre), lat)),
    projectLine: (line) => relativeLine(line).map((rel) => (rel === null ? null : toPixel(rawProject(rel[0], rel[1])))),
    bounds: { x: offsetX, y: offsetY, width: (x1 - x0) * scale, height: (y1 - y0) * scale }
  }
  return frame
}


export function featureLines(features) {
  /*
   * Every coordinate line of a feature list (for geoFrame).
   */
  const lines = []
  for (let i = 0; i < features.length; i = i + 1) {
    const parts = geometryLines(features[i].geometry)
    for (let p = 0; p < parts.length; p = p + 1) {
      lines.push(parts[p])
    }
  }
  return lines
}


export function geometryPath(geometry, frame) {
  /*
   * SVG path data for a geometry: closed rings for polygons, open paths
   * for lines and a small circle for each point. "" when nothing drawable.
   */
  if (geometry === null || typeof geometry !== "object" || Array.isArray(geometry.coordinates) === false) {
    return ""
  }
  const closed = geometry.type === "Polygon" || geometry.type === "MultiPolygon"
  const isPoint = geometry.type === "Point" || geometry.type === "MultiPoint"
  const lines = geometryLines(geometry)
  let data = ""
  for (let l = 0; l < lines.length; l = l + 1) {
    const pts = frame.projectLine(lines[l])
    if (isPoint === true) {
      const p = pts[0]
      if (p !== null && p !== undefined) {
        data = data + `M${(p.x - 2).toFixed(2)},${p.y.toFixed(2)} a2,2 0 1,0 4,0 a2,2 0 1,0 -4,0 `
      }
      continue
    }
    let pen = false
    for (let p = 0; p < pts.length; p = p + 1) {
      if (pts[p] === null) {
        pen = false
        continue
      }
      data = data + `${pen === true ? "L" : "M"}${pts[p].x.toFixed(2)},${pts[p].y.toFixed(2)} `
      pen = true
    }
    if (closed === true && pen === true) {
      data = data + "Z "
    }
  }
  return data.trim()
}


export function isAreal(geometry) {
  /*
   * True for polygon geometries (which take a fill).
   */
  const areal = geometry !== null && typeof geometry === "object" &&
    (geometry.type === "Polygon" || geometry.type === "MultiPolygon")
  return areal
}


export function drawBaseMap(parent, features, frame) {
  /*
   * Draw features as a neutral base-map layer in its own group, which is
   * appended to parent and returned (overlays go after it).
   */
  const group = svgEl("g", { part: "base-map", "aria-hidden": "true" }, [])
  for (let fi = 0; fi < features.length; fi = fi + 1) {
    const geometry = features[fi].geometry
    const pathData = geometryPath(geometry, frame)
    if (pathData === "") {
      continue
    }
    const areal = isAreal(geometry)
    const point = geometry.type === "Point" || geometry.type === "MultiPoint"
    group.appendChild(svgEl("path", {
      d: pathData,
      fill: areal === true || point === true ? BASE_MAP_FILL : "none",
      stroke: point === true ? "var(--mj-border-strong, #878e9c)" : BASE_MAP_STROKE,
      "stroke-width": areal === true ? 0.5 : 1,
      "stroke-linejoin": "round"
    }, []))
  }
  parent.appendChild(group)
  return group
}


/* ─── class colours and legends ─────────────────────────────────────────────── */

export function classScale(values, options) {
  /*
   * Equal-interval classes over numeric values.
   *
   * :param values: The data values (non-numbers ignored).
   * :param options: { classes (2..9), scheme: "sequential" | "diverging",
   *     midpoint } -- the diverging scheme centres the classes on the
   *     midpoint (default 0) and colours below / above it with two hues.
   * :returns: { count, breaks: [b0..bn], classOf(v), colorOf(v),
   *     textColorOf(v), min, max } -- classOf(v) = min(floor(t * n), n - 1).
   */
  const given = options !== null && options !== undefined ? options : {}
  const count = isNumber(given.classes) === true
    ? Math.max(2, Math.min(9, Math.round(given.classes))) : DEFAULT_CLASSES
  const diverging = given.scheme === "diverging"
  let min = Infinity
  let max = -Infinity
  for (let i = 0; i < values.length; i = i + 1) {
    if (isNumber(values[i]) === true) {
      min = Math.min(min, values[i])
      max = Math.max(max, values[i])
    }
  }
  if (min === Infinity) {
    min = 0
    max = 1
  }
  if (diverging === true) {
    const mid = isNumber(given.midpoint) === true ? given.midpoint : 0
    const half = Math.max(Math.abs(max - mid), Math.abs(mid - min), 1e-9)
    min = mid - half
    max = mid + half
  }
  if (min === max) {
    min = min - 0.5
    max = max + 0.5
  }

  const breaks = []
  for (let i = 0; i <= count; i = i + 1) {
    breaks.push(min + ((max - min) * i) / count)
  }
  const classOf = (value) => {
    const t = (value - min) / (max - min)
    return Math.max(0, Math.min(Math.floor(t * count), count - 1))
  }

  /* Class colours: spread the classes over the ramp. */
  const colors = []
  const darkText = []
  for (let c = 0; c < count; c = c + 1) {
    if (diverging === true) {
      const centre = (count - 1) / 2
      const distance = Math.abs(c - centre) / Math.max(centre, 0.5)
      const hue = c < centre ? DIVERGING_LOW : DIVERGING_HIGH
      const share = Math.round(15 + distance * 85)
      colors.push(Math.abs(c - centre) < 0.01 ? DIVERGING_MID : `color-mix(in oklab, ${hue} ${share}%, ${DIVERGING_MID})`)
      darkText.push(distance < 0.6)
    } else {
      const index = count === 1 ? 0 : Math.round((c / (count - 1)) * (SEQ_RAMP.length - 1))
      colors.push(SEQ_RAMP[index])
      darkText.push(index <= 3)
    }
  }

  const scale = {
    count: count,
    breaks: breaks,
    min: min,
    max: max,
    classOf: classOf,
    colorOf: (value) => (isNumber(value) === true ? colors[classOf(value)] : NO_DATA_FILL),
    textColorOf: (value) => (isNumber(value) === true && darkText[classOf(value)] === false ? HIGH_TEXT : LOW_TEXT),
    colorAt: (index) => colors[index]
  }
  return scale
}


export function appendClassLegend(parent, scale, x, y, title, withNoData) {
  /*
   * A vertical legend of the classes, highest first, each labelled with
   * its range (class breaks).
   */
  const legend = svgEl("g", { part: "legend", "aria-hidden": "true" }, [])
  const rowH = LEGEND_SWATCH_SIZE + 4
  let top = y
  if (typeof title === "string" && title.length > 0) {
    legend.appendChild(svgEl("text", {
      x: x, y: top + 9, "font-size": 10, "font-weight": "600",
      fill: "var(--mj-text-muted, #5f6673)"
    }, title))
    top = top + 16
  }
  const span = scale.max - scale.min
  const digits = span >= 50 ? 0 : (span >= 5 ? 1 : 2)
  const fmt = (value) => formatNumber(value, { maximumFractionDigits: digits })
  for (let c = scale.count - 1; c >= 0; c = c - 1) {
    const sy = top + (scale.count - 1 - c) * rowH
    legend.appendChild(svgEl("rect", {
      x: x, y: sy, width: LEGEND_SWATCH_SIZE, height: LEGEND_SWATCH_SIZE,
      fill: scale.colorAt(c),
      stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 0.5
    }, []))
    legend.appendChild(svgEl("text", {
      x: x + LEGEND_SWATCH_SIZE + 4, y: sy + LEGEND_SWATCH_SIZE - 2,
      "font-size": 10, fill: "var(--mj-text-muted, #5f6673)"
    }, `${fmt(scale.breaks[c])} – ${fmt(scale.breaks[c + 1])}`))
  }
  if (withNoData === true) {
    const sy = top + scale.count * rowH
    legend.appendChild(svgEl("rect", {
      x: x, y: sy, width: LEGEND_SWATCH_SIZE, height: LEGEND_SWATCH_SIZE,
      fill: NO_DATA_FILL, stroke: "var(--mj-border, #e0e3e9)", "stroke-width": 0.5
    }, []))
    legend.appendChild(svgEl("text", {
      x: x + LEGEND_SWATCH_SIZE + 4, y: sy + LEGEND_SWATCH_SIZE - 2,
      "font-size": 10, fill: "var(--mj-text-muted, #5f6673)"
    }, "No data"))
  }
  parent.appendChild(legend)
  return legend
}


export function appendSizeLegend(parent, radiusOf, maxValue, x, y, title) {
  /*
   * A nested-circle legend for an area-proportional size encoding.
   *
   * :param radiusOf: value -> radius in pixels.
   */
  const legend = svgEl("g", { part: "legend", "aria-hidden": "true" }, [])
  if (isNumber(maxValue) === false || maxValue <= 0) {
    return legend
  }
  /* Up to three round reference values: about max, max / 4 and max / 16. */
  const roundDown = (v) => {
    const magnitude = Math.pow(10, Math.floor(Math.log10(v)))
    return Math.floor(v / magnitude) * magnitude
  }
  const values = []
  for (const share of [1 / 16, 1 / 4, 1]) {
    const v = roundDown(maxValue * share)
    if (v > 0 && values.indexOf(v) < 0) {
      values.push(v)
    }
  }
  const largest = radiusOf(values[values.length - 1])
  let top = y
  if (typeof title === "string" && title.length > 0) {
    legend.appendChild(svgEl("text", {
      x: x, y: top + 9, "font-size": 10, "font-weight": "600",
      fill: "var(--mj-text-muted, #5f6673)"
    }, title))
    top = top + 16
  }
  const baseY = top + largest * 2
  const cx = x + largest
  for (let i = values.length - 1; i >= 0; i = i - 1) {
    const r = radiusOf(values[i])
    legend.appendChild(svgEl("circle", {
      cx: cx, cy: baseY - r, r: r,
      fill: "none", stroke: "var(--mj-text-muted, #5f6673)", "stroke-width": 0.75
    }, []))
    legend.appendChild(svgEl("line", {
      x1: cx, y1: baseY - 2 * r, x2: cx + largest + 6, y2: baseY - 2 * r,
      stroke: "var(--mj-border-strong, #878e9c)", "stroke-width": 0.5, "stroke-dasharray": "2,2"
    }, []))
    legend.appendChild(svgEl("text", {
      x: cx + largest + 8, y: baseY - 2 * r + 3,
      "font-size": 9, fill: "var(--mj-text-muted, #5f6673)"
    }, formatNumber(values[i], { notation: values[i] >= 1e5 ? "compact" : "standard" })))
  }
  parent.appendChild(legend)
  return legend
}


function _legendSpace(ctx) {
  /*
   * Width kept for an in-chart legend (none on very narrow charts).
   */
  const space = ctx.width >= 280 ? LEGEND_W : 0
  return space
}


/* ─── choropleth renderer ───────────────────────────────────────────────────── */

function _regionValues(regions) {
  /*
   * A Map id -> { value, label } of the regions with a numeric value.
   */
  const map = new Map()
  for (let i = 0; i < regions.length; i = i + 1) {
    const region = regions[i]
    if (region === null || typeof region !== "object" || region.id === undefined || region.id === null) {
      continue
    }
    map.set(String(region.id), {
      value: isNumber(region.value) === true ? region.value : null,
      label: typeof region.label === "string" && region.label.length > 0 ? region.label : null,
      region: region
    })
  }
  return map
}


function _renderChoropleth(ctx) {
  /*
   * Render a choropleth map: filled region polygons coloured by value
   * class. Regions with lat/lon and no geometry are drawn as dots.
   *
   * :param ctx: Renderer context.
   * :returns: A <g> SVGElement.
   */
  const raw = ctx.raw !== null && ctx.raw !== undefined ? ctx.raw : {}
  const root = svgEl("g", { part: "plot" }, [])

  const regions = Array.isArray(raw.regions) === true ? raw.regions : []
  const features = readFeatures(ctx)
  if (regions.length === 0 && features.length === 0) {
    return root
  }

  const legendAreaW = regions.length > 0 ? _legendSpace(ctx) : 0
  const drawW = Math.max(ctx.width - MARGIN * 2 - legendAreaW, 10)
  const drawH = Math.max(ctx.height - MARGIN * 2, 10)

  const pointRegions = regions.filter((r) => r !== null && typeof r === "object" &&
    isNumber(r.lat) === true && lonOf(r) !== null)
  const fitLines = features.length > 0
    ? featureLines(features)
    : pointRegions.map((r) => [[lonOf(r), r.lat]])
  const frame = geoFrame(fitLines, projectionName(ctx), drawW, drawH, features.length > 0 ? 0.02 : 0.15)

  const plot = svgEl("g", { transform: `translate(${MARGIN},${MARGIN})` }, [])
  root.appendChild(plot)

  const lookup = _regionValues(regions)
  const scale = classScale(Array.from(lookup.values()).map((entry) => entry.value), {
    classes: raw.classes,
    scheme: raw.scheme,
    midpoint: raw.midpoint
  })

  const tableRows = []
  const drawnIds = new Set()
  const regionGroup = svgEl("g", { part: "regions" }, [])
  plot.appendChild(regionGroup)

  for (let fi = 0; fi < features.length; fi = fi + 1) {
    const feature = features[fi]
    const pathData = geometryPath(feature.geometry, frame)
    if (pathData === "") {
      continue
    }
    const entry = lookup.get(feature.key)
    const value = entry !== undefined ? entry.value : null
    const label = entry !== undefined && entry.label !== null ? entry.label : feature.name
    const tooltipText = value !== null ? `${label}: ${formatNumber(value)}` : `${label}: no data`
    const areal = isAreal(feature.geometry)

    const path = svgEl("path", {
      d: pathData,
      fill: areal === true ? scale.colorOf(value) : "none",
      stroke: areal === true ? REGION_STROKE : scale.colorOf(value),
      "stroke-width": areal === true ? 0.75 : 2,
      "stroke-linejoin": "round",
      part: "region",
      "aria-label": tooltipText,
      cursor: "pointer"
    }, [svgEl("title", null, tooltipText)])
    makeInteractive(path, "mj-chart-select", { id: feature.key, label: label, value: value }, ctx.emit)
    regionGroup.appendChild(path)
    drawnIds.add(feature.key)
  }

  /* Regions with a position but no geometry: dots. */
  if (features.length === 0) {
    for (let ri = 0; ri < pointRegions.length; ri = ri + 1) {
      const region = pointRegions[ri]
      const pt = frame.project(lonOf(region), region.lat)
      const value = isNumber(region.value) === true ? region.value : null
      const label = typeof region.label === "string" ? region.label : String(region.id)
      const tooltipText = value !== null ? `${label}: ${formatNumber(value)}` : `${label}: no data`
      const circle = svgEl("circle", {
        cx: pt.x, cy: pt.y, r: 8,
        fill: scale.colorOf(value), stroke: "var(--mj-border-strong, #878e9c)", "stroke-width": 1,
        part: "region", "aria-label": tooltipText, cursor: "pointer"
      }, [svgEl("title", null, tooltipText)])
      makeInteractive(circle, "mj-chart-select", { id: region.id, label: label, value: value }, ctx.emit)
      regionGroup.appendChild(circle)
      drawnIds.add(String(region.id))
    }
  }

  lookup.forEach((entry, id) => {
    tableRows.push([entry.label !== null ? entry.label : id, id, entry.value === null ? "" : entry.value])
  })

  if (legendAreaW > 0) {
    const hasNoData = features.some((f) => lookup.has(f.key) === false || lookup.get(f.key).value === null)
    const legendX = Math.min(frame.bounds.x + frame.bounds.width + 16, drawW + 8)
    appendClassLegend(plot, scale, legendX, 0,
      typeof ctx.model.meta.valueLabel === "string" ? ctx.model.meta.valueLabel : "", hasNoData)
  }

  ctx.setTable({ columns: ["Region", "Id", "Value"], rows: tableRows })
  return root
}


/* ─── symbol / bubble / proportional-symbol renderer ───────────────────────── */

function _symbolPath(symbolType, cx, cy, halfSize) {
  /*
   * A minimal SVG path `d` for a non-circle symbol centred at (cx, cy).
   * The shapes keep the area of a circle of radius halfSize, so a size
   * encoding stays area-proportional across symbol types.
   *
   * :param symbolType: "square" | "triangle" | "diamond".
   * :returns: SVG path data string, or null for unsupported types.
   */
  const area = Math.PI * halfSize * halfSize
  if (symbolType === "square") {
    const h = Math.sqrt(area) / 2
    return `M${cx - h},${cy - h} L${cx + h},${cy - h} L${cx + h},${cy + h} L${cx - h},${cy + h} Z`
  }
  if (symbolType === "diamond") {
    const h = Math.sqrt(area / 2)
    return `M${cx},${cy - h} L${cx + h},${cy} L${cx},${cy + h} L${cx - h},${cy} Z`
  }
  if (symbolType === "triangle") {
    /* Equilateral: area = (sqrt(3) / 4) side^2. */
    const side = Math.sqrt((4 * area) / Math.sqrt(3))
    const height = (side * Math.sqrt(3)) / 2
    return `M${cx},${cy - (2 * height) / 3} L${cx + side / 2},${cy + height / 3} L${cx - side / 2},${cy + height / 3} Z`
  }
  return null
}


function _symbolSeries(ctx) {
  /*
   * The symbol layers: the visible series (raw.series via the model), or
   * one layer from raw.markers.
   */
  const raw = ctx.raw !== null && ctx.raw !== undefined ? ctx.raw : {}
  const layers = []
  const series = ctx.model.series
  if (series.length > 0) {
    for (let si = 0; si < series.length; si = si + 1) {
      const s = series[si]
      layers.push({
        name: s.name,
        symbol: typeof s.symbol === "string" ? s.symbol : "circle",
        color: ctx.colorFor(s.name),
        points: Array.isArray(s.points) === true ? s.points : []
      })
    }
  } else if (Array.isArray(raw.markers) === true && raw.markers.length > 0) {
    const pts = raw.markers.filter((m) => m !== null && typeof m === "object").map((m) => ({
      id: m.id !== undefined ? m.id : m.label,
      label: m.label !== undefined ? m.label : m.id,
      lon: lonOf(m),
      lat: m.lat,
      size: isNumber(m.size) === true ? m.size : m.value
    }))
    layers.push({
      name: "Markers",
      symbol: typeof raw.symbol === "string" ? raw.symbol : "circle",
      color: ctx.colorFor(0),
      points: pts
    })
  }
  return layers
}


function _renderSymbolMap(ctx) {
  /*
   * Render a symbol map, bubble map, or proportional-symbol map.
   *
   * :param ctx: Renderer context.
   * :returns: A <g> SVGElement.
   */
  const root = svgEl("g", { part: "plot" }, [])
  const layers = _symbolSeries(ctx)
  if (layers.length === 0) {
    return root
  }

  const sized = ctx.type === "bubble-map" || ctx.type === "proportional-symbol-map"
  const sizeScaleMode = ctx.attrs("size-scale", sized === true ? "sqrt" : "none")

  /* Every symbol with a position, and the largest positive size. */
  const marks = []
  let sizeMax = 0
  for (let si = 0; si < layers.length; si = si + 1) {
    const layer = layers[si]
    for (let pi = 0; pi < layer.points.length; pi = pi + 1) {
      const pt = layer.points[pi]
      const lon = lonOf(pt)
      if (lon === null || isNumber(pt.lat) === false) {
        continue
      }
      const size = isNumber(pt.size) === true ? pt.size : null
      if (size !== null && size > 0) {
        sizeMax = Math.max(sizeMax, size)
      }
      marks.push({ layer: layer, point: pt, lon: lon, lat: pt.lat, size: size })
    }
  }

  const useSize = sizeScaleMode === "sqrt" && sizeMax > 0
  const legendAreaW = useSize === true ? _legendSpace(ctx) : 0
  const drawW = Math.max(ctx.width - MARGIN * 2 - legendAreaW, 10)
  const drawH = Math.max(ctx.height - MARGIN * 2, 10)

  const features = readFeatures(ctx)
  const fitLines = features.length > 0 ? featureLines(features) : marks.map((m) => [[m.lon, m.lat]])
  const frame = geoFrame(fitLines, projectionName(ctx), drawW, drawH, features.length > 0 ? 0.02 : 0.15)

  const plot = svgEl("g", { transform: `translate(${MARGIN},${MARGIN})` }, [])
  root.appendChild(plot)
  drawBaseMap(plot, features, frame)

  /* Area-proportional radius: max-radius x sqrt(size / largest size). */
  const minRadius = Math.max(Number(ctx.attrs("min-radius", "2")), 0)
  const maxRadius = Math.max(Number(ctx.attrs("max-radius", "28")), minRadius + 1)
  const radiusOf = (size) => Math.max(maxRadius * Math.sqrt(size / sizeMax), minRadius)

  /* Largest symbols first so small ones stay on top. */
  if (useSize === true) {
    marks.sort((a, b) => (b.size !== null ? b.size : 0) - (a.size !== null ? a.size : 0))
  }

  const showLabels = booleanOption(ctx, "show-labels", false)
  const symbolGroup = svgEl("g", { part: "symbols" }, [])
  plot.appendChild(symbolGroup)
  const labelGroup = svgEl("g", { "aria-hidden": "true", part: "labels" }, [])
  const tableRows = []

  for (let mi = 0; mi < marks.length; mi = mi + 1) {
    const m = marks[mi]
    const pt = m.point
    const label = pt.label !== undefined && pt.label !== null ? String(pt.label)
      : (pt.id !== undefined && pt.id !== null ? String(pt.id)
        : `(${formatNumber(m.lon)}, ${formatNumber(m.lat)})`)
    tableRows.push([label, m.layer.name, m.lat, m.lon, m.size === null ? "" : m.size])

    let radius = 6
    if (useSize === true) {
      if (m.size === null || m.size <= 0) {
        /* No positive size: nothing to encode, no symbol. */
        continue
      }
      radius = radiusOf(m.size)
    }

    const projected = frame.project(m.lon, m.lat)
    const tooltipText = m.size !== null ? `${label}: ${formatNumber(m.size)}` : label
    let mark = null
    const shared = {
      fill: m.layer.color, "fill-opacity": useSize === true ? 0.6 : 0.85,
      stroke: "var(--mj-surface, #ffffff)", "stroke-width": 1,
      part: "symbol", "aria-label": tooltipText, cursor: "pointer"
    }
    const pathData = m.layer.symbol === "circle" ? null : _symbolPath(m.layer.symbol, projected.x, projected.y, radius)
    if (pathData !== null) {
      mark = svgEl("path", { d: pathData, ...shared }, [svgEl("title", null, tooltipText)])
    } else {
      mark = svgEl("circle", { cx: projected.x, cy: projected.y, r: radius, ...shared },
        [svgEl("title", null, tooltipText)])
    }
    /* A point without an id is identified by its label (as markers are). */
    const pointId = pt.id !== undefined && pt.id !== null ? pt.id : label
    makeInteractive(mark, "mj-chart-select", {
      id: pointId, label: label, lon: m.lon, lat: m.lat,
      value: m.size, series: m.layer.name
    }, ctx.emit)
    symbolGroup.appendChild(mark)

    if (showLabels === true && pt.label !== undefined && pt.label !== null) {
      labelGroup.appendChild(svgEl("text", {
        x: projected.x, y: projected.y - radius - 3,
        "text-anchor": "middle", "font-size": 9,
        fill: "var(--mj-text, #14181f)",
        stroke: "var(--mj-surface, #ffffff)", "stroke-width": 2.5, "paint-order": "stroke"
      }, String(pt.label)))
    }
  }
  plot.appendChild(labelGroup)

  if (useSize === true && legendAreaW > 0) {
    const title = typeof ctx.model.meta.sizeLabel === "string" ? ctx.model.meta.sizeLabel : ""
    const legendX = Math.min(frame.bounds.x + frame.bounds.width + 16, drawW + 8)
    appendSizeLegend(plot, (v) => radiusOf(v), sizeMax, legendX, 0, title)
  }

  ctx.setTable({ columns: ["Place", "Series", "Latitude", "Longitude", "Size"], rows: tableRows })
  return root
}


/* ─── hex-map / tile-grid-map renderer ──────────────────────────────────────── */

function _hexPoints(cx, cy, radius, orientation) {
  /*
   * The six corners of a regular hexagon as an SVG points string: a
   * flat-top hexagon starts at 0°, a pointy-top one at 30°, matching the
   * axial spacing of _axialToUnit.
   */
  const points = []
  const startAngle = orientation === "pointy" ? Math.PI / 6 : 0
  for (let corner = 0; corner < 6; corner = corner + 1) {
    const angle = startAngle + corner * (Math.PI / 3)
    const x = cx + radius * Math.cos(angle)
    const y = cy + radius * Math.sin(angle)
    points.push(`${x.toFixed(2)},${y.toFixed(2)}`)
  }
  return points.join(" ")
}


function _axialToUnit(q, r, orientation) {
  /*
   * Axial hex coordinates (q, r) to a centre for circumradius 1.
   */
  if (orientation === "flat") {
    return { x: 1.5 * q, y: Math.sqrt(3) * (r + q / 2) }
  }
  return { x: Math.sqrt(3) * (q + r / 2), y: 1.5 * r }
}


function _tileLayout(regions, rawLayout) {
  /*
   * A Map id -> {q, r} from the data's layout; regions without a position
   * are placed on free rows below it, in a near-square block. The data is
   * not modified.
   */
  const layout = new Map()
  const source = rawLayout !== null && typeof rawLayout === "object" ? rawLayout : {}
  let maxR = -1
  for (let i = 0; i < regions.length; i = i + 1) {
    const id = String(regions[i].id)
    const pos = source[id]
    if (pos !== null && typeof pos === "object" && isNumber(pos.q) === true && isNumber(pos.r) === true) {
      layout.set(id, { q: pos.q, r: pos.r })
      maxR = Math.max(maxR, pos.r)
    }
  }
  const unplaced = regions.filter((region) => layout.has(String(region.id)) === false)
  const columns = Math.max(Math.ceil(Math.sqrt(unplaced.length * 1.6)), 1)
  for (let i = 0; i < unplaced.length; i = i + 1) {
    layout.set(String(unplaced[i].id), { q: i % columns, r: maxR + 1 + Math.floor(i / columns) })
  }
  return layout
}


function _renderHexMap(ctx) {
  /*
   * Render a hex-map (hexagonal tiles on an axial grid) or a tile-grid map
   * (square tiles on a column/row grid). Each region's tile is coloured
   * by its value class.
   *
   * :param ctx: Renderer context.
   * :returns: A <g> SVGElement.
   */
  const raw = ctx.raw !== null && ctx.raw !== undefined ? ctx.raw : {}
  const root = svgEl("g", { part: "plot" }, [])

  const regions = (Array.isArray(raw.regions) === true ? raw.regions : [])
    .filter((r) => r !== null && typeof r === "object" && r.id !== undefined && r.id !== null)
  if (regions.length === 0) {
    return root
  }

  const orientation = ctx.attrs("hex-orientation", "flat") === "pointy" ? "pointy" : "flat"
  const shapeAttr = ctx.attrs("shape", null)
  const square = shapeAttr !== null ? shapeAttr === "square" : ctx.type === "tile-grid-map"
  const layout = _tileLayout(regions, raw.layout)

  const lookup = _regionValues(regions)
  const scale = classScale(Array.from(lookup.values()).map((entry) => entry.value), {
    classes: raw.classes, scheme: raw.scheme, midpoint: raw.midpoint
  })

  /* Tile centres for unit size, and the pixel extent of every tile. */
  const halfW = square === true ? 0.5 : (orientation === "flat" ? 1 : Math.sqrt(3) / 2)
  const halfH = square === true ? 0.5 : (orientation === "flat" ? Math.sqrt(3) / 2 : 1)
  const centres = new Map()
  let x0 = Infinity
  let x1 = -Infinity
  let y0 = Infinity
  let y1 = -Infinity
  layout.forEach((pos, id) => {
    const c = square === true ? { x: pos.q, y: pos.r } : _axialToUnit(pos.q, pos.r, orientation)
    centres.set(id, c)
    x0 = Math.min(x0, c.x - halfW)
    x1 = Math.max(x1, c.x + halfW)
    y0 = Math.min(y0, c.y - halfH)
    y1 = Math.max(y1, c.y + halfH)
  })

  const legendAreaW = _legendSpace(ctx)
  const drawW = Math.max(ctx.width - MARGIN * 2 - legendAreaW, 10)
  const drawH = Math.max(ctx.height - MARGIN * 2, 10)
  const unit = Math.min(drawW / (x1 - x0), drawH / (y1 - y0))
  const offsetX = MARGIN + (drawW - (x1 - x0) * unit) / 2 - x0 * unit
  const offsetY = MARGIN + (drawH - (y1 - y0) * unit) / 2 - y0 * unit

  const plot = svgEl("g", { part: "tiles" }, [])
  root.appendChild(plot)
  const labels = svgEl("g", { "aria-hidden": "true", part: "labels" }, [])
  const tableRows = []

  for (let i = 0; i < regions.length; i = i + 1) {
    const region = regions[i]
    const id = String(region.id)
    const c = centres.get(id)
    const cx = offsetX + c.x * unit
    const cy = offsetY + c.y * unit
    const entry = lookup.get(id)
    const value = entry !== undefined ? entry.value : null
    const labelText = entry !== undefined && entry.label !== null ? entry.label : id
    const tooltipText = value !== null ? `${labelText}: ${formatNumber(value)}` : `${labelText}: no data`

    let mark = null
    if (square === true) {
      const size = unit * 0.94
      mark = svgEl("rect", {
        x: cx - size / 2, y: cy - size / 2, width: size, height: size, rx: Math.min(size * 0.08, 4),
        fill: scale.colorOf(value),
        part: "region", "aria-label": tooltipText, cursor: "pointer"
      }, [svgEl("title", null, tooltipText)])
    } else {
      mark = svgEl("polygon", {
        points: _hexPoints(cx, cy, unit * 0.95, orientation),
        fill: scale.colorOf(value),
        part: "region", "aria-label": tooltipText, cursor: "pointer"
      }, [svgEl("title", null, tooltipText)])
    }
    makeInteractive(mark, "mj-chart-select", { id: id, label: labelText, value: value }, ctx.emit)
    plot.appendChild(mark)
    tableRows.push([labelText, id, value === null ? "" : value])

    /* Label in a colour that reads on the tile's fill. */
    const fontSize = Math.min(unit * (square === true ? 0.36 : 0.5), 12)
    if (fontSize >= 7) {
      labels.appendChild(svgEl("text", {
        x: cx, y: cy + fontSize * 0.35,
        "text-anchor": "middle",
        "font-size": fontSize,
        fill: scale.textColorOf(value),
        "pointer-events": "none"
      }, labelText))
    }
  }
  root.appendChild(labels)

  if (legendAreaW > 0) {
    const gridRight = offsetX + x1 * unit
    const hasNoData = regions.some((r) => lookup.get(String(r.id)).value === null)
    appendClassLegend(root, scale, Math.min(gridRight + 12, ctx.width - legendAreaW + 4), MARGIN,
      typeof ctx.model.meta.valueLabel === "string" ? ctx.model.meta.valueLabel : "", hasNoData)
  }

  ctx.setTable({ columns: ["Region", "Id", "Value"], rows: tableRows })
  return root
}


/* ─── dispatch & registration ───────────────────────────────────────────────── */

export function render(ctx) {
  /*
   * Geographic map renderer dispatcher: the sub-renderer of ctx.type.
   *
   * :param ctx: Renderer context.
   * :returns: A <g> SVGElement.
   */
  const chartType = typeof ctx.type === "string" ? ctx.type : ctx.attrs("type", "choropleth")
  let root = null
  if (chartType === "symbol-map" || chartType === "bubble-map" || chartType === "proportional-symbol-map") {
    root = _renderSymbolMap(ctx)
  } else if (chartType === "hex-map" || chartType === "tile-grid-map") {
    root = _renderHexMap(ctx)
  } else {
    root = _renderChoropleth(ctx)
  }
  return root
}


registerRenderer("choropleth", render, { legend: "none" })
registerRenderer("symbol-map", render)
registerRenderer("bubble-map", render)
registerRenderer("proportional-symbol-map", render)
registerRenderer("hex-map", render, { legend: "none" })
registerRenderer("tile-grid-map", render, { legend: "none" })
