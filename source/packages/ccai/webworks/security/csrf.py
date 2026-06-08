"""
.. module:: csrf
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Cross-Site Request Forgery (CSRF) protection primitives, ASGI
        middleware, and templating context processor.

.. moduleauthor:: Code Craft AI LLC

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
      the ``X-CSRF-Token`` header, with built-in fallback to a hidden
      ``csrf_token`` field in ``application/x-www-form-urlencoded``
      request bodies. Subclasses may override
      :meth:`CSRFMiddleware._extract_form_token` to support additional
      body shapes (e.g. ``multipart/form-data``).
    - :func:`make_csrf_context_processor` — factory that returns a context
      processor compatible with :class:`ccai.webworks.templating.context.ContextProcessorRegistry`.
      The processor injects ``csrf_token`` into the template context when
      a session identifier is present in the incoming context.

Token transport
---------------

The middleware extracts the candidate token from the ``X-CSRF-Token``
header first. This is the recommended transport for AJAX/fetch calls
and works without inspecting the request body. When the header is
absent on an unsafe method, the middleware also looks at the request
body: for ``application/x-www-form-urlencoded`` posts it parses out a
hidden ``csrf_token`` field, buffers the body, and replays it to the
wrapped application via a wrapped ``receive`` callable so the
downstream handler can still read its form fields. The maximum body
size that the middleware is willing to buffer is bounded by
``max_form_body_bytes`` (64 KiB by default); requests exceeding that
limit skip form-token extraction and must use the header transport.

Subclasses may override :meth:`CSRFMiddleware._extract_form_token` to
add support for other body shapes (e.g. ``multipart/form-data``). The
override returns a ``(token, replay_receive)`` tuple — see the method
docstring for the contract.

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

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


import base64
import hashlib
import hmac
import json
import logging
import secrets

from typing import Any, Awaitable, Callable, Dict, Optional, Set, Tuple
from urllib.parse import parse_qsl


# Type aliases for ASGI callables — match the conventions in
# ccai.webworks.authentication.middleware so wiring is uniform.
ReceiveCallable = Callable[[], Awaitable[Dict[str, Any]]]
SendCallable = Callable[[Dict[str, Any]], Awaitable[None]]
ASGIApplication = Callable[
    [Dict[str, Any], ReceiveCallable, SendCallable],
    Awaitable[None]
]


DEFAULT_HEADER_NAME = "X-CSRF-Token"
DEFAULT_FORM_FIELD_NAME = "csrf_token"
DEFAULT_UNSAFE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})

# Content-Type prefix that the base middleware will parse as a form
# body when looking for a token. The match is on the prefix only so
# that explicit charset suffixes (e.g.
# ``application/x-www-form-urlencoded; charset=utf-8``) still match.
FORM_URLENCODED_CONTENT_TYPE = "application/x-www-form-urlencoded"

# Default ceiling on the request body size the middleware will buffer
# for form-token extraction. CSRF-protected dashboard forms are tiny
# in practice (a few KiB at most); this cap protects the middleware
# from being asked to buffer large file uploads or pathological
# request bodies just to look for a hidden field.
DEFAULT_MAX_FORM_BODY_BYTES = 65536

# Sentinel ASGI message-type strings; mirrors the constants in
# :mod:`ccai.webworks.asgi.constants` but kept local so this
# module remains free of cross-module imports inside the security
# subtree.
_HTTP_REQUEST_MESSAGE_TYPE = "http.request"
_HTTP_DISCONNECT_MESSAGE_TYPE = "http.disconnect"


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
               (``X-CSRF-Token`` by default). If the header is absent
               and the request body is
               ``application/x-www-form-urlencoded``, the middleware
               buffers the body, parses out the hidden ``csrf_token``
               field (configurable via ``form_field_name``), and
               wraps the ``receive`` callable so the downstream
               application still observes the original body. Other
               body shapes (e.g. multipart) fall through to the
               :meth:`_extract_form_token` hook for subclasses.
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
        :param form_field_name: Name of the form field that carries the
                                token in
                                ``application/x-www-form-urlencoded``
                                bodies. Defaults to ``csrf_token``.
        :param max_form_body_bytes: Maximum number of body bytes the
                                    middleware will buffer when
                                    extracting a form-encoded token.
                                    Requests with a larger
                                    ``Content-Length`` skip form-body
                                    extraction and must transport the
                                    token via the header. Defaults to
                                    64 KiB.
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
        form_field_name: str = DEFAULT_FORM_FIELD_NAME,
        max_form_body_bytes: int = DEFAULT_MAX_FORM_BODY_BYTES,
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
            :param form_field_name: Form field name used to transport
                                    the token in form-encoded bodies.
            :param max_form_body_bytes: Maximum body size to buffer
                                        when looking for a form token.
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
        self._form_field_name = str(form_field_name or DEFAULT_FORM_FIELD_NAME)

        if max_form_body_bytes is None:
            self._max_form_body_bytes = DEFAULT_MAX_FORM_BODY_BYTES
        else:
            self._max_form_body_bytes = int(max_form_body_bytes)

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
    def form_field_name(self) -> str:
        return self._form_field_name

    @property
    def max_form_body_bytes(self) -> int:
        return self._max_form_body_bytes

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
                      header is absent or empty.
        """
        value = self._read_request_header(scope, self._header_name_lower)
        if value is None:
            return None

        if len(value) == 0:
            return None

        return value

    def _read_request_header(
        self,
        scope: Dict[str, Any],
        target_name_lower: str
    ) -> Optional[str]:
        """
            Read a single request header out of the ASGI scope.

            :param scope: ASGI scope dictionary for the current request.
            :param target_name_lower: Header name to look for, in
                                      lowercase.

            :returns: The decoded header value as a string, or ``None``
                      when the header is absent.
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

            if name != target_name_lower:
                continue

            if isinstance(value_bytes, (bytes, bytearray)):
                value = bytes(value_bytes).decode("latin-1")
            else:
                value = str(value_bytes)

            return value

        return None

    def _resolve_content_type(self, scope: Dict[str, Any]) -> str:
        """
            Read the ``Content-Type`` request header, normalised to
            lowercase. Returns an empty string when the header is
            absent.

            :param scope: ASGI scope dictionary for the current request.

            :returns: Lowercased content-type value, or empty string.
        """
        raw = self._read_request_header(scope, "content-type")
        if raw is None:
            return ""

        rtnval = raw.strip().lower()
        return rtnval

    def _resolve_content_length(self, scope: Dict[str, Any]) -> Optional[int]:
        """
            Read the ``Content-Length`` request header as an integer.

            :param scope: ASGI scope dictionary for the current request.

            :returns: The parsed length, or ``None`` when the header is
                      absent or malformed.
        """
        raw = self._read_request_header(scope, "content-length")
        if raw is None:
            return None

        try:
            rtnval = int(raw.strip())
        except ValueError:
            return None

        if rtnval < 0:
            return None

        return rtnval

    async def _buffer_request_body(
        self,
        receive: ReceiveCallable
    ) -> Optional[bytes]:
        """
            Drain the ASGI request stream into a bytes buffer, capped
            at ``self._max_form_body_bytes``.

            :param receive: Original ASGI receive callable.

            :returns: The accumulated body bytes when fully buffered
                      under the cap, or ``None`` when the cap was
                      exceeded mid-stream or a disconnect arrived
                      before the body completed.
        """
        chunks: list = []
        total = 0

        while True:
            message = await receive()
            message_type = message.get("type", "")

            if message_type == _HTTP_DISCONNECT_MESSAGE_TYPE:
                return None

            if message_type != _HTTP_REQUEST_MESSAGE_TYPE:
                continue

            body_chunk = message.get("body", b"") or b""
            if isinstance(body_chunk, (bytes, bytearray)) and len(body_chunk) > 0:
                chunk_bytes = bytes(body_chunk)
                total = total + len(chunk_bytes)
                if total > self._max_form_body_bytes:
                    return None
                chunks.append(chunk_bytes)

            more_body = message.get("more_body", False)
            if not more_body:
                break

        if len(chunks) == 0:
            buffered = b""
        elif len(chunks) == 1:
            buffered = chunks[0]
        else:
            buffered = b"".join(chunks)

        return buffered

    def _build_replay_receive(
        self,
        buffered_body: bytes,
        original_receive: ReceiveCallable
    ) -> ReceiveCallable:
        """
            Wrap ``original_receive`` with a callable that first replays
            ``buffered_body`` as a single ``http.request`` message, then
            delegates further calls to the original receive.

            :param buffered_body: Body bytes to replay on the first call.
            :param original_receive: The receive callable that this
                                     middleware originally consumed.

            :returns: An ASGI-compatible receive callable.
        """
        delivered = False

        async def replay_receive() -> Dict[str, Any]:
            nonlocal delivered
            if not delivered:
                delivered = True
                rtnmsg = {
                    "type": _HTTP_REQUEST_MESSAGE_TYPE,
                    "body": buffered_body,
                    "more_body": False,
                }
                return rtnmsg

            rtnmsg = await original_receive()
            return rtnmsg

        return replay_receive

    def _parse_form_token(self, body: bytes) -> Optional[str]:
        """
            Parse a buffered form-encoded body and return the value of
            the configured CSRF form field, if present.

            :param body: Buffered request body bytes.

            :returns: The token string when the form field is present,
                      ``None`` otherwise.
        """
        try:
            body_text = body.decode("utf-8")
        except UnicodeDecodeError:
            return None

        try:
            pairs = parse_qsl(
                body_text,
                keep_blank_values=True,
                strict_parsing=False
            )
        except ValueError:
            return None

        for name, value in pairs:
            if name == self._form_field_name:
                if value is None or len(value) == 0:
                    return None
                return value

        return None

    async def _extract_form_token(
        self,
        scope: Dict[str, Any],
        receive: ReceiveCallable
    ) -> Tuple[Optional[str], Optional[ReceiveCallable]]:
        """
            Extract the candidate CSRF token from the request body when
            the body is ``application/x-www-form-urlencoded``.

            The base implementation handles only form-urlencoded bodies.
            When invoked it:

                1. Inspects the ``Content-Type`` header. Non-form
                   content types short-circuit to ``(None, None)`` and
                   the body is left untouched for the downstream app.
                2. Inspects the ``Content-Length`` header. Bodies
                   declared larger than ``max_form_body_bytes`` are
                   skipped without consuming the receive stream.
                3. Drains the body into a bounded buffer, parses the
                   configured form field, and constructs a replacement
                   ``receive`` callable that replays the buffered body
                   before delegating to the original.

            Subclasses may override to support additional body shapes
            (e.g. ``multipart/form-data``). An override **must** return
            ``(None, None)`` when it does not consume the request body,
            and must return ``(token_or_None, replay_receive)`` when it
            does consume the body, so the wrapped application can still
            read the original payload.

            :param scope: ASGI scope dictionary for the current request.
            :param receive: Original ASGI receive callable.

            :returns: A ``(token, replay_receive)`` tuple. When the
                      body was not consumed, ``replay_receive`` is
                      ``None`` and the caller forwards the original
                      ``receive`` to the wrapped application.
        """
        content_type = self._resolve_content_type(scope)
        if not content_type.startswith(FORM_URLENCODED_CONTENT_TYPE):
            return None, None

        content_length = self._resolve_content_length(scope)
        if content_length is not None and content_length > self._max_form_body_bytes:
            self._logger.debug(
                "CSRF form-token extraction skipped: declared body length "
                "%d exceeds cap %d for path %r",
                content_length,
                self._max_form_body_bytes,
                scope.get("path", "")
            )
            return None, None

        buffered = await self._buffer_request_body(receive)
        if buffered is None:
            return None, None

        token = self._parse_form_token(buffered)
        replay_receive = self._build_replay_receive(buffered, receive)
        return token, replay_receive

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
        downstream_receive = receive

        if token is None:
            form_token, replay_receive = await self._extract_form_token(
                scope=scope,
                receive=receive
            )
            if form_token is not None:
                token = form_token
            if replay_receive is not None:
                downstream_receive = replay_receive

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

        await self._app(scope, downstream_receive, send)
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
                  :class:`ccai.webworks.templating.context.ContextProcessorRegistry`.
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
