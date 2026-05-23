"""
    test_dyn_charts_progress.py

    Playwright tests covering dynamic updates and interactivity for the four
    progress/metrics chart components in the mj-* library:

      - mj-burndown-chart
      - mj-cumulative-flow
      - mj-velocity-chart
      - mj-build-status-board

    Tests are grouped by component.  Each test navigates independently to
    the playground page, so they are fully isolated.

    Test categories per component
    ------------------------------
    1. Initial render  - set .data via the prototype setter, assert the
                         shadow DOM contains the expected primitives.
    2. Dynamic update  - set data A, measure; set different data B; assert
                         the render changed.
    3. Interactivity   - install an event collector, trigger an interaction,
                         assert the correct mj-* event fired.
                         For mj-build-status-board also covers sort and
                         row-selection interactions.

    Shadow-own-property workaround
    --------------------------------
    The playground example <script> assigns .data before the custom element
    upgrades, which creates a plain own property that shadows the prototype
    setter.  _force_draw() deletes that own property and re-assigns the
    value through the setter so _draw() / _renderRows() is called.
"""

import pytest


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


def _force_draw(frame, tag: str) -> None:
    """
        Re-trigger the component's draw by reassigning .data through the
        prototype setter.

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


def _set_data(frame, tag: str, data: object) -> None:
    """
        Assign new data to the component through the prototype setter,
        deleting any shadowing own property first.

        :param frame: The Playwright Frame containing the element.
        :param tag: The host custom-element tag name.
        :param data: A JSON-serialisable data object.
    """

    frame.evaluate(
        """([tag, data]) => {
            const el = document.querySelector(tag);
            if (el === null) { return; }
            if (el.hasOwnProperty('data')) { delete el.data; }
            el.data = data;
        }""",
        [tag, data],
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


def _collect_events(frame, tag: str, event_names: list) -> None:
    """
        Install a window.__mjevents collector for the given event names.

        Must be called before the interaction that fires the events.

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
# mj-burndown-chart
# ---------------------------------------------------------------------------

_BURNDOWN_DATA_A = {
    "totalScope": 60,
    "dailyValues": [
        {"date": "2025-01-01", "value": 60},
        {"date": "2025-01-02", "value": 52},
        {"date": "2025-01-03", "value": 44},
        {"date": "2025-01-04", "value": 38},
        {"date": "2025-01-05", "value": 30},
    ],
    "scopeChanges": [],
}

_BURNDOWN_DATA_B = {
    "totalScope": 100,
    "dailyValues": [
        {"date": "2025-02-01", "value": 100},
        {"date": "2025-02-02", "value": 90},
        {"date": "2025-02-03", "value": 80},
        {"date": "2025-02-04", "value": 68},
        {"date": "2025-02-05", "value": 55},
        {"date": "2025-02-06", "value": 40},
        {"date": "2025-02-07", "value": 25},
        {"date": "2025-02-08", "value": 10},
    ],
    "scopeChanges": [],
}


@pytest.mark.functional
def test_burndown_chart_initial_render(page, base_url):
    """
        mj-burndown-chart renders SVG data points when data is assigned.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-burndown-chart")
    _set_data(frame, "mj-burndown-chart", _BURNDOWN_DATA_A)
    _wait_for_shadow(frame, "mj-burndown-chart", "[part=data-point]")

    count = _shadow_count(frame, "mj-burndown-chart", "[part=data-point]")
    assert count == 5

    assert _shadow_exists(frame, "mj-burndown-chart", "[part=actual-line]") is True
    assert _shadow_exists(frame, "mj-burndown-chart", "[part=ideal-line]") is True

    return


@pytest.mark.functional
def test_burndown_chart_dynamic_update(page, base_url):
    """
        Reassigning .data re-renders mj-burndown-chart with the new values.

        Sets data A (5 points), then data B (8 points) and verifies the
        point count changed accordingly.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-burndown-chart")

    _set_data(frame, "mj-burndown-chart", _BURNDOWN_DATA_A)
    _wait_for_shadow(frame, "mj-burndown-chart", "[part=data-point]")
    count_a = _shadow_count(frame, "mj-burndown-chart", "[part=data-point]")

    _set_data(frame, "mj-burndown-chart", _BURNDOWN_DATA_B)
    frame.wait_for_function(
        """() => {
            const el = document.querySelector('mj-burndown-chart');
            if (el === null || el.shadowRoot === null) { return false; }
            return el.shadowRoot.querySelectorAll('[part=data-point]').length > 5;
        }""",
        timeout=10000,
    )
    count_b = _shadow_count(frame, "mj-burndown-chart", "[part=data-point]")

    assert count_b == 8
    assert count_b != count_a

    return


@pytest.mark.functional
def test_burndown_chart_point_select_event(page, base_url):
    """
        Clicking a data-point circle fires the mj-point-select event.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-burndown-chart")
    _set_data(frame, "mj-burndown-chart", _BURNDOWN_DATA_A)
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

_CFD_DATA_A = {
    "states": [
        {"id": "backlog", "name": "Backlog"},
        {"id": "inprogress", "name": "In Progress"},
        {"id": "done", "name": "Done"},
    ],
    "dailySeries": [
        {"date": "2025-01-01", "backlog": 20, "inprogress": 5, "done": 0},
        {"date": "2025-01-02", "backlog": 17, "inprogress": 6, "done": 2},
        {"date": "2025-01-03", "backlog": 14, "inprogress": 7, "done": 4},
        {"date": "2025-01-04", "backlog": 10, "inprogress": 8, "done": 7},
        {"date": "2025-01-05", "backlog": 7, "inprogress": 6, "done": 12},
    ],
}

_CFD_DATA_B = {
    "states": [
        {"id": "todo", "name": "To Do"},
        {"id": "active", "name": "Active"},
        {"id": "testing", "name": "Testing"},
        {"id": "released", "name": "Released"},
    ],
    "dailySeries": [
        {"date": "2025-03-01", "todo": 30, "active": 4, "testing": 2, "released": 0},
        {"date": "2025-03-02", "todo": 26, "active": 6, "testing": 3, "released": 1},
        {"date": "2025-03-03", "todo": 22, "active": 7, "testing": 4, "released": 3},
    ],
}


@pytest.mark.functional
def test_cumulative_flow_initial_render(page, base_url):
    """
        mj-cumulative-flow renders polygon bands and legend buttons when data
        is assigned.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-cumulative-flow")
    _set_data(frame, "mj-cumulative-flow", _CFD_DATA_A)
    _wait_for_shadow(frame, "mj-cumulative-flow", "[part=state-band]")

    band_count = _shadow_count(frame, "mj-cumulative-flow", "[part=state-band]")
    legend_count = _shadow_count(frame, "mj-cumulative-flow", "[part=legend-item]")

    assert band_count == 3
    assert legend_count == 3

    return


@pytest.mark.functional
def test_cumulative_flow_dynamic_update(page, base_url):
    """
        Reassigning .data re-renders mj-cumulative-flow with the new states.

        Sets data A (3 states) then data B (4 states) and verifies that the
        band and legend-button counts updated.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-cumulative-flow")

    _set_data(frame, "mj-cumulative-flow", _CFD_DATA_A)
    _wait_for_shadow(frame, "mj-cumulative-flow", "[part=state-band]")
    bands_a = _shadow_count(frame, "mj-cumulative-flow", "[part=state-band]")

    _set_data(frame, "mj-cumulative-flow", _CFD_DATA_B)
    frame.wait_for_function(
        """() => {
            const el = document.querySelector('mj-cumulative-flow');
            if (el === null || el.shadowRoot === null) { return false; }
            return el.shadowRoot.querySelectorAll('[part=state-band]').length === 4;
        }""",
        timeout=10000,
    )
    bands_b = _shadow_count(frame, "mj-cumulative-flow", "[part=state-band]")
    legends_b = _shadow_count(frame, "mj-cumulative-flow", "[part=legend-item]")

    assert bands_b == 4
    assert legends_b == 4
    assert bands_b != bands_a

    return


@pytest.mark.functional
def test_cumulative_flow_state_toggle_event(page, base_url):
    """
        Clicking a legend button fires the mj-state-toggle event.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-cumulative-flow")
    _set_data(frame, "mj-cumulative-flow", _CFD_DATA_A)
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

_VELOCITY_DATA_A = {
    "sprints": [
        {"name": "S1", "committed": 30, "completed": 28},
        {"name": "S2", "committed": 32, "completed": 34},
        {"name": "S3", "committed": 35, "completed": 31},
    ],
}

_VELOCITY_DATA_B = {
    "sprints": [
        {"name": "S1", "committed": 40, "completed": 37},
        {"name": "S2", "committed": 42, "completed": 45},
        {"name": "S3", "committed": 44, "completed": 40},
        {"name": "S4", "committed": 45, "completed": 48},
        {"name": "S5", "committed": 46, "completed": 43},
        {"name": "S6", "committed": 48, "completed": 50},
    ],
}


@pytest.mark.functional
def test_velocity_chart_initial_render(page, base_url):
    """
        mj-velocity-chart renders one bar-group per sprint when data is
        assigned.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-velocity-chart")
    _set_data(frame, "mj-velocity-chart", _VELOCITY_DATA_A)
    _wait_for_shadow(frame, "mj-velocity-chart", "[part=bar-group]")

    count = _shadow_count(frame, "mj-velocity-chart", "[part=bar-group]")
    assert count == 3

    assert _shadow_exists(frame, "mj-velocity-chart", "[part=average-line]") is True

    return


@pytest.mark.functional
def test_velocity_chart_dynamic_update(page, base_url):
    """
        Reassigning .data re-renders mj-velocity-chart with the new sprint
        count.

        Sets data A (3 sprints), then data B (6 sprints) and verifies the
        bar-group count updated.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-velocity-chart")

    _set_data(frame, "mj-velocity-chart", _VELOCITY_DATA_A)
    _wait_for_shadow(frame, "mj-velocity-chart", "[part=bar-group]")
    count_a = _shadow_count(frame, "mj-velocity-chart", "[part=bar-group]")

    _set_data(frame, "mj-velocity-chart", _VELOCITY_DATA_B)
    frame.wait_for_function(
        """() => {
            const el = document.querySelector('mj-velocity-chart');
            if (el === null || el.shadowRoot === null) { return false; }
            return el.shadowRoot.querySelectorAll('[part=bar-group]').length === 6;
        }""",
        timeout=10000,
    )
    count_b = _shadow_count(frame, "mj-velocity-chart", "[part=bar-group]")

    assert count_b == 6
    assert count_b != count_a

    return


@pytest.mark.functional
def test_velocity_chart_sprint_select_event(page, base_url):
    """
        Clicking a bar group fires the mj-sprint-select event.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-velocity-chart")
    _set_data(frame, "mj-velocity-chart", _VELOCITY_DATA_A)
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
# mj-build-status-board
# ---------------------------------------------------------------------------

_BSB_DATA_A = {
    "rows": [
        {
            "id": "r1", "name": "main / build", "status": "passed",
            "deployTarget": "staging", "lastRun": "2025-01-10T08:00:00Z",
            "duration": 120, "actor": "alice",
        },
        {
            "id": "r2", "name": "main / deploy", "status": "running",
            "deployTarget": "staging", "lastRun": "2025-01-10T08:02:00Z",
            "duration": 0, "actor": "ci-bot",
        },
        {
            "id": "r3", "name": "feat/auth / build", "status": "failed",
            "deployTarget": "", "lastRun": "2025-01-10T07:50:00Z",
            "duration": 74, "actor": "carol",
        },
    ],
}

_BSB_DATA_B = {
    "rows": [
        {
            "id": "b1", "name": "release / build", "status": "passed",
            "deployTarget": "prod", "lastRun": "2025-02-01T10:00:00Z",
            "duration": 90, "actor": "bob",
        },
        {
            "id": "b2", "name": "release / deploy", "status": "passed",
            "deployTarget": "prod", "lastRun": "2025-02-01T10:02:00Z",
            "duration": 45, "actor": "bob",
        },
        {
            "id": "b3", "name": "nightly / test", "status": "cancelled",
            "deployTarget": "", "lastRun": "2025-02-01T02:00:00Z",
            "duration": 0, "actor": "cron",
        },
        {
            "id": "b4", "name": "hotfix / build", "status": "passed",
            "deployTarget": "prod", "lastRun": "2025-02-01T09:00:00Z",
            "duration": 98, "actor": "alice",
        },
        {
            "id": "b5", "name": "hotfix / deploy", "status": "running",
            "deployTarget": "prod", "lastRun": "2025-02-01T09:03:00Z",
            "duration": 0, "actor": "alice",
        },
    ],
}


@pytest.mark.functional
def test_build_status_board_initial_render(page, base_url):
    """
        mj-build-status-board renders one data-row per row in the supplied
        data and shows status badges.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-build-status-board")
    _set_data(frame, "mj-build-status-board", _BSB_DATA_A)
    _wait_for_shadow(frame, "mj-build-status-board", "[part=data-row]")

    row_count = _shadow_count(frame, "mj-build-status-board", "[part=data-row]")
    badge_count = _shadow_count(frame, "mj-build-status-board", "[part=status-badge]")

    assert row_count == 3
    assert badge_count == 3

    return


@pytest.mark.functional
def test_build_status_board_dynamic_update(page, base_url):
    """
        Reassigning .data re-renders mj-build-status-board with the new rows.

        Sets data A (3 rows) then data B (5 rows) and verifies that the
        table body updated.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-build-status-board")

    _set_data(frame, "mj-build-status-board", _BSB_DATA_A)
    _wait_for_shadow(frame, "mj-build-status-board", "[part=data-row]")
    count_a = _shadow_count(frame, "mj-build-status-board", "[part=data-row]")

    _set_data(frame, "mj-build-status-board", _BSB_DATA_B)
    frame.wait_for_function(
        """() => {
            const el = document.querySelector('mj-build-status-board');
            if (el === null || el.shadowRoot === null) { return false; }
            return el.shadowRoot.querySelectorAll('[part=data-row]').length === 5;
        }""",
        timeout=10000,
    )
    count_b = _shadow_count(frame, "mj-build-status-board", "[part=data-row]")

    assert count_b == 5
    assert count_b != count_a

    return


@pytest.mark.functional
def test_build_status_board_sort_change_event(page, base_url):
    """
        Clicking the Status column header fires the mj-sort-change event.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-build-status-board")
    _set_data(frame, "mj-build-status-board", _BSB_DATA_A)
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
        Clicking a row checkbox fires the mj-row-select event.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-build-status-board")
    _set_data(frame, "mj-build-status-board", _BSB_DATA_A)
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
def test_build_status_board_sort_updates_row_order(page, base_url):
    """
        Clicking the Name column header sorts the rows alphabetically.

        After clicking the Name header (ascending) the first row's name
        should come before the second row's name lexicographically.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-build-status-board")
    _set_data(frame, "mj-build-status-board", _BSB_DATA_A)
    _wait_for_shadow(frame, "mj-build-status-board", "[part=data-row]")

    # Click Name header to sort ascending.
    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-build-status-board');
            const th = el.shadowRoot.querySelector('th[data-col=name]');
            if (th !== null) { th.click(); }
        }"""
    )

    frame.wait_for_function(
        """() => {
            const el = document.querySelector('mj-build-status-board');
            if (el === null || el.shadowRoot === null) { return false; }
            const th = el.shadowRoot.querySelector('th[data-col=name]');
            return th !== null && th.getAttribute('aria-sort') === 'ascending';
        }""",
        timeout=5000,
    )

    names = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-build-status-board');
            const rows = Array.from(el.shadowRoot.querySelectorAll('[part=data-row]'));
            return rows.map(r => r.querySelector('td:nth-child(2)').textContent.trim());
        }"""
    )

    assert len(names) >= 2
    assert names[0] <= names[1]

    return
