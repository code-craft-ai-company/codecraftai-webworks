"""
    02_distribution_relationship.py

    ChartTypeDoc catalog entries for the DISTRIBUTION and RELATIONSHIP chart
    categories supported by the <mj-chart> controller. Each entry documents
    the JSON its renderer reads (data_shape), the option attributes the
    renderer reads through ctx.attrs (options) and a gallery of runnable
    examples, the first of which is the canonical usage.

    Verified against the renderers in charts/core/renderers/ (histogram.js,
    boxplot.js, violin.js, strip.js, rug.js, dothistogram.js, ridgeline.js,
    qqplot.js, cdf.js, scatter.js, heatmap.js, density.js, hexbin.js,
    splom.js, beeswarm.js and the shared diststats.js).
"""

import html
import json
import math
import random

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

def _chart(type_key, data, label, attrs="", height=280, legend=False, chart_id="demo-chart"):
    """
        Markup of one <mj-chart> with inline JSON data.

        :param type_key: The chart type.
        :param data: The chart data (JSON-serialisable).
        :param label: The accessible name (plain text).
        :param attrs: Further option attributes, written as markup.
        :param height: The block size in px.
        :param legend: True to nest an <mj-chart-legend>.
        :param chart_id: The id of the chart element.

        :returns: The HTML.
    """

    attr_text = "" if attrs == "" else " " + attrs
    lines = [
        '<mj-chart id="{}" type="{}"{} label="{}" style="height:{}px">'.format(
            chart_id, type_key, attr_text, html.escape(label, quote=True), height)
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


def _normal(seed, count, mean, sd, digits=1, low=None, high=None):
    """
        Deterministic normally distributed sample values for the examples.

        :param seed: The generator seed (the same seed gives the same list).
        :param count: The number of values.
        :param mean: The mean.
        :param sd: The standard deviation.
        :param digits: The decimals kept.
        :param low: Optional lower clamp.
        :param high: Optional upper clamp.

        :returns: A list of floats (ints when digits is 0).
    """

    generator = random.Random(seed)
    values = []
    for _ in range(count):
        value = generator.gauss(mean, sd)
        if low is not None:
            value = max(low, value)
        if high is not None:
            value = min(high, value)
        value = round(value, digits)
        if digits == 0:
            value = int(value)
        values.append(value)
    return values


def _exponential(seed, count, mean, digits=1):
    """
        Deterministic exponentially distributed sample values.
    """

    generator = random.Random(seed)
    values = [round(generator.expovariate(1.0 / mean), digits) for _ in range(count)]
    return values


def _cluster_points(seed, count, cx, cy, sx, sy, rho=0.0, digits=2):
    """
        Deterministic bivariate normal points {x, y}.
    """

    generator = random.Random(seed)
    points = []
    for _ in range(count):
        a = generator.gauss(0, 1)
        b = generator.gauss(0, 1)
        x = cx + sx * a
        y = cy + sy * (rho * a + math.sqrt(1 - rho * rho) * b)
        points.append({"x": round(x, digits), "y": round(y, digits)})
    return points


# ---------------------------------------------------------------------------
# Shared option docs and shapes
# ---------------------------------------------------------------------------

_BIN_COUNT = AttributeDoc(name="bin-count", description="Number of bins (default: from `bin-method`).",
                          kind="number")
_BIN_WIDTH = AttributeDoc(name="bin-width", description="Bin width in data units; wins over `bin-count`.",
                          kind="number")
_BIN_METHOD = AttributeDoc(name="bin-method", description="Rule for the default bin count.", kind="enum",
                           values=["sturges", "scott", "fd"], default="sturges")
_BANDWIDTH = AttributeDoc(name="bandwidth",
                          description="KDE bandwidth in data units (Silverman's rule of thumb when absent).",
                          kind="number")
_FILL = AttributeDoc(name="fill", description="Shade the area under density curves and polygons.",
                     kind="enum", values=["area", "none"], default="area")
_NORMALIZE = AttributeDoc(name="normalize",
                          description=("`density`: heights are count / (n x bin width), so every series "
                                       "encloses an area of 1 and samples of different sizes compare."),
                          kind="enum", values=["density"])

_SAMPLES_SHAPE = (
    '<pre><code>{\n'
    '  series: [{\n'
    '    name: string,\n'
    '    samples?: (number | null)[],                    // raw observations\n'
    '    bins?: [{ x0: number, x1: number, count: number }]   // or pre-binned counts\n'
    '  }]\n'
    '}</code></pre>'
    '<p>Values that are not finite numbers (<code>null</code>, text) are missing data and ignored. '
    'Every <code>samples</code> series is counted into one shared set of bin edges computed from the '
    'pooled range, so overlaid and stacked series line up.</p>'
)

_GROUPS_SHAPE = (
    '<pre><code>{\n'
    '  categories?: string[],          // display order; else the order of the groups\n'
    '  series: [{\n'
    '    name: string,\n'
    '    groups: [{ category: string, samples: (number | null)[] }]\n'
    '  }]\n'
    '}</code></pre>'
    '<p>Non-finite samples are missing data and ignored. Several series are drawn side by side within '
    'each category.</p>'
)

_POINTS_SHAPE = (
    '<pre><code>{\n'
    '  meta?: { xLabel?: string, yLabel?: string },     // axis titles\n'
    '  series: [{\n'
    '    name: string,\n'
    '    shape?: "circle" | "square" | "triangle" | "diamond",\n'
    '    points: [{ x: number, y: number, size?: number, label?: string }]\n'
    '  }]\n'
    '}</code></pre>'
    '<p>Points with a missing or non-finite x or y are skipped. Marks are never moved off their data '
    'position: the axis domains widen so the largest mark fits.</p>'
)

_MATRIX_SHAPE = (
    '<pre><code>{\n'
    '  categories: string[],                          // column labels (x)\n'
    '  series: [{ name: string, values: (number | null)[] }]   // one row per series (y)\n'
    '}</code></pre>'
    '<p>One value per category; <code>null</code> or non-numeric cells are missing and left '
    'empty.</p>'
)

_SCATTER_COMMON = [
    AttributeDoc(name="trend", description="`linear`: a least-squares line per series.", kind="enum",
                 values=["linear"]),
]


def _show_labels(default):
    """
        The show-labels option; `default` is "true" for the types that label
        their points unless show-labels="false" (bubble, connected-scatter).
    """

    option = boolean_option("show-labels", "Print each point's `label` (or its value) next to it.",
                            default == "true")
    return option


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

_REACTION = {
    "series": [{"name": "Reaction time (ms)", "samples": [
        210, 225, 230, 235, 240, 242, 245, 248, 250, 252, 255, 258, 260, 263, 265,
        268, 270, 273, 275, 278, 280, 285, 290, 295, 300, 308, 315, 325, 340, 360]}],
}

_COMMUTE = {
    "series": [
        {"name": "Car", "samples": _normal(11, 60, 34, 9, 0, low=5)},
        {"name": "Transit", "samples": _normal(12, 45, 46, 11, 0, low=10)},
    ],
}

_SESSION_LENGTH = {
    "series": [
        {"name": "Web (n = 200)", "samples": _normal(21, 200, 6.5, 2.0, 1, low=0.5)},
        {"name": "App (n = 40)", "samples": _normal(22, 40, 9.0, 2.5, 1, low=0.5)},
    ],
}

_AGE_BINS = {
    "series": [{"name": "Customers", "bins": [
        {"x0": 18, "x1": 25, "count": 140}, {"x0": 25, "x1": 35, "count": 310},
        {"x0": 35, "x1": 45, "count": 265}, {"x0": 45, "x1": 55, "count": 190},
        {"x0": 55, "x1": 65, "count": 120}, {"x0": 65, "x1": 80, "count": 70}]}],
}

_TEST_SCORES = {
    "series": [
        {"name": "Group A", "samples": [48, 51, 53, 55, 56, 57, 58, 59, 60, 61,
                                        62, 63, 64, 65, 66, 67, 68, 70, 72, 75]},
        {"name": "Group B", "samples": [55, 60, 63, 65, 66, 67, 68, 69, 70, 71,
                                        72, 73, 74, 75, 76, 77, 78, 80, 83, 88]},
    ],
}

_GEYSER = {
    "series": [{"name": "Eruption interval (min)",
                "samples": _normal(31, 40, 54, 5, 0) + _normal(32, 60, 80, 6, 0)}],
}

_THREE_LINES = {
    "series": [
        {"name": "Line 1", "samples": _normal(41, 50, 10.0, 0.30, 2)},
        {"name": "Line 2", "samples": _normal(42, 50, 10.4, 0.25, 2)},
        {"name": "Line 3", "samples": _normal(43, 50, 9.8, 0.45, 2)},
    ],
}

_SCORE_BINS = {
    "series": [{"name": "Score", "bins": [
        {"x0": 0, "x1": 10, "count": 3}, {"x0": 10, "x1": 20, "count": 8},
        {"x0": 20, "x1": 30, "count": 15}, {"x0": 30, "x1": 40, "count": 22},
        {"x0": 40, "x1": 50, "count": 18}, {"x0": 50, "x1": 60, "count": 11},
        {"x0": 60, "x1": 70, "count": 6}, {"x0": 70, "x1": 80, "count": 2}]}],
}

_HEIGHTS = {
    "series": [
        {"name": "Women", "samples": _normal(51, 80, 164, 6.5, 0)},
        {"name": "Men", "samples": _normal(52, 80, 177, 7.0, 0)},
    ],
}

_YIELD = {
    "categories": ["Control", "Treatment A", "Treatment B"],
    "series": [
        {"name": "2024", "groups": [
            {"category": "Control", "samples": [52, 58, 50, 54, 63, 37, 45, 53, 54, 53, 49, 56]},
            {"category": "Treatment A", "samples": [63, 58, 76, 63, 58, 60, 60, 61, 45, 58, 67, 54]},
            {"category": "Treatment B", "samples": [58, 64, 63, 67, 48, 56, 56, 62, 65, 42, 65, 49]}]},
        {"name": "2025", "groups": [
            {"category": "Control", "samples": [59, 46, 56, 62, 54, 56, 60, 56, 54, 64, 61, 53]},
            {"category": "Treatment A", "min": 57, "q1": 60, "median": 67, "q3": 70, "max": 71,
             "outliers": [82], "n": 12},
            {"category": "Treatment B", "samples": [57, 54, 71, 67, 72, 57, 63, 56, 68, 73, 58, 72]}]},
    ],
}

_RESPONSE_BY_REGION = {
    "categories": ["eu-west", "us-east", "ap-south", "sa-east"],
    "series": [{"name": "Response time (ms)", "groups": [
        {"category": "eu-west", "samples": _normal(61, 40, 120, 18, 0) + [210, 245, None]},
        {"category": "us-east", "samples": _normal(62, 40, 105, 14, 0) + [190]},
        {"category": "ap-south", "samples": _normal(63, 40, 165, 30, 0) + [320, 355]},
        {"category": "sa-east", "samples": _normal(64, 40, 150, 22, 0) + [None, None]}]}],
}

_SALARY_STATS = {
    "categories": ["Junior", "Mid", "Senior", "Staff"],
    "series": [{"name": "Salary ($k)", "groups": [
        {"category": "Junior", "min": 52, "q1": 60, "median": 66, "q3": 72, "max": 84, "outliers": [95]},
        {"category": "Mid", "min": 70, "q1": 82, "median": 90, "q3": 98, "max": 115},
        {"category": "Senior", "min": 98, "q1": 112, "median": 124, "q3": 136, "max": 158, "outliers": [182, 190]},
        {"category": "Staff", "min": 135, "q1": 150, "median": 162, "q3": 178, "max": 205}]}],
}

_IRIS_PETALS = {
    "categories": ["Setosa", "Versicolor", "Virginica"],
    "series": [{"name": "Petal length (cm)", "groups": [
        {"category": "Setosa", "samples": [1.4, 1.4, 1.3, 1.5, 1.4, 1.7, 1.4, 1.5, 1.4, 1.5, 1.5, 1.6, 1.4,
                                           1.1, 1.2, 1.5, 1.3, 1.4, 1.7, 1.5]},
        {"category": "Versicolor", "samples": [4.7, 4.5, 4.9, 4.0, 4.6, 4.5, 4.7, 3.3, 4.6, 3.9, 3.5, 4.2,
                                               4.0, 4.7, 3.6, 4.4, 4.5, 4.1, 4.5, 3.9]},
        {"category": "Virginica", "samples": [6.0, 5.1, 5.9, 5.6, 5.8, 6.6, 4.5, 6.3, 5.8, 6.1, 5.1, 5.3,
                                              5.5, 5.0, 5.1, 5.3, 5.5, 6.7, 6.9, 5.0]}]}],
}

_DELIVERY = {
    "categories": ["Standard", "Express", "Same day"],
    "series": [{"name": "Delivery time (h)", "groups": [
        {"category": "Standard", "samples": _normal(71, 60, 52, 12, 1, low=12)},
        {"category": "Express", "samples": _normal(72, 60, 22, 5, 1, low=4)},
        {"category": "Same day", "samples": _normal(73, 30, 6, 1.5, 1, low=1) + _normal(74, 10, 11, 1, 1)}]}],
}

_SLEEP = {
    "categories": ["18-29", "30-44", "45-64", "65+"],
    "series": [{"name": "Sleep (h)", "groups": [
        {"category": "18-29", "samples": _normal(81, 50, 7.4, 1.1, 1)},
        {"category": "30-44", "samples": _normal(82, 50, 6.8, 0.9, 1)},
        {"category": "45-64", "samples": _normal(83, 50, 6.9, 1.0, 1)},
        {"category": "65+", "samples": _normal(84, 50, 7.2, 1.3, 1)}]}],
}

_WEEKLY_REVENUE = {
    "categories": ["Q1", "Q2", "Q3", "Q4"],
    "series": [{"name": "Revenue ($k)", "groups": [
        {"category": "Q1", "samples": [42, 45, 38, 50, 44, 47, 41, 49, 43, 46, 44, 45, 40]},
        {"category": "Q2", "samples": [55, 58, 52, 60, 57, 54, 59, 56, 61, 53, 57, 58, 55]},
        {"category": "Q3", "samples": [48, 51, 45, 55, 50, 47, 53, 49, 52, 46, 50, 51, 49]},
        {"category": "Q4", "samples": [65, 70, 62, 75, 68, 72, 66, 71, 64, 69, 70, 73, 67]}]}],
}

_TRIAL = {
    "categories": ["Week 4", "Week 8", "Week 12"],
    "series": [
        {"name": "Placebo", "groups": [
            {"category": "Week 4", "samples": _normal(91, 18, 2.1, 1.0, 1)},
            {"category": "Week 8", "samples": _normal(92, 18, 2.4, 1.1, 1)},
            {"category": "Week 12", "samples": _normal(93, 18, 2.6, 1.2, 1)}]},
        {"name": "Drug", "groups": [
            {"category": "Week 4", "samples": _normal(94, 18, 3.0, 1.0, 1)},
            {"category": "Week 8", "samples": _normal(95, 18, 4.2, 1.1, 1)},
            {"category": "Week 12", "samples": _normal(96, 18, 5.1, 1.3, 1)}]},
    ],
}

_LEVEL_SCORES = {
    "categories": ["Low", "Medium", "High"],
    "series": [{"name": "Score", "groups": [
        {"category": "Low", "samples": [22, 25, 28, 24, 21, 27, 23, 26, 29, 20, 24, 24, 25, 25, 25]},
        {"category": "Medium", "samples": [45, 48, 42, 50, 46, 44, 49, 47, 43, 51, 46, 46, 47, 47, 47]},
        {"category": "High", "samples": [70, 74, 68, 76, 72, 71, 75, 69, 73, 77, 72, 72, 72, 73, 74]}]}],
}

_BUILD_TIMES = {
    "categories": ["main", "release", "feature"],
    "series": [{"name": "Build time (s)", "groups": [
        {"category": "main", "samples": _normal(101, 120, 312, 28, 0)},
        {"category": "release", "samples": _normal(102, 60, 405, 35, 0)},
        {"category": "feature", "samples": _normal(103, 150, 268, 40, 0)}]}],
}

_RUG_GROUPS = {
    "series": [
        {"name": "Group A", "samples": [12, 15, 18, 20, 22, 23, 25, 27, 28, 30, 31, 33, 35, 38, 40, 43, 45,
                                        48, 50, 55]},
        {"name": "Group B", "samples": [25, 28, 30, 32, 34, 35, 37, 38, 40, 41, 43, 44, 46, 48, 50, 52, 55,
                                        58, 60, 65]},
    ],
}

_RUG_DENSE = {
    "series": [{"name": "Transaction amount ($)", "samples": _exponential(111, 400, 42, 1)}],
}

_ERRORS_PER_BUILD = {
    "series": [{"name": "Errors", "samples": [1, 1, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 4, 5, 5, 5, 5, 6, 6,
                                              6, 7, 7, 8, 9]}],
}

_GOALS = {
    "series": [
        {"name": "Home", "samples": [0, 1, 1, 2, 2, 2, 3, 1, 0, 2, 1, 4, 2, 3, 1, 1, 2, 0, 3, 2]},
        {"name": "Away", "samples": [0, 0, 1, 1, 2, 1, 0, 3, 1, 1, 0, 2, 1, 2, 0, 1, 1, 0, 2, 1]},
    ],
}

_RATING_BINS = {
    "series": [{"name": "Reviews", "bins": [
        {"x0": 0.5, "x1": 1.5, "count": 3}, {"x0": 1.5, "x1": 2.5, "count": 5},
        {"x0": 2.5, "x1": 3.5, "count": 9}, {"x0": 3.5, "x1": 4.5, "count": 14},
        {"x0": 4.5, "x1": 5.5, "count": 11}]}],
}

_PAGE_VIEWS = {
    "series": [{"name": "Pages per visit", "samples": _normal(121, 60, 6, 2, 0, low=1)}],
}

_TEMPERATURES = {
    "categories": ["2020", "2021", "2022", "2023", "2024"],
    "series": [{"name": "Daily high (°F)", "groups": [
        {"category": "2020", "samples": [62, 65, 68, 70, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 85, 87, 90, 94]},
        {"category": "2021", "samples": [60, 63, 66, 68, 70, 72, 73, 74, 75, 76, 77, 78, 79, 81, 83, 85, 88, 91, 95, 98]},
        {"category": "2022", "samples": [64, 67, 70, 72, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 85, 87, 89, 92, 96, 99]},
        {"category": "2023", "samples": [66, 69, 72, 74, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 87, 89, 91, 94, 97, 100]},
        {"category": "2024", "samples": [68, 71, 74, 76, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 89, 91, 93, 96, 99,
                                         102]}]}],
}

_RIDGE_TWO = {
    "categories": ["Mon", "Tue", "Wed", "Thu", "Fri"],
    "series": [
        {"name": "Desktop", "groups": [
            {"category": day, "samples": _normal(130 + i, 40, 14 + i * 0.5, 3, 1)}
            for i, day in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri"])]},
        {"name": "Mobile", "groups": [
            {"category": day, "samples": _normal(140 + i, 40, 19 - i * 0.4, 4, 1)}
            for i, day in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri"])]},
    ],
}

_RESIDUALS_30 = {
    "series": [{"name": "Residuals", "samples": [
        -1.38, -1.27, -1.03, -0.79, -0.44, -0.43, -0.37, -0.30, -0.18, -0.15,
        -0.13, 0.00, 0.14, 0.15, 0.28, 0.32, 0.35, 0.57, 0.57, 0.58,
        0.63, 0.76, 0.86, 1.13, 1.26, 1.40, 1.47, 2.01, 2.90, 3.40]}],
}

_TWO_SAMPLE = {
    "series": [
        {"name": "Plant A (mm)", "samples": _normal(151, 40, 25.0, 0.8, 2)},
        {"name": "Plant B (mm)", "samples": _normal(152, 40, 25.3, 1.2, 2)},
    ],
}

_WAITS = {
    "series": [{"name": "Wait between arrivals (min)", "samples": _exponential(161, 50, 4.0, 2)}],
}

_INCOMES = {
    "series": [
        {"name": "Region North", "theoretical": "lognormal",
         "samples": [round(math.exp(value), 1) for value in _normal(171, 40, 3.7, 0.45, 3)]},
    ],
}

_RESPONSE_BEFORE_AFTER = {
    "series": [
        {"name": "Before", "samples": [10, 14, 17, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 41, 45, 49, 54,
                                       60, 68, 80]},
        {"name": "After", "samples": [20, 24, 27, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48, 51, 55, 59, 64, 70,
                                      78, 90]},
    ],
}

_BATTERY_LIFE = {
    "series": [
        {"name": "Model X", "samples": _normal(181, 120, 14.0, 2.2, 1, low=4)},
        {"name": "Model Y", "samples": _normal(182, 120, 16.5, 3.4, 1, low=4)},
    ],
}

_CDF_POINTS = {
    "series": [{"name": "Population (%)", "points": [
        {"x": 0, "y": 0}, {"x": 10, "y": 8}, {"x": 20, "y": 21}, {"x": 30, "y": 38},
        {"x": 50, "y": 62}, {"x": 75, "y": 81}, {"x": 100, "y": 90}, {"x": 150, "y": 97},
        {"x": 250, "y": 100}]}],
}

_TEMP_SALES = {
    "meta": {"xLabel": "Temperature (°C)", "yLabel": "Sales (k units)"},
    "series": [
        {"name": "City A", "points": [
            {"x": 1.2, "y": 3.4}, {"x": 2.0, "y": 5.1}, {"x": 2.8, "y": 4.7}, {"x": 3.5, "y": 6.2},
            {"x": 4.1, "y": 7.0}, {"x": 4.8, "y": 6.8}, {"x": 5.5, "y": 8.3}, {"x": 6.2, "y": 9.1},
            {"x": 7.0, "y": 8.9}, {"x": 7.8, "y": 10.2}]},
        {"name": "City B", "points": [
            {"x": 1.5, "y": 2.1}, {"x": 2.3, "y": 3.8}, {"x": 3.0, "y": 4.2}, {"x": 3.8, "y": 5.5},
            {"x": 4.5, "y": 5.9}, {"x": 5.2, "y": 7.1}, {"x": 6.0, "y": 7.8}, {"x": 6.7, "y": 8.5},
            {"x": 7.5, "y": 9.0}, {"x": 8.2, "y": 9.8}]},
    ],
}

_SHAPES = {
    "meta": {"xLabel": "Sepal length (cm)", "yLabel": "Sepal width (cm)"},
    "series": [
        {"name": "Setosa", "shape": "circle", "points": [
            {"x": 5.1, "y": 3.5}, {"x": 4.9, "y": 3.0}, {"x": 4.7, "y": 3.2}, {"x": 5.0, "y": 3.6},
            {"x": 5.4, "y": 3.9}, {"x": 4.6, "y": 3.4}]},
        {"name": "Versicolor", "shape": "square", "points": [
            {"x": 7.0, "y": 3.2}, {"x": 6.4, "y": 3.2}, {"x": 6.9, "y": 3.1}, {"x": 5.5, "y": 2.3},
            {"x": 6.5, "y": 2.8}, {"x": 5.7, "y": 2.8}]},
        {"name": "Virginica", "shape": "triangle", "points": [
            {"x": 6.3, "y": 3.3}, {"x": 5.8, "y": 2.7}, {"x": 7.1, "y": 3.0}, {"x": 6.3, "y": 2.9},
            {"x": 6.5, "y": 3.0}, {"x": 7.6, "y": 3.0}]},
        {"name": "Hybrid", "shape": "diamond", "points": [
            {"x": 6.0, "y": 3.4}, {"x": 5.6, "y": 3.1}, {"x": 6.2, "y": 3.6}, {"x": 5.9, "y": 3.2}]},
    ],
}

_LABELLED_POINTS = {
    "meta": {"xLabel": "Marketing spend ($k)", "yLabel": "New customers"},
    "series": [{"name": "Campaigns", "points": [
        {"x": 12, "y": 140, "label": "Search"}, {"x": 30, "y": 210, "label": "Social"},
        {"x": 8, "y": 95, "label": "Email"}, {"x": 45, "y": 260, "label": "TV"},
        {"x": 22, "y": 60, "label": "Print"}, {"x": 18, "y": 190, "label": "Referral"},
        {"x": 35, "y": None, "label": "Podcast (no data)"}]}],
}

_COUNTRIES = {
    "meta": {"xLabel": "GDP per capita (k$)", "yLabel": "Life expectancy (years)"},
    "series": [{"name": "Countries", "points": [
        {"x": 8.2, "y": 72, "size": 1400, "label": "China"}, {"x": 10.5, "y": 74, "size": 1200, "label": "India"},
        {"x": 62.0, "y": 78, "size": 330, "label": "USA"}, {"x": 45.0, "y": 82, "size": 128, "label": "Japan"},
        {"x": 48.0, "y": 81, "size": 83, "label": "Germany"}, {"x": 28.0, "y": 76, "size": 215, "label": "Brazil"},
        {"x": 18.0, "y": 70, "size": 180, "label": "Pakistan"}, {"x": 55.0, "y": 80, "size": 68, "label": "France"}]}],
}

_PRODUCTS = {
    "meta": {"xLabel": "Price ($)", "yLabel": "Rating"},
    "series": [
        {"name": "Hardware", "points": [
            {"x": 49, "y": 4.1, "size": 1200, "label": "Mouse"}, {"x": 129, "y": 4.4, "size": 640, "label": "Keyboard"},
            {"x": 349, "y": 4.6, "size": 210, "label": "Monitor"}, {"x": 89, "y": 3.8, "size": 380, "label": "Webcam"}]},
        {"name": "Software", "points": [
            {"x": 15, "y": 4.3, "size": 2600, "label": "Notes"}, {"x": 60, "y": 4.0, "size": 900, "label": "Office"},
            {"x": 240, "y": 4.7, "size": 150, "label": "CAD"}, {"x": 99, "y": 3.6, "size": 300, "label": "Backup"}]},
    ],
}

_STARTUPS = {
    "meta": {"xLabel": "Company age (years)", "yLabel": "Employees"},
    "series": [{"name": "Startups", "points": [
        {"x": 9, "y": 420, "size": 900, "label": "Northwind"}, {"x": 7, "y": 160, "size": 40, "label": "Brightpath"},
        {"x": 5, "y": 75, "size": 6, "label": "Kiteworks"}, {"x": 3, "y": 30, "size": 1, "label": "Tinyloop"}]}],
}

_LIFECYCLE = {
    "meta": {"xLabel": "Market share (%)", "yLabel": "Revenue (M$)"},
    "series": [{"name": "Lifecycle", "points": [
        {"x": 5, "y": 12, "label": "2018"}, {"x": 12, "y": 22, "label": "2019"}, {"x": 20, "y": 35, "label": "2020"},
        {"x": 18, "y": 30, "label": "2021"}, {"x": 25, "y": 42, "label": "2022"}, {"x": 32, "y": 55, "label": "2023"},
        {"x": 38, "y": 61, "label": "2024"}]}],
}

_PHILLIPS = {
    "meta": {"xLabel": "Unemployment (%)", "yLabel": "Inflation (%)"},
    "series": [
        {"name": "Country A", "points": [
            {"x": 4.1, "y": 2.0, "label": "2019"}, {"x": 7.9, "y": 1.2, "label": "2020"},
            {"x": 5.6, "y": 4.7, "label": "2021"}, {"x": 3.8, "y": 8.0, "label": "2022"},
            {"x": 3.9, "y": 4.1, "label": "2023"}]},
        {"name": "Country B", "points": [
            {"x": 6.2, "y": 1.4, "label": "2019"}, {"x": 8.8, "y": 0.4, "label": "2020"},
            {"x": 7.4, "y": 2.6, "label": "2021"}, {"x": 6.6, "y": 9.1, "label": "2022"},
            {"x": 6.1, "y": 5.4, "label": "2023"}]},
    ],
}

_GAPPED_PATH = {
    "meta": {"xLabel": "Distance (km)", "yLabel": "Elevation (m)"},
    "series": [{"name": "Hike", "points": [
        {"x": 0, "y": 420, "label": "Start"}, {"x": 2.5, "y": 610}, {"x": 4.0, "y": 780},
        {"x": 5.5, "y": None}, {"x": 7.0, "y": 905}, {"x": 8.5, "y": 1010, "label": "Summit"},
        {"x": 11.0, "y": 640, "label": "Hut"}]}],
}

_RESIDUAL_POINTS = {
    "series": [{"name": "Residuals", "points": [
        {"x": 10, "y": 0.8}, {"x": 15, "y": -0.3}, {"x": 20, "y": 1.1}, {"x": 25, "y": -0.7},
        {"x": 30, "y": 0.4}, {"x": 35, "y": -1.2}, {"x": 40, "y": 0.2}, {"x": 45, "y": 0.9},
        {"x": 50, "y": -0.5}, {"x": 55, "y": 1.4}, {"x": 60, "y": -0.8}, {"x": 65, "y": 0.3}]}],
}


def _fan_points():
    generator = random.Random(191)
    points = []
    for index in range(40):
        fitted = 5 + index * 2.5
        points.append({"x": round(fitted, 1), "y": round(generator.gauss(0, 0.08 * fitted), 2)})
    return points


_FAN = {
    "meta": {"xLabel": "Predicted price ($k)", "yLabel": "Residual ($k)"},
    "series": [{"name": "Model v1", "points": _fan_points()}],
}

_SCALE_LOCATION = {
    "meta": {"xLabel": "Predicted price ($k)", "yLabel": "sqrt(|standardised residual|)"},
    "residual": {"transform": "scale-location"},
    "series": [{"name": "Model v1", "points": _fan_points()}],
}

_VISITORS = {
    "categories": ["Mon", "Tue", "Wed", "Thu", "Fri"],
    "series": [
        {"name": "Morning", "values": [42, 55, 38, 60, 72]},
        {"name": "Afternoon", "values": [78, 85, 70, 90, 95]},
        {"name": "Evening", "values": [55, 62, 48, 68, 80]},
        {"name": "Night", "values": [20, 18, 22, 15, 25]},
    ],
}

_INDEX = {
    "categories": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
    "series": [
        {"name": "Electronics", "values": [104, 98, 112, 120, 95, 88]},
        {"name": "Apparel", "values": [92, 97, 101, 108, 115, 110]},
        {"name": "Groceries", "values": [100, 101, 99, 102, 103, 100]},
        {"name": "Garden", "values": [70, 82, 118, 135, 140, 126]},
    ],
}

_ACTIVITY = {
    "categories": ["00", "03", "06", "09", "12", "15", "18", "21"],
    "series": [
        {"name": "Mon", "values": [2, 1, 6, 28, 34, 30, 19, 8]},
        {"name": "Tue", "values": [3, 1, 7, 31, 36, 33, 21, 9]},
        {"name": "Wed", "values": [2, 2, 8, 29, 35, None, 22, 10]},
        {"name": "Thu", "values": [4, 1, 6, 30, 33, 31, 20, 9]},
        {"name": "Fri", "values": [5, 2, 5, 25, 29, 26, 24, 15]},
        {"name": "Sat", "values": [9, 4, 3, 10, 18, 22, 25, 20]},
        {"name": "Sun", "values": [8, 5, 2, 8, 15, 18, None, 14]},
    ],
}

_BODY = {
    "categories": ["Height", "Weight", "Age", "Exercise", "Resting HR"],
    "series": [
        {"name": "Height", "values": [1.00, 0.82, 0.15, 0.05, -0.12]},
        {"name": "Weight", "values": [0.82, 1.00, 0.22, -0.41, 0.18]},
        {"name": "Age", "values": [0.15, 0.22, 1.00, -0.35, 0.27]},
        {"name": "Exercise", "values": [0.05, -0.41, -0.35, 1.00, -0.78]},
        {"name": "Resting HR", "values": [-0.12, 0.18, 0.27, -0.78, 1.00]},
    ],
}

_ASSETS = {
    "categories": ["Stocks", "Bonds", "Gold", "Real estate", "Cash", "Crypto"],
    "series": [
        {"name": "Stocks", "values": [1.00, -0.32, 0.05, 0.61, -0.08, 0.44]},
        {"name": "Bonds", "values": [-0.32, 1.00, 0.28, -0.12, 0.35, -0.21]},
        {"name": "Gold", "values": [0.05, 0.28, 1.00, 0.10, 0.02, 0.18]},
        {"name": "Real estate", "values": [0.61, -0.12, 0.10, 1.00, -0.05, 0.26]},
        {"name": "Cash", "values": [-0.08, 0.35, 0.02, -0.05, 1.00, -0.14]},
        {"name": "Crypto", "values": [0.44, -0.21, 0.18, 0.26, -0.14, 1.00]},
    ],
}

_OBSERVATIONS_2D = {
    "meta": {"xLabel": "Hours studied", "yLabel": "Exam score"},
    "series": [{"name": "Students", "points": _cluster_points(201, 120, 6, 68, 1.8, 9, rho=0.7)}],
    "density": {"resolution": 32},
}

_TWO_CLUSTERS = {
    "meta": {"xLabel": "Session length (min)", "yLabel": "Pages viewed"},
    "series": [{"name": "Sessions", "points": (
        _cluster_points(211, 90, 4, 3, 1.2, 1.0, rho=0.4) + _cluster_points(212, 70, 12, 9, 2.0, 1.8, rho=0.6))}],
    "density": {"resolution": 48, "bandwidth": "auto"},
}


def _grid(function, xs, ys):
    z = [[round(function(x, y), 3) for x in xs] for y in ys]
    grid = {"x": xs, "y": ys, "z": z}
    return grid


_GRID_X = [round(-3 + index * 0.5, 1) for index in range(13)]
_GRID_Y = [round(-2 + index * 0.5, 1) for index in range(9)]

_TERRAIN = {
    "meta": {"xLabel": "East (km)", "yLabel": "North (km)"},
    "grid": _grid(lambda x, y: 800 * math.exp(-((x - 1) ** 2 + y ** 2) / 2) +
                  450 * math.exp(-((x + 1.6) ** 2 + (y - 0.8) ** 2) / 1.2) + 100, _GRID_X, _GRID_Y),
}

_CONTOUR_POINTS = {
    "meta": {"xLabel": "Longitude offset", "yLabel": "Latitude offset"},
    "series": [{"name": "Sightings", "points": (
        _cluster_points(221, 80, 0, 0, 1.0, 0.7, rho=0.3) + _cluster_points(222, 50, 2.8, 1.8, 0.6, 0.6))}],
    "density": {"levels": 8, "resolution": 32},
}

_CONTOUR_LEVELS = {
    "meta": {"xLabel": "East (km)", "yLabel": "North (km)"},
    "grid": _TERRAIN["grid"],
    "levels": [200, 400, 600, 800],
    "fill": True,
}

_HEX_POINTS = {
    "meta": {"xLabel": "Engine size (l)", "yLabel": "Fuel use (l / 100 km)"},
    "series": [{"name": "Cars", "points": (
        _cluster_points(231, 160, 1.8, 6.0, 0.35, 0.8, rho=0.6) + _cluster_points(232, 90, 3.2, 9.5, 0.5, 1.2, rho=0.5))}],
    "hexbin": {"bins": 16},
}


def _valued_points():
    generator = random.Random(241)
    points = []
    for point in _cluster_points(242, 180, 50, 50, 22, 18, digits=1):
        distance = math.hypot(point["x"] - 60, point["y"] - 55)
        point["value"] = round(max(5, 120 - distance * 2 + generator.gauss(0, 8)), 1)
        points.append(point)
    return points


_HEX_MEAN = {
    "meta": {"xLabel": "Floor position x (m)", "yLabel": "Floor position y (m)"},
    "series": [{"name": "Purchases", "points": _valued_points()}],
    "hexbin": {"bins": 12, "stat": "mean"},
}

_IRIS_SPLOM = {
    "variables": ["SepalLen", "SepalWid", "PetalLen"],
    "series": [
        {"name": "Setosa", "points": [
            {"SepalLen": 5.1, "SepalWid": 3.5, "PetalLen": 1.4}, {"SepalLen": 4.9, "SepalWid": 3.0, "PetalLen": 1.4},
            {"SepalLen": 4.7, "SepalWid": 3.2, "PetalLen": 1.3}, {"SepalLen": 5.0, "SepalWid": 3.4, "PetalLen": 1.5},
            {"SepalLen": 5.4, "SepalWid": 3.9, "PetalLen": 1.7}, {"SepalLen": 4.6, "SepalWid": 3.4, "PetalLen": 1.4}]},
        {"name": "Versicolor", "points": [
            {"SepalLen": 7.0, "SepalWid": 3.2, "PetalLen": 4.7}, {"SepalLen": 6.4, "SepalWid": 3.2, "PetalLen": 4.5},
            {"SepalLen": 6.9, "SepalWid": 3.1, "PetalLen": 4.9}, {"SepalLen": 6.5, "SepalWid": 2.8, "PetalLen": 4.6},
            {"SepalLen": 5.7, "SepalWid": 2.8, "PetalLen": 4.5}, {"SepalLen": 6.3, "SepalWid": 3.3, "PetalLen": 4.7}]},
    ],
}

_HOUSING = {
    "variables": ["Area", "Rooms", "Age", "Price"],
    "series": [
        {"name": "City", "points": [
            {"Area": 62, "Rooms": 2, "Age": 41, "Price": 410}, {"Area": 85, "Rooms": 3, "Age": 22, "Price": 560},
            {"Area": 48, "Rooms": 1, "Age": 55, "Price": 305}, {"Area": 110, "Rooms": 4, "Age": 12, "Price": 780},
            {"Area": 74, "Rooms": 3, "Age": 30, "Price": 495}, {"Area": 95, "Rooms": 3, "Age": 8, "Price": 690}]},
        {"name": "Suburb", "points": [
            {"Area": 120, "Rooms": 4, "Age": 18, "Price": 520}, {"Area": 145, "Rooms": 5, "Age": 9, "Price": 640},
            {"Area": 98, "Rooms": 3, "Age": 35, "Price": 380}, {"Area": 160, "Rooms": 5, "Age": 4, "Price": 715},
            {"Area": 132, "Rooms": 4, "Age": 26, "Price": 505}, {"Area": 88, "Rooms": 3, "Age": 47, "Price": 330}]},
    ],
}

_COMPLETION = {
    "series": [
        {"name": "Group A", "points": [{"x": value} for value in [12, 15, 18, 20, 22, 23, 25, 27, 28, 30]]},
        {"name": "Group B", "points": [{"x": value} for value in [30, 33, 35, 37, 38, 40, 42, 45, 48, 52]]},
    ],
    "radius": 5,
    "padding": 1,
}

_VERTICAL_SWARM = {
    "series": [
        {"name": "Release 1.4", "points": [{"y": value} for value in _normal(251, 40, 220, 35, 0)]},
        {"name": "Release 1.5", "points": [{"y": value} for value in _normal(252, 40, 180, 25, 0)]},
    ],
}

_PACKAGES = {
    "series": [{"name": "Bundle size (kB)", "points": [
        {"x": 12, "label": "date-utils"}, {"x": 48, "label": "charts"}, {"x": 7, "label": "uuid"},
        {"x": 95, "label": "editor"}, {"x": 31, "label": "router"}, {"x": 22, "label": "i18n"},
        {"x": 48, "label": "forms"}, {"x": 64, "label": "grid"}, {"x": 9, "label": "clsx"},
        {"x": 31, "label": "store"}, {"x": 140, "label": "maps"}, {"x": 18, "label": "icons"}]}],
}


# ---------------------------------------------------------------------------
# DISTRIBUTION
# ---------------------------------------------------------------------------

_HISTOGRAM_OPTIONS = [
    orientation_option("vertical", "`horizontal` puts the value axis on y and grows the bars to the right."),
    _BIN_COUNT,
    _BIN_WIDTH,
    _BIN_METHOD,
    AttributeDoc(name="group", description="Several series: drawn over each other or stacked per bin.",
                 kind="enum", values=["overlay", "stack"], default="overlay"),
    _NORMALIZE,
    AttributeDoc(name="smooth", description="`kde`: draw a kernel density curve instead of bars.", kind="enum",
                 values=["kde"]),
    AttributeDoc(name="display", description="`polygon`: draw a frequency polygon instead of bars.",
                 kind="enum", values=["bar", "polygon"], default="bar"),
    _BANDWIDTH,
    _FILL,
]

_HISTOGRAM = ChartTypeDoc(
    type_key="histogram",
    title="Histogram",
    category="DISTRIBUTION",
    summary="Divides a continuous variable into bins and counts observations per bin.",
    description=(
        "Accepts raw samples or pre-computed bins {x0, x1, count}; null or non-numeric samples are "
        "missing data and are ignored. All samples series are counted into one shared set of "
        "equal-width bins (Sturges by default; bin-method=\"scott\" or \"fd\", bin-count or bin-width "
        "override it), so overlaid and stacked series line up. group=\"stack\" stacks the series per "
        "bin, normalize=\"density\" rescales each bar to count / (n x bin width) so every series has "
        "area 1, smooth=\"kde\" draws a kernel density curve instead (see the density type) and "
        "display=\"polygon\" a frequency polygon. The count axis uses whole-number ticks. Each bar is "
        "focusable; a click or Enter / Space emits mj-chart-bar-click { series, x0, x1, count }."
    ),
    data_shape=_SAMPLES_SHAPE,
    options=_HISTOGRAM_OPTIONS,
    examples=[
        gallery_example(
            "basic", "Raw samples",
            "<p>Thirty reaction times binned with Sturges' rule.</p>",
            _chart("histogram", _REACTION, "Reaction time distribution", height=260),
        ),
        gallery_example(
            "stacked", "Two series stacked",
            "<p><code>group=\"stack\"</code> with <code>bin-width=\"5\"</code>: both modes share the same "
            "bin edges, so the stacks line up.</p>",
            _chart("histogram", _COMMUTE, "Commute time by mode (min)", attrs='group="stack" bin-width="5"',
                   legend=True),
        ),
        gallery_example(
            "normalized", "Density-normalised",
            "<p>A sample of 200 and a sample of 40 compared with <code>normalize=\"density\"</code>: each "
            "encloses an area of 1.</p>",
            _chart("histogram", _SESSION_LENGTH, "Session length (min)", attrs='normalize="density"',
                   legend=True),
        ),
        gallery_example(
            "pre-binned", "Pre-binned, horizontal",
            "<p>Counts given as <code>bins</code> with unequal widths, drawn with "
            "<code>orientation=\"horizontal\"</code>.</p>",
            _chart("histogram", _AGE_BINS, "Customers by age", attrs='orientation="horizontal"'),
        ),
        gallery_example(
            "events", "Click events",
            "<p>The script logs <code>mj-chart-bar-click</code> for a clicked bin and for Enter on the "
            "last one.</p>",
            _chart("histogram", _REACTION, "Reaction time distribution", height=260),
            script=_events_script(["mj-chart-bar-click"], "bar"),
        ),
    ],
)

_DENSITY = ChartTypeDoc(
    type_key="density",
    title="Density Plot",
    category="DISTRIBUTION",
    summary="Smoothed kernel density estimate of a continuous variable.",
    description=(
        "Draws one Gaussian kernel density curve per series (Silverman's rule-of-thumb bandwidth, "
        "0.9 x min(sd, IQR / 1.34) x n^-1/5, unless bandwidth is set), extended three bandwidths past "
        "the data so the tails reach zero; the y axis is probability density. The area under each "
        "curve is filled unless fill=\"none\". Series given as pre-computed bins are drawn as a curve "
        "through the bin densities. The legend toggles a series. Each curve is focusable; a click or "
        "Enter / Space emits mj-chart-density-click { series, bandwidth }."
    ),
    data_shape=_SAMPLES_SHAPE,
    options=[
        orientation_option("vertical", "`horizontal` puts the value axis on y."),
        _BANDWIDTH,
        _FILL,
    ],
    examples=[
        gallery_example(
            "basic", "Two groups",
            "<p>Two groups of test scores as filled density curves.</p>",
            _chart("density", _TEST_SCORES, "Test scores of two groups", legend=True, height=260),
        ),
        gallery_example(
            "bandwidth", "Bandwidth",
            "<p>A bimodal sample with <code>bandwidth=\"3\"</code>; try 1 and 10 in the controls to see "
            "under- and over-smoothing.</p>",
            _chart("density", _GEYSER, "Geyser eruption intervals", attrs='bandwidth="3"', height=260),
        ),
        gallery_example(
            "lines-only", "Lines only",
            "<p>Three production lines with <code>fill=\"none\"</code>.</p>",
            _chart("density", _THREE_LINES, "Part diameter by line (mm)", attrs='fill="none"', legend=True,
                   height=260),
        ),
        gallery_example(
            "pre-binned", "From bins",
            "<p>Pre-binned counts: the curve runs through the bin densities.</p>",
            _chart("density", _SCORE_BINS, "Exam score density", height=260),
        ),
        gallery_example(
            "events", "Click events",
            "<p>The script logs <code>mj-chart-density-click</code> (with the bandwidth used) for both "
            "curves.</p>",
            _chart("density", _TEST_SCORES, "Test scores of two groups", legend=True, height=260),
            script=_events_script(["mj-chart-density-click"], "density-line"),
        ),
    ],
)

_FREQUENCY_POLYGON = ChartTypeDoc(
    type_key="frequency-polygon",
    title="Frequency Polygon",
    category="DISTRIBUTION",
    summary="Line graph connecting bin midpoints, a continuous alternative to the histogram.",
    description=(
        "Draws a line through the midpoint of each bin, closed to zero half a bin beyond the first and "
        "last bins, with a focusable dot per bin. Accepts the same samples or pre-binned data (and the "
        "same bin-count, bin-width, bin-method and normalize=\"density\" options) as the histogram; "
        "several sample series share one set of bin edges, so their polygons compare point by point. "
        "fill=\"none\" removes the shading beneath the line. A click or Enter / Space on a dot emits "
        "mj-chart-polygon-click { series, x0, x1, count }."
    ),
    data_shape=_SAMPLES_SHAPE,
    options=[
        orientation_option("vertical", "`horizontal` puts the value axis on y."),
        _BIN_COUNT,
        _BIN_WIDTH,
        _BIN_METHOD,
        _NORMALIZE,
        _FILL,
    ],
    examples=[
        gallery_example(
            "basic", "Pre-binned counts",
            "<p>Eight score bins joined at their midpoints.</p>",
            _chart("frequency-polygon", _SCORE_BINS, "Exam score frequency", height=260),
        ),
        gallery_example(
            "two-series", "Two samples",
            "<p>Two height samples on shared 4 cm bins (<code>bin-width=\"4\"</code>), lines only.</p>",
            _chart("frequency-polygon", _HEIGHTS, "Adult height (cm)", attrs='bin-width="4" fill="none"',
                   legend=True),
        ),
        gallery_example(
            "normalized", "Density-normalised",
            "<p><code>normalize=\"density\"</code> makes the large and the small sample comparable.</p>",
            _chart("frequency-polygon", _SESSION_LENGTH, "Session length (min)", attrs='normalize="density"',
                   legend=True),
        ),
        gallery_example(
            "events", "Click events",
            "<p>The script logs <code>mj-chart-polygon-click</code> for a clicked dot and for Enter on the "
            "last one.</p>",
            _chart("frequency-polygon", _SCORE_BINS, "Exam score frequency", height=260),
            script=_events_script(["mj-chart-polygon-click"], "polygon-point"),
        ),
    ],
)

_BOXPLOT = ChartTypeDoc(
    type_key="boxplot",
    title="Box Plot",
    category="DISTRIBUTION",
    summary="Five-number summary (median, quartiles, whiskers) with outlier dots, per group.",
    description=(
        "Each group supplies either raw samples (quartiles by linear interpolation, whiskers at the most "
        "extreme samples within iqr-mult x IQR of the box, the rest drawn as outliers; null samples are "
        "ignored) or pre-computed {min, q1, median, q3, max, outliers, n} stats, where min and max are "
        "the whisker ends. Several series are drawn side by side within each category band; the legend "
        "toggles a series. categories is optional (the group order is used). notched notches "
        "the box at the median's 95% interval (median +/- 1.57 x IQR / sqrt(n); needs samples or n). "
        "Each box is focusable; a click or Enter / Space emits mj-chart-boxplot-click "
        "{ series, category, stats: { count, q1, median, q3, whiskerLow, whiskerHigh, outliers, ... } }."
    ),
    data_shape=(
        '<pre><code>{\n'
        '  categories?: string[],\n'
        '  series: [{\n'
        '    name: string,\n'
        '    groups: [\n'
        '      { category: string, samples: (number | null)[] }\n'
        '      | { category: string, min: number, q1: number, median: number, q3: number, max: number,\n'
        '          outliers?: number[], n?: number }\n'
        '    ]\n'
        '  }]\n'
        '}</code></pre>'
        '<p>Pre-computed groups need numeric <code>q1</code>, <code>median</code> and <code>q3</code>; '
        '<code>n</code> enables the notch.</p>'
    ),
    options=[
        orientation_option("vertical", "`horizontal` lays the boxes on their side."),
        boolean_option("notched", "Notches each box at the 95% interval of its median."),
        AttributeDoc(name="iqr-mult", description="IQR multiplier of the whisker fences.", kind="number",
                     default="1.5"),
    ],
    examples=[
        gallery_example(
            "basic", "Two series",
            "<p>Two years per treatment; 2025 Treatment A is given as pre-computed stats.</p>",
            _chart("boxplot", _YIELD, "Crop yield by treatment", legend=True),
        ),
        gallery_example(
            "notched", "Notched",
            "<p>The bare <code>notched</code> attribute (any boolean option is on when present): boxes "
            "whose notches do not overlap have clearly different medians.</p>",
            _chart("boxplot", _YIELD, "Crop yield by treatment", attrs='notched', legend=True),
        ),
        gallery_example(
            "horizontal", "Horizontal, wider fences",
            "<p><code>orientation=\"horizontal\"</code> with <code>iqr-mult=\"3\"</code>: only extreme "
            "values remain outliers. The <code>null</code> samples are ignored.</p>",
            _chart("boxplot", _RESPONSE_BY_REGION, "Response time by region (ms)",
                   attrs='orientation="horizontal" iqr-mult="3"'),
        ),
        gallery_example(
            "precomputed", "Pre-computed stats",
            "<p>Only summary statistics, as a report would publish them.</p>",
            _chart("boxplot", _SALARY_STATS, "Salary by level ($k)"),
        ),
        gallery_example(
            "events", "Click events",
            "<p>The script logs <code>mj-chart-boxplot-click</code> (with the box statistics) for a "
            "clicked box and for Enter on the last one.</p>",
            _chart("boxplot", _YIELD, "Crop yield by treatment", legend=True),
            script=_events_script(["mj-chart-boxplot-click"], "boxplot-hit"),
        ),
    ],
)

_VIOLIN = ChartTypeDoc(
    type_key="violin",
    title="Violin Plot",
    category="DISTRIBUTION",
    summary="Mirrored kernel density estimate showing the full distribution shape per group.",
    description=(
        "Each group's kernel density (Silverman bandwidth, or bandwidth) is evaluated on its own range, "
        "three bandwidths past its data, and mirrored around the category centre; a median tick marks "
        "the middle. violin-scale=\"area\" (default) gives every violin the same area, so widths compare "
        "densities; violin-scale=\"width\" makes each as wide as its band. show-box overlays a "
        "miniature box plot, show-points the raw observations and half draws one half "
        "only; orientation=\"horizontal\" lays the violins on their side. These three options need the "
        "exact value \"true\". Each violin is focusable; a click or Enter / Space emits "
        "mj-chart-violin-click { series, category, median, bandwidth }."
    ),
    data_shape=_GROUPS_SHAPE,
    options=[
        orientation_option("vertical", "`horizontal` lays the violins on their side."),
        boolean_option("show-box", "Embeds a miniature box plot in each violin."),
        boolean_option("show-points", "Overlays the raw observations."),
        boolean_option("half", "Draws the right (or lower) half only."),
        _BANDWIDTH,
        AttributeDoc(name="violin-scale",
                     description="`area`: equal areas (widths compare densities); `width`: every violin fills its band.",
                     kind="enum", values=["area", "width"], default="area"),
    ],
    examples=[
        gallery_example(
            "basic", "With box plots",
            "<p>Three species, each violin as wide as its band and with a box plot inside.</p>",
            _chart("violin", _IRIS_PETALS, "Petal length by species", attrs='show-box="true" violin-scale="width"',
                   height=260),
        ),
        gallery_example(
            "points", "Equal areas with points",
            "<p>The default <code>violin-scale=\"area\"</code> plus <code>show-points=\"true\"</code>: the "
            "widely spread Standard group gets a tall, narrow violin of the same area as the others.</p>",
            _chart("violin", _DELIVERY, "Delivery time by service (h)", attrs='show-points="true"'),
        ),
        gallery_example(
            "half-horizontal", "Half violins, horizontal",
            "<p><code>half</code> and <code>orientation=\"horizontal\"</code>: a compact "
            "ridge-like layout.</p>",
            _chart("violin", _SLEEP, "Sleep duration by age group", attrs='half orientation="horizontal"'),
        ),
        gallery_example(
            "events", "Click events",
            "<p>The script logs <code>mj-chart-violin-click</code> for a clicked violin and for Enter on "
            "the last one.</p>",
            _chart("violin", _IRIS_PETALS, "Petal length by species", attrs='show-box="true" violin-scale="width"',
                   height=260),
            script=_events_script(["mj-chart-violin-click"], "violin-hit"),
        ),
    ],
)

_STRIP = ChartTypeDoc(
    type_key="strip",
    title="Strip Plot",
    category="DISTRIBUTION",
    summary="Individual observations scattered with jitter along a category axis.",
    description=(
        "Data shape mirrors the box plot: series[].groups[].{category, samples}. Dots are spread across "
        "the band with a deterministic jitter that stays the same on every render. jitter=\"none\" "
        "aligns the dots on the centre line, jitter=\"swarm\" places them without overlap (the swarm "
        "type), and r sets the dot radius. Several series sit side by side in each category. Null "
        "samples are ignored. The data table lists every observation. Each dot is focusable; a click "
        "or Enter / Space emits mj-chart-point-click { series, category, value }."
    ),
    data_shape=_GROUPS_SHAPE,
    options=[
        orientation_option("vertical", "`horizontal` puts the categories on rows."),
        AttributeDoc(name="jitter", description="Spread of the dots across the band.", kind="enum",
                     values=["random", "none", "swarm"], default="random"),
        AttributeDoc(name="r", description="Dot radius in px.", kind="number", default="4"),
    ],
    examples=[
        gallery_example(
            "basic", "Jittered dots",
            "<p>Weekly revenue for each quarter, jittered across the band.</p>",
            _chart("strip", _WEEKLY_REVENUE, "Weekly revenue by quarter", height=260),
        ),
        gallery_example(
            "no-jitter", "Aligned, larger dots",
            "<p><code>jitter=\"none\"</code> with <code>r=\"6\"</code>: overlapping dots darken where "
            "values repeat.</p>",
            _chart("strip", _WEEKLY_REVENUE, "Weekly revenue by quarter", attrs='jitter="none" r="6"', height=260),
        ),
        gallery_example(
            "two-series", "Two series, horizontal",
            "<p>Placebo and drug arms side by side in each week, laid out horizontally.</p>",
            _chart("strip", _TRIAL, "Symptom improvement score", attrs='orientation="horizontal"', legend=True),
        ),
        gallery_example(
            "events", "Click events",
            "<p>The script logs <code>mj-chart-point-click</code> for a clicked dot and for Enter on the "
            "last one.</p>",
            _chart("strip", _WEEKLY_REVENUE, "Weekly revenue by quarter", height=260),
            script=_events_script(["mj-chart-point-click"], "point"),
        ),
    ],
)

_SWARM = ChartTypeDoc(
    type_key="swarm",
    title="Swarm Plot",
    category="DISTRIBUTION",
    summary="Non-overlapping dot layout along a category axis, beeswarm style.",
    description=(
        "Uses the same renderer and data as the strip plot but defaults to jitter=\"swarm\": dots are "
        "visited in value order and each takes the free position nearest the centre line, so no two "
        "dots overlap and tied values sit side by side. When a band is too narrow for its densest pile "
        "the dot radius shrinks (down to 1.5 px) before any remaining dots are spread over the band. "
        "Comfortable up to a few hundred observations per group. A click or Enter / Space on a dot "
        "emits mj-chart-point-click { series, category, value }."
    ),
    data_shape=_GROUPS_SHAPE,
    options=[
        orientation_option("vertical", "`horizontal` puts the categories on rows."),
        AttributeDoc(name="jitter", description="Dot placement; `swarm` avoids every overlap.", kind="enum",
                     values=["swarm", "random", "none"], default="swarm"),
        AttributeDoc(name="r", description="Largest dot radius in px (shrinks for dense groups).", kind="number",
                     default="4"),
    ],
    examples=[
        gallery_example(
            "basic", "Swarm",
            "<p>Scores by level; the many tied values each get their own place.</p>",
            _chart("swarm", _LEVEL_SCORES, "Scores by level", height=260),
        ),
        gallery_example(
            "dense", "Dense groups",
            "<p>Up to 150 builds per branch, horizontal: the radius shrinks so the swarm fits its "
            "band.</p>",
            _chart("swarm", _BUILD_TIMES, "Build time by branch (s)", attrs='orientation="horizontal"', height=320),
        ),
        gallery_example(
            "two-series", "Two series",
            "<p>Two trial arms swarm side by side in each week.</p>",
            _chart("swarm", _TRIAL, "Symptom improvement score", legend=True, height=300),
        ),
        gallery_example(
            "events", "Click events",
            "<p>The script logs <code>mj-chart-point-click</code> for a clicked dot and for Enter on the "
            "last one.</p>",
            _chart("swarm", _LEVEL_SCORES, "Scores by level", height=260),
            script=_events_script(["mj-chart-point-click"], "point"),
        ),
    ],
)

_RUG = ChartTypeDoc(
    type_key="rug",
    title="Rug Plot",
    category="DISTRIBUTION",
    summary="Tick marks along an axis showing the exact position of each observation.",
    description=(
        "Values run along the x axis and each series is a thin strip with its name beside it (the "
        "registered default orientation is horizontal and the default height 140px); "
        "orientation=\"vertical\" puts the values on y with one column per series. Tick opacity scales "
        "with density (denser data, lower opacity) unless opacity is set; tick-height sets the tick "
        "length (default 70% of the strip). Null samples are ignored. Each tick is focusable; a click "
        "or Enter / Space emits mj-chart-rug-click { series, value }."
    ),
    data_shape=(
        '<pre><code>{ series: [{ name: string, samples: (number | null)[] }] }</code></pre>'
        '<p>One strip (or column) per series; non-finite samples are missing data.</p>'
    ),
    options=[
        orientation_option("horizontal", "`vertical` puts the values on y with one column per series."),
        AttributeDoc(name="tick-height", description="Tick length in px (default 70% of the strip).", kind="number"),
        AttributeDoc(name="opacity", description="Opacity of every tick, 0-1 (default: lower for denser data).",
                     kind="number"),
    ],
    examples=[
        gallery_example(
            "basic", "Two strips",
            "<p>Two groups of observations, one strip each.</p>",
            _chart("rug", _RUG_GROUPS, "Observations of two groups", height=140),
        ),
        gallery_example(
            "vertical", "Vertical",
            "<p><code>orientation=\"vertical\"</code>: the values run up the y axis, one column per "
            "series.</p>",
            _chart("rug", _RUG_GROUPS, "Observations of two groups", attrs='orientation="vertical"', height=280),
        ),
        gallery_example(
            "dense", "Dense data",
            "<p>400 skewed transaction amounts: the ticks become translucent so clusters read as "
            "darker. Set <code>opacity</code> to override.</p>",
            _chart("rug", _RUG_DENSE, "Transaction amounts", attrs='tick-height="40"', height=120),
        ),
        gallery_example(
            "events", "Click events",
            "<p>The script logs <code>mj-chart-rug-click</code> for a clicked tick and for Enter on the "
            "last one.</p>",
            _chart("rug", _RUG_GROUPS, "Observations of two groups", height=140),
            script=_events_script(["mj-chart-rug-click"], "rug-tick"),
        ),
    ],
)

_DOT_HISTOGRAM = ChartTypeDoc(
    type_key="dot-histogram",
    title="Dot Histogram",
    category="DISTRIBUTION",
    summary="Wilkinson dot plot: stacked dots instead of bars to show individual counts.",
    description=(
        "One dot per observation, stacked per bin; dot k sits on count k + 0.5 of the count axis so "
        "stacks always agree with the gridlines, and the radius is the largest that fits the bin and "
        "one count unit (dot-size scales it, 0-1). It switches to bars, with a note saying so, when a "
        "series has more than dot-limit observations (default 200) or the dots would be too small. "
        "bin-count / bin-width control the shared bins; several series sit side by side within each "
        "bin unless group=\"overlay\". type=\"dothistogram\" is an alias. Each stack is focusable; a "
        "click or Enter / Space emits mj-chart-dot-click { series, x0, x1, count }."
    ),
    data_shape=_SAMPLES_SHAPE,
    options=[
        orientation_option("vertical", "`horizontal` stacks the dots to the right."),
        AttributeDoc(name="bin-count", description="Number of bins (default Sturges).", kind="number"),
        _BIN_WIDTH,
        AttributeDoc(name="dot-size", description="Dot diameter as a share (0-1] of the largest that fits.",
                     kind="number", default="1"),
        AttributeDoc(name="group", description="`overlay`: series share each bin; default side by side.",
                     kind="enum", values=["overlay"]),
        AttributeDoc(name="dot-limit", description="Most dots of any series before bars are drawn instead.",
                     kind="number", default="200"),
    ],
    examples=[
        gallery_example(
            "basic", "One dot per build",
            "<p>Errors per build, one bin per whole number (<code>bin-width=\"1\"</code>).</p>",
            _chart("dot-histogram", _ERRORS_PER_BUILD, "Errors per build", attrs='bin-width="1"', height=260),
        ),
        gallery_example(
            "two-series", "Two series side by side",
            "<p>Goals per match, home and away dots side by side in each bin.</p>",
            _chart("dot-histogram", _GOALS, "Goals per match", attrs='bin-width="1"', legend=True),
        ),
        gallery_example(
            "pre-binned", "Pre-binned, smaller dots",
            "<p>Review counts given as bins, with <code>dot-size=\"0.7\"</code>.</p>",
            _chart("dot-histogram", _RATING_BINS, "Star ratings", attrs='dot-size="0.7"'),
        ),
        gallery_example(
            "bars-fallback", "Too many dots",
            "<p><code>dot-limit=\"40\"</code> with 60 observations: the chart draws bars and says so.</p>",
            _chart("dot-histogram", _PAGE_VIEWS, "Pages per visit", attrs='dot-limit="40" bin-width="1"'),
        ),
        gallery_example(
            "events", "Click events",
            "<p>The script logs <code>mj-chart-dot-click</code> for a clicked stack and for Enter on the "
            "last one.</p>",
            _chart("dot-histogram", _ERRORS_PER_BUILD, "Errors per build", attrs='bin-width="1"', height=260),
            script=_events_script(["mj-chart-dot-click"], "dot-stack"),
        ),
    ],
)

_RIDGELINE = ChartTypeDoc(
    type_key="ridgeline",
    title="Ridgeline Plot",
    category="DISTRIBUTION",
    summary="Vertically offset density curves, one per group, revealing distribution shifts.",
    description=(
        "The categories list controls the row order (top to bottom); headroom is reserved so the top "
        "ridge is never cut off. With one series every row has its own colour and there is no legend; "
        "with several series each row overlays one curve per series, coloured by series. overlap sets "
        "how far a full-height ridge reaches into the row above (default 0.5, 0 for none), "
        "mode=\"histogram\" draws stepped histogram ridges (bin-count, default Sturges of the largest "
        "group) and bandwidth overrides the KDE bandwidth. Each ridge is focusable; a click or Enter / "
        "Space emits mj-chart-ridge-click { series, category, median }."
    ),
    data_shape=_GROUPS_SHAPE.replace(
        "Several series are drawn side by side within each category.",
        "Each category is one row; several series overlay their curves in each row."),
    options=[
        AttributeDoc(name="mode", description="Smooth density ridges or stepped histogram ridges.", kind="enum",
                     values=["density", "histogram"], default="density"),
        AttributeDoc(name="overlap", description="How far a full-height ridge reaches into the row above, in rows.",
                     kind="number", default="0.5"),
        _BANDWIDTH,
        AttributeDoc(name="bin-count", description="Bins of histogram mode (default Sturges of the largest group).",
                     kind="number"),
    ],
    examples=[
        gallery_example(
            "basic", "Five years",
            "<p>Daily highs per year; each row has its own colour.</p>",
            _chart("ridgeline", _TEMPERATURES, "Daily high temperature by year", height=300),
        ),
        gallery_example(
            "histogram", "Histogram ridges",
            "<p><code>mode=\"histogram\"</code> with <code>bin-count=\"8\"</code> and no overlap "
            "(<code>overlap=\"0\"</code>).</p>",
            _chart("ridgeline", _TEMPERATURES, "Daily high temperature by year",
                   attrs='mode="histogram" bin-count="8" overlap="0"', height=300),
        ),
        gallery_example(
            "two-series", "Two series per row",
            "<p>Desktop and mobile session lengths overlaid in each weekday row, with more overlap "
            "(<code>overlap=\"1\"</code>).</p>",
            _chart("ridgeline", _RIDGE_TWO, "Session length by weekday (min)", attrs='overlap="1"',
                   legend=True, height=320),
        ),
        gallery_example(
            "events", "Click events",
            "<p>The script logs <code>mj-chart-ridge-click</code> (with the row median) for a clicked "
            "ridge and for Enter on the last one.</p>",
            _chart("ridgeline", _TEMPERATURES, "Daily high temperature by year", height=300),
            script=_events_script(["mj-chart-ridge-click"], "ridge"),
        ),
    ],
)

_QQ = ChartTypeDoc(
    type_key="qq",
    title="Q-Q Plot",
    category="DISTRIBUTION",
    summary="Quantile-quantile plot comparing sample quantiles to a theoretical distribution.",
    description=(
        "Plots each sample's order statistics against the quantiles of a distribution fitted to it, at "
        "plotting positions (i - 0.5) / n: normal (default; mean and sd), uniform (min / max), "
        "exponential (mean) or lognormal (mean / sd of log x, positive samples only), chosen by the "
        "theoretical attribute or a series' own theoretical field. With exactly two sample series and "
        "no theoretical attribute it compares the two samples (series 0 on x, series 1 on y). A dashed "
        "y = x line marks agreement; reference=\"quartile\" draws the line through the quartile pairs "
        "instead, which is robust to outliers. type=\"qqplot\" is an alias. Each point is focusable; a "
        "click or Enter / Space emits mj-chart-qq-click { series, theoretical, observed }."
    ),
    data_shape=(
        '<pre><code>{\n'
        '  series: [{\n'
        '    name: string,\n'
        '    samples: (number | null)[],\n'
        '    theoretical?: "normal" | "uniform" | "exponential" | "lognormal"\n'
        '  }]\n'
        '}</code></pre>'
        '<p>Two series and no <code>theoretical</code> attribute: a two-sample Q-Q plot. Non-finite '
        'samples are ignored.</p>'
    ),
    options=[
        AttributeDoc(name="theoretical",
                     description=("Reference distribution for every series. When absent: a series' own "
                                  "`theoretical`, else normal, or a two-sample plot for two series."),
                     kind="enum", values=["normal", "uniform", "exponential", "lognormal"]),
        AttributeDoc(name="reference", description="Reference line: y = x, or through the quartile pairs.",
                     kind="enum", values=["identity", "quartile"], default="identity"),
    ],
    examples=[
        gallery_example(
            "basic", "Normal Q-Q",
            "<p>Thirty model residuals against the normal: the right tail bends away from the line.</p>",
            _chart("qq", _RESIDUALS_30, "Normal Q-Q plot of model residuals", height=300),
        ),
        gallery_example(
            "two-sample", "Two samples",
            "<p>Two plants' parts compared directly: Plant B's wider spread tilts the points.</p>",
            _chart("qq", _TWO_SAMPLE, "Part length, plant A against plant B", height=300),
        ),
        gallery_example(
            "exponential", "Exponential, quartile line",
            "<p>Arrival gaps against an exponential with <code>reference=\"quartile\"</code>.</p>",
            _chart("qq", _WAITS, "Exponential Q-Q plot of waiting times",
                   attrs='theoretical="exponential" reference="quartile"', height=300),
        ),
        gallery_example(
            "lognormal", "Per-series distribution",
            "<p>The series asks for a lognormal fit in its own <code>theoretical</code> field.</p>",
            _chart("qq", _INCOMES, "Lognormal Q-Q plot of household income ($k)", height=300),
        ),
        gallery_example(
            "events", "Click events",
            "<p>The script logs <code>mj-chart-qq-click</code> for a clicked point and for Enter on the "
            "last one.</p>",
            _chart("qq", _RESIDUALS_30, "Normal Q-Q plot of model residuals", height=300),
            script=_events_script(["mj-chart-qq-click"], "qq-point"),
        ),
    ],
)

_CDF = ChartTypeDoc(
    type_key="cdf",
    title="CDF",
    category="DISTRIBUTION",
    summary="Empirical cumulative distribution function: share of data at or below each value.",
    description=(
        "Renders the empirical CDF as a right-continuous step function: 0 left of the smallest value, "
        "a riser of k / n at each distinct value (k tied samples) and 1 to the right edge. "
        "smooth draws a monotone curve through the step corners, direction=\"descending\" the "
        "survival function 1 - F, scale=\"percent\" a 0-100 axis, and markers controls the per-value "
        "markers (auto: shown up to 60 distinct values). Pre-computed curves can be given as points "
        "{x, y} with y in [0, 1] or in percent. orientation=\"horizontal\" puts the cumulative share on "
        "x. The markers are the focusable marks (a click or Enter / Space emits mj-chart-cdf-point-click "
        "{ series, x, y }); without markers each curve is one, emitting mj-chart-cdf-click { series }."
    ),
    data_shape=(
        '<pre><code>{\n'
        '  series: [{\n'
        '    name: string,\n'
        '    samples?: (number | null)[],          // raw observations\n'
        '    points?: [{ x: number, y: number }]   // or a pre-computed curve\n'
        '  }]\n'
        '}</code></pre>'
        '<p>Pre-computed <code>y</code> values are cumulative shares in [0, 1] or percent.</p>'
    ),
    options=[
        orientation_option("vertical", "`horizontal` puts the cumulative share on x."),
        AttributeDoc(name="direction", description="`descending` plots the survival function 1 - F.", kind="enum",
                     values=["ascending", "descending"], default="ascending"),
        AttributeDoc(name="scale", description="Cumulative axis as 0-1 or as percent.", kind="enum",
                     values=["probability", "percent"], default="probability"),
        boolean_option("smooth", "A monotone curve through the step corners."),
        AttributeDoc(name="markers", description="Per-value markers; `auto` shows them up to 60 distinct values, a bare `markers` is `true`.",
                     kind="enum", values=["auto", "true", "false"], default="auto"),
    ],
    examples=[
        gallery_example(
            "basic", "Before and after",
            "<p>Two response-time samples; the After curve lies to the right.</p>",
            _chart("cdf", _RESPONSE_BEFORE_AFTER, "Response time before and after the fix", legend=True),
        ),
        gallery_example(
            "survival", "Survival, percent",
            "<p><code>direction=\"descending\"</code> and <code>scale=\"percent\"</code>: the share of "
            "batteries still running after each number of hours. 120 values per series, so no "
            "markers.</p>",
            _chart("cdf", _BATTERY_LIFE, "Battery life (h)", attrs='direction="descending" scale="percent"',
                   legend=True),
        ),
        gallery_example(
            "smooth", "Smooth curve",
            "<p><code>smooth=\"true\"</code> with markers forced on (<code>markers=\"true\"</code>).</p>",
            _chart("cdf", _RESPONSE_BEFORE_AFTER, "Response time before and after the fix",
                   attrs='smooth="true" markers="true"', legend=True),
        ),
        gallery_example(
            "pre-computed", "Pre-computed points",
            "<p>A published cumulative curve given as points with y in percent.</p>",
            _chart("cdf", _CDF_POINTS, "Population by distance to the nearest hospital (km)"),
        ),
        gallery_example(
            "events", "Click events",
            "<p>With markers each marker is a mark (<code>mj-chart-cdf-point-click</code>); the second chart "
            "has <code>markers=\"false\"</code>, so its curves are the marks (<code>mj-chart-cdf-click</code>). "
            "The script activates one of each.</p>",
            _chart("cdf", _RESPONSE_BEFORE_AFTER, "Response time before and after the fix", legend=True,
                   height=240) + "\n" +
            _chart("cdf", _RESPONSE_BEFORE_AFTER, "Response time, curves only", attrs='markers="false"',
                   height=240, chart_id="curves-chart"),
            script=(
                'const chart = document.getElementById("demo-chart")\n'
                'const curves = document.getElementById("curves-chart")\n'
                'for (const target of [chart, curves]) {\n'
                '  for (const name of ["mj-chart-cdf-click", "mj-chart-cdf-point-click"]) {\n'
                '    target.addEventListener(name, (event) => mjSandbox.log("listener: " + name, event.detail))\n'
                '  }\n'
                '}\n'
                '\n'
                'await Promise.all([chart.redraw(), curves.redraw()])\n'
                'const marker = chart.shadowRoot.querySelector(\'[part~="cdf-point"][tabindex]\')\n'
                'marker.focus()\n'
                'marker.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true }))\n'
                'const curve = curves.shadowRoot.querySelector(\'[part~="cdf-line"][tabindex]\')\n'
                'curve.dispatchEvent(new MouseEvent("click", { bubbles: true }))\n'
            ),
        ),
    ],
)


# ---------------------------------------------------------------------------
# RELATIONSHIP
# ---------------------------------------------------------------------------

_SCATTER = ChartTypeDoc(
    type_key="scatter",
    title="Scatter Plot",
    category="RELATIONSHIP",
    summary="Individual observations plotted at (x, y) coordinates to reveal correlations.",
    description=(
        "Each series provides {x, y} points; points with a missing coordinate are skipped. With several "
        "series each gets its own mark shape as well as its colour (the series shape field picks one: "
        "circle, square, triangle or diamond). trend=\"linear\" adds a least-squares line per series, "
        "meta.xLabel / meta.yLabel title the axes and show-labels=\"true\" prints point labels. The "
        "bubble, connected and residual attributes (=\"true\") switch the drawing to the bubble, "
        "connected-scatter and residual forms. Each point is focusable; a click or Enter / Space emits "
        "mj-chart-point-click { series, x, y, size?, label? }."
    ),
    data_shape=_POINTS_SHAPE,
    options=_SCATTER_COMMON + [
        _show_labels("false"),
        boolean_option("bubble", "Size the marks by `size`, as the bubble type does."),
        boolean_option("connected", "Join the points in data order, as connected-scatter does."),
        boolean_option("residual", "Centre y on 0 with a zero line, as the residual type does."),
    ],
    examples=[
        gallery_example(
            "basic", "Two series with trends",
            "<p>Two cities with a least-squares trend line each.</p>",
            _chart("scatter", _TEMP_SALES, "Temperature versus sales", attrs='trend="linear"', legend=True),
        ),
        gallery_example(
            "shapes", "Mark shapes",
            "<p>Four groups, each with the mark shape named in its <code>shape</code> field.</p>",
            _chart("scatter", _SHAPES, "Sepal measurements by species", legend=True, height=300),
        ),
        gallery_example(
            "labels", "Point labels and a missing value",
            "<p><code>show-labels=\"true\"</code>; the Podcast point has <code>y: null</code> and is "
            "skipped.</p>",
            _chart("scatter", _LABELLED_POINTS, "Campaign spend versus new customers", attrs='show-labels="true"'),
        ),
        gallery_example(
            "events", "Click events",
            "<p>The script logs <code>mj-chart-point-click</code> for a clicked point and for Enter on the "
            "last one.</p>",
            _chart("scatter", _TEMP_SALES, "Temperature versus sales", attrs='trend="linear"', legend=True),
            script=_events_script(["mj-chart-point-click"], "point"),
        ),
    ],
)

_BUBBLE = ChartTypeDoc(
    type_key="bubble",
    title="Bubble Chart",
    category="RELATIONSHIP",
    summary="Scatter plot with a third dimension encoded as circle area.",
    description=(
        "Each point carries a size field; bubble AREA is proportional to it (radius = max-radius x "
        "sqrt(size / largest size)). max-radius (default 40 px) is capped at 12% of the smaller chart "
        "dimension so small charts stay legible, and min-radius (default 3 px) is only a visibility "
        "floor. Bubbles are never moved off their data position: the axes are widened so the largest "
        "bubble fits. Larger bubbles are drawn first; labels are shown by default "
        "(show-labels=\"false\" hides them). A click or Enter / Space on a bubble emits "
        "mj-chart-point-click { series, x, y, size, label? }."
    ),
    data_shape=_POINTS_SHAPE.replace("size?: number", "size: number"),
    options=[
        AttributeDoc(name="min-radius", description="Smallest bubble radius in px (a visibility floor).",
                     kind="number", default="3"),
        AttributeDoc(name="max-radius",
                     description="Radius of the largest bubble in px (capped at 12% of the smaller chart side).",
                     kind="number", default="40"),
        _show_labels("true"),
    ] + _SCATTER_COMMON,
    examples=[
        gallery_example(
            "basic", "Countries",
            "<p>Population as bubble area against income and life expectancy.</p>",
            _chart("bubble", _COUNTRIES, "Population, income and life expectancy", height=300),
        ),
        gallery_example(
            "two-series", "Two series",
            "<p>Two product lines; <code>max-radius=\"28\"</code> keeps the bubbles apart.</p>",
            _chart("bubble", _PRODUCTS, "Price, rating and units sold", attrs='max-radius="28"', legend=True,
                   height=300),
        ),
        gallery_example(
            "min-radius", "Visibility floor",
            "<p>Sizes from 1 to 900: with <code>min-radius=\"6\"</code> the tiny values stay "
            "visible.</p>",
            _chart("bubble", _STARTUPS, "Startups by age, staff and funding", attrs='min-radius="6"', height=280),
        ),
        gallery_example(
            "events", "Click events",
            "<p>The script logs <code>mj-chart-point-click</code> (with size and label) for a clicked "
            "bubble and for Enter on the last one.</p>",
            _chart("bubble", _COUNTRIES, "Population, income and life expectancy", height=300),
            script=_events_script(["mj-chart-point-click"], "point"),
        ),
    ],
)

_CONNECTED_SCATTER = ChartTypeDoc(
    type_key="connected-scatter",
    title="Connected Scatter",
    category="RELATIONSHIP",
    summary="Scatter points joined by lines in data order, for time-path trajectories.",
    description=(
        "Uses the same data shape as the scatter plot. Points are connected in the order they appear "
        "in the array (not sorted by x); a point with a missing coordinate breaks the path. Labels are "
        "drawn next to each point by default (show-labels=\"false\" hides them), so the label is "
        "usually the period. Each series is its own path and colour. A click or Enter / Space on a "
        "point emits mj-chart-point-click { series, x, y, label? }."
    ),
    data_shape=_POINTS_SHAPE,
    options=[_show_labels("true")] + _SCATTER_COMMON,
    examples=[
        gallery_example(
            "basic", "Trajectory",
            "<p>A product's share and revenue year by year; 2021 doubles back.</p>",
            _chart("connected-scatter", _LIFECYCLE, "Product lifecycle, 2018 to 2024"),
        ),
        gallery_example(
            "two-series", "Two paths",
            "<p>Unemployment against inflation for two countries.</p>",
            _chart("connected-scatter", _PHILLIPS, "Unemployment and inflation, 2019 to 2023", legend=True,
                   height=300),
        ),
        gallery_example(
            "gap", "A missing point",
            "<p>The 5.5 km reading is <code>null</code>: the path breaks there.</p>",
            _chart("connected-scatter", _GAPPED_PATH, "Hike elevation profile"),
        ),
        gallery_example(
            "events", "Click events",
            "<p>The script logs <code>mj-chart-point-click</code> for a clicked point and for Enter on the "
            "last one.</p>",
            _chart("connected-scatter", _LIFECYCLE, "Product lifecycle, 2018 to 2024"),
            script=_events_script(["mj-chart-point-click"], "point"),
        ),
    ],
)

_RESIDUAL = ChartTypeDoc(
    type_key="residual",
    title="Residual Plot",
    category="RELATIONSHIP",
    summary="Scatter with a y = 0 reference line for visualizing model residuals.",
    description=(
        "Same data shape as the scatter plot: x is the fitted value, y the residual. The y axis is "
        "symmetric around 0 so the dashed zero-reference line is always visible, and the axes default "
        "to 'Fitted values' and 'Residuals' (meta.xLabel / meta.yLabel override them). "
        "residual.transform = \"scale-location\" plots sqrt(|residual|) instead. Patterns in the "
        "residuals (trends, fan shapes) indicate model mis-specification. A click or Enter / Space on a "
        "point emits mj-chart-point-click { series, x, y }."
    ),
    data_shape=(
        _POINTS_SHAPE +
        '<p><code>residual.transform</code>: <code>"scale-location"</code> plots '
        '<code>sqrt(|y|)</code>.</p>'
    ),
    options=[_show_labels("false")] + _SCATTER_COMMON,
    examples=[
        gallery_example(
            "basic", "Residuals",
            "<p>Residuals scattered evenly around zero: a well-specified model.</p>",
            _chart("residual", _RESIDUAL_POINTS, "Residuals versus fitted values"),
        ),
        gallery_example(
            "fan", "Fan shape",
            "<p>The spread grows with the fitted value (heteroscedasticity); axis titles from "
            "<code>meta</code>.</p>",
            _chart("residual", _FAN, "Residuals of the price model", height=300),
        ),
        gallery_example(
            "scale-location", "Scale-location",
            "<p><code>residual.transform = \"scale-location\"</code>: the rising trend of "
            "sqrt(|residual|) shows the same problem.</p>",
            _chart("residual", _SCALE_LOCATION, "Scale-location plot of the price model",
                   attrs='trend="linear"', height=300),
        ),
        gallery_example(
            "events", "Click events",
            "<p>The script logs <code>mj-chart-point-click</code> for a clicked point and for Enter on the "
            "last one.</p>",
            _chart("residual", _RESIDUAL_POINTS, "Residuals versus fitted values"),
            script=_events_script(["mj-chart-point-click"], "point"),
        ),
    ],
)

_CELL_OPTIONS = [
    _show_labels("false"),
    AttributeDoc(name="gap", description="Space between cells in px.", kind="number", default="1"),
    AttributeDoc(name="corner-radius", description="Cell corner radius in px.", kind="number", default="2"),
    AttributeDoc(name="triangle", description="Show the whole grid or one triangle (square matrices).",
                 kind="enum", values=["full", "upper", "lower"], default="full"),
    AttributeDoc(name="mark", description="`circle`: a circle whose AREA encodes the absolute value.",
                 kind="enum", values=["rect", "circle"], default="rect"),
]

_HEATMAP = ChartTypeDoc(
    type_key="heatmap",
    title="Heatmap",
    category="RELATIONSHIP",
    summary="Grid of colored cells encoding a numeric value at each (row, column) intersection.",
    description=(
        "categories defines the column labels; each series is a row with one value per category (null "
        "leaves the cell empty). Cells use a sequential ramp over the value range, mixed from the chart "
        "palette and the surface so it follows the theme, read back by the colour bar on the right. "
        "scale=\"diverging\" switches to a two-hue ramp centred on midpoint (default 0) that reaches "
        "full colour at the largest |value - midpoint|; value-source=\"correlation\" treats the data "
        "as a correlation matrix. show-labels=\"true\" prints values inside cells, gap and "
        "corner-radius shape the cells, mark=\"circle\" encodes |value| as circle area and triangle "
        "shows half a square matrix. Long column labels are rotated. Each cell is focusable; a click or "
        "Enter / Space emits mj-chart-cell-click { row, col, value }."
    ),
    data_shape=_MATRIX_SHAPE,
    options=[
        AttributeDoc(name="scale", description="Colour ramp: one hue, or two hues around `midpoint`.", kind="enum",
                     values=["sequential", "diverging"], default="sequential"),
        AttributeDoc(name="midpoint", description="Centre of the diverging scale.", kind="number", default="0"),
        AttributeDoc(name="value-source", description="`correlation`: draw as a correlation matrix (fixed [-1, 1]).",
                     kind="enum", values=["correlation"]),
    ] + _CELL_OPTIONS,
    examples=[
        gallery_example(
            "basic", "Labelled cells",
            "<p>Visitors by day and time of day, values printed in the cells.</p>",
            _chart("heatmap", _VISITORS, "Store visitors by day and time", attrs='show-labels="true"', height=260),
        ),
        gallery_example(
            "diverging", "Diverging around 100",
            "<p>A sales index: <code>scale=\"diverging\"</code> with <code>midpoint=\"100\"</code> shows "
            "months above and below the baseline in two hues.</p>",
            _chart("heatmap", _INDEX, "Sales index by department (100 = last year)",
                   attrs='scale="diverging" midpoint="100" show-labels="true"', height=260),
        ),
        gallery_example(
            "missing-cells", "Missing cells, wider gaps",
            "<p>Two hours have no data (<code>null</code>) and stay empty; <code>gap=\"3\"</code> and "
            "<code>corner-radius=\"4\"</code>.</p>",
            _chart("heatmap", _ACTIVITY, "Commits by weekday and hour", attrs='gap="3" corner-radius="4"',
                   height=300),
        ),
        gallery_example(
            "circles", "Circle marks",
            "<p><code>mark=\"circle\"</code>: circle area encodes the value.</p>",
            _chart("heatmap", _VISITORS, "Store visitors by day and time", attrs='mark="circle"', height=260),
        ),
        gallery_example(
            "events", "Click events",
            "<p>The script logs <code>mj-chart-cell-click</code> for a clicked cell and for Enter on the "
            "last one.</p>",
            _chart("heatmap", _VISITORS, "Store visitors by day and time", attrs='show-labels="true"', height=260),
            script=_events_script(["mj-chart-cell-click"], "cell"),
        ),
    ],
)

_CORRELATION_MATRIX = ChartTypeDoc(
    type_key="correlation-matrix",
    title="Correlation Matrix",
    category="RELATIONSHIP",
    summary="Symmetric heatmap of pairwise correlation coefficients on a diverging scale.",
    description=(
        "The heatmap renderer with a diverging ramp fixed to [-1, 1]: one hue for positive and another "
        "for negative correlations, deeper colour for stronger correlation on both sides, neutral at "
        "zero, with a colour bar. Values should be in [-1, 1]; scale and midpoint are ignored. "
        "triangle=\"upper\" or \"lower\" shows half the matrix, mark=\"circle\" encodes |r| as circle "
        "area and show-labels=\"true\" prints the coefficients. A click or Enter / Space on a cell emits "
        "mj-chart-cell-click { row, col, value }."
    ),
    data_shape=_MATRIX_SHAPE.replace(
        "One value per category;",
        "A square matrix: rows and columns name the same variables, values in [-1, 1];"),
    options=_CELL_OPTIONS,
    examples=[
        gallery_example(
            "basic", "Labelled matrix",
            "<p>Five body measures with their coefficients printed.</p>",
            _chart("correlation-matrix", _BODY, "Correlation of body measures", attrs='show-labels="true"',
                   height=300),
        ),
        gallery_example(
            "lower-triangle", "Lower triangle",
            "<p><code>triangle=\"lower\"</code> drops the redundant half of a symmetric matrix.</p>",
            _chart("correlation-matrix", _ASSETS, "Correlation of asset returns",
                   attrs='triangle="lower" show-labels="true"', height=320),
        ),
        gallery_example(
            "circles", "Circle marks",
            "<p><code>mark=\"circle\"</code>: the circle area shows the strength, the colour the "
            "sign.</p>",
            _chart("correlation-matrix", _ASSETS, "Correlation of asset returns", attrs='mark="circle"', height=320),
        ),
        gallery_example(
            "events", "Click events",
            "<p>The script logs <code>mj-chart-cell-click</code> for a clicked cell and for Enter on the "
            "last one.</p>",
            _chart("correlation-matrix", _BODY, "Correlation of body measures", attrs='show-labels="true"',
                   height=300),
            script=_events_script(["mj-chart-cell-click"], "cell"),
        ),
    ],
)

_DENSITY_SHAPE = (
    '<pre><code>{\n'
    '  meta?: { xLabel?: string, yLabel?: string },\n'
    '  series?: [{ name: string, points: [{ x: number, y: number }] }],   // raw points, or\n'
    '  grid?: { x: number[], y: number[], z: (number | null)[][] },       // a computed surface\n'
    '  density?: {\n'
    '    style?: "fill" | "contour" | "both",   // the density-style attribute wins over it\n'
    '    levels?: number | number[],            // iso-level count (3-20, default 8) or values\n'
    '    resolution?: number,                   // KDE grid nodes per axis (8-128, default 32)\n'
    '    bandwidth?: "auto" | number\n'
    '  },\n'
    '  levels?: number[],                       // iso-level values (same as density.levels)\n'
    '  fill?: true                              // contour type: also fill the surface\n'
    '}</code></pre>'
    '<p><code>z[i][j]</code> is the value at <code>(x[j], y[i])</code>; non-finite z values are holes. '
    'Raw points get a bivariate Gaussian KDE (sigma x n^-1/6 per axis by default); the surface is a '
    'true density.</p>'
)

_DENSITY_OPTIONS_DOC = [
    AttributeDoc(name="density-style",
                 description="Surface, iso-lines or both; overrides `density.style` in the data.",
                 kind="enum", values=["fill", "contour", "both"]),
    AttributeDoc(name="max-points", description="Points used for the KDE (larger sets are thinned evenly).",
                 kind="number", default="2000"),
]

_DENSITY_2D = ChartTypeDoc(
    type_key="density-2d",
    title="2D Density",
    category="RELATIONSHIP",
    summary="2D kernel density estimate visualized as a filled heat-surface.",
    description=(
        "Accepts raw points for a bivariate Gaussian KDE or a pre-computed grid {x, y, z}. The surface "
        "is drawn edge to edge inside the plot with a colour bar; density.resolution sets the grid "
        "nodes per axis and density.bandwidth the kernel. density-style (which wins over density.style "
        "in the data) picks fill (default for this type), contour or both. The KDE is cached per data "
        "object and reused on resize. The surface is one focusable mark: a click reports the density "
        "under the pointer and Enter / Space the peak, as mj-chart-density-click { x, y, density }."
    ),
    data_shape=_DENSITY_SHAPE,
    options=[
        AttributeDoc(name="density-style", description=_DENSITY_OPTIONS_DOC[0].description, kind="enum",
                     values=["fill", "contour", "both"], default="fill"),
        _DENSITY_OPTIONS_DOC[1],
    ],
    examples=[
        gallery_example(
            "basic", "KDE surface",
            "<p>120 students: study hours against exam score as a density surface. Try "
            "<code>density-style</code> in the controls.</p>",
            _chart("density-2d", _OBSERVATIONS_2D, "Study time and exam score density"),
        ),
        gallery_example(
            "both", "Surface with contours",
            "<p><code>density-style=\"both\"</code> on two clusters with a finer grid "
            "(<code>density.resolution: 48</code>).</p>",
            _chart("density-2d", _TWO_CLUSTERS, "Session length and pages viewed", attrs='density-style="both"',
                   height=300),
        ),
        gallery_example(
            "grid", "Pre-computed grid",
            "<p>A terrain surface given as <code>grid</code>: no KDE is computed.</p>",
            _chart("density-2d", _TERRAIN, "Terrain elevation (m)"),
        ),
        gallery_example(
            "events", "Click events",
            "<p>The script clicks the surface (density under the pointer) and presses Enter (the peak); "
            "both emit <code>mj-chart-density-click</code>.</p>",
            _chart("density-2d", _OBSERVATIONS_2D, "Study time and exam score density"),
            script=_events_script(["mj-chart-density-click"], "density-hit"),
        ),
    ],
)

_CONTOUR = ChartTypeDoc(
    type_key="contour",
    title="Contour Plot",
    category="RELATIONSHIP",
    summary="Iso-contour lines tracing equal levels of a 2D density or surface.",
    description=(
        "Traces iso-lines from the KDE grid (or a pre-computed grid {x, y, z}) with marching squares; "
        "each level is one joined, labelled and focusable path. density.levels sets a count (3-20, "
        "default 8) or levels / density.levels an array of level values; density-style=\"both\" (or, "
        "without the attribute, density.style = \"both\" or fill: true in the data) adds the filled "
        "surface; the attribute always wins over the data. meta.xLabel / "
        "meta.yLabel title the axes. A click or Enter / Space on a level emits mj-chart-contour-click "
        "{ level, index, lines }."
    ),
    data_shape=_DENSITY_SHAPE,
    options=[
        AttributeDoc(name="density-style", description=_DENSITY_OPTIONS_DOC[0].description, kind="enum",
                     values=["fill", "contour", "both"], default="contour"),
        _DENSITY_OPTIONS_DOC[1],
    ],
    examples=[
        gallery_example(
            "basic", "Density contours",
            "<p>Eight levels of the density of two clusters of sightings.</p>",
            _chart("contour", _CONTOUR_POINTS, "Contours of the sighting density"),
        ),
        gallery_example(
            "levels-fill", "Chosen levels, filled",
            "<p>A terrain grid with explicit <code>levels</code> (200 / 400 / 600 / 800 m) and "
            "<code>fill: true</code>.</p>",
            _chart("contour", _CONTOUR_LEVELS, "Terrain contours (m)"),
        ),
        gallery_example(
            "events", "Click events",
            "<p>The script logs <code>mj-chart-contour-click</code> for a clicked level and for Enter on "
            "the last one.</p>",
            _chart("contour", _CONTOUR_POINTS, "Contours of the sighting density"),
            script=_events_script(["mj-chart-contour-click"], "contour"),
        ),
    ],
)

_HEXBIN = ChartTypeDoc(
    type_key="hexbin",
    title="Hexbin",
    category="RELATIONSHIP",
    summary="Aggregates dense scatter data into hexagonal bins colored by count.",
    description=(
        "Points from all series are merged and assigned to flat-topped hexagonal cells. hexbin.bins "
        "sets the number of hexagon columns across the plot (the grid scales with the chart, so "
        "resizing does not regroup points); hexbin.radius sets a fixed radius in px. hexbin.stat picks "
        "the per-bin statistic: count (default), sum or mean of each point's value field. The radius "
        "and stat attributes win over the data (like every renderer option). meta.xLabel / meta.yLabel "
        "title the axes. The colour ramp starts at "
        "zero, so single-point bins stay visible, and a colour bar reads it back; encoding=\"size\" "
        "encodes the statistic as hexagon area instead. Each hexagon is focusable; a click or Enter / "
        "Space emits mj-chart-hexbin-click { x, y, x0, x1, y0, y1, stat, value, count, cx, cy } with "
        "the bin centre and extent in data units."
    ),
    data_shape=(
        '<pre><code>{\n'
        '  meta?: { xLabel?: string, yLabel?: string },     // axis titles\n'
        '  series: [{ name: string, points: [{ x: number, y: number, value?: number }] }],\n'
        '  hexbin?: {\n'
        '    bins?: number,                    // hexagon columns across the plot\n'
        '    radius?: number,                  // or a fixed circumradius in px (default 20)\n'
        '    stat?: "count" | "sum" | "mean"   // of value; the stat attribute wins over it\n'
        '  }\n'
        '}</code></pre>'
    ),
    options=[
        AttributeDoc(name="stat", description="Per-bin statistic; overrides `hexbin.stat` in the data.",
                     kind="enum", values=["count", "sum", "mean"], default="count"),
        AttributeDoc(name="encoding", description="Encode the statistic as colour or as hexagon area.",
                     kind="enum", values=["color", "size"], default="color"),
        _show_labels("false"),
        AttributeDoc(name="radius",
                     description="Hexagon circumradius in px; overrides `hexbin.bins` and `hexbin.radius` in the data.",
                     kind="number", default="20"),
    ],
    examples=[
        gallery_example(
            "basic", "Counts",
            "<p>250 cars in 16 hexagon columns, coloured by count; <code>meta.xLabel</code> / "
            "<code>meta.yLabel</code> title the axes. Set <code>radius</code> in the controls: the "
            "attribute wins over <code>hexbin.bins</code> in the data.</p>",
            _chart("hexbin", _HEX_POINTS, "Engine size and fuel use"),
        ),
        gallery_example(
            "size", "Size encoding",
            "<p><code>encoding=\"size\"</code>: hexagon area shows the count.</p>",
            _chart("hexbin", _HEX_POINTS, "Engine size and fuel use", attrs='encoding="size"'),
        ),
        gallery_example(
            "mean", "Mean of a value",
            "<p><code>hexbin.stat: \"mean\"</code> of each purchase's value: the bins near the entrance "
            "spend more.</p>",
            _chart("hexbin", _HEX_MEAN, "Average purchase by store position ($)", height=300),
        ),
        gallery_example(
            "events", "Click events",
            "<p>The script logs <code>mj-chart-hexbin-click</code> for a clicked hexagon and for Enter on "
            "the last one.</p>",
            _chart("hexbin", _HEX_POINTS, "Engine size and fuel use"),
            script=_events_script(["mj-chart-hexbin-click"], "hexbin"),
        ),
    ],
)

_SPLOM = ChartTypeDoc(
    type_key="splom",
    title="Scatter Plot Matrix",
    category="RELATIONSHIP",
    summary="N x N grid of scatter sub-plots for every pair of numeric variables.",
    description=(
        "variables lists the field names to plot, in order (without it the numeric fields of the first "
        "point are used). Each series is one group (e.g. species), told apart by colour and mark shape. "
        "One linear scale per variable is shared along its row and column, with tick labels along the "
        "left and bottom edges. Diagonal cells show the variable name; diagonal=\"histogram\" adds a "
        "pooled histogram and diagonal=\"density\" one density curve per group. triangle=\"lower\" or "
        "\"upper\" shows half the matrix and puts Pearson's r of each pair in the other half. Every "
        "point is focusable; a click or Enter / Space emits mj-chart-point-click "
        "{ series, xVar, yVar, x, y }."
    ),
    data_shape=(
        '<pre><code>{\n'
        '  variables?: string[],                                  // numeric field names, in order\n'
        '  series: [{ name: string, points: [{ [variable]: number }] }]\n'
        '}</code></pre>'
        '<p>Non-finite values are skipped for the pairs that need them.</p>'
    ),
    options=[
        AttributeDoc(name="diagonal", description="What the diagonal cells show.", kind="enum",
                     values=["label", "histogram", "density"], default="label"),
        AttributeDoc(name="triangle", description="Whole matrix, or one half with Pearson's r in the other.",
                     kind="enum", values=["full", "lower", "upper"], default="full"),
    ],
    examples=[
        gallery_example(
            "basic", "Lower triangle with densities",
            "<p>Two species, density curves on the diagonal and r in the upper half.</p>",
            _chart("splom", _IRIS_SPLOM, "Iris measurements by species", attrs='diagonal="density" triangle="lower"',
                   legend=True, height=340),
        ),
        gallery_example(
            "full-histogram", "Full matrix, histograms",
            "<p>Four housing variables with pooled histograms on the diagonal.</p>",
            _chart("splom", _HOUSING, "Housing variables", attrs='diagonal="histogram"', legend=True, height=420),
        ),
        gallery_example(
            "upper", "Upper triangle",
            "<p><code>triangle=\"upper\"</code>: the scatter cells above the diagonal, r below.</p>",
            _chart("splom", _HOUSING, "Housing variables", attrs='triangle="upper"', legend=True, height=420),
        ),
        gallery_example(
            "events", "Click events",
            "<p>The script logs <code>mj-chart-point-click</code> (with the variable pair) for a clicked "
            "point and for Enter on the last one.</p>",
            _chart("splom", _IRIS_SPLOM, "Iris measurements by species", attrs='diagonal="density" triangle="lower"',
                   legend=True, height=340),
            script=_events_script(["mj-chart-point-click"], "point"),
        ),
    ],
)

_BEESWARM = ChartTypeDoc(
    type_key="beeswarm",
    title="Beeswarm",
    category="RELATIONSHIP",
    summary="Non-overlapping dot layout along a single continuous axis.",
    description=(
        "Every point of every series is placed in one swarm along one value axis, coloured by its "
        "series; the cross axis carries no meaning. "
        "Points with x values give a horizontal swarm, y values a vertical one (an explicit orientation "
        "wins). Dots never overlap (tied values sit side by side); a crowded swarm shrinks its dots "
        "before spreading any overflow. radius and padding (attributes, else data fields) set the dot "
        "size and gap, mode=\"strip\" turns collision avoidance off, and a dashed median line per "
        "series is drawn unless show-median=\"false\". A click or Enter / Space on a dot emits "
        "mj-chart-dot-click { series, value, label }."
    ),
    data_shape=(
        '<pre><code>{\n'
        '  series: [{ name: string, points: [{ x?: number, y?: number, label?: string }] }],\n'
        '  radius?: number,    // dot radius in px (default 4)\n'
        '  padding?: number    // gap between dots in px (default 1)\n'
        '}</code></pre>'
        '<p>Non-finite values are missing data.</p>'
    ),
    options=[
        orientation_option(None, "Swarm direction; by default horizontal when the points carry only `x`."),
        AttributeDoc(name="radius", description="Dot radius in px; wins over the data's `radius`.", kind="number",
                     default="4"),
        AttributeDoc(name="padding", description="Gap between dots in px; wins over the data's `padding`.",
                     kind="number", default="1"),
        AttributeDoc(name="mode", description="`strip` places the dots without collision avoidance.",
                     kind="enum", values=["beeswarm", "strip"], default="beeswarm"),
        boolean_option("show-median", "Dashed median line of each series; `show-median=\"false\"` hides it.", True),
    ],
    examples=[
        gallery_example(
            "basic", "Two swarms",
            "<p>Completion times of two groups in one horizontal swarm, coloured by group, with a median "
            "line per group.</p>",
            _chart("beeswarm", _COMPLETION, "Task completion time by group (s)", legend=True, height=240),
        ),
        gallery_example(
            "vertical", "Vertical swarm",
            "<p>Points with <code>y</code> values swarm vertically; both releases share the swarm and "
            "each has its own median line.</p>",
            _chart("beeswarm", _VERTICAL_SWARM, "Page load time by release (ms)", legend=True, height=320),
        ),
        gallery_example(
            "labels-strip", "Labelled points, strip mode",
            "<p>Each dot reads its package name; <code>mode=\"strip\"</code> lets tied sizes overlap and "
            "<code>show-median=\"false\"</code> hides the median.</p>",
            _chart("beeswarm", _PACKAGES, "Bundle size by package (kB)", attrs='mode="strip" show-median="false"',
                   height=180),
        ),
        gallery_example(
            "events", "Click events",
            "<p>The script logs <code>mj-chart-dot-click</code> for a clicked dot and for Enter on the "
            "last one.</p>",
            _chart("beeswarm", _COMPLETION, "Task completion time by group (s)", legend=True, height=240),
            script=_events_script(["mj-chart-dot-click"], "dot"),
        ),
    ],
)


# ---------------------------------------------------------------------------
# Exported catalog
# ---------------------------------------------------------------------------

CHART_TYPES = [
    _HISTOGRAM,
    _DENSITY,
    _FREQUENCY_POLYGON,
    _BOXPLOT,
    _VIOLIN,
    _STRIP,
    _SWARM,
    _RUG,
    _DOT_HISTOGRAM,
    _RIDGELINE,
    _QQ,
    _CDF,
    _SCATTER,
    _BUBBLE,
    _CONNECTED_SCATTER,
    _RESIDUAL,
    _HEATMAP,
    _CORRELATION_MATRIX,
    _DENSITY_2D,
    _CONTOUR,
    _HEXBIN,
    _SPLOM,
    _BEESWARM,
]
