"""
.. module:: inlinenodechain
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: A linked sequence of inline nodes whose positions stay valid while nodes are wrapped and removed.

.. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []

from typing import Dict, List

from ccai.webworks.markdown.inlinenode import InlineNode

#: The position that stands for "no node": before the first node or after the last one.
INLINE_CHAIN_NO_POSITION = -1


class InlineNodeChain:
    """
        The inline nodes of a block as a doubly linked sequence.

        Resolving emphasis wraps the nodes between two delimiters in a new node and removes delimiters that are used
        up, once for every pair of delimiters. In a plain list each of those steps has to find a node by searching for
        it and then moves every node behind it, so a text with many pairs takes time that grows with the square of its
        length. In the chain a node keeps the position it was given when it was added, finding it is a dictionary
        lookup, and wrapping or removing touches only the nodes involved.

        Positions are plain integers. The nodes the chain was created with have the positions ``0``, ``1``, ``2`` and
        so on; a wrapper gets the next unused position. :data:`INLINE_CHAIN_NO_POSITION` stands for no node.
    """

    def __init__(self, nodes: List[InlineNode]):
        """
            Creates a chain that holds the nodes in the order given.

            :param nodes: The nodes.
        """
        self._nodes: List[InlineNode] = list(nodes)
        self._previous: List[int] = []
        self._next: List[int] = []
        self._positions: Dict[int, int] = {}

        count = len(self._nodes)
        for position in range(count):
            node = self._nodes[position]
            self._previous.append(position - 1)
            self._next.append(position + 1)
            self._positions[id(node)] = position

        self._first = INLINE_CHAIN_NO_POSITION
        if count > 0:
            self._first = 0
            self._next[count - 1] = INLINE_CHAIN_NO_POSITION

        return

    def position_of(self, node: InlineNode) -> int:
        """
            The position of a node, compared by identity.

            :param node: The node.

            :returns: Its position.

            :raises: ValueError
        """
        node_key = id(node)
        if node_key not in self._positions:
            errmsg = "The inline node {!r} is not in the node chain.".format(node)
            raise ValueError(errmsg)

        rtnval = self._positions[node_key]
        return rtnval

    def wrap_between(self, open_position: int, close_position: int, wrapper: InlineNode) -> int:
        """
            Moves the nodes that lie between two nodes into ``wrapper.children`` and puts the wrapper in their place.

            :param open_position: The position of the node before the first node to wrap.
            :param close_position: The position of the node after the last node to wrap. It must come after
                                   ``open_position`` in the chain.
            :param wrapper: The node that receives the wrapped nodes as its children.

            :returns: The position of the wrapper.
        """
        inner: List[InlineNode] = []
        cursor = self._next[open_position]
        while cursor != close_position:
            if cursor == INLINE_CHAIN_NO_POSITION:
                errmsg = "The node at position {} does not come after the node at position {} in the node chain.".format(
                    close_position, open_position)
                raise ValueError(errmsg)

            inner_node = self._nodes[cursor]
            inner.append(inner_node)
            del self._positions[id(inner_node)]
            cursor = self._next[cursor]

        wrapper.children = inner

        wrapper_position = len(self._nodes)
        self._nodes.append(wrapper)
        self._previous.append(open_position)
        self._next.append(close_position)
        self._positions[id(wrapper)] = wrapper_position

        self._next[open_position] = wrapper_position
        self._previous[close_position] = wrapper_position

        return wrapper_position

    def remove(self, position: int) -> None:
        """
            Takes a node out of the chain.

            :param position: The position of the node.
        """
        node = self._nodes[position]
        del self._positions[id(node)]

        previous_position = self._previous[position]
        next_position = self._next[position]

        if previous_position == INLINE_CHAIN_NO_POSITION:
            self._first = next_position
        else:
            self._next[previous_position] = next_position

        if next_position != INLINE_CHAIN_NO_POSITION:
            self._previous[next_position] = previous_position

        return

    def to_list(self) -> List[InlineNode]:
        """
            The nodes of the chain in order.

            :returns: The nodes.
        """
        nodes: List[InlineNode] = []
        cursor = self._first
        while cursor != INLINE_CHAIN_NO_POSITION:
            nodes.append(self._nodes[cursor])
            cursor = self._next[cursor]

        return nodes
