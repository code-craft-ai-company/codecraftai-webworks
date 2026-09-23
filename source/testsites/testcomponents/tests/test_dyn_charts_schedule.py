"""
    .. module:: testcomponents.tests.test_dyn_charts_schedule

    Playwright tests covering interactivity and dynamic data updates for the
    four schedule/timeline chart components:

      - mj-gantt-chart
      - mj-roadmap-chart
      - mj-milestone-timeline
      - mj-release-calendar

    For each component three aspects are tested:

    1. Initial render -- assign .data and assert that expected SVG or DOM
       primitives appear in the shadow DOM.

    2. Dynamic update -- set data A, measure a count (task bars, initiative
       bars, markers, or event chips); set data B with a different item
       count; assert the shadow DOM reflects the new count.

    3. Interactivity -- install an event collector, click the clickable
       element (task bar / initiative bar / marker / event chip), and
       assert the correct mj-* custom event was dispatched.

    Background note on own-property shadowing
    ------------------------------------------
    The playground example <script> blocks often run before the custom
    element upgrades, creating a plain own property on the element that
    shadows the prototype setter.  Every test deletes that own property
    before assigning data so the class setter (and its _draw / _renderCalendar
    call) actually executes.

    Helper pattern (applied in every test): call _assign_data(frame, tag, data)
    which deletes any own-property shadow then assigns via the setter.
"""

import ccai.testbase as testbase

from testcomponents.harness.factories import create_page


# ---------------------------------------------------------------------------
# Shared helpers (mirrors test_func_charts.py style)
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


def _assign_data(frame, tag: str, data: dict) -> None:
    """
        Delete any own-property shadow and assign data through the setter.

        :param frame: The Playwright Frame containing the element.
        :param tag: The host custom-element tag name.
        :param data: The data object to assign (serialised via JSON).
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


def _wait_for_shadow_count(frame, tag: str, selector: str, expected: int, timeout: int = 10000) -> None:
    """
        Wait until the shadow DOM contains exactly ``expected`` matches.

        :param frame: The Playwright Frame.
        :param tag: The host element tag.
        :param selector: CSS selector to query.
        :param expected: The exact count to wait for.
        :param timeout: Maximum wait time in milliseconds.
    """

    frame.wait_for_function(
        """([tag, sel, n]) => {
            const el = document.querySelector(tag);
            if (el === null || el.shadowRoot === null) { return false; }
            return el.shadowRoot.querySelectorAll(sel).length === n;
        }""",
        arg=[tag, selector, expected],
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
# mj-gantt-chart
# ---------------------------------------------------------------------------

_GANTT_DATA_A = {
    "tasks": [
        {"id": "t1", "name": "Requirements", "start": "2026-04-01", "end": "2026-04-10", "percentComplete": 100, "status": "done"},
        {"id": "t2", "name": "Design",       "start": "2026-04-08", "end": "2026-04-20", "percentComplete": 100, "status": "done"},
        {"id": "t3", "name": "Backend dev",  "start": "2026-04-18", "end": "2026-05-10", "percentComplete":  75, "status": "in-progress"},
        {"id": "t4", "name": "Frontend dev", "start": "2026-04-22", "end": "2026-05-14", "percentComplete":  60, "status": "in-progress"},
        {"id": "t5", "name": "QA testing",   "start": "2026-05-12", "end": "2026-05-26", "percentComplete":   0, "status": "planned"},
        {"id": "t6", "name": "Release",       "start": "2026-05-27", "end": "2026-05-28", "percentComplete":   0, "status": "planned"},
    ],
    "dependencies": [
        {"from": "t1", "to": "t2"},
        {"from": "t3", "to": "t5"},
    ],
}

_GANTT_DATA_B = {
    "tasks": [
        {"id": "x1", "name": "Alpha sprint", "start": "2026-06-01", "end": "2026-06-14", "percentComplete": 50, "status": "in-progress"},
        {"id": "x2", "name": "Beta sprint",  "start": "2026-06-15", "end": "2026-06-28", "percentComplete":  0, "status": "planned"},
    ],
}


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_gantt_chart_initial_render(page, base_url):
    """
        mj-gantt-chart renders task bars after data is assigned.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-gantt-chart")
    _assign_data(frame, "mj-gantt-chart", _GANTT_DATA_A)
    _wait_for_shadow(frame, "mj-gantt-chart", "[part=task-bar]")

    count = _shadow_count(frame, "mj-gantt-chart", "[part=task-bar]")
    assert count >= 6

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_gantt_chart_dynamic_update(page, base_url):
    """
        Reassigning .data on mj-gantt-chart re-renders the SVG.

        Data A has 6 task bars.  Data B has 2.  After reassignment the
        shadow DOM must reflect the new count.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-gantt-chart")

    _assign_data(frame, "mj-gantt-chart", _GANTT_DATA_A)
    _wait_for_shadow(frame, "mj-gantt-chart", "[part=task-bar]")
    count_a = _shadow_count(frame, "mj-gantt-chart", "[part=task-bar]")
    assert count_a >= 6

    _assign_data(frame, "mj-gantt-chart", _GANTT_DATA_B)
    # Each task renders a <g part="task-bar"> wrapper plus a <rect part="task-bar">
    # inside it, so 2 tasks produce 4 elements matching [part=task-bar].
    _wait_for_shadow_count(frame, "mj-gantt-chart", "[part=task-bar]", 4)
    count_b = _shadow_count(frame, "mj-gantt-chart", "[part=task-bar]")
    # count_b must be strictly less than the 6-task set count_a.
    assert count_b < count_a

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
    _assign_data(frame, "mj-gantt-chart", _GANTT_DATA_A)
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

_ROADMAP_DATA_A = {
    "swimlanes": [
        {"id": "platform", "name": "Platform"},
        {"id": "mobile",   "name": "Mobile"},
        {"id": "data",     "name": "Data"},
    ],
    "buckets": [
        {"id": "q1", "name": "Q1 2026"},
        {"id": "q2", "name": "Q2 2026"},
        {"id": "q3", "name": "Q3 2026"},
        {"id": "q4", "name": "Q4 2026"},
    ],
    "initiatives": [
        {"id": "i1", "name": "API Gateway v2",    "swimlaneId": "platform", "columnId": "q1", "status": "done"},
        {"id": "i2", "name": "Auth SSO",           "swimlaneId": "platform", "columnId": "q2", "status": "in-progress"},
        {"id": "i3", "name": "iOS redesign",       "swimlaneId": "mobile",   "columnId": "q2", "status": "planned"},
        {"id": "i4", "name": "Android widgets",    "swimlaneId": "mobile",   "columnId": "q3", "status": "planned"},
        {"id": "i5", "name": "Data lake v3",       "swimlaneId": "data",     "columnId": "q1", "status": "at-risk"},
        {"id": "i6", "name": "Real-time streams",  "swimlaneId": "data",     "columnId": "q3", "status": "planned"},
    ],
}

_ROADMAP_DATA_B = {
    "swimlanes": [
        {"id": "web", "name": "Web"},
    ],
    "buckets": [
        {"id": "h1", "name": "H1 2026"},
        {"id": "h2", "name": "H2 2026"},
    ],
    "initiatives": [
        {"id": "j1", "name": "Redesign homepage", "swimlaneId": "web", "columnId": "h1", "status": "in-progress"},
        {"id": "j2", "name": "Perf optimisation", "swimlaneId": "web", "columnId": "h2", "status": "planned"},
    ],
}


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_roadmap_chart_initial_render(page, base_url):
    """
        mj-roadmap-chart renders initiative bars after data is assigned.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-roadmap-chart")
    _assign_data(frame, "mj-roadmap-chart", _ROADMAP_DATA_A)
    _wait_for_shadow(frame, "mj-roadmap-chart", "[part=initiative-bar]")

    count = _shadow_count(frame, "mj-roadmap-chart", "[part=initiative-bar]")
    assert count >= 6

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_roadmap_chart_dynamic_update(page, base_url):
    """
        Reassigning .data on mj-roadmap-chart re-renders the SVG.

        Data A has 6 initiative bars.  Data B has 2.  After reassignment
        the shadow DOM must reflect the new count.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-roadmap-chart")

    _assign_data(frame, "mj-roadmap-chart", _ROADMAP_DATA_A)
    _wait_for_shadow(frame, "mj-roadmap-chart", "[part=initiative-bar]")
    count_a = _shadow_count(frame, "mj-roadmap-chart", "[part=initiative-bar]")
    assert count_a >= 6

    _assign_data(frame, "mj-roadmap-chart", _ROADMAP_DATA_B)
    _wait_for_shadow_count(frame, "mj-roadmap-chart", "[part=initiative-bar]", 2)
    count_b = _shadow_count(frame, "mj-roadmap-chart", "[part=initiative-bar]")
    assert count_b == 2

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
    _assign_data(frame, "mj-roadmap-chart", _ROADMAP_DATA_A)
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

_MILESTONE_DATA_A = {
    "markers": [
        {"name": "v2.0 branch cut", "date": "2026-04-15", "type": "freeze",    "description": "No new features after this date."},
        {"name": "RC1",             "date": "2026-04-28", "type": "tag",        "description": "First release candidate."},
        {"name": "v2.0 GA",         "date": "2026-05-12", "type": "release",   "description": "General availability."},
        {"name": "Sprint 14 start", "date": "2026-05-18", "type": "milestone"},
        {"name": "v2.1 planning",   "date": "2026-06-02", "type": "milestone"},
    ],
    "phases": [
        {"name": "Stabilisation", "start": "2026-04-15", "end": "2026-05-12"},
    ],
}

_MILESTONE_DATA_B = {
    "markers": [
        {"name": "Beta launch",  "date": "2026-07-01", "type": "release"},
        {"name": "GA launch",    "date": "2026-08-01", "type": "release"},
    ],
}


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_milestone_timeline_initial_render(page, base_url):
    """
        mj-milestone-timeline renders marker groups after data is assigned.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-milestone-timeline")
    _assign_data(frame, "mj-milestone-timeline", _MILESTONE_DATA_A)
    _wait_for_shadow(frame, "mj-milestone-timeline", "[part=marker]")

    count = _shadow_count(frame, "mj-milestone-timeline", "[part=marker]")
    assert count >= 5

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_milestone_timeline_dynamic_update(page, base_url):
    """
        Reassigning .data on mj-milestone-timeline re-renders the SVG.

        Data A has 5 markers.  Data B has 2.  After reassignment the
        shadow DOM must reflect the new count.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-milestone-timeline")

    _assign_data(frame, "mj-milestone-timeline", _MILESTONE_DATA_A)
    _wait_for_shadow(frame, "mj-milestone-timeline", "[part=marker]")
    count_a = _shadow_count(frame, "mj-milestone-timeline", "[part=marker]")
    assert count_a >= 5

    _assign_data(frame, "mj-milestone-timeline", _MILESTONE_DATA_B)
    _wait_for_shadow_count(frame, "mj-milestone-timeline", "[part=marker]", 2)
    count_b = _shadow_count(frame, "mj-milestone-timeline", "[part=marker]")
    assert count_b == 2

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
    _assign_data(frame, "mj-milestone-timeline", _MILESTONE_DATA_A)
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
# mj-release-calendar
# ---------------------------------------------------------------------------

# Events in May 2026 so they appear in the displayed month.
_CAL_DATA_A = {
    "events": [
        {"id": "ev1", "name": "v3.1.0 release", "type": "release",   "startDate": "2026-05-08"},
        {"id": "ev2", "name": "Code freeze",     "type": "freeze",    "startDate": "2026-05-05", "endDate": "2026-05-08"},
        {"id": "ev3", "name": "EU downtime",     "type": "blackout",  "startDate": "2026-05-20", "endDate": "2026-05-21"},
        {"id": "ev4", "name": "Sprint 15 demo",  "type": "milestone", "startDate": "2026-05-15"},
        {"id": "ev5", "name": "Memorial Day",    "type": "holiday",   "startDate": "2026-05-25"},
        {"id": "ev6", "name": "v3.2.0-beta",     "type": "release",   "startDate": "2026-05-29"},
    ],
}

# Fewer events in May 2026 (only 2) for the update test.
_CAL_DATA_B = {
    "events": [
        {"id": "u1", "name": "Hotfix deploy",   "type": "release",   "startDate": "2026-05-10"},
        {"id": "u2", "name": "DB maintenance",  "type": "blackout",  "startDate": "2026-05-17"},
    ],
}


def _navigate_to_may_2026(frame) -> None:
    """
        Click the next-month button until the calendar title contains 'May 2026'.

        The example sets current-date='2026-05-01' but timezone conversion
        can shift the displayed month.  This helper ensures May 2026 is
        always visible before chip assertions run.

        :param frame: The Playwright Frame containing mj-release-calendar.
    """

    for _ in range(3):
        title = frame.evaluate(
            """() => {
                const el = document.querySelector('mj-release-calendar');
                if (el === null || el.shadowRoot === null) { return ''; }
                const span = el.shadowRoot.querySelector('.cal-title');
                return span !== null ? span.textContent : '';
            }"""
        )
        if "May" in title and "2026" in title:
            break
        frame.evaluate(
            """() => {
                const el = document.querySelector('mj-release-calendar');
                if (el === null || el.shadowRoot === null) { return; }
                const btn = el.shadowRoot.querySelector('.next-btn');
                if (btn !== null) { btn.click(); }
            }"""
        )

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_release_calendar_initial_render(page, base_url):
    """
        mj-release-calendar renders day cells after data is assigned.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-release-calendar")
    _assign_data(frame, "mj-release-calendar", _CAL_DATA_A)
    _wait_for_shadow(frame, "mj-release-calendar", "[part=day-cell]")

    count = _shadow_count(frame, "mj-release-calendar", "[part=day-cell]")
    assert count >= 28

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_release_calendar_dynamic_update(page, base_url):
    """
        Reassigning .data on mj-release-calendar re-renders the grid.

        Data A has 6 events in May 2026 (at least 1 chip visible per chip).
        Data B has 2 events in May 2026.  After reassignment the total
        chip count across all day cells must drop.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-release-calendar")

    _assign_data(frame, "mj-release-calendar", _CAL_DATA_A)
    _wait_for_shadow(frame, "mj-release-calendar", "[part=day-cell]")
    _navigate_to_may_2026(frame)
    _wait_for_shadow(frame, "mj-release-calendar", "[part=event-chip]")
    count_a = _shadow_count(frame, "mj-release-calendar", "[part=event-chip]")
    assert count_a >= 1

    _assign_data(frame, "mj-release-calendar", _CAL_DATA_B)
    _navigate_to_may_2026(frame)
    _wait_for_shadow(frame, "mj-release-calendar", "[part=event-chip]")
    count_b = _shadow_count(frame, "mj-release-calendar", "[part=event-chip]")

    # Data B has only 2 events so the visible chip count must be strictly
    # less than the 6-event set from data A.
    assert count_b < count_a

    return


@testbase.mark_categories(categories=["functional"])
@testbase.attach.parameter(create_page, identifier="page")
def test_release_calendar_event_select_event(page, base_url):
    """
        Clicking an event chip fires the mj-event-select event.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_chart(page, base_url, "mj-release-calendar")
    _assign_data(frame, "mj-release-calendar", _CAL_DATA_A)
    _wait_for_shadow(frame, "mj-release-calendar", "[part=day-cell]")
    _navigate_to_may_2026(frame)
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


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
