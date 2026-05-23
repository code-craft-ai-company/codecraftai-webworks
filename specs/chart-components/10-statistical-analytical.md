# Statistical & Analytical Charts

> Catalog of chart types in this category for the automojo-webworks SVG chart
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

- **Renderer / `type`:** `box` — **Primary renderer**
- **Controller:** `<mj-chart type="box" ...>`
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
  the IQR box (reuses `box` renderer primitives). Half-violin — `half="true"`
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
- **Notes:** Cap width is configurable via `cap-width` attribute (default 8 px).
  Scales: `band` + `linear`. When used as an overlay on another chart (e.g. a
  bar chart) the controller can accept a second dataset in `error_series` that
  is drawn after the primary marks. Accessibility: tooltip and data-table expose
  value, lower bound (`value − error_low`), and upper bound (`value + error_high`).

---

### Confidence interval plot  *(CI plot, estimate range plot)*

- **Renderer / `type`:** `ci` — **Variant of `errorbar`**
- **Controller:** `<mj-chart type="ci" ...>`
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
  half-widths from the point estimate to each CI bound.
- **SVG primitives:** `<line>` (interval span), `<circle>` (point estimate),
  `<line>` (optional end caps), `<line>` (optional reference line at 0 or 1),
  `<g>`, `<text>`
- **Orientation:** `horizontal` | `vertical` — horizontal layout (value on
  x-axis, parameters on y-axis) is conventional for CI plots.
- **Variants / modes:** None beyond the `errorbar` parent. A reference-line
  annotation (zero-effect line) is added via `<mj-chart-annotation>`.
- **Phase:** P3
- **Notes:** The `ci` type key selects the `errorbar` renderer with default
  `orientation="horizontal"`, no centre bar, and a zero-reference annotation
  automatically injected into the model. No separate renderer file; `ci.js`
  re-exports `errorbar` renderer with a preset options object.

---

### Control chart  *(Shewhart control chart, SPC chart)*

- **Renderer / `type`:** `control` — **Primary renderer**
- **Controller:** `<mj-chart type="control" ...>`
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
  control limit (`lcl`), and centre line (`cl`). Multiple limit sets (e.g. for
  sigma levels) may be supplied as an array. Time points use ISO-8601 strings
  or sequence integers.
- **SVG primitives:** `<path>` (data series line), `<circle>` (sample points,
  coloured red when out-of-control), `<line>` (UCL, LCL, CL reference lines),
  `<rect>` (optional control-region band fill between UCL/LCL), `<g>`, `<text>`
- **Orientation:** `vertical` only (time on x-axis, value on y-axis); the
  horizontal mode is not meaningful for time-ordered process data.
- **Variants / modes:** X-bar, R-chart, S-chart, p-chart, c-chart — all use
  the same renderer; the chart sub-type is metadata that changes the y-axis
  label and the out-of-control detection rules applied by the data layer before
  the JSON is passed to the renderer.
- **Phase:** P3
- **Notes:** Out-of-control points are flagged in the JSON by an optional
  `"ooc": true` field on individual point objects; the renderer colours those
  `<circle>` elements using the `--mj-color-danger` token. Western Electric
  rules are the data layer's responsibility, not the renderer's. Scales:
  `time` or `point` (x), `linear` (y).

---

### Run chart  *(run sequence plot)*

- **Renderer / `type`:** `run` — **Variant of `line`**
- **Controller:** `<mj-chart type="run" ...>`
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
      { "label": "Median", "value": 3.1 }
    ]
  }
  ```
  Uses the XY `points` shape from plan §3.4. `reference_lines` is an optional
  array of horizontal annotations passed through to `<mj-chart-annotation>`.
- **SVG primitives:** `<path>` (connecting line), `<circle>` (individual
  observations), `<line>` (median / reference lines), `<g>`, `<text>`
- **Orientation:** `vertical` only (sequence on x-axis).
- **Variants / modes:** None. The `run` type key selects the `line` renderer
  with `markers="true"` and injects any `reference_lines` as annotation model
  entries. No separate renderer file.
- **Phase:** P3
- **Notes:** The median reference line is a common addition; the JSON
  `reference_lines` array avoids requiring a separate `<mj-chart-annotation>`
  declaration for the simple case. Scales: `point` (x), `linear` (y).

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
        "name": "Model v2 (AUC = 0.87)",
        "points": [
          { "x": 0.00, "y": 0.00 },
          { "x": 0.05, "y": 0.48 },
          { "x": 1.00, "y": 1.00 }
        ]
      }
    ]
  }
  ```
  Uses the XY `points` shape from plan §3.4. `x` = FPR, `y` = TPR. Multiple
  series overlay multiple models. The diagonal chance-line annotation is
  injected automatically by the model builder when `type="roc"`.
- **SVG primitives:** `<path>` (curve line per series), `<circle>` (optional
  threshold marker), `<path>` (optional AUC fill area), `<line>` (diagonal
  reference), `<g>`, `<text>`
- **Orientation:** `n/a` — axes are always FPR (x) vs TPR (y), both 0–1.
- **Variants / modes:** AUC shading — `shade-auc="true"` fills the area under
  the curve. Multiple series for multi-model comparison.
- **Phase:** P3
- **Notes:** The `roc` type key selects the shared `curve` renderer
  (`charts/core/renderers/curve.js`) with preset axis domain [0,1]×[0,1],
  axis labels "False Positive Rate" / "True Positive Rate", and a diagonal
  `<line>` annotation injected into the model. No separate renderer file.
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
        "name": "Model v3 (AP = 0.72)",
        "points": [
          { "x": 0.00, "y": 1.00 },
          { "x": 0.55, "y": 0.81 },
          { "x": 1.00, "y": 0.34 }
        ]
      }
    ]
  }
  ```
  `x` = recall, `y` = precision. A baseline annotation at `y = class_prevalence`
  is injected by the model builder when `type="precision-recall"`.
- **SVG primitives:** `<path>` (curve), `<circle>` (threshold markers),
  `<path>` (optional AP fill), `<line>` (baseline), `<g>`, `<text>`
- **Orientation:** `n/a`
- **Variants / modes:** Average precision (AP) shading — `shade-auc="true"`.
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
  `x` = proportion of population contacted (0–1), `y` = cumulative lift
  (ratio). A baseline at `y = 1` is injected automatically.
- **SVG primitives:** `<path>` (lift curve per model), `<line>` (baseline
  y = 1), `<circle>` (optional key threshold markers), `<g>`, `<text>`
- **Orientation:** `n/a`
- **Variants / modes:** Gains chart — `mode="gains"` changes the y-axis to
  cumulative percentage of positives captured; data layer recalculates `y`,
  renderer is unchanged.
- **Phase:** P3
- **Notes:** Shares the `curve` renderer. Preset axis label "% Population
  Contacted" / "Lift". Baseline annotation (`y = 1`) injected by the model
  builder. No separate renderer file.

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
- **Variants / modes:** Size-by-count — `size-by="n"` scales point radii via
  `sqrt` scale. Histogram overlay — `show-histogram="true"` adds a small
  prediction-distribution bar chart beneath the main plot.
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
  (0–1). `censored: true` marks a censored observation; the renderer draws a
  tick mark at that point rather than a step drop.
- **SVG primitives:** `<path>` (step-function line built with horizontal-then-
  vertical segments), `<circle>` or `<line>` tick (censored observation marks),
  `<path>` (optional confidence-band fill), `<g>`, `<text>`
- **Orientation:** `vertical` only (time on x-axis, survival probability on
  y-axis).
- **Variants / modes:** Confidence bands — `ci="true"` expects additional
  `ci_lower` / `ci_upper` fields on each point and draws a shaded band.
  Cumulative incidence — `mode="cumulative"` plots `1 − S(t)` (the y-axis is
  inverted in the model before rendering; the renderer is unchanged).
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
- **Variants / modes:** None beyond `survival` parent. Log-rank p-value
  annotation added via `<mj-chart-annotation>` when `p-value` is supplied
  in the JSON `meta`.
- **Phase:** P3
- **Notes:** The `kaplan-meier` type key selects the `survival` renderer with
  `markers="censored-ticks"` and optionally renders the at-risk table as an
  additional `<g>` inside the plot SVG. No separate renderer file. Accessibility:
  data-table includes time, survival estimate, and at-risk count columns.

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
  at each SE level.
- **SVG primitives:** `<circle>` (individual study points), `<path>` (funnel
  boundary lines — two lines converging upward), `<line>` (vertical summary-
  effect reference line), `<g>`, `<text>` (optional point labels)
- **Orientation:** `n/a` — axes are always effect (x) vs precision/SE (y,
  inverted).
- **Variants / modes:** Contour-enhanced funnel — `contours="true"` adds
  shaded significance-level regions (p < 0.05, p < 0.01) rendered as
  `<path>` bands between the funnel lines. Also cross-listed in the Flow &
  Process category where `type="funnel"` refers to the marketing/sales funnel
  chart — these are completely different renderers sharing only a name.
- **Phase:** P4
- **Notes:** The y-axis is inverted (larger SE at the bottom, zero at top);
  the model builder sets `y_invert: true` in the scale config. The funnel
  boundary path is computed from the `pseudo_ci` array by the `svgdraw.js`
  path builder. Scales: `linear` (x), `linear` inverted (y).
  Cross-reference: the marketing funnel chart uses `type="funnel"` (see
  08-flow-process.md); this statistical funnel uses `type="funnel-plot"` to
  avoid collision.
