# Comparison Charts

> Catalog of chart types in this category for the automojo-webworks SVG chart
> library. Architecture, the coordinated-element model, the part components,
> the JSON contract, and phasing are defined in `../../chart-components-plan.md`
> and are not repeated here.

Charts in this category compare discrete categories or entities against one
another, either for a single measure or across multiple measures.

---

### Bar chart  *(horizontal bar chart)*

- **Renderer / `type`:** `bar` — **Primary renderer**
- **Controller:** `<mj-chart type="bar" orientation="horizontal">`
- **Purpose:** Compare discrete categories by a single quantitative measure,
  drawn with horizontal bars so category labels read naturally left-to-right.
- **Decomposition:**
  - `mj-chart-plot` — bar marks
  - `mj-chart-axis` ×2 — `kind="category" side="start"` and `kind="value" side="bottom"`
  - `mj-chart-grid` — vertical gridlines on the value axis
  - `mj-chart-legend` — visible when `group` mode is set; hidden for single-series
  - `mj-chart-title`
  - `mj-chart-tooltip`
  - `mj-chart-value-labels` — optional end-of-bar labels
  - `mj-chart-annotation` — optional reference lines / targets
  - `mj-chart-data-table`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "string", "orientation": "horizontal" },
    "categories": ["Cat A", "Cat B", "Cat C"],
    "series": [
      { "name": "Series 1", "values": [42, 17, 63], "color": "optional" }
    ]
  }
  ```
- **SVG primitives:** `<rect>` (bars), `<text>` (axis labels, value labels),
  `<line>` (axis lines, ticks, gridlines), `<g>` (grouping per series / category).
- **Orientation:** `horizontal` (canonical for Bar); `vertical` renders as Column
  (see Variant below). Both orientations use the same renderer — the category
  and value axes are swapped.
- **Variants / modes:**
  - `orientation="vertical"` → Column chart
  - `group="cluster"` → Grouped bar / Grouped column
  - `group="stack"` → Stacked bar / Stacked column
  - `group="stack100"` → 100% stacked bar / 100% stacked column
- **Phase:** P1
- **Notes:** Uses `band` scale for categories and `linear` scale for values.
  Negative values are supported (bars extend left/down from the zero baseline).
  The zero-line baseline is always rendered; clip-path applied so bars do not
  overflow the plot box.

---

### Column chart  *(vertical bar chart)*

- **Renderer / `type`:** `bar` — **Variant of `bar`**
- **Controller:** `<mj-chart type="bar" orientation="vertical">`
- **Purpose:** Compare discrete categories by a single quantitative measure,
  drawn with vertical bars — the conventional upright form.
- **Decomposition:** Same parts as Bar chart with axes swapped:
  `kind="category" side="bottom"` and `kind="value" side="start"`.
- **JSON shape:** Identical to Bar chart; `orientation` in `meta` or on the
  controller attribute drives the axis swap.
- **SVG primitives:** `<rect>`, `<text>`, `<line>`, `<g>`.
- **Orientation:** `vertical` (canonical for Column); use `orientation="horizontal"`
  to render as Bar.
- **Variants / modes:** All `group` modes apply identically — `cluster`, `stack`,
  `stack100`.
- **Phase:** P1
- **Notes:** No separate renderer file — `bar.js` reads `orientation` from the
  model and rotates its drawing logic. Default orientation when `orientation` is
  not specified is `vertical`.

---

### Grouped bar chart  *(clustered bar, grouped column)*

- **Renderer / `type`:** `bar` — **Variant of `bar`**
- **Controller:** `<mj-chart type="bar" group="cluster" orientation="horizontal|vertical">`
- **Purpose:** Compare multiple series (groups) side-by-side within each
  category to reveal cross-series differences at each category.
- **Decomposition:** Same as Bar chart. `mj-chart-legend` is always visible
  (one entry per series). `mj-chart-value-labels` optional.
- **JSON shape:**
  ```json
  {
    "meta": { "title": "string", "orientation": "horizontal" },
    "categories": ["Q1", "Q2", "Q3"],
    "series": [
      { "name": "Product A", "values": [10, 20, 15] },
      { "name": "Product B", "values": [8,  18, 22] }
    ]
  }
  ```
- **SVG primitives:** `<rect>` (one per series per category, offset within the
  band), `<text>`, `<line>`, `<g>`.
- **Orientation:** `horizontal` or `vertical`.
- **Variants / modes:** This is the `cluster` mode of the `bar` renderer.
  Switching `group` changes mode without a renderer change.
- **Phase:** P1
- **Notes:** Within each category band, bars are sub-divided using a nested
  `band` scale (`bandwidth / seriesCount`). Color comes from the categorical
  token ramp. Legend is required for legibility.

---

### Stacked bar chart  *(stacked column)*

- **Renderer / `type`:** `bar` — **Variant of `bar`**
- **Controller:** `<mj-chart type="bar" group="stack" orientation="horizontal|vertical">`
- **Purpose:** Show category totals while revealing each series' contribution
  to that total; good for part-to-whole within a comparison context.
- **Decomposition:** Same as Bar chart; `mj-chart-legend` always visible;
  `mj-chart-value-labels` optional (segment labels).
- **JSON shape:** Identical multi-series envelope to Grouped bar chart. The
  renderer stacks `values` in series order.
- **SVG primitives:** `<rect>` (segments stacked end-to-end per category),
  `<text>`, `<line>`, `<g>`.
- **Orientation:** `horizontal` or `vertical`.
- **Variants / modes:** `group="stack"` mode of `bar`. Switch to `stack100`
  for proportional stacking.
- **Phase:** P1
- **Notes:** Renderer computes cumulative baselines per category using the D3
  stack algorithm pattern (implemented in `svgdraw.js`, no D3 dependency). Only
  the bottom-most series has a zero baseline; upper segments are anchored to
  the top of the segment below.

---

### 100% stacked bar chart  *(percent stacked bar, proportional stacked bar)*

- **Renderer / `type`:** `bar` — **Variant of `bar`**
- **Controller:** `<mj-chart type="bar" group="stack100" orientation="horizontal|vertical">`
- **Purpose:** Compare the proportional composition across categories when
  absolute totals are less important than relative share.
- **Decomposition:** Same as Stacked bar. Value axis labeled as percentages
  (0–100%). `mj-chart-value-labels` shows percentage values in segments.
- **JSON shape:** Same multi-series envelope; the renderer normalizes raw
  values to 0–100 per category internally.
- **SVG primitives:** `<rect>`, `<text>`, `<line>`, `<g>`.
- **Orientation:** `horizontal` or `vertical`.
- **Variants / modes:** `group="stack100"` mode of `bar`.
- **Phase:** P1
- **Notes:** Value scale is always `linear` 0–100 regardless of raw data range.
  Segments narrower than ~14px suppress their value label to avoid overlap.

---

### Lollipop chart  *(lollipop plot, dot-and-stick chart)*

- **Renderer / `type`:** `lollipop` — **Primary renderer**
- **Controller:** `<mj-chart type="lollipop" orientation="horizontal|vertical">`
- **Purpose:** A cleaner, lower-ink alternative to bar charts; emphasizes the
  data point position rather than the filled bar area.
- **Decomposition:**
  - `mj-chart-plot` — stems and dot heads
  - `mj-chart-axis` ×2 — category axis and value axis
  - `mj-chart-grid` — gridlines on value axis
  - `mj-chart-legend` — when multiple series present
  - `mj-chart-title`
  - `mj-chart-tooltip`
  - `mj-chart-value-labels` — optional labels beside dots
  - `mj-chart-annotation` — reference lines
  - `mj-chart-data-table`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "string", "orientation": "horizontal" },
    "categories": ["Alpha", "Beta", "Gamma"],
    "series": [
      { "name": "Score", "values": [78, 54, 91], "color": "optional" }
    ]
  }
  ```
  Optional `"markerSize"` per series (pixels, default 8).
- **SVG primitives:** `<line>` (stem from baseline to value), `<circle>` (dot
  head at value position), `<text>`, `<g>`.
- **Orientation:** `horizontal` or `vertical`.
- **Variants / modes:** Multiple series render side-by-side lollipops within a
  category band (cluster mode, controlled by `group="cluster"`). No stack mode.
- **Phase:** P2
- **Notes:** Uses `band` scale for categories and `linear` scale for values.
  Stems use `stroke-width` from `--mj-chart-stem-width` token. Dot size
  overridable via `markerSize` in the series config or a global `marker-size`
  attribute on the controller.

---

### Dot plot  *(Cleveland dot plot, strip plot — single value per category)*

- **Renderer / `type`:** `dotplot` — **Primary renderer**
- **Controller:** `<mj-chart type="dotplot" orientation="horizontal|vertical">`
- **Purpose:** Compare values across categories with maximum data-ink ratio;
  especially effective when categories must be read precisely with minimal
  visual clutter.
- **Decomposition:**
  - `mj-chart-plot` — dot marks and optional connector lines
  - `mj-chart-axis` ×2 — category axis and value axis
  - `mj-chart-grid` — light gridlines on value axis
  - `mj-chart-legend` — when multiple series present
  - `mj-chart-title`
  - `mj-chart-tooltip`
  - `mj-chart-annotation`
  - `mj-chart-data-table`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "string", "orientation": "horizontal" },
    "categories": ["Item A", "Item B", "Item C"],
    "series": [
      { "name": "2024", "values": [3.1, 5.7, 2.4] },
      { "name": "2025", "values": [4.0, 6.2, 1.9] }
    ]
  }
  ```
  Optional `"showConnectors": true` to draw a line between series dots in the
  same category (Dumbbell mode — see below).
- **SVG primitives:** `<circle>` (dots), `<line>` (optional connectors, gridlines,
  axis), `<text>`, `<g>`.
- **Orientation:** `horizontal` or `vertical`.
- **Variants / modes:**
  - Single series: classic Cleveland dot plot.
  - Two series with `showConnectors: true`: Dumbbell chart (see Dumbbell entry).
- **Phase:** P2
- **Notes:** Uses `point` scale (not `band`) for categories — dots align to
  category midpoints without a bandwidth gap. Multiple series dots for the same
  category are drawn at the same x (or y) position, differentiated by color and
  shape (shape variation ensures non-color accessibility).

---

### Bullet chart  *(bullet graph)*

- **Renderer / `type`:** `bullet` — **Primary renderer**
- **Controller:** `<mj-chart type="bullet" orientation="horizontal|vertical">`
- **Purpose:** Compare a primary performance measure against one or more
  qualitative ranges (Poor/Satisfactory/Good) and a target marker; a compact,
  information-dense KPI alternative to gauges.
- **Decomposition:**
  - `mj-chart-plot` — range bands, performance bar, and target tick
  - `mj-chart-axis` — value axis only (`kind="value"`)
  - `mj-chart-title` — category label (often used as chart label)
  - `mj-chart-tooltip`
  - `mj-chart-annotation` — additional reference lines
  - `mj-chart-data-table`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "string", "orientation": "horizontal" },
    "categories": ["Revenue", "Profit", "Satisfaction"],
    "series": [
      {
        "name": "Revenue",
        "value": 275,
        "target": 300,
        "ranges": [200, 250, 350],
        "rangeLabels": ["Poor", "Satisfactory", "Good"]
      }
    ]
  }
  ```
  Each element of `series` represents one bullet. `ranges` is an ascending
  array of thresholds; the renderer draws a band between each pair.
- **SVG primitives:** `<rect>` (qualitative range bands, performance bar),
  `<line>` (target tick mark), `<text>` (labels), `<g>`.
- **Orientation:** `horizontal` (canonical — wide bar) or `vertical` (tall bar).
- **Variants / modes:** None. Multiple bullets stack as independent rows/columns
  sharing the same value scale.
- **Phase:** P2
- **Notes:** Range bands use progressively lighter fills from `--mj-chart-range-*`
  tokens. Performance bar is drawn narrower (≈40% of band width) and centered.
  Target tick is drawn as a short perpendicular `<line>`. `ranges` values define
  the domain for the `linear` value scale; the performance bar is clipped to the
  max range.

---

### Dumbbell chart  *(connected dot plot, DNA chart, gap chart)*

- **Renderer / `type`:** `dotplot` — **Variant of `dotplot`**
- **Controller:** `<mj-chart type="dotplot" show-connectors="true">`
- **Purpose:** Highlight the magnitude and direction of change between exactly
  two values (e.g. before/after, start/end) per category.
- **Decomposition:** Same as Dot plot.
- **JSON shape:** Identical to Dot plot with exactly two series. `showConnectors`
  may be set in `meta` or via the `show-connectors` controller attribute.
  ```json
  {
    "meta": { "title": "string", "orientation": "horizontal", "showConnectors": true },
    "categories": ["Region A", "Region B", "Region C"],
    "series": [
      { "name": "2020", "values": [45, 62, 38] },
      { "name": "2024", "values": [58, 55, 71] }
    ]
  }
  ```
- **SVG primitives:** `<line>` (connector between the two dots per category),
  `<circle>` (endpoint dots), `<text>`, `<g>`.
- **Orientation:** `horizontal` or `vertical`.
- **Variants / modes:** This is the `showConnectors=true` mode of `dotplot`.
  Semantically best with exactly two series; the renderer draws connectors for
  all adjacent series pairs if more than two are present.
- **Phase:** P2
- **Notes:** Connector line styled with `--mj-chart-connector-stroke` and
  `--mj-chart-connector-stroke-width`. Arrow heads on connectors are optional
  (`show-arrows` attribute, rendered as `<polygon>` or `<path>` arrowhead).

---

### Slope chart  *(slope graph, slopegraph)*

- **Renderer / `type`:** `slope` — **Primary renderer**
- **Controller:** `<mj-chart type="slope">`
- **Purpose:** Show the direction and magnitude of change for multiple entities
  between exactly two time points or states; best for ranked comparisons across
  two conditions.
- **Decomposition:**
  - `mj-chart-plot` — slope lines and endpoint dots
  - `mj-chart-axis` ×2 — one `kind="category"` axis per column (left and right),
    each with `kind="value"` — implemented as two independent value axes sharing
    the same `linear` scale
  - `mj-chart-legend`
  - `mj-chart-title`
  - `mj-chart-tooltip`
  - `mj-chart-value-labels` — inline labels at endpoints
  - `mj-chart-data-table`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "string" },
    "categories": ["2020", "2025"],
    "series": [
      { "name": "Company A", "values": [120, 185] },
      { "name": "Company B", "values": [200, 165] },
      { "name": "Company C", "values": [95,  210] }
    ]
  }
  ```
  `categories` must have exactly two entries (the two columns). `values` must
  have exactly two entries per series.
- **SVG primitives:** `<line>` (slope line), `<circle>` (endpoints),
  `<text>` (category column headers, endpoint value labels, series labels),
  `<g>`.
- **Orientation:** `n/a` — the chart is always rendered left-column to right-column.
- **Variants / modes:** None. For three or more time points, use a Line chart.
- **Phase:** P2
- **Notes:** Both columns share a single `linear` value scale, so slopes are
  visually accurate. Endpoint labels are right-aligned on the left column and
  left-aligned on the right column. Collision detection in `svgdraw.js` adjusts
  label y positions to avoid overlap. Lines are colored per series from the
  categorical token ramp.

---

### Radar chart  *(spider chart, web chart, star chart, polar area)*

- **Renderer / `type`:** `radar` — **Primary renderer**
- **Controller:** `<mj-chart type="radar">`
- **Purpose:** Compare multiple entities (series) across several quantitative
  dimensions simultaneously; surfaces multivariate profiles at a glance.
- **Decomposition:**
  - `mj-chart-plot` — radial axes, polygon/area fills, dot markers
  - `mj-chart-grid` — concentric ring gridlines (circular or polygonal)
  - `mj-chart-legend`
  - `mj-chart-title`
  - `mj-chart-tooltip`
  - `mj-chart-annotation` — reference rings
  - `mj-chart-data-table`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "string" },
    "categories": ["Speed", "Power", "Range", "Accuracy", "Reliability"],
    "series": [
      { "name": "Model X", "values": [80, 65, 90, 70, 85] },
      { "name": "Model Y", "values": [60, 90, 55, 88, 72] }
    ]
  }
  ```
  `categories` define the axes (spokes); `values` must have the same length as
  `categories`. Optional `"domainMin"` and `"domainMax"` per axis for
  independent axis scaling.
- **SVG primitives:** `<polygon>` or `<path>` (filled area per series),
  `<line>` (radial axis spokes), `<circle>` (ring gridlines or dot markers),
  `<text>` (axis labels at spoke tips, ring value labels), `<g>`.
- **Orientation:** `n/a` — the chart is radially symmetric; orientation does
  not apply.
- **Variants / modes:**
  - `fill="true"`: filled polygons with opacity (default).
  - `fill="false"`: outline only (line-only radar).
  - `grid-shape="circle"` vs `grid-shape="polygon"`: ring gridlines rendered as
    `<circle>` or `<polygon>`.
- **Phase:** P4
- **Notes:** Each spoke maps a `linear` scale from 0 (or `domainMin`) to
  `domainMax`. Spoke angles are evenly distributed: `2π / N` radians apart
  starting from the top (−π/2). Point positions are computed in `svgdraw.js`
  and joined as a `<polygon>` or `<path>`. With many overlapping series, fill
  opacity is reduced (default `--mj-chart-area-opacity: 0.3`). Accessibility:
  each spoke is labelled; data table provides the tabular alternative.

---

### Parallel coordinates plot  *(parallel coordinates chart)*

- **Renderer / `type`:** `parallel` — **Primary renderer**
- **Controller:** `<mj-chart type="parallel">`
- **Purpose:** Compare many numeric dimensions for multiple entities or
  observations simultaneously; useful for finding clusters, outliers, and
  cross-dimension correlations in high-dimensional data.
- **Decomposition:**
  - `mj-chart-plot` — vertical axes and polylines per series/observation
  - `mj-chart-axis` — one per dimension, each independently scaled and labeled
    (the renderer manages these internally; external `mj-chart-axis` parts are
    not used for parallel coordinates)
  - `mj-chart-brush` — per-axis range brush for interactive filtering
  - `mj-chart-legend`
  - `mj-chart-title`
  - `mj-chart-tooltip`
  - `mj-chart-data-table`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "string" },
    "dimensions": [
      { "name": "Height",  "domain": [0, 200], "unit": "cm" },
      { "name": "Weight",  "domain": [0, 150], "unit": "kg" },
      { "name": "Age",     "domain": [0, 100]             },
      { "name": "Score",   "domain": [0, 100]             }
    ],
    "series": [
      { "name": "Group A", "color": "optional",
        "observations": [
          [172, 68, 34, 82],
          [165, 55, 29, 91]
        ]
      }
    ]
  }
  ```
  `dimensions` replaces the common `categories` field for this chart type.
  Each observation row maps to `dimensions` by index. `domain` is required per
  dimension; the renderer builds an independent `linear` scale for each.
- **SVG primitives:** `<line>` (vertical axis lines), `<path>` (polyline per
  observation, using straight segments — `M x0,y0 L x1,y1 L x2,y2 …`),
  `<text>` (dimension labels, axis tick labels), `<rect>` (brush selection
  overlay), `<g>`.
- **Orientation:** `n/a` — axes are always vertical; the layout is fixed
  left-to-right.
- **Variants / modes:**
  - `curved="true"`: paths use `cubic-bezier` curves between axes for a
    smoother look (same `<path>` element, `C` commands instead of `L`).
  - `color-by="dimension-name"`: line color encodes the value on a named
    dimension using a sequential scale instead of a series categorical color.
- **Phase:** P4
- **Notes:** Each dimension has its own independent `linear` scale with the
  same pixel range (plot height). Dimension columns are evenly spaced
  horizontally. Brushing on an axis (`mj-chart-brush`) hides observations
  outside the selected range on that axis; multiple brushes AND together.
  With large datasets (> ~500 observations) lines are drawn at low opacity
  (`--mj-chart-parallel-opacity: 0.4`) to reveal density. Accessibility: the
  data table provides the full matrix; brushed state is reflected in the table.

---

<!-- renderer count: 7 primary renderers (bar, lollipop, dotplot, bullet, slope, radar, parallel) -->
