"""
.. module:: csrf
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Cross-Site Request Forgery (CSRF) protection primitives, ASGI
        middleware, and templating context processor.

.. moduleauthor:: Automation Mojo LLC

This module provides a stateless, synchronizer-token style CSRF protection
suite for downstream web applications. The token is an HMAC-SHA256 of a
session identifier with a server-side secret key and is therefore
deterministically reproducible from the session id alone — no separate
storage is required.

Components:

    - :class:`CSRFTokenManager` — generates and validates tokens for a given
      session identifier using an application-level secret key.
    - :class:`CSRFMiddleware` — ASGI middleware that requires a valid CSRF
      token on unsafe HTTP methods (configurable; defaults to
      ``POST``/``PUT``/``PATCH``/``DELETE``). Token transport defaults to
      the ``X-CSRF-Token`` header. Subclasses may override
      :meth:`CSRFMiddleware._extract_form_token` to support
      ``application/x-www-form-urlencoded`` request bodies.
    - :func:`make_csrf_context_processor` — factory that returns a context
      processor compatible with :class:`automojo.webworks.templating.context.ContextProcessorRegistry`.
      The processor injects ``csrf_token`` into the template context when
      a session identifier is present in the incoming context.

Token transport
---------------

The middleware extracts the candidate token from the ``X-CSRF-Token``
header by default. This is the recommended transport for AJAX/fetch
calls and works without inspecting the request body. For traditional
``<form>`` posts, applications may either:

    1. Submit the token via JavaScript using the ``X-CSRF-Token`` header.
    2. Subclass :class:`CSRFMiddleware` and override
       :meth:`CSRFMiddleware._extract_form_token` to read the token from
       a form-encoded body field. Body parsing is intentionally not done
       in the base middleware so applications can choose their own body
       buffering / replay strategy.

Threat model
------------

This module mitigates the standard "submitting state-changing requests
on behalf of an authenticated user" CSRF attack. It assumes:

    - The application uses cookie-bound sessions (so the session identifier
      is determined by the same-origin cookie — what an attacker cannot
      replicate cross-origin).
    - The CSRF secret key is held confidential by the server and rotated
      out-of-band when compromised.
    - HTTPS is in effect for production deployments.

It is *not* a substitute for ``SameSite`` cookies, ``Origin`` header
checks, or output-side defences (CSP, HTML escaping). It complements
those.
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


import base64
import hashlib
import hmac
import json
import logging
import secrets

from typing import Any, Awaitable, Callable, Dict, Optional, Set


# Type aliases for ASGI callables — match the conventions in
# automojo.webworks.authentication.middleware so wiring is uniform.
ReceiveCallable = Callable[[], Awaitable[Dict[str, Any]]]
SendCallable = Callable[[Dict[str, Any]], Awaitable[None]]
ASGIApplication = Callable[
    [Dict[str, Any], ReceiveCallable, SendCallable],
    Awaitable[None]
]


DEFAULT_HEADER_NAME = "X-CSRF-Token"
DEFAULT_FORM_FIELD_NAME = "csrf_token"
DEFAULT_UNSAFE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


# Module-level logger used by free functions and the
# :class:`CSRFTokenManager`. The :class:`CSRFMiddleware` keeps its
# own configurable ``self._logger`` so applications can route
# CSRF audit lines to a dedicated handler — this module logger is
# the default fallback.
logger = logging.getLogger(__name__)


class CSRFError(Exception):
    """
        Raised when CSRF token generation or validation fails for a reason
        the caller should treat as a programming or configuration error
        rather than a normal "missing/invalid token" outcome.

        Routine "no token supplied" or "token did not match" results from
        :meth:`CSRFTokenManager.validate` are reported by returning
        ``False``, not by raising. ``CSRFError`` is reserved for cases such
        as an empty secret key or a malformed token argument.
    """

    pass


class CSRFTokenManager:
    """
        Generates and validates HMAC-based CSRF tokens.

        Tokens are derived deterministically from the session identifier
        and a server-side secret key, so neither the manager nor the
        application needs to persist the token. A token is considered
        valid for a given session when it equals
        ``HMAC-SHA256(secret_key, session_id)`` encoded as URL-safe base64
        without padding.

        :param secret_key: Server-side secret key used to sign tokens.
                           Must be a non-empty ``str`` or ``bytes``. Treat
                           this value as sensitive material — it grants
                           the ability to forge CSRF tokens for any
                           session.
    """

    def __init__(self, secret_key):
        """
            Construct a token manager bound to a secret key.

            :param secret_key: Server-side secret key used to sign tokens.

            :raises CSRFError: When the secret key is empty.
        """
        if secret_key is None:
            raise CSRFError("CSRF secret_key is required")

        if isinstance(secret_key, str):
            secret_bytes = secret_key.encode("utf-8")
        elif isinstance(secret_key, (bytes, bytearray)):
            secret_bytes = bytes(secret_key)
        else:
            raise CSRFError("CSRF secret_key must be str or bytes")

        if len(secret_bytes) == 0:
            raise CSRFError("CSRF secret_key must not be empty")

        self._secret_bytes = secret_bytes
        return

    def generate(self, session_id: str) -> str:
        """
            Generate a CSRF token for the supplied session identifier.

            :param session_id: Identifier of the session for which the
                               token is being generated.

            :returns: A URL-safe base64-encoded token string suitable for
                      embedding in HTML forms or HTTP headers.
            :raises CSRFError: When ``session_id`` is empty or not a string.
        """
        if session_id is None:
            raise CSRFError("session_id is required to generate a CSRF token")

        if not isinstance(session_id, str):
            raise CSRFError("session_id must be a string")

        if len(session_id) == 0:
            raise CSRFError("session_id must not be empty")

        digest = hmac.new(
            key=self._secret_bytes,
            msg=session_id.encode("utf-8"),
            digestmod=hashlib.sha256
        ).digest()

        token = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
        return token

    def validate(self, session_id: Optional[str], token: Optional[str]) -> bool:
        """
            Validate a CSRF token against the expected value for a session.

            Comparison is performed with :func:`secrets.compare_digest` to
            avoid leaking timing information about partial matches. A
            ``None`` or empty value for either argument is treated as an
            invalid pairing and yields ``False`` rather than raising.

            :param session_id: Identifier of the session the token was
                               supposedly generated for.
            :param token: Candidate token supplied by the client.

            :returns: ``True`` when the token matches the expected value
                      for ``session_id``, ``False`` otherwise.
        """
        if session_id is None or not isinstance(session_id, str):
            return False
        if len(session_id) == 0:
            return False

        if token is None or not isinstance(token, str):
            return False
        if len(token) == 0:
            return False

        try:
            expected = self.generate(session_id)
        except CSRFError as exc:
            # Generation should only fail when ``session_id`` is
            # malformed in a way ``validate``'s up-front guard didn't
            # catch, or when the secret key has been mis-configured.
            # Either case is operator-visible.
            logger.warning(
                "CSRF validate: token generation failed for session_id-prefix=%s: %s",
                session_id[:8] if isinstance(session_id, str) else "<n/a>",
                exc,
            )
            return False

        is_valid = secrets.compare_digest(expected, token)
        return is_valid


# Type alias for the session_id resolver callable.
SessionIdResolver = Callable[[Dict[str, Any]], Optional[str]]


def cookie_session_id_resolver(cookie_name: str) -> SessionIdResolver:
    """
        Build a session-id resolver that reads the session identifier from
        a request cookie.

        The returned callable inspects the ASGI scope's ``headers`` list
        for a ``Cookie`` header and parses the named cookie out of it.

        :param cookie_name: Name of the session cookie issued by the
                            application's session blueprint.

        :returns: A callable suitable for use as the ``session_id_resolver``
                  argument of :class:`CSRFMiddleware`.
        :raises CSRFError: When ``cookie_name`` is empty.
    """
    if cookie_name is None or len(str(cookie_name)) == 0:
        raise CSRFError("cookie_name is required")

    target_name = str(cookie_name)

    def resolver(scope: Dict[str, Any]) -> Optional[str]:
        headers = scope.get("headers", []) or []
        cookie_header_value = None

        for header_pair in headers:
            if not isinstance(header_pair, (list, tuple)):
                continue
            if len(header_pair) < 2:
                continue

            name_bytes = header_pair[0]
            value_bytes = header_pair[1]

            if isinstance(name_bytes, (bytes, bytearray)):
                name = bytes(name_bytes).decode("latin-1").lower()
            else:
                name = str(name_bytes).lower()

            if name != "cookie":
                continue

            if isinstance(value_bytes, (bytes, bytearray)):
                cookie_header_value = bytes(value_bytes).decode("latin-1")
            else:
                cookie_header_value = str(value_bytes)
            break

        if cookie_header_value is None:
            return None

        for pair in cookie_header_value.split(";"):
            pair = pair.strip()
            if "=" not in pair:
                continue

            name, _, value = pair.partition("=")
            name = name.strip()
            value = value.strip()

            if name == target_name and len(value) > 0:
                return value

        return None

    return resolver


class CSRFMiddleware:
    """
        ASGI middleware that enforces CSRF token validation on unsafe
        HTTP methods.

        The middleware lets requests using safe methods (GET, HEAD,
        OPTIONS, TRACE by default) pass through unchanged. For unsafe
        methods (POST, PUT, PATCH, DELETE by default) it:

            1. Resolves the session identifier from the request via the
               configured ``session_id_resolver``.
            2. Extracts the candidate token from the configured header
               (``X-CSRF-Token`` by default), falling back to the
               :meth:`_extract_form_token` hook if the header is absent.
            3. Validates the token against the session id using the
               configured :class:`CSRFTokenManager`.

        On validation failure the middleware short-circuits the pipeline
        and returns a ``403 Forbidden`` JSON response. On success the
        request is forwarded to the wrapped application unchanged.

        :param app: Wrapped ASGI application.
        :param token_manager: :class:`CSRFTokenManager` used for validation.
        :param session_id_resolver: Callable that, given the ASGI scope,
                                    returns the session identifier or
                                    ``None``.
        :param header_name: HTTP header that carries the candidate token.
                            Defaults to ``X-CSRF-Token``.
        :param unsafe_methods: Iterable of HTTP method names that require
                               token validation. Defaults to
                               ``{"POST", "PUT", "PATCH", "DELETE"}``.
        :param exempt_paths: Optional set of exact request paths that
                             bypass validation entirely (e.g. webhook
                             endpoints with their own signing scheme).
        :param logger: Logger used for diagnostic messages. When ``None``
                       a module-default logger is used.
    """

    def __init__(
        self,
        app: ASGIApplication,
        token_manager: CSRFTokenManager,
        session_id_resolver: SessionIdResolver,
        header_name: str = DEFAULT_HEADER_NAME,
        unsafe_methods: Optional[Set[str]] = None,
        exempt_paths: Optional[Set[str]] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
            Construct the middleware.

            :param app: Wrapped ASGI application.
            :param token_manager: Token manager used for validation.
            :param session_id_resolver: Callable returning the current
                                        session identifier from the scope.
            :param header_name: Header name used to transport the token.
            :param unsafe_methods: HTTP methods that require validation.
            :param exempt_paths: Request paths that bypass validation.
            :param logger: Logger for diagnostic messages.

            :raises CSRFError: When required arguments are missing.
        """
        if app is None:
            raise CSRFError("app is required")
        if token_manager is None:
            raise CSRFError("token_manager is required")
        if session_id_resolver is None:
            raise CSRFError("session_id_resolver is required")

        self._app = app
        self._token_manager = token_manager
        self._session_id_resolver = session_id_resolver
        self._header_name = str(header_name or DEFAULT_HEADER_NAME)
        self._header_name_lower = self._header_name.lower()

        if unsafe_methods is None:
            self._unsafe_methods = set(DEFAULT_UNSAFE_METHODS)
        else:
            self._unsafe_methods = {
                str(method).upper() for method in unsafe_methods
            }

        if exempt_paths is None:
            self._exempt_paths = set()
        else:
            self._exempt_paths = {str(path) for path in exempt_paths}

        if logger is None:
            self._logger = logging.getLogger(__name__)
        else:
            self._logger = logger

        return

    @property
    def header_name(self) -> str:
        return self._header_name

    @property
    def unsafe_methods(self) -> Set[str]:
        return set(self._unsafe_methods)

    @property
    def exempt_paths(self) -> Set[str]:
        return set(self._exempt_paths)

    def _extract_header_token(self, scope: Dict[str, Any]) -> Optional[str]:
        """
            Read the candidate CSRF token from the configured request header.

            :param scope: ASGI scope dictionary for the current request.

            :returns: The header value as a string, or ``None`` when the
                      header is absent.
        """
        headers = scope.get("headers", []) or []
        for header_pair in headers:
            if not isinstance(header_pair, (list, tuple)):
                continue
            if len(header_pair) < 2:
                continue

            name_bytes = header_pair[0]
            value_bytes = header_pair[1]

            if isinstance(name_bytes, (bytes, bytearray)):
                name = bytes(name_bytes).decode("latin-1").lower()
            else:
                name = str(name_bytes).lower()

            if name != self._header_name_lower:
                continue

            if isinstance(value_bytes, (bytes, bytearray)):
                value = bytes(value_bytes).decode("latin-1")
            else:
                value = str(value_bytes)

            if len(value) > 0:
                return value

        return None

    def _extract_form_token(
        self,
        scope: Dict[str, Any],
        receive: ReceiveCallable
    ) -> Optional[str]:
        """
            Hook that subclasses may override to read the candidate token
            from a form-encoded request body.

            The base implementation returns ``None`` and does not consume
            the receive stream. Subclasses that override this method are
            responsible for buffering the body and re-yielding it to the
            wrapped application via a wrapped ``receive`` callable, since
            ASGI does not allow re-reading messages from the original
            ``receive``.

            :param scope: ASGI scope dictionary for the current request.
            :param receive: Original ASGI receive callable.

            :returns: The candidate token string, or ``None`` when not
                      present.
        """
        return None

    def _is_exempt(self, scope: Dict[str, Any]) -> bool:
        """
            Determine whether the current request bypasses CSRF validation.

            :param scope: ASGI scope dictionary for the current request.

            :returns: ``True`` when the request method is safe or the path
                      is exempt; ``False`` otherwise.
        """
        method = str(scope.get("method", "")).upper()
        if method not in self._unsafe_methods:
            return True

        path = scope.get("path", "")
        if path in self._exempt_paths:
            return True

        return False

    async def _send_forbidden(
        self,
        send: SendCallable,
        error_code: str,
        error_description: str
    ) -> None:
        """
            Send a 403 Forbidden response with a JSON body describing the
            CSRF failure.

            :param send: ASGI send callable.
            :param error_code: Short machine-readable error identifier.
            :param error_description: Human-readable error description.

            :returns: ``None``.
        """
        body_payload = {
            "error": error_code,
            "error_description": error_description,
        }
        body_bytes = json.dumps(body_payload).encode("utf-8")

        start_message = {
            "type": "http.response.start",
            "status": 403,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body_bytes)).encode("ascii")),
            ],
        }
        body_message = {
            "type": "http.response.body",
            "body": body_bytes,
            "more_body": False,
        }

        await send(start_message)
        await send(body_message)
        return

    async def __call__(
        self,
        scope: Dict[str, Any],
        receive: ReceiveCallable,
        send: SendCallable
    ) -> None:
        """
            ASGI entry point: validate the CSRF token on unsafe methods.

            :param scope: ASGI scope dictionary.
            :param receive: ASGI receive callable.
            :param send: ASGI send callable.

            :returns: ``None``.
        """
        if scope.get("type") != "http":
            await self._app(scope, receive, send)
            return

        if self._is_exempt(scope):
            await self._app(scope, receive, send)
            return

        session_id = self._session_id_resolver(scope)
        if session_id is None or len(session_id) == 0:
            self._logger.debug(
                "CSRF rejected: no session identifier resolved for path %r",
                scope.get("path", "")
            )
            await self._send_forbidden(
                send=send,
                error_code="csrf_missing_session",
                error_description="No active session for CSRF validation."
            )
            return

        token = self._extract_header_token(scope)
        if token is None:
            token = self._extract_form_token(scope, receive)

        if token is None:
            self._logger.debug(
                "CSRF rejected: no token presented for path %r",
                scope.get("path", "")
            )
            await self._send_forbidden(
                send=send,
                error_code="csrf_token_missing",
                error_description="No CSRF token was supplied with the request."
            )
            return

        is_valid = self._token_manager.validate(session_id, token)
        if not is_valid:
            self._logger.debug(
                "CSRF rejected: token validation failed for path %r",
                scope.get("path", "")
            )
            await self._send_forbidden(
                send=send,
                error_code="csrf_token_invalid",
                error_description="The CSRF token did not match this session."
            )
            return

        await self._app(scope, receive, send)
        return


def make_csrf_context_processor(
    token_manager: CSRFTokenManager,
    session_id_key: str = "session_id",
    token_key: str = "csrf_token"
) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """
        Build a context processor that injects a CSRF token for the
        current session into the template context.

        The returned callable expects the rendering context to include the
        session identifier under ``session_id_key``. When that key is
        present and non-empty, the processor returns
        ``{token_key: <generated_token>}``. When the session identifier is
        absent the processor returns an empty dict so anonymous renders
        succeed without a token.

        :param token_manager: :class:`CSRFTokenManager` that will sign
                              tokens.
        :param session_id_key: Context key under which the caller stores
                               the session identifier.
        :param token_key: Context key under which the processor exposes
                          the generated token.

        :returns: A callable suitable for registration with
                  :class:`automojo.webworks.templating.context.ContextProcessorRegistry`.
    """

    def processor(context: Dict[str, Any]) -> Dict[str, Any]:
        session_id = None
        if isinstance(context, dict):
            session_id = context.get(session_id_key)

        if session_id is None:
            return {}

        if not isinstance(session_id, str):
            return {}

        if len(session_id) == 0:
            return {}

        token = token_manager.generate(session_id)
        return {token_key: token}

    return processor
