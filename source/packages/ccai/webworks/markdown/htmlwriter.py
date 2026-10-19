"""
.. module:: htmlwriter
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Writes parsed markdown blocks as HTML, collecting the document's headings and links on the way.

.. moduleauthor:: Code Craft AI LLC

Every piece of text from the markdown is escaped. Link and image destinations can be rewritten by the caller (to turn
``chapter-2.md`` into the URL a site serves it at), and a destination whose scheme is not ``http``, ``https``,
``mailto`` or ``ftp`` is dropped: such a link is written as its text alone and such an image as its description.

Two hooks let a site shape the HTML without taking over the parsing: a code block writer writes the HTML of each code
block (to highlight it, label it or hide some of its lines), and a paragraph classifier gives a paragraph a CSS class
(to style a caption, for example).
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []

import html
import re
import urllib.parse

from typing import Callable, Dict, List, Optional, Tuple

from ccai.webworks.markdown.blocknode import (
    BLOCK_KIND_BLOCKQUOTE,
    BLOCK_KIND_CODE,
    BLOCK_KIND_HEADING,
    BLOCK_KIND_LIST,
    BLOCK_KIND_PARAGRAPH,
    BLOCK_KIND_TABLE,
    BLOCK_KIND_THEMATIC_BREAK,
    TABLE_ALIGN_NONE,
    BlockNode,
)
from ccai.webworks.markdown.headingslugger import HeadingSlugger
from ccai.webworks.markdown.inlinenode import (
    INLINE_KIND_CODE,
    INLINE_KIND_EMPHASIS,
    INLINE_KIND_HARD_BREAK,
    INLINE_KIND_IMAGE,
    INLINE_KIND_LINK,
    INLINE_KIND_SOFT_BREAK,
    INLINE_KIND_STRIKETHROUGH,
    INLINE_KIND_STRONG,
    INLINE_KIND_TEXT,
    InlineNode,
)
from ccai.webworks.markdown.inlineparser import InlineParser
from ccai.webworks.markdown.markdownheading import MarkdownHeading
from ccai.webworks.markdown.markdownlink import MarkdownLink

#: The URL schemes a link or image may use. A destination without a scheme (relative, or a fragment) is always allowed.
MARKDOWN_SAFE_URL_SCHEMES = ("http", "https", "mailto", "ftp")

#: The characters left as they are when a destination is percent-encoded.
MARKDOWN_URL_SAFE_CHARACTERS = "%!#$&'()*+,/:;=?@[]~-._"

#: The scheme at the start of a URL.
MARKDOWN_URL_SCHEME_PATTERN = re.compile(r"^([A-Za-z][A-Za-z0-9+.\-]*):")

#: Characters a browser ignores inside a URL, removed before the scheme is checked.
MARKDOWN_URL_IGNORED_CHARACTERS_PATTERN = re.compile(r"[\x00-\x20\x7f]")


def is_safe_url(url: str) -> bool:
    """
        Whether a link or image destination is safe to write into a page: it has no scheme, or one of
        :data:`MARKDOWN_SAFE_URL_SCHEMES`. Characters a browser would ignore (such as a tab inside ``java\\tscript:``)
        are removed before the check.

        :param url: The destination.

        :returns: True when the destination is safe.
    """
    cleaned = MARKDOWN_URL_IGNORED_CHARACTERS_PATTERN.sub("", url)
    scheme_match = MARKDOWN_URL_SCHEME_PATTERN.match(cleaned)
    if scheme_match is None:
        return True

    scheme = scheme_match.group(1).lower()
    rtnval = scheme in MARKDOWN_SAFE_URL_SCHEMES
    return rtnval


def encode_url(url: str) -> str:
    """
        Percent-encodes the characters of a destination that may not appear in a URL as written (spaces and non-ASCII
        characters), leaving existing ``%xx`` escapes and URL punctuation alone.

        :param url: The destination.

        :returns: The encoded destination.
    """
    rtnval = urllib.parse.quote(url, safe=MARKDOWN_URL_SAFE_CHARACTERS)
    return rtnval


def escape_text(text: str) -> str:
    """
        Escapes text for an HTML element's content.

        :param text: The text.

        :returns: The escaped text.
    """
    rtnval = html.escape(text, quote=False)
    return rtnval


def escape_attribute(value: str) -> str:
    """
        Escapes a value for a double-quoted HTML attribute.

        :param value: The value.

        :returns: The escaped value.
    """
    rtnval = html.escape(value, quote=True)
    return rtnval


class HtmlWriter:
    """
        Writes the blocks of one document as HTML and collects its headings and links.
    """

    def __init__(self, *, definitions: Optional[Dict[str, Tuple[str, str]]] = None,
                 link_rewriter: Optional[Callable[[str], Optional[str]]] = None,
                 code_block_writer: Optional[Callable[[str, str], str]] = None,
                 paragraph_classifier: Optional[Callable[[str], Optional[str]]] = None):
        """
            Creates a writer for one document.

            :param definitions: The document's link reference definitions (see :attr:`BlockParser.definitions`).
            :param link_rewriter: Called with the destination of every link and image; what it returns is written in
                                  its place, and None drops the link (its text is kept) or the image (its description
                                  is kept). None writes destinations as they are.
            :param code_block_writer: Called with the code and the info string (empty for an indented block) of every
                                      code block; what it returns is written as the block's HTML, as it is, so it must
                                      escape the code itself. None writes ``<pre><code>``.
            :param paragraph_classifier: Called with the markdown source of every paragraph that is written with
                                         ``<p>``; a name it returns becomes the paragraph's ``class``.
        """
        self._definitions: Dict[str, Tuple[str, str]] = {}
        if definitions is not None:
            self._definitions = definitions
        self._link_rewriter = link_rewriter
        self._code_block_writer = code_block_writer
        self._paragraph_classifier = paragraph_classifier
        self._slugger = HeadingSlugger()
        self._headings: List[MarkdownHeading] = []
        self._links: List[MarkdownLink] = []
        self._paragraphs: List[str] = []
        return

    @property
    def headings(self) -> List[MarkdownHeading]:
        """
            The headings written so far, in document order.
        """
        return self._headings

    @property
    def links(self) -> List[MarkdownLink]:
        """
            The links written so far, in document order.
        """
        return self._links

    @property
    def paragraphs(self) -> List[str]:
        """
            The plain text of the paragraphs written so far, in document order.
        """
        return self._paragraphs

    def write(self, blocks: List[BlockNode]) -> str:
        """
            Writes blocks as HTML.

            :param blocks: The blocks of the document.

            :returns: The HTML.
        """
        parts: List[str] = []
        for block in blocks:
            self._write_block(block, parts, tight=False)

        rtnval = "".join(parts)
        return rtnval

    def _write_block(self, block: BlockNode, parts: List[str], *, tight: bool) -> None:
        """
            Writes one block.

            :param block: The block.
            :param parts: The HTML written so far; the block's HTML is appended.
            :param tight: Whether the block is directly inside an item of a tight list, where paragraphs are written
                          without ``<p>``.
        """
        if block.kind == BLOCK_KIND_PARAGRAPH:
            self._write_paragraph(block, parts, tight=tight)
        elif block.kind == BLOCK_KIND_HEADING:
            self._write_heading(block, parts)
        elif block.kind == BLOCK_KIND_THEMATIC_BREAK:
            parts.append("<hr />\n")
        elif block.kind == BLOCK_KIND_CODE:
            self._write_code(block, parts)
        elif block.kind == BLOCK_KIND_BLOCKQUOTE:
            parts.append("<blockquote>\n")
            for child in block.children:
                self._write_block(child, parts, tight=False)
            parts.append("</blockquote>\n")
        elif block.kind == BLOCK_KIND_LIST:
            self._write_list(block, parts)
        elif block.kind == BLOCK_KIND_TABLE:
            self._write_table(block, parts)
        else:
            errmsg = "The markdown block kind '{}' has no HTML writer.".format(block.kind)
            raise ValueError(errmsg)

        return

    def _write_paragraph(self, block: BlockNode, parts: List[str], *, tight: bool) -> None:
        """
            Writes a paragraph and records its plain text. Inside a tight list the paragraph is written without
            ``<p>``; otherwise the paragraph classifier may give it a class.

            :param block: The paragraph.
            :param parts: The HTML written so far.
            :param tight: Whether the paragraph is directly inside an item of a tight list.
        """
        nodes = self._parse_inline(block.text)
        self._paragraphs.append(self._plain_text(nodes))
        content = self._write_inline(nodes)

        if tight:
            parts.append(content + "\n")
            return

        css_class = None
        if self._paragraph_classifier is not None:
            css_class = self._paragraph_classifier(block.text)

        if css_class is not None and css_class != "":
            parts.append('<p class="{}">{}</p>\n'.format(escape_attribute(css_class), content))
        else:
            parts.append("<p>{}</p>\n".format(content))
        return

    def _write_heading(self, block: BlockNode, parts: List[str]) -> None:
        """
            Writes a heading with a unique anchor and records it.

            :param block: The heading.
            :param parts: The HTML written so far.
        """
        nodes = self._parse_inline(block.text)
        text = self._plain_text(nodes)
        anchor = self._slugger.slug(text)
        self._headings.append(MarkdownHeading(level=block.level, text=text, anchor=anchor))

        content = self._write_inline(nodes)
        parts.append('<h{level} id="{anchor}">{content}</h{level}>\n'.format(level=block.level, anchor=escape_attribute(anchor),
                                                                              content=content))
        return

    def _write_code(self, block: BlockNode, parts: List[str]) -> None:
        """
            Writes a code block: with the code block writer when there is one, otherwise as ``<pre><code>`` with the
            first word of the fence's info string, the language, written as a ``language-*`` class.

            :param block: The code block.
            :param parts: The HTML written so far.
        """
        if self._code_block_writer is not None:
            block_html = self._code_block_writer(block.text, block.info)
            parts.append(block_html)
            return

        info_words = block.info.split()
        if len(info_words) > 0:
            language = info_words[0]
            parts.append('<pre><code class="language-{}">'.format(escape_attribute(language)))
        else:
            parts.append("<pre><code>")

        parts.append(escape_text(block.text))
        parts.append("</code></pre>\n")
        return

    def _write_list(self, block: BlockNode, parts: List[str]) -> None:
        """
            Writes a bullet or ordered list. An ordered list that does not start at 1 says where it starts.

            :param block: The list.
            :param parts: The HTML written so far.
        """
        if block.ordered:
            if block.start != 1:
                parts.append('<ol start="{}">\n'.format(block.start))
            else:
                parts.append("<ol>\n")
            closing = "</ol>\n"
        else:
            parts.append("<ul>\n")
            closing = "</ul>\n"

        for item in block.children:
            item_parts: List[str] = []
            for child in item.children:
                self._write_block(child, item_parts, tight=block.tight)
            content = "".join(item_parts)
            if block.tight:
                content = content.rstrip("\n")
                parts.append("<li>{}</li>\n".format(content))
            else:
                parts.append("<li>\n{}</li>\n".format(content))

        parts.append(closing)
        return

    def _write_table(self, block: BlockNode, parts: List[str]) -> None:
        """
            Writes a table. A column's alignment is written as an ``align-*`` class, so a page whose
            Content-Security-Policy forbids inline styles still shows it.

            :param block: The table.
            :param parts: The HTML written so far.
        """
        parts.append("<table>\n<thead>\n<tr>\n")
        for index, cell in enumerate(block.header_cells):
            opening = self._cell_opening("th", block.alignments, index)
            parts.append("{}{}</th>\n".format(opening, self._write_inline_text(cell)))
        parts.append("</tr>\n</thead>\n")

        if len(block.body_rows) > 0:
            parts.append("<tbody>\n")
            for row in block.body_rows:
                parts.append("<tr>\n")
                for index, cell in enumerate(row):
                    opening = self._cell_opening("td", block.alignments, index)
                    parts.append("{}{}</td>\n".format(opening, self._write_inline_text(cell)))
                parts.append("</tr>\n")
            parts.append("</tbody>\n")

        parts.append("</table>\n")
        return

    def _cell_opening(self, tag: str, alignments: List[str], index: int) -> str:
        """
            The opening tag of a table cell, with the column's alignment class.

            :param tag: ``th`` or ``td``.
            :param alignments: The alignments of the columns.
            :param index: The column of the cell.

            :returns: The opening tag.
        """
        alignment = TABLE_ALIGN_NONE
        if index < len(alignments):
            alignment = alignments[index]

        if alignment == TABLE_ALIGN_NONE:
            rtnval = "<{}>".format(tag)
        else:
            rtnval = '<{} class="align-{}">'.format(tag, alignment)
        return rtnval

    def _parse_inline(self, text: str) -> List[InlineNode]:
        """
            Parses inline content.

            :param text: The content.

            :returns: The inline nodes.
        """
        parser = InlineParser(definitions=self._definitions)
        rtnval = parser.parse(text)
        return rtnval

    def _write_inline_text(self, text: str) -> str:
        """
            Parses and writes inline content.

            :param text: The content.

            :returns: The HTML.
        """
        nodes = self._parse_inline(text)
        rtnval = self._write_inline(nodes)
        return rtnval

    def _plain_text(self, nodes: List[InlineNode]) -> str:
        """
            The plain text of inline nodes.

            :param nodes: The nodes.

            :returns: The text.
        """
        parts = []
        for node in nodes:
            node_text = node.to_text()
            parts.append(node_text)
        rtnval = "".join(parts).strip()
        return rtnval

    def _write_inline(self, nodes: List[InlineNode]) -> str:
        """
            Writes inline nodes as HTML and records the links among them.

            :param nodes: The nodes.

            :returns: The HTML.
        """
        parts: List[str] = []
        for node in nodes:
            if node.kind == INLINE_KIND_TEXT:
                parts.append(escape_text(node.text))
            elif node.kind == INLINE_KIND_CODE:
                parts.append("<code>{}</code>".format(escape_text(node.text)))
            elif node.kind == INLINE_KIND_EMPHASIS:
                parts.append("<em>{}</em>".format(self._write_inline(node.children)))
            elif node.kind == INLINE_KIND_STRONG:
                parts.append("<strong>{}</strong>".format(self._write_inline(node.children)))
            elif node.kind == INLINE_KIND_STRIKETHROUGH:
                parts.append("<del>{}</del>".format(self._write_inline(node.children)))
            elif node.kind == INLINE_KIND_SOFT_BREAK:
                parts.append("\n")
            elif node.kind == INLINE_KIND_HARD_BREAK:
                parts.append("<br />\n")
            elif node.kind == INLINE_KIND_LINK:
                parts.append(self._write_link(node))
            elif node.kind == INLINE_KIND_IMAGE:
                parts.append(self._write_image(node))
            else:
                errmsg = "The inline node kind '{}' has no HTML writer.".format(node.kind)
                raise ValueError(errmsg)

        rtnval = "".join(parts)
        return rtnval

    def _resolve_destination(self, destination: str) -> Optional[str]:
        """
            The URL to write for a destination: rewritten by the caller's rewriter, checked and encoded.

            :param destination: The destination as written.

            :returns: The URL, or None when the rewriter dropped it or it is not safe to write.
        """
        target = destination
        if self._link_rewriter is not None:
            target = self._link_rewriter(destination)
            if target is None:
                return None

        if not is_safe_url(target):
            return None

        rtnval = encode_url(target)
        return rtnval

    def _write_link(self, node: InlineNode) -> str:
        """
            Writes a link and records it.

            :param node: The link node.

            :returns: The HTML.
        """
        text = self._plain_text(node.children)
        self._links.append(MarkdownLink(destination=node.destination, text=text))

        content = self._write_inline(node.children)
        href = self._resolve_destination(node.destination)
        if href is None:
            return content

        if node.title != "":
            rtnval = '<a href="{}" title="{}">{}</a>'.format(escape_attribute(href), escape_attribute(node.title), content)
        else:
            rtnval = '<a href="{}">{}</a>'.format(escape_attribute(href), content)
        return rtnval

    def _write_image(self, node: InlineNode) -> str:
        """
            Writes an image; its description becomes the ``alt`` text.

            :param node: The image node.

            :returns: The HTML.
        """
        description = self._plain_text(node.children)
        source = self._resolve_destination(node.destination)
        if source is None:
            rtnval = escape_text(description)
            return rtnval

        if node.title != "":
            rtnval = '<img src="{}" alt="{}" title="{}" />'.format(escape_attribute(source), escape_attribute(description),
                                                                   escape_attribute(node.title))
        else:
            rtnval = '<img src="{}" alt="{}" />'.format(escape_attribute(source), escape_attribute(description))
        return rtnval
