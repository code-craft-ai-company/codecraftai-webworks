"""
.. module:: test_policy_attachment
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Tests for policy attachment, validation, and inheritance chain.

.. moduleauthor:: Automation Mojo LLC

This module contains unit tests and property-based tests for the policy
attachment and inheritance functionality provided by the
:mod:`automojo.webworks.security.policyattachment` module.
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

from automojo.webworks.security.accesspolicy import AccessPolicy
from automojo.webworks.security.errors import PolicyValidationError
from automojo.webworks.security.policyattachment import (
    POLICY_CONSTRAINTS_KEY,
    PolicyInheritanceNode,
    attach_policy,
    get_attached_policy,
    validate_policy,
)


# =============================================================================
# Unit Tests for validate_policy (Task 9.1)
# =============================================================================


def test_validate_policy_accepts_valid_access_policy():
    """
        Verify that validate_policy does not raise for a valid AccessPolicy.
    """
    policy = AccessPolicy(
        roles=("admin",),
        scopes=("read",),
        require_auth=True
    )

    validate_policy(policy)

    return


def test_validate_policy_rejects_non_access_policy():
    """
        Verify that validate_policy raises PolicyValidationError when given
        an object that is not an AccessPolicy instance.
    """
    caught = False

    try:
        validate_policy("not-a-policy")
    except PolicyValidationError:
        caught = True

    if caught is not True:
        errmsg = "Expected PolicyValidationError for non-AccessPolicy object"
        raise AssertionError(errmsg)

    return


def test_validate_policy_rejects_none():
    """
        Verify that validate_policy raises PolicyValidationError when given
        None.
    """
    caught = False

    try:
        validate_policy(None)
    except PolicyValidationError:
        caught = True

    if caught is not True:
        errmsg = "Expected PolicyValidationError for None"
        raise AssertionError(errmsg)

    return


def test_validate_policy_rejects_dict():
    """
        Verify that validate_policy raises PolicyValidationError when given
        a plain dictionary that looks like a policy.
    """
    fake_policy = {
        "roles": ("admin",),
        "scopes": ("read",),
        "require_auth": True
    }

    caught = False

    try:
        validate_policy(fake_policy)
    except PolicyValidationError:
        caught = True

    if caught is not True:
        errmsg = "Expected PolicyValidationError for dict"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for attach_policy (Task 9.1)
# =============================================================================


def test_attach_policy_stores_policy_in_constraints():
    """
        Verify that attach_policy stores the policy under the access_policy
        key in the constraints dictionary.
    """
    policy = AccessPolicy(roles=("editor",), scopes=("write",))
    constraints = {}

    attach_policy(descriptor_constraints=constraints, policy=policy)

    stored = constraints.get(POLICY_CONSTRAINTS_KEY, None)

    if stored is not policy:
        errmsg = (
            f"Expected policy to be stored in constraints under "
            f"'{POLICY_CONSTRAINTS_KEY}', got {stored}"
        )
        raise AssertionError(errmsg)

    return


def test_attach_policy_validates_before_storing():
    """
        Verify that attach_policy raises PolicyValidationError for invalid
        policies and does not modify the constraints dictionary.
    """
    constraints = {}
    caught = False

    try:
        attach_policy(descriptor_constraints=constraints, policy=42)
    except PolicyValidationError:
        caught = True

    if caught is not True:
        errmsg = "Expected PolicyValidationError for invalid policy"
        raise AssertionError(errmsg)

    has_key = POLICY_CONSTRAINTS_KEY in constraints
    if has_key is True:
        errmsg = "Constraints should not be modified when validation fails"
        raise AssertionError(errmsg)

    return


def test_attach_policy_overwrites_existing_policy():
    """
        Verify that attach_policy overwrites a previously attached policy.
    """
    policy_a = AccessPolicy(roles=("viewer",))
    policy_b = AccessPolicy(roles=("admin",))
    constraints = {}

    attach_policy(descriptor_constraints=constraints, policy=policy_a)
    attach_policy(descriptor_constraints=constraints, policy=policy_b)

    stored = constraints.get(POLICY_CONSTRAINTS_KEY, None)

    if stored is not policy_b:
        errmsg = (
            f"Expected policy_b to overwrite policy_a, got {stored}"
        )
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for get_attached_policy (Task 9.1)
# =============================================================================


def test_get_attached_policy_returns_stored_policy():
    """
        Verify that get_attached_policy retrieves a previously attached policy.
    """
    policy = AccessPolicy(roles=("user",))
    constraints = {}

    attach_policy(descriptor_constraints=constraints, policy=policy)

    retrieved = get_attached_policy(descriptor_constraints=constraints)

    if retrieved is not policy:
        errmsg = f"Expected the attached policy, got {retrieved}"
        raise AssertionError(errmsg)

    return


def test_get_attached_policy_returns_none_when_empty():
    """
        Verify that get_attached_policy returns None when no policy is stored.
    """
    constraints = {}

    retrieved = get_attached_policy(descriptor_constraints=constraints)

    if retrieved is not None:
        errmsg = f"Expected None for empty constraints, got {retrieved}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for PolicyInheritanceNode (Task 9.2)
# =============================================================================


def test_inheritance_node_get_chain_single_node():
    """
        Verify that get_chain returns a single-element list for a root node.
    """
    root = PolicyInheritanceNode(
        path="/",
        policy=AccessPolicy(roles=("admin",)),
        source="explicit",
        parent=None
    )

    chain = root.get_chain()

    if len(chain) != 1:
        errmsg = f"Expected chain length 1, got {len(chain)}"
        raise AssertionError(errmsg)

    if chain[0] is not root:
        errmsg = "Expected chain[0] to be the root node"
        raise AssertionError(errmsg)

    return


def test_inheritance_node_get_chain_multiple_nodes():
    """
        Verify that get_chain returns nodes from root to leaf in order.
    """
    root = PolicyInheritanceNode(
        path="/",
        policy=AccessPolicy(roles=("user",)),
        source="explicit",
        parent=None
    )

    child = PolicyInheritanceNode(
        path="/api",
        policy=AccessPolicy(roles=("api_user",)),
        source="explicit",
        parent=root
    )

    grandchild = PolicyInheritanceNode(
        path="/api/admin",
        policy=AccessPolicy(roles=("admin",)),
        source="explicit",
        parent=child
    )

    chain = grandchild.get_chain()

    if len(chain) != 3:
        errmsg = f"Expected chain length 3, got {len(chain)}"
        raise AssertionError(errmsg)

    if chain[0] is not root:
        errmsg = "Expected chain[0] to be root"
        raise AssertionError(errmsg)

    if chain[1] is not child:
        errmsg = "Expected chain[1] to be child"
        raise AssertionError(errmsg)

    if chain[2] is not grandchild:
        errmsg = "Expected chain[2] to be grandchild"
        raise AssertionError(errmsg)

    return


def test_inheritance_node_get_effective_policy_single_explicit():
    """
        Verify that get_effective_policy returns the node's own policy
        when it is the only node in the chain.
    """
    root = PolicyInheritanceNode(
        path="/",
        policy=AccessPolicy(roles=("admin",), scopes=("read",)),
        source="explicit",
        parent=None
    )

    effective = root.get_effective_policy()

    if effective.roles != ("admin",):
        errmsg = f"Expected roles ('admin',), got {effective.roles}"
        raise AssertionError(errmsg)

    if effective.scopes != ("read",):
        errmsg = f"Expected scopes ('read',), got {effective.scopes}"
        raise AssertionError(errmsg)

    return


def test_inheritance_node_get_effective_policy_merges_parent_child():
    """
        Verify that get_effective_policy merges parent and child policies
        using union for roles and scopes.
    """
    parent = PolicyInheritanceNode(
        path="/",
        policy=AccessPolicy(roles=("user",), scopes=("read",)),
        source="explicit",
        parent=None
    )

    child = PolicyInheritanceNode(
        path="/admin",
        policy=AccessPolicy(roles=("admin",), scopes=("write",)),
        source="explicit",
        parent=parent
    )

    effective = child.get_effective_policy()

    expected_roles = ("user", "admin")
    if effective.roles != expected_roles:
        errmsg = (
            f"Expected roles {expected_roles}, got {effective.roles}"
        )
        raise AssertionError(errmsg)

    expected_scopes = ("read", "write")
    if effective.scopes != expected_scopes:
        errmsg = (
            f"Expected scopes {expected_scopes}, got {effective.scopes}"
        )
        raise AssertionError(errmsg)

    return


def test_inheritance_node_get_effective_policy_inherits_when_child_has_none():
    """
        Verify that get_effective_policy returns the parent policy when the
        child has no explicit policy (policy is None).
    """
    parent = PolicyInheritanceNode(
        path="/",
        policy=AccessPolicy(roles=("user",), scopes=("read",)),
        source="explicit",
        parent=None
    )

    child = PolicyInheritanceNode(
        path="/page",
        policy=None,
        source="inherited",
        parent=parent
    )

    effective = child.get_effective_policy()

    if effective.roles != ("user",):
        errmsg = f"Expected inherited roles ('user',), got {effective.roles}"
        raise AssertionError(errmsg)

    if effective.scopes != ("read",):
        errmsg = (
            f"Expected inherited scopes ('read',), got {effective.scopes}"
        )
        raise AssertionError(errmsg)

    return


def test_inheritance_node_get_effective_policy_default_when_no_policies():
    """
        Verify that get_effective_policy returns a default policy with
        require_auth=True when no node in the chain has a policy.
    """
    root = PolicyInheritanceNode(
        path="/",
        policy=None,
        source="default",
        parent=None
    )

    child = PolicyInheritanceNode(
        path="/open",
        policy=None,
        source="default",
        parent=root
    )

    effective = child.get_effective_policy()

    if effective.require_auth is not True:
        errmsg = (
            f"Expected default require_auth=True, "
            f"got {effective.require_auth}"
        )
        raise AssertionError(errmsg)

    if len(effective.roles) != 0:
        errmsg = f"Expected empty roles for default, got {effective.roles}"
        raise AssertionError(errmsg)

    if len(effective.scopes) != 0:
        errmsg = f"Expected empty scopes for default, got {effective.scopes}"
        raise AssertionError(errmsg)

    return


def test_inheritance_node_get_effective_policy_three_level_merge():
    """
        Verify that get_effective_policy correctly merges across three
        levels of the hierarchy.
    """
    root = PolicyInheritanceNode(
        path="/",
        policy=AccessPolicy(roles=("base",), scopes=("read",)),
        source="explicit",
        parent=None
    )

    mid = PolicyInheritanceNode(
        path="/api",
        policy=AccessPolicy(roles=("api",), scopes=("list",)),
        source="explicit",
        parent=root
    )

    leaf = PolicyInheritanceNode(
        path="/api/admin",
        policy=AccessPolicy(roles=("admin",), scopes=("write",)),
        source="explicit",
        parent=mid
    )

    effective = leaf.get_effective_policy()

    expected_roles = ("base", "api", "admin")
    if effective.roles != expected_roles:
        errmsg = (
            f"Expected roles {expected_roles}, got {effective.roles}"
        )
        raise AssertionError(errmsg)

    expected_scopes = ("read", "list", "write")
    if effective.scopes != expected_scopes:
        errmsg = (
            f"Expected scopes {expected_scopes}, got {effective.scopes}"
        )
        raise AssertionError(errmsg)

    return


# =============================================================================
# Property-Based Tests for Policy Attachment Storage (Task 9.3)
# =============================================================================

import random
import string


def _random_string_tuple(max_length=5):
    """
        Generate a tuple of random unique strings for use as roles or scopes.

        :returns: A tuple of 0 to max_length random lowercase strings.
    """
    count = random.randint(0, max_length)
    items = []

    for _ in range(count):
        length = random.randint(1, 8)
        item = "".join(random.choices(string.ascii_lowercase, k=length))
        items.append(item)

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for item in items:
        if item not in seen:
            seen.add(item)
            unique.append(item)

    rtnval = tuple(unique)

    return rtnval


def _random_access_policy():
    """
        Generate a random valid AccessPolicy with random roles, scopes,
        require_auth, and constraints.

        :returns: A randomly configured AccessPolicy instance.
    """
    policy_roles = _random_string_tuple()
    policy_scopes = _random_string_tuple()
    require_auth = random.choice([True, False])

    constraints = {}
    constraint_count = random.randint(0, 3)
    for _ in range(constraint_count):
        key = "".join(random.choices(string.ascii_lowercase, k=4))
        value = random.randint(0, 100)
        constraints[key] = value

    rtnval = AccessPolicy(
        roles=policy_roles,
        scopes=policy_scopes,
        require_auth=require_auth,
        constraints=constraints
    )

    return rtnval


def _random_invalid_policy():
    """
        Generate a random object that is not a valid AccessPolicy.

        :returns: A randomly chosen invalid policy object.
    """
    choices = [
        None,
        42,
        "not-a-policy",
        {"roles": ("admin",)},
        ["admin"],
        True,
        3.14,
    ]

    rtnval = random.choice(choices)

    return rtnval


def test_property_policy_attachment_storage():
    """
        Property test for Policy Attachment Storage.

        **Validates: Requirements 2.2, 2.4, 2.5**

        For any endpoint with an attached AccessPolicy:
        - The policy SHALL be stored in the EndpointDescriptor's constraints
          field under the access_policy key.
        - The stored policy SHALL be a valid AccessPolicy instance.
        - Invalid policy attachments SHALL raise PolicyValidationError.
    """
    iteration_count = 100

    for iteration in range(iteration_count):
        # --- Valid policy attachment ---
        policy = _random_access_policy()
        constraints = {}

        attach_policy(descriptor_constraints=constraints, policy=policy)

        # Verify the policy is stored under the correct key
        stored = constraints.get(POLICY_CONSTRAINTS_KEY, None)

        if stored is None:
            errmsg = (
                f"Iteration {iteration}: Policy was not stored in "
                f"constraints under '{POLICY_CONSTRAINTS_KEY}'"
            )
            raise AssertionError(errmsg)

        # Verify the stored policy is the same AccessPolicy instance
        if stored is not policy:
            errmsg = (
                f"Iteration {iteration}: Stored policy is not the same "
                f"instance. Expected id={id(policy)}, got id={id(stored)}"
            )
            raise AssertionError(errmsg)

        # Verify the stored policy is a valid AccessPolicy instance
        is_access_policy = isinstance(stored, AccessPolicy)
        if is_access_policy is not True:
            errmsg = (
                f"Iteration {iteration}: Stored object is not an "
                f"AccessPolicy instance, got {type(stored).__name__}"
            )
            raise AssertionError(errmsg)

        # Verify retrieval via get_attached_policy
        retrieved = get_attached_policy(descriptor_constraints=constraints)
        if retrieved is not policy:
            errmsg = (
                f"Iteration {iteration}: get_attached_policy returned "
                f"a different object than what was attached"
            )
            raise AssertionError(errmsg)

        # --- Invalid policy attachment ---
        invalid_policy = _random_invalid_policy()
        invalid_constraints = {}
        caught = False

        try:
            attach_policy(
                descriptor_constraints=invalid_constraints,
                policy=invalid_policy
            )
        except PolicyValidationError:
            caught = True

        if caught is not True:
            errmsg = (
                f"Iteration {iteration}: Expected PolicyValidationError "
                f"for invalid policy {type(invalid_policy).__name__}, "
                f"but no exception was raised"
            )
            raise AssertionError(errmsg)

        # Verify invalid policy was not stored
        has_key = POLICY_CONSTRAINTS_KEY in invalid_constraints
        if has_key is True:
            errmsg = (
                f"Iteration {iteration}: Invalid policy should not be "
                f"stored in constraints"
            )
            raise AssertionError(errmsg)

    return
