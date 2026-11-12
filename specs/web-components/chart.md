# Chart Spec

- **Tag:** `<mj-chart>`
- **Class / file:** `MjChart` / `charts/mjchart.js`
- **Category:** Media & visualization
- **Primary or Variant:** Primary
- **Synonyms covered:** Line chart, Bar chart, Column chart, Pie chart, Donut chart, Area chart, Scatter plot, Heatmap, and every other chart type of the chart catalog
- **Phase:** P3
- **Status:** Implemented. This spec summarizes the shipped controller in
  `charts/mjchart.js`. The architecture is in `chart-components-plan.md` (repository
  root), the per-type renderers, JSON shapes and options in
  [`../chart-components/`](../chart-components/README.md), and the coordinated part
  elements in their own specs:
  - [charttitle.md](charttitle.md) — `<mj-chart-title>`
  - [chartlegend.md](chartlegend.md) — `<mj-chart-legend>`
  - [chartdatatable.md](chartdatatable.md) — `<mj-chart-data-table>`

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

> **History.** An earlier version of this spec (Status: Planned) described an
> adapter-based chart (an external engine passed as `adapter`, `show-legend`,
> `show-table`, `aspect-ratio`, `color-scheme`, `loading` and `locale` attributes,
> `title` / `legend` / `empty` / `donut-center` slots, focusable data-table cells
> with `mj-chart-point-*` events). None of that shipped. The library draws SVG
> itself, and the title, legend and visible data table are separate part elements.

## 1. Purpose

`<mj-chart>` is the chart controller of the in-house SVG chart library. It reads
JSON data, builds a normalized model, sizes an SVG drawing surface, and calls the
renderer registered for its `type` (139 catalogued chart types, from bar, line and
pie to sankey, treemap, maps, gantt and word clouds; a page can register its own
with `registerRenderer`). It owns the accessible surface — the `figure` role and
name, a text description, a visually hidden data table, keyboard movement between
marks — and broadcasts its model to the coordinated part elements
(`<mj-chart-title>`, `<mj-chart-legend>`, `<mj-chart-data-table>`) bound to it.
No charting engine is bundled or required.

## 2. When to use / when not to use

**Use** for data visualizations in dashboards, reports and analytics pages where an
accessible, themed chart is needed, from simple comparisons to flow, hierarchy,
statistical, financial, scientific and geographic charts.

**Do not use** for a compact inline trend inside text or a table cell (use
`<mj-sparkline>`), for a single-value dial with its own form semantics (use
`<mj-gauge>`), for editable node/edge diagrams (use `<mj-diagram>`), or for the
project-management charts that have dedicated components (`<mj-burndown-chart>`,
`<mj-velocity-chart>`, ...).

`<mj-gantt-chart>`, `<mj-roadmap-chart>`, `<mj-milestone-timeline>` and
`<mj-dependency-graph>` are not separate implementations: each is this element
with its type fixed (`gantt`, `roadmap`, `milestone`, `dependency-graph`), its own
data shape and a toolbar / detail panel (§21). The chart types are canonical
(WW-1498).

## 3. Anatomy

- **Host** — `display: flex; flex-direction: column`; gets `role="figure"` unless
  the page set a role, and an `aria-label` (§13).
- **description (part)** — visually hidden `<p>` with the `description` text (or
  `meta.description`); hidden when there is none.
- **surface (part)** — the drawing area. It takes the host's block size when the
  page gives the host a height, else `--mj-chart-min-height` (§9). It holds either
  - **svg (part)** — the renderer's drawing, or
  - **message (part)** — a centered text with a second part name for its kind:
    `::part(message loading)`, `::part(message empty)`, `::part(message error)`.
- **default slot** — nested chart parts: `<mj-chart-title>` is drawn above the
  surface (`order: -1`), `<mj-chart-legend>` and `<mj-chart-data-table>` below it in
  source order. Any other light-DOM child (including the inline JSON `<script>`)
  is not displayed.
- **`empty` slot** — inside the empty message: page content shown instead of
  "No chart data supplied." while the data holds nothing to draw.
- **table (part)** — the visually hidden accessible data table (§13).

## 4. Variants & modes

| Mode | Selected by | Behavior |
|------|-------------|----------|
| Chart type | `type="<key>"` (default `bar`) | The renderer registered for that key draws the chart. The keys, their JSON shapes and their options are listed per category in `../chart-components/` and on the xtest site's chart-type pages (`/chart-type/<type>`). An unknown key shows the error message |
| Orientation | `orientation="vertical\|horizontal"` | Passed to the renderer; default `meta.orientation`, then the orientation the type registered |
| Drawing variant | `variant="<name>"` | What renderers read as their "style" option (stacked, grouped, smooth, ...; per type). The `style` attribute stays CSS |
| Renderer options | any other attribute | Read by the renderer through `ctx.attrs(name, fallback)` (for example `x-scale`, `show-markers`, `inner-radius`); a change re-renders. Boolean options accept the bare attribute; only `"false"` is off |
| Data source | `data` property, `src` URL, or an inline `<script type="application/json">` child | In that priority order. A `src` response is fetched once and reused; `reload()` fetches it again |
| Composed parts | nested or `chart="<id>"`-bound part elements | Title, legend and visible data table are separate elements bound to the chart (see the part specs) |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `type` | string | `"bar"` | No | Chart type key |
| `orientation` | `"vertical"\|"horizontal"` | type's default | No | Orientation passed to the renderer |
| `src` | URL | — | No | JSON data URL (used when `data` is not set) |
| `label` | string | — | No | Accessible name of the chart (§13 for the fallback chain) |
| `title` | string | — | No | Native tooltip; also a fallback for the accessible name. It draws no visible title — use `<mj-chart-title>` |
| `description` | string | — | No | Longer text alternative, exposed through the visually hidden `description` part; default `meta.description` |
| `variant` | string | — | No | Renderer drawing variant |
| (any other) | string | — | No | Renderer option (§4) |

Common MjElement attributes (`dock`, `anchor`, `theme`, `hidden`, `context-menu`)
behave as on every component.

## 6. Properties

| Property | Type | Description |
|----------|------|-------------|
| `data` | `object \| null` | The chart data (`{ meta?, categories?, series?, ...family-specific fields }`); setting it re-renders |
| `chartModel` | `object \| null` (read-only) | The normalized model of the last render (`meta`, `categories`, visible `series`, `allSeries`, `hiddenSeries`, `raw`, `isEmpty`) |
| `chartContext` | `object \| null` (read-only) | The context delivered to parts (`type`, `width`, `height`, `orientation`, `label`, `colorScale`, `colorFor`, `hiddenSeries`, `legend`, `table`) |
| `chartTable` | `object \| null` (read-only) | The accessible table model (`columns`, `rows`, `caption`, `totalRows`, `truncated`) |
| `chartState` | string (read-only) | `"idle"`, `"loading"`, `"ready"`, `"empty"`, `"error"` or `"deferred"` (drawn when the surface gets a size) |
| `chartLabel` | string (read-only) | The accessible name the chart currently carries |
| `hiddenSeries` | `string[]` (read-only) | Names of the hidden series (a copy) |

**Methods**

| Method | Description |
|--------|-------------|
| `hideSeries(name)` / `showSeries(name)` | Hide / show a series by name and re-render; returns whether anything changed |
| `toggleSeries(name)` | Flip a series; returns whether it is visible afterwards |
| `showAllSeries()` / `isSeriesHidden(name)` | Show every series / query one |
| `reload()` | Fetch `src` again (or re-read the inline JSON) and render; returns a Promise |
| `redraw()` | Render now (after changing the `data` object in place); returns a Promise |
| `hasLegendPart()` | Whether an `<mj-chart-legend>` is bound |
| `registerPart(part)`, `unregisterPart(part)`, `refreshLabel()` | Part-facing: used by the chart part elements, not by page code |

**Subclass hooks** (an element that is one chart type with its own data shape,
e.g. `<mj-gantt-chart>`; see §21)

| Hook | Default | Description |
|------|---------|-------------|
| `get chartType()` | the `type` attribute, else `"bar"` | The type key drawn |
| `get defaultChartLabel()` | "`<type>` chart" | The last fallback of the accessible name (§13) |
| `adaptChartData(data)` | returns `data` | The data the renderer reads, built from the resolved data (`data`, `src` or inline JSON). It must return the same object for the same input, so colours and cached layouts stay put. A throw shows the error message |
| `readOption(name, fallback)` | the attribute (`variant` for `"style"`) | What `ctx.attrs` returns; override to map the element's own attribute names and defaults onto renderer options |

## 7. Slots

| Slot | Description |
|------|-------------|
| (default) | Nested chart parts (`<mj-chart-title>`, `<mj-chart-legend>`, `<mj-chart-data-table>`) and the inline JSON `<script>`. Other content is not displayed |
| `empty` | Replaces the text of the empty message ("No chart data supplied.") |

## 8. Events

All events bubble and are composed; none is cancelable.

| Event | `detail` | Description |
|-------|----------|-------------|
| `mj-chart-render` | `{ type: string, duration: number }` | After a successful draw |
| `mj-chart-empty` | `{ type: string }` | The data holds nothing to draw |
| `mj-chart-error` | `{ message: string }` | Data load / parse failure, unknown type, or a renderer exception |
| `mj-chart-series-toggle` | `{ series, seriesIndex, visible, hidden, hiddenSeries }` | A series was hidden or shown (legend or API) |
| `mj-chart-connect` | `{}` | The controller connected or got a new `id` (parts bind on it) |
| `mj-chart-<mark>-click` | per type | Renderer interaction events (`mj-chart-bar-click`, `mj-chart-point-click`, `mj-chart-slice-click`, `mj-chart-node-click`, `mj-chart-marker-click`, ...), on click and on Enter / Space on a focused mark. The detail shapes are listed on each chart-type page; the project types add the mark's data `index` |
| `mj-chart-group-toggle` | `{ group, collapsed, collapsedGroups }` | gantt: a group header row was activated (§21) |
| `mj-chart-cycle-detect` | `{ cycles: string[][] }` | dependency-graph: the data has cycles; once per data object, not per redraw (§21) |
| `mj-chart-select` | per type | Selection event of the geo heatmap surface |

`mj-chart-legend-toggle` is emitted by `<mj-chart-legend>`, not by the chart.

## 9. CSS parts & custom properties

**Parts**
- `::part(description)`, `::part(surface)`, `::part(svg)`, `::part(table)`
- `::part(message)` with `::part(message loading)`, `::part(message empty)`,
  `::part(message error)`
- Renderers put further part names on their marks inside the SVG (`bar`, `point`,
  `slice`, `legend`, ...); see the chart-type specs.

**Custom properties**

| Property | Default | Description |
|----------|---------|-------------|
| `--mj-chart-min-height` | the type's registered `minHeight`, else `280px` | Block size of the surface when the host has no height of its own |
| `--mj-chart-series-1` ... `--mj-chart-series-8` | tokens in `tokens.css` (light / dark values) | Categorical series palette; slots past 8 repeat the hues with a lightness shift (24 distinct colors) |
| `--mj-chart-series-secondary`, `--mj-chart-series-secondary-border` | tokens | Secondary / comparison marks |
| `--mj-chart-geo-land`, `--mj-chart-geo-no-data` | tokens | Map backgrounds |

The part elements have their own properties (`--mj-chart-title-font-size`,
`--mj-chart-title-color`, `--mj-chart-legend-swatch`; see their specs).

## 10. States

| State (`chartState`) | Visual effect | ARIA effect |
|----------------------|---------------|-------------|
| `loading` | "Loading" message while a `src` is fetched and nothing is drawn yet (a drawn chart stays while its replacement loads) | `aria-busy="true"` |
| `ready` | The drawing | Marks focusable (§12) |
| `empty` | "No chart data supplied." message | Table emptied |
| `error` | Error message | `mj-chart-error` |
| `deferred` | Nothing drawn: the surface is 0 x 0 (e.g. `hidden`); drawn when it gets a size | Table and parts still updated |
| series hidden | The series is left out of the drawing, the generic table and the legend's pressed state | — |

## 11. Behavior & interactions

- The chart re-renders when `data`, `src`, the inline JSON, `type`, `orientation`,
  any renderer option attribute, the hidden-series set or its size changes. Local
  data is drawn synchronously; a `src` still loading is drawn when the response
  arrives, and a newer render always wins over an older response.
- Each render builds the model, asks the renderer to draw, collects what it
  publishes (`ctx.setTable`, `ctx.setLegend`, `ctx.setContentHeight`), builds the
  legend entries and the accessible table, and delivers the model and context to
  every bound part.
- **Parts** bind by `chart="<id>"` or as descendants; a part that appears before
  the chart binds when the chart announces itself (`mj-chart-connect`). A chart
  that is removed clears its parts and fills them again when it is re-inserted.
  When the chart's accessible name changes without a render (a bound title's text
  changes, a title binds or leaves), the chart re-delivers its model so the parts
  that show the name — a data table's default caption — follow at once.
- A bound `<mj-chart-legend>` makes radar, parallel, bullet and streamgraph leave out
  their inline key.
- Each series keeps its color — its own `color` in the data, else the palette
  slot of its position in the data — so hiding a series never recolors the
  others; non-series keys get palette slots for the lifetime of the data.

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| `Tab` | Enters the drawing: its focusable marks form one tab stop (roving tabindex) |
| `←` / `↑` | Previous mark |
| `→` / `↓` | Next mark |
| `Home` / `End` | First / last mark |
| `Enter` / `Space` | Activates the focused mark where the renderer offers it (its `mj-chart-<mark>-click` event) |

Legend toggles are keyboard-operable buttons of `<mj-chart-legend>`.

## 13. Accessibility

- The host is a `figure`. Its `aria-label` is, in order: an `aria-label` the page
  wrote, `label`, `title`, the text of a bound `<mj-chart-title>`, `meta.title`, else
  "`<type>` chart". With `aria-labelledby` the chart writes no `aria-label`.
- `description` (or `meta.description`) is read with the chart from the visually
  hidden `description` part.
- The drawing is exposed (not `aria-hidden`); focusable marks carry their own labels.
- A visually hidden data table (`::part(table)`) follows the drawing: the
  renderer's table for its type when it publishes one, else a generic table of the
  data (categories x series, points, or flattened family data), at most 500 rows
  with a note. Its caption is the renderer's caption, else the chart's name. It is
  not a live region. `<mj-chart-data-table>` shows the same table visibly.
- Series are not distinguished by color alone where the renderer offers markers,
  labels or patterns; the legend marks hidden series with a hollow swatch and a
  struck-through label.

## 14. Form participation

N/A — `<mj-chart>` is a display component with no form value.

## 15. Internationalization & RTL

- Numbers in the drawing and the table follow the library locale (`core/intl.js`
  `formatNumber`); a locale change re-renders.
- "Loading" goes through `t("core.loading")`. The empty / error messages and the
  hidden table's default caption and truncation note are English literals in
  `mjchart.js`; `core/intl.js` already registers `mj.chart.*` keys for them.
- Layout uses logical properties; renderers mirror where the type defines it.

## 16. Progressive enhancement / SSR

Without script nothing is drawn; the inline JSON `<script>` is inert. A page that
needs a no-script fallback can render a static `<table>` next to the chart (or
inside an `<mj-chart-data-table>`, whose light DOM shows until it upgrades).

## 17. Dependencies

- `MjElement` (`core/mjelement.js`) — lifecycle, attributes, theming, docking.
- `charts/core/chartmodel.js` (model and table), `chartregistry.js` (part
  binding), `renderregistry.js` (renderers and their options), `scales.js`
  (scales and the palette), `svgdraw.js` (SVG helpers), `jsonsource.js` (data
  sources), and the renderers in `charts/core/renderers/`.
- `core/intl.js` — locale, number formatting, strings.
- Registered with the parts by `charts/index.js` (`defineAll`).

## 18. Edge cases & error handling

- Invalid JSON, a failed `src` fetch or non-object data: error message,
  `mj-chart-error`, parts cleared.
- Unknown `type` or a renderer exception: error message; the generic table and a
  series legend are still delivered.
- 0 x 0 surface: rendering is deferred until the surface has a size.
- Every series hidden: the chart is not "empty"; the drawing has no series. (The
  chart's own hidden table then lists the remaining data, e.g. the categories, by
  the generic family-data path; `<mj-chart-data-table>` shows "All series are
  hidden." instead.)
- More than 500 table rows: the table is cut with a note.

## 19. Acceptance criteria

- [ ] Every catalogued `type` renders its example without error (xtest chart-type pages).
- [ ] `data`, `src` and inline JSON are read in that priority; `reload()` refetches `src`.
- [ ] Changing `type`, `orientation`, an option attribute or `data` re-renders.
- [ ] The host is a `figure` named per §13; `description` is exposed.
- [ ] The hidden data table is present after each render, capped at 500 rows.
- [ ] Marks are one tab stop with arrow / Home / End movement.
- [ ] `hideSeries` / `showSeries` / `toggleSeries` update the drawing, the table and bound legends, and emit `mj-chart-series-toggle`.
- [ ] Bound title, legend and data-table parts follow every render and the chart's name.
- [ ] Loading, empty, error and deferred states behave as in §10.
- [ ] axe scan zero violations on the chart-type pages.

## 20. Open questions

- Should the empty / error messages and the hidden table's strings go through `t()`?
- Should the generic table show an empty state instead of the remaining data when
  every series is hidden?
- Should the chart drop its hidden table while a visible `<mj-chart-data-table>` is
  bound, to avoid reading the data twice?
- Which of the planned parts (`<mj-chart-plot>`, `-axis`, `-grid`, `-tooltip`,
  `-annotation`, ...) of `chart-components-plan.md` §3.3 are still wanted?

## 21. Project chart types and their wrapper elements (WW-1498)

The four standalone project-management charts were merged into the chart types;
what they did that the types lacked moved into the renderers, so
`<mj-chart type="...">` has it too. The wrappers keep their tag, data shape,
attributes and events (their specs list only what differs).

**gantt** (`renderers/gantt.js`)
- Data: `tasks` as before plus `milestone: true`; `groups: [{ id, label }]` gives the
  order and names of the header rows (with it, a task naming another group is
  ungrouped); `markers: [{ label, date }]`; `phases: [{ label, start, end }]`.
- A start-only task runs to the edge of the chart (dashed) instead of being a
  diamond; `milestone: true`, a zero-length span or an end only is a diamond; a task
  outside the window shows an arrow at the edge it lies beyond.
- Group header rows are buttons (`aria-expanded`): activating one updates the
  host's `collapsed-groups` attribute (a JSON array of group ids, also settable by
  the page) and emits `mj-chart-group-toggle`; the table keeps collapsed tasks and
  the axis does not rescale.
- Markers are focusable marks (`mj-chart-marker-click { label, date, index }`) with a
  dashed line, a diamond and the name; phases are background bands; the today line
  has a "Today" label.
- Options: `start-date`, `end-date`, `scale` (day / week / month / quarter),
  `show-progress`, `show-dependencies`, `density`, `row-height`, `collapsed-groups`.
- The chart asks for the height of its rows (`ctx.setContentHeight`; 32 px rows,
  24 px compact) and registers `minHeight: 120`.

**roadmap** (same renderer)
- One lane per group; bars that do not overlap share a row, overlapping bars stack.
- Columns: calendar periods (`scale` quarter / month / half-year) with headers, or
  with `mode="bucket"` the `buckets: [{ id, label }]` (a task's `bucket` names its
  column). Unknown groups go to an "Unassigned" lane; tasks that cannot be placed
  are counted in a note (`part="unplaced-note"`) and listed as "Not placed".
- Status colour and icon: planned, in-progress / active, completed / done,
  at-risk (now amber, was red), blocked. Markers, phase bands with names in their
  own row, the today line with its label row.
- Options: `mode`, `scale`, `start-date`, `end-date`, `density`, `today`.

**timeline / milestone** (`renderers/timeline.js`)
- `kind` on an event (release diamond, freeze triangle, tag / milestone circle)
  sets the shape and, without a `status`, the colour; `phases` bands; a today line;
  events on the same date are nudged apart.
- Options: `start-date`, `end-date` (events outside are listed, not drawn),
  `dim-past` (past events faded, state in the accessible name), `density`, `today`.
- `mj-chart-event-click` adds `kind` and `index`.

**dependency-graph** (`renderers/network.js`)
- Labelled boxes (name, status line) instead of circles; border colour by `status`
  (todo, in-progress, done, blocked), else by group; the graph asks for the height
  of its busiest column.
- `criticalPath: [id, ...]` highlights its nodes and the links between consecutive
  entries (`show-critical-path="false"` turns it off); cycles are drawn dashed red,
  their nodes get a badge and "in a cycle" in their name, and
  `mj-chart-cycle-detect` reports them once per data object. The table gains
  Status and Critical path columns.

**Wrapper elements** (`components/pmchartwrapper.js` + one file each) extend
`MjChart` through the subclass hooks of §6: fixed type, a memoised data adapter,
option-name aliases (`today-marker` -> `today`, `show-percent` -> `show-progress`),
a toolbar whose button discloses the chart's own table (`part="table data-table"`),
a selection marked `aria-current` with a detail panel and slot, `mj-data-load`
once per data and `mj-error` for a data failure.
