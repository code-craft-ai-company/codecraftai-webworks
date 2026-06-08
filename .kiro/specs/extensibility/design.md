# Design Document: Extensibility

## Overview

This design document describes the architecture and implementation approach for the Extensibility feature. The feature provides an Extension/Plugin API that allows third-party developers and internal teams to extend the ccai web framework with custom functionality without modifying the core codebase.

The design follows a registry-based approach with clear separation between extension discovery, lifecycle management, and hook execution. Extensions are self-contained modules that register with the framework through well-defined extension points and hooks.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Application Layer                                │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                    WebApplication                                  │  │
│  │  - Initializes Extension_Registry                                 │  │
│  │  - Triggers lifecycle events                                      │  │
│  │  - Provides Extension_Context                                     │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Registry Layer                                   │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                    Extension_Registry                              │  │
│  │  - Extension registration and discovery                           │  │
│  │  - Dependency resolution (topological sort)                       │  │
│  │  - Lifecycle management (init, activate, deactivate, shutdown)    │  │
│  │  - State tracking                                                 │  │
│  │  - Extension point management                                     │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                    │                                     │
│           ┌────────────────────────┼────────────────────────┐           │
│           ▼                        ▼                        ▼           │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐     │
│  │ Extension_Loader│    │   Hook_Manager  │    │ Extension_Point │     │
│  │                 │    │                 │    │    Registry     │     │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘     │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Extension Layer                                  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐   │
│  │  Extension  │ │  Extension  │ │  Extension  │ │   Extension     │   │
│  │      A      │ │      B      │ │      C      │ │   (custom)      │   │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Context Layer                                    │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                    Extension_Context                               │  │
│  │  - Application configuration access                               │  │
│  │  - Logger access                                                  │  │
│  │  - Service registry                                               │  │
│  │  - Endpoint registry access                                       │  │
│  │  - URL node map access                                            │  │
│  │  - Dependency access                                              │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### Extension Base Class

```python
class Extension(ABC):
    """
    Base class for all extensions. Subclass this to create custom extensions.
    """
    
    # Class attributes for extension metadata
    name: str = ""
    version: str = "0.0.0"
    description: str = ""
    dependencies: List[str] = []
    optional_dependencies: List[str] = []
    
    def __init__(self):
        self._context: Optional['ExtensionContext'] = None
        self._state: ExtensionState = ExtensionState.REGISTERED
    
    @property
    def context(self) -> 'ExtensionContext':
        """
        Get the extension context.
        
        Returns:
            The extension context providing access to framework services.
        
        Raises:
            ExtensionNotInitializedError: If accessed before initialization.
        """
        if self._context is None:
            raise ExtensionNotInitializedError(self.name)
        return self._context
    
    @property
    def state(self) -> 'ExtensionState':
        """Get the current extension state."""
        return self._state
    
    def initialize(self, context: 'ExtensionContext') -> None:
        """
        Initialize the extension with the provided context.
        
        Args:
            context: The extension context providing framework services.
        """
        self._context = context
        self._state = ExtensionState.INITIALIZED
    
    def activate(self) -> None:
        """
        Activate the extension. Called when the extension is enabled.
        Override this method to perform activation logic.
        """
        self._state = ExtensionState.ACTIVE
    
    def deactivate(self) -> None:
        """
        Deactivate the extension. Called when the extension is disabled.
        Override this method to perform deactivation logic.
        """
        self._state = ExtensionState.DISABLED
    
    def shutdown(self) -> None:
        """
        Shutdown the extension. Called during application shutdown.
        Override this method to perform cleanup logic.
        """
        pass
```

### ExtensionRegistry Class

```python
class ExtensionRegistry:
    """
    Central registry for managing extensions.
    """
    
    def __init__(self, app_context: 'ApplicationContext'):
        """
        Args:
            app_context: The application context for creating extension contexts.
        """
        self._app_context = app_context
        self._extensions: Dict[str, Extension] = {}
        self._extension_states: Dict[str, ExtensionState] = {}
        self._hook_manager = HookManager()
        self._extension_points: Dict[str, ExtensionPointDefinition] = {}
        self._contributions: Dict[str, List[Any]] = {}
        self._error_counts: Dict[str, int] = {}
        self._error_threshold: int = 5
    
    def register(self, extension: Extension) -> None:
        """
        Register an extension manually.
        
        Args:
            extension: The extension instance to register.
        
        Raises:
            ExtensionAlreadyRegisteredError: If extension name already exists.
        """
        pass
    
    def discover(self, paths: List[Path]) -> List[str]:
        """
        Discover and register extensions from the given paths.
        
        Args:
            paths: List of directory paths to search for extensions.
        
        Returns:
            List of discovered extension names.
        """
        pass
    
    def get(self, name: str) -> Optional[Extension]:
        """
        Get a registered extension by name.
        
        Args:
            name: The extension name.
        
        Returns:
            The extension instance or None if not found.
        """
        return self._extensions.get(name)
    
    def list(self) -> List[Extension]:
        """
        List all registered extensions.
        
        Returns:
            List of all registered extension instances.
        """
        return list(self._extensions.values())
    
    def enable(self, name: str) -> None:
        """
        Enable a registered extension.
        
        Args:
            name: The extension name.
        
        Raises:
            ExtensionNotFoundError: If extension is not registered.
            ExtensionDependencyError: If dependencies are not satisfied.
        """
        pass
    
    def disable(self, name: str) -> None:
        """
        Disable an active extension.
        
        Args:
            name: The extension name.
        
        Raises:
            ExtensionNotFoundError: If extension is not registered.
        """
        pass
    
    def initialize_all(self) -> None:
        """
        Initialize all registered extensions in dependency order.
        
        Raises:
            ExtensionDependencyError: If circular dependencies detected.
        """
        pass
    
    def get_state(self, name: str) -> ExtensionState:
        """
        Get the state of an extension.
        
        Args:
            name: The extension name.
        
        Returns:
            The extension state.
        """
        return self._extension_states.get(name, ExtensionState.UNKNOWN)
    
    def query_by_capability(self, capability: str) -> List[Extension]:
        """
        Query extensions that provide a specific capability.
        
        Args:
            capability: The capability name.
        
        Returns:
            List of extensions providing the capability.
        """
        pass
    
    def reload(self, name: str) -> None:
        """
        Hot-reload an extension.
        
        Args:
            name: The extension name.
        """
        pass
```

### ExtensionLoader Class

```python
class ExtensionLoader:
    """
    Discovers and loads extensions from various sources.
    """
    
    def __init__(self, registry: ExtensionRegistry):
        """
        Args:
            registry: The extension registry to register discovered extensions.
        """
        self._registry = registry
        self._lazy_extensions: Dict[str, Callable[[], Extension]] = {}
    
    def discover_from_paths(self, paths: List[Path]) -> List[ExtensionManifest]:
        """
        Discover extensions from directory paths.
        
        Args:
            paths: List of paths to search.
        
        Returns:
            List of discovered extension manifests.
        """
        pass
    
    def discover_from_entry_points(self, group: str = "ccai.extensions") -> List[ExtensionManifest]:
        """
        Discover extensions from Python entry points.
        
        Args:
            group: The entry point group name.
        
        Returns:
            List of discovered extension manifests.
        """
        pass
    
    def load_manifest(self, path: Path) -> ExtensionManifest:
        """
        Load an extension manifest from a file.
        
        Args:
            path: Path to the manifest file.
        
        Returns:
            The parsed extension manifest.
        
        Raises:
            ExtensionManifestError: If manifest is invalid.
        """
        pass
    
    def load_extension(self, manifest: ExtensionManifest) -> Extension:
        """
        Load an extension from its manifest.
        
        Args:
            manifest: The extension manifest.
        
        Returns:
            The loaded extension instance.
        """
        pass
    
    def filter_by_pattern(
        self,
        manifests: List[ExtensionManifest],
        pattern: str
    ) -> List[ExtensionManifest]:
        """
        Filter manifests by name pattern.
        
        Args:
            manifests: List of manifests to filter.
            pattern: Glob pattern to match.
        
        Returns:
            Filtered list of manifests.
        """
        pass
```

### ExtensionContext Class

```python
class ExtensionContext:
    """
    Context provided to extensions for accessing framework services.
    """
    
    def __init__(
        self,
        extension_name: str,
        app_context: 'ApplicationContext',
        config: Dict[str, Any]
    ):
        """
        Args:
            extension_name: The name of the extension this context belongs to.
            app_context: The application context.
            config: Extension-specific configuration.
        """
        self._extension_name = extension_name
        self._app_context = app_context
        self._config = config
        self._services: Dict[str, Any] = {}
        self._frozen = False
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get extension-specific configuration."""
        return self._config
    
    @property
    def logger(self) -> 'Logger':
        """Get a logger for this extension."""
        return self._app_context.get_logger(f"extension.{self._extension_name}")
    
    @property
    def app_config(self) -> 'ConfigurationModel':
        """Get the application configuration."""
        return self._app_context.config
    
    @property
    def endpoint_registry(self) -> 'EndpointRegistry':
        """Get the endpoint registry."""
        return self._app_context.endpoint_registry
    
    @property
    def url_node_map(self) -> 'UrlNodeMap':
        """Get the URL node map."""
        return self._app_context.url_node_map
    
    @property
    def middleware(self) -> List['Middleware']:
        """Get registered middleware."""
        return self._app_context.middleware
    
    def register_service(self, name: str, service: Any) -> None:
        """
        Register a service for other extensions to use.
        
        Args:
            name: The service name.
            service: The service instance.
        
        Raises:
            ExtensionContextFrozenError: If context is frozen.
        """
        if self._frozen:
            raise ExtensionContextFrozenError(self._extension_name)
        self._services[name] = service
    
    def get_service(self, name: str) -> Optional[Any]:
        """
        Get a registered service by name.
        
        Args:
            name: The service name.
        
        Returns:
            The service instance or None if not found.
        """
        return self._services.get(name)
    
    def has_dependency(self, name: str) -> bool:
        """
        Check if a dependency extension is available.
        
        Args:
            name: The dependency extension name.
        
        Returns:
            True if the dependency is available.
        """
        pass
    
    def get_dependency(self, name: str) -> Optional[Extension]:
        """
        Get a reference to a dependency extension.
        
        Args:
            name: The dependency extension name.
        
        Returns:
            The dependency extension or None if not available.
        """
        pass
    
    def freeze(self) -> None:
        """Freeze the context to prevent further modifications."""
        self._frozen = True
```

### HookManager Class

```python
class HookManager:
    """
    Manages hook registration and execution.
    """
    
    def __init__(self):
        self._hooks: Dict[str, List[HookRegistration]] = {}
    
    def register(
        self,
        hook_name: str,
        callback: Callable,
        priority: int = HookPriority.NORMAL,
        extension_name: Optional[str] = None,
        before: Optional[List[str]] = None,
        after: Optional[List[str]] = None
    ) -> None:
        """
        Register a hook callback.
        
        Args:
            hook_name: The name of the hook.
            callback: The callback function.
            priority: Numeric priority (lower executes first).
            extension_name: The registering extension's name.
            before: List of extension names this hook should run before.
            after: List of extension names this hook should run after.
        """
        pass
    
    def unregister(self, hook_name: str, callback: Callable) -> None:
        """
        Unregister a hook callback.
        
        Args:
            hook_name: The name of the hook.
            callback: The callback to unregister.
        """
        pass
    
    def execute(
        self,
        hook_name: str,
        *args,
        stop_on_result: bool = False,
        **kwargs
    ) -> List[Any]:
        """
        Execute all callbacks for a hook.
        
        Args:
            hook_name: The name of the hook.
            *args: Positional arguments to pass to callbacks.
            stop_on_result: If True, stop execution when a callback returns a non-None value.
            **kwargs: Keyword arguments to pass to callbacks.
        
        Returns:
            List of callback return values.
        """
        pass
    
    def get_execution_order(self, hook_name: str) -> List[str]:
        """
        Get the execution order for a hook's callbacks.
        
        Args:
            hook_name: The name of the hook.
        
        Returns:
            List of extension names in execution order.
        """
        pass
```

### ExtensionManifest Class

```python
@dataclass
class ExtensionManifest:
    """
    Metadata describing an extension.
    """
    name: str
    version: str
    entry_point: str
    description: str = ""
    author: str = ""
    license: str = ""
    homepage: str = ""
    dependencies: List[str] = field(default_factory=list)
    optional_dependencies: List[str] = field(default_factory=list)
    framework_dependencies: List[str] = field(default_factory=list)
    provides_extension_points: List[str] = field(default_factory=list)
    consumes_extension_points: List[str] = field(default_factory=list)
    config_schema: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_yaml(cls, content: str) -> 'ExtensionManifest':
        """Parse manifest from YAML content."""
        pass
    
    @classmethod
    def from_json(cls, content: str) -> 'ExtensionManifest':
        """Parse manifest from JSON content."""
        pass
    
    @classmethod
    def from_file(cls, path: Path) -> 'ExtensionManifest':
        """Load manifest from a file (auto-detect format)."""
        pass
    
    def to_yaml(self) -> str:
        """Serialize manifest to YAML."""
        pass
    
    def to_json(self) -> str:
        """Serialize manifest to JSON."""
        pass
    
    def validate(self) -> List[str]:
        """
        Validate the manifest.
        
        Returns:
            List of validation error messages (empty if valid).
        """
        pass
```

## Data Models

### ExtensionState Enum

```python
class ExtensionState(Enum):
    """States an extension can be in."""
    UNKNOWN = "unknown"
    REGISTERED = "registered"
    INITIALIZED = "initialized"
    ACTIVE = "active"
    DISABLED = "disabled"
    ERROR = "error"
    QUARANTINED = "quarantined"
```

### HookPriority Constants

```python
class HookPriority:
    """Named priority constants for hook ordering."""
    HIGHEST = 0
    HIGH = 25
    NORMAL = 50
    LOW = 75
    LOWEST = 100
```

### HookRegistration Dataclass

```python
@dataclass
class HookRegistration:
    """A registered hook callback."""
    callback: Callable
    priority: int
    extension_name: Optional[str]
    before: List[str] = field(default_factory=list)
    after: List[str] = field(default_factory=list)
```

### ExtensionPointDefinition Dataclass

```python
@dataclass
class ExtensionPointDefinition:
    """Definition of an extension point."""
    name: str
    interface: Type
    description: str = ""
    multiple: bool = True  # Whether multiple contributions are allowed
```

### LifecycleEvent Dataclass

```python
@dataclass
class LifecycleEvent:
    """An extension lifecycle event."""
    event_type: str
    extension_name: str
    timestamp: datetime
    data: Dict[str, Any] = field(default_factory=dict)
```

### ExtensionError Dataclass

```python
@dataclass
class ExtensionError:
    """Information about an extension error."""
    extension_name: str
    hook_name: Optional[str]
    exception: Exception
    timestamp: datetime
    stack_trace: str
```

</content>
</invoke>


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Extension Lifecycle Methods

*For any* Extension subclass, calling initialize() with a valid context, then activate(), then deactivate(), then shutdown() SHALL execute without error and transition the extension through the expected states (REGISTERED → INITIALIZED → ACTIVE → DISABLED).

**Validates: Requirements 1.1, 1.2, 1.3, 1.4**

### Property 2: Extension Context Access

*For any* initialized Extension, accessing the context property SHALL return the ExtensionContext provided during initialization, and accessing it before initialization SHALL raise ExtensionNotInitializedError.

**Validates: Requirements 1.5**

### Property 3: Extension Metadata Declaration

*For any* Extension subclass with name, version, and dependencies class attributes, those attributes SHALL be accessible and used for identification and dependency resolution.

**Validates: Requirements 1.6, 1.7, 1.8**

### Property 4: Registry Registration Round-Trip

*For any* Extension instance registered with the registry, calling get() with the extension's name SHALL return the same extension instance.

**Validates: Requirements 2.1, 2.3**

### Property 5: Registry List Completeness

*For any* set of registered extensions, calling list() SHALL return all registered extensions and only registered extensions.

**Validates: Requirements 2.4**

### Property 6: Extension Enable/Disable State Transitions

*For any* registered extension, calling enable() SHALL transition it to ACTIVE state and call activate(), and calling disable() SHALL transition it to DISABLED state and call deactivate().

**Validates: Requirements 2.5, 2.6, 11.2, 11.3**

### Property 7: Dependency Resolution Order

*For any* set of extensions with dependencies, the registry SHALL initialize them in topological order such that all dependencies are initialized before their dependents.

**Validates: Requirements 2.7, 12.3, 12.4**

### Property 8: Circular Dependency Detection

*For any* set of extensions with circular dependencies, the registry SHALL raise ExtensionDependencyError and not initialize any extensions in the cycle.

**Validates: Requirements 2.8**

### Property 9: Missing Dependency Error

*For any* extension with a required dependency that is not registered, attempting to initialize it SHALL raise ExtensionDependencyError.

**Validates: Requirements 2.9, 12.5**

### Property 10: Optional Dependency Handling

*For any* extension with an optional dependency that is not registered, initialization SHALL succeed and log a warning.

**Validates: Requirements 12.6**

### Property 11: Extension Discovery from Paths

*For any* directory containing valid extension manifests, calling discover() with that path SHALL register all valid extensions from that directory.

**Validates: Requirements 3.1, 3.3**

### Property 12: Manifest Format Round-Trip

*For any* valid ExtensionManifest, serializing to YAML and parsing back, or serializing to JSON and parsing back, SHALL produce an equivalent manifest.

**Validates: Requirements 4.1**

### Property 13: Manifest Required Fields Validation

*For any* manifest missing required fields (name, version, entry_point), parsing SHALL raise ExtensionManifestError.

**Validates: Requirements 4.2, 4.9, 4.10**

### Property 14: Manifest Optional Fields Parsing

*For any* manifest with optional fields (description, author, license, homepage, dependencies, config_schema), those fields SHALL be correctly parsed and accessible.

**Validates: Requirements 4.3, 4.4, 4.5, 4.6, 4.7, 4.8**

### Property 15: Hook Priority Ordering

*For any* set of hooks registered for the same event with different priorities, executing the hook SHALL call callbacks in ascending priority order (lower numbers first), and callbacks with the same priority SHALL execute in registration order.

**Validates: Requirements 5.6, 6.7, 8.1, 8.3, 8.5**

### Property 16: Hook Before/After Constraints

*For any* hook with before/after constraints referencing other extensions, the hook SHALL execute in an order satisfying those constraints, or raise HookOrderingError if constraints cannot be satisfied.

**Validates: Requirements 8.6, 8.7**

### Property 17: Request Lifecycle Hooks Execution

*For any* request processed by the framework, the before_request hooks SHALL be called before processing, after_request hooks SHALL be called after processing, and teardown_request hooks SHALL be called after the response is sent.

**Validates: Requirements 5.1, 5.2, 5.5**

### Property 18: Before Request Short-Circuit

*For any* before_request hook that returns a response, the framework SHALL short-circuit request processing and return that response without calling subsequent hooks or the handler.

**Validates: Requirements 5.8**

### Property 19: Application Lifecycle Hooks Execution

*For any* application startup, the on_app_init hook SHALL be called during initialization, on_config_loaded after configuration loading, on_routes_registered after route registration, and on_app_ready when ready to serve.

**Validates: Requirements 6.1, 6.2, 6.4, 6.5**

### Property 20: Component Registration Hooks

*For any* component registered via register_middleware, register_auth_provider, register_serializer, register_template_engine, register_error_handler, or register_cli_command hooks, the component SHALL be available through the standard framework APIs.

**Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7**

### Property 21: Component Interface Validation

*For any* component registered via a registration hook, the framework SHALL validate that it implements the required interface and reject invalid components.

**Validates: Requirements 7.8**

### Property 22: Extension Configuration Namespacing

*For any* extension with configuration, the configuration keys SHALL be namespaced by extension name (e.g., extensions.my_extension.setting).

**Validates: Requirements 9.1, 9.2, 9.3**

### Property 23: Extension Configuration Validation

*For any* extension with a configuration schema, loading the extension SHALL validate its configuration against the schema and raise ExtensionConfigurationError if validation fails.

**Validates: Requirements 9.5, 9.6**

### Property 24: Extension Configuration Defaults

*For any* extension configuration key with a default value in the schema, if the key is not provided, the default value SHALL be used.

**Validates: Requirements 9.7**

### Property 25: Extension Context Services

*For any* ExtensionContext, the app_config, logger, endpoint_registry, url_node_map, and middleware properties SHALL return the corresponding framework services.

**Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5**

### Property 26: Service Registration Round-Trip

*For any* service registered via register_service(), calling get_service() with the same name SHALL return the registered service.

**Validates: Requirements 10.6, 10.7**

### Property 27: Context Immutability After Init

*For any* ExtensionContext that has been frozen, attempting to register a service SHALL raise ExtensionContextFrozenError.

**Validates: Requirements 10.8**

### Property 28: Extension State Tracking

*For any* extension, the registry SHALL accurately track its state through all transitions (REGISTERED → INITIALIZED → ACTIVE ↔ DISABLED → ERROR/QUARANTINED).

**Validates: Requirements 11.1, 11.7**

### Property 29: Extension Reload Sequence

*For any* extension being reloaded, the framework SHALL call deactivate(), reload the module, and call activate() in that order.

**Validates: Requirements 11.5**

### Property 30: Extension Point Contribution

*For any* extension point declared with @extension_point, contributions made via contribute_to() SHALL be retrievable via get_contributions().

**Validates: Requirements 13.1, 13.3, 13.4**

### Property 31: Extension Point Interface Validation

*For any* contribution to an extension point, the framework SHALL validate that it implements the required interface and raise ExtensionPointError if it does not.

**Validates: Requirements 13.5, 13.6**

### Property 32: Error Isolation

*For any* extension that raises an exception during initialization or in a hook, the framework SHALL log the error, mark the extension as errored, and continue with other extensions/hooks.

**Validates: Requirements 14.1, 14.2, 6.8**

### Property 33: Error Threshold Quarantine

*For any* extension that exceeds the configured error threshold, the framework SHALL quarantine it and prevent further execution.

**Validates: Requirements 14.4, 14.8**

### Property 34: Dependency Availability Check

*For any* extension, calling has_dependency() SHALL return True if the dependency is registered and available, and get_dependency() SHALL return the dependency extension.

**Validates: Requirements 12.7, 12.8**

## Error Handling

### ExtensionError (Base)

Base exception for extension-related errors.

```python
class ExtensionError(Exception):
    """Base exception for extension errors."""
    
    def __init__(self, message: str, extension_name: Optional[str] = None):
        self.extension_name = extension_name
        super().__init__(message)
```

### ExtensionNotFoundError

Raised when an extension is not found in the registry.

```python
class ExtensionNotFoundError(ExtensionError):
    """Raised when an extension is not found."""
    
    def __init__(self, name: str):
        super().__init__(f"Extension not found: {name}", extension_name=name)
```

### ExtensionAlreadyRegisteredError

Raised when attempting to register an extension with a duplicate name.

```python
class ExtensionAlreadyRegisteredError(ExtensionError):
    """Raised when an extension is already registered."""
    
    def __init__(self, name: str):
        super().__init__(f"Extension already registered: {name}", extension_name=name)
```

### ExtensionDependencyError

Raised when extension dependencies cannot be resolved.

```python
class ExtensionDependencyError(ExtensionError):
    """Raised when extension dependencies cannot be resolved."""
    
    def __init__(self, message: str, extension_name: str, missing_deps: Optional[List[str]] = None):
        self.missing_deps = missing_deps or []
        super().__init__(message, extension_name=extension_name)
```

### ExtensionManifestError

Raised when an extension manifest is invalid.

```python
class ExtensionManifestError(ExtensionError):
    """Raised when an extension manifest is invalid."""
    
    def __init__(self, message: str, path: Optional[Path] = None):
        self.path = path
        super().__init__(message)
```

### ExtensionConfigurationError

Raised when extension configuration is invalid.

```python
class ExtensionConfigurationError(ExtensionError):
    """Raised when extension configuration is invalid."""
    
    def __init__(self, message: str, extension_name: str, key: Optional[str] = None):
        self.key = key
        super().__init__(message, extension_name=extension_name)
```

### ExtensionNotInitializedError

Raised when accessing context before initialization.

```python
class ExtensionNotInitializedError(ExtensionError):
    """Raised when accessing extension context before initialization."""
    
    def __init__(self, name: str):
        super().__init__(
            f"Extension '{name}' has not been initialized. "
            "Context is only available after initialize() is called.",
            extension_name=name
        )
```

### ExtensionContextFrozenError

Raised when attempting to modify a frozen context.

```python
class ExtensionContextFrozenError(ExtensionError):
    """Raised when attempting to modify a frozen extension context."""
    
    def __init__(self, extension_name: str):
        super().__init__(
            f"Cannot modify context for extension '{extension_name}': context is frozen",
            extension_name=extension_name
        )
```

### HookOrderingError

Raised when hook ordering constraints cannot be satisfied.

```python
class HookOrderingError(ExtensionError):
    """Raised when hook ordering constraints cannot be satisfied."""
    
    def __init__(self, hook_name: str, conflicting_constraints: List[str]):
        self.hook_name = hook_name
        self.conflicting_constraints = conflicting_constraints
        super().__init__(
            f"Cannot satisfy ordering constraints for hook '{hook_name}': "
            f"{', '.join(conflicting_constraints)}"
        )
```

### ExtensionPointError

Raised when an extension point operation fails.

```python
class ExtensionPointError(ExtensionError):
    """Raised when an extension point operation fails."""
    
    def __init__(self, message: str, point_name: str):
        self.point_name = point_name
        super().__init__(message)
```

## Testing Strategy

### Unit Tests

Unit tests should cover:

1. **Extension Base Class Tests**
   - Verify lifecycle methods can be called
   - Verify state transitions
   - Verify context access before/after initialization

2. **ExtensionRegistry Tests**
   - Verify registration and retrieval
   - Verify enable/disable functionality
   - Verify dependency resolution
   - Verify error handling

3. **ExtensionLoader Tests**
   - Verify path discovery
   - Verify manifest parsing
   - Verify filtering

4. **ExtensionContext Tests**
   - Verify service registration and retrieval
   - Verify framework service access
   - Verify freeze functionality

5. **HookManager Tests**
   - Verify hook registration
   - Verify priority ordering
   - Verify before/after constraints
   - Verify execution

6. **ExtensionManifest Tests**
   - Verify YAML parsing
   - Verify JSON parsing
   - Verify validation

### Property-Based Tests

Property-based tests should use the testbase framework and cover:

1. **Manifest Round-Trip** (Property 12)
   - Generate random valid manifests
   - Serialize and deserialize
   - Verify equivalence

2. **Dependency Resolution Order** (Property 7)
   - Generate random dependency graphs
   - Verify topological ordering

3. **Hook Priority Ordering** (Property 15)
   - Generate random hook registrations with priorities
   - Verify execution order

4. **Service Registration Round-Trip** (Property 26)
   - Generate random services
   - Register and retrieve
   - Verify identity

### Integration Tests

Integration tests should cover:

1. **Full Extension Lifecycle**
   - Load extension from manifest
   - Initialize, activate, deactivate, shutdown
   - Verify all hooks called

2. **Multi-Extension Scenarios**
   - Multiple extensions with dependencies
   - Verify correct initialization order
   - Verify hook execution order

3. **Error Scenarios**
   - Extension failures during lifecycle
   - Verify error isolation
   - Verify quarantine behavior

## Notes

- All tests should use the testbase framework as specified in AGENTS.md
- Test files should be placed in `source/testroots/ccai/tests/singlehost/webworks/extensibility/`
- Property-based tests should run minimum 100 iterations
