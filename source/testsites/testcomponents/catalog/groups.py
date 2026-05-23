"""
    groups.py

    Declares the ordered list of component groups for the testcomponents
    site. Each group is served by a dedicated blueprint and gets a section
    on the browse page.
"""


class ComponentGroup:
    """
        Metadata for one component group (a navigable section of the site).
    """

    def __init__(self, key: str, title: str, description: str):
        """
            Construct a ComponentGroup.

            :param key: Short url-safe group identifier.
            :param title: Human-readable group title.
            :param description: One-line description of the group.
        """

        self.key = key
        self.title = title
        self.description = description
        return


# The canonical ordered list of groups. The `key` is used in URLs as
# /components/<key> and /components/<key>/<tag>.
GROUP_ORDER = [
    ComponentGroup(
        key="selection",
        title="Selection & Pickers",
        description="Dropdowns, listboxes, comboboxes, and value pickers.",
    ),
    ComponentGroup(
        key="text",
        title="Text & Data Entry",
        description="Text fields, editors, sliders, and form-structure controls.",
    ),
    ComponentGroup(
        key="buttons",
        title="Buttons & Actions",
        description="Buttons and action triggers in all their variants.",
    ),
    ComponentGroup(
        key="navigation",
        title="Navigation",
        description="App bars, menus, tabs, breadcrumbs, and wayfinding.",
    ),
    ComponentGroup(
        key="layout",
        title="Layout & Containers",
        description="Cards, grids, docking, accordions, and structural surfaces.",
    ),
    ComponentGroup(
        key="feedback",
        title="Feedback & Status",
        description="Alerts, toasts, progress, badges, and tooltips.",
    ),
    ComponentGroup(
        key="overlays",
        title="Dialogs & Overlays",
        description="Modals, popovers, drawers, and command surfaces.",
    ),
    ComponentGroup(
        key="data",
        title="Tables, Lists & Data",
        description="Tables, data grids, virtualized lists, and boards.",
    ),
    ComponentGroup(
        key="media",
        title="Media & Visualization",
        description="Images, players, charts, maps, and diagrams.",
    ),
    ComponentGroup(
        key="productivity",
        title="Application & Productivity",
        description="App shells, toolbars, file browsers, and chat surfaces.",
    ),
    ComponentGroup(
        key="charts",
        title="Project & SCM Charts",
        description="Branch graphs, pipelines, Gantt, and planning charts.",
    ),
]


def group_by_key(key: str) -> "ComponentGroup | None":
    """
        Resolve a ComponentGroup by its key.

        :param key: The group key to look up.

        :returns: The matching ComponentGroup, or None if not found.
    """

    found = None
    for group in GROUP_ORDER:
        if group.key == key:
            found = group
            break

    return found
