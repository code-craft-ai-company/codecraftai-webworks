"""
.. module:: bookpage
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Everything a book page shows: the rendered document and the navigation around it.

.. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []

from dataclasses import dataclass, field
from typing import Optional, Tuple

from ccai.webworks.books.booknavlink import BookNavLink


@dataclass(frozen=True)
class BookPage:
    """
        The content of one page of a book site, ready to be written as HTML by :class:`BookPageWriter`.

        :param title: The title of the page.
        :param library_title: The title of the library.
        :param library_url: The URL of the library's index page.
        :param stylesheet_url: The URL of the page's stylesheet.
        :param content_html: The HTML of the rendered document. It is written into the page as it is, so it must
                             already be safe (as the output of :class:`MarkdownRenderer` is).
        :param breadcrumbs: The trail from the library to the page; the last link is the page itself, marked current.
        :param book: The link to the index of the book the page belongs to, or None.
        :param contents: The book's reading order, or, on the library page, the books; the page's own entry is marked
                         current.
        :param previous: The page before this one in the book, or None.
        :param next: The page after this one in the book, or None.
        :param outline: Links to the page's own headings.
    """
    title: str
    library_title: str
    library_url: str
    stylesheet_url: str
    content_html: str
    breadcrumbs: Tuple[BookNavLink, ...] = field(default_factory=tuple)
    book: Optional[BookNavLink] = None
    contents: Tuple[BookNavLink, ...] = field(default_factory=tuple)
    previous: Optional[BookNavLink] = None
    next: Optional[BookNavLink] = None
    outline: Tuple[BookNavLink, ...] = field(default_factory=tuple)
