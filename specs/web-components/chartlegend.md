# Chart Legend Spec

- **Tag:** `<mj-chart-legend>`
- **Class / file:** `MjChartLegend` / `charts/mjchartlegend.js`
- **Category:** Media & visualization (§5.9) — chart part of `<mj-chart>`
- **Primary or Variant:** Primary (a companion part of `<mj-chart>`)
- **Synonyms covered:** Chart legend, Series legend, Color key, Series toggle
- **Phase:** P3 (ships with `<mj-chart>`; Phase 1 of `chart-components-plan.md` §7)
- **Status:** Implemented (this spec documents the shipped behavior of `mjchartlegend.js`)

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-chart-legend>` lists what the colors of a chart stand for. It is one of the
coordinated part elements of the chart library (`chart-components-plan.md` §3.3):
it binds to an `<mj-chart>` controller — by the controller's id in its `chart`
attribute, or as a descendant of the chart — and shows the legend entries the
controller built for its last render, each a color swatch and a label. An entry
that stands for a series is a toggle button: activating it hides or shows that
series through the controller's series-visibility API and emits
`mj-chart-legend-toggle`. An entry that only explains a color (a pie slice, a
category) is plain text. The legend is the "series labels not color-only" and
interactive series toggle of plan §5.9.

## 2. When to use / when not to use

Use with multi-series charts so users can identify each series and filter the
drawing, and with part-to-whole charts (pie, donut, waffle) as a color key. As a
separate element it can be placed beside the chart, docked, or laid out
vertically.

Do not use:
- for chart types that register no legend (`legend: "none"`: sankey, network,
  gauge, KPI, sparkline, maps, ...) — the element stays empty;
- as a general filter UI with many options or search — use `<mj-filter-panel>`
  or `<mj-checkbox-group>` and drive `hideSeries()` / `showSeries()` on the chart;
- for a continuous color scale (heatmaps, choropleths) — those renderers draw
  their own key.

## 3. Anatomy

- **Host element** — `display: block`.
- **legend (part)** — `<ul class="legend" role="list">`, a wrapping flex row (or
  a column).
- **entry (part)** — one `<li class="entry">` per legend entry.
- **item (part)** — inside each entry: a `<button type="button" class="item">`
  for a series entry (with `aria-pressed` and `data-index`), or a
  `<span class="item">` for a color-key entry.
- **swatch (part)** — `<span class="swatch" aria-hidden="true">`, a small square
  filled and bordered with the entry color.
- **label** (`<span class="label">`, not a part) — the entry text, after the
  swatch.

## 4. Variants & modes

| Mode | Selected by | Description |
|------|-------------|-------------|
| Horizontal (default) | `orientation` absent or any value other than `vertical` | Entries in a wrapping row |
| Vertical | `orientation="vertical"` | Entries in a column |
| Toggle entry | entry carries a `series` name | `<button>` with `aria-pressed`; activation hides/shows the series |
| Color-key entry | entry has no `series` | `<span>`; not interactive |

Which entries appear is decided by the chart for each render (§11): what the
renderer published (`ctx.setLegend`), else its type registration's `legend`
option — `"series"` (default: one toggle per series), `"categories"` (one
color-key entry per category: pie, donut, waffle), `"none"` (no entries), or a
function.

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `chart` | string (element id) | — | No | Id of the `<mj-chart>` to bind to (trimmed). Looked up in the legend's own root (document or shadow root), then in the document; an element that is not an `<mj-chart>` is ignored. Without it, or when it does not resolve, the nearest `<mj-chart>` ancestor is used (crossing shadow roots). Changing it rebinds |
| `orientation` | `horizontal\|vertical` | — (row) | No | Layout of the entries. CSS only: exactly `vertical` stacks them; any other value or none is a row. Independent of the chart's `orientation` |
| `disabled` | boolean | absent | No (the MjElement `disabled` property sets it) | Disables the toggle buttons (native `disabled`): they take neither focus nor activation, by pointer or keyboard, so no series can be toggled from this legend. The chart's own visibility API still works and the pressed states keep following it. Color-key entries are unaffected |

`chart` and `orientation` have no property. Common MjElement attributes (`dock`,
`anchor`, `theme`, `hidden`, `context-menu`) behave as on every component.

## 6. Properties

| Property | Type | Description |
|----------|------|-------------|
| `controller` | `MjChart \| null` (read-only) | The chart the legend is bound to (ChartPart mixin) |

**Methods**

| Method | Description |
|--------|-------------|
| `applyModel(model, context)` | Called by the controller with its model and render context (both `null` while the chart has nothing to show); caches them and redraws. Controller-facing; page code does not call it |

The legend exposes no entries API; series visibility is read and changed on the
chart (`hiddenSeries`, `isSeriesHidden()`, `hideSeries()`, `showSeries()`,
`toggleSeries()`, `showAllSeries()`).

## 7. Slots

N/A — the shadow root has no slot; light-DOM children are not rendered once the
element is upgraded.

## 8. Events

| Event | `detail` | Bubbles | Composed | Cancelable | Description |
|-------|----------|---------|----------|------------|-------------|
| `mj-chart-legend-toggle` | `{ series: string, seriesIndex: number, visible: boolean, hidden: boolean }` | Yes | Yes | No | Fires on the legend after a series entry was activated and the chart has applied the change. `series` is the series name; `seriesIndex` its position in the data (`sourceIndex`), `-1` when no series of that name exists; `visible` is the state after the toggle and `hidden` its negation |

Related chart event: `<mj-chart>` emits `mj-chart-series-toggle`
`{ series, seriesIndex, visible, hidden, hiddenSeries }` (bubbles, composed, not
cancelable) for every visibility change, including programmatic ones. On a legend
activation it fires first, on the chart, followed by `mj-chart-legend-toggle` on
the legend. A nested legend's event bubbles through the chart.

Programmatic visibility changes on the chart update the legend's pressed states
but do not emit `mj-chart-legend-toggle`.

## 9. CSS parts & custom properties

**Parts**
- `::part(legend)` — the list
- `::part(entry)` — each list item
- `::part(item)` — the toggle button or color-key span of each entry
- `::part(swatch)` — the color square of each entry

**Custom properties**

| Property | Default | Description |
|---|---|---|
| `--mj-chart-legend-swatch` | `var(--mj-accent, #2563eb)` | Swatch fill and border color. The legend sets it inline on each swatch from the entry color, and `<mj-chart>` gives every entry a color, so a value set from outside only shows for an entry without one. Restyle swatches through `::part(swatch)` |

Shared tokens read directly (fallbacks as in the CSS):

| Token | Fallback | Used for |
|---|---|---|
| `--mj-space-2` | `0.5rem` | Gap between entries and between swatch and label |
| `--mj-space-1` | `0.25rem` | Item padding |
| `--mj-font-size-sm` | `0.875rem` | Label size |
| `--mj-text` | `#14181f` | Label color |
| `--mj-text-muted` | `#5f6673` | Label color of a hidden series |
| `--mj-radius-sm` | `0.25rem` | Item corner radius |
| `--mj-bg-muted` | `#eef0f3` | Button hover background |
| `--mj-focus-ring-width` | `2px` | Focus outline width |
| `--mj-focus-ring` | `#4d83f7` | Focus outline color |

The swatch is `0.85rem` square with a `3px` radius (not tokenized).

## 10. States

| State | Visual effect | ARIA effect |
|-------|---------------|-------------|
| series shown | Filled swatch, normal label | `aria-pressed="true"` |
| series hidden | Hollow swatch (transparent fill, colored border), muted label, label struck through | `aria-pressed="false"` |
| color-key entry | Filled swatch, normal label, no hover | No role or state |
| hover (button) | `--mj-bg-muted` background, pointer cursor | — |
| focus-visible (button) | Outline `--mj-focus-ring-width` `--mj-focus-ring`, offset 1px | — |
| empty | No entries (unbound, chart empty or failed, type with no legend) | Empty list |
| `disabled` | Toggle buttons at `opacity: 0.55` with a not-allowed cursor; the base stylesheet also sets `pointer-events: none` on the host | The buttons are natively `disabled` (exposed as disabled, out of the tab order) |

## 11. Behavior & interactions

- **Binding** (ChartPart mixin): on connect the legend resolves its controller
  (§5 `chart`), registers with it (`registerPart`) and receives the chart's
  current model if it has one. A chart that is not upgraded yet, or enters the
  page or gets its id later, announces itself with `mj-chart-connect` and the
  legend binds then. On disconnect it unregisters.
- **Entries**: on every delivery the legend reads `context.legend` (the chart
  always supplies an array). Only without a context does it build one entry per
  series of the model itself (`allSeries`, else `series`), colored through
  `context.colorScale` when available and marked hidden from
  `model.hiddenSeries`.
- **Entries the chart builds** for a render, as `{ key, label, color, series,
  hidden }`: the renderer's published entries; else the type's declared `legend`
  option (§4); else one toggle per series, hidden ones included. Every entry gets
  a color (the renderer's, else the chart's `colorFor` palette by series name or
  label). Unknown chart type or a renderer exception: one toggle per series.
  Empty data: no entries. Data failure (fetch / parse) or chart removed: the
  model is `null` and the list is emptied.
- **In-place updates**: entries are fingerprinted by key (`<index>:<label>`) and
  kind (toggle / color key). When a render delivers the same fingerprint (a
  resize, a toggle) the existing items are updated in place — label text, swatch
  color, `aria-pressed` — so the focused button keeps focus. A different set of
  entries rebuilds the list.
- **Activation**: one delegated `click` listener on the list handles every
  button. Activating a toggle calls `controller.toggleSeries(series)` (nothing
  happens when the legend is unbound, is `disabled`, or the controller has no
  `toggleSeries`).
- **Disabled**: while `disabled` is present every toggle button carries the
  native `disabled` property, set again on each redraw and whenever the
  attribute changes; removing the attribute enables them again.
  The chart flips the series' hidden state by name, re-renders — synchronously
  for local data or an already-fetched `src`, when the response arrives for a
  `src` still loading — and broadcasts the new legend, which updates
  `aria-pressed`. The chart emits `mj-chart-series-toggle`; then the legend looks
  up `seriesIndex` in `controller.chartModel.allSeries` and emits
  `mj-chart-legend-toggle`.
- **Hidden state lives on the chart**: it is kept by series name across
  re-renders and data changes; the legend only displays it. Programmatic changes
  (`hideSeries`, `showSeries`, `toggleSeries`, `showAllSeries`) show up in the
  legend on the next render.
- **Effect on the chart**: while any `<mj-chart-legend>` is bound,
  `chart.hasLegendPart()` is true and the radar, parallel, bullet and
  streamgraph renderers leave out their inline key so series are not listed
  twice. The chart re-renders when the first legend binds or the last one leaves.
- **Zero-size chart**: when the chart's box is 0 x 0 (e.g. the chart is
  `hidden`), the renderer does not run, so the entries come from the type's
  declared `legend` option rather than renderer-published entries.
- **Layout when nested**: `<mj-chart>` styles slotted parts `flex: 0 0 auto`; a
  nested legend is drawn below the drawing, in source order among the nested
  legend and data-table parts.

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| `Tab` | Moves to the next toggle button (each toggle is its own tab stop; color-key entries are skipped) |
| `Shift+Tab` | Moves to the previous toggle button |
| `Enter` | Toggles the focused series (native button activation) |
| `Space` | Toggles the focused series (native button activation) |

There is no custom key handling: no arrow-key movement and no roving tabindex.
A `disabled` legend has no tab stops and handles no keys.

## 13. Accessibility

- The list is a `<ul>` with an explicit `role="list"` (kept although the list
  style is removed). It has no accessible name.
- A series entry is a native `<button>`; `aria-pressed="true"` means the series
  is shown, `"false"` that it is hidden. Its name is the entry label; the swatch
  is `aria-hidden="true"`.
- A hidden series is shown by a hollow swatch, a struck-through label and muted
  text, not by color alone (plan §5.9).
- A color-key entry is plain text in a list item; the color itself is not
  conveyed to assistive technology, the label names the category.
- The buttons have no `aria-controls` to the chart, and the chart's redraw is not
  announced (the chart is not a live region); the pressed state change on the
  focused button is the feedback.
- Focus stays on the activated button across the redraw as long as the entry set
  is unchanged.
- No minimum target size is enforced: a button is the label line plus
  `--mj-space-1` padding on each side.
- There is no `forced-colors` handling for the swatches.

## 14. Form participation

N/A. `<mj-chart-legend>` is not form-associated.

## 15. Internationalization & RTL

- The component has no built-in strings and uses no `t()` keys. Labels are series
  names, category labels or renderer-published labels from the data.
- A locale change re-renders the element (MjElement default `onLocaleChanged` →
  `renderAgain()`), which unregisters and re-registers it with the chart.
- The flex row follows the inline direction, so entry order and the
  swatch-before-label order mirror in RTL. No physical properties are used.

## 16. Progressive enhancement / SSR

There is nothing to server-render: the entries exist only once the chart has
rendered on the client. Because the shadow root has no slot, any light-DOM
content (for example a static server-rendered key) is visible before upgrade and
without script, and is no longer rendered once the element upgrades and the live
entries take over.

## 17. Dependencies

- **Registry + base element helper** (§6) — `MjElement` (`render`, `afterRender`,
  `listen`, `emit`, docking / anchoring, theming)
- **ChartPart mixin** — `charts/core/chartpart.js` and
  `charts/core/chartregistry.js` (`resolveController`, `mj-chart-connect`)
- **`<mj-chart>`** — `charts/mjchart.js`: `registerPart` / `unregisterPart`,
  `toggleSeries`, `chartModel`, `hasLegendPart`, legend entries
  (`_buildLegend`) and colors (`colorFor`, `seriesColor` from
  `charts/core/scales.js`). See [chart.md](chart.md): the controller has no
  legend of its own; the legend is this separate element,
  `mj-chart-legend-toggle` comes from it with
  `{ series, seriesIndex, visible, hidden }`, and the chart emits
  `mj-chart-series-toggle`.
- **Renderer registry** — `charts/core/renderregistry.js` (`legend` registration
  option, `ctx.setLegend`, `ctx.hasLegendPart`)
- **Design-token stylesheet** (§6)
- Registered by `charts/index.js` (`defineAll`).

## 18. Edge cases & error handling

- Duplicate series names: hidden state is kept by name, so toggling one entry
  hides or shows every series with that name.
- A renderer-published entry whose `series` names no series in the data: it is
  still a toggle; activating it records the name as hidden (the button shows
  not pressed) but nothing in the drawing changes, and `seriesIndex` is `-1`.
- Hiding every series is allowed; the chart is not treated as empty and every
  button shows `aria-pressed="false"`.
- Hidden names survive data replacement: a series with the same name in new data
  starts hidden.
- `src` still loading when a toggle is activated: the event fires at once with
  the new state; `aria-pressed` updates when that render paints.
- A renderer that publishes a different entry set after a toggle causes a
  rebuild, and focus on the activated button is lost.
- Long labels are not truncated; many entries wrap onto further rows. There is
  no scrolling or overflow affordance.
- Unbound legend: empty list; clicks do nothing.
- `disabled`: the buttons are natively disabled, so neither pointer nor
  keyboard (Tab, Enter, Space) reaches them; a button that had focus loses it.
  Programmatic `chart.hideSeries()` / `showSeries()` still update the pressed
  states.
- Chart removed from the page: the list is emptied; the legend stays registered
  and is filled again when the chart is re-inserted.
- A failure while the controller delivers a model is caught by the controller
  (console warning) and does not stop the chart or its other parts.

## 19. Acceptance criteria

- [ ] Bound to a multi-series chart, the legend shows one toggle button per series with the series color and name.
- [ ] Bound to a pie / donut / waffle, entries are color-key spans, not buttons.
- [ ] A type registered with `legend: "none"` gives an empty list.
- [ ] Activating a toggle hides the series in the chart; activating it again shows it.
- [ ] `aria-pressed` is `true` for a shown series and `false` for a hidden one; hidden entries have a hollow swatch and struck-through label.
- [ ] `mj-chart-legend-toggle` fires once per activation with `series`, `seriesIndex`, `visible`, `hidden`; it bubbles, is composed and is not cancelable.
- [ ] The chart's `mj-chart-series-toggle` fires before `mj-chart-legend-toggle`.
- [ ] `chart.hideSeries()` / `showSeries()` update `aria-pressed` without a legend event.
- [ ] Focus stays on the activated button after the chart redraws.
- [ ] Enter and Space toggle; Tab visits only the toggle buttons.
- [ ] With `disabled`, the buttons are disabled: Tab skips them and no series can be toggled from the legend; removing `disabled` restores them.
- [ ] `orientation="vertical"` stacks the entries; other values lay them out in a row.
- [ ] Binding works nested, by `chart` id, and when the chart is inserted or given its id later; changing `chart` rebinds.
- [ ] Binding a legend makes radar / parallel / bullet / streamgraph drop their inline key; removing it brings the key back.
- [ ] When the chart's data fails or the chart is removed, the list is emptied.
- [ ] axe scan zero violations with shown, hidden and color-key entries.
- [ ] Light, dark, high-contrast and RTL rendering verified.

## 20. Open questions

- Should the list get an accessible name (a localized "Legend", or the chart's
  name)?
- Should many entries use arrow-key movement with a roving tabindex instead of one
  tab stop per entry?
- Should the buttons reference the chart (`aria-controls`) or state the action in
  their name?
- Should hiding the last visible series be prevented?
- Should a cancelable request event precede the toggle?
- Should hidden names that are not in new data be dropped?
- Should the swatches support `forced-colors` (for example a system-color border)?
- Should `orientation` default from the chart's orientation or the dock edge?
