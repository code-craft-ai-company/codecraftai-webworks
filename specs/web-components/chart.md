# Chart Spec

- **Tag:** `<mj-chart>`
- **Class / file:** `MjChart` / `mjchart.js`
- **Category:** Media & visualization
- **Primary or Variant:** Primary
- **Synonyms covered:** Line chart, Bar chart, Pie chart, Donut chart, Area chart, Scatter plot, Heatmap
- **Phase:** P3
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-chart>` renders data visualizations — line, bar, pie, donut, area, scatter,
and heatmap — using a pluggable rendering adapter so no charting engine is
bundled in-house. The component owns the accessible surface (ARIA, data-table
fallback, keyboard-reachable tooltips, color-independent encoding) while
delegating all pixel-level drawing to the adapter (e.g. Chart.js, Vega-Lite,
D3). It is responsive, theme-aware, and re-renders automatically on resize.

## 2. When to use / when not to use

**Use** for data visualizations embedded in dashboards, reports, and analytics
pages where an accessible, themed chart is required.

**Do not use** for sparklines (use `<mj-sparkline>` for compact inline trends),
for gauges (use `<mj-gauge>`), or for node/edge diagrams (use `<mj-diagram>`).
Do not use without supplying a rendering adapter — the component will render only
its accessible data table alternative in that case.

## 3. Anatomy

- **Container** (`::part(container)`) — outermost element, holds all sub-parts.
- **Title** (`::part(title)`) — visible chart title rendered as a heading.
- **Description** (`::part(description)`) — visible or visually-hidden subtitle
  or description text.
- **Canvas/SVG region** (`::part(render-target)`) — the element passed to the
  adapter for drawing; may be a `<canvas>` or `<svg>` depending on the adapter.
- **Legend** (`::part(legend)`) — series/category legend with shapes and labels;
  rendered in HTML for accessibility.
- **Tooltip** (`::part(tooltip)`) — keyboard- and pointer-reachable tooltip for
  data point detail.
- **Data table** (`::part(data-table)`) — accessible `<table>` that mirrors the
  full dataset; visible or visually-hidden per `show-table` attribute.
- **Loading** (`::part(loading)`) — spinner shown while async data resolves.
- **Error** (`::part(error)`) — error message shown when data or adapter fails.
- **Empty** (`::part(empty)`) — no-data message.

## 4. Variants & modes

| Variant / mode | Attribute value | Behavior |
|----------------|----------------|----------|
| Line | `type="line"` | Series plotted as connected lines; supports multiple series |
| Bar (vertical) | `type="bar"` | Grouped or stacked vertical bars |
| Bar (horizontal) | `type="bar-horizontal"` | Horizontal bar; useful for labeled categories |
| Pie | `type="pie"` | Circular slices; single series |
| Donut | `type="donut"` | Pie with center hole; center label slot available |
| Area | `type="area"` | Line chart with filled area; stacked option |
| Scatter | `type="scatter"` | X/Y point plot; optional bubble size |
| Heatmap | `type="heatmap"` | Two-dimensional cell grid colored by value |
| Show table | `show-table` (boolean) | Renders the accessible data table visibly below the chart |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `type` | `"line"\|"bar"\|"bar-horizontal"\|"pie"\|"donut"\|"area"\|"scatter"\|"heatmap"` | `"bar"` | Yes | Chart type |
| `title` | `string` | `""` | Yes | Chart title (rendered as heading and passed to adapter) |
| `description` | `string` | `""` | Yes | Accessible description of what the chart shows |
| `aspect-ratio` | `string` | `"16/9"` | Yes | CSS aspect-ratio of the render area |
| `show-legend` | `boolean` | `true` | Yes | Show/hide the legend |
| `show-table` | `boolean` | `false` | Yes | Show the data table visibly (always present in DOM for accessibility) |
| `show-tooltip` | `boolean` | `true` | Yes | Enable data-point tooltips |
| `color-scheme` | `string` | `""` | Yes | Named token palette for series colors (e.g. `"categorical"`, `"sequential-blue"`) |
| `loading` | `boolean` | `false` | Yes | Shows the loading state |
| `locale` | `string` | `""` | Yes | BCP 47 locale for axis tick formatting; defaults to document locale |

## 6. Properties

| Property | Type | Description |
|----------|------|-------------|
| `data` | `ChartData` | Dataset object; `{ labels: string[], series: Series[] }` where `Series = { name: string, values: number[], pattern?: string }` |
| `adapter` | `ChartAdapter` | The pluggable rendering adapter instance; must implement `{ render(target, data, options): void, destroy(): void, resize(): void }` |
| `adapterOptions` | `object` | Adapter-specific configuration object passed verbatim to `adapter.render()`; not reflected to attributes |
| `selectedPoint` | `{ seriesIndex: number, pointIndex: number } \| null` | Currently focused/selected data point; read/write |

## 7. Slots

| Slot | Description |
|------|-------------|
| `title` | Rich HTML chart title replacing the `title` attribute |
| `description` | Rich HTML description replacing the `description` attribute |
| `legend` | Custom legend replacing the generated legend |
| `empty` | Content shown when `data.series` is empty or all values are null |
| `donut-center` | Center label content for `type="donut"` charts only |

## 8. Events

| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-chart-point-focus` | `{ seriesIndex: number, pointIndex: number, value: number, label: string }` | Yes | No | Fired when a data point is focused via keyboard or pointer hover |
| `mj-chart-point-select` | `{ seriesIndex: number, pointIndex: number, value: number, label: string }` | Yes | No | Fired when a data point is selected (click or Enter) |
| `mj-chart-point-deselect` | `{}` | Yes | No | Fired when selection is cleared |
| `mj-chart-render` | `{ type: string, duration: number }` | Yes | No | Fired after the adapter completes a render pass |
| `mj-chart-error` | `{ message: string }` | Yes | No | Fired when adapter or data loading fails |
| `mj-chart-legend-toggle` | `{ seriesIndex: number, visible: boolean }` | Yes | No | Fired when a legend item is toggled |

## 9. CSS parts & custom properties

**Parts**
- `::part(container)`, `::part(title)`, `::part(description)`
- `::part(render-target)`, `::part(legend)`, `::part(tooltip)`
- `::part(data-table)`, `::part(loading)`, `::part(error)`, `::part(empty)`

**Custom properties**
| Property | Default | Description |
|----------|---------|-------------|
| `--mj-chart-title-font-size` | `var(--mj-font-size-lg)` | Title font size |
| `--mj-chart-title-color` | `var(--mj-color-text-primary)` | Title color |
| `--mj-chart-legend-font-size` | `var(--mj-font-size-sm)` | Legend label font size |
| `--mj-chart-legend-gap` | `var(--mj-space-3)` | Gap between legend items |
| `--mj-chart-tooltip-bg` | `var(--mj-color-surface-overlay)` | Tooltip background |
| `--mj-chart-tooltip-color` | `var(--mj-color-text-primary)` | Tooltip text color |
| `--mj-chart-tooltip-radius` | `var(--mj-radius-sm)` | Tooltip corner radius |
| `--mj-chart-series-1` through `--mj-chart-series-8` | (token palette) | Per-series color tokens |
| `--mj-chart-series-1-pattern` through `--mj-chart-series-8-pattern` | (token SVG patterns) | Per-series fill patterns for no-color-only encoding |

## 10. States

- **loading** — spinner visible; render target hidden; `aria-busy="true"` on container.
- **empty** — no data or all-null series; empty slot shown.
- **error** — adapter threw or data fetch failed; error part shown.
- **ready** — adapter rendered; render target visible.
- **point-focused** — a data point is focused; tooltip shown; `aria-activedescendant`
  points to the focused data cell in the data table.
- **legend-hidden-series** — a series is toggled off via its legend item;
  reflected in adapter re-render and data table row `aria-hidden`.

## 11. Behavior & interactions

On `connectedCallback` the component:
1. Resolves the render target (`<canvas>` or adapter-specified element type).
2. Calls `adapter.render(target, data, adapterOptions)`.
3. Attaches a `ResizeObserver` to the container; on resize calls `adapter.resize()`.
4. Builds the accessible data table from `data` (always in the shadow DOM, visually
   hidden unless `show-table` is set).
5. Builds the HTML legend from `data.series`; each legend item is a `<button>`
   that toggles the series via `adapter` and fires `mj-chart-legend-toggle`.

When `data` property changes, the component calls `adapter.render()` again and
rebuilds the data table and legend.

Keyboard-reachable tooltips: the data table `<td>` cells are the keyboard-accessible
data point targets. When a cell receives focus the component fires
`mj-chart-point-focus` and requests the adapter to highlight the corresponding
visual point. The tooltip is positioned near the render target at the adapter's
reported point coordinates.

Color-independent encoding: every series has both a `--mj-chart-series-N` color
token and a `--mj-chart-series-N-pattern` fill pattern token. The adapter is
responsible for applying these. Legend items show a colored+patterned swatch that
matches the series encoding so users who cannot distinguish colors can still
identify series.

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| `Tab` | Move focus into the chart; first stop is the data table region |
| `←` / `→` | Move focus between data points within a series (via data table cell navigation) |
| `↑` / `↓` | Move focus between series |
| `Enter` / `Space` | Select focused data point; fire `mj-chart-point-select` |
| `Escape` | Clear selection; fire `mj-chart-point-deselect` |
| `Tab` (within legend) | Move focus between legend toggle buttons |
| `Space` (on legend item) | Toggle series visibility |

## 13. Accessibility

- The component renders `role="figure"` with `aria-label` set to `title` + `description`.
- The accessible data table is always present in the shadow DOM; it has a
  `<caption>` matching the chart title. Column headers use `scope="col"` and
  row headers use `scope="row"`.
- Series are never distinguished by color alone: each series also has a distinct
  pattern (dashes, dots, cross-hatch) encoded through the adapter and the
  `--mj-chart-series-N-pattern` tokens.
- The legend items are `<button>` elements with `aria-pressed` indicating visibility.
- When a data point is focused, `aria-live="polite"` region announces the value
  and series name (e.g. "Q3 Revenue: $1.2M, Series: North America").
- The render target (`<canvas>`) carries `aria-hidden="true"` because all
  accessible content is in the data table and live region.
- The chart region has `tabindex="0"` so it can receive focus before Tab enters
  the data table.

## 14. Form participation

N/A — `<mj-chart>` is a display component with no form value.

## 15. Internationalization & RTL

- Axis tick values and tooltip numbers are formatted via `Intl.NumberFormat` using
  the `locale` attribute or document locale.
- Date axis ticks use `Intl.DateTimeFormat`.
- In RTL mode the X-axis reads right-to-left; the adapter receives an `rtl` flag
  in `adapterOptions`; the legend layout flips via `dir="rtl"` on its container.
- All user-facing strings (loading, error, empty messages; legend toggle labels)
  are overridable via the localization hook (§3.8).

## 16. Progressive enhancement / SSR

The server may render a `<table>` inside `<mj-chart>` as a light-DOM child; the
component promotes this as its data table on upgrade. Without scripting the table
remains visible as the fallback data representation.

## 17. Dependencies

- **Registry + base element helper** (§6) — lifecycle, attribute reflection.
- **Design-token stylesheet** (§6) — color, typography, and pattern tokens.
- **Live-region service** (§6) — data point focus announcements.
- **Localization hook** (§6) — all user-facing strings.
- **Overlay/positioning engine** (§6) — tooltip positioning.
- **Data-source adapter interface** (§6) — async/paged data loading for large datasets.
- **Pluggable rendering adapter** — supplied by the host application; not bundled.

## 18. Edge cases & error handling

- No `adapter` set: renders only the data table; logs a console warning.
- `adapter.render()` throws: catches the error, shows the error state, fires
  `mj-chart-error`; does not rethrow.
- `data.series` is empty or `data.labels` has zero entries: shows empty state.
- All values in a series are `null` or `NaN`: treated as gaps in line/area charts;
  skipped in bar/pie; documented in the adapter contract.
- Container resized to zero width: `ResizeObserver` callback skips render; waits
  for non-zero size.
- `type` attribute changed at runtime: calls `adapter.destroy()` then
  `adapter.render()` with the new type; rebuilds table and legend.
- More than 8 series: series beyond index 8 cycle through the token palette;
  console warning logged recommending a smaller series count for readability.

## 19. Acceptance criteria

- [ ] All seven `type` values render without error when a compatible adapter is supplied.
- [ ] `data` property change triggers adapter re-render and table rebuild.
- [ ] Accessible data table is always in the shadow DOM; caption matches `title`.
- [ ] Series are distinguished by both color and pattern (no color-only encoding).
- [ ] Legend items are `<button>` with `aria-pressed`; toggling hides/shows series.
- [ ] Keyboard navigation through data table cells fires `mj-chart-point-focus`.
- [ ] `Enter`/`Space` on a focused cell fires `mj-chart-point-select`.
- [ ] Data point focus is announced via live region with value and series name.
- [ ] `ResizeObserver` triggers `adapter.resize()` on container size change.
- [ ] `show-table` reveals the data table visually.
- [ ] Number and date formatting respects `locale` attribute and `Intl` APIs.
- [ ] RTL layout reverses axis direction and legend order.
- [ ] Adapter error is caught; `mj-chart-error` fires; error state is shown.
- [ ] No-adapter fallback shows data table with a warning logged.
- [ ] Automated accessibility checks pass with no violations.

## 20. Open questions

- Should the adapter interface be defined as a TypeScript interface in a shared
  types package, or documented only as a duck-typed contract?
- Should `<mj-chart>` own an optional async data-fetch URL attribute, or should
  data always be provided via the `data` property?
- Should the heatmap type share the row/column model of the data table, or require
  a distinct `{ x, y, value }` flat array format?
