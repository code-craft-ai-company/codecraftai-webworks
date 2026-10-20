"""
    Tests for rendering markdown as HTML.

    The renderer follows CommonMark for blocks and inlines, adds GitHub tables, strikethrough and bare-address links,
    escapes raw HTML and drops unsafe link destinations, and reports a document's title, headings and links.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []

from typing import Optional

from ccai import testbase

from ccai.webworks.markdown import MarkdownRenderer


def _html(text: str) -> str:
    """
        Renders markdown and returns the HTML.
    """
    document = MarkdownRenderer().render(text)
    rtnval = document.html
    return rtnval


def test_atx_and_setext_headings_get_levels_and_github_anchors():
    """
        **Feature: markdown headings**
        **Property: ``#`` to ``######`` give levels 1 to 6 and a closing run of ``#`` is dropped; a line underlined with ``===`` is level 1 and with
        ``---`` level 2; every heading gets the anchor GitHub would give it.**
    """
    testbase.assert_equal(
        (
            _html("# Title #"),
            _html("###### Six"),
            _html("Big\n==="),
            _html("Smaller\n---"),
            _html("#NotAHeading"),
        ),
        (
            '<h1 id="title">Title</h1>\n',
            '<h6 id="six">Six</h6>\n',
            '<h1 id="big">Big</h1>\n',
            '<h2 id="smaller">Smaller</h2>\n',
            "<p>#NotAHeading</p>\n",
        ),
    )
    return


def test_repeated_heading_text_gets_numbered_anchors():
    """
        **Feature: markdown headings**
        **Property: the second and third headings with the same text get ``-1`` and ``-2`` added to their anchor, and an em dash between spaces becomes
        two hyphens, as on GitHub.**
    """
    document = MarkdownRenderer().render("## Setup\n\n## Setup\n\n## Setup\n\n## Volume — Operating")
    anchors = [heading.anchor for heading in document.headings]
    testbase.assert_equal(anchors, ["setup", "setup-1", "setup-2", "volume--operating"])
    return


def test_the_title_is_the_first_level_one_heading():
    """
        **Feature: markdown document title**
        **Property: the title is the text of the first level-one heading, else of the first heading, and None when there are no headings; the title is
        plain text with the markup removed.**
    """
    renderer = MarkdownRenderer()
    testbase.assert_equal(
        (
            renderer.render("## Second\n\n# The *First* `One`").title,
            renderer.render("### Only a third").title,
            renderer.render("No headings.").title,
        ),
        ("The First One", "Only a third", None),
    )
    return


def test_emphasis_nests_by_the_delimiter_run_rules():
    """
        **Feature: markdown emphasis**
        **Property: single delimiters make emphasis and double ones strong emphasis, they nest, ``***`` makes both, ``_`` does not work inside a word,
        ``~~`` strikes through, and a delimiter with no partner stays as text.**
    """
    testbase.assert_equal(
        (
            _html("*a **b** c*"),
            _html("**foo*bar*baz**"),
            _html("***both***"),
            _html("snake_case_name and _em_"),
            _html("~~gone~~"),
            _html("a * b ** c"),
        ),
        (
            "<p><em>a <strong>b</strong> c</em></p>\n",
            "<p><strong>foo<em>bar</em>baz</strong></p>\n",
            "<p><em><strong>both</strong></em></p>\n",
            "<p>snake_case_name and <em>em</em></p>\n",
            "<p><del>gone</del></p>\n",
            "<p>a * b ** c</p>\n",
        ),
    )
    return


def test_code_spans_and_code_blocks_keep_their_text():
    """
        **Feature: markdown code**
        **Property: a code span closes at a run of the same number of backticks; fenced blocks (backticks or tildes) carry their language as a class;
        indented blocks are code; markup inside code is escaped, never interpreted.**
    """
    testbase.assert_equal(
        (
            _html("Use `` a`b `` here"),
            _html("```python\nx = '<b>' * 2\n```"),
            _html("~~~\nplain\n~~~"),
            _html("    indented *not em*"),
            _html("```\nunclosed"),
        ),
        (
            "<p>Use <code>a`b</code> here</p>\n",
            '<pre><code class="language-python">x = \'&lt;b&gt;\' * 2\n</code></pre>\n',
            "<pre><code>plain\n</code></pre>\n",
            "<pre><code>indented *not em*\n</code></pre>\n",
            "<pre><code>unclosed\n</code></pre>\n",
        ),
    )
    return


def test_tight_lists_have_bare_items_and_loose_lists_have_paragraphs():
    """
        **Feature: markdown lists**
        **Property: items with no blank line between them are written without ``<p>``; a blank line between items makes every item a paragraph; an
        indented list nests inside its item; an ordered list says where it starts when that is not 1.**
    """
    testbase.assert_equal(
        (
            _html("- a\n- b\n  - c"),
            _html("- a\n\n- b"),
            _html("3. three\n4. four"),
        ),
        (
            "<ul>\n<li>a</li>\n<li>b\n<ul>\n<li>c</li>\n</ul></li>\n</ul>\n",
            "<ul>\n<li>\n<p>a</p>\n</li>\n<li>\n<p>b</p>\n</li>\n</ul>\n",
            '<ol start="3">\n<li>three</li>\n<li>four</li>\n</ol>\n',
        ),
    )
    return


def test_a_change_of_list_marker_starts_a_new_list():
    """
        **Feature: markdown lists**
        **Property: ``1.`` and ``1)`` belong to different lists, as do ``-`` and ``*``.**
    """
    testbase.assert_equal(
        (_html("1. one\n2) two"), _html("- dash\n* star")),
        (
            '<ol>\n<li>one</li>\n</ol>\n<ol start="2">\n<li>two</li>\n</ol>\n',
            "<ul>\n<li>dash</li>\n</ul>\n<ul>\n<li>star</li>\n</ul>\n",
        ),
    )
    return


def test_a_list_item_holds_code_and_lazy_continuation_lines():
    """
        **Feature: markdown lists**
        **Property: a fenced block indented under an item belongs to the item, and an unindented line right after an item's paragraph continues that
        paragraph.**
    """
    testbase.assert_equal(
        (
            _html("- item\n  ```\n  code\n  ```"),
            _html("- first line\nlazy line"),
        ),
        (
            "<ul>\n<li>item\n<pre><code>code\n</code></pre></li>\n</ul>\n",
            "<ul>\n<li>first line\nlazy line</li>\n</ul>\n",
        ),
    )
    return


def test_block_quotes_nest_and_continue_lazily():
    """
        **Feature: markdown block quotes**
        **Property: ``>`` lines make a block quote whose content is parsed as blocks, ``>>`` nests, and a line without ``>`` that continues the quoted
        paragraph stays in the quote.**
    """
    testbase.assert_equal(
        (
            _html("> quoted\nlazy\n> - item"),
            _html("> outer\n>> inner"),
        ),
        (
            "<blockquote>\n<p>quoted\nlazy</p>\n<ul>\n<li>item</li>\n</ul>\n</blockquote>\n",
            "<blockquote>\n<p>outer</p>\n<blockquote>\n<p>inner</p>\n</blockquote>\n</blockquote>\n",
        ),
    )
    return


def test_tables_have_aligned_columns_and_padded_rows():
    """
        **Feature: markdown tables**
        **Property: the delimiter row sets each column's alignment as an ``align-*`` class, short rows are padded to the header's width, an escaped pipe
        stays in its cell, and a table can follow a paragraph line directly.**
    """
    table = "Intro:\n| a | b \\| c | d |\n|:--|:-:|--:|\n| 1 | 2 |"
    testbase.assert_equal(
        _html(table),
        (
            "<p>Intro:</p>\n<table>\n<thead>\n<tr>\n"
            '<th class="align-left">a</th>\n<th class="align-center">b | c</th>\n<th class="align-right">d</th>\n'
            "</tr>\n</thead>\n<tbody>\n<tr>\n"
            '<td class="align-left">1</td>\n<td class="align-center">2</td>\n<td class="align-right"></td>\n'
            "</tr>\n</tbody>\n</table>\n"
        ),
    )
    return


def test_a_delimiter_row_with_a_different_cell_count_is_not_a_table():
    """
        **Feature: markdown tables**
        **Property: when the delimiter row does not have the header's number of cells there is no table; ``a | b`` over ``---`` is a setext heading.**
    """
    testbase.assert_equal(_html("a | b\n---"), '<h2 id="a--b">a | b</h2>\n')
    return


def test_inline_reference_and_auto_links_are_written_and_collected_in_order():
    """
        **Feature: markdown links**
        **Property: inline links with titles, full, collapsed and shortcut references, ``<...>`` autolinks and bare ``https://`` and ``www.`` addresses
        all become links; trailing sentence punctuation is not part of a bare address; every link is reported with its destination and text in document
        order.**
    """
    text = (
        '[inline](http://a.example "T") [full][ref] [ref][] [ref] <https://b.example>\n'
        "See https://c.example/path. And www.d.example!\n\n"
        "[ref]: /reference\n"
    )
    document = MarkdownRenderer().render(text)
    links = [(link.destination, link.text) for link in document.links]
    testbase.assert_equal(
        (document.html, links),
        (
            '<p><a href="http://a.example" title="T">inline</a> <a href="/reference">full</a> <a href="/reference">ref</a> '
            '<a href="/reference">ref</a> <a href="https://b.example">https://b.example</a>\n'
            'See <a href="https://c.example/path">https://c.example/path</a>. And <a href="http://www.d.example">www.d.example</a>!</p>\n',
            [
                ("http://a.example", "inline"), ("/reference", "full"), ("/reference", "ref"), ("/reference", "ref"),
                ("https://b.example", "https://b.example"), ("https://c.example/path", "https://c.example/path"),
                ("http://www.d.example", "www.d.example"),
            ],
        ),
    )
    return


def test_a_link_rewriter_replaces_destinations_but_the_reported_link_keeps_the_original():
    """
        **Feature: markdown links**
        **Property: the rewriter's result is written as the ``href`` and ``src``, spaces are percent-encoded, and the reported link still carries the
        destination as written.**
    """

    def rewrite(destination: str) -> str:
        rewritten = "/site/" + destination
        return rewritten

    document = MarkdownRenderer().render("[Chapter one](<one two.md>) ![Figure](fig.png)", link_rewriter=rewrite)
    testbase.assert_equal(
        (document.html, [link.destination for link in document.links]),
        ('<p><a href="/site/one%20two.md">Chapter one</a> <img src="/site/fig.png" alt="Figure" /></p>\n', ["one two.md"]),
    )
    return


def test_raw_html_is_escaped_and_unsafe_destinations_are_dropped():
    """
        **Feature: markdown safety**
        **Property: a ``<script>`` in the text is escaped; a ``javascript:``, ``vbscript:`` or ``data:`` link keeps its text but loses its link, whatever its
        case; an image with an unsafe source becomes its description; quotes in a title are escaped.**
    """
    testbase.assert_equal(
        (
            _html("<script>alert(1)</script>"),
            _html("[x](javascript:alert(1)) [y](JavaScript:alert(1)) [z](vbscript:msgbox) [w](data:text/html,hi)"),
            _html("![pic](javascript:alert(1))"),
            _html('[t](/ok "say \\"hi\\"")'),
        ),
        (
            "<p>&lt;script&gt;alert(1)&lt;/script&gt;</p>\n",
            "<p>x y z w</p>\n",
            "<p>pic</p>\n",
            '<p><a href="/ok" title="say &quot;hi&quot;">t</a></p>\n',
        ),
    )
    return


def test_escapes_entities_and_line_breaks():
    """
        **Feature: markdown inline text**
        **Property: a backslash makes punctuation literal; known entities become their characters and unknown ones stay as text; two trailing spaces or a
        trailing backslash make a hard break, and a plain line ending stays a line ending.**
    """
    testbase.assert_equal(
        (
            _html("\\*not em\\* &copy; &bogus; &#65;"),
            _html("one  \ntwo\\\nthree\nfour"),
        ),
        (
            "<p>*not em* © &amp;bogus; A</p>\n",
            "<p>one<br />\ntwo<br />\nthree\nfour</p>\n",
        ),
    )
    return


def test_thematic_breaks_and_link_definitions_produce_no_text():
    """
        **Feature: markdown blocks**
        **Property: ``***`` and ``- - -`` are thematic breaks, and a link reference definition on its own is not written.**
    """
    testbase.assert_equal(_html("***\n\n- - -\n\n[unused]: /nowhere"), "<hr />\n<hr />\n")
    return


def test_a_link_rewriter_that_returns_none_drops_the_link_but_keeps_the_text():
    """
        **Feature: markdown links**
        **Property: when the rewriter returns None, a link is written as its text alone and an image as its description, and the link is still
        reported.**
    """

    def drop_specs(destination: str) -> Optional[str]:
        if "specs/" in destination:
            return None
        return destination

    document = MarkdownRenderer().render("See [the spec](../specs/x.md), ![chart](specs/c.png) and [Rust](https://rust-lang.org).",
                                         link_rewriter=drop_specs)
    testbase.assert_equal(
        (document.html, [link.destination for link in document.links]),
        ('<p>See the spec, chart and <a href="https://rust-lang.org">Rust</a>.</p>\n', ["../specs/x.md", "https://rust-lang.org"]),
    )
    return


def test_a_code_block_writer_writes_every_code_block():
    """
        **Feature: markdown hooks**
        **Property: the code block writer is called with the code and the fence's info string (empty for an indented block), and what it returns is
        written in the block's place.**
    """
    calls = []

    def write_code(code: str, info: str) -> str:
        calls.append((code, info))
        written = '<div class="listing">{}</div>\n'.format(len(code))
        return written

    renderer = MarkdownRenderer(code_block_writer=write_code)
    html = renderer.render("```loup,does_not_compile\nf(1)\n```\n\n    indented\n").html
    testbase.assert_equal(
        (html, calls),
        ('<div class="listing">5</div>\n<div class="listing">9</div>\n', [("f(1)\n", "loup,does_not_compile"), ("indented\n", "")]),
    )
    return


def test_a_paragraph_classifier_classes_paragraphs_and_their_text_is_reported():
    """
        **Feature: markdown hooks**
        **Property: the classifier sees each paragraph's markdown source and a name it returns becomes the paragraph's class; every paragraph's plain
        text is reported in document order, including paragraphs inside block quotes and lists.**
    """

    def classify(source: str) -> Optional[str]:
        if source.startswith("*Listing"):
            return "listing-caption"
        return None

    renderer = MarkdownRenderer(paragraph_classifier=classify)
    document = renderer.render("First *one*.\n\n*Listing 1-1: Hello*\n\n> Quoted\n\n- Item")
    testbase.assert_equal(
        (document.html.split("\n")[:2], document.paragraphs),
        (['<p>First <em>one</em>.</p>', '<p class="listing-caption"><em>Listing 1-1: Hello</em></p>'], ("First one.", "Listing 1-1: Hello", "Quoted", "Item")),
    )
    return
