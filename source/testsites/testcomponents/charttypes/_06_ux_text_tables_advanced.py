"""
    06_ux_text_tables_advanced.py

    ChartTypeDoc catalog entries for:
      - UX / Product / Business charts (gauge, kpi, cohort, retention,
        user-journey, session-flow)
      - Text / Categorical charts (word-cloud, venn, euler, upset, matrix)
      - Tables with Visual Encoding (heatmap-table, bar-in-cell,
        conditional-format-table, icon-array, waffle-pictograph, scorecard)
      - Less Common / Advanced charts (calendar-heatmap, voronoi, spiral,
        pixel, glyph, faceted)

    The example markup helpers (inline JSON data, the events example) are
    shared with ``_05_scientific_geographic``.
"""

from testcomponents.catalog.componentdoc import AttributeDoc
from testcomponents.charttypes.charttypedoc import ChartTypeDoc
from testcomponents.charttypes.examplemarkup import chart_example
from testcomponents.charttypes.examplemarkup import events_example
from testcomponents.charttypes.examplemarkup import with_changes


# ---------------------------------------------------------------------------
# Example data (the basic example of each type first)
# ---------------------------------------------------------------------------

_GAUGE_DATA = {
    "gauge": {
        "value": 72,
        "min": 0,
        "max": 100,
        "unit": "%",
        "thresholds": [
            {"value": 40, "label": "Fair", "color": "--mj-color-warning"},
            {"value": 70, "label": "Good", "color": "--mj-color-success"},
        ],
        "needle": True,
    },
}


_KPI_DATA = {
    "kpi": {
        "value": 48320,
        "label": "Monthly Active Users",
        "format": ",.0f",
        "comparison": {"value": 41500, "label": "vs last month"},
        "spark": [31200, 34800, 38100, 41500, 43900, 46200, 48320],
    },
}


_COHORT_DATA = {
    "cohorts": [
        {"label": "Jan", "size": 1200, "periods": [1.0, 0.72, 0.55, 0.41, 0.33, 0.28]},
        {"label": "Feb", "size": 980, "periods": [1.0, 0.68, 0.5, 0.38, 0.3]},
        {"label": "Mar", "size": 1350, "periods": [1.0, 0.75, 0.58, 0.44]},
        {"label": "Apr", "size": 1100, "periods": [1.0, 0.7, 0.53]},
        {"label": "May", "size": 1450, "periods": [1.0, 0.74]},
    ],
    "period_labels": ["Week 0", "Week 1", "Week 2", "Week 3", "Week 4", "Week 5"],
    "mode": "rate",
}


_RETENTION_DATA = {
    "cohorts": [
        {"label": "2024-Q1", "size": 5000, "periods": [1.0, 0.6, 0.42, 0.31, 0.24]},
        {"label": "2024-Q2", "size": 4800, "periods": [1.0, 0.63, 0.45, 0.34]},
        {"label": "2024-Q3", "size": 5200, "periods": [1.0, 0.58, 0.4]},
        {"label": "2024-Q4", "size": 6100, "periods": [1.0, 0.65]},
    ],
    "period_labels": ["Month 0", "Month 1", "Month 2", "Month 3", "Month 4"],
    "mode": "rate",
}


_USER_JOURNEY_DATA = {
    "steps": [
        {"label": "Awareness", "score": 3.5, "touchpoints": ["Ad", "Blog"], "pain_points": []},
        {
            "label": "Consideration",
            "score": 2.8,
            "touchpoints": ["Website"],
            "pain_points": ["Slow load"],
        },
        {"label": "Purchase", "score": 3.9, "touchpoints": ["Checkout"], "pain_points": []},
        {
            "label": "Onboarding",
            "score": 2.2,
            "touchpoints": ["Email"],
            "pain_points": ["Confusing setup"],
        },
        {
            "label": "Retention",
            "score": 4.1,
            "touchpoints": ["App", "Support"],
            "pain_points": [],
        },
    ],
    "score_range": [1, 5],
}


_SESSION_FLOW_DATA = {
    "nodes": [
        {"id": "home", "label": "Home"},
        {"id": "catalog", "label": "Catalog"},
        {"id": "product", "label": "Product"},
        {"id": "cart", "label": "Cart"},
        {"id": "checkout", "label": "Checkout"},
        {"id": "exit", "label": "Exit"},
    ],
    "links": [
        {"source": "home", "target": "catalog", "value": 820},
        {"source": "home", "target": "exit", "value": 180},
        {"source": "catalog", "target": "product", "value": 610},
        {"source": "catalog", "target": "exit", "value": 210},
        {"source": "product", "target": "cart", "value": 390},
        {"source": "product", "target": "exit", "value": 220},
        {"source": "product", "target": "catalog", "value": 80},
        {"source": "cart", "target": "checkout", "value": 270},
        {"source": "cart", "target": "exit", "value": 120},
    ],
}


_WORD_CLOUD_DATA = {
    "words": [
        {"text": "Python", "value": 320},
        {"text": "JavaScript", "value": 280},
        {"text": "TypeScript", "value": 240},
        {"text": "Rust", "value": 190},
        {"text": "Go", "value": 175},
        {"text": "SQL", "value": 160},
        {"text": "Docker", "value": 145},
        {"text": "Kubernetes", "value": 130},
        {"text": "GraphQL", "value": 110},
        {"text": "React", "value": 210},
        {"text": "FastAPI", "value": 95},
        {"text": "Postgres", "value": 88},
        {"text": "Redis", "value": 75},
        {"text": "Kafka", "value": 68},
        {"text": "Terraform", "value": 60},
    ],
    "max_words": 60,
    "rotation": "mixed",
}


_VENN_DATA = {
    "sets": [
        {"name": "Backend", "size": 420},
        {"name": "Frontend", "size": 380},
        {"name": "DevOps", "size": 210},
    ],
    "intersections": [
        {"sets": ["Backend", "Frontend"], "size": 95},
        {"sets": ["Backend", "DevOps"], "size": 78},
        {"sets": ["Frontend", "DevOps"], "size": 42},
        {"sets": ["Backend", "Frontend", "DevOps"], "size": 30},
    ],
    "proportional": False,
}


_EULER_DATA = {
    "sets": [{"name": "Subscribers", "size": 8000}, {"name": "Paid", "size": 3200}],
    "intersections": [{"sets": ["Subscribers", "Paid"], "size": 3200}],
    "proportional": True,
}


_UPSET_DATA = {
    "sets": [
        {"name": "Email", "size": 5200},
        {"name": "Push", "size": 3800},
        {"name": "SMS", "size": 2100},
        {"name": "In-App", "size": 4400},
    ],
    "intersections": [
        {"sets": ["Email"], "size": 1800},
        {"sets": ["Push"], "size": 1200},
        {"sets": ["In-App"], "size": 1400},
        {"sets": ["Email", "Push"], "size": 980},
        {"sets": ["Email", "In-App"], "size": 870},
        {"sets": ["Push", "In-App"], "size": 640},
        {"sets": ["Email", "Push", "In-App"], "size": 420},
        {"sets": ["SMS"], "size": 520},
        {"sets": ["Email", "SMS"], "size": 310},
    ],
}


_MATRIX_DATA = {
    "meta": {"yLabel": "Region"},
    "x_categories": ["Q1", "Q2", "Q3", "Q4"],
    "y_categories": ["APAC", "EMEA", "LATAM", "NA"],
    "cells": [
        {"x": "Q1", "y": "APAC", "value": 42},
        {"x": "Q1", "y": "EMEA", "value": 78},
        {"x": "Q1", "y": "LATAM", "value": 31},
        {"x": "Q1", "y": "NA", "value": 95},
        {"x": "Q2", "y": "APAC", "value": 55},
        {"x": "Q2", "y": "EMEA", "value": 82},
        {"x": "Q2", "y": "LATAM", "value": 40},
        {"x": "Q2", "y": "NA", "value": 110},
        {"x": "Q3", "y": "APAC", "value": 68},
        {"x": "Q3", "y": "EMEA", "value": 74},
        {"x": "Q3", "y": "LATAM", "value": 52},
        {"x": "Q3", "y": "NA", "value": 98},
        {"x": "Q4", "y": "APAC", "value": 80},
        {"x": "Q4", "y": "EMEA", "value": 91},
        {"x": "Q4", "y": "LATAM", "value": 63},
        {"x": "Q4", "y": "NA", "value": 125},
    ],
    "mark": "circle",
}


_HEATMAP_TABLE_DATA = {
    "columns": [
        {"key": "region", "label": "Region", "type": "string"},
        {"key": "jan", "label": "Jan", "type": "number"},
        {"key": "feb", "label": "Feb", "type": "number"},
        {"key": "mar", "label": "Mar", "type": "number"},
        {"key": "apr", "label": "Apr", "type": "number"},
    ],
    "rows": [
        {"region": "North", "jan": 82, "feb": 76, "mar": 91, "apr": 88},
        {"region": "South", "jan": 55, "feb": 61, "mar": 70, "apr": 74},
        {"region": "East", "jan": 93, "feb": 88, "mar": 95, "apr": 99},
        {"region": "West", "jan": 47, "feb": 52, "mar": 60, "apr": 65},
        {"region": "Central", "jan": 68, "feb": 71, "mar": 78, "apr": 83},
    ],
    "colorScale": "sequential",
}


_BAR_IN_CELL_DATA = {
    "columns": [
        {"key": "product", "label": "Product", "type": "string"},
        {
            "key": "revenue",
            "label": "Revenue",
            "type": "number",
            "render": "bar",
            "format": "$,.0f",
        },
        {"key": "units", "label": "Units", "type": "number", "render": "bar", "format": ",.0f"},
        {"key": "margin", "label": "Margin %", "type": "number"},
    ],
    "rows": [
        {"product": "Widget A", "revenue": 128000, "units": 3200, "margin": 38},
        {"product": "Widget B", "revenue": 94000, "units": 2400, "margin": 42},
        {"product": "Gadget X", "revenue": 210000, "units": 5100, "margin": 29},
        {"product": "Gadget Y", "revenue": 67000, "units": 1800, "margin": 51},
        {"product": "Module Z", "revenue": 155000, "units": 3900, "margin": 35},
    ],
}


_CONDITIONAL_FORMAT_TABLE_DATA = {
    "columns": [
        {"key": "metric", "label": "Metric", "type": "string"},
        {"key": "current", "label": "Current", "type": "number"},
        {"key": "target", "label": "Target", "type": "number"},
        {"key": "status", "label": "vs Target", "type": "number"},
    ],
    "rows": [
        {"metric": "Uptime %", "current": 99.8, "target": 99.9, "status": -0.1},
        {"metric": "Error Rate", "current": 1.4, "target": 2.0, "status": 0.6},
        {"metric": "P95 Latency", "current": 320, "target": 300, "status": -20},
        {"metric": "Throughput", "current": 4800, "target": 4000, "status": 800},
        {"metric": "MTTR (min)", "current": 18, "target": 15, "status": -3},
    ],
    "rules": [
        {
            "column": "status",
            "op": "lt",
            "value": 0,
            "style": {"fill": "var(--mj-color-danger-surface, #fee2e2)", "icon": "warning"},
        },
        {
            "column": "status",
            "op": "gte",
            "value": 0,
            "style": {"fill": "var(--mj-color-success-surface, #dcfce7)", "icon": "check"},
        },
        {"column": "metric", "op": "contains", "value": "Latency", "style": {"weight": 700}},
    ],
}


_ICON_ARRAY_DATA = {
    "total": 100,
    "series": [
        {"name": "Treated", "count": 63, "icon": "person"},
        {"name": "Placebo", "count": 27, "icon": "person"},
        {"name": "Untreated", "count": 10, "icon": "person"},
    ],
    "grid": {"cols": 10},
}


_WAFFLE_PICTOGRAPH_DATA = {
    "total": 100,
    "series": [
        {"name": "Completed", "count": 74, "icon": "square"},
        {"name": "In Progress", "count": 18, "icon": "square"},
        {"name": "Blocked", "count": 8, "icon": "square"},
    ],
    "grid": {"cols": 10},
}


_SCORECARD_DATA = {
    "metrics": [
        {
            "label": "Revenue",
            "value": 2480000,
            "target": 3000000,
            "format": "$,.3s",
            "delta": 0.12,
            "trend": "up",
            "sparkline": [1900000, 2050000, 2120000, 2300000, 2380000, 2480000],
        },
        {
            "label": "Churn Rate",
            "value": 0.032,
            "target": 0.04,
            "format": ".1%",
            "delta": -0.08,
            "trend": "down",
            "good": "down",
            "sparkline": [0.041, 0.039, 0.037, 0.035, 0.033, 0.032],
        },
        {
            "label": "NPS",
            "value": 62,
            "target": 70,
            "delta": 0.05,
            "trend": "up",
            "sparkline": [48, 51, 55, 57, 60, 62],
        },
    ],
}


_CALENDAR_HEATMAP_DATA = {
    "years": [2025],
    "data": [
        {"date": "2025-01-06", "value": 12},
        {"date": "2025-01-07", "value": 5},
        {"date": "2025-01-13", "value": 28},
        {"date": "2025-01-20", "value": 18},
        {"date": "2025-02-03", "value": 42},
        {"date": "2025-02-17", "value": 37},
        {"date": "2025-03-10", "value": 55},
        {"date": "2025-03-24", "value": 61},
        {"date": "2025-04-07", "value": 48},
        {"date": "2025-04-21", "value": 73},
        {"date": "2025-05-05", "value": 88},
        {"date": "2025-05-19", "value": 94},
        {"date": "2025-06-02", "value": 102},
        {"date": "2025-06-16", "value": 115},
        {"date": "2025-07-04", "value": 78},
        {"date": "2025-07-14", "value": 65},
        {"date": "2025-08-11", "value": 50},
        {"date": "2025-09-01", "value": 88},
        {"date": "2025-10-13", "value": 120},
        {"date": "2025-11-03", "value": 95},
        {"date": "2025-12-25", "value": 30},
    ],
    "colorScale": "sequential",
}


_VORONOI_DATA = {
    "series": [
        {
            "name": "Cluster A",
            "points": [
                {"x": 1.2, "y": 2.8, "label": "P1"},
                {"x": 2.0, "y": 4.1, "label": "P2"},
                {"x": 3.1, "y": 1.5, "label": "P3"},
            ],
        },
        {
            "name": "Cluster B",
            "points": [
                {"x": 5.5, "y": 3.2, "label": "P4"},
                {"x": 6.8, "y": 5.0, "label": "P5"},
                {"x": 7.2, "y": 1.8, "label": "P6"},
            ],
        },
        {
            "name": "Cluster C",
            "points": [{"x": 4.0, "y": 7.5, "label": "P7"}, {"x": 5.2, "y": 8.8, "label": "P8"}],
        },
    ],
}


_SPIRAL_DATA = {
    "cycle": "week",
    "series": [
        {
            "name": "Page Views",
            "points": [
                {"t": "2025-01-06", "value": 4200},
                {"t": "2025-01-07", "value": 3800},
                {"t": "2025-01-08", "value": 6100},
                {"t": "2025-01-09", "value": 5900},
                {"t": "2025-01-10", "value": 5400},
                {"t": "2025-01-11", "value": 2100},
                {"t": "2025-01-12", "value": 1800},
                {"t": "2025-01-13", "value": 4500},
                {"t": "2025-01-14", "value": 4100},
                {"t": "2025-01-15", "value": 6400},
                {"t": "2025-01-16", "value": 6000},
                {"t": "2025-01-17", "value": 5600},
                {"t": "2025-01-18", "value": 2300},
                {"t": "2025-01-19", "value": 1900},
            ],
        },
    ],
}


_PIXEL_DATA = {
    "xDimension": "Hour of Day",
    "yDimension": "Day of Week",
    "valueMeasure": "Incidents",
    "xCategories": ["00h", "01h", "02h", "03h", "04h", "05h", "06h", "07h", "08h", "09h", "10h", "11h"],
    "yCategories": ["Mon", "Tue", "Wed"],
    "colorScale": "sequential",
    "bins": [
        {"x": 0, "y": 0, "value": 2},
        {"x": 1, "y": 0, "value": 1},
        {"x": 2, "y": 0, "value": 0},
        {"x": 3, "y": 0, "value": 3},
        {"x": 4, "y": 0, "value": 5},
        {"x": 5, "y": 0, "value": 8},
        {"x": 6, "y": 0, "value": 12},
        {"x": 7, "y": 0, "value": 18},
        {"x": 8, "y": 0, "value": 22},
        {"x": 9, "y": 0, "value": 19},
        {"x": 10, "y": 0, "value": 15},
        {"x": 11, "y": 0, "value": 11},
        {"x": 0, "y": 1, "value": 1},
        {"x": 1, "y": 1, "value": 0},
        {"x": 2, "y": 1, "value": 0},
        {"x": 3, "y": 1, "value": 2},
        {"x": 4, "y": 1, "value": 4},
        {"x": 5, "y": 1, "value": 7},
        {"x": 6, "y": 1, "value": 10},
        {"x": 7, "y": 1, "value": 16},
        {"x": 8, "y": 1, "value": 20},
        {"x": 9, "y": 1, "value": 17},
        {"x": 10, "y": 1, "value": 13},
        {"x": 11, "y": 1, "value": 9},
        {"x": 0, "y": 2, "value": 0},
        {"x": 5, "y": 2, "value": 3},
        {"x": 6, "y": 2, "value": 6},
        {"x": 7, "y": 2, "value": 9},
        {"x": 8, "y": 2, "value": 14},
        {"x": 9, "y": 2, "value": 11},
        {"x": 10, "y": 2, "value": 8},
        {"x": 11, "y": 2, "value": 5},
    ],
}


_GLYPH_DATA = {
    "axes": ["Speed", "Accuracy", "Reliability", "Cost", "Scalability"],
    "glyphType": "radar",
    "grid": {"cols": 4},
    "series": [
        {"name": "Service A", "values": [0.9, 0.7, 0.8, 0.5, 0.85]},
        {"name": "Service B", "values": [0.6, 0.95, 0.9, 0.7, 0.65]},
        {"name": "Service C", "values": [0.75, 0.6, 0.7, 0.9, 0.8]},
        {"name": "Service D", "values": [0.5, 0.8, 0.6, 0.4, 0.95]},
        {"name": "Service E", "values": [0.85, 0.75, 0.65, 0.6, 0.7]},
        {"name": "Service F", "values": [0.4, 0.5, 0.85, 0.95, 0.55]},
        {"name": "Service G", "values": [0.95, 0.65, 0.55, 0.35, 0.9]},
        {"name": "Service H", "values": [0.7, 0.85, 0.8, 0.65, 0.6]},
    ],
}


_FACETED_DATA = {
    "childType": "bar",
    "categories": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
    "grid": {"cols": 2, "colGap": 12, "rowGap": 12},
    "sharedScales": True,
    "panels": [
        {"label": "North", "series": [{"name": "Revenue", "values": [42, 55, 61, 58, 70, 75]}]},
        {"label": "South", "series": [{"name": "Revenue", "values": [28, 32, 38, 45, 51, 49]}]},
        {"label": "East", "series": [{"name": "Revenue", "values": [65, 70, 78, 82, 90, 95]}]},
        {"label": "West", "series": [{"name": "Revenue", "values": [38, 42, 48, 53, 60, 58]}]},
    ],
}


_GAUGE_RING_DATA = {
    "gauge": {
        "value": 64,
        "unit": "%",
        "needle": False,
        "start_angle": 0,
        "sweep_angle": 360,
        "thresholds": [
            {"value": 0, "label": "Started", "color": "--mj-chart-series-1"},
            {"value": 80, "label": "Nearly done", "color": "--mj-chart-series-3"},
        ],
    },
}


_GAUGE_SEMICIRCLE_DATA = {
    "gauge": {
        "value": 3450,
        "min": 0,
        "max": 6000,
        "unit": " rpm",
        "start_angle": -90,
        "sweep_angle": 180,
        "thresholds": [
            {"value": 800, "label": "Idle"},
            {"value": 3000, "label": "Cruise"},
            {"value": 5000, "label": "Red line", "color": "--mj-color-danger"},
        ],
    },
}


_GAUGE_OUT_OF_RANGE_DATA = {
    "gauge": {
        "value": 112,
        "min": 0,
        "max": 100,
        "unit": " °C",
        "thresholds": [{"value": 90, "label": "Hot", "color": "--mj-color-danger"}],
    },
}


_KPI_GOOD_DOWN_DATA = {
    "kpi": {
        "value": 18250,
        "label": "Cloud spend (month)",
        "format": "$,.0f",
        "good": "down",
        "comparison": {"value": 21400, "label": "vs last month"},
        "spark": [24100, 23300, 22800, None, 21400, 18250],
    },
}


_KPI_ZERO_BASELINE_DATA = {
    "kpi": {
        "value": 0.042,
        "label": "Checkout error rate",
        "format": ".1%",
        "good": "down",
        "comparison": {"value": 0, "label": "vs last release"},
    },
}


_KPI_NO_VALUE_DATA = {
    "kpi": {
        "value": None,
        "label": "Orders today (feed delayed)",
        "comparison": {"value": 1280, "label": "vs yesterday"},
    },
}


_COHORT_COUNT_DATA = {
    "cohorts": [
        {"label": "Week 1", "size": 820, "periods": [820, 410, 300, 246]},
        {"label": "Week 2", "size": 760, "periods": [760, 395, 281]},
        {"label": "Week 3", "size": 905, "periods": [905, 480, None]},
        {"label": "Week 4", "size": 640, "periods": [640]},
    ],
    "period_labels": ["Day 0", "Day 7", "Day 14", "Day 21"],
}


_COHORT_PERCENT_DATA = {
    "unit": "percent",
    "cohorts": [
        {"label": "2025-01", "size": 3100, "periods": [100, 46, 38, 33, 31]},
        {"label": "2025-02", "size": 2870, "periods": [100, 49, 40, 36]},
        {"label": "2025-03", "size": 3420, "periods": [100, 52, 44]},
        {"label": "2025-04", "size": 3010, "periods": [100, 55]},
    ],
    "period_labels": ["M0", "M1", "M2", "M3", "M4"],
}


_JOURNEY_PERSONAS_DATA = {
    "score_range": [1, 5],
    "personas": [
        {
            "name": "First-time buyer",
            "steps": [
                {"label": "Search", "score": 3.2, "touchpoints": ["Search ad"], "pain_points": []},
                {"label": "Compare", "score": 2.4, "touchpoints": ["Website", "Reviews"],
                 "pain_points": ["Hidden fees"]},
                {"label": "Buy", "score": 3.8, "touchpoints": ["Checkout"], "pain_points": []},
                {"label": "Delivery", "score": 4.3, "touchpoints": ["SMS", "Courier"], "pain_points": []},
            ],
        },
        {
            "name": "Returning buyer",
            "steps": [
                {"label": "Search", "score": 4.0, "touchpoints": ["App"], "pain_points": []},
                {"label": "Compare", "score": 3.9, "touchpoints": ["App"], "pain_points": []},
                {"label": "Buy", "score": 4.5, "touchpoints": ["One-click"], "pain_points": []},
                {"label": "Delivery", "score": 2.9, "touchpoints": ["Courier"],
                 "pain_points": ["Late parcel"]},
            ],
        },
    ],
}


_JOURNEY_GAP_DATA = {
    "score_range": [-2, 2],
    "steps": [
        {"label": "Sign up", "score": 1.2, "touchpoints": ["Landing page"], "pain_points": []},
        {"label": "Verify email", "score": -1.5, "touchpoints": ["Email"], "pain_points": ["Email in spam"]},
        {"label": "Tour", "score": None, "touchpoints": [], "pain_points": []},
        {"label": "First project", "score": 0.8, "touchpoints": ["App", "Docs", "Chat"], "pain_points": []},
        {"label": "Invite team", "score": 3.5, "touchpoints": ["App"], "pain_points": []},
    ],
}


_SESSION_FLOW_SMALL_DATA = {
    "nodes": [
        {"id": "landing", "label": "Landing"},
        {"id": "pricing", "label": "Pricing"},
        {"id": "signup", "label": "Sign up"},
        {"id": "docs", "label": "Docs"},
    ],
    "links": [
        {"source": "landing", "target": "pricing", "value": 540},
        {"source": "landing", "target": "docs", "value": 260},
        {"source": "pricing", "target": "signup", "value": 210},
        {"source": "docs", "target": "pricing", "value": 90},
        {"source": "pricing", "target": "landing", "value": 60},
        {"source": "docs", "target": "docs", "value": 40},
    ],
}


_WORD_CLOUD_EQUAL_DATA = {
    "rotation": "none",
    "words": [
        {"text": "latency", "value": 10}, {"text": "throughput", "value": 10},
        {"text": "uptime", "value": 10}, {"text": "errors", "value": 10},
        {"text": "saturation", "value": 10}, {"text": "cost", "value": 10},
    ],
}


_VENN_TWO_DATA = {
    "sets": [{"name": "Read the docs", "size": 1200}, {"name": "Opened a ticket", "size": 450}],
    "intersections": [{"sets": ["Read the docs", "Opened a ticket"], "size": 180}],
}


_VENN_FOUR_DATA = {
    "sets": [
        {"name": "Email", "size": 520}, {"name": "Push", "size": 380},
        {"name": "SMS", "size": 210}, {"name": "In-app", "size": 440},
    ],
    "intersections": [{"sets": ["Email", "Push"], "size": 98}],
}


_EULER_THREE_DATA = {
    "sets": [
        {"name": "Python", "size": 900},
        {"name": "JavaScript", "size": 700},
        {"name": "Rust", "size": 150},
    ],
    "intersections": [
        {"sets": ["Python", "JavaScript"], "size": 320},
        {"sets": ["Python", "Rust"], "size": 90},
        {"sets": ["JavaScript", "Rust"], "size": 60},
        {"sets": ["Python", "JavaScript", "Rust"], "size": 40},
    ],
}


_EULER_DISJOINT_DATA = {
    "sets": [
        {"name": "Trial users", "size": 2400},
        {"name": "Enterprise", "size": 600},
        {"name": "Churned", "size": 900},
    ],
    "intersections": [{"sets": ["Trial users", "Churned"], "size": 500}],
}


_UPSET_ELEMENTS_DATA = {
    "sets": [{"name": "Bug"}, {"name": "UI"}, {"name": "Backend"}, {"name": "Urgent"}],
    "elements": [
        ["Bug", "UI"], ["Bug", "UI"], ["Bug", "Backend"], ["Bug", "Backend", "Urgent"],
        ["UI"], ["UI"], ["UI"], ["Backend"], ["Backend", "Urgent"], ["Bug"],
        ["Bug", "UI", "Urgent"], ["Urgent"],
    ],
}


_MATRIX_SQUARE_DATA = {
    "mark": "square",
    "cells": [
        {"x": "Mon", "y": "Web", "value": 120}, {"x": "Tue", "y": "Web", "value": 132},
        {"x": "Wed", "y": "Web", "value": 101}, {"x": "Mon", "y": "Mobile", "value": 210},
        {"x": "Tue", "y": "Mobile", "value": 190}, {"x": "Wed", "y": "Mobile", "value": 0},
        {"x": "Mon", "y": "API", "value": 44}, {"x": "Wed", "y": "API", "value": 61},
    ],
}


_MATRIX_SIGNED_DATA = {
    "x_categories": ["Price", "Speed", "Support", "Docs"],
    "y_categories": ["Plan A", "Plan B", "Plan C"],
    "cells": [
        {"x": "Price", "y": "Plan A", "value": 0.6}, {"x": "Speed", "y": "Plan A", "value": -0.2},
        {"x": "Support", "y": "Plan A", "value": 0.3}, {"x": "Docs", "y": "Plan A", "value": 0.1},
        {"x": "Price", "y": "Plan B", "value": -0.5}, {"x": "Speed", "y": "Plan B", "value": 0.8},
        {"x": "Support", "y": "Plan B", "value": -0.1}, {"x": "Docs", "y": "Plan B", "value": 0.4},
        {"x": "Price", "y": "Plan C", "value": 0.2}, {"x": "Speed", "y": "Plan C", "value": 0.1},
        {"x": "Support", "y": "Plan C", "value": -0.7},
    ],
}


_HEATMAP_TABLE_DIVERGING_DATA = {
    "colorScale": "diverging",
    "midpoint": 0,
    "columns": [
        {"key": "team", "label": "Team"},
        {"key": "q1", "label": "Q1", "format": {"style": "percent", "signDisplay": "exceptZero"}},
        {"key": "q2", "label": "Q2", "format": {"style": "percent", "signDisplay": "exceptZero"}},
        {"key": "q3", "label": "Q3", "format": {"style": "percent", "signDisplay": "exceptZero"}},
    ],
    "rows": [
        {"team": "Sales", "q1": 0.12, "q2": 0.05, "q3": -0.03},
        {"team": "Support", "q1": -0.08, "q2": -0.02, "q3": 0.04},
        {"team": "Platform", "q1": 0.2, "q2": 0.15, "q3": 0.18},
        {"team": "Design", "q1": -0.15, "q2": None, "q3": 0.01},
    ],
}


_HEATMAP_TABLE_COLUMNS_DATA = {
    "scale": "column",
    "columns": [
        {"key": "city", "label": "City"},
        {"key": "visits", "label": "Visits", "format": ",.0f"},
        {"key": "conversion", "label": "Conversion", "format": ".1%"},
        {"key": "revenue", "label": "Revenue", "format": "$,.3s"},
    ],
    "rows": [
        {"city": "Austin", "visits": 18200, "conversion": 0.031, "revenue": 412000},
        {"city": "Boston", "visits": 24100, "conversion": 0.024, "revenue": 530000},
        {"city": "Chicago", "visits": 31800, "conversion": 0.019, "revenue": 610000},
        {"city": "Denver", "visits": 9800, "conversion": 0.042, "revenue": 288000},
    ],
}


_BAR_IN_CELL_SIGNED_DATA = {
    "columns": [
        {"key": "account", "label": "Account"},
        {"key": "change", "label": "Change vs plan", "type": "number", "render": "bar", "format": {"signDisplay": "exceptZero", "maximumFractionDigits": 0}},
        {"key": "share", "label": "Share", "type": "number", "render": "bar", "format": ".0%",
         "domain": [0, 1]},
    ],
    "rows": [
        {"account": "Northwind", "change": 42000, "share": 0.31},
        {"account": "Contoso", "change": -18500, "share": 0.22},
        {"account": "Fabrikam", "change": 7300, "share": 0.18},
        {"account": "Tailspin", "change": -31000, "share": 0.09},
        {"account": "Litware", "change": None, "share": 0.2},
    ],
}


_CONDITIONAL_TEXT_DATA = {
    "columns": [
        {"key": "service", "label": "Service"},
        {"key": "status", "label": "Status"},
        {"key": "p99", "label": "p99 (ms)", "type": "number"},
        {"key": "owner", "label": "Owner"},
    ],
    "rows": [
        {"service": "checkout", "status": "degraded", "p99": 840, "owner": "payments"},
        {"service": "search", "status": "ok", "p99": 120, "owner": "discovery"},
        {"service": "auth", "status": "down", "p99": None, "owner": "identity"},
        {"service": "catalog", "status": "ok", "p99": 95, "owner": "discovery"},
    ],
    "rules": [
        {"column": "status", "op": "eq", "value": "down",
         "style": {"fill": "var(--mj-color-danger-surface, #fee2e2)", "icon": "cross", "weight": 700}},
        {"column": "status", "op": "eq", "value": "degraded",
         "style": {"fill": "var(--mj-color-warning-surface, #fef3c7)", "icon": "warning"}},
        {"column": "p99", "op": "gt", "value": 500, "style": {"color": "var(--mj-color-danger, #b91c1c)", "weight": 700}},
        {"op": "contains", "value": "discovery", "style": {"icon": "info"}},
    ],
}


_ICON_ARRAY_LARGE_DATA = {
    "total": 12000,
    "per_icon": 100,
    "grid": {"cols": 20},
    "series": [
        {"name": "Vaccinated", "count": 8700},
        {"name": "Scheduled", "count": 1900},
        {"name": "Declined", "count": 1400},
    ],
}


_ICON_ARRAY_OVER_DATA = {
    "total": 20,
    "grid": {"cols": 5},
    "series": [
        {"name": "Seats sold", "count": 17, "icon": "square"},
        {"name": "Reserved", "count": 6, "icon": "circle"},
    ],
}


_SCORECARD_SIX_DATA = {
    "columns": 3,
    "metrics": [
        {"label": "Signups", "value": 1840, "format": ",.0f", "delta": 0.18},
        {"label": "Activation", "value": 0.46, "format": ".0%", "delta": 0.03, "target": 0.5},
        {"label": "MRR", "value": 128400, "format": "$,.0f", "delta": 0.07, "target": 150000},
        {"label": "Churn", "value": 0.021, "format": ".1%", "delta": -0.12, "good": "down"},
        {"label": "Tickets", "value": 312, "delta": 0.0, "trend": "flat", "good": "neutral"},
        {"label": "Latency p95", "value": None, "format": ",.0f"},
    ],
}


_CALENDAR_MULTI_YEAR_DATA = {
    "weekStart": 0,
    "colorScale": "diverging",
    "midpoint": 0,
    "data": [
        {"date": "2024-11-04", "value": -3}, {"date": "2024-11-18", "value": 2},
        {"date": "2024-12-02", "value": 5}, {"date": "2024-12-23", "value": -6},
        {"date": "2025-01-13", "value": 4}, {"date": "2025-02-10", "value": -1},
        {"date": "2025-03-03", "value": 7}, {"date": "2025-03-04", "value": -2},
    ],
}


_VORONOI_OVERLAY_DATA = {
    "series": [
        {
            "name": "Depots",
            "points": [
                {"x": 0, "y": 0, "label": "D1"}, {"x": 10, "y": 2, "label": "D2"},
                {"x": 4, "y": 6, "label": "D3"}, {"x": 9, "y": 9, "label": "D4"},
                {"x": 2, "y": 10, "label": "D5"}, {"x": 4, "y": 6, "label": "D3 (duplicate)"},
            ],
        },
    ],
}


_SPIRAL_DAY_DATA = {
    "cycle": "day",
    "series": [
        {
            "name": "Requests per hour",
            "points": [
                {"t": "2025-03-03T00:00", "value": 120}, {"t": "2025-03-03T04:00", "value": 60},
                {"t": "2025-03-03T08:00", "value": 480}, {"t": "2025-03-03T12:00", "value": 620},
                {"t": "2025-03-03T16:00", "value": 540}, {"t": "2025-03-03T20:00", "value": 300},
                {"t": "2025-03-04T00:00", "value": 140}, {"t": "2025-03-04T04:00", "value": None},
                {"t": "2025-03-04T08:00", "value": 510}, {"t": "2025-03-04T12:00", "value": 680},
                {"t": "2025-03-04T16:00", "value": 560}, {"t": "2025-03-04T20:00", "value": 330},
            ],
        },
    ],
}


_SPIRAL_YEAR_DATA = {
    "cycle": "year",
    "series": [
        {
            "name": "Rainfall (mm)",
            "points": [
                {"t": "2023-01-15", "value": 78}, {"t": "2023-03-15", "value": 61},
                {"t": "2023-05-15", "value": 49}, {"t": "2023-07-15", "value": 22},
                {"t": "2023-09-15", "value": 55}, {"t": "2023-11-15", "value": 90},
                {"t": "2024-01-15", "value": 84}, {"t": "2024-03-15", "value": 58},
                {"t": "2024-05-15", "value": 40}, {"t": "2024-07-15", "value": 18},
                {"t": "2024-09-15", "value": 63}, {"t": "2024-11-15", "value": 97},
            ],
        },
    ],
}


_PIXEL_LABELS_DATA = {
    "xDimension": "Build",
    "yDimension": "Test suite",
    "valueMeasure": "Δ duration (s)",
    "colorScale": "diverging",
    "xCategories": ["#101", "#102", "#103", "#104", "#105"],
    "bins": [
        {"x": "#101", "y": "unit", "value": -2}, {"x": "#102", "y": "unit", "value": 1},
        {"x": "#103", "y": "unit", "value": 0}, {"x": "#104", "y": "unit", "value": 4},
        {"x": "#101", "y": "integration", "value": 12}, {"x": "#102", "y": "integration", "value": -8},
        {"x": "#104", "y": "integration", "value": 15}, {"x": "#105", "y": "integration", "value": -3},
        {"x": "#103", "y": "browser", "value": 25}, {"x": "#105", "y": "browser", "value": -20},
        {"x": "#105", "y": "browser", "value": -5},
    ],
}


_GLYPH_STAR_DATA = {
    "glyphType": "star",
    "scale": "relative",
    "axes": ["Price ($)", "Range (km)", "Seats", "Charge (kW)"],
    "grid": {"cols": 3},
    "series": [
        {"name": "Hatchback", "values": [28000, 320, 5, 100]},
        {"name": "Saloon", "values": [42000, 510, 5, 170]},
        {"name": "SUV", "values": [55000, 450, 7, 150]},
        {"name": "Van", "values": [48000, 300, 8, None]},
        {"name": "Roadster", "values": [61000, 390, 2, 250]},
    ],
}


_FACETED_LINE_DATA = {
    "childType": "line",
    "categories": ["W1", "W2", "W3", "W4", "W5"],
    "grid": {"cols": 3},
    "panels": [
        {"label": "Web", "series": [{"name": "Errors", "values": [12, 9, 14, 8, 6]}]},
        {"label": "API", "series": [{"name": "Errors", "values": [140, 160, 120, None, 95]}]},
        {"label": "Batch", "series": [{"name": "Errors", "values": [2, 1, 3, 2, 1]}]},
    ],
}


_FACETED_GAUGE_DATA = {
    "childType": "gauge",
    "grid": {"cols": 3},
    "panels": [
        {"label": "CPU", "gauge": {"value": 62, "unit": "%"}},
        {"label": "Memory", "gauge": {"value": 81, "unit": "%",
                                       "thresholds": [{"value": 80, "label": "High", "color": "--mj-color-danger"}]}},
        {"label": "Disk", "gauge": {"value": 37, "unit": "%"}},
    ],
}


# ---------------------------------------------------------------------------
# Shared notes and options
# ---------------------------------------------------------------------------

_FORMAT_NOTE = (
    "<p><code>format</code> is a number format: a d3-style string "
    "<code>[$][,][.precision][f|d|e|s|%]</code> (<code>\",.0f\"</code>, <code>\".1%\"</code>, "
    "<code>\"$,.2f\"</code>, <code>\".3s\"</code>), the keywords <code>\"compact\"</code>, "
    "<code>\"percent\"</code>, <code>\"integer\"</code>, or an "
    "<code>Intl.NumberFormat</code> options object.</p>"
)

_TABLE_SHAPE = (
    "<pre><code>{\n"
    "  columns: [{ key: string, label?: string, type?: \"number\" | \"string\",\n"
    "              render?: \"bar\", domain?: [min, max], format? }],\n"
    "  rows: [{ [key]: value, label?: string }],  // label: row header when no column uses it\n"
    "  domain?: [min, max]                       // colour (heatmap) or bar (bar-in-cell) domain\n"
    "}</code></pre>"
    "<p>A column without <code>type</code> is numeric when all its values are numbers. The "
    "first column (or <code>rows[].label</code>) is the row header. The table scrolls inside "
    "the chart when it does not fit, with a sticky header; cells are focusable "
    "(one tab stop, arrow keys move).</p>"
)

_ORIENTATION_OPTION = AttributeDoc(
    name="orientation", description="Layout direction.", kind="enum",
    values=["horizontal", "vertical"], default="horizontal")

_DIVERGING_VARIANT_OPTION = AttributeDoc(
    name="variant",
    description="`diverging` forces the diverging ramp (around `midpoint`); any other value leaves "
                "the data's `colorScale` in charge.",
    kind="enum", values=["diverging"])

_CELL_EVENT_NOTE = (
    "<p>Cells emit <code>mj-chart-cell-click</code> <code>{ row, column, value }</code> (row "
    "index, column key) on click or Enter.</p>"
)


# ---------------------------------------------------------------------------
# UX / product / business
# ---------------------------------------------------------------------------

_UX = [

    ChartTypeDoc(
        type_key="gauge",
        title="Gauge",
        category="ux-product-business",
        summary="Arc dial showing one value against a min / max range with threshold bands.",
        description=(
            "A speedometer-style dial. Each entry of gauge.thresholds starts a band that runs to "
            "the next threshold (or max), drawn as a ring outside the track in the threshold's "
            "colour (a CSS colour or a custom-property name such as \"--mj-color-success\"; "
            "without one, a palette step); the range below the first threshold is neutral and "
            "the value arc takes the colour of the band the value falls in. The value label "
            "sits under the needle pivot. start_angle and sweep_angle set the arc (sweep 360 "
            "draws a progress ring). A value outside the range pins the needle and says so; a "
            "missing value shows a no-data dial and min >= max a message. The dial is one "
            "focusable mark emitting mj-chart-gauge-click."
        ),
        data_shape=(
            "<pre><code>{\n"
            "  gauge: {\n"
            "    value: number | string | null,      // a numeric string is accepted\n"
            "    min?: number, max?: number,         // default 0 / 100\n"
            "    unit?: string,                      // appended to the numbers\n"
            "    thresholds?: [{ value: number, label?: string, color?: string }],\n"
            "    needle?: boolean,                   // default true\n"
            "    start_angle?: number,               // degrees from 12 o'clock, default -135\n"
            "    sweep_angle?: number                // default 270; 360 = ring; negative = counter-clockwise\n"
            "  }\n"
            "}</code></pre>"
        ),
        options=[],
        examples=[
            chart_example(
                "basic", "Dial with bands",
                "<p>72% on a 0-100 dial with Fair and Good bands; the arc takes the Good "
                "colour.</p>",
                "gauge", _GAUGE_DATA),
            chart_example(
                "progress-ring", "Progress ring",
                "<p><code>sweep_angle: 360</code>, <code>start_angle: 0</code> and no needle: "
                "a ring with the value centred.</p>",
                "gauge", _GAUGE_RING_DATA),
            chart_example(
                "semicircle", "Half dial, palette bands",
                "<p>A 180° dial from -90°; thresholds without a colour get palette steps, the "
                "red line uses a token.</p>",
                "gauge", _GAUGE_SEMICIRCLE_DATA),
            chart_example(
                "out-of-range", "Out of range",
                "<p>112 °C on a 0-100 dial: the needle is pinned to the end and the label says "
                "\"above range\".</p>",
                "gauge", _GAUGE_OUT_OF_RANGE_DATA),
            events_example(
                "gauge", _GAUGE_DATA, ["mj-chart-gauge-click"],
                "<p>The dial emits <code>mj-chart-gauge-click</code> <code>{ value, min, max "
                "}</code>.</p>"),
        ],
    ),

    ChartTypeDoc(
        type_key="kpi",
        title="KPI Card",
        category="ux-product-business",
        summary="Big-number metric card with a change badge and an optional sparkline.",
        description=(
            "Shows a headline value fitted to the card width and formatted with kpi.format, a "
            "sub-label, a change badge computed from kpi.comparison (the absolute change when "
            "the baseline is 0) and an optional sparkline (nulls are gaps). kpi.trend overrides "
            "the arrow; kpi.good (up, down or neutral) decides whether a change is coloured as "
            "good or bad. A missing value shows a dash, never 0. The card is one focusable "
            "mark emitting mj-chart-kpi-click."
        ),
        data_shape=(
            "<pre><code>{\n"
            "  kpi: {\n"
            "    value: number | string | null,\n"
            "    label?: string,\n"
            "    format?: string | object,           // see below\n"
            "    comparison?: { value: number, label?: string },\n"
            "    trend?: \"up\" | \"down\" | \"flat\",   // default: from the comparison\n"
            "    good?: \"up\" | \"down\" | \"neutral\", // default \"up\"\n"
            "    spark?: (number | null)[]\n"
            "  }\n"
            "}</code></pre>" + _FORMAT_NOTE
        ),
        options=[],
        examples=[
            chart_example(
                "basic", "Monthly active users",
                "<p>Value, label, change against last month and a sparkline.</p>",
                "kpi", _KPI_DATA),
            chart_example(
                "good-down", "Lower is better",
                "<p><code>good: \"down\"</code>: the fall in spend is shown as good; the null "
                "month is a gap in the sparkline.</p>",
                "kpi", _KPI_GOOD_DOWN_DATA),
            chart_example(
                "zero-baseline", "Zero baseline",
                "<p>Against a baseline of 0 the percentage is undefined, so the absolute change "
                "is shown.</p>",
                "kpi", _KPI_ZERO_BASELINE_DATA),
            chart_example(
                "no-value", "Missing value",
                "<p>A null value shows a dash, not 0.</p>",
                "kpi", _KPI_NO_VALUE_DATA),
            events_example(
                "kpi", _KPI_DATA, ["mj-chart-kpi-click"],
                "<p>The card emits <code>mj-chart-kpi-click</code> <code>{ value, label }</code>.</p>"),
        ],
    ),

    ChartTypeDoc(
        type_key="cohort",
        title="Cohort Retention Grid",
        category="ux-product-business",
        summary="Heat-coloured grid of retention per cohort (rows) and period (columns).",
        description=(
            "Each row is a cohort with its label and size; each column a period. mode \"rate\" "
            "(default) reads retention as fractions or percentages (decided once for the whole "
            "data set, or set with unit); mode \"count\" reads user counts and colours each "
            "cell by count / size. The mode attribute overrides the data's mode. Values are "
            "printed when they fit; periods a cohort has not reached and periods without a "
            "number are greyed out, and a 0-100% colour key is drawn under the grid. Cells emit "
            "mj-chart-cohort-click. The same data as curves is type=\"retention\"."
        ),
        data_shape=(
            "<pre><code>{\n"
            "  cohorts: [{ label: string, size?: number, periods: (number | null)[] }],\n"
            "  period_labels?: string[],\n"
            "  mode?: \"rate\" | \"count\",              // the mode attribute wins\n"
            "  unit?: \"fraction\" | \"percent\"         // rate mode; default: guessed (percent when any rate > 1)\n"
            "}</code></pre>"
            "<p>In count mode the rate is count / size (or / the first period without a "
            "size).</p>"
        ),
        options=[
            AttributeDoc(name="mode", description="How `periods` are read; overrides the data's `mode`.",
                         kind="enum", values=["rate", "count"], default="rate"),
        ],
        examples=[
            chart_example(
                "basic", "Weekly retention rates",
                "<p>Five monthly cohorts as fractions; later cohorts have fewer periods.</p>",
                "cohort", _COHORT_DATA),
            chart_example(
                "counts", "User counts",
                "<p><code>mode=\"count\"</code>: periods are user counts, coloured by count / "
                "size; the null is a period without data.</p>",
                "cohort", _COHORT_COUNT_DATA, attributes={"mode": "count"}),
            chart_example(
                "percent", "Percentages",
                "<p><code>unit: \"percent\"</code>: periods are given as 0-100.</p>",
                "cohort", _COHORT_PERCENT_DATA),
            events_example(
                "cohort", _COHORT_DATA, ["mj-chart-cohort-click"],
                "<p>Cells emit <code>mj-chart-cohort-click</code> <code>{ cohort, period, "
                "value, rate }</code> (rate as a fraction).</p>"),
        ],
    ),

    ChartTypeDoc(
        type_key="retention",
        title="Retention Curve",
        category="ux-product-business",
        summary="Retention curves: one line per cohort over the periods on a 0-100% axis.",
        description=(
            "Draws the cohort data as retention curves (also registered as "
            "type=\"retention-curve\"): one line per cohort, retention on a 0-100% axis, "
            "periods along the bottom, and a legend of cohorts. Accepts the cohort data shape "
            "(cohorts, period_labels, mode, unit); periods without data are gaps in the line. "
            "Points emit mj-chart-cohort-click."
        ),
        data_shape=(
            "<pre><code>{\n"
            "  cohorts: [{ label: string, size?: number, periods: (number | null)[] }],\n"
            "  period_labels?: string[],\n"
            "  mode?: \"rate\" | \"count\", unit?: \"fraction\" | \"percent\"\n"
            "}</code></pre>"
            "<p>The same data and modes as <code>cohort</code>.</p>"
        ),
        options=[
            AttributeDoc(name="mode", description="How `periods` are read; overrides the data's `mode`.",
                         kind="enum", values=["rate", "count"], default="rate"),
        ],
        examples=[
            chart_example(
                "basic", "Quarterly cohorts",
                "<p>Four cohorts as curves with a legend of cohorts.</p>",
                "retention", _RETENTION_DATA, legend=True),
            chart_example(
                "counts", "From user counts",
                "<p><code>mode=\"count\"</code> turns counts into rates; the null is a gap.</p>",
                "retention", _COHORT_COUNT_DATA, attributes={"mode": "count"}, legend=True),
            events_example(
                "retention", _RETENTION_DATA, ["mj-chart-cohort-click"],
                "<p>Points emit <code>mj-chart-cohort-click</code> <code>{ cohort, period, "
                "value, rate }</code>.</p>",
                legend=True),
        ],
    ),

    ChartTypeDoc(
        type_key="user-journey",
        title="User Journey Map",
        category="ux-product-business",
        summary="Emotion-score line across journey steps with touchpoint and pain-point markers.",
        description=(
            "Draws a satisfaction score across ordered steps, left to right by default "
            "(orientation=\"vertical\" runs top to bottom). Steps are placed by position, a "
            "step without a score is a gap and scores are clamped into score_range. Node size "
            "encodes the number of touchpoints and a red dot marks steps with pain_points. "
            "Several personas (personas: [{name, steps}] or an array of step arrays) get their "
            "own colour and a legend. Steps emit mj-chart-journey-click."
        ),
        data_shape=(
            "<pre><code>{\n"
            "  steps: [{ label: string, score: number | null,\n"
            "            touchpoints?: string[], pain_points?: string[] }],\n"
            "  // or several personas: personas: [{ name, steps: [...] }] | [[...], [...]]\n"
            "  score_range?: [min, max]              // default [1, 5]\n"
            "}</code></pre>"
        ),
        options=[_ORIENTATION_OPTION],
        examples=[
            chart_example(
                "basic", "Purchase journey",
                "<p>Five steps; hover a step for its touchpoints and pain points.</p>",
                "user-journey", _USER_JOURNEY_DATA),
            chart_example(
                "personas", "Two personas",
                "<p>Two personas on shared step columns, each in its own colour with a "
                "legend.</p>",
                "user-journey", _JOURNEY_PERSONAS_DATA, legend=True),
            chart_example(
                "gap-and-clamp", "Gap, clamped score, vertical",
                "<p><code>orientation=\"vertical\"</code>; the Tour step has no score (a gap) "
                "and 3.5 is clamped to the top of <code>score_range [-2, 2]</code>.</p>",
                "user-journey", _JOURNEY_GAP_DATA, attributes={"orientation": "vertical"}, height=360),
            events_example(
                "user-journey", _USER_JOURNEY_DATA, ["mj-chart-journey-click"],
                "<p>Steps emit <code>mj-chart-journey-click</code> <code>{ label, score, "
                "touchpoints, pain_points, persona, index }</code>.</p>"),
        ],
    ),

    ChartTypeDoc(
        type_key="session-flow",
        title="Session Flow",
        category="ux-product-business",
        summary="Sankey-style navigation flow: page nodes and session bands between them.",
        description=(
            "Nodes are placed in columns by their longest path from an entry page, each node's "
            "size is max(inflow, outflow), and links are bands whose widths stack along the "
            "node edges. Cycles such as back-navigation or self-links are detected and drawn "
            "as return arcs below the flow instead of taking part in the column layout. Flows "
            "run left to right by default; orientation=\"vertical\" runs top to bottom. Nodes "
            "emit mj-chart-flow-click."
        ),
        data_shape=(
            "<pre><code>{\n"
            "  nodes: [{ id: string, label?: string }],\n"
            "  links: [{ source: id, target: id, value: number }]\n"
            "}</code></pre>"
        ),
        options=[_ORIENTATION_OPTION],
        examples=[
            chart_example(
                "basic", "Shop sessions",
                "<p>Home to checkout with exits; product back to catalog is a return arc.</p>",
                "session-flow", _SESSION_FLOW_DATA, height=300),
            chart_example(
                "cycles", "Back-navigation and a self-link",
                "<p>Pricing back to Landing and Docs to Docs are drawn as return arcs; node "
                "sizes are max(inflow, outflow).</p>",
                "session-flow", _SESSION_FLOW_SMALL_DATA, height=300),
            chart_example(
                "vertical", "Top to bottom",
                "<p><code>orientation=\"vertical\"</code>.</p>",
                "session-flow", _SESSION_FLOW_DATA, attributes={"orientation": "vertical"}, height=420),
            events_example(
                "session-flow", _SESSION_FLOW_DATA, ["mj-chart-flow-click"],
                "<p>Nodes emit <code>mj-chart-flow-click</code> <code>{ id, label, flow, "
                "inflow, outflow }</code>.</p>",
                height=300),
        ],
    ),
]


# ---------------------------------------------------------------------------
# Text / categorical
# ---------------------------------------------------------------------------

_SETS_SHAPE = (
    "<pre><code>{\n"
    "  sets: [{ name: string, size: number }],          // 1 to 3 sets\n"
    "  intersections?: [{ sets: string[], size: number }], // inclusive sizes\n"
    "  proportional?: boolean\n"
    "}</code></pre>"
    "<p>|A ∩ B| counts the triple region too. With 4 or more sets the chart shows a message "
    "recommending <code>type=\"upset\"</code> and emits <code>mj-chart-error</code>.</p>"
)

_TEXT = [

    ChartTypeDoc(
        type_key="word-cloud",
        title="Word Cloud",
        category="text-categorical",
        summary="Tag cloud where a word's area tracks its value (square-root font scale).",
        description=(
            "Words are placed greedily on an Archimedean spiral stretched to the chart and "
            "reaching its corners, using measured text boxes. Font size follows a zero-based "
            "square-root scale, so a word's area (font size squared) is proportional to its "
            "value and equal values get equal sizes; all sizes shrink together when the words "
            "would not fit, and a word that still does not fit is retried smaller before it is "
            "left out (the table lists every word). rotation \"mixed\" turns every fourth word "
            "vertical; max_words caps the list (default 80). Words emit mj-chart-word-click."
        ),
        data_shape=(
            "<pre><code>{\n"
            "  words: [{ text: string, value: number }], // others are skipped\n"
            "  max_words?: number,                   // default 80; 0 draws nothing\n"
            "  rotation?: \"none\" | \"mixed\"          // default \"none\"\n"
            "}</code></pre>"
        ),
        options=[],
        examples=[
            chart_example(
                "basic", "Technologies",
                "<p>Fifteen words by mention count, with mixed rotation.</p>",
                "word-cloud", _WORD_CLOUD_DATA),
            chart_example(
                "top-five", "Capped list",
                "<p><code>max_words: 5</code> keeps the five largest; <code>rotation: "
                "\"none\"</code> keeps them horizontal.</p>",
                "word-cloud", with_changes(_WORD_CLOUD_DATA, max_words=5, rotation="none")),
            chart_example(
                "equal-values", "Equal values",
                "<p>Six words with the same value are drawn at the same size.</p>",
                "word-cloud", _WORD_CLOUD_EQUAL_DATA),
            events_example(
                "word-cloud", _WORD_CLOUD_DATA, ["mj-chart-word-click"],
                "<p>Words emit <code>mj-chart-word-click</code> <code>{ text, value }</code>.</p>"),
        ],
    ),

    ChartTypeDoc(
        type_key="venn",
        title="Venn Diagram",
        category="text-categorical",
        summary="Overlapping circles showing membership and intersection sizes of 1 to 3 sets.",
        description=(
            "By default the venn type is schematic: equal circles in the classic 2- or 3-set "
            "arrangement so every region is visible, with the sizes printed in the regions. "
            "proportional: true switches to the Euler layout (circle area proportional to set "
            "size, pairwise overlaps fitted to the declared intersections). With 4 or more sets "
            "the chart shows a message recommending type=\"upset\". Each set is focusable and "
            "emits mj-chart-venn-click; the legend names the sets."
        ),
        data_shape=_SETS_SHAPE + "<p><code>proportional</code> defaults to false for venn.</p>",
        options=[],
        examples=[
            chart_example(
                "basic", "Three teams",
                "<p>Schematic layout: every region visible, sizes printed.</p>",
                "venn", _VENN_DATA, legend=True),
            chart_example(
                "two-sets", "Two sets",
                "<p>The classic two-circle arrangement.</p>",
                "venn", _VENN_TWO_DATA, legend=True),
            chart_example(
                "proportional", "Proportional layout",
                "<p>The three teams with <code>proportional: true</code>: circle areas and "
                "overlaps follow the sizes.</p>",
                "venn", with_changes(_VENN_DATA, proportional=True), legend=True),
            chart_example(
                "too-many-sets", "Four sets",
                "<p>Four sets cannot be drawn: a message recommends <code>upset</code> and "
                "<code>mj-chart-error</code> appears in Events.</p>",
                "venn", _VENN_FOUR_DATA),
            events_example(
                "venn", _VENN_DATA, ["mj-chart-venn-click", "mj-chart-error"],
                "<p>Sets emit <code>mj-chart-venn-click</code> <code>{ name, size }</code>.</p>",
                legend=True),
        ],
    ),

    ChartTypeDoc(
        type_key="euler",
        title="Euler Diagram",
        category="text-categorical",
        summary="Proportional set diagram: circle and overlap areas follow the set sizes.",
        description=(
            "Proportional by default: circle area is proportional to set size (no minimum "
            "radius), and the centre distance of each pair is found so the overlap area matches "
            "the declared intersection. An undeclared pair is disjoint and an intersection equal "
            "to the smaller set nests it inside the other. Three sets are placed from the three "
            "pairwise distances; the triple region is labelled but not fitted. proportional: "
            "false gives the schematic venn layout. Sets emit mj-chart-venn-click."
        ),
        data_shape=_SETS_SHAPE + "<p><code>proportional</code> defaults to true for euler.</p>",
        options=[],
        examples=[
            chart_example(
                "basic", "Nested sets",
                "<p>All paid users are subscribers: the intersection equals the smaller set, "
                "so Paid is drawn inside Subscribers.</p>",
                "euler", _EULER_DATA, legend=True),
            chart_example(
                "three-sets", "Three languages",
                "<p>Three sets placed from their pairwise overlaps; the triple size is printed "
                "but not fitted.</p>",
                "euler", _EULER_THREE_DATA, legend=True),
            chart_example(
                "disjoint", "Disjoint sets",
                "<p>Enterprise has no declared intersection, so it is drawn apart.</p>",
                "euler", _EULER_DISJOINT_DATA, legend=True),
            events_example(
                "euler", _EULER_THREE_DATA, ["mj-chart-venn-click"],
                "<p>Sets emit <code>mj-chart-venn-click</code> <code>{ name, size }</code>.</p>",
                legend=True),
        ],
    ),

    ChartTypeDoc(
        type_key="upset",
        title="UpSet Plot",
        category="text-categorical",
        summary="Set intersections as bars over a membership dot matrix, for many sets.",
        description=(
            "Top: bars with value labels for each intersection, sorted by size (sort=\"degree\" "
            "orders by the number of sets). Below: a dot matrix showing which sets take part "
            "in each intersection, joined by a line. Left: bars with values for the set sizes. "
            "Intersections naming unknown sets are dropped and repeats drawn once; elements "
            "(one list of set names per element) computes the exclusive intersections and the "
            "set sizes instead. When columns would be narrower than about 14px (or more than "
            "max_columns) only the largest are drawn and a note says how many were left out. "
            "Intersection bars emit mj-chart-upset-click and set bars mj-chart-upset-set-click."
        ),
        data_shape=(
            "<pre><code>{\n"
            "  sets: [{ name: string, size?: number }],\n"
            "  intersections?: [{ sets: string[], size: number }], // drawn as given\n"
            "  elements?: (string[] | { sets: string[] })[],      // computes exclusive intersections\n"
            "  max_columns?: number\n"
            "}</code></pre>"
        ),
        options=[
            AttributeDoc(name="sort", description="Intersection order.", kind="enum",
                         values=["size", "degree"], default="size"),
        ],
        examples=[
            chart_example(
                "basic", "Notification channels",
                "<p>Four channels and nine intersections, largest first.</p>",
                "upset", _UPSET_DATA, height=300),
            chart_example(
                "by-degree", "Sorted by degree",
                "<p><code>sort=\"degree\"</code> groups the single-set columns first.</p>",
                "upset", _UPSET_DATA, attributes={"sort": "degree"}, height=300),
            chart_example(
                "elements", "From elements, capped",
                "<p>Twelve issues listed by their labels: intersections and set sizes are "
                "computed; <code>max_columns: 5</code> shows the five largest.</p>",
                "upset", with_changes(_UPSET_ELEMENTS_DATA, max_columns=5), height=300),
            events_example(
                "upset", _UPSET_DATA, ["mj-chart-upset-click", "mj-chart-upset-set-click"],
                "<p>Intersection bars emit <code>mj-chart-upset-click</code> <code>{ sets, size "
                "}</code>; set bars emit <code>mj-chart-upset-set-click</code> <code>{ name, "
                "size }</code>.</p>",
                height=300),
        ],
    ),

    ChartTypeDoc(
        type_key="matrix",
        title="Matrix Chart",
        category="text-categorical",
        summary="Row x column grid of categories with bubble (circle) or filled square marks.",
        description=(
            "mark \"circle\" (default) sizes bubbles on a square-root scale so area encodes "
            "|value|; negative values use the second palette colour and the legend names both "
            "signs. mark \"square\" fills cells with a sequential ramp (diverging around 0 with "
            "negative values) and prints the value when it fits. x_categories / y_categories "
            "are optional (derived from the cells in first-seen order); a repeated x / y pair "
            "adds up; a zero is a real value and a missing cell is blank. Cells with a value "
            "emit mj-chart-matrix-click. Square labels are black or white for contrast with the "
            "fill. The accessible table's corner header is meta.yLabel (default \"Row\")."
        ),
        data_shape=(
            "<pre><code>{\n"
            "  x_categories?: string[], y_categories?: string[],\n"
            "  cells: [{ x: string, y: string, value: number }],\n"
            "  mark?: \"circle\" | \"square\",        // default \"circle\"\n"
            "  meta?: { yLabel?: string }          // names the row categories\n"
            "}</code></pre>"
        ),
        options=[],
        examples=[
            chart_example(
                "basic", "Regional sales",
                "<p>Bubbles for four regions by quarter.</p>",
                "matrix", _MATRIX_DATA),
            chart_example(
                "squares", "Squares, derived categories",
                "<p><code>mark: \"square\"</code> with categories derived from the cells; the "
                "zero is drawn, the missing API / Tue cell is blank.</p>",
                "matrix", _MATRIX_SQUARE_DATA),
            chart_example(
                "signed", "Negative values",
                "<p>Correlations with both signs: negative bubbles use a second colour, named "
                "in the legend.</p>",
                "matrix", _MATRIX_SIGNED_DATA, legend=True),
            events_example(
                "matrix", _MATRIX_DATA, ["mj-chart-matrix-click"],
                "<p>Cells emit <code>mj-chart-matrix-click</code> <code>{ x, y, value }</code>.</p>"),
        ],
    ),
]


# ---------------------------------------------------------------------------
# Tables with visual encoding
# ---------------------------------------------------------------------------

_ICON_SHAPE = (
    "<pre><code>{\n"
    "  series: [{ name: string, count: number, icon?: \"circle\" | \"square\" | \"person\",\n"
    "             color?: string }],\n"
    "  total?: number,                       // slots; default the sum of the counts\n"
    "  grid?: { cols: number },              // default 10\n"
    "  per_icon?: number                     // units per icon; chosen automatically above 400 icons\n"
    "}</code></pre>"
    "<p>Icon counts are rounded with the largest-remainder method so they add up; counts above "
    "the total are cut at the total and the chart says so. Only <code>total</code> slots are "
    "outlined. The grid is centred and a wrapping legend (name, count, share) is drawn "
    "below.</p>"
)

def _icon_options(default_icon: str) -> "list[AttributeDoc]":
    """
        The option docs of the icon-array family.

        :param default_icon: The type's default icon.

        :returns: The AttributeDoc list.
    """

    options = [
        AttributeDoc(name="icon", description="Default icon for series without `icon`.", kind="enum",
                     values=["circle", "square", "person"], default=default_icon),
        AttributeDoc(name="mode", description="Same as `icon` (read when `icon` is absent).", kind="enum",
                     values=["circle", "square", "person"]),
        AttributeDoc(name="orientation", description="`horizontal` fills rows left to right, `vertical` "
                     "fills columns top to bottom.", kind="enum", values=["horizontal", "vertical"],
                     default="horizontal"),
    ]
    return options

_TABLES = [

    ChartTypeDoc(
        type_key="heatmap-table",
        title="Heatmap Table",
        category="tables-visual-encoding",
        summary="A real table whose numeric cells are filled by value (sequential or diverging).",
        description=(
            "Draws a DOM table (header row, row headers, selectable text) inside the chart whose "
            "numeric cells are filled by value, with a colour key above it. colorScale "
            "\"sequential\" (default) or \"diverging\" (around midpoint, default 0; the variant "
            "attribute \"diverging\" does the same); domain sets the colour range, else it is "
            "computed across all numeric cells (scale \"column\" gives each numeric column its "
            "own range). Each cell's text is black or white, whichever contrasts more with its "
            "fill (at least 4.5:1 in both themes). Cells emit mj-chart-cell-click."
        ),
        data_shape=(
            _TABLE_SHAPE.replace("}</code></pre>",
                                 "  colorScale?: \"sequential\" | \"diverging\", midpoint?: number,\n"
                                 "  scale?: \"table\" | \"column\"           // one colour domain, or one per column\n"
                                 "}</code></pre>")
            + _FORMAT_NOTE + _CELL_EVENT_NOTE
        ),
        options=[_DIVERGING_VARIANT_OPTION],
        examples=[
            chart_example(
                "basic", "Regional scores",
                "<p>Five regions by month on a sequential ramp.</p>",
                "heatmap-table", _HEATMAP_TABLE_DATA),
            chart_example(
                "diverging", "Diverging with formats",
                "<p><code>colorScale: \"diverging\"</code> around 0 with signed percentages "
                "(an <code>Intl.NumberFormat</code> options object); the null cell stays "
                "empty.</p>",
                "heatmap-table", _HEATMAP_TABLE_DIVERGING_DATA),
            chart_example(
                "per-column", "One scale per column",
                "<p><code>scale: \"column\"</code>: visits, conversion and revenue are each "
                "coloured on their own range.</p>",
                "heatmap-table", _HEATMAP_TABLE_COLUMNS_DATA),
            events_example(
                "heatmap-table", _HEATMAP_TABLE_DATA, ["mj-chart-cell-click"],
                "<p>Cells emit <code>mj-chart-cell-click</code> <code>{ row, column, value "
                "}</code>.</p>"),
        ],
    ),

    ChartTypeDoc(
        type_key="bar-in-cell",
        title="Bar-in-Cell Table",
        category="tables-visual-encoding",
        summary="A real table with small horizontal bars drawn inside numeric cells.",
        description=(
            "Columns with render \"bar\" draw an in-cell bar from zero, so bar length is "
            "proportional to the value (the automatic domain always includes 0; negative values "
            "draw left of a zero line), followed by the value formatted with the column's "
            "format. Other columns show their text. The bar domain can be set per column "
            "(columns[].domain) or for the table (domain). Cells emit mj-chart-cell-click."
        ),
        data_shape=_TABLE_SHAPE + _FORMAT_NOTE + _CELL_EVENT_NOTE,
        options=[],
        examples=[
            chart_example(
                "basic", "Product revenue",
                "<p>Revenue and units as bars, margin as text.</p>",
                "bar-in-cell", _BAR_IN_CELL_DATA),
            chart_example(
                "signed", "Negative values and a fixed domain",
                "<p>Changes against plan draw either side of a zero line; Share uses "
                "<code>domain: [0, 1]</code>; the null change draws no bar.</p>",
                "bar-in-cell", _BAR_IN_CELL_SIGNED_DATA),
            events_example(
                "bar-in-cell", _BAR_IN_CELL_DATA, ["mj-chart-cell-click"],
                "<p>Cells emit <code>mj-chart-cell-click</code> <code>{ row, column, value "
                "}</code>.</p>"),
        ],
    ),

    ChartTypeDoc(
        type_key="conditional-format-table",
        title="Conditional Format Table",
        category="tables-visual-encoding",
        summary="A real table with rules-based cell fills, text colours, weights and icons.",
        description=(
            "Rules are tested in order and the first match styles the cell. Ops: lt, lte, gt, "
            "gte, eq, neq, contains; numbers compare numerically and text compares as text. A "
            "rule without column applies to every cell. style.fill and style.color take any CSS "
            "colour, style.weight a font weight and style.icon \"warning\", \"check\", \"info\" "
            "or \"cross\". The tooltip names the matched rule. Cells emit mj-chart-cell-click."
        ),
        data_shape=(
            _TABLE_SHAPE.replace("}</code></pre>",
                                 "  rules: [{ column?: key, op: \"lt\" | \"lte\" | \"gt\" | \"gte\" | \"eq\" | \"neq\" | \"contains\",\n"
                                 "            value: number | string,\n"
                                 "            style: { fill?, color?, weight?, icon? } }]\n"
                                 "}</code></pre>")
            + _CELL_EVENT_NOTE
        ),
        options=[],
        examples=[
            chart_example(
                "basic", "Service levels",
                "<p>Numeric rules colour vs Target and add icons; a text rule bolds the latency "
                "row's metric.</p>",
                "conditional-format-table", _CONDITIONAL_FORMAT_TABLE_DATA),
            chart_example(
                "text-rules", "Text rules and colours",
                "<p><code>eq</code> rules on a status column, a text-colour rule on p99 and a "
                "rule without <code>column</code> that marks every cell containing "
                "\"discovery\".</p>",
                "conditional-format-table", _CONDITIONAL_TEXT_DATA),
            events_example(
                "conditional-format-table", _CONDITIONAL_FORMAT_TABLE_DATA, ["mj-chart-cell-click"],
                "<p>Cells emit <code>mj-chart-cell-click</code> <code>{ row, column, value "
                "}</code>.</p>"),
        ],
    ),

    ChartTypeDoc(
        type_key="icon-array",
        title="Icon Array",
        category="tables-visual-encoding",
        summary="Grid of countable unit icons (circle, square or person) coloured by series.",
        description=(
            "Icons are placed in series order, rows left to right by default "
            "(orientation=\"vertical\" fills columns). The icon comes from the series, else the "
            "icon (or mode) attribute, else circle. total sets the number of slots (default the "
            "sum of the counts); counts are rounded so they add up, counts above the total are "
            "cut and the chart says so, and large totals use one icon per per_icon units. Each "
            "series is one focusable group emitting mj-chart-icon-click."
        ),
        data_shape=_ICON_SHAPE,
        options=_icon_options("circle"),
        examples=[
            chart_example(
                "basic", "Treatment outcomes",
                "<p>100 people as person icons, ten per row.</p>",
                "icon-array", _ICON_ARRAY_DATA, height=300),
            chart_example(
                "per-icon", "One icon per 100",
                "<p>12,000 people with <code>per_icon: 100</code>: 120 icons, 20 per row.</p>",
                "icon-array", _ICON_ARRAY_LARGE_DATA, height=300),
            chart_example(
                "over-total", "Counts above the total, vertical",
                "<p>23 requested for 20 seats: the counts are cut at the total and the chart "
                "says so; <code>orientation=\"vertical\"</code> fills columns.</p>",
                "icon-array", _ICON_ARRAY_OVER_DATA, attributes={"orientation": "vertical"}),
            events_example(
                "icon-array", _ICON_ARRAY_DATA, ["mj-chart-icon-click"],
                "<p>Series groups emit <code>mj-chart-icon-click</code> <code>{ series, count "
                "}</code>.</p>",
                height=300),
        ],
    ),

    ChartTypeDoc(
        type_key="waffle-pictograph",
        title="Waffle Pictograph",
        category="tables-visual-encoding",
        summary="The icon array with square icons by default: a waffle chart of unit squares.",
        description=(
            "The icon-array renderer with square icons by default; the icon of a series, or the "
            "icon / mode attribute, still wins. Same data, rounding, legend and events "
            "(mj-chart-icon-click) as icon-array."
        ),
        data_shape=_ICON_SHAPE,
        options=_icon_options("square"),
        examples=[
            chart_example(
                "basic", "Task status",
                "<p>100 squares for three task states.</p>",
                "waffle-pictograph", _WAFFLE_PICTOGRAPH_DATA, height=300),
            chart_example(
                "circle-icons", "Circles via the attribute",
                "<p><code>icon=\"circle\"</code> on series without their own icon.</p>",
                "waffle-pictograph", {
                    "total": 50,
                    "grid": {"cols": 10},
                    "series": [{"name": "Renewed", "count": 31}, {"name": "Lapsed", "count": 19}],
                },
                attributes={"icon": "circle"}),
            events_example(
                "waffle-pictograph", _WAFFLE_PICTOGRAPH_DATA, ["mj-chart-icon-click"],
                "<p>Series groups emit <code>mj-chart-icon-click</code> <code>{ series, count "
                "}</code>.</p>",
                height=300),
        ],
    ),

    ChartTypeDoc(
        type_key="scorecard",
        title="Scorecard",
        category="tables-visual-encoding",
        summary="Grid of KPI tiles: value, change, trend arrow, progress to target and sparkline.",
        description=(
            "Tiles wrap into rows of tiles at least about 150px wide (orientation "
            "\"horizontal\", the default) or stack one per row (\"vertical\"); columns sets the "
            "column count. Each tile has its own bands for label, value (formatted with format "
            "and fitted), change, progress bar and sparkline (dropped when there is no room). "
            "delta is a fractional change (0.12 = +12%); good \"down\" marks metrics where a "
            "fall is good. The progress bar shows attainment of target (target / value when "
            "lower is better). mode=\"compact\" shows only label and value. Tiles emit "
            "mj-chart-tile-click."
        ),
        data_shape=(
            "<pre><code>{\n"
            "  metrics: [{ label: string, value: number | string | null, format?,\n"
            "              target?: number, delta?: number,  // 0.12 = +12%\n"
            "              trend?: \"up\" | \"down\" | \"flat\", good?: \"up\" | \"down\" | \"neutral\",\n"
            "              sparkline?: (number | null)[] }],\n"
            "  columns?: number\n"
            "}</code></pre>" + _FORMAT_NOTE
        ),
        options=[
            AttributeDoc(name="mode", description="`compact` shows only label and value.", kind="enum",
                         values=["full", "compact"], default="full"),
            _ORIENTATION_OPTION,
        ],
        examples=[
            chart_example(
                "basic", "Three metrics",
                "<p>Revenue, churn (lower is better) and NPS with targets and sparklines.</p>",
                "scorecard", _SCORECARD_DATA),
            chart_example(
                "six-tiles", "Six tiles in three columns",
                "<p><code>columns: 3</code>, a flat neutral metric and a missing value (dash).</p>",
                "scorecard", _SCORECARD_SIX_DATA, height=300),
            chart_example(
                "compact", "Compact tiles",
                "<p><code>mode=\"compact\"</code>: label and value only.</p>",
                "scorecard", _SCORECARD_SIX_DATA, attributes={"mode": "compact"}, height=200),
            events_example(
                "scorecard", _SCORECARD_DATA, ["mj-chart-tile-click"],
                "<p>Tiles emit <code>mj-chart-tile-click</code> <code>{ metric, index }</code> "
                "(metric is the data object).</p>"),
        ],
    ),
]


# ---------------------------------------------------------------------------
# Less common / advanced
# ---------------------------------------------------------------------------

_ADVANCED = [

    ChartTypeDoc(
        type_key="calendar-heatmap",
        title="Calendar Heatmap",
        category="advanced",
        summary="GitHub-style year grid: week columns, weekday rows, days coloured by value.",
        description=(
            "Dates are YYYY-MM-DD local calendar days (ISO timestamps, Date objects and epoch "
            "ms also work; values of one day add up). Weeks start on Monday (weekStart 0 for "
            "Sunday); each year block is labelled and years defaults to every year from the "
            "earliest to the latest date. Days without data have a muted fill so the grid stays "
            "readable, and a less-to-more colour key is drawn below. domain fixes the range; "
            "colorScale \"diverging\" (or variant=\"diverging\") centres on midpoint (0). "
            "orientation=\"vertical\" runs weeks top to bottom. Days with a value emit "
            "mj-chart-day-click."
        ),
        data_shape=(
            "<pre><code>{\n"
            "  data: [{ date: string | number, value: number }],\n"
            "  years?: (number | string)[],          // default: the years of the data\n"
            "  domain?: [min, max],\n"
            "  colorScale?: \"sequential\" | \"diverging\", midpoint?: number,\n"
            "  weekStart?: 1 | 0                     // Monday (default) or Sunday\n"
            "}</code></pre>"
        ),
        options=[_DIVERGING_VARIANT_OPTION, _ORIENTATION_OPTION],
        examples=[
            chart_example(
                "basic", "One year",
                "<p>2025 with 21 days of data; empty days are visible in both themes.</p>",
                "calendar-heatmap", _CALENDAR_HEATMAP_DATA),
            chart_example(
                "two-years-diverging", "Two years, Sunday weeks, diverging",
                "<p>Data spanning 2024 and 2025 (both years drawn and labelled), weeks from "
                "Sunday and signed values on a diverging ramp.</p>",
                "calendar-heatmap", _CALENDAR_MULTI_YEAR_DATA, height=320),
            chart_example(
                "vertical", "Vertical",
                "<p><code>orientation=\"vertical\"</code>: weeks run top to bottom.</p>",
                "calendar-heatmap", _CALENDAR_HEATMAP_DATA, attributes={"orientation": "vertical"},
                height=520),
            events_example(
                "calendar-heatmap", _CALENDAR_HEATMAP_DATA, ["mj-chart-day-click"],
                "<p>Days with a value emit <code>mj-chart-day-click</code> <code>{ date, value "
                "}</code> (date as YYYY-MM-DD).</p>"),
        ],
    ),

    ChartTypeDoc(
        type_key="voronoi",
        title="Voronoi Diagram",
        category="advanced",
        summary="Nearest-neighbour partition of the plane around seed points.",
        description=(
            "Each point of every series is a cell seed. Cells are computed in data units by "
            "half-plane clipping (no external library), so they do not change on resize; "
            "aspect=\"equal\" draws both axes on one scale so cells also look Euclidean. "
            "Duplicate seeds are merged and the domain is padded. Cells take their series' "
            "colour; mode=\"overlay\" draws outlines only. Cells emit mj-chart-cell-click."
        ),
        data_shape=(
            "<pre><code>{\n"
            "  series: [{ name: string, color?, points: [{ x: number, y: number, label? }] }],\n"
            "  aspect?: \"equal\"                     // the aspect attribute wins\n"
            "}</code></pre>"
        ),
        options=[
            AttributeDoc(name="mode", description="Filled cells, or outlines only.", kind="enum",
                         values=["filled", "overlay"], default="filled"),
            AttributeDoc(name="aspect", description="`equal` uses one scale for both axes.", kind="enum",
                         values=["equal"]),
        ],
        examples=[
            chart_example(
                "basic", "Three clusters",
                "<p>Eight seeds in three series, with a legend.</p>",
                "voronoi", _VORONOI_DATA, legend=True),
            chart_example(
                "overlay-equal", "Outlines on an equal-aspect plot",
                "<p><code>mode=\"overlay\"</code> and <code>aspect=\"equal\"</code>; the "
                "duplicate D3 seed is merged.</p>",
                "voronoi", _VORONOI_OVERLAY_DATA, attributes={"mode": "overlay", "aspect": "equal"},
                height=300),
            events_example(
                "voronoi", _VORONOI_DATA, ["mj-chart-cell-click"],
                "<p>Cells emit <code>mj-chart-cell-click</code> <code>{ series, label, x, y "
                "}</code>.</p>",
                legend=True),
        ],
    ),

    ChartTypeDoc(
        type_key="spiral",
        title="Spiral Chart",
        category="advanced",
        summary="Time series on an Archimedean spiral: one turn per cycle, phases on spokes.",
        description=(
            "cycle sets the period of one turn: \"week\" (default, Monday at the top), \"year\" "
            "(month spokes at each month's first day) or \"day\" (hour spokes). The angle is "
            "each timestamp's phase within its cycle in the viewer's local time and the turn "
            "counts cycles since the first point, so the same weekday always lies on the same "
            "spoke. The value pushes the line outward from a thin base spiral (0 lies on it); "
            "a null value is a gap. mode=\"bar\" draws radial bars instead of the line. Points "
            "emit mj-chart-point-click, bars mj-chart-bar-click."
        ),
        data_shape=(
            "<pre><code>{\n"
            "  cycle?: \"week\" | \"year\" | \"day\",   // default \"week\"\n"
            "  series: [{ name: string, color?,\n"
            "             points: [{ t: string | number, value: number | null }] }]\n"
            "}</code></pre>"
            "<p><code>t</code>: a Date, epoch ms, ISO string or YYYY-MM-DD (a local day); points "
            "whose t is not a date are skipped.</p>"
        ),
        options=[
            AttributeDoc(name="mode", description="A line with a point per value, or radial bars.",
                         kind="enum", values=["line", "bar"], default="line"),
        ],
        examples=[
            chart_example(
                "basic", "Two weeks of page views",
                "<p>Weekdays line up on their spokes; the weekend dip repeats.</p>",
                "spiral", _SPIRAL_DATA, height=320),
            chart_example(
                "bars", "Radial bars",
                "<p><code>mode=\"bar\"</code>.</p>",
                "spiral", _SPIRAL_DATA, attributes={"mode": "bar"}, height=320),
            chart_example(
                "day-cycle", "Daily cycle with a gap",
                "<p><code>cycle: \"day\"</code>: two days of 4-hourly requests; the null at "
                "04:00 on day two is a gap.</p>",
                "spiral", _SPIRAL_DAY_DATA, height=320),
            chart_example(
                "year-cycle", "Yearly cycle",
                "<p><code>cycle: \"year\"</code>: two years of rainfall on month spokes.</p>",
                "spiral", _SPIRAL_YEAR_DATA, height=320, legend=True),
            events_example(
                "spiral", _SPIRAL_DATA, ["mj-chart-point-click", "mj-chart-bar-click"],
                "<p>Points emit <code>mj-chart-point-click</code> <code>{ series, t, value "
                "}</code>; in bar mode bars emit <code>mj-chart-bar-click</code> with the same "
                "detail.</p>",
                height=320),
        ],
    ),

    ChartTypeDoc(
        type_key="pixel",
        title="Pixel Chart",
        category="advanced",
        summary="Dense grid of cells, one per observation or bin, coloured by value.",
        description=(
            "x and y of each bin are 0-based indices or category labels (looked up in "
            "xCategories / yCategories; unlisted labels are added in first-seen order); a "
            "repeated x / y pair adds up. Only the supplied bins are drawn over one background, "
            "so sparse grids stay cheap. Colour follows the sequential or diverging ramp "
            "(colorScale, or variant=\"diverging\", around midpoint); domain fixes the range "
            "and a colour key names valueMeasure. Above 2,000 bins cells are not individually "
            "focusable. Cells emit mj-chart-pixel-click."
        ),
        data_shape=(
            "<pre><code>{\n"
            "  bins: [{ x: number | string, y: number | string, value: number }],\n"
            "  xCategories?: string[], yCategories?: string[],\n"
            "  xDimension?: string, yDimension?: string, valueMeasure?: string,\n"
            "  colorScale?: \"sequential\" | \"diverging\", midpoint?: number,\n"
            "  domain?: [min, max]\n"
            "}</code></pre>"
        ),
        options=[_DIVERGING_VARIANT_OPTION],
        examples=[
            chart_example(
                "basic", "Incidents by hour",
                "<p>Twelve hours by three days, with category labels and a colour key.</p>",
                "pixel", _PIXEL_DATA),
            chart_example(
                "labels-diverging", "Labels as positions, diverging",
                "<p>Bins addressed by label (the y labels are collected from the bins), signed "
                "values on a diverging ramp; the two #105 browser bins add up.</p>",
                "pixel", _PIXEL_LABELS_DATA),
            events_example(
                "pixel", _PIXEL_DATA, ["mj-chart-pixel-click"],
                "<p>Cells emit <code>mj-chart-pixel-click</code> <code>{ x, y, value }</code> "
                "with the category labels (or indices).</p>"),
        ],
    ),

    ChartTypeDoc(
        type_key="glyph",
        title="Glyph Chart",
        category="advanced",
        summary="Small multiples of star, radar or bar glyphs: one glyph per observation.",
        description=(
            "Each series is one observation drawn as a glyph over the axes. By default each "
            "axis runs from 0 at the centre to 1 (values in [0, 1]) or to the axis maximum, so "
            "glyph size is proportional to the value; domains / domain set the ranges and scale "
            "\"relative\" rescales each axis to the observed min-max. Every glyph has half- and "
            "full-scale rings and the first cell is a key glyph with the axis names. glyphType "
            "(or the mode attribute when glyphType is absent) is \"radar\" (filled, default), "
            "\"star\" (outline) or \"bar-glyph\" (radial bars). A null value is drawn at the "
            "centre with a hollow marker. Glyphs emit mj-chart-glyph-click."
        ),
        data_shape=(
            "<pre><code>{\n"
            "  axes: string[],\n"
            "  series: [{ name: string, values: (number | null)[] }],  // one per observation\n"
            "  glyphType?: \"radar\" | \"star\" | \"bar-glyph\",\n"
            "  grid?: { cols: number },\n"
            "  domains?: [[min, max], ...], domain?: [min, max],\n"
            "  scale?: \"absolute\" | \"relative\"     // default \"absolute\"\n"
            "}</code></pre>"
        ),
        options=[
            AttributeDoc(name="mode", description="Glyph type, used when the data has no `glyphType`.",
                         kind="enum", values=["radar", "star", "bar-glyph"], default="radar"),
        ],
        examples=[
            chart_example(
                "basic", "Service profiles",
                "<p>Eight services as radar glyphs on 0-1 axes.</p>",
                "glyph", _GLYPH_DATA, height=300),
            chart_example(
                "star-relative", "Stars on relative axes",
                "<p><code>glyphType: \"star\"</code> with <code>scale: \"relative\"</code> "
                "(units differ per axis); the Van has no charge rating (hollow marker).</p>",
                "glyph", _GLYPH_STAR_DATA, height=300),
            chart_example(
                "bar-glyph", "Bar glyphs via the attribute",
                "<p>Without <code>glyphType</code> in the data, <code>mode=\"bar-glyph\"</code> "
                "draws radial bars.</p>",
                "glyph", with_changes(_GLYPH_DATA, glyphType=None), attributes={"mode": "bar-glyph"},
                height=300),
            events_example(
                "glyph", _GLYPH_DATA, ["mj-chart-glyph-click"],
                "<p>Glyphs emit <code>mj-chart-glyph-click</code> <code>{ series, values "
                "}</code>.</p>",
                height=300),
        ],
    ),

    ChartTypeDoc(
        type_key="faceted",
        title="Faceted (Small Multiples)",
        category="advanced",
        summary="One chart type repeated across panels in a grid, on one shared scale.",
        description=(
            "childType (or the child-type attribute) names the panel chart type, default bar. "
            "For bar, column, line and area with shared scales (the default) the panels are "
            "drawn on one value scale, with the value axis on the first column and category "
            "labels on the bottom row only, so panels compare directly. mode=\"free-scale\" (or "
            "sharedScales: false) and every other child type draw each panel with that type's "
            "own renderer and scale; every panel field is passed through, so gauge or kpi "
            "panels work too. Series keep one colour across panels and the legend lists every "
            "series. No child mj-chart elements are created. Built-in panels emit "
            "mj-chart-series-click; delegated panels emit their type's events with panelIndex "
            "and panel added."
        ),
        data_shape=(
            "<pre><code>{\n"
            "  childType?: string,                   // default \"bar\"\n"
            "  categories?: string[],                // shared; a panel may carry its own\n"
            "  panels: [{ label: string, series?: [{ name, values: (number | null)[] }],\n"
            "             ...fields of the child type }],\n"
            "  grid?: { cols?: number, colGap?: number, rowGap?: number },\n"
            "  sharedScales?: boolean                // default true\n"
            "}</code></pre>"
        ),
        options=[
            AttributeDoc(name="child-type", description="Panel chart type; overrides `childType` "
                         "(the older `facet-type` attribute is also read).", kind="string",
                         values=["bar", "column", "line", "area", "pie", "gauge", "kpi"]),
            AttributeDoc(name="mode", description="`free-scale` lets every panel scale itself.",
                         kind="enum", values=["free-scale"]),
        ],
        examples=[
            chart_example(
                "basic", "Revenue by region",
                "<p>Four bar panels on one shared value scale.</p>",
                "faceted", _FACETED_DATA, height=300, legend=True),
            chart_example(
                "free-scale", "Lines, free scales",
                "<p>Line panels with <code>mode=\"free-scale\"</code>: each panel gets its own "
                "axis, so the small Batch counts stay readable; the API null is a gap.</p>",
                "faceted", _FACETED_LINE_DATA, attributes={"mode": "free-scale"}, height=260),
            chart_example(
                "gauge-panels", "Gauge panels",
                "<p><code>childType: \"gauge\"</code>: each panel's <code>gauge</code> field is "
                "passed to the gauge renderer.</p>",
                "faceted", _FACETED_GAUGE_DATA, height=240),
            events_example(
                "faceted", _FACETED_DATA, ["mj-chart-series-click"],
                "<p>Bars of the built-in panels emit <code>mj-chart-series-click</code> "
                "<code>{ panelIndex, panel, series, category, value }</code>.</p>",
                height=300, legend=True),
        ],
    ),
]


CHART_TYPES = _UX + _TEXT + _TABLES + _ADVANCED
