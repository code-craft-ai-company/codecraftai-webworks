"""
.. module:: session
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Session-based authentication implementation.

.. moduleauthor:: Automation Mojo LLC

This module provides the SessionAuthenticator class which implements session-based
authentication using secure cookies. It supports configurable session expiration,
renewal on activity, and secure cookie attributes (HttpOnly, Secure, SameSite).
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, Optional, Protocol, runtime_checkable

from automojo.webworks.authentication.core import (
    AuthenticationContext,
    AuthenticationResult,
    AuthenticationStatus,
    Principal
)


class SameSitePolicy(Enum):
    """
        SameSite cookie attribute values.
        
        :cvar STRICT: Cookie only sent in first-party context.
        :cvar LAX: Cookie sent with top-level navigations and GET from third-party.
        :cvar NONE: Cookie sent in all contexts (requires Secure).
    """
    
    STRICT = "Strict"
    LAX = "Lax"
    NONE = "None"


@dataclass
class SessionData:
    """
        Represents a user session.
        
        This dataclass contains all the information about an active session
        including the session identifier, associated principal, timestamps,
        and arbitrary session data.
        
        :param session_id: Unique identifier for the session.
        :param principal_id: Identifier of the authenticated principal.
        :param principal: The full Principal object for the session.
        :param created_at: Timestamp when the session was created.
        :param last_accessed: Timestamp of the last session access.
        :param expires_at: Optional expiration timestamp for the session.
        :param data: Additional session data storage.
    """
    
    session_id: str
    principal_id: str
    principal: Principal
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_accessed: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    data: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_expired(self) -> bool:
        """
            Check if the session has expired.

            Naive ``expires_at`` values (no ``tzinfo``) are interpreted as UTC
            so the comparison against the current time always operates on aware
            datetimes; otherwise callers passing ``datetime.utcnow()`` would
            trigger ``TypeError: can't compare offset-naive and offset-aware
            datetimes``.

            :returns: True if expires_at is set and has passed, False otherwise.
        """
        if self.expires_at is None:
            return False

        expires_at = self.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        return datetime.now(timezone.utc) > expires_at


@dataclass
class CookieAttributes:
    """
        Attributes for session cookies.
        
        This dataclass encapsulates all the security-related attributes
        that should be set on session cookies.
        
        :param http_only: If True, cookie is not accessible via JavaScript.
        :param secure: If True, cookie only sent over HTTPS.
        :param same_site: SameSite policy for the cookie.
        :param path: URL path for which the cookie is valid.
        :param domain: Domain for which the cookie is valid.
        :param max_age: Maximum age of the cookie in seconds.
    """
    
    http_only: bool = True
    secure: bool = True
    same_site: SameSitePolicy = SameSitePolicy.LAX
    path: str = "/"
    domain: Optional[str] = None
    max_age: Optional[int] = None
    
    def to_cookie_string(self, name: str, value: str) -> str:
        """
            Generate a Set-Cookie header value with all attributes.
            
            :param name: The cookie name.
            :param value: The cookie value.
            
            :returns: A complete Set-Cookie header value string.
        """
        parts = [f"{name}={value}"]
        
        if self.path:
            parts.append(f"Path={self.path}")
        
        if self.domain:
            parts.append(f"Domain={self.domain}")
        
        if self.max_age is not None:
            parts.append(f"Max-Age={self.max_age}")
        
        if self.http_only:
            parts.append("HttpOnly")
        
        if self.secure:
            parts.append("Secure")
        
        parts.append(f"SameSite={self.same_site.value}")
        
        return "; ".join(parts)
    
    def to_clear_cookie_string(self, name: str) -> str:
        """
            Generate a Set-Cookie header value to clear the cookie.
            
            :param name: The cookie name to clear.
            
            :returns: A Set-Cookie header value that clears the cookie.
        """
        parts = [f"{name}="]
        parts.append("Path=" + self.path)
        parts.append("Max-Age=0")
        parts.append("Expires=Thu, 01 Jan 1970 00:00:00 GMT")
        
        if self.http_only:
            parts.append("HttpOnly")
        
        if self.secure:
            parts.append("Secure")
        
        parts.append(f"SameSite={self.same_site.value}")
        
        return "; ".join(parts)


@runtime_checkable
class SessionStore(Protocol):
    """
        Protocol for session storage backends.
        
        A SessionStore is responsible for persisting and retrieving session
        data. Implementations can use various backends such as in-memory
        storage, Redis, databases, etc.
    """
    
    async def create_session(
        self,
        principal: Principal,
        expires_in: Optional[int] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> SessionData:
        """
            Create a new session for the given principal.
            
            :param principal: The authenticated principal.
            :param expires_in: Session lifetime in seconds (None for no expiration).
            :param data: Optional initial session data.
            
            :returns: The created SessionData.
        """
        ...
    
    async def get_session(self, session_id: str) -> Optional[SessionData]:
        """
            Retrieve a session by its identifier.
            
            :param session_id: The session identifier.
            
            :returns: The SessionData if found and valid, None otherwise.
        """
        ...
    
    async def update_session(
        self,
        session_id: str,
        data: Optional[Dict[str, Any]] = None,
        extend_expiration: bool = False
    ) -> Optional[SessionData]:
        """
            Update a session's data and/or extend its expiration.
            
            :param session_id: The session identifier.
            :param data: New session data to merge.
            :param extend_expiration: If True, reset the expiration timer.
            
            :returns: The updated SessionData if found, None otherwise.
        """
        ...
    
    async def delete_session(self, session_id: str) -> bool:
        """
            Delete a session.
            
            :param session_id: The session identifier.
            
            :returns: True if the session was deleted, False if not found.
        """
        ...
    
    async def delete_sessions_for_principal(self, principal_id: str) -> int:
        """
            Delete all sessions for a given principal.
            
            :param principal_id: The principal identifier.
            
            :returns: The number of sessions deleted.
        """
        ...


class InMemorySessionStore:
    """
        In-memory implementation of SessionStore for testing.
        
        This implementation stores sessions in a dictionary. It is suitable
        for testing and development but should not be used in production
        as sessions are lost on restart and not shared across processes.
        
        :param default_expiration: Default session lifetime in seconds.
        :param session_id_length: Length of generated session IDs in bytes.
    """
    
    def __init__(
        self,
        default_expiration: Optional[int] = 3600,
        session_id_length: int = 32
    ):
        """
            Initialize the in-memory session store.
            
            :param default_expiration: Default session lifetime in seconds.
                                      None means sessions don't expire.
            :param session_id_length: Length of generated session IDs in bytes.
        """
        self._sessions: Dict[str, SessionData] = {}
        self._default_expiration = default_expiration
        self._session_id_length = session_id_length
    
    def _generate_session_id(self) -> str:
        """
            Generate a cryptographically secure session ID.
            
            :returns: A hex-encoded random session ID.
        """
        return secrets.token_hex(self._session_id_length)
    
    async def create_session(
        self,
        principal: Principal,
        expires_in: Optional[int] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> SessionData:
        """
            Create a new session for the given principal.
            
            :param principal: The authenticated principal.
            :param expires_in: Session lifetime in seconds (None uses default).
            :param data: Optional initial session data.
            
            :returns: The created SessionData.
        """
        session_id = self._generate_session_id()
        
        # Determine expiration
        expiration_seconds = expires_in if expires_in is not None else self._default_expiration
        expires_at = None
        if expiration_seconds is not None:
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=expiration_seconds)
        
        session = SessionData(
            session_id=session_id,
            principal_id=principal.identifier,
            principal=principal,
            expires_at=expires_at,
            data=data or {}
        )
        
        self._sessions[session_id] = session
        return session
    
    async def get_session(self, session_id: str) -> Optional[SessionData]:
        """
            Retrieve a session by its identifier.
            
            :param session_id: The session identifier.
            
            :returns: The SessionData if found and not expired, None otherwise.
        """
        session = self._sessions.get(session_id)
        
        if session is None:
            return None
        
        # Check expiration
        if session.is_expired:
            # Clean up expired session
            del self._sessions[session_id]
            return None
        
        # Update last accessed time
        session.last_accessed = datetime.now(timezone.utc)
        
        return session
    
    async def update_session(
        self,
        session_id: str,
        data: Optional[Dict[str, Any]] = None,
        extend_expiration: bool = False
    ) -> Optional[SessionData]:
        """
            Update a session's data and/or extend its expiration.
            
            :param session_id: The session identifier.
            :param data: New session data to merge.
            :param extend_expiration: If True, reset the expiration timer.
            
            :returns: The updated SessionData if found, None otherwise.
        """
        session = self._sessions.get(session_id)
        
        if session is None:
            return None
        
        # Check expiration
        if session.is_expired:
            del self._sessions[session_id]
            return None
        
        # Update data
        if data is not None:
            session.data.update(data)
        
        # Update last accessed
        session.last_accessed = datetime.now(timezone.utc)
        
        # Extend expiration if requested
        if extend_expiration and self._default_expiration is not None:
            session.expires_at = datetime.now(timezone.utc) + timedelta(
                seconds=self._default_expiration
            )
        
        return session
    
    async def delete_session(self, session_id: str) -> bool:
        """
            Delete a session.
            
            :param session_id: The session identifier.
            
            :returns: True if the session was deleted, False if not found.
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False
    
    async def delete_sessions_for_principal(self, principal_id: str) -> int:
        """
            Delete all sessions for a given principal.
            
            :param principal_id: The principal identifier.
            
            :returns: The number of sessions deleted.
        """
        sessions_to_delete = [
            sid for sid, session in self._sessions.items()
            if session.principal_id == principal_id
        ]
        
        for sid in sessions_to_delete:
            del self._sessions[sid]
        
        return len(sessions_to_delete)
    
    def get_session_count(self) -> int:
        """
            Get the total number of sessions in the store.
            
            :returns: The number of sessions.
        """
        return len(self._sessions)
    
    def clear_all_sessions(self) -> int:
        """
            Clear all sessions from the store.
            
            :returns: The number of sessions cleared.
        """
        count = len(self._sessions)
        self._sessions.clear()
        return count




class SessionAuthenticator:
    """
        Session-based authentication implementation.
        
        This authenticator implements session-based authentication using
        secure cookies. It supports:
        
        - Secure session ID generation using cryptographic randomness
        - Configurable session expiration
        - Session renewal on activity
        - Secure cookie attributes (HttpOnly, Secure, SameSite)
        
        The authentication flow is:
        1. Check for session cookie in the request
        2. Validate the session against the SessionStore
        3. Return SUCCESS with context or FAILURE with error
        
        Example usage::
        
            session_store = InMemorySessionStore(default_expiration=3600)
            authenticator = SessionAuthenticator(
                session_store=session_store,
                cookie_name="session_id",
                cookie_attributes=CookieAttributes(secure=True, http_only=True)
            )
            
            result = await authenticator.authenticate(request)
            if result.status == AuthenticationStatus.SUCCESS:
                principal = result.context.principal
        
        :param session_store: The store for session persistence.
        :param cookie_name: Name of the session cookie.
        :param cookie_attributes: Security attributes for the cookie.
        :param renew_on_access: If True, extend session expiration on each access.
    """
    
    def __init__(
        self,
        session_store: SessionStore,
        cookie_name: str = "session_id",
        cookie_attributes: Optional[CookieAttributes] = None,
        renew_on_access: bool = True
    ):
        """
            Initialize the SessionAuthenticator.
            
            :param session_store: The store for session persistence.
            :param cookie_name: Name of the session cookie. Defaults to "session_id".
            :param cookie_attributes: Security attributes for the cookie.
                                     Defaults to secure settings.
            :param renew_on_access: If True, extend session expiration on each access.
                                   Defaults to True.
        """
        self._session_store = session_store
        self._cookie_name = cookie_name
        self._cookie_attributes = cookie_attributes or CookieAttributes()
        self._renew_on_access = renew_on_access
    
    @property
    def scheme(self) -> str:
        """
            Return the authentication scheme identifier.
            
            :returns: The string "Session".
        """
        return "Session"
    
    @property
    def cookie_name(self) -> str:
        """
            Return the session cookie name.
            
            :returns: The configured cookie name.
        """
        return self._cookie_name
    
    @property
    def cookie_attributes(self) -> CookieAttributes:
        """
            Return the cookie attributes.
            
            :returns: The configured CookieAttributes.
        """
        return self._cookie_attributes
    
    @property
    def session_store(self) -> SessionStore:
        """
            Return the session store.
            
            :returns: The configured SessionStore.
        """
        return self._session_store
    
    def can_handle(self, request: Any) -> bool:
        """
            Check if this authenticator can handle the given request.
            
            This method checks if the request contains a session cookie.
            
            :param request: The HTTP request object to examine.
            
            :returns: True if the request has a session cookie, False otherwise.
        """
        session_id = self._extract_session_id(request)
        return session_id is not None
    
    async def authenticate(self, request: Any) -> AuthenticationResult:
        """
            Attempt to authenticate the request using session authentication.
            
            This method:
            1. Extracts the session ID from the cookie
            2. Validates the session against the SessionStore
            3. Optionally renews the session expiration
            4. Returns the appropriate AuthenticationResult
            
            :param request: The HTTP request containing the session cookie.
            
            :returns: An AuthenticationResult with:
                     - SUCCESS and context if session is valid
                     - FAILURE with error if session is invalid or expired
                     - SKIP if no session cookie present
        """
        session_id = self._extract_session_id(request)
        
        # No session cookie - skip this authenticator
        if session_id is None:
            return AuthenticationResult(status=AuthenticationStatus.SKIP)
        
        # Empty session ID
        if session_id.strip() == "":
            return AuthenticationResult(
                status=AuthenticationStatus.FAILURE,
                error_code="invalid_session",
                error_description="Empty session identifier"
            )
        
        # Retrieve session from store
        session = await self._session_store.get_session(session_id)
        
        if session is None:
            return self._session_invalid_response()
        
        # Check if session is expired
        if session.is_expired:
            # Clean up the expired session
            await self._session_store.delete_session(session_id)
            return self._session_expired_response()
        
        # Renew session if configured
        if self._renew_on_access:
            await self._session_store.update_session(
                session_id,
                extend_expiration=True
            )
        
        # Success - return context with principal
        return AuthenticationResult(
            status=AuthenticationStatus.SUCCESS,
            context=AuthenticationContext(
                principal=session.principal,
                scheme=self.scheme,
                expires_at=session.expires_at,
                attributes={
                    "session_id": session.session_id,
                    "session_data": session.data,
                    "created_at": session.created_at.isoformat(),
                    "last_accessed": session.last_accessed.isoformat()
                }
            )
        )
    
    async def create_session(
        self,
        principal: Principal,
        expires_in: Optional[int] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> tuple:
        """
            Create a new session for the given principal.
            
            This method creates a session in the store and returns both
            the session data and the Set-Cookie header value.
            
            :param principal: The authenticated principal.
            :param expires_in: Session lifetime in seconds.
            :param data: Optional initial session data.
            
            :returns: A tuple of (SessionData, Set-Cookie header value).
        """
        session = await self._session_store.create_session(
            principal=principal,
            expires_in=expires_in,
            data=data
        )
        
        # Calculate max_age for cookie
        max_age = None
        if session.expires_at is not None:
            delta = session.expires_at - datetime.now(timezone.utc)
            max_age = int(delta.total_seconds())
        
        # Create cookie attributes with max_age
        cookie_attrs = CookieAttributes(
            http_only=self._cookie_attributes.http_only,
            secure=self._cookie_attributes.secure,
            same_site=self._cookie_attributes.same_site,
            path=self._cookie_attributes.path,
            domain=self._cookie_attributes.domain,
            max_age=max_age
        )
        
        cookie_header = cookie_attrs.to_cookie_string(
            self._cookie_name,
            session.session_id
        )
        
        return session, cookie_header
    
    async def invalidate_session(self, session_id: str) -> tuple:
        """
            Invalidate a session and return the clear cookie header.
            
            :param session_id: The session identifier to invalidate.
            
            :returns: A tuple of (success boolean, Set-Cookie header to clear).
        """
        success = await self._session_store.delete_session(session_id)
        clear_cookie = self._cookie_attributes.to_clear_cookie_string(
            self._cookie_name
        )
        return success, clear_cookie
    
    async def invalidate_all_sessions(self, principal_id: str) -> tuple:
        """
            Invalidate all sessions for a principal.
            
            :param principal_id: The principal identifier.
            
            :returns: A tuple of (count deleted, Set-Cookie header to clear).
        """
        count = await self._session_store.delete_sessions_for_principal(
            principal_id
        )
        clear_cookie = self._cookie_attributes.to_clear_cookie_string(
            self._cookie_name
        )
        return count, clear_cookie
    
    def _extract_session_id(self, request: Any) -> Optional[str]:
        """
            Extract the session ID from the request cookies.
            
            This method handles different request object types by checking
            for common cookie access patterns.
            
            :param request: The HTTP request object.
            
            :returns: The session ID or None if not present.
        """
        # Handle dict-like request objects (e.g., test mocks)
        if isinstance(request, dict):
            cookies = request.get("cookies", {})
            if isinstance(cookies, dict):
                return cookies.get(self._cookie_name)
            return None
        
        # Handle request objects with cookies attribute
        if hasattr(request, "cookies"):
            cookies = request.cookies
            if isinstance(cookies, dict):
                return cookies.get(self._cookie_name)
            elif hasattr(cookies, "get"):
                return cookies.get(self._cookie_name)
        
        return None
    
    def _session_invalid_response(self) -> AuthenticationResult:
        """
            Create a response for invalid session.
            
            :returns: An AuthenticationResult with FAILURE status.
        """
        return AuthenticationResult(
            status=AuthenticationStatus.FAILURE,
            error_code="invalid_session",
            error_description="Session not found or invalid"
        )
    
    def _session_expired_response(self) -> AuthenticationResult:
        """
            Create a response for expired session.
            
            :returns: An AuthenticationResult with FAILURE status.
        """
        return AuthenticationResult(
            status=AuthenticationStatus.FAILURE,
            error_code="session_expired",
            error_description="Session has expired"
        )


def generate_secure_session_id(length: int = 32) -> str:
    """
        Generate a cryptographically secure session ID.
        
        This utility function creates a random session ID using
        Python's secrets module for cryptographic security.
        
        :param length: The length of the session ID in bytes.
        
        :returns: A hex-encoded random session ID.
    """
    return secrets.token_hex(length)
