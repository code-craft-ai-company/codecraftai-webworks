# Chart Components Implementation Plan

> **Status.** The library is built. This plan is kept as its architecture
> record and is updated where the shipped design differs: `<mj-chart>` draws
> each chart whole (plot, axes, gridlines, marks, value labels, reference
> lines) and shows a tooltip for the hovered or focused mark; the separate part
> elements are `<mj-chart-title>`, `<mj-chart-legend>` and
> `<mj-chart-data-table>` only. The other planned parts were dropped (§3.3).
> The controller is specified in `specs/web-components/chart.md`.

## 1. Purpose & Scope

This plan defines the architecture and delivery approach for a comprehensive
SVG charting library for `codecraftai-webworks`. It covers ~150 chart types
across 17 categories (see `specs/chart-components/` for the full catalog).

Every chart is built from **coordinated web components** — a chart is not one
monolithic element but a controller plus independently-placeable parts. All
chart code lives under a new `charts/` directory, separate from `components/`.

This plan satisfies these stated requirements:

- Charts receive their data as **JSON**.
- Charts are drawn with **SVG**.
- A chart's distinct parts are **separate web components** wherever it is
  sensible: title, legend and data table (the drawing itself — plot, axes,
  gridlines, marks — is one SVG drawn by the controller; see §3.3).
- Parts are **coordinated elements** so they can be placed independently
  anywhere in the consumer's HTML.
- Parts render **vertically or horizontally** wherever orientation is
  meaningful.
- All chart components support **docking and anchoring**.
- All chart components and their parts live under **`charts/`**, not
  `components/`.

## 2. Relationship to the existing library

Chart components are native Custom Elements built on the same foundation as
the `mj-*` component library:

- They extend **`MjElement`** (`core/mjelement.js`) and therefore inherit
  Shadow DOM, theming via design tokens, the `dock`/`anchor` attributes, the
  context menu, lifecycle, and the `emit` event helper for free.
- They register through the idempotent **`registry.js`**.
- They reuse **`overlay.js`** (tooltip/popup positioning) and
  **`anchoring.js`** (docking).

The 13 project/SCM chart components currently under `components/`
(`mjbranchgraph.js`, `mjganttchart.js`, …) and the media charts (`mjchart.js`,
`mjgauge.js`, `mjsparkline.js`, `mjdiagram.js`) are **superseded** by this
architecture. Phase 5 migrates them: their tags are preserved as thin
compatibility wrappers over the new coordinated charts, then the old files are
removed.

## 3. Architecture

### 3.1 The coordinated-element model

A chart is a **family of elements**, not a single element. One **controller**
holds the data and the computed model; **part** elements draw or present
pieces of the chart and may be placed anywhere in the document.

```
<mj-chart id="sales" type="bar" src="/data/sales.json" orientation="vertical"></mj-chart>

<mj-chart-title      chart="sales">Quarterly Sales</mj-chart-title>
<mj-chart-legend     chart="sales" orientation="horizontal"></mj-chart-legend>
<mj-chart-data-table chart="sales"></mj-chart-data-table>
```

Each part finds its controller by:

1. the **`chart` attribute** — the controller's `id` (primary; lets a part
   live anywhere in the DOM, even in a different subtree); or
2. the **nearest ancestor `<mj-chart>`** — a convenience when parts are
   nested inside the controller.

Coordination protocol:

- On `connectedCallback`, a part resolves its controller and calls
  `controller.registerPart(this)`.
- The controller keeps a registry of parts and a single **chart model**
  (Section 3.4).
- When the data or the hidden series change, the controller calls each
  part's `applyModel(model, ...)` after it draws.
- On `disconnectedCallback`, a part calls `controller.unregisterPart(this)`.

Because parts are ordinary elements extending `MjElement`, they can be docked
(`dock="top|bottom|start|end|fill"`) inside an `<mj-dock-layout>` and anchored
(`anchor="top-end"`, …) inside any positioned container — fulfilling the
docking/anchoring requirement with no extra code.

### 3.2 The chart controller — `<mj-chart>`

Responsibilities:

- **Ingest data** (Section 3.4) and parse it into the normalized model.
- **Compute scales** (Section 3.6) from data domains and its drawing box.
- **Maintain the part registry** and broadcast model updates.
- **Draw the chart**: the renderer of its `type` draws the whole drawing —
  plot, axes, gridlines, marks, value labels and reference lines — into one
  SVG. Title, legend and data table are optional bound parts (§3.3).
- **Tooltip**: the hovered or keyboard-focused mark shows its label in a
  tooltip above it (`no-tooltip` turns it off).

Key attributes / properties:

| Name | Type | Purpose |
|------|------|---------|
| `type` | attr | The chart kind / renderer key, e.g. `bar`, `line`, `scatter`. |
| `data` | property | The chart data as a JSON object. |
| `src` | attr | URL to fetch JSON data from. |
| `orientation` | attr | `horizontal` \| `vertical` default for parts. |
| `theme` | attr | Token theme scope (inherited from `MjElement`). |

Events (as shipped; `specs/web-components/chart.md` §8): `mj-chart-render`,
`mj-chart-empty`, `mj-chart-error`, `mj-chart-series-toggle` and
`mj-chart-connect` from the controller, and the interaction events of each
chart type. Each type keeps its own event names and detail shapes
(`mj-chart-bar-click`, `mj-chart-slice-click`, `mj-chart-word-click`, ...),
listed on its chart-type page; there is no common `mj-chart-point` /
`mj-chart-select` event across types, by decision (WW-1660, WW-1269). An
earlier draft of this plan proposed `mj-chart-ready`, `mj-chart-model` and
a common `mj-chart-point`; they were not built.

### 3.3 Chart part components

The elements of the library — each a web component under `charts/`, each
extending `MjElement`, each dockable/anchorable:

| Tag | Role | Orientation-aware |
|-----|------|-------------------|
| `<mj-chart>` | Controller; draws the whole chart (plot, axes, gridlines, marks, value labels, reference lines) and shows the tooltip of the hovered or focused mark. | yes (sets default) |
| `<mj-chart-title>` | Title / subtitle text block. | n/a |
| `<mj-chart-legend>` | Series legend; interactive series toggle. | yes (row vs column) |
| `<mj-chart-data-table>` | A visible table of the chart's data (the controller always keeps a visually hidden one). | n/a |

Any chart can bind the three parts.

**Dropped parts.** The first version of this plan also proposed
`<mj-chart-plot>`, `<mj-chart-axis>`, `<mj-chart-grid>`, `<mj-chart-tooltip>`,
`<mj-chart-crosshair>`, `<mj-chart-brush>`, `<mj-chart-annotation>`,
`<mj-chart-series>` and `<mj-chart-value-labels>`. They were not built and
will not be: the renderers draw axes, gridlines, value labels and reference
lines inside the one drawing, the tooltip is the controller's, and series
options come with the JSON data. Crosshair and brush (range selection) are not
available. The catalog entries no longer list a decomposition into parts.

### 3.4 JSON data contract

Charts accept data three ways, in priority order:

1. The **`data` property** — a JSON object set from script.
2. The **`src` attribute** — a URL the controller fetches as JSON.
3. An inline **`<script type="application/json" slot="data">`** child.

All data uses a common envelope; chart-family-specific fields extend it. The
controller validates against a per-`type` schema and emits `mj-chart-error`
with a clear message on mismatch.

**Common envelope**

```json
{
  "meta":   { "title": "string", "orientation": "vertical|horizontal" },
  "categories": ["A", "B", "C"],
  "series": [
    { "name": "2025", "values": [10, 20, 15], "color": "optional" }
  ]
}
```

**Family-specific shapes** (full schemas in the catalog):

- *XY / relationship*: `series[].points: [{ "x": n, "y": n, "size": n }]`.
- *Hierarchical*: `root: { "name": s, "value": n, "children": [ … ] }`.
- *Flow / network*: `nodes: [{ "id" }]`, `links: [{ "source", "target", "value" }]`.
- *Geographic*: `regions: [{ "id", "value" }]` plus a `topology`/`geojson` ref.
- *Statistical*: per-group `{ "q1", "median", "q3", "min", "max", "outliers" }`.
- *Financial*: `candles: [{ "t", "o", "h", "l", "c", "v" }]`.
- *Distribution*: raw `samples: [n …]` or pre-binned `bins: [{ "x0","x1","count" }]`.

The JSON shapes are documented per chart so a data layer can target them
directly.

### 3.5 SVG drawing model

- Every drawing part renders **one `<svg>`** in its shadow root, sized to the
  element (`width:100%; height:100%`), with a `viewBox` matching the measured
  pixel box (or a logical space the renderer chooses).
- Drawing uses only **SVG primitives** — `<rect>`, `<line>`, `<path>`,
  `<circle>`, `<polygon>`, `<text>`, `<g>`. No `<canvas>`, no external
  charting library.
- A shared **`svgdraw.js`** helper supplies path builders (line/area/arc/
  curve), tick generation, label placement, and number formatting.
- **Renderers** are pure functions keyed by chart `type`:
  `render(model, surface) -> SVG fragment`. The plot part dispatches on
  `type`. Renderers live in `charts/core/renderers/` and are individually
  importable so a page only loads the renderers it uses.
- All visual values come from **design tokens** (`--mj-*`), including a
  categorical series-color ramp; charts are themeable and never encode meaning
  by color alone (marks also vary by shape/pattern/label where needed).

### 3.6 Scales & orientation

- **Scales** (`charts/core/scales.js`): `linear`, `log`, `time`, `band`
  (categorical), `point`, `ordinal-color`, `sqrt` (for bubble radius). A scale
  maps a data **domain** to a pixel **range**.
- The controller owns the scale objects. The plot reports its pixel box →
  controller sets each scale's range → all parts (plot, axes, grid) read the
  **same** scale, so independently-placed parts stay aligned.
- **Orientation**: `orientation="horizontal|vertical"` on the controller (and
  overridable per part). For Cartesian charts the renderer swaps which axis is
  the category axis and which is the value axis (e.g. a bar chart is a column
  chart rotated). Axes and legends also honor `orientation` (a legend lays out
  as a row or a column). For chart types with no meaningful orientation (pie,
  treemap, network, geographic) the attribute is ignored — "where possible".

### 3.7 Docking & anchoring

No chart-specific work is required: every chart element extends `MjElement`,
which already implements `dock` and `anchor` (see
`web-component-development-plan.md` §3 and `core/anchoring.js`).

Typical dashboard layout:

```html
<mj-dock-layout>
  <mj-chart-title  chart="c1" dock="top"></mj-chart-title>
  <mj-chart-legend chart="c1" dock="end" orientation="vertical"></mj-chart-legend>
  <mj-chart id="c1" type="bar" dock="fill"></mj-chart>
</mj-dock-layout>
```

### 3.8 Accessibility, theming, events

- The controller always builds a **data-table model** and keeps it as a
  visually hidden `<table>` after the drawing; `<mj-chart-data-table>` shows it.
  Focusable marks carry `role="img"` and an `aria-label`.
- Keyboard: focusable marks/legend items; arrow-key traversal of data points;
  `Enter`/`Space` to select; the focused mark shows its tooltip.
- Interaction events are namespaced `mj-chart-*` and bubble from parts through
  the controller.
- Honors `prefers-reduced-motion` (no entry animation) and `forced-colors`.

## 4. Directory layout

All chart code lives under `charts/`, never `components/`:

```
static/javascript/charts/
  index.js                 barrel: imports + registers all chart components
  mjchart.js                <mj-chart>  controller (drawing and tooltip)
  mjchartlegend.js          <mj-chart-legend>
  mjcharttitle.js           <mj-chart-title>
  mjchartdatatable.js       <mj-chart-data-table>
  core/
    chartmodel.js           normalized model + table model builder
    chartregistry.js        controller<->part coordination helpers
    jsonsource.js           data ingestion (property / src / inline JSON)
    scales.js               scale constructors
    svgdraw.js              SVG primitive + path/tick/format helpers
    schema.js               per-type JSON schema validation
    renderers/
      bar.js  line.js  area.js  scatter.js  pie.js  ...  (one per renderer)
```

Component file naming follows the repo convention: file named after the
class, all lowercase, no underscores (`MjChartLegend` → `mjchartlegend.js`).

## 5. Shared chart foundation (build first)

These modules in `charts/core/` are built before any chart and reused by all:

- **`jsonsource.js`** — resolve and parse data from property / `src` / inline.
- **`schema.js`** — validate parsed data per chart `type`.
- **`chartmodel.js`** — normalize data into the model; build the table model.
- **`scales.js`** — the scale constructors.
- **`svgdraw.js`** — SVG primitive builders, tick/label/format utilities,
  the categorical color ramp from tokens.
- **`chartregistry.js`** — controller/part resolution (`chart` attr + ancestry),
  registration, model broadcast.
- The **part base** behavior — a `ChartPart` mixin over `MjElement` that does
  controller resolution, registration, and `applyModel` plumbing so every part
  component stays thin.

## 6. Chart catalog

The full per-chart catalog is in **`specs/chart-components/`**, one file per
category. Each entry records: the renderer/`type` key, synonym/variant
consolidation, purpose, **JSON shape**, **SVG primitives**, **orientation**
support, **events** and **phase**.

Categories:

1. Comparison charts
2. Trend & time-series charts
3. Distribution charts
4. Relationship & correlation charts
5. Part-to-whole charts
6. Ranking charts
7. Geographic & map charts
8. Flow & process charts
9. Hierarchical charts
10. Statistical & analytical charts
11. Financial charts
12. Project & schedule charts
13. Scientific & technical charts
14. UX, product & business charts
15. Text & categorical charts
16. Tables with visual encoding
17. Less common / advanced charts

**Consolidation policy** — many listed charts are the same renderer in a
different mode and must not become separate code:

- Bar / Column = `bar` renderer with `orientation`.
- Grouped / Stacked / 100%-stacked bar = `bar` renderer with
  `group="cluster|stack|stack100"`.
- Pie / Donut = `pie` renderer with an `inner-radius`.
- Candlestick / OHLC = `ohlc` renderer with a `style`.
- Area / Stacked / 100%-stacked area = `area` renderer with a stack mode.
- Treemap / Icicle / Sunburst / Circle-packing = one hierarchical layout
  engine with a `layout` mode.

Each catalog entry marks whether it is a **Primary renderer** or a **variant**
of one. The result is ~150 catalog names mapping to a much smaller set of
renderers, each drawn by `<mj-chart>` with the optional parts of §3.3.

## 7. Implementation phasing

**Phase 0 — Foundation.** Everything in §5, the `<mj-chart>` controller, and
the part base. A demo harness.

**Phase 1 — Parts & common charts.** `<mj-chart-legend>`, `<mj-chart-title>`,
`<mj-chart-data-table>`. Renderers: bar/column (+ group/
stack modes), line/multi-line, area (+ stack modes), step, scatter, sparkline.

**Phase 2 — Part-to-whole, distribution, ranking.** Pie/donut, treemap,
sunburst, waffle, histogram, density, box plot, violin, sorted bar, Pareto,
lollipop, dot plot, bullet, waterfall.

**Phase 3 — Relationship, statistical, financial, schedule.** Bubble,
hexbin, heatmap, correlation matrix, error bars / confidence intervals,
control/run charts, ROC/PR curves, candlestick/OHLC, volume, moving-average
overlays, Gantt, timeline, burndown/burnup, cumulative flow.

**Phase 4 — Flow, hierarchy, geographic, radial, scientific.** Sankey/
alluvial, chord, network/arc, funnel, dendrogram/org chart/circle-packing,
choropleth/symbol/flow maps, radar/polar/wind-rose/Nightingale, contour/
surface/vector-field and the scientific set.

**Phase 5 — Advanced, UX/business, tables, migration.** Streamgraph, horizon,
bump, UpSet, Voronoi, beeswarm, calendar heatmap; KPI/gauge/cohort/funnel
dashboards; visual-encoding tables; and migration of the existing
`components/` chart elements onto this architecture as compatibility wrappers.

Phasing rule: a chart is not started until every part and renderer it composes
exists and is tested.

## 8. Testing strategy

- **Foundation unit tests** — scales, schema validation, model normalization,
  SVG path/tick helpers.
- **Per-chart rendering tests** — given a known JSON input, assert the SVG
  contains the expected primitives (correct number of `<rect>`/`<path>` etc.)
  and that the data-table model matches.
- **Coordination tests** — independently-placed parts resolve their controller
  by `chart` id and by ancestry and follow every render.
- **Orientation tests** — horizontal vs vertical produce the swapped mapping.
- **Docking/anchoring tests** — chart parts inside `<mj-dock-layout>` lay out;
  `anchor` pins parts.
- **Accessibility tests** — data-table alternative present; marks/legend
  keyboard-operable; no color-only encoding.
- Charts are exercised on the `testcomponents` site with Playwright, following
  the same harness used by the component library.

## 9. Definition of done (per chart)

1. Receives data as JSON via `data` / `src` / inline, validated by schema.
2. Drawn entirely with SVG, styled only from `--mj-*` tokens.
3. Works with the title, legend and data-table parts, each an
   independently-placeable coordinated element, and shows the tooltip of the
   hovered or focused mark.
4. Renders horizontally and vertically where orientation is meaningful.
5. Every part supports `dock` and `anchor` (inherited from `MjElement`).
6. Provides the accessible data-table alternative and keyboard interaction.
7. Lives under `charts/`, registered through `charts/index.js`.
8. Rendering, coordination, orientation, and accessibility tests pass.
9. Documented with JSON shape and a usage example.
