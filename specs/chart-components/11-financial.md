# Financial Charts

> Catalog of chart types in this category for the codecraftai-webworks SVG chart
> library. Architecture, the coordinated-element model, the part components,
> the JSON contract, and phasing are defined in `../../chart-components-plan.md`
> and are not repeated here.

---

### Candlestick Chart  *(Japanese candlestick, OHLC candle)*
- **Renderer / `type`:** `ohlc` — **Primary renderer**
- **Controller:** `<mj-chart type="ohlc" style="candle" ...>`
- **Purpose:** Visualise stock or asset price movement over time; body encodes open-to-close range, wicks encode high/low extremes.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (time, bottom; value, start), `mj-chart-grid`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-crosshair`, `mj-chart-brush`, `mj-chart-annotation`, `mj-chart-data-table`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "AAPL – Daily", "orientation": "vertical" },
    "candles": [
      { "t": "2025-01-02", "o": 185.2, "h": 189.4, "l": 184.1, "c": 188.7, "v": 52340000 }
    ]
  }
  ```
  Fields: `t` — ISO-8601 date/datetime; `o` open; `h` high; `l` low; `c` close; `v` volume (optional).
- **SVG primitives:** `<rect>` (candle body), `<line>` (upper and lower wicks), `<g>` (per-candle group), `<text>` (axis labels)
- **Orientation:** vertical (time → x, price → y); horizontal layout is `n/a` — price candles have no conventional horizontal form.
- **Variants / modes:** `style="candle"` (default, filled body) vs `style="ohlc"` (tick-bar form — see OHLC chart below).
- **Phase:** P3
- **Notes:** Uses `time` scale on the category axis and `linear` scale on the value axis. Bullish candles (close ≥ open) and bearish candles (close < open) are coloured from `--mj-chart-positive` / `--mj-chart-negative` design tokens so no meaning is encoded by color alone — tooltip and `aria-label` carry directional text. Volume bars may be overlaid at reduced opacity in the lower portion of the same plot or via a companion `mj-chart` controller sharing the time scale. The `mj-chart-brush` allows zooming the time window.

---

### OHLC Chart  *(open-high-low-close bar chart, bar chart)*
- **Renderer / `type`:** `ohlc` — **Variant of `ohlc`**
- **Controller:** `<mj-chart type="ohlc" style="ohlc" ...>`
- **Purpose:** Display open-high-low-close prices as vertical tick bars; preferred when many bars are shown at high density.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (time, bottom; value, start), `mj-chart-grid`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-crosshair`, `mj-chart-brush`, `mj-chart-annotation`, `mj-chart-data-table`
- **JSON shape:** Identical to Candlestick — same `candles` array.
- **SVG primitives:** `<line>` (vertical range line), `<line>` (left tick = open), `<line>` (right tick = close), `<g>` (per-bar group)
- **Orientation:** vertical only — same rationale as Candlestick.
- **Variants / modes:** `style="candle"` switches to Candlestick rendering; no separate renderer code required.
- **Phase:** P3
- **Notes:** Shares the `ohlc` renderer module entirely; `style` attribute selects the drawing subroutine. Positive/negative colouring uses the same token pair as the Candlestick.

---

### Volume Chart  *(trading volume bar chart)*
- **Renderer / `type`:** `volume` — **Primary renderer**
- **Controller:** `<mj-chart type="volume" ...>`
- **Purpose:** Display trading volume as vertical bars over a time axis; often paired below a Candlestick or OHLC chart.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (time, bottom; value, start), `mj-chart-grid`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "AAPL – Volume" },
    "candles": [
      { "t": "2025-01-02", "o": 185.2, "h": 189.4, "l": 184.1, "c": 188.7, "v": 52340000 }
    ]
  }
  ```
  The renderer reads only `t` and `v`; the full `candles` shape is reused so a single data source can feed both a price chart and a volume chart.
- **SVG primitives:** `<rect>` (volume bar per period), `<g>`, `<text>`
- **Orientation:** vertical (time → x, volume → y). Horizontal is `n/a` for conventional volume displays.
- **Variants / modes:** Bar colour may follow price direction (bullish/bearish from `o`/`c`) or use a uniform series colour, controlled via `color-mode="direction|series"`.
- **Phase:** P3
- **Notes:** Uses `time` scale + `linear` scale. Frequently composed below a candlestick/OHLC chart in a shared `<mj-dock-layout>` with a shared `mj-chart-brush`.

---

### Moving Average Chart  *(MA, SMA, EMA, WMA overlay)*
- **Renderer / `type`:** `ohlc` with `mj-chart-annotation` — **Variant of `ohlc`**
- **Controller:** `<mj-chart type="ohlc" ...>` (price) + `<mj-chart-annotation chart="..." kind="line-series" ...>` (MA overlay)
- **Purpose:** Overlay one or more smoothed price-trend lines (SMA, EMA, WMA) on top of a price chart to reveal direction and momentum.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (time, bottom; value, start), `mj-chart-grid`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-crosshair`, `mj-chart-annotation`, `mj-chart-data-table`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "AAPL with SMA 20 / EMA 50" },
    "candles": [
      { "t": "2025-01-02", "o": 185.2, "h": 189.4, "l": 184.1, "c": 188.7, "v": 52340000 }
    ],
    "overlays": [
      { "name": "SMA 20", "kind": "line", "values": [{ "t": "2025-01-02", "y": 186.1 }] },
      { "name": "EMA 50", "kind": "line", "values": [{ "t": "2025-01-02", "y": 184.9 }] }
    ]
  }
  ```
- **SVG primitives:** `<path>` (smoothed line per overlay via `svgdraw.js` curve builder), `<g>`, `<text>`
- **Orientation:** vertical only (matches the host price chart).
- **Variants / modes:** The `mj-chart-annotation` `kind="line-series"` attribute renders the overlay; multiple annotations can be stacked for SMA, EMA, WMA simultaneously.
- **Phase:** P3
- **Notes:** MA computation (SMA, EMA, WMA) is done in the data layer before delivery to the chart; the chart renders pre-computed overlay values. This follows the plan's principle that the renderer is a pure drawing function. The `overlays` array is an extension field in the `candles`-family envelope; unrecognised fields are ignored by chart types that do not use them.

---

### Bollinger Bands Chart  *(Keltner channels, price envelope)*
- **Renderer / `type`:** `ohlc` with `mj-chart-annotation` — **Variant of `ohlc`**
- **Controller:** `<mj-chart type="ohlc" ...>` + `<mj-chart-annotation chart="..." kind="band" ...>`
- **Purpose:** Overlay an upper band, a moving-average midline, and a lower band on a price chart to visualise volatility and potential reversal zones.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (time, bottom; value, start), `mj-chart-grid`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-crosshair`, `mj-chart-annotation`, `mj-chart-data-table`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "AAPL – Bollinger Bands (20, 2)" },
    "candles": [
      { "t": "2025-01-02", "o": 185.2, "h": 189.4, "l": 184.1, "c": 188.7, "v": 52340000 }
    ],
    "overlays": [
      {
        "name": "BB Upper", "kind": "band",
        "upper": [{ "t": "2025-01-02", "y": 192.4 }],
        "mid":   [{ "t": "2025-01-02", "y": 186.1 }],
        "lower": [{ "t": "2025-01-02", "y": 179.8 }]
      }
    ]
  }
  ```
- **SVG primitives:** `<path>` (filled band area between upper/lower using `svgdraw.js` area builder), `<path>` (midline), `<g>`, `<text>`
- **Orientation:** vertical only.
- **Variants / modes:** `kind="band"` on `mj-chart-annotation` renders a filled envelope; the same annotation kind covers Keltner channels and Donchian channels by supplying different computed values.
- **Phase:** P3
- **Notes:** Like Moving Average, band values are pre-computed by the data layer. The filled band is rendered at reduced opacity using `--mj-chart-band-fill-opacity` token. The renderer reuses the `area` path builder from `svgdraw.js`.

---

### Waterfall Chart  *(bridge chart, cascade chart)*
- **Renderer / `type`:** `waterfall` — **Primary renderer**
- **Controller:** `<mj-chart type="waterfall" ...>`
- **Purpose:** Show cumulative effect of sequential positive and negative contributions, revealing how an initial value reaches a final value through a series of incremental changes.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (category, bottom; value, start), `mj-chart-grid`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-value-labels`, `mj-chart-data-table`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Q4 P&L Bridge", "orientation": "vertical" },
    "series": [
      {
        "name": "P&L",
        "values": [
          { "label": "Opening",  "value": 1200, "kind": "total" },
          { "label": "Revenue",  "value": 400,  "kind": "positive" },
          { "label": "COGS",     "value": -150, "kind": "negative" },
          { "label": "OpEx",     "value": -200, "kind": "negative" },
          { "label": "Closing",  "value": 1250, "kind": "total" }
        ]
      }
    ]
  }
  ```
  `kind` values: `"positive"` (gain), `"negative"` (loss), `"total"` (absolute bar floating from zero).
- **SVG primitives:** `<rect>` (each bar, floating at computed y-offset), `<line>` (connector line between bars), `<text>` (value labels), `<g>`
- **Orientation:** `vertical` (categories → x, values → y) and `horizontal` (categories → y, values → x).
- **Variants / modes:** None — the `kind` field inside values drives bar colour (positive/negative/total) without needing a separate renderer.
- **Phase:** P2
- **Notes:** Uses `band` scale on the category axis and `linear` scale on the value axis. The renderer tracks a running cumulative total to position each floating bar. Total bars always originate from y=0. Connector lines are drawn between the top or bottom of adjacent bars.

---

### Budget vs Actual Chart  *(plan vs actual, variance chart)*
- **Renderer / `type`:** `bar` — **Variant of `bar`**
- **Controller:** `<mj-chart type="bar" group="cluster" ...>`
- **Purpose:** Compare planned budget figures against actual results to highlight over- and under-performance across categories or time periods.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (category, bottom; value, start), `mj-chart-grid`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-value-labels`, `mj-chart-annotation`, `mj-chart-data-table`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "2025 Budget vs Actual", "orientation": "vertical" },
    "categories": ["Q1", "Q2", "Q3", "Q4"],
    "series": [
      { "name": "Budget", "values": [300, 320, 290, 350] },
      { "name": "Actual", "values": [280, 335, 275, 360] }
    ]
  }
  ```
- **SVG primitives:** `<rect>` (clustered bars), `<text>` (labels), `<g>`
- **Orientation:** `vertical` and `horizontal`.
- **Variants / modes:** Uses the `bar` renderer with `group="cluster"`. An optional variance sub-chart showing the delta (`actual - budget`) may be added as a second `mj-chart` controller sharing the same category axis, using the `bar` renderer with a diverging color scale.
- **Phase:** P1
- **Notes:** No renderer code beyond the standard `bar` renderer is needed. The "variance" interpretation is a data-layer concern. `mj-chart-annotation` may be used to add a reference line at zero variance.

---

### Break-Even Chart  *(cost-volume-profit chart, CVP chart)*
- **Renderer / `type`:** `line` — **Variant of `line`**
- **Controller:** `<mj-chart type="line" ...>`
- **Purpose:** Plot fixed costs, total costs, and total revenue as lines against production or sales volume to reveal the break-even point and profit/loss zones.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (value/quantity, bottom; value/currency, start), `mj-chart-grid`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-crosshair`, `mj-chart-annotation`, `mj-chart-data-table`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Break-Even Analysis" },
    "series": [
      { "name": "Fixed Costs",  "points": [{ "x": 0, "y": 5000 }, { "x": 1000, "y": 5000 }] },
      { "name": "Total Costs",  "points": [{ "x": 0, "y": 5000 }, { "x": 1000, "y": 12000 }] },
      { "name": "Revenue",      "points": [{ "x": 0, "y": 0 },    { "x": 1000, "y": 15000 }] }
    ]
  }
  ```
  Uses the XY/relationship `points` shape from the plan §3.4.
- **SVG primitives:** `<path>` (line per series), `<circle>` (intersection marker at break-even), `<text>` (zone labels), `<g>`
- **Orientation:** `vertical` (quantity → x, currency → y). Horizontal is `n/a` — break-even charts have a conventional axis orientation.
- **Variants / modes:** Uses the standard `line` renderer. The break-even intersection point and profit/loss zone shading are added via `mj-chart-annotation` (`kind="point"` for the intersection, `kind="band"` for zone fills).
- **Phase:** P1
- **Notes:** Both axes are `linear` scales. The intersection point calculation is a data-layer responsibility; the chart receives it as an annotation coordinate.

---

### Tornado Chart  *(butterfly chart, sensitivity chart)*
- **Renderer / `type`:** `tornado` — **Primary renderer**
- **Controller:** `<mj-chart type="tornado" ...>`
- **Purpose:** Rank variables by their impact on an outcome, showing positive and negative sensitivity ranges as horizontal diverging bars sorted by magnitude.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (value, bottom; category, start), `mj-chart-grid`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-value-labels`, `mj-chart-annotation`, `mj-chart-data-table`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "NPV Sensitivity Analysis" },
    "baseline": 1200,
    "series": [
      {
        "name": "Sensitivity",
        "values": [
          { "label": "Discount Rate", "low": 950,  "high": 1480 },
          { "label": "Unit Price",    "low": 1050, "high": 1390 },
          { "label": "Volume",        "low": 1100, "high": 1340 }
        ]
      }
    ]
  }
  ```
  `baseline` is the central reference value; `low`/`high` define the extent of each bar on either side.
- **SVG primitives:** `<rect>` (left/negative bar), `<rect>` (right/positive bar), `<line>` (centre baseline), `<text>` (labels), `<g>`
- **Orientation:** `horizontal` only — the defining characteristic of a tornado chart is horizontal diverging bars sorted top-to-bottom by spread magnitude.
- **Variants / modes:** `style="butterfly"` renders the two bars symmetrically mirrored around the centre axis (demographic pyramid style) when `low`/`high` are magnitudes rather than absolute values.
- **Phase:** P2
- **Notes:** Uses `linear` scale on the value axis (diverging, centred on `baseline`), and `band` scale on the category axis. The renderer sorts rows by `(high - low)` descending before drawing so that the widest bar is always at the top. The centre baseline is drawn via `mj-chart-annotation kind="line"`.

---

### Contribution Margin Chart  *(revenue waterfall, cost-structure chart)*
- **Renderer / `type`:** `waterfall` — **Variant of `waterfall`**
- **Controller:** `<mj-chart type="waterfall" ...>`
- **Purpose:** Decompose revenue into variable costs, contribution margin, fixed costs, and operating profit to reveal cost structure and profitability levers.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (category, bottom; value, start), `mj-chart-grid`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-value-labels`, `mj-chart-data-table`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Contribution Margin – FY 2025", "orientation": "vertical" },
    "series": [
      {
        "name": "P&L",
        "values": [
          { "label": "Revenue",              "value": 5000, "kind": "total" },
          { "label": "Variable Costs",       "value": -2000,"kind": "negative" },
          { "label": "Contribution Margin",  "value": 3000, "kind": "total" },
          { "label": "Fixed Costs",          "value": -1200,"kind": "negative" },
          { "label": "Operating Profit",     "value": 1800, "kind": "total" }
        ]
      }
    ]
  }
  ```
- **SVG primitives:** `<rect>`, `<line>`, `<text>`, `<g>` — identical to Waterfall.
- **Orientation:** `vertical` and `horizontal`.
- **Variants / modes:** Satisfied entirely by the `waterfall` renderer with appropriate `kind` labels; no additional renderer code.
- **Phase:** P2
- **Notes:** This is a semantic variant of the Waterfall chart — same renderer, same JSON shape, different business labelling convention. The `waterfall` renderer does not need to distinguish the two; the data layer supplies the correct `kind` values.
