# Trend & Time-Series Charts

> Catalog of chart types in this category for the automojo-webworks SVG chart
> library. Architecture, the coordinated-element model, the part components,
> the JSON contract, and phasing are defined in `../../chart-components-plan.md`
> and are not repeated here.

Charts that show how values change over time or ordered intervals. Fourteen catalog
names map to **nine primary renderers** after consolidation.

---

### Line Chart  *(line graph, time-series line)*

- **Renderer / `type`:** `line` — **Primary renderer**
- **Controller:** `<mj-chart type="line" ...>`
- **Purpose:** Show a single continuous trend over a time axis.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (kind="time" side="bottom" + kind="value" side="start"), `mj-chart-grid`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-crosshair`, `mj-chart-annotation`, `mj-chart-data-table`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Monthly Revenue", "orientation": "vertical" },
    "series": [
      {
        "name": "Revenue",
        "color": "#optional",
        "points": [
          { "x": "2025-01", "y": 42000 },
          { "x": "2025-02", "y": 47500 }
        ]
      }
    ]
  }
  ```
  `x` values are ISO date strings or epoch milliseconds; the controller maps
  them to a `time` scale. `y` is numeric.
- **SVG primitives:** `<path>` (polyline via `svgdraw.linePath`), `<circle>` (point markers, optional), `<text>` (axis labels, value labels), `<line>` (axis, gridlines, crosshair), `<g>` (series group)
- **Orientation:** `vertical` (time on x-axis) / `horizontal` (time on y-axis)
- **Variants / modes:** Multi-line chart (multiple `series[]` entries on the same renderer); see below.
- **Phase:** P1
- **Notes:** Uses `time` scale on the temporal axis and `linear` scale on the value axis. A `curve` attribute on `<mj-chart>` (values: `linear` | `monotone` | `step`) selects the path interpolation algorithm in `svgdraw.js`. Dot markers are toggled by `show-points` attribute. This renderer is reused by the Sparkline (stripped-down mode).

---

### Multi-Line Chart  *(multiple series line, comparative line)*

- **Renderer / `type`:** `line` — **Variant of `line`**
- **Controller:** `<mj-chart type="line" ...>`
- **Purpose:** Compare multiple continuous trends over a shared time axis.
- **Decomposition:** Same as Line chart.
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Product Trends" },
    "series": [
      { "name": "Product A", "points": [{ "x": "2025-01", "y": 120 }, { "x": "2025-02", "y": 135 }] },
      { "name": "Product B", "points": [{ "x": "2025-01", "y": 80  }, { "x": "2025-02", "y": 95  }] }
    ]
  }
  ```
  Multiple `series[]` entries, all sharing the same time domain; the renderer
  draws one `<path>` per series and assigns colors from the token color ramp.
- **SVG primitives:** `<path>` (one per series), `<circle>` (markers), `<text>`, `<line>`, `<g>`
- **Orientation:** `vertical` / `horizontal`
- **Variants / modes:** Single-series line chart is a degenerate case of the same renderer.
- **Phase:** P1
- **Notes:** No separate renderer; the `line` renderer handles any number of `series[]` entries. Legend is essential here and becomes interactive (series toggle via `mj-chart-series-toggle` event).

---

### Area Chart  *(filled line chart)*

- **Renderer / `type`:** `area` — **Primary renderer**
- **Controller:** `<mj-chart type="area" ...>`
- **Purpose:** Show a trend and emphasise the magnitude of values below (or above) the line.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (time + value), `mj-chart-grid`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-crosshair`, `mj-chart-annotation`, `mj-chart-data-table`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Bandwidth Usage" },
    "series": [
      { "name": "Download", "points": [{ "x": "2025-01", "y": 320 }, { "x": "2025-02", "y": 410 }] }
    ]
  }
  ```
  Same `series[].points: [{x, y}]` shape as `line`. A `stack` attribute on
  `<mj-chart>` controls the stack mode (see Variants).
- **SVG primitives:** `<path>` (closed area fill + upper stroke), `<text>`, `<line>`, `<g>`
- **Orientation:** `vertical` / `horizontal`
- **Variants / modes:** Stacked Area Chart (`stack="stack"`); 100% Stacked Area Chart (`stack="stack100"`). Both are served by this renderer with a different stacking computation applied to the model before drawing.
- **Phase:** P1
- **Notes:** The renderer closes the path to the baseline (zero or stacked baseline). Fill opacity is controlled by `--mj-chart-area-fill-opacity` token (default ~0.3). Curve interpolation follows the same `curve` attribute as `line`. When `stack="stack100"` the value axis range is forced to `[0, 1]` and axis labels are formatted as percentages.

---

### Stacked Area Chart  *(layered area)*

- **Renderer / `type`:** `area` — **Variant of `area`**
- **Controller:** `<mj-chart type="area" stack="stack" ...>`
- **Purpose:** Show how multiple series contribute to a cumulative total over time.
- **Decomposition:** Same as Area chart.
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Traffic by Source" },
    "series": [
      { "name": "Organic", "points": [{ "x": "2025-Q1", "y": 5400 }, { "x": "2025-Q2", "y": 6200 }] },
      { "name": "Paid",    "points": [{ "x": "2025-Q1", "y": 2100 }, { "x": "2025-Q2", "y": 3000 }] }
    ]
  }
  ```
- **SVG primitives:** `<path>` (one closed band per series), `<text>`, `<line>`, `<g>`
- **Orientation:** `vertical` / `horizontal`
- **Variants / modes:** Base `area` renderer; controlled via `stack="stack"`.
- **Phase:** P1
- **Notes:** Stack baselines are computed by `chartmodel.js` before the renderer runs; the renderer receives pre-stacked `y0`/`y1` pairs per point.

---

### 100% Stacked Area Chart  *(proportional area, normalized stacked area)*

- **Renderer / `type`:** `area` — **Variant of `area`**
- **Controller:** `<mj-chart type="area" stack="stack100" ...>`
- **Purpose:** Show proportional composition of multiple series over time, always summing to 100%.
- **Decomposition:** Same as Area chart.
- **JSON shape:** Same multi-series `series[].points: [{x, y}]` shape as Stacked Area; normalization is applied in the model layer.
- **SVG primitives:** `<path>`, `<text>`, `<line>`, `<g>`
- **Orientation:** `vertical` / `horizontal`
- **Variants / modes:** Base `area` renderer; controlled via `stack="stack100"`.
- **Phase:** P1
- **Notes:** Value axis is locked to `[0%, 100%]`. Tooltip shows both absolute value and percentage share. Accessibility note: color alone does not distinguish layers — patterns or labels are added when `forced-colors` is active.

---

### Step Chart  *(step line, staircase chart)*

- **Renderer / `type`:** `step` — **Primary renderer**
- **Controller:** `<mj-chart type="step" ...>`
- **Purpose:** Visualise values that remain constant between discrete change points (e.g. interest rates, threshold changes, inventory levels).
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (time + value), `mj-chart-grid`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-crosshair`, `mj-chart-annotation`, `mj-chart-data-table`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Interest Rate History" },
    "series": [
      {
        "name": "Fed Funds Rate",
        "points": [
          { "x": "2023-07-26", "y": 5.25 },
          { "x": "2023-11-01", "y": 5.50 },
          { "x": "2024-09-18", "y": 5.00 }
        ]
      }
    ]
  }
  ```
  Same `points: [{x, y}]` shape as `line`. A `step-position` attribute
  (`before` | `after` | `middle`, default `after`) controls where the
  vertical jump is placed relative to each `x` value.
- **SVG primitives:** `<path>` (horizontal + vertical segments via `svgdraw.stepPath`), `<circle>` (change markers, optional), `<text>`, `<line>`, `<g>`
- **Orientation:** `vertical` / `horizontal`
- **Variants / modes:** Filled step area possible by applying `area`-style path closing — not a separate renderer, controlled by a `fill` boolean attribute.
- **Phase:** P1
- **Notes:** The step path builder in `svgdraw.js` is a sibling of `linePath`; it emits only horizontal and vertical segments. Reuses the `time` + `linear` scale pair from `line`.

---

### Sparkline  *(inline trend, micro chart)*

- **Renderer / `type`:** `sparkline` — **Primary renderer**
- **Controller:** `<mj-chart type="sparkline" ...>`
- **Purpose:** Provide a compact, word-sized trend summary embedded inline in text, tables, or dashboards — no axes, no legend, minimal chrome.
- **Decomposition:** `mj-chart-plot` only (no axes, no legend, no title). `mj-chart-tooltip` is optional. `mj-chart-data-table` is always present but visually hidden.
- **JSON shape:**
  ```json
  {
    "meta": { "title": "30-day price trend" },
    "series": [
      { "name": "Price", "points": [{ "x": "2025-04-01", "y": 142 }, { "x": "2025-04-02", "y": 138 }] }
    ]
  }
  ```
  Alternatively, a shorthand `values` array may be used when timestamps are
  uniform and unimportant:
  ```json
  { "series": [{ "name": "Price", "values": [142, 138, 145, 151, 148] }] }
  ```
- **SVG primitives:** `<path>` (line or area), `<circle>` (start/end/min/max markers), `<rect>` (bar variant), `<text>` (optional last-value label)
- **Orientation:** `vertical` (default) / `horizontal`
- **Variants / modes:** Sparkline bar variant (`sparkline-variant="bar"`) renders a row of `<rect>` instead of a `<path>`. Both share this renderer.
- **Phase:** P1
- **Notes:** The element is designed to be 60–200 px wide and 20–40 px tall. No axis ticks are drawn; the `time` and `linear` scales are still used internally for accurate proportional placement. Highlight markers (first, last, min, max) are configurable via attributes. Supersedes the existing `mjsparkline.js` in `components/` (Phase 5 compatibility wrapper).

---

### Candlestick Chart  *(Japanese candlestick, OHLC candlestick)*

- **Renderer / `type`:** `ohlc` — **Primary renderer**
- **Controller:** `<mj-chart type="ohlc" style="candlestick" ...>`
- **Purpose:** Visualise financial price movement — open, high, low, and close — with filled bodies distinguishing bullish from bearish sessions.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (time + value), `mj-chart-grid`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-crosshair`, `mj-chart-annotation`, `mj-chart-data-table`. Volume sub-plot: second `mj-chart-plot` with its own value axis sharing the same time axis. No `mj-chart-legend` (usually single instrument).
- **JSON shape:**
  ```json
  {
    "meta": { "title": "AAPL Daily" },
    "candles": [
      { "t": "2025-04-01", "o": 171.20, "h": 175.80, "l": 170.55, "c": 174.90, "v": 52341200 },
      { "t": "2025-04-02", "o": 174.90, "h": 176.10, "l": 172.30, "c": 173.05, "v": 48200100 }
    ]
  }
  ```
  `t` — timestamp (ISO date or epoch ms); `o` — open; `h` — high; `l` — low;
  `c` — close; `v` — volume (optional).
- **SVG primitives:** `<rect>` (candle body; filled green/red per token `--mj-chart-up-color` / `--mj-chart-down-color`), `<line>` (upper and lower wicks), `<g>` (per candle group), `<text>` (axis labels)
- **Orientation:** `vertical` only (time on x-axis is conventional; horizontal is not supported and the attribute is ignored).
- **Variants / modes:** OHLC Chart (`style="ohlc"`) — same renderer, different mark shape (tick lines instead of filled rect); see below.
- **Phase:** P3
- **Notes:** Uses `time` scale (x) and `linear` scale (y, auto-domain from min `l` to max `h`). Candle width is computed from the time scale band width; the renderer adjusts at zoom levels. Bullish/bearish coloring never uses color alone — bodies are also distinguished by fill vs. outline when `forced-colors` is active.

---

### OHLC Chart  *(bar chart OHLC, open-high-low-close)*

- **Renderer / `type`:** `ohlc` — **Variant of `ohlc`**
- **Controller:** `<mj-chart type="ohlc" style="ohlc" ...>`
- **Purpose:** Show open-high-low-close financial data using the classic OHLC tick-bar style instead of filled candlestick bodies.
- **Decomposition:** Same as Candlestick chart.
- **JSON shape:** Identical to Candlestick — `candles: [{t, o, h, l, c, v}]`.
- **SVG primitives:** `<line>` (vertical range bar from `l` to `h`; left tick at `o`; right tick at `c`), `<g>`, `<text>`
- **Orientation:** `vertical` only.
- **Variants / modes:** Base `ohlc` renderer; controlled via `style="ohlc"`.
- **Phase:** P3
- **Notes:** The only difference from Candlestick is the mark drawing routine inside the renderer; all scale and model logic is shared. Both styles may be toggled at runtime by changing the `style` attribute.

---

### Gantt Chart  *(project timeline, task bar chart)*

- **Renderer / `type`:** `gantt` — **Primary renderer**
- **Controller:** `<mj-chart type="gantt" ...>`
- **Purpose:** Display project tasks, dependencies, and milestones on a horizontal time axis to communicate schedule and progress.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (kind="time" side="top" or "bottom"), `mj-chart-axis` (kind="category" side="start" — task/resource labels), `mj-chart-grid`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-annotation`, `mj-chart-data-table`. No `mj-chart-legend` unless task coloring by category is enabled.
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Q3 Launch Plan" },
    "tasks": [
      {
        "id": "design",
        "label": "UI Design",
        "start": "2025-07-01",
        "end":   "2025-07-14",
        "progress": 0.6,
        "group": "Design",
        "depends": [],
        "milestone": false
      },
      {
        "id": "dev",
        "label": "Frontend Dev",
        "start": "2025-07-10",
        "end":   "2025-07-28",
        "progress": 0.0,
        "group": "Engineering",
        "depends": ["design"],
        "milestone": false
      },
      {
        "id": "launch",
        "label": "Launch",
        "start": "2025-07-31",
        "end":   "2025-07-31",
        "progress": 0.0,
        "group": "Delivery",
        "depends": ["dev"],
        "milestone": true
      }
    ]
  }
  ```
  `progress` is `[0, 1]`; `milestone: true` renders a diamond instead of a bar.
- **SVG primitives:** `<rect>` (task bar; progress fill overlay), `<polygon>` (milestone diamond), `<line>` (dependency arrows — elbow connectors), `<text>` (task labels, axis ticks), `<g>` (per-task group)
- **Orientation:** `horizontal` (time on x-axis, tasks on y-axis) is canonical; `vertical` is not meaningful and the attribute is ignored.
- **Variants / modes:** Resource-grouped view (tasks grouped by `group` field) vs. flat list — controlled by a `group-by` attribute, not a separate renderer.
- **Phase:** P3
- **Notes:** Uses `time` scale (x) and `band` scale (y — one band per task row). Dependency arrows are drawn as elbow-connector `<line>` elements with arrowhead markers (`<marker>` in `<defs>`). Supersedes the existing `mjganttchart.js` in `components/` (Phase 5 compatibility wrapper). Row height is driven by `--mj-chart-gantt-row-height` token.

---

### Timeline Chart  *(event timeline, chronology chart)*

- **Renderer / `type`:** `timeline` — **Primary renderer**
- **Controller:** `<mj-chart type="timeline" ...>`
- **Purpose:** Plot discrete events or spans at their chronological positions on a time axis, emphasising sequence and temporal relationships rather than numeric magnitude.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (kind="time" side="bottom"), `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-annotation`, `mj-chart-data-table`. `mj-chart-legend` optional (when events are color-coded by category).
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Product History" },
    "events": [
      { "id": "v1",   "label": "v1.0 Launch",      "t": "2022-03-15",                       "category": "Release" },
      { "id": "outg", "label": "Major Outage",      "t": "2023-01-08",                       "category": "Incident" },
      { "id": "v2",   "label": "v2.0 Beta → GA",   "start": "2024-06-01", "end": "2024-08-20", "category": "Release" }
    ]
  }
  ```
  Point events have `t`; span events have `start`/`end`. Both may coexist.
- **SVG primitives:** `<circle>` (point event marker), `<rect>` (span event bar), `<line>` (leader lines from marker to label), `<text>` (event labels, axis ticks), `<g>` (per-event group)
- **Orientation:** `horizontal` (time on x-axis, events staggered vertically to avoid overlap) is primary; `vertical` (time on y-axis) is supported.
- **Variants / modes:** Single-lane vs. multi-lane (events sorted into swim lanes by category). Lane assignment is a layout step in `chartmodel.js`, not a separate renderer.
- **Phase:** P3
- **Notes:** Label collision avoidance is handled by a simple greedy vertical-offset algorithm in `chartmodel.js`. Uses `time` scale (temporal axis) and a computed lane count for the orthogonal axis. Supersedes `mjbranchgraph.js`-style timeline use-cases (Phase 5).

---

### Horizon Chart  *(folded area chart, dense time-series)*

- **Renderer / `type`:** `horizon` — **Primary renderer**
- **Controller:** `<mj-chart type="horizon" ...>`
- **Purpose:** Display many time series in a compact vertical stack by folding and layering area bands, enabling dense comparative views that would be unreadable as overlapping lines.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (kind="time" side="bottom"), `mj-chart-axis` (kind="category" side="start" — row labels), `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`. No `mj-chart-legend` (color encodes magnitude bands — a band legend `mj-chart-annotation` is used instead).
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Server CPU by Host" },
    "horizon-bands": 3,
    "series": [
      { "name": "web-01", "points": [{ "x": "2025-04-01T00:00Z", "y": 0.72 }, { "x": "2025-04-01T01:00Z", "y": 0.65 }] },
      { "name": "web-02", "points": [{ "x": "2025-04-01T00:00Z", "y": 0.41 }, { "x": "2025-04-01T01:00Z", "y": 0.88 }] }
    ]
  }
  ```
  `horizon-bands` specifies how many color bands the value range is divided
  into (default 3). Each series renders as one fixed-height row.
- **SVG primitives:** `<clipPath>` + `<path>` (each band is a filled area clipped to a fixed row height), `<rect>` (row background), `<text>` (row labels, axis ticks), `<g>` (per-row group)
- **Orientation:** `horizontal` (time on x-axis, series stacked vertically); `vertical` is not meaningful.
- **Variants / modes:** Positive-only (default) vs. diverging (negative values folded downward in a contrasting hue) — controlled by `diverging` boolean attribute.
- **Phase:** P5
- **Notes:** Uses `time` scale (x) and a fixed pixel height per row (configurable via `--mj-chart-horizon-row-height` token). The folding/layering is achieved by rendering N `<path>` fills at offset `y` positions inside a `<clipPath>` per row. The `band` count determines the sequential color ramp depth drawn from `--mj-chart-sequential-*` tokens.

---

### Streamgraph  *(stream chart, flowing stacked area)*

- **Renderer / `type`:** `streamgraph` — **Primary renderer**
- **Controller:** `<mj-chart type="streamgraph" ...>`
- **Purpose:** Show flowing composition of multiple categories over time using a symmetric, organic layout that emphasises the shape and rhythm of change rather than absolute values.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (kind="time" side="bottom"), `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-legend`, `mj-chart-data-table`. No value axis (y-values are layout positions, not meaningful magnitudes).
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Music Genre Streams by Year" },
    "series": [
      { "name": "Pop",      "points": [{ "x": "2018", "y": 3200 }, { "x": "2019", "y": 3800 }] },
      { "name": "Hip-Hop",  "points": [{ "x": "2018", "y": 2900 }, { "x": "2019", "y": 3500 }] },
      { "name": "Rock",     "points": [{ "x": "2018", "y": 2100 }, { "x": "2019", "y": 1900 }] }
    ]
  }
  ```
  Same `series[].points: [{x, y}]` shape as `area`. The streamgraph layout
  (Wiggle/silhouette baseline) is computed in `chartmodel.js`.
- **SVG primitives:** `<path>` (one closed organic band per series, drawn with monotone curve interpolation), `<text>` (inline series labels, axis ticks), `<g>` (series group)
- **Orientation:** `horizontal` (time on x-axis) is primary; `vertical` is not conventional.
- **Variants / modes:** Layout baseline modes — `wiggle` (default, minimises slope), `silhouette` (centered), `zero` (bottom-aligned, equivalent to stacked area) — controlled by `baseline` attribute.
- **Phase:** P5
- **Notes:** The streamgraph layout algorithm (Stacked Wiggle) is implemented in `chartmodel.js` as a pre-render transform that computes `y0`/`y1` pairs. When `baseline="zero"` the result is indistinguishable from a stacked area chart. The value axis is hidden because the y-positions carry no absolute meaning; a percentage tooltip is shown instead. Smooth `monotone` curves are used via `svgdraw.areaPath`.

---

### Bump Chart  *(rank chart, ranking-over-time chart)*

- **Renderer / `type`:** `bump` — **Primary renderer**
- **Controller:** `<mj-chart type="bump" ...>`
- **Purpose:** Track how ranked positions of competing items change across discrete time periods or categories, making rank crossings and trends immediately visible.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (kind="time" or "category" side="bottom"), `mj-chart-axis` (kind="value" side="start" — rank axis, inverted so rank 1 is at top), `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Streaming Platform Rankings" },
    "series": [
      {
        "name": "Platform A",
        "points": [
          { "x": "2022", "y": 3 },
          { "x": "2023", "y": 1 },
          { "x": "2024", "y": 2 }
        ]
      },
      {
        "name": "Platform B",
        "points": [
          { "x": "2022", "y": 1 },
          { "x": "2023", "y": 2 },
          { "x": "2024", "y": 1 }
        ]
      }
    ]
  }
  ```
  `y` values are integer ranks (1 = best). The value axis is inverted (rank 1
  at top). `x` values may be years, quarters, or any ordered category.
- **SVG primitives:** `<path>` (smooth S-curve connector between rank positions, drawn with monotone curve), `<circle>` (rank dot at each time period), `<text>` (series labels at start/end, axis ticks), `<g>` (per-series group)
- **Orientation:** `horizontal` (time/categories on x-axis, ranks on y-axis) is canonical; `vertical` is not meaningful.
- **Variants / modes:** None — the renderer is purpose-built for rank data. When `y` values are continuous (not integer ranks) the renderer still works but the y-axis is not inverted.
- **Phase:** P5
- **Notes:** Uses `point` scale (x — evenly-spaced category positions) and `linear` scale (y — inverted domain, e.g. `[N, 1]`). The S-curve between rank dots is produced by `svgdraw.bumpPath` (horizontal-to-vertical monotone cubic). Dots and curves share the same series color from the token ramp. End-of-line labels use a collision-avoidance nudge so they do not overlap when two series share the same final rank.
