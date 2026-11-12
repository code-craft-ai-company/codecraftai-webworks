"""
    Tests for splitting markdown text into blocks.

    These cover the cost of parsing as well as its result: a container that takes lazy continuation lines, and a
    heading with a long run of spaces, must be read in time that grows with the length of the text, not its square.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []

import time

from ccai import testbase

from ccai.webworks.markdown.blocknode import BLOCK_KIND_BLOCKQUOTE, BLOCK_KIND_HEADING, BLOCK_KIND_LIST, BLOCK_KIND_PARAGRAPH
from ccai.webworks.markdown.blockparser import BlockParser

#: How long parsing one of the large texts below may take. Each takes well under a tenth of this; the quadratic
#: parsing they guard against took several times longer than this.
PARSE_TIME_LIMIT_SECONDS = 3.0


def test_lazy_continuation_lines_of_a_block_quote_are_read_in_linear_time():
    """
        **Feature: markdown block quotes**
        **Property: a block quote followed by 8,000 lazy continuation lines is one quote holding one paragraph with every line, and parsing it takes
        no more than a few seconds.**
    """
    line_count = 8000
    text = "> a\n" + "b\n" * line_count

    started = time.perf_counter()
    blocks = BlockParser().parse(text)
    elapsed = time.perf_counter() - started

    quote = blocks[0]
    paragraph = quote.children[0]
    testbase.assert_equal(
        (len(blocks), quote.kind, len(quote.children), paragraph.kind, paragraph.text.count("\n")),
        (1, BLOCK_KIND_BLOCKQUOTE, 1, BLOCK_KIND_PARAGRAPH, line_count),
    )
    testbase.assert_lessthan(elapsed, PARSE_TIME_LIMIT_SECONDS, api="BlockParser.parse of a block quote with 8,000 lazy continuation lines (seconds)")
    return


def test_lazy_continuation_lines_of_a_list_item_are_read_in_linear_time():
    """
        **Feature: markdown lists**
        **Property: a list item followed by 8,000 lazy continuation lines is one item holding one paragraph with every line, and parsing it takes no
        more than a few seconds.**
    """
    line_count = 8000
    text = "- a\n" + "b\n" * line_count

    started = time.perf_counter()
    blocks = BlockParser().parse(text)
    elapsed = time.perf_counter() - started

    items = blocks[0].children
    paragraph = items[0].children[0]
    testbase.assert_equal(
        (len(blocks), blocks[0].kind, len(items), paragraph.kind, paragraph.text.count("\n")),
        (1, BLOCK_KIND_LIST, 1, BLOCK_KIND_PARAGRAPH, line_count),
    )
    testbase.assert_lessthan(elapsed, PARSE_TIME_LIMIT_SECONDS, api="BlockParser.parse of a list item with 8,000 lazy continuation lines (seconds)")
    return


def test_a_line_after_an_open_fence_in_a_block_quote_is_not_a_lazy_continuation():
    """
        **Feature: markdown block quotes**
        **Property: a line without ``>`` that follows a quote ending inside an open code fence is not taken into the quote, while the same line after
        the fence has been closed and a paragraph started is.**
    """
    open_fence_blocks = BlockParser().parse("> ```\n> code\nafter")
    closed_fence_blocks = BlockParser().parse("> ```\n> code\n> ```\n> text\nafter")

    open_fence_kinds = [block.kind for block in open_fence_blocks]
    closed_fence_kinds = [block.kind for block in closed_fence_blocks]
    closed_fence_paragraph = closed_fence_blocks[0].children[1]

    testbase.assert_equal(
        (open_fence_kinds, closed_fence_kinds, closed_fence_paragraph.text),
        ([BLOCK_KIND_BLOCKQUOTE, BLOCK_KIND_PARAGRAPH], [BLOCK_KIND_BLOCKQUOTE], "text\nafter"),
    )
    return


def test_a_line_after_an_open_fence_in_a_list_item_is_not_a_lazy_continuation():
    """
        **Feature: markdown lists**
        **Property: a line that is not indented and follows a list item ending inside an open code fence is not taken into the item.**
    """
    blocks = BlockParser().parse("- ```\n  code\nafter")

    kinds = [block.kind for block in blocks]
    testbase.assert_equal(kinds, [BLOCK_KIND_LIST, BLOCK_KIND_PARAGRAPH])
    return


def test_a_heading_with_a_long_run_of_spaces_is_read_in_linear_time():
    """
        **Feature: markdown headings**
        **Property: a heading whose text holds a run of 40,000 spaces keeps its text, and parsing it takes no more than a few seconds.**
    """
    space_count = 40000
    text = "# a" + " " * space_count + "b"

    started = time.perf_counter()
    blocks = BlockParser().parse(text)
    elapsed = time.perf_counter() - started

    heading = blocks[0]
    testbase.assert_equal((heading.kind, heading.level, heading.text), (BLOCK_KIND_HEADING, 1, "a" + " " * space_count + "b"))
    testbase.assert_lessthan(elapsed, PARSE_TIME_LIMIT_SECONDS, api="BlockParser.parse of a heading with a run of 40,000 spaces (seconds)")
    return


def test_a_closing_run_of_hashes_is_dropped_only_after_a_space():
    """
        **Feature: markdown headings**
        **Property: a closing run of ``#`` is removed from a heading with the spaces before it when it follows a space or a tab or is the whole
        content, and is kept when it follows any other character.**
    """
    texts = ["# Title ##", "# Title\t#", "## ##", "# Title#", "# C# and F#", "# a # b ###   "]

    heading_texts = []
    for text in texts:
        blocks = BlockParser().parse(text)
        heading_texts.append(blocks[0].text)

    testbase.assert_equal(heading_texts, ["Title", "Title", "", "Title#", "C# and F#", "a # b"])
    return
