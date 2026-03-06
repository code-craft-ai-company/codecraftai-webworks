# Implementation Plan: OpenAPI and Swagger UI

## Overview

This implementation plan updates the OpenAPI specification generation and Swagger UI hosting feature to use fully bundled static assets instead of CDN references. The plan preserves all existing generation, validation, caching, and CLI functionality while adding a vendored asset layer, an asset resolver, and updated HTML templates that reference local paths. New tasks focus on the static asset infrastructure; existing completed tasks are retained for traceability.

## Tasks

- [x] 1. Set up module structure and base classes
  - [x] 1.1 Create `automojo.webworks.openapi` package with `__init__.py`
  - [x] 1.2 Create configuration dataclasses (OpenAPIInfo, ServerObject, etc.)
  - [x] 1.3 Create security scheme dataclasses

- [x] 2. Implement Schema_Converter
  - [x] 2.1 Create Schema_Converter class with type mapping
  - [x] 2.2 Implement dataclass conversion
  - [x] 2.3 Implement Pydantic model conversion
  - [x] 2.4 Implement complex type handling
  - [x] 2.5 Implement $ref handling for nested schemas
  - [x] 2.6 Write property test for schema conversion round-trip

- [x] 3. Checkpoint - Verify schema conversion

- [x] 4. Implement OpenAPI_Generator core
  - [x] 4.1 Create OpenAPI_Generator class skeleton
  - [x] 4.2 Implement path building from endpoint descriptors
  - [x] 4.3 Write property test for path parameter extraction
  - [x] 4.4 Implement operation building
  - [x] 4.5 Implement query parameter handling
  - [x] 4.6 Implement request body building
  - [x] 4.7 Implement response building
  - [x] 4.8 Write property test for operation completeness

- [x] 5. Implement security and tag handling
  - [x] 5.1 Implement security extraction from access_policy
  - [x] 5.2 Implement security schemes building
  - [x] 5.3 Implement scope handling for OAuth2
  - [x] 5.4 Write property test for security scheme consistency
  - [x] 5.5 Implement tag collection and building
  - [x] 5.6 Implement automatic tag derivation from path

- [x] 6. Checkpoint - Verify generator core

- [x] 7. Implement specification validation
  - [x] 7.1 Create ValidationIssue and SpecificationValidationError classes
  - [x] 7.2 Create OpenAPIValidator class
  - [x] 7.3 Implement strict mode validation
  - [x] 7.4 Add validate() method to OpenAPI_Generator
  - [x] 7.5 Write property test for specification validity

- [x] 8. Implement export functionality
  - [x] 8.1 Implement JSON export
  - [x] 8.2 Implement YAML export
  - [x] 8.3 Implement file export
  - [x] 8.4 Write property test for export format consistency

- [x] 9. Implement specification caching
  - [x] 9.1 Create SpecificationCache class
  - [x] 9.2 Create CachedOpenAPIGenerator class
  - [x] 9.3 Implement development mode cache invalidation
  - [x] 9.4 Write property test for cache consistency

- [x] 10. Checkpoint - Verify generator complete

- [x] 11. Vendor static assets and create asset resolver
  - [x] 11.1 Create static asset directory structure
    - Create `source/packages/automojo/webworks/openapi/static/swagger-ui/`
    - Create `source/packages/automojo/webworks/openapi/static/redoc/`
    - Create `source/packages/automojo/webworks/openapi/static/manifest.json` with empty structure
    - _Requirements: 7.1, 7.2_

  - [x] 11.2 Download and vendor Swagger UI distribution files
    - Download `swagger-ui-bundle.js`, `swagger-ui.css`, `favicon-32x32.png` from the latest Swagger UI GitHub release
    - Place files in `static/swagger-ui/`
    - Record version, download URLs, and SHA-256 checksums in `manifest.json`
    - _Requirements: 7.1, 7.5, 7.6_

  - [x] 11.3 Download and vendor ReDoc standalone bundle
    - Download `redoc.standalone.js` from the latest ReDoc GitHub release
    - Place file in `static/redoc/`
    - Record version, download URL, and SHA-256 checksum in `manifest.json`
    - _Requirements: 7.2, 7.5, 7.6_

  - [x] 11.4 Create `AssetResolver` class in `source/packages/automojo/webworks/openapi/assets.py`
    - Implement `resolve(asset_group, filename)` to read bundled files using `__file__`-relative paths
    - Implement `content_type(filename)` with MIME type mapping for .js, .css, .png, .svg, .ico, .json, .woff, .woff2, .ttf
    - Implement `verify_integrity()` to check SHA-256 checksums against manifest
    - Implement `swagger_ui_version` and `redoc_version` properties
    - _Requirements: 7.1, 7.2, 7.5, 7.6, 8.8_

  - [x] 11.5 Write unit tests for AssetResolver
    - Create `source/testroots/automojo/tests/singlehost/webworks/openapi/test_assets.py`
    - Test `resolve` returns bytes for each vendored file
    - Test `resolve` returns None for non-existent files
    - Test `content_type` returns correct MIME type for each supported extension
    - Test `verify_integrity` passes for unmodified vendored files
    - Test `swagger_ui_version` and `redoc_version` return version strings from manifest
    - _Requirements: 7.1, 7.2, 7.5, 7.6, 8.8_

  - [x] 11.6 Write property test for Content-Type correctness
    - **Property 4: Content-Type Correctness**
    - For all supported file extensions, verify the MIME type mapping returns the correct Content-Type
    - **Validates: Requirements 8.8**

  - [x] 11.7 Write property test for asset integrity
    - **Property 2: Asset Integrity**
    - For all entries in manifest.json, verify the SHA-256 checksum matches the actual file content
    - **Validates: Requirements 7.5, 7.6**

- [x] 12. Checkpoint - Verify asset resolver and vendored files

- [x] 13. Update Swagger UI Blueprint to serve bundled assets
  - [x] 13.1 Update `SwaggerUIBlueprint.__init__` to accept `static_path` parameter
    - Add `static_path` parameter (default: `/_swagger`)
    - Instantiate `AssetResolver` internally
    - _Requirements: 8.1_

  - [x] 13.2 Update `_build_swagger_html` to reference local asset paths
    - Replace CDN URLs with `{static_path}/swagger-ui-bundle.js` and `{static_path}/swagger-ui.css`
    - Add favicon link referencing `{static_path}/favicon-32x32.png`
    - Remove `SwaggerUIStandalonePreset` and `StandaloneLayout` references
    - _Requirements: 8.4, 8.5_

  - [x] 13.3 Implement `serve_static` method
    - Accept filename parameter, delegate to `AssetResolver.resolve("swagger-ui", filename)`
    - Set Content-Type header from `AssetResolver.content_type(filename)`
    - Set `Cache-Control: public, max-age=31536000, immutable` header
    - Return 404 if file not found
    - _Requirements: 8.1, 8.8, 8.9_

  - [x] 13.4 Update `get_descriptors` to include static asset route
    - Add an EndpointDescriptor for `{static_path}/<filename>` (GET) pointing to `serve_static`
    - _Requirements: 8.1_

  - [x] 13.5 Write unit tests for updated SwaggerUIBlueprint
    - Test `_build_swagger_html` output contains no external CDN references
    - Test `_build_swagger_html` output references `static_path` for JS and CSS
    - Test `serve_static` returns correct Content-Type and Cache-Control headers
    - Test `serve_static` returns 404 for non-existent files
    - Test `get_descriptors` includes UI, spec, and static routes
    - _Requirements: 8.1, 8.4, 8.5, 8.8, 8.9_

  - [x] 13.6 Write property test for self-containment
    - **Property 1: Self-Containment**
    - For generated Swagger UI HTML, verify no `src` or `href` attributes reference external domains (only relative paths)
    - **Validates: Requirements 8.4, 8.5**

- [x] 14. Update ReDoc Blueprint to serve bundled assets
  - [x] 14.1 Update `ReDocBlueprint.__init__` to accept `static_path` parameter
    - Add `static_path` parameter (default: `/_redoc`)
    - Instantiate `AssetResolver` internally
    - _Requirements: 12.1_

  - [x] 14.2 Update `_build_redoc_html` to reference local asset paths
    - Replace CDN URL with `{static_path}/redoc.standalone.js`
    - Remove Google Fonts CDN link
    - _Requirements: 12.3, 12.4_

  - [x] 14.3 Implement `serve_static` method for ReDoc
    - Accept filename parameter, delegate to `AssetResolver.resolve("redoc", filename)`
    - Set Content-Type and Cache-Control headers
    - Return 404 if file not found
    - _Requirements: 12.1_

  - [x] 14.4 Update `get_descriptors` to include static asset route
    - Add an EndpointDescriptor for `{static_path}/<filename>` (GET) pointing to `serve_static`
    - _Requirements: 12.1_

  - [x] 14.5 Write unit tests for updated ReDocBlueprint
    - Test `_build_redoc_html` output contains no external CDN references
    - Test `_build_redoc_html` output references `static_path` for JS
    - Test `serve_static` returns correct Content-Type and Cache-Control headers
    - Test `serve_static` returns 404 for non-existent files
    - _Requirements: 12.1, 12.3, 12.4_

  - [x] 14.6 Write property test for ReDoc self-containment
    - For generated ReDoc HTML, verify no `src` or `href` attributes reference external domains
    - **Validates: Requirements 12.3, 12.4**

- [x] 15. Checkpoint - Verify updated UI blueprints serve from bundled assets

- [x] 16. Implement asset update CLI command
  - [x] 16.1 Create `AssetUpdater` class in `source/packages/automojo/webworks/openapi/assets.py`
    - Implement `update_swagger_ui(version=None)` to download from GitHub releases
    - Implement `update_redoc(version=None)` to download from GitHub releases
    - Implement `_download_file(url, dest)` returning SHA-256 checksum
    - Implement `_update_manifest(group, version, files)` to write manifest.json
    - Implement `_get_latest_release(repo)` to query GitHub API for latest tag
    - _Requirements: 7.4, 7.5, 7.6_

  - [x] 16.2 Add `update-assets` subcommand to the openapi CLI group
    - Accept `--swagger-version` and `--redoc-version` optional arguments
    - Call `AssetUpdater.update_swagger_ui()` and `AssetUpdater.update_redoc()`
    - Print summary of downloaded versions and checksums
    - _Requirements: 7.4_

  - [x] 16.3 Write unit tests for AssetUpdater
    - Test `_get_latest_release` parses GitHub API response (mock HTTP)
    - Test `_download_file` computes correct SHA-256 (mock HTTP)
    - Test `_update_manifest` writes valid JSON with correct structure
    - Test `update_swagger_ui` downloads all expected files (mock HTTP)
    - Test `update_redoc` downloads expected file (mock HTTP)
    - _Requirements: 7.4, 7.5, 7.6_

- [x] 17. Update pyproject.toml for package-data inclusion
  - [x] 17.1 Add `static/**/*` to package-data in pyproject.toml
    - Ensure `manifest.json` and all vendored asset files are included in the distribution
    - _Requirements: 7.3_

- [x] 18. Update blueprintdemo test site to use bundled assets
  - [x] 18.1 Verify blueprintdemo `/docs` page loads without external requests
    - Start the blueprintdemo dev server
    - Confirm Swagger UI renders using only local `/_swagger/` asset paths
    - Confirm no network errors in browser console
    - _Requirements: 8.4, 8.5_

- [x] 19. Final checkpoint - Verify complete implementation
  - Run full test suite to ensure all tests pass
  - Verify Swagger UI and ReDoc render from bundled assets with no external requests

## Notes

- Tasks 1–10 are already completed from the original implementation
- Tasks 11–19 implement the bundled asset layer and update existing blueprints
- The `update-assets` CLI command is the only operation that requires network access; it is a developer-time tool, not a runtime dependency
- All vendored assets are committed to version control so builds never require network access
- Each task references specific requirements for traceability
- All tests use the `testbase` framework per repository conventions
- Property tests use data-driven iteration over generated inputs (minimum 10 iterations per property)
