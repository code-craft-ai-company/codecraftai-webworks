# Distribution Charts

> Catalog of chart types in this category for the codecraftai-webworks SVG chart
> library. Architecture, the coordinated-element model, the part components,
> the JSON contract, and phasing are defined in `../../chart-components-plan.md`
> and are not repeated here.

Distribution charts show how values spread across a range — their shape,
density, summary statistics, and outliers. Most renderers derive their geometry
from raw `samples: [n …]` arrays; callers may also supply pre-binned
`bins: [{ "x0", "x1", "count" }]` to skip client-side computation.

---

### Histogram  *(frequency histogram, bin chart)*
- **Renderer / `type`:** `histogram` — **Primary renderer**
- **Controller:** `<mj-chart type="histogram" ...>`
- **Purpose:** Show the frequency distribution of a continuous variable by grouping values into equal-width (or custom-width) bins.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (value — count/frequency, category — bin ranges), `mj-chart-grid`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`, `mj-chart-annotation`, `mj-chart-value-labels`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Score Distribution", "orientation": "vertical" },
    "series": [
      {
        "name": "Scores",
        "samples": [74, 88, 91, 63, 77, 85, 90, 72],
        "color": "optional"
      }
    ]
  }
  ```
  Pre-binned alternative (renderer uses bins directly without computing them):
  ```json
  {
    "meta": { "title": "Score Distribution", "orientation": "vertical" },
    "series": [
      {
        "name": "Scores",
        "bins": [
          { "x0": 60, "x1": 70, "count": 3 },
          { "x0": 70, "x1": 80, "count": 8 },
          { "x0": 80, "x1": 90, "count": 12 },
          { "x0": 90, "x1": 100, "count": 5 }
        ]
      }
    ]
  }
  ```
- **SVG primitives:** `<rect>` (one per bin), `<text>` (value labels), `<g>` (per-series group)
- **Orientation:** `vertical` (bars rise from the bottom — default) and `horizontal` (bars extend rightward); orientation swaps which axis carries counts vs bin ranges.
- **Variants / modes:**
  - `group="overlay"` — overlapping semi-transparent histograms for multi-series comparison.
  - `group="stack"` — stacked bins for multi-series histograms.
  - `normalize="density"` — y-axis shows probability density instead of count (area sums to 1); used by the density plot variant.
  - `bin-count` / `bin-width` attributes control automatic bin generation from `samples`.
- **Phase:** P2
- **Notes:** When `samples` is provided the renderer computes bins using a configurable algorithm (Sturges, Scott, or Freedman–Diaconis, defaulting to Sturges). When `bins` is provided, bin edges are taken as-is. Scales used: `linear` for the value (count/density) axis; `linear` or `band` for the bin-range axis. The data-table model lists each bin as a row with columns `[range, count]`.

---

### Density Plot  *(kernel density estimate, KDE plot, smooth histogram)*
- **Renderer / `type`:** `histogram` — **Variant of `histogram`**
- **Controller:** `<mj-chart type="histogram" normalize="density" smooth="kde" ...>`
- **Purpose:** Show the smoothed continuous probability density of a variable, emphasising shape over bin count.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (value — density, category — continuous range), `mj-chart-grid`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`
- **JSON shape:** Same as Histogram — `samples: [n …]` array per series. The renderer derives KDE internally from raw samples; pre-binned `bins` input is also accepted and converted to a smooth curve estimate.
  ```json
  {
    "meta": { "title": "Response Time Density" },
    "series": [
      { "name": "API v1", "samples": [120, 135, 142, 98, 160, 115] },
      { "name": "API v2", "samples": [95, 101, 108, 97, 112, 99] }
    ]
  }
  ```
- **SVG primitives:** `<path>` (filled area curve per series using a smooth cubic-bezier or monotone spline from `svgdraw.js`), `<text>` (axis labels), `<g>` (per-series group)
- **Orientation:** `vertical` (density on y, range on x) and `horizontal` (density on x, range on y).
- **Variants / modes:** `fill="area"` adds a translucent fill under each density curve; `fill="none"` renders line only.
- **Phase:** P2
- **Notes:** Rendered by the `histogram` renderer with `normalize="density"` and `smooth="kde"`. The KDE bandwidth is auto-selected via Silverman's rule-of-thumb but overridable with a `bandwidth` attribute. The renderer evaluates density at evenly-spaced points across the data range and emits a `<path>` using the curve builder in `svgdraw.js`. Scales: `linear` for both axes.

---

### Box Plot  *(box-and-whisker plot)*
- **Renderer / `type`:** `boxplot` — **Primary renderer**
- **Controller:** `<mj-chart type="boxplot" ...>`
- **Purpose:** Summarise a distribution's median, interquartile range, and outliers as a compact five-number summary, enabling quick comparison across groups.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (value — continuous, category — group labels), `mj-chart-grid`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`, `mj-chart-annotation`
- **JSON shape:**
  Raw samples (renderer computes the five-number summary):
  ```json
  {
    "meta": { "title": "Salary by Department" },
    "categories": ["Engineering", "Design", "Marketing"],
    "series": [
      {
        "name": "2025",
        "groups": [
          { "category": "Engineering", "samples": [95, 102, 110, 88, 130, 97] },
          { "category": "Design",      "samples": [72, 78, 85, 70, 91, 80] },
          { "category": "Marketing",   "samples": [65, 70, 74, 63, 82, 68] }
        ]
      }
    ]
  }
  ```
  Pre-computed summary (renderer skips derivation):
  ```json
  {
    "meta": { "title": "Salary by Department" },
    "categories": ["Engineering", "Design", "Marketing"],
    "series": [
      {
        "name": "2025",
        "groups": [
          {
            "category": "Engineering",
            "min": 88, "q1": 95, "median": 102, "q3": 112, "max": 130,
            "outliers": [145, 150]
          }
        ]
      }
    ]
  }
  ```
- **SVG primitives:** `<rect>` (IQR box), `<line>` (whiskers, median line), `<circle>` (outlier points), `<g>` (per-group)
- **Orientation:** `vertical` (value on y, groups on x) and `horizontal` (value on x, groups on y).
- **Variants / modes:**
  - `notched="true"` — notched box to indicate confidence interval around the median.
  - Combined with `violin` renderer via `overlay="violin"` to add a violin silhouette behind each box.
- **Phase:** P2
- **Notes:** Outliers are defined as points beyond 1.5 × IQR from Q1/Q3 by default; the multiplier is configurable. Scales: `band` for the category axis; `linear` for the value axis. The data-table model exposes min, Q1, median, Q3, max, and outlier count per group.

---

### Violin Plot  *(bean plot)*
- **Renderer / `type`:** `violin` — **Primary renderer**
- **Controller:** `<mj-chart type="violin" ...>`
- **Purpose:** Show the full distribution shape and density for each group using a mirrored KDE silhouette, revealing multimodality that a box plot hides.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (value — continuous, category — group labels), `mj-chart-grid`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`
- **JSON shape:** Same `samples` per group structure as Box Plot:
  ```json
  {
    "meta": { "title": "Response Times by Region" },
    "categories": ["US", "EU", "APAC"],
    "series": [
      {
        "name": "Q4",
        "groups": [
          { "category": "US",   "samples": [120, 135, 142, 98, 160, 115, 190] },
          { "category": "EU",   "samples": [95, 101, 108, 97, 112, 99, 105] },
          { "category": "APAC", "samples": [200, 215, 188, 230, 205, 195] }
        ]
      }
    ]
  }
  ```
- **SVG primitives:** `<path>` (mirrored KDE silhouette per group — two symmetrical curves joined at endpoints), `<line>` (optional embedded median marker), `<rect>` (optional embedded IQR box when `show-box="true"`), `<g>` (per-group)
- **Orientation:** `vertical` (value on y, groups on x) and `horizontal` (value on x, groups on y).
- **Variants / modes:**
  - `show-box="true"` — renders a miniature box-plot inside each violin.
  - `show-points="true"` — overlays a strip plot of raw sample points.
  - `half="true"` — renders only the right half of each violin (half-violin / raincloud left side).
- **Phase:** P2
- **Notes:** KDE computed from `samples` using the same engine as the density plot renderer. Each violin is drawn as a symmetric `<path>` around the group's band center using `svgdraw.js` curve helpers. Scales: `band` (category), `linear` (value).

---

### Strip Plot  *(jitter plot, univariate scatter)*
- **Renderer / `type`:** `strip` — **Primary renderer**
- **Controller:** `<mj-chart type="strip" ...>`
- **Purpose:** Display every individual data point along a categorical axis to expose the raw distribution without binning or smoothing.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (value — continuous, category — group labels), `mj-chart-grid`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Test Scores by Class" },
    "categories": ["Class A", "Class B", "Class C"],
    "series": [
      {
        "name": "Exam 1",
        "groups": [
          { "category": "Class A", "samples": [74, 88, 91, 63, 77, 85] },
          { "category": "Class B", "samples": [80, 82, 79, 90, 85, 76] },
          { "category": "Class C", "samples": [65, 70, 72, 68, 75, 71] }
        ]
      }
    ]
  }
  ```
- **SVG primitives:** `<circle>` (one per data point), `<g>` (per-group, per-series)
- **Orientation:** `vertical` (value on y, groups on x) and `horizontal` (value on x, groups on y).
- **Variants / modes:**
  - `jitter="random"` (default) — points offset randomly along the category axis to reduce overplotting.
  - `jitter="none"` — all points aligned on the category center (pure strip).
  - Overlaid on `boxplot` or `violin` via respective renderers' `overlay="strip"` attribute.
- **Phase:** P2
- **Notes:** The random jitter seed is deterministic (derived from value) so the chart is stable across re-renders. Point opacity is reduced for dense data. Scales: `band` (category), `linear` (value). The data-table model lists individual observations.

---

### Swarm Plot  *(beeswarm plot)*
- **Renderer / `type`:** `strip` — **Variant of `strip`**
- **Controller:** `<mj-chart type="strip" jitter="swarm" ...>`
- **Purpose:** Display individual data points along a categorical axis without overlap, using a force-directed beeswarm layout so every point is visible.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (value — continuous, category — group labels), `mj-chart-grid`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`
- **JSON shape:** Identical to Strip Plot — `groups[].samples` array per series/category.
- **SVG primitives:** `<circle>` (one per data point, placed by swarm algorithm), `<g>` (per-group)
- **Orientation:** `vertical` and `horizontal`; the swarm expands perpendicular to the value axis.
- **Variants / modes:** None beyond those of the `strip` renderer; `jitter="swarm"` activates the non-overlapping placement pass.
- **Phase:** P2
- **Notes:** The swarm layout runs a greedy bin-packing pass: points are sorted by value, then placed at the first position along the category band that does not overlap any already-placed point (within one point radius). This is a single-pass O(n log n) approximation, not a full force simulation. Scales: `band` (category), `linear` (value).

---

### Rug Plot  *(tick-mark marginal plot)*
- **Renderer / `type`:** `rug` — **Primary renderer**
- **Controller:** `<mj-chart type="rug" ...>`
- **Purpose:** Display the marginal distribution of a variable as a row of tick marks along an axis — typically combined with a scatter or density plot to annotate where observations fall.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (value — continuous), `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Observation Rug" },
    "series": [
      { "name": "Variable A", "samples": [12, 18, 22, 35, 41, 47, 60] },
      { "name": "Variable B", "samples": [15, 20, 28, 33, 44, 52] }
    ]
  }
  ```
- **SVG primitives:** `<line>` (one short vertical or horizontal tick per observation), `<g>` (per-series)
- **Orientation:** `horizontal` (ticks run vertically along a horizontal value axis) and `vertical` (ticks run horizontally along a vertical value axis). The rug is rendered as a thin strip; `height` / `width` of the `mj-chart-plot` element controls the strip thickness.
- **Variants / modes:** No standalone variants; the rug renderer is most often composed as an `overlay` on a scatter or density chart using `<mj-chart-annotation>` or a secondary `mj-chart-plot` sharing the same controller.
- **Phase:** P2
- **Notes:** Tick opacity is reduced for overlapping observations. The renderer intentionally has no value axis — ticks are purely positional along a shared scale owned by the parent controller. Scales: `linear` for the value axis (shared with host chart when used as overlay).

---

### Dot Histogram  *(Wilkinson dot plot, dot plot histogram, isotype histogram)*
- **Renderer / `type`:** `dothistogram` — **Primary renderer**
- **Controller:** `<mj-chart type="dothistogram" ...>`
- **Purpose:** Show count distributions using stacked dots instead of bars, making individual counts readable and preserving a data-density feel.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (value — count, category — bin ranges), `mj-chart-grid`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`
- **JSON shape:** Identical envelope to Histogram — `samples: [n …]` or `bins: [{ x0, x1, count }]` per series:
  ```json
  {
    "meta": { "title": "Coin Flip Runs" },
    "series": [
      {
        "name": "Heads",
        "bins": [
          { "x0": 0, "x1": 2, "count": 4 },
          { "x0": 2, "x1": 4, "count": 9 },
          { "x0": 4, "x1": 6, "count": 6 },
          { "x0": 6, "x1": 8, "count": 2 }
        ]
      }
    ]
  }
  ```
- **SVG primitives:** `<circle>` (one per unit count, stacked within each bin), `<g>` (per-bin)
- **Orientation:** `vertical` (dots stack upward — default) and `horizontal` (dots stack rightward).
- **Variants / modes:** `dot-size` attribute controls circle radius relative to bin width. Multiple series stack dots side-by-side within each bin (grouped mode) or atop one another with different colors (overlay mode, `group="overlay"`).
- **Phase:** P2
- **Notes:** Dot radius is auto-sized so dots fill the bin width without overlap; the renderer computes `radius = binWidth / 2` and stacks `count` circles per bin. Scales: `band` or `linear` for bin axis; `linear` for count axis. For large counts, the renderer auto-switches to a bar representation with an info annotation rather than rendering thousands of dots.

---

### Ridgeline Plot  *(joy plot, ridge plot)*
- **Renderer / `type`:** `ridgeline` — **Primary renderer**
- **Controller:** `<mj-chart type="ridgeline" ...>`
- **Purpose:** Compare distribution shapes across many groups by displaying partially overlapping density curves (or histograms) in offset rows — effective for showing change across time periods or categories.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (value — continuous, category — group labels on an offset y scale), `mj-chart-title`, `mj-chart-legend`, `mj-chart-tooltip`, `mj-chart-data-table`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Temperature Distribution by Month" },
    "categories": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
    "series": [
      {
        "name": "Temperature °C",
        "groups": [
          { "category": "Jan", "samples": [-5, -2, 0, 3, 1, -3] },
          { "category": "Feb", "samples": [-3, 0, 2, 4, 1, -1] },
          { "category": "Mar", "samples": [2, 5, 8, 10, 6, 4] },
          { "category": "Apr", "samples": [8, 12, 15, 14, 11, 9] },
          { "category": "May", "samples": [14, 17, 20, 19, 16, 15] },
          { "category": "Jun", "samples": [19, 22, 25, 24, 21, 20] }
        ]
      }
    ]
  }
  ```
- **SVG primitives:** `<path>` (filled KDE area curve per group, vertically offset), `<text>` (group labels on the left), `<line>` (optional baseline per row), `<g>` (per-group)
- **Orientation:** `vertical` only — groups are stacked along the y-axis with each row's density distributed horizontally along the shared value scale. Horizontal orientation is `n/a` for this layout.
- **Variants / modes:**
  - `mode="density"` (default) — KDE curves.
  - `mode="histogram"` — binned bars per row instead of smooth curves.
  - `overlap` attribute controls the fractional row-height overlap between adjacent groups (default `0.5`).
- **Phase:** P2
- **Notes:** Each group's KDE is computed independently at the same set of x evaluation points so all curves share one common value scale. Row offsets are computed from a `band` scale over the category axis; the KDE amplitude is scaled to fit within one row height (×`1 + overlap`). Fill opacity is set so overlapping rows remain legible. Scales: `linear` (value), `band` (group/category offset).

---

### Q-Q Plot  *(quantile–quantile plot)*
- **Renderer / `type`:** `qqplot` — **Primary renderer**
- **Controller:** `<mj-chart type="qqplot" ...>`
- **Purpose:** Assess how closely an observed distribution matches a theoretical distribution (or another empirical distribution) by plotting quantiles against each other; deviations from the diagonal reveal skew, heavy tails, or other departures.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (x — theoretical quantiles, y — observed quantiles), `mj-chart-grid`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-annotation` (45° reference line), `mj-chart-data-table`
- **JSON shape:**
  Single-sample against a theoretical distribution:
  ```json
  {
    "meta": { "title": "Normal Q-Q: Residuals" },
    "series": [
      {
        "name": "Residuals",
        "samples": [0.1, -0.3, 0.5, 1.2, -0.8, 0.0, 0.4, -0.2],
        "theoretical": "normal"
      }
    ]
  }
  ```
  Two empirical samples compared:
  ```json
  {
    "meta": { "title": "Q-Q: API v1 vs API v2" },
    "series": [
      { "name": "v1", "samples": [120, 135, 142, 98, 160] },
      { "name": "v2", "samples": [95, 101, 108, 97, 112] }
    ]
  }
  ```
- **SVG primitives:** `<circle>` (one per quantile pair), `<line>` (45° reference line, rendered via `mj-chart-annotation`), `<g>` (per-series)
- **Orientation:** `n/a` — x always carries theoretical/reference quantiles; y always carries observed quantiles.
- **Variants / modes:** `theoretical` field accepts `"normal"`, `"uniform"`, `"exponential"`, or `"lognormal"` for single-sample mode; omitting it and providing two series activates empirical-vs-empirical mode.
- **Phase:** P3
- **Notes:** The renderer sorts `samples`, computes empirical quantiles at equally-spaced probability points, then maps them against the theoretical inverse CDF (percent-point function). For two-sample mode the shorter sample's quantiles are interpolated to align with the longer. Scales: `linear` on both axes with symmetric domain expansion to show the diagonal clearly. The 45° reference line is injected as an `mj-chart-annotation` reference-line record.

---

### Cumulative Distribution Chart  *(CDF chart, ECDF plot, percentile chart, ogive)*
- **Renderer / `type`:** `cdf` — **Primary renderer**
- **Controller:** `<mj-chart type="cdf" ...>`
- **Purpose:** Show what fraction of observations fall at or below (or above) each value — useful for reading off percentiles and comparing distributions by their cumulative shape.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (value — continuous, cumulative — 0–1 or 0–100%), `mj-chart-grid`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`, `mj-chart-annotation`
- **JSON shape:**
  Raw samples (renderer computes the empirical CDF):
  ```json
  {
    "meta": { "title": "Response Time CDF" },
    "series": [
      { "name": "API v1", "samples": [120, 135, 142, 98, 160, 115] },
      { "name": "API v2", "samples": [95, 101, 108, 97, 112, 99] }
    ]
  }
  ```
  Pre-computed (renderer uses provided cumulative values directly):
  ```json
  {
    "meta": { "title": "Response Time CDF" },
    "series": [
      {
        "name": "API v1",
        "points": [
          { "x": 98,  "y": 0.10 },
          { "x": 115, "y": 0.30 },
          { "x": 120, "y": 0.50 },
          { "x": 135, "y": 0.70 },
          { "x": 142, "y": 0.90 },
          { "x": 160, "y": 1.00 }
        ]
      }
    ]
  }
  ```
- **SVG primitives:** `<path>` (step-function line per series for ECDF; smooth curve for theoretical CDF), `<circle>` (optional step markers), `<line>` (optional reference percentile annotations), `<g>` (per-series)
- **Orientation:** `vertical` (value on x, cumulative probability on y — default) and `horizontal` (cumulative probability on x, value on y — "percentile" orientation).
- **Variants / modes:**
  - `direction="ascending"` (default) — fraction at or below.
  - `direction="descending"` — fraction above (survival function / complementary CDF).
  - `scale="percent"` — y-axis shown as 0–100% instead of 0–1.
  - `smooth="true"` — connects points with a monotone spline instead of a step function (appropriate for pre-computed theoretical CDFs).
- **Phase:** P2
- **Notes:** The ECDF is computed by sorting `samples` and assigning rank/(n) as cumulative probability. Scales: `linear` for both axes. Reference annotation lines (e.g., p50, p95, p99) can be added via `mj-chart-annotation`.

---

### Frequency Polygon  *(frequency curve)*
- **Renderer / `type`:** `histogram` — **Variant of `histogram`**
- **Controller:** `<mj-chart type="histogram" display="polygon" ...>`
- **Purpose:** Show distribution trends across bins as a connected line through bin midpoints rather than as bars — makes multi-series comparisons easier to read when bars would overlap.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (value — count/frequency, category — bin ranges), `mj-chart-grid`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`
- **JSON shape:** Identical to Histogram — `samples: [n …]` or `bins: [{ x0, x1, count }]` per series. Bins are computed the same way; only the rendering pass changes.
  ```json
  {
    "meta": { "title": "Score Frequency Polygon" },
    "series": [
      { "name": "Class A", "samples": [74, 88, 91, 63, 77, 85, 90, 72] },
      { "name": "Class B", "samples": [80, 82, 79, 90, 85, 76, 88, 84] }
    ]
  }
  ```
- **SVG primitives:** `<path>` (polyline through bin-midpoint coordinates — straight segments, not a smooth curve), `<circle>` (optional midpoint markers), `<g>` (per-series)
- **Orientation:** `vertical` (count on y, bin midpoints on x) and `horizontal` (count on x, bin midpoints on y).
- **Variants / modes:** `fill="area"` adds a translucent filled area beneath each polygon line. When `fill="area"` and multiple series are present, `group="stack"` stacks the polygons.
- **Phase:** P2
- **Notes:** Rendered by the `histogram` renderer's `display="polygon"` mode: bins are computed identically, but instead of `<rect>` elements the renderer emits a `<path>` connecting the midpoint of each bin at the appropriate count height, with anchor points at `(x0_first, 0)` and `(x1_last, 0)` to close the polygon. Scales: `linear` (count/frequency axis), `linear` (bin-midpoint axis).
