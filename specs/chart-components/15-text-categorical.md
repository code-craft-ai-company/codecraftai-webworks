# Text & Categorical Charts

> Catalog of chart types in this category for the automojo-webworks SVG chart
> library. Architecture, the coordinated-element model, the part components,
> the JSON contract, and phasing are defined in `../../chart-components-plan.md`
> and are not repeated here.

---

### Word Cloud  *(tag cloud, text cloud, wordle)*
- **Renderer / `type`:** `wordcloud` — **Primary renderer**
- **Controller:** `<mj-chart type="wordcloud" ...>`
- **Purpose:** Display a corpus of terms sized by frequency or weight — communicates the relative prominence of words in a body of text at a glance.
- **Decomposition:** `mj-chart-plot`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`.
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Support Ticket Topics" },
    "words": [
      { "text": "login",    "value": 842 },
      { "text": "password", "value": 610 },
      { "text": "billing",  "value": 530 },
      { "text": "crash",    "value": 317 },
      { "text": "slow",     "value": 289 }
    ],
    "max_words": 80,
    "rotation": "none"
  }
  ```
- **SVG primitives:** `<text>` (one per word, font-size driven by `sqrt` scale over word values, positioned by a collision-layout algorithm), `<g>` (layout container with `transform` for centering).
- **Orientation:** `n/a` — radial/free placement; orientation attribute ignored.
- **Variants / modes:** Rotated layout (`rotation="mixed"` allows ±90° word orientations); masked layout (`mask` field provides an SVG `<path>` boundary to constrain word placement).
- **Phase:** P5
- **Notes:** Font size is mapped through a `sqrt` scale (same scale type used for bubble radius, from `scales.js`) so large values do not visually overwhelm. Word placement uses a greedy spiral-packing layout built in the renderer — no external library. To avoid color-only encoding, word prominence is conveyed by font size; color is supplementary (categorical ramp from `--mj-chart-categorical-*` tokens). The data-table exposes term and frequency as a two-column sorted table for screen readers.

---

### Bar Chart  *(column chart, bar graph)*
- **Renderer / `type`:** `bar` — **Primary renderer**
- **Controller:** `<mj-chart type="bar" ...>`
- **Purpose:** Compare values across discrete categories using proportional rectangular bars — the canonical chart for categorical frequency comparison.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (category, `side="bottom"` for vertical / `side="start"` for horizontal), `mj-chart-axis` (value, `side="start"` for vertical / `side="bottom"` for horizontal), `mj-chart-grid`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-value-labels`, `mj-chart-data-table`.
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Downloads by Language", "orientation": "vertical" },
    "categories": ["Python", "JavaScript", "TypeScript", "Rust", "Go"],
    "series": [
      { "name": "2025", "values": [48200, 39100, 28700, 14300, 11800] }
    ]
  }
  ```
- **SVG primitives:** `<rect>` (one bar per category per series), `<text>` (axis tick labels, optional value labels), `<g>` (per-series groups).
- **Orientation:** `vertical` (bars rise from x-axis; default) and `horizontal` (bars extend from y-axis) — `orientation` attribute on the controller swaps which axis is category vs. value.
- **Variants / modes:** Grouped/clustered bars (`group="cluster"`), stacked bars (`group="stack"`), 100%-normalized stacked bars (`group="stack100"`). See **Stacked Bar Chart** entry below.
- **Phase:** P1
- **Notes:** The `bar` renderer is the foundational Cartesian renderer built first in Phase 1. It is reused by numerous variant entries in other catalog files — Churn chart and Segmentation chart in this file (`specs/chart-components/14-ux-product-business.md`), and ranked bar variants in `specs/chart-components/06-ranking.md`. Uses a `band` scale for categories and a `linear` scale for values. Negative values draw bars below (or left of) the zero baseline.

---

### Stacked Bar Chart  *(stacked column chart, segmented bar chart)*
- **Renderer / `type`:** `bar` — **Variant of `bar`**
- **Controller:** `<mj-chart type="bar" group="stack" ...>`
- **Purpose:** Show how a total is composed of multiple series contributions across categories — reveals both part-to-whole structure and cross-category trends simultaneously.
- **Decomposition:** Same as **Bar Chart** above. `mj-chart-legend` is particularly important for distinguishing stacked segments.
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Support Volume by Channel", "orientation": "vertical" },
    "categories": ["Jan", "Feb", "Mar", "Apr", "May"],
    "series": [
      { "name": "Email",   "values": [820, 910, 760, 840, 900] },
      { "name": "Chat",    "values": [340, 380, 420, 390, 450] },
      { "name": "Phone",   "values": [210, 190, 230, 200, 180] }
    ]
  }
  ```
- **SVG primitives:** `<rect>` (stacked segment per series per category), `<text>` (axis labels, optional segment value labels), `<g>` (per-series groups). Identical to the `bar` renderer primitives.
- **Orientation:** `vertical` and `horizontal` via the `bar` renderer's orientation swap.
- **Variants / modes:** 100%-normalized stacked bar (`group="stack100"`) normalizes each column to 100% to show proportional composition without absolute scale.
- **Phase:** P1
- **Notes:** Stacking is computed in `chartmodel.js` as a `d3-stack`-style cumulative offset pass over the series values. The `bar` renderer reads pre-stacked `[y0, y1]` segments directly. This renderer is also cross-referenced in `specs/chart-components/14-ux-product-business.md` (Segmentation chart) and `specs/chart-components/01-comparison.md`.

---

### Mosaic Plot  *(marimekko chart, mekko chart, mosaic chart)*
- **Renderer / `type`:** `mosaic` — **Primary renderer**
- **Controller:** `<mj-chart type="mosaic" ...>`
- **Purpose:** Display the joint distribution of two categorical variables — cell width encodes the marginal frequency of one variable, cell height encodes the conditional frequency of the other.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (x-category with proportional `band` widths, `side="bottom"`), `mj-chart-axis` (y-percentage 0–100 %, `side="start"`), `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-value-labels`, `mj-chart-data-table`.
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Market Share by Region" },
    "categories": ["North America", "Europe", "Asia", "Other"],
    "series": [
      { "name": "Brand A", "values": [420, 310, 580, 95] },
      { "name": "Brand B", "values": [310, 270, 390, 60] },
      { "name": "Brand C", "values": [180, 140, 210, 40] }
    ]
  }
  ```
- **SVG primitives:** `<rect>` (one cell per series per category, with variable x-width and y-height), `<text>` (axis tick labels, optional cell labels), `<g>` (per-column groups).
- **Orientation:** `n/a` — the x/y assignment is semantic (column width = category marginal, height = conditional share); swapping produces a different chart type.
- **Variants / modes:** None; the proportional width and stacked height are intrinsic to the mosaic encoding.
- **Phase:** P5
- **Notes:** Column widths are computed from the column totals `sum(series[i].values[col])` normalized across all columns to fill the plot width — a two-pass normalization in the renderer. Cell heights within a column are proportional to each series value relative to the column total (a `stack100` pass). Uses two `linear` scales: one for column-width fractions and one for the 0–100 % height axis. The `bar` renderer's `<rect>` drawing utility is reused for cells. This chart is cross-referenced from `specs/chart-components/14-ux-product-business.md` — Segmentation chart uses grouped bars rather than mosaic encoding.

---

### UpSet Plot  *(set intersection bar chart)*
- **Renderer / `type`:** `upset` — **Primary renderer**
- **Controller:** `<mj-chart type="upset" ...>`
- **Purpose:** Visualize the sizes of all intersections among three or more sets in a scalable matrix layout — the UpSet design is far more readable than a multi-set Venn diagram.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (intersection-size value, `side="start"`), `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`.
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Feature Co-Usage" },
    "sets": [
      { "name": "Export", "size": 3400 },
      { "name": "Share",  "size": 2100 },
      { "name": "Comment","size": 1800 },
      { "name": "Tag",    "size": 1200 }
    ],
    "intersections": [
      { "sets": ["Export", "Share"],           "size": 870 },
      { "sets": ["Export", "Comment"],         "size": 540 },
      { "sets": ["Share", "Comment"],          "size": 430 },
      { "sets": ["Export", "Share", "Comment"],"size": 210 }
    ]
  }
  ```
- **SVG primitives:** `<rect>` (intersection-size bars at the top, set-size bars on the left side), `<circle>` (filled dot per set in the membership matrix), `<line>` (vertical connector between filled dots in an intersection column), `<text>` (set names, size labels), `<g>` (regions: top bars, left bars, matrix).
- **Orientation:** `n/a` — the UpSet layout is a fixed two-region composition (bar area + matrix area); swapping is not meaningful.
- **Variants / modes:** Sorted by intersection size (default) or by degree (number of sets in the intersection), toggled by `sort="size|degree"`.
- **Phase:** P5
- **Notes:** The three regions (intersection bars, set bars, membership matrix) share the same `band` scale for columns. The intersection-size bars reuse the `bar` renderer's `<rect>` drawing utility. Dot membership matrix is drawn directly by the `upset` renderer. The data-table exposes each intersection's set membership and count as rows.

---

### Venn Diagram  *(two-set Venn, overlapping circles diagram)*
- **Renderer / `type`:** `venn` — **Primary renderer**
- **Controller:** `<mj-chart type="venn" ...>`
- **Purpose:** Show set overlap between two (or three) sets using overlapping circles — communicates which items belong exclusively to each set and which are shared.
- **Decomposition:** `mj-chart-plot`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`.
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Skill Overlap" },
    "sets": [
      { "name": "Frontend", "size": 120 },
      { "name": "Backend",  "size": 95 }
    ],
    "intersections": [
      { "sets": ["Frontend", "Backend"], "size": 38 }
    ]
  }
  ```
- **SVG primitives:** `<circle>` (one per set, fill semi-transparent via `fill-opacity`), `<text>` (set labels, intersection count labels), `<g>` (per-set groups).
- **Orientation:** `n/a` — radial/spatial layout; orientation attribute ignored.
- **Variants / modes:** Three-set Venn (three overlapping circles; same renderer handles up to three sets). For four or more sets, the **UpSet Plot** is the recommended alternative and is noted in the tooltip help text.
- **Phase:** P5
- **Notes:** Circle radii are proportional to `sqrt(size)` (using the `sqrt` scale from `scales.js`) so area encodes set size. Circle center positions are computed iteratively to achieve the correct intersection area overlap using a simple force-placement pass in the renderer. Color encoding uses the `--mj-chart-categorical-*` token ramp with `fill-opacity: 0.4` for the overlap region. The data-table lists each set name, exclusive count, and all intersection counts as rows.

---

### Euler Diagram  *(area-proportional Venn, Euler chart)*
- **Renderer / `type`:** `euler` — **Variant of `venn`**
- **Controller:** `<mj-chart type="euler" ...>`
- **Purpose:** Draw an area-proportional set diagram where circles (or ellipses) are positioned so their overlapping areas approximate the actual intersection sizes — more precise than a conventional Venn diagram but still intuitive.
- **Decomposition:** Same as **Venn Diagram** above.
- **JSON shape:** Identical to the **Venn Diagram** JSON shape; the renderer uses the same envelope with an optional `"proportional": true` flag (default for Euler).
  ```json
  {
    "meta": { "title": "Audience Overlap" },
    "sets": [
      { "name": "Email List",  "size": 5400 },
      { "name": "Social Fans", "size": 3200 },
      { "name": "App Users",   "size": 2800 }
    ],
    "intersections": [
      { "sets": ["Email List",  "Social Fans"], "size": 920 },
      { "sets": ["Email List",  "App Users"],   "size": 680 },
      { "sets": ["Social Fans", "App Users"],   "size": 430 },
      { "sets": ["Email List",  "Social Fans",  "App Users"], "size": 180 }
    ],
    "proportional": true
  }
  ```
- **SVG primitives:** `<circle>` or `<ellipse>` (sets), `<text>` (labels, counts), `<g>`. Identical to the `venn` renderer primitives.
- **Orientation:** `n/a`.
- **Variants / modes:** None separate from the `venn` renderer — `type="euler"` sets `proportional: true` as the default and allows ellipses when circles cannot achieve the target overlap.
- **Phase:** P5
- **Notes:** When circles alone cannot satisfy the area constraints (a common occurrence with three or more sets), the renderer falls back to ellipses (`<ellipse>` SVG primitive with a `transform="rotate(...)"` attribute). Placement uses an iterative numerical optimization pass seeded by the `venn` initial positions. For four or more sets the renderer emits an `mj-chart-error` recommendation to use `type="upset"` instead.

---

### Matrix Chart  *(categorical matrix, cross-tab chart, bubble matrix)*
- **Renderer / `type`:** `matrix` — **Primary renderer**
- **Controller:** `<mj-chart type="matrix" ...>`
- **Purpose:** Display relationships between two categorical dimensions using a grid of marks (circles, squares, or color fills) sized or colored by a third numeric measure.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (x-category, `side="bottom"`), `mj-chart-axis` (y-category, `side="start"`), `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`.
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Team Collaboration Frequency" },
    "x_categories": ["Design", "Engineering", "Product", "Marketing", "Sales"],
    "y_categories": ["Design", "Engineering", "Product", "Marketing", "Sales"],
    "cells": [
      { "x": "Design",      "y": "Engineering", "value": 42 },
      { "x": "Design",      "y": "Product",     "value": 87 },
      { "x": "Engineering", "y": "Product",     "value": 95 }
    ],
    "mark": "circle"
  }
  ```
- **SVG primitives:** `<circle>` (for `mark="circle"`, radius ∝ `sqrt` scale of value), `<rect>` (for `mark="square"`, area ∝ value; or for color-fill mode), `<text>` (axis tick labels, optional cell value labels), `<g>` (row and column groups).
- **Orientation:** `n/a` — the x/y grid assignment is semantically fixed by the two categorical axes.
- **Variants / modes:** Circle matrix (`mark="circle"`, size-encoded); square/color matrix (`mark="square"`, color-encoded — delegates cell fill to the `heatmap` renderer's color-scale logic). Correlation matrix is a special case of `mark="square"` with a diverging color scale, cross-referenced in `specs/chart-components/04-relationship-correlation.md`.
- **Phase:** P5
- **Notes:** For `mark="circle"` mode, mark radius uses a `sqrt` scale over `[0, max(cell.value)]` to ensure area (not radius) is proportional to value. For `mark="square"` color mode, the fill logic reuses the `heatmap` renderer's `--mj-chart-sequential-*` or `--mj-chart-diverging-*` token ramp (see **Heatmap** in `specs/chart-components/14-ux-product-business.md`). Size encoding is never the sole encoding — tooltip and the data-table always expose the exact numeric value.

---

### Sentiment Chart  *(sentiment breakdown chart, opinion bar, sentiment distribution)*
- **Renderer / `type`:** `sentiment` — **Variant of `bar`**
- **Controller:** `<mj-chart type="sentiment" ...>`
- **Purpose:** Show the proportion of positive, neutral, and negative sentiment across categories (topics, products, time periods) — used for survey, review, and social-listening analytics.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (category, `side="start"` for horizontal default), `mj-chart-axis` (value −100 % to +100 %, `side="bottom"`), `mj-chart-grid` (zero-line), `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-value-labels`, `mj-chart-data-table`.
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Product Review Sentiment", "orientation": "horizontal" },
    "categories": ["Battery Life", "Camera", "Display", "Performance", "Price"],
    "series": [
      { "name": "Positive", "values": [65, 72, 81, 58, 43] },
      { "name": "Neutral",  "values": [20, 18, 12, 25, 30] },
      { "name": "Negative", "values": [15, 10,  7, 17, 27] }
    ]
  }
  ```
- **SVG primitives:** `<rect>` (diverging bars: positive extends right from center, negative extends left, neutral straddles center), `<line>` (zero/center axis line), `<text>` (axis labels, percentage labels), `<g>` (per-series and per-category groups). Same primitives as the `bar` renderer.
- **Orientation:** `horizontal` (categories on y-axis, sentiment diverges left/right; default and canonical); `vertical` supported via the `bar` renderer's orientation swap.
- **Variants / modes:** Stacked diverging (`group="stack"`, all three segments stacked from a center baseline); percentage-normalized (`group="stack100"` normalizes to 100 % total).
- **Phase:** P5
- **Notes:** No new renderer code; `type="sentiment"` is the `bar` renderer configured with a diverging layout where negative-series values are negated and drawn from the zero baseline in the opposite direction. The center-zero baseline is enforced by the `linear` scale's domain. Positive/neutral/negative encoding uses semantic token colors (`--mj-color-success`, `--mj-color-neutral`, `--mj-color-danger`) and never relies on color alone — segment labels and tooltip text always name the sentiment tier. The `bar` renderer is defined in the **Bar Chart** entry above and in `specs/chart-components/01-comparison.md`.
