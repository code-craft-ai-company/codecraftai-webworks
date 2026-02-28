# Requirements Document

## Introduction

This document specifies the requirements for the Blueprint Endpoints feature. This feature provides a composable system for grouping related HTTP endpoints under shared parent paths with inherited constraints. Blueprints enable developers to organize CRUD handlers, versioned APIs, and related endpoint collections as cohesive units while maintaining consistent access policies, rate limits, and metadata.

The feature supports three key patterns:
1. Blueprint as a reusable endpoint container that emits multiple attachments
2. Class-decorated endpoint methods using `attach_at` for binding handlers to URL locations
3. Endpoint functions as attachment anchors via `attach_child` for hierarchical composition

## Glossary

- **Blueprint**: An endpoint composite that emits multiple attachments in one declaration, grouping related handlers under a shared parent path.
- **Endpoint**: A base class providing a reusable container for constraints such as AccessPolicy, rate limits, and per-endpoint metadata.
- **attach_at**: A classmethod decorator that binds a handler to an absolute location in the URL tree.
- **attach_child**: A method that attaches a child endpoint relative to a parent's base path/leaf.
- **EndpointDescriptor**: A dataclass record containing handler reference plus merged metadata for routing and documentation.
- **base_path**: The URL path prefix that child endpoints inherit from their parent blueprint.
- **base_leaf**: The URL leaf segment prefix that child endpoints inherit from their parent blueprint.
- **merge_tags**: A boolean flag controlling whether child tags are merged with parent tags or replace them.
- **AccessPolicy**: A security constraint object defining roles, scopes, and authentication requirements.
- **RateLimit**: A constraint object defining request throttling parameters.
- **Router**: The interface that consumes endpoint descriptors for request routing.

## Requirements

### Requirement 1: Blueprint as Reusable Endpoint Container

**User Story:** As a developer, I want to group related endpoints under a shared parent path, so that I can manage CRUD handlers or versioned APIs as a single unit with shared constraints.

#### Acceptance Criteria

1. THE Blueprint class SHALL represent endpoint composites that emit multiple attachments in one declaration.
2. THE Blueprint class SHALL derive from Endpoint or aggregate one to inherit constraint handling capabilities.
3. THE Blueprint class SHALL call `attach_at` for each child endpoint relative to a shared parent path.
4. THE Blueprint class SHALL provide a `register(router=None)` method that returns the list of EndpointDescriptor objects it generates.
5. WHEN `router` is supplied to `register()`, THE method SHALL also call `router.add_endpoint(descriptor)` for each node.
6. WHEN `router` is not supplied to `register()`, THE method SHALL return descriptors without requiring a live router instance for testability.
7. THE Blueprint SHALL support `base_path` and `base_leaf` attributes so nested attachments automatically prefix their routes.
8. THE Blueprint SHALL ensure that every nested endpoint shares the parent's constraints (policies, rate limits) while allowing per-handler overrides.

### Requirement 2: Blueprint Constraint Inheritance

**User Story:** As a security architect, I want blueprints to enforce consistent security policies across grouped endpoints, so that nested definitions do not inadvertently weaken security.

#### Acceptance Criteria

1. WHEN parent and child define the same attribute such as tags, THE child value SHALL win unless the blueprint sets `merge_tags=True`.
2. WHEN `merge_tags=True` is set on the blueprint, THE parent tags SHALL be appended to the child tags.
3. THE security-related attributes such as `access_policy`, `scopes`, and `rate_limit` SHALL follow a "parent defaults, child overrides" strategy.
4. WHEN a child does not set a security attribute, THE child SHALL inherit the parent value.
5. WHEN a child sets a security attribute, THE child value SHALL override the parent value.
6. FOR list-like fields such as roles and scopes, THE default behavior SHALL be union (parent union child).
7. WHEN `replace_scopes=True` or `replace_roles=True` is set, THE child list SHALL fully replace the parent list.
8. WHEN multiple policies must apply (e.g., blueprint requires `hero`, handler adds `admin`), THE combined policy SHALL enforce all constraints via logical AND.
9. THE rate limits SHALL stack with the most restrictive window applying unless the child explicitly opts out via `rate_limit=None`.

### Requirement 3: Class-Decorated Endpoint Methods

**User Story:** As a developer, I want to use decorators to bind handler functions to URL locations, so that I can declaratively define endpoint routing with clear constraint inheritance.

#### Acceptance Criteria

1. THE `attach_at` method SHALL return the original function after recording the association so existing decorator stacking still works.
2. THE `attach_at` method SHALL bind an endpoint to an absolute location in the URL tree using `leaf` or `path` parameters.
3. WHEN constraints are declared on the endpoint class, THE constraints SHALL be immutable during attachment unless explicitly re-specified in the decorator call.
4. IF mandatory metadata such as `leaf` is missing, THEN THE `attach_at` method SHALL raise EndpointRegistrationError with details.
5. IF the attachment conflicts with previously registered handlers, THEN THE `attach_at` method SHALL raise EndpointRegistrationError with details about the existing registration.
6. THE `attach_at` method SHALL support parameters: `leaf`, `path`, `methods`, `version`, `tags`, `access_policy`, `rate_limit`, `request_schema`, `response_schema`, `error_map`, and `doc`.
7. WHEN additional kwargs are passed to `attach_at`, THE kwargs SHALL be stored verbatim on the descriptor so custom endpoint types can extend the contract.
8. WHEN a subclass declares class defaults such as `methods = ["GET", "POST", "DELETE"]`, THE child handler SHALL inherit those defaults but MAY narrow or expand the list via `attach_at` kwargs.
9. WHEN `attach_at` is invoked with explicit kwargs, THE explicit kwargs SHALL override class attributes.
10. WHEN `attach_at` is invoked without certain kwargs, THE missing kwargs SHALL fall back to class defaults.

### Requirement 4: Endpoint Function as Attachment Anchor

**User Story:** As a developer, I want to build hierarchical endpoint structures using parent-child relationships, so that I can compose complex URL trees declaratively from the root down.

#### Acceptance Criteria

1. THE Endpoint classes MAY declare intrinsic identity metadata as class attributes (e.g., `leaf = "portals"`, `version = "v1"`) before being bound to a parent.
2. THE parent endpoints SHALL expose `attach_child(child_endpoint, *, leaf=None, path=None, **kwargs)` that copies the child descriptor with optional placement overrides.
3. THE `attach_child` method SHALL be relative to the parent's base leaf/path.
4. WHEN a parent with `base_path="/api/v1"` calls `attach_child(..., leaf="portals")`, THE resulting path SHALL be `/api/v1/portals`.
5. THE permitted overrides for `attach_child` SHALL include: `leaf`, `path`, `methods`, `version`, `tags`, `access_policy`, `rate_limit`, and REST-specific schema/doc fields.
6. WHEN attributes are not supplied to `attach_child`, THE attributes SHALL remain as defined on the child endpoint.
7. THE application root object (e.g., App or SiteMap) SHALL expose the same `attach_child` API for building the entire tree hierarchically.
8. THE dual approach of `attach_at` for absolute placement and `attach_child` for parent-relative placement SHALL support both standalone endpoint declaration and hierarchical extension.

### Requirement 5: Declarative Descriptor Emission

**User Story:** As a framework author, I want every endpoint attachment to emit a descriptor record, so that I can collect the full endpoint map without executing handlers.

#### Acceptance Criteria

1. WHEN `Endpoint.attach_at` or a subclass variant is called, THE call SHALL emit an EndpointDescriptor record containing the handler reference plus merged metadata.
2. THE EndpointDescriptor SHALL contain typed attribute slots such as `access_policy`, `rate_limit`, `methods`, and `serializer` for uniform downstream tooling.
3. WHEN mixed decorator stacks are used, THE `attach_at` method SHALL return the original function and descriptor generation SHALL occur at decorate time.
4. THE descriptor generation SHALL be rerunnable for documentation builds without re-executing handlers.
5. THE map builder SHALL be able to filter or transform descriptors without touching handler implementations.
6. WHEN `attach_at` or `attach_child` is called, THE call SHALL push the descriptor into a module-level EndpointRegistry.
7. WHEN a package is imported, THE import SHALL register every endpoint deterministically without runtime execution of handlers.

### Requirement 6: Blueprint Registration Workflow

**User Story:** As a framework author, I want a consistent workflow for registering blueprint endpoints, so that routers can consume the endpoint map through a minimal interface.

#### Acceptance Criteria

1. THE EndpointRegistry SHALL expose `collect() -> list[EndpointDescriptor]` for routers to consume.
2. THE Router interface SHALL accept descriptors via `Router.add_endpoint(descriptor: EndpointDescriptor) -> None`.
3. WHEN two descriptors target the same path+method combination, THE EndpointRegistry SHALL raise EndpointConflictError naming both handlers.
4. WHEN `on_conflict="replace"` is passed to `attach_at`, THE caller MAY intentionally override an existing mapping without error.
5. WHEN `attach_child` is used, THE child descriptor SHALL inherit the parent's `base_path`, `base_leaf`, `version`, `tags`, and security constraints unless overridden via kwargs.
6. THE overridden values from `attach_child` SHALL apply only to that child descriptor.
7. THE Blueprint `register()` method SHALL be idempotent, returning the same descriptors on repeated calls.

</content>
</invoke>