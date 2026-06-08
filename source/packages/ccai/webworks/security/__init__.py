"""
.. module:: security
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Package containing access policy and security infrastructure for the ccai webworks framework.

.. moduleauthor:: Code Craft AI LLC

This package provides a comprehensive security framework for web applications including:

- AccessPolicy for declarative security constraints (roles, scopes, authentication)
- Security_Context for authenticated user identity and permissions
- Authentication providers (JWT, session, API key) with pluggable architecture
- Authorization engine for centralized access decisions
- Audit logging for compliance and forensics
- Security middleware for request-level enforcement
- Policy factories and decorators for convenient security patterns
- Security error classes for standardized error responses

The system implements a default-deny model where all endpoints require
explicit authorization unless configured otherwise.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


# Core data models
# These will be populated as subsequent tasks implement the modules.

from ccai.webworks.security.securitycontext import SecurityContext
from ccai.webworks.security.accesspolicy import AccessPolicy

# Authentication
from ccai.webworks.security.authenticationprovider import (
    AuthenticationProvider,
    JWTAuthProvider,
    SessionAuthProvider,
    APIKeyAuthProvider,
)
from ccai.webworks.security.authenticationmanager import AuthenticationManager

# Authorization
from ccai.webworks.security.authorizationengine import (
    AuthorizationEngine,
    AuthorizationResult,
    AuthorizationRule,
)

# Audit logging
from ccai.webworks.security.auditlogger import (
    AuditLogger,
    AuditEntry,
    AuditLevel,
    AuditDestination,
)

# Policy factories
from ccai.webworks.security.policyfactories import (
    public,
    authenticated,
    roles,
    scopes,
)

# Security decorators
from ccai.webworks.security.decorators import (
    require_auth,
    require_roles,
    require_scopes,
    public_endpoint,
)

# Error classes
from ccai.webworks.security.errors import (
    SecurityError,
    AuthenticationError,
    AuthorizationError,
    PolicyValidationError,
    SecurityCompletenessError,
)

# Policy attachment and inheritance
from ccai.webworks.security.policyattachment import (
    PolicyInheritanceNode,
    validate_policy,
    attach_policy,
    get_attached_policy,
    POLICY_CONSTRAINTS_KEY,
)

# Middleware
from ccai.webworks.security.middleware import SecurityMiddleware
from ccai.webworks.security.middleware import validate_security_completeness

# Password hashing (stdlib-only; werkzeug.security-compatible wire format)
from ccai.webworks.security.passwords import (
    DEFAULT_ITERATIONS,
    DEFAULT_SALT_LENGTH,
    hash_password,
    verify_password,
)


__all__ = [
    # Core data models
    "AccessPolicy",
    "SecurityContext",
    # Authentication
    "AuthenticationProvider",
    "JWTAuthProvider",
    "SessionAuthProvider",
    "APIKeyAuthProvider",
    "AuthenticationManager",
    # Authorization
    "AuthorizationEngine",
    "AuthorizationResult",
    "AuthorizationRule",
    # Audit logging
    "AuditLogger",
    "AuditEntry",
    "AuditLevel",
    "AuditDestination",
    # Policy factories
    "public",
    "authenticated",
    "roles",
    "scopes",
    # Security decorators
    "require_auth",
    "require_roles",
    "require_scopes",
    "public_endpoint",
    # Error classes
    "SecurityError",
    "AuthenticationError",
    "AuthorizationError",
    "PolicyValidationError",
    "SecurityCompletenessError",
    # Policy attachment and inheritance
    "PolicyInheritanceNode",
    "validate_policy",
    "attach_policy",
    "get_attached_policy",
    "POLICY_CONSTRAINTS_KEY",
    # Middleware
    "SecurityMiddleware",
    "validate_security_completeness",
    # Password hashing
    "DEFAULT_ITERATIONS",
    "DEFAULT_SALT_LENGTH",
    "hash_password",
    "verify_password",
]
