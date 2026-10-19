"""
.. module:: delimiterrun
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: A run of ``*``, ``_`` or ``~`` characters that may open or close emphasis.

.. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []

from ccai.webworks.markdown.inlinenode import InlineNode


class DelimiterRun:
    """
        A run of ``*``, ``_`` or ``~`` characters on the delimiter stack of the inline parser.

        The run's characters live in ``node`` (a text node). When the run opens or closes emphasis the characters it uses
        are taken off ``node`` and ``count`` goes down; ``original_count`` keeps the length the run was written with,
        which the "multiple of three" rule of CommonMark looks at.
    """

    def __init__(self, *, node: InlineNode, char: str, count: int, can_open: bool, can_close: bool):
        """
            Creates a delimiter run.

            :param node: The text node that holds the run's characters.
            :param char: The delimiter character: ``*``, ``_`` or ``~``.
            :param count: The number of characters in the run.
            :param can_open: Whether the run can open emphasis.
            :param can_close: Whether the run can close emphasis.
        """
        self.node = node
        self.char = char
        self.count = count
        self.original_count = count
        self.can_open = can_open
        self.can_close = can_close
        return

    def __repr__(self) -> str:
        """
            A short description of the run for the debugger.

            :returns: The description.
        """
        rtnval = "DelimiterRun({!r} x{}, open={}, close={})".format(self.char, self.count, self.can_open, self.can_close)
        return rtnval
