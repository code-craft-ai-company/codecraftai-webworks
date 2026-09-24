# Feature Specifications

## Web Application Persona & Presence

### `WebApplication` Root Class
- `ccai.webworks.webapplication.WebApplication` extends `ThisApplication` and adds overridable hooks (`prepare_database`, `connect_database`, `startup_database`, `ensure_database_ready`) so services can define their database bootstrap flow once and reuse it during CLI or worker startup.
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
- Mirrors `ccai.thisapp.persona.establish_app_persona` but instantiates the `WebApplication` singleton and wires it into both `ccai.thisapp.wellknown.THISAPPLICATION_SINGLETON` and `ccai.webworks.wellknown.WEBAPPLICATION_SINGLETON`.
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
- `ccai.webworks.wellknown.WebApplicationSingleton()` mirrors `ccai.thisapp.wellknown.ThisApplicationSingleton()` but surfaces the richer `WebApplication` root. Both point to the same object once `establish_webapp_persona` runs, so legacy code calling either accessor stays consistent.
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
- A nested child attaches its descendants under the prefix its parent gave it by passing the descriptor it received as `parent_placement`: `v1 = RootBlueprint.attach_child(V1Blueprint)` (`/api/v1`), then `V1Blueprint.attach_child(UsersEndpoint, parent_placement=v1)` yields `/api/v1/users` and inherits the placement's merged policies, rate limits, tags and version. Without `parent_placement`, `attach_child` stays relative to the class's own base.
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

## Access Policy (Canonical)

### `ccai.webworks.security.accesspolicy.AccessPolicy`
- The canonical immutable security constraint for an endpoint. Frozen dataclass; ``roles`` and ``scopes`` are stored as tuples regardless of the iterable type the caller supplies (lists, sets, generators are coerced in ``__post_init__``).
- ``ccai.webworks.endpoints.accesspolicy.AccessPolicy`` is now a re-export of the security-package class. The two parallel definitions that used to ship with webworks have been unified — the endpoints module retains the import path purely so existing consumers keep resolving without code changes.
- ``check(subject)`` is polymorphic and accepts any of three subject shapes:
  - :class:`ccai.webworks.security.securitycontext.SecurityContext` — flat immutable context with ``user_id`` / ``roles`` / ``scopes``.
  - :class:`ccai.webworks.authentication.core.AuthenticationContext` — wraps a :class:`Principal`. Scopes are evaluated against ``principal.permissions`` since :class:`Principal` carries scope-equivalent grants under that name.
  - Any duck-typed *User* with ``is_authenticated`` / ``roles`` / ``scopes`` attributes — used by tooling and tests that don't construct full security contexts.
- Discrimination is performed by attribute presence at call time (``hasattr(subject, 'principal')`` → AuthenticationContext, ``hasattr(subject, 'user_id')`` → SecurityContext, otherwise User). Adding a new subject shape is a matter of routing inside ``check`` — no consumer changes required.
- Named convenience methods preserved from the legacy endpoints implementation: ``check_authentication_context(ctx)``, ``check_roles(ctx)``, ``check_permissions(ctx)``. ``get_denial_reason(subject)`` is similarly polymorphic.
- ``merge_with(other, replace_roles=False, replace_scopes=False)`` returns a new ``AccessPolicy`` combining constraints. Roles and scopes default to deduplicated union; ``require_auth`` is the logical OR; the custom ``constraints`` dict is shallow-merged with ``other`` precedence.
- :class:`ccai.webworks.endpoints.constraints.EndpointConstraints` retains its list-typed ``roles`` and ``scopes`` fields. Its ``__post_init__`` coerces incoming iterables (commonly tuples handed off from an ``AccessPolicy``) to lists so consumer code continues to receive the list shape it has always seen.

### Decorator wire-through (`Endpoint.attach_at` / `RestEndpoint.attach_at`)
- Security decorators (``@require_auth``, ``@require_roles``, ``@require_scopes``, ``@public_endpoint``) attach an :class:`AccessPolicy` to the handler function under the ``_access_policy`` attribute. When the function is then registered via :meth:`Endpoint.attach_at` (or any subclass that inherits this behavior — :class:`RestEndpoint`, :class:`Blueprint`, :class:`RestBlueprint`), the registration logic reads ``_access_policy`` and merges it into the descriptor's effective policy alongside any explicit ``access_policy=`` kwarg and the class-level default.
- Merge order: ``cls.access_policy`` (class default) → explicit ``access_policy=`` kwarg → handler-attached ``_access_policy``. Each step uses :meth:`AccessPolicy.merge_with`, so roles and scopes accumulate as a deduplicated union; ``require_auth`` is the logical OR.

```python
class DashboardBlueprint(RestBlueprint):
    base_path = "/dashboard"

@DashboardBlueprint.attach_at(path="/internal", methods=["GET"])
@require_roles("authenticated-user", "system-admin")
def internal_dashboard(request):
    ...
```

The handler's effective policy is ``AccessPolicy(roles=("authenticated-user", "system-admin"), require_auth=True)`` and the :class:`SecurityMiddleware` / :class:`AuthenticationMiddleware` reads it from the descriptor.
## Flash Messaging

### `ccai.webworks.flash`
- Provides one-shot user-feedback messaging modeled after the classic Flask `flash()` / `get_flashed_messages()` API: a handler emits a message before redirecting, and the next render consumes it.
- Three composable pieces: `FlashStore` (abstract backend), `InMemoryFlashStore` (process-local default), `FlashManager` (input-validating facade), and `make_flash_context_processor` (templating integration via `ContextProcessorRegistry`).
- Each message is a `(category, message)` tuple. Category is a free-form string the rendering layer can key on for styling — `info`, `success`, `warning`, `error` are the conventional values, but any string is accepted.
- The default `consume=True` mode drains the store on read so subsequent renders do not duplicate messages. A `consume=False` peek mode is provided for admin tooling and tests.
- The store is intentionally session-coupled but storage-independent: implementations of `FlashStore` may share state across workers via Redis or any other backend without changing handler call sites.

```python
from ccai.webworks.flash import FlashManager, make_flash_context_processor

flash_manager = FlashManager()  # uses InMemoryFlashStore by default

# Inside a postback handler:
flash_manager.add(session_id=current_session_id, message="Saved.", category="success")

# Wire flash_messages into every template render:
context_processors.register(make_flash_context_processor(flash_manager))
```

- Validation: `FlashManager.add` requires both `session_id` and `message` to be non-empty strings and raises `FlashError` otherwise. `consume_all` and `peek_all` are lenient on read paths and return `[]` for missing or empty session ids.
## Authentication Blueprints

### `SessionAuthBlueprint.establish_session`
- The credential `login` endpoint is split into two halves: credential validation (delegated to `IdentityProvider.validate_credentials`) and session materialization (cookie + store + response).
- The materialization half is exposed as a public classmethod `establish_session(principal, *, request=None, remember_me=False, scheme="Session", success_message="Session established", extra_attributes=None)` so sibling auth blueprints can reuse it without re-implementing cookie generation, store wiring, or the `post_authenticate` hook.
- Intended consumers include the magic-link redemption blueprint, OAuth client callback handlers, and SSO assertion handlers — flows where the principal is established through a channel other than username/password and still needs an HTTP session cookie issued.
- The `scheme` parameter is recorded on the resulting `AuthenticationContext` so downstream subscribers can distinguish channels (`"Session"` for credential login, `"MagicLink"` for one-time tokens, `"OAuth"` for IdP callbacks, etc.). The `extra_attributes` mapping is merged into `AuthenticationContext.attributes` for channel-specific metadata such as the consumed token id or the issuing IdP.
- The credential `login` endpoint preserves its historical wire contract (`message="Login successful"`) by passing `success_message="Login successful"` to `establish_session`. New callers default to `"Session established"`.

```python
# Inside a magic-link redemption handler that has just consumed a one-time token:
response = SiteSessionAuth.establish_session(
    principal=Principal(identifier=user.id, display_name=user.display_name, roles={user.role}),
    scheme="MagicLink",
    extra_attributes={"token_id": consumed_token.id},
    success_message="Welcome — your link has been redeemed",
)
```

## CSRF Protection

### `ccai.webworks.security.csrf`
- Provides synchronizer-token style CSRF protection backed by an HMAC-SHA256 over the session identifier with a server-side secret key. Tokens are deterministically reproducible from the session id alone, so neither the manager nor the application persists per-request token state.
- The module ships three pieces that compose: `CSRFTokenManager` for the cryptographic primitives, `CSRFMiddleware` for ASGI enforcement on unsafe HTTP methods, and `make_csrf_context_processor` for templating integration via the existing `ContextProcessorRegistry`.
- Token transport defaults to the `X-CSRF-Token` header. Subclasses of `CSRFMiddleware` may override `_extract_form_token(scope, receive)` to read the token from `application/x-www-form-urlencoded` request bodies. Body parsing is intentionally not done in the base middleware so applications can choose their own body buffering / replay strategy.
- Threat-model notes: this layer assumes cookie-bound sessions, an in-confidence secret key, and HTTPS in production. It complements `SameSite` cookie attributes and `Origin` checks rather than replacing them.

```python
from ccai.webworks.security.csrf import (
    CSRFMiddleware,
    CSRFTokenManager,
    cookie_session_id_resolver,
    make_csrf_context_processor,
)

token_manager = CSRFTokenManager(secret_key=settings.csrf_secret)

# Wire the ASGI middleware in front of the application stack.
app = CSRFMiddleware(
    app=app,
    token_manager=token_manager,
    session_id_resolver=cookie_session_id_resolver(cookie_name="session_id"),
    exempt_paths={"/webhooks/stripe"},
)

# Make {{ csrf_token }} available in every render that carries
# session_id in the rendering context.
context_processors.register(make_csrf_context_processor(token_manager))
```

- Validation results: `csrf_missing_session` when the resolver returns no session, `csrf_token_missing` when the token is absent, `csrf_token_invalid` when it does not match. All three short-circuit with HTTP 403.
- The context processor returns an empty mapping when the rendering context has no `session_id`, so anonymous renders succeed without a token. Forms protected by CSRF must therefore only be rendered for authenticated users (or use a separate anti-CSRF mechanism such as captcha for purely public submissions).
