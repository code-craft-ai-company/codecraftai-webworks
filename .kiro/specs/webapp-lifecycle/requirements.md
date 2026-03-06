# Requirements Document

## Introduction

The `WebApplication` singleton currently manages only persona/identity concerns (logging, settings, service name, database hooks). Every test site and application must manually wire together the Router, Dispatcher, EndpointRegistry, and ASGIApplication with identical boilerplate code. This feature extends `WebApplication` to own the full lifecycle and state of a modern web application — including web infrastructure wiring, credential management, data profile management, configuration management, authentication management, and endpoint/blueprint registration — so that applications can be stood up with minimal ceremony.

## Glossary

- **WebApplication**: The singleton class (`automojo.webworks.persona.webapplication.WebApplication`) that extends `ThisApplication` and serves as the central object managing web application lifecycle and state.
- **Router**: The URL routing tree (`automojo.webworks.routing.router.Router`) that maps request paths and methods to endpoint handlers.
- **Dispatcher**: The request dispatcher (`automojo.webworks.routing.dispatcher.Dispatcher`) that receives an HTTP request, resolves a route via the Router, runs the middleware pipeline, and invokes the matched handler.
- **ASGIApplication**: The ASGI protocol handler (`automojo.webworks.asgi.application.ASGIApplication`) that receives raw ASGI scope/receive/send calls and delegates to HTTP, WebSocket, and lifespan handlers.
- **EndpointRegistry**: The class-level registry (`automojo.webworks.endpoints.registry.EndpointRegistry`) that collects `EndpointDescriptor` instances registered via `Endpoint.attach_at` and `RestBlueprint.attach_at`.
- **EndpointDescriptor**: A data object describing a single registered endpoint (handler, path, methods, tags, constraints, etc.).
- **Endpoint**: A base class providing the `attach_at` class-method decorator for registering standalone handler functions with the EndpointRegistry.
- **RestBlueprint**: A base class providing the `attach_at` class-method decorator for registering grouped REST handlers under a common base path with the EndpointRegistry.
- **AuthenticationSystem**: The central authentication coordinator (`automojo.webworks.authentication.system.AuthenticationSystem`) that manages a registry of `Authenticator` implementations.
- **AuthenticationMiddleware**: ASGI middleware (`automojo.webworks.authentication.middleware.AuthenticationMiddleware`) that intercepts requests and performs authentication via the AuthenticationSystem.
- **ManagedConfigRegistry**: The configuration lifecycle manager (`automojo.webworks.configuration.lifecycle.ManagedConfigRegistry`) that loads, validates, and optionally watches configuration sources.
- **MiddlewarePipeline**: The ordered chain of middleware functions that the Dispatcher executes before invoking the matched handler.
- **Credential_Manager**: The integration point with `automojo-credentials` for loading and managing application credentials.
- **DataProfile_Manager**: The integration point with `automojo-dataprofiles` for loading and managing data profiles.
- **Lifecycle_Phase**: A discrete stage in the WebApplication startup sequence (e.g., configure, authenticate, wire, ready).

## Requirements

### Requirement 1: Web Infrastructure Ownership

**User Story:** As a web application developer, I want the WebApplication to own the Router, Dispatcher, and ASGIApplication wiring, so that I do not have to repeat the same boilerplate in every application entry point.

#### Acceptance Criteria

1. WHEN `establish_webapp_persona` completes, THE WebApplication SHALL hold a reference to a Router instance accessible via a `router` property.
2. WHEN `establish_webapp_persona` completes, THE WebApplication SHALL hold a reference to a Dispatcher instance accessible via a `dispatcher` property.
3. WHEN `establish_webapp_persona` completes, THE WebApplication SHALL hold a reference to an ASGIApplication instance accessible via a `asgi_app` property.
4. WHEN the WebApplication creates the Dispatcher, THE WebApplication SHALL configure the Dispatcher with the Router owned by the WebApplication.
5. WHEN the WebApplication creates the ASGIApplication, THE WebApplication SHALL wire the ASGIApplication HTTP handler to use the Dispatcher `dispatch_async` method.
6. THE WebApplication SHALL load all EndpointDescriptor instances from the EndpointRegistry into the Router during infrastructure setup.

### Requirement 2: Endpoint Registration API

**User Story:** As a web application developer, I want to register individual endpoint handlers through the WebApplication using an `attach_route` decorator, so that I have a single entry point for wiring handlers without touching the Router or EndpointRegistry directly.

#### Acceptance Criteria

1. THE WebApplication SHALL provide an `attach_route` decorator that accepts a path string and optional HTTP methods and returns a decorator that registers the decorated function as an EndpointDescriptor in the Router.
2. WHEN `attach_route` is used with a path that conflicts with an already-registered path and method combination, THE WebApplication SHALL raise an `EndpointConflictError`.
3. THE `attach_route` decorator SHALL preserve the original function signature and docstring on the decorated handler.

### Requirement 3: Blueprint Registration API

**User Story:** As a web application developer, I want to register RestBlueprint instances through the WebApplication using `attach_blueprint_to_route`, so that I can attach grouped endpoint collections without manually loading them into the Router.

#### Acceptance Criteria

1. THE WebApplication SHALL provide an `attach_blueprint_to_route` method that accepts a RestBlueprint class and registers all of the RestBlueprint EndpointDescriptor instances into the Router.
2. WHEN `attach_blueprint_to_route` is called with a RestBlueprint that has already been registered, THE WebApplication SHALL raise a descriptive error indicating the duplicate registration.
3. WHEN `attach_blueprint_to_route` is called, THE WebApplication SHALL preserve the RestBlueprint base path, tag merging, and version inheritance behavior defined by `RestBlueprint.attach_at`.

### Requirement 4: Configuration Management

**User Story:** As a web application developer, I want the WebApplication to manage application configuration through the ManagedConfigRegistry, so that configuration loading and validation happen automatically during startup.

#### Acceptance Criteria

1. THE WebApplication SHALL hold a reference to a ManagedConfigRegistry instance accessible via a `config` property.
2. WHEN the WebApplication initializes the ManagedConfigRegistry, THE WebApplication SHALL call `setup_from_persona` using the persona settings established by `establish_webapp_persona`.
3. WHEN configuration loading fails during startup, THE WebApplication SHALL raise a descriptive error that includes the configuration source path and the validation failure details.

### Requirement 5: Credential Management

**User Story:** As a web application developer, I want the WebApplication to integrate with automojo-credentials, so that credentials are loaded and accessible through the application lifecycle.

#### Acceptance Criteria

1. THE WebApplication SHALL hold a reference to a Credential_Manager instance accessible via a `credentials` property.
2. WHEN the WebApplication initializes the Credential_Manager, THE WebApplication SHALL use the presence directory from the persona settings to locate credential stores.
3. IF the credential store cannot be located or loaded, THEN THE WebApplication SHALL raise a descriptive error that includes the expected credential store path.

### Requirement 6: Data Profile Management

**User Story:** As a web application developer, I want the WebApplication to integrate with automojo-dataprofiles, so that data profiles are loaded and accessible through the application lifecycle.

#### Acceptance Criteria

1. THE WebApplication SHALL hold a reference to a DataProfile_Manager instance accessible via a `data_profiles` property.
2. WHEN the WebApplication initializes the DataProfile_Manager, THE WebApplication SHALL use the presence directory from the persona settings to locate data profile sources.
3. IF the data profile source cannot be located or loaded, THEN THE WebApplication SHALL raise a descriptive error that includes the expected data profile source path.

### Requirement 7: Authentication Management

**User Story:** As a web application developer, I want the WebApplication to manage the AuthenticationSystem and AuthenticationMiddleware, so that I can configure authentication providers and policies through the WebApplication rather than wiring them manually.

#### Acceptance Criteria

1. THE WebApplication SHALL hold a reference to an AuthenticationSystem instance accessible via a `auth_system` property.
2. THE WebApplication SHALL provide a `register_authenticator` method that accepts an Authenticator instance and an optional priority integer and delegates registration to the AuthenticationSystem.
3. THE WebApplication SHALL provide a `configure_auth_middleware` method that accepts exclude paths, optional paths, path policies, a default policy, and a realm string, and creates an AuthenticationMiddleware instance wired to the ASGIApplication and AuthenticationSystem.
4. WHEN `configure_auth_middleware` is called before the ASGIApplication has been created, THE WebApplication SHALL raise a descriptive error indicating that infrastructure must be initialized first.

### Requirement 8: Lifecycle Phase Ordering

**User Story:** As a web application developer, I want the WebApplication to enforce a deterministic startup sequence, so that subsystems are initialized in the correct dependency order and I receive clear errors if I attempt operations out of order.

#### Acceptance Criteria

1. THE WebApplication SHALL execute lifecycle phases in the following order: configuration loading, credential loading, data profile loading, database preparation, authentication setup, web infrastructure wiring, and readiness verification.
2. WHEN a caller invokes a lifecycle method that depends on a phase that has not yet completed, THE WebApplication SHALL raise a descriptive error naming the missing prerequisite phase.
3. THE WebApplication SHALL expose a `startup` method that executes all lifecycle phases in the defined order and returns the fully initialized WebApplication instance.
4. THE WebApplication SHALL expose a `shutdown` method that tears down subsystems in reverse lifecycle order, releasing resources held by the ManagedConfigRegistry, Credential_Manager, DataProfile_Manager, and ASGIApplication.

### Requirement 9: Extensibility via Subclassing

**User Story:** As a framework consumer, I want to override individual lifecycle phases in a WebApplication subclass, so that I can customize startup behavior without replacing the entire lifecycle.

#### Acceptance Criteria

1. THE WebApplication SHALL implement each lifecycle phase as a separate overridable method (e.g., `setup_configuration`, `setup_credentials`, `setup_data_profiles`, `setup_authentication`, `setup_infrastructure`).
2. WHEN a subclass overrides a lifecycle phase method, THE WebApplication `startup` method SHALL invoke the overridden method in place of the default implementation.
3. THE WebApplication SHALL continue to accept an `application_cls` parameter in `establish_webapp_persona` that allows instantiation of a custom subclass.
