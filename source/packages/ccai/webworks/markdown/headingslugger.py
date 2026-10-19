"""
.. module:: headingslugger
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Gives headings the same anchors GitHub gives them, unique within a document.

.. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []

import unicodedata

from typing import Dict

#: The anchor given to a heading whose text has no letters or digits.
HEADING_SLUG_FALLBACK = "section"


def make_heading_slug(text: str) -> str:
    """
        The anchor GitHub makes from a heading's text: lower case, every space a hyphen, and every character that is
        not a letter, digit, mark, hyphen or underscore removed. ``Appendix Volume — Operating`` becomes
        ``appendix-volume--operating``.

        :param text: The heading's plain text.

        :returns: The anchor; it may be empty.
    """
    kept = []
    lowered = text.lower()
    for char in lowered:
        if char == " ":
            kept.append("-")
            continue
        if char == "-" or char == "_":
            kept.append(char)
            continue
        category = unicodedata.category(char)
        major = category[0]
        if major == "L" or major == "N" or major == "M":
            kept.append(char)

    rtnval = "".join(kept)
    return rtnval


class HeadingSlugger:
    """
        Gives each heading of one document a unique anchor. The second heading with the same text gets ``-1`` added,
        the third ``-2`` and so on, as on GitHub.
    """

    def __init__(self):
        """
            Creates a slugger with no anchors given yet.
        """
        self._occurrences: Dict[str, int] = {}
        return

    def slug(self, text: str) -> str:
        """
            The anchor for the next heading.

            :param text: The heading's plain text.

            :returns: An anchor not given to any earlier heading of the document.
        """
        base = make_heading_slug(text)
        if base == "":
            base = HEADING_SLUG_FALLBACK

        candidate = base
        while candidate in self._occurrences:
            self._occurrences[base] += 1
            candidate = "{}-{}".format(base, self._occurrences[base])

        self._occurrences[candidate] = 0

        rtnval = candidate
        return rtnval
