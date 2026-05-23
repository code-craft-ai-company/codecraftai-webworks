# Part-to-Whole Charts

> Catalog of part-to-whole chart types for the automojo-webworks SVG chart
> library. Architecture, the coordinated-element model, the part components,
> the JSON contract, and phasing are defined in `../../chart-components-plan.md`
> and are not repeated here.

---

### Pie Chart  *(circle chart, sector chart)*

- **Renderer / `type`:** `pie` — **Primary renderer**
- **Controller:** `<mj-chart type="pie" ...>`
- **Purpose:** Compare parts of a whole when there are a small number of slices and relative proportion is the primary message.
- **Decomposition:** `mj-chart-plot`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`, `mj-chart-value-labels`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Browser Share" },
    "categories": ["Chrome", "Safari", "Firefox", "Other"],
    "series": [
      { "name": "2025", "values": [62, 19, 4, 15] }
    ]
  }
  ```
  `categories` are the slice labels; `series[0].values` are the slice magnitudes. Only the first series is consumed; additional series are ignored. Values must be non-negative; the renderer sums them to compute proportions.
- **SVG primitives:** `<path>` (arc sectors via `svgdraw.arc()`), `<text>` (slice labels and percentage annotations), `<g>` (per-slice group)
- **Orientation:** `n/a` — pie charts have no meaningful horizontal/vertical orientation.
- **Variants / modes:**
  - `inner-radius` attribute > 0 → Donut chart (see entry below).
- **Phase:** P2
- **Notes:** Scales used: `ordinal-color` for slice fill. Angular domain is `[0, 2π]` mapped from the value sum. Labels are placed radially; an optional leader-line mode activates when slices are narrow. The renderer enforces a maximum of 12 slices before emitting `mj-chart-error` and collapsing excess slices into an "Other" segment.

---

### Donut Chart  *(doughnut chart, ring chart)*

- **Renderer / `type`:** `pie` — **Variant of `pie`**
- **Controller:** `<mj-chart type="pie" inner-radius="0.5" ...>`
- **Purpose:** Same as pie chart but reserves a center area, typically used for a summary KPI label or total annotation.
- **Decomposition:** `mj-chart-plot`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`, `mj-chart-value-labels`
- **JSON shape:** Identical to the `pie` renderer. The `inner-radius` attribute (0–1 as a fraction of outer radius, default `0.5`) activates donut mode; no JSON change is required.
  ```json
  {
    "meta": { "title": "Storage Used", "center-label": "84 GB" },
    "categories": ["Used", "Free"],
    "series": [
      { "name": "Disk", "values": [84, 16] }
    ]
  }
  ```
  The optional `meta.center-label` string is rendered as a `<text>` element at the geometric center.
- **SVG primitives:** `<path>` (annular sectors), `<text>` (center label, slice annotations), `<g>`
- **Orientation:** `n/a`
- **Variants / modes:** `inner-radius="0"` degrades to a standard pie.
- **Phase:** P2
- **Notes:** Implemented by the same `pie.js` renderer. The center label is drawn by the renderer when `meta.center-label` is present; it can also be supplied as a regular DOM child positioned via `anchor` over the plot.

---

### Stacked Bar Chart  *(stacked column chart)*

- **Renderer / `type`:** `bar` — **Variant of `bar`**
- **Controller:** `<mj-chart type="bar" group="stack" orientation="vertical" ...>`
- **Purpose:** Show how each category is composed of multiple sub-series, and compare absolute totals across categories.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (category + value), `mj-chart-grid`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`, `mj-chart-value-labels`, `mj-chart-annotation`
- **JSON shape:** Standard common envelope with multiple series:
  ```json
  {
    "meta": { "title": "Revenue by Region", "orientation": "vertical" },
    "categories": ["Q1", "Q2", "Q3", "Q4"],
    "series": [
      { "name": "North", "values": [120, 135, 148, 160] },
      { "name": "South", "values": [80,  95,  88,  102] },
      { "name": "West",  "values": [60,  70,  75,  90]  }
    ]
  }
  ```
- **SVG primitives:** `<rect>` (stacked segments per bar), `<text>` (optional segment and total labels), `<g>` (per-category group)
- **Orientation:** `horizontal` | `vertical` — `orientation` attribute swaps category and value axes; `bar` renderer handles both modes.
- **Variants / modes:** `group="cluster"` → grouped bar; `group="stack100"` → 100% stacked bar. All three modes live in `bar.js`.
- **Phase:** P1 (bar renderer); stacked mode enabled in P1.
- **Notes:** Value axis scale is `linear` over `[0, max-stack-total]`. Stacking is computed in `chartmodel.js` before the renderer runs. See the `bar` primary renderer entry in `01-comparison.md` for full axis and scale details.

---

### 100% Stacked Bar Chart  *(normalized stacked bar, relative composition bar)*

- **Renderer / `type`:** `bar` — **Variant of `bar`**
- **Controller:** `<mj-chart type="bar" group="stack100" orientation="vertical" ...>`
- **Purpose:** Compare the relative composition across categories when absolute magnitudes are less important than proportional breakdown.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (category + value, value axis labeled 0–100%), `mj-chart-grid`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`, `mj-chart-value-labels`
- **JSON shape:** Identical to the stacked bar. `chartmodel.js` normalizes each stack to 100% when `group="stack100"`.
  ```json
  {
    "meta": { "title": "Market Share by Quarter" },
    "categories": ["Q1", "Q2", "Q3", "Q4"],
    "series": [
      { "name": "Brand A", "values": [40, 38, 35, 33] },
      { "name": "Brand B", "values": [35, 37, 40, 42] },
      { "name": "Brand C", "values": [25, 25, 25, 25] }
    ]
  }
  ```
- **SVG primitives:** `<rect>`, `<text>`, `<g>` — same primitives as stacked bar; only the value scale changes.
- **Orientation:** `horizontal` | `vertical`
- **Variants / modes:** Reducing `stack100` to `stack` reverts to absolute stacked bar.
- **Phase:** P1 (enabled alongside stacked mode in `bar.js`).
- **Notes:** Value axis domain is fixed `[0, 100]`; tick labels are formatted as percentages. Tooltip shows both the absolute value and the percentage. No new renderer file — `bar.js` branch on `model.group`.

---

### Treemap  *(rectangular treemap, squarified treemap)*

- **Renderer / `type`:** `treemap` — **Primary renderer**
- **Controller:** `<mj-chart type="treemap" layout="squarify" ...>`
- **Purpose:** Visualize hierarchical part-to-whole data where area encodes magnitude and nesting encodes hierarchy; effective for spotting dominant nodes.
- **Decomposition:** `mj-chart-plot`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`, `mj-chart-legend`
- **JSON shape:** Hierarchical family shape (plan §3.4):
  ```json
  {
    "meta": { "title": "Global Revenue by Region and Product" },
    "root": {
      "name": "Total",
      "value": null,
      "children": [
        {
          "name": "EMEA",
          "value": null,
          "children": [
            { "name": "Software", "value": 420, "children": [] },
            { "name": "Services", "value": 180, "children": [] }
          ]
        },
        {
          "name": "AMER",
          "value": null,
          "children": [
            { "name": "Software", "value": 610, "children": [] },
            { "name": "Services", "value": 290, "children": [] }
          ]
        }
      ]
    }
  }
  ```
  `value` is `null` for internal nodes (summed from children by `chartmodel.js`) and a positive number for leaf nodes.
- **SVG primitives:** `<rect>` (one per node), `<text>` (node name and value inside rect; hidden when rect is too small), `<g>` (per-depth group for clip-path scope)
- **Orientation:** `n/a` — layout fills the available rectangle.
- **Variants / modes:**
  - `layout="squarify"` (default) — squarified tiling.
  - `layout="slice"` — row-only tiling.
  - `layout="dice"` — column-only tiling.
  - `layout="slice-dice"` — alternating (Treemap/Icicle mix).
  - Sunburst chart uses the same hierarchical layout engine with a polar projection (see entry below).
- **Phase:** P2
- **Notes:** Layout algorithm lives in `charts/core/hierarchylayout.js` (shared with Sunburst). Colors are assigned by `ordinal-color` scale at depth 1; child nodes are tinted lighter. Breadcrumb drill-down is an optional overlay using `mj-chart-annotation`.

---

### Sunburst Chart  *(radial treemap, multilevel pie)*

- **Renderer / `type`:** `sunburst` — **Variant of `treemap`**
- **Controller:** `<mj-chart type="sunburst" ...>`
- **Purpose:** Show hierarchical proportions in a radial layout where each ring represents one level of the hierarchy; supports drill-down interaction.
- **Decomposition:** `mj-chart-plot`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`, `mj-chart-legend`
- **JSON shape:** Identical hierarchical shape as Treemap (`root` with recursive `children` and leaf `value`).
  ```json
  {
    "meta": { "title": "File System Usage" },
    "root": {
      "name": "/",
      "value": null,
      "children": [
        {
          "name": "usr",
          "value": null,
          "children": [
            { "name": "lib",  "value": 3200, "children": [] },
            { "name": "bin",  "value": 800,  "children": [] }
          ]
        },
        { "name": "var", "value": 1500, "children": [] }
      ]
    }
  }
  ```
- **SVG primitives:** `<path>` (annular arc sectors via `svgdraw.arc()` for each node), `<text>` (radial labels for larger arcs), `<g>` (per-depth ring group)
- **Orientation:** `n/a`
- **Variants / modes:** `inner-radius="0"` collapses to a full multi-ring pie. The Icicle chart (linear icicle partition) uses the same layout engine with a Cartesian projection and is a further variant keyed `icicle`.
- **Phase:** P2
- **Notes:** Partitioning is computed by `hierarchylayout.js` (shared with Treemap); `sunburst.js` only applies the polar coordinate projection (`angle → arc path`). Click-to-zoom drill-down re-roots the visible subtree and re-calls the layout engine without re-fetching data.

---

### Waffle Chart  *(unit chart, grid chart, pictogram chart)*

- **Renderer / `type`:** `waffle` — **Primary renderer**
- **Controller:** `<mj-chart type="waffle" ...>`
- **Purpose:** Communicate a percentage or progress in a visually approachable grid of equal units; favored for dashboards and infographics over precise comparisons.
- **Decomposition:** `mj-chart-plot`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`, `mj-chart-legend`, `mj-chart-value-labels`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Survey Completion", "grid": { "cols": 10, "rows": 10 } },
    "categories": ["Complete", "Incomplete"],
    "series": [
      { "name": "Respondents", "values": [73, 27] }
    ]
  }
  ```
  `meta.grid.cols` and `meta.grid.rows` define the grid dimensions (default 10×10 = 100 cells). Each value is the count of cells assigned to that category; values must sum to `cols × rows`.
- **SVG primitives:** `<rect>` (one per cell, styled by category fill), `<text>` (center percentage label), `<g>` (grid row groups)
- **Orientation:** `n/a` — the grid fills the plot area. `meta.grid` controls shape.
- **Variants / modes:** Icon-based pictogram variant (replacing `<rect>` with a repeated `<path>` icon) is a future enhancement enabled by an optional `meta.icon` SVG path string.
- **Phase:** P2
- **Notes:** The renderer lays out cells in reading order (left-to-right, top-to-bottom). Color assignments use `ordinal-color` scale. Hover highlights the category group across all matching cells.

---

### Marimekko Chart  *(Mekko chart, mosaic bar chart)*

- **Renderer / `type`:** `marimekko` — **Primary renderer**
- **Controller:** `<mj-chart type="marimekko" ...>`
- **Purpose:** Show composition across two categorical dimensions simultaneously: bar width encodes the category's share of the whole, while bar segments show the internal breakdown.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (value axis: 0–100%), `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`, `mj-chart-legend`, `mj-chart-value-labels`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Revenue Mix by Country and Product" },
    "categories": ["Germany", "France", "UK"],
    "series": [
      { "name": "Hardware", "values": [50, 30, 45] },
      { "name": "Software", "values": [30, 55, 35] },
      { "name": "Services", "values": [20, 15, 20] }
    ]
  }
  ```
  Column widths are proportional to column totals; segment heights are proportional to each series value within the column total (normalized to 100%).
- **SVG primitives:** `<rect>` (one per cell, variable width and height), `<text>` (category and series labels), `<line>` (optional column separator), `<g>` (per-column group)
- **Orientation:** `n/a` — Marimekko layout is defined by its two-dimensional encoding; rotation is not meaningful.
- **Variants / modes:** None. The Mosaic plot (see below) is a distinct renderer with a statistical framing.
- **Phase:** P2
- **Notes:** Width scale is `linear` over the proportion of each column total to the grand total. Height segments are normalized per column. `chartmodel.js` computes column totals and proportions before rendering. Labels inside narrow columns are suppressed; a tooltip provides exact values.

---

### Mosaic Plot  *(mosaic chart, spine plot)*

- **Renderer / `type`:** `mosaic` — **Primary renderer**
- **Controller:** `<mj-chart type="mosaic" ...>`
- **Purpose:** Visualize the relationship and interaction between two categorical variables using area-encoded cells, similar to a Marimekko but emphasizing statistical frequency rather than business composition.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (both axes categorical), `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`, `mj-chart-legend`, `mj-chart-annotation`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Survival by Class and Sex" },
    "categories": ["1st", "2nd", "3rd", "Crew"],
    "series": [
      { "name": "Survived", "values": [203, 118, 178, 212] },
      { "name": "Died",     "values": [122, 167, 528, 673] }
    ]
  }
  ```
  Column widths proportional to column marginal totals; segment heights proportional to conditional frequency within the column. Optional Pearson residual coloring is activated via `meta.residuals: true`.
- **SVG primitives:** `<rect>` (variable-width, variable-height cells), `<text>` (axis labels, cell frequency labels), `<g>`
- **Orientation:** `n/a`
- **Variants / modes:** Spine plot is a degenerate mosaic where all column widths are equal (`meta.equal-widths: true`).
- **Phase:** P2
- **Notes:** Distinguished from Marimekko by statistical intent (contingency table input, optional residual coloring) rather than by renderer mechanism. May share layout geometry helpers with `marimekko.js` but is a separate renderer file to keep statistical logic isolated.

---

### Waterfall Chart  *(bridge chart, cascade chart)*

- **Renderer / `type`:** `waterfall` — **Primary renderer**
- **Controller:** `<mj-chart type="waterfall" ...>`
- **Purpose:** Show how an initial value is increased or decreased by a series of intermediate positive and negative contributions, arriving at a final total.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (category + value), `mj-chart-grid`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`, `mj-chart-value-labels`, `mj-chart-annotation`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Net Income Bridge" },
    "categories": ["Revenue", "COGS", "Gross Profit", "OpEx", "EBIT", "Tax", "Net Income"],
    "series": [
      {
        "name": "2025",
        "values": [1200, -480, null, -310, null, -82, null],
        "kinds":  ["start", "delta", "subtotal", "delta", "subtotal", "delta", "total"]
      }
    ]
  }
  ```
  Each element in `values` is the delta amount. `kinds` classifies bars: `"start"` is the opening bar (anchored at zero), `"delta"` floats above/below the running total, `"subtotal"` and `"total"` are grounded bars recomputed from the running sum. A `null` value signals a computed bar.
- **SVG primitives:** `<rect>` (floating delta bars, grounded start/total/subtotal bars), `<line>` (connectors between bars), `<text>` (value labels), `<g>`
- **Orientation:** `horizontal` | `vertical` — orientation swaps category (categorical `band` scale) and value (`linear`) axes.
- **Variants / modes:** None. Stacked waterfall (multiple series) is a future enhancement.
- **Phase:** P2
- **Notes:** Delta bars are positioned by computing running totals in `chartmodel.js`. Positive deltas use one token color, negative deltas another (`--mj-chart-positive`, `--mj-chart-negative`). Connector lines span from the top of one bar to the base of the next floating bar, drawn as `<line>` elements. Value axis domain must accommodate negative running totals.
