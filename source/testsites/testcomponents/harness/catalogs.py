"""
    .. module:: testcomponents.harness.catalogs
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Catalog views the site suite iterates over.

    The site documents every component and chart type from its catalogs; the tests
    that sweep "every component" read the same catalogs so the two cannot drift.
"""

import re

from typing import List, Tuple

from testcomponents.catalog import CATALOG
from testcomponents.catalog.groups import GROUP_ORDER
from testcomponents.charttypes import CHART_TYPE_CATALOG


# A representative sample of chart types for the deeper render check; the full
# catalog is covered by the page-load sweep.
SAMPLE_CHART_TYPES = [
    "bar", "line", "area", "pie", "donut", "scatter", "bubble",
    "sankey", "treemap", "sunburst", "histogram", "boxplot",
    "heatmap", "choropleth", "gantt", "timeline", "polar",
    "radar", "ohlc", "candlestick", "gauge", "kpi", "funnel",
    "network", "calendar-heatmap", "sparkline", "step",
]

_NON_IDENTIFIER = re.compile(r"[^0-9a-zA-Z_]+")


def all_components() -> List[Tuple[str, str, str]]:
    """
        Return every catalogued component as (group_key, tag, title).

        :returns: A list of (group, tag, title) tuples in catalog order.
    """

    entries = []
    for group_key in CATALOG:
        for doc in CATALOG[group_key]:
            entries.append((group_key, doc.tag, doc.title))

    return entries


def all_groups() -> List[Tuple[str, str]]:
    """
        Return every component group as (group_key, title).

        :returns: A list of (group_key, title) tuples in display order.
    """

    groups = []
    for group in GROUP_ORDER:
        groups.append((group.key, group.title))

    return groups


def all_chart_types() -> List[Tuple[str, str]]:
    """
        Return every catalogued chart type as (type_key, title).

        :returns: A list of (type_key, title) tuples in catalog order.
    """

    entries = []
    for doc in CHART_TYPE_CATALOG:
        entries.append((doc.type_key, doc.title))

    return entries


def identifier_for(*parts: str) -> str:
    """
        Turn catalog keys such as ``"buttons"`` and ``"mj-button"`` into a fragment
        usable in a Python function name, e.g. ``buttons_mj_button``.

        :param parts: The key fragments to join.

        :returns: The joined, identifier-safe fragment.
    """

    cleaned = [_NON_IDENTIFIER.sub("_", part).strip("_") for part in parts]
    identifier = "_".join(cleaned)
    return identifier
