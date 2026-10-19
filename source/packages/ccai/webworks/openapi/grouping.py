"""
.. module:: grouping
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Group an OpenAPI document's operations by where their paths put them.

.. moduleauthor:: Code Craft AI LLC

An API reference reads best when operations that sit together in the URL space sit together on the page. Hand-written tags describe
features; the path says where an operation lives. :func:`group_operations_by_path` returns a copy of a document in which every
operation is tagged by the fixed words of its path, so Swagger UI (which groups by tag) shows ``projects / rpa`` as one group
instead of one group per feature name.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []

import copy

from typing import Any, Dict, List, Mapping

#: The operation members of a path item.
HTTP_METHODS = ("get", "put", "post", "delete", "options", "head", "patch", "trace")

#: Where the tags an operation (or the document) had before grouping are kept.
ORIGINAL_TAGS_KEY: str = "x-original-tags"

#: The group of a path that has no fixed words at all.
ROOT_GROUP: str = "/"


def path_group(path: str, depth: int = 2) -> str:
    """
        The group a path belongs to: its first ``depth`` fixed words, joined with `` / ``. A path parameter (``{project_id}``) is
        skipped, and so is an action on one item (``{id}:start``), which belongs to the group of the item it acts on.

        :param path: An OpenAPI path such as ``/projects/{project_id}/rpa/specs``.
        :param depth: How many fixed words name a group (at least 1).

        :returns: The group name, such as ``projects / rpa``; ``/`` for a path with no fixed words.

        :raises: ValueError when ``depth`` is less than 1.
    """
    if depth < 1:
        raise ValueError("depth must be at least 1, not {}".format(depth))

    words: List[str] = []
    for part in path.split("/"):
        if len(part) == 0 or part.startswith("{"):
            continue
        words.append(part)

    if len(words) == 0:
        rtnval = ROOT_GROUP
        return rtnval

    rtnval = " / ".join(words[:depth])
    return rtnval


def group_operations_by_path(document: Mapping[str, Any], depth: int = 2) -> Dict[str, Any]:
    """
        A copy of an OpenAPI document with every operation tagged by :func:`path_group` and the document's tag list rebuilt to match
        (one entry per group, in order, naming how many operations it holds). The tags the input had are kept under
        ``x-original-tags``, on the operation and on the document, so nothing is lost; the input is not changed.

        :param document: An OpenAPI document (a mapping, as parsed from JSON or YAML).
        :param depth: How many fixed words of a path name its group.

        :returns: The grouped copy.
    """
    rtnval: Dict[str, Any] = copy.deepcopy(dict(document))

    counts: Dict[str, int] = {}
    for path, item in dict(rtnval.get("paths", {}) or {}).items():
        if not isinstance(item, dict):
            continue
        group = path_group(path, depth)
        for method in HTTP_METHODS:
            operation = item.get(method, None)
            if not isinstance(operation, dict):
                continue
            previous = operation.get("tags", None)
            if previous:
                operation[ORIGINAL_TAGS_KEY] = list(previous)
            operation["tags"] = [group]
            counts[group] = counts.get(group, 0) + 1

    if rtnval.get("tags", None):
        rtnval[ORIGINAL_TAGS_KEY] = rtnval["tags"]
    rtnval["tags"] = [
        {"name": name, "description": "{} operation{}".format(count, "" if count == 1 else "s")}
        for name, count in sorted(counts.items())
    ]

    return rtnval


__all__ = [
    "HTTP_METHODS",
    "ORIGINAL_TAGS_KEY",
    "ROOT_GROUP",
    "group_operations_by_path",
    "path_group",
]
