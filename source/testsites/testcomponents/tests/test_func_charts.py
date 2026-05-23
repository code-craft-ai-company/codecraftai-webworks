"""
    test_func_charts.py

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

import pytest
from playwright.sync_api import expect


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

@pytest.mark.functional
def test_branch_graph_svg_rendered(page, base_url):
    """
        mj-branch-graph renders an SVG in its shadow DOM.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-branch-graph")
    assert _shadow_exists(frame, "mj-branch-graph", "svg") is True

    return


@pytest.mark.functional
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


@pytest.mark.functional
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


@pytest.mark.functional
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


@pytest.mark.functional
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


@pytest.mark.functional
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


# ---------------------------------------------------------------------------
# mj-pipeline-chart
# ---------------------------------------------------------------------------

@pytest.mark.functional
def test_pipeline_chart_svg_rendered(page, base_url):
    """
        mj-pipeline-chart renders an SVG in its shadow DOM.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-pipeline-chart")
    assert _shadow_exists(frame, "mj-pipeline-chart", "svg") is True

    return


@pytest.mark.functional
def test_pipeline_chart_accessible_list_present(page, base_url):
    """
        mj-pipeline-chart always renders an accessible ordered list.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-pipeline-chart")
    assert _shadow_exists(frame, "mj-pipeline-chart", "ol[part=a11y-list]") is True

    return


@pytest.mark.functional
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


@pytest.mark.functional
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


@pytest.mark.functional
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


# ---------------------------------------------------------------------------
# mj-gantt-chart
# ---------------------------------------------------------------------------

@pytest.mark.functional
def test_gantt_chart_svg_rendered(page, base_url):
    """
        mj-gantt-chart renders an SVG in its shadow DOM.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-gantt-chart")
    assert _shadow_exists(frame, "mj-gantt-chart", "svg") is True

    return


@pytest.mark.functional
def test_gantt_chart_accessible_table_present(page, base_url):
    """
        mj-gantt-chart always includes a data table in the shadow DOM.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-gantt-chart")
    assert _shadow_exists(frame, "mj-gantt-chart", "table[part=data-table]") is True

    return


@pytest.mark.functional
def test_gantt_chart_task_bars_present(page, base_url):
    """
        mj-gantt-chart renders task bars for all 6 tasks in the example.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-gantt-chart")
    _force_draw(frame, "mj-gantt-chart")
    _wait_for_shadow(frame, "mj-gantt-chart", "[part=task-bar]")

    count = _shadow_count(frame, "mj-gantt-chart", "[part=task-bar]")
    assert count >= 6

    return


@pytest.mark.functional
def test_gantt_chart_dependency_arrows_present(page, base_url):
    """
        mj-gantt-chart renders dependency arrows between tasks.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-gantt-chart")
    _force_draw(frame, "mj-gantt-chart")
    _wait_for_shadow(frame, "mj-gantt-chart", "[part=dependency-arrow]")

    assert _shadow_exists(frame, "mj-gantt-chart", "[part=dependency-arrow]") is True

    return


@pytest.mark.functional
def test_gantt_chart_task_select_event(page, base_url):
    """
        Clicking a task bar fires the mj-task-select event.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-gantt-chart")
    _force_draw(frame, "mj-gantt-chart")
    _wait_for_shadow(frame, "mj-gantt-chart", "[part=task-bar]")

    _collect_events(frame, "mj-gantt-chart", ["mj-task-select"])

    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-gantt-chart');
            const bar = el.shadowRoot.querySelector('[part=task-bar]');
            if (bar !== null) {
                bar.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
            }
        }"""
    )

    events = frame.evaluate("() => window.__mjevents")
    assert "mj-task-select" in events

    return


# ---------------------------------------------------------------------------
# mj-roadmap-chart
# ---------------------------------------------------------------------------

@pytest.mark.functional
def test_roadmap_chart_svg_rendered(page, base_url):
    """
        mj-roadmap-chart renders an SVG in its shadow DOM.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-roadmap-chart")
    assert _shadow_exists(frame, "mj-roadmap-chart", "svg") is True

    return


@pytest.mark.functional
def test_roadmap_chart_accessible_table_present(page, base_url):
    """
        mj-roadmap-chart includes a data table in the shadow DOM.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-roadmap-chart")
    assert _shadow_exists(frame, "mj-roadmap-chart", "table[part=data-table]") is True

    return


@pytest.mark.functional
def test_roadmap_chart_initiative_bars_present(page, base_url):
    """
        mj-roadmap-chart renders initiative bars for all 6 initiatives.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-roadmap-chart")
    _force_draw(frame, "mj-roadmap-chart")
    _wait_for_shadow(frame, "mj-roadmap-chart", "[part=initiative-bar]")

    count = _shadow_count(frame, "mj-roadmap-chart", "[part=initiative-bar]")
    assert count >= 6

    return


@pytest.mark.functional
def test_roadmap_chart_column_headers_present(page, base_url):
    """
        mj-roadmap-chart renders column headers for the bucket columns.

        The example has 4 quarters (Q1-Q4 2026).

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-roadmap-chart")
    _force_draw(frame, "mj-roadmap-chart")
    _wait_for_shadow(frame, "mj-roadmap-chart", "[part=column-header]")

    count = _shadow_count(frame, "mj-roadmap-chart", "[part=column-header]")
    assert count >= 4

    return


@pytest.mark.functional
def test_roadmap_chart_initiative_select_event(page, base_url):
    """
        Clicking an initiative bar fires the mj-initiative-select event.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-roadmap-chart")
    _force_draw(frame, "mj-roadmap-chart")
    _wait_for_shadow(frame, "mj-roadmap-chart", "[part=initiative-bar]")

    _collect_events(frame, "mj-roadmap-chart", ["mj-initiative-select"])

    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-roadmap-chart');
            const bar = el.shadowRoot.querySelector('[part=initiative-bar]');
            if (bar !== null) {
                bar.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
            }
        }"""
    )

    events = frame.evaluate("() => window.__mjevents")
    assert "mj-initiative-select" in events

    return


# ---------------------------------------------------------------------------
# mj-milestone-timeline
# ---------------------------------------------------------------------------

@pytest.mark.functional
def test_milestone_timeline_svg_rendered(page, base_url):
    """
        mj-milestone-timeline renders an SVG in its shadow DOM.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-milestone-timeline")
    assert _shadow_exists(frame, "mj-milestone-timeline", "svg") is True

    return


@pytest.mark.functional
def test_milestone_timeline_accessible_list_present(page, base_url):
    """
        mj-milestone-timeline includes an accessible ordered list.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-milestone-timeline")
    assert _shadow_exists(frame, "mj-milestone-timeline", "ol[part=a11y-list]") is True

    return


@pytest.mark.functional
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


@pytest.mark.functional
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


@pytest.mark.functional
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


# ---------------------------------------------------------------------------
# mj-burndown-chart
# ---------------------------------------------------------------------------

@pytest.mark.functional
def test_burndown_chart_svg_rendered(page, base_url):
    """
        mj-burndown-chart renders an SVG in its shadow DOM.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-burndown-chart")
    assert _shadow_exists(frame, "mj-burndown-chart", "svg") is True

    return


@pytest.mark.functional
def test_burndown_chart_accessible_table_present(page, base_url):
    """
        mj-burndown-chart always includes a data table in the shadow DOM.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-burndown-chart")
    assert _shadow_exists(frame, "mj-burndown-chart", "table[part=data-table]") is True

    return


@pytest.mark.functional
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


@pytest.mark.functional
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


@pytest.mark.functional
def test_burndown_chart_data_points_rendered(page, base_url):
    """
        mj-burndown-chart renders clickable data-point circles for past values.

        The example has 11 daily values ending 2026-05-15, all in the past.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-burndown-chart")
    _force_draw(frame, "mj-burndown-chart")
    _wait_for_shadow(frame, "mj-burndown-chart", "[part=data-point]")

    count = _shadow_count(frame, "mj-burndown-chart", "[part=data-point]")
    assert count >= 1

    return


@pytest.mark.functional
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


# ---------------------------------------------------------------------------
# mj-cumulative-flow
# ---------------------------------------------------------------------------

@pytest.mark.functional
def test_cumulative_flow_svg_rendered(page, base_url):
    """
        mj-cumulative-flow renders an SVG in its shadow DOM.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-cumulative-flow")
    assert _shadow_exists(frame, "mj-cumulative-flow", "svg") is True

    return


@pytest.mark.functional
def test_cumulative_flow_accessible_table_present(page, base_url):
    """
        mj-cumulative-flow includes a data table in the shadow DOM.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-cumulative-flow")
    assert _shadow_exists(frame, "mj-cumulative-flow", "table[part=data-table]") is True

    return


@pytest.mark.functional
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


@pytest.mark.functional
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


@pytest.mark.functional
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


# ---------------------------------------------------------------------------
# mj-velocity-chart
# ---------------------------------------------------------------------------

@pytest.mark.functional
def test_velocity_chart_svg_rendered(page, base_url):
    """
        mj-velocity-chart renders an SVG in its shadow DOM.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-velocity-chart")
    assert _shadow_exists(frame, "mj-velocity-chart", "svg") is True

    return


@pytest.mark.functional
def test_velocity_chart_accessible_table_present(page, base_url):
    """
        mj-velocity-chart includes a data table in the shadow DOM.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-velocity-chart")
    assert _shadow_exists(frame, "mj-velocity-chart", "table[part=data-table]") is True

    return


@pytest.mark.functional
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


@pytest.mark.functional
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


@pytest.mark.functional
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


# ---------------------------------------------------------------------------
# mj-dependency-graph
# ---------------------------------------------------------------------------

@pytest.mark.functional
def test_dependency_graph_svg_rendered(page, base_url):
    """
        mj-dependency-graph renders an SVG in its shadow DOM.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-dependency-graph")
    assert _shadow_exists(frame, "mj-dependency-graph", "svg") is True

    return


@pytest.mark.functional
def test_dependency_graph_accessible_list_present(page, base_url):
    """
        mj-dependency-graph includes an accessible definition list.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-dependency-graph")
    assert _shadow_exists(frame, "mj-dependency-graph", "dl[part=a11y-list]") is True

    return


@pytest.mark.functional
def test_dependency_graph_nodes_present(page, base_url):
    """
        mj-dependency-graph renders one node element per graph node.

        The example has 7 nodes; critical path nodes use
        part='critical-path-node'.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-dependency-graph")
    _force_draw(frame, "mj-dependency-graph")
    frame.wait_for_function(
        """() => {
            const el = document.querySelector('mj-dependency-graph');
            if (el === null || el.shadowRoot === null) { return false; }
            const nodes = el.shadowRoot.querySelectorAll('[part=node],[part=critical-path-node]');
            return nodes.length >= 7;
        }""",
        timeout=10000,
    )

    count_nodes = _shadow_count(frame, "mj-dependency-graph", "[part=node]")
    count_crit = _shadow_count(frame, "mj-dependency-graph", "[part=critical-path-node]")
    assert (count_nodes + count_crit) >= 7

    return


@pytest.mark.functional
def test_dependency_graph_critical_path_highlighted(page, base_url):
    """
        mj-dependency-graph highlights critical-path nodes with amber border.

        The example provides 5 critical-path nodes.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-dependency-graph")
    _force_draw(frame, "mj-dependency-graph")
    _wait_for_shadow(frame, "mj-dependency-graph", "[part=critical-path-node]")

    count = _shadow_count(frame, "mj-dependency-graph", "[part=critical-path-node]")
    assert count >= 5

    return


@pytest.mark.functional
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
            return el.shadowRoot.querySelectorAll('[part=node],[part=critical-path-node]').length >= 1;
        }""",
        timeout=10000,
    )

    _collect_events(frame, "mj-dependency-graph", ["mj-node-select"])

    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-dependency-graph');
            const node = el.shadowRoot.querySelector('[part=node],[part=critical-path-node]');
            if (node !== null) {
                node.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
            }
        }"""
    )

    events = frame.evaluate("() => window.__mjevents")
    assert "mj-node-select" in events

    return


# ---------------------------------------------------------------------------
# mj-workflow-diagram
# ---------------------------------------------------------------------------

@pytest.mark.functional
def test_workflow_diagram_svg_rendered(page, base_url):
    """
        mj-workflow-diagram renders an SVG in its shadow DOM.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-workflow-diagram")
    assert _shadow_exists(frame, "mj-workflow-diagram", "svg") is True

    return


@pytest.mark.functional
def test_workflow_diagram_accessible_list_present(page, base_url):
    """
        mj-workflow-diagram includes an accessible definition list.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-workflow-diagram")
    assert _shadow_exists(frame, "mj-workflow-diagram", "dl[part=a11y-list]") is True

    return


@pytest.mark.functional
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


@pytest.mark.functional
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


@pytest.mark.functional
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


# ---------------------------------------------------------------------------
# mj-release-calendar
# ---------------------------------------------------------------------------

@pytest.mark.functional
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


@pytest.mark.functional
def test_release_calendar_accessible_list_present(page, base_url):
    """
        mj-release-calendar includes an accessible ordered list of events.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-release-calendar")
    assert _shadow_exists(frame, "mj-release-calendar", "ol[part=a11y-list]") is True

    return


@pytest.mark.functional
def test_release_calendar_event_chips_present(page, base_url):
    """
        mj-release-calendar renders event chips for events in the visible month.

        The example provides 6 events in May 2026.  The current-date attribute
        is parsed as a UTC midnight date; in non-UTC timezones this may display
        April instead of May.  The test navigates forward one month to ensure
        the May events are visible before asserting chip presence.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-release-calendar")
    _force_draw(frame, "mj-release-calendar")

    # Navigate forward one month to ensure the May events are displayed
    # regardless of the local timezone offset applied to the current-date attribute.
    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-release-calendar');
            const btn = el.shadowRoot.querySelector('.next-btn');
            if (btn !== null) { btn.click(); }
        }"""
    )

    _wait_for_shadow(frame, "mj-release-calendar", "[part=event-chip]")

    count = _shadow_count(frame, "mj-release-calendar", "[part=event-chip]")
    assert count >= 1

    return


@pytest.mark.functional
def test_release_calendar_event_select_event(page, base_url):
    """
        Clicking an event chip fires the mj-event-select event.

        The test navigates forward one month so that May 2026 events are
        visible as chips before interacting.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-release-calendar")
    _force_draw(frame, "mj-release-calendar")

    # Navigate forward one month to ensure May events are visible.
    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-release-calendar');
            const btn = el.shadowRoot.querySelector('.next-btn');
            if (btn !== null) { btn.click(); }
        }"""
    )

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


# ---------------------------------------------------------------------------
# mj-env-promotion-chart
# ---------------------------------------------------------------------------

@pytest.mark.functional
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


@pytest.mark.functional
def test_env_promotion_chart_accessible_list_present(page, base_url):
    """
        mj-env-promotion-chart includes an accessible ordered list.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-env-promotion-chart")
    assert _shadow_exists(frame, "mj-env-promotion-chart", "ol[part=a11y-list]") is True

    return


@pytest.mark.functional
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


@pytest.mark.functional
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


@pytest.mark.functional
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


# ---------------------------------------------------------------------------
# mj-build-status-board
# ---------------------------------------------------------------------------

@pytest.mark.functional
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


@pytest.mark.functional
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


@pytest.mark.functional
def test_build_status_board_filter_bar_present(page, base_url):
    """
        mj-build-status-board renders a filter bar with a status select.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-build-status-board")
    assert _shadow_exists(frame, "mj-build-status-board", "[part=filter-bar]") is True

    return


@pytest.mark.functional
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


@pytest.mark.functional
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


@pytest.mark.functional
def test_build_status_board_pagination_controls_present(page, base_url):
    """
        mj-build-status-board renders pagination controls.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-build-status-board")
    assert _shadow_exists(frame, "mj-build-status-board", "[part=pagination]") is True

    return
