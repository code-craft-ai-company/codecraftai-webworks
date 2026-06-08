# Design Document

## Overview

The Authentication Blueprints system provides a set of specialized blueprint classes that extend RestBlueprint to offer pre-built authentication endpoints. Each blueprint corresponds to an authentication method (Basic, Bearer, OAuth2, etc.) and provides default endpoint implementations that can be customized or extended.

The design follows the existing blueprint pattern in webworks, where blueprints group related endpoints under a shared base path with inherited configuration.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Authentication Blueprints                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│                    ┌──────────────────────┐                         │
│                    │   RestBlueprint      │                         │
│                    └──────────────────────┘                         │
│                              │                                       │
│                              ▼                                       │
│                    ┌──────────────────────┐                         │
│                    │  Security_Blueprint  │                         │
│                    │  (Base Class)        │                         │
│                    └──────────────────────┘                         │
│                              │                                       │
│         ┌────────────────────┼────────────────────┐                 │
│         │                    │                    │                 │
│         ▼                    ▼                    ▼                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐             │
│  │Basic_Auth   │    │Bearer_Auth  │    │Session_Auth │             │
│  │Blueprint    │    │Blueprint    │    │Blueprint    │             │
│  └─────────────┘    └─────────────┘    └─────────────┘             │
│         │                    │                                      │
│         │                    │                                      │
│  ┌─────────────┐    ┌─────────────┐                                │
│  │API_Key      │    │OAuth2       │                                │
│  │Blueprint    │    │Blueprint    │                                │
│  └─────────────┘    └─────────────┘                                │
│                              │                                      │
│                              ▼                                      │
│                    ┌─────────────┐                                  │
│                    │OIDC         │                                  │
│                    │Blueprint    │                                  │
│                    └─────────────┘                                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### Security Blueprint Base Class

```python
from typing import Any, Callable, Dict, List, Optional, Type
from dataclasses import dataclass

from ccai.webworks.endpoints.restblueprint import RestBlueprint
from ccai.webworks.endpoints.accesspolicy import AccessPolicy
from ccai.webworks.endpoints.doc import Doc
from ccai.webworks.authentication.system import AuthenticationSystem
from ccai.webworks.authentication.context import AuthenticationContext


@dataclass
class AuthResponse:
    """Standard authentication response structure."""
    access_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_in: Optional[int] = None
    refresh_token: Optional[str] = None
    scope: Optional[str] = None
    
    def to_dict(self) -> dict:
        result = {}
        if self.access_token:
            result["access_token"] = self.access_token
            result["token_type"] = self.token_type
        if self.expires_in:
            result["expires_in"] = self.expires_in
        if self.refresh_token:
            result["refresh_token"] = self.refresh_token
        if self.scope:
            result["scope"] = self.scope
        return result


@dataclass
class AuthError:
    """Standard authentication error response per RFC 6749."""
    error: str
    error_description: Optional[str] = None
    error_uri: Optional[str] = None
    
    def to_dict(self) -> dict:
        result = {"error": self.error}
        if self.error_description:
            result["error_description"] = self.error_description
        if self.error_uri:
            result["error_uri"] = self.error_uri
        return result


class SecurityBlueprint(RestBlueprint):
    """
        Base class for authentication blueprints.
        
        Provides common functionality for authentication endpoints including
        error handling, hooks, and integration with the authentication system.
        
        Class Attributes:
            auth_system: The AuthenticationSystem instance for validation.
            enabled_endpoints: Set of endpoint names that are enabled.
            error_format: Format for error responses ("json" or "form").
    """
    
    auth_system: Optional[AuthenticationSystem] = None
    enabled_endpoints: set = {"all"}
    error_format: str = "json"
    
    @classmethod
    def configure(
        cls,
        auth_system: AuthenticationSystem,
        base_path: Optional[str] = None,
        enabled_endpoints: Optional[set] = None
    ) -> None:
        """
            Configure the blueprint with authentication system and options.
            
            :param auth_system: The authentication system for validation.
            :param base_path: Optional base path override.
            :param enabled_endpoints: Set of endpoint names to enable.
        """
        cls.auth_system = auth_system
        if base_path is not None:
            cls.base_path = base_path
        if enabled_endpoints is not None:
            cls.enabled_endpoints = enabled_endpoints
    
    @classmethod
    def is_endpoint_enabled(cls, endpoint_name: str) -> bool:
        """Check if a specific endpoint is enabled."""
        return "all" in cls.enabled_endpoints or endpoint_name in cls.enabled_endpoints
    
    @classmethod
    def pre_authenticate(cls, request: Any) -> Optional[AuthError]:
        """
            Hook called before authentication processing.
            
            Override to add custom pre-authentication logic like rate limiting.
            Return AuthError to abort authentication.
        """
        return None
    
    @classmethod
    def post_authenticate(
        cls, 
        request: Any, 
        context: AuthenticationContext
    ) -> None:
        """
            Hook called after successful authentication.
            
            Override to add custom post-authentication logic like logging.
        """
        pass
    
    @classmethod
    def format_error(cls, error: AuthError, status_code: int = 401) -> dict:
        """Format an error response according to configured format."""
        return {
            "status": status_code,
            "body": error.to_dict(),
            "content_type": "application/json"
        }
    
    @classmethod
    def format_success(cls, response: AuthResponse, status_code: int = 200) -> dict:
        """Format a success response."""
        return {
            "status": status_code,
            "body": response.to_dict(),
            "content_type": "application/json"
        }
```

### Basic Authentication Blueprint

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class LoginRequest:
    """Request schema for login endpoint."""
    username: str
    password: str


@dataclass
class LoginResponse:
    """Response schema for login endpoint."""
    authenticated: bool
    principal_id: Optional[str] = None
    message: Optional[str] = None


class BasicAuthBlueprint(SecurityBlueprint):
    """
        Blueprint for HTTP Basic Authentication endpoints.
        
        Provides login and logout endpoints for username/password authentication.
        
        Default Endpoints:
            POST /login - Authenticate with username/password
            POST /logout - End the current session (optional)
    """
    
    base_path: str = "/auth/basic"
    tags: List[str] = ["Authentication", "Basic"]
    
    # Configuration
    identity_provider: Optional['IdentityProvider'] = None
    issue_token: bool = False  # If True, return JWT token on login
    
    @classmethod
    @SecurityBlueprint.create(
        leaf="login",
        request_schema=LoginRequest,
        response_schema=LoginResponse,
        doc=Doc(
            summary="Login with username and password",
            description="Authenticate using HTTP Basic credentials."
        )
    )
    def login(cls, request: Any) -> dict:
        """
            Handle login request with username/password.
            
            Validates credentials against the configured identity provider
            and returns authentication result.
        """
        if not cls.is_endpoint_enabled("login"):
            return cls.format_error(
                AuthError("endpoint_disabled", "Login endpoint is disabled"),
                status_code=404
            )
        
        # Pre-authentication hook
        pre_error = cls.pre_authenticate(request)
        if pre_error:
            return cls.format_error(pre_error)
        
        # Extract credentials from request body
        body = request.json()
        username = body.get("username")
        password = body.get("password")
        
        if not username or not password:
            return cls.format_error(
                AuthError("invalid_request", "Username and password required")
            )
        
        # Validate credentials
        principal = cls.identity_provider.validate_credentials(username, password)
        
        if principal is None:
            return cls.format_error(
                AuthError("invalid_credentials", "Invalid username or password")
            )
        
        # Create authentication context
        context = AuthenticationContext(
            principal=principal,
            scheme="Basic"
        )
        
        # Post-authentication hook
        cls.post_authenticate(request, context)
        
        # Return response
        response = LoginResponse(
            authenticated=True,
            principal_id=principal.identifier,
            message="Login successful"
        )
        
        return cls.format_success(
            AuthResponse(access_token=None),  # Or JWT if issue_token=True
            status_code=200
        )
    
    @classmethod
    @SecurityBlueprint.create(
        leaf="logout",
        doc=Doc(
            summary="Logout",
            description="End the current authentication session."
        )
    )
    def logout(cls, request: Any) -> dict:
        """Handle logout request."""
        if not cls.is_endpoint_enabled("logout"):
            return cls.format_error(
                AuthError("endpoint_disabled", "Logout endpoint is disabled"),
                status_code=404
            )
        
        return {"status": 200, "body": {"message": "Logged out"}}
```

### Bearer Token Blueprint

```python
@dataclass
class TokenRequest:
    """Request schema for token endpoint."""
    grant_type: str
    username: Optional[str] = None
    password: Optional[str] = None
    refresh_token: Optional[str] = None
    scope: Optional[str] = None


@dataclass
class TokenResponse:
    """Response schema for token endpoint."""
    access_token: str
    token_type: str = "Bearer"
    expires_in: Optional[int] = None
    refresh_token: Optional[str] = None
    scope: Optional[str] = None


class BearerAuthBlueprint(SecurityBlueprint):
    """
        Blueprint for Bearer Token/JWT authentication endpoints.
        
        Provides endpoints for token issuance, refresh, revocation,
        and introspection.
        
        Default Endpoints:
            POST /token - Issue access token
            POST /token/refresh - Refresh access token
            POST /token/revoke - Revoke token
            POST /token/introspect - Validate and inspect token
    """
    
    base_path: str = "/auth/token"
    tags: List[str] = ["Authentication", "Bearer", "JWT"]
    
    # JWT Configuration
    jwt_secret: Optional[str] = None
    jwt_algorithm: str = "HS256"
    access_token_expires: int = 3600  # 1 hour
    refresh_token_expires: int = 86400 * 7  # 7 days
    token_store: Optional['TokenStore'] = None
    
    @classmethod
    @SecurityBlueprint.create(
        path="",
        request_schema=TokenRequest,
        response_schema=TokenResponse,
        doc=Doc(
            summary="Issue access token",
            description="Exchange credentials for an access token."
        )
    )
    def token(cls, request: Any) -> dict:
        """Issue a new access token."""
        if not cls.is_endpoint_enabled("token"):
            return cls.format_error(
                AuthError("endpoint_disabled"),
                status_code=404
            )
        
        body = request.json()
        grant_type = body.get("grant_type")
        
        if grant_type == "password":
            return cls._handle_password_grant(body)
        elif grant_type == "refresh_token":
            return cls._handle_refresh_grant(body)
        elif grant_type == "client_credentials":
            return cls._handle_client_credentials_grant(body)
        else:
            return cls.format_error(
                AuthError("unsupported_grant_type", f"Grant type '{grant_type}' not supported")
            )
    
    @classmethod
    @SecurityBlueprint.create(
        leaf="refresh",
        doc=Doc(
            summary="Refresh access token",
            description="Exchange a refresh token for a new access token."
        )
    )
    def refresh(cls, request: Any) -> dict:
        """Refresh an access token using a refresh token."""
        if not cls.is_endpoint_enabled("refresh"):
            return cls.format_error(AuthError("endpoint_disabled"), status_code=404)
        
        body = request.json()
        refresh_token = body.get("refresh_token")
        
        if not refresh_token:
            return cls.format_error(
                AuthError("invalid_request", "Refresh token required")
            )
        
        # Validate refresh token and issue new access token
        # Implementation details...
        pass
    
    @classmethod
    @SecurityBlueprint.create(
        leaf="revoke",
        doc=Doc(
            summary="Revoke token",
            description="Revoke an access or refresh token."
        )
    )
    def revoke(cls, request: Any) -> dict:
        """Revoke a token."""
        if not cls.is_endpoint_enabled("revoke"):
            return cls.format_error(AuthError("endpoint_disabled"), status_code=404)
        
        body = request.json()
        token = body.get("token")
        
        if cls.token_store:
            cls.token_store.revoke_token(token)
        
        return {"status": 200, "body": {}}
    
    @classmethod
    @SecurityBlueprint.create(
        leaf="introspect",
        doc=Doc(
            summary="Introspect token",
            description="Validate and return information about a token."
        )
    )
    def introspect(cls, request: Any) -> dict:
        """Introspect a token to check validity and get claims."""
        if not cls.is_endpoint_enabled("introspect"):
            return cls.format_error(AuthError("endpoint_disabled"), status_code=404)
        
        body = request.json()
        token = body.get("token")
        
        # Validate token and return claims
        # Implementation details...
        pass
```


### API Key Blueprint

```python
@dataclass
class APIKeyCreateRequest:
    """Request schema for API key creation."""
    name: str
    scopes: Optional[List[str]] = None
    expires_in: Optional[int] = None


@dataclass
class APIKeyResponse:
    """Response schema for API key operations."""
    key_id: str
    name: str
    key: Optional[str] = None  # Only returned on creation
    scopes: List[str] = None
    created_at: str = None
    expires_at: Optional[str] = None


class APIKeyBlueprint(SecurityBlueprint):
    """
        Blueprint for API Key management endpoints.
        
        Provides endpoints for generating, listing, and revoking API keys.
        
        Default Endpoints:
            POST /keys - Generate new API key
            GET /keys - List active API keys
            GET /keys/{key_id} - Get key details
            DELETE /keys/{key_id} - Revoke API key
    """
    
    base_path: str = "/auth/keys"
    tags: List[str] = ["Authentication", "API Keys"]
    
    key_store: Optional['APIKeyStore'] = None
    default_expiration: Optional[int] = None  # Seconds, None = no expiration
    
    @classmethod
    @SecurityBlueprint.create(
        path="",
        request_schema=APIKeyCreateRequest,
        response_schema=APIKeyResponse,
        doc=Doc(
            summary="Generate API key",
            description="Create a new API key. The key value is only returned once."
        )
    )
    def create_key(cls, request: Any) -> dict:
        """Generate a new API key."""
        if not cls.is_endpoint_enabled("create"):
            return cls.format_error(AuthError("endpoint_disabled"), status_code=404)
        
        body = request.json()
        # Generate and store key
        # Return key value only on creation
        pass
    
    @classmethod
    @SecurityBlueprint.read(
        path="",
        response_schema=List[APIKeyResponse],
        doc=Doc(
            summary="List API keys",
            description="List all active API keys for the authenticated user."
        )
    )
    def list_keys(cls, request: Any) -> dict:
        """List all active API keys."""
        if not cls.is_endpoint_enabled("list"):
            return cls.format_error(AuthError("endpoint_disabled"), status_code=404)
        
        # Return list of keys (without key values)
        pass
    
    @classmethod
    @SecurityBlueprint.read(
        path="{key_id}",
        response_schema=APIKeyResponse,
        doc=Doc(
            summary="Get API key details",
            description="Retrieve details about a specific API key."
        )
    )
    def get_key(cls, request: Any, key_id: str) -> dict:
        """Get details for a specific API key."""
        if not cls.is_endpoint_enabled("get"):
            return cls.format_error(AuthError("endpoint_disabled"), status_code=404)
        
        # Return key details (without key value)
        pass
    
    @classmethod
    @SecurityBlueprint.delete(
        path="{key_id}",
        doc=Doc(
            summary="Revoke API key",
            description="Revoke an API key, making it immediately invalid."
        )
    )
    def revoke_key(cls, request: Any, key_id: str) -> dict:
        """Revoke an API key."""
        if not cls.is_endpoint_enabled("revoke"):
            return cls.format_error(AuthError("endpoint_disabled"), status_code=404)
        
        # Revoke key
        pass
```

### Session Authentication Blueprint

```python
@dataclass
class SessionLoginRequest:
    """Request schema for session login."""
    username: str
    password: str
    remember_me: bool = False


@dataclass
class SessionInfo:
    """Response schema for session info."""
    session_id: str
    principal_id: str
    created_at: str
    expires_at: Optional[str] = None
    last_accessed: str = None


class SessionAuthBlueprint(SecurityBlueprint):
    """
        Blueprint for session-based authentication endpoints.
        
        Provides endpoints for cookie-based session management.
        
        Default Endpoints:
            POST /session/login - Create session
            POST /session/logout - Destroy session
            GET /session - Get session info
    """
    
    base_path: str = "/auth/session"
    tags: List[str] = ["Authentication", "Session"]
    
    session_store: Optional['SessionStore'] = None
    session_duration: int = 3600  # 1 hour
    remember_me_duration: int = 86400 * 30  # 30 days
    cookie_name: str = "session_id"
    cookie_secure: bool = True
    cookie_httponly: bool = True
    cookie_samesite: str = "Lax"
    
    @classmethod
    @SecurityBlueprint.create(
        leaf="login",
        request_schema=SessionLoginRequest,
        response_schema=SessionInfo,
        doc=Doc(
            summary="Login and create session",
            description="Authenticate and create a new session with cookie."
        )
    )
    def login(cls, request: Any) -> dict:
        """Create a new session."""
        if not cls.is_endpoint_enabled("login"):
            return cls.format_error(AuthError("endpoint_disabled"), status_code=404)
        
        # Validate credentials, create session, set cookie
        pass
    
    @classmethod
    @SecurityBlueprint.create(
        leaf="logout",
        doc=Doc(
            summary="Logout and destroy session",
            description="Invalidate the current session and clear cookie."
        )
    )
    def logout(cls, request: Any) -> dict:
        """Destroy the current session."""
        if not cls.is_endpoint_enabled("logout"):
            return cls.format_error(AuthError("endpoint_disabled"), status_code=404)
        
        # Invalidate session, clear cookie
        pass
    
    @classmethod
    @SecurityBlueprint.read(
        path="",
        response_schema=SessionInfo,
        doc=Doc(
            summary="Get session info",
            description="Retrieve information about the current session."
        )
    )
    def info(cls, request: Any) -> dict:
        """Get current session information."""
        if not cls.is_endpoint_enabled("info"):
            return cls.format_error(AuthError("endpoint_disabled"), status_code=404)
        
        # Return session info
        pass
```

### OAuth 2.0 Blueprint

```python
@dataclass
class OAuth2AuthorizeRequest:
    """Query parameters for authorization endpoint."""
    response_type: str
    client_id: str
    redirect_uri: str
    scope: Optional[str] = None
    state: Optional[str] = None
    code_challenge: Optional[str] = None
    code_challenge_method: Optional[str] = None


@dataclass
class OAuth2TokenRequest:
    """Request schema for token endpoint."""
    grant_type: str
    code: Optional[str] = None
    redirect_uri: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    code_verifier: Optional[str] = None
    refresh_token: Optional[str] = None
    scope: Optional[str] = None


class OAuth2Blueprint(SecurityBlueprint):
    """
        Blueprint for OAuth 2.0 authorization server endpoints.
        
        Provides endpoints for OAuth 2.0 authorization flows.
        
        Default Endpoints:
            GET /oauth/authorize - Authorization endpoint
            POST /oauth/token - Token endpoint
            GET /oauth/callback - Callback handler
            POST /oauth/revoke - Token revocation
    """
    
    base_path: str = "/oauth"
    tags: List[str] = ["Authentication", "OAuth2"]
    
    # OAuth2 Configuration
    client_store: Optional['OAuth2ClientStore'] = None
    authorization_code_store: Optional['AuthorizationCodeStore'] = None
    token_store: Optional['TokenStore'] = None
    supported_grant_types: List[str] = ["authorization_code", "client_credentials", "refresh_token"]
    supported_response_types: List[str] = ["code"]
    require_pkce: bool = False
    
    @classmethod
    @SecurityBlueprint.read(
        leaf="authorize",
        doc=Doc(
            summary="Authorization endpoint",
            description="OAuth 2.0 authorization endpoint for initiating auth flows."
        )
    )
    def authorize(cls, request: Any) -> dict:
        """Handle authorization request."""
        if not cls.is_endpoint_enabled("authorize"):
            return cls.format_error(AuthError("endpoint_disabled"), status_code=404)
        
        # Validate client, redirect_uri, response_type
        # Generate authorization code
        # Redirect to redirect_uri with code and state
        pass
    
    @classmethod
    @SecurityBlueprint.create(
        leaf="token",
        request_schema=OAuth2TokenRequest,
        response_schema=TokenResponse,
        doc=Doc(
            summary="Token endpoint",
            description="OAuth 2.0 token endpoint for exchanging codes/credentials for tokens."
        )
    )
    def token(cls, request: Any) -> dict:
        """Handle token request."""
        if not cls.is_endpoint_enabled("token"):
            return cls.format_error(AuthError("endpoint_disabled"), status_code=404)
        
        body = request.json()
        grant_type = body.get("grant_type")
        
        if grant_type not in cls.supported_grant_types:
            return cls.format_error(
                AuthError("unsupported_grant_type")
            )
        
        # Handle different grant types
        pass
    
    @classmethod
    @SecurityBlueprint.read(
        leaf="callback",
        doc=Doc(
            summary="OAuth callback",
            description="Handle OAuth provider callback with authorization code."
        )
    )
    def callback(cls, request: Any) -> dict:
        """Handle OAuth callback from provider."""
        if not cls.is_endpoint_enabled("callback"):
            return cls.format_error(AuthError("endpoint_disabled"), status_code=404)
        
        # Validate state, exchange code for tokens
        pass
    
    @classmethod
    @SecurityBlueprint.create(
        leaf="revoke",
        doc=Doc(
            summary="Revoke token",
            description="OAuth 2.0 token revocation endpoint."
        )
    )
    def revoke(cls, request: Any) -> dict:
        """Revoke a token."""
        if not cls.is_endpoint_enabled("revoke"):
            return cls.format_error(AuthError("endpoint_disabled"), status_code=404)
        
        # Revoke token
        pass
```


### OpenID Connect Blueprint

```python
@dataclass
class OIDCDiscovery:
    """OpenID Connect discovery document."""
    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    userinfo_endpoint: str
    jwks_uri: str
    response_types_supported: List[str]
    subject_types_supported: List[str]
    id_token_signing_alg_values_supported: List[str]
    scopes_supported: List[str]
    claims_supported: List[str]


@dataclass
class UserInfo:
    """UserInfo response schema."""
    sub: str
    name: Optional[str] = None
    email: Optional[str] = None
    email_verified: Optional[bool] = None
    picture: Optional[str] = None


class OIDCBlueprint(OAuth2Blueprint):
    """
        Blueprint for OpenID Connect provider endpoints.
        
        Extends OAuth2Blueprint with OIDC-specific functionality.
        
        Default Endpoints (in addition to OAuth2):
            GET /.well-known/openid-configuration - Discovery
            GET /userinfo - UserInfo endpoint
            GET /.well-known/jwks.json - JSON Web Key Set
    """
    
    base_path: str = "/oidc"
    tags: List[str] = ["Authentication", "OIDC", "OAuth2"]
    
    # OIDC Configuration
    issuer: str = None
    jwks: Optional[dict] = None
    supported_scopes: List[str] = ["openid", "profile", "email"]
    supported_claims: List[str] = ["sub", "name", "email", "email_verified"]
    id_token_lifetime: int = 3600
    
    @classmethod
    @SecurityBlueprint.read(
        path="/.well-known/openid-configuration",
        absolute=True,
        response_schema=OIDCDiscovery,
        doc=Doc(
            summary="OpenID Connect Discovery",
            description="Returns the OpenID Connect discovery document."
        )
    )
    def discovery(cls, request: Any) -> dict:
        """Return OIDC discovery document."""
        if not cls.is_endpoint_enabled("discovery"):
            return cls.format_error(AuthError("endpoint_disabled"), status_code=404)
        
        base_url = cls._get_base_url(request)
        
        discovery = OIDCDiscovery(
            issuer=cls.issuer or base_url,
            authorization_endpoint=f"{base_url}{cls.base_path}/authorize",
            token_endpoint=f"{base_url}{cls.base_path}/token",
            userinfo_endpoint=f"{base_url}{cls.base_path}/userinfo",
            jwks_uri=f"{base_url}/.well-known/jwks.json",
            response_types_supported=cls.supported_response_types,
            subject_types_supported=["public"],
            id_token_signing_alg_values_supported=["RS256"],
            scopes_supported=cls.supported_scopes,
            claims_supported=cls.supported_claims
        )
        
        return {"status": 200, "body": discovery.__dict__}
    
    @classmethod
    @SecurityBlueprint.read(
        leaf="userinfo",
        response_schema=UserInfo,
        doc=Doc(
            summary="UserInfo endpoint",
            description="Returns claims about the authenticated user."
        )
    )
    def userinfo(cls, request: Any) -> dict:
        """Return user information for authenticated user."""
        if not cls.is_endpoint_enabled("userinfo"):
            return cls.format_error(AuthError("endpoint_disabled"), status_code=404)
        
        # Get authenticated user from context
        # Return user claims
        pass
    
    @classmethod
    @SecurityBlueprint.read(
        path="/.well-known/jwks.json",
        absolute=True,
        doc=Doc(
            summary="JSON Web Key Set",
            description="Returns the public keys for verifying ID tokens."
        )
    )
    def jwks_endpoint(cls, request: Any) -> dict:
        """Return JWKS for token verification."""
        if not cls.is_endpoint_enabled("jwks"):
            return cls.format_error(AuthError("endpoint_disabled"), status_code=404)
        
        return {"status": 200, "body": cls.jwks or {"keys": []}}
```

## Data Models

### Blueprint Configuration

```python
@dataclass
class BlueprintConfig:
    """Configuration for authentication blueprints."""
    base_path: str
    enabled_endpoints: set
    rate_limit: Optional[RateLimit] = None
    access_policy: Optional[AccessPolicy] = None
    cors_origins: Optional[List[str]] = None
```

### Error Codes

Standard OAuth 2.0 error codes used across blueprints:

| Error Code | Description |
|------------|-------------|
| invalid_request | Missing or invalid parameter |
| invalid_client | Client authentication failed |
| invalid_grant | Invalid authorization code or refresh token |
| unauthorized_client | Client not authorized for grant type |
| unsupported_grant_type | Grant type not supported |
| invalid_scope | Invalid or unknown scope |
| access_denied | Resource owner denied request |
| server_error | Internal server error |



## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Blueprint Endpoint Registration

*For any* authentication blueprint class with a configured base_path, when registered with a router, all default endpoints SHALL be registered at paths relative to the base_path.

**Validates: Requirements 2.1, 3.1, 3.2, 3.3, 3.8, 4.1, 4.2, 4.3, 4.4, 5.1, 5.2, 5.3, 6.1, 6.2, 6.3, 6.7, 7.2, 7.3, 7.4**

### Property 2: Valid Credentials Produce Success Response

*For any* authentication blueprint and valid credentials, the login/token endpoint SHALL return a success response with authentication data (token or context).

**Validates: Requirements 2.2, 3.4**

### Property 3: Invalid Credentials Produce 401

*For any* authentication blueprint and invalid credentials, the login/token endpoint SHALL return a 401 status response.

**Validates: Requirements 2.3**

### Property 4: Authenticator Configuration

*For any* Security_Blueprint subclass, setting the auth_system attribute SHALL cause that authentication system to be used for credential validation.

**Validates: Requirements 1.2, 1.5, 2.4**

### Property 5: Pre/Post Authentication Hooks

*For any* authentication request processed by a Security_Blueprint, the pre_authenticate hook SHALL be called before validation and post_authenticate SHALL be called after successful validation.

**Validates: Requirements 1.3**

### Property 6: Error Response Format Consistency

*For any* authentication failure across all blueprint types, the error response SHALL contain "error" field and optionally "error_description" per RFC 6749 format.

**Validates: Requirements 1.4, 1.6, 10.1**

### Property 7: Path Customization

*For any* Security_Blueprint subclass with a custom base_path, all registered endpoints SHALL have paths prefixed with that base_path.

**Validates: Requirements 2.5, 8.2**

### Property 8: Endpoint Enable/Disable

*For any* Security_Blueprint with enabled_endpoints configured, only endpoints in that set SHALL respond to requests; disabled endpoints SHALL return 404.

**Validates: Requirements 2.6, 8.6**

### Property 9: Token Expiration Configuration

*For any* Bearer_Auth_Blueprint with configured expiration times, issued tokens SHALL have exp claims matching the configuration.

**Validates: Requirements 3.5**

### Property 10: JWT Algorithm Configuration

*For any* Bearer_Auth_Blueprint with configured signing algorithm, issued JWTs SHALL be signed with that algorithm and verifiable with the configured secret/key.

**Validates: Requirements 3.6**

### Property 11: Refresh Token Flow

*For any* valid refresh token submitted to the refresh endpoint, a new access token SHALL be issued with fresh expiration.

**Validates: Requirements 3.7**

### Property 12: API Key Single Exposure

*For any* API key generated by API_Key_Blueprint, the raw key value SHALL appear only in the creation response and never in subsequent list or get responses.

**Validates: Requirements 4.5**

### Property 13: Session Cookie Security

*For any* successful login via Session_Auth_Blueprint, the response SHALL set a cookie with HttpOnly, Secure (when configured), and SameSite attributes.

**Validates: Requirements 5.4**

### Property 14: Session Invalidation

*For any* logout request to Session_Auth_Blueprint, the session SHALL be removed from the store and the cookie SHALL be cleared.

**Validates: Requirements 5.5**

### Property 15: OAuth2 State Validation

*For any* OAuth2 authorization callback, the state parameter SHALL be validated against the original request, and mismatched states SHALL result in an error.

**Validates: Requirements 6.4**

### Property 16: PKCE Verification

*For any* OAuth2 token request with PKCE, the code_verifier SHALL be validated against the stored code_challenge using the specified method.

**Validates: Requirements 6.6**

### Property 17: OAuth2 Error Redirect

*For any* failed OAuth2 authorization request, the response SHALL redirect to the redirect_uri with error and error_description query parameters.

**Validates: Requirements 6.8**

### Property 18: OIDC ID Token Claims

*For any* OIDC token response, the id_token SHALL contain at minimum the sub, iss, aud, exp, and iat claims.

**Validates: Requirements 7.5**

### Property 19: Method Override Behavior

*For any* Security_Blueprint subclass that overrides a default handler method, requests to that endpoint SHALL invoke the overridden implementation.

**Validates: Requirements 8.1, 8.5**

### Property 20: Custom Endpoint Addition

*For any* Security_Blueprint subclass with additional endpoints defined via attach_at, those endpoints SHALL be registered alongside default endpoints.

**Validates: Requirements 8.3**

### Property 21: Blueprint Router Integration

*For any* Security_Blueprint registered with a Router, all enabled endpoints SHALL be accessible via the router's request handling.

**Validates: Requirements 9.1, 9.2, 9.6**

### Property 22: Access Policy Application

*For any* Security_Blueprint with configured access_policy, that policy SHALL be applied to all blueprint endpoints.

**Validates: Requirements 9.4**

### Property 23: Rate Limiting Application

*For any* Security_Blueprint with configured rate_limit, requests exceeding the limit SHALL receive 429 responses.

**Validates: Requirements 9.5, 10.4**

### Property 24: Error Response Sanitization

*For any* error response from a Security_Blueprint, the response body SHALL NOT contain credentials, tokens, secrets, or stack traces.

**Validates: Requirements 10.2, 10.5**

### Property 25: CORS Header Configuration

*For any* Security_Blueprint with configured cors_origins, responses SHALL include appropriate CORS headers for those origins.

**Validates: Requirements 10.6**

## Error Handling

### Error Response Structure

All authentication blueprints return errors in RFC 6749 format:

```python
{
    "error": "error_code",
    "error_description": "Human-readable description"
}
```

### HTTP Status Codes

| Status | Usage |
|--------|-------|
| 200 | Successful authentication |
| 302 | OAuth redirect |
| 400 | Invalid request parameters |
| 401 | Authentication failed |
| 403 | Forbidden (valid auth, insufficient permissions) |
| 404 | Endpoint disabled |
| 429 | Rate limit exceeded |
| 500 | Internal server error |

## Testing Strategy

### Dual Testing Approach

- **Unit tests**: Verify specific endpoint behaviors and edge cases
- **Property tests**: Verify universal properties across all inputs

### Property-Based Testing Configuration

- **Framework**: testbase framework with property test patterns
- **Minimum iterations**: 100 per property test
- **Tag format**: `Feature: authentication-blueprints, Property {number}: {property_text}`

### Test Categories

1. **Endpoint Registration Tests**
   - Verify all blueprints register expected endpoints
   - Verify path customization works correctly
   - Verify endpoint enable/disable functionality

2. **Authentication Flow Tests**
   - Valid credential handling
   - Invalid credential handling
   - Token issuance and validation

3. **Configuration Tests**
   - Authenticator configuration
   - Expiration configuration
   - Algorithm configuration

4. **Integration Tests**
   - Router integration
   - Registry integration
   - Middleware integration

5. **Security Tests**
   - Error response sanitization
   - Rate limiting
   - CORS handling
