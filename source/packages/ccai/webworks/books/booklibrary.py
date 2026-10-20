"""
.. module:: booklibrary
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: A library of markdown books in a folder, navigated by the links in its index documents.

.. moduleauthor:: Code Craft AI LLC

Navigation comes from the markdown, not from the folders the files are in. The library's index document (the
``README.md`` at the root by default) links to the books, and each book's index document links to its documents. The
order of the links, in lists, tables or paragraphs, is the order of the navigation, and the text of each link is the
title the navigation shows. A link to a folder means the folder's ``README.md`` (or ``index.md``).

A library only hands out files inside its root folder: locations that climb out of it with ``..``, name a hidden file or
folder (``.git``), or lead out of it through a symbolic link are refused. Besides markdown documents it serves images.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []

import os
import posixpath
import threading
import urllib.parse

from typing import Callable, Dict, List, Optional, Set, Tuple

from ccai.errors.exceptions import ConfigurationError

from ccai.webworks.books.book import Book
from ccai.webworks.books.bookentry import BookEntry
from ccai.webworks.markdown.markdowndocument import MarkdownDocument
from ccai.webworks.markdown.markdownrenderer import MarkdownRenderer

#: The names a folder's index document may have, in the order they are tried.
BOOKS_INDEX_NAMES: Tuple[str, ...] = ("README.md", "index.md")

#: The extension of a markdown document.
BOOKS_DOCUMENT_EXTENSION = ".md"

#: The files a library serves besides its documents, by extension, with their content types.
BOOKS_ASSET_CONTENT_TYPES: Dict[str, str] = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
    ".webp": "image/webp",
}

#: The title of a library whose index document has no heading and that was given no title.
BOOKS_DEFAULT_TITLE = "Library"


class BookLibrary:
    """
        A library of markdown books in a folder.

        :meth:`books` lists the books the library index links to, and :meth:`book_for` finds the book a document
        belongs to. Documents are rendered with :meth:`render_document`. The navigation is built once and built again
        when one of the index documents it was built from changes, so edits show without a restart.
    """

    def __init__(self, root_dir: str, *, index_document: str = "README.md", title: Optional[str] = None,
                 renderer: Optional[MarkdownRenderer] = None):
        """
            Creates a library.

            :param root_dir: The folder that holds the library. Nothing outside it is ever served.
            :param index_document: The location of the library's index document, from the root folder. It may name a
                                   folder, which means the folder's ``README.md`` or ``index.md``.
            :param title: The library's title; None takes the title of the index document.
            :param renderer: The renderer for the documents; None creates one.

            :raises: ConfigurationError
        """
        expanded = os.path.expanduser(root_dir)
        resolved_root = os.path.realpath(expanded)
        if not os.path.isdir(resolved_root):
            err_msg_lines = [
                "The root folder of a book library does not exist or is not a folder.",
                "ROOT: {}".format(root_dir),
                "RESOLVED: {}".format(resolved_root),
            ]
            err_msg = os.linesep.join(err_msg_lines)
            raise ConfigurationError(err_msg)

        self._root_dir = resolved_root
        self._title = title
        self._renderer = MarkdownRenderer()
        if renderer is not None:
            self._renderer = renderer

        self._lock = threading.Lock()
        self._books: Optional[List[Book]] = None
        self._index_title: Optional[str] = None
        self._navigation_stamps: Dict[str, int] = {}

        resolved_index = self.resolve_document(index_document)
        if resolved_index is None:
            err_msg_lines = [
                "The index document of a book library was not found in the library.",
                "ROOT: {}".format(self._root_dir),
                "INDEX DOCUMENT: {}".format(index_document),
                "An index document is a markdown file ('{}') inside the root folder, or a folder that holds one of: {}".format(
                    BOOKS_DOCUMENT_EXTENSION, ", ".join(BOOKS_INDEX_NAMES)),
            ]
            err_msg = os.linesep.join(err_msg_lines)
            raise ConfigurationError(err_msg)

        self._index_document = resolved_index
        return

    @property
    def root_dir(self) -> str:
        """
            The library's root folder, with symbolic links resolved.
        """
        return self._root_dir

    @property
    def index_document(self) -> str:
        """
            The location of the library's index document.
        """
        return self._index_document

    def canonical_location(self, location: str) -> Optional[str]:
        """
            The canonical form of a location in the library: its parts joined by ``/``, with empty parts and ``.``
            removed. The root is the empty string.

            :param location: A location, from the library root, with ``/`` between its parts.

            :returns: The canonical location, or None when the location climbs out of the root (``..``), names a
                      hidden file or folder, holds a backslash or a NUL, or leads out of the root through a symbolic
                      link.
        """
        if "\x00" in location or "\\" in location:
            return None

        parts: List[str] = []
        for part in location.split("/"):
            if part == "" or part == ".":
                continue
            if part.startswith("."):
                return None
            parts.append(part)

        full_path = self._full_path(parts)
        resolved = os.path.realpath(full_path)
        if resolved != self._root_dir and not resolved.startswith(self._root_dir + os.sep):
            return None

        rtnval = "/".join(parts)
        return rtnval

    def resolve_document(self, location: str) -> Optional[str]:
        """
            The markdown document a location names. A folder names its ``README.md`` (or ``index.md``).

            :param location: A location, from the library root.

            :returns: The canonical location of the document, or None when the location does not name a markdown
                      document in the library.
        """
        relative = self.canonical_location(location)
        if relative is None:
            return None

        full_path = self._full_path(relative.split("/"))
        if os.path.isdir(full_path):
            for name in BOOKS_INDEX_NAMES:
                if relative == "":
                    candidate = name
                else:
                    candidate = "{}/{}".format(relative, name)
                candidate_relative = self.canonical_location(candidate)
                if candidate_relative is None:
                    continue
                candidate_full = self._full_path(candidate_relative.split("/"))
                if os.path.isfile(candidate_full):
                    return candidate_relative
            return None

        if os.path.isfile(full_path) and relative.lower().endswith(BOOKS_DOCUMENT_EXTENSION):
            return relative

        return None

    def resolve_asset(self, location: str) -> Optional[str]:
        """
            The image a location names.

            :param location: A location, from the library root.

            :returns: The canonical location of the image, or None when the location does not name a file of one of
                      the types in :data:`BOOKS_ASSET_CONTENT_TYPES`.
        """
        relative = self.canonical_location(location)
        if relative is None or relative == "":
            return None

        _, extension = posixpath.splitext(relative)
        if extension.lower() not in BOOKS_ASSET_CONTENT_TYPES:
            return None

        full_path = self._full_path(relative.split("/"))
        if not os.path.isfile(full_path):
            return None

        return relative

    def asset_content_type(self, asset: str) -> str:
        """
            The content type of an image.

            :param asset: The location of the image.

            :returns: The content type.

            :raises: ValueError
        """
        _, extension = posixpath.splitext(asset)
        content_type = BOOKS_ASSET_CONTENT_TYPES.get(extension.lower())
        if content_type is None:
            errmsg = "The file '{}' is not one of the image types a book library serves.".format(asset)
            raise ValueError(errmsg)
        return content_type

    def is_document(self, location: str) -> bool:
        """
            Whether a canonical location names a markdown document (rather than an image).

            :param location: A canonical location.

            :returns: True for a document.
        """
        rtnval = location.lower().endswith(BOOKS_DOCUMENT_EXTENSION)
        return rtnval

    def resolve_link(self, *, document: str, destination: str) -> Optional[Tuple[str, str]]:
        """
            What a link in a document points to inside the library. A relative destination is taken from the document's
            folder and a destination starting with ``/`` from the library root.

            :param document: The location of the document the link is in.
            :param destination: The link's destination as written.

            :returns: ``(canonical location of the document or image, fragment)``, or None when the destination is a
                      fragment alone, has a scheme or a host, or does not name a document or image in the library.
        """
        target = destination.strip()
        if target == "" or target.startswith("#"):
            return None

        split = urllib.parse.urlsplit(target)
        if split.scheme != "" or split.netloc != "":
            return None

        path = urllib.parse.unquote(split.path)
        if path == "":
            return None

        if path.startswith("/"):
            joined = path.lstrip("/")
        else:
            base = posixpath.dirname(document)
            joined = posixpath.join(base, path)

        normalized = posixpath.normpath(joined)
        if normalized == ".":
            normalized = ""
        if normalized == ".." or normalized.startswith("../"):
            return None

        resolved = self.resolve_document(normalized)
        if resolved is None:
            resolved = self.resolve_asset(normalized)
        if resolved is None:
            return None

        rtnval = (resolved, split.fragment)
        return rtnval

    def read_document(self, document: str) -> str:
        """
            The text of a document. Bytes that are not UTF-8 are replaced rather than refused.

            :param document: The canonical location of the document.

            :returns: The markdown text.
        """
        full_path = self._full_path(document.split("/"))
        with open(full_path, "r", encoding="utf-8", errors="replace") as document_file:
            text = document_file.read()
        return text

    def read_asset(self, asset: str) -> bytes:
        """
            The bytes of an image.

            :param asset: The canonical location of the image.

            :returns: The content.
        """
        full_path = self._full_path(asset.split("/"))
        with open(full_path, "rb") as asset_file:
            content = asset_file.read()
        return content

    def render_document(self, document: str, *, link_rewriter: Optional[Callable[[str], str]] = None) -> MarkdownDocument:
        """
            Renders a document.

            :param document: The canonical location of the document.
            :param link_rewriter: Called with the destination of every link and image; see
                                  :meth:`MarkdownRenderer.render`.

            :returns: The rendered document.
        """
        text = self.read_document(document)
        rtnval = self._renderer.render(text, link_rewriter=link_rewriter)
        return rtnval

    def library_title(self) -> str:
        """
            The library's title: the title it was given, else the title of its index document.

            :returns: The title.
        """
        if self._title is not None:
            return self._title

        with self._lock:
            self._refresh_navigation()
            title = self._index_title

        if title is None:
            title = BOOKS_DEFAULT_TITLE

        rtnval = title
        return rtnval

    def books(self) -> List[Book]:
        """
            The books of the library: the documents its index document links to, in the order of the links.

            :returns: The books.
        """
        with self._lock:
            self._refresh_navigation()
            rtnval = list(self._books)
        return rtnval

    def book_for(self, document: str) -> Optional[Book]:
        """
            The book a document belongs to: the book whose index it is, else the first book that lists it.

            :param document: The canonical location of the document.

            :returns: The book, or None when no book holds the document.
        """
        books = self.books()

        for book in books:
            if book.document == document:
                return book

        for book in books:
            if book.contains(document):
                return book

        return None

    def _full_path(self, parts: List[str]) -> str:
        """
            The path on disk of a location's parts.

            :param parts: The parts of the location; empty parts are ignored.

            :returns: The path.
        """
        kept = []
        for part in parts:
            if part != "":
                kept.append(part)
        rtnval = os.path.join(self._root_dir, *kept)
        return rtnval

    def _stamp(self, document: str) -> int:
        """
            The modification time of a document, used to tell when the navigation has to be built again.

            :param document: The canonical location of the document.

            :returns: The modification time in nanoseconds, or -1 when the document no longer exists.
        """
        full_path = self._full_path(document.split("/"))
        if not os.path.isfile(full_path):
            return -1
        status = os.stat(full_path)
        rtnval = status.st_mtime_ns
        return rtnval

    def _refresh_navigation(self) -> None:
        """
            Builds the navigation when it has not been built or when a document it was built from has changed. The
            caller holds the lock.
        """
        if self._books is not None:
            current = True
            for document, stamp in self._navigation_stamps.items():
                if self._stamp(document) != stamp:
                    current = False
                    break
            if current:
                return

        stamps: Dict[str, int] = {}
        index_rendered = self._render_for_navigation(self._index_document, stamps)

        books: List[Book] = []
        seen: Set[str] = {self._index_document}
        for link in index_rendered.links:
            resolved = self.resolve_link(document=self._index_document, destination=link.destination)
            if resolved is None:
                continue
            location, _ = resolved
            if not self.is_document(location) or location in seen:
                continue
            seen.add(location)

            book = self._build_book(location, label=link.text, stamps=stamps)
            books.append(book)

        self._books = books
        self._index_title = index_rendered.title
        self._navigation_stamps = stamps
        return

    def _build_book(self, document: str, *, label: str, stamps: Dict[str, int]) -> Book:
        """
            Builds a book from its index document.

            :param document: The canonical location of the book's index document.
            :param label: The text of the library index's link to the book.
            :param stamps: The modification times of the documents read so far; the documents read here are added.

            :returns: The book.
        """
        rendered = self._render_for_navigation(document, stamps)

        title = label.strip()
        if title == "":
            title = self._title_of(rendered, document)

        entries: List[BookEntry] = []
        seen: Set[str] = {document, self._index_document}
        for link in rendered.links:
            resolved = self.resolve_link(document=document, destination=link.destination)
            if resolved is None:
                continue
            location, _ = resolved
            if not self.is_document(location) or location in seen:
                continue
            seen.add(location)

            entry_title = link.text.strip()
            if entry_title == "":
                entry_rendered = self._render_for_navigation(location, stamps)
                entry_title = self._title_of(entry_rendered, location)
            entries.append(BookEntry(document=location, title=entry_title))

        rtnval = Book(document=document, title=title, entries=tuple(entries))
        return rtnval

    def _render_for_navigation(self, document: str, stamps: Dict[str, int]) -> MarkdownDocument:
        """
            Renders a document that the navigation is built from and records its modification time.

            :param document: The canonical location of the document.
            :param stamps: The modification times recorded so far.

            :returns: The rendered document.
        """
        stamps[document] = self._stamp(document)
        rtnval = self.render_document(document)
        return rtnval

    def _title_of(self, rendered: MarkdownDocument, document: str) -> str:
        """
            The title of a document: its first heading, else its file name.

            :param rendered: The rendered document.
            :param document: The canonical location of the document.

            :returns: The title.
        """
        if rendered.title is not None and rendered.title != "":
            return rendered.title

        rtnval = posixpath.basename(document)
        return rtnval
