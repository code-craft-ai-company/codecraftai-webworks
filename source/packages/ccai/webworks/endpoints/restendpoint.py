"""
.. module:: restendpoint
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: REST-specific endpoint class with schema and documentation metadata.

.. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

import logging

from typing import Any, Callable, Dict, List, Optional, Type, TypeVar

from ccai.webworks.endpoints.accesspolicy import AccessPolicy
from ccai.webworks.endpoints.constraints import EndpointConstraints
from ccai.webworks.endpoints.descriptor import (
    REST_ERROR_MAP_TYPES_EXTRA,
    REST_QUERY_PARAMS_EXTRA,
    REST_REQUEST_SCHEMA_TYPE_EXTRA,
    REST_RESPONSE_SCHEMA_TYPE_EXTRA,
    declare_on_class,
    EndpointDescriptor,
    mark_handler,
    record_rest_processing
)
from ccai.webworks.endpoints.doc import Doc
from ccai.webworks.endpoints.endpoint import Endpoint
from ccai.webworks.endpoints.exceptions import EndpointRegistrationError, SchemaInspectionError
from ccai.webworks.endpoints.ratelimit import RateLimit
from ccai.webworks.endpoints.typeinspection import dataclass_to_json_schema, type_to_json_schema
from ccai.webworks.security.decorators import HANDLER_POLICY_ATTR


# Module-level logger. Schema inspection wraps the underlying
# error in ``SchemaInspectionError`` so the OpenAPI generator can
# produce a clean error message — the original traceback is added
# to the journal here so the operator can pinpoint a malformed
# schema without re-running the inspection.
logger = logging.getLogger(__name__)


# Type variable for preserving function signatures in decorators
F = TypeVar("F", bound=Callable[..., Any])


class RestEndpoint(Endpoint):
    """
        Endpoint subclass with REST-specific metadata for auto-generating
        API descriptions (OpenAPI paths, verbs, payload schemas).
        
        RestEndpoint extends the base Endpoint class with additional
        attributes for request/response schemas, error mappings, and
        documentation fields. It also provides CRUD helper methods
        that pre-populate common HTTP verbs and documentation.
        
        Class Attributes:
            request_schema: Default request body schema (dataclass or Pydantic).
            response_schema: Default response body schema.
            error_map: Mapping of status codes to error schemas.
            summary: Default summary text for documentation.
            description: Default description text for documentation.
    """
    
    # REST-specific class-level defaults
    request_schema: Optional[Type] = None
    response_schema: Optional[Type] = None
    error_map: Dict[int, Type] = {}
    summary: Optional[str] = None
    description: Optional[str] = None

    @classmethod
    def attach_at(
        cls,
        leaf: Optional[str] = None,
        path: Optional[str] = None,
        methods: Optional[List[str]] = None,
        version: Optional[str] = None,
        tags: Optional[List[str]] = None,
        access_policy: Optional[AccessPolicy] = None,
        rate_limit: Optional[RateLimit] = None,
        request_schema: Optional[Type] = None,
        response_schema: Optional[Type] = None,
        error_map: Optional[Dict[int, Type]] = None,
        doc: Optional[Doc] = None,
        on_conflict: str = "error",
        query_params: Optional[Dict[str, Type]] = None,
        rest_processing: Optional[bool] = None,
        **extras
    ) -> Callable[[F], F]:
        """
            Decorator that binds a REST handler to an absolute URL location.
            
            This method extends the base Endpoint.attach_at() with REST-specific
            schema inspection. When request_schema or response_schema are provided
            (or inherited from class attributes), the decorator inspects them
            to capture JSON-schema fragments in the descriptor.
            
            :param leaf: URL leaf segment (e.g., "status" -> /status).
            :param path: Full URL path (alternative to leaf).
            :param methods: HTTP methods (defaults to class attribute).
            :param version: API version string.
            :param tags: Documentation tags.
            :param access_policy: Security policy (defaults to class attribute).
            :param rate_limit: Rate limiting config (defaults to class attribute).
            :param request_schema: Request body schema (dataclass or Pydantic).
            :param response_schema: Response body schema.
            :param error_map: Mapping of status codes to error schemas.
            :param doc: Documentation object with summary/description.
            :param on_conflict: "error" to raise on conflict, "replace" to override.
            :param query_params: The query parameters the handler reads, as a
                                 mapping of parameter name to Python type
                                 (for example ``{"page": int, "q": str}``).
                                 They are recorded for documentation; the
                                 OpenAPI generator emits one optional query
                                 parameter for each.
            :param rest_processing: Whether a handler declared with REST
                                    metadata (a request schema, a response
                                    schema or an error map, given here or
                                    inherited from the class) is served
                                    through the REST request/response
                                    processing. False for a handler that
                                    parses the body and shapes the response
                                    itself; None takes the class attribute
                                    ``rest_processing`` (True).
            :param extras: Additional kwargs stored in descriptor.extras.
            
            :returns: Decorator that returns the original function unchanged.
            
            :raises EndpointRegistrationError: If mandatory metadata missing.
            :raises SchemaInspectionError: If schema inspection fails.
        """
        merged_rest_processing = rest_processing if rest_processing is not None else cls.rest_processing

        def decorator(func: F) -> F:
            # Validate mandatory metadata
            if leaf is None and path is None:
                raise EndpointRegistrationError(
                    message="Either 'leaf' or 'path' must be provided to attach_at()",
                    endpoint=cls,
                    missing_fields=["leaf", "path"]
                )
            
            # Merge class attributes with kwargs (kwargs override)
            merged_methods = methods if methods is not None else list(cls.methods)
            merged_version = version if version is not None else cls.version
            merged_tags = tags if tags is not None else list(cls.tags)
            merged_access_policy = access_policy if access_policy is not None else cls.access_policy
            merged_rate_limit = rate_limit if rate_limit is not None else cls.rate_limit

            # Honor any AccessPolicy attached to the handler by security
            # decorators. See Endpoint.attach_at for rationale.
            handler_policy = getattr(func, HANDLER_POLICY_ATTR, None)
            if handler_policy is not None:
                if merged_access_policy is None:
                    merged_access_policy = handler_policy
                else:
                    merged_access_policy = merged_access_policy.merge_with(handler_policy)

            # Merge REST-specific attributes
            merged_request_schema = request_schema if request_schema is not None else cls.request_schema
            merged_response_schema = response_schema if response_schema is not None else cls.response_schema
            merged_error_map = error_map if error_map is not None else dict(cls.error_map)
            
            # Build or merge doc object
            merged_doc = doc
            if merged_doc is None and (cls.summary is not None or cls.description is not None):
                merged_doc = Doc(
                    summary=cls.summary,
                    description=cls.description
                )
            
            # Build constraints object
            constraints = EndpointConstraints(
                access_policy=merged_access_policy,
                rate_limit=merged_rate_limit,
                scopes=merged_access_policy.scopes if merged_access_policy else [],
                roles=merged_access_policy.roles if merged_access_policy else []
            )
            
            # Build extras dict with any additional kwargs
            extras_dict: Dict[str, Any] = dict(extras)

            # Every endpoint declared through the REST family is a REST
            # endpoint. Documentation generators select on this, so it is
            # stamped here rather than only by RestBlueprint; a subclass
            # that declares another type (the authentication blueprints
            # use "auth") keeps its own value.
            if "endpoint_type" not in extras_dict:
                extras_dict["endpoint_type"] = "rest"
            
            # Build REST-specific extras with schema inspection. The
            # inspected JSON-schema dict is what documentation exports read;
            # the schema class is kept beside it because validating a
            # request body and generating an OpenAPI component both need the
            # class, which cannot be recovered from the dict.
            rest_extras: Dict[str, Any] = {}
            
            if merged_request_schema is not None:
                rest_extras["request_schema"] = cls._inspect_rest_schema(merged_request_schema)
                rest_extras[REST_REQUEST_SCHEMA_TYPE_EXTRA] = merged_request_schema
            
            if merged_response_schema is not None:
                rest_extras["response_schema"] = cls._inspect_rest_schema(merged_response_schema)
                rest_extras[REST_RESPONSE_SCHEMA_TYPE_EXTRA] = merged_response_schema
            
            if merged_error_map:
                rest_extras["error_map"] = {
                    code: cls._inspect_rest_schema(schema)
                    for code, schema in merged_error_map.items()
                }
                rest_extras[REST_ERROR_MAP_TYPES_EXTRA] = dict(merged_error_map)

            if query_params is not None and len(query_params) > 0:
                rest_extras[REST_QUERY_PARAMS_EXTRA] = dict(query_params)

            # Whether the route is served through the REST processing (the
            # default) or opted out of it.
            record_rest_processing(rest_extras, merged_rest_processing)
            
            if rest_extras:
                extras_dict["rest"] = rest_extras
            
            # Store serializers in extras if class has them
            if cls.serializers:
                extras_dict["serializers"] = dict(cls.serializers)
            
            # Create the descriptor
            descriptor = EndpointDescriptor(
                handler=func,
                module=func.__module__,
                leaf=leaf,
                path=path,
                methods=merged_methods,
                version=merged_version,
                tags=merged_tags,
                constraints=constraints,
                doc=merged_doc,
                extras=extras_dict
            )
            
            # Mark the handler; a registry collects it later. Record it on
            # the declaring class too, so `cls.register()` and `add_crud`
            # find handlers that are free functions. This decorator builds
            # its own descriptor rather than delegating to
            # `Endpoint.attach_at`, so it has to do both halves itself.
            descriptor.on_conflict = on_conflict
            mark_handler(func, descriptor)
            declare_on_class(cls, descriptor)

            # Return the original function unchanged
            return func
        
        return decorator

    @classmethod
    def _inspect_rest_schema(cls, schema: Type) -> Dict[str, Any]:
        """
            Inspect a schema type and extract JSON schema information.
            
            This method inspects Pydantic models (via model_json_schema) and
            dataclasses (via __dataclass_fields__) to capture JSON-schema
            fragments for documentation generation.
            
            :param schema: The schema type to inspect.
            
            :returns: Dictionary containing JSON schema information.
            
            :raises SchemaInspectionError: If schema cannot be inspected.
        """
        # Try Pydantic model first (v2 API)
        if hasattr(schema, "model_json_schema"):
            try:
                return schema.model_json_schema()
            except Exception as err:
                logger.exception(
                    "Schema inspection: model_json_schema() failed for %s",
                    getattr(schema, "__name__", schema),
                )
                raise SchemaInspectionError(
                    schema=schema,
                    reason=f"Pydantic model_json_schema() failed: {err}"
                ) from err

        # Try Pydantic v1 API
        if hasattr(schema, "schema"):
            try:
                return schema.schema()
            except Exception as err:
                logger.exception(
                    "Schema inspection: schema() failed for %s",
                    getattr(schema, "__name__", schema),
                )
                raise SchemaInspectionError(
                    schema=schema,
                    reason=f"Pydantic schema() failed: {err}"
                ) from err

        # Try dataclass
        if hasattr(schema, "__dataclass_fields__"):
            try:
                return cls._dataclass_to_json_schema(schema)
            except Exception as err:
                logger.exception(
                    "Schema inspection: dataclass inspection failed for %s",
                    getattr(schema, "__name__", schema),
                )
                raise SchemaInspectionError(
                    schema=schema,
                    reason=f"Dataclass inspection failed: {err}"
                ) from err
        
        # Return a reference schema for unknown types
        return {"$ref": f"#/components/schemas/{schema.__name__}"}

    @classmethod
    def _dataclass_to_json_schema(cls, schema: Type) -> Dict[str, Any]:
        """
            Convert a dataclass to a JSON schema representation.

            Field annotations are resolved first, so postponed annotations
            (``from __future__ import annotations``), PEP 604 unions and
            nested dataclasses are described by their real types.

            :param schema: The dataclass type to convert.

            :returns: Dictionary containing JSON schema information.
        """
        rtnval = dataclass_to_json_schema(schema, include_title=True)
        return rtnval

    @classmethod
    def _python_type_to_json_schema(cls, field_type: Any) -> Dict[str, Any]:
        """
            Convert a Python type to a JSON schema type.

            :param field_type: The Python type to convert.

            :returns: Dictionary containing JSON schema type information.
        """
        rtnval = type_to_json_schema(field_type)
        return rtnval

    @classmethod
    def read(
        cls,
        leaf: Optional[str] = None,
        path: Optional[str] = None,
        version: Optional[str] = None,
        tags: Optional[List[str]] = None,
        access_policy: Optional[AccessPolicy] = None,
        rate_limit: Optional[RateLimit] = None,
        response_schema: Optional[Type] = None,
        error_map: Optional[Dict[int, Type]] = None,
        doc: Optional[Doc] = None,
        on_conflict: str = "error",
        rest_processing: Optional[bool] = None,
        **extras
    ) -> Callable[[F], F]:
        """
            Helper decorator for GET endpoints with pre-populated documentation.
            
            This method is a convenience wrapper around attach_at() that
            pre-sets the HTTP method to GET and provides sensible defaults
            for read operations.
            
            :param leaf: URL leaf segment.
            :param path: Full URL path.
            :param version: API version string.
            :param tags: Documentation tags.
            :param access_policy: Security policy.
            :param rate_limit: Rate limiting config.
            :param response_schema: Response body schema.
            :param error_map: Mapping of status codes to error schemas.
            :param doc: Documentation object.
            :param on_conflict: Conflict handling strategy.
            :param rest_processing: False to opt the handler out of the REST
                                    processing (see :meth:`attach_at`).
            :param extras: Additional kwargs.
            
            :returns: Decorator that returns the original function unchanged.
        """
        return cls.attach_at(
            leaf=leaf,
            path=path,
            methods=["GET"],
            version=version,
            tags=tags,
            access_policy=access_policy,
            rate_limit=rate_limit,
            request_schema=None,
            response_schema=response_schema,
            error_map=error_map,
            doc=doc,
            on_conflict=on_conflict,
            rest_processing=rest_processing,
            **extras
        )

    @classmethod
    def create(
        cls,
        leaf: Optional[str] = None,
        path: Optional[str] = None,
        version: Optional[str] = None,
        tags: Optional[List[str]] = None,
        access_policy: Optional[AccessPolicy] = None,
        rate_limit: Optional[RateLimit] = None,
        request_schema: Optional[Type] = None,
        response_schema: Optional[Type] = None,
        error_map: Optional[Dict[int, Type]] = None,
        doc: Optional[Doc] = None,
        on_conflict: str = "error",
        rest_processing: Optional[bool] = None,
        **extras
    ) -> Callable[[F], F]:
        """
            Helper decorator for POST endpoints with pre-populated documentation.
            
            This method is a convenience wrapper around attach_at() that
            pre-sets the HTTP method to POST and provides sensible defaults
            for create operations.
            
            :param leaf: URL leaf segment.
            :param path: Full URL path.
            :param version: API version string.
            :param tags: Documentation tags.
            :param access_policy: Security policy.
            :param rate_limit: Rate limiting config.
            :param request_schema: Request body schema.
            :param response_schema: Response body schema.
            :param error_map: Mapping of status codes to error schemas.
            :param doc: Documentation object.
            :param on_conflict: Conflict handling strategy.
            :param rest_processing: False to opt the handler out of the REST
                                    processing (see :meth:`attach_at`).
            :param extras: Additional kwargs.
            
            :returns: Decorator that returns the original function unchanged.
        """
        return cls.attach_at(
            leaf=leaf,
            path=path,
            methods=["POST"],
            version=version,
            tags=tags,
            access_policy=access_policy,
            rate_limit=rate_limit,
            request_schema=request_schema,
            response_schema=response_schema,
            error_map=error_map,
            doc=doc,
            on_conflict=on_conflict,
            rest_processing=rest_processing,
            **extras
        )

    @classmethod
    def update(
        cls,
        leaf: Optional[str] = None,
        path: Optional[str] = None,
        version: Optional[str] = None,
        tags: Optional[List[str]] = None,
        access_policy: Optional[AccessPolicy] = None,
        rate_limit: Optional[RateLimit] = None,
        request_schema: Optional[Type] = None,
        response_schema: Optional[Type] = None,
        error_map: Optional[Dict[int, Type]] = None,
        doc: Optional[Doc] = None,
        on_conflict: str = "error",
        rest_processing: Optional[bool] = None,
        **extras
    ) -> Callable[[F], F]:
        """
            Helper decorator for PUT/PATCH endpoints with pre-populated documentation.
            
            This method is a convenience wrapper around attach_at() that
            pre-sets the HTTP methods to PUT and PATCH and provides sensible
            defaults for update operations.
            
            :param leaf: URL leaf segment.
            :param path: Full URL path.
            :param version: API version string.
            :param tags: Documentation tags.
            :param access_policy: Security policy.
            :param rate_limit: Rate limiting config.
            :param request_schema: Request body schema.
            :param response_schema: Response body schema.
            :param error_map: Mapping of status codes to error schemas.
            :param doc: Documentation object.
            :param on_conflict: Conflict handling strategy.
            :param rest_processing: False to opt the handler out of the REST
                                    processing (see :meth:`attach_at`).
            :param extras: Additional kwargs.
            
            :returns: Decorator that returns the original function unchanged.
        """
        return cls.attach_at(
            leaf=leaf,
            path=path,
            methods=["PUT", "PATCH"],
            version=version,
            tags=tags,
            access_policy=access_policy,
            rate_limit=rate_limit,
            request_schema=request_schema,
            response_schema=response_schema,
            error_map=error_map,
            doc=doc,
            on_conflict=on_conflict,
            rest_processing=rest_processing,
            **extras
        )

    @classmethod
    def delete(
        cls,
        leaf: Optional[str] = None,
        path: Optional[str] = None,
        version: Optional[str] = None,
        tags: Optional[List[str]] = None,
        access_policy: Optional[AccessPolicy] = None,
        rate_limit: Optional[RateLimit] = None,
        response_schema: Optional[Type] = None,
        error_map: Optional[Dict[int, Type]] = None,
        doc: Optional[Doc] = None,
        on_conflict: str = "error",
        rest_processing: Optional[bool] = None,
        **extras
    ) -> Callable[[F], F]:
        """
            Helper decorator for DELETE endpoints with pre-populated documentation.
            
            This method is a convenience wrapper around attach_at() that
            pre-sets the HTTP method to DELETE and provides sensible defaults
            for delete operations.
            
            :param leaf: URL leaf segment.
            :param path: Full URL path.
            :param version: API version string.
            :param tags: Documentation tags.
            :param access_policy: Security policy.
            :param rate_limit: Rate limiting config.
            :param response_schema: Response body schema.
            :param error_map: Mapping of status codes to error schemas.
            :param doc: Documentation object.
            :param on_conflict: Conflict handling strategy.
            :param rest_processing: False to opt the handler out of the REST
                                    processing (see :meth:`attach_at`).
            :param extras: Additional kwargs.
            
            :returns: Decorator that returns the original function unchanged.
        """
        return cls.attach_at(
            leaf=leaf,
            path=path,
            methods=["DELETE"],
            version=version,
            tags=tags,
            access_policy=access_policy,
            rate_limit=rate_limit,
            request_schema=None,
            response_schema=response_schema,
            error_map=error_map,
            doc=doc,
            on_conflict=on_conflict,
            rest_processing=rest_processing,
            **extras
        )
