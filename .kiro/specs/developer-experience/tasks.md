# Implementation Plan: Developer Experience

## Overview

This implementation plan creates the Developer Experience feature providing CLI tooling, testing utilities, and debug/error pages. The implementation builds on the webapp-persona and endpoint-abstractions features and integrates with the testbase framework.

## Tasks

- [x] 1. Create CLI framework foundation
  - [x] 1.1 Create `CLICommand` base class with name, help, add_arguments, and execute methods
    - _Requirements: 1.1, 1.3_

  - [x] 1.2 Create `CLIGroup` class for organizing related commands
    - _Requirements: 1.2_

  - [x] 1.3 Create `WebworksCLI` main entry point class
    - Implement command and group registration
    - Implement argument parsing with global options (--verbose, --config, --env)
    - _Requirements: 1.1, 1.4_

  - [x] 1.4 Implement configuration loading from file and environment variables
    - Environment variables take precedence over file config
    - _Requirements: 1.5, 1.6_

  - [x] 1.5 Implement colored output support with terminal detection
    - _Requirements: 1.7_

  - [x] 1.6 Implement exit code handling
    - _Requirements: 1.8_

  - [x] 1.7 Write property test for CLI exit code consistency
    - **Property 4: CLI Exit Code Consistency**
    - **Validates: Requirements 1.8**

  - [x] 1.8 Write property test for configuration precedence
    - **Property 8: Configuration Precedence**
    - **Validates: Requirements 1.5, 1.6**

- [x] 2. Implement project scaffolding commands
  - [x] 2.1 Create `NewProjectCommand` for `webworks new <project-name>`
    - Create project directory with standard structure
    - Support --template option for project types
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 2.2 Create `GenerateEndpointCommand` for `webworks generate endpoint <name>`
    - Generate endpoint file with boilerplate
    - _Requirements: 2.4, 2.7_

  - [x] 2.3 Create `GenerateBlueprintCommand` for `webworks generate blueprint <name>`
    - Generate blueprint file with standard structure
    - _Requirements: 2.5, 2.7_

  - [x] 2.4 Implement --dry-run option for all generate commands
    - Preview generated files without writing
    - _Requirements: 2.6_

- [x] 3. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Implement development server
  - [x] 4.1 Create `DevelopmentServer` class with host, port, debug, reload configuration
    - _Requirements: 3.1, 3.2, 3.3_

  - [x] 4.2 Create `ServeCommand` for `webworks serve`
    - Support --host, --port, --reload, --no-debug options
    - _Requirements: 3.1, 3.2, 3.4, 3.7_

  - [x] 4.3 Implement request logging middleware
    - Log method, path, status code, and response time
    - _Requirements: 3.6_

  - [x] 4.4 Implement port-in-use error handling
    - Display clear error message with suggestions
    - _Requirements: 3.8_

- [x] 5. Implement auto-reload functionality
  - [x] 5.1 Create `FileWatcher` class with pattern matching
    - Support configurable watch patterns
    - Support exclude patterns for non-source directories
    - _Requirements: 4.1, 4.3, 4.4_

  - [x] 5.2 Implement file change detection and server restart
    - Restart within 2 seconds of file modification
    - Preserve bound address across restarts
    - _Requirements: 4.2, 4.6_

  - [x] 5.3 Implement syntax error handling during reload
    - Display error and continue watching for fixes
    - _Requirements: 4.5_

  - [x] 5.4 Implement --extra-files option for additional file types
    - _Requirements: 4.7_

  - [x] 5.5 Write property test for auto-reload file exclusion
    - **Property 5: Auto-Reload File Exclusion**
    - **Validates: Requirements 4.4**

- [x] 6. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Implement test client
  - [x] 7.1 Create `TestClient` class with HTTP method helpers
    - Implement get, post, put, patch, delete, head, options methods
    - _Requirements: 5.1, 5.2_

  - [x] 7.2 Create `TestResponse` dataclass with status_code, headers, body
    - Implement text and json properties
    - _Requirements: 5.3_

  - [x] 7.3 Implement request body handling
    - Support json parameter for JSON bodies
    - Support data parameter for form data
    - _Requirements: 5.4, 5.5_

  - [x] 7.4 Implement headers and query parameters support
    - _Requirements: 5.6, 5.7_

  - [x] 7.5 Implement cookie handling with CookieJar
    - Persist cookies across multiple requests
    - _Requirements: 5.8_

  - [x] 7.6 Implement authentication helpers
    - _Requirements: 5.9_

  - [x] 7.7 Write property test for TestClient request-response consistency
    - **Property 1: TestClient Request-Response Consistency**
    - **Validates: Requirements 5.1, 5.2, 5.3**

  - [x] 7.8 Write property test for cookie persistence
    - **Property 7: Cookie Persistence Across Requests**
    - **Validates: Requirements 5.8**

- [x] 8. Implement test fixtures
  - [x] 8.1 Create `create_test_app` resource factory
    - Integrate with testbase framework
    - Support configuration overrides
    - _Requirements: 6.1, 6.6_

  - [x] 8.2 Create `create_test_client` resource factory
    - Bind to test application instance
    - _Requirements: 6.2_

  - [x] 8.3 Create `create_mock_request` resource factory
    - Support custom method, path, headers, body
    - _Requirements: 6.3_

  - [x] 8.4 Create `create_mock_response` resource factory
    - _Requirements: 6.4_

  - [x] 8.5 Implement automatic resource cleanup
    - _Requirements: 6.7_

- [x] 9. Implement assertion helpers
  - [x] 9.1 Create `TestAssertions` class with static assertion methods
    - _Requirements: 7.1_

  - [x] 9.2 Implement `assert_status` helper
    - _Requirements: 7.2_

  - [x] 9.3 Implement `assert_json` helper with partial matching support
    - _Requirements: 7.3_

  - [x] 9.4 Implement `assert_header` helper
    - _Requirements: 7.4_

  - [x] 9.5 Implement `assert_content_type` helper
    - _Requirements: 7.5_

  - [x] 9.6 Implement `assert_redirect` helper
    - _Requirements: 7.6_

  - [x] 9.7 Implement clear error messages with expected vs actual values
    - _Requirements: 7.7_

  - [x] 9.8 Write property test for assertion error messages
    - **Property 2: Test Assertion Error Messages**
    - **Validates: Requirements 7.7**

- [x] 10. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 11. Implement debug error pages
  - [x] 11.1 Create `DebugErrorHandler` class
    - Support debug and production modes
    - _Requirements: 8.1, 10.1_

  - [x] 11.2 Implement debug error page rendering
    - Display exception type, message, and stack trace
    - Highlight error line with source context
    - Display local variables at each frame
    - Display request information
    - _Requirements: 8.2, 8.3, 8.4, 8.5, 8.6_

  - [x] 11.3 Implement syntax highlighting and styling
    - _Requirements: 8.7_

  - [x] 11.4 Implement production mode security
    - Prevent debug page display in production
    - _Requirements: 8.8_

  - [x] 11.5 Write property test for debug page security boundary
    - **Property 3: Debug Page Security Boundary**
    - **Validates: Requirements 8.8, 10.2**

- [x] 12. Implement interactive debugger
  - [x] 12.1 Create `InteractiveDebugger` class
    - Support PIN-based security
    - _Requirements: 9.1, 9.3_

  - [x] 12.2 Implement expression evaluation in frame context
    - _Requirements: 9.2, 9.4_

  - [x] 12.3 Implement stack frame navigation
    - _Requirements: 9.5_

  - [x] 12.4 Implement session timeout
    - _Requirements: 9.6_

  - [x] 12.5 Implement opt-in activation (disabled by default)
    - _Requirements: 9.7_

- [x] 13. Implement production error pages
  - [x] 13.1 Implement generic production error page
    - Hide internal details
    - Display user-friendly message
    - Include error reference ID
    - _Requirements: 10.1, 10.2, 10.3, 10.4_

  - [x] 13.2 Implement custom error page templates
    - Support different templates per status code
    - _Requirements: 10.5, 10.6_

  - [x] 13.3 Implement server-side error logging
    - _Requirements: 10.7_

- [x] 14. Implement request inspector
  - [x] 14.1 Create `RequestInspector` class
    - _Requirements: 11.1_

  - [x] 14.2 Create `RequestInfo` dataclass
    - Capture method, path, query params, headers, body
    - _Requirements: 11.2, 11.3, 11.4_

  - [x] 14.3 Implement body size limiting and truncation
    - _Requirements: 11.4_

  - [x] 14.4 Implement JSON/form data parsing
    - _Requirements: 11.5_

  - [x] 14.5 Implement path pattern filtering
    - _Requirements: 11.6_

  - [x] 14.6 Implement debug endpoint for request review
    - _Requirements: 11.7, 11.8_

  - [x] 14.7 Write property test for request inspector size limits
    - **Property 6: Request Inspector Size Limits**
    - **Validates: Requirements 11.4**

- [x] 15. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 16. Implement CLI database commands
  - [x] 16.1 Create `DatabaseGroup` command group
    - _Requirements: 12.1_

  - [x] 16.2 Implement `db init` command
    - _Requirements: 12.1_

  - [x] 16.3 Implement `db migrate` command
    - _Requirements: 12.2_

  - [x] 16.4 Implement `db rollback` command
    - _Requirements: 12.3_

  - [x] 16.5 Implement `db seed` command
    - _Requirements: 12.4_

  - [x] 16.6 Implement `db status` command
    - _Requirements: 12.6_

  - [x] 16.7 Implement --env option and migration error handling
    - _Requirements: 12.5, 12.7_

- [x] 17. Implement CLI routes command
  - [x] 17.1 Create `RoutesCommand` for `webworks routes`
    - Display all registered endpoints
    - _Requirements: 13.1, 13.2_

  - [x] 17.2 Implement --format option (table, json, csv)
    - _Requirements: 13.3_

  - [x] 17.3 Implement --filter option for path pattern filtering
    - _Requirements: 13.4_

  - [x] 17.4 Implement --verbose option for additional metadata
    - _Requirements: 13.5_

  - [x] 17.5 Implement authentication indicator in output
    - _Requirements: 13.6_

- [x] 18. Implement CLI shell command
  - [x] 18.1 Create `ShellCommand` for `webworks shell`
    - Start interactive Python shell
    - _Requirements: 14.1_

  - [x] 18.2 Pre-load application instance and common imports
    - _Requirements: 14.2, 14.3_

  - [x] 18.3 Implement IPython support with fallback
    - _Requirements: 14.4_

  - [x] 18.4 Implement startup file loading
    - _Requirements: 14.5_

  - [x] 18.5 Implement banner with available objects
    - _Requirements: 14.6_

- [x] 19. Implement development logging
  - [x] 19.1 Configure DEBUG level logging in debug mode
    - _Requirements: 15.1_

  - [x] 19.2 Implement log formatting with timestamps and source location
    - _Requirements: 15.2_

  - [x] 19.3 Implement colored log output
    - _Requirements: 15.3_

  - [x] 19.4 Implement SQL query logging option
    - _Requirements: 15.4_

  - [x] 19.5 Implement --log-level CLI option
    - _Requirements: 15.5_

  - [x] 19.6 Implement --log-file CLI option
    - _Requirements: 15.6_

  - [x] 19.7 Implement request ID correlation
    - _Requirements: 15.7_

- [x] 20. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- Implementation uses Python with testbase framework per repository conventions
- Test files should be located at `source/testroots/automojo/tests/singlehost/webworks/devexp/`
