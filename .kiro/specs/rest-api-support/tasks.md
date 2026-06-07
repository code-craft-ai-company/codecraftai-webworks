# Implementation Plan: REST API Support

## Overview

This implementation plan creates the REST API Support feature providing resource-oriented helpers, serialization/validation infrastructure, and a standard REST error model. The implementation builds on the endpoint-abstractions feature and integrates with the router-request-handling feature.

## Tasks

- [x] 1. Create core data models and error classes
  - [x] 1.1 Create `RESTError` dataclass with error, message, details, and field_errors fields
    - Implement `to_dict()` method for serialization
    - _Requirements: 7.1, 7.2_

  - [x] 1.2 Create `FieldError` dataclass with field, code, and message fields
    - _Requirements: 5.5, 7.2_

  - [x] 1.3 Create `ValidationError` exception class with message and field_errors
    - _Requirements: 5.4_

  - [x] 1.4 Create `ErrorMapping` dataclass with status_code, error_code, and message_template
    - Implement `build_response()` method with attribute interpolation
    - _Requirements: 8.1, 8.3_

  - [x] 1.5 Write property test for RESTError serialization round-trip
    - **Property 3: Response Serialization Round-Trip**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**

- [x] 2. Implement serialization infrastructure
  - [x] 2.1 Create `Serializer` and `Deserializer` protocol classes
    - Define content_type attribute and serialize/deserialize methods
    - _Requirements: 4.1, 3.1_

  - [x] 2.2 Implement `JSONSerializer` class
    - Support dict, dataclass, Pydantic model, and list serialization
    - _Requirements: 4.2, 4.3, 4.4, 4.5_

  - [x] 2.3 Implement `JSONDeserializer` class
    - Support dict, dataclass, and Pydantic model deserialization
    - Raise ValidationError on parse or type errors
    - _Requirements: 3.2, 3.3, 3.4, 3.5, 3.6_

  - [x] 2.4 Create `SerializerRegistry` class
    - Implement register_serializer, register_deserializer, get_serializer, get_deserializer
    - Implement negotiate_content_type for Accept header parsing
    - _Requirements: 6.3_

  - [x] 2.5 Write property test for JSON serialization round-trip
    - **Property 2: Request Deserialization Round-Trip**
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.4**

- [x] 3. Implement validation infrastructure
  - [x] 3.1 Create `Validator` class with validate method
    - Support partial=True parameter for partial updates
    - _Requirements: 5.1, 11.5_

  - [x] 3.2 Implement Pydantic model validation in Validator
    - Use model_validate() and capture validation errors
    - _Requirements: 5.2_

  - [x] 3.3 Implement dataclass validation in Validator
    - Support field metadata and post-init validation
    - _Requirements: 5.3_

  - [x] 3.4 Implement nested schema validation
    - Recursively validate nested objects with field path tracking
    - _Requirements: 5.6_

  - [x] 3.5 Write property test for validation error structure
    - **Property 4: Validation Error Structure**
    - **Validates: Requirements 5.4, 5.5**

- [x] 4. Implement error handling
  - [x] 4.1 Create `ErrorHandler` class with default mappings
    - Include mappings for ValueError, KeyError, PermissionError, ValidationError
    - _Requirements: 8.4_

  - [x] 4.2 Implement `handle()` method in ErrorHandler
    - Check endpoint error_map first, then global mappings, then fallback
    - _Requirements: 8.2, 8.5_

  - [x] 4.3 Implement error_map inheritance for endpoints
    - Merge parent and child error maps with child override
    - _Requirements: 8.6_

  - [x] 4.4 Implement production mode error hiding
    - Hide internal error details when debug=False
    - _Requirements: 7.9_

  - [x] 4.5 Write property test for error response status code mapping
    - **Property 7: Error Response Status Code Mapping**
    - **Validates: Requirements 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 8.1, 8.2**

- [x] 5. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Implement content negotiation
  - [x] 6.1 Create `ContentNegotiator` class
    - Implement select_response_format from Accept header
    - Implement validate_request_format for Content-Type
    - _Requirements: 6.1, 6.6_

  - [x] 6.2 Create `NotAcceptable` exception (406)
    - Include list of supported formats in response
    - _Requirements: 6.4_

  - [x] 6.3 Create `UnsupportedMediaType` exception (415)
    - Include unsupported type and supported formats in response
    - _Requirements: 6.7_

  - [x] 6.4 Implement default to application/json when no Accept header
    - _Requirements: 6.2, 6.5_

  - [x] 6.5 Write property test for content negotiation selection
    - **Property 6: Content Negotiation Selection**
    - **Validates: Requirements 6.1, 6.4, 6.5**

- [x] 7. Implement ResourceEndpoint class
  - [x] 7.1 Create `ResourceEndpoint` class extending RestEndpoint
    - Define resource_name, id_param, allowed_methods, request_schema, response_schema attributes
    - _Requirements: 1.1, 1.4, 1.5_

  - [x] 7.2 Implement CRUD method stubs (get, create, update, partial_update, delete)
    - Raise NotImplementedError for subclass implementation
    - _Requirements: 1.1_

  - [x] 7.3 Implement HTTP method to CRUD operation mapping
    - Map GET→get, POST→create, PUT→update, PATCH→partial_update, DELETE→delete
    - _Requirements: 1.2_

  - [x] 7.4 Implement `register()` method for route registration
    - Register routes based on allowed_methods configuration
    - _Requirements: 1.3, 1.6, 1.7_

  - [x] 7.5 Implement `get_resource_url()` method for Location header
    - _Requirements: 10.3_

  - [x] 7.6 Write property test for HTTP method to CRUD operation mapping
    - **Property 1: HTTP Method to CRUD Operation Mapping**
    - **Validates: Requirements 1.2, 1.3, 1.7**

- [x] 8. Implement response helpers
  - [x] 8.1 Create `PaginationInfo` dataclass
    - Include total, page, page_size, total_pages, and navigation links
    - Implement `create()` classmethod for computed fields
    - _Requirements: 2.6_

  - [x] 8.2 Create `PaginatedResponse` dataclass
    - Include items list and PaginationInfo
    - Implement `to_dict()` method
    - _Requirements: 2.6_

  - [x] 8.3 Implement status code selection logic
    - Map HTTP methods to default status codes
    - Support status_code attribute override
    - Support (data, status_code) tuple returns
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7_

  - [x] 8.4 Implement Location header generation for POST/201 responses
    - _Requirements: 10.1, 10.2, 10.4_

  - [x] 8.5 Write property test for HTTP method to status code mapping
    - **Property 8: HTTP Method to Status Code Mapping**
    - **Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5**

  - [x] 8.6 Write property test for pagination consistency
    - **Property 9: Pagination Consistency**
    - **Validates: Requirements 2.2, 2.3, 2.6**

- [x] 9. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Implement CollectionEndpoint class
  - [x] 10.1 Create `CollectionEndpoint` class extending ResourceEndpoint
    - Define default_page_size, max_page_size, filter_fields, sort_fields attributes
    - _Requirements: 2.1, 2.3_

  - [x] 10.2 Implement `list()` method with pagination support
    - Parse page and page_size query parameters
    - Enforce max_page_size limit
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 10.3 Implement filtering support
    - Parse filter query parameters based on filter_fields
    - _Requirements: 2.4_

  - [x] 10.4 Implement sorting support
    - Parse sort query parameter with field names and direction
    - _Requirements: 2.5_

- [x] 11. Implement partial update support
  - [x] 11.1 Implement partial_update_schema handling
    - Use partial_update_schema or request_schema with partial=True
    - _Requirements: 11.1_

  - [x] 11.2 Implement JSON Merge Patch semantics
    - Handle null values as field removal
    - _Requirements: 11.3_

  - [x] 11.3 Write property test for partial update field preservation
    - **Property 5: Partial Update Field Preservation**
    - **Validates: Requirements 11.2, 11.4**

- [x] 12. Implement bulk operations
  - [x] 12.1 Create `BulkOperationResult` and `BulkItemError` dataclasses
    - _Requirements: 12.5_

  - [x] 12.2 Implement `bulk_create()` method in CollectionEndpoint
    - _Requirements: 12.1_

  - [x] 12.3 Implement `bulk_update()` method in CollectionEndpoint
    - _Requirements: 12.2_

  - [x] 12.4 Implement `bulk_delete()` method in CollectionEndpoint
    - _Requirements: 12.3_

  - [x] 12.5 Implement bulk route registration when bulk_enabled=True
    - _Requirements: 12.4_

  - [x] 12.6 Implement atomic bulk operations with rollback
    - _Requirements: 12.7_

  - [x] 12.7 Implement validation-first bulk processing
    - Validate all items before processing any
    - _Requirements: 12.6_

  - [x] 12.8 Write property test for bulk operation results
    - **Property 10: Bulk Operation Results**
    - **Validates: Requirements 12.1, 12.2, 12.3, 12.5, 12.6**

- [x] 13. Implement REST middleware
  - [x] 13.1 Create `RESTMiddleware` class
    - Wire together serialization, validation, error handling, and content negotiation
    - _Requirements: 3.7, 4.7_

  - [x] 13.2 Implement request deserialization in middleware
    - Deserialize and validate request body based on endpoint schema
    - _Requirements: 3.1, 5.1_

  - [x] 13.3 Implement response serialization in middleware
    - Serialize response based on Accept header and endpoint schema
    - _Requirements: 4.1, 6.1_

  - [x] 13.4 Implement error handling in middleware
    - Catch exceptions and convert to RESTError responses
    - _Requirements: 7.3, 7.8_

  - [x] 13.5 Write property test for Location header generation
    - **Property 11: Location Header for Created Resources**
    - **Validates: Requirements 10.1, 10.2, 10.4**

  - [x] 13.6 Write property test for error map inheritance
    - **Property 12: Error Map Inheritance**
    - **Validates: Requirements 8.6**

- [x] 14. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- Implementation uses Python with testbase framework per repository conventions
- Test files should be located at `source/testroots/ccai/tests/singlehost/webworks/rest/`
