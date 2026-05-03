"""
.. module:: generator
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: OpenAPI 3.0+ specification generator from endpoint descriptors.

.. moduleauthor:: Automation Mojo LLC

This module provides the :class:`OpenAPI_Generator` class which generates
OpenAPI 3.0+ specifications from endpoint descriptors collected by the
:class:`EndpointRegistry`. It converts endpoint paths, parameters, request
and response schemas, security requirements, and tags into a complete
OpenAPI specification dictionary.
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

import json
import re

from typing import Any, Dict, List, Optional, Type

from automojo.webworks.openapi.configuration import (
    ExternalDocs,
    OpenAPIInfo,
    ServerObject,
)
from automojo.webworks.openapi.schemaconverter import (
    PYTHON_TO_JSON_SCHEMA,
    SchemaConverter,
)
from automojo.webworks.openapi.securityschemes import OAuth2SecurityScheme, SecurityScheme
from automojo.webworks.openapi.validation import OpenAPIValidator, ValidationIssue


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
}

# Standard error responses included in every operation.
STANDARD_ERROR_RESPONSES: Dict[str, Dict[str, Any]] = {
    "400": {
        "description": "Bad Request - Invalid input",
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/RESTError"},
            },
        },
    },
    "401": {
        "description": "Unauthorized - Authentication required",
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/RESTError"},
            },
        },
    },
    "403": {
        "description": "Forbidden - Insufficient permissions",
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/RESTError"},
            },
        },
    },
    "404": {
        "description": "Not Found - Resource does not exist",
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/RESTError"},
            },
        },
    },
    "500": {
        "description": "Internal Server Error",
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/RESTError"},
            },
        },
    },
}


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
        return

    def generate(self) -> Dict[str, Any]:
        """
            Generate a complete OpenAPI 3.0.3 specification.

            Iterates all endpoint descriptors from the registry and converts
            them into OpenAPI path items, operations, parameters, request bodies,
            responses, and security requirements.

            :returns: A complete OpenAPI specification dictionary.
        """
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

        self._cache = spec
        return spec

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
        try:
            import yaml
        except ImportError:
            errmsg = (
                "PyYAML is required for YAML export. "
                "Install it with: pip install pyyaml"
            )
            raise ImportError(errmsg)

        spec = self.generate()
        yaml_str = yaml.dump(spec, default_flow_style=False, sort_keys=True)
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

        for descriptor in descriptors:
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

            if openapi_path not in paths:
                paths[openapi_path] = {}

            for method in descriptor.methods:
                method_lower = method.lower()
                operation = self._build_operation(descriptor=descriptor, method=method_lower)
                paths[openapi_path][method_lower] = operation

        return paths

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

            Generates the operationId from the handler function name, includes
            summary and description from the doc attribute, includes tags,
            and assembles parameters, request body, and responses.

            :param descriptor: The endpoint descriptor.
            :param method: The HTTP method in lowercase.

            :returns: An OpenAPI operation object dictionary.
        """
        handler_name = descriptor.handler.__name__
        operation_id = handler_name

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

        # Build request body
        request_body = self._build_request_body(descriptor=descriptor)
        if request_body is not None:
            operation["requestBody"] = request_body

        # Build responses
        responses = self._build_responses(descriptor=descriptor)
        operation["responses"] = responses

        # Build security
        security = self._build_security(descriptor=descriptor)
        if security is not None:
            operation["security"] = security

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
            query_params = rest_extras.get("query_params")
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
        request_schema = rest_extras.get("request_schema")
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

    def _build_responses(self, descriptor) -> Dict[str, Any]:
        """
            Build the responses object for an operation.

            Includes a success response (200) from the descriptor's
            ``response_schema``, standard error responses (400, 401, 403,
            404, 500), and any custom error responses from the ``error_map``.

            :param descriptor: The endpoint descriptor.

            :returns: An OpenAPI responses dictionary.
        """
        responses: Dict[str, Any] = {}

        # Build success response
        extras = descriptor.extras
        response_schema = None
        error_map = None

        if extras is not None and "rest" in extras:
            rest_extras = extras["rest"]
            response_schema = rest_extras.get("response_schema")
            error_map = rest_extras.get("error_map")

        if response_schema is not None:
            json_schema = self._schema_converter.convert(python_type=response_schema)
            responses["200"] = {
                "description": "Successful response",
                "content": {
                    "application/json": {
                        "schema": json_schema,
                    },
                },
            }
        else:
            responses["200"] = {
                "description": "Successful response",
            }

        # Add standard error responses
        for status_code, error_response in STANDARD_ERROR_RESPONSES.items():
            responses[status_code] = dict(error_response)

        # Add custom error responses from error_map
        if error_map is not None:
            for status_code, error_type in error_map.items():
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

    def _build_security(self, descriptor) -> Optional[List[Dict[str, List[str]]]]:
        """
            Build security requirements from the descriptor's access_policy.

            Extracts authentication requirements from the endpoint constraints
            and maps them to security scheme references. For OAuth2 schemes,
            scopes from the access_policy are included. For non-OAuth2 schemes
            (apiKey, http), empty scope arrays are used per the OpenAPI
            specification.

            When no security_schemes are configured on the generator, falls
            back to a generic "oauth2" reference with the access_policy scopes.

            :param descriptor: The endpoint descriptor.

            :returns: A list of security requirement objects, or None.
        """
        constraints = descriptor.constraints
        if constraints is None:
            return None

        access_policy = constraints.access_policy
        if access_policy is None:
            return None

        if not access_policy.require_auth:
            return None

        security: List[Dict[str, List[str]]] = []
        scopes = list(access_policy.scopes) if access_policy.scopes else []

        if len(self.security_schemes) > 0:
            for scheme_name, scheme_obj in self.security_schemes.items():
                if isinstance(scheme_obj, OAuth2SecurityScheme):
                    security.append({scheme_name: scopes})
                else:
                    security.append({scheme_name: []})
        else:
            security.append({"oauth2": scopes})

        return security

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
            the standard RESTError schema. Also includes security scheme
            definitions.

            :returns: An OpenAPI components dictionary.
        """
        components: Dict[str, Any] = {}

        # Build schemas section
        schemas = dict(self._schema_converter.get_all_schemas())
        schemas["RESTError"] = dict(REST_ERROR_SCHEMA)

        components["schemas"] = schemas

        # Build security schemes section
        if len(self.security_schemes) > 0:
            security_schemes_dict: Dict[str, Any] = {}
            for name, scheme in self.security_schemes.items():
                security_schemes_dict[name] = scheme.to_dict()
            components["securitySchemes"] = security_schemes_dict

        return components
