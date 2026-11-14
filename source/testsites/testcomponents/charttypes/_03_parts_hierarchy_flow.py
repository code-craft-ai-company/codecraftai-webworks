"""
    03_parts_hierarchy_flow.py

    Chart-type catalog entries for:
      - Part-to-whole charts (pie, donut, waffle, marimekko, mosaic,
        waterfall, pareto)
      - Hierarchical charts (treemap, sunburst, icicle, circle-pack via
        hierlayout.js; tree, dendrogram, org-chart, mindmap, decision-tree
        via tree.js)
      - Flow & process charts (sankey, alluvial, chord, flowchart,
        decision-flow, funnel, network, arc-diagram, node-link,
        edge-bundling, dependency-graph via network.js)
"""

import html as _html

from testcomponents.catalog.componentdoc import AttributeDoc
from testcomponents.charttypes.charttypedoc import ChartTypeDoc
from testcomponents.charttypes.examplemarkup import basic_example
from testcomponents.charttypes.examplemarkup import gallery_example
from testcomponents.charttypes.examplemarkup import inline_json_script
from testcomponents.charttypes.examplemarkup import orientation_option


# ---------------------------------------------------------------------------
# Shared sample data helpers
# ---------------------------------------------------------------------------

# The shared writer: compact one-line JSON in an inline script element.
_inline = inline_json_script


# ---------------------------------------------------------------------------
# Shared tree (depth-3, ~12 leaves) used by all hierlayout.js types
# ---------------------------------------------------------------------------

_HIER_ROOT = {
    "name": "Product",
    "children": [
        {
            "name": "Hardware",
            "children": [
                {"name": "CPU", "value": 420},
                {"name": "Memory", "value": 280},
                {"name": "Storage", "value": 195},
                {"name": "GPU", "value": 350},
            ],
        },
        {
            "name": "Software",
            "children": [
                {"name": "OS", "value": 310},
                {"name": "Runtime", "value": 175},
                {"name": "Libraries", "value": 220},
                {"name": "Tooling", "value": 140},
            ],
        },
        {
            "name": "Services",
            "children": [
                {"name": "Auth", "value": 130},
                {"name": "Analytics", "value": 185},
                {"name": "Support", "value": 95},
            ],
        },
    ],
}

# ---------------------------------------------------------------------------
# Shared node-link tree (depth-3, ~10 leaves) used by tree.js types
# ---------------------------------------------------------------------------

_TREE_ROOT = {
    "name": "Engineering",
    "children": [
        {
            "name": "Frontend",
            "children": [
                {"name": "React"},
                {"name": "Accessibility"},
                {"name": "Design Sys"},
            ],
        },
        {
            "name": "Backend",
            "children": [
                {"name": "API"},
                {"name": "Auth"},
                {"name": "Data"},
                {"name": "Search"},
            ],
        },
        {
            "name": "Platform",
            "children": [
                {"name": "Infra"},
                {"name": "CI/CD"},
                {"name": "Observ."},
            ],
        },
    ],
}

# ---------------------------------------------------------------------------
# Shared flow data (8 nodes / 11 links) used by sankey / alluvial
# ---------------------------------------------------------------------------

_FLOW_NODES = [
    {"id": "visitors", "label": "Visitors"},
    {"id": "search",   "label": "Search"},
    {"id": "direct",   "label": "Direct"},
    {"id": "social",   "label": "Social"},
    {"id": "browse",   "label": "Browse"},
    {"id": "cart",     "label": "Cart"},
    {"id": "checkout", "label": "Checkout"},
    {"id": "purchase", "label": "Purchase"},
]

_FLOW_LINKS = [
    {"source": "visitors", "target": "search",   "value": 4200},
    {"source": "visitors", "target": "direct",   "value": 2800},
    {"source": "visitors", "target": "social",   "value": 1900},
    {"source": "search",   "target": "browse",   "value": 3100},
    {"source": "direct",   "target": "browse",   "value": 2100},
    {"source": "social",   "target": "browse",   "value": 1300},
    {"source": "browse",   "target": "cart",     "value": 2600},
    {"source": "cart",     "target": "checkout", "value": 1850},
    {"source": "checkout", "target": "purchase", "value": 1420},
    {"source": "search",   "target": "cart",     "value": 480},
    {"source": "direct",   "target": "cart",     "value": 320},
]

# ---------------------------------------------------------------------------
# Shared network data (9 nodes / 12 links) used by network.js types
# ---------------------------------------------------------------------------

_NET_NODES = [
    {"id": "auth",     "label": "Auth",     "group": "security", "value": 8},
    {"id": "api",      "label": "API GW",   "group": "gateway",  "value": 12},
    {"id": "users",    "label": "Users",    "group": "service",  "value": 6},
    {"id": "orders",   "label": "Orders",   "group": "service",  "value": 7},
    {"id": "products", "label": "Products", "group": "service",  "value": 6},
    {"id": "payments", "label": "Payments", "group": "service",  "value": 5},
    {"id": "notify",   "label": "Notify",   "group": "infra",    "value": 4},
    {"id": "db",       "label": "Database", "group": "infra",    "value": 9},
    {"id": "cache",    "label": "Cache",    "group": "infra",    "value": 5},
]

_NET_LINKS = [
    {"source": "api",      "target": "auth",     "value": 3},
    {"source": "api",      "target": "users",    "value": 4},
    {"source": "api",      "target": "orders",   "value": 4},
    {"source": "api",      "target": "products", "value": 3},
    {"source": "orders",   "target": "payments", "value": 3},
    {"source": "orders",   "target": "notify",   "value": 2},
    {"source": "users",    "target": "db",       "value": 2},
    {"source": "orders",   "target": "db",       "value": 3},
    {"source": "products", "target": "db",       "value": 2},
    {"source": "users",    "target": "cache",    "value": 2},
    {"source": "products", "target": "cache",    "value": 2},
    {"source": "payments", "target": "notify",   "value": 2},
]

# ---------------------------------------------------------------------------
# Shared chord data (6 nodes / 11 directed links; EU->NA and AP->NA are the
# reverse flows of NA->EU and NA->AP, so those ribbons differ in width at
# each end)
# ---------------------------------------------------------------------------

_CHORD_NODES = [
    {"id": "NA",  "label": "N. America"},
    {"id": "EU",  "label": "Europe"},
    {"id": "AP",  "label": "Asia-Pac"},
    {"id": "LA",  "label": "Lat. America"},
    {"id": "ME",  "label": "Middle East"},
    {"id": "AF",  "label": "Africa"},
]

_CHORD_LINKS = [
    {"source": "NA", "target": "EU", "value": 1200},
    {"source": "EU", "target": "NA", "value": 760},
    {"source": "NA", "target": "AP", "value": 980},
    {"source": "AP", "target": "NA", "value": 1310},
    {"source": "NA", "target": "LA", "value": 640},
    {"source": "EU", "target": "AP", "value": 870},
    {"source": "EU", "target": "ME", "value": 420},
    {"source": "EU", "target": "AF", "value": 310},
    {"source": "AP", "target": "ME", "value": 530},
    {"source": "AP", "target": "LA", "value": 280},
    {"source": "ME", "target": "AF", "value": 190},
]

# ---------------------------------------------------------------------------
# Flowchart data (8 nodes / 9 links)
# ---------------------------------------------------------------------------

_FC_NODES = [
    {"id": "start",   "label": "Start",         "shape": "oval"},
    {"id": "input",   "label": "Receive Order",  "shape": "rect"},
    {"id": "check",   "label": "In Stock?",      "shape": "diamond"},
    {"id": "reserve", "label": "Reserve Item",   "shape": "rect"},
    {"id": "backord", "label": "Back-order",     "shape": "rect"},
    {"id": "pay",     "label": "Process Payment","shape": "rect"},
    {"id": "payok",   "label": "Payment OK?",    "shape": "diamond"},
    {"id": "ship",    "label": "Ship Order",     "shape": "rect"},
    {"id": "end",     "label": "End",            "shape": "oval"},
]

_FC_LINKS = [
    {"source": "start",   "target": "input"},
    {"source": "input",   "target": "check"},
    {"source": "check",   "target": "reserve", "label": "Yes"},
    {"source": "check",   "target": "backord",  "label": "No"},
    {"source": "reserve", "target": "pay"},
    {"source": "backord",  "target": "pay"},
    {"source": "pay",     "target": "payok"},
    {"source": "payok",   "target": "ship",    "label": "Yes"},
    {"source": "payok",   "target": "pay",     "label": "No (retry)"},
    {"source": "ship",    "target": "end"},
]

# ---------------------------------------------------------------------------
# Decision-flow data (7 nodes / 7 links)
# ---------------------------------------------------------------------------

_DF_NODES = [
    {"id": "alert",    "label": "Alert fired",   "shape": "oval"},
    {"id": "severity", "label": "Severity high?", "shape": "diamond"},
    {"id": "page",     "label": "Page on-call",  "shape": "rect"},
    {"id": "known",    "label": "Known issue?",  "shape": "diamond"},
    {"id": "ticket",   "label": "Auto-ticket",   "shape": "rect"},
    {"id": "resolve",  "label": "Auto-resolve",  "shape": "rect"},
    {"id": "done",     "label": "Done",          "shape": "oval"},
]

_DF_LINKS = [
    {"source": "alert",    "target": "severity"},
    {"source": "severity", "target": "page",    "label": "Yes"},
    {"source": "severity", "target": "known",   "label": "No"},
    {"source": "known",    "target": "ticket",  "label": "No"},
    {"source": "known",    "target": "resolve", "label": "Yes"},
    {"source": "page",     "target": "done"},
    {"source": "ticket",   "target": "done"},
]

# ---------------------------------------------------------------------------
# Org-chart tree
# ---------------------------------------------------------------------------

_ORG_ROOT = {
    "name": "Alice Chen",
    "role": "Chief Executive",
    "children": [
        {
            "name": "Bob Park",
            "role": "CTO",
            "children": [
                {"name": "Carol Davis", "role": "VP Engineering"},
                {"name": "Dan Ellis",   "role": "VP Infrastructure"},
            ],
        },
        {
            "name": "Eve Martin",
            "role": "CFO",
            "children": [
                {"name": "Frank Wu",  "role": "Controller"},
                {"name": "Grace Lee", "role": "FP&A Lead"},
            ],
        },
        {
            "name": "Hiro Tanaka",
            "role": "CMO",
            "children": [
                {"name": "Iris Müller", "role": "Brand"},
                {"name": "James Osei",  "role": "Growth"},
            ],
        },
    ],
}

# ---------------------------------------------------------------------------
# Mindmap tree
# ---------------------------------------------------------------------------

_MINDMAP_ROOT = {
    "name": "Strategy 2026",
    "children": [
        {
            "name": "Growth",
            "children": [
                {"name": "New Markets"},
                {"name": "Upsell"},
                {"name": "Referrals"},
            ],
        },
        {
            "name": "Product",
            "children": [
                {"name": "Mobile"},
                {"name": "API Platform"},
                {"name": "AI Features"},
            ],
        },
        {
            "name": "Operations",
            "children": [
                {"name": "Cost Control"},
                {"name": "Automation"},
            ],
        },
        {
            "name": "People",
            "children": [
                {"name": "Hiring"},
                {"name": "Learning"},
                {"name": "Culture"},
            ],
        },
    ],
}

# ---------------------------------------------------------------------------
# Decision-tree tree
# ---------------------------------------------------------------------------

_DT_ROOT = {
    "name": "Credit score?",
    "children": [
        {
            "name": "Income?",
            "edgeLabel": "≥ 700",
            "children": [
                {"name": "Approve", "edgeLabel": "≥ 60k"},
                {"name": "Review",  "edgeLabel": "< 60k"},
            ],
        },
        {
            "name": "Collateral?",
            "edgeLabel": "600–699",
            "children": [
                {"name": "Review",  "edgeLabel": "Yes"},
                {"name": "Decline", "edgeLabel": "No"},
            ],
        },
        {"name": "Decline", "edgeLabel": "< 600"},
    ],
}

# ---------------------------------------------------------------------------
# Alluvial data (nodes carry group to drive column assignment)
# ---------------------------------------------------------------------------

_ALLUVIAL_NODES = [
    {"id": "search_s",  "label": "Search",    "group": "Source"},
    {"id": "social_s",  "label": "Social",    "group": "Source"},
    {"id": "direct_s",  "label": "Direct",    "group": "Source"},
    {"id": "mobile_d",  "label": "Mobile",    "group": "Device"},
    {"id": "desktop_d", "label": "Desktop",   "group": "Device"},
    {"id": "new_u",     "label": "New",       "group": "User"},
    {"id": "return_u",  "label": "Returning", "group": "User"},
]

_ALLUVIAL_LINKS = [
    {"source": "search_s",  "target": "mobile_d",  "value": 2100},
    {"source": "search_s",  "target": "desktop_d", "value": 1400},
    {"source": "social_s",  "target": "mobile_d",  "value": 1800},
    {"source": "social_s",  "target": "desktop_d", "value": 600},
    {"source": "direct_s",  "target": "desktop_d", "value": 1300},
    {"source": "direct_s",  "target": "mobile_d",  "value": 700},
    {"source": "mobile_d",  "target": "new_u",     "value": 2900},
    {"source": "mobile_d",  "target": "return_u",  "value": 1700},
    {"source": "desktop_d", "target": "new_u",     "value": 1100},
    {"source": "desktop_d", "target": "return_u",  "value": 2200},
]


# ===========================================================================
# PART-TO-WHOLE
# ===========================================================================

_pie_data = {
    "categories": ["Direct", "Organic Search", "Referral", "Social", "Email", "Paid"],
    "series": [{"name": "Sessions", "values": [3200, 4850, 1640, 2100, 980, 1230]}],
}

_pie_example = (
    '<mj-chart type="pie" style="height:260px">'
    + _inline(_pie_data)
    + "</mj-chart>"
)

_donut_data = {
    "categories": ["Direct", "Organic Search", "Referral", "Social", "Email", "Paid"],
    "series": [{"name": "Sessions", "values": [3200, 4850, 1640, 2100, 980, 1230]}],
    "meta": {"center-label": "14,000"},
}

_donut_example = (
    '<mj-chart type="donut" style="height:260px">'
    + _inline(_donut_data)
    + "</mj-chart>"
)

_waffle_data = {
    "categories": ["Q1", "Q2", "Q3", "Q4"],
    "series": [{"name": "Sales", "values": [22, 31, 27, 20]}],
    "meta": {"grid": {"cols": 10, "rows": 10}},
}

_waffle_example = (
    '<mj-chart type="waffle" style="height:260px">'
    + _inline(_waffle_data)
    + "</mj-chart>"
)

_marimekko_data = {
    "categories": ["APAC", "EMEA", "Americas"],
    "series": [
        {"name": "Enterprise", "values": [820, 1140, 1600]},
        {"name": "Mid-Market", "values": [640, 780, 1100]},
        {"name": "SMB",        "values": [390, 420,  680]},
    ],
}

_marimekko_example = (
    '<mj-chart type="marimekko" style="height:260px">'
    + _inline(_marimekko_data)
    + "<mj-chart-legend></mj-chart-legend>"
    + "</mj-chart>"
)

_mosaic_data = {
    "meta": {"title": "Titanic survival by class", "residuals": True},
    "categories": ["First", "Second", "Third", "Crew"],
    "series": [
        {"name": "Survived", "values": [203, 118, 178, 212]},
        {"name": "Perished", "values": [122, 167, 528, 673]},
    ],
}

_mosaic_example = (
    '<mj-chart type="mosaic" style="height:260px">'
    + _inline(_mosaic_data)
    + "<mj-chart-legend></mj-chart-legend>"
    + "</mj-chart>"
)

_waterfall_data = {
    "categories": ["Jan", "Feb", "Mar", "Q1", "Apr", "May", "Jun", "H1"],
    "series": [
        {
            "name": "Revenue delta",
            "values": [420, -80, 310, None, 190, -140, 260, None],
            "kinds": ["start", "delta", "delta", "subtotal",
                      "delta", "delta", "delta", "total"],
        }
    ],
}

_waterfall_example = (
    '<mj-chart type="waterfall" style="height:260px">'
    + _inline(_waterfall_data)
    + "<mj-chart-legend></mj-chart-legend>"
    + "</mj-chart>"
)

_pareto_data = {
    "categories": [
        "Late delivery", "Wrong item", "Damaged", "Missing part",
        "Invoice error", "Poor packing", "Other",
    ],
    "series": [
        {
            "name": "Complaints",
            "values": [312, 241, 185, 143, 97, 64, 38],
        }
    ],
}

_pareto_example = (
    '<mj-chart type="pareto" style="height:260px">'
    + _inline(_pareto_data)
    + "<mj-chart-legend></mj-chart-legend>"
    + "</mj-chart>"
)


# ===========================================================================
# HIERARCHICAL — hierlayout.js (data shape: raw.root nested tree)
# ===========================================================================

_hier_inline = _inline({"root": _HIER_ROOT})

_treemap_example = (
    '<mj-chart type="treemap" label="Product cost by component" style="height:260px">'
    + _hier_inline
    + "</mj-chart>"
)

_sunburst_example = (
    '<mj-chart type="sunburst" label="Product cost by component" style="height:300px">'
    + "<mj-chart-legend></mj-chart-legend>"
    + _hier_inline
    + "</mj-chart>"
)

_icicle_example = (
    '<mj-chart type="icicle" label="Product cost by component" style="height:260px">'
    + _hier_inline
    + "</mj-chart>"
)

_circle_pack_example = (
    '<mj-chart type="circle-pack" label="Product cost by component" style="height:300px">'
    + "<mj-chart-legend></mj-chart-legend>"
    + _hier_inline
    + "</mj-chart>"
)


# ===========================================================================
# HIERARCHICAL — tree.js (data shape: raw.root nested tree)
# ===========================================================================

_tree_inline = _inline({"root": _TREE_ROOT})

_tree_example = (
    '<mj-chart type="tree" label="Engineering teams" style="height:260px">'
    + _tree_inline
    + "</mj-chart>"
)

# Merge distances (1 - correlation) of an average-linkage clustering of
# gene-expression profiles: leaves sit at distance 0, each internal node at
# the distance where its children merge.
_dendrogram_data = {
    "root": {
        "name": "All samples",
        "distance": 0.94,
        "children": [
            {
                "name": "Cluster A",
                "distance": 0.62,
                "children": [
                    {
                        "name": "A1",
                        "distance": 0.21,
                        "children": [
                            {"name": "Liver 1"},
                            {"name": "Liver 2"},
                        ],
                    },
                    {
                        "name": "A2",
                        "distance": 0.38,
                        "children": [
                            {"name": "Kidney 1"},
                            {"name": "Kidney 2"},
                            {"name": "Kidney 3"},
                        ],
                    },
                ],
            },
            {
                "name": "Cluster B",
                "distance": 0.47,
                "children": [
                    {"name": "Brain 1"},
                    {
                        "name": "B1",
                        "distance": 0.29,
                        "children": [
                            {"name": "Brain 2"},
                            {"name": "Spinal cord"},
                        ],
                    },
                ],
            },
        ],
    }
}

_dendrogram_example = (
    '<mj-chart type="dendrogram" label="Tissue sample clustering" style="height:260px">'
    + _inline(_dendrogram_data)
    + "</mj-chart>"
)

_org_example = (
    '<mj-chart type="org-chart" label="Leadership team" style="height:260px">'
    + _inline({"root": _ORG_ROOT})
    + "</mj-chart>"
)

_mindmap_example = (
    '<mj-chart type="mindmap" label="Strategy 2026 themes" style="height:260px">'
    + _inline({"root": _MINDMAP_ROOT})
    + "</mj-chart>"
)

_decision_tree_example = (
    '<mj-chart type="decision-tree" label="Loan application decision" style="height:300px">'
    + _inline({"root": _DT_ROOT})
    + "</mj-chart>"
)


# ===========================================================================
# FLOW & PROCESS
# ===========================================================================

_sankey_example = (
    '<mj-chart type="sankey" label="Website visitor flow" style="height:260px">'
    + _inline({"nodes": _FLOW_NODES, "links": _FLOW_LINKS})
    + "</mj-chart>"
)

_alluvial_example = (
    '<mj-chart type="alluvial" label="Visits by source, device and user type"'
    ' style="height:260px">'
    + _inline({"nodes": _ALLUVIAL_NODES, "links": _ALLUVIAL_LINKS})
    + "</mj-chart>"
)

_chord_example = (
    '<mj-chart type="chord" label="Trade flows between regions" style="height:260px">'
    + _inline({"nodes": _CHORD_NODES, "links": _CHORD_LINKS})
    + "</mj-chart>"
)

_flowchart_example = (
    '<mj-chart type="flowchart" style="height:260px">'
    + _inline({"nodes": _FC_NODES, "links": _FC_LINKS})
    + "<mj-chart-legend></mj-chart-legend>"
    + "</mj-chart>"
)

_decision_flow_example = (
    '<mj-chart type="decision-flow" style="height:260px">'
    + _inline({"nodes": _DF_NODES, "links": _DF_LINKS})
    + "<mj-chart-legend></mj-chart-legend>"
    + "</mj-chart>"
)

_funnel_data = {
    "categories": ["Awareness", "Interest", "Consideration", "Intent", "Purchase"],
    "series": [
        {"name": "Leads", "values": [12400, 7800, 4200, 1950, 870]}
    ],
}

_funnel_example = (
    '<mj-chart type="funnel" style="height:260px">'
    + _inline(_funnel_data)
    + "</mj-chart>"
)

_network_example = (
    '<mj-chart type="network" style="height:260px">'
    + _inline({"nodes": _NET_NODES, "links": _NET_LINKS})
    + "<mj-chart-legend></mj-chart-legend>"
    + "</mj-chart>"
)

_arc_diagram_example = (
    '<mj-chart type="arc-diagram" style="height:260px">'
    + _inline({"nodes": _NET_NODES, "links": _NET_LINKS})
    + "<mj-chart-legend></mj-chart-legend>"
    + "</mj-chart>"
)

_node_link_example = (
    '<mj-chart type="node-link" style="height:260px">'
    + _inline({"nodes": _NET_NODES, "links": _NET_LINKS})
    + "<mj-chart-legend></mj-chart-legend>"
    + "</mj-chart>"
)

_edge_bundling_example = (
    '<mj-chart type="edge-bundling" tension="0.85" style="height:260px">'
    + _inline({"nodes": _NET_NODES, "links": _NET_LINKS})
    + "<mj-chart-legend></mj-chart-legend>"
    + "</mj-chart>"
)

_dep_graph_nodes = [
    {"id": "app",      "label": "app",      "group": "ui",      "value": 5},
    {"id": "router",   "label": "router",   "group": "ui",      "value": 4},
    {"id": "store",    "label": "store",    "group": "state",   "value": 4},
    {"id": "auth",     "label": "auth",     "group": "service", "value": 3},
    {"id": "api",      "label": "api",      "group": "service", "value": 4},
    {"id": "utils",    "label": "utils",    "group": "library", "value": 2},
    {"id": "logger",   "label": "logger",   "group": "library", "value": 2},
    {"id": "types",    "label": "types",    "group": "library", "value": 1},
]

_dep_graph_links = [
    {"source": "app",    "target": "router"},
    {"source": "app",    "target": "store"},
    {"source": "app",    "target": "auth"},
    {"source": "router", "target": "api"},
    {"source": "store",  "target": "api"},
    {"source": "auth",   "target": "api"},
    {"source": "api",    "target": "utils"},
    {"source": "api",    "target": "logger"},
    {"source": "utils",  "target": "types"},
    {"source": "logger", "target": "types"},
    {"source": "auth",   "target": "utils"},
    {"source": "store",  "target": "utils"},
]

_dep_graph_example = (
    '<mj-chart type="dependency-graph" style="height:260px">'
    + _inline({"nodes": _dep_graph_nodes, "links": _dep_graph_links})
    + "<mj-chart-legend></mj-chart-legend>"
    + "</mj-chart>"
)


# ===========================================================================
# Sandbox gallery helpers
# ===========================================================================

def chart_markup(chart_type, data, chart_id=None, label=None, style="height:260px",
            attrs=None, legend=False, after=""):
    """
        Build the markup of one <mj-chart> with inline JSON data.

        :param chart_type: The chart ``type`` attribute.
        :param data: The chart data (serialised into the inline script).
        :param chart_id: Optional id of the chart (scripts use it).
        :param label: Optional accessible name (``label`` attribute).
        :param style: The inline style of the chart host.
        :param attrs: Optional renderer option attributes (name -> value).
        :param legend: True nests an <mj-chart-legend>.
        :param after: Optional markup placed after the chart.
        :returns: The HTML string.
    """
    opening = "<mj-chart"
    if chart_id is not None:
        opening = opening + f' id="{chart_id}"'
    opening = opening + f' type="{chart_type}"'
    if attrs is not None:
        for name, value in attrs.items():
            opening = opening + f' {name}="{_html.escape(str(value), quote=True)}"'
    if label is not None:
        opening = opening + f' label="{_html.escape(label, quote=True)}"'
    opening = opening + f' style="{style}">'
    lines = [opening, "  " + _inline(data)]
    if legend is True:
        lines.append("  <mj-chart-legend></mj-chart-legend>")
    lines.append("</mj-chart>")
    result = "\n".join(lines)
    if after != "":
        result = result + "\n" + after
    return result


#: CSS of the line under an events example that shows the last event.
OUTPUT_CSS = (
    ".chart-output { display: block; margin-block-start: var(--mj-space-2); "
    "color: var(--mj-text-muted); font-size: var(--mj-font-size-sm); "
    "overflow-wrap: anywhere; }"
)


def events_example(chart_type, data, events, click, enter=None, description="",
                    attrs=None, legend=False, label=None, style="height:260px"):
    """
        Build the ``events`` gallery entry of a chart type: the script listens
        for the renderer's events, shows the last detail under the chart, and
        activates two marks (a click on one, Enter on another) so the event
        log shows them on load.

        :param chart_type: The chart type key.
        :param data: The chart data.
        :param events: The event names to listen for.
        :param click: CSS selector (in the shadow root) of the mark to click.
        :param enter: CSS selector of the marks of which the LAST one gets
            Enter; None uses ``click``. A selector starting with ``click:``
            clicks that mark instead of pressing Enter.
        :param description: The example description (HTML).
        :returns: A ComponentExample keyed ``events``.
    """
    chart_id = "events-chart"
    html = chart_markup(
        chart_type, data, chart_id=chart_id, label=label, style=style, attrs=attrs,
        legend=legend,
        after='<output id="events-output" class="chart-output">Click or press Enter on a mark.</output>',
    )
    second = enter if enter is not None else click
    second_action = "enter"
    if second.startswith("click:") is True:
        second = second[len("click:"):]
        second_action = "click"
    names = ", ".join(f'"{name}"' for name in events)
    script = (
        'const chart = document.getElementById("events-chart")\n'
        'const output = document.getElementById("events-output")\n'
        f'for (const name of [{names}]) {{\n'
        '  chart.addEventListener(name, (event) => {\n'
        '    output.textContent = name + " " + JSON.stringify(event.detail)\n'
        '  })\n'
        '}\n'
        '// Rendering happens on the next frame: wait for the first render.\n'
        'if (chart.chartState !== "ready") {\n'
        '  await Promise.race([\n'
        '    new Promise((resolve) => chart.addEventListener("mj-chart-render", resolve, { once: true })),\n'
        '    new Promise((resolve) => setTimeout(resolve, 3000)),\n'
        '  ])\n'
        '}\n'
        f'const first = chart.shadowRoot.querySelector("{click}")\n'
        'if (first !== null) {\n'
        '  first.dispatchEvent(new MouseEvent("click", { bubbles: true }))\n'
        '}\n'
        f'const marks = chart.shadowRoot.querySelectorAll("{second}")\n'
        'const last = marks[marks.length - 1]\n'
        'if (last !== undefined) {\n'
    )
    if second_action == "enter":
        script = script + (
            '  last.focus()\n'
            '  last.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true }))\n'
            '}\n'
        )
    else:
        script = script + (
            '  last.dispatchEvent(new MouseEvent("click", { bubbles: true }))\n'
            '}\n'
        )
    result = gallery_example("events", "Events", description, html, script=script, css=OUTPUT_CSS)
    return result


_CATEGORY_SHAPE = (
    "<pre><code>{\n"
    "  categories: string[],\n"
    "  series: [{ name: string, values: (number | null)[] }]\n"
    "}</code></pre>"
)

_TREE_SHAPE = (
    "<pre><code>{\n"
    "  root: { name: string, value?: number, children?: [ ...same shape ] }\n"
    "}</code></pre>"
)

_GRAPH_SHAPE = (
    "<pre><code>{\n"
    "  nodes?: [{ id: string, label?: string, group?: string }],\n"
    "  links: [{ source: string, target: string, value: number }]\n"
    "}</code></pre>"
)


# ===========================================================================
# Extra sample data for the galleries
# ===========================================================================

_LANGUAGES = {
    "categories": [
        "Python", "JavaScript", "TypeScript", "Java", "C#", "C++", "Go", "Rust",
        "PHP", "Kotlin", "Swift", "Ruby", "Scala", "Dart", "Elixir",
    ],
    "series": [{"name": "Repositories", "values": [
        2310, 2050, 1620, 1180, 840, 760, 520, 410, 380, 260, 210, 170, 90, 70, 40,
    ]}],
}

_PIE_EDGE = {
    "categories": ["Direct", "Organic Search", "Referral", "Social", "Email"],
    "series": [{"name": "Sessions", "values": [3200, None, 1640, -120, 980]}],
}

_DONUT_THIN = {
    "categories": ["Compute", "Storage", "Network", "Support"],
    "series": [{"name": "Spend", "values": [5200, 2100, 900, 400]}],
    "meta": {"center-label": "$8.6k"},
}

_DONUT_SINGLE = {
    "categories": ["Uptime"],
    "series": [{"name": "Availability", "values": [100]}],
    "meta": {"center-label": "100%"},
}

_WAFFLE_COUNTS = {
    "categories": ["Renewables", "Gas", "Nuclear", "Coal"],
    "series": [{"name": "Generation share", "values": [46, 31, 15, 8]}],
    "meta": {"grid": {"cols": 20, "rows": 5}},
}

_WAFFLE_SURVEY = {
    "categories": ["Very satisfied", "Satisfied", "Neutral", "Dissatisfied", "No answer"],
    "series": [{"name": "Responses", "values": [412, 268, 133, 51, None]}],
}

_MEKKO_WIDE = {
    "categories": ["United States", "Germany", "Japan", "United Kingdom", "Brazil", "India"],
    "series": [
        {"name": "Cloud", "values": [920, 310, 280, 240, 90, 140]},
        {"name": "On-premise", "values": [410, 260, 300, 150, 120, 110]},
        {"name": "Hybrid", "values": [380, 170, 120, 130, 40, 70]},
        {"name": "Edge", "values": [120, 60, 90, 40, 20, 30]},
    ],
}

_MEKKO_EDGE = {
    "categories": ["North", "South", "East"],
    "series": [
        {"name": "Online", "values": [540, None, 380]},
        {"name": "Retail", "values": [310, 420, -60]},
    ],
}

_MOSAIC_HAIR = {
    "meta": {"title": "Eye colour by hair colour"},
    "categories": ["Black", "Brown", "Red", "Blond"],
    "series": [
        {"name": "Brown eyes", "values": [68, 119, 26, 7]},
        {"name": "Blue eyes", "values": [20, 84, 17, 94]},
        {"name": "Hazel eyes", "values": [15, 54, 14, 10]},
        {"name": "Green eyes", "values": [5, 29, 14, 16]},
    ],
}

_MOSAIC_SPINE = {
    "meta": {"equal-widths": True},
    "categories": ["18-29", "30-44", "45-64", "65+"],
    "series": [
        {"name": "Mobile first", "values": [410, 350, 210, 60]},
        {"name": "Desktop first", "values": [90, 150, 240, 190]},
    ],
}

_WATERFALL_PNL = {
    "categories": ["Revenue", "Cost of sales", "Gross profit", "Operating costs",
                   "Other income", "Tax", "Net profit"],
    "series": [{"name": "P&L (k€)", "values": [
        {"v": 1250, "kind": "start"},
        {"v": 480, "kind": "subtract"},
        {"v": None, "kind": "subtotal"},
        {"v": 390, "kind": "decrease"},
        {"v": 45, "kind": "increase"},
        {"v": 95, "kind": "subtract"},
        {"v": None, "kind": "total"},
    ]}],
}

_PARETO_INCIDENTS = {
    "meta": {"pareto-line": False},
    "categories": [
        "Disk full", "Expired certificate", "Bad deploy", "DNS", "Memory leak",
        "Network partition", "Config drift", "Dependency outage", "Rate limiting",
        "Clock skew", "Permissions", "Unknown",
    ],
    "series": [{"name": "Incidents", "values": [14, 9, 41, 7, 22, 5, 17, 12, 4, 2, 6, 3]}],
}

_PARETO_EDGE = {
    "categories": ["Scratch", "Dent", "Wrong colour", "Loose part", "Missing label"],
    "series": [{"name": "Defects", "values": [48, None, 31, -4, 12]}],
}

_DISK_ROOT = {
    "name": "/",
    "children": [
        {"name": "home", "children": [
            {"name": "alice", "children": [
                {"name": "documents", "value": 1200},
                {"name": "photos", "value": 5400},
                {"name": "music", "value": 2300},
            ]},
            {"name": "bob", "children": [
                {"name": "code", "value": 3100},
                {"name": "videos", "value": 7200},
            ]},
        ]},
        {"name": "usr", "children": [
            {"name": "lib", "value": 4100},
            {"name": "share", "value": 2600},
            {"name": "bin", "value": 900},
        ]},
        {"name": "var", "children": [
            {"name": "log", "value": 1800},
            {"name": "cache", "value": 2200},
        ]},
        {"name": "opt", "value": 1500},
    ],
}

# A root given as an array: the children of an unnamed root. Missing and
# negative values count as 0, so "Transport" and "Gifts" draw nothing.
_BUDGET_FLAT = {"root": [
    {"name": "Rent", "value": 1450},
    {"name": "Groceries", "value": 620},
    {"name": "Utilities", "value": 210},
    {"name": "Leisure", "value": 180},
    {"name": "Transport"},
    {"name": "Gifts", "value": -40},
]}

_PROFILE_ROOT = {
    "name": "main",
    "children": [
        {"name": "parse", "children": [
            {"name": "tokenize", "value": 120},
            {"name": "build AST", "value": 80},
        ]},
        {"name": "render", "children": [
            {"name": "layout", "value": 210},
            {"name": "paint", "value": 160},
            {"name": "composite", "value": 40},
        ]},
        {"name": "gc", "value": 60},
    ],
}


def _large_tree():
    """
        A 40-node service tree (3 regions x 4 clusters x 2 services).

        :returns: The ``root`` dictionary.
    """
    regions = []
    for region in ["eu-west", "us-east", "ap-south"]:
        clusters = []
        for number in range(1, 5):
            services = [{"name": f"api-{number}"}, {"name": f"worker-{number}"}]
            clusters.append({"name": f"{region}-{number}", "children": services})
        regions.append({"name": region, "children": clusters})
    result = {"name": "Fleet", "children": regions}
    return result


_ORG_LONG = {
    "name": "Mara Okonkwo-Lindqvist",
    "role": "Chief Executive Officer",
    "children": [
        {"name": "Theo Albrecht", "role": "Senior Vice President, Product Engineering"},
        {"name": "Priya Raman", "role": "Vice President, Customer Success and Support"},
        {"name": "Luis Fernández", "role": "Director of Finance"},
    ],
}

_MINDMAP_SMALL = {
    "name": "Launch plan",
    "children": [
        {"name": "Marketing", "children": [{"name": "Blog post"}, {"name": "Webinar"}]},
        {"name": "Engineering", "children": [{"name": "Feature flags"}, {"name": "Load test"}]},
    ],
}

_DENDRO_PLAIN = {"root": {
    "name": "Fruit",
    "children": [
        {"name": "Citrus", "children": [{"name": "Lemon"}, {"name": "Lime"}, {"name": "Orange"}]},
        {"name": "Berries", "children": [
            {"name": "Soft", "children": [{"name": "Raspberry"}, {"name": "Blackberry"}]},
            {"name": "Blueberry"},
        ]},
        {"name": "Apple"},
    ],
}}

_BUDGET_FLOW = {
    "nodes": [
        {"id": "salary", "label": "Salary"},
        {"id": "budget", "label": "Budget"},
        {"id": "housing", "label": "Housing"},
        {"id": "savings", "label": "Savings"},
        {"id": "living", "label": "Living costs"},
    ],
    "links": [
        {"source": "salary", "target": "budget", "value": 4200},
        {"source": "budget", "target": "housing", "value": 1500},
        {"source": "budget", "target": "living", "value": 1700},
        {"source": "budget", "target": "savings", "value": 1000},
        {"source": "savings", "target": "budget", "value": 200},
        {"source": "living", "target": "living", "value": 50},
        {"source": "housing", "target": "savings", "value": 0},
    ],
}

_WAVES_NODES = [
    {"id": "w1-a", "label": "Promoter", "time": 2023},
    {"id": "w1-b", "label": "Passive", "time": 2023},
    {"id": "w1-c", "label": "Detractor", "time": 2023},
    {"id": "w2-a", "label": "Promoter", "time": 2024},
    {"id": "w2-b", "label": "Passive", "time": 2024},
    {"id": "w2-c", "label": "Detractor", "time": 2024},
    {"id": "w3-a", "label": "Promoter", "time": 2025},
    {"id": "w3-b", "label": "Passive", "time": 2025},
    {"id": "w3-c", "label": "Detractor", "time": 2025},
]

_WAVES_LINKS = [
    {"source": "w1-a", "target": "w2-a", "value": 310},
    {"source": "w1-a", "target": "w2-b", "value": 60},
    {"source": "w1-b", "target": "w2-a", "value": 90},
    {"source": "w1-b", "target": "w2-b", "value": 180},
    {"source": "w1-b", "target": "w2-c", "value": 40},
    {"source": "w1-c", "target": "w2-b", "value": 70},
    {"source": "w1-c", "target": "w2-c", "value": 120},
    {"source": "w2-a", "target": "w3-a", "value": 340},
    {"source": "w2-a", "target": "w3-b", "value": 60},
    {"source": "w2-b", "target": "w3-a", "value": 110},
    {"source": "w2-b", "target": "w3-b", "value": 170},
    {"source": "w2-b", "target": "w3-c", "value": 30},
    {"source": "w2-c", "target": "w3-b", "value": 50},
    {"source": "w2-c", "target": "w3-c", "value": 110},
]

# Listed once per pair (one-way flows) plus a self-link drawn as a loop.
_CHORD_ONEWAY = {
    "nodes": [
        {"id": "eng", "label": "Engineering"},
        {"id": "design", "label": "Design"},
        {"id": "product", "label": "Product"},
        {"id": "sales", "label": "Sales"},
    ],
    "links": [
        {"source": "eng", "target": "design", "value": 34},
        {"source": "eng", "target": "product", "value": 52},
        {"source": "design", "target": "product", "value": 27},
        {"source": "product", "target": "sales", "value": 41},
        {"source": "eng", "target": "sales", "value": 12},
        {"source": "eng", "target": "eng", "value": 30},
    ],
}

# Zero, negative and missing values are ignored; "Legal" has no flow left
# and its arc is omitted.
_CHORD_EDGE = {
    "nodes": [
        {"id": "a", "label": "Support"},
        {"id": "b", "label": "Billing"},
        {"id": "c", "label": "Onboarding"},
        {"id": "d", "label": "Legal"},
    ],
    "links": [
        {"source": "a", "target": "b", "value": 18},
        {"source": "b", "target": "a", "value": 7},
        {"source": "a", "target": "c", "value": 11},
        {"source": "c", "target": "b", "value": 4},
        {"source": "a", "target": "d", "value": 0},
        {"source": "d", "target": "b", "value": -3},
        {"source": "d", "target": "c"},
    ],
}

_FC_LINEAR_NODES = [
    {"id": "commit", "label": "Commit", "shape": "oval"},
    {"id": "build", "label": "Build"},
    {"id": "test", "label": "Tests pass?", "shape": "diamond"},
    {"id": "deploy", "label": "Deploy to staging"},
    {"id": "fix", "label": "Fix and push"},
    {"id": "done", "label": "Ready for review", "shape": "oval"},
]

_FC_LINEAR_LINKS = [
    {"source": "commit", "target": "build"},
    {"source": "build", "target": "test"},
    {"source": "test", "target": "deploy", "label": "Yes"},
    {"source": "test", "target": "fix", "label": "No"},
    {"source": "fix", "target": "build"},
    {"source": "deploy", "target": "done"},
]

# The "False" branch is listed first: decision-flow still places "True"
# before it.
_DF_BOOL_NODES = [
    {"id": "req", "label": "Request", "shape": "oval"},
    {"id": "cached", "label": "In cache?", "shape": "diamond"},
    {"id": "fetch", "label": "Fetch origin"},
    {"id": "fresh", "label": "Still fresh?", "shape": "diamond"},
    {"id": "serve", "label": "Serve cached"},
    {"id": "store", "label": "Store and serve"},
]

_DF_BOOL_LINKS = [
    {"source": "req", "target": "cached"},
    {"source": "cached", "target": "fetch", "label": "False"},
    {"source": "cached", "target": "fresh", "label": "True"},
    {"source": "fresh", "target": "fetch", "label": "False"},
    {"source": "fresh", "target": "serve", "label": "True"},
    {"source": "fetch", "target": "store"},
]

_FUNNEL_EDGE = {
    "categories": ["Visited", "Signed up", "Activated", "Subscribed", "Renewed"],
    "series": [{"name": "Users", "values": [9800, 4100, None, 1200, -5]}],
}

_FUNNEL_HIRING = {
    "categories": ["Applications", "Screened", "Interviewed", "Offers", "Hires"],
    "series": [{"name": "Candidates", "values": [1240, 410, 96, 18, 12]}],
}

_NET_STATIC = {
    "nodes": [
        {"id": "ams", "label": "Amsterdam", "group": "hub", "x": 4.9, "y": -52.4, "value": 9},
        {"id": "fra", "label": "Frankfurt", "group": "hub", "x": 8.7, "y": -50.1, "value": 10},
        {"id": "lon", "label": "London", "group": "hub", "x": -0.1, "y": -51.5, "value": 11},
        {"id": "par", "label": "Paris", "group": "edge", "x": 2.4, "y": -48.9, "value": 6},
        {"id": "mad", "label": "Madrid", "group": "edge", "x": -3.7, "y": -40.4, "value": 5},
        {"id": "mil", "label": "Milan", "group": "edge", "x": 9.2, "y": -45.5, "value": 5},
        {"id": "sto", "label": "Stockholm", "group": "edge", "x": 18.1, "y": -59.3, "value": 4},
    ],
    "links": [
        {"source": "lon", "target": "ams", "value": 8},
        {"source": "ams", "target": "fra", "value": 9},
        {"source": "lon", "target": "par", "value": 6},
        {"source": "par", "target": "fra", "value": 5},
        {"source": "par", "target": "mad", "value": 3},
        {"source": "fra", "target": "mil", "value": 4},
        {"source": "ams", "target": "sto", "value": 3},
    ],
}

_NET_DIRECTED = {
    "directed": True,
    "nodes": [
        {"id": "ana", "label": "Ana", "group": "design"},
        {"id": "ben", "label": "Ben", "group": "eng"},
        {"id": "cho", "label": "Cho", "group": "eng"},
        {"id": "dev", "label": "Dev", "group": "pm"},
        {"id": "eli", "label": "Eli", "group": "eng"},
        {"id": "fay", "label": "Fay", "group": "design"},
    ],
    "links": [
        {"source": "ana", "target": "ben", "value": 3},
        {"source": "ben", "target": "cho", "value": 2},
        {"source": "cho", "target": "ana", "value": 1},
        {"source": "dev", "target": "ben", "value": 4},
        {"source": "dev", "target": "eli", "value": 2},
        {"source": "eli", "target": "fay", "value": 1},
        {"source": "fay", "target": "ana", "value": 2},
    ],
}

# Characters of a play in scene order; links are shared scenes.
_ARC_ORDERED = {
    "nodes": [
        {"id": "romeo", "label": "Romeo", "group": "Montague", "order": 1},
        {"id": "benvolio", "label": "Benvolio", "group": "Montague", "order": 2},
        {"id": "mercutio", "label": "Mercutio", "group": "Prince", "order": 3},
        {"id": "juliet", "label": "Juliet", "group": "Capulet", "order": 4},
        {"id": "nurse", "label": "Nurse", "group": "Capulet", "order": 5},
        {"id": "tybalt", "label": "Tybalt", "group": "Capulet", "order": 6},
        {"id": "laurence", "label": "Friar", "group": "Church", "order": 7},
    ],
    "links": [
        {"source": "romeo", "target": "benvolio", "value": 6},
        {"source": "romeo", "target": "mercutio", "value": 4},
        {"source": "romeo", "target": "juliet", "value": 7},
        {"source": "juliet", "target": "nurse", "value": 6},
        {"source": "mercutio", "target": "tybalt", "value": 2},
        {"source": "romeo", "target": "laurence", "value": 4},
        {"source": "juliet", "target": "laurence", "value": 3},
        {"source": "benvolio", "target": "tybalt", "value": 1},
    ],
}

_DEP_CYCLE = {
    "nodes": [
        {"id": "ui", "label": "ui", "group": "app"},
        {"id": "forms", "label": "forms", "group": "app"},
        {"id": "validate", "label": "validate", "group": "lib"},
        {"id": "i18n", "label": "i18n", "group": "lib"},
        {"id": "format", "label": "format", "group": "lib"},
    ],
    "links": [
        {"source": "ui", "target": "forms"},
        {"source": "forms", "target": "validate"},
        {"source": "validate", "target": "i18n"},
        {"source": "i18n", "target": "format"},
        {"source": "format", "target": "validate"},
        {"source": "forms", "target": "forms"},
    ],
}


# ===========================================================================
# Options shared by renderer families
# ===========================================================================

def _hier_options(type_key):
    """
        The options of the hierlayout.js types.

        :param type_key: The chart type key (its own layout is the default).
        :returns: A list of AttributeDoc.
    """
    options = [
        AttributeDoc(
            name="layout",
            description=(
                "Draws another hierarchy layout with the same data: treemap, sunburst, "
                "icicle (alias partition) or circle-pack (alias pack). Default: the "
                "layout of the chart type."
            ),
            kind="enum",
            values=["treemap", "sunburst", "icicle", "partition", "circle-pack", "pack"],
            default=type_key,
        ),
    ]
    if type_key == "icicle":
        options.append(orientation_option(
            "vertical",
            "vertical: root band at the top; horizontal: root on the left (flame graph).",
        ))
    return options


def _tree_options(type_key):
    """
        The options of the tree.js types.

        :param type_key: The chart type key.
        :returns: A list of AttributeDoc.
    """
    options = [
        AttributeDoc(
            name="mode",
            description=(
                "Draws another tree mode with the same data: tree, dendrogram, org-chart "
                "(alias org), mindmap or decision-tree (alias decision). Default: the mode "
                "of the chart type."
            ),
            kind="enum",
            values=["tree", "dendrogram", "org-chart", "org", "mindmap", "decision-tree",
                    "decision"],
            default=type_key,
        ),
    ]
    if type_key == "dendrogram":
        options.append(orientation_option(
            "horizontal",
            "horizontal: leaves on the left, distance axis along the bottom; vertical: "
            "leaves on top.",
        ))
    elif type_key != "mindmap":
        options.append(orientation_option(
            "vertical", "vertical: root at the top; horizontal: root on the left.",
        ))
        options.append(AttributeDoc(
            name="edge-style",
            description="Connector shape: curve (cubic Bezier) or elbow (right angles).",
            kind="enum",
            values=["curve", "elbow"],
            default="elbow" if type_key == "org-chart" else "curve",
        ))
    return options


def _network_options(type_key):
    """
        The options of the network.js types.

        :param type_key: The chart type key.
        :returns: A list of AttributeDoc.
    """
    defaults = {
        "network": "force", "node-link": "force", "arc-diagram": "arc",
        "edge-bundling": "bundled", "dependency-graph": "layered",
    }
    options = [
        AttributeDoc(
            name="layout",
            description=(
                "force (spring layout), arc (one axis, links as arcs), layered (ranked DAG "
                "with arrowheads), bundled (ring with bundled links) or static (fixed "
                "`nodes[].x` / `y`). Wins over `raw.layout`; default: the type's layout."
            ),
            kind="enum",
            values=["force", "arc", "layered", "bundled", "static"],
            default=defaults[type_key],
        ),
        orientation_option(
            "horizontal" if type_key in ("arc-diagram", "dependency-graph") else None,
            "Used by the arc and layered layouts: horizontal runs the axis / ranks left to "
            "right, vertical top to bottom.",
        ),
    ]
    if type_key in ("network", "node-link"):
        options.append(AttributeDoc(
            name="mode",
            description="`static` selects the static layout when no `layout` is given.",
            kind="enum",
            values=["static"],
        ))
    if type_key == "edge-bundling":
        options.append(AttributeDoc(
            name="tension",
            description=(
                "Bundling strength from 0 (straight chords) to 1 (tightly bundled); "
                "`raw.tension` is used when the attribute is absent."
            ),
            kind="number",
            default="0.85",
        ))
    return options


_FLOWCHART_OPTIONS = [
    orientation_option(
        None,
        "vertical: top to bottom; horizontal: left to right. Not set: the direction that "
        "draws the diagram larger in the chart's box.",
    ),
]

_SANKEY_ORIENTATION = orientation_option(
    "horizontal", "horizontal: columns left to right; vertical: columns top to bottom.",
)


# ===========================================================================
# CHART_TYPES list
# ===========================================================================

CHART_TYPES = [

    # -----------------------------------------------------------------------
    # Part-to-whole
    # -----------------------------------------------------------------------

    ChartTypeDoc(
        type_key="pie",
        title="Pie Chart",
        category="part-to-whole",
        summary="Proportional slices of a whole; each slice is one category.",
        description=(
            "A circle divided into wedges proportional to their values, each slice in "
            "its own colour. Up to 12 slices are drawn; any further categories are "
            "collapsed into an Other slice. When there is room beside the pie every "
            "slice is labelled with its name and share on a leader line; on a narrow "
            "chart wide slices show their share and the legend names them. Values must "
            "be non-negative: a null is a gap and a negative value is left out and "
            "reported with mj-chart-error."
        ),
        data_shape=(
            _CATEGORY_SHAPE
            + "<ul>"
            "<li><code>categories</code>: slice names (the legend lists them).</li>"
            "<li><code>series[0].values</code>: slice magnitudes, one per category; only "
            "the first series is drawn. <code>null</code> = no slice.</li>"
            "<li><code>meta[\"center-label\"]</code>: text in the hole when "
            "<code>inner-radius</code> &gt; 0.</li>"
            "</ul>"
        ),
        options=[
            AttributeDoc(
                name="inner-radius",
                description="Hole size as a fraction of the radius, 0 to 0.95; above 0 draws a ring.",
                kind="number",
                default="0",
            ),
        ],
        examples=[
            basic_example(_pie_example, "<p>Six traffic sources, each slice labelled with its name and share.</p>"),
            gallery_example(
                "legend",
                "Narrow chart with legend",
                "<p>On a narrow chart the slice names are shortened; "
                "the <code>&lt;mj-chart-legend&gt;</code> lists them in full.</p>",
                chart_markup("pie", _pie_data, label="Sessions by source",
                        style="height:240px; max-inline-size:320px", legend=True),
            ),
            gallery_example(
                "many-slices",
                "Over 12 categories",
                "<p>Fifteen languages: the four smallest are collapsed into one Other slice.</p>",
                chart_markup("pie", _LANGUAGES, label="Repositories by language", style="height:300px"),
            ),
            gallery_example(
                "edge-data",
                "Null and negative values",
                "<p>Organic Search is <code>null</code> (no slice) and Social is negative: it is "
                "left out and <code>mj-chart-error</code> appears in the Events panel.</p>",
                chart_markup("pie", _PIE_EDGE, label="Sessions with gaps", legend=True),
            ),
            events_example(
                "pie", _pie_data, ["mj-chart-slice-click"], "[part=slice]",
                description=(
                    "<p>Click a slice, or focus the chart and press Enter: "
                    "<code>mj-chart-slice-click</code> carries the label, value and fraction. "
                    "The script activates two slices on load.</p>"
                ),
            ),
        ],
    ),

    ChartTypeDoc(
        type_key="donut",
        title="Donut Chart",
        category="part-to-whole",
        summary="Like a pie chart but with a hollow centre that can display a label.",
        description=(
            "The pie renderer drawn as a ring. The hole is half the radius by default; "
            "the inner-radius attribute sets it as a fraction between 0 and 0.95 (0 gives "
            "a full pie). An optional center-label in meta is drawn inside the hole. A "
            "single 100% slice draws a whole ring."
        ),
        data_shape=(
            _CATEGORY_SHAPE
            + "<ul>"
            "<li><code>series[0].values</code>: slice magnitudes (non-negative; "
            "<code>null</code> = no slice).</li>"
            "<li><code>meta[\"center-label\"]</code>: optional text drawn in the hole.</li>"
            "</ul>"
        ),
        options=[
            AttributeDoc(
                name="inner-radius",
                description="Hole size as a fraction of the radius, 0 to 0.95 (0 draws a pie).",
                kind="number",
                default="0.5",
            ),
        ],
        examples=[
            basic_example(_donut_example, "<p>Traffic sources as a ring with the total in the centre.</p>"),
            gallery_example(
                "thin-ring",
                "Thin ring with legend",
                "<p><code>inner-radius=\"0.78\"</code> leaves a thin ring around the centre label.</p>",
                chart_markup("donut", _DONUT_THIN, label="Monthly cloud spend",
                        attrs={"inner-radius": "0.78"}, legend=True),
            ),
            gallery_example(
                "single-slice",
                "One 100% slice",
                "<p>A single category draws a complete ring rather than nothing.</p>",
                chart_markup("donut", _DONUT_SINGLE, label="Availability", style="height:220px"),
            ),
            events_example(
                "donut", _donut_data, ["mj-chart-slice-click"], "[part=slice]",
                description="<p>Click a ring segment to read its <code>mj-chart-slice-click</code> detail.</p>",
            ),
        ],
    ),

    ChartTypeDoc(
        type_key="waffle",
        title="Waffle Chart",
        category="part-to-whole",
        summary="Unit grid where each cell represents a fraction of the whole.",
        description=(
            "A grid of square cells (10 x 10 by default) coloured by category, with a key "
            "naming each category and its share. Values that sum to the cell count are "
            "cell counts; other values are shared out with the largest-remainder method, "
            "so the grid is always exactly full. Each category is one focus stop, and "
            "hovering or focusing it highlights its cells. Nulls are gaps; negative values "
            "get no cells and raise mj-chart-error."
        ),
        data_shape=(
            "<pre><code>{\n"
            "  categories: string[],\n"
            "  series: [{ name: string, values: (number | null)[] }],\n"
            "  meta?: { grid?: { cols: number, rows: number } }\n"
            "}</code></pre>"
            "<ul>"
            "<li><code>series[0].values[i]</code>: amount of category <i>i</i>; values past "
            "the categories are ignored.</li>"
            "<li><code>meta.grid</code>: grid size, default 10 x 10.</li>"
            "</ul>"
        ),
        options=[],
        examples=[
            basic_example(_waffle_example, "<p>Quarterly sales shares on a 10 x 10 grid.</p>"),
            gallery_example(
                "cell-counts",
                "Wide grid, cell counts",
                "<p><code>meta.grid</code> is 20 x 5 and the values sum to 100, so each value is "
                "a number of cells.</p>",
                chart_markup("waffle", _WAFFLE_COUNTS, label="Electricity generation mix",
                        style="height:220px", legend=True),
            ),
            gallery_example(
                "proportional",
                "Shared out proportionally",
                "<p>864 survey answers on 100 cells: the largest-remainder method keeps the grid "
                "full. No answer is <code>null</code> and gets no cells.</p>",
                chart_markup("waffle", _WAFFLE_SURVEY, label="Customer satisfaction", legend=True),
            ),
            events_example(
                "waffle", _waffle_data, ["mj-chart-cell-click"], "[part=category]",
                description=(
                    "<p>Click a category's cells, or press Enter on it: "
                    "<code>mj-chart-cell-click</code> reports the category, value and fraction.</p>"
                ),
            ),
        ],
    ),

    ChartTypeDoc(
        type_key="marimekko",
        title="Marimekko Chart",
        category="part-to-whole",
        summary=(
            "Variable-width stacked bar where column widths encode column totals "
            "and segment heights encode conditional shares."
        ),
        description=(
            "Also called a Mekko chart. Column widths are proportional to each column's "
            "share of the grand total; within each column the segment heights are "
            "normalised to 100%, so each column shows the series breakdown of its "
            "category. Column names and shares are only printed where they fit (names "
            "are shortened first); the tooltip, legend and table keep the full names. A "
            "null is a gap; negative values are not drawn and raise mj-chart-error."
        ),
        data_shape=(
            _CATEGORY_SHAPE
            + "<ul>"
            "<li><code>categories</code>: the columns.</li>"
            "<li><code>series</code>: the breakdown; <code>values[i]</code> is the magnitude "
            "of the series in column <i>i</i>.</li>"
            "</ul>"
        ),
        options=[],
        examples=[
            basic_example(_marimekko_example, "<p>Revenue by region (column width) and customer segment (height).</p>"),
            gallery_example(
                "many-columns",
                "Six columns, long names",
                "<p>Narrow columns shorten or drop their names; hover a segment for the full text.</p>",
                chart_markup("marimekko", _MEKKO_WIDE, label="Infrastructure spend by country",
                        style="height:300px", legend=True),
            ),
            gallery_example(
                "edge-data",
                "Null and negative values",
                "<p>South has no Online value (gap) and East's Retail value is negative: it is "
                "not drawn and <code>mj-chart-error</code> is logged.</p>",
                chart_markup("marimekko", _MEKKO_EDGE, label="Sales channels", legend=True),
            ),
            events_example(
                "marimekko", _marimekko_data, ["mj-chart-segment-click"], "[part=segment]",
                legend=True,
                description=(
                    "<p><code>mj-chart-segment-click</code> reports the series, category, value "
                    "and the segment's share of its column (<code>pct</code>).</p>"
                ),
            ),
        ],
    ),

    ChartTypeDoc(
        type_key="mosaic",
        title="Mosaic Plot",
        category="part-to-whole",
        summary="Contingency-table visualisation where tile area encodes cell frequency.",
        description=(
            "Shows the joint distribution of two categorical variables. Column widths are "
            "proportional to the column totals, and segment heights within a column to "
            "the conditional frequencies. With meta.residuals the cells are shaded by "
            "their Pearson residual (blue above, orange below what independence predicts, "
            "neutral within plus or minus 2); without it they take their row's series "
            "colour. meta equal-widths draws a spine plot. Negative frequencies count as 0 "
            "and raise mj-chart-error."
        ),
        data_shape=(
            "<pre><code>{\n"
            "  categories: string[],          // column variable levels\n"
            "  series: [{ name: string, values: (number | null)[] }],  // row levels\n"
            "  meta?: { residuals?: boolean, \"equal-widths\"?: boolean }\n"
            "}</code></pre>"
            "<ul>"
            "<li><code>series[s].values[c]</code>: frequency of row level <i>s</i> in "
            "column <i>c</i>.</li>"
            "<li><code>meta.residuals</code>: shade cells by Pearson residual; the legend "
            "lists the bands.</li>"
            "<li><code>meta[\"equal-widths\"]</code>: all columns equally wide (spine plot).</li>"
            "</ul>"
        ),
        options=[],
        examples=[
            basic_example(_mosaic_example, "<p>Titanic survival by class, shaded by residual: crew and third class perished more than independence predicts.</p>"),
            gallery_example(
                "series-colours",
                "Series colours",
                "<p>Without <code>meta.residuals</code> the cells take their row's colour and the "
                "legend lists the eye colours.</p>",
                chart_markup("mosaic", _MOSAIC_HAIR, label="Eye colour by hair colour",
                        style="height:300px", legend=True),
            ),
            gallery_example(
                "spine",
                "Spine plot",
                "<p><code>meta[\"equal-widths\"]</code> gives every age group the same width, so "
                "only the conditional shares are compared.</p>",
                chart_markup("mosaic", _MOSAIC_SPINE, label="Device preference by age", legend=True),
            ),
            events_example(
                "mosaic", _mosaic_data, ["mj-chart-cell-click"], "[part=cell]", legend=True,
                description=(
                    "<p><code>mj-chart-cell-click</code> reports the series, category, value, "
                    "share and Pearson residual of the cell.</p>"
                ),
            ),
        ],
    ),

    ChartTypeDoc(
        type_key="waterfall",
        title="Waterfall Chart",
        category="part-to-whole",
        summary="Cascade of running-total deltas with start, subtotal, and total bars.",
        description=(
            "Shows how an opening value is changed by a series of increases and decreases. "
            "Each step's kind comes from a parallel kinds array or from object values: "
            "start, delta (default), add or increase, subtract or decrease, subtotal and "
            "total; a null subtotal or total is computed from the running sum. Increases "
            "and decreases use a colour-blind-safe blue and orange pair and totals a "
            "neutral colour (override with --mj-chart-positive, --mj-chart-negative and "
            "--mj-chart-neutral). Every bar is labelled and dashed connectors join "
            "consecutive bars. An unknown kind is drawn as a delta and raises mj-chart-error."
        ),
        data_shape=(
            "<pre><code>{\n"
            "  categories: string[],\n"
            "  series: [{\n"
            "    name: string,\n"
            "    values: (number | null | { v: number | null, kind: string })[],\n"
            "    kinds?: string[]\n"
            "  }]\n"
            "}</code></pre>"
            "<ul>"
            "<li><code>values[i]</code>: the step amount, or <code>{v, kind}</code> "
            "(<code>value</code> / <code>type</code> also work).</li>"
            "<li><code>kinds[i]</code>: start, delta, add, increase, subtract, decrease, "
            "subtotal or total (case-insensitive).</li>"
            "<li>A <code>null</code> subtotal / total is the running sum; a number sets "
            "an explicit checkpoint.</li>"
            "</ul>"
        ),
        options=[orientation_option("vertical", "vertical: columns; horizontal: bars from left to right.")],
        examples=[
            basic_example(_waterfall_example, "<p>Monthly revenue changes with a computed Q1 subtotal and H1 total.</p>"),
            gallery_example(
                "horizontal",
                "Horizontal P&amp;L bridge",
                "<p><code>orientation=\"horizontal\"</code>; steps use the <code>{v, kind}</code> "
                "form with subtract / decrease kinds, so amounts are written unsigned.</p>",
                chart_markup("waterfall", _WATERFALL_PNL, label="Profit and loss bridge",
                        attrs={"orientation": "horizontal"}, style="height:300px", legend=True),
            ),
            gallery_example(
                "custom-colours",
                "Custom colours",
                "<p>The page sets <code>--mj-chart-positive</code>, <code>--mj-chart-negative</code> "
                "and <code>--mj-chart-neutral</code> on the chart.</p>",
                chart_markup("waterfall", _waterfall_data, chart_id="branded",
                        label="Revenue delta, custom colours", legend=True),
                css=(
                    "#branded {\n"
                    "  --mj-chart-positive: var(--mj-chart-series-3);\n"
                    "  --mj-chart-negative: var(--mj-chart-series-5);\n"
                    "  --mj-chart-neutral: var(--mj-text-muted);\n"
                    "}"
                ),
            ),
            events_example(
                "waterfall", _waterfall_data, ["mj-chart-bar-click"], "[part=bar]",
                description=(
                    "<p><code>mj-chart-bar-click</code> reports the category, index, amount, kind "
                    "and the running total after the bar.</p>"
                ),
            ),
        ],
    ),

    ChartTypeDoc(
        type_key="pareto",
        title="Pareto Chart",
        category="part-to-whole",
        summary="Sorted bars plus a cumulative-percentage line, with an 80% reference.",
        description=(
            "Categories are sorted by value, largest first (ties keep data order). A "
            "cumulative-percentage line runs on a right axis and a dashed 80% reference "
            "line marks the vital few (meta pareto-line false hides it). Category labels "
            "are level when they fit, rotated when they do not, and thinned out when even "
            "rotated labels would collide. Nulls are left out; negative counts are left "
            "out and raise mj-chart-error."
        ),
        data_shape=(
            _CATEGORY_SHAPE
            + "<ul>"
            "<li><code>series[0].values</code>: counts, in any order.</li>"
            "<li><code>meta[\"pareto-line\"]</code>: <code>false</code> hides the 80% line.</li>"
            "</ul>"
        ),
        options=[],
        examples=[
            basic_example(_pareto_example, "<p>Complaint causes: three of seven make up over 70% of the total.</p>"),
            gallery_example(
                "many-categories",
                "Unsorted data, no 80% line",
                "<p>Twelve incident causes given in any order are sorted; the long labels rotate. "
                "<code>meta[\"pareto-line\"]: false</code> hides the reference line.</p>",
                chart_markup("pareto", _PARETO_INCIDENTS, label="Production incidents by cause",
                        style="height:320px", legend=True),
            ),
            gallery_example(
                "edge-data",
                "Null and negative counts",
                "<p>Dent is <code>null</code> and Loose part negative: both are left out and "
                "<code>mj-chart-error</code> names the negative one.</p>",
                chart_markup("pareto", _PARETO_EDGE, label="Defects found at inspection", legend=True),
            ),
            events_example(
                "pareto", _pareto_data, ["mj-chart-bar-click", "mj-chart-dot-click"],
                "[part=bar]", enter="click:[part=dot]", legend=True,
                description=(
                    "<p>Bars emit <code>mj-chart-bar-click</code> (with <code>cumulativePct</code>); "
                    "the line's dots emit <code>mj-chart-dot-click</code> (clickable, not tab "
                    "stops). The script clicks the first bar and the last dot.</p>"
                ),
            ),
        ],
    ),

    # -----------------------------------------------------------------------
    # Hierarchical -- hierlayout.js
    # -----------------------------------------------------------------------

    ChartTypeDoc(
        type_key="treemap",
        title="Treemap",
        category="hierarchical",
        summary="Squarified space-filling rectangles sized by subtree value.",
        description=(
            "Partitions the plot into tiles whose areas are proportional to node totals "
            "(Bruls squarified algorithm). The root is not drawn; each group gets a header "
            "strip with its name, and every tile takes the colour of its top-level branch, "
            "lighter at deeper levels. Leaves carry value; an internal node without its "
            "own value is the sum of its children; missing or negative values count as 0. "
            "The accessible table lists every node with its parent, level, value and share."
        ),
        data_shape=(
            _TREE_SHAPE
            + "<ul>"
            "<li><code>root</code>: nested tree; leaves carry <code>value</code>.</li>"
            "<li>An internal <code>value</code> is optional (default: the sum of its "
            "children).</li>"
            "<li>A <code>root</code> given as an array is read as the children of an unnamed "
            "root.</li>"
            "</ul>"
        ),
        options=_hier_options("treemap"),
        examples=[
            basic_example(_treemap_example, "<p>Product cost by component: three branches, each with its own colour.</p>"),
            gallery_example(
                "deep",
                "Four levels with legend",
                "<p>Disk usage four levels deep; the legend lists the top-level folders.</p>",
                chart_markup("treemap", {"root": _DISK_ROOT}, label="Disk usage (MB)",
                        style="height:320px", legend=True),
            ),
            gallery_example(
                "flat",
                "Array root, missing values",
                "<p>A <code>root</code> array is one level of tiles. Transport has no value and "
                "Gifts is negative: both count as 0 and draw nothing.</p>",
                chart_markup("treemap", _BUDGET_FLAT, label="Monthly budget"),
            ),
            events_example(
                "treemap", {"root": _HIER_ROOT}, ["mj-chart-node-click"], "[part=treemap-tile]",
                label="Product cost by component",
                description=(
                    "<p><code>mj-chart-node-click</code> reports the name, total value, depth and "
                    "the <code>path</code> from the root.</p>"
                ),
            ),
        ],
    ),

    ChartTypeDoc(
        type_key="sunburst",
        title="Sunburst",
        category="hierarchical",
        summary="Radial partition chart: the root disc in the centre, one ring per tree depth.",
        description=(
            "The root is the centre disc and each depth level is one ring; arc spans are "
            "proportional to subtree totals and colours follow the top-level branch, "
            "lighter further out. Uses the same root tree as the treemap; layout sunburst "
            "draws this layout on any of the four hierarchy types."
        ),
        data_shape=(
            _TREE_SHAPE
            + "<p>Same shape as <code>treemap</code>: leaves carry <code>value</code>, internal "
            "nodes default to the sum of their children.</p>"
        ),
        options=_hier_options("sunburst"),
        examples=[
            basic_example(_sunburst_example, "<p>Product cost by component with the branch legend.</p>"),
            gallery_example(
                "deep",
                "Four rings",
                "<p>Disk usage: one ring per folder level, the deepest ring lightest.</p>",
                chart_markup("sunburst", {"root": _DISK_ROOT}, label="Disk usage (MB)",
                        style="height:340px", legend=True),
            ),
            gallery_example(
                "from-treemap-data",
                "layout attribute",
                "<p>A <code>type=\"treemap\"</code> chart with <code>layout=\"sunburst\"</code> "
                "draws this layout: the attribute wins over the type.</p>",
                chart_markup("treemap", {"root": _PROFILE_ROOT}, label="CPU time by function (ms)",
                        attrs={"layout": "sunburst"}, style="height:300px"),
            ),
            events_example(
                "sunburst", {"root": _HIER_ROOT}, ["mj-chart-node-click"], "[part=sunburst-arc]",
                label="Product cost by component", style="height:300px",
                description="<p>Click an arc: <code>mj-chart-node-click</code> carries its <code>path</code>.</p>",
            ),
        ],
    ),

    ChartTypeDoc(
        type_key="icicle",
        title="Icicle Chart",
        category="hierarchical",
        summary="Rectangular partition bands, root at top, leaves at bottom.",
        description=(
            "One band per depth level, root first; within a band, child widths are "
            "proportional to their subtree totals relative to the parent, and colours "
            "follow the top-level branch. orientation horizontal puts the root on the "
            "left, which gives a flame graph."
        ),
        data_shape=_TREE_SHAPE + "<p>Same shape as <code>treemap</code>.</p>",
        options=_hier_options("icicle"),
        examples=[
            basic_example(_icicle_example, "<p>Product cost by component, root band on top.</p>"),
            gallery_example(
                "flame-graph",
                "Flame graph",
                "<p><code>orientation=\"horizontal\"</code>: a CPU profile with the root on the left.</p>",
                chart_markup("icicle", {"root": _PROFILE_ROOT}, label="CPU time by function (ms)",
                        attrs={"orientation": "horizontal"}),
            ),
            gallery_example(
                "deep",
                "Four levels with legend",
                "<p>Disk usage four levels deep.</p>",
                chart_markup("icicle", {"root": _DISK_ROOT}, label="Disk usage (MB)",
                        style="height:300px", legend=True),
            ),
            events_example(
                "icicle", {"root": _HIER_ROOT}, ["mj-chart-node-click"], "[part=icicle-tile]",
                label="Product cost by component",
                description="<p>Click a band: <code>mj-chart-node-click</code> reports name, value, depth and path.</p>",
            ),
        ],
    ),

    ChartTypeDoc(
        type_key="circle-pack",
        title="Circle Pack",
        category="hierarchical",
        summary="Nested packed circles whose areas are proportional to values.",
        description=(
            "Leaf radii follow a square-root scale so area encodes value. Siblings are "
            "packed without overlap (front-chain packing) inside the smallest enclosing "
            "circle of their parent, and the whole layout is scaled to fit the plot. "
            "Groups are drawn as light discs in their branch colour. Same root tree as the "
            "treemap; layout pack is an alias."
        ),
        data_shape=_TREE_SHAPE + "<p>Same shape as <code>treemap</code>.</p>",
        options=_hier_options("circle-pack"),
        examples=[
            basic_example(_circle_pack_example, "<p>Product cost by component with the branch legend.</p>"),
            gallery_example(
                "deep",
                "Nested four levels",
                "<p>Disk usage: folders nest inside folders.</p>",
                chart_markup("circle-pack", {"root": _DISK_ROOT}, label="Disk usage (MB)",
                        style="height:340px", legend=True),
            ),
            gallery_example(
                "flat",
                "One level",
                "<p>An array <code>root</code>: one circle per entry; entries without a positive "
                "value draw nothing.</p>",
                chart_markup("circle-pack", _BUDGET_FLAT, label="Monthly budget"),
            ),
            events_example(
                "circle-pack", {"root": _HIER_ROOT}, ["mj-chart-node-click"], "[part=pack-circle]",
                label="Product cost by component", style="height:300px",
                description="<p>Click a circle to read its <code>mj-chart-node-click</code> detail.</p>",
            ),
        ],
    ),

    # -----------------------------------------------------------------------
    # Hierarchical -- tree.js
    # -----------------------------------------------------------------------

    ChartTypeDoc(
        type_key="tree",
        title="Tree",
        category="hierarchical",
        summary="Tidy node-link tree layout.",
        description=(
            "A tidy tree: leaves evenly spaced along one axis, depth along the other, "
            "parents centred over their children. Edges are curves or elbows "
            "(edge-style); orientation horizontal puts the root on the left. A tree larger "
            "than the chart is scaled to fit (long labels are shortened first). Nodes may "
            "carry a value, shown in their tooltip and the node table."
        ),
        data_shape=(
            _TREE_SHAPE
            + "<ul>"
            "<li><code>name</code>: node label (a number is fine; a missing name draws no "
            "label).</li>"
            "<li><code>value</code>: optional, shown in the tooltip and table.</li>"
            "</ul>"
        ),
        options=_tree_options("tree"),
        examples=[
            basic_example(_tree_example, "<p>Engineering teams, root on top with curved connectors.</p>"),
            gallery_example(
                "horizontal-elbow",
                "Horizontal with elbows",
                "<p><code>orientation=\"horizontal\"</code> and <code>edge-style=\"elbow\"</code>.</p>",
                chart_markup("tree", {"root": _TREE_ROOT}, label="Engineering teams",
                        attrs={"orientation": "horizontal", "edge-style": "elbow"}, style="height:320px"),
            ),
            gallery_example(
                "large",
                "40 nodes, scaled to fit",
                "<p>A fleet of 40 nodes: the layout shrinks to the chart and leaf labels stagger.</p>",
                chart_markup("tree", {"root": _large_tree()}, label="Service fleet", style="height:320px"),
            ),
            events_example(
                "tree", {"root": _TREE_ROOT}, ["mj-chart-node-click"], "[part=tree-node]",
                label="Engineering teams",
                description=(
                    "<p><code>mj-chart-node-click</code> reports name, value, depth, role and the "
                    "<code>path</code> from the root.</p>"
                ),
            ),
        ],
    ),

    ChartTypeDoc(
        type_key="dendrogram",
        title="Dendrogram",
        category="hierarchical",
        summary="Hierarchical clustering tree where the merge point encodes distance.",
        description=(
            "Leaves sit at distance 0, equally spaced; each internal node is drawn at its "
            "merge distance (distance, height or value) on a labelled distance axis, and "
            "its children's stems join with a crossbar there. Without distances every "
            "merge is one level above its tallest child. Horizontal by default (leaves on "
            "the left); orientation vertical puts the leaves on top."
        ),
        data_shape=(
            _TREE_SHAPE
            + "<ul>"
            "<li><code>distance</code> (or <code>height</code>, <code>value</code>): merge "
            "distance of an internal node; leaves default to 0.</li>"
            "</ul>"
        ),
        options=_tree_options("dendrogram"),
        examples=[
            basic_example(_dendrogram_example, "<p>Tissue samples clustered by expression distance.</p>"),
            gallery_example(
                "vertical",
                "Leaves on top",
                "<p><code>orientation=\"vertical\"</code>: the distance axis runs down the side.</p>",
                chart_markup("dendrogram", _dendrogram_data, label="Tissue sample clustering",
                        attrs={"orientation": "vertical"}, style="height:320px"),
            ),
            gallery_example(
                "no-distances",
                "Without distances",
                "<p>No <code>distance</code> fields: each merge is one level above its tallest child.</p>",
                chart_markup("dendrogram", _DENDRO_PLAIN, label="Fruit taxonomy"),
            ),
            events_example(
                "dendrogram", _dendrogram_data, ["mj-chart-node-click"], "[part=tree-node]",
                label="Tissue sample clustering",
                description="<p>Click a node: <code>mj-chart-node-click</code> carries its path.</p>",
            ),
        ],
    ),

    ChartTypeDoc(
        type_key="org-chart",
        title="Org Chart",
        category="hierarchical",
        summary="Reporting hierarchy drawn as cards with a name and a role line.",
        description=(
            "A tidy tree drawn with cards joined by elbow connectors. Each node has a "
            "name (bold) and an optional role (muted line). Cards narrow to fit the width "
            "(long text is shortened; the full text stays in the tooltip and table) and a "
            "wider chart is scaled down. mode org selects this layout on a tree chart."
        ),
        data_shape=(
            _TREE_SHAPE.replace("value?: number", "role?: string")
            + "<ul><li><code>role</code>: optional second line of the card.</li></ul>"
        ),
        options=_tree_options("org-chart"),
        examples=[
            basic_example(_org_example, "<p>A leadership team three levels deep.</p>"),
            gallery_example(
                "horizontal",
                "Horizontal",
                "<p><code>orientation=\"horizontal\"</code> grows the chart to the right.</p>",
                chart_markup("org-chart", {"root": _ORG_ROOT}, label="Leadership team",
                        attrs={"orientation": "horizontal"}, style="height:360px"),
            ),
            gallery_example(
                "long-content",
                "Long names, curved edges",
                "<p>Long roles are shortened on the cards (hover for the full text); "
                "<code>edge-style=\"curve\"</code> replaces the elbows.</p>",
                chart_markup("org-chart", {"root": _ORG_LONG}, label="Executive staff",
                        attrs={"edge-style": "curve"}, style="height:220px"),
            ),
            events_example(
                "org-chart", {"root": _ORG_ROOT}, ["mj-chart-node-click"], "[part=org-node]",
                label="Leadership team",
                description="<p><code>mj-chart-node-click</code> includes the card's <code>role</code>.</p>",
            ),
        ],
    ),

    ChartTypeDoc(
        type_key="mindmap",
        title="Mind Map",
        category="hierarchical",
        summary="Central topic with branches growing to both sides, coloured per branch.",
        description=(
            "The root bubble sits in the centre; first-level branches are split between "
            "the right and left sides to balance their leaves, and each side grows outward "
            "in columns as wide as their widest label, so bubbles never overlap. On a "
            "narrow chart all branches go to one side when that fits better. Connectors "
            "and outlines take the first-level branch colour."
        ),
        data_shape=_TREE_SHAPE + "<p>Only <code>name</code> and <code>children</code> are drawn.</p>",
        options=_tree_options("mindmap"),
        examples=[
            basic_example(_mindmap_example, "<p>Four strategy themes balanced on both sides of the centre.</p>"),
            gallery_example(
                "narrow",
                "Narrow chart",
                "<p>At 340px wide the branches move to one side.</p>",
                chart_markup("mindmap", {"root": _MINDMAP_ROOT}, label="Strategy 2026 themes",
                        style="height:360px; max-inline-size:340px"),
            ),
            gallery_example(
                "small",
                "Two branches",
                "<p>A small launch plan: one branch per side.</p>",
                chart_markup("mindmap", {"root": _MINDMAP_SMALL}, label="Launch plan", style="height:220px"),
            ),
            events_example(
                "mindmap", {"root": _MINDMAP_ROOT}, ["mj-chart-node-click"], "[part=mindmap-node]",
                label="Strategy 2026 themes",
                description="<p>Click a bubble to read its <code>mj-chart-node-click</code> detail.</p>",
            ),
        ],
    ),

    ChartTypeDoc(
        type_key="decision-tree",
        title="Decision Tree",
        category="hierarchical",
        summary="Tidy tree of decision and outcome boxes with conditions on the edges.",
        description=(
            "Decision nodes are boxes, outcomes (leaves) are tinted pills, and each edge "
            "shows the condition from the child's edgeLabel (or label when the node also "
            "has a name); edges without a condition stay unlabelled. Vertical by default; "
            "orientation horizontal grows the tree to the right. mode decision selects "
            "this layout on a tree chart."
        ),
        data_shape=(
            "<pre><code>{\n"
            "  root: { name: string, edgeLabel?: string, children?: [ ...same shape ] }\n"
            "}</code></pre>"
            "<ul><li><code>edgeLabel</code> (or <code>label</code> next to a "
            "<code>name</code>): the condition on the edge from the parent.</li></ul>"
        ),
        options=_tree_options("decision-tree"),
        examples=[
            basic_example(_decision_tree_example, "<p>A loan decision: conditions on the edges, outcomes as pills.</p>"),
            gallery_example(
                "horizontal",
                "Horizontal",
                "<p><code>orientation=\"horizontal\"</code> reads left to right.</p>",
                chart_markup("decision-tree", {"root": _DT_ROOT}, label="Loan application decision",
                        attrs={"orientation": "horizontal"}, style="height:320px"),
            ),
            gallery_example(
                "elbow",
                "Elbow connectors",
                "<p><code>edge-style=\"elbow\"</code> draws right-angled edges.</p>",
                chart_markup("decision-tree", {"root": _DT_ROOT}, label="Loan application decision",
                        attrs={"edge-style": "elbow"}, style="height:300px"),
            ),
            events_example(
                "decision-tree", {"root": _DT_ROOT}, ["mj-chart-node-click"], "[part=decision-node]",
                label="Loan application decision", style="height:300px",
                description="<p>Click a box: <code>mj-chart-node-click</code> carries the path of decisions.</p>",
            ),
        ],
    ),

    # -----------------------------------------------------------------------
    # Flow & Process
    # -----------------------------------------------------------------------

    ChartTypeDoc(
        type_key="sankey",
        title="Sankey Diagram",
        category="flow-and-process",
        summary="Flow ribbons whose widths encode transfer quantities between nodes.",
        description=(
            "A node's column is its longest path from a source node; columns run left to "
            "right by default (orientation vertical stacks them top to bottom). One value "
            "scale sizes every node bar and ribbon, so the ribbons leaving a node fill it "
            "exactly; nodes are relaxed toward their neighbours to reduce crossings. "
            "Self-links and links that close a cycle are not drawn and are flagged in the "
            "data table; links without a positive value are not drawn. mode alluvial "
            "switches to the alluvial layout."
        ),
        data_shape=(
            _GRAPH_SHAPE
            + "<ul>"
            "<li><code>nodes</code>: optional; nodes named only in <code>links</code> are "
            "added.</li>"
            "<li><code>links[].value</code>: flow size; must be positive.</li>"
            "</ul>"
        ),
        options=[
            _SANKEY_ORIENTATION,
            AttributeDoc(name="mode", description="`alluvial` lays the nodes out by their `time` / `group` columns.",
                         kind="enum", values=["sankey", "alluvial"], default="sankey"),
        ],
        examples=[
            basic_example(_sankey_example, "<p>Website visitors flowing from source to purchase.</p>"),
            gallery_example(
                "vertical",
                "Vertical",
                "<p><code>orientation=\"vertical\"</code>: columns run top to bottom.</p>",
                chart_markup("sankey", {"nodes": _FLOW_NODES, "links": _FLOW_LINKS},
                        label="Website visitor flow", attrs={"orientation": "vertical"},
                        style="height:420px"),
            ),
            gallery_example(
                "cycle",
                "Cycle and self-link",
                "<p>Savings flows back to Budget (a cycle), Living costs links to itself and "
                "Housing to Savings has value 0: none of them is drawn; open the data table to "
                "see them flagged.</p>",
                chart_markup("sankey", _BUDGET_FLOW, label="Monthly budget flow"),
            ),
            events_example(
                "sankey", {"nodes": _FLOW_NODES, "links": _FLOW_LINKS},
                ["mj-chart-link-click", "mj-chart-node-click"], "[part=link]", enter="[part=node]",
                label="Website visitor flow",
                description=(
                    "<p>Ribbons emit <code>mj-chart-link-click</code> (source, target, value) and "
                    "node bars <code>mj-chart-node-click</code> (id, label).</p>"
                ),
            ),
        ],
    ),

    ChartTypeDoc(
        type_key="alluvial",
        title="Alluvial Diagram",
        category="flow-and-process",
        summary="Sankey variant whose columns come from each node's time or group field.",
        description=(
            "The sankey ribbon layout, but each node is pinned to the column of its time "
            "value (sorted) or, failing that, its group (in order of first appearance), "
            "with the column names drawn as headers. Shows how a population redistributes "
            "across survey waves or classification dimensions. Links that do not run to a "
            "later column are not drawn."
        ),
        data_shape=(
            "<pre><code>{\n"
            "  nodes: [{ id: string, label?: string, time?: number | string, group?: string }],\n"
            "  links: [{ source: string, target: string, value: number }]\n"
            "}</code></pre>"
            "<ul>"
            "<li><code>time</code>: column key, sorted; else <code>group</code>, in order of "
            "first appearance.</li>"
            "<li><code>links[].value</code>: positive flow size.</li>"
            "</ul>"
        ),
        options=[_SANKEY_ORIENTATION],
        examples=[
            basic_example(_alluvial_example, "<p>Visits by source, device and user type: one column per <code>group</code>.</p>"),
            gallery_example(
                "time",
                "Survey waves",
                "<p>Columns from <code>time</code> (2023, 2024, 2025): how NPS answers move "
                "between waves.</p>",
                chart_markup("alluvial", {"nodes": _WAVES_NODES, "links": _WAVES_LINKS},
                        label="NPS category by survey wave", style="height:300px"),
            ),
            gallery_example(
                "vertical",
                "Vertical",
                "<p><code>orientation=\"vertical\"</code>: the columns become rows.</p>",
                chart_markup("alluvial", {"nodes": _ALLUVIAL_NODES, "links": _ALLUVIAL_LINKS},
                        label="Visits by source, device and user type",
                        attrs={"orientation": "vertical"}, style="height:400px"),
            ),
            events_example(
                "alluvial", {"nodes": _ALLUVIAL_NODES, "links": _ALLUVIAL_LINKS},
                ["mj-chart-link-click", "mj-chart-node-click"], "[part=link]", enter="[part=node]",
                label="Visits by source, device and user type",
                description="<p>Same events as the sankey: <code>mj-chart-link-click</code> and <code>mj-chart-node-click</code>.</p>",
            ),
        ],
    ),

    ChartTypeDoc(
        type_key="chord",
        title="Chord Diagram",
        category="flow-and-process",
        summary="Circular arc segments connected by ribbons proportional to flow values.",
        description=(
            "Each node is an arc on a ring as long as the ribbon ends it holds. One ribbon "
            "joins each connected pair: when both directions are given it is as wide at "
            "each end as the flow that end sends (Asia-Pac sends more to N. America than it "
            "receives), a one-way flow is equally wide at both ends, and the ribbon takes "
            "the colour of the bigger sender. A self-link is a loop on its own arc. Links "
            "without a positive value are ignored and nodes without flow get no arc. "
            "Labels are shortened when space is tight."
        ),
        data_shape=(
            _GRAPH_SHAPE
            + "<ul>"
            "<li>Links are directed; duplicates add up. A pair may be listed once (one-way) "
            "or in both directions.</li>"
            "<li><code>source === target</code> draws a loop.</li>"
            "</ul>"
        ),
        options=[],
        examples=[
            basic_example(_chord_example, "<p>Trade flows between six regions; two pairs flow both ways.</p>"),
            gallery_example(
                "one-way",
                "One-way flows and a loop",
                "<p>Hand-offs between teams listed once per pair; Engineering's self-link is a loop.</p>",
                chart_markup("chord", _CHORD_ONEWAY, label="Hand-offs between teams"),
            ),
            gallery_example(
                "edge-data",
                "Zero and negative values",
                "<p>Links to and from Legal are 0, negative or missing: they are ignored and Legal "
                "gets no arc.</p>",
                chart_markup("chord", _CHORD_EDGE, label="Ticket transfers"),
            ),
            events_example(
                "chord", {"nodes": _CHORD_NODES, "links": _CHORD_LINKS},
                ["mj-chart-chord-click", "mj-chart-node-click"], "[part=chord]", enter="[part=arc]",
                label="Trade flows between regions",
                description=(
                    "<p>Ribbons emit <code>mj-chart-chord-click</code> (value and "
                    "<code>reverseValue</code>); arcs emit <code>mj-chart-node-click</code> "
                    "(total, sent, received).</p>"
                ),
            ),
        ],
    ),

    ChartTypeDoc(
        type_key="flowchart",
        title="Flowchart",
        category="flow-and-process",
        summary="Process diagram with rect, diamond, and oval shapes and arrowheads.",
        description=(
            "Nodes have three shapes: rect (process, default), diamond (decision) and oval "
            "(start or end), sized from their wrapped label and coloured by kind (listed "
            "in the legend). A layered layout with cycle detection ranks the steps; loops "
            "(here the payment retry) are drawn dashed through a side channel. Edges are "
            "orthogonal connectors with optional label text. The diagram is scaled down to "
            "fit; without an orientation attribute it runs in the direction that draws it "
            "larger."
        ),
        data_shape=(
            "<pre><code>{\n"
            "  nodes: [{ id: string, label: string, shape?: 'rect' | 'diamond' | 'oval' }],\n"
            "  links: [{ source: string, target: string, label?: string }]\n"
            "}</code></pre>"
            "<ul>"
            "<li><code>shape</code>: rect (default), diamond or oval.</li>"
            "<li><code>links[].label</code>: text drawn on the edge (e.g. Yes / No).</li>"
            "</ul>"
        ),
        options=_FLOWCHART_OPTIONS,
        examples=[
            basic_example(_flowchart_example, "<p>Order handling with two decisions and a dashed retry loop.</p>"),
            gallery_example(
                "horizontal",
                "Left to right",
                "<p><code>orientation=\"horizontal\"</code> forces left-to-right ranks.</p>",
                chart_markup("flowchart", {"nodes": _FC_NODES, "links": _FC_LINKS},
                        label="Order handling", attrs={"orientation": "horizontal"},
                        style="height:300px", legend=True),
            ),
            gallery_example(
                "vertical",
                "Top to bottom",
                "<p>A CI pipeline with <code>orientation=\"vertical\"</code>; the fix loop runs "
                "back up the side.</p>",
                chart_markup("flowchart", {"nodes": _FC_LINEAR_NODES, "links": _FC_LINEAR_LINKS},
                        label="Continuous integration", attrs={"orientation": "vertical"},
                        style="height:460px", legend=True),
            ),
            events_example(
                "flowchart", {"nodes": _FC_NODES, "links": _FC_LINKS},
                ["mj-chart-node-click", "mj-chart-edge-click"], "[part=node]",
                enter="click:[part~=edge]", label="Order handling", style="height:300px",
                description=(
                    "<p>Steps emit <code>mj-chart-node-click</code> (id, label); edges are "
                    "clickable and emit <code>mj-chart-edge-click</code> (source, target, label).</p>"
                ),
            ),
        ],
    ),

    ChartTypeDoc(
        type_key="decision-flow",
        title="Decision Flow",
        category="flow-and-process",
        summary="Flowchart variant with fixed Yes / No branch sides for decision logic.",
        description=(
            "The flowchart's data and drawing with one difference: the branch labelled "
            "Yes (or True) always sits before the branch labelled No (or False), left of "
            "it top-to-bottom and above it left-to-right, so every decision reads the same "
            "way. Diamonds are the questions; branch labels are drawn where each branch "
            "leaves its diamond. Loops are drawn dashed through a side channel."
        ),
        data_shape=(
            "<pre><code>{\n"
            "  nodes: [{ id: string, label: string, shape?: 'rect' | 'diamond' | 'oval' }],\n"
            "  links: [{ source: string, target: string, label?: 'Yes' | 'No' | 'True' | 'False' | string }]\n"
            "}</code></pre>"
        ),
        options=_FLOWCHART_OPTIONS,
        examples=[
            basic_example(_decision_flow_example, "<p>Alert triage: Yes branches always come first.</p>"),
            gallery_example(
                "horizontal",
                "Left to right",
                "<p><code>orientation=\"horizontal\"</code>: Yes branches sit above No branches.</p>",
                chart_markup("decision-flow", {"nodes": _DF_NODES, "links": _DF_LINKS},
                        label="Alert triage", attrs={"orientation": "horizontal"},
                        style="height:300px", legend=True),
            ),
            gallery_example(
                "true-false",
                "True / False branches",
                "<p>The False links are listed first in the data, yet every True branch is "
                "placed first.</p>",
                chart_markup("decision-flow", {"nodes": _DF_BOOL_NODES, "links": _DF_BOOL_LINKS},
                        label="Cache lookup", attrs={"orientation": "vertical"},
                        style="height:420px", legend=True),
            ),
            events_example(
                "decision-flow", {"nodes": _DF_NODES, "links": _DF_LINKS},
                ["mj-chart-node-click", "mj-chart-edge-click"], "[part=node]",
                enter="click:[part~=edge]", label="Alert triage",
                description="<p>Same events as the flowchart.</p>",
            ),
        ],
    ),

    ChartTypeDoc(
        type_key="funnel",
        title="Funnel Chart",
        category="flow-and-process",
        summary="Trapezoid segments narrowing stage by stage to show conversion drop-off.",
        description=(
            "Each stage is a trapezoid whose wide edge is the stage value and narrow edge "
            "the next stage's value, on one scale relative to the largest stage. Stage "
            "names sit beside the shape, values inside it (or next to it when the stage is "
            "too narrow), and the signed change to the next stage is annotated between "
            "stages. mode pyramid stacks the stages from the base up; orientation "
            "horizontal runs them left to right. Stages without a number are left out; "
            "negative values are left out and raise mj-chart-error."
        ),
        data_shape=(
            _CATEGORY_SHAPE
            + "<ul>"
            "<li><code>categories</code>: stage names, in funnel order.</li>"
            "<li><code>series[0].values</code>: stage counts (non-negative).</li>"
            "</ul>"
        ),
        options=[
            AttributeDoc(name="mode", description="funnel: first stage on top; pyramid: first stage is the base.",
                         kind="enum", values=["funnel", "pyramid"], default="funnel"),
            orientation_option("vertical", "vertical: stages top to bottom; horizontal: left to right."),
        ],
        examples=[
            basic_example(_funnel_example, "<p>A marketing funnel with the drop between stages.</p>"),
            gallery_example(
                "pyramid",
                "Pyramid",
                "<p><code>mode=\"pyramid\"</code>: the first stage is the base.</p>",
                chart_markup("funnel", _FUNNEL_HIRING, label="Hiring pipeline", attrs={"mode": "pyramid"},
                        style="height:300px"),
            ),
            gallery_example(
                "horizontal",
                "Horizontal",
                "<p><code>orientation=\"horizontal\"</code>: stage names above the shape.</p>",
                chart_markup("funnel", _FUNNEL_HIRING, label="Hiring pipeline",
                        attrs={"orientation": "horizontal"}, style="height:220px"),
            ),
            gallery_example(
                "edge-data",
                "Missing and negative stages",
                "<p>Activated is <code>null</code> and Renewed negative: both are left out and "
                "<code>mj-chart-error</code> is logged.</p>",
                chart_markup("funnel", _FUNNEL_EDGE, label="Subscription funnel"),
            ),
            events_example(
                "funnel", _funnel_data, ["mj-chart-segment-click"], "[part=segment]",
                description="<p><code>mj-chart-segment-click</code> reports the stage, value and index.</p>",
            ),
        ],
    ),

    ChartTypeDoc(
        type_key="network",
        title="Network Graph",
        category="flow-and-process",
        summary="Force-directed node-link diagram for exploring graph topology.",
        description=(
            "A Fruchterman-Reingold force layout (deterministic start, cooled steps, "
            "overlap removal), cached per data object so resizing rescales instead of "
            "re-simulating. Node radius is square-root scaled from value (or size), node "
            "colour encodes group (listed in the legend) and link width encodes value; "
            "directed true adds arrowheads. Other layouts: arc, layered, bundled or static "
            "(fixed x / y). Nodes without an id and links to unknown nodes are skipped."
        ),
        data_shape=(
            "<pre><code>{\n"
            "  nodes: [{ id: string, label?: string, group?: string, value?: number,\n"
            "            order?: number, x?: number, y?: number }],\n"
            "  links: [{ source: string, target: string, value?: number, label?: string }],\n"
            "  directed?: boolean,\n"
            "  layout?: 'force' | 'arc' | 'layered' | 'bundled' | 'static'\n"
            "}</code></pre>"
            "<ul>"
            "<li><code>value</code> (alias <code>size</code>): node radius (sqrt scale).</li>"
            "<li><code>x</code> / <code>y</code>: positions for the static layout, fitted to "
            "the plot.</li>"
            "<li><code>directed</code>: arrowheads in the force layout.</li>"
            "</ul>"
        ),
        options=_network_options("network"),
        examples=[
            basic_example(_network_example, "<p>Nine services: colour is the group, size the value.</p>"),
            gallery_example(
                "layered",
                "Layered layout",
                "<p><code>layout=\"layered\"</code> ranks the same graph with arrowheads.</p>",
                chart_markup("network", {"nodes": _NET_NODES, "links": _NET_LINKS},
                        label="Service calls", attrs={"layout": "layered"}, legend=True),
            ),
            gallery_example(
                "static",
                "Fixed positions",
                "<p><code>layout=\"static\"</code> places nodes at their <code>x</code> / "
                "<code>y</code> (longitude / negated latitude here).</p>",
                chart_markup("network", _NET_STATIC, label="European network hubs",
                        attrs={"layout": "static"}, style="height:300px", legend=True),
            ),
            gallery_example(
                "directed",
                "Directed graph",
                "<p><code>directed: true</code> in the data adds arrowheads to the force layout.</p>",
                chart_markup("network", _NET_DIRECTED, label="Who reviews whose code", legend=True),
            ),
            events_example(
                "network", {"nodes": _NET_NODES, "links": _NET_LINKS},
                ["mj-chart-node-click", "mj-chart-edge-click"], "[part=node]",
                enter="click:[part=edge]", legend=True,
                description=(
                    "<p>Nodes emit <code>mj-chart-node-click</code> (id, label, group); links are "
                    "clickable and emit <code>mj-chart-edge-click</code> (source, target, value, "
                    "label).</p>"
                ),
            ),
        ],
    ),

    ChartTypeDoc(
        type_key="arc-diagram",
        title="Arc Diagram",
        category="flow-and-process",
        summary="Nodes on a single axis with edges drawn as arcs.",
        description=(
            "Places the nodes evenly along one axis, in nodes[].order when given, else in "
            "data order; horizontal by default, orientation vertical stands the axis up. "
            "Each link is a half-ellipse arc whose height grows with the distance it spans, "
            "scaled so the longest arc fits. Arcs and nodes are coloured by group. Useful "
            "for structural patterns in linear orderings."
        ),
        data_shape=(
            _GRAPH_SHAPE.replace("group?: string }", "group?: string, order?: number }")
            + "<ul><li><code>order</code>: position on the axis (default: data order).</li></ul>"
        ),
        options=_network_options("arc-diagram"),
        examples=[
            basic_example(_arc_diagram_example, "<p>The service graph on one axis.</p>"),
            gallery_example(
                "vertical",
                "Vertical axis",
                "<p><code>orientation=\"vertical\"</code>: arcs bulge to the side.</p>",
                chart_markup("arc-diagram", {"nodes": _NET_NODES, "links": _NET_LINKS},
                        label="Service calls", attrs={"orientation": "vertical"},
                        style="height:360px", legend=True),
            ),
            gallery_example(
                "ordered",
                "Ordered nodes",
                "<p><code>nodes[].order</code> puts the characters in order of appearance; "
                "links are shared scenes.</p>",
                chart_markup("arc-diagram", _ARC_ORDERED, label="Shared scenes", legend=True),
            ),
            events_example(
                "arc-diagram", {"nodes": _NET_NODES, "links": _NET_LINKS},
                ["mj-chart-node-click", "mj-chart-edge-click"], "[part=node]",
                enter="click:[part=arc-link]", legend=True,
                description="<p>Nodes emit <code>mj-chart-node-click</code>; arcs emit <code>mj-chart-edge-click</code>.</p>",
            ),
        ],
    ),

    ChartTypeDoc(
        type_key="node-link",
        title="Node-Link Diagram",
        category="flow-and-process",
        summary="Force-directed graph with explicit node and link data; synonym of network.",
        description=(
            "An alias of network: the same force-directed layout, drawing, group colours, "
            "data fields and layout options. Use whichever name reads better on the page."
        ),
        data_shape="<p>Same shape as <code>network</code>.</p>" + _GRAPH_SHAPE,
        options=_network_options("node-link"),
        examples=[
            basic_example(_node_link_example, "<p>The service graph with the force layout.</p>"),
            gallery_example(
                "directed",
                "Directed graph",
                "<p><code>directed: true</code> adds arrowheads.</p>",
                chart_markup("node-link", _NET_DIRECTED, label="Who reviews whose code", legend=True),
            ),
            gallery_example(
                "arc-layout",
                "Arc layout",
                "<p><code>layout=\"arc\"</code> draws the same data as an arc diagram.</p>",
                chart_markup("node-link", {"nodes": _NET_NODES, "links": _NET_LINKS},
                        label="Service calls", attrs={"layout": "arc"}, legend=True),
            ),
            events_example(
                "node-link", {"nodes": _NET_NODES, "links": _NET_LINKS},
                ["mj-chart-node-click", "mj-chart-edge-click"], "[part=node]",
                enter="click:[part=edge]", legend=True,
                description="<p>Same events as <code>network</code>.</p>",
            ),
        ],
    ),

    ChartTypeDoc(
        type_key="edge-bundling",
        title="Edge Bundling",
        category="flow-and-process",
        summary="Radial graph whose links are bundled along their node groups.",
        description=(
            "Nodes sit on a ring, grouped by group with a gap between groups. Each link is "
            "a curve routed through its groups' control points (hierarchical edge "
            "bundling), so links between the same two groups run together. tension (0 to "
            "1, default 0.85) sets the bundling strength; 0 draws straight chords."
        ),
        data_shape=(
            _GRAPH_SHAPE
            + "<ul><li><code>group</code>: the ring sector of the node.</li>"
            "<li><code>tension</code>: optional number at the root, used when the attribute "
            "is absent.</li></ul>"
        ),
        options=_network_options("edge-bundling"),
        examples=[
            basic_example(_edge_bundling_example, "<p>Service links bundled by group at tension 0.85.</p>"),
            gallery_example(
                "straight",
                "Tension 0",
                "<p><code>tension=\"0\"</code>: every link is a straight chord.</p>",
                chart_markup("edge-bundling", {"nodes": _NET_NODES, "links": _NET_LINKS},
                        label="Service calls", attrs={"tension": "0"}, legend=True),
            ),
            gallery_example(
                "tight",
                "Tension 1",
                "<p><code>tension=\"1\"</code> pulls the links fully into their bundles.</p>",
                chart_markup("edge-bundling", {"nodes": _ARC_ORDERED["nodes"], "links": _ARC_ORDERED["links"]},
                        label="Shared scenes by family", attrs={"tension": "1"}, legend=True),
            ),
            events_example(
                "edge-bundling", {"nodes": _NET_NODES, "links": _NET_LINKS},
                ["mj-chart-node-click", "mj-chart-edge-click"], "[part=node]",
                enter="click:[part=edge]", legend=True,
                description="<p>Nodes emit <code>mj-chart-node-click</code>; links <code>mj-chart-edge-click</code>.</p>",
            ),
        ],
    ),

    ChartTypeDoc(
        type_key="dependency-graph",
        title="Dependency Graph",
        category="flow-and-process",
        summary="Layered DAG layout (Sugiyama-style) with directed arrowheads.",
        description=(
            "A longest-path layered layout, left to right by default (orientation vertical "
            "for top to bottom), with barycentre ordering to reduce crossings and "
            "arrowheads on every edge. Cycles are detected: back-edges and self-links are "
            "drawn dashed instead of being ranked. Node colour encodes group. Suitable for "
            "module dependencies, build pipelines and similar graphs."
        ),
        data_shape=(
            "<pre><code>{\n"
            "  nodes: [{ id: string, label?: string, group?: string, value?: number }],\n"
            "  links: [{ source: string, target: string }]   // source depends on target\n"
            "}</code></pre>"
        ),
        options=_network_options("dependency-graph"),
        examples=[
            basic_example(_dep_graph_example, "<p>Front-end module dependencies, left to right.</p>"),
            gallery_example(
                "vertical",
                "Top to bottom",
                "<p><code>orientation=\"vertical\"</code> ranks the modules downward.</p>",
                chart_markup("dependency-graph", {"nodes": _dep_graph_nodes, "links": _dep_graph_links},
                        label="Module dependencies", attrs={"orientation": "vertical"},
                        style="height:360px", legend=True),
            ),
            gallery_example(
                "cycle",
                "Cycle and self-link",
                "<p>format depends back on validate (a cycle) and forms on itself: both are "
                "drawn dashed and left out of the ranking.</p>",
                chart_markup("dependency-graph", _DEP_CYCLE, label="Circular imports", legend=True),
            ),
            events_example(
                "dependency-graph", {"nodes": _dep_graph_nodes, "links": _dep_graph_links},
                ["mj-chart-node-click", "mj-chart-edge-click"], "[part=node]",
                enter="click:[part=edge]", legend=True,
                description="<p>Modules emit <code>mj-chart-node-click</code>; edges <code>mj-chart-edge-click</code>.</p>",
            ),
        ],
    ),
]
