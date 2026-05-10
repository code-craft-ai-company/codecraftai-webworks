"""
.. module:: session
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Session-based authentication blueprint providing login, logout, and info endpoints.

.. moduleauthor:: Automation Mojo LLC

This module provides the :class:`SessionAuthBlueprint` class which extends
:class:`SecurityBlueprint` to offer pre-built endpoints for cookie-based
session management. The blueprint delegates credential validation to a
configurable :class:`IdentityProvider` and manages sessions via an optional
:class:`SessionStore`.

Sessions are tracked using secure cookies with configurable HttpOnly,
Secure, and SameSite attributes. The blueprint supports configurable
session duration, remember-me extended duration, and session renewal
on activity.

Endpoints:
    - ``POST <base_path>/login`` — Authenticate and create a new session.
    - ``POST <base_path>/logout`` — Invalidate the session and clear the cookie.
    - ``GET <base_path>`` — Retrieve information about the current session.
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


import asyncio
import logging
import secrets
import time

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from automojo.webworks.authentication.basic import IdentityProvider
from automojo.webworks.authentication.core import AuthenticationContext, Principal
from automojo.webworks.authentication.blueprints.responses import (
    AuthError,
    AuthResponse
)
from automojo.webworks.authentication.blueprints.schemas import (
    SessionLoginRequest,
    SessionInfo
)
from automojo.webworks.authentication.blueprints.security import (
    SecurityBlueprint
)
from automojo.webworks.endpoints.doc import Doc


# Module-level logger used by the session-blueprint handlers when an
# error is converted into an HTTP error response. Without it the
# operator sees only the wire-format error code in the journal,
# never the underlying cause (e.g. malformed expires_at, identity
# provider raising, session-store backend crashing).
logger = logging.getLogger(__name__)


def _session_id_prefix(session_id: Optional[str]) -> str:
    """
        Truncate a session identifier to a journal-safe prefix.

        Logs should not contain live session ids — a leak of the
        journal must not be sufficient to hijack a session. This
        helper returns the first 8 characters of *session_id* with
        an ellipsis suffix so the operator can correlate journal
        lines with a session without exposing the full secret.

        :param session_id: The session identifier, or None.

        :returns: A short prefix string suitable for inclusion in
                  log messages, or ``"<none>"`` when the input is
                  ``None``/empty.
    """
    if session_id is None:
        return "<none>"
    if len(session_id) == 0:
        return "<empty>"
    if len(session_id) <= 8:
        return "{}…".format(session_id[:4])
    rtnval = "{}…".format(session_id[:8])
    return rtnval


def _run_async(coro: Any) -> Any:
    """
        Run an asynchronous coroutine synchronously, regardless of
        whether the calling thread already has a running event loop.

        Uvicorn / Hypercorn workers always have a running loop on the
        request-handling thread, so the naive pattern
        ``asyncio.get_event_loop().run_until_complete(coro)`` raises
        ``RuntimeError: This event loop is already running``. When a
        running loop is detected this helper offloads the coroutine
        to a fresh worker thread with its own loop and blocks on the
        thread's result; the sync caller observes a normal return
        value with no nested-loop interleaving.

        :param coro: The coroutine to execute.

        :returns: The result of the coroutine.
    """
    try:
        running_loop = asyncio.get_running_loop()
    except RuntimeError:
        running_loop = None

    if running_loop is None:
        # No running loop on this thread — drive the coroutine here
        # with a fresh loop.
        result = asyncio.run(coro)
        return result

    # A running loop is present (the typical ASGI case). Offload to
    # a worker thread that owns its own loop so we never recurse
    # into the live loop.
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(asyncio.run, coro)
        result = future.result()

    return result


class SessionStore:
    """
        Abstract base class for session persistence.

        Subclasses must implement all methods to provide session storage
        and retrieval. The default :class:`SessionAuthBlueprint` uses an
        in-memory dictionary when no store is configured.

        Each session is represented as a dictionary with the following keys:
            - ``session_id``: Unique session identifier string.
            - ``principal_id``: Identifier of the authenticated principal.
            - ``created_at``: ISO 8601 timestamp of session creation.
            - ``expires_at``: ISO 8601 timestamp of session expiration, or None.
            - ``last_accessed``: ISO 8601 timestamp of last activity.
    """

    async def create_session(
        self,
        session_id: str,
        principal_id: str,
        created_at: str,
        expires_at: Optional[str],
        last_accessed: str
    ) -> None:
        """
            Store a new session.

            :param session_id: Unique session identifier.
            :param principal_id: Identifier of the authenticated principal.
            :param created_at: ISO 8601 creation timestamp.
            :param expires_at: ISO 8601 expiration timestamp, or None.
            :param last_accessed: ISO 8601 last-accessed timestamp.
        """
        raise NotImplementedError("Subclasses must implement create_session")

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
            Retrieve a session by its identifier.

            :param session_id: The session identifier to look up.

            :returns: A dictionary of session data, or None if not found.
        """
        raise NotImplementedError("Subclasses must implement get_session")

    async def delete_session(self, session_id: str) -> bool:
        """
            Remove a session from the store.

            :param session_id: The session identifier to remove.

            :returns: True if the session was found and removed, False otherwise.
        """
        raise NotImplementedError("Subclasses must implement delete_session")

    async def update_last_accessed(self, session_id: str, last_accessed: str) -> bool:
        """
            Update the last-accessed timestamp for a session.

            Used for session renewal on activity.

            :param session_id: The session identifier to update.
            :param last_accessed: The new ISO 8601 last-accessed timestamp.

            :returns: True if the session was found and updated, False otherwise.
        """
        raise NotImplementedError("Subclasses must implement update_last_accessed")


class SessionAuthBlueprint(SecurityBlueprint):
    """
        Blueprint for session-based authentication endpoints.

        Provides login, logout, and session info endpoints for cookie-based
        session management. Credential validation is delegated to a
        configurable :class:`IdentityProvider` instance. Sessions are
        persisted via an optional :class:`SessionStore`; when no store is
        configured, an in-memory dictionary is used.

        Login responses include a ``Set-Cookie`` header with configurable
        security attributes (HttpOnly, Secure, SameSite). The blueprint
        supports configurable session duration, extended remember-me
        duration, and session renewal on activity.

        Default Endpoints:
            - ``POST /auth/session/login`` — Authenticate and create a
              new session with a secure cookie.
            - ``POST /auth/session/logout`` — Invalidate the current
              session and clear the cookie.
            - ``GET /auth/session`` — Retrieve information about the
              current session.

        Class Attributes:
            base_path: Base URL path for all endpoints. Defaults to
                       ``"/auth/session"``.
            tags: Documentation tags applied to all endpoints.
            identity_provider: The :class:`IdentityProvider` used for
                               credential validation. Must be set before
                               the login endpoint can process requests.
            session_store: Optional :class:`SessionStore` for persisting
                           sessions. When None, sessions are stored in an
                           in-memory dictionary.
            session_duration: Default session lifetime in seconds. Defaults
                              to 3600 (1 hour).
            remember_me_duration: Extended session lifetime in seconds when
                                  the ``remember_me`` flag is set. Defaults
                                  to 2592000 (30 days).
            cookie_name: Name of the session cookie. Defaults to
                         ``"session_id"``.
            cookie_secure: Whether to set the Secure flag on the cookie.
                           Defaults to True.
            cookie_httponly: Whether to set the HttpOnly flag on the cookie.
                             Defaults to True.
            cookie_samesite: The SameSite attribute for the cookie. Defaults
                             to ``"Lax"``.
    """

    base_path: str = "/auth/session"
    tags: List[str] = ["Authentication", "Session"]

    identity_provider: Optional[IdentityProvider] = None
    session_store: Optional[SessionStore] = None
    session_duration: int = 3600
    remember_me_duration: int = 86400 * 30
    cookie_name: str = "session_id"
    cookie_secure: bool = True
    cookie_httponly: bool = True
    cookie_samesite: str = "Lax"

    # --- Class constants ---
    # Override these on a subclass to rebrand wire-format strings without
    # rewriting the handler bodies.

    # Error codes
    ENDPOINT_DISABLED_ERROR_CODE: str = "endpoint_disabled"
    SERVER_ERROR_CODE: str = "server_error"
    INVALID_CREDENTIALS_ERROR_CODE: str = "invalid_credentials"
    INVALID_SESSION_ERROR_CODE: str = "invalid_session"
    SESSION_EXPIRED_ERROR_CODE: str = "session_expired"
    INVALID_REQUEST_ERROR_CODE: str = "invalid_request"

    # Success / response messages
    LOGIN_SUCCESS_MESSAGE: str = "Login successful"
    SESSION_ESTABLISHED_MESSAGE: str = "Session established"
    LOGOUT_MESSAGE: str = "Logged out"

    # Authentication scheme label written into AuthenticationContext
    SCHEME_LABEL: str = "Session"

    # Cookie attribute literals
    COOKIE_PATH: str = "/"
    COOKIE_HTTPONLY_FLAG: str = "HttpOnly"
    COOKIE_SECURE_FLAG: str = "Secure"
    COOKIE_SAMESITE_PREFIX: str = "SameSite="
    COOKIE_PART_SEPARATOR: str = "; "
    COOKIE_HEADER_NAME: str = "Cookie"
    SET_COOKIE_HEADER: str = "Set-Cookie"

    # In-memory fallback store when no session_store is configured
    _memory_store: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def _generate_session_id(cls) -> str:
        """
            Generate a cryptographically secure session identifier.

            The identifier is a URL-safe base64-encoded string of 32
            random bytes, providing 256 bits of entropy.

            :returns: A random session identifier string.
        """
        session_id = secrets.token_urlsafe(32)
        return session_id

    @classmethod
    def _build_cookie_header(cls, session_id: str, max_age: int) -> str:
        """
            Build a Set-Cookie header value with security attributes.

            Constructs the cookie string including the session identifier,
            Max-Age, Path, and the configured security flags (HttpOnly,
            Secure, SameSite).

            :param session_id: The session identifier to set in the cookie.
            :param max_age: The cookie lifetime in seconds.

            :returns: A complete Set-Cookie header value string.
        """
        parts = []
        parts.append("{}={}".format(cls.cookie_name, session_id))
        parts.append("Max-Age={}".format(max_age))
        parts.append("Path={}".format(cls.COOKIE_PATH))

        if cls.cookie_httponly:
            parts.append(cls.COOKIE_HTTPONLY_FLAG)

        if cls.cookie_secure:
            parts.append(cls.COOKIE_SECURE_FLAG)

        if cls.cookie_samesite:
            parts.append("{}{}".format(cls.COOKIE_SAMESITE_PREFIX, cls.cookie_samesite))

        cookie_header = cls.COOKIE_PART_SEPARATOR.join(parts)
        return cookie_header

    @classmethod
    def _build_clear_cookie_header(cls) -> str:
        """
            Build a Set-Cookie header value that clears the session cookie.

            Sets the cookie value to empty and Max-Age to 0, which instructs
            the browser to remove the cookie immediately.

            :returns: A Set-Cookie header value string that clears the cookie.
        """
        parts = []
        parts.append("{}=".format(cls.cookie_name))
        parts.append("Max-Age=0")
        parts.append("Path={}".format(cls.COOKIE_PATH))

        if cls.cookie_httponly:
            parts.append(cls.COOKIE_HTTPONLY_FLAG)

        if cls.cookie_secure:
            parts.append(cls.COOKIE_SECURE_FLAG)

        if cls.cookie_samesite:
            parts.append("{}{}".format(cls.COOKIE_SAMESITE_PREFIX, cls.cookie_samesite))

        cookie_header = cls.COOKIE_PART_SEPARATOR.join(parts)
        return cookie_header

    @classmethod
    def _get_session_id_from_request(cls, request: Any) -> Optional[str]:
        """
            Extract the session identifier from the request cookies.

            Looks for the configured cookie name in the request's cookie
            header and returns its value if found.

            :param request: The incoming HTTP request object.

            :returns: The session identifier string, or None if not found.
        """
        cookies = None

        if hasattr(request, "cookies"):
            cookies = request.cookies
        elif hasattr(request, "headers"):
            headers = request.headers
            cookie_header = None
            if isinstance(headers, dict):
                cookie_header = headers.get(cls.COOKIE_HEADER_NAME) or headers.get(cls.COOKIE_HEADER_NAME.lower())
            if cookie_header is not None:
                cookies = {}
                for pair in cookie_header.split(";"):
                    pair = pair.strip()
                    if "=" in pair:
                        key, value = pair.split("=", 1)
                        cookies[key.strip()] = value.strip()

        if cookies is None:
            return None

        session_id = cookies.get(cls.cookie_name)
        return session_id

    @classmethod
    @SecurityBlueprint.create(
        leaf="login",
        request_schema=SessionLoginRequest,
        response_schema=SessionInfo,
        doc=Doc(
            summary="Login and create session",
            description="Authenticate with username and password and create "
                        "a new session with a secure cookie."
        ),
        on_conflict="replace"
    )
    def login(cls, request: Any) -> dict:
        """
            Handle a login request and create a new session.

            Validates the provided credentials against the configured
            :attr:`identity_provider`. On success, creates a new session,
            stores it, and returns a response with a Set-Cookie header
            containing the session identifier and security attributes.

            When the ``remember_me`` flag is set in the request body, the
            session uses the extended :attr:`remember_me_duration` instead
            of the default :attr:`session_duration`.

            The endpoint can be disabled via the ``enabled_endpoints``
            configuration. When disabled, a 404 response is returned.

            :param request: The incoming HTTP request object. The request
                            body must contain ``username`` and ``password``
                            fields, and may optionally include ``remember_me``.

            :returns: A response dictionary with ``status``, ``body``,
                      ``content_type``, and ``headers`` keys.
        """
        if not cls.is_endpoint_enabled("login"):
            error = AuthError(
                error=cls.ENDPOINT_DISABLED_ERROR_CODE,
                error_description="Login endpoint is disabled"
            )
            response = cls.format_error(error, status_code=404)
            return response

        # Pre-authentication hook
        pre_error = cls.pre_authenticate(request)
        if pre_error is not None:
            response = cls.format_error(pre_error)
            return response

        # Extract credentials from request body
        body = request.json()
        username = body.get("username")
        password = body.get("password")
        remember_me = body.get("remember_me", False)

        if username is None or password is None:
            error = AuthError(
                error=cls.INVALID_REQUEST_ERROR_CODE,
                error_description="Username and password required"
            )
            response = cls.format_error(error)
            return response

        if len(username) == 0 or len(password) == 0:
            error = AuthError(
                error=cls.INVALID_REQUEST_ERROR_CODE,
                error_description="Username and password must not be empty"
            )
            response = cls.format_error(error)
            return response

        # Validate credentials via the identity provider
        if cls.identity_provider is None:
            # Misconfigured deployment — log so the operator sees the
            # 500 in the journal even when the wire body is generic.
            logger.error(
                "Session login: identity_provider is not configured on %s; "
                "returning 500",
                cls.__name__,
            )
            error = AuthError(
                error=cls.SERVER_ERROR_CODE,
                error_description="No identity provider configured"
            )
            response = cls.format_error(error, status_code=500)
            return response

        principal = _run_async(
            cls.identity_provider.validate_credentials(username, password)
        )

        if principal is None:
            error = AuthError(
                error=cls.INVALID_CREDENTIALS_ERROR_CODE,
                error_description="Invalid username or password"
            )
            response = cls.format_error(error)
            return response

        response = cls.establish_session(
            principal=principal,
            request=request,
            remember_me=remember_me,
            scheme=cls.SCHEME_LABEL,
            success_message=cls.LOGIN_SUCCESS_MESSAGE,
        )
        return response

    @classmethod
    def establish_session(
        cls,
        principal: Principal,
        request: Optional[Any] = None,
        remember_me: bool = False,
        scheme: Optional[str] = None,
        success_message: Optional[str] = None,
        extra_attributes: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
            Materialize a session for an already-authenticated principal.

            This method performs the post-credential-validation half of a
            login flow: it builds an :class:`AuthenticationContext`, runs the
            ``post_authenticate`` hook, persists a new session record via the
            configured :attr:`session_store` (or the in-memory fallback), and
            returns a ready-to-send response dict containing the session
            cookie.

            It is intended for sibling auth blueprints (magic-link redemption,
            OAuth callback, SSO assertion handlers, etc.) that need to produce
            a session for a principal they validated through some channel
            other than the username/password ``login`` endpoint. The
            ``login`` endpoint itself delegates to this method after
            ``identity_provider.validate_credentials`` succeeds.

            :param principal: The authenticated :class:`Principal`. Callers
                              are responsible for verifying credentials before
                              calling this method.
            :param request: Optional incoming HTTP request, forwarded to the
                            ``post_authenticate`` hook so subclasses can
                            inspect it.
            :param remember_me: When ``True``, use
                                :attr:`remember_me_duration` instead of
                                :attr:`session_duration` for the session and
                                cookie lifetime.
            :param scheme: Authentication scheme label recorded on the
                           :class:`AuthenticationContext`. Sibling blueprints
                           should pass a label that identifies their channel
                           (e.g. ``"MagicLink"``, ``"OAuth"``).
            :param success_message: ``message`` field included in the
                                    response body. Defaults to
                                    ``"Session established"``; the
                                    credential login path overrides this with
                                    ``"Login successful"`` to preserve its
                                    historical wire format.
            :param extra_attributes: Optional mapping merged into the
                                     :class:`AuthenticationContext` attributes.
                                     Useful for recording channel-specific
                                     metadata (token id, idp issuer, etc.).

            :returns: A response dictionary with ``status``, ``body``,
                      ``content_type`` and ``headers`` keys. The ``Set-Cookie``
                      header carries the new session id with the configured
                      security flags.
        """
        if scheme is None:
            scheme = cls.SCHEME_LABEL
        if success_message is None:
            success_message = cls.SESSION_ESTABLISHED_MESSAGE

        attributes: Dict[str, Any] = {}
        if extra_attributes is not None:
            attributes.update(extra_attributes)

        context = AuthenticationContext(
            principal=principal,
            scheme=scheme,
            attributes=attributes
        )

        cls.post_authenticate(request, context)

        if remember_me:
            duration = cls.remember_me_duration
        else:
            duration = cls.session_duration

        session_id = cls._generate_session_id()
        now = datetime.now(tz=timezone.utc)
        created_at = now.isoformat()
        last_accessed = created_at
        expires_ts = time.time() + duration
        expires_at = datetime.fromtimestamp(
            expires_ts, tz=timezone.utc
        ).isoformat()

        session_data = {
            "session_id": session_id,
            "principal_id": principal.identifier,
            "created_at": created_at,
            "expires_at": expires_at,
            "last_accessed": last_accessed,
        }

        if cls.session_store is not None:
            _run_async(
                cls.session_store.create_session(
                    session_id=session_id,
                    principal_id=principal.identifier,
                    created_at=created_at,
                    expires_at=expires_at,
                    last_accessed=last_accessed
                )
            )
        else:
            cls._memory_store[session_id] = session_data

        cookie_header = cls._build_cookie_header(session_id, duration)

        response_body = {
            "session_id": session_id,
            "principal_id": principal.identifier,
            "created_at": created_at,
            "expires_at": expires_at,
            "last_accessed": last_accessed,
            "message": success_message,
        }

        response = {
            "status": 200,
            "body": response_body,
            "content_type": cls.JSON_CONTENT_TYPE,
            "headers": {
                cls.SET_COOKIE_HEADER: cookie_header,
            },
        }
        return response

    @classmethod
    @SecurityBlueprint.create(
        leaf="logout",
        doc=Doc(
            summary="Logout and destroy session",
            description="Invalidate the current session and clear the "
                        "session cookie."
        ),
        on_conflict="replace"
    )
    def logout(cls, request: Any) -> dict:
        """
            Handle a logout request and destroy the current session.

            Extracts the session identifier from the request cookie,
            removes the session from the store, and returns a response
            with a Set-Cookie header that clears the cookie.

            The endpoint can be disabled via the ``enabled_endpoints``
            configuration. When disabled, a 404 response is returned.

            :param request: The incoming HTTP request object. The session
                            identifier is read from the cookie header.

            :returns: A response dictionary with ``status``, ``body``,
                      ``content_type``, and ``headers`` keys.
        """
        if not cls.is_endpoint_enabled("logout"):
            error = AuthError(
                error=cls.ENDPOINT_DISABLED_ERROR_CODE,
                error_description="Logout endpoint is disabled"
            )
            response = cls.format_error(error, status_code=404)
            return response

        # Extract session ID from cookie
        session_id = cls._get_session_id_from_request(request)

        if session_id is not None:
            # Invalidate the session in the store
            if cls.session_store is not None:
                _run_async(cls.session_store.delete_session(session_id))
            else:
                cls._memory_store.pop(session_id, None)

        # Build the clear-cookie header
        clear_cookie = cls._build_clear_cookie_header()

        response = {
            "status": 200,
            "body": {"message": cls.LOGOUT_MESSAGE},
            "content_type": cls.JSON_CONTENT_TYPE,
            "headers": {
                cls.SET_COOKIE_HEADER: clear_cookie,
            },
        }
        return response

    @classmethod
    @SecurityBlueprint.read(
        path="",
        response_schema=SessionInfo,
        doc=Doc(
            summary="Get session info",
            description="Retrieve information about the current session."
        ),
        on_conflict="replace"
    )
    def info(cls, request: Any) -> dict:
        """
            Retrieve information about the current session.

            Extracts the session identifier from the request cookie and
            looks up the session data. If the session is found and has
            not expired, the last-accessed timestamp is updated to support
            session renewal on activity.

            The endpoint can be disabled via the ``enabled_endpoints``
            configuration. When disabled, a 404 response is returned.

            :param request: The incoming HTTP request object. The session
                            identifier is read from the cookie header.

            :returns: A response dictionary with ``status``, ``body``, and
                      ``content_type`` keys.
        """
        if not cls.is_endpoint_enabled("info"):
            error = AuthError(
                error=cls.ENDPOINT_DISABLED_ERROR_CODE,
                error_description="Session info endpoint is disabled"
            )
            response = cls.format_error(error, status_code=404)
            return response

        # Extract session ID from cookie
        session_id = cls._get_session_id_from_request(request)

        if session_id is None:
            error = AuthError(
                error=cls.INVALID_SESSION_ERROR_CODE,
                error_description="No session cookie found"
            )
            response = cls.format_error(error, status_code=401)
            return response

        # Look up the session
        if cls.session_store is not None:
            session_data = _run_async(
                cls.session_store.get_session(session_id)
            )
        else:
            session_data = cls._memory_store.get(session_id)

        if session_data is None:
            error = AuthError(
                error=cls.INVALID_SESSION_ERROR_CODE,
                error_description="Session not found or expired"
            )
            response = cls.format_error(error, status_code=401)
            return response

        # Check expiration
        expires_at = session_data.get("expires_at")
        if expires_at is not None:
            now = datetime.now(tz=timezone.utc)
            try:
                expires_dt = datetime.fromisoformat(expires_at)
                if now > expires_dt:
                    # Session has expired — remove it
                    if cls.session_store is not None:
                        _run_async(
                            cls.session_store.delete_session(session_id)
                        )
                    else:
                        cls._memory_store.pop(session_id, None)

                    error = AuthError(
                        error=cls.SESSION_EXPIRED_ERROR_CODE,
                        error_description="Session has expired"
                    )
                    response = cls.format_error(error, status_code=401)
                    return response
            except (ValueError, TypeError):
                # Stored expires_at is malformed (legacy session, store
                # corruption, clock-skew round-tripping issues). The
                # session is salvageable but the operator wants to know
                # the store is producing bad timestamps.
                logger.warning(
                    "Session info: failed to parse expires_at=%r for session=%s; "
                    "skipping expiry check",
                    expires_at,
                    _session_id_prefix(session_id),
                )

        # Renew session — update last_accessed timestamp
        now_str = datetime.now(tz=timezone.utc).isoformat()

        if cls.session_store is not None:
            _run_async(
                cls.session_store.update_last_accessed(session_id, now_str)
            )
        else:
            if session_id in cls._memory_store:
                cls._memory_store[session_id]["last_accessed"] = now_str

        # Build response body
        response_body = {
            "session_id": session_data.get("session_id"),
            "principal_id": session_data.get("principal_id"),
            "created_at": session_data.get("created_at"),
            "expires_at": session_data.get("expires_at"),
            "last_accessed": now_str,
        }

        response = {
            "status": 200,
            "body": response_body,
            "content_type": cls.JSON_CONTENT_TYPE,
        }
        return response
