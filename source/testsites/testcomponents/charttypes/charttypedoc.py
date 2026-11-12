"""
    charttypedoc.py

    Defines the ChartTypeDoc record describing one chart TYPE of the
    mj-* chart library. Unlike a component (one tag), a chart type is the
    <mj-chart> controller configured with a `type` attribute, so every
    chart type shares the `mj-chart` tag and is keyed by its type string.
"""

from testcomponents.catalog.componentdoc import AttributeDoc
from testcomponents.catalog.componentdoc import ComponentExample
from testcomponents.catalog.componentdoc import normalize_attributes
from testcomponents.catalog.componentdoc import normalize_triples
from testcomponents.catalog.componentexample import build_gallery


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
        example: str = "",
        description: str = "",
        data_shape: str = "",
        options: "list[AttributeDoc | tuple[str, str]] | None" = None,
        examples: "list[ComponentExample] | None" = None,
        events: "list[tuple[str, str] | tuple[str, str, str]] | None" = None,
    ):
        """
            Construct a ChartTypeDoc.

            :param type_key: The chart `type` value, e.g. ``bar``.
            :param title: Human-readable chart name.
            :param category: The chart category key.
            :param summary: One-line description used in the gallery (plain text).
            :param example: A complete HTML snippet -- an <mj-chart> element
                with a `type` attribute and inline JSON data -- used as the one
                gallery entry (key ``basic``) when ``examples`` is empty.
            :param description: Optional longer description, shown in the
                About section (plain text: entities are decoded, the text is
                escaped and `backticked` words become code; a blank line
                starts a new paragraph).
            :param data_shape: A short HTML fragment describing the JSON the
                renderer reads, e.g. ``<code>{categories: string[], series:
                [{name, values: number[]}]}</code>`` plus notes.
            :param options: The renderer option attributes of the chart type, as
                AttributeDoc entries (or ``(name, description)`` tuples). The
                controls panel sets them on the first <mj-chart> in the preview.
            :param examples: The gallery, in display order; each html holds an
                <mj-chart type="..."> element.
            :param events: The events the chart type emits, as ``(name,
                description)`` or ``(name, description, detail)`` tuples;
                ``detail`` describes the event's detail shape, e.g.
                ``"{ seriesIndex: number, index: number, value: number }"``.
                Shown as an events table like a component's.

            :raises SemanticError: When an option, event or example has the wrong
                shape, or there is no example at all.
        """

        self.type_key = type_key
        self.title = title
        self.category = category
        self.summary = summary
        self.example = example
        self.description = description
        self.data_shape = data_shape

        owner = "chart type {!r}".format(type_key)
        self.options = normalize_attributes(owner, options)
        self.events = normalize_triples(owner, "events", events)

        if examples is not None:
            self.examples = list(examples)
        else:
            self.examples = []

        # The gallery the page shows: the examples, or the legacy example.
        self.gallery = build_gallery(owner, self.examples, example)
        return

    @property
    def slug(self) -> str:
        """
            Return the URL slug for this chart type.

            :returns: The type key, used as the path segment.
        """

        value = self.type_key
        return value

    def example_for(self, key: "str | None") -> ComponentExample:
        """
            Resolve a gallery example by key, falling back to the first one.

            :param key: The requested example key, or None.

            :returns: The matching ComponentExample, else the first gallery entry.
        """

        found = self.gallery[0]
        if key is not None:
            for entry in self.gallery:
                if entry.key == key:
                    found = entry
                    break

        return found
