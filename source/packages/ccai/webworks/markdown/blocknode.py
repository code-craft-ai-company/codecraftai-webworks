"""
.. module:: blocknode
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: One block of a markdown document: a paragraph, heading, code block, list, table and so on.

.. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []

from typing import List

#: A paragraph; ``text`` holds its inline content.
BLOCK_KIND_PARAGRAPH = "paragraph"

#: A heading; ``level`` is 1 to 6 and ``text`` holds its inline content.
BLOCK_KIND_HEADING = "heading"

#: A thematic break (``---``, ``***`` or ``___``).
BLOCK_KIND_THEMATIC_BREAK = "thematic_break"

#: A fenced or indented code block; ``text`` holds the code and ``info`` the fence's info string.
BLOCK_KIND_CODE = "code"

#: A block quote; ``children`` hold its blocks.
BLOCK_KIND_BLOCKQUOTE = "blockquote"

#: A bullet or ordered list; ``children`` are its items.
BLOCK_KIND_LIST = "list"

#: An item of a list; ``children`` hold its blocks.
BLOCK_KIND_LIST_ITEM = "list_item"

#: A table; ``header_cells``, ``body_rows`` and ``alignments`` describe it.
BLOCK_KIND_TABLE = "table"

#: A table column with no alignment marker.
TABLE_ALIGN_NONE = ""

#: A table column marked ``:---``.
TABLE_ALIGN_LEFT = "left"

#: A table column marked ``:---:``.
TABLE_ALIGN_CENTER = "center"

#: A table column marked ``---:``.
TABLE_ALIGN_RIGHT = "right"


class BlockNode:
    """
        One block of a markdown document.

        Leaf blocks keep their source in ``text`` (the inline content of a paragraph or heading, or the code of a code
        block). Container blocks (block quotes, lists and list items) keep their blocks in ``children``.
        ``blank_before`` records whether a blank line separated the block from the one before it in the same container,
        which decides whether a list is loose.
    """

    def __init__(self, kind: str):
        """
            Creates a block.

            :param kind: One of the ``BLOCK_KIND_*`` constants.
        """
        self.kind = kind
        self.children: List[BlockNode] = []
        self.text = ""
        self.level = 0
        self.info = ""
        self.ordered = False
        self.start = 1
        self.tight = True
        self.blank_before = False
        self.alignments: List[str] = []
        self.header_cells: List[str] = []
        self.body_rows: List[List[str]] = []
        return

    def __repr__(self) -> str:
        """
            A short description of the block for the debugger.

            :returns: The description.
        """
        if len(self.children) > 0:
            rtnval = "BlockNode({}, children={})".format(self.kind, len(self.children))
        else:
            rtnval = "BlockNode({}, {!r})".format(self.kind, self.text[:40])
        return rtnval
