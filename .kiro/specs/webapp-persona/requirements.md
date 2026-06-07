# Requirements Document

## Introduction

This document specifies the requirements for the Web Application Persona & Presence feature. This feature provides the foundational infrastructure for web applications built on the ccai framework, including application identity, configuration management, presence directories, and singleton access patterns. It extends the base `ThisApplication` functionality (from `codecraftai-this-app` package) with web-specific hooks and ensures consistent configuration across CLI tools and worker processes.

## Dependencies

This feature depends on the `codecraftai-this-app` package which provides:
- `ccai.thisapp.wellknown.ThisApplication` - Base application class with persona management
- `ccai.thisapp.persona.establish_app_persona` - Function pattern for persona establishment
- `ccai.thisapp.persona.AppPersona` - Class for storing persona attributes (AM_NAME, AM_PRESENCE_DIR, etc.)
- `ccai.thisapp.wellknown.PersonaVariablesDesc` - Variable descriptors for persona configuration
- `ccai.thisapp.wellknown.SINGLETON_LOCK` - Thread lock for singleton initialization
- `ccai.thisapp.wellknown.THISAPPLICATION_SINGLETON` - Global singleton variable
- `ccai.thisapp.wellknown.ThisApplicationSingleton()` - Accessor function for the singleton
- `ccai.thisapp.wellknown.SemanticError` - Exception for semantic errors

## Glossary

- **WebApplication**: The root class for web applications that extends `ccai.thisapp.wellknown.ThisApplication` with database lifecycle hooks and web-specific functionality.
- **ThisWebApplication**: The global singleton instance of `WebApplication` (or a subclass) that represents the active web application.
- **Persona**: The identity and configuration metadata for an application instance, including name, logging configuration, and directory paths.
- **Presence_Directory**: The canonical filesystem location where an application stores its configuration, logs, and data files.
- **AppPersona**: Class from `ccai.thisapp.persona` that stores persona attributes as class variables (AM_NAME, AM_PRESENCE_DIR, AM_LOG_DIRECTORY, AM_SETTINGS_FILENAME, etc.).
- **PersonaVariablesDesc**: Variable descriptor class from `ccai.thisapp.wellknown` that defines persona-related configuration variables.
- **WebAppPersona**: Web-specific extension of AppPersona for storing web application persona attributes.
- **ContextPaths**: A hierarchical tree structure for storing and retrieving runtime values by path (e.g., `/environment/presence/*`).
- **WebApplicationSingleton**: The global accessor function in `ccai.webworks.wellknown` that returns the active `WebApplication` instance.
- **ThisApplicationSingleton**: The global accessor function from `ccai.thisapp.wellknown` that returns the active `ThisApplication` instance.

## Requirements

### Requirement 1: WebApplication Root Class

**User Story:** As a web application developer, I want a root application class with database lifecycle hooks, so that I can define my database bootstrap flow once and reuse it during CLI or worker startup.

#### Acceptance Criteria

1. THE WebApplication class SHALL extend `ccai.thisapp.wellknown.ThisApplication` and inherit all persona and variable stack functionality.
2. THE WebApplication class SHALL provide an overridable `prepare_database` hook for database preparation tasks such as migrations.
3. THE WebApplication class SHALL provide an overridable `connect_database` hook for establishing database connections and session pools.
4. THE WebApplication class SHALL provide an overridable `startup_database` hook for database startup operations.
5. THE WebApplication class SHALL provide an overridable `ensure_database_ready` hook for verifying database readiness.
6. WHEN a project-level application subclasses WebApplication, THE subclass SHALL be able to add helpers such as ORM models and DI containers while inheriting the presence and variable stack from ThisApplication.
7. WHEN a database hook method is called, THE WebApplication SHALL allow the method to access persona variables and context paths for configuration.
8. THE WebApplication constructor SHALL require a `from_establish_webapp_persona=True` keyword argument to prevent direct instantiation, mirroring the pattern used by ThisApplication.
9. THE WebApplication constructor SHALL pass `from_establish_app_persona=True` to the parent ThisApplication constructor to satisfy its instantiation guard.

### Requirement 2: Establish WebApp Persona

**User Story:** As a framework user, I want a helper function to establish the web application persona, so that I can initialize the application singleton with consistent configuration across all entry points.

#### Acceptance Criteria

1. THE establish_webapp_persona function SHALL create and instantiate the WebApplication singleton, mirroring the pattern used by `ccai.thisapp.persona.establish_app_persona` for ThisApplication.
2. THE establish_webapp_persona function SHALL wire the singleton into `ccai.webworks.wellknown.THISWEBAPPLICATION_SINGLETON` and also set `ccai.thisapp.wellknown.THISAPPLICATION_SINGLETON` to the same instance.
3. THE establish_webapp_persona function SHALL accept the persona fields: `name`, `logger_name`, `log_basename`, `presence_dir`, `log_directory`, `settings_file`, `extensions`, and `service_name`.
4. THE establish_webapp_persona function SHALL accept an optional `application_cls` parameter to allow callers to swap in custom WebApplication subclasses (defaulting to WebApplication if not provided).
5. WHEN no presence_dir is supplied, THE establish_webapp_persona function SHALL default to `~/<appname>` using `os.path.join("~", name.lower())`.
6. WHEN no log_directory is supplied, THE establish_webapp_persona function SHALL default to `<presence_dir>/logs`.
7. WHEN no settings_file is supplied, THE establish_webapp_persona function SHALL default to `<presence_dir>/settings.config`.
8. WHEN settings_file is just a filename (basename equals the full value), THE establish_webapp_persona function SHALL join it with presence_dir.
9. WHEN settings_file is a path (not just a filename), THE establish_webapp_persona function SHALL use `os.path.abspath(os.path.expandvars(os.path.expanduser(settings_file)))`.
10. WHEN instantiation completes, THE establish_webapp_persona function SHALL call `override_variable_value` on the singleton for all PersonaVariablesDesc variables (AM_NAME, AM_LOGGER_NAME, AM_LOG_BASENAME, AM_LOG_DIRECTORY, AM_PRESENCE_DIR, AM_SERVICE_NAME, AM_EXTENSIONS).
11. THE establish_webapp_persona function SHALL return the created WebApplication singleton instance to the caller.
12. THE establish_webapp_persona function SHALL populate `ccai.thisapp.persona.AppPersona` class attributes with the resolved persona values before creating the singleton.

### Requirement 3: Presence Directory and Configuration Layout

**User Story:** As a runtime system, I want well-defined canonical paths for configuration, logs, and data, so that subsystems can discover directories without knowing how they were derived.

#### Acceptance Criteria

1. THE `ccai.thisapp.persona.AppPersona` class attributes SHALL capture the canonical paths including AM_PRESENCE_DIR, AM_LOG_DIRECTORY, and AM_SETTINGS_FILENAME.
2. THE Presence_Directory system SHALL provide a well-defined location to create config, log, and data folders before the router starts.
3. WHEN presence information is established, THE system SHALL flow the paths into ContextPaths at `/environment/presence/*` via the ThisApplication context methods.
4. WHEN other subsystems such as logging or pipelines need directory information, THE system SHALL allow discovery through ContextPaths without requiring knowledge of derivation logic.
5. THE settings.config file SHALL be stored in the presence directory by default.
6. WHEN the ConfigParser inside ThisApplication or WebApplication hydrates defaults, THE system SHALL read from the settings.config file in the presence directory.
7. WHEN overrides are needed, THE system SHALL allow overrides from environment variables or direct calls to `override_variable_value` on the singleton.

### Requirement 4: Variable Descriptions and Accessors

**User Story:** As a configuration consumer, I want a single source of truth for configuration values, so that documentation generators and runtime code stay in sync with the persona.

#### Acceptance Criteria

1. THE `ccai.thisapp.wellknown.PersonaVariablesDesc` class SHALL provide variable descriptors for all persona-related configuration (AM_NAME, AM_LOGGER_NAME, AM_LOG_BASENAME, AM_LOG_DIRECTORY, AM_PRESENCE_DIR, AM_SERVICE_NAME, AM_EXTENSIONS, AM_SETTINGS_FILENAME).
2. THE PersonaVariablesDesc.items() method SHALL return an iterable of all variable descriptors for enumeration.
3. THE ThisApplication.override_variable_value method SHALL allow setting variable values that take precedence over environment and settings sources.
4. THE ThisApplication.get_variable_value method SHALL resolve variable values respecting the configured lookup order.
5. WHEN documentation generators list every variable descriptor, THE system SHALL provide accurate metadata about each variable.
6. WHEN runtime code references a persona variable, THE system SHALL return the value in sync with the established persona.

### Requirement 5: Wellknown Singletons

**User Story:** As a framework user, I want consistent singleton access patterns, so that legacy code and new code can access the application instance through either accessor.

#### Acceptance Criteria

1. THE `ccai.webworks.wellknown` module SHALL define a `THISWEBAPPLICATION_SINGLETON` variable to hold the WebApplication instance.
2. THE `ccai.webworks.wellknown.ThisWebApplicationSingleton()` function SHALL return the WebApplication root instance.
3. THE ThisWebApplicationSingleton function SHALL mirror the behavior of `ccai.thisapp.wellknown.ThisApplicationSingleton()` but surface the richer WebApplication type.
4. WHEN establish_webapp_persona runs, BOTH ThisWebApplicationSingleton and ThisApplicationSingleton SHALL point to the same object.
5. WHEN legacy code calls ThisApplicationSingleton, THE system SHALL return the same instance as ThisWebApplicationSingleton for consistency.
6. THE singleton lock from `ccai.thisapp.wellknown.SINGLETON_LOCK` SHALL be reused to guard initialization.
7. IF multiple personas are attempted to be established, THEN THE system SHALL prevent the second establishment and maintain the original singleton.
8. THE ThisWebApplicationSingleton function SHALL raise `ccai.thisapp.wellknown.SemanticError` if called before establish_webapp_persona has been called.
