# Design Document: OpenAPI and Swagger UI

## Overview

This design document describes the architecture and implementation approach for the OpenAPI and Swagger UI feature. The feature provides automatic OpenAPI 3.0+ specification generation from endpoint descriptors and hosts interactive documentation via Swagger UI and ReDoc using fully bundled static assets.

Key design principles:
- Self-contained: All UI assets (JS, CSS, fonts) are vendored in the package — no CDN or external network access at runtime
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
│                      Bundled Static Asset Layer                               │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  openapi/static/swagger-ui/                                         │   │
│  │    swagger-ui-bundle.js                                             │   │
│  │    swagger-ui.css                                                   │   │
│  │    swagger-ui-standalone-preset.js (if needed by version)           │   │
│  │    favicon-32x32.png                                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  openapi/static/redoc/                                              │   │
│  │    redoc.standalone.js                                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  openapi/static/manifest.json                                       │   │
│  │    { asset_name, version, url, sha256 }                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                      Documentation Hosting                                   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Swagger_UI_Blueprint                              │   │
│  │  /docs              -> Swagger UI HTML (refs local assets)          │   │
│  │  /openapi.json      -> Generated OpenAPI spec                       │   │
│  │  /_swagger/<file>   -> Bundled static assets                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    ReDoc_Blueprint                                   │   │
│  │  /redoc             -> ReDoc HTML (refs local assets)               │   │
│  │  /_redoc/<file>     -> Bundled static assets                        │   │
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

### Static Asset Management

#### Directory Layout

```
source/packages/ccai/webworks/openapi/
├── static/
│   ├── manifest.json              # Asset versions and checksums
│   ├── swagger-ui/
│   │   ├── swagger-ui-bundle.js   # Main Swagger UI JS bundle
│   │   ├── swagger-ui.css         # Swagger UI stylesheet
│   │   └── favicon-32x32.png     # Swagger UI favicon
│   └── redoc/
│       └── redoc.standalone.js    # ReDoc standalone bundle
├── assets.py                      # Asset resolver and serving helpers
├── swaggerui.py                   # Swagger UI blueprint (updated)
├── redoc.py                       # ReDoc blueprint (updated)
└── ...                            # Existing modules unchanged
```

#### manifest.json Schema

```json
{
    "swagger-ui": {
        "version": "5.18.2",
        "files": {
            "swagger-ui-bundle.js": {
                "url": "https://github.com/swagger-api/swagger-ui/releases/...",
                "sha256": "abc123..."
            },
            "swagger-ui.css": {
                "url": "https://github.com/swagger-api/swagger-ui/releases/...",
                "sha256": "def456..."
            },
            "favicon-32x32.png": {
                "url": "https://github.com/swagger-api/swagger-ui/releases/...",
                "sha256": "ghi789..."
            }
        }
    },
    "redoc": {
        "version": "2.1.5",
        "files": {
            "redoc.standalone.js": {
                "url": "https://github.com/Redocly/redoc/releases/...",
                "sha256": "jkl012..."
            }
        }
    }
}
```

#### AssetResolver Class

```python
class AssetResolver:
    """
    Resolves and serves bundled static assets for Swagger UI and ReDoc.

    Uses the ``static/`` directory co-located with this module as the
    asset root.  All file reads use ``importlib.resources`` (or
    ``__file__``-relative paths) so the assets work from both source
    trees and installed wheels.
    """

    # MIME type mapping for static asset Content-Type headers
    MIME_TYPES = {
        ".js": "application/javascript",
        ".css": "text/css",
        ".png": "image/png",
        ".svg": "image/svg+xml",
        ".ico": "image/x-icon",
        ".json": "application/json",
        ".map": "application/json",
        ".woff": "font/woff",
        ".woff2": "font/woff2",
        ".ttf": "font/ttf",
    }

    def __init__(self):
        self._static_dir = os.path.join(os.path.dirname(__file__), "static")
        self._manifest = self._load_manifest()

    def _load_manifest(self) -> dict:
        """Load manifest.json from the static directory."""
        pass

    def resolve(self, asset_group: str, filename: str) -> Optional[bytes]:
        """
        Read a bundled asset file.

        :param asset_group: 'swagger-ui' or 'redoc'.
        :param filename: File name within the asset group directory.
        :returns: File contents as bytes, or None if not found.
        """
        pass

    def content_type(self, filename: str) -> str:
        """
        Determine the Content-Type for a filename based on extension.

        :param filename: The asset filename.
        :returns: MIME type string.
        """
        pass

    def verify_integrity(self) -> List[str]:
        """
        Verify all vendored assets match their manifest checksums.

        :returns: List of error messages (empty if all pass).
        """
        pass

    @property
    def swagger_ui_version(self) -> Optional[str]:
        """Return the vendored Swagger UI version from the manifest."""
        pass

    @property
    def redoc_version(self) -> Optional[str]:
        """Return the vendored ReDoc version from the manifest."""
        pass
```

### Updated Swagger_UI_Blueprint Class

```python
class SwaggerUIBlueprint(RestBlueprint):
    """
    Blueprint that serves Swagger UI from bundled assets and the
    OpenAPI specification.  No external CDN requests are made.
    """

    base_path = "/docs"

    def __init__(
        self,
        generator: "OpenAPIGenerator",
        ui_path: str = "/docs",
        spec_path: str = "/openapi.json",
        static_path: str = "/_swagger",
        try_it_out: bool = True,
        doc_expansion: str = "list",
        filter: bool = True,
        **swagger_config
    ):
        self.generator = generator
        self.ui_path = ui_path
        self.spec_path = spec_path
        self.static_path = static_path
        self.try_it_out = try_it_out
        self.doc_expansion = doc_expansion
        self.filter = filter
        self.swagger_config = swagger_config
        self._asset_resolver = AssetResolver()

    def serve_ui(self) -> Tuple[str, int, Dict[str, str]]:
        """Serve the Swagger UI HTML page referencing local assets."""
        pass

    def serve_spec(self) -> Tuple[str, int, Dict[str, str]]:
        """Serve the OpenAPI specification as JSON."""
        pass

    def serve_static(self, filename: str) -> Tuple[bytes, int, Dict[str, str]]:
        """
        Serve a bundled Swagger UI static asset.

        :param filename: The asset filename (e.g. 'swagger-ui-bundle.js').
        :returns: Tuple of (content_bytes, status_code, headers).
        """
        pass

    def _build_swagger_html(self) -> str:
        """
        Build Swagger UI HTML referencing local static paths.

        The generated HTML uses self.static_path for all JS/CSS
        references instead of CDN URLs.
        """
        pass

    def get_descriptors(self) -> List["EndpointDescriptor"]:
        """
        Create endpoint descriptors for UI, spec, and static routes.

        Returns descriptors for:
        - ui_path (GET) -> serve_ui
        - spec_path (GET) -> serve_spec
        - static_path/<filename> (GET) -> serve_static
        """
        pass
```

### Updated Swagger UI HTML Template

```python
SWAGGER_UI_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Swagger UI</title>
    <link rel="stylesheet" href="{static_path}/swagger-ui.css">
    <link rel="icon" type="image/png" href="{static_path}/favicon-32x32.png" sizes="32x32">
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="{static_path}/swagger-ui-bundle.js"></script>
    <script>
        window.onload = function() {{
            SwaggerUIBundle({{
                url: "{spec_url}",
                dom_id: '#swagger-ui',
                presets: [
                    SwaggerUIBundle.presets.apis
                ],
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
```

### Updated ReDoc_Blueprint Class

```python
class ReDocBlueprint(RestBlueprint):
    """
    Blueprint that serves ReDoc from bundled assets.
    No external CDN requests are made.
    """

    base_path = "/redoc"

    def __init__(
        self,
        generator: "OpenAPIGenerator",
        ui_path: str = "/redoc",
        spec_url: str = "/openapi.json",
        static_path: str = "/_redoc",
        **redoc_config
    ):
        self.generator = generator
        self.ui_path = ui_path
        self.spec_url = spec_url
        self.static_path = static_path
        self.redoc_config = redoc_config
        self._asset_resolver = AssetResolver()

    def serve_ui(self) -> Tuple[str, int, Dict[str, str]]:
        """Serve the ReDoc HTML page referencing local assets."""
        pass

    def serve_static(self, filename: str) -> Tuple[bytes, int, Dict[str, str]]:
        """Serve a bundled ReDoc static asset."""
        pass

    def _build_redoc_html(self) -> str:
        """Build ReDoc HTML referencing local static paths."""
        pass
```

### Updated ReDoc HTML Template

```python
REDOC_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - API Documentation</title>
    <style>
        body {{ margin: 0; padding: 0; }}
    </style>
</head>
<body>
    <redoc spec-url="{spec_url}" {extra_config}></redoc>
    <script src="{static_path}/redoc.standalone.js"></script>
</body>
</html>
"""
```

### Asset Update CLI Command

```python
class AssetUpdater:
    """
    Downloads and vendors the latest Swagger UI and ReDoc releases
    from their official GitHub repositories.

    Usage via CLI:
        webworks openapi update-assets
        webworks openapi update-assets --swagger-version 5.18.2
        webworks openapi update-assets --redoc-version 2.1.5
    """

    SWAGGER_UI_GITHUB = "swagger-api/swagger-ui"
    REDOC_GITHUB = "Redocly/redoc"

    SWAGGER_UI_FILES = [
        "swagger-ui-bundle.js",
        "swagger-ui.css",
        "favicon-32x32.png",
    ]

    REDOC_FILES = [
        "redoc.standalone.js",
    ]

    def __init__(self, static_dir: Optional[str] = None):
        self._static_dir = static_dir or os.path.join(
            os.path.dirname(__file__), "static"
        )

    def update_swagger_ui(self, version: Optional[str] = None) -> None:
        """
        Download Swagger UI distribution files from GitHub releases.

        :param version: Specific version to download, or None for latest.
        """
        pass

    def update_redoc(self, version: Optional[str] = None) -> None:
        """
        Download ReDoc standalone bundle from GitHub releases.

        :param version: Specific version to download, or None for latest.
        """
        pass

    def _download_file(self, url: str, dest: str) -> str:
        """
        Download a file and return its SHA-256 checksum.

        :param url: URL to download from.
        :param dest: Local file path to write to.
        :returns: Hex-encoded SHA-256 checksum of the downloaded content.
        """
        pass

    def _update_manifest(self, group: str, version: str,
                         files: Dict[str, Dict]) -> None:
        """
        Update manifest.json with new version and checksum info.

        :param group: 'swagger-ui' or 'redoc'.
        :param version: Version string.
        :param files: Dict of filename -> {url, sha256}.
        """
        pass

    def _get_latest_release(self, repo: str) -> str:
        """
        Query GitHub API for the latest release tag.

        :param repo: GitHub repo in 'owner/name' format.
        :returns: Version tag string.
        """
        pass
```

### Existing Components (Unchanged)

The following components from the existing design remain unchanged:

- **OpenAPI_Generator** — generates OpenAPI 3.0+ specs from EndpointRegistry
- **Schema_Converter** — converts Python types to JSON Schema
- **Configuration dataclasses** — OpenAPIInfo, ServerObject, ContactObject, etc.
- **Security scheme dataclasses** — SecurityScheme, APIKeySecurityScheme, HTTPSecurityScheme, OAuth2SecurityScheme
- **OpenAPIValidator** — validates generated specs against OpenAPI 3.0 schema
- **SpecificationCache / CachedOpenAPIGenerator** — caching layer
- **CLI commands** — generate, validate, export (plus new update-assets)

## Data Models

### OpenAPI Specification Structure

```python
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
```

## Correctness Properties

### Property 1: Self-Containment
For any deployment of the package, the Swagger UI and ReDoc documentation pages SHALL render correctly without making any HTTP requests to external hosts. All JavaScript, CSS, and font resources SHALL be served from the application's own endpoints.

### Property 2: Asset Integrity
For any vendored asset file, the SHA-256 checksum recorded in the manifest SHALL match the actual file content. The asset update command SHALL reject downloads whose checksums do not match expected values.

### Property 3: Specification Determinism
For any fixed set of endpoint descriptors and generator configuration, calling generate() multiple times SHALL produce byte-identical JSON output.

### Property 4: Content-Type Correctness
For any static asset request, the response Content-Type header SHALL match the file's actual MIME type (e.g., .js → application/javascript, .css → text/css, .png → image/png).

### Property 5: Specification Validity
For any set of valid endpoint descriptors, the generated OpenAPI specification SHALL pass validation against the OpenAPI 3.0 JSON Schema.

### Property 6: Schema Conversion Round-Trip
For any Python dataclass or Pydantic model, converting to JSON Schema and then validating a conforming JSON object against that schema SHALL accept all valid instances of the original type.

### Property 7: Path Parameter Extraction
For any EndpointDescriptor with path parameters, the generated OpenAPI path SHALL contain corresponding parameter objects with correct names and types.

### Property 8: Operation Completeness
For any EndpointDescriptor with multiple HTTP methods, the generated specification SHALL contain a separate operation object for each method with correct operationId, summary, and tags.

### Property 9: Security Scheme Consistency
For any endpoint with an access_policy, the generated operation SHALL reference security schemes that exist in the components/securitySchemes section.

### Property 10: Export Format Consistency
For any OpenAPI specification, exporting to JSON and then parsing SHALL produce an equivalent dictionary to the original specification.

### Property 11: Cache Consistency
For any cached specification, retrieving from cache SHALL return a specification equivalent to regenerating from the same endpoint registry state.

## Error Handling

### Asset Errors

| Error Type | Condition | Handling |
|------------|-----------|----------|
| AssetNotFoundError | Requested static file not in bundle | Return 404 response |
| AssetIntegrityError | Checksum mismatch during verification | Log warning, serve file anyway (non-fatal) |
| ManifestNotFoundError | manifest.json missing from static dir | Log warning, assets still servable by path |

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

- AssetResolver file resolution for each asset type
- AssetResolver Content-Type mapping for all supported extensions
- AssetResolver integrity verification (matching and mismatched checksums)
- Swagger UI HTML template contains only local asset references (no CDN URLs)
- ReDoc HTML template contains only local asset references (no CDN URLs)
- Static asset endpoint returns correct Content-Type and Cache-Control headers
- Schema conversion for each supported Python type
- Path parameter parsing for various formats
- Security scheme extraction from access policies
- Cache behavior (hit, miss, expiration, invalidation)

### Property-Based Tests

Property-based tests verify universal properties using the testbase framework:

1. **Self-Containment**: For generated HTML pages, verify no `src` or `href` attributes reference external domains
2. **Asset Integrity**: For all manifest entries, verify SHA-256 checksums match file contents
3. **Content-Type Correctness**: For all supported file extensions, verify correct MIME type mapping
4. **Schema Round-Trip**: Generate random dataclasses, convert to JSON Schema, validate conforming instances
5. **Path Extraction**: Generate random path patterns, verify parameter extraction
6. **Specification Validity**: Generate specifications from random endpoint sets, validate against OpenAPI schema
7. **Export Consistency**: Generate specifications, export to JSON/YAML, parse back, compare

### Integration Tests

- Full specification generation from a sample endpoint registry
- Swagger UI serving from bundled assets (verify no external requests)
- ReDoc serving from bundled assets (verify no external requests)
- Static asset serving with correct headers
- CLI export command execution
- CLI update-assets command execution (with mocked HTTP)
