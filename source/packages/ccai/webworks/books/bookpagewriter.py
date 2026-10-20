"""
.. module:: bookpagewriter
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Writes a :class:`BookPage` as a complete HTML page.

.. moduleauthor:: Code Craft AI LLC

The page is a header with the library's name and a trail of breadcrumbs, the book's contents on the left, the document
in the middle with links to the previous and next documents under it, and the document's headings on the right. The
page holds no script and no inline style, so it works under a Content-Security-Policy of ``default-src 'none';
style-src 'self'``. Every value is escaped except the document's HTML, which comes from the markdown renderer.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []

import html

from typing import List

from ccai.webworks.books.booknavlink import BookNavLink
from ccai.webworks.books.bookpage import BookPage


def _escape(value: str) -> str:
    """
        Escapes a value for element content or a double-quoted attribute.

        :param value: The value.

        :returns: The escaped value.
    """
    rtnval = html.escape(value, quote=True)
    return rtnval


class BookPageWriter:
    """
        Writes book pages as HTML.
    """

    def write(self, page: BookPage) -> str:
        """
            Writes a page.

            :param page: The page.

            :returns: The HTML document.
        """
        lines: List[str] = [
            "<!DOCTYPE html>",
            '<html lang="en">',
            "<head>",
            '    <meta charset="UTF-8">',
            '    <meta name="viewport" content="width=device-width, initial-scale=1.0">',
            "    <title>{}</title>".format(_escape(self._document_title(page))),
            '    <link rel="stylesheet" href="{}">'.format(_escape(page.stylesheet_url)),
            "</head>",
            '<body class="books">',
        ]

        self._write_header(page, lines)

        lines.append('<div class="books-layout">')
        self._write_contents(page, lines)

        lines.append('    <main class="books-main">')
        lines.append('        <article class="books-article">')
        lines.append(page.content_html)
        lines.append("        </article>")
        self._write_pager(page, lines)
        lines.append("    </main>")

        self._write_outline(page, lines)
        lines.append("</div>")
        lines.append("</body>")
        lines.append("</html>")
        lines.append("")

        rtnval = "\n".join(lines)
        return rtnval

    def _document_title(self, page: BookPage) -> str:
        """
            The text of the page's ``<title>``.

            :param page: The page.

            :returns: The title.
        """
        if page.title == page.library_title:
            rtnval = page.title
        else:
            rtnval = "{} - {}".format(page.title, page.library_title)
        return rtnval

    def _write_header(self, page: BookPage, lines: List[str]) -> None:
        """
            Writes the header: the library's name and the breadcrumbs from the library to the page.

            :param page: The page.
            :param lines: The lines written so far.
        """
        lines.append('<header class="books-header">')
        lines.append('    <a class="books-library" href="{}">{}</a>'.format(_escape(page.library_url), _escape(page.library_title)))

        if len(page.breadcrumbs) > 0:
            lines.append('    <nav class="books-breadcrumbs" aria-label="Breadcrumbs">')
            lines.append("        <ol>")
            for crumb in page.breadcrumbs:
                if crumb.current:
                    lines.append('            <li aria-current="page">{}</li>'.format(_escape(crumb.title)))
                else:
                    lines.append('            <li><a href="{}">{}</a></li>'.format(_escape(crumb.url), _escape(crumb.title)))
            lines.append("        </ol>")
            lines.append("    </nav>")

        lines.append("</header>")
        return

    def _write_contents(self, page: BookPage, lines: List[str]) -> None:
        """
            Writes the contents: the book's reading order, or the library's books on the library page.

            :param page: The page.
            :param lines: The lines written so far.
        """
        if len(page.contents) == 0:
            return

        lines.append('    <nav class="books-contents" aria-label="Contents">')
        if page.book is not None:
            lines.append('        <p class="books-contents-title"><a href="{}">{}</a></p>'.format(_escape(page.book.url),
                                                                                                 _escape(page.book.title)))
        else:
            lines.append('        <p class="books-contents-title">Books</p>')

        lines.append("        <ol>")
        for link in page.contents:
            lines.append("            <li>{}</li>".format(self._link(link)))
        lines.append("        </ol>")
        lines.append("    </nav>")
        return

    def _write_pager(self, page: BookPage, lines: List[str]) -> None:
        """
            Writes the links to the previous and next documents of the book.

            :param page: The page.
            :param lines: The lines written so far.
        """
        if page.previous is None and page.next is None:
            return

        lines.append('        <nav class="books-pager" aria-label="Previous and next">')
        if page.previous is not None:
            lines.append('            <a class="books-pager-previous" rel="prev" href="{}"><span>Previous</span> {}</a>'.format(
                _escape(page.previous.url), _escape(page.previous.title)))
        if page.next is not None:
            lines.append('            <a class="books-pager-next" rel="next" href="{}"><span>Next</span> {}</a>'.format(
                _escape(page.next.url), _escape(page.next.title)))
        lines.append("        </nav>")
        return

    def _write_outline(self, page: BookPage, lines: List[str]) -> None:
        """
            Writes the links to the page's own headings.

            :param page: The page.
            :param lines: The lines written so far.
        """
        if len(page.outline) == 0:
            return

        lines.append('    <nav class="books-outline" aria-label="On this page">')
        lines.append('        <p class="books-outline-title">On this page</p>')
        lines.append("        <ol>")
        for link in page.outline:
            lines.append('            <li class="books-outline-level-{}"><a href="{}">{}</a></li>'.format(
                link.level, _escape(link.url), _escape(link.title)))
        lines.append("        </ol>")
        lines.append("    </nav>")
        return

    def _link(self, link: BookNavLink) -> str:
        """
            Writes a navigation link; the link to the page being shown is marked ``aria-current``.

            :param link: The link.

            :returns: The HTML.
        """
        if link.current:
            rtnval = '<a href="{}" aria-current="page">{}</a>'.format(_escape(link.url), _escape(link.title))
        else:
            rtnval = '<a href="{}">{}</a>'.format(_escape(link.url), _escape(link.title))
        return rtnval
