"""
.. module:: bookentry
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: A document listed in a book's index: where it is and the title the index gives it.

.. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []

from dataclasses import dataclass


@dataclass(frozen=True)
class BookEntry:
    """
        A document of a book.

        :param document: The document's location in the library: its path from the library root, with ``/`` between
                         the parts (``volumes/00-foundations/chapters/03-the-error-vocabulary.md``).
        :param title: The text of the index's link to the document, which is the title the navigation shows.
    """
    document: str
    title: str
