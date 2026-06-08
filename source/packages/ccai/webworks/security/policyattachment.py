"""
.. module:: policyattachment
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Policy attachment and inheritance for URL node hierarchies.

.. moduleauthor:: Code Craft AI LLC

This module provides functions for attaching AccessPolicy objects to endpoint
descriptors and a PolicyInheritanceNode class for modelling and traversing
policy inheritance chains in a URL routing hierarchy.

The :func:`validate_policy` function checks whether a given object is a valid
AccessPolicy instance. The :func:`attach_policy` function validates and stores
a policy inside a descriptor constraints dictionary. The
:class:`PolicyInheritanceNode` dataclass represents a single node in the
inheritance chain and supports computing the effective merged policy from
root to leaf.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ccai.webworks.security.accesspolicy import AccessPolicy
from ccai.webworks.security.errors import PolicyValidationError


POLICY_CONSTRAINTS_KEY = "access_policy"


def validate_policy(policy: Any) -> None:
    """
        Validate that the given object is a valid AccessPolicy instance.

        Checks that the policy is an instance of AccessPolicy and that its
        core attributes (roles, scopes, require_auth) are present and of
        the correct types.

        :param policy: The object to validate as an AccessPolicy.

        :raises PolicyValidationError: If the policy is not a valid
            AccessPolicy instance or has invalid attribute types.
    """
    if not isinstance(policy, AccessPolicy):
        errmsg = (
            f"Expected an AccessPolicy instance, "
            f"got {type(policy).__name__}"
        )
        raise PolicyValidationError(message=errmsg, policy=policy)


    if not isinstance(policy.roles, tuple):
        errmsg = (
            f"AccessPolicy.roles must be a tuple, "
            f"got {type(policy.roles).__name__}"
        )
        raise PolicyValidationError(message=errmsg, policy=policy)

    if not isinstance(policy.scopes, tuple):
        errmsg = (
            f"AccessPolicy.scopes must be a tuple, "
            f"got {type(policy.scopes).__name__}"
        )
        raise PolicyValidationError(message=errmsg, policy=policy)

    if not isinstance(policy.require_auth, bool):
        errmsg = (
            f"AccessPolicy.require_auth must be a bool, "
            f"got {type(policy.require_auth).__name__}"
        )
        raise PolicyValidationError(message=errmsg, policy=policy)

    return


def attach_policy(descriptor_constraints: Dict[str, Any],
                  policy: AccessPolicy) -> None:
    """
        Validate and store an AccessPolicy in a descriptor constraints
        dictionary.

        The policy is validated using :func:`validate_policy` before being
        stored under the ``access_policy`` key in the constraints dictionary.

        :param descriptor_constraints: The constraints dictionary of an
            EndpointDescriptor where the policy will be stored.
        :param policy: The AccessPolicy to attach.

        :raises PolicyValidationError: If the policy is not a valid
            AccessPolicy instance.
    """
    validate_policy(policy)

    descriptor_constraints[POLICY_CONSTRAINTS_KEY] = policy

    return


def get_attached_policy(
        descriptor_constraints: Dict[str, Any]) -> Optional[AccessPolicy]:
    """
        Retrieve the AccessPolicy stored in a descriptor constraints
        dictionary.

        :param descriptor_constraints: The constraints dictionary of an
            EndpointDescriptor to inspect.

        :returns: The attached AccessPolicy, or None if no policy is stored.
    """
    rtnval = descriptor_constraints.get(POLICY_CONSTRAINTS_KEY, None)

    return rtnval


@dataclass
class PolicyInheritanceNode:
    """
        Node in the policy inheritance chain for debugging and audit.

        Each node represents a point in the URL hierarchy that may have
        an explicit policy, an inherited policy, or a default policy.
        The :meth:`get_chain` method returns the full chain from root to
        this node, and :meth:`get_effective_policy` computes the merged
        policy by walking the chain from root to leaf.

        :param path: The URL path segment this node represents.
        :param policy: The AccessPolicy at this node, or None if no
            explicit policy is defined.
        :param source: How the policy was determined. One of ``"explicit"``,
            ``"inherited"``, or ``"default"``.
        :param parent: The parent node in the inheritance chain, or None
            for the root node.
    """

    path: str = ""
    policy: Optional[AccessPolicy] = None
    source: str = "default"
    parent: Optional["PolicyInheritanceNode"] = None

    def get_chain(self) -> List["PolicyInheritanceNode"]:
        """
            Get the full inheritance chain from root to this node.

            Walks up the parent references to build the chain, then
            reverses it so the root node is first and this node is last.

            :returns: A list of PolicyInheritanceNode from root to self.
        """
        chain = []
        current = self

        while current is not None:
            chain.append(current)
            current = current.parent

        chain.reverse()

        return chain

    def get_effective_policy(self) -> AccessPolicy:
        """
            Compute the effective merged policy for this node.

            Walks the inheritance chain from root to this node, merging
            each explicit policy encountered along the way. If no policies
            are found in the chain, returns a default AccessPolicy with
            ``require_auth=True``.

            The merge follows the "parent defaults, child overrides"
            strategy where child policies are merged on top of the
            accumulated parent policy using the default union merge.

            :returns: The effective AccessPolicy for this node.
        """
        chain = self.get_chain()

        effective = None

        for node in chain:
            node_policy = node.policy
            if node_policy is not None:
                if effective is None:
                    effective = node_policy
                else:
                    effective = effective.merge_with(node_policy)

        if effective is None:
            effective = AccessPolicy(require_auth=True)

        return effective
