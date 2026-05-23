# Build Status Board Spec

- **Tag:** `<mj-build-status-board>`
- **Class / file:** `BuildStatusBoard` / `buildstatusboard.js`
- **Category:** Project-management & configuration-management charts
- **Primary or Variant:** Variant of `<mj-data-table>`
- **Synonyms covered:** Build status board, Release status board, Pipeline
  status dashboard
- **Phase:** P3
- **Status:** Planned

> Universal requirements (Custom Element standard, Shadow DOM/theming, WCAG 2.2
> AA, events/API, form participation, SSR, i18n, performance, testing, docs) are
> defined once in `web-component-development-plan.md` §3 and are not repeated
> here. This spec records only what is specific to this component.

## 1. Purpose

`<mj-build-status-board>` renders a grid of pipelines or branches and their
current build and deployment status — a "big board" view suitable for wall
monitors or CI dashboards. Each row represents a pipeline or branch; columns show
the latest build status, deploy target, last run time, duration, and triggering
actor. It is implemented as a specialized DataTable variant with live-updating
status cells and semantic status conventions.

## 2. When to use / when not to use

**Use** for aggregate visibility across many pipelines or branches at once —
wall-display dashboards, team CI health monitors, or release readiness overviews.
**Do not use** for a single pipeline's stage detail (use `<mj-pipeline-chart>`)
or for artifact promotion across environments (use `<mj-env-promotion-chart>`).
Nearest alternative: `<mj-pipeline-chart>` for a single pipeline drill-down.

## 3. Anatomy

- **Table grid** — DataTable-based `role="grid"` with keyboard navigation;
  columns sortable and filterable.
- **Pipeline/branch rows** — one row per pipeline or branch; include name link,
  status cell, deploy-target cell, last-run time, duration, and actor.
- **Status cell** — icon + text badge showing build/deploy status
  (pending/running/passed/failed/cancelled/skipped); not color-only.
- **Duration cell** — human-readable duration (e.g. "2m 14s").
- **Actor cell** — triggering user or bot avatar + name.
- **Live-status indicator** — pulsing badge in the board header when `live`.
- **Filter bar** — optional filter inputs above the table (status, branch
  pattern).
- **Bulk-action bar** — appears on row selection (re-run, cancel).
- **Accessible caption** — `<caption>` describes the table context.

## 4. Variants & modes

| Mode / Variant | Attribute | Behavior |
|---|---|---|
| Pipeline view | `group-by="pipeline"` (default) | One row per named pipeline |
| Branch view | `group-by="branch"` | One row per branch name |
| Compact | `density="compact"` | Reduced row height; actor avatar only (no name) |
| Full | `density="full"` (default) | Full row with all columns |
| Live | `live` (boolean) | Polls or streams; rows update in place |

## 5. Attributes

| Attribute | Type | Default | Reflects | Description |
|-----------|------|---------|----------|-------------|
| `src` | string | `""` | yes | URL for the data-source adapter |
| `adapter` | string | `"static"` | yes | Adapter key: `"static"`, `"github-actions"`, `"gitlab-ci"`, `"jenkins"` |
| `group-by` | `"pipeline"` \| `"branch"` | `"pipeline"` | yes | Row grouping dimension |
| `density` | `"compact"` \| `"full"` | `"full"` | yes | Row height variant |
| `live` | boolean | `false` | yes | Enable live status updates |
| `poll-interval` | number (ms) | `30000` | yes | Polling interval in live mode |
| `filter-status` | string | `""` | yes | Comma-separated status values to pre-filter (e.g. `"failed,running"`) |
| `filter-pattern` | string | `""` | yes | Glob pattern to pre-filter pipeline/branch names |
| `page-size` | number | `25` | yes | Rows per page; `0` disables pagination |
| `sort-column` | string | `"lastRun"` | yes | Column key for initial sort |
| `sort-direction` | `"asc"` \| `"desc"` | `"desc"` | yes | Initial sort direction |
| `locale` | string | `""` | yes | BCP 47 locale for date/duration formatting |
| `label-loading` | string | `"Loading status board…"` | yes | Loading message |
| `label-empty` | string | `"No pipelines found."` | yes | Empty message |
| `label-error` | string | `"Failed to load status board."` | yes | Error message |

## 6. Properties

| Property | Type | Description |
|----------|------|-------------|
| `data` | `StatusBoardData` | `{ rows: PipelineRow[] }` where each has `{ id, name, url, status, deployTarget, lastRun, duration, actor, branch }` |
| `selectedRows` | `Set<string>` | IDs of currently selected rows for bulk actions |
| `filteredRows` | `PipelineRow[]` | Rows after filter/sort applied (read-only) |

## 7. Slots

| Slot | Description |
|------|-------------|
| `(default)` | Fallback `<table>` rendered before upgrade |
| `bulk-actions` | Custom bulk-action bar content; receives `selectedRows` via property |
| `row-actions` | Custom per-row action cell content |
| `empty` | Shown when `filteredRows` is empty |
| `loading` | Shown during adapter fetch |
| `error` | Shown on adapter failure |

## 8. Events

| Event | `detail` | Bubbles | Cancelable | Description |
|-------|----------|---------|------------|-------------|
| `mj-row-select` | `{ row: PipelineRow, selected: boolean }` | yes | no | Row selection toggled |
| `mj-row-activate` | `{ row: PipelineRow }` | yes | no | Row name link or Enter key activated |
| `mj-bulk-action` | `{ action: string, rows: PipelineRow[] }` | yes | yes | Bulk action triggered; cancelable |
| `mj-status-change` | `{ rowId: string, previous: string, current: string }` | yes | no | Live status update for a row |
| `mj-sort-change` | `{ column: string, direction: string }` | yes | no | Column sort changed |
| `mj-filter-change` | `{ status: string, pattern: string }` | yes | no | Filter changed |
| `mj-data-load` | `{ rows: number }` | yes | no | Data loaded |
| `mj-error` | `{ message: string, cause: unknown }` | yes | no | Adapter error |

## 9. CSS parts & custom properties

**Parts:**
- `::part(table)` — the `<table>` element
- `::part(caption)` — table caption
- `::part(header-row)` — `<thead>` row
- `::part(header-cell)` — individual `<th>`
- `::part(data-row)` — individual `<tr>` in `<tbody>`
- `::part(status-cell)` — build/deploy status `<td>`
- `::part(status-badge)` — icon + text badge within status cell
- `::part(duration-cell)` — duration `<td>`
- `::part(actor-cell)` — actor avatar + name `<td>`
- `::part(filter-bar)` — filter controls above the table
- `::part(bulk-action-bar)` — bulk action controls
- `::part(live-indicator)` — pulsing live badge in header
- `::part(pagination)` — pagination controls

**Custom properties:**
- `--mj-row-height` — table row height (default `48px`)
- `--mj-status-pending-color` — pending badge accent
- `--mj-status-running-color` — running badge accent (with animation)
- `--mj-status-passed-color` — passed badge accent
- `--mj-status-failed-color` — failed badge accent
- `--mj-status-cancelled-color` — cancelled badge accent
- `--mj-status-skipped-color` — skipped badge accent
- `--mj-failed-row-bg` — background tint on failed rows
- `--mj-running-row-animation` — animation applied to running row indicator

## 10. States

- **loading** — `aria-busy="true"`; loading slot shown.
- **empty** — empty slot shown; filter bar still accessible.
- **error** — error slot shown.
- **row-selected** — row checkbox checked; bulk-action bar appears;
  `aria-selected="true"` on `<tr>`.
- **live-active** — live-indicator pulsing; `aria-live` region active.
- **failed-row** — failed status row has background tint and a text badge
  "Failed" (not color-only).
- **running-row** — running status row has a subtle animation on the status badge.
- **sorted** — sorted column header shows `aria-sort="ascending"` or
  `"descending"`.
- **filtered** — "N results" count shown in filter bar; "Clear filters" button
  available.

## 11. Behavior & interactions

The DataTable foundation provides column sorting (click column header; keyboard
activatable), filtering (filter bar inputs bind to `filter-status` and
`filter-pattern` properties), and pagination (`page-size`). Row selection uses
checkboxes in the first column with a select-all checkbox in the header.
The pipeline/branch name is a link (`<a>`) to the pipeline run URL. Status cells
update in place on `mj-status-change` without re-rendering the entire table.
In live mode the adapter polls `src` at `poll-interval`; only rows whose status
has changed are patched. The bulk-action bar appears when `selectedRows` is
non-empty and is slotted; the host provides action buttons that fire
`mj-bulk-action`.

## 12. Keyboard interaction

| Key | Action |
|-----|--------|
| `Tab` | Move focus between filter bar, table, pagination, bulk-action bar |
| `Arrow Up` / `Arrow Down` | Move focus between rows within the table (grid navigation) |
| `Arrow Left` / `Arrow Right` | Move focus between cells in the focused row |
| `Enter` | Activate the pipeline name link in the focused row |
| `Space` | Toggle row selection checkbox in the focused row |
| `Home` / `End` | Jump to first / last cell in the current row |
| `Ctrl+Home` / `Ctrl+End` | Jump to first / last row |
| `S` | Focus the sort control on the currently focused column header |

## 13. Accessibility

- Table: `role="grid"` with `<caption>` = "Build status board: {n} pipelines,
  last updated {time}".
- Column headers: `<th scope="col">` with `aria-sort` reflecting current sort.
- Status cells: icon has `aria-hidden="true"`; adjacent text badge conveys status.
- Row checkboxes: `<input type="checkbox">` with `aria-label` = "Select {name}".
- Select-all checkbox: `aria-label` = "Select all pipelines";
  `aria-checked="mixed"` when partially selected.
- Bulk-action bar: `role="toolbar"` with `aria-label` = "{n} pipelines selected".
- Live status changes announced via live-region: "{name} status changed to
  {status}" with `aria-live="polite"`.
- Failed status announced assertively when severity is `"failed"`:
  "{name} pipeline failed" with `aria-live="assertive"`.
- Running row animation: respects `prefers-reduced-motion`; animation replaced
  by a static indicator.

## 14. Form participation

N/A — this component is not an input control.

## 15. Internationalization & RTL

- Last-run timestamps use `Intl.DateTimeFormat` with `locale`; duration uses
  `Intl.DurationFormat` where available, falling back to "{m}m {s}s" pattern.
- Status text labels overridable: `label-status-pending`, `label-status-running`,
  `label-status-passed`, `label-status-failed`, `label-status-cancelled`,
  `label-status-skipped`.
- All UI strings: `label-loading`, `label-empty`, `label-error`,
  `label-select-all`, `label-clear-filters`, `label-filter-status`,
  `label-filter-pattern`, `label-n-selected`.
- RTL: table columns maintain their logical order; `dir` attribute propagates to
  `<table>`; text cells align correctly.

## 16. Progressive enhancement / SSR

Server renders a `<table>` of pipeline rows inside the default slot. On upgrade
the component hides the table and initializes the DataTable variant with live
updating, sorting, and filtering without layout shift.

## 17. Dependencies

- `<mj-data-table>` (§5.8; base grid component — row/cell keyboard navigation,
  sort, filter, pagination, selection)
- §6 data-source adapter interface (adapter keys: `static`, `github-actions`,
  `gitlab-ci`, `jenkins`)
- §6 registry + base element helper
- §6 design-token stylesheet
- §6 live-region/announcement service
- §6 localization/formatting hook (`Intl.DateTimeFormat`, `Intl.DurationFormat`)

## 18. Edge cases & error handling

- **Empty filter result** — empty slot shown; "Clear filters" button present and
  resets filters.
- **All rows failing** — all rows show failed state; board header shows "All
  pipelines failed" alert banner using the Alert component.
- **Row name longer than column width** — truncated with tooltip.
- **Duration > 1 hour** — displayed as "{h}h {m}m"; `Intl.DurationFormat` handles
  this automatically.
- **Adapter failure in live mode** — last known data retained; error toast shown
  via the Toast region; board continues polling.
- **`page-size=0` with >500 rows** — all rows rendered; performance warning
  logged recommending a non-zero `page-size`.
- **Status value not in the known set** — rendered as "Unknown" with a question-mark
  icon; logged as a warning.

## 19. Acceptance criteria

- [ ] Rows render from static `data` with name, status badge, duration, and actor.
- [ ] Status badges show icon + text label for all six status values.
- [ ] Clicking a column header sorts the table and sets `aria-sort`.
- [ ] Filter bar filters rows by status and pattern.
- [ ] Row checkbox toggles `aria-selected` and shows bulk-action bar.
- [ ] Select-all checkbox uses `aria-checked="mixed"` for partial selection.
- [ ] Live mode fires `mj-status-change` and patches only changed rows.
- [ ] `mj-row-activate` fires when the pipeline name link is activated.
- [ ] Keyboard navigation per §12 covers grid cells, filter bar, and pagination.
- [ ] Failed pipeline fires `aria-live="assertive"` announcement.
- [ ] `prefers-reduced-motion` disables running-row animation.
- [ ] RTL table renders without broken layout.
- [ ] axe automated accessibility check passes with zero violations.

## 20. Open questions

- Should the board support a "wall display" full-screen mode that hides the
  filter bar and pagination and rotates through all failing rows?
- Is a column for "deploy target" always present or should it be hidden when
  all pipelines deploy to a single environment?
- Should the `jenkins` adapter support multi-branch pipeline job naming
  conventions differently from flat job names?
