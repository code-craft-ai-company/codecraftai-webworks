"""
.. module:: blockparser
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Splits markdown text into blocks: paragraphs, headings, code blocks, block quotes, lists and tables.

.. moduleauthor:: Code Craft AI LLC

The parser reads the lines of a document from the top and decides what kind of block each one starts, following the
block rules of CommonMark: ATX and setext headings, thematic breaks, fenced and indented code blocks, block quotes
(with lazy continuation lines), bullet and ordered lists (tight or loose, nested by indentation), paragraphs and link
reference definitions. It adds GitHub tables.

Containers (block quotes and list items) are parsed by collecting their lines, removing the container's prefix or
indentation, and parsing those lines again as a document of their own. Raw HTML blocks are not recognised; their lines
are read as paragraph text and escaped when the HTML is written.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []

import re

from typing import Dict, List, Optional, Tuple

from ccai.webworks.markdown.blocknode import (
    BLOCK_KIND_BLOCKQUOTE,
    BLOCK_KIND_CODE,
    BLOCK_KIND_HEADING,
    BLOCK_KIND_LIST,
    BLOCK_KIND_LIST_ITEM,
    BLOCK_KIND_PARAGRAPH,
    BLOCK_KIND_TABLE,
    BLOCK_KIND_THEMATIC_BREAK,
    TABLE_ALIGN_CENTER,
    TABLE_ALIGN_LEFT,
    TABLE_ALIGN_NONE,
    TABLE_ALIGN_RIGHT,
    BlockNode,
)
from ccai.webworks.markdown.inlineparser import normalize_link_label, unescape_markdown
from ccai.webworks.markdown.listmarker import ListMarker

#: The number of columns a tab advances to (the next multiple of this).
MARKDOWN_TAB_STOP = 4

#: How deeply block quotes and lists may nest before the rest is read as a paragraph.
MARKDOWN_MAX_NESTING = 64

#: The opening line of a fenced code block (after its indentation).
MARKDOWN_FENCE_PATTERN = re.compile(r"^(`{3,}|~{3,})(.*)$")

#: An ATX heading (after its indentation): one to six ``#`` followed by a space, a tab or the end of the line.
MARKDOWN_ATX_HEADING_PATTERN = re.compile(r"^(#{1,6})(?:[ \t]+(.*))?$")

#: A thematic break (after its indentation).
MARKDOWN_THEMATIC_BREAK_PATTERN = re.compile(r"^(?:(?:\*[ \t]*){3,}|(?:-[ \t]*){3,}|(?:_[ \t]*){3,})$")

#: The underline of a setext heading (after its indentation).
MARKDOWN_SETEXT_UNDERLINE_PATTERN = re.compile(r"^(=+|-+)[ \t]*$")

#: A bullet list marker (after its indentation).
MARKDOWN_BULLET_MARKER_PATTERN = re.compile(r"^([-+*])(?:([ \t]+)(.*))?$")

#: An ordered list marker (after its indentation).
MARKDOWN_ORDERED_MARKER_PATTERN = re.compile(r"^([0-9]{1,9})([.)])(?:([ \t]+)(.*))?$")

#: The delimiter row of a table (stripped).
MARKDOWN_TABLE_DELIMITER_PATTERN = re.compile(r"^\|?[ \t]*:?-+:?[ \t]*(?:\|[ \t]*:?-+:?[ \t]*)*\|?$")

#: A link reference definition on one line (after its indentation).
MARKDOWN_LINK_DEFINITION_PATTERN = re.compile(
    r"^\[((?:[^\[\]\\]|\\.){1,999})\]:[ \t]*(<[^<>\n]*>|\S+)"
    r"(?:[ \t]+(\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*'|\((?:[^()\\]|\\.)*\)))?[ \t]*$"
)


def is_blank(line: str) -> bool:
    """
        Whether a line holds nothing but spaces and tabs.

        :param line: The line.

        :returns: True for a blank line.
    """
    rtnval = line.strip(" \t") == ""
    return rtnval


def leading_columns(line: str) -> int:
    """
        The number of columns of whitespace at the start of a line, with tabs advancing to the next tab stop.

        :param line: The line.

        :returns: The number of columns.
    """
    columns = 0
    for char in line:
        if char == " ":
            columns += 1
        elif char == "\t":
            columns += MARKDOWN_TAB_STOP - (columns % MARKDOWN_TAB_STOP)
        else:
            break
    return columns


def remove_columns(line: str, columns: int) -> str:
    """
        Removes up to ``columns`` columns of whitespace from the start of a line. A tab that reaches past the last
        removed column leaves the rest of its width as spaces.

        :param line: The line.
        :param columns: How many columns to remove.

        :returns: The line without the removed columns.
    """
    removed = 0
    index = 0
    while index < len(line) and removed < columns:
        char = line[index]
        if char == " ":
            removed += 1
            index += 1
        elif char == "\t":
            width = MARKDOWN_TAB_STOP - (removed % MARKDOWN_TAB_STOP)
            if removed + width > columns:
                remaining = removed + width - columns
                rtnval = " " * remaining + line[index + 1:]
                return rtnval
            removed += width
            index += 1
        else:
            break

    rtnval = line[index:]
    return rtnval


def split_table_cells(line: str) -> List[str]:
    """
        Splits a table row into its cells. Leading and trailing pipes are optional and an escaped pipe ``\\|`` is part
        of a cell.

        :param line: The row.

        :returns: The cells, without surrounding whitespace.
    """
    content = line.strip()
    if content.startswith("|"):
        content = content[1:]
    if content.endswith("|") and not content.endswith("\\|"):
        content = content[:-1]

    cells: List[str] = []
    current: List[str] = []
    index = 0
    while index < len(content):
        char = content[index]
        if char == "\\" and index + 1 < len(content) and content[index + 1] == "|":
            current.append("|")
            index += 2
            continue
        if char == "|":
            cells.append("".join(current).strip())
            current = []
            index += 1
            continue
        current.append(char)
        index += 1

    cells.append("".join(current).strip())
    return cells


def table_alignment(delimiter_cell: str) -> str:
    """
        The alignment that a cell of a table's delimiter row asks for.

        :param delimiter_cell: The cell, such as ``:---:``.

        :returns: One of the ``TABLE_ALIGN_*`` constants.
    """
    cell = delimiter_cell.strip()
    starts = cell.startswith(":")
    ends = cell.endswith(":")
    if starts and ends:
        rtnval = TABLE_ALIGN_CENTER
    elif ends:
        rtnval = TABLE_ALIGN_RIGHT
    elif starts:
        rtnval = TABLE_ALIGN_LEFT
    else:
        rtnval = TABLE_ALIGN_NONE
    return rtnval


class BlockParser:
    """
        Splits markdown text into a list of :class:`BlockNode` objects and collects its link reference definitions.

        An instance parses one document at a time; :meth:`parse` resets its state.
    """

    def __init__(self):
        """
            Creates a block parser.
        """
        self._definitions: Dict[str, Tuple[str, str]] = {}
        self._depth = 0
        return

    @property
    def definitions(self) -> Dict[str, Tuple[str, str]]:
        """
            The link reference definitions of the last document parsed, by normalized label, as
            ``(destination, title)``.
        """
        return self._definitions

    def parse(self, text: str) -> List[BlockNode]:
        """
            Parses a document.

            :param text: The markdown text.

            :returns: The blocks of the document.
        """
        normalized = text.replace("\r\n", "\n")
        normalized = normalized.replace("\r", "\n")
        normalized = normalized.replace("\x00", "�")
        if normalized.startswith("﻿"):
            normalized = normalized[1:]

        lines = normalized.split("\n")

        self._definitions = {}
        self._depth = 0

        rtnval = self._parse_blocks(lines)
        return rtnval

    def _parse_blocks(self, lines: List[str]) -> List[BlockNode]:
        """
            Parses a sequence of lines (a document, or the content of a container) into blocks.

            :param lines: The lines, with any container prefix already removed.

            :returns: The blocks.
        """
        blocks: List[BlockNode] = []

        if self._depth > MARKDOWN_MAX_NESTING:
            paragraph = BlockNode(BLOCK_KIND_PARAGRAPH)
            paragraph.text = "\n".join(lines).strip()
            if paragraph.text != "":
                blocks.append(paragraph)
            return blocks

        self._depth += 1

        index = 0
        blank_before = False
        total = len(lines)
        while index < total:
            line = lines[index]
            if is_blank(line):
                blank_before = True
                index += 1
                continue

            block, index = self._parse_block_at(lines, index)
            if block is not None:
                block.blank_before = blank_before
                blocks.append(block)
                blank_before = False

        self._depth -= 1
        return blocks

    def _parse_block_at(self, lines: List[str], index: int) -> Tuple[Optional[BlockNode], int]:
        """
            Parses the block that starts on a line.

            :param lines: The lines.
            :param index: The line the block starts on; it is not blank.

            :returns: ``(block, index of the line after it)``. The block is None when the lines held only link
                      reference definitions.
        """
        line = lines[index]
        indent = leading_columns(line)
        if indent >= 4:
            rtnval = self._parse_indented_code(lines, index)
            return rtnval

        stripped = line.lstrip(" \t")

        fence_match = MARKDOWN_FENCE_PATTERN.match(stripped)
        if fence_match is not None and self._is_valid_fence(fence_match):
            rtnval = self._parse_fenced_code(lines, index, indent=indent, fence_match=fence_match)
            return rtnval

        heading_match = MARKDOWN_ATX_HEADING_PATTERN.match(stripped)
        if heading_match is not None:
            rtnval = self._parse_atx_heading(heading_match, index)
            return rtnval

        if MARKDOWN_THEMATIC_BREAK_PATTERN.match(stripped) is not None:
            rtnval = (BlockNode(BLOCK_KIND_THEMATIC_BREAK), index + 1)
            return rtnval

        if stripped.startswith(">"):
            rtnval = self._parse_blockquote(lines, index)
            return rtnval

        marker = self._list_marker(line)
        if marker is not None:
            rtnval = self._parse_list(lines, index, first=marker)
            return rtnval

        if self._starts_table(lines, index):
            rtnval = self._parse_table(lines, index)
            return rtnval

        rtnval = self._parse_paragraph(lines, index)
        return rtnval

    def _is_valid_fence(self, fence_match: re.Match) -> bool:
        """
            Whether a fence-like line opens a code block. The info string of a backtick fence may not hold a backtick.

            :param fence_match: The match of :data:`MARKDOWN_FENCE_PATTERN`.

            :returns: True when the line opens a code block.
        """
        fence = fence_match.group(1)
        info = fence_match.group(2)
        if fence.startswith("`") and "`" in info:
            return False
        return True

    def _parse_fenced_code(self, lines: List[str], index: int, *, indent: int, fence_match: re.Match) -> Tuple[BlockNode, int]:
        """
            Parses a fenced code block. The block ends at a fence of the same character that is at least as long, or
            at the end of the lines. Content lines lose as much indentation as the opening fence had.

            :param lines: The lines.
            :param index: The line of the opening fence.
            :param indent: The indentation of the opening fence.
            :param fence_match: The match of :data:`MARKDOWN_FENCE_PATTERN` on the opening fence.

            :returns: ``(code block, index of the line after it)``.
        """
        fence = fence_match.group(1)
        fence_char = fence[0]
        info = fence_match.group(2).strip()

        closing_pattern = re.compile(r"^(" + re.escape(fence_char) + r"{" + str(len(fence)) + r",})[ \t]*$")

        content: List[str] = []
        cursor = index + 1
        total = len(lines)
        while cursor < total:
            line = lines[cursor]
            if leading_columns(line) <= 3:
                stripped = line.lstrip(" \t")
                if closing_pattern.match(stripped) is not None:
                    cursor += 1
                    break
            content.append(remove_columns(line, indent))
            cursor += 1

        block = BlockNode(BLOCK_KIND_CODE)
        block.info = unescape_markdown(info)
        if len(content) > 0:
            block.text = "\n".join(content) + "\n"

        rtnval = (block, cursor)
        return rtnval

    def _parse_indented_code(self, lines: List[str], index: int) -> Tuple[BlockNode, int]:
        """
            Parses an indented code block: lines indented four or more columns, with blank lines between them. Blank
            lines after the last code line are left for the next block.

            :param lines: The lines.
            :param index: The first line of the block.

            :returns: ``(code block, index of the line after it)``.
        """
        content: List[str] = []
        cursor = index
        total = len(lines)
        while cursor < total:
            line = lines[cursor]
            if is_blank(line) or leading_columns(line) >= 4:
                content.append(remove_columns(line, 4))
                cursor += 1
                continue
            break

        while len(content) > 0 and is_blank(content[-1]):
            content.pop()
            cursor -= 1

        block = BlockNode(BLOCK_KIND_CODE)
        block.text = "\n".join(content) + "\n"

        rtnval = (block, cursor)
        return rtnval

    def _parse_atx_heading(self, heading_match: re.Match, index: int) -> Tuple[BlockNode, int]:
        """
            Builds an ATX heading. A closing run of ``#`` that follows a space is not part of the heading text.

            :param heading_match: The match of :data:`MARKDOWN_ATX_HEADING_PATTERN`.
            :param index: The line of the heading.

            :returns: ``(heading, index of the line after it)``.
        """
        marks = heading_match.group(1)
        content = heading_match.group(2)
        if content is None:
            content = ""
        content = content.strip()
        content = re.sub(r"(?:^|[ \t]+)#+$", "", content)

        block = BlockNode(BLOCK_KIND_HEADING)
        block.level = len(marks)
        block.text = content.strip()

        rtnval = (block, index + 1)
        return rtnval

    def _parse_blockquote(self, lines: List[str], index: int) -> Tuple[BlockNode, int]:
        """
            Parses a block quote: lines that start with ``>`` (and one optional space after it), plus lazy
            continuation lines of a paragraph inside it.

            :param lines: The lines.
            :param index: The first line of the quote.

            :returns: ``(block quote, index of the line after it)``.
        """
        inner: List[str] = []
        cursor = index
        total = len(lines)
        while cursor < total:
            line = lines[cursor]
            if leading_columns(line) <= 3:
                stripped = line.lstrip(" \t")
                if stripped.startswith(">"):
                    rest = stripped[1:]
                    if rest.startswith(" ") or rest.startswith("\t"):
                        rest = rest[1:]
                    inner.append(rest)
                    cursor += 1
                    continue

            if is_blank(line):
                break

            if self._can_continue_lazily(inner, lines, cursor):
                inner.append(line)
                cursor += 1
                continue

            break

        block = BlockNode(BLOCK_KIND_BLOCKQUOTE)
        block.children = self._parse_blocks(inner)

        rtnval = (block, cursor)
        return rtnval

    def _list_marker(self, line: str) -> Optional[ListMarker]:
        """
            Reads the list marker at the start of a line.

            :param line: The line.

            :returns: The marker, or None when the line does not start a list item.
        """
        indent = leading_columns(line)
        if indent > 3:
            return None

        stripped = line.lstrip(" \t")

        bullet_match = MARKDOWN_BULLET_MARKER_PATTERN.match(stripped)
        if bullet_match is not None:
            ordered = False
            symbol = bullet_match.group(1)
            number = 0
            marker_text = symbol
            spaces = bullet_match.group(2)
            content = bullet_match.group(3)
        else:
            ordered_match = MARKDOWN_ORDERED_MARKER_PATTERN.match(stripped)
            if ordered_match is None:
                return None
            ordered = True
            digits = ordered_match.group(1)
            symbol = ordered_match.group(2)
            number = int(digits)
            marker_text = digits + symbol
            spaces = ordered_match.group(3)
            content = ordered_match.group(4)

        if spaces is None:
            spaces = ""
        if content is None:
            content = ""

        marker_end = indent + len(marker_text)
        if content.strip() == "":
            content_column = marker_end + 1
            first_line = ""
        else:
            prefix = " " * marker_end + spaces
            space_columns = leading_columns(prefix) - marker_end
            if space_columns >= 5:
                content_column = marker_end + 1
                first_line = " " * (space_columns - 1) + content
            else:
                content_column = marker_end + space_columns
                first_line = content

        rtnval = ListMarker(ordered=ordered, symbol=symbol, number=number, indent=indent, content_column=content_column,
                            first_line=first_line)
        return rtnval

    def _is_thematic_break(self, line: str) -> bool:
        """
            Whether a line is a thematic break.

            :param line: The line.

            :returns: True for a thematic break.
        """
        if leading_columns(line) > 3:
            return False
        stripped = line.lstrip(" \t")
        rtnval = MARKDOWN_THEMATIC_BREAK_PATTERN.match(stripped) is not None
        return rtnval

    def _parse_list(self, lines: List[str], index: int, *, first: ListMarker) -> Tuple[BlockNode, int]:
        """
            Parses a list: items whose markers match the first one. The list is loose when blank lines separate its
            items or separate blocks inside an item.

            :param lines: The lines.
            :param index: The line of the first item.
            :param first: The marker of the first item.

            :returns: ``(list, index of the line after it)``.
        """
        block = BlockNode(BLOCK_KIND_LIST)
        block.ordered = first.ordered
        if first.ordered:
            block.start = first.number

        loose = False
        cursor = index
        total = len(lines)
        while cursor < total:
            line = lines[cursor]
            marker = None
            if not is_blank(line) and not self._is_thematic_break(line):
                marker = self._list_marker(line)
            if marker is None or not marker.is_same_list(first):
                break

            item_lines, cursor = self._collect_list_item(lines, cursor, marker=marker)

            item = BlockNode(BLOCK_KIND_LIST_ITEM)
            item.children = self._parse_blocks(item_lines)
            for position, child in enumerate(item.children):
                if position > 0 and child.blank_before:
                    loose = True
            block.children.append(item)

            following_index = cursor
            while following_index < total and is_blank(lines[following_index]):
                following_index += 1

            if following_index == cursor:
                continue

            following = None
            if following_index < total and not self._is_thematic_break(lines[following_index]):
                following = self._list_marker(lines[following_index])

            if following is not None and following.is_same_list(first):
                loose = True
                cursor = following_index
                continue

            break

        block.tight = not loose

        rtnval = (block, cursor)
        return rtnval

    def _collect_list_item(self, lines: List[str], index: int, *, marker: ListMarker) -> Tuple[List[str], int]:
        """
            Collects the lines of one list item with the item's indentation removed: the marker line, lines indented
            to the item's content column (with blank lines between them) and lazy continuation lines of a paragraph.

            :param lines: The lines.
            :param index: The line of the item's marker.
            :param marker: The item's marker.

            :returns: ``(the item's lines, index of the line after the item)``. Blank lines after the item are left
                      in place.
        """
        item_lines = [marker.first_line]
        started_empty = marker.first_line.strip() == ""

        cursor = index + 1
        total = len(lines)
        while cursor < total:
            line = lines[cursor]

            if is_blank(line):
                if started_empty and len(item_lines) == 1:
                    break

                lookahead = cursor
                while lookahead < total and is_blank(lines[lookahead]):
                    lookahead += 1
                if lookahead < total and leading_columns(lines[lookahead]) >= marker.content_column:
                    while cursor < lookahead:
                        item_lines.append("")
                        cursor += 1
                    continue
                break

            if leading_columns(line) >= marker.content_column:
                item_lines.append(remove_columns(line, marker.content_column))
                cursor += 1
                continue

            if self._can_continue_lazily(item_lines, lines, cursor):
                item_lines.append(line)
                cursor += 1
                continue

            break

        rtnval = (item_lines, cursor)
        return rtnval

    def _can_continue_lazily(self, container_lines: List[str], lines: List[str], index: int) -> bool:
        """
            Whether a line that lacks a container's prefix still belongs to the container as a lazy continuation of a
            paragraph: the container's last line is paragraph text and the line does not start a block of its own.

            :param container_lines: The lines collected for the container so far, prefix removed.
            :param lines: The lines being read.
            :param index: The line to decide about.

            :returns: True when the line continues the container.
        """
        if len(container_lines) == 0:
            return False

        last = container_lines[-1]
        if is_blank(last) or leading_columns(last) >= 4:
            return False

        last_stripped = last.lstrip(" \t")
        if MARKDOWN_ATX_HEADING_PATTERN.match(last_stripped) is not None:
            return False
        if MARKDOWN_THEMATIC_BREAK_PATTERN.match(last_stripped) is not None:
            return False
        if self._inside_open_fence(container_lines):
            return False

        if self._starts_block(lines, index):
            return False

        return True

    def _starts_block(self, lines: List[str], index: int) -> bool:
        """
            Whether a line starts a block other than paragraph text: a fence, heading, thematic break, block quote,
            list item or table. Indented lines never do.

            :param lines: The lines.
            :param index: The line.

            :returns: True when the line starts a block.
        """
        line = lines[index]
        if leading_columns(line) >= 4:
            return False

        stripped = line.lstrip(" \t")

        fence_match = MARKDOWN_FENCE_PATTERN.match(stripped)
        if fence_match is not None and self._is_valid_fence(fence_match):
            return True
        if MARKDOWN_ATX_HEADING_PATTERN.match(stripped) is not None:
            return True
        if MARKDOWN_THEMATIC_BREAK_PATTERN.match(stripped) is not None:
            return True
        if stripped.startswith(">"):
            return True
        if self._list_marker(line) is not None:
            return True
        if self._starts_table(lines, index):
            return True

        return False

    def _inside_open_fence(self, container_lines: List[str]) -> bool:
        """
            Whether the lines end inside a fenced code block that has not been closed.

            :param container_lines: The lines.

            :returns: True when a fence is still open after the last line.
        """
        open_fence = ""
        for line in container_lines:
            if leading_columns(line) > 3:
                continue
            stripped = line.lstrip(" \t")
            if open_fence == "":
                fence_match = MARKDOWN_FENCE_PATTERN.match(stripped)
                if fence_match is not None and self._is_valid_fence(fence_match):
                    open_fence = fence_match.group(1)
            else:
                closing = stripped.rstrip(" \t")
                if closing.startswith(open_fence) and closing.strip(open_fence[0]) == "":
                    open_fence = ""

        rtnval = open_fence != ""
        return rtnval

    def _interrupts_paragraph(self, lines: List[str], index: int) -> bool:
        """
            Whether a line ends the paragraph above it by starting another block. A list item interrupts a paragraph
            only when it has content, and an ordered one only when it starts at 1.

            :param lines: The lines.
            :param index: The line.

            :returns: True when the line interrupts the paragraph.
        """
        line = lines[index]
        if leading_columns(line) >= 4:
            return False

        stripped = line.lstrip(" \t")

        fence_match = MARKDOWN_FENCE_PATTERN.match(stripped)
        if fence_match is not None and self._is_valid_fence(fence_match):
            return True
        if MARKDOWN_ATX_HEADING_PATTERN.match(stripped) is not None:
            return True
        if MARKDOWN_THEMATIC_BREAK_PATTERN.match(stripped) is not None:
            return True
        if stripped.startswith(">"):
            return True

        marker = self._list_marker(line)
        if marker is not None and marker.first_line.strip() != "":
            if not marker.ordered or marker.number == 1:
                return True

        if self._starts_table(lines, index):
            return True

        return False

    def _parse_paragraph(self, lines: List[str], index: int) -> Tuple[Optional[BlockNode], int]:
        """
            Parses a paragraph, or a setext heading when the paragraph's lines are followed by an ``===`` or ``---``
            underline. Link reference definitions at the start of the paragraph are collected and removed.

            :param lines: The lines.
            :param index: The first line.

            :returns: ``(paragraph or heading, index of the line after it)``. The block is None when the lines held
                      only link reference definitions.
        """
        total = len(lines)
        cursor = index

        while cursor < total and not is_blank(lines[cursor]) and leading_columns(lines[cursor]) <= 3:
            definition_match = MARKDOWN_LINK_DEFINITION_PATTERN.match(lines[cursor].lstrip(" \t"))
            if definition_match is None:
                break
            self._add_definition(definition_match)
            cursor += 1

        if cursor > index:
            if cursor >= total or is_blank(lines[cursor]) or self._starts_block(lines, cursor):
                rtnval = (None, cursor)
                return rtnval

        collected = [lines[cursor].lstrip(" \t")]
        cursor += 1
        while cursor < total:
            line = lines[cursor]
            if is_blank(line):
                break

            if leading_columns(line) <= 3:
                underline_match = MARKDOWN_SETEXT_UNDERLINE_PATTERN.match(line.lstrip(" \t"))
                if underline_match is not None:
                    heading = BlockNode(BLOCK_KIND_HEADING)
                    if underline_match.group(1).startswith("="):
                        heading.level = 1
                    else:
                        heading.level = 2
                    heading.text = "\n".join(collected).strip()
                    rtnval = (heading, cursor + 1)
                    return rtnval

            if self._interrupts_paragraph(lines, cursor):
                break

            collected.append(line.lstrip(" \t"))
            cursor += 1

        paragraph = BlockNode(BLOCK_KIND_PARAGRAPH)
        paragraph.text = "\n".join(collected).rstrip()

        rtnval = (paragraph, cursor)
        return rtnval

    def _add_definition(self, definition_match: re.Match) -> None:
        """
            Records a link reference definition. The first definition of a label wins.

            :param definition_match: The match of :data:`MARKDOWN_LINK_DEFINITION_PATTERN`.
        """
        label = normalize_link_label(definition_match.group(1))
        if label == "" or label in self._definitions:
            return

        destination = definition_match.group(2)
        if destination.startswith("<") and destination.endswith(">"):
            destination = destination[1:-1]

        title = definition_match.group(3)
        if title is None:
            title = ""
        else:
            title = title[1:-1]

        self._definitions[label] = (unescape_markdown(destination), unescape_markdown(title))
        return

    def _starts_table(self, lines: List[str], index: int) -> bool:
        """
            Whether a line is the header row of a table: it holds a pipe and the next line is a delimiter row with the
            same number of cells.

            :param lines: The lines.
            :param index: The line.

            :returns: True when a table starts on the line.
        """
        if index + 1 >= len(lines):
            return False

        header = lines[index]
        delimiter = lines[index + 1]
        if leading_columns(header) > 3 or leading_columns(delimiter) > 3:
            return False
        if "|" not in header:
            return False
        if MARKDOWN_TABLE_DELIMITER_PATTERN.match(delimiter.strip()) is None:
            return False

        header_cells = split_table_cells(header)
        delimiter_cells = split_table_cells(delimiter)
        rtnval = len(header_cells) == len(delimiter_cells)
        return rtnval

    def _parse_table(self, lines: List[str], index: int) -> Tuple[BlockNode, int]:
        """
            Parses a table: the header row, the delimiter row and the body rows that follow. The table ends at a blank
            line, a line without a pipe, or a line that starts a block quote, heading or fence. Body rows are padded or
            cut to the header's number of cells.

            :param lines: The lines.
            :param index: The header row.

            :returns: ``(table, index of the line after it)``.
        """
        header_cells = split_table_cells(lines[index])
        delimiter_cells = split_table_cells(lines[index + 1])

        alignments = []
        for cell in delimiter_cells:
            alignment = table_alignment(cell)
            alignments.append(alignment)

        width = len(header_cells)
        rows: List[List[str]] = []
        cursor = index + 2
        total = len(lines)
        while cursor < total:
            line = lines[cursor]
            if is_blank(line) or "|" not in line:
                break
            if leading_columns(line) <= 3:
                stripped = line.lstrip(" \t")
                if stripped.startswith(">") or MARKDOWN_ATX_HEADING_PATTERN.match(stripped) is not None:
                    break
                fence_match = MARKDOWN_FENCE_PATTERN.match(stripped)
                if fence_match is not None and self._is_valid_fence(fence_match):
                    break

            cells = split_table_cells(line)
            if len(cells) < width:
                padding = [""] * (width - len(cells))
                cells.extend(padding)
            elif len(cells) > width:
                cells = cells[:width]
            rows.append(cells)
            cursor += 1

        block = BlockNode(BLOCK_KIND_TABLE)
        block.header_cells = header_cells
        block.alignments = alignments
        block.body_rows = rows

        rtnval = (block, cursor)
        return rtnval
