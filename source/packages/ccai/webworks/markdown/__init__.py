"""
.. module:: markdown
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Package that renders markdown as HTML without third-party libraries.

.. moduleauthor:: Code Craft AI LLC

This package provides:

- :class:`MarkdownRenderer`, which renders CommonMark plus GitHub tables, strikethrough and bare-address links
- :class:`MarkdownDocument`, the result: the HTML with the document's title, headings and links
- :func:`is_safe_url`, the check that keeps ``javascript:`` and other unsafe destinations out of a page

Example::

    from ccai.webworks.markdown import MarkdownRenderer

    document = MarkdownRenderer().render("# Title\\n\\nSome *text*.")
    document.html   # '<h1 id="title">Title</h1>\\n<p>Some <em>text</em>.</p>\\n'
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []

from ccai.webworks.markdown.headingslugger import HeadingSlugger, make_heading_slug
from ccai.webworks.markdown.htmlwriter import is_safe_url
from ccai.webworks.markdown.markdowndocument import MarkdownDocument
from ccai.webworks.markdown.markdownheading import MarkdownHeading
from ccai.webworks.markdown.markdownlink import MarkdownLink
from ccai.webworks.markdown.markdownrenderer import MarkdownRenderer

__all__ = [
    "HeadingSlugger",
    "MarkdownDocument",
    "MarkdownHeading",
    "MarkdownLink",
    "MarkdownRenderer",
    "is_safe_url",
    "make_heading_slug",
]
