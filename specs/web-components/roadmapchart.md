# Roadmap Chart Spec

- **Tag:** `<mj-roadmap-chart>`
- **Class / file:** `RoadmapChart` / `roadmapchart.js`
- **Category:** Project-management & configuration-management charts
- **Primary or Variant:** Primary
- **Synonyms covered:** Now/Next/Later roadmap, Release roadmap, Initiative roadmap
- **Phase:** P3
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-roadmap-chart>` renders initiatives, epics, or features grouped by
timeframe (calendar quarters, sprints, or named buckets like Now/Next/Later) in
horizontal swimlane rows. It supports milestone markers, time-column headers, and
an optional editable mode. It is the primary tool for communicating product or
release plans to stakeholders.

## 2. When to use / when not to use

**Use** for high-level initiative or feature roadmaps where the audience needs
to understand what ships in which timeframe without day-level precision. **Do
not use** for task-level scheduling (use `<mj-gantt-chart>`), for sprint
burn-down tracking (use `<mj-burndown-chart>`), or for a single axis of key
dates (use `<mj-milestone-timeline>`). Nearest alternatives: `<mj-gantt-chart>`
for detailed task planning.

## 3. Anatomy

- **Column headers** — timeframe labels (Q1 2025, Q2 2025… or Now/Next/Later)
  spanning the top of the chart; driven by the time-axis utility in calendar
  mode or by a named-bucket list in bucket mode.
- **Swimlane rows** — one row per team, product area, or theme; labeled on the
  left.
- **Initiative bars** — horizontal bars placed in the intersecting column of a
  swimlane; carry a label, status chip, and optional percent-complete.
- **Milestone markers** — named vertical markers from the shared milestone/marker
  model overlaid on the column headers.
- **Phase bands** — optional color spans across multiple columns (e.g. "H1
  Investment Theme").
- **Accessible data table** — visually hidden `<table>` of all initiatives.
- **Legend** — maps status colors/icons to labels.

## 4. Variants & modes

| Mode / Variant | Attribute | Behavior |
|---|---|---|
| Calendar mode | `mode="calendar"` (default) | Columns are time periods; time-axis utility used |
| Bucket mode | `mode="bucket"` | Columns are named buckets (Now/Next/Later); no time axis |
| Read-only | `readonly` (boolean, default) | No bar editing |
| Editable | `editable` (boolean) | Bars are draggable between columns |
| Compact | `density="compact"` | Reduced swimlane height; label only on bars |
| Full | `density="full"` (default) | Full bar details including status chip |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `src` | string | `""` | yes | URL for the data-source adapter |
| `adapter` | string | `"static"` | yes | Adapter key: `"static"`, `"jira"`, `"linear"`, `"productboard"` |
| `mode` | `"calendar"` \| `"bucket"` | `"calendar"` | yes | Column type: time periods or named buckets |
| `scale` | `"month"` \| `"quarter"` \| `"half-year"` \| `"year"` | `"quarter"` | yes | Calendar column granularity (calendar mode only) |
| `start-date` | string (ISO 8601) | `""` | yes | Start of visible calendar range |
| `end-date` | string (ISO 8601) | `""` | yes | End of visible calendar range |
| `today-marker` | boolean | `true` | yes | Show today line in calendar mode |
| `editable` | boolean | `false` | yes | Allow drag-to-move of initiative bars |
| `readonly` | boolean | `false` | yes | Explicit read-only lock |
| `density` | `"compact"` \| `"full"` | `"full"` | yes | Row height variant |
| `locale` | string | `""` | yes | BCP 47 locale for column header formatting |
| `label-loading` | string | `"Loading roadmap…"` | yes | Loading message override |
| `label-empty` | string | `"No initiatives."` | yes | Empty state message |
| `label-error` | string | `"Failed to load roadmap."` | yes | Error message override |

## 6. Properties

| Property | Type | Description |
|----------|------|-------------|
| `data` | `RoadmapData` | `{ swimlanes, initiatives, buckets, markers, phases }` |
| `selectedInitiative` | `Initiative \| null` | Currently selected initiative bar |
| `visibleRange` | `{ start: Date, end: Date }` | Current visible window (calendar mode) |

## 7. Slots

| Slot | Description |
|------|-------------|
| `(default)` | Fallback `<table>` rendered before upgrade |
| `initiative-detail` | Custom detail panel for a selected initiative |
| `legend` | Custom legend markup |
| `empty` | Shown when no initiatives are present |
| `loading` | Shown during adapter fetch |
| `error` | Shown on adapter failure |

## 8. Events

| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-initiative-select` | `{ initiative: Initiative }` | yes | no | Initiative bar activated |
| `mj-initiative-deselect` | `{}` | yes | no | Selection cleared |
| `mj-initiative-move` | `{ initiative: Initiative, fromColumn: string, toColumn: string }` | yes | yes | Bar dragged to a new column (editable mode) |
| `mj-marker-select` | `{ marker: Marker }` | yes | no | Milestone marker activated |
| `mj-range-change` | `{ start: string, end: string }` | yes | no | Visible calendar range changed |
| `mj-data-load` | `{ initiatives: number, swimlanes: number }` | yes | no | Data loaded successfully |
| `mj-error` | `{ message: string, cause: unknown }` | yes | no | Adapter error |

## 9. CSS parts & custom properties

**Parts:**
- `::part(column-header)` — timeframe or bucket column header cell
- `::part(swimlane-label)` — left-hand row label for each swimlane
- `::part(swimlane-row)` — full row container across all columns
- `::part(initiative-bar)` — initiative item bar
- `::part(initiative-label)` — text label inside bar
- `::part(milestone-marker)` — vertical marker line and label
- `::part(phase-band)` — background phase color span
- `::part(today-marker)` — today vertical line
- `::part(legend)` — legend container

**Custom properties:**
- `--mj-roadmap-row-height` — swimlane row height (default `64px`)
- `--mj-roadmap-label-width` — swimlane label column width (default `200px`)
- `--mj-roadmap-column-min-width` — minimum column width (default `120px`)
- `--mj-bar-radius` — bar corner radius (default `4px`)
- `--mj-phase-opacity` — phase band opacity (default `0.10`)
- `--mj-marker-release-color` — release marker color
- `--mj-marker-freeze-color` — freeze marker color
- `--mj-today-color` — today marker stroke color

## 10. States

- **loading** — `aria-busy="true"`; loading slot shown.
- **empty** — empty slot shown.
- **error** — error slot shown.
- **initiative-selected** — bar highlighted; detail panel open.
- **initiative-dragging** — bar partially transparent; destination column
  highlighted; live region announces current target column.
- **editable** — drag handles visible on bars.

## 11. Behavior & interactions

In calendar mode the time-axis utility renders column headers and positions
initiative bars by `startDate`/`endDate`. In bucket mode columns are defined by
the `buckets` array in `data`; initiatives are placed by `bucketId`. Clicking an
initiative bar fires `mj-initiative-select` and opens the detail panel. In
editable mode a bar can be dragged horizontally to a new column; dropping fires
`mj-initiative-move` (cancelable for validation). The column-header area pans in
calendar mode via the time-axis utility. Swimlanes without initiatives in a given
column show an empty cell. Milestone markers appear as vertical lines in the
column header band.

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| `Tab` | Move focus between initiative bars, swimlane labels, column headers, markers |
| `Arrow Left` / `Arrow Right` | Move focus between initiative bars in the same swimlane |
| `Arrow Up` / `Arrow Down` | Move focus between swimlane rows |
| `Enter` / `Space` | Select focused initiative bar or marker |
| `Escape` | Deselect; cancel drag |
| `M` | Move focused bar left one column (editable mode) |
| `Period` (`.`) | Move focused bar right one column (editable mode) |
| `Home` / `End` | Focus first / last initiative in current swimlane |

## 13. Accessibility

- Root: `role="img"` with `aria-label` = "Roadmap: {n} initiatives across
  {m} swimlanes, {start} to {end}".
- Grid structure: `role="grid"` on the chart area; `role="rowheader"` on
  swimlane labels; `role="columnheader"` on column headers.
- Initiative bars: `role="gridcell"` with `aria-label` = "{name}, {status},
  {column}"; `aria-selected` when selected.
- Drag operations announced via live-region: "Moving {name} to {column}".
- Milestone markers: `role="button"` with `aria-label` = "{name} {type} marker,
  {date or column}".
- Accessible data table: columns Initiative, Swimlane, Column/Timeframe, Status,
  % Complete; toggleable via a "Show data table" disclosure button.
- Color supplemented by status text badge and icon on each bar.

## 14. Form participation

N/A.

## 15. Internationalization & RTL

- Column headers in calendar mode use `Intl.DateTimeFormat` with the `locale`
  attribute.
- Named bucket labels are supplied by the consumer (no translation needed).
- Localizable UI strings (attributes): `label-loading`, `label-empty`,
  `label-error`, `label-today`, `label-show-table`, `label-move-left`,
  `label-move-right`.
- RTL: columns flow right-to-left; swimlane labels appear on the right; bars
  mirror correctly via CSS logical properties.

## 16. Progressive enhancement / SSR

Server renders a `<table>` of initiatives inside the default slot. On upgrade the
component hides the table visually (toggleable), draws the roadmap grid, and
positions bars without layout shift using `height-hint`.

## 17. Dependencies

- §6 time-axis utility (calendar mode zoom/pan/today/ticks)
- §6 milestone/marker model
- §6 data-source adapter interface (adapter keys: `static`, `jira`, `linear`,
  `productboard`)
- §6 registry + base element helper
- §6 design-token stylesheet
- §6 live-region/announcement service
- §6 localization/formatting hook

## 18. Edge cases & error handling

- **Initiative spans multiple columns** — bar stretches across column borders;
  label shown in the leftmost occupied cell.
- **No swimlanes** — all initiatives placed in a default unlabeled swimlane.
- **`start-date` after `end-date`** — swapped with console warning.
- **Bar dragged outside visible range** — chart pans to follow; drop target must
  be within defined columns/range.
- **Adapter failure** — error slot shown; stale data retained.
- **Long initiative names** — truncated with tooltip on hover/focus.
- **More than 20 swimlanes** — virtual scroll on swimlane axis.

## 19. Acceptance criteria

- [ ] Initiatives render in correct swimlane × column intersection from `data`.
- [ ] Calendar mode column headers reflect `scale` and `locale`.
- [ ] Bucket mode renders named columns in supplied order.
- [ ] Milestone markers appear on correct column boundary.
- [ ] Selecting an initiative fires `mj-initiative-select` and opens detail panel.
- [ ] Editable drag fires `mj-initiative-move` with from/to columns.
- [ ] Keyboard column-move (M/.) fires `mj-initiative-move` in editable mode.
- [ ] Accessible data table lists all initiatives with status and column.
- [ ] RTL layout mirrors correctly.
- [ ] axe automated accessibility check passes with zero violations.
- [ ] Empty, loading, and error states display correct slots.

## 20. Open questions

- Should initiative bars support a sub-bar for a linked "dependency release"
  date, or is that modeled as a separate milestone marker?
- Is a "now/next/later" bucket mode with drag-to-prioritize (reorder within
  column) in scope, or is that a separate product-management component?
- Should multi-team roadmaps support nested swimlanes (team → sub-team)?
