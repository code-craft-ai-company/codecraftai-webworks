"""
    charts.py

    Catalog entries for the 'Charts' component group.

    This module exposes a module-level ``COMPONENTS`` list of ComponentDoc
    instances describing and demonstrating the project-management chart and
    diagram components of the CodeCraftAI WebWorks library (mj-branch-graph,
    mj-pipeline-chart, mj-gantt-chart, mj-roadmap-chart, mj-milestone-timeline,
    mj-burndown-chart, mj-cumulative-flow, mj-velocity-chart,
    mj-dependency-graph, mj-workflow-diagram, mj-release-calendar,
    mj-env-promotion-chart and mj-build-status-board).

    Every chart shares the data contract of ``components/pmchartsupport.js``:
    data comes from the ``data`` property, a ``src`` URL or an inline
    ``<script type="application/json">`` child, and a chart without data shows
    its empty state. mj-gantt-chart, mj-roadmap-chart, mj-milestone-timeline
    and mj-dependency-graph are wrappers over <mj-chart> types (WW-1498): their
    pages say so and show the equivalent <mj-chart> markup. The examples compute their dates relative to today in
    their script, so "today" markers, past / upcoming states and the burndown
    verdict show what they would show in a live project.
"""

import textwrap

from testcomponents.catalog.componentdoc import AttributeDoc
from testcomponents.catalog.componentdoc import ComponentDoc
from testcomponents.catalog.componentdoc import ComponentExample


def _code(text: str) -> str:
    """
        Normalise an indented code block written inside this module: strip the
        common indentation and the surrounding blank lines.

        :param text: The code as written in the source.

        :returns: The code, flush left, ending in one newline.
    """

    normalized = textwrap.dedent(text).strip("\n") + "\n"
    return normalized


# ---------------------------------------------------------------------------
# Shared pieces
# ---------------------------------------------------------------------------

#: A `YYYY-MM-DD` key for the local day `offset` days from today.
DAY_HELPER = _code(
    """
    const day = (offset) => {
      const date = new Date()
      date.setDate(date.getDate() + offset)
      return date.getFullYear() + "-" + String(date.getMonth() + 1).padStart(2, "0") + "-" + String(date.getDate()).padStart(2, "0")
    }
    """
)

#: An ISO date-time `hours` hours before now.
HOURS_AGO_HELPER = _code(
    """
    const hoursAgo = (hours) => new Date(Date.now() - hours * 3600000).toISOString()
    """
)

#: A promise that resolves after `ms` milliseconds.
PAUSE_HELPER = _code(
    """
    const pause = (ms) => new Promise((resolve) => setTimeout(resolve, ms))
    """
)

#: Clicks a shadow mark (SVG marks have no click() method).
CLICK_HELPER = _code(
    """
    const clickMark = (host, key) => {
      const mark = host.shadowRoot.querySelector(`[data-mark="${key}"]`)
      mark.dispatchEvent(new MouseEvent("click", { bubbles: true }))
      return mark
    }
    const pressKey = (target, key) => {
      target.dispatchEvent(new KeyboardEvent("keydown", { key: key, bubbles: true, composed: true }))
    }
    """
)

STACK_CSS = _code(
    """
    .stack { display: grid; gap: var(--mj-space-3); }
    .stack-caption { margin: 0; font-size: var(--mj-font-size-xs); color: var(--mj-text-muted); }
    """
)

DATA_SOURCES_HTML = (
    "<p>Data comes from, in this order: the <code>data</code> property, a "
    "<code>src</code> URL fetched as JSON, or an inline "
    "<code>&lt;script type=\"application/json\"&gt;</code> child. Until data "
    "arrives the chart shows its empty state (the <code>empty</code> slot "
    "replaces the default &ldquo;No data to display.&rdquo; message); while a "
    "<code>src</code> request is in flight it shows &ldquo;Loading&rdquo;, and "
    "a failed request or malformed inline JSON shows the error message and "
    "emits <code>mj-error</code>. Assigning <code>data</code> always wins over "
    "declared data.</p>"
)

DATES_HTML = (
    "<p>A <code>YYYY-MM-DD</code> date is a local calendar day (not UTC "
    "midnight), and a date-only end date is inclusive: a span ending "
    "<code>2026-05-28</code> covers all of 28 May.</p>"
)

MARKS_HTML = (
    "<p>The marks are buttons inside a labelled group with a single tab stop: "
    "Tab into the chart, move between marks with the arrow keys, Home and "
    "End, and activate with Enter or Space. Escape closes the detail panel and "
    "returns focus to the mark that opened it.</p>"
)

ERROR_EVENT = (
    "mj-error",
    "Declared data (`src` or inline JSON) could not be fetched or parsed, or is not an object (a JSON string or number); the error state shows the message.",
    "{ message: string }",
)

EMPTY_SLOT = (
    "empty",
    "Replaces the default empty-state message shown while the chart has no data.",
    "<span>Nothing to chart yet.</span>",
)

FALLBACK_SLOT = (
    "",
    "Fallback content shown inside the empty state until data arrives (for example a server-rendered summary); hidden once the chart draws. An inline JSON script child also lives here.",
    "<p>Server-rendered summary shown until the chart has data.</p>",
)

EMPTY_STATE_PART = ("empty-state", "The empty / loading / error block (`data-state` is empty, loading, error or ready).")

#: The `empty` slot of the four charts that wrap an <mj-chart> type.
WRAPPER_EMPTY_SLOT = (
    "empty",
    "Replaces the chart's default message (\u201cNo chart data supplied.\u201d) while the data holds nothing to draw.",
    "<span>Nothing to chart yet.</span>",
)

#: The parts every wrapper of an <mj-chart> type shares (the chart's own parts).
WRAPPER_PARTS = [
    ("toolbar", "Toolbar with the data-table button."),
    ("surface", "The drawing area of the chart."),
    ("svg", "The chart SVG."),
    ("message", "The loading / empty / error message (also carries `loading`, `empty` or `error`)."),
    ("table data-table", "The chart's data table; visually hidden until the toolbar button discloses it."),
]


def _wrapper_html(tag: str, chart_type: str) -> str:
    """
        The paragraph every wrapper page starts its description with: the tag
        is a convenience wrapper for one <mj-chart> type.

        :param tag: The wrapper tag, e.g. ``mj-gantt-chart``.
        :param chart_type: The <mj-chart> type it draws.

        :returns: An HTML paragraph.
    """

    paragraph = (
        f"<p><code>&lt;{tag}&gt;</code> is a convenience wrapper for "
        f"<code>&lt;mj-chart type=\"{chart_type}\"&gt;</code>: the chart type does the "
        "drawing, layout, keyboard support (one tab stop, arrow keys, Home and End "
        "between marks, Enter or Space to activate), the data table and the data "
        f"loading, and this tag fixes the type, accepts the data shape below, maps its "
        "attributes onto the chart type's options and adds a toolbar, a detail panel "
        f"and its own events. See the <a href=\"/chart-type/{chart_type}\">{chart_type} "
        "chart type</a> for everything the drawing does.</p>"
    )
    return paragraph


WRAPPER_DATA_HTML = (
    "<p>Data comes from, in this order: the <code>data</code> property, a "
    "<code>src</code> URL fetched as JSON, or an inline "
    "<code>&lt;script type=\"application/json\"&gt;</code> child. Assigning "
    "<code>data</code> draws at once. While a <code>src</code> request runs the chart "
    "shows Loading; a failed request, malformed inline JSON or JSON that is not an "
    "object shows the chart's error message and emits <code>mj-error</code>. Without "
    "data the chart shows its empty message (the <code>empty</code> slot replaces "
    "it).</p>"
)

WRAPPER_MARKS_HTML = (
    "<p>The marks form one tab stop: Tab into the chart, move with the arrow keys, "
    "Home and End, activate with Enter or Space. The activated mark is marked current "
    "and its details open in the detail panel; Escape or Close closes it and returns "
    "focus to the mark. The toolbar button discloses the chart's data table.</p>"
)


def _src_attribute(what: str) -> AttributeDoc:
    """
        The `src` attribute row every chart in this group shares.

        :param what: What the JSON document holds, for the description.

        :returns: The attribute documentation.
    """

    attribute = AttributeDoc(
        name="src",
        description=(
            f"URL of a JSON document with the {what}, fetched when no `data` property is set. "
            "The chart shows Loading while the request runs and the error state if it fails; "
            "changing the URL reloads."
        ),
        kind="string",
    )
    return attribute


def _data_property(shape: str) -> tuple:
    """
        The `data` property row every chart in this group shares.

        :param shape: A short reminder of the data shape.

        :returns: The (name, description) pair.
    """

    row = (
        "data",
        f"object | null. The chart data ({shape}). Assigning a new object redraws the chart, clears the selection and emits `mj-data-load`; mutating the old object does not redraw.",
    )
    return row


def _date_attribute(name: str, edge: str) -> AttributeDoc:
    """
        A `start-date` / `end-date` attribute row.

        :param name: The attribute name.
        :param edge: "left" or "right".

        :returns: The attribute documentation.
    """

    attribute = AttributeDoc(
        name=name,
        description=f"`YYYY-MM-DD` (local day) or ISO date-time that fixes the {edge} edge of the time axis; without it the axis follows the data.",
        kind="string",
    )
    return attribute


def _today_attribute(what: str) -> AttributeDoc:
    """
        The default-on `today-marker` attribute row.

        :param what: What the marker is, for the description.

        :returns: The attribute documentation.
    """

    attribute = AttributeDoc(
        name="today-marker",
        description=f"{what} Shown by default whenever today falls inside the visible range; set to `false` to hide it.",
        kind="boolean",
        default="true",
    )
    return attribute


DENSITY_VALUES = ["normal", "compact"]


# ---------------------------------------------------------------------------
# mj-branch-graph
# ---------------------------------------------------------------------------

BRANCH_GRAPH_BASIC_SCRIPT = DAY_HELPER + _code(
    """
    const graph = document.getElementById("demo-branches")

    /* Show four days past today so the upcoming code freeze is visible. */
    graph.setAttribute("end-date", day(4))

    graph.data = {
      branches: [
        { id: "main", name: "main" },
        { id: "feat-auth", name: "feat/auth" },
        { id: "hotfix", name: "hotfix/login" }
      ],
      commits: [
        { id: "c1", sha: "a1b2c3d4", branch: "main", date: day(-13), message: "Initial commit", author: "alice" },
        { id: "c2", sha: "e4f5a6b7", branch: "main", date: day(-11), message: "Add CI workflow", author: "bob" },
        { id: "c3", sha: "f7a8b9c0", branch: "feat-auth", date: day(-10), message: "Start auth feature", author: "carol" },
        { id: "c4", sha: "b3c4d5e6", branch: "hotfix", date: day(-8), message: "Fix login redirect", author: "alice" },
        { id: "c5", sha: "f6a7b8c9", branch: "main", date: day(-7), message: "Merge hotfix/login", author: "alice" },
        { id: "c6", sha: "d0e1f2a3", branch: "feat-auth", date: day(-4), message: "OAuth integration", author: "carol" },
        { id: "c7", sha: "a9b8c7d6", branch: "main", date: day(-1), message: "Merge feat/auth", author: "bob" }
      ],
      merges: [
        { from: "c4", to: "c5" },
        { from: "c6", to: "c7" }
      ],
      markers: [
        { name: "v1.2.0", date: day(-7), type: "release" },
        { name: "Code freeze", date: day(2), type: "freeze" }
      ],
      phases: [
        { name: "Sprint 14", start: day(-13), end: day(-7) },
        { name: "Sprint 15", start: day(-6), end: day(4) }
      ]
    }
    """
)

BRANCH_GRAPH_INLINE_HTML = _code(
    """
    <mj-branch-graph density="compact" readonly today-marker="false"
      start-date="2026-03-02" end-date="2026-03-20">
      <span slot="legend" class="lane-key">
        <span><i class="dot dot-1"></i>main</span>
        <span><i class="dot dot-2"></i>release/3.1</span>
      </span>
      <script type="application/json">
      {
        "branches": [
          { "id": "main", "name": "main" },
          { "id": "rel", "name": "release/3.1" }
        ],
        "commits": [
          { "id": "m1", "sha": "4d2a9f1", "branch": "main", "date": "2026-03-02", "message": "Bump dependencies", "author": "dana" },
          { "id": "r1", "sha": "77c01be", "branch": "rel", "date": "2026-03-04", "message": "Cut release/3.1", "author": "dana" },
          { "id": "r2", "sha": "a01f3c9", "branch": "rel", "date": "2026-03-09", "message": "Fix currency rounding", "author": "eli" },
          { "id": "m2", "sha": "9be4410", "branch": "main", "date": "2026-03-10", "message": "Start 3.2 work", "author": "eli" },
          { "id": "r3", "sha": "c3d8e27", "branch": "rel", "date": "2026-03-13", "message": "Release 3.1.0", "author": "dana" },
          { "id": "m3", "sha": "e81b0a4", "branch": "main", "date": "2026-03-16", "message": "Merge release/3.1", "author": "dana" }
        ],
        "merges": [ { "from": "r3", "to": "m3" } ],
        "markers": [
          { "name": "3.1.0-rc1", "date": "2026-03-09", "type": "tag" },
          { "name": "v3.1.0", "date": "2026-03-13", "type": "release" }
        ],
        "phases": [ { "name": "Stabilisation", "start": "2026-03-04", "end": "2026-03-13" } ]
      }
      </script>
    </mj-branch-graph>
    """
)

BRANCH_GRAPH_INLINE_CSS = _code(
    """
    .lane-key { display: inline-flex; gap: var(--mj-space-3); font-size: var(--mj-font-size-xs); color: var(--mj-text-muted); }
    .lane-key span { display: inline-flex; align-items: center; gap: var(--mj-space-1); }
    .dot { inline-size: 10px; block-size: 10px; border-radius: 50%; display: inline-block; }
    .dot-1 { background: var(--mj-chart-series-1, light-dark(#2563eb, #8ab4ff)); }
    .dot-2 { background: var(--mj-chart-series-2, light-dark(#15803d, #4ade80)); }
    """
)

BRANCH_GRAPH_STATES_HTML = _code(
    """
    <div class="stack">
      <mj-branch-graph id="empty-graph">
        <span slot="empty">No commits yet &mdash; push a branch to see its history.</span>
      </mj-branch-graph>
      <p class="stack-caption">Malformed inline JSON: the error state names the parser's complaint.</p>
      <mj-branch-graph id="broken-graph">
        <script type="application/json">{ "branches": [ { "id": "main" } ], "commits": [ </script>
      </mj-branch-graph>
    </div>
    """
)

BRANCH_GRAPH_STATES_SCRIPT = _code(
    """
    const stateOf = (id) => document.getElementById(id).shadowRoot.querySelector("[part=empty-state]").getAttribute("data-state")
    mjSandbox.log("empty states", { "empty-graph": stateOf("empty-graph"), "broken-graph": stateOf("broken-graph") })
    """
)

BRANCH_GRAPH_EVENTS_SCRIPT = DAY_HELPER + PAUSE_HELPER + CLICK_HELPER + _code(
    """
    const graph = document.getElementById("event-branches")
    graph.data = {
      branches: [{ id: "main", name: "main" }, { id: "docs", name: "docs/api" }],
      commits: [
        { id: "a", sha: "1a2b3c4", branch: "main", date: day(-6), message: "Add pagination", author: "alice" },
        { id: "b", sha: "5d6e7f8", branch: "docs", date: day(-4), message: "Document pagination", author: "bob" },
        { id: "c", sha: "9a8b7c6", branch: "main", date: day(-2), message: "Merge docs/api", author: "alice" }
      ],
      merges: [{ from: "b", to: "c" }],
      markers: [{ name: "v0.9.0", date: day(-2), type: "release" }]
    }

    graph.addEventListener("mj-node-select", (event) => mjSandbox.log("commit selected", { message: event.detail.node.message, branch: event.detail.branch }))
    graph.addEventListener("mj-marker-select", (event) => mjSandbox.log("marker selected", event.detail.marker.name))

    await pause(400)
    const commit = clickMark(graph, "commit:1")
    await pause(900)
    /* Escape closes the panel (mj-node-deselect) and puts focus back on the commit. */
    pressKey(graph.shadowRoot.querySelector("[part=detail-panel]"), "Escape")
    await pause(500)
    pressKey(commit, "ArrowRight")
    clickMark(graph, "marker:0")
    """
)

BRANCH_GRAPH_LIVE_SCRIPT = DAY_HELPER + _code(
    """
    const graph = document.getElementById("live-branches")
    graph.setAttribute("start-date", day(-5))
    graph.setAttribute("end-date", day(1))

    const messages = ["Tidy imports", "Add retry to client", "Fix flaky test", "Update changelog", "Raise timeout", "Refactor parser"]
    const commits = [
      { id: "h1", sha: "0f1e2d3", branch: "main", date: day(-5), message: "Start of the week", author: "alice" },
      { id: "h2", sha: "4c5b6a7", branch: "feature", date: day(-3), message: "Spike: streaming API", author: "bob" },
      { id: "h3", sha: "8f9e0d1", branch: "main", date: day(-2), message: "Hotfix release", author: "alice" }
    ]
    const merges = []
    let count = 0

    const draw = () => {
      graph.data = {
        branches: [{ id: "main", name: "main" }, { id: "feature", name: "feat/streaming" }],
        commits: commits.slice(),
        merges: merges.slice(),
        markers: [{ name: "Demo day", date: day(1), type: "release" }]
      }
    }
    draw()

    /* Every 3 seconds a push arrives: feature commits, and every fourth push merges into main. */
    setInterval(() => {
      count = count + 1
      const merge = count % 4 === 0
      const id = "live-" + count
      commits.push({ id: id, sha: Math.random().toString(16).slice(2, 9), branch: merge ? "main" : "feature", date: new Date().toISOString(), message: merge ? "Merge feat/streaming" : messages[count % messages.length], author: merge ? "alice" : "bob" })
      if (merge) {
        merges.push({ from: "live-" + (count - 1), to: id })
      }
      while (commits.length > 12) {
        commits.shift()
      }
      draw()
    }, 3000)
    """
)

BRANCH_GRAPH = ComponentDoc(
    tag="mj-branch-graph",
    title="Branch Graph",
    group="charts",
    summary="Branch network and commit history graph with lanes, merge edges, milestone markers, phase bands and a today line.",
    description=(
        "<p><code>&lt;mj-branch-graph&gt;</code> draws a Git-style branch "
        "network on a shared time axis. Each branch is a horizontal lane in "
        "the colour of its position in the series palette; commits are "
        "circles on their lane (commits on the same lane and day are spread "
        "apart); merges are curves from the source commit to the merge "
        "commit. Markers draw a full-height flag line coloured by type "
        "(<code>release</code> green, <code>freeze</code> amber, anything "
        "else blue) and phases shade a named background band. A dashed red "
        "line marks today when it is inside the range.</p>"
        "<p>Activating a commit or a marker opens a floating detail panel and "
        "emits <code>mj-node-select</code> or <code>mj-marker-select</code>; "
        "<code>readonly</code> turns the marks into plain labelled images. "
        "The toolbar button discloses a table of all commits.</p>"
        + DATA_SOURCES_HTML + DATES_HTML + MARKS_HTML
    ),
    how_to_use=(
        "<p>Give the element data with <code>branches</code> "
        "(<code>{ id, name }</code>) and <code>commits</code> "
        "(<code>{ id, sha, branch, date, message, author }</code>, where "
        "<code>branch</code> is a branch id); <code>merges</code> "
        "(<code>{ from, to }</code> commit ids), <code>markers</code> "
        "(<code>{ name, date, type }</code>) and <code>phases</code> "
        "(<code>{ name, start, end }</code>) are optional. Commits on unknown "
        "branches or outside the range are not drawn but stay in the data "
        "table.</p>"
        "<p>The axis spans the commit dates; use <code>start-date</code> / "
        "<code>end-date</code> to fix a window (markers and the today line "
        "are only drawn inside it). The <code>legend</code> slot sits at the "
        "end of the toolbar and the <code>detail-panel</code> slot adds "
        "content below the commit details.</p>"
    ),
    example="",
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>Three branches over the last two weeks, two merges, a past "
                "release and an upcoming freeze. The red dashed line is today. "
                "Click a commit to open its details.</p>"
            ),
            html='<mj-branch-graph id="demo-branches"></mj-branch-graph>\n',
            script=BRANCH_GRAPH_BASIC_SCRIPT,
        ),
        ComponentExample(
            key="inline-json",
            title="Inline JSON, compact, read-only",
            description=(
                "<p>Data declared in an inline JSON child, a fixed historical "
                "window, <code>density=\"compact\"</code>, <code>readonly</code> "
                "(marks are not interactive) and a lane key in the "
                "<code>legend</code> slot. The <code>tag</code> marker is blue.</p>"
            ),
            html=BRANCH_GRAPH_INLINE_HTML,
            css=BRANCH_GRAPH_INLINE_CSS,
        ),
        ComponentExample(
            key="states",
            title="Empty and error states",
            description=(
                "<p>A graph without data shows the <code>empty</code> slot; one "
                "whose inline JSON is malformed shows the parser error and "
                "emits <code>mj-error</code> (see Events).</p>"
            ),
            html=BRANCH_GRAPH_STATES_HTML,
            css=STACK_CSS,
            script=BRANCH_GRAPH_STATES_SCRIPT,
        ),
        ComponentExample(
            key="events",
            title="Selection events and keyboard",
            description=(
                "<p>The script opens a commit (<code>mj-node-select</code>), "
                "closes it with Escape (<code>mj-node-deselect</code>), moves "
                "focus with ArrowRight and opens the release marker "
                "(<code>mj-marker-select</code>).</p>"
            ),
            html='<mj-branch-graph id="event-branches"></mj-branch-graph>\n',
            script=BRANCH_GRAPH_EVENTS_SCRIPT,
        ),
        ComponentExample(
            key="live",
            title="Live updates",
            description=(
                "<p>A new commit is pushed every 3 seconds (every fourth one a "
                "merge into <code>main</code>); the script reassigns "
                "<code>data</code> and each draw emits <code>mj-data-load</code>. "
                "New commits land on today's line.</p>"
            ),
            html='<mj-branch-graph id="live-branches"></mj-branch-graph>\n',
            script=BRANCH_GRAPH_LIVE_SCRIPT,
        ),
    ],
    attributes=[
        _date_attribute("start-date", "left"),
        _date_attribute("end-date", "right"),
        AttributeDoc(name="density", description="`compact` draws 32px lanes instead of 48px.", kind="enum", values=DENSITY_VALUES, default="normal"),
        AttributeDoc(name="readonly", description="Commits and markers become labelled images: no tab stop, no detail panel, no select events.", kind="boolean"),
        _today_attribute("Dashed red line at the current time."),
        _src_attribute("branches, commits, merges, markers and phases"),
    ],
    events=[
        ("mj-node-select", "A commit was activated (click, Enter or Space); the detail panel opens.", "{ node: object, branch: string }"),
        ("mj-node-deselect", "The commit detail panel was closed (Close button or Escape).", "{ node: object }"),
        ("mj-marker-select", "A milestone marker was activated.", "{ marker: object }"),
        ("mj-marker-deselect", "The marker detail panel was closed.", "{ marker: object }"),
        ("mj-data-load", "Data was assigned (or loaded) and drawn.", "{ branches: number, commits: number }"),
        ERROR_EVENT,
    ],
    slots=[
        ("legend", "Content at the end of the toolbar, for example a lane key.", '<span>&#9679; main &#9679; feature</span>'),
        ("detail-panel", "Extra content below the details of the selected commit or marker.", '<p><a href="#commit-log">Open in the repository browser</a></p>'),
        EMPTY_SLOT,
        FALLBACK_SLOT,
    ],
    properties=[
        _data_property("{ branches, commits, merges, markers, phases }"),
        ("selectedNode", "object | null. Read-only. The selected commit object from the data."),
        ("selectedMarker", "object | null. Read-only. The selected marker object from the data."),
    ],
    methods=[],
    parts=[
        ("wrapper", "Outer group; its aria-label summarises branches, commits and milestones."),
        ("toolbar", "Toolbar with the data-table button and the `legend` slot."),
        ("chart-area", "Scrolling area that holds the SVG."),
        ("svg", "The chart SVG (role group)."),
        ("time-axis", "Each tick label of the time axis."),
        ("lane", "Each branch lane line."),
        ("lane-label", "Each branch name."),
        ("phase-band", "Each phase background band."),
        ("phase-label", "Each phase name."),
        ("commit-node", "Each commit circle."),
        ("merge-edge", "Each merge curve."),
        ("milestone-marker", "Each marker group (line, flag and label)."),
        ("today-marker", "The today line."),
        ("detail-panel", "The floating commit / marker detail panel."),
        ("data-table", "The disclosed table of commits."),
        EMPTY_STATE_PART,
    ],
    css_properties=[
        ("--mj-chart-series-1 … --mj-chart-series-8", "Lane and phase colours by position (defaults: an accessible light / dark palette)."),
        ("--mj-color-success / --mj-color-warning / --mj-color-info", "Theme tokens for release, freeze and other marker colours."),
        ("--mj-color-danger", "Theme token for the today line."),
    ],
)


# ---------------------------------------------------------------------------
# mj-pipeline-chart
# ---------------------------------------------------------------------------

PIPELINE_BASIC_SCRIPT = _code(
    """
    const pipeline = document.getElementById("demo-pipeline")
    pipeline.data = {
      id: "run-1842",
      stages: [
        { id: "build", name: "Build", status: "passed", duration: "1m 12s", logs: "Compiling 214 modules...\\nBuild succeeded in 72 s." },
        { id: "test", name: "Test", status: "passed", duration: "3m 45s", logs: "412 tests, 0 failures." },
        { id: "lint", name: "Lint", status: "passed", duration: "22s" },
        { id: "deploy", name: "Deploy", status: "running", duration: "41s", logs: "Rolling out to staging (2 of 4 pods)..." },
        { id: "smoke", name: "Smoke", status: "pending" }
      ],
      gates: [
        { name: "QA gate", fromStage: "test", status: "approved" },
        { name: "Release approval", fromStage: "deploy", status: "pending" }
      ],
      edges: [
        { from: "build", to: "test" },
        { from: "build", to: "lint" },
        { from: "test", to: "deploy" },
        { from: "lint", to: "deploy" },
        { from: "deploy", to: "smoke" }
      ]
    }
    """
)

PIPELINE_INLINE_HTML = _code(
    """
    <mj-pipeline-chart density="compact">
      <script type="application/json">
      {
        "id": "nightly-311",
        "stages": [
          { "id": "checkout", "name": "Checkout", "status": "passed", "duration": "8s" },
          { "id": "build", "name": "Build", "status": "passed", "duration": "2m 3s" },
          { "id": "unit", "name": "Unit tests", "status": "failed", "duration": "1m 40s", "logs": "FAIL test_invoice_totals\\nexpected 104.50, got 104.49" },
          { "id": "integration", "name": "Integration", "status": "cancelled" },
          { "id": "docs", "name": "Docs", "status": "skipped" },
          { "id": "publish", "name": "Publish artifacts to the registry", "status": "pending" }
        ],
        "gates": [
          { "name": "Security scan", "fromStage": "build", "status": "auto" },
          { "name": "QA sign-off", "fromStage": "unit", "status": "rejected" }
        ]
      }
      </script>
    </mj-pipeline-chart>
    """
)

PIPELINE_STATES_HTML = _code(
    """
    <div class="stack">
      <mj-pipeline-chart id="empty-pipeline">
        <span slot="empty">This pipeline has not run yet.</span>
      </mj-pipeline-chart>
      <p class="stack-caption"><code>src</code> pointing at a missing file: Loading, then the request error.</p>
      <mj-pipeline-chart id="missing-pipeline" src="/static/data/missing-pipeline-run.json"></mj-pipeline-chart>
    </div>
    """
)

PIPELINE_EVENTS_SCRIPT = PAUSE_HELPER + CLICK_HELPER + _code(
    """
    const pipeline = document.getElementById("event-pipeline")
    pipeline.data = {
      stages: [
        { id: "build", name: "Build", status: "passed", duration: "58s", logs: "Build succeeded." },
        { id: "deploy", name: "Deploy staging", status: "passed", duration: "1m 5s" },
        { id: "prod", name: "Deploy prod", status: "pending" }
      ],
      gates: [{ name: "Change board", fromStage: "deploy", status: "pending" }]
    }

    /* The host vetoes rejections (it would handle them server-side). */
    pipeline.addEventListener("mj-gate-approve", (event) => {
      if (event.detail.action === "reject") {
        event.preventDefault()
        mjSandbox.log("rejection cancelled by host", event.detail.gate.name)
      }
    })

    await pause(400)
    clickMark(pipeline, "stage:0")
    await pause(900)
    pressKey(pipeline.shadowRoot.querySelector("[data-mark='stage:0']"), "Escape")
    await pause(400)
    clickMark(pipeline, "gate:0")
    await pause(600)
    pipeline.shadowRoot.querySelector("[data-gate-action=reject]").click()
    await pause(600)
    pipeline.shadowRoot.querySelector("[data-gate-action=approve]").click()
    mjSandbox.log("gate after approve", pipeline.shadowRoot.querySelector("[data-mark='gate:0']").getAttribute("aria-label"))
    """
)

PIPELINE_LIVE_SCRIPT = _code(
    """
    const pipeline = document.getElementById("live-pipeline")
    const names = ["Build", "Test", "Package", "Deploy", "Verify"]
    let run = 100
    let step = 0

    /* Stage i is passed before `step`, running at `step`, pending after it. */
    const draw = () => {
      const stages = names.map((name, index) => {
        let status = "pending"
        if (index < step) {
          status = "passed"
        } else if (index === step) {
          status = "running"
        }
        return { id: name.toLowerCase(), name: name, status: status }
      })
      pipeline.data = { id: "run-" + run, stages: stages }
    }
    draw()

    setInterval(() => {
      step = step + 1
      if (step > names.length) {
        step = 0
        run = run + 1
      }
      draw()
    }, 2500)
    """
)

PIPELINE_CHART = ComponentDoc(
    tag="mj-pipeline-chart",
    title="Pipeline Chart",
    group="charts",
    summary="CI/CD pipeline stage-flow diagram with status icons, parallel stages, approval gates and a log panel.",
    description=(
        "<p><code>&lt;mj-pipeline-chart&gt;</code> draws the stages of a "
        "CI/CD run as boxes laid out by dependency level: stages that run in "
        "parallel share a column, fan-out and fan-in edges are routed between "
        "the boxes, and an edge that loops back is drawn dashed above them. "
        "Without an <code>edges</code> array the stages form a chain in data "
        "order. Each stage shows its status icon and text "
        "(<code>pending</code>, <code>running</code>, <code>passed</code>, "
        "<code>failed</code>, <code>cancelled</code>, <code>skipped</code>; "
        "anything else is shown as given with the pending icon) and a status "
        "legend sits below the chart.</p>"
        "<p>Gate diamonds sit after the stage named by "
        "<code>fromStage</code> and show their status "
        "(<code>pending</code>, <code>approved</code>, <code>rejected</code>, "
        "<code>auto</code>). Activating a stage selects it and shows its "
        "<code>logs</code> in the log panel (a stage without logs hides the "
        "panel); activating a gate opens an inline gate panel which, for a "
        "pending gate and unless <code>readonly</code>, offers Approve and "
        "Reject. A decision emits the cancelable <code>mj-gate-approve</code>; "
        "if it is not cancelled the gate shows the new status. The host's "
        "data object is never modified.</p>"
        + DATA_SOURCES_HTML + MARKS_HTML
    ),
    how_to_use=(
        "<p>Assign <code>{ id, stages, gates, edges }</code>: each stage "
        "<code>{ id, name, status, duration, logs }</code> (only "
        "<code>id</code> or <code>name</code> is needed), each gate "
        "<code>{ name, fromStage, status }</code>, each edge "
        "<code>{ from, to }</code> by stage id. <code>overallStatus</code> "
        "reports the run as a whole.</p>"
        "<p>For a running pipeline set <code>live</code> and reassign "
        "<code>data</code> as statuses change: each stage whose status "
        "differs from the previous data emits <code>mj-status-change</code> "
        "and is announced to screen readers. Escape clears the stage "
        "selection.</p>"
    ),
    example="",
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>Test and Lint run in parallel after Build; Deploy is "
                "running and a release gate waits for approval. Click Build to "
                "see its logs, or the amber gate to approve it.</p>"
            ),
            html='<mj-pipeline-chart id="demo-pipeline"></mj-pipeline-chart>\n',
            script=PIPELINE_BASIC_SCRIPT,
        ),
        ComponentExample(
            key="inline-json",
            title="Every status, no edges (inline JSON)",
            description=(
                "<p>Inline JSON with no <code>edges</code>, so the stages chain "
                "in order. Shows failed, cancelled, skipped and pending stages, "
                "<code>auto</code> and <code>rejected</code> gates, a long "
                "truncated name and <code>density=\"compact\"</code>.</p>"
            ),
            html=PIPELINE_INLINE_HTML,
        ),
        ComponentExample(
            key="states",
            title="Empty and error states",
            description=(
                "<p>No data shows the <code>empty</code> slot. A "
                "<code>src</code> that answers 404 shows Loading, then the "
                "request error, and emits <code>mj-error</code>.</p>"
            ),
            html=PIPELINE_STATES_HTML,
            css=STACK_CSS,
        ),
        ComponentExample(
            key="events",
            title="Gate decisions and events",
            description=(
                "<p>The script selects Build (<code>mj-stage-select</code>), "
                "clears it with Escape (<code>mj-stage-deselect</code>), opens "
                "the gate, tries Reject (the host cancels "
                "<code>mj-gate-approve</code>, the gate stays pending) and then "
                "Approves it.</p>"
            ),
            html='<mj-pipeline-chart id="event-pipeline"></mj-pipeline-chart>\n',
            script=PIPELINE_EVENTS_SCRIPT,
        ),
        ComponentExample(
            key="live",
            title="Live run",
            description=(
                "<p>With <code>live</code> set, the script advances the run "
                "every 2.5 seconds; each reassignment emits "
                "<code>mj-status-change</code> for the stages that changed and "
                "<code>mj-data-load</code> with the run id.</p>"
            ),
            html='<mj-pipeline-chart id="live-pipeline" live></mj-pipeline-chart>\n',
            script=PIPELINE_LIVE_SCRIPT,
        ),
    ],
    attributes=[
        AttributeDoc(name="density", description="`compact` draws smaller stage boxes (112x48 instead of 140x64).", kind="enum", values=DENSITY_VALUES, default="normal"),
        AttributeDoc(name="readonly", description="Pending gates show no Approve / Reject buttons; stages and gates can still be selected.", kind="boolean"),
        AttributeDoc(name="live", description="Reassigned data emits `mj-status-change` for every stage whose status changed and announces it.", kind="boolean"),
        _src_attribute("stages, gates and edges"),
    ],
    events=[
        ("mj-stage-select", "A stage was activated; its logs (if any) show in the log panel.", "{ stage: object }"),
        ("mj-stage-deselect", "The stage selection was cleared with Escape or by opening a gate.", "{}"),
        ("mj-gate-approve", "Cancelable. Approve or Reject was pressed on a pending gate; `preventDefault()` keeps it pending.", "{ gate: object, action: 'approve' | 'reject' }"),
        ("mj-status-change", "Live mode only: a stage's status differs from the previous data.", "{ stageId: string, previous: string, current: string }"),
        ("mj-data-load", "Data was assigned (or loaded) and drawn.", "{ stages: number, runId: string }"),
        ERROR_EVENT,
    ],
    slots=[
        ("gate-detail", "Extra content below the details of the open gate.", '<p><a href="#change-request">View the change request</a></p>'),
        EMPTY_SLOT,
        FALLBACK_SLOT,
    ],
    properties=[
        _data_property("{ id, stages, gates, edges }"),
        ("selectedStage", "object | null. Read-only. The selected stage object from the data."),
        ("overallStatus", "string. Read-only. failed if any stage failed, else running, else cancelled, else passed (all passed or skipped), skipped (all skipped) or pending."),
    ],
    methods=[],
    parts=[
        ("wrapper", "Outer group; its aria-label states the stage count and overall status."),
        ("svg", "The stage-flow SVG (role group)."),
        ("stage-node", "Each stage box (role button, aria-expanded while its logs show)."),
        ("edge", "Each edge; a return edge carries `data-return-edge`."),
        ("gate-node", "Each gate diamond."),
        ("log-panel", "The log panel of the selected stage."),
        ("gate-detail", "The inline gate panel."),
        ("gate-controls", "The Approve / Reject buttons of a pending gate."),
        ("status-legend", "The status legend below the chart."),
        ("legend-item", "Each legend entry."),
        ("a11y-list", "The disclosed ordered list of stages and gates."),
        EMPTY_STATE_PART,
    ],
    css_properties=[
        ("--mj-color-success / --mj-color-danger / --mj-color-info / --mj-color-warning", "Theme tokens for passed, failed, running and pending-gate colours."),
        ("--mj-font-mono", "Theme token for the log panel font."),
    ],
)


# ---------------------------------------------------------------------------
# mj-gantt-chart
# ---------------------------------------------------------------------------

GANTT_BASIC_SCRIPT = DAY_HELPER + _code(
    """
    const gantt = document.getElementById("demo-gantt")
    gantt.data = {
      tasks: [
        { id: "t1", name: "Requirements", start: day(-28), end: day(-19), percentComplete: 100, status: "done" },
        { id: "t2", name: "Design", start: day(-21), end: day(-10), percentComplete: 100, status: "done" },
        { id: "t3", name: "Backend development", start: day(-12), end: day(9), percentComplete: 60, status: "in progress" },
        { id: "t4", name: "Frontend development", start: day(-8), end: day(13), percentComplete: 45, status: "in progress" },
        { id: "t5", name: "QA and testing", start: day(10), end: day(20), percentComplete: 0, status: "planned" },
        { id: "t6", name: "Release", start: day(21), end: day(22), percentComplete: 0, status: "planned" }
      ],
      dependencies: [
        { from: "t1", to: "t2" },
        { from: "t2", to: "t3" },
        { from: "t2", to: "t4" },
        { from: "t3", to: "t5" },
        { from: "t4", to: "t5" },
        { from: "t5", to: "t6" }
      ],
      markers: [{ name: "Code freeze", date: day(9) }],
      phases: [
        { name: "Discovery", start: day(-28), end: day(-10) },
        { name: "Delivery", start: day(-9), end: day(22) }
      ]
    }
    """
)

GANTT_GROUPS_HTML = _code(
    """
    <mj-gantt-chart id="grouped-plan" density="compact">
      <span slot="toolbar" class="scale-switch" role="group" aria-label="Time scale">
        <button type="button" data-scale="">Auto</button>
        <button type="button" data-scale="day">Day</button>
        <button type="button" data-scale="week">Week</button>
        <button type="button" data-scale="month">Month</button>
      </span>
    </mj-gantt-chart>
    """
)

GANTT_GROUPS_CSS = _code(
    """
    .scale-switch { display: inline-flex; gap: var(--mj-space-1); }
    .scale-switch button { font: inherit; font-size: var(--mj-font-size-xs); padding: 2px var(--mj-space-2); border: 1px solid var(--mj-border-strong); border-radius: var(--mj-radius-sm); background: var(--mj-surface); color: var(--mj-text); cursor: pointer; }
    """
)

GANTT_GROUPS_SCRIPT = DAY_HELPER + _code(
    """
    const gantt = document.getElementById("grouped-plan")
    gantt.data = {
      groups: [
        { id: "api", name: "API team" },
        { id: "web", name: "Web team" }
      ],
      tasks: [
        { id: "kickoff", name: "Kick-off", start: day(-15) + "T09:00:00", end: day(-15) + "T09:00:00" },
        { id: "support", name: "Support rotation (open-ended)", start: day(-10) },
        { id: "schema", name: "Schema changes", start: day(-12), end: day(-4), percentComplete: 100, groupId: "api" },
        { id: "endpoints", name: "New endpoints", start: day(-3), end: day(8), percentComplete: 30, groupId: "api" },
        { id: "screens", name: "Checkout screens", start: day(-6), end: day(10), percentComplete: 50, groupId: "web" },
        { id: "beta", name: "Beta launch", start: day(12), milestone: true, groupId: "web" },
        { id: "contractor", name: "Hire a contractor (no dates yet)", groupId: "web" }
      ],
      dependencies: [
        { from: "schema", to: "endpoints" },
        { from: "endpoints", to: "beta" },
        { from: "screens", to: "beta" }
      ]
    }

    /* The toolbar slot drives the scale attribute. */
    for (const button of gantt.querySelectorAll("[data-scale]")) {
      button.addEventListener("click", () => {
        const scale = button.getAttribute("data-scale")
        if (scale === "") {
          gantt.removeAttribute("scale")
        } else {
          gantt.setAttribute("scale", scale)
        }
      })
    }
    """
)

GANTT_INLINE_HTML = _code(
    """
    <mj-gantt-chart scale="month" show-percent="false" show-dependencies="false"
      start-date="2026-01-01" end-date="2026-06-30">
      <script type="application/json">
      {
        "tasks": [
          { "id": "a", "name": "Vendor selection", "start": "2026-01-05", "end": "2026-02-13", "percentComplete": 100, "status": "done" },
          { "id": "b", "name": "Data migration", "start": "2026-02-16", "end": "2026-04-10", "percentComplete": 80, "status": "late" },
          { "id": "c", "name": "Training", "start": "2026-04-13", "end": "2026-05-29", "percentComplete": 20 },
          { "id": "d", "name": "Old system shutdown", "start": "2026-07-06", "end": "2026-07-10" }
        ],
        "dependencies": [ { "from": "a", "to": "b" }, { "from": "b", "to": "c" } ],
        "markers": [ { "name": "Board review", "date": "2026-03-31" } ]
      }
      </script>
    </mj-gantt-chart>
    """
)

GANTT_EQUIVALENT_HTML = _code(
    """
    <div class="stack">
      <mj-gantt-chart id="wrapper-gantt" today-marker="false">
        <script type="application/json">
        {
          "groups": [ { "id": "build", "name": "Build" } ],
          "tasks": [
            { "id": "spec", "name": "Specification", "start": "2026-03-02", "end": "2026-03-13", "percentComplete": 100 },
            { "id": "code", "name": "Implementation", "start": "2026-03-16", "end": "2026-04-10", "percentComplete": 40, "groupId": "build" },
            { "id": "test", "name": "Testing", "start": "2026-04-06", "end": "2026-04-24", "groupId": "build" }
          ],
          "dependencies": [ { "from": "spec", "to": "code" }, { "from": "code", "to": "test" } ],
          "markers": [ { "name": "Release", "date": "2026-04-17" } ]
        }
        </script>
      </mj-gantt-chart>
      <p class="stack-caption">The same plan as &lt;mj-chart type="gantt"&gt;:</p>
      <mj-chart type="gantt" today="false" row-height="40" label="Gantt chart">
        <script type="application/json">
        {
          "groups": [ { "id": "build", "label": "Build" } ],
          "tasks": [
            { "id": "spec", "label": "Specification", "start": "2026-03-02", "end": "2026-03-13", "progress": 1 },
            { "id": "code", "label": "Implementation", "start": "2026-03-16", "end": "2026-04-10", "progress": 0.4, "group": "build", "depends": ["spec"] },
            { "id": "test", "label": "Testing", "start": "2026-04-06", "end": "2026-04-24", "progress": 0, "group": "build", "depends": ["code"] }
          ],
          "markers": [ { "label": "Release", "date": "2026-04-17" } ]
        }
        </script>
      </mj-chart>
    </div>
    """
)

GANTT_STATES_HTML = _code(
    """
    <div class="stack">
      <mj-gantt-chart id="empty-gantt">
        <span slot="empty">No tasks scheduled. Add a task to start planning.</span>
      </mj-gantt-chart>
      <p class="stack-caption">Malformed inline JSON (an unquoted date):</p>
      <mj-gantt-chart id="broken-gantt">
        <script type="application/json">{ "tasks": [ { "id": "t1", "name": "Plan", "start": 2026-01-05 } ] }</script>
      </mj-gantt-chart>
      <p class="stack-caption">Valid JSON that is not an object (a string):</p>
      <mj-gantt-chart id="string-gantt">
        <script type="application/json">"tasks"</script>
      </mj-gantt-chart>
    </div>
    """
)

GANTT_EVENTS_SCRIPT = DAY_HELPER + PAUSE_HELPER + CLICK_HELPER + _code(
    """
    const gantt = document.getElementById("event-gantt")
    gantt.data = {
      groups: [{ id: "launch", name: "Launch" }],
      tasks: [
        { id: "copy", name: "Write copy", start: day(-4), end: day(2), percentComplete: 70, status: "in progress", groupId: "launch" },
        { id: "site", name: "Landing page", start: day(1), end: day(8), percentComplete: 0, status: "planned", groupId: "launch" }
      ],
      dependencies: [{ from: "copy", to: "site" }],
      markers: [{ name: "Press day", date: day(9) }]
    }
    gantt.addEventListener("mj-task-select", (event) => mjSandbox.log("task", event.detail.task.name))

    await pause(400)
    clickMark(gantt, "task:0")
    await pause(900)
    gantt.shadowRoot.querySelector("[part=task-detail] .detail-close").click()
    await pause(400)
    clickMark(gantt, "marker:0")
    await pause(700)
    /* The group header is a disclosure: collapse, then expand it again. */
    clickMark(gantt, "group:0")
    await pause(700)
    clickMark(gantt, "group:0")
    mjSandbox.log("collapsed groups", Array.from(gantt.collapsedGroups))
    """
)

GANTT_CHART = ComponentDoc(
    tag="mj-gantt-chart",
    title="Gantt Chart",
    group="charts",
    summary="Gantt chart with task bars, percent-complete fills, dependency arrows, milestones, phase bands, collapsible groups and a today line.",
    description=(
        _wrapper_html("mj-gantt-chart", "gantt") +
        "<p>Tasks are listed on the left and drawn as bars from <code>start</code> "
        "to <code>end</code> on a time axis whose ticks fall on calendar "
        "boundaries. The darker fill shows <code>percentComplete</code>; dependency "
        "arrows join the end of one bar to the start of the next; markers draw a "
        "dashed amber line with a diamond; phases shade the background; a dashed "
        "line marks today. The chart grows with its rows.</p>"
        "<p>Tasks may be grouped: <code>data.groups</code> adds a header row "
        "per group that collapses and expands its tasks "
        "(<code>mj-group-toggle</code>). A task without an end runs to the "
        "edge of the chart with a dashed outline; a task whose start and end "
        "are the same instant, or that has <code>milestone: true</code> and no "
        "end, is a diamond; a task without dates keeps its row with a "
        "&ldquo;no dates&rdquo; placeholder; a task outside the window shows "
        "an arrow at the edge it lies beyond.</p>"
        "<p>Activating a bar or a marker opens a floating detail panel "
        "(<code>mj-task-select</code>, <code>mj-marker-select</code>).</p>"
        + WRAPPER_DATA_HTML + DATES_HTML + WRAPPER_MARKS_HTML
    ),
    how_to_use=(
        "<p>Assign <code>{ tasks, groups, dependencies, markers, phases }</code>. "
        "A task is <code>{ id, name, start, end, percentComplete, status, "
        "groupId }</code> (<code>status</code> is free text shown in the "
        "details and the table); a dependency <code>{ from, to }</code> by "
        "task id; a group <code>{ id, name }</code>; a marker "
        "<code>{ name, date }</code>; a phase <code>{ name, start, end }</code>.</p>"
        "<p>The axis follows the tasks unless <code>start-date</code> / "
        "<code>end-date</code> fix it; <code>scale</code> forces day, week, "
        "month or quarter ticks (the step still grows when there is no room). "
        "The <code>toolbar</code> slot adds controls next to the table button "
        "and the <code>task-detail</code> slot adds content to the detail "
        "panel.</p>"
    ),
    example="",
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>A six-week plan around today: finished, running and planned "
                "tasks with dependencies, a code freeze marker, two phases and "
                "the today line. Click a bar for its details.</p>"
            ),
            html='<mj-gantt-chart id="demo-gantt"></mj-gantt-chart>\n',
            script=GANTT_BASIC_SCRIPT,
        ),
        ComponentExample(
            key="groups",
            title="Groups, milestones and the toolbar slot",
            description=(
                "<p>Two collapsible groups, a zero-duration kick-off, a "
                "<code>milestone</code> task, an open-ended task and a task "
                "without dates. The buttons in the <code>toolbar</code> slot set "
                "<code>scale</code>.</p>"
            ),
            html=GANTT_GROUPS_HTML,
            css=GANTT_GROUPS_CSS,
            script=GANTT_GROUPS_SCRIPT,
        ),
        ComponentExample(
            key="inline-json",
            title="Inline JSON with a fixed window",
            description=(
                "<p>Inline JSON, <code>scale=\"month\"</code>, a fixed "
                "January&ndash;June window, <code>show-percent=\"false\"</code> "
                "and <code>show-dependencies=\"false\"</code>. The July task "
                "lies outside the window and shows an edge arrow.</p>"
            ),
            html=GANTT_INLINE_HTML,
        ),
        ComponentExample(
            key="states",
            title="Empty and error states",
            description=(
                "<p>No data shows the <code>empty</code> slot; inline JSON with "
                "an unquoted date shows the parser error, and JSON that is not "
                "an object (<code>\"tasks\"</code>) shows a data error; both emit "
                "<code>mj-error</code>.</p>"
            ),
            html=GANTT_STATES_HTML,
            css=STACK_CSS,
        ),
        ComponentExample(
            key="events",
            title="Selection and group events",
            description=(
                "<p>The script opens a task (<code>mj-task-select</code>), "
                "closes it (<code>mj-task-deselect</code>), opens the marker "
                "(<code>mj-marker-select</code>) and collapses and expands the "
                "group (<code>mj-group-toggle</code>).</p>"
            ),
            html='<mj-gantt-chart id="event-gantt"></mj-gantt-chart>\n',
            script=GANTT_EVENTS_SCRIPT,
        ),
        ComponentExample(
            key="mj-chart",
            title="The same chart as <mj-chart>",
            description=(
                "<p>The wrapper above and <code>&lt;mj-chart type=\"gantt\"&gt;</code> "
                "below draw the same plan: the chart type reads <code>label</code>, "
                "<code>progress</code> (0&ndash;1), <code>group</code> and "
                "<code>depends</code> where the wrapper reads <code>name</code>, "
                "<code>percentComplete</code>, <code>groupId</code> and "
                "<code>dependencies</code>, and its option <code>show-progress</code> is "
                "the wrapper's <code>show-percent</code>, <code>today</code> its "
                "<code>today-marker</code>.</p>"
            ),
            html=GANTT_EQUIVALENT_HTML,
            css=STACK_CSS,
        ),
    ],
    attributes=[
        AttributeDoc(name="scale", description="Forces the tick granularity; without it the ticks are chosen to fit.", kind="enum", values=["day", "week", "month", "quarter"]),
        _date_attribute("start-date", "left"),
        _date_attribute("end-date", "right"),
        _today_attribute("Dashed line at the current time, labelled Today."),
        AttributeDoc(name="show-dependencies", description="Set to `false` to hide the dependency arrows.", kind="boolean", default="true"),
        AttributeDoc(name="show-percent", description="Set to `false` to hide the percent-complete fill.", kind="boolean", default="true"),
        AttributeDoc(name="density", description="`compact` draws 28px rows instead of 40px.", kind="enum", values=DENSITY_VALUES, default="normal"),
        _src_attribute("tasks, groups, dependencies, markers and phases"),
        AttributeDoc(name="collapsed-groups", description="JSON array of the collapsed group ids; activating a group header updates it, and assigning new data removes it.", kind="json"),
    ],
    events=[
        ("mj-task-select", "A task bar was activated; the detail panel opens.", "{ task: object }"),
        ("mj-task-deselect", "The detail panel of a task was closed.", "{}"),
        ("mj-marker-select", "A milestone marker was activated.", "{ marker: object }"),
        ("mj-group-toggle", "A group header was activated.", "{ groupId: string, collapsed: boolean }"),
        ("mj-data-load", "Data was assigned (or loaded) and drawn.", "{ tasks: number, groups: number }"),
        ERROR_EVENT,
    ],
    slots=[
        ("toolbar", "Controls placed in the toolbar after the data-table button.", '<button type="button">Export</button>'),
        ("task-detail", "Extra content below the details of the selected task or marker.", '<p><a href="#task">Open the task</a></p>'),
        WRAPPER_EMPTY_SLOT,
    ],
    properties=[
        _data_property("{ tasks, groups, dependencies, markers, phases }"),
        ("selectedTask", "object | null. Read-only. The selected task object from the data."),
        ("collapsedGroups", "Set<string>. Read-only. Ids of the collapsed groups; cleared when new data is assigned."),
    ],
    methods=[],
    parts=WRAPPER_PARTS + [
        ("time-axis", "Each tick label."),
        ("task-label task-list-panel", "Each task name in the label column."),
        ("bar task-bar", "Each task mark (bar, diamond, edge arrow or no-dates placeholder)."),
        ("bar-fill task-bar-fill", "The percent-complete fill."),
        ("group-row", "Each group header row (role button with aria-expanded)."),
        ("dependency dependency-arrow", "Each dependency arrow."),
        ("milestone-marker", "Each marker (line, diamond and name)."),
        ("phase-band", "Each phase band."),
        ("today-marker", "The today line."),
        ("today-label", "The Today label."),
        ("task-detail", "The floating detail panel."),
    ],
    css_properties=[
        ("--mj-chart-series-1 … --mj-chart-series-8", "Bar colours (one per group, the first without groups) and phase band colours by position."),
        ("--mj-color-warning", "Theme token for the milestone markers."),
        ("--mj-accent", "Theme token for the today line."),
        ("--mj-chart-min-height", "Smallest height of the chart (it grows with its rows)."),
    ],
)


# ---------------------------------------------------------------------------
# mj-roadmap-chart
# ---------------------------------------------------------------------------

ROADMAP_BASIC_SCRIPT = DAY_HELPER + _code(
    """
    const roadmap = document.getElementById("demo-roadmap")
    roadmap.data = {
      swimlanes: [
        { id: "platform", name: "Platform" },
        { id: "mobile", name: "Mobile" },
        { id: "data", name: "Data" }
      ],
      initiatives: [
        { id: "i1", name: "API gateway v2", swimlaneId: "platform", startDate: day(-150), endDate: day(-40), status: "done", percentComplete: 100 },
        { id: "i2", name: "Single sign-on", swimlaneId: "platform", startDate: day(-30), endDate: day(75), status: "in-progress", percentComplete: 40 },
        { id: "i3", name: "iOS redesign", swimlaneId: "mobile", startDate: day(-60), endDate: day(40), status: "at-risk", percentComplete: 55, description: "Waiting on design system tokens." },
        { id: "i4", name: "Android widgets", swimlaneId: "mobile", startDate: day(60), endDate: day(170), status: "planned" },
        { id: "i5", name: "Data lake v3", swimlaneId: "data", startDate: day(-120), endDate: day(10), status: "blocked", percentComplete: 70 },
        { id: "i6", name: "Real-time streams", swimlaneId: "data", startDate: day(30), endDate: day(200), status: "planned" }
      ],
      markers: [{ name: "GA launch", date: day(80) }]
    }
    """
)

ROADMAP_BUCKET_HTML = _code(
    """
    <mj-roadmap-chart mode="bucket">
      <span slot="legend" class="status-key">
        <span>&#9675; planned</span><span>&#9678; in progress</span><span>&#10003; done</span><span>&#9888; at risk</span><span>&#8856; blocked</span>
      </span>
      <script type="application/json">
      {
        "swimlanes": [
          { "id": "growth", "name": "Growth" },
          { "id": "core", "name": "Core product" }
        ],
        "buckets": [
          { "id": "now", "name": "Now" },
          { "id": "next", "name": "Next" },
          { "id": "later", "name": "Later" }
        ],
        "initiatives": [
          { "name": "Referral programme", "swimlane": "growth", "bucket": "now", "status": "in-progress" },
          { "name": "Pricing page test", "swimlane": "growth", "bucket": "now", "status": "done" },
          { "name": "Partner portal", "swimlane": "growth", "bucket": "later", "status": "planned" },
          { "name": "Offline mode", "swimlane": "core", "bucket": "next", "status": "blocked" },
          { "name": "Search rewrite", "swimlane": "core", "bucket": "now", "status": "at-risk" },
          { "name": "Accessibility audit", "swimlane": "compliance", "bucket": "next", "status": "planned" },
          { "name": "Moonshot idea", "swimlane": "core", "bucket": "someday", "status": "planned" }
        ]
      }
      </script>
    </mj-roadmap-chart>
    """
)

ROADMAP_BUCKET_CSS = _code(
    """
    .status-key { display: inline-flex; flex-wrap: wrap; gap: var(--mj-space-3); font-size: var(--mj-font-size-xs); color: var(--mj-text-muted); }
    """
)

ROADMAP_SCALE_SCRIPT = DAY_HELPER + _code(
    """
    const roadmap = document.getElementById("monthly-roadmap")
    roadmap.setAttribute("start-date", day(-45))
    roadmap.setAttribute("end-date", day(135))
    roadmap.data = {
      swimlanes: [{ id: "web", name: "Web" }, { id: "ops", name: "Operations" }],
      initiatives: [
        { name: "Checkout revamp", swimlane: "web", start: day(-40), end: day(25), status: "in-progress", percentComplete: 65 },
        { name: "Dark mode", swimlane: "web", start: day(10), end: day(70), status: "planned" },
        { name: "Edge caching", swimlane: "web", start: day(-20), end: day(50), status: "at-risk" },
        { name: "Kubernetes upgrade", swimlane: "ops", start: day(-30), end: day(-5), status: "done", percentComplete: 100 },
        { name: "Cost dashboard", swimlane: "ops", start: day(40), end: day(120), status: "planned" }
      ],
      markers: [{ name: "Holiday freeze", date: day(45) }],
      phases: [{ name: "Annual planning", start: day(60), end: day(95) }]
    }
    """
)

ROADMAP_EQUIVALENT_HTML = _code(
    """
    <div class="stack">
      <mj-roadmap-chart mode="bucket">
        <script type="application/json">
        {
          "swimlanes": [ { "id": "web", "name": "Web" }, { "id": "app", "name": "App" } ],
          "buckets": [ { "id": "now", "name": "Now" }, { "id": "next", "name": "Next" }, { "id": "later", "name": "Later" } ],
          "initiatives": [
            { "name": "Checkout", "swimlaneId": "web", "columnId": "now", "status": "in-progress" },
            { "name": "Search", "swimlaneId": "web", "columnId": "next", "status": "planned" },
            { "name": "Offline mode", "swimlaneId": "app", "columnId": "later", "status": "at-risk" }
          ]
        }
        </script>
      </mj-roadmap-chart>
      <p class="stack-caption">The same roadmap as &lt;mj-chart type="roadmap"&gt;:</p>
      <mj-chart type="roadmap" mode="bucket" label="Roadmap chart">
        <script type="application/json">
        {
          "groups": [ { "id": "web", "label": "Web" }, { "id": "app", "label": "App" } ],
          "buckets": [ { "id": "now", "label": "Now" }, { "id": "next", "label": "Next" }, { "id": "later", "label": "Later" } ],
          "tasks": [
            { "label": "Checkout", "group": "web", "bucket": "now", "status": "in-progress" },
            { "label": "Search", "group": "web", "bucket": "next", "status": "planned" },
            { "label": "Offline mode", "group": "app", "bucket": "later", "status": "at-risk" }
          ]
        }
        </script>
      </mj-chart>
    </div>
    """
)

ROADMAP_STATES_HTML = _code(
    """
    <div class="stack">
      <mj-roadmap-chart id="empty-roadmap">
        <span slot="empty">The roadmap is empty. Add a swimlane and an initiative.</span>
      </mj-roadmap-chart>
      <p class="stack-caption">Malformed inline JSON:</p>
      <mj-roadmap-chart id="broken-roadmap">
        <script type="application/json">{ swimlanes: [] }</script>
      </mj-roadmap-chart>
    </div>
    """
)

ROADMAP_EVENTS_SCRIPT = DAY_HELPER + PAUSE_HELPER + CLICK_HELPER + _code(
    """
    const roadmap = document.getElementById("event-roadmap")
    roadmap.data = {
      swimlanes: [{ id: "app", name: "App" }],
      initiatives: [
        { name: "Onboarding flow", swimlaneId: "app", startDate: day(-20), endDate: day(40), status: "in-progress", percentComplete: 35, description: "New sign-up wizard with progress saving." },
        { name: "Notifications", swimlaneId: "app", startDate: day(50), endDate: day(110), status: "planned" }
      ]
    }
    roadmap.addEventListener("mj-initiative-select", (event) => mjSandbox.log("initiative", event.detail.initiative.name))

    await pause(400)
    const bar = clickMark(roadmap, "task:0")
    await pause(900)
    pressKey(roadmap.shadowRoot.querySelector("[part=initiative-detail]"), "Escape")
    await pause(400)
    pressKey(bar, "ArrowRight")
    clickMark(roadmap, "task:1")
    mjSandbox.log("selectedInitiative", roadmap.selectedInitiative.name)
    """
)

ROADMAP_CHART = ComponentDoc(
    tag="mj-roadmap-chart",
    title="Roadmap Chart",
    group="charts",
    summary="Initiative roadmap with swimlane rows and calendar-period or named-bucket columns, stacked overlapping bars and a today line.",
    description=(
        _wrapper_html("mj-roadmap-chart", "roadmap") +
        "<p>It draws a strategic roadmap: "
        "rows are swimlanes (teams, products or themes), columns are calendar "
        "periods or named buckets, and each initiative is a bar with a status "
        "icon and colour (<code>planned</code>, <code>in-progress</code>, "
        "<code>done</code>, <code>at-risk</code>, <code>blocked</code>). Bars "
        "that overlap in one swimlane are stacked in sub-rows rather than "
        "drawn on top of each other.</p>"
        "<p>In the default <code>mode=\"calendar\"</code> the columns are "
        "quarters, months or half-years aligned to period starts and each "
        "initiative spans its <code>startDate</code>&ndash;<code>endDate</code> "
        "(fractions of a period included). Calendar mode also draws "
        "<code>markers</code> (amber milestone lines), <code>phases</code> "
        "(background bands) and the today line. In <code>mode=\"bucket\"</code> "
        "the columns are <code>data.buckets</code> and each initiative goes in "
        "the bucket named by <code>columnId</code>.</p>"
        "<p>Initiatives whose swimlane is unknown go to an "
        "&ldquo;Unassigned&rdquo; lane; initiatives that cannot be placed "
        "(no dates, unknown bucket, outside the range) are counted in a note "
        "below the chart and listed in the data table as &ldquo;not "
        "placed&rdquo;. Activating a bar opens an inline detail panel and "
        "emits <code>mj-initiative-select</code>. The roadmap fits the chart's "
        "width (columns share it) and grows with its lanes.</p>"
        + WRAPPER_DATA_HTML + DATES_HTML + WRAPPER_MARKS_HTML
    ),
    how_to_use=(
        "<p>Assign <code>{ swimlanes, initiatives, buckets, markers, phases }</code>. "
        "A swimlane is <code>{ id, name }</code>; an initiative "
        "<code>{ id, name, swimlaneId, status, percentComplete, description }</code> "
        "plus either <code>startDate</code> / <code>endDate</code> (calendar) "
        "or <code>columnId</code> (bucket). The aliases <code>swimlane</code>, "
        "<code>start</code>, <code>end</code>, <code>bucket</code> and "
        "<code>column</code> are accepted too.</p>"
        "<p>Calendar columns cover the initiative dates unless "
        "<code>start-date</code> / <code>end-date</code> fix the range; "
        "<code>scale</code> picks quarter (default), month or half-year "
        "columns. Bucket mode without any buckets falls back to calendar "
        "mode.</p>"
    ),
    example="",
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>Calendar mode (the default): quarters around today, six "
                "initiatives in three swimlanes, a launch marker and the today "
                "line. The columns share the chart's width. Click a bar for its "
                "details.</p>"
            ),
            html='<mj-roadmap-chart id="demo-roadmap"></mj-roadmap-chart>\n',
            script=ROADMAP_BASIC_SCRIPT,
        ),
        ComponentExample(
            key="bucket",
            title="Bucket mode from inline JSON",
            description=(
                "<p><code>mode=\"bucket\"</code> with Now / Next / Later columns: "
                "two initiatives share a cell and stack, one names an unknown "
                "swimlane (Unassigned lane), one an unknown bucket (see the note "
                "below the chart). A status key fills the <code>legend</code> "
                "slot.</p>"
            ),
            html=ROADMAP_BUCKET_HTML,
            css=ROADMAP_BUCKET_CSS,
        ),
        ComponentExample(
            key="monthly",
            title="Monthly scale, fixed window, compact",
            description=(
                "<p><code>scale=\"month\"</code> and "
                "<code>density=\"compact\"</code> with a six-month window set by "
                "the script, a marker and a planning phase; the field aliases "
                "<code>swimlane</code>, <code>start</code> and <code>end</code> "
                "are used.</p>"
            ),
            html='<mj-roadmap-chart id="monthly-roadmap" scale="month" density="compact"></mj-roadmap-chart>\n',
            script=ROADMAP_SCALE_SCRIPT,
        ),
        ComponentExample(
            key="states",
            title="Empty and error states",
            description=(
                "<p>No data shows the <code>empty</code> slot; inline JSON with "
                "unquoted keys shows the parser error and emits "
                "<code>mj-error</code>.</p>"
            ),
            html=ROADMAP_STATES_HTML,
            css=STACK_CSS,
        ),
        ComponentExample(
            key="events",
            title="Selection events",
            description=(
                "<p>The script opens an initiative "
                "(<code>mj-initiative-select</code>), closes it with Escape "
                "(<code>mj-initiative-deselect</code>) and selects the next one "
                "with the keyboard.</p>"
            ),
            html='<mj-roadmap-chart id="event-roadmap"></mj-roadmap-chart>\n',
            script=ROADMAP_EVENTS_SCRIPT,
        ),
        ComponentExample(
            key="mj-chart",
            title="The same chart as <mj-chart>",
            description=(
                "<p>The wrapper and <code>&lt;mj-chart type=\"roadmap\"&gt;</code> draw "
                "the same roadmap: the chart type reads <code>tasks</code> with "
                "<code>label</code>, <code>start</code> / <code>end</code>, "
                "<code>group</code> and <code>bucket</code>, and <code>groups</code> / "
                "<code>buckets</code> as <code>{ id, label }</code>, where the wrapper "
                "reads <code>initiatives</code>, <code>swimlanes</code> and "
                "<code>buckets</code> with <code>name</code>.</p>"
            ),
            html=ROADMAP_EQUIVALENT_HTML,
            css=STACK_CSS,
        ),
    ],
    attributes=[
        AttributeDoc(name="mode", description="`calendar` places initiatives by their dates; `bucket` places them in `data.buckets` columns by `columnId`.", kind="enum", values=["calendar", "bucket"], default="calendar"),
        AttributeDoc(name="scale", description="Calendar column period.", kind="enum", values=["quarter", "month", "half-year"], default="quarter"),
        _date_attribute("start-date", "left"),
        _date_attribute("end-date", "right"),
        _today_attribute("Calendar mode only: dashed line at the current time, labelled Today."),
        AttributeDoc(name="density", description="`compact` draws 24px bars instead of 32px.", kind="enum", values=DENSITY_VALUES, default="normal"),
        _src_attribute("swimlanes, initiatives, buckets, markers and phases"),
    ],
    events=[
        ("mj-initiative-select", "An initiative bar was activated; the detail panel opens.", "{ initiative: object }"),
        ("mj-initiative-deselect", "The detail panel was closed (Close button or Escape).", "{}"),
        ("mj-data-load", "Data was assigned (or loaded) and drawn.", "{ initiatives: number, swimlanes: number }"),
        ERROR_EVENT,
    ],
    slots=[
        ("legend", "Content in the toolbar after the data-table button, for example a status key.", '<span>&#9675; planned &#9678; in progress &#10003; done</span>'),
        ("initiative-detail", "Extra content below the details of the selected initiative.", '<p><a href="#initiative">Open the initiative brief</a></p>'),
        WRAPPER_EMPTY_SLOT,
    ],
    properties=[
        _data_property("{ swimlanes, initiatives, buckets, markers, phases }"),
        ("selectedInitiative", "object | null. Read-only. The selected initiative object from the data."),
    ],
    methods=[],
    parts=WRAPPER_PARTS + [
        ("column-header", "Each column heading."),
        ("swimlane-label", "Each swimlane name."),
        ("bar initiative-bar", "Each initiative bar."),
        ("initiative-label", "The name inside a bar."),
        ("milestone-marker", "Each marker (calendar mode)."),
        ("phase-band", "Each phase band (calendar mode)."),
        ("phase-label", "Each phase name, in its own row under the swimlanes (calendar mode)."),
        ("today-marker", "The today line (calendar mode)."),
        ("today-label", "The Today label, in a row of its own below the phase names (calendar mode)."),
        ("unplaced-note", "Note that counts initiatives that could not be placed."),
        ("initiative-detail", "The inline detail panel."),
    ],
    css_properties=[
        ("--mj-accent / --mj-color-success / --mj-color-warning / --mj-color-danger", "Theme tokens for in-progress, done, at-risk and blocked bars (planned uses --mj-text-muted)."),
        ("--mj-chart-series-1 … --mj-chart-series-8", "Phase band colours by position."),
    ],
)


# ---------------------------------------------------------------------------
# mj-milestone-timeline
# ---------------------------------------------------------------------------

MILESTONE_BASIC_SCRIPT = DAY_HELPER + _code(
    """
    const timeline = document.getElementById("demo-timeline")
    timeline.data = {
      markers: [
        { name: "v2.0 branch cut", date: day(-20), type: "freeze", description: "No new features after this date." },
        { name: "RC1", date: day(-9), type: "tag", description: "First release candidate." },
        { name: "v2.0 GA", date: day(0), type: "release", description: "General availability release." },
        { name: "Sprint 15 start", date: day(6), type: "milestone" },
        { name: "v2.1 planning", date: day(20), type: "milestone" },
        { name: "v2.1 GA", date: day(34), type: "release" }
      ],
      phases: [
        { name: "Stabilisation", start: day(-20), end: day(0) },
        { name: "Sprint 15", start: day(6), end: day(19) }
      ]
    }
    """
)

MILESTONE_INLINE_HTML = _code(
    """
    <mj-milestone-timeline density="compact" today-marker="false"
      start-date="2026-01-01" end-date="2026-03-31">
      <script type="application/json">
      {
        "markers": [
          { "name": "Kick-off", "date": "2026-01-12" },
          { "name": "Alpha", "date": "2026-02-02", "type": "tag" },
          { "name": "Feature freeze", "date": "2026-02-27", "type": "freeze" },
          { "name": "1.0 launch", "date": "2026-03-23", "type": "release" }
        ],
        "phases": [ { "name": "Build", "start": "2026-01-12", "end": "2026-02-27" } ]
      }
      </script>
    </mj-milestone-timeline>
    """
)

MILESTONE_CROWDED_SCRIPT = DAY_HELPER + _code(
    """
    const timeline = document.getElementById("crowded-timeline")
    timeline.data = {
      markers: [
        { name: "Security review sign-off for the payments service", date: day(-3), type: "milestone" },
        { name: "Docs freeze", date: day(-3), type: "freeze" },
        { name: "Translations due", date: day(-2), type: "milestone" },
        { name: "RC2", date: day(-1), type: "tag" },
        { name: "Go / no-go meeting", date: day(0), type: "milestone" },
        { name: "v4.0", date: day(1), type: "release" },
        { name: "Marketing launch", date: day(1), type: "milestone" },
        { name: "Retro", date: day(2) }
      ]
    }
    """
)

MILESTONE_EQUIVALENT_HTML = _code(
    """
    <div class="stack">
      <mj-milestone-timeline start-date="2026-01-01" end-date="2026-03-31">
        <script type="application/json">
        {
          "markers": [
            { "name": "Alpha", "date": "2026-01-20", "type": "tag" },
            { "name": "Feature freeze", "date": "2026-02-20", "type": "freeze" },
            { "name": "1.0", "date": "2026-03-16", "type": "release" }
          ],
          "phases": [ { "name": "Hardening", "start": "2026-02-20", "end": "2026-03-16" } ]
        }
        </script>
      </mj-milestone-timeline>
      <p class="stack-caption">The same markers as &lt;mj-chart type="milestone"&gt;:</p>
      <mj-chart type="milestone" dim-past start-date="2026-01-01" end-date="2026-03-31" label="Milestone timeline" style="height:200px">
        <script type="application/json">
        {
          "events": [
            { "label": "Alpha", "date": "2026-01-20", "kind": "tag" },
            { "label": "Feature freeze", "date": "2026-02-20", "kind": "freeze" },
            { "label": "1.0", "date": "2026-03-16", "kind": "release" }
          ],
          "phases": [ { "label": "Hardening", "start": "2026-02-20", "end": "2026-03-16" } ]
        }
        </script>
      </mj-chart>
    </div>
    """
)

MILESTONE_STATES_HTML = _code(
    """
    <div class="stack">
      <mj-milestone-timeline id="empty-timeline">
        <span slot="empty">No milestones planned.</span>
      </mj-milestone-timeline>
      <p class="stack-caption">Malformed inline JSON:</p>
      <mj-milestone-timeline id="broken-timeline">
        <script type="application/json">{ "markers": [ { "name": "Launch", } ] }</script>
      </mj-milestone-timeline>
    </div>
    """
)

MILESTONE_EVENTS_HTML = _code(
    """
    <mj-milestone-timeline id="event-timeline">
      <p slot="marker-detail" class="detail-note"><a href="#release-notes">Read the release notes</a></p>
    </mj-milestone-timeline>
    """
)

MILESTONE_EVENTS_SCRIPT = DAY_HELPER + PAUSE_HELPER + CLICK_HELPER + _code(
    """
    const timeline = document.getElementById("event-timeline")
    timeline.data = {
      markers: [
        { name: "Beta", date: day(-5), type: "tag", description: "Opened to 500 beta testers." },
        { name: "Launch", date: day(3), type: "release", description: "Public launch with the press release." }
      ]
    }
    timeline.addEventListener("mj-marker-select", (event) => mjSandbox.log("marker", event.detail.marker.name))

    await pause(400)
    const beta = clickMark(timeline, "event:0")
    await pause(900)
    timeline.shadowRoot.querySelector("[part=detail-popover] .detail-close").click()
    await pause(400)
    pressKey(beta, "End")
    clickMark(timeline, "event:1")
    """
)

MILESTONE_TIMELINE = ComponentDoc(
    tag="mj-milestone-timeline",
    title="Milestone Timeline",
    group="charts",
    summary="Single horizontal time axis of named milestones with past, today and upcoming states, phase bands and a today line.",
    description=(
        _wrapper_html("mj-milestone-timeline", "milestone") +
        "<p>It is the lightest "
        "timeline in the library: one horizontal axis with named markers on "
        "it. The shape and colour follow the <code>type</code>: "
        "<code>release</code> is a green diamond, <code>freeze</code> an amber "
        "triangle, <code>tag</code> a blue circle and <code>milestone</code> "
        "(the default) an accent circle. A marker more than a day before now "
        "is <em>past</em> and drawn faded; within a day of now it is "
        "<em>today</em>; later it is <em>upcoming</em>. The state is part of "
        "each marker's accessible name.</p>"
        "<p>Labels are placed in tiers above and below the axis so neighbours "
        "do not collide; a marker with no room keeps its shape and its name stays "
        "in the tooltip and the data table. Markers on the same date are nudged "
        "apart. Phases shade a band behind the axis. "
        "Activating a marker opens an inline detail panel with its type, date "
        "and <code>description</code>.</p>"
        + WRAPPER_DATA_HTML + DATES_HTML + WRAPPER_MARKS_HTML
    ),
    how_to_use=(
        "<p>Assign <code>{ markers, phases }</code>: each marker "
        "<code>{ name, date, type, description }</code>, each phase "
        "<code>{ name, start, end }</code>. The axis spans the marker dates "
        "plus a small margin unless <code>start-date</code> / "
        "<code>end-date</code> fix it; markers outside the window and markers "
        "with an invalid date are listed in the data table but not drawn.</p>"
        "<p>The <code>marker-detail</code> slot adds content (a link, an "
        "action) to the detail panel of every marker.</p>"
    ),
    example="",
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>A release train around today: the freeze and RC are past "
                "(faded), GA is today and the next milestones are "
                "upcoming. Click a marker for its description.</p>"
            ),
            html='<mj-milestone-timeline id="demo-timeline"></mj-milestone-timeline>\n',
            script=MILESTONE_BASIC_SCRIPT,
        ),
        ComponentExample(
            key="inline-json",
            title="Inline JSON, fixed window, compact",
            description=(
                "<p>Inline JSON for a past quarter with a fixed window, "
                "<code>density=\"compact\"</code> (shorter labels, tighter rows) "
                "and <code>today-marker=\"false\"</code>. Every marker is past.</p>"
            ),
            html=MILESTONE_INLINE_HTML,
        ),
        ComponentExample(
            key="crowded",
            title="Crowded dates and long names",
            description=(
                "<p>Eight markers within six days, two pairs on the same date "
                "and a very long name: labels take alternating rows, coincident "
                "markers are nudged apart and the long name is truncated.</p>"
            ),
            html='<mj-milestone-timeline id="crowded-timeline"></mj-milestone-timeline>\n',
            script=MILESTONE_CROWDED_SCRIPT,
        ),
        ComponentExample(
            key="states",
            title="Empty and error states",
            description=(
                "<p>No data shows the <code>empty</code> slot; inline JSON with "
                "a trailing comma shows the parser error and emits "
                "<code>mj-error</code>.</p>"
            ),
            html=MILESTONE_STATES_HTML,
            css=STACK_CSS,
        ),
        ComponentExample(
            key="events",
            title="Selection events and the detail slot",
            description=(
                "<p>The <code>marker-detail</code> slot adds a link to every "
                "panel. The script opens Beta (<code>mj-marker-select</code>), "
                "closes it (<code>mj-marker-deselect</code>), presses End and "
                "opens Launch.</p>"
            ),
            html=MILESTONE_EVENTS_HTML,
            script=MILESTONE_EVENTS_SCRIPT,
        ),
        ComponentExample(
            key="mj-chart",
            title="The same chart as <mj-chart>",
            description=(
                "<p>The wrapper and <code>&lt;mj-chart type=\"milestone\"&gt;</code> draw "
                "the same markers: the chart type reads <code>events</code> with "
                "<code>label</code> and <code>kind</code> where the wrapper reads "
                "<code>markers</code> with <code>name</code> and <code>type</code>, and "
                "the wrapper switches the chart type's <code>dim-past</code> option on.</p>"
            ),
            html=MILESTONE_EQUIVALENT_HTML,
            css=STACK_CSS,
        ),
    ],
    attributes=[
        _date_attribute("start-date", "left"),
        _date_attribute("end-date", "right"),
        AttributeDoc(name="density", description="`compact` uses shorter labels (12 characters) and tighter label rows.", kind="enum", values=DENSITY_VALUES, default="normal"),
        _today_attribute("Dashed line labelled Today."),
        _src_attribute("markers and phases"),
    ],
    events=[
        ("mj-marker-select", "A marker was activated; the detail panel opens.", "{ marker: object }"),
        ("mj-marker-deselect", "The detail panel was closed (Close button or Escape).", "{}"),
        ("mj-data-load", "Data was assigned (or loaded) and drawn.", "{ markers: number, phases: number }"),
        ERROR_EVENT,
    ],
    slots=[
        ("marker-detail", "Extra content below the details of the selected marker.", '<p><a href="#release-notes">Release notes</a></p>'),
        WRAPPER_EMPTY_SLOT,
    ],
    properties=[
        _data_property("{ markers, phases }"),
        ("selectedMarker", "object | null. Read-only. The selected marker object from the data."),
    ],
    methods=[],
    parts=WRAPPER_PARTS + [
        ("time-axis", "The axis line and each tick label."),
        ("marker", "Each marker; past markers have reduced opacity."),
        ("marker-label", "Each visible marker label."),
        ("phase-band", "Each phase band."),
        ("today-marker", "The today line."),
        ("today-label", "The Today label."),
        ("detail-popover", "The inline detail panel."),
    ],
    css_properties=[
        ("--mj-color-success / --mj-color-warning / --mj-color-info / --mj-accent", "Theme tokens for release, freeze, tag and milestone markers."),
        ("--mj-chart-series-1 … --mj-chart-series-8", "Phase band colours by position."),
        ("--mj-chart-min-height", "Height of the chart when the page gives it none (default 200px)."),
    ],
)


# ---------------------------------------------------------------------------
# mj-burndown-chart
# ---------------------------------------------------------------------------

BURNDOWN_BASIC_SCRIPT = DAY_HELPER + _code(
    """
    const chart = document.getElementById("demo-burndown")

    /* A two-week sprint that started a week ago; the team is behind the ideal line. */
    chart.data = {
      startDate: day(-7),
      endDate: day(6),
      totalScope: 80,
      dailyValues: [
        { date: day(-7), value: 80 },
        { date: day(-6), value: 76 },
        { date: day(-5), value: 73 },
        { date: day(-4), value: 75 },
        { date: day(-3), value: 69 },
        { date: day(-2), value: 66 },
        { date: day(-1), value: 64 },
        { date: day(0), value: 61 }
      ],
      scopeChanges: [{ date: day(-4), delta: 5 }]
    }
    """
)

BURNUP_SCRIPT = DAY_HELPER + _code(
    """
    const chart = document.getElementById("burnup-chart")

    /* Completed tasks climb ahead of the ideal line: no badge. */
    chart.data = {
      startDate: day(-5),
      endDate: day(8),
      totalScope: 40,
      dailyValues: [
        { date: day(-5), value: 0 },
        { date: day(-4), value: 5 },
        { date: day(-3), value: 9 },
        { date: day(-2), value: 14 },
        { date: day(-1), value: 18 },
        { date: day(0), value: 21 }
      ],
      scopeChanges: [{ date: day(-2), delta: -3 }]
    }
    """
)

BURNDOWN_INLINE_HTML = _code(
    """
    <mj-burndown-chart unit="story points" show-scope-changes="false">
      <script type="application/json">
      {
        "startDate": "2026-03-02",
        "endDate": "2026-03-13",
        "totalScope": 34,
        "dailyValues": [
          { "date": "2026-03-02", "value": 34 },
          { "date": "2026-03-04", "value": 30 },
          { "date": "2026-03-06", "value": 21 },
          { "date": "2026-03-09", "value": 13 },
          { "date": "2026-03-11", "value": 5 },
          { "date": "2026-03-13", "value": 0 }
        ],
        "scopeChanges": [ { "date": "2026-03-06", "delta": 3 } ]
      }
      </script>
    </mj-burndown-chart>
    """
)

BURNDOWN_STATES_HTML = _code(
    """
    <div class="stack">
      <mj-burndown-chart id="empty-burndown">
        <span slot="empty">The sprint has not started yet.</span>
      </mj-burndown-chart>
      <p class="stack-caption">Malformed inline JSON:</p>
      <mj-burndown-chart id="broken-burndown">
        <script type="application/json">{ "totalScope": 40, "dailyValues": [ { "date": "2026-01-05" "value": 40 } ] }</script>
      </mj-burndown-chart>
    </div>
    """
)

BURNDOWN_EVENTS_SCRIPT = DAY_HELPER + PAUSE_HELPER + CLICK_HELPER + _code(
    """
    const chart = document.getElementById("event-burndown")
    chart.data = {
      startDate: day(-4),
      endDate: day(5),
      totalScope: 30,
      dailyValues: [
        { date: day(-4), value: 30 },
        { date: day(-3), value: 27 },
        { date: day(-2), value: 22 },
        { date: day(-1), value: 20 },
        { date: day(0), value: 17 }
      ]
    }
    chart.addEventListener("mj-point-select", (event) => mjSandbox.log("point", event.detail.point))

    await pause(400)
    const point = clickMark(chart, "point:2")
    await pause(800)
    /* Arrow keys move focus between points; Enter selects the focused one. */
    point.focus()
    pressKey(point, "ArrowRight")
    pressKey(chart.shadowRoot.activeElement, "Enter")
    await pause(800)
    pressKey(chart.shadowRoot.activeElement, "Escape")
    """
)

BURNDOWN_LIVE_SCRIPT = DAY_HELPER + _code(
    """
    const chart = document.getElementById("live-burndown")
    const history = [
      { date: day(-6), value: 50 },
      { date: day(-5), value: 47 },
      { date: day(-4), value: 45 },
      { date: day(-3), value: 42 },
      { date: day(-2), value: 40 },
      { date: day(-1), value: 38 }
    ]
    let remaining = 38

    const draw = () => {
      chart.data = { startDate: day(-6), endDate: day(7), totalScope: 50, dailyValues: history.concat([{ date: day(0), value: remaining }]) }
    }
    draw()

    /* Stories close during today's work: the badge clears once the team catches up. */
    setInterval(() => {
      remaining = remaining > 18 ? remaining - 3 : 38
      draw()
      mjSandbox.log("remaining today", remaining)
    }, 2500)
    """
)

BURNDOWN_CHART = ComponentDoc(
    tag="mj-burndown-chart",
    title="Burndown Chart",
    group="charts",
    summary="Sprint burndown or burnup chart with an ideal line, actual line, scope-change markers, a today line and a Behind schedule badge.",
    description=(
        "<p><code>&lt;mj-burndown-chart&gt;</code> plots the work remaining "
        "(burndown) or completed (burnup) per day of a sprint. A dashed ideal "
        "line runs from the total scope to zero (or from zero to the total) "
        "across the sprint; the solid actual line joins the daily values up to "
        "now &mdash; values dated after now are plans and are not plotted. "
        "Amber dashed lines mark days on which scope was added or removed, "
        "and a red dashed line marks today.</p>"
        "<p>The sprint runs from <code>start-date</code> to "
        "<code>end-date</code>, else from <code>data.startDate</code> to "
        "<code>data.endDate</code>, else over the extent of the values. The "
        "&ldquo;Behind schedule&rdquo; badge compares the latest actual value "
        "with the ideal at the earlier of now and the sprint end; when no "
        "sprint end is declared and the latest value is from today or "
        "yesterday, the sprint is taken to be running with an unknown end and "
        "no verdict is shown.</p>"
        "<p>Each data point is a button: selecting it enlarges it and writes "
        "its date, value and the ideal value to the read-out in the header "
        "(<code>mj-point-select</code>); Escape clears it. The value axis is "
        "titled with the <code>unit</code>. The header button discloses a "
        "table of values, ideal values and scope changes.</p>"
        + DATA_SOURCES_HTML + DATES_HTML
    ),
    how_to_use=(
        "<p>Assign <code>{ totalScope, dailyValues, scopeChanges, startDate, "
        "endDate }</code>: <code>dailyValues</code> are "
        "<code>{ date, value }</code>, <code>scopeChanges</code> "
        "<code>{ date, delta }</code>. Without <code>totalScope</code> the "
        "first value (burndown) or the highest value (burnup) is used.</p>"
        "<p>Set <code>mode=\"burnup\"</code> to plot completed work, "
        "<code>unit</code> for the axis title and accessible labels, and "
        "<code>show-ideal=\"false\"</code> / "
        "<code>show-scope-changes=\"false\"</code> to hide those layers. "
        "Reassign <code>data</code> as the day progresses to update the badge.</p>"
    ),
    example="",
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>A two-week sprint, one week in: the remaining work is above "
                "the ideal line, so the &ldquo;Behind schedule&rdquo; badge "
                "shows. Five points were added four days ago. Click a point to "
                "read its values in the header.</p>"
            ),
            html='<mj-burndown-chart id="demo-burndown" unit="points"></mj-burndown-chart>\n',
            script=BURNDOWN_BASIC_SCRIPT,
        ),
        ComponentExample(
            key="burnup",
            title="Burnup, on track",
            description=(
                "<p><code>mode=\"burnup\"</code> with <code>unit=\"tasks\"</code>: "
                "completed work climbs ahead of the ideal line, so there is no "
                "badge. A scope reduction is marked.</p>"
            ),
            html='<mj-burndown-chart id="burnup-chart" mode="burnup" unit="tasks"></mj-burndown-chart>\n',
            script=BURNUP_SCRIPT,
        ),
        ComponentExample(
            key="inline-json",
            title="Finished sprint from inline JSON",
            description=(
                "<p>A past sprint declared inline that burned down to zero: no "
                "badge, no today line. <code>show-scope-changes=\"false\"</code> "
                "hides the scope marker (the table still lists it).</p>"
            ),
            html=BURNDOWN_INLINE_HTML,
        ),
        ComponentExample(
            key="states",
            title="Empty and error states",
            description=(
                "<p>No data shows the <code>empty</code> slot; inline JSON with "
                "a missing comma shows the parser error and emits "
                "<code>mj-error</code>.</p>"
            ),
            html=BURNDOWN_STATES_HTML,
            css=STACK_CSS,
        ),
        ComponentExample(
            key="events",
            title="Point selection and keyboard",
            description=(
                "<p>The script clicks a point (<code>mj-point-select</code>), "
                "moves to the next one with ArrowRight, selects it with Enter "
                "and clears the selection with Escape "
                "(<code>mj-point-deselect</code>).</p>"
            ),
            html='<mj-burndown-chart id="event-burndown"></mj-burndown-chart>\n',
            script=BURNDOWN_EVENTS_SCRIPT,
        ),
        ComponentExample(
            key="live",
            title="Live updates",
            description=(
                "<p>Every 2.5 seconds the script lowers today's remaining value "
                "and reassigns <code>data</code>; watch the badge disappear when "
                "the team gets below the ideal line, then the demo starts "
                "over.</p>"
            ),
            html='<mj-burndown-chart id="live-burndown" unit="points"></mj-burndown-chart>\n',
            script=BURNDOWN_LIVE_SCRIPT,
        ),
    ],
    attributes=[
        AttributeDoc(name="mode", description="`burndown` plots work remaining, `burnup` work completed.", kind="enum", values=["burndown", "burnup"], default="burndown"),
        AttributeDoc(name="unit", description="Unit of the values: the value-axis title and the accessible labels.", kind="string", values=["points", "story points", "tasks", "hours"], default="points"),
        AttributeDoc(name="start-date", description="Sprint start (`YYYY-MM-DD` or ISO date-time); overrides `data.startDate`.", kind="string"),
        AttributeDoc(name="end-date", description="Sprint end, inclusive; overrides `data.endDate`. The ideal line and the badge use it.", kind="string"),
        _today_attribute("Dashed red line at the current time."),
        AttributeDoc(name="show-ideal", description="Set to `false` to hide the ideal line and its legend entry.", kind="boolean", default="true"),
        AttributeDoc(name="show-scope-changes", description="Set to `false` to hide the scope-change markers and their legend entry.", kind="boolean", default="true"),
        _src_attribute("sprint values"),
    ],
    events=[
        ("mj-point-select", "A data point was activated; the header read-out shows its values.", "{ point: object }"),
        ("mj-point-deselect", "Escape cleared the selected point.", "{}"),
        ("mj-data-load", "Data was assigned (or loaded) and drawn.", "{ days: number, unit: string }"),
        ERROR_EVENT,
    ],
    slots=[
        EMPTY_SLOT,
        FALLBACK_SLOT,
    ],
    properties=[
        _data_property("{ totalScope, dailyValues, scopeChanges, startDate, endDate }"),
        ("selectedPoint", "object | null. Read-only. The selected daily-value object from the data."),
    ],
    methods=[],
    parts=[
        ("wrapper", "Outer group; its aria-label summarises the sprint and the verdict."),
        ("status-badge", "The Behind schedule badge (hidden when on track)."),
        ("point-detail", "The read-out of the selected point (role status)."),
        ("svg", "The chart SVG (role group)."),
        ("value-axis", "The value axis line."),
        ("value-axis-title", "The value axis title (the unit)."),
        ("time-axis", "The time axis line."),
        ("ideal-line", "The dashed ideal line."),
        ("actual-line", "The actual line."),
        ("data-point", "Each data point (role button)."),
        ("scope-change-marker", "Each scope-change marker."),
        ("today-marker", "The today line."),
        ("legend", "The legend below the chart."),
        ("data-table", "The disclosed table of values."),
        EMPTY_STATE_PART,
    ],
    css_properties=[
        ("--mj-accent", "Theme token for the actual line and points."),
        ("--mj-color-warning", "Theme token for scope-change markers."),
        ("--mj-color-danger / --mj-color-danger-surface", "Theme tokens for the today line and the badge."),
    ],
)


# ---------------------------------------------------------------------------
# mj-cumulative-flow
# ---------------------------------------------------------------------------

CFD_STATES_JS = _code(
    """
    const states = [
      { id: "backlog", name: "Backlog" },
      { id: "ready", name: "Ready" },
      { id: "doing", name: "In progress" },
      { id: "review", name: "In review" },
      { id: "done", name: "Done" }
    ]
    /* Two weeks of daily snapshots ending today: backlog drains into done. */
    const series = []
    for (let offset = -13; offset <= 0; offset = offset + 1) {
      const n = offset + 13
      series.push({ date: day(offset), backlog: 30 - n, ready: 8 + (n % 3), doing: 5 + Math.round(n / 4), review: 2 + (n % 2), done: n * 2 })
    }
    """
)

CFD_BASIC_SCRIPT = DAY_HELPER + CFD_STATES_JS + _code(
    """
    const flow = document.getElementById("demo-flow")

    /* Include all of today so the today line shows after the last snapshot. */
    flow.setAttribute("end-date", day(0))
    flow.data = { states: states, dailySeries: series }
    """
)

CFD_INLINE_HTML = _code(
    """
    <mj-cumulative-flow normalized>
      <script type="application/json">
      {
        "states": [
          { "id": "todo", "name": "To do" },
          { "id": "doing", "name": "Doing" },
          { "id": "done", "name": "Done" }
        ],
        "dailySeries": [
          { "date": "2026-04-06", "todo": 20, "doing": 4, "done": 0 },
          { "date": "2026-04-07", "todo": 18, "doing": 5, "done": 2 },
          { "date": "2026-04-08", "todo": 16, "doing": 6, "done": 4 },
          { "date": "2026-04-09", "todo": 15, "doing": 5, "done": 7 },
          { "date": "2026-04-10", "todo": 12, "doing": 6, "done": 9 },
          { "date": "2026-04-13", "todo": 10, "doing": 5, "done": 13 },
          { "date": "2026-04-14", "todo": 7, "doing": 6, "done": 16 },
          { "date": "2026-04-15", "todo": 5, "doing": 4, "done": 21 }
        ]
      }
      </script>
    </mj-cumulative-flow>
    """
)

CFD_STATES_HTML = _code(
    """
    <div class="stack">
      <mj-cumulative-flow id="empty-flow">
        <span slot="empty">No board snapshots recorded yet.</span>
      </mj-cumulative-flow>
      <p class="stack-caption">Malformed inline JSON:</p>
      <mj-cumulative-flow id="broken-flow">
        <script type="application/json">{ "states": [ { "id": "todo" } ], "dailySeries": </script>
      </mj-cumulative-flow>
    </div>
    """
)

CFD_EVENTS_SCRIPT = DAY_HELPER + PAUSE_HELPER + CLICK_HELPER + CFD_STATES_JS + _code(
    """
    const flow = document.getElementById("event-flow")
    flow.data = { states: states, dailySeries: series }
    flow.addEventListener("mj-column-select", (event) => mjSandbox.log("day", event.detail))

    await pause(400)
    /* The legend buttons hide and show a band; the other bands keep their colours. */
    const legend = flow.shadowRoot.querySelectorAll("[part=legend-item]")
    legend[0].click()
    await pause(700)
    mjSandbox.log("hidden states", Array.from(flow.hiddenStates))
    legend[0].click()
    await pause(500)
    /* A day column shows counts, WIP and the approximate lead time in the header. */
    const column = clickMark(flow, "col:10")
    await pause(900)
    pressKey(column, "Escape")
    """
)

CFD_LIVE_SCRIPT = DAY_HELPER + CFD_STATES_JS + _code(
    """
    const flow = document.getElementById("live-flow")
    flow.setAttribute("end-date", day(0))
    const today = series[series.length - 1]
    const order = ["backlog", "ready", "doing", "review", "done"]
    flow.data = { states: states, dailySeries: series }

    /* Every 2.5 seconds a card moves one column to the right on today's board. */
    setInterval(() => {
      const movable = order.slice(0, 4).filter((id) => today[id] > 0)
      const from = movable[Math.floor(Math.random() * movable.length)]
      const to = order[order.indexOf(from) + 1]
      today[from] = today[from] - 1
      today[to] = today[to] + 1
      flow.data = { states: states, dailySeries: series.slice() }
      mjSandbox.log("card moved", from + " -> " + to)
    }, 2500)
    """
)

CUMULATIVE_FLOW = ComponentDoc(
    tag="mj-cumulative-flow",
    title="Cumulative Flow Diagram",
    group="charts",
    summary="Stacked area chart of work items per workflow state over time, with a toggleable legend and a WIP / lead-time read-out per day.",
    description=(
        "<p><code>&lt;mj-cumulative-flow&gt;</code> stacks one band per "
        "workflow state (first state at the bottom) over the days of "
        "<code>dailySeries</code>. Widening bands show queues building up; "
        "parallel bands show steady flow. Each state keeps the colour and fill "
        "texture of its position in <code>data.states</code> whether or not "
        "other states are hidden, and the legend swatches use the same "
        "texture, so the chart does not rely on colour alone.</p>"
        "<p>The legend buttons toggle a band (<code>mj-state-toggle</code>); "
        "<code>normalized</code> shows each day as percentages of the visible "
        "states. Every day is a selectable column: selecting it writes the "
        "counts, the work in progress (items between the first and the last "
        "state) and the approximate lead time to the header read-out "
        "(<code>mj-column-select</code>); Escape clears it. A single day is "
        "drawn as a bar. The header button discloses a table of all "
        "counts.</p>"
        + DATA_SOURCES_HTML + DATES_HTML
    ),
    how_to_use=(
        "<p>Assign <code>{ states, dailySeries }</code>: <code>states</code> "
        "is <code>[{ id, name }]</code> in flow order, and each row of "
        "<code>dailySeries</code> is <code>{ date, &lt;stateId&gt;: count, "
        "... }</code> (missing or negative counts are 0). "
        "<code>start-date</code> / <code>end-date</code> limit the rows that "
        "are drawn. The approximate lead time needs at least three states.</p>"
    ),
    example="",
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>Two weeks of daily snapshots ending today across five "
                "states; the today line sits just after the last snapshot. "
                "Click a legend entry to hide a band, or a day to read its WIP "
                "and lead time.</p>"
            ),
            html='<mj-cumulative-flow id="demo-flow"></mj-cumulative-flow>\n',
            script=CFD_BASIC_SCRIPT,
        ),
        ComponentExample(
            key="normalized",
            title="Normalized, from inline JSON",
            description=(
                "<p>Inline JSON with three states and <code>normalized</code>: "
                "each day fills 100%, so the share of finished work is easy to "
                "read.</p>"
            ),
            html=CFD_INLINE_HTML,
        ),
        ComponentExample(
            key="states",
            title="Empty and error states",
            description=(
                "<p>No data shows the <code>empty</code> slot; truncated inline "
                "JSON shows the parser error and emits <code>mj-error</code>.</p>"
            ),
            html=CFD_STATES_HTML,
            css=STACK_CSS,
        ),
        ComponentExample(
            key="events",
            title="Legend toggle and day selection",
            description=(
                "<p>The script hides and shows the Backlog band "
                "(<code>mj-state-toggle</code>), selects a day "
                "(<code>mj-column-select</code> with its counts) and clears it "
                "with Escape (<code>mj-column-deselect</code>).</p>"
            ),
            html='<mj-cumulative-flow id="event-flow"></mj-cumulative-flow>\n',
            script=CFD_EVENTS_SCRIPT,
        ),
        ComponentExample(
            key="live",
            title="Live board",
            description=(
                "<p>Every 2.5 seconds a card moves one state to the right on "
                "today's board; the script reassigns <code>data</code> and the "
                "last day of the chart changes.</p>"
            ),
            html='<mj-cumulative-flow id="live-flow"></mj-cumulative-flow>\n',
            script=CFD_LIVE_SCRIPT,
        ),
    ],
    attributes=[
        AttributeDoc(name="normalized", description="Show each day as percentages of the visible states instead of counts.", kind="boolean"),
        AttributeDoc(name="start-date", description="`YYYY-MM-DD` or ISO date-time: rows before it are not drawn and the axis starts there.", kind="string"),
        AttributeDoc(name="end-date", description="`YYYY-MM-DD` (inclusive) or ISO date-time: rows after it are not drawn and the axis ends there.", kind="string"),
        _today_attribute("Dashed red line at the current time."),
        _src_attribute("states and daily series"),
    ],
    events=[
        ("mj-state-toggle", "A legend button hid or showed a state's band.", "{ stateId: string, visible: boolean }"),
        ("mj-column-select", "A day column was activated; the read-out shows its counts, WIP and lead time.", "{ date: string, values: { [stateId]: number } }"),
        ("mj-column-deselect", "Escape cleared the selected day.", "{}"),
        ("mj-data-load", "Data was assigned (or loaded) and drawn.", "{ states: number, days: number }"),
        ERROR_EVENT,
    ],
    slots=[
        EMPTY_SLOT,
        FALLBACK_SLOT,
    ],
    properties=[
        _data_property("{ states, dailySeries }"),
        ("hiddenStates", "Set<string>. Read-only. Ids of the states hidden through the legend; ids the new data lacks are dropped."),
        ("selectedDate", "string | null. Read-only. `YYYY-MM-DD` of the selected day."),
    ],
    methods=[],
    parts=[
        ("wrapper", "Outer group; its aria-label states the states, days and date range."),
        ("column-detail", "The read-out of the selected day (role status)."),
        ("svg", "The chart SVG (role group)."),
        ("value-axis", "The value axis line."),
        ("time-axis", "The time axis line."),
        ("state-band", "Each state band."),
        ("day-column", "Each selectable day column (role button)."),
        ("today-marker", "The today line."),
        ("legend", "The legend group."),
        ("legend-item", "Each legend toggle button (aria-pressed)."),
        ("data-table", "The disclosed table of counts."),
        EMPTY_STATE_PART,
    ],
    css_properties=[
        ("--mj-chart-series-1 … --mj-chart-series-8", "Band colours by state position; past eight the colours repeat with a different texture."),
        ("--mj-surface", "Theme token for the band textures."),
    ],
)


# ---------------------------------------------------------------------------
# mj-velocity-chart
# ---------------------------------------------------------------------------

VELOCITY_BASIC_SCRIPT = _code(
    """
    const chart = document.getElementById("demo-velocity")
    chart.data = {
      sprints: [
        { name: "Sprint 8", committed: 40, completed: 37 },
        { name: "Sprint 9", committed: 42, completed: 45 },
        { name: "Sprint 10", committed: 44, completed: 40 },
        { name: "Sprint 11", committed: 45, completed: 48 },
        { name: "Sprint 12", committed: 46, completed: 43 },
        { name: "Sprint 13", committed: 48, completed: 50 },
        { name: "Sprint 14", committed: 48, completed: 22 }
      ]
    }
    """
)

VELOCITY_INLINE_HTML = _code(
    """
    <mj-velocity-chart bar-mode="overlay" unit="tasks" rolling-window="2">
      <script type="application/json">
      {
        "sprints": [
          { "name": "January", "committed": 18, "completed": 15 },
          { "name": "February", "committed": 20, "completed": 21 },
          { "name": "Hardening", "committed": 0, "completed": 6 },
          { "name": "March", "committed": 22, "completed": 16 },
          { "name": "April", "committed": 20, "completed": 20 }
        ]
      }
      </script>
    </mj-velocity-chart>
    """
)

VELOCITY_STATES_HTML = _code(
    """
    <div class="stack">
      <mj-velocity-chart id="empty-velocity">
        <span slot="empty">Velocity appears after the first finished sprint.</span>
      </mj-velocity-chart>
      <p class="stack-caption">Malformed inline JSON:</p>
      <mj-velocity-chart id="broken-velocity">
        <script type="application/json">{ "sprints": [ { "name": 'Sprint 1' } ] }</script>
      </mj-velocity-chart>
    </div>
    """
)

VELOCITY_EVENTS_SCRIPT = PAUSE_HELPER + CLICK_HELPER + _code(
    """
    const chart = document.getElementById("event-velocity")
    chart.data = {
      sprints: [
        { name: "Sprint 21", committed: 30, completed: 31 },
        { name: "Sprint 22", committed: 32, completed: 24 },
        { name: "Sprint 23", committed: 30, completed: 30 }
      ]
    }
    chart.addEventListener("mj-sprint-select", (event) => mjSandbox.log("sprint", event.detail.sprint))

    await pause(400)
    const group = clickMark(chart, "sprint:1")
    await pause(800)
    mjSandbox.log("rolling average", chart.rollingAverage)
    pressKey(group, "ArrowRight")
    pressKey(chart.shadowRoot.activeElement, " ")
    await pause(800)
    pressKey(chart.shadowRoot.activeElement, "Escape")
    """
)

VELOCITY_LIVE_SCRIPT = _code(
    """
    const chart = document.getElementById("live-velocity")
    const sprints = [
      { name: "Sprint 30", committed: 34, completed: 31 },
      { name: "Sprint 31", committed: 35, completed: 36 },
      { name: "Sprint 32", committed: 36, completed: 30 },
      { name: "Sprint 33", committed: 34, completed: 35 }
    ]
    let number = 33
    chart.data = { sprints: sprints.slice() }

    /* Every 3 seconds another sprint closes; the chart keeps the last eight. */
    setInterval(() => {
      number = number + 1
      const committed = 30 + Math.round(Math.random() * 10)
      const completed = Math.max(0, committed + Math.round(Math.random() * 14) - 10)
      sprints.push({ name: "Sprint " + number, committed: committed, completed: completed })
      while (sprints.length > 8) {
        sprints.shift()
      }
      chart.data = { sprints: sprints.slice() }
    }, 3000)
    """
)

VELOCITY_CHART = ComponentDoc(
    tag="mj-velocity-chart",
    title="Velocity Chart",
    group="charts",
    summary="Bar chart of committed versus completed work per sprint with a rolling-average line and delivery captions.",
    description=(
        "<p><code>&lt;mj-velocity-chart&gt;</code> draws one group per sprint "
        "with a muted &ldquo;committed&rdquo; bar and a solid "
        "&ldquo;completed&rdquo; bar, and an amber line through the rolling "
        "average of completed work over the last <code>rolling-window</code> "
        "sprints. A sprint that completed more than its commitment is captioned "
        "&ldquo;Exceeded&rdquo; (green); one that fell more than 20% short is "
        "&ldquo;Under-delivered&rdquo; (red); short of room the caption "
        "becomes an arrow. Sprint labels are shortened in the middle so "
        "&ldquo;Sprint 10&rdquo; and &ldquo;Sprint 11&rdquo; stay distinct, "
        "and groups keep a minimum width so a long history scrolls.</p>"
        "<p>In <code>bar-mode=\"overlay\"</code> the completed bar is drawn "
        "narrower inside the committed bar. Each sprint group is a button: "
        "selecting it outlines the group and writes its values, status and "
        "average to the header read-out (<code>mj-sprint-select</code>); "
        "Escape clears it. The header button discloses a table with the "
        "difference and the average per sprint.</p>"
        + DATA_SOURCES_HTML
    ),
    how_to_use=(
        "<p>Assign <code>{ sprints: [{ name, committed, completed }] }</code> "
        "(negative values count as 0; a missing name becomes &ldquo;Sprint "
        "N&rdquo;). Set <code>unit</code> for the value-axis title, "
        "<code>rolling-window</code> for the average (a whole number, at least "
        "1) and <code>show-average=\"false\"</code> / "
        "<code>show-committed=\"false\"</code> to hide those layers. "
        "<code>rollingAverage</code> returns the averages drawn.</p>"
    ),
    example="",
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>Seven sprints with a three-sprint rolling average; Sprint 14 "
                "is under-delivered and two sprints exceeded their commitment. "
                "Click a sprint to read its numbers in the header.</p>"
            ),
            html='<mj-velocity-chart id="demo-velocity" unit="points" rolling-window="3"></mj-velocity-chart>\n',
            script=VELOCITY_BASIC_SCRIPT,
        ),
        ComponentExample(
            key="overlay",
            title="Overlay bars from inline JSON",
            description=(
                "<p>Inline JSON with <code>bar-mode=\"overlay\"</code>, "
                "<code>unit=\"tasks\"</code> and a two-sprint average. The "
                "Hardening sprint committed nothing, so it has no committed "
                "bar.</p>"
            ),
            html=VELOCITY_INLINE_HTML,
        ),
        ComponentExample(
            key="states",
            title="Empty and error states",
            description=(
                "<p>No data shows the <code>empty</code> slot; inline JSON with "
                "single quotes shows the parser error and emits "
                "<code>mj-error</code>.</p>"
            ),
            html=VELOCITY_STATES_HTML,
            css=STACK_CSS,
        ),
        ComponentExample(
            key="events",
            title="Sprint selection and keyboard",
            description=(
                "<p>The script clicks Sprint 22 (<code>mj-sprint-select</code>), "
                "logs <code>rollingAverage</code>, moves right and selects with "
                "Space, then clears with Escape (<code>mj-sprint-deselect</code>).</p>"
            ),
            html='<mj-velocity-chart id="event-velocity"></mj-velocity-chart>\n',
            script=VELOCITY_EVENTS_SCRIPT,
        ),
        ComponentExample(
            key="live",
            title="Live updates",
            description=(
                "<p>Every 3 seconds another sprint closes with random numbers; "
                "the chart keeps the last eight sprints and the average "
                "follows.</p>"
            ),
            html='<mj-velocity-chart id="live-velocity"></mj-velocity-chart>\n',
            script=VELOCITY_LIVE_SCRIPT,
        ),
    ],
    attributes=[
        AttributeDoc(name="unit", description="Unit of the values: the value-axis title and the accessible labels.", kind="string", values=["points", "tasks", "hours"], default="points"),
        AttributeDoc(name="bar-mode", description="`grouped` draws the bars side by side; `overlay` draws the completed bar inside the committed bar.", kind="enum", values=["grouped", "overlay"], default="grouped"),
        AttributeDoc(name="rolling-window", description="Number of sprints in the rolling average; values below 1 or not a number fall back to 3.", kind="number", default="3"),
        AttributeDoc(name="show-average", description="Set to `false` to hide the rolling-average line and its legend entry.", kind="boolean", default="true"),
        AttributeDoc(name="show-committed", description="Set to `false` to hide the committed bars and their legend entry.", kind="boolean", default="true"),
        _src_attribute("sprints"),
    ],
    events=[
        ("mj-sprint-select", "A sprint group was activated; the read-out shows its values.", "{ sprint: object }"),
        ("mj-sprint-deselect", "Escape cleared the selected sprint.", "{}"),
        ("mj-data-load", "Data was assigned (or loaded) and drawn.", "{ sprints: number }"),
        ERROR_EVENT,
    ],
    slots=[
        EMPTY_SLOT,
        FALLBACK_SLOT,
    ],
    properties=[
        _data_property("{ sprints }"),
        ("selectedSprint", "object | null. Read-only. The selected sprint object from the data."),
        ("rollingAverage", "number[]. Read-only. The rolling average per sprint, in data order."),
    ],
    methods=[],
    parts=[
        ("wrapper", "Outer group; its aria-label states the sprint count, unit and window."),
        ("sprint-detail", "The read-out of the selected sprint (role status)."),
        ("svg", "The chart SVG (role group)."),
        ("value-axis", "The value axis line."),
        ("value-axis-title", "The value axis title (the unit)."),
        ("sprint-axis", "The sprint axis line."),
        ("bar-group", "Each sprint group (role button)."),
        ("committed-bar", "Each committed bar."),
        ("completed-bar", "Each completed bar."),
        ("average-line", "The rolling-average line."),
        ("legend", "The legend below the chart."),
        ("legend-committed", "The committed legend entry."),
        ("legend-completed", "The completed legend entry."),
        ("legend-average", "The average legend entry."),
        ("data-table", "The disclosed table of sprints."),
        EMPTY_STATE_PART,
    ],
    css_properties=[
        ("--mj-chart-series-secondary", "Fill of the committed bars (default --mj-bg-muted)."),
        ("--mj-chart-series-secondary-border", "Outline of the committed bars (default --mj-border-strong)."),
        ("--mj-accent", "Theme token for the completed bars."),
        ("--mj-color-warning", "Theme token for the rolling-average line."),
    ],
)


# ---------------------------------------------------------------------------
# mj-dependency-graph
# ---------------------------------------------------------------------------

DEPENDENCY_BASIC_SCRIPT = _code(
    """
    const graph = document.getElementById("demo-dependencies")
    graph.data = {
      nodes: [
        { id: "design", name: "Design", status: "done", estimate: "3 d" },
        { id: "api", name: "API layer", status: "done", estimate: "5 d" },
        { id: "db", name: "Database schema", status: "done", estimate: "2 d" },
        { id: "backend", name: "Backend", status: "in-progress", estimate: "8 d" },
        { id: "frontend", name: "Frontend", status: "in-progress", estimate: "6 d" },
        { id: "tests", name: "End-to-end tests", status: "todo", estimate: "4 d" },
        { id: "deploy", name: "Deployment", status: "todo", estimate: "1 d" }
      ],
      edges: [
        { from: "design", to: "api" },
        { from: "design", to: "frontend" },
        { from: "api", to: "backend" },
        { from: "db", to: "backend" },
        { from: "backend", to: "tests" },
        { from: "frontend", to: "tests" },
        { from: "tests", to: "deploy" }
      ],
      criticalPath: ["design", "api", "backend", "tests", "deploy"]
    }
    """
)

DEPENDENCY_INLINE_HTML = _code(
    """
    <mj-dependency-graph show-critical-path="false">
      <script type="application/json">
      {
        "nodes": [
          { "id": "schema", "name": "Schema", "status": "done" },
          { "id": "migrations", "name": "Migrations", "status": "blocked", "estimate": "2 d" },
          { "id": "seed", "name": "Seed data", "status": "in-progress" },
          { "id": "reports", "name": "Reports", "status": "todo" },
          { "id": "docs", "name": "API docs", "status": "todo" },
          { "id": "changelog", "name": "Changelog", "status": "todo" }
        ],
        "edges": [
          { "from": "schema", "to": "migrations" },
          { "from": "migrations", "to": "seed" },
          { "from": "seed", "to": "schema" },
          { "from": "seed", "to": "reports" },
          { "from": "docs", "to": "changelog" }
        ],
        "criticalPath": [ "schema", "migrations", "seed", "reports" ]
      }
      </script>
    </mj-dependency-graph>
    """
)

DEPENDENCY_EQUIVALENT_HTML = _code(
    """
    <div class="stack">
      <mj-dependency-graph>
        <script type="application/json">
        {
          "nodes": [
            { "id": "spec", "name": "Spec", "status": "done" },
            { "id": "api", "name": "API", "status": "in-progress" },
            { "id": "ui", "name": "UI", "status": "todo" },
            { "id": "ship", "name": "Ship", "status": "todo" }
          ],
          "edges": [ { "from": "spec", "to": "api" }, { "from": "spec", "to": "ui" }, { "from": "api", "to": "ship" }, { "from": "ui", "to": "ship" } ],
          "criticalPath": [ "spec", "api", "ship" ]
        }
        </script>
      </mj-dependency-graph>
      <p class="stack-caption">The same graph as &lt;mj-chart type="dependency-graph"&gt;:</p>
      <mj-chart type="dependency-graph" label="Dependency graph">
        <script type="application/json">
        {
          "nodes": [
            { "id": "spec", "label": "Spec", "status": "done" },
            { "id": "api", "label": "API", "status": "in-progress" },
            { "id": "ui", "label": "UI", "status": "todo" },
            { "id": "ship", "label": "Ship", "status": "todo" }
          ],
          "links": [ { "source": "spec", "target": "api" }, { "source": "spec", "target": "ui" }, { "source": "api", "target": "ship" }, { "source": "ui", "target": "ship" } ],
          "criticalPath": [ "spec", "api", "ship" ]
        }
        </script>
      </mj-chart>
    </div>
    """
)

DEPENDENCY_STATES_HTML = _code(
    """
    <div class="stack">
      <mj-dependency-graph id="empty-dependencies">
        <span slot="empty">No work items have dependencies yet.</span>
      </mj-dependency-graph>
      <p class="stack-caption"><code>src</code> pointing at a missing file:</p>
      <mj-dependency-graph id="missing-dependencies" src="/static/data/missing-dependencies.json"></mj-dependency-graph>
    </div>
    """
)

DEPENDENCY_EVENTS_HTML = _code(
    """
    <mj-dependency-graph id="event-dependencies">
      <p slot="node-detail"><a href="#work-item">Open the work item</a></p>
    </mj-dependency-graph>
    """
)

DEPENDENCY_EVENTS_SCRIPT = PAUSE_HELPER + CLICK_HELPER + _code(
    """
    const graph = document.getElementById("event-dependencies")
    graph.data = {
      nodes: [
        { id: "a", name: "Auth service", status: "done", estimate: "5 d" },
        { id: "b", name: "Billing", status: "in-progress", estimate: "8 d" },
        { id: "c", name: "Invoices", status: "todo" }
      ],
      edges: [{ from: "a", to: "b" }, { from: "b", to: "c" }],
      criticalPath: ["a", "b", "c"]
    }
    graph.addEventListener("mj-node-select", (event) => mjSandbox.log("node", event.detail.node.name))

    await pause(400)
    clickMark(graph, "node:1")
    await pause(900)
    graph.shadowRoot.querySelector("[part=detail-panel] .detail-close").click()
    await pause(500)
    /* A new edge c -> a closes a cycle: banner, dashed return edge, mj-cycle-detected. */
    graph.data = Object.assign({}, graph.data, { edges: graph.data.edges.concat([{ from: "c", to: "a" }]) })
    mjSandbox.log("cycles", graph.cycles)
    """
)

DEPENDENCY_LIVE_SCRIPT = _code(
    """
    const graph = document.getElementById("live-dependencies")
    const nodes = [
      { id: "spec", name: "Spec" },
      { id: "ui", name: "UI mock-ups" },
      { id: "api", name: "API" },
      { id: "client", name: "Client" },
      { id: "qa", name: "QA" },
      { id: "ship", name: "Ship" }
    ]
    const edges = [
      { from: "spec", to: "ui" },
      { from: "spec", to: "api" },
      { from: "ui", to: "client" },
      { from: "api", to: "client" },
      { from: "client", to: "qa" },
      { from: "qa", to: "ship" }
    ]
    let progress = 0

    /* Items before `progress` are done, the next one in progress, the rest to do. */
    const draw = () => {
      graph.data = {
        nodes: nodes.map((node, index) => Object.assign({}, node, { status: index < progress ? "done" : (index === progress ? "in-progress" : "todo") })),
        edges: edges,
        criticalPath: ["spec", "api", "client", "qa", "ship"]
      }
    }
    draw()

    setInterval(() => {
      progress = progress >= nodes.length ? 0 : progress + 1
      draw()
    }, 2500)
    """
)

DEPENDENCY_GRAPH = ComponentDoc(
    tag="mj-dependency-graph",
    title="Dependency Graph",
    group="charts",
    summary="Directed dependency graph laid out by level, with critical-path highlighting and cycle detection.",
    description=(
        _wrapper_html("mj-dependency-graph", "dependency-graph") +
        "<p>It draws work items or "
        "modules as boxes and their dependencies as arrows. Nodes are placed "
        "in columns by their longest path from a root, an edge that skips "
        "columns is routed between the boxes, and each column is ordered to "
        "reduce crossings. Each node shows its name and status "
        "(<code>todo</code>, <code>in-progress</code>, <code>done</code>, "
        "<code>blocked</code>; anything else is shown as given).</p>"
        "<p>Nodes listed in <code>criticalPath</code> are drawn amber, and so "
        "is every edge that joins two consecutive entries of the path. A cycle "
        "does not break the layout: the edge that closes it is a dashed red "
        "curved edge, the nodes on it get a warning badge, a banner names the "
        "cycle and <code>mj-cycle-detected</code> fires. Edges that name an "
        "unknown node are ignored. Activating a node opens an inline detail "
        "panel with its status and <code>estimate</code>. The graph fits the "
        "chart's width and grows with its busiest column.</p>"
        + WRAPPER_DATA_HTML + WRAPPER_MARKS_HTML
    ),
    how_to_use=(
        "<p>Assign <code>{ nodes, edges, criticalPath }</code>: each node "
        "<code>{ id, name, status, estimate }</code>, each edge "
        "<code>{ from, to }</code> (from the prerequisite to the dependent "
        "item), <code>criticalPath</code> an ordered array of node ids. "
        "<code>show-critical-path=\"false\"</code> turns the highlighting off. "
        "<code>mj-data-load</code> and <code>mj-cycle-detected</code> fire once "
        "per data assignment, not per redraw.</p>"
    ),
    example="",
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>Seven work items with a five-step critical path in amber; "
                "Frontend's edge to the tests is routed between the boxes. "
                "Click a node for its estimate.</p>"
            ),
            html='<mj-dependency-graph id="demo-dependencies"></mj-dependency-graph>\n',
            script=DEPENDENCY_BASIC_SCRIPT,
        ),
        ComponentExample(
            key="cycle",
            title="Cycle, blocked item and disconnected parts",
            description=(
                "<p>Inline JSON whose Seed data &rarr; Schema edge closes a cycle "
                "(banner, dashed return edge, <code>mj-cycle-detected</code> in "
                "Events), a blocked item, a separate Docs &rarr; Changelog pair "
                "and <code>show-critical-path=\"false\"</code>.</p>"
            ),
            html=DEPENDENCY_INLINE_HTML,
        ),
        ComponentExample(
            key="states",
            title="Empty and error states",
            description=(
                "<p>No data shows the <code>empty</code> slot; a "
                "<code>src</code> that answers 404 shows the request error and "
                "emits <code>mj-error</code>.</p>"
            ),
            html=DEPENDENCY_STATES_HTML,
            css=STACK_CSS,
        ),
        ComponentExample(
            key="events",
            title="Selection, detail slot and cycle events",
            description=(
                "<p>The <code>node-detail</code> slot adds a link to the panel. "
                "The script opens Billing (<code>mj-node-select</code>), closes "
                "it (<code>mj-node-deselect</code>), then assigns data with an "
                "extra edge that creates a cycle (<code>mj-cycle-detected</code>).</p>"
            ),
            html=DEPENDENCY_EVENTS_HTML,
            script=DEPENDENCY_EVENTS_SCRIPT,
        ),
        ComponentExample(
            key="live",
            title="Live progress",
            description=(
                "<p>Every 2.5 seconds the next item moves to in progress and "
                "the previous one to done; after shipping the plan starts "
                "over.</p>"
            ),
            html='<mj-dependency-graph id="live-dependencies"></mj-dependency-graph>\n',
            script=DEPENDENCY_LIVE_SCRIPT,
        ),
        ComponentExample(
            key="mj-chart",
            title="The same chart as <mj-chart>",
            description=(
                "<p>The wrapper and <code>&lt;mj-chart type=\"dependency-graph\"&gt;</code> "
                "draw the same graph: the chart type reads <code>nodes</code> with "
                "<code>label</code> and <code>links</code> with <code>source</code> / "
                "<code>target</code> where the wrapper reads <code>name</code> and "
                "<code>edges</code> with <code>from</code> / <code>to</code>; "
                "<code>criticalPath</code> and <code>status</code> are the same.</p>"
            ),
            html=DEPENDENCY_EQUIVALENT_HTML,
            css=STACK_CSS,
        ),
    ],
    attributes=[
        AttributeDoc(name="show-critical-path", description="Set to `false` to draw critical-path nodes and edges like the others.", kind="boolean", default="true"),
        _src_attribute("nodes, edges and critical path"),
    ],
    events=[
        ("mj-node-select", "A node was activated; the detail panel opens.", "{ node: object }"),
        ("mj-node-deselect", "The detail panel was closed (Close button or Escape).", "{}"),
        ("mj-cycle-detected", "The assigned data contains at least one cycle.", "{ cycles: string[][] }"),
        ("mj-data-load", "Data was assigned (or loaded) and drawn.", "{ nodes: number, edges: number, hasCycles: boolean }"),
        ERROR_EVENT,
    ],
    slots=[
        ("node-detail", "Extra content below the details of the selected node.", '<p><a href="#work-item">Open the work item</a></p>'),
        WRAPPER_EMPTY_SLOT,
    ],
    properties=[
        _data_property("{ nodes, edges, criticalPath }"),
        ("selectedNode", "object | null. Read-only. The selected node object from the data."),
        ("cycles", "string[][]. Read-only. Every cycle found, as arrays of node ids."),
        ("zoom", "number. Read-only. Always 1; the graph does not zoom (a tall graph grows and scrolls)."),
    ],
    methods=[],
    parts=WRAPPER_PARTS + [
        ("cycle-banner", "The banner that names the cycles."),
        ("node", "Each node box."),
        ("node critical-path-node", "A node on the critical path carries both names."),
        ("edge", "Each edge; cycle edges carry `data-cycle-edge`."),
        ("edge critical-path-edge", "An edge between consecutive critical-path nodes carries both names."),
        ("cycle-badge", "The warning badge on a node that is part of a cycle."),
        ("detail-panel", "The inline detail panel."),
    ],
    css_properties=[
        ("--mj-color-warning / --mj-color-warning-surface", "Theme tokens for the critical path."),
        ("--mj-color-danger / --mj-color-danger-surface", "Theme tokens for cycle edges, badges and the banner."),
    ],
)


# ---------------------------------------------------------------------------
# mj-workflow-diagram
# ---------------------------------------------------------------------------

WORKFLOW_DATA_JS = _code(
    """
    const reviewFlow = {
      states: [
        { id: "start", name: "Start", type: "start" },
        { id: "draft", name: "Draft", type: "state", description: "The author is writing the change." },
        { id: "review", name: "In review", type: "state", description: "Two approvals are required." },
        { id: "approve", name: "Approved?", type: "decision" },
        { id: "merged", name: "Merged", type: "state" },
        { id: "end", name: "End", type: "end" }
      ],
      transitions: [
        { from: "start", to: "draft", label: "create" },
        { from: "draft", to: "review", label: "submit" },
        { from: "review", to: "approve", label: "decide" },
        { from: "approve", to: "merged", label: "yes" },
        { from: "approve", to: "draft", label: "request changes" },
        { from: "merged", to: "end", label: "close" }
      ]
    }
    """
)

WORKFLOW_BASIC_SCRIPT = WORKFLOW_DATA_JS + _code(
    """
    document.getElementById("demo-workflow").data = reviewFlow
    """
)

WORKFLOW_SWIMLANE_HTML = _code(
    """
    <mj-workflow-diagram diagram-type="swimlane" current-state="triage">
      <script type="application/json">
      {
        "actors": [
          { "id": "customer", "name": "Customer" },
          { "id": "support", "name": "Support" },
          { "id": "eng", "name": "Engineering" }
        ],
        "states": [
          { "id": "open", "name": "Report issue", "type": "start", "actor": "customer" },
          { "id": "triage", "name": "Triage", "actor": "support", "description": "Reproduce and set a priority." },
          { "id": "known", "name": "Known issue?", "type": "decision", "actor": "support" },
          { "id": "fix", "name": "Fix", "actor": "eng" },
          { "id": "reply", "name": "Reply", "actor": "support" },
          { "id": "closed", "name": "Closed", "type": "end", "actor": "customer" }
        ],
        "transitions": [
          { "from": "open", "to": "triage", "label": "new ticket" },
          { "from": "triage", "to": "triage", "label": "needs info" },
          { "from": "triage", "to": "known" },
          { "from": "known", "to": "reply", "label": "yes" },
          { "from": "known", "to": "fix", "label": "no" },
          { "from": "fix", "to": "reply", "label": "deployed" },
          { "from": "reply", "to": "closed" }
        ]
      }
      </script>
    </mj-workflow-diagram>
    """
)

WORKFLOW_STATES_HTML = _code(
    """
    <div class="stack">
      <mj-workflow-diagram id="empty-workflow">
        <span slot="empty">Define states to draw the workflow.</span>
      </mj-workflow-diagram>
      <p class="stack-caption">Malformed inline JSON:</p>
      <mj-workflow-diagram id="broken-workflow">
        <script type="application/json">{ "states": [ { "id": "a" } ], "transitions": [ { "from": "a" "to": "b" } ] }</script>
      </mj-workflow-diagram>
    </div>
    """
)

WORKFLOW_EVENTS_HTML = _code(
    """
    <mj-workflow-diagram id="event-workflow" current-state="draft">
      <p slot="node-detail"><a href="#state-docs">How this state works</a></p>
    </mj-workflow-diagram>
    """
)

WORKFLOW_EVENTS_SCRIPT = WORKFLOW_DATA_JS + PAUSE_HELPER + CLICK_HELPER + _code(
    """
    const diagram = document.getElementById("event-workflow")
    diagram.data = reviewFlow
    diagram.addEventListener("mj-state-change", (event) => mjSandbox.log("current state", event.detail))

    await pause(400)
    clickMark(diagram, "node:2")
    await pause(900)
    pressKey(diagram.shadowRoot.querySelector("[part=detail-panel]"), "Escape")
    await pause(400)
    /* Transitions are marks too: open the rework loop. */
    clickMark(diagram, "transition:4")
    await pause(900)
    diagram.setAttribute("current-state", "review")
    """
)

WORKFLOW_LIVE_SCRIPT = WORKFLOW_DATA_JS + _code(
    """
    const diagram = document.getElementById("live-workflow")
    diagram.data = reviewFlow

    /* A change walks through review, is sent back once, then merges. */
    const path = ["start", "draft", "review", "approve", "draft", "review", "approve", "merged", "end"]
    let position = 0
    setInterval(() => {
      position = (position + 1) % path.length
      diagram.setAttribute("current-state", path[position])
    }, 2500)
    """
)

WORKFLOW_DIAGRAM = ComponentDoc(
    tag="mj-workflow-diagram",
    title="Workflow Diagram",
    group="charts",
    summary="State-machine or cross-actor swimlane process diagram with a pulsing current-state ring and selectable transitions.",
    description=(
        "<p><code>&lt;mj-workflow-diagram&gt;</code> draws states and the "
        "transitions between them. The shape follows the <code>type</code>: "
        "<code>start</code> is a filled circle, <code>end</code> a double "
        "circle, <code>decision</code> a diamond and <code>state</code> (the "
        "default) a rounded box. States are placed in columns by their longest "
        "path from the start states, ignoring transitions that loop back, so a "
        "rework loop does not collapse the layout: it is drawn as a dashed "
        "return edge above the nodes, and a self-transition as a loop above "
        "its node. Transition labels are drawn on the edges.</p>"
        "<p>The state named by <code>current-state</code> gets a pulsing ring "
        "(any shape; the animation stops under reduced motion) and "
        "<code>aria-current</code>. Changing the attribute emits "
        "<code>mj-state-change</code> and announces the new state; an unknown "
        "id is ignored with one console warning. In "
        "<code>diagram-type=\"swimlane\"</code> with <code>actors</code>, each "
        "actor gets a lane and each state goes in the lane of its "
        "<code>actor</code> (unknown actors go to an Unassigned lane) while "
        "the column still follows the flow.</p>"
        "<p>States and transitions are both marks: activating one opens an "
        "inline detail panel (type, actor and description, or from / to / "
        "label).</p>"
        + DATA_SOURCES_HTML + MARKS_HTML
    ),
    how_to_use=(
        "<p>Assign <code>{ states, transitions, actors }</code>: each state "
        "<code>{ id, name, type, actor, description }</code>, each transition "
        "<code>{ from, to, label }</code>, each actor <code>{ id, name }</code>. "
        "Set <code>current-state</code> to the id of the active state and "
        "update it as the process moves; the initial value does not emit "
        "<code>mj-state-change</code>. <code>show-labels=\"false\"</code> "
        "hides the transition labels.</p>"
    ),
    example="",
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>A code-review flow with a decision and a "
                "&ldquo;request changes&rdquo; rework loop drawn as a dashed "
                "return edge. <code>current-state=\"review\"</code> pulses. Click "
                "a state or an edge.</p>"
            ),
            html='<mj-workflow-diagram id="demo-workflow" current-state="review"></mj-workflow-diagram>\n',
            script=WORKFLOW_BASIC_SCRIPT,
        ),
        ComponentExample(
            key="swimlane",
            title="Swimlanes from inline JSON",
            description=(
                "<p><code>diagram-type=\"swimlane\"</code> with three actors, a "
                "&ldquo;needs info&rdquo; self-transition on Triage (the current "
                "state) and state descriptions in the detail panel.</p>"
            ),
            html=WORKFLOW_SWIMLANE_HTML,
        ),
        ComponentExample(
            key="states",
            title="Empty and error states",
            description=(
                "<p>No data shows the <code>empty</code> slot; inline JSON with "
                "a missing comma shows the parser error and emits "
                "<code>mj-error</code>.</p>"
            ),
            html=WORKFLOW_STATES_HTML,
            css=STACK_CSS,
        ),
        ComponentExample(
            key="events",
            title="Selection and state-change events",
            description=(
                "<p>The <code>node-detail</code> slot adds a link. The script "
                "opens In review (<code>mj-node-select</code>), closes it "
                "(<code>mj-node-deselect</code>), opens the rework transition "
                "(<code>mj-transition-select</code>) and moves "
                "<code>current-state</code> to review "
                "(<code>mj-state-change</code>).</p>"
            ),
            html=WORKFLOW_EVENTS_HTML,
            script=WORKFLOW_EVENTS_SCRIPT,
        ),
        ComponentExample(
            key="live",
            title="Live current state",
            description=(
                "<p>Every 2.5 seconds the script moves <code>current-state</code> "
                "along the flow (including one rework round); each move emits "
                "<code>mj-state-change</code>.</p>"
            ),
            html='<mj-workflow-diagram id="live-workflow" current-state="start"></mj-workflow-diagram>\n',
            script=WORKFLOW_LIVE_SCRIPT,
        ),
    ],
    attributes=[
        AttributeDoc(name="diagram-type", description="`swimlane` puts each state in the lane of its actor (needs `data.actors`).", kind="enum", values=["state", "swimlane"], default="state"),
        AttributeDoc(name="current-state", description="Id of the active state: pulsing ring and aria-current. Changes emit `mj-state-change`.", kind="string", values=["start", "draft", "review", "approve", "merged", "end"]),
        AttributeDoc(name="show-labels", description="Set to `false` to hide the transition labels.", kind="boolean", default="true"),
        _src_attribute("states, transitions and actors"),
    ],
    events=[
        ("mj-node-select", "A state was activated; the detail panel opens.", "{ node: object }"),
        ("mj-node-deselect", "The detail panel of a state was closed.", "{}"),
        ("mj-transition-select", "A transition was activated; the detail panel opens.", "{ transition: object }"),
        ("mj-state-change", "`current-state` changed after the first render.", "{ from: string, to: string }"),
        ("mj-data-load", "Data was assigned (or loaded) and drawn.", "{ states: number, transitions: number, actors: number }"),
        ERROR_EVENT,
    ],
    slots=[
        ("node-detail", "Extra content below the details of the selected state or transition.", '<p><a href="#state-docs">How this state works</a></p>'),
        EMPTY_SLOT,
        FALLBACK_SLOT,
    ],
    properties=[
        _data_property("{ states, transitions, actors }"),
        ("selectedNode", "object | null. Read-only. The selected state object from the data."),
        ("selectedTransition", "object | null. Read-only. The selected transition object from the data."),
    ],
    methods=[],
    parts=[
        ("wrapper", "Outer group; its aria-label states states, transitions and actors."),
        ("toolbar", "Toolbar with the definition-list button."),
        ("canvas", "Scrolling area that holds the SVG."),
        ("svg", "The diagram SVG (role group)."),
        ("state-node", "Each state that is not current (role button)."),
        ("state-node-current", "The current state."),
        ("start-node", "The circle of a start state."),
        ("end-node", "The outer circle of an end state."),
        ("decision-node", "The diamond of a decision state."),
        ("transition-edge", "Each transition line."),
        ("transition-label", "Each transition label."),
        ("swimlane", "Each lane background (swimlane mode)."),
        ("swimlane-label", "Each lane name (swimlane mode)."),
        ("detail-panel", "The inline detail panel."),
        ("a11y-list", "The disclosed definition list."),
        EMPTY_STATE_PART,
    ],
    css_properties=[
        ("--mj-current-state-pulse", "Duration of one pulse of the current-state ring (default 1.5s)."),
        ("--mj-color-info / --mj-color-info-surface", "Theme tokens for the current state."),
    ],
)


# ---------------------------------------------------------------------------
# mj-release-calendar
# ---------------------------------------------------------------------------

CALENDAR_EVENTS_JS = DAY_HELPER + _code(
    """
    const events = [
      { id: "freeze", name: "Code freeze", type: "freeze", startDate: day(-2), endDate: day(1) },
      { id: "demo", name: "Sprint 15 demo", type: "milestone", startDate: day(0) },
      { id: "r310", name: "v3.1.0 release", type: "release", startDate: day(2), description: "Payments and invoices." },
      { id: "api", name: "API v2 launch", type: "release", startDate: day(5) },
      { id: "docs", name: "Docs refresh", type: "milestone", startDate: day(5) },
      { id: "train", name: "Support training", type: "milestone", startDate: day(5) },
      { id: "dbm", name: "Database maintenance", type: "blackout", startDate: day(5) },
      { id: "eu", name: "EU data-centre move", type: "blackout", startDate: day(9), endDate: day(10) },
      { id: "offsite", name: "Team offsite", type: "holiday", startDate: day(16) },
      { id: "beta", name: "v3.2.0-beta", type: "release", startDate: day(18), description: "Early access beta for partners.", url: "#release-notes-3-2" }
    ]
    """
)

CALENDAR_BASIC_SCRIPT = CALENDAR_EVENTS_JS + _code(
    """
    document.getElementById("demo-calendar").data = { events: events }
    """
)

CALENDAR_WEEK_SCRIPT = CALENDAR_EVENTS_JS + _code(
    """
    document.getElementById("week-calendar").data = { events: events }
    """
)

CALENDAR_INLINE_HTML = _code(
    """
    <mj-release-calendar current-date="2026-05-01" today-marker="false" locale="en-GB">
      <script type="application/json">
      {
        "events": [
          { "id": "ev1", "name": "v3.1.0 release", "type": "release", "startDate": "2026-05-08" },
          { "id": "ev2", "name": "Code freeze", "type": "freeze", "startDate": "2026-05-05", "endDate": "2026-05-08" },
          { "id": "ev3", "name": "EU downtime", "type": "blackout", "start": "2026-05-20", "end": "2026-05-21" },
          { "id": "ev4", "name": "Sprint 15 demo", "type": "milestone", "startDate": "2026-05-15" },
          { "id": "ev5", "name": "Company holiday", "type": "holiday", "startDate": "2026-05-25" },
          { "id": "ev6", "name": "Partner webinar", "type": "webinar", "startDate": "2026-05-28" }
        ]
      }
      </script>
    </mj-release-calendar>
    """
)

CALENDAR_STATES_HTML = _code(
    """
    <div class="stack">
      <mj-release-calendar id="empty-calendar">
        <span slot="empty">No releases planned yet.</span>
      </mj-release-calendar>
      <p class="stack-caption">Malformed inline JSON: the error shows above the grid and <code>mj-error</code> is emitted.</p>
      <mj-release-calendar id="broken-calendar">
        <script type="application/json">{ "events": [ { "name": "Launch", "startDate": } ] }</script>
      </mj-release-calendar>
    </div>
    """
)

CALENDAR_EVENTS_HTML = _code(
    """
    <mj-release-calendar id="event-calendar">
      <p slot="event-detail"><a href="#change-calendar">Open in the change calendar</a></p>
    </mj-release-calendar>
    """
)

CALENDAR_EVENTS_SCRIPT = CALENDAR_EVENTS_JS + PAUSE_HELPER + _code(
    """
    const calendar = document.getElementById("event-calendar")
    calendar.data = { events: events }
    const root = calendar.shadowRoot
    calendar.addEventListener("mj-period-change", (event) => mjSandbox.log("period", event.detail))

    await pause(400)
    root.querySelector(".next-btn").click()
    await pause(600)
    root.querySelector(".today-btn").click()
    await pause(600)
    root.querySelector(".view-btn[data-view=week]").click()
    await pause(600)
    root.querySelector(".view-btn[data-view=month]").click()
    await pause(400)
    /* Today's demo (events[1]) is always in the month that Today showed. */
    root.querySelector(`.day-cell[data-day="${day(0)}"] .event-chip[data-event-index="1"]`).click()
    await pause(900)
    root.querySelector("[part=detail-popover]").dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true, composed: true }))
    """
)

RELEASE_CALENDAR = ComponentDoc(
    tag="mj-release-calendar",
    title="Release Calendar",
    group="charts",
    summary="Month or week calendar grid of releases, freezes, blackouts, milestones and holidays shown as event chips.",
    description=(
        "<p><code>&lt;mj-release-calendar&gt;</code> renders a navigable "
        "calendar (a CSS grid with ARIA grid semantics) and puts each event "
        "on the days it covers as a coloured chip with an icon: "
        "<em>release</em> (green rocket), <em>freeze</em> (amber snowflake), "
        "<em>blackout</em> (red stop), <em>milestone</em> (blue diamond), "
        "<em>holiday</em> (muted calendar); other types use the milestone "
        "style and show their type as given. A multi-day event repeats on "
        "every day it covers. A month cell shows up to three chips and a "
        "&ldquo;+N more&rdquo; button; a week cell up to eight. Today's cell is "
        "highlighted.</p>"
        "<p>The header has previous / next buttons, a Today button, a Month / "
        "Week switch and a button that discloses an ordered list of all "
        "events. Activating a chip opens the detail panel below the grid with "
        "the type, dates, description and (for a safe <code>url</code>) a "
        "link that opens in a new tab. Names, weekdays and dates are "
        "formatted for <code>locale</code>.</p>"
        "<p>Keyboard: one day cell is in the tab order; arrow keys move a day "
        "or a week, Home / End go to the start / end of the week, Page Up / "
        "Page Down move a month, Tab reaches the focused day's chips and Enter "
        "lists all of that day's events. Escape closes the panel and returns "
        "focus.</p>"
        "<p>Data comes from the <code>data</code> property, a <code>src</code> "
        "URL or an inline JSON child. Without events the grid stays (it can "
        "still be navigated) and a status block above it says so: the "
        "<code>empty</code> slot, a loading message while a <code>src</code> "
        "is fetched, or the error when the data could not be loaded or is not "
        "an object (also emitted as <code>mj-error</code>).</p>"
        + DATES_HTML
    ),
    how_to_use=(
        "<p>Assign <code>{ events: [{ id, name, type, startDate, endDate, "
        "description, url }] }</code> (<code>start</code> / <code>end</code> "
        "are accepted as aliases; an event without a usable start appears "
        "only in the list). The calendar opens on today's month unless "
        "<code>current-date</code> names another day; <code>view</code>, "
        "<code>first-day-of-week</code> and <code>locale</code> shape the "
        "grid.</p>"
        "<p>Navigation by the user (arrows, Today, the view switch, paging "
        "the focus out of the period) emits <code>mj-period-change</code> "
        "with local <code>YYYY-MM-DD</code> dates; attribute changes update "
        "the grid without events.</p>"
    ),
    example="",
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>Events around today: a freeze spanning today, a demo today, "
                "a release in two days, a day with four events (&ldquo;+1 "
                "more&rdquo;), a two-day blackout and a beta with a link. Click "
                "a chip for its details.</p>"
            ),
            html='<mj-release-calendar id="demo-calendar"></mj-release-calendar>\n',
            script=CALENDAR_BASIC_SCRIPT,
        ),
        ComponentExample(
            key="week",
            title="Week view, Monday start, German",
            description=(
                "<p><code>view=\"week\"</code>, <code>first-day-of-week=\"1\"</code> "
                "and <code>locale=\"de-DE\"</code>: one week with up to eight "
                "chips per day and German weekday and month names.</p>"
            ),
            html='<mj-release-calendar id="week-calendar" view="week" first-day-of-week="1" locale="de-DE"></mj-release-calendar>\n',
            script=CALENDAR_WEEK_SCRIPT,
        ),
        ComponentExample(
            key="inline-json",
            title="Inline JSON on a fixed month",
            description=(
                "<p>Inline JSON for May 2026 with <code>current-date</code>, "
                "<code>today-marker=\"false\"</code>, "
                "<code>locale=\"en-GB\"</code>, the <code>start</code> / "
                "<code>end</code> aliases and an unknown <code>webinar</code> "
                "type.</p>"
            ),
            html=CALENDAR_INLINE_HTML,
        ),
        ComponentExample(
            key="states",
            title="Empty calendar and invalid data",
            description=(
                "<p>Without events the grid stays navigable and the status "
                "block above it shows the <code>empty</code> slot. Malformed "
                "inline JSON shows the parser error there (it stays while you "
                "page through months) and emits <code>mj-error</code>.</p>"
            ),
            html=CALENDAR_STATES_HTML,
            css=STACK_CSS,
        ),
        ComponentExample(
            key="events",
            title="Navigation and selection events",
            description=(
                "<p>The script pages to next month and back with Today "
                "(<code>mj-period-change</code>), switches to week and back "
                "(<code>mj-view-change</code>), opens today's demo "
                "(<code>mj-event-select</code>, with the <code>event-detail</code> "
                "slot link) and closes it with Escape "
                "(<code>mj-event-deselect</code>).</p>"
            ),
            html=CALENDAR_EVENTS_HTML,
            script=CALENDAR_EVENTS_SCRIPT,
        ),
    ],
    attributes=[
        AttributeDoc(name="view", description="Month grid or a single week.", kind="enum", values=["month", "week"], default="month"),
        AttributeDoc(name="current-date", description="`YYYY-MM-DD` (local day) of the period to show; defaults to today.", kind="string"),
        _today_attribute("Highlight of today's cell."),
        AttributeDoc(name="first-day-of-week", description="First column of the week: 0 = Sunday ... 6 = Saturday.", kind="enum", values=["0", "1", "2", "3", "4", "5", "6"], default="0"),
        AttributeDoc(name="locale", description="BCP 47 tag for weekday, month and date formatting; an invalid tag falls back to the library locale.", kind="string", values=["en-US", "en-GB", "de-DE", "fr-FR", "ja-JP"]),
        _src_attribute("events"),
    ],
    events=[
        ("mj-event-select", "An event chip (or an entry of a day's list) was activated; the detail panel opens.", "{ event: object }"),
        ("mj-event-deselect", "The event detail panel was closed.", "{}"),
        ("mj-period-change", "The user moved to another period (previous / next, Today, view switch, keyboard paging).", "{ start: string, end: string, view: 'month' | 'week' }"),
        ("mj-view-change", "The Month / Week switch changed the view.", "{ view: 'month' | 'week' }"),
        ("mj-data-load", "Data was assigned (or loaded) and drawn.", "{ events: number }"),
        ERROR_EVENT,
    ],
    slots=[
        ("event-detail", "Extra content below the details of the selected event.", '<p><a href="#change-calendar">Open in the change calendar</a></p>'),
        EMPTY_SLOT,
        FALLBACK_SLOT,
    ],
    properties=[
        _data_property("{ events }"),
        ("selectedEvent", "object | null. Read-only. The selected event object from the data."),
        ("visiblePeriod", "{ start: Date, end: Date }. Read-only. Local-midnight first and last day of the shown period."),
    ],
    methods=[],
    parts=[
        ("wrapper", "Outer region."),
        ("nav-controls", "The header with navigation, view switch and list button."),
        ("view-switcher", "The Month / Week button group."),
        ("calendar-grid", "The day grid (role grid)."),
        ("day-cell", "Each day cell (role gridcell)."),
        ("today-cell", "Today's cell (in addition to day-cell)."),
        ("event-chip", "Each event chip."),
        ("event-icon", "The name inside a chip."),
        ("more-events", "The +N more button of a full day."),
        ("detail-popover", "The detail panel below the grid."),
        ("a11y-list", "The disclosed ordered list of events."),
        EMPTY_STATE_PART,
    ],
    css_properties=[
        ("--mj-color-success / --mj-color-warning / --mj-color-danger / --mj-color-info (and their -surface tokens)", "Theme tokens for release, freeze, blackout and milestone chips."),
        ("--mj-color-info-surface", "Theme token for today's cell."),
    ],
)


# ---------------------------------------------------------------------------
# mj-env-promotion-chart
# ---------------------------------------------------------------------------

ENV_BASIC_SCRIPT = HOURS_AGO_HELPER + _code(
    """
    const chart = document.getElementById("demo-promotion")
    chart.data = {
      environments: [
        { id: "dev", name: "Dev", version: "v3.2.1-sha.abc123", health: "healthy", lastPromotion: hoursAgo(2) },
        { id: "staging", name: "Staging", version: "v3.2.0", health: "degraded", lastPromotion: hoursAgo(30) },
        { id: "prod", name: "Production", version: "v3.1.5", health: "healthy", lastPromotion: hoursAgo(240) }
      ],
      gates: [
        { fromEnv: "dev", status: "approved", name: "QA" },
        { fromEnv: "staging", status: "pending", name: "Change board" }
      ]
    }
    """
)

ENV_INLINE_HTML = _code(
    """
    <mj-env-promotion-chart artifact-id="search-indexer">
      <script type="application/json">
      {
        "environments": [
          { "id": "dev", "name": "Dev", "version": "v8.4.0-rc.3", "health": "healthy" },
          { "id": "qa", "name": "QA", "version": "v8.4.0-rc.2", "health": "degraded" },
          { "id": "staging", "name": "Staging", "version": "v8.3.9", "health": "down" },
          { "id": "perf", "name": "Performance lab", "version": "v8.3.9", "health": "unknown" },
          { "id": "prod", "name": "Production", "version": "v8.3.7", "health": "healthy" }
        ],
        "gates": [
          { "fromEnv": "dev", "status": "auto" },
          { "fromEnv": "qa", "status": "rejected", "name": "Security review" },
          { "fromEnv": "perf", "status": "approved", "name": "CAB" }
        ],
        "promotions": [
          { "environment": "qa", "version": "v8.4.0-rc.2", "at": "2026-05-18T14:30:00Z" },
          { "environment": "prod", "version": "v8.3.7", "at": "2026-05-02T09:00:00Z" }
        ]
      }
      </script>
    </mj-env-promotion-chart>
    """
)

ENV_VERTICAL_SCRIPT = HOURS_AGO_HELPER + _code(
    """
    document.getElementById("vertical-promotion").data = {
      environments: [
        { id: "canary", name: "Canary", version: "v12.0.0", health: "healthy", lastPromotion: hoursAgo(1) },
        { id: "eu", name: "EU region", version: "v11.9.2", health: "healthy", lastPromotion: hoursAgo(50) },
        { id: "us", name: "US region", version: "v11.9.2", health: "degraded", lastPromotion: hoursAgo(52) }
      ],
      gates: [
        { fromEnv: "canary", status: "pending", name: "Error budget" },
        { fromEnv: "eu", status: "auto" }
      ]
    }
    """
)

ENV_STATES_HTML = _code(
    """
    <div class="stack">
      <mj-env-promotion-chart id="empty-promotion" artifact-id="new-service">
        <span slot="empty">This artifact has not been deployed anywhere yet.</span>
      </mj-env-promotion-chart>
      <p class="stack-caption">Malformed inline JSON:</p>
      <mj-env-promotion-chart id="broken-promotion">
        <script type="application/json">{ "environments": [ { "id": "dev", "health": healthy } ] }</script>
      </mj-env-promotion-chart>
    </div>
    """
)

ENV_EVENTS_SCRIPT = HOURS_AGO_HELPER + PAUSE_HELPER + CLICK_HELPER + _code(
    """
    const chart = document.getElementById("event-promotion")
    chart.data = {
      environments: [
        { id: "staging", name: "Staging", version: "v2.0.0", health: "healthy", lastPromotion: hoursAgo(5) },
        { id: "prod", name: "Production", version: "v1.9.4", health: "healthy", lastPromotion: hoursAgo(100) }
      ],
      gates: [{ fromEnv: "staging", status: "pending", name: "Release manager" }]
    }

    /* The first decision is handled by the host: cancel it and keep the gate pending. */
    let handledByHost = false
    chart.addEventListener("mj-gate-action", (event) => {
      if (handledByHost === false) {
        handledByHost = true
        event.preventDefault()
        mjSandbox.log("host handles", event.detail)
      }
    })

    await pause(400)
    clickMark(chart, "env:0")
    await pause(800)
    chart.shadowRoot.querySelector("[part=environment-detail] .detail-close").click()
    await pause(400)
    chart.shadowRoot.querySelector(".gate-reject").click()
    await pause(700)
    chart.shadowRoot.querySelector(".gate-approve").click()
    mjSandbox.log("pending gates", chart.pendingGates.length)
    """
)

ENV_LIVE_SCRIPT = HOURS_AGO_HELPER + _code(
    """
    const chart = document.getElementById("live-promotion")
    let build = 41
    const draw = () => {
      chart.data = {
        environments: [
          { id: "dev", name: "Dev", version: "v5.0." + build, health: build % 3 === 0 ? "degraded" : "healthy", lastPromotion: new Date().toISOString() },
          { id: "staging", name: "Staging", version: "v5.0." + (build - build % 2), health: "healthy", lastPromotion: hoursAgo(6) },
          { id: "prod", name: "Production", version: "v4.9.12", health: "healthy", lastPromotion: hoursAgo(72) }
        ],
        gates: [{ fromEnv: "dev", status: "auto" }, { fromEnv: "staging", status: "pending" }]
      }
    }
    draw()

    /* With live set the chart emits mj-poll-tick every poll-interval (at least 5 s);
       the host answers with fresh data and a changed version emits mj-promotion-update. */
    chart.addEventListener("mj-poll-tick", () => {
      build = build + 1
      draw()
    })
    """
)

ENV_PROMOTION_CHART = ComponentDoc(
    tag="mj-env-promotion-chart",
    title="Environment Promotion Chart",
    group="charts",
    summary="Artifact promotion track showing version, health and last promotion per environment, with approval gates and live polling.",
    description=(
        "<p><code>&lt;mj-env-promotion-chart&gt;</code> lays out environment "
        "cards in promotion order (Dev &rarr; Staging &rarr; Production, "
        "&hellip;). Each card shows the deployed version, a health indicator "
        "(<code>healthy</code>, <code>degraded</code>, <code>down</code>, "
        "<code>unknown</code>) and when it was last promoted (from "
        "<code>lastPromotion</code> or the newest matching record in "
        "<code>promotions</code>). Between two cards sits the gate whose "
        "<code>fromEnv</code> is the left card &mdash; a diamond with its "
        "status in text (<code>pending</code>, <code>approved</code>, "
        "<code>rejected</code>, <code>auto</code>) &mdash; or a plain arrow "
        "when there is none.</p>"
        "<p>A pending gate offers Approve and Reject unless "
        "<code>readonly</code>. A decision emits the cancelable "
        "<code>mj-gate-action</code>; if the host does not cancel it the gate "
        "shows the new status, <code>mj-gate-change</code> fires, focus moves "
        "to the gate and the outcome is announced. The host's data object is "
        "never modified. Cards and gates are marks: activating one opens an "
        "inline detail panel.</p>"
        "<p>With <code>live</code> the chart shows a Live badge and every "
        "<code>poll-interval</code> it refetches <code>src</code> or, without "
        "one, emits <code>mj-poll-tick</code> so the host can assign fresh "
        "data; a changed version emits <code>mj-promotion-update</code>.</p>"
        + DATA_SOURCES_HTML + MARKS_HTML
    ),
    how_to_use=(
        "<p>Assign <code>{ environments, gates, promotions }</code>: each "
        "environment <code>{ id, name, version, health, lastPromotion }</code>, "
        "each gate <code>{ fromEnv, status, name }</code>, each promotion "
        "<code>{ environment, version, at }</code>. Set "
        "<code>artifact-id</code> to name the artifact in the header and "
        "<code>actor</code> to the signed-in user so decisions carry it. To "
        "decide on the server, call <code>event.preventDefault()</code> in "
        "<code>mj-gate-action</code> and assign the new data when it is "
        "done.</p>"
    ),
    example="",
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>Three environments, an approved QA gate and a pending change "
                "board gate with Approve / Reject buttons. Click a card for its "
                "details.</p>"
            ),
            html='<mj-env-promotion-chart id="demo-promotion" artifact-id="checkout-service" actor="alice"></mj-env-promotion-chart>\n',
            script=ENV_BASIC_SCRIPT,
        ),
        ComponentExample(
            key="inline-json",
            title="Every health and gate state (inline JSON)",
            description=(
                "<p>Inline JSON with healthy, degraded, down and unknown "
                "environments, auto, rejected and approved gates, a missing gate "
                "(plain arrow) and last-promotion times taken from "
                "<code>promotions</code>.</p>"
            ),
            html=ENV_INLINE_HTML,
        ),
        ComponentExample(
            key="vertical",
            title="Vertical, compact, read-only",
            description=(
                "<p><code>orientation=\"vertical\"</code>, "
                "<code>density=\"compact\"</code> (health as icon only, no "
                "promotion time) and <code>readonly</code>: the pending gate has "
                "no buttons.</p>"
            ),
            html='<mj-env-promotion-chart id="vertical-promotion" orientation="vertical" density="compact" readonly artifact-id="edge-proxy"></mj-env-promotion-chart>\n',
            script=ENV_VERTICAL_SCRIPT,
        ),
        ComponentExample(
            key="states",
            title="Empty and error states",
            description=(
                "<p>No data shows the <code>empty</code> slot; inline JSON with "
                "an unquoted value shows the parser error and emits "
                "<code>mj-error</code>.</p>"
            ),
            html=ENV_STATES_HTML,
            css=STACK_CSS,
        ),
        ComponentExample(
            key="events",
            title="Gate decisions and events",
            description=(
                "<p>The script opens Staging "
                "(<code>mj-environment-select</code> / <code>-deselect</code>), "
                "presses Reject (the host cancels <code>mj-gate-action</code>, the "
                "gate stays pending) and then Approve (<code>mj-gate-change</code> "
                "with <code>actor</code>).</p>"
            ),
            html='<mj-env-promotion-chart id="event-promotion" artifact-id="api-gateway" actor="release-bot"></mj-env-promotion-chart>\n',
            script=ENV_EVENTS_SCRIPT,
        ),
        ComponentExample(
            key="live",
            title="Live polling",
            description=(
                "<p><code>live</code> with <code>poll-interval=\"5000\"</code>: "
                "every 5 seconds the chart emits <code>mj-poll-tick</code>, the "
                "script assigns a new Dev build and the chart emits "
                "<code>mj-promotion-update</code>.</p>"
            ),
            html='<mj-env-promotion-chart id="live-promotion" artifact-id="web-frontend" live poll-interval="5000"></mj-env-promotion-chart>\n',
            script=ENV_LIVE_SCRIPT,
        ),
    ],
    attributes=[
        AttributeDoc(name="orientation", description="Lay the track out left to right or top to bottom.", kind="enum", values=["horizontal", "vertical"], default="horizontal"),
        AttributeDoc(name="density", description="`compact` shows health as an icon only and hides the last-promotion line.", kind="enum", values=DENSITY_VALUES, default="normal"),
        AttributeDoc(name="readonly", description="Pending gates show no Approve / Reject buttons.", kind="boolean"),
        AttributeDoc(name="live", description="Show the Live badge and poll every `poll-interval`: refetch `src`, or emit `mj-poll-tick`.", kind="boolean"),
        AttributeDoc(name="poll-interval", description="Polling period in milliseconds while `live` (minimum 5000).", kind="number", default="30000"),
        AttributeDoc(name="artifact-id", description="Name of the promoted artifact, shown in the header and the summary.", kind="string"),
        AttributeDoc(name="actor", description="Who decides: passed in `mj-gate-action` and `mj-gate-change` (read when a decision is made).", kind="string"),
        _src_attribute("environments, gates and promotions"),
    ],
    events=[
        ("mj-environment-select", "An environment card was activated; the detail panel opens.", "{ environment: object }"),
        ("mj-environment-deselect", "The environment detail panel was closed.", "{}"),
        ("mj-gate-select", "A gate was activated; the detail panel opens.", "{ gate: object }"),
        ("mj-gate-deselect", "The gate detail panel was closed.", "{}"),
        ("mj-gate-action", "Cancelable. Approve or Reject was pressed; `preventDefault()` keeps the gate pending.", "{ gate: object, action: 'approve' | 'reject', actor: string }"),
        ("mj-gate-change", "A decision was applied in the chart.", "{ gate: object, status: 'approved' | 'rejected', actor: string }"),
        ("mj-promotion-update", "Live mode: newly assigned data has a different version in an environment.", "{ environment: object, version: string }"),
        ("mj-poll-tick", "Live mode without `src`: time to assign fresh data.", "{}"),
        ("mj-data-load", "Data was assigned (or loaded) and drawn.", "{ environments: number, pendingGates: number }"),
        ("mj-error", "Declared data could not be fetched or parsed, or a live refetch of `src` failed.", "{ message: string }"),
    ],
    slots=[
        ("environment-detail", "Extra content below the details of the selected environment or gate.", '<p><a href="#deployments">Deployment history</a></p>'),
        EMPTY_SLOT,
        FALLBACK_SLOT,
    ],
    properties=[
        _data_property("{ environments, gates, promotions }"),
        ("selectedEnvironment", "object | null. Read-only. The selected environment object from the data."),
        ("selectedGate", "object | null. Read-only. The selected gate object from the data."),
        ("pendingGates", "object[]. Read-only. The gate objects that are still pending (decisions made in the chart count)."),
    ],
    methods=[],
    parts=[
        ("wrapper", "Outer region; its aria-label states the artifact, environments and pending gates."),
        ("live-indicator", "The Live badge."),
        ("env-track", "The track of cards and gates."),
        ("environment-column", "Each environment card (role button)."),
        ("environment-header", "The environment name."),
        ("version-badge", "The version."),
        ("health-indicator", "The health icon and text."),
        ("promoted-at", "The last-promotion line."),
        ("gate-node", "Each gate diamond."),
        ("gate-status", "Each gate status text."),
        ("gate-controls", "The Approve / Reject buttons of a pending gate."),
        ("environment-detail", "The inline detail panel."),
        ("a11y-list", "The disclosed summary list."),
        EMPTY_STATE_PART,
    ],
    css_properties=[
        ("--mj-color-success / --mj-color-warning / --mj-color-danger", "Theme tokens for health and gate colours."),
        ("--mj-font-mono", "Theme token for the version badge."),
    ],
)


# ---------------------------------------------------------------------------
# mj-build-status-board
# ---------------------------------------------------------------------------

BOARD_BASIC_SCRIPT = HOURS_AGO_HELPER + _code(
    """
    const board = document.getElementById("demo-board")
    board.data = {
      rows: [
        { id: "r1", name: "main / build", status: "passed", deployTarget: "staging", lastRun: hoursAgo(0.5), duration: 132, actor: "alice" },
        { id: "r2", name: "main / deploy", status: "running", deployTarget: "staging", lastRun: hoursAgo(0.2), duration: 0, actor: "ci-bot" },
        { id: "r3", name: "feat/auth / build", status: "failed", deployTarget: "", lastRun: hoursAgo(1.5), duration: 74, actor: "carol" },
        { id: "r4", name: "hotfix / build", status: "passed", deployTarget: "prod", lastRun: hoursAgo(11), duration: 98, actor: "bob" },
        { id: "r5", name: "hotfix / deploy", status: "passed", deployTarget: "prod", lastRun: hoursAgo(10.9), duration: 45, actor: "bob" },
        { id: "r6", name: "nightly / test", status: "cancelled", deployTarget: "", lastRun: hoursAgo(7), duration: 0, actor: "cron" }
      ]
    }
    """
)

BOARD_INLINE_HTML = _code(
    """
    <mj-build-status-board group-by="deployTarget" page-size="6" sort-column="duration" sort-direction="asc" density="compact">
      <script type="application/json">
      {
        "rows": [
          { "id": "b1", "name": "web / build", "status": "passed", "deployTarget": "staging", "lastRun": "2026-05-22T08:10:00Z", "duration": 132, "actor": "alice", "url": "#runs/b1" },
          { "id": "b2", "name": "web / deploy", "status": "passed", "deployTarget": "staging", "lastRun": "2026-05-22T08:14:00Z", "duration": 61, "actor": "ci-bot" },
          { "id": "b3", "name": "api / build", "status": "failed", "deployTarget": "staging", "lastRun": "2026-05-22T07:55:00Z", "duration": 74, "actor": "carol" },
          { "id": "b4", "name": "api / migrate", "status": "skipped", "deployTarget": "staging", "lastRun": "2026-05-22T07:56:00Z", "duration": 0, "actor": "ci-bot" },
          { "id": "b5", "name": "web / release", "status": "passed", "deployTarget": "prod", "lastRun": "2026-05-21T22:00:00Z", "duration": 3725, "actor": "bob" },
          { "id": "b6", "name": "api / release", "status": "pending", "deployTarget": "prod", "lastRun": "2026-05-21T22:05:00Z", "duration": 0, "actor": "bob" },
          { "id": "b7", "name": "docs / publish", "status": "queued", "deployTarget": "", "lastRun": "2026-05-22T09:00:00Z", "duration": 0, "actor": "dana" },
          { "id": "b8", "name": "nightly / e2e", "status": "cancelled", "deployTarget": "", "lastRun": "2026-05-22T02:00:00Z", "duration": 980, "actor": "cron" },
          { "id": "b9", "name": "nightly / load test", "status": "passed", "deployTarget": "", "lastRun": "2026-05-22T03:00:00Z", "duration": 1500, "actor": "cron" }
        ]
      }
      </script>
    </mj-build-status-board>
    """
)

BOARD_EVENTS_HTML = _code(
    """
    <mj-build-status-board id="event-board">
      <span slot="bulk-actions" class="bulk-actions">
        <button type="button" data-action="rerun">Re-run selected</button>
        <button type="button" data-action="cancel">Cancel selected</button>
      </span>
    </mj-build-status-board>
    """
)

BOARD_EVENTS_CSS = _code(
    """
    .bulk-actions { display: inline-flex; gap: var(--mj-space-2); }
    .bulk-actions button { font: inherit; font-size: var(--mj-font-size-xs); padding: 2px var(--mj-space-2); border: 1px solid var(--mj-border-strong); border-radius: var(--mj-radius-sm); background: var(--mj-surface); color: var(--mj-text); cursor: pointer; }
    """
)

BOARD_EVENTS_SCRIPT = HOURS_AGO_HELPER + PAUSE_HELPER + _code(
    """
    const board = document.getElementById("event-board")
    board.data = {
      rows: [
        { id: "e1", name: "app / build", status: "failed", deployTarget: "staging", lastRun: hoursAgo(1), duration: 88, actor: "alice" },
        { id: "e2", name: "app / test", status: "failed", deployTarget: "staging", lastRun: hoursAgo(0.9), duration: 240, actor: "alice" },
        { id: "e3", name: "app / deploy", status: "pending", deployTarget: "staging", lastRun: hoursAgo(0.8), duration: 0, actor: "ci-bot" },
        { id: "e4", name: "lib / build", status: "passed", deployTarget: "", lastRun: hoursAgo(3), duration: 51, actor: "bob" }
      ]
    }
    const root = board.shadowRoot

    /* The bulk-action buttons act on board.selectedRows. */
    for (const button of board.querySelectorAll("[data-action]")) {
      button.addEventListener("click", () => {
        const next = button.getAttribute("data-action") === "rerun" ? "running" : "cancelled"
        for (const rowId of Array.from(board.selectedRows)) {
          board.updateRowStatus(rowId, next)
        }
      })
    }

    await pause(400)
    root.querySelector("th[data-col=status] .sort-btn").click()
    await pause(500)
    const failed = root.querySelectorAll("tr[data-status=failed] input[type=checkbox]")
    failed[0].click()
    failed[1].click()
    await pause(700)
    board.querySelector("[data-action=rerun]").click()
    await pause(700)
    const filter = root.querySelector(".filter-status")
    filter.value = "running"
    filter.dispatchEvent(new Event("change"))
    await pause(700)
    root.querySelector(".clear-filters-btn").click()
    root.querySelector("tr[data-row-id=e4] .pipeline-link").click()
    """
)

BOARD_STATES_HTML = _code(
    """
    <div class="stack">
      <mj-build-status-board id="empty-board">
        <span slot="empty">No pipelines have run in this project.</span>
      </mj-build-status-board>
      <p class="stack-caption">Malformed inline JSON:</p>
      <mj-build-status-board id="broken-board">
        <script type="application/json">{ "rows": [ { "id": "x1", "status": "passed" }, ] }</script>
      </mj-build-status-board>
      <p class="stack-caption">Rows, but the status filter matches none of them:</p>
      <mj-build-status-board id="filtered-board" filter-status="cancelled">
        <script type="application/json">{ "rows": [ { "id": "w1", "name": "web / build", "status": "passed" }, { "id": "a1", "name": "api / build", "status": "failed" } ] }</script>
      </mj-build-status-board>
    </div>
    """
)

BOARD_LIVE_SCRIPT = HOURS_AGO_HELPER + _code(
    """
    const board = document.getElementById("live-board")
    const names = ["web / build", "web / test", "api / build", "api / test", "worker / build", "docs / publish"]
    board.data = {
      rows: names.map((name, index) => ({ id: "l" + index, name: name, status: index % 2 === 0 ? "running" : "passed", deployTarget: index < 4 ? "staging" : "", lastRun: hoursAgo(index * 0.3), duration: 60 + index * 15, actor: "ci-bot" }))
    }

    /* Each poll tick (every 5 s) one run finishes and another starts. */
    board.addEventListener("mj-poll-tick", () => {
      const running = board.data.rows.filter((row) => row.status === "running")
      const idle = board.data.rows.filter((row) => row.status !== "running")
      if (running.length > 0) {
        const done = running[Math.floor(Math.random() * running.length)]
        board.updateRowStatus(done.id, Math.random() < 0.75 ? "passed" : "failed")
      }
      if (idle.length > 0) {
        board.updateRowStatus(idle[Math.floor(Math.random() * idle.length)].id, "running")
      }
    })
    """
)

BUILD_STATUS_BOARD = ComponentDoc(
    tag="mj-build-status-board",
    title="Build Status Board",
    group="charts",
    summary="Sortable, filterable, groupable and paginated big-board table of pipeline runs with row selection, bulk actions and live polling.",
    description=(
        "<p><code>&lt;mj-build-status-board&gt;</code> lists CI/CD pipeline "
        "runs in a native table: a selection checkbox, the pipeline name (a "
        "link when the row has a <code>url</code>, otherwise a button that "
        "emits <code>mj-row-activate</code>), a status badge with icon and "
        "text, the deploy target, the last run time, the duration and the "
        "actor. Failed and running rows are tinted. Unknown statuses are "
        "shown, styled and filtered as &ldquo;Unknown&rdquo;.</p>"
        "<p>The column headers are sort buttons (<code>aria-sort</code>); the "
        "filter bar narrows by status and by a name substring and counts the "
        "results; <code>group-by</code> inserts a heading row per value; a "
        "pager splits the rows into pages of <code>page-size</code>. Selecting "
        "rows (or all filtered rows with the header checkbox) shows the bulk "
        "action bar with the <code>bulk-actions</code> slot. "
        "<code>updateRowStatus()</code> changes one row in place and "
        "announces it.</p>"
        "<p>With <code>live</code> the board shows a Live badge and emits "
        "<code>mj-poll-tick</code> every <code>poll-interval</code> so the "
        "host can refresh rows. With no data the empty state shows; when the "
        "board has rows but the filters match none it says that no pipeline "
        "matches the filters. Changing an attribute such as "
        "<code>density</code>, <code>group-by</code> or <code>page-size</code> "
        "keeps the sort and filters the user chose; only a change of a sort or "
        "filter attribute itself replaces them.</p>"
        + DATA_SOURCES_HTML
    ),
    how_to_use=(
        "<p>Assign <code>{ rows: [{ id, name, status, deployTarget, lastRun, "
        "duration, actor, url }] }</code>: <code>status</code> is one of "
        "pending, running, passed, failed, cancelled, skipped (anything else "
        "is Unknown), <code>lastRun</code> an ISO date-time and "
        "<code>duration</code> seconds. Initial sorting, filters, grouping and "
        "paging come from the attributes; the user can change sort and "
        "filters afterwards.</p>"
        "<p>Put buttons in the <code>bulk-actions</code> slot and act on "
        "<code>selectedRows</code>. For live boards set <code>live</code> and "
        "answer <code>mj-poll-tick</code> with "
        "<code>updateRowStatus()</code> or a new <code>data</code> object.</p>"
    ),
    example="",
    examples=[
        ComponentExample(
            key="basic",
            title="Basic usage",
            description=(
                "<p>Six recent runs sorted by last run, newest first. Click a "
                "column header to sort, use the filter bar, or tick rows to see "
                "the bulk bar.</p>"
            ),
            html='<mj-build-status-board id="demo-board" page-size="10"></mj-build-status-board>\n',
            script=BOARD_BASIC_SCRIPT,
        ),
        ComponentExample(
            key="inline-json",
            title="Grouped and paged, from inline JSON",
            description=(
                "<p>Inline JSON with nine runs, <code>group-by=\"deployTarget\"</code>, "
                "<code>page-size=\"6\"</code> (two pages), sorted by duration "
                "ascending, <code>density=\"compact\"</code>, a row with a link "
                "and a <code>queued</code> status shown as Unknown.</p>"
            ),
            html=BOARD_INLINE_HTML,
        ),
        ComponentExample(
            key="events",
            title="Bulk actions, status updates and events",
            description=(
                "<p>The script sorts by status (<code>mj-sort-change</code>), "
                "selects both failed runs (<code>mj-row-select</code>, "
                "<code>mj-selection-change</code>), re-runs them from the "
                "<code>bulk-actions</code> slot (<code>updateRowStatus()</code> "
                "&rarr; <code>mj-status-change</code>), filters and clears "
                "(<code>mj-filter-change</code>) and activates a name "
                "(<code>mj-row-activate</code>).</p>"
            ),
            html=BOARD_EVENTS_HTML,
            css=BOARD_EVENTS_CSS,
            script=BOARD_EVENTS_SCRIPT,
        ),
        ComponentExample(
            key="states",
            title="Empty and error states",
            description=(
                "<p>No data shows the <code>empty</code> slot; inline JSON with "
                "a trailing comma shows the parser error and emits "
                "<code>mj-error</code>. The third board has rows but "
                "<code>filter-status=\"cancelled\"</code> matches none: it says "
                "so instead of &ldquo;No data&rdquo;; Clear filters brings the "
                "rows back.</p>"
            ),
            html=BOARD_STATES_HTML,
            css=STACK_CSS,
        ),
        ComponentExample(
            key="live",
            title="Live polling",
            description=(
                "<p><code>live</code> with <code>poll-interval=\"5000\"</code>: "
                "on every <code>mj-poll-tick</code> the script finishes one "
                "running build and starts another with "
                "<code>updateRowStatus()</code>.</p>"
            ),
            html='<mj-build-status-board id="live-board" live poll-interval="5000"></mj-build-status-board>\n',
            script=BOARD_LIVE_SCRIPT,
        ),
    ],
    attributes=[
        AttributeDoc(name="group-by", description="Column whose value groups the rows under heading rows.", kind="enum", values=["name", "status", "deployTarget", "actor"]),
        AttributeDoc(name="density", description="`compact` reduces the row padding.", kind="enum", values=DENSITY_VALUES, default="normal"),
        AttributeDoc(name="live", description="Show the Live badge and emit `mj-poll-tick` every `poll-interval`.", kind="boolean"),
        AttributeDoc(name="poll-interval", description="Polling period in milliseconds while `live` (minimum 5000).", kind="number", default="30000"),
        AttributeDoc(name="filter-status", description="Initial status filter.", kind="enum", values=["pending", "running", "passed", "failed", "cancelled", "skipped", "unknown"]),
        AttributeDoc(name="filter-pattern", description="Initial name filter (case-insensitive substring).", kind="string"),
        AttributeDoc(name="page-size", description="Rows per page; 0 shows every row on one page.", kind="number", default="25"),
        AttributeDoc(name="sort-column", description="Initial sort column.", kind="enum", values=["name", "status", "deployTarget", "lastRun", "duration"], default="lastRun"),
        AttributeDoc(name="sort-direction", description="Initial sort direction.", kind="enum", values=["asc", "desc"], default="desc"),
        _src_attribute("rows"),
    ],
    events=[
        ("mj-row-select", "A row checkbox was toggled (the header checkbox emits only `mj-selection-change`).", "{ row: object, selected: boolean }"),
        ("mj-selection-change", "The set of selected rows changed.", "{ rows: object[], count: number }"),
        ("mj-row-activate", "A pipeline name (link or button) was activated.", "{ row: object }"),
        ("mj-sort-change", "A column header changed the sort.", "{ column: string, direction: 'asc' | 'desc' }"),
        ("mj-filter-change", "The user changed the status or name filter, or cleared them.", "{ status: string, pattern: string }"),
        ("mj-status-change", "`updateRowStatus()` changed a row.", "{ rowId: string, previous: string, current: string }"),
        ("mj-poll-tick", "Live mode: time to refresh the rows.", "{}"),
        ("mj-data-load", "Data was assigned (or loaded) and drawn.", "{ rows: number }"),
        ERROR_EVENT,
    ],
    slots=[
        ("bulk-actions", "Buttons shown in the bulk action bar while rows are selected.", '<button type="button">Re-run selected</button>'),
        EMPTY_SLOT,
        FALLBACK_SLOT,
    ],
    properties=[
        _data_property("{ rows }"),
        ("selectedRows", "Set<string>. Read-only. Ids of the selected rows (kept across data changes while the ids exist)."),
        ("filteredRows", "object[]. Read-only. The rows that pass the filters, in display order."),
    ],
    methods=[
        ("updateRowStatus(rowId, newStatus)", "Sets the status of one row (on the row object itself), re-renders, emits `mj-status-change` and announces the change."),
    ],
    parts=[
        ("wrapper", "Outer container."),
        ("live-indicator", "The Live badge."),
        ("filter-bar", "Status select, name filter, Clear button and result count."),
        ("table", "The native table."),
        ("caption", "The table caption with the row count."),
        ("header-row", "The header row."),
        ("header-cell", "Each column header."),
        ("table-body", "The table body."),
        ("data-row", "Each run row (`data-status`, `data-selected`)."),
        ("group-row", "Each group heading row."),
        ("check-cell", "Each selection cell."),
        ("status-cell", "Each status cell."),
        ("status-badge", "Each status badge."),
        ("duration-cell", "Each duration cell."),
        ("actor-cell", "Each actor cell."),
        ("bulk-action-bar", "The bulk action bar."),
        ("pagination", "The pager."),
        EMPTY_STATE_PART,
    ],
    css_properties=[
        ("--mj-color-danger-surface / --mj-color-info-surface", "Theme tokens for failed and running row tints."),
        ("--mj-accent", "Theme token for pipeline links and the selected-row bar."),
    ],
)


COMPONENTS = [
    BRANCH_GRAPH,
    PIPELINE_CHART,
    GANTT_CHART,
    ROADMAP_CHART,
    MILESTONE_TIMELINE,
    BURNDOWN_CHART,
    CUMULATIVE_FLOW,
    VELOCITY_CHART,
    DEPENDENCY_GRAPH,
    WORKFLOW_DIAGRAM,
    RELEASE_CALENDAR,
    ENV_PROMOTION_CHART,
    BUILD_STATUS_BOARD,
]
