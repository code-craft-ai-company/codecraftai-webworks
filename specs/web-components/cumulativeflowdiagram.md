# Cumulative Flow Diagram Spec

- **Tag:** `<mj-cumulative-flow>`
- **Class / file:** `CumulativeFlow` / `cumulativeflow.js`
- **Category:** Project-management & configuration-management charts
- **Primary or Variant:** Primary
- **Synonyms covered:** Cumulative flow diagram, CFD
- **Phase:** P3
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-cumulative-flow>` renders a stacked area chart where each area represents
the count of work items in a workflow state (e.g. Backlog, In Progress, In
Review, Done) over time. It exposes WIP (work-in-progress) width and approximate
lead-time height as interactive callouts, giving teams insight into flow
efficiency and bottlenecks.

## 2. When to use / when not to use

**Use** to analyze flow efficiency across workflow states over a sprint or
release. **Do not use** for simple remaining-work tracking (use
`<mj-burndown-chart>`) or per-sprint velocity (use `<mj-velocity-chart>`).
Nearest alternative: `<mj-burndown-chart>` for remaining work only.

## 3. Anatomy

- **Time axis** — shared horizontal ruler; time-axis utility; today marker.
- **Value axis** — vertical axis showing total work-item count.
- **State bands** — stacked SVG area paths, one per workflow state; ordered
  from bottom (earliest state, e.g. Backlog) to top (latest state, e.g. Done).
- **WIP callout** — horizontal bracket annotation spanning the horizontal width
  of the "In Progress" band at the current date; labeled with WIP count.
- **Lead-time callout** — vertical bracket annotation spanning the vertical
  height of a selected band column; labeled with approximate lead time in days.
- **Data points** — per-day values on each band boundary; focusable.
- **Legend** — maps band color + pattern to state label.
- **Accessible data table** — `<table>` of daily per-state counts.

## 4. Variants & modes

| Mode / Variant | Attribute | Behavior |
|---|---|---|
| Stacked area | `type="area"` (default) | Smooth stacked area paths |
| Stacked step | `type="step"` | Step-interpolated stacked areas (daily resolution) |
| Normalized | `normalized` (boolean) | Y axis shows percentage share rather than count |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `src` | string | `""` | yes | URL for the data-source adapter |
| `adapter` | string | `"static"` | yes | Adapter key: `"static"`, `"jira"`, `"linear"`, `"github"` |
| `type` | `"area"` \| `"step"` | `"area"` | yes | Area interpolation style |
| `normalized` | boolean | `false` | yes | Show percentage share on Y axis |
| `start-date` | string (ISO 8601) | `""` | yes | Left bound |
| `end-date` | string (ISO 8601) | `""` | yes | Right bound |
| `today-marker` | boolean | `true` | yes | Show today vertical line |
| `show-wip-callout` | boolean | `true` | yes | Show WIP annotation |
| `show-lead-time-callout` | boolean | `true` | yes | Show lead-time annotation |
| `locale` | string | `""` | yes | BCP 47 locale for axis labels |
| `label-loading` | string | `"Loading diagram…"` | yes | Loading message |
| `label-empty` | string | `"No flow data."` | yes | Empty message |
| `label-error` | string | `"Failed to load diagram."` | yes | Error message |

## 6. Properties

| Property | Type | Description |
|----------|------|-------------|
| `data` | `CFDData` | `{ states: WorkflowState[], dailySeries: DaySeries[] }` |
| `selectedDate` | `string \| null` | ISO date of the focused column |
| `hiddenStates` | `Set<string>` | State IDs toggled off via legend |

## 7. Slots

| Slot | Description |
|------|-------------|
| `(default)` | Fallback `<table>` rendered before upgrade |
| `column-detail` | Custom popover for a selected date column |
| `empty` | Shown when no daily series data is present |
| `loading` | Shown during adapter fetch |
| `error` | Shown on adapter failure |

## 8. Events

| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-column-select` | `{ date: string, values: Record<string, number> }` | yes | no | A date column focused/activated |
| `mj-column-deselect` | `{}` | yes | no | Column deselected |
| `mj-state-toggle` | `{ stateId: string, visible: boolean }` | yes | no | Legend item toggled |
| `mj-data-load` | `{ states: number, days: number }` | yes | no | Data loaded |
| `mj-error` | `{ message: string, cause: unknown }` | yes | no | Adapter error |

## 9. CSS parts & custom properties

**Parts:**
- `::part(time-axis)` — horizontal ruler
- `::part(value-axis)` — vertical ruler
- `::part(state-band)` — individual stacked area path (one per state)
- `::part(wip-callout)` — WIP annotation bracket
- `::part(lead-time-callout)` — lead-time annotation bracket
- `::part(today-marker)` — today line
- `::part(legend)` — legend container
- `::part(legend-item)` — individual legend row

**Custom properties:**
- `--mj-cfd-band-opacity` — area fill opacity (default `0.85`)
- `--mj-cfd-stroke-width` — band boundary stroke width (default `1.5px`)
- `--mj-today-color` — today marker color
- `--mj-wip-callout-color` — WIP bracket color
- `--mj-lead-time-callout-color` — lead-time bracket color
- `--mj-axis-tick-color` — tick label color

State band colors are assigned from a token palette (`--mj-color-cfd-band-1`
through `--mj-color-cfd-band-8`) in order of state definition; each is also
distinguished by a fill pattern for non-color accessibility.

## 10. States

- **loading** — `aria-busy="true"`; loading slot shown.
- **empty** — empty slot shown.
- **error** — error slot shown.
- **column-selected** — vertical line appears on selected date; column detail
  popover open.
- **state-hidden** — a legend item toggled off; corresponding band removed from
  chart; band label has `aria-pressed="false"` on legend button.

## 11. Behavior & interactions

The rendering adapter draws stacked area SVG paths. The y-value for each band is
the cumulative sum of all states at or below it. Hovering or focusing a date
column selects it and shows per-state counts. WIP is computed as the horizontal
span from the left boundary to the right boundary of the "In Progress" (or
equivalent configured) state band at the selected date. Lead time is the
vertical distance from bottom to top of the stacked area at a representative
point. Legend items are toggle buttons; hiding a state removes its band and
recalculates the stack.

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| `Tab` | Move focus to legend items, then to the chart area, then to individual date columns |
| `Arrow Left` / `Arrow Right` | Move focus between date columns |
| `Enter` / `Space` | Select focused column; toggle legend item |
| `Escape` | Deselect column; close popover |
| `Home` / `End` | Jump to first / last date column |

## 13. Accessibility

- Root: `role="img"` with `aria-label` = "Cumulative flow diagram: {n} states,
  {start} to {end}".
- Legend items: `role="button"` with `aria-pressed` for toggle state;
  `aria-label` = "{state name}, currently {visible|hidden}".
- Date columns: `role="button"` with `aria-label` = "{date}: {state1}: {n1},
  {state2}: {n2}, …".
- State bands use both color and fill pattern (hatching, dots) to distinguish
  them; pattern definitions live in an `<svg><defs>` block.
- WIP callout: `aria-label` = "WIP on {date}: {n} items".
- Lead-time callout: `aria-label` = "Approximate lead time: {n} days".
- Accessible data table: columns Date plus one column per workflow state.

## 14. Form participation

N/A.

## 15. Internationalization & RTL

- Axis tick labels use `Intl.DateTimeFormat` and `Intl.NumberFormat` with
  `locale` attribute.
- Localizable UI strings (attributes): `label-loading`, `label-empty`,
  `label-error`, `label-today`, `label-wip`, `label-lead-time`,
  `label-show-table`.
- RTL: time axis flows right-to-left; SVG area paths mirror; value axis moves to
  right side.

## 16. Progressive enhancement / SSR

Server renders a `<table>` inside the default slot. On upgrade the table is
hidden visually (re-accessible via toggle) and the SVG chart is drawn.

## 17. Dependencies

- §6 time-axis utility
- §6 data-source adapter interface (adapter keys: `static`, `jira`, `linear`,
  `github`)
- §6 registry + base element helper
- §6 design-token stylesheet
- §6 overlay/positioning engine (column detail popover)
- §6 localization/formatting hook
- §5.9 pluggable rendering adapter (SVG stacked area)

## 18. Edge cases & error handling

- **Single state** — only one band; no stacking needed; chart degrades to a
  simple area chart.
- **Missing days** — gaps in `dailySeries` treated as repeating the previous
  day's values; gap annotated visually with a dashed boundary.
- **All items in Done** — only the Done band visible; WIP callout shows 0.
- **Adapter failure** — error slot shown; stale data retained.
- **More than 8 states** — states beyond 8 merged into an "Other" band with a
  distinct pattern.

## 19. Acceptance criteria

- [ ] Stacked area bands render in correct order from `data.states`.
- [ ] Band colors and patterns are both distinct for each state.
- [ ] WIP callout shows correct count on the current date.
- [ ] Lead-time callout shows approximate days.
- [ ] Legend toggle hides/shows bands and fires `mj-state-toggle`.
- [ ] Selecting a column fires `mj-column-select` with per-state counts.
- [ ] Keyboard navigation per §12 moves through columns.
- [ ] Accessible data table present with all dates and state counts.
- [ ] Normalized mode switches Y axis to percentage.
- [ ] RTL layout mirrors correctly.
- [ ] axe automated accessibility check passes with zero violations.

## 20. Open questions

- Should WIP and lead-time callouts be computed from configurable state-name
  mappings, or is there a standard "in-progress" state concept in the data model?
- Is a cycle-time scatter plot overlay (individual item dots) in scope for the
  same component, or a separate visualization?
