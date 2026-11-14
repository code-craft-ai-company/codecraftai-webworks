"""
    04_stat_finance_project.py

    ChartTypeDoc catalog entries for statistical, financial, and
    project/schedule chart types rendered by <mj-chart>.

    Categories covered:
      Statistical  — errorbar, confidence-interval, control-chart, run-chart,
                     roc, precision-recall, lift, calibration, survival,
                     kaplan-meier, forest, funnel-plot
      Financial    — ohlc, candlestick, volume, tornado
      Project      — gantt, roadmap, timeline, milestone, kanban,
                     resource-allocation
"""

from testcomponents.catalog.componentdoc import AttributeDoc
from testcomponents.charttypes.charttypedoc import ChartTypeDoc
from testcomponents.charttypes._03_parts_hierarchy_flow import chart_markup
from testcomponents.charttypes._03_parts_hierarchy_flow import events_example
from testcomponents.charttypes.examplemarkup import basic_example
from testcomponents.charttypes.examplemarkup import boolean_option
from testcomponents.charttypes.examplemarkup import compact_json
from testcomponents.charttypes.examplemarkup import gallery_example
from testcomponents.charttypes.examplemarkup import orientation_option


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_LEGEND = '<mj-chart-legend></mj-chart-legend>'


def _chart(chart_type: str, data: object, height: str = "260px",
           attrs: dict = None, legend: bool = False) -> str:
    """
        Build a minimal <mj-chart> HTML snippet with inline JSON data.

        :param chart_type: The ``type`` attribute value for <mj-chart>.
        :param data: A Python object that will be serialised to the inline
            ``<script type="application/json">`` child element.
        :param height: CSS height applied via the ``style`` attribute.
        :param attrs: Optional renderer option attributes (name -> value),
            e.g. ``{"scale": "log"}`` or ``{"variant": "heatmap"}``.
        :param legend: True nests an <mj-chart-legend> that lists what the
            chart's colours stand for.
        :returns: A complete HTML snippet string.
    """
    payload = compact_json(data)
    options = ""
    if attrs is not None:
        for name, value in attrs.items():
            options = options + f' {name}="{value}"'
    legend_line = f'  {_LEGEND}\n' if legend is True else ""
    result = (
        f'<mj-chart type="{chart_type}"{options} style="height:{height}">\n'
        f'  <script type="application/json">{payload}</script>\n'
        f'{legend_line}'
        f'</mj-chart>'
    )
    return result


# ---------------------------------------------------------------------------
# Shared realistic sample datasets
# ---------------------------------------------------------------------------

_ERRORBAR_DATA = {
    "series": [
        {
            "name": "Treatment A",
            "groups": [
                {"category": "Week 1", "value": 4.2, "error_low": 0.6, "error_high": 0.8},
                {"category": "Week 2", "value": 5.1, "error_low": 0.5, "error_high": 0.7},
                {"category": "Week 3", "value": 6.8, "error_low": 0.9, "error_high": 1.1},
                {"category": "Week 4", "value": 7.4, "error_low": 0.7, "error_high": 0.9},
                {"category": "Week 6", "value": 8.0, "error_low": 1.0, "error_high": 1.2},
            ],
        },
        {
            "name": "Control",
            "groups": [
                {"category": "Week 1", "value": 3.9, "error_low": 0.5, "error_high": 0.5},
                {"category": "Week 2", "value": 4.0, "error_low": 0.4, "error_high": 0.6},
                {"category": "Week 3", "value": 4.2, "error_low": 0.6, "error_high": 0.6},
                {"category": "Week 4", "value": 4.1, "error_low": 0.5, "error_high": 0.7},
                {"category": "Week 6", "value": 4.3, "error_low": 0.5, "error_high": 0.8},
            ],
        },
    ]
}

_CI_DATA = {
    "series": [
        {
            "name": "Mean difference (mmHg)",
            "groups": [
                {"category": "Overall",        "value": -4.2, "error_low": 1.6, "error_high": 1.6},
                {"category": "Age < 60",       "value": -5.1, "error_low": 2.3, "error_high": 2.3},
                {"category": "Age 60+",        "value": -3.0, "error_low": 2.4, "error_high": 2.4},
                {"category": "Diabetic",       "value": -1.2, "error_low": 3.1, "error_high": 3.1},
                {"category": "Non-diabetic",   "value": -5.0, "error_low": 1.9, "error_high": 1.9},
            ],
        }
    ]
}

_CONTROL_CHART_DATA = {
    "series": [
        {
            "name": "Defect Rate",
            "points": [
                {"x": 1,  "y": 2.1},
                {"x": 2,  "y": 3.4},
                {"x": 3,  "y": 2.8},
                {"x": 4,  "y": 4.1},
                {"x": 5,  "y": 3.0},
                {"x": 6,  "y": 2.5},
                {"x": 7,  "y": 6.9, "ooc": True},
                {"x": 8,  "y": 3.2},
                {"x": 9,  "y": 2.7},
                {"x": 10, "y": 3.6},
                {"x": 11, "y": 2.9},
                {"x": 12, "y": 3.1},
            ],
        }
    ],
    "control_limits": {"ucl": 6.0, "lcl": 0.5, "cl": 3.1},
}

# Dated daily observations: the x axis becomes a calendar axis.
_CONTROL_DATES = [
    "2025-03-03", "2025-03-04", "2025-03-05", "2025-03-06", "2025-03-07",
    "2025-03-10", "2025-03-11", "2025-03-12", "2025-03-13", "2025-03-14",
    "2025-03-17", "2025-03-18",
]
for _index, _point in enumerate(_CONTROL_CHART_DATA["series"][0]["points"]):
    _point["x"] = _CONTROL_DATES[_index]
_CONTROL_CHART_DATA["series"][0]["points"][6].pop("ooc")

_RUN_CHART_DATA = {
    "series": [
        {
            "name": "Cycle Time (days)",
            "points": [
                {"x": 1,  "y": 5.2},
                {"x": 2,  "y": 4.8},
                {"x": 3,  "y": 6.1},
                {"x": 4,  "y": 4.5},
                {"x": 5,  "y": 5.9},
                {"x": 6,  "y": 5.3},
                {"x": 7,  "y": 4.7},
                {"x": 8,  "y": 6.4},
                {"x": 9,  "y": 5.0},
                {"x": 10, "y": 4.9},
                {"x": 11, "y": 4.6},
                {"x": 12, "y": 4.4},
                {"x": 13, "y": 4.7},
                {"x": 14, "y": 4.5},
                {"x": 15, "y": 4.3},
                {"x": 16, "y": 4.6},
            ],
        }
    ],
    "reference_lines": [{"label": "Target 5.5", "value": 5.5}],
}

_ROC_DATA = {
    "series": [
        {
            "name": "Gradient Boosting",
            "points": [
                {"x": 0.00, "y": 0.00},
                {"x": 0.02, "y": 0.30},
                {"x": 0.05, "y": 0.55},
                {"x": 0.10, "y": 0.72},
                {"x": 0.20, "y": 0.85},
                {"x": 0.30, "y": 0.90},
                {"x": 0.50, "y": 0.95},
                {"x": 0.75, "y": 0.98},
                {"x": 1.00, "y": 1.00},
            ],
        },
        {
            "name": "Logistic Regression",
            "points": [
                {"x": 0.00, "y": 0.00},
                {"x": 0.05, "y": 0.40},
                {"x": 0.10, "y": 0.60},
                {"x": 0.20, "y": 0.75},
                {"x": 0.40, "y": 0.87},
                {"x": 0.60, "y": 0.93},
                {"x": 0.80, "y": 0.97},
                {"x": 1.00, "y": 1.00},
            ],
        },
    ]
}

_PR_DATA = {
    "baseline_prevalence": 0.15,
    "series": [
        {
            "name": "XGBoost",
            "points": [
                {"x": 0.0,  "y": 1.00},
                {"x": 0.10, "y": 0.92},
                {"x": 0.25, "y": 0.85},
                {"x": 0.40, "y": 0.78},
                {"x": 0.55, "y": 0.68},
                {"x": 0.70, "y": 0.55},
                {"x": 0.85, "y": 0.40},
                {"x": 1.00, "y": 0.15},
            ],
        }
    ],
}

_LIFT_DATA = {
    "series": [
        {
            "name": "Email Campaign Model",
            "points": [
                {"x": 0.00, "y": 4.8},
                {"x": 0.10, "y": 3.9},
                {"x": 0.20, "y": 3.1},
                {"x": 0.30, "y": 2.5},
                {"x": 0.40, "y": 2.0},
                {"x": 0.50, "y": 1.7},
                {"x": 0.65, "y": 1.3},
                {"x": 0.80, "y": 1.05},
                {"x": 1.00, "y": 1.0},
            ],
        }
    ]
}

_CALIBRATION_DATA = {
    "series": [
        {
            "name": "Random Forest",
            "points": [
                {"x": 0.05, "y": 0.04,  "n": 220},
                {"x": 0.15, "y": 0.13,  "n": 310},
                {"x": 0.25, "y": 0.22,  "n": 280},
                {"x": 0.35, "y": 0.38,  "n": 190},
                {"x": 0.45, "y": 0.44,  "n": 170},
                {"x": 0.55, "y": 0.60,  "n": 140},
                {"x": 0.65, "y": 0.71,  "n": 110},
                {"x": 0.75, "y": 0.79,  "n": 90},
                {"x": 0.85, "y": 0.88,  "n": 60},
                {"x": 0.95, "y": 0.96,  "n": 30},
            ],
        }
    ]
}

_SURVIVAL_DATA = {
    "series": [
        {
            "name": "Treatment",
            "points": [
                {"x": 0,   "y": 1.00, "at_risk": 120, "ci_lower": 1.00, "ci_upper": 1.00},
                {"x": 6,   "y": 0.92, "at_risk": 110, "ci_lower": 0.86, "ci_upper": 0.96},
                {"x": 12,  "y": 0.83, "at_risk": 97,  "ci_lower": 0.76, "ci_upper": 0.89},
                {"x": 18,  "y": 0.71, "at_risk": 80,  "ci_lower": 0.63, "ci_upper": 0.78},
                {"x": 20,  "y": 0.71, "censored": True},
                {"x": 24,  "y": 0.62, "at_risk": 65,  "ci_lower": 0.54, "ci_upper": 0.70},
                {"x": 30,  "y": 0.54, "at_risk": 50,  "ci_lower": 0.45, "ci_upper": 0.62},
                {"x": 36,  "y": 0.47, "at_risk": 38,  "ci_lower": 0.38, "ci_upper": 0.56},
                {"x": 42,  "y": 0.47, "censored": True},
            ],
        },
        {
            "name": "Control",
            "points": [
                {"x": 0,   "y": 1.00, "at_risk": 115, "ci_lower": 1.00, "ci_upper": 1.00},
                {"x": 6,   "y": 0.86, "at_risk": 98,  "ci_lower": 0.79, "ci_upper": 0.92},
                {"x": 12,  "y": 0.74, "at_risk": 82,  "ci_lower": 0.65, "ci_upper": 0.81},
                {"x": 18,  "y": 0.61, "at_risk": 66,  "ci_lower": 0.52, "ci_upper": 0.70},
                {"x": 24,  "y": 0.51, "at_risk": 52,  "ci_lower": 0.41, "ci_upper": 0.60},
                {"x": 28,  "y": 0.51, "censored": True},
                {"x": 30,  "y": 0.42, "at_risk": 38,  "ci_lower": 0.33, "ci_upper": 0.51},
                {"x": 36,  "y": 0.35, "at_risk": 28,  "ci_lower": 0.26, "ci_upper": 0.44},
                {"x": 40,  "y": 0.35, "censored": True},
            ],
        },
    ]
}

_FOREST_DATA = {
    "series": [
        {
            "name": "Subgroup Analysis",
            "groups": [
                {"category": "Age < 50",       "value":  0.72, "error_low": 0.18, "error_high": 0.22, "weight": 3.2},
                {"category": "Age 50–65",       "value":  0.85, "error_low": 0.12, "error_high": 0.15, "weight": 5.8},
                {"category": "Age > 65",        "value":  0.91, "error_low": 0.20, "error_high": 0.24, "weight": 2.5},
                {"category": "Female",          "value":  0.78, "error_low": 0.14, "error_high": 0.18, "weight": 4.7},
                {"category": "Male",            "value":  0.82, "error_low": 0.13, "error_high": 0.16, "weight": 5.2},
                {"category": "High Risk",       "value":  1.05, "error_low": 0.22, "error_high": 0.28, "weight": 2.1},
                {"category": "Standard Risk",   "value":  0.76, "error_low": 0.11, "error_high": 0.13, "weight": 6.3},
            ],
        }
    ],
    "pooled": {
        "value": 0.82,
        "ci_lower": 0.74,
        "ci_upper": 0.90,
        "label": "Pooled (n=7 studies)",
    },
}

_FUNNEL_PLOT_DATA = {
    "series": [
        {
            "name": "Studies",
            "points": [
                {"x":  0.65, "y": 0.18, "label": "Smith 2018"},
                {"x":  0.82, "y": 0.14, "label": "Jones 2019"},
                {"x":  0.78, "y": 0.21, "label": "Lee 2020"},
                {"x":  0.91, "y": 0.09, "label": "Wang 2020"},
                {"x":  0.73, "y": 0.25, "label": "Patel 2021"},
                {"x":  0.88, "y": 0.12, "label": "Kim 2021"},
                {"x":  0.60, "y": 0.30, "label": "Müller 2022"},
                {"x":  0.95, "y": 0.07, "label": "Chen 2022"},
                {"x":  0.71, "y": 0.19, "label": "Brown 2023"},
                {"x":  1.10, "y": 0.28, "label": "Davis 2023"},
            ],
        }
    ],
    "funnel": {
        "summary_effect": 0.82,
        "pseudo_ci": [
            {"se": 0.00, "lower": 0.82, "upper": 0.82},
            {"se": 0.10, "lower": 0.62, "upper": 1.02},
            {"se": 0.20, "lower": 0.42, "upper": 1.22},
            {"se": 0.30, "lower": 0.22, "upper": 1.42},
        ],
    },
}

_CANDLES = [
    {"t": "2025-04-01", "o": 182.50, "h": 186.30, "l": 181.10, "c": 185.40, "v": 31200000},
    {"t": "2025-04-02", "o": 185.40, "h": 187.90, "l": 183.60, "c": 184.10, "v": 27800000},
    {"t": "2025-04-03", "o": 184.10, "h": 188.50, "l": 183.00, "c": 187.80, "v": 35100000},
    {"t": "2025-04-04", "o": 187.80, "h": 190.20, "l": 186.40, "c": 189.60, "v": 29400000},
    {"t": "2025-04-07", "o": 189.60, "h": 191.00, "l": 185.50, "c": 186.20, "v": 33700000},
    {"t": "2025-04-08", "o": 186.20, "h": 188.70, "l": 184.90, "c": 187.50, "v": 24600000},
    {"t": "2025-04-09", "o": 187.50, "h": 192.30, "l": 186.80, "c": 191.70, "v": 41200000},
    {"t": "2025-04-10", "o": 191.70, "h": 193.80, "l": 190.10, "c": 192.50, "v": 36800000},
    {"t": "2025-04-11", "o": 192.50, "h": 194.60, "l": 189.30, "c": 190.80, "v": 28900000},
    {"t": "2025-04-14", "o": 190.80, "h": 193.10, "l": 189.90, "c": 192.00, "v": 31500000},
]

_OHLC_DATA = {"candles": _CANDLES}

_VOLUME_DATA = {"candles": _CANDLES}

_TORNADO_DATA = {
    "baseline": 4200000,
    "low_label": "Input at low case",
    "high_label": "Input at high case",
    "series": [
        {
            "name": "Sensitivity",
            "values": [
                {"label": "Selling Price",       "low": 2800000, "high": 6100000},
                {"label": "Unit Volume",         "low": 3100000, "high": 5600000},
                {"label": "COGS",                "low": 3500000, "high": 5000000},
                {"label": "Marketing Spend",     "low": 3700000, "high": 4900000},
                {"label": "Customer Churn",      "low": 3900000, "high": 4700000},
                {"label": "R&D Investment",      "low": 4000000, "high": 4500000},
                {"label": "Discount Rate",       "low": 4900000, "high": 3600000},
            ],
        }
    ],
}

_GANTT_DATA = {
    "tasks": [
        {
            "id": "req",
            "group": "Planning",
            "label": "Requirements",
            "start": "2025-04-01",
            "end": "2025-04-14",
            "progress": 1.0,
            "assignee": "Alice",
        },
        {
            "id": "design",
            "group": "Planning",
            "label": "System Design",
            "start": "2025-04-10",
            "end": "2025-04-28",
            "progress": 0.8,
            "assignee": "Bob",
            "depends": ["req"],
        },
        {
            "id": "dev-fe",
            "group": "Build",
            "label": "Frontend Dev",
            "start": "2025-04-21",
            "end": "2025-05-16",
            "progress": 0.4,
            "assignee": "Carol",
            "depends": ["design"],
        },
        {
            "id": "dev-be",
            "group": "Build",
            "label": "Backend Dev",
            "start": "2025-04-21",
            "end": "2025-05-23",
            "progress": 0.3,
            "assignee": "Dave",
            "depends": ["design"],
        },
        {
            "id": "qa",
            "group": "Release",
            "label": "QA & Testing",
            "start": "2025-05-19",
            "end": "2025-06-06",
            "progress": 0.0,
            "assignee": "Eve",
            "depends": ["dev-fe", "dev-be"],
        },
        {
            "id": "launch",
            "group": "Release",
            "label": "Launch",
            "start": "2025-06-09",
            "end": "2025-06-13",
            "progress": 0.0,
            "assignee": "Alice",
            "depends": ["qa"],
        },
    ]
}

_ROADMAP_DATA = {
    "tasks": [
        {
            "id": "p1",
            "label": "Auth & SSO",
            "start": "2025-Q1",
            "end": "2025-Q1",
            "status": "completed",
            "group": "Platform",
        },
        {
            "id": "p2",
            "label": "API Gateway v2",
            "start": "2025-Q2",
            "end": "2025-Q2",
            "status": "in-progress",
            "group": "Platform",
        },
        {
            "id": "p3",
            "label": "Observability Stack",
            "start": "2025-Q3",
            "end": "2025-Q4",
            "status": "planned",
            "group": "Platform",
        },
        {
            "id": "m1",
            "label": "Dashboard Redesign",
            "start": "2025-Q1",
            "end": "2025-Q2",
            "status": "in-progress",
            "group": "Mobile",
        },
        {
            "id": "m2",
            "label": "Offline Mode",
            "start": "2025-Q3",
            "end": "2025-Q3",
            "status": "planned",
            "group": "Mobile",
        },
        {
            "id": "m3",
            "label": "Push Notifications",
            "start": "2025-Q4",
            "end": "2025-Q4",
            "status": "at-risk",
            "group": "Mobile",
        },
    ]
}

_TIMELINE_DATA = {
    "events": [
        {"id": "e1", "label": "Project Kickoff",    "date": "2025-01-06", "status": "completed"},
        {"id": "e2", "label": "Alpha Release",       "date": "2025-02-17", "status": "completed"},
        {"id": "e3", "label": "Beta Launch",         "date": "2025-03-31", "status": "completed"},
        {"id": "e4", "label": "Security Audit",      "date": "2025-04-14", "status": "active"},
        {"id": "e5", "label": "GA Release",          "date": "2025-05-26", "status": "planned"},
        {"id": "e6", "label": "Post-Launch Review",  "date": "2025-07-07", "status": "planned"},
    ]
}

_MILESTONE_DATA = {
    "events": [
        {"id": "m1", "label": "Seed Round Closes",    "date": "2024-09-01",  "status": "completed"},
        {"id": "m2", "label": "MVP Shipped",           "date": "2024-11-15",  "status": "completed"},
        {"id": "m3", "label": "First 1000 Users",      "date": "2025-01-20",  "status": "completed"},
        {"id": "m4", "label": "Series A",              "date": "2025-04-01",  "status": "active"},
        {"id": "m5", "label": "Enterprise Launch",     "date": "2025-07-01",  "status": "planned"},
        {"id": "m6", "label": "Profitability Target",  "date": "2025-12-31",  "status": "planned"},
    ]
}

_KM_DATA = {
    "series": [
        {
            "name": "Stage I",
            "points": [
                {"x": 0,  "y": 1.00, "at_risk": 40},
                {"x": 4,  "y": 0.95, "at_risk": 38},
                {"x": 9,  "y": 0.90, "at_risk": 35},
                {"x": 11, "y": 0.90, "censored": True},
                {"x": 15, "y": 0.84, "at_risk": 30},
                {"x": 22, "y": 0.77, "at_risk": 24},
                {"x": 30, "y": 0.77, "censored": True},
            ],
        },
        {
            "name": "Stage III",
            "points": [
                {"x": 0,  "y": 1.00, "at_risk": 36},
                {"x": 3,  "y": 0.86, "at_risk": 31},
                {"x": 7,  "y": 0.72, "at_risk": 25},
                {"x": 12, "y": 0.58, "at_risk": 19},
                {"x": 14, "y": 0.58, "censored": True},
                {"x": 19, "y": 0.43, "at_risk": 12},
                {"x": 26, "y": 0.32, "at_risk": 7},
                {"x": 28, "y": 0.32, "censored": True},
            ],
        },
    ]
}

_KANBAN_DATA = {
    "columns": [
        {
            "name": "Backlog",
            "items": [
                {"id": "TK-14", "label": "Add dark mode toggle",        "priority": "low",    "assignee": "Carol"},
                {"id": "TK-15", "label": "Improve search indexing",      "priority": "medium", "assignee": "Dave"},
                {"id": "TK-16", "label": "Migrate legacy endpoints",     "priority": "medium", "assignee": None},
            ],
        },
        {
            "name": "In Progress",
            "wip-limit": 3,
            "items": [
                {"id": "TK-09", "label": "OAuth2 integration",           "priority": "high",     "assignee": "Alice"},
                {"id": "TK-11", "label": "Rate limiting middleware",      "priority": "high",     "assignee": "Bob"},
                {"id": "TK-12", "label": "Dashboard chart components",   "priority": "critical", "assignee": "Carol"},
                {"id": "TK-13", "label": "Audit log export",             "priority": "medium",   "assignee": "Eve"},
            ],
        },
        {
            "name": "Review",
            "wip-limit": 2,
            "items": [
                {"id": "TK-07", "label": "API pagination refactor",      "priority": "medium", "assignee": "Dave"},
                {"id": "TK-08", "label": "Error boundary improvements",  "priority": "high",   "assignee": "Alice"},
            ],
        },
        {
            "name": "Done",
            "items": [
                {"id": "TK-01", "label": "User auth scaffold",           "priority": "critical", "assignee": "Bob"},
                {"id": "TK-03", "label": "CI/CD pipeline setup",         "priority": "high",     "assignee": "Eve"},
                {"id": "TK-05", "label": "Database migration scripts",   "priority": "medium",   "assignee": "Dave"},
            ],
        },
    ]
}

_RESOURCE_DATA = {
    "resources": [
        {
            "id": "alice",
            "label": "Alice (FE Lead)",
            "capacity": 1.0,
            "allocations": [
                {"task": "Dashboard v2",    "start": "2025-04-01", "end": "2025-04-18", "load": 0.8},
                {"task": "Sprint Planning", "start": "2025-04-22", "end": "2025-04-25", "load": 0.3},
                {"task": "Auth Redesign",   "start": "2025-04-28", "end": "2025-05-09", "load": 0.9},
            ],
        },
        {
            "id": "bob",
            "label": "Bob (BE Lead)",
            "capacity": 1.0,
            "allocations": [
                {"task": "API Gateway",     "start": "2025-04-01", "end": "2025-04-25", "load": 0.7},
                {"task": "DB Migrations",   "start": "2025-04-14", "end": "2025-04-30", "load": 0.5},
            ],
        },
        {
            "id": "carol",
            "label": "Carol (QA)",
            "capacity": 1.0,
            "allocations": [
                {"task": "Regression Suite","start": "2025-04-07", "end": "2025-04-11", "load": 1.0},
                {"task": "Load Testing",    "start": "2025-04-21", "end": "2025-04-30", "load": 0.6},
                {"task": "Sec Audit",       "start": "2025-05-05", "end": "2025-05-09", "load": 0.8},
            ],
        },
        {
            "id": "dave",
            "label": "Dave (DevOps)",
            "capacity": 1.0,
            "allocations": [
                {"task": "K8s Upgrade",     "start": "2025-04-01", "end": "2025-04-07", "load": 1.0},
                {"task": "CI Refactor",     "start": "2025-04-14", "end": "2025-05-02", "load": 0.5},
                {"task": "On-Call",         "start": "2025-04-01", "end": "2025-05-09", "load": 0.2},
            ],
        },
    ]
}


# ---------------------------------------------------------------------------
# Extra sample data for the galleries
# ---------------------------------------------------------------------------

_LATENCY_BARS = {
    "series": [
        {
            "name": "p50 latency (ms)",
            "groups": [
                {"category": "eu-west", "value": 182, "error_low": 24, "error_high": 41, "bar": True},
                {"category": "us-east", "value": 205, "error_low": 30, "error_high": 52, "bar": True},
                {"category": "ap-south", "value": 264, "error_low": 38, "error_high": 77, "bar": True},
                {"category": "sa-east", "value": 231, "error_low": 35, "error_high": 60, "bar": True},
            ],
        }
    ]
}

_ODDS_DATA = {
    "series": [
        {
            "name": "Odds ratio",
            "groups": [
                {"category": "Smoking", "value": 2.4, "error_low": 0.6, "error_high": 0.9},
                {"category": "Obesity", "value": 1.7, "error_low": 0.4, "error_high": 0.5},
                {"category": "Exercise", "value": 0.7, "error_low": 0.2, "error_high": 0.2},
                {"category": "Diet score", "value": 0.95, "error_low": 0.15, "error_high": 0.2},
            ],
        }
    ]
}

_FILL_WEIGHTS = [
    501.2, 499.8, 500.6, 502.1, 498.9, 500.3, 501.7, 499.5, 500.9, 503.8,
    500.1, 499.2, 501.4, 500.0, 497.1, 500.8, 501.1, 499.9, 500.4, 502.6,
]

_CONTROL_AUTO = {
    "series": [{
        "name": "Fill weight (g)",
        "points": [{"x": index + 1, "y": value} for index, value in enumerate(_FILL_WEIGHTS)],
    }],
}

_CONTROL_ZONES = {
    "series": [{
        "name": "Fill weight (g)",
        "points": [{"x": index + 1, "y": value} for index, value in enumerate(_FILL_WEIGHTS)],
    }],
    "control_limits": [
        {"ucl": 503.6, "lcl": 496.6, "cl": 500.1, "label": "3 sigma"},
        {"ucl": 502.4, "lcl": 497.8, "label": "2 sigma"},
        {"ucl": 501.3, "lcl": 498.9, "label": "1 sigma"},
    ],
}

_CONTROL_WEEKDAYS = {
    "series": [{
        "name": "Tickets per hour",
        "points": [
            {"x": "Mon", "y": 42}, {"x": "Tue", "y": 38}, {"x": "Wed", "y": None},
            {"x": "Thu", "y": 45}, {"x": "Fri", "y": 61, "ooc": True}, {"x": "Sat", "y": 22},
            {"x": "Sun", "y": 19},
        ],
    }],
    "control_limits": {"ucl": 70, "lcl": 10, "cl": 40},
}

_RUN_WEEKS = {
    "series": [{
        "name": "Deploys per week",
        "points": [
            {"x": f"W{week}", "y": value}
            for week, value in enumerate([6, 8, 7, None, 9, 5, 8, 7, 10, 6, 9, 8], start=1)
        ],
    }],
    "reference_lines": [{"label": "Goal 8", "value": 8}, {"label": "Floor 5", "value": 5}],
}


def _roc_dense():
    """
        An 81-point ROC curve in percent, so markers are off by default.

        :returns: The chart data.
    """
    points = []
    for step in range(0, 81):
        fpr = step * 1.25
        tpr = 100.0 * (1.0 - (1.0 - fpr / 100.0) ** 3.2)
        points.append({"x": round(fpr, 2), "y": round(tpr, 2)})
    result = {"series": [{"name": "Fraud model (%)", "points": points}]}
    return result


_PR_TWO = {
    "series": [
        {"name": "Transformer", "points": [
            {"x": 0.0, "y": 1.0}, {"x": 0.2, "y": 0.95}, {"x": 0.4, "y": 0.9},
            {"x": 0.6, "y": 0.82}, {"x": 0.8, "y": 0.66}, {"x": 1.0, "y": 0.3},
        ]},
        {"name": "Bag of words", "points": [
            {"x": 0.0, "y": 1.0}, {"x": 0.2, "y": 0.84}, {"x": 0.4, "y": 0.72},
            {"x": 0.6, "y": 0.6}, {"x": 0.8, "y": 0.47}, {"x": 1.0, "y": 0.3},
        ]},
    ],
}

_GAINS_DATA = {
    "series": [{
        "name": "Churn model",
        "points": [
            {"x": 0.0, "y": 0.0}, {"x": 0.1, "y": 0.34}, {"x": 0.2, "y": 0.55},
            {"x": 0.3, "y": 0.69}, {"x": 0.4, "y": 0.79}, {"x": 0.5, "y": 0.86},
            {"x": 0.6, "y": 0.91}, {"x": 0.8, "y": 0.97}, {"x": 1.0, "y": 1.0},
        ],
    }],
}

_LIFT_PERCENT = {
    "series": [
        {"name": "Model A", "points": [
            {"x": decile * 10, "y": lift}
            for decile, lift in enumerate([3.6, 3.2, 2.6, 2.1, 1.8, 1.5, 1.35, 1.2, 1.1, 1.0], start=1)
        ]},
        {"name": "Model B", "points": [
            {"x": decile * 10, "y": lift}
            for decile, lift in enumerate([2.4, 2.1, 1.9, 1.7, 1.5, 1.35, 1.25, 1.15, 1.05, 1.0], start=1)
        ]},
    ],
}

_CALIBRATION_TWO = {
    "series": [
        {"name": "Calibrated", "points": [
            {"x": 0.1, "y": 0.09}, {"x": 0.3, "y": 0.31}, {"x": 0.5, "y": 0.48},
            {"x": 0.7, "y": 0.71}, {"x": 0.9, "y": 0.88},
        ]},
        {"name": "Over-confident", "points": [
            {"x": 0.1, "y": 0.22}, {"x": 0.3, "y": 0.36}, {"x": 0.5, "y": 0.5},
            {"x": 0.7, "y": 0.62}, {"x": 0.9, "y": 0.74},
        ]},
    ],
}

_SURVIVAL_DATES = {
    "series": [{
        "name": "Subscribers retained (%)",
        "points": [
            {"x": "2025-01-01", "y": 100, "at_risk": 500},
            {"x": "2025-02-01", "y": 91, "at_risk": 455},
            {"x": "2025-03-01", "y": 84, "at_risk": 418},
            {"x": "2025-03-20", "y": 84, "censored": True},
            {"x": "2025-04-01", "y": 79, "at_risk": 380},
            {"x": "2025-06-01", "y": 71, "at_risk": 331},
            {"x": "2025-08-01", "y": 66, "at_risk": 296},
            {"x": "2025-09-15", "y": 66, "censored": True},
        ],
    }],
}

_FOREST_DIFF = {
    "series": [{
        "name": "Mean change in HbA1c (%)",
        "groups": [
            {"category": "Trial A (2019)", "value": -0.42, "error_low": 0.18, "error_high": 0.18, "weight": 4.1},
            {"category": "Trial B (2020)", "value": -0.31, "error_low": 0.22, "error_high": 0.22, "weight": 3.0},
            {"category": "Trial C (2021)", "value": -0.55, "error_low": 0.12, "error_high": 0.12, "weight": 6.2},
            {"category": "Trial D (2023)", "value": 0.05, "error_low": 0.3, "error_high": 0.3, "weight": 1.8},
        ],
    }],
    "pooled": {"value": -0.41, "ci_lower": -0.52, "ci_upper": -0.3, "label": "Pooled"},
}

_FOREST_ARROW = {
    "series": [{
        "name": "Hazard ratio",
        "groups": [
            {"category": "Cohort 1", "value": 0.8, "error_low": 0.2, "error_high": 0.3, "weight": 4},
            {"category": "Cohort 2 (small)", "value": 0.6, "error_low": 0.7, "error_high": 1.4, "weight": 1},
            {"category": "Cohort 3", "value": 1.1, "error_low": 0.25, "error_high": 0.35, "weight": 3},
        ],
    }],
}

_FUNNEL_LOGOR = {
    "series": [{
        "name": "Log odds ratio",
        "points": [
            {"x": -0.35, "y": 0.08, "label": "Ortiz 2017"},
            {"x": -0.2, "y": 0.12, "label": "Novak 2018"},
            {"x": -0.42, "y": 0.15, "label": "Adeyemi 2019"},
            {"x": -0.05, "y": 0.2, "label": "Sato 2020"},
            {"x": -0.6, "y": 0.27, "label": "Haddad 2021"},
            {"x": -0.75, "y": 0.33, "label": "Berg 2021"},
            {"x": -0.28, "y": 0.1, "label": "Moreau 2022"},
            {"x": -0.9, "y": 0.38, "label": "Kowal 2023"},
        ],
    }],
    "funnel": {"summary_effect": -0.31},
}


def _dense_candles():
    """
        400 deterministic daily sessions (merged into wider bars on screen).

        :returns: The chart data.
    """
    import datetime as _datetime
    candles = []
    price = 100.0
    day = _datetime.date(2024, 1, 1)
    while len(candles) < 400:
        if day.weekday() < 5:
            index = len(candles)
            drift = ((index * 37) % 11 - 5) * 0.35
            open_price = price
            close_price = round(price + drift, 2)
            high = round(max(open_price, close_price) + 0.4 + (index % 3) * 0.3, 2)
            low = round(min(open_price, close_price) - 0.4 - (index % 4) * 0.25, 2)
            candles.append({
                "t": day.isoformat(), "o": round(open_price, 2), "h": high, "l": low,
                "c": close_price, "v": 1000000 + (index * 7919) % 600000,
            })
            price = close_price
        day = day + _datetime.timedelta(days=1)
    result = {"candles": candles}
    return result


_VOLUME_ONLY = {"candles": [{"t": candle["t"], "v": candle["v"]} for candle in _CANDLES]}

_PYRAMID_DATA = {
    "baseline": 0,
    "low_label": "Male",
    "high_label": "Female",
    "series": [{
        "name": "Population (thousands)",
        "values": [
            {"label": "80+", "low": 142, "high": 231},
            {"label": "60-79", "low": 610, "high": 668},
            {"label": "40-59", "low": 802, "high": 795},
            {"label": "20-39", "low": 760, "high": 741},
            {"label": "0-19", "low": 690, "high": 655},
        ],
    }],
}

_TORNADO_EDGE = {
    "baseline": 120,
    "series": [{
        "name": "NPV (k€)",
        "values": [
            {"label": "Energy price", "low": 80, "high": 165},
            {"label": "Subsidy", "high": 150},
            {"label": "Maintenance", "low": 135, "high": 104},
            {"label": "Interest rate", "low": "n/a", "high": 112},
        ],
    }],
}

_GANTT_MIXED = {
    "tasks": [
        {"id": "kick", "label": "Kick-off", "start": "2025-03-03", "group": "Milestones"},
        {"id": "research", "label": "User research", "start": "2025-03", "end": "2025-04",
         "progress": 0.6, "group": "Discovery", "assignee": "Priya"},
        {"id": "spec", "label": "Specification", "start": "2025-04-14", "end": "2025-05-02",
         "group": "Discovery", "depends": ["research"]},
        {"id": "budget", "label": "Budget approval", "group": "Discovery"},
        {"id": "gate", "label": "Go / no-go", "start": "2025-05-05", "end": "2025-05-05",
         "group": "Milestones", "depends": ["spec"]},
    ]
}

_ROADMAP_MONTHS = {
    "tasks": [
        {"id": "a", "label": "Billing revamp", "start": "2025-01", "end": "2025-03",
         "status": "completed", "group": "Payments"},
        {"id": "b", "label": "Wallet support", "start": "2025-03", "end": "2025-06",
         "status": "in-progress", "group": "Payments"},
        {"id": "c", "label": "Fraud scoring", "start": "2025-05", "end": "2025-08",
         "status": "at-risk", "group": "Risk"},
        {"id": "d", "label": "Dispute portal", "start": "2025-08", "end": "2025-11",
         "status": "planned", "group": "Risk"},
    ]
}

_TIMELINE_LANES = {
    "events": [
        {"id": "a", "label": "Design freeze", "date": "2025-02-03", "group": "Product",
         "status": "completed", "icon": "✓", "description": "All screens signed off."},
        {"id": "b", "label": "API beta", "date": "2025-03-17", "group": "Engineering",
         "status": "completed"},
        {"id": "c", "label": "Load test", "date": "2025-04-22", "group": "Engineering",
         "status": "at-risk", "icon": "!", "description": "Waiting for the staging cluster."},
        {"id": "d", "label": "Press briefing", "date": "2025-05-12", "group": "Marketing",
         "status": "planned"},
        {"id": "e", "label": "Launch", "date": "2025-06-02", "group": "Product",
         "status": "planned", "icon": "★"},
        {"id": "f", "label": "Campaign", "date": "2025-06-09", "group": "Marketing",
         "status": "planned"},
    ]
}

_KANBAN_BUSY = {
    "columns": [
        {"name": "To do", "items": [
            {"id": f"OPS-{number}", "label": f"Rotate credentials batch {number}",
             "priority": "medium"}
            for number in range(1, 13)
        ]},
        {"name": "Doing", "wip-limit": 2, "items": [
            {"id": "OPS-20", "label": "Patch kernel on db hosts", "priority": "critical",
             "assignee": "Dave"},
            {"id": "OPS-21", "label": "Renew TLS certificates", "priority": "high",
             "assignee": "Eve"},
            {"id": "OPS-22", "label": "Tune autoscaler", "priority": "low"},
        ]},
        {"name": "Done", "items": [
            {"id": "OPS-10", "label": "Backup restore drill", "priority": "high"},
        ]},
    ]
}

_RESOURCE_HOURS = {
    "resources": [
        {"id": "design", "label": "Design team", "capacity": 80, "allocations": [
            {"task": "Brand refresh", "start": "2025-06-02", "end": "2025-06-20", "load": 48},
            {"task": "App screens", "start": "2025-06-09", "end": "2025-06-27", "load": 40},
        ]},
        {"id": "web", "label": "Web team", "capacity": 120, "allocations": [
            {"task": "Checkout", "start": "2025-06-02", "end": "2025-06-27", "load": 70},
            {"task": "Search", "start": "2025-06-16", "end": "2025-06-27", "load": 40},
        ]},
        {"id": "data", "label": "Data team", "capacity": 60, "allocations": [
            {"task": "Warehouse migration", "start": "2025-06-02", "end": "2025-06-13", "load": 55},
            {"task": "Dashboards", "start": "2025-06-16", "end": "2025-06-27", "load": 30},
        ]},
    ]
}

_GANTT_PLAN = {
    "groups": [{"id": "api", "label": "API team"}, {"id": "web", "label": "Web team"}],
    "tasks": [
        {"id": "kick", "label": "Kick-off", "start": "2026-03-02", "milestone": True},
        {"id": "support", "label": "Support rotation", "start": "2026-03-02"},
        {"id": "schema", "label": "Schema", "start": "2026-03-02", "end": "2026-03-13", "progress": 1,
         "group": "api", "status": "done"},
        {"id": "endpoints", "label": "Endpoints", "start": "2026-03-16", "end": "2026-04-03",
         "progress": 0.5, "group": "api", "depends": ["schema"]},
        {"id": "screens", "label": "Screens", "start": "2026-03-09", "end": "2026-04-10",
         "progress": 0.3, "group": "web"},
        {"id": "migrate", "label": "Data migration", "start": "2026-05-04", "end": "2026-05-15",
         "group": "web"},
    ],
    "markers": [{"label": "Beta", "date": "2026-04-13"}],
    "phases": [{"label": "Build", "start": "2026-03-02", "end": "2026-04-10"}],
}

_ROADMAP_LANES = {
    "groups": [{"id": "platform", "label": "Platform"}, {"id": "mobile", "label": "Mobile"}],
    "tasks": [
        {"id": "sso", "label": "Single sign-on", "start": "2026-01-12", "end": "2026-03-20",
         "status": "done", "group": "platform"},
        {"id": "gateway", "label": "API gateway", "start": "2026-02-02", "end": "2026-05-29",
         "status": "in-progress", "group": "platform", "progress": 0.4},
        {"id": "audit", "label": "Audit log", "start": "2026-04-06", "end": "2026-06-26",
         "status": "planned", "group": "platform"},
        {"id": "ios", "label": "iOS redesign", "start": "2026-01-19", "end": "2026-04-30",
         "status": "at-risk", "group": "mobile", "description": "Waiting on design tokens."},
        {"id": "widgets", "label": "Widgets", "start": "2026-05-04", "end": "2026-08-28",
         "status": "blocked", "group": "mobile"},
        {"id": "tablet", "label": "Tablet layout", "start": "2026-06-01", "end": "2026-07-31",
         "status": "planned", "group": "design"},
        {"id": "dark", "label": "Dark theme", "status": "planned", "group": "mobile"},
    ],
    "markers": [{"label": "GA", "date": "2026-05-15"}],
    "phases": [{"label": "Planning", "start": "2026-01-05", "end": "2026-01-30"}],
}

_ROADMAP_BUCKETS = {
    "groups": [{"id": "growth", "label": "Growth"}, {"id": "core", "label": "Core"}],
    "buckets": [{"id": "now", "label": "Now"}, {"id": "next", "label": "Next"},
                {"id": "later", "label": "Later"}],
    "tasks": [
        {"label": "Referrals", "group": "growth", "bucket": "now", "status": "in-progress"},
        {"label": "Pricing test", "group": "growth", "bucket": "now", "status": "done"},
        {"label": "Partner portal", "group": "growth", "bucket": "later", "status": "planned"},
        {"label": "Search rewrite", "group": "core", "bucket": "next", "status": "at-risk"},
        {"label": "Moonshot", "group": "core", "bucket": "someday", "status": "planned"},
    ],
}

_MILESTONE_KINDS = {
    "events": [
        {"id": "a", "label": "Alpha", "date": "2026-01-19", "kind": "tag"},
        {"id": "b", "label": "Feature freeze", "date": "2026-02-20", "kind": "freeze",
         "description": "No new features after this date."},
        {"id": "c", "label": "Release candidate", "date": "2026-03-06", "kind": "tag"},
        {"id": "d", "label": "1.0", "date": "2026-03-23", "kind": "release"},
        {"id": "e", "label": "Retro", "date": "2026-03-27", "kind": "milestone"},
    ],
    "phases": [{"label": "Hardening", "start": "2026-02-20", "end": "2026-03-20"}],
}

#: Script of the gantt "today" example: tasks around the current date.
_GANTT_TODAY_SCRIPT = (
    'const chart = document.getElementById("today-chart")\n'
    'const day = 24 * 60 * 60 * 1000\n'
    'const iso = (offset) => new Date(Date.now() + offset * day).toISOString().slice(0, 10)\n'
    'chart.data = {\n'
    '  tasks: [\n'
    '    { id: "build", label: "Build", start: iso(-20), end: iso(-3), progress: 1, group: "Sprint" },\n'
    '    { id: "test", label: "Test", start: iso(-6), end: iso(8), progress: 0.4, group: "Sprint", depends: ["build"] },\n'
    '    { id: "ship", label: "Ship", start: iso(10), end: iso(12), group: "Sprint", depends: ["test"] },\n'
    '  ]\n'
    '}\n'
    'mjSandbox.log("tasks placed around today", { today: iso(0) })\n'
)


# ---------------------------------------------------------------------------
# Option documentation shared by renderer families
# ---------------------------------------------------------------------------

def _errorbar_options(type_key):
    """
        The errorbar / confidence-interval options.

        :returns: A list of AttributeDoc.
    """
    is_ci = type_key == "confidence-interval"
    options = [
        AttributeDoc(name="cap-width", description="Width of the whisker end caps in px.",
                     kind="number", default="8"),
        AttributeDoc(
            name="null-value",
            description=(
                "Value of the dashed reference line (always drawn and kept in view)."
                if is_ci else
                "Draws a dashed reference line at this value (none when absent)."
            ),
            kind="number",
            default="0" if is_ci else None,
        ),
        orientation_option(
            "horizontal" if is_ci else "vertical",
            "vertical: categories along x; horizontal: categories down the y axis.",
        ),
    ]
    return options


_MARKERS = AttributeDoc(
    name="markers",
    description=("Point markers: `auto` shows them for series of up to 50 points; a bare `markers` is "
                 "`true`. Without visible markers every point keeps an invisible mark that appears on "
                 "hover or focus, so the curve stays keyboard reachable and clickable."),
    kind="enum",
    values=["auto", "true", "false"],
    default="auto",
)

_SHADE_AUC = boolean_option("shade-auc", "Fills the area under the curve.")

_SURVIVAL_OPTIONS = [
    boolean_option("ci", "Shades the stepped confidence band from `ci_lower` / `ci_upper`."),
    boolean_option("at-risk", "Adds the numbers-at-risk table under the plot from `at_risk`."),
    AttributeDoc(name="mode", description="`cumulative` draws the cumulative incidence 1 - S(t).",
                 kind="enum", values=["cumulative"]),
]


def _price_options(type_key):
    """
        The ohlc / candlestick options.

        :returns: A list of AttributeDoc.
    """
    options = [
        AttributeDoc(
            name="variant",
            description="ohlc: high-low line with open / close ticks; candle: bodies and wicks.",
            kind="enum",
            values=["ohlc", "candle"],
            default="ohlc" if type_key == "ohlc" else "candle",
        ),
    ]
    return options


def _gantt_options(type_key):
    """
        The gantt / roadmap options.

        :returns: A list of AttributeDoc.
    """
    options = [
        AttributeDoc(
            name="variant",
            description=(
                "gantt: one row per task with progress fills and dependency arrows; roadmap: "
                "one lane per group with stacked status-coloured bars under period or bucket "
                "columns."
            ),
            kind="enum",
            values=["gantt", "roadmap"],
            default=type_key,
        ),
        boolean_option("today", "Dashed today marker (drawn when today is in range); `today=\"false\"` "
                       "hides it.", True),
        AttributeDoc(name="start-date", description="Fixes the start of the time axis (`YYYY-MM-DD`, "
                     "`YYYY-MM`, `YYYY-Qn` or ISO); without it the axis follows the tasks.", kind="string"),
        AttributeDoc(name="end-date", description="Fixes the end of the time axis (a calendar end is "
                     "inclusive). A task outside the window shows an edge arrow (gantt) or is listed as "
                     "not placed (roadmap).", kind="string"),
        AttributeDoc(name="density", description="`compact`: shorter rows (gantt) or thinner bars (roadmap).",
                     kind="enum", values=["normal", "compact"], default="normal"),
    ]
    if type_key == "gantt":
        options.extend([
            AttributeDoc(name="scale", description="Tick unit of the axis; the step still grows when "
                         "there is no room. Without it the ticks are chosen to fit.", kind="enum",
                         values=["day", "week", "month", "quarter"]),
            boolean_option("show-progress", "Progress fills; `false` hides them.", True),
            boolean_option("show-dependencies", "Dependency arrows; `false` hides them.", True),
            AttributeDoc(name="row-height", description="Minimum row height in px (rows stretch up to "
                         "half as much again to fill a taller chart).", kind="number", default="32"),
            AttributeDoc(name="collapsed-groups", description="JSON array (or comma list) of the "
                         "collapsed group ids; activating a group header updates it.", kind="json"),
        ])
    else:
        options.extend([
            AttributeDoc(name="mode", description="`bucket` places tasks in the `buckets` columns by "
                         "their `bucket`; `calendar` by their dates.", kind="enum",
                         values=["calendar", "bucket"], default="calendar"),
            AttributeDoc(name="scale", description="Calendar column period.", kind="enum",
                         values=["quarter", "month", "half-year"], default="quarter"),
        ])
    return options


_GANTT_EVENTS = [
    ("mj-chart-bar-click", "A task bar was activated (click, Enter or Space).",
     "{ id, label, start, end, index: number }"),
    ("mj-chart-marker-click", "A milestone marker was activated.", "{ label, date, index: number }"),
    ("mj-chart-group-toggle", "A group header was activated (gantt); the chart's `collapsed-groups` "
     "attribute already holds the new set.", "{ group: string, collapsed: boolean, collapsedGroups: string[] }"),
]


def _timeline_options(type_key):
    """
        The timeline / milestone options.

        :returns: A list of AttributeDoc.
    """
    options = [
        AttributeDoc(
            name="variant",
            description="timeline: circle markers; milestone: diamond markers (an event's `kind` wins).",
            kind="enum",
            values=["timeline", "milestone"],
            default=type_key,
        ),
        orientation_option(
            "horizontal",
            "horizontal: time runs left to right; vertical: time runs down the page.",
        ),
        boolean_option("today", "Dashed today line (drawn when today is in range); `today=\"false\"` "
                       "hides it.", True),
        AttributeDoc(name="start-date", description="Fixes the start of the time axis; earlier events "
                     "are listed in the table but not drawn.", kind="string"),
        AttributeDoc(name="end-date", description="Fixes the end of the time axis (a `YYYY-MM-DD` end is "
                     "inclusive); later events are listed in the table but not drawn.", kind="string"),
        boolean_option("dim-past", "Draws events more than a day before today faded and adds past / "
                       "today / upcoming to each marker's accessible name."),
        AttributeDoc(name="density", description="`compact`: smaller labels, cut at about 12 characters.",
                     kind="enum", values=["normal", "compact"], default="normal"),
    ]
    return options


_TIMELINE_EVENTS = [
    ("mj-chart-event-click", "A marker was activated (click, Enter or Space).",
     "{ id, label, date, group, status, kind, index: number }"),
]


_SERIES_POINTS_SHAPE = (
    "<pre><code>{\n"
    "  series: [{ name: string, points: [{ x: number, y: number, n?: number }] }]\n"
    "}</code></pre>"
)

_GROUPS_SHAPE = (
    "<pre><code>{\n"
    "  series: [{\n"
    "    name: string,\n"
    "    groups: [{ category: string, value: number, error_low: number, error_high: number,\n"
    "               bar?: boolean }]\n"
    "  }]\n"
    "}</code></pre>"
)

_CONTROL_SHAPE = (
    "<pre><code>{\n"
    "  series: [{ name: string, points: [{ x: number | string, y: number | null, ooc?: boolean }] }],\n"
    "  control_limits?: { ucl?: number, lcl?: number, cl?: number, label?: string }\n"
    "                   | [ ...one set per sigma zone ],\n"
    "  reference_lines?: [{ label: string, value: number }]\n"
    "}</code></pre>"
)

_SURVIVAL_SHAPE = (
    "<pre><code>{\n"
    "  series: [{\n"
    "    name: string,\n"
    "    points: [{ x: number | string, y: number, censored?: boolean,\n"
    "               ci_lower?: number, ci_upper?: number, at_risk?: number }]\n"
    "  }]\n"
    "}</code></pre>"
    "<ul>"
    "<li><code>x</code>: time, a number or a date (<code>YYYY-MM-DD</code> is a local day).</li>"
    "<li><code>y</code>: survival probability 0-1 (a series above 1 is read as percent).</li>"
    "<li><code>censored</code>: a tick, no step. <code>ci_lower</code> / <code>ci_upper</code>: "
    "band with <code>ci=\"true\"</code>. <code>at_risk</code>: the at-risk table and tooltips.</li>"
    "</ul>"
)

_CANDLES_SHAPE = (
    "<pre><code>{\n"
    "  candles: [{ t: string | number, o: number, h: number, l: number, c: number, v?: number }]\n"
    "}</code></pre>"
    "<ul>"
    "<li><code>t</code>: <code>YYYY-MM-DD</code> (local day), ISO date-time or epoch ms; a "
    "candle without a usable date is skipped.</li>"
    "<li><code>o</code> / <code>h</code> / <code>l</code> / <code>c</code>: prices (numeric "
    "strings accepted).</li>"
    "<li><code>v</code>: volume, not drawn here (see <code>volume</code>).</li>"
    "</ul>"
)

_TASKS_SHAPE = (
    "<pre><code>{\n"
    "  tasks: [{ id: string, label: string, start?: string, end?: string, progress?: number,\n"
    "            assignee?: string, group?: string, depends?: string[], status?: string,\n"
    "            milestone?: boolean, bucket?: string, description?: string }],\n"
    "  groups?: [{ id: string, label: string }],\n"
    "  markers?: [{ label: string, date: string }],\n"
    "  phases?: [{ label: string, start: string, end: string }],\n"
    "  buckets?: [{ id: string, label: string }]      // roadmap, mode=\"bucket\"\n"
    "}</code></pre>"
    "<ul>"
    "<li><code>start</code> / <code>end</code>: <code>YYYY-MM-DD</code> (local day, end "
    "inclusive), <code>YYYY-MM</code> (whole month), <code>YYYY-Qn</code> (whole quarter), "
    "ISO date-time or epoch ms.</li>"
    "<li>A start and no end: the bar runs to the edge of the chart (dashed); "
    "<code>milestone: true</code>, a zero-length span or an end only: a diamond; no dates: "
    "the row is kept and marked No dates.</li>"
    "<li><code>groups</code> gives the order and names of the groups (gantt header rows, "
    "roadmap lanes); a task names its group by id or label. Without <code>groups</code> the "
    "groups come from the tasks; with them a task naming another group is ungrouped "
    "(roadmap: the Unassigned lane).</li>"
    "<li><code>progress</code> 0-1, <code>depends</code> = predecessor ids (gantt); "
    "<code>status</code> = planned, in-progress, completed / done, at-risk, blocked (roadmap "
    "colour and icon).</li>"
    "</ul>"
)

_EVENTS_SHAPE = (
    "<pre><code>{\n"
    "  events: [{ id?: string, label: string, date: string | number, group?: string,\n"
    "             status?: 'completed' | 'active' | 'planned' | 'at-risk',\n"
    "             kind?: 'release' | 'freeze' | 'tag' | 'milestone',\n"
    "             icon?: string, description?: string }],\n"
    "  phases?: [{ label: string, start: string, end: string }]\n"
    "}</code></pre>"
    "<ul>"
    "<li><code>group</code>: one lane per distinct group.</li>"
    "<li><code>kind</code>: the marker shape (release diamond, freeze triangle, tag and "
    "milestone circle) and, without a <code>status</code>, its colour.</li>"
    "<li><code>phases</code>: background bands (end inclusive).</li>"
    "<li><code>icon</code>: short glyph before the label; <code>description</code>: tooltip "
    "and table.</li>"
    "<li>Events without a usable date are listed in the table but not drawn.</li>"
    "</ul>"
)


# ---------------------------------------------------------------------------
# Catalog
# ---------------------------------------------------------------------------

CHART_TYPES = [
    # ------------------------------------------------------------------
    # STATISTICAL
    # ------------------------------------------------------------------
    ChartTypeDoc(
        type_key="errorbar",
        title="Error Bar",
        category="statistical",
        summary=(
            "Point estimates with asymmetric error whiskers per category; "
            "several series sit side by side, optionally as bars from zero."
        ),
        description=(
            "Each group entry has a category, a central value and positive half-widths "
            "error_low and error_high, so the whiskers run from value minus error_low to "
            "value plus error_high. bar true on an entry draws its value as a bar from "
            "zero and the axis then includes zero. null-value adds a dashed reference "
            "line, cap-width sizes the whisker caps and orientation horizontal puts the "
            "categories on the y axis. Several series sit side by side; the legend toggles "
            "them. Numeric strings are accepted; an entry without a numeric value is "
            "skipped and a missing error counts as zero."
        ),
        data_shape=(
            _GROUPS_SHAPE
            + "<ul>"
            "<li><code>error_low</code> / <code>error_high</code>: positive half-widths below "
            "and above <code>value</code>.</li>"
            "<li><code>bar</code>: draw the value as a bar from zero.</li>"
            "</ul>"
        ),
        options=_errorbar_options("errorbar"),
        examples=[
            basic_example(_chart("errorbar", _ERRORBAR_DATA, legend=True),
                          "<p>Treatment against control over six weeks, with asymmetric whiskers.</p>"),
            gallery_example(
                "bars",
                "Bars from zero",
                "<p><code>bar: true</code> on every entry and <code>null-value=\"200\"</code> for the "
                "latency target line.</p>",
                chart_markup("errorbar", _LATENCY_BARS, label="Latency by region",
                             attrs={"null-value": "200"}),
            ),
            gallery_example(
                "horizontal",
                "Horizontal, wide caps",
                "<p><code>orientation=\"horizontal\"</code> and <code>cap-width=\"14\"</code>.</p>",
                chart_markup("errorbar", _ERRORBAR_DATA, label="Response by week",
                             attrs={"orientation": "horizontal", "cap-width": "14"},
                             style="height:320px", legend=True),
            ),
            events_example(
                "errorbar", _ERRORBAR_DATA, ["mj-chart-errorbar-click"], "[part=errorbar]",
                legend=True,
                description=(
                    "<p><code>mj-chart-errorbar-click</code> reports the series, category, value "
                    "and the whisker ends (<code>low</code>, <code>high</code>).</p>"
                ),
            ),
        ],
    ),
    ChartTypeDoc(
        type_key="confidence-interval",
        title="Confidence Interval",
        category="statistical",
        summary=(
            "Horizontal interval plot of estimates and their confidence "
            "intervals against a dashed no-effect line."
        ),
        description=(
            "Same data as errorbar (error_low and error_high are positive half-widths) "
            "but drawn horizontally by default, as intervals only (no bars), with a "
            "reference line at null-value (default 0) that is always in view. An interval "
            "that crosses the line is not significant at its level. orientation vertical "
            "draws columns."
        ),
        data_shape=_GROUPS_SHAPE + "<p><code>bar</code> is ignored: intervals only.</p>",
        options=_errorbar_options("confidence-interval"),
        examples=[
            basic_example(_chart("confidence-interval", _CI_DATA),
                          "<p>Blood-pressure change by subgroup; the diabetic interval crosses 0.</p>"),
            gallery_example(
                "vertical",
                "Vertical",
                "<p><code>orientation=\"vertical\"</code>: one column per subgroup.</p>",
                chart_markup("confidence-interval", _CI_DATA, label="Mean difference by subgroup",
                             attrs={"orientation": "vertical"}),
            ),
            gallery_example(
                "ratio",
                "Ratios around 1",
                "<p>Odds ratios with <code>null-value=\"1\"</code>: Diet score crosses the line.</p>",
                chart_markup("confidence-interval", _ODDS_DATA, label="Risk factors (odds ratio)",
                             attrs={"null-value": "1"}),
            ),
            events_example(
                "confidence-interval", _CI_DATA, ["mj-chart-errorbar-click"], "[part=errorbar]",
                description="<p>Intervals emit <code>mj-chart-errorbar-click</code> with their bounds.</p>",
            ),
        ],
    ),
    ChartTypeDoc(
        type_key="control-chart",
        title="Control Chart",
        category="statistical",
        summary=(
            "Statistical process control chart with UCL / CL / LCL lines; "
            "points beyond the limits are flagged automatically."
        ),
        description=(
            "Process values in time order with control limits. x may be a number, a date "
            "(YYYY-MM-DD is a local day) or a label such as Mon; the axis follows. A null y "
            "is a gap in the line. control_limits is one set of ucl, lcl and cl or an array "
            "of sets for sigma zones; each limit is drawn on its own. A point beyond the "
            "outermost limits, or with ooc true, is drawn as a red diamond. Without "
            "control_limits, or with limits auto, the individuals-chart limits are "
            "computed from the first series: CL is the mean and UCL / LCL are CL plus or "
            "minus 2.66 times the average moving range."
        ),
        data_shape=(
            _CONTROL_SHAPE
            + "<ul>"
            "<li><code>x</code>: number, date or label; <code>y</code>: number or "
            "<code>null</code> (gap).</li>"
            "<li><code>ooc</code>: flag a point as out of control.</li>"
            "<li><code>control_limits</code>: one set, or an array (sigma zones).</li>"
            "</ul>"
        ),
        options=[
            AttributeDoc(name="limits", description="`auto` computes I-MR limits instead of using `control_limits`.",
                         kind="enum", values=["auto"]),
        ],
        examples=[
            basic_example(_chart("control-chart", _CONTROL_CHART_DATA, legend=True),
                          "<p>Daily defect rate on a calendar axis; one point is above the UCL.</p>"),
            gallery_example(
                "auto-limits",
                "Computed limits",
                "<p>No <code>control_limits</code> in the data: CL, UCL and LCL are computed "
                "from the fill weights, and points beyond them are flagged.</p>",
                chart_markup("control-chart", _CONTROL_AUTO, label="Fill weight", legend=True),
            ),
            gallery_example(
                "sigma-zones",
                "Sigma zones",
                "<p><code>control_limits</code> as an array of three labelled sets.</p>",
                chart_markup("control-chart", _CONTROL_ZONES, label="Fill weight with zones",
                             style="height:300px", legend=True),
            ),
            gallery_example(
                "labels-and-gaps",
                "Label axis, gap, ooc",
                "<p>Weekday labels on x, Wednesday's <code>null</code> is a gap and Friday is flagged "
                "with <code>ooc: true</code>.</p>",
                chart_markup("control-chart", _CONTROL_WEEKDAYS, label="Support tickets", legend=True),
            ),
            events_example(
                "control-chart", _CONTROL_CHART_DATA, ["mj-chart-point-click"], "[part=point]",
                legend=True,
                description=(
                    "<p><code>mj-chart-point-click</code> reports the series, x, y and whether the "
                    "point is out of control (<code>ooc</code>) or in a shift.</p>"
                ),
            ),
        ],
    ),
    ChartTypeDoc(
        type_key="run-chart",
        title="Run Chart",
        category="statistical",
        summary=(
            "Time-ordered line chart with its median; shifts of six or more "
            "points on one side of the median are ringed."
        ),
        description=(
            "The control-chart data, but control limits are ignored: the median of the "
            "data is computed and drawn, and every point in a run of six or more "
            "consecutive points above or below it (a shift) is ringed. reference_lines add "
            "targets or other annotations. x may be a number, date or label; a null y is a "
            "gap."
        ),
        data_shape=(
            _CONTROL_SHAPE
            + "<p><code>control_limits</code> and <code>ooc</code> are ignored.</p>"
        ),
        options=[],
        examples=[
            basic_example(_chart("run-chart", _RUN_CHART_DATA, legend=True),
                          "<p>Cycle time with its median; the last run of points below it is ringed as a shift.</p>"),
            gallery_example(
                "weeks",
                "Week labels, two targets",
                "<p>Week labels on x, a <code>null</code> week as a gap and two reference lines.</p>",
                chart_markup("run-chart", _RUN_WEEKS, label="Deploys per week", legend=True),
            ),
            gallery_example(
                "dates",
                "Dates, limits ignored",
                "<p>The control-chart data on a run chart: the limits are not drawn, the median is.</p>",
                chart_markup("run-chart", _CONTROL_CHART_DATA, label="Defect rate", legend=True),
            ),
            events_example(
                "run-chart", _RUN_CHART_DATA, ["mj-chart-point-click"], "[part=point]", legend=True,
                description="<p>Points emit <code>mj-chart-point-click</code>; <code>shift</code> is true inside a shift.</p>",
            ),
        ],
    ),
    ChartTypeDoc(
        type_key="roc",
        title="ROC Curve",
        category="statistical",
        summary=(
            "Receiver Operating Characteristic curves with the chance "
            "diagonal; the legend reports each model's AUC."
        ),
        description=(
            "Points are pairs of false positive rate (x) and true positive rate (y), as "
            "fractions or percentages: an axis whose data goes above 1 (and not above 100) "
            "is read as percent. Several series overlay on the same axes and the legend "
            "shows each area under the curve. shade-auc fills the area; markers "
            "appear for series of up to 50 points unless the markers attribute says "
            "otherwise, and without them each point is an invisible, focusable mark that "
            "shows on hover or focus (Tab, then the arrow keys). Marks are clipped to the plot."
        ),
        data_shape=(
            _SERIES_POINTS_SHAPE
            + "<ul><li><code>x</code>: false positive rate; <code>y</code>: true positive rate "
            "(0-1 or 0-100).</li></ul>"
        ),
        options=[_SHADE_AUC, _MARKERS],
        examples=[
            basic_example(_chart("roc", _ROC_DATA, height="300px", legend=True),
                          "<p>Two models against the chance diagonal; the legend shows their AUC.</p>"),
            gallery_example(
                "shaded",
                "Shaded area",
                "<p><code>shade-auc</code> fills the area under the curve.</p>",
                chart_markup("roc", {"series": [_ROC_DATA["series"][0]]}, label="Gradient boosting ROC",
                             attrs={"shade-auc": "true"}, style="height:300px", legend=True),
            ),
            gallery_example(
                "percent-dense",
                "81 points in percent",
                "<p>Rates in percent are read as such; with more than 50 points the markers are "
                "off (set <code>markers</code> to show them), but every point can still be focused "
                "with the keyboard and clicked: it shows when hovered or focused.</p>",
                chart_markup("roc", _roc_dense(), label="Fraud model ROC", style="height:300px",
                             legend=True),
            ),
            events_example(
                "roc", _ROC_DATA, ["mj-chart-point-click"], "[part=point]", legend=True,
                style="height:300px",
                description="<p>Markers emit <code>mj-chart-point-click</code> with the series, x and y.</p>",
            ),
        ],
    ),
    ChartTypeDoc(
        type_key="precision-recall",
        title="Precision-Recall Curve",
        category="statistical",
        summary=(
            "Precision vs. recall trade-off curve with the no-skill "
            "baseline at the positive prevalence."
        ),
        description=(
            "Points are recall (x) and precision (y). baseline_prevalence at the root "
            "draws the horizontal no-skill line. The legend shows the area under each "
            "curve (average precision); shade-auc true fills it. Fractions or percentages "
            "are accepted."
        ),
        data_shape=(
            "<pre><code>{\n"
            "  baseline_prevalence?: number,\n"
            "  series: [{ name: string, points: [{ x: number, y: number }] }]\n"
            "}</code></pre>"
            "<ul><li><code>x</code>: recall; <code>y</code>: precision.</li>"
            "<li><code>baseline_prevalence</code>: positive share, the no-skill line.</li></ul>"
        ),
        options=[_SHADE_AUC, _MARKERS],
        examples=[
            basic_example(
                _chart("precision-recall", _PR_DATA, attrs={"shade-auc": "true"}, height="300px",
                       legend=True),
                "<p>One model, shaded, with the no-skill line at 15% prevalence.</p>",
            ),
            gallery_example(
                "two-models",
                "Two models, no markers",
                "<p>No <code>baseline_prevalence</code>, so no baseline; <code>markers=\"false\"</code>.</p>",
                chart_markup("precision-recall", _PR_TWO, label="Spam classifiers",
                             attrs={"markers": "false"}, style="height:300px", legend=True),
            ),
            events_example(
                "precision-recall", _PR_DATA, ["mj-chart-point-click"], "[part=point]",
                legend=True, style="height:300px",
                description="<p>Markers emit <code>mj-chart-point-click</code>.</p>",
            ),
        ],
    ),
    ChartTypeDoc(
        type_key="lift",
        title="Lift Chart",
        category="statistical",
        summary=(
            "Model lift vs. population contacted, with the lift = 1 "
            "baseline of random selection; mode=\"gains\" draws cumulative gains."
        ),
        description=(
            "Points are the fraction of the population contacted (x, 0-1 or percent) and "
            "the lift (y). The y axis starts at zero so the dashed random-selection line at "
            "lift 1 is always visible. With mode gains the points are a cumulative-gains "
            "curve (fraction of positives captured) against the chance diagonal."
        ),
        data_shape=(
            _SERIES_POINTS_SHAPE
            + "<ul><li><code>x</code>: population contacted; <code>y</code>: lift (or gains "
            "with <code>mode=\"gains\"</code>).</li></ul>"
        ),
        options=[
            AttributeDoc(name="mode", description="`gains` draws a cumulative-gains chart.",
                         kind="enum", values=["gains"]),
            _MARKERS,
        ],
        examples=[
            basic_example(_chart("lift", _LIFT_DATA, height="300px"),
                          "<p>An email campaign model against the lift = 1 baseline.</p>"),
            gallery_example(
                "gains",
                "Cumulative gains",
                "<p><code>mode=\"gains\"</code>: share of churners captured against the diagonal.</p>",
                chart_markup("lift", _GAINS_DATA, label="Churn model gains", attrs={"mode": "gains"},
                             style="height:300px"),
            ),
            gallery_example(
                "percent",
                "Deciles in percent",
                "<p>Two models by decile, x in percent.</p>",
                chart_markup("lift", _LIFT_PERCENT, label="Lift by decile", style="height:300px",
                             legend=True),
            ),
            events_example(
                "lift", _LIFT_DATA, ["mj-chart-point-click"], "[part=point]", style="height:300px",
                description="<p>Markers emit <code>mj-chart-point-click</code>.</p>",
            ),
        ],
    ),
    ChartTypeDoc(
        type_key="calibration",
        title="Calibration Plot",
        category="statistical",
        summary=(
            "Mean predicted probability vs. observed fraction of positives "
            "against the perfect-calibration diagonal."
        ),
        description=(
            "Points are the mean predicted probability (x) and the observed fraction of "
            "positives (y), with an optional bucket count n. size-by n scales the dot "
            "area by n and show-histogram true adds bars of n along the bottom. The dashed "
            "diagonal marks perfect calibration."
        ),
        data_shape=(
            _SERIES_POINTS_SHAPE
            + "<ul><li><code>n</code>: bucket count, for <code>size-by</code> and the "
            "histogram.</li></ul>"
        ),
        options=[
            AttributeDoc(name="size-by", description="`n` scales each dot's area by its bucket count.",
                         kind="enum", values=["n"]),
            boolean_option("show-histogram", "Adds bars of `n` along the bottom."),
            _MARKERS,
        ],
        examples=[
            basic_example(
                _chart("calibration", _CALIBRATION_DATA,
                       attrs={"size-by": "n", "show-histogram": "true"}, height="300px"),
                "<p>Dots sized by bucket count, with the count histogram along the bottom.</p>",
            ),
            gallery_example(
                "two-models",
                "Two models",
                "<p>An over-confident model bends away from the diagonal.</p>",
                chart_markup("calibration", _CALIBRATION_TWO, label="Model calibration",
                             style="height:300px", legend=True),
            ),
            events_example(
                "calibration", _CALIBRATION_DATA, ["mj-chart-point-click"], "[part=point]",
                attrs={"size-by": "n"}, style="height:300px",
                description="<p>Dots emit <code>mj-chart-point-click</code> with their bucket count <code>n</code>.</p>",
            ),
        ],
    ),
    ChartTypeDoc(
        type_key="survival",
        title="Survival Curve",
        category="statistical",
        summary=(
            "Kaplan-Meier step functions with censoring ticks, stepped "
            "confidence bands and a numbers-at-risk table."
        ),
        description=(
            "A right-continuous step function per series: it holds each value until the "
            "next event and continues to the last observation, censored ones included. "
            "Censored observations are ticks. ci true shades the stepped confidence band "
            "and at-risk true adds the numbers-at-risk table; mode cumulative draws "
            "1 - S(t). Every event time can be focused to read S(t), the interval and the "
            "number at risk. The estimates are supplied, not computed from raw durations."
        ),
        data_shape=_SURVIVAL_SHAPE,
        options=_SURVIVAL_OPTIONS,
        examples=[
            basic_example(
                _chart("survival", _SURVIVAL_DATA, attrs={"ci": "true", "at-risk": "true"},
                       height="360px", legend=True),
                "<p>Treatment against control with confidence bands and the at-risk table.</p>",
            ),
            gallery_example(
                "cumulative",
                "Cumulative incidence",
                "<p><code>mode=\"cumulative\"</code> draws 1 - S(t), rising from 0.</p>",
                chart_markup("survival", _SURVIVAL_DATA, label="Cumulative incidence",
                             attrs={"mode": "cumulative"}, style="height:300px", legend=True),
            ),
            gallery_example(
                "dates-percent",
                "Dates and percent",
                "<p>Dated observations and survival in percent (read as such because it exceeds 1).</p>",
                chart_markup("survival", _SURVIVAL_DATES, label="Subscriber retention",
                             attrs={"at-risk": "true"}, style="height:340px", legend=True),
            ),
            events_example(
                "survival", _SURVIVAL_DATA, ["mj-chart-point-click"], "[part=event]",
                enter="click:[part=censor-tick]", legend=True, style="height:300px",
                description=(
                    "<p>Event times and censoring ticks emit <code>mj-chart-point-click</code> "
                    "(<code>censored</code>, <code>at_risk</code>). The script clicks the first "
                    "event and the last censoring tick.</p>"
                ),
            ),
        ],
    ),
    ChartTypeDoc(
        type_key="kaplan-meier",
        title="Kaplan-Meier",
        category="statistical",
        summary=(
            "Alias of survival for time-to-event analysis; same step "
            "function, censoring ticks and options."
        ),
        description=(
            "The survival renderer with the same data and options (ci, at-risk, mode "
            "cumulative). The alias makes intent explicit on clinical or epidemiological "
            "pages."
        ),
        data_shape=_SURVIVAL_SHAPE,
        options=_SURVIVAL_OPTIONS,
        examples=[
            basic_example(
                _chart("kaplan-meier", _KM_DATA, attrs={"at-risk": "true"}, height="340px",
                       legend=True),
                "<p>Stage I against stage III with the numbers at risk.</p>",
            ),
            gallery_example(
                "ci",
                "Confidence bands",
                "<p><code>ci=\"true\"</code> with <code>ci_lower</code> / <code>ci_upper</code> in the data.</p>",
                chart_markup("kaplan-meier", _SURVIVAL_DATA, label="Overall survival",
                             attrs={"ci": "true"}, style="height:300px", legend=True),
            ),
            gallery_example(
                "cumulative",
                "Cumulative incidence",
                "<p><code>mode=\"cumulative\"</code>.</p>",
                chart_markup("kaplan-meier", _KM_DATA, label="Cumulative incidence by stage",
                             attrs={"mode": "cumulative"}, style="height:300px", legend=True),
            ),
            events_example(
                "kaplan-meier", _KM_DATA, ["mj-chart-point-click"], "[part=event]",
                enter="click:[part=censor-tick]", legend=True, style="height:300px",
                description="<p>Same events as <code>survival</code>.</p>",
            ),
        ],
    ),
    ChartTypeDoc(
        type_key="forest",
        title="Forest Plot",
        category="statistical",
        summary=(
            "Meta-analysis blobbogram: per-study effect sizes with CI "
            "whiskers, weight-scaled squares and a pooled diamond."
        ),
        description=(
            "One row per study in data order: a square sized by weight at the estimate "
            "and a whisker over its confidence interval (error_low and error_high are "
            "positive half-widths). The optional pooled object adds the pooled-estimate "
            "diamond. Ratio measures (odds, hazard and risk ratios) belong on scale log, "
            "where the no-effect line is at 1; a bound at or below zero is shown as an "
            "arrow at the axis edge. Differences use the default linear scale with the "
            "line at 0; null-value moves it. Horizontal only."
        ),
        data_shape=(
            "<pre><code>{\n"
            "  series: [{ name: string,\n"
            "    groups: [{ category: string, value: number, error_low: number,\n"
            "               error_high: number, weight?: number }] }],\n"
            "  pooled?: { value: number, ci_lower: number, ci_upper: number, label: string }\n"
            "}</code></pre>"
            "<ul><li><code>weight</code>: square size.</li>"
            "<li><code>pooled</code>: the diamond, with absolute bounds.</li></ul>"
        ),
        options=[
            AttributeDoc(name="scale", description="`log` for ratio measures (no-effect line at 1).",
                         kind="enum", values=["linear", "log"], default="linear"),
            AttributeDoc(name="null-value", description="Position of the no-effect line (default 0, or 1 on a log scale).",
                         kind="number"),
        ],
        examples=[
            basic_example(_chart("forest", _FOREST_DATA, attrs={"scale": "log"}, height="300px"),
                          "<p>Hazard ratios by subgroup on a log scale with the pooled diamond.</p>"),
            gallery_example(
                "linear",
                "Differences, linear",
                "<p>Mean differences on the default linear scale; the no-effect line is at 0.</p>",
                chart_markup("forest", _FOREST_DIFF, label="HbA1c change by trial"),
            ),
            gallery_example(
                "arrow",
                "Bound below zero on log",
                "<p>Cohort 2's lower bound is below zero: on <code>scale=\"log\"</code> its whisker "
                "ends in an arrow at the axis edge.</p>",
                chart_markup("forest", _FOREST_ARROW, label="Hazard ratio by cohort",
                             attrs={"scale": "log"}, style="height:220px"),
            ),
            events_example(
                "forest", _FOREST_DATA, ["mj-chart-study-click", "mj-chart-pooled-click"],
                "[part=study]", enter="click:[part=pooled]", attrs={"scale": "log"},
                style="height:300px",
                description=(
                    "<p>Studies emit <code>mj-chart-study-click</code> (bounds and weight); the "
                    "diamond emits <code>mj-chart-pooled-click</code>.</p>"
                ),
            ),
        ],
    ),
    ChartTypeDoc(
        type_key="funnel-plot",
        title="Funnel Plot",
        category="statistical",
        summary=(
            "Publication-bias scatter: effect estimate vs. standard error "
            "with an inverted y axis and the pseudo-confidence funnel."
        ),
        description=(
            "Each study is a point at its effect estimate (x) and standard error (y, "
            "inverted: the most precise studies at the top). funnel.summary_effect draws "
            "the summary line; funnel.pseudo_ci gives the funnel edges, otherwise the 95% "
            "funnel summary plus or minus 1.96 SE is drawn. contours true shades the "
            "p < 0.05 and p < 0.01 regions around null-value (default 0, for differences "
            "and log ratios); labels true labels the studies. Not the conversion funnel "
            "type."
        ),
        data_shape=(
            "<pre><code>{\n"
            "  series: [{ name: string, points: [{ x: number, y: number, label?: string }] }],\n"
            "  funnel?: { summary_effect: number, pseudo_ci?: [{ se: number, lower: number, upper: number }] }\n"
            "}</code></pre>"
            "<ul><li><code>x</code>: effect estimate; <code>y</code>: standard error.</li>"
            "<li><code>pseudo_ci</code>: funnel bounds per SE level (default: 1.96 SE).</li></ul>"
        ),
        options=[
            boolean_option("contours", "Shades where a study would be significant at p < 0.05 and p < 0.01."),
            boolean_option("labels", "Labels each study."),
            AttributeDoc(name="null-value", description="Null effect of the contours.", kind="number",
                         default="0"),
        ],
        examples=[
            basic_example(_chart("funnel-plot", _FUNNEL_PLOT_DATA, attrs={"labels": "true"}, height="300px"),
                          "<p>Ten labelled studies inside the pseudo-confidence funnel.</p>"),
            gallery_example(
                "contours",
                "Contour-enhanced",
                "<p><code>contours=\"true\"</code> around the null effect 0 of log odds ratios; the "
                "funnel is computed from <code>summary_effect</code>.</p>",
                chart_markup("funnel-plot", _FUNNEL_LOGOR, label="Small-study effects",
                             attrs={"contours": "true"}, style="height:300px"),
            ),
            gallery_example(
                "unlabelled",
                "Computed funnel, no labels",
                "<p>Without <code>pseudo_ci</code> the 95% funnel is drawn from the summary effect.</p>",
                chart_markup("funnel-plot", {"series": _FUNNEL_PLOT_DATA["series"],
                                             "funnel": {"summary_effect": 0.82}},
                             label="Study precision", style="height:300px"),
            ),
            events_example(
                "funnel-plot", _FUNNEL_PLOT_DATA, ["mj-chart-study-click"], "[part=study]",
                style="height:300px",
                description="<p>Points emit <code>mj-chart-study-click</code> with x, y and the study label.</p>",
            ),
        ],
    ),
    # ------------------------------------------------------------------
    # FINANCIAL
    # ------------------------------------------------------------------
    ChartTypeDoc(
        type_key="ohlc",
        title="OHLC Chart",
        category="financial",
        summary=(
            "Open-High-Low-Close bars: a vertical high-low line with an "
            "open tick on the left and a close tick on the right."
        ),
        description=(
            "Each session is a vertical high-low line with the open tick on the left and "
            "the close tick on the right. Sessions sit in equal slots (no weekend gaps), "
            "the same slots the volume type uses, and dense series are merged into wider "
            "bars (first open, highest high, lowest low, last close). Rising sessions are "
            "hollow and falling ones filled, so direction is not shown by colour alone. "
            "variant candle switches to candlestick bodies."
        ),
        data_shape=_CANDLES_SHAPE,
        options=_price_options("ohlc"),
        examples=[
            basic_example(_chart("ohlc", _OHLC_DATA, legend=True), "<p>Ten trading sessions as tick bars.</p>"),
            gallery_example(
                "candle-variant",
                "Candle variant",
                "<p><code>variant=\"candle\"</code> draws bodies and wicks.</p>",
                chart_markup("ohlc", _OHLC_DATA, label="Share price", attrs={"variant": "candle"},
                             legend=True),
            ),
            gallery_example(
                "large-data",
                "400 sessions",
                "<p>More sessions than 3px slots: consecutive sessions are merged.</p>",
                chart_markup("ohlc", _dense_candles(), label="Share price, 2024-2025", legend=True),
            ),
            events_example(
                "ohlc", _OHLC_DATA, ["mj-chart-candle-click"], "[part=candle]",
                description=(
                    "<p><code>mj-chart-candle-click</code> reports t, o, h, l, c, the direction and "
                    "how many sessions the bar merges (<code>count</code>).</p>"
                ),
            ),
        ],
    ),
    ChartTypeDoc(
        type_key="candlestick",
        title="Candlestick",
        category="financial",
        summary=(
            "Japanese candlestick chart: hollow rising and filled falling "
            "bodies with wicks; same data shape as OHLC."
        ),
        description=(
            "The ohlc data drawn as candles: bodies span open to close and wicks reach the "
            "session high and low; rising bodies are hollow so direction is not shown by "
            "colour alone. variant ohlc switches to tick bars. Volume (v) is not drawn "
            "here: a volume chart of the same data at the same width lines up session by "
            "session."
        ),
        data_shape=_CANDLES_SHAPE,
        options=_price_options("candlestick"),
        examples=[
            basic_example(_chart("candlestick", _OHLC_DATA, legend=True), "<p>Ten sessions as candles.</p>"),
            gallery_example(
                "ohlc-variant",
                "OHLC variant",
                "<p><code>variant=\"ohlc\"</code> draws tick bars.</p>",
                chart_markup("candlestick", _OHLC_DATA, label="Share price", attrs={"variant": "ohlc"},
                             legend=True),
            ),
            gallery_example(
                "with-volume",
                "Price over volume",
                "<p>A candlestick chart above a volume chart of the same data: the sessions line up.</p>",
                chart_markup("candlestick", _OHLC_DATA, label="Share price", style="height:220px",
                             after=chart_markup("volume", _VOLUME_DATA, label="Volume",
                                                style="height:120px")),
            ),
            events_example(
                "candlestick", _OHLC_DATA, ["mj-chart-candle-click"], "[part=candle]",
                description="<p>Candles emit <code>mj-chart-candle-click</code>.</p>",
            ),
        ],
    ),
    ChartTypeDoc(
        type_key="volume",
        title="Volume",
        category="financial",
        summary=(
            "Trading-volume bars per session, coloured by price direction "
            "(rising / falling) or a uniform series colour."
        ),
        description=(
            "One bar per trading session from the candles data; each entry needs t and v "
            "(numbers or numeric strings). With o and c the bars follow the price "
            "direction (color-mode direction, the default; falling bars are also lighter). "
            "color-mode series uses one colour. Session slots, margins and date labels "
            "match ohlc and candlestick for a stacked price-and-volume view."
        ),
        data_shape=(
            "<pre><code>{\n"
            "  candles: [{ t: string | number, v: number, o?: number, c?: number }]\n"
            "}</code></pre>"
            "<ul><li><code>o</code> / <code>c</code>: give the direction colour; without them "
            "the bar takes the series colour.</li></ul>"
        ),
        options=[
            AttributeDoc(name="color-mode", description="direction: rising / falling colours; series: one colour.",
                         kind="enum", values=["direction", "series"], default="direction"),
        ],
        examples=[
            basic_example(_chart("volume", _VOLUME_DATA, height="200px", legend=True),
                          "<p>Volume coloured by price direction.</p>"),
            gallery_example(
                "series-colour",
                "One colour",
                "<p><code>color-mode=\"series\"</code>.</p>",
                chart_markup("volume", _VOLUME_DATA, label="Volume", attrs={"color-mode": "series"},
                             style="height:200px"),
            ),
            gallery_example(
                "volume-only",
                "Without prices",
                "<p>Entries with only <code>t</code> and <code>v</code> use the series colour.</p>",
                chart_markup("volume", _VOLUME_ONLY, label="Volume", style="height:200px"),
            ),
            events_example(
                "volume", _VOLUME_DATA, ["mj-chart-bar-click"], "[part=bar]", style="height:200px",
                description="<p><code>mj-chart-bar-click</code> reports the date, volume, open and close.</p>",
            ),
        ],
    ),
    ChartTypeDoc(
        type_key="tornado",
        title="Tornado Chart",
        category="financial",
        summary=(
            "Sensitivity analysis: paired bars diverge from a central "
            "baseline, widest impact first, with values at the bar ends."
        ),
        description=(
            "The root baseline sets the centre value. Each entry has a label and the "
            "output low and high at the input's low and high case (absolute axis values); "
            "an inverse driver such as the discount rate simply has its bars swapped. Rows "
            "are sorted widest first. low_label and high_label name the two colours in the "
            "legend. variant butterfly treats low and high as magnitudes to the left and "
            "right (a population pyramid) and keeps the data order. A missing or "
            "non-numeric side draws no bar."
        ),
        data_shape=(
            "<pre><code>{\n"
            "  baseline?: number,\n"
            "  low_label?: string, high_label?: string,\n"
            "  series: [{ name: string, values: [{ label: string, low?: number, high?: number }] }]\n"
            "}</code></pre>"
            "<ul><li><code>low</code> / <code>high</code>: output at the low / high input "
            "(magnitudes in the butterfly variant).</li></ul>"
        ),
        options=[
            AttributeDoc(name="variant", description="`butterfly`: two-sided magnitudes in data order.",
                         kind="enum", values=["butterfly"]),
        ],
        examples=[
            basic_example(_chart("tornado", _TORNADO_DATA, height="300px", legend=True),
                          "<p>Profit sensitivity to seven inputs; the discount rate is an inverse driver.</p>"),
            gallery_example(
                "butterfly",
                "Population pyramid",
                "<p><code>variant=\"butterfly\"</code> with <code>low_label</code> / "
                "<code>high_label</code> naming the sides.</p>",
                chart_markup("tornado", _PYRAMID_DATA, label="Population by age and sex",
                             attrs={"variant": "butterfly"}, style="height:280px", legend=True),
            ),
            gallery_example(
                "edge-data",
                "Missing sides",
                "<p>Subsidy has no low case and Interest rate a non-numeric one: those bars are "
                "not drawn.</p>",
                chart_markup("tornado", _TORNADO_EDGE, label="NPV sensitivity", legend=True),
            ),
            events_example(
                "tornado", _TORNADO_DATA, ["mj-chart-bar-click"], "[part=bar]", style="height:300px",
                description="<p><code>mj-chart-bar-click</code> reports the label, side, value and baseline.</p>",
            ),
        ],
    ),
    # ------------------------------------------------------------------
    # PROJECT / SCHEDULE
    # ------------------------------------------------------------------
    ChartTypeDoc(
        type_key="gantt",
        title="Gantt Chart",
        category="project",
        summary=(
            "Project schedule: task bars with progress fills, group header "
            "rows and finish-to-start dependency arrows."
        ),
        description=(
            "Task bars over a time axis with progress fills, an assignee beside the bar, a "
            "header row per group (tasks are gathered under it and coloured by it) and "
            "finish-to-start arrows from depends. A group header is a button: it collapses "
            "and expands its tasks (the chart's `collapsed-groups` attribute holds the "
            "collapsed ids). markers draw a dashed line with a diamond, phases shade the "
            "background, and a dashed line marks today when it is in range (today false "
            "hides it). YYYY-MM-DD dates are local days and the end day is inclusive; month "
            "and quarter strings are accepted. A task with a start and no end runs to the "
            "edge of the chart; a milestone task is a diamond; one without dates keeps its "
            "row, marked No dates. start-date / end-date fix the window (a task outside it "
            "shows an arrow at the edge), scale fixes the tick unit, density and row-height "
            "the rows. The chart grows to fit its rows.\n\n"
            "`<mj-gantt-chart>` is this type with the project data shape of the component "
            "family (name, percentComplete, groupId, dependencies) and a detail panel."
        ),
        data_shape=_TASKS_SHAPE,
        options=_gantt_options("gantt"),
        events=_GANTT_EVENTS,
        examples=[
            basic_example(_chart("gantt", _GANTT_DATA, height="320px", legend=True),
                          "<p>A release plan in three groups with progress and dependencies.</p>"),
            gallery_example(
                "milestones-and-undated",
                "Diamonds, months, no dates",
                "<p>One-date tasks are diamonds, <code>YYYY-MM</code> covers whole months and "
                "Budget approval has no dates.</p>",
                chart_markup("gantt", _GANTT_MIXED, label="Discovery phase", style="height:300px",
                             legend=True),
            ),
            gallery_example(
                "plan",
                "Groups, markers, phases, window",
                "<p>Declared <code>groups</code>, a <code>milestone</code> task, an open-ended "
                "task, a marker, a phase band and a window (<code>start-date</code> / "
                "<code>end-date</code>) that leaves Data migration outside: it shows an edge "
                "arrow. Activate a group header to collapse it.</p>",
                chart_markup("gantt", _GANTT_PLAN, label="Release plan", style="height:340px",
                             attrs={"start-date": "2026-03-01", "end-date": "2026-04-30", "scale": "week"},
                             legend=True),
            ),
            gallery_example(
                "today",
                "Today marker (data-driven)",
                "<p>The script sets <code>chart.data</code> with tasks around the current date, so "
                "the dashed today line shows; set <code>today</code> to false to hide it.</p>",
                chart_markup("gantt", {"tasks": []}, chart_id="today-chart", label="Current sprint",
                             style="height:220px"),
                script=_GANTT_TODAY_SCRIPT,
            ),
            gallery_example(
                "roadmap-variant",
                "Roadmap variant",
                "<p><code>variant=\"roadmap\"</code>: no progress fills or arrows.</p>",
                chart_markup("gantt", _GANTT_DATA, label="Release plan", attrs={"variant": "roadmap"},
                             style="height:320px"),
            ),
            events_example(
                "gantt", _GANTT_DATA, ["mj-chart-bar-click", "mj-chart-marker-click", "mj-chart-group-toggle"], "[part~=bar]", style="height:320px",
                description="<p><code>mj-chart-bar-click</code> reports the task id, label, start and end.</p>",
            ),
        ],
    ),
    ChartTypeDoc(
        type_key="roadmap",
        title="Roadmap",
        category="project",
        summary=(
            "Strategic roadmap: one lane per group with stacked status-coloured "
            "bars under quarter, month, half-year or bucket columns."
        ),
        description=(
            "The gantt data drawn as a roadmap: one lane per group, in which bars that do not "
            "overlap share a row and overlapping ones stack. The columns are calendar periods "
            "(scale quarter, month or half-year) covering the tasks, or with mode bucket the "
            "named buckets (a task goes in the column its bucket names). status colours the "
            "bars and adds an icon (planned, in-progress, done, at-risk, blocked); the legend "
            "names them. markers, phases (named in a row under the lanes) and the today line "
            "are drawn in calendar mode. Tasks that cannot be placed are counted in a note "
            "and listed in the table as Not placed. Quarter strings in start and end cover "
            "the whole quarter. variant gantt switches back to the gantt drawing.\n\n"
            "`<mj-roadmap-chart>` is this type with the initiative data shape of the "
            "component family (swimlanes, initiatives, buckets) and a detail panel."
        ),
        data_shape=_TASKS_SHAPE,
        options=_gantt_options("roadmap"),
        events=_GANTT_EVENTS[:2],
        examples=[
            basic_example(_chart("roadmap", _ROADMAP_DATA, height="300px", legend=True),
                          "<p>Two product lanes by quarter, coloured by status.</p>"),
            gallery_example(
                "lanes",
                "Stacked lanes, markers, phases",
                "<p>Overlapping initiatives stack in their lane, a GA marker and a planning "
                "phase, <code>scale=\"month\"</code>; Tablet layout names an undeclared group "
                "and goes to the Unassigned lane, and Dark theme has no dates, so the note "
                "counts it and the table lists it as Not placed.</p>",
                chart_markup("roadmap", _ROADMAP_LANES, label="Product roadmap", style="height:300px",
                             attrs={"scale": "month"}, legend=True),
            ),
            gallery_example(
                "buckets",
                "Now / Next / Later buckets",
                "<p><code>mode=\"bucket\"</code>: two items share the Now cell and stack; "
                "Moonshot names an unknown bucket and is counted in the note.</p>",
                chart_markup("roadmap", _ROADMAP_BUCKETS, label="Bucket roadmap", style="height:260px",
                             attrs={"mode": "bucket"}, legend=True),
            ),
            gallery_example(
                "months",
                "Month ranges",
                "<p><code>YYYY-MM</code> start and end months.</p>",
                chart_markup("roadmap", _ROADMAP_MONTHS, label="Payments roadmap", style="height:260px",
                             legend=True),
            ),
            gallery_example(
                "gantt-variant",
                "Gantt variant",
                "<p><code>variant=\"gantt\"</code> on the gantt data brings back progress and arrows.</p>",
                chart_markup("roadmap", _GANTT_DATA, label="Release plan", attrs={"variant": "gantt"},
                             style="height:320px"),
            ),
            events_example(
                "roadmap", _ROADMAP_DATA, ["mj-chart-bar-click"], "[part~=bar]", style="height:300px",
                description="<p>Bars emit <code>mj-chart-bar-click</code>.</p>",
            ),
        ],
    ),
    ChartTypeDoc(
        type_key="timeline",
        title="Timeline",
        category="project",
        summary=(
            "Event markers along a time spine; labels are placed in tiers "
            "above and below so they never overlap; one lane per group."
        ),
        description=(
            "Events as circle markers along a time spine. Labels are placed in tiers above "
            "and below the spine so they never overlap; a label with no free slot stays in "
            "the marker's tooltip. Each distinct group gets its own lane, sharing the chart "
            "height. status colours the marker (planned markers are hollow); icon adds a "
            "short glyph and description the tooltip text. kind sets the marker shape "
            "(release diamond, freeze triangle, tag and milestone circle). phases shade bands "
            "behind the markers and a dashed line marks today when it is in range. "
            "start-date / end-date fix the window, dim-past fades events before today, "
            "density compact shortens the labels. Horizontal by default; orientation "
            "vertical runs time down the page."
        ),
        data_shape=_EVENTS_SHAPE,
        options=_timeline_options("timeline"),
        events=_TIMELINE_EVENTS,
        examples=[
            basic_example(_chart("timeline", _TIMELINE_DATA, legend=True),
                          "<p>Six project events coloured by status.</p>"),
            gallery_example(
                "lanes",
                "Lanes, icons, descriptions",
                "<p>One lane per <code>group</code>; hover a marker for its description.</p>",
                chart_markup("timeline", _TIMELINE_LANES, label="Launch timeline", style="height:320px",
                             legend=True),
            ),
            gallery_example(
                "vertical",
                "Vertical",
                "<p><code>orientation=\"vertical\"</code>: labels to the right of the spine.</p>",
                chart_markup("timeline", _TIMELINE_DATA, label="Project timeline",
                             attrs={"orientation": "vertical"}, style="height:420px"),
            ),
            events_example(
                "timeline", _TIMELINE_DATA, ["mj-chart-event-click"], "[part=marker]",
                description="<p><code>mj-chart-event-click</code> reports id, label, date, group and status.</p>",
            ),
        ],
    ),
    ChartTypeDoc(
        type_key="milestone",
        title="Milestone",
        category="project",
        summary=(
            "Diamond-marker variant of the timeline for key delivery dates, "
            "funding rounds and checkpoints."
        ),
        description=(
            "The timeline layout with diamond markers for discrete one-day events; status "
            "colours follow the same mapping, and an event's kind picks its own shape and "
            "colour (release diamond, freeze triangle, tag and milestone circle). phases, the "
            "today line, the start-date / end-date window, dim-past and density work as on "
            "the timeline. variant timeline switches back to circles.\n\n"
            "`<mj-milestone-timeline>` is this type with the marker data shape of the "
            "component family (markers with name and type), dim-past on, and a detail panel."
        ),
        data_shape=_EVENTS_SHAPE,
        options=_timeline_options("milestone"),
        events=_TIMELINE_EVENTS,
        examples=[
            basic_example(_chart("milestone", _MILESTONE_DATA, legend=True),
                          "<p>Company milestones as diamonds.</p>"),
            gallery_example(
                "kinds",
                "Kinds, phases, past markers",
                "<p><code>kind</code> picks the shape and colour, a hardening phase, a fixed "
                "window and <code>dim-past</code> (every event here is past, so all are "
                "faded).</p>",
                chart_markup("milestone", _MILESTONE_KINDS, label="Release train", style="height:220px",
                             attrs={"dim-past": "", "start-date": "2026-01-05", "end-date": "2026-03-31"},
                             legend=True),
            ),
            gallery_example(
                "timeline-variant",
                "Circle markers",
                "<p><code>variant=\"timeline\"</code>.</p>",
                chart_markup("milestone", _MILESTONE_DATA, label="Company milestones",
                             attrs={"variant": "timeline"}, legend=True),
            ),
            gallery_example(
                "vertical",
                "Vertical",
                "<p><code>orientation=\"vertical\"</code>.</p>",
                chart_markup("milestone", _MILESTONE_DATA, label="Company milestones",
                             attrs={"orientation": "vertical"}, style="height:420px"),
            ),
            events_example(
                "milestone", _MILESTONE_DATA, ["mj-chart-event-click"], "[part=marker]",
                description="<p>Diamonds emit <code>mj-chart-event-click</code>.</p>",
            ),
        ],
    ),
    ChartTypeDoc(
        type_key="kanban",
        title="Kanban Board",
        category="project",
        summary=(
            "WIP-column board with priority-striped cards; columns over "
            "their WIP limit are tinted and marked."
        ),
        description=(
            "Columns of item cards with a priority-colour stripe (critical, high, medium, "
            "low). Each header shows the item count, and count / limit when the column has "
            "a wip-limit; a column over its limit is tinted, says over limit and gets a "
            "dashed line under the last card within the limit. Cards that do not fit "
            "become a focusable +N more mark; every card is in the data table. orientation "
            "vertical (automatic on narrow charts) stacks the columns as rows; variant "
            "count draws a bar of item counts per column with its WIP limit."
        ),
        data_shape=(
            "<pre><code>{\n"
            "  columns: [{ name: string, \"wip-limit\"?: number,\n"
            "              items: [{ id: string, label: string, assignee?: string,\n"
            "                        priority?: 'critical' | 'high' | 'medium' | 'low' }] }]\n"
            "}</code></pre>"
        ),
        options=[
            AttributeDoc(name="variant", description="`count`: one bar per column with its WIP limit.",
                         kind="enum", values=["count"]),
            orientation_option(
                "horizontal",
                "horizontal: columns side by side; vertical: columns as rows. Not set: vertical "
                "on narrow charts with more than two columns.",
            ),
        ],
        examples=[
            basic_example(_chart("kanban", _KANBAN_DATA, height="340px", legend=True),
                          "<p>Four columns; In Progress is over its WIP limit of 3.</p>"),
            gallery_example(
                "count",
                "Count variant",
                "<p><code>variant=\"count\"</code>: item counts against the WIP limits.</p>",
                chart_markup("kanban", _KANBAN_DATA, label="Sprint board counts",
                             attrs={"variant": "count"}),
            ),
            gallery_example(
                "vertical",
                "Columns as rows",
                "<p><code>orientation=\"vertical\"</code>.</p>",
                chart_markup("kanban", _KANBAN_DATA, label="Sprint board",
                             attrs={"orientation": "vertical"}, style="height:420px"),
            ),
            gallery_example(
                "overflow",
                "Too many cards",
                "<p>Twelve cards in a short board: the rest is summarised as +N more.</p>",
                chart_markup("kanban", _KANBAN_BUSY, label="Ops board", style="height:300px"),
            ),
            events_example(
                "kanban", _KANBAN_BUSY, ["mj-chart-card-click", "mj-chart-overflow-click"],
                "[part=card]", enter="[part=overflow]", label="Ops board", style="height:300px",
                description=(
                    "<p>Cards emit <code>mj-chart-card-click</code>; the +N more mark emits "
                    "<code>mj-chart-overflow-click</code> with the hidden items.</p>"
                ),
            ),
        ],
    ),
    ChartTypeDoc(
        type_key="resource-allocation",
        title="Resource Allocation",
        category="project",
        summary=(
            "Resource rows over time with allocations stacked by load; "
            "periods whose summed load exceeds capacity are flagged."
        ),
        description=(
            "One row per resource over a time axis. Allocations that run at the same time "
            "are stacked by load; the dashed line is the capacity (default 1) and every "
            "period whose summed load exceeds it is outlined in red. Bar height is load "
            "relative to the larger of capacity and peak, so any unit works (fractions, "
            "hours). Dates follow the gantt rules (local days, end inclusive). variant "
            "heatmap shows each period's utilisation as a colour band instead."
        ),
        data_shape=(
            "<pre><code>{\n"
            "  resources: [{ id: string, label: string, capacity?: number,\n"
            "                allocations: [{ task: string, start: string, end: string, load: number }] }]\n"
            "}</code></pre>"
            "<ul><li><code>load</code>: in the same unit as <code>capacity</code>.</li>"
            "<li>Allocations without usable dates or load are listed in the table, not drawn.</li></ul>"
        ),
        options=[
            AttributeDoc(name="variant", description="`heatmap`: utilisation per period as a colour band.",
                         kind="enum", values=["heatmap"]),
        ],
        examples=[
            basic_example(_chart("resource-allocation", _RESOURCE_DATA, height="300px", legend=True),
                          "<p>Four people; Bob and Dave are over capacity where allocations overlap.</p>"),
            gallery_example(
                "heatmap",
                "Heatmap variant",
                "<p><code>variant=\"heatmap\"</code>: colour shows summed load / capacity.</p>",
                chart_markup("resource-allocation", _RESOURCE_DATA, label="Team utilisation",
                             attrs={"variant": "heatmap"}, style="height:260px", legend=True),
            ),
            gallery_example(
                "hours",
                "Capacity in hours",
                "<p>Capacities of 60-120 hours a week; Design and Web exceed theirs.</p>",
                chart_markup("resource-allocation", _RESOURCE_HOURS, label="Team hours",
                             legend=True),
            ),
            events_example(
                "resource-allocation", _RESOURCE_DATA, ["mj-chart-allocation-click"],
                "[part=allocation]", enter="click:[part=over-allocation]", style="height:300px",
                description=(
                    "<p>Allocations and over-capacity flags emit <code>mj-chart-allocation-click</code>; "
                    "a flag's detail has <code>overAllocated: true</code>.</p>"
                ),
            ),
        ],
    ),
]
