# Roadmap Chart Spec

- **Tag:** `<mj-roadmap-chart>`
- **Class / file:** `MjRoadmapChart` / `components/mjroadmapchart.js` (base: `components/pmchartwrapper.js`)
- **Category:** Project-management & configuration-management charts
- **Primary or Variant:** Variant — a convenience wrapper for `<mj-chart type="roadmap">`
- **Synonyms covered:** Now/Next/Later roadmap, Release roadmap, Initiative roadmap
- **Status:** Implemented (wrapper since WW-1498)

> `<mj-roadmap-chart>` is `<mj-chart type="roadmap">` with the type fixed and the
> initiative data shape of this component family. Drawing (swimlanes with stacked
> bars, period or bucket columns, markers, phases, today), keyboard support, the
> data table and data loading are the chart's: see [chart.md](chart.md) (§21) and
> the `roadmap` chart-type page. This spec records only what differs.

## 1. Purpose and when to use

A strategic roadmap: swimlane rows, calendar-period or named-bucket columns,
status-coloured bars with icons. Use `<mj-gantt-chart>` for task-level schedules
and `<mj-milestone-timeline>` for a single axis of key dates.

## 2. Data shape (mapped onto the chart type)

```
{ swimlanes: [{ id, name }], buckets: [{ id, name }],
  initiatives: [{ id, name, swimlaneId, status, percentComplete, description,
                  columnId | startDate + endDate }],
  markers: [{ name, date }], phases: [{ name, start, end }] }
```

| Wrapper field | Chart type field |
|---|---|
| `initiatives` | `tasks` |
| `name` (else `id`, else "Initiative N") | `label` |
| `swimlaneId` / `swimlane` | `group`; `swimlanes` -> `groups [{ id, label }]` |
| `startDate` / `start`, `endDate` / `end` | `start`, `end` |
| `columnId` / `bucket` / `column` | `bucket`; `buckets` -> `buckets [{ id, label }]` |
| `status` (missing = planned) | `status` |
| `percentComplete` | `progress` (0-1; shown in the table and the detail panel) |
| `markers[].name`, `phases[].name` | `label` |

An initiative naming an unknown swimlane goes to the "Unassigned" lane; one that
cannot be placed (no dates in the range, unknown bucket) is counted in a note
under the chart and listed as "Not placed" in the table.

## 3. Attributes

| Attribute | Chart type option | Notes |
|---|---|---|
| `mode` | same | calendar (default) / bucket; bucket without buckets falls back to calendar |
| `scale` | same | quarter (default) / month / half-year |
| `start-date`, `end-date` | same | fix the calendar range |
| `today-marker` | `today` | calendar mode; default on |
| `density` | same | compact: 24 px bars instead of 32 px |
| `src` | — | as on `<mj-chart>` |

## 4. Properties

| Property | Description |
|---|---|
| `data` | The data above; assigning draws at once, clears the selection, emits `mj-data-load` |
| `selectedInitiative` | The selected initiative object, or null |

## 5. Events

| Event | `detail` | From |
|---|---|---|
| `mj-initiative-select` | `{ initiative }` | `mj-chart-bar-click`; opens the inline detail panel |
| `mj-initiative-deselect` | `{}` | the detail panel closed |
| `mj-data-load` | `{ initiatives, swimlanes }` | first draw of each data object |
| `mj-error` | `{ message }` | `mj-chart-error` |

## 6. Slots, parts, custom properties

- Slots: `legend` (toolbar content after the data-table button), `initiative-detail`, `empty`.
- Parts: `toolbar`, `initiative-detail`, the chart's `surface`, `svg`, `message`,
  `table data-table`, and the renderer's: `column-header`, `swimlane-label`,
  `bar initiative-bar`, `initiative-label`, `milestone-marker`, `phase-band`,
  `phase-label`, `today-marker`, `today-label`, `unplaced-note`.
- Status colours: planned `--mj-text-muted`, in-progress `--mj-accent`, done
  `--mj-color-success`, at-risk `--mj-color-warning`, blocked `--mj-color-danger`.

## 7. Migration (behaviour changes from the standalone implementation)

- The roadmap fits its width (columns share it); it no longer scrolls sideways
  with 160 px minimum columns.
- In-progress bars use `--mj-accent` (was `--mj-color-info`).
- Markers are focusable marks (they were images); activating one does nothing in
  the wrapper (`mj-chart-marker-click` still fires).
- An initiative without dates is no longer placed by a `columnId` that names a
  generated period (`Q1-2026`) in calendar mode; use dates or bucket mode.
- Parts `wrapper` and `empty-state` are gone (`surface`, `message`); the unplaced
  note is SVG text inside the chart. Error texts are the chart's generic messages
  (detail in `mj-error`); the default-slot fallback is not shown.
- Not built (removed from this spec): editable mode and its events, drag between
  columns, adapters, `locale`.
