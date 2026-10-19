"""
.. module:: booksblueprint
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Blueprint that serves a library of markdown books as HTML pages.

.. moduleauthor:: Code Craft AI LLC

:class:`BooksBlueprint` serves a :class:`BookLibrary` under a mount path (``/books`` by default):

- ``/books/`` is the library's index document, with the list of books beside it
- ``/books/<location>`` is a document of the library, rendered with the contents of its book, breadcrumbs, links to the
  previous and next documents and an outline of its headings; or an image of the library
- ``/books/_books/books.css`` is the stylesheet of the pages

Links between the markdown files are rewritten to the URLs the documents are served at, so a library reads the same on
the site as it does in the repository. Pages carry a Content-Security-Policy that allows no script at all.

Example::

    from ccai.webworks.books import BookLibrary, BooksBlueprint

    library = BookLibrary("~/repos/codecraftai-books")
    books = BooksBlueprint(library, mount_path="/books")
    books.attach_to_webapp(webapp)
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []

import os
import posixpath
import urllib.parse

from typing import Dict, List, Optional, TYPE_CHECKING

from ccai.errors.exceptions import SemanticError

from ccai.webworks.books.booklibrary import BookLibrary
from ccai.webworks.books.booknavlink import BookNavLink
from ccai.webworks.books.bookpage import BookPage
from ccai.webworks.books.bookpagewriter import BookPageWriter
from ccai.webworks.endpoints.descriptor import EndpointDescriptor
from ccai.webworks.endpoints.doc import Doc
from ccai.webworks.endpoints.restblueprint import RestBlueprint, Router
from ccai.webworks.markdown.markdowndocument import MarkdownDocument
from ccai.webworks.routing.request import Request
from ccai.webworks.routing.response import HTMLResponse, RedirectResponse, Response
from ccai.webworks.routing.router import Router as RoutingRouter

if TYPE_CHECKING:
    from ccai.webworks.webapplication import WebApplication

#: The path segment, under the mount path, that the blueprint's own files are served from. A library file under a
#: folder of this name cannot be reached.
BOOKS_RESERVED_SEGMENT = "_books"

#: The file name of the pages' stylesheet.
BOOKS_STYLESHEET_NAME = "books.css"

#: Where the stylesheet is inside the package.
BOOKS_STYLESHEET_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", BOOKS_STYLESHEET_NAME)

#: The Content-Security-Policy of a page. ``{styles}`` is where the stylesheet may come from.
BOOKS_PAGE_SECURITY_POLICY = (
    "default-src 'none'; style-src {styles}; img-src 'self' data: https:; base-uri 'none'; form-action 'none'; "
    "frame-ancestors 'self'"
)

#: The Content-Security-Policy of an image, so an SVG opened on its own cannot run a script.
BOOKS_ASSET_SECURITY_POLICY = "default-src 'none'; style-src 'unsafe-inline'; sandbox"

#: The status of the redirect from a folder or a non-canonical location to a document's URL.
BOOKS_REDIRECT_STATUS = 302


class BooksBlueprint(RestBlueprint):
    """
        Blueprint that serves a library of markdown books as HTML pages.

        The blueprint is configured when it is created, so its routes are registered from an instance: with
        :meth:`attach_to_webapp`, or with ``BooksBlueprint.register(router=router, instance=books)``.

        :param library: The library to serve.
        :param mount_path: The URL path the library is served under. ``/`` serves it at the root of the site.
        :param stylesheet_url: The URL of the pages' stylesheet; None serves the blueprint's own stylesheet. A
                               stylesheet on another host is allowed by the pages' Content-Security-Policy.
    """

    def __init__(self, library: BookLibrary, *, mount_path: str = "/books", stylesheet_url: Optional[str] = None):
        """
            Creates the blueprint.

            :param library: The library to serve.
            :param mount_path: The URL path the library is served under; ``/`` serves it at the root of the site.
            :param stylesheet_url: The URL of the pages' stylesheet; None serves the blueprint's own stylesheet.
        """
        stripped = mount_path.strip("/")
        if stripped == "":
            prefix = ""
        else:
            prefix = "/{}".format(stripped)

        self._library = library
        self._prefix = prefix

        if stylesheet_url is None:
            self._stylesheet_url = "{}/{}/{}".format(prefix, BOOKS_RESERVED_SEGMENT, BOOKS_STYLESHEET_NAME)
        else:
            self._stylesheet_url = stylesheet_url

        self._page_security_policy = self._build_page_security_policy(stylesheet_url)
        self._page_writer = BookPageWriter()

        with open(BOOKS_STYLESHEET_FILE, "rb") as stylesheet_file:
            self._stylesheet = stylesheet_file.read()

        return

    @property
    def library(self) -> BookLibrary:
        """
            The library the blueprint serves.
        """
        return self._library

    @property
    def mount_path(self) -> str:
        """
            The URL path the library is served under (``/`` at the root of the site).
        """
        if self._prefix == "":
            return "/"
        return self._prefix

    def library_url(self) -> str:
        """
            The URL of the library's index page.

            :returns: The URL.
        """
        rtnval = "{}/".format(self._prefix)
        return rtnval

    def url_for(self, location: str) -> str:
        """
            The URL a document or image of the library is served at.

            :param location: The canonical location of the document or image.

            :returns: The URL. The library's index document is served at :meth:`library_url`.
        """
        if location == self._library.index_document:
            rtnval = self.library_url()
            return rtnval

        quoted = urllib.parse.quote(location, safe="/")
        rtnval = "{}/{}".format(self._prefix, quoted)
        return rtnval

    def serve_library(self, request: Request) -> Response:
        """
            Serves the library's index page.

            :param request: The request.

            :returns: The page.
        """
        rtnval = self._document_response(self._library.index_document)
        return rtnval

    def serve_document(self, request: Request) -> Response:
        """
            Serves a document or an image of the library. A folder, or a location that is not written the canonical
            way, is redirected to the document's URL.

            :param request: The request; its ``document`` path parameter is the location in the library.

            :returns: The page, the image, a redirect, or a page that says the location is not in the library.
        """
        requested = request.path_params.get("document", "")
        canonical = self._library.canonical_location(requested)
        if canonical is None:
            rtnval = self._not_found_response()
            return rtnval

        document = self._library.resolve_document(canonical)
        if document is not None:
            if document == self._library.index_document or document != requested:
                target = self.url_for(document)
                rtnval = RedirectResponse(url=target, status_code=BOOKS_REDIRECT_STATUS)
                return rtnval
            rtnval = self._document_response(document)
            return rtnval

        asset = self._library.resolve_asset(canonical)
        if asset is not None:
            rtnval = self._asset_response(asset)
            return rtnval

        rtnval = self._not_found_response()
        return rtnval

    def serve_stylesheet(self, request: Request) -> Response:
        """
            Serves the pages' stylesheet.

            :param request: The request; its ``asset`` path parameter is the file name.

            :returns: The stylesheet, or a page that says the file is not here.
        """
        asset = request.path_params.get("asset", "")
        if asset != BOOKS_STYLESHEET_NAME:
            rtnval = self._not_found_response()
            return rtnval

        headers = {
            "Content-Type": "text/css; charset=utf-8",
            "Cache-Control": "public, max-age=3600",
            "X-Content-Type-Options": "nosniff",
        }
        rtnval = Response(status_code=200, headers=headers, body=self._stylesheet)
        return rtnval

    def get_descriptors(self, *, include_trailing_slash: bool = True) -> List[EndpointDescriptor]:
        """
            The endpoint descriptors of the blueprint's routes: the library page, the stylesheet and the documents.

            :param include_trailing_slash: Whether to register the library page under the mount path with a trailing
                                           slash as well as without one, for a router that tells the two apart
                                           (``strict_slashes``).

            :returns: The descriptors.
        """
        module = self.__class__.__module__

        if self._prefix == "":
            library_paths = ["/"]
        else:
            library_paths = [self._prefix]
            if include_trailing_slash:
                library_paths.append("{}/".format(self._prefix))

        descriptors: List[EndpointDescriptor] = []
        for library_path in library_paths:
            descriptors.append(EndpointDescriptor(
                handler=self.serve_library,
                module=module,
                path=library_path,
                methods=["GET"],
                tags=["books"],
                doc=Doc(summary="Book library", description="The library's index page and its list of books."),
            ))

        descriptors.append(EndpointDescriptor(
            handler=self.serve_stylesheet,
            module=module,
            path="{}/{}/{{asset}}".format(self._prefix, BOOKS_RESERVED_SEGMENT),
            methods=["GET"],
            tags=["books"],
            doc=Doc(summary="Book page stylesheet", description="The stylesheet of the book pages."),
        ))

        descriptors.append(EndpointDescriptor(
            handler=self.serve_document,
            module=module,
            path="{}/{{document:path}}".format(self._prefix),
            methods=["GET"],
            tags=["books"],
            doc=Doc(summary="Book document", description="A markdown document of the library rendered as HTML, or an image."),
        ))

        return descriptors

    def attach_to_webapp(self, webapp: "WebApplication") -> None:
        """
            Registers the blueprint's routes on a web application, before or after it starts.

            :param webapp: The web application.
        """
        descriptors = self.get_descriptors(include_trailing_slash=True)
        for descriptor in descriptors:
            decorator = webapp.attach_route(descriptor.path, methods=descriptor.methods)
            decorator(descriptor.handler)
        return

    @classmethod
    def register(cls, router: Optional[Router] = None, instance: Optional["BooksBlueprint"] = None) -> List[EndpointDescriptor]:
        """
            Registers the routes of a blueprint instance and returns their descriptors.

            :param router: The router to add the routes to; None only returns the descriptors.
            :param instance: The configured blueprint.

            :returns: The descriptors.

            :raises: SemanticError when no instance is given: the blueprint is configured when it is created, so the
                     class alone (``webapp.attach_blueprint_to_route(BooksBlueprint)``) has no routes to register.
        """
        if instance is None:
            err_msg_lines = [
                "BooksBlueprint.register() needs the configured blueprint as 'instance'.",
                "The blueprint is configured with a BookLibrary when it is created, so the class alone has no routes.",
                "Use 'books.attach_to_webapp(webapp)' or 'BooksBlueprint.register(router=router, instance=books)'.",
            ]
            err_msg = os.linesep.join(err_msg_lines)
            raise SemanticError(err_msg)

        include_trailing_slash = True
        if isinstance(router, RoutingRouter):
            include_trailing_slash = router.strict_slashes

        descriptors = instance.get_descriptors(include_trailing_slash=include_trailing_slash)

        if router is not None:
            for descriptor in descriptors:
                router.add_endpoint(descriptor)

        return descriptors

    def _build_page_security_policy(self, stylesheet_url: Optional[str]) -> str:
        """
            The Content-Security-Policy of the pages, allowing the stylesheet's host when it is on another one.

            :param stylesheet_url: The stylesheet URL the blueprint was given, or None for its own.

            :returns: The policy.
        """
        styles = "'self'"
        if stylesheet_url is not None:
            split = urllib.parse.urlsplit(stylesheet_url)
            if split.scheme != "" and split.netloc != "":
                styles = "'self' {}://{}".format(split.scheme, split.netloc)

        rtnval = BOOKS_PAGE_SECURITY_POLICY.format(styles=styles)
        return rtnval

    def _page_headers(self) -> Dict[str, str]:
        """
            The headers of a page.

            :returns: The headers.
        """
        rtnval = {
            "Content-Security-Policy": self._page_security_policy,
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "no-cache",
        }
        return rtnval

    def _rewrite_destination(self, *, document: str, destination: str) -> str:
        """
            The URL to write for a link or image in a document: documents and images of the library become the URLs
            they are served at; fragments, addresses on other sites and paths that lead out of the library are left as
            they are.

            :param document: The location of the document the link is in.
            :param destination: The destination as written.

            :returns: The URL to write.
        """
        if destination.strip().startswith("#"):
            return destination

        resolved = self._library.resolve_link(document=document, destination=destination)
        if resolved is None:
            return destination

        location, fragment = resolved
        url = self.url_for(location)
        if fragment != "":
            url = "{}#{}".format(url, fragment)

        rtnval = url
        return rtnval

    def _document_response(self, document: str) -> Response:
        """
            Renders a document as a page.

            :param document: The canonical location of the document.

            :returns: The page.
        """

        def rewrite(destination: str) -> str:
            rewritten = self._rewrite_destination(document=document, destination=destination)
            return rewritten

        rendered = self._library.render_document(document, link_rewriter=rewrite)
        page = self._build_page(document=document, rendered=rendered)
        html_text = self._page_writer.write(page)

        rtnval = HTMLResponse(content=html_text, headers=self._page_headers())
        return rtnval

    def _build_page(self, *, document: str, rendered: MarkdownDocument) -> BookPage:
        """
            Gathers what the page of a document shows: the library and book it belongs to, the book's reading order,
            the previous and next documents and the document's headings.

            :param document: The canonical location of the document.
            :param rendered: The rendered document.

            :returns: The page.
        """
        library_title = self._library.library_title()
        library_url = self.library_url()

        if rendered.title is not None and rendered.title != "":
            title = rendered.title
        else:
            title = posixpath.basename(document)

        breadcrumbs: List[BookNavLink] = []
        contents: List[BookNavLink] = []
        book_link = None
        previous_link = None
        next_link = None

        if document == self._library.index_document:
            breadcrumbs.append(BookNavLink(title=library_title, url=library_url, current=True))
            for book in self._library.books():
                contents.append(BookNavLink(title=book.title, url=self.url_for(book.document)))
        else:
            breadcrumbs.append(BookNavLink(title=library_title, url=library_url))

            book = self._library.book_for(document)
            if book is not None:
                is_book_index = book.document == document
                book_url = self.url_for(book.document)
                book_link = BookNavLink(title=book.title, url=book_url, current=is_book_index)
                if not is_book_index:
                    breadcrumbs.append(BookNavLink(title=book.title, url=book_url))

                for entry in book.sequence():
                    is_current = entry.document == document
                    contents.append(BookNavLink(title=entry.title, url=self.url_for(entry.document), current=is_current))

                previous_entry, next_entry = book.neighbors(document)
                if previous_entry is not None:
                    previous_link = BookNavLink(title=previous_entry.title, url=self.url_for(previous_entry.document))
                if next_entry is not None:
                    next_link = BookNavLink(title=next_entry.title, url=self.url_for(next_entry.document))

            breadcrumbs.append(BookNavLink(title=title, url=self.url_for(document), current=True))

        outline: List[BookNavLink] = []
        for heading in rendered.headings:
            if heading.level == 2 or heading.level == 3:
                outline.append(BookNavLink(title=heading.text, url="#{}".format(heading.anchor), level=heading.level))

        rtnval = BookPage(
            title=title,
            library_title=library_title,
            library_url=library_url,
            stylesheet_url=self._stylesheet_url,
            content_html=rendered.html,
            breadcrumbs=tuple(breadcrumbs),
            book=book_link,
            contents=tuple(contents),
            previous=previous_link,
            next=next_link,
            outline=tuple(outline),
        )
        return rtnval

    def _asset_response(self, asset: str) -> Response:
        """
            Serves an image of the library.

            :param asset: The canonical location of the image.

            :returns: The image.
        """
        content = self._library.read_asset(asset)
        headers = {
            "Content-Type": self._library.asset_content_type(asset),
            "Content-Security-Policy": BOOKS_ASSET_SECURITY_POLICY,
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "no-cache",
        }
        rtnval = Response(status_code=200, headers=headers, body=content)
        return rtnval

    def _not_found_response(self) -> Response:
        """
            The page for a location that is not in the library.

            :returns: A page with status 404.
        """
        library_title = self._library.library_title()
        library_url = self.library_url()
        content_lines = [
            '<h1 id="not-found">Not found</h1>',
            "<p>This page is not in the library.</p>",
        ]
        page = BookPage(
            title="Not found",
            library_title=library_title,
            library_url=library_url,
            stylesheet_url=self._stylesheet_url,
            content_html="\n".join(content_lines),
            breadcrumbs=(
                BookNavLink(title=library_title, url=library_url),
                BookNavLink(title="Not found", url="", current=True),
            ),
        )
        html_text = self._page_writer.write(page)

        rtnval = HTMLResponse(content=html_text, status_code=404, headers=self._page_headers())
        return rtnval
