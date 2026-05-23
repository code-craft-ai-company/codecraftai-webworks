"""
    charttypedoc.py

    Defines the ChartTypeDoc record describing one chart TYPE of the
    mj-* chart library. Unlike a component (one tag), a chart type is the
    <mj-chart> controller configured with a `type` attribute, so every
    chart type shares the `mj-chart` tag and is keyed by its type string.
"""


class ChartTypeDoc:
    """
        Documentation and demo metadata for one <mj-chart> chart type.

        Per-category catalog modules build lists of ChartTypeDoc; the
        charttypes package aggregates them and the test site renders a
        gallery and an interactive playground page for each.
    """

    def __init__(
        self,
        type_key: str,
        title: str,
        category: str,
        summary: str,
        example: str,
        description: str = "",
    ):
        """
            Construct a ChartTypeDoc.

            :param type_key: The chart `type` value, e.g. ``bar``.
            :param title: Human-readable chart name.
            :param category: The chart category key.
            :param summary: One-line description used in the gallery.
            :param example: A complete HTML snippet -- an <mj-chart> element
                with a `type` attribute and inline JSON data -- used both as
                the live gallery tile and the playground editor contents.
            :param description: Optional longer description.
        """

        self.type_key = type_key
        self.title = title
        self.category = category
        self.summary = summary
        self.example = example
        self.description = description
        return

    @property
    def slug(self) -> str:
        """
            Return the URL slug for this chart type.

            :returns: The type key, used as the path segment.
        """

        value = self.type_key
        return value
