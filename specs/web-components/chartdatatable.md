# Chart Data Table Spec

- **Tag:** `<mj-chart-data-table>`
- **Class / file:** `MjChartDataTable` / `charts/mjchartdatatable.js`
- **Category:** Media & visualization (§5.9) — chart part of `<mj-chart>`
- **Primary or Variant:** Primary (a companion part of `<mj-chart>`)
- **Synonyms covered:** Chart data table, Accessible data table, Data inspector
- **Phase:** P3 (ships with `<mj-chart>`; Phase 1 of `chart-components-plan.md` §7)
- **Status:** Implemented (this spec documents the shipped behavior of `mjchartdatatable.js`)

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-chart-data-table>` renders the data of a chart as a real, visible
`<table>`. It is one of the coordinated part elements of the chart library
(`chart-components-plan.md` §3.3): it binds to an `<mj-chart>` controller — by
the controller's id in its `chart` attribute, or as a descendant of the chart —
and shows the table model the controller built for its last render: the
renderer's own table for its chart type when it supplies one, else the generic
table of the data. The generic table leaves hidden series out; with every series
hidden a short note takes the table's place. A table is cut at 500 rows with a
note. The element is both the visible accessible
alternative that plan §5.9 asks for and a data inspector next to the drawing.

## 2. When to use / when not to use

Use when the numbers behind a chart should be visible on the page: under or next
to the chart, in a dashboard "data" tab, or as the visible text alternative of a
complex chart. It follows every redraw, so it also suits live data.

Do not use:
- only to make a chart accessible — `<mj-chart>` always renders its own visually
  hidden data table; add this part when the table should be seen;
- for a sortable, filterable, paginated or editable grid — use `<mj-data-table>`
  (fed with the same data);
- to show data without a chart — the part has nothing to show unless it is bound
  to an `<mj-chart>`.

## 3. Anatomy

- **Host element** — `display: block; overflow: auto` (it scrolls when the table
  is wider than the host).
- **container (part)** — `<div>` holding the table (or the note below); empty
  when there is no table.
- **table (part)** — the `<table>`:
  - `<caption>` — the caption text (§11);
  - `<thead>` — one row of `<th scope="col">` column headers;
  - `<tbody>` — one `<tr>` per row; the first cell is a `<th scope="row">` when
    it is not blank, otherwise a `<td>`; the other cells are `<td>`;
  - `<tfoot>` — present only when rows were cut: one `<td colspan>` with the
    truncation note.
- **empty (part)** — `<p class="empty">` shown instead of the table while every
  series is hidden: "All series are hidden." (`mj.chart.tableAllSeriesHidden`).

## 4. Variants & modes

| Mode | When | Table |
|------|------|-------|
| Generic — values | series carry `values` | First column "Category" (or "#" when the data has no categories), then one column per visible series; one row per category / position |
| Generic — points | series carry `points` | One row per point: "Series", then the point fields (`X`, `Y`, `Z` for array points; the object's keys otherwise) |
| Generic — family data | no series data (nodes, links, tasks, trees, gauge values, ...) | One row per flattened record; a leading "Group" column when records come from several collections; at most 12 columns |
| Renderer table | the chart type publishes `ctx.setTable` or registers a `table` function | The renderer's columns, rows and caption |
| Truncated | more than 500 rows | The first 500 rows plus the footer note |
| All series hidden | the model has hidden series and no visible one | No table: the `empty` note "All series are hidden." |

The part does not choose between these; the controller does (§11).

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `chart` | string (element id) | — | No | Id of the `<mj-chart>` to bind to (trimmed). Looked up in the part's own root (document or shadow root), then in the document; an element that is not an `<mj-chart>` is ignored. Without it, or when it does not resolve, the nearest `<mj-chart>` ancestor is used (crossing shadow roots). Changing it rebinds |
| `caption` | string | — | No | Table caption. Blank (empty or whitespace) counts as absent; a non-blank value is used as written (not trimmed). Default chain in §11. Changing it redraws from the cached model |

Neither attribute has a property. Common MjElement attributes (`dock`, `anchor`,
`theme`, `hidden`, `context-menu`) behave as on every component. `disabled` has
no component-specific effect.

## 6. Properties

| Property | Type | Description |
|----------|------|-------------|
| `controller` | `MjChart \| null` (read-only) | The chart the table is bound to (ChartPart mixin) |

**Methods**

| Method | Description |
|--------|-------------|
| `applyModel(model, context)` | Called by the controller with its model and render context (both `null` while the chart has nothing to show); caches them and redraws. Controller-facing; page code does not call it |

The table model itself is available on the chart as `chart.chartTable`
(`{ columns, rows, caption, totalRows, truncated }`).

## 7. Slots

N/A — the shadow root has no slot; light-DOM children are not rendered once the
element is upgraded.

## 8. Events

N/A — `<mj-chart-data-table>` dispatches no events. It redraws when the chart
delivers a render; listen to the chart's `mj-chart-render`, `mj-chart-empty` and
`mj-chart-error` to react to the same moments.

## 9. CSS parts & custom properties

**Parts**
- `::part(container)` — the `<div>` around the table
- `::part(table)` — the `<table>` element (its caption, rows and cells are not
  parts and cannot be targeted from outside)
- `::part(empty)` — the note shown instead of the table while every series is
  hidden

**Custom properties**

N/A — no component-specific custom properties. The shared tokens it reads, with
their fallbacks in the CSS:

| Token | Fallback | Used for |
|---|---|---|
| `--mj-font-size-sm` | `0.875rem` | Table text size; note text size |
| `--mj-text` | `#14181f` | Table text color |
| `--mj-font-weight-medium` | `500` | Caption and row-header weight |
| `--mj-space-2` | `0.5rem` | Caption bottom padding; cell block padding; note block padding |
| `--mj-space-3` | `0.75rem` | Cell inline padding |
| `--mj-border` | `#e0e3e9` | Row separator (bottom border of every cell) |
| `--mj-bg-subtle` | `#f7f8fa` | Column-header background |
| `--mj-text-muted` | `#5f6673` | Column-header text; truncation note; all-hidden note (italic) |
| `--mj-font-size-xs` | `0.75rem` | Column-header size (upper-case, `0.05em` letter spacing) |
| `--mj-bg-muted` | `#eef0f3` | Body row hover background |

## 10. States

| State | Visual effect | ARIA effect |
|-------|---------------|-------------|
| populated | Caption, header row and body rows | Native table semantics |
| truncated | Italic, muted note in the footer | Note is a footer cell |
| all series hidden | Italic, muted "All series are hidden." paragraph instead of the table | Plain text; no table is exposed |
| row hover | `--mj-bg-muted` background on the body row | — |
| empty | Nothing rendered (unbound, chart without data, data failure, table without columns) | Nothing exposed |

The table is not interactive: there are no focus, selected, sorted, disabled or
loading states.

## 11. Behavior & interactions

- **Binding** (ChartPart mixin): on connect the part resolves its controller
  (§5 `chart`), registers with it (`registerPart`) and receives the chart's
  current model if it has one. A chart that is not upgraded yet, or enters the
  page or gets its id later, announces itself with `mj-chart-connect` and the part
  binds then. On disconnect it unregisters.
- **Table source**: with a `null` model the container is emptied. Otherwise the
  table is `context.table` — always set by the chart — and only without a context
  the generic table built from the model.
- **Which table the chart builds** for a render: the table the renderer published
  with `ctx.setTable`, else the type's registered `table` function, else the
  generic table of the model; a renderer table that is not usable, or has no
  columns, falls back to the generic one. The generic table is built from the
  visible series only; a renderer table is built by the renderer from the model it
  is given, whose `series` holds the visible series. Rows are capped at 500
  (`TABLE_ROW_LIMIT`), with `truncated` and `totalRows` recorded.
- **Caption**, in order: the `caption` attribute when not blank; the renderer
  table's caption; the chart's accessible name (`context.label`: an `aria-label`
  the page wrote, the chart's `label`, its `title` attribute, a bound
  `<mj-chart-title>`, `meta.title`, else "`<type>` chart"); the localized
  `t("mj.chart.tableCaption")` ("Chart data"). Because the chart's name is never
  empty, the last one is only reached without a chart context.
- **Every series hidden**: when the model has hidden series and no visible one,
  the part shows the `empty` note instead of a table, whatever table the chart
  built (the generic table would otherwise list the remaining data, such as the
  category labels). Showing a series brings the table back.
- **Redraw only on change**: the chart broadcasts on every render, including each
  resize. The part fingerprints the caption plus the table's columns, rows,
  caption and total; an identical fingerprint leaves the DOM untouched, a
  different one replaces the whole table.
- **Cell content**: every value is written as text, never markup. The first cell
  of a row is shown as written. Other numeric cells are formatted with
  `Intl.NumberFormat` in the library locale (`formatNumber`); `null`,
  `undefined` and `NaN` give an empty cell; booleans read `true` / `false`; dates
  are ISO strings; lists of scalars are comma-joined, cut after 12 entries with
  ", …"; lists of objects read "`N` items".
- **Chart states**: chart with no data — the table model has no columns and the
  container is emptied; data failure (fetch / parse) or chart removed — the model
  is `null` and the container is emptied; unknown chart type or a renderer
  exception — the generic table is shown (the model is kept); chart with a 0 x 0
  box (e.g. `hidden`) — the renderer does not run but the table is still built
  and delivered (a table published only through `ctx.setTable` needs a draw).
- **Caption follows the chart name at once**: when the chart's name changes
  without a re-render (a bound title's text changes, a title part binds or
  leaves), the chart's `refreshLabel()` delivers the model to its parts again, so
  a caption taken from the chart name changes immediately.
- **Layout when nested**: `<mj-chart>` styles slotted parts `flex: 0 0 auto`, so
  a nested table keeps its full height below the drawing. In a chart with a fixed
  height the drawing surface (which may shrink to 0) gives up the room; at 0 the
  chart postpones drawing until it has a size again. Long tables belong outside
  the chart, bound with `chart="<id>"`.

## 12. Keyboard interaction

N/A — the part contains no focusable element and handles no keys. Screen-reader
table navigation works on the native table. The host's scroll container gets no
`tabindex`.

## 13. Accessibility

- Native table semantics: the caption names the table; column headers are
  `<th scope="col">`; the first cell of each row is a `<th scope="row">` unless
  it is blank, in which case the row has no header. Blank column headers in a
  renderer table are named "Row" (first column) or "Column `N`" by the model.
- `<mj-chart>` keeps its own visually hidden table (its `::part(table)`), so with
  this part bound, assistive-technology users meet the data twice. The chart is
  not linked to the visible table.
- Table updates are not announced (no live region); the whole table is replaced
  on change.
- The truncation note is text in a footer cell.
- Column headers are visually upper-cased with CSS only; the text is unchanged.

## 14. Form participation

N/A. `<mj-chart-data-table>` is not form-associated.

## 15. Internationalization & RTL

- The default caption, the truncation note and the all-hidden note are read
  through `t()`: `mj.chart.tableCaption` ("Chart data"),
  `mj.chart.tableTruncated` (plural forms `one` / `other`, `{count}` = the
  number of rows shown: "Only the first {count} rows are shown.") and
  `mj.chart.tableAllSeriesHidden` ("All series are hidden."). Strings registered
  with `registerStrings` replace them; the part re-renders on the change.
- Generic table headers ("Category", "#", "Group", "Series", field names with the
  first letter capitalized), "Summary" and "`N` items" come from
  `charts/core/chartmodel.js` and are English literals.
- Numbers (except in the first column) follow the library locale. A locale change
  re-renders the element (MjElement default `onLocaleChanged` → `renderAgain()`),
  which rebinds it and re-formats the numbers. Dates stay ISO strings.
- Caption and cells use `text-align: start`, so they follow the inherited
  direction; the table mirrors in RTL.

## 16. Progressive enhancement / SSR

The table exists only once the chart has rendered on the client. Because the
shadow root has no slot, a server-rendered `<table>` placed inside the element is
visible before upgrade and without script, and is no longer rendered once the
element upgrades and the live table takes over — a usable no-script fallback.

## 17. Dependencies

- **Registry + base element helper** (§6) — `MjElement` (`render`, `afterRender`,
  `onAttributeChanged`, docking / anchoring, theming)
- **ChartPart mixin** — `charts/core/chartpart.js` and
  `charts/core/chartregistry.js` (`resolveController`, `mj-chart-connect`)
- **Chart model** — `charts/core/chartmodel.js` (`buildTableModel`,
  `buildTableElement`, `tableSignature`, `TABLE_ROW_LIMIT` = 500) and
  `formatNumber` from `charts/core/svgdraw.js` (library locale via
  `core/intl.js`)
- **`<mj-chart>`** — `charts/mjchart.js`: `registerPart` / `unregisterPart`, the
  render context (`table`, `label`), `chartTable`, `refreshLabel`. See
  [chart.md](chart.md): the chart keeps a visually hidden `::part(table)`; the
  visible table is this separate element, and its cells are not focusable.
- **Renderer registry** — `charts/core/renderregistry.js` (`table` registration
  option, `ctx.setTable`)
- **Design-token stylesheet** (§6)
- Registered by `charts/index.js` (`defineAll`).

## 18. Edge cases & error handling

- Every series hidden: the `empty` note "All series are hidden." replaces the
  table (the chart's own hidden table still takes the generic family-data path
  and lists the category labels as "Index" / "Value" rows; see chart.md §18).
- More than 500 rows: the first 500 are shown with the footer note; `{count}` is
  the number shown (500), and the plural form is chosen for it in the current
  locale.
- Generic family-data tables keep at most 12 columns; values-by-series tables
  have one column per visible series, with no cap.
- A renderer table that is not usable (no `columns` / `rows` arrays) or has no
  columns: the generic table is used.
- Blank first cell: the row has no row header.
- Whitespace-only `caption`: ignored. Leading and trailing spaces of a non-blank
  `caption` are kept.
- Unbound part, or `chart` id that does not resolve with no chart ancestor:
  nothing is rendered.
- Chart removed from the page: the table is cleared; the part stays registered
  and is filled again when the chart is re-inserted.
- Wide tables: the host scrolls; headers are not sticky.
- Live data: each changed table replaces the DOM, so a text selection inside the
  table is lost.
- A failure while the controller delivers a model is caught by the controller
  (console warning) and does not stop the chart or its other parts.

## 19. Acceptance criteria

- [ ] Bound to a categories-and-series chart, the table has a "Category" column and one column per series, one row per category.
- [ ] Without categories, the first column is "#" with the row positions.
- [ ] A chart type that supplies its own table shows that table (columns, rows, caption).
- [ ] Hiding a series removes its column from the generic table; showing it brings it back.
- [ ] Hiding every series shows "All series are hidden." instead of a table; showing one brings the table back.
- [ ] The default caption and the truncation note come from `t()` (`mj.chart.tableCaption`, `mj.chart.tableTruncated`) and follow `registerStrings`.
- [ ] A caption taken from the chart's name follows a bound title's text change at once.
- [ ] More than 500 rows: 500 rows are shown with the footer note.
- [ ] `caption` overrides the caption; removing it falls back to the renderer caption, then the chart's accessible name.
- [ ] Column headers are `th scope="col"`; non-blank first cells are `th scope="row"`.
- [ ] Numeric cells are formatted for the library locale and re-formatted after `setLocale()`.
- [ ] A resize re-render with unchanged data leaves the table DOM untouched.
- [ ] Changing the chart's `data` updates the table.
- [ ] Chart with no data, a data failure, or the chart removed: the part renders nothing.
- [ ] Binding works nested, by `chart` id, and when the chart is inserted or given its id later; changing `chart` rebinds.
- [ ] Cell values are written as text, never parsed as markup.
- [ ] axe scan zero violations for a populated and a truncated table.
- [ ] Light, dark, high-contrast and RTL rendering verified.

## 20. Open questions

- Should the chart drop (or point to) its own hidden table while a visible data
  table part is bound, as it drops renderer inline keys for a bound legend?
- Should an empty chart show a message ("No data") rather than nothing?
- Should a scrolling table be a focusable, labelled region (`role="region"`,
  `tabindex="0"`) so it can be scrolled from the keyboard?
- Should dates and first-column numbers be formatted for the locale?
- Should the `caption` attribute be trimmed like the renderer caption?
- Should sorting, sticky headers or column formatting be offered here, or left to
  `<mj-data-table>`?
