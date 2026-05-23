# Less Common & Advanced Charts

> Catalog of chart types in this category for the automojo-webworks SVG chart
> library. Architecture, the coordinated-element model, the part components,
> the JSON contract, and phasing are defined in `../../chart-components-plan.md`
> and are not repeated here.

Several entries in this category relate to renderers defined elsewhere:
Node-link diagram, matrix plot, and edge bundling all reuse or extend the
network renderer family (see also category 8 — Flow & process). Nightingale
rose and coxcomb reuse the `radial` / `polar-bar` renderer (see also category
4). Faceted chart / small multiples is a meta-layout that tiles any renderer
and relates to the `small-multiples-table` entry in category 16. These
relationships are noted per entry.

---

### Voronoi diagram  *(Voronoi tessellation, nearest-region map)*
- **Renderer / `type`:** `voronoi` — **Primary renderer**
- **Controller:** `<mj-chart type="voronoi" ...>`
- **Purpose:** Partition a 2-D plane into nearest-neighbor regions around a set
  of seed points, used for proximity analysis, interactive hit-testing overlays,
  and geographic nearest-facility maps.
- **Decomposition:** `mj-chart-plot`, `mj-chart-title`, `mj-chart-tooltip`,
  `mj-chart-legend`, `mj-chart-axis` × 2, `mj-chart-grid`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Nearest Facility" },
    "series": [
      {
        "name": "Hospitals",
        "points": [
          { "x": 12.4, "y": 48.9, "label": "City General" },
          { "x": 13.1, "y": 49.2, "label": "North Clinic"  }
        ]
      }
    ]
  }
  ```
- **SVG primitives:** `<path>` (one closed polygon per Voronoi cell, filled and
  stroked); `<circle>` (seed point marker); `<text>` (optional site label).
- **Orientation:** `n/a`
- **Variants / modes:** `mode="overlay"` renders cells as a transparent hit-test
  layer over another chart (e.g. scatter) to improve tooltip targeting;
  `mode="clipped"` clips cells to a bounding rectangle.
- **Phase:** P5
- **Notes:** Voronoi cell polygons are computed client-side using Fortune's
  algorithm implemented in `svgdraw.js` (no external library). Each cell's path
  is emitted as a `<path d="M…Z">` element. When used as an overlay the cells
  are `fill-opacity:0` and handle pointer events only.

---

### Beeswarm plot  *(strip plot, dot plot — distribution variant)*
- **Renderer / `type`:** `beeswarm` — **Primary renderer**
- **Controller:** `<mj-chart type="beeswarm" ...>`
- **Purpose:** Show the distribution of individual observations as non-overlapping
  dots arranged along one axis, preserving every data point while avoiding
  overplotting.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` × 1, `mj-chart-title`,
  `mj-chart-legend`, `mj-chart-tooltip`, `mj-chart-grid`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Test Scores by Class" },
    "series": [
      {
        "name": "Class A",
        "points": [
          { "x": 72 }, { "x": 85 }, { "x": 91 }
        ]
      }
    ],
    "radius": 4,
    "padding": 1
  }
  ```
- **SVG primitives:** `<circle>` (one per observation, jitter-positioned to
  avoid overlap); `<line>` (optional median/mean marker).
- **Orientation:** `horizontal` (observations along the x-axis) / `vertical`
  (observations along the y-axis)
- **Variants / modes:** `mode="strip"` allows overlap (no jitter); `mode="violin"`
  delegates to the `violin` renderer for a density envelope behind the dots.
- **Phase:** P5
- **Notes:** Dot placement uses a greedy collision-avoidance algorithm: dots are
  sorted by value and placed at the closest available y-position (for horizontal
  orientation) that does not intersect any placed dot. The algorithm runs in the
  renderer. The single axis maps the data dimension; the perpendicular axis has
  no semantic meaning (jitter only) and no `<mj-chart-axis>` is needed on that
  side.

---

### Arc diagram  *(linear network, arc plot)*
- **Renderer / `type`:** `arc-diagram` — **Primary renderer**
- **Controller:** `<mj-chart type="arc-diagram" ...>`
- **Purpose:** Display relationships between nodes arranged on a single line,
  with arcs of varying height drawn above (or below) the line to represent edges,
  making cyclic or hierarchical relationships readable without 2-D node layout.
- **Decomposition:** `mj-chart-plot`, `mj-chart-title`, `mj-chart-legend`,
  `mj-chart-tooltip`, `mj-chart-annotation`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Co-authorship Network" },
    "nodes": [
      { "id": "alice", "label": "Alice", "group": "math" },
      { "id": "bob",   "label": "Bob",   "group": "cs"   }
    ],
    "links": [
      { "source": "alice", "target": "bob", "value": 3 }
    ]
  }
  ```
- **SVG primitives:** `<circle>` (node marker on the baseline); `<path>`
  (quadratic Bézier arc per edge, radius proportional to node distance);
  `<text>` (node label below baseline); `<line>` (baseline).
- **Orientation:** `horizontal` (nodes along x) / `vertical` (nodes along y)
- **Variants / modes:** `mode="below"` draws arcs below the baseline; `mode="both"`
  draws arcs on both sides (alternating by edge group).
- **Phase:** P5
- **Notes:** Uses the flow/network JSON shape (plan §3.4). Node order along the
  line can be set explicitly via `nodes[].order` or auto-computed by minimizing
  arc crossings (greedy heuristic in the renderer). Arc radius equals half the
  pixel distance between source and target nodes. Relationship to the network
  renderers in category 8: arc-diagram is a constrained 1-D layout of the same
  `nodes`/`links` data contract.

---

### Matrix plot  *(adjacency matrix, relationship density grid)*
- **Renderer / `type`:** `matrix-plot` — **Primary renderer**
- **Controller:** `<mj-chart type="matrix-plot" ...>`
- **Purpose:** Represent network or pairwise relationship data as a symmetric
  grid where each cell encodes the presence, count, or weight of an edge between
  two nodes, making community structure readable without hairball layouts.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` × 2, `mj-chart-title`,
  `mj-chart-legend`, `mj-chart-tooltip`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Link Matrix" },
    "nodes": [
      { "id": "a", "label": "Alpha", "group": 1 },
      { "id": "b", "label": "Beta",  "group": 1 },
      { "id": "c", "label": "Gamma", "group": 2 }
    ],
    "links": [
      { "source": "a", "target": "b", "value": 5 },
      { "source": "a", "target": "c", "value": 2 }
    ]
  }
  ```
- **SVG primitives:** `<rect>` (one cell per node pair, fill encodes edge weight);
  `<text>` (axis tick labels = node labels); `<g>` (row / column groups).
- **Orientation:** `n/a`
- **Variants / modes:** `mode="binary"` fills cells as solid if any link exists;
  `mode="weighted"` uses a sequential color scale on cell fill; `mode="grouped"`
  reorders nodes by group to reveal block structure.
- **Phase:** P5
- **Notes:** Uses the flow/network JSON shape (plan §3.4). The renderer builds
  an N×N matrix from `nodes` and `links`, then emits N² `<rect>` elements. Node
  ordering by group uses a stable sort; interactive reordering can be triggered
  via `mj-chart-select` events. Relationship to the `heatmap` renderer: the
  matrix-plot is topologically identical but the axes are node labels rather than
  independent category/value dimensions. Relationship to the `node-link` and
  `edge-bundling` renderers: all three share the same JSON contract and can be
  switched by changing `type`.

---

### Node-link diagram  *(force-directed graph, network graph)*
- **Renderer / `type`:** `node-link` — **Primary renderer**
- **Controller:** `<mj-chart type="node-link" ...>`
- **Purpose:** Visualize entity relationships as a spatial network of nodes and
  edges where a force simulation positions nodes to minimize crossings and
  surface cluster structure.
- **Decomposition:** `mj-chart-plot`, `mj-chart-title`, `mj-chart-legend`,
  `mj-chart-tooltip`, `mj-chart-annotation`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Dependency Graph" },
    "nodes": [
      { "id": "api",   "label": "API",      "group": "backend", "size": 10 },
      { "id": "ui",    "label": "Frontend", "group": "frontend","size": 8  }
    ],
    "links": [
      { "source": "api", "target": "ui", "value": 1, "label": "REST" }
    ],
    "layout": "force"
  }
  ```
- **SVG primitives:** `<circle>` or `<path>` (node, sized by `nodes[].size`);
  `<line>` or `<path>` (edge, with optional arrowhead `<marker>`);
  `<text>` (node and edge labels); `<g>` (per-node group wrapper).
- **Orientation:** `n/a`
- **Variants / modes:** `mode="tree"` uses a Reingold-Tilford tree layout instead
  of force simulation (requires a DAG or tree); `mode="radial-tree"` uses a
  radial tree layout; `mode="static"` uses fixed `nodes[].x` / `nodes[].y`
  coordinates and skips the simulation.
- **Phase:** P5
- **Notes:** Uses the flow/network JSON shape (plan §3.4). The force simulation
  is a lightweight Verlet integrator implemented in the renderer — no external
  physics library. Tick count is capped to prevent long first-render times;
  the simulation runs to completion off-screen and then a single repaint occurs.
  Drag interaction updates node fixed positions via `mj-chart-select` events.
  Relationship to `arc-diagram` and `matrix-plot`: all three consume the same
  JSON; switching `type` changes the layout strategy only.

---

### Edge bundling chart  *(hierarchical edge bundling, bundled network)*
- **Renderer / `type`:** `edge-bundling` — **Variant of `node-link`**
- **Controller:** `<mj-chart type="edge-bundling" ...>`
- **Purpose:** Simplify visually dense networks by routing edges along a shared
  hierarchy so that edges between nodes in the same cluster are drawn close
  together, reducing perceived hairball complexity.
- **Decomposition:** `mj-chart-plot`, `mj-chart-title`, `mj-chart-legend`,
  `mj-chart-tooltip`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Module Dependencies" },
    "nodes": [
      { "id": "core.auth",  "label": "auth",  "group": "core"   },
      { "id": "ui.login",   "label": "login", "group": "ui"     }
    ],
    "links": [
      { "source": "ui.login", "target": "core.auth", "value": 1 }
    ],
    "tension": 0.85
  }
  ```
- **SVG primitives:** `<path>` (cubic Bézier bundled edge, one per link);
  `<circle>` (leaf node on the radial ring); `<text>` (node label, radially
  positioned).
- **Orientation:** `n/a` (radial layout)
- **Variants / modes:** inherits `mode="static"` from `node-link`; `tension`
  controls bundling strength (0 = straight edges, 1 = fully bundled).
- **Phase:** P5
- **Notes:** Shares the flow/network JSON shape with `node-link` and `matrix-plot`.
  Nodes are arranged on a circle; edges are Bézier curves routed through
  hierarchical control points derived from `nodes[].group` (dot-delimited path,
  e.g. `"core.auth"` implies a two-level hierarchy). The bundling algorithm
  (Holten-style) is implemented in the renderer. `tension` is passed as a
  renderer attribute.

---

### Calendar heatmap  *(activity calendar, GitHub contribution graph)*
- **Renderer / `type`:** `calendar-heatmap` — **Primary renderer**
- **Controller:** `<mj-chart type="calendar-heatmap" ...>`
- **Purpose:** Show a continuous metric across every day of one or more calendar
  years as a color-encoded grid aligned to weeks and months, revealing seasonal
  or weekly activity patterns.
- **Decomposition:** `mj-chart-plot`, `mj-chart-title`, `mj-chart-legend`,
  `mj-chart-tooltip`, `mj-chart-annotation`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Commit Activity" },
    "domain": "year",
    "years": [2024, 2025],
    "colorScale": "sequential",
    "data": [
      { "date": "2024-03-15", "value": 12 },
      { "date": "2024-03-16", "value":  4 }
    ]
  }
  ```
- **SVG primitives:** `<rect>` (one per day, fill from sequential color scale);
  `<text>` (month labels, day-of-week labels); `<g>` (one per week column).
- **Orientation:** `horizontal` (weeks along x, days along y — standard) /
  `vertical` (weeks along y, days along x)
- **Variants / modes:** `mode="month"` restricts the grid to one month;
  `mode="week"` shows a single week in detail.
- **Phase:** P5
- **Notes:** The renderer builds a `time` scale over the date range and a `band`
  scale for day-of-week. Missing dates are rendered as low-opacity empty cells.
  Month boundary labels are placed at the start of each month's first week
  column. `<mj-chart-annotation>` can highlight a specific date range (e.g. a
  holiday). Relationship to `heatmap-table`: the calendar heatmap is a pure-SVG
  time-structured grid; the heatmap-table is a DOM-table with arbitrary row/column
  dimensions.

---

### Spiral chart  *(time spiral, cyclical timeline)*
- **Renderer / `type`:** `spiral` — **Primary renderer**
- **Controller:** `<mj-chart type="spiral" ...>`
- **Purpose:** Map a time series onto an Archimedean spiral so that repeating
  cycles (days of the week, months of the year) align radially, making periodic
  patterns and anomalies immediately visible.
- **Decomposition:** `mj-chart-plot`, `mj-chart-title`, `mj-chart-tooltip`,
  `mj-chart-legend`, `mj-chart-annotation`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Weekly Traffic Pattern" },
    "cycle": "week",
    "series": [
      {
        "name": "Page Views",
        "points": [
          { "t": "2024-01-01", "value": 4210 },
          { "t": "2024-01-02", "value": 3980 }
        ]
      }
    ]
  }
  ```
- **SVG primitives:** `<path>` (spiral arc — one continuous or segmented path
  per series, color-encoded by value via `stroke` or segmented `<rect>`-like
  wedges); `<text>` (cycle tick labels arranged radially); `<circle>` (center
  anchor).
- **Orientation:** `n/a` (radial layout)
- **Variants / modes:** `mode="bar"` renders the value as a radial bar extending
  outward from the spiral path rather than coloring the path stroke; `mode="line"`
  offsets the path radially by value magnitude.
- **Phase:** P5
- **Notes:** The Archimedean spiral parametric equations (`x = r·cos θ`, `y = r·sin θ`,
  `r = a + b·θ`) are computed in the renderer; `b` is chosen so one full cycle
  occupies a fixed radial band width. Time is mapped via a `time` scale to θ.
  The cycle length (`"week"`, `"year"`, `"day"`) determines the angular period.

---

### Nightingale rose chart  *(polar area chart, coxcomb — equal-angle variant)*
- **Renderer / `type`:** `polar-bar` — **Primary renderer**
- **Controller:** `<mj-chart type="polar-bar" ...>`
- **Purpose:** Compare values across categories arranged around a circle by
  encoding magnitude as the radius of equal-angle sectors, combining the
  readability of a bar chart with a circular layout that emphasizes cyclicality
  or closure.
- **Decomposition:** `mj-chart-plot`, `mj-chart-title`, `mj-chart-legend`,
  `mj-chart-tooltip`, `mj-chart-annotation`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Causes of Mortality" },
    "categories": ["Jan", "Feb", "Mar", "Apr"],
    "series": [
      { "name": "Preventable", "values": [83, 64, 72, 91], "color": "#4c9" },
      { "name": "Other",       "values": [12,  9, 15, 10] }
    ]
  }
  ```
- **SVG primitives:** `<path>` (one arc-slice per category per series, built
  with SVG arc commands `A`); `<text>` (category labels at sector midpoints,
  radially placed); `<line>` (radial grid spokes, optional).
- **Orientation:** `n/a` (radial layout)
- **Variants / modes:** `mode="stacked"` stacks series radially per sector;
  `mode="grouped"` places series side-by-side within each sector; the `coxcomb`
  catalog entry maps to `mode="proportional"` — see below.
- **Phase:** P5
- **Notes:** Each sector subtends an equal angle (`2π / N` where N = category
  count). Radius is mapped by a `linear` or `sqrt` scale from data value to
  pixel radius. Stacked and grouped modes follow the same stacking logic as the
  `bar` renderer but applied radially. The radial axis is drawn by a specialized
  configuration of `<mj-chart-axis kind="radial">`.

---

### Coxcomb chart  *(polar proportional chart — proportional-angle variant)*
- **Renderer / `type`:** `polar-bar` — **Variant of `polar-bar`**
- **Controller:** `<mj-chart type="polar-bar" mode="proportional" ...>`
- **Purpose:** Like the Nightingale rose but with sector angles proportional to
  category values (rather than equal-angle sectors), so that both angle and
  radius encode magnitude — analogous to a polar pie chart.
- **Decomposition:** `mj-chart-plot`, `mj-chart-title`, `mj-chart-legend`,
  `mj-chart-tooltip`
- **JSON shape:** identical to `polar-bar` (common envelope with `categories`
  and `series[].values`).
- **SVG primitives:** `<path>` (arc-wedge with both angle and radius varying per
  category); `<text>` (category labels).
- **Orientation:** `n/a`
- **Variants / modes:** satisfied by `mode="proportional"` on the `polar-bar`
  renderer.
- **Phase:** P5
- **Notes:** In `mode="proportional"` both the angle subtended and the radius
  encode value magnitude, making it a doubly-encoded variant. The distinction
  from the Nightingale rose is one arithmetic difference in the arc path
  computation; no new renderer file is needed. Historically also called a
  "coxcomb chart" after Florence Nightingale's diagram of the causes of
  mortality. Relationship to the `pie` renderer: coxcomb uses radial bars; pie
  uses constant-radius arcs with variable angles only.

---

### Tile grid map  *(tile map, equal-area map, cartogram grid)*
- **Renderer / `type`:** `tile-grid-map` — **Primary renderer**
- **Controller:** `<mj-chart type="tile-grid-map" ...>`
- **Purpose:** Display geographic regions as equal-sized tiles arranged in a
  grid that approximately preserves spatial layout, eliminating area distortion
  and making small regions visible while preserving coarse geographic intuition.
- **Decomposition:** `mj-chart-plot`, `mj-chart-title`, `mj-chart-legend`,
  `mj-chart-tooltip`, `mj-chart-annotation`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Election Results by State" },
    "topology": "us-states-tile-grid",
    "regions": [
      { "id": "CA", "label": "California", "value": 0.63, "group": "west" },
      { "id": "TX", "label": "Texas",      "value": 0.47, "group": "south" }
    ],
    "colorScale": "diverging",
    "domain": [0, 1],
    "midpoint": 0.5
  }
  ```
- **SVG primitives:** `<rect>` (one tile per region, fill from color scale);
  `<text>` (region abbreviation label and optional value label inside tile);
  `<g>` (row groups).
- **Orientation:** `n/a`
- **Variants / modes:** `mode="hex"` uses `<polygon>` hexagonal tiles instead
  of rectangular tiles; `mode="value"` scales tile sizes by value (breaking the
  equal-area guarantee).
- **Phase:** P5
- **Notes:** The grid layout (which row/col each region occupies) is specified by
  the `topology` reference — a small JSON lookup bundled in the renderer for
  common topologies (`us-states-tile-grid`, `eu-countries-tile-grid`). Custom
  topologies can be passed inline as `topology: { "CA": [0,5], "TX": [3,4] }`.
  Fill color is mapped via a `linear` scale. Relationship to the `choropleth`
  renderer (category 7): choropleth uses actual geographic outlines; tile-grid-map
  uses equal-area tiles.

---

### Faceted chart / small multiples  *(trellis chart, panel chart)*
- **Renderer / `type`:** `faceted` — **Primary renderer**
- **Controller:** `<mj-chart type="faceted" child-type="bar" ...>`
- **Purpose:** Repeat the same chart type across independent panels, one per
  value of a facet dimension, so that patterns within each group can be compared
  on identical scales without overplotting.
- **Decomposition:** `mj-chart-plot`, `mj-chart-title`, `mj-chart-legend`,
  `mj-chart-tooltip`, `mj-chart-axis` × 2
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Sales by Region" },
    "facetDimension": "region",
    "childType": "line",
    "sharedScales": true,
    "grid": { "cols": 3, "rowGap": 16, "colGap": 16 },
    "categories": ["Jan", "Feb", "Mar"],
    "panels": [
      {
        "label": "North",
        "series": [{ "name": "Revenue", "values": [10, 15, 12] }]
      },
      {
        "label": "South",
        "series": [{ "name": "Revenue", "values": [ 8, 11,  9] }]
      }
    ]
  }
  ```
- **SVG primitives:** determined by `childType` — e.g. `<path>` for line panels,
  `<rect>` for bar panels; `<text>` (panel title above each panel); `<g>` (per-panel
  wrapper); `<line>` (shared axis ticks on border panels only).
- **Orientation:** `horizontal` / `vertical` (applies to the `childType` renderer
  within each panel and to panel fill direction)
- **Variants / modes:** any value of `childType` supported by the renderer
  registry (bar, line, area, scatter, …); `mode="free-scale"` disables shared
  scales so each panel auto-scales independently.
- **Phase:** P5
- **Notes:** The `faceted` renderer is a meta-layout: it calls the `childType`
  renderer function once per panel with a sub-region of the plot surface. It does
  not spawn child `<mj-chart>` controllers; instead it allocates sub-`<g>` regions
  within the single `<mj-chart-plot>` SVG. When `sharedScales: true`, domains
  are unioned across all panels before any panel is drawn. Axes appear only on
  border panels to reduce clutter. Relationship to `small-multiples-table`
  (category 16): that renderer arranges panels in a DOM-table grid; `faceted`
  uses a pure-SVG grid and supports any `childType` renderer.

---

### Chernoff faces  *(face chart, anthropomorphic chart)*
- **Renderer / `type`:** `chernoff` — **Primary renderer**
- **Controller:** `<mj-chart type="chernoff" ...>`
- **Purpose:** Encode multiple variables per observation as the features of a
  cartoon face (eye size, brow angle, mouth curve, nose length, face width), exploiting
  human pattern recognition for multivariate outlier detection in small datasets.
- **Decomposition:** `mj-chart-plot`, `mj-chart-title`, `mj-chart-legend`,
  `mj-chart-tooltip`, `mj-chart-data-table`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Country Risk Profiles" },
    "features": {
      "faceWidth":  "gdp",
      "eyeSize":    "literacy",
      "browAngle":  "corruption",
      "mouthCurve": "happiness",
      "noseLength": "inequality"
    },
    "series": [
      {
        "name": "Country A",
        "values": { "gdp": 0.72, "literacy": 0.91,
                    "corruption": 0.34, "happiness": 0.68, "inequality": 0.45 }
      }
    ]
  }
  ```
- **SVG primitives:** `<ellipse>` (face outline, eyes); `<path>` (mouth curve,
  brows, nose — all Bézier arcs); `<circle>` (pupils, nostrils); `<text>`
  (observation label below face); `<g>` (one face per observation).
- **Orientation:** `horizontal` (faces in a row) / `vertical` (faces stacked)
- **Variants / modes:** `mode="simple"` uses fewer features (eyes + mouth only)
  for legibility with more than ~8 observations.
- **Phase:** P5
- **Notes:** Each feature is mapped through a `linear` scale `[data-min, data-max]`
  → `[feature-min-px, feature-max-px]`. The face geometry is parameterized by
  five scalars; `svgdraw.js` provides a `drawFace(params) → SVG fragment` helper.
  Best used with N ≤ 20 observations; the renderer emits a console warning for
  larger datasets. The `features` mapping lets callers assign any data key to
  any facial feature. The `<mj-chart-data-table>` is mandatory for this renderer
  as the visual encoding is not independently decodable.

---

### Glyph chart  *(star glyph, radar glyph, multivariate icon)*
- **Renderer / `type`:** `glyph` — **Primary renderer**
- **Controller:** `<mj-chart type="glyph" ...>`
- **Purpose:** Encode multiple variables per observation as the shape of a
  repeated visual symbol (star, radar polygon, or custom glyph), enabling
  multivariate comparison at a glance across a grid of observations.
- **Decomposition:** `mj-chart-plot`, `mj-chart-title`, `mj-chart-legend`,
  `mj-chart-tooltip`, `mj-chart-data-table`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Player Attributes" },
    "axes": ["Speed", "Strength", "Stamina", "Accuracy", "Defense"],
    "series": [
      {
        "name": "Player A",
        "values": [0.85, 0.60, 0.72, 0.90, 0.55]
      },
      {
        "name": "Player B",
        "values": [0.70, 0.80, 0.65, 0.75, 0.88]
      }
    ],
    "glyphType": "star",
    "grid": { "cols": 4 }
  }
  ```
- **SVG primitives:** `<polygon>` (star/radar polygon connecting axis values);
  `<line>` (axis spokes); `<circle>` (center origin, optional dot at each
  axis value); `<text>` (axis labels, observation label below glyph); `<g>`
  (one glyph per observation).
- **Orientation:** `n/a`
- **Variants / modes:** `mode="radar"` (filled polygon, same as the `radar`
  renderer but as a miniature tiled glyph); `mode="star"` (line spokes without
  fill); `mode="bar-glyph"` (radial bars per axis, similar to `polar-bar`).
- **Phase:** P5
- **Notes:** The `radar` renderer (category 4) is the full-sized single-observation
  variant; the `glyph` renderer tiles many miniature instances. Axis values are
  normalized to `[0,1]` via per-axis `linear` scales so all axes fit the same
  glyph radius. The `<mj-chart-data-table>` is mandatory for accessibility.
  `glyphType` is resolved by the renderer to a drawing function in `svgdraw.js`.

---

### Pixel chart  *(density pixel chart, unit heatmap, raster chart)*
- **Renderer / `type`:** `pixel` — **Primary renderer**
- **Controller:** `<mj-chart type="pixel" ...>`
- **Purpose:** Represent very large discrete datasets as a dense grid of
  colored pixels where each pixel encodes one observation or one aggregate bin,
  maximizing information density when individual marks would overlap completely.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` × 2, `mj-chart-title`,
  `mj-chart-legend`, `mj-chart-tooltip`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Request Log Density" },
    "xDimension": "hour",
    "yDimension": "day",
    "valueMeasure": "count",
    "colorScale": "sequential",
    "domain": [0, 500],
    "bins": [
      { "x": 0, "y": 0, "value": 142 },
      { "x": 1, "y": 0, "value": 89  }
    ]
  }
  ```
- **SVG primitives:** `<rect>` (one 1×1 or N×N pixel per bin, fill from color
  scale; grouped in `<g>` rows for performance); alternatively a single
  `<image>` element backed by an `ImageData` canvas for datasets exceeding
  ~10 000 pixels (with fallback aria-label).
- **Orientation:** `horizontal` / `vertical` (swaps which dimension is x vs y)
- **Variants / modes:** `mode="svg"` forces individual `<rect>` elements (default
  for ≤ 10 000 bins); `mode="canvas"` renders to an off-screen `<canvas>` and
  embeds the result as `<image>` for performance with very large bin counts.
- **Phase:** P5
- **Notes:** For `mode="svg"` (the primary SVG path) the renderer groups `<rect>`
  elements in row-level `<g>` elements to keep the DOM tree shallow. Each `<rect>`
  width and height equal `plotWidth / xBins` and `plotHeight / yBins` respectively.
  Color is from a `linear` scale mapped to `--mj-*` sequential token ramp. For
  `mode="canvas"` the renderer writes pixel data to an `OffscreenCanvas`, converts
  to a data URL, and sets it as `<image xlink:href="…">` inside the SVG — the SVG
  drawing model is still the host. Tooltip hit-testing in canvas mode uses a
  second invisible same-size hit canvas.
