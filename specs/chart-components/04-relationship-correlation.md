# Relationship & Correlation Charts

> Catalog of chart types in this category for the codecraftai-webworks SVG chart
> library. Architecture, the coordinated-element model, the part components,
> the JSON contract, and phasing are defined in `../../chart-components-plan.md`
> and are not repeated here.

Charts in this category reveal associations, correlations, and density patterns
between two or more numeric variables. Three primary renderers cover all ten
entries: `scatter` (points and paths), `heatmap` (grid-cell intensity), and
`density` (continuous density surfaces).

---

### Scatter plot  *(XY plot, point chart)*

- **Renderer / `type`:** `scatter` — **Primary renderer**
- **Controller:** `<mj-chart type="scatter" ...>`
- **Purpose:** Show the relationship between two numeric variables; reveal
  clusters, trends, and outliers in bivariate data.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (x, value; y, value),
  `mj-chart-grid`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`,
  `mj-chart-crosshair`, `mj-chart-brush`, `mj-chart-annotation`,
  `mj-chart-data-table`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Height vs Weight", "orientation": "vertical" },
    "series": [
      {
        "name": "Group A",
        "color": "optional",
        "points": [
          { "x": 1.72, "y": 68.5, "label": "optional" },
          { "x": 1.85, "y": 82.1 }
        ]
      }
    ]
  }
  ```
  Each `series[].points` entry carries `x` (numeric) and `y` (numeric).
  The `size` field is absent for scatter; it is added by the bubble variant.
  The optional `label` annotates individual points.
- **SVG primitives:** `<circle>` (one per point), `<g>` (series group),
  `<text>` (point labels when enabled)
- **Orientation:** `n/a` — axes are always x (horizontal) and y (vertical);
  swapping them changes the data meaning, not a rendering orientation.
- **Variants / modes:** Bubble chart (adds `size` field and a sqrt scale),
  Connected scatter plot (adds `path` mode joining points in data order),
  Residual plot (same renderer; residual values on y-axis).
- **Phase:** P1
- **Notes:** Uses `linear` scales for both axes. The renderer plots each
  series as a `<g>` of `<circle>` elements. Point shape can be varied per
  series (`circle`, `square`, `triangle`, `diamond`) via a series-level
  `shape` field, ensuring encoding is never color-only. The `mj-chart-brush`
  part enables rectangular range selection for zoom or filtering.

---

### Bubble chart  *(bubble plot)*

- **Renderer / `type`:** `scatter` — **Variant of `scatter`**
- **Controller:** `<mj-chart type="scatter" bubble="true" ...>`
- **Purpose:** Extend a scatter plot with a third numeric variable encoded as
  circle area, enabling simultaneous inspection of three dimensions.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (x, value; y, value),
  `mj-chart-grid`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`,
  `mj-chart-data-table`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "GDP vs Life Expectancy" },
    "series": [
      {
        "name": "2025",
        "points": [
          { "x": 45000, "y": 78.4, "size": 331000000, "label": "USA" },
          { "x": 12000, "y": 72.1, "size": 1400000000, "label": "IND" }
        ]
      }
    ]
  }
  ```
  `size` is a raw numeric value (e.g. population); the renderer applies a
  `sqrt` scale mapping it to pixel radius so area is proportional to value.
- **SVG primitives:** `<circle>` (radius from sqrt scale), `<g>`, `<text>`
  (point labels)
- **Orientation:** `n/a` — same as scatter.
- **Variants / modes:** Activated via `bubble="true"` on the controller;
  no separate renderer file. Size-scale legend (showing example bubble sizes)
  is rendered inside `mj-chart-legend` when `bubble="true"`.
- **Phase:** P3
- **Notes:** The `sqrt` scale (`scales.js`) maps `size` domain to a pixel
  radius range (e.g. 4–40 px) so that perceived area is proportional to
  value. The renderer clamps bubbles that would overlap the plot boundary.
  Accessibility: tooltip and data-table expose the raw `size` value with a
  configurable `size-label` attribute (e.g. `size-label="Population"`).

---

### Connected scatter plot  *(sequence plot, path scatter)*

- **Renderer / `type`:** `scatter` — **Variant of `scatter`**
- **Controller:** `<mj-chart type="scatter" connected="true" ...>`
- **Purpose:** Reveal how a relationship between two variables evolves over a
  sequence or time, by drawing a path that joins points in their data order.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (x, value; y, value),
  `mj-chart-grid`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`,
  `mj-chart-data-table`, `mj-chart-annotation`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Unemployment vs Inflation Over Time" },
    "series": [
      {
        "name": "Economy",
        "points": [
          { "x": 4.2, "y": 2.1, "label": "2020" },
          { "x": 6.7, "y": 5.4, "label": "2021" },
          { "x": 3.9, "y": 8.0, "label": "2022" }
        ]
      }
    ]
  }
  ```
  Points are rendered in array order; the optional `label` appears as a
  text annotation beside each point.
- **SVG primitives:** `<path>` (polyline connecting points in order),
  `<circle>` (one per point), `<text>` (sequence labels), `<g>`
- **Orientation:** `n/a` — same as scatter.
- **Variants / modes:** Activated via `connected="true"`; the scatter
  renderer draws a `<path>` through the series points using `svgdraw.js`
  line-builder before drawing the circles on top.
- **Phase:** P3
- **Notes:** Path draw order follows data array index, not x-sort, so the
  line traces the actual sequence. Arrowheads (`<marker>` defs) can be
  enabled via `arrows="true"` to show direction of travel along the path.

---

### Hexbin plot  *(hexagonal binning)*

- **Renderer / `type`:** `hexbin` — **Primary renderer**
- **Controller:** `<mj-chart type="hexbin" ...>`
- **Purpose:** Summarize very dense scatter data by aggregating points into
  hexagonal bins and encoding bin count (or a statistic) as fill color or
  hexagon size.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (x, value; y, value),
  `mj-chart-grid`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`,
  `mj-chart-data-table`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Event Density" },
    "series": [
      {
        "name": "Events",
        "points": [
          { "x": 2.3, "y": 5.1 },
          { "x": 2.4, "y": 5.2 }
        ]
      }
    ],
    "hexbin": {
      "radius": 20,
      "stat": "count"
    }
  }
  ```
  Raw `points` are identical to the scatter shape. The `hexbin` config
  block sets the bin radius in pixels and the aggregation statistic
  (`count`, `sum`, `mean`). When `stat` is `sum` or `mean`, each point
  should carry a `value` field.
- **SVG primitives:** `<polygon>` (six-sided hexagon per bin), `<g>`,
  `<text>` (optional count labels inside bins)
- **Orientation:** `n/a` — hexagonal grid is symmetric; no swap applies.
- **Variants / modes:** Color-encoded bins (fill by count/stat — default)
  or size-encoded bins (radius proportional to count, `encoding="size"`).
- **Phase:** P3
- **Notes:** The hexbin layout algorithm is implemented in the renderer
  (`charts/core/renderers/hexbin.js`) using offset-grid geometry; it does
  not depend on an external library. Each hexagon vertex list is computed
  from center coordinates by `svgdraw.js` hex-path helper. The color ramp
  is a sequential `ordinal-color` scale from design tokens, overridable
  via `--mj-chart-heat-*` tokens.

---

### 2D density plot  *(bivariate density, kernel density 2D)*

- **Renderer / `type`:** `density` — **Primary renderer**
- **Controller:** `<mj-chart type="density" ...>`
- **Purpose:** Estimate and display the joint probability density of two
  numeric variables across a continuous surface, useful for revealing the
  underlying distribution in dense scatter data.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (x, value; y, value),
  `mj-chart-grid`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`,
  `mj-chart-data-table`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "2D Density of X vs Y" },
    "series": [
      {
        "name": "Observations",
        "points": [
          { "x": 1.4, "y": 3.2 },
          { "x": 1.6, "y": 3.8 }
        ]
      }
    ],
    "density": {
      "bandwidth": "auto",
      "resolution": 64,
      "style": "fill"
    }
  }
  ```
  `bandwidth` controls the kernel bandwidth (`auto` uses Silverman's rule).
  `resolution` is the grid cell count per axis. `style` is `fill`
  (filled color surface), `contour` (iso-lines only), or `both`.
- **SVG primitives:** `<rect>` (rasterized grid cells for fill style),
  `<path>` (iso-contour lines for contour style), `<g>`
- **Orientation:** `n/a` — both axes are numeric value axes.
- **Variants / modes:** `style="contour"` produces the contour plot variant;
  `style="fill"` is the 2D density heatmap; `style="both"` overlays both.
  The contour plot is therefore a mode of the `density` renderer.
- **Phase:** P4
- **Notes:** The renderer computes a 2D KDE on a `resolution × resolution`
  grid using a Gaussian kernel. For the fill style, grid cells become
  `<rect>` elements colored by a sequential color scale. For the contour
  style, the marching-squares algorithm (implemented in `svgdraw.js`)
  traces iso-level `<path>` elements. Large point sets are downsampled to
  a configurable `max-points` before KDE to keep computation bounded.

---

### Contour plot  *(iso-contour plot, level-set plot)*

- **Renderer / `type`:** `density` — **Variant of `density`**
- **Controller:** `<mj-chart type="density" density.style="contour" ...>`
- **Purpose:** Show lines of equal density or equal value (iso-contours)
  across a 2D space, conveying structure, peaks, and gradients.
- **Decomposition:** Same as 2D density plot.
- **JSON shape:** Same as 2D density plot. When the input data is a
  pre-computed grid rather than raw points, use:
  ```json
  {
    "meta": { "title": "Elevation Contours" },
    "density": { "style": "contour", "levels": 10 },
    "grid": {
      "x": [0, 1, 2, 3],
      "y": [0, 1, 2, 3],
      "z": [[0.1, 0.4, 0.3, 0.1], [0.2, 0.9, 0.7, 0.2]]
    }
  }
  ```
  When `grid` is present the KDE step is skipped; marching squares runs
  directly on the supplied z-values.
- **SVG primitives:** `<path>` (one closed or open path per iso-level),
  `<text>` (optional level labels), `<g>`
- **Orientation:** `n/a`
- **Variants / modes:** Pure mode of `density` renderer via
  `density.style="contour"`. Filled contour (choropleth-style bands) is
  `density.style="both"` with `opacity` on fill.
- **Phase:** P4
- **Notes:** This entry exists as a named catalog entry because "contour
  plot" is a commonly searched chart type. Implementation is entirely within
  the `density` renderer; no separate file is created. Level count defaults
  to 10; iso-values are evenly spaced across the density range.

---

### Correlation matrix  *(correlation heatmap)*

- **Renderer / `type`:** `heatmap` — **Variant of `heatmap`**
- **Controller:** `<mj-chart type="heatmap" value-source="correlation" ...>`
- **Purpose:** Display pairwise correlation coefficients between multiple
  numeric variables as a symmetric color-encoded grid.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (x, category/band;
  y, category/band), `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`,
  `mj-chart-data-table`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Variable Correlations" },
    "categories": ["Age", "Income", "Spend", "Score"],
    "series": [
      { "name": "Age",    "values": [1.00,  0.42, 0.31, -0.15] },
      { "name": "Income", "values": [0.42,  1.00, 0.78,  0.20] },
      { "name": "Spend",  "values": [0.31,  0.78, 1.00,  0.10] },
      { "name": "Score",  "values": [-0.15, 0.20, 0.10,  1.00] }
    ]
  }
  ```
  `categories` names the columns; `series[i].name` names the rows;
  `series[i].values[j]` is the cell value at row i, column j. Values are
  expected in [-1, 1] for a correlation matrix; the renderer uses a
  diverging color scale centered at 0.
- **SVG primitives:** `<rect>` (one per cell), `<text>` (optional cell
  value labels, correlation coefficient), `<g>`
- **Orientation:** `n/a` — the grid is symmetric; rotation is meaningless.
- **Variants / modes:** Mode of the `heatmap` renderer. A diverging color
  scale (negative = one hue, zero = neutral, positive = opposite hue) is
  automatically applied when `value-source="correlation"`.
- **Phase:** P3
- **Notes:** The grid axes use `band` scales so cells are evenly spaced.
  The renderer optionally draws a diagonal divider line and can suppress the
  upper or lower triangle (`triangle="upper|lower|full"`). Circle encoding
  (circle area proportional to |r|, color for sign) is available via
  `mark="circle"`.

---

### Heatmap  *(intensity map, heat grid)*

- **Renderer / `type`:** `heatmap` — **Primary renderer**
- **Controller:** `<mj-chart type="heatmap" ...>`
- **Purpose:** Encode a scalar intensity value across two categorical or
  ordinal dimensions as a color-filled grid, revealing patterns by position
  and hue.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (x, category/band;
  y, category/band), `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`,
  `mj-chart-data-table`, `mj-chart-annotation`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Weekly Activity Heatmap" },
    "categories": ["Mon", "Tue", "Wed", "Thu", "Fri"],
    "series": [
      { "name": "08:00", "values": [12, 45, 38, 52, 20] },
      { "name": "09:00", "values": [80, 95, 88, 91, 60] },
      { "name": "10:00", "values": [55, 70, 66, 78, 40] }
    ]
  }
  ```
  `categories` defines the x-axis (columns); each `series` entry defines
  one row, and its `values` array has one entry per category. Cell value
  drives the fill color via a sequential or diverging scale.
- **SVG primitives:** `<rect>` (one per cell), `<text>` (optional value
  labels), `<g>`
- **Orientation:** `n/a` — the grid is a fixed 2D layout; no swap is
  meaningful.
- **Variants / modes:** Correlation matrix (`value-source="correlation"`,
  diverging scale), 2D density heatmap (grid supplied by `density` renderer
  via `grid` block), Calendar heatmap (P5 — day/week axes, special layout).
- **Phase:** P3
- **Notes:** Both axes use `band` scales. Color scale defaults to a
  sequential single-hue ramp from `--mj-chart-heat-*` tokens; set
  `scale="diverging"` for a two-hue ramp centered at a configurable midpoint.
  Cell gap (`gap` attribute, default 1 px) lets the grid breathe. The
  renderer optionally rounds cell corners (`corner-radius` attribute).
  Accessibility: each cell carries `aria-label` with row, column, and value.

---

### Pair plot  *(scatterplot matrix, SPLOM)*

- **Renderer / `type`:** `splom` — **Primary renderer**
- **Controller:** `<mj-chart type="splom" ...>`
- **Purpose:** Display all pairwise scatter plots for a set of numeric
  variables in a grid layout, enabling rapid inspection of multi-dimensional
  relationships.
- **Decomposition:** `mj-chart-plot` (the full grid surface), `mj-chart-title`,
  `mj-chart-tooltip`, `mj-chart-data-table`, `mj-chart-legend`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Iris Dataset Pair Plot" },
    "variables": ["sepal_length", "sepal_width", "petal_length", "petal_width"],
    "series": [
      {
        "name": "Setosa",
        "points": [
          { "sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2 },
          { "sepal_length": 4.9, "sepal_width": 3.0, "petal_length": 1.4, "petal_width": 0.2 }
        ]
      }
    ]
  }
  ```
  `variables` is the ordered list of numeric field names. Each point is a
  record with a value for every variable. The renderer derives all
  variable-pair combinations from this single flat data shape.
- **SVG primitives:** `<circle>` (scatter points in each cell), `<rect>`
  (diagonal cell background), `<text>` (variable name labels on diagonal
  or axes), `<line>` (axis ticks), `<g>` (one per cell)
- **Orientation:** `n/a` — the matrix layout is symmetric and fixed.
- **Variants / modes:** Diagonal cells can show a histogram or KDE of
  each variable alone (`diagonal="histogram|density|label"`, default
  `label`). Upper triangle can be suppressed or replaced with correlation
  values (`triangle="lower|full"`).
- **Phase:** P4
- **Notes:** The SPLOM renderer manages an N×N grid of sub-plots, each
  sharing synchronized `linear` scales per variable (one x-scale per
  column, one y-scale per row). All sub-plots are rendered into a single
  `<svg>` in `mj-chart-plot`; each sub-plot is a `<g>` with a `clipPath`
  to its cell bounds. Brushing on one cell projects the selected points
  across all cells (requires `mj-chart-brush`). Axes are drawn only on the
  outer edge cells to avoid repetition. Color and shape vary by series so
  groups are distinguishable without color alone.

---

### Residual plot  *(residuals vs fitted, diagnostic plot)*

- **Renderer / `type`:** `scatter` — **Variant of `scatter`**
- **Controller:** `<mj-chart type="scatter" residual="true" ...>`
- **Purpose:** Diagnose regression model fit by plotting residuals
  (observed minus predicted) against fitted values or a predictor, exposing
  heteroscedasticity, non-linearity, and outliers.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (x, value "Fitted";
  y, value "Residual"), `mj-chart-grid`, `mj-chart-title`, `mj-chart-tooltip`,
  `mj-chart-annotation` (zero reference line), `mj-chart-data-table`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Residuals vs Fitted" },
    "series": [
      {
        "name": "Model A",
        "points": [
          { "x": 12.4, "y": 0.34, "label": "obs_1" },
          { "x": 15.7, "y": -1.02, "label": "obs_2" },
          { "x": 18.1, "y": 0.11 }
        ]
      }
    ],
    "residual": {
      "zero-line": true
    }
  }
  ```
  `x` is the fitted value (or predictor); `y` is the residual. The
  `residual.zero-line` flag instructs the renderer to draw a horizontal
  reference line at y = 0 via `mj-chart-annotation`.
- **SVG primitives:** `<circle>` (one per observation), `<line>` (zero
  reference line), `<text>` (optional point labels), `<g>`
- **Orientation:** `n/a` — x is fitted values, y is residuals; swapping
  changes meaning.
- **Variants / modes:** Residuals vs predictor (same shape; x changes
  semantic only). Scale-location plot (y = √|residual|; computed by the
  renderer when `residual.transform="scale-location"`).
- **Phase:** P3
- **Notes:** This is a semantically specialized scatter plot. The
  `residual="true"` flag triggers automatic zero-line injection via
  `mj-chart-annotation` and sets default axis labels to "Fitted values"
  and "Residuals". No new renderer file is needed; the scatter renderer
  handles it via the `residual` config block in the JSON.
