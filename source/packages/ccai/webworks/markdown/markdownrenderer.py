"""
.. module:: markdownrenderer
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Renders markdown text as HTML.

.. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []

from typing import Callable, List, Optional

from ccai.webworks.markdown.blockparser import BlockParser
from ccai.webworks.markdown.htmlwriter import HtmlWriter
from ccai.webworks.markdown.markdowndocument import MarkdownDocument
from ccai.webworks.markdown.markdownheading import MarkdownHeading


class MarkdownRenderer:
    """
        Renders markdown text as HTML.

        The renderer covers CommonMark (headings, paragraphs, emphasis, code, block quotes, lists, links, images,
        thematic breaks) and the GitHub extensions that documentation relies on: tables, strikethrough and links made
        from bare addresses. Raw HTML in the markdown is escaped rather than passed through, and link destinations with
        unsafe schemes are dropped, so the HTML is safe to put in a page.

        A site can shape the HTML with two hooks: a code block writer that writes the HTML of each code block (to
        highlight it, label it or hide some of its lines), and a paragraph classifier that gives a paragraph a class.

        Rendering is stateless; one renderer may be shared.
    """

    def __init__(self, *, code_block_writer: Optional[Callable[[str, str], str]] = None,
                 paragraph_classifier: Optional[Callable[[str], Optional[str]]] = None):
        """
            Creates a renderer.

            :param code_block_writer: Called with the code and the info string (empty for an indented block) of every
                                      code block; what it returns is written as the block's HTML, as it is, so it must
                                      escape the code itself. None writes ``<pre><code class="language-...">``.
            :param paragraph_classifier: Called with the markdown source of every paragraph written with ``<p>``; a name
                                         it returns becomes the paragraph's ``class``, and None leaves it without one.
        """
        self._code_block_writer = code_block_writer
        self._paragraph_classifier = paragraph_classifier
        return

    def render(self, text: str, *, link_rewriter: Optional[Callable[[str], Optional[str]]] = None) -> MarkdownDocument:
        """
            Renders markdown text.

            :param text: The markdown.
            :param link_rewriter: Called with the destination of every link and image, as written; what it returns is
                                  written in its place. A site uses it to turn the relative paths between markdown files
                                  into the URLs it serves them at. Returning None drops the link and keeps its text
                                  (an image keeps its description).

            :returns: The HTML with the document's title, headings, links and paragraphs.
        """
        parser = BlockParser()
        blocks = parser.parse(text)

        writer = HtmlWriter(definitions=parser.definitions, link_rewriter=link_rewriter,
                            code_block_writer=self._code_block_writer, paragraph_classifier=self._paragraph_classifier)
        html_text = writer.write(blocks)

        headings = tuple(writer.headings)
        links = tuple(writer.links)
        paragraphs = tuple(writer.paragraphs)
        title = self._choose_title(writer.headings)

        rtnval = MarkdownDocument(html=html_text, title=title, headings=headings, links=links, paragraphs=paragraphs)
        return rtnval

    def _choose_title(self, headings: List[MarkdownHeading]) -> Optional[str]:
        """
            The title of a document: its first level-one heading, else its first heading.

            :param headings: The document's headings.

            :returns: The title, or None when there are no headings.
        """
        for heading in headings:
            if heading.level == 1:
                return heading.text

        if len(headings) > 0:
            first = headings[0]
            rtnval = first.text
            return rtnval

        return None
