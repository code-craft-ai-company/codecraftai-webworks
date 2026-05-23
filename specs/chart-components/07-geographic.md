# Geographic & Map Charts

> Catalog of chart types in this category for the automojo-webworks SVG chart
> library. Architecture, the coordinated-element model, the part components,
> the JSON contract, and phasing are defined in `../../chart-components-plan.md`
> and are not repeated here.

All map renderers project supplied GeoJSON or TopoJSON geometry into SVG
`<path>` elements using a pure-SVG projection pipeline in `charts/core/geo/`.
No external mapping library is used. A `topology`/`geojson` reference in the
JSON data provides the geometry; region `id` values link geometry features to
data values. Orientation is `n/a` for every chart in this category — maps have
no meaningful horizontal/vertical swap.

---

### Choropleth Map  *(filled map, area map)*

- **Renderer / `type`:** `choropleth` — **Primary renderer**
- **Controller:** `<mj-chart type="choropleth" ...>`
- **Purpose:** Visualise a single quantitative value per region by filling each
  geographic polygon with a color drawn from a sequential or diverging color
  scale — best for showing spatial distribution of a measure (population
  density, election results, sales territory).
- **Decomposition:** `mj-chart-plot`, `mj-chart-legend` (continuous color
  ramp), `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`,
  `mj-chart-annotation`.
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Regional Sales", "projection": "mercator" },
    "topology": "/geo/us-states.topojson",
    "regions": [
      { "id": "CA", "value": 4200 },
      { "id": "TX", "value": 3100 }
    ],
    "series": [{ "name": "Revenue", "color-scale": "sequential-blue" }]
  }
  ```
  `topology` (TopoJSON URL) or `geojson` (GeoJSON URL or inline
  `FeatureCollection`) provides geometry. Each `regions[]` entry matches a
  feature by its `id` property. The `projection` meta field selects the SVG
  projection (`mercator`, `equal-area`, `orthographic`, `natural-earth`);
  defaults to `mercator`.
- **SVG primitives:** `<path>` (one per region polygon/multipolygon),
  `<g>` (layer groups for base, data, graticule, labels), `<text>` (region
  labels, optional), `<line>` (graticule lines, optional).
- **Orientation:** `n/a`
- **Variants / modes:** none — choropleth is a distinct primary renderer.
- **Phase:** P4
- **Notes:** Uses a `sequential` or `diverging` color scale from
  `charts/core/scales.js` mapped over the value domain. Regions with no
  matching data value receive a neutral fill from design tokens
  (`--mj-chart-geo-no-data`). The accessible data-table lists region name and
  value; the SVG carries `role="img"` with a generated summary. Interactive
  click/hover emits `mj-chart-select` with the region `id` and value.

---

### Symbol Map  *(point map, dot map)*

- **Renderer / `type`:** `symbol-map` — **Primary renderer**
- **Controller:** `<mj-chart type="symbol-map" ...>`
- **Purpose:** Plot discrete point locations on a map using a consistent symbol
  at each coordinate — best for showing where events, facilities, or incidents
  occur without encoding magnitude.
- **Decomposition:** `mj-chart-plot`, `mj-chart-legend` (symbol/color key),
  `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`,
  `mj-chart-annotation`.
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Store Locations", "projection": "mercator" },
    "topology": "/geo/world.topojson",
    "series": [
      {
        "name": "Retail",
        "points": [
          { "id": "NYC", "label": "New York", "lon": -74.006, "lat": 40.713 },
          { "id": "LAX", "label": "Los Angeles", "lon": -118.244, "lat": 34.052 }
        ]
      }
    ]
  }
  ```
  Each `series[].points[]` entry supplies a `lon`/`lat` pair (decimal degrees)
  and an optional `label`. The renderer projects the coordinate pair to SVG
  pixel space via the declared projection.
- **SVG primitives:** `<path>` (base map polygons), `<circle>` or `<use>`
  (symbol at each point), `<text>` (optional point labels), `<g>`.
- **Orientation:** `n/a`
- **Variants / modes:** Bubble Map (`size` attribute on each point, uses `sqrt`
  size scale — see Bubble Map entry), Proportional Symbol Map (same `size`
  mechanism, different framing — see Proportional Symbol Map entry).
- **Phase:** P4
- **Notes:** Symbol shape is controlled by `series[].symbol`
  (`circle|square|triangle|diamond`); defaults to `circle`. Multiple series
  produce differently-colored and/or shaped symbol sets, each togglable via
  `mj-chart-legend`. The base map layer (country/region polygons) uses the
  same path-projection pipeline as `choropleth`.

---

### Bubble Map  *(graduated symbol map)*

- **Renderer / `type`:** `symbol-map` — **Variant of `symbol-map`**
- **Controller:** `<mj-chart type="symbol-map" size-scale="sqrt" ...>`
- **Purpose:** Show magnitude at point locations by scaling a circle's area
  proportionally to a value — best for comparing quantities across geographic
  sites where both location and relative size matter.
- **Decomposition:** `mj-chart-plot`, `mj-chart-legend` (size legend + color
  key), `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`,
  `mj-chart-annotation`.
- **JSON shape:**
  ```json
  {
    "meta": { "title": "City Population", "projection": "mercator" },
    "topology": "/geo/world.topojson",
    "series": [
      {
        "name": "Population 2025",
        "points": [
          { "id": "TYO", "label": "Tokyo",    "lon": 139.69, "lat": 35.69, "size": 37400068 },
          { "id": "DEL", "label": "Delhi",    "lon": 77.10,  "lat": 28.70, "size": 32941000 }
        ]
      }
    ]
  }
  ```
  Same envelope as Symbol Map with a `size` field on each point. The renderer
  maps `size` through a `sqrt` scale (area proportional to value) to a pixel
  radius, clamped by `min-radius` / `max-radius` controller attributes.
- **SVG primitives:** `<path>` (base map), `<circle>` (scaled bubble per
  point), `<text>` (optional labels), `<g>`.
- **Orientation:** `n/a`
- **Variants / modes:** activates the `size-scale="sqrt"` mode of `symbol-map`;
  Proportional Symbol Map is the same renderer with non-circular symbols.
- **Phase:** P4
- **Notes:** Bubbles are rendered largest-first (painter's order) so smaller
  bubbles are not hidden behind larger ones. The size legend shows a set of
  representative radius circles with their corresponding values. Color may
  optionally encode a second variable via an `ordinal-color` scale.

---

### Heat Map / Density Map  *(geographic density, concentration map)*

- **Renderer / `type`:** `geo-heatmap` — **Primary renderer**
- **Controller:** `<mj-chart type="geo-heatmap" ...>`
- **Purpose:** Reveal spatial concentration or intensity across a continuous
  surface — best for showing where events cluster in geographic space (foot
  traffic, incident density, signal strength).
- **Decomposition:** `mj-chart-plot`, `mj-chart-legend` (continuous color
  ramp), `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`.
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Incident Density", "projection": "mercator" },
    "topology": "/geo/city-boundary.topojson",
    "series": [
      {
        "name": "Incidents",
        "points": [
          { "lon": -87.629, "lat": 41.878, "weight": 1 },
          { "lon": -87.631, "lat": 41.875, "weight": 3 }
        ]
      }
    ]
  }
  ```
  Each `points[]` entry has a `lon`/`lat` and an optional `weight` (defaults to
  1). The renderer computes a kernel density estimate on the projected pixel
  grid and renders the result as a color ramp using SVG `<image>` (rasterised
  density grid) or a set of `<path>` contour bands.
- **SVG primitives:** `<path>` (base map, optional clip boundary, contour
  bands), `<image>` (rasterised density bitmap, embedded as data URI),
  `<g>`.
- **Orientation:** `n/a`
- **Variants / modes:** Contour rendering mode (SVG `<path>` bands) vs raster
  mode (`<image>`) selected by `render-mode="contour|raster"` attribute.
- **Phase:** P4
- **Notes:** The kernel density estimate is computed in JavaScript over the
  projected pixel coordinates using a Gaussian kernel with configurable
  bandwidth (`bandwidth` attribute). Raster mode writes pixel values into an
  `OffscreenCanvas` then embeds the result as a base-64 PNG `<image>`. Contour
  mode produces iso-level `<path>` elements (shares logic with the
  `isoline` renderer). Clipping to a topology boundary is applied via
  `<clipPath>`.

---

### Cartogram  *(value-distorted map, area cartogram)*

- **Renderer / `type`:** `cartogram` — **Primary renderer**
- **Controller:** `<mj-chart type="cartogram" ...>`
- **Purpose:** Distort geographic region shapes so that each area is
  proportional to a data value rather than physical size — best for making
  value differences visually obvious when physical area misleads (e.g. electoral
  vote cartograms).
- **Decomposition:** `mj-chart-plot`, `mj-chart-legend` (color key),
  `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`,
  `mj-chart-annotation`.
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Electoral Votes Cartogram" },
    "topology": "/geo/us-states.topojson",
    "regions": [
      { "id": "CA", "value": 54, "color": "optional" },
      { "id": "TX", "value": 40 }
    ],
    "series": [{ "name": "Electoral Votes" }]
  }
  ```
  Same `regions[]` shape as `choropleth`. The `value` drives the distortion
  target area for each polygon; an iterative Gastner–Newman or Dougenik–Sheehan
  algorithm resizes polygons in JavaScript, then the resulting coordinates are
  projected to SVG paths.
- **SVG primitives:** `<path>` (one distorted polygon per region), `<text>`
  (region labels), `<g>`.
- **Orientation:** `n/a`
- **Variants / modes:** Dorling cartogram variant (regions replaced by
  scaled circles, no polygon distortion) selected by `style="dorling"`;
  uses `<circle>` instead of `<path>` for region marks.
- **Phase:** P4
- **Notes:** Cartogram layout is computationally expensive; the iterative
  algorithm runs in a `Worker` thread and posts completed path data back to the
  renderer. During computation the chart shows the un-distorted choropleth as a
  loading state. The `style="dorling"` variant skips distortion and uses
  `sqrt`-scaled circles positioned at region centroids, reusing the
  `symbol-map` circle-drawing logic.

---

### Flow Map  *(origin-destination map, migration map)*

- **Renderer / `type`:** `flow-map` — **Primary renderer**
- **Controller:** `<mj-chart type="flow-map" ...>`
- **Purpose:** Show movement, migration, or transfers between geographic
  locations using directed arcs or tapered lines — best for visualising
  trade flows, commuter patterns, or data-packet routing.
- **Decomposition:** `mj-chart-plot`, `mj-chart-legend` (volume/color key),
  `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`,
  `mj-chart-annotation`.
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Migration Flows 2024", "projection": "natural-earth" },
    "topology": "/geo/world.topojson",
    "nodes": [
      { "id": "MEX", "lon": -102.55, "lat": 23.63 },
      { "id": "USA", "lon":  -95.71, "lat": 37.09 }
    ],
    "links": [
      { "source": "MEX", "target": "USA", "value": 250000 }
    ]
  }
  ```
  `nodes[]` provide named geographic anchors with `lon`/`lat`. `links[]` follow
  the flow/network family shape from plan §3.4. The renderer draws a curved arc
  between each origin-destination pair; line width or taper encodes `value`.
- **SVG primitives:** `<path>` (curved arc per flow, base map polygons),
  `<circle>` (node markers), `<polygon>` (arrowhead), `<text>` (node labels),
  `<g>`.
- **Orientation:** `n/a`
- **Variants / modes:** Straight-line mode (`arc="straight"`) draws `<line>`
  segments instead of cubic-Bézier arcs. Tapered mode (`taper="true"`, default)
  varies stroke width from source to destination proportional to `value`.
- **Phase:** P4
- **Notes:** Arc curvature direction (clockwise/counter-clockwise) is chosen
  automatically to prevent self-intersecting arcs between bidirectional pairs.
  When many flows share a common hub the renderer optionally bundles arcs
  (`bundling="true"`) using a force-directed edge-bundling pass. Arrowheads are
  rendered as `<polygon>` markers appended near the destination centroid.

---

### Route Map  *(path map, travel map, network route map)*

- **Renderer / `type`:** `route-map` — **Primary renderer**
- **Controller:** `<mj-chart type="route-map" ...>`
- **Purpose:** Render fixed paths or itineraries on a map — best for showing
  transport routes, delivery corridors, or multi-stop journeys where the exact
  line geometry (not a free-form arc) matters.
- **Decomposition:** `mj-chart-plot`, `mj-chart-legend` (route/series key),
  `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`,
  `mj-chart-annotation`.
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Airline Routes", "projection": "mercator" },
    "topology": "/geo/world.topojson",
    "series": [
      {
        "name": "Trans-Pacific",
        "routes": [
          {
            "id": "LAX-NRT",
            "waypoints": [
              { "lon": -118.408, "lat": 33.943 },
              { "lon":  139.781, "lat": 35.553 }
            ]
          }
        ]
      }
    ]
  }
  ```
  Each `series[].routes[]` entry has an `id` and an ordered `waypoints[]`
  array of `lon`/`lat` pairs. The renderer projects each waypoint and draws a
  polyline. Alternatively a route may supply a `geojson` LineString inline for
  pre-computed geometry (e.g. road-following paths).
- **SVG primitives:** `<path>` (polyline per route, base map polygons),
  `<circle>` (waypoint stops), `<polygon>` (directional arrowhead, optional),
  `<text>` (stop labels), `<g>`.
- **Orientation:** `n/a`
- **Variants / modes:** `style="great-circle"` interpolates waypoints along the
  geodesic and renders a smooth `<path>` curve rather than straight segments.
- **Phase:** P4
- **Notes:** Routes within the same series share a color from the design-token
  color ramp; `series[].color` overrides. Stop markers at each waypoint are
  toggled by `show-stops="true"` attribute. When a route supplies an inline
  GeoJSON geometry, the coordinates are projected directly using the same
  projection function as the base map, ensuring alignment.

---

### Isoline / Contour Map  *(contour map, isobar map, isochrone map)*

- **Renderer / `type`:** `isoline` — **Primary renderer**
- **Controller:** `<mj-chart type="isoline" ...>`
- **Purpose:** Depict a continuous geographic variable as a set of lines
  connecting points of equal value — best for elevation, atmospheric pressure,
  travel-time zones (isochrones), or temperature fields.
- **Decomposition:** `mj-chart-plot`, `mj-chart-legend` (level/color key),
  `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`,
  `mj-chart-annotation`.
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Elevation Contours", "projection": "mercator" },
    "topology": "/geo/terrain-boundary.topojson",
    "series": [
      {
        "name": "Elevation (m)",
        "grid": {
          "lon-min": -125.0, "lon-max": -66.9,
          "lat-min":   24.4, "lat-max":  49.4,
          "cols": 200, "rows": 150,
          "values": [ 0, 12, 340, 820, "..." ]
        },
        "levels": [200, 500, 1000, 2000, 3000]
      }
    ]
  }
  ```
  `grid` supplies a regular lon/lat raster with `cols × rows` scalar `values`
  in row-major order. `levels` specifies the iso-values at which contour lines
  are traced. Alternatively `geojson` may provide pre-computed contour
  MultiLineString/MultiPolygon features.
- **SVG primitives:** `<path>` (contour line per iso-level, base map polygons,
  filled contour bands), `<text>` (level labels on contour lines), `<g>`.
- **Orientation:** `n/a`
- **Variants / modes:** `style="lines"` (default) draws unfilled contour lines;
  `style="filled"` draws filled contour bands between consecutive levels using
  closed `<path>` polygons and a sequential color scale. Shares contour-tracing
  logic with the `geo-heatmap` contour render mode.
- **Phase:** P4
- **Notes:** Contour tracing uses the marching-squares algorithm implemented in
  JavaScript. The resulting polyline coordinates are in grid space; the renderer
  maps them through the geographic projection (lon/lat interpolation) before
  drawing. Label placement rotates `<text>` elements to follow the contour
  slope.

---

### Hex Map  *(hexagonal tile map, equal-area hex cartogram)*

- **Renderer / `type`:** `hex-map` — **Primary renderer**
- **Controller:** `<mj-chart type="hex-map" ...>`
- **Purpose:** Replace geographic regions with equal-sized hexagonal tiles so
  that every region receives the same visual weight regardless of physical area
  — best for comparing values across regions when geographic size differences
  would distort perception.
- **Decomposition:** `mj-chart-plot`, `mj-chart-legend` (color or size key),
  `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`,
  `mj-chart-annotation`.
- **JSON shape:**
  ```json
  {
    "meta": { "title": "US States Hex Map" },
    "layout": "/geo/us-states-hexgrid.json",
    "regions": [
      { "id": "CA", "label": "CA", "value": 39538223 },
      { "id": "TX", "label": "TX", "value": 29145505 }
    ],
    "series": [{ "name": "Population", "color-scale": "sequential-green" }]
  }
  ```
  `layout` references a pre-computed hexgrid layout file that maps each region
  `id` to a hex grid coordinate `{ "q": n, "r": n }`. Values are mapped to a
  color scale (sequential/diverging) or left as a single-color series. No
  geographic projection is applied — hex positions are computed directly from
  axial grid coordinates.
- **SVG primitives:** `<polygon>` (regular hexagon per region), `<text>`
  (region label and optional value inside hex), `<g>`.
- **Orientation:** `n/a`
- **Variants / modes:** `shape="square"` switches to a square tile grid
  (tile map); uses `<rect>` instead of `<polygon>`.
- **Phase:** P4
- **Notes:** Hexagon geometry is calculated from axial (q, r) coordinates
  converted to pixel (x, y) using flat-top or pointy-top orientation
  (`hex-orientation="flat|pointy"` attribute, default `flat`). The layout file
  is a JSON object mapping region `id` to `{ "q", "r" }` — it is authored once
  per territory set and shipped as a static asset. Color fill is driven by the
  same `sequential`/`diverging` scale used by `choropleth`.

---

### Proportional Symbol Map  *(scaled symbol map)*

- **Renderer / `type`:** `symbol-map` — **Variant of `symbol-map`**
- **Controller:** `<mj-chart type="symbol-map" size-scale="sqrt" symbol="square" ...>`
- **Purpose:** Scale non-circular symbols (squares, triangles, custom shapes)
  proportionally to a geographic data value — best when circle area alone is
  insufficient to differentiate categories at the same location, or when
  conventions call for non-circular markers.
- **Decomposition:** `mj-chart-plot`, `mj-chart-legend` (size + shape key),
  `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`,
  `mj-chart-annotation`.
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Mineral Production by Site", "projection": "mercator" },
    "topology": "/geo/world.topojson",
    "series": [
      {
        "name": "Coal (Mt)",
        "symbol": "square",
        "points": [
          { "id": "S1", "label": "Shenhua", "lon": 110.3, "lat": 39.6, "size": 420 },
          { "id": "S2", "label": "Powder River", "lon": -106.1, "lat": 44.3, "size": 310 }
        ]
      }
    ]
  }
  ```
  Identical to the Bubble Map JSON shape; distinguished by `series[].symbol`
  set to a non-circle value. The `size` field maps through the `sqrt` scale to
  symbol area (not radius). Multiple series may use different symbol shapes to
  encode category alongside magnitude.
- **SVG primitives:** `<path>` (base map, non-circular symbol paths via
  `svgdraw.js` symbol builder), `<rect>` (square symbols), `<polygon>`
  (triangle symbols), `<text>` (labels), `<g>`.
- **Orientation:** `n/a`
- **Variants / modes:** Activates the `symbol` + `size-scale` mode of the
  `symbol-map` renderer. Bubble Map is the circular variant of the same renderer.
- **Phase:** P4
- **Notes:** Symbol `<path>` definitions for standard shapes (square, triangle,
  diamond, cross) are generated by `svgdraw.js` given a target area in pixels,
  then translated to the projected lon/lat point. For custom symbols, a
  `series[].symbol-path` SVG path string may be supplied and is scaled uniformly
  to match the computed area.
