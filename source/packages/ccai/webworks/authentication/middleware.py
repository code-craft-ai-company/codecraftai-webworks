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

Contract with the rest of the framework (kept stable):

* Authenticators receive a :class:`ccai.webworks.routing.request.Request`
  built from the ASGI scope, so headers, cookies and query parameters are
  read the same way an endpoint handler reads them. The raw scope stays
  reachable through ``request.scope``.
* ``scope["auth"]`` is set before the wrapped application is called, for
  ``http`` and ``websocket`` scopes: it holds the
  :class:`AuthenticationContext` when authentication succeeded and ``None``
  when the path is excluded or optional and no identity was established.
  The key is absent for scope types the middleware does not authenticate
  (``lifespan``).
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


import json
import logging
import re
import urllib.parse
from typing import Any, Awaitable, Callable, Dict, List, Optional, Pattern, Set, Tuple, Union

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
        
        WebSocket handshakes are authenticated the same way and are
        closed before they are accepted when authentication or the access
        policy fails. Only scopes that carry no request (``lifespan``) are
        passed through untouched.
        
        The middleware supports:
        - Protected paths that require authentication
        - Optional authentication paths where identity is available if present
        - Excluded paths that bypass authentication entirely
        - Pattern-based path matching using glob or regex patterns
        - Access policy integration for role-based and permission-based access control
        
        Paths are compared in their canonical form, the form the router
        matches (see :func:`ccai.webworks.routing.router.canonicalize_path`):
        ``//admin//users`` is decided, and handed on, as ``/admin/users``.
        A path with a ``.`` segment is answered with a 308 redirect to the
        path without it (a WebSocket handshake is closed instead).
        
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
    
    # Scope types that carry a request the middleware authenticates.
    AUTHENTICATED_SCOPE_TYPES: Tuple[str, ...] = ("http", "websocket")
    
    # WebSocket close code sent when a handshake is refused (1008 is
    # "policy violation"). Closing before accepting makes the server
    # answer the handshake with HTTP 403.
    WEBSOCKET_POLICY_VIOLATION_CODE: int = 1008
    
    # Error codes an authenticator uses to report throttling. They are
    # answered with 429 instead of 401.
    THROTTLED_ERROR_CODES: Tuple[str, ...] = ("rate_limit_exceeded", "account_locked")
    
    # Default cap for the request body buffered on behalf of
    # authenticators that sign the body (1 MiB).
    DEFAULT_MAX_BODY_BYTES: int = 1048576
    
    # Characters left as they are when a path is written into a Location
    # header; everything else is percent-encoded.
    LOCATION_SAFE_CHARS: str = "/:@!$&'()*+,;=-._~"
    
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
        realm: str = "Restricted",
        max_body_bytes: Optional[int] = None
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
            :param max_body_bytes: Largest request body the middleware buffers
                                   when a registered authenticator needs the
                                   body (HMAC signing). Larger requests are
                                   refused with 413. Defaults to 1 MiB.
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
        
        if max_body_bytes is None:
            self._max_body_bytes = self.DEFAULT_MAX_BODY_BYTES
        else:
            self._max_body_bytes = max_body_bytes
        
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
    
    def add_exclude_pattern(self, pattern: Union[str, Pattern]) -> None:
        """
            Exclude every path matching a pattern from authentication.
            
            Use this for anything that is not one exact path: the
            ``exclude_paths`` set is compared by equality, so a glob
            string added to it never matches.
            
            :param pattern: A glob string (``*``, ``**``, ``?``) or a
                            compiled regular expression.
        """
        compiled = self._compile_patterns([pattern])
        self._exclude_patterns.extend(compiled)
        return
    
    def add_optional_pattern(self, pattern: Union[str, Pattern]) -> None:
        """
            Make authentication optional for every path matching a pattern.
            
            :param pattern: A glob string (``*``, ``**``, ``?``) or a
                            compiled regular expression.
        """
        compiled = self._compile_patterns([pattern])
        self._optional_patterns.extend(compiled)
        return
    
    def add_policy_pattern(
        self,
        pattern: Union[str, Pattern],
        policy: AccessPolicy
    ) -> None:
        """
            Apply an access policy to every path matching a pattern.
            
            :param pattern: A glob string (``*``, ``**``, ``?``) or a
                            compiled regular expression.
            :param policy: The :class:`AccessPolicy` for matching paths.
        """
        compiled = self._compile_policy_patterns([(pattern, policy)])
        self._policy_patterns.extend(compiled)
        return
    
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
            
            Intercepts HTTP requests and WebSocket handshakes to perform
            authentication and access policy enforcement before passing
            to the wrapped application.
            
            :param scope: ASGI scope dictionary.
            :param receive: Async callable to receive messages.
            :param send: Async callable to send messages.
        """
        scope_type = scope.get("type")

        # Scopes that carry no request (lifespan) have nothing to authenticate
        if scope_type not in self.AUTHENTICATED_SCOPE_TYPES:
            await self._app(scope, receive, send)
            return

        # Decide on the spelling of the path the router matches, so an
        # exclusion or a policy keyed on '/admin/users' also applies to
        # '//admin/users'. A path with '.' segments is redirected instead.
        scope, redirect_path = self._canonicalize_scope(scope)
        if redirect_path is not None:
            await self._redirect_to_path(scope, send, redirect_path)
            return

        path = scope.get("path", "/")
        
        # Skip authentication for excluded paths
        if self._is_excluded(path):
            self._logger.debug(f"Path '{path}' is excluded from authentication")
            scope["auth"] = None
            await self._app(scope, receive, send)
            return
        
        # Buffer the body when an authenticator signs it, and replay it
        # to the wrapped application afterwards.
        body = b""
        downstream_receive = receive
        if scope_type == "http" and self._auth_system.requires_body:
            body, body_complete = await self._read_body(receive)
            if not body_complete:
                self._logger.debug(
                    f"Request body for path '{path}' exceeds the "
                    f"authentication buffer limit"
                )
                await self._send_payload_too_large(send)
                return
            downstream_receive = self._create_replay_receive(body, receive)
        
        # Authenticators read headers, cookies and query parameters
        # through the framework Request, not the raw ASGI scope.
        request = self._build_request(scope, body)
        
        # Attempt authentication
        result = await self._auth_system.authenticate(request)
        
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
                await self._deny_forbidden(scope, send)
                return
            
            downstream_send = send
            if scope_type == "http" and len(result.response_headers) > 0:
                downstream_send = self._create_header_injecting_send(
                    send, result.response_headers
                )
            
            await self._app(scope, downstream_receive, downstream_send)
            return
        
        # Authentication did not succeed (CHALLENGE, SKIP or FAILURE)
        if self._is_optional(path):
            # Allow unauthenticated access for optional paths
            scope["auth"] = None
            self._logger.debug(
                f"Authentication not established for optional path '{path}' "
                f"({result.status.value}), proceeding without context"
            )
            
            # Check access policy for unauthenticated access
            if not self.check_access_policy(path, None):
                self._logger.debug(
                    f"Access denied for path '{path}': "
                    f"policy check failed for unauthenticated access"
                )
                await self._deny_unauthenticated(scope, send, result)
                return
            
            await self._app(scope, downstream_receive, send)
            return
        
        self._logger.debug(
            f"Authentication failed for protected path '{path}': "
            f"{result.status.value} {result.error_code}"
        )
        await self._deny_unauthenticated(scope, send, result)
        
        return
    
    def _canonicalize_scope(
        self,
        scope: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Optional[str]]:
        """
            Put the request path in the form the router matches.

            The router behind the middleware matches the canonical form of
            a path (see :func:`ccai.webworks.routing.router.canonicalize_path`),
            so ``//admin/users`` reaches the handler registered for
            ``/admin/users``. Comparing the path as the client spelled it
            would let such a request past a policy keyed on
            ``/admin/users``. The canonical path is therefore written into
            a copy of the scope, which is used for the policy checks and
            handed on to the application, so both see one path.

            A path with a ``.`` segment is a second spelling of another
            path too. It is not decided at all: the caller redirects it to
            the path without the ``.`` segments.

            A path without a canonical form (a ``..`` segment, a NUL) is
            left alone: no route matches it, so the router answers 404
            whatever is decided here.

            :param scope: ASGI scope dictionary.

            :returns: The scope to use (the original or a copy with the
                      canonical path) and the path to redirect to, or None.
        """
        # Imported here because the routing package imports
        # authentication.core while it is being initialised.
        from ccai.webworks.routing.router import canonicalize_path, remove_dot_segments

        effective_scope = scope
        redirect_path: Optional[str] = None

        raw_path = scope.get("path")

        if isinstance(raw_path, str):
            canonical_path = canonicalize_path(raw_path)

            if canonical_path is not None:
                dot_free_path = remove_dot_segments(canonical_path)

                if dot_free_path != canonical_path:
                    redirect_path = dot_free_path
                elif canonical_path != raw_path:
                    effective_scope = dict(scope)
                    effective_scope["path"] = canonical_path

        return effective_scope, redirect_path

    async def _redirect_to_path(
        self,
        scope: Dict[str, Any],
        send: SendCallable,
        path: str
    ) -> None:
        """
            Answer a request with a permanent redirect to another spelling
            of its path, keeping the query string. A WebSocket handshake
            can not be redirected and is closed instead.

            :param scope: ASGI scope dictionary.
            :param send: Async callable to send messages.
            :param path: The path to redirect to.
        """
        if scope.get("type") == "websocket":
            await self._send_websocket_close(send)
            return

        location = urllib.parse.quote(path, safe=self.LOCATION_SAFE_CHARS)

        query_string = scope.get("query_string", b"")
        if isinstance(query_string, bytes):
            query_string = query_string.decode("latin-1")
        if query_string:
            location = f"{location}?{query_string}"

        # 308 keeps the method and the body of the request.
        await send({
            "type": "http.response.start",
            "status": 308,
            "headers": [
                (b"location", location.encode("latin-1")),
                (b"content-length", b"0"),
            ],
        })
        await send({"type": "http.response.body", "body": b"", "more_body": False})

        return

    def _build_request(self, scope: Dict[str, Any], body: bytes) -> Any:
        """
            Wrap an ASGI scope in the framework Request.
            
            ASGI delivers headers as a list of byte pairs and cookies
            only inside the ``cookie`` header; the Request parses both,
            which is the shape every shipped authenticator reads.
            
            :param scope: ASGI scope dictionary (http or websocket).
            :param body: The buffered request body, or empty bytes.
            
            :returns: A Request bound to the scope.
        """
        # Imported here because the routing package imports
        # authentication.core while it is being initialised.
        from ccai.webworks.routing.request import Request
        
        request = Request.from_asgi(scope, body)
        return request
    
    async def _read_body(self, receive: ReceiveCallable) -> Tuple[bytes, bool]:
        """
            Read the whole request body from the ASGI receive channel.
            
            :param receive: Async callable to receive messages.
            
            :returns: A tuple of (body, complete). complete is False when
                      the body is larger than the configured limit or the
                      client disconnected before sending all of it.
        """
        chunks: List[bytes] = []
        total = 0
        
        while True:
            message = await receive()
            message_type = message.get("type")
            
            if message_type != "http.request":
                # http.disconnect (or anything unexpected): the body
                # cannot be completed.
                return (b"", False)
            
            chunk = message.get("body", b"") or b""
            total += len(chunk)
            if total > self._max_body_bytes:
                return (b"", False)
            
            chunks.append(chunk)
            
            if not message.get("more_body", False):
                break
        
        body = b"".join(chunks)
        return (body, True)
    
    def _create_replay_receive(
        self,
        body: bytes,
        receive: ReceiveCallable
    ) -> ReceiveCallable:
        """
            Create a receive callable that replays a buffered body.
            
            The first call returns the whole body as one ``http.request``
            message; later calls go to the original receive channel so the
            application still observes ``http.disconnect``.
            
            :param body: The buffered request body.
            :param receive: The original receive callable.
            
            :returns: The replaying receive callable.
        """
        state = {"replayed": False}
        
        async def replay_receive() -> Dict[str, Any]:
            if not state["replayed"]:
                state["replayed"] = True
                return {"type": "http.request", "body": body, "more_body": False}
            message = await receive()
            return message
        
        return replay_receive
    
    def _create_header_injecting_send(
        self,
        send: SendCallable,
        response_headers: Dict[str, str]
    ) -> SendCallable:
        """
            Create a send callable that adds headers to the response start.
            
            Used for headers an authenticator asks for on a successful
            request, such as a renewed session cookie.
            
            :param send: The original send callable.
            :param response_headers: Header names and values to add.
            
            :returns: The wrapping send callable.
        """
        extra_headers = self._encode_headers(response_headers)
        
        async def send_with_headers(message: Dict[str, Any]) -> None:
            if message.get("type") == "http.response.start":
                headers = list(message.get("headers", []))
                headers.extend(extra_headers)
                message = dict(message)
                message["headers"] = headers
            await send(message)
            return
        
        return send_with_headers
    
    def _encode_headers(self, response_headers: Dict[str, str]) -> List[tuple]:
        """
            Encode header names and values as ASGI byte pairs.
            
            :param response_headers: Header names and values.
            
            :returns: List of (name, value) byte tuples.
        """
        encoded = []
        for name, value in response_headers.items():
            encoded.append(
                (str(name).lower().encode("latin-1"), str(value).encode("latin-1"))
            )
        return encoded
    
    def _build_fallback_challenge(self) -> str:
        """
            Build a challenge when no authenticator supplied one.
            
            RFC 7235 requires ``WWW-Authenticate`` on every 401. The
            fallback names each registered scheme with the middleware
            realm, or Basic when no scheme is registered.
            
            :returns: The ``WWW-Authenticate`` header value.
        """
        schemes = self._auth_system.get_registered_schemes()
        if len(schemes) == 0:
            schemes = ["Basic"]
        
        challenges = [f'{scheme} realm="{self._realm}"' for scheme in schemes]
        rtnval = ", ".join(challenges)
        return rtnval
    
    async def _deny_unauthenticated(
        self,
        scope: Dict[str, Any],
        send: SendCallable,
        result: AuthenticationResult
    ) -> None:
        """
            Refuse a request whose authentication did not succeed.
            
            HTTP requests get 401 (429 when the authenticator reports
            throttling); WebSocket handshakes are closed before accept.
            
            :param scope: ASGI scope dictionary.
            :param send: Async callable to send messages.
            :param result: The authentication result.
        """
        if scope.get("type") == "websocket":
            await self._send_websocket_close(send)
            return
        
        if result.error_code in self.THROTTLED_ERROR_CODES:
            await self._send_too_many_requests(send, result)
            return
        
        if result.status == AuthenticationStatus.CHALLENGE:
            await self._send_challenge(send, result.challenge)
            return
        
        await self._send_unauthorized(send, result)
        return
    
    async def _deny_forbidden(
        self,
        scope: Dict[str, Any],
        send: SendCallable
    ) -> None:
        """
            Refuse an authenticated request that fails the access policy.
            
            :param scope: ASGI scope dictionary.
            :param send: Async callable to send messages.
        """
        if scope.get("type") == "websocket":
            await self._send_websocket_close(send)
            return
        
        await self._send_forbidden(send)
        return
    
    async def _send_websocket_close(self, send: SendCallable) -> None:
        """
            Refuse a WebSocket handshake.
            
            Sending ``websocket.close`` before ``websocket.accept`` makes
            the server reject the handshake (HTTP 403), so no connection
            is ever established.
            
            :param send: Async callable to send messages.
        """
        await send({
            "type": "websocket.close",
            "code": self.WEBSOCKET_POLICY_VIOLATION_CODE
        })
        return
    
    async def _send_too_many_requests(
        self,
        send: SendCallable,
        result: AuthenticationResult
    ) -> None:
        """
            Send a 429 Too Many Requests response.
            
            :param send: Async callable to send messages.
            :param result: The authentication result with error details
                           and an optional ``Retry-After`` response header.
        """
        headers = [
            (b"content-type", b"application/json"),
        ]
        headers.extend(self._encode_headers(result.response_headers))
        
        await send({
            "type": "http.response.start",
            "status": 429,
            "headers": headers
        })
        
        body = {
            "error": result.error_code,
            "error_description": result.error_description or "Too many attempts"
        }
        
        await send({
            "type": "http.response.body",
            "body": json.dumps(body).encode("utf-8")
        })
        
        return
    
    async def _send_payload_too_large(self, send: SendCallable) -> None:
        """
            Send a 413 response for a body the middleware will not buffer.
            
            :param send: Async callable to send messages.
        """
        await send({
            "type": "http.response.start",
            "status": 413,
            "headers": [(b"content-type", b"application/json")]
        })
        
        body = {
            "error": "payload_too_large",
            "error_description": "Request body is too large to authenticate"
        }
        
        await send({
            "type": "http.response.body",
            "body": json.dumps(body).encode("utf-8")
        })
        
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
        
        # A 401 always names the schemes the client may use (RFC 7235)
        challenge = result.challenge
        if not challenge:
            challenge = self._build_fallback_challenge()
        headers.append((b"www-authenticate", challenge.encode("utf-8")))
        
        # Headers the authenticator asked for (e.g. clearing an expired
        # session cookie)
        headers.extend(self._encode_headers(result.response_headers))
        
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
    realm: str = "Restricted",
    max_body_bytes: Optional[int] = None
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
        :param max_body_bytes: Largest request body buffered for
                               authenticators that sign the body.
        
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
        realm=realm,
        max_body_bytes=max_body_bytes
    )
