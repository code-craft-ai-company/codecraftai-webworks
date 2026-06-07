# Design Document

## Overview

The Authentication System provides a modular, extensible framework for authenticating requests in the codecraftai-webworks framework. It follows a pluggable architecture where different authentication mechanisms (Basic, Bearer, OAuth2, etc.) are implemented as discrete Authenticator components that can be registered and configured independently.

The design prioritizes:
- **Debuggability**: Clear error messages and comprehensive logging
- **Extensibility**: Easy addition of new authentication schemes
- **Integration**: Seamless integration with existing ASGI/WSGI layers and access policies
- **Security**: Secure defaults and protection against common attacks

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Request Flow                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────┐    ┌─────────────────────┐    ┌──────────────────┐   │
│  │  Request │───▶│ Authentication      │───▶│ Endpoint Handler │   │
│  │          │    │ Middleware          │    │                  │   │
│  └──────────┘    └─────────────────────┘    └──────────────────┘   │
│                           │                                         │
│                           ▼                                         │
│                  ┌─────────────────────┐                           │
│                  │ Authentication      │                           │
│                  │ System              │                           │
│                  └─────────────────────┘                           │
│                           │                                         │
│         ┌─────────────────┼─────────────────┐                      │
│         ▼                 ▼                 ▼                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                │
│  │   Basic     │  │   Bearer    │  │   OAuth2    │  ...           │
│  │Authenticator│  │Authenticator│  │Authenticator│                │
│  └─────────────┘  └─────────────┘  └─────────────┘                │
│         │                 │                 │                      │
│         ▼                 ▼                 ▼                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                │
│  │  Identity   │  │   Token     │  │   OAuth     │                │
│  │  Provider   │  │   Store     │  │   Provider  │                │
│  └─────────────┘  └─────────────┘  └─────────────┘                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### Core Interfaces

#### AuthenticationResult

```python
from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass

class AuthenticationStatus(Enum):
    """Status of an authentication attempt."""
    SUCCESS = "success"
    FAILURE = "failure"
    CHALLENGE = "challenge"  # Requires client response (e.g., Digest auth)
    SKIP = "skip"  # Authenticator doesn't apply to this request

@dataclass
class AuthenticationResult:
    """Result of an authentication attempt."""
    status: AuthenticationStatus
    context: Optional['AuthenticationContext'] = None
    challenge: Optional[str] = None  # WWW-Authenticate header value
    error_code: Optional[str] = None
    error_description: Optional[str] = None
```

#### Principal

```python
from typing import Set, Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class Principal:
    """Represents an authenticated entity."""
    identifier: str
    display_name: Optional[str] = None
    roles: Set[str] = field(default_factory=set)
    permissions: Set[str] = field(default_factory=set)
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    def has_role(self, role: str) -> bool:
        """Check if principal has a specific role."""
        return role in self.roles
    
    def has_permission(self, permission: str) -> bool:
        """Check if principal has a specific permission."""
        return permission in self.permissions
```

#### AuthenticationContext

```python
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class AuthenticationContext:
    """Context containing authentication information."""
    principal: Principal
    scheme: str
    authenticated_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_expired(self) -> bool:
        """Check if authentication has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
```

#### Authenticator Protocol

```python
from typing import Protocol, Optional
from abc import abstractmethod

class Authenticator(Protocol):
    """Protocol for authentication implementations."""
    
    @property
    def scheme(self) -> str:
        """Return the authentication scheme identifier."""
        ...
    
    @abstractmethod
    async def authenticate(self, request: 'Request') -> AuthenticationResult:
        """
        Attempt to authenticate the request.
        
        Returns:
            AuthenticationResult with status and context/error info
        """
        ...
    
    def can_handle(self, request: 'Request') -> bool:
        """Check if this authenticator can handle the request."""
        ...
```

#### IdentityProvider Protocol

```python
from typing import Protocol, Optional

class IdentityProvider(Protocol):
    """Protocol for identity validation backends."""
    
    async def validate_credentials(
        self, 
        username: str, 
        password: str
    ) -> Optional[Principal]:
        """Validate username/password credentials."""
        ...
    
    async def get_principal(self, identifier: str) -> Optional[Principal]:
        """Retrieve principal by identifier."""
        ...
```

#### TokenStore Protocol

```python
from typing import Protocol, Optional, Dict, Any

class TokenStore(Protocol):
    """Protocol for token storage and validation."""
    
    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate token and return claims if valid."""
        ...
    
    async def store_token(
        self, 
        token: str, 
        claims: Dict[str, Any], 
        expires_in: int
    ) -> None:
        """Store a token with its claims."""
        ...
    
    async def revoke_token(self, token: str) -> bool:
        """Revoke a token."""
        ...
```

### Authentication System

```python
from typing import Dict, List, Optional

class AuthenticationSystem:
    """Central authentication coordinator."""
    
    def __init__(self):
        self._authenticators: Dict[str, Authenticator] = {}
        self._scheme_order: List[str] = []
    
    def register(
        self, 
        authenticator: Authenticator, 
        priority: int = 0
    ) -> None:
        """Register an authenticator with optional priority."""
        scheme = authenticator.scheme
        self._authenticators[scheme] = authenticator
        self._update_order(scheme, priority)
    
    def unregister(self, scheme: str) -> bool:
        """Unregister an authenticator by scheme."""
        if scheme in self._authenticators:
            del self._authenticators[scheme]
            self._scheme_order.remove(scheme)
            return True
        return False
    
    async def authenticate(self, request: 'Request') -> AuthenticationResult:
        """
        Attempt authentication using registered authenticators.
        
        Iterates through authenticators in priority order until one
        succeeds or returns a definitive failure.
        """
        challenges = []
        
        for scheme in self._scheme_order:
            authenticator = self._authenticators[scheme]
            
            if not authenticator.can_handle(request):
                continue
            
            result = await authenticator.authenticate(request)
            
            if result.status == AuthenticationStatus.SUCCESS:
                return result
            elif result.status == AuthenticationStatus.CHALLENGE:
                challenges.append(result.challenge)
            elif result.status == AuthenticationStatus.FAILURE:
                # Definitive failure, stop trying
                return result
        
        # No authenticator succeeded
        if challenges:
            return AuthenticationResult(
                status=AuthenticationStatus.CHALLENGE,
                challenge=", ".join(challenges)
            )
        
        return AuthenticationResult(
            status=AuthenticationStatus.FAILURE,
            error_code="no_credentials",
            error_description="No valid credentials provided"
        )
```

### Authenticator Implementations

#### BasicAuthenticator

```python
import base64
from typing import Optional

class BasicAuthenticator:
    """HTTP Basic Authentication implementation."""
    
    def __init__(self, identity_provider: IdentityProvider, realm: str = "Restricted"):
        self._identity_provider = identity_provider
        self._realm = realm
    
    @property
    def scheme(self) -> str:
        return "Basic"
    
    def can_handle(self, request: 'Request') -> bool:
        auth_header = request.headers.get("Authorization", "")
        return auth_header.lower().startswith("basic ")
    
    async def authenticate(self, request: 'Request') -> AuthenticationResult:
        auth_header = request.headers.get("Authorization", "")
        
        if not auth_header:
            return self._challenge_response()
        
        try:
            scheme, credentials = auth_header.split(" ", 1)
            if scheme.lower() != "basic":
                return AuthenticationResult(status=AuthenticationStatus.SKIP)
            
            decoded = base64.b64decode(credentials).decode("utf-8")
            if ":" not in decoded:
                return self._bad_request("Malformed credentials")
            
            username, password = decoded.split(":", 1)
            
        except (ValueError, UnicodeDecodeError):
            return self._bad_request("Invalid Base64 encoding")
        
        principal = await self._identity_provider.validate_credentials(
            username, password
        )
        
        if principal is None:
            return AuthenticationResult(
                status=AuthenticationStatus.FAILURE,
                error_code="invalid_credentials",
                error_description="Invalid username or password"
            )
        
        return AuthenticationResult(
            status=AuthenticationStatus.SUCCESS,
            context=AuthenticationContext(
                principal=principal,
                scheme=self.scheme
            )
        )
    
    def _challenge_response(self) -> AuthenticationResult:
        return AuthenticationResult(
            status=AuthenticationStatus.CHALLENGE,
            challenge=f'Basic realm="{self._realm}"'
        )
    
    def _bad_request(self, message: str) -> AuthenticationResult:
        return AuthenticationResult(
            status=AuthenticationStatus.FAILURE,
            error_code="bad_request",
            error_description=message
        )
```

#### BearerAuthenticator

```python
from typing import Optional, List
import jwt
from datetime import datetime

class BearerAuthenticator:
    """Bearer Token Authentication with JWT support."""
    
    def __init__(
        self,
        token_store: Optional[TokenStore] = None,
        jwt_secret: Optional[str] = None,
        jwt_algorithms: List[str] = None,
        jwt_issuer: Optional[str] = None,
        jwt_audience: Optional[str] = None
    ):
        self._token_store = token_store
        self._jwt_secret = jwt_secret
        self._jwt_algorithms = jwt_algorithms or ["HS256"]
        self._jwt_issuer = jwt_issuer
        self._jwt_audience = jwt_audience
    
    @property
    def scheme(self) -> str:
        return "Bearer"
    
    def can_handle(self, request: 'Request') -> bool:
        auth_header = request.headers.get("Authorization", "")
        return auth_header.lower().startswith("bearer ")
    
    async def authenticate(self, request: 'Request') -> AuthenticationResult:
        auth_header = request.headers.get("Authorization", "")
        
        if not auth_header:
            return AuthenticationResult(status=AuthenticationStatus.SKIP)
        
        try:
            scheme, token = auth_header.split(" ", 1)
            if scheme.lower() != "bearer":
                return AuthenticationResult(status=AuthenticationStatus.SKIP)
        except ValueError:
            return AuthenticationResult(status=AuthenticationStatus.SKIP)
        
        # Try JWT validation first
        if self._jwt_secret:
            result = self._validate_jwt(token)
            if result.status != AuthenticationStatus.SKIP:
                return result
        
        # Fall back to token store
        if self._token_store:
            claims = await self._token_store.validate_token(token)
            if claims:
                return self._create_success_result(claims)
        
        return AuthenticationResult(
            status=AuthenticationStatus.FAILURE,
            error_code="invalid_token",
            error_description="The access token is invalid"
        )
    
    def _validate_jwt(self, token: str) -> AuthenticationResult:
        try:
            claims = jwt.decode(
                token,
                self._jwt_secret,
                algorithms=self._jwt_algorithms,
                issuer=self._jwt_issuer,
                audience=self._jwt_audience
            )
            return self._create_success_result(claims)
        except jwt.ExpiredSignatureError:
            return AuthenticationResult(
                status=AuthenticationStatus.FAILURE,
                error_code="invalid_token",
                error_description="The access token has expired"
            )
        except jwt.InvalidTokenError as e:
            return AuthenticationResult(
                status=AuthenticationStatus.FAILURE,
                error_code="invalid_token",
                error_description=str(e)
            )
    
    def _create_success_result(self, claims: dict) -> AuthenticationResult:
        principal = Principal(
            identifier=claims.get("sub", "unknown"),
            display_name=claims.get("name"),
            roles=set(claims.get("roles", [])),
            attributes=claims
        )
        
        expires_at = None
        if "exp" in claims:
            expires_at = datetime.fromtimestamp(claims["exp"])
        
        return AuthenticationResult(
            status=AuthenticationStatus.SUCCESS,
            context=AuthenticationContext(
                principal=principal,
                scheme=self.scheme,
                expires_at=expires_at,
                attributes=claims
            )
        )
```

#### APIKeyAuthenticator

```python
from typing import Optional
from enum import Enum

class APIKeyLocation(Enum):
    HEADER = "header"
    QUERY = "query"
    COOKIE = "cookie"

class APIKeyAuthenticator:
    """API Key Authentication implementation."""
    
    def __init__(
        self,
        key_store: 'APIKeyStore',
        key_name: str = "X-API-Key",
        location: APIKeyLocation = APIKeyLocation.HEADER
    ):
        self._key_store = key_store
        self._key_name = key_name
        self._location = location
    
    @property
    def scheme(self) -> str:
        return "APIKey"
    
    def can_handle(self, request: 'Request') -> bool:
        return self._extract_key(request) is not None
    
    async def authenticate(self, request: 'Request') -> AuthenticationResult:
        api_key = self._extract_key(request)
        
        if api_key is None:
            return AuthenticationResult(
                status=AuthenticationStatus.FAILURE,
                error_code="missing_api_key",
                error_description="API key not provided"
            )
        
        key_info = await self._key_store.validate_key(api_key)
        
        if key_info is None:
            return AuthenticationResult(
                status=AuthenticationStatus.FAILURE,
                error_code="invalid_api_key",
                error_description="Invalid API key"
            )
        
        principal = Principal(
            identifier=key_info.get("client_id", api_key[:8]),
            display_name=key_info.get("name"),
            roles=set(key_info.get("roles", [])),
            permissions=set(key_info.get("permissions", [])),
            attributes=key_info
        )
        
        return AuthenticationResult(
            status=AuthenticationStatus.SUCCESS,
            context=AuthenticationContext(
                principal=principal,
                scheme=self.scheme,
                attributes=key_info
            )
        )
    
    def _extract_key(self, request: 'Request') -> Optional[str]:
        if self._location == APIKeyLocation.HEADER:
            return request.headers.get(self._key_name)
        elif self._location == APIKeyLocation.QUERY:
            return request.query_params.get(self._key_name)
        elif self._location == APIKeyLocation.COOKIE:
            return request.cookies.get(self._key_name)
        return None
```

### Authentication Middleware

```python
from typing import Optional, Set, Callable

class AuthenticationMiddleware:
    """ASGI middleware for authentication."""
    
    def __init__(
        self,
        app: 'ASGIApplication',
        auth_system: AuthenticationSystem,
        exclude_paths: Optional[Set[str]] = None,
        optional_paths: Optional[Set[str]] = None
    ):
        self._app = app
        self._auth_system = auth_system
        self._exclude_paths = exclude_paths or set()
        self._optional_paths = optional_paths or set()
    
    async def __call__(self, scope: dict, receive: Callable, send: Callable):
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return
        
        path = scope.get("path", "/")
        
        # Skip authentication for excluded paths
        if self._is_excluded(path):
            await self._app(scope, receive, send)
            return
        
        request = Request(scope)
        result = await self._auth_system.authenticate(request)
        
        if result.status == AuthenticationStatus.SUCCESS:
            # Attach context to scope
            scope["auth"] = result.context
            await self._app(scope, receive, send)
            
        elif result.status == AuthenticationStatus.CHALLENGE:
            if self._is_optional(path):
                # Allow unauthenticated access for optional paths
                scope["auth"] = None
                await self._app(scope, receive, send)
            else:
                await self._send_challenge(send, result.challenge)
                
        else:  # FAILURE or SKIP
            if self._is_optional(path):
                scope["auth"] = None
                await self._app(scope, receive, send)
            else:
                await self._send_unauthorized(send, result)
    
    def _is_excluded(self, path: str) -> bool:
        return path in self._exclude_paths
    
    def _is_optional(self, path: str) -> bool:
        return path in self._optional_paths
    
    async def _send_challenge(self, send: Callable, challenge: str):
        await send({
            "type": "http.response.start",
            "status": 401,
            "headers": [
                (b"content-type", b"application/json"),
                (b"www-authenticate", challenge.encode())
            ]
        })
        await send({
            "type": "http.response.body",
            "body": b'{"error": "authentication_required"}'
        })
    
    async def _send_unauthorized(self, send: Callable, result: AuthenticationResult):
        body = {
            "error": result.error_code or "unauthorized",
            "error_description": result.error_description or "Authentication failed"
        }
        await send({
            "type": "http.response.start",
            "status": 401,
            "headers": [(b"content-type", b"application/json")]
        })
        await send({
            "type": "http.response.body",
            "body": json.dumps(body).encode()
        })
```

## Data Models

### Session Data Model

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional

@dataclass
class SessionData:
    """Represents a user session."""
    session_id: str
    principal_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    data: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
```

### OAuth2 Token Models

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Set

@dataclass
class OAuth2Token:
    """OAuth 2.0 token representation."""
    access_token: str
    token_type: str = "Bearer"
    expires_in: Optional[int] = None
    refresh_token: Optional[str] = None
    scope: Optional[Set[str]] = None
    
    def to_dict(self) -> dict:
        result = {
            "access_token": self.access_token,
            "token_type": self.token_type
        }
        if self.expires_in:
            result["expires_in"] = self.expires_in
        if self.refresh_token:
            result["refresh_token"] = self.refresh_token
        if self.scope:
            result["scope"] = " ".join(self.scope)
        return result

@dataclass
class OAuth2AuthorizationCode:
    """OAuth 2.0 authorization code."""
    code: str
    client_id: str
    redirect_uri: str
    scope: Set[str]
    state: Optional[str]
    code_challenge: Optional[str] = None  # PKCE
    code_challenge_method: Optional[str] = None  # PKCE
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
```



## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Authenticator Registry Consistency

*For any* set of Authenticators registered with the Authentication_System, the registry SHALL contain exactly those authenticators, each associated with its unique scheme identifier, and the count of registered authenticators SHALL equal the number of registrations.

**Validates: Requirements 1.1, 1.2, 1.3**

### Property 2: Authentication Iteration Terminates on Success

*For any* request and set of registered Authenticators where at least one can successfully authenticate, the Authentication_System SHALL return SUCCESS with a valid Authentication_Context, and no subsequent authenticators SHALL be invoked after the first success.

**Validates: Requirements 1.4, 1.5**

### Property 3: Authentication Failure When All Fail

*For any* request where no registered Authenticator succeeds, the Authentication_System SHALL return a FAILURE or CHALLENGE result with no Authentication_Context.

**Validates: Requirements 1.6**

### Property 4: Basic Auth Credential Round-Trip

*For any* valid username and password pair, encoding them as a Basic Authorization header and then extracting/decoding SHALL produce the original username and password.

**Validates: Requirements 2.1, 2.2**

### Property 5: Basic Auth Valid Credentials Produce Context

*For any* request with valid Basic credentials where the Identity_Provider confirms the credentials, the Basic_Authenticator SHALL return SUCCESS with an Authentication_Context containing a Principal with the correct identifier.

**Validates: Requirements 2.3, 2.4**

### Property 6: Basic Auth Invalid Credentials Produce 401

*For any* request with Basic credentials where the Identity_Provider rejects the credentials, the Basic_Authenticator SHALL return FAILURE with error indicating invalid credentials.

**Validates: Requirements 2.5**

### Property 7: Basic Auth Malformed Header Produces Error

*For any* Authorization header that starts with "Basic " but contains invalid Base64 or lacks the ":" separator, the Basic_Authenticator SHALL return FAILURE with a bad request error.

**Validates: Requirements 2.6**

### Property 8: Digest Auth Challenge Contains Nonce

*For any* unauthenticated request to a Digest-protected endpoint, the response SHALL include a WWW-Authenticate header with a non-empty nonce value.

**Validates: Requirements 3.1**

### Property 9: Digest Auth Nonce Freshness Validation

*For any* Digest authentication attempt with a nonce older than the configured maximum age, the Digest_Authenticator SHALL reject the request and indicate stale=true.

**Validates: Requirements 3.4, 3.6**

### Property 10: Bearer Token Extraction

*For any* request with an Authorization header of form "Bearer {token}", the Bearer_Authenticator SHALL extract exactly the token portion.

**Validates: Requirements 4.1**

### Property 11: JWT Validation Rejects Invalid Tokens

*For any* JWT token with an invalid signature, expired timestamp, or mismatched issuer, the Bearer_Authenticator SHALL return FAILURE with error_code="invalid_token".

**Validates: Requirements 4.4, 4.6, 4.7**

### Property 12: Valid JWT Produces Context with Claims

*For any* valid JWT token, the Bearer_Authenticator SHALL return SUCCESS with an Authentication_Context where the Principal identifier equals the "sub" claim and attributes contain all token claims.

**Validates: Requirements 4.5**

### Property 13: API Key Extraction from All Locations

*For any* API key placed in a header, query parameter, or cookie with the configured key name, the API_Key_Authenticator SHALL extract the same key value regardless of location.

**Validates: Requirements 5.1, 5.2, 5.3, 5.4**

### Property 14: Valid API Key Produces Context

*For any* valid API key recognized by the key store, the API_Key_Authenticator SHALL return SUCCESS with an Authentication_Context.

**Validates: Requirements 5.5, 5.6**

### Property 15: Invalid API Key Produces 401

*For any* API key not recognized by the key store, the API_Key_Authenticator SHALL return FAILURE.

**Validates: Requirements 5.7**

### Property 16: OAuth2 State Parameter Round-Trip

*For any* OAuth2 authorization request, the state parameter generated during initiation SHALL be validated during callback, and mismatched states SHALL be rejected.

**Validates: Requirements 6.5**

### Property 17: PKCE Code Challenge Verification

*For any* PKCE-enabled OAuth2 flow, the code_verifier provided during token exchange SHALL correctly verify against the code_challenge from authorization, using the specified method (plain or S256).

**Validates: Requirements 6.6**

### Property 18: OAuth2 Error Response Format

*For any* failed OAuth2 token exchange, the error response SHALL contain "error" and optionally "error_description" fields per RFC 6749.

**Validates: Requirements 6.9**

### Property 19: OIDC ID Token Claim Extraction

*For any* valid OIDC id_token, the Authentication_Context SHALL contain the standard claims (sub, name, email) as Principal attributes when present in the token.

**Validates: Requirements 7.4, 7.5**

### Property 20: Session Round-Trip

*For any* successful authentication that creates a session, the session ID stored in the cookie SHALL, when presented in a subsequent request, restore an equivalent Authentication_Context with the same Principal identifier.

**Validates: Requirements 8.1, 8.2, 8.3**

### Property 21: Session Expiration Enforcement

*For any* session with a configured expiration time, requests after that time SHALL fail authentication and clear the session cookie.

**Validates: Requirements 8.4, 8.8**

### Property 22: Session Cookie Security Attributes

*For any* session cookie set by the Session_Authenticator, the cookie SHALL have HttpOnly, Secure (when configured), and SameSite attributes set.

**Validates: Requirements 8.6**

### Property 23: HMAC Signature Validation

*For any* request with a valid HMAC signature computed over the canonical request string with the correct secret, the HMAC_Authenticator SHALL return SUCCESS.

**Validates: Requirements 9.1, 9.5, 9.6**

### Property 24: HMAC Timestamp Window Enforcement

*For any* HMAC-signed request with a timestamp outside the configured window, the HMAC_Authenticator SHALL return FAILURE.

**Validates: Requirements 9.3, 9.8**

### Property 25: Middleware Context Attachment

*For any* successfully authenticated request passing through Authentication_Middleware, the request scope SHALL contain an "auth" key with a valid Authentication_Context.

**Validates: Requirements 10.1, 10.2**

### Property 26: Middleware Protected Endpoint Enforcement

*For any* request to a protected endpoint without valid authentication, the Authentication_Middleware SHALL return a 401 response and NOT invoke the endpoint handler.

**Validates: Requirements 10.4, 10.7**

### Property 27: Middleware Optional Authentication

*For any* request to an optional-auth endpoint, the endpoint handler SHALL be invoked regardless of authentication status, with auth context present if authenticated or None if not.

**Validates: Requirements 10.5**

### Property 28: Authentication Context Structure Completeness

*For any* successful authentication regardless of scheme, the Authentication_Context SHALL contain: a non-null Principal, the scheme identifier string, and an authenticated_at timestamp.

**Validates: Requirements 11.1, 11.2, 11.3, 11.4**

### Property 29: Principal Structure Completeness

*For any* Principal in an Authentication_Context, the Principal SHALL have a non-empty identifier, and the roles and permissions collections SHALL be iterable (possibly empty).

**Validates: Requirements 11.5, 11.6**

### Property 30: Cross-Scheme Context Interface Consistency

*For any* two Authentication_Contexts produced by different authentication schemes, both SHALL expose the same interface (principal, scheme, authenticated_at, attributes) with compatible types.

**Validates: Requirements 11.7**

### Property 31: Error Response Credential Sanitization

*For any* authentication failure, the error response body and headers SHALL NOT contain the original credentials, tokens, or secrets from the request.

**Validates: Requirements 12.1**

### Property 32: Rate Limiting Enforcement

*For any* client exceeding the configured authentication attempt rate, subsequent attempts SHALL be rejected with a rate limit error until the window expires.

**Validates: Requirements 12.3**

### Property 33: Internal Error Response Safety

*For any* internal exception during authentication processing, the response SHALL be a 500 status with a generic error message that does not expose stack traces or internal details.

**Validates: Requirements 12.6**

## Error Handling

### Error Categories

1. **Client Errors (4xx)**
   - 400 Bad Request: Malformed credentials or request format
   - 401 Unauthorized: Missing, invalid, or expired credentials
   - 403 Forbidden: Valid credentials but insufficient permissions
   - 429 Too Many Requests: Rate limit exceeded

2. **Server Errors (5xx)**
   - 500 Internal Server Error: Unexpected errors during authentication
   - 503 Service Unavailable: Identity provider or token store unavailable

### Error Response Format

```python
@dataclass
class AuthenticationError:
    """Standard authentication error response."""
    error: str  # Error code (e.g., "invalid_token", "invalid_credentials")
    error_description: Optional[str] = None  # Human-readable description
    error_uri: Optional[str] = None  # URI for more information
    
    def to_dict(self) -> dict:
        result = {"error": self.error}
        if self.error_description:
            result["error_description"] = self.error_description
        if self.error_uri:
            result["error_uri"] = self.error_uri
        return result
```

### Error Handling Strategy

- All credential data is sanitized before logging
- Stack traces are never exposed in responses
- Detailed errors are logged server-side for debugging
- Client receives minimal information to prevent information leakage
- Rate limiting prevents brute force attacks

## Testing Strategy

### Dual Testing Approach

The authentication system requires both unit tests and property-based tests:

- **Unit tests**: Verify specific examples, edge cases, and error conditions
- **Property tests**: Verify universal properties across all valid inputs

### Property-Based Testing Configuration

- **Framework**: Use `hypothesis` patterns adapted for `testbase` framework
- **Minimum iterations**: 100 per property test
- **Tag format**: `Feature: authentication, Property {number}: {property_text}`

### Test Categories

1. **Credential Extraction Tests**
   - Basic auth header parsing
   - Bearer token extraction
   - API key extraction from headers/query/cookies
   - Digest auth parameter parsing

2. **Validation Tests**
   - JWT signature verification
   - Token expiration checking
   - HMAC signature validation
   - Session validity checking

3. **Round-Trip Tests**
   - Basic auth encode/decode
   - Session create/restore
   - OAuth2 state parameter
   - PKCE challenge/verifier

4. **Error Handling Tests**
   - Malformed input handling
   - Invalid credential responses
   - Rate limiting behavior
   - Internal error sanitization

5. **Integration Tests**
   - Middleware request flow
   - Multi-authenticator scenarios
   - Access policy integration

### Test Data Generation

For property-based tests, generators should produce:
- Valid and invalid credentials
- Various token formats (valid JWT, expired, wrong signature)
- Edge cases (empty strings, special characters, very long values)
- Boundary conditions (timestamps at expiration boundary)
