"""
    Tests for parsing the inline content of a markdown block.

    These cover the cost of parsing as well as its result: emphasis, links and code spans must be resolved in time that
    grows with the length of the text, not its square, and markup nested without limit must not exhaust the stack.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []

import time

from typing import List

from ccai import testbase

from ccai.webworks.markdown import MarkdownRenderer
from ccai.webworks.markdown.inlinenode import (
    INLINE_KIND_CODE,
    INLINE_KIND_EMPHASIS,
    INLINE_KIND_LINK,
    INLINE_KIND_STRIKETHROUGH,
    INLINE_KIND_STRONG,
    INLINE_KIND_TEXT,
    InlineNode,
)
from ccai.webworks.markdown.inlineparser import MARKDOWN_MAX_INLINE_NESTING, InlineParser

#: How long parsing one of the large texts below may take. Each takes well under a fifth of this; the quadratic
#: parsing they guard against took several times longer than this.
PARSE_TIME_LIMIT_SECONDS = 3.0


def _nesting_depth(nodes: List[InlineNode]) -> int:
    """
        How deeply the nodes nest: 0 for nodes without children. Walks with a list of work to do, so it can measure
        a nesting that recursion could not.
    """
    deepest = 0
    pending = [(nodes, 0)]
    while len(pending) > 0:
        siblings, depth = pending.pop()
        if depth > deepest:
            deepest = depth
        for node in siblings:
            if len(node.children) > 0:
                pending.append((node.children, depth + 1))
    return deepest


def test_many_emphasis_pairs_are_resolved_in_linear_time():
    """
        **Feature: markdown emphasis**
        **Property: 8,000 separate ``*a*`` pairs each become an emphasis node, and parsing them takes no more than a few seconds.**
    """
    pair_count = 8000
    text = "*a* " * pair_count

    started = time.perf_counter()
    nodes = InlineParser().parse(text)
    elapsed = time.perf_counter() - started

    emphasis_count = 0
    for node in nodes:
        if node.kind == INLINE_KIND_EMPHASIS:
            emphasis_count += 1

    testbase.assert_equal(emphasis_count, pair_count)
    testbase.assert_lessthan(elapsed, PARSE_TIME_LIMIT_SECONDS, api="InlineParser.parse of 8,000 emphasis pairs (seconds)")
    return


def test_closers_without_an_opener_do_not_rescan_the_openers():
    """
        **Feature: markdown emphasis**
        **Property: 8,000 ``*`` openers followed by 8,000 ``_`` closers that match none of them stay text, and parsing them takes no more than a
        few seconds.**
    """
    run_count = 8000
    text = "*a " * run_count + "b_ " * run_count

    started = time.perf_counter()
    nodes = InlineParser().parse(text)
    elapsed = time.perf_counter() - started

    testbase.assert_equal(([node.kind for node in nodes], nodes[0].text), ([INLINE_KIND_TEXT], text))
    testbase.assert_lessthan(elapsed, PARSE_TIME_LIMIT_SECONDS, api="InlineParser.parse of 8,000 openers and 8,000 closers that do not match (seconds)")
    return


def test_many_links_are_resolved_in_linear_time():
    """
        **Feature: markdown links**
        **Property: 16,000 inline links each become a link node, and parsing them takes no more than a few seconds.**
    """
    link_count = 16000
    text = "[a](b) " * link_count

    started = time.perf_counter()
    nodes = InlineParser().parse(text)
    elapsed = time.perf_counter() - started

    found_count = 0
    for node in nodes:
        if node.kind == INLINE_KIND_LINK:
            found_count += 1

    testbase.assert_equal(found_count, link_count)
    testbase.assert_lessthan(elapsed, PARSE_TIME_LIMIT_SECONDS, api="InlineParser.parse of 16,000 links (seconds)")
    return


def test_backtick_runs_without_a_closing_run_are_read_in_linear_time():
    """
        **Feature: markdown code spans**
        **Property: runs of backticks of 700 different lengths, none of which has a closing run, stay text, and parsing them takes no more than a
        few seconds.**
    """
    runs = []
    for run_length in range(1, 701):
        runs.append("`" * run_length)
    text = " ".join(runs)

    started = time.perf_counter()
    nodes = InlineParser().parse(text)
    elapsed = time.perf_counter() - started

    testbase.assert_equal(([node.kind for node in nodes], nodes[0].text), ([INLINE_KIND_TEXT], text))
    testbase.assert_lessthan(elapsed, PARSE_TIME_LIMIT_SECONDS, api="InlineParser.parse of 700 backtick runs without a closing run (seconds)")
    return


def test_a_code_span_is_closed_by_the_next_run_of_the_same_length():
    """
        **Feature: markdown code spans**
        **Property: a run of backticks opens a code span closed by the next run of the same length, a longer run between them is part of the code,
        and a run with no closing run after it is text.**
    """
    nodes = InlineParser().parse("`a ``` b` c `` d")

    testbase.assert_equal(
        [(node.kind, node.text) for node in nodes],
        [(INLINE_KIND_CODE, "a ``` b"), (INLINE_KIND_TEXT, " c `` d")],
    )
    return


def test_emphasis_strong_and_strikethrough_are_matched():
    """
        **Feature: markdown emphasis**
        **Property: ``*`` and ``_`` pairs give emphasis, doubled pairs give strong, ``~~`` pairs give strikethrough, they nest, and a run that
        matches nothing stays text.**
    """
    nodes = InlineParser().parse("*a* __b__ ~~c~~ ***d*** *e **f** g* h*")

    kinds = [node.kind for node in nodes]
    nested_strong = nodes[6].children[0]
    nested_emphasis = nodes[8].children[1]

    testbase.assert_equal(
        (kinds, nested_strong.kind, nested_emphasis.kind, nodes[9].text),
        (
            [INLINE_KIND_EMPHASIS, INLINE_KIND_TEXT, INLINE_KIND_STRONG, INLINE_KIND_TEXT, INLINE_KIND_STRIKETHROUGH, INLINE_KIND_TEXT,
             INLINE_KIND_EMPHASIS, INLINE_KIND_TEXT, INLINE_KIND_EMPHASIS, INLINE_KIND_TEXT],
            INLINE_KIND_STRONG,
            INLINE_KIND_STRONG,
            " h*",
        ),
    )
    return


def test_the_multiple_of_three_rule_decides_which_opener_a_closer_takes():
    """
        **Feature: markdown emphasis**
        **Property: a closer does not take an opener when either could both open and close and their lengths add up to a multiple of three, unless
        both lengths are multiples of three, so ``*foo**bar*`` is one emphasis and ``**foo*bar**`` has the single ``*`` as text.**
    """
    first = InlineParser().parse("*foo**bar*")
    second = InlineParser().parse("foo***bar***baz")

    testbase.assert_equal(
        (
            [node.kind for node in first],
            first[0].to_text(),
            [node.kind for node in second],
            second[1].children[0].kind,
        ),
        (
            [INLINE_KIND_EMPHASIS],
            "foo**bar",
            [INLINE_KIND_TEXT, INLINE_KIND_EMPHASIS, INLINE_KIND_TEXT],
            INLINE_KIND_STRONG,
        ),
    )
    return


def test_adjacent_text_is_merged_into_one_node():
    """
        **Feature: markdown inline text**
        **Property: text read in pieces (around an escape, an unmatched delimiter and an entity) is returned as one text node.**
    """
    nodes = InlineParser().parse("a \\* b * c &amp; d")

    testbase.assert_equal([(node.kind, node.text) for node in nodes], [(INLINE_KIND_TEXT, "a * b * c & d")])
    return


def test_emphasis_nested_without_limit_is_cut_off_at_the_nesting_limit():
    """
        **Feature: markdown emphasis**
        **Property: 1,200 emphasis pairs nested in each other nest only as deep as the limit; the text of the pairs beyond it is kept.**
    """
    pair_count = 1200
    text = "*a " * pair_count + " a*" * pair_count

    nodes = InlineParser().parse(text)

    plain_parts = []
    for node in nodes:
        plain_parts.append(node.to_text())
    plain_text = "".join(plain_parts)

    testbase.assert_equal(
        (_nesting_depth(nodes), plain_text.count("a")),
        (MARKDOWN_MAX_INLINE_NESTING, pair_count * 2),
    )
    return


def test_images_nested_without_limit_are_cut_off_at_the_nesting_limit():
    """
        **Feature: markdown images**
        **Property: 1,200 images nested in each other's descriptions nest only as deep as the limit.**
    """
    image_count = 1200
    text = "![" * image_count + "a" + "](u)" * image_count

    nodes = InlineParser().parse(text)

    testbase.assert_equal(_nesting_depth(nodes), MARKDOWN_MAX_INLINE_NESTING)
    return


def test_deeply_nested_emphasis_renders_instead_of_raising():
    """
        **Feature: markdown emphasis**
        **Property: a paragraph of 1,200 nested emphasis pairs renders as HTML with as many ``<em>`` elements as the nesting limit, instead of
        raising RecursionError.**
    """
    pair_count = 1200
    text = "*a " * pair_count + " a*" * pair_count

    document = MarkdownRenderer().render(text)

    testbase.assert_equal(
        (document.html.count("<em>"), document.html.count("</em>")),
        (MARKDOWN_MAX_INLINE_NESTING, MARKDOWN_MAX_INLINE_NESTING),
    )
    return


def test_nesting_up_to_the_limit_keeps_its_markup():
    """
        **Feature: markdown emphasis**
        **Property: emphasis nested exactly as deep as the limit is kept whole.**
    """
    pair_count = MARKDOWN_MAX_INLINE_NESTING
    text = "*a " * pair_count + " a*" * pair_count

    document = MarkdownRenderer().render(text)

    testbase.assert_equal(document.html.count("<em>"), pair_count)
    return
