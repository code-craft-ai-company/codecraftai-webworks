"""
.. module:: session
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Session-based authentication blueprint providing login, logout, and info endpoints.

.. moduleauthor:: Code Craft AI LLC

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

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


import logging
import secrets
import time

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ccai.webworks.authentication.basic import IdentityProvider
from ccai.webworks.authentication.core import AuthenticationContext, Principal
from ccai.webworks.authentication.session import InMemorySessionStore
from ccai.webworks.authentication.blueprints.responses import AuthError
from ccai.webworks.authentication.blueprints.schemas import (
    SessionLoginRequest,
    SessionInfo
)
from ccai.webworks.authentication.blueprints.security import (
    SecurityBlueprint,
    run_async as _shared_run_async
)
from ccai.webworks.endpoints.doc import Doc


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


def run_async(coro: Any) -> Any:
    """
        Public, supported name for running an asynchronous coroutine
        synchronously regardless of whether the calling thread
        already has a running event loop.

        Downstream applications bridge sync handler code onto async
        session stores through this helper, so it is part of the
        module's supported surface. Delegates to :func:`_run_async`,
        which several framework modules still call internally.

        :param coro: The coroutine to run to completion.

        :returns: Whatever the coroutine returns.
    """
    rtnval = _run_async(coro)
    return rtnval


def _run_async(coro: Any) -> Any:
    """
        Run an asynchronous coroutine synchronously, regardless of
        whether the calling thread already has a running event loop.

        Delegates to
        :func:`ccai.webworks.authentication.blueprints.security.run_async`,
        which drives the coroutine on the application's event loop when
        the handler was offloaded from it.

        :param coro: The coroutine to execute.

        :returns: The result of the coroutine.
    """
    result = _shared_run_async(coro)
    return result


class SessionStore:
    """
        Legacy abstract base class for blueprint-only session persistence.

        This record-oriented contract stores the principal identifier
        only, so a session kept in such a store cannot be turned back
        into an authenticated request by
        :class:`ccai.webworks.authentication.session.SessionAuthenticator`.
        It remains supported for the blueprint's own endpoints.

        New code should configure :attr:`SessionAuthBlueprint.session_store`
        with a store that follows
        :class:`ccai.webworks.authentication.session.SessionStore` (for
        example :class:`InMemorySessionStore`), which persists the full
        :class:`Principal` and is the store the authenticator reads. That
        is also what the blueprint uses when no store is configured.

        Subclasses must implement all methods to provide session storage
        and retrieval.

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
            session_store: Optional store for persisting sessions. A
                           store that follows
                           :class:`ccai.webworks.authentication.session.SessionStore`
                           keeps the full principal and is shared with
                           :class:`SessionAuthenticator`; a subclass of
                           this module's legacy :class:`SessionStore`
                           is still accepted. When None, an
                           :class:`InMemorySessionStore` private to the
                           blueprint class is used (see
                           :meth:`get_session_store`).
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
    session_store: Optional[Any] = None
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

    # Session data key under which the authentication scheme that
    # created the session is recorded.
    SESSION_DATA_SCHEME_KEY: str = "scheme"

    @classmethod
    def get_session_store(cls) -> Any:
        """
            Get the store the blueprint keeps sessions in.

            Returns the configured :attr:`session_store`, or an
            :class:`InMemorySessionStore` that belongs to this blueprint
            class alone (a subclass gets its own). Hand the same store to
            :class:`ccai.webworks.authentication.session.SessionAuthenticator`
            so the cookie a login sets authenticates later requests::

                SessionAuthenticator(
                    session_store=SiteSession.get_session_store(),
                    cookie_name=SiteSession.cookie_name
                )

            :returns: The session store in use.
        """
        if cls.session_store is not None:
            return cls.session_store

        store = cls.__dict__.get("_default_session_store")
        if store is None:
            store = InMemorySessionStore(
                default_expiration=cls.session_duration,
                max_sessions=cls.MEMORY_STORE_MAX_ENTRIES
            )
            cls._default_session_store = store
            cls.note_memory_fallback("session_store")

        return store

    @classmethod
    def _uses_legacy_store(cls) -> bool:
        """
            Check whether the configured store follows the legacy,
            record-oriented :class:`SessionStore` contract.

            :returns: True for a legacy store, False for a store that
                      follows the authenticator's protocol.
        """
        rtnval = isinstance(cls.session_store, SessionStore)
        return rtnval

    @classmethod
    def _parse_expiry(cls, expires_at: Any) -> Optional[datetime]:
        """
            Parse a stored ``expires_at`` value into an aware datetime.

            A timestamp without a timezone (common after a database round
            trip) is taken to be UTC.

            :param expires_at: An ISO 8601 string or a datetime.

            :returns: The aware datetime, or None if the value cannot be
                      interpreted.
        """
        expires_dt = None

        if isinstance(expires_at, datetime):
            expires_dt = expires_at
        elif isinstance(expires_at, str):
            try:
                expires_dt = datetime.fromisoformat(expires_at)
            except ValueError:
                expires_dt = None

        if expires_dt is not None and expires_dt.tzinfo is None:
            expires_dt = expires_dt.replace(tzinfo=timezone.utc)

        return expires_dt

    @classmethod
    def _isoformat(cls, value: Any) -> Optional[str]:
        """
            Render a timestamp from a session record for a response.

            :param value: A datetime, an ISO 8601 string or None.

            :returns: The ISO 8601 string, or None.
        """
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.isoformat()
        return str(value)

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
    def build_clear_cookie_header(cls) -> str:
        """
            Public, supported name for building a ``Set-Cookie``
            header value that clears the session cookie.

            Downstream applications issue logout responses with this
            value, so it is part of the blueprint's supported
            surface.

            :returns: A Set-Cookie header value string that clears
                      the cookie.
        """
        rtnval = cls._build_clear_cookie_header()
        return rtnval

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
        body = cls.read_request_data(request)
        if body is None:
            response = cls.invalid_body_response()
            return response

        username = body.get("username")
        password = body.get("password")
        remember_me = body.get("remember_me", False) is True

        if not isinstance(username, str) or not isinstance(password, str):
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

        throttled_response = cls.check_login_throttle(request, username)
        if throttled_response is not None:
            return throttled_response

        principal = _run_async(
            cls.identity_provider.validate_credentials(username, password)
        )

        cls.record_login_attempt(request, username, principal is not None)

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

        if cls._uses_legacy_store():
            # Legacy record-oriented store: only the principal id is kept
            session_id = cls._generate_session_id()
            now = datetime.now(tz=timezone.utc)
            created_at = now.isoformat()
            last_accessed = created_at
            expires_ts = time.time() + duration
            expires_at = datetime.fromtimestamp(
                expires_ts, tz=timezone.utc
            ).isoformat()

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
            # The session is created through the store protocol that
            # SessionAuthenticator reads, with the full principal, so
            # the cookie authenticates later requests.
            session_values: Dict[str, Any] = dict(attributes)
            session_values[cls.SESSION_DATA_SCHEME_KEY] = scheme

            session = _run_async(
                cls.get_session_store().create_session(
                    principal=principal,
                    expires_in=duration,
                    data=session_values
                )
            )

            session_id = session.session_id
            created_at = cls._isoformat(session.created_at)
            last_accessed = cls._isoformat(session.last_accessed)
            expires_at = cls._isoformat(session.expires_at)

        cookie_header = cls._build_cookie_header(session_id, duration)

        # The session id travels only in the HttpOnly cookie. Echoing it
        # in the body would hand it to any script running in the page.
        response_body = {
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
            _run_async(cls.get_session_store().delete_session(session_id))

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

        session_store = cls.get_session_store()

        # Look up the session
        session_data = _run_async(session_store.get_session(session_id))

        if session_data is None:
            error = AuthError(
                error=cls.INVALID_SESSION_ERROR_CODE,
                error_description="Session not found or expired"
            )
            response = cls.format_error(error, status_code=401)
            response["headers"] = {
                cls.SET_COOKIE_HEADER: cls._build_clear_cookie_header()
            }
            return response

        is_legacy_record = isinstance(session_data, dict)

        # Check expiration. A session whose expiry cannot be read is
        # treated as expired rather than as valid forever.
        if is_legacy_record:
            expires_at = session_data.get("expires_at")
            is_expired = False
            if expires_at is not None:
                expires_dt = cls._parse_expiry(expires_at)
                if expires_dt is None:
                    logger.warning(
                        "Session info: unreadable expires_at=%r for session=%s; "
                        "treating the session as expired",
                        expires_at,
                        _session_id_prefix(session_id),
                    )
                    is_expired = True
                else:
                    is_expired = datetime.now(tz=timezone.utc) > expires_dt
        else:
            is_expired = session_data.is_expired

        if is_expired:
            # Session has expired — remove it and clear the cookie
            _run_async(session_store.delete_session(session_id))
            error = AuthError(
                error=cls.SESSION_EXPIRED_ERROR_CODE,
                error_description="Session has expired"
            )
            response = cls.format_error(error, status_code=401)
            response["headers"] = {
                cls.SET_COOKIE_HEADER: cls._build_clear_cookie_header()
            }
            return response

        # Renew session — update last_accessed timestamp
        now_str = datetime.now(tz=timezone.utc).isoformat()
        if is_legacy_record:
            _run_async(
                session_store.update_last_accessed(session_id, now_str)
            )
            principal_id = session_data.get("principal_id")
            created_at = cls._isoformat(session_data.get("created_at"))
            expires_at = cls._isoformat(session_data.get("expires_at"))
        else:
            _run_async(session_store.update_session(session_id))
            principal_id = session_data.principal_id
            created_at = cls._isoformat(session_data.created_at)
            expires_at = cls._isoformat(session_data.expires_at)

        # Build response body. The session id stays in the HttpOnly
        # cookie and is not repeated here.
        response_body = {
            "principal_id": principal_id,
            "created_at": created_at,
            "expires_at": expires_at,
            "last_accessed": now_str,
        }

        response = {
            "status": 200,
            "body": response_body,
            "content_type": cls.JSON_CONTENT_TYPE,
        }
        return response
