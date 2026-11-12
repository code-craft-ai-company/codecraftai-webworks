"""
    01_comparison_trend.py

    ChartTypeDoc catalog entries for the Comparison and Trend chart families.
    Each entry documents one <mj-chart type="..."> variant: the JSON its
    renderer reads (data_shape), the option attributes the renderer reads
    through ctx.attrs (options) and a gallery of runnable examples, the first
    of which is the canonical usage.

    Verified against the renderers in charts/core/renderers/ (bar.js,
    lollipop.js, dotplot.js, bullet.js, slope.js, radar.js, parallel.js,
    line.js, area.js, step.js, sparkline.js, horizon.js, streamgraph.js,
    bump.js).
"""

import html
import json

from testcomponents.catalog.componentdoc import AttributeDoc
from testcomponents.charttypes.charttypedoc import ChartTypeDoc
from testcomponents.charttypes.examplemarkup import boolean_option
from testcomponents.charttypes.examplemarkup import gallery_example
from testcomponents.charttypes.examplemarkup import json_text
from testcomponents.charttypes.examplemarkup import orientation_option


_LEGEND = '<mj-chart-legend></mj-chart-legend>'



# ---------------------------------------------------------------------------
# Example builders
# ---------------------------------------------------------------------------

def _chart(type_key, data, label, attrs="", height=280, legend=False, chart_id="demo-chart", width=None):
    """
        Markup of one <mj-chart> with inline JSON data.

        :param type_key: The chart type.
        :param data: The chart data (JSON-serialisable).
        :param label: The accessible name (plain text).
        :param attrs: Further option attributes, written as markup.
        :param height: The block size in px.
        :param legend: True to nest an <mj-chart-legend>.
        :param chart_id: The id of the chart element.
        :param width: An optional inline size in px.

        :returns: The HTML.
    """

    style = "height:{}px".format(height)
    if width is not None:
        style = style + ";width:{}px".format(width)
    attr_text = "" if attrs == "" else " " + attrs
    lines = [
        '<mj-chart id="{}" type="{}"{} label="{}" style="{}">'.format(
            chart_id, type_key, attr_text, html.escape(label, quote=True), style)
    ]
    if legend is True:
        lines.append("  " + _LEGEND)
    lines.append('  <script type="application/json">')
    lines.append("  " + json_text(data, 2))
    lines.append("  </script>")
    lines.append("</mj-chart>")
    markup = "\n".join(lines)
    return markup


def _events_script(events, part, chart_id="demo-chart"):
    """
        An example script that listens for the renderer's events, then clicks
        the first mark and presses Enter on the last one so the Events panel
        shows both activations.

        :param events: The event names to listen for.
        :param part: The `part` name of the focusable marks to activate.
        :param chart_id: The id of the chart element.

        :returns: The JavaScript source.
    """

    script = (
        'const chart = document.getElementById("{chart_id}")\n'
        'for (const name of {names}) {{\n'
        '  chart.addEventListener(name, (event) => mjSandbox.log("listener: " + name, event.detail))\n'
        '}}\n'
        '\n'
        '// Draw now so the marks exist, then activate two of them.\n'
        'await chart.redraw()\n'
        'const marks = chart.shadowRoot.querySelectorAll(\'[part~="{part}"][tabindex]\')\n'
        'marks[0].dispatchEvent(new MouseEvent("click", {{ bubbles: true }}))\n'
        'const last = marks[marks.length - 1]\n'
        'last.focus()\n'
        'last.dispatchEvent(new KeyboardEvent("keydown", {{ key: "Enter", bubbles: true }}))\n'
    ).format(chart_id=chart_id, names=json.dumps(list(events)), part=part)
    return script


# ---------------------------------------------------------------------------
# Shared option docs
# ---------------------------------------------------------------------------

def _sort_option():
    option = AttributeDoc(
        name="sort",
        description="Order the categories by their total across the visible series (`none` keeps the data order).",
        kind="enum", values=["none", "asc", "desc"], default="none")
    return option


def _x_scale_option(default="auto"):
    """
        The x-scale option; bump charts default to `category` (one slot per
        period).
    """

    option = AttributeDoc(
        name="x-scale",
        description=("X scale: `auto` picks time for ISO dates / epoch ms, linear for other numbers and "
                     "category for anything else."),
        kind="enum", values=["auto", "time", "linear", "category"], default=default)
    return option


def _curve_option(default="linear"):
    option = AttributeDoc(
        name="curve",
        description=("Path interpolation: `monotone` is smooth without overshooting the data, `step` holds "
                     "each value until the next x; any other value draws straight segments."),
        kind="enum", values=["linear", "monotone", "step"], default=default)
    return option


_CATEGORY_SERIES_SHAPE = (
    '<pre><code>{\n'
    '  categories: string[],\n'
    '  series: [{ name: string, values: (number | null)[], color?: string }]\n'
    '}</code></pre>'
    '<ul>'
    '<li><code>categories</code> (or <code>labels</code>): one band per entry, positioned by index, so '
    'repeated labels keep their own marks.</li>'
    '<li><code>series[].values</code>: index-aligned with the categories; <code>null</code> or non-numeric '
    'text draws nothing, numeric strings such as <code>"10"</code> are read as numbers.</li>'
    '<li><code>series[].color</code>: optional CSS colour, else the palette slot of the series.</li>'
    '<li><code>meta.orientation</code>: optional default orientation.</li>'
    '</ul>'
)

_TREND_SHAPE = (
    '<pre><code>{\n'
    '  categories?: string[],\n'
    '  series: [{\n'
    '    name: string,\n'
    '    values?: (number | null)[],               // aligned with categories\n'
    '    points?: [{ x: string | number, y: number | null }],\n'
    '    color?: string\n'
    '  }]\n'
    '}</code></pre>'
    '<ul>'
    '<li><code>series[].points</code>: <code>x</code> as ISO date (<code>"2025"</code>, '
    '<code>"2025-01"</code>, <code>"2025-01-15"</code>, date-time) or epoch ms gives a time scale, other '
    'numbers a linear scale, anything else categories. Points are drawn in x order.</li>'
    '<li><code>series[].values</code>: the shorthand, index-aligned with <code>categories</code>.</li>'
    '<li>A <code>null</code> y is a gap, never a zero.</li>'
    '</ul>'
)


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

_REGIONS = {
    "categories": ["North", "South", "East", "West", "Central"],
    "series": [
        {"name": "2023", "values": [142, 98, 175, 110, 63]},
        {"name": "2024", "values": [158, 115, 190, 128, 87]},
    ],
}

_CASH_FLOW = {
    "categories": ["North", "South", "East", "West", "Central"],
    "series": [
        {"name": "Inflow", "values": [210, 165, 240, 180, 120]},
        {"name": "Outflow", "values": [-150, -170, -185, -120, -95]},
    ],
}

_TICKET_CHANNELS = {
    "categories": ["EMEA", "Americas", "APAC"],
    "series": [
        {"name": "Email", "values": [420, 610, 280]},
        {"name": "Chat", "values": [380, 520, 410]},
        {"name": "Phone", "values": [190, 240, 95]},
    ],
}

_DEFECTS = {
    "categories": ["Checkout and payments", "Search", "Account settings", "Notifications",
                   "Reporting dashboard", "Mobile onboarding flow"],
    "series": [{"name": "Open defects", "values": [34, 21, None, 9, 27, 15]}],
}

_QUARTERS = {
    "categories": ["Q1", "Q2", "Q3", "Q4"],
    "series": [
        {"name": "Product A", "values": [320, 410, 375, 490]},
        {"name": "Product B", "values": [210, 275, 340, 420]},
        {"name": "Product C", "values": [140, 195, 215, 260]},
    ],
}

_MONTHS_24 = [
    "Jan 2024", "Feb 2024", "Mar 2024", "Apr 2024", "May 2024", "Jun 2024",
    "Jul 2024", "Aug 2024", "Sep 2024", "Oct 2024", "Nov 2024", "Dec 2024",
    "Jan 2025", "Feb 2025", "Mar 2025", "Apr 2025", "May 2025", "Jun 2025",
    "Jul 2025", "Aug 2025", "Sep 2025", "Oct 2025", "Nov 2025", "Dec 2025",
]

_SIGNUPS = {
    "categories": _MONTHS_24,
    "series": [{"name": "Sign-ups", "values": [
        1180, 1240, 1395, 1410, 1525, 1490, 1610, 1705, 1660, 1820, 1915, 2140,
        2080, 2150, 2290, 2340, 2410, 2385, 2520, 2610, 2575, 2730, 2860, 3050]}],
}

_PROFIT = {
    "categories": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
    "series": [{"name": "Operating profit ($k)", "values": [48, -12, 35, -27, 61, None]}],
}

_SCORES = {
    "categories": ["Accessibility", "Performance", "SEO", "Best Practices", "Security"],
    "series": [{"name": "Score", "values": [92, 78, 88, 95, 84]}],
}

_LOAD_TIMES = {
    "categories": ["Chrome", "Firefox", "Safari", "Edge"],
    "series": [
        {"name": "Desktop", "values": [1.8, 2.1, 1.9, 1.7]},
        {"name": "Mobile", "values": [2.9, 3.4, 2.6, 3.1]},
    ],
}

_ANOMALY = {
    "categories": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug"],
    "series": [{"name": "Anomaly (°C)", "values": [0.42, -0.18, 0.65, None, -0.31, 0.12, 0.88, 0.57]}],
}

_ENGAGEMENT = {
    "categories": ["Marketing", "Engineering", "Sales", "Support", "Operations"],
    "series": [
        {"name": "2022", "values": [62, 91, 74, 55, 68]},
        {"name": "2024", "values": [71, 96, 80, 63, 75]},
    ],
}

_SATISFACTION = {
    "categories": ["Onboarding", "Billing", "Mobile app", "Support", "Documentation", "Integrations"],
    "series": [
        {"name": "Small business", "values": [7.8, 6.1, 8.2, 7.4, 6.6, 5.9]},
        {"name": "Mid-market", "values": [7.1, 6.8, 7.5, 8.0, 7.2, 6.8]},
        {"name": "Enterprise", "values": [6.4, 7.3, 6.9, 8.6, 7.9, 7.7]},
    ],
}

_RELEASE_GAP = {
    "meta": {"showConnectors": True},
    "categories": ["Build", "Unit tests", "Integration", "Deploy"],
    "series": [
        {"name": "Before cache", "values": [14.2, 9.8, 22.5, 6.1]},
        {"name": "After cache", "values": [5.4, 8.9, 17.2, 5.8]},
    ],
}

_KPIS = {
    "series": [
        {"name": "Revenue ($k)", "value": 275, "target": 300, "ranges": [200, 250, 350],
         "rangeLabels": ["Poor", "Satisfactory", "Good"]},
        {"name": "Margin (%)", "value": 42, "target": 50, "ranges": [30, 45, 60],
         "rangeLabels": ["Poor", "Satisfactory", "Good"]},
        {"name": "NPS", "value": 38, "target": 45, "ranges": [20, 35, 55],
         "rangeLabels": ["Poor", "Satisfactory", "Good"]},
    ],
}

_QUOTAS = {
    "series": [
        {"name": "North", "value": 412, "target": 450, "ranges": [300, 400, 500],
         "rangeLabels": ["Behind", "On track", "Ahead"]},
        {"name": "South", "value": 468, "target": 420, "ranges": [300, 400, 500],
         "rangeLabels": ["Behind", "On track", "Ahead"]},
        {"name": "East", "value": 289, "target": 400, "ranges": [300, 400, 500],
         "rangeLabels": ["Behind", "On track", "Ahead"]},
        {"name": "West", "value": 395, "target": 380, "ranges": [300, 400, 500],
         "rangeLabels": ["Behind", "On track", "Ahead"]},
    ],
}

_STORAGE = {
    "series": [
        {"name": "eu-1", "value": 62, "target": 80, "ranges": [50, 80, 100]},
        {"name": "us-1", "value": 87, "target": 80, "ranges": [50, 80, 100]},
        {"name": "ap-1", "value": 41, "target": 80, "ranges": [50, 80, 100]},
        {"name": "sa-1", "value": 73, "target": 80, "ranges": [50, 80, 100]},
    ],
}

_BROADBAND = {
    "categories": ["2020", "2024"],
    "series": [
        {"name": "Europe", "values": [42, 58]},
        {"name": "Asia", "values": [55, 74]},
        {"name": "North America", "values": [38, 46]},
        {"name": "Africa", "values": [22, 35]},
        {"name": "Oceania", "values": [48, 52]},
    ],
}

_CHURN = {
    "categories": ["Before redesign", "After redesign"],
    "series": [
        {"name": "Starter", "values": [8.4, 6.1]},
        {"name": "Team", "values": [5.2, 5.0]},
        {"name": "Business", "values": [4.9, 5.3]},
        {"name": "Enterprise", "values": [2.1, 1.8]},
        {"name": "Education", "values": [5.1, 3.2]},
        {"name": "Non-profit", "values": [6.9, 6.5]},
    ],
}

_THREE_PERIODS = {
    "categories": ["2020", "2022", "2024"],
    "series": [
        {"name": "Europe", "values": [42, 50, 58]},
        {"name": "Asia", "values": [55, 66, 74]},
    ],
}

_PLATFORMS = {
    "categories": ["Speed", "Reliability", "Scalability", "Security", "Usability", "Cost"],
    "series": [
        {"name": "Platform A", "values": [80, 92, 75, 88, 70, 60]},
        {"name": "Platform B", "values": [65, 78, 90, 72, 85, 74]},
    ],
}

_PLAYERS = {
    "categories": ["Pace", "Shooting", "Passing", "Dribbling", "Defending", "Physical"],
    "series": [
        {"name": "Winger", "values": [92, 78, 74, 88, 35, 62]},
        {"name": "Midfielder", "values": [71, 69, 89, 82, 72, 75]},
        {"name": "Defender", "values": [68, 45, 64, 60, 90, 86]},
    ],
}

_LAPTOPS = {
    "categories": ["Rating (1-5)", "Battery (h)", "Weight (kg)", "Price ($)", "Screen (in)"],
    "dimensions": [
        {"domainMin": 1, "domainMax": 5},
        {"domainMin": 0, "domainMax": 24},
        {"domainMin": 0, "domainMax": 3},
        {"domainMin": 0, "domainMax": 3000},
        {"domainMin": 11, "domainMax": 17},
    ],
    "series": [
        {"name": "Ultrabook", "values": [4.6, 18, 1.1, 1900, 13.3]},
        {"name": "Workstation", "values": [4.2, 7, 2.4, 2800, 16]},
    ],
}

_SURVEY_GAPS = {
    "categories": ["Speed", "Reliability", "Scalability", "Security", "Usability", "Cost"],
    "series": [
        {"name": "Vendor X", "values": [74, 81, None, 90, 66, 58]},
        {"name": "Vendor Y", "values": [62, 70, 84, 77, None, 80]},
    ],
}

_ATHLETES = {
    "dimensions": [
        {"name": "Height", "domain": [150, 200], "unit": "cm"},
        {"name": "Weight", "domain": [50, 100], "unit": "kg"},
        {"name": "Age", "domain": [18, 55], "unit": "yr"},
        {"name": "Score", "domain": [50, 100], "unit": "pts"},
    ],
    "series": [
        {"name": "Group A", "observations": [
            [172, 68, 34, 82], [165, 55, 29, 91], [180, 90, 45, 74], [158, 60, 52, 88],
            [175, 75, 38, 65], [168, 72, 41, 79]]},
        {"name": "Group B", "observations": [
            [160, 58, 28, 95], [170, 80, 35, 70], [185, 95, 50, 60], [162, 65, 44, 85],
            [177, 85, 40, 72], [155, 52, 30, 90]]},
    ],
}

_CARS = {
    "dimensions": [
        {"name": "Power", "unit": "kW"},
        {"name": "Weight", "unit": "kg"},
        {"name": "0-100", "unit": "s"},
        {"name": "Range", "unit": "km"},
    ],
    "series": [
        {"name": "Electric", "observations": [
            [150, 1610, 7.3, 420], [210, 1840, 5.9, 510], [320, 2100, 4.1, 560],
            [100, 1480, 9.2, 310], [250, 2050, None, 480]]},
        {"name": "Combustion", "observations": [
            [96, 1250, 9.8, 780], [140, 1420, 7.9, 690], [185, 1560, 6.4, None],
            [260, 1690, 4.8, 610], [75, 1130, 11.5, 820]]},
    ],
}

_REVENUE_POINTS = {
    "series": [{"name": "Revenue", "points": [
        {"x": "2025-01", "y": 410}, {"x": "2025-02", "y": 385}, {"x": "2025-03", "y": 442},
        {"x": "2025-04", "y": 468}, {"x": "2025-05", "y": 510}, {"x": "2025-06", "y": 488},
        {"x": "2025-07", "y": 530}, {"x": "2025-08", "y": 572}]}],
}

_STOPPING = {
    "series": [{"name": "Stopping distance (m)", "points": [
        {"x": 20, "y": 6}, {"x": 30, "y": 14}, {"x": 40, "y": 24}, {"x": 50, "y": 38},
        {"x": 60, "y": 55}, {"x": 80, "y": 96}, {"x": 100, "y": 150}, {"x": 120, "y": 216}]}],
}

_SENSOR = {
    "categories": ["00:00", "02:00", "04:00", "06:00", "08:00", "10:00", "12:00", "14:00",
                   "16:00", "18:00", "20:00", "22:00"],
    "series": [{"name": "Humidity (%)", "values": [71, 73, 75, None, None, 62, 55, 51, 54, 60, None, 69]}],
}

_DEVICES = {
    "categories": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug"],
    "series": [
        {"name": "Desktop", "values": [520, 490, 545, 580, 610, 598, 640, 675]},
        {"name": "Mobile", "values": [310, 340, 385, 420, 445, 470, 510, 548]},
        {"name": "Tablet", "values": [120, 115, 130, 140, 135, 142, 155, 160]},
    ],
}

_LATENCY = {
    "series": [
        {"name": "p50", "points": [
            {"x": "2025-03-03", "y": 112}, {"x": "2025-03-04", "y": 108}, {"x": "2025-03-06", "y": 119},
            {"x": "2025-03-10", "y": 104}, {"x": "2025-03-11", "y": 101}, {"x": "2025-03-17", "y": 98}]},
        {"name": "p95", "points": [
            {"x": "2025-03-03", "y": 340}, {"x": "2025-03-04", "y": 362}, {"x": "2025-03-06", "y": 415},
            {"x": "2025-03-10", "y": 298}, {"x": "2025-03-11", "y": 286}, {"x": "2025-03-17", "y": 270}]},
    ],
}

_PRICES = {
    "categories": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    "series": [
        {"name": "Store A", "values": [12.4, 12.9, None, 13.4, 13.1, 14.0, 14.6]},
        {"name": "Store B", "values": [11.8, 12.1, 12.6, None, None, 13.2, 13.5]},
    ],
}

_SESSIONS = {
    "categories": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug"],
    "series": [{"name": "Sessions", "values": [12400, 13100, 11800, 14200, 15600, 14900, 16300, 17800]}],
}

_TRADE = {
    "categories": ["2018", "2019", "2020", "2021", "2022", "2023", "2024"],
    "series": [{"name": "Trade balance ($bn)", "values": [-12, -18, -31, -24, -9, 6, 14]}],
}

_TRAFFIC = {
    "categories": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    "series": [
        {"name": "Organic", "values": [3200, 3450, 3380, 3610, 3150, 2100, 1980]},
        {"name": "Paid", "values": [1400, 1550, 1620, 1580, 1720, 2350, 2480]},
    ],
}

_OUTAGE = {
    "categories": ["W1", "W2", "W3", "W4", "W5", "W6", "W7", "W8"],
    "series": [{"name": "Requests (k)", "values": [820, 860, 905, None, 790, 845, 880, 930]}],
}

_WORKLOADS = {
    "categories": ["2018", "2019", "2020", "2021", "2022", "2023", "2024"],
    "series": [
        {"name": "Cloud", "values": [120, 185, 240, 310, 380, 450, 530]},
        {"name": "On-Prem", "values": [480, 420, 350, 290, 230, 180, 140]},
        {"name": "Hybrid", "values": [80, 120, 170, 220, 260, 300, 330]},
    ],
}

_ENERGY = {
    "series": [
        {"name": "Solar", "points": [
            {"x": "2025-06-01T06:00", "y": 0.4}, {"x": "2025-06-01T09:00", "y": 3.1},
            {"x": "2025-06-01T12:00", "y": 5.6}, {"x": "2025-06-01T15:00", "y": 4.2},
            {"x": "2025-06-01T18:00", "y": 1.0}, {"x": "2025-06-01T21:00", "y": 0}]},
        {"name": "Grid", "points": [
            {"x": "2025-06-01T06:00", "y": 1.6}, {"x": "2025-06-01T09:00", "y": 0.8},
            {"x": "2025-06-01T12:00", "y": 0.3}, {"x": "2025-06-01T15:00", "y": 0.6},
            {"x": "2025-06-01T18:00", "y": 2.2}, {"x": "2025-06-01T21:00", "y": 2.9}]},
        {"name": "Battery", "points": [
            {"x": "2025-06-01T06:00", "y": 0.2}, {"x": "2025-06-01T09:00", "y": 0},
            {"x": "2025-06-01T12:00", "y": 0}, {"x": "2025-06-01T15:00", "y": 0.4},
            {"x": "2025-06-01T18:00", "y": 1.1}, {"x": "2025-06-01T21:00", "y": 1.4}]},
    ],
}

_BACKLOG = {
    "categories": ["Sprint 1", "Sprint 2", "Sprint 3", "Sprint 4", "Sprint 5", "Sprint 6"],
    "series": [
        {"name": "Bugs", "values": [34, 28, None, 22, 19, 15]},
        {"name": "Features", "values": [52, 58, 61, 55, 49, 44]},
        {"name": "Chores", "values": [12, 15, 14, None, 18, 16]},
    ],
}

_BROWSERS = {
    "categories": ["2019", "2020", "2021", "2022", "2023", "2024"],
    "series": [
        {"name": "Chrome", "values": [64, 66, 65, 66, 65, 66]},
        {"name": "Safari", "values": [19, 17, 19, 20, 19, 20]},
        {"name": "Firefox", "values": [9, 8, 8, 7, 6, 5]},
        {"name": "Other", "values": [8, 9, 8, 7, 10, 9]},
    ],
}

_FLEET = {
    "series": [
        {"name": "Petrol", "points": [
            {"x": "2021-01", "y": 640}, {"x": "2021-07", "y": 610}, {"x": "2022-01", "y": 575},
            {"x": "2022-07", "y": 520}, {"x": "2023-01", "y": 470}, {"x": "2023-07", "y": 430}]},
        {"name": "Hybrid", "points": [
            {"x": "2021-01", "y": 210}, {"x": "2021-07", "y": 240}, {"x": "2022-01", "y": 265},
            {"x": "2022-07", "y": 290}, {"x": "2023-01", "y": 300}, {"x": "2023-07", "y": 310}]},
        {"name": "Electric", "points": [
            {"x": "2021-01", "y": 50}, {"x": "2021-07", "y": 85}, {"x": "2022-01", "y": 130},
            {"x": "2022-07", "y": 185}, {"x": "2023-01", "y": 240}, {"x": "2023-07", "y": 300}]},
    ],
}

_FED_RATE = {
    "series": [{"name": "Fed funds rate", "points": [
        {"x": "2022-03-17", "y": 0.5}, {"x": "2022-05-05", "y": 1.0}, {"x": "2022-06-16", "y": 1.75},
        {"x": "2022-07-28", "y": 2.5}, {"x": "2022-09-22", "y": 3.25}, {"x": "2022-11-03", "y": 4.0},
        {"x": "2022-12-15", "y": 4.5}, {"x": "2023-02-02", "y": 4.75}, {"x": "2023-03-23", "y": 5.0},
        {"x": "2023-05-04", "y": 5.25}, {"x": "2023-07-27", "y": 5.5}, {"x": "2024-09-19", "y": 5.0},
        {"x": "2024-11-08", "y": 4.75}, {"x": "2024-12-19", "y": 4.5}]}],
}

_STOCK = {
    "categories": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
    "series": [{"name": "Units on hand", "values": [120, 120, 85, 85, 140, 60]}],
}

_PRICING_TIERS = {
    "categories": ["v1.0", "v1.1", "v1.2", "v2.0", "v2.1"],
    "series": [
        {"name": "Basic", "values": [9, 9, 12, 12, 15]},
        {"name": "Pro", "values": [29, 29, 29, 39, 39]},
    ],
}

_THERMOSTAT = {
    "categories": ["06:00", "08:00", "10:00", "12:00", "14:00", "16:00", "18:00", "20:00"],
    "series": [{"name": "Set point (°C)", "values": [19, 21, 21, None, 20, 20, 22, 18]}],
}

_WEEKLY_REVENUE = {
    "series": [{"name": "Revenue", "values": [88, 92, 85, 97, 104, 99, 111, 108, 120, 115, 128, 135]}],
}

_NET_FLOW = {
    "series": [{"name": "Net flow", "values": [12, 8, -5, -14, 3, 18, 22, -9, 6, 15, -3, 11]}],
}

_SERVERS = {
    "categories": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "series": [
        {"name": "CPU", "values": [45, 52, 48, 61, 70, 66, 78, 82, 74, 65, 58, 50]},
        {"name": "Memory", "values": [60, 63, 65, 68, 72, 75, 80, 84, 82, 78, 70, 65]},
        {"name": "Network", "values": [30, 38, 35, 42, 55, 50, 62, 68, 60, 48, 40, 35]},
    ],
}

_TEMPERATURE_ANOMALY = {
    "categories": ["1995", "1998", "2001", "2004", "2007", "2010", "2013", "2016", "2019", "2022"],
    "series": [
        {"name": "Arctic", "values": [-0.4, 0.2, 0.5, 0.9, 1.4, 1.1, 1.8, 2.6, 2.2, 2.9]},
        {"name": "Tropics", "values": [-0.2, 0.6, -0.1, 0.1, 0.3, 0.5, 0.2, 0.8, 0.6, 0.7]},
        {"name": "Antarctic", "values": [0.3, -0.5, -0.2, 0.4, -0.6, -0.3, 0.1, -0.8, 0.2, -0.4]},
    ],
}

_NODES = {
    "categories": ["00", "02", "04", "06", "08", "10", "12", "14", "16", "18", "20", "22"],
    "series": [
        {"name": "node-01", "values": [22, 18, 15, 30, 64, 88, 91, 85, 79, 62, 41, 28]},
        {"name": "node-02", "values": [25, 21, 17, 28, 59, 81, 95, 93, 84, 66, 45, 30]},
        {"name": "node-03", "values": [12, 10, 9, 14, 33, 52, 60, 58, 51, 38, 22, 15]},
        {"name": "node-04", "values": [40, 38, 35, 44, 70, 92, 98, 97, 90, 75, 58, 46]},
        {"name": "node-05", "values": [8, 7, 6, 9, 21, 35, 39, 37, 30, 22, 14, 10]},
        {"name": "node-06", "values": [30, None, None, 34, 61, 79, 83, 80, 72, 57, 40, 33]},
    ],
}

_GENRES = {
    "categories": ["2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023", "2024"],
    "series": [
        {"name": "Jazz", "values": [42, 45, 38, 50, 35, 40, 48, 52, 55]},
        {"name": "Rock", "values": [88, 82, 76, 70, 65, 62, 60, 58, 55]},
        {"name": "Pop", "values": [110, 118, 125, 130, 120, 135, 142, 148, 155]},
        {"name": "Electronic", "values": [30, 38, 50, 65, 80, 95, 108, 120, 132]},
        {"name": "Classical", "values": [25, 22, 24, 20, 18, 20, 22, 24, 26]},
    ],
}

_ADJUSTMENTS = {
    "categories": ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6"],
    "series": [
        {"name": "Hardware", "values": [40, 52, 48, 61, 58, 66]},
        {"name": "Software", "values": [35, 30, -6, 42, 47, 51]},
        {"name": "Services", "values": [22, 28, 31, 29, 36, 40]},
    ],
}

_LEAGUE = {
    "categories": ["2020", "2021", "2022", "2023", "2024"],
    "series": [
        {"name": "Alpha", "values": [3, 2, 1, 2, 1]},
        {"name": "Beta", "values": [1, 3, 4, 3, 4]},
        {"name": "Gamma", "values": [2, 1, 2, 1, 2]},
        {"name": "Delta", "values": [5, 4, 3, 4, 3]},
        {"name": "Epsilon", "values": [4, 5, 5, 5, 5]},
    ],
}

_APP_STORE = {
    "categories": ["W1", "W2", "W3", "W4", "W5", "W6", "W7", "W8"],
    "series": [
        {"name": "NoteFlow", "values": [4, 3, 3, 1, 1, 2, 2, 1]},
        {"name": "TaskPilot", "values": [1, 1, 2, 2, 3, 3, 1, 2]},
        {"name": "MindMap+", "values": [2, 2, 1, 3, 2, 1, 3, 3]},
        {"name": "Calendo", "values": [3, 4, 4, 4, None, None, 5, 4]},
        {"name": "Focus Timer", "values": [5, 5, 5, 5, 4, 4, 4, 5]},
    ],
}

_TIED_RANKS = {
    "series": [
        {"name": "Team Red", "points": [
            {"x": "2024-Q1", "y": 1}, {"x": "2024-Q2", "y": 2}, {"x": "2024-Q3", "y": 2}, {"x": "2024-Q4", "y": 1}]},
        {"name": "Team Blue", "points": [
            {"x": "2024-Q1", "y": 2}, {"x": "2024-Q2", "y": 2}, {"x": "2024-Q3", "y": 1}, {"x": "2024-Q4", "y": 3}]},
        {"name": "Team Green", "points": [
            {"x": "2024-Q1", "y": 3}, {"x": "2024-Q2", "y": 1}, {"x": "2024-Q3", "y": None}, {"x": "2024-Q4", "y": 2}]},
    ],
}


# ---------------------------------------------------------------------------
# COMPARISON
# ---------------------------------------------------------------------------

_BAR_OPTIONS = [
    orientation_option("vertical", "`horizontal` draws bars; `type=\"bar\"` draws columns unless this is set."),
    AttributeDoc(
        name="group",
        description=("How several series share a category: side by side, stacked (negative values below "
                     "zero) or as each value's signed share of the category on a percent axis. `grouped` "
                     "and `stacked` are aliases; any other value clusters."),
        kind="enum", values=["cluster", "stack", "stack100"], default="cluster"),
    _sort_option(),
]

_BAR = ChartTypeDoc(
    type_key="bar",
    title="Bar Chart",
    category="comparison",
    summary="Bars comparing values across categories (horizontal with orientation=\"horizontal\").",
    description=(
        "Rendered by bar.js, the same renderer as the column chart: type=\"bar\" draws vertical columns "
        "unless orientation=\"horizontal\" is set, which every example here does. Several series are "
        "clustered side by side; group=\"stack\" stacks them (negative values stack below zero) and "
        "group=\"stack100\" shows each value's signed share of its category on a percent axis. "
        "sort=\"asc\" or \"desc\" orders the categories by their total. A null value draws no bar, "
        "duplicate category labels keep their own bars, and long labels get the room they need or are "
        "shortened with an ellipsis. Every bar is a focusable mark (the chart is one tab stop; the "
        "arrow keys move between bars) and a click or Enter / Space emits mj-chart-bar-click "
        "{ series, category, value }."
    ),
    data_shape=_CATEGORY_SERIES_SHAPE,
    options=_BAR_OPTIONS,
    examples=[
        gallery_example(
            "basic", "Clustered bars",
            "<p>Two series compared region by region; the legend hides and shows a series.</p>",
            _chart("bar", _REGIONS, "Sales by region", attrs='orientation="horizontal"', legend=True),
        ),
        gallery_example(
            "stacked", "Stacked with negatives",
            "<p><code>group=\"stack\"</code>: inflows stack to the right of zero, outflows to the left, "
            "so each row shows both totals.</p>",
            _chart("bar", _CASH_FLOW, "Cash flow by region ($k)",
                   attrs='orientation="horizontal" group="stack"', legend=True),
        ),
        gallery_example(
            "percent", "100% stacked",
            "<p><code>group=\"stack100\"</code>: every bar is 100% of its region; hover a segment for its "
            "count and share.</p>",
            _chart("bar", _TICKET_CHANNELS, "Support tickets by channel",
                   attrs='orientation="horizontal" group="stack100"', legend=True, height=240),
        ),
        gallery_example(
            "sorted", "Sorted, long labels and a gap",
            "<p><code>sort=\"desc\"</code> ranks the components; the long label gets its room, and "
            "<em>Account settings</em> has a <code>null</code> value, so it has no bar.</p>",
            _chart("bar", _DEFECTS, "Open defects by component",
                   attrs='orientation="horizontal" sort="desc"'),
        ),
        gallery_example(
            "events", "Click events",
            "<p>The script listens for <code>mj-chart-bar-click</code>, clicks the first bar and presses "
            "Enter on the last one; see the Events panel.</p>",
            _chart("bar", _REGIONS, "Sales by region", attrs='orientation="horizontal"', legend=True),
            script=_events_script(["mj-chart-bar-click"], "bar"),
        ),
    ],
)

_COLUMN = ChartTypeDoc(
    type_key="column",
    title="Column Chart",
    category="comparison",
    summary="Vertical columns comparing values across categories.",
    description=(
        "The vertical form of the bar chart, drawn by the same bar.js renderer (vertical is the default "
        "orientation, so type=\"column\" and type=\"bar\" draw the same chart). Several series cluster "
        "in each category; group=\"stack\" stacks them and group=\"stack100\" normalises each category "
        "to 100 percent; sort=\"asc\" / \"desc\" orders the categories by total. Crowded category labels "
        "are thinned or rotated so they never overprint. Negative values grow down from the zero line "
        "and a null value draws nothing. Clicking a column, or Enter / Space on the focused column, "
        "emits mj-chart-bar-click { series, category, value }."
    ),
    data_shape=_CATEGORY_SERIES_SHAPE,
    options=[
        orientation_option("vertical", "`horizontal` turns the columns into bars."),
        _BAR_OPTIONS[1],
        _BAR_OPTIONS[2],
    ],
    examples=[
        gallery_example(
            "basic", "Clustered columns",
            "<p>Three products per quarter; toggle a product in the legend.</p>",
            _chart("column", _QUARTERS, "Quarterly revenue by product", legend=True),
        ),
        gallery_example(
            "stacked", "Stacked columns",
            "<p><code>group=\"stack\"</code>: the top of each column is the quarter's total.</p>",
            _chart("column", _QUARTERS, "Quarterly revenue by product", attrs='group="stack"', legend=True),
        ),
        gallery_example(
            "many-categories", "24 categories",
            "<p>Two years of monthly data: the category labels are thinned or rotated to fit. Narrow the "
            "preview to see it adapt.</p>",
            _chart("column", _SIGNUPS, "Monthly sign-ups"),
        ),
        gallery_example(
            "negative-and-missing", "Negative and missing values",
            "<p>Loss months grow down from zero; June is <code>null</code> (not closed yet) and has no "
            "column.</p>",
            _chart("column", _PROFIT, "Operating profit ($k)", height=260),
        ),
        gallery_example(
            "events", "Click events",
            "<p>The script logs <code>mj-chart-bar-click</code> for a clicked column and for Enter on "
            "the last one.</p>",
            _chart("column", _QUARTERS, "Quarterly revenue by product", legend=True),
            script=_events_script(["mj-chart-bar-click"], "bar"),
        ),
    ],
)

_LOLLIPOP = ChartTypeDoc(
    type_key="lollipop",
    title="Lollipop Chart",
    category="comparison",
    summary="Stem-and-dot alternative to bar charts with less ink.",
    description=(
        "Each category is a thin stem from zero to a dot at its value: lower ink than a bar chart and "
        "well suited to ranked scorecards. Vertical by default (stems rise from the category axis); "
        "orientation=\"horizontal\" lays them along rows. sort=\"desc\" (or \"asc\") orders the "
        "categories by value, the ranking form. marker-size sets the dot radius (a series may set its "
        "own markerSize); several series sit side by side in each category. The value axis always "
        "includes zero, so negative values hang below it; a null value draws no lollipop. Clicking a "
        "dot, or Enter / Space on it, emits mj-chart-lollipop-click { series, category, value }."
    ),
    data_shape=(
        _CATEGORY_SERIES_SHAPE +
        '<p><code>series[].markerSize</code>: optional dot radius of that series in px.</p>'
    ),
    options=[
        orientation_option("vertical", "`horizontal` puts the categories on rows and the stems along x."),
        AttributeDoc(name="marker-size", description="Dot radius in px (1-40).", kind="number", default="8"),
        _sort_option(),
    ],
    examples=[
        gallery_example(
            "basic", "Ranked scorecard",
            "<p>Horizontal lollipops sorted from the best to the weakest score.</p>",
            _chart("lollipop", _SCORES, "Site audit scores", attrs='orientation="horizontal" sort="desc"',
                   height=260),
        ),
        gallery_example(
            "two-series", "Two series, vertical",
            "<p>The default vertical layout with two series side by side and smaller dots "
            "(<code>marker-size=\"6\"</code>).</p>",
            _chart("lollipop", _LOAD_TIMES, "Median page load time (s)", attrs='marker-size="6"', legend=True),
        ),
        gallery_example(
            "negative-and-missing", "Negative and missing values",
            "<p>Stems hang below zero for negative anomalies; April is <code>null</code> and is left "
            "out.</p>",
            _chart("lollipop", _ANOMALY, "Monthly temperature anomaly (°C)", height=260),
        ),
        gallery_example(
            "events", "Click events",
            "<p>The script logs <code>mj-chart-lollipop-click</code> for a clicked dot and for Enter on "
            "the last one.</p>",
            _chart("lollipop", _SCORES, "Site audit scores", attrs='orientation="horizontal" sort="desc"',
                   height=260),
            script=_events_script(["mj-chart-lollipop-click"], "dot"),
        ),
    ],
)

_DOTPLOT = ChartTypeDoc(
    type_key="dotplot",
    title="Dot Plot",
    category="comparison",
    summary="Cleveland dot plot comparing two periods or groups per category.",
    description=(
        "Dots sit at the centre of each category's band; the value axis spans the data (it need not "
        "start at zero) and leaves room for the markers at both ends. Each series has its own marker "
        "shape as well as its own colour. The show-connectors boolean attribute (or "
        "meta.showConnectors in the data) joins the dots of neighbouring series, turning the plot into "
        "a dumbbell chart that emphasises the change. marker-size sets the marker radius and "
        "sort=\"asc\" / \"desc\" orders the categories. Vertical by default; orientation=\"horizontal\" "
        "puts the categories on rows. Clicking a dot, or Enter / Space on it, emits "
        "mj-chart-dotplot-click { series, category, value }."
    ),
    data_shape=(
        _CATEGORY_SERIES_SHAPE +
        '<p><code>meta.showConnectors</code>: <code>true</code> draws the dumbbell connectors when the '
        '<code>show-connectors</code> attribute is absent.</p>'
    ),
    options=[
        orientation_option("vertical", "`horizontal` puts the categories on rows (the usual Cleveland layout)."),
        AttributeDoc(name="show-connectors",
                     description="Join the dots of neighbouring series in each category (dumbbell chart).",
                     kind="boolean"),
        AttributeDoc(name="marker-size", description="Marker radius in px (1-30).", kind="number", default="6"),
        _sort_option(),
    ],
    examples=[
        gallery_example(
            "basic", "Dumbbell",
            "<p>Two survey years per department joined by connectors.</p>",
            _chart("dotplot", _ENGAGEMENT, "Engagement score by department",
                   attrs='orientation="horizontal" show-connectors', legend=True),
        ),
        gallery_example(
            "three-series", "Three series, sorted",
            "<p>Three segments without connectors: each has its own marker shape. "
            "<code>sort=\"desc\"</code> orders the areas by their total score.</p>",
            _chart("dotplot", _SATISFACTION, "Satisfaction by product area (0-10)",
                   attrs='orientation="horizontal" sort="desc" marker-size="7"', legend=True, height=300),
        ),
        gallery_example(
            "vertical", "Vertical, connectors from the data",
            "<p>The default vertical layout; the connectors come from <code>meta.showConnectors</code>, "
            "not from an attribute.</p>",
            _chart("dotplot", _RELEASE_GAP, "Pipeline stage duration (min)", legend=True),
        ),
        gallery_example(
            "events", "Click events",
            "<p>The script logs <code>mj-chart-dotplot-click</code> for a clicked dot and for Enter on "
            "the last one.</p>",
            _chart("dotplot", _ENGAGEMENT, "Engagement score by department",
                   attrs='orientation="horizontal" show-connectors', legend=True),
            script=_events_script(["mj-chart-dotplot-click"], "dot"),
        ),
    ],
)

_BULLET = ChartTypeDoc(
    type_key="bullet",
    title="Bullet Chart",
    category="comparison",
    summary="Compact KPI bars against qualitative ranges and a target marker.",
    description=(
        "Each series entry is one bullet: a performance bar (value), a target tick (target) and "
        "qualitative range bands (ranges, read in ascending order whatever order they are given in, "
        "with optional rangeLabels). Bullets are horizontal rows by default; orientation=\"vertical\" "
        "draws columns. scale=\"auto\" gives each bullet its own scale and tick labels when the bullets' "
        "ranges differ, scale=\"shared\" forces one common scale and scale=\"independent\" always uses "
        "one per bullet. The range labels form the key above the bullets and the chart's legend; the "
        "accessible table has one row per bullet. Clicking a performance bar, or Enter / Space on it, "
        "emits mj-chart-bullet-click { name, value, target }."
    ),
    data_shape=(
        '<pre><code>{\n'
        '  series: [{\n'
        '    name: string,\n'
        '    value: number,          // the performance measure\n'
        '    target?: number,        // the target tick\n'
        '    ranges?: number[],      // band thresholds, any order\n'
        '    rangeLabels?: string[]  // names of the bands, darkest first\n'
        '  }]\n'
        '}</code></pre>'
        '<p>Band <em>i</em> spans from the previous threshold (or 0) to threshold <em>i</em>. A '
        'bullet\'s track ends at its largest range, or at its value / target when larger; the bar is '
        'clipped to the track.</p>'
    ),
    options=[
        orientation_option("horizontal", "Bullets are rows by default; `vertical` draws columns."),
        AttributeDoc(
            name="scale",
            description=("One value scale for all bullets (`shared`), one per bullet (`independent`), or "
                         "`auto`: independent when the bullets' ranges differ."),
            kind="enum", values=["auto", "shared", "independent"], default="auto"),
    ],
    examples=[
        gallery_example(
            "basic", "KPI bullets",
            "<p>Three KPIs with different ranges, so each bullet has its own scale.</p>",
            _chart("bullet", _KPIS, "Quarter KPIs", height=240),
        ),
        gallery_example(
            "shared-scale", "Shared scale",
            "<p>Four regions against their quotas on one common scale "
            "(<code>scale=\"shared\"</code>), with custom range labels.</p>",
            _chart("bullet", _QUOTAS, "Regional sales against quota ($k)", attrs='scale="shared"', height=280),
        ),
        gallery_example(
            "vertical", "Vertical bullets",
            "<p><code>orientation=\"vertical\"</code> draws the bullets as columns; these have no range "
            "labels, so the key shows only the target.</p>",
            _chart("bullet", _STORAGE, "Storage used per cluster (TB)", attrs='orientation="vertical"', height=300),
        ),
        gallery_example(
            "events", "Click events",
            "<p>The script logs <code>mj-chart-bullet-click</code> for a clicked bar and for Enter on the "
            "last one.</p>",
            _chart("bullet", _KPIS, "Quarter KPIs", height=240),
            script=_events_script(["mj-chart-bullet-click"], "bullet-bar"),
        ),
    ],
)

_SLOPE = ChartTypeDoc(
    type_key="slope",
    title="Slope Chart",
    category="comparison",
    summary="Shows direction and magnitude of change between two time points.",
    description=(
        "Exactly two categories define the left and right columns and each series gives its two "
        "values; both columns share one value scale, so the slopes compare honestly. Endpoint labels "
        "show the name and value in the text colour beside a dot in the series colour; labels that "
        "would overlap are nudged apart (with a short leader) and the gutters are as wide as the "
        "longest label. Data with more than two periods is a render error (the chart shows it and "
        "emits mj-chart-error): use a line chart for those. The renderer has no option attributes. "
        "Each slope line is focusable; a click or Enter / Space emits mj-chart-slope-click "
        "{ series, leftValue, rightValue }."
    ),
    data_shape=(
        '<pre><code>{\n'
        '  categories: [string, string],          // the two column headers\n'
        '  series: [{ name: string, values: [number, number], color?: string }]\n'
        '}</code></pre>'
        '<p>More than two categories (or more than two values without categories) is an error.</p>'
    ),
    options=[],
    examples=[
        gallery_example(
            "basic", "Two periods",
            "<p>Five regions between 2020 and 2024 on one shared scale.</p>",
            _chart("slope", _BROADBAND, "Broadband adoption, percent of households"),
        ),
        gallery_example(
            "crowded-labels", "Close values",
            "<p>Several plans end close together: their labels are nudged apart and joined to their dots "
            "by leaders.</p>",
            _chart("slope", _CHURN, "Monthly churn by plan (%)", height=320),
        ),
        gallery_example(
            "error", "Three periods (error)",
            "<p>Three categories are rejected: the chart shows the render error state and emits "
            "<code>mj-chart-error</code> (see Events).</p>",
            _chart("slope", _THREE_PERIODS, "Broadband adoption, three periods", height=220),
        ),
        gallery_example(
            "events", "Click events",
            "<p>The script logs <code>mj-chart-slope-click</code> for a clicked line and for Enter on the "
            "last one.</p>",
            _chart("slope", _BROADBAND, "Broadband adoption, percent of households"),
            script=_events_script(["mj-chart-slope-click"], "slope-line"),
        ),
    ],
)

_RADAR = ChartTypeDoc(
    type_key="radar",
    title="Radar Chart",
    category="comparison",
    summary="Spider chart comparing entities across multiple dimensions.",
    description=(
        "Categories define the spokes (starting at the top, clockwise) and each series draws a polygon. "
        "All spokes share one scale from 0 (or the smallest value, when one is negative) to a nice "
        "maximum, so the rings are labelled with values and spokes can be compared; a spoke gets its "
        "own scale only when the data supplies dimensions[i].domainMin / domainMax, and then each spoke "
        "label shows its range. fill=\"false\" draws outlines only and grid-shape=\"circle\" round "
        "rings. A null value leaves the outline open at that spoke. Each polygon and each dot is "
        "focusable: a polygon emits mj-chart-radar-click { series } and a dot "
        "mj-chart-radar-dot-click { series, category, value }. Several series get a key row under the "
        "radar; with a nested <mj-chart-legend> the key is left out and the legend lists the series as "
        "show / hide toggles."
    ),
    data_shape=(
        '<pre><code>{\n'
        '  categories: string[],                  // the spokes\n'
        '  series: [{ name: string, values: (number | null)[] }],\n'
        '  dimensions?: [{ domainMin?: number, domainMax?: number }]   // by spoke index\n'
        '}</code></pre>'
        '<p>One value per spoke; extra values are ignored. Values outside a spoke\'s own scale are drawn '
        'at its centre or rim.</p>'
    ),
    options=[
        AttributeDoc(name="fill", description="Fill the polygons; `false` draws outlines only.",
                     kind="boolean", default="true"),
        AttributeDoc(name="grid-shape", description="Shape of the ring gridlines.", kind="enum",
                     values=["polygon", "circle"], default="polygon"),
    ],
    examples=[
        gallery_example(
            "basic", "Two platforms",
            "<p>Two filled polygons on a shared, labelled scale; the key above the plot names them.</p>",
            _chart("radar", _PLATFORMS, "Platform evaluation", attrs='grid-shape="polygon"',
                   height=320),
        ),
        gallery_example(
            "outlines", "Outlines on round rings",
            "<p><code>fill=\"false\"</code> and <code>grid-shape=\"circle\"</code> with three series; "
            "the nested <code>&lt;mj-chart-legend&gt;</code> replaces the inline key (click an entry to "
            "hide a player).</p>",
            _chart("radar", _PLAYERS, "Player attributes", attrs='fill="false" grid-shape="circle"',
                   height=340, legend=True),
        ),
        gallery_example(
            "spoke-scales", "A scale per spoke",
            "<p><code>dimensions[i].domainMin / domainMax</code> give each spoke its own range (shown in "
            "the spoke label), for measures in different units.</p>",
            _chart("radar", _LAPTOPS, "Laptop comparison", height=340),
        ),
        gallery_example(
            "missing-values", "Missing values",
            "<p>A <code>null</code> leaves each outline open at that spoke instead of dropping to "
            "zero.</p>",
            _chart("radar", _SURVEY_GAPS, "Vendor survey (incomplete)", height=320),
        ),
        gallery_example(
            "events", "Click events",
            "<p>The script clicks a polygon (<code>mj-chart-radar-click</code>) and presses Enter on a "
            "dot (<code>mj-chart-radar-dot-click</code>).</p>",
            _chart("radar", _PLATFORMS, "Platform evaluation", height=320),
            script=(
                'const chart = document.getElementById("demo-chart")\n'
                'for (const name of ["mj-chart-radar-click", "mj-chart-radar-dot-click"]) {\n'
                '  chart.addEventListener(name, (event) => mjSandbox.log("listener: " + name, event.detail))\n'
                '}\n'
                '\n'
                'await chart.redraw()\n'
                'const area = chart.shadowRoot.querySelector(\'[part~="radar-area"]\')\n'
                'area.dispatchEvent(new MouseEvent("click", { bubbles: true }))\n'
                'const dot = chart.shadowRoot.querySelector(\'[part~="dot"]\')\n'
                'dot.focus()\n'
                'dot.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true }))\n'
            ),
        ),
    ],
)

_PARALLEL = ChartTypeDoc(
    type_key="parallel",
    title="Parallel Coordinates",
    category="comparison",
    summary="Multi-dimensional comparison with one vertical axis per dimension.",
    description=(
        "Each dimension is a vertical axis with its name, an optional unit and an optional domain "
        "[min, max] (without one the axis spans the observed values, nicely rounded). Each series "
        "carries observations, numeric rows aligned with the dimensions, drawn as polylines across the "
        "axes; a null value breaks the line and lines are clipped to the plot. The curved attribute "
        "draws smooth curves between the axes and color-by=\"<dimension name>\" colours the lines with "
        "a sequential ramp keyed below the plot. Up to 200 observations are focusable marks; a click or "
        "Enter / Space emits mj-chart-parallel-click { series, observation }. The accessible table "
        "lists every observation. Several series get a key below the plot, unless a nested "
        "<mj-chart-legend> lists them (as show / hide toggles)."
    ),
    data_shape=(
        '<pre><code>{\n'
        '  dimensions: [{ name: string, domain?: [number, number], unit?: string }],\n'
        '  series: [{ name: string, color?: string, observations: (number | null)[][] }]\n'
        '}</code></pre>'
        '<p>Each observation has one value per dimension, in order. Denser data (more than 200 '
        'observations) is drawn as plain lines at reduced opacity.</p>'
    ),
    options=[
        AttributeDoc(name="curved", description="Draw cubic curves between the axes instead of straight lines.",
                     kind="boolean"),
        AttributeDoc(name="color-by",
                     description=("Name of a dimension: colour every line by its value there with a "
                                  "sequential ramp (a gradient key replaces the series key)."),
                     kind="string", values=["Height", "Weight", "Age", "Score"]),
    ],
    examples=[
        gallery_example(
            "basic", "Curved lines",
            "<p>Two groups of athletes across four measures with fixed domains.</p>",
            _chart("parallel", _ATHLETES, "Athlete measurements", attrs="curved", height=300),
        ),
        gallery_example(
            "color-by", "Coloured by a dimension",
            "<p><code>color-by=\"Score\"</code>: the line colour follows each athlete's score; the "
            "gradient key below the plot reads it.</p>",
            _chart("parallel", _ATHLETES, "Athlete measurements coloured by score", attrs='color-by="Score"',
                   height=320),
        ),
        gallery_example(
            "auto-domains", "Automatic domains and gaps",
            "<p>No <code>domain</code>, so each axis spans its data; two <code>null</code> values break "
            "their lines. The nested <code>&lt;mj-chart-legend&gt;</code> takes the place of the inline "
            "key.</p>",
            _chart("parallel", _CARS, "Car specifications", height=300, legend=True),
        ),
        gallery_example(
            "events", "Click events",
            "<p>The script logs <code>mj-chart-parallel-click</code> for a clicked line and for Enter on "
            "the last one.</p>",
            _chart("parallel", _ATHLETES, "Athlete measurements", attrs="curved", height=300),
            script=_events_script(["mj-chart-parallel-click"], "observation"),
        ),
    ],
)


# ---------------------------------------------------------------------------
# TREND
# ---------------------------------------------------------------------------

_LINE_OPTIONS = [
    _curve_option("linear"),
    AttributeDoc(name="show-points",
                 description="A marker on every point (a point without a neighbour always gets one).",
                 kind="boolean"),
    _x_scale_option(),
]

_LINE = ChartTypeDoc(
    type_key="line",
    title="Line Chart",
    category="trend",
    summary="Line showing values over time, a number line or categories.",
    description=(
        "Rendered by line.js. Series use points [{x, y}] or values aligned with categories. ISO dates "
        "and epoch milliseconds in x use a time scale (points are placed by date and drawn in date "
        "order), other numbers a linear scale, anything else categories; x-scale overrides the choice. "
        "A null y is a gap. show-points adds a marker at every point (an isolated point always gets "
        "one) and curve accepts linear (default), monotone (smooth without overshooting) or step. "
        "Every point has a focusable target: a click or Enter / Space emits mj-chart-line-click "
        "{ series, x, y }."
    ),
    data_shape=_TREND_SHAPE,
    options=_LINE_OPTIONS,
    examples=[
        gallery_example(
            "basic", "Monthly time series",
            "<p>Points with <code>YYYY-MM</code> dates on a time scale, with markers.</p>",
            _chart("line", _REVENUE_POINTS, "Monthly revenue ($k)", attrs="show-points", height=260),
        ),
        gallery_example(
            "numeric-x", "Numeric x, smooth curve",
            "<p>Numeric x values use a linear scale, so uneven speeds are spaced honestly; "
            "<code>curve=\"monotone\"</code> smooths the line.</p>",
            _chart("line", _STOPPING, "Stopping distance by speed (km/h)", attrs='curve="monotone" show-points',
                   height=260),
        ),
        gallery_example(
            "gaps", "Gaps for missing values",
            "<p><code>null</code> readings break the line; the lone 22:00 reading still gets a "
            "marker.</p>",
            _chart("line", _SENSOR, "Greenhouse humidity", height=260),
        ),
        gallery_example(
            "step-curve", "Step curve",
            "<p><code>curve=\"step\"</code> holds each value until the next point.</p>",
            _chart("line", _PRICING_TIERS, "Monthly price by release ($)", attrs='curve="step" show-points',
                   legend=True, height=260),
        ),
        gallery_example(
            "events", "Click events",
            "<p>The script logs <code>mj-chart-line-click</code> for a clicked point and for Enter on the "
            "last one.</p>",
            _chart("line", _REVENUE_POINTS, "Monthly revenue ($k)", attrs="show-points", height=260),
            script=_events_script(["mj-chart-line-click"], "hit"),
        ),
    ],
)

_MULTILINE = ChartTypeDoc(
    type_key="multiline",
    title="Multi-line Chart",
    category="trend",
    summary="Multiple series on a shared axis for trend comparison.",
    description=(
        "multiline is an alias of line registered in line.js: any number of series share the axes and "
        "the legend hides and shows them (mj-chart-series-toggle). Series may mix values aligned with "
        "categories or points with their own x; dated points of different series are placed on one "
        "time axis. curve=\"monotone\" smooths the lines with a monotone cubic that never overshoots "
        "the data. A null y is a gap. Every point has a focusable target: a click or Enter / Space "
        "emits mj-chart-line-click { series, x, y }."
    ),
    data_shape=_TREND_SHAPE,
    options=_LINE_OPTIONS,
    examples=[
        gallery_example(
            "basic", "Three series",
            "<p>Three device types with smooth monotone curves; toggle a series in the legend.</p>",
            _chart("multiline", _DEVICES, "Sessions by device", attrs='curve="monotone"', legend=True),
        ),
        gallery_example(
            "time-points", "Irregular dates",
            "<p>Two series with unevenly spaced dates share one time axis; gaps between samples are "
            "drawn to scale.</p>",
            _chart("multiline", _LATENCY, "API latency (ms)", attrs="show-points", legend=True),
        ),
        gallery_example(
            "gaps", "Missing values",
            "<p>Each store has unrecorded days (<code>null</code>): its line breaks there.</p>",
            _chart("multiline", _PRICES, "Average basket price ($)", attrs="show-points", legend=True),
        ),
        gallery_example(
            "events", "Series toggle and click events",
            "<p>The script hides <em>Tablet</em> with <code>toggleSeries()</code> "
            "(<code>mj-chart-series-toggle</code>) and clicks a point "
            "(<code>mj-chart-line-click</code>).</p>",
            _chart("multiline", _DEVICES, "Sessions by device", attrs='curve="monotone"', legend=True),
            script=(
                'const chart = document.getElementById("demo-chart")\n'
                'for (const name of ["mj-chart-line-click", "mj-chart-series-toggle"]) {\n'
                '  chart.addEventListener(name, (event) => mjSandbox.log("listener: " + name, event.detail))\n'
                '}\n'
                '\n'
                'chart.toggleSeries("Tablet")\n'
                'await chart.redraw()\n'
                'const point = chart.shadowRoot.querySelector(\'[part~="hit"][tabindex]\')\n'
                'point.dispatchEvent(new MouseEvent("click", { bubbles: true }))\n'
            ),
        ),
    ],
)

_AREA_OPTIONS = [
    AttributeDoc(name="stack",
                 description=("Stacking of several series: `none` overlaps them, `stack` stacks them, "
                              "`stack100` normalises every x to 100 percent. The default comes from the type."),
                 kind="enum", values=["none", "stack", "stack100"]),
    _curve_option("linear"),
    AttributeDoc(name="fill-opacity", description="Opacity of the filled areas (0-1).", kind="number",
                 default="0.3"),
    _x_scale_option(),
]

_AREA_SHAPE = _TREND_SHAPE + (
    '<p>In the stacked modes positive values stack upward and negative values downward from zero; a '
    '<code>null</code> splits that layer while the layers above keep stacking on the ones below.</p>'
)


def _area_options(default_stack):
    """
        The area option docs with the stack default of the type.
    """

    stack = AttributeDoc(name="stack", description=_AREA_OPTIONS[0].description, kind="enum",
                         values=["none", "stack", "stack100"], default=default_stack)
    options = [stack] + _AREA_OPTIONS[1:]
    return options


_AREA = ChartTypeDoc(
    type_key="area",
    title="Area Chart",
    category="trend",
    summary="Filled area chart showing volume beneath a trend line.",
    description=(
        "An unstacked area fills each series to zero (all-negative data fills downward from zero). "
        "fill-opacity sets the translucency and curve works as for the line chart. A null value "
        "splits the area instead of dropping to zero. Several series overlap unless stack=\"stack\" or "
        "stack=\"stack100\" is set (or the stacked-area / area100 types are used). Each point is "
        "focusable and reads its value; a click or Enter / Space emits mj-chart-area-click "
        "{ series, x, y } (plus share in the stacked modes)."
    ),
    data_shape=_AREA_SHAPE,
    options=_area_options("none"),
    examples=[
        gallery_example(
            "basic", "Single area",
            "<p>A smooth area with <code>fill-opacity=\"0.4\"</code>.</p>",
            _chart("area", _SESSIONS, "Website sessions", attrs='curve="monotone" fill-opacity="0.4"',
                   height=260),
        ),
        gallery_example(
            "negative", "Negative values",
            "<p>The deficit years fill from zero downward, the surplus years upward.</p>",
            _chart("area", _TRADE, "Trade balance ($bn)", height=260),
        ),
        gallery_example(
            "overlap", "Overlapping series",
            "<p>Two unstacked series overlap; a lower <code>fill-opacity</code> keeps both readable.</p>",
            _chart("area", _TRAFFIC, "Visits by source", attrs='fill-opacity="0.25"', legend=True, height=260),
        ),
        gallery_example(
            "gaps", "A gap",
            "<p>Week 4 is <code>null</code> (an outage): the area is split there, not dropped to "
            "zero.</p>",
            _chart("area", _OUTAGE, "Weekly requests", height=260),
        ),
        gallery_example(
            "events", "Click events",
            "<p>The script logs <code>mj-chart-area-click</code> for a clicked point and for Enter on the "
            "last one.</p>",
            _chart("area", _SESSIONS, "Website sessions", attrs='curve="monotone" fill-opacity="0.4"',
                   height=260),
            script=_events_script(["mj-chart-area-click"], "hit"),
        ),
    ],
)

_STACKED_AREA = ChartTypeDoc(
    type_key="stacked-area",
    title="Stacked Area",
    category="trend",
    summary="Area chart with series stacked to reveal part-to-whole trends.",
    description=(
        "stacked-area is an alias registered in area.js that stacks the series bottom-up (stack "
        "defaults to \"stack\"), so the top edge at any x is the total. Negative values stack downward "
        "from zero. With curve=\"monotone\" the layers stay flush because each band's lower edge follows "
        "the curve of the layer below. A null value splits that layer. Each point's target reads its "
        "value and its share of the total; a click or Enter / Space emits mj-chart-area-click "
        "{ series, x, y, share }."
    ),
    data_shape=_AREA_SHAPE,
    options=_area_options("stack"),
    examples=[
        gallery_example(
            "basic", "Stacked layers",
            "<p>Three deployment types stacked; the top edge is the total.</p>",
            _chart("stacked-area", _WORKLOADS, "Workloads by deployment ($M)", legend=True),
        ),
        gallery_example(
            "time-monotone", "Dated points, smooth",
            "<p>Date-time points on a time axis with <code>curve=\"monotone\"</code>; the bands stay "
            "flush.</p>",
            _chart("stacked-area", _ENERGY, "Household energy use (kWh)", attrs='curve="monotone"', legend=True),
        ),
        gallery_example(
            "gaps", "Missing values",
            "<p>A <code>null</code> splits that layer; the layers above still stack on the ones "
            "below.</p>",
            _chart("stacked-area", _BACKLOG, "Open backlog items", legend=True),
        ),
        gallery_example(
            "events", "Click events",
            "<p>The script logs <code>mj-chart-area-click</code> (with <code>share</code>) for a clicked "
            "point and for Enter on the last one.</p>",
            _chart("stacked-area", _WORKLOADS, "Workloads by deployment ($M)", legend=True),
            script=_events_script(["mj-chart-area-click"], "hit"),
        ),
    ],
)

_AREA100 = ChartTypeDoc(
    type_key="area100",
    title="100% Stacked Area",
    category="trend",
    summary="Stacked area normalised to 100% to show share over time.",
    description=(
        "area100 is an alias registered in area.js (stack defaults to \"stack100\") that normalises "
        "every x position so the series sum to 100 percent of the absolute total; the value axis is "
        "labelled in percent and each point reads both its value and its share, which makes "
        "market-share or composition trends readable. A null value splits that layer. A click or Enter "
        "/ Space on a point emits mj-chart-area-click { series, x, y, share }."
    ),
    data_shape=_AREA_SHAPE,
    options=_area_options("stack100"),
    examples=[
        gallery_example(
            "basic", "Market share",
            "<p>Four browsers as shares of 100 percent per year.</p>",
            _chart("area100", _BROWSERS, "Browser share (%)", legend=True),
        ),
        gallery_example(
            "time-monotone", "Dated points, smooth",
            "<p>Fleet composition from half-yearly dates, smoothed with "
            "<code>curve=\"monotone\"</code>.</p>",
            _chart("area100", _FLEET, "Company fleet by drivetrain", attrs='curve="monotone"', legend=True),
        ),
        gallery_example(
            "gaps", "Missing values",
            "<p>The shares are computed from the values present at each x; <code>null</code> values "
            "split their layer.</p>",
            _chart("area100", _BACKLOG, "Backlog composition", legend=True),
        ),
        gallery_example(
            "events", "Click events",
            "<p>The script logs <code>mj-chart-area-click</code> for a clicked point and for Enter on the "
            "last one.</p>",
            _chart("area100", _BROWSERS, "Browser share (%)", legend=True),
            script=_events_script(["mj-chart-area-click"], "hit"),
        ),
    ],
)

_STEP = ChartTypeDoc(
    type_key="step",
    title="Step Chart",
    category="trend",
    summary="Step-line chart for values that hold until the next change.",
    description=(
        "Dates use a time scale, so each tread is as long as the level lasted. step-position controls "
        "where the jump sits: after (default) holds each value until the next x (the axis runs one "
        "interval past the last change so the final level has a tread), before jumps at the previous "
        "x, middle half-way between two x values. The fill boolean attribute shades the area down to "
        "zero and show-points=\"false\" hides the change markers. The value axis always includes zero. "
        "A null value is a gap: the level stops at its x and restarts at the next value. A click or "
        "Enter / Space on a point emits mj-chart-step-click { series, x, y }."
    ),
    data_shape=_TREND_SHAPE,
    options=[
        AttributeDoc(name="step-position", description="Where the vertical jump sits relative to each x.",
                     kind="enum", values=["after", "before", "middle"], default="after"),
        AttributeDoc(name="fill", description="Shade the area under the steps down to zero.", kind="boolean"),
        AttributeDoc(name="show-points", description="Markers at the change points; `false` hides them.",
                     kind="boolean", default="true"),
        _x_scale_option(),
    ],
    examples=[
        gallery_example(
            "basic", "Policy rate",
            "<p>Rate decisions on their real dates, filled; each level lasts until the next "
            "decision.</p>",
            _chart("step", _FED_RATE, "Fed funds target rate, upper bound (%)",
                   attrs='step-position="after" fill', height=260),
        ),
        gallery_example(
            "before", "Jump before",
            "<p><code>step-position=\"before\"</code>: each value applies from the previous day up to its "
            "own.</p>",
            _chart("step", _STOCK, "Warehouse stock level", attrs='step-position="before"', height=260),
        ),
        gallery_example(
            "middle", "Middle, no markers",
            "<p><code>step-position=\"middle\"</code> with <code>show-points=\"false\"</code>, two "
            "series.</p>",
            _chart("step", _PRICING_TIERS, "Monthly price by release ($)",
                   attrs='step-position="middle" show-points="false"', legend=True, height=260),
        ),
        gallery_example(
            "gaps", "A gap",
            "<p>12:00 is <code>null</code>: the 10:00 level stops there and the line restarts at "
            "14:00.</p>",
            _chart("step", _THERMOSTAT, "Thermostat schedule", height=260),
        ),
        gallery_example(
            "events", "Click events",
            "<p>The script logs <code>mj-chart-step-click</code> for a clicked point and for Enter on the "
            "last one.</p>",
            _chart("step", _FED_RATE, "Fed funds target rate, upper bound (%)",
                   attrs='step-position="after" fill', height=260),
            script=_events_script(["mj-chart-step-click"], "hit"),
        ),
    ],
)

_SPARKLINE = ChartTypeDoc(
    type_key="sparkline",
    title="Sparkline",
    category="trend",
    summary="Compact, axes-free inline trend indicator.",
    description=(
        "Sparklines draw only the trend shape: no axes, gridlines or legend. They are 48px tall unless "
        "the page sizes them, and keep working at word size. The values shorthand needs no categories; "
        "points with dates use a time scale. show-markers (default on) marks the first, last, minimum "
        "and maximum points, show-last-value adds the final value as text and "
        "sparkline-variant=\"bar\" draws zero-based bars. Only the first series is drawn (a console "
        "warning names the others). Hovering shows the nearest point; with markers each marker is "
        "focusable, without them the line is one focusable mark whose arrow keys step through the "
        "points. A click or Enter / Space emits mj-chart-sparkline-click { x, y }."
    ),
    data_shape=(
        '<pre><code>{\n'
        '  series: [{\n'
        '    name: string,\n'
        '    values?: (number | null)[],\n'
        '    points?: [{ x: string | number, y: number | null }]\n'
        '  }]\n'
        '}</code></pre>'
        '<p>Only <code>series[0]</code> is drawn. <code>categories</code> are optional and only label the '
        'points.</p>'
    ),
    options=[
        AttributeDoc(name="sparkline-variant", description="Line or zero-based bars.", kind="enum",
                     values=["line", "bar"], default="line"),
        AttributeDoc(name="show-markers", description="Dots on the first, last, minimum and maximum points.",
                     kind="boolean", default="true"),
        AttributeDoc(name="show-last-value", description="The final value as text after the line.",
                     kind="boolean"),
        _x_scale_option(),
    ],
    examples=[
        gallery_example(
            "basic", "Word-sized line",
            "<p>A 180 x 32 px sparkline with its last value.</p>",
            _chart("sparkline", _WEEKLY_REVENUE, "Weekly revenue trend", attrs="show-last-value",
                   height=32, width=180),
        ),
        gallery_example(
            "bars", "Bar variant",
            "<p><code>sparkline-variant=\"bar\"</code>: zero-based bars, negative values below the "
            "baseline.</p>",
            _chart("sparkline", _NET_FLOW, "Daily net flow", attrs='sparkline-variant="bar"',
                   height=40, width=220),
        ),
        gallery_example(
            "in-text", "In a KPI table",
            "<p>Sparklines inside table cells; the first one is driven by the controls.</p>",
            '<table class="kpis">\n'
            '  <thead><tr><th scope="col">Metric</th><th scope="col">Last 12 weeks</th></tr></thead>\n'
            '  <tbody>\n'
            '    <tr><th scope="row">Revenue</th><td>'
            '<mj-chart id="demo-chart" type="sparkline" show-last-value label="Revenue trend" '
            'style="height:28px;width:160px"><script type="application/json">'
            '{"series":[{"name":"Revenue","values":[88,92,85,97,104,99,111,108,120,115,128,135]}]}'
            '</script></mj-chart></td></tr>\n'
            '    <tr><th scope="row">Churn</th><td>'
            '<mj-chart type="sparkline" show-last-value label="Churn trend" '
            'style="height:28px;width:160px"><script type="application/json">'
            '{"series":[{"name":"Churn","values":[5.1,5.0,4.8,4.9,4.6,4.4,4.5,4.2,4.1,4.3,3.9,3.8]}]}'
            '</script></mj-chart></td></tr>\n'
            '    <tr><th scope="row">Tickets</th><td>'
            '<mj-chart type="sparkline" sparkline-variant="bar" label="Tickets trend" '
            'style="height:28px;width:160px"><script type="application/json">'
            '{"series":[{"name":"Tickets","values":[40,38,45,52,47,39,36,41,44,50,46,42]}]}'
            '</script></mj-chart></td></tr>\n'
            '  </tbody>\n'
            '</table>',
            css=(
                ".kpis { border-collapse: collapse; margin: var(--mj-space-4); }\n"
                ".kpis th, .kpis td { padding: var(--mj-space-2) var(--mj-space-3); text-align: start;\n"
                "  border-block-end: 1px solid var(--mj-border); }\n"
                ".kpis thead th { color: var(--mj-text-muted); font-weight: 600; }\n"
            ),
        ),
        gallery_example(
            "no-markers", "Without markers",
            "<p><code>show-markers=\"false\"</code>: the line itself is focusable; focus it and use the "
            "arrow keys to step through the points.</p>",
            _chart("sparkline", _WEEKLY_REVENUE, "Weekly revenue trend", attrs='show-markers="false"',
                   height=48, width=260),
        ),
        gallery_example(
            "events", "Click events",
            "<p>The script logs <code>mj-chart-sparkline-click</code> for a clicked marker and for Enter "
            "on the last one.</p>",
            _chart("sparkline", _WEEKLY_REVENUE, "Weekly revenue trend", attrs="show-last-value",
                   height=48, width=260),
            script=_events_script(["mj-chart-sparkline-click"], "spark-marker"),
        ),
    ],
)

_HORIZON = ChartTypeDoc(
    type_key="horizon",
    title="Horizon Chart",
    category="trend",
    summary="Banded folded area chart for dense multi-series time data.",
    description=(
        "Each series is one row; the rows share the chart height (row-height caps a row's height, rows "
        "never overflow the chart). Values are cut into horizon-bands magnitude bands (default 3, or "
        "the data's \"horizon-bands\") that are folded into the row and shaded darker for higher bands; "
        "the key above the rows gives each shade's value range and is the chart's legend. Negative "
        "values fold downward in a second hue: diverging is on automatically when the data has a "
        "negative value, diverging=\"false\" draws them as zero. Hovering a row reads the value under "
        "the pointer; each row is a focusable mark and a click or Enter / Space emits "
        "mj-chart-horizon-click { series }."
    ),
    data_shape=(
        _TREND_SHAPE +
        '<p><code>"horizon-bands"</code> (top level): optional default band count.</p>'
    ),
    options=[
        AttributeDoc(name="horizon-bands", description="Number of magnitude bands (1-8).", kind="number",
                     default="3"),
        AttributeDoc(name="row-height", description="Largest row height in px; by default the rows share the height.",
                     kind="number"),
        AttributeDoc(name="diverging",
                     description=("Fold negative values downward in a second hue. Default: on when the data "
                                  "holds a negative value; `false` draws negatives as zero, a bare "
                                  "`diverging` is `true`."),
                     kind="enum", values=["true", "false"]),
        _x_scale_option(),
    ],
    examples=[
        gallery_example(
            "basic", "Three rows",
            "<p>Three utilisation series folded into three bands each.</p>",
            _chart("horizon", _SERVERS, "Server utilisation (%)", attrs='horizon-bands="3"', height=200),
        ),
        gallery_example(
            "diverging", "Negative values",
            "<p>Temperature anomalies above and below zero: diverging turns on by itself and negative "
            "values fold down in a second hue.</p>",
            _chart("horizon", _TEMPERATURE_ANOMALY, "Temperature anomaly by region (°C)", height=220),
        ),
        gallery_example(
            "dense", "Many rows, more bands",
            "<p>Six nodes with <code>horizon-bands=\"4\"</code> and <code>row-height=\"32\"</code>; "
            "node-06 has two <code>null</code> readings (gaps).</p>",
            _chart("horizon", _NODES, "CPU load by node (%)", attrs='horizon-bands="4" row-height="32"',
                   height=260),
        ),
        gallery_example(
            "events", "Click events",
            "<p>The script logs <code>mj-chart-horizon-click</code> for a clicked row and for Enter on the "
            "last one.</p>",
            _chart("horizon", _SERVERS, "Server utilisation (%)", attrs='horizon-bands="3"', height=200),
            script=_events_script(["mj-chart-horizon-click"], "horizon-hit"),
        ),
    ],
)

_STREAMGRAPH = ChartTypeDoc(
    type_key="streamgraph",
    title="Streamgraph",
    category="trend",
    summary="Flowing symmetric stacked area emphasising rhythm and volume.",
    description=(
        "The baseline attribute sets the vertical layout: wiggle (default; the ThemeRiver baseline "
        "that minimises the streams' weighted slope), silhouette (centred on zero) or zero (a "
        "bottom-aligned stacked area). The y axis is hidden because y positions are layout artefacts. "
        "Streams are labelled at their thickest point; streams too thin for a label are listed in a "
        "key below the axis. curve defaults to monotone. A stream cannot be negative: a negative value "
        "is drawn as zero and reported with mj-chart-error; a null value is a gap in that stream. Each "
        "value is focusable and reads its share of the total; a click or Enter / Space emits "
        "mj-chart-stream-click { series, x, y, share }."
    ),
    data_shape=_TREND_SHAPE,
    options=[
        AttributeDoc(name="baseline", description="Vertical layout of the stack.", kind="enum",
                     values=["wiggle", "silhouette", "zero"], default="wiggle"),
        _curve_option("monotone"),
        _x_scale_option(),
    ],
    examples=[
        gallery_example(
            "basic", "Wiggle baseline",
            "<p>Five genres over nine years on the ThemeRiver baseline.</p>",
            _chart("streamgraph", _GENRES, "Streams by genre (millions)", attrs='baseline="wiggle" curve="monotone"'),
        ),
        gallery_example(
            "silhouette", "Silhouette, straight segments",
            "<p><code>baseline=\"silhouette\"</code> centres the stack on zero; "
            "<code>curve=\"linear\"</code> draws straight segments.</p>",
            _chart("streamgraph", _GENRES, "Streams by genre (millions)", attrs='baseline="silhouette" curve="linear"'),
        ),
        gallery_example(
            "zero", "Zero baseline",
            "<p><code>baseline=\"zero\"</code> is a bottom-aligned stacked area of dated "
            "points.</p>",
            _chart("streamgraph", _ENERGY, "Household energy use (kWh)", attrs='baseline="zero"'),
        ),
        gallery_example(
            "negative-value", "Negative value (error)",
            "<p>Software has a negative value in Q3: it is drawn as zero and "
            "<code>mj-chart-error</code> reports it (see Events).</p>",
            _chart("streamgraph", _ADJUSTMENTS, "Revenue by segment ($M)"),
        ),
        gallery_example(
            "events", "Click events",
            "<p>The script logs <code>mj-chart-stream-click</code> for a clicked value and for Enter on "
            "the last one.</p>",
            _chart("streamgraph", _GENRES, "Streams by genre (millions)", attrs='baseline="wiggle" curve="monotone"'),
            script=_events_script(["mj-chart-stream-click"], "hit"),
        ),
    ],
)

_BUMP = ChartTypeDoc(
    type_key="bump",
    title="Bump Chart",
    category="trend",
    summary="Rank-over-time chart using S-curve connectors between positions.",
    description=(
        "Each series records a rank per period (1 = best). Integer ranks spanning at most 30 places use "
        "an inverted axis with rank 1 at the top and one gridline per rank; any other values use a "
        "normal value axis with nice ticks. Consecutive ranks are joined by S-curves and a null rank "
        "(not ranked that period) breaks the line. Each series is labelled beside its own last point "
        "in the text colour with a leader in the series colour, labels nudged apart; tied dots are set "
        "slightly apart so each stays visible and clickable. A click or Enter / Space on a dot emits "
        "mj-chart-bump-click { series, x, rank }. Ranks are per period, so the x axis is categorical by "
        "default (one evenly spaced slot per season, year strings such as \"2024\" stay labels); "
        "x-scale=\"auto\" or \"time\" gives a proportional time axis."
    ),
    data_shape=_TREND_SHAPE.replace("y: number | null", "y: number | null   // the rank"),
    options=[_x_scale_option("category")],
    examples=[
        gallery_example(
            "basic", "League positions",
            "<p>Five teams over five seasons; rank 1 is at the top and every season gets its own "
            "slot (the x axis is categorical by default).</p>",
            _chart("bump", _LEAGUE, "League position by season"),
        ),
        gallery_example(
            "gaps", "Unranked periods",
            "<p>Calendo dropped out of the chart in weeks 5 and 6 (<code>null</code>): its line "
            "breaks.</p>",
            _chart("bump", _APP_STORE, "App store rank, productivity category", legend=True),
        ),
        gallery_example(
            "ties", "Tied ranks",
            "<p>Point data with tied ranks in Q1-Q3: the tied dots are set apart so each is "
            "clickable.</p>",
            _chart("bump", _TIED_RANKS, "Hackathon standings", height=240),
        ),
        gallery_example(
            "events", "Click events",
            "<p>The script logs <code>mj-chart-bump-click</code> for a clicked dot and for Enter on the "
            "last one.</p>",
            _chart("bump", _LEAGUE, "League position by season"),
            script=_events_script(["mj-chart-bump-click"], "hit"),
        ),
    ],
)


CHART_TYPES = [
    _BAR,
    _COLUMN,
    _LOLLIPOP,
    _DOTPLOT,
    _BULLET,
    _SLOPE,
    _RADAR,
    _PARALLEL,
    _LINE,
    _MULTILINE,
    _AREA,
    _STACKED_AREA,
    _AREA100,
    _STEP,
    _SPARKLINE,
    _HORIZON,
    _STREAMGRAPH,
    _BUMP,
]
