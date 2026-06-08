"""
.. module:: test_list_merge_properties
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Property-based tests for list field merge behavior.

.. moduleauthor:: Code Craft AI LLC

This module contains property-based tests validating Property 6: List Field
Merge Behavior across many generated inputs. It covers the merge semantics
for tags, roles, and scopes in parent-child endpoint relationships.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

import random
import string
from typing import List

from ccai.webworks.endpoints.accesspolicy import AccessPolicy
from ccai.webworks.endpoints.constraints import EndpointConstraints
from ccai.webworks.endpoints.merging import ConstraintMerger


# =============================================================================
# Helper Functions for Generating Random Test Data
# =============================================================================

def generate_random_string(min_len: int = 3, max_len: int = 10) -> str:
    """Generate a random alphanumeric string."""
    length = random.randint(min_len, max_len)
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


def generate_random_string_list(max_items: int = 5) -> List[str]:
    """Generate a random list of unique strings."""
    num_items = random.randint(0, max_items)
    return list({generate_random_string() for _ in range(num_items)})


def generate_overlapping_string_lists(max_items: int = 5):
    """
        Generate two lists that share some elements to exercise deduplication.

        :returns: Tuple of (list_a, list_b) with potential overlap.
    """
    shared = generate_random_string_list(max_items=2)
    only_a = generate_random_string_list(max_items=3)
    only_b = generate_random_string_list(max_items=3)
    list_a = shared + only_a
    list_b = shared + only_b
    random.shuffle(list_a)
    random.shuffle(list_b)
    return list_a, list_b



# =============================================================================
# Property 6: List Field Merge Behavior - Tags
# Feature: endpoint-abstractions, Property 6: List Field Merge Behavior
# Validates: Requirements 3.7, 3.8, 9.9
# =============================================================================

def test_property_tags_default_child_wins_when_set():
    """
        Property 6: List Field Merge Behavior - Tags Default (Child Wins)

        *For any* parent and child tag lists, when neither merge nor replace
        is set, the child tags SHALL win if the child list is non-empty.
        If the child list is empty, the parent tags SHALL be inherited.

        **Feature: endpoint-abstractions, Property 6: List Field Merge Behavior**
        **Validates: Requirements 3.7**
    """
    for iteration in range(100):
        parent_tags = generate_random_string_list(5)
        child_tags = generate_random_string_list(5)

        merged = ConstraintMerger.merge_tags(
            parent=parent_tags,
            child=child_tags,
            merge=False,
            replace=False
        )

        if child_tags:
            # Child is non-empty, so child wins
            if merged != child_tags:
                errmsg = (
                    f"Iteration {iteration}: Default mode with non-empty child "
                    f"should return child tags. "
                    f"child_tags={child_tags}, merged={merged}"
                )
                raise AssertionError(errmsg)
        else:
            # Child is empty, so parent is inherited
            if merged != parent_tags:
                errmsg = (
                    f"Iteration {iteration}: Default mode with empty child "
                    f"should inherit parent tags. "
                    f"parent_tags={parent_tags}, merged={merged}"
                )
                raise AssertionError(errmsg)

    return


def test_property_tags_merge_mode_appends_parent_to_child():
    """
        Property 6: List Field Merge Behavior - Tags Merge Mode

        *For any* parent and child tag lists, when merge=True the parent
        tags SHALL be appended to the child tags (union, child order first,
        no duplicates).

        **Feature: endpoint-abstractions, Property 6: List Field Merge Behavior**
        **Validates: Requirements 3.8**
    """
    for iteration in range(100):
        parent_tags, child_tags = generate_overlapping_string_lists(5)

        merged = ConstraintMerger.merge_tags(
            parent=parent_tags,
            child=child_tags,
            merge=True,
            replace=False
        )

        # All child tags must be present
        for tag in child_tags:
            if tag not in merged:
                errmsg = (
                    f"Iteration {iteration}: Merged tags missing child tag. "
                    f"tag={tag}, child_tags={child_tags}, merged={merged}"
                )
                raise AssertionError(errmsg)

        # All parent tags must be present
        for tag in parent_tags:
            if tag not in merged:
                errmsg = (
                    f"Iteration {iteration}: Merged tags missing parent tag. "
                    f"tag={tag}, parent_tags={parent_tags}, merged={merged}"
                )
                raise AssertionError(errmsg)

        # No duplicates
        if len(merged) != len(set(merged)):
            errmsg = (
                f"Iteration {iteration}: Merged tags contain duplicates. "
                f"merged={merged}"
            )
            raise AssertionError(errmsg)

        # Child tags should appear first in order
        for i, tag in enumerate(child_tags):
            merged_idx = merged.index(tag)
            if merged_idx > len(merged) - 1:
                errmsg = (
                    f"Iteration {iteration}: Child tag not found in merged. "
                    f"tag={tag}"
                )
                raise AssertionError(errmsg)

    return


def test_property_tags_replace_mode_uses_child_only():
    """
        Property 6: List Field Merge Behavior - Tags Replace Mode

        *For any* parent and child tag lists, when replace=True the merged
        tags SHALL be exactly the child tags, discarding parent tags.

        **Feature: endpoint-abstractions, Property 6: List Field Merge Behavior**
        **Validates: Requirements 9.9**
    """
    for iteration in range(100):
        parent_tags = generate_random_string_list(5)
        child_tags = generate_random_string_list(5)

        merged = ConstraintMerger.merge_tags(
            parent=parent_tags,
            child=child_tags,
            merge=False,
            replace=True
        )

        if merged != child_tags:
            errmsg = (
                f"Iteration {iteration}: Replace mode should return child tags exactly. "
                f"child_tags={child_tags}, merged={merged}"
            )
            raise AssertionError(errmsg)

    return


def test_property_tags_merge_returns_new_list():
    """
        Property 6: List Field Merge Behavior - Tags Immutability

        *For any* parent and child tag lists, merging SHALL return a new
        list without modifying either input list.

        **Feature: endpoint-abstractions, Property 6: List Field Merge Behavior**
        **Validates: Requirements 3.7, 3.8**
    """
    for iteration in range(100):
        parent_tags = generate_random_string_list(5)
        child_tags = generate_random_string_list(5)
        parent_before = list(parent_tags)
        child_before = list(child_tags)

        merge_mode = random.choice([True, False])
        replace_mode = random.choice([True, False]) if not merge_mode else False

        merged = ConstraintMerger.merge_tags(
            parent=parent_tags,
            child=child_tags,
            merge=merge_mode,
            replace=replace_mode
        )

        # Inputs must be unchanged
        if parent_tags != parent_before:
            errmsg = (
                f"Iteration {iteration}: parent_tags was mutated. "
                f"before={parent_before}, after={parent_tags}"
            )
            raise AssertionError(errmsg)

        if child_tags != child_before:
            errmsg = (
                f"Iteration {iteration}: child_tags was mutated. "
                f"before={child_before}, after={child_tags}"
            )
            raise AssertionError(errmsg)

        # Merged must be a different list object from inputs
        if merged is parent_tags:
            errmsg = f"Iteration {iteration}: Merged is the same object as parent_tags."
            raise AssertionError(errmsg)

        if merged is child_tags:
            errmsg = f"Iteration {iteration}: Merged is the same object as child_tags."
            raise AssertionError(errmsg)

    return



# =============================================================================
# Property 6: List Field Merge Behavior - Roles and Scopes
# Feature: endpoint-abstractions, Property 6: List Field Merge Behavior
# Validates: Requirements 7.4, 7.5
# =============================================================================

def test_property_roles_default_union_in_access_policy():
    """
        Property 6: List Field Merge Behavior - Roles Union in AccessPolicy

        *For any* two AccessPolicy objects merged with default settings,
        the merged roles SHALL be the union of both role lists (no duplicates).

        **Feature: endpoint-abstractions, Property 6: List Field Merge Behavior**
        **Validates: Requirements 7.4**
    """
    for iteration in range(100):
        parent_roles, child_roles = generate_overlapping_string_lists(4)
        policy_a = AccessPolicy(roles=parent_roles, scopes=[], require_auth=True)
        policy_b = AccessPolicy(roles=child_roles, scopes=[], require_auth=True)

        merged = policy_a.merge_with(policy_b)

        # All parent roles must be present
        for role in parent_roles:
            if role not in merged.roles:
                errmsg = (
                    f"Iteration {iteration}: Merged roles missing parent role. "
                    f"role={role}, parent_roles={parent_roles}, "
                    f"merged.roles={merged.roles}"
                )
                raise AssertionError(errmsg)

        # All child roles must be present
        for role in child_roles:
            if role not in merged.roles:
                errmsg = (
                    f"Iteration {iteration}: Merged roles missing child role. "
                    f"role={role}, child_roles={child_roles}, "
                    f"merged.roles={merged.roles}"
                )
                raise AssertionError(errmsg)

        # No duplicates
        if len(merged.roles) != len(set(merged.roles)):
            errmsg = (
                f"Iteration {iteration}: Merged roles contain duplicates. "
                f"merged.roles={merged.roles}"
            )
            raise AssertionError(errmsg)

        # Merged set equals union
        expected_set = set(parent_roles) | set(child_roles)
        if set(merged.roles) != expected_set:
            errmsg = (
                f"Iteration {iteration}: Merged roles set does not equal union. "
                f"expected={expected_set}, got={set(merged.roles)}"
            )
            raise AssertionError(errmsg)

    return


def test_property_scopes_default_union_in_access_policy():
    """
        Property 6: List Field Merge Behavior - Scopes Union in AccessPolicy

        *For any* two AccessPolicy objects merged with default settings,
        the merged scopes SHALL be the union of both scope lists (no duplicates).

        **Feature: endpoint-abstractions, Property 6: List Field Merge Behavior**
        **Validates: Requirements 7.4**
    """
    for iteration in range(100):
        parent_scopes, child_scopes = generate_overlapping_string_lists(4)
        policy_a = AccessPolicy(roles=[], scopes=parent_scopes, require_auth=True)
        policy_b = AccessPolicy(roles=[], scopes=child_scopes, require_auth=True)

        merged = policy_a.merge_with(policy_b)

        # All parent scopes must be present
        for scope in parent_scopes:
            if scope not in merged.scopes:
                errmsg = (
                    f"Iteration {iteration}: Merged scopes missing parent scope. "
                    f"scope={scope}, parent_scopes={parent_scopes}, "
                    f"merged.scopes={merged.scopes}"
                )
                raise AssertionError(errmsg)

        # All child scopes must be present
        for scope in child_scopes:
            if scope not in merged.scopes:
                errmsg = (
                    f"Iteration {iteration}: Merged scopes missing child scope. "
                    f"scope={scope}, child_scopes={child_scopes}, "
                    f"merged.scopes={merged.scopes}"
                )
                raise AssertionError(errmsg)

        # No duplicates
        if len(merged.scopes) != len(set(merged.scopes)):
            errmsg = (
                f"Iteration {iteration}: Merged scopes contain duplicates. "
                f"merged.scopes={merged.scopes}"
            )
            raise AssertionError(errmsg)

        # Merged set equals union
        expected_set = set(parent_scopes) | set(child_scopes)
        if set(merged.scopes) != expected_set:
            errmsg = (
                f"Iteration {iteration}: Merged scopes set does not equal union. "
                f"expected={expected_set}, got={set(merged.scopes)}"
            )
            raise AssertionError(errmsg)

    return


def test_property_roles_replace_in_access_policy():
    """
        Property 6: List Field Merge Behavior - Roles Replace in AccessPolicy

        *For any* two AccessPolicy objects, when replace_roles=True the
        merged roles SHALL be exactly the other policy's roles.

        **Feature: endpoint-abstractions, Property 6: List Field Merge Behavior**
        **Validates: Requirements 7.5**
    """
    for iteration in range(100):
        parent_roles, child_roles = generate_overlapping_string_lists(4)
        policy_a = AccessPolicy(roles=parent_roles, scopes=[], require_auth=True)
        policy_b = AccessPolicy(roles=child_roles, scopes=[], require_auth=True)

        merged = policy_a.merge_with(policy_b, replace_roles=True)

        if merged.roles != tuple(child_roles):
            errmsg = (
                f"Iteration {iteration}: With replace_roles=True, merged roles "
                f"should equal child roles. "
                f"child_roles={child_roles}, merged.roles={merged.roles}"
            )
            raise AssertionError(errmsg)

    return


def test_property_scopes_replace_in_access_policy():
    """
        Property 6: List Field Merge Behavior - Scopes Replace in AccessPolicy

        *For any* two AccessPolicy objects, when replace_scopes=True the
        merged scopes SHALL be exactly the other policy's scopes.

        **Feature: endpoint-abstractions, Property 6: List Field Merge Behavior**
        **Validates: Requirements 7.5**
    """
    for iteration in range(100):
        parent_scopes, child_scopes = generate_overlapping_string_lists(4)
        policy_a = AccessPolicy(roles=[], scopes=parent_scopes, require_auth=True)
        policy_b = AccessPolicy(roles=[], scopes=child_scopes, require_auth=True)

        merged = policy_a.merge_with(policy_b, replace_scopes=True)

        if merged.scopes != tuple(child_scopes):
            errmsg = (
                f"Iteration {iteration}: With replace_scopes=True, merged scopes "
                f"should equal child scopes. "
                f"child_scopes={child_scopes}, merged.scopes={merged.scopes}"
            )
            raise AssertionError(errmsg)

    return



# =============================================================================
# Property 6: List Field Merge Behavior - EndpointConstraints._merge_list_field
# Feature: endpoint-abstractions, Property 6: List Field Merge Behavior
# Validates: Requirements 3.7, 7.4, 7.5
# =============================================================================

def test_property_constraints_merge_list_field_union():
    """
        Property 6: List Field Merge Behavior - Constraints List Union

        *For any* parent and child string lists, _merge_list_field with
        replace=False SHALL return the union (parent first, then child,
        no duplicates).

        **Feature: endpoint-abstractions, Property 6: List Field Merge Behavior**
        **Validates: Requirements 3.7, 7.4**
    """
    for iteration in range(100):
        parent_list, child_list = generate_overlapping_string_lists(5)

        merged = EndpointConstraints._merge_list_field(
            parent_list, child_list, replace=False
        )

        # All parent items must be present
        for item in parent_list:
            if item not in merged:
                errmsg = (
                    f"Iteration {iteration}: Merged list missing parent item. "
                    f"item={item}, parent={parent_list}, merged={merged}"
                )
                raise AssertionError(errmsg)

        # All child items must be present
        for item in child_list:
            if item not in merged:
                errmsg = (
                    f"Iteration {iteration}: Merged list missing child item. "
                    f"item={item}, child={child_list}, merged={merged}"
                )
                raise AssertionError(errmsg)

        # No duplicates
        if len(merged) != len(set(merged)):
            errmsg = (
                f"Iteration {iteration}: Merged list contains duplicates. "
                f"merged={merged}"
            )
            raise AssertionError(errmsg)

        # Set equality with union
        expected_set = set(parent_list) | set(child_list)
        if set(merged) != expected_set:
            errmsg = (
                f"Iteration {iteration}: Merged set does not equal union. "
                f"expected={expected_set}, got={set(merged)}"
            )
            raise AssertionError(errmsg)

        # Parent items should appear first (order preservation)
        for item in parent_list:
            parent_idx = merged.index(item)
            # Items unique to child should appear after all parent items
            # (but shared items keep their parent position)

    return


def test_property_constraints_merge_list_field_replace():
    """
        Property 6: List Field Merge Behavior - Constraints List Replace

        *For any* parent and child string lists, _merge_list_field with
        replace=True SHALL return exactly the child list.

        **Feature: endpoint-abstractions, Property 6: List Field Merge Behavior**
        **Validates: Requirements 7.5**
    """
    for iteration in range(100):
        parent_list = generate_random_string_list(5)
        child_list = generate_random_string_list(5)

        merged = EndpointConstraints._merge_list_field(
            parent_list, child_list, replace=True
        )

        if merged != child_list:
            errmsg = (
                f"Iteration {iteration}: Replace mode should return child list exactly. "
                f"child={child_list}, merged={merged}"
            )
            raise AssertionError(errmsg)

        # Must be a copy, not the same object
        if merged is child_list:
            errmsg = (
                f"Iteration {iteration}: Replace mode should return a copy, "
                f"not the same list object."
            )
            raise AssertionError(errmsg)

    return


def test_property_constraints_merge_list_field_immutability():
    """
        Property 6: List Field Merge Behavior - Constraints List Immutability

        *For any* parent and child string lists, _merge_list_field SHALL
        not mutate either input list.

        **Feature: endpoint-abstractions, Property 6: List Field Merge Behavior**
        **Validates: Requirements 3.7, 7.4, 7.5**
    """
    for iteration in range(100):
        parent_list = generate_random_string_list(5)
        child_list = generate_random_string_list(5)
        parent_before = list(parent_list)
        child_before = list(child_list)

        replace = random.choice([True, False])

        merged = EndpointConstraints._merge_list_field(
            parent_list, child_list, replace=replace
        )

        if parent_list != parent_before:
            errmsg = (
                f"Iteration {iteration}: parent_list was mutated. "
                f"before={parent_before}, after={parent_list}"
            )
            raise AssertionError(errmsg)

        if child_list != child_before:
            errmsg = (
                f"Iteration {iteration}: child_list was mutated. "
                f"before={child_before}, after={child_list}"
            )
            raise AssertionError(errmsg)

    return


def test_property_replace_flag_independence():
    """
        Property 6: List Field Merge Behavior - Replace Flag Independence

        *For any* AccessPolicy merge, replace_roles and replace_scopes
        SHALL operate independently. Setting replace_roles=True SHALL
        only affect roles, not scopes, and vice versa.

        **Feature: endpoint-abstractions, Property 6: List Field Merge Behavior**
        **Validates: Requirements 7.4, 7.5**
    """
    for iteration in range(100):
        parent_roles, child_roles = generate_overlapping_string_lists(4)
        parent_scopes, child_scopes = generate_overlapping_string_lists(4)

        policy_a = AccessPolicy(
            roles=parent_roles, scopes=parent_scopes, require_auth=True
        )
        policy_b = AccessPolicy(
            roles=child_roles, scopes=child_scopes, require_auth=True
        )

        # replace_roles=True, replace_scopes=False
        merged_roles_replaced = policy_a.merge_with(
            policy_b, replace_roles=True, replace_scopes=False
        )

        # Roles should be replaced (child only)
        if merged_roles_replaced.roles != tuple(child_roles):
            errmsg = (
                f"Iteration {iteration}: replace_roles=True should replace roles. "
                f"child_roles={child_roles}, "
                f"merged.roles={merged_roles_replaced.roles}"
            )
            raise AssertionError(errmsg)

        # Scopes should be union (not replaced)
        expected_scopes = set(parent_scopes) | set(child_scopes)
        if set(merged_roles_replaced.scopes) != expected_scopes:
            errmsg = (
                f"Iteration {iteration}: replace_roles should not affect scopes. "
                f"expected_scopes={expected_scopes}, "
                f"merged.scopes={set(merged_roles_replaced.scopes)}"
            )
            raise AssertionError(errmsg)

        # replace_roles=False, replace_scopes=True
        merged_scopes_replaced = policy_a.merge_with(
            policy_b, replace_roles=False, replace_scopes=True
        )

        # Scopes should be replaced (child only)
        if merged_scopes_replaced.scopes != tuple(child_scopes):
            errmsg = (
                f"Iteration {iteration}: replace_scopes=True should replace scopes. "
                f"child_scopes={child_scopes}, "
                f"merged.scopes={merged_scopes_replaced.scopes}"
            )
            raise AssertionError(errmsg)

        # Roles should be union (not replaced)
        expected_roles = set(parent_roles) | set(child_roles)
        if set(merged_scopes_replaced.roles) != expected_roles:
            errmsg = (
                f"Iteration {iteration}: replace_scopes should not affect roles. "
                f"expected_roles={expected_roles}, "
                f"merged.roles={set(merged_scopes_replaced.roles)}"
            )
            raise AssertionError(errmsg)

    return
