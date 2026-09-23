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

import dataclasses
import json
from typing import Any, Dict, List, Optional, Protocol, Type, runtime_checkable

from ccai.webworks.endpoints.rest.exceptions import ValidationError
from ccai.webworks.endpoints.rest.models import FieldError


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


class JSONSerializer:
    """
        JSON serializer supporting dataclasses and Pydantic models.
        
        This serializer converts Python objects to JSON bytes. It handles:
        - dict: Direct JSON encoding
        - dataclass: Convert to dict via dataclasses.asdict()
        - Pydantic model: Use model_dump()
        - list: Serialize each item recursively
        
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
        if data is None:
            return None
        
        if isinstance(data, (str, int, float, bool)):
            return data
        
        if isinstance(data, dict):
            return {key: self._convert_to_serializable(value) for key, value in data.items()}
        
        if isinstance(data, (list, tuple)):
            return [self._convert_to_serializable(item) for item in data]
        
        if _is_pydantic_model_instance(data):
            # Pydantic model: use model_dump()
            return data.model_dump()
        
        if _is_dataclass_instance(data):
            # Dataclass: use asdict()
            return dataclasses.asdict(data)
        
        # Fallback: try to convert to string
        return str(data)



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
        
        for dc_field in fields:
            field_name = dc_field.name
            
            if field_name in data:
                # Field is present in data
                value = data[field_name]
                
                # Check for nested dataclass
                if _is_dataclass_type(dc_field.type):
                    try:
                        value = self._deserialize_dataclass(value, dc_field.type)
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
        accept_types = self._parse_accept_header(accept_header)
        
        # Sort by quality (descending)
        accept_types.sort(key=lambda x: x[1], reverse=True)
        
        # Find first supported type
        for content_type, _ in accept_types:
            # Handle wildcards
            if content_type == "*/*":
                # Return first registered serializer's content type
                if self._serializers:
                    return next(iter(self._serializers.keys()))
            elif content_type.endswith("/*"):
                # Type wildcard (e.g., "application/*")
                type_prefix = content_type[:-1]  # "application/"
                for registered_type in self._serializers.keys():
                    if registered_type.startswith(type_prefix):
                        return registered_type
            elif content_type in self._serializers:
                return content_type
        
        return None
    
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
