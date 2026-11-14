"""
.. module:: typeinspection
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Shared helpers for reading the type annotations of schema classes.

.. moduleauthor:: Code Craft AI LLC

Schema inspection, the OpenAPI schema converter and the REST validator all
have to answer the same questions about a schema class: what are the real
types of its fields, is a field optional, and what JSON Schema describes a
type. They used to answer them separately and disagreed -- a field written
``nick: str | None`` was a plain string to one, an object to another and a
required non-null value to the third. This module is the one place that
answers them.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

import dataclasses
import enum
import logging
import types
import typing

from datetime import date, datetime, time
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID


logger = logging.getLogger(__name__)


#: The origin :func:`typing.get_origin` reports for a PEP 604 union such as
#: ``str | None``. It is not :data:`typing.Union`, which is why code that only
#: compared against ``Union`` did not recognise the newer spelling.
UNION_ORIGINS: Tuple[Any, ...] = (Union, types.UnionType)

#: JSON Schema fragments for the scalar types a schema field commonly uses.
SCALAR_JSON_SCHEMAS: Dict[Any, Dict[str, Any]] = {
    str: {"type": "string"},
    int: {"type": "integer"},
    float: {"type": "number"},
    bool: {"type": "boolean"},
    bytes: {"type": "string", "format": "binary"},
    datetime: {"type": "string", "format": "date-time"},
    date: {"type": "string", "format": "date"},
    time: {"type": "string", "format": "time"},
    UUID: {"type": "string", "format": "uuid"},
    Decimal: {"type": "string", "format": "decimal"},
    type(None): {"type": "null"},
}


def is_dataclass_type(candidate: Any) -> bool:
    """
        Whether ``candidate`` is a dataclass *class* (not an instance of one).

        :param candidate: The object to check.

        :returns: True when ``candidate`` is a dataclass class.
    """
    rtnval = isinstance(candidate, type) and dataclasses.is_dataclass(candidate)
    return rtnval


def is_union_type(field_type: Any) -> bool:
    """
        Whether ``field_type`` is a union, in either spelling: ``Union[A, B]``,
        ``Optional[A]`` or the PEP 604 form ``A | B``.

        :param field_type: The annotation to check.

        :returns: True when the annotation is a union.
    """
    origin = typing.get_origin(field_type)

    rtnval = False
    for union_origin in UNION_ORIGINS:
        if origin is union_origin:
            rtnval = True
            break

    return rtnval


def union_members(field_type: Any) -> Tuple[Any, ...]:
    """
        The member types of a union annotation.

        :param field_type: The annotation to read.

        :returns: The members of the union, or an empty tuple when the
                  annotation is not a union.
    """
    rtnval: Tuple[Any, ...] = ()
    if is_union_type(field_type):
        rtnval = typing.get_args(field_type)

    return rtnval


def is_optional_type(field_type: Any) -> bool:
    """
        Whether ``field_type`` accepts ``None``: ``Optional[T]``,
        ``Union[T, None]`` or ``T | None``.

        :param field_type: The annotation to check.

        :returns: True when ``None`` is one of the union's members.
    """
    rtnval = type(None) in union_members(field_type)
    return rtnval


def non_none_members(field_type: Any) -> List[Any]:
    """
        The members of a union annotation other than ``None``.

        :param field_type: The annotation to read.

        :returns: The non-``None`` members; a single-element list holding
                  ``field_type`` itself when it is not a union.
    """
    members = union_members(field_type)
    if len(members) == 0:
        return [field_type]

    rtnval = [member for member in members if member is not type(None)]
    return rtnval


def unwrap_optional(field_type: Any) -> Any:
    """
        The type inside ``Optional[T]`` (or ``T | None``).

        :param field_type: The annotation to unwrap.

        :returns: ``T`` when the annotation is a union of exactly one type and
                  ``None``; otherwise the annotation unchanged.
    """
    rtnval = field_type
    if is_optional_type(field_type):
        members = non_none_members(field_type)
        if len(members) == 1:
            rtnval = members[0]

    return rtnval


def resolve_field_types(schema: Any) -> Dict[str, Any]:
    """
        The real types of a schema class's fields.

        ``dataclasses.fields()`` reports an annotation exactly as it was
        written, so under ``from __future__ import annotations`` -- or for any
        quoted forward reference -- ``field.type`` is a *string*. This resolves
        the annotations with :func:`typing.get_type_hints` and falls back to
        the raw ``field.type`` for a field whose annotation cannot be resolved
        (a forward reference to a name that is not importable, say), so one
        bad annotation does not hide the others.

        :param schema: A dataclass class.

        :returns: Field name to resolved type, in field declaration order.
    """
    try:
        hints = typing.get_type_hints(schema)
    except Exception as exc:
        logger.warning(
            "get_type_hints(%s) failed (%s); falling back to the declared field types",
            getattr(schema, "__name__", schema),
            exc,
        )
        hints = {}

    rtnval: Dict[str, Any] = {}
    for dc_field in dataclasses.fields(schema):
        rtnval[dc_field.name] = hints.get(dc_field.name, dc_field.type)

    return rtnval


def field_is_required(dc_field: dataclasses.Field) -> bool:
    """
        Whether a dataclass field must be supplied: it has neither a default
        value nor a default factory.

        :param dc_field: The dataclass field.

        :returns: True when the field has no default of either kind.
    """
    rtnval = (dc_field.default is dataclasses.MISSING
              and dc_field.default_factory is dataclasses.MISSING)
    return rtnval


def type_to_json_schema(field_type: Any, _active: Optional[List[Any]] = None) -> Dict[str, Any]:
    """
        A self-contained JSON Schema fragment for a Python type.

        Handles scalars, ``List``/``Set``/``Tuple``/``Dict`` generics, unions in
        both spellings, enums, nested dataclasses and Pydantic models. Nested
        dataclasses are written inline; a dataclass that refers back to itself
        is cut off at the repeat with a bare ``{"type": "object"}`` so the
        fragment stays finite.

        A type that cannot be described -- an unresolved string annotation, an
        arbitrary class -- maps to ``{"type": "string"}``, which is what the
        endpoint schema inspectors have always reported for unknown types.

        :param field_type: The type to describe.
        :param _active: The dataclasses currently being expanded. Internal;
                        callers leave it unset.

        :returns: The JSON Schema fragment as a new dict.
    """
    active: List[Any] = _active if _active is not None else []

    if field_type is Any:
        return {}

    if isinstance(field_type, type) and field_type in SCALAR_JSON_SCHEMAS:
        return dict(SCALAR_JSON_SCHEMAS[field_type])

    if field_type is list or field_type is set or field_type is frozenset or field_type is tuple:
        return {"type": "array"}

    if field_type is dict:
        return {"type": "object"}

    if is_union_type(field_type):
        members = non_none_members(field_type)
        member_schemas = [type_to_json_schema(member, active) for member in members]
        if is_optional_type(field_type):
            member_schemas.append({"type": "null"})
        return {"anyOf": member_schemas}

    origin = typing.get_origin(field_type)
    args = typing.get_args(field_type)

    if origin is list or origin is set or origin is frozenset:
        rtnval: Dict[str, Any] = {"type": "array"}
        if len(args) > 0:
            rtnval["items"] = type_to_json_schema(args[0], active)
        return rtnval

    if origin is tuple:
        rtnval = {"type": "array"}
        # Tuple[T, ...] is a homogeneous sequence; a fixed-shape tuple has no
        # single item type to report.
        if len(args) == 2 and args[1] is Ellipsis:
            rtnval["items"] = type_to_json_schema(args[0], active)
        return rtnval

    if origin is dict:
        rtnval = {"type": "object"}
        if len(args) == 2 and args[1] is not Any:
            rtnval["additionalProperties"] = type_to_json_schema(args[1], active)
        return rtnval

    if origin is typing.Literal:
        return {"enum": list(args)}

    if isinstance(field_type, type) and issubclass(field_type, enum.Enum):
        return {"enum": [member.value for member in field_type]}

    if is_dataclass_type(field_type):
        if field_type in active:
            return {"type": "object"}
        active.append(field_type)
        try:
            rtnval = dataclass_to_json_schema(field_type, _active=active)
        finally:
            active.remove(field_type)
        return rtnval

    if hasattr(field_type, "model_json_schema"):
        return field_type.model_json_schema()

    return {"type": "string"}


def dataclass_to_json_schema(
    schema: Any,
    include_title: bool = False,
    _active: Optional[List[Any]] = None
) -> Dict[str, Any]:
    """
        A JSON Schema object definition for a dataclass.

        Field types are resolved first (see :func:`resolve_field_types`), so
        postponed annotations, PEP 604 unions and nested dataclasses are
        described by their real types.

        :param schema: The dataclass class.
        :param include_title: Add a ``title`` holding the class name.
        :param _active: The dataclasses currently being expanded. Internal;
                        callers leave it unset.

        :returns: The JSON Schema object definition.
    """
    active: List[Any] = _active if _active is not None else [schema]

    field_types = resolve_field_types(schema)

    properties: Dict[str, Any] = {}
    required: List[str] = []

    for dc_field in dataclasses.fields(schema):
        properties[dc_field.name] = type_to_json_schema(field_types[dc_field.name], active)
        if field_is_required(dc_field):
            required.append(dc_field.name)

    rtnval: Dict[str, Any] = {"type": "object"}
    if include_title:
        rtnval["title"] = schema.__name__
    rtnval["properties"] = properties

    if len(required) > 0:
        rtnval["required"] = required

    return rtnval
