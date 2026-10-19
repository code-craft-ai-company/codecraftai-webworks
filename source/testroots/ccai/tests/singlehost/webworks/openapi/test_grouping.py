"""
    Tests for grouping an OpenAPI document's operations by path.

    An API reference reads best when operations that sit together in the URL space sit together on the page, so
    group_operations_by_path tags every operation by the fixed words of its path.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []

import copy

from ccai import testbase

from ccai.webworks.openapi.grouping import (
    ORIGINAL_TAGS_KEY,
    ROOT_GROUP,
    group_operations_by_path,
    path_group,
)


def _document():
    """
        A small document: tagged by feature, with ids, an action suffix and a path-less root.
    """
    rtnval = {
        "openapi": "3.1.0",
        "info": {"title": "Demo", "version": "1"},
        "tags": [{"name": "rpa"}, {"name": "projects"}],
        "paths": {
            "/projects": {"get": {"tags": ["projects"], "summary": "List projects."}, "post": {"tags": ["projects"], "summary": "Create one."}},
            "/projects/{project_id}/rpa/specs": {"get": {"tags": ["rpa"], "summary": "List specs."}},
            "/projects/{project_id}/rpa/specs/{spec_id}/trigger": {"post": {"tags": ["rpa"], "summary": "Trigger."}},
            "/agent-rollouts/{rollout_id}:start": {"post": {"summary": "Start a rollout."}},
            "/": {"get": {"summary": "Root."}},
        },
    }
    return rtnval


def test_a_path_is_grouped_by_its_first_two_fixed_words():
    """
        **Feature: grouping an API reference by path**
        **Property: the group of a path is its first two fixed words joined with " / ", so every project's RPA specs sit in one group.**
    """
    testbase.assert_equal(
        (path_group("/projects/{project_id}/rpa/specs/{spec_id}/trigger"), path_group("/projects/{project_id}/rpa/specs"), path_group("/secrets/{secret_ref}")),
        ("projects / rpa", "projects / rpa", "secrets"),
    )
    return


def test_ids_and_actions_on_an_item_do_not_name_a_group():
    """
        **Feature: grouping an API reference by path**
        **Property: a path parameter and an ``{id}:action`` suffix are skipped, so an action sits in the group of the item it acts on; a word with a colon
        in it that is not a parameter (``clients:inventory``) is a fixed word like any other.**
    """
    testbase.assert_equal(
        (path_group("/agent-rollouts/{rollout_id}:start"), path_group("/clients:inventory"), path_group("/a/{x}/b/{y}/c")),
        ("agent-rollouts", "clients:inventory", "a / b"),
    )
    return


def test_a_path_with_no_fixed_words_is_the_root_group_and_a_depth_below_one_is_refused():
    """
        **Feature: grouping an API reference by path**
        **Property: "/" is grouped as "/", and asking for a depth of zero raises ValueError.**
    """
    refused = False
    try:
        path_group("/a/b", depth=0)
    except ValueError:
        refused = True
    testbase.assert_equal((path_group("/"), ROOT_GROUP, refused), ("/", "/", True))
    return


def test_the_depth_sets_how_many_fixed_words_name_a_group():
    """
        **Feature: grouping an API reference by path**
        **Property: with depth 1 the group is the first word; with depth 3 it is the first three.**
    """
    path = "/projects/{project_id}/rpa/specs/{spec_id}/trigger"
    testbase.assert_equal((path_group(path, depth=1), path_group(path, depth=3)), ("projects", "projects / rpa / specs"))
    return


def test_every_operation_is_tagged_by_its_group():
    """
        **Feature: grouping an API reference by path**
        **Property: after grouping each operation has exactly one tag, its path's group, whatever tags it had.**
    """
    grouped = group_operations_by_path(_document())
    found = {
        (path, method): operation["tags"]
        for path, item in grouped["paths"].items() for method, operation in item.items()
    }
    testbase.assert_equal(
        found,
        {
            ("/projects", "get"): ["projects"], ("/projects", "post"): ["projects"],
            ("/projects/{project_id}/rpa/specs", "get"): ["projects / rpa"],
            ("/projects/{project_id}/rpa/specs/{spec_id}/trigger", "post"): ["projects / rpa"],
            ("/agent-rollouts/{rollout_id}:start", "post"): ["agent-rollouts"], ("/", "get"): ["/"],
        },
    )
    return


def test_the_document_tag_list_is_rebuilt_with_a_count_per_group_in_order():
    """
        **Feature: grouping an API reference by path**
        **Property: the document's tags become one entry per group, sorted by name, each saying how many operations it holds (singular for one).**
    """
    grouped = group_operations_by_path(_document())
    testbase.assert_equal(
        grouped["tags"],
        [
            {"name": "/", "description": "1 operation"},
            {"name": "agent-rollouts", "description": "1 operation"},
            {"name": "projects", "description": "2 operations"},
            {"name": "projects / rpa", "description": "2 operations"},
        ],
    )
    return


def test_the_tags_an_operation_and_the_document_had_are_kept_under_an_extension_key():
    """
        **Feature: grouping an API reference by path**
        **Property: an operation that had tags keeps them under ``x-original-tags`` (one that had none gets no such key), and so does the document's tag list.**
    """
    grouped = group_operations_by_path(_document())
    trigger = grouped["paths"]["/projects/{project_id}/rpa/specs/{spec_id}/trigger"]["post"]
    start = grouped["paths"]["/agent-rollouts/{rollout_id}:start"]["post"]
    testbase.assert_equal(
        (trigger[ORIGINAL_TAGS_KEY], ORIGINAL_TAGS_KEY in start, grouped[ORIGINAL_TAGS_KEY]),
        (["rpa"], False, [{"name": "rpa"}, {"name": "projects"}]),
    )
    return


def test_grouping_does_not_change_the_document_it_is_given():
    """
        **Feature: grouping an API reference by path**
        **Property: the input document is unchanged after grouping, and grouping the result again gives the same groups.**
    """
    document = _document()
    before = copy.deepcopy(document)
    once = group_operations_by_path(document)
    twice = group_operations_by_path(once)
    testbase.assert_equal(
        (document == before, [tag["name"] for tag in twice["tags"]] == [tag["name"] for tag in once["tags"]]),
        (True, True),
    )
    return


def test_a_document_with_no_paths_gets_an_empty_tag_list():
    """
        **Feature: grouping an API reference by path**
        **Property: grouping a document without paths returns it with ``tags`` empty and raises nothing.**
    """
    grouped = group_operations_by_path({"openapi": "3.1.0", "info": {"title": "Empty", "version": "1"}})
    testbase.assert_equal((grouped["tags"], "paths" in grouped), ([], False))
    return
