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

import json

from testcomponents.charttypes.charttypedoc import ChartTypeDoc


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _json(obj: object) -> str:
    """
        Serialise *obj* to a compact JSON string.

        :param obj: Any JSON-serialisable Python object.
        :returns: A compact JSON string.
    """
    result = json.dumps(obj, separators=(",", ":"))
    return result


def _chart(chart_type: str, data: object, height: str = "260px") -> str:
    """
        Build a minimal <mj-chart> HTML snippet with inline JSON data.

        :param chart_type: The ``type`` attribute value for <mj-chart>.
        :param data: A Python object that will be serialised to the inline
            ``<script type="application/json">`` child element.
        :param height: CSS height applied via the ``style`` attribute.
        :returns: A complete HTML snippet string.
    """
    payload = _json(data)
    result = (
        f'<mj-chart type="{chart_type}" style="height:{height}">\n'
        f'  <script type="application/json">{payload}</script>\n'
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
            "name": "Model A",
            "groups": [
                {"category": "Group 1", "value": 0.72, "error_low": 0.08, "error_high": 0.10},
                {"category": "Group 2", "value": 0.55, "error_low": 0.12, "error_high": 0.13},
                {"category": "Group 3", "value": 0.81, "error_low": 0.07, "error_high": 0.09},
                {"category": "Group 4", "value": 0.48, "error_low": 0.15, "error_high": 0.16},
                {"category": "Group 5", "value": 0.65, "error_low": 0.10, "error_high": 0.11},
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
            ],
        }
    ],
    "reference_lines": [{"label": "Median", "value": 5.25}],
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
            ],
        }
    ],
}

_GANTT_DATA = {
    "tasks": [
        {
            "id": "req",
            "label": "Requirements",
            "start": "2025-04-01",
            "end": "2025-04-14",
            "progress": 1.0,
            "assignee": "Alice",
        },
        {
            "id": "design",
            "label": "System Design",
            "start": "2025-04-10",
            "end": "2025-04-28",
            "progress": 0.8,
            "assignee": "Bob",
            "depends": ["req"],
        },
        {
            "id": "dev-fe",
            "label": "Frontend Dev",
            "start": "2025-04-21",
            "end": "2025-05-16",
            "progress": 0.4,
            "assignee": "Carol",
            "depends": ["design"],
        },
        {
            "id": "dev-be",
            "label": "Backend Dev",
            "start": "2025-04-21",
            "end": "2025-05-23",
            "progress": 0.3,
            "assignee": "Dave",
            "depends": ["design"],
        },
        {
            "id": "qa",
            "label": "QA & Testing",
            "start": "2025-05-19",
            "end": "2025-06-06",
            "progress": 0.0,
            "assignee": "Eve",
            "depends": ["dev-fe", "dev-be"],
        },
        {
            "id": "launch",
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
            "Displays point estimates with asymmetric error whiskers; "
            "supports multiple series and optional bar-mode centre marks."
        ),
        example=_chart("errorbar", _ERRORBAR_DATA),
        description=(
            "Each data point requires a <code>category</code>, a central "
            "<code>value</code>, and positive half-widths "
            "<code>error_low</code> / <code>error_high</code>. "
            "Set <code>bar: true</code> on a point to render its centre "
            "mark as a filled bar instead of a dot. "
            "Supports <code>orientation=\"horizontal\"</code>."
        ),
    ),
    ChartTypeDoc(
        type_key="confidence-interval",
        title="Confidence Interval",
        category="statistical",
        summary=(
            "Alias of errorbar; suited to displaying CI bounds around "
            "effect estimates or survey proportions."
        ),
        example=_chart("confidence-interval", _CI_DATA),
        description=(
            "Uses the same renderer and JSON shape as <code>errorbar</code>. "
            "Provide <code>error_low</code> and <code>error_high</code> as "
            "positive half-widths; the renderer draws whiskers at "
            "<code>value ± error_*</code>."
        ),
    ),
    ChartTypeDoc(
        type_key="control-chart",
        title="Control Chart",
        category="statistical",
        summary=(
            "Statistical process control chart with UCL/LCL/CL limit lines "
            "and out-of-control point highlighting."
        ),
        example=_chart("control-chart", _CONTROL_CHART_DATA),
        description=(
            "Supply <code>series[].points[]</code> with numeric <code>x</code> "
            "(sequence index or timestamp) and <code>y</code> values. "
            "Add <code>ooc: true</code> to flag out-of-control points in danger "
            "red. <code>control_limits</code> is optional; omit it to render a "
            "plain run chart with control styling."
        ),
    ),
    ChartTypeDoc(
        type_key="run-chart",
        title="Run Chart",
        category="statistical",
        summary=(
            "Simple time-ordered line chart with optional reference-line "
            "annotations (e.g. median); no control limits."
        ),
        example=_chart("run-chart", _RUN_CHART_DATA),
        description=(
            "Identical renderer to <code>control-chart</code> but without "
            "UCL/LCL bands. Use <code>reference_lines</code> to annotate "
            "a median or target. Each point has numeric <code>x</code> and "
            "<code>y</code> fields."
        ),
    ),
    ChartTypeDoc(
        type_key="roc",
        title="ROC Curve",
        category="statistical",
        summary=(
            "Receiver Operating Characteristic curve with diagonal "
            "chance-line reference; compares classifier performance."
        ),
        example=_chart("roc", _ROC_DATA),
        description=(
            "Points are <code>{x, y}</code> pairs where <code>x</code> is "
            "False Positive Rate and <code>y</code> is True Positive Rate. "
            "Multiple series overlay on the same axes. "
            "Set <code>shade-auc=\"true\"</code> to fill area under the curve."
        ),
    ),
    ChartTypeDoc(
        type_key="precision-recall",
        title="Precision-Recall Curve",
        category="statistical",
        summary=(
            "Precision vs. recall trade-off curve with optional baseline "
            "prevalence reference line."
        ),
        example=_chart("precision-recall", _PR_DATA),
        description=(
            "Points: <code>x</code> = Recall, <code>y</code> = Precision. "
            "Provide <code>baseline_prevalence</code> at the root to draw a "
            "horizontal no-skill reference line. "
            "Shade area under curve with <code>shade-auc=\"true\"</code>."
        ),
    ),
    ChartTypeDoc(
        type_key="lift",
        title="Lift Chart",
        category="statistical",
        summary=(
            "Model lift vs. population contacted; horizontal baseline at "
            "lift = 1 marks random selection performance."
        ),
        example=_chart("lift", _LIFT_DATA),
        description=(
            "Points: <code>x</code> = fraction of population contacted "
            "(0–1), <code>y</code> = lift ratio. "
            "A horizontal reference line is automatically drawn at y = 1. "
            "Useful for evaluating direct-marketing or recommendation models."
        ),
    ),
    ChartTypeDoc(
        type_key="calibration",
        title="Calibration Plot",
        category="statistical",
        summary=(
            "Mean predicted probability vs. fraction of positives; "
            "diagonal perfect-calibration line included."
        ),
        example=_chart("calibration", _CALIBRATION_DATA),
        description=(
            "Points: <code>x</code> = mean predicted probability, "
            "<code>y</code> = observed fraction of positives, optional "
            "<code>n</code> = sample count in bucket. "
            "Add <code>size-by=\"n\"</code> attribute to scale dot area by "
            "sample count. Diagonal reference line marks perfect calibration."
        ),
    ),
    ChartTypeDoc(
        type_key="survival",
        title="Survival Curve",
        category="statistical",
        summary=(
            "Kaplan-Meier step function with censored observation ticks "
            "and optional confidence bands."
        ),
        example=_chart("survival", _SURVIVAL_DATA),
        description=(
            "Points require <code>x</code> (time) and <code>y</code> "
            "(survival probability 0–1). Mark censored observations with "
            "<code>censored: true</code>. Provide <code>ci_lower</code> / "
            "<code>ci_upper</code> on points and set <code>ci=\"true\"</code> "
            "to shade confidence bands. Add <code>at_risk</code> counts and "
            "<code>at-risk=\"true\"</code> to render the numbers-at-risk table."
        ),
    ),
    ChartTypeDoc(
        type_key="kaplan-meier",
        title="Kaplan-Meier",
        category="statistical",
        summary=(
            "Alias of survival; renders the classic Kaplan-Meier step "
            "function for time-to-event analysis."
        ),
        example=_chart("kaplan-meier", _SURVIVAL_DATA),
        description=(
            "Same renderer and JSON shape as <code>survival</code>. "
            "The alias makes intent explicit when the chart is used in a "
            "clinical or epidemiological context."
        ),
    ),
    ChartTypeDoc(
        type_key="forest",
        title="Forest Plot",
        category="statistical",
        summary=(
            "Meta-analysis blobbogram: per-study effect sizes with CI "
            "whiskers, weight-scaled square markers, and pooled diamond."
        ),
        example=_chart("forest", _FOREST_DATA),
        description=(
            "Each group entry needs <code>category</code>, <code>value</code>, "
            "<code>error_low</code>, <code>error_high</code>, and optional "
            "<code>weight</code> (drives marker size). "
            "The optional root-level <code>pooled</code> object "
            "(<code>value</code>, <code>ci_lower</code>, <code>ci_upper</code>, "
            "<code>label</code>) renders a pooled-estimate diamond at the bottom. "
            "Set <code>scale=\"log\"</code> for odds-ratio plots."
        ),
    ),
    ChartTypeDoc(
        type_key="funnel-plot",
        title="Funnel Plot",
        category="statistical",
        summary=(
            "Publication-bias scatter: effect estimate vs. standard error "
            "with inverted y-axis and funnel boundary overlay."
        ),
        example=_chart("funnel-plot", _FUNNEL_PLOT_DATA),
        description=(
            "Each point: <code>x</code> = effect estimate, "
            "<code>y</code> = standard error (larger SE at the bottom). "
            "Provide <code>funnel.summary_effect</code> and "
            "<code>funnel.pseudo_ci</code> (array of "
            "<code>{se, lower, upper}</code>) to draw the funnel boundaries. "
            "Set <code>labels=\"true\"</code> to show per-point study labels. "
            "Note: this is distinct from the <code>funnel</code> chart type "
            "(pipeline/conversion funnel)."
        ),
    ),
    # ------------------------------------------------------------------
    # FINANCIAL
    # ------------------------------------------------------------------
    ChartTypeDoc(
        type_key="ohlc",
        title="OHLC Chart",
        category="financial",
        summary=(
            "Open-High-Low-Close price chart using vertical range lines "
            "with open/close tick marks."
        ),
        example=_chart("ohlc", _OHLC_DATA),
        description=(
            "Each candle requires <code>t</code> (ISO date or epoch ms), "
            "<code>o</code> (open), <code>h</code> (high), <code>l</code> "
            "(low), and <code>c</code> (close). "
            "Set attribute <code>style=\"ohlc\"</code> to use tick-mark "
            "rendering instead of the default candlestick body. "
            "Bullish candles (c &ge; o) are coloured green; bearish red."
        ),
    ),
    ChartTypeDoc(
        type_key="candlestick",
        title="Candlestick",
        category="financial",
        summary=(
            "Japanese candlestick chart with filled bodies and wicks; "
            "same data shape as OHLC."
        ),
        example=_chart("candlestick", _OHLC_DATA),
        description=(
            "Alias of <code>ohlc</code> with <code>style=\"candle\"</code> "
            "as default. Candle bodies span open-to-close; upper and lower "
            "wicks extend to the session high and low. "
            "Volume (<code>v</code>) is stored but not drawn by this renderer "
            "— pair with the <code>volume</code> chart type for a composite view."
        ),
    ),
    ChartTypeDoc(
        type_key="volume",
        title="Volume",
        category="financial",
        summary=(
            "Trading-volume bar chart coloured by price direction "
            "(bullish / bearish) or a uniform series colour."
        ),
        example=_chart("volume", _VOLUME_DATA),
        description=(
            "Reuses the <code>candles</code> envelope; each entry needs "
            "<code>t</code> and <code>v</code>. Include <code>o</code> and "
            "<code>c</code> to enable direction colouring "
            "(<code>color-mode=\"direction\"</code>, the default). "
            "Set <code>color-mode=\"series\"</code> for a uniform colour."
        ),
    ),
    ChartTypeDoc(
        type_key="tornado",
        title="Tornado Chart",
        category="financial",
        summary=(
            "Sensitivity / what-if analysis: paired horizontal bars diverge "
            "from a central baseline, sorted by impact magnitude."
        ),
        example=_chart("tornado", _TORNADO_DATA),
        description=(
            "Root-level <code>baseline</code> sets the centre reference value. "
            "Each entry in <code>series[].values[]</code> requires a "
            "<code>label</code>, <code>low</code>, and <code>high</code> "
            "(absolute axis values). Rows are automatically sorted widest-first. "
            "Set attribute <code>style=\"butterfly\"</code> to treat "
            "<code>low</code>/<code>high</code> as magnitudes mirrored around "
            "the baseline."
        ),
    ),
    # ------------------------------------------------------------------
    # PROJECT / SCHEDULE
    # ------------------------------------------------------------------
    ChartTypeDoc(
        type_key="gantt",
        title="Gantt Chart",
        category="project",
        summary=(
            "Project timeline with horizontal task bars, progress fills, "
            "swimlane group headers, and dependency arrows."
        ),
        example=_chart("gantt", _GANTT_DATA),
        description=(
            "Each task requires <code>id</code>, <code>label</code>, "
            "<code>start</code>, and <code>end</code> (ISO YYYY-MM-DD). "
            "Optional fields: <code>progress</code> (0–1 fraction), "
            "<code>assignee</code>, <code>group</code> (swimlane name), "
            "and <code>depends</code> (array of predecessor <code>id</code> "
            "strings) for dependency arrows. "
            "Quarter strings (e.g. <code>2025-Q2</code>) are also accepted."
        ),
    ),
    ChartTypeDoc(
        type_key="roadmap",
        title="Roadmap",
        category="project",
        summary=(
            "Strategic roadmap variant of the Gantt renderer: broader bars, "
            "quarter-level ticks, status colour coding, no dependency arrows."
        ),
        example=_chart("roadmap", _ROADMAP_DATA),
        description=(
            "Same JSON shape as <code>gantt</code>. "
            "Use <code>status</code> on each task to apply semantic colours: "
            "<code>completed</code> (green), <code>in-progress</code> (blue), "
            "<code>planned</code> (grey), <code>at-risk</code> (red). "
            "Quarter strings in <code>start</code>/<code>end</code> are "
            "automatically expanded to quarter boundaries."
        ),
    ),
    ChartTypeDoc(
        type_key="timeline",
        title="Timeline",
        category="project",
        summary=(
            "Event markers along a time spine; labels alternate above and "
            "below; optional multi-lane layout via the group field."
        ),
        example=_chart("timeline", _TIMELINE_DATA),
        description=(
            "Each event requires <code>date</code> (ISO string) and "
            "<code>label</code>. Optional: <code>id</code>, <code>group</code> "
            "(enables multi-lane layout), <code>status</code> "
            "(<code>completed</code>, <code>active</code>, <code>planned</code>, "
            "<code>at-risk</code>). "
            "Markers are circles by default; switch to diamonds with the "
            "<code>milestone</code> type alias."
        ),
    ),
    ChartTypeDoc(
        type_key="milestone",
        title="Milestone",
        category="project",
        summary=(
            "Diamond-marker variant of the timeline; ideal for key delivery "
            "dates, funding rounds, and strategic checkpoints."
        ),
        example=_chart("milestone", _MILESTONE_DATA),
        description=(
            "Same renderer and JSON shape as <code>timeline</code> with "
            "<code>style=\"milestone\"</code> applied internally. "
            "Diamond markers communicate discrete one-day events rather than "
            "durations. Status colours follow the same mapping as timeline."
        ),
    ),
    ChartTypeDoc(
        type_key="kanban",
        title="Kanban Board",
        category="project",
        summary=(
            "WIP-column board with priority-striped item cards, item-count "
            "badges, and optional WIP-limit indicator lines."
        ),
        example=_chart("kanban", _KANBAN_DATA),
        description=(
            "Root key: <code>columns</code> array. Each column has "
            "<code>name</code>, optional <code>wip-limit</code> (integer), "
            "and <code>items</code> array. Each item: <code>id</code>, "
            "<code>label</code>, optional <code>priority</code> "
            "(<code>critical</code>, <code>high</code>, <code>medium</code>, "
            "<code>low</code>), and optional <code>assignee</code>. "
            "Exceeding the WIP limit renders the indicator in danger red."
        ),
    ),
    ChartTypeDoc(
        type_key="resource-allocation",
        title="Resource Allocation",
        category="project",
        summary=(
            "Resource rows over a time axis with load-proportional allocation "
            "bars; over-allocated periods are highlighted in danger red."
        ),
        example=_chart("resource-allocation", _RESOURCE_DATA),
        description=(
            "Root key: <code>resources</code> array. Each resource has "
            "<code>id</code>, <code>label</code>, optional <code>capacity</code> "
            "(default 1.0), and <code>allocations</code> array. "
            "Each allocation: <code>task</code>, <code>start</code>, "
            "<code>end</code> (ISO dates), <code>load</code> (0–1 fraction). "
            "Bar height encodes load within the row bandwidth. "
            "Set <code>style=\"heatmap\"</code> for a daily-aggregated heat band."
        ),
    ),
]
