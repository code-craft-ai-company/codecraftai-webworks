# Gantt Chart Spec

- **Tag:** `<mj-gantt-chart>`
- **Class / file:** `MjGanttChart` / `components/mjganttchart.js` (base: `components/pmchartwrapper.js`)
- **Category:** Project-management & configuration-management charts
- **Primary or Variant:** Variant — a convenience wrapper for `<mj-chart type="gantt">`
- **Synonyms covered:** Gantt chart
- **Status:** Implemented (wrapper since WW-1498)

> `<mj-gantt-chart>` is `<mj-chart type="gantt">` with the type fixed and the
> project data shape of this component family. Drawing, layout, keyboard
> support, the data table, data loading (`data`, `src`, inline JSON), the
> loading / empty / error states and resizing are the chart's: see
> [chart.md](chart.md) (§21 for the gantt type) and the `gantt` chart-type page.
> This spec records only what differs. Universal requirements are in
> `web-component-development-plan.md` §3.

## 1. Purpose and when to use

A project schedule: task bars with percent-complete fills, finish-to-start
dependency arrows, collapsible group rows, milestone markers, phase bands and a
today line. Use it when the page already holds data in the shape below; use
`<mj-chart type="gantt">` directly for the chart type's own shape. For
initiative-level plans use `<mj-roadmap-chart>`, for a single axis of key dates
`<mj-milestone-timeline>`.

## 2. Data shape (mapped onto the chart type)

```
{ tasks: [{ id, name, start, end, percentComplete, status, groupId, milestone }],
  groups: [{ id, name }], dependencies: [{ from, to }],
  markers: [{ name, date }], phases: [{ name, start, end }] }
```

| Wrapper field | Chart type field |
|---|---|
| `task.name` (else `id`, else `task-N`) | `label`; `id` defaults to the name, else `task-N` |
| `task.percentComplete` (0-100, clamped; missing = 0) | `progress` (0-1) |
| `task.groupId` naming a declared group | `group` (an unknown id leaves the task ungrouped) |
| `dependencies: [{ from, to }]` | `depends` of the `to` task |
| `task.milestone` / `type: "milestone"` | `milestone: true` |
| `groups[].name`, `markers[].name`, `phases[].name` | `label` |

`YYYY-MM-DD` dates are local days and a date-only end is inclusive. A task with
a start and no end runs to the edge of the chart; one without dates keeps its
row ("No dates").

## 3. Attributes

| Attribute | Chart type option | Notes |
|---|---|---|
| `scale` | `scale` | day / week / month / quarter |
| `start-date`, `end-date` | same | fix the window |
| `today-marker` | `today` | default on |
| `show-dependencies` | same | default on |
| `show-percent` | `show-progress` | default on |
| `density` | `density`, and `row-height` 40 (normal) / 28 (compact) | |
| `collapsed-groups` | same | JSON array of collapsed group ids; activating a header updates it; new data removes it |
| `src` | — | as on `<mj-chart>` |

## 4. Properties

| Property | Description |
|---|---|
| `data` | The data above. Assigning draws at once, clears the selection and the collapsed groups, and emits `mj-data-load` |
| `selectedTask` | The selected task object, or null |
| `collapsedGroups` | `Set` of the collapsed group ids (as the data names them) |

All `<mj-chart>` properties and methods (`chartState`, `chartTable`, `redraw()`, ...) are available.

## 5. Events

| Event | `detail` | From |
|---|---|---|
| `mj-task-select` | `{ task }` | `mj-chart-bar-click`; opens the detail panel |
| `mj-task-deselect` | `{}` | the detail panel closed (Close, Escape) |
| `mj-marker-select` | `{ marker }` | `mj-chart-marker-click` |
| `mj-group-toggle` | `{ groupId, collapsed }` | `mj-chart-group-toggle` |
| `mj-data-load` | `{ tasks, groups }` | first draw of each assigned / loaded data object |
| `mj-error` | `{ message }` | `mj-chart-error` (once per message) |

The chart's own events (`mj-chart-*`) fire as well.

## 6. Slots, parts, custom properties

- Slots: `toolbar` (controls after the data-table button), `task-detail` (extra
  detail-panel content), `empty` (the chart's empty message).
- Parts: `toolbar`, `task-detail` (floating panel), the chart's `surface`, `svg`,
  `message`, `table data-table`, and the renderer's mark parts, which carry the
  wrapper's names too: `bar task-bar`, `bar-fill task-bar-fill`,
  `dependency dependency-arrow`, `task-label task-list-panel`, `group-row`,
  `milestone-marker`, `phase-band`, `time-axis`, `today-marker`, `today-label`.
- Custom properties: the chart's (`--mj-chart-series-*`, `--mj-chart-min-height`).

## 7. Keyboard and accessibility

The chart's model: the marks (group headers, bars, markers) are one tab stop with
arrow / Home / End movement; Enter or Space activates. The activated mark gets
`aria-current="true"`; the detail panel is a labelled region that takes focus,
and Escape or Close returns focus to the mark. The toolbar button discloses the
chart's data table (`aria-expanded`).

## 8. Migration (behaviour changes from the standalone implementation)

- The chart fits its width; a long plan no longer scrolls sideways (3 px/day
  minimum). Rows grow the chart vertically as before.
- Bars use the chart palette (the group's colour, else series 1) instead of
  `--mj-accent`; the today line is the accent colour (was danger red); marker
  colour is unchanged (warning).
- Parts `wrapper`, `chart-area` and `empty-state` are gone (use `surface` and
  `message`); `data-table` now names the table's container.
- The empty / loading / error states are the chart's messages: the error text is
  generic ("Chart data is not valid." / "Chart data could not be loaded."); the
  detail is in `mj-error` / `mj-chart-error`. The default-slot fallback content is
  no longer shown before data arrives.
- The host's accessible name is "Gantt chart" (no task count); the table is
  Task / Group / Start / End / Progress / Status / Assignee / Depends on.
- Marks are `role="img"` with `aria-current` for the selection (were
  `role="button"` with `aria-pressed`); group headers stay buttons.
- Not built (removed from this spec, never implemented): `editable` / `readonly`,
  `mj-task-update`, zoom and pan, `mj-range-change`, `visibleRange`, `adapter`,
  `locale`, `max-rows`, `loading` / `error` slots, the `label-*` attributes.
