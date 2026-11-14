# Financial Charts

> Catalog of chart types in this category for the codecraftai-webworks SVG chart
> library. Architecture, the coordinated-element model, the title / legend /
> data-table parts, the JSON contract, and phasing are defined in
> `../../chart-components-plan.md` and are not repeated here. `<mj-chart>` draws
> each type whole (plot, axes, gridlines, marks) and shows the tooltip of the
> hovered or focused mark; any chart can bind the three parts.

---

### Candlestick Chart  *(Japanese candlestick, OHLC candle)*
- **Renderer / `type`:** `candlestick` — **Variant of `ohlc`** (`ohlc.js` registers both keys)
- **Controller:** `<mj-chart type="candlestick" ...>` (same drawing as `<mj-chart type="ohlc" variant="candle" ...>`)
- **Purpose:** Visualise stock or asset price movement over time; body encodes open-to-close range, wicks encode high/low extremes.
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
- **SVG primitives:** `<rect>` (candle body — hollow when close ≥ open, filled when close < open), `<line>` (upper and lower wicks), `<g>` (per-candle group), `<text>` (axis labels)
- **Orientation:** vertical (time → x, price → y); horizontal layout is `n/a` — price candles have no conventional horizontal form.
- **Variants / modes:** The drawing follows the type key — `candlestick` draws bodies and wicks, `ohlc` draws tick bars — and `variant="ohlc" | "candle"` overrides it (`variant="candlestick"` reads as `candle`), so `type="candlestick" variant="ohlc"` draws the OHLC chart below.
- **Events:** `mj-chart-candle-click` `{ t, o, h, l, c, direction, count }` (each session; `t` is the session's first date, `direction` `rising` / `falling`, `count` the data rows merged into it); the same for every drawing `variant`.
- **Phase:** P3
- **Notes:** Uses `time` scale on the category axis and `linear` scale on the value axis. Bullish candles (close ≥ open) and bearish candles (close < open) are coloured from `--mj-color-success` / `--mj-color-danger` and are hollow / filled, so no meaning is encoded by color alone — tooltip and `aria-label` carry directional text. Volume is not drawn by this renderer; a separate `type="volume"` chart of the same data at the same width lines up with it (same session slots and margins). There is no zoom or brushing of the time window: when there are more candles than 3 px slots, consecutive candles are merged into one session.

---

### OHLC Chart  *(open-high-low-close bar chart, bar chart)*
- **Renderer / `type`:** `ohlc` — **Primary renderer** (`ohlc.js`, shared with `candlestick`)
- **Controller:** `<mj-chart type="ohlc" ...>` (tick bars are the `ohlc` key's default drawing)
- **Purpose:** Display open-high-low-close prices as vertical tick bars; preferred when many bars are shown at high density.
- **JSON shape:** Identical to Candlestick — same `candles` array.
- **SVG primitives:** `<line>` (vertical range line), `<line>` (left tick = open), `<line>` (right tick = close), `<g>` (per-bar group)
- **Orientation:** vertical only — same rationale as Candlestick.
- **Variants / modes:** `variant="candle"` switches to Candlestick rendering (as `type="candlestick"` does); `variant="ohlc"` forces tick bars on a `candlestick` chart; no separate renderer code required.
- **Events:** `mj-chart-candle-click` `{ t, o, h, l, c, direction, count }` (each session; `t` is the session's first date, `direction` `rising` / `falling`, `count` the data rows merged into it); the same for every drawing `variant`.
- **Phase:** P3
- **Notes:** Shares the `ohlc` renderer module entirely; the type key, overridden by the `variant` attribute, selects the drawing subroutine. Positive/negative colouring uses the same token pair as the Candlestick.

---

### Volume Chart  *(trading volume bar chart)*
- **Renderer / `type`:** `volume` — **Primary renderer**
- **Controller:** `<mj-chart type="volume" ...>`
- **Purpose:** Display trading volume as vertical bars over a time axis; often paired below a Candlestick or OHLC chart.
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
- **Events:** `mj-chart-bar-click` `{ date, volume, open, close, count }` (each session bar).
- **Phase:** P3
- **Notes:** Uses `time` scale + `linear` scale. Frequently placed below a candlestick/OHLC chart of the same data (e.g. in a shared `<mj-dock-layout>`); at the same width its bars line up with the candles, because both renderers use the same session slots and margins. There is no shared brush or zoom.

---

### Moving Average Chart  *(MA, SMA, EMA, WMA overlay)*
- **Renderer / `type`:** not implemented — `ohlc.js` draws the price candles and ignores `overlays`, so no moving-average line is drawn
- **Controller:** none yet (`<mj-chart type="ohlc" ...>` draws the price chart without the overlay)
- **Purpose:** Overlay one or more smoothed price-trend lines (SMA, EMA, WMA) on top of a price chart to reveal direction and momentum.
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
- **Variants / modes:** not implemented: with no overlay element, the `ohlc` renderer itself would have to draw one line per `overlays` entry with `"kind": "line"` (SMA, EMA and WMA together); it reads no `overlays` field today.
- **Events:** `mj-chart-candle-click` `{ t, o, h, l, c, direction, count }` from the price chart (each session); the overlay lines are not drawn (not implemented).
- **Phase:** P3
- **Notes:** MA computation (SMA, EMA, WMA) is done in the data layer before delivery to the chart; the chart renders pre-computed overlay values. This follows the plan's principle that the renderer is a pure drawing function. The `overlays` array is an extension field in the `candles`-family envelope; unrecognised fields are ignored by chart types that do not use them.

---

### Bollinger Bands Chart  *(Keltner channels, price envelope)*
- **Renderer / `type`:** not implemented — `ohlc.js` draws the price candles and ignores `overlays`, so no band is drawn
- **Controller:** none yet (`<mj-chart type="ohlc" ...>` draws the price chart without the band)
- **Purpose:** Overlay an upper band, a moving-average midline, and a lower band on a price chart to visualise volatility and potential reversal zones.
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
- **Variants / modes:** not implemented: with no overlay element, the `ohlc` renderer itself would have to draw an `overlays` entry with `"kind": "band"` as a filled envelope (the same kind would cover Keltner and Donchian channels with different computed values); it reads no `overlays` field today.
- **Events:** `mj-chart-candle-click` `{ t, o, h, l, c, direction, count }` from the price chart (each session); the band is not drawn (not implemented).
- **Phase:** P3
- **Notes:** Like Moving Average, band values are pre-computed by the data layer. The filled band is rendered at reduced opacity using `--mj-chart-band-fill-opacity` token. The renderer reuses the `area` path builder from `svgdraw.js`.

---

### Waterfall Chart  *(bridge chart, cascade chart)*
- **Renderer / `type`:** `waterfall` — **Primary renderer**
- **Controller:** `<mj-chart type="waterfall" ...>`
- **Purpose:** Show cumulative effect of sequential positive and negative contributions, revealing how an initial value reaches a final value through a series of incremental changes.
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
- **Events:** `mj-chart-bar-click` `{ category, index, value, kind, runningTotal }` (each bar).
- **Phase:** P2
- **Notes:** Uses `band` scale on the category axis and `linear` scale on the value axis. The renderer tracks a running cumulative total to position each floating bar. Total bars always originate from y=0. Connector lines are drawn between the top or bottom of adjacent bars.

---

### Budget vs Actual Chart  *(plan vs actual, variance chart)*
- **Renderer / `type`:** `bar` — **Variant of `bar`**
- **Controller:** `<mj-chart type="bar" group="cluster" ...>`
- **Purpose:** Compare planned budget figures against actual results to highlight over- and under-performance across categories or time periods.
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
- **Events:** `mj-chart-bar-click` `{ series, category, value }` (each bar).
- **Phase:** P1
- **Notes:** No renderer code beyond the standard `bar` renderer is needed. The "variance" interpretation is a data-layer concern. The `bar` renderer always draws the zero baseline (its value domain always includes zero), which is the zero-variance line of a variance chart; no other reference line can be added.

---

### Break-Even Chart  *(cost-volume-profit chart, CVP chart)*
- **Renderer / `type`:** `line` — **Variant of `line`**
- **Controller:** `<mj-chart type="line" ...>`
- **Purpose:** Plot fixed costs, total costs, and total revenue as lines against production or sales volume to reveal the break-even point and profit/loss zones.
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
- **Variants / modes:** Uses the standard `line` renderer, which draws the lines only: it marks no break-even point and shades no profit/loss zones. The intersection can be given as a one-point series, which always gets a marker.
- **Events:** `mj-chart-line-click` `{ series, x, y }` (each point target).
- **Phase:** P1
- **Notes:** Both axes are `linear` scales. The intersection point calculation is a data-layer responsibility; the chart receives it as a one-point series.

---

### Tornado Chart  *(butterfly chart, sensitivity chart)*
- **Renderer / `type`:** `tornado` — **Primary renderer**
- **Controller:** `<mj-chart type="tornado" ...>`
- **Purpose:** Rank variables by their impact on an outcome, showing positive and negative sensitivity ranges as horizontal diverging bars sorted by magnitude.
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
- **Variants / modes:** `variant="butterfly"` treats `low` / `high` as magnitudes drawn to the left and right of `baseline` (population pyramid, two-sided comparison); rows keep the data order (no spread sort), values show as magnitudes on both sides, and the legend names default to "Left" / "Right" (`low_label` / `high_label` override them; tornado defaults are "Low input" / "High input").
- **Events:** `mj-chart-bar-click` `{ label, side, value, baseline }` (each bar; `side` is `low` or `high`, `value` as drawn — a magnitude with `variant="butterfly"`).
- **Phase:** P2
- **Notes:** Uses `linear` scale on the value axis (diverging, centred on `baseline`), and `band` scale on the category axis. Without `variant="butterfly"` the renderer sorts rows by `(high - low)` descending before drawing so that the widest bar is always at the top. The renderer draws the centre line at `baseline` itself, labelled "Base <value>" above the plot (unlabelled with `variant="butterfly"`).

---

### Contribution Margin Chart  *(revenue waterfall, cost-structure chart)*
- **Renderer / `type`:** `waterfall` — **Variant of `waterfall`**
- **Controller:** `<mj-chart type="waterfall" ...>`
- **Purpose:** Decompose revenue into variable costs, contribution margin, fixed costs, and operating profit to reveal cost structure and profitability levers.
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
- **Events:** `mj-chart-bar-click` `{ category, index, value, kind, runningTotal }` (each bar).
- **Phase:** P2
- **Notes:** This is a semantic variant of the Waterfall chart — same renderer, same JSON shape, different business labelling convention. The `waterfall` renderer does not need to distinguish the two; the data layer supplies the correct `kind` values.
