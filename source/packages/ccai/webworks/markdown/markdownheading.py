"""
.. module:: markdownheading
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: A heading of a rendered markdown document and the anchor it can be linked to by.

.. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []

from dataclasses import dataclass


@dataclass(frozen=True)
class MarkdownHeading:
    """
        A heading of a rendered markdown document.

        :param level: The heading level, 1 to 6.
        :param text: The heading's plain text.
        :param anchor: The ``id`` the heading was given, so ``#anchor`` links to it. Anchors follow GitHub's rules, so
                       links written against a repository on GitHub keep working.
    """
    level: int
    text: str
    anchor: str
