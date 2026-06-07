"""
.. module:: schemaconverter
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Converts Python types to JSON Schema for OpenAPI 3.0+ specifications.

.. moduleauthor:: Code Craft AI LLC

This module provides the :class:`Schema_Converter` class which converts Python types
including dataclasses, Pydantic models, and primitive types into JSON Schema
representations suitable for inclusion in OpenAPI specifications. It handles
complex type constructs such as ``List[T]``, ``Dict[K, V]``, ``Optional[T]``,
and ``Union[A, B]``, as well as nested type references via ``$ref`` and circular
reference detection.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

import dataclasses

from datetime import date, datetime, time
from decimal import Decimal
from typing import Any, Dict, List, Optional, Set, Tuple, Type, Union
from uuid import UUID

try:
    import typing
    _get_origin = getattr(typing, "get_origin", None)
    _get_args = getattr(typing, "get_args", None)
except ImportError:
    _get_origin = None
    _get_args = None

try:
    from pydantic import BaseModel as PydanticBaseModel
    HAS_PYDANTIC = True
except ImportError:
    PydanticBaseModel = None
    HAS_PYDANTIC = False


# Type mapping for Python primitives to JSON Schema representations.
PYTHON_TO_JSON_SCHEMA: Dict[Type, Dict[str, Any]] = {
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
    Any: {},
}


class SchemaConverter:
    """
        Converts Python types to JSON Schema for OpenAPI specifications.

        The converter handles primitive types, dataclasses, Pydantic models,
        and complex generic types such as ``List``, ``Dict``, ``Optional``,
        and ``Union``. Nested complex types are tracked via ``$ref`` references
        to avoid duplication and to handle circular references.
    """

    def __init__(self):
        self._schema_cache: Dict[str, Dict[str, Any]] = {}
        self._refs: Dict[Type, str] = {}
        self._processing: Set[Type] = set()
        return

    def convert(self, python_type: Type) -> Dict[str, Any]:
        """
            Convert a Python type to JSON Schema.

            :param python_type: A Python type such as a dataclass, Pydantic model,
                primitive type, or generic type annotation.

            :returns: A JSON Schema dictionary representing the given type.
        """
        # Handle None type
        if python_type is type(None):
            result = {"type": "null"}
            return result

        # Handle primitive types
        if python_type in PYTHON_TO_JSON_SCHEMA:
            result = dict(PYTHON_TO_JSON_SCHEMA[python_type])
            return result

        # Handle generic types (List, Dict, Optional, Union)
        origin = _get_origin(python_type) if _get_origin is not None else None
        args = _get_args(python_type) if _get_args is not None else ()

        if origin is not None:
            result = self._convert_generic(origin=origin, args=args)
            return result

        # Handle dataclasses
        if dataclasses.is_dataclass(python_type) and isinstance(python_type, type):
            schema_name = self._get_schema_name(python_type=python_type)
            ref_path = f"#/components/schemas/{schema_name}"

            # Circular reference detection
            if python_type in self._processing:
                result = {"$ref": ref_path}
                return result

            # If already cached, return a $ref
            if schema_name in self._schema_cache:
                self._refs[python_type] = ref_path
                result = {"$ref": ref_path}
                return result

            # Convert and cache the dataclass schema
            self._processing.add(python_type)
            schema = self._convert_dataclass(dc_type=python_type)
            self._schema_cache[schema_name] = schema
            self._refs[python_type] = ref_path
            self._processing.discard(python_type)

            result = {"$ref": ref_path}
            return result

        # Handle Pydantic models
        if HAS_PYDANTIC and PydanticBaseModel is not None:
            if isinstance(python_type, type) and issubclass(python_type, PydanticBaseModel):
                schema_name = self._get_schema_name(python_type=python_type)
                ref_path = f"#/components/schemas/{schema_name}"

                if python_type in self._processing:
                    result = {"$ref": ref_path}
                    return result

                if schema_name in self._schema_cache:
                    self._refs[python_type] = ref_path
                    result = {"$ref": ref_path}
                    return result

                self._processing.add(python_type)
                schema = self._convert_pydantic(model_type=python_type)
                self._schema_cache[schema_name] = schema
                self._refs[python_type] = ref_path
                self._processing.discard(python_type)

                result = {"$ref": ref_path}
                return result

        # Fallback for unknown types
        result = {"type": "object"}
        return result

    def get_ref(self, python_type: Type) -> str:
        """
            Get the ``$ref`` path for a complex type.

            If the type has not been converted yet, it will be converted first
            to ensure the schema is registered.

            :param python_type: The Python type to get a reference for.

            :returns: A reference path string such as ``#/components/schemas/UserCreate``.
        """
        if python_type not in self._refs:
            self.convert(python_type=python_type)

        ref_path = self._refs.get(python_type, "")
        return ref_path

    def get_all_schemas(self) -> Dict[str, Dict[str, Any]]:
        """
            Get all collected schemas for the ``components/schemas`` section.

            :returns: A dictionary mapping schema names to their JSON Schema definitions.
        """
        result = dict(self._schema_cache)
        return result

    def _convert_dataclass(self, dc_type: Type) -> Dict[str, Any]:
        """
            Convert a dataclass type to a JSON Schema object definition.

            Extracts fields from the dataclass using ``dataclasses.fields()``,
            converts each field type recursively, and preserves field descriptions
            and default values from field metadata.

            :param dc_type: A Python dataclass type.

            :returns: A JSON Schema dictionary representing the dataclass.
        """
        properties: Dict[str, Any] = {}
        required_fields: List[str] = []

        fields = dataclasses.fields(dc_type)

        for field in fields:
            field_schema = self.convert(python_type=field.type)

            # Extract description from field metadata
            metadata = field.metadata
            if metadata is not None and "description" in metadata:
                field_schema = dict(field_schema)
                field_schema["description"] = metadata["description"]

            # Handle default values
            has_default = field.default is not dataclasses.MISSING
            has_default_factory = field.default_factory is not dataclasses.MISSING

            if has_default:
                field_schema = dict(field_schema)
                field_schema["default"] = field.default
            elif has_default_factory:
                # We note the presence of a factory but do not call it
                pass
            else:
                required_fields.append(field.name)

            properties[field.name] = field_schema

        schema: Dict[str, Any] = {
            "type": "object",
            "properties": properties,
        }

        if len(required_fields) > 0:
            schema["required"] = required_fields

        return schema

    def _convert_pydantic(self, model_type: Type) -> Dict[str, Any]:
        """
            Convert a Pydantic model type to a JSON Schema definition.

            Uses the Pydantic ``model_json_schema()`` method to generate the
            schema. If Pydantic is not installed, raises a ``RuntimeError``.

            :param model_type: A Pydantic BaseModel subclass.

            :returns: A JSON Schema dictionary representing the Pydantic model.

            :raises: RuntimeError
        """
        if not HAS_PYDANTIC:
            errmsg = "Pydantic is not installed. Cannot convert Pydantic models."
            raise RuntimeError(errmsg)

        raw_schema = model_type.model_json_schema()

        # Handle $defs from Pydantic schema and register nested models
        defs = raw_schema.pop("$defs", None)
        if defs is not None:
            for def_name, def_schema in defs.items():
                if def_name not in self._schema_cache:
                    self._schema_cache[def_name] = def_schema

        # Rewrite Pydantic $ref paths from #/$defs/Name to #/components/schemas/Name
        schema = self._rewrite_pydantic_refs(schema=raw_schema)

        return schema

    def _rewrite_pydantic_refs(self, schema: Any) -> Any:
        """
            Rewrite Pydantic ``$ref`` paths to use OpenAPI component paths.

            Pydantic generates references like ``#/$defs/ModelName`` which need
            to be rewritten to ``#/components/schemas/ModelName`` for OpenAPI
            compatibility.

            :param schema: A schema value that may contain ``$ref`` entries.

            :returns: The schema with rewritten reference paths.
        """
        if isinstance(schema, dict):
            if "$ref" in schema:
                ref_value = schema["$ref"]
                if ref_value.startswith("#/$defs/"):
                    model_name = ref_value.replace("#/$defs/", "")
                    schema["$ref"] = f"#/components/schemas/{model_name}"
                return schema

            rewritten = {}
            for key, value in schema.items():
                rewritten[key] = self._rewrite_pydantic_refs(schema=value)
            return rewritten

        if isinstance(schema, list):
            rewritten_list = []
            for item in schema:
                rewritten_list.append(self._rewrite_pydantic_refs(schema=item))
            return rewritten_list

        return schema

    def _convert_primitive(self, python_type: Type) -> Dict[str, Any]:
        """
            Convert a primitive Python type to its JSON Schema representation.

            :param python_type: A primitive Python type from the ``PYTHON_TO_JSON_SCHEMA`` mapping.

            :returns: A JSON Schema dictionary for the primitive type.
        """
        if python_type in PYTHON_TO_JSON_SCHEMA:
            result = dict(PYTHON_TO_JSON_SCHEMA[python_type])
            return result

        result = {"type": "object"}
        return result

    def _convert_generic(self, origin: Type, args: Tuple) -> Dict[str, Any]:
        """
            Convert a generic type annotation to JSON Schema.

            Dispatches to the appropriate handler based on the origin type
            (``list``, ``dict``, ``Union``).

            :param origin: The origin type of the generic (e.g., ``list``, ``dict``).
            :param args: The type arguments of the generic.

            :returns: A JSON Schema dictionary for the generic type.
        """
        # Handle List[T]
        if origin is list:
            item_type = args[0] if len(args) > 0 else Any
            result = self._convert_list(item_type=item_type)
            return result

        # Handle Dict[K, V]
        if origin is dict:
            key_type = args[0] if len(args) > 0 else str
            value_type = args[1] if len(args) > 1 else Any
            result = self._convert_dict(key_type=key_type, value_type=value_type)
            return result

        # Handle Optional[T] which is Union[T, None]
        if origin is Union:
            non_none_types = [t for t in args if t is not type(None)]
            has_none = len(non_none_types) < len(args)

            if has_none and len(non_none_types) == 1:
                result = self._convert_optional(inner_type=non_none_types[0])
                return result

            if len(non_none_types) > 1:
                result = self._convert_union(types=tuple(non_none_types))
                if has_none:
                    result = dict(result)
                    result["nullable"] = True
                return result

            if len(non_none_types) == 1:
                result = self.convert(python_type=non_none_types[0])
                return result

        # Fallback
        result = {"type": "object"}
        return result

    def _convert_list(self, item_type: Type) -> Dict[str, Any]:
        """
            Convert a ``List[T]`` type to a JSON Schema array definition.

            :param item_type: The element type of the list.

            :returns: A JSON Schema dictionary with ``type: array`` and ``items``.
        """
        items_schema = self.convert(python_type=item_type)

        result = {
            "type": "array",
            "items": items_schema,
        }

        return result

    def _convert_dict(self, key_type: Type, value_type: Type) -> Dict[str, Any]:
        """
            Convert a ``Dict[K, V]`` type to a JSON Schema object definition.

            JSON Schema objects use ``additionalProperties`` to describe the
            value type. The key type is assumed to be string-compatible.

            :param key_type: The key type of the dictionary.
            :param value_type: The value type of the dictionary.

            :returns: A JSON Schema dictionary with ``type: object`` and ``additionalProperties``.
        """
        value_schema = self.convert(python_type=value_type)

        result: Dict[str, Any] = {
            "type": "object",
            "additionalProperties": value_schema,
        }

        return result

    def _convert_optional(self, inner_type: Type) -> Dict[str, Any]:
        """
            Convert an ``Optional[T]`` type to a nullable JSON Schema.

            :param inner_type: The inner type that is optional.

            :returns: A JSON Schema dictionary with the ``nullable`` flag set to ``True``.
        """
        inner_schema = self.convert(python_type=inner_type)
        result = dict(inner_schema)
        result["nullable"] = True

        return result

    def _convert_union(self, types: Tuple[Type, ...]) -> Dict[str, Any]:
        """
            Convert a ``Union[A, B, ...]`` type to a JSON Schema ``oneOf`` definition.

            :param types: The tuple of types in the union.

            :returns: A JSON Schema dictionary with a ``oneOf`` array.
        """
        schemas = []
        for union_type in types:
            schema = self.convert(python_type=union_type)
            schemas.append(schema)

        result = {"oneOf": schemas}

        return result

    def _get_schema_name(self, python_type: Type) -> str:
        """
            Generate a unique schema name from a Python type.

            Uses the class ``__name__`` attribute. If a name collision is detected
            with a different type already in the cache, the module name is prepended
            for disambiguation.

            :param python_type: The Python type to generate a name for.

            :returns: A unique schema name string.
        """
        base_name = python_type.__name__

        # Check for name collision with a different type
        if base_name in self._schema_cache:
            existing_ref_types = [
                t for t, ref in self._refs.items()
                if ref == f"#/components/schemas/{base_name}"
            ]
            if len(existing_ref_types) > 0 and python_type not in existing_ref_types:
                module_name = getattr(python_type, "__module__", "")
                disambiguated_name = f"{module_name}.{base_name}"
                return disambiguated_name

        return base_name
