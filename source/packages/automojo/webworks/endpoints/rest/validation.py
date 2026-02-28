"""
.. module:: automojo.webworks.endpoints.rest.validation
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Validation infrastructure for REST API support.
               Provides schema validation for dataclasses and Pydantic models
               with support for partial updates and nested validation.

.. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

import dataclasses
from typing import Any, Dict, List, Optional, Type, get_type_hints, get_origin, get_args, Union

from automojo.webworks.endpoints.rest.exceptions import ValidationError
from automojo.webworks.endpoints.rest.models import FieldError


def _is_dataclass_type(obj_type: Type) -> bool:
    """Check if a type is a dataclass."""
    return dataclasses.is_dataclass(obj_type) and isinstance(obj_type, type)


def _is_pydantic_model_type(obj_type: Type) -> bool:
    """Check if a type is a Pydantic model class."""
    try:
        from pydantic import BaseModel
        return isinstance(obj_type, type) and issubclass(obj_type, BaseModel)
    except ImportError:
        return False


def _is_optional_type(field_type: Type) -> bool:
    """Check if a type is Optional (Union with None)."""
    origin = get_origin(field_type)
    if origin is Union:
        args = get_args(field_type)
        return type(None) in args
    return False


def _get_inner_type(field_type: Type) -> Type:
    """Get the inner type from Optional[T] -> T."""
    origin = get_origin(field_type)
    if origin is Union:
        args = get_args(field_type)
        # Filter out NoneType
        non_none_args = [arg for arg in args if arg is not type(None)]
        if len(non_none_args) == 1:
            return non_none_args[0]
    return field_type


class Validator:
    """
        Schema validator supporting dataclasses and Pydantic models.
        
        This validator validates incoming data against schema definitions,
        supporting both Pydantic models and dataclasses. It provides:
        - Full validation for create/update operations
        - Partial validation for PATCH operations (partial=True)
        - Nested schema validation with field path tracking
        - Detailed field-level error reporting
    """
    
    def validate(
        self,
        data: Any,
        schema: Type,
        partial: bool = False
    ) -> Any:
        """
            Validate data against schema.
            
            Args:
                data: Data to validate (usually dict from JSON).
                schema: Schema type to validate against (dataclass or Pydantic model).
                partial: If True, required fields are optional (for PATCH operations).
            
            Returns:
                Validated and coerced data as schema instance.
            
            Raises:
                ValidationError: If validation fails with field-level error details.
        """
        if data is None:
            raise ValidationError(
                message="Request body is required",
                field_errors=[
                    FieldError(
                        field="$",
                        code="required",
                        message="Request body cannot be null"
                    )
                ]
            )
        
        # Handle dict schema (untyped JSON)
        if schema is dict:
            if not isinstance(data, dict):
                raise ValidationError(
                    message="Expected JSON object",
                    field_errors=[
                        FieldError(
                            field="$",
                            code="type_error",
                            message=f"Expected object, got {type(data).__name__}"
                        )
                    ]
                )
            return data
        
        # Handle Pydantic model
        if _is_pydantic_model_type(schema):
            return self._validate_pydantic(data, schema, partial)
        
        # Handle dataclass
        if _is_dataclass_type(schema):
            return self._validate_dataclass(data, schema, partial)
        
        # Unsupported schema type
        raise ValidationError(
            message=f"Unsupported schema type: {schema}",
            field_errors=[
                FieldError(
                    field="$",
                    code="schema_error",
                    message=f"Schema must be a dataclass or Pydantic model, got {schema}"
                )
            ]
        )
    
    def _validate_pydantic(
        self,
        data: Any,
        schema: Type,
        partial: bool
    ) -> Any:
        """
            Validate using Pydantic model.
            
            Uses Pydantic's model_validate() for validation. For partial updates,
            creates a modified model with all fields optional.
            
            Args:
                data: Data to validate (should be a dict).
                schema: Pydantic model class.
                partial: If True, all required fields become optional.
            
            Returns:
                Validated Pydantic model instance.
            
            Raises:
                ValidationError: On validation errors with field details.
        """
        if not isinstance(data, dict):
            raise ValidationError(
                message="Expected JSON object",
                field_errors=[
                    FieldError(
                        field="$",
                        code="type_error",
                        message=f"Expected object, got {type(data).__name__}"
                    )
                ]
            )
        
        try:
            from pydantic import ValidationError as PydanticValidationError
            
            if partial:
                # For partial validation, we validate only the provided fields
                # by creating a partial model or using model_construct with validation
                return self._validate_pydantic_partial(data, schema)
            else:
                return schema.model_validate(data)
                
        except PydanticValidationError as e:
            field_errors = self._convert_pydantic_errors(e)
            raise ValidationError(
                message="Request validation failed",
                field_errors=field_errors
            )
    
    def _validate_pydantic_partial(self, data: Dict[str, Any], schema: Type) -> Any:
        """
            Validate partial data against Pydantic model.
            
            For partial updates, only validates the fields that are present
            in the data, allowing required fields to be omitted.
            
            Args:
                data: Partial data to validate.
                schema: Pydantic model class.
            
            Returns:
                Pydantic model instance with only provided fields set.
            
            Raises:
                ValidationError: On validation errors for provided fields.
        """
        from pydantic import ValidationError as PydanticValidationError
        
        # Get model fields
        model_fields = schema.model_fields
        
        # Validate each provided field individually
        field_errors: List[FieldError] = []
        validated_data: Dict[str, Any] = {}
        
        for field_name, value in data.items():
            if field_name not in model_fields:
                # Unknown field - could be an error or ignored based on model config
                # For now, we'll include it and let Pydantic handle extra fields
                validated_data[field_name] = value
                continue
            
            field_info = model_fields[field_name]
            field_type = field_info.annotation
            
            # Validate the individual field value
            try:
                # For nested Pydantic models, recursively validate
                if _is_pydantic_model_type(field_type):
                    if isinstance(value, dict):
                        validated_data[field_name] = self._validate_pydantic(value, field_type, partial=False)
                    else:
                        validated_data[field_name] = value
                else:
                    validated_data[field_name] = value
            except ValidationError as e:
                # Prefix field errors with current field name
                for fe in e.field_errors:
                    prefixed_field = f"{field_name}.{fe.field}" if fe.field != "$" else field_name
                    field_errors.append(FieldError(
                        field=prefixed_field,
                        code=fe.code,
                        message=fe.message
                    ))
        
        if field_errors:
            raise ValidationError(
                message="Request validation failed",
                field_errors=field_errors
            )
        
        # Use model_construct to create instance without full validation
        # but we've already validated the provided fields
        try:
            # Try to validate with only the provided fields
            # Create a temporary dict with defaults for missing required fields
            return schema.model_construct(**validated_data)
        except Exception as e:
            raise ValidationError(
                message=f"Failed to construct partial model: {e}",
                field_errors=[
                    FieldError(
                        field="$",
                        code="construction_error",
                        message=str(e)
                    )
                ]
            )
    
    def _convert_pydantic_errors(self, pydantic_error) -> List[FieldError]:
        """
            Convert Pydantic validation errors to FieldError list.
            
            Args:
                pydantic_error: Pydantic ValidationError instance.
            
            Returns:
                List of FieldError objects with field paths.
        """
        field_errors = []
        for error in pydantic_error.errors():
            # Build field path from location
            loc = error.get("loc", ())
            field_path = ".".join(str(part) for part in loc) if loc else "$"
            
            field_errors.append(FieldError(
                field=field_path,
                code=error.get("type", "validation_error"),
                message=error.get("msg", "Validation failed")
            ))
        
        return field_errors
    
    def _validate_dataclass(
        self,
        data: Any,
        schema: Type,
        partial: bool,
        field_prefix: str = ""
    ) -> Any:
        """
            Validate using dataclass fields.
            
            Validates data against dataclass field definitions, supporting:
            - Required vs optional fields
            - Default values and default factories
            - Nested dataclass validation
            - Field metadata validation
            - Post-init validation via __post_init__
            
            Args:
                data: Data to validate (should be a dict).
                schema: Dataclass type.
                partial: If True, required fields are optional.
                field_prefix: Prefix for nested field paths (e.g., "user.address").
            
            Returns:
                Validated dataclass instance.
            
            Raises:
                ValidationError: On validation errors with field details.
        """
        if not isinstance(data, dict):
            field_path = field_prefix if field_prefix else "$"
            raise ValidationError(
                message="Expected JSON object for dataclass",
                field_errors=[
                    FieldError(
                        field=field_path,
                        code="type_error",
                        message=f"Expected object, got {type(data).__name__}"
                    )
                ]
            )
        
        # Get dataclass fields
        fields = dataclasses.fields(schema)
        field_errors: List[FieldError] = []
        kwargs: Dict[str, Any] = {}
        
        # Try to get type hints for better type checking
        try:
            type_hints = get_type_hints(schema)
        except Exception:
            type_hints = {}
        
        for dc_field in fields:
            field_name = dc_field.name
            full_field_path = f"{field_prefix}.{field_name}" if field_prefix else field_name
            field_type = type_hints.get(field_name, dc_field.type)
            
            if field_name in data:
                # Field is present in data
                value = data[field_name]
                
                # Handle None value
                if value is None:
                    if _is_optional_type(field_type):
                        kwargs[field_name] = None
                        continue
                    else:
                        field_errors.append(FieldError(
                            field=full_field_path,
                            code="type_error",
                            message=f"Field '{field_name}' cannot be null"
                        ))
                        continue
                
                # Get the actual type (unwrap Optional)
                actual_type = _get_inner_type(field_type) if _is_optional_type(field_type) else field_type
                
                # Check for nested dataclass
                if _is_dataclass_type(actual_type):
                    try:
                        value = self._validate_dataclass(
                            value, 
                            actual_type, 
                            partial=False,  # Nested objects are fully validated
                            field_prefix=full_field_path
                        )
                    except ValidationError as e:
                        field_errors.extend(e.field_errors)
                        continue
                
                # Check for nested Pydantic model
                elif _is_pydantic_model_type(actual_type):
                    try:
                        value = self._validate_pydantic(value, actual_type, partial=False)
                    except ValidationError as e:
                        # Prefix field errors with current field path
                        for fe in e.field_errors:
                            prefixed_field = f"{full_field_path}.{fe.field}" if fe.field != "$" else full_field_path
                            field_errors.append(FieldError(
                                field=prefixed_field,
                                code=fe.code,
                                message=fe.message
                            ))
                        continue
                
                # Check for list of nested objects
                elif get_origin(actual_type) is list:
                    list_args = get_args(actual_type)
                    if list_args and (_is_dataclass_type(list_args[0]) or _is_pydantic_model_type(list_args[0])):
                        if isinstance(value, list):
                            validated_list = []
                            for idx, item in enumerate(value):
                                item_path = f"{full_field_path}.{idx}"
                                try:
                                    if _is_dataclass_type(list_args[0]):
                                        validated_item = self._validate_dataclass(
                                            item, list_args[0], partial=False, field_prefix=item_path
                                        )
                                    else:
                                        validated_item = self._validate_pydantic(item, list_args[0], partial=False)
                                    validated_list.append(validated_item)
                                except ValidationError as e:
                                    field_errors.extend(e.field_errors)
                            value = validated_list
                        else:
                            field_errors.append(FieldError(
                                field=full_field_path,
                                code="type_error",
                                message=f"Expected list, got {type(value).__name__}"
                            ))
                            continue
                
                # Validate field metadata if present
                metadata_errors = self._validate_field_metadata(dc_field, value, full_field_path)
                if metadata_errors:
                    field_errors.extend(metadata_errors)
                    continue
                
                kwargs[field_name] = value
            
            elif partial:
                # In partial mode, skip missing fields
                continue
            
            elif dc_field.default is not dataclasses.MISSING:
                # Field has a default value
                kwargs[field_name] = dc_field.default
            
            elif dc_field.default_factory is not dataclasses.MISSING:
                # Field has a default factory
                kwargs[field_name] = dc_field.default_factory()
            
            elif _is_optional_type(field_type):
                # Optional field without default - use None
                kwargs[field_name] = None
            
            else:
                # Required field is missing
                field_errors.append(FieldError(
                    field=full_field_path,
                    code="required",
                    message=f"Field '{field_name}' is required"
                ))
        
        if field_errors:
            raise ValidationError(
                message="Request validation failed",
                field_errors=field_errors
            )
        
        # For partial validation, return a dict with only the validated fields
        # This allows PATCH operations to work without requiring all fields
        if partial:
            return kwargs
        
        try:
            instance = schema(**kwargs)
            
            # Run post-init validation if defined
            # Note: __post_init__ is automatically called by dataclass __init__
            # If it raises an exception, we catch it here
            
            return instance
            
        except TypeError as e:
            raise ValidationError(
                message=f"Failed to construct {schema.__name__}: {e}",
                field_errors=[
                    FieldError(
                        field=field_prefix if field_prefix else "$",
                        code="construction_error",
                        message=str(e)
                    )
                ]
            )
        except ValueError as e:
            # Post-init validation failure
            raise ValidationError(
                message=f"Validation failed in {schema.__name__}: {e}",
                field_errors=[
                    FieldError(
                        field=field_prefix if field_prefix else "$",
                        code="post_init_error",
                        message=str(e)
                    )
                ]
            )
    
    def _validate_field_metadata(
        self,
        dc_field: dataclasses.Field,
        value: Any,
        field_path: str
    ) -> List[FieldError]:
        """
            Validate field value against field metadata constraints.
            
            Supports metadata keys:
            - min_length: Minimum string/list length
            - max_length: Maximum string/list length
            - min_value: Minimum numeric value
            - max_value: Maximum numeric value
            - pattern: Regex pattern for string validation
            - choices: List of allowed values
            
            Args:
                dc_field: Dataclass field definition.
                value: Value to validate.
                field_path: Full field path for error reporting.
            
            Returns:
                List of FieldError objects for any validation failures.
        """
        errors: List[FieldError] = []
        metadata = dc_field.metadata
        
        if not metadata:
            return errors
        
        # Min length validation
        if "min_length" in metadata:
            min_len = metadata["min_length"]
            if hasattr(value, "__len__") and len(value) < min_len:
                errors.append(FieldError(
                    field=field_path,
                    code="min_length",
                    message=f"Length must be at least {min_len}"
                ))
        
        # Max length validation
        if "max_length" in metadata:
            max_len = metadata["max_length"]
            if hasattr(value, "__len__") and len(value) > max_len:
                errors.append(FieldError(
                    field=field_path,
                    code="max_length",
                    message=f"Length must be at most {max_len}"
                ))
        
        # Min value validation
        if "min_value" in metadata:
            min_val = metadata["min_value"]
            if isinstance(value, (int, float)) and value < min_val:
                errors.append(FieldError(
                    field=field_path,
                    code="min_value",
                    message=f"Value must be at least {min_val}"
                ))
        
        # Max value validation
        if "max_value" in metadata:
            max_val = metadata["max_value"]
            if isinstance(value, (int, float)) and value > max_val:
                errors.append(FieldError(
                    field=field_path,
                    code="max_value",
                    message=f"Value must be at most {max_val}"
                ))
        
        # Pattern validation
        if "pattern" in metadata:
            import re
            pattern = metadata["pattern"]
            if isinstance(value, str) and not re.match(pattern, value):
                errors.append(FieldError(
                    field=field_path,
                    code="pattern",
                    message=f"Value does not match pattern: {pattern}"
                ))
        
        # Choices validation
        if "choices" in metadata:
            choices = metadata["choices"]
            if value not in choices:
                errors.append(FieldError(
                    field=field_path,
                    code="invalid_choice",
                    message=f"Value must be one of: {choices}"
                ))
        
        return errors
