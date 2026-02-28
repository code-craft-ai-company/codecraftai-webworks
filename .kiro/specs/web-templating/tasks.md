# Implementation Plan: Web Templating

## Overview

This implementation plan creates the Web Templating feature providing template engine integration and rendering capabilities for the web framework. The implementation supports multiple template engines (Jinja2, Mako) through a pluggable architecture with auto-escaping enabled by default for security.

## Tasks

- [x] 1. Create template engine abstraction
  - [x] 1.1 Create `TemplateEngine` abstract base class
    - Define abstract methods: render(), render_string(), add_filter(), add_global(), clear_cache()
    - Define default implementations for render_async() and render_stream()
    - _Requirements: 1.1, 2.1, 2.2, 2.5, 2.7_

  - [x] 1.2 Create `TemplateEngineRegistry` class
    - Implement register() for engine adapter registration
    - Implement get() and create() for engine instantiation
    - Implement set_default() and list_engines()
    - _Requirements: 1.2, 1.5_

  - [x] 1.3 Write property test for engine registration idempotence
    - **Property 8: Engine Registration Idempotence**
    - **Validates: Requirements 1.2**

- [x] 2. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 3. Create template loading components
  - [x] 3.1 Create `TemplateLoader` class
    - Implement load() for reading template files
    - Implement exists() for checking template existence
    - Implement get_path() and get_mtime() for file info
    - Support multiple directories with priority ordering
    - _Requirements: 6.1, 6.2, 6.9_

  - [x] 3.2 Create `TemplateCache` class
    - Implement get() and set() for cache operations
    - Implement clear() and remove() for cache management
    - Support max_size limit and auto_reload mode
    - _Requirements: 6.4, 6.5, 6.6, 6.7_

  - [x] 3.3 Write property test for cache consistency
    - **Property 7: Cache Consistency**
    - **Validates: Requirements 6.6, 6.8**

- [x] 4. Create auto-escaping utilities
  - [x] 4.1 Create `SafeString` class and `safe()` function
    - Implement SafeString as str subclass with __html__() method
    - Implement safe() function to create SafeString instances
    - _Requirements: 5.3, 5.7_

  - [x] 4.2 Implement escape functions
    - Implement escape() for HTML special characters
    - Implement escape_json() for JavaScript contexts
    - Implement escape_url() for URL encoding
    - _Requirements: 5.2, 5.8, 5.9, 5.10_

  - [x] 4.3 Write property test for auto-escaping correctness
    - **Property 2: Auto-Escaping Correctness**
    - **Validates: Requirements 5.1, 5.2, 5.6**

  - [x] 4.4 Write property test for safe string bypass
    - **Property 3: Safe String Bypass**
    - **Validates: Requirements 5.3, 5.7**

- [x] 5. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Create template context management
  - [x] 6.1 Create `TemplateContext` class
    - Implement dictionary-like interface (__getitem__, __setitem__, __contains__)
    - Implement get(), update(), merge(), to_dict() methods
    - _Requirements: 3.1_

  - [x] 6.2 Implement context variable access features
    - Support nested dictionary access via dot notation
    - Support list/sequence iteration
    - Support callable object invocation
    - Support object attribute access
    - _Requirements: 3.2, 3.3, 3.4, 3.9_

  - [x] 6.3 Implement global and request-scoped context
    - Support global context variables
    - Support request-scoped context variables
    - Support context processors
    - _Requirements: 3.5, 3.6, 3.10_

  - [x] 6.4 Implement undefined variable handling
    - Support silent mode (return empty string)
    - Support strict mode (raise UndefinedVariableError)
    - Support configurable behavior
    - _Requirements: 3.7, 3.8_

  - [x] 6.5 Write property test for context variable access
    - **Property 4: Context Variable Access**
    - **Validates: Requirements 3.2, 3.7, 3.8**

- [x] 7. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Create built-in filters
  - [x] 8.1 Implement string manipulation filters
    - Implement lower, upper, title, trim filters
    - Implement format filter with args/kwargs support
    - _Requirements: 7.3, 7.5_

  - [x] 8.2 Implement collection filters
    - Implement length, join, first, last filters
    - Implement sort, reverse filters
    - _Requirements: 7.3, 7.4_

  - [x] 8.3 Implement utility filters
    - Implement safe, escape, default filters
    - Implement date, json filters
    - _Requirements: 7.3, 7.9_

  - [x] 8.4 Write property test for filter chaining correctness
    - **Property 6: Filter Chaining Correctness**
    - **Validates: Requirements 7.4**

- [x] 9. Create Jinja2 adapter
  - [x] 9.1 Create `Jinja2Adapter` class
    - Implement __init__ with configuration options
    - Create and configure Jinja2 Environment
    - _Requirements: 1.3, 1.6_

  - [x] 9.2 Implement Jinja2 rendering methods
    - Implement render() using Jinja2 get_template()
    - Implement render_string() using Jinja2 from_string()
    - Implement render_async() for async rendering
    - Implement render_stream() for streaming
    - _Requirements: 2.1, 2.2, 2.5, 2.7_

  - [x] 9.3 Implement Jinja2 filter and global registration
    - Implement add_filter() to register Jinja2 filters
    - Implement add_global() to register Jinja2 globals
    - _Requirements: 7.1, 7.2_

  - [x] 9.4 Implement Jinja2 auto-escaping configuration
    - Configure autoescape based on file extension
    - Support enabling/disabling per template
    - _Requirements: 5.1, 5.4, 5.5_

  - [x] 9.5 Implement Jinja2 cache management
    - Implement clear_cache() to clear bytecode cache
    - Support auto_reload for development
    - _Requirements: 6.4, 6.6, 6.10_

- [x] 10. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 11. Create Mako adapter
  - [x] 11.1 Create `MakoAdapter` class
    - Implement __init__ with configuration options
    - Create and configure Mako TemplateLookup
    - _Requirements: 1.4, 1.6_

  - [x] 11.2 Implement Mako rendering methods
    - Implement render() using Mako get_template()
    - Implement render_string() using Mako Template()
    - _Requirements: 2.1, 2.2_

  - [x] 11.3 Implement Mako filter and global registration
    - Implement add_filter() for Mako filters
    - Implement add_global() for Mako globals
    - _Requirements: 7.1, 7.2_

  - [x] 11.4 Implement Mako auto-escaping configuration
    - Configure default_filters for auto-escaping
    - _Requirements: 5.1_

- [x] 12. Create template renderer
  - [x] 12.1 Create `TemplateRenderer` class
    - Implement __init__ with engine and context processors
    - Implement _build_context() for context merging
    - _Requirements: 2.1, 3.10_

  - [x] 12.2 Implement rendering methods
    - Implement render() with context building
    - Implement render_async() for async rendering
    - Implement render_string() for string templates
    - Implement render_stream() for streaming
    - _Requirements: 2.1, 2.2, 2.5, 2.7_

  - [x] 12.3 Implement context processor support
    - Implement add_context_processor() method
    - Apply context processors during rendering
    - _Requirements: 3.10_

  - [x] 12.4 Write property test for template rendering determinism
    - **Property 1: Template Rendering Determinism**
    - **Validates: Requirements 2.1, 2.6**

- [x] 13. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 14. Implement template inheritance support
  - [x] 14.1 Verify Jinja2 inheritance support
    - Test extends directive functionality
    - Test block override functionality
    - Test super() call functionality
    - _Requirements: 4.1, 4.2, 4.3_

  - [x] 14.2 Verify template include support
    - Test include directive functionality
    - Test variable passing to includes
    - Test conditional includes
    - _Requirements: 4.4, 4.5, 4.6_

  - [x] 14.3 Implement inheritance error handling
    - Detect and report missing parent templates
    - Detect and report circular inheritance
    - _Requirements: 4.7, 4.8_

  - [x] 14.4 Write property test for template inheritance chain
    - **Property 5: Template Inheritance Chain**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.9**

- [x] 15. Create error handling
  - [x] 15.1 Create template exception classes
    - Implement TemplateNotFoundError with searched paths
    - Implement TemplateSyntaxError with line number
    - Implement TemplateRenderError with variable name
    - Implement UndefinedVariableError for strict mode
    - _Requirements: 2.3, 2.4, 2.8, 9.6_

  - [x] 15.2 Implement error message formatting
    - Include template filename in all errors
    - Include line number where applicable
    - Include source context in debug mode
    - _Requirements: 9.1, 9.2, 9.3_

  - [x] 15.3 Implement additional exception classes
    - Implement TemplateInheritanceError with chain
    - Implement TemplateEngineNotFoundError with available list
    - Implement TemplateFilterNotFoundError
    - Implement TemplateConfigurationError
    - _Requirements: 1.8, 4.8, 7.6, 10.9_

  - [x] 15.4 Write property test for error message completeness
    - **Property 9: Error Message Completeness**
    - **Validates: Requirements 9.1, 9.2**

- [x] 16. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 17. Create response integration
  - [x] 17.1 Implement render_template() helper
    - Return HTTP Response with rendered body
    - Set Content-Type header (default text/html)
    - Support custom status code and headers
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

  - [x] 17.2 Implement render_template_stream() helper
    - Return StreamingResponse with rendered body
    - Support large template streaming
    - _Requirements: 8.8_

  - [x] 17.3 Integrate with request context
    - Inject request context variables automatically
    - Use configured template engine
    - _Requirements: 8.6, 8.7_

  - [x] 17.4 Write property test for response integration correctness
    - **Property 10: Response Integration Correctness**
    - **Validates: Requirements 8.1, 8.2, 8.4**

- [x] 18. Create configuration system
  - [x] 18.1 Create `TemplateConfig` dataclass
    - Define configuration fields with defaults
    - Implement validate() method
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6_

  - [x] 18.2 Implement configuration loading
    - Load from application configuration
    - Support environment-specific settings
    - Support nested engine options
    - _Requirements: 10.7, 10.10_

  - [x] 18.3 Implement configuration validation
    - Validate on application startup
    - Raise TemplateConfigurationError for invalid config
    - _Requirements: 10.8, 10.9_

- [x] 19. Wire all components together
  - [x] 19.1 Register built-in engine adapters
    - Register Jinja2Adapter as "jinja2"
    - Register MakoAdapter as "mako"
    - Set Jinja2 as default engine
    - _Requirements: 1.3, 1.4, 1.5_

  - [x] 19.2 Register built-in filters
    - Register all BUILTIN_FILTERS with engines
    - _Requirements: 7.3, 7.9_

  - [x] 19.3 Integrate TemplateLoader with engines
    - Configure loader directories from config
    - Support package template loading
    - _Requirements: 6.1, 6.2, 6.3_

  - [x] 19.4 Integrate TemplateCache with engines
    - Configure cache from config
    - Support cache disabling for development
    - _Requirements: 6.4, 6.10_

- [x] 20. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- Implementation uses Python with testbase framework per repository conventions
- Test files should be located at `source/testroots/automojo/tests/singlehost/webworks/templating/`
- Jinja2 and Mako are external dependencies that must be installed
