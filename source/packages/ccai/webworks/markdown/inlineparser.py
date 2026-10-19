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

        self._process_emphasis(bottom=0)

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

        search = run_end
        close_start = -1
        while True:
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

        self._process_emphasis(bottom=opener.delimiter_bottom)

        opener_index = self._index_of(opener.node)
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
            for earlier in self._brackets:
                if not earlier.is_image:
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

    def _index_of(self, node: InlineNode) -> int:
        """
            The position of a node in the node list, compared by identity.

            :param node: The node.

            :returns: Its position.

            :raises: ValueError
        """
        for index, candidate in enumerate(self._nodes):
            if candidate is node:
                return index

        errmsg = "The inline node {!r} is not in the node list of the parser.".format(node)
        raise ValueError(errmsg)

    def _process_emphasis(self, *, bottom: int) -> None:
        """
            Matches openers and closers on the delimiter stack above ``bottom`` and wraps what is between them in
            emphasis, strong or strikethrough nodes, following the "process emphasis" procedure of CommonMark.

            :param bottom: The height of the stack below which delimiters are left alone.
        """
        current = bottom
        while current < len(self._delimiters):
            closer = self._delimiters[current]
            if not closer.can_close:
                current += 1
                continue

            opener_index = current - 1
            found_index = -1
            while opener_index >= bottom:
                opener = self._delimiters[opener_index]
                if opener.char == closer.char and opener.can_open and self._delimiters_match(opener=opener, closer=closer):
                    found_index = opener_index
                    break
                opener_index -= 1

            if found_index >= 0:
                current = self._apply_emphasis(opener_index=found_index, closer_index=current)
            elif not closer.can_open:
                del self._delimiters[current]
            else:
                current += 1

        del self._delimiters[bottom:]
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

    def _apply_emphasis(self, *, opener_index: int, closer_index: int) -> int:
        """
            Wraps the nodes between a matched opener and closer, uses up their delimiter characters and removes the
            delimiters between them from the stack.

            :param opener_index: The position of the opener on the delimiter stack.
            :param closer_index: The position of the closer on the delimiter stack.

            :returns: The position on the delimiter stack to continue from.
        """
        opener = self._delimiters[opener_index]
        closer = self._delimiters[closer_index]

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

        open_position = self._index_of(opener.node)
        close_position = self._index_of(closer.node)
        inner = self._nodes[open_position + 1:close_position]
        wrapper = InlineNode(kind, children=inner)
        self._nodes[open_position + 1:close_position] = [wrapper]

        del self._delimiters[opener_index + 1:closer_index]
        next_index = opener_index + 1

        if opener.count == 0:
            opener_position = self._index_of(opener.node)
            del self._nodes[opener_position]
            del self._delimiters[opener_index]
            next_index -= 1

        if closer.count == 0:
            closer_position = self._index_of(closer.node)
            del self._nodes[closer_position]
            del self._delimiters[next_index]

        return next_index

    def _merge_text_nodes(self, nodes: List[InlineNode]) -> List[InlineNode]:
        """
            Joins neighbouring text nodes and drops empty ones, in this list and inside every container.

            :param nodes: The nodes.

            :returns: The merged list.
        """
        merged: List[InlineNode] = []
        for node in nodes:
            if node.kind == INLINE_KIND_TEXT:
                if node.text == "":
                    continue
                if len(merged) > 0 and merged[-1].kind == INLINE_KIND_TEXT:
                    merged[-1].text = merged[-1].text + node.text
                    continue
                merged.append(InlineNode(INLINE_KIND_TEXT, text=node.text))
                continue

            if len(node.children) > 0:
                node.children = self._merge_text_nodes(node.children)
            merged.append(node)

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
