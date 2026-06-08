# UX, Product & Business Charts

> Catalog of chart types in this category for the codecraftai-webworks SVG chart
> library. Architecture, the coordinated-element model, the part components,
> the JSON contract, and phasing are defined in `../../chart-components-plan.md`
> and are not repeated here.

---

### KPI Card  *(metric card, scorecard tile, big-number card)*
- **Renderer / `type`:** `kpi` — **Primary renderer**
- **Controller:** `<mj-chart type="kpi" ...>`
- **Purpose:** Display a single headline metric with an optional comparison value, trend indicator, and spark trend line.
- **Decomposition:** `mj-chart-plot`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`.
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Monthly Active Users", "orientation": "vertical" },
    "kpi": {
      "value": 42800,
      "format": ",.0f",
      "label": "MAU",
      "comparison": { "value": 39100, "label": "Last month" },
      "trend": "up",
      "spark": [38000, 39100, 40500, 41200, 42800]
    }
  }
  ```
- **SVG primitives:** `<text>` (primary value, label, comparison delta), `<path>` (spark trend line, trend-arrow icon), `<rect>` (background badge for delta), `<g>` (layout groups).
- **Orientation:** `n/a` — the card is a fixed single-block layout; no axis swap applies.
- **Variants / modes:** None; multiple KPI cards are simply multiple `<mj-chart type="kpi">` elements arranged by the host layout.
- **Phase:** P5
- **Notes:** The optional spark line reuses the `line` renderer path builder from `svgdraw.js`. Trend direction is never encoded by color alone — an arrow icon and accessible `aria-label` on the delta are required. The data-table model exposes current value, comparison value, and delta percentage as a two-row `<table>`.

---

### Gauge Chart  *(dial chart, speedometer chart, arc gauge)*
- **Renderer / `type`:** `gauge` — **Primary renderer**
- **Controller:** `<mj-chart type="gauge" ...>`
- **Purpose:** Show progress of a single metric toward a target on a circular arc dial — ideal for KPI dashboards.
- **Decomposition:** `mj-chart-plot`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-annotation`, `mj-chart-data-table`.
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Server CPU" },
    "gauge": {
      "value": 68,
      "min": 0,
      "max": 100,
      "unit": "%",
      "thresholds": [
        { "value": 60, "label": "Warning", "color": "--mj-color-warning" },
        { "value": 85, "label": "Critical", "color": "--mj-color-danger" }
      ],
      "needle": true,
      "start_angle": -135,
      "sweep_angle": 270
    }
  }
  ```
- **SVG primitives:** `<path>` (arc track segments, needle), `<circle>` (needle pivot), `<text>` (value label, unit, min/max tick labels), `<g>` (rotation transforms for needle).
- **Orientation:** `n/a` — radial layout; orientation attribute ignored.
- **Variants / modes:** Semicircle gauge (`sweep_angle=180`); full-circle progress ring (`sweep_angle=360`). Both are modes of `gauge`, not separate renderers.
- **Phase:** P5 (supersedes `mjgauge.js` in Phase 5 migration)
- **Notes:** Uses a `linear` scale mapping `[min, max]` to `[start_angle, start_angle + sweep_angle]`. Threshold bands are drawn as separate arc `<path>` segments. The needle is never the sole indicator — the numeric value label is always present. Accessibility: `role="meter"`, `aria-valuenow`, `aria-valuemin`, `aria-valuemax` on the SVG root.

---

### Bullet Chart  *(bullet graph)*
- **Renderer / `type`:** `bullet` — **Primary renderer**
- **Controller:** `<mj-chart type="bullet" ...>`
- **Purpose:** Compare an actual value against one or more targets and qualitative ranges — a dense, space-efficient alternative to the gauge.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (value, `side="bottom"` for horizontal), `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`.
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Revenue", "orientation": "horizontal" },
    "bullet": {
      "value": 270,
      "target": 300,
      "ranges": [
        { "value": 200, "label": "Poor" },
        { "value": 250, "label": "Satisfactory" },
        { "value": 320, "label": "Good" }
      ],
      "unit": "k"
    }
  }
  ```
- **SVG primitives:** `<rect>` (qualitative range bands, feature bar), `<line>` (target comparative marker), `<text>` (axis tick labels), `<g>` (row grouping for stacked multi-bullet).
- **Orientation:** `horizontal` (default) and `vertical`; the `bar` renderer orientation swap logic (plan §3.6) applies directly since bullet is a specialized bar.
- **Variants / modes:** Multi-bullet — multiple `bullet` objects in a `bullets: [...]` array; each row is one bullet drawn by the same renderer.
- **Phase:** P2
- **Notes:** Qualitative range `<rect>` elements use progressively lighter shades of a single token color (`--mj-chart-bullet-range-*`) so the chart is readable in forced-colors mode. The target marker line is never the only encoding — the data-table exposes actual, target, and range labels.

---

### Funnel Chart  *(conversion funnel, sales funnel, pipeline funnel)*
- **Renderer / `type`:** `funnel` — **Primary renderer**
- **Controller:** `<mj-chart type="funnel" ...>`
- **Purpose:** Visualize sequential stages of a conversion pipeline, showing volume lost at each step.
- **Decomposition:** `mj-chart-plot`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-value-labels`, `mj-chart-data-table`.
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Signup Funnel", "orientation": "vertical" },
    "categories": ["Visited", "Signed Up", "Verified", "Activated", "Retained"],
    "series": [
      { "name": "Users", "values": [10000, 6800, 4200, 2900, 1750] }
    ]
  }
  ```
- **SVG primitives:** `<polygon>` or `<path>` (trapezoid stage shapes), `<text>` (stage label, count, conversion-rate annotation), `<g>` (per-stage groups).
- **Orientation:** `vertical` (wide top, narrowing downward; default) and `horizontal` (left-to-right pipeline); the renderer swaps the major axis.
- **Variants / modes:** Stacked funnel (multiple series stacked across width, `group="stack"`).
- **Phase:** P4
- **Notes:** Stage widths are proportional to the `linear` scale over `[0, max(values)]`. Conversion rate between adjacent stages is computed in the renderer and exposed on `mj-chart-point` events. The data-table includes stage name, count, and drop-off rate columns.

---

### Cohort Chart  *(cohort retention matrix, cohort heatmap)*
- **Renderer / `type`:** `cohort` — **Primary renderer**
- **Controller:** `<mj-chart type="cohort" ...>`
- **Purpose:** Track how discrete user cohorts (grouped by sign-up period) retain or convert over successive time periods — the canonical product-analytics retention view.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (category, `side="start"` for row labels), `mj-chart-axis` (time/period, `side="top"`), `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`.
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Weekly Cohort Retention" },
    "cohorts": [
      {
        "label": "2025-W01",
        "size": 1200,
        "periods": [1.0, 0.62, 0.45, 0.38, 0.31, 0.27]
      },
      {
        "label": "2025-W02",
        "size": 980,
        "periods": [1.0, 0.59, 0.43, 0.36, 0.29]
      }
    ],
    "period_labels": ["Week 0", "Week 1", "Week 2", "Week 3", "Week 4", "Week 5"]
  }
  ```
- **SVG primitives:** `<rect>` (cell background fill), `<text>` (retention percentage per cell, axis labels), `<g>` (row and column groups).
- **Orientation:** `n/a` — the row/column grid is fixed; orientation is not meaningful.
- **Variants / modes:** Absolute count mode (`values` are raw user counts rather than retention rates, toggled by `mode="count"`).
- **Phase:** P5
- **Notes:** Cell color encodes retention rate via a sequential color scale (`--mj-chart-sequential-*` tokens) from full retention (darkest) to zero (lightest). Color is never the sole encoding — the numeric value is printed inside each cell. This renderer is essentially a specialized heatmap; the cell-fill logic reuses the `heatmap` renderer's color-scale mapping (see **Heatmap** entry below). The data-table exposes the full cohort × period matrix.

---

### Retention Curve  *(user retention curve, survival curve, retention over time)*
- **Renderer / `type`:** `retention-curve` — **Variant of `line`**
- **Controller:** `<mj-chart type="retention-curve" ...>`
- **Purpose:** Plot the fraction of users from each cohort still active at each period offset — reveals how quickly different cohorts decay.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (time/period, `side="bottom"`), `mj-chart-axis` (value 0–100 %, `side="start"`), `mj-chart-grid`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-crosshair`, `mj-chart-data-table`.
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Cohort Retention Curves" },
    "categories": [0, 1, 2, 3, 4, 5, 6, 7],
    "series": [
      { "name": "2025-W01", "values": [100, 62, 45, 38, 31, 27, 24, 22] },
      { "name": "2025-W02", "values": [100, 59, 43, 36, 29, 25, 22] }
    ]
  }
  ```
- **SVG primitives:** `<path>` (line per series via `svgdraw.js` line builder), `<circle>` (data-point markers), `<text>` (axis labels), `<g>` (per-series groups). Identical to the `line` renderer's primitives.
- **Orientation:** `horizontal` (period on x-axis, retention % on y-axis; default and canonical); `vertical` supported via the `line` renderer orientation swap.
- **Variants / modes:** None beyond the `line` renderer's existing curve styles (`curve="linear|monotone|step"`).
- **Phase:** P5
- **Notes:** This is the `line` renderer configured with a `[0, 100]` value domain, percentage axis formatting, and a clamp that prevents values above 100. No new renderer code is required — `type="retention-curve"` applies a preset JSON-schema and default scale configuration on top of the `line` renderer.

---

### Churn Chart  *(churn rate chart, attrition chart)*
- **Renderer / `type`:** `churn` — **Variant of `bar`**
- **Controller:** `<mj-chart type="churn" ...>`
- **Purpose:** Display churn (or attrition) rate over time periods, optionally segmented by reason or cohort — highlights when and where users are lost.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (time, `side="bottom"`), `mj-chart-axis` (value, `side="start"`), `mj-chart-grid`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-value-labels`, `mj-chart-data-table`.
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Monthly Churn Rate", "orientation": "vertical" },
    "categories": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
    "series": [
      { "name": "Voluntary", "values": [2.1, 2.4, 2.0, 1.8, 2.2, 1.9] },
      { "name": "Involuntary", "values": [0.6, 0.5, 0.7, 0.4, 0.6, 0.5] }
    ]
  }
  ```
- **SVG primitives:** `<rect>` (bars per period, stacked or grouped), `<text>` (axis labels, value labels), `<g>` (per-series groups). Identical to the `bar` renderer's primitives.
- **Orientation:** `vertical` (time on x-axis, rate % on y-axis; default) and `horizontal`.
- **Variants / modes:** Single-series total churn (`group="cluster"`), segmented stacked churn (`group="stack"`). Both handled by the `bar` renderer's existing `group` attribute.
- **Phase:** P5
- **Notes:** No new renderer; `type="churn"` applies a percentage axis format preset and negative-value coloring convention (bars drawn in `--mj-color-danger` tokens when values represent loss). The `bar` renderer in `charts/core/renderers/bar.js` (defined in `specs/chart-components/01-comparison.md`) is the underlying renderer.

---

### User Journey Map  *(journey map, experience map, UX flow)*
- **Renderer / `type`:** `journey` — **Primary renderer**
- **Controller:** `<mj-chart type="journey" ...>`
- **Purpose:** Visualize discrete steps (or phases) in a user experience, with a sentiment or quality score at each step — used for qualitative UX storytelling alongside quantitative data.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (category/steps, `side="bottom"`), `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`.
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Onboarding Journey" },
    "steps": [
      { "label": "Discover",  "score": 4.2, "touchpoints": ["Ad", "Word of mouth"], "pain_points": [] },
      { "label": "Sign Up",   "score": 3.5, "touchpoints": ["Website"],             "pain_points": ["Long form"] },
      { "label": "Onboard",   "score": 2.8, "touchpoints": ["Email"],               "pain_points": ["Confusing UI"] },
      { "label": "First Use", "score": 3.9, "touchpoints": ["App"],                 "pain_points": [] },
      { "label": "Retention", "score": 4.5, "touchpoints": ["Push", "Email"],        "pain_points": [] }
    ],
    "score_range": [1, 5]
  }
  ```
- **SVG primitives:** `<path>` (emotion/score line connecting steps), `<circle>` (step node markers, sized by touchpoint count), `<rect>` (step lane backgrounds), `<text>` (step labels, scores, pain-point annotations), `<g>` (per-step groups).
- **Orientation:** `horizontal` (steps flow left to right; default and canonical); `vertical` (steps flow top to bottom) supported.
- **Variants / modes:** Multi-persona journey — multiple `steps` arrays, one per persona, drawn as separate lines on the same layout.
- **Phase:** P5
- **Notes:** Uses a `linear` scale for `score_range` on the vertical axis and a `band` scale for steps on the horizontal axis. The emotion line reuses the `line` renderer's `<path>` builder. Pain-point annotations reuse `mj-chart-annotation`. Accessibility: the data-table exposes step, score, touchpoints, and pain points as a structured table.

---

### Heatmap  *(calendar heatmap, usage heatmap, density heatmap, grid heatmap)*
- **Renderer / `type`:** `heatmap` — **Primary renderer**
- **Controller:** `<mj-chart type="heatmap" ...>`
- **Purpose:** Encode a numeric value in a two-dimensional grid of cells using color intensity — reveals spatial, temporal, or categorical density and usage patterns.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (x-category, `side="bottom"`), `mj-chart-axis` (y-category, `side="start"`), `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`.
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Page Views by Hour and Day" },
    "x_categories": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    "y_categories": ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00"],
    "cells": [
      { "x": "Mon", "y": "08:00", "value": 1420 },
      { "x": "Mon", "y": "12:00", "value": 2310 }
    ],
    "color_scale": "sequential"
  }
  ```
- **SVG primitives:** `<rect>` (one per cell, fill driven by sequential color scale), `<text>` (optional value labels inside cells, axis tick labels), `<g>` (row groups).
- **Orientation:** `n/a` — the x/y grid axes are semantically fixed; swapping them is a data transform, not an orientation mode.
- **Variants / modes:** Calendar heatmap (`layout="calendar"`, with year/month/week grid structure); diverging color scale (`color_scale="diverging"` for values above and below a midpoint).
- **Phase:** P3
- **Notes:** Color scale is a `linear` scale mapping `[domain_min, domain_max]` to the `--mj-chart-sequential-*` or `--mj-chart-diverging-*` token ramp. Color is never the sole encoding — a numeric label or tooltip with the exact value is always accessible. The `cohort` renderer (above) reuses this cell-fill logic directly. The correlation matrix renderer (in `specs/chart-components/04-relationship-correlation.md`) also delegates cell fills to this renderer.

---

### Session Flow Chart  *(user flow chart, navigation flow, user path analysis)*
- **Renderer / `type`:** `session-flow` — **Variant of `sankey`**
- **Controller:** `<mj-chart type="session-flow" ...>`
- **Purpose:** Show aggregated paths users navigate through an application — which pages or screens they visit in sequence and where they exit.
- **Decomposition:** `mj-chart-plot`, `mj-chart-title`, `mj-chart-legend`, `mj-chart-tooltip`, `mj-chart-data-table`.
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Checkout Session Flow" },
    "nodes": [
      { "id": "home",     "label": "Home" },
      { "id": "pdp",      "label": "Product" },
      { "id": "cart",     "label": "Cart" },
      { "id": "checkout", "label": "Checkout" },
      { "id": "confirm",  "label": "Confirm" },
      { "id": "exit",     "label": "Exit" }
    ],
    "links": [
      { "source": "home",     "target": "pdp",      "value": 5400 },
      { "source": "pdp",      "target": "cart",     "value": 2100 },
      { "source": "pdp",      "target": "exit",     "value": 3300 },
      { "source": "cart",     "target": "checkout", "value": 1600 },
      { "source": "checkout", "target": "confirm",  "value": 1200 },
      { "source": "checkout", "target": "exit",     "value": 400  }
    ]
  }
  ```
- **SVG primitives:** `<rect>` (stage nodes), `<path>` (flow bands between stages via cubic Bézier), `<text>` (node labels, flow volume), `<g>` (per-stage groups). Same primitives as the `sankey` renderer.
- **Orientation:** `horizontal` (stages flow left to right; default) and `vertical`.
- **Variants / modes:** None beyond the `sankey` renderer modes. Exit nodes are simply leaf nodes with no outbound links.
- **Phase:** P5
- **Notes:** This is the `sankey` renderer (defined in `specs/chart-components/08-flow-process.md`) applied to session navigation data. `type="session-flow"` sets default node coloring by depth level and enables an exit-rate annotation via `mj-chart-annotation`. No new renderer code is required.

---

### Feature Adoption Chart  *(adoption curve, feature uptake chart)*
- **Renderer / `type`:** `feature-adoption` — **Variant of `line`**
- **Controller:** `<mj-chart type="feature-adoption" ...>`
- **Purpose:** Track the cumulative or periodic percentage of users who have adopted one or more features over time — shows uptake curves and compares feature rollout trajectories.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (time, `side="bottom"`), `mj-chart-axis` (value 0–100 %, `side="start"`), `mj-chart-grid`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-crosshair`, `mj-chart-annotation`, `mj-chart-data-table`.
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Feature Adoption Over Time", "orientation": "vertical" },
    "categories": ["2025-01", "2025-02", "2025-03", "2025-04", "2025-05", "2025-06"],
    "series": [
      { "name": "Dark Mode",     "values": [2.1, 8.4, 18.2, 31.0, 44.5, 55.3] },
      { "name": "Export to CSV", "values": [0.0, 1.2,  5.6, 12.1, 20.4, 27.8] }
    ],
    "annotations": [
      { "type": "line", "axis": "x", "value": "2025-02", "label": "GA Launch" }
    ]
  }
  ```
- **SVG primitives:** `<path>` (line per series), `<circle>` (data-point markers), `<line>` (annotation reference lines), `<text>` (axis labels, annotation labels), `<g>`. Identical to the `line` renderer.
- **Orientation:** `vertical` (time on x-axis; default) and `horizontal`.
- **Variants / modes:** Cumulative vs. periodic adoption toggled by `mode="cumulative|periodic"`.
- **Phase:** P5
- **Notes:** `type="feature-adoption"` is the `line` renderer with a `[0, 100]` value clamp, percentage y-axis formatting, and launch-event annotations via `mj-chart-annotation`. No new renderer code; the schema preset enforces the `0–100` value domain. The `line` renderer lives in `specs/chart-components/02-trend-timeseries.md`.

---

### Segmentation Chart  *(user segmentation chart, segment comparison chart)*
- **Renderer / `type`:** `segmentation` — **Variant of `bar`**
- **Controller:** `<mj-chart type="segmentation" ...>`
- **Purpose:** Compare quantitative metrics across distinct user segments side by side — reveals how cohorts or persona groups differ on key KPIs.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (category/segment, `side="bottom"` or `side="start"`), `mj-chart-axis` (value, `side="start"` or `side="bottom"`), `mj-chart-grid`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-value-labels`, `mj-chart-data-table`.
- **JSON shape:**
  ```json
  {
    "meta": { "title": "KPI by User Segment", "orientation": "vertical" },
    "categories": ["Power Users", "Casual Users", "Trial Users", "Churned"],
    "series": [
      { "name": "Avg Session (min)", "values": [24.1, 9.3, 4.7, 2.1] },
      { "name": "Feature Depth",     "values": [8.4,  3.2, 1.1, 0.8] }
    ]
  }
  ```
- **SVG primitives:** `<rect>` (bars per segment, grouped or stacked), `<text>` (axis labels, value labels), `<g>` (per-series groups). Identical to the `bar` renderer.
- **Orientation:** `vertical` (segments on x-axis; default) and `horizontal` (segments on y-axis, useful for long segment names).
- **Variants / modes:** Grouped (`group="cluster"`, default), stacked (`group="stack"`), 100%-normalized (`group="stack100"`). All handled by the `bar` renderer's existing `group` attribute.
- **Phase:** P5
- **Notes:** No new renderer; `type="segmentation"` is the `bar` renderer with a preset that defaults to `group="cluster"` and enables segment-label truncation for long names. The `bar` renderer is defined in `specs/chart-components/01-comparison.md`.
