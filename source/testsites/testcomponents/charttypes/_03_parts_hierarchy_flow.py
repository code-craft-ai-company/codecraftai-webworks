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

import json

from testcomponents.charttypes.charttypedoc import ChartTypeDoc


# ---------------------------------------------------------------------------
# Shared sample data helpers
# ---------------------------------------------------------------------------

def _json(obj):
    """
        Serialise obj to a compact, single-line JSON string.

        :param obj: Python object (dict / list / scalar).
        :returns: JSON string.
    """
    result = json.dumps(obj, separators=(",", ":"))
    return result


def _inline(obj):
    """
        Wrap a JSON-serialised object in an inline script tag.

        :param obj: Python object to serialise.
        :returns: HTML <script> element string.
    """
    result = f'<script type="application/json">{_json(obj)}</script>'
    return result


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
# Shared chord data (6 nodes / 9 links)
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
    {"source": "NA", "target": "AP", "value": 980},
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
    "name": "CEO",
    "role": "Alice Chen",
    "children": [
        {
            "name": "CTO",
            "role": "Bob Park",
            "children": [
                {"name": "VP Eng",  "role": "Carol Davis"},
                {"name": "VP Infra","role": "Dan Ellis"},
            ],
        },
        {
            "name": "CFO",
            "role": "Eve Martin",
            "children": [
                {"name": "Controller", "role": "Frank Wu"},
                {"name": "FP&A",       "role": "Grace Lee"},
            ],
        },
        {
            "name": "CMO",
            "role": "Hiro Tanaka",
            "children": [
                {"name": "Brand",   "role": "Iris Müller"},
                {"name": "Growth",  "role": "James Osei"},
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
    "name": "Loan Application",
    "children": [
        {
            "name": "Credit ≥ 700",
            "label": "Yes",
            "children": [
                {
                    "name": "Income ≥ 60k",
                    "label": "Yes",
                    "children": [
                        {"name": "Approve", "label": "Yes"},
                        {"name": "Review",  "label": "No"},
                    ],
                },
                {"name": "Decline", "label": "No"},
            ],
        },
        {
            "name": "Collateral?",
            "label": "No",
            "children": [
                {"name": "Manual Review", "label": "Yes"},
                {"name": "Decline",       "label": "No"},
            ],
        },
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
    '<mj-chart type="donut" inner-radius="0.55" style="height:260px">'
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
    + "</mj-chart>"
)

_mosaic_data = {
    "categories": ["First", "Second", "Third"],
    "series": [
        {"name": "Survived", "values": [203, 118, 178]},
        {"name": "Perished", "values": [122, 167, 528]},
    ],
}

_mosaic_example = (
    '<mj-chart type="mosaic" style="height:260px">'
    + _inline(_mosaic_data)
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
    + "</mj-chart>"
)


# ===========================================================================
# HIERARCHICAL — hierlayout.js (data shape: raw.root nested tree)
# ===========================================================================

_hier_inline = _inline({"root": _HIER_ROOT})

_treemap_example = (
    '<mj-chart type="treemap" layout="treemap" style="height:260px">'
    + _hier_inline
    + "</mj-chart>"
)

_sunburst_example = (
    '<mj-chart type="sunburst" layout="sunburst" style="height:260px">'
    + _hier_inline
    + "</mj-chart>"
)

_icicle_example = (
    '<mj-chart type="icicle" layout="icicle" style="height:260px">'
    + _hier_inline
    + "</mj-chart>"
)

_circle_pack_example = (
    '<mj-chart type="circle-pack" layout="circle-pack" style="height:260px">'
    + _hier_inline
    + "</mj-chart>"
)


# ===========================================================================
# HIERARCHICAL — tree.js (data shape: raw.root nested tree)
# ===========================================================================

_tree_inline = _inline({"root": _TREE_ROOT})

_tree_example = (
    '<mj-chart type="tree" mode="tree" style="height:260px">'
    + _tree_inline
    + "</mj-chart>"
)

_dendrogram_data = {
    "root": {
        "name": "All Species",
        "value": 1.0,
        "children": [
            {
                "name": "Mammals",
                "value": 0.85,
                "children": [
                    {
                        "name": "Primates",
                        "value": 0.55,
                        "children": [
                            {"name": "Human",       "value": 0.0},
                            {"name": "Chimpanzee",  "value": 0.06},
                        ],
                    },
                    {
                        "name": "Rodents",
                        "value": 0.70,
                        "children": [
                            {"name": "Mouse",  "value": 0.0},
                            {"name": "Rat",    "value": 0.04},
                            {"name": "Rabbit", "value": 0.15},
                        ],
                    },
                ],
            },
            {
                "name": "Fish",
                "value": 0.92,
                "children": [
                    {"name": "Salmon",  "value": 0.0},
                    {"name": "Zebrafish","value": 0.12},
                    {"name": "Cod",     "value": 0.20},
                ],
            },
        ],
    }
}

_dendrogram_example = (
    '<mj-chart type="dendrogram" mode="dendrogram" style="height:260px">'
    + _inline(_dendrogram_data)
    + "</mj-chart>"
)

_org_example = (
    '<mj-chart type="org-chart" mode="org-chart" style="height:260px">'
    + _inline({"root": _ORG_ROOT})
    + "</mj-chart>"
)

_mindmap_example = (
    '<mj-chart type="mindmap" mode="mindmap" style="height:260px">'
    + _inline({"root": _MINDMAP_ROOT})
    + "</mj-chart>"
)

_decision_tree_example = (
    '<mj-chart type="decision-tree" mode="decision-tree" style="height:260px">'
    + _inline({"root": _DT_ROOT})
    + "</mj-chart>"
)


# ===========================================================================
# FLOW & PROCESS
# ===========================================================================

_sankey_example = (
    '<mj-chart type="sankey" style="height:260px">'
    + _inline({"nodes": _FLOW_NODES, "links": _FLOW_LINKS})
    + "</mj-chart>"
)

_alluvial_example = (
    '<mj-chart type="alluvial" mode="alluvial" style="height:260px">'
    + _inline({"nodes": _ALLUVIAL_NODES, "links": _ALLUVIAL_LINKS})
    + "</mj-chart>"
)

_chord_example = (
    '<mj-chart type="chord" style="height:260px">'
    + _inline({"nodes": _CHORD_NODES, "links": _CHORD_LINKS})
    + "</mj-chart>"
)

_flowchart_example = (
    '<mj-chart type="flowchart" style="height:260px">'
    + _inline({"nodes": _FC_NODES, "links": _FC_LINKS})
    + "</mj-chart>"
)

_decision_flow_example = (
    '<mj-chart type="decision-flow" style="height:260px">'
    + _inline({"nodes": _DF_NODES, "links": _DF_LINKS})
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
    + "</mj-chart>"
)

_arc_diagram_example = (
    '<mj-chart type="arc-diagram" layout="arc" style="height:260px">'
    + _inline({"nodes": _NET_NODES, "links": _NET_LINKS})
    + "</mj-chart>"
)

_node_link_example = (
    '<mj-chart type="node-link" style="height:260px">'
    + _inline({"nodes": _NET_NODES, "links": _NET_LINKS})
    + "</mj-chart>"
)

_edge_bundling_example = (
    '<mj-chart type="edge-bundling" style="height:260px">'
    + _inline({"nodes": _NET_NODES, "links": _NET_LINKS})
    + "</mj-chart>"
)

_dep_graph_nodes = [
    {"id": "app",      "label": "app",      "value": 5},
    {"id": "router",   "label": "router",   "value": 4},
    {"id": "store",    "label": "store",    "value": 4},
    {"id": "auth",     "label": "auth",     "value": 3},
    {"id": "api",      "label": "api",      "value": 4},
    {"id": "utils",    "label": "utils",    "value": 2},
    {"id": "logger",   "label": "logger",   "value": 2},
    {"id": "types",    "label": "types",    "value": 1},
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
    '<mj-chart type="dependency-graph" layout="layered" style="height:260px">'
    + _inline({"nodes": _dep_graph_nodes, "links": _dep_graph_links})
    + "</mj-chart>"
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
        example=_pie_example,
        description=(
            "Renders a circular chart divided into wedges proportional to their "
            "values. Up to 12 categories are drawn; any excess are collapsed into "
            "an 'Other' slice. Labels appear inside wide slices and as leader "
            "lines for narrow ones."
        ),
    ),

    ChartTypeDoc(
        type_key="donut",
        title="Donut Chart",
        category="part-to-whole",
        summary="Like a pie chart but with a hollow centre that can display a label.",
        example=_donut_example,
        description=(
            "Identical to the pie renderer but with the `inner-radius` attribute "
            "set to a fraction between 0 and 0.95, which cuts a hole in the centre. "
            "An optional `center-label` in `meta` is rendered inside the hole."
        ),
    ),

    ChartTypeDoc(
        type_key="waffle",
        title="Waffle Chart",
        category="part-to-whole",
        summary="Unit grid where each cell represents a fraction of the whole.",
        example=_waffle_example,
        description=(
            "Renders a rectangular grid (default 10×10) where each cell is "
            "coloured by category. Category values are proportionally assigned "
            "to cells using the largest-remainder method, so the total always "
            "fills the grid exactly."
        ),
    ),

    ChartTypeDoc(
        type_key="marimekko",
        title="Marimekko Chart",
        category="part-to-whole",
        summary=(
            "Variable-width stacked bar where column widths encode column totals "
            "and segment heights encode conditional shares."
        ),
        example=_marimekko_example,
        description=(
            "Also called a Mekko chart. Column widths are proportional to each "
            "column's share of the grand total. Within each column, segment "
            "heights are normalised to 100%, encoding the row-series breakdown. "
            "Multiple series are required."
        ),
    ),

    ChartTypeDoc(
        type_key="mosaic",
        title="Mosaic Plot",
        category="part-to-whole",
        summary="Contingency-table visualisation where tile area encodes cell frequency.",
        example=_mosaic_example,
        description=(
            "A spine / mosaic plot that encodes the joint distribution of two "
            "categorical variables. Column widths are proportional to marginal "
            "column totals; segment heights within each column reflect conditional "
            "frequencies. Useful for identifying departures from independence."
        ),
    ),

    ChartTypeDoc(
        type_key="waterfall",
        title="Waterfall Chart",
        category="part-to-whole",
        summary="Cascade of running-total deltas with start, subtotal, and total bars.",
        example=_waterfall_example,
        description=(
            "Shows how an initial value is affected by a series of positive or "
            "negative increments. Series values carry a `kinds` array: 'start', "
            "'delta', 'subtotal', or 'total'. Positive deltas are green, negative "
            "red, and subtotals/totals neutral. Connector lines link floating bars."
        ),
    ),

    ChartTypeDoc(
        type_key="pareto",
        title="Pareto Chart",
        category="part-to-whole",
        summary="Sorted bars plus a cumulative-percentage line, with an 80% reference.",
        example=_pareto_example,
        description=(
            "Categories are automatically sorted descending by value. A red "
            "cumulative-percentage line is overlaid on a right Y axis. A dashed "
            "80% reference line helps identify the vital few contributors. "
            "Set `meta[\"pareto-line\"]` to false to hide the reference line."
        ),
    ),

    # -----------------------------------------------------------------------
    # Hierarchical — hierlayout.js
    # -----------------------------------------------------------------------

    ChartTypeDoc(
        type_key="treemap",
        title="Treemap",
        category="hierarchical",
        summary="Squarified space-filling rectangles sized by subtree value.",
        example=_treemap_example,
        description=(
            "Uses the Bruls squarified treemap algorithm to partition a rectangle "
            "into tiles whose areas are proportional to node totals. The data must "
            "supply `raw.root` — a nested tree where leaves carry `value` and "
            "internal nodes optionally carry their own `value` (otherwise the "
            "subtree sum is used)."
        ),
    ),

    ChartTypeDoc(
        type_key="sunburst",
        title="Sunburst",
        category="hierarchical",
        summary="Radial partition chart: concentric rings per tree depth.",
        example=_sunburst_example,
        description=(
            "Each depth level occupies one ring; arc spans are proportional to "
            "subtree totals. Uses the same `raw.root` tree shape as the treemap. "
            "Activated by `layout='sunburst'` (or `type='sunburst'`)."
        ),
    ),

    ChartTypeDoc(
        type_key="icicle",
        title="Icicle Chart",
        category="hierarchical",
        summary="Rectangular partition rows, root at top, leaves at bottom.",
        example=_icicle_example,
        description=(
            "Partitions the plot area into horizontal bands per depth level. "
            "Within each band, child widths are proportional to their subtree "
            "totals relative to the parent. Horizontal orientation ('flame graph') "
            "is available via the `orientation` attribute."
        ),
    ),

    ChartTypeDoc(
        type_key="circle-pack",
        title="Circle Pack",
        category="hierarchical",
        summary="Packed circles whose areas are proportional to leaf values.",
        example=_circle_pack_example,
        description=(
            "Leaf radii are computed via a sqrt scale so area encodes value. "
            "Internal nodes are drawn as enclosing circles with lower opacity. "
            "The packing uses a front-chain (Wang-Bhatt) heuristic. "
            "Same `raw.root` tree shape as treemap / sunburst / icicle."
        ),
    ),

    # -----------------------------------------------------------------------
    # Hierarchical — tree.js
    # -----------------------------------------------------------------------

    ChartTypeDoc(
        type_key="tree",
        title="Tree",
        category="hierarchical",
        summary="Tidy node-link tree layout (Reingold-Tilford).",
        example=_tree_example,
        description=(
            "Renders a standard tidy tree with leaves evenly spaced along one "
            "axis and depth mapped to the other. Edges are drawn as cubic Bézier "
            "or elbow connectors (set via `edge-style`). "
            "Data shape: `raw.root` nested tree; nodes may carry `value`."
        ),
    ),

    ChartTypeDoc(
        type_key="dendrogram",
        title="Dendrogram",
        category="hierarchical",
        summary="Hierarchical clustering tree where branch height encodes merge distance.",
        example=_dendrogram_example,
        description=(
            "Leaf nodes are placed equidistantly on one axis. Internal node "
            "positions on the distance axis are derived from their `value` "
            "property (merge distance / linkage height). Uses elbow connectors "
            "and activates via `mode='dendrogram'`."
        ),
    ),

    ChartTypeDoc(
        type_key="org-chart",
        title="Org Chart",
        category="hierarchical",
        summary="Rectangular node cards with name and role lines.",
        example=_org_example,
        description=(
            "A tidy tree rendered with wider card nodes. Each node may carry "
            "`name` (bold) and `role` (muted sub-label). Card dimensions are "
            "fixed at 100×40 px; depth and leaf spacing auto-adjust to fit. "
            "Activated via `mode='org-chart'`."
        ),
    ),

    ChartTypeDoc(
        type_key="mindmap",
        title="Mind Map",
        category="hierarchical",
        summary="Radial layout emanating from a central root with branch-coloured connectors.",
        example=_mindmap_example,
        description=(
            "Root is placed at the centre; first-level children are distributed "
            "evenly around the full circle; deeper nodes are constrained to their "
            "parent's half-plane sector. Branch colours are inherited from the "
            "first-level ancestor. Activated via `mode='mindmap'`."
        ),
    ),

    ChartTypeDoc(
        type_key="decision-tree",
        title="Decision Tree",
        category="hierarchical",
        summary="Left-to-right tidy tree with Yes / No (or custom) labels on edges.",
        example=_decision_tree_example,
        description=(
            "A tidy tree rendered horizontally with edge labels taken from each "
            "node's `label` field (falls back to 'Yes' for the first child, 'No' "
            "for the second). Activated via `mode='decision-tree'`. Orientation "
            "defaults to horizontal."
        ),
    ),

    # -----------------------------------------------------------------------
    # Flow & Process
    # -----------------------------------------------------------------------

    ChartTypeDoc(
        type_key="sankey",
        title="Sankey Diagram",
        category="flow-and-process",
        summary="Flow ribbons whose widths encode transfer quantities between nodes.",
        example=_sankey_example,
        description=(
            "Node ranks are assigned via BFS from source nodes (those with no "
            "incoming links). Nodes are drawn as vertical bars within each rank "
            "column; cubic-Bézier ribbons connect them, with stroke-width "
            "proportional to link value. Data shape: `raw.nodes` + `raw.links`."
        ),
    ),

    ChartTypeDoc(
        type_key="alluvial",
        title="Alluvial Diagram",
        category="flow-and-process",
        summary="Sankey variant where column positions come from a node `group` field.",
        example=_alluvial_example,
        description=(
            "Same ribbon layout as the sankey renderer but column ranks are "
            "derived from each node's `group` property rather than link topology, "
            "making it ideal for showing how categorical distributions shift across "
            "survey waves or user-journey stages. Activated via `mode='alluvial'`."
        ),
    ),

    ChartTypeDoc(
        type_key="chord",
        title="Chord Diagram",
        category="flow-and-process",
        summary="Circular arc segments connected by ribbons proportional to flow values.",
        example=_chord_example,
        description=(
            "Each node occupies an arc on a ring proportional to its total flow. "
            "Chord ribbons connect pairs of nodes; the renderer symmetrises "
            "directional links automatically. Labels appear outside the ring. "
            "Data shape: `raw.nodes` + `raw.links` (directed or undirected)."
        ),
    ),

    ChartTypeDoc(
        type_key="flowchart",
        title="Flowchart",
        category="flow-and-process",
        summary="Process diagram with rect, diamond, and oval shapes and arrowheads.",
        example=_flowchart_example,
        description=(
            "Nodes support three `shape` values: 'rect' (default), 'diamond' "
            "(decision), and 'oval' (start / end). Ranks are assigned via BFS "
            "with DFS cycle detection; back-edges are highlighted in amber. "
            "Edges are orthogonal elbow connectors with optional `label` text."
        ),
    ),

    ChartTypeDoc(
        type_key="decision-flow",
        title="Decision Flow",
        category="flow-and-process",
        summary="Flowchart variant optimised for binary decision trees.",
        example=_decision_flow_example,
        description=(
            "Uses the same renderer as `flowchart` but is semantically intended "
            "for branching decision logic. Diamond nodes encode branch questions; "
            "edge `label` text (e.g. 'Yes' / 'No') is rendered mid-edge. "
            "Back-edges (cycles) are drawn in amber for quick identification."
        ),
    ),

    ChartTypeDoc(
        type_key="funnel",
        title="Funnel Chart",
        category="flow-and-process",
        summary="Trapezoid segments narrowing stage by stage to show conversion drop-off.",
        example=_funnel_example,
        description=(
            "Each stage is a trapezoid whose top width encodes the stage value "
            "and bottom width encodes the next stage value. Drop-off percentages "
            "are annotated between stages. Uses the standard `categories` + "
            "`series[0].values` model envelope; no `raw` object is needed."
        ),
    ),

    ChartTypeDoc(
        type_key="network",
        title="Network Graph",
        category="flow-and-process",
        summary="Force-directed node-link diagram for exploring graph topology.",
        example=_network_example,
        description=(
            "Iterative spring-repulsion layout (180 iterations). Node radii are "
            "sqrt-scaled from optional `value` fields. Node colour is keyed by "
            "optional `group`. Data shape: `raw.nodes` + `raw.links`. "
            "Override layout with `layout='arc'` or `layout='layered'`."
        ),
    ),

    ChartTypeDoc(
        type_key="arc-diagram",
        title="Arc Diagram",
        category="flow-and-process",
        summary="Nodes on a single axis with edges drawn as semicircular arcs.",
        example=_arc_diagram_example,
        description=(
            "Positions all nodes evenly along the horizontal axis (or vertical "
            "if `orientation='vertical'`). Connections are rendered as "
            "semi-circular arcs above the axis. Useful for highlighting "
            "structural patterns in linear orderings. Activated via `layout='arc'`."
        ),
    ),

    ChartTypeDoc(
        type_key="node-link",
        title="Node-Link Diagram",
        category="flow-and-process",
        summary="Force-directed graph with explicit node and link data — synonym of network.",
        example=_node_link_example,
        description=(
            "Registered as a separate type key but uses the same force-directed "
            "layout and rendering pipeline as the `network` type. Useful when the "
            "semantic intent is to emphasise the graph-as-diagram rather than the "
            "network-topology interpretation."
        ),
    ),

    ChartTypeDoc(
        type_key="edge-bundling",
        title="Edge Bundling",
        category="flow-and-process",
        summary="Force-directed graph that visually clusters structurally similar edges.",
        example=_edge_bundling_example,
        description=(
            "Currently rendered with the same force-directed layout as `network`. "
            "The type key signals intent to group and visually bundle parallel "
            "edges in a future rendering pass. Data shape: `raw.nodes` + `raw.links`."
        ),
    ),

    ChartTypeDoc(
        type_key="dependency-graph",
        title="Dependency Graph",
        category="flow-and-process",
        summary="Layered DAG layout (Sugiyama-style) with directed arrowheads.",
        example=_dep_graph_example,
        description=(
            "Uses a BFS-rank Sugiyama layered layout by default (`layout='layered'`). "
            "Arrowheads are drawn on all edges to show direction. Suitable for "
            "module dependency trees, build pipelines, and similar DAG structures. "
            "Data shape: `raw.nodes` + `raw.links`."
        ),
    ),
]
