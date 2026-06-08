"""
    charts.py

    Catalog entries for the 'Charts' component group.

    This module exposes a module-level ``COMPONENTS`` list of ComponentDoc
    instances describing and demonstrating the chart and diagram components
    of the CodeCraftAI WebWorks library.
"""

from testcomponents.catalog.componentdoc import ComponentDoc


COMPONENTS = [
    ComponentDoc(
        tag="mj-branch-graph",
        title="Branch Graph",
        group="charts",
        summary="Branch network and commit history graph with lanes, merge edges, and milestone markers.",
        description=(
            "<p><code>&lt;mj-branch-graph&gt;</code> renders a Git-style "
            "branch network on a shared linear time axis. Each branch is "
            "displayed as a horizontal lane; commits appear as clickable "
            "circles; merge edges are drawn as Bezier curves between lanes. "
            "Optional phase bands shade background regions and milestone "
            "markers flag key dates. An accessible data table is always "
            "present in the shadow DOM alongside the SVG (which is "
            "<code>aria-hidden</code>).</p>"
            "<p>Data is supplied exclusively via the <code>.data</code> "
            "JavaScript property. The object must contain at minimum a "
            "<code>branches</code> array and a <code>commits</code> array; "
            "<code>merges</code>, <code>markers</code>, and "
            "<code>phases</code> are optional.</p>"
        ),
        how_to_use=(
            "<p>Add the element to the page, then assign a data object to "
            "the element&rsquo;s <code>.data</code> property. Each commit "
            "must reference a valid <code>branch</code> id. Each merge must "
            "reference a <code>from</code> and <code>to</code> commit id. "
            "Use <code>start-date</code> and <code>end-date</code> attributes "
            "to fix the visible time window; omit them to let the component "
            "auto-range. Click any commit node to open the detail panel and "
            "receive a <code>mj-node-select</code> event.</p>"
        ),
        example=(
            "<mj-branch-graph id=\"bg1\" style=\"height:260px\"></mj-branch-graph>\n"
            "<script>\n"
            "  (function () {\n"
            "    var el = document.getElementById('bg1');\n"
            "    el.data = {\n"
            "      branches: [\n"
            "        { id: 'main',    name: 'main' },\n"
            "        { id: 'feat-a',  name: 'feat/auth' },\n"
            "        { id: 'hotfix',  name: 'hotfix/login' }\n"
            "      ],\n"
            "      commits: [\n"
            "        { id: 'c1', sha: 'a1b2c3d', branch: 'main',   date: '2026-05-01', message: 'Initial commit',      author: 'alice' },\n"
            "        { id: 'c2', sha: 'e4f5a6b', branch: 'main',   date: '2026-05-04', message: 'Add CI workflow',      author: 'bob'   },\n"
            "        { id: 'c3', sha: 'f7a8b9c', branch: 'feat-a', date: '2026-05-03', message: 'Start auth feature',   author: 'carol' },\n"
            "        { id: 'c4', sha: 'd0e1f2a', branch: 'feat-a', date: '2026-05-06', message: 'OAuth integration',    author: 'carol' },\n"
            "        { id: 'c5', sha: 'b3c4d5e', branch: 'hotfix', date: '2026-05-05', message: 'Fix login redirect',   author: 'alice' },\n"
            "        { id: 'c6', sha: 'f6a7b8c', branch: 'main',   date: '2026-05-08', message: 'Merge hotfix',         author: 'alice' }\n"
            "      ],\n"
            "      merges: [\n"
            "        { from: 'c5', to: 'c6' }\n"
            "      ],\n"
            "      markers: [\n"
            "        { name: 'v1.2.0', date: '2026-05-08', type: 'release' }\n"
            "      ],\n"
            "      phases: [\n"
            "        { start: '2026-05-01', end: '2026-05-05', name: 'Sprint 1' }\n"
            "      ]\n"
            "    };\n"
            "  }());\n"
            "</script>"
        ),
        attributes=[
            ("start-date", "ISO date string; fixes the left edge of the time axis."),
            ("end-date", "ISO date string; fixes the right edge of the time axis."),
            ("density", "Compact | normal lane spacing hint."),
            ("orientation", "horizontal (default) layout hint."),
            ("readonly", "Boolean; disables interactive detail panel."),
            ("today-marker", "Boolean-like; set to 'false' to suppress the today line."),
        ],
        events=[
            ("mj-node-select", "Fired when a commit node is activated; detail contains node and branch."),
        ],
    ),
    ComponentDoc(
        tag="mj-pipeline-chart",
        title="Pipeline Chart",
        group="charts",
        summary="CI/CD pipeline stage-flow diagram with status icons, gates, and log panels.",
        description=(
            "<p><code>&lt;mj-pipeline-chart&gt;</code> renders a horizontal "
            "stage flow for a CI/CD pipeline. Each stage is a clickable "
            "rectangle carrying a status icon (<code>pending</code>, "
            "<code>running</code>, <code>passed</code>, <code>failed</code>, "
            "<code>cancelled</code>, <code>skipped</code>). Optional gate "
            "diamonds sit between stages. Clicking a stage expands a "
            "monospace log panel below the chart. An accessible ordered "
            "list mirrors the SVG content.</p>"
            "<p>Data is supplied via the <code>.data</code> JavaScript "
            "property. The object must contain a <code>stages</code> array; "
            "<code>gates</code> and <code>edges</code> are optional.</p>"
        ),
        how_to_use=(
            "<p>Assign a data object to the element&rsquo;s <code>.data</code> "
            "property. Each stage should carry an <code>id</code>, "
            "<code>name</code>, <code>status</code>, and optionally "
            "<code>duration</code> and <code>logs</code>. Add "
            "<code>edges</code> to draw arrows between non-sequential "
            "stages. Gates reference the <code>fromStage</code> id they "
            "follow. Listen for <code>mj-stage-select</code> to receive "
            "stage click events.</p>"
        ),
        example=(
            "<mj-pipeline-chart id=\"pc1\"></mj-pipeline-chart>\n"
            "<script>\n"
            "  (function () {\n"
            "    var el = document.getElementById('pc1');\n"
            "    el.data = {\n"
            "      stages: [\n"
            "        { id: 'build',   name: 'Build',   status: 'passed',  duration: '1m 12s', logs: 'Build succeeded.' },\n"
            "        { id: 'test',    name: 'Test',    status: 'passed',  duration: '3m 45s', logs: '42 tests passed.' },\n"
            "        { id: 'lint',    name: 'Lint',    status: 'passed',  duration: '22s'    },\n"
            "        { id: 'deploy',  name: 'Deploy',  status: 'running', duration: ''       },\n"
            "        { id: 'smoke',   name: 'Smoke',   status: 'pending'                     }\n"
            "      ],\n"
            "      gates: [\n"
            "        { name: 'QA gate', fromStage: 'test', status: 'approved' }\n"
            "      ],\n"
            "      edges: [\n"
            "        { from: 'build',  to: 'test'   },\n"
            "        { from: 'build',  to: 'lint'   },\n"
            "        { from: 'test',   to: 'deploy' },\n"
            "        { from: 'deploy', to: 'smoke'  }\n"
            "      ]\n"
            "    };\n"
            "  }());\n"
            "</script>"
        ),
        attributes=[
            ("orientation", "horizontal (default) layout hint."),
            ("density", "Compact | normal spacing hint."),
            ("readonly", "Boolean; disables interactive log expansion."),
            ("live", "Boolean; enables live-update mode."),
        ],
        events=[
            ("mj-stage-select", "Fired when a stage is activated; detail contains stage."),
            ("mj-stage-deselect", "Fired on Escape key dismissal."),
        ],
    ),
    ComponentDoc(
        tag="mj-gantt-chart",
        title="Gantt Chart",
        group="charts",
        summary="Project Gantt chart with task bars, percent-complete fills, dependency arrows, and milestone diamonds.",
        description=(
            "<p><code>&lt;mj-gantt-chart&gt;</code> renders a classic Gantt "
            "chart on a shared horizontal time axis. Each task appears as a "
            "labeled bar whose width spans its <code>start</code> to "
            "<code>end</code> dates. A filled inner bar represents "
            "<code>percentComplete</code>. Optional dependency arrows "
            "connect finish-to-start task pairs. Milestone diamonds and "
            "phase bands can be overlaid. An accessible data table is always "
            "present alongside the SVG.</p>"
            "<p>Data is supplied via the <code>.data</code> JavaScript "
            "property. The object must contain a <code>tasks</code> array; "
            "<code>dependencies</code>, <code>markers</code>, and "
            "<code>phases</code> are optional.</p>"
        ),
        how_to_use=(
            "<p>Assign a data object to <code>.data</code>. Each task needs "
            "<code>id</code> (or <code>name</code>), <code>name</code>, "
            "<code>start</code>, <code>end</code>, and optionally "
            "<code>percentComplete</code> and <code>status</code>. "
            "Dependencies reference task ids via <code>from</code> / "
            "<code>to</code>. Set <code>today-marker=\"false\"</code> to "
            "suppress the current-date line. Click a task bar to open the "
            "detail panel and receive <code>mj-task-select</code>.</p>"
        ),
        example=(
            "<mj-gantt-chart id=\"gc1\" style=\"height:280px\"></mj-gantt-chart>\n"
            "<script>\n"
            "  (function () {\n"
            "    var el = document.getElementById('gc1');\n"
            "    el.data = {\n"
            "      tasks: [\n"
            "        { id: 't1', name: 'Requirements',    start: '2026-04-01', end: '2026-04-10', percentComplete: 100, status: 'done'        },\n"
            "        { id: 't2', name: 'Design',          start: '2026-04-08', end: '2026-04-20', percentComplete: 100, status: 'done'        },\n"
            "        { id: 't3', name: 'Backend dev',     start: '2026-04-18', end: '2026-05-10', percentComplete:  75, status: 'in-progress' },\n"
            "        { id: 't4', name: 'Frontend dev',    start: '2026-04-22', end: '2026-05-14', percentComplete:  60, status: 'in-progress' },\n"
            "        { id: 't5', name: 'QA & testing',    start: '2026-05-12', end: '2026-05-26', percentComplete:   0, status: 'planned'     },\n"
            "        { id: 't6', name: 'Release',         start: '2026-05-27', end: '2026-05-28', percentComplete:   0, status: 'planned'     }\n"
            "      ],\n"
            "      dependencies: [\n"
            "        { from: 't1', to: 't2' },\n"
            "        { from: 't3', to: 't5' },\n"
            "        { from: 't4', to: 't5' },\n"
            "        { from: 't5', to: 't6' }\n"
            "      ],\n"
            "      markers: [\n"
            "        { name: 'Code freeze', date: '2026-05-12' }\n"
            "      ],\n"
            "      phases: [\n"
            "        { name: 'Phase 1', start: '2026-04-01', end: '2026-04-20' },\n"
            "        { name: 'Phase 2', start: '2026-04-21', end: '2026-05-28' }\n"
            "      ]\n"
            "    };\n"
            "  }());\n"
            "</script>"
        ),
        attributes=[
            ("scale", "day | week | month; time-axis granularity."),
            ("start-date", "ISO date string; fixes the left edge of the time axis."),
            ("end-date", "ISO date string; fixes the right edge of the time axis."),
            ("today-marker", "Set to 'false' to suppress the today line."),
            ("show-dependencies", "Set to 'false' to hide dependency arrows."),
            ("show-percent", "Boolean; show percent-complete labels on bars."),
            ("density", "Compact | normal row spacing."),
        ],
        events=[
            ("mj-task-select", "Fired when a task bar is activated; detail contains task."),
            ("mj-task-deselect", "Fired when the detail panel is closed."),
        ],
    ),
    ComponentDoc(
        tag="mj-roadmap-chart",
        title="Roadmap Chart",
        group="charts",
        summary="Initiative roadmap with swimlane rows and calendar or named-bucket columns.",
        description=(
            "<p><code>&lt;mj-roadmap-chart&gt;</code> renders a strategic "
            "roadmap grid. Rows are swimlanes (teams, products, or themes); "
            "columns are calendar periods (quarters, months, or half-years) "
            "or custom named buckets. Initiatives are plotted as colored "
            "bars inside the appropriate swimlane/column cell with a status "
            "icon. An accessible data table is always present.</p>"
            "<p>Data is supplied via the <code>.data</code> JavaScript "
            "property. The object must contain <code>swimlanes</code> and "
            "<code>initiatives</code> arrays. For bucket mode also supply "
            "a <code>buckets</code> array; for calendar mode set "
            "<code>start-date</code> and <code>end-date</code> attributes.</p>"
        ),
        how_to_use=(
            "<p>Set <code>mode=\"calendar\"</code> (default) for automatic "
            "quarter/month columns or <code>mode=\"bucket\"</code> for named "
            "buckets. Each initiative needs <code>name</code>, "
            "<code>swimlaneId</code>, <code>status</code>, and either "
            "<code>columnId</code> (bucket mode) or date fields "
            "(<code>startDate</code> / <code>endDate</code>) for calendar "
            "mode. Click an initiative bar to receive "
            "<code>mj-initiative-select</code>.</p>"
        ),
        example=(
            "<mj-roadmap-chart id=\"rc1\" mode=\"bucket\"></mj-roadmap-chart>\n"
            "<script>\n"
            "  (function () {\n"
            "    var el = document.getElementById('rc1');\n"
            "    el.data = {\n"
            "      swimlanes: [\n"
            "        { id: 'platform', name: 'Platform' },\n"
            "        { id: 'mobile',   name: 'Mobile'   },\n"
            "        { id: 'data',     name: 'Data'     }\n"
            "      ],\n"
            "      buckets: [\n"
            "        { id: 'q1', name: 'Q1 2026' },\n"
            "        { id: 'q2', name: 'Q2 2026' },\n"
            "        { id: 'q3', name: 'Q3 2026' },\n"
            "        { id: 'q4', name: 'Q4 2026' }\n"
            "      ],\n"
            "      initiatives: [\n"
            "        { id: 'i1', name: 'API Gateway v2',   swimlaneId: 'platform', columnId: 'q1', status: 'done'        },\n"
            "        { id: 'i2', name: 'Auth SSO',         swimlaneId: 'platform', columnId: 'q2', status: 'in-progress' },\n"
            "        { id: 'i3', name: 'iOS redesign',     swimlaneId: 'mobile',   columnId: 'q2', status: 'planned'     },\n"
            "        { id: 'i4', name: 'Android widgets',  swimlaneId: 'mobile',   columnId: 'q3', status: 'planned'     },\n"
            "        { id: 'i5', name: 'Data lake v3',     swimlaneId: 'data',     columnId: 'q1', status: 'at-risk'     },\n"
            "        { id: 'i6', name: 'Real-time streams',swimlaneId: 'data',     columnId: 'q3', status: 'planned'     }\n"
            "      ]\n"
            "    };\n"
            "  }());\n"
            "</script>"
        ),
        attributes=[
            ("mode", "calendar (default) | bucket column layout."),
            ("scale", "quarter | month | half-year for calendar mode."),
            ("start-date", "ISO date string; calendar mode range start."),
            ("end-date", "ISO date string; calendar mode range end."),
            ("today-marker", "Set to 'false' to suppress the today indicator."),
            ("density", "Compact | normal row spacing."),
        ],
        events=[
            ("mj-initiative-select", "Fired when an initiative bar is activated; detail contains initiative."),
            ("mj-initiative-deselect", "Fired on Escape key dismissal."),
        ],
    ),
    ComponentDoc(
        tag="mj-milestone-timeline",
        title="Milestone Timeline",
        group="charts",
        summary="Single horizontal timeline axis of named milestones, key dates, and phase bands.",
        description=(
            "<p><code>&lt;mj-milestone-timeline&gt;</code> is the lightest "
            "timeline visualization in the library. It draws a single "
            "horizontal axis and plots named markers above and below it. "
            "Each marker has a shape that reflects its type: "
            "<code>release</code> &rarr; diamond, "
            "<code>freeze</code> &rarr; triangle, "
            "<code>milestone</code> / <code>tag</code> &rarr; circle. "
            "Past markers are rendered at reduced opacity. Optional phase "
            "bands shade background regions. An accessible ordered list "
            "mirrors all markers.</p>"
            "<p>Data is supplied via the <code>.data</code> JavaScript "
            "property. The object must contain a <code>markers</code> array; "
            "<code>phases</code> is optional.</p>"
        ),
        how_to_use=(
            "<p>Assign a data object to <code>.data</code>. Each marker "
            "needs <code>name</code>, <code>date</code>, and optionally "
            "<code>type</code> (<code>release</code>, <code>freeze</code>, "
            "<code>milestone</code>, <code>tag</code>) and "
            "<code>description</code>. Set <code>start-date</code> and "
            "<code>end-date</code> attributes to fix the visible range. "
            "Click a marker to open a detail popover and receive "
            "<code>mj-marker-select</code>.</p>"
        ),
        example=(
            "<mj-milestone-timeline id=\"mt1\"></mj-milestone-timeline>\n"
            "<script>\n"
            "  (function () {\n"
            "    var el = document.getElementById('mt1');\n"
            "    el.data = {\n"
            "      markers: [\n"
            "        { name: 'v2.0 branch cut',  date: '2026-04-15', type: 'freeze',    description: 'No new features after this date.' },\n"
            "        { name: 'RC1',              date: '2026-04-28', type: 'tag',        description: 'First release candidate.' },\n"
            "        { name: 'v2.0 GA',          date: '2026-05-12', type: 'release',   description: 'General availability release.' },\n"
            "        { name: 'Sprint 14 start',  date: '2026-05-18', type: 'milestone'  },\n"
            "        { name: 'v2.1 planning',    date: '2026-06-02', type: 'milestone'  }\n"
            "      ],\n"
            "      phases: [\n"
            "        { name: 'Stabilisation', start: '2026-04-15', end: '2026-05-12' }\n"
            "      ]\n"
            "    };\n"
            "  }());\n"
            "</script>"
        ),
        attributes=[
            ("start-date", "ISO date string; fixes the left edge of the time axis."),
            ("end-date", "ISO date string; fixes the right edge of the time axis."),
            ("orientation", "horizontal (default) layout hint."),
            ("density", "Compact | normal marker spacing."),
            ("today-marker", "Set to 'false' to suppress the today line."),
        ],
        events=[
            ("mj-marker-select", "Fired when a milestone marker is activated; detail contains marker."),
            ("mj-marker-deselect", "Fired when the detail popover is dismissed."),
        ],
    ),
    ComponentDoc(
        tag="mj-burndown-chart",
        title="Burndown Chart",
        group="charts",
        summary="Sprint burndown or burnup chart with an ideal line, actual line, and scope-change markers.",
        description=(
            "<p><code>&lt;mj-burndown-chart&gt;</code> plots story points "
            "(or any work unit) remaining (burndown) or completed (burnup) "
            "over the sprint calendar. A dashed ideal line provides the "
            "reference trajectory. When the actual line falls behind the "
            "ideal a &ldquo;Behind schedule&rdquo; badge is shown. Vertical "
            "scope-change markers flag days when work was added or removed. "
            "An accessible data table is always present.</p>"
            "<p>Data is supplied via the <code>.data</code> JavaScript "
            "property. The object must contain <code>dailyValues</code> "
            "(array of <code>{date, value}</code>) and "
            "<code>totalScope</code>. <code>scopeChanges</code> is "
            "optional.</p>"
        ),
        how_to_use=(
            "<p>Assign a data object to <code>.data</code>. Set "
            "<code>mode=\"burndown\"</code> (default) or "
            "<code>mode=\"burnup\"</code>. Set <code>unit</code> to the "
            "label shown in tooltips (e.g. <code>points</code>, "
            "<code>tasks</code>). Each <code>dailyValues</code> entry "
            "needs <code>date</code> and <code>value</code>. Points beyond "
            "today are not plotted as actual data. Set "
            "<code>show-ideal=\"false\"</code> to hide the reference "
            "line.</p>"
        ),
        example=(
            "<mj-burndown-chart id=\"bd1\" mode=\"burndown\" unit=\"points\"></mj-burndown-chart>\n"
            "<script>\n"
            "  (function () {\n"
            "    var el = document.getElementById('bd1');\n"
            "    el.data = {\n"
            "      totalScope: 80,\n"
            "      dailyValues: [\n"
            "        { date: '2026-05-01', value: 80 },\n"
            "        { date: '2026-05-04', value: 72 },\n"
            "        { date: '2026-05-05', value: 65 },\n"
            "        { date: '2026-05-06', value: 60 },\n"
            "        { date: '2026-05-07', value: 54 },\n"
            "        { date: '2026-05-08', value: 50 },\n"
            "        { date: '2026-05-11', value: 44 },\n"
            "        { date: '2026-05-12', value: 39 },\n"
            "        { date: '2026-05-13', value: 35 },\n"
            "        { date: '2026-05-14', value: 28 },\n"
            "        { date: '2026-05-15', value: 21 }\n"
            "      ],\n"
            "      scopeChanges: [\n"
            "        { date: '2026-05-06', delta: 5 }\n"
            "      ]\n"
            "    };\n"
            "  }());\n"
            "</script>"
        ),
        attributes=[
            ("mode", "burndown (default) | burnup direction of the chart."),
            ("unit", "Label for the Y axis and tooltips, e.g. points or tasks."),
            ("start-date", "ISO date string; fixes the left edge of the time axis."),
            ("end-date", "ISO date string; fixes the right edge of the time axis."),
            ("today-marker", "Set to 'false' to suppress the today line."),
            ("show-ideal", "Set to 'false' to hide the ideal reference line."),
            ("show-scope-changes", "Set to 'false' to hide scope-change markers."),
        ],
        events=[
            ("mj-point-select", "Fired when a data point circle is activated; detail contains point."),
            ("mj-point-deselect", "Fired on Escape key dismissal."),
        ],
    ),
    ComponentDoc(
        tag="mj-cumulative-flow",
        title="Cumulative Flow Diagram",
        group="charts",
        summary="Stacked area chart of work items per workflow state over time, with a toggleable state legend.",
        description=(
            "<p><code>&lt;mj-cumulative-flow&gt;</code> renders a stacked "
            "area (CFD) chart. Each band represents a workflow state "
            "(<em>Backlog</em>, <em>In Progress</em>, <em>Done</em>, etc.). "
            "The band height on any day shows how many items were in that "
            "state. Wide bands signal queuing; converging bands signal "
            "throughput improvement. The legend doubles as a toggle control: "
            "clicking a state hides or shows its band. An accessible data "
            "table is always present.</p>"
            "<p>Data is supplied via the <code>.data</code> JavaScript "
            "property. The object must contain a <code>states</code> array "
            "and a <code>dailySeries</code> array. Each daily-series row is "
            "an object keyed by state id plus a <code>date</code> field.</p>"
        ),
        how_to_use=(
            "<p>Assign a data object to <code>.data</code>. Define "
            "<code>states</code> as an array of <code>{id, name}</code> "
            "objects. Each <code>dailySeries</code> entry must have a "
            "<code>date</code> field and a numeric count for every state id. "
            "Set <code>normalized</code> to show percentages instead of "
            "absolute counts.</p>"
        ),
        example=(
            "<mj-cumulative-flow id=\"cfd1\"></mj-cumulative-flow>\n"
            "<script>\n"
            "  (function () {\n"
            "    var el = document.getElementById('cfd1');\n"
            "    el.data = {\n"
            "      states: [\n"
            "        { id: 'backlog',     name: 'Backlog'     },\n"
            "        { id: 'ready',       name: 'Ready'       },\n"
            "        { id: 'inprogress',  name: 'In Progress' },\n"
            "        { id: 'review',      name: 'In Review'   },\n"
            "        { id: 'done',        name: 'Done'        }\n"
            "      ],\n"
            "      dailySeries: [\n"
            "        { date: '2026-05-01', backlog: 30, ready: 8,  inprogress: 5, review: 2, done:  0 },\n"
            "        { date: '2026-05-04', backlog: 27, ready: 9,  inprogress: 6, review: 3, done:  5 },\n"
            "        { date: '2026-05-05', backlog: 24, ready: 10, inprogress: 7, review: 2, done:  9 },\n"
            "        { date: '2026-05-06', backlog: 22, ready: 8,  inprogress: 7, review: 4, done: 12 },\n"
            "        { date: '2026-05-07', backlog: 20, ready: 7,  inprogress: 8, review: 3, done: 16 },\n"
            "        { date: '2026-05-08', backlog: 18, ready: 6,  inprogress: 6, review: 4, done: 21 },\n"
            "        { date: '2026-05-11', backlog: 15, ready: 5,  inprogress: 7, review: 3, done: 26 }\n"
            "      ]\n"
            "    };\n"
            "  }());\n"
            "</script>"
        ),
        attributes=[
            ("type", "area (default) chart type hint."),
            ("normalized", "Boolean; display percentages instead of absolute counts."),
            ("start-date", "ISO date string; fixes the left edge of the time axis."),
            ("end-date", "ISO date string; fixes the right edge of the time axis."),
            ("today-marker", "Set to 'false' to suppress the today line."),
        ],
        events=[
            ("mj-state-toggle", "Fired when a legend button is pressed; detail contains stateId and visible."),
        ],
    ),
    ComponentDoc(
        tag="mj-velocity-chart",
        title="Velocity Chart",
        group="charts",
        summary="Grouped bar chart of committed vs completed work per sprint with a rolling-average line.",
        description=(
            "<p><code>&lt;mj-velocity-chart&gt;</code> plots sprint velocity "
            "as a grouped bar chart. Each sprint group has a lighter "
            "&ldquo;committed&rdquo; bar and a solid &ldquo;completed&rdquo; "
            "bar. A rolling-average polyline overlays the chart. Sprints "
            "where the team significantly under-delivered are labeled "
            "&ldquo;Under-delivered&rdquo; in red; over-delivered sprints "
            "show &ldquo;Exceeded&rdquo; in green. An accessible data table "
            "is always present.</p>"
            "<p>Data is supplied via the <code>.data</code> JavaScript "
            "property. The object must contain a <code>sprints</code> "
            "array where each sprint has <code>name</code>, "
            "<code>committed</code>, and <code>completed</code>.</p>"
        ),
        how_to_use=(
            "<p>Assign a data object to <code>.data</code>. Set "
            "<code>unit</code> to the label for the Y axis (default "
            "<code>points</code>). Set <code>rolling-window</code> to "
            "control how many sprints the average spans. Use "
            "<code>bar-mode=\"grouped\"</code> (default) or "
            "<code>bar-mode=\"overlay\"</code> to stack the committed bar "
            "behind the completed bar. Listen for "
            "<code>mj-sprint-select</code> on bar click.</p>"
        ),
        example=(
            "<mj-velocity-chart id=\"vc1\" unit=\"points\" rolling-window=\"3\"></mj-velocity-chart>\n"
            "<script>\n"
            "  (function () {\n"
            "    var el = document.getElementById('vc1');\n"
            "    el.data = {\n"
            "      sprints: [\n"
            "        { name: 'Sprint 8',  committed: 40, completed: 37 },\n"
            "        { name: 'Sprint 9',  committed: 42, completed: 45 },\n"
            "        { name: 'Sprint 10', committed: 44, completed: 40 },\n"
            "        { name: 'Sprint 11', committed: 45, completed: 48 },\n"
            "        { name: 'Sprint 12', committed: 46, completed: 43 },\n"
            "        { name: 'Sprint 13', committed: 48, completed: 50 },\n"
            "        { name: 'Sprint 14', committed: 48, completed: 22 }\n"
            "      ]\n"
            "    };\n"
            "  }());\n"
            "</script>"
        ),
        attributes=[
            ("unit", "Label for the Y axis, e.g. points or tasks."),
            ("bar-mode", "grouped (default) | overlay bar rendering."),
            ("rolling-window", "Number of sprints for the rolling average (default 3)."),
            ("show-average", "Set to 'false' to hide the rolling-average line."),
            ("show-committed", "Set to 'false' to hide the committed bar."),
        ],
        events=[
            ("mj-sprint-select", "Fired when a sprint bar group is activated; detail contains sprint."),
            ("mj-sprint-deselect", "Fired on Escape key dismissal."),
        ],
    ),
    ComponentDoc(
        tag="mj-dependency-graph",
        title="Dependency Graph",
        group="charts",
        summary="Directed node/edge dependency graph with critical path highlighting and cycle detection.",
        description=(
            "<p><code>&lt;mj-dependency-graph&gt;</code> renders a "
            "directed acyclic graph (DAG) of work items or module "
            "dependencies. Nodes are laid out by topological level. "
            "Critical-path nodes and edges are highlighted in amber. "
            "If the data contains a cycle a banner alert is shown and "
            "<code>mj-cycle-detected</code> is emitted. An accessible "
            "dependency list mirrors the graph.</p>"
            "<p>Data is supplied via the <code>.data</code> JavaScript "
            "property. The object must contain <code>nodes</code> and "
            "<code>edges</code> arrays; <code>criticalPath</code> (array "
            "of node ids) is optional.</p>"
        ),
        how_to_use=(
            "<p>Assign a data object to <code>.data</code>. Each node needs "
            "<code>id</code> (or <code>name</code>), <code>name</code>, "
            "and optionally <code>status</code> "
            "(<code>todo</code>, <code>in-progress</code>, "
            "<code>done</code>, <code>blocked</code>) and "
            "<code>estimate</code>. Each edge needs <code>from</code> and "
            "<code>to</code> node ids. Supply <code>criticalPath</code> as "
            "an array of node ids to highlight that path. Set "
            "<code>show-critical-path=\"false\"</code> to disable "
            "highlighting.</p>"
        ),
        example=(
            "<mj-dependency-graph id=\"dg1\"></mj-dependency-graph>\n"
            "<script>\n"
            "  (function () {\n"
            "    var el = document.getElementById('dg1');\n"
            "    el.data = {\n"
            "      nodes: [\n"
            "        { id: 'design',   name: 'Design',       status: 'done'        },\n"
            "        { id: 'api',      name: 'API layer',    status: 'done'        },\n"
            "        { id: 'db',       name: 'DB schema',    status: 'done'        },\n"
            "        { id: 'backend',  name: 'Backend',      status: 'in-progress' },\n"
            "        { id: 'frontend', name: 'Frontend',     status: 'in-progress' },\n"
            "        { id: 'tests',    name: 'Tests',        status: 'todo'        },\n"
            "        { id: 'deploy',   name: 'Deployment',   status: 'todo'        }\n"
            "      ],\n"
            "      edges: [\n"
            "        { from: 'design',   to: 'api'      },\n"
            "        { from: 'design',   to: 'frontend' },\n"
            "        { from: 'api',      to: 'backend'  },\n"
            "        { from: 'db',       to: 'backend'  },\n"
            "        { from: 'backend',  to: 'tests'    },\n"
            "        { from: 'frontend', to: 'tests'    },\n"
            "        { from: 'tests',    to: 'deploy'   }\n"
            "      ],\n"
            "      criticalPath: ['design', 'api', 'backend', 'tests', 'deploy']\n"
            "    };\n"
            "  }());\n"
            "</script>"
        ),
        attributes=[
            ("graph-type", "dag (default) graph layout type."),
            ("show-critical-path", "Set to 'false' to disable critical-path highlighting."),
            ("show-minimap", "Boolean; show a minimap overlay (planned)."),
            ("layout", "topological (default) layout algorithm hint."),
        ],
        events=[
            ("mj-node-select", "Fired when a node is activated; detail contains node."),
            ("mj-node-deselect", "Fired when the detail panel is closed."),
            ("mj-cycle-detected", "Fired when a cycle is found in the graph; detail contains cycles."),
            ("mj-data-load", "Fired after each draw; detail contains nodes, edges, and hasCycles counts."),
        ],
    ),
    ComponentDoc(
        tag="mj-workflow-diagram",
        title="Workflow Diagram",
        group="charts",
        summary="State machine or cross-actor swimlane process-flow diagram with animated current-state indicator.",
        description=(
            "<p><code>&lt;mj-workflow-diagram&gt;</code> renders a "
            "state-machine diagram or a cross-actor swimlane process flow. "
            "Node shapes vary by type: filled circle for <em>start</em>, "
            "double circle for <em>end</em>, diamond for <em>decision</em>, "
            "and rounded rectangle for ordinary <em>state</em> nodes. "
            "The current state is highlighted with a pulsing ring. "
            "Transition edges carry optional labels. An accessible "
            "definition list mirrors the state/transition structure.</p>"
            "<p>Data is supplied via the <code>.data</code> JavaScript "
            "property. The object must contain <code>states</code> and "
            "<code>transitions</code> arrays; <code>actors</code> is "
            "required for swimlane mode.</p>"
        ),
        how_to_use=(
            "<p>Assign a data object to <code>.data</code>. Each state "
            "needs <code>id</code>, <code>name</code>, and optionally "
            "<code>type</code> (<code>start</code>, <code>end</code>, "
            "<code>decision</code>, or <code>state</code>). Each transition "
            "needs <code>from</code>, <code>to</code>, and optionally "
            "<code>label</code>. Set the <code>current-state</code> "
            "attribute to the id of the active state. For swimlane mode set "
            "<code>diagram-type=\"swimlane\"</code> and include "
            "<code>actors</code>.</p>"
        ),
        example=(
            "<mj-workflow-diagram id=\"wd1\" current-state=\"review\"></mj-workflow-diagram>\n"
            "<script>\n"
            "  (function () {\n"
            "    var el = document.getElementById('wd1');\n"
            "    el.data = {\n"
            "      states: [\n"
            "        { id: 'start',   name: 'Start',       type: 'start'    },\n"
            "        { id: 'draft',   name: 'Draft',       type: 'state'    },\n"
            "        { id: 'review',  name: 'In Review',   type: 'state'    },\n"
            "        { id: 'approve', name: 'Approve?',    type: 'decision' },\n"
            "        { id: 'merged',  name: 'Merged',      type: 'state'    },\n"
            "        { id: 'end',     name: 'End',         type: 'end'      }\n"
            "      ],\n"
            "      transitions: [\n"
            "        { from: 'start',   to: 'draft',   label: 'create'    },\n"
            "        { from: 'draft',   to: 'review',  label: 'submit'    },\n"
            "        { from: 'review',  to: 'approve', label: 'check'     },\n"
            "        { from: 'approve', to: 'merged',  label: 'yes'       },\n"
            "        { from: 'approve', to: 'draft',   label: 'no'        },\n"
            "        { from: 'merged',  to: 'end',     label: 'close'     }\n"
            "      ]\n"
            "    };\n"
            "  }());\n"
            "</script>"
        ),
        attributes=[
            ("diagram-type", "state (default) | swimlane layout mode."),
            ("swimlane-direction", "horizontal (default) swimlane orientation."),
            ("current-state", "Id of the currently active state; triggers the pulsing ring."),
            ("layout", "topological (default) layout algorithm hint."),
            ("show-labels", "Set to 'false' to hide transition edge labels."),
        ],
        events=[
            ("mj-node-select", "Fired when a state node is activated; detail contains node."),
            ("mj-transition-select", "Fired when a transition edge is activated; detail contains transition."),
            ("mj-state-change", "Fired when the current-state attribute changes; detail contains from and to."),
            ("mj-data-load", "Fired after each draw; detail contains states, transitions, and actors counts."),
        ],
    ),
    ComponentDoc(
        tag="mj-release-calendar",
        title="Release Calendar",
        group="charts",
        summary="Month/week calendar grid showing releases, freezes, blackouts, and key dates as event chips.",
        description=(
            "<p><code>&lt;mj-release-calendar&gt;</code> renders a "
            "navigable calendar grid (month or week view) that overlays "
            "release-lifecycle events as colored chips. Event types carry "
            "semantic colors and icons: "
            "<em>release</em> (green rocket), "
            "<em>freeze</em> (amber snowflake), "
            "<em>blackout</em> (red stop), "
            "<em>milestone</em> (blue diamond), "
            "<em>holiday</em> (muted calendar). "
            "Multi-day events span from their start to end dates. "
            "Clicking a chip opens a detail popover. Navigation arrows "
            "and a Today button are built in. An accessible event list "
            "is always present.</p>"
            "<p>Data is supplied via the <code>.data</code> JavaScript "
            "property. The object must contain an <code>events</code> "
            "array.</p>"
        ),
        how_to_use=(
            "<p>Assign a data object to <code>.data</code>. Each event "
            "needs <code>id</code> (or <code>name</code>), <code>name</code>, "
            "<code>type</code>, and <code>startDate</code> (or "
            "<code>start</code>). For multi-day events also set "
            "<code>endDate</code>. Optionally add <code>description</code> "
            "and <code>url</code>. Set <code>current-date</code> to open "
            "the calendar at a specific month. Listen for "
            "<code>mj-event-select</code> on chip click and "
            "<code>mj-period-change</code> on navigation.</p>"
        ),
        example=(
            "<mj-release-calendar id=\"cal1\"\n"
            "  current-date=\"2026-05-01\"></mj-release-calendar>\n"
            "<script>\n"
            "  (function () {\n"
            "    var el = document.getElementById('cal1');\n"
            "    el.data = {\n"
            "      events: [\n"
            "        { id: 'ev1', name: 'v3.1.0 release', type: 'release',   startDate: '2026-05-08' },\n"
            "        { id: 'ev2', name: 'Code freeze',    type: 'freeze',    startDate: '2026-05-05', endDate: '2026-05-08' },\n"
            "        { id: 'ev3', name: 'EU downtime',    type: 'blackout',  startDate: '2026-05-20', endDate: '2026-05-21' },\n"
            "        { id: 'ev4', name: 'Sprint 15 demo', type: 'milestone', startDate: '2026-05-15' },\n"
            "        { id: 'ev5', name: 'Memorial Day',   type: 'holiday',   startDate: '2026-05-25' },\n"
            "        { id: 'ev6', name: 'v3.2.0-beta',    type: 'release',   startDate: '2026-05-29', description: 'Early access beta.' }\n"
            "      ]\n"
            "    };\n"
            "  }());\n"
            "</script>"
        ),
        attributes=[
            ("view", "month (default) | week calendar view."),
            ("current-date", "ISO date string; the month shown on initial render."),
            ("today-marker", "Set to 'false' to suppress today cell highlight."),
            ("first-day-of-week", "0 = Sunday (default), 1 = Monday week start."),
            ("locale", "BCP 47 locale tag for date formatting."),
        ],
        events=[
            ("mj-event-select", "Fired when an event chip is clicked; detail contains event."),
            ("mj-period-change", "Fired on navigation; detail contains start, end, and view."),
            ("mj-view-change", "Fired when the month/week view is switched; detail contains view."),
        ],
    ),
    ComponentDoc(
        tag="mj-env-promotion-chart",
        title="Environment Promotion Chart",
        group="charts",
        summary="Artifact promotion track showing version and health per environment with inline approval gates.",
        description=(
            "<p><code>&lt;mj-env-promotion-chart&gt;</code> renders a "
            "horizontal track of environment cards (Dev &rarr; Staging "
            "&rarr; Production, etc.). Each card shows the deployed "
            "version, a health indicator, and &mdash; when applicable "
            "&mdash; a last-promotion timestamp. Approval gate diamonds "
            "sit between cards. When a gate is in <code>pending</code> "
            "state and the component is not <code>readonly</code>, "
            "inline Approve and Reject buttons are rendered. Clicking "
            "Approve emits a cancelable <code>mj-gate-action</code> "
            "event and transitions the gate to <code>approved</code> "
            "unless the event is prevented.</p>"
            "<p>Data is supplied via the <code>.data</code> JavaScript "
            "property. The object must contain an <code>environments</code> "
            "array; <code>gates</code> and <code>promotions</code> are "
            "optional.</p>"
        ),
        how_to_use=(
            "<p>Assign a data object to <code>.data</code>. Each "
            "environment needs <code>id</code> (or <code>name</code>), "
            "<code>name</code>, <code>version</code>, and "
            "<code>health</code> (<code>healthy</code>, "
            "<code>degraded</code>, <code>down</code>, or "
            "<code>unknown</code>). Each gate needs <code>fromEnv</code> "
            "(the environment id it follows) and <code>status</code> "
            "(<code>pending</code>, <code>approved</code>, "
            "<code>rejected</code>, or <code>auto</code>). Listen for "
            "<code>mj-gate-action</code> and call "
            "<code>event.preventDefault()</code> to handle approval "
            "server-side.</p>"
        ),
        example=(
            "<mj-env-promotion-chart id=\"ep1\"\n"
            "  artifact-id=\"my-service\"></mj-env-promotion-chart>\n"
            "<script>\n"
            "  (function () {\n"
            "    var el = document.getElementById('ep1');\n"
            "    el.data = {\n"
            "      environments: [\n"
            "        { id: 'dev',     name: 'Dev',        version: 'v3.2.1-sha.abc', health: 'healthy',  lastPromotion: '2026-05-20T10:00:00Z' },\n"
            "        { id: 'staging', name: 'Staging',    version: 'v3.2.0',         health: 'degraded', lastPromotion: '2026-05-18T14:30:00Z' },\n"
            "        { id: 'prod',    name: 'Production', version: 'v3.1.5',         health: 'healthy',  lastPromotion: '2026-05-10T09:00:00Z' }\n"
            "      ],\n"
            "      gates: [\n"
            "        { fromEnv: 'dev',     status: 'approved' },\n"
            "        { fromEnv: 'staging', status: 'pending'  }\n"
            "      ]\n"
            "    };\n"
            "  }());\n"
            "</script>"
        ),
        attributes=[
            ("orientation", "horizontal (default) track orientation."),
            ("density", "Compact | normal card spacing."),
            ("readonly", "Boolean; hides Approve/Reject buttons on pending gates."),
            ("live", "Boolean; enables live-update polling mode."),
            ("artifact-id", "Display label for the artifact being promoted."),
        ],
        events=[
            ("mj-environment-select", "Fired when an environment card is clicked; detail contains environment."),
            ("mj-environment-deselect", "Fired when the detail panel is closed."),
            ("mj-gate-action", "Cancelable; fired on Approve or Reject click; detail contains gate and action."),
            ("mj-data-load", "Fired after each draw; detail contains environments and pendingGates counts."),
        ],
    ),
    ComponentDoc(
        tag="mj-build-status-board",
        title="Build Status Board",
        group="charts",
        summary="Sortable, filterable big-board table of pipeline build and deploy statuses with live-update support.",
        description=(
            "<p><code>&lt;mj-build-status-board&gt;</code> is a grid "
            "big-board that lists CI/CD pipeline runs. Each row carries "
            "a pipeline name (optionally linked), a color-coded status "
            "badge, deploy target, last-run time, duration, and actor. "
            "Column headers are clickable sort controls. An inline "
            "filter bar lets users narrow by status or name. Rows are "
            "selectable via checkboxes; a bulk-action bar appears when "
            "one or more rows are selected. Pagination is built in. "
            "When <code>live</code> is set the component emits "
            "<code>mj-poll-tick</code> on the configured interval so "
            "the host can refresh data.</p>"
            "<p>Data is supplied via the <code>.data</code> JavaScript "
            "property. The object must contain a <code>rows</code> "
            "array.</p>"
        ),
        how_to_use=(
            "<p>Assign a data object to <code>.data</code>. Each row "
            "needs <code>id</code> (or <code>name</code>), <code>name</code>, "
            "<code>status</code>, and optionally <code>deployTarget</code>, "
            "<code>lastRun</code> (ISO datetime), <code>duration</code> "
            "(seconds), <code>actor</code>, and <code>url</code>. "
            "Use the <code>updateRowStatus(rowId, newStatus)</code> method "
            "to apply live updates. Set <code>live</code> to activate "
            "the polling badge and <code>mj-poll-tick</code> events. "
            "Set <code>page-size</code> to control pagination.</p>"
        ),
        example=(
            "<mj-build-status-board id=\"bsb1\" page-size=\"10\"></mj-build-status-board>\n"
            "<script>\n"
            "  (function () {\n"
            "    var el = document.getElementById('bsb1');\n"
            "    el.data = {\n"
            "      rows: [\n"
            "        { id: 'r1', name: 'main / build',       status: 'passed',    deployTarget: 'staging',    lastRun: '2026-05-22T08:10:00Z', duration: 132, actor: 'alice'  },\n"
            "        { id: 'r2', name: 'main / deploy',      status: 'running',   deployTarget: 'staging',    lastRun: '2026-05-22T08:12:00Z', duration: 0,   actor: 'ci-bot' },\n"
            "        { id: 'r3', name: 'feat/auth / build',  status: 'failed',    deployTarget: '',           lastRun: '2026-05-22T07:55:00Z', duration: 74,  actor: 'carol'  },\n"
            "        { id: 'r4', name: 'hotfix / build',     status: 'passed',    deployTarget: 'prod',       lastRun: '2026-05-21T22:00:00Z', duration: 98,  actor: 'bob'    },\n"
            "        { id: 'r5', name: 'hotfix / deploy',    status: 'passed',    deployTarget: 'prod',       lastRun: '2026-05-21T22:03:00Z', duration: 45,  actor: 'bob'    },\n"
            "        { id: 'r6', name: 'nightly / test',     status: 'cancelled', deployTarget: '',           lastRun: '2026-05-22T02:00:00Z', duration: 0,   actor: 'cron'   }\n"
            "      ]\n"
            "    };\n"
            "  }());\n"
            "</script>"
        ),
        attributes=[
            ("group-by", "Column name to group rows by."),
            ("density", "Compact | normal row height."),
            ("live", "Boolean; activates the live-update badge and poll-tick events."),
            ("filter-status", "Pre-set status filter value."),
            ("filter-pattern", "Pre-set name filter string."),
            ("page-size", "Rows per page (default 25)."),
            ("sort-column", "Initial sort column key (default lastRun)."),
            ("sort-direction", "asc | desc (default desc)."),
        ],
        events=[
            ("mj-row-select", "Fired when a row checkbox is toggled; detail contains row and selected."),
            ("mj-row-activate", "Fired when a pipeline link is clicked; detail contains row."),
            ("mj-sort-change", "Fired when the sort column or direction changes; detail contains column and direction."),
            ("mj-filter-change", "Fired when the status filter dropdown changes; detail contains status and pattern."),
            ("mj-status-change", "Fired by updateRowStatus(); detail contains rowId, previous, and current."),
            ("mj-poll-tick", "Fired on each polling interval when live is enabled."),
            ("mj-data-load", "Fired after each render; detail contains rows count."),
        ],
    ),
]
