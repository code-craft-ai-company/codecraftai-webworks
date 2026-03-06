# Requirements Document

## Introduction

This document specifies the requirements for the OpenAPI and Swagger UI feature. This feature provides automatic OpenAPI specification generation from endpoint descriptors and hosts a fully self-contained interactive Swagger UI for API exploration and testing.

A core design principle is that the package must be fully self-reliant. The Swagger UI and ReDoc assets (CSS, JavaScript, fonts) must be bundled within the package itself so that no external CDN requests are made at runtime. This enables the documentation UI to function in air-gapped environments, behind firewalls, and without internet connectivity.

The feature enables developers to automatically generate OpenAPI 3.0+ specifications from the endpoint registry without manual documentation, expose interactive API documentation via a locally-served Swagger UI, and maintain documentation that stays synchronized with the actual API implementation.

## Glossary

- **OpenAPI_Specification**: A machine-readable document (JSON or YAML) describing a REST API's endpoints, parameters, request/response schemas, authentication, and metadata following the OpenAPI 3.0+ standard.
- **Swagger_UI**: An interactive web-based interface that renders OpenAPI specifications and allows users to explore and test API endpoints directly from the browser.
- **Bundled_Assets**: The Swagger UI and ReDoc static files (JavaScript, CSS, fonts, images) vendored into the package distribution so they can be served without external network access.
- **EndpointDescriptor**: A dataclass containing handler reference, path, methods, schemas, and metadata collected during endpoint registration.
- **EndpointRegistry**: A module-level registry that collects all EndpointDescriptor objects from attach_at/attach_child calls.
- **Schema_Converter**: A component that converts Python types (dataclasses, Pydantic models) to JSON Schema for OpenAPI specification.
- **Security_Scheme**: An OpenAPI construct describing authentication methods (API key, OAuth2, HTTP bearer, etc.).
- **Tag**: A grouping mechanism in OpenAPI for organizing related endpoints.
- **Operation_Object**: An OpenAPI construct describing a single API operation (HTTP method + path combination).
- **Path_Item**: An OpenAPI construct describing all operations available at a single path.
- **Info_Object**: An OpenAPI construct containing API metadata (title, version, description, contact, license).
- **Server_Object**: An OpenAPI construct describing API server URLs and variables.

## Requirements

### Requirement 1: OpenAPI Specification Generation

**User Story:** As an API developer, I want automatic OpenAPI specification generation, so that my API documentation stays synchronized with the actual implementation without manual maintenance.

#### Acceptance Criteria

1. THE OpenAPI_Generator class SHALL produce a valid OpenAPI 3.0+ specification from the EndpointRegistry.
2. WHEN generate() is called, THE OpenAPI_Generator SHALL iterate all EndpointDescriptor objects and convert them to OpenAPI path items and operations.
3. THE generated specification SHALL include the info object with title, version, and description from configuration.
4. THE generated specification SHALL include server objects for configured API base URLs.
5. THE generated specification SHALL be exportable as both JSON and YAML formats.
6. WHEN an endpoint has request_schema defined, THE specification SHALL include the corresponding requestBody with JSON Schema.
7. WHEN an endpoint has response_schema defined, THE specification SHALL include the corresponding response with JSON Schema.

### Requirement 2: Schema Conversion

**User Story:** As an API developer, I want automatic schema conversion, so that my Python type definitions are accurately represented in the OpenAPI specification.

#### Acceptance Criteria

1. THE Schema_Converter SHALL convert Python dataclasses to JSON Schema format.
2. THE Schema_Converter SHALL convert Pydantic models to JSON Schema format using model_json_schema().
3. THE Schema_Converter SHALL handle nested schemas by generating $ref references to the components/schemas section.
4. THE Schema_Converter SHALL preserve field descriptions, defaults, and constraints in the generated JSON Schema.
5. THE Schema_Converter SHALL support common Python types: str, int, float, bool, List, Dict, Optional, Union.
6. WHEN a schema contains circular references, THE Schema_Converter SHALL handle them using $ref without infinite recursion.
7. THE Schema_Converter SHALL generate unique schema names based on the Python class name and module.

### Requirement 3: Path and Operation Generation

**User Story:** As an API developer, I want accurate path and operation generation, so that the OpenAPI specification correctly describes all my API endpoints.

#### Acceptance Criteria

1. THE OpenAPI_Generator SHALL convert EndpointDescriptor path attributes to OpenAPI path strings.
2. THE OpenAPI_Generator SHALL convert path parameters (e.g., {id:int}) to OpenAPI parameter objects with correct types.
3. WHEN an endpoint supports multiple HTTP methods, THE generator SHALL create separate operation objects for each method.
4. THE operation object SHALL include operationId derived from the handler function name.
5. THE operation object SHALL include summary and description from the endpoint's doc attribute.
6. THE operation object SHALL include tags from the endpoint's tags attribute.
7. WHEN an endpoint has query parameters, THE generator SHALL include them as parameter objects with in: query.

### Requirement 4: Security Scheme Documentation

**User Story:** As an API developer, I want security schemes documented, so that API consumers understand the authentication requirements for each endpoint.

#### Acceptance Criteria

1. THE OpenAPI_Generator SHALL extract security requirements from endpoint access_policy attributes.
2. THE specification SHALL include securitySchemes in the components section for all referenced authentication methods.
3. WHEN an endpoint requires authentication, THE operation SHALL include a security array referencing the required schemes.
4. THE generator SHALL support common security schemes: apiKey, http (bearer/basic), oauth2, openIdConnect.
5. WHEN an endpoint has no access_policy, THE operation SHALL indicate no security requirements (empty security array or omitted).
6. THE generator SHALL support scope requirements for OAuth2 security schemes.

### Requirement 5: Tag Organization

**User Story:** As an API developer, I want tag-based organization, so that related endpoints are grouped together in the documentation.

#### Acceptance Criteria

1. THE OpenAPI_Generator SHALL collect all unique tags from endpoint descriptors.
2. THE specification SHALL include a tags array with tag objects containing name and description.
3. WHEN an endpoint has tags defined, THE operation SHALL include those tags.
4. THE generator SHALL support tag descriptions via a tag_descriptions configuration mapping.
5. WHEN tags are not explicitly defined on an endpoint, THE generator SHALL optionally derive tags from the path hierarchy.

### Requirement 6: Error Response Documentation

**User Story:** As an API developer, I want error responses documented, so that API consumers understand possible error conditions and response formats.

#### Acceptance Criteria

1. THE OpenAPI_Generator SHALL include standard error responses (400, 401, 403, 404, 500) in operation responses.
2. WHEN an endpoint has an error_map defined, THE generator SHALL include those specific error responses.
3. THE error response schema SHALL reference the standard RESTError schema from components/schemas.
4. THE generator SHALL include response descriptions explaining each error condition.
5. THE generator SHALL support custom error schemas per endpoint when specified.

### Requirement 7: Bundled Static Asset Management

**User Story:** As an API developer, I want the Swagger UI and ReDoc assets bundled within the package, so that the documentation UI works without any external network access.

#### Acceptance Criteria

1. THE package SHALL include a vendored copy of the Swagger UI distribution files (swagger-ui-bundle.js, swagger-ui.css, and supporting assets) under `source/packages/automojo/webworks/openapi/static/swagger-ui/`.
2. THE package SHALL include a vendored copy of the ReDoc standalone JavaScript file under `source/packages/automojo/webworks/openapi/static/redoc/`.
3. THE static assets SHALL be included in the package distribution via `pyproject.toml` package-data configuration.
4. THE package SHALL provide a management script or CLI command (`webworks openapi update-assets`) that downloads the latest Swagger UI and ReDoc releases from their official GitHub repositories and updates the vendored copies.
5. THE asset update command SHALL record the downloaded version numbers in a manifest file (`static/manifest.json`) containing asset name, version, download URL, and SHA-256 checksum.
6. THE asset update command SHALL verify downloaded file integrity using SHA-256 checksums before overwriting vendored files.
7. THE vendored assets SHALL be committed to version control so that builds and deployments never require network access.
8. THE HTML templates SHALL reference the bundled assets via local URL paths (e.g., `/_swagger/swagger-ui-bundle.js`) rather than CDN URLs.

### Requirement 8: Swagger UI Hosting

**User Story:** As an API developer, I want Swagger UI hosted automatically from bundled assets, so that I can provide interactive documentation without additional setup or external dependencies.

#### Acceptance Criteria

1. THE Swagger_UI_Blueprint SHALL serve the bundled Swagger UI static assets at a configurable base path (default: `/_swagger/`).
2. THE Swagger_UI_Blueprint SHALL serve the Swagger UI HTML page at a configurable path (default: `/docs`).
3. THE Swagger_UI_Blueprint SHALL serve the OpenAPI specification at a configurable path (default: `/openapi.json`).
4. WHEN a user visits the Swagger UI path, THE system SHALL render the interactive documentation interface using only locally-served assets.
5. THE Swagger UI HTML page SHALL NOT contain any references to external CDNs, unpkg, or other remote asset sources.
6. THE Swagger_UI_Blueprint SHALL support enabling/disabling the "Try it out" feature via configuration.
7. THE Swagger_UI_Blueprint SHALL support custom Swagger UI configuration options (e.g., docExpansion, filter, defaultModelsExpandDepth).
8. THE static asset endpoint SHALL set appropriate Content-Type headers based on file extension (application/javascript for .js, text/css for .css, etc.).
9. THE static asset endpoint SHALL set Cache-Control headers to enable browser caching of immutable assets.
10. THE Swagger_UI_Blueprint SHALL serve a favicon for the documentation pages from the bundled assets.

### Requirement 9: Specification Customization

**User Story:** As an API developer, I want specification customization options, so that I can add additional metadata and customize the generated documentation.

#### Acceptance Criteria

1. THE OpenAPI_Generator SHALL accept an info configuration with title, version, description, termsOfService, contact, and license.
2. THE OpenAPI_Generator SHALL accept a servers configuration with URL templates and variables.
3. THE OpenAPI_Generator SHALL support external documentation links via externalDocs configuration.
4. THE generator SHALL support custom x- extension fields on operations and schemas.
5. THE generator SHALL support filtering endpoints by tag or path pattern for partial specification generation.
6. THE generator SHALL support merging additional OpenAPI content from external files.

### Requirement 10: Specification Validation

**User Story:** As an API developer, I want specification validation, so that I can ensure the generated OpenAPI document is valid before deployment.

#### Acceptance Criteria

1. THE OpenAPI_Generator SHALL validate the generated specification against the OpenAPI 3.0 schema.
2. WHEN validation fails, THE generator SHALL raise a SpecificationValidationError with details about the violations.
3. THE generator SHALL support a strict mode that fails on warnings (e.g., missing descriptions).
4. THE generator SHALL provide a validate() method that checks the specification without generating output.
5. THE validation SHALL detect missing schema references and undefined security schemes.

### Requirement 11: Specification Export

**User Story:** As an API developer, I want specification export capabilities, so that I can use the generated documentation with external tools and CI/CD pipelines.

#### Acceptance Criteria

1. THE OpenAPI_Generator SHALL support exporting the specification to a file path.
2. THE export SHALL support both JSON and YAML output formats based on file extension or explicit format parameter.
3. THE generator SHALL support a CLI command for specification generation (e.g., `webworks openapi generate`).
4. THE CLI command SHALL support output path, format, and filtering options.
5. THE generator SHALL support writing to stdout for pipeline integration.
6. THE export SHALL produce deterministic output (consistent ordering) for version control diffing.

### Requirement 12: ReDoc Alternative UI

**User Story:** As an API developer, I want an alternative documentation UI option, so that I can choose the documentation style that best fits my project.

#### Acceptance Criteria

1. THE ReDoc_Blueprint SHALL serve the bundled ReDoc static assets at a configurable path (default: `/redoc`).
2. THE ReDoc_Blueprint SHALL use the same OpenAPI specification as Swagger UI.
3. WHEN a user visits the ReDoc path, THE system SHALL render the ReDoc documentation interface using only locally-served assets.
4. THE ReDoc HTML page SHALL NOT contain any references to external CDNs or remote asset sources.
5. THE ReDoc_Blueprint SHALL support custom ReDoc configuration options.
6. THE system SHALL support enabling Swagger UI, ReDoc, or both simultaneously.

### Requirement 13: Specification Caching

**User Story:** As an API developer, I want specification caching, so that the OpenAPI document is not regenerated on every request.

#### Acceptance Criteria

1. THE OpenAPI_Generator SHALL cache the generated specification after first generation.
2. WHEN the cache is valid, THE Swagger_UI_Blueprint SHALL serve the cached specification.
3. THE cache SHALL be invalidated when endpoints are modified (development mode).
4. THE system SHALL support a cache_ttl configuration for time-based cache expiration.
5. THE system SHALL support manual cache invalidation via a refresh() method.
6. IN production mode, THE specification SHALL be generated once at startup and cached indefinitely.

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
