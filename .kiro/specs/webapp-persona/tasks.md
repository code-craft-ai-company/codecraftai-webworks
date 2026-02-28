# Implementation Plan: Web Application Persona & Presence

## Overview

This implementation plan creates the foundational infrastructure for web applications in the automojo framework. The implementation leverages the existing `automojo-this-app` package which provides `ThisApplication`, `establish_app_persona`, `AppPersona`, `PersonaVariablesDesc`, and singleton infrastructure. The implementation follows a bottom-up approach, starting with the WebApplication class and building up to the high-level establishment function.

## Dependencies

The implementation uses the following from `automojo-this-app`:
- `automojo.thisapp.wellknown.ThisApplication` - Base class to extend
- `automojo.thisapp.wellknown.SINGLETON_LOCK` - Thread lock for singleton initialization
- `automojo.thisapp.wellknown.THISAPPLICATION_SINGLETON` - Global singleton variable
- `automojo.thisapp.wellknown.PersonaVariablesDesc` - Variable descriptors
- `automojo.thisapp.wellknown.SemanticError` - Exception class
- `automojo.thisapp.persona.AppPersona` - Persona attribute storage
- `automojo.thisapp.persona.APP_PERSONA_ESTABLISHED` - Establishment flag

## Tasks

- [x] 1. Create core data structures and enums
  - [x] 1.1 Create VariableSource enum with bit flags for lookup order
    - Implement NONE, ENVIRONMENT, SETTINGS, DEFAULTS flags
    - Implement common combinations (ENV_THEN_SETTINGS, ALL)
    - _Requirements: 4.1_

  - [x] 1.2 Create AppVarDesc class for variable descriptors
    - Implement constructor with name, sources, default, context_path, description
    - Store VariableSource flags for lookup order
    - _Requirements: 4.1, 4.2_

  - [x] 1.3 Write property test for VariableSource flag combinations
    - **Property 8: Variable Override Precedence**
    - **Validates: Requirements 3.7, 4.1**

- [x] 2. Implement WebApplication class
  - [x] 2.1 Create WebApplication extending ThisApplication
    - Import `ThisApplication` from `automojo.thisapp.wellknown`
    - Import `SemanticError` from `automojo.thisapp.wellknown`
    - Constructor should accept same parameters as ThisApplication plus `from_establish_webapp_persona` flag
    - Raise SemanticError if `from_establish_webapp_persona` is not passed (prevent direct instantiation)
    - Call `super().__init__` with `from_establish_app_persona=True` to satisfy parent check
    - Implement `prepare_database()` hook (empty default implementation)
    - Implement `connect_database()` hook (empty default implementation)
    - Implement `startup_database()` hook (empty default implementation)
    - Implement `ensure_database_ready()` hook (returns True by default)
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.8, 1.9_

  - [x] 2.2 Write property test for WebApplication inheritance
    - **Property 1: WebApplication Inheritance Preservation**
    - **Validates: Requirements 1.1, 1.6**

- [x] 3. Implement singleton infrastructure
  - [x] 3.1 Create wellknown module at automojo.webworks.wellknown
    - Import `SINGLETON_LOCK` from `automojo.thisapp.wellknown` (reuse the same lock)
    - Import `SemanticError` from `automojo.thisapp.wellknown`
    - Define `THISWEBAPPLICATION_SINGLETON` module variable (initially None)
    - Implement `ThisWebApplicationSingleton()` function that:
      - Acquires `SINGLETON_LOCK`
      - Raises `SemanticError` if `THISWEBAPPLICATION_SINGLETON` is None (with helpful message about calling establish_webapp_persona)
      - Returns `THISWEBAPPLICATION_SINGLETON`
    - _Requirements: 5.1, 5.2, 5.3, 5.6, 5.8_

  - [x] 3.2 Write property test for singleton identity
    - **Property 2: Singleton Identity Consistency**
    - **Validates: Requirements 2.2, 5.4**

  - [x] 3.3 Write property test for thread-safe initialization
    - **Property 11: Thread-Safe Initialization**
    - **Validates: Requirements 5.6**

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement establish_webapp_persona function
  - [x] 5.1 Create establish_webapp_persona with all persona fields (mirroring establish_app_persona pattern)
    - Import `AppPersona` from `automojo.thisapp.persona`
    - Import `PersonaVariablesDesc` from `automojo.thisapp.wellknown`
    - Import `SINGLETON_LOCK`, `THISAPPLICATION_SINGLETON` from `automojo.thisapp.wellknown`
    - Accept name, logger_name, log_basename, presence_dir, log_directory, settings_file, extensions, service_name
    - Accept optional `application_cls` parameter (defaults to WebApplication)
    - Define `WEBAPP_PERSONA_ESTABLISHED` module variable to prevent double establishment
    - _Requirements: 2.1, 2.3, 2.4_

  - [x] 5.2 Implement default path computation logic (matching establish_app_persona)
    - Default presence_dir to `~/<appname>` (using `os.path.join("~", name.lower())`)
    - Default log_directory to `<presence_dir>/logs`
    - Default settings_file to `<presence_dir>/settings.config`
    - If settings_file is just a filename (`os.path.basename(settings_file) == settings_file`), join with presence_dir
    - If settings_file is a path, use `os.path.abspath(os.path.expandvars(os.path.expanduser()))`
    - _Requirements: 2.5, 2.6, 2.7, 2.8, 2.9_

  - [x] 5.3 Populate AppPersona class attributes and create WebApplication singleton
    - Set `AppPersona.AM_NAME`, `AM_LOGGER_NAME`, `AM_LOG_BASENAME`, `AM_PRESENCE_DIR`, `AM_LOG_DIRECTORY`, `AM_SETTINGS_FILENAME`, `AM_EXTENSIONS`, `AM_SERVICE_NAME`
    - Instantiate WebApplication (or application_cls) with `from_establish_webapp_persona=True`
    - Acquire `SINGLETON_LOCK` before setting singletons
    - Set `automojo.webworks.wellknown.THISWEBAPPLICATION_SINGLETON` to the new instance
    - Set `automojo.thisapp.wellknown.THISAPPLICATION_SINGLETON` to the same instance
    - Call `override_variable_value` for all PersonaVariablesDesc variables
    - Return the created singleton instance
    - _Requirements: 2.1, 2.2, 2.10, 2.11, 2.12_

  - [x] 5.4 Write property test for default path computation
    - **Property 3: Default Path Computation**
    - **Validates: Requirements 2.5, 2.6, 2.7**

  - [x] 5.5 Write property test for absolute path preservation
    - **Property 4: Absolute Path Preservation**
    - **Validates: Requirements 2.8, 2.9**

  - [x] 5.6 Write property test for custom class instantiation
    - **Property 5: Custom Class Instantiation**
    - **Validates: Requirements 2.4**

- [x] 6. Implement singleton establishment guard
  - [x] 6.1 Add establishment guard in establish_webapp_persona
    - Define `WEBAPP_PERSONA_ESTABLISHED` module variable (initially False)
    - Check if `WEBAPP_PERSONA_ESTABLISHED` is True at start of establish_webapp_persona
    - If already established, raise `PersonaAlreadyEstablishedError` with existing persona name
    - Set `WEBAPP_PERSONA_ESTABLISHED = True` before creating singleton
    - Also check that `automojo.thisapp.wellknown.THISAPPLICATION_SINGLETON` is None before setting
    - _Requirements: 5.7_

  - [x] 6.2 Write property test for establishment guard
    - **Property 10: Singleton Establishment Guard**
    - **Validates: Requirements 5.7**

- [x] 7. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Implement error handling
  - [x] 8.1 Create PersonaAlreadyEstablishedError exception
    - Raise when establishing persona after one already exists
    - Include existing persona name in error message
    - _Requirements: 5.7_

- [x] 9. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- All tests should use the testbase framework as specified in AGENTS.md
- Test files should be placed in `source/testroots/automojo/tests/singlehost/webworks/persona/`
- The implementation leverages existing functionality from `automojo-this-app`:
  - `ThisApplication` provides base persona management, context, config parser, and variable resolution
  - `AppPersona` provides class-level storage for persona attributes
  - `PersonaVariablesDesc` provides variable descriptors for all persona variables
  - `SINGLETON_LOCK` provides thread-safe singleton initialization
  - `SemanticError` provides consistent error handling
