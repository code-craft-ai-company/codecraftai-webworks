# Requirements Document

## Introduction

This document specifies the requirements for the Endpoint Abstractions feature. This feature provides a declarative, composable system for defining HTTP endpoints with centralized access control, metadata, and routing configuration. It supports both single-endpoint handlers and blueprint-style attachments, enabling a repository-wide endpoint map to be derived from code without manual duplication.

The feature enables developers to centralize access control and constraints once and reuse them across handlers, provide declarative metadata for routing and documentation generation, and build hierarchical endpoint structures through parent/child attachment patterns.

## Glossary

- **Endpoint**: A base class providing a reusable container for constraints such as AccessPolicy, rate limits, serialization hooks, and per-endpoint metadata.
- **Blueprint**: An endpoint composite that emits multiple attachments in one declaration, grouping related handlers under a shared parent path.
- **EndpointDescriptor**: A dataclass record containing handler reference plus merged metadata (bindings + class attributes) for routing and documentation.
- **EndpointRegistry**: A module-level registry that collects all endpoint descriptors from `attach_at`/`attach_child` calls.
- **AccessPolicy**: A security constraint object defining roles, scopes, and authentication requirements for an endpoint.
- **RateLimit**: A constraint object defining request throttling parameters for an endpoint.
- **RestEndpoint**: An Endpoint subclass with REST-specific metadata for auto-generating API descriptions (OpenAPI paths, verbs, payload schemas).
- **RestBlueprint**: A RestEndpoint subclass representing a collection of REST nodes sharing higher-level metadata (version, tag, auth scopes).
- **attach_at**: A classmethod decorator that binds an endpoint to an absolute location in the URL tree.
- **attach_child**: A method that attaches a child endpoint relative to a parent's base path/leaf.
- **EndpointRegistrationError**: An exception raised when mandatory metadata is missing or conflicts with previously registered handlers.
- **EndpointConflictError**: An exception raised when two descriptors target the same path+method combination.

## Requirements

### Requirement 1: Endpoint Base Class

**User Story:** As a web application developer, I want a base endpoint class with reusable constraints, so that I can define access policies, rate limits, and metadata once and apply them to multiple handlers.

#### Acceptance Criteria

1. THE Endpoint class SHALL provide a reusable container for constraints such as AccessPolicy, rate limits, serialization hooks, and per-endpoint metadata.
2. THE Endpoint class SHALL expose a classmethod `attach_at(**bindings)` that decorates a callable handler and registers it with the router using the provided bindings.
3. WHEN `attach_at` is invoked with explicit kwargs, THE explicit kwargs SHALL override class attributes.
4. WHEN `attach_at` is invoked without certain kwargs, THE missing kwargs SHALL fall back to class defaults.
5. THE Endpoint class SHALL support subclassing to bake in constraints that all handlers for that endpoint must satisfy.
6. WHEN a subclass defines class attributes such as `access_policy`, `throttle`, `serializers`, or `blueprint` metadata, THE handler decorated with `.attach_at()` SHALL inherit those constraints automatically.
7. THE Endpoint class SHALL document which attributes subclasses honor so authors know what can be overridden per attachment.

### Requirement 2: Attachment Semantics

**User Story:** As a developer, I want clear attachment semantics for binding endpoints to URL locations, so that I can predictably place handlers in the URL tree with proper constraint inheritance.

#### Acceptance Criteria

1. THE `attach_at` method SHALL return the original function after recording the association so existing decorator stacking still works.
2. THE `attach_at` method SHALL bind an endpoint to an absolute location in the URL tree using `leaf` or `path` parameters.
3. WHEN constraints are declared on the endpoint class, THE constraints SHALL be immutable during attachment unless explicitly re-specified in the decorator call.
4. IF mandatory metadata such as `leaf` is missing, THEN THE `attach_at` method SHALL raise EndpointRegistrationError with details.
5. IF the attachment conflicts with previously registered handlers, THEN THE `attach_at` method SHALL raise EndpointRegistrationError with details about the existing registration.
6. THE `attach_at` method SHALL support parameters: `leaf`, `path`, `methods`, `version`, `tags`, `access_policy`, `rate_limit`, `request_schema`, `response_schema`, `error_map`, and `doc`.
7. WHEN additional kwargs are passed to `attach_at`, THE kwargs SHALL be stored verbatim on the descriptor so custom endpoint types can extend the contract.
8. WHEN a subclass declares class defaults such as `methods = ["GET", "POST", "DELETE"]`, THE child handler SHALL inherit those defaults but MAY narrow or expand the list via `attach_at` kwargs.

### Requirement 3: Blueprints

**User Story:** As a developer, I want to group related endpoints under a shared parent path, so that I can manage CRUD handlers or versioned APIs as a single unit with shared constraints.

#### Acceptance Criteria

1. THE Blueprint class SHALL represent endpoint composites that emit multiple attachments in one declaration.
2. THE Blueprint class SHALL derive from Endpoint or aggregate one and call `attach_at` for each child endpoint relative to a shared parent path.
3. THE Blueprint class SHALL provide a `register(router=None)` method that returns the list of EndpointDescriptor objects it generates.
4. WHEN `router` is supplied to `register()`, THE method SHALL also call `router.add_endpoint(descriptor)` for each node.
5. WHEN `router` is not supplied to `register()`, THE method SHALL return descriptors without requiring a live router instance for testability.
6. THE Blueprint SHALL ensure that every nested endpoint shares the parent's constraints (policies, rate limits) while allowing per-handler overrides.
7. WHEN parent and child define the same attribute such as tags, THE child value SHALL win unless the blueprint sets `merge_tags=True`.
8. WHEN `merge_tags=True` is set, THE parent tags SHALL be appended to the child tags.

### Requirement 4: Declarative Map Semantics

**User Story:** As a framework author, I want every endpoint attachment to emit a descriptor record, so that I can collect the full endpoint map without executing handlers.

#### Acceptance Criteria

1. WHEN `Endpoint.attach_at` or a subclass variant is called, THE call SHALL emit an EndpointDescriptor record containing the handler reference plus merged metadata.
2. THE EndpointDescriptor SHALL contain typed attribute slots such as `access_policy`, `rate_limit`, `methods`, and `serializer` for uniform downstream tooling.
3. WHEN mixed decorator stacks are used, THE `attach_at` method SHALL return the original function and descriptor generation SHALL occur at decorate time.
4. THE descriptor generation SHALL be rerunnable for documentation builds without re-executing handlers.
5. THE map builder SHALL be able to filter or transform descriptors without touching handler implementations.

### Requirement 5: EndpointDescriptor

**User Story:** As a documentation generator, I want a structured descriptor for each endpoint, so that I can produce OpenAPI specs and security audits from code.

#### Acceptance Criteria

1. THE EndpointDescriptor SHALL be a dataclass with fields: `handler`, `module`, `leaf`, `path`, `methods`, `version`, `tags`, `constraints`, `doc`, and `extras`.
2. THE `constraints` field SHALL store normalized objects such as AccessPolicy and RateLimit rather than loose kwargs.
3. THE `extras` field SHALL be namespaced per endpoint type (e.g., `rest.request_schema`) to avoid collisions.
4. THE descriptor builders SHALL preserve unknown keys in `extras` for downstream consumers.

### Requirement 6: Endpoint Map Builder Workflow

**User Story:** As a framework author, I want a registry that collects all endpoint descriptors deterministically, so that routers can consume the endpoint map through a minimal interface.

#### Acceptance Criteria

1. WHEN `attach_at` or `attach_child` is called, THE call SHALL push the descriptor into a module-level EndpointRegistry.
2. WHEN a package is imported, THE import SHALL register every endpoint deterministically without runtime execution of handlers.
3. THE EndpointRegistry SHALL expose `collect() -> list[EndpointDescriptor]` for routers to consume.
4. THE Router interface SHALL accept descriptors via `Router.add_endpoint(descriptor: EndpointDescriptor) -> None`.
5. WHEN two descriptors target the same path+method combination, THE EndpointRegistry SHALL raise EndpointConflictError naming both handlers.
6. WHEN `on_conflict="replace"` is passed to `attach_at`, THE caller MAY intentionally override an existing mapping without error.
7. WHEN `attach_child` is used, THE child descriptor SHALL inherit the parent's `base_path`, `base_leaf`, `version`, `tags`, and security constraints unless overridden via kwargs.
8. THE overridden values from `attach_child` SHALL apply only to that child descriptor.

### Requirement 7: Security Composition Rules

**User Story:** As a security architect, I want predictable security inheritance rules, so that nested endpoint definitions do not inadvertently weaken security.

#### Acceptance Criteria

1. THE security-related attributes such as `access_policy`, `scopes`, and `rate_limit` SHALL follow a "parent defaults, child overrides" strategy.
2. WHEN a child does not set a security attribute, THE child SHALL inherit the parent value.
3. WHEN a child sets a security attribute, THE child value SHALL override the parent value.
4. FOR list-like fields such as roles and scopes, THE default behavior SHALL be union (parent union child).
5. WHEN `replace_scopes=True` or `replace_roles=True` is set, THE child list SHALL fully replace the parent list.
6. WHEN multiple policies must apply (e.g., blueprint requires `hero`, handler adds `admin`), THE combined policy SHALL enforce all constraints via logical AND.
7. THE combined policy SHALL ensure nested definitions do not inadvertently weaken security.
8. THE rate limits SHALL stack with the most restrictive window applying unless the child explicitly opts out via `rate_limit=None`.

### Requirement 8: RestEndpoint

**User Story:** As an API developer, I want a REST-specific endpoint class with schema and documentation metadata, so that I can auto-generate OpenAPI descriptions from my handler definitions.

#### Acceptance Criteria

1. THE RestEndpoint class SHALL inherit from Endpoint and layer on REST-specific metadata for auto-generating API descriptions.
2. THE RestEndpoint class SHALL provide helper descriptors: `methods`, `request_schema`, `response_schema`, `error_map`, and `summary/description` text.
3. WHEN `RestEndpoint.attach_at(method="GET", leaf="status")` is invoked, THE call SHALL record both routing info and documentation payload.
4. THE RestEndpoint class SHALL support mixins/helpers for CRUD conventions (`RestEndpoint.read`, `.create`, `.update`, `.delete`) that pre-populate common verbs and documentation fields.
5. THE RestEndpoint class SHALL emit structured descriptors that documentation tooling can walk to produce OpenAPI/Blueprint files.
6. THE RestEndpoint class SHALL allow blueprints to emit multiple REST endpoints while sharing versioning, tags, and authentication requirements.
7. WHEN request/response schemas are standard dataclasses or Pydantic models, THE `attach_at` decorator SHALL inspect `.model_json_schema()` or `__dataclass_fields__` to capture JSON-schema fragments.
8. THE non-REST endpoint types SHALL be able to reuse the base EndpointDescriptor with REST-specific extras living under `extras["rest"]`.

### Requirement 9: RestBlueprint

**User Story:** As an API developer, I want a REST blueprint class for grouping related REST endpoints, so that I can manage versioned API collections with shared metadata.

#### Acceptance Criteria

1. THE RestBlueprint class SHALL subclass RestEndpoint to represent a collection of REST nodes sharing higher-level metadata.
2. THE RestBlueprint class SHALL provide a `register()` hook that calls `attach_at` repeatedly to expose each child resource under the blueprint's parent path.
3. THE RestBlueprint class SHALL offer helpers like `add_crud(resource, schema)` that register standardized routes (GET list, POST create, etc.) with documentation fields.
4. THE RestBlueprint class SHALL ensure child endpoints inherit REST documentation context (tags, security schemes, version) without re-declaring them.
5. THE RestBlueprint class SHALL produce aggregated descriptors so documentation generators can emit grouped sections for the entire blueprint.
6. THE RestBlueprint class SHALL support `base_path` and `base_leaf` attributes so nested attachments automatically prefix their routes.
7. WHEN a child attachment passes `absolute=True`, THE child attachment SHALL override the prefix.
8. THE blueprint tags, security schemes, and versions SHALL cascade to children unless a child explicitly sets the attribute.
9. FOR list attributes such as tags and scopes, THE default behavior SHALL be merge; setting `replace_tags=True` SHALL cause the child list to fully replace the parent list.

### Requirement 10: Parent/Child Attachment Flow

**User Story:** As a developer, I want to build hierarchical endpoint structures, so that I can compose complex URL trees declaratively from the root down.

#### Acceptance Criteria

1. THE Endpoint classes MAY declare intrinsic identity metadata as class attributes (e.g., `leaf = "portals"`, `version = "v1"`) before being bound to a parent.
2. THE parent endpoints SHALL expose `attach_child(child_endpoint, *, leaf=None, path=None, **kwargs)` that copies the child descriptor with optional placement overrides.
3. THE `attach_child` method SHALL be relative to the parent's base leaf/path.
4. WHEN a parent with `base_path="/api/v1"` calls `attach_child(..., leaf="portals")`, THE resulting path SHALL be `/api/v1/portals`.
5. THE permitted overrides for `attach_child` SHALL include: `leaf`, `path`, `methods`, `version`, `tags`, `access_policy`, `rate_limit`, and REST-specific schema/doc fields.
6. WHEN attributes are not supplied to `attach_child`, THE attributes SHALL remain as defined on the child endpoint.
7. THE application root object (e.g., App or SiteMap) SHALL expose the same `attach_child` API for building the entire tree hierarchically.
8. THE dual approach of `attach_at` for absolute placement and `attach_child` for parent-relative placement SHALL support both standalone endpoint declaration and hierarchical extension.

### Requirement 11: Security Documentation and Auditing

**User Story:** As a security reviewer, I want to generate a web map showing each endpoint's security posture, so that I can confirm sensitive routes enforce correct roles before deployment.

#### Acceptance Criteria

1. WHEN `collect()` is called on the EndpointRegistry, THE result SHALL include consolidated metadata (path, methods, access_policy, scopes, rate_limits) for each descriptor.
2. THE system SHALL support generating a "web map" artifact (CSV/Markdown table) with columns: path, methods, handler, access_policy, scopes, rate_limit, doc.summary.
3. THE web map SHALL enable reviewers to confirm that sensitive routes (admin, hero, etc.) enforce the correct roles before deployment.
4. THE EndpointRegistry SHALL provide tooling hooks such as `export_security_map(filter_tag="admin")` for CI integration.
5. THE CI tooling SHALL be able to diff the map and block changes that weaken security without code reviewers manually tracing decorators.
