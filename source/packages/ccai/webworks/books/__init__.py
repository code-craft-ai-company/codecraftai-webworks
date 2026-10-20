"""
.. module:: books
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Package that serves a library of markdown books as HTML pages.

.. moduleauthor:: Code Craft AI LLC

This package provides:

- :class:`BookLibrary`, a folder of markdown books whose navigation comes from the links in its index documents
- :class:`BooksBlueprint`, the blueprint that serves a library: rendered documents with contents, breadcrumbs,
  previous and next links and an outline, plus the library's images and the pages' stylesheet
- :class:`Book` and :class:`BookEntry`, the navigation read from the index documents

Navigation does not depend on how the files are arranged in folders. The library index (``README.md`` at the root)
links to the books; each book's index links to its documents; the order of those links is the reading order.

Example::

    from ccai.webworks.books import BookLibrary, BooksBlueprint

    library = BookLibrary("~/repos/codecraftai-books")
    books = BooksBlueprint(library, mount_path="/books")
    books.attach_to_webapp(webapp)
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []

from ccai.webworks.books.book import Book
from ccai.webworks.books.bookentry import BookEntry
from ccai.webworks.books.booklibrary import BOOKS_ASSET_CONTENT_TYPES, BOOKS_INDEX_NAMES, BookLibrary
from ccai.webworks.books.booknavlink import BookNavLink
from ccai.webworks.books.bookpage import BookPage
from ccai.webworks.books.bookpagewriter import BookPageWriter
from ccai.webworks.books.booksblueprint import BooksBlueprint

__all__ = [
    "BOOKS_ASSET_CONTENT_TYPES",
    "BOOKS_INDEX_NAMES",
    "Book",
    "BookEntry",
    "BookLibrary",
    "BookNavLink",
    "BookPage",
    "BookPageWriter",
    "BooksBlueprint",
]
