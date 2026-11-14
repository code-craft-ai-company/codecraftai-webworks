"""
    charttypes

    Aggregates the per-category chart-type catalog modules into a single
    queryable catalog used by the test site to render the chart gallery
    and the per-type playground pages.

    Each per-category module exposes a module-level ``CHART_TYPES`` list of
    ChartTypeDoc instances. The coordinated chart PART components (title,
    legend, data table) are documented in :mod:`chartparts` and served on
    their own pages.
"""

from testcomponents.catalog.componentdoc import ComponentDoc
from testcomponents.charttypes.charttypedoc import ChartTypeDoc
from testcomponents.charttypes.chartparts import CHART_PARTS

from testcomponents.charttypes import _01_comparison_trend as _01
from testcomponents.charttypes import _02_distribution_relationship as _02
from testcomponents.charttypes import _03_parts_hierarchy_flow as _03
from testcomponents.charttypes import _04_stat_finance_project as _04
from testcomponents.charttypes import _05_scientific_geographic as _05
from testcomponents.charttypes import _06_ux_text_tables_advanced as _06


CHART_CATEGORIES = [
    ("comparison",    "Comparison",                  "#2563eb"),
    ("trend",         "Trend & Time-Series",         "#0891b2"),
    ("distribution",  "Distribution",                "#ca8a04"),
    ("relationship",  "Relationship & Correlation",  "#16a34a"),
    ("part-to-whole", "Part-to-Whole",               "#7c3aed"),
    ("ranking",       "Ranking",                     "#0d9488"),
    ("hierarchical",  "Hierarchical",                "#4f46e5"),
    ("flow",          "Flow & Process",              "#db2777"),
    ("statistical",   "Statistical & Analytical",    "#3949c4"),
    ("financial",     "Financial",                   "#dc2626"),
    ("project",       "Project & Schedule",          "#ea580c"),
    ("scientific",    "Scientific & Technical",      "#0d9488"),
    ("geographic",    "Geographic & Map",            "#15803d"),
    ("ux",            "UX, Product & Business",      "#7c3aed"),
    ("text",          "Text & Categorical",          "#0891b2"),
    ("tables",        "Tables with Visual Encoding", "#6b7280"),
    ("advanced",      "Less Common & Advanced",      "#9333ea"),
]


_CATEGORY_ALIASES = {
    "DISTRIBUTION":           "distribution",
    "RELATIONSHIP":           "relationship",
    "flow-and-process":       "flow",
    "ux-product-business":    "ux",
    "text-categorical":       "text",
    "tables-visual-encoding": "tables",
    "PART-TO-WHOLE":          "part-to-whole",
    "HIERARCHICAL":           "hierarchical",
    "FLOW":                   "flow",
    "STATISTICAL":            "statistical",
    "FINANCIAL":              "financial",
    "PROJECT":                "project",
    "SCIENTIFIC":             "scientific",
    "GEOGRAPHIC":             "geographic",
    "UX":                     "ux",
    "TEXT":                   "text",
    "TABLES":                 "tables",
    "ADVANCED":               "advanced",
    "COMPARISON":             "comparison",
    "TREND":                  "trend",
    "less-common":            "advanced",
}


def _normalize(doc: ChartTypeDoc) -> ChartTypeDoc:
    """
        Normalize a chart type's category key onto the canonical set.

        :param doc: A ChartTypeDoc.

        :returns: The same doc with category remapped if needed.
    """

    canonical = _CATEGORY_ALIASES.get(doc.category)
    if canonical is not None:
        doc.category = canonical
    return doc


def _collect() -> "list[ChartTypeDoc]":
    """
        Concatenate the per-category CHART_TYPES lists into one catalog.

        :returns: A list of every ChartTypeDoc.
    """

    catalog = []
    seen = set()
    for module in [_01, _02, _03, _04, _05, _06]:
        for doc in module.CHART_TYPES:
            normalized = _normalize(doc)
            if normalized.type_key in seen:
                continue
            seen.add(normalized.type_key)
            catalog.append(normalized)
    return catalog


CHART_TYPE_CATALOG = _collect()

BY_TYPE = { doc.type_key: doc for doc in CHART_TYPE_CATALOG }


def chart_types_by_category() -> "dict[str, list[ChartTypeDoc]]":
    """
        Group the catalog by category key.

        :returns: A dict from category key to list of ChartTypeDoc.
    """

    grouped = {}
    for category_key, _title, _accent in CHART_CATEGORIES:
        grouped[category_key] = []

    for doc in CHART_TYPE_CATALOG:
        bucket = grouped.get(doc.category)
        if bucket is None:
            grouped[doc.category] = [doc]
        else:
            bucket.append(doc)

    return grouped


def chart_type_count() -> int:
    """
        Return the total number of catalogued chart types.

        :returns: The integer count.
    """

    count = len(CHART_TYPE_CATALOG)
    return count


def chart_type_for(type_key: str) -> "ChartTypeDoc | None":
    """
        Resolve a ChartTypeDoc by its type key.

        :param type_key: The chart type key.

        :returns: The ChartTypeDoc, or None when unknown.
    """

    doc = BY_TYPE.get(type_key)
    return doc


def chart_type_neighbours(type_key: str) -> "tuple[ChartTypeDoc | None, ChartTypeDoc | None]":
    """
        Return the chart types before and after one in the gallery order
        (category order, then catalog order within a category).

        :param type_key: The chart type key.

        :returns: (previous, next); either is None at the ends or when unknown.
    """

    ordered = []
    grouped = chart_types_by_category()
    for category_key in grouped:
        for doc in grouped[category_key]:
            ordered.append(doc)

    previous_doc = None
    next_doc = None
    for index, doc in enumerate(ordered):
        if doc.type_key == type_key:
            if index > 0:
                previous_doc = ordered[index - 1]
            if index + 1 < len(ordered):
                next_doc = ordered[index + 1]
            break

    return previous_doc, next_doc


def chart_part_for(tag: str) -> "ComponentDoc | None":
    """
        Resolve a chart part doc by its tag.

        :param tag: The part tag, e.g. ``mj-chart-legend``.

        :returns: The ComponentDoc, or None when unknown.
    """

    found = None
    for doc in CHART_PARTS:
        if doc.tag == tag:
            found = doc
            break

    return found


def chart_part_count() -> int:
    """
        Return the number of documented chart part components.

        :returns: The integer count.
    """

    count = len(CHART_PARTS)
    return count
