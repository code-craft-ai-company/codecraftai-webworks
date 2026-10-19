"""
.. module:: markdowndocument
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: The result of rendering a markdown document: its HTML, title, headings and links.

.. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []

from dataclasses import dataclass, field
from typing import Optional, Tuple

from ccai.webworks.markdown.markdownheading import MarkdownHeading
from ccai.webworks.markdown.markdownlink import MarkdownLink


@dataclass(frozen=True)
class MarkdownDocument:
    """
        A rendered markdown document.

        :param html: The HTML of the document's body (no ``<html>``, ``<head>`` or ``<body>``). Everything taken from
                     the markdown is escaped.
        :param title: The text of the first level-one heading, or of the first heading when there is no level-one
                      heading, or None when the document has no headings.
        :param headings: Every heading, in document order.
        :param links: Every link, in document order.
        :param paragraphs: The plain text of every paragraph, in document order, including the paragraphs inside block
                           quotes and lists. A site takes a page's summary from them.
    """
    html: str
    title: Optional[str]
    headings: Tuple[MarkdownHeading, ...]
    links: Tuple[MarkdownLink, ...]
    paragraphs: Tuple[str, ...] = field(default_factory=tuple)
