# Design Document: Access Policy and Security

## Overview

This design document describes the architecture and implementation approach for the Access Policy and Security feature. The feature provides a comprehensive security framework for web applications, including access control policies, authentication providers, authorization engines, and audit logging.

The design follows a layered architecture where `AccessPolicy` serves as the core constraint object, `Authentication_Provider` handles identity verification, `Authorization_Engine` makes access decisions, and `Audit_Logger` records security events. The system implements a default-deny model where all endpoints require explicit authorization.

Key design principles:
- Default-deny: Access is denied unless explicitly permitted
- Composition over replacement: Security constraints combine via logical AND
- Declarative security: Policies are defined at decoration time, not runtime
- Auditability: All security decisions are logged for compliance and forensics
- Extensibility: Custom providers, rules, and constraints can be plugged in

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Security Layer Architecture                          │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         Request Flow                                 │    │
│  │                                                                      │    │
│  │  Request → Authentication → Authorization → Handler → Response      │    │
│  │              │                  │                                    │    │
│  │              ▼                  ▼                                    │    │
│  │       Security_Context    AccessPolicy                              │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Authentication Layer                              │    │
│  │                                                                      │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │    │
│  │  │ JWT Provider│  │Session Prov │  │API Key Prov │  ...             │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                  │    │
│  │         │                │                │                          │    │
│  │         └────────────────┼────────────────┘                          │    │
│  │                          ▼                                           │    │
│  │              ┌─────────────────────┐                                 │    │
│  │              │  Security_Context   │                                 │    │
│  │              │  - user_id          │                                 │    │
│  │              │  - roles            │                                 │    │
│  │              │  - scopes           │                                 │    │
│  │              └─────────────────────┘                                 │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Authorization Layer                               │    │
│  │                                                                      │    │
│  │  ┌─────────────────────┐      ┌─────────────────────┐               │    │
│  │  │   AccessPolicy      │      │ Authorization_Engine │               │    │
│  │  │   - roles           │ ───▶ │ - evaluate()         │               │    │
│  │  │   - scopes          │      │ - check_roles()      │               │    │
│  │  │   - require_auth    │      │ - check_scopes()     │               │    │
│  │  └─────────────────────┘      └─────────────────────┘               │    │
│  │                                        │                             │    │
│  │                                        ▼                             │    │
│  │                          ┌─────────────────────┐                     │    │
│  │                          │ AuthorizationResult │                     │    │
│  │                          │ - allowed: bool     │                     │    │
│  │                          │ - reason: str       │                     │    │
│  │                          └─────────────────────┘                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      Audit Layer                                     │    │
│  │                                                                      │    │
│  │  ┌─────────────────────┐      ┌─────────────────────┐               │    │
│  │  │   Audit_Logger      │      │   Audit_Entry       │               │    │
│  │  │   - log_auth()      │ ───▶ │   - timestamp       │               │    │
│  │  │   - log_authz()     │      │   - event_type      │               │    │
│  │  │   - log_violation() │      │   - user_id         │               │    │
│  │  └─────────────────────┘      │   - outcome         │               │    │
│  │           │                   └─────────────────────┘               │    │
│  │           ▼                                                          │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │    │
│  │  │ File Dest   │  │  DB Dest    │  │External Dest│                  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                    Policy Inheritance Flow                                   │
│                                                                              │
│  Parent Endpoint                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  access_policy = AccessPolicy(roles=["user"], scopes=["read"])      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│         │                                                                    │
│         │ attach_child(child, roles=["admin"])                              │
│         ▼                                                                    │
│  Child Endpoint (merged policy)                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  access_policy = AccessPolicy(                                       │    │
│  │      roles=["user", "admin"],  # union (default)                    │    │
│  │      scopes=["read"]           # inherited                          │    │
│  │  )                                                                   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  With replace_roles=True:                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  access_policy = AccessPolicy(                                       │    │
│  │      roles=["admin"],          # replaced                           │    │
│  │      scopes=["read"]           # inherited                          │    │
│  │  )                                                                   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### AccessPolicy Class

```python
@dataclass(frozen=True)
class AccessPolicy:
    """
    Security constraint defining roles, scopes, and authentication
    requirements for an endpoint. Immutable after creation.
    """
    
    roles: Tuple[str, ...] = field(default_factory=tuple)
    scopes: Tuple[str, ...] = field(default_factory=tuple)
    require_auth: bool = True
    constraints: Dict[str, Any] = field(default_factory=dict)
    
    def merge_with(
        self,
        other: "AccessPolicy",
        replace_roles: bool = False,
        replace_scopes: bool = False
    ) -> "AccessPolicy":
        """
        Merge this policy with another, combining constraints.
        
        The merged policy enforces all constraints (logical AND).
        
        Args:
            other: Policy to merge with.
            replace_roles: If True, other.roles replaces self.roles.
            replace_scopes: If True, other.scopes replaces self.scopes.
        
        Returns:
            New AccessPolicy with combined constraints.
        """
        pass
    
    def check(self, context: "Security_Context") -> bool:
        """
        Check if a security context satisfies this policy.
        
        Args:
            context: Security context to check against policy.
        
        Returns:
            True if context satisfies all constraints.
        """
        pass
    
    def get_denial_reason(self, context: "Security_Context") -> Optional[str]:
        """
        Get the reason why a context fails this policy.
        
        Args:
            context: Security context that failed the check.
        
        Returns:
            Human-readable denial reason, or None if check passes.
        """
        pass
```

### Security_Context Class

```python
@dataclass(frozen=True)
class Security_Context:
    """
    Immutable security context containing authenticated user information.
    """
    
    user_id: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None
    roles: Tuple[str, ...] = field(default_factory=tuple)
    scopes: Tuple[str, ...] = field(default_factory=tuple)
    provider: Optional[str] = None
    authenticated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    extra: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_authenticated(self) -> bool:
        """Return True if this context represents an authenticated user."""
        return self.user_id is not None
    
    @property
    def is_expired(self) -> bool:
        """Return True if this context has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    def has_role(self, role: str) -> bool:
        """Check if context has a specific role."""
        return role in self.roles
    
    def has_scope(self, scope: str) -> bool:
        """Check if context has a specific scope."""
        return scope in self.scopes
    
    def has_any_role(self, *roles: str) -> bool:
        """Check if context has any of the specified roles."""
        return any(role in self.roles for role in roles)
    
    def has_all_scopes(self, *scopes: str) -> bool:
        """Check if context has all of the specified scopes."""
        return all(scope in self.scopes for scope in scopes)
    
    @classmethod
    def guest(cls) -> "Security_Context":
        """Return a guest context with no authentication."""
        return cls()
```

### Authentication_Provider Protocol

```python
class Authentication_Provider(Protocol):
    """
    Protocol for authentication providers that verify user identity.
    """
    
    @property
    def name(self) -> str:
        """Return the provider name for logging."""
        ...
    
    @property
    def priority(self) -> int:
        """Return priority (lower = higher priority)."""
        ...
    
    def authenticate(self, request: "Request") -> Optional[Security_Context]:
        """
        Attempt to authenticate a request.
        
        Args:
            request: The incoming request to authenticate.
        
        Returns:
            Security_Context if authentication succeeds, None otherwise.
        """
        ...
    
    async def authenticate_async(
        self, request: "Request"
    ) -> Optional[Security_Context]:
        """
        Async version of authenticate for non-blocking I/O.
        
        Args:
            request: The incoming request to authenticate.
        
        Returns:
            Security_Context if authentication succeeds, None otherwise.
        """
        ...
```

### Built-in Authentication Providers

```python
class JWTAuthProvider:
    """
    Authentication provider for JWT bearer tokens.
    """
    
    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        header_name: str = "Authorization",
        header_prefix: str = "Bearer",
        priority: int = 10
    ):
        pass
    
    def authenticate(self, request: "Request") -> Optional[Security_Context]:
        """Extract and validate JWT from Authorization header."""
        pass


class SessionAuthProvider:
    """
    Authentication provider for session cookies.
    """
    
    def __init__(
        self,
        session_store: "SessionStore",
        cookie_name: str = "session_id",
        priority: int = 20
    ):
        pass
    
    def authenticate(self, request: "Request") -> Optional[Security_Context]:
        """Extract and validate session from cookie."""
        pass


class APIKeyAuthProvider:
    """
    Authentication provider for API keys.
    """
    
    def __init__(
        self,
        key_store: "APIKeyStore",
        header_name: str = "X-API-Key",
        query_param: Optional[str] = "api_key",
        priority: int = 30
    ):
        pass
    
    def authenticate(self, request: "Request") -> Optional[Security_Context]:
        """Extract and validate API key from header or query param."""
        pass
```

### Authentication_Manager Class

```python
class Authentication_Manager:
    """
    Manages multiple authentication providers and coordinates
    the authentication process.
    """
    
    def __init__(self):
        self._providers: List[Authentication_Provider] = []
    
    def register_provider(self, provider: Authentication_Provider) -> None:
        """
        Register an authentication provider.
        
        Providers are sorted by priority after registration.
        """
        pass
    
    def authenticate(self, request: "Request") -> Security_Context:
        """
        Attempt authentication using all registered providers.
        
        Tries each provider in priority order until one succeeds.
        Returns guest context if all providers fail.
        
        Args:
            request: The incoming request to authenticate.
        
        Returns:
            Security_Context (authenticated or guest).
        """
        pass
    
    async def authenticate_async(self, request: "Request") -> Security_Context:
        """Async version of authenticate."""
        pass
```

### Authorization_Engine Class

```python
@dataclass
class AuthorizationResult:
    """Result of an authorization decision."""
    
    allowed: bool
    reason: Optional[str] = None
    policy: Optional[AccessPolicy] = None
    context: Optional[Security_Context] = None


class Authorization_Engine:
    """
    Evaluates access policies against security contexts to make
    authorization decisions.
    """
    
    def __init__(
        self,
        default_policy: Optional[AccessPolicy] = None,
        custom_rules: Optional[List["AuthorizationRule"]] = None
    ):
        self._default_policy = default_policy or AccessPolicy()
        self._custom_rules = custom_rules or []
        self._pre_hooks: List[Callable] = []
        self._post_hooks: List[Callable] = []
    
    def evaluate(
        self,
        policy: AccessPolicy,
        context: Security_Context
    ) -> AuthorizationResult:
        """
        Evaluate a policy against a security context.
        
        Args:
            policy: The access policy to evaluate.
            context: The security context to check.
        
        Returns:
            AuthorizationResult with decision and reason.
        """
        pass
    
    def check_roles(
        self,
        required_roles: Tuple[str, ...],
        context: Security_Context
    ) -> bool:
        """
        Check if context has any of the required roles (OR logic).
        
        Args:
            required_roles: Roles to check for.
            context: Security context to check.
        
        Returns:
            True if context has at least one required role.
        """
        pass
    
    def check_scopes(
        self,
        required_scopes: Tuple[str, ...],
        context: Security_Context
    ) -> bool:
        """
        Check if context has all required scopes (AND logic).
        
        Args:
            required_scopes: Scopes to check for.
            context: Security context to check.
        
        Returns:
            True if context has all required scopes.
        """
        pass
    
    def add_pre_hook(self, hook: Callable) -> None:
        """Add a pre-authorization hook."""
        pass
    
    def add_post_hook(self, hook: Callable) -> None:
        """Add a post-authorization hook."""
        pass
    
    def add_custom_rule(self, rule: "AuthorizationRule") -> None:
        """Add a custom authorization rule."""
        pass
```

### AuthorizationRule Protocol

```python
class AuthorizationRule(Protocol):
    """Protocol for custom authorization rules."""
    
    def evaluate(
        self,
        policy: AccessPolicy,
        context: Security_Context,
        request: "Request"
    ) -> Optional[AuthorizationResult]:
        """
        Evaluate custom rule.
        
        Returns:
            AuthorizationResult if rule applies, None to continue.
        """
        ...
```

### Audit_Logger Class

```python
class AuditLevel(Enum):
    """Audit logging levels."""
    NONE = "none"
    FAILURES_ONLY = "failures_only"
    ALL = "all"


@dataclass
class Audit_Entry:
    """Structured audit log entry."""
    
    timestamp: datetime
    event_type: str  # "authentication", "authorization", "violation"
    outcome: str  # "success", "failure"
    user_id: Optional[str]
    endpoint: Optional[str]
    policy: Optional[str]
    reason: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    request_id: Optional[str]
    correlation_id: Optional[str]
    extra: Dict[str, Any] = field(default_factory=dict)
    
    def to_json(self) -> str:
        """Serialize entry to JSON."""
        pass


class AuditDestination(Protocol):
    """Protocol for audit log destinations."""
    
    def write(self, entry: Audit_Entry) -> None:
        """Write an audit entry."""
        ...
    
    async def write_async(self, entry: Audit_Entry) -> None:
        """Async write an audit entry."""
        ...


class Audit_Logger:
    """
    Logs security events for compliance and forensics.
    """
    
    def __init__(
        self,
        level: AuditLevel = AuditLevel.ALL,
        destinations: Optional[List[AuditDestination]] = None
    ):
        self._level = level
        self._destinations = destinations or []
        self._queue: asyncio.Queue = asyncio.Queue()
    
    def log_authentication(
        self,
        request: "Request",
        context: Security_Context,
        provider: str,
        success: bool
    ) -> None:
        """Log an authentication attempt."""
        pass
    
    def log_authorization(
        self,
        request: "Request",
        context: Security_Context,
        policy: AccessPolicy,
        result: AuthorizationResult
    ) -> None:
        """Log an authorization decision."""
        pass
    
    def log_violation(
        self,
        request: "Request",
        context: Security_Context,
        policy: AccessPolicy,
        constraint: str
    ) -> None:
        """Log a policy violation."""
        pass
    
    def add_destination(self, destination: AuditDestination) -> None:
        """Add an audit log destination."""
        pass
    
    def query(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_type: Optional[str] = None,
        user_id: Optional[str] = None,
        outcome: Optional[str] = None
    ) -> List[Audit_Entry]:
        """Query historical audit entries."""
        pass
```

### Policy Factories

```python
def public() -> AccessPolicy:
    """
    Create a policy that allows unauthenticated access.
    
    Returns:
        AccessPolicy with require_auth=False.
    """
    return AccessPolicy(require_auth=False)


def authenticated() -> AccessPolicy:
    """
    Create a policy requiring any authenticated user.
    
    Returns:
        AccessPolicy with require_auth=True, no role/scope requirements.
    """
    return AccessPolicy(require_auth=True)


def roles(*role_names: str) -> AccessPolicy:
    """
    Create a policy requiring specific roles.
    
    Args:
        *role_names: Role names required for access.
    
    Returns:
        AccessPolicy with specified roles.
    """
    return AccessPolicy(roles=tuple(role_names), require_auth=True)


def scopes(*scope_names: str) -> AccessPolicy:
    """
    Create a policy requiring specific scopes.
    
    Args:
        *scope_names: Scope names required for access.
    
    Returns:
        AccessPolicy with specified scopes.
    """
    return AccessPolicy(scopes=tuple(scope_names), require_auth=True)
```

### Security Decorators

```python
def require_auth(handler: F) -> F:
    """
    Decorator that enforces authentication on a handler.
    
    Integrates with EndpointDescriptor to record security metadata.
    """
    pass


def require_roles(*role_names: str) -> Callable[[F], F]:
    """
    Decorator that enforces role requirements on a handler.
    
    Args:
        *role_names: Role names required for access.
    """
    pass


def require_scopes(*scope_names: str) -> Callable[[F], F]:
    """
    Decorator that enforces scope requirements on a handler.
    
    Args:
        *scope_names: Scope names required for access.
    """
    pass


def public_endpoint(handler: F) -> F:
    """
    Decorator that marks an endpoint as publicly accessible.
    
    Integrates with EndpointDescriptor to record security metadata.
    """
    pass
```

### Security Error Classes

```python
class SecurityError(Exception):
    """Base class for security-related errors."""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)
    
    def to_response_body(self, include_details: bool = False) -> Dict[str, Any]:
        """Convert to response body dict."""
        pass


class AuthenticationError(SecurityError):
    """Raised when authentication fails."""
    
    def __init__(
        self,
        message: str = "Authentication required",
        schemes: Optional[List[str]] = None
    ):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_REQUIRED",
            status_code=401
        )
        self.schemes = schemes or []
    
    def get_www_authenticate_header(self) -> str:
        """Get WWW-Authenticate header value."""
        pass


class AuthorizationError(SecurityError):
    """Raised when authorization fails."""
    
    def __init__(
        self,
        message: str = "Access denied",
        reason: Optional[str] = None
    ):
        super().__init__(
            message=message,
            error_code="ACCESS_DENIED",
            status_code=403
        )
        self._internal_reason = reason  # Not exposed in response


class PolicyValidationError(SecurityError):
    """Raised when an invalid policy is attached."""
    
    def __init__(self, message: str, policy: Any):
        super().__init__(
            message=message,
            error_code="INVALID_POLICY",
            status_code=500
        )
        self.policy = policy


class SecurityCompletenessError(SecurityError):
    """Raised when security completeness validation fails."""
    
    def __init__(self, unprotected_endpoints: List[str]):
        super().__init__(
            message=f"Security completeness check failed: {len(unprotected_endpoints)} unprotected endpoints",
            error_code="SECURITY_INCOMPLETE",
            status_code=500
        )
        self.unprotected_endpoints = unprotected_endpoints
```

### Security Middleware

```python
class SecurityMiddleware:
    """
    Middleware that handles authentication and authorization
    for incoming requests.
    """
    
    def __init__(
        self,
        auth_manager: Authentication_Manager,
        authz_engine: Authorization_Engine,
        audit_logger: Audit_Logger,
        default_policy: Optional[AccessPolicy] = None,
        security_audit_mode: bool = False
    ):
        pass
    
    def __call__(self, request: "Request", next: Callable) -> "Response":
        """
        Process request through security layer.
        
        1. Authenticate request
        2. Get policy for endpoint
        3. Authorize request
        4. Log security events
        5. Call next handler or return error
        """
        pass
    
    def get_policy_for_endpoint(
        self,
        endpoint: "EndpointDescriptor"
    ) -> AccessPolicy:
        """Get the effective policy for an endpoint."""
        pass
```

## Data Models

### Request Metadata for Audit

```python
@dataclass
class RequestSecurityMetadata:
    """Security-relevant request metadata for audit logging."""
    
    ip_address: str
    user_agent: str
    request_id: str
    correlation_id: Optional[str]
    endpoint_path: str
    http_method: str
    timestamp: datetime
```

### Policy Inheritance Chain

```python
@dataclass
class PolicyInheritanceNode:
    """Node in the policy inheritance chain for debugging."""
    
    path: str
    policy: Optional[AccessPolicy]
    source: str  # "explicit", "inherited", "default"
    parent: Optional["PolicyInheritanceNode"]
    
    def get_chain(self) -> List["PolicyInheritanceNode"]:
        """Get the full inheritance chain from root to this node."""
        pass
    
    def get_effective_policy(self) -> AccessPolicy:
        """Compute the effective merged policy for this node."""
        pass
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property 1: Policy Merge Behavior

*For any* two AccessPolicy objects P1 and P2, when `P1.merge_with(P2)` is called:
- The resulting policy's roles SHALL be the union of P1.roles and P2.roles (unless `replace_roles=True`)
- The resulting policy's scopes SHALL be the union of P1.scopes and P2.scopes (unless `replace_scopes=True`)
- When `replace_roles=True`, the result SHALL contain only P2.roles
- When `replace_scopes=True`, the result SHALL contain only P2.scopes
- The resulting policy's `require_auth` SHALL be True if either P1 or P2 requires auth

**Validates: Requirements 1.5, 3.3, 3.4, 3.5, 3.6, 3.7**

### Property 2: Policy Evaluation

*For any* AccessPolicy P and Security_Context C, `P.check(C)` SHALL return True if and only if:
- If `P.require_auth=True`, then `C.is_authenticated` must be True
- If `P.roles` is non-empty, then C must have at least one role from P.roles (OR logic)
- If `P.scopes` is non-empty, then C must have all scopes from P.scopes (AND logic)

**Validates: Requirements 1.6, 1.7, 5.1, 5.3, 5.4, 5.5**

### Property 3: Policy Inheritance Security

*For any* parent-child endpoint relationship where parent has policy P_parent and child has policy P_child:
- If P_child is None, the effective policy SHALL be P_parent
- If P_child is defined, the effective policy SHALL be at least as restrictive as P_parent
- The combined policy SHALL never allow access that P_parent would deny (security non-weakening)

**Validates: Requirements 3.1, 3.2, 3.8, 3.9**

### Property 4: Authentication Provider Chain

*For any* set of registered Authentication_Providers and any request:
- Providers SHALL be tried in priority order (lower priority number first)
- If a provider returns a Security_Context, subsequent providers SHALL NOT be called
- If a provider returns None, the next provider SHALL be tried
- If all providers return None, a guest Security_Context SHALL be returned

**Validates: Requirements 4.4, 4.7, 4.8**

### Property 5: Audit Log Completeness

*For any* authentication attempt or authorization decision:
- An Audit_Entry SHALL be created with timestamp, event_type, and outcome
- The entry SHALL include user_id (if authenticated), endpoint, and policy
- The entry SHALL include request metadata: IP address, user agent, request_id
- The entry SHALL be serializable to valid JSON

**Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.7**

### Property 6: Security Context Integrity

*For any* Security_Context C:
- C SHALL be immutable after creation (frozen dataclass)
- `C.has_role(r)` SHALL return True iff r is in C.roles
- `C.has_scope(s)` SHALL return True iff s is in C.scopes
- `C.has_any_role(*rs)` SHALL return True iff any r in rs is in C.roles
- `C.has_all_scopes(*ss)` SHALL return True iff all s in ss are in C.scopes

**Validates: Requirements 8.6, 8.7**

### Property 7: Security Decorator Behavior

*For any* handler function decorated with security decorators:
- `@require_auth` SHALL create an AccessPolicy with `require_auth=True`
- `@require_roles(*rs)` SHALL create an AccessPolicy with `roles=rs`
- `@require_scopes(*ss)` SHALL create an AccessPolicy with `scopes=ss`
- `@public_endpoint` SHALL create an AccessPolicy with `require_auth=False`
- Decorators SHALL be stackable and the resulting policy SHALL combine all constraints
- The EndpointDescriptor SHALL contain the combined policy in its constraints

**Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.8**

### Property 8: Security Error Response

*For any* authentication or authorization failure:
- Authentication failures SHALL return HTTP 401 with error_code and message
- Authorization failures SHALL return HTTP 403 with error_code and message
- 401 responses SHALL include WWW-Authenticate header
- Error responses SHALL NOT include internal security details (role names, specific constraints)

**Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.6**

### Property 9: Default-Deny Enforcement

*For any* endpoint without an explicit AccessPolicy:
- The system SHALL apply the configured default_access_policy
- If no default is configured, access SHALL be denied
- The effective policy SHALL never be less restrictive than the default

**Validates: Requirements 6.1, 6.2**

### Property 10: Policy Attachment Storage

*For any* endpoint with an attached AccessPolicy:
- The policy SHALL be stored in the EndpointDescriptor's constraints field
- The stored policy SHALL be a valid AccessPolicy instance
- Invalid policy attachments SHALL raise PolicyValidationError

**Validates: Requirements 2.2, 2.4, 2.5**

## Error Handling

### Authentication Errors

Authentication errors occur when a request cannot be authenticated:

```python
class AuthenticationError(SecurityError):
    """Raised when authentication fails."""
    
    def __init__(
        self,
        message: str = "Authentication required",
        schemes: Optional[List[str]] = None
    ):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_REQUIRED",
            status_code=401
        )
        self.schemes = schemes or ["Bearer"]
```

Common scenarios:
- Missing authentication credentials
- Invalid or expired token
- Malformed authentication header

### Authorization Errors

Authorization errors occur when an authenticated user lacks required permissions:

```python
class AuthorizationError(SecurityError):
    """Raised when authorization fails."""
    
    def __init__(
        self,
        message: str = "Access denied",
        reason: Optional[str] = None
    ):
        super().__init__(
            message=message,
            error_code="ACCESS_DENIED",
            status_code=403
        )
        self._internal_reason = reason  # Logged but not exposed
```

Common scenarios:
- User lacks required role
- User lacks required scope
- Custom authorization rule denied access

### Policy Validation Errors

Policy validation errors occur when invalid policies are attached:

```python
class PolicyValidationError(SecurityError):
    """Raised when an invalid policy is attached."""
    
    def __init__(self, message: str, policy: Any):
        super().__init__(
            message=message,
            error_code="INVALID_POLICY",
            status_code=500
        )
        self.policy = policy
```

### Security Completeness Errors

Security completeness errors occur during startup validation:

```python
class SecurityCompletenessError(SecurityError):
    """Raised when security completeness validation fails."""
    
    def __init__(self, unprotected_endpoints: List[str]):
        super().__init__(
            message=f"Security completeness check failed",
            error_code="SECURITY_INCOMPLETE",
            status_code=500
        )
        self.unprotected_endpoints = unprotected_endpoints
```

## Testing Strategy

### Unit Tests

Unit tests should cover:

1. **AccessPolicy Tests**
   - Verify AccessPolicy has roles, scopes, require_auth attributes
   - Verify merge_with() method exists and accepts parameters
   - Verify check() method exists and returns boolean
   - Verify policy factories return valid AccessPolicy instances

2. **Security_Context Tests**
   - Verify Security_Context has all required fields
   - Verify helper methods (has_role, has_scope, etc.) exist
   - Verify guest() factory returns unauthenticated context
   - Verify immutability (frozen dataclass)

3. **Authentication Provider Tests**
   - Verify JWTAuthProvider extracts and validates tokens
   - Verify SessionAuthProvider validates sessions
   - Verify APIKeyAuthProvider validates API keys
   - Verify providers return None on failure (no exceptions)

4. **Authorization Engine Tests**
   - Verify evaluate() returns AuthorizationResult
   - Verify role checking uses OR logic
   - Verify scope checking uses AND logic
   - Verify hooks are called in correct order

5. **Audit Logger Tests**
   - Verify log entries contain required fields
   - Verify JSON serialization works
   - Verify filtering by level works

6. **Error Response Tests**
   - Verify 401 responses include WWW-Authenticate header
   - Verify error bodies have correct structure
   - Verify sensitive info is not leaked

### Property-Based Tests

Property-based tests should use the `testbase` framework with minimum 100 iterations per property. Each test should be tagged with the property it validates.

**Testing Framework**: testbase (as specified in AGENTS.md)

**Property Test Configuration**:
- Minimum iterations: 100
- Tag format: `Feature: access-policy, Property N: <property_text>`

**Generator Requirements**:
- Generate valid AccessPolicy objects with random roles/scopes
- Generate valid Security_Context objects with random user data
- Generate parent-child policy hierarchies
- Generate authentication provider chains
- Generate audit log entries with random metadata

### Test Organization

Following the repository conventions from AGENTS.md:

```
source/testroots/ccai/tests/singlehost/webworks/
├── security/
│   ├── test_access_policy.py          # AccessPolicy tests
│   ├── test_security_context.py       # Security_Context tests
│   ├── test_authentication.py         # Authentication provider tests
│   ├── test_authorization.py          # Authorization engine tests
│   ├── test_audit_logger.py           # Audit logging tests
│   ├── test_policy_factories.py       # Policy factory tests
│   ├── test_security_decorators.py    # Decorator tests
│   └── test_security_errors.py        # Error handling tests
```

### Integration Points

- Integration with EndpointDescriptor for policy storage
- Integration with Router for policy enforcement
- Integration with Middleware pipeline for request processing
- Integration with logging system for audit output
- Integration with configuration system for default policies
