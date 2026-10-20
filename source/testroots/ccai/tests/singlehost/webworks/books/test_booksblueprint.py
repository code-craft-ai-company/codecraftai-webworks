"""
    Tests for the blueprint that serves a library of markdown books.

    The blueprint's routes are registered on a real router and requests go through a real dispatcher, so the tests see
    exactly what a browser would get: pages with navigation from the index documents, rewritten links, redirects to
    canonical URLs, images, the stylesheet, and 404 pages for everything outside the library.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []

import re
import tempfile

from typing import Callable, Dict, List, Tuple

from ccai import testbase

from ccai.errors.exceptions import SemanticError

from ccai.testshared.books.librarysample import SAMPLE_IMAGE_BYTES, write_sample_library

from ccai.webworks.books import BookLibrary, BooksBlueprint
from ccai.webworks.routing.dispatcher import Dispatcher
from ccai.webworks.routing.request import Request
from ccai.webworks.routing.response import Response
from ccai.webworks.routing.router import Router


def _serve(root: str, *, mount_path: str = "/books", strict_slashes: bool = True) -> Callable[[str], Response]:
    """
        Builds the sample library's blueprint on a router and returns a function that GETs a path.
    """
    library = BookLibrary(root)
    books = BooksBlueprint(library, mount_path=mount_path)
    router = Router(strict_slashes=strict_slashes)
    BooksBlueprint.register(router=router, instance=books)
    dispatcher = Dispatcher(router=router)

    def get(path: str) -> Response:
        response = dispatcher.dispatch(Request(method="GET", path=path))
        return response

    return get


def _section(page: str, css_class: str) -> str:
    """
        The ``<nav>`` of a page with a class, or the empty string.
    """
    match = re.search(r'<nav class="{}".*?</nav>'.format(css_class), page, re.S)
    if match is None:
        return ""
    rtnval = match.group(0)
    return rtnval


def _links(html: str) -> List[Tuple[str, str]]:
    """
        The ``(href, text)`` of every link in some HTML, with the markers of the current link kept in the href.
    """
    rtnval = re.findall(r'<a\b[^>]*?\bhref="([^"]*)"[^>]*>(.*?)</a>', html, re.S)
    return rtnval


def test_the_library_page_lists_the_books_from_the_library_index():
    """
        **Feature: books blueprint**
        **Property: the mount path with and without a trailing slash serves the library index rendered as a page whose contents are the books in link
        order, and the index's own location redirects to the mount path.**
    """
    with tempfile.TemporaryDirectory() as root:
        write_sample_library(root)
        get = _serve(root)
        bare = get("/books")
        slashed = get("/books/")
        index = get("/books/README.md")

    page = slashed.body.decode("utf-8")
    testbase.assert_equal(
        (
            bare.status_code, slashed.status_code, "<h1 id=\"the-library\">The Library</h1>" in page,
            _links(_section(page, "books-contents")),
            index.status_code, index.headers.get("Location"),
        ),
        (
            200, 200, True,
            [
                ("/books/volumes/one/README.md", "First Volume"),
                ("/books/volumes/two/index.md", "Second Volume"),
                ("/books/series.md", "series plan"),
            ],
            302, "/books/",
        ),
    )
    return


def test_a_chapter_page_shows_its_book_breadcrumbs_neighbours_and_outline():
    """
        **Feature: books blueprint**
        **Property: a chapter's page lists its book's reading order with the chapter marked current, has breadcrumbs from the library through the book,
        links to the book index as previous and the next entry as next, and outlines its second- and third-level headings.**
    """
    with tempfile.TemporaryDirectory() as root:
        write_sample_library(root)
        get = _serve(root)
        response = get("/books/volumes/one/chapters/01-start.md")

    page = response.body.decode("utf-8")
    breadcrumbs = re.findall(r"<li(?: aria-current=\"page\")?>(?:<a href=\"[^\"]*\">)?([^<]*)", _section(page, "books-breadcrumbs"))
    testbase.assert_equal(
        (
            response.status_code,
            re.findall(r'<li><a href="([^"]*)"( aria-current="page")?>', _section(page, "books-contents")),
            breadcrumbs,
            _links(_section(page, "books-pager")),
            _links(_section(page, "books-outline")),
        ),
        (
            200,
            [
                ("/books/volumes/one/README.md", ""),
                ("/books/volumes/one/chapters/01-start.md", ' aria-current="page"'),
                ("/books/volumes/one/chapters/02-further.md", ""),
                ("/books/volumes/one/appendix/a.md", ""),
            ],
            ["The Library", "First Volume", "Getting Started"],
            [
                ("/books/volumes/one/README.md", "<span>Previous</span> First Volume"),
                ("/books/volumes/one/chapters/02-further.md", "<span>Next</span> Going Further"),
            ],
            [("#setup", "Setup"), ("#details-of-setup", "Details of setup")],
        ),
    )
    return


def test_links_between_markdown_files_become_site_urls():
    """
        **Feature: books blueprint**
        **Property: relative and root-relative links to documents and images of the library are rewritten to the URLs they are served at, keeping their
        fragments, while a link that leads out of the library is left as written.**
    """
    with tempfile.TemporaryDirectory() as root:
        write_sample_library(root)
        get = _serve(root)
        page = get("/books/volumes/one/chapters/01-start.md").body.decode("utf-8")

    article = re.search(r'<article class="books-article">(.*?)</article>', page, re.S).group(1)
    testbase.assert_equal(
        (re.findall(r'(?:href|src)="([^"]*)"', article)),
        [
            "/books/volumes/one/figures/diagram.png",
            "/books/volumes/one/chapters/02-further.md#details",
            "/books/series.md",
            "../../../../elsewhere/code.py",
        ],
    )
    return


def test_folders_and_non_canonical_locations_redirect_to_the_document():
    """
        **Feature: books blueprint**
        **Property: a folder redirects to its index document and a location with empty parts or ``.`` redirects to its canonical URL.**
    """
    with tempfile.TemporaryDirectory() as root:
        write_sample_library(root)
        get = _serve(root)
        responses = [get("/books/volumes/one/"), get("/books/volumes/two"), get("/books/volumes//one/./README.md")]

    testbase.assert_equal(
        [(response.status_code, response.headers.get("Location")) for response in responses],
        [
            (302, "/books/volumes/one/README.md"),
            (302, "/books/volumes/two/index.md"),
            (302, "/books/volumes/one/README.md"),
        ],
    )
    return


def test_images_and_the_stylesheet_are_served_with_their_types():
    """
        **Feature: books blueprint**
        **Property: an image of the library is served with its content type and a sandboxing Content-Security-Policy, and the stylesheet is served as
        CSS.**
    """
    with tempfile.TemporaryDirectory() as root:
        write_sample_library(root)
        get = _serve(root)
        image = get("/books/volumes/one/figures/diagram.png")
        stylesheet = get("/books/_books/books.css")

    testbase.assert_equal(
        (
            image.status_code, image.headers.get("Content-Type"), image.body, "sandbox" in image.headers.get("Content-Security-Policy", ""),
            stylesheet.status_code, stylesheet.headers.get("Content-Type"), b".books-layout" in stylesheet.body,
        ),
        (200, "image/png", SAMPLE_IMAGE_BYTES, True, 200, "text/css; charset=utf-8", True),
    )
    return


def test_locations_outside_the_library_are_not_found():
    """
        **Feature: books blueprint**
        **Property: climbing out of the root, a hidden file, a file that is neither a document nor an image, a missing document and an unknown file under
        the reserved ``_books`` path all get a 404 page.**
    """
    with tempfile.TemporaryDirectory() as root:
        write_sample_library(root)
        get = _serve(root)
        statuses = []
        for path in ("/books/../README.md", "/books/volumes/../../etc/passwd", "/books/.hidden/secret.md", "/books/notes.txt",
                     "/books/volumes/one/chapters/missing.md", "/books/_books/other.css"):
            statuses.append(get(path).status_code)

    testbase.assert_equal(statuses, [404, 404, 404, 404, 404, 404])
    return


def test_pages_hold_no_script_and_forbid_scripts():
    """
        **Feature: books blueprint**
        **Property: library, book, chapter and not-found pages contain no ``<script>`` and carry a Content-Security-Policy whose default is 'none' and
        that allows styles from the site only.**
    """
    with tempfile.TemporaryDirectory() as root:
        write_sample_library(root)
        get = _serve(root)
        responses = [get("/books/"), get("/books/volumes/one/README.md"), get("/books/volumes/one/chapters/01-start.md"), get("/books/nope.md")]

    checks = []
    for response in responses:
        policy = response.headers.get("Content-Security-Policy", "")
        checks.append(("<script" in response.body.decode("utf-8"), "default-src 'none'" in policy, "style-src 'self'" in policy))

    testbase.assert_equal(checks, [(False, True, True)] * 4)
    return


def test_the_library_can_be_mounted_at_the_root_of_a_site():
    """
        **Feature: books blueprint**
        **Property: mounted at ``/``, the library page is ``/`` and documents are served from the root.**
    """
    with tempfile.TemporaryDirectory() as root:
        write_sample_library(root)
        get = _serve(root, mount_path="/")
        library_page = get("/")
        chapter = get("/volumes/two/only.md")

    testbase.assert_equal(
        (library_page.status_code, chapter.status_code, '<link rel="stylesheet" href="/_books/books.css">' in chapter.body.decode("utf-8")),
        (200, 200, True),
    )
    return


def test_a_router_without_strict_slashes_gets_one_library_route():
    """
        **Feature: books blueprint**
        **Property: on a router that treats ``/books`` and ``/books/`` as one path, the library page is registered once, so registration does not
        conflict, and both addresses are served.**
    """
    with tempfile.TemporaryDirectory() as root:
        write_sample_library(root)
        get = _serve(root, strict_slashes=False)
        statuses = (get("/books").status_code, get("/books/").status_code)

    testbase.assert_equal(statuses, (200, 200))
    return


def test_registering_the_class_without_an_instance_is_a_semantic_error():
    """
        **Feature: books blueprint**
        **Property: the blueprint is configured when it is created, so registering the class alone raises SemanticError instead of registering
        nothing.**
    """
    error_name = None
    try:
        BooksBlueprint.register(router=Router())
    except SemanticError as err:
        error_name = type(err).__name__

    testbase.assert_equal(error_name, "SemanticError")
    return


class _RecordingWebApplication:
    """
        Stands in for a web application and records the routes attached to it.
    """

    def __init__(self) -> None:
        """
            Creates the stand-in with no routes.
        """
        self.routes: Dict[str, List[str]] = {}
        return

    def attach_route(self, path: str, methods: List[str]) -> Callable:
        """
            Records a route the way WebApplication.attach_route registers one.

            :param path: The route's path.
            :param methods: The route's methods.

            :returns: A decorator that records the handler's route.
        """

        def decorator(handler: Callable) -> Callable:
            self.routes[path] = methods
            return handler

        return decorator


def test_attaching_to_a_web_application_attaches_every_route():
    """
        **Feature: books blueprint**
        **Property: attach_to_webapp attaches the library page with and without a trailing slash, the stylesheet route and the document route, all for
        GET.**
    """
    with tempfile.TemporaryDirectory() as root:
        write_sample_library(root)
        books = BooksBlueprint(BookLibrary(root), mount_path="/library")
        webapp = _RecordingWebApplication()
        books.attach_to_webapp(webapp)

    testbase.assert_equal(
        webapp.routes,
        {
            "/library": ["GET"],
            "/library/": ["GET"],
            "/library/_books/{asset}": ["GET"],
            "/library/{document:path}": ["GET"],
        },
    )
    return
