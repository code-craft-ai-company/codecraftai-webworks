"""
.. module:: inlinenode
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: One piece of the inline content of a markdown block: text, code, emphasis, a link and so on.

.. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []

from typing import List, Optional

#: Plain text.
INLINE_KIND_TEXT = "text"

#: A code span; its text is shown exactly as written.
INLINE_KIND_CODE = "code"

#: Emphasis (``*text*`` or ``_text_``).
INLINE_KIND_EMPHASIS = "emphasis"

#: Strong emphasis (``**text**`` or ``__text__``).
INLINE_KIND_STRONG = "strong"

#: Struck-through text (``~~text~~``).
INLINE_KIND_STRIKETHROUGH = "strikethrough"

#: A link; its children are the link text.
INLINE_KIND_LINK = "link"

#: An image; its children are the image description (the alt text).
INLINE_KIND_IMAGE = "image"

#: A line ending inside a paragraph that is not a hard break.
INLINE_KIND_SOFT_BREAK = "softbreak"

#: A hard line break (two trailing spaces or a trailing backslash).
INLINE_KIND_HARD_BREAK = "hardbreak"


class InlineNode:
    """
        One piece of the inline content of a paragraph, heading or table cell.

        ``text`` holds the characters of a text or code node. ``children`` hold the content of emphasis, strong,
        strikethrough, link and image nodes. ``destination`` and ``title`` belong to links and images.
    """

    def __init__(self, kind: str, *, text: str = "", children: Optional[List["InlineNode"]] = None, destination: str = "",
                 title: str = ""):
        """
            Creates an inline node.

            :param kind: One of the ``INLINE_KIND_*`` constants.
            :param text: The characters of a text or code node.
            :param children: The content of a container node (emphasis, strong, strikethrough, link or image).
            :param destination: The destination of a link or the source of an image.
            :param title: The title of a link or image.
        """
        self.kind = kind
        self.text = text
        self.children: List[InlineNode] = []
        if children is not None:
            self.children = children
        self.destination = destination
        self.title = title
        return

    def to_text(self) -> str:
        """
            The plain text of this node: the characters of text and code, a space for a line break and the text of the
            children of a container. An image contributes its description.

            :returns: The plain text.
        """
        if self.kind == INLINE_KIND_TEXT or self.kind == INLINE_KIND_CODE:
            rtnval = self.text
        elif self.kind == INLINE_KIND_SOFT_BREAK or self.kind == INLINE_KIND_HARD_BREAK:
            rtnval = " "
        else:
            parts = []
            for child in self.children:
                child_text = child.to_text()
                parts.append(child_text)
            rtnval = "".join(parts)

        return rtnval

    def __repr__(self) -> str:
        """
            A short description of the node for the debugger.

            :returns: The description.
        """
        if self.kind == INLINE_KIND_TEXT or self.kind == INLINE_KIND_CODE:
            rtnval = "InlineNode({}, {!r})".format(self.kind, self.text)
        else:
            rtnval = "InlineNode({}, children={})".format(self.kind, len(self.children))
        return rtnval
