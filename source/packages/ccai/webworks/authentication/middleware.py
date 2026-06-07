"""
.. module:: middleware
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: ASGI middleware for authentication.

.. moduleauthor:: Code Craft AI LLC

This module provides the AuthenticationMiddleware class which integrates
authentication into the ASGI request pipeline. It intercepts requests
before they reach endpoint handlers and attaches authentication context
to the request scope.

The middleware also integrates with the AccessPolicy system to enforce
role-based and permission-based access control.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


import json
import logging
import re
from typing import Any, Awaitable, Callable, Dict, List, Optional, Pattern, Set, Union

from ccai.webworks.authentication.core import (
    AuthenticationContext,
    AuthenticationResult,
    AuthenticationStatus
)
from ccai.webworks.authentication.system import AuthenticationSystem
from ccai.webworks.endpoints.accesspolicy import AccessPolicy


# Type aliases for ASGI callables
ReceiveCallable = Callable[[], Awaitable[Dict[str, Any]]]
SendCallable = Callable[[Dict[str, Any]], Awaitable[None]]
ASGIApplication = Callable[
    [Dict[str, Any], ReceiveCallable, SendCallable],
    Awaitable[None]
]


class AuthenticationMiddleware:
    """
        ASGI middleware for authentication.
        
        This middleware intercepts HTTP requests before they reach endpoint
        handlers and performs authentication using the configured
        AuthenticationSystem. Upon successful authentication, it attaches
        the AuthenticationContext to the request scope under the "auth" key.
        
        The middleware supports:
        - Protected paths that require authentication
        - Optional authentication paths where identity is available if present
        - Excluded paths that bypass authentication entirely
        - Pattern-based path matching using glob or regex patterns
        - Access policy integration for role-based and permission-based access control
        
        Example usage::
        
            auth_system = AuthenticationSystem()
            auth_system.register(BasicAuthenticator(identity_provider))
            
            middleware = AuthenticationMiddleware(
                app=my_asgi_app,
                auth_system=auth_system,
                exclude_paths={"/health", "/public"},
                optional_paths={"/api/optional"}
            )
            
            # Use middleware as ASGI application
            await middleware(scope, receive, send)
        
        Access policy integration::
        
            # Define path-specific access policies
            path_policies = {
                "/admin": AccessPolicy(roles=["admin"]),
                "/api/users": AccessPolicy(roles=["admin", "user"], scopes=["read:users"])
            }
            
            middleware = AuthenticationMiddleware(
                app=my_asgi_app,
                auth_system=auth_system,
                path_policies=path_policies
            )
    """
    
    def __init__(
        self,
        app: ASGIApplication,
        auth_system: AuthenticationSystem,
        exclude_paths: Optional[Set[str]] = None,
        optional_paths: Optional[Set[str]] = None,
        exclude_patterns: Optional[List[Union[str, Pattern]]] = None,
        optional_patterns: Optional[List[Union[str, Pattern]]] = None,
        path_policies: Optional[Dict[str, AccessPolicy]] = None,
        policy_patterns: Optional[List[tuple]] = None,
        default_policy: Optional[AccessPolicy] = None,
        logger: Optional[logging.Logger] = None,
        realm: str = "Restricted"
    ):
        """
            Initialize the AuthenticationMiddleware.
            
            :param app: The ASGI application to wrap.
            :param auth_system: The AuthenticationSystem to use for authentication.
            :param exclude_paths: Set of exact paths to exclude from authentication.
            :param optional_paths: Set of exact paths where authentication is optional.
            :param exclude_patterns: List of patterns (glob or regex) for excluded paths.
            :param optional_patterns: List of patterns (glob or regex) for optional paths.
            :param path_policies: Dict mapping exact paths to AccessPolicy instances.
            :param policy_patterns: List of (pattern, AccessPolicy) tuples for pattern-based policies.
            :param default_policy: Default AccessPolicy for paths without specific policies.
            :param logger: Logger for middleware logging. If None, a default logger is created.
            :param realm: The realm to use in WWW-Authenticate challenges.
        """
        self._app = app
        self._auth_system = auth_system
        self._exclude_paths = exclude_paths or set()
        self._optional_paths = optional_paths or set()
        self._exclude_patterns = self._compile_patterns(exclude_patterns or [])
        self._optional_patterns = self._compile_patterns(optional_patterns or [])
        self._path_policies: Dict[str, AccessPolicy] = path_policies or {}
        self._policy_patterns = self._compile_policy_patterns(policy_patterns or [])
        self._default_policy = default_policy
        self._realm = realm
        
        if logger is None:
            self._logger = logging.getLogger(__name__)
        else:
            self._logger = logger
        
        return
    
    @property
    def app(self) -> ASGIApplication:
        """
            Get the wrapped ASGI application.
            
            :returns: The wrapped ASGI application.
        """
        return self._app
    
    @property
    def auth_system(self) -> AuthenticationSystem:
        """
            Get the authentication system.
            
            :returns: The AuthenticationSystem instance.
        """
        return self._auth_system
    
    @property
    def exclude_paths(self) -> Set[str]:
        """
            Get the set of excluded paths.
            
            :returns: Set of paths excluded from authentication.
        """
        return self._exclude_paths
    
    @property
    def optional_paths(self) -> Set[str]:
        """
            Get the set of optional authentication paths.
            
            :returns: Set of paths where authentication is optional.
        """
        return self._optional_paths
    
    @property
    def path_policies(self) -> Dict[str, AccessPolicy]:
        """
            Get the path-to-policy mapping.
            
            :returns: Dict mapping paths to AccessPolicy instances.
        """
        return self._path_policies
    
    @property
    def default_policy(self) -> Optional[AccessPolicy]:
        """
            Get the default access policy.
            
            :returns: The default AccessPolicy, or None if not set.
        """
        return self._default_policy
    
    @property
    def realm(self) -> str:
        """
            Get the authentication realm.
            
            :returns: The realm string used in WWW-Authenticate challenges.
        """
        return self._realm
    
    def _compile_patterns(
        self,
        patterns: List[Union[str, Pattern]]
    ) -> List[Pattern]:
        """
            Compile string patterns to regex patterns.
            
            Supports glob-style patterns with * and ** wildcards.
            
            :param patterns: List of string patterns or compiled regex patterns.
            
            :returns: List of compiled regex patterns.
        """
        compiled = []
        for pattern in patterns:
            if isinstance(pattern, str):
                # Convert glob-style pattern to regex
                regex_pattern = self._glob_to_regex(pattern)
                compiled.append(re.compile(regex_pattern))
            else:
                # Already a compiled pattern
                compiled.append(pattern)
        return compiled
    
    def _glob_to_regex(self, glob_pattern: str) -> str:
        """
            Convert a glob-style pattern to a regex pattern.
            
            Supports:
            - * matches any characters except /
            - ** matches any characters including /
            - ? matches any single character
            
            :param glob_pattern: The glob pattern to convert.
            
            :returns: The equivalent regex pattern.
        """
        # Escape special regex characters except * and ?
        result = ""
        i = 0
        while i < len(glob_pattern):
            char = glob_pattern[i]
            if char == '*':
                # Check for **
                if i + 1 < len(glob_pattern) and glob_pattern[i + 1] == '*':
                    result += ".*"
                    i += 2
                else:
                    result += "[^/]*"
                    i += 1
            elif char == '?':
                result += "."
                i += 1
            elif char in r'\^$.|+()[]{}':
                result += '\\' + char
                i += 1
            else:
                result += char
                i += 1
        return f"^{result}$"
    
    def _compile_policy_patterns(
        self,
        patterns: List[tuple]
    ) -> List[tuple]:
        """
            Compile policy pattern tuples to (regex, AccessPolicy) tuples.
            
            :param patterns: List of (pattern_string, AccessPolicy) tuples.
            
            :returns: List of (compiled_regex, AccessPolicy) tuples.
        """
        compiled = []
        for pattern, policy in patterns:
            if isinstance(pattern, str):
                regex_pattern = self._glob_to_regex(pattern)
                compiled.append((re.compile(regex_pattern), policy))
            else:
                # Already a compiled pattern
                compiled.append((pattern, policy))
        return compiled
    
    def get_policy_for_path(self, path: str) -> Optional[AccessPolicy]:
        """
            Get the AccessPolicy for a given path.
            
            Checks in order:
            1. Exact path match in path_policies
            2. Pattern match in policy_patterns
            3. Default policy
            
            :param path: The request path.
            
            :returns: The AccessPolicy for the path, or None if no policy applies.
        """
        # Check exact match first
        if path in self._path_policies:
            return self._path_policies[path]
        
        # Check patterns
        for pattern, policy in self._policy_patterns:
            if pattern.match(path):
                return policy
        
        # Return default policy
        return self._default_policy
    
    def check_access_policy(
        self,
        path: str,
        context: Optional[AuthenticationContext]
    ) -> bool:
        """
            Check if the authentication context satisfies the access policy for a path.
            
            :param path: The request path.
            :param context: The AuthenticationContext, or None if not authenticated.
            
            :returns: True if access is allowed, False otherwise.
        """
        policy = self.get_policy_for_path(path)
        
        if policy is None:
            # No policy defined, allow access
            return True
        
        return policy.check_authentication_context(context)
    
    def _is_excluded(self, path: str) -> bool:
        """
            Check if a path is excluded from authentication.
            
            :param path: The request path to check.
            
            :returns: True if the path is excluded, False otherwise.
        """
        # Check exact match
        if path in self._exclude_paths:
            return True
        
        # Check patterns
        for pattern in self._exclude_patterns:
            if pattern.match(path):
                return True
        
        return False
    
    def _is_optional(self, path: str) -> bool:
        """
            Check if authentication is optional for a path.
            
            :param path: The request path to check.
            
            :returns: True if authentication is optional, False otherwise.
        """
        # Check exact match
        if path in self._optional_paths:
            return True
        
        # Check patterns
        for pattern in self._optional_patterns:
            if pattern.match(path):
                return True
        
        return False
    
    async def __call__(
        self,
        scope: Dict[str, Any],
        receive: ReceiveCallable,
        send: SendCallable
    ) -> None:
        """
            ASGI middleware entry point.
            
            Intercepts HTTP requests to perform authentication and access
            policy enforcement before passing to the wrapped application.
            
            :param scope: ASGI scope dictionary.
            :param receive: Async callable to receive messages.
            :param send: Async callable to send messages.
        """
        # Only handle HTTP requests
        if scope.get("type") != "http":
            await self._app(scope, receive, send)
            return
        
        path = scope.get("path", "/")
        
        # Skip authentication for excluded paths
        if self._is_excluded(path):
            self._logger.debug(f"Path '{path}' is excluded from authentication")
            scope["auth"] = None
            await self._app(scope, receive, send)
            return
        
        # Attempt authentication
        result = await self._auth_system.authenticate(scope)
        
        if result.status == AuthenticationStatus.SUCCESS:
            # Attach context to scope
            scope["auth"] = result.context
            self._logger.debug(
                f"Authentication successful for path '{path}' "
                f"with scheme '{result.context.scheme}'"
            )
            
            # Check access policy
            if not self.check_access_policy(path, result.context):
                self._logger.debug(
                    f"Access denied for path '{path}': "
                    f"policy check failed"
                )
                await self._send_forbidden(send)
                return
            
            await self._app(scope, receive, send)
            
        elif result.status == AuthenticationStatus.CHALLENGE:
            if self._is_optional(path):
                # Allow unauthenticated access for optional paths
                scope["auth"] = None
                self._logger.debug(
                    f"Optional authentication for path '{path}', "
                    f"proceeding without context"
                )
                
                # Check access policy for unauthenticated access
                if not self.check_access_policy(path, None):
                    self._logger.debug(
                        f"Access denied for path '{path}': "
                        f"policy check failed for unauthenticated access"
                    )
                    await self._send_challenge(send, result.challenge)
                    return
                
                await self._app(scope, receive, send)
            else:
                # Send challenge response
                self._logger.debug(
                    f"Authentication challenge for path '{path}'"
                )
                await self._send_challenge(send, result.challenge)
                
        elif result.status == AuthenticationStatus.SKIP:
            if self._is_optional(path):
                # No credentials provided but path is optional
                scope["auth"] = None
                self._logger.debug(
                    f"No credentials for optional path '{path}', "
                    f"proceeding without context"
                )
                
                # Check access policy for unauthenticated access
                if not self.check_access_policy(path, None):
                    self._logger.debug(
                        f"Access denied for path '{path}': "
                        f"policy check failed for unauthenticated access"
                    )
                    await self._send_unauthorized(send, result)
                    return
                
                await self._app(scope, receive, send)
            else:
                # No authenticator could handle the request
                self._logger.debug(
                    f"No credentials provided for protected path '{path}'"
                )
                await self._send_unauthorized(send, result)
                
        else:  # FAILURE
            if self._is_optional(path):
                # Authentication failed but path is optional
                scope["auth"] = None
                self._logger.debug(
                    f"Authentication failed for optional path '{path}', "
                    f"proceeding without context"
                )
                
                # Check access policy for unauthenticated access
                if not self.check_access_policy(path, None):
                    self._logger.debug(
                        f"Access denied for path '{path}': "
                        f"policy check failed for unauthenticated access"
                    )
                    await self._send_unauthorized(send, result)
                    return
                
                await self._app(scope, receive, send)
            else:
                # Authentication failed
                self._logger.debug(
                    f"Authentication failed for path '{path}': "
                    f"{result.error_code}"
                )
                await self._send_unauthorized(send, result)
        
        return
    
    async def _send_challenge(
        self,
        send: SendCallable,
        challenge: Optional[str]
    ) -> None:
        """
            Send a 401 response with WWW-Authenticate challenge.
            
            :param send: Async callable to send messages.
            :param challenge: The WWW-Authenticate header value.
        """
        headers = [
            (b"content-type", b"application/json"),
        ]
        
        if challenge:
            headers.append((b"www-authenticate", challenge.encode("utf-8")))
        else:
            # Default challenge if none provided
            headers.append(
                (b"www-authenticate", f'Basic realm="{self._realm}"'.encode("utf-8"))
            )
        
        await send({
            "type": "http.response.start",
            "status": 401,
            "headers": headers
        })
        
        body = {
            "error": "authentication_required",
            "error_description": "Authentication is required to access this resource"
        }
        
        await send({
            "type": "http.response.body",
            "body": json.dumps(body).encode("utf-8")
        })
        
        return
    
    async def _send_unauthorized(
        self,
        send: SendCallable,
        result: AuthenticationResult
    ) -> None:
        """
            Send a 401 Unauthorized response.
            
            :param send: Async callable to send messages.
            :param result: The authentication result with error details.
        """
        headers = [
            (b"content-type", b"application/json"),
        ]
        
        # Add challenge header if available
        if result.challenge:
            headers.append((b"www-authenticate", result.challenge.encode("utf-8")))
        
        await send({
            "type": "http.response.start",
            "status": 401,
            "headers": headers
        })
        
        body = {
            "error": result.error_code or "unauthorized",
            "error_description": result.error_description or "Authentication failed"
        }
        
        await send({
            "type": "http.response.body",
            "body": json.dumps(body).encode("utf-8")
        })
        
        return
    
    async def _send_forbidden(
        self,
        send: SendCallable
    ) -> None:
        """
            Send a 403 Forbidden response.
            
            This is sent when authentication succeeds but the user does not
            have the required roles or permissions to access the resource.
            
            :param send: Async callable to send messages.
        """
        await send({
            "type": "http.response.start",
            "status": 403,
            "headers": [(b"content-type", b"application/json")]
        })
        
        body = {
            "error": "forbidden",
            "error_description": "You do not have permission to access this resource"
        }
        
        await send({
            "type": "http.response.body",
            "body": json.dumps(body).encode("utf-8")
        })
        
        return


def create_authentication_middleware(
    app: ASGIApplication,
    auth_system: AuthenticationSystem,
    exclude_paths: Optional[Set[str]] = None,
    optional_paths: Optional[Set[str]] = None,
    exclude_patterns: Optional[List[Union[str, Pattern]]] = None,
    optional_patterns: Optional[List[Union[str, Pattern]]] = None,
    path_policies: Optional[Dict[str, AccessPolicy]] = None,
    policy_patterns: Optional[List[tuple]] = None,
    default_policy: Optional[AccessPolicy] = None,
    logger: Optional[logging.Logger] = None,
    realm: str = "Restricted"
) -> AuthenticationMiddleware:
    """
        Factory function to create an AuthenticationMiddleware instance.
        
        :param app: The ASGI application to wrap.
        :param auth_system: The AuthenticationSystem to use for authentication.
        :param exclude_paths: Set of exact paths to exclude from authentication.
        :param optional_paths: Set of exact paths where authentication is optional.
        :param exclude_patterns: List of patterns (glob or regex) for excluded paths.
        :param optional_patterns: List of patterns (glob or regex) for optional paths.
        :param path_policies: Dict mapping exact paths to AccessPolicy instances.
        :param policy_patterns: List of (pattern, AccessPolicy) tuples for pattern-based policies.
        :param default_policy: Default AccessPolicy for paths without specific policies.
        :param logger: Logger for middleware logging.
        :param realm: The realm to use in WWW-Authenticate challenges.
        
        :returns: Configured AuthenticationMiddleware instance.
    """
    return AuthenticationMiddleware(
        app=app,
        auth_system=auth_system,
        exclude_paths=exclude_paths,
        optional_paths=optional_paths,
        exclude_patterns=exclude_patterns,
        optional_patterns=optional_patterns,
        path_policies=path_policies,
        policy_patterns=policy_patterns,
        default_policy=default_policy,
        logger=logger,
        realm=realm
    )
