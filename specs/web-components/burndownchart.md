# Burndown Chart Spec

- **Tag:** `<mj-burndown-chart>`
- **Class / file:** `BurndownChart` / `burndownchart.js`
- **Category:** Project-management & configuration-management charts
- **Primary or Variant:** Primary
- **Synonyms covered:** Burndown chart, Burnup chart, Sprint burndown
- **Phase:** P3
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-burndown-chart>` renders remaining work (burndown) or completed work
(burnup) over the days of a sprint or release, plotted against an ideal
progress line. It surfaces scope-change events and shows whether the team is
on track to finish by the sprint end date. A burnup variant tracks cumulative
completed work instead of remaining work, making scope changes clearly visible
as a gap between total-scope and completed-work lines.

## 2. When to use / when not to use

**Use** for sprint-level or release-level work-remaining tracking. **Do not use**
for cross-sprint velocity trends (use `<mj-velocity-chart>`) or multi-state
work-item flow (use `<mj-cumulative-flow>`). Nearest alternatives:
`<mj-velocity-chart>` for aggregated iteration comparisons.

## 3. Anatomy

- **Time axis** — shared horizontal ruler spanning sprint start to end; driven
  by the time-axis utility; locale-aware tick labels.
- **Value axis** — vertical axis showing story points, hours, or issue count;
  labeled with unit.
- **Ideal line** — straight line from total scope on day 0 to zero on the last
  day (burndown) or from zero to total scope (burnup).
- **Actual line** — plotted from actual daily remaining (burndown) or completed
  (burnup) values.
- **Scope-change indicators** — vertical markers on dates where scope was added
  or removed; labeled with delta.
- **Today marker** — vertical line at the current date.
- **Data points** — interactive dots on the actual line; show date and value on
  hover/focus.
- **Accessible data table** — `<table>` of daily values always in DOM.

## 4. Variants & modes

| Mode / Variant | Attribute | Behavior |
|---|---|---|
| Burndown | `mode="burndown"` (default) | Y-axis shows remaining work; ideal line descends |
| Burnup | `mode="burnup"` | Y-axis shows completed work; ideal line ascends; second line shows total scope |
| Story points | `unit="points"` (default) | Y-axis unit is story points |
| Hours | `unit="hours"` | Y-axis unit is hours |
| Issue count | `unit="issues"` | Y-axis unit is issue count |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `src` | string | `""` | yes | URL for the data-source adapter |
| `adapter` | string | `"static"` | yes | Adapter key: `"static"`, `"jira"`, `"linear"`, `"github"` |
| `mode` | `"burndown"` \| `"burnup"` | `"burndown"` | yes | Chart variant |
| `unit` | `"points"` \| `"hours"` \| `"issues"` | `"points"` | yes | Work unit for Y axis |
| `start-date` | string (ISO 8601) | `""` | yes | Sprint/release start date |
| `end-date` | string (ISO 8601) | `""` | yes | Sprint/release end date |
| `today-marker` | boolean | `true` | yes | Show today vertical line |
| `show-ideal` | boolean | `true` | yes | Show ideal progress line |
| `show-scope-changes` | boolean | `true` | yes | Show scope-change markers |
| `locale` | string | `""` | yes | BCP 47 locale for axis labels |
| `label-loading` | string | `"Loading chart…"` | yes | Loading message |
| `label-empty` | string | `"No sprint data."` | yes | Empty message |
| `label-error` | string | `"Failed to load chart."` | yes | Error message |

## 6. Properties

| Property | Type | Description |
|----------|------|-------------|
| `data` | `BurndownData` | `{ startDate, endDate, totalScope, dailyValues: DayValue[], scopeChanges: ScopeChange[] }` |
| `selectedPoint` | `DayValue \| null` | Currently focused data point |

## 7. Slots

| Slot | Description |
|------|-------------|
| `(default)` | Fallback `<table>` rendered before upgrade |
| `point-detail` | Custom tooltip/popover content for a selected data point |
| `empty` | Shown when no daily data is present |
| `loading` | Shown during adapter fetch |
| `error` | Shown on adapter failure |

## 8. Events

| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-point-select` | `{ point: DayValue }` | yes | no | Data point activated |
| `mj-point-deselect` | `{}` | yes | no | Selection cleared |
| `mj-data-load` | `{ days: number, unit: string }` | yes | no | Data loaded successfully |
| `mj-error` | `{ message: string, cause: unknown }` | yes | no | Adapter error |

## 9. CSS parts & custom properties

**Parts:**
- `::part(time-axis)` — horizontal date ruler
- `::part(value-axis)` — vertical work-unit ruler
- `::part(ideal-line)` — ideal progress line SVG path
- `::part(actual-line)` — actual progress line SVG path
- `::part(scope-line)` — total scope line in burnup mode
- `::part(data-point)` — individual dot on the actual line
- `::part(scope-change-marker)` — vertical scope-change indicator
- `::part(today-marker)` — today vertical line
- `::part(legend)` — line legend

**Custom properties:**
- `--mj-ideal-line-color` — ideal line stroke (default token: `--mj-color-neutral-40`)
- `--mj-actual-line-color` — actual line stroke (default token: `--mj-color-primary`)
- `--mj-scope-line-color` — total-scope line in burnup (default token: `--mj-color-warning`)
- `--mj-scope-change-color` — scope-change marker color
- `--mj-today-color` — today marker color
- `--mj-point-radius` — data point circle radius (default `4px`)
- `--mj-line-stroke-width` — line stroke width (default `2px`)

## 10. States

- **loading** — `aria-busy="true"`; loading slot shown.
- **empty** — empty slot shown.
- **error** — error slot shown.
- **on-track** — actual line at or below (burndown) / above (burnup) ideal line.
- **behind** — actual line above (burndown) / below (burnup) ideal line; no color-only
  encoding: "Behind" text badge in chart header.
- **point-selected** — data point circle enlarged; detail popover open.
- **future-days** — data points after today are not plotted (null values); line
  ends at today.

## 11. Behavior & interactions

On load the adapter returns `BurndownData` for the given sprint/release. The
rendering adapter draws ideal and actual lines using SVG `<polyline>` elements.
Data points are SVG `<circle>` elements with `tabindex` and `role="button"`.
Hovering or focusing a data point fires `mj-point-select` and opens the detail
popover showing date and remaining/completed value. Scope-change markers are
vertical `<line>` elements with a label showing the delta (e.g. "+3 points").
The ideal line is recalculated if scope changes are present in the data.

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| `Tab` | Move focus to the data-point series, then to scope-change markers |
| `Arrow Left` / `Arrow Right` | Move focus between data points in date order |
| `Enter` / `Space` | Activate focused data point (open detail popover) |
| `Escape` | Close detail popover; deselect point |
| `Home` / `End` | Focus first / last data point |

## 13. Accessibility

- Root: `role="img"` with `aria-label` = "Burndown chart: sprint {name},
  {start} to {end}, unit: {unit}".
- Data points: `role="button"` with `aria-label` = "Day {date}: {value} {unit}
  remaining" (burndown) or "completed" (burnup).
- Ideal line: `aria-hidden="true"` with a text description in the legend:
  "Ideal: linear progress from {total} to 0".
- Scope-change markers: `aria-label` = "Scope change on {date}: {+/-n} {unit}".
- Legend items include text labels ("Ideal", "Actual") not just colored swatches.
- Accessible data table: columns Date, Remaining/Completed, Ideal, Scope Change.
- "Behind schedule" state announced via live region if data updates change status.

## 14. Form participation

N/A.

## 15. Internationalization & RTL

- Axis tick labels use `Intl.DateTimeFormat` and `Intl.NumberFormat` with
  `locale` attribute.
- Unit labels ("points", "hours", "issues") overridable via `label-unit-points`,
  `label-unit-hours`, `label-unit-issues` attributes.
- All UI strings overridable: `label-loading`, `label-empty`, `label-error`,
  `label-today`, `label-ideal`, `label-actual`, `label-scope`.
- RTL: time axis flows right-to-left; SVG lines mirror; value axis moves to the
  right side.

## 16. Progressive enhancement / SSR

Server renders a `<table>` of daily values inside the default slot. On upgrade
the component hides the table visually and draws the chart without layout shift.

## 17. Dependencies

- §6 time-axis utility
- §6 data-source adapter interface (adapter keys: `static`, `jira`, `linear`,
  `github`)
- §6 registry + base element helper
- §6 design-token stylesheet
- §6 overlay/positioning engine (data point detail popover)
- §6 live-region/announcement service
- §6 localization/formatting hook
- §5.9 pluggable rendering adapter (SVG line chart)

## 18. Edge cases & error handling

- **No data points** — empty slot shown; ideal line still rendered if
  `start-date`/`end-date` are set.
- **Single data point** — one dot; no connecting line.
- **Scope increases past original total** — Y axis rescales; ideal line
  recalculated from the new scope total.
- **Sprint end in the past** — today marker absent; full line rendered.
- **Adapter failure** — error slot shown; stale data retained.
- **Negative remaining work** — clamped to 0 with a warning in the console.

## 19. Acceptance criteria

- [ ] Actual line renders from daily `data.dailyValues` at correct positions.
- [ ] Ideal line descends (burndown) or ascends (burnup) linearly.
- [ ] Scope-change markers appear at correct dates with delta labels.
- [ ] Today marker appears at the current date.
- [ ] Selecting a data point fires `mj-point-select` and opens popover.
- [ ] Keyboard navigation per §12 moves through data points.
- [ ] Accessible data table present with date, value, and ideal columns.
- [ ] "Behind schedule" state uses text badge, not color alone.
- [ ] Burnup mode shows total-scope line in addition to completed line.
- [ ] RTL layout mirrors correctly.
- [ ] axe automated accessibility check passes with zero violations.

## 20. Open questions

- Should scope-change events link to the specific issues added/removed, requiring
  a deep-link attribute on each `ScopeChange` object?
- Is a combined burndown+burnup dual-axis view useful, or is toggling `mode`
  sufficient?
