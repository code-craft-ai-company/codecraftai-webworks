# Statistical & Analytical Charts

> Catalog of chart types in this category for the codecraftai-webworks SVG chart
> library. Architecture, the coordinated-element model, the part components,
> the JSON contract, and phasing are defined in `../../chart-components-plan.md`
> and are not repeated here.

Charts in this category visualize statistical summaries, model diagnostics,
clinical measurements, and process quality data. Several entries (box plot,
violin plot, funnel plot) also appear in adjacent categories; those entries
cross-reference rather than redefine. Line-curve charts (ROC, precision-recall,
lift, calibration) share the `curve` renderer — the type key selects the
default axis labelling and tooltip behaviour, not a different drawing path.

---

### Box plot  *(box-and-whisker plot)*

- **Renderer / `type`:** `boxplot` — **Primary renderer**
- **Controller:** `<mj-chart type="boxplot" ...>`
- **Purpose:** Display five-number summary statistics (min, Q1, median, Q3,
  max) with optional outliers for one or more groups; best for comparing
  distributions across categories at a glance.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (category + value),
  `mj-chart-grid`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`,
  `mj-chart-data-table`, `mj-chart-annotation`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Scores by Group", "orientation": "vertical" },
    "series": [
      {
        "name": "Group A",
        "color": "optional",
        "groups": [
          {
            "category": "Control",
            "q1": 42, "median": 55, "q3": 68,
            "min": 28, "max": 81,
            "outliers": [12, 95]
          }
        ]
      }
    ]
  }
  ```
  The per-group statistical shape `{ q1, median, q3, min, max, outliers }`
  is the canonical statistical family shape from plan §3.4. Pre-computed
  values are accepted directly; the renderer does not compute quartiles
  from raw samples (use the `histogram` renderer pipeline for that).
- **SVG primitives:** `<rect>` (IQR box), `<line>` (whiskers, median line),
  `<circle>` (outlier points), `<g>` (per-group container), `<text>` (axis
  labels, value labels when enabled)
- **Orientation:** `horizontal` | `vertical` — swaps category and value axes;
  vertical draws boxes top-to-bottom, horizontal draws boxes left-to-right.
- **Variants / modes:** Notched box plot — `notch="true"` attribute cuts a
  notch at the median for visual confidence-interval indication, rendered as a
  narrowed `<rect>` or `<path>` polygon. Grouped boxes — multiple series share
  a category axis position with a band-scale sub-group offset.
- **Phase:** P2
- **Notes:** Also cross-listed in the Distribution category (03-distribution.md).
  Scales: `band` for category axis, `linear` for value axis. Whisker extent is
  configurable (`whisker="tukey|minmax"`; default `tukey` = 1.5×IQR). Outliers
  rendered as `<circle>` only when `outliers` array is non-empty. Accessibility:
  data-table exposes all five statistics plus outlier count per group.

---

### Violin plot

- **Renderer / `type`:** `violin` — **Primary renderer**
- **Controller:** `<mj-chart type="violin" ...>`
- **Purpose:** Show the full distribution shape (kernel-density estimate) of
  one or more groups; richer than a box plot when the distribution is
  multi-modal or skewed.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (category + value),
  `mj-chart-grid`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`,
  `mj-chart-data-table`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Distribution by Cohort" },
    "series": [
      {
        "name": "Cohort A",
        "groups": [
          {
            "category": "Baseline",
            "q1": 40, "median": 54, "q3": 66,
            "min": 20, "max": 85,
            "outliers": [],
            "density": [
              { "value": 20, "density": 0.002 },
              { "value": 35, "density": 0.018 }
            ]
          }
        ]
      }
    ]
  }
  ```
  The `density` array holds pre-computed KDE points `{ value, density }`. If
  omitted, the renderer falls back to a box-plot silhouette using the five-
  number summary. Pre-computation is the caller's responsibility; the renderer
  does not perform KDE internally.
- **SVG primitives:** `<path>` (mirrored density curve filled as a closed
  area), `<line>` (median mark, whiskers if overlay enabled), `<rect>`
  (optional IQR box overlay), `<g>`, `<text>`
- **Orientation:** `horizontal` | `vertical`
- **Variants / modes:** Box-inside violin — `box-overlay="true"` superimposes
  the IQR box (reuses `boxplot` renderer primitives). Half-violin — `half="true"`
  draws only one side of the mirrored path, useful for paired comparisons.
- **Phase:** P2
- **Notes:** Also cross-listed in the Distribution category (03-distribution.md).
  The mirrored path is built by reflecting the density array across the group
  centre line using `svgdraw.js` path builder. Scales: `band` + `linear`
  (category + value) plus a local `linear` width scale mapping peak density to
  half the band width. Accessibility: data-table exposes the five-number
  summary; raw density points are not tabulated.

---

### Error bar chart  *(error bars)*

- **Renderer / `type`:** `errorbar` — **Primary renderer**
- **Controller:** `<mj-chart type="errorbar" ...>`
- **Purpose:** Overlay symmetric or asymmetric error bars (standard deviation,
  standard error, or confidence interval) on a point or bar chart; best for
  showing measurement uncertainty or variability alongside central values.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (category + value),
  `mj-chart-grid`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`,
  `mj-chart-data-table`, `mj-chart-annotation`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Mean ± SD by Condition" },
    "series": [
      {
        "name": "Treatment",
        "groups": [
          {
            "category": "Week 1",
            "value": 52.4,
            "error_low": 4.1,
            "error_high": 4.1
          }
        ]
      }
    ]
  }
  ```
  `error_low` and `error_high` are the extents below and above `value`
  respectively (both positive numbers). Symmetric errors may set both to the
  same value. An optional `bar` field (`"bar": true`) renders the central
  value as a `<rect>` instead of a `<circle>`.
- **SVG primitives:** `<line>` (whisker shaft), `<line>` (whisker caps — top
  and bottom horizontal strokes), `<circle>` (central point) or `<rect>`
  (central bar), `<g>`, `<text>`
- **Orientation:** `horizontal` | `vertical`
- **Variants / modes:** Grouped error bars — multiple series share a category
  axis using band-scale offsets. The `bar` mode is a variant that pairs error
  bars with a bar chart background.
- **Phase:** P3
- **Notes:** Cap width is configurable via `cap-width` attribute (px, default 8;
  `0` draws no caps; never wider than the series' sub-band). `null-value`
  (a number) draws a dashed reference line at that value and keeps it in the
  value domain; on `errorbar` this reference line is drawn only when
  `null-value` is given (without it, a plain solid zero line is drawn when 0
  lies inside the domain). Scales: `band` + `linear`. Accessibility: tooltip and data-table expose value, lower bound
  (`value − error_low`), and upper bound (`value + error_high`).

---

### Confidence interval plot  *(CI plot, estimate range plot)*

- **Renderer / `type`:** `confidence-interval` — **Variant of `errorbar`**
- **Controller:** `<mj-chart type="confidence-interval" ...>`
- **Purpose:** Visualise point estimates with explicit lower and upper
  confidence-interval bounds across multiple parameters or time points; best
  for presenting regression coefficients, survey estimates, or model outputs.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (category + value),
  `mj-chart-grid`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`,
  `mj-chart-data-table`, `mj-chart-annotation`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Parameter Estimates (95% CI)" },
    "series": [
      {
        "name": "Model 1",
        "groups": [
          {
            "category": "Age coefficient",
            "value": 0.34,
            "error_low": 0.12,
            "error_high": 0.18
          }
        ]
      }
    ]
  }
  ```
  Same statistical family shape as `errorbar`; `error_low` / `error_high` are
  half-widths from the point estimate to each CI bound. A `bar` field is
  ignored (intervals only).
- **SVG primitives:** `<line>` (interval span), `<circle>` (point estimate),
  `<line>` (end caps, `cap-width`), `<line>` (dashed reference line at
  `null-value`), `<g>`, `<text>`
- **Orientation:** `horizontal` (registered default — value on x-axis,
  parameters on y-axis, conventional for CI plots) | `vertical`.
- **Variants / modes:** None beyond the `errorbar` parent. `null-value`
  (number, default 0) places the reference line — e.g. `null-value="1"` for
  ratios; `cap-width` as on `errorbar`.
- **Phase:** P3
- **Notes:** There is no `ci.js`: `errorbar.js` registers
  `confidence-interval` beside `errorbar`, with `orientation="horizontal"` as
  its default. It draws intervals only — a dot at each point estimate with its
  whisker, never a bar — and a dashed reference line at `null-value`
  (default 0) that is always drawn and always kept in the value domain. The
  renderer draws the line itself; no `<mj-chart-annotation>` is needed.

---

### Control chart  *(Shewhart control chart, SPC chart)*

- **Renderer / `type`:** `control-chart` — **Primary renderer** (`control.js`, shared with `run-chart`)
- **Controller:** `<mj-chart type="control-chart" ...>`
- **Purpose:** Monitor a process variable over time against statistical control
  limits (UCL / LCL / centre line); best for detecting out-of-control signals
  in manufacturing, operations, or quality contexts.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (time/sequence + value),
  `mj-chart-grid`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`,
  `mj-chart-data-table`, `mj-chart-annotation`, `mj-chart-crosshair`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "X-bar Chart — Fill Weight" },
    "series": [
      {
        "name": "Sample mean",
        "points": [
          { "x": "2025-01-01", "y": 502.1 }
        ]
      }
    ],
    "control_limits": {
      "ucl": 512.4,
      "lcl": 491.8,
      "cl": 502.1
    }
  }
  ```
  `control_limits` carries the pre-computed upper control limit (`ucl`), lower
  control limit (`lcl`), and centre line (`cl`), plus an optional `label`. It
  may also be an array of such sets (sigma zones); a set's `label` is appended
  to its UCL / LCL / CL line labels. Each of `ucl`, `lcl`, `cl` is drawn only
  when it is a number. Without `control_limits` the limits are computed (see
  `limits="auto"`). `x` is a number (sequence, timestamp), a date
  (`YYYY-MM-DD` is a local day; ISO date-times) or a category label — the
  axis follows; a null or non-numeric `y` is a gap. Optional
  `reference_lines: [{ label, value }]` adds dashed horizontal lines.
- **SVG primitives:** `<path>` (data series line), `<circle>` (sample points),
  `<polygon>` (red diamond for an out-of-control point), `<line>` (UCL / LCL
  dashed, CL solid; reference lines), `<rect>` (band fill between a set's UCL
  and LCL when both are given), `<g>`, `<text>` (limit labels right of the plot)
- **Orientation:** `vertical` only (time on x-axis, value on y-axis); the
  horizontal mode is not meaningful for time-ordered process data.
- **Variants / modes:** `limits="auto"` computes the limits from the first
  series instead of using `control_limits`: CL = mean, UCL / LCL = CL ± 2.66 ×
  average moving range (an individuals chart). A control chart whose data has
  no `control_limits` gets these computed limits too. X-bar, R-chart, S-chart,
  p-chart, c-chart — all use the same renderer with pre-computed
  `control_limits`; there is no sub-type option.
- **Phase:** P3
- **Notes:** A point is flagged out of control automatically when its `y`
  lies beyond the outermost limits (the highest UCL or the lowest LCL of all
  sets, computed or given), or when the data sets `"ooc": true` on it. Flagged
  points are drawn as red diamonds (`--mj-color-danger`), say "out of
  control" in their accessible name and table row, and add an "Out of control"
  legend entry. Other run rules (Western Electric, Nelson) are not evaluated:
  mark those points with `ooc: true`. Scales: `linear`, `time` or `point`
  (x, from the x values), `linear` (y).

---

### Run chart  *(run sequence plot)*

- **Renderer / `type`:** `run-chart` — **Variant of `control-chart`** (registered by `control.js`)
- **Controller:** `<mj-chart type="run-chart" ...>`
- **Purpose:** Plot individual process observations in time order to reveal
  trends, cycles, and shifts before formal control limits are established;
  simpler and more honest than a control chart when limits cannot yet be
  calculated.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (sequence + value),
  `mj-chart-grid`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`,
  `mj-chart-annotation`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Turnaround Time (consecutive orders)" },
    "series": [
      {
        "name": "TAT (hours)",
        "points": [
          { "x": 1, "y": 3.4 },
          { "x": 2, "y": 2.9 }
        ]
      }
    ],
    "reference_lines": [
      { "label": "Target", "value": 3.0 }
    ]
  }
  ```
  Uses the XY `points` shape from plan §3.4 (`x` and `y` read as on the
  Control chart). `reference_lines` is an optional array of `{ label, value }`
  horizontal lines drawn dashed by the renderer; the median needs no entry.
  `control_limits` is ignored.
- **SVG primitives:** `<path>` (connecting line), `<circle>` (individual
  observations; rings for shift points), `<line>` (median / reference lines),
  `<g>`, `<text>`
- **Orientation:** `vertical` only (sequence on x-axis).
- **Variants / modes:** None. The median is computed from the data (the
  first series' values) and drawn as a dashed line labelled "Median"; control
  limits (`control_limits`, `limits`) are ignored and no point is flagged out
  of control. A shift — 6 or more consecutive points on one side of the
  median (points on the median neither break nor extend a run) — is marked
  with rings (larger hollow circles), named in the point's accessible name and
  table row, and adds a legend entry.
- **Phase:** P3
- **Notes:** Not a `line` variant: `control.js` registers `run-chart` beside
  `control-chart` and draws it with the same code minus the limits. Scales:
  `linear`, `time` or `point` (x, from the x values), `linear` (y).

---

### Bland-Altman plot  *(limits of agreement plot, difference plot)*

- **Renderer / `type`:** `bland-altman` — **Primary renderer**
- **Controller:** `<mj-chart type="bland-altman" ...>`
- **Purpose:** Assess agreement between two measurement methods by plotting
  their difference against their mean; best for clinical measurement validation
  and method-comparison studies.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (value + value),
  `mj-chart-grid`, `mj-chart-title`, `mj-chart-tooltip`,
  `mj-chart-data-table`, `mj-chart-annotation`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Bland-Altman: Device A vs Device B" },
    "series": [
      {
        "name": "Subjects",
        "points": [
          { "x": 112.5, "y": 3.2, "label": "optional subject id" }
        ]
      }
    ],
    "limits": {
      "mean_diff": 1.1,
      "loa_upper": 8.4,
      "loa_lower": -6.2
    }
  }
  ```
  The data layer is expected to pre-compute `x = (method_A + method_B) / 2`
  and `y = method_A − method_B` for each subject. `limits` carries the
  mean difference and limits of agreement (LoA), also pre-computed. The
  renderer draws the scatter and overlays the three horizontal reference lines.
- **SVG primitives:** `<circle>` (subject points), `<line>` (mean difference
  and LoA reference lines), `<rect>` (optional shaded LoA band),
  `<g>`, `<text>` (axis labels, line annotations)
- **Orientation:** `n/a` — axes are always mean (x) vs difference (y).
- **Variants / modes:** Percentage Bland-Altman — `mode="percent"` changes
  the y-axis to `(A−B)/mean × 100`; the data layer recomputes `y` accordingly,
  the renderer is unchanged.
- **Phase:** P3
- **Notes:** The three annotation lines (mean, upper LoA, lower LoA) are
  injected into the model as horizontal `<mj-chart-annotation>` entries so
  they participate in axis scale computation. Scales: `linear` (x and y).
  Accessibility: data-table lists per-subject mean and difference values plus
  the limit values.

---

### ROC curve  *(receiver operating characteristic curve)*

- **Renderer / `type`:** `roc` — **Variant of `curve`**
- **Controller:** `<mj-chart type="roc" ...>`
- **Purpose:** Evaluate binary classifier performance across all decision
  thresholds by plotting true-positive rate against false-positive rate; best
  for model selection and threshold optimisation.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (FPR + TPR),
  `mj-chart-grid`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`,
  `mj-chart-data-table`, `mj-chart-annotation`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "ROC Curve — Sepsis Model" },
    "series": [
      {
        "name": "Model v2",
        "points": [
          { "x": 0.00, "y": 0.00 },
          { "x": 0.05, "y": 0.48 },
          { "x": 1.00, "y": 1.00 }
        ]
      }
    ]
  }
  ```
  Uses the XY `points` shape from plan §3.4. `x` = FPR, `y` = TPR, as
  fractions (0–1) or percentages (0–100). Multiple series overlay multiple
  models. The renderer draws the dashed chance diagonal, and the legend
  appends each series' AUC (trapezoid area), e.g. "Model v2 (AUC 0.87)".
- **SVG primitives:** `<path>` (curve line per series), `<circle>` (optional
  threshold marker), `<path>` (optional AUC fill area), `<line>` (diagonal
  reference), `<g>`, `<text>`
- **Orientation:** `n/a` — axes are always FPR (x) vs TPR (y), both 0–1.
- **Variants / modes:** AUC shading — `shade-auc="true"` fills the area under
  the curve. Markers — `markers="true|false"`; by default markers are shown
  when a series has at most 50 points. Hidden markers stay as transparent
  marks that show on hover / focus, so every point remains focusable and
  clickable. Multiple series for multi-model comparison.
- **Phase:** P3
- **Notes:** The `roc` type key selects the shared `curve` renderer
  (`charts/core/renderers/curve.js`) with preset axis domain [0,1]×[0,1],
  axis labels "False Positive Rate" / "True Positive Rate", and a diagonal
  `<line>` drawn by the renderer. No separate renderer file.
  Scales: `linear` (x and y). The `curve` renderer is also used by
  `precision-recall`, `lift`, and `calibration`.

---

### Precision-recall curve  *(PR curve)*

- **Renderer / `type`:** `precision-recall` — **Variant of `curve`**
- **Controller:** `<mj-chart type="precision-recall" ...>`
- **Purpose:** Evaluate classifier performance when class imbalance makes ROC
  analysis misleading; plots precision against recall across thresholds.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (recall + precision),
  `mj-chart-grid`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`,
  `mj-chart-data-table`, `mj-chart-annotation`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Precision-Recall — Fraud Detector" },
    "series": [
      {
        "name": "Model v3",
        "points": [
          { "x": 0.00, "y": 1.00 },
          { "x": 0.55, "y": 0.81 },
          { "x": 1.00, "y": 0.34 }
        ]
      }
    ]
  }
  ```
  `x` = recall, `y` = precision. An optional top-level `baseline_prevalence`
  number draws the dashed no-skill line at that precision. The legend appends
  each series' AP (area under the curve), e.g. "Model v3 (AP 0.72)".
- **SVG primitives:** `<path>` (curve), `<circle>` (threshold markers),
  `<path>` (optional AP fill), `<line>` (baseline), `<g>`, `<text>`
- **Orientation:** `n/a`
- **Variants / modes:** Average precision (AP) shading — `shade-auc="true"`.
  `markers` as on the ROC curve.
- **Phase:** P3
- **Notes:** Shares the `curve` renderer with `roc`, `lift`, and `calibration`.
  Preset axis domain [0,1]×[0,1], axis labels "Recall" / "Precision". No
  separate renderer file.

---

### Lift chart  *(cumulative lift curve, gain chart)*

- **Renderer / `type`:** `lift` — **Variant of `curve`**
- **Controller:** `<mj-chart type="lift" ...>`
- **Purpose:** Show how much better a model targets positive cases compared to
  random selection, expressed as a ratio against population percentage contacted;
  best for direct-marketing and campaign-optimisation decisions.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (% population + lift
  or % captured), `mj-chart-grid`, `mj-chart-legend`, `mj-chart-title`,
  `mj-chart-tooltip`, `mj-chart-data-table`, `mj-chart-annotation`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Cumulative Lift — Campaign Model" },
    "series": [
      {
        "name": "Model A",
        "points": [
          { "x": 0.10, "y": 3.2 },
          { "x": 0.50, "y": 1.8 },
          { "x": 1.00, "y": 1.0 }
        ]
      }
    ]
  }
  ```
  `x` = proportion of population contacted (0–1, or 0–100 as percent),
  `y` = cumulative lift (ratio). The renderer draws a dashed baseline at
  `y = 1`.
- **SVG primitives:** `<path>` (lift curve per model), `<line>` (baseline
  y = 1), `<circle>` (optional key threshold markers), `<g>`, `<text>`
- **Orientation:** `n/a`
- **Variants / modes:** Gains chart — `mode="gains"` draws a cumulative-gains
  chart instead: the y-axis becomes "Positives captured" (fraction or percent,
  so the data supplies gains `y` values, not lift), and a dashed chance
  diagonal replaces the `y = 1` baseline. `markers` as on the ROC curve.
  `shade-auc` does not apply.
- **Phase:** P3
- **Notes:** Shares the `curve` renderer. Preset axis label "% Population
  Contacted" / "Lift". The baseline (`y = 1`) is drawn by the renderer. No
  separate renderer file.

---

### Calibration plot  *(reliability diagram, calibration curve)*

- **Renderer / `type`:** `calibration` — **Variant of `curve`**
- **Controller:** `<mj-chart type="calibration" ...>`
- **Purpose:** Compare a classifier's predicted probabilities against observed
  event rates (binned) to assess and communicate model calibration quality.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (predicted + observed),
  `mj-chart-grid`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`,
  `mj-chart-data-table`, `mj-chart-annotation`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Calibration — 30-day Readmission Model" },
    "series": [
      {
        "name": "Model (ECE = 0.04)",
        "points": [
          { "x": 0.10, "y": 0.09, "n": 412 },
          { "x": 0.30, "y": 0.27, "n": 308 },
          { "x": 0.70, "y": 0.74, "n": 118 }
        ]
      }
    ]
  }
  ```
  `x` = mean predicted probability for the bin, `y` = observed event rate,
  optional `n` = number of observations in the bin (drives point size).
  The diagonal perfect-calibration line is injected automatically.
- **SVG primitives:** `<path>` (calibration curve), `<circle>` (bin points,
  optionally sized by `n`), `<line>` (perfect calibration diagonal),
  `<rect>` (optional histogram bars for bin counts below the plot),
  `<g>`, `<text>`
- **Orientation:** `n/a` — axes are always predicted (x) vs observed (y).
- **Variants / modes:** Size-by-count — `size-by="n"` scales point radii by
  `n` via a `sqrt` scale (3–12 px). Histogram overlay — `show-histogram="true"`
  draws translucent bars of `n` along the bottom of the plot (at most 20 % of
  its height); points need `n`. `markers` as on the ROC curve. `shade-auc`
  does not apply.
- **Phase:** P3
- **Notes:** Shares the `curve` renderer. Preset axis domain [0,1]×[0,1],
  axis labels "Mean Predicted Probability" / "Fraction of Positives". No
  separate renderer file.

---

### Survival curve  *(survival function plot)*

- **Renderer / `type`:** `survival` — **Primary renderer**
- **Controller:** `<mj-chart type="survival" ...>`
- **Purpose:** Plot the estimated probability of surviving (or not experiencing
  an event) beyond each time point; umbrella entry for the step-function
  survival curve family.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (time + probability),
  `mj-chart-grid`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`,
  `mj-chart-data-table`, `mj-chart-annotation`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Overall Survival" },
    "series": [
      {
        "name": "Treatment arm",
        "points": [
          { "x": 0,   "y": 1.000, "censored": false },
          { "x": 6,   "y": 0.872, "censored": false },
          { "x": 9,   "y": 0.872, "censored": true  },
          { "x": 12,  "y": 0.741, "censored": false }
        ]
      }
    ]
  }
  ```
  Uses the XY `points` shape from plan §3.4. `y` is the survival probability
  (0–1); a series whose values go above 1 is read as percent (0–100), its
  `ci_lower` / `ci_upper` too. `x` is a number or a date (`YYYY-MM-DD` is a
  local day; ISO date-times) — when any `x` is not a number the x-axis is a
  time axis. `censored: true` marks a censored observation; the renderer draws
  a tick mark at that point rather than a step drop. Optional `ci_lower` /
  `ci_upper` (band, with `ci`) and `at_risk` (at-risk table, with `at-risk`).
- **SVG primitives:** `<path>` (step-function line built with horizontal-then-
  vertical segments), `<line>` tick (censored observation marks), `<circle>`
  (transparent focusable mark per event), `<path>` (optional confidence-band
  fill), `<g>`, `<text>`
- **Orientation:** `vertical` only (time on x-axis, survival probability on
  y-axis).
- **Variants / modes:** Confidence bands — `ci="true"` expects additional
  `ci_lower` / `ci_upper` fields on each point and draws a shaded band,
  stepped like the curve. Cumulative incidence — `mode="cumulative"` plots
  `1 − S(t)`: the data stays S(t) and the renderer converts it (the curve
  starts at 0, CI bounds are converted too, the y-axis reads "Cumulative
  incidence"). Numbers at risk — `at-risk="true"` draws a "Number at risk"
  table under the x-axis, one row per series, showing the latest `at_risk` at
  or before each x tick.
- **Phase:** P3
- **Notes:** The step-function path is built using the `svgdraw.js` step-line
  builder (same helper as the `step` line renderer). Scales: `linear` or `time`
  (x), `linear` (y, domain [0,1]). The `kaplan-meier` type key is a variant of
  this renderer (see below).

---

### Kaplan-Meier chart  *(KM curve, KM estimator plot)*

- **Renderer / `type`:** `kaplan-meier` — **Variant of `survival`**
- **Controller:** `<mj-chart type="kaplan-meier" ...>`
- **Purpose:** Display Kaplan-Meier survival estimates for one or more cohorts,
  with censored-observation ticks, optional confidence bands, and at-risk
  tables; the most common form of survival analysis in clinical research.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (time + survival),
  `mj-chart-grid`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`,
  `mj-chart-data-table`, `mj-chart-annotation`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Kaplan-Meier — OS by Treatment Arm" },
    "series": [
      {
        "name": "Arm A (n=120)",
        "points": [
          { "x": 0,  "y": 1.000, "censored": false, "at_risk": 120 },
          { "x": 6,  "y": 0.883, "censored": false, "at_risk": 104 },
          { "x": 12, "y": 0.761, "censored": true,  "at_risk": 89  }
        ]
      }
    ]
  }
  ```
  Same shape as `survival`; adds optional `at_risk` field per point for the
  numbers-at-risk table rendered below the plot.
- **SVG primitives:** Identical to `survival` (`<path>`, censored tick marks,
  optional CI band). Numbers-at-risk table rendered as a `<g>` of `<text>`
  elements below the x-axis when `at-risk="true"`.
- **Orientation:** `vertical` only.
- **Variants / modes:** None beyond `survival` parent: `ci`, `at-risk` and
  `mode="cumulative"` (1 − S(t)) work the same, and percent `y` values and
  date `x` values are read the same way. No log-rank p-value is drawn.
- **Phase:** P3
- **Notes:** `survival.js` registers `kaplan-meier` beside `survival`; both
  keys draw the same chart. Censored ticks are always drawn; the at-risk table
  is drawn under the plot only with `at-risk`. No separate renderer file.
  Accessibility: data-table includes time, survival estimate, CI bounds,
  at-risk count and censored columns.

---

### Forest plot  *(blobbogram)*

- **Renderer / `type`:** `forest` — **Primary renderer**
- **Controller:** `<mj-chart type="forest" ...>`
- **Purpose:** Compare effect sizes (odds ratios, hazard ratios, risk
  differences) and their confidence intervals across multiple studies or
  subgroups, with an optional pooled-estimate diamond; best for meta-analysis
  and subgroup analysis reporting.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (value + category),
  `mj-chart-grid`, `mj-chart-title`, `mj-chart-tooltip`,
  `mj-chart-data-table`, `mj-chart-annotation`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Forest Plot — Statin Trials" },
    "series": [
      {
        "name": "Studies",
        "groups": [
          {
            "category": "JUPITER 2008",
            "value": 0.56,
            "error_low": 0.18,
            "error_high": 0.22,
            "weight": 14.2
          }
        ]
      }
    ],
    "pooled": {
      "value": 0.61,
      "ci_lower": 0.52,
      "ci_upper": 0.72,
      "label": "Overall (I² = 24%)"
    }
  }
  ```
  Uses the statistical family `{ value, error_low, error_high }` shape.
  `weight` (optional) drives the size of the square marker. `pooled` supplies
  the summary diamond at the bottom; `ci_lower` / `ci_upper` are absolute
  bounds (not half-widths) for the diamond.
- **SVG primitives:** `<rect>` (square study marker, sized by weight),
  `<line>` (CI whisker shaft), `<line>` (CI whisker caps), `<polygon>`
  (pooled-estimate diamond), `<line>` (null-effect reference line at x = 0
  or x = 1 for ratios), `<text>` (study labels, value labels),
  `<g>` (per-study container)
- **Orientation:** `horizontal` only — effect size on the x-axis, studies on
  the y-axis (category band scale).
- **Variants / modes:** Log scale — `scale="log"` applies a `log` x-scale for
  odds-ratio or hazard-ratio data. The null-effect reference line moves to
  `x = 1` automatically in the model builder.
- **Phase:** P3
- **Notes:** Study labels are rendered as `<text>` to the left of the plot
  area; the plot SVG must leave left padding sufficient for the longest label,
  or labels go in a separate `<mj-chart-axis>` with `kind="category"`.
  Scales: `linear` or `log` (x), `band` (y). Accessibility: data-table lists
  study name, point estimate, lower CI, upper CI, and weight for each row.

---

### Funnel plot  *(publication-bias funnel, meta-analysis funnel)*

- **Renderer / `type`:** `funnel-plot` — **Primary renderer**
- **Controller:** `<mj-chart type="funnel-plot" ...>`
- **Purpose:** Detect publication bias or small-study effects in a meta-analysis
  by plotting study effect sizes against a precision measure (standard error,
  sample size); best for systematic reviews and meta-analytic reporting.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (effect + precision),
  `mj-chart-grid`, `mj-chart-title`, `mj-chart-tooltip`,
  `mj-chart-data-table`, `mj-chart-annotation`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Funnel Plot — Publication Bias Check" },
    "series": [
      {
        "name": "Studies",
        "points": [
          { "x": 0.56, "y": 0.12, "label": "JUPITER 2008" }
        ]
      }
    ],
    "funnel": {
      "summary_effect": 0.61,
      "pseudo_ci": [
        { "se": 0.0,  "lower": 0.61, "upper": 0.61 },
        { "se": 0.50, "lower": 0.12, "upper": 1.10 }
      ]
    }
  }
  ```
  Uses the XY `points` shape. `x` = study effect estimate, `y` = standard
  error (note: y-axis is inverted by convention — zero SE at top). `funnel`
  carries the summary effect and pre-computed pseudo-confidence funnel bounds
  at each SE level; without `pseudo_ci` the 95 % funnel `summary_effect ±
  1.96 × SE` is drawn.
- **SVG primitives:** `<circle>` (individual study points), `<path>` (funnel
  boundary lines — two lines converging upward), `<line>` (vertical summary-
  effect reference line), `<rect>` / `<polygon>` (contour shading), `<g>`,
  `<text>` (optional point labels)
- **Orientation:** `n/a` — axes are always effect (x) vs precision/SE (y,
  inverted).
- **Variants / modes:** Contour-enhanced funnel — `contours="true"` shades
  where a study would be significant against the null effect: p < 0.01
  (outside the 99 % wedge) and 0.01 ≤ p < 0.05 (between the 95 % and 99 %
  wedges), with wedges opening from SE 0 at `null-value`; both bands get a
  legend entry. `null-value` (number, default 0 — right for differences and
  log ratios) is the null effect of the contours. `labels="true"` draws each
  point's `label` right of it (flipped left near the right edge, nudged or
  dropped on overlap). Also cross-listed in the Flow & Process category where
  `type="funnel"` refers to the marketing/sales funnel chart — these are
  completely different renderers sharing only a name.
- **Phase:** P4
- **Notes:** The y-axis is inverted (larger SE at the bottom, zero at top);
  the model builder sets `y_invert: true` in the scale config. The funnel
  boundary path is computed from the `pseudo_ci` array by the `svgdraw.js`
  path builder. Scales: `linear` (x), `linear` inverted (y).
  Cross-reference: the marketing funnel chart uses `type="funnel"` (see
  08-flow-process.md); this statistical funnel uses `type="funnel-plot"` to
  avoid collision.
