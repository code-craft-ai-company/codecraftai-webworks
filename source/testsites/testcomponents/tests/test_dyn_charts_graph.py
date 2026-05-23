"""
    test_dyn_charts_graph.py

    Functional Playwright tests for the five graph/flow-chart components:

      mj-branch-graph      -- branch network / commit history graph
      mj-pipeline-chart    -- CI/CD pipeline stage-flow diagram
      mj-dependency-graph  -- directed node/edge dependency graph
      mj-workflow-diagram  -- state machine / swimlane process flow
      mj-env-promotion-chart -- artifact environment promotion chart

    Each component is tested for:
      * initial render -- set data, assert shadow DOM contains expected SVG elements
      * dynamic update -- set data A, measure; set data B, assert the SVG changed
      * interactivity  -- install event collector, click node/stage/state, assert event

    Key fixture facts
    -----------------
    - ``base_url`` and ``page`` come from conftest.py.
    - Pages live at /components/charts/<tag>.
    - The playground preview iframe has data-testid="playground-preview".
    - The inline <script> may assign .data before the element upgrades, creating
      an own property that shadows the prototype setter.  All tests call
      ``_force_draw`` to delete the own property and re-assign through the setter.
    - SVG elements (<g>, <circle>, <rect>) lack a native .click(); a MouseEvent
      is dispatched via frame.evaluate with bubbles:true so delegated handlers fire.
"""

import pytest


# ---------------------------------------------------------------------------
# Shared helpers (mirrors the pattern in test_func_charts.py)
# ---------------------------------------------------------------------------

def _open_chart(page, base_url: str, tag: str):
    """
        Navigate to the component playground page and return a ready Frame.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
        :param tag: The custom element tag name.

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


def _force_draw(frame, tag: str, data=None) -> None:
    """
        Re-trigger the component draw by deleting any shadowing own property
        and re-assigning .data through the prototype setter.

        When ``data`` is None the current value is reused (round-trip).
        When ``data`` is provided it is passed as the new value.

        :param frame: The Playwright Frame containing the element.
        :param tag: The host custom-element tag name.
        :param data: Optional new data object to assign.
    """

    if data is None:
        frame.evaluate(
            """tag => {
                const el = document.querySelector(tag);
                if (el === null) { return; }
                const saved = el.hasOwnProperty('data') ? el.data : el.data;
                delete el.data;
                el.data = saved;
            }""",
            tag,
        )
    else:
        frame.evaluate(
            """([tag, newData]) => {
                const el = document.querySelector(tag);
                if (el === null) { return; }
                delete el.data;
                el.data = newData;
            }""",
            [tag, data],
        )
    return


def _shadow_count(frame, tag: str, selector: str) -> int:
    """
        Count elements matching a CSS selector inside the shadow root.

        :param frame: The Playwright Frame.
        :param tag: The host custom-element tag name.
        :param selector: CSS selector to query inside the shadow root.

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

    return _shadow_count(frame, tag, selector) > 0


def _wait_for_shadow(frame, tag: str, selector: str, timeout: int = 10000) -> None:
    """
        Wait until at least one element matching selector exists in the shadow root.

        :param frame: The Playwright Frame.
        :param tag: The host element tag.
        :param selector: CSS selector to look for inside the shadow root.
        :param timeout: Maximum wait in milliseconds.
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


def _collect_events(frame, tag: str, event_names: list) -> None:
    """
        Install a window.__mjevents collector for the given event names.

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


# ---------------------------------------------------------------------------
# mj-branch-graph
# ---------------------------------------------------------------------------

_BRANCH_GRAPH_DATA_A = {
    "branches": [
        {"id": "main", "name": "main"},
        {"id": "feat", "name": "feature"},
    ],
    "commits": [
        {"id": "c1", "sha": "aaa0001", "branch": "main",  "date": "2026-01-01", "message": "init",    "author": "alice"},
        {"id": "c2", "sha": "aaa0002", "branch": "feat",  "date": "2026-01-03", "message": "branch",  "author": "bob"},
        {"id": "c3", "sha": "aaa0003", "branch": "main",  "date": "2026-01-05", "message": "fix",     "author": "alice"},
    ],
    "merges": [{"from": "c2", "to": "c3"}],
    "markers": [{"name": "v1.0", "date": "2026-01-05", "type": "release"}],
    "phases": [],
}

_BRANCH_GRAPH_DATA_B = {
    "branches": [
        {"id": "main", "name": "main"},
        {"id": "feat", "name": "feature"},
        {"id": "hot",  "name": "hotfix"},
    ],
    "commits": [
        {"id": "d1", "sha": "bbb0001", "branch": "main",  "date": "2026-02-01", "message": "start",  "author": "alice"},
        {"id": "d2", "sha": "bbb0002", "branch": "feat",  "date": "2026-02-02", "message": "feat-a", "author": "bob"},
        {"id": "d3", "sha": "bbb0003", "branch": "hot",   "date": "2026-02-03", "message": "hot",    "author": "carol"},
        {"id": "d4", "sha": "bbb0004", "branch": "main",  "date": "2026-02-04", "message": "merge",  "author": "alice"},
        {"id": "d5", "sha": "bbb0005", "branch": "feat",  "date": "2026-02-05", "message": "feat-b", "author": "bob"},
    ],
    "merges": [{"from": "d2", "to": "d4"}],
    "markers": [],
    "phases": [],
}


@pytest.mark.functional
def test_branch_graph_initial_render(page, base_url):
    """
        mj-branch-graph renders commit-node circles after .data is assigned.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-branch-graph")
    _force_draw(frame, "mj-branch-graph", _BRANCH_GRAPH_DATA_A)
    _wait_for_shadow(frame, "mj-branch-graph", "[part=commit-node]")

    count = _shadow_count(frame, "mj-branch-graph", "[part=commit-node]")
    assert count >= 3

    return


@pytest.mark.functional
def test_branch_graph_dynamic_update(page, base_url):
    """
        Reassigning .data on mj-branch-graph re-renders the SVG.

        Data A has 3 commits; data B has 5 commits.  After the update the
        commit-node count must reflect data B.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-branch-graph")

    _force_draw(frame, "mj-branch-graph", _BRANCH_GRAPH_DATA_A)
    _wait_for_shadow(frame, "mj-branch-graph", "[part=commit-node]")
    count_a = _shadow_count(frame, "mj-branch-graph", "[part=commit-node]")

    _force_draw(frame, "mj-branch-graph", _BRANCH_GRAPH_DATA_B)
    frame.wait_for_function(
        """([tag, expected]) => {
            const el = document.querySelector(tag);
            if (el === null || el.shadowRoot === null) { return false; }
            return el.shadowRoot.querySelectorAll('[part=commit-node]').length >= expected;
        }""",
        arg=["mj-branch-graph", 5],
        timeout=10000,
    )
    count_b = _shadow_count(frame, "mj-branch-graph", "[part=commit-node]")

    assert count_b > count_a
    assert count_b >= 5

    return


@pytest.mark.functional
def test_branch_graph_interactivity(page, base_url):
    """
        Clicking a commit node fires the mj-node-select event.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-branch-graph")
    _force_draw(frame, "mj-branch-graph", _BRANCH_GRAPH_DATA_A)
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

_PIPELINE_DATA_A = {
    "stages": [
        {"id": "build",  "name": "Build",  "status": "passed"},
        {"id": "test",   "name": "Test",   "status": "running"},
        {"id": "deploy", "name": "Deploy", "status": "pending"},
    ],
    "gates": [],
    "edges": [
        {"from": "build", "to": "test"},
        {"from": "test",  "to": "deploy"},
    ],
}

_PIPELINE_DATA_B = {
    "stages": [
        {"id": "lint",   "name": "Lint",    "status": "passed"},
        {"id": "build",  "name": "Build",   "status": "passed"},
        {"id": "unit",   "name": "Unit",    "status": "passed"},
        {"id": "e2e",    "name": "E2E",     "status": "failed"},
        {"id": "deploy", "name": "Deploy",  "status": "pending"},
    ],
    "gates": [{"fromStage": "unit", "name": "QA Gate", "status": "pending"}],
    "edges": [
        {"from": "lint",  "to": "build"},
        {"from": "build", "to": "unit"},
        {"from": "unit",  "to": "e2e"},
        {"from": "e2e",   "to": "deploy"},
    ],
}


@pytest.mark.functional
def test_pipeline_chart_initial_render(page, base_url):
    """
        mj-pipeline-chart renders one stage-node per stage after .data is set.

        Data A has 3 stages.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-pipeline-chart")
    _force_draw(frame, "mj-pipeline-chart", _PIPELINE_DATA_A)
    _wait_for_shadow(frame, "mj-pipeline-chart", "[part=stage-node]")

    count = _shadow_count(frame, "mj-pipeline-chart", "[part=stage-node]")
    assert count >= 3

    return


@pytest.mark.functional
def test_pipeline_chart_dynamic_update(page, base_url):
    """
        Reassigning .data on mj-pipeline-chart re-renders with new stage count.

        Data A has 3 stages; data B has 5.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-pipeline-chart")

    _force_draw(frame, "mj-pipeline-chart", _PIPELINE_DATA_A)
    _wait_for_shadow(frame, "mj-pipeline-chart", "[part=stage-node]")
    count_a = _shadow_count(frame, "mj-pipeline-chart", "[part=stage-node]")

    _force_draw(frame, "mj-pipeline-chart", _PIPELINE_DATA_B)
    frame.wait_for_function(
        """([tag, expected]) => {
            const el = document.querySelector(tag);
            if (el === null || el.shadowRoot === null) { return false; }
            return el.shadowRoot.querySelectorAll('[part=stage-node]').length >= expected;
        }""",
        arg=["mj-pipeline-chart", 5],
        timeout=10000,
    )
    count_b = _shadow_count(frame, "mj-pipeline-chart", "[part=stage-node]")

    assert count_b > count_a
    assert count_b >= 5

    return


@pytest.mark.functional
def test_pipeline_chart_interactivity(page, base_url):
    """
        Clicking a stage node fires the mj-stage-select event.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-pipeline-chart")
    _force_draw(frame, "mj-pipeline-chart", _PIPELINE_DATA_A)
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
# mj-dependency-graph
# ---------------------------------------------------------------------------

_DEP_GRAPH_DATA_A = {
    "nodes": [
        {"id": "a", "name": "Alpha", "status": "done"},
        {"id": "b", "name": "Beta",  "status": "in-progress"},
        {"id": "c", "name": "Gamma", "status": "todo"},
    ],
    "edges": [
        {"from": "a", "to": "b"},
        {"from": "b", "to": "c"},
    ],
    "criticalPath": ["a", "b", "c"],
}

_DEP_GRAPH_DATA_B = {
    "nodes": [
        {"id": "x", "name": "X-one",   "status": "done"},
        {"id": "y", "name": "Y-two",   "status": "done"},
        {"id": "z", "name": "Z-three", "status": "in-progress"},
        {"id": "w", "name": "W-four",  "status": "blocked"},
        {"id": "v", "name": "V-five",  "status": "todo"},
    ],
    "edges": [
        {"from": "x", "to": "z"},
        {"from": "y", "to": "z"},
        {"from": "z", "to": "w"},
        {"from": "z", "to": "v"},
    ],
    "criticalPath": ["x", "z", "w"],
}


@pytest.mark.functional
def test_dependency_graph_initial_render(page, base_url):
    """
        mj-dependency-graph renders one node element per graph node.

        Data A has 3 nodes including critical-path nodes.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-dependency-graph")
    _force_draw(frame, "mj-dependency-graph", _DEP_GRAPH_DATA_A)
    frame.wait_for_function(
        """() => {
            const el = document.querySelector('mj-dependency-graph');
            if (el === null || el.shadowRoot === null) { return false; }
            return el.shadowRoot.querySelectorAll('[part=node],[part=critical-path-node]').length >= 3;
        }""",
        timeout=10000,
    )

    count = _shadow_count(frame, "mj-dependency-graph", "[part=node]") + \
            _shadow_count(frame, "mj-dependency-graph", "[part=critical-path-node]")
    assert count >= 3

    return


@pytest.mark.functional
def test_dependency_graph_dynamic_update(page, base_url):
    """
        Reassigning .data on mj-dependency-graph re-renders with a new node count.

        Data A has 3 nodes; data B has 5.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-dependency-graph")

    _force_draw(frame, "mj-dependency-graph", _DEP_GRAPH_DATA_A)
    frame.wait_for_function(
        """() => {
            const el = document.querySelector('mj-dependency-graph');
            if (el === null || el.shadowRoot === null) { return false; }
            return el.shadowRoot.querySelectorAll('[part=node],[part=critical-path-node]').length >= 3;
        }""",
        timeout=10000,
    )
    count_a = (
        _shadow_count(frame, "mj-dependency-graph", "[part=node]") +
        _shadow_count(frame, "mj-dependency-graph", "[part=critical-path-node]")
    )

    _force_draw(frame, "mj-dependency-graph", _DEP_GRAPH_DATA_B)
    frame.wait_for_function(
        """() => {
            const el = document.querySelector('mj-dependency-graph');
            if (el === null || el.shadowRoot === null) { return false; }
            return el.shadowRoot.querySelectorAll('[part=node],[part=critical-path-node]').length >= 5;
        }""",
        timeout=10000,
    )
    count_b = (
        _shadow_count(frame, "mj-dependency-graph", "[part=node]") +
        _shadow_count(frame, "mj-dependency-graph", "[part=critical-path-node]")
    )

    assert count_b > count_a
    assert count_b >= 5

    return


@pytest.mark.functional
def test_dependency_graph_interactivity(page, base_url):
    """
        Clicking a node element fires the mj-node-select event.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-dependency-graph")
    _force_draw(frame, "mj-dependency-graph", _DEP_GRAPH_DATA_A)
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

_WORKFLOW_DATA_A = {
    "states": [
        {"id": "open",   "name": "Open",   "type": "start"},
        {"id": "review", "name": "Review", "type": "state"},
        {"id": "closed", "name": "Closed", "type": "end"},
    ],
    "transitions": [
        {"from": "open",   "to": "review", "label": "submit"},
        {"from": "review", "to": "closed", "label": "approve"},
    ],
    "actors": [],
}

_WORKFLOW_DATA_B = {
    "states": [
        {"id": "draft",   "name": "Draft",    "type": "start"},
        {"id": "review",  "name": "Review",   "type": "state"},
        {"id": "approve", "name": "Approved", "type": "state"},
        {"id": "reject",  "name": "Rejected", "type": "state"},
        {"id": "done",    "name": "Done",      "type": "end"},
    ],
    "transitions": [
        {"from": "draft",   "to": "review",  "label": "submit"},
        {"from": "review",  "to": "approve", "label": "approve"},
        {"from": "review",  "to": "reject",  "label": "reject"},
        {"from": "approve", "to": "done",    "label": "close"},
    ],
    "actors": [],
}


@pytest.mark.functional
def test_workflow_diagram_initial_render(page, base_url):
    """
        mj-workflow-diagram renders one node group per state after .data is set.

        Data A has 3 states.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-workflow-diagram")
    _force_draw(frame, "mj-workflow-diagram", _WORKFLOW_DATA_A)
    frame.wait_for_function(
        """() => {
            const el = document.querySelector('mj-workflow-diagram');
            if (el === null || el.shadowRoot === null) { return false; }
            return el.shadowRoot.querySelectorAll('[part=state-node],[part=state-node-current]').length >= 3;
        }""",
        timeout=10000,
    )

    count = (
        _shadow_count(frame, "mj-workflow-diagram", "[part=state-node]") +
        _shadow_count(frame, "mj-workflow-diagram", "[part=state-node-current]")
    )
    assert count >= 3

    return


@pytest.mark.functional
def test_workflow_diagram_dynamic_update(page, base_url):
    """
        Reassigning .data on mj-workflow-diagram re-renders with new state count.

        Data A has 3 states; data B has 5.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-workflow-diagram")

    _force_draw(frame, "mj-workflow-diagram", _WORKFLOW_DATA_A)
    frame.wait_for_function(
        """() => {
            const el = document.querySelector('mj-workflow-diagram');
            if (el === null || el.shadowRoot === null) { return false; }
            return el.shadowRoot.querySelectorAll('[part=state-node],[part=state-node-current]').length >= 3;
        }""",
        timeout=10000,
    )
    count_a = (
        _shadow_count(frame, "mj-workflow-diagram", "[part=state-node]") +
        _shadow_count(frame, "mj-workflow-diagram", "[part=state-node-current]")
    )

    _force_draw(frame, "mj-workflow-diagram", _WORKFLOW_DATA_B)
    frame.wait_for_function(
        """() => {
            const el = document.querySelector('mj-workflow-diagram');
            if (el === null || el.shadowRoot === null) { return false; }
            return el.shadowRoot.querySelectorAll('[part=state-node],[part=state-node-current]').length >= 5;
        }""",
        timeout=10000,
    )
    count_b = (
        _shadow_count(frame, "mj-workflow-diagram", "[part=state-node]") +
        _shadow_count(frame, "mj-workflow-diagram", "[part=state-node-current]")
    )

    assert count_b > count_a
    assert count_b >= 5

    return


@pytest.mark.functional
def test_workflow_diagram_interactivity(page, base_url):
    """
        Clicking a state node fires the mj-node-select event.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-workflow-diagram")
    _force_draw(frame, "mj-workflow-diagram", _WORKFLOW_DATA_A)
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
# mj-env-promotion-chart
# ---------------------------------------------------------------------------

_ENV_PROMO_DATA_A = {
    "environments": [
        {"id": "dev",     "name": "Dev",        "version": "1.0.0", "health": "healthy"},
        {"id": "staging", "name": "Staging",    "version": "0.9.0", "health": "degraded"},
        {"id": "prod",    "name": "Production", "version": "0.8.0", "health": "healthy"},
    ],
    "gates": [
        {"fromEnv": "staging", "name": "Prod Gate", "status": "pending"},
    ],
    "promotions": [],
}

_ENV_PROMO_DATA_B = {
    "environments": [
        {"id": "dev",     "name": "Dev",     "version": "2.0.0", "health": "healthy"},
        {"id": "qa",      "name": "QA",      "version": "1.9.0", "health": "healthy"},
        {"id": "staging", "name": "Staging", "version": "1.8.0", "health": "healthy"},
        {"id": "prod",    "name": "Prod",    "version": "1.7.0", "health": "healthy"},
    ],
    "gates": [
        {"fromEnv": "qa",      "name": "Gate QA-Staging", "status": "approved"},
        {"fromEnv": "staging", "name": "Gate Staging-Prod", "status": "pending"},
    ],
    "promotions": [],
}


@pytest.mark.functional
def test_env_promotion_chart_initial_render(page, base_url):
    """
        mj-env-promotion-chart renders one environment column per environment.

        Data A has 3 environments.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-env-promotion-chart")
    _force_draw(frame, "mj-env-promotion-chart", _ENV_PROMO_DATA_A)
    _wait_for_shadow(frame, "mj-env-promotion-chart", "[part=environment-column]")

    count = _shadow_count(frame, "mj-env-promotion-chart", "[part=environment-column]")
    assert count >= 3

    return


@pytest.mark.functional
def test_env_promotion_chart_dynamic_update(page, base_url):
    """
        Reassigning .data on mj-env-promotion-chart re-renders with new column count.

        Data A has 3 environments; data B has 4.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-env-promotion-chart")

    _force_draw(frame, "mj-env-promotion-chart", _ENV_PROMO_DATA_A)
    _wait_for_shadow(frame, "mj-env-promotion-chart", "[part=environment-column]")
    count_a = _shadow_count(frame, "mj-env-promotion-chart", "[part=environment-column]")

    _force_draw(frame, "mj-env-promotion-chart", _ENV_PROMO_DATA_B)
    frame.wait_for_function(
        """([tag, expected]) => {
            const el = document.querySelector(tag);
            if (el === null || el.shadowRoot === null) { return false; }
            return el.shadowRoot.querySelectorAll('[part=environment-column]').length >= expected;
        }""",
        arg=["mj-env-promotion-chart", 4],
        timeout=10000,
    )
    count_b = _shadow_count(frame, "mj-env-promotion-chart", "[part=environment-column]")

    assert count_b > count_a
    assert count_b >= 4

    return


@pytest.mark.functional
def test_env_promotion_chart_interactivity_env_select(page, base_url):
    """
        Clicking an environment column fires the mj-environment-select event.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-env-promotion-chart")
    _force_draw(frame, "mj-env-promotion-chart", _ENV_PROMO_DATA_A)
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
def test_env_promotion_chart_gate_approve_event(page, base_url):
    """
        Clicking the Approve gate button fires the mj-gate-action event.

        Data A has one pending gate, so Approve and Reject buttons are rendered.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-env-promotion-chart")
    _force_draw(frame, "mj-env-promotion-chart", _ENV_PROMO_DATA_A)
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
