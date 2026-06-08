/*
 * geomap.js
 *
 * Geographic map renderers: choropleth fills, symbol/bubble/proportional-symbol
 * overlays, hex tile grid, and tile-grid maps.
 *
 * Registered types:
 *   "choropleth"              — filled region map (value per region)
 *   "symbol-map"              — point/circle/bubble/proportional-symbol map
 *   "bubble-map"              — alias, activates sqrt size scale
 *   "proportional-symbol-map" — alias, activates symbol + size scale
 *   "hex-map"                 — equal-area hexagonal tile map
 *   "tile-grid-map"           — equal-area square tile map
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
 *   Choropleth / cartogram / hex-map:
 *     raw.regions  [{id, value, label?}]
 *     raw.geojson  GeoJSON FeatureCollection (inline) — optional
 *     raw.layout   hex-grid layout map  id -> {q, r}  — hex-map only
 *
 *   Symbol / bubble / proportional:
 *     raw.series   [{name, symbol?, points:[{id,label?,lon,lat,size?}]}]
 *     raw.geojson  GeoJSON FeatureCollection for the base map — optional
 *
 * GeoJSON polygons are projected with an equirectangular projection computed
 * from the bounding box of all coordinates in the FeatureCollection.
 */

import { registerRenderer } from "../renderregistry.js";
import { svgEl, escapeHtml, formatNumber } from "../svgdraw.js";
import { linearScale, sqrtScale } from "../scales.js";


/* ─── constants ────────────────────────────────────────────────────────────── */

const MARGIN = 12
const LEGEND_W = 110
const LEGEND_SWATCH_SIZE = 12
const CHOROPLETH_STEPS = 6

/* Sequential blue token ramp (light → dark), 6 stops */
const SEQ_RAMP = [
  "var(--mj-color-accent-100, #dbeafe)",
  "var(--mj-color-accent-200, #bfdbfe)",
  "var(--mj-color-accent-300, #80a8ff)",
  "var(--mj-color-accent-400, #3b82f6)",
  "var(--mj-color-accent-500, #2563eb)",
  "var(--mj-color-accent-800, #122f78)"
]

const NO_DATA_FILL = "var(--mj-chart-geo-no-data, #e5e7eb)"
const REGION_STROKE = "var(--mj-border, #e0e3e9)"
const BASE_MAP_FILL = "var(--mj-surface-2, #f3f4f6)"
const BASE_MAP_STROKE = "var(--mj-border, #e0e3e9)"


/* ─── projection helpers ────────────────────────────────────────────────────── */

function _geoJsonBounds(geojson) {
  /*
   * Compute [lonMin, lonMax, latMin, latMax] over all coordinates in a
   * GeoJSON FeatureCollection.
   *
   * :param geojson: A GeoJSON FeatureCollection.
   * :returns: [lonMin, lonMax, latMin, latMax]
   */
  let lonMin = Infinity
  let lonMax = -Infinity
  let latMin = Infinity
  let latMax = -Infinity

  const visitCoords = (coords) => {
    if (coords === null || coords === undefined) {
      return
    }
    if (typeof coords[0] === "number") {
      const lon = coords[0]
      const lat = coords[1]
      if (lon < lonMin) { lonMin = lon }
      if (lon > lonMax) { lonMax = lon }
      if (lat < latMin) { latMin = lat }
      if (lat > latMax) { latMax = lat }
      return
    }
    for (let index = 0; index < coords.length; index = index + 1) {
      visitCoords(coords[index])
    }
  }

  const features = (geojson && geojson.features) ? geojson.features : []
  for (let fi = 0; fi < features.length; fi = fi + 1) {
    const geometry = features[fi].geometry
    if (geometry === null || geometry === undefined) {
      continue
    }
    visitCoords(geometry.coordinates)
  }

  if (lonMin === Infinity) {
    return [-180, 180, -90, 90]
  }
  return [lonMin, lonMax, latMin, latMax]
}


function _makeProjection(geojson, drawW, drawH) {
  /*
   * Build an equirectangular projection function for the given GeoJSON bounds
   * that maps (lon, lat) -> {x, y} within [0..drawW] x [0..drawH].
   *
   * :param geojson: GeoJSON FeatureCollection or null.
   * :param drawW:   Available drawing width in pixels.
   * :param drawH:   Available drawing height in pixels.
   * :returns: A projection function (lon, lat) -> {x, y}.
   */
  const bounds = _geoJsonBounds(geojson)
  const lonMin = bounds[0]
  const lonMax = bounds[1]
  const latMin = bounds[2]
  const latMax = bounds[3]

  const lonSpan = (lonMax - lonMin) || 1
  const latSpan = (latMax - latMin) || 1

  /* Fit with uniform scale so aspect ratio is preserved. */
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


function _markerProjection(markers, drawW, drawH) {
  /*
   * Build a projection from a markers array [{lat,lng}] when no GeoJSON is
   * available.  Falls back to the full world bounds when markers is empty.
   */
  let lonMin = Infinity
  let lonMax = -Infinity
  let latMin = Infinity
  let latMax = -Infinity

  for (let i = 0; i < markers.length; i = i + 1) {
    const m = markers[i]
    const lon = m.lng !== undefined ? m.lng : (m.lon !== undefined ? m.lon : 0)
    const lat = m.lat !== undefined ? m.lat : 0
    if (lon < lonMin) { lonMin = lon }
    if (lon > lonMax) { lonMax = lon }
    if (lat < latMin) { latMin = lat }
    if (lat > latMax) { latMax = lat }
  }

  if (lonMin === Infinity) {
    lonMin = -180; lonMax = 180; latMin = -90; latMax = 90
  } else {
    /* Add padding so edge markers don't sit on the border. */
    const lonPad = Math.max((lonMax - lonMin) * 0.15, 2)
    const latPad = Math.max((latMax - latMin) * 0.15, 2)
    lonMin = lonMin - lonPad
    lonMax = lonMax + lonPad
    latMin = latMin - latPad
    latMax = latMax + latPad
  }

  const fakeGeoJson = {
    features: [{
      geometry: {
        coordinates: [[
          [lonMin, latMin], [lonMax, latMin],
          [lonMax, latMax], [lonMin, latMax]
        ]]
      }
    }]
  }
  return _makeProjection(fakeGeoJson, drawW, drawH)
}


/* ─── GeoJSON → SVG path ────────────────────────────────────────────────────── */

function _ringToPathSegment(ring, project) {
  /*
   * Convert a GeoJSON coordinate ring [[lon,lat],...] to an SVG path segment.
   *
   * :returns: A partial SVG path data string for one ring.
   */
  let data = ""
  for (let index = 0; index < ring.length; index = index + 1) {
    const coord = ring[index]
    const pt = project(coord[0], coord[1])
    const command = index === 0 ? "M" : "L"
    data = data + `${command}${pt.x.toFixed(2)},${pt.y.toFixed(2)} `
  }
  data = data + "Z"
  return data.trim()
}


function _featureToPathData(feature, project) {
  /*
   * Build a full SVG path `d` attribute for a GeoJSON Polygon or
   * MultiPolygon feature.
   *
   * :param feature: A GeoJSON Feature.
   * :param project: A projection function (lon, lat) -> {x, y}.
   * :returns: A path data string, or "" when geometry type is unsupported.
   */
  const geometry = feature.geometry
  if (geometry === null || geometry === undefined) {
    return ""
  }

  let segments = []

  if (geometry.type === "Polygon") {
    for (let ri = 0; ri < geometry.coordinates.length; ri = ri + 1) {
      segments.push(_ringToPathSegment(geometry.coordinates[ri], project))
    }
  } else if (geometry.type === "MultiPolygon") {
    for (let pi = 0; pi < geometry.coordinates.length; pi = pi + 1) {
      const polygon = geometry.coordinates[pi]
      for (let ri = 0; ri < polygon.length; ri = ri + 1) {
        segments.push(_ringToPathSegment(polygon[ri], project))
      }
    }
  }

  const data = segments.join(" ")
  return data
}


/* ─── color helpers ─────────────────────────────────────────────────────────── */

function _sequentialColor(normalizedValue, ramp) {
  /*
   * Map a normalised [0..1] value to a color stop in the ramp.
   *
   * :param normalizedValue: A value in [0, 1].
   * :param ramp:            Array of CSS color strings.
   * :returns: A CSS color string.
   */
  const palette = ramp || SEQ_RAMP
  const maxIndex = palette.length - 1
  const floatIndex = normalizedValue * maxIndex
  const index = Math.min(Math.floor(floatIndex), maxIndex)
  return palette[index]
}


/* ─── legend builders ───────────────────────────────────────────────────────── */

function _appendChoroplethLegend(parent, valueMin, valueMax, ramp, x, y) {
  /*
   * Draw a vertical sequential-color legend with CHOROPLETH_STEPS swatches.
   *
   * :param parent: The parent SVG group element.
   * :param valueMin: Domain minimum.
   * :param valueMax: Domain maximum.
   * :param ramp: Color ramp array.
   * :param x: Left edge of the legend.
   * :param y: Top edge of the legend.
   */
  const palette = ramp || SEQ_RAMP
  const steps = CHOROPLETH_STEPS
  const swatchH = LEGEND_SWATCH_SIZE + 2

  for (let step = 0; step < steps; step = step + 1) {
    const t = steps > 1 ? (steps - 1 - step) / (steps - 1) : 1
    const color = _sequentialColor(t, palette)
    const sy = y + step * swatchH

    parent.appendChild(svgEl("rect", {
      x: x, y: sy,
      width: LEGEND_SWATCH_SIZE, height: LEGEND_SWATCH_SIZE,
      fill: color,
      stroke: REGION_STROKE, "stroke-width": 0.5
    }, []))

    if (step === 0 || step === steps - 1) {
      const labelValue = step === 0 ? valueMax : valueMin
      parent.appendChild(svgEl("text", {
        x: x + LEGEND_SWATCH_SIZE + 4,
        y: sy + LEGEND_SWATCH_SIZE - 2,
        "font-size": 10,
        fill: "var(--mj-text-muted, #6b7280)"
      }, formatNumber(labelValue)))
    }
  }
}


function _appendSymbolLegend(parent, series, x, y) {
  /*
   * Draw a simple symbol-per-series legend.
   *
   * :param parent: The parent SVG group element.
   * :param series: Array of {name, color, symbol?}.
   * :param x: Left edge.
   * :param y: Top edge.
   */
  const rowH = LEGEND_SWATCH_SIZE + 4
  for (let si = 0; si < series.length; si = si + 1) {
    const row = series[si]
    const sy = y + si * rowH
    const cx = x + LEGEND_SWATCH_SIZE / 2
    const cy = sy + LEGEND_SWATCH_SIZE / 2

    parent.appendChild(svgEl("circle", {
      cx: cx, cy: cy,
      r: LEGEND_SWATCH_SIZE / 2,
      fill: row.color,
      opacity: 0.8
    }, []))

    parent.appendChild(svgEl("text", {
      x: x + LEGEND_SWATCH_SIZE + 4,
      y: sy + LEGEND_SWATCH_SIZE - 2,
      "font-size": 10,
      fill: "var(--mj-text-muted, #6b7280)"
    }, escapeHtml(row.name)))
  }
}


/* ─── base map layer ────────────────────────────────────────────────────────── */

function _drawBaseMap(plot, geojson, project) {
  /*
   * Draw GeoJSON polygon features as a grey base map layer.
   *
   * :param plot: The SVG group to append paths into.
   * :param geojson: A GeoJSON FeatureCollection.
   * :param project: Projection function.
   */
  if (geojson === null || geojson === undefined) {
    return
  }
  const features = geojson.features || []
  for (let fi = 0; fi < features.length; fi = fi + 1) {
    const feature = features[fi]
    const pathData = _featureToPathData(feature, project)
    if (pathData === "") {
      continue
    }
    plot.appendChild(svgEl("path", {
      d: pathData,
      fill: BASE_MAP_FILL,
      stroke: BASE_MAP_STROKE,
      "stroke-width": 0.5,
      "stroke-linejoin": "round"
    }, []))
  }
}


/* ─── symbol drawing helper ─────────────────────────────────────────────────── */

function _symbolPath(symbolType, cx, cy, halfSize) {
  /*
   * Return a minimal SVG path `d` for a non-circle symbol centred at (cx, cy)
   * with the given half-size.  Used for square, triangle, and diamond symbols.
   *
   * :param symbolType: "square" | "triangle" | "diamond".
   * :param cx: Centre x.
   * :param cy: Centre y.
   * :param halfSize: Half the outer dimension.
   * :returns: SVG path data string, or null for unsupported types.
   */
  const h = halfSize
  if (symbolType === "square") {
    return `M${cx - h},${cy - h} L${cx + h},${cy - h} L${cx + h},${cy + h} L${cx - h},${cy + h} Z`
  }
  if (symbolType === "triangle") {
    return `M${cx},${cy - h} L${cx + h},${cy + h} L${cx - h},${cy + h} Z`
  }
  if (symbolType === "diamond") {
    return `M${cx},${cy - h} L${cx + h},${cy} L${cx},${cy + h} L${cx - h},${cy} Z`
  }
  return null
}


function _makeInteractive(element, eventName, detail, emit) {
  /*
   * Attach accessibility attributes and keyboard/click interaction to an
   * SVG element, following the bar.js pattern.
   *
   * :param element:   The SVG element.
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
}


/* ─── choropleth renderer ───────────────────────────────────────────────────── */

function _renderChoropleth(ctx) {
  /*
   * Render a choropleth map: filled region polygons from GeoJSON, colored by
   * value through a sequential ramp.
   *
   * :param ctx: Renderer context.
   * :returns: A <g> SVGElement.
   */
  const raw = ctx.raw
  const root = svgEl("g", { part: "plot" }, [])

  const regions = (raw && Array.isArray(raw.regions)) ? raw.regions : []
  const geojson = (raw && raw.geojson) ? raw.geojson : null

  if (regions.length === 0 && geojson === null) {
    return root
  }

  const legendAreaW = regions.length > 0 ? LEGEND_W : 0
  const drawW = Math.max(ctx.width - MARGIN * 2 - legendAreaW, 10)
  const drawH = Math.max(ctx.height - MARGIN * 2, 10)

  /* Build projection from GeoJSON, or fall back to world bounds. */
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

  /* Build value lookup and domain. */
  const valueMap = {}
  let valMin = Infinity
  let valMax = -Infinity
  for (let i = 0; i < regions.length; i = i + 1) {
    const region = regions[i]
    if (typeof region.value === "number") {
      valueMap[region.id] = region.value
      if (region.value < valMin) { valMin = region.value }
      if (region.value > valMax) { valMax = region.value }
    }
  }
  if (valMin === Infinity) {
    valMin = 0
    valMax = 1
  }
  if (valMin === valMax) {
    valMax = valMin + 1
  }
  const valScale = linearScale([valMin, valMax], [0, 1])

  /* Draw regions. */
  const features = geojson !== null ? (geojson.features || []) : []
  for (let fi = 0; fi < features.length; fi = fi + 1) {
    const feature = features[fi]
    const featureId = (feature.properties && feature.properties.id !== undefined)
      ? String(feature.properties.id)
      : String(fi)
    const pathData = _featureToPathData(feature, project)
    if (pathData === "") {
      continue
    }

    const value = valueMap[featureId]
    const hasValue = value !== undefined
    const fill = hasValue
      ? _sequentialColor(valScale(value), SEQ_RAMP)
      : NO_DATA_FILL

    const regionLabel = (feature.properties && feature.properties.name)
      ? feature.properties.name
      : featureId
    const tooltipText = hasValue
      ? `${regionLabel}: ${formatNumber(value)}`
      : regionLabel

    const path = svgEl("path", {
      d: pathData,
      fill: fill,
      stroke: REGION_STROKE,
      "stroke-width": 0.75,
      "stroke-linejoin": "round",
      part: "region",
      "aria-label": tooltipText,
      cursor: "pointer"
    }, [svgEl("title", null, tooltipText)])

    _makeInteractive(path, "mj-chart-select", {
      id: featureId, label: regionLabel, value: value
    }, ctx.emit)

    plot.appendChild(path)
  }

  /* When no GeoJSON features, render markers as circles if available. */
  if (features.length === 0 && regions.length > 0) {
    for (let ri = 0; ri < regions.length; ri = ri + 1) {
      const region = regions[ri]
      if (region.lat === undefined || region.lon === undefined) {
        continue
      }
      const pt = project(region.lon, region.lat)
      const value = typeof region.value === "number" ? region.value : 0
      const fill = _sequentialColor(valScale(value), SEQ_RAMP)
      const label = region.label || region.id
      const tooltipText = `${label}: ${formatNumber(value)}`

      const circle = svgEl("circle", {
        cx: pt.x, cy: pt.y, r: 8,
        fill: fill, stroke: REGION_STROKE, "stroke-width": 1,
        part: "region", "aria-label": tooltipText, cursor: "pointer"
      }, [svgEl("title", null, tooltipText)])

      _makeInteractive(circle, "mj-chart-select", {
        id: region.id, label: label, value: value
      }, ctx.emit)

      plot.appendChild(circle)
    }
  }

  /* Legend. */
  if (regions.length > 0) {
    const legendX = drawW + MARGIN + 4
    _appendChoroplethLegend(plot, valMin, valMax, SEQ_RAMP, legendX, 0)
  }

  return root
}


/* ─── symbol / bubble / proportional-symbol renderer ───────────────────────── */

function _renderSymbolMap(ctx) {
  /*
   * Render a symbol map, bubble map, or proportional-symbol map.
   * Points from raw.series[].points or raw.markers are projected and drawn
   * as circles or shaped symbols.  A GeoJSON base map is drawn underneath
   * when raw.geojson is supplied.
   *
   * :param ctx: Renderer context.
   * :returns: A <g> SVGElement.
   */
  const raw = ctx.raw
  const root = svgEl("g", { part: "plot" }, [])

  /* Collect all points from series or flat markers array. */
  const seriesData = []
  if (raw && Array.isArray(raw.series) && raw.series.length > 0) {
    for (let si = 0; si < raw.series.length; si = si + 1) {
      const s = raw.series[si]
      const points = Array.isArray(s.points) ? s.points : []
      seriesData.push({
        name: s.name || `Series ${si + 1}`,
        symbol: s.symbol || "circle",
        color: ctx.colorFor(si),
        points: points
      })
    }
  } else if (raw && Array.isArray(raw.markers) && raw.markers.length > 0) {
    const pts = raw.markers.map((m) => ({
      id: m.id || m.label,
      label: m.label || m.id,
      lon: m.lng !== undefined ? m.lng : m.lon,
      lat: m.lat,
      size: m.value
    }))
    seriesData.push({
      name: "Markers",
      symbol: "circle",
      color: ctx.colorFor(0),
      points: pts
    })
  }

  if (seriesData.length === 0) {
    return root
  }

  const geojson = (raw && raw.geojson) ? raw.geojson : null

  const legendAreaW = LEGEND_W
  const drawW = Math.max(ctx.width - MARGIN * 2 - legendAreaW, 10)
  const drawH = Math.max(ctx.height - MARGIN * 2, 10)

  /* Collect all points to derive projection bounds when no GeoJSON. */
  const allPoints = []
  for (let si = 0; si < seriesData.length; si = si + 1) {
    const pts = seriesData[si].points
    for (let pi = 0; pi < pts.length; pi = pi + 1) {
      allPoints.push(pts[pi])
    }
  }

  const project = geojson !== null
    ? _makeProjection(geojson, drawW, drawH)
    : _markerProjection(allPoints, drawW, drawH)

  const plot = svgEl("g", { transform: `translate(${MARGIN},${MARGIN})` }, [])
  root.appendChild(plot)

  /* Base map. */
  _drawBaseMap(plot, geojson, project)

  /* Compute size scale from all `size` values, for bubble/proportional mode. */
  const sizeScaleMode = ctx.attrs("size-scale", "none")
  let allSizes = []
  for (let si = 0; si < seriesData.length; si = si + 1) {
    const pts = seriesData[si].points
    for (let pi = 0; pi < pts.length; pi = pi + 1) {
      const sz = pts[pi].size
      if (typeof sz === "number" && sz > 0) {
        allSizes.push(sz)
      }
    }
  }

  let sizeScale = null
  if (allSizes.length > 0 && sizeScaleMode === "sqrt") {
    let sizeMin = allSizes[0]
    let sizeMax = allSizes[0]
    for (let i = 0; i < allSizes.length; i = i + 1) {
      if (allSizes[i] < sizeMin) { sizeMin = allSizes[i] }
      if (allSizes[i] > sizeMax) { sizeMax = allSizes[i] }
    }
    const minRadius = Number(ctx.attrs("min-radius", "4"))
    const maxRadius = Number(ctx.attrs("max-radius", "28"))
    sizeScale = sqrtScale([sizeMin, sizeMax], [minRadius, maxRadius])
  }

  /* Draw each series — bubbles rendered largest-first (painter's order). */
  for (let si = 0; si < seriesData.length; si = si + 1) {
    const series = seriesData[si]
    const symbolType = series.symbol
    const color = series.color

    let pts = series.points.slice()
    if (sizeScale !== null) {
      pts.sort((a, b) => {
        const sa = typeof a.size === "number" ? a.size : 0
        const sb = typeof b.size === "number" ? b.size : 0
        return sb - sa
      })
    }

    for (let pi = 0; pi < pts.length; pi = pi + 1) {
      const pt = pts[pi]
      const lon = pt.lon !== undefined ? pt.lon : (pt.lng !== undefined ? pt.lng : null)
      const lat = pt.lat !== undefined ? pt.lat : null
      if (lon === null || lat === null) {
        continue
      }

      const projected = project(lon, lat)
      const px = projected.x
      const py = projected.y

      const radius = sizeScale !== null && typeof pt.size === "number"
        ? sizeScale(pt.size)
        : 6
      const label = pt.label || pt.id || `(${lon}, ${lat})`
      const tooltipText = typeof pt.size === "number"
        ? `${label}: ${formatNumber(pt.size)}`
        : label

      let mark = null

      if (symbolType === "circle" || symbolType === undefined) {
        mark = svgEl("circle", {
          cx: px, cy: py, r: radius,
          fill: color, "fill-opacity": 0.75,
          stroke: "var(--mj-surface, #ffffff)", "stroke-width": 1,
          part: "symbol",
          "aria-label": tooltipText,
          cursor: "pointer"
        }, [svgEl("title", null, tooltipText)])
      } else {
        const pathData = _symbolPath(symbolType, px, py, radius)
        if (pathData !== null) {
          mark = svgEl("path", {
            d: pathData,
            fill: color, "fill-opacity": 0.75,
            stroke: "var(--mj-surface, #ffffff)", "stroke-width": 1,
            part: "symbol",
            "aria-label": tooltipText,
            cursor: "pointer"
          }, [svgEl("title", null, tooltipText)])
        }
      }

      if (mark !== null) {
        _makeInteractive(mark, "mj-chart-select", {
          id: pt.id, label: label,
          lon: lon, lat: lat,
          value: pt.size !== undefined ? pt.size : null,
          series: series.name
        }, ctx.emit)
        plot.appendChild(mark)
      }

      /* Optional point label. */
      if (ctx.attrs("show-labels", "false") === "true" && pt.label) {
        plot.appendChild(svgEl("text", {
          x: px, y: py - radius - 3,
          "text-anchor": "middle",
          "font-size": 9,
          fill: "var(--mj-text, #14181f)"
        }, escapeHtml(pt.label)))
      }
    }
  }

  /* Legend. */
  const legendX = drawW + MARGIN + 4
  const legendSeries = seriesData.map((s) => ({ name: s.name, color: s.color, symbol: s.symbol }))
  _appendSymbolLegend(plot, legendSeries, legendX, 0)

  return root
}


/* ─── hex-map renderer ──────────────────────────────────────────────────────── */

function _hexPoints(cx, cy, radius, orientation) {
  /*
   * Compute the six corner points of a regular hexagon as an SVG points string.
   *
   * :param cx:          Centre x.
   * :param cy:          Centre y.
   * :param radius:      Circumradius.
   * :param orientation: "flat" | "pointy"
   * :returns: SVG polygon points string.
   */
  const points = []
  const startAngle = orientation === "pointy" ? 0 : Math.PI / 6
  for (let corner = 0; corner < 6; corner = corner + 1) {
    const angle = startAngle + corner * (Math.PI / 3)
    const x = cx + radius * Math.cos(angle)
    const y = cy + radius * Math.sin(angle)
    points.push(`${x.toFixed(2)},${y.toFixed(2)}`)
  }
  return points.join(" ")
}


function _axialToPixel(q, r, radius, orientation) {
  /*
   * Convert axial hex grid coordinates (q, r) to pixel centre (x, y).
   *
   * :param q:           Column.
   * :param r:           Row.
   * :param radius:      Circumradius.
   * :param orientation: "flat" | "pointy"
   * :returns: { x, y }
   */
  let x = 0
  let y = 0
  if (orientation === "flat") {
    x = radius * 1.5 * q
    y = radius * Math.sqrt(3) * (r + q / 2)
  } else {
    x = radius * Math.sqrt(3) * (q + r / 2)
    y = radius * 1.5 * r
  }
  return { x: x, y: y }
}


function _renderHexMap(ctx) {
  /*
   * Render a hex-map (equal-area hexagonal tile map) or square tile-grid map.
   * Each region maps to a hex tile coloured by value.
   *
   * :param ctx: Renderer context.
   * :returns: A <g> SVGElement.
   */
  const raw = ctx.raw
  const root = svgEl("g", { part: "plot" }, [])

  const regions = (raw && Array.isArray(raw.regions)) ? raw.regions : []
  /* layout: object mapping id -> {q, r}  (pre-computed hex grid positions) */
  const layout = (raw && typeof raw.layout === "object") ? raw.layout : {}

  if (regions.length === 0) {
    return root
  }

  const hexOrientation = ctx.attrs("hex-orientation", "flat")
  const shapePref = ctx.attrs("shape", "hex")
  const useTiles = shapePref === "square"

  /* Build value lookup and domain. */
  const valueMap = {}
  let valMin = Infinity
  let valMax = -Infinity
  for (let i = 0; i < regions.length; i = i + 1) {
    const region = regions[i]
    if (typeof region.value === "number") {
      valueMap[region.id] = region.value
      if (region.value < valMin) { valMin = region.value }
      if (region.value > valMax) { valMax = region.value }
    }
  }
  if (valMin === Infinity) { valMin = 0; valMax = 1 }
  if (valMin === valMax) { valMax = valMin + 1 }
  const valScale = linearScale([valMin, valMax], [0, 1])

  /* Compute bounding box of axial positions. */
  let qMin = Infinity; let qMax = -Infinity
  let rMin = Infinity; let rMax = -Infinity
  for (let i = 0; i < regions.length; i = i + 1) {
    const id = regions[i].id
    const pos = layout[id]
    if (pos === undefined) { continue }
    if (pos.q < qMin) { qMin = pos.q }
    if (pos.q > qMax) { qMax = pos.q }
    if (pos.r < rMin) { rMin = pos.r }
    if (pos.r > rMax) { rMax = pos.r }
  }
  if (qMin === Infinity) {
    /* No layout provided: auto-layout in a single row. */
    for (let i = 0; i < regions.length; i = i + 1) {
      layout[regions[i].id] = { q: i, r: 0 }
    }
    qMin = 0; qMax = regions.length - 1; rMin = 0; rMax = 0
  }

  const legendAreaW = LEGEND_W
  const drawW = Math.max(ctx.width - MARGIN * 2 - legendAreaW, 10)
  const drawH = Math.max(ctx.height - MARGIN * 2, 10)

  /* Determine hex radius to fill the drawing area. */
  const qSpan = (qMax - qMin) + 1
  const rSpan = (rMax - rMin) + 1
  let radius = 0
  if (useTiles === false) {
    if (hexOrientation === "flat") {
      radius = Math.min(
        drawW / (qSpan * 1.5 + 0.5) / 1,
        drawH / ((rSpan + 0.5) * Math.sqrt(3))
      )
    } else {
      radius = Math.min(
        drawW / ((qSpan + 0.5) * Math.sqrt(3)),
        drawH / (rSpan * 1.5 + 0.5)
      )
    }
    radius = Math.max(radius * 0.92, 4)
  } else {
    radius = Math.min(drawW / qSpan, drawH / rSpan) * 0.46
  }

  /* Origin offset so grid is centred in the draw area. */
  const origin = _axialToPixel(qMin, rMin, radius, hexOrientation)
  const lastPos = _axialToPixel(qMax, rMax, radius, hexOrientation)
  const offsetX = MARGIN + (drawW - (lastPos.x - origin.x)) / 2 - origin.x
  const offsetY = MARGIN + (drawH - (lastPos.y - origin.y)) / 2 - origin.y

  const plot = svgEl("g", { transform: `translate(${offsetX},${offsetY})` }, [])
  root.appendChild(plot)

  for (let i = 0; i < regions.length; i = i + 1) {
    const region = regions[i]
    const pos = layout[region.id]
    if (pos === undefined) { continue }

    const centre = _axialToPixel(pos.q, pos.r, radius, hexOrientation)
    const cx = centre.x
    const cy = centre.y
    const value = valueMap[region.id]
    const hasValue = value !== undefined
    const fill = hasValue ? _sequentialColor(valScale(value), SEQ_RAMP) : NO_DATA_FILL
    const labelText = region.label || region.id
    const tooltipText = hasValue
      ? `${labelText}: ${formatNumber(value)}`
      : labelText

    let mark = null
    if (useTiles === false) {
      const pts = _hexPoints(cx, cy, radius * 0.97, hexOrientation)
      mark = svgEl("polygon", {
        points: pts,
        fill: fill,
        stroke: "var(--mj-surface, #ffffff)", "stroke-width": 1,
        part: "region",
        "aria-label": tooltipText,
        cursor: "pointer"
      }, [svgEl("title", null, tooltipText)])
    } else {
      const tileW = radius * 2
      mark = svgEl("rect", {
        x: cx - radius, y: cy - radius,
        width: tileW, height: tileW,
        fill: fill,
        stroke: "var(--mj-surface, #ffffff)", "stroke-width": 1,
        part: "region",
        "aria-label": tooltipText,
        cursor: "pointer"
      }, [svgEl("title", null, tooltipText)])
    }

    _makeInteractive(mark, "mj-chart-select", {
      id: region.id, label: labelText, value: value
    }, ctx.emit)
    plot.appendChild(mark)

    /* Label inside the tile. */
    const fontSize = Math.min(radius * 0.5, 11)
    if (fontSize >= 7) {
      plot.appendChild(svgEl("text", {
        x: cx, y: cy + fontSize * 0.35,
        "text-anchor": "middle",
        "font-size": fontSize,
        fill: "var(--mj-text, #14181f)",
        "pointer-events": "none"
      }, escapeHtml(labelText)))
    }
  }

  /* Legend. */
  const legendX = offsetX + (lastPos.x - origin.x) + radius + 8
  _appendChoroplethLegend(root, valMin, valMax, SEQ_RAMP, legendX, MARGIN)

  return root
}


/* ─── dispatch & registration ───────────────────────────────────────────────── */

export function render(ctx) {
  /*
   * Top-level geographic map renderer dispatcher.
   *
   * Delegates to the appropriate sub-renderer based on ctx.model.meta.type
   * (falling back to context.attrs("type", "choropleth")).
   *
   * :param ctx: Renderer context.
   * :returns: A <g> SVGElement.
   */
  const chartType = (ctx.model && ctx.model.meta && ctx.model.meta.type)
    ? ctx.model.meta.type
    : ctx.attrs("type", "choropleth")

  if (chartType === "symbol-map" ||
      chartType === "bubble-map" ||
      chartType === "proportional-symbol-map") {
    const root = _renderSymbolMap(ctx)
    return root
  }

  if (chartType === "hex-map" || chartType === "tile-grid-map") {
    const root = _renderHexMap(ctx)
    return root
  }

  /* Default: choropleth */
  const root = _renderChoropleth(ctx)
  return root
}


registerRenderer("choropleth", render)
registerRenderer("symbol-map", render)
registerRenderer("bubble-map", render)
registerRenderer("proportional-symbol-map", render)
registerRenderer("hex-map", render)
registerRenderer("tile-grid-map", render)
