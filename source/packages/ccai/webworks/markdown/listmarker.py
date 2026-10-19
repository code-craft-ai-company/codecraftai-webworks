"""
.. module:: listmarker
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: The marker that starts a list item (``-``, ``*``, ``+``, ``1.`` or ``1)``) and where its content starts.

.. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []

from dataclasses import dataclass


@dataclass(frozen=True)
class ListMarker:
    """
        The marker at the start of a list item line.

        :param ordered: Whether the marker is a number (``1.`` or ``1)``) rather than a bullet.
        :param symbol: The bullet character (``-``, ``*`` or ``+``) or the delimiter after the number (``.`` or ``)``).
                       Items belong to the same list only when their symbols are the same.
        :param number: The number of an ordered marker; 0 for a bullet.
        :param indent: The column the marker starts at.
        :param content_column: The column the item's content starts at. Continuation lines indented this far belong to
                               the item.
        :param first_line: The content on the marker's line, after the marker.
    """
    ordered: bool
    symbol: str
    number: int
    indent: int
    content_column: int
    first_line: str

    def is_same_list(self, other: "ListMarker") -> bool:
        """
            Whether an item with this marker continues the list that an item with ``other`` belongs to.

            :param other: The marker of an earlier item.

            :returns: True when both are bullets with the same character, or both are numbers with the same delimiter.
        """
        rtnval = self.ordered == other.ordered and self.symbol == other.symbol
        return rtnval
