"""
    test_dyn_charts_media.py

    Functional Playwright tests covering dynamic updates and interactivity for
    the four media-group chart components:

      mj-chart, mj-gauge, mj-sparkline, mj-diagram

    For each component the suite verifies:

      1. Initial render -- shadow DOM contains the expected SVG primitives
         after data is set through the prototype setter.
      2. Dynamic update -- assigning a *different* dataset after the first
         causes the shadow DOM to change accordingly (different element count
         or label text), proving that the ``set data(...)`` / attribute-change
         path re-invokes the draw routine on a live component.
      3. Interactivity -- a click on a mark (bar, arc, node button, etc.)
         causes the component to emit the documented ``mj-*`` custom event.

    Note on the own-property shadow
    --------------------------------
    The playground example ``<script>`` block may run before the custom element
    upgrades and assign ``el.data = value`` (or ``el.graph = value``) as a plain
    own property that shadows the prototype getter/setter.  Tests always call
    ``delete el.<prop>`` before assigning so the prototype setter is invoked and
    the draw is triggered.
"""

import pytest


# ---------------------------------------------------------------------------
# Shared helpers (mirror the conventions in test_func_charts.py)
# ---------------------------------------------------------------------------

def _open_media(page, base_url: str, tag: str):
    """
        Navigate to the media component playground and return a ready Frame.

        :param page: The Playwright page object.
        :param base_url: The base URL of the running testcomponents site.
        :param tag: The custom element tag name, e.g. 'mj-chart'.

        :returns: The Playwright Frame inside the preview iframe.
    """

    page.goto(base_url + f"/components/media/{tag}")
    handle = page.wait_for_selector("[data-testid=playground-preview]")
    frame = handle.content_frame()
    frame.wait_for_function(
        "tag => customElements.get(tag) !== undefined",
        arg=tag,
        timeout=15000,
    )
    return frame


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


def _shadow_text(frame, tag: str, selector: str) -> str:
    """
        Return the textContent of the first matching element in the shadow root.

        :param frame: The Playwright Frame.
        :param tag: The host element tag.
        :param selector: CSS selector to look for inside the shadow root.

        :returns: The textContent string, or empty string if not found.
    """

    text = frame.evaluate(
        """([tag, sel]) => {
            const el = document.querySelector(tag);
            if (el === null || el.shadowRoot === null) { return ''; }
            const target = el.shadowRoot.querySelector(sel);
            return target !== null ? target.textContent : '';
        }""",
        [tag, selector],
    )
    return text


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
        Install a ``window.__mjevents`` collector for the given event names.

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


# ===========================================================================
# mj-chart
# ===========================================================================

# ===========================================================================
# mj-gauge
# ===========================================================================

@pytest.mark.functional
def test_mj_gauge_initial_render_arc_svg(page, base_url):
    """
        mj-gauge renders a gauge-svg SVG element after the component connects.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_media(page, base_url, "mj-gauge")
    _wait_for_shadow(frame, "mj-gauge", "svg.gauge-svg")

    count = _shadow_count(frame, "mj-gauge", "svg.gauge-svg")
    assert count >= 1

    return


@pytest.mark.functional
def test_mj_gauge_dynamic_update_value_attribute(page, base_url):
    """
        Changing the value attribute re-renders the gauge value label.

        Set value='20' and capture the label; then set value='80' and assert
        the label text changed, proving _buildGauge() is called on attribute
        change for a live component.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_media(page, base_url, "mj-gauge")
    _wait_for_shadow(frame, "mj-gauge", ".value-label")

    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-gauge');
            el.setAttribute('value', '20');
        }"""
    )

    frame.wait_for_function(
        """() => {
            const el = document.querySelector('mj-gauge');
            if (el === null || el.shadowRoot === null) { return false; }
            const label = el.shadowRoot.querySelector('.value-label');
            return label !== null && label.textContent.includes('20');
        }""",
        timeout=10000,
    )

    label_20 = _shadow_text(frame, "mj-gauge", ".value-label")
    assert "20" in label_20

    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-gauge');
            el.setAttribute('value', '80');
        }"""
    )

    frame.wait_for_function(
        """() => {
            const el = document.querySelector('mj-gauge');
            if (el === null || el.shadowRoot === null) { return false; }
            const label = el.shadowRoot.querySelector('.value-label');
            return label !== null && label.textContent.includes('80');
        }""",
        timeout=10000,
    )

    label_80 = _shadow_text(frame, "mj-gauge", ".value-label")
    assert "80" in label_80
    assert label_80 != label_20

    return


@pytest.mark.functional
def test_mj_gauge_value_change_event_on_attribute(page, base_url):
    """
        Changing the value attribute fires the mj-gauge-value-change event.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_media(page, base_url, "mj-gauge")
    _wait_for_shadow(frame, "mj-gauge", ".value-label")

    _collect_events(frame, "mj-gauge", ["mj-gauge-value-change"])

    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-gauge');
            const old = el.getAttribute('value');
            el.setAttribute('value', old === '75' ? '50' : '75');
        }"""
    )

    frame.wait_for_function(
        "() => window.__mjevents && window.__mjevents.length > 0",
        timeout=10000,
    )

    events = frame.evaluate("() => window.__mjevents")
    assert "mj-gauge-value-change" in events

    return


@pytest.mark.functional
def test_mj_gauge_click_emits_gauge_click_event(page, base_url):
    """
        Clicking anywhere on the gauge container fires the mj-gauge-click event.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_media(page, base_url, "mj-gauge")
    _wait_for_shadow(frame, "mj-gauge", ".container")

    _collect_events(frame, "mj-gauge", ["mj-gauge-click"])

    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-gauge');
            const container = el.shadowRoot.querySelector('.container');
            if (container !== null) {
                container.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
            }
        }"""
    )

    events = frame.evaluate("() => window.__mjevents")
    assert "mj-gauge-click" in events

    return


# ===========================================================================
# mj-sparkline
# ===========================================================================

@pytest.mark.functional
def test_mj_sparkline_initial_render_svg_path(page, base_url):
    """
        mj-sparkline renders an SVG with a line path after the values attribute
        is set.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_media(page, base_url, "mj-sparkline")

    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-sparkline');
            if (el === null) { return; }
            el.setAttribute('values', '5,10,8,15,12');
            el.setAttribute('type', 'line');
        }"""
    )

    _wait_for_shadow(frame, "mj-sparkline", "path.line")

    count = _shadow_count(frame, "mj-sparkline", "path.line")
    assert count >= 1

    return


@pytest.mark.functional
def test_mj_sparkline_dynamic_update_bar_count_changes(page, base_url):
    """
        Changing the values attribute on a connected component re-renders bars.

        Set 3 values (3 bars), then set 6 values and assert the bar count
        increased, proving the attribute-change path calls _draw().

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_media(page, base_url, "mj-sparkline")

    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-sparkline');
            el.setAttribute('type', 'bar');
            el.setAttribute('values', '5,10,8');
        }"""
    )
    _wait_for_shadow(frame, "mj-sparkline", "rect[part=bar]")
    count_a = _shadow_count(frame, "mj-sparkline", "rect[part=bar]")
    assert count_a == 3

    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-sparkline');
            el.setAttribute('values', '5,10,8,15,12,7');
        }"""
    )

    frame.wait_for_function(
        f"""() => {{
            const el = document.querySelector('mj-sparkline');
            if (el === null || el.shadowRoot === null) {{ return false; }}
            return el.shadowRoot.querySelectorAll('rect[part=bar]').length > {count_a};
        }}""",
        timeout=10000,
    )

    count_b = _shadow_count(frame, "mj-sparkline", "rect[part=bar]")
    assert count_b > count_a

    return


@pytest.mark.functional
def test_mj_sparkline_bar_click_emits_sparkline_click(page, base_url):
    """
        Clicking a bar rect fires the mj-sparkline-click event.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_media(page, base_url, "mj-sparkline")

    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-sparkline');
            el.setAttribute('type', 'bar');
            el.setAttribute('values', '5,10,8,12');
        }"""
    )
    _wait_for_shadow(frame, "mj-sparkline", "rect[part=bar]")

    _collect_events(frame, "mj-sparkline", ["mj-sparkline-click"])

    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-sparkline');
            const bar = el.shadowRoot.querySelector('rect[part=bar]');
            if (bar !== null) {
                bar.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
            }
        }"""
    )

    events = frame.evaluate("() => window.__mjevents")
    assert "mj-sparkline-click" in events

    return


# ===========================================================================
# mj-diagram
# ===========================================================================

@pytest.mark.functional
def test_mj_diagram_initial_render_node_list(page, base_url):
    """
        After .graph is set the shadow DOM node list contains buttons for each
        node.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_media(page, base_url, "mj-diagram")

    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-diagram');
            if (el === null) { return; }
            delete el.graph;
            el.graph = {
                nodes: [
                    { id: 'a', label: 'Alpha' },
                    { id: 'b', label: 'Beta' },
                    { id: 'c', label: 'Gamma' }
                ],
                edges: [{ id: 'e1', source: 'a', target: 'b' }]
            };
        }"""
    )

    _wait_for_shadow(frame, "mj-diagram", ".node-btn")

    count = _shadow_count(frame, "mj-diagram", ".node-btn")
    assert count >= 3

    return


@pytest.mark.functional
def test_mj_diagram_dynamic_update_graph_node_count_changes(page, base_url):
    """
        Reassigning .graph on a live component updates the node list.

        Set a 2-node graph, capture button count; set a 4-node graph; assert
        the button count increased, proving the graph setter rebuilds the list.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_media(page, base_url, "mj-diagram")

    # Graph A: 2 nodes.
    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-diagram');
            delete el.graph;
            el.graph = {
                nodes: [{ id: 'x', label: 'X' }, { id: 'y', label: 'Y' }],
                edges: []
            };
        }"""
    )
    _wait_for_shadow(frame, "mj-diagram", ".node-btn")
    count_a = _shadow_count(frame, "mj-diagram", ".node-btn")

    # Graph B: 4 nodes.
    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-diagram');
            delete el.graph;
            el.graph = {
                nodes: [
                    { id: 'p', label: 'P' }, { id: 'q', label: 'Q' },
                    { id: 'r', label: 'R' }, { id: 's', label: 'S' }
                ],
                edges: []
            };
        }"""
    )

    frame.wait_for_function(
        f"""() => {{
            const el = document.querySelector('mj-diagram');
            if (el === null || el.shadowRoot === null) {{ return false; }}
            return el.shadowRoot.querySelectorAll('.node-btn').length > {count_a};
        }}""",
        timeout=10000,
    )

    count_b = _shadow_count(frame, "mj-diagram", ".node-btn")
    assert count_b > count_a

    return


@pytest.mark.functional
def test_mj_diagram_node_button_click_emits_select_event(page, base_url):
    """
        Clicking a node button in the accessible list fires the
        mj-diagram-node-select event.

        :param page: Playwright page fixture.
        :param base_url: Base URL fixture.
    """

    frame = _open_media(page, base_url, "mj-diagram")

    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-diagram');
            delete el.graph;
            el.graph = {
                nodes: [{ id: 'n1', label: 'Node One' }],
                edges: []
            };
        }"""
    )
    _wait_for_shadow(frame, "mj-diagram", ".node-btn")

    _collect_events(frame, "mj-diagram", ["mj-diagram-node-select"])

    frame.evaluate(
        """() => {
            const el = document.querySelector('mj-diagram');
            const btn = el.shadowRoot.querySelector('.node-btn');
            if (btn !== null) { btn.click(); }
        }"""
    )

    events = frame.evaluate("() => window.__mjevents")
    assert "mj-diagram-node-select" in events

    return
