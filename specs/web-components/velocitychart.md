# Velocity Chart Spec

- **Tag:** `<mj-velocity-chart>`
- **Class / file:** `VelocityChart` / `velocitychart.js`
- **Category:** Project-management & configuration-management charts
- **Primary or Variant:** Primary
- **Synonyms covered:** Velocity chart, Sprint velocity
- **Phase:** P3
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-velocity-chart>` renders a grouped bar chart of committed versus completed
work per iteration (sprint or release), with a rolling-average line overlaid.
It gives teams and stakeholders a historical view of throughput to inform
planning and capacity decisions.

## 2. When to use / when not to use

**Use** to compare sprint-over-sprint delivery throughput and to visualize the
difference between committed and completed work. **Do not use** for in-sprint
remaining work (use `<mj-burndown-chart>`) or for cumulative state counts (use
`<mj-cumulative-flow>`). Nearest alternative: `<mj-burndown-chart>` for a single
sprint focus.

## 3. Anatomy

- **Sprint axis** — horizontal axis with one tick per sprint/iteration label;
  not a continuous time axis but uses the time-axis utility for zoom/scroll when
  there are many sprints.
- **Value axis** — vertical axis showing story points, hours, or issue count.
- **Committed bars** — lighter grouped bars showing story points committed at
  sprint start.
- **Completed bars** — darker grouped bars showing story points actually completed.
- **Rolling-average line** — SVG polyline overlaid at the rolling mean of
  completed values over the last N sprints (configurable).
- **Sprint labels** — names/numbers below each bar group.
- **Accessible data table** — `<table>` of per-sprint values.
- **Legend** — maps committed/completed bars and average line to labels.

## 4. Variants & modes

| Mode / Variant | Attribute | Behavior |
|---|---|---|
| Grouped bars | `bar-mode="grouped"` (default) | Committed and completed bars side by side |
| Stacked bars | `bar-mode="stacked"` | Completed stacked on committed; gap visible as uncommitted |
| Story points | `unit="points"` (default) | Y-axis unit is story points |
| Hours | `unit="hours"` | Y-axis unit is hours |
| Issue count | `unit="issues"` | Y-axis unit is issue count |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `src` | string | `""` | yes | URL for the data-source adapter |
| `adapter` | string | `"static"` | yes | Adapter key: `"static"`, `"jira"`, `"linear"`, `"github"` |
| `unit` | `"points"` \| `"hours"` \| `"issues"` | `"points"` | yes | Work unit for Y axis |
| `bar-mode` | `"grouped"` \| `"stacked"` | `"grouped"` | yes | Bar layout |
| `rolling-window` | number | `3` | yes | Number of sprints for the rolling average |
| `show-average` | boolean | `true` | yes | Show rolling-average line |
| `show-committed` | boolean | `true` | yes | Show committed bars |
| `max-sprints` | number | `20` | yes | Number of sprints visible before scroll activates |
| `locale` | string | `""` | yes | BCP 47 locale for axis labels |
| `label-loading` | string | `"Loading velocity chart…"` | yes | Loading message |
| `label-empty` | string | `"No sprint data."` | yes | Empty message |
| `label-error` | string | `"Failed to load velocity."` | yes | Error message |

## 6. Properties

| Property | Type | Description |
|----------|------|-------------|
| `data` | `VelocityData` | `{ sprints: SprintResult[] }` where each has `{ id, name, committed, completed, startDate, endDate }` |
| `selectedSprint` | `SprintResult \| null` | Currently selected sprint |
| `rollingAverage` | `number[]` | Computed rolling averages per sprint (read-only) |

## 7. Slots

| Slot | Description |
|------|-------------|
| `(default)` | Fallback `<table>` rendered before upgrade |
| `sprint-detail` | Custom popover/detail for a selected sprint bar group |
| `empty` | Shown when no sprint data is present |
| `loading` | Shown during adapter fetch |
| `error` | Shown on adapter failure |

## 8. Events

| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-sprint-select` | `{ sprint: SprintResult }` | yes | no | Sprint bar group activated |
| `mj-sprint-deselect` | `{}` | yes | no | Selection cleared |
| `mj-data-load` | `{ sprints: number, unit: string }` | yes | no | Data loaded successfully |
| `mj-error` | `{ message: string, cause: unknown }` | yes | no | Adapter error |

## 9. CSS parts & custom properties

**Parts:**
- `::part(sprint-axis)` — horizontal sprint label axis
- `::part(value-axis)` — vertical work-unit axis
- `::part(committed-bar)` — committed work bar
- `::part(completed-bar)` — completed work bar
- `::part(average-line)` — rolling-average SVG polyline
- `::part(bar-group)` — wrapper for one sprint's bars
- `::part(legend)` — legend container

**Custom properties:**
- `--mj-committed-bar-color` — committed bar fill color
- `--mj-completed-bar-color` — completed bar fill color
- `--mj-average-line-color` — rolling average line stroke
- `--mj-average-line-width` — rolling average stroke width (default `2px`)
- `--mj-bar-radius` — bar corner radius (default `3px`)
- `--mj-bar-gap` — gap between committed and completed bars in grouped mode (default `4px`)
- `--mj-axis-tick-color` — tick label color

## 10. States

- **loading** — `aria-busy="true"`; loading slot shown.
- **empty** — empty slot shown.
- **error** — error slot shown.
- **sprint-selected** — bar group highlighted; detail popover open.
- **over-committed** — completed < committed by more than 20%; bar group
  labeled "Under-delivered" (text, not color-only).
- **exceeded** — completed > committed; "Exceeded" label on bar group.

## 11. Behavior & interactions

The rendering adapter draws grouped or stacked bar sets, one per sprint, in
chronological order left to right. The rolling average is computed client-side
from `data.sprints` over the `rolling-window` count. Clicking or pressing
Enter/Space on a bar group fires `mj-sprint-select` and opens the sprint-detail
popover showing committed, completed, difference, dates, and rolling average at
that point. When `max-sprints` is exceeded the axis scrolls horizontally; the
most recent sprint is visible by default.

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| `Tab` | Move focus to the chart area, then legend items |
| `Arrow Left` / `Arrow Right` | Move focus between sprint bar groups |
| `Enter` / `Space` | Activate focused sprint bar group |
| `Escape` | Deselect sprint; close popover |
| `Home` / `End` | Focus first / last sprint |

## 13. Accessibility

- Root: `role="img"` with `aria-label` = "Velocity chart: {n} sprints, unit:
  {unit}, rolling window: {rolling-window}".
- Bar groups: `role="button"` with `aria-label` = "Sprint {name}: committed {n},
  completed {m}, {under-delivered|exceeded|on target}".
- Committed and completed bars within a group are SVG `<rect>` elements with
  `aria-hidden="true"`; the group button carries all accessible information.
- Rolling-average line: `aria-hidden="true"` with a text description in the
  legend: "Rolling average ({rolling-window}-sprint): {current value} {unit}".
- Legend items include both color swatch and text label.
- Under-delivered state: labeled with text badge, not color alone.
- Accessible data table: columns Sprint, Committed, Completed, Difference,
  Rolling Average.

## 14. Form participation

N/A.

## 15. Internationalization & RTL

- Value axis labels use `Intl.NumberFormat` with `locale` attribute.
- Sprint names are rendered verbatim (consumer responsibility).
- All UI strings overridable: `label-loading`, `label-empty`, `label-error`,
  `label-committed`, `label-completed`, `label-average`, `label-show-table`,
  `label-unit-points`, `label-unit-hours`, `label-unit-issues`.
- RTL: sprint axis flows right-to-left (oldest sprint on right, newest on left);
  bar groups mirror.

## 16. Progressive enhancement / SSR

Server renders a `<table>` of sprint velocity data inside the default slot. On
upgrade the table is hidden visually (re-accessible via toggle) and the bar chart
is drawn without layout shift.

## 17. Dependencies

- §6 data-source adapter interface (adapter keys: `static`, `jira`, `linear`,
  `github`)
- §6 registry + base element helper
- §6 design-token stylesheet
- §6 overlay/positioning engine (sprint detail popover)
- §6 localization/formatting hook (`Intl.NumberFormat`)
- §5.9 pluggable rendering adapter (SVG bar chart)

## 18. Edge cases & error handling

- **Single sprint** — one bar group; rolling average equals the single completed
  value; no line rendered.
- **Committed = 0** — committed bar absent; completed bar shown alone.
- **Completed > committed significantly** — Y axis rescales; "Exceeded" label shown.
- **`rolling-window` larger than sprint count** — rolling average computed over
  available sprints; label clarifies "Average over {actual} sprints".
- **Adapter failure** — error slot shown; stale data retained.
- **More than `max-sprints`** — horizontal scroll activates; most recent sprint
  in view by default.

## 19. Acceptance criteria

- [ ] Committed and completed bars render for each sprint from `data.sprints`.
- [ ] Rolling-average line plots correct values at each sprint.
- [ ] `bar-mode="stacked"` stacks completed on committed.
- [ ] Selecting a sprint fires `mj-sprint-select` with full sprint data.
- [ ] Keyboard navigation per §12 moves between sprint groups.
- [ ] Accessible data table present with committed, completed, and average columns.
- [ ] Under-delivered sprints show text badge not color alone.
- [ ] `rolling-window` attribute changes the average calculation.
- [ ] RTL layout reverses sprint order correctly.
- [ ] axe automated accessibility check passes with zero violations.

## 20. Open questions

- Should `show-committed` defaulting to `false` be useful as a "completed only"
  velocity chart, or is that always misleading without the committed baseline?
- Is a "prediction band" (upper/lower confidence interval based on historical
  variance) in scope for P3?
