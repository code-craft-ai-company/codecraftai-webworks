"""
    componentdoc.py

    Defines the ComponentDoc record used to document and test a single
    web component on the testcomponents site, and the helpers that
    normalize its reference tables.

    The related records are defined in their own modules and re-exported
    here so a catalog module can import everything from one place::

        from testcomponents.catalog.componentdoc import AttributeDoc
        from testcomponents.catalog.componentdoc import ComponentDoc
        from testcomponents.catalog.componentdoc import ComponentExample
"""

from ccai.errors.exceptions import SemanticError

from testcomponents.catalog.attributedoc import ATTRIBUTE_KINDS
from testcomponents.catalog.attributedoc import AttributeDoc
from testcomponents.catalog.componentexample import ComponentExample
from testcomponents.catalog.componentexample import build_gallery


__all__ = [
    "ATTRIBUTE_KINDS",
    "AttributeDoc",
    "ComponentDoc",
    "ComponentExample",
    "normalize_attributes",
    "normalize_pairs",
    "normalize_triples",
]


def normalize_pairs(owner: str, field: str, rows: "list | None") -> "list[tuple[str, str]]":
    """
        Validate a reference table given as ``(name, description)`` pairs.

        :param owner: The tag or chart type the table belongs to, for messages.
        :param field: The field name, for messages.
        :param rows: The rows as given (None means no rows).

        :returns: The rows as a new list of 2-tuples of strings.

        :raises SemanticError: When a row is not a pair of strings.
    """

    normalized = []
    if rows is None:
        return normalized

    for row in rows:
        valid = isinstance(row, (tuple, list)) and len(row) == 2
        if valid is True:
            name, description = row
            valid = isinstance(name, str) and isinstance(description, str)
        if valid is False:
            errmsg = "{}: every '{}' row must be a (name, description) tuple of strings, got {!r}.".format(
                owner, field, row)
            raise SemanticError(errmsg)
        normalized.append((name, description))

    return normalized


def normalize_triples(owner: str, field: str, rows: "list | None") -> "list[tuple[str, str, str]]":
    """
        Validate a reference table whose rows are ``(name, description)`` with
        an optional third string (an event's detail shape, a slot's sample markup).

        :param owner: The tag or chart type the table belongs to, for messages.
        :param field: The field name, for messages.
        :param rows: The rows as given (None means no rows).

        :returns: The rows as a new list of 3-tuples of strings ("" when the
            third element was not given).

        :raises SemanticError: When a row is not a 2- or 3-tuple of strings.
    """

    normalized = []
    if rows is None:
        return normalized

    for row in rows:
        valid = isinstance(row, (tuple, list)) and len(row) in (2, 3)
        if valid is True:
            if len(row) == 2:
                name, description = row
                extra = ""
            else:
                name, description, extra = row
            valid = isinstance(name, str) and isinstance(description, str) and isinstance(extra, str)
        if valid is False:
            errmsg = (
                "{}: every '{}' row must be a (name, description) or "
                "(name, description, extra) tuple of strings, got {!r}.".format(owner, field, row)
            )
            raise SemanticError(errmsg)
        normalized.append((name, description, extra))

    return normalized


def normalize_attributes(owner: str, rows: "list | None") -> "list[AttributeDoc]":
    """
        Accept AttributeDoc entries and legacy ``(name, description)`` tuples.

        :param owner: The tag or chart type the attributes belong to, for messages.
        :param rows: The entries as given (None means none).

        :returns: The entries as a list of AttributeDoc.

        :raises SemanticError: When an entry is neither form or a name repeats.
    """

    normalized = []
    if rows is None:
        return normalized

    seen = set()
    for row in rows:
        doc = AttributeDoc.from_entry(row)
        if doc.name in seen:
            errmsg = "{}: the attribute {!r} is listed twice.".format(owner, doc.name)
            raise SemanticError(errmsg)
        seen.add(doc.name)
        normalized.append(doc)

    return normalized


class ComponentDoc:
    """
        Documentation and test metadata for one mj-* web component.

        Each per-group catalog module builds a list of ComponentDoc
        instances; the catalog package aggregates them and the group
        blueprints render them into browsable, interactive pages.

        Every field after ``how_to_use`` is optional, so the original
        ``example`` / ``attributes`` / ``events`` form keeps working. The
        page shows only the panels and reference tables that have content.
    """

    def __init__(
        self,
        tag: str,
        title: str,
        group: str,
        summary: str,
        description: str,
        how_to_use: str,
        example: str = "",
        attributes: "list[AttributeDoc | tuple[str, str]] | None" = None,
        events: "list[tuple[str, str] | tuple[str, str, str]] | None" = None,
        examples: "list[ComponentExample] | None" = None,
        slots: "list[tuple[str, str] | tuple[str, str, str]] | None" = None,
        properties: "list[tuple[str, str]] | None" = None,
        methods: "list[tuple[str, str]] | None" = None,
        parts: "list[tuple[str, str]] | None" = None,
        css_properties: "list[tuple[str, str]] | None" = None,
    ):
        """
            Construct a ComponentDoc.

            :param tag: The custom element tag, e.g. ``mj-button``.
            :param title: Human-readable component name.
            :param group: The group key this component belongs to.
            :param summary: One-line summary used in listings (HTML allowed).
            :param description: Paragraph describing what the component is
                and what it is used for (an HTML fragment).
            :param how_to_use: Guidance on how to use the component (HTML).
            :param example: The single legacy example snippet. When ``examples``
                is empty it becomes the one gallery entry (key ``basic``). It may
                be left empty when ``examples`` is given.
            :param attributes: AttributeDoc entries, or ``(name, description)``
                tuples (read as kind ``string``).
            :param events: ``(name, description)`` or ``(name, description,
                detail)`` tuples; ``detail`` describes the event's detail shape,
                e.g. ``"{ value: string }"``.
            :param examples: The gallery, in display order. The first entry is
                the one the page opens with.
            :param slots: ``(name, description)`` or ``(name, description,
                sample_html)`` tuples. The default slot is named ``""``.
                ``sample_html`` is the content the slot inspector adds when the
                slot is switched on; without it a generic placeholder is used.
            :param properties: ``(name, description)`` tuples for JS properties.
            :param methods: ``(signature, description)`` tuples, e.g.
                ``("show(options)", "Opens the dialog.")``.
            :param parts: ``(part name, description)`` tuples for ``::part()``.
            :param css_properties: ``(--custom-property, description)`` tuples.

            :raises SemanticError: When a field has the wrong shape, two examples
                share a key, or there is no example at all.
        """

        self.tag = tag
        self.title = title
        self.group = group
        self.summary = summary
        self.description = description
        self.how_to_use = how_to_use
        self.example = example

        self.attributes = normalize_attributes(tag, attributes)
        self.events = normalize_triples(tag, "events", events)
        self.slots = normalize_triples(tag, "slots", slots)
        self.properties = normalize_pairs(tag, "properties", properties)
        self.methods = normalize_pairs(tag, "methods", methods)
        self.parts = normalize_pairs(tag, "parts", parts)
        self.css_properties = normalize_pairs(tag, "css_properties", css_properties)

        if examples is not None:
            self.examples = list(examples)
        else:
            self.examples = []

        # The gallery the page shows: the examples, or the legacy example.
        self.gallery = build_gallery(tag, self.examples, example)

        return

    @property
    def slug(self) -> str:
        """
            Return the URL slug for this component (its tag name).

            :returns: The tag string, used as the path segment.
        """

        value = self.tag
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
