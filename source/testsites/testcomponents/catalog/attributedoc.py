"""
    attributedoc.py

    Defines the AttributeDoc record: the typed description of one attribute
    of an mj-* component (or one renderer option of an <mj-chart> type).

    The kind decides which live control the sandbox page renders for the
    attribute, and the values / default feed the reference table.
"""

import re

from ccai.errors.exceptions import SemanticError


#: The attribute kinds the sandbox controls panel knows how to render.
#:
#:   boolean  a checkbox; presence of the attribute means true
#:   enum     a select over ``values``
#:   string   a text field
#:   number   a number field
#:   color    a color picker
#:   json     a multi-line JSON editor; the value is validated before it is set
ATTRIBUTE_KINDS = ("boolean", "enum", "string", "number", "color", "json")

# Attribute names as HTML allows them in markup the sandbox writes.
_ATTRIBUTE_NAME = re.compile(r"^[a-zA-Z_:][-a-zA-Z0-9_:.]*$")


def _default_text(default: "str | bool | int | float | None") -> "str | None":
    """
        Normalize a default value to the attribute text it stands for.

        :param default: The default as given: a string, a bool, a number or None.

        :returns: The default as attribute text ("true"/"false" for a bool), or None.
    """

    if default is None:
        text = None
    elif isinstance(default, bool):
        if default is True:
            text = "true"
        else:
            text = "false"
    elif isinstance(default, (int, float)):
        text = str(default)
    else:
        text = str(default)

    return text


class AttributeDoc:
    """
        Typed documentation for one attribute.

        ``AttributeDoc(name="variant", description="...", kind="enum",
        values=["primary", "secondary"], default="primary")``

        A plain ``(name, description)`` tuple is still accepted wherever an
        AttributeDoc is; it is read as ``kind="string"`` with no values and no
        default (see :meth:`from_entry`).
    """

    def __init__(
        self,
        name: str,
        description: str,
        kind: str,
        values: "list[str] | None" = None,
        default: "str | bool | int | float | None" = None,
    ):
        """
            Construct an AttributeDoc.

            :param name: The attribute name as written in markup, e.g. ``max-items``.
            :param description: What the attribute does, as plain text; the page
                escapes it and shows `backticked` words as code.
            :param kind: One of :data:`ATTRIBUTE_KINDS`.
            :param values: The allowed values; required and non-empty for ``enum``,
                optional suggestions for ``string``, ignored by the other kinds.
            :param default: The value the component behaves as when the attribute is
                absent, as attribute text (``"primary"``, ``"3"``, ``"true"``). A bool
                or number is converted to that text. For a ``boolean`` attribute,
                ``"true"`` means the component is on unless the attribute is set to
                ``"false"``; the control then writes ``name="false"`` to turn it off.

            :raises SemanticError: When the name is not a valid attribute name, the
                kind is unknown, or an ``enum`` has no values.
        """

        if not isinstance(name, str) or _ATTRIBUTE_NAME.match(name) is None:
            errmsg = "AttributeDoc name {!r} is not a valid attribute name.".format(name)
            raise SemanticError(errmsg)

        if kind not in ATTRIBUTE_KINDS:
            errmsg_lines = [
                "AttributeDoc {!r} has unknown kind {!r}.".format(name, kind),
                "KNOWN KINDS: {}".format(", ".join(ATTRIBUTE_KINDS)),
            ]
            errmsg = "\n".join(errmsg_lines)
            raise SemanticError(errmsg)

        value_list = []
        if values is not None:
            for value in values:
                value_list.append(str(value))

        if kind == "enum" and len(value_list) == 0:
            errmsg = "AttributeDoc {!r} is an enum but lists no values.".format(name)
            raise SemanticError(errmsg)

        self.name = name
        self.description = description
        self.kind = kind
        self.values = value_list
        self.default = _default_text(default)

        # False for an entry converted from a legacy (name, description)
        # tuple: its kind is assumed, not documented.
        self.typed = True
        return

    @classmethod
    def from_entry(cls, entry: "AttributeDoc | tuple") -> "AttributeDoc":
        """
            Accept an AttributeDoc or a legacy ``(name, description)`` tuple.

            :param entry: An AttributeDoc, or a 2-tuple of name and description.

            :returns: The AttributeDoc for the entry.

            :raises SemanticError: When the entry is neither.
        """

        if isinstance(entry, AttributeDoc):
            doc = entry
        elif isinstance(entry, (tuple, list)) and len(entry) == 2:
            name, description = entry
            doc = cls(name=name, description=description, kind="string")
            doc.typed = False
        else:
            errmsg = (
                "An attribute entry must be an AttributeDoc or a (name, description) "
                "tuple, got {!r}.".format(entry)
            )
            raise SemanticError(errmsg)

        return doc

    def as_dict(self) -> "dict[str, object]":
        """
            Return the JSON-ready form the sandbox controls panel reads.

            :returns: A dictionary with name, kind, values, default and description.
        """

        data = {
            "name": self.name,
            "kind": self.kind,
            "values": list(self.values),
            "default": self.default,
            "description": self.description,
            "typed": self.typed,
        }
        return data

    def __repr__(self) -> str:
        """
            :returns: A debugging representation.
        """

        text = "AttributeDoc(name={!r}, kind={!r})".format(self.name, self.kind)
        return text
