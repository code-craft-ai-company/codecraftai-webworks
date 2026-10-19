"""
.. module:: bracketopener
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: An opening ``[`` or ``![`` that may become the start of a link or an image.

.. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []

from ccai.webworks.markdown.inlinenode import InlineNode


class BracketOpener:
    """
        An opening ``[`` (or ``![`` for an image) on the bracket stack of the inline parser.

        When a ``]`` is followed by a link destination or a known reference, everything after ``node`` becomes the
        content of the link or image. ``delimiter_bottom`` is the height of the delimiter stack when the bracket was
        opened, so emphasis inside the link text is resolved on its own. A link cannot contain a link, so the openers
        below a finished link are made inactive.
    """

    def __init__(self, *, node: InlineNode, is_image: bool, label_start: int, delimiter_bottom: int):
        """
            Creates a bracket opener.

            :param node: The text node that holds ``[`` or ``![``.
            :param is_image: Whether the opener is ``![``.
            :param label_start: The position in the source just after the opening bracket.
            :param delimiter_bottom: The height of the delimiter stack when the bracket was opened.
        """
        self.node = node
        self.is_image = is_image
        self.label_start = label_start
        self.delimiter_bottom = delimiter_bottom
        self.active = True
        return

    def __repr__(self) -> str:
        """
            A short description of the opener for the debugger.

            :returns: The description.
        """
        rtnval = "BracketOpener(image={}, active={}, at={})".format(self.is_image, self.active, self.label_start)
        return rtnval
