# Tables with Visual Encoding

> Catalog of chart types in this category for the codecraftai-webworks SVG chart
> library. Architecture, the coordinated-element model, the part components,
> the JSON contract, and phasing are defined in `../../chart-components-plan.md`
> and are not repeated here.

Table-based charts blend tabular DOM structure with inline SVG cell encodings.
The plain table shell reuses `<mj-table>` / `<mj-data-table>` from the
component library when the primary structure is a DOM `<table>`; the SVG chart
system contributes in-cell SVG marks rendered by a thin cell-renderer function
keyed on `type`. Pure SVG rendering (the `<mj-chart-plot>` surface) is used
only where the spatial layout cannot be expressed as rows and columns — notably
icon arrays and small-multiples tables.

---

### Data table  *(exact-value table, tabular report)*
- **Renderer / `type`:** `data-table` — **Primary renderer**
- **Controller:** `<mj-chart type="data-table" ...>`
- **Purpose:** Display raw or summarized data as exact values in a sortable,
  scrollable DOM table; the chart system's accessible baseline for every chart
  type.
- **Decomposition:** `mj-chart-data-table`, `mj-chart-title`, `mj-chart-tooltip`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Sales Report" },
    "columns": [
      { "key": "region", "label": "Region", "type": "string" },
      { "key": "q1",     "label": "Q1",     "type": "number", "format": ",.0f" }
    ],
    "rows": [
      { "region": "North", "q1": 142000 },
      { "region": "South", "q1": 98500  }
    ]
  }
  ```
- **SVG primitives:** none — rendered as a plain DOM `<table>` via
  `<mj-chart-data-table>`; SVG is not used in the default data-table view.
- **Orientation:** `n/a`
- **Variants / modes:** `mode="striped"` alternates row fills; `mode="compact"`
  reduces cell padding; `mode="bordered"` adds cell borders. The `heatmap-table`
  renderer adds per-cell fill SVG — see below.
- **Phase:** P5
- **Notes:** This is the accessible data-table alternative surfaced by every
  other chart type. As a standalone chart type it becomes a fully-featured
  report table. Sorting is handled via a `sort` event on column headers;
  pagination is caller-controlled through `data` updates. No SVG rendering
  occurs; `<mj-chart-data-table>` generates a real `<table>` that screen readers
  traverse normally.

---

### Heatmap table  *(color-encoded table, tabular heatmap)*
- **Renderer / `type`:** `heatmap-table` — **Primary renderer**
- **Controller:** `<mj-chart type="heatmap-table" ...>`
- **Purpose:** Show a matrix of numeric values where each cell's background fill
  intensity encodes magnitude, combining exact readability with spatial pattern
  detection.
- **Decomposition:** `mj-chart-data-table`, `mj-chart-title`, `mj-chart-legend`,
  `mj-chart-tooltip`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Correlation Matrix" },
    "columns": [
      { "key": "jan", "label": "Jan", "type": "number" }
    ],
    "rows": [
      { "label": "Product A", "jan": 0.82 }
    ],
    "domain": [0, 1],
    "colorScale": "sequential"
  }
  ```
- **SVG primitives:** `<rect>` (per-cell fill layer, rendered inside each `<td>`
  as an inline `<svg>` sized to the cell); `<text>` (the numeric label, drawn on
  top of the fill rect so it remains selectable as DOM text via the table row,
  with the SVG text as the visual replica).
- **Orientation:** `n/a`
- **Variants / modes:** `mode="diverging"` uses a bi-directional color scale
  centred at zero; `mode="categorical"` maps discrete categories to hue bands.
- **Phase:** P5
- **Notes:** The DOM `<table>` is emitted by `<mj-chart-data-table>`; each cell
  hosts a small inline `<svg>` that the `heatmap-table` cell-renderer injects.
  The sequential/diverging scale is a `linear` scale from `scales.js` mapped to
  an `ordinal-color` ramp from design tokens. The legend shows the color ramp
  gradient. Relationship to the `heatmap` renderer (category 10): that renderer
  is a pure-SVG Cartesian heatmap; this one is DOM-table-first with SVG fills.

---

### Bar-in-cell table  *(inline bar table, magnitude table)*
- **Renderer / `type`:** `bar-cell-table` — **Primary renderer**
- **Controller:** `<mj-chart type="bar-cell-table" ...>`
- **Purpose:** Render a DOM table where one or more numeric columns are replaced
  by miniature horizontal bars, enabling compact side-by-side magnitude
  comparisons across rows without leaving tabular alignment.
- **Decomposition:** `mj-chart-data-table`, `mj-chart-title`, `mj-chart-tooltip`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Team Velocity" },
    "columns": [
      { "key": "team",  "label": "Team",     "type": "string" },
      { "key": "score", "label": "Score",    "type": "number", "render": "bar" },
      { "key": "delta", "label": "Δ vs Prev","type": "number", "render": "bar",
        "domain": [-20, 20] }
    ],
    "rows": [
      { "team": "Alpha", "score": 78, "delta": 5 }
    ],
    "domain": [0, 100]
  }
  ```
- **SVG primitives:** `<rect>` (bar fill); `<rect>` (bar background track);
  `<text>` (value label at bar end, optional via `show-label` attribute).
- **Orientation:** `n/a` (bars are always horizontal within cells)
- **Variants / modes:** `mode="diverging"` centers bars on zero for delta
  columns; `mode="stacked"` splits a cell into a proportional pair (positive /
  negative segments).
- **Phase:** P5
- **Notes:** Each cell flagged `"render": "bar"` receives an inline `<svg>` from
  the `bar-cell-table` cell-renderer. Bars share the same domain across all rows
  in that column (set by `column.domain` or auto-computed from data). This is
  a DOM-first table; the bar SVGs are decorative and `aria-hidden`; the numeric
  value is present as accessible text inside the `<td>`.

---

### Icon array  *(unit chart, isotype grid, waffle table)*
- **Renderer / `type`:** `icon-array` — **Primary renderer**
- **Controller:** `<mj-chart type="icon-array" ...>`
- **Purpose:** Represent counts or proportions as a grid of discrete unit icons,
  making the magnitude of a part-to-whole relationship viscerally countable.
- **Decomposition:** `mj-chart-plot`, `mj-chart-title`, `mj-chart-legend`,
  `mj-chart-tooltip`, `mj-chart-value-labels`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Vaccination Rate" },
    "total": 100,
    "series": [
      { "name": "Vaccinated",   "count": 73, "icon": "circle", "color": "#4c9" },
      { "name": "Unvaccinated", "count": 27, "icon": "circle" }
    ],
    "grid": { "cols": 10 }
  }
  ```
- **SVG primitives:** `<circle>` or `<path>` (one element per unit icon,
  grouped in `<g>` per series); `<text>` (optional count labels).
- **Orientation:** `horizontal` (fills rows left-to-right) / `vertical` (fills
  columns top-to-bottom)
- **Variants / modes:** `mode="person"` uses a person-silhouette `<path>`
  instead of circles; `mode="square"` uses `<rect>` icons.
- **Phase:** P5
- **Notes:** Rendered entirely on `<mj-chart-plot>` as pure SVG — not a DOM
  table. The grid layout is computed in the renderer: `total` icons are placed
  at `(col, row)` positions; series fill sequentially. Icon paths are inline SVG
  paths from `svgdraw.js`. The `waffle` renderer (category 5) is the analogous
  area-proportional square grid; this renderer uses discrete countable units.

---

### Conditional formatting table  *(highlight table, rules-based table)*
- **Renderer / `type`:** `cf-table` — **Primary renderer**
- **Controller:** `<mj-chart type="cf-table" ...>`
- **Purpose:** Emphasize patterns in tabular data by applying color, icon, or
  typographic highlights to cells that satisfy declarative rules, analogous to
  spreadsheet conditional formatting.
- **Decomposition:** `mj-chart-data-table`, `mj-chart-title`, `mj-chart-tooltip`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "SLA Dashboard" },
    "columns": [
      { "key": "svc",    "label": "Service", "type": "string" },
      { "key": "uptime", "label": "Uptime",  "type": "number", "format": ".1%" }
    ],
    "rows": [
      { "svc": "Auth", "uptime": 0.9991 }
    ],
    "rules": [
      { "column": "uptime", "op": "lt", "value": 0.999,
        "style": { "fill": "#f44", "icon": "warning" } },
      { "column": "uptime", "op": "gte", "value": 0.9999,
        "style": { "fill": "#4c9", "icon": "check" } }
    ]
  }
  ```
- **SVG primitives:** `<rect>` (cell fill); `<path>` (icon glyph, e.g. warning
  triangle, check mark); `<text>` (value text replica); all inline per-cell.
- **Orientation:** `n/a`
- **Variants / modes:** `mode="icon-only"` hides fill and shows only the icon;
  `mode="text-color"` applies rule color to the text rather than the background.
- **Phase:** P5
- **Notes:** Rules are evaluated client-side by the renderer; order is
  first-match. Icons are drawn as `<path>` elements from a small icon set in
  `svgdraw.js`. The DOM `<table>` carries the data; per-cell SVG is
  `aria-hidden`; `aria-label` on each `<td>` includes the rule state
  (e.g. "Uptime 99.8% — below threshold").

---

### Pivot table  *(cross-tab, multi-dimensional summary)*
- **Renderer / `type`:** `pivot-table` — **Primary renderer**
- **Controller:** `<mj-chart type="pivot-table" ...>`
- **Purpose:** Summarize multi-dimensional data by grouping rows and columns
  independently, displaying aggregated values at each intersection, with
  optional visual encoding in cells.
- **Decomposition:** `mj-chart-data-table`, `mj-chart-title`, `mj-chart-tooltip`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Revenue by Region × Quarter" },
    "rowDimension":    "region",
    "columnDimension": "quarter",
    "valueMeasure":    "revenue",
    "aggregation":     "sum",
    "rows": [
      { "region": "North", "quarter": "Q1", "revenue": 142000 },
      { "region": "North", "quarter": "Q2", "revenue": 156000 },
      { "region": "South", "quarter": "Q1", "revenue": 98500  }
    ],
    "totals": { "rows": true, "columns": true, "grand": true }
  }
  ```
- **SVG primitives:** `<rect>` (optional heatmap fill in value cells, when
  `cell-encoding="heatmap"` is set); `<text>` (value text replica).
- **Orientation:** `n/a`
- **Variants / modes:** `mode="heatmap"` activates per-cell fill encoding (reuses
  the `heatmap-table` cell-renderer on value cells); `mode="bar"` activates
  bar-in-cell encoding on value cells.
- **Phase:** P5
- **Notes:** Aggregation (`sum`, `mean`, `count`, `min`, `max`) is performed
  client-side by the controller from flat `rows` data; the pivot matrix is
  computed at model build time in `chartmodel.js`. Hierarchical row/column
  grouping (multiple row or column dimensions) is handled by nested `<th>`
  spanning. The DOM `<table>` carries all data; SVG is decorative and
  `aria-hidden`.

---

### Scorecard  *(KPI card, metric tile, big-number card)*
- **Renderer / `type`:** `scorecard` — **Primary renderer**
- **Controller:** `<mj-chart type="scorecard" ...>`
- **Purpose:** Surface one or more key performance indicators as prominently
  displayed numbers with supporting context (label, target, trend indicator,
  delta), suitable for dashboard headers and metric tiles.
- **Decomposition:** `mj-chart-plot`, `mj-chart-title`, `mj-chart-tooltip`,
  `mj-chart-annotation`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "This Week" },
    "metrics": [
      {
        "label": "Active Users",
        "value": 14382,
        "format": ",.0f",
        "target": 15000,
        "delta": 0.034,
        "trend": "up",
        "sparkline": [130, 145, 139, 158, 144, 162, 171]
      }
    ]
  }
  ```
- **SVG primitives:** `<text>` (headline value, label, delta); `<path>` (trend
  arrow glyph, sparkline line); `<rect>` (progress bar toward target, optional);
  `<circle>` (sparkline dots, optional); all within `<mj-chart-plot>`'s SVG.
- **Orientation:** `horizontal` (metrics arranged in a row) / `vertical`
  (metrics stacked)
- **Variants / modes:** `mode="compact"` shows only value + label; `mode="full"`
  adds target, delta, and sparkline; `mode="gauge"` replaces the progress bar
  with a radial arc (reuses the `gauge` renderer arc primitive).
- **Phase:** P5
- **Notes:** Each metric's sparkline is a miniature `line` renderer path drawn
  directly on the scorecard SVG surface; a full `<mj-chart>` is not spawned per
  metric. Target progress is expressed as a `linear` scale mapping `[0, target]`
  to the bar width. Trend arrows are `<path>` glyphs from `svgdraw.js`. The
  scorecard is pure SVG (not a DOM table) so that visual alignment across
  metrics is pixel-accurate.

---

### Small multiples table  *(trellis table, sparkline grid, panel grid)*
- **Renderer / `type`:** `small-multiples-table` — **Primary renderer**
- **Controller:** `<mj-chart type="small-multiples-table" ...>`
- **Purpose:** Arrange many miniature chart panels in a row-column grid, each
  showing the same chart type applied to a different data slice, facilitating
  comparison across groups without overlapping series.
- **Decomposition:** `mj-chart-plot`, `mj-chart-title`, `mj-chart-legend`,
  `mj-chart-tooltip`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Sales by Product" },
    "panelDimension": "product",
    "grid": { "cols": 4 },
    "childType": "line",
    "sharedScales": true,
    "categories": ["Jan", "Feb", "Mar", "Apr"],
    "panels": [
      {
        "label": "Widget A",
        "series": [{ "name": "Revenue", "values": [12, 15, 11, 18] }]
      },
      {
        "label": "Widget B",
        "series": [{ "name": "Revenue", "values": [8, 9, 14, 12] }]
      }
    ]
  }
  ```
- **SVG primitives:** determined by `childType` — e.g. `<path>` for line
  sparklines, `<rect>` for bar panels; `<text>` for panel labels; `<g>` to
  wrap each panel; `<line>` for shared-axis tick marks.
- **Orientation:** `horizontal` / `vertical` (controls whether panels fill the
  grid row-first or column-first)
- **Variants / modes:** `mode="sparkline"` renders line sparklines with no axes;
  `mode="bar"` renders bar sparklines; `mode="area"` renders area sparklines.
  The `faceted` renderer in category 17 is the general-purpose version of this
  pattern applied to any renderer — note the relationship.
- **Phase:** P5
- **Notes:** When `sharedScales: true`, all panels share the same domain (union
  of all panel domains) so panel heights are visually comparable. Each mini-chart
  is rendered by delegating to the `childType` renderer function directly on a
  sub-`<svg>` or `<g>` region of the plot surface — a full `<mj-chart>`
  controller is not spawned per panel. Panel labels are `<text>` drawn above each
  panel. Relationship to `small-multiples-table`: this renderer lays panels out
  in a grid that can be embedded in a DOM table (row = category, column =
  metric) when `mode="table-layout"`.
