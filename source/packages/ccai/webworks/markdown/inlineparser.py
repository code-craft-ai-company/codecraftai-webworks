"""
.. module:: inlineparser
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Parses the inline content of a markdown block into :class:`InlineNode` objects.

.. moduleauthor:: Code Craft AI LLC

The parser follows the inline rules of CommonMark: code spans, emphasis and strong emphasis (with the delimiter-run
algorithm, so ``*a **b** c*`` nests the way the specification says), inline and reference links and images, autolinks,
backslash escapes, entity references and line breaks. It adds the GitHub extensions the books use: strikethrough with
``~~`` and links made from bare ``http://``, ``https://`` and ``www.`` addresses.

Raw HTML is not passed through: a ``<tag>`` in the text is kept as text and escaped when the HTML is written.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []

import html
import re
import unicodedata

from typing import Dict, List, Optional, Tuple

from ccai.webworks.markdown.bracketopener import BracketOpener
from ccai.webworks.markdown.delimiterrun import DelimiterRun
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
from ccai.webworks.markdown.inlinenodechain import InlineNodeChain

#: The position on the delimiter stack that stands for "no delimiter".
MARKDOWN_NO_DELIMITER = -1

#: How deeply emphasis, links and images may nest. Content nested deeper keeps its text and loses its markup, so the
#: walks over the inline nodes (merging text, linking addresses, writing HTML) never recurse further than this.
MARKDOWN_MAX_INLINE_NESTING = 32

#: The ASCII punctuation characters that a backslash makes literal.
MARKDOWN_ESCAPABLE_CHARACTERS = "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"

#: The characters at which plain text stops so the parser can look at what follows.
MARKDOWN_INLINE_SPECIAL_CHARACTERS = "\\`*_~[]!<&\n"

#: A named, decimal or hexadecimal entity reference.
MARKDOWN_ENTITY_PATTERN = re.compile(r"&(?:#[0-9]{1,7}|#[xX][0-9a-fA-F]{1,6}|[A-Za-z][A-Za-z0-9]{1,31});")

#: A backslash escape or an entity reference, for unescaping link destinations and titles in one pass.
MARKDOWN_UNESCAPE_PATTERN = re.compile(
    r"\\([!\"#$%&'()*+,\-./:;<=>?@\[\\\]^_`{|}~])|(&(?:#[0-9]{1,7}|#[xX][0-9a-fA-F]{1,6}|[A-Za-z][A-Za-z0-9]{1,31});)"
)

#: An autolink to an absolute URI: ``<https://example.com>``.
MARKDOWN_AUTOLINK_URI_PATTERN = re.compile(r"<([A-Za-z][A-Za-z0-9+.\-]{1,31}:[^\s<>\x00-\x20]*)>")

#: An autolink to an email address: ``<someone@example.com>``.
MARKDOWN_AUTOLINK_EMAIL_PATTERN = re.compile(
    r"<([A-Za-z0-9.!#$%&'*+/=?^_`{|}~\-]+@[A-Za-z0-9](?:[A-Za-z0-9\-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9\-]{0,61}[A-Za-z0-9])?)*)>"
)

#: A bare address in text that becomes a link (the GitHub autolink extension).
MARKDOWN_BARE_URL_PATTERN = re.compile(r"(?<![^\s*_~(])(?:https?://[A-Za-z0-9][^\s<]*|www\.[A-Za-z0-9\-]+\.[^\s<]*)")

#: The characters trimmed from the end of a bare address, because they almost always end the sentence instead.
MARKDOWN_BARE_URL_TRAILING_CHARACTERS = "?!.,:*_~'\""

#: The longest label a link reference may have.
MARKDOWN_MAX_LABEL_LENGTH = 999


def normalize_link_label(label: str) -> str:
    """
        The form of a link label used to match a reference to its definition: whitespace collapsed and case folded.

        :param label: The label as written.

        :returns: The normalized label.
    """
    words = label.split()
    joined = " ".join(words)
    rtnval = joined.casefold()
    return rtnval


def unescape_markdown(value: str) -> str:
    """
        Replaces backslash escapes and entity references in a link destination, link title or code fence info string.

        :param value: The text as written.

        :returns: The text with escapes and entities replaced by the characters they stand for.
    """

    def replace(match: re.Match) -> str:
        escaped = match.group(1)
        if escaped is not None:
            return escaped
        entity = match.group(2)
        decoded = decode_entity(entity)
        return decoded

    rtnval = MARKDOWN_UNESCAPE_PATTERN.sub(replace, value)
    return rtnval


def decode_entity(entity: str) -> str:
    """
        The character an entity reference stands for. An unknown named entity is returned as it was written, and the
        character zero becomes the replacement character.

        :param entity: The entity reference, ``&`` through ``;``.

        :returns: The decoded text.
    """
    decoded = html.unescape(entity)
    if decoded == "\x00":
        decoded = "\ufffd"
    rtnval = decoded
    return rtnval


def is_unicode_whitespace(char: str) -> bool:
    """
        Whether a character counts as whitespace for the emphasis rules. The empty string stands for the start or end
        of the text, which counts as whitespace.

        :param char: One character, or the empty string.

        :returns: True for whitespace.
    """
    if char == "":
        return True
    if char in "\t\n\f\r":
        return True
    category = unicodedata.category(char)
    rtnval = category == "Zs"
    return rtnval


def is_unicode_punctuation(char: str) -> bool:
    """
        Whether a character counts as punctuation for the emphasis rules: Unicode punctuation and symbols.

        :param char: One character, or the empty string.

        :returns: True for punctuation.
    """
    if char == "":
        return False
    category = unicodedata.category(char)
    major = category[0]
    rtnval = major == "P" or major == "S"
    return rtnval


class InlineParser:
    """
        Parses the inline content of one block (a paragraph, a heading or a table cell) into a list of
        :class:`InlineNode` objects.

        An instance parses one text at a time; :meth:`parse` resets its state.
    """

    def __init__(self, *, definitions: Optional[Dict[str, Tuple[str, str]]] = None):
        """
            Creates an inline parser.

            :param definitions: The link reference definitions of the document, by normalized label (see
                                :func:`normalize_link_label`), as ``(destination, title)``.
        """
        self._definitions: Dict[str, Tuple[str, str]] = {}
        if definitions is not None:
            self._definitions = definitions
        self._text = ""
        self._pos = 0
        self._nodes: List[InlineNode] = []
        self._delimiters: List[DelimiterRun] = []
        self._brackets: List[BracketOpener] = []
        self._last_backtick_runs: Optional[Dict[int, int]] = None
        return

    def parse(self, text: str) -> List[InlineNode]:
        """
            Parses the inline content of a block.

            :param text: The content, with the lines of a paragraph joined by ``\\n``.

            :returns: The inline nodes.
        """
        self._text = text
        self._pos = 0
        self._nodes = []
        self._delimiters = []
        self._brackets = []
        self._last_backtick_runs = None

        length = len(text)
        while self._pos < length:
            char = text[self._pos]
            if char == "\\":
                self._parse_backslash()
            elif char == "`":
                self._parse_code_span()
            elif char == "*" or char == "_" or char == "~":
                self._parse_delimiter_run()
            elif char == "[":
                self._parse_open_bracket(is_image=False)
            elif char == "!" and self._char_at(self._pos + 1) == "[":
                self._parse_open_bracket(is_image=True)
            elif char == "]":
                self._parse_close_bracket()
            elif char == "<":
                self._parse_angle_bracket()
            elif char == "&":
                self._parse_entity()
            elif char == "\n":
                self._parse_line_ending()
            else:
                self._parse_plain_text()

        self._process_emphasis(bottom=0, first_node=0)

        self._limit_nesting(self._nodes)

        merged = self._merge_text_nodes(self._nodes)
        rtnval = self._link_bare_urls(merged)
        return rtnval

    def _char_at(self, position: int) -> str:
        """
            The character at a position, or the empty string past either end of the text.

            :param position: The position.

            :returns: The character.
        """
        if position < 0 or position >= len(self._text):
            return ""
        rtnval = self._text[position]
        return rtnval

    def _append_text(self, text: str) -> InlineNode:
        """
            Appends a text node.

            :param text: The characters of the node.

            :returns: The new node.
        """
        node = InlineNode(INLINE_KIND_TEXT, text=text)
        self._nodes.append(node)
        return node

    def _parse_plain_text(self) -> None:
        """
            Consumes text up to the next character that may start something else. The first character is always
            consumed, so a ``!`` that does not start an image is taken as text.
        """
        start = self._pos
        position = start + 1
        length = len(self._text)
        while position < length and self._text[position] not in MARKDOWN_INLINE_SPECIAL_CHARACTERS:
            position += 1

        self._append_text(self._text[start:position])
        self._pos = position
        return

    def _parse_backslash(self) -> None:
        """
            A backslash makes the punctuation character after it literal; before a line ending it is a hard break;
            anywhere else it is a backslash.
        """
        following = self._char_at(self._pos + 1)
        if following == "\n":
            self._nodes.append(InlineNode(INLINE_KIND_HARD_BREAK))
            self._pos += 2
            self._skip_leading_spaces()
        elif following != "" and following in MARKDOWN_ESCAPABLE_CHARACTERS:
            self._append_text(following)
            self._pos += 2
        else:
            self._append_text("\\")
            self._pos += 1
        return

    def _parse_code_span(self) -> None:
        """
            A run of backticks opens a code span that the next run of the same length closes. Line endings inside the
            span become spaces, and one space is removed from each end when both ends have one. A run with no closing
            run is literal text.
        """
        start = self._pos
        run_end = self._run_end(start, "`")
        run_length = run_end - start

        # Looking for the closing run reads every run of backticks up to it. That is only done when a run of the
        # right length is known to follow; otherwise a text made of runs of different lengths would be read to its
        # end once for every run.
        search = run_end
        close_start = -1
        while self._has_backtick_run_after(run_length, run_end):
            found = self._text.find("`", search)
            if found < 0:
                break
            found_end = self._run_end(found, "`")
            if found_end - found == run_length:
                close_start = found
                break
            search = found_end

        if close_start < 0:
            self._append_text(self._text[start:run_end])
            self._pos = run_end
            return

        content = self._text[run_end:close_start]
        content = content.replace("\n", " ")
        if len(content) >= 2 and content[0] == " " and content[-1] == " " and content.strip(" ") != "":
            content = content[1:-1]

        self._nodes.append(InlineNode(INLINE_KIND_CODE, text=content))
        self._pos = close_start + run_length
        return

    def _has_backtick_run_after(self, run_length: int, position: int) -> bool:
        """
            Whether a run of exactly ``run_length`` backticks starts at or after a position. The first call reads the
            text once and notes where the last run of each length starts.

            :param run_length: The length of the run to look for.
            :param position: The position to look from.

            :returns: True when such a run exists.
        """
        if self._last_backtick_runs is None:
            last_runs: Dict[int, int] = {}
            search = 0
            while True:
                found = self._text.find("`", search)
                if found < 0:
                    break
                found_end = self._run_end(found, "`")
                last_runs[found_end - found] = found
                search = found_end
            self._last_backtick_runs = last_runs

        rtnval = False
        if run_length in self._last_backtick_runs:
            rtnval = self._last_backtick_runs[run_length] >= position
        return rtnval

    def _run_end(self, start: int, char: str) -> int:
        """
            The position just after a run of one character.

            :param start: Where the run starts.
            :param char: The character of the run.

            :returns: The position after the run.
        """
        position = start
        length = len(self._text)
        while position < length and self._text[position] == char:
            position += 1
        return position

    def _parse_delimiter_run(self) -> None:
        """
            A run of ``*``, ``_`` or ``~`` becomes a text node and, when it can open or close emphasis, an entry on the
            delimiter stack. Whether it can open or close follows the flanking rules of CommonMark; ``_`` may not open
            or close inside a word. A run of three or more tildes is plain text.
        """
        start = self._pos
        char = self._text[start]
        end = self._run_end(start, char)
        count = end - start

        before = self._char_at(start - 1)
        after = self._char_at(end)

        before_is_space = is_unicode_whitespace(before)
        after_is_space = is_unicode_whitespace(after)
        before_is_punctuation = is_unicode_punctuation(before)
        after_is_punctuation = is_unicode_punctuation(after)

        left_flanking = False
        if not after_is_space:
            if not after_is_punctuation:
                left_flanking = True
            elif before_is_space or before_is_punctuation:
                left_flanking = True

        right_flanking = False
        if not before_is_space:
            if not before_is_punctuation:
                right_flanking = True
            elif after_is_space or after_is_punctuation:
                right_flanking = True

        if char == "_":
            can_open = left_flanking and (not right_flanking or before_is_punctuation)
            can_close = right_flanking and (not left_flanking or after_is_punctuation)
        else:
            can_open = left_flanking
            can_close = right_flanking

        node = self._append_text(self._text[start:end])

        if char == "~" and count > 2:
            can_open = False
            can_close = False

        if can_open or can_close:
            run = DelimiterRun(node=node, char=char, count=count, can_open=can_open, can_close=can_close)
            self._delimiters.append(run)

        self._pos = end
        return

    def _parse_open_bracket(self, *, is_image: bool) -> None:
        """
            Pushes ``[`` or ``![`` on the bracket stack.

            :param is_image: Whether the bracket is ``![``.
        """
        if is_image:
            node = self._append_text("![")
            label_start = self._pos + 2
        else:
            node = self._append_text("[")
            label_start = self._pos + 1

        opener = BracketOpener(node=node, is_image=is_image, label_start=label_start,
                               delimiter_bottom=len(self._delimiters))
        self._brackets.append(opener)
        self._pos = label_start
        return

    def _parse_close_bracket(self) -> None:
        """
            A ``]`` closes the most recent bracket when it is followed by an inline destination ``(...)`` or names a
            known reference; the nodes after the opener become the content of the link or image. Otherwise the ``]``
            is text.
        """
        close_position = self._pos

        if len(self._brackets) == 0:
            self._append_text("]")
            self._pos += 1
            return

        opener = self._brackets[-1]
        if not opener.active:
            self._brackets.pop()
            self._append_text("]")
            self._pos += 1
            return

        label_text = self._text[opener.label_start:close_position]
        after = close_position + 1

        target = self._parse_inline_destination(after)
        if target is None:
            target = self._parse_reference(after, label_text)

        if target is None:
            self._brackets.pop()
            self._append_text("]")
            self._pos += 1
            return

        destination, title, end_position = target

        opener_index = self._last_index_of(opener.node)

        self._process_emphasis(bottom=opener.delimiter_bottom, first_node=opener_index + 1)

        children = self._nodes[opener_index + 1:]
        del self._nodes[opener_index:]

        if opener.is_image:
            kind = INLINE_KIND_IMAGE
        else:
            kind = INLINE_KIND_LINK
        node = InlineNode(kind, children=children, destination=destination, title=title)
        self._nodes.append(node)

        self._brackets.pop()
        if not opener.is_image:
            # A link cannot contain a link, so every "[" below this one is made inactive. Every time this happens the
            # whole stack is covered, so below an inactive "[" there is nothing left to do.
            for earlier in reversed(self._brackets):
                if not earlier.is_image:
                    if not earlier.active:
                        break
                    earlier.active = False

        self._pos = end_position
        return

    def _parse_inline_destination(self, position: int) -> Optional[Tuple[str, str, int]]:
        """
            Parses ``(destination "title")`` after a closing bracket.

            :param position: The position just after the ``]``.

            :returns: ``(destination, title, position after the closing parenthesis)``, or None when there is no
                      inline destination at the position.
        """
        if self._char_at(position) != "(":
            return None

        cursor = self._skip_link_whitespace(position + 1)

        parsed_destination = self._parse_destination(cursor)
        if parsed_destination is None:
            return None
        raw_destination, after_destination = parsed_destination

        cursor = self._skip_link_whitespace(after_destination)
        raw_title = ""
        opener = self._char_at(cursor)
        if cursor > after_destination and (opener == '"' or opener == "'" or opener == "("):
            parsed_title = self._parse_title(cursor)
            if parsed_title is None:
                return None
            raw_title, after_title = parsed_title
            cursor = self._skip_link_whitespace(after_title)

        if self._char_at(cursor) != ")":
            return None

        destination = unescape_markdown(raw_destination)
        title = unescape_markdown(raw_title)
        rtnval = (destination, title, cursor + 1)
        return rtnval

    def _skip_link_whitespace(self, position: int) -> int:
        """
            Skips spaces, tabs and at most one line ending inside a link destination.

            :param position: Where to start.

            :returns: The first position that is not skipped.
        """
        cursor = position
        newline_seen = False
        while cursor < len(self._text):
            char = self._text[cursor]
            if char == " " or char == "\t":
                cursor += 1
            elif char == "\n" and not newline_seen:
                newline_seen = True
                cursor += 1
            else:
                break
        return cursor

    def _parse_destination(self, position: int) -> Optional[Tuple[str, int]]:
        """
            Parses a link destination: ``<...>`` or a run of characters without spaces whose parentheses balance.

            :param position: Where the destination starts.

            :returns: ``(destination as written, position after it)``, or None when there is no valid destination.
        """
        length = len(self._text)

        if self._char_at(position) == "<":
            cursor = position + 1
            while cursor < length:
                char = self._text[cursor]
                if char == "\\" and cursor + 1 < length:
                    cursor += 2
                    continue
                if char == ">":
                    rtnval = (self._text[position + 1:cursor], cursor + 1)
                    return rtnval
                if char == "<" or char == "\n":
                    return None
                cursor += 1
            return None

        depth = 0
        cursor = position
        while cursor < length:
            char = self._text[cursor]
            if char == "\\" and cursor + 1 < length and self._text[cursor + 1] in MARKDOWN_ESCAPABLE_CHARACTERS:
                cursor += 2
                continue
            if char == "(":
                depth += 1
                if depth > 32:
                    return None
            elif char == ")":
                if depth == 0:
                    break
                depth -= 1
            elif char.isspace() or ord(char) < 0x20:
                break
            cursor += 1

        if depth != 0:
            return None

        rtnval = (self._text[position:cursor], cursor)
        return rtnval

    def _parse_title(self, position: int) -> Optional[Tuple[str, int]]:
        """
            Parses a link title in double quotes, single quotes or parentheses.

            :param position: The position of the opening quote or parenthesis.

            :returns: ``(title as written, position after the closing character)``, or None when the title is not
                      closed.
        """
        opener = self._text[position]
        if opener == "(":
            closer = ")"
        else:
            closer = opener

        cursor = position + 1
        length = len(self._text)
        while cursor < length:
            char = self._text[cursor]
            if char == "\\" and cursor + 1 < length:
                cursor += 2
                continue
            if char == closer:
                rtnval = (self._text[position + 1:cursor], cursor + 1)
                return rtnval
            if opener == "(" and char == "(":
                return None
            cursor += 1
        return None

    def _parse_reference(self, position: int, label_text: str) -> Optional[Tuple[str, str, int]]:
        """
            Resolves a full (``[text][label]``), collapsed (``[text][]``) or shortcut (``[text]``) reference.

            :param position: The position just after the ``]`` of the link text.
            :param label_text: The link text as written, used as the label of collapsed and shortcut references.

            :returns: ``(destination, title, position after the reference)``, or None when the reference is not
                      defined.
        """
        if self._char_at(position) == "[":
            close = self._find_label_end(position + 1)
            if close >= 0:
                inner = self._text[position + 1:close]
                if inner.strip() == "":
                    label = label_text
                else:
                    label = inner
                definition = self._lookup_definition(label)
                if definition is not None:
                    destination, title = definition
                    rtnval = (destination, title, close + 1)
                    return rtnval
                if inner.strip() != "":
                    return None

        definition = self._lookup_definition(label_text)
        if definition is None:
            return None

        destination, title = definition
        rtnval = (destination, title, position)
        return rtnval

    def _find_label_end(self, position: int) -> int:
        """
            Finds the ``]`` that closes a reference label. A label may not hold an unescaped ``[``.

            :param position: The position just after the ``[`` that opens the label.

            :returns: The position of the closing ``]``, or -1 when there is none.
        """
        cursor = position
        length = len(self._text)
        while cursor < length and cursor - position <= MARKDOWN_MAX_LABEL_LENGTH:
            char = self._text[cursor]
            if char == "\\" and cursor + 1 < length:
                cursor += 2
                continue
            if char == "[":
                return -1
            if char == "]":
                return cursor
            cursor += 1
        return -1

    def _lookup_definition(self, label: str) -> Optional[Tuple[str, str]]:
        """
            Finds the definition of a reference label.

            :param label: The label as written.

            :returns: ``(destination, title)``, or None when the label is not defined.
        """
        if len(label) > MARKDOWN_MAX_LABEL_LENGTH:
            return None

        normalized = normalize_link_label(label)
        if normalized == "":
            return None

        rtnval = self._definitions.get(normalized)
        return rtnval

    def _parse_angle_bracket(self) -> None:
        """
            ``<`` starts an autolink to a URI or an email address; otherwise it is text.
        """
        uri_match = MARKDOWN_AUTOLINK_URI_PATTERN.match(self._text, self._pos)
        if uri_match is not None:
            address = uri_match.group(1)
            label = InlineNode(INLINE_KIND_TEXT, text=address)
            self._nodes.append(InlineNode(INLINE_KIND_LINK, children=[label], destination=address))
            self._pos = uri_match.end()
            return

        email_match = MARKDOWN_AUTOLINK_EMAIL_PATTERN.match(self._text, self._pos)
        if email_match is not None:
            address = email_match.group(1)
            label = InlineNode(INLINE_KIND_TEXT, text=address)
            destination = "mailto:{}".format(address)
            self._nodes.append(InlineNode(INLINE_KIND_LINK, children=[label], destination=destination))
            self._pos = email_match.end()
            return

        self._append_text("<")
        self._pos += 1
        return

    def _parse_entity(self) -> None:
        """
            An entity reference becomes the character it stands for; an unknown one, or a lone ``&``, is text.
        """
        match = MARKDOWN_ENTITY_PATTERN.match(self._text, self._pos)
        if match is None:
            self._append_text("&")
            self._pos += 1
            return

        entity = match.group(0)
        decoded = decode_entity(entity)
        self._append_text(decoded)
        self._pos = match.end()
        return

    def _parse_line_ending(self) -> None:
        """
            A line ending is a hard break when the line ended with two or more spaces, and a soft break otherwise.
            Trailing spaces before it and leading spaces after it are dropped.
        """
        hard = False
        if len(self._nodes) > 0:
            last = self._nodes[-1]
            if last.kind == INLINE_KIND_TEXT:
                stripped = last.text.rstrip(" ")
                trailing = len(last.text) - len(stripped)
                if trailing >= 2:
                    hard = True
                last.text = stripped

        if hard:
            self._nodes.append(InlineNode(INLINE_KIND_HARD_BREAK))
        else:
            self._nodes.append(InlineNode(INLINE_KIND_SOFT_BREAK))

        self._pos += 1
        self._skip_leading_spaces()
        return

    def _skip_leading_spaces(self) -> None:
        """
            Skips the spaces at the start of a line.
        """
        length = len(self._text)
        while self._pos < length and self._text[self._pos] == " ":
            self._pos += 1
        return

    def _last_index_of(self, node: InlineNode) -> int:
        """
            The position of a node in the node list, compared by identity and searched from the end. The node of an
            opening bracket is found this way: everything behind it is about to become the content of its link, so
            the search costs no more than the link has nodes.

            :param node: The node.

            :returns: Its position.

            :raises: ValueError
        """
        index = len(self._nodes) - 1
        while index >= 0:
            if self._nodes[index] is node:
                return index
            index -= 1

        errmsg = "The inline node {!r} is not in the node list of the parser.".format(node)
        raise ValueError(errmsg)

    def _process_emphasis(self, *, bottom: int, first_node: int) -> None:
        """
            Matches openers and closers on the delimiter stack above ``bottom`` and wraps what is between them in
            emphasis, strong or strikethrough nodes, following the "process emphasis" procedure of CommonMark.

            The delimiters above ``bottom`` are taken off the stack and linked to their neighbours by position, and
            the nodes they belong to are put in an :class:`InlineNodeChain`, so matching a pair costs the same however
            many delimiters and nodes there are. For each kind of closer the procedure remembers how far down the
            stack it has already looked without finding an opener (the "openers bottom" of CommonMark) and does not
            look there again.

            :param bottom: The height of the stack below which delimiters are left alone.
            :param first_node: The position in the node list of the first node that can belong to a delimiter above
                               ``bottom``. The nodes before it are left alone.
        """
        runs = self._delimiters[bottom:]
        del self._delimiters[bottom:]

        total = len(runs)
        if total == 0:
            return

        chain = InlineNodeChain(self._nodes[first_node:])

        # The delimiters as a linked sequence: previous_run[i] and next_run[i] are the positions in "runs" of the
        # neighbours of runs[i] that are still on the stack.
        previous_run: List[int] = []
        next_run: List[int] = []
        for position in range(total):
            previous_run.append(position - 1)
            next_run.append(position + 1)
        next_run[total - 1] = MARKDOWN_NO_DELIMITER

        # For each kind of closer, the position at or below which no opener can match it.
        openers_bottom: Dict[Tuple[str, bool, int], int] = {}

        current = 0
        while current != MARKDOWN_NO_DELIMITER:
            closer = runs[current]
            if not closer.can_close:
                current = next_run[current]
                continue

            closer_kind = self._closer_kind(closer)
            search_bottom = openers_bottom.get(closer_kind, MARKDOWN_NO_DELIMITER)

            found = MARKDOWN_NO_DELIMITER
            candidate = previous_run[current]
            while candidate > search_bottom:
                opener = runs[candidate]
                if opener.char == closer.char and opener.can_open and self._delimiters_match(opener=opener, closer=closer):
                    found = candidate
                    break
                candidate = previous_run[candidate]

            if found != MARKDOWN_NO_DELIMITER:
                current = self._apply_emphasis(runs, previous_run, next_run, chain, opener_index=found, closer_index=current)
                continue

            # No opener matches this kind of closer anywhere below it.
            openers_bottom[closer_kind] = previous_run[current]

            following = next_run[current]
            if not closer.can_open:
                self._unlink_delimiter(previous_run, next_run, current)
            current = following

        self._nodes[first_node:] = chain.to_list()
        return

    def _closer_kind(self, closer: DelimiterRun) -> Tuple[str, bool, int]:
        """
            What decides whether an opener matches a closer, apart from the opener itself: the closer's character and,
            for ``*`` and ``_``, whether it can also open and its original length modulo three (the "multiple of three"
            rule); for ``~``, its length. Two closers of the same kind are matched by exactly the same openers.

            :param closer: The closing run.

            :returns: The kind, usable as a dictionary key.
        """
        if closer.char == "~":
            rtnval = (closer.char, False, closer.count)
        else:
            rtnval = (closer.char, closer.can_open, closer.original_count % 3)
        return rtnval

    def _unlink_delimiter(self, previous_run: List[int], next_run: List[int], position: int) -> None:
        """
            Takes a delimiter out of the linked sequence of delimiters.

            :param previous_run: For each delimiter, the position of the delimiter before it.
            :param next_run: For each delimiter, the position of the delimiter after it.
            :param position: The position of the delimiter to take out.
        """
        before = previous_run[position]
        after = next_run[position]

        if before != MARKDOWN_NO_DELIMITER:
            next_run[before] = after
        if after != MARKDOWN_NO_DELIMITER:
            previous_run[after] = before

        return

    def _delimiters_match(self, *, opener: DelimiterRun, closer: DelimiterRun) -> bool:
        """
            Whether an opener can be closed by a closer of the same character. Tildes match a run of the same length.
            For ``*`` and ``_``, when either run could both open and close, the lengths may not add up to a multiple
            of three unless both are multiples of three.

            :param opener: The opening run.
            :param closer: The closing run.

            :returns: True when they match.
        """
        if closer.char == "~":
            rtnval = opener.count == closer.count
            return rtnval

        rtnval = True
        if opener.can_close or closer.can_open:
            total = opener.original_count + closer.original_count
            if total % 3 == 0:
                both_multiples = opener.original_count % 3 == 0 and closer.original_count % 3 == 0
                if not both_multiples:
                    rtnval = False

        return rtnval

    def _apply_emphasis(self, runs: List[DelimiterRun], previous_run: List[int], next_run: List[int], chain: InlineNodeChain,
                        *, opener_index: int, closer_index: int) -> int:
        """
            Wraps the nodes between a matched opener and closer, uses up their delimiter characters and removes the
            delimiters between them from the stack.

            :param runs: The delimiters being processed.
            :param previous_run: For each delimiter, the position of the delimiter before it.
            :param next_run: For each delimiter, the position of the delimiter after it.
            :param chain: The nodes the delimiters belong to.
            :param opener_index: The position of the opener in ``runs``.
            :param closer_index: The position of the closer in ``runs``.

            :returns: The position in ``runs`` to continue from, or :data:`MARKDOWN_NO_DELIMITER` at the end.
        """
        opener = runs[opener_index]
        closer = runs[closer_index]

        if closer.char == "~":
            used = closer.count
            kind = INLINE_KIND_STRIKETHROUGH
        elif opener.count >= 2 and closer.count >= 2:
            used = 2
            kind = INLINE_KIND_STRONG
        else:
            used = 1
            kind = INLINE_KIND_EMPHASIS

        opener.count -= used
        closer.count -= used
        opener.node.text = opener.node.text[:len(opener.node.text) - used]
        closer.node.text = closer.node.text[used:]

        open_position = chain.position_of(opener.node)
        close_position = chain.position_of(closer.node)
        wrapper = InlineNode(kind)
        chain.wrap_between(open_position, close_position, wrapper)

        # The delimiters between the opener and the closer are inside the wrapper now and can no longer match.
        next_run[opener_index] = closer_index
        previous_run[closer_index] = opener_index

        if opener.count == 0:
            chain.remove(open_position)
            self._unlink_delimiter(previous_run, next_run, opener_index)

        next_index = closer_index
        if closer.count == 0:
            chain.remove(close_position)
            next_index = next_run[closer_index]
            self._unlink_delimiter(previous_run, next_run, closer_index)

        return next_index

    def _limit_nesting(self, nodes: List[InlineNode]) -> None:
        """
            Makes sure emphasis, links and images nest no deeper than :data:`MARKDOWN_MAX_INLINE_NESTING`. A node
            nested deeper is replaced by its content, so its text is kept and its markup is dropped. The nodes are
            changed in place.

            This walk and the flattening it does use a list of work to do rather than recursion, because the nodes it
            is given can be nested thousands deep.

            :param nodes: The top-level nodes.
        """
        pending: List[Tuple[List[InlineNode], int]] = [(nodes, 0)]
        while len(pending) > 0:
            siblings, depth = pending.pop()

            if depth >= MARKDOWN_MAX_INLINE_NESTING:
                siblings[:] = self._flatten_nodes(siblings)
                continue

            for node in siblings:
                if len(node.children) > 0:
                    pending.append((node.children, depth + 1))

        return

    def _flatten_nodes(self, nodes: List[InlineNode]) -> List[InlineNode]:
        """
            The text, code and line break nodes found in a list of nodes and in everything nested in them, in order.

            :param nodes: The nodes.

            :returns: The nodes that hold no other nodes.
        """
        flattened: List[InlineNode] = []

        pending: List[InlineNode] = list(reversed(nodes))
        while len(pending) > 0:
            node = pending.pop()

            is_container = node.kind in (INLINE_KIND_EMPHASIS, INLINE_KIND_STRONG, INLINE_KIND_STRIKETHROUGH, INLINE_KIND_LINK,
                                         INLINE_KIND_IMAGE)
            if is_container:
                pending.extend(reversed(node.children))
                continue

            flattened.append(node)

        return flattened

    def _merge_text_nodes(self, nodes: List[InlineNode]) -> List[InlineNode]:
        """
            Joins neighbouring text nodes and drops empty ones, in this list and inside every container.

            :param nodes: The nodes.

            :returns: The merged list.
        """
        merged: List[InlineNode] = []

        # The texts of the neighbouring text nodes read since the last other node. They are joined once, when the
        # run of text nodes ends; adding each one to a growing string copies that string every time.
        run_texts: List[str] = []

        for node in nodes:
            if node.kind == INLINE_KIND_TEXT:
                if node.text != "":
                    run_texts.append(node.text)
                continue

            if len(run_texts) > 0:
                merged.append(InlineNode(INLINE_KIND_TEXT, text="".join(run_texts)))
                run_texts = []

            if len(node.children) > 0:
                node.children = self._merge_text_nodes(node.children)
            merged.append(node)

        if len(run_texts) > 0:
            merged.append(InlineNode(INLINE_KIND_TEXT, text="".join(run_texts)))

        return merged

    def _link_bare_urls(self, nodes: List[InlineNode]) -> List[InlineNode]:
        """
            Turns bare ``http://``, ``https://`` and ``www.`` addresses in text into links. Text inside links, images
            and code is left alone.

            :param nodes: The nodes.

            :returns: The nodes with the addresses linked.
        """
        result: List[InlineNode] = []
        for node in nodes:
            if node.kind == INLINE_KIND_TEXT:
                pieces = self._split_bare_urls(node.text)
                result.extend(pieces)
                continue

            if node.kind == INLINE_KIND_EMPHASIS or node.kind == INLINE_KIND_STRONG or node.kind == INLINE_KIND_STRIKETHROUGH:
                node.children = self._link_bare_urls(node.children)

            result.append(node)

        return result

    def _split_bare_urls(self, text: str) -> List[InlineNode]:
        """
            Splits a text node around the bare addresses in it.

            :param text: The text.

            :returns: Text and link nodes.
        """
        pieces: List[InlineNode] = []
        cursor = 0
        for match in MARKDOWN_BARE_URL_PATTERN.finditer(text):
            address = self._trim_bare_url(match.group(0))
            if address == "" or address == "www." or address.endswith("://"):
                continue

            start = match.start()
            if start > cursor:
                pieces.append(InlineNode(INLINE_KIND_TEXT, text=text[cursor:start]))

            if address.startswith("www."):
                destination = "http://{}".format(address)
            else:
                destination = address

            label = InlineNode(INLINE_KIND_TEXT, text=address)
            pieces.append(InlineNode(INLINE_KIND_LINK, children=[label], destination=destination))
            cursor = start + len(address)

        if cursor < len(text):
            pieces.append(InlineNode(INLINE_KIND_TEXT, text=text[cursor:]))

        return pieces

    def _trim_bare_url(self, candidate: str) -> str:
        """
            Removes the punctuation that ends a sentence rather than an address: trailing ``?!.,:*_~'"``, closing
            parentheses that have no opening partner in the address, and a trailing entity-like ``&name;``.

            :param candidate: The address as matched.

            :returns: The trimmed address.
        """
        address = candidate
        changed = True
        while changed and address != "":
            changed = False
            last = address[-1]
            if last in MARKDOWN_BARE_URL_TRAILING_CHARACTERS:
                address = address[:-1]
                changed = True
            elif last == ")" and address.count(")") > address.count("("):
                address = address[:-1]
                changed = True
            elif last == ";":
                entity_match = re.search(r"&[A-Za-z0-9]+;$", address)
                if entity_match is not None:
                    address = address[:entity_match.start()]
                    changed = True

        return address
