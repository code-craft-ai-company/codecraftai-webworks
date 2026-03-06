"""
.. module:: middleware
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Security middleware for authenticating and authorizing incoming
        requests through the security layer.

.. moduleauthor:: Automation Mojo LLC

This module provides the SecurityMiddleware class that processes incoming
requests through the authentication and authorization layers. It also
provides the validate_security_completeness function for startup validation
of endpoint security coverage.

The middleware implements a default-deny model: when an endpoint has no
explicit AccessPolicy and no default policy is configured, access is denied.
When security_audit_mode is enabled, authorization failures are logged as
warnings instead of producing error responses, allowing gradual migration.
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

import logging
from typing import Any, Callable, Dict, List, Optional

from automojo.webworks.security.accesspolicy import AccessPolicy
from automojo.webworks.security.authenticationmanager import AuthenticationManager
from automojo.webworks.security.authorizationengine import AuthorizationEngine
from automojo.webworks.security.auditlogger import AuditLogger
from automojo.webworks.security.errors import (
    AuthenticationError,
    AuthorizationError,
    SecurityCompletenessError,
)
from automojo.webworks.security.policyattachment import (
    get_attached_policy,
    POLICY_CONSTRAINTS_KEY,
)
from automojo.webworks.security.securitycontext import SecurityContext


logger = logging.getLogger(__name__)



# Default deny-all policy used when no default is configured
_DENY_ALL_POLICY = AccessPolicy(require_auth=True)


class SecurityMiddleware:
    """
        Middleware that handles authentication and authorization for
        incoming requests.

        The middleware processes each request through the following steps:

        1. Authenticate the request via Authentication_Manager
        2. Determine the effective policy for the endpoint
        3. Authorize the request via Authorization_Engine
        4. Log security events via Audit_Logger
        5. Call the next handler or return an error response

        When an endpoint has no explicit policy, the configured
        default_policy is used. When no default_policy is configured,
        a deny-all policy (require_auth=True) is applied, enforcing
        the default-deny security model.

        When security_audit_mode is True, authorization failures are
        logged as warnings and the request is allowed to proceed. This
        supports gradual migration to a fully secured application.

        :param auth_manager: The authentication manager for identity verification.
        :param authz_engine: The authorization engine for access decisions.
        :param audit_logger: The audit logger for recording security events.
        :param default_policy: The default policy applied to endpoints without
            an explicit policy. When None, a deny-all policy is used.
        :param security_audit_mode: When True, authorization failures are
            logged as warnings instead of producing error responses.
    """

    def __init__(
        self,
        auth_manager: AuthenticationManager,
        authz_engine: AuthorizationEngine,
        audit_logger: AuditLogger,
        default_policy: Optional[AccessPolicy] = None,
        security_audit_mode: bool = False
    ):
        self._auth_manager = auth_manager
        self._authz_engine = authz_engine
        self._audit_logger = audit_logger
        self._default_policy = default_policy
        self._security_audit_mode = security_audit_mode
        return

    def __call__(self, request: Dict[str, Any], next_handler: Callable) -> Dict[str, Any]:
        """
            Process a request through the security layer.

            Authenticates the request, determines the effective policy,
            authorizes the request, logs events, and either calls the
            next handler or returns an error response.

            The request is expected to be a dictionary (or dict-like object)
            with the following optional keys:

            - ``headers``: dict of HTTP headers
            - ``cookies``: dict of cookies
            - ``query_params``: dict of query parameters
            - ``path``: the request path string
            - ``constraints``: dict containing endpoint constraints
                (including any attached access_policy)

            :param request: The incoming request dictionary.
            :param next_handler: The next handler callable to invoke on success.

            :returns: A response dictionary with at minimum a ``status_code`` key.
        """
        # Step 1: Authenticate the request
        security_context = self._auth_manager.authenticate(request)

        is_authenticated = security_context.is_authenticated
        provider_name = security_context.provider if security_context.provider is not None else "none"

        # Extract request metadata for logging
        request_path = request.get("path", "unknown")
        request_headers = request.get("headers", {})
        ip_address = request_headers.get("x-forwarded-for", None)
        user_agent = request_headers.get("user-agent", None)

        # Log the authentication attempt
        self._audit_logger.log_authentication(
            context=security_context,
            provider=provider_name,
            success=is_authenticated,
            endpoint=request_path,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # Step 2: Get the effective policy for the endpoint
        constraints = request.get("constraints", {})
        effective_policy = self.get_policy_for_endpoint(constraints)

        # Step 3: Authorize the request
        authz_result = self._authz_engine.evaluate(effective_policy, security_context)

        # Log the authorization decision
        self._audit_logger.log_authorization(
            context=security_context,
            policy=effective_policy,
            allowed=authz_result.allowed,
            reason=authz_result.reason,
            endpoint=request_path,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # Step 4: Handle authorization result
        if authz_result.allowed is not True:
            # In audit mode, log a warning and allow the request through
            if self._security_audit_mode is True:
                logger.warning(
                    "Security audit mode: authorization failure for %s "
                    "by user %s - reason: %s (request allowed to proceed)",
                    request_path,
                    security_context.user_id,
                    authz_result.reason,
                )
            else:
                # Determine the appropriate error response
                if is_authenticated is not True and effective_policy.require_auth is True:
                    response = {
                        "status_code": 401,
                        "body": {
                            "error": "AUTHENTICATION_REQUIRED",
                            "message": "Authentication required",
                        },
                        "headers": {
                            "WWW-Authenticate": "Bearer",
                        },
                    }
                    return response

                response = {
                    "status_code": 403,
                    "body": {
                        "error": "ACCESS_DENIED",
                        "message": "Access denied",
                    },
                }
                return response

        # Step 5: Call the next handler
        response = next_handler(request)

        return response

    def get_policy_for_endpoint(
        self,
        constraints: Dict[str, Any]
    ) -> AccessPolicy:
        """
            Get the effective policy for an endpoint.

            Checks the endpoint constraints for an attached policy. If no
            policy is found, falls back to the configured default_policy.
            If no default_policy is configured, falls back to a deny-all
            policy (require_auth=True), enforcing the default-deny model.

            :param constraints: The endpoint constraints dictionary that
                may contain an attached access_policy.

            :returns: The effective AccessPolicy for the endpoint.
        """
        attached_policy = get_attached_policy(constraints)

        if attached_policy is not None:
            return attached_policy

        if self._default_policy is not None:
            return self._default_policy

        # Default-deny: no explicit policy and no default configured
        rtnval = _DENY_ALL_POLICY
        return rtnval



def validate_security_completeness(
    endpoints: List[Dict[str, Any]],
    default_policy: Optional[AccessPolicy] = None,
    audit_mode: bool = False
) -> None:
    """
        Validate that all endpoints have security policies at startup.

        Iterates through the provided endpoints and checks whether each
        has an explicit access policy attached in its constraints. Endpoints
        without an explicit policy are considered unprotected unless a
        default_policy is configured.

        When unprotected endpoints are found and no default_policy is
        configured:

        - If audit_mode is False, a SecurityCompletenessError is raised
          listing all unprotected endpoint paths.
        - If audit_mode is True, a warning is logged for each unprotected
          endpoint instead of raising an error.

        :param endpoints: A list of endpoint dictionaries. Each dictionary
            should have a ``path`` key (str) and a ``constraints`` key (dict).
        :param default_policy: The application-level default policy. When
            provided, endpoints without explicit policies are considered
            covered by the default.
        :param audit_mode: When True, log warnings instead of raising errors
            for unprotected endpoints.

        :raises SecurityCompletenessError: When unprotected endpoints are
            found, no default_policy is configured, and audit_mode is False.
    """
    unprotected = []

    for endpoint in endpoints:
        endpoint_path = endpoint.get("path", "unknown")
        constraints = endpoint.get("constraints", {})

        attached_policy = get_attached_policy(constraints)

        if attached_policy is None and default_policy is None:
            unprotected.append(endpoint_path)

    if len(unprotected) > 0:
        if audit_mode is True:
            for path in unprotected:
                logger.warning(
                    "Security completeness warning: endpoint '%s' has no "
                    "explicit security policy and no default policy is configured",
                    path,
                )
        else:
            raise SecurityCompletenessError(unprotected_endpoints=unprotected)

    return
