"""
    catalog

    Aggregates the per-group component documentation modules into a single
    queryable catalog used by the blueprints to render pages.

    Each group module (selection.py, text.py, ...) exposes a module-level
    ``COMPONENTS`` list of ComponentDoc instances.
"""

from testcomponents.catalog.componentdoc import ComponentDoc
from testcomponents.catalog.groups import GROUP_ORDER
from testcomponents.catalog.groups import group_by_key

from testcomponents.catalog import selection
from testcomponents.catalog import text
from testcomponents.catalog import buttons
from testcomponents.catalog import navigation
from testcomponents.catalog import layout
from testcomponents.catalog import feedback
from testcomponents.catalog import overlays
from testcomponents.catalog import data
from testcomponents.catalog import media
from testcomponents.catalog import productivity
from testcomponents.catalog import charts


# Map of group key -> the group module that supplies its COMPONENTS list.
_GROUP_MODULES = {
    "selection": selection,
    "text": text,
    "buttons": buttons,
    "navigation": navigation,
    "layout": layout,
    "feedback": feedback,
    "overlays": overlays,
    "data": data,
    "media": media,
    "productivity": productivity,
    "charts": charts,
}


def _build_catalog() -> "dict[str, list[ComponentDoc]]":
    """
        Build the catalog mapping of group key -> list of ComponentDoc.

        :returns: Dictionary keyed by group with component lists as values.
    """

    catalog = {}
    for group in GROUP_ORDER:
        module = _GROUP_MODULES[group.key]
        components = list(module.COMPONENTS)
        components.sort(key=lambda doc: doc.title.lower())
        catalog[group.key] = components

    return catalog


def _build_tag_index(
    catalog: "dict[str, list[ComponentDoc]]",
) -> "dict[str, ComponentDoc]":
    """
        Build a flat index of component tag -> ComponentDoc.

        :param catalog: The group-keyed catalog dictionary.

        :returns: Dictionary keyed by component tag.
    """

    index = {}
    for group_key in catalog:
        for doc in catalog[group_key]:
            index[doc.tag] = doc

    return index


CATALOG = _build_catalog()

BY_TAG = _build_tag_index(CATALOG)


def group_components(group_key: str) -> "list[ComponentDoc]":
    """
        Return the components belonging to a group.

        :param group_key: The group key to look up.

        :returns: The list of ComponentDoc for the group (empty if unknown).
    """

    components = CATALOG.get(group_key, [])
    return components


def component_for(group_key: str, tag: str) -> "ComponentDoc | None":
    """
        Resolve a ComponentDoc within a group by tag.

        :param group_key: The group key the component must belong to.
        :param tag: The component tag to resolve.

        :returns: The matching ComponentDoc, or None when not found.
    """

    doc = BY_TAG.get(tag)
    if doc is None:
        return None

    if doc.group != group_key:
        return None

    return doc


def total_component_count() -> int:
    """
        Return the total number of catalogued components.

        :returns: The integer count of all components across all groups.
    """

    count = len(BY_TAG)
    return count
