"""
    Tests for a library of markdown books.

    The navigation of a library comes from the links in its index documents, not from the folders its files are in;
    the library only hands out documents and images inside its root folder.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []

import os
import tempfile
import time

from ccai import testbase

from ccai.errors.exceptions import ConfigurationError

from ccai.testshared.books.librarysample import write_sample_library

from ccai.webworks.books import BookLibrary


def test_the_books_are_the_documents_the_library_index_links_to_in_link_order():
    """
        **Feature: book library navigation**
        **Property: the books are the markdown documents the library index links to, in the order of the links, titled by the link text; a folder link
        means the folder's README.md, a link to index.md is followed, and links to other sites are not books.**
    """
    with tempfile.TemporaryDirectory() as root:
        write_sample_library(root)
        library = BookLibrary(root)
        books = [(book.document, book.title) for book in library.books()]

    testbase.assert_equal(
        books,
        [
            ("volumes/one/README.md", "First Volume"),
            ("volumes/two/index.md", "Second Volume"),
            ("series.md", "series plan"),
        ],
    )
    return


def test_a_books_entries_follow_its_index_links_not_its_folders():
    """
        **Feature: book library navigation**
        **Property: a book's entries are the documents its index links to, in link order, titled by the link text: the link back to the library, a
        repeated link and a link to an image are not entries; a linked appendix outside the chapters folder is one; an unlinked chapter inside the
        chapters folder is not.**
    """
    with tempfile.TemporaryDirectory() as root:
        write_sample_library(root)
        library = BookLibrary(root)
        first, second, _ = library.books()

    testbase.assert_equal(
        (
            [(entry.document, entry.title) for entry in first.entries],
            [(entry.document, entry.title) for entry in second.entries],
        ),
        (
            [
                ("volumes/one/chapters/01-start.md", "Getting Started"),
                ("volumes/one/chapters/02-further.md", "Going Further"),
                ("volumes/one/appendix/a.md", "Appendix A"),
            ],
            [("volumes/two/only.md", "The Only Chapter")],
        ),
    )
    return


def test_a_document_belongs_to_the_book_whose_index_lists_it():
    """
        **Feature: book library navigation**
        **Property: a book index belongs to its own book even when another book lists it; an entry belongs to the book that lists it; a document no
        index lists belongs to no book.**
    """
    with tempfile.TemporaryDirectory() as root:
        write_sample_library(root)
        library = BookLibrary(root)
        found = []
        for document in ("volumes/one/README.md", "volumes/one/chapters/02-further.md", "volumes/two/only.md", "volumes/one/chapters/99-unlisted.md"):
            book = library.book_for(document)
            if book is None:
                found.append(None)
            else:
                found.append(book.title)

    testbase.assert_equal(found, ["First Volume", "First Volume", "Second Volume", None])
    return


def test_the_reading_order_runs_from_the_index_through_the_entries():
    """
        **Feature: book library navigation**
        **Property: the document before the first entry is the book's index, the entries follow one another in link order, and the last entry has no
        next document.**
    """
    with tempfile.TemporaryDirectory() as root:
        write_sample_library(root)
        library = BookLibrary(root)
        book = library.book_for("volumes/one/README.md")

    neighbors = []
    for document in ("volumes/one/README.md", "volumes/one/chapters/01-start.md", "volumes/one/appendix/a.md"):
        previous_entry, next_entry = book.neighbors(document)
        previous_document = None
        if previous_entry is not None:
            previous_document = previous_entry.document
        next_document = None
        if next_entry is not None:
            next_document = next_entry.document
        neighbors.append((previous_document, next_document))

    testbase.assert_equal(
        neighbors,
        [
            (None, "volumes/one/chapters/01-start.md"),
            ("volumes/one/README.md", "volumes/one/chapters/02-further.md"),
            ("volumes/one/chapters/02-further.md", None),
        ],
    )
    return


def test_links_resolve_from_the_documents_folder_or_the_library_root():
    """
        **Feature: book library links**
        **Property: a relative link resolves from the linking document's folder and keeps its fragment, a link starting with ``/`` resolves from the
        library root, a folder link resolves to its index, and an image resolves as an image.**
    """
    with tempfile.TemporaryDirectory() as root:
        write_sample_library(root)
        library = BookLibrary(root)
        chapter = "volumes/one/chapters/01-start.md"
        resolved = (
            library.resolve_link(document=chapter, destination="02-further.md#details"),
            library.resolve_link(document=chapter, destination="/series.md"),
            library.resolve_link(document=chapter, destination="../../two/"),
            library.resolve_link(document=chapter, destination="../figures/diagram.png"),
        )

    testbase.assert_equal(
        resolved,
        (
            ("volumes/one/chapters/02-further.md", "details"),
            ("series.md", ""),
            ("volumes/two/index.md", ""),
            ("volumes/one/figures/diagram.png", ""),
        ),
    )
    return


def test_links_outside_the_library_or_to_nothing_do_not_resolve():
    """
        **Feature: book library links**
        **Property: a fragment alone, an address on another site, a path that climbs out of the root, a missing document and a file that is neither a
        document nor an image resolve to nothing.**
    """
    with tempfile.TemporaryDirectory() as root:
        write_sample_library(root)
        library = BookLibrary(root)
        chapter = "volumes/one/chapters/01-start.md"
        resolved = []
        for destination in ("#setup", "https://example.com/a.md", "../../../../elsewhere/code.py", "../../../../../README.md",
                            "99-missing.md", "/notes.txt"):
            resolved.append(library.resolve_link(document=chapter, destination=destination))

    testbase.assert_equal(resolved, [None, None, None, None, None, None])
    return


def test_locations_that_leave_the_root_or_name_hidden_files_are_refused():
    """
        **Feature: book library safety**
        **Property: ``..``, a hidden file or folder, a backslash and a NUL are refused; empty parts and ``.`` are dropped from an accepted location.**
    """
    with tempfile.TemporaryDirectory() as root:
        write_sample_library(root)
        library = BookLibrary(root)
        canonical = []
        for location in ("../outside.md", "volumes/../README.md", ".hidden/secret.md", "volumes\\one", "README.md\x00", "volumes//one/./README.md"):
            canonical.append(library.canonical_location(location))

    testbase.assert_equal(canonical, [None, None, None, None, None, "volumes/one/README.md"])
    return


def test_a_symbolic_link_out_of_the_root_is_refused():
    """
        **Feature: book library safety**
        **Property: a document reached through a symbolic link that points outside the root is refused, while one that points inside the root is
        served.**
    """
    with tempfile.TemporaryDirectory() as root, tempfile.TemporaryDirectory() as outside:
        write_sample_library(root)
        with open(os.path.join(outside, "leak.md"), "w", encoding="utf-8") as leak_file:
            leak_file.write("# Leak\n")
        os.symlink(outside, os.path.join(root, "escape"))
        os.symlink(os.path.join(root, "volumes", "two"), os.path.join(root, "shortcut"))

        library = BookLibrary(root)
        resolved = (library.resolve_document("escape/leak.md"), library.resolve_document("shortcut/only.md"))

    testbase.assert_equal(resolved, (None, "shortcut/only.md"))
    return


def test_a_missing_root_or_index_is_a_configuration_error():
    """
        **Feature: book library configuration**
        **Property: a root folder that does not exist and a root with no index document both raise ConfigurationError; another index document can be
        named.**
    """
    with tempfile.TemporaryDirectory() as root:
        missing_root_error = None
        try:
            BookLibrary(os.path.join(root, "does-not-exist"))
        except ConfigurationError as err:
            missing_root_error = type(err).__name__

        missing_index_error = None
        try:
            BookLibrary(root)
        except ConfigurationError as err:
            missing_index_error = type(err).__name__

        write_sample_library(root)
        library = BookLibrary(root, index_document="series.md")
        index_document = library.index_document

    testbase.assert_equal(
        (missing_root_error, missing_index_error, index_document),
        ("ConfigurationError", "ConfigurationError", "series.md"),
    )
    return


def test_the_navigation_follows_edits_to_the_index_documents():
    """
        **Feature: book library navigation**
        **Property: after the library index changes on disk, the books follow the new links without a restart.**
    """
    with tempfile.TemporaryDirectory() as root:
        write_sample_library(root)
        library = BookLibrary(root)
        before = [book.title for book in library.books()]

        index_path = os.path.join(root, "README.md")
        with open(index_path, "w", encoding="utf-8") as index_file:
            index_file.write("# The Library\n\n1. [Volume Two First](volumes/two/)\n")
        later = time.time() + 10
        os.utime(index_path, (later, later))

        after = [book.title for book in library.books()]

    testbase.assert_equal((before, after), (["First Volume", "Second Volume", "series plan"], ["Volume Two First"]))
    return


def test_the_library_title_is_the_index_title_unless_one_is_given():
    """
        **Feature: book library title**
        **Property: the library's title is its index document's title, and a title given to the library wins.**
    """
    with tempfile.TemporaryDirectory() as root:
        write_sample_library(root)
        titles = (BookLibrary(root).library_title(), BookLibrary(root, title="Code Craft AI Books").library_title())

    testbase.assert_equal(titles, ("The Library", "Code Craft AI Books"))
    return
