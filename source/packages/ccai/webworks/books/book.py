"""
.. module:: book
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: A book of a library: its index document and the documents the index links to, in order.

.. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []

from dataclasses import dataclass
from typing import List, Optional, Tuple

from ccai.webworks.books.bookentry import BookEntry


@dataclass(frozen=True)
class Book:
    """
        A book (a volume) of a library.

        A book is defined by its index document, not by the folders its files are in: the documents of the book are the
        markdown documents the index links to, in the order the links appear (in lists, tables or paragraphs), and
        the reading order runs from the index through those documents.

        :param document: The location of the book's index document.
        :param title: The title of the book: the text of the library index's link to it.
        :param entries: The documents the index links to, in the order of the links.
    """
    document: str
    title: str
    entries: Tuple[BookEntry, ...]

    def sequence(self) -> List[BookEntry]:
        """
            The reading order of the book: the index document, then its entries.

            :returns: The entries of the reading order.
        """
        index_entry = BookEntry(document=self.document, title=self.title)
        rtnval = [index_entry]
        rtnval.extend(self.entries)
        return rtnval

    def contains(self, document: str) -> bool:
        """
            Whether a document is the book's index or one of its entries.

            :param document: The location of the document.

            :returns: True when the document is part of the book.
        """
        if document == self.document:
            return True

        for entry in self.entries:
            if entry.document == document:
                return True

        return False

    def neighbors(self, document: str) -> Tuple[Optional[BookEntry], Optional[BookEntry]]:
        """
            The documents before and after a document in the book's reading order.

            :param document: The location of the document.

            :returns: ``(previous, next)``; either is None at the ends of the book, and both are None when the document
                      is not part of the book.
        """
        sequence = self.sequence()

        position = -1
        for index, entry in enumerate(sequence):
            if entry.document == document:
                position = index
                break

        if position < 0:
            rtnval = (None, None)
            return rtnval

        previous_entry = None
        if position > 0:
            previous_entry = sequence[position - 1]

        next_entry = None
        if position + 1 < len(sequence):
            next_entry = sequence[position + 1]

        rtnval = (previous_entry, next_entry)
        return rtnval
