# Project & Schedule Charts

> Catalog of chart types in this category for the automojo-webworks SVG chart
> library. Architecture, the coordinated-element model, the part components,
> the JSON contract, and phasing are defined in `../../chart-components-plan.md`
> and are not repeated here.

---

### Gantt Chart  *(project bar chart, schedule chart)*
- **Renderer / `type`:** `gantt` — **Primary renderer**
- **Controller:** `<mj-chart type="gantt" ...>`
- **Purpose:** Display project tasks as horizontal bars along a time axis, showing start dates, durations, dependencies, and resource assignments at a glance.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (time, top; category/task, start), `mj-chart-grid`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-brush`, `mj-chart-annotation`, `mj-chart-data-table`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Website Redesign – Sprint 3" },
    "tasks": [
      {
        "id": "t1",
        "label": "Wireframes",
        "start": "2025-03-01",
        "end":   "2025-03-08",
        "progress": 1.0,
        "assignee": "Alice",
        "group": "Design",
        "depends": []
      },
      {
        "id": "t2",
        "label": "Visual Design",
        "start": "2025-03-09",
        "end":   "2025-03-22",
        "progress": 0.6,
        "assignee": "Alice",
        "group": "Design",
        "depends": ["t1"]
      }
    ]
  }
  ```
  Fields: `id` (unique key); `label` (display name); `start`/`end` (ISO-8601 date); `progress` (0–1, optional); `assignee` (string, optional); `group` (swimlane label, optional); `depends` (array of `id` strings for dependency arrows, optional).
- **SVG primitives:** `<rect>` (task bar), `<rect>` (progress fill within bar), `<line>` / `<path>` (dependency arrows with arrowhead markers), `<text>` (task label, date ticks), `<g>` (per-task and per-group groups)
- **Orientation:** `horizontal` only — task bars run left-to-right along the time axis; this is the defining characteristic of a Gantt chart.
- **Variants / modes:** `group` field enables swimlane rows with group-header separators. `progress` field enables a filled sub-bar. Dependency arrows rendered only when `depends` arrays are present.
- **Phase:** P3
- **Notes:** Uses `time` scale on the horizontal axis and `band` scale on the vertical (task/row) axis. The `band` scale accommodates variable row heights for group headers. `mj-chart-annotation kind="line"` marks today's date. `mj-chart-brush` enables horizontal time-range zoom. Dependency arrows are SVG `<path>` elements with an `<marker>` arrowhead defined in the `<defs>` block; arrow routing avoids bar overlaps with a simple right-angle elbow layout.

---

### Timeline  *(event timeline, horizontal timeline)*
- **Renderer / `type`:** `timeline` — **Primary renderer**
- **Controller:** `<mj-chart type="timeline" ...>`
- **Purpose:** Plot discrete events or milestones at their dates along a time axis; shows sequence, clustering, and temporal gaps without duration bars.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (time, bottom), `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-annotation`, `mj-chart-data-table`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Product Launch Timeline" },
    "events": [
      { "id": "e1", "label": "Alpha Release", "date": "2025-04-01", "group": "Engineering", "icon": "rocket" },
      { "id": "e2", "label": "Beta Launch",   "date": "2025-06-15", "group": "Marketing",   "icon": "flag" }
    ]
  }
  ```
  Fields: `id`; `label`; `date` (ISO-8601); `group` (lane, optional); `icon` (optional icon key from token set); `description` (optional long text shown in tooltip).
- **SVG primitives:** `<circle>` (event marker), `<line>` (stem connecting marker to axis), `<text>` (event label), `<path>` (axis spine), `<g>` (per-event group)
- **Orientation:** `horizontal` (time → x) and `vertical` (time → y) — both are conventional for timelines.
- **Variants / modes:** Multi-lane timelines (using `group`) stack event rows above the axis spine. Single-lane timelines alternate label positions above/below the spine to reduce overlap.
- **Phase:** P3
- **Notes:** Uses `time` scale. Label collision avoidance is performed after initial placement by shifting overlapping labels along the time axis. The optional `icon` renders as a small `<text>` glyph using the design-token icon font, or is omitted if icons are not loaded.

---

### Roadmap Chart  *(product roadmap, initiative map)*
- **Renderer / `type`:** `gantt` — **Variant of `gantt`**
- **Controller:** `<mj-chart type="gantt" style="roadmap" ...>`
- **Purpose:** Display product or project initiatives as horizontal bars grouped by theme or team across quarters, emphasising planning horizons rather than precise task durations.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (time, top; category, start), `mj-chart-grid`, `mj-chart-legend`, `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-data-table`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "2025–2026 Product Roadmap" },
    "tasks": [
      {
        "id": "i1",
        "label": "Mobile App v2",
        "start": "2025-Q1",
        "end":   "2025-Q3",
        "group": "Mobile",
        "status": "in-progress"
      },
      {
        "id": "i2",
        "label": "API Gateway",
        "start": "2025-Q2",
        "end":   "2026-Q1",
        "group": "Platform",
        "status": "planned"
      }
    ]
  }
  ```
  `start`/`end` accept quarter strings (`YYYY-Qn`) in addition to ISO dates — the renderer normalises these to the first and last day of the quarter before passing to the `time` scale. `status` maps to bar colour tokens (`in-progress`, `planned`, `completed`, `at-risk`).
- **SVG primitives:** `<rect>` (initiative bar, rounded corners via `rx`), `<text>`, `<g>` — same as Gantt.
- **Orientation:** `horizontal` only.
- **Variants / modes:** `style="roadmap"` suppresses dependency arrows and progress fills, uses rounded bar corners, and renders quarter/year tick marks instead of day/week ticks. No additional renderer code beyond the `gantt` renderer.
- **Phase:** P3
- **Notes:** The `gantt` renderer's `style` attribute selects a sub-mode that adjusts tick granularity and bar styling. Quarter-string normalisation is handled in the `chartmodel.js` normalisation step before the `time` scale receives domain values.

---

### Milestone Chart  *(key-date chart, diamond chart)*
- **Renderer / `type`:** `timeline` — **Variant of `timeline`**
- **Controller:** `<mj-chart type="timeline" style="milestone" ...>`
- **Purpose:** Highlight key project dates (deadlines, deliverables, go-live dates) as prominent diamond or flag markers on a time axis, with no duration bars.
- **Decomposition:** `mj-chart-plot`, `mj-chart-axis` (time, bottom), `mj-chart-title`, `mj-chart-tooltip`, `mj-chart-annotation`, `mj-chart-data-table`
- **JSON shape:**
  ```json
  {
    "meta": { "title": "Q3 Milestones" },
    "events": [
      { "id": "m1", "label": "Beta Freeze",    "date": "2025-07-31", "status": "completed" },
      { "id": "m2", "label": "GA Release",     "date": "2025-09-15", "status": "planned" }
    ]
  }
  ```
  Same `events` shape as Timeline; `status` maps to marker colour tokens.
- **SVG primitives:** `<polygon>` (diamond marker — four-point rotated square), `<line>` (stem), `<text>` (label), `<g>`
- **Orientation:** `horizontal` and `vertical` — same as Timeline.
- **Variants / modes:** `style="milestone"` selects diamond/flag markers instead of circle markers; otherwise uses the `timeline` renderer unchanged.
- **Phase:** P3
- **Notes:** The `timeline` renderer switches marker shape based on `style`. No separate renderer module is needed.

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
- **Orientation:** `horizontal` (columns left-to-right, items stacked vertically within each column). A `vertical` layout (columns stacked top-to-bottom, items arranged horizontally) is supported for narrow viewports.
- **Variants / modes:** `count-only` mode renders a simple bar chart of item counts per column (reusing the `bar` renderer) when item-level detail is not needed.
- **Phase:** P3
- **Notes:** The Kanban chart is the only chart in this category whose primary visual is a card-based layout rather than a Cartesian plot. Item cards are `<rect>` + `<text>` groups; priority is encoded by a left-border colour stripe and an `aria-label` (not colour alone). WIP-limit violations are flagged by changing the column background colour using a `--mj-chart-wip-exceeded` token and adding an `aria-alert` annotation. Uses `band` scale for columns. The `mj-chart-annotation kind="line"` draws the WIP limit bar.

---

### Resource Allocation Chart  *(resource heatmap, staffing chart, capacity chart)*
- **Renderer / `type`:** `resource` — **Primary renderer**
- **Controller:** `<mj-chart type="resource" ...>`
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
- **Variants / modes:** `style="heatmap"` collapses each resource row to a single heat-colour band (colour encodes total load percentage) instead of stacked allocation bars, useful for many resources over long time horizons. Colour also varies by pattern/texture under `forced-colors` mode.
- **Phase:** P3
- **Notes:** Uses `time` scale on the horizontal axis and `band` scale on the vertical (resource/row) axis. Over-allocation (`load` sum > `capacity` in an interval) is highlighted using `--mj-chart-overload` colour token and an `aria-label` warning; pattern fill is used alongside colour. `mj-chart-brush` enables horizontal time-range zoom. The renderer stacks multiple allocation bars vertically within a single resource row when tasks overlap in time.
