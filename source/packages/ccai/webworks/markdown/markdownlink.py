"""
.. module:: markdownlink
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: A link found while rendering a markdown document: where it points and what its text says.

.. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []

from dataclasses import dataclass


@dataclass(frozen=True)
class MarkdownLink:
    """
        A link of a rendered markdown document, in the order the links appear in the document. Lists and tables of
        links are how an index document describes the documents it leads to.

        :param destination: The destination as written in the markdown, before any rewriting.
        :param text: The plain text of the link.
    """
    destination: str
    text: str
