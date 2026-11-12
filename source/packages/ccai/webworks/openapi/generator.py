"""
.. module:: generator
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: OpenAPI 3.0+ specification generator from endpoint descriptors.

.. moduleauthor:: Code Craft AI LLC

This module provides the :class:`OpenAPIGenerator` class which generates
OpenAPI 3.0+ specifications from endpoint descriptors collected by the
:class:`EndpointRegistry`. It converts endpoint paths, parameters, request
and response schemas, security requirements, and tags into a complete
OpenAPI specification dictionary.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

import copy
import json
import re

from typing import Any, Dict, List, Optional, Tuple

from ccai.webworks.endpoints.descriptor import (
    REST_ERROR_MAP_TYPES_EXTRA,
    REST_MANAGED_EXTRA,
    REST_QUERY_PARAMS_EXTRA,
    REST_REQUEST_SCHEMA_TYPE_EXTRA,
    REST_RESPONSE_SCHEMA_TYPE_EXTRA,
)
from ccai.webworks.openapi.configuration import (
    ExternalDocs,
    OpenAPIInfo,
    ServerObject,
)
from ccai.webworks.openapi.schemaconverter import (
    PYTHON_TO_JSON_SCHEMA,
    SchemaConverter,
)
from ccai.webworks.openapi.securityschemes import OAuth2SecurityScheme, SecurityScheme
from ccai.webworks.openapi.validation import OpenAPIValidator, ValidationIssue


# Regex pattern for extracting path parameters with optional type annotations.
# Matches patterns like {id}, {id:int}, {slug:str}
_PATH_PARAM_PATTERN = re.compile(r"\{(\w+)(?::(\w+))?\}")

# Mapping from path parameter type annotations to OpenAPI schema types.
_PATH_TYPE_MAP: Dict[str, Dict[str, str]] = {
    "int": {"type": "integer"},
    "float": {"type": "number"},
    "str": {"type": "string"},
    "bool": {"type": "boolean"},
    "uuid": {"type": "string", "format": "uuid"},
}

# Standard error response schema included in components/schemas.
REST_ERROR_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "error": {
            "type": "string",
            "description": "Error code",
        },
        "message": {
            "type": "string",
            "description": "Human-readable error message",
        },
        "details": {
            "type": "object",
            "description": "Additional error context",
            "additionalProperties": True,
        },
        "field_errors": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "field": {"type": "string"},
                    "code": {"type": "string"},
                    "message": {"type": "string"},
                },
                "required": ["field", "code", "message"],
            },
        },
    },
    "required": ["error", "message"],
    "example": {
        "error": "validation_error",
        "message": "Request validation failed",
        "field_errors": [
            {"field": "email", "code": "required", "message": "Field 'email' is required"},
        ],
    },
}

# Error body the dispatcher sends for an HTTP error raised by routing or by
# a handler: ``{"detail": ..., "status_code": ...}``.
HTTP_ERROR_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "detail": {
            "type": "string",
            "description": "Human-readable description of the error",
        },
        "status_code": {
            "type": "integer",
            "description": "The HTTP status code of the response",
        },
    },
    "required": ["detail", "status_code"],
    "example": {
        "detail": "Not Found",
        "status_code": 404,
    },
}

# Names of the error schemas in components/schemas.
REST_ERROR_SCHEMA_NAME = "RESTError"
HTTP_ERROR_SCHEMA_NAME = "HTTPError"

# Descriptions of the standard error responses included in every operation.
STANDARD_ERROR_DESCRIPTIONS: Dict[str, str] = {
    "400": "Bad Request - Invalid input",
    "401": "Unauthorized - Authentication required",
    "403": "Forbidden - Insufficient permissions",
    "404": "Not Found - Resource does not exist",
    "500": "Internal Server Error",
}

# Success status code by HTTP method for endpoints whose handler runs the
# REST request/response processing. Every other endpoint answers 200 unless
# its handler builds a response itself.
REST_SUCCESS_STATUS_CODES: Dict[str, str] = {
    "get": "200",
    "post": "201",
    "put": "200",
    "patch": "200",
    "delete": "204",
}

# Vendor extensions carrying the parts of an access policy that an OpenAPI
# security requirement cannot express.
REQUIRED_ROLES_EXTENSION = "x-required-roles"
REQUIRED_SCOPES_EXTENSION = "x-required-scopes"

# Key in descriptor extras naming the security schemes an endpoint accepts.
SECURITY_SCHEMES_EXTRA = "security_schemes"


def build_standard_error_responses(schema_name: str) -> Dict[str, Dict[str, Any]]:
    """
        Build the standard error responses (400, 401, 403, 404, 500) whose
        body is the named component schema.

        Every call returns new dictionaries all the way down. The responses
        used to be shared between operations, which made a YAML export full
        of ``&id001`` anchors and ``*id001`` aliases.

        :param schema_name: Name of the error schema in components/schemas.

        :returns: Mapping of status code string to OpenAPI response object.
    """
    responses: Dict[str, Dict[str, Any]] = {}

    for status_code, description in STANDARD_ERROR_DESCRIPTIONS.items():
        responses[status_code] = {
            "description": description,
            "content": {
                "application/json": {
                    "schema": {"$ref": f"#/components/schemas/{schema_name}"},
                },
            },
        }

    return responses


def dump_yaml(spec: Dict[str, Any]) -> str:
    """
        Serialize a specification to YAML without anchors or aliases.

        PyYAML writes an object that appears twice as an anchor and an
        alias. Some OpenAPI tools reject those and they make a diff of two
        exports unreadable, so every occurrence is written out in full.

        :param spec: The specification dictionary.

        :returns: A YAML string with deterministic key ordering.

        :raises ImportError: If the PyYAML library is not installed.
    """
    try:
        import yaml
    except ImportError as exc:
        errmsg = (
            "PyYAML is required for YAML export. "
            "Install it with: pip install pyyaml"
        )
        raise ImportError(errmsg) from exc

    class AliasFreeDumper(yaml.SafeDumper):
        """
            A YAML dumper that never emits anchors or aliases.
        """

        def ignore_aliases(self, data: Any) -> bool:
            return True

    yaml_str = yaml.dump(spec, Dumper=AliasFreeDumper, default_flow_style=False, sort_keys=True)
    return yaml_str


# Standard error responses included in every operation that is not served by
# the REST request/response processing. Kept for callers that read it; the
# generator builds a fresh copy for each operation.
STANDARD_ERROR_RESPONSES: Dict[str, Dict[str, Any]] = build_standard_error_responses(HTTP_ERROR_SCHEMA_NAME)


def strip_path_type_annotations(path: str) -> str:
    """
        Strip type annotations from path parameter placeholders.

        Converts path strings like ``/users/{id:int}`` to ``/users/{id}``.

        :param path: A URL path string potentially containing typed parameters.

        :returns: The path with type annotations removed from parameter placeholders.
    """
    result = _PATH_PARAM_PATTERN.sub(r"{\1}", path)
    return result


def extract_path_parameters(path: str) -> List[Dict[str, Any]]:
    """
        Extract path parameter objects from a URL path string.

        Parses path parameters with optional type annotations and returns
        a list of OpenAPI parameter objects. For example, ``/users/{id:int}``
        produces a parameter with name ``id``, ``in: path``, and schema
        ``{"type": "integer"}``.

        :param path: A URL path string with parameter placeholders.

        :returns: A list of OpenAPI parameter dictionaries.
    """
    parameters: List[Dict[str, Any]] = []

    for match in _PATH_PARAM_PATTERN.finditer(path):
        param_name = match.group(1)
        param_type = match.group(2)

        schema = _PATH_TYPE_MAP.get(param_type, {"type": "string"}) if param_type else {"type": "string"}

        param_obj: Dict[str, Any] = {
            "name": param_name,
            "in": "path",
            "required": True,
            "schema": dict(schema),
        }

        parameters.append(param_obj)

    return parameters


class OpenAPIGenerator:
    """
        Generates OpenAPI 3.0+ specifications from endpoint descriptors.

        The generator collects endpoint descriptors from a registry, converts
        their paths, parameters, request/response schemas, security requirements,
        and tags into a complete OpenAPI specification dictionary.

        Supports filtering endpoints by path prefix or tag so that only
        relevant API endpoints appear in the generated specification.

        :param registry: The endpoint registry providing descriptors.
        :param info: The OpenAPI info object with API metadata.
        :param servers: Optional list of server objects.
        :param security_schemes: Optional mapping of scheme name to SecurityScheme.
        :param tag_descriptions: Optional mapping of tag name to description.
        :param external_docs: Optional external documentation link.
        :param derive_tags_from_path: Whether to derive tags from path hierarchy.
        :param include_paths: Optional list of path prefixes to include.
            Only endpoints whose path starts with one of these prefixes will
            appear in the specification.
        :param exclude_paths: Optional list of path prefixes to exclude.
        :param include_tags: Optional list of tags to include.  Only endpoints
            with at least one matching tag will appear.
        :param exclude_tags: Optional list of tags to exclude.
    """

    def __init__(
        self,
        registry,
        info: OpenAPIInfo,
        servers: Optional[List[ServerObject]] = None,
        security_schemes: Optional[Dict[str, SecurityScheme]] = None,
        tag_descriptions: Optional[Dict[str, str]] = None,
        external_docs: Optional[ExternalDocs] = None,
        derive_tags_from_path: bool = False,
        include_paths: Optional[List[str]] = None,
        exclude_paths: Optional[List[str]] = None,
        include_tags: Optional[List[str]] = None,
        exclude_tags: Optional[List[str]] = None,
        rest_only: bool = True,
    ):
        self.registry = registry
        self.info = info
        self.servers = servers or []
        self.security_schemes = security_schemes or {}
        self.tag_descriptions = tag_descriptions or {}
        self.external_docs = external_docs
        self.derive_tags_from_path = derive_tags_from_path
        self.include_paths = include_paths
        self.exclude_paths = exclude_paths
        self.include_tags = include_tags
        self.exclude_tags = exclude_tags
        self.rest_only = rest_only
        self._schema_converter = SchemaConverter()
        self._cache: Optional[Dict[str, Any]] = None
        self._cache_key: Optional[Tuple[Any, ...]] = None
        self._operation_ids: Dict[Tuple[int, str], str] = {}
        return

    def generate(self) -> Dict[str, Any]:
        """
            Generate a complete OpenAPI 3.0.3 specification.

            Iterates all endpoint descriptors from the registry and converts
            them into OpenAPI path items, operations, parameters, request bodies,
            responses, and security requirements.

            The result is cached: until :meth:`refresh` is called, or the
            set of registered endpoints changes, later calls return a copy
            of the same specification without rebuilding it. Each call
            returns its own copy, so a caller may modify what it receives.

            :returns: A complete OpenAPI specification dictionary.
        """
        cache_key = self._build_cache_key()
        if self._cache is not None and self._cache_key == cache_key:
            cached = copy.deepcopy(self._cache)
            return cached

        spec: Dict[str, Any] = {
            "openapi": "3.0.3",
            "info": self.info.to_dict(),
        }

        if len(self.servers) > 0:
            spec["servers"] = [s.to_dict() for s in self.servers]

        paths = self._build_paths()
        spec["paths"] = paths

        components = self._build_components()
        if len(components) > 0:
            spec["components"] = components

        tags = self._collect_tags()
        if len(tags) > 0:
            spec["tags"] = tags

        if self.external_docs is not None:
            spec["externalDocs"] = self.external_docs.to_dict()

        self._cache = copy.deepcopy(spec)
        self._cache_key = cache_key
        return spec

    def _build_cache_key(self) -> Tuple[Any, ...]:
        """
            Build a value that changes whenever the generated specification
            would: the registered endpoints (which descriptors, at which
            paths, for which methods) and the generator's own settings.

            :returns: A tuple to compare against the key of the cached
                      specification.
        """
        endpoint_keys: List[Tuple[Any, ...]] = []
        for descriptor in self.registry.collect():
            endpoint_keys.append((
                id(descriptor),
                descriptor.path,
                descriptor.leaf,
                tuple(descriptor.methods),
                tuple(descriptor.tags or ()),
            ))

        external_docs_key = None
        if self.external_docs is not None:
            external_docs_key = repr(self.external_docs.to_dict())

        settings_key = (
            repr(self.info.to_dict()),
            tuple(repr(server.to_dict()) for server in self.servers),
            tuple((name, repr(scheme.to_dict())) for name, scheme in self.security_schemes.items()),
            tuple(sorted(self.tag_descriptions.items())),
            external_docs_key,
            self.derive_tags_from_path,
            tuple(self.include_paths) if self.include_paths is not None else None,
            tuple(self.exclude_paths) if self.exclude_paths is not None else None,
            tuple(self.include_tags) if self.include_tags is not None else None,
            tuple(self.exclude_tags) if self.exclude_tags is not None else None,
            self.rest_only,
        )

        rtnval = (tuple(endpoint_keys), settings_key)
        return rtnval

    def validate(self, strict: bool = False) -> List[ValidationIssue]:
        """
            Validate the generated specification.

            Generates the specification (if not already cached) and validates
            it using :class:`OpenAPIValidator`. If validation errors are found,
            raises :class:`SpecificationValidationError`.

            :param strict: If True, treat warnings as errors.

            :returns: A list of :class:`ValidationIssue` objects (empty if valid).

            :raises SpecificationValidationError: If validation fails.
        """
        spec = self.generate()
        validator = OpenAPIValidator(strict=strict)
        issues = validator.validate(spec)
        return issues

    def generate_json(self, indent: int = 2) -> str:
        """
            Generate the OpenAPI specification as a JSON string.

            Generates the specification (if not already cached) and serializes
            it to a JSON string with deterministic key ordering.

            :param indent: Number of spaces for indentation. Defaults to 2.

            :returns: A JSON string representation of the OpenAPI specification.
        """
        spec = self.generate()
        json_str = json.dumps(spec, indent=indent, sort_keys=True)
        return json_str

    def generate_yaml(self) -> str:
        """
            Generate the OpenAPI specification as a YAML string.

            Generates the specification (if not already cached) and serializes
            it to a YAML string with deterministic key ordering. Requires the
            PyYAML library to be installed.

            :returns: A YAML string representation of the OpenAPI specification.

            :raises ImportError: If the PyYAML library is not installed.
        """
        spec = self.generate()
        yaml_str = dump_yaml(spec)
        return yaml_str

    def export(self, path: str, format: Optional[str] = None) -> None:
        """
            Export the OpenAPI specification to a file.

            Writes the specification to the given file path. The output format
            is inferred from the file extension unless explicitly provided via
            the ``format`` parameter.

            :param path: Output file path.
            :param format: Output format, either ``'json'`` or ``'yaml'``.
                Inferred from the file extension if not specified.

            :raises ValueError: If the format cannot be determined from the
                file extension and is not explicitly provided.
        """
        if format is None:
            if path.endswith(".json"):
                format = "json"
            elif path.endswith(".yaml") or path.endswith(".yml"):
                format = "yaml"
            else:
                errmsg = (
                    f"Cannot infer export format from file extension: '{path}'. "
                    "Provide an explicit format parameter ('json' or 'yaml')."
                )
                raise ValueError(errmsg)

        if format == "json":
            content = self.generate_json()
        elif format == "yaml":
            content = self.generate_yaml()
        else:
            errmsg = f"Unsupported export format: '{format}'. Use 'json' or 'yaml'."
            raise ValueError(errmsg)

        with open(path, "w", encoding="utf-8") as file_handle:
            file_handle.write(content)

        return

    def refresh(self) -> None:
        """
            Invalidate the cached specification.
        """
        self._cache = None
        self._cache_key = None
        return

    def _build_paths(self) -> Dict[str, Any]:
        """
            Build the paths object from endpoint descriptors.

            Groups operations by their OpenAPI path (with type annotations
            stripped) and creates operation objects for each HTTP method.
            Applies path prefix and tag filters when configured.

            :returns: A dictionary mapping OpenAPI paths to path item objects.
        """
        paths: Dict[str, Any] = {}
        descriptors = self.registry.collect()

        included: List[Tuple[Any, str]] = []
        for descriptor in descriptors:
            openapi_path = strip_path_type_annotations(self._get_raw_path(descriptor))

            if not self._should_include_descriptor(descriptor, openapi_path):
                continue

            included.append((descriptor, openapi_path))

        # operationId must be unique across the whole document, so the ids
        # are assigned with every included operation in view.
        self._operation_ids = self._assign_operation_ids(included)

        for descriptor, openapi_path in included:
            if openapi_path not in paths:
                paths[openapi_path] = {}

            for method in descriptor.methods:
                method_lower = method.lower()
                operation = self._build_operation(descriptor=descriptor, method=method_lower)
                paths[openapi_path][method_lower] = operation

        return paths

    @staticmethod
    def _get_raw_path(descriptor) -> str:
        """
            Get the URL path of a descriptor, from its ``path`` or its
            ``leaf``.

            :param descriptor: The endpoint descriptor.

            :returns: The path as declared, with any type annotations.
        """
        raw_path = descriptor.path
        if raw_path is None:
            leaf = descriptor.leaf
            if leaf is not None:
                raw_path = f"/{leaf}"
            else:
                raw_path = "/"

        return raw_path

    def _assign_operation_ids(self, included: List[Tuple[Any, str]]) -> Dict[Tuple[int, str], str]:
        """
            Choose a unique operationId for every operation in the document.

            An operation is named after its handler function whenever that
            name is used by no other operation, so the ids of an existing
            API do not change. When a name is shared -- one handler serving
            several methods (``RestEndpoint.update`` registers PUT and
            PATCH), or handlers of the same name in different modules --
            each of those operations gets the handler name followed by its
            method (``update_item_put``), and if that is still shared, the
            method, path and handler name together, which cannot collide
            because a path and method identify one operation.

            :param included: The ``(descriptor, openapi_path)`` pairs that
                             appear in the document.

            :returns: Mapping of ``(id(descriptor), lowercase method)`` to
                      the operationId.
        """
        operations: List[Tuple[Any, str, str, str]] = []
        for descriptor, openapi_path in included:
            handler_name = getattr(descriptor.handler, "__name__", "operation")
            for method in descriptor.methods:
                operations.append((descriptor, method.lower(), openapi_path, handler_name))

        name_counts: Dict[str, int] = {}
        for _, _, _, handler_name in operations:
            name_counts[handler_name] = name_counts.get(handler_name, 0) + 1

        with_method_counts: Dict[str, int] = {}
        for _, method, _, handler_name in operations:
            with_method = f"{handler_name}_{method}"
            with_method_counts[with_method] = with_method_counts.get(with_method, 0) + 1

        assigned: Dict[Tuple[int, str], str] = {}
        used: List[str] = []
        for descriptor, method, openapi_path, handler_name in operations:
            with_method = f"{handler_name}_{method}"

            if name_counts[handler_name] == 1 and with_method_counts.get(handler_name, 0) == 0:
                operation_id = handler_name
            elif with_method_counts[with_method] == 1 and name_counts.get(with_method, 0) == 0:
                operation_id = with_method
            else:
                path_part = re.sub(r"[^0-9A-Za-z]+", "_", openapi_path).strip("_")
                if len(path_part) == 0:
                    path_part = "root"
                operation_id = f"{method}_{path_part}_{handler_name}"

            # Last resort: a number, should two ids still coincide
            candidate = operation_id
            suffix = 2
            while candidate in used:
                candidate = f"{operation_id}_{suffix}"
                suffix += 1

            used.append(candidate)
            assigned[(id(descriptor), method)] = candidate

        return assigned

    def _should_include_descriptor(self, descriptor, openapi_path: str) -> bool:
        """
            Determine whether a descriptor should be included in the
            spec based on the configured path and tag filters.

            When ``rest_only`` is ``True`` (the default), only
            descriptors whose ``extras["endpoint_type"]`` is one of
            ``{"rest", "auth"}`` are included. This ensures that
            plain page routes registered via :meth:`Endpoint.attach_at`
            are excluded while REST API routes registered via
            :meth:`RestBlueprint.attach_at` (``"rest"``) and
            authentication-flow routes registered via
            :class:`SecurityBlueprint` subclasses (``"auth"``) are
            both included. Despite the misleading attribute name
            ``rest_only``, the auth flows belong in the generated
            API docs alongside REST endpoints — they're documented
            HTTP routes consumers care about.

            When ``include_paths`` is set, the endpoint path must
            start with at least one of the listed prefixes. When
            ``exclude_paths`` is set, the endpoint path must not
            start with any of the listed prefixes. Tag filters work
            similarly against the descriptor's tag list.

            :param descriptor: The endpoint descriptor.
            :param openapi_path: The normalised OpenAPI path string.

            :returns: True if the descriptor passes all filters.
        """
        # Documented-endpoint filter: skip plain page routes that
        # weren't registered via a documented-endpoint family.
        if self.rest_only:
            endpoint_type = descriptor.extras.get("endpoint_type")
            if endpoint_type not in ("rest", "auth"):
                return False
        # Path prefix inclusion filter
        if self.include_paths is not None:
            matched = False
            for prefix in self.include_paths:
                if openapi_path.startswith(prefix):
                    matched = True
                    break
            if not matched:
                return False

        # Path prefix exclusion filter
        if self.exclude_paths is not None:
            for prefix in self.exclude_paths:
                if openapi_path.startswith(prefix):
                    return False

        # Tag inclusion filter
        descriptor_tags = descriptor.tags or []

        if self.include_tags is not None:
            if len(descriptor_tags) == 0:
                return False
            matched = False
            for tag in descriptor_tags:
                if tag in self.include_tags:
                    matched = True
                    break
            if not matched:
                return False

        # Tag exclusion filter
        if self.exclude_tags is not None:
            for tag in descriptor_tags:
                if tag in self.exclude_tags:
                    return False

        return True

    def _build_operation(self, descriptor, method: str) -> Dict[str, Any]:
        """
            Build an operation object for a single endpoint method.

            Uses the operationId assigned by :meth:`_assign_operation_ids`
            (the handler function name, made unique), includes summary and
            description from the doc attribute, includes tags, and assembles
            parameters, request body, and responses.

            :param descriptor: The endpoint descriptor.
            :param method: The HTTP method in lowercase.

            :returns: An OpenAPI operation object dictionary.
        """
        operation_id = self._operation_ids.get((id(descriptor), method))
        if operation_id is None:
            operation_id = getattr(descriptor.handler, "__name__", "operation")

        operation: Dict[str, Any] = {
            "operationId": operation_id,
        }

        # Add documentation from doc attribute
        doc = descriptor.doc
        if doc is not None:
            if doc.summary is not None:
                operation["summary"] = doc.summary
            if doc.description is not None:
                operation["description"] = doc.description
            if doc.deprecated:
                operation["deprecated"] = True
            if doc.external_docs is not None:
                operation["externalDocs"] = {"url": doc.external_docs}

        # Add tags
        tags = descriptor.tags
        if tags is not None and len(tags) > 0:
            operation["tags"] = list(tags)
        elif self.derive_tags_from_path:
            derived_tag = self._derive_tag_from_path(descriptor)
            if derived_tag is not None:
                operation["tags"] = [derived_tag]

        # Build parameters (path + query)
        parameters = self._build_parameters(descriptor=descriptor)
        if len(parameters) > 0:
            operation["parameters"] = parameters

        # Build request body. GET, HEAD and DELETE requests carry none, so
        # an endpoint that serves several methods documents it only on the
        # methods that take one.
        if method not in ("get", "head", "delete", "options"):
            request_body = self._build_request_body(descriptor=descriptor)
            if request_body is not None:
                operation["requestBody"] = request_body

        # Build responses
        responses = self._build_responses(descriptor=descriptor, method=method)
        operation["responses"] = responses

        # Build security
        security = self._build_security(descriptor=descriptor)
        if security is not None:
            operation["security"] = security

        # The parts of the access policy a security requirement cannot say
        operation.update(self._build_security_extensions(descriptor=descriptor, security=security))

        return operation

    def _build_parameters(self, descriptor) -> List[Dict[str, Any]]:
        """
            Build parameter objects from path parameters and query parameters.

            Extracts path parameters from the descriptor's path string and
            query parameters from the ``extras["rest"]["query_params"]`` metadata.

            :param descriptor: The endpoint descriptor.

            :returns: A list of OpenAPI parameter dictionaries.
        """
        parameters: List[Dict[str, Any]] = []

        # Extract path parameters
        raw_path = descriptor.path
        if raw_path is None:
            leaf = descriptor.leaf
            if leaf is not None:
                raw_path = f"/{leaf}"
            else:
                raw_path = "/"

        path_params = extract_path_parameters(raw_path)
        parameters.extend(path_params)

        # Extract query parameters from extras
        extras = descriptor.extras
        if extras is not None and "rest" in extras:
            rest_extras = extras["rest"]
            query_params = rest_extras.get(REST_QUERY_PARAMS_EXTRA)
            if query_params is not None:
                for param_name, param_type in query_params.items():
                    schema = self._convert_query_param_type(param_type=param_type)
                    param_obj: Dict[str, Any] = {
                        "name": param_name,
                        "in": "query",
                        "required": False,
                        "schema": schema,
                    }
                    parameters.append(param_obj)

        return parameters

    def _convert_query_param_type(self, param_type) -> Dict[str, Any]:
        """
            Convert a query parameter Python type to a JSON Schema type.

            Uses the PYTHON_TO_JSON_SCHEMA mapping for primitive types and
            falls back to the schema converter for complex types.

            :param param_type: The Python type of the query parameter.

            :returns: A JSON Schema dictionary for the parameter type.
        """
        if param_type in PYTHON_TO_JSON_SCHEMA:
            result = dict(PYTHON_TO_JSON_SCHEMA[param_type])
            return result

        result = self._schema_converter.convert(python_type=param_type)
        return result

    def _build_request_body(self, descriptor) -> Optional[Dict[str, Any]]:
        """
            Build a requestBody object from the descriptor's request_schema.

            If the descriptor has ``extras["rest"]["request_schema"]`` defined,
            converts the Python type to JSON Schema and wraps it in a
            requestBody with ``application/json`` content type.

            :param descriptor: The endpoint descriptor.

            :returns: An OpenAPI requestBody dictionary, or None if no schema.
        """
        extras = descriptor.extras
        if extras is None or "rest" not in extras:
            return None

        rest_extras = extras["rest"]
        request_schema = self._get_declared_schema(
            rest_extras=rest_extras,
            type_key=REST_REQUEST_SCHEMA_TYPE_EXTRA,
            schema_key="request_schema"
        )
        if request_schema is None:
            return None

        json_schema = self._schema_converter.convert(python_type=request_schema)

        result: Dict[str, Any] = {
            "required": True,
            "content": {
                "application/json": {
                    "schema": json_schema,
                },
            },
        }

        return result

    @staticmethod
    def _get_declared_schema(rest_extras: Dict[str, Any], type_key: str, schema_key: str) -> Any:
        """
            Get a schema an endpoint declared, in the best form available.

            ``attach_at`` stores the schema class under ``type_key`` and the
            JSON Schema it inspected from that class under ``schema_key``.
            The class is preferred: the converter turns it into a named
            component and a ``$ref``. A descriptor that carries only the
            inspected dict, or a hand-built one that holds the class under
            ``schema_key``, is used as it is -- the converter accepts both.

            :param rest_extras: The descriptor's ``extras["rest"]`` mapping.
            :param type_key: Key holding the schema class.
            :param schema_key: Key holding the inspected schema.

            :returns: The schema class, the JSON Schema dict, or None.
        """
        declared = rest_extras.get(type_key)
        if declared is None:
            declared = rest_extras.get(schema_key)

        return declared

    @staticmethod
    def _is_rest_managed(descriptor) -> bool:
        """
            Whether an endpoint's handler runs the REST request/response
            processing, which decides the success status by method and
            reports errors as ``RESTError``.

            :param descriptor: The endpoint descriptor.

            :returns: True when the endpoint is marked as REST managed.
        """
        extras = descriptor.extras
        if extras is None or "rest" not in extras:
            return False

        rest_extras = extras["rest"]
        if not isinstance(rest_extras, dict):
            return False

        rtnval = rest_extras.get(REST_MANAGED_EXTRA) is True
        return rtnval

    def _build_responses(self, descriptor, method: str = "get") -> Dict[str, Any]:
        """
            Build the responses object for an operation.

            Includes the success response from the descriptor's
            ``response_schema``, standard error responses (400, 401, 403,
            404, 500), and any custom error responses from the ``error_map``.

            The status codes and error bodies documented are the ones the
            server sends. An endpoint served by the REST request/response
            processing answers 201 to a POST, 204 with no body to a DELETE
            and 200 otherwise, and reports errors as ``RESTError``. Any
            other endpoint answers 200, and its routing errors are the
            dispatcher's ``HTTPError`` body.

            :param descriptor: The endpoint descriptor.
            :param method: The HTTP method in lowercase.

            :returns: An OpenAPI responses dictionary.
        """
        responses: Dict[str, Any] = {}

        # Build success response
        extras = descriptor.extras
        response_schema = None
        error_map = None

        if extras is not None and "rest" in extras:
            rest_extras = extras["rest"]
            response_schema = self._get_declared_schema(
                rest_extras=rest_extras,
                type_key=REST_RESPONSE_SCHEMA_TYPE_EXTRA,
                schema_key="response_schema"
            )
            error_map = rest_extras.get(REST_ERROR_MAP_TYPES_EXTRA)
            if error_map is None:
                error_map = rest_extras.get("error_map")

        rest_managed = self._is_rest_managed(descriptor)

        success_status = "200"
        error_schema_name = HTTP_ERROR_SCHEMA_NAME
        if rest_managed:
            success_status = REST_SUCCESS_STATUS_CODES.get(method, "200")
            error_schema_name = REST_ERROR_SCHEMA_NAME

        if success_status == "204":
            responses[success_status] = {
                "description": "Successful response with no content",
            }
        elif response_schema is not None:
            json_schema = self._schema_converter.convert(python_type=response_schema)
            responses[success_status] = {
                "description": "Successful response",
                "content": {
                    "application/json": {
                        "schema": json_schema,
                    },
                },
            }
        else:
            responses[success_status] = {
                "description": "Successful response",
            }

        # Add standard error responses
        for status_code, error_response in build_standard_error_responses(error_schema_name).items():
            responses[status_code] = error_response

        # Add custom error responses from error_map
        if error_map is not None:
            for status_code, error_type in error_map.items():
                if not isinstance(status_code, (int, str)) or isinstance(status_code, bool):
                    # A resource endpoint's error_map maps exception types
                    # to error mappings; that is runtime configuration, not
                    # a documented response.
                    continue
                status_str = str(status_code)
                error_schema = self._schema_converter.convert(python_type=error_type)
                responses[status_str] = {
                    "description": f"Error response {status_str}",
                    "content": {
                        "application/json": {
                            "schema": error_schema,
                        },
                    },
                }

        return responses

    def _get_required_access_policy(self, descriptor) -> Any:
        """
            Get the access policy of a descriptor when it requires
            authentication.

            :param descriptor: The endpoint descriptor.

            :returns: The AccessPolicy, or None when the endpoint has no
                      policy or its policy does not require authentication.
        """
        constraints = descriptor.constraints
        if constraints is None:
            return None

        access_policy = constraints.access_policy
        if access_policy is None:
            return None

        if not access_policy.require_auth:
            return None

        return access_policy

    def _get_applicable_scheme_names(self, descriptor) -> List[str]:
        """
            Get the names of the configured security schemes an endpoint
            accepts.

            An endpoint names the schemes it accepts with a
            ``security_schemes`` entry in its extras
            (``attach_at(..., security_schemes=["bearer"])``); names that
            are not configured on the generator are left out, since a
            requirement must not reference an undefined scheme. An endpoint
            that names none accepts every configured scheme.

            :param descriptor: The endpoint descriptor.

            :returns: Scheme names, in the generator's configuration order.
        """
        configured_names = list(self.security_schemes.keys())

        extras = descriptor.extras
        accepted = None
        if extras is not None:
            accepted = extras.get(SECURITY_SCHEMES_EXTRA)

        if accepted is None:
            return configured_names

        if isinstance(accepted, str):
            accepted = [accepted]

        rtnval = [name for name in configured_names if name in accepted]
        return rtnval

    def _build_security(self, descriptor) -> Optional[List[Dict[str, List[str]]]]:
        """
            Build security requirements from the descriptor's access_policy.

            Extracts authentication requirements from the endpoint constraints
            and maps them to security scheme references. For OAuth2 schemes,
            scopes from the access_policy are included. For non-OAuth2 schemes
            (apiKey, http), empty scope arrays are used per the OpenAPI
            specification.

            Only schemes that are configured on the generator and that the
            endpoint accepts (see :meth:`_get_applicable_scheme_names`) are
            referenced, each as an alternative. When there is none -- no
            scheme is configured, or none of the configured ones applies --
            no requirement is written: a requirement naming a scheme that
            ``components.securitySchemes`` does not define makes the
            document invalid.

            :param descriptor: The endpoint descriptor.

            :returns: A list of security requirement objects, or None.
        """
        access_policy = self._get_required_access_policy(descriptor)
        if access_policy is None:
            return None

        scheme_names = self._get_applicable_scheme_names(descriptor)
        if len(scheme_names) == 0:
            return None

        security: List[Dict[str, List[str]]] = []
        scopes = list(access_policy.scopes) if access_policy.scopes else []

        for scheme_name in scheme_names:
            scheme_obj = self.security_schemes[scheme_name]
            if isinstance(scheme_obj, OAuth2SecurityScheme):
                security.append({scheme_name: list(scopes)})
            else:
                security.append({scheme_name: []})

        return security

    def _build_security_extensions(
        self,
        descriptor,
        security: Optional[List[Dict[str, List[str]]]]
    ) -> Dict[str, Any]:
        """
            Build the vendor extensions that record what an access policy
            requires beyond what the security requirements express.

            - ``x-required-roles``: the roles the caller must hold. OpenAPI
              has no place for roles.
            - ``x-required-scopes``: the scopes the caller must hold, when
              they are not all carried by an OAuth2 requirement (no scheme
              is configured, or an accepted scheme is not OAuth2).

            :param descriptor: The endpoint descriptor.
            :param security: The security requirements built for the
                             operation, or None.

            :returns: Extension name to value; empty when nothing is needed.
        """
        extensions: Dict[str, Any] = {}

        access_policy = self._get_required_access_policy(descriptor)
        if access_policy is None:
            return extensions

        roles = list(access_policy.roles) if access_policy.roles else []
        if len(roles) > 0:
            extensions[REQUIRED_ROLES_EXTENSION] = roles

        scopes = list(access_policy.scopes) if access_policy.scopes else []
        if len(scopes) > 0:
            scopes_expressed = security is not None and len(security) > 0
            if scopes_expressed:
                for requirement in security:
                    for requirement_scopes in requirement.values():
                        if len(requirement_scopes) == 0:
                            scopes_expressed = False
            if not scopes_expressed:
                extensions[REQUIRED_SCOPES_EXTENSION] = scopes

        return extensions

    def _collect_tags(self) -> List[Dict[str, str]]:
        """
            Collect unique tags from all endpoint descriptors.

            Iterates all descriptors and collects unique tag names, then
            builds tag objects with optional descriptions from the
            ``tag_descriptions`` configuration.

            When ``derive_tags_from_path`` is enabled and an endpoint has
            no explicit tags, a tag is derived from the first non-parameter
            segment of the path (e.g., ``/users/{id}`` yields ``users``).

            :returns: A list of OpenAPI tag objects.
        """
        seen_tags: List[str] = []
        descriptors = self.registry.collect()

        for descriptor in descriptors:
            # Apply the same inclusion filters used by _build_paths so
            # that tags from excluded endpoints (e.g. non-REST page
            # routes) do not leak into the specification.
            raw_path = descriptor.path
            if raw_path is None:
                leaf = descriptor.leaf
                if leaf is not None:
                    raw_path = f"/{leaf}"
                else:
                    raw_path = "/"
            openapi_path = strip_path_type_annotations(raw_path)
            if not self._should_include_descriptor(descriptor, openapi_path):
                continue

            tags = descriptor.tags
            if tags is not None and len(tags) > 0:
                for tag in tags:
                    if tag not in seen_tags:
                        seen_tags.append(tag)
            elif self.derive_tags_from_path:
                derived_tag = self._derive_tag_from_path(descriptor)
                if derived_tag is not None and derived_tag not in seen_tags:
                    seen_tags.append(derived_tag)

        result: List[Dict[str, str]] = []
        for tag_name in seen_tags:
            tag_obj: Dict[str, str] = {"name": tag_name}
            description = self.tag_descriptions.get(tag_name)
            if description is not None:
                tag_obj["description"] = description
            result.append(tag_obj)

        return result
    def _derive_tag_from_path(self, descriptor) -> Optional[str]:
        """
            Derive a tag name from the first path segment of a descriptor.

            Extracts the first non-parameter segment from the path. For
            example, ``/users/{id}`` yields ``users`` and ``/api/v1/orders``
            yields ``api``.

            :param descriptor: The endpoint descriptor.

            :returns: A derived tag name, or None if no segment can be derived.
        """
        raw_path = descriptor.path
        if raw_path is None:
            leaf = descriptor.leaf
            if leaf is not None:
                raw_path = f"/{leaf}"
            else:
                return None

        segments = raw_path.strip("/").split("/")
        for segment in segments:
            if len(segment) > 0 and not segment.startswith("{"):
                return segment

        return None

    def _build_components(self) -> Dict[str, Any]:
        """
            Build the components object with schemas and security schemes.

            Collects all schemas from the schema converter cache and adds
            the standard error schemas, ``RESTError`` and ``HTTPError``.
            Also includes security scheme definitions.

            :returns: An OpenAPI components dictionary.
        """
        components: Dict[str, Any] = {}

        # Build schemas section
        schemas = copy.deepcopy(self._schema_converter.get_all_schemas())
        schemas[REST_ERROR_SCHEMA_NAME] = copy.deepcopy(REST_ERROR_SCHEMA)
        schemas[HTTP_ERROR_SCHEMA_NAME] = copy.deepcopy(HTTP_ERROR_SCHEMA)

        components["schemas"] = schemas

        # Build security schemes section
        if len(self.security_schemes) > 0:
            security_schemes_dict: Dict[str, Any] = {}
            for name, scheme in self.security_schemes.items():
                security_schemes_dict[name] = scheme.to_dict()
            components["securitySchemes"] = security_schemes_dict

        return components
