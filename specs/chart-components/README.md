# Chart Components Catalog

The per-category catalog for the codecraftai-webworks SVG chart library. The
architecture — the coordinated-element model, the `<mj-chart>` controller, the
title / legend / data-table parts, the JSON data contract, the SVG drawing model, orientation,
docking/anchoring, the `charts/` directory layout, phasing, and the definition
of done — is in **`../../chart-components-plan.md`**.

Each entry records the renderer/`type` key, whether it is a Primary renderer
or a variant, its JSON shape, the SVG primitives it emits, orientation
support, the events it emits, and its implementation phase. Entry format:
`_template.md`.

Synonyms and mode-variants are consolidated onto a small set of **Primary
renderers** — the ~150 catalogued chart names map to roughly 80 renderers.

## Categories

1. [Comparison charts](01-comparison.md)
2. [Trend & time-series charts](02-trend-time-series.md)
3. [Distribution charts](03-distribution.md)
4. [Relationship & correlation charts](04-relationship-correlation.md)
5. [Part-to-whole charts](05-part-to-whole.md)
6. [Ranking charts](06-ranking.md)
7. [Geographic & map charts](07-geographic.md)
8. [Flow & process charts](08-flow-process.md)
9. [Hierarchical charts](09-hierarchical.md)
10. [Statistical & analytical charts](10-statistical-analytical.md)
11. [Financial charts](11-financial.md)
12. [Project & schedule charts](12-project-schedule.md)
13. [Scientific & technical charts](13-scientific-technical.md)
14. [UX, product & business charts](14-ux-product-business.md)
15. [Text & categorical charts](15-text-categorical.md)
16. [Tables with visual encoding](16-tables-visual-encoding.md)
17. [Less common & advanced charts](17-advanced.md)

## How a chart is built

`<mj-chart>` draws every chart type whole — plot, axes, gridlines, marks,
value labels and reference lines in one SVG — and shows a tooltip with the
label of the hovered or keyboard-focused mark. A title, a legend and a visible
data table are optional parts that can be placed anywhere and docked:

```html
<mj-chart id="c1" type="bar" src="/data/sales.json" orientation="vertical"></mj-chart>

<mj-chart-title      chart="c1">Quarterly Sales</mj-chart-title>
<mj-chart-legend     chart="c1" orientation="horizontal"></mj-chart-legend>
<mj-chart-data-table chart="c1"></mj-chart-data-table>
```

Plot, axis, grid, tooltip, crosshair, brush, annotation, series and
value-label part elements were planned once and dropped (plan §3.3).

All chart code lives under `static/javascript/charts/` — see the plan §4.
