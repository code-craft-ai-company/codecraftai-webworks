"""
.. module:: middleware
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Security middleware for authenticating and authorizing incoming
        requests through the security layer.

.. moduleauthor:: Code Craft AI LLC

This module provides the SecurityMiddleware class that processes incoming
requests through the authentication and authorization layers. It also
provides the validate_security_completeness function for startup validation
of endpoint security coverage.

The middleware implements a default-deny model: when an endpoint has no
explicit AccessPolicy and no default policy is configured, access is denied.
When security_audit_mode is enabled, authorization failures are logged as
warnings instead of producing error responses, allowing gradual migration.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

import logging
from typing import Any, Awaitable, Callable, Dict, List, Mapping, Optional

from ccai.webworks.security.accesspolicy import AccessPolicy
from ccai.webworks.security.authenticationmanager import AuthenticationManager
from ccai.webworks.security.authorizationengine import AuthorizationEngine
from ccai.webworks.security.auditlogger import AuditLogger
from ccai.webworks.security.errors import SecurityCompletenessError
from ccai.webworks.security.policyattachment import get_attached_policy
from ccai.webworks.security.securitycontext import (
    SECURITY_CONTEXT_SCOPE_KEY,
    SecurityContext,
)


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

        Use in the request pipeline: the middleware is a
        ``(request, call_next)`` middleware over the routing
        :class:`Request` and :class:`Response`. It reads the policy from
        the descriptor of the matched route, so it belongs in the part of
        the pipeline that runs after routing::

            dispatcher.route_pipeline.add(SecurityMiddleware(...))

        The authentication providers read ``request.headers`` and
        ``request.cookies``, which the routing Request provides. The
        resolved :class:`SecurityContext` is stored on the request scope
        under :data:`SECURITY_CONTEXT_SCOPE_KEY`, where handlers and the
        dispatcher's own policy check find it. A refusal is a routing
        ``JSONResponse`` with status 401 or 403. The middleware runs in the
        synchronous pipeline through ``__call__`` and in the asynchronous
        pipeline through ``call_async``.

        A request given as a plain mapping (``path``, ``headers``,
        ``constraints`` keys) is still accepted and answered with a
        response dictionary, for callers that drive the middleware
        outside the routing pipeline.

        :param auth_manager: The authentication manager for identity verification.
        :param authz_engine: The authorization engine for access decisions.
        :param audit_logger: The audit logger for recording security events.
        :param default_policy: The default policy applied to endpoints without
            an explicit policy. When None, a deny-all policy is used.
        :param security_audit_mode: When True, authorization failures are
            logged as warnings instead of producing error responses.
    """

    name: str = "security"

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

    def __call__(self, request: Any, next_handler: Callable) -> Any:
        """
            Process a request through the security layer.

            Authenticates the request, determines the effective policy,
            authorizes the request, logs events, and either calls the
            next handler or returns an error response.

            The request is a routing :class:`Request`, or a mapping with
            the following optional keys:

            - ``headers``: dict of HTTP headers
            - ``cookies``: dict of cookies
            - ``query_params``: dict of query parameters
            - ``path``: the request path string
            - ``constraints``: dict containing endpoint constraints
                (including any attached access_policy)

            :param request: The incoming request.
            :param next_handler: The next handler callable to invoke on success.

            :returns: The response of the next handler, or a 401/403
                response: a routing ``JSONResponse`` for a routing
                Request, a dictionary with a ``status_code`` key for a
                mapping request.
        """
        # Step 1: Authenticate the request
        security_context = self._auth_manager.authenticate(request)

        denial = self._authorize(request, security_context)

        if denial is not None:
            return denial

        # Step 5: Call the next handler
        response = next_handler(request)

        return response

    async def call_async(
        self,
        request: Any,
        next_handler: Callable[[Any], Awaitable[Any]]
    ) -> Any:
        """
            Process a request through the security layer in the
            asynchronous pipeline. Behaves as :meth:`__call__`, using the
            asynchronous form of the authentication providers.

            :param request: The incoming request.
            :param next_handler: The async next handler callable.

            :returns: The response of the next handler, or a 401/403 response.
        """
        # Step 1: Authenticate the request
        security_context = await self._auth_manager.authenticate_async(request)

        denial = self._authorize(request, security_context)

        if denial is not None:
            return denial

        # Step 5: Call the next handler
        response = await next_handler(request)

        return response

    def _authorize(self, request: Any, security_context: SecurityContext) -> Optional[Any]:
        """
            Publish the security context on the request, audit the
            authentication, and decide whether the request may proceed.

            :param request: The incoming request.
            :param security_context: The context authentication produced.

            :returns: None when the request may proceed, otherwise the
                401 or 403 response to return.
        """
        is_authenticated = security_context.is_authenticated
        provider_name = security_context.provider if security_context.provider is not None else "none"

        self._publish_security_context(request, security_context)

        # Extract request metadata for logging
        request_path = self._get_request_value(request, "path", "unknown")
        ip_address = self._get_request_header(request, "x-forwarded-for")
        user_agent = self._get_request_header(request, "user-agent")

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
        constraints = self._get_request_constraints(request)
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

        rtnval: Optional[Any] = None

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
            elif is_authenticated is not True and effective_policy.require_auth is True:
                rtnval = self._build_denial(
                    request,
                    status_code=401,
                    error="AUTHENTICATION_REQUIRED",
                    message="Authentication required",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            else:
                rtnval = self._build_denial(
                    request,
                    status_code=403,
                    error="ACCESS_DENIED",
                    message="Access denied",
                    headers=None
                )

        return rtnval

    def _get_request_value(self, request: Any, name: str, default: Any) -> Any:
        """
            Read a value of the request, whichever shape the request has.

            :param request: A routing Request or a mapping.
            :param name: The attribute or key to read.
            :param default: Value returned when it is absent.

            :returns: The value, or the default.
        """
        if isinstance(request, Mapping):
            rtnval = request.get(name, default)
        else:
            rtnval = getattr(request, name, default)

        return rtnval

    def _get_request_header(self, request: Any, header_name: str) -> Optional[str]:
        """
            Read a request header, whichever shape the request has.

            :param request: A routing Request or a mapping.
            :param header_name: The header name.

            :returns: The header value, or None when it is absent.
        """
        headers = self._get_request_value(request, "headers", None)

        rtnval = None
        if headers is not None:
            rtnval = headers.get(header_name, None)

        return rtnval

    def _get_request_constraints(self, request: Any) -> Any:
        """
            Find the constraints of the endpoint a request is for.

            A routing Request carries them on the descriptor of the route
            the dispatcher matched (``request.middleware_context``). A
            mapping request carries them under its ``constraints`` key.

            :param request: A routing Request or a mapping.

            :returns: The endpoint constraints (a dict or an
                EndpointConstraints object), or an empty dict when the
                request is not bound to an endpoint.
        """
        rtnval: Any = {}

        if isinstance(request, Mapping):
            rtnval = request.get("constraints", {})
        else:
            middleware_context = getattr(request, "middleware_context", None)
            descriptor = getattr(middleware_context, "endpoint_descriptor", None)

            if descriptor is not None:
                rtnval = getattr(descriptor, "constraints", {})

        return rtnval

    def _publish_security_context(self, request: Any, security_context: SecurityContext) -> None:
        """
            Store the security context where the rest of the request
            processing finds it: on the scope of a routing Request, or in
            a mapping request itself.

            :param request: A routing Request or a mapping.
            :param security_context: The context to publish.
        """
        if isinstance(request, dict):
            request[SECURITY_CONTEXT_SCOPE_KEY] = security_context
        else:
            scope = getattr(request, "scope", None)
            if isinstance(scope, dict):
                scope[SECURITY_CONTEXT_SCOPE_KEY] = security_context

        return

    def _build_denial(
        self,
        request: Any,
        status_code: int,
        error: str,
        message: str,
        headers: Optional[Dict[str, str]]
    ) -> Any:
        """
            Build the response that refuses a request.

            :param request: The refused request; its shape decides the
                shape of the response.
            :param status_code: 401 or 403.
            :param error: Machine-readable error code.
            :param message: Human-readable message.
            :param headers: Optional response headers.

            :returns: A routing ``JSONResponse`` for a routing Request, a
                response dictionary for a mapping request.
        """
        body = {
            "error": error,
            "message": message,
        }

        if isinstance(request, Mapping):
            rtnval: Any = {
                "status_code": status_code,
                "body": body,
            }
            if headers is not None:
                rtnval["headers"] = dict(headers)
        else:
            # Imported here: the routing package imports this package
            # while it is itself being imported.
            from ccai.webworks.routing.response import JSONResponse

            rtnval = JSONResponse(body, status_code=status_code, headers=headers)

        return rtnval

    def get_policy_for_endpoint(
        self,
        constraints: Any
    ) -> AccessPolicy:
        """
            Get the effective policy for an endpoint.

            Checks the endpoint constraints for an attached policy. If no
            policy is found, falls back to the configured default_policy.
            If no default_policy is configured, falls back to a deny-all
            policy (require_auth=True), enforcing the default-deny model.

            :param constraints: The endpoint constraints that may contain
                an attached access_policy: a constraints dictionary, an
                ``EndpointConstraints`` object, or an ``EndpointDescriptor``.

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
    endpoints: List[Any],
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

        :param endpoints: A list of endpoints: ``EndpointDescriptor``
            objects (for example ``registry.collect()``), or dictionaries
            with a ``path`` key (str) and a ``constraints`` key (dict).
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
        if isinstance(endpoint, Mapping):
            endpoint_path = endpoint.get("path", "unknown")
            constraints = endpoint.get("constraints", {})
        else:
            endpoint_path = getattr(endpoint, "path", None)
            if endpoint_path is None:
                leaf = getattr(endpoint, "leaf", None)
                endpoint_path = f"/{leaf}" if leaf is not None else "unknown"
            constraints = getattr(endpoint, "constraints", {})

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
