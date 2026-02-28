# Design Document: OpenAPI and Swagger UI

## Overview

This design document describes the architecture and implementation approach for the OpenAPI and Swagger UI feature. The feature provides automatic OpenAPI 3.0+ specification generation from endpoint descriptors and hosts interactive documentation via Swagger UI and ReDoc.

Key design principles:
- Automatic: Specifications are generated from endpoint metadata without manual documentation
- Accurate: Generated documentation reflects the actual API implementation
- Extensible: Custom schemas, security schemes, and metadata can be added
- Cacheable: Specifications are cached to avoid regeneration overhead
- Standards-compliant: Output conforms to OpenAPI 3.0+ specification

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      OpenAPI Generation Pipeline                             │
│                                                                              │
│  ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐    │
│  │ EndpointRegistry│ -> │ OpenAPI_Generator│ -> │ OpenAPI_Specification│   │
│  │   .collect()    │    │                  │    │   (JSON/YAML)        │   │
│  └─────────────────┘    └──────────────────┘    └─────────────────────┘    │
│                                │                                            │
│                                ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      Schema_Converter                                │   │
│  │  - dataclass -> JSON Schema                                         │   │
│  │  - Pydantic model -> JSON Schema                                    │   │
│  │  - Nested types -> $ref                                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                      Documentation Hosting                                   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Swagger_UI_Blueprint                              │   │
│  │  /docs          -> Swagger UI HTML                                  │   │
│  │  /openapi.json  -> Generated OpenAPI spec                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    ReDoc_Blueprint                                   │   │
│  │  /redoc         -> ReDoc HTML                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                      Specification Caching                                   │
│                                                                              │
│  ┌───────────────┐    ┌─────────────────┐    ┌──────────────────────┐      │
│  │ First Request │ -> │ Generate Spec   │ -> │ Cache Specification  │      │
│  └───────────────┘    └─────────────────┘    └──────────────────────┘      │
│                                                       │                     │
│  ┌───────────────┐    ┌─────────────────┐            │                     │
│  │ Next Request  │ -> │ Return Cached   │ <──────────┘                     │
│  └───────────────┘    └─────────────────┘                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### OpenAPI_Generator Class

```python
class OpenAPI_Generator:
    """
    Generates OpenAPI 3.0+ specifications from endpoint descriptors.
    """
    
    def __init__(
        self,
        registry: "EndpointRegistry",
        info: "OpenAPIInfo",
        servers: Optional[List["ServerObject"]] = None,
        security_schemes: Optional[Dict[str, "SecurityScheme"]] = None,
        tag_descriptions: Optional[Dict[str, str]] = None,
        external_docs: Optional["ExternalDocs"] = None
    ):
        self.registry = registry
        self.info = info
        self.servers = servers or []
        self.security_schemes = security_schemes or {}
        self.tag_descriptions = tag_descriptions or {}
        self.external_docs = external_docs
        self._schema_converter = Schema_Converter()
        self._cache: Optional[Dict[str, Any]] = None
    
    def generate(self) -> Dict[str, Any]:
        """
        Generate complete OpenAPI specification.
        
        Returns:
            OpenAPI specification as a dictionary.
        """
        pass
    
    def generate_json(self, indent: int = 2) -> str:
        """Generate specification as JSON string."""
        pass
    
    def generate_yaml(self) -> str:
        """Generate specification as YAML string."""
        pass
    
    def export(self, path: str, format: Optional[str] = None) -> None:
        """
        Export specification to file.
        
        Args:
            path: Output file path.
            format: 'json' or 'yaml', inferred from extension if not specified.
        """
        pass
    
    def validate(self, strict: bool = False) -> List["ValidationIssue"]:
        """
        Validate the generated specification.
        
        Args:
            strict: If True, treat warnings as errors.
        
        Returns:
            List of validation issues (empty if valid).
        
        Raises:
            SpecificationValidationError: If validation fails.
        """
        pass
    
    def refresh(self) -> None:
        """Invalidate cached specification."""
        self._cache = None
    
    def _build_paths(self) -> Dict[str, Any]:
        """Build paths object from endpoint descriptors."""
        pass
    
    def _build_operation(self, descriptor: "EndpointDescriptor", method: str) -> Dict[str, Any]:
        """Build operation object for a single endpoint method."""
        pass
    
    def _build_parameters(self, descriptor: "EndpointDescriptor") -> List[Dict[str, Any]]:
        """Build parameter objects from path and query parameters."""
        pass
    
    def _build_request_body(self, descriptor: "EndpointDescriptor") -> Optional[Dict[str, Any]]:
        """Build requestBody object from request_schema."""
        pass
    
    def _build_responses(self, descriptor: "EndpointDescriptor") -> Dict[str, Any]:
        """Build responses object including success and error responses."""
        pass
    
    def _build_security(self, descriptor: "EndpointDescriptor") -> Optional[List[Dict[str, List[str]]]]:
        """Build security requirements from access_policy."""
        pass
    
    def _collect_tags(self) -> List[Dict[str, str]]:
        """Collect and build tags array."""
        pass
    
    def _build_components(self) -> Dict[str, Any]:
        """Build components object with schemas and security schemes."""
        pass
```

### Schema_Converter Class

```python
class Schema_Converter:
    """
    Converts Python types to JSON Schema for OpenAPI specifications.
    """
    
    def __init__(self):
        self._schema_cache: Dict[str, Dict[str, Any]] = {}
        self._refs: Dict[str, str] = {}  # type -> $ref path
    
    def convert(self, python_type: Type) -> Dict[str, Any]:
        """
        Convert a Python type to JSON Schema.
        
        Args:
            python_type: Python type (dataclass, Pydantic model, or primitive).
        
        Returns:
            JSON Schema dictionary.
        """
        pass
    
    def get_ref(self, python_type: Type) -> str:
        """
        Get $ref path for a complex type.
        
        Args:
            python_type: Python type to reference.
        
        Returns:
            Reference path (e.g., "#/components/schemas/UserCreate").
        """
        pass
    
    def get_all_schemas(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all collected schemas for components/schemas section.
        
        Returns:
            Dictionary of schema name -> JSON Schema.
        """
        return dict(self._schema_cache)
    
    def _convert_dataclass(self, dc_type: Type) -> Dict[str, Any]:
        """Convert dataclass to JSON Schema."""
        pass
    
    def _convert_pydantic(self, model_type: Type) -> Dict[str, Any]:
        """Convert Pydantic model to JSON Schema."""
        pass
    
    def _convert_primitive(self, python_type: Type) -> Dict[str, Any]:
        """Convert primitive type to JSON Schema."""
        pass
    
    def _convert_list(self, item_type: Type) -> Dict[str, Any]:
        """Convert List[T] to JSON Schema array."""
        pass
    
    def _convert_dict(self, key_type: Type, value_type: Type) -> Dict[str, Any]:
        """Convert Dict[K, V] to JSON Schema object."""
        pass
    
    def _convert_optional(self, inner_type: Type) -> Dict[str, Any]:
        """Convert Optional[T] to nullable JSON Schema."""
        pass
    
    def _convert_union(self, types: Tuple[Type, ...]) -> Dict[str, Any]:
        """Convert Union[A, B, ...] to JSON Schema oneOf."""
        pass
    
    def _get_schema_name(self, python_type: Type) -> str:
        """Generate unique schema name from Python type."""
        pass


# Type mapping for primitives
PYTHON_TO_JSON_SCHEMA = {
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
```

### Swagger_UI_Blueprint Class

```python
class Swagger_UI_Blueprint(RestBlueprint):
    """
    Blueprint that serves Swagger UI and OpenAPI specification.
    """
    
    base_path = "/docs"
    
    def __init__(
        self,
        generator: OpenAPI_Generator,
        ui_path: str = "/docs",
        spec_path: str = "/openapi.json",
        try_it_out: bool = True,
        doc_expansion: str = "list",
        filter: bool = True,
        **swagger_config
    ):
        self.generator = generator
        self.ui_path = ui_path
        self.spec_path = spec_path
        self.try_it_out = try_it_out
        self.doc_expansion = doc_expansion
        self.filter = filter
        self.swagger_config = swagger_config
    
    @classmethod
    def register(cls, router: Optional["Router"] = None) -> List["EndpointDescriptor"]:
        """Register Swagger UI routes."""
        pass
    
    def serve_ui(self) -> "Response":
        """
        Serve Swagger UI HTML page.
        
        Returns:
            HTML response with Swagger UI.
        """
        pass
    
    def serve_spec(self) -> "Response":
        """
        Serve OpenAPI specification JSON.
        
        Returns:
            JSON response with OpenAPI spec.
        """
        pass
    
    def _build_swagger_html(self) -> str:
        """Build Swagger UI HTML with configuration."""
        pass
```

### ReDoc_Blueprint Class

```python
class ReDoc_Blueprint(RestBlueprint):
    """
    Blueprint that serves ReDoc documentation UI.
    """
    
    base_path = "/redoc"
    
    def __init__(
        self,
        generator: OpenAPI_Generator,
        ui_path: str = "/redoc",
        spec_url: str = "/openapi.json",
        **redoc_config
    ):
        self.generator = generator
        self.ui_path = ui_path
        self.spec_url = spec_url
        self.redoc_config = redoc_config
    
    @classmethod
    def register(cls, router: Optional["Router"] = None) -> List["EndpointDescriptor"]:
        """Register ReDoc routes."""
        pass
    
    def serve_ui(self) -> "Response":
        """
        Serve ReDoc HTML page.
        
        Returns:
            HTML response with ReDoc.
        """
        pass
    
    def _build_redoc_html(self) -> str:
        """Build ReDoc HTML with configuration."""
        pass
```

### Configuration Data Classes

```python
@dataclass
class OpenAPIInfo:
    """
    OpenAPI info object configuration.
    """
    
    title: str
    version: str
    description: Optional[str] = None
    terms_of_service: Optional[str] = None
    contact: Optional["ContactObject"] = None
    license: Optional["LicenseObject"] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to OpenAPI info object."""
        result = {
            "title": self.title,
            "version": self.version
        }
        if self.description:
            result["description"] = self.description
        if self.terms_of_service:
            result["termsOfService"] = self.terms_of_service
        if self.contact:
            result["contact"] = self.contact.to_dict()
        if self.license:
            result["license"] = self.license.to_dict()
        return result


@dataclass
class ContactObject:
    """OpenAPI contact object."""
    
    name: Optional[str] = None
    url: Optional[str] = None
    email: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {}
        if self.name:
            result["name"] = self.name
        if self.url:
            result["url"] = self.url
        if self.email:
            result["email"] = self.email
        return result


@dataclass
class LicenseObject:
    """OpenAPI license object."""
    
    name: str
    url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {"name": self.name}
        if self.url:
            result["url"] = self.url
        return result


@dataclass
class ServerObject:
    """OpenAPI server object."""
    
    url: str
    description: Optional[str] = None
    variables: Optional[Dict[str, "ServerVariable"]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {"url": self.url}
        if self.description:
            result["description"] = self.description
        if self.variables:
            result["variables"] = {
                k: v.to_dict() for k, v in self.variables.items()
            }
        return result


@dataclass
class ServerVariable:
    """OpenAPI server variable."""
    
    default: str
    enum: Optional[List[str]] = None
    description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {"default": self.default}
        if self.enum:
            result["enum"] = self.enum
        if self.description:
            result["description"] = self.description
        return result


@dataclass
class ExternalDocs:
    """OpenAPI external documentation object."""
    
    url: str
    description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {"url": self.url}
        if self.description:
            result["description"] = self.description
        return result
```

### Security Scheme Classes

```python
@dataclass
class SecurityScheme:
    """Base class for OpenAPI security schemes."""
    
    type: str
    description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {"type": self.type}
        if self.description:
            result["description"] = self.description
        return result


@dataclass
class APIKeySecurityScheme(SecurityScheme):
    """API key security scheme."""
    
    type: str = "apiKey"
    name: str = "X-API-Key"
    in_: str = "header"  # header, query, or cookie
    
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result["name"] = self.name
        result["in"] = self.in_
        return result


@dataclass
class HTTPSecurityScheme(SecurityScheme):
    """HTTP security scheme (bearer, basic)."""
    
    type: str = "http"
    scheme: str = "bearer"
    bearer_format: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result["scheme"] = self.scheme
        if self.bearer_format:
            result["bearerFormat"] = self.bearer_format
        return result


@dataclass
class OAuth2SecurityScheme(SecurityScheme):
    """OAuth2 security scheme."""
    
    type: str = "oauth2"
    flows: "OAuthFlows" = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        if self.flows:
            result["flows"] = self.flows.to_dict()
        return result


@dataclass
class OAuthFlows:
    """OAuth2 flows configuration."""
    
    implicit: Optional["OAuthFlow"] = None
    password: Optional["OAuthFlow"] = None
    client_credentials: Optional["OAuthFlow"] = None
    authorization_code: Optional["OAuthFlow"] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {}
        if self.implicit:
            result["implicit"] = self.implicit.to_dict()
        if self.password:
            result["password"] = self.password.to_dict()
        if self.client_credentials:
            result["clientCredentials"] = self.client_credentials.to_dict()
        if self.authorization_code:
            result["authorizationCode"] = self.authorization_code.to_dict()
        return result


@dataclass
class OAuthFlow:
    """Single OAuth2 flow configuration."""
    
    scopes: Dict[str, str]  # scope name -> description
    authorization_url: Optional[str] = None
    token_url: Optional[str] = None
    refresh_url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {"scopes": self.scopes}
        if self.authorization_url:
            result["authorizationUrl"] = self.authorization_url
        if self.token_url:
            result["tokenUrl"] = self.token_url
        if self.refresh_url:
            result["refreshUrl"] = self.refresh_url
        return result
```

### Validation Classes

```python
@dataclass
class ValidationIssue:
    """Single validation issue in the specification."""
    
    path: str  # JSON path to the issue location
    message: str
    severity: str  # "error" or "warning"


class SpecificationValidationError(Exception):
    """Raised when OpenAPI specification validation fails."""
    
    def __init__(self, issues: List[ValidationIssue]):
        self.issues = issues
        message = f"OpenAPI specification validation failed with {len(issues)} issue(s)"
        super().__init__(message)


class OpenAPIValidator:
    """
    Validates OpenAPI specifications against the schema.
    """
    
    def __init__(self, strict: bool = False):
        self.strict = strict
    
    def validate(self, spec: Dict[str, Any]) -> List[ValidationIssue]:
        """
        Validate an OpenAPI specification.
        
        Args:
            spec: OpenAPI specification dictionary.
        
        Returns:
            List of validation issues.
        
        Raises:
            SpecificationValidationError: If validation fails.
        """
        pass
    
    def _validate_structure(self, spec: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate basic structure requirements."""
        pass
    
    def _validate_refs(self, spec: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate all $ref references resolve."""
        pass
    
    def _validate_security(self, spec: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate security scheme references."""
        pass
    
    def _validate_schemas(self, spec: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate JSON Schema definitions."""
        pass
```

### Specification Cache

```python
class SpecificationCache:
    """
    Caches generated OpenAPI specifications.
    """
    
    def __init__(self, ttl: Optional[int] = None, production_mode: bool = False):
        self.ttl = ttl  # Time-to-live in seconds
        self.production_mode = production_mode
        self._cache: Optional[Dict[str, Any]] = None
        self._cache_time: Optional[float] = None
    
    def get(self) -> Optional[Dict[str, Any]]:
        """
        Get cached specification if valid.
        
        Returns:
            Cached specification or None if expired/missing.
        """
        if self._cache is None:
            return None
        
        if self.production_mode:
            return self._cache
        
        if self.ttl and self._cache_time:
            if time.time() - self._cache_time > self.ttl:
                self.invalidate()
                return None
        
        return self._cache
    
    def set(self, spec: Dict[str, Any]) -> None:
        """Cache a specification."""
        self._cache = spec
        self._cache_time = time.time()
    
    def invalidate(self) -> None:
        """Invalidate the cache."""
        self._cache = None
        self._cache_time = None


class CachedOpenAPIGenerator(OpenAPI_Generator):
    """
    OpenAPI generator with caching support.
    """
    
    def __init__(
        self,
        registry: "EndpointRegistry",
        info: "OpenAPIInfo",
        cache_ttl: Optional[int] = None,
        production_mode: bool = False,
        **kwargs
    ):
        super().__init__(registry, info, **kwargs)
        self._spec_cache = SpecificationCache(
            ttl=cache_ttl,
            production_mode=production_mode
        )
    
    def generate(self) -> Dict[str, Any]:
        """Generate specification with caching."""
        cached = self._spec_cache.get()
        if cached is not None:
            return cached
        
        spec = super().generate()
        self._spec_cache.set(spec)
        return spec
    
    def refresh(self) -> None:
        """Invalidate cache and regenerate."""
        self._spec_cache.invalidate()
```

## Data Models

### OpenAPI Specification Structure

```python
# OpenAPI 3.0 specification structure
OPENAPI_SPEC_TEMPLATE = {
    "openapi": "3.0.3",
    "info": {
        "title": "",
        "version": ""
    },
    "servers": [],
    "paths": {},
    "components": {
        "schemas": {},
        "securitySchemes": {}
    },
    "tags": [],
    "security": []
}

# Standard error response schema
REST_ERROR_SCHEMA = {
    "type": "object",
    "properties": {
        "error": {
            "type": "string",
            "description": "Error code"
        },
        "message": {
            "type": "string",
            "description": "Human-readable error message"
        },
        "details": {
            "type": "object",
            "description": "Additional error context",
            "additionalProperties": True
        },
        "field_errors": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "field": {"type": "string"},
                    "code": {"type": "string"},
                    "message": {"type": "string"}
                },
                "required": ["field", "code", "message"]
            }
        }
    },
    "required": ["error", "message"]
}

# Standard error responses
STANDARD_ERROR_RESPONSES = {
    "400": {
        "description": "Bad Request - Invalid input",
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/RESTError"}
            }
        }
    },
    "401": {
        "description": "Unauthorized - Authentication required",
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/RESTError"}
            }
        }
    },
    "403": {
        "description": "Forbidden - Insufficient permissions",
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/RESTError"}
            }
        }
    },
    "404": {
        "description": "Not Found - Resource does not exist",
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/RESTError"}
            }
        }
    },
    "500": {
        "description": "Internal Server Error",
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/RESTError"}
            }
        }
    }
}
```

### Swagger UI HTML Template

```python
SWAGGER_UI_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Swagger UI</title>
    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
    <script>
        window.onload = function() {{
            SwaggerUIBundle({{
                url: "{spec_url}",
                dom_id: '#swagger-ui',
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIBundle.SwaggerUIStandalonePreset
                ],
                layout: "StandaloneLayout",
                tryItOutEnabled: {try_it_out},
                docExpansion: "{doc_expansion}",
                filter: {filter},
                {extra_config}
            }});
        }};
    </script>
</body>
</html>
"""

REDOC_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - API Documentation</title>
    <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
    <style>
        body {{ margin: 0; padding: 0; }}
    </style>
</head>
<body>
    <redoc spec-url="{spec_url}" {extra_config}></redoc>
    <script src="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js"></script>
</body>
</html>
"""
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Schema Conversion Round-Trip

*For any* Python dataclass or Pydantic model, converting to JSON Schema and then validating a conforming JSON object against that schema SHALL accept all valid instances of the original type.

**Validates: Requirements 2.1, 2.2, 2.4**

### Property 2: Path Parameter Extraction

*For any* EndpointDescriptor with path parameters (e.g., `/users/{id:int}`), the generated OpenAPI path SHALL contain corresponding parameter objects with correct names and types.

**Validates: Requirements 3.1, 3.2**

### Property 3: Operation Completeness

*For any* EndpointDescriptor with multiple HTTP methods, the generated OpenAPI specification SHALL contain a separate operation object for each method, all with correct operationId, summary, and tags.

**Validates: Requirements 3.3, 3.4, 3.5, 3.6**

### Property 4: Security Scheme Consistency

*For any* endpoint with an access_policy, the generated operation SHALL reference security schemes that exist in the components/securitySchemes section.

**Validates: Requirements 4.1, 4.2, 4.3**

### Property 5: Specification Validity

*For any* generated OpenAPI specification, the output SHALL pass validation against the OpenAPI 3.0 JSON Schema without errors.

**Validates: Requirements 9.1, 9.5**

### Property 6: Export Format Consistency

*For any* OpenAPI specification, exporting to JSON and then parsing SHALL produce an equivalent dictionary to the original specification.

**Validates: Requirements 10.1, 10.2, 10.6**

### Property 7: Cache Consistency

*For any* cached specification, retrieving from cache SHALL return a specification equivalent to regenerating from the same endpoint registry state.

**Validates: Requirements 12.1, 12.2**

## Error Handling

### Generation Errors

| Error Type | Condition | Handling |
|------------|-----------|----------|
| SchemaConversionError | Cannot convert Python type to JSON Schema | Log warning, use generic object schema |
| CircularReferenceError | Circular type references detected | Use $ref to break cycle |
| InvalidPathError | Path format is invalid | Raise with path details |
| DuplicateOperationIdError | Two operations have same operationId | Append suffix to make unique |

### Validation Errors

| Error Type | Condition | Handling |
|------------|-----------|----------|
| MissingRefError | $ref points to undefined schema | Add to validation issues |
| InvalidSecuritySchemeError | Security requirement references undefined scheme | Add to validation issues |
| MissingRequiredFieldError | Required OpenAPI field is missing | Add to validation issues |
| InvalidSchemaError | JSON Schema is malformed | Add to validation issues |

### Runtime Errors

| Error Type | Condition | Handling |
|------------|-----------|----------|
| CacheError | Cache read/write fails | Fall back to regeneration |
| ExportError | Cannot write to file path | Raise with path and reason |
| YAMLSerializationError | Cannot serialize to YAML | Fall back to JSON |

## Testing Strategy

### Unit Tests

Unit tests verify specific examples and edge cases:

- Schema conversion for each supported Python type
- Path parameter parsing for various formats
- Security scheme extraction from access policies
- HTML template generation with various configurations
- Cache behavior (hit, miss, expiration, invalidation)

### Property-Based Tests

Property-based tests verify universal properties using the testbase framework:

1. **Schema Round-Trip**: Generate random dataclasses, convert to JSON Schema, validate conforming instances
2. **Path Extraction**: Generate random path patterns, verify parameter extraction
3. **Specification Validity**: Generate specifications from random endpoint sets, validate against OpenAPI schema
4. **Export Consistency**: Generate specifications, export to JSON/YAML, parse back, compare

### Integration Tests

Integration tests verify end-to-end behavior:

- Full specification generation from a sample endpoint registry
- Swagger UI serving and configuration
- ReDoc serving and configuration
- CLI export command execution
