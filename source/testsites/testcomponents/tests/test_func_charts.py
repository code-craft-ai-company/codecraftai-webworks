"""
    .. module:: testcomponents.tests.test_func_charts

    Functional Playwright tests for the 'charts' component group.

    Covers all 13 chart/diagram components:
      mj-branch-graph, mj-pipeline-chart, mj-gantt-chart,
      mj-roadmap-chart, mj-milestone-timeline, mj-burndown-chart,
      mj-cumulative-flow, mj-velocity-chart, mj-dependency-graph,
      mj-workflow-diagram, mj-release-calendar, mj-env-promotion-chart,
      mj-build-status-board.

    Each test navigates to /components/charts/<tag>, waits for the
    custom element to register inside the preview iframe, and then
    asserts the rendering and interactive behaviour described by each
    component's JS implementation.

    Background note on data initialization
    ---------------------------------------
    All chart components expose a `.data` setter that triggers a draw
    when the shadow DOM is ready.  The playground example <script> blocks
    run early and may assign `.data` before the custom element has
    upgraded, which silently creates an own property on the element that
    shadows the prototype getter/setter.  As a result the draw is never
    triggered.

    Each test that needs chart content calls `_force_draw(frame, tag)` to
    work around this: it reads the already-present data value, deletes
    the shadow-obscuring own property, and re-assigns via the prototype
    setter so the component's `_draw()` method is invoked properly.
"""

import json

import ccai.testbase as testbase

from testcomponents.harness.factories import create_page


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _open_chart(page, base_url: str, tag: str):
    """
        Navigate to the component playground page and return a ready Frame.

        Waits for the custom element to be registered inside the preview
        iframe before returning.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
        :param tag: The custom element tag name, e.g. 'mj-branch-graph'.

        :returns: The Playwright Frame inside the preview iframe.
    """

    page.goto(base_url + f"/components/charts/{tag}")
    handle = page.wait_for_selector("[data-testid=playground-preview]")
    frame = handle.content_frame()
    frame.wait_for_function(
        "tag => customElements.get(tag) !== undefined",
        arg=tag,
        timeout=15000,
    )
    # The example's script runs as a module after the upgrade and assigns the
    # data; wait for it so a test's own assignment is not overwritten later.
    frame.wait_for_function(
        "() => window.mjSandbox !== undefined && window.mjSandbox.ready === true",
        timeout=15000,
    )
    return frame


def _force_draw(frame, tag: str) -> None:
    """
        Re-trigger the component's draw by reassigning .data through the
        prototype setter.

        When a playground example script runs before the custom element
        upgrades, ``el.data = value`` sets a plain own property that
        shadows the prototype getter/setter.  This helper deletes that
        own property and re-assigns the value through the setter so the
        component's ``_draw()`` is called properly.

        :param frame: The Playwright Frame containing the element.
        :param tag: The host custom-element tag name.
    """

    frame.evaluate(
        """tag => {
            const el = document.querySelector(tag);
            if (el === null) { return; }
            if (!el.hasOwnProperty('data')) { return; }
            const saved = el.data;
            delete el.data;
            el.data = saved;
        }""",
        tag,
    )
    return


def _shadow_count(frame, tag: str, selector: str) -> int:
    """
        Count elements matching a CSS selector inside the shadow root.

        :param frame: The Playwright Frame containing the element.
        :param tag: The host custom-element tag name.
        :param selector: A CSS selector to query inside the shadow root.

        :returns: The number of matching elements.
    """

    count = frame.evaluate(
        """([tag, sel]) => {
            const el = document.querySelector(tag);
            if (el === null || el.shadowRoot === null) { return 0; }
            return el.shadowRoot.querySelectorAll(sel).length;
        }""",
        [tag, selector],
    )
    return count


def _shadow_exists(frame, tag: str, selector: str) -> bool:
    """
        Return True if at least one element matches inside the shadow root.

        :param frame: The Playwright Frame.
        :param tag: The host element tag.
        :param selector: CSS selector to look for.

        :returns: True when at least one match is found.
    """

    result = _shadow_count(frame, tag, selector)
    return result > 0


def _collect_events(frame, tag: str, event_names: list) -> None:
    """
        Install a window.__mjevents collector for the given event names.

        Must be called before the interaction that fires the events.
        Retrieve captured names via
        ``frame.evaluate('() => window.__mjevents')``.

        :param frame: The Playwright Frame.
        :param tag: The host element tag.
        :param event_names: A list of DOM event name strings to listen for.
    """

    listeners_js = ", ".join(f'"{n}"' for n in event_names)
    frame.evaluate(
        f"""() => {{
            window.__mjevents = [];
            const el = document.querySelector('{tag}');
            [{listeners_js}].forEach(n => {{
                el.addEventListener(n, () => window.__mjevents.push(n));
            }});
        }}"""
    )
    return


def _wait_for_shadow(frame, tag: str, selector: str, timeout: int = 10000) -> None:
    """
        Wait until at least one matching element exists in the shadow root.

        :param frame: The Playwright Frame.
        :param tag: The host element tag.
        :param selector: CSS selector to look for inside the shadow root.
        :param timeout: Maximum wait time in milliseconds.
    """

    frame.wait_for_function(
        """([tag, sel]) => {
            const el = document.querySelector(tag);
            if (el === null || el.shadowRoot === null) { return false; }
            return el.shadowRoot.querySelectorAll(sel).length > 0;
        }""",
        arg=[tag, selector],
        timeout=timeout,
    )
    return


# ---------------------------------------------------------------------------
# mj-branch-graph
# ---------------------------------------------------------------------------

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_branch_graph_svg_rendered(page, base_url):
    """
        mj-branch-graph renders an SVG in its shadow DOM.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-branch-graph")
    assert _shadow_exists(frame, "mj-branch-graph", "svg") is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_branch_graph_accessible_table_present(page, base_url):
    """
        mj-branch-graph always renders an accessible data table.

        The table is hidden by default; its presence in the shadow DOM is
        sufficient.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-branch-graph")
    assert _shadow_exists(frame, "mj-branch-graph", "table[part=data-table]") is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_branch_graph_commit_nodes_present(page, base_url):
    """
        mj-branch-graph renders one commit-node circle per commit.

        The example data contains 6 commits.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-branch-graph")
    _force_draw(frame, "mj-branch-graph")
    _wait_for_shadow(frame, "mj-branch-graph", "[part=commit-node]")

    count = _shadow_count(frame, "mj-branch-graph", "[part=commit-node]")
    assert count >= 6

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_branch_graph_merge_edge_rendered(page, base_url):
    """
        mj-branch-graph renders Bezier merge-edge paths between lanes.

        The example data has one merge, so at least one path with
        part='merge-edge' should be present.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-branch-graph")
    _force_draw(frame, "mj-branch-graph")
    _wait_for_shadow(frame, "mj-branch-graph", "[part=merge-edge]")

    assert _shadow_exists(frame, "mj-branch-graph", "[part=merge-edge]") is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_branch_graph_milestone_marker_rendered(page, base_url):
    """
        mj-branch-graph renders a milestone marker line for each marker entry.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-branch-graph")
    _force_draw(frame, "mj-branch-graph")
    _wait_for_shadow(frame, "mj-branch-graph", "[part=milestone-marker]")

    assert _shadow_exists(frame, "mj-branch-graph", "[part=milestone-marker]") is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_branch_graph_node_select_event(page, base_url):
    """
        Clicking a commit node fires the mj-node-select event.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-branch-graph")
    _force_draw(frame, "mj-branch-graph")
    _wait_for_shadow(frame, "mj-branch-graph", "[part=commit-node]")

    _collect_events(frame, "mj-branch-graph", ["mj-node-select"])

    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-branch-graph');
            const node = el.shadowRoot.querySelector('[part=commit-node]');
            if (node !== null) {
                node.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
            }
        }"""
    )

    events = frame.evaluate("() => window.__mjevents")
    assert "mj-node-select" in events

    return


_INJECTION = "x'\"><img src=\"data:,x\" onerror=\"top.__hits=(top.__hits||0)+1\">"

# ---------------------------------------------------------------------------
# Wrappers over <mj-chart> types (WW-1498): shared checks
# ---------------------------------------------------------------------------

_COMPARE_JS = """async ([markup]) => {
    document.body.innerHTML = markup;
    await new Promise((resolve) => setTimeout(resolve, 700));
    const describe = (element) => {
        const sr = element.shadowRoot;
        return {
            type: element.chartType,
            marks: Array.from(sr.querySelectorAll('[data-mark]')).map((mark) => [mark.getAttribute('data-mark'), mark.getAttribute('part'), mark.getAttribute('aria-label')]),
            rows: Array.from(sr.querySelectorAll('[data-chart-table] tbody tr')).map((row) => row.textContent),
            columns: Array.from(sr.querySelectorAll('[data-chart-table] thead th')).map((cell) => cell.textContent)
        };
    };
    const charts = Array.from(document.body.children);
    return { wrapper: describe(charts[0]), chart: describe(charts[1]) };
}"""


def _compare_with_chart(frame, wrapper_markup: str, chart_markup: str) -> dict:
    """
        Render a wrapper and the equivalent <mj-chart> side by side and
        describe what each drew: its marks (key, part and accessible name)
        and its data table.

        :param frame: The preview Frame.
        :param wrapper_markup: The wrapper element with inline JSON.
        :param chart_markup: The <mj-chart type="..."> element with inline JSON.

        :returns: { wrapper, chart } descriptions.
    """

    result = frame.evaluate(_COMPARE_JS, [wrapper_markup + chart_markup])
    return result


def _inline(tag: str, data: dict, attrs: str = "") -> str:
    """
        Markup of one element with inline JSON data and a fixed width.

        :param tag: The element markup name and type, e.g. ``mj-chart type="gantt"``.
        :param data: The JSON-serialisable data.
        :param attrs: Further attributes.

        :returns: The HTML string.
    """

    name = tag.split(" ")[0]
    markup = f'<{tag} {attrs} style="width:640px"><script type="application/json">{json.dumps(data)}</script></{name}>'
    return markup



@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_branch_graph_marks_exposed_and_roving(page, base_url):
    """
        The host is not forced to role=img, the marks sit in a labelled
        group with a single tab stop, and the arrow keys move between them.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-branch-graph")
    _force_draw(frame, "mj-branch-graph")
    _wait_for_shadow(frame, "mj-branch-graph", "[part=commit-node]")

    result = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-branch-graph');
            const sr = el.shadowRoot;
            const marks = Array.from(sr.querySelectorAll('[data-mark]'));
            marks[0].focus();
            marks[0].dispatchEvent(new KeyboardEvent('keydown', {key: 'ArrowRight', bubbles: true, composed: true}));
            return {
                hostRole: el.getAttribute('role'),
                svgRole: sr.querySelector('svg').getAttribute('role'),
                svgPart: sr.querySelector('svg').getAttribute('part'),
                tabStops: marks.filter((m) => m.getAttribute('tabindex') === '0').length,
                focused: sr.activeElement === marks[1],
                markers: sr.querySelectorAll('[part=milestone-marker][data-mark]').length
            };
        }"""
    )

    assert result["hostRole"] is None
    assert result["svgRole"] == "group"
    assert result["svgPart"] == "svg"
    assert result["tabStops"] == 1
    assert result["focused"] is True
    assert result["markers"] >= 1

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_branch_graph_single_commit_and_today_default(page, base_url):
    """
        One commit (or commits sharing a date) still yields a usable axis,
        same-day commits are spread apart, and the today line is drawn by
        default when today is inside the range.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-branch-graph")
    result = frame.evaluate(
        """async () => {
            const el = document.querySelector('mj-branch-graph');
            const day = (offset) => {
                const d = new Date(Date.now() + offset * 86400000);
                return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
            };
            el.data = { branches: [{ id: 'm', name: 'main' }], commits: [
                { id: 'a', branch: 'm', date: day(0), message: 'one' },
                { id: 'b', branch: 'm', date: day(0), message: 'two' }
            ] };
            await new Promise((r) => setTimeout(r, 50));
            const sr = el.shadowRoot;
            const xs = Array.from(sr.querySelectorAll('[part=commit-node]')).map((c) => Number(c.getAttribute('cx')));
            const ticks = Array.from(sr.querySelectorAll('.axis-tick')).map((t) => t.textContent);
            return { xs: xs, distinctTicks: new Set(ticks).size, ticks: ticks.length, today: sr.querySelectorAll('[part=today-marker]').length };
        }"""
    )

    assert len(result["xs"]) == 2
    assert abs(result["xs"][0] - result["xs"][1]) >= 10
    assert result["distinctTicks"] == result["ticks"]
    assert result["today"] == 1

    return


# ---------------------------------------------------------------------------
# mj-pipeline-chart
# ---------------------------------------------------------------------------

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_pipeline_chart_svg_rendered(page, base_url):
    """
        mj-pipeline-chart renders an SVG in its shadow DOM.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-pipeline-chart")
    assert _shadow_exists(frame, "mj-pipeline-chart", "svg") is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_pipeline_chart_accessible_list_present(page, base_url):
    """
        mj-pipeline-chart always renders an accessible ordered list.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-pipeline-chart")
    assert _shadow_exists(frame, "mj-pipeline-chart", "ol[part=a11y-list]") is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_pipeline_chart_stage_nodes_present(page, base_url):
    """
        mj-pipeline-chart renders one stage-node group per stage.

        The example data has 5 stages.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-pipeline-chart")
    _force_draw(frame, "mj-pipeline-chart")
    _wait_for_shadow(frame, "mj-pipeline-chart", "[part=stage-node]")

    count = _shadow_count(frame, "mj-pipeline-chart", "[part=stage-node]")
    assert count >= 5

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_pipeline_chart_gate_node_rendered(page, base_url):
    """
        mj-pipeline-chart renders a gate-node diamond for the example gate.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-pipeline-chart")
    _force_draw(frame, "mj-pipeline-chart")
    _wait_for_shadow(frame, "mj-pipeline-chart", "[part=gate-node]")

    assert _shadow_exists(frame, "mj-pipeline-chart", "[part=gate-node]") is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_pipeline_chart_stage_select_event(page, base_url):
    """
        Clicking a stage node fires the mj-stage-select event.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-pipeline-chart")
    _force_draw(frame, "mj-pipeline-chart")
    _wait_for_shadow(frame, "mj-pipeline-chart", "[part=stage-node]")

    _collect_events(frame, "mj-pipeline-chart", ["mj-stage-select"])

    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-pipeline-chart');
            const node = el.shadowRoot.querySelector('[part=stage-node]');
            if (node !== null) {
                node.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
            }
        }"""
    )

    events = frame.evaluate("() => window.__mjevents")
    assert "mj-stage-select" in events

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_pipeline_chart_data_escaped_and_parallel_layout(page, base_url):
    """
        Stage status and duration are escaped, and stages that run in
        parallel (build -> test and build -> lint) share a column.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-pipeline-chart")
    result = frame.evaluate(
        """async ([payload]) => {
            const el = document.querySelector('mj-pipeline-chart');
            el.data = {
                stages: [
                    { id: 'build', name: 'Build', status: 'passed', duration: payload },
                    { id: 'test', name: 'Test', status: payload },
                    { id: 'lint', name: 'Lint', status: 'passed' }
                ],
                gates: [{ name: payload, fromStage: 'build', status: payload }],
                edges: [{ from: 'build', to: 'test' }, { from: 'build', to: 'lint' }]
            };
            await new Promise((r) => setTimeout(r, 100));
            const sr = el.shadowRoot;
            const x = (id) => Number(sr.querySelector(`[data-mark="stage:${id}"] rect`).getAttribute('x'));
            return { hits: top.__hits === undefined ? 0 : top.__hits, images: sr.querySelectorAll('img').length, sameColumn: x(1) === x(2), wrapperRole: sr.querySelector('.wrapper').getAttribute('role') };
        }""",
        [_INJECTION],
    )

    assert result["hits"] == 0
    assert result["images"] == 0
    assert result["sameColumn"] is True
    assert result["wrapperRole"] == "group"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_pipeline_chart_log_panel_follows_selection(page, base_url):
    """
        Selecting a stage without logs hides the previous stage's logs and
        aria-expanded is true only on the stage whose logs are shown.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-pipeline-chart")
    _force_draw(frame, "mj-pipeline-chart")
    _wait_for_shadow(frame, "mj-pipeline-chart", "[part=stage-node]")

    result = frame.evaluate(
        """() => {
            const sr = document.querySelector('mj-pipeline-chart').shadowRoot;
            const stage = (i) => sr.querySelector(`[data-mark="stage:${i}"]`);
            stage(0).dispatchEvent(new MouseEvent('click', {bubbles: true}));
            const shownAfterBuild = sr.querySelector('.log-panel').hidden === false;
            stage(2).dispatchEvent(new MouseEvent('click', {bubbles: true}));
            return {
                shownAfterBuild: shownAfterBuild,
                hiddenAfterLint: sr.querySelector('.log-panel').hidden,
                expanded: [0, 1, 2].map((i) => stage(i).getAttribute('aria-expanded'))
            };
        }"""
    )

    assert result["shownAfterBuild"] is True
    assert result["hiddenAfterLint"] is True
    assert result["expanded"] == ["false", "false", "false"]

    return


# ---------------------------------------------------------------------------
# mj-gantt-chart
# ---------------------------------------------------------------------------

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_gantt_chart_svg_rendered(page, base_url):
    """
        mj-gantt-chart renders an SVG in its shadow DOM.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-gantt-chart")
    assert _shadow_exists(frame, "mj-gantt-chart", "svg") is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_gantt_chart_accessible_table_present(page, base_url):
    """
        mj-gantt-chart always includes a data table in the shadow DOM (the
        chart's table, part `table data-table`).

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-gantt-chart")
    assert _shadow_exists(frame, "mj-gantt-chart", "[part~=data-table] table") is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_gantt_chart_task_bars_present(page, base_url):
    """
        mj-gantt-chart renders task bars for all 6 tasks in the example.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-gantt-chart")
    _force_draw(frame, "mj-gantt-chart")
    _wait_for_shadow(frame, "mj-gantt-chart", "[part~=task-bar]")

    count = _shadow_count(frame, "mj-gantt-chart", "[part~=task-bar]")
    assert count >= 6

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_gantt_chart_dependency_arrows_present(page, base_url):
    """
        mj-gantt-chart renders dependency arrows between tasks.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-gantt-chart")
    _force_draw(frame, "mj-gantt-chart")
    _wait_for_shadow(frame, "mj-gantt-chart", "[part~=dependency-arrow]")

    assert _shadow_exists(frame, "mj-gantt-chart", "[part~=dependency-arrow]") is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_gantt_chart_task_select_event(page, base_url):
    """
        Clicking a task bar fires the mj-task-select event.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-gantt-chart")
    _force_draw(frame, "mj-gantt-chart")
    _wait_for_shadow(frame, "mj-gantt-chart", "[part~=task-bar]")

    _collect_events(frame, "mj-gantt-chart", ["mj-task-select"])

    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-gantt-chart');
            const bar = el.shadowRoot.querySelector('[part~=task-bar]');
            if (bar !== null) {
                bar.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
            }
        }"""
    )

    events = frame.evaluate("() => window.__mjevents")
    assert "mj-task-select" in events

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_gantt_chart_narrow_width_and_incomplete_tasks(page, base_url):
    """
        The chart draws at phone widths (276-355 px used to throw
        RangeError) and a task without an end date or a name does not abort
        the draw.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-gantt-chart")
    result = frame.evaluate(
        """async () => {
            const el = document.querySelector('mj-gantt-chart');
            const errors = [];
            const counts = [];
            for (const width of [280, 320, 355]) {
                el.style.width = width + 'px';
                try {
                    el.data = { tasks: [
                        { id: 'a', name: 'Open ended', start: '2026-04-01' },
                        { id: 'only-id', start: '2026-04-03', end: '2026-04-09' },
                        { id: 'c', name: 'Normal', start: '2026-04-02', end: '2026-04-12', percentComplete: 140 }
                    ] };
                } catch (error) {
                    errors.push(error.message);
                }
                await new Promise((r) => setTimeout(r, 50));
                counts.push(el.shadowRoot.querySelectorAll('g[part~=task-bar]').length);
            }
            const rows = Array.from(el.shadowRoot.querySelectorAll('tbody tr')).map((r) => r.textContent);
            return { errors: errors, counts: counts, rows: rows };
        }"""
    )

    assert result["errors"] == []
    assert result["counts"] == [3, 3, 3]
    assert "Open-ended" in result["rows"][0]
    assert result["rows"][1].startswith("only-id")
    assert "100%" in result["rows"][2]

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_gantt_chart_non_object_inline_data_shows_error(page, base_url):
    """
        Declared data that parses to a non-object (inline JSON "tasks") is an
        error: the chart's error message shows and mj-error is emitted (once,
        with the reason), and no mj-data-load reports an empty chart.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-gantt-chart")
    result = frame.evaluate(
        """async () => {
            const seen = [];
            const messages = [];
            for (const name of ['mj-error', 'mj-data-load']) {
                document.addEventListener(name, (event) => {
                    seen.push(name);
                    if (name === 'mj-error') { messages.push(event.detail.message); }
                }, true);
            }
            document.body.innerHTML = '<mj-gantt-chart id="string-gantt"><script type="application/json">"tasks"</' + 'script></mj-gantt-chart>';
            await new Promise((resolve) => setTimeout(resolve, 300));
            const chart = document.getElementById('string-gantt');
            const block = chart.shadowRoot.querySelector('[part~=message]');
            return {
                seen: seen, messages: messages, state: chart.chartState,
                error: block !== null && block.getAttribute('part').split(' ').includes('error'),
                text: block !== null ? block.textContent : null
            };
        }"""
    )

    assert result["seen"] == ["mj-error"], f"events: {result}"
    assert result["state"] == "error" and result["error"] is True, f"error state: {result}"
    assert "object" in result["messages"][0], f"error message: {result}"

    return


_GANTT_WRAPPER_DATA = {
    "groups": [{"id": "g1", "name": "Build"}],
    "tasks": [
        {"id": "spec", "name": "Spec", "start": "2026-03-02", "end": "2026-03-13", "percentComplete": 100, "status": "done"},
        {"id": "code", "name": "Code", "start": "2026-03-16", "end": "2026-04-10", "percentComplete": 40, "groupId": "g1"},
        {"id": "ops", "name": "Ops", "start": "2026-03-20", "groupId": "g1"},
    ],
    "dependencies": [{"from": "spec", "to": "code"}],
    "markers": [{"name": "Beta", "date": "2026-04-01"}],
    "phases": [{"name": "Build", "start": "2026-03-16", "end": "2026-04-10"}],
}

_GANTT_CHART_DATA = {
    "groups": [{"id": "g1", "label": "Build"}],
    "tasks": [
        {"id": "spec", "label": "Spec", "start": "2026-03-02", "end": "2026-03-13", "progress": 1, "status": "done"},
        {"id": "code", "label": "Code", "start": "2026-03-16", "end": "2026-04-10", "progress": 0.4, "group": "g1", "depends": ["spec"]},
        {"id": "ops", "label": "Ops", "start": "2026-03-20", "progress": 0, "group": "g1"},
    ],
    "markers": [{"label": "Beta", "date": "2026-04-01"}],
    "phases": [{"label": "Build", "start": "2026-03-16", "end": "2026-04-10"}],
}


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_gantt_chart_draws_like_mj_chart_gantt(page, base_url):
    """
        mj-gantt-chart is <mj-chart type="gantt">: the same plan in the
        wrapper's data shape and in the chart type's draws the same marks
        (keys, parts, accessible names) and the same data table.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-gantt-chart")
    result = _compare_with_chart(
        frame,
        _inline("mj-gantt-chart", _GANTT_WRAPPER_DATA, 'today-marker="false"'),
        _inline('mj-chart type="gantt"', _GANTT_CHART_DATA, 'today="false" row-height="40"'),
    )

    assert result["wrapper"]["type"] == "gantt", f"type: {result}"
    assert len(result["wrapper"]["marks"]) == 5, f"marks: {result}"
    assert result["wrapper"]["marks"] == result["chart"]["marks"], f"marks differ: {result}"
    assert result["wrapper"]["rows"] == result["chart"]["rows"], f"tables differ: {result}"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_gantt_chart_documented_events_fire(page, base_url):
    """
        mj-gantt-chart keeps its documented events and properties:
        mj-data-load { tasks, groups } once per assignment, mj-task-select
        { task } with the task object and the detail panel, mj-task-deselect
        on Escape (focus back on the bar), mj-marker-select { marker },
        mj-group-toggle { groupId, collapsed } with collapsedGroups, and the
        toolbar button discloses the data table.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-gantt-chart")
    result = frame.evaluate(
        """async ([data]) => {
            document.body.innerHTML = '<mj-gantt-chart id="g"></mj-gantt-chart>';
            const el = document.getElementById('g');
            const seen = [];
            for (const name of ['mj-data-load', 'mj-task-select', 'mj-task-deselect', 'mj-marker-select', 'mj-group-toggle']) {
                el.addEventListener(name, (event) => seen.push([name, event.detail]));
            }
            el.data = data;
            const sr = el.shadowRoot;
            const loadedAtOnce = seen.length;
            const mark = (key) => sr.querySelector(`[data-mark="${key}"]`);
            mark('task:1').dispatchEvent(new MouseEvent('click', { bubbles: true }));
            const panel = sr.querySelector('[part=task-detail]');
            const selected = { same: el.selectedTask === data.tasks[1], panelOpen: panel.hidden === false, current: mark('task:1').getAttribute('aria-current') };
            panel.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true, composed: true }));
            const afterEscape = { panelOpen: panel.hidden === false, focus: sr.activeElement !== null ? sr.activeElement.getAttribute('data-mark') : null, selected: el.selectedTask };
            mark('marker:0').dispatchEvent(new MouseEvent('click', { bubbles: true }));
            mark('group:0').dispatchEvent(new MouseEvent('click', { bubbles: true }));
            await new Promise((resolve) => setTimeout(resolve, 200));
            const collapsed = Array.from(el.collapsedGroups);
            const button = sr.querySelector('[part=toolbar] button');
            button.click();
            const table = sr.querySelector('[part~=data-table]');
            return {
                loadedAtOnce: loadedAtOnce, seen: seen.map((entry) => entry[0]), details: seen.map((entry) => entry[1]),
                selected: selected, afterEscape: afterEscape, collapsed: collapsed,
                markerSame: seen.some((entry) => entry[0] === 'mj-marker-select' && entry[1].marker === data.markers[0]),
                disclosed: button.getAttribute('aria-expanded'), tableHeight: table.getBoundingClientRect().height
            };
        }""",
        [_GANTT_WRAPPER_DATA],
    )

    assert result["loadedAtOnce"] == 1, f"mj-data-load on assignment: {result}"
    assert result["seen"] == ["mj-data-load", "mj-task-select", "mj-task-deselect", "mj-marker-select", "mj-group-toggle"], f"events: {result}"
    assert result["details"][0] == {"tasks": 3, "groups": 1}, f"mj-data-load detail: {result}"
    assert result["selected"] == {"same": True, "panelOpen": True, "current": "true"}, f"selection: {result}"
    assert result["afterEscape"] == {"panelOpen": False, "focus": "task:1", "selected": None}, f"Escape: {result}"
    assert result["markerSame"] is True, f"mj-marker-select detail: {result}"
    assert result["details"][4] == {"groupId": "g1", "collapsed": True}, f"mj-group-toggle detail: {result}"
    assert result["collapsed"] == ["g1"], f"collapsedGroups: {result}"
    assert result["disclosed"] == "true" and result["tableHeight"] > 40, f"table disclosure: {result}"

    return


# ---------------------------------------------------------------------------
# mj-roadmap-chart
# ---------------------------------------------------------------------------

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_roadmap_chart_svg_rendered(page, base_url):
    """
        mj-roadmap-chart renders an SVG in its shadow DOM.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-roadmap-chart")
    assert _shadow_exists(frame, "mj-roadmap-chart", "svg") is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_roadmap_chart_accessible_table_present(page, base_url):
    """
        mj-roadmap-chart includes a data table in the shadow DOM.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-roadmap-chart")
    assert _shadow_exists(frame, "mj-roadmap-chart", "[part~=data-table] table") is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_roadmap_chart_initiative_bars_present(page, base_url):
    """
        mj-roadmap-chart renders initiative bars for all 6 initiatives.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-roadmap-chart")
    _force_draw(frame, "mj-roadmap-chart")
    _wait_for_shadow(frame, "mj-roadmap-chart", "[part~=initiative-bar]")

    count = _shadow_count(frame, "mj-roadmap-chart", "[part~=initiative-bar]")
    assert count >= 6

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_roadmap_chart_column_headers_present(page, base_url):
    """
        mj-roadmap-chart renders column headers for the bucket columns.

        The example's initiatives span at least four calendar quarters.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-roadmap-chart")
    _force_draw(frame, "mj-roadmap-chart")
    _wait_for_shadow(frame, "mj-roadmap-chart", "[part=column-header]")

    count = _shadow_count(frame, "mj-roadmap-chart", "[part=column-header]")
    assert count >= 4

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_roadmap_chart_initiative_select_event(page, base_url):
    """
        Clicking an initiative bar fires the mj-initiative-select event.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-roadmap-chart")
    _force_draw(frame, "mj-roadmap-chart")
    _wait_for_shadow(frame, "mj-roadmap-chart", "[part~=initiative-bar]")

    _collect_events(frame, "mj-roadmap-chart", ["mj-initiative-select"])

    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-roadmap-chart');
            const bar = el.shadowRoot.querySelector('[part~=initiative-bar]');
            if (bar !== null) {
                bar.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
            }
        }"""
    )

    events = frame.evaluate("() => window.__mjevents")
    assert "mj-initiative-select" in events

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_roadmap_chart_calendar_mode_uses_dates_and_stacks(page, base_url):
    """
        In calendar mode initiatives are placed by startDate/endDate, and
        initiatives that overlap in one swimlane are stacked rather than
        drawn on top of each other. percentComplete is escaped.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-roadmap-chart")
    result = frame.evaluate(
        """async ([payload]) => {
            const el = document.querySelector('mj-roadmap-chart');
            el.setAttribute('mode', 'calendar');
            el.data = {
                swimlanes: [{ id: 'p', name: 'Platform' }],
                initiatives: [
                    { id: 'a', name: 'Early', swimlaneId: 'p', startDate: '2026-01-05', endDate: '2026-03-20', percentComplete: payload },
                    { id: 'b', name: 'Late', swimlaneId: 'p', startDate: '2026-07-01', endDate: '2026-09-30' },
                    { id: 'c', name: 'Overlap', swimlaneId: 'p', startDate: '2026-02-01', endDate: '2026-04-30' }
                ]
            };
            await new Promise((r) => setTimeout(r, 100));
            const sr = el.shadowRoot;
            const box = (i) => {
                const r = sr.querySelector(`[data-mark="task:${i}"] rect`);
                return { x: Number(r.getAttribute('x')), y: Number(r.getAttribute('y')) };
            };
            return {
                headers: Array.from(sr.querySelectorAll('[part=column-header]')).map((t) => t.lastChild.textContent),
                a: box(0), b: box(1), c: box(2),
                hits: top.__hits === undefined ? 0 : top.__hits
            };
        }""",
        [_INJECTION],
    )

    assert result["headers"] == ["Q1 2026", "Q2 2026", "Q3 2026"]
    assert result["b"]["x"] > result["a"]["x"]
    assert result["c"]["y"] != result["a"]["y"]
    assert result["hits"] == 0

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_roadmap_chart_data_load_and_separate_phase_and_today_rows(page, base_url):
    """
        Assigning data emits mj-data-load { initiatives, swimlanes }, and in
        calendar mode a phase that covers today has its name and the Today
        label in separate rows under the swimlanes (no overlap with each
        other or with the bars).

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-roadmap-chart")
    result = frame.evaluate(
        """async () => {
            const el = document.querySelector('mj-roadmap-chart');
            const loads = [];
            el.addEventListener('mj-data-load', (event) => loads.push(event.detail));
            const day = (offset) => {
                const date = new Date();
                date.setDate(date.getDate() + offset);
                return date.toISOString().slice(0, 10);
            };
            el.setAttribute('mode', 'calendar');
            el.removeAttribute('today-marker');
            el.data = {
                swimlanes: [{ id: 'p', name: 'Platform' }, { id: 'q', name: 'Quality' }],
                initiatives: [
                    { id: 'a', name: 'Now', swimlaneId: 'p', startDate: day(-20), endDate: day(20) },
                    { id: 'b', name: 'Next', swimlaneId: 'q', startDate: day(-5), endDate: day(40) }
                ],
                phases: [{ name: 'Planning phase', start: day(-30), end: day(30) }]
            };
            await new Promise((resolve) => setTimeout(resolve, 100));
            const sr = el.shadowRoot;
            const box = (node) => { const b = node.getBBox(); return { top: b.y, bottom: b.y + b.height }; };
            const phase = sr.querySelector('[part=phase-label]');
            const today = sr.querySelector('[part=today-label]');
            const bars = Array.from(sr.querySelectorAll('[part~=initiative-bar] rect')).map(box);
            return {
                loads: loads,
                phase: phase === null ? null : box(phase),
                today: today === null ? null : box(today),
                barsBottom: Math.max(...bars.map((bar) => bar.bottom))
            };
        }"""
    )

    assert result["loads"] == [{"initiatives": 2, "swimlanes": 2}], f"mj-data-load: {result}"
    assert result["phase"] is not None and result["today"] is not None, f"labels missing: {result}"
    assert result["phase"]["bottom"] <= result["today"]["top"], f"phase and Today labels overlap: {result}"
    assert result["phase"]["top"] >= result["barsBottom"], f"phase label overlaps the bars: {result}"

    return


_ROADMAP_WRAPPER_DATA = {
    "swimlanes": [{"id": "web", "name": "Web"}, {"id": "app", "name": "App"}],
    "initiatives": [
        {"id": "a", "name": "Checkout", "swimlaneId": "web", "startDate": "2026-01-05", "endDate": "2026-03-27", "status": "in-progress", "percentComplete": 50},
        {"id": "b", "name": "Search", "swimlane": "web", "start": "2026-04-06", "end": "2026-06-26", "status": "planned"},
        {"id": "c", "name": "Offline", "swimlaneId": "app", "startDate": "2026-02-02", "endDate": "2026-05-29", "status": "at-risk", "description": "Needs a sync engine."},
    ],
    "markers": [{"name": "Launch", "date": "2026-04-01"}],
}

_ROADMAP_CHART_DATA = {
    "groups": [{"id": "web", "label": "Web"}, {"id": "app", "label": "App"}],
    "tasks": [
        {"id": "a", "label": "Checkout", "group": "web", "start": "2026-01-05", "end": "2026-03-27", "status": "in-progress", "progress": 0.5},
        {"id": "b", "label": "Search", "group": "web", "start": "2026-04-06", "end": "2026-06-26", "status": "planned"},
        {"id": "c", "label": "Offline", "group": "app", "start": "2026-02-02", "end": "2026-05-29", "status": "at-risk", "description": "Needs a sync engine."},
    ],
    "markers": [{"label": "Launch", "date": "2026-04-01"}],
}


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_roadmap_chart_draws_like_mj_chart_roadmap(page, base_url):
    """
        mj-roadmap-chart is <mj-chart type="roadmap">: the same roadmap in
        both data shapes draws the same marks and the same data table.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-roadmap-chart")
    result = _compare_with_chart(
        frame,
        _inline("mj-roadmap-chart", _ROADMAP_WRAPPER_DATA, 'today-marker="false"'),
        _inline('mj-chart type="roadmap"', _ROADMAP_CHART_DATA, 'today="false"'),
    )

    assert result["wrapper"]["type"] == "roadmap", f"type: {result}"
    assert len(result["wrapper"]["marks"]) == 4, f"marks: {result}"
    assert result["wrapper"]["marks"] == result["chart"]["marks"], f"marks differ: {result}"
    assert result["wrapper"]["rows"] == result["chart"]["rows"], f"tables differ: {result}"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_roadmap_chart_documented_events_fire(page, base_url):
    """
        mj-roadmap-chart keeps mj-data-load { initiatives, swimlanes },
        mj-initiative-select { initiative } with the detail panel and
        selectedInitiative, and mj-initiative-deselect on Escape.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-roadmap-chart")
    result = frame.evaluate(
        """async ([data]) => {
            document.body.innerHTML = '<mj-roadmap-chart id="r"></mj-roadmap-chart>';
            const el = document.getElementById('r');
            const seen = [];
            for (const name of ['mj-data-load', 'mj-initiative-select', 'mj-initiative-deselect']) {
                el.addEventListener(name, (event) => seen.push([name, event.detail]));
            }
            el.data = data;
            const sr = el.shadowRoot;
            sr.querySelector('[data-mark="task:2"]').dispatchEvent(new MouseEvent('click', { bubbles: true }));
            const panel = sr.querySelector('[part=initiative-detail]');
            const opened = { same: el.selectedInitiative === data.initiatives[2], text: panel.textContent.replace(/\\s+/g, ' ') };
            panel.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true, composed: true }));
            return { seen: seen.map((entry) => entry[0]), load: seen[0][1], opened: opened, after: el.selectedInitiative, same: seen[1][1].initiative === data.initiatives[2] };
        }""",
        [_ROADMAP_WRAPPER_DATA],
    )

    assert result["seen"] == ["mj-data-load", "mj-initiative-select", "mj-initiative-deselect"], f"events: {result}"
    assert result["load"] == {"initiatives": 3, "swimlanes": 2}, f"mj-data-load detail: {result}"
    assert result["opened"]["same"] is True and result["same"] is True, f"selection: {result}"
    assert "Needs a sync engine." in result["opened"]["text"], f"detail panel: {result}"
    assert result["after"] is None, f"deselect: {result}"

    return


# ---------------------------------------------------------------------------
# mj-milestone-timeline
# ---------------------------------------------------------------------------

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_milestone_timeline_svg_rendered(page, base_url):
    """
        mj-milestone-timeline renders an SVG in its shadow DOM.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-milestone-timeline")
    assert _shadow_exists(frame, "mj-milestone-timeline", "svg") is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_milestone_timeline_accessible_list_present(page, base_url):
    """
        mj-milestone-timeline includes the chart's data table (it replaced
        the accessible ordered list).

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-milestone-timeline")
    assert _shadow_exists(frame, "mj-milestone-timeline", "[part~=data-table] table") is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_milestone_timeline_time_axis_rendered(page, base_url):
    """
        mj-milestone-timeline renders a horizontal time axis line.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-milestone-timeline")
    _force_draw(frame, "mj-milestone-timeline")
    _wait_for_shadow(frame, "mj-milestone-timeline", "[part=time-axis]")

    assert _shadow_exists(frame, "mj-milestone-timeline", "[part=time-axis]") is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_milestone_timeline_markers_present(page, base_url):
    """
        mj-milestone-timeline renders one marker group per marker entry.

        The example has 5 markers.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-milestone-timeline")
    _force_draw(frame, "mj-milestone-timeline")
    _wait_for_shadow(frame, "mj-milestone-timeline", "[part=marker]")

    count = _shadow_count(frame, "mj-milestone-timeline", "[part=marker]")
    assert count >= 5

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_milestone_timeline_marker_select_event(page, base_url):
    """
        Clicking a marker group fires the mj-marker-select event.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-milestone-timeline")
    _force_draw(frame, "mj-milestone-timeline")
    _wait_for_shadow(frame, "mj-milestone-timeline", "[part=marker]")

    _collect_events(frame, "mj-milestone-timeline", ["mj-marker-select"])

    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-milestone-timeline');
            const marker = el.shadowRoot.querySelector('[part=marker]');
            if (marker !== null) {
                marker.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
            }
        }"""
    )

    events = frame.evaluate("() => window.__mjevents")
    assert "mj-marker-select" in events

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_milestone_timeline_type_escaped_and_invalid_date(page, base_url):
    """
        A marker type containing markup is escaped in the data table,
        and a marker with an invalid date does not abort the draw.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-milestone-timeline")
    result = frame.evaluate(
        """async ([payload]) => {
            const el = document.querySelector('mj-milestone-timeline');
            let error = null;
            try {
                el.data = { markers: [
                    { name: 'A', date: '2026-05-01', type: payload },
                    { name: 'B', date: 'not a date' },
                    { name: 'C', date: '2026-05-20', type: 'release' }
                ] };
            } catch (caught) {
                error = caught.message;
            }
            await new Promise((r) => setTimeout(r, 100));
            const sr = el.shadowRoot;
            return {
                error: error,
                items: sr.querySelectorAll('[part~=data-table] tbody tr').length,
                images: sr.querySelectorAll('img').length,
                marks: sr.querySelectorAll('[part=marker]').length,
                hits: top.__hits === undefined ? 0 : top.__hits
            };
        }""",
        [_INJECTION],
    )

    assert result["error"] is None
    assert result["items"] == 3
    assert result["images"] == 0
    assert result["marks"] == 2
    assert result["hits"] == 0

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_milestone_timeline_emits_data_load(page, base_url):
    """
        Assigning data emits mj-data-load { markers, phases } like the other
        charts of the group.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-milestone-timeline")
    loads = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-milestone-timeline');
            const loads = [];
            el.addEventListener('mj-data-load', (event) => loads.push(event.detail));
            el.data = {
                markers: [{ name: 'Beta', date: '2026-03-01' }, { name: 'GA', date: '2026-05-01', type: 'release' }],
                phases: [{ name: 'Hardening', start: '2026-03-01', end: '2026-04-30' }]
            };
            return loads;
        }"""
    )

    assert loads == [{"markers": 2, "phases": 1}], f"mj-data-load: {loads}"

    return


_MILESTONE_WRAPPER_DATA = {
    "markers": [
        {"name": "Alpha", "date": "2026-01-20", "type": "tag"},
        {"name": "Freeze", "date": "2026-02-20", "type": "freeze", "description": "No new features."},
        {"name": "GA", "date": "2026-03-16", "type": "release"},
        {"name": "Retro", "date": "2026-03-20"},
    ],
    "phases": [{"name": "Hardening", "start": "2026-02-20", "end": "2026-03-16"}],
}

_MILESTONE_CHART_DATA = {
    "events": [
        {"label": "Alpha", "date": "2026-01-20", "kind": "tag"},
        {"label": "Freeze", "date": "2026-02-20", "kind": "freeze", "description": "No new features."},
        {"label": "GA", "date": "2026-03-16", "kind": "release"},
        {"label": "Retro", "date": "2026-03-20", "kind": "milestone"},
    ],
    "phases": [{"label": "Hardening", "start": "2026-02-20", "end": "2026-03-16"}],
}


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_milestone_timeline_draws_like_mj_chart_milestone(page, base_url):
    """
        mj-milestone-timeline is <mj-chart type="milestone" dim-past>: the
        same markers in both data shapes draw the same marks and the same
        data table.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-milestone-timeline")
    result = _compare_with_chart(
        frame,
        _inline("mj-milestone-timeline", _MILESTONE_WRAPPER_DATA, 'start-date="2026-01-01" end-date="2026-03-31"'),
        _inline('mj-chart type="milestone"', _MILESTONE_CHART_DATA, 'dim-past start-date="2026-01-01" end-date="2026-03-31"'),
    )

    assert result["wrapper"]["type"] == "milestone", f"type: {result}"
    assert len(result["wrapper"]["marks"]) == 4, f"marks: {result}"
    assert result["wrapper"]["marks"] == result["chart"]["marks"], f"marks differ: {result}"
    assert result["wrapper"]["rows"] == result["chart"]["rows"], f"tables differ: {result}"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_milestone_timeline_documented_events_fire(page, base_url):
    """
        mj-milestone-timeline keeps mj-marker-select { marker } with the
        detail panel and selectedMarker, and mj-marker-deselect when the
        panel's Close button is used.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-milestone-timeline")
    result = frame.evaluate(
        """async ([data]) => {
            document.body.innerHTML = '<mj-milestone-timeline id="m"></mj-milestone-timeline>';
            const el = document.getElementById('m');
            const seen = [];
            for (const name of ['mj-data-load', 'mj-marker-select', 'mj-marker-deselect']) {
                el.addEventListener(name, (event) => seen.push([name, event.detail]));
            }
            el.data = data;
            const sr = el.shadowRoot;
            sr.querySelector('[data-mark="event:1"]').dispatchEvent(new MouseEvent('click', { bubbles: true }));
            const panel = sr.querySelector('[part=detail-popover]');
            const opened = { same: el.selectedMarker === data.markers[1], text: panel.textContent.replace(/\\s+/g, ' ') };
            panel.querySelector('.detail-close').click();
            return { seen: seen.map((entry) => entry[0]), load: seen[0][1], opened: opened, after: el.selectedMarker, hidden: panel.hidden };
        }""",
        [_MILESTONE_WRAPPER_DATA],
    )

    assert result["seen"] == ["mj-data-load", "mj-marker-select", "mj-marker-deselect"], f"events: {result}"
    assert result["load"] == {"markers": 4, "phases": 1}, f"mj-data-load detail: {result}"
    assert result["opened"]["same"] is True and "No new features." in result["opened"]["text"], f"selection: {result}"
    assert result["after"] is None and result["hidden"] is True, f"deselect: {result}"

    return


# ---------------------------------------------------------------------------
# mj-burndown-chart
# ---------------------------------------------------------------------------

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_burndown_chart_svg_rendered(page, base_url):
    """
        mj-burndown-chart renders an SVG in its shadow DOM.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-burndown-chart")
    assert _shadow_exists(frame, "mj-burndown-chart", "svg") is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_burndown_chart_accessible_table_present(page, base_url):
    """
        mj-burndown-chart always includes a data table in the shadow DOM.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-burndown-chart")
    assert _shadow_exists(frame, "mj-burndown-chart", "table[part=data-table]") is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_burndown_chart_actual_line_present(page, base_url):
    """
        mj-burndown-chart renders an actual-line polyline for past data points.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-burndown-chart")
    _force_draw(frame, "mj-burndown-chart")
    _wait_for_shadow(frame, "mj-burndown-chart", "[part=actual-line]")

    assert _shadow_exists(frame, "mj-burndown-chart", "[part=actual-line]") is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_burndown_chart_ideal_line_present(page, base_url):
    """
        mj-burndown-chart renders a dashed ideal-line by default.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-burndown-chart")
    _force_draw(frame, "mj-burndown-chart")
    _wait_for_shadow(frame, "mj-burndown-chart", "[part=ideal-line]")

    assert _shadow_exists(frame, "mj-burndown-chart", "[part=ideal-line]") is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_burndown_chart_data_points_rendered(page, base_url):
    """
        mj-burndown-chart renders clickable data-point circles for past values.

        The example's daily values run up to today, so all of them are plotted.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-burndown-chart")
    _force_draw(frame, "mj-burndown-chart")
    _wait_for_shadow(frame, "mj-burndown-chart", "[part=data-point]")

    count = _shadow_count(frame, "mj-burndown-chart", "[part=data-point]")
    assert count >= 1

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_burndown_chart_point_select_event(page, base_url):
    """
        Clicking a data point circle fires the mj-point-select event.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-burndown-chart")
    _force_draw(frame, "mj-burndown-chart")
    _wait_for_shadow(frame, "mj-burndown-chart", "[part=data-point]")

    _collect_events(frame, "mj-burndown-chart", ["mj-point-select"])

    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-burndown-chart');
            const pt = el.shadowRoot.querySelector('[part=data-point]');
            if (pt !== null) {
                pt.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
            }
        }"""
    )

    events = frame.evaluate("() => window.__mjevents")
    assert "mj-point-select" in events

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_burndown_chart_badge_uses_sprint_range(page, base_url):
    """
        The ideal line and the "Behind schedule" badge use the sprint range
        (start-date / end-date), not the extent of the data: a sprint
        burned down to zero is never behind, and a mid-sprint value on the
        ideal line is on track. Scope-change values are escaped.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-burndown-chart")
    result = frame.evaluate(
        """async ([payload]) => {
            const el = document.querySelector('mj-burndown-chart');
            const sr = el.shadowRoot;
            const day = (offset) => {
                const d = new Date(Date.now() + offset * 86400000);
                return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
            };
            const badge = () => sr.querySelector('.status-badge').hidden === false;
            const settle = () => new Promise((r) => setTimeout(r, 50));

            el.data = { totalScope: 40, dailyValues: [{ date: '2026-01-01', value: 40 }, { date: '2026-01-10', value: 0 }],
                        scopeChanges: [{ date: '2026-01-05', delta: payload }], dailyValuesExtra: payload };
            await settle();
            const finished = badge();

            el.setAttribute('start-date', day(-5));
            el.setAttribute('end-date', day(5));
            /* The ideal "now" is 50..40 over the course of today; 38 is on track at any hour. */
            el.data = { totalScope: 100, dailyValues: [{ date: day(-5), value: 100 }, { date: day(0), value: 38 }] };
            await settle();
            const onTrack = badge();

            el.data = { totalScope: 100, dailyValues: [{ date: day(-5), value: 100 }, { date: day(0), value: 90 }] };
            await settle();
            const behind = badge();

            return { finished: finished, onTrack: onTrack, behind: behind, hits: top.__hits === undefined ? 0 : top.__hits };
        }""",
        [_INJECTION],
    )

    assert result["finished"] is False
    assert result["onTrack"] is False
    assert result["behind"] is True
    assert result["hits"] == 0

    return


# ---------------------------------------------------------------------------
# mj-cumulative-flow
# ---------------------------------------------------------------------------

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_cumulative_flow_svg_rendered(page, base_url):
    """
        mj-cumulative-flow renders an SVG in its shadow DOM.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-cumulative-flow")
    assert _shadow_exists(frame, "mj-cumulative-flow", "svg") is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_cumulative_flow_accessible_table_present(page, base_url):
    """
        mj-cumulative-flow includes a data table in the shadow DOM.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-cumulative-flow")
    assert _shadow_exists(frame, "mj-cumulative-flow", "table[part=data-table]") is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_cumulative_flow_state_bands_present(page, base_url):
    """
        mj-cumulative-flow renders one polygon state-band per workflow state.

        The example has 5 states.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-cumulative-flow")
    _force_draw(frame, "mj-cumulative-flow")
    _wait_for_shadow(frame, "mj-cumulative-flow", "[part=state-band]")

    count = _shadow_count(frame, "mj-cumulative-flow", "[part=state-band]")
    assert count >= 5

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_cumulative_flow_legend_buttons_present(page, base_url):
    """
        mj-cumulative-flow renders a legend button for each workflow state.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-cumulative-flow")
    _force_draw(frame, "mj-cumulative-flow")
    _wait_for_shadow(frame, "mj-cumulative-flow", "[part=legend-item]")

    count = _shadow_count(frame, "mj-cumulative-flow", "[part=legend-item]")
    assert count >= 5

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_cumulative_flow_state_toggle_event(page, base_url):
    """
        Clicking a legend button fires the mj-state-toggle event.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-cumulative-flow")
    _force_draw(frame, "mj-cumulative-flow")
    _wait_for_shadow(frame, "mj-cumulative-flow", "[part=legend-item]")

    _collect_events(frame, "mj-cumulative-flow", ["mj-state-toggle"])

    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-cumulative-flow');
            const btn = el.shadowRoot.querySelector('[part=legend-item]');
            if (btn !== null) { btn.click(); }
        }"""
    )

    events = frame.evaluate("() => window.__mjevents")
    assert "mj-state-toggle" in events

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_cumulative_flow_toggle_keeps_colors_and_focus(page, base_url):
    """
        Hiding a state keeps the other bands' colors (pattern ids follow the
        position in data.states) and the pressed legend button keeps focus.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-cumulative-flow")
    _force_draw(frame, "mj-cumulative-flow")
    _wait_for_shadow(frame, "mj-cumulative-flow", "[part=state-band]")

    result = frame.evaluate(
        """() => {
            const sr = document.querySelector('mj-cumulative-flow').shadowRoot;
            const fills = () => Array.from(sr.querySelectorAll('[part=state-band]')).map((b) => b.getAttribute('fill'));
            const before = fills();
            const button = sr.querySelector('[part=legend-item]');
            button.focus();
            button.click();
            return { before: before, after: fills(), focusKept: sr.activeElement === button, pressed: button.getAttribute('aria-pressed') };
        }"""
    )

    assert result["after"] == result["before"][1:]
    assert result["focusKept"] is True
    assert result["pressed"] == "false"

    return


# ---------------------------------------------------------------------------
# mj-velocity-chart
# ---------------------------------------------------------------------------

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_velocity_chart_svg_rendered(page, base_url):
    """
        mj-velocity-chart renders an SVG in its shadow DOM.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-velocity-chart")
    assert _shadow_exists(frame, "mj-velocity-chart", "svg") is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_velocity_chart_accessible_table_present(page, base_url):
    """
        mj-velocity-chart includes a data table in the shadow DOM.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-velocity-chart")
    assert _shadow_exists(frame, "mj-velocity-chart", "table[part=data-table]") is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_velocity_chart_bar_groups_present(page, base_url):
    """
        mj-velocity-chart renders one bar-group per sprint (7 in example).

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-velocity-chart")
    _force_draw(frame, "mj-velocity-chart")
    _wait_for_shadow(frame, "mj-velocity-chart", "[part=bar-group]")

    count = _shadow_count(frame, "mj-velocity-chart", "[part=bar-group]")
    assert count >= 7

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_velocity_chart_rolling_average_line_present(page, base_url):
    """
        mj-velocity-chart renders the rolling-average polyline by default.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-velocity-chart")
    _force_draw(frame, "mj-velocity-chart")
    _wait_for_shadow(frame, "mj-velocity-chart", "[part=average-line]")

    assert _shadow_exists(frame, "mj-velocity-chart", "[part=average-line]") is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_velocity_chart_sprint_select_event(page, base_url):
    """
        Clicking a bar group fires the mj-sprint-select event.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-velocity-chart")
    _force_draw(frame, "mj-velocity-chart")
    _wait_for_shadow(frame, "mj-velocity-chart", "[part=bar-group]")

    _collect_events(frame, "mj-velocity-chart", ["mj-sprint-select"])

    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-velocity-chart');
            const group = el.shadowRoot.querySelector('[part=bar-group]');
            if (group !== null) {
                group.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
            }
        }"""
    )

    events = frame.evaluate("() => window.__mjevents")
    assert "mj-sprint-select" in events

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_velocity_chart_labels_distinct_and_window_clamped(page, base_url):
    """
        Sprint axis labels stay distinguishable (Sprint 10..14 no longer all
        read "Sprint 1") and a rolling window of 0 does not produce NaN.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-velocity-chart")
    _force_draw(frame, "mj-velocity-chart")
    _wait_for_shadow(frame, "mj-velocity-chart", "[part=bar-group]")

    result = frame.evaluate(
        """async () => {
            const el = document.querySelector('mj-velocity-chart');
            el.setAttribute('rolling-window', '0');
            await new Promise((r) => setTimeout(r, 50));
            const labels = Array.from(el.shadowRoot.querySelectorAll('svg > text')).map((t) => t.lastChild.textContent).filter((t) => t.indexOf('Sprint') === 0);
            return { labels: labels, averages: el.rollingAverage };
        }"""
    )

    assert len(result["labels"]) == 7
    assert len(set(result["labels"])) == 7
    assert all(value == value for value in result["averages"])

    return


# ---------------------------------------------------------------------------
# mj-dependency-graph
# ---------------------------------------------------------------------------

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_dependency_graph_svg_rendered(page, base_url):
    """
        mj-dependency-graph renders an SVG in its shadow DOM.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-dependency-graph")
    assert _shadow_exists(frame, "mj-dependency-graph", "svg") is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_dependency_graph_accessible_list_present(page, base_url):
    """
        mj-dependency-graph includes the chart's data table (it replaced the
        accessible definition list).

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-dependency-graph")
    assert _shadow_exists(frame, "mj-dependency-graph", "[part~=data-table] table") is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_dependency_graph_nodes_present(page, base_url):
    """
        mj-dependency-graph renders one node element per graph node.

        The example has 7 nodes; critical path nodes carry the part names
        'node critical-path-node'.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-dependency-graph")
    _force_draw(frame, "mj-dependency-graph")
    frame.wait_for_function(
        """() => {
            const el = document.querySelector('mj-dependency-graph');
            if (el === null || el.shadowRoot === null) { return false; }
            const nodes = el.shadowRoot.querySelectorAll('[part~=node]');
            return nodes.length >= 7;
        }""",
        timeout=10000,
    )

    count_nodes = _shadow_count(frame, "mj-dependency-graph", "[part~=node]")
    assert count_nodes >= 7

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_dependency_graph_critical_path_highlighted(page, base_url):
    """
        mj-dependency-graph highlights critical-path nodes with amber border.

        The example provides 5 critical-path nodes.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-dependency-graph")
    _force_draw(frame, "mj-dependency-graph")
    _wait_for_shadow(frame, "mj-dependency-graph", "[part~=critical-path-node]")

    count = _shadow_count(frame, "mj-dependency-graph", "[part~=critical-path-node]")
    assert count >= 5

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_dependency_graph_node_select_event(page, base_url):
    """
        Clicking a node fires the mj-node-select event.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-dependency-graph")
    _force_draw(frame, "mj-dependency-graph")
    frame.wait_for_function(
        """() => {
            const el = document.querySelector('mj-dependency-graph');
            if (el === null || el.shadowRoot === null) { return false; }
            return el.shadowRoot.querySelectorAll('[part~=node]').length >= 1;
        }""",
        timeout=10000,
    )

    _collect_events(frame, "mj-dependency-graph", ["mj-node-select"])

    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-dependency-graph');
            const node = el.shadowRoot.querySelector('[part~=node]');
            if (node !== null) {
                node.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
            }
        }"""
    )

    events = frame.evaluate("() => window.__mjevents")
    assert "mj-node-select" in events

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_dependency_graph_cycle_safe_layout(page, base_url):
    """
        A cycle (b -> c -> b) and an edge to an unknown node no longer pile
        nodes into one column; the estimate is escaped in the detail panel.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-dependency-graph")
    result = frame.evaluate(
        """async ([payload]) => {
            const el = document.querySelector('mj-dependency-graph');
            el.data = {
                nodes: [{ id: 'a', name: 'A', estimate: payload }, { id: 'b', name: 'B' }, { id: 'c', name: 'C' }, { id: 'd', name: 'D' }],
                edges: [{ from: 'a', to: 'b' }, { from: 'b', to: 'c' }, { from: 'c', to: 'b' }, { from: 'c', to: 'd' }, { from: 'a', to: 'zzz' }]
            };
            await new Promise((r) => setTimeout(r, 100));
            const sr = el.shadowRoot;
            const xs = [0, 1, 2, 3].map((i) => Number(sr.querySelector(`[data-mark="node:${i}"] rect`).getAttribute('x')));
            sr.querySelector('[data-mark="node:0"]').dispatchEvent(new MouseEvent('click', {bubbles: true}));
            return { xs: xs, cycles: el.cycles.length, images: sr.querySelectorAll('img').length, hits: top.__hits === undefined ? 0 : top.__hits };
        }""",
        [_INJECTION],
    )

    assert len(set(result["xs"])) == 4
    assert result["xs"] == sorted(result["xs"])
    assert result["cycles"] == 1
    assert result["images"] == 0
    assert result["hits"] == 0

    return


_DEPENDENCY_WRAPPER_DATA = {
    "nodes": [
        {"id": "a", "name": "Alpha", "status": "done", "estimate": "2 d"},
        {"id": "b", "name": "Beta", "status": "in-progress"},
        {"id": "c", "name": "Gamma"},
    ],
    "edges": [{"from": "a", "to": "b"}, {"from": "b", "to": "c"}, {"from": "c", "to": "b"}],
    "criticalPath": ["a", "b"],
}

_DEPENDENCY_CHART_DATA = {
    "nodes": [
        {"id": "a", "label": "Alpha", "status": "done"},
        {"id": "b", "label": "Beta", "status": "in-progress"},
        {"id": "c", "label": "Gamma", "status": "todo"},
    ],
    "links": [{"source": "a", "target": "b"}, {"source": "b", "target": "c"}, {"source": "c", "target": "b"}],
    "criticalPath": ["a", "b"],
}


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_dependency_graph_draws_like_mj_chart_dependency_graph(page, base_url):
    """
        mj-dependency-graph is <mj-chart type="dependency-graph">: the same
        graph in both data shapes draws the same marks and the same data
        table.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-dependency-graph")
    result = _compare_with_chart(
        frame,
        _inline("mj-dependency-graph", _DEPENDENCY_WRAPPER_DATA),
        _inline('mj-chart type="dependency-graph"', _DEPENDENCY_CHART_DATA),
    )

    assert result["wrapper"]["type"] == "dependency-graph", f"type: {result}"
    assert len(result["wrapper"]["marks"]) == 3, f"marks: {result}"
    assert result["wrapper"]["marks"] == result["chart"]["marks"], f"marks differ: {result}"
    assert result["wrapper"]["rows"] == result["chart"]["rows"], f"tables differ: {result}"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_dependency_graph_documented_events_fire(page, base_url):
    """
        mj-dependency-graph keeps mj-data-load { nodes, edges, hasCycles },
        mj-cycle-detected { cycles } once per assignment (not per redraw)
        with the banner and the `cycles` property, mj-node-select { node }
        with the estimate in the detail panel, and mj-node-deselect.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-dependency-graph")
    result = frame.evaluate(
        """async ([data]) => {
            document.body.innerHTML = '<mj-dependency-graph id="d"></mj-dependency-graph>';
            const el = document.getElementById('d');
            const seen = [];
            for (const name of ['mj-data-load', 'mj-cycle-detected', 'mj-node-select', 'mj-node-deselect']) {
                el.addEventListener(name, (event) => seen.push([name, event.detail]));
            }
            el.data = data;
            await el.redraw();
            const sr = el.shadowRoot;
            const banner = sr.querySelector('[part=cycle-banner]');
            sr.querySelector('[data-mark="node:0"]').dispatchEvent(new MouseEvent('click', { bubbles: true }));
            const panel = sr.querySelector('[part=detail-panel]');
            const opened = { same: el.selectedNode === data.nodes[0], text: panel.textContent.replace(/\\s+/g, ' ') };
            panel.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true, composed: true }));
            return {
                seen: seen.map((entry) => entry[0]), load: seen[0][1], cycles: seen[1][1].cycles,
                property: el.cycles, banner: banner.hidden === false ? banner.textContent : null,
                opened: opened, after: el.selectedNode, zoom: el.zoom
            };
        }""",
        [_DEPENDENCY_WRAPPER_DATA],
    )

    assert result["seen"] == ["mj-data-load", "mj-cycle-detected", "mj-node-select", "mj-node-deselect"], f"events: {result}"
    assert result["load"] == {"nodes": 3, "edges": 3, "hasCycles": True}, f"mj-data-load detail: {result}"
    assert result["cycles"] == [["b", "c"]] and result["property"] == [["b", "c"]], f"cycles: {result}"
    assert result["banner"] is not None and "Beta → Gamma → Beta" in result["banner"], f"banner: {result}"
    assert result["opened"]["same"] is True and "2 d" in result["opened"]["text"], f"selection: {result}"
    assert result["after"] is None and result["zoom"] == 1, f"deselect / zoom: {result}"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_pm_chart_wrappers_escape_every_field(page, base_url):
    """
        Every data field and attribute the four wrappers accept, set to an
        HTML injection payload, is drawn and shown in the detail panels as
        text: no element is created from it and no handler runs.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-dependency-graph")
    result = frame.evaluate(
        """async ([x]) => {
            document.body.innerHTML =
                `<mj-gantt-chart id="g"></mj-gantt-chart><mj-roadmap-chart id="r"></mj-roadmap-chart>` +
                `<mj-milestone-timeline id="m"></mj-milestone-timeline><mj-dependency-graph id="d"></mj-dependency-graph>`;
            const attrs = ['scale', 'start-date', 'end-date', 'today-marker', 'show-dependencies', 'show-percent', 'density', 'mode', 'show-critical-path', 'collapsed-groups'];
            for (const el of document.body.children) {
                for (const name of attrs) { el.setAttribute(name, x); }
            }
            document.getElementById('g').data = {
                groups: [{ id: x, name: x }],
                tasks: [{ id: x, name: x, start: '2026-03-02', end: '2026-03-20', percentComplete: x, status: x, groupId: x }, { id: 't2', name: x, start: x, end: x }],
                dependencies: [{ from: x, to: 't2' }], markers: [{ name: x, date: '2026-03-10' }], phases: [{ name: x, start: '2026-03-02', end: '2026-03-09' }]
            };
            document.getElementById('r').data = {
                swimlanes: [{ id: x, name: x }], buckets: [{ id: x, name: x }],
                initiatives: [{ id: x, name: x, swimlaneId: x, columnId: x, status: x, percentComplete: x, description: x, startDate: '2026-01-05', endDate: '2026-02-27' }],
                markers: [{ name: x, date: '2026-02-02' }], phases: [{ name: x, start: '2026-01-05', end: '2026-01-30' }]
            };
            document.getElementById('m').data = { markers: [{ name: x, date: '2026-03-01', type: x, description: x }], phases: [{ name: x, start: '2026-02-01', end: '2026-03-31' }] };
            document.getElementById('d').data = { nodes: [{ id: x, name: x, status: x, estimate: x }, { id: 'b', name: 'B' }], edges: [{ from: x, to: 'b' }, { from: 'b', to: x }], criticalPath: [x, 'b'] };
            await new Promise((resolve) => setTimeout(resolve, 500));
            let images = 0;
            for (const el of document.body.children) {
                for (const mark of el.shadowRoot.querySelectorAll('[data-mark]')) {
                    mark.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                    images = images + el.shadowRoot.querySelectorAll('img').length;
                }
                el.shadowRoot.querySelector('[part=toolbar] button').click();
                images = images + el.shadowRoot.querySelectorAll('img').length;
            }
            await new Promise((resolve) => setTimeout(resolve, 300));
            return {
                images: images, hits: top.__hits === undefined ? 0 : top.__hits,
                tables: Array.from(document.body.children).map((el) => el.shadowRoot.querySelector('[data-chart-table]').textContent.includes(x))
            };
        }""",
        [_INJECTION],
    )

    assert result["images"] == 0, f"markup was created from data: {result}"
    assert result["hits"] == 0, f"an injected handler ran: {result}"
    assert result["tables"] == [True, True, True, True], f"the payload is not shown as text: {result}"

    return


# ---------------------------------------------------------------------------
# mj-workflow-diagram
# ---------------------------------------------------------------------------

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_workflow_diagram_svg_rendered(page, base_url):
    """
        mj-workflow-diagram renders an SVG in its shadow DOM.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-workflow-diagram")
    assert _shadow_exists(frame, "mj-workflow-diagram", "svg") is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_workflow_diagram_accessible_list_present(page, base_url):
    """
        mj-workflow-diagram includes an accessible definition list.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-workflow-diagram")
    assert _shadow_exists(frame, "mj-workflow-diagram", "dl[part=a11y-list]") is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_workflow_diagram_state_nodes_present(page, base_url):
    """
        mj-workflow-diagram renders one node group per state.

        The example has 6 states; the current state gets
        part='state-node-current'.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-workflow-diagram")
    _force_draw(frame, "mj-workflow-diagram")
    frame.wait_for_function(
        """() => {
            const el = document.querySelector('mj-workflow-diagram');
            if (el === null || el.shadowRoot === null) { return false; }
            const all = el.shadowRoot.querySelectorAll('[part=state-node],[part=state-node-current]');
            return all.length >= 6;
        }""",
        timeout=10000,
    )

    count_normal = _shadow_count(frame, "mj-workflow-diagram", "[part=state-node]")
    count_current = _shadow_count(frame, "mj-workflow-diagram", "[part=state-node-current]")
    assert (count_normal + count_current) >= 6

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_workflow_diagram_current_state_pulsing_ring(page, base_url):
    """
        The state matching current-state='review' gets a pulsing ring element.

        The example sets current-state='review'; the JS renders a rect with
        class 'current-pulse' inside that state node.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-workflow-diagram")
    _force_draw(frame, "mj-workflow-diagram")
    _wait_for_shadow(frame, "mj-workflow-diagram", ".current-pulse")

    assert _shadow_exists(frame, "mj-workflow-diagram", ".current-pulse") is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_workflow_diagram_node_select_event(page, base_url):
    """
        Clicking a state node fires the mj-node-select event.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-workflow-diagram")
    _force_draw(frame, "mj-workflow-diagram")
    frame.wait_for_function(
        """() => {
            const el = document.querySelector('mj-workflow-diagram');
            if (el === null || el.shadowRoot === null) { return false; }
            return el.shadowRoot.querySelectorAll('[part=state-node],[part=state-node-current]').length >= 1;
        }""",
        timeout=10000,
    )

    _collect_events(frame, "mj-workflow-diagram", ["mj-node-select"])

    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-workflow-diagram');
            const node = el.shadowRoot.querySelector('[part=state-node],[part=state-node-current]');
            if (node !== null) {
                node.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
            }
        }"""
    )

    events = frame.evaluate("() => window.__mjevents")
    assert "mj-node-select" in events

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_workflow_diagram_rework_loop_layout(page, base_url):
    """
        The catalog example has an approve -> draft rework loop. Every state
        still gets its own column in flow order, and the loop is drawn as a
        return edge.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-workflow-diagram")
    _force_draw(frame, "mj-workflow-diagram")
    _wait_for_shadow(frame, "mj-workflow-diagram", "[part=state-node]")

    result = frame.evaluate(
        """() => {
            const sr = document.querySelector('mj-workflow-diagram').shadowRoot;
            const nodes = Array.from(sr.querySelectorAll('[data-mark^="node:"]'));
            const xs = nodes.map((n) => { const b = n.querySelector('.node-frame').getBBox(); return Math.round(b.x + b.width / 2); });
            const dashed = Array.from(sr.querySelectorAll('.edge-line')).filter((p) => p.getAttribute('stroke-dasharray') !== 'none').length;
            return { xs: xs, dashed: dashed, wrapperRole: sr.querySelector('.wrapper').getAttribute('role') };
        }"""
    )

    assert len(set(result["xs"])) == 6
    assert result["xs"] == sorted(result["xs"])
    assert result["dashed"] == 1
    assert result["wrapperRole"] == "group"

    return


# ---------------------------------------------------------------------------
# mj-release-calendar
# ---------------------------------------------------------------------------

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_release_calendar_grid_rendered(page, base_url):
    """
        mj-release-calendar renders a calendar grid of day cells.

        The release calendar does not use the .data setter pattern;
        it renders its grid in afterRender and on each data assignment.
        The grid is visible immediately.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-release-calendar")
    _wait_for_shadow(frame, "mj-release-calendar", "[part=day-cell]")

    count = _shadow_count(frame, "mj-release-calendar", "[part=day-cell]")
    assert count >= 28

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_release_calendar_accessible_list_present(page, base_url):
    """
        mj-release-calendar includes an accessible ordered list of events.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-release-calendar")
    assert _shadow_exists(frame, "mj-release-calendar", "ol[part=a11y-list]") is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_release_calendar_event_chips_present(page, base_url):
    """
        mj-release-calendar renders event chips for events in the visible month.

        The example's events are dated relative to today (one of them today)
        and the calendar opens on the current month, so chips are visible on
        first render without navigating.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-release-calendar")
    _force_draw(frame, "mj-release-calendar")

    _wait_for_shadow(frame, "mj-release-calendar", "[part=event-chip]")

    count = _shadow_count(frame, "mj-release-calendar", "[part=event-chip]")
    assert count >= 1

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_release_calendar_event_select_event(page, base_url):
    """
        Clicking an event chip fires the mj-event-select event.

        The calendar opens on the current month, which holds the example's
        events dated around today, so chips are visible without navigating.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-release-calendar")
    _force_draw(frame, "mj-release-calendar")

    _wait_for_shadow(frame, "mj-release-calendar", "[part=event-chip]")

    _collect_events(frame, "mj-release-calendar", ["mj-event-select"])

    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-release-calendar');
            const chip = el.shadowRoot.querySelector('[part=event-chip]');
            if (chip !== null) { chip.click(); }
        }"""
    )

    events = frame.evaluate("() => window.__mjevents")
    assert "mj-event-select" in events

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_release_calendar_local_days_and_safe_links(page, base_url):
    """
        current-date="2026-05-01" opens May whatever the time zone, an event
        dated 2026-05-08 sits in the 8 May cell, and javascript: URLs are not
        rendered as links while http(s) links get rel="noopener noreferrer".

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-release-calendar")
    result = frame.evaluate(
        """async ([payload]) => {
            const el = document.querySelector('mj-release-calendar');
            el.setAttribute('current-date', '2026-05-01');
            el.data = { events: [
                { id: 'bad', name: 'Bad', type: payload, startDate: '2026-05-08', url: 'javascript:top.__hits=1' },
                { id: 'ok', name: 'Ok', type: 'release', startDate: '2026-05-12', url: 'https://example.com/r' }
            ] };
            await new Promise((r) => setTimeout(r, 100));
            const sr = el.shadowRoot;
            const chipIn = (day) => sr.querySelector(`.day-cell[data-day="${day}"] .event-chip`);
            const title = sr.querySelector('.cal-title').textContent;
            const onEighth = chipIn('2026-05-08') !== null;
            chipIn('2026-05-08').click();
            const badLink = sr.querySelector('.detail-content a');
            chipIn('2026-05-12').click();
            const okLink = sr.querySelector('.detail-content a');
            return {
                title: title, onEighth: onEighth, onNinth: chipIn('2026-05-09') !== null,
                badLink: badLink !== null, okRel: okLink !== null ? okLink.getAttribute('rel') : null,
                images: sr.querySelectorAll('img').length, hits: top.__hits === undefined ? 0 : top.__hits
            };
        }""",
        [_INJECTION],
    )

    assert "May" in result["title"] and "2026" in result["title"]
    assert result["onEighth"] is True
    assert result["onNinth"] is False
    assert result["badLink"] is False
    assert result["okRel"] == "noopener noreferrer"
    assert result["images"] == 0
    assert result["hits"] == 0

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_release_calendar_shows_empty_and_error_states(page, base_url):
    """
        Without events the calendar shows its empty state (the `empty` slot)
        above a navigable grid; malformed or non-object inline JSON shows the
        error there, which stays while the user pages through months and
        goes away when data is assigned.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-release-calendar")
    result = frame.evaluate(
        """async () => {
            const errors = [];
            document.addEventListener('mj-error', (event) => errors.push(event.target.id), true);
            document.body.innerHTML =
                '<mj-release-calendar id="empty"><span slot="empty">No releases yet.</span></mj-release-calendar>' +
                '<mj-release-calendar id="broken"><script type="application/json">{ "events": [ </' + 'script></mj-release-calendar>' +
                '<mj-release-calendar id="number"><script type="application/json">42</' + 'script></mj-release-calendar>';
            await new Promise((resolve) => setTimeout(resolve, 300));
            const state = (id) => {
                const root = document.getElementById(id).shadowRoot;
                const block = root.querySelector('[part=empty-state]');
                return { state: block.getAttribute('data-state'), hidden: block.hidden,
                         cells: root.querySelectorAll('[part~=day-cell]').length };
            };
            const before = { empty: state('empty'), broken: state('broken'), number: state('number') };
            document.getElementById('broken').shadowRoot.querySelector('.next-btn').click();
            const afterPaging = state('broken');
            document.getElementById('broken').data = { events: [{ name: 'R1', type: 'release', startDate: '2026-11-12' }] };
            const afterData = state('broken');
            return { before: before, afterPaging: afterPaging, afterData: afterData, errors: errors.sort() };
        }"""
    )

    before = result["before"]
    assert before["empty"]["state"] == "empty" and before["empty"]["hidden"] is False, f"empty: {result}"
    assert before["empty"]["cells"] >= 28, f"the grid stays: {result}"
    assert before["broken"]["state"] == "error" and before["number"]["state"] == "error", f"errors: {result}"
    assert result["errors"] == ["broken", "number"], f"mj-error: {result}"
    assert result["afterPaging"]["state"] == "error", f"paging dropped the error: {result}"
    assert result["afterData"]["state"] == "ready" and result["afterData"]["hidden"] is True, f"data: {result}"

    return


# ---------------------------------------------------------------------------
# mj-env-promotion-chart
# ---------------------------------------------------------------------------

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_env_promotion_chart_env_columns_rendered(page, base_url):
    """
        mj-env-promotion-chart renders one environment column per environment.

        The example has 3 environments.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-env-promotion-chart")
    _force_draw(frame, "mj-env-promotion-chart")
    _wait_for_shadow(frame, "mj-env-promotion-chart", "[part=environment-column]")

    count = _shadow_count(frame, "mj-env-promotion-chart", "[part=environment-column]")
    assert count >= 3

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_env_promotion_chart_accessible_list_present(page, base_url):
    """
        mj-env-promotion-chart includes an accessible ordered list.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-env-promotion-chart")
    assert _shadow_exists(frame, "mj-env-promotion-chart", "ol[part=a11y-list]") is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_env_promotion_chart_pending_gate_approve_button(page, base_url):
    """
        mj-env-promotion-chart renders Approve and Reject buttons for pending gates.

        The example has one pending gate (fromEnv='staging') and is not
        readonly, so inline approval buttons should appear.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-env-promotion-chart")
    _force_draw(frame, "mj-env-promotion-chart")
    _wait_for_shadow(frame, "mj-env-promotion-chart", ".gate-approve")

    assert _shadow_exists(frame, "mj-env-promotion-chart", ".gate-approve") is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_env_promotion_chart_environment_select_event(page, base_url):
    """
        Clicking an environment column fires the mj-environment-select event.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-env-promotion-chart")
    _force_draw(frame, "mj-env-promotion-chart")
    _wait_for_shadow(frame, "mj-env-promotion-chart", "[part=environment-column]")

    _collect_events(frame, "mj-env-promotion-chart", ["mj-environment-select"])

    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-env-promotion-chart');
            const col = el.shadowRoot.querySelector('[part=environment-column]');
            if (col !== null) { col.click(); }
        }"""
    )

    events = frame.evaluate("() => window.__mjevents")
    assert "mj-environment-select" in events

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_env_promotion_chart_gate_action_event(page, base_url):
    """
        Clicking the Approve button fires the mj-gate-action event.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-env-promotion-chart")
    _force_draw(frame, "mj-env-promotion-chart")
    _wait_for_shadow(frame, "mj-env-promotion-chart", ".gate-approve")

    _collect_events(frame, "mj-env-promotion-chart", ["mj-gate-action"])

    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-env-promotion-chart');
            const btn = el.shadowRoot.querySelector('.gate-approve');
            if (btn !== null) { btn.click(); }
        }"""
    )

    events = frame.evaluate("() => window.__mjevents")
    assert "mj-gate-action" in events

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_env_promotion_chart_gate_decision_keeps_focus_and_data(page, base_url):
    """
        Approving a gate keeps focus on the gate, states the new status in
        its label, and leaves the host's data object unchanged. The wrapper
        is no longer role=img.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-env-promotion-chart")
    _force_draw(frame, "mj-env-promotion-chart")
    _wait_for_shadow(frame, "mj-env-promotion-chart", ".gate-approve")

    result = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-env-promotion-chart');
            const sr = el.shadowRoot;
            const button = sr.querySelector('.gate-approve');
            button.focus();
            button.click();
            const active = sr.activeElement;
            return {
                wrapperRole: sr.querySelector('.wrapper').getAttribute('role'),
                focusLabel: active !== null ? active.getAttribute('aria-label') : null,
                hostStatus: el.data.gates[1].status,
                pending: el.pendingGates.length
            };
        }"""
    )

    assert result["wrapperRole"] != "img"
    assert result["focusLabel"] is not None and "Approved" in result["focusLabel"]
    assert result["hostStatus"] == "pending"
    assert result["pending"] == 0

    return


# ---------------------------------------------------------------------------
# mj-build-status-board
# ---------------------------------------------------------------------------

@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_build_status_board_table_rendered(page, base_url):
    """
        mj-build-status-board renders a table with data rows.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-build-status-board")
    _force_draw(frame, "mj-build-status-board")
    _wait_for_shadow(frame, "mj-build-status-board", "[part=data-row]")

    count = _shadow_count(frame, "mj-build-status-board", "[part=data-row]")
    assert count >= 6

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_build_status_board_status_badges_present(page, base_url):
    """
        mj-build-status-board renders a status badge in each data row.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-build-status-board")
    _force_draw(frame, "mj-build-status-board")
    _wait_for_shadow(frame, "mj-build-status-board", "[part=status-badge]")

    count = _shadow_count(frame, "mj-build-status-board", "[part=status-badge]")
    assert count >= 6

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_build_status_board_filter_bar_present(page, base_url):
    """
        mj-build-status-board renders a filter bar with a status select.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-build-status-board")
    assert _shadow_exists(frame, "mj-build-status-board", "[part=filter-bar]") is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_build_status_board_sort_on_header_click(page, base_url):
    """
        Clicking the 'Status' column header fires the mj-sort-change event.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-build-status-board")
    _force_draw(frame, "mj-build-status-board")
    _wait_for_shadow(frame, "mj-build-status-board", "th[data-col=status]")

    _collect_events(frame, "mj-build-status-board", ["mj-sort-change"])

    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-build-status-board');
            const th = el.shadowRoot.querySelector('th[data-col=status]');
            if (th !== null) { th.click(); }
        }"""
    )

    events = frame.evaluate("() => window.__mjevents")
    assert "mj-sort-change" in events

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_build_status_board_row_select_event(page, base_url):
    """
        Checking a row checkbox fires the mj-row-select event.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-build-status-board")
    _force_draw(frame, "mj-build-status-board")
    _wait_for_shadow(frame, "mj-build-status-board", "[part=data-row]")

    _collect_events(frame, "mj-build-status-board", ["mj-row-select"])

    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-build-status-board');
            const chk = el.shadowRoot.querySelector('[part=data-row] input[type=checkbox]');
            if (chk !== null) { chk.click(); }
        }"""
    )

    events = frame.evaluate("() => window.__mjevents")
    assert "mj-row-select" in events

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_build_status_board_pagination_controls_present(page, base_url):
    """
        mj-build-status-board renders pagination controls.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-build-status-board")
    assert _shadow_exists(frame, "mj-build-status-board", "[part=pagination]") is True

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_build_status_board_attribute_change_keeps_user_sort_and_filter(page, base_url):
    """
        Changing density, group-by or page-size keeps the sort the user
        picked with a header and the filter chosen in the filter bar; a
        filter attribute change still applies and syncs the controls.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-build-status-board")
    _force_draw(frame, "mj-build-status-board")
    _wait_for_shadow(frame, "mj-build-status-board", "[part=data-row]")
    result = frame.evaluate(
        """async () => {
            const board = document.querySelector('mj-build-status-board');
            const sr = board.shadowRoot;
            board.data = { rows: [
                { id: '1', name: 'web / build', status: 'passed', lastRun: '2026-11-10T10:00:00Z' },
                { id: '2', name: 'api / build', status: 'failed', lastRun: '2026-11-10T11:00:00Z' },
                { id: '3', name: 'docs / publish', status: 'failed', lastRun: '2026-11-10T09:00:00Z' }
            ] };
            sr.querySelector('th[data-col=name] button').click();
            const select = sr.querySelector('.filter-status');
            select.value = 'failed';
            select.dispatchEvent(new Event('change', { bubbles: true }));
            board.setAttribute('density', 'compact');
            board.setAttribute('group-by', 'status');
            board.setAttribute('page-size', '10');
            await new Promise((resolve) => setTimeout(resolve, 50));
            const kept = {
                names: board.filteredRows.map((row) => row.name),
                select: select.value,
                nameSort: sr.querySelector('th[data-col=name]').getAttribute('aria-sort')
            };
            board.setAttribute('filter-status', 'passed');
            await new Promise((resolve) => setTimeout(resolve, 50));
            return { kept: kept, attr: { names: board.filteredRows.map((row) => row.name), select: select.value } };
        }"""
    )

    assert result["kept"]["names"] == ["api / build", "docs / publish"], f"filter or sort reset: {result}"
    assert result["kept"]["select"] == "failed", f"filter control: {result}"
    assert result["kept"]["nameSort"] == "ascending", f"sort reset: {result}"
    assert result["attr"] == {"names": ["web / build"], "select": "passed"}, f"filter attribute: {result}"

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_build_status_board_filters_without_match_say_so(page, base_url):
    """
        When the board has rows but the filters match none, the empty state
        says that no pipeline matches the filters (not "No data"); without
        rows it shows the empty state.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-build-status-board")
    _force_draw(frame, "mj-build-status-board")
    _wait_for_shadow(frame, "mj-build-status-board", "[part=data-row]")
    result = frame.evaluate(
        """async () => {
            const board = document.querySelector('mj-build-status-board');
            const sr = board.shadowRoot;
            const block = sr.querySelector('[part=empty-state]');
            const input = sr.querySelector('.filter-pattern');
            input.value = 'no-such-pipeline';
            input.dispatchEvent(new Event('input', { bubbles: true }));
            await new Promise((resolve) => setTimeout(resolve, 50));
            const noMatch = { state: block.getAttribute('data-state'), text: block.innerText.trim() };
            board.data = { rows: [] };
            await new Promise((resolve) => setTimeout(resolve, 50));
            return { noMatch: noMatch, empty: block.getAttribute('data-state') };
        }"""
    )

    assert result["noMatch"]["state"] == "no-match", f"state: {result}"
    assert "match" in result["noMatch"]["text"] and "No data" not in result["noMatch"]["text"], f"text: {result}"
    assert result["empty"] == "empty", f"no rows: {result}"

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
