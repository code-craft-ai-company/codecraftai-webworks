"""
    componentexample.py

    Defines the ComponentExample record: one named, selectable example in the
    gallery of a component page or a chart-type page. Selecting it loads its
    HTML, CSS and script into the sandbox editors and runs it in the preview.
"""

import re

from ccai.errors.exceptions import SemanticError


# Example keys appear in URLs (?example=<key>) and in data-testid values.
EXAMPLE_KEY_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

#: The key and title given to the gallery entry built from a doc's single
#: legacy ``example`` string when the doc lists no ``examples``.
DEFAULT_EXAMPLE_KEY = "basic"
DEFAULT_EXAMPLE_TITLE = "Basic usage"


class ComponentExample:
    """
        One gallery example.

        ``ComponentExample(key="variants", title="Variants", description="<p>...</p>",
        html='<mj-button variant="primary">Save</mj-button>', css="", script="",
        height=None)``
    """

    def __init__(
        self,
        key: str,
        title: str,
        description: str,
        html: str,
        css: str = "",
        script: str = "",
        height: "int | None" = None,
    ):
        """
            Construct a ComponentExample.

            :param key: URL-safe identifier, unique within its page: lower-case
                letters, digits and single hyphens (``basic``, ``with-icons``).
            :param title: Short plain-text name shown in the gallery.
            :param description: What the example shows (an HTML fragment).
            :param html: The markup placed in the preview's <body>. It should not
                carry the behaviour; put that in ``script``.
            :param css: CSS for the preview document (added in a <style> in its head).
            :param script: JavaScript run as a module after the library has defined
                every element in the preview, so methods and properties work. It may
                use top-level ``await`` and ``import``.
            :param height: Minimum preview height in CSS pixels, for content that does
                not take up layout space (fixed overlays, toasts, full-height layouts).
                None lets the preview size itself to its content.

            :raises SemanticError: When the key is malformed, the title is empty, there
                is neither html nor script, or the height is not a positive integer.
        """

        if not isinstance(key, str) or EXAMPLE_KEY_PATTERN.match(key) is None:
            errmsg = (
                "ComponentExample key {!r} must be lower-case letters, digits and "
                "single hyphens, e.g. 'basic' or 'with-icons'.".format(key)
            )
            raise SemanticError(errmsg)

        if not isinstance(title, str) or title.strip() == "":
            errmsg = "ComponentExample {!r} needs a non-empty title.".format(key)
            raise SemanticError(errmsg)

        if html.strip() == "" and script.strip() == "":
            errmsg = "ComponentExample {!r} has neither html nor script.".format(key)
            raise SemanticError(errmsg)

        if height is not None:
            if isinstance(height, bool) or not isinstance(height, int) or height <= 0:
                errmsg = (
                    "ComponentExample {!r} height must be a positive number of "
                    "pixels or None, got {!r}.".format(key, height)
                )
                raise SemanticError(errmsg)

        self.key = key
        self.title = title
        self.description = description
        self.html = html
        self.css = css
        self.script = script
        self.height = height
        return

    def as_dict(self) -> "dict[str, object]":
        """
            Return the JSON-ready form the sandbox page script reads.

            :returns: A dictionary of every field.
        """

        data = {
            "key": self.key,
            "title": self.title,
            "description": self.description,
            "html": self.html,
            "css": self.css,
            "script": self.script,
            "height": self.height,
        }
        return data

    def __repr__(self) -> str:
        """
            :returns: A debugging representation.
        """

        text = "ComponentExample(key={!r}, title={!r})".format(self.key, self.title)
        return text


def build_gallery(
    owner: str,
    examples: "list[ComponentExample] | None",
    example: str,
) -> "list[ComponentExample]":
    """
        Build the gallery of a page: its ``examples`` when it lists any, else one
        entry made from its single legacy ``example`` string.

        :param owner: The tag or chart type the gallery belongs to, for messages.
        :param examples: The doc's examples list (may be None or empty).
        :param example: The doc's single legacy example markup.

        :returns: The non-empty, ordered list of gallery examples.

        :raises SemanticError: When an entry is not a ComponentExample, two entries
            share a key, or there is no example at all.
    """

    gallery = []
    if examples is not None:
        for entry in examples:
            if not isinstance(entry, ComponentExample):
                errmsg = "{}: examples must hold ComponentExample instances, got {!r}.".format(
                    owner, entry)
                raise SemanticError(errmsg)
            gallery.append(entry)

    if len(gallery) == 0:
        if example is None or example.strip() == "":
            errmsg = "{}: give either an 'example' string or a non-empty 'examples' list.".format(
                owner)
            raise SemanticError(errmsg)
        legacy = ComponentExample(
            key=DEFAULT_EXAMPLE_KEY,
            title=DEFAULT_EXAMPLE_TITLE,
            description="",
            html=example,
        )
        gallery.append(legacy)

    seen = set()
    for entry in gallery:
        if entry.key in seen:
            errmsg = "{}: two examples share the key {!r}.".format(owner, entry.key)
            raise SemanticError(errmsg)
        seen.add(entry.key)

    return gallery
