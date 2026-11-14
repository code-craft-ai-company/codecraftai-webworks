"""
.. module:: ccai.webworks.endpoints.rest.validation
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Validation infrastructure for REST API support.
               Provides schema validation for dataclasses and Pydantic models
               with support for partial updates and nested validation.

.. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

import dataclasses
import enum
import functools
import logging
import typing

from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation
from typing import Annotated, Any, Dict, List, Tuple, Type, get_origin, get_args
from uuid import UUID

from ccai.webworks.endpoints.rest.exceptions import ValidationError
from ccai.webworks.endpoints.rest.models import FieldError
from ccai.webworks.endpoints.typeinspection import (
    is_optional_type,
    is_union_type,
    non_none_members,
    resolve_field_types,
    unwrap_optional,
)


# Module-level logger. ``get_type_hints`` can fail on schemas that
# reference forward strings whose modules failed to import — falling
# back to an empty dict keeps validation moving but the operator
# wants the breadcrumb so a chronically-broken schema is visible.
logger = logging.getLogger(__name__)


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


def _skip_before_model_validator(cls, data: Any) -> Any:
    """Stand-in for a ``mode="before"`` model validator in a partial model."""
    return data


def _skip_after_model_validator(self) -> Any:
    """Stand-in for a ``mode="after"`` model validator in a partial model."""
    return self


def _skip_wrap_model_validator(cls, data: Any, handler: Any) -> Any:
    """Stand-in for a ``mode="wrap"`` model validator in a partial model."""
    return handler(data)


@functools.lru_cache(maxsize=256)
def _partial_pydantic_model(schema: Type) -> Type:
    """
        Derive the model a PATCH body is validated with from a Pydantic model.

        The derived model is a subclass of ``schema`` in which no field is
        required: a required field gets a default of None that is never
        validated or returned. Everything that checks one field is inherited
        and runs on each field the body sends: its type, its ``Field()``
        constraints and alias, its field validators, and the model's policy
        for unknown keys (``extra``). Model validators are replaced, by name,
        with ones that do nothing: they check the whole resource, which a
        partial body is not (validate it after merging, in
        ``partial_update()``, or name a ``partial_update_schema``).

        Args:
            schema: Pydantic model class.

        Returns:
            The derived model class, built once per schema.
    """
    from pydantic import Field, create_model, model_validator

    overrides: Dict[str, Any] = {}
    for field_name, field_info in schema.model_fields.items():
        if field_info.is_required():
            # The original FieldInfo in Annotated keeps the constraints and
            # alias; the assigned Field only makes the field optional.
            overrides[field_name] = (
                Annotated[field_info.annotation, field_info],
                Field(default=None, validate_default=False),
            )

    stand_ins = {
        "before": classmethod(_skip_before_model_validator),
        "after": _skip_after_model_validator,
        "wrap": classmethod(_skip_wrap_model_validator),
    }
    validators: Dict[str, Any] = {}
    decorators = getattr(schema, "__pydantic_decorators__", None)
    if decorators is not None:
        for validator_name, decorator in decorators.model_validators.items():
            mode = decorator.info.mode
            validators[validator_name] = model_validator(mode=mode)(stand_ins[mode])

    partial_model = create_model(
        f"{schema.__name__}Partial",
        __base__=schema,
        __module__=schema.__module__,
        __validators__=validators,
        **overrides,
    )
    return partial_model


def _is_optional_type(field_type: Type) -> bool:
    """Check if a type is Optional (a union with None, in either spelling)."""
    return is_optional_type(field_type)


def _get_inner_type(field_type: Type) -> Type:
    """Get the inner type from Optional[T] -> T."""
    return unwrap_optional(field_type)


# Names used in error messages for the JSON value kinds.
_JSON_TYPE_NAMES: Dict[type, str] = {
    str: "string",
    bool: "boolean",
    int: "integer",
    float: "number",
    list: "list",
    dict: "object",
    type(None): "null",
}


def _json_type_name(value: Any) -> str:
    """Name the JSON kind of a value for an error message."""
    rtnval = _JSON_TYPE_NAMES.get(type(value), type(value).__name__)
    return rtnval


class Validator:
    """
        Schema validator supporting dataclasses and Pydantic models.
        
        This validator validates incoming data against schema definitions,
        supporting both Pydantic models and dataclasses. It provides:
        - Full validation for create/update operations
        - Partial validation for PATCH operations (partial=True)
        - Nested schema validation with field path tracking
        - Detailed field-level error reporting

        Args:
            reject_unknown_fields: If True, a key in the data that is not a
                                   field of a dataclass schema is reported as
                                   an ``unknown_field`` error. By default such
                                   keys are ignored, which is also what a
                                   Pydantic model does unless configured
                                   otherwise.
    """

    def __init__(self, reject_unknown_fields: bool = False):
        """
            Initialize a Validator.

            Args:
                reject_unknown_fields: If True, report keys that are not
                                       fields of a dataclass schema.
        """
        self.reject_unknown_fields = reject_unknown_fields
    
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
                Validated and coerced data as a schema instance; with
                partial=True, a dict of the validated fields present in
                data (by field name).
            
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
            validates with a derived model in which no field is required (see
            _validate_pydantic_partial).
            
            Args:
                data: Data to validate (should be a dict).
                schema: Pydantic model class.
                partial: If True, all required fields become optional.
            
            Returns:
                Validated Pydantic model instance, or for partial=True a dict
                of the validated fields present in data.
            
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
                return self._validate_pydantic_partial(data, schema)
            else:
                return schema.model_validate(data)
                
        except PydanticValidationError as e:
            field_errors = self._convert_pydantic_errors(e)
            raise ValidationError(
                message="Request validation failed",
                field_errors=field_errors
            )
    
    def _validate_pydantic_partial(self, data: Dict[str, Any], schema: Type) -> Dict[str, Any]:
        """
            Validate partial data against a Pydantic model.

            Each field present in the data is validated as a full request
            would validate it -- type, ``Field()`` constraints, field
            validators, a nested model in full -- and a field that is absent
            is not required. Unknown keys follow the model's ``extra``
            setting. Model validators do not run; they check a whole
            resource.

            Args:
                data: Partial data to validate.
                schema: Pydantic model class.

            Returns:
                Dict of the validated values of the fields present in the
                data, by field name, in the model's field order; with
                ``extra="allow"`` the unknown keys follow.

            Raises:
                pydantic.ValidationError: On validation errors for provided
                                          fields (converted by the caller).
        """
        partial_model = _partial_pydantic_model(schema)
        instance = partial_model.model_validate(data)

        fields_set = instance.model_fields_set
        validated: Dict[str, Any] = {}
        for field_name in partial_model.model_fields:
            if field_name in fields_set:
                validated[field_name] = getattr(instance, field_name)

        extra = instance.model_extra
        if extra:
            validated.update(extra)

        return validated
    
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
        
        # Resolve the annotations to real types, so postponed annotations
        # and PEP 604 unions are checked as what they mean
        type_hints = resolve_field_types(schema)

        if self.reject_unknown_fields:
            known_names = [dc_field.name for dc_field in fields]
            for key in data:
                if key not in known_names:
                    unknown_path = f"{field_prefix}.{key}" if field_prefix else str(key)
                    field_errors.append(FieldError(
                        field=unknown_path,
                        code="unknown_field",
                        message=f"Field '{key}' is not defined on {schema.__name__}"
                    ))
        
        for dc_field in fields:
            field_name = dc_field.name
            full_field_path = f"{field_prefix}.{field_name}" if field_prefix else field_name
            field_type = type_hints.get(field_name, dc_field.type)
            
            if field_name in data:
                # Field is present in data
                value = data[field_name]
                
                # Handle None value
                if value is None:
                    if _is_optional_type(field_type) or field_type is Any:
                        kwargs[field_name] = None
                        continue
                    else:
                        field_errors.append(FieldError(
                            field=full_field_path,
                            code="type_error",
                            message=f"Field '{field_name}' cannot be null"
                        ))
                        continue
                
                # Check the value against the field's type, converting it
                # where the JSON form differs from the Python one (nested
                # schemas, dates, UUIDs, enums and so on)
                value, value_errors = self._check_value(value, field_type, full_field_path)
                if len(value_errors) > 0:
                    field_errors.extend(value_errors)
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
    
    def _check_value(
        self,
        value: Any,
        field_type: Any,
        field_path: str
    ) -> Tuple[Any, List[FieldError]]:
        """
            Check a value against the type a field declares.

            JSON has fewer types than Python, so a matching value is also
            converted to the Python form the schema asks for: an object to a
            nested dataclass or Pydantic model, ISO 8601 text to a
            ``datetime``/``date``/``time``, text to a ``UUID`` or ``Decimal``,
            a value to its ``Enum`` member, a whole number to a ``float`` and
            a list to a ``set`` or ``tuple``. Values are never converted
            between unrelated kinds: the text ``"5"`` is not an integer and
            ``true`` is not a number.

            Elements of ``List[T]`` and values of ``Dict[K, V]`` are checked
            the same way, each reported under its own path
            (``tags.2``, ``limits.daily``).

            A type this method has no rule for -- an unresolved string
            annotation, a type variable, an arbitrary class -- accepts any
            value unchanged.

            Args:
                value: The value from the request data. Not None; a null is
                       handled by the caller, which knows the field name.
                field_type: The resolved type of the field.
                field_path: Full field path for error reporting.

            Returns:
                Tuple of (value, errors). When errors is empty the value is
                the checked, converted value; otherwise it is the input.
        """
        if field_type is Any or isinstance(field_type, (str, typing.TypeVar)):
            return value, []

        if is_union_type(field_type):
            return self._check_union_value(value, field_type, field_path)

        origin = get_origin(field_type)
        args = get_args(field_type)

        if origin is typing.Literal:
            if value in args:
                return value, []
            return value, [FieldError(
                field=field_path,
                code="invalid_choice",
                message=f"Value must be one of: {list(args)}"
            )]

        if field_type in (list, set, frozenset, tuple) or origin in (list, set, frozenset, tuple):
            return self._check_sequence_value(value, field_type, field_path)

        if field_type is dict or origin is dict:
            return self._check_mapping_value(value, field_type, field_path)

        if origin is not None:
            # Some other generic (Callable, a user generic); no rule for it.
            return value, []

        if _is_dataclass_type(field_type):
            try:
                validated = self._validate_dataclass(
                    value,
                    field_type,
                    partial=False,  # Nested objects are fully validated
                    field_prefix=field_path
                )
            except ValidationError as e:
                return value, list(e.field_errors)
            return validated, []

        if _is_pydantic_model_type(field_type):
            try:
                validated = self._validate_pydantic(value, field_type, partial=False)
            except ValidationError as e:
                # Prefix field errors with current field path
                prefixed_errors: List[FieldError] = []
                for fe in e.field_errors:
                    prefixed_field = f"{field_path}.{fe.field}" if fe.field != "$" else field_path
                    prefixed_errors.append(FieldError(
                        field=prefixed_field,
                        code=fe.code,
                        message=fe.message
                    ))
                return value, prefixed_errors
            return validated, []

        if isinstance(field_type, type):
            return self._check_scalar_value(value, field_type, field_path)

        return value, []

    def _check_union_value(
        self,
        value: Any,
        field_type: Any,
        field_path: str
    ) -> Tuple[Any, List[FieldError]]:
        """
            Check a value against a union: it must satisfy one member.

            Members are tried in the order they are written and the first
            one the value satisfies wins.

            Args:
                value: The value from the request data (not None).
                field_type: The union type.
                field_path: Full field path for error reporting.

            Returns:
                Tuple of (value, errors) as for :meth:`_check_value`.
        """
        members = non_none_members(field_type)
        if len(members) == 0:
            return value, []

        first_errors: List[FieldError] = []
        for member in members:
            checked, member_errors = self._check_value(value, member, field_path)
            if len(member_errors) == 0:
                return checked, []
            if len(first_errors) == 0:
                first_errors = member_errors

        if len(members) == 1:
            # Optional[T]: the errors of T are the useful ones
            return value, first_errors

        member_names = ", ".join(getattr(member, "__name__", str(member)) for member in members)
        return value, [FieldError(
            field=field_path,
            code="type_error",
            message=f"Expected one of ({member_names}), got {_json_type_name(value)}"
        )]

    def _check_sequence_value(
        self,
        value: Any,
        field_type: Any,
        field_path: str
    ) -> Tuple[Any, List[FieldError]]:
        """
            Check a value against a list, set, frozenset or tuple type,
            including the type of its elements when one is declared.

            Args:
                value: The value from the request data (not None).
                field_type: The sequence type, bare or parameterised.
                field_path: Full field path for error reporting.

            Returns:
                Tuple of (value, errors) as for :meth:`_check_value`.
        """
        if not isinstance(value, list):
            return value, [FieldError(
                field=field_path,
                code="type_error",
                message=f"Expected list, got {type(value).__name__}"
            )]

        origin = get_origin(field_type)
        container = origin if origin is not None else field_type
        args = get_args(field_type)

        item_types: List[Any] = []
        if container is tuple and len(args) > 0 and not (len(args) == 2 and args[1] is Ellipsis):
            # A fixed-shape tuple: one type per position
            if len(args) != len(value):
                return value, [FieldError(
                    field=field_path,
                    code="type_error",
                    message=f"Expected {len(args)} items, got {len(value)}"
                )]
            item_types = list(args)
        elif len(args) > 0:
            item_types = [args[0]] * len(value)
        else:
            item_types = [Any] * len(value)

        errors: List[FieldError] = []
        checked_items: List[Any] = []
        for index, item in enumerate(value):
            item_path = f"{field_path}.{index}"
            item_type = item_types[index]
            if item is None:
                if item_type is Any or _is_optional_type(item_type):
                    checked_items.append(None)
                else:
                    errors.append(FieldError(
                        field=item_path,
                        code="type_error",
                        message="Item cannot be null"
                    ))
                continue
            checked_item, item_errors = self._check_value(item, item_type, item_path)
            if len(item_errors) > 0:
                errors.extend(item_errors)
                continue
            checked_items.append(checked_item)

        if len(errors) > 0:
            return value, errors

        if container is list:
            return checked_items, []

        try:
            converted = container(checked_items)
        except TypeError:
            # Unhashable items for a set
            return value, [FieldError(
                field=field_path,
                code="type_error",
                message=f"Items cannot be collected into a {container.__name__}"
            )]

        return converted, []

    def _check_mapping_value(
        self,
        value: Any,
        field_type: Any,
        field_path: str
    ) -> Tuple[Any, List[FieldError]]:
        """
            Check a value against a dict type, including the type of its
            values when one is declared. Keys are left as the strings JSON
            delivers them as.

            Args:
                value: The value from the request data (not None).
                field_type: The dict type, bare or parameterised.
                field_path: Full field path for error reporting.

            Returns:
                Tuple of (value, errors) as for :meth:`_check_value`.
        """
        if not isinstance(value, dict):
            return value, [FieldError(
                field=field_path,
                code="type_error",
                message=f"Expected object, got {type(value).__name__}"
            )]

        args = get_args(field_type)
        if len(args) != 2 or args[1] is Any:
            return value, []

        value_type = args[1]
        errors: List[FieldError] = []
        checked: Dict[Any, Any] = {}
        for key, item in value.items():
            item_path = f"{field_path}.{key}"
            if item is None:
                if _is_optional_type(value_type):
                    checked[key] = None
                else:
                    errors.append(FieldError(
                        field=item_path,
                        code="type_error",
                        message="Value cannot be null"
                    ))
                continue
            checked_item, item_errors = self._check_value(item, value_type, item_path)
            if len(item_errors) > 0:
                errors.extend(item_errors)
                continue
            checked[key] = checked_item

        if len(errors) > 0:
            return value, errors

        return checked, []

    def _check_scalar_value(
        self,
        value: Any,
        field_type: type,
        field_path: str
    ) -> Tuple[Any, List[FieldError]]:
        """
            Check a value against a plain class: a JSON scalar type, one of
            the types JSON carries as text (dates, UUID, Decimal), an enum,
            or any other class.

            Args:
                value: The value from the request data (not None).
                field_type: The class the field declares.
                field_path: Full field path for error reporting.

            Returns:
                Tuple of (value, errors) as for :meth:`_check_value`.
        """
        def mismatch(expected: str) -> Tuple[Any, List[FieldError]]:
            return value, [FieldError(
                field=field_path,
                code="type_error",
                message=f"Expected {expected}, got {_json_type_name(value)}"
            )]

        if issubclass(field_type, enum.Enum):
            try:
                return field_type(value), []
            except (ValueError, TypeError):
                choices = [member.value for member in field_type]
                return value, [FieldError(
                    field=field_path,
                    code="invalid_choice",
                    message=f"Value must be one of: {choices}"
                )]

        if field_type is bool:
            if isinstance(value, bool):
                return value, []
            return mismatch("boolean")

        if field_type is int:
            # bool is a subclass of int, but true/false is not a number
            if isinstance(value, bool):
                return mismatch("integer")
            if isinstance(value, int):
                return value, []
            if isinstance(value, float) and value.is_integer():
                return int(value), []
            return mismatch("integer")

        if field_type is float:
            if isinstance(value, bool):
                return mismatch("number")
            if isinstance(value, (int, float)):
                return float(value), []
            return mismatch("number")

        if field_type is str:
            if isinstance(value, str):
                return value, []
            return mismatch("string")

        if field_type is bytes:
            if isinstance(value, str):
                return value.encode("utf-8"), []
            return mismatch("string")

        if field_type in (datetime, date, time):
            if isinstance(value, field_type) and type(value) is field_type:
                return value, []
            if not isinstance(value, str):
                return mismatch("ISO 8601 string")
            try:
                return field_type.fromisoformat(value), []
            except ValueError:
                return value, [FieldError(
                    field=field_path,
                    code="type_error",
                    message=f"Expected an ISO 8601 {field_type.__name__}, got '{value}'"
                )]

        if field_type is UUID:
            if isinstance(value, UUID):
                return value, []
            if not isinstance(value, str):
                return mismatch("UUID string")
            try:
                return UUID(value), []
            except ValueError:
                return value, [FieldError(
                    field=field_path,
                    code="type_error",
                    message=f"Expected a UUID, got '{value}'"
                )]

        if field_type is Decimal:
            if isinstance(value, bool) or not isinstance(value, (str, int, float)):
                return mismatch("decimal number")
            try:
                return Decimal(str(value)), []
            except InvalidOperation:
                return value, [FieldError(
                    field=field_path,
                    code="type_error",
                    message=f"Expected a decimal number, got '{value}'"
                )]

        # Any other class: there is no JSON form to check it against
        return value, []

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
