# Requirements Document

## Introduction

This document specifies the requirements for the REST API Support feature. This feature provides resource-oriented helpers, serialization/validation infrastructure, and a standard REST error model to simplify building RESTful APIs on top of the endpoint abstractions framework.

The feature enables developers to define REST resources with consistent CRUD operations, automatically serialize/deserialize request and response payloads using schema definitions, validate incoming data against schemas, and return standardized error responses that clients can reliably parse and handle.

## Glossary

- **Resource**: A REST resource representing a domain entity that can be accessed and manipulated via standard HTTP methods (GET, POST, PUT, PATCH, DELETE).
- **ResourceEndpoint**: A specialized endpoint class that provides resource-oriented helpers for CRUD operations on a single resource type.
- **CollectionEndpoint**: A specialized endpoint class for handling collections of resources with list, create, and bulk operations.
- **Serializer**: A component that converts Python objects to wire format (JSON, XML, etc.) for response bodies.
- **Deserializer**: A component that converts wire format data to Python objects for request bodies.
- **Schema**: A definition (dataclass, Pydantic model, or JSON Schema) describing the structure and validation rules for request/response payloads.
- **Validator**: A component that validates incoming data against a schema and reports validation errors.
- **ValidationError**: An exception raised when request data fails schema validation.
- **RESTError**: A standardized error response structure containing error code, message, details, and optional field-level errors.
- **ErrorMap**: A mapping of exception types to HTTP status codes and error response formats.
- **ContentNegotiation**: The process of selecting the appropriate serialization format based on Accept headers.
- **PaginationInfo**: Metadata about paginated collection responses including total count, page size, and navigation links.

## Requirements

### Requirement 1: Resource-Oriented Endpoint Helpers

**User Story:** As an API developer, I want resource-oriented endpoint helpers, so that I can quickly define CRUD operations with consistent patterns and reduced boilerplate.

#### Acceptance Criteria

1. THE ResourceEndpoint class SHALL provide helper methods for standard CRUD operations: `get`, `create`, `update`, `partial_update`, and `delete`.
2. THE ResourceEndpoint class SHALL automatically map HTTP methods to CRUD operations: GET to `get`, POST to `create`, PUT to `update`, PATCH to `partial_update`, DELETE to `delete`.
3. WHEN a ResourceEndpoint is attached, THE endpoint SHALL register routes for the configured CRUD operations based on the `allowed_methods` attribute.
4. THE ResourceEndpoint class SHALL support a `resource_name` attribute that determines the URL leaf (e.g., `resource_name="users"` yields `/users` and `/users/{id}`).
5. THE ResourceEndpoint class SHALL support an `id_param` attribute specifying the path parameter name and type for single-resource operations (default: `{id:int}`).
6. WHEN `allowed_methods` is not specified, THE ResourceEndpoint SHALL default to all CRUD operations.
7. WHEN `allowed_methods` is specified, THE ResourceEndpoint SHALL only register routes for the listed operations.

### Requirement 2: Collection Endpoint Helpers

**User Story:** As an API developer, I want collection endpoint helpers, so that I can handle list operations with pagination, filtering, and sorting support.

#### Acceptance Criteria

1. THE CollectionEndpoint class SHALL provide a `list` method for retrieving collections of resources.
2. THE CollectionEndpoint class SHALL support pagination via `page` and `page_size` query parameters.
3. THE CollectionEndpoint class SHALL support configurable default and maximum page sizes via `default_page_size` and `max_page_size` attributes.
4. THE CollectionEndpoint class SHALL support filtering via query parameters mapped to filter fields.
5. THE CollectionEndpoint class SHALL support sorting via `sort` query parameter with field names and direction (e.g., `sort=name,-created_at`).
6. WHEN a collection response is returned, THE response SHALL include PaginationInfo with `total`, `page`, `page_size`, `total_pages`, and navigation links (`next`, `prev`, `first`, `last`).
7. THE CollectionEndpoint class SHALL support bulk operations via `bulk_create`, `bulk_update`, and `bulk_delete` methods when enabled.

### Requirement 3: Request Serialization

**User Story:** As an API developer, I want automatic request deserialization, so that incoming JSON payloads are converted to typed Python objects without manual parsing.

#### Acceptance Criteria

1. WHEN a `request_schema` is specified on an endpoint, THE system SHALL automatically deserialize the request body to an instance of that schema.
2. THE system SHALL support dataclass schemas with automatic JSON deserialization.
3. THE system SHALL support Pydantic model schemas with automatic JSON deserialization and validation.
4. THE system SHALL support dict schemas for untyped JSON payloads.
5. WHEN deserialization fails due to malformed JSON, THE system SHALL raise a ValidationError with details about the parsing failure.
6. WHEN deserialization fails due to type mismatches, THE system SHALL raise a ValidationError with field-level error details.
7. THE deserialized object SHALL be passed to the handler as a parameter (e.g., `def create(self, payload: UserCreate)`).

### Requirement 4: Response Serialization

**User Story:** As an API developer, I want automatic response serialization, so that Python objects are converted to JSON responses without manual encoding.

#### Acceptance Criteria

1. WHEN a `response_schema` is specified on an endpoint, THE system SHALL automatically serialize the handler return value to JSON.
2. THE system SHALL support dataclass response schemas with automatic JSON serialization.
3. THE system SHALL support Pydantic model response schemas with automatic JSON serialization.
4. THE system SHALL support dict responses for untyped JSON payloads.
5. THE system SHALL support list responses for collection endpoints.
6. WHEN the handler returns None, THE system SHALL return an empty response with appropriate status code (204 No Content for DELETE).
7. THE serialized response SHALL include the appropriate Content-Type header (`application/json`).

### Requirement 5: Schema Validation

**User Story:** As an API developer, I want automatic request validation, so that invalid data is rejected before reaching my handler logic.

#### Acceptance Criteria

1. WHEN a `request_schema` with validation rules is specified, THE system SHALL validate incoming data against those rules.
2. THE system SHALL support Pydantic validation rules including type constraints, string patterns, numeric ranges, and custom validators.
3. THE system SHALL support dataclass field validation via `field()` metadata or post-init validation.
4. WHEN validation fails, THE system SHALL raise a ValidationError containing all field-level errors.
5. THE ValidationError SHALL include the field path, error code, and human-readable message for each validation failure.
6. THE system SHALL support nested schema validation for complex request payloads.
7. THE system SHALL support optional fields with default values.
8. THE system SHALL support required fields that must be present in the request.

### Requirement 6: Content Negotiation

**User Story:** As an API developer, I want content negotiation support, so that my API can serve different formats based on client preferences.

#### Acceptance Criteria

1. THE system SHALL inspect the `Accept` header to determine the preferred response format.
2. THE system SHALL support `application/json` as the default and primary format.
3. THE system SHALL support registering additional serializers for other formats (e.g., `application/xml`, `text/csv`).
4. WHEN the client requests an unsupported format, THE system SHALL return a 406 Not Acceptable response.
5. WHEN no `Accept` header is provided, THE system SHALL default to `application/json`.
6. THE system SHALL inspect the `Content-Type` header to determine the request body format.
7. WHEN the request `Content-Type` is unsupported, THE system SHALL return a 415 Unsupported Media Type response.

### Requirement 7: Standard REST Error Model

**User Story:** As an API consumer, I want standardized error responses, so that I can reliably parse and handle errors from any endpoint.

#### Acceptance Criteria

1. THE RESTError response structure SHALL include: `error` (error code string), `message` (human-readable description), `details` (optional additional context), and `field_errors` (optional list of field-level errors).
2. THE field_errors list SHALL contain objects with: `field` (field path), `code` (error code), and `message` (human-readable description).
3. WHEN a ValidationError is raised, THE system SHALL return a 400 Bad Request with field_errors populated.
4. WHEN a resource is not found, THE system SHALL return a 404 Not Found with error code `not_found`.
5. WHEN authentication fails, THE system SHALL return a 401 Unauthorized with error code `unauthorized`.
6. WHEN authorization fails, THE system SHALL return a 403 Forbidden with error code `forbidden`.
7. WHEN a method is not allowed, THE system SHALL return a 405 Method Not Allowed with error code `method_not_allowed` and an `Allow` header listing permitted methods.
8. WHEN an unhandled exception occurs, THE system SHALL return a 500 Internal Server Error with error code `internal_error`.
9. THE 500 response SHALL NOT expose internal error details in production mode.

### Requirement 8: Error Mapping

**User Story:** As an API developer, I want to map domain exceptions to HTTP errors, so that my business logic exceptions are automatically converted to appropriate REST responses.

#### Acceptance Criteria

1. THE system SHALL support an `error_map` attribute on endpoints mapping exception types to HTTP status codes and error codes.
2. WHEN an exception in the error_map is raised, THE system SHALL return the mapped status code with the mapped error code.
3. THE error_map SHALL support custom message templates with exception attribute interpolation.
4. THE system SHALL provide default mappings for common exceptions: `ValueError` to 400, `KeyError` to 404, `PermissionError` to 403.
5. WHEN an exception is not in the error_map, THE system SHALL fall back to the global error handler.
6. THE error_map SHALL be inheritable from parent endpoints with child maps extending or overriding parent mappings.

### Requirement 9: Response Status Codes

**User Story:** As an API developer, I want automatic status code selection, so that my handlers return appropriate HTTP status codes without explicit specification.

#### Acceptance Criteria

1. WHEN a GET request succeeds, THE system SHALL return 200 OK.
2. WHEN a POST request creates a resource, THE system SHALL return 201 Created.
3. WHEN a PUT or PATCH request updates a resource, THE system SHALL return 200 OK.
4. WHEN a DELETE request succeeds, THE system SHALL return 204 No Content.
5. THE system SHALL support a `status_code` attribute on endpoints to override the default status code.
6. THE system SHALL support returning a tuple of `(data, status_code)` from handlers to specify custom status codes.
7. WHEN a POST request does not create a resource (e.g., action endpoint), THE system SHALL return 200 OK.

### Requirement 10: Location Header for Created Resources

**User Story:** As an API consumer, I want Location headers on resource creation, so that I can discover the URL of newly created resources.

#### Acceptance Criteria

1. WHEN a resource is created via POST, THE response SHALL include a `Location` header with the URL of the created resource.
2. THE Location URL SHALL be constructed from the resource endpoint path and the created resource's identifier.
3. THE system SHALL support a `get_resource_url(resource)` method on ResourceEndpoint for customizing the Location URL.
4. WHEN the created resource has no identifier, THE Location header SHALL be omitted.

### Requirement 11: Partial Update Support

**User Story:** As an API developer, I want partial update support via PATCH, so that clients can update individual fields without sending the entire resource.

#### Acceptance Criteria

1. THE system SHALL support PATCH requests for partial updates using a `partial_update_schema` or the `request_schema` with all fields optional.
2. WHEN a PATCH request is received, THE system SHALL only update fields present in the request body.
3. THE system SHALL support JSON Merge Patch (RFC 7396) semantics where `null` values remove fields.
4. THE system SHALL validate partial updates against the schema with required fields relaxed.
5. THE system SHALL support a `partial=True` parameter on schema validation to enable partial update mode.

### Requirement 12: Bulk Operations

**User Story:** As an API developer, I want bulk operation support, so that clients can create, update, or delete multiple resources in a single request.

#### Acceptance Criteria

1. THE CollectionEndpoint class SHALL support `bulk_create` for creating multiple resources from a list payload.
2. THE CollectionEndpoint class SHALL support `bulk_update` for updating multiple resources identified by their IDs.
3. THE CollectionEndpoint class SHALL support `bulk_delete` for deleting multiple resources by ID list.
4. WHEN bulk operations are enabled, THE endpoint SHALL register appropriate routes (e.g., POST `/users/bulk`, DELETE `/users/bulk`).
5. THE bulk operation response SHALL include results for each item indicating success or failure.
6. WHEN any item in a bulk operation fails validation, THE system SHALL return errors for all failed items without processing any.
7. THE system SHALL support `atomic=True` option for bulk operations to roll back all changes on any failure.

</content>
</invoke>