"""
    Tests for the linked sequence of inline nodes that emphasis is resolved in.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []

from typing import List

from ccai import testbase

from ccai.webworks.markdown.inlinenode import INLINE_KIND_EMPHASIS, INLINE_KIND_TEXT, InlineNode
from ccai.webworks.markdown.inlinenodechain import InlineNodeChain


def _text_nodes(texts: List[str]) -> List[InlineNode]:
    """
        Creates one text node for each text.
    """
    nodes = []
    for text in texts:
        node = InlineNode(INLINE_KIND_TEXT, text=text)
        nodes.append(node)
    return nodes


def test_a_chain_lists_its_nodes_in_the_order_given():
    """
        **Feature: inline node chain**
        **Property: a chain returns the nodes it was created with in the same order, and an empty chain returns none.**
    """
    nodes = _text_nodes(["a", "b", "c"])

    listed = InlineNodeChain(nodes).to_list()
    empty = InlineNodeChain([]).to_list()

    testbase.assert_equal(([node.text for node in listed], empty), (["a", "b", "c"], []))
    return


def test_wrapping_moves_the_nodes_between_two_nodes_into_the_wrapper():
    """
        **Feature: inline node chain**
        **Property: wrapping between two nodes makes the nodes between them the children of the wrapper, in order, and leaves the wrapper in their
        place.**
    """
    nodes = _text_nodes(["*", "a", "b", "*", "c"])
    chain = InlineNodeChain(nodes)
    wrapper = InlineNode(INLINE_KIND_EMPHASIS)

    chain.wrap_between(chain.position_of(nodes[0]), chain.position_of(nodes[3]), wrapper)

    listed = chain.to_list()
    testbase.assert_equal(
        ([node.kind for node in listed], listed[1] is wrapper, [child.text for child in wrapper.children]),
        ([INLINE_KIND_TEXT, INLINE_KIND_EMPHASIS, INLINE_KIND_TEXT, INLINE_KIND_TEXT], True, ["a", "b"]),
    )
    return


def test_wrapping_two_neighbours_gives_an_empty_wrapper_between_them():
    """
        **Feature: inline node chain**
        **Property: wrapping between two nodes that are next to each other puts a wrapper without children between them.**
    """
    nodes = _text_nodes(["*", "*"])
    chain = InlineNodeChain(nodes)
    wrapper = InlineNode(INLINE_KIND_EMPHASIS)

    chain.wrap_between(0, 1, wrapper)

    listed = chain.to_list()
    testbase.assert_equal((len(listed), listed[1] is wrapper, wrapper.children), (3, True, []))
    return


def test_positions_stay_valid_after_wrapping_and_removing():
    """
        **Feature: inline node chain**
        **Property: after nodes are wrapped and removed, the nodes still in the chain have the positions they had before.**
    """
    nodes = _text_nodes(["a", "*", "b", "*", "c", "d"])
    chain = InlineNodeChain(nodes)
    before = [chain.position_of(nodes[0]), chain.position_of(nodes[4]), chain.position_of(nodes[5])]

    chain.wrap_between(chain.position_of(nodes[1]), chain.position_of(nodes[3]), InlineNode(INLINE_KIND_EMPHASIS))
    chain.remove(chain.position_of(nodes[1]))
    chain.remove(chain.position_of(nodes[3]))

    after = [chain.position_of(nodes[0]), chain.position_of(nodes[4]), chain.position_of(nodes[5])]
    listed = chain.to_list()
    testbase.assert_equal(
        (after, [node.kind for node in listed]),
        (before, [INLINE_KIND_TEXT, INLINE_KIND_EMPHASIS, INLINE_KIND_TEXT, INLINE_KIND_TEXT]),
    )
    return


def test_removing_the_first_and_last_nodes_leaves_the_rest():
    """
        **Feature: inline node chain**
        **Property: the first node and the last node of a chain can be removed, and the nodes between them remain in order.**
    """
    nodes = _text_nodes(["a", "b", "c", "d"])
    chain = InlineNodeChain(nodes)

    chain.remove(0)
    chain.remove(3)

    testbase.assert_equal([node.text for node in chain.to_list()], ["b", "c"])
    return


def test_the_position_of_a_node_that_was_wrapped_or_never_added_is_an_error():
    """
        **Feature: inline node chain**
        **Property: asking for the position of a node that is not in the chain, because it was never added or has become the child of a wrapper,
        raises ValueError.**
    """
    nodes = _text_nodes(["*", "a", "*"])
    chain = InlineNodeChain(nodes)
    chain.wrap_between(0, 2, InlineNode(INLINE_KIND_EMPHASIS))

    raised = []
    for node in (nodes[1], InlineNode(INLINE_KIND_TEXT, text="other")):
        try:
            chain.position_of(node)
            raised.append(False)
        except ValueError:
            raised.append(True)

    testbase.assert_equal(raised, [True, True])
    return
