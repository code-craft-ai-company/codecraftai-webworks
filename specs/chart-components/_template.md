# <Category Name>

> Catalog of chart types in this category for the automojo-webworks SVG chart
> library. Architecture, the coordinated-element model, the part components,
> the JSON contract, and phasing are defined in `../../chart-components-plan.md`
> and are not repeated here.

Each entry uses this format:

### <Chart name>  *(synonyms / alternate names)*
- **Renderer / `type`:** `<key>` — **Primary renderer** | **Variant of `<key>`**
- **Controller:** `<mj-chart type="<key>" ...>`
- **Purpose:** one line — what this chart is best for.
- **Decomposition:** the part components it uses (`mj-chart-plot`,
  `mj-chart-axis` x N, `mj-chart-legend`, `mj-chart-title`,
  `mj-chart-tooltip`, `mj-chart-grid`, `mj-chart-data-table`,
  `mj-chart-annotation`, …). List only the parts that apply.
- **JSON shape:** the concrete data shape this chart consumes, as a compact
  JSON snippet using the common envelope or a documented family-specific
  shape from the plan §3.4.
- **SVG primitives:** the SVG elements the renderer emits (`<rect>`, `<path>`,
  `<circle>`, `<line>`, `<polygon>`, `<text>`, `<g>` …).
- **Orientation:** `horizontal` / `vertical` support, or `n/a` when the chart
  has no meaningful orientation.
- **Variants / modes:** related catalog names satisfied by an attribute mode
  of this renderer, if any.
- **Phase:** P0–P5 per the plan's phasing.
- **Notes:** anything implementation-relevant (scales used, layout engine,
  accessibility specifics, reuse of another renderer).

Synonyms and mode-variants are consolidated onto a single **Primary renderer**
wherever the catalog list repeats a chart or lists a mode of another chart.
