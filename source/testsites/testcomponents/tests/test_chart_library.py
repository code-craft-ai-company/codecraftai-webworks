"""
    .. module:: testcomponents.tests.test_chart_library
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: The comprehensive <mj-chart> chart library.

    Tests for the comprehensive <mj-chart> chart library and its dedicated
    landing/gallery on /charts plus per-type playground pages at
    /chart-type/<type>. The per-type sweeps are defined as individual
    module-level tests named ``<check>__<type>`` so a broken chart type is
    reported by name.
"""

import json
import math

import ccai.testbase as testbase

from testcomponents.charttypes import chart_type_count

from testcomponents.harness.browsers import expect
from testcomponents.harness.catalogs import SAMPLE_CHART_TYPES
from testcomponents.harness.catalogs import all_chart_types
from testcomponents.harness.catalogs import identifier_for
from testcomponents.harness.factories import create_page
from testcomponents.harness.generation import define_page_tests


# One case per catalogued chart type: (identifier, (type_key, title)).
_CHART_CASES = [
    (identifier_for(type_key), (type_key, title))
    for type_key, title in all_chart_types()
]

# A representative sample for the deeper render check: (identifier, (type_key,)).
_SAMPLE_CASES = [
    (identifier_for(type_key), (type_key,))
    for type_key in SAMPLE_CHART_TYPES
]


@testbase.attach.parameter(create_page, identifier="page")
def test_chart_library_landing_lists_every_type(page, base_url):
    """
        The /charts page renders one card per catalogued chart type.
    """

    page.goto(base_url + "/charts")

    expect(page.get_by_test_id("chart-library-intro")).to_be_visible()
    cards = page.locator('[data-testid^="chart-type-card-"]')
    expect(cards).to_have_count(chart_type_count())

    return


def _check_chart_type_page_loads(page, base_url, type_key, title):
    """
        Every catalogued chart type has its own playground page that
        loads and shows the chart heading and the playground.

        :param type_key: The chart `type` key.
        :param title: The chart title.
    """

    page.goto(base_url + f"/chart-type/{type_key}")

    heading = page.get_by_test_id("chart-type-heading")
    expect(heading).to_be_visible()
    expect(heading).to_contain_text(title)
    expect(page.get_by_test_id("playground-editor")).to_be_visible()
    expect(page.get_by_test_id("playground-preview")).to_be_attached()

    return


def _check_chart_type_renders_svg(page, base_url, type_key):
    """
        A representative sample of chart types draws an SVG with marks in
        the playground preview iframe.

        :param type_key: The chart `type` key.
    """

    page.goto(base_url + f"/chart-type/{type_key}")
    handle = page.wait_for_selector("[data-testid=playground-preview]")
    frame = handle.content_frame()
    frame.wait_for_function(
        "() => customElements.get('mj-chart') !== undefined",
        timeout=15000,
    )
    page.wait_for_timeout(1200)

    info = frame.evaluate(
        """() => {
            const el = document.querySelector('mj-chart');
            if (el === null || el.shadowRoot === null) {
                return { marks: 0 };
            }
            const sr = el.shadowRoot;
            const marks = sr.querySelectorAll(
                'svg rect, svg path, svg circle, svg line, svg polygon, svg ellipse'
            ).length;
            return { marks: marks };
        }"""
    )

    assert info["marks"] > 1, (
        f"<mj-chart type='{type_key}'> did not draw any marks "
        f"(marks={info['marks']})"
    )

    return


def _check_chart_type_is_accessible(page, base_url, type_key):
    """
        A representative sample of chart types renders as a named figure
        whose drawing is not hidden from assistive technology, whose
        focusable marks are at most one tab stop, and whose fallback table
        has rows (also for the family-specific data shapes).

        :param type_key: The chart `type` key.
    """

    page.goto(base_url + f"/chart-type/{type_key}")
    handle = page.wait_for_selector("[data-testid=playground-preview]")
    frame = handle.content_frame()
    frame.wait_for_function(
        """() => {
            const chart = document.querySelector('mj-chart');
            return chart !== null && chart.chartState === 'ready';
        }""",
        timeout=15000,
    )

    info = frame.evaluate(
        """() => {
            const chart = document.querySelector('mj-chart');
            const root = chart.shadowRoot;
            const svg = root.querySelector('svg');
            const table = root.querySelector('[data-chart-table] table');
            return {
                role: chart.getAttribute('role'),
                label: chart.getAttribute('aria-label'),
                svgHidden: svg.getAttribute('aria-hidden'),
                tabStops: svg.querySelectorAll('[tabindex="0"]').length,
                tableRows: table !== null ? table.querySelectorAll('tbody tr').length : 0,
                live: root.querySelector('[data-chart-table]').getAttribute('aria-live')
            };
        }"""
    )

    assert info["role"] == "figure", f"{type_key}: role is {info['role']}"
    assert info["label"] is not None and len(info["label"]) > 0, f"{type_key}: no accessible name"
    assert info["svgHidden"] is None, f"{type_key}: the drawing is aria-hidden"
    assert info["tabStops"] <= 1, f"{type_key}: {info['tabStops']} tab stops in the drawing"
    assert info["tableRows"] > 0, f"{type_key}: the fallback table is empty"
    assert info["live"] is None, f"{type_key}: the fallback table is a live region"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_charts_page_has_chart_library_section(page, base_url):
    """
        The Chart Library section is present and labelled correctly.
    """

    page.goto(base_url + "/charts")
    intro = page.get_by_test_id("chart-library-intro")
    expect(intro).to_be_visible()
    expect(intro).to_contain_text("Chart Library")
    expect(intro).to_contain_text("chart types")

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_chart_library_card_navigates(page, base_url):
    """
        Clicking a chart-type card opens the chart-type playground.
    """

    page.goto(base_url + "/charts")
    page.get_by_test_id("chart-type-card-bar").click()
    expect(page).to_have_url(base_url + "/chart-type/bar")
    expect(page.get_by_test_id("chart-type-heading")).to_contain_text("Bar")

    return


# ---------------------------------------------------------------------------
# Part-to-whole, hierarchy and flow renderers
# ---------------------------------------------------------------------------

def _ready_preview(page, base_url, type_key):
    """
        Open a chart-type page and wait until its preview chart is drawn.

        :param type_key: The chart `type` key.
        :returns: The preview iframe's Frame.
    """

    page.goto(base_url + f"/chart-type/{type_key}")
    handle = page.wait_for_selector("[data-testid=playground-preview]")
    frame = handle.content_frame()
    frame.wait_for_function(
        """() => {
            const chart = document.querySelector('mj-chart');
            return chart !== null && chart.chartState === 'ready';
        }""",
        timeout=15000,
    )

    return frame


def _render_in_preview(frame, markup, data):
    """
        Replace the preview with one chart, give it data, and report what it
        drew once it settles.

        :param markup: The <mj-chart> markup.
        :param data: The chart data (JSON-serialisable).
        :returns: { state, errors, fills, marks, bad, texts, legend }.
    """

    info = frame.evaluate(
        """async ([markup, data]) => {
            document.body.innerHTML = markup;
            const chart = document.querySelector('mj-chart');
            const errors = [];
            chart.addEventListener('mj-chart-error', (event) => errors.push(event.detail.message));
            chart.data = data;
            await new Promise((resolve) => setTimeout(resolve, 600));
            const svg = chart.shadowRoot.querySelector('svg');
            const nodes = svg !== null ? Array.from(svg.querySelectorAll('*')) : [];
            const bad = [];
            for (const node of nodes) {
                for (const attribute of node.attributes) {
                    if (/NaN|undefined|Infinity/.test(attribute.value)) {
                        bad.push(node.tagName + '.' + attribute.name);
                    }
                }
            }
            const fills = new Set(nodes
                .filter((node) => node.hasAttribute('part') && node.hasAttribute('fill'))
                .map((node) => node.getAttribute('fill')));
            return {
                state: chart.chartState,
                errors: errors,
                fills: fills.size,
                marks: svg !== null ? svg.querySelectorAll('[tabindex]').length : 0,
                bad: bad,
                texts: nodes.filter((node) => node.tagName === 'text').map((node) => node.textContent)
            };
        }""",
        [markup, data],
    )

    return info


@testbase.attach.parameter(create_page, identifier="page")
def test_pie_slices_have_distinct_colours_and_labels(page, base_url):
    """
        Every pie slice has its own colour and is labelled with its
        category, and the legend lists the slices.
    """

    frame = _ready_preview(page, base_url, "pie")
    info = frame.evaluate(
        """() => {
            const chart = document.querySelector('mj-chart');
            const slices = chart.shadowRoot.querySelectorAll('[part=slice]');
            const fills = new Set(Array.from(slices).map((slice) => slice.getAttribute('fill')));
            const text = chart.shadowRoot.querySelector('svg').textContent;
            return { slices: slices.length, fills: fills.size, text: text };
        }"""
    )

    assert info["slices"] == 6, f"expected 6 slices, got {info['slices']}"
    assert info["fills"] == 6, f"slices share colours: {info['fills']} distinct fills"
    assert "Organic Search" in info["text"], "slices are not labelled with their category"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_donut_draws_a_ring_by_default(page, base_url):
    """
        type="donut" without inner-radius draws a ring, and a single 100%
        slice draws a whole ring rather than nothing.
    """

    frame = _ready_preview(page, base_url, "donut")
    info = _render_in_preview(
        frame,
        '<mj-chart type="donut" style="height:240px"></mj-chart>',
        {"categories": ["Only"], "series": [{"name": "s", "values": [5]}]},
    )
    path = frame.evaluate(
        """() => document.querySelector('mj-chart').shadowRoot
            .querySelector('[part=slice]').getAttribute('d')"""
    )

    assert info["state"] == "ready", f"donut state {info['state']}"
    assert path.count("A") == 4, f"a full ring has two outer and two inner arcs: {path}"
    assert info["bad"] == [], f"invalid geometry: {info['bad']}"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_part_to_whole_rejects_negative_values(page, base_url):
    """
        A negative pie value is left out and reported with mj-chart-error
        instead of producing shares over 100%.
    """

    frame = _ready_preview(page, base_url, "pie")
    info = _render_in_preview(
        frame,
        '<mj-chart type="pie" style="height:240px"></mj-chart>',
        {"categories": ["A", "B", "C"], "series": [{"name": "s", "values": [5, -3, 2]}]},
    )

    assert info["state"] == "ready", f"pie state {info['state']}"
    assert len(info["errors"]) == 1, f"expected one mj-chart-error, got {info['errors']}"
    assert info["marks"] == 2, f"expected 2 slices, got {info['marks']}"
    assert not any("125" in text for text in info["texts"]), f"share over 100%: {info['texts']}"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_waffle_cells_coloured_by_category(page, base_url):
    """
        Waffle cells are coloured per category, grouped into one focusable
        mark per category, and survive more values than categories.
    """

    frame = _ready_preview(page, base_url, "waffle")
    info = frame.evaluate(
        """() => {
            const svg = document.querySelector('mj-chart').shadowRoot.querySelector('svg');
            const groups = svg.querySelectorAll('[part=category]');
            const fills = new Set(Array.from(groups).map((group) => group.getAttribute('fill')));
            return { groups: groups.length, fills: fills.size, cells: svg.querySelectorAll('[part=cell]').length };
        }"""
    )
    assert info["groups"] == 4, f"expected 4 category groups, got {info['groups']}"
    assert info["fills"] == 4, f"categories share colours: {info['fills']}"
    assert info["cells"] == 100, f"expected 100 cells, got {info['cells']}"

    extra = _render_in_preview(
        frame,
        '<mj-chart type="waffle" style="height:240px"></mj-chart>',
        {"categories": ["A", "B"], "series": [{"name": "s", "values": [10, 10, 80]}]},
    )
    assert extra["state"] == "ready", f"waffle with extra values: {extra['state']}"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_waterfall_object_values_and_labels(page, base_url):
    """
        The spec's { v, kind } value form draws one labelled bar per step
        and computes the running total.
    """

    frame = _ready_preview(page, base_url, "waterfall")
    info = _render_in_preview(
        frame,
        '<mj-chart type="waterfall" style="height:260px"></mj-chart>',
        {
            "categories": ["Start", "Revenue", "COGS", "Net"],
            "series": [{"name": "P&L", "values": [
                {"v": 500, "kind": "total"}, {"v": 200, "kind": "add"},
                {"v": -80, "kind": "subtract"}, {"v": None, "kind": "total"},
            ]}],
        },
    )

    assert info["state"] == "ready", f"waterfall state {info['state']}"
    assert info["marks"] == 4, f"expected 4 bars, got {info['marks']}"
    assert "+200" in info["texts"] and "-80" in info["texts"], f"no step labels: {info['texts']}"
    assert "620" in info["texts"], f"running total not labelled: {info['texts']}"

    return


_CYCLE_GRAPH = {
    "nodes": [{"id": "a", "label": "A"}, {"id": "b", "label": "B"}, {"id": "c", "label": "C"}],
    "links": [
        {"source": "a", "target": "b", "value": 5},
        {"source": "b", "target": "c", "value": 3},
        {"source": "c", "target": "b", "value": 1},
        {"source": "b", "target": "b", "value": 1},
    ],
}


@testbase.attach.parameter(create_page, identifier="page")
def test_sankey_cycle_and_self_link_render(page, base_url):
    """
        A cycle and a self-link in sankey links are broken instead of
        looping until the tab runs out of memory.
    """

    frame = _ready_preview(page, base_url, "sankey")
    info = _render_in_preview(
        frame, '<mj-chart type="sankey" style="height:240px"></mj-chart>', _CYCLE_GRAPH
    )

    assert info["state"] == "ready", f"sankey with a cycle: {info['state']}"
    assert info["marks"] > 0, "sankey with a cycle drew nothing"
    assert info["bad"] == [], f"invalid geometry: {info['bad']}"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_dependency_graph_cycle_render(page, base_url):
    """
        The layered layout of dependency-graph breaks cycles and self-links.
    """

    frame = _ready_preview(page, base_url, "dependency-graph")
    info = _render_in_preview(
        frame, '<mj-chart type="dependency-graph" style="height:240px"></mj-chart>', _CYCLE_GRAPH
    )

    assert info["state"] == "ready", f"dependency-graph with a cycle: {info['state']}"
    assert info["bad"] == [], f"invalid geometry: {info['bad']}"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_network_force_layout_stays_finite(page, base_url):
    """
        The force layout keeps every coordinate finite on a 100-node graph.
    """

    nodes = [{"id": f"n{index}", "group": f"g{index % 4}"} for index in range(100)]
    links = [{"source": f"n{index}", "target": f"n{(index - 1) // 2}"} for index in range(1, 100)]
    frame = _ready_preview(page, base_url, "network")
    info = _render_in_preview(
        frame, '<mj-chart type="network" style="height:280px"></mj-chart>',
        {"nodes": nodes, "links": links},
    )

    assert info["state"] == "ready", f"network state {info['state']}"
    assert info["bad"] == [], f"non-finite geometry: {info['bad'][:5]}"
    assert info["fills"] >= 4, f"node groups share colours: {info['fills']}"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_chord_groups_have_distinct_colours(page, base_url):
    """
        Chord arcs are coloured per node rather than all in one colour.
    """

    frame = _ready_preview(page, base_url, "chord")
    info = frame.evaluate(
        """() => {
            const svg = document.querySelector('mj-chart').shadowRoot.querySelector('svg');
            const fills = new Set(Array.from(svg.querySelectorAll('path[fill]'))
                .map((path) => path.getAttribute('fill')).filter((fill) => fill !== 'none'));
            return { fills: fills.size };
        }"""
    )

    assert info["fills"] >= 3, f"chord arcs share colours: {info['fills']} distinct fills"

    return


_SMALL_TREE = {
    "root": {
        "name": "Root",
        "children": [
            {"name": "A", "children": [{"name": "A1", "value": 3}, {"name": "A2", "value": 2}]},
            {"name": "B", "children": [{"name": "B1", "value": 4}]},
        ],
    },
}


@testbase.attach.parameter(create_page, identifier="page")
def test_hierarchy_types_dispatch_on_type_key(page, base_url):
    """
        type="sunburst" draws arcs and type="treemap" draws rectangles without
        a layout attribute, coloured by top-level branch, and the data object
        is left untouched.
    """

    frame = _ready_preview(page, base_url, "sunburst")
    shapes = {}
    for type_key in ["sunburst", "treemap"]:
        info = frame.evaluate(
            """async ([typeKey, data]) => {
                document.body.innerHTML = `<mj-chart type="${typeKey}" style="height:240px"></mj-chart>`;
                const chart = document.querySelector('mj-chart');
                const before = JSON.stringify(data);
                chart.data = data;
                await new Promise((resolve) => setTimeout(resolve, 600));
                const svg = chart.shadowRoot.querySelector('svg');
                const marks = Array.from(svg.querySelectorAll('[tabindex]'));
                return {
                    state: chart.chartState,
                    tags: Array.from(new Set(marks.map((mark) => mark.tagName))),
                    fills: new Set(marks.map((mark) => mark.getAttribute('fill'))).size,
                    untouched: JSON.stringify(data) === before
                };
            }""",
            [type_key, _SMALL_TREE],
        )
        assert info["state"] == "ready", f"{type_key}: state {info['state']}"
        assert info["untouched"] is True, f"{type_key}: the renderer wrote into the data"
        assert info["fills"] >= 2, f"{type_key}: branches share one colour"
        shapes[type_key] = info["tags"]

    assert "path" in shapes["sunburst"], f"sunburst drew {shapes['sunburst']}"
    assert "rect" in shapes["treemap"], f"treemap drew {shapes['treemap']}"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_tree_types_render_ready_with_a_node_table(page, base_url):
    """
        The five tree types finish their render (no circular-structure
        error from parent back-pointers) and publish a node table.
    """

    frame = _ready_preview(page, base_url, "tree")
    for type_key in ["tree", "dendrogram", "org-chart", "mindmap", "decision-tree"]:
        info = frame.evaluate(
            """async ([typeKey, data]) => {
                document.body.innerHTML = `<mj-chart type="${typeKey}" style="height:260px"></mj-chart>`;
                const chart = document.querySelector('mj-chart');
                let rendered = 0;
                chart.addEventListener('mj-chart-render', () => { rendered = rendered + 1; });
                chart.data = data;
                await new Promise((resolve) => setTimeout(resolve, 600));
                const table = chart.shadowRoot.querySelector('[data-chart-table] table');
                return {
                    state: chart.chartState,
                    rendered: rendered,
                    rows: table !== null ? table.querySelectorAll('tbody tr').length : 0,
                    serialisable: (() => { try { JSON.stringify(data); return true; } catch (error) { return false; } })()
                };
            }""",
            [type_key, _SMALL_TREE],
        )
        assert info["state"] == "ready", f"{type_key}: state {info['state']}"
        assert info["rendered"] >= 1, f"{type_key}: mj-chart-render never fired"
        assert info["rows"] >= 6, f"{type_key}: node table has {info['rows']} rows"
        assert info["serialisable"] is True, f"{type_key}: the data gained back-pointers"

    return


# ---------------------------------------------------------------------------
# Comparison and trend renderers (bar, bullet, radar, slope, line, sparkline,
# streamgraph): behaviour checks on markup mounted in a playground frame.
# ---------------------------------------------------------------------------

def _mount_charts(page, base_url, markup):
    """
        Open a chart-type playground, replace its preview body with chart
        markup and wait until every <mj-chart> has settled.

        :param markup: The HTML to place in the preview body.

        :returns: The preview Frame.
    """

    page.goto(base_url + "/chart-type/line")
    handle = page.wait_for_selector("[data-testid=playground-preview]")
    frame = handle.content_frame()
    frame.wait_for_function(
        "() => customElements.get('mj-chart') !== undefined",
        timeout=15000,
    )
    frame.evaluate("markup => { document.body.innerHTML = markup; }", markup)
    frame.wait_for_function(
        """() => {
            const charts = Array.from(document.querySelectorAll('mj-chart'));
            return charts.length > 0 && charts.every((chart) => {
                const state = chart.chartState;
                return state === 'ready' || state === 'empty' || state === 'error';
            });
        }""",
        timeout=10000,
    )
    return frame


def _chart(type_key, data, attrs=""):
    """
        Markup of one <mj-chart> with inline JSON data.
    """

    markup = (
        f'<mj-chart type="{type_key}" {attrs} style="height:240px;width:480px">'
        f'<script type="application/json">{json.dumps(data)}</script></mj-chart>'
    )
    return markup


@testbase.attach.parameter(create_page, identifier="page")
def test_line_places_date_x_values_on_a_time_scale(page, base_url):
    """
        ISO date x values are spaced by elapsed time and drawn in date order,
        not evenly in data order.
    """

    frame = _mount_charts(page, base_url, _chart("line", {"series": [{"name": "Rev", "points": [
        {"x": "2025-01-01", "y": 10}, {"x": "2025-12-31", "y": 30}, {"x": "2025-01-02", "y": 12}
    ]}]}))
    xs = frame.evaluate(
        """() => Array.from(document.querySelector('mj-chart').shadowRoot
            .querySelectorAll('circle[part=hit]')).map((hit) => Number(hit.getAttribute('cx')))"""
    )
    assert len(xs) == 3, f"expected 3 point targets, got {xs}"
    assert xs == sorted(xs), f"points are not in date order: {xs}"
    assert xs[1] - xs[0] < (xs[2] - xs[0]) * 0.02, f"one day is not drawn as a small gap: {xs}"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_radar_spokes_share_one_scale(page, base_url):
    """
        A single radar series is drawn against one shared scale, so spokes
        with different values have different radii (not a full ring).
    """

    frame = _mount_charts(page, base_url, _chart("radar", {
        "categories": ["A", "B", "C", "D"], "series": [{"name": "S", "values": [80, 20, 50, 5]}]
    }))
    radii = frame.evaluate(
        """() => {
            const root = document.querySelector('mj-chart').shadowRoot;
            const dots = Array.from(root.querySelectorAll('circle[part=dot]'));
            const ring = root.querySelector('[part=axes] line');
            const cx = Number(ring.getAttribute('x1'));
            const cy = Number(ring.getAttribute('y1'));
            return dots.map((dot) => Math.hypot(Number(dot.getAttribute('cx')) - cx, Number(dot.getAttribute('cy')) - cy));
        }"""
    )
    assert len(radii) == 4
    assert abs(radii[0] / radii[1] - 4) < 0.05, f"80 is not four times 20: {radii}"
    assert abs(radii[0] / radii[3] - 16) < 0.3, f"80 is not sixteen times 5: {radii}"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_streamgraph_wiggle_baseline_moves(page, base_url):
    """
        The default wiggle baseline displaces the stack (its lower edge is
        not flat), while baseline="zero" keeps a flat bottom edge.
    """

    data = {"categories": ["a", "b", "c", "d", "e"], "series": [
        {"name": "A", "values": [10, 40, 15, 60, 20]},
        {"name": "B", "values": [50, 20, 70, 10, 40]},
        {"name": "C", "values": [5, 30, 10, 40, 25]}
    ]}
    frame = _mount_charts(page, base_url,
                          _chart("streamgraph", data, 'curve="linear"') +
                          _chart("streamgraph", data, 'curve="linear" baseline="zero"'))
    spreads = frame.evaluate(
        """() => Array.from(document.querySelectorAll('mj-chart')).map((chart) => {
            const path = chart.shadowRoot.querySelector('path[part=stream]').getAttribute('d');
            const ys = Array.from(path.matchAll(/[ML]([-0-9.]+),([-0-9.]+)/g)).map((m) => Number(m[2]));
            const bottom = ys.slice(ys.length / 2);
            return Math.max(...bottom) - Math.min(...bottom);
        })"""
    )
    assert spreads[0] > 10, f"wiggle baseline is flat (spread {spreads[0]})"
    assert spreads[1] < 0.5, f"zero baseline is not flat (spread {spreads[1]})"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_sparkline_bars_start_at_zero_inside_the_drawing(page, base_url):
    """
        Bar sparkline heights are proportional to the values (zero-based)
        and no bar is cut by the drawing edge.
    """

    frame = _mount_charts(page, base_url,
                          '<mj-chart type="sparkline" sparkline-variant="bar" style="width:200px;height:40px">'
                          '<script type="application/json">{"series":[{"name":"P","values":[50,55,60]}]}'
                          '</script></mj-chart>')
    bars = frame.evaluate(
        """() => Array.from(document.querySelector('mj-chart').shadowRoot
            .querySelectorAll('rect[part=spark-bar]')).map((bar) => ({
                x: Number(bar.getAttribute('x')), width: Number(bar.getAttribute('width')),
                height: Number(bar.getAttribute('height'))
            }))"""
    )
    assert len(bars) == 3
    assert abs(bars[0]["height"] / bars[2]["height"] - 50 / 60) < 0.02, f"bars are not zero-based: {bars}"
    assert bars[0]["x"] >= 0, f"first bar starts left of the drawing: {bars}"
    assert bars[2]["x"] + bars[2]["width"] <= 200, f"last bar ends past the drawing: {bars}"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_bar_keeps_duplicate_categories_and_escapes_nothing(page, base_url):
    """
        Two categories with the same label keep their own bars and values,
        a null value draws no bar, and labels show "R&D" as written.
    """

    frame = _mount_charts(page, base_url, _chart("column", {
        "categories": ["Jan", "Feb", "Jan", "R&D"], "series": [{"name": "S", "values": [1, 2, 9, None]}]
    }))
    result = frame.evaluate(
        """() => {
            const root = document.querySelector('mj-chart').shadowRoot;
            return {
                labels: Array.from(root.querySelectorAll('rect[part=bar]')).map((bar) => bar.getAttribute('aria-label')),
                texts: Array.from(root.querySelectorAll('svg text')).map((text) => text.textContent)
            };
        }"""
    )
    assert result["labels"] == ["S, Jan: 1", "S, Feb: 2", "S, Jan: 9"], result["labels"]
    assert "R&D" in result["texts"], result["texts"]

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_bullet_defaults_to_horizontal_rows(page, base_url):
    """
        Without an orientation the bullets are horizontal rows (the
        registered default), each a capped-thickness band.
    """

    frame = _mount_charts(page, base_url, _chart("bullet", {"series": [
        {"name": "Revenue", "value": 275, "target": 300, "ranges": [350, 250, 200]}
    ]}))
    bar = frame.evaluate(
        """() => {
            const bar = document.querySelector('mj-chart').shadowRoot.querySelector('rect[part=bullet-bar]');
            return { width: Number(bar.getAttribute('width')), height: Number(bar.getAttribute('height')) };
        }"""
    )
    assert bar["width"] > bar["height"] * 4, f"bullet is not horizontal: {bar}"
    assert bar["height"] <= 32 * 0.4 + 0.01, f"bullet band is not capped: {bar}"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_slope_rejects_more_than_two_periods(page, base_url):
    """
        A slope chart with three periods shows the render error instead of
        silently dropping the third period.
    """

    frame = _mount_charts(page, base_url, _chart("slope", {
        "categories": ["2020", "2022", "2024"], "series": [{"name": "S", "values": [1, 2, 3]}]
    }))
    state = frame.evaluate("() => document.querySelector('mj-chart').chartState")
    assert state == "error", f"slope with three periods rendered as {state}"

    return


# ---------------------------------------------------------------------------
# Distribution and relationship renderers (histogram family, boxplot, violin,
# swarm, qq, scatter / bubble, correlation matrix).
# ---------------------------------------------------------------------------

def _distribution_parts(frame, part, attributes):
    """
        For every <mj-chart> in the frame, the requested attributes of its
        marks with the given `part`.

        :param part: The part name, e.g. "bar".
        :param attributes: Attribute names to read from each mark.
        :returns: A list (one entry per chart) of lists of attribute dicts.
    """

    result = frame.evaluate(
        """([part, attributes]) => Array.from(document.querySelectorAll('mj-chart')).map((chart) =>
            Array.from(chart.shadowRoot.querySelectorAll(`[part~="${part}"]`)).map((mark) => {
                const values = {};
                for (const name of attributes) {
                    values[name] = mark.getAttribute(name);
                }
                return values;
            }))""",
        [part, attributes],
    )
    return result


@testbase.attach.parameter(create_page, identifier="page")
def test_density_and_frequency_polygon_draw_their_own_type(page, base_url):
    """
        type="density" draws one density curve per series (no bars) and
        type="frequency-polygon" draws polygon points (no bars), without any
        mode attribute.
    """

    samples = {"series": [
        {"name": "A", "samples": [48, 51, 53, 55, 56, 57, 58, 60, 61, 63]},
        {"name": "B", "samples": [55, 60, 63, 65, 66, 67, 68, 70, 72, 75]},
    ]}
    frame = _mount_charts(page, base_url, _chart("density", samples) + _chart("frequency-polygon", samples))
    bars = _distribution_parts(frame, "bar", ["x"])
    curves = _distribution_parts(frame, "density-line", ["d"])
    points = _distribution_parts(frame, "polygon-point", ["cx"])

    assert bars == [[], []], f"density / polygon drew histogram bars: {bars}"
    assert len(curves[0]) == 2, f"expected 2 density curves, got {len(curves[0])}"
    assert len(points[1]) > 0, "frequency-polygon drew no polygon points"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_boxplot_draws_every_series_and_ignores_nulls(page, base_url):
    """
        Two series x two categories draw four boxes at four positions, and a
        null sample is missing data, not an outlier at zero.
    """

    data = {"categories": ["A", "B"], "series": [
        {"name": "S1", "groups": [{"category": "A", "samples": [10, 11, 12, None, 13, 14]},
                                  {"category": "B", "samples": [5, 6, 7, 8]}]},
        {"name": "S2", "groups": [{"category": "A", "samples": [9, 10, 11]},
                                  {"category": "B", "samples": [1, 2, 3]}]},
    ]}
    frame = _mount_charts(page, base_url, _chart("boxplot", data))
    boxes = _distribution_parts(frame, "boxplot-hit", ["x", "aria-label"])[0]
    outliers = _distribution_parts(frame, "outlier", ["cy"])[0]

    assert len(boxes) == 4, f"expected 4 boxes, got {len(boxes)}"
    assert len({box["x"] for box in boxes}) == 4, f"boxes overlap: {[box['x'] for box in boxes]}"
    assert outliers == [], f"a null sample was drawn as an outlier: {outliers}"
    assert "median 12" in boxes[0]["aria-label"], f"null counted in the median: {boxes[0]['aria-label']}"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_qq_tail_points_follow_the_normal_quantiles(page, base_url):
    """
        With n = 40 the extreme points (p < 0.02425) use the tail branch of
        the normal quantile function: a sample of exact normal quantiles lies
        on the reference line, so theoretical and observed agree.
    """

    probit = [-2.2414, -1.7805, -1.5341, -1.3581, -1.2160, -1.0939, -0.9842, -0.8853,
              -0.7926, -0.7063, -0.6239, -0.5464, -0.4705, -0.3989, -0.3264, -0.2533,
              -0.1891, -0.1257, -0.0627, -0.0000]
    samples = probit + [-value for value in reversed(probit)]
    frame = _mount_charts(page, base_url, _chart("qq", {"series": [{"name": "Z", "samples": samples}]}))
    labels = [mark["aria-label"] for mark in _distribution_parts(frame, "qq-point", ["aria-label"])[0]]

    assert len(labels) == 40, f"expected 40 points, got {len(labels)}"
    for label in (labels[0], labels[-1]):
        numbers = [float(text.replace("−", "-")) for text in
                   label.replace(",", " ").split() if text.replace("−", "-").lstrip("-").replace(".", "").isdigit()]
        theoretical, observed = numbers[0], numbers[1]
        assert abs(theoretical - observed) < 0.15, f"tail point off the line: {label}"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_swarm_keeps_tied_values_apart(page, base_url):
    """
        Tied samples each get their own position in a swarm.
    """

    data = {"series": [{"name": "S", "groups": [{"category": "a", "samples": [5, 5, 5, 5, 5, 5, 7, 7, 7, 9]}]}]}
    frame = _mount_charts(page, base_url, _chart("swarm", data))
    points = _distribution_parts(frame, "point", ["cx", "cy"])[0]

    assert len(points) == 10, f"expected 10 dots, got {len(points)}"
    assert len({(point["cx"], point["cy"]) for point in points}) == 10, "tied values share a position"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_bubble_area_is_proportional_to_size(page, base_url):
    """
        Bubble radii follow sqrt(size): sizes 90 and 100 differ by about 5%
        in radius, not by the full min-to-max radius range.
    """

    data = {"series": [{"name": "S", "points": [{"x": 1, "y": 1, "size": 90}, {"x": 2, "y": 2, "size": 100}]}]}
    frame = _mount_charts(page, base_url, _chart("bubble", data))
    radii = sorted(float(point["r"]) for point in _distribution_parts(frame, "point", ["r"])[0])

    assert len(radii) == 2, f"expected 2 bubbles, got {radii}"
    ratio = (radii[0] / radii[1]) ** 2
    assert abs(ratio - 0.9) < 0.01, f"area ratio {ratio:.3f} is not 90 / 100"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_correlation_matrix_negative_colours_deepen(page, base_url):
    """
        On the diverging ramp r = -0.95 is a deeper colour than r = -0.1
        (the negative side used to be inverted).
    """

    data = {"categories": ["a", "b"], "series": [
        {"name": "a", "values": [1, -0.95]}, {"name": "b", "values": [-0.1, 1]}]}
    frame = _mount_charts(page, base_url, _chart("correlation-matrix", data))
    cells = _distribution_parts(frame, "cell", ["aria-label", "fill"])[0]
    share = {}
    for cell in cells:
        percent = cell["fill"].split("%")[0].split()[-1]
        share[cell["aria-label"].split(": ")[-1].replace("−", "-")] = float(percent)

    assert share["-0.95"] > share["-0.1"], f"negative ramp inverted: {share}"
    assert share["-0.95"] >= 90, f"strong negative correlation is pale: {share}"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_violin_horizontal_stays_inside_the_drawing(page, base_url):
    """
        orientation="horizontal" lays violins on their side: every outline
        point stays inside the drawing's height.
    """

    data = {"categories": ["A", "B"], "series": [{"name": "S", "groups": [
        {"category": "A", "samples": [1, 2, 2, 3, 3, 3, 4]}, {"category": "B", "samples": [3, 4, 5, 5, 6]}]}]}
    frame = _mount_charts(page, base_url, _chart("violin", data, 'orientation="horizontal"'))
    outlines = [mark["d"] for mark in _distribution_parts(frame, "violin", ["d"])[0]]
    height = frame.evaluate(
        "() => Number(document.querySelector('mj-chart').shadowRoot.querySelector('svg').viewBox.baseVal.height)"
    )

    assert len(outlines) == 2, f"expected 2 violins, got {len(outlines)}"
    for outline in outlines:
        ys = [float(pair.split(",")[1]) for pair in outline.replace("M", " ").replace("L", " ").replace("Z", " ").split()]
        assert max(ys) + 16 <= height, f"violin outline leaves the drawing: max y {max(ys)} of {height}"

    return


# ---------------------------------------------------------------------------
# Statistical, financial and project renderers (errorbar, control, survival,
# forest, ohlc, tornado, gantt / roadmap, timeline / milestone, resource).
# ---------------------------------------------------------------------------

_CANDLES = [
    {"t": "2025-04-01", "o": 10, "h": 12, "l": 9, "c": 11, "v": 100},
    {"t": "2025-04-02", "o": 11, "h": 11.5, "l": 9.5, "c": 10, "v": 80},
    {"t": "2025-04-03", "o": 10, "h": 13, "l": 10, "c": 12.5, "v": 120},
]


@testbase.attach.parameter(create_page, identifier="page")
def test_alias_types_draw_their_own_variant(page, base_url):
    """
        type="ohlc" draws tick bars (no bodies), type="candlestick" draws
        bodies, type="roadmap" draws no dependency arrows and
        type="milestone" draws diamond markers -- chosen by the type key,
        not by the inline style.
    """

    tasks = {"tasks": [
        {"id": "a", "label": "A", "start": "2025-01-01", "end": "2025-01-10"},
        {"id": "b", "label": "B", "start": "2025-01-11", "end": "2025-01-20", "depends": ["a"]},
    ]}
    events = {"events": [{"label": "One", "date": "2025-01-01"}, {"label": "Two", "date": "2025-03-01"}]}
    markup = (
        _chart("ohlc", {"candles": _CANDLES}) + _chart("candlestick", {"candles": _CANDLES}) +
        _chart("gantt", tasks) + _chart("roadmap", tasks) +
        _chart("timeline", events) + _chart("milestone", events)
    )
    frame = _mount_charts(page, base_url, markup)
    info = frame.evaluate(
        """() => Array.from(document.querySelectorAll('mj-chart')).map((chart) => {
            const svg = chart.shadowRoot.querySelector('svg');
            return {
                bodies: svg.querySelectorAll('[part=candle] rect').length,
                arrows: svg.querySelectorAll('[part~=dependency]').length,
                diamonds: svg.querySelectorAll('polygon[part=marker]').length,
                circles: svg.querySelectorAll('circle[part=marker]').length
            };
        })"""
    )
    assert info[0]["bodies"] == 0, f"ohlc drew candle bodies: {info[0]}"
    assert info[1]["bodies"] == 3, f"candlestick did not draw bodies: {info[1]}"
    assert info[2]["arrows"] == 1, f"gantt lost its dependency arrow: {info[2]}"
    assert info[3]["arrows"] == 0, f"roadmap drew dependency arrows: {info[3]}"
    assert info[4]["circles"] == 2 and info[4]["diamonds"] == 0, f"timeline markers: {info[4]}"
    assert info[5]["diamonds"] == 2 and info[5]["circles"] == 0, f"milestone markers: {info[5]}"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_timeline_spreads_events_over_the_width_and_lanes_fit(page, base_url):
    """
        Without an orientation attribute the timeline runs across the whole
        width, and three lanes share the chart height (every marker inside
        the drawing).
    """

    events = {"events": [
        {"label": "Kickoff", "date": "2025-01-06", "group": "Eng"},
        {"label": "Beta", "date": "2025-04-01", "group": "Ops"},
        {"label": "GA", "date": "2025-07-07", "group": "Sales"},
    ]}
    frame = _mount_charts(page, base_url, _chart("timeline", events))
    info = frame.evaluate(
        """() => {
            const svg = document.querySelector('mj-chart').shadowRoot.querySelector('svg');
            const box = svg.viewBox.baseVal;
            const markers = Array.from(svg.querySelectorAll('[part=marker]')).map((marker) => {
                const rect = marker.getBBox();
                const matrix = marker.getCTM();
                return { x: rect.x + matrix.e, y: rect.y + rect.height + matrix.f };
            });
            return { width: box.width, height: box.height, markers: markers };
        }"""
    )
    xs = [marker["x"] for marker in info["markers"]]
    assert len(xs) == 3, f"expected 3 markers: {info}"
    assert max(xs) - min(xs) > info["width"] * 0.6, f"events are squeezed: {xs} in {info['width']}"
    assert all(marker["y"] <= info["height"] for marker in info["markers"]), f"a lane is off the chart: {info}"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_gantt_markers_phases_window_and_open_tasks(page, base_url):
    """
        type="gantt" draws markers (focusable, mj-chart-marker-click with the
        index) and phase bands, a start-only task runs to the edge (dashed),
        a milestone task is a diamond, a task outside the start-date /
        end-date window shows an edge arrow, scale="week" puts the ticks on
        Mondays, and show-progress / show-dependencies switch fills and
        arrows off (moved from mj-gantt-chart, WW-1498).
    """

    data = {
        "tasks": [
            {"id": "a", "label": "Design", "start": "2026-03-02", "end": "2026-03-13", "progress": 0.5},
            {"id": "b", "label": "Build", "start": "2026-03-16", "end": "2026-04-03", "depends": ["a"]},
            {"id": "c", "label": "Support", "start": "2026-03-09"},
            {"id": "d", "label": "Beta", "start": "2026-04-06", "milestone": True},
            {"id": "e", "label": "Later", "start": "2026-06-01", "end": "2026-06-12"},
        ],
        "markers": [{"label": "Review", "date": "2026-03-20"}],
        "phases": [{"label": "Build phase", "start": "2026-03-16", "end": "2026-04-03"}],
    }
    window = 'start-date="2026-03-01" end-date="2026-04-30" scale="week"'
    markup = (
        _chart("gantt", data, window) +
        _chart("gantt", data, window + ' show-progress="false" show-dependencies="false"')
    )
    frame = _mount_charts(page, base_url, markup)
    info = frame.evaluate(
        """() => {
            const charts = Array.from(document.querySelectorAll('mj-chart'));
            const clicks = [];
            charts[0].addEventListener('mj-chart-marker-click', (event) => clicks.push(event.detail));
            const sr = charts[0].shadowRoot;
            const mark = (key) => sr.querySelector(`[data-mark="${key}"]`);
            mark('marker:0').dispatchEvent(new MouseEvent('click', { bubbles: true }));
            const ticks = Array.from(sr.querySelectorAll('[part~=time-axis]')).map((node) => node.textContent);
            return {
                markers: sr.querySelectorAll('[part~=milestone-marker]').length,
                markerFocusable: mark('marker:0').getAttribute('tabindex') !== null,
                phases: sr.querySelectorAll('[part~=phase-band]').length,
                openDash: mark('task:2').querySelector('rect').getAttribute('stroke-dasharray'),
                openLabel: mark('task:2').getAttribute('aria-label'),
                milestoneShape: mark('task:3').querySelector('polygon') !== null && mark('task:3').querySelector('rect') === null,
                outsideShape: mark('task:4').querySelector('polygon') !== null,
                fills: sr.querySelectorAll('[part~=task-bar-fill]').length,
                arrows: sr.querySelectorAll('[part~=dependency-arrow]').length,
                ticks: ticks,
                clicks: clicks,
                offFills: charts[1].shadowRoot.querySelectorAll('[part~=bar-fill]').length,
                offArrows: charts[1].shadowRoot.querySelectorAll('[part~=dependency]').length
            };
        }"""
    )

    assert info["markers"] == 1 and info["markerFocusable"] is True, f"markers: {info}"
    assert info["clicks"] == [{"label": "Review", "date": "2026-03-20", "index": 0}], f"marker click: {info}"
    assert info["phases"] == 1, f"phase bands: {info}"
    assert info["openDash"] == "5 3" and "no end date" in info["openLabel"], f"open-ended task: {info}"
    assert info["milestoneShape"] is True, f"milestone task: {info}"
    assert info["outsideShape"] is True, f"task outside the window: {info}"
    assert info["fills"] == 1 and info["arrows"] == 1, f"fills / arrows: {info}"
    assert info["offFills"] == 0 and info["offArrows"] == 0, f"show-progress / show-dependencies off: {info}"
    assert len(info["ticks"]) >= 4, f"week ticks: {info}"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_gantt_groups_collapse_and_rows_set_the_height(page, base_url):
    """
        Declared groups give the order and names of the gantt header rows;
        a header is a button that collapses its tasks (collapsed-groups
        attribute, mj-chart-group-toggle) and expands them again; a chart
        without a height grows with its rows (moved from mj-gantt-chart,
        WW-1498).
    """

    tasks = [{"id": f"t{index}", "label": f"Task {index}", "start": "2026-03-02", "end": "2026-03-06",
              "group": "late" if index >= 6 else "early"} for index in range(12)]
    data = {"groups": [{"id": "late", "label": "Late work"}, {"id": "early", "label": "Early work"}], "tasks": tasks}
    frame = _mount_charts(page, base_url, '<mj-chart type="gantt" style="width:600px">'
                          f'<script type="application/json">{json.dumps(data)}</script></mj-chart>')
    info = frame.evaluate(
        """async () => {
            const chart = document.querySelector('mj-chart');
            const sr = chart.shadowRoot;
            const toggles = [];
            chart.addEventListener('mj-chart-group-toggle', (event) => toggles.push(event.detail));
            const height = chart.getBoundingClientRect().height;
            const headers = Array.from(sr.querySelectorAll('[part~=group-row]')).map((node) => node.getAttribute('aria-label'));
            const header = sr.querySelector('[data-mark="group:0"]');
            header.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
            await new Promise((resolve) => setTimeout(resolve, 300));
            const collapsed = {
                attribute: chart.getAttribute('collapsed-groups'),
                bars: sr.querySelectorAll('[part~=task-bar]').length,
                expanded: sr.querySelector('[data-mark="group:0"]').getAttribute('aria-expanded'),
                rows: sr.querySelectorAll('[data-chart-table] tbody tr').length
            };
            sr.querySelector('[data-mark="group:0"]').dispatchEvent(new MouseEvent('click', { bubbles: true }));
            await new Promise((resolve) => setTimeout(resolve, 300));
            return {
                height: height, headers: headers, toggles: toggles, collapsed: collapsed,
                attributeAfter: chart.getAttribute('collapsed-groups'),
                barsAfter: sr.querySelectorAll('[part~=task-bar]').length
            };
        }"""
    )

    assert info["height"] >= 12 * 32, f"the chart did not grow with its rows: {info}"
    assert info["headers"][0].startswith("Late work, group of 6 tasks"), f"declared group order: {info}"
    assert info["collapsed"]["attribute"] == '["late"]', f"collapsed-groups: {info}"
    assert info["collapsed"]["bars"] == 6 and info["collapsed"]["expanded"] == "false", f"collapse: {info}"
    assert info["collapsed"]["rows"] == 12, f"the table keeps collapsed tasks: {info}"
    assert info["toggles"][0] == {"group": "late", "collapsed": True, "collapsedGroups": ["late"]}, f"event: {info}"
    assert info["attributeAfter"] is None and info["barsAfter"] == 12, f"expand: {info}"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_roadmap_lanes_pack_bars_under_period_and_bucket_columns(page, base_url):
    """
        type="roadmap" draws one lane per group in which bars that do not
        overlap share a row and overlapping ones stack, period column
        headers (scale="month"), status icons, markers, phase and today rows;
        mode="bucket" places bars in the bucket columns and counts the ones
        it cannot place (moved from mj-roadmap-chart, WW-1498).
    """

    calendar = {
        "groups": [{"id": "p", "label": "Platform"}],
        "tasks": [
            {"id": "a", "label": "First", "start": "2026-01-05", "end": "2026-01-30", "group": "p", "status": "done"},
            {"id": "b", "label": "Second", "start": "2026-02-09", "end": "2026-03-13", "group": "p", "status": "blocked"},
            {"id": "c", "label": "Overlap", "start": "2026-01-19", "end": "2026-02-20", "group": "p"},
        ],
        "markers": [{"label": "Launch", "date": "2026-02-02"}],
        "phases": [{"label": "Plan", "start": "2026-01-05", "end": "2026-01-16"}],
    }
    buckets = {
        "groups": [{"id": "g", "label": "Growth"}],
        "buckets": [{"id": "now", "label": "Now"}, {"id": "next", "label": "Next"}],
        "tasks": [
            {"label": "One", "group": "g", "bucket": "next"},
            {"label": "Two", "group": "g", "bucket": "someday"},
        ],
    }
    frame = _mount_charts(page, base_url, _chart("roadmap", calendar, 'scale="month"') +
                          _chart("roadmap", buckets, 'mode="bucket"'))
    info = frame.evaluate(
        """() => {
            const charts = Array.from(document.querySelectorAll('mj-chart'));
            const box = (sr, key) => {
                const rect = sr.querySelector(`[data-mark="${key}"] rect`);
                return { x: Number(rect.getAttribute('x')), y: Number(rect.getAttribute('y')), w: Number(rect.getAttribute('width')) };
            };
            const one = charts[0].shadowRoot;
            const two = charts[1].shadowRoot;
            return {
                headers: Array.from(one.querySelectorAll('[part~=column-header]')).map((node) => node.lastChild.textContent),
                a: box(one, 'task:0'), b: box(one, 'task:1'), c: box(one, 'task:2'),
                icon: one.querySelector('[data-mark="task:1"] text').textContent,
                markers: one.querySelectorAll('[part~=milestone-marker]').length,
                phaseLabels: Array.from(one.querySelectorAll('[part~=phase-label]')).map((node) => node.lastChild.textContent),
                bucketHeaders: Array.from(two.querySelectorAll('[part~=column-header]')).map((node) => node.lastChild.textContent),
                bucketBar: box(two, 'task:0'),
                bucketWidth: two.querySelector('svg').viewBox.baseVal.width,
                placed: two.querySelectorAll('[part~=initiative-bar]').length,
                note: two.querySelector('[part~=unplaced-note]') !== null ? two.querySelector('[part~=unplaced-note]').textContent : null,
                table: Array.from(two.querySelectorAll('[data-chart-table] tbody tr')).map((row) => row.textContent)
            };
        }"""
    )

    assert info["headers"] == ["Jan 2026", "Feb 2026", "Mar 2026"], f"month columns: {info}"
    assert info["a"]["y"] == info["b"]["y"], f"bars that do not overlap should share a row: {info}"
    assert info["c"]["y"] > info["a"]["y"], f"the overlapping bar should stack: {info}"
    assert info["icon"] == "⊘", f"blocked icon: {info}"
    assert info["markers"] == 1 and info["phaseLabels"] == ["Plan"], f"markers / phases: {info}"
    assert info["bucketHeaders"] == ["Now", "Next"], f"bucket columns: {info}"
    assert info["placed"] == 1 and info["bucketBar"]["x"] > info["bucketWidth"] * 0.4, f"bucket placement: {info}"
    assert info["note"] is not None and info["note"].startswith("1 of 2"), f"unplaced note: {info}"
    assert any("Not placed" in row for row in info["table"]), f"table: {info}"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_milestone_kinds_dim_past_phases_and_window(page, base_url):
    """
        type="milestone" draws an event's kind (freeze = triangle, tag =
        circle, release = diamond), phase bands and the today line, hides
        events outside the start-date / end-date window (the table keeps
        them), and with dim-past fades past events and names their state
        (moved from mj-milestone-timeline, WW-1498).
    """

    frame = _mount_charts(page, base_url, '<mj-chart type="milestone" style="height:200px;width:600px"></mj-chart>')
    info = frame.evaluate(
        """async () => {
            const chart = document.querySelector('mj-chart');
            const day = (offset) => {
                const date = new Date();
                date.setDate(date.getDate() + offset);
                return date.getFullYear() + '-' + String(date.getMonth() + 1).padStart(2, '0') + '-' + String(date.getDate()).padStart(2, '0');
            };
            chart.setAttribute('dim-past', '');
            chart.setAttribute('start-date', day(-30));
            chart.setAttribute('end-date', day(30));
            chart.data = {
                events: [
                    { label: 'Freeze', date: day(-10), kind: 'freeze' },
                    { label: 'Tag', date: day(5), kind: 'tag' },
                    { label: 'Release', date: day(20), kind: 'release' },
                    { label: 'Outside', date: day(60), kind: 'release' }
                ],
                phases: [{ label: 'Hardening', start: day(-10), end: day(5) }]
            };
            await new Promise((resolve) => setTimeout(resolve, 300));
            const sr = chart.shadowRoot;
            const mark = (index) => sr.querySelector(`[data-mark="event:${index}"]`);
            return {
                freeze: { tag: mark(0).localName, points: mark(0).getAttribute('points').trim().split(' ').length, opacity: mark(0).getAttribute('opacity'), label: mark(0).getAttribute('aria-label') },
                tag: { tag: mark(1).localName, opacity: mark(1).getAttribute('opacity'), label: mark(1).getAttribute('aria-label') },
                release: mark(2).localName,
                outside: mark(3),
                rows: sr.querySelectorAll('[data-chart-table] tbody tr').length,
                phases: sr.querySelectorAll('[part~=phase-band]').length,
                today: sr.querySelectorAll('[part~=today-marker]').length
            };
        }"""
    )

    assert info["freeze"]["tag"] == "polygon" and info["freeze"]["points"] == 3, f"freeze triangle: {info}"
    assert info["freeze"]["opacity"] == "0.55" and info["freeze"]["label"].endswith("past"), f"dim-past: {info}"
    assert info["tag"]["tag"] == "circle" and info["tag"]["opacity"] is None, f"tag circle: {info}"
    assert "upcoming" in info["tag"]["label"], f"state in the name: {info}"
    assert info["release"] == "polygon", f"release diamond: {info}"
    assert info["outside"] is None and info["rows"] == 4, f"window: {info}"
    assert info["phases"] == 1 and info["today"] == 1, f"phases / today: {info}"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_dependency_graph_boxes_critical_path_and_cycle_event(page, base_url):
    """
        type="dependency-graph" draws labelled boxes with their status,
        highlights criticalPath nodes and the links between consecutive
        entries, and reports a cycle with mj-chart-cycle-detect once per
        data object, not on every redraw (moved from mj-dependency-graph,
        WW-1498).
    """

    frame = _mount_charts(page, base_url, '<mj-chart type="dependency-graph" style="height:300px;width:640px"></mj-chart>')
    info = frame.evaluate(
        """async () => {
            const chart = document.querySelector('mj-chart');
            const cycles = [];
            chart.addEventListener('mj-chart-cycle-detect', (event) => cycles.push(event.detail.cycles));
            chart.data = {
                nodes: [
                    { id: 'a', label: 'Alpha', status: 'done' }, { id: 'b', label: 'Beta', status: 'in-progress' },
                    { id: 'c', label: 'Gamma' }, { id: 'd', label: 'Delta', status: 'blocked' }
                ],
                links: [
                    { source: 'a', target: 'b' }, { source: 'b', target: 'c' }, { source: 'c', target: 'b' }, { source: 'a', target: 'd' }
                ],
                criticalPath: ['a', 'b', 'c']
            };
            await new Promise((resolve) => setTimeout(resolve, 300));
            await chart.redraw();
            const sr = chart.shadowRoot;
            const node = (index) => sr.querySelector(`[data-mark="node:${index}"]`);
            return {
                boxes: sr.querySelectorAll('[part~=node] rect').length,
                texts: Array.from(node(0).querySelectorAll('text')).map((text) => text.textContent),
                cycleTexts: Array.from(node(1).querySelectorAll('text')).map((text) => text.textContent),
                critical: sr.querySelectorAll('[part~=critical-path-node]').length,
                criticalEdges: sr.querySelectorAll('[part~=critical-path-edge]').length,
                cycleEdges: sr.querySelectorAll('[data-cycle-edge]').length,
                badges: sr.querySelectorAll('[part~=cycle-badge]').length,
                label: node(2).getAttribute('aria-label'),
                columns: Array.from(sr.querySelectorAll('[data-chart-table] thead th')).map((cell) => cell.textContent),
                cycles: cycles
            };
        }"""
    )

    assert info["boxes"] == 4 and info["texts"] == ["Alpha", "done"], f"boxes: {info}"
    assert info["cycleTexts"] == ["Beta", "in-progress", "⚠"], f"cycle badge: {info}"
    assert info["critical"] == 3 and info["criticalEdges"] == 2, f"critical path: {info}"
    assert info["cycleEdges"] == 1 and info["badges"] == 2, f"cycle drawing: {info}"
    assert "in a cycle" in info["label"] and "critical path" in info["label"], f"accessible name: {info}"
    assert "Status" in info["columns"] and "Critical path" in info["columns"], f"table: {info}"
    assert info["cycles"] == [[["b", "c"]]], f"mj-chart-cycle-detect once per data: {info}"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_resource_allocation_flags_summed_over_allocation(page, base_url):
    """
        Two concurrent allocations of 0.7 and 0.5 on a capacity-1 resource
        are stacked and the overlapping period is flagged as over capacity;
        a resource whose allocations never overlap is not flagged.
    """

    data = {"resources": [
        {"id": "bob", "label": "Bob", "capacity": 1, "allocations": [
            {"task": "API", "start": "2025-04-01", "end": "2025-04-25", "load": 0.7},
            {"task": "DB", "start": "2025-04-14", "end": "2025-04-30", "load": 0.5},
        ]},
        {"id": "eve", "label": "Eve", "capacity": 1, "allocations": [
            {"task": "QA", "start": "2025-04-01", "end": "2025-04-10", "load": 0.9},
            {"task": "Docs", "start": "2025-04-11", "end": "2025-04-20", "load": 0.9},
        ]},
    ]}
    frame = _mount_charts(page, base_url, _chart("resource-allocation", data))
    labels = frame.evaluate(
        """() => Array.from(document.querySelector('mj-chart').shadowRoot
            .querySelectorAll('[part=over-allocation]')).map((mark) => mark.getAttribute('aria-label'))"""
    )
    assert len(labels) == 1, f"expected one over-capacity period: {labels}"
    assert labels[0].startswith("Bob") and "120%" in labels[0], f"wrong over-capacity flag: {labels}"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_survival_curve_reaches_the_last_censored_observation(page, base_url):
    """
        The step curve continues past the last event to the censored
        observation at t = 12 (it used to stop at t = 6).
    """

    data = {"series": [{"name": "KM", "points": [
        {"x": 0, "y": 1.0}, {"x": 6, "y": 0.8}, {"x": 12, "y": 0.8, "censored": True},
    ]}]}
    frame = _mount_charts(page, base_url, _chart("kaplan-meier", data))
    info = frame.evaluate(
        """() => {
            const svg = document.querySelector('mj-chart').shadowRoot.querySelector('svg');
            const tick = svg.querySelector('[part=censor-tick]');
            const paths = Array.from(svg.querySelectorAll('path')).map((path) => path.getAttribute('d'));
            const curve = paths.find((d) => d.indexOf('H') >= 0 && d.indexOf('V') >= 0);
            const last = curve.trim().split(' ').pop();
            return { end: Number(last.slice(1)), tick: Number(tick.getAttribute('x1')) };
        }"""
    )
    assert abs(info["end"] - info["tick"]) < 0.5, f"curve ends before the censored time: {info}"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_control_chart_reads_dates_and_flags_points_beyond_the_limits(page, base_url):
    """
        Date x values give a drawn line (no NaN) and a point above the UCL
        is flagged without an ooc field; a null y is a gap, not a zero.
    """

    data = {
        "series": [{"name": "Daily", "points": [
            {"x": "2025-01-01", "y": 5}, {"x": "2025-01-02", "y": 6}, {"x": "2025-01-03", "y": None},
            {"x": "2025-01-04", "y": 9.5}, {"x": "2025-01-05", "y": 5.2},
        ]}],
        "control_limits": {"ucl": 8},
    }
    frame = _mount_charts(page, base_url, _chart("control-chart", data))
    info = frame.evaluate(
        """() => {
            const svg = document.querySelector('mj-chart').shadowRoot.querySelector('svg');
            const bad = Array.from(svg.querySelectorAll('*')).some((node) =>
                Array.from(node.attributes).some((attribute) => /NaN|Infinity/.test(attribute.value)));
            const points = Array.from(svg.querySelectorAll('[part=point]'));
            return {
                bad: bad,
                points: points.length,
                flagged: points.filter((point) => /out of control/.test(point.getAttribute('aria-label'))).length
            };
        }"""
    )
    assert info["bad"] is False, f"NaN geometry: {info}"
    assert info["points"] == 4, f"the null point should be a gap: {info}"
    assert info["flagged"] == 1, f"the point above the UCL is not flagged: {info}"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_forest_log_scale_and_labels_are_plain_text(page, base_url):
    """
        A forest plot on scale="log" puts the no-effect line at 1, has more
        than one tick label, and shows "Age < 50" as written.
    """

    data = {"series": [{"name": "S", "groups": [
        {"category": "Age < 50", "value": 0.72, "error_low": 0.18, "error_high": 0.22},
        {"category": "R&D", "value": 1.3, "error_low": 0.2, "error_high": 0.4},
    ]}]}
    frame = _mount_charts(page, base_url, _chart("forest", data, 'scale="log"'))
    texts = frame.evaluate(
        """() => Array.from(document.querySelector('mj-chart').shadowRoot
            .querySelectorAll('svg text')).map((text) => text.textContent)"""
    )
    assert "Age < 50" in texts and "R&D" in texts, f"labels are escaped: {texts}"
    assert "1" in texts, f"no tick at the no-effect value 1: {texts}"
    assert not any("&amp;" in text or "&lt;" in text for text in texts), f"escaped text: {texts}"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_tornado_and_errorbar_bars_stay_inside_the_plot(page, base_url):
    """
        A tornado row whose low output is above the baseline (an inverse
        driver) and errorbar bars from zero stay inside the drawing.
    """

    tornado = {"baseline": 1200, "series": [{"name": "S", "values": [
        {"label": "Discount rate", "low": 1480, "high": 950},
        {"label": "Price", "low": 1000, "high": 1500},
    ]}]}
    errorbar = {"series": [{"name": "S", "groups": [
        {"category": "A", "value": 4.2, "error_low": 0.6, "error_high": 0.8, "bar": True},
        {"category": "B", "value": 8.0, "error_low": 1.0, "error_high": 1.2, "bar": True},
    ]}]}
    frame = _mount_charts(page, base_url, _chart("tornado", tornado) + _chart("errorbar", errorbar))
    boxes = frame.evaluate(
        """() => Array.from(document.querySelectorAll('mj-chart')).map((chart) => {
            const svg = chart.shadowRoot.querySelector('svg');
            const box = svg.viewBox.baseVal;
            const rects = Array.from(svg.querySelectorAll('[part=bar], [part=errorbar] rect'));
            return rects.map((rect) => {
                const bounds = rect.getBBox();
                const matrix = rect.getCTM();
                return {
                    left: bounds.x + matrix.e, right: bounds.x + bounds.width + matrix.e,
                    top: bounds.y + matrix.f, bottom: bounds.y + bounds.height + matrix.f,
                    width: box.width, height: box.height
                };
            });
        })"""
    )
    assert len(boxes[0]) == 4 and len(boxes[1]) == 2, f"unexpected bars: {boxes}"
    for chart_boxes in boxes:
        for box in chart_boxes:
            assert box["left"] >= 0 and box["right"] <= box["width"] + 0.5, f"bar outside: {box}"
            assert box["top"] >= 0 and box["bottom"] <= box["height"] + 0.5, f"bar outside: {box}"

    return


# ---------------------------------------------------------------------------
# UX, text, table and advanced renderers (word cloud, session flow, table
# types, faceted, calendar heatmap, gauge, spiral, euler).
# ---------------------------------------------------------------------------

@testbase.attach.parameter(create_page, identifier="page")
def test_word_cloud_draws_every_word_of_the_example(page, base_url):
    """
        The documented 15-word example places all 15 words (the placement
        spiral reaches the corners of the box).
    """

    frame = _ready_preview(page, base_url, "word-cloud")
    count = frame.evaluate(
        "() => document.querySelector('mj-chart').shadowRoot.querySelectorAll('[part=word]').length"
    )
    assert count == 15, f"only {count} of 15 words were drawn"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_session_flow_cycle_renders_and_sizes_nodes_by_max_flow(page, base_url):
    """
        Back-navigation and self-links do not hang the layout, and a node is
        sized by max(inflow, outflow), not their sum.
    """

    data = {
        "nodes": [{"id": "home", "label": "Home"}, {"id": "cat", "label": "Catalog"},
                  {"id": "prod", "label": "Product"}],
        "links": [{"source": "home", "target": "cat", "value": 10},
                  {"source": "cat", "target": "prod", "value": 10},
                  {"source": "prod", "target": "cat", "value": 2},
                  {"source": "prod", "target": "prod", "value": 1}],
    }
    frame = _mount_charts(page, base_url, _chart("session-flow", data))
    info = frame.evaluate(
        """() => {
            const chart = document.querySelector('mj-chart');
            const rects = Array.from(chart.shadowRoot.querySelectorAll('[part=flow-node] rect'));
            return { state: chart.chartState,
                     heights: rects.map((rect) => Number(rect.getAttribute('height'))) };
        }"""
    )
    assert info["state"] == "ready", f"session-flow did not draw: {info}"
    assert len(info["heights"]) == 3, f"unexpected nodes: {info}"
    ratio = info["heights"][1] / info["heights"][0]
    assert abs(ratio - 1.2) < 0.05, f"Catalog (in 12, out 10) vs Home (10): ratio {ratio}"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_table_types_draw_a_scrolling_dom_table(page, base_url):
    """
        heatmap-table, bar-in-cell and conditional-format-table draw a real
        <table> with row headers that scrolls when the rows do not fit, and
        publish the same rows as the accessible table.
    """

    rows = [{"label": f"Row {index}", "a": index, "b": 20 - index} for index in range(14)]
    data = {"columns": [{"key": "a", "label": "A", "render": "bar"},
                        {"key": "b", "label": "B", "render": "bar"}],
            "rows": rows}
    markup = "".join(_chart(type_key, data) for type_key in
                     ["heatmap-table", "bar-in-cell", "conditional-format-table"])
    frame = _mount_charts(page, base_url, markup)
    infos = frame.evaluate(
        """() => Array.from(document.querySelectorAll('mj-chart')).map((chart) => {
            const root = chart.shadowRoot;
            const table = root.querySelector('svg foreignObject table');
            const scroller = root.querySelector('svg foreignObject [part=table-scroll]');
            const fallback = root.querySelector('[data-chart-table] table');
            return {
                rows: table !== null ? table.querySelectorAll('tbody tr').length : 0,
                rowHeaders: table !== null ? table.querySelectorAll('tbody th[scope=row]').length : 0,
                scrolls: scroller !== null && scroller.scrollHeight > scroller.clientHeight,
                fallbackRows: fallback !== null ? fallback.querySelectorAll('tbody tr').length : 0
            };
        })"""
    )
    for info in infos:
        assert info["rows"] == 14 and info["rowHeaders"] == 14, f"table rows missing: {info}"
        assert info["scrolls"] is True, f"the table does not scroll: {info}"
        assert info["fallbackRows"] == 14, f"accessible table rows: {info}"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_bar_in_cell_bars_start_at_zero(page, base_url):
    """
        In-cell bars are drawn from zero, so their lengths are proportional to
        the values (50 is half of 100).
    """

    data = {"columns": [{"key": "name", "type": "string"},
                        {"key": "v", "type": "number", "render": "bar"}],
            "rows": [{"name": "half", "v": 50}, {"name": "full", "v": 100}]}
    frame = _mount_charts(page, base_url, _chart("bar-in-cell", data))
    widths = frame.evaluate(
        """() => Array.from(document.querySelector('mj-chart').shadowRoot
            .querySelectorAll('rect[part=bar]')).map((rect) => Number(rect.getAttribute('width')))"""
    )
    assert len(widths) == 2, f"unexpected bars: {widths}"
    assert abs(widths[0] / widths[1] - 0.5) < 0.01, f"bar widths not proportional: {widths}"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_faceted_shared_scale_bars_compare_across_panels(page, base_url):
    """
        With shared scales (the default) the tallest bars of two panels are in
        the ratio of their values.
    """

    data = {"childType": "bar", "categories": ["a", "b"],
            "panels": [{"label": "Low", "series": [{"name": "S", "values": [25, 50]}]},
                       {"label": "High", "series": [{"name": "S", "values": [80, 100]}]}]}
    frame = _mount_charts(page, base_url, _chart("faceted", data))
    heights = frame.evaluate(
        """() => Array.from(document.querySelector('mj-chart').shadowRoot
            .querySelectorAll('[part=panel]')).map((panel) => Math.max(...Array.from(
                panel.querySelectorAll('rect[part=bar]')).map((rect) => Number(rect.getAttribute('height')))))"""
    )
    assert len(heights) == 2, f"unexpected panels: {heights}"
    assert abs(heights[0] / heights[1] - 0.5) < 0.02, f"panel scales differ: {heights}"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_calendar_heatmap_years_from_data_and_visible_empty_days(page, base_url):
    """
        Without `years` the calendar shows the year of the data, labels it,
        and draws days without data in a fill that differs from the page.
    """

    data = {"data": [{"date": "2023-03-01", "value": 4}, {"date": "2023-03-01", "value": 2}]}
    frame = _mount_charts(page, base_url, _chart("calendar-heatmap", data))
    info = frame.evaluate(
        """() => {
            const root = document.querySelector('mj-chart').shadowRoot;
            const label = root.querySelector('[part=year-label]');
            const empty = root.querySelector('rect[part="day empty"]');
            const day = root.querySelector('rect[part=day]');
            return {
                year: label !== null ? label.textContent : null,
                emptyFill: empty !== null ? getComputedStyle(empty).fill : null,
                page: getComputedStyle(document.body).backgroundColor,
                dayLabel: day !== null ? day.getAttribute('aria-label') : null
            };
        }"""
    )
    assert info["year"] == "2023", f"year label: {info}"
    assert info["emptyFill"] is not None and info["emptyFill"] != info["page"], f"empty days invisible: {info}"
    assert info["dayLabel"] is not None and info["dayLabel"].endswith("6"), f"values of a day add up: {info}"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_gauge_bands_follow_thresholds_and_label_clears_the_pivot(page, base_url):
    """
        Each band takes its threshold's colour, and the value label is drawn
        below the needle pivot.
    """

    data = {"gauge": {"value": 72, "thresholds": [
        {"value": 40, "label": "Fair", "color": "rgb(200, 100, 0)"},
        {"value": 70, "label": "Good", "color": "rgb(0, 120, 60)"}]}}
    frame = _mount_charts(page, base_url, _chart("gauge", data))
    info = frame.evaluate(
        """() => {
            const root = document.querySelector('mj-chart').shadowRoot;
            const pivot = root.querySelector('[part=gauge-pivot]');
            const value = root.querySelector('[part=gauge-value]');
            return {
                bands: Array.from(root.querySelectorAll('[part=gauge-band]')).map((band) => band.getAttribute('fill')),
                fill: root.querySelector('[part=gauge-fill]').getAttribute('fill'),
                pivotBottom: Number(pivot.getAttribute('cy')) + Number(pivot.getAttribute('r')),
                valueTop: value.getBBox().y
            };
        }"""
    )
    assert info["bands"] == ["rgb(200, 100, 0)", "rgb(0, 120, 60)"], f"band colours: {info}"
    assert info["fill"] == "rgb(0, 120, 60)", f"value arc colour: {info}"
    assert info["valueTop"] >= info["pivotBottom"], f"value label overlaps the pivot: {info}"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_spiral_places_points_by_weekday(page, base_url):
    """
        A weekly spiral whose first point is a Thursday draws it on the
        Thursday spoke (3/7 of a turn after Monday at the top).
    """

    data = {"cycle": "week", "series": [{"name": "S", "points": [{"t": "2025-01-09", "value": 1}]}]}
    frame = _mount_charts(page, base_url, _chart("spiral", data))
    angle = frame.evaluate(
        """() => {
            const svg = document.querySelector('mj-chart').shadowRoot.querySelector('svg');
            const box = svg.viewBox.baseVal;
            const point = svg.querySelector('[part=point]');
            const dx = Number(point.getAttribute('cx')) - box.width / 2;
            const dy = Number(point.getAttribute('cy')) - box.height / 2;
            return Math.atan2(dy, dx);
        }"""
    )
    expected = math.atan2(math.sin(3 / 7 * 2 * math.pi - math.pi / 2),
                          math.cos(3 / 7 * 2 * math.pi - math.pi / 2))
    assert abs(angle - expected) < 0.02, f"Thursday drawn at {angle}, expected {expected}"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_euler_areas_are_proportional_and_disjoint_sets_apart(page, base_url):
    """
        Euler circle areas are proportional to set size (no radius floor), and
        sets with no declared intersection do not overlap.
    """

    data = {"sets": [{"name": "A", "size": 100}, {"name": "B", "size": 25}]}
    frame = _mount_charts(page, base_url, _chart("euler", data))
    circles = frame.evaluate(
        """() => Array.from(document.querySelector('mj-chart').shadowRoot
            .querySelectorAll('[part=venn-set] circle')).map((circle) => ({
                x: Number(circle.getAttribute('cx')), y: Number(circle.getAttribute('cy')),
                r: Number(circle.getAttribute('r')) }))"""
    )
    assert len(circles) == 2, f"unexpected circles: {circles}"
    assert abs(circles[1]["r"] / circles[0]["r"] - 0.5) < 0.01, f"radii not sqrt(size): {circles}"
    distance = math.hypot(circles[0]["x"] - circles[1]["x"], circles[0]["y"] - circles[1]["y"])
    assert distance >= circles[0]["r"] + circles[1]["r"] - 0.5, f"disjoint sets overlap: {circles}"

    return


# ---------------------------------------------------------------------------
# Scientific and geographic renderers (polar family, surface, vector field,
# ternary, log axes, symbol / tile maps, routes): behaviour checks on markup
# mounted in a playground frame.
# ---------------------------------------------------------------------------

@testbase.attach.parameter(create_page, identifier="page")
def test_vector_field_arrows_point_along_u_and_v(page, base_url):
    """
        A vector (u=0, v=1) is drawn pointing up and (u=1, v=0) pointing
        right: the arrow tip lies in the direction of the field.
    """

    frame = _mount_charts(page, base_url, _chart("vector-field", {"vectors": [
        {"x": 0, "y": 0, "u": 0, "v": 1}, {"x": 1, "y": 0, "u": 1, "v": 0}
    ]}))
    arrows = frame.evaluate(
        """() => Array.from(document.querySelector('mj-chart').shadowRoot
            .querySelectorAll('[part=vector]')).map((group) => {
                const shaft = group.querySelector('line');
                const tip = group.querySelector('polygon').getAttribute('points').split(' ')[0].split(',').map(Number);
                return { x1: Number(shaft.getAttribute('x1')), y1: Number(shaft.getAttribute('y1')),
                         tipX: tip[0], tipY: tip[1] };
            })"""
    )
    assert len(arrows) == 2, f"expected 2 arrows, got {arrows}"
    up = arrows[0]
    right = arrows[1]
    assert up["tipY"] < up["y1"] - 5 and abs(up["tipX"] - up["x1"]) < 1, f"(0, 1) does not point up: {up}"
    assert right["tipX"] > right["x1"] + 5 and abs(right["tipY"] - right["y1"]) < 1, f"(1, 0) does not point right: {right}"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_surface_paints_far_faces_before_near_ones(page, base_url):
    """
        On a steep peak no face is covered at its centre by a face that is
        farther from the viewer (painter's order by grid depth).
    """

    axis = list(range(12))
    peak = [[round(10 * math.exp(-((c - 5.5) ** 2 + (r - 5.5) ** 2) / 8), 3) for c in axis] for r in axis]
    frame = _mount_charts(page, base_url, _chart("surface", {"grid": {"x": axis, "y": axis, "z": peak}}))
    violations = frame.evaluate(
        """() => {
            const root = document.querySelector('mj-chart').shadowRoot;
            const faces = Array.from(root.querySelectorAll('[part=surface-face]'));
            const depth = (face) => {
                const numbers = face.getAttribute('aria-label').match(/-?[\\d.]+/g).map(Number);
                return numbers[0] + numbers[2];
            };
            let bad = 0;
            for (const face of faces) {
                const box = face.getBoundingClientRect();
                const hit = root.elementFromPoint(box.left + box.width / 2, box.top + box.height / 2);
                if (hit !== null && hit !== face && hit.getAttribute('part') === 'surface-face' &&
                    depth(hit) < depth(face)) {
                    const matrix = face.getScreenCTM().inverse();
                    const point = new DOMPoint(box.left + box.width / 2, box.top + box.height / 2).matrixTransform(matrix);
                    if (face.isPointInFill(point) === true) {
                        bad = bad + 1;
                    }
                }
            }
            return { faces: faces.length, bad: bad };
        }"""
    )
    assert violations["faces"] == 121, f"expected 121 faces: {violations}"
    assert violations["bad"] == 0, f"far faces painted over near ones: {violations}"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_ternary_left_edge_is_labelled_with_component_a(page, base_url):
    """
        The left-edge tick next to the A vertex (bottom left) reads 100 and
        the one next to the C vertex (top) reads 0; a point whose components
        sum to zero is not drawn.
    """

    frame = _mount_charts(page, base_url, _chart("ternary", {"series": [{"name": "S", "points": [
        {"a": 70, "b": 20, "c": 10}, {"a": 0, "b": 0, "c": 0}
    ]}]}))
    info = frame.evaluate(
        """() => {
            const root = document.querySelector('mj-chart').shadowRoot;
            const left = Array.from(root.querySelectorAll('text[text-anchor=end]'))
                .filter((text) => /^\\d+$/.test(text.textContent))
                .map((text) => ({ y: Number(text.getAttribute('y')), label: text.textContent }))
                .sort((a, b) => a.y - b.y);
            return { top: left[0].label, bottom: left[left.length - 1].label,
                     points: root.querySelectorAll('[part=point]').length };
        }"""
    )
    assert info["top"] == "0" and info["bottom"] == "100", f"left edge does not read A: {info}"
    assert info["points"] == 1, f"a zero-total point was drawn: {info}"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_bubble_map_area_is_proportional_to_value(page, base_url):
    """
        bubble-map sizes its circles by default, with area proportional to
        value from zero; a zero value draws no circle.
    """

    frame = _mount_charts(page, base_url, _chart("bubble-map", {"markers": [
        {"lat": 0, "lng": 0, "value": 100, "label": "A"},
        {"lat": 5, "lng": 5, "value": 25, "label": "B"},
        {"lat": 9, "lng": 9, "value": 0, "label": "C"}
    ]}))
    radii = frame.evaluate(
        """() => Array.from(document.querySelector('mj-chart').shadowRoot
            .querySelectorAll('[part=symbol]')).map((circle) => Number(circle.getAttribute('r')))"""
    )
    assert len(radii) == 2, f"expected 2 bubbles, got {radii}"
    ratio = (radii[0] / radii[1]) ** 2
    assert abs(ratio - 4) < 0.05, f"area ratio {ratio} is not the value ratio 4: {radii}"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_tile_grid_map_draws_square_tiles_on_a_plain_grid(page, base_url):
    """
        tile-grid-map draws squares (not hexagons) whose columns line up and
        which do not overlap; hex-map hexagons are flat-topped by default.
    """

    regions = [{"id": key, "value": index * 10} for index, key in enumerate(["A", "B", "C", "D"])]
    layout = {"A": {"q": 0, "r": 0}, "B": {"q": 1, "r": 0}, "C": {"q": 0, "r": 1}, "D": {"q": 1, "r": 1}}
    frame = _mount_charts(page, base_url,
                          _chart("tile-grid-map", {"regions": regions, "layout": layout}) +
                          _chart("hex-map", {"regions": regions, "layout": layout}))
    info = frame.evaluate(
        """() => {
            const charts = Array.from(document.querySelectorAll('mj-chart'));
            const tiles = Array.from(charts[0].shadowRoot.querySelectorAll('rect[part=region]')).map((rect) => ({
                x: Number(rect.getAttribute('x')), y: Number(rect.getAttribute('y')),
                size: Number(rect.getAttribute('width')) }));
            const hex = charts[1].shadowRoot.querySelector('polygon[part=region]').getBBox();
            return { tiles: tiles, hexPolygons: charts[0].shadowRoot.querySelectorAll('polygon').length,
                     hexRatio: hex.width / hex.height };
        }"""
    )
    tiles = info["tiles"]
    assert len(tiles) == 4 and info["hexPolygons"] == 0, f"tile-grid-map did not draw 4 squares: {info}"
    assert abs(tiles[0]["x"] - tiles[2]["x"]) < 0.5, f"columns do not line up: {tiles}"
    assert tiles[1]["x"] - tiles[0]["x"] >= tiles[0]["size"], f"tiles overlap: {tiles}"
    assert abs(info["hexRatio"] - 2 / 3 ** 0.5) < 0.02, f"flat hexagon has the wrong aspect: {info}"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_route_map_crosses_the_antimeridian_the_short_way(page, base_url):
    """
        A Pacific route (LAX -> NRT) is drawn across the antimeridian, so it
        spans a modest share of the drawing instead of the whole map.
    """

    frame = _mount_charts(page, base_url, _chart("route-map", {"series": [{"name": "Pacific", "routes": [
        {"id": "LAX-NRT", "waypoints": [{"lon": -118.41, "lat": 33.94}, {"lon": 139.78, "lat": 35.55}]}
    ]}, {"name": "Atlantic", "routes": [
        {"id": "JFK-LHR", "waypoints": [{"lon": -73.78, "lat": 40.64}, {"lon": -0.46, "lat": 51.48}]}
    ]}]}))
    spans = frame.evaluate(
        """() => Array.from(document.querySelector('mj-chart').shadowRoot
            .querySelectorAll('[part=route]')).map((path) => path.getBBox().width)"""
    )
    assert len(spans) == 2, f"expected 2 routes, got {spans}"
    # 102 degrees of longitude across the Pacific against 73 across the Atlantic.
    assert spans[0] < spans[1] * 1.8, f"the Pacific route goes the long way round: {spans}"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_log_axes_break_the_line_at_non_positive_values(page, base_url):
    """
        semi-log with only scale-x="log" keeps a linear y axis; a point with
        x = 0 is a gap (two line pieces) and is reported as a warning.
    """

    frame = _mount_charts(page, base_url, _chart("log-log", {"series": [{"name": "S", "points": [{"x": 1, "y": 1}]}]}))
    info = frame.evaluate(
        """async () => {
            document.body.innerHTML = '<mj-chart type="semi-log" scale-x="log" style="height:240px;width:480px"></mj-chart>';
            const chart = document.querySelector('mj-chart');
            const warnings = [];
            chart.addEventListener('mj-chart-error', (event) => warnings.push(event.detail));
            chart.data = { series: [{ name: 'S', points: [
                { x: 1, y: 0 }, { x: 10, y: 50 }, { x: 0, y: 60 }, { x: 100, y: 80 }, { x: 1000, y: 90 }] }] };
            await new Promise((resolve) => setTimeout(resolve, 600));
            const root = chart.shadowRoot;
            const line = root.querySelector('[part=line]').getAttribute('d');
            return { pieces: (line.match(/M/g) || []).length, points: root.querySelectorAll('[part=point]').length,
                     warnings: warnings.map((detail) => detail.severity + ':' + detail.dropped) };
        }"""
    )
    assert info["points"] == 4, f"the y = 0 point must stay on a linear y axis: {info}"
    assert info["pieces"] == 2, f"the line bridges the dropped point: {info}"
    assert "warning:1" in info["warnings"], f"no warning for the dropped point: {info}"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_scientific_labels_are_plain_text(page, base_url):
    """
        Labels reach the drawing as plain text: "R&D" is announced as
        "R&D", not as an HTML entity.
    """

    frame = _mount_charts(page, base_url, _chart("wind-rose", {
        "directions": ["N", "S"], "series": [{"name": "R&D <5", "values": [3, 4]}]}))
    labels = frame.evaluate(
        """() => Array.from(document.querySelector('mj-chart').shadowRoot
            .querySelectorAll('[part=petal]')).map((petal) => petal.getAttribute('aria-label'))"""
    )
    assert labels == ["N, R&D <5: 3", "S, R&D <5: 4"], f"labels are escaped or wrong: {labels}"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_boolean_options_read_a_bare_attribute_as_true(page, base_url):
    """
        Every renderer reads boolean options through one helper: a bare
        attribute (`<mj-chart show-points>`) is on, `="false"` is off and an
        absent attribute falls back to the type default (scatter: labels off,
        bubble: labels on).
    """

    samples = {"series": [{"name": "A", "groups": [{"category": "c", "samples": [3, 4, 5, 5, 6, 7, 9]}]}]}
    points = {"series": [{"name": "S", "points": [
        {"x": 1, "y": 2, "size": 3, "label": "p1"}, {"x": 2, "y": 3, "size": 5, "label": "p2"}]}]}
    markup = (
        _chart("violin", samples, 'id="v-absent"') + _chart("violin", samples, 'id="v-bare" show-points')
        + _chart("violin", samples, 'id="v-false" show-points="false"')
        + _chart("scatter", points, 'id="s-absent"') + _chart("scatter", points, 'id="s-bare" show-labels')
        + _chart("bubble", points, 'id="b-absent"') + _chart("bubble", points, 'id="b-false" show-labels="false"')
    )
    frame = _mount_charts(page, base_url, markup)
    counts = frame.evaluate(
        """() => {
            const count = (id, part) => document.getElementById(id).shadowRoot.querySelectorAll(`[part=${part}]`).length;
            return {
                violinAbsent: count('v-absent', 'violin-point'), violinBare: count('v-bare', 'violin-point'),
                violinFalse: count('v-false', 'violin-point'),
                scatterAbsent: count('s-absent', 'point-label'), scatterBare: count('s-bare', 'point-label'),
                bubbleAbsent: count('b-absent', 'point-label'), bubbleFalse: count('b-false', 'point-label')
            };
        }"""
    )
    assert counts["violinAbsent"] == 0 and counts["violinFalse"] == 0, f"points shown without the option: {counts}"
    assert counts["violinBare"] == 7, f"a bare show-points must overlay the observations: {counts}"
    assert counts["scatterAbsent"] == 0 and counts["scatterBare"] == 2, f"scatter show-labels: {counts}"
    assert counts["bubbleAbsent"] == 2 and counts["bubbleFalse"] == 0, f"bubble show-labels default: {counts}"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_hexbin_titles_its_axes_and_attributes_win_over_the_data(page, base_url):
    """
        meta.xLabel / meta.yLabel title the hexbin axes, and the `stat` and
        `radius` attributes win over hexbin.stat / hexbin.bins in the data
        (density-style wins over density.style the same way).
    """

    points = [{"x": index % 7, "y": (index * 3) % 5, "value": index} for index in range(40)]
    data = {"meta": {"xLabel": "Engine size", "yLabel": "Fuel use"},
            "series": [{"name": "Cars", "points": points}],
            "hexbin": {"bins": 4, "stat": "sum"}}
    grid = {"density": {"style": "contour"},
            "series": [{"name": "P", "points": [{"x": index % 9, "y": (index * 7) % 11} for index in range(60)]}]}
    markup = (
        _chart("hexbin", data, 'id="hex" stat="mean" radius="10"')
        + _chart("density-2d", grid, 'id="dens" density-style="fill"')
    )
    frame = _mount_charts(page, base_url, markup)
    info = frame.evaluate(
        """() => {
            const root = document.getElementById('hex').shadowRoot;
            const texts = Array.from(root.querySelectorAll('svg text')).map((node) => node.textContent);
            const hex = root.querySelector('[part=hexbin]');
            const xs = hex.getAttribute('points').split(' ').map((pair) => Number(pair.split(',')[0]));
            const dens = document.getElementById('dens').shadowRoot;
            return {
                titles: texts.filter((text) => text === 'Engine size' || text === 'Fuel use'),
                width: Math.max(...xs) - Math.min(...xs),
                label: hex.getAttribute('aria-label'),
                contours: dens.querySelectorAll('[part=contour]').length,
                surface: dens.querySelectorAll('[part=density-surface]').length
            };
        }"""
    )
    assert sorted(info["titles"]) == ["Engine size", "Fuel use"], f"axis titles missing: {info}"
    assert abs(info["width"] - 20) < 0.5, f"radius attribute ignored (hexagon width): {info}"
    assert "mean" in info["label"], f"stat attribute ignored: {info}"
    assert info["surface"] == 1 and info["contours"] == 0, f"density-style must win over density.style: {info}"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_rug_vertical_columns_share_the_width(page, base_url):
    """
        orientation="vertical": the series columns spread across the plot and
        their names under the columns do not overlap.
    """

    data = {"series": [{"name": "Group A", "samples": [1, 2, 3, 4, 8]},
                       {"name": "Group B", "samples": [2, 5, 6, 7, 9]}]}
    frame = _mount_charts(page, base_url, _chart("rug", data, 'orientation="vertical"'))
    info = frame.evaluate(
        """() => {
            const root = document.querySelector('mj-chart').shadowRoot;
            const groups = Array.from(root.querySelectorAll('[part=rug]'));
            const centres = groups.map((group) => {
                const box = group.getBoundingClientRect();
                return box.left + box.width / 2;
            });
            const labels = Array.from(root.querySelectorAll('svg text'))
                .filter((node) => node.textContent.startsWith('Group'))
                .map((node) => { const box = node.getBoundingClientRect(); return [box.left, box.right]; });
            const width = root.querySelector('svg').getBoundingClientRect().width;
            return { centres: centres, labels: labels, width: width };
        }"""
    )
    assert len(info["centres"]) == 2, f"two columns expected: {info}"
    assert info["centres"][1] - info["centres"][0] > info["width"] * 0.3, f"columns packed together: {info}"
    assert len(info["labels"]) == 2 and info["labels"][0][1] <= info["labels"][1][0], f"labels overlap: {info}"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_inline_key_is_left_out_when_a_legend_part_is_bound(page, base_url):
    """
        radar and parallel draw their own series key only when no
        <mj-chart-legend> lists the series.
    """

    radar = {"categories": ["A", "B", "C"], "series": [{"name": "One", "values": [1, 2, 3]},
                                                     {"name": "Two", "values": [3, 2, 1]}]}
    parallel = {"dimensions": [{"name": "P"}, {"name": "Q"}],
                "series": [{"name": "One", "observations": [[1, 2]]}, {"name": "Two", "observations": [[2, 1]]}]}
    legend = "<mj-chart-legend></mj-chart-legend>"
    markup = (
        _chart("radar", radar, 'id="radar-plain"')
        + _chart("radar", radar, 'id="radar-legend"').replace("<script", legend + "<script")
        + _chart("parallel", parallel, 'id="parallel-plain"')
        + _chart("parallel", parallel, 'id="parallel-legend"').replace("<script", legend + "<script")
    )
    frame = _mount_charts(page, base_url, markup)
    page.wait_for_timeout(300)
    keys = frame.evaluate(
        """() => {
            const keys = (id) => document.getElementById(id).shadowRoot.querySelectorAll('svg [part=legend]').length;
            return { radarPlain: keys('radar-plain'), radarLegend: keys('radar-legend'),
                     parallelPlain: keys('parallel-plain'), parallelLegend: keys('parallel-legend') };
        }"""
    )
    assert keys["radarPlain"] == 1 and keys["parallelPlain"] == 1, f"inline key missing: {keys}"
    assert keys["radarLegend"] == 0 and keys["parallelLegend"] == 0, f"series listed twice: {keys}"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_bump_year_strings_get_one_slot_per_period(page, base_url):
    """
        A bump chart's x axis is categorical by default: year strings label
        their own slots instead of becoming a time axis with half-year ticks.
    """

    data = {"series": [{"name": "A", "points": [{"x": str(year), "y": rank} for year, rank in
                                               [(2020, 1), (2021, 2), (2022, 1), (2023, 3)]]},
                       {"name": "B", "points": [{"x": str(year), "y": rank} for year, rank in
                                               [(2020, 2), (2021, 1), (2022, 3), (2023, 1)]]}]}
    frame = _mount_charts(page, base_url, _chart("bump", data) + _chart("bump", data, 'x-scale="time"'))
    labels = frame.evaluate(
        """() => Array.from(document.querySelectorAll('mj-chart')).map((chart) =>
            Array.from(chart.shadowRoot.querySelectorAll('[part=axes] text')).map((node) => node.textContent))"""
    )
    assert all(year in labels[0] for year in ["2020", "2021", "2022", "2023"]), f"period labels: {labels[0]}"
    assert not any("Jul" in text for text in labels[0]), f"category axis has half-year ticks: {labels[0]}"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_roc_without_markers_keeps_focusable_clickable_points(page, base_url):
    """
        markers="false" hides the markers but every point stays a focusable,
        clickable (invisible) mark that emits mj-chart-point-click.
    """

    data = {"series": [{"name": "Model", "points": [{"x": 0, "y": 0}, {"x": 0.2, "y": 0.6},
                                                    {"x": 0.5, "y": 0.85}, {"x": 1, "y": 1}]}]}
    frame = _mount_charts(page, base_url, _chart("roc", data, 'markers="false"'))
    info = frame.evaluate(
        """() => {
            const chart = document.querySelector('mj-chart');
            const points = Array.from(chart.shadowRoot.querySelectorAll('[part=point]'));
            let detail = null;
            chart.addEventListener('mj-chart-point-click', (event) => { detail = event.detail; });
            points[1].dispatchEvent(new MouseEvent('click', { bubbles: true }));
            return {
                count: points.length,
                focusable: points.filter((point) => point.hasAttribute('tabindex')).length,
                quiet: points.filter((point) => point.hasAttribute('data-quiet-mark')).length,
                opacity: getComputedStyle(points[1]).fillOpacity,
                detail: detail
            };
        }"""
    )
    assert info["count"] == 4 and info["focusable"] == 4, f"points must stay focusable: {info}"
    assert info["quiet"] == 4 and info["opacity"] == "0", f"markers must stay invisible: {info}"
    assert info["detail"] is not None and info["detail"]["x"] == 0.2, f"no point click event: {info}"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_symbol_points_without_an_id_report_their_label(page, base_url):
    """
        mj-chart-select from a series point without `id` carries its label
        as the id (as markers do).
    """

    data = {"series": [{"name": "Wind (MW)", "points": [
        {"label": "Esbjerg", "lon": 8.45, "lat": 55.47, "value": 2100},
        {"label": "Aalborg", "lon": 9.92, "lat": 57.05, "value": 900}]}]}
    frame = _mount_charts(page, base_url, _chart("proportional-symbol-map", data))
    detail = frame.evaluate(
        """() => {
            const chart = document.querySelector('mj-chart');
            let detail = null;
            chart.addEventListener('mj-chart-select', (event) => { detail = event.detail; });
            const symbol = Array.from(chart.shadowRoot.querySelectorAll('[part=symbol]'))
                .find((node) => node.getAttribute('aria-label').startsWith('Esbjerg'));
            symbol.dispatchEvent(new MouseEvent('click', { bubbles: true }));
            return detail;
        }"""
    )
    assert detail is not None and detail["id"] == "Esbjerg" and detail["label"] == "Esbjerg", f"detail: {detail}"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_geo_heatmap_surface_emits_select_on_click_and_enter(page, base_url):
    """
        The geo-heatmap surface reports the data point nearest a click, and
        Enter reports the hottest spot, as mj-chart-select.
    """

    data = {"series": [{"name": "Incidents", "points": [
        {"lon": 2.35, "lat": 48.86, "weight": 5, "label": "Paris"},
        {"lon": 2.4, "lat": 48.9, "weight": 4},
        {"lon": 13.4, "lat": 52.52, "weight": 1, "label": "Berlin"}]}]}
    frame = _mount_charts(page, base_url, _chart("geo-heatmap", data))
    details = frame.evaluate(
        """() => {
            const chart = document.querySelector('mj-chart');
            const details = [];
            chart.addEventListener('mj-chart-select', (event) => { details.push(event.detail); });
            const surface = chart.shadowRoot.querySelector('[part=heat-surface]');
            const box = surface.getBoundingClientRect();
            /* The top right corner: Berlin is the point nearest to it. */
            surface.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: box.right - 2, clientY: box.top + 2 }));
            surface.focus();
            surface.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
            return details;
        }"""
    )
    assert len(details) == 2, f"expected a click and an Enter event: {details}"
    assert details[0]["label"] == "Berlin" and details[0]["series"] == "Incidents", f"nearest point: {details}"
    assert details[1]["lon"] < 3 and details[1]["density"] == 1, f"hottest spot (the Paris cluster): {details}"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_gauge_semicircle_end_labels_stay_inside_a_narrow_chart(page, base_url):
    """
        A 180 degree dial at 390px leaves room for its min / max labels.
    """

    data = {"gauge": {"value": 4200, "min": 0, "max": 6000, "start_angle": -90, "sweep_angle": 180}}
    markup = _chart("gauge", data).replace("width:480px", "width:390px")
    frame = _mount_charts(page, base_url, markup)
    info = frame.evaluate(
        """() => {
            const svg = document.querySelector('mj-chart').shadowRoot.querySelector('svg');
            const frameBox = svg.getBoundingClientRect();
            const texts = Array.from(svg.querySelectorAll('text')).map((node) => {
                const box = node.getBoundingClientRect();
                return { text: node.textContent, left: box.left - frameBox.left, right: box.right - frameBox.left };
            });
            return { width: frameBox.width, texts: texts };
        }"""
    )
    labels = [entry for entry in info["texts"] if entry["text"] in ("0", "6,000")]
    assert len(labels) == 2, f"min / max labels: {info}"
    for entry in labels:
        assert entry["left"] >= 0 and entry["right"] <= info["width"], f"label clipped: {entry} in {info['width']}"

    return


_CONTRAST_JS = """(selector) => {
    const probe = document.createElement('canvas');
    probe.width = 1;
    probe.height = 1;
    const paint = probe.getContext('2d', { willReadFrequently: true });
    const rgb = (css) => {
        paint.clearRect(0, 0, 1, 1);
        paint.fillStyle = '#808080';
        paint.fillStyle = css;
        paint.fillRect(0, 0, 1, 1);
        return Array.from(paint.getImageData(0, 0, 1, 1).data).slice(0, 3);
    };
    const luminance = (channels) => {
        const linear = channels.map((value) => {
            const c = value / 255;
            return c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
        });
        return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2];
    };
    const chart = document.querySelector('mj-chart');
    const cells = Array.from(chart.shadowRoot.querySelectorAll(selector));
    return cells.map((cell) => {
        const style = getComputedStyle(cell);
        const text = luminance(rgb(cell.namespaceURI.endsWith('svg') ? style.fill : style.color));
        const fill = luminance(rgb(cell.namespaceURI.endsWith('svg') ? cell.previousElementSibling.getAttribute('fill') : style.backgroundColor));
        const ratio = (Math.max(text, fill) + 0.05) / (Math.min(text, fill) + 0.05);
        return { text: cell.textContent, ratio: Math.round(ratio * 100) / 100 };
    });
}"""


@testbase.attach.parameter(create_page, identifier="page")
def test_heatmap_table_cell_text_contrasts_with_its_fill(page, base_url):
    """
        Every filled heatmap-table cell's text reaches 4.5:1 against its fill
        (black or white text picked from the resolved fill), in both themes.
    """

    data = {"columns": [{"key": "region", "label": "Region"}, {"key": "jan", "label": "Jan", "type": "number"},
                        {"key": "feb", "label": "Feb", "type": "number"}],
            "rows": [{"region": "North", "jan": 12, "feb": 55}, {"region": "East", "jan": 74, "feb": 91},
                     {"region": "West", "jan": 99, "feb": 33}]}
    frame = _mount_charts(page, base_url, _chart("heatmap-table", data))
    for theme in ["light", "dark"]:
        frame.evaluate("theme => document.documentElement.setAttribute('data-theme', theme)", theme)
        page.wait_for_timeout(100)
        ratios = frame.evaluate(_CONTRAST_JS, "td[style]")
        assert len(ratios) == 6, f"filled cells ({theme}): {ratios}"
        low = [entry for entry in ratios if entry["ratio"] < 4.5]
        assert low == [], f"cells below 4.5:1 in the {theme} theme: {low}"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_matrix_table_corner_header_has_text(page, base_url):
    """
        The matrix's accessible table names its corner header (meta.yLabel,
        else "Row"), so no column header is empty.
    """

    cells = [{"x": "Q1", "y": "North", "value": 3}, {"x": "Q2", "y": "South", "value": 5}]
    markup = _chart("matrix", {"cells": cells}, 'id="plain"') + _chart(
        "matrix", {"cells": cells, "meta": {"yLabel": "Region"}}, 'id="named"')
    frame = _mount_charts(page, base_url, markup)
    headers = frame.evaluate(
        """() => ['plain', 'named'].map((id) => Array.from(document.getElementById(id).shadowRoot
            .querySelectorAll('.a11y-table thead th')).map((th) => th.textContent.trim()))"""
    )
    assert headers[0][0] == "Row" and headers[1][0] == "Region", f"corner headers: {headers}"
    assert all(text != "" for row in headers for text in row), f"an empty column header: {headers}"

    return


# ---------------------------------------------------------------------------
# Chart parts: <mj-chart-title>, <mj-chart-legend>, <mj-chart-data-table>.
# ---------------------------------------------------------------------------

_PART_DATA = {"meta": {"title": "From meta"}, "categories": ["Q1", "Q2", "Q3"],
              "series": [{"name": "North", "values": [3, 5, 4]}, {"name": "South", "values": [2, 4, 6]}]}


@testbase.attach.parameter(create_page, identifier="page")
def test_chart_data_table_localizes_its_default_caption_and_truncation_note(page, base_url):
    """
        The data table reads its truncation note (plural form) and its
        default caption through t(): strings registered with registerStrings
        replace the English ones.
    """

    large = {"categories": [f"C{index}" for index in range(600)],
             "series": [{"name": "Count", "values": list(range(600))}]}
    markup = _chart("column", large, 'id="big"') + '<mj-chart-data-table id="big-table" chart="big"></mj-chart-data-table>'
    frame = _mount_charts(page, base_url, markup)

    texts = frame.evaluate(
        """async () => {
            const table = document.getElementById('big-table');
            const note = () => table.shadowRoot.querySelector('tfoot td').textContent;
            const english = note();
            const intl = await import('/static/javascript/core/intl.js');
            intl.registerStrings({
                'mj.chart.tableTruncated': { one: 'Nur {count} Zeile.', other: 'Nur die ersten {count} Zeilen.' },
                'mj.chart.tableCaption': 'Diagrammdaten'
            });
            await new Promise((resolve) => setTimeout(resolve, 200));
            const german = note();

            /* Without a chart context the caption falls back to the registered default. */
            const loose = document.createElement('mj-chart-data-table');
            document.body.appendChild(loose);
            loose.applyModel({ meta: {}, categories: ['A'], series: [{ name: 'S', values: [1], points: [] }],
                               allSeries: [], hiddenSeries: [], raw: {} }, null);
            const caption = loose.shadowRoot.querySelector('caption').textContent;
            const rows = table.shadowRoot.querySelectorAll('tbody tr').length;
            intl.registerStrings({
                'mj.chart.tableTruncated': { one: 'Only the first {count} row is shown.',
                                             other: 'Only the first {count} rows are shown.' },
                'mj.chart.tableCaption': 'Chart data'
            });
            return { english, german, caption, rows };
        }"""
    )
    assert texts["rows"] == 500, f"rows shown: {texts}"
    assert texts["english"] == "Only the first 500 rows are shown.", f"English note: {texts}"
    assert texts["german"] == "Nur die ersten 500 Zeilen.", f"registered note not used: {texts}"
    assert texts["caption"] == "Diagrammdaten", f"registered default caption not used: {texts}"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_chart_data_table_shows_a_note_when_every_series_is_hidden(page, base_url):
    """
        With every series hidden the data table shows the "All series are
        hidden." note instead of listing the categories as Index / Value
        rows; showing a series brings the table back with only its column.
    """

    markup = _chart("column", _PART_DATA, 'id="parts"') + (
        '<mj-chart-data-table id="parts-table" chart="parts"></mj-chart-data-table>'
    )
    frame = _mount_charts(page, base_url, markup)

    state = frame.evaluate(
        """async () => {
            const chart = document.getElementById('parts');
            const root = document.getElementById('parts-table').shadowRoot;
            const read = () => ({
                note: root.querySelector('[part=empty]') !== null ? root.querySelector('[part=empty]').textContent : null,
                tables: root.querySelectorAll('table').length,
                headers: Array.from(root.querySelectorAll('thead th')).map((th) => th.textContent)
            });
            chart.hideSeries('North');
            chart.hideSeries('South');
            await new Promise((resolve) => setTimeout(resolve, 100));
            const hidden = read();
            chart.showSeries('South');
            await new Promise((resolve) => setTimeout(resolve, 100));
            return { hidden, shown: read() };
        }"""
    )
    assert state["hidden"]["note"] == "All series are hidden.", f"no note: {state}"
    assert state["hidden"]["tables"] == 0 and state["hidden"]["headers"] == [], f"table still listed: {state}"
    assert state["shown"]["note"] is None, f"note kept: {state}"
    assert state["shown"]["headers"] == ["Category", "South"], f"table not restored: {state}"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_chart_hidden_table_is_empty_when_every_series_is_hidden(page, base_url):
    """
        The chart's own visually hidden data table describes only visible
        series: with every series hidden it has no rows (it does not fall back
        to listing the categories), and showing the series restores it.
    """

    frame = _mount_charts(page, base_url, _chart("column", _PART_DATA, 'id="own"'))

    state = frame.evaluate(
        """async () => {
            const chart = document.getElementById('own');
            const rows = () => chart.shadowRoot.querySelectorAll('[data-chart-table] tbody tr').length;
            const before = rows();
            chart.hideSeries('North');
            chart.hideSeries('South');
            await new Promise((resolve) => setTimeout(resolve, 100));
            const hidden = rows();
            chart.showAllSeries();
            await new Promise((resolve) => setTimeout(resolve, 100));
            return { before, hidden, restored: rows() };
        }"""
    )
    assert state["before"] > 0, f"no table rows to begin with: {state}"
    assert state["hidden"] == 0, f"hidden table still lists rows: {state}"
    assert state["restored"] == state["before"], f"table not restored: {state}"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_chart_title_content_without_text_is_shown_and_names_the_chart(page, base_url):
    """
        Title content without text counts as content: an <img alt> is shown
        and its alt names the chart; a decorative (aria-hidden) icon is shown
        and the chart's name falls back to meta.title.
    """

    image = '<mj-chart-title id="image-title"><img alt="Revenue logo" src="data:image/gif;base64,R0lGODlhAQABAAAAACw="></mj-chart-title>'
    icon = ('<mj-chart-title id="icon-title"><svg aria-hidden="true" width="16" height="16">'
            '<circle cx="8" cy="8" r="6"></circle></svg></mj-chart-title>')
    markup = (
        _chart("column", _PART_DATA, 'id="with-image"').replace("<script", image + "<script")
        + _chart("column", _PART_DATA, 'id="with-icon"').replace("<script", icon + "<script")
    )
    frame = _mount_charts(page, base_url, markup)

    info = frame.evaluate(
        """() => ['image', 'icon'].map((name) => {
            const title = document.getElementById(name + '-title');
            const chart = document.getElementById('with-' + name);
            return {
                slotHidden: title.shadowRoot.querySelector('slot').hidden,
                text: title.shadowRoot.querySelector('[data-title-text]').textContent,
                label: title.chartLabel,
                chart: chart.getAttribute('aria-label')
            };
        })"""
    )
    assert info[0]["slotHidden"] is False and info[0]["label"] == "Revenue logo", f"image title: {info[0]}"
    assert info[0]["chart"] == "Revenue logo", f"chart not named by the alt: {info[0]}"
    assert info[1]["slotHidden"] is False and info[1]["text"] == "", f"icon content not shown: {info[1]}"
    assert info[1]["label"] == "" and info[1]["chart"] == "From meta", f"icon title name: {info[1]}"

    alt = frame.evaluate(
        """async () => {
            document.querySelector('#image-title img').setAttribute('alt', 'New logo');
            await new Promise((resolve) => setTimeout(resolve, 100));
            return document.getElementById('with-image').getAttribute('aria-label');
        }"""
    )
    assert alt == "New logo", f"alt change not followed: {alt}"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_chart_data_table_caption_follows_the_title_at_once(page, base_url):
    """
        A data table whose caption is the chart's name follows a title edit
        immediately, without waiting for the chart's next render.
    """

    parts = '<mj-chart-title id="live-title">First title</mj-chart-title><mj-chart-data-table id="live-table"></mj-chart-data-table>'
    plain = dict(_PART_DATA)
    plain.pop("meta")
    markup = _chart("column", plain, 'id="named"').replace("<script", parts + "<script")
    frame = _mount_charts(page, base_url, markup)

    captions = frame.evaluate(
        """async () => {
            const chart = document.getElementById('named');
            const caption = () => document.getElementById('live-table').shadowRoot.querySelector('caption').textContent;
            /* Let any resize re-render settle before counting renders. */
            await new Promise((resolve) => setTimeout(resolve, 300));
            let renders = 0;
            chart.addEventListener('mj-chart-render', () => { renders = renders + 1 });
            const before = caption();
            document.getElementById('live-title').textContent = 'Second title';
            await Promise.resolve();
            await new Promise((resolve) => setTimeout(resolve, 0));
            return { before, after: caption(), chart: chart.getAttribute('aria-label'), renders };
        }"""
    )
    assert captions["before"] == "First title", f"initial caption: {captions}"
    assert captions["chart"] == "Second title", f"chart name: {captions}"
    assert captions["after"] == "Second title" and captions["renders"] == 0, f"caption stale: {captions}"

    return


@testbase.attach.parameter(create_page, identifier="page")
def test_chart_legend_disabled_blocks_keyboard_toggles(page, base_url):
    """
        A disabled legend disables its toggle buttons: Tab skips them and no
        series can be toggled; enabled again, Enter and Space toggle.
    """

    markup = (
        _chart("column", _PART_DATA, 'id="kbd"')
        + '<button id="before">before</button>'
        + '<mj-chart-legend id="kbd-legend" chart="kbd" disabled></mj-chart-legend>'
        + '<button id="after">after</button>'
    )
    frame = _mount_charts(page, base_url, markup)
    active = """() => {
        const legend = document.getElementById('kbd-legend');
        const inner = legend.shadowRoot.activeElement;
        return document.activeElement.id + (inner !== null ? ':' + inner.textContent : '');
    }"""

    disabled = frame.evaluate(
        "() => Array.from(document.getElementById('kbd-legend').shadowRoot.querySelectorAll('button.item'))"
        ".map((button) => button.disabled)"
    )
    assert disabled == [True, True], f"buttons not disabled: {disabled}"

    frame.focus("#before")
    page.keyboard.press("Tab")
    assert frame.evaluate(active) == "after", f"Tab reached the disabled legend: {frame.evaluate(active)}"
    hidden = frame.evaluate("() => document.getElementById('kbd').hiddenSeries")
    assert hidden == [], f"series toggled while disabled: {hidden}"

    frame.evaluate("() => document.getElementById('kbd-legend').removeAttribute('disabled')")
    frame.focus("#before")
    page.keyboard.press("Tab")
    assert frame.evaluate(active) == "kbd-legend:North", f"Tab missed the legend: {frame.evaluate(active)}"
    page.keyboard.press("Enter")
    page.wait_for_timeout(100)
    assert frame.evaluate("() => document.getElementById('kbd').hiddenSeries") == ["North"]
    page.keyboard.press("Space")
    page.wait_for_timeout(100)
    assert frame.evaluate("() => document.getElementById('kbd').hiddenSeries") == []

    return


define_page_tests(globals(), "test_chart_type_page_loads",
                  _check_chart_type_page_loads, _CHART_CASES)
define_page_tests(globals(), "test_chart_type_renders_svg",
                  _check_chart_type_renders_svg, _SAMPLE_CASES)
define_page_tests(globals(), "test_chart_type_is_accessible",
                  _check_chart_type_is_accessible, _SAMPLE_CASES)


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
