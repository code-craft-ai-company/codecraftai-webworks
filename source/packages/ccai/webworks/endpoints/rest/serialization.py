"""
.. module:: ccai.webworks.endpoints.rest.serialization
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Serialization and deserialization infrastructure for REST API support.
               Provides protocol classes, JSON implementations, and a registry for
               content type negotiation.

.. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

import base64
import dataclasses
import enum
import json

from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Protocol, Type, runtime_checkable
from uuid import UUID

from ccai.webworks.endpoints.rest.exceptions import ValidationError
from ccai.webworks.endpoints.rest.models import FieldError
from ccai.webworks.endpoints.typeinspection import resolve_field_types, unwrap_optional


@runtime_checkable
class Serializer(Protocol):
    """
        Protocol for response serializers.
        
        Serializers convert Python objects to wire format (bytes) for
        response bodies. Each serializer handles a specific content type.
        
        Attributes:
            content_type: MIME type this serializer handles, e.g., "application/json".
    """
    
    content_type: str
    
    def serialize(self, data: Any, schema: Optional[Type] = None) -> bytes:
        """
            Serialize data to wire format.
            
            Args:
                data: Python object to serialize (dict, dataclass, Pydantic model, or list).
                schema: Optional schema type for type hints during serialization.
            
            Returns:
                Serialized bytes in the serializer's content type format.
        """


@runtime_checkable
class Deserializer(Protocol):
    """
        Protocol for request deserializers.
        
        Deserializers convert wire format data (bytes) to Python objects
        for request bodies. Each deserializer handles a specific content type.
        
        Attributes:
            content_type: MIME type this deserializer handles, e.g., "application/json".
    """
    
    content_type: str
    
    def deserialize(self, data: bytes, schema: Type) -> Any:
        """
            Deserialize wire format to Python object.
            
            Args:
                data: Raw bytes from request body.
                schema: Target schema type to deserialize into.
            
            Returns:
                Deserialized object matching the schema type.
            
            Raises:
                ValidationError: If deserialization fails due to malformed data
                                 or type mismatches.
        """



def _is_dataclass_type(obj_type: Type) -> bool:
    """Check if a type is a dataclass."""
    return dataclasses.is_dataclass(obj_type) and isinstance(obj_type, type)


def _is_dataclass_instance(obj: Any) -> bool:
    """Check if an object is a dataclass instance."""
    return dataclasses.is_dataclass(obj) and not isinstance(obj, type)


def _is_pydantic_model_type(obj_type: Type) -> bool:
    """Check if a type is a Pydantic model class."""
    try:
        from pydantic import BaseModel
        return isinstance(obj_type, type) and issubclass(obj_type, BaseModel)
    except ImportError:
        return False


def _is_pydantic_model_instance(obj: Any) -> bool:
    """Check if an object is a Pydantic model instance."""
    try:
        from pydantic import BaseModel
        return isinstance(obj, BaseModel)
    except ImportError:
        return False


def to_json_compatible(data: Any) -> Any:
    """
        Convert a Python value into one :func:`json.dumps` can write.

        Containers are converted recursively, so a ``datetime`` three levels
        down inside a dataclass is handled the same as one at the top. The
        conversions are:

        - ``datetime`` / ``date`` / ``time``: ISO 8601 text.
        - ``timedelta``: seconds, as a number.
        - ``UUID`` and ``Decimal``: their text form. A ``Decimal`` is not
          written as a JSON number because a float cannot hold it exactly.
        - ``Enum``: the member's value, converted in turn.
        - ``bytes`` / ``bytearray``: base64 text.
        - ``set`` / ``frozenset`` / ``tuple``: a list.
        - Pydantic model: ``model_dump(mode="json")``.
        - an object with a ``to_dict()`` method: the converted result.
        - any other dataclass instance: an object of its fields.

        A dict key that is not a string, number, bool or None is converted the
        same way and then written as text.

        :param data: The value to convert.

        :returns: A value built only from dict, list, str, int, float, bool
                  and None.

        :raises TypeError: If a value has no JSON representation. It used to
                           be written as ``str(value)``, which put text such
                           as ``<Order object at 0x7f...>`` in a response and
                           hid the mistake.
    """
    # Enum first: an IntEnum or StrEnum member is also an int or a str.
    if isinstance(data, enum.Enum):
        return to_json_compatible(data.value)

    if data is None or isinstance(data, (str, bool, int, float)):
        return data

    if isinstance(data, dict):
        converted: Dict[Any, Any] = {}
        for key, value in data.items():
            converted[_to_json_key(key)] = to_json_compatible(value)
        return converted

    if isinstance(data, (list, tuple, set, frozenset)):
        return [to_json_compatible(item) for item in data]

    if isinstance(data, (datetime, date, time)):
        return data.isoformat()

    if isinstance(data, timedelta):
        return data.total_seconds()

    if isinstance(data, (UUID, Decimal)):
        return str(data)

    if isinstance(data, (bytes, bytearray)):
        return base64.b64encode(bytes(data)).decode("ascii")

    if _is_pydantic_model_instance(data):
        # mode="json" makes Pydantic itself render datetime, UUID, Decimal
        # and Enum fields, honouring any serializers the model declares.
        return to_json_compatible(data.model_dump(mode="json"))

    # An object that defines its own wire form (PaginatedResponse,
    # BulkOperationResult, RESTError) is asked for it, before the generic
    # dataclass rule below would dump its fields as they are.
    to_dict = getattr(data, "to_dict", None)
    if callable(to_dict):
        return to_json_compatible(to_dict())

    if _is_dataclass_instance(data):
        # Not dataclasses.asdict(): it deep-copies every value, and what is
        # needed here is the conversion of each field.
        converted = {}
        for dc_field in dataclasses.fields(data):
            converted[dc_field.name] = to_json_compatible(getattr(data, dc_field.name))
        return converted

    errmsg = "Object of type {} is not JSON serializable".format(type(data).__name__)
    raise TypeError(errmsg)


def _to_json_key(key: Any) -> Any:
    """
        Convert a dict key into one JSON accepts.

        :param key: The key to convert.

        :returns: The key unchanged when JSON accepts it as it is, otherwise
                  its converted value as text.
    """
    if isinstance(key, enum.Enum):
        rtnval = str(to_json_compatible(key.value))
        return rtnval

    if key is None or isinstance(key, (str, int, float, bool)):
        return key

    rtnval = str(to_json_compatible(key))
    return rtnval


class JSONSerializer:
    """
        JSON serializer supporting dataclasses and Pydantic models.
        
        This serializer converts Python objects to JSON bytes. It handles:
        - dict: Direct JSON encoding
        - dataclass: An object of its fields
        - Pydantic model: Use model_dump(mode="json")
        - list: Serialize each item recursively
        - datetime, date, time, UUID, Decimal, Enum and bytes values,
          wherever they appear (see :func:`to_json_compatible`)
        
        Attributes:
            content_type: Always "application/json".
    """
    
    content_type: str = "application/json"
    
    def serialize(self, data: Any, schema: Optional[Type] = None) -> bytes:
        """
            Serialize data to JSON bytes.
            
            Args:
                data: Python object to serialize.
                schema: Optional schema type (unused, for protocol compatibility).
            
            Returns:
                JSON-encoded bytes with UTF-8 encoding.

            Raises:
                TypeError: If a value in ``data`` has no JSON representation.
        """
        converted = self._convert_to_serializable(data)
        return json.dumps(converted, ensure_ascii=False).encode("utf-8")
    
    def _convert_to_serializable(self, data: Any) -> Any:
        """
            Convert data to a JSON-serializable form.
            
            Args:
                data: Data to convert.
            
            Returns:
                JSON-serializable Python object (dict, list, or primitive).
        """
        rtnval = to_json_compatible(data)
        return rtnval



class JSONDeserializer:
    """
        JSON deserializer supporting dataclasses and Pydantic models.
        
        This deserializer converts JSON bytes to Python objects. It handles:
        - dict schema: Return parsed JSON dict
        - dataclass: Construct from parsed dict
        - Pydantic model: Use model_validate()
        
        Attributes:
            content_type: Always "application/json".
    """
    
    content_type: str = "application/json"
    
    def deserialize(self, data: bytes, schema: Type) -> Any:
        """
            Deserialize JSON bytes to schema instance.
            
            Args:
                data: Raw JSON bytes from request body.
                schema: Target schema type to deserialize into.
            
            Returns:
                Deserialized object matching the schema type.
            
            Raises:
                ValidationError: On JSON parse errors or type mismatches.
        """
        # Parse JSON
        try:
            parsed = json.loads(data.decode("utf-8"))
        except json.JSONDecodeError as e:
            raise ValidationError(
                message=f"Invalid JSON: {e.msg}",
                field_errors=[
                    FieldError(
                        field="$",
                        code="parse_error",
                        message=f"JSON parse error at line {e.lineno}, column {e.colno}: {e.msg}"
                    )
                ]
            )
        except UnicodeDecodeError as e:
            raise ValidationError(
                message="Invalid UTF-8 encoding in request body",
                field_errors=[
                    FieldError(
                        field="$",
                        code="encoding_error",
                        message=str(e)
                    )
                ]
            )
        
        # Handle dict schema (untyped JSON)
        if schema is dict:
            if not isinstance(parsed, dict):
                raise ValidationError(
                    message="Expected JSON object",
                    field_errors=[
                        FieldError(
                            field="$",
                            code="type_error",
                            message=f"Expected object, got {type(parsed).__name__}"
                        )
                    ]
                )
            return parsed
        
        # Handle Pydantic model
        if _is_pydantic_model_type(schema):
            return self._deserialize_pydantic(parsed, schema)
        
        # Handle dataclass
        if _is_dataclass_type(schema):
            return self._deserialize_dataclass(parsed, schema)
        
        # Fallback: return parsed data as-is
        return parsed
    
    def _deserialize_pydantic(self, data: Any, schema: Type) -> Any:
        """
            Deserialize data to a Pydantic model.
            
            Args:
                data: Parsed JSON data.
                schema: Pydantic model class.
            
            Returns:
                Pydantic model instance.
            
            Raises:
                ValidationError: On validation errors.
        """
        try:
            from pydantic import ValidationError as PydanticValidationError
            
            return schema.model_validate(data)
        except PydanticValidationError as e:
            field_errors = []
            for error in e.errors():
                # Build field path from location
                loc = error.get("loc", ())
                field_path = ".".join(str(part) for part in loc) if loc else "$"
                
                field_errors.append(FieldError(
                    field=field_path,
                    code=error.get("type", "validation_error"),
                    message=error.get("msg", "Validation failed")
                ))
            
            raise ValidationError(
                message="Request validation failed",
                field_errors=field_errors
            )
    
    def _deserialize_dataclass(self, data: Any, schema: Type) -> Any:
        """
            Deserialize data to a dataclass.
            
            Args:
                data: Parsed JSON data (should be a dict).
                schema: Dataclass type.
            
            Returns:
                Dataclass instance.
            
            Raises:
                ValidationError: On type errors or missing required fields.
        """
        if not isinstance(data, dict):
            raise ValidationError(
                message="Expected JSON object for dataclass",
                field_errors=[
                    FieldError(
                        field="$",
                        code="type_error",
                        message=f"Expected object, got {type(data).__name__}"
                    )
                ]
            )
        
        # Get dataclass fields
        fields = dataclasses.fields(schema)
        field_errors: List[FieldError] = []
        kwargs: Dict[str, Any] = {}

        # Resolve the annotations to real types: under postponed annotations
        # ``dc_field.type`` is a string, and an optional nested dataclass
        # (``Address | None``) is a union, so neither would be recognised
        # as a nested dataclass from the declared type alone.
        field_types = resolve_field_types(schema)
        
        for dc_field in fields:
            field_name = dc_field.name
            field_type = unwrap_optional(field_types.get(field_name, dc_field.type))
            
            if field_name in data:
                # Field is present in data
                value = data[field_name]
                
                # Check for nested dataclass
                if value is not None and _is_dataclass_type(field_type):
                    try:
                        value = self._deserialize_dataclass(value, field_type)
                    except ValidationError as e:
                        # Prefix field errors with parent field name
                        for fe in e.field_errors:
                            prefixed_field = f"{field_name}.{fe.field}" if fe.field != "$" else field_name
                            field_errors.append(FieldError(
                                field=prefixed_field,
                                code=fe.code,
                                message=fe.message
                            ))
                        continue
                
                kwargs[field_name] = value
            
            elif dc_field.default is not dataclasses.MISSING:
                # Field has a default value
                kwargs[field_name] = dc_field.default
            
            elif dc_field.default_factory is not dataclasses.MISSING:
                # Field has a default factory
                kwargs[field_name] = dc_field.default_factory()
            
            else:
                # Required field is missing
                field_errors.append(FieldError(
                    field=field_name,
                    code="required",
                    message=f"Field '{field_name}' is required"
                ))
        
        if field_errors:
            raise ValidationError(
                message="Request validation failed",
                field_errors=field_errors
            )
        
        try:
            return schema(**kwargs)
        except TypeError as e:
            raise ValidationError(
                message=f"Failed to construct {schema.__name__}: {e}",
                field_errors=[
                    FieldError(
                        field="$",
                        code="construction_error",
                        message=str(e)
                    )
                ]
            )



class SerializerRegistry:
    """
        Registry of serializers and deserializers by content type.
        
        This registry stores serializers and deserializers indexed by their
        content type. It provides methods to register, retrieve, and negotiate
        content types based on HTTP Accept headers.
        
        Attributes:
            _serializers: Dictionary mapping content types to serializers.
            _deserializers: Dictionary mapping content types to deserializers.
    """
    
    def __init__(self):
        """Initialize an empty registry."""
        self._serializers: Dict[str, Serializer] = {}
        self._deserializers: Dict[str, Deserializer] = {}
    
    def register_serializer(self, serializer: Serializer) -> None:
        """
            Register a serializer for its content type.
            
            Args:
                serializer: Serializer instance to register.
        """
        self._serializers[serializer.content_type] = serializer
    
    def register_deserializer(self, deserializer: Deserializer) -> None:
        """
            Register a deserializer for its content type.
            
            Args:
                deserializer: Deserializer instance to register.
        """
        self._deserializers[deserializer.content_type] = deserializer
    
    def get_serializer(self, content_type: str) -> Optional[Serializer]:
        """
            Get serializer for a content type.
            
            Args:
                content_type: MIME type to look up.
            
            Returns:
                Serializer for the content type, or None if not found.
        """
        # Handle content type with parameters (e.g., "application/json; charset=utf-8")
        base_type = content_type.split(";")[0].strip().lower()
        return self._serializers.get(base_type)
    
    def get_deserializer(self, content_type: str) -> Optional[Deserializer]:
        """
            Get deserializer for a content type.
            
            Args:
                content_type: MIME type to look up.
            
            Returns:
                Deserializer for the content type, or None if not found.
        """
        # Handle content type with parameters
        base_type = content_type.split(";")[0].strip().lower()
        return self._deserializers.get(base_type)
    
    def negotiate_content_type(self, accept_header: str) -> Optional[str]:
        """
            Select best content type from Accept header.
            
            Parses the Accept header and returns the first supported content type
            based on quality values (q parameter). If no Accept header is provided
            or is empty, returns None (caller should default to application/json).
            
            Args:
                accept_header: HTTP Accept header value.
            
            Returns:
                Selected content type, or None if no match found.
        """
        if not accept_header or not accept_header.strip():
            return None
        
        # Parse Accept header into list of (content_type, quality) tuples
        parsed_types = self._parse_accept_header(accept_header)

        # A range with q=0 means "not acceptable" (RFC 9110 section 12.4.2):
        # it is never selected, and a type it names is not selected through
        # a wildcard either.
        refused_types = [content_type for content_type, quality in parsed_types if quality <= 0.0]
        accept_types = [(content_type, quality) for content_type, quality in parsed_types if quality > 0.0]
        
        # Sort by quality (descending)
        accept_types.sort(key=lambda x: x[1], reverse=True)
        
        # Find first supported type
        for content_type, _ in accept_types:
            # Handle wildcards
            if content_type == "*/*":
                # Return the first registered serializer the client did not refuse
                for registered_type in self._serializers.keys():
                    if not self._is_refused(registered_type, refused_types):
                        return registered_type
            elif content_type.endswith("/*"):
                # Type wildcard (e.g., "application/*")
                type_prefix = content_type[:-1]  # "application/"
                for registered_type in self._serializers.keys():
                    if registered_type.startswith(type_prefix):
                        if not self._is_refused(registered_type, refused_types):
                            return registered_type
            elif content_type in self._serializers:
                return content_type
        
        return None

    @staticmethod
    def _is_refused(content_type: str, refused_types: List[str]) -> bool:
        """
            Whether a content type is covered by a media range the client
            sent with ``q=0``.

            Args:
                content_type: A registered content type.
                refused_types: The media ranges sent with ``q=0``.

            Returns:
                True if the client refused the content type.
        """
        for refused in refused_types:
            if refused == "*/*" or refused == content_type:
                return True
            if refused.endswith("/*") and content_type.startswith(refused[:-1]):
                return True

        return False
    
    def _parse_accept_header(self, accept_header: str) -> List[tuple]:
        """
            Parse Accept header into list of (content_type, quality) tuples.
            
            Args:
                accept_header: HTTP Accept header value.
            
            Returns:
                List of (content_type, quality) tuples.
        """
        result = []
        
        for part in accept_header.split(","):
            part = part.strip()
            if not part:
                continue
            
            # Split content type from parameters
            segments = part.split(";")
            content_type = segments[0].strip().lower()
            
            # Default quality is 1.0
            quality = 1.0
            
            # Look for q parameter
            for segment in segments[1:]:
                segment = segment.strip()
                if segment.startswith("q="):
                    try:
                        quality = float(segment[2:])
                    except ValueError:
                        quality = 0.0
                    break
            
            result.append((content_type, quality))
        
        return result
    
    @property
    def supported_content_types(self) -> List[str]:
        """
            Get list of supported content types for serialization.
            
            Returns:
                List of registered serializer content types.
        """
        return list(self._serializers.keys())
    
    @property
    def supported_request_types(self) -> List[str]:
        """
            Get list of supported content types for deserialization.
            
            Returns:
                List of registered deserializer content types.
        """
        return list(self._deserializers.keys())


def create_default_registry() -> SerializerRegistry:
    """
        Create a SerializerRegistry with default JSON serializer and deserializer.
        
        Returns:
            SerializerRegistry with JSONSerializer and JSONDeserializer registered.
    """
    registry = SerializerRegistry()
    registry.register_serializer(JSONSerializer())
    registry.register_deserializer(JSONDeserializer())
    return registry
