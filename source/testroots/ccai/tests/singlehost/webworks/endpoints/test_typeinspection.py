"""
    Tests for the shared type inspection helpers.

    The helpers answer, in one place, the questions that schema inspection,
    the OpenAPI schema converter and the REST validator all ask about a
    schema class: the real types of its fields, whether a field is optional,
    and the JSON Schema that describes a type.
"""

from __future__ import annotations

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []

import enum

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union

from ccai import testbase

from ccai.webworks.endpoints.typeinspection import (
    dataclass_to_json_schema,
    is_optional_type,
    is_union_type,
    non_none_members,
    resolve_field_types,
    type_to_json_schema,
    unwrap_optional,
)


class Colour(enum.Enum):
    RED = "red"
    BLUE = "blue"


@dataclass
class Address:
    city: str
    zip_code: Optional[str] = None


@dataclass
class Person:
    # Every annotation in this module is postponed (a string at runtime),
    # because of the ``from __future__ import annotations`` above.
    name: str
    age: int
    nick: str | None = None
    address: Address | None = None
    tags: List[str] = field(default_factory=list)
    scores: Dict[str, int] = field(default_factory=dict)
    colour: Colour = Colour.RED


@dataclass
class Node:
    label: str
    parent: Optional[Node] = None


def test_is_optional_type_recognises_the_pep_604_spelling():
    """``str | None`` is optional, exactly as ``Optional[str]`` is."""
    testbase.assert_equal(is_optional_type(str | None), True)
    testbase.assert_equal(is_optional_type(Optional[str]), True)
    return


def test_is_optional_type_is_false_for_a_union_without_none():
    """A union that cannot be ``None`` is a union but is not optional."""
    testbase.assert_equal(is_union_type(int | str), True)
    testbase.assert_equal(is_optional_type(int | str), False)
    testbase.assert_equal(is_optional_type(Union[int, str]), False)
    return


def test_is_union_type_is_false_for_a_plain_type():
    """A plain class or a generic list is not a union."""
    testbase.assert_equal(is_union_type(str), False)
    testbase.assert_equal(is_union_type(List[str]), False)
    return


def test_unwrap_optional_returns_the_inner_type_for_both_spellings():
    """The type inside an optional is found whichever way it is written."""
    testbase.assert_equal(unwrap_optional(int | None), int)
    testbase.assert_equal(unwrap_optional(Optional[int]), int)
    testbase.assert_equal(unwrap_optional(int), int)
    return


def test_non_none_members_lists_the_members_that_are_not_none():
    """The non-None members of a union are listed in declaration order."""
    testbase.assert_equal(non_none_members(int | str | None), [int, str])
    testbase.assert_equal(non_none_members(bool), [bool])
    return


def test_resolve_field_types_resolves_postponed_annotations():
    """Under postponed annotations the field types are still real types, not strings."""
    field_types = resolve_field_types(Person)

    testbase.assert_equal(field_types["name"], str)
    testbase.assert_equal(field_types["age"], int)
    testbase.assert_equal(field_types["tags"], List[str])
    testbase.assert_equal(is_optional_type(field_types["nick"]), True)
    return


def test_dataclass_schema_describes_postponed_annotations_by_their_real_type():
    """An ``int`` field written under postponed annotations is an integer, not the fallback string."""
    schema = dataclass_to_json_schema(Person)

    testbase.assert_equal(schema["properties"]["age"], {"type": "integer"})
    testbase.assert_equal(schema["properties"]["tags"], {"type": "array", "items": {"type": "string"}})
    return


def test_dataclass_schema_marks_a_pep_604_optional_field_as_nullable_and_not_required():
    """``nick: str | None = None`` allows null and is not a required property."""
    schema = dataclass_to_json_schema(Person)

    testbase.assert_equal(schema["properties"]["nick"], {"anyOf": [{"type": "string"}, {"type": "null"}]})
    testbase.assert_equal(schema["required"], ["name", "age"])
    return


def test_dataclass_schema_describes_a_nested_dataclass_as_an_object():
    """A field whose type is another dataclass is described by that dataclass's properties."""
    schema = dataclass_to_json_schema(Person)

    nested = schema["properties"]["address"]["anyOf"][0]
    testbase.assert_equal(nested["type"], "object")
    testbase.assert_equal(sorted(nested["properties"].keys()), ["city", "zip_code"])
    testbase.assert_equal(nested["required"], ["city"])
    return


def test_dataclass_schema_stops_at_a_self_reference():
    """A dataclass that refers to itself yields a finite schema."""
    schema = dataclass_to_json_schema(Node)

    testbase.assert_equal(schema["properties"]["parent"], {"anyOf": [{"type": "object"}, {"type": "null"}]})
    return


def test_type_schema_for_an_enum_lists_its_values():
    """An enum is described by the values of its members."""
    testbase.assert_equal(type_to_json_schema(Colour), {"enum": ["red", "blue"]})
    return


def test_type_schema_for_a_typed_dict_describes_its_values():
    """``Dict[str, int]`` is an object whose values are integers."""
    testbase.assert_equal(
        type_to_json_schema(Dict[str, int]),
        {"type": "object", "additionalProperties": {"type": "integer"}},
    )
    return


def test_dataclass_schema_carries_a_title_only_when_asked():
    """The class name is added as ``title`` on request."""
    testbase.assert_equal("title" in dataclass_to_json_schema(Address), False)
    testbase.assert_equal(dataclass_to_json_schema(Address, include_title=True)["title"], "Address")
    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
