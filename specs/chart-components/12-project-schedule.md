# Project & Schedule Charts

> Catalog of chart types in this category for the codecraftai-webworks SVG chart
> library. Architecture, the coordinated-element model, the part components,
> the JSON contract, and phasing are defined in `../../chart-components-plan.md`
> and are not repeated here.

---

### Gantt Chart  *(project bar chart, schedule chart)*
- **Renderer / `type`:** `gantt` — **Primary renderer** (`charts/core/renderers/gantt.js`, shared with `roadmap`)
- **Controller:** `<mj-chart type="gantt" ...>`; `<mj-gantt-chart>` is a convenience wrapper for this type with its own data shape (see `../web-components/ganttchart.md`)
- **Purpose:** Display project tasks as horizontal bars along a time axis, showing start dates, durations, progress, dependencies, milestones and phases at a glance.
- **Decomposition:** drawn by the renderer inside `<mj-chart>`; `mj-chart-legend` (one entry per group), `mj-chart-title` and `mj-chart-data-table` bind as parts.
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Website Redesign – Sprint 3" },
    "groups": [ { "id": "design", "label": "Design" } ],
    "tasks": [
      { "id": "t1", "label": "Wireframes", "start": "2025-03-01", "end": "2025-03-08",
        "progress": 1.0, "assignee": "Alice", "group": "design", "depends": [] },
      { "id": "t2", "label": "Visual Design", "start": "2025-03-09", "end": "2025-03-22",
        "progress": 0.6, "assignee": "Alice", "group": "design", "depends": ["t1"] },
      { "id": "t3", "label": "Support rotation", "start": "2025-03-03" },
      { "id": "t4", "label": "Sign-off", "start": "2025-03-24", "milestone": true }
    ],
    "markers": [ { "label": "Design review", "date": "2025-03-14" } ],
    "phases":  [ { "label": "Discovery", "start": "2025-03-01", "end": "2025-03-08" } ]
  }
  ```
  Fields:
  - `tasks[]`: `id` (key used by `depends`; else the index); `label` (else the id); `start` / `end` — `YYYY-MM-DD` (a local calendar day; an end day is inclusive), `YYYY-MM` (whole month), `YYYY-Qn` (whole quarter), ISO date-time or epoch ms; `progress` (0–1); `assignee` (drawn beside the bar when there is room); `group` (a group id or label); `depends` (predecessor ids, finish-to-start arrows); `status` (shown in the accessible name and table); `milestone` (`true` draws a diamond).
  - `groups[]` (optional): `{ id, label }` — the order and names of the group header rows (empty groups included). With `groups`, a task naming any other group is ungrouped; without it, the groups are the ones the tasks name, in order of first appearance.
  - `markers[]` (optional): `{ label, date }` milestone lines. `phases[]` (optional): `{ label, start, end }` background bands (end inclusive).
- **Drawing:** one row per task; ungrouped tasks first, then a header row per group with its tasks indented. A task with `start` and `end` is a bar (with a darker progress fill); a task with only a `start` is an **open-ended bar that runs to the right edge of the chart with a dashed outline**; `milestone: true`, a zero-length span or an end only is a diamond; a task without a usable date keeps its row with a dashed "No dates" placeholder; a task entirely outside the `start-date` / `end-date` window shows an arrow at the edge it lies beyond. Markers are a dashed amber (`--mj-color-warning`) line with a diamond on the axis and the name beside it; phases are translucent bands coloured by position (`--mj-chart-series-*`); a dashed accent line labelled "Today" marks the current date when it is in range. Bars are coloured by group (`ctx.colorFor(group)`), else series 1.
- **SVG primitives:** `<g>` per task mark holding `<rect>` (bar, progress fill) or `<polygon>` (diamond, edge arrow); `<g role="button">` per group header; `<path>` dependency arrows (right-angle elbow routing, `<marker>` arrowhead in `<defs>`); `<rect>` phase bands; `<g>` markers with `<line>`, `<polygon>`, `<text>`; `<line>` / `<text>` axis ticks and the today line.
- **Orientation:** `horizontal` only (registered default).
- **Options (attributes on `<mj-chart>`):**
  | Option | Default | Effect |
  |---|---|---|
  | `variant` | type key | `roadmap` draws the roadmap layout from the same data |
  | `today` | on | `"false"` hides the today line |
  | `start-date`, `end-date` | data range + 2 % | fix the window (same date forms as the tasks; a calendar end is inclusive) |
  | `scale` | automatic | `day` / `week` (Mondays) / `month` / `quarter` tick unit; the step still grows when labels would collide |
  | `show-progress` | on | `"false"` hides the progress fills |
  | `show-dependencies` | on | `"false"` hides the dependency arrows |
  | `density` | `normal` | `compact` shortens the rows |
  | `row-height` | 32 (24 compact) | minimum row height in px; rows stretch up to 1.5x to fill a taller chart |
  | `collapsed-groups` | — | JSON array (or comma list) of collapsed group ids; activating a header updates it |
- **Height:** the renderer asks for `32 + rows × row-height + 14` px (`ctx.setContentHeight`), so a chart without a fixed height grows with its rows; registered `minHeight` is **120** (was the 280 px default). With a fixed height taller rows stretch, shorter ones scroll.
- **Interaction & accessibility:** bars, group headers and markers are the focusable marks (one tab stop, arrow keys, Home / End; Enter / Space activates). A group header is `role="button"` with `aria-expanded`; activating it collapses or expands its tasks (the table keeps them and the axis does not rescale). The accessible table lists every task: Task, Group, Start, End ("Open-ended" for a start-only task), Progress, Status, Assignee, Depends on.
- **Events:**
  | Event | `detail` |
  |---|---|
  | `mj-chart-bar-click` | `{ id, label, start, end, index }` |
  | `mj-chart-marker-click` | `{ label, date, index }` |
  | `mj-chart-group-toggle` | `{ group, collapsed, collapsedGroups }` |
- **Parts:** `plot`; `bar task-bar` (each task mark); `bar-fill task-bar-fill`; `dependency dependency-arrow`; `group-row`; `task-label task-list-panel`; `milestone-marker`; `phase-band`; `time-axis` (tick labels); `today-marker`; `today-label`. Marks carry `data-mark` keys (`task:<index>`, `group:<n>`, `marker:<index>`).
- **Phase:** P3 — implemented.
- **Notes:** Uses a `time` scale on the horizontal axis; rows are laid out by the renderer (no band scale). `<mj-gantt-chart>` maps `name`, `percentComplete`, `groupId` and `dependencies` onto this shape and adds a toolbar and detail panel (WW-1498).

---

### Timeline  *(event timeline, horizontal timeline)*
- **Renderer / `type`:** `timeline` — **Primary renderer** (`charts/core/renderers/timeline.js`, shared with `milestone`)
- **Controller:** `<mj-chart type="timeline" ...>`
- **Purpose:** Plot discrete events or milestones at their dates along a time axis; shows sequence, clustering, and temporal gaps without duration bars.
- **Decomposition:** drawn by the renderer inside `<mj-chart>`; `mj-chart-legend` (statuses, else kinds, else lanes), `mj-chart-title` and `mj-chart-data-table` bind as parts.
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Product Launch Timeline" },
    "events": [
      { "id": "e1", "label": "Alpha Release", "date": "2025-04-01", "group": "Engineering", "kind": "tag" },
      { "id": "e2", "label": "Beta Launch",   "date": "2025-06-15", "group": "Marketing",   "status": "planned",
        "icon": "★", "description": "Public beta with the press release." }
    ],
    "phases": [ { "label": "Hardening", "start": "2025-05-01", "end": "2025-06-14" } ]
  }
  ```
  Fields: `id`; `label`; `date` (Date, epoch ms or ISO; `YYYY-MM-DD` is a local day); `group` (one lane per distinct group, optional); `status` (`completed`, `active`, `planned` — hollow marker —, `at-risk`; sets the colour); `kind` (`release` diamond, `freeze` triangle, `tag` / `milestone` circle — sets the shape and, without a `status`, the colour: success, warning, info, accent); `icon` (a short glyph, at most 4 characters, before the label); `description` (tooltip and table); `phases[]` background bands (end inclusive).
- **Drawing:** a spine per lane with markers on it; labels are placed in tiers above and below the spine (horizontal) or to the right (vertical) so they never overlap — a label with no free slot stays in the tooltip; events on (nearly) the same date are nudged apart so none hides another. Phase bands are drawn behind the markers (coloured by position); a dashed accent line labelled "Today" marks the current date when it is in range. With `dim-past`, events more than a day before now are drawn at 55 % opacity.
- **SVG primitives:** `<circle>` / `<polygon>` (marker — the focusable mark), `<line>` (stem to the label), `<text>` (labels, ticks), `<rect>` (phase bands), `<line>` (spine, today line), `<g>` layers.
- **Orientation:** `horizontal` (registered default; time → x) and `vertical` (time → y).
- **Options:**
  | Option | Default | Effect |
  |---|---|---|
  | `variant` | type key | `timeline` circles / `milestone` diamonds for events without a `kind` |
  | `orientation` | `horizontal` | `vertical` runs time down the page |
  | `today` | on | `"false"` hides the today line |
  | `start-date`, `end-date` | data range + 5 % | fix the window; events outside it are listed in the table but not drawn (a `YYYY-MM-DD` end is inclusive) |
  | `dim-past` | off | fade past events and add "past" / "today" / "upcoming" to each marker's accessible name |
  | `density` | `normal` | `compact`: 10 px labels cut at about 12 characters |
- **Events:** `mj-chart-event-click` `{ id, label, date, group, status, kind, index }`.
- **Parts:** `plot`, `marker`, `marker-label`, `phase-band`, `time-axis`, `today-marker`, `today-label`; markers carry `data-mark="event:<index>"`.
- **Accessible table:** Event, Date, Group, Status, Kind (when any event has one), Description.
- **Phase:** P3 — implemented.
- **Notes:** Uses a `time` scale; lanes share the cross axis equally. Events without a usable date are listed in the table but not drawn.

---

### Roadmap Chart  *(product roadmap, initiative map)*
- **Renderer / `type`:** `roadmap` — **Variant of `gantt`** (same renderer module; `<mj-chart type="gantt" variant="roadmap">` draws the same)
- **Controller:** `<mj-chart type="roadmap" ...>`; `<mj-roadmap-chart>` is a convenience wrapper for this type with the initiative data shape (see `../web-components/roadmapchart.md`)
- **Purpose:** Display product or project initiatives grouped by theme or team across calendar periods or Now / Next / Later buckets, emphasising planning horizons rather than precise task durations.
- **Decomposition:** drawn by the renderer inside `<mj-chart>`; `mj-chart-legend` (one entry per status seen, with its icon), `mj-chart-title` and `mj-chart-data-table` bind as parts.
- **JSON shape:**
  ```json
  {
    "meta": { "title": "2025–2026 Product Roadmap" },
    "groups":  [ { "id": "mobile", "label": "Mobile" }, { "id": "platform", "label": "Platform" } ],
    "buckets": [ { "id": "now", "label": "Now" }, { "id": "next", "label": "Next" } ],
    "tasks": [
      { "id": "i1", "label": "Mobile App v2", "start": "2025-Q1", "end": "2025-Q3",
        "group": "mobile", "status": "in-progress", "progress": 0.4, "bucket": "now" },
      { "id": "i2", "label": "API Gateway", "start": "2025-Q2", "end": "2026-Q1",
        "group": "platform", "status": "planned", "description": "Replaces the v1 proxy." }
    ],
    "markers": [ { "label": "GA", "date": "2025-09-15" } ],
    "phases":  [ { "label": "Planning", "start": "2025-01-06", "end": "2025-01-31" } ]
  }
  ```
  `tasks`, `groups`, `markers` and `phases` as in the Gantt chart (`start` / `end` accept `YYYY-Qn` and `YYYY-MM`); `status`: `planned`, `in-progress` / `active`, `completed` / `done`, `at-risk`, `blocked` (any other text shows as given with the planned look); `bucket` names a column in `mode="bucket"`; `description` goes to the tooltip and the table; `progress` to the table.
- **Drawing (changed from the earlier one-row-per-task variant):** **one lane per group**; inside a lane, bars that do not overlap share a row and overlapping bars stack in sub-rows. **Columns** are calendar periods with a header cell each (`scale` quarter — default —, month or half-year) covering the tasks, or, with `mode="bucket"` and `buckets` given, the named buckets (equal widths; a task spans the column its `bucket` names). Each bar is a surface-filled rounded rectangle with a status-coloured border and tint, a **status icon** (○ planned, ◎ in progress, ✓ done, ⚠ at risk, ⊘ blocked) and its label. Status colours: planned `--mj-text-muted`, in-progress `--mj-accent`, done `--mj-color-success`, **at-risk `--mj-color-warning` (amber; was danger red)**, blocked `--mj-color-danger`. Tasks naming no known group go to an "Unassigned" lane (unlabelled when no group exists at all). Tasks that cannot be placed (no dates in the range, unknown bucket) are counted in a note under the lanes and listed in the table as "Not placed". In calendar mode markers (dashed amber line and diamond), phase bands with their names in a row under the lanes, and the today line with its "Today" label in a row of its own are drawn. Progress fills and dependency arrows are not drawn.
- **SVG primitives:** `<rect>` (column header cells, bars, lane label column, phase bands), `<text>` (headers, lane labels, icons, bar labels, phase / today labels, note), `<line>` (column and lane rules, today line), `<g>` per bar mark and marker.
- **Orientation:** `horizontal` only.
- **Options:**
  | Option | Default | Effect |
  |---|---|---|
  | `variant` | type key | `gantt` draws the gantt layout from the same data |
  | `mode` | `calendar` | `bucket` places tasks in the `buckets` columns (falls back to calendar without buckets) |
  | `scale` | `quarter` | `month` / `half-year` calendar columns |
  | `start-date`, `end-date` | the tasks' range | fix the calendar range |
  | `today` | on | `"false"` hides the today line (calendar mode) |
  | `density` | `normal` | `compact`: 24 px bars instead of 32 px |
- **Height:** the renderer asks for the height of its header, lanes and footer rows (`ctx.setContentHeight`); registered `minHeight` 120. The columns share the chart's width.
- **Events:** `mj-chart-bar-click` `{ id, label, start, end, index }`, `mj-chart-marker-click` `{ label, date, index }` (calendar mode).
- **Parts:** `plot`, `column-header`, `swimlane-label`, `bar initiative-bar`, `initiative-label`, `milestone-marker`, `phase-band`, `phase-label`, `today-marker`, `today-label`, `unplaced-note`; bars carry `data-mark="task:<index>"`.
- **Accessible table:** Initiative, Group, Timeframe ("Not placed" when unplaced), Status, Progress, Description.
- **Phase:** P3 — implemented.
- **Notes:** Quarter and month strings are read by the renderer's `parseScheduleDate` (a calendar end covers the whole period). `<mj-roadmap-chart>` maps `swimlanes`, `initiatives` (`name`, `swimlaneId`, `startDate` / `endDate`, `columnId`, `percentComplete`) onto this shape (WW-1498).

---

### Milestone Chart  *(key-date chart, diamond chart)*
- **Renderer / `type`:** `milestone` — **Variant of `timeline`** (same renderer module; `<mj-chart type="timeline" variant="milestone">` draws the same)
- **Controller:** `<mj-chart type="milestone" ...>`; `<mj-milestone-timeline>` is a convenience wrapper for this type with `dim-past` on and its own data shape (see `../web-components/milestonetimeline.md`)
- **Purpose:** Highlight key project dates (deadlines, deliverables, go-live dates) as prominent markers on a time axis, with no duration bars.
- **Decomposition:** as Timeline.
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Q3 Milestones" },
    "events": [
      { "id": "m1", "label": "Beta Freeze", "date": "2025-07-31", "kind": "freeze" },
      { "id": "m2", "label": "GA Release",  "date": "2025-09-15", "status": "planned", "kind": "release" }
    ],
    "phases": [ { "label": "Hardening", "start": "2025-08-01", "end": "2025-09-12" } ]
  }
  ```
  Same `events` / `phases` shape as Timeline; `status` maps to the marker colour, `kind` to its shape (and colour without a status).
- **Drawing:** the Timeline layout with **diamond** markers for events without a `kind`; `kind` picks triangle (freeze) or circle (tag, milestone) instead. Phases, the today line, the window, `dim-past` and `density` work as on the Timeline.
- **SVG primitives:** `<polygon>` (diamond / triangle marker), `<circle>` (tag / milestone kinds), `<line>` (stem), `<text>` (label), `<rect>` (phase bands), `<g>`.
- **Orientation:** `horizontal` (default) and `vertical` — same as Timeline.
- **Options, events, parts, table:** as Timeline (`variant="timeline"` switches the default shape back to circles).
- **Events:** `mj-chart-event-click` `{ id, label, date, group, status, kind, index }` (each marker), as Timeline.
- **Phase:** P3 — implemented.
- **Notes:** The `timeline` renderer dispatches on `ctx.type` (and the `variant` option); no separate module.

---

### Burndown Chart  *(sprint burndown, release burndown)*
- **Renderer / `type`:** `line` — **Primary renderer** (for burndown/burnup family)
- **Controller:** `<mj-chart type="line" ...>`
- **Purpose:** Track remaining work (story points, tasks, or hours) against calendar time to show whether a sprint or release is on track.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (time, bottom; value, start), `mj-chart-grid`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-crosshair`, `mj-chart-annotation`, `mj-chart-data-table`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Sprint 12 Burndown" },
    "series": [
      {
        "name": "Ideal",
        "points": [{ "x": "2025-03-01", "y": 40 }, { "x": "2025-03-14", "y": 0 }]
      },
      {
        "name": "Actual",
        "points": [{ "x": "2025-03-01", "y": 40 }, { "x": "2025-03-07", "y": 28 }, { "x": "2025-03-14", "y": 12 }]
      }
    ]
  }
  ```
  Uses the XY/relationship `points` shape with `x` as ISO date and `y` as remaining work.
- **SVG primitives:** `<path>` (line per series via `svgdraw.js` line builder), `<circle>` (data point markers), `<text>`, `<g>`
- **Orientation:** `vertical` (time → x, remaining work → y). Horizontal is `n/a` — the downward slope is the defining visual.
- **Variants / modes:** The `Burnup chart` is a variant of this same renderer entry — see below.
- **Events:** `mj-chart-line-click` `{ series, x, y }` (each point target).
- **Phase:** P3
- **Notes:** Uses `time` scale on the x-axis and `linear` scale on the y-axis. The "Ideal" series is a straight line from total scope to zero; the "Actual" series is the measured remaining work. `mj-chart-annotation kind="line"` marks today's date.

---

### Burnup Chart  *(cumulative completion chart)*
- **Renderer / `type`:** `line` — **Variant of `line`**
- **Controller:** `<mj-chart type="line" ...>`
- **Purpose:** Track completed work and total scope over time; reveals scope creep by showing both the completed and the total-scope lines diverging.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (time, bottom; value, start), `mj-chart-grid`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-crosshair`, `mj-chart-annotation`, `mj-chart-data-table`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Release Burnup" },
    "series": [
      {
        "name": "Scope",
        "points": [{ "x": "2025-03-01", "y": 80 }, { "x": "2025-03-14", "y": 90 }]
      },
      {
        "name": "Completed",
        "points": [{ "x": "2025-03-01", "y": 0 },  { "x": "2025-03-14", "y": 55 }]
      }
    ]
  }
  ```
- **SVG primitives:** `<path>`, `<circle>`, `<text>`, `<g>` — identical to Burndown.
- **Orientation:** `vertical` only — matching Burndown for comparability.
- **Variants / modes:** Uses the standard `line` renderer; the distinction from Burndown is purely in how the data layer populates the series (completed work ascending vs remaining work descending). No renderer attribute needed.
- **Events:** `mj-chart-line-click` `{ series, x, y }` (each point target).
- **Phase:** P3
- **Notes:** The area between the "Scope" and "Completed" lines may optionally be filled using `mj-chart-annotation kind="band"` to highlight the gap. Scope creep is visible when the "Scope" line rises; a flat "Scope" line with a rising "Completed" line indicates a healthy burnup.

---

### Cumulative Flow Diagram  *(CFD, flow chart)*
- **Renderer / `type`:** `area` — **Variant of `area`**
- **Controller:** `<mj-chart type="area" group="stack" ...>`
- **Purpose:** Visualise the quantity of work in each workflow state (backlog, in-progress, done, etc.) over time using stacked bands, revealing bottlenecks and cycle time.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (time, bottom; value, start), `mj-chart-grid`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-crosshair`, `mj-chart-data-table`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Kanban CFD – March 2025" },
    "categories": ["2025-03-01", "2025-03-02", "2025-03-03"],
    "series": [
      { "name": "Done",        "values": [0,  5, 12] },
      { "name": "In Progress", "values": [3,  4,  3] },
      { "name": "In Review",   "values": [2,  2,  2] },
      { "name": "Backlog",     "values": [20, 14, 8] }
    ]
  }
  ```
  Uses the common envelope; `categories` are ISO dates; `series` ordered bottom-to-top (done first). The `area` renderer with `group="stack"` stacks the bands.
- **SVG primitives:** `<path>` (filled stacked area band per series via `svgdraw.js` area builder), `<text>`, `<g>`
- **Orientation:** `vertical` (time → x, count → y). Horizontal is `n/a` — time flows left to right by convention.
- **Variants / modes:** Consolidates onto the `area` renderer with `group="stack"`. The CFD is distinguished from a generic stacked area only by the nature of the data (workflow state counts over time) — no renderer change needed.
- **Events:** `mj-chart-area-click` — `{ series, x, y }` from each point target, with `share` added when the areas are stacked (`area` reads `stack="stack"`, not `group`); a click on a filled band (pointer only) emits `{ series }`.
- **Phase:** P3
- **Notes:** Uses `time` scale on the x-axis (the `categories` array values are parsed as dates) and `linear` scale on the y-axis. Series should be ordered so that "Done" accumulates at the bottom and "Backlog" sits at the top; the slope of the "Done" band's upper boundary indicates throughput. Bottlenecks appear as expanding bands for a given state.

---

### Kanban Chart  *(WIP chart, work-state distribution chart)*
- **Renderer / `type`:** `kanban` — **Primary renderer**
- **Controller:** `<mj-chart type="kanban" ...>`
- **Purpose:** Snapshot the count (or list) of work items in each workflow column at a point in time; shows work-in-progress limits and column load.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (category/column, bottom; value/count, start), `mj-chart-grid`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-value-labels`, `mj-chart-annotation`, `mj-chart-data-table`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Engineering Board – 2025-03-15" },
    "columns": [
      {
        "name": "Backlog",
        "wip-limit": null,
        "items": [
          { "id": "PROJ-101", "label": "Auth service refactor", "assignee": "Bob", "priority": "high" },
          { "id": "PROJ-102", "label": "Update docs",           "assignee": null,  "priority": "low"  }
        ]
      },
      {
        "name": "In Progress",
        "wip-limit": 3,
        "items": [
          { "id": "PROJ-99", "label": "Payment gateway",       "assignee": "Carol", "priority": "critical" }
        ]
      }
    ]
  }
  ```
  Fields: `columns` array; each column has `name`, optional `wip-limit`, and `items` array. Each item has `id`, `label`, optional `assignee` and `priority`.
- **SVG primitives:** `<rect>` (column background lane), `<rect>` (item card), `<text>` (item label, assignee, column header), `<line>` (WIP-limit indicator), `<g>` (per-column and per-item groups)
- **Orientation:** `horizontal` (registered default; columns left-to-right, items stacked vertically within each column) | `vertical` (columns stacked top-to-bottom as rows, cards flowing across). With no `orientation` attribute, a chart narrower than 480 px with more than 2 columns uses the vertical layout automatically.
- **Variants / modes:** `variant="count"` draws a bar per column of its item count with the WIP limit marked as a dashed line (an over-limit column's bar in `--mj-color-danger`), when item-level detail is not needed; it is drawn by `kanban.js`, not the `bar` renderer. Cards that do not fit a column are summarised by a focusable "+N more" mark; every card is listed in the data table.
- **Events:** `mj-chart-card-click` `{ column, id, label }`; `mj-chart-overflow-click` `{ column, hidden, items }` (the "+N more" mark); `mj-chart-column-click` `{ column, count, wipLimit }` (count variant).
- **Phase:** P3
- **Notes:** The Kanban chart is the only chart in this category whose primary visual is a card-based layout rather than a Cartesian plot. Item cards are `<rect>` + `<text>` groups; priority is encoded by a left-border colour stripe and an `aria-label` (not colour alone). WIP-limit violations are flagged by changing the column background colour using a `--mj-chart-wip-exceeded` token and adding an `aria-alert` annotation. Uses `band` scale for columns. The `mj-chart-annotation kind="line"` draws the WIP limit bar.

---

### Resource Allocation Chart  *(resource heatmap, staffing chart, capacity chart)*
- **Renderer / `type`:** `resource-allocation` — **Primary renderer** (`charts/core/renderers/resource.js`)
- **Controller:** `<mj-chart type="resource-allocation" ...>`
- **Purpose:** Show how people or resources are allocated across tasks or projects over time; reveals over-allocation, under-utilisation, and scheduling conflicts.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (time, top; category/resource, start), `mj-chart-grid`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-brush`, `mj-chart-annotation`, `mj-chart-data-table`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Team Capacity – March 2025" },
    "resources": [
      {
        "id": "r1",
        "label": "Alice",
        "capacity": 1.0,
        "allocations": [
          { "task": "Website Redesign", "start": "2025-03-01", "end": "2025-03-14", "load": 0.5 },
          { "task": "API Gateway",      "start": "2025-03-01", "end": "2025-03-31", "load": 0.5 }
        ]
      },
      {
        "id": "r2",
        "label": "Bob",
        "capacity": 1.0,
        "allocations": [
          { "task": "Website Redesign", "start": "2025-03-10", "end": "2025-03-31", "load": 1.0 }
        ]
      }
    ]
  }
  ```
  Fields: `resources` array; each resource has `id`, `label`, `capacity` (1.0 = full-time), and `allocations` array. Each allocation has `task` name, `start`/`end` ISO dates, and `load` (fraction of capacity, 0–1; values > 1 indicate over-allocation).
- **SVG primitives:** `<rect>` (allocation bar per task, width proportional to duration and height/opacity proportional to load), `<line>` (capacity ceiling), `<text>` (resource labels, task names, date ticks), `<g>` (per-resource row groups)
- **Orientation:** `horizontal` only — resource rows run left-to-right along the time axis, mirroring Gantt chart conventions.
- **Variants / modes:** `variant="heatmap"` collapses each resource row to a single band whose colour shows the utilisation (summed load / capacity) of each period — under 50 %, 50–89 %, 90–100 %, over capacity (`--mj-color-danger`) — instead of stacked allocation bars, useful for many resources over long time horizons.
- **Events:** `mj-chart-allocation-click` — allocation bars `{ resource, task, start, end, load }`; heatmap cells `{ resource, start, end, load, utilization }`; over-capacity flags `{ resource, start, end, load, overAllocated }`.
- **Phase:** P3
- **Notes:** Uses `time` scale on the horizontal axis and `band` scale on the vertical (resource/row) axis. Over-allocation (`load` sum > `capacity` in an interval) is highlighted using `--mj-chart-overload` colour token and an `aria-label` warning; pattern fill is used alongside colour. `mj-chart-brush` enables horizontal time-range zoom. The renderer stacks multiple allocation bars vertically within a single resource row when tasks overlap in time.
