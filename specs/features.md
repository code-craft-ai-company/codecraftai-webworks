# Feature Specifications

## Web Application Persona & Presence

### `WebApplication` Root Class
- `automojo.webworks.webapplication.WebApplication` extends `ThisApplication` and adds overridable hooks (`prepare_database`, `connect_database`, `startup_database`, `ensure_database_ready`) so services can define their database bootstrap flow once and reuse it during CLI or worker startup.
- Project-level apps subclass `WebApplication` to add helpers (ORM models, DI containers, etc.) while still inheriting the presence/variable stack from `ThisApplication`.
- Example:

```python
class PortalWebApp(WebApplication):
    def prepare_database(self):
        run_migrations(self.settings_file)

    def connect_database(self):
        self.context_insert("/db/session", build_session_pool())
```

### `establish_webapp_persona`
- Mirrors `automojo.thisapp.persona.establish_app_persona` but instantiates the `WebApplication` singleton and wires it into both `automojo.thisapp.wellknown.THISAPPLICATION_SINGLETON` and `automojo.webworks.wellknown.WEBAPPLICATION_SINGLETON`.
- Accepts the familiar persona fields (`name`, `logger_name`, `log_basename`, `presence_dir`, `log_directory`, `settings_file`, `extensions`, `service_name`) plus an optional `application_cls` so callers can swap in custom subclasses.
- Computes defaults identical to `AppPersona`: if no presence is supplied the folder defaults to `~/<appname>`, log directory defaults to `<presence>/logs`, and `settings.config` lives under the presence directory unless an absolute/expanded path is passed.
- After instantiation the helper overrides the `PersonaVariablesDesc` values so every `AppVarAccessor` returns the resolved persona metadata immediately.

### Presence Directory & Configuration Layout
- `AppPersona` captures the canonical paths (`AM_PRESENCE_DIR`, `AM_LOG_DIRECTORY`, `AM_SETTINGS_FILENAME`, etc.), giving the runtime a well-defined location to create config, log, and data folders even before the router starts.
- Presence information flows into `ContextPaths` (`/environment/presence/*`) so other subsystems (logging, pipelines, results) can discover directories without knowing how they were derived.
- The persona makes it trivial to share settings: storing `settings.config` in the presence directory allows the `ConfigParser` inside `ThisApplication`/`WebApplication` to hydrate defaults, while overrides can still come from environment variables or direct calls to `override_variable_value`.

### Variable Descriptions & Accessors
- Variable declarations live in `AppVarDesc` instances (grouped via `AppVarSet` subclasses like `PersonaVariablesDesc`). Each descriptor encodes its lookup order via `VariableSource` bits (environment vs. settings vs. defaults) and optional `ContextPaths` integration so values can be mirrored into the contextual tree.
- `AppVarAccessor` is a descriptor that resolves variable values lazily from the global singleton (`ThisApplicationSingleton` or `WebApplicationSingleton`). Accessors enforce read-only semantics to ensure overrides happen centrally on the application object.
- Combined with the persona overrides, this gives a single source of truth for configuration—documentation generators can list every `AppVarDesc`, and runtime code simply references `PersonaVariables.AM_PRESENCE_DIR()` to stay in sync with the persona.

### Wellknown Singletons
- `automojo.webworks.wellknown.WebApplicationSingleton()` mirrors `automojo.thisapp.wellknown.ThisApplicationSingleton()` but surfaces the richer `WebApplication` root. Both point to the same object once `establish_webapp_persona` runs, so legacy code calling either accessor stays consistent.
- The singleton lock from `thisapp.wellknown` is reused to guard initialization, preventing multiple personas from being established accidentally.

## Endpoint Abstractions

### Goals
- centralize access control and other constraints once and reuse them across handlers
- provide declarative metadata that can be inspected during routing or documentation generation
- support both single-endpoint handlers and blueprint-style attachments
- enable a repository-wide endpoint map to be derived from code without manual duplication

### `Endpoint` Base Class
- Provides a reusable container for constraints such as `AccessPolicy`, rate limits, serialization hooks, or per-endpoint metadata.
- Exposes a classmethod `attach_at(**bindings)` that decorates a callable handler and registers it with the router using the provided bindings (`leaf`, `path`, `method`, `version`, `tags`, etc.). Explicit kwargs always override class attributes; missing kwargs fall back to class defaults.
- Can be subclassed to bake in constraints that all handlers for that endpoint must satisfy. Subclasses should document which attributes they honor so authors know what can be overridden per attachment.

```python
Endpoint.attach_at(leaf="status")
def handler_status():
    return {"ok": True}
```

### Custom Endpoint Example
- Subclass `Endpoint` to declare shared constraints.
- Subclasses may define class attributes such as `access_policy`, `throttle`, `serializers`, or `blueprint` metadata.
- When `.attach_at()` is invoked, the handler inherits the subclass constraints automatically before being registered.

```python
class MyEndpoint(Endpoint):
    access_policy = AccessPolicy(roles=["hero"])

@MyEndpoint.attach_at(leaf="portal")
def secure_handler_something(user):
    return {"user": user.id}
```

### Attachment Semantics
- `attach_at` returns the original function after recording the association so existing decorator stacking still works.
- `attach_at` is used to bind an endpoint to an absolute location in the URL tree (`leaf="status"` under the global root or `path="/api/v1/status"`). It is best suited for top-level placement where the parent is implicit (e.g., a global router).
- Constraints declared on the endpoint class are immutable during attachment unless explicitly re-specified in the decorator call (e.g., `@MyEndpoint.attach_at(access_policy=...)`), making overrides an opt-in decision.
- Attachment should fail fast if mandatory metadata (e.g., `leaf`) is missing or conflicts with previously registered handlers. The helper raises `EndpointRegistrationError` with details about the existing registration.
- Supported parameters: `leaf`, `path`, `methods`, `version`, `tags`, `access_policy`, `rate_limit`, `request_schema`, `response_schema`, `error_map`, and `doc`. Additional kwargs are stored verbatim on the descriptor so custom endpoint types can extend the contract without modifying the base class.
- Class defaults act as archetypes but are always overridable per handler. Example: a `RestCollectionEndpoint` subclass can declare `methods = ["GET", "POST", "DELETE"]` so every child handler inherits collection semantics, yet authors may narrow or expand the list by passing `@RestCollectionEndpoint.attach_at(methods=["GET"])` on a specific handler.

### Blueprints
- Blueprints represent endpoint composites that emit multiple attachments in one declaration.
- A blueprint derives from `Endpoint` (or aggregates one) and calls `attach_at` for each child endpoint relative to a shared parent path.
- Use cases include grouping CRUD handlers or versioned APIs under a single namespace.
- The blueprint `register(router=None)` method returns the list of `EndpointDescriptor` objects it generates; when `router` is supplied the helper also calls `router.add_endpoint(descriptor)` for each node. This dual mode keeps blueprints testable without a live router instance.

```python
class CrudBlueprint(Endpoint):
    base_leaf = "items"

    @classmethod
    def register(cls):
        cls.attach_at(leaf=f"{cls.base_leaf}/list")(list_items)
        cls.attach_at(leaf=f"{cls.base_leaf}/create")(create_item)
```

- Blueprints ensure that every nested endpoint shares the parent's constraints (policies, rate limits, etc.) while still allowing per-handler overrides passed to each `attach_at` invocation.
- When parent and child define the same attribute (e.g., tags), the child value wins unless the blueprint sets `merge_tags=True`, in which case parent tags are appended. This keeps inheritance rules predictable.

### Declarative Map Semantics
- Every call to `Endpoint.attach_at` (or a subclass variant) emits an `EndpointDescriptor` record containing the handler reference plus merged metadata (bindings + class attributes). Collecting these descriptors results in the full endpoint map without executing the handlers.
- Subclasses provide typed attribute slots (e.g., `access_policy`, `rate_limit`, `methods`, `serializer`) so downstream tooling can reason about constraints in a uniform way, irrespective of which handler defined them.
- Mixed decorator stacks are respected because `attach_at` returns the original function; descriptor generation occurs at decorate time and can be rerun for documentation builds.
- Blueprints simply loop over multiple `.attach_at` invocations, so the same descriptor pipeline applies—blueprints become declarative bundles rather than imperative registration code.
- The map builder can filter or transform descriptors (e.g., grouping by `leaf`, generating OpenAPI paths) without touching handler implementations, enabling repeatable doc/graph exports.

#### `EndpointDescriptor`
- Shape: dataclass with `handler`, `module`, `leaf`, `path`, `methods`, `version`, `tags`, `constraints` (dict of access policy/rate limits/etc.), `doc` (summary + description), and `extras` (arbitrary kwargs captured during attachment).
- `constraints` stores normalized objects (e.g., `AccessPolicy`, `RateLimit`) rather than loose kwargs so policy engines can introspect without parsing strings.
- `extras` is namespaced per endpoint type (e.g., `rest.request_schema`) to avoid collisions; descriptor builders should preserve unknown keys for downstream consumers.

### Endpoint Map Builder Workflow
- All `attach_at`/`attach_child` calls push their descriptors into a module-level `EndpointRegistry`. Importing a package registers every endpoint deterministically; no runtime execution of handlers is required.
- The registry exposes `collect() -> list[EndpointDescriptor]`. Routers consume that list via a minimal interface (`Router.add_endpoint(descriptor: EndpointDescriptor) -> None`), making the contract explicit for framework authors.
- Conflict policy: when two descriptors target the same path+method combination, `EndpointRegistry` raises `EndpointConflictError` naming both handlers. Callers may pass `on_conflict="replace"` to `attach_at` if they intentionally override an existing mapping.
- Merging rules for parent-relative attachments: `attach_child` inherits the parent’s `base_path`, `base_leaf`, `version`, `tags`, and security constraints unless overridden via keyword arguments. Overridden values apply only to that child descriptor.
- Because descriptors are plain dataclasses, higher-level tooling (OpenAPI generation, sitemap export, etc.) just iterates `collect()` and renders the relevant fields.

### Security Composition Rules
- Security-related attributes (e.g., `access_policy`, `scopes`, `rate_limit`) follow a “parent defaults, child overrides” strategy: the child inherits the parent value unless it sets the same attribute.
- For list-like fields (roles/scopes), the default behavior is union (parent union child). Set `replace_scopes=True` or `replace_roles=True` to force replacement.
- When multiple policies must apply (e.g., blueprint requires `hero`, handler adds `admin`), the combined policy enforces all constraints (logical AND), ensuring nested definitions do not inadvertently weaken security.
- Rate limits stack similarly: the most restrictive window applies unless the child explicitly opts out via `rate_limit=None`.

### `RestEndpoint`
- Inherits from `Endpoint` and layers on REST-specific metadata needed to auto-generate API descriptions (e.g., OpenAPI paths, verbs, payload schemas).
- Provides helper descriptors such as `methods`, `request_schema`, `response_schema`, `error_map`, and `summary/description` text.
- When `RestEndpoint.attach_at(method="GET", leaf="status")` is invoked, it records both the routing info and the documentation payload for downstream doc builders.
- Supports mixins/helpers for CRUD conventions (`RestEndpoint.read`, `.create`, `.update`, `.delete`) that pre-populate common verbs and documentation fields.
- Emits structured descriptors (dicts or dataclasses) that documentation tooling can walk to produce OpenAPI/Blueprint files without re-crawling code.
- Allows blueprints to emit multiple REST endpoints at once while sharing versioning, tags, and authentication requirements.
- Request/response schemas are standard dataclasses or Pydantic models. The `attach_at` decorator inspects `.model_json_schema()`/`__dataclass_fields__` to capture JSON-schema fragments. Example:

```python
class PortalRequest(BaseModel):
    destination: str

class PortalResponse(BaseModel):
    portal_id: str

@RestEndpoint.attach_at(
    leaf="portals",
    path="/api/portals",
    methods=["POST"],
    request_schema=PortalRequest,
    response_schema=PortalResponse,
    doc=Doc(summary="Create a portal")
)
def create_portal(payload: PortalRequest) -> PortalResponse:
    ...
```

Class-level REST archetypes build on this override model. For example:

```python
class RestCollectionEndpoint(RestEndpoint):
    methods = ["GET", "POST", "DELETE"]
    leaf = "items"

class HeroCollection(RestCollectionEndpoint):
    access_policy = AccessPolicy(roles=["hero"])

@HeroCollection.attach_at(methods=["GET"])  # narrows to read-only
def list_heroes(): ...

@HeroCollection.attach_at(methods=["POST"])
def create_hero(): ...
```

The defaults make it easy to replicate collection behavior, while per-attachment overrides keep unique handlers flexible.

- Non-REST endpoint types can still reuse the base `EndpointDescriptor`. REST-specific extras live under `extras["rest"]`, so RPC, GraphQL, or websocket endpoint types simply ignore those keys and provide their own namespaced metadata without impacting the shared contract.

### `RestBlueprint`
- Subclasses `RestEndpoint` to represent a collection of REST nodes that share higher-level metadata (version, tag, auth scopes).
- Provides a `register()` (or similar) hook that calls `attach_at` repeatedly to expose each child resource under the blueprint’s parent path.
- Can offer helpers like `add_crud(resource, schema)` that register standardized routes (`GET list`, `POST create`, etc.) while filling documentation fields.
- Ensures child endpoints inherit REST documentation context (e.g., tags, security schemes, version) without re-declaring them.
- Produces aggregated descriptors so documentation generators can emit grouped sections for the entire blueprint (e.g., `/users/*` endpoints).
- Supports `base_path`/`base_leaf` attributes so nested attachments automatically prefix their routes (e.g., `base_path="/api/v1/users"`). Child attachments may override the prefix by passing `absolute=True`.
- Inheritance rules: blueprint tags, security schemes, and versions cascade to children unless a child explicitly sets the attribute. For lists (tags/scopes) the default behavior is merge; setting `replace_tags=True` causes the child list to fully replace the parent list.

### Parent/Child Attachment Flow
- Endpoints may declare intrinsic identity metadata as class attributes (e.g., `leaf = "portals"`, `version = "v1"`) similar to ORM models. These attributes exist even before the endpoint is bound to a parent.
- Parents expose `attach_child(child_endpoint, *, leaf=None, path=None, **kwargs)` that copies the child descriptor, optionally overriding placement attributes (`leaf`, `path`) at the moment of attachment. `attach_child` is always relative to the parent’s base leaf/path (e.g., `PortalBlueprint` with `base_path="/api/v1"` plus `attach_child(..., leaf="portals")` yields `/api/v1/portals`).
- Permitted overrides include `leaf`, `path`, `methods`, `version`, `tags`, `access_policy`, `rate_limit`, and REST-specific schema/doc fields. Attributes not supplied remain as defined on the child endpoint, preserving its self-contained metadata.
- The application root object (e.g., `App` or `SiteMap`) exposes the same `attach_child` API so you can build the entire tree hierarchically: instantiate the root, attach top-level blueprints/endpoints, then let each child attach its own descendants. This keeps the whole site map declarative and consistent from the root down.
- Example workflow:

```python
class PortalEndpoint(RestEndpoint):
    leaf = "portals"

class PortalBlueprint(RestBlueprint):
    base_leaf = "magic"

portal_bp = PortalBlueprint()
portal_bp.attach_child(PortalEndpoint, leaf="magic/portals")
```

- This dual approach—`attach_at` for absolute placement vs. `attach_child` for parent-relative placement—supports both “standalone endpoint declaration” and “hierarchical extension,” making complex maps manageable without repeating definitions.

### Security Documentation & Auditing
- Because every descriptor includes consolidated metadata (path, methods, access_policy, scopes, rate limits), generating a “web map” for review is trivial: `collect()` → render table/JSON describing each endpoint’s security posture.
- Suggested artifact: CSV/Markdown table with columns `[path, methods, handler, access_policy, scopes, rate_limit, doc.summary]`. This enables reviewers to confirm that sensitive routes (admin, hero, etc.) enforce the correct roles before deployment.
- Provide tooling hooks (e.g., `EndpointRegistry.export_security_map(filter_tag="admin")`) so CI can diff the map and block changes that weaken security without code reviewers manually tracing decorators.
