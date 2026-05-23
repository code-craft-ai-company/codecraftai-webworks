# Ranking Charts

> Catalog of ranking chart types for the automojo-webworks SVG chart
> library. Architecture, the coordinated-element model, the part components,
> the JSON contract, and phasing are defined in `../../chart-components-plan.md`
> and are not repeated here.

Most ranking charts are the `bar`, `line`, or `scatter` renderers operated in
a sorted mode. They are documented as variants of their primary renderer and
consolidated onto that renderer's file. Only charts with layout logic that
cannot be expressed as an attribute of an existing renderer become new primary
renderers.

---

### Sorted Bar Chart  *(ranked bar chart, ordered column chart)*

- **Renderer / `type`:** `bar` — **Variant of `bar`**
- **Controller:** `<mj-chart type="bar" sort="desc" orientation="horizontal" ...>`
- **Purpose:** Rank a set of categories by a single quantitative measure so the viewer can immediately identify the highest, lowest, and relative positions.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (category + value), `mj-chart-grid`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`, `mj-chart-value-labels`, `mj-chart-annotation`
- **JSON shape:** Standard common envelope. Sorting is specified in the controller attribute (`sort="asc|desc|none"`), not in JSON, so the same dataset can be re-ordered without mutation.
  ```json
  {
    "meta": { "title": "Top Countries by GDP", "orientation": "horizontal" },
    "categories": ["USA", "China", "Germany", "Japan", "India"],
    "series": [
      { "name": "GDP (USD tn)", "values": [25.5, 17.7, 4.1, 4.2, 3.4] }
    ]
  }
  ```
- **SVG primitives:** `<rect>` (bars), `<text>` (axis labels, value labels), `<g>`
- **Orientation:** `horizontal` is idiomatic for ranked bars (label readability); `vertical` is supported.
- **Variants / modes:**
  - `sort="desc"` (default ranking) / `sort="asc"` (reverse ranking).
  - `sort="none"` reverts to an unordered comparison bar chart.
  - `group="cluster"` + `sort` → sorted grouped bar.
  - See `01-comparison.md` for the `bar` primary renderer.
- **Phase:** P1 (`sort` attribute added alongside the base `bar` renderer; no new renderer file).
- **Notes:** `chartmodel.js` re-indexes categories and values together when `sort` is set, preserving series alignment. Rank numbers can be drawn as a leading `<text>` element in the bar or on the category axis label via a `meta.show-rank: true` flag.

---

### Pareto Chart  *(Pareto diagram, 80/20 chart)*

- **Renderer / `type`:** `pareto` — **Primary renderer**
- **Controller:** `<mj-chart type="pareto" ...>`
- **Purpose:** Rank categories by descending frequency or cost and overlay a cumulative percentage line to identify the "vital few" contributors (the 80/20 rule).
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (category, left value for bars, right value for cumulative % line), `mj-chart-grid`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`, `mj-chart-value-labels`, `mj-chart-annotation`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Defect Frequency by Type" },
    "categories": ["Scratch", "Dent", "Discolor", "Crack", "Missing"],
    "series": [
      { "name": "Count", "values": [85, 53, 30, 21, 11] }
    ]
  }
  ```
  The renderer sorts categories by descending value, computes cumulative percentages internally, and produces the dual-scale layout automatically. The data need not be pre-sorted.
- **SVG primitives:** `<rect>` (sorted frequency bars), `<path>` (cumulative % polyline via `svgdraw.line()`), `<circle>` (data points on the cumulative line), `<text>` (axis labels, optional 80% reference annotation), `<line>` (reference line at 80%), `<g>`
- **Orientation:** `vertical` only — Pareto convention requires bars descending left-to-right.
- **Variants / modes:** None. Pareto is a distinct renderer because it requires a dual value axis (absolute counts left, cumulative % right) and mandatory sort, which cannot be expressed cleanly as `bar` attributes.
- **Phase:** P2
- **Notes:** Left value axis: `linear` scale over `[0, grand total]`. Right value axis: `linear` scale fixed `[0, 100]` (percentage). The cumulative line is drawn by the same renderer file; no second series needs to be supplied in JSON. A reference annotation at 80% on the right axis is drawn automatically via the `mj-chart-annotation` protocol; it can be suppressed with `meta.pareto-line: false`.

---

### Bump Chart  *(rank-over-time chart, ranking timeline)*

- **Renderer / `type`:** `bump` — **Primary renderer**
- **Controller:** `<mj-chart type="bump" ...>`
- **Purpose:** Show how entities change rank position across a sequence of time periods or ordered categories; emphasizes crossings and relative movement rather than absolute values.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (time/ordinal X, rank Y — inverted so rank 1 is at top), `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`, `mj-chart-annotation`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Programming Language Popularity Rank" },
    "categories": ["2021", "2022", "2023", "2024", "2025"],
    "series": [
      { "name": "Python",     "values": [1, 1, 1, 1, 1] },
      { "name": "JavaScript", "values": [2, 2, 2, 3, 2] },
      { "name": "Java",       "values": [3, 3, 3, 2, 3] },
      { "name": "C++",        "values": [4, 5, 4, 4, 4] },
      { "name": "Rust",       "values": [null, null, 8, 6, 5] }
    ]
  }
  ```
  `values` are rank positions (1 = best). `null` means the entity was not ranked in that period; the line is broken. The Y axis domain is `[1, max-rank]`, inverted.
- **SVG primitives:** `<path>` (smoothed S-curve connecting rank positions via `svgdraw.curve()`), `<circle>` (rank dots at each period), `<text>` (entity name labels at start and/or end of line), `<g>` (per-series group)
- **Orientation:** `n/a` — bump charts are always horizontal (time/ordinal left-to-right, rank top-to-bottom). The rank Y axis is necessarily inverted.
- **Variants / modes:** `meta.show-values: true` replaces rank integers with raw values on the Y axis (value bump chart). This is a display mode, not a separate renderer.
- **Phase:** P5
- **Notes:** A new primary renderer because the inverted ordinal rank axis and the S-curve interpolation between discrete rank positions cannot be expressed as a `line` renderer variant without special-casing that would pollute `line.js`. Color is assigned per series via `ordinal-color`. Interactive hover highlights the hovered series and dims others.

---

### Lollipop Chart  *(lollipop ranking chart, dot-and-stick chart)*

- **Renderer / `type`:** `lollipop` — **Variant of `bar`**
- **Controller:** `<mj-chart type="lollipop" sort="desc" ...>`
- **Purpose:** Rank categories with a cleaner, less visually heavy alternative to a full bar; the stick makes small differences more legible and reduces ink-to-data ratio.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (category + value), `mj-chart-grid`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`, `mj-chart-value-labels`
- **JSON shape:** Identical to sorted bar chart — standard common envelope with `sort` controlled by the attribute.
  ```json
  {
    "meta": { "title": "Employee Satisfaction Score" },
    "categories": ["Engineering", "Design", "Sales", "Support", "Marketing"],
    "series": [
      { "name": "Score", "values": [8.4, 7.9, 7.2, 8.1, 6.8] }
    ]
  }
  ```
- **SVG primitives:** `<line>` (the stick from axis baseline to dot), `<circle>` (the dot at the data value), `<text>` (axis labels, optional value labels), `<g>`
- **Orientation:** `horizontal` | `vertical`
- **Variants / modes:** `sort="none"` degrades to an unranked lollipop comparison chart.
- **Phase:** P2
- **Notes:** Implemented in `bar.js` under a `style="lollipop"` branch: the renderer emits `<line>` + `<circle>` instead of `<rect>`. Dot radius comes from the `--mj-chart-dot-radius` design token. Sorting is handled the same way as for sorted bar (category re-indexing in `chartmodel.js`).

---

### Dot Ranking Chart  *(dot plot, Cleveland dot plot)*

- **Renderer / `type`:** `dotplot` — **Variant of `scatter`**
- **Controller:** `<mj-chart type="dotplot" sort="desc" ...>`
- **Purpose:** Provide a compact ordered comparison of a single quantitative measure across many categories, especially effective when bar height would waste space on a sparse dataset.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (category + value), `mj-chart-grid`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`, `mj-chart-value-labels`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "City Population Density" },
    "categories": ["Tokyo", "Seoul", "Mumbai", "Cairo", "Lagos"],
    "series": [
      { "name": "People/km²", "values": [6158, 16364, 20694, 19376, 13123] }
    ]
  }
  ```
  When two series are supplied, the renderer draws a connected dot pair (dumbbell / DNA chart) to highlight the gap.
- **SVG primitives:** `<circle>` (dots), `<line>` (connecting line in dumbbell variant), `<text>` (axis labels, optional value labels), `<g>`
- **Orientation:** `horizontal` | `vertical`
- **Variants / modes:**
  - Two-series input → dumbbell chart (dot pair connected by a `<line>`).
  - `sort="none"` → unranked Cleveland dot plot.
  - See `04-relationship.md` for the `scatter` primary renderer.
- **Phase:** P2
- **Notes:** Differs from a lollipop in that there is no baseline stick to zero; dots are placed directly at their value on the value axis. Implemented as a thin mode in `scatter.js` where the category axis uses a `band` scale (as in bar charts) rather than a continuous `linear` or `time` scale.

---

### Slope Chart  *(slope graph, slopegraph)*

- **Renderer / `type`:** `slope` — **Variant of `line`**
- **Controller:** `<mj-chart type="slope" ...>`
- **Purpose:** Highlight rank or value change between exactly two periods for multiple entities; named lines make individual trajectories easy to trace.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (two-point ordinal X, value Y), `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`, `mj-chart-legend`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Executive Approval: Before vs After" },
    "categories": ["Before", "After"],
    "series": [
      { "name": "Policy A", "values": [72, 58] },
      { "name": "Policy B", "values": [45, 63] },
      { "name": "Policy C", "values": [81, 79] }
    ]
  }
  ```
  Exactly two `categories` entries are expected. The renderer emits `mj-chart-error` if more than two are supplied, guiding the author toward a line chart instead.
- **SVG primitives:** `<line>` (one slope line per series, straight — no curve interpolation), `<circle>` (endpoints), `<text>` (entity name labels at left and right endpoints, value annotations), `<g>`
- **Orientation:** `n/a` — left column is always "before", right column is always "after"; rotation is not meaningful.
- **Variants / modes:** For more than two time periods, use `type="line"` (see `02-trend.md`). For rank positions specifically, use `type="bump"`.
- **Phase:** P5
- **Notes:** Implemented in `line.js` under a `style="slope"` branch: the renderer enforces the two-period constraint, draws straight `<line>` segments (no `svgdraw.curve()`), and places inline text labels at endpoints rather than relying on `mj-chart-axis`. Label collision detection offsets overlapping right-side labels vertically.

---

### Leaderboard Table with Bars  *(ranked table, bar-in-table ranking)*

- **Renderer / `type`:** `bar` — **Variant of `bar`**
- **Controller:** `<mj-chart type="bar" style="leaderboard" sort="desc" ...>`
- **Purpose:** Present ranked data in a tabular format where a proportional bar inside each row provides visual magnitude at a glance, combining the precision of a table with the quick scanning of a bar chart.
- **Decomposition:** `mj-chart-plot`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`, `mj-chart-value-labels`
- **JSON shape:**
  ```json
  {
    "meta": {
      "title": "Sales Leaderboard",
      "columns": ["Rank", "Name", "Region", "Revenue", "Bar"]
    },
    "categories": ["Alice", "Bob", "Carol", "David", "Eve"],
    "series": [
      { "name": "Revenue", "values": [420000, 385000, 310000, 275000, 240000] }
    ]
  }
  ```
  `meta.columns` lists the visible column headers; `"Bar"` is the reserved keyword for the inline bar column. Additional `series` entries can supply text columns (e.g. Region) rendered as plain text cells.
- **SVG primitives:** `<rect>` (proportional inline bar), `<text>` (rank number, label, numeric value, column headers), `<line>` (optional row separator), `<g>` (per-row group)
- **Orientation:** `vertical` (rows top-to-bottom) only; the bar within each row is always horizontal.
- **Variants / modes:** `sort="asc"` reverses rank order. `style="leaderboard"` on a multi-series `bar` controller adds secondary text columns. Degrades to a plain sorted bar if `meta.columns` is absent.
- **Phase:** P5
- **Notes:** The leaderboard layout is a table-like arrangement of SVG rows, not an HTML `<table>`. The `mj-chart-data-table` part always provides the accessible HTML table equivalent. The proportional bar width uses a `linear` scale over `[0, max-value]`. Row height is derived from the `--mj-chart-row-height` token.
