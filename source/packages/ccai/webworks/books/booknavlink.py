"""
.. module:: booknavlink
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: One link of a book page's navigation: its title, its URL and whether it is the page being shown.

.. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []

from dataclasses import dataclass


@dataclass(frozen=True)
class BookNavLink:
    """
        A link in the navigation of a book page.

        :param title: The text of the link.
        :param url: Where the link goes.
        :param current: Whether the link is to the page being shown.
        :param level: The heading level, for links to the headings of the page; 0 otherwise.
    """
    title: str
    url: str
    current: bool = False
    level: int = 0
