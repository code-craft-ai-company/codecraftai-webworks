"""
    Tests for the API explorer's data model (``static/explorer/explorer-model.js``).

    The model is plain JavaScript with no page behind it: it turns an OpenAPI document into rows, a tree, a search and a page address, and cuts one
    operation out of the document for a pane. ``explorer_model_probe.js`` runs it under node over a small document and prints what it produced; each
    test here checks one property of that output.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []

import json
import os
import shutil
import subprocess

from typing import Any, Dict, Optional

from ccai import testbase

import ccai.webworks.openapi as openapi_package

_PROBE_PATH = os.path.join(os.path.dirname(__file__), "explorer_model_probe.js")
_MODEL_PATH = os.path.join(os.path.dirname(openapi_package.__file__), "static", "explorer", "explorer-model.js")

_cached_results: Optional[Dict[str, Any]] = None


def _probe_results() -> Dict[str, Any]:
    """
        What the probe printed, run once for the whole module.
    """
    global _cached_results

    if _cached_results is None:
        node = shutil.which("node")
        assert node is not None, "node is needed to test the API explorer's JavaScript model, and it is not on the PATH"
        completed = subprocess.run([node, _PROBE_PATH, _MODEL_PATH], capture_output=True, text=True, timeout=60)
        assert completed.returncode == 0, "the probe failed: {}".format(completed.stderr)
        _cached_results = json.loads(completed.stdout)

    return _cached_results


def test_a_path_puts_an_operation_under_its_fixed_words_and_actions_are_places_of_their_own():
    """
        **Feature: API explorer model**
        **Property: path parameters name no place; ``{id}:verb`` and ``collection:verb`` give a place ``:verb`` under the item or collection they act on;
        ``/`` and a path of parameters only sit under ``(root)``; each piece remembers the text of the path that follows it.**
    """
    split = _probe_results()["splitPath"]
    names = {label: [piece["name"] for piece in pieces] for label, pieces in split.items()}
    testbase.assert_equal(
        names,
        {
            "plain": ["projects", "rpa", "specs"],
            "itemAction": ["projects", "rpa", "specs", ":trigger"],
            "collectionAction": ["clients", ":inventory"],
            "root": ["(root)"],
            "onlyParameter": ["(root)"],
        },
    )
    testbase.assert_equal(
        (split["plain"][0]["after"], split["plain"][2]["after"], split["itemAction"][2]["after"], split["collectionAction"][0]["after"], split["onlyParameter"][0]["after"]),
        ("/{project_id}/rpa/specs", "", "/{spec_id}:trigger", ":inventory", "/{thing_id}"),
    )
    return


def test_operations_are_the_methods_of_each_path_sorted_by_path_then_method():
    """
        **Feature: API explorer model**
        **Property: a path item's operation members become rows keyed ``METHOD path``; ``parameters``, ``summary`` and ``x-`` members are not rows; rows sort by
        path then by method (GET before POST before PUT, PATCH, DELETE); the row keeps the tags and the deprecated flag.**
    """
    results = _probe_results()
    testbase.assert_equal(
        results["operationKeys"],
        [
            "GET /", "GET /clients", "GET /clients:inventory", "GET /projects", "POST /projects", "GET /projects/{project_id}",
            "DELETE /projects/{project_id}", "GET /projects/{project_id}/rpa/jobs/{job_id}", "GET /projects/{project_id}/rpa/specs",
            "POST /projects/{project_id}/rpa/specs", "POST /projects/{project_id}/rpa/specs/{spec_id}:trigger", "GET /settings/mail/templates",
            "PUT /settings/mail/templates/{template_id}",
        ],
    )
    testbase.assert_equal(
        results["operationMembers"],
        {"notOperations": 0, "deprecated": True, "notDeprecated": False, "tags": ["projects"], "operationIdWhenAbsent": ""},
    )
    return


def test_the_tree_nests_the_places_counts_every_operation_below_and_folds_a_chain_with_one_child():
    """
        **Feature: API explorer model**
        **Property: groups nest by path word, sorted by name, each counting the operations in it and below it; a group with a single child group and no
        operations of its own folds into that child (``settings / mail / templates``, depth 3, id of the deepest); a group that has operations of its own
        does not fold.**
    """
    results = _probe_results()
    testbase.assert_equal(results["topLevel"], ["(root)", "clients", "projects", "settings / mail / templates"])
    testbase.assert_equal(results["folded"], {"name": "settings / mail / templates", "id": "/settings/mail/templates", "depth": 3, "ops": 2})
    testbase.assert_equal(results["projectsRpaKids"], ["jobs", "specs"])

    projects = [group for group in results["outline"] if group["name"] == "projects"][0]
    testbase.assert_equal((projects["count"], projects["depth"], len(projects["ops"]), [child["name"] for child in projects["children"]]), (8, 1, 4, ["rpa"]))
    specs = projects["children"][0]["children"][1]
    testbase.assert_equal((specs["name"], specs["count"], [child["name"] for child in specs["children"]]), ("specs", 3, [":trigger"]))
    return


def test_a_row_shows_the_part_of_its_path_the_group_name_does_not_already_say():
    """
        **Feature: API explorer model**
        **Property: ``restOf`` is the text of the path after the group's own words: ``/{project_id}`` for an item in ``projects``, nothing for the collection
        itself or for an action in its ``:verb`` group.**
    """
    testbase.assert_equal(
        _probe_results()["restOf"],
        {
            "itemInGroup": "/{project_id}", "collectionInGroup": "", "jobInGroup": "/{job_id}", "specsInGroup": "", "actionInGroup": "",
            "collectionInClients": "", "collectionActionInGroup": "",
        },
    )
    return


def test_the_groups_that_lead_to_an_operation_are_listed_outermost_first_so_the_page_can_open_them():
    """
        **Feature: API explorer model**
        **Property: ``groupIdsFor`` lists the ids of the groups from the top level down to the one holding the operation, and nothing for an unknown key.**
    """
    testbase.assert_equal(
        _probe_results()["groupIds"],
        {
            "trigger": ["/projects", "/projects/rpa", "/projects/rpa/specs", "/projects/rpa/specs/:trigger"],
            "projectsList": ["/projects"],
            "unknown": [],
        },
    )
    return


def test_a_search_needs_every_term_and_a_method_name_filters_by_method_only():
    """
        **Feature: API explorer model**
        **Property: terms are lower case and split on spaces; every term must match somewhere in the row (path, summary, operation id, tag); a term that is
        a method name matches that method only, so ``get`` does not match ``/budget``; no terms match nothing special (the page then shows the whole tree).**
    """
    query = _probe_results()["query"]
    testbase.assert_equal(query["terms"], ["mail", "templates"])
    testbase.assert_equal(query["empty"], [])
    testbase.assert_equal(query["everyTerm"], ["PUT /settings/mail/templates/{template_id}"])
    testbase.assert_equal(query["byMethod"], ["DELETE /projects/{project_id}"])
    testbase.assert_equal(
        query["methodAndWord"],
        ["POST /projects/{project_id}/rpa/specs", "POST /projects/{project_id}/rpa/specs/{spec_id}:trigger"],
    )
    testbase.assert_equal((query["word"], query["summaryWord"]), (["GET /clients:inventory"], ["POST /projects/{project_id}/rpa/specs/{spec_id}:trigger"]))
    testbase.assert_equal((query["tagWord"], query["none"], query["methodNameIsNotASubstring"]), (8, [], []))
    return


def test_pruning_keeps_only_the_groups_that_still_hold_a_matching_operation_and_recounts():
    """
        **Feature: API explorer model**
        **Property: ``pruneTree`` returns a copy with only the accepted operations, drops groups left empty and recounts; the full tree is not changed.**
    """
    pruned = _probe_results()["pruned"]
    testbase.assert_equal((pruned["names"], pruned["count"], pruned["fullCountUnchanged"]), (["projects"], 1, 13))
    testbase.assert_equal(pruned["kept"][0]["ops"], ["DELETE /projects/{project_id}"])
    return


def test_the_page_address_keeps_the_pins_the_folds_and_the_search_in_a_form_a_person_can_read():
    """
        **Feature: API explorer model**
        **Property: the fragment lists ``pin=`` for each pinned API in order, ``fold=`` only for pinned ones, and ``q=``; it reads back to the same state
        (duplicates dropped, folds of unpinned APIs dropped) with or without the ``#``; slashes, braces and colons are not percent-encoded; no state is an
        empty fragment.**
    """
    address = _probe_results()["address"]
    testbase.assert_equal(address["readable"], True)
    testbase.assert_equal(address["text"].count("fold="), 1)
    expected = {
        "pins": ["GET /projects", "POST /projects/{project_id}/rpa/specs/{spec_id}:trigger"],
        "folds": ["GET /projects"],
        "query": "mail templates",
    }
    testbase.assert_equal((address["parsed"], address["parsedWithoutHash"]), (expected, expected))
    testbase.assert_equal((address["empty"], address["emptyText"]), ({"pins": [], "folds": [], "query": ""}, ""))
    return


def test_a_pane_document_holds_one_operation_and_only_the_components_it_reaches():
    """
        **Feature: API explorer model**
        **Property: the document cut for a pane has the same ``openapi``, ``info``, ``servers`` and ``security``, one path holding one operation (without its
        tags, with the path item's shared ``parameters``), the components reached through ``$ref`` transitively and no others, and every security scheme.**
    """
    results = _probe_results()
    read, create, job = results["paneRead"], results["paneCreate"], results["paneJob"]

    testbase.assert_equal(
        (read["openapi"], read["servers"], read["security"], create["info"]),
        ("3.1.0", [{"url": "/api/v1"}], [{"session": []}], {"title": "Demo", "version": "1"}),
    )
    testbase.assert_equal(list(read["paths"].keys()), ["/projects/{project_id}"])
    testbase.assert_equal(sorted(read["paths"]["/projects/{project_id}"].keys()), ["get", "parameters", "summary"])
    testbase.assert_equal("tags" in read["paths"]["/projects/{project_id}"]["get"], False)
    testbase.assert_equal(sorted(read["components"].keys()), ["parameters", "securitySchemes"])
    testbase.assert_equal(list(read["components"]["parameters"].keys()), ["ProjectId"])

    testbase.assert_equal(list(create["paths"]["/projects"].keys()), ["post"])
    testbase.assert_equal(sorted(create["components"]["schemas"].keys()), ["Owner", "ProjectNew"])
    testbase.assert_equal(list(job["components"].keys()), ["securitySchemes"])
    return


def test_cutting_a_pane_document_does_not_change_the_document_and_unknown_references_are_ignored():
    """
        **Feature: API explorer model**
        **Property: the input document is unchanged after panes are cut from it; ``reachableComponents`` follows a response to the schema it names, and skips a
        reference to a component that does not exist and one that points outside ``#/components``.**
    """
    results = _probe_results()
    testbase.assert_equal(results["inputUnchanged"], True)
    testbase.assert_equal(
        results["reachable"],
        {
            "responses": {"Ok": {"description": "ok", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Owner"}}}}},
            "schemas": {"Owner": {"type": "object", "properties": {"name": {"type": "string"}}}},
        },
    )
    return


def test_path_words_and_keys_named_like_inherited_object_members_are_ordinary_names():
    """
        **Feature: API explorer model**
        **Property: a document whose path words are ``constructor``, ``toString`` or ``hasOwnProperty`` builds a tree with those groups; the map of
        operations by key has no entry for a name it was never given, such as ``constructor``; and a ``$ref`` to a component called ``constructor``
        that does not exist reaches nothing.**
    """
    results = _probe_results()
    prototype_names = results["prototypeNames"]

    testbase.assert_equal(prototype_names["topLevel"], ["constructor", "hasOwnProperty / valueOf", "toString"])
    testbase.assert_equal(prototype_names["count"], 3)
    testbase.assert_equal(prototype_names["inheritedNamesAreNotKeys"], [])
    testbase.assert_equal(prototype_names["realKeyIsFound"], True)
    testbase.assert_equal(prototype_names["reachable"], {"schemas": {"Real": {"type": "object"}}})
    return

