# Implementation Plan: Configuration System

## Overview

This implementation plan creates the unified configuration system for the ccai framework. The implementation follows a bottom-up approach, starting with core data structures and enums, building up through sources and schema, to the registry and model layers. Each task builds on previous work to ensure incremental, testable progress.

## Tasks

- [x] 1. Create core data structures and enums
  - [x] 1.1 Create ConfigSourceType enum with precedence values
    - Implement OVERRIDE, ENVIRONMENT, SECRETS, FILE, DEFAULT values
    - Define default precedence order
    - _Requirements: 2.6, 2.7_

  - [x] 1.2 Create ConfigValue dataclass
    - Implement fields: key, value, source, source_detail, is_override, is_sensitive
    - _Requirements: 1.8_

  - [x] 1.3 Create ConfigValueMetadata dataclass
    - Implement fields: source, source_detail, is_override, is_sensitive, schema_type, schema_default, schema_description
    - _Requirements: 1.8_

  - [x] 1.4 Create ConfigKeyDefinition dataclass
    - Implement fields: key, type, required, default, description, sensitive, choices, validator
    - _Requirements: 3.1, 3.2, 3.4, 3.5_

  - [x] 1.5 Create ValidationError dataclass
    - Implement fields: key, message, expected_type, actual_value, constraint
    - _Requirements: 3.7_

  - [x] 1.6 Create ConfigChangeEvent dataclass
    - Implement fields: key, old_value, new_value, source, timestamp
    - _Requirements: 6.5_

- [x] 2. Create exception classes
  - [x] 2.1 Create ConfigurationError base exception
    - Implement with message and optional key
    - _Requirements: 1.6_

  - [x] 2.2 Create ConfigurationValidationError exception
    - Implement with list of ValidationError
    - Format error message with all failures
    - _Requirements: 3.7_

  - [x] 2.3 Create ConfigurationFileNotFoundError exception
    - Implement with path and optional referenced_from
    - _Requirements: 5.8_

  - [x] 2.4 Create ConfigurationFrozenError exception
    - Implement with key that was attempted to modify
    - _Requirements: 6.8_

  - [x] 2.5 Create ConfigurationTypeError exception
    - Implement with key, expected_type, and actual_value
    - _Requirements: 1.2_

- [x] 3. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Implement SecretValue wrapper
  - [x] 4.1 Create SecretValue class
    - Implement constructor with value, key, and optional audit_logger
    - Implement get_secret_value() method with audit logging
    - Implement __str__ and __repr__ to return masked value
    - _Requirements: 4.6, 4.7_

  - [x] 4.2 Write property test for SecretValue wrapper behavior
    - **Property 15: SecretValue Wrapper Behavior**
    - **Validates: Requirements 4.6, 4.7**

- [x] 5. Implement ConfigSchema
  - [x] 5.1 Create ConfigSchema class with key definitions
    - Implement define() method for adding key definitions
    - Implement nested() method for nested schemas
    - Store ConfigKeyDefinition instances
    - _Requirements: 3.1, 3.2, 3.4, 3.5_

  - [x] 5.2 Implement type coercion logic
    - Implement string to int, float, bool coercion
    - Implement string to list and dict coercion (JSON parsing)
    - _Requirements: 3.8_

  - [x] 5.3 Write property test for type coercion
    - **Property 10: Type Coercion**
    - **Validates: Requirements 3.8**

  - [x] 5.4 Implement schema validation
    - Implement validate() method
    - Check required keys, types, enum constraints, custom validators
    - Return list of ValidationError
    - _Requirements: 3.1, 3.2, 3.6, 3.7, 3.10_

  - [x] 5.5 Write property test for schema validation completeness
    - **Property 9: Schema Validation Completeness**
    - **Validates: Requirements 3.1, 3.2, 3.6, 3.7**

  - [x] 5.6 Write property test for enum constraint validation
    - **Property 12: Enum Constraint Validation**
    - **Validates: Requirements 3.10**

  - [x] 5.7 Implement nested schema validation
    - Recursively validate nested structures
    - _Requirements: 3.9_

  - [x] 5.8 Write property test for nested schema validation
    - **Property 11: Nested Schema Validation**
    - **Validates: Requirements 3.9**

- [x] 6. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Implement ConfigSource base and EnvironmentSource
  - [x] 7.1 Create ConfigSource abstract base class
    - Define abstract load() method
    - Define abstract source_type property
    - _Requirements: 2.1_

  - [x] 7.2 Create EnvironmentSource class
    - Implement constructor with prefix, separator, lowercase_keys
    - Implement load() to read environment variables with prefix
    - Implement key mapping (APP_DATABASE_HOST -> database.host)
    - _Requirements: 2.1, 2.10_

  - [x] 7.3 Write property test for environment variable mapping
    - **Property 8: Environment Variable Mapping**
    - **Validates: Requirements 2.10**

- [x] 8. Implement FileSource with format support
  - [x] 8.1 Create ConfigLoader abstract base class
    - Define abstract load(content: str) method
    - _Requirements: 2.8_

  - [x] 8.2 Implement INI format loader
    - Parse INI format configuration
    - Support nested keys via section names
    - _Requirements: 2.2_

  - [x] 8.3 Implement YAML format loader
    - Parse YAML format configuration
    - _Requirements: 2.3_

  - [x] 8.4 Implement JSON format loader
    - Parse JSON format configuration
    - _Requirements: 2.4_

  - [x] 8.5 Implement TOML format loader
    - Parse TOML format configuration
    - _Requirements: 2.5_

  - [x] 8.6 Create FileSource class
    - Implement constructor with paths, format, required
    - Implement load() to read and parse files
    - Auto-detect format from file extension
    - _Requirements: 2.2, 2.3, 2.4, 2.5_

  - [x] 8.7 Write property test for file format round-trip
    - **Property 6: File Format Round-Trip**
    - **Validates: Requirements 2.2, 2.3, 2.4, 2.5**

  - [x] 8.8 Implement include directive processing
    - Parse include directives in configuration files
    - Load and merge included files
    - _Requirements: 5.7_

  - [x] 8.9 Write property test for include directive processing
    - **Property 20: Include Directive Processing**
    - **Validates: Requirements 5.7**

  - [x] 8.10 Write property test for missing file error
    - **Property 21: Missing File Error**
    - **Validates: Requirements 5.8**

- [x] 9. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Implement SecretsProvider
  - [x] 10.1 Create SecretsProvider class
    - Implement constructor with env_prefix, secrets_file, encryption_key, audit_logger
    - Implement load() to read secrets from environment and file
    - _Requirements: 4.1, 4.2_

  - [x] 10.2 Implement encryption/decryption for secrets file
    - Implement encrypt_secrets() for writing encrypted file
    - Implement decrypt_secrets() for reading encrypted file
    - _Requirements: 4.1, 4.10_

  - [x] 10.3 Write property test for secret encryption round-trip
    - **Property 13: Secret Encryption Round-Trip**
    - **Validates: Requirements 4.1**

  - [x] 10.4 Implement secret masking in logs and errors
    - Ensure SecretValue is used for sensitive values
    - Mask values in string representations
    - _Requirements: 4.4, 4.5_

  - [x] 10.5 Write property test for secret masking
    - **Property 14: Secret Masking**
    - **Validates: Requirements 4.4, 4.5**

  - [x] 10.6 Implement audit logging for secret access
    - Log access to sensitive values when audit_logger is provided
    - _Requirements: 4.9_

  - [x] 10.7 Write property test for secret audit logging
    - **Property 16: Secret Audit Logging**
    - **Validates: Requirements 4.9**

  - [x] 10.8 Implement reload() for secret rotation
    - Allow reloading secrets without restart
    - _Requirements: 4.8_

- [x] 11. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 12. Implement ConfigRegistry
  - [x] 12.1 Create ConfigRegistry class
    - Implement constructor with schema and precedence
    - Initialize source and loader registries
    - _Requirements: 2.6, 2.7_

  - [x] 12.2 Implement source registration
    - Implement register_source() method
    - Implement register_loader() method
    - _Requirements: 2.1, 2.8_

  - [x] 12.3 Implement configuration loading and merging
    - Implement load() method
    - Load from all sources in precedence order
    - Merge values according to precedence
    - _Requirements: 2.6, 2.9_

  - [x] 12.4 Write property test for source precedence
    - **Property 7: Source Precedence**
    - **Validates: Requirements 2.6, 2.9**

  - [x] 12.5 Implement override mechanism
    - Implement override() method
    - Store overrides with highest precedence
    - _Requirements: 6.1, 6.2_

  - [x] 12.6 Write property test for runtime override precedence
    - **Property 22: Runtime Override Precedence**
    - **Validates: Requirements 6.1, 6.2**

  - [x] 12.7 Implement freeze functionality
    - Implement freeze() method
    - Raise ConfigurationFrozenError on modification attempts
    - _Requirements: 6.7, 6.8_

  - [x] 12.8 Write property test for configuration freeze
    - **Property 25: Configuration Freeze**
    - **Validates: Requirements 6.7, 6.8**

  - [x] 12.9 Implement change notification
    - Implement on_change() callback registration
    - Fire ConfigChangeEvent on changes
    - _Requirements: 6.5_

  - [x] 12.10 Write property test for change notification callbacks
    - **Property 23: Change Notification Callbacks**
    - **Validates: Requirements 6.5**

  - [x] 12.11 Implement atomic updates
    - Ensure all-or-nothing update semantics
    - _Requirements: 6.6_

  - [x] 12.12 Write property test for atomic updates
    - **Property 24: Atomic Updates**
    - **Validates: Requirements 6.6**

- [x] 13. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 14. Implement ConfigurationModel
  - [x] 14.1 Create ConfigurationModel class
    - Implement constructor with registry
    - Initialize value cache
    - _Requirements: 1.1_

  - [x] 14.2 Implement typed access methods
    - Implement get(), get_str(), get_int(), get_float(), get_bool(), get_list(), get_dict()
    - Apply type coercion as needed
    - _Requirements: 1.2_

  - [x] 14.3 Write property test for typed access consistency
    - **Property 1: Typed Access Consistency**
    - **Validates: Requirements 1.2**

  - [x] 14.4 Implement dot-notation and dictionary access
    - Implement __getattr__ for dot-notation
    - Implement __getitem__ for dictionary access
    - _Requirements: 1.3, 1.4_

  - [x] 14.5 Write property test for access method equivalence
    - **Property 2: Access Method Equivalence**
    - **Validates: Requirements 1.3, 1.4**

  - [x] 14.6 Implement default value handling
    - Return default when key not found
    - Raise ConfigurationError when required key missing
    - _Requirements: 1.5, 1.6_

  - [x] 14.7 Write property test for default value resolution
    - **Property 3: Default Value Resolution**
    - **Validates: Requirements 1.5**

  - [x] 14.8 Write property test for missing required key error
    - **Property 4: Missing Required Key Error**
    - **Validates: Requirements 1.6**

  - [x] 14.9 Implement metadata access
    - Implement get_metadata() method
    - Return ConfigValueMetadata with source info
    - _Requirements: 1.8_

  - [x] 14.10 Write property test for value source metadata
    - **Property 5: Value Source Metadata**
    - **Validates: Requirements 1.8**

  - [x] 14.11 Implement namespace grouping
    - Implement namespace() method
    - Return ConfigNamespace for scoped access
    - _Requirements: 1.7_

- [x] 15. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 16. Implement file discovery and profiles
  - [x] 16.1 Implement configuration file discovery
    - Search configurable directories for config files
    - Support file name patterns
    - _Requirements: 5.1, 5.2, 5.3_

  - [x] 16.2 Write property test for file discovery
    - **Property 17: File Discovery**
    - **Validates: Requirements 5.1, 5.3**

  - [x] 16.3 Implement environment-specific files
    - Load environment-specific config files (e.g., settings.production.yaml)
    - Merge with base configuration
    - _Requirements: 5.4_

  - [x] 16.4 Write property test for environment-specific files
    - **Property 18: Environment-Specific Files**
    - **Validates: Requirements 5.4**

  - [x] 16.5 Write property test for file merge precedence
    - **Property 19: File Merge Precedence**
    - **Validates: Requirements 5.5**

  - [x] 16.6 Implement profile support
    - Support APP_PROFILE environment variable
    - Load and merge profile-specific configuration
    - _Requirements: 8.6, 8.7, 8.8_

  - [x] 16.7 Write property test for profile configuration
    - **Property 31: Profile Configuration**
    - **Validates: Requirements 8.6, 8.7, 8.8**

- [x] 17. Implement export functionality
  - [x] 17.1 Implement configuration export
    - Implement export() method for INI, YAML, JSON, TOML
    - Support file output and string return
    - _Requirements: 7.1_

  - [x] 17.2 Write property test for export round-trip
    - **Property 26: Export Round-Trip**
    - **Validates: Requirements 7.1**

  - [x] 17.3 Implement template export
    - Implement export_template() method
    - Include defaults and descriptions
    - _Requirements: 7.2_

  - [x] 17.4 Implement documentation generation
    - Implement export_documentation() method
    - Include key name, type, default, description, required status
    - _Requirements: 7.3, 7.4_

  - [x] 17.5 Write property test for documentation completeness
    - **Property 27: Documentation Completeness**
    - **Validates: Requirements 7.2, 7.3, 7.4**

  - [x] 17.6 Implement diff export
    - Implement export_diff() method
    - Show only values that differ from defaults
    - _Requirements: 7.6_

  - [x] 17.7 Write property test for export diff accuracy
    - **Property 28: Export Diff Accuracy**
    - **Validates: Requirements 7.6**

  - [x] 17.8 Implement secret masking in exports
    - Mask sensitive values by default
    - Support explicit unmasking
    - _Requirements: 7.7_

  - [x] 17.9 Write property test for export secret masking
    - **Property 29: Export Secret Masking**
    - **Validates: Requirements 7.7**

- [x] 18. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 19. Implement ConfigWatcher
  - [x] 19.1 Create ConfigWatcher class
    - Implement constructor with registry
    - Implement watch() method to add paths
    - _Requirements: 6.3_

  - [x] 19.2 Implement file change monitoring
    - Implement start() and stop() methods
    - Trigger reload callback on file changes
    - _Requirements: 6.3, 6.4_

- [x] 20. Implement lazy loading
  - [x] 20.1 Add lazy loading support to ConfigRegistry
    - Defer source loading until first access
    - _Requirements: 8.3_

  - [x] 20.2 Write property test for lazy loading
    - **Property 30: Lazy Loading**
    - **Validates: Requirements 8.3**

- [x] 21. Implement application lifecycle integration
  - [x] 21.1 Integrate with persona system
    - Use presence directory for configuration discovery
    - _Requirements: 8.2_

  - [x] 21.2 Implement eager validation option
    - Support --validate-config for startup validation
    - _Requirements: 8.4_

  - [x] 21.3 Implement cleanup on shutdown
    - Close file handles and connections
    - _Requirements: 8.5_

- [x] 22. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- All tests should use the testbase framework as specified in AGENTS.md
- Test files should be placed in `source/testroots/ccai/tests/singlehost/webworks/configuration/`

