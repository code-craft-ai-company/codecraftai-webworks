# Implementation Plan: OpenAPI and Swagger UI

## Overview

This implementation plan creates the OpenAPI specification generation and Swagger UI hosting feature. The implementation follows a bottom-up approach: first building the schema converter, then the specification generator, then the UI blueprints, and finally the CLI tooling.

## Tasks

- [ ] 1. Set up module structure and base classes
  - [ ] 1.1 Create `automojo.webworks.openapi` package with `__init__.py`
    - Create package directory structure
    - Export public API classes
    - _Requirements: 1.1_

  - [ ] 1.2 Create configuration dataclasses (OpenAPIInfo, ServerObject, etc.)
    - Implement OpenAPIInfo with title, version, description, contact, license
    - Implement ContactObject and LicenseObject
    - Implement ServerObject and ServerVariable
    - Implement ExternalDocs
    - _Requirements: 8.1, 8.2, 8.3_

  - [ ] 1.3 Create security scheme dataclasses
    - Implement SecurityScheme base class
    - Implement APIKeySecurityScheme
    - Implement HTTPSecurityScheme
    - Implement OAuth2SecurityScheme with OAuthFlows and OAuthFlow
    - _Requirements: 4.4_

- [ ] 2. Implement Schema_Converter
  - [ ] 2.1 Create Schema_Converter class with type mapping
    - Implement primitive type conversion (str, int, float, bool, etc.)
    - Implement PYTHON_TO_JSON_SCHEMA mapping
    - _Requirements: 2.5_

  - [ ] 2.2 Implement dataclass conversion
    - Extract fields from dataclass using dataclasses.fields()
    - Convert field types recursively
    - Preserve field descriptions and defaults
    - _Requirements: 2.1, 2.4_

  - [ ] 2.3 Implement Pydantic model conversion
    - Use model_json_schema() for Pydantic models
    - Handle nested model references
    - _Requirements: 2.2_

  - [ ] 2.4 Implement complex type handling
    - Implement List[T] to array conversion
    - Implement Dict[K, V] to object conversion
    - Implement Optional[T] to nullable schema
    - Implement Union[A, B] to oneOf schema
    - _Requirements: 2.5_

  - [ ] 2.5 Implement $ref handling for nested schemas
    - Generate unique schema names
    - Track schemas in cache for components/schemas
    - Handle circular references
    - _Requirements: 2.3, 2.6, 2.7_

  - [ ]* 2.6 Write property test for schema conversion round-trip
    - **Property 1: Schema Conversion Round-Trip**
    - **Validates: Requirements 2.1, 2.2, 2.4**

- [ ] 3. Checkpoint - Verify schema conversion
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 4. Implement OpenAPI_Generator core
  - [ ] 4.1 Create OpenAPI_Generator class skeleton
    - Initialize with registry, info, servers, security_schemes
    - Set up schema converter instance
    - _Requirements: 1.1_

  - [ ] 4.2 Implement path building from endpoint descriptors
    - Convert EndpointDescriptor paths to OpenAPI path format
    - Extract and convert path parameters
    - Group operations by path
    - _Requirements: 3.1, 3.2_

  - [ ]* 4.3 Write property test for path parameter extraction
    - **Property 2: Path Parameter Extraction**
    - **Validates: Requirements 3.1, 3.2**

  - [ ] 4.4 Implement operation building
    - Generate operationId from handler name
    - Include summary and description from doc attribute
    - Include tags from endpoint tags
    - _Requirements: 3.3, 3.4, 3.5, 3.6_

  - [ ] 4.5 Implement query parameter handling
    - Extract query parameters from endpoint metadata
    - Convert to OpenAPI parameter objects
    - _Requirements: 3.7_

  - [ ] 4.6 Implement request body building
    - Build requestBody from request_schema
    - Use schema converter for JSON Schema
    - _Requirements: 1.6_

  - [ ] 4.7 Implement response building
    - Build success response from response_schema
    - Include standard error responses
    - Include custom error responses from error_map
    - _Requirements: 1.7, 6.1, 6.2, 6.3, 6.4_

  - [ ]* 4.8 Write property test for operation completeness
    - **Property 3: Operation Completeness**
    - **Validates: Requirements 3.3, 3.4, 3.5, 3.6**

- [ ] 5. Implement security and tag handling
  - [ ] 5.1 Implement security extraction from access_policy
    - Extract authentication requirements
    - Map to security scheme references
    - _Requirements: 4.1, 4.3_

  - [ ] 5.2 Implement security schemes building
    - Build securitySchemes in components section
    - Support apiKey, http, oauth2 schemes
    - _Requirements: 4.2, 4.4_

  - [ ] 5.3 Implement scope handling for OAuth2
    - Extract scope requirements from access_policy
    - Include in security requirement objects
    - _Requirements: 4.6_

  - [ ]* 5.4 Write property test for security scheme consistency
    - **Property 4: Security Scheme Consistency**
    - **Validates: Requirements 4.1, 4.2, 4.3**

  - [ ] 5.5 Implement tag collection and building
    - Collect unique tags from all endpoints
    - Build tags array with descriptions
    - Support tag_descriptions configuration
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

  - [ ] 5.6 Implement automatic tag derivation from path
    - Derive tags from path hierarchy when not specified
    - _Requirements: 5.5_

- [ ] 6. Checkpoint - Verify generator core
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. Implement specification validation
  - [ ] 7.1 Create ValidationIssue and SpecificationValidationError classes
    - Implement ValidationIssue dataclass
    - Implement SpecificationValidationError exception
    - _Requirements: 9.2_

  - [ ] 7.2 Create OpenAPIValidator class
    - Implement structure validation
    - Implement $ref resolution validation
    - Implement security scheme reference validation
    - _Requirements: 9.1, 9.5_

  - [ ] 7.3 Implement strict mode validation
    - Check for missing descriptions
    - Check for missing examples
    - _Requirements: 9.3_

  - [ ] 7.4 Add validate() method to OpenAPI_Generator
    - Integrate validator with generator
    - Support strict parameter
    - _Requirements: 9.4_

  - [ ]* 7.5 Write property test for specification validity
    - **Property 5: Specification Validity**
    - **Validates: Requirements 9.1, 9.5**

- [ ] 8. Implement export functionality
  - [ ] 8.1 Implement JSON export
    - Add generate_json() method
    - Support indentation parameter
    - _Requirements: 1.5, 10.1_

  - [ ] 8.2 Implement YAML export
    - Add generate_yaml() method
    - Use PyYAML or ruamel.yaml
    - _Requirements: 1.5, 10.2_

  - [ ] 8.3 Implement file export
    - Add export() method with path and format
    - Infer format from file extension
    - Ensure deterministic output ordering
    - _Requirements: 10.1, 10.2, 10.6_

  - [ ]* 8.4 Write property test for export format consistency
    - **Property 6: Export Format Consistency**
    - **Validates: Requirements 10.1, 10.2, 10.6**

- [ ] 9. Implement specification caching
  - [ ] 9.1 Create SpecificationCache class
    - Implement get/set/invalidate methods
    - Support TTL-based expiration
    - Support production mode (no expiration)
    - _Requirements: 12.1, 12.4, 12.6_

  - [ ] 9.2 Create CachedOpenAPIGenerator class
    - Extend OpenAPI_Generator with caching
    - Implement refresh() method
    - _Requirements: 12.2, 12.5_

  - [ ] 9.3 Implement development mode cache invalidation
    - Detect endpoint modifications
    - Auto-invalidate on changes
    - _Requirements: 12.3_

  - [ ]* 9.4 Write property test for cache consistency
    - **Property 7: Cache Consistency**
    - **Validates: Requirements 12.1, 12.2**

- [ ] 10. Checkpoint - Verify generator complete
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 11. Implement Swagger UI Blueprint
  - [ ] 11.1 Create Swagger_UI_Blueprint class
    - Extend RestBlueprint
    - Configure ui_path and spec_path
    - _Requirements: 7.1, 7.2_

  - [ ] 11.2 Implement serve_ui() endpoint
    - Generate Swagger UI HTML
    - Configure Swagger UI options
    - _Requirements: 7.3, 7.4_

  - [ ] 11.3 Implement serve_spec() endpoint
    - Return cached OpenAPI specification
    - Set Content-Type to application/json
    - _Requirements: 7.2_

  - [ ] 11.4 Implement Swagger UI configuration options
    - Support try_it_out enable/disable
    - Support docExpansion, filter options
    - Support custom configuration
    - _Requirements: 7.5, 7.6_

  - [ ] 11.5 Implement blueprint registration
    - Register UI and spec routes
    - Support custom paths
    - _Requirements: 7.1, 7.2_

- [ ] 12. Implement ReDoc Blueprint
  - [ ] 12.1 Create ReDoc_Blueprint class
    - Extend RestBlueprint
    - Configure ui_path and spec_url
    - _Requirements: 11.1, 11.2_

  - [ ] 12.2 Implement serve_ui() endpoint
    - Generate ReDoc HTML
    - Configure ReDoc options
    - _Requirements: 11.3_

  - [ ] 12.3 Implement ReDoc configuration options
    - Support custom ReDoc configuration
    - _Requirements: 11.4_

  - [ ] 12.4 Support simultaneous UI hosting
    - Allow both Swagger UI and ReDoc
    - Share OpenAPI specification
    - _Requirements: 11.5_

- [ ] 13. Implement CLI tooling
  - [ ] 13.1 Create openapi CLI command group
    - Add to webworks CLI
    - _Requirements: 10.3_

  - [ ] 13.2 Implement generate subcommand
    - Accept output path parameter
    - Accept format parameter (json/yaml)
    - Accept filter options (tags, paths)
    - _Requirements: 10.3, 10.4_

  - [ ] 13.3 Implement stdout output
    - Support writing to stdout for pipelines
    - _Requirements: 10.5_

  - [ ] 13.4 Implement validate subcommand
    - Validate specification without export
    - Support strict mode flag
    - _Requirements: 9.4_

- [ ] 14. Final checkpoint - Verify complete implementation
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- The testbase framework should be used for all tests per repository conventions
