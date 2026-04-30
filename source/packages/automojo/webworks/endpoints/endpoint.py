"""
.. module:: endpoint
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Base endpoint class for declarative HTTP endpoint definition.

.. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

import dataclasses
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar

from automojo.webworks.endpoints.accesspolicy import AccessPolicy
from automojo.webworks.endpoints.constraints import EndpointConstraints
from automojo.webworks.endpoints.descriptor import EndpointDescriptor
from automojo.webworks.endpoints.doc import Doc
from automojo.webworks.endpoints.exceptions import EndpointRegistrationError
from automojo.webworks.endpoints.ratelimit import RateLimit
from automojo.webworks.endpoints.registry import EndpointConflictError, EndpointRegistry
from automojo.webworks.security.decorators import HANDLER_POLICY_ATTR


# Type variable for preserving function signatures in decorators
F = TypeVar("F", bound=Callable[..., Any])


class Endpoint:
    """
        Base class providing a reusable container for endpoint constraints
        and metadata. Supports both direct attachment via attach_at() and
        hierarchical composition via attach_child().
        
        Subclasses can override class-level attributes to define default
        constraints that apply to all handlers decorated with attach_at().
        Explicit kwargs passed to attach_at() override class attributes.
        
        Class Attributes:
            access_policy: Default access policy for all handlers.
            rate_limit: Default rate limit for all handlers.
            methods: Default HTTP methods (defaults to ["GET"]).
            version: Default API version string.
            tags: Default documentation tags.
            serializers: Default serializer configuration.
    """
    
    # Class-level defaults that subclasses can override
    access_policy: Optional[AccessPolicy] = None
    rate_limit: Optional[RateLimit] = None
    methods: List[str] = ["GET"]
    version: Optional[str] = None
    tags: List[str] = []
    serializers: Dict[str, Any] = {}
    
    # Blueprint-related attributes (used by attach_child)
    base_path: Optional[str] = None
    base_leaf: Optional[str] = None

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
        **extras
    ) -> Callable[[F], F]:
        """
            Decorator that binds a handler to an absolute URL location.
            
            This classmethod returns a decorator that registers the handler
            with the EndpointRegistry. The decorator returns the original
            function unchanged, allowing decorator stacking to work correctly.
            
            Class attributes are used as defaults for any parameters not
            explicitly provided. Explicit kwargs override class attributes.
            
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
            :param extras: Additional kwargs stored in descriptor.extras.
            
            :returns: Decorator that returns the original function unchanged.
            
            :raises EndpointRegistrationError: If mandatory metadata missing.
            :raises EndpointConflictError: If path+method conflicts with existing.
        """
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
            # decorators (require_auth, require_roles, require_scopes,
            # public_endpoint). The decorator's policy is merged into the
            # one already resolved from explicit kwargs / class attributes
            # so decorator-supplied roles and scopes accumulate via
            # AccessPolicy.merge_with rather than being silently dropped.
            handler_policy = getattr(func, HANDLER_POLICY_ATTR, None)
            if handler_policy is not None:
                if merged_access_policy is None:
                    merged_access_policy = handler_policy
                else:
                    merged_access_policy = merged_access_policy.merge_with(handler_policy)

            # Build constraints object
            constraints = EndpointConstraints(
                access_policy=merged_access_policy,
                rate_limit=merged_rate_limit,
                scopes=merged_access_policy.scopes if merged_access_policy else [],
                roles=merged_access_policy.roles if merged_access_policy else []
            )
            
            # Build extras dict with any additional kwargs
            extras_dict: Dict[str, Any] = dict(extras)
            
            # Add REST-specific extras if provided
            if request_schema is not None or response_schema is not None or error_map is not None:
                rest_extras: Dict[str, Any] = {}
                if request_schema is not None:
                    rest_extras["request_schema"] = cls._inspect_schema(request_schema)
                if response_schema is not None:
                    rest_extras["response_schema"] = cls._inspect_schema(response_schema)
                if error_map is not None:
                    rest_extras["error_map"] = {
                        code: cls._inspect_schema(schema)
                        for code, schema in error_map.items()
                    }
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
                doc=doc,
                extras=extras_dict
            )
            
            # Register with the registry
            EndpointRegistry.register(descriptor, on_conflict=on_conflict)
            
            # Return the original function unchanged
            return func
        
        return decorator

    @classmethod
    def attach_child(
        cls,
        child_endpoint: Type["Endpoint"],
        leaf: Optional[str] = None,
        path: Optional[str] = None,
        methods: Optional[List[str]] = None,
        version: Optional[str] = None,
        tags: Optional[List[str]] = None,
        access_policy: Optional[AccessPolicy] = None,
        rate_limit: Optional[RateLimit] = None,
        replace_scopes: bool = False,
        replace_roles: bool = False,
        merge_tags: bool = False,
        **kwargs
    ) -> EndpointDescriptor:
        """
            Attach a child endpoint relative to this endpoint's base path.
            
            This method creates a descriptor for the child endpoint with
            paths computed relative to the parent's base_path/base_leaf.
            Constraints are merged following inheritance rules.
            
            :param child_endpoint: The child endpoint class to attach.
            :param leaf: Override for child's leaf (relative to parent base).
            :param path: Override for child's path (relative to parent base).
            :param methods: Override for child's methods.
            :param version: Override for child's version.
            :param tags: Override for child's tags.
            :param access_policy: Override for child's access policy.
            :param rate_limit: Override for child's rate limit.
            :param replace_scopes: If True, child scopes replace parent scopes.
            :param replace_roles: If True, child roles replace parent roles.
            :param merge_tags: If True, parent tags are appended to child tags.
            :param kwargs: Additional overrides for child descriptor.
            
            :returns: The merged EndpointDescriptor for the child.
        """
        # Determine child's leaf/path
        child_leaf = leaf if leaf is not None else child_endpoint.base_leaf
        child_path = path if path is not None else child_endpoint.base_path
        
        # Compute the final path relative to parent's base
        final_path = cls._compute_child_path(child_leaf, child_path)
        
        # Determine final leaf (None if we computed a full path)
        final_leaf = None
        if final_path is None:
            # No path computed, use leaf directly
            final_leaf = child_leaf
        
        # Merge methods
        merged_methods = methods if methods is not None else list(child_endpoint.methods)
        
        # Merge version (child overrides parent)
        merged_version = version if version is not None else child_endpoint.version
        if merged_version is None:
            merged_version = cls.version
        
        # Merge tags
        child_tags = tags if tags is not None else list(child_endpoint.tags)
        if merge_tags:
            # Parent tags appended to child tags
            merged_tags = list(child_tags)
            for tag in cls.tags:
                if tag not in merged_tags:
                    merged_tags.append(tag)
        else:
            # Child tags win (default behavior)
            merged_tags = child_tags if child_tags else list(cls.tags)
        
        # Build parent constraints
        parent_constraints = EndpointConstraints(
            access_policy=cls.access_policy,
            rate_limit=cls.rate_limit,
            scopes=cls.access_policy.scopes if cls.access_policy else [],
            roles=cls.access_policy.roles if cls.access_policy else []
        )
        
        # Build child constraints
        child_access_policy = access_policy if access_policy is not None else child_endpoint.access_policy
        child_rate_limit = rate_limit if rate_limit is not None else child_endpoint.rate_limit
        child_constraints = EndpointConstraints(
            access_policy=child_access_policy,
            rate_limit=child_rate_limit,
            scopes=child_access_policy.scopes if child_access_policy else [],
            roles=child_access_policy.roles if child_access_policy else []
        )
        
        # Merge constraints following inheritance rules
        merged_constraints = EndpointConstraints.merge(
            parent_constraints,
            child_constraints,
            replace_scopes=replace_scopes,
            replace_roles=replace_roles
        )
        
        # Build extras from kwargs
        extras_dict: Dict[str, Any] = dict(kwargs)
        
        # Store serializers if child has them
        if child_endpoint.serializers:
            extras_dict["serializers"] = dict(child_endpoint.serializers)
        
        # Create a placeholder handler for the child descriptor
        # The actual handler will be set when the child is decorated
        def placeholder_handler() -> None:
            pass
        
        placeholder_handler.__name__ = f"{child_endpoint.__name__}_child"
        placeholder_handler.__module__ = child_endpoint.__module__
        
        # Create the descriptor
        descriptor = EndpointDescriptor(
            handler=placeholder_handler,
            module=child_endpoint.__module__,
            leaf=final_leaf,
            path=final_path,
            methods=merged_methods,
            version=merged_version,
            tags=merged_tags,
            constraints=merged_constraints,
            doc=kwargs.get("doc"),
            extras=extras_dict
        )
        
        return descriptor
    
    @classmethod
    def _compute_child_path(
        cls,
        child_leaf: Optional[str],
        child_path: Optional[str]
    ) -> Optional[str]:
        """
            Compute the final path for a child endpoint.
            
            The child's path is computed relative to the parent's
            base_path or base_leaf.
            
            :param child_leaf: The child's leaf segment.
            :param child_path: The child's path.
            
            :returns: The computed path, or None if no path can be computed.
        """
        # Determine parent base
        parent_base = cls.base_path
        if parent_base is None and cls.base_leaf is not None:
            parent_base = f"/{cls.base_leaf}"
        
        if parent_base is None:
            # No parent base, return child path as-is
            if child_path is not None:
                return child_path
            return None
        
        # Ensure parent base doesn't end with /
        parent_base = parent_base.rstrip("/")
        
        # Compute child path relative to parent
        if child_path is not None:
            # Child has explicit path
            if child_path.startswith("/"):
                # Absolute path - append to parent base
                return f"{parent_base}{child_path}"
            else:
                # Relative path
                return f"{parent_base}/{child_path}"
        elif child_leaf is not None:
            # Child has leaf - append to parent base
            return f"{parent_base}/{child_leaf}"
        else:
            # No child path or leaf - use parent base
            return parent_base
    
    @classmethod
    def _inspect_schema(cls, schema: Type) -> Dict[str, Any]:
        """
            Inspect a schema type and extract JSON schema information.
            
            Supports Pydantic models (via model_json_schema) and
            dataclasses (via __dataclass_fields__).
            
            :param schema: The schema type to inspect.
            
            :returns: Dictionary containing JSON schema information.
        """
        # Try Pydantic model first
        if hasattr(schema, "model_json_schema"):
            return schema.model_json_schema()
        
        # Try dataclass
        if hasattr(schema, "__dataclass_fields__"):
            return cls._dataclass_to_schema(schema)
        
        # Return a reference schema for unknown types
        return {"$ref": f"#/components/schemas/{schema.__name__}"}
    
    @classmethod
    def _dataclass_to_schema(cls, schema: Type) -> Dict[str, Any]:
        """
            Convert a dataclass to a JSON schema representation.
            
            :param schema: The dataclass type to convert.
            
            :returns: Dictionary containing JSON schema information.
        """
        properties: Dict[str, Any] = {}
        required: List[str] = []
        
        for field_name, field_info in schema.__dataclass_fields__.items():
            field_type = field_info.type
            properties[field_name] = cls._type_to_schema(field_type)
            
            # Check if field has a default — a field is required when
            # both .default and .default_factory are the MISSING sentinel.
            if (field_info.default is dataclasses.MISSING
                    and field_info.default_factory is dataclasses.MISSING):
                required.append(field_name)
        
        result: Dict[str, Any] = {
            "type": "object",
            "properties": properties,
        }
        
        if required:
            result["required"] = required
        
        return result
    
    @classmethod
    def _type_to_schema(cls, field_type: Any) -> Dict[str, Any]:
        """
            Convert a Python type to a JSON schema type.
            
            :param field_type: The Python type to convert.
            
            :returns: Dictionary containing JSON schema type information.
        """
        # Handle basic types
        type_mapping = {
            str: {"type": "string"},
            int: {"type": "integer"},
            float: {"type": "number"},
            bool: {"type": "boolean"},
            list: {"type": "array"},
            dict: {"type": "object"},
        }
        
        if field_type in type_mapping:
            return type_mapping[field_type]
        
        # Handle string type annotations
        if isinstance(field_type, str):
            return {"type": "string"}
        
        # Default to string for unknown types
        return {"type": "string"}
