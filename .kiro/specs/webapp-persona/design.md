# Design Document: Web Application Persona & Presence

## Overview

This design document describes the architecture and implementation approach for the Web Application Persona & Presence feature. The feature provides the foundational infrastructure for web applications in the ccai framework, extending the base `ThisApplication` (from `codecraftai-this-app` package) with web-specific database lifecycle hooks, persona establishment, presence directory management, and singleton access patterns.

The design follows a layered approach where `WebApplication` extends `ccai.thisapp.wellknown.ThisApplication`, inheriting all persona and variable stack functionality while adding web-specific hooks. The `establish_webapp_persona` function serves as the primary entry point for initializing the application singleton with consistent configuration.

## Dependencies

This feature depends on the `codecraftai-this-app` package which provides:

| Component | Import Path | Description |
|-----------|-------------|-------------|
| `ThisApplication` | `ccai.thisapp.wellknown` | Base application class with persona management, context, config parser |
| `establish_app_persona` | `ccai.thisapp.persona` | Reference implementation for persona establishment pattern |
| `AppPersona` | `ccai.thisapp.persona` | Class-level storage for persona attributes (AM_NAME, AM_PRESENCE_DIR, etc.) |
| `PersonaVariablesDesc` | `ccai.thisapp.wellknown` | Variable descriptors for persona configuration |
| `SINGLETON_LOCK` | `ccai.thisapp.wellknown` | Thread lock for singleton initialization |
| `THISAPPLICATION_SINGLETON` | `ccai.thisapp.wellknown` | Global singleton variable |
| `ThisApplicationSingleton()` | `ccai.thisapp.wellknown` | Accessor function for the singleton |
| `SemanticError` | `ccai.thisapp.wellknown` | Exception for semantic errors |
| `APP_PERSONA_ESTABLISHED` | `ccai.thisapp.persona` | Flag to track if persona is established |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Application Layer                             │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Project-Level WebApp Subclass               │    │
│  │  (e.g., PortalWebApp with ORM models, DI containers)    │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    WebApplication                        │    │
│  │  - prepare_database()                                    │    │
│  │  - connect_database()                                    │    │
│  │  - startup_database()                                    │    │
│  │  - ensure_database_ready()                               │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    ThisApplication                       │    │
│  │  - Persona management                                    │    │
│  │  - Variable stack                                        │    │
│  │  - Context paths                                         │    │
│  │  - ConfigParser integration                              │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    Singleton Access Layer                        │
│  ┌───────────────────────────┐    ┌──────────────────────┐      │
│  │ThisWebApplicationSingleton│◄──►│ThisApplicationSingleton│     │
│  └───────────────────────────┘    └──────────────────────┘      │
│                              │                                   │
│                    ┌─────────┴─────────┐                        │
│                    │   SINGLETON_LOCK   │                        │
│                    └───────────────────┘                        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    Configuration Layer                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   AppVarDesc    │  │   AppVarSet     │  │  AppVarAccessor │ │
│  │ (descriptors)   │  │ (groupings)     │  │ (lazy access)   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    ContextPaths                          │    │
│  │  /environment/presence/dir                               │    │
│  │  /environment/presence/logs                              │    │
│  │  /environment/presence/settings                          │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### WebApplication Class

```python
from ccai.thisapp.wellknown import ThisApplication, SemanticError

class WebApplication(ThisApplication):
    """
    Root class for web applications extending ThisApplication with
    database lifecycle hooks.
    """
    
    def __init__(self, *, name: str, logger_name: str, log_basename: str, 
                 presence_dir: str, log_directory: str, settings_file: str, 
                 extensions: str, service_name: str, **other):
        """
        Constructs a WebApplication object.
        
        :param name: A one-word short name for the application.
        :param logger_name: Name for the logger.
        :param log_basename: Base name for log files.
        :param presence_dir: The directory for application presence.
        :param log_directory: The directory for log files.
        :param settings_file: The path to the settings file.
        :param extensions: Extension modules to load.
        :param service_name: Service identifier for distributed systems.
        """
        if "from_establish_webapp_persona" not in other:
            errmsg = "The `WebApplication` singleton object should not be instantiated directly. " \
                     "Call `establish_webapp_persona` to establish application wide presence settings " \
                     "and then use the wellknown singleton to access the application presence instance."
            raise SemanticError(errmsg)
        
        # Pass from_establish_app_persona=True to satisfy parent's instantiation guard
        super().__init__(
            name=name, logger_name=logger_name, log_basename=log_basename,
            presence_dir=presence_dir, log_directory=log_directory,
            settings_file=settings_file, extensions=extensions,
            service_name=service_name, from_establish_app_persona=True
        )
    
    def prepare_database(self) -> None:
        """
        Hook for database preparation tasks such as running migrations.
        Override in subclasses to implement project-specific logic.
        """
        pass
    
    def connect_database(self) -> None:
        """
        Hook for establishing database connections and session pools.
        Override in subclasses to implement project-specific logic.
        """
        pass
    
    def startup_database(self) -> None:
        """
        Hook for database startup operations.
        Override in subclasses to implement project-specific logic.
        """
        pass
    
    def ensure_database_ready(self) -> bool:
        """
        Hook for verifying database readiness.
        Override in subclasses to implement project-specific logic.
        
        Returns:
            True if database is ready, False otherwise.
        """
        return True
```

### establish_webapp_persona Function

```python
import os
from typing import Optional, Type

from ccai.thisapp.persona import AppPersona
from ccai.thisapp.wellknown import (
    SINGLETON_LOCK, THISAPPLICATION_SINGLETON, 
    PersonaVariablesDesc, SemanticError
)
from ccai.webworks import wellknown as webworks_wellknown
from ccai.thisapp import wellknown as thisapp_wellknown

WEBAPP_PERSONA_ESTABLISHED = False

def establish_webapp_persona(
    *, 
    name: str,
    logger_name: str,
    log_basename: str,
    presence_dir: Optional[str] = None,
    log_directory: Optional[str] = None,
    settings_file: Optional[str] = None,
    extensions: Optional[str] = None,
    service_name: Optional[str] = None,
    application_cls: Optional[Type['WebApplication']] = None
) -> 'WebApplication':
    """
    Establish the web application persona and initialize the singleton.
    
    Mirrors the pattern used by ccai.thisapp.persona.establish_app_persona
    but instantiates WebApplication and wires it into both wellknown modules.
    
    Args:
        name: Application name used for defaults and identification.
        logger_name: Name for the logger.
        log_basename: Base name for log files.
        presence_dir: Root directory for app presence (defaults to ~/<name>).
        log_directory: Directory for log files (defaults to <presence_dir>/logs).
        settings_file: Path to settings file (defaults to <presence_dir>/settings.config).
        extensions: Extension modules to load.
        service_name: Service identifier for distributed systems.
        application_cls: Custom WebApplication subclass to instantiate.
    
    Returns:
        The initialized WebApplication singleton.
    
    Raises:
        PersonaAlreadyEstablishedError: If persona was already established.
        SemanticError: If THISAPPLICATION_SINGLETON is already set.
    """
    global WEBAPP_PERSONA_ESTABLISHED
    
    if WEBAPP_PERSONA_ESTABLISHED:
        raise PersonaAlreadyEstablishedError(AppPersona.AM_NAME)
    
    WEBAPP_PERSONA_ESTABLISHED = True
    
    # Populate AppPersona class attributes (same pattern as establish_app_persona)
    AppPersona.AM_NAME = name
    AppPersona.AM_LOGGER_NAME = logger_name
    AppPersona.AM_LOG_BASENAME = log_basename
    
    if presence_dir is not None:
        AppPersona.AM_PRESENCE_DIR = presence_dir
    else:
        AppPersona.AM_PRESENCE_DIR = os.path.join("~", name.lower())
    
    if log_directory is not None:
        AppPersona.AM_LOG_DIRECTORY = log_directory
    else:
        AppPersona.AM_LOG_DIRECTORY = os.path.join(AppPersona.AM_PRESENCE_DIR, "logs")
    
    if settings_file is not None:
        # If we are only given the filename, the file must be located in the presence directory
        if os.path.basename(settings_file) == settings_file:
            AppPersona.AM_SETTINGS_FILENAME = os.path.join(AppPersona.AM_PRESENCE_DIR, settings_file)
        else:
            AppPersona.AM_SETTINGS_FILENAME = os.path.abspath(os.path.expandvars(os.path.expanduser(settings_file)))
    else:
        AppPersona.AM_SETTINGS_FILENAME = os.path.join(AppPersona.AM_PRESENCE_DIR, 'settings.config')
    
    AppPersona.AM_EXTENSIONS = extensions
    AppPersona.AM_SERVICE_NAME = service_name
    
    # Check that THISAPPLICATION_SINGLETON is not already set
    if thisapp_wellknown.THISAPPLICATION_SINGLETON is not None:
        errmsg = "The singleton 'wellknown.THISAPPLICATION_SINGLETON' must not be set when calling 'establish_webapp_persona'"
        raise SemanticError(errmsg)
    
    # Determine which class to instantiate
    if application_cls is None:
        application_cls = WebApplication
    
    # Create the singleton instance
    this_app = application_cls(
        name=name, logger_name=logger_name, log_basename=log_basename,
        presence_dir=AppPersona.AM_PRESENCE_DIR,
        log_directory=AppPersona.AM_LOG_DIRECTORY,
        settings_file=AppPersona.AM_SETTINGS_FILENAME,
        extensions=AppPersona.AM_EXTENSIONS,
        service_name=AppPersona.AM_SERVICE_NAME,
        from_establish_webapp_persona=True
    )
    
    # Wire into both wellknown modules
    SINGLETON_LOCK.acquire()
    try:
        webworks_wellknown.THISWEBAPPLICATION_SINGLETON = this_app
        thisapp_wellknown.THISAPPLICATION_SINGLETON = this_app
    finally:
        SINGLETON_LOCK.release()
    
    # Override variable values for PersonaVariablesDesc
    this_app.override_variable_value(PersonaVariablesDesc.AM_NAME, this_app.name)
    this_app.override_variable_value(PersonaVariablesDesc.AM_LOGGER_NAME, AppPersona.AM_LOGGER_NAME)
    this_app.override_variable_value(PersonaVariablesDesc.AM_LOG_BASENAME, AppPersona.AM_LOG_BASENAME)
    this_app.override_variable_value(PersonaVariablesDesc.AM_LOG_DIRECTORY, AppPersona.AM_LOG_DIRECTORY)
    this_app.override_variable_value(PersonaVariablesDesc.AM_PRESENCE_DIR, AppPersona.AM_PRESENCE_DIR)
    this_app.override_variable_value(PersonaVariablesDesc.AM_SERVICE_NAME, AppPersona.AM_SERVICE_NAME)
    this_app.override_variable_value(PersonaVariablesDesc.AM_EXTENSIONS, AppPersona.AM_EXTENSIONS)
    
    return this_app
```

### AppVarDesc Class

```python
class AppVarDesc:
    """
    Descriptor for application variables with configurable lookup order.
    """
    
    def __init__(
        self,
        name: str,
        sources: VariableSource,
        default: Optional[Any] = None,
        context_path: Optional[str] = None,
        description: Optional[str] = None
    ):
        """
        Args:
            name: Variable name (e.g., AM_PRESENCE_DIR).
            sources: Bit flags for lookup order (environment, settings, defaults).
            default: Default value if not found in other sources.
            context_path: Optional path to mirror value in ContextPaths.
            description: Human-readable description for documentation.
        """
        self.name = name
        self.sources = sources
        self.default = default
        self.context_path = context_path
        self.description = description
```

### AppVarAccessor Class

```python
class AppVarAccessor:
    """
    Descriptor providing lazy, read-only access to application variables.
    """
    
    def __init__(self, var_desc: AppVarDesc):
        """
        Args:
            var_desc: The variable descriptor to access.
        """
        self.var_desc = var_desc
    
    def __get__(self, obj, objtype=None) -> Any:
        """
        Resolve the variable value from the global singleton.
        
        Returns:
            The resolved variable value.
        
        Raises:
            PersonaNotEstablishedError: If no persona has been established.
        """
        pass
    
    def __set__(self, obj, value):
        """
        Prevent direct assignment to enforce centralized overrides.
        
        Raises:
            AttributeError: Always, as accessors are read-only.
        """
        raise AttributeError("AppVarAccessor is read-only. Use override_variable_value().")
```

### VariableSource Enum

```python
class VariableSource(Flag):
    """
    Bit flags indicating variable lookup sources and order.
    """
    NONE = 0
    ENVIRONMENT = auto()  # Check environment variables
    SETTINGS = auto()     # Check settings file
    DEFAULTS = auto()     # Use default value
    
    # Common combinations
    ENV_THEN_SETTINGS = ENVIRONMENT | SETTINGS
    ALL = ENVIRONMENT | SETTINGS | DEFAULTS
```

### Wellknown Singleton Functions

```python
# In ccai.webworks.wellknown

from typing import Optional
from ccai.thisapp.wellknown import SINGLETON_LOCK, SemanticError

THISWEBAPPLICATION_SINGLETON: Optional['WebApplication'] = None

def ThisWebApplicationSingleton() -> 'WebApplication':
    """
    Return the global WebApplication singleton.
    
    Returns:
        The WebApplication instance.
    
    Raises:
        SemanticError: If no persona has been established.
    """
    global THISWEBAPPLICATION_SINGLETON
    
    SINGLETON_LOCK.acquire()
    try:
        if THISWEBAPPLICATION_SINGLETON is None:
            errmsg = "You must call 'establish_webapp_persona' early in your application startup to define " \
                     "your application's presence settings before attempting to use the `WebApplication` " \
                     "object or its corresponding singleton."
            raise SemanticError(errmsg)
    finally:
        SINGLETON_LOCK.release()
    
    return THISWEBAPPLICATION_SINGLETON
```

Note: `ThisApplicationSingleton()` is already provided by `ccai.thisapp.wellknown` and will return the same instance after `establish_webapp_persona` is called.

## Data Models

### AppPersona (from codecraftai-this-app)

The `AppPersona` class from `ccai.thisapp.persona` stores persona attributes as class variables:

```python
# Provided by codecraftai-this-app package
class AppPersona:
    """
    Class-level storage for persona attributes.
    These are set by establish_app_persona or establish_webapp_persona.
    """
    AM_NAME: str = None
    AM_LOGGER_NAME: str = None
    AM_LOG_BASENAME: str = None
    AM_PRESENCE_DIR: str = None
    AM_LOG_DIRECTORY: str = None
    AM_SETTINGS_FILENAME: str = None
    AM_EXTENSIONS: str = None
    AM_SERVICE_NAME: str = None
```

### PersonaVariablesDesc (from codecraftai-this-app)

The `PersonaVariablesDesc` class from `ccai.thisapp.wellknown` provides variable descriptors:

```python
# Provided by codecraftai-this-app package
class PersonaVariablesDesc:
    """
    Variable descriptors for persona-related configuration.
    """
    AM_NAME = ...
    AM_LOGGER_NAME = ...
    AM_LOG_BASENAME = ...
    AM_PRESENCE_DIR = ...
    AM_LOG_DIRECTORY = ...
    AM_SETTINGS_FILENAME = ...
    AM_EXTENSIONS = ...
    AM_SERVICE_NAME = ...
    
    @classmethod
    def items(cls):
        """Return iterable of all variable descriptors."""
        ...
```

</text>
</invoke>


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: WebApplication Inheritance Preservation

*For any* WebApplication instance or subclass, the instance SHALL be an instance of ThisApplication and SHALL have access to all inherited persona and variable stack functionality.

**Validates: Requirements 1.1, 1.6**

### Property 2: Singleton Identity Consistency

*For any* established web application persona, calling ThisWebApplicationSingleton() and ThisApplicationSingleton() SHALL return the exact same object instance (identity equality).

**Validates: Requirements 2.2, 5.4**

### Property 3: Default Path Computation

*For any* application name and optional presence_dir, when establish_webapp_persona is called without explicit paths:
- If presence_dir is not supplied, it SHALL default to `~/<appname>`
- If log_directory is not supplied, it SHALL default to `<presence_dir>/logs`
- If settings_file is not supplied, it SHALL default to `<presence_dir>/settings.config`

**Validates: Requirements 2.5, 2.6, 2.7**

### Property 4: Absolute Path Preservation

*For any* absolute or expanded path passed as settings_file to establish_webapp_persona, the resulting persona SHALL use that exact path without modification.

**Validates: Requirements 2.8**

### Property 5: Custom Class Instantiation

*For any* custom WebApplication subclass passed via application_cls parameter, establish_webapp_persona SHALL instantiate that specific class and the singleton SHALL be an instance of that class.

**Validates: Requirements 2.4**

### Property 6: Accessor Resolution Consistency

*For any* established persona, all AppVarAccessor descriptors SHALL resolve to values that match the established persona metadata, and resolution SHALL occur lazily at access time.

**Validates: Requirements 2.9, 4.4, 4.7**

### Property 7: ContextPaths Integration

*For any* established persona with variables that have context_path configured, the values SHALL be mirrored into ContextPaths at the specified paths, and subsystems SHALL be able to discover these values through ContextPaths queries.

**Validates: Requirements 3.3, 3.4, 4.2**

### Property 8: Variable Override Precedence

*For any* variable with VariableSource flags set, the lookup order SHALL respect the configured sources (environment → settings → defaults), and explicit overrides via override_variable_value SHALL take precedence over all sources.

**Validates: Requirements 3.7, 4.1**

### Property 9: Read-Only Accessor Enforcement

*For any* AppVarAccessor descriptor, attempting to assign a value directly SHALL raise an AttributeError, ensuring all overrides happen centrally on the application object.

**Validates: Requirements 4.5**

### Property 10: Singleton Establishment Guard

*For any* sequence of establish_webapp_persona calls, only the first call SHALL succeed; subsequent calls SHALL raise PersonaAlreadyEstablishedError and the original singleton SHALL remain unchanged.

**Validates: Requirements 5.6**

### Property 11: Thread-Safe Initialization

*For any* concurrent calls to establish_webapp_persona from multiple threads, exactly one call SHALL succeed and all threads SHALL observe the same singleton instance after initialization completes.

**Validates: Requirements 5.5**

## Error Handling

### PersonaAlreadyEstablishedError

Raised when `establish_webapp_persona` is called after a persona has already been established. The error message should include the name of the existing persona to aid debugging.

```python
class PersonaAlreadyEstablishedError(Exception):
    """Raised when attempting to establish a persona that already exists."""
    
    def __init__(self, existing_name: str):
        self.existing_name = existing_name
        super().__init__(
            f"Persona already established with name '{existing_name}'. "
            "Cannot establish a new persona."
        )
```

### PersonaNotEstablishedError

Raised when accessing singleton functions or AppVarAccessors before a persona has been established.

```python
class PersonaNotEstablishedError(Exception):
    """Raised when accessing persona-dependent resources before establishment."""
    
    def __init__(self):
        super().__init__(
            "No persona has been established. "
            "Call establish_webapp_persona() first."
        )
```

### VariableResolutionError

Raised when a required variable cannot be resolved from any configured source.

```python
class VariableResolutionError(Exception):
    """Raised when a variable cannot be resolved from any source."""
    
    def __init__(self, var_name: str, sources: VariableSource):
        self.var_name = var_name
        self.sources = sources
        super().__init__(
            f"Cannot resolve variable '{var_name}' from sources: {sources}"
        )
```

## Testing Strategy

### Unit Tests

Unit tests should cover:

1. **Class Structure Tests**
   - Verify WebApplication extends ThisApplication
   - Verify all database hook methods exist and are callable
   - Verify hook methods can be overridden in subclasses

2. **Function Signature Tests**
   - Verify establish_webapp_persona accepts all documented parameters
   - Verify default parameter values

3. **Error Condition Tests**
   - Verify PersonaAlreadyEstablishedError on double establishment
   - Verify PersonaNotEstablishedError on premature access
   - Verify AttributeError on accessor assignment

4. **Path Computation Tests**
   - Verify default presence_dir computation
   - Verify default log_directory computation
   - Verify default settings_file computation
   - Verify absolute path preservation

### Property-Based Tests

Property-based tests should use the `testbase` framework with minimum 100 iterations per property. Each test should be tagged with the property it validates.

**Testing Framework**: testbase (as specified in AGENTS.md)

**Property Test Configuration**:
- Minimum iterations: 100
- Tag format: `Feature: webapp-persona, Property N: <property_text>`

**Generator Requirements**:
- Generate valid application names (non-empty strings, valid filesystem characters)
- Generate valid path strings (absolute and relative)
- Generate valid VariableSource flag combinations
- Generate concurrent thread scenarios for thread-safety tests

### Test Organization

Following the repository conventions from AGENTS.md:

```
source/testroots/ccai/tests/singlehost/webworks/persona/
├── test_webapplication.py       # WebApplication class tests
├── test_establish_persona.py    # establish_webapp_persona tests
└── test_wellknown_singletons.py # Singleton access tests
```

### Integration Points

- Integration with `ccai.thisapp` module for base functionality (ThisApplication, AppPersona, PersonaVariablesDesc)
- Integration with ConfigParser for settings file reading (inherited from ThisApplication)
- Integration with Context for value storage (inherited from ThisApplication)
- Integration with logging subsystem for log directory discovery
