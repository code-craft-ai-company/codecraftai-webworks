"""
    componentdoc.py

    Defines the ComponentDoc record used to document and test a single
    web component on the testcomponents site.
"""

import os


class ComponentDoc:
    """
        Documentation and test metadata for one mj-* web component.

        Each per-group catalog module builds a list of ComponentDoc
        instances; the catalog package aggregates them and the group
        blueprints render them into browsable, interactive pages.
    """

    def __init__(
        self,
        tag: str,
        title: str,
        group: str,
        summary: str,
        description: str,
        how_to_use: str,
        example: str,
        attributes: "list[tuple[str, str]] | None" = None,
        events: "list[tuple[str, str]] | None" = None,
    ):
        """
            Construct a ComponentDoc.

            :param tag: The custom element tag, e.g. ``mj-button``.
            :param title: Human-readable component name.
            :param group: The group key this component belongs to.
            :param summary: One-line summary used in listings.
            :param description: Paragraph describing what the component is
                and what it is used for.
            :param how_to_use: Guidance on how to use the component.
            :param example: An HTML snippet demonstrating the component;
                also the initial contents of the live playground editor.
            :param attributes: Optional list of (name, description) pairs.
            :param events: Optional list of (name, description) pairs.
        """

        self.tag = tag
        self.title = title
        self.group = group
        self.summary = summary
        self.description = description
        self.how_to_use = how_to_use
        self.example = example

        if attributes is not None:
            self.attributes = attributes
        else:
            self.attributes = []

        if events is not None:
            self.events = events
        else:
            self.events = []

        return

    @property
    def slug(self) -> str:
        """
            Return the URL slug for this component (its tag name).

            :returns: The tag string, used as the path segment.
        """

        value = self.tag
        return value
