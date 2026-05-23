# Gantt Chart Spec

- **Tag:** `<mj-gantt-chart>`
- **Class / file:** `GanttChart` / `ganttchart.js`
- **Category:** Project-management & configuration-management charts
- **Primary or Variant:** Primary
- **Synonyms covered:** Gantt chart
- **Phase:** P3
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-gantt-chart>` renders a classic Gantt chart — task bars positioned on a
shared time axis with dependency arrows, percent-complete fills, milestone
diamonds, and phase bands. It serves as the primary tool for visualizing project
schedules and release plans in the webworks component library.

## 2. When to use / when not to use

**Use** for project schedules where start/end dates, task dependencies, and
completion status need to be visualized together. **Do not use** for a simple
list of milestones (use `<mj-milestone-timeline>`), for sprint velocity trends
(use `<mj-velocity-chart>`), or for CI pipeline stages (use
`<mj-pipeline-chart>`). Nearest alternative: `<mj-roadmap-chart>` for
initiative-level roadmaps without day-level precision.

## 3. Anatomy

- **Task list panel** — left column listing task names and optional metadata
  (assignee, status chip); collapsible.
- **Time axis** — shared horizontal ruler from the time-axis utility; supports
  zoom, pan, today marker, locale-aware tick labels.
- **Task bars** — horizontal bars spanning start-to-end per task; filled to
  show `% complete`.
- **Dependency arrows** — finish-to-start (and other) directed arrows between
  bars.
- **Milestone diamonds** — from the shared milestone/marker model; sit on the
  time axis above or on a specific task row.
- **Phase bands** — colored date-range backgrounds (e.g. design, development,
  QA, release).
- **Today marker** — vertical line indicating the current date.
- **Group rows** — collapsible parent rows that aggregate child tasks.
- **Accessible data table** — a visually hidden `<table>` of tasks always in DOM.

## 4. Variants & modes

| Mode / Variant | Attribute | Behavior |
|---|---|---|
| Day scale | `scale="day"` | Axis ticks at day intervals |
| Week scale | `scale="week"` (default) | Axis ticks at week intervals |
| Month scale | `scale="month"` | Axis ticks at month intervals |
| Quarter scale | `scale="quarter"` | Axis ticks at quarter intervals |
| Read-only | `readonly` (boolean, default) | No task editing or drag |
| Editable | `editable` (boolean) | Bar drag-to-reschedule and percent-complete handle |
| Compact | `density="compact"` | Reduced row height; no assignee chip |
| Full | `density="full"` (default) | Full row height with assignee and status chips |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `src` | string | `""` | yes | URL for the data-source adapter |
| `adapter` | string | `"static"` | yes | Adapter key: `"static"`, `"jira"`, `"linear"`, `"asana"` |
| `scale` | `"day"` \| `"week"` \| `"month"` \| `"quarter"` | `"week"` | yes | Time axis granularity |
| `start-date` | string (ISO 8601) | `""` | yes | Left bound of visible window |
| `end-date` | string (ISO 8601) | `""` | yes | Right bound of visible window |
| `today-marker` | boolean | `true` | yes | Show today vertical line |
| `show-dependencies` | boolean | `true` | yes | Render dependency arrows |
| `show-percent` | boolean | `true` | yes | Render % complete fill on bars |
| `editable` | boolean | `false` | yes | Enable bar drag and resize |
| `readonly` | boolean | `false` | yes | Alias; explicit read-only lock |
| `density` | `"compact"` \| `"full"` | `"full"` | yes | Row height variant |
| `locale` | string | `""` | yes | BCP 47 locale for axis tick formatting |
| `max-rows` | number | `500` | yes | Row count above which virtual scroll activates |

## 6. Properties

| Property | Type | Description |
|----------|------|-------------|
| `data` | `GanttData` | `{ tasks, groups, dependencies, markers, phases }` |
| `selectedTask` | `Task \| null` | Currently focused/selected task |
| `collapsedGroups` | `Set<string>` | IDs of collapsed group rows |
| `visibleRange` | `{ start: Date, end: Date }` | Current time window |

## 7. Slots

| Slot | Description |
|------|-------------|
| `(default)` | Fallback `<table>` rendered before upgrade |
| `task-detail` | Custom detail panel for a selected task |
| `toolbar` | Custom controls to slot above the chart (e.g. scale picker) |
| `empty` | Shown when `data.tasks` is empty |
| `loading` | Shown during adapter fetch |
| `error` | Shown on adapter failure |

## 8. Events

| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-task-select` | `{ task: Task }` | yes | no | Task row or bar focused/clicked |
| `mj-task-deselect` | `{}` | yes | no | Selection cleared |
| `mj-task-update` | `{ task: Task, changes: Partial<Task> }` | yes | yes | Bar drag/resize complete (editable mode) |
| `mj-group-toggle` | `{ groupId: string, collapsed: boolean }` | yes | no | Group row collapsed or expanded |
| `mj-range-change` | `{ start: string, end: string }` | yes | no | Visible time window changed |
| `mj-marker-select` | `{ marker: Marker }` | yes | no | Milestone marker activated |
| `mj-data-load` | `{ tasks: number, groups: number }` | yes | no | Data fetch succeeded |
| `mj-error` | `{ message: string, cause: unknown }` | yes | no | Adapter or validation error |

## 9. CSS parts & custom properties

**Parts:**
- `::part(task-list-panel)` — left column task list
- `::part(task-list-header)` — header row of task list column
- `::part(chart-area)` — scrollable bar area to the right
- `::part(time-axis)` — horizontal ruler
- `::part(task-row)` — individual task row across both panels
- `::part(task-bar)` — horizontal bar for a task
- `::part(task-bar-fill)` — inner fill showing % complete
- `::part(dependency-arrow)` — SVG arrow between dependent tasks
- `::part(milestone-marker)` — diamond and label
- `::part(phase-band)` — background phase span
- `::part(today-marker)` — today vertical line
- `::part(group-row)` — collapsible group header row

**Custom properties:**
- `--mj-gantt-row-height` — task row height (default `40px`)
- `--mj-gantt-task-list-width` — left panel width (default `260px`)
- `--mj-bar-color` — default task bar fill color
- `--mj-bar-complete-color` — % complete fill color
- `--mj-bar-milestone-color` — milestone diamond color
- `--mj-dependency-color` — dependency arrow stroke color
- `--mj-today-color` — today marker stroke color
- `--mj-phase-opacity` — phase band fill opacity (default `0.10`)
- `--mj-axis-tick-color` — tick label color

## 10. States

- **loading** — `aria-busy="true"`; loading slot shown.
- **empty** — empty slot shown.
- **error** — error slot shown; `mj-error` fired.
- **task-selected** — row highlighted; detail panel opens.
- **group-collapsed** — child rows hidden; group collapse button `aria-expanded="false"`.
- **editable** — cursor changes on bars; drag handles visible.
- **task-dragging** — bar currently being repositioned; live region announces new dates.

## 11. Behavior & interactions

The time-axis utility controls zoom (scroll wheel, pinch, ± buttons) and pan
(drag on axis, Arrow keys). Task bars are positioned by the rendering adapter
using `start`/`end` dates relative to the axis scale. Clicking a task row or
bar fires `mj-task-select` and opens the detail panel. Group rows toggle child
visibility via a disclosure button. In editable mode, drag-handle on bar ends
resizes; dragging the bar body repositions; dropping fires `mj-task-update`
(cancelable so the host can validate or revert). Dependency arrows are SVG paths
drawn from the right edge of the predecessor bar to the left edge of the
successor bar; they update on zoom/pan. Percent-complete fill is a nested div
with width set to `task.percentComplete + "%"`.

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| `Tab` | Move focus between task rows, group collapse buttons, toolbar controls, and milestone markers |
| `Arrow Up` / `Arrow Down` | Move focus between task rows |
| `Arrow Left` / `Arrow Right` | Scroll the chart area left/right; also adjusts bar dates in editable mode (by one `scale` unit) |
| `Enter` / `Space` | Select focused task; toggle group collapse |
| `Escape` | Deselect task; cancel pending bar drag |
| `+` / `-` | Zoom in / zoom out on the time axis |
| `0` | Reset zoom to fit all tasks |
| `Home` / `End` | Jump to first / last task row |
| `Page Up` / `Page Down` | Scroll task list by one viewport height |

## 13. Accessibility

- Root: `role="img"` with `aria-label` = "Gantt chart: {n} tasks, {start} to {end}".
- Task list panel: `role="treegrid"` with `aria-label` = "Task list".
- Each task row: `role="row"`; task name cell `role="rowheader"`.
- Group rows: `aria-expanded` on collapse button; `aria-controls` points to
  child row group.
- Task bars: `aria-label` = "{name}: {start} to {end}, {percent}% complete,
  status: {status}"; role is presentational inside the row.
- Milestone markers: `role="button"` with `aria-label` = "{name} milestone, {date}".
- Dependency arrows: `aria-hidden="true"` (visual only; relationship conveyed
  by data table).
- Accessible data table: columns Task, Start, End, % Complete, Status, Dependencies.
- Bar drag in editable mode: new dates announced via live-region as bar is dropped.
- Phase bands: `aria-hidden="true"`.

## 14. Form participation

N/A — this component is not an input control.

## 15. Internationalization & RTL

- Axis tick labels use `Intl.DateTimeFormat` with `locale` attribute.
- Localizable strings (all overridable via attributes): `label-loading`,
  `label-empty`, `label-error`, `label-today`, `label-collapse`, `label-expand`,
  `label-zoom-in`, `label-zoom-out`, `label-reset-zoom`, `label-show-table`.
- RTL: time axis flows right-to-left; task list panel moves to the right;
  dependency arrows mirror; bar fill grows from right to left.

## 16. Progressive enhancement / SSR

Server renders a `<table>` of tasks inside the default slot. Before the script
loads the table is the full accessible content. On upgrade the component hides
the table visually (accessible via a disclosure toggle), initializes the adapter,
and draws the Gantt without layout shift using `height-hint`.

## 17. Dependencies

- §6 time-axis utility (zoom, pan, today marker, locale-aware tick labels)
- §6 milestone/marker model
- §6 data-source adapter interface (adapter keys: `static`, `jira`, `linear`,
  `asana`)
- §6 registry + base element helper
- §6 design-token stylesheet
- §6 live-region/announcement service
- §6 localization/formatting hook
- §5.9 pluggable rendering adapter (SVG; injected, not bundled)

## 18. Edge cases & error handling

- **Tasks with no end date** — bar extends to the right edge of the viewport
  with a dashed border.
- **Overlapping tasks in the same row** — bars stack vertically within the row
  up to `max-overlap` (default 3); remaining tasks shown as "+N more".
- **Circular dependencies** — detected on load; warning emitted; affected arrows
  drawn in an error color.
- **`start-date` after `end-date`** — swapped with console warning.
- **Zero-duration task** (start equals end) — rendered as a milestone diamond
  regardless of task type.
- **Adapter failure** — error slot shown; stale data retained.
- **More than `max-rows` tasks** — virtual scroll activates; offscreen rows
  not rendered.
- **Long task names** — truncated in the task list panel with tooltip on hover/focus.

## 19. Acceptance criteria

- [ ] Task bars render at correct positions from static `data` property.
- [ ] Dependency arrows connect predecessor right-edge to successor left-edge.
- [ ] Percent-complete fill matches `task.percentComplete`.
- [ ] Today marker appears at the current date on the axis.
- [ ] Milestone diamonds render at correct dates with names.
- [ ] Phase bands span correct date ranges behind task bars.
- [ ] Group collapse toggles child rows and fires `mj-group-toggle`.
- [ ] Zoom changes axis tick labels and repositions bars.
- [ ] Keyboard navigation per §12 works across rows and toolbar.
- [ ] Accessible data table present with all tasks and dependency columns.
- [ ] In editable mode, bar drag fires `mj-task-update` with new dates.
- [ ] RTL layout mirrors correctly.
- [ ] axe automated accessibility check passes with zero violations.
- [ ] Empty, loading, and error states display correct slots.

## 20. Open questions

- Should `mj-task-update` carry only the changed fields or the full updated task
  object? Partial updates are easier for the host to merge but require careful
  diffing.
- Is a resource/assignee swim-lane grouping mode (tasks grouped by owner instead
  of hierarchy) in scope for P3?
- Should the critical path be highlighted automatically based on the dependency
  graph, or is that deferred to `<mj-dependency-graph>`?
