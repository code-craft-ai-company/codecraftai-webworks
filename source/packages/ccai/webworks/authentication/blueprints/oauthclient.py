"""
.. module:: oauthclient
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: OAuth 2.0 client (relying-party) blueprint that drives
        kickoff / callback for one or more configured providers.

.. moduleauthor:: Code Craft AI LLC

This module hosts :class:`OAuthClientBlueprint` — the *client* side
of the OAuth 2.0 protocol, in contrast to the *server* side hosted
by :class:`ccai.webworks.authentication.blueprints.oauth2.OAuth2Blueprint`.
The blueprint exposes three endpoints that together implement
"sign in with Google / GitHub / Microsoft / Apple":

    * ``GET <base_path>/login`` — kickoff. Reads the ``provider``
      query parameter, generates a state value and (for OIDC
      providers) a nonce, signs them onto a short-lived cookie, and
      redirects the browser to the provider's authorization
      endpoint.
    * ``POST <base_path>/register`` — captcha-verified entry point
      for the registration flow. Returns a JSON body with the
      kickoff URL the client should redirect to with ``register=1``.
    * ``GET <base_path>/callback`` — provider redirect target.
      Validates the signed cookie, exchanges the authorization code
      for a token, parses the OIDC ``id_token`` (or fetches the
      userinfo endpoint for non-OIDC providers), hands the parsed
      claims to a site-supplied ``user_resolver`` to obtain a
      :class:`Principal`, optionally persists the token via
      ``token_persister``, calls
      :meth:`SessionAuthBlueprint.establish_session` to issue the
      site session cookie, and redirects to the configured success
      URL.

The pre-auth state cookie is the only durable carrier between
kickoff and callback: the user has no session yet when they click
"Sign in with Google", so the blueprint can't lean on
``SessionStore``. Instead it signs
``{provider, state, nonce, register}`` into a cookie via
:class:`ccai.webworks.security.signedserializer.TimedSerializer`
keyed off a site-supplied secret. The cookie is short-lived (10 minutes by
default) so a replayable artifact does not loiter; it is HttpOnly +
Secure + SameSite=Lax so it is not exposed to JavaScript and is not
sent on cross-site requests other than the top-level callback
redirect.

The blueprint owns the OAuth boilerplate (state-cookie signing,
provider-config lookup, authorization-URL construction, code
exchange, claims parsing, redirect-with-cookie response building,
error-code surfacing). The site keeps ownership of:

  * **Provider config** — ``provider_resolver`` returns the
    authlib-style kwargs dict for a provider name; sites typically
    point this at their own YAML loader / secrets-manager wrapper.
  * **Principal construction** — ``user_resolver`` translates the
    parsed OAuth claims into a :class:`Principal` and may
    short-circuit with a different redirect when business logic
    requires (e.g. send a local-credential user to
    ``/convert-user-to-oauth`` instead of silently shadowing their
    account).
  * **Token persistence** — ``token_persister`` is an optional
    callback the blueprint hands the issued token payload to so the
    site can store it for later refresh.
  * **State-cookie signing secret** — supplied via
    ``state_cookie_secret_resolver``; sites typically reuse their
    application CSRF secret here.
  * **Captcha verification** for the registration entry — supplied
    via ``captcha_verifier``.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


import json
import logging

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Type
from urllib.parse import urlencode

from ccai.webworks.authentication.blueprints.responses import AuthError
from ccai.webworks.authentication.blueprints.security import (
    SecurityBlueprint
)
from ccai.webworks.authentication.blueprints.session import (
    SessionAuthBlueprint
)
from ccai.webworks.authentication.core import Principal
from ccai.webworks.authentication.oauth import (
    OAuthClient,
    generate_oauth_nonce,
    generate_oauth_state,
)
from ccai.webworks.endpoints.doc import Doc
from ccai.webworks.routing.response import Response


logger = logging.getLogger(__name__)


# Canonical error codes surfaced on the failure-redirect's
# ``?error=<code>`` query parameter. Sites can pass any short
# string back from ``user_resolver``; this set is the vocabulary
# the blueprint itself emits.
ERROR_PROVIDER_UNAVAILABLE = "oauth_provider_unavailable"
ERROR_UNKNOWN_PROVIDER = "unknown_provider"
ERROR_PROVIDER_MISSING_ON_CALLBACK = "provider_missing_callback"
ERROR_TOKEN_PARSE_FAILED = "token_parse_failed"
ERROR_NO_TOKEN = "oauth_no_token"
ERROR_AUTHORIZATION_FAILED = "oauth_authorization_failed"
ERROR_NOT_CONFIGURED = "oauth_not_configured"


# Default state-cookie configuration. The ten-minute TTL matches the
# legacy site implementation: an OAuth round trip should complete in
# seconds, and giving it ten minutes leaves room for a slow human
# without keeping a replayable cookie around indefinitely.
DEFAULT_STATE_COOKIE_NAME = "ccai_oauth_state"
DEFAULT_STATE_COOKIE_MAX_AGE_SECONDS = 600
DEFAULT_STATE_COOKIE_SIGNATURE_SALT = "codecraftai-oauth-state-v1"


@dataclass
class OAuthCallbackResult:
    """
        Result returned by a site-supplied ``user_resolver``
        callable.

        Exactly one of :attr:`principal`, :attr:`error_code`, or
        :attr:`short_circuit_redirect_url` should be populated. The
        blueprint evaluates them in that order: a populated
        :attr:`error_code` short-circuits the flow with an error
        redirect; a populated
        :attr:`short_circuit_redirect_url` short-circuits with a
        plain redirect (no Set-Cookie, no error parameter); a
        populated :attr:`principal` is the success path.

        The success path additionally carries the ``user_id`` and
        ``provider_ref_id`` the blueprint forwards to the optional
        :attr:`token_persister`.

        :param principal: The :class:`Principal` to log in on
                          success. ``None`` on the failure or
                          short-circuit paths.
        :param error_code: Short, URL-safe error code on the failure
                           path. Surfaced to the browser as
                           ``?error=<code>``. ``None`` on success or
                           short-circuit.
        :param short_circuit_redirect_url: Absolute or site-relative
                                           URL the blueprint should
                                           redirect the browser to
                                           when business logic
                                           requires diverting the
                                           flow (e.g. a local-
                                           credential user trying to
                                           sign in via OAuth needs
                                           to land on
                                           ``/convert-user-to-oauth``
                                           rather than logging in).
        :param user_id: Site identifier for the resolved user, used
                        when invoking :attr:`token_persister`. Falls
                        back to :attr:`Principal.identifier` when
                        omitted.
        :param provider_ref_id: Provider-side identifier for the
                                user (typically the OIDC ``sub``
                                claim or the GitHub ``id``). Forwarded
                                to :attr:`token_persister` so the
                                site can index its token storage by
                                provider identity.
        :param extra_attributes: Optional extra attributes merged
                                 into the
                                 :class:`AuthenticationContext` on
                                 the success path.
    """

    principal: Optional[Principal] = None
    error_code: Optional[str] = None
    short_circuit_redirect_url: Optional[str] = None
    user_id: Optional[str] = None
    provider_ref_id: Optional[str] = None
    extra_attributes: Optional[Dict[str, Any]] = None


# Type aliases for the site-supplied callables. These are documented
# here rather than as ``Protocol`` classes because Python's import
# machinery makes inheriting from ``Protocol`` in a class attribute
# default value fragile when the type is generic.
ProviderResolver = Callable[[str], Optional[Dict[str, Any]]]
ProviderNameLister = Callable[[], List[str]]
UserResolver = Callable[
    [str, Dict[str, Any], bool, Any],
    OAuthCallbackResult,
]
TokenPersister = Callable[[str, str, str, Dict[str, Any]], None]
StateCookieSecretResolver = Callable[[], str]
CaptchaVerifier = Callable[[str], bool]
ProviderExtrasResolver = Callable[[str, bool], Dict[str, str]]


class OAuthClientBlueprint(SecurityBlueprint):
    """
        Blueprint for OAuth 2.0 *client* (relying-party) endpoints.

        Mounts three endpoints under :attr:`base_path`:

          * ``GET /login`` — kickoff redirect to the provider.
          * ``POST /register`` — captcha-verified registration intent.
          * ``GET /callback`` — provider redirect target.

        Each endpoint can be disabled via ``enabled_endpoints``.

        Class Attributes:
            base_path: Base URL path for all endpoints. Defaults to
                       ``"/auth/oauth"``. Sites that need to preserve
                       a legacy URL (e.g. ``"/oauth"``) override this
                       on their subclass.
            tags: Documentation tags applied to all endpoints.
            provider_resolver: Site-supplied callable that returns
                               the authlib-style kwargs dict for a
                               provider name, or ``None`` when the
                               provider is not configured.
            provider_name_lister: Site-supplied callable that returns
                                  the list of registered provider
                                  names. Used by the kickoff
                                  handler to distinguish "no
                                  providers configured" (all
                                  providers blocked) from "this
                                  particular provider is not
                                  configured" (typo or stale link).
            user_resolver: Site-supplied callable that translates
                           parsed OAuth claims into an
                           :class:`OAuthCallbackResult`. Receives
                           ``(provider_name, user_info,
                           is_register_flow, request)``.
            token_persister: Optional site-supplied callable that
                             persists the issued OAuth token payload
                             for later refresh. Receives
                             ``(user_id, provider_name,
                             provider_ref_id, token_payload)``.
            state_cookie_secret_resolver: Site-supplied callable
                                          that returns the secret
                                          used to sign / verify the
                                          pre-auth state cookie.
                                          Sites typically reuse their
                                          application CSRF secret.
            captcha_verifier: Optional site-supplied callable that
                              verifies the captcha token in the
                              registration postback body. When
                              ``None`` the registration endpoint is
                              effectively a no-op verifier — a
                              development-mode default.
            session_blueprint: The :class:`SessionAuthBlueprint`
                               subclass used to issue the session
                               cookie on success. Required.
            provider_extras_resolver: Optional site-supplied callable
                                      that returns provider-specific
                                      extras merged into the
                                      authorization URL (e.g.
                                      ``access_type=offline`` for
                                      Google). Receives
                                      ``(provider_name,
                                      is_register_flow)``.
            default_provider_name: Provider name used when the
                                   kickoff query string omits
                                   ``provider=``. Defaults to
                                   ``"google"``.
            state_cookie_name: Name of the signed state cookie.
            state_cookie_max_age_seconds: TTL for the state cookie.
            state_cookie_signature_salt: Namespace salt applied to the
                                         derived signing key.
            post_login_redirect_url: Location for the success
                                     redirect. Defaults to
                                     ``"/dashboard/"``.
            error_redirect_url: Location for the failure redirect.
                                The blueprint appends
                                ``?error=<code>``.
            scheme_label: ``scheme`` value recorded on the
                          :class:`AuthenticationContext`.
                          Defaults to ``"OAuth"``.
            csrf_exempt_paths: Read-only set of paths sites should
                               add to their CSRF middleware exempt
                               list. The registration endpoint is
                               POST and runs before any session
                               exists; sites populate their CSRF
                               middleware with this set so they
                               don't have to maintain a parallel
                               list.
    """

    base_path: str = "/auth/oauth"
    tags: List[str] = ["Authentication", "OAuth"]

    provider_resolver: Optional[ProviderResolver] = None
    provider_name_lister: Optional[ProviderNameLister] = None
    user_resolver: Optional[UserResolver] = None
    token_persister: Optional[TokenPersister] = None
    state_cookie_secret_resolver: Optional[StateCookieSecretResolver] = None
    captcha_verifier: Optional[CaptchaVerifier] = None
    session_blueprint: Optional[Type[SessionAuthBlueprint]] = None
    provider_extras_resolver: Optional[ProviderExtrasResolver] = None

    default_provider_name: str = "google"

    state_cookie_name: str = DEFAULT_STATE_COOKIE_NAME
    state_cookie_max_age_seconds: int = DEFAULT_STATE_COOKIE_MAX_AGE_SECONDS
    state_cookie_signature_salt: str = DEFAULT_STATE_COOKIE_SIGNATURE_SALT

    post_login_redirect_url: str = "/dashboard/"
    error_redirect_url: str = "/login"
    scheme_label: str = "OAuth"

    success_message_template: str = "Welcome — signed in via {provider}"

    # --- Class constants ---
    # Override these on a subclass to rebrand wire-format strings without
    # rewriting handler bodies. Module-level ``ERROR_*`` constants stay in
    # place for backward compatibility; the class attributes mirror them so
    # subclasses can override individual codes without touching the module.

    # OAuth client-side error codes (mirrored from module constants).
    PROVIDER_UNAVAILABLE_ERROR_CODE: str = ERROR_PROVIDER_UNAVAILABLE
    UNKNOWN_PROVIDER_ERROR_CODE: str = ERROR_UNKNOWN_PROVIDER
    PROVIDER_MISSING_ON_CALLBACK_ERROR_CODE: str = ERROR_PROVIDER_MISSING_ON_CALLBACK
    TOKEN_PARSE_FAILED_ERROR_CODE: str = ERROR_TOKEN_PARSE_FAILED
    NO_TOKEN_ERROR_CODE: str = ERROR_NO_TOKEN
    AUTHORIZATION_FAILED_ERROR_CODE: str = ERROR_AUTHORIZATION_FAILED
    NOT_CONFIGURED_ERROR_CODE: str = ERROR_NOT_CONFIGURED

    # Endpoint-disabled error code / message template
    ENDPOINT_DISABLED_ERROR_CODE: str = "endpoint_disabled"
    ENDPOINT_DISABLED_MESSAGE_TEMPLATE: str = "OAuth {} endpoint is disabled"

    # Captcha-related error codes
    MISSING_CAPTCHA_ERROR_CODE: str = "missing_captcha"
    CAPTCHA_FAILED_ERROR_CODE: str = "captcha_failed"

    # Cookie attribute literals
    COOKIE_PATH: str = "/"
    COOKIE_HTTPONLY_FLAG: str = "HttpOnly"
    COOKIE_SECURE_FLAG: str = "Secure"
    COOKIE_SAMESITE_LAX: str = "SameSite=Lax"
    COOKIE_EXPIRED_DATE: str = "Expires=Thu, 01 Jan 1970 00:00:00 GMT"
    COOKIE_MAX_AGE_ZERO: str = "Max-Age=0"
    COOKIE_PART_SEPARATOR: str = "; "
    COOKIE_HEADER_NAME: str = "Cookie"
    SET_COOKIE_HEADER: str = "Set-Cookie"
    LOCATION_HEADER: str = "Location"
    CONTENT_TYPE_HEADER: str = "Content-Type"
    JSON_CONTENT_TYPE_UTF8: str = "application/json; charset=utf-8"

    # URL leaves used by callback / kickoff URL builders
    CALLBACK_LEAF: str = "/callback"
    LOGIN_LEAF: str = "/login"
    REGISTER_LEAF: str = "/register"

    # Default scheme / host fallbacks for callback URL construction
    DEFAULT_SCHEME: str = "https"
    DEFAULT_HOST: str = "localhost"

    # Truthy values accepted on the kickoff query string ``register=``
    # parameter.
    REGISTER_FLAG_TRUTHY_VALUES: tuple = ("1", "true", "yes", "on")

    # Provider-id claim names attempted in order when the resolver does
    # not surface an explicit provider_ref_id.
    PROVIDER_ID_CLAIM_FALLBACKS: tuple = ("sub", "id", "user_id")

    # AuthenticationContext attribute key for the OAuth provider name.
    OAUTH_PROVIDER_ATTRIBUTE: str = "oauth_provider"

    # OAuth wire parameter names referenced by handlers
    OAUTH_PARAM_PROVIDER: str = "provider"
    OAUTH_PARAM_REGISTER: str = "register"
    OAUTH_PARAM_STATE: str = "state"
    OAUTH_PARAM_NONCE: str = "nonce"
    OAUTH_PARAM_CODE: str = "code"
    OAUTH_PARAM_ERROR: str = "error"
    OAUTH_PARAM_PROVIDER_ERROR: str = "provider_error"
    OAUTH_PARAM_CAPTCHA_RESPONSE: str = "captcha_response"
    OAUTH_PARAM_ID_TOKEN: str = "id_token"

    # Multi-Set-Cookie joining literal used when emitting two cookies
    # simultaneously on the wire.
    MULTI_SET_COOKIE_SEPARATOR: str = "\r\n"

    # --------------------------------------------------------------
    # State cookie helpers (sign / unsign / build / read).
    # --------------------------------------------------------------

    @classmethod
    def _build_state_serializer(cls):
        """
            Construct a :class:`TimedSerializer` keyed off the site's
            signing secret with the configured salt.

            :returns: A configured serializer instance, or ``None``
                      when no secret resolver is wired (the kickoff
                      handler treats this as
                      ``oauth_not_configured``).
        """
        # The signed state cookie is produced and consumed entirely by
        # webworks, so it uses the in-house
        # ``ccai.webworks.security.signedserializer`` rather than a
        # third-party signing library.
        from ccai.webworks.security.signedserializer import TimedSerializer

        if cls.state_cookie_secret_resolver is None:
            return None

        secret = cls.state_cookie_secret_resolver()

        serializer = TimedSerializer(
            secret_key=secret,
            salt=cls.state_cookie_signature_salt,
        )
        return serializer

    @classmethod
    def _sign_state_payload(cls, payload: Dict[str, Any]) -> Optional[str]:
        """
            Sign the OAuth state payload into a cookie value.

            :param payload: Dict containing at least ``provider`` and
                            ``state``. The full set of recognised
                            keys is
                            ``{"provider", "state", "nonce", "register"}``.

            :returns: The signed cookie value, or ``None`` when no
                      signing secret is wired.
        """
        serializer = cls._build_state_serializer()
        if serializer is None:
            return None

        rtnval = serializer.dumps(payload)
        return rtnval

    @classmethod
    def _unsign_state_payload(
        cls,
        cookie_value: str,
    ) -> Optional[Dict[str, Any]]:
        """
            Verify and parse an OAuth state cookie.

            :param cookie_value: Raw cookie value as it arrives on
                                 the callback request.

            :returns: The original payload dict on success, or
                      ``None`` when the cookie is missing, malformed,
                      expired, or signed with the wrong key. Callers
                      treat ``None`` as
                      ``token_parse_failed``.
        """
        if cookie_value is None:
            return None

        cookie_str = str(cookie_value).strip()
        if cookie_str == "":
            return None

        serializer = cls._build_state_serializer()
        if serializer is None:
            return None

        try:
            payload = serializer.loads(
                cookie_str,
                max_age=cls.state_cookie_max_age_seconds,
            )
        except Exception:
            logger.exception("OAuth state cookie failed verification.")
            return None

        if not isinstance(payload, dict):
            return None

        rtnval = payload
        return rtnval

    @classmethod
    def _build_state_set_cookie(cls, value: str) -> str:
        """
            Build the ``Set-Cookie`` header value for the signed
            state cookie.

            :param value: Signed cookie value to set.

            :returns: A complete ``Set-Cookie`` header string.
        """
        parts = [
            "{}={}".format(cls.state_cookie_name, value),
            "Path={}".format(cls.COOKIE_PATH),
            "Max-Age={}".format(cls.state_cookie_max_age_seconds),
            cls.COOKIE_HTTPONLY_FLAG,
            cls.COOKIE_SECURE_FLAG,
            cls.COOKIE_SAMESITE_LAX,
        ]

        rtnval = cls.COOKIE_PART_SEPARATOR.join(parts)
        return rtnval

    @classmethod
    def _build_state_clear_cookie(cls) -> str:
        """
            Build the ``Set-Cookie`` header value to clear the OAuth
            state cookie after a successful callback.

            :returns: A complete ``Set-Cookie`` header string.
        """
        parts = [
            "{}=".format(cls.state_cookie_name),
            "Path={}".format(cls.COOKIE_PATH),
            cls.COOKIE_MAX_AGE_ZERO,
            cls.COOKIE_EXPIRED_DATE,
            cls.COOKIE_HTTPONLY_FLAG,
            cls.COOKIE_SECURE_FLAG,
            cls.COOKIE_SAMESITE_LAX,
        ]

        rtnval = cls.COOKIE_PART_SEPARATOR.join(parts)
        return rtnval

    @classmethod
    def _read_state_cookie(cls, request: Any) -> str:
        """
            Read the raw OAuth state cookie value from an incoming
            request.

            Supports attribute-style cookie access (the typical
            webworks request shape) and falls back to parsing the
            ``Cookie`` header when only headers are exposed.

            :param request: Incoming HTTP request.

            :returns: The raw cookie value, or ``""`` when absent.
        """
        cookies_attr = getattr(request, "cookies", None)
        if isinstance(cookies_attr, dict):
            value = cookies_attr.get(cls.state_cookie_name)
            if value is not None:
                return str(value).strip()

        headers = getattr(request, "headers", None)
        cookie_header = ""
        if headers is not None and hasattr(headers, "get"):
            raw = headers.get(cls.COOKIE_HEADER_NAME) or headers.get(cls.COOKIE_HEADER_NAME.lower()) or ""
            cookie_header = str(raw)

        if cookie_header == "":
            return ""

        for chunk in cookie_header.split(";"):
            if "=" not in chunk:
                continue
            name, value = chunk.split("=", 1)
            if name.strip() == cls.state_cookie_name:
                return value.strip()

        return ""

    # --------------------------------------------------------------
    # Request-shape helpers.
    # --------------------------------------------------------------

    @classmethod
    def _read_query_param(cls, request: Any, name: str) -> str:
        """
            Read a single query parameter from an incoming request.

            Tolerant of the two shapes webworks adapters surface:
            attribute-style (``request.query_params``) and
            mapping-style (``request["query_params"]``).

            :param request: Incoming HTTP request.
            :param name: Query parameter name.

            :returns: The parameter value as a stripped string, or
                      ``""`` when absent.
        """
        query = getattr(request, "query_params", None)
        if query is None and isinstance(request, dict):
            query = request.get("query_params")

        if query is None:
            return ""

        if hasattr(query, "get"):
            raw = query.get(name)
            if raw is None:
                return ""
            return str(raw).strip()

        return ""

    @classmethod
    def _read_request_body(cls, request: Any) -> Dict[str, Any]:
        """
            Read the request body as a dict.

            Tries ``request.json()`` first, falls back to
            ``request.form()`` for traditional form-encoded posts.
            Empty / unparseable bodies yield an empty dict so the
            handler can branch on key presence rather than
            try/except.

            :param request: Incoming HTTP request.

            :returns: The parsed body as a dict (empty when
                      unparseable).
        """
        body: Dict[str, Any] = {}

        if hasattr(request, "json"):
            try:
                parsed = request.json()
            except Exception:
                parsed = None
            if isinstance(parsed, dict):
                body.update(parsed)
                return body

        if hasattr(request, "form"):
            try:
                form = request.form()
            except Exception:
                form = None
            if form is not None and hasattr(form, "keys"):
                for key in form.keys():
                    body[key] = form.get(key)

        return body

    @classmethod
    def _build_callback_url(
        cls,
        request: Any,
        provider_name: str,
    ) -> str:
        """
            Build the absolute callback URL for a provider.

            Uses the request's ``scheme`` and ``host`` so the URL
            carries the right host the provider should redirect back
            to. The path resolves against the blueprint's
            :attr:`base_path` plus ``"/callback"``.

            :param request: Incoming HTTP request.
            :param provider_name: Provider name to embed as a query
                                  parameter.

            :returns: A fully-qualified URL.
        """
        scheme = str(getattr(request, "scheme", cls.DEFAULT_SCHEME) or cls.DEFAULT_SCHEME)
        host = str(getattr(request, "host", "") or "")
        if host == "":
            host = cls.DEFAULT_HOST

        callback_path = "{}{}".format(cls._get_base_path() or "", cls.CALLBACK_LEAF)

        rtnval = "{}://{}{}?{}={}".format(
            scheme,
            host,
            callback_path,
            cls.OAUTH_PARAM_PROVIDER,
            provider_name,
        )
        return rtnval

    # --------------------------------------------------------------
    # Response builders.
    # --------------------------------------------------------------

    @classmethod
    def _build_redirect_response(
        cls,
        location: str,
        set_cookies: Optional[List[str]] = None,
    ) -> Response:
        """
            Build a 302 redirect :class:`Response`.

            Returns a real :class:`Response` (not a dict) so the
            webworks request dispatcher can pass it through unchanged
            — dict-shape returns get JSON-serialised by
            ``Dispatcher.dispatch`` and lose their status / headers.

            Multiple ``Set-Cookie`` headers are joined with ``\\r\\n``
            because the underlying :class:`Response` exposes a
            ``Dict[str, str]`` header surface; the joining string is
            recognised by most ASGI adapters as the boundary between
            distinct ``Set-Cookie`` lines on the wire. The blueprint
            emits at most two cookies simultaneously (the new session
            cookie and the OAuth state-clear cookie on the callback
            success path).

            :param location: The URL to redirect to.
            :param set_cookies: Optional list of ``Set-Cookie``
                                header values.

            :returns: A 302 :class:`Response` with the supplied
                      ``Location`` header (and joined ``Set-Cookie``
                      lines when provided).
        """
        headers: Dict[str, str] = {cls.LOCATION_HEADER: location}

        if set_cookies is not None:
            non_empty = [
                str(c).strip()
                for c in set_cookies
                if c is not None and str(c).strip() != ""
            ]
            if len(non_empty) > 0:
                headers[cls.SET_COOKIE_HEADER] = cls.MULTI_SET_COOKIE_SEPARATOR.join(non_empty)

        response = Response(status_code=302, headers=headers, body=b"")
        return response

    @classmethod
    def _build_error_redirect(
        cls,
        error_code: str,
        extra_query: Optional[Dict[str, str]] = None,
        set_cookies: Optional[List[str]] = None,
    ) -> Response:
        """
            Build a 302 redirect to :attr:`error_redirect_url` with
            ``?error=<code>`` and optional additional query
            parameters.

            :param error_code: Short, URL-safe error code.
            :param extra_query: Additional query parameters to merge.
            :param set_cookies: Optional ``Set-Cookie`` header values
                                to attach (e.g. the state-clear
                                cookie when the error arises after
                                the callback has already validated
                                state).

            :returns: A redirect :class:`Response`.
        """
        params: Dict[str, str] = {cls.OAUTH_PARAM_ERROR: str(error_code)}
        if extra_query is not None:
            for key, value in extra_query.items():
                if value is None:
                    continue
                params[str(key)] = str(value)

        encoded = urlencode(params)

        base = cls.error_redirect_url
        if "?" in base:
            location = "{}&{}".format(base, encoded)
        else:
            location = "{}?{}".format(base, encoded)

        rtnval = cls._build_redirect_response(
            location=location,
            set_cookies=set_cookies,
        )
        return rtnval

    @classmethod
    def _build_disabled_response(cls, endpoint_name: str) -> Response:
        """
            Build the 404 :class:`Response` returned when an endpoint
            is disabled via ``enabled_endpoints``.

            :param endpoint_name: Endpoint identifier used in the
                                  error description.

            :returns: A 404 :class:`Response` with a JSON body
                      carrying an ``endpoint_disabled``
                      :class:`AuthError`.
        """
        error = AuthError(
            error=cls.ENDPOINT_DISABLED_ERROR_CODE,
            error_description=cls.ENDPOINT_DISABLED_MESSAGE_TEMPLATE.format(endpoint_name),
        )
        rtnval = cls._build_auth_error_response(
            error=error,
            status_code=404,
        )
        return rtnval

    @classmethod
    def _build_auth_error_response(
        cls,
        error: AuthError,
        status_code: int,
    ) -> Response:
        """
            Build a JSON :class:`Response` carrying an
            :class:`AuthError` body.

            Replaces the dict-form return that
            :meth:`SecurityBlueprint.format_error` produces, which
            does not survive the request dispatcher (the dispatcher
            wraps non-Response returns in ``JSONResponse`` and
            ignores the ``status`` key).

            :param error: The :class:`AuthError` to surface.
            :param status_code: HTTP status code.

            :returns: A :class:`Response` with a JSON body and the
                      requested status code.
        """
        body_bytes = json.dumps(error.to_dict()).encode("utf-8")

        headers: Dict[str, str] = {
            cls.CONTENT_TYPE_HEADER: cls.JSON_CONTENT_TYPE_UTF8,
        }

        response = Response(
            status_code=status_code,
            headers=headers,
            body=body_bytes,
        )
        return response

    @classmethod
    def _build_json_response(
        cls,
        body: Any,
        status_code: int,
    ) -> Response:
        """
            Build a JSON :class:`Response` for handlers that emit
            structured JSON bodies (the ``register`` endpoint).

            :param body: JSON-serialisable Python object.
            :param status_code: HTTP status code.

            :returns: A :class:`Response` with the body
                      JSON-serialised and a
                      ``Content-Type: application/json`` header.
        """
        body_bytes = json.dumps(body).encode("utf-8")

        headers: Dict[str, str] = {
            cls.CONTENT_TYPE_HEADER: cls.JSON_CONTENT_TYPE_UTF8,
        }

        response = Response(
            status_code=status_code,
            headers=headers,
            body=body_bytes,
        )
        return response

    # --------------------------------------------------------------
    # Provider lookup and extras.
    # --------------------------------------------------------------

    @classmethod
    def _resolve_provider_extras(
        cls,
        provider_name: str,
        is_register_flow: bool,
    ) -> Dict[str, str]:
        """
            Resolve provider-specific authorization-URL extras.

            Sites override per-provider behaviour (e.g. Google's
            ``access_type=offline`` + ``prompt=consent`` on
            registration) by supplying a
            :attr:`provider_extras_resolver`. When no resolver is
            wired the blueprint emits no extras.

            :param provider_name: Provider name being kicked off.
            :param is_register_flow: ``True`` when the kickoff was
                                     triggered by the registration
                                     postback.

            :returns: Dict of extra query parameters to merge into
                      the authorization URL.
        """
        if cls.provider_extras_resolver is None:
            return {}

        try:
            extras = cls.provider_extras_resolver(
                provider_name,
                is_register_flow,
            )
        except Exception:
            logger.exception(
                "OAuth provider_extras_resolver raised for "
                "provider %r.",
                provider_name,
            )
            return {}

        if not isinstance(extras, dict):
            return {}

        rtnval = {str(k): str(v) for k, v in extras.items()}
        return rtnval

    @classmethod
    def _resolve_oauth_client(
        cls,
        provider_name: str,
    ) -> Optional[OAuthClient]:
        """
            Look up the configured provider via
            :attr:`provider_resolver` and construct a fresh
            :class:`OAuthClient`.

            :param provider_name: Provider name.

            :returns: A new :class:`OAuthClient`, or ``None`` when
                      the provider is not configured or the
                      configuration is invalid.
        """
        if cls.provider_resolver is None:
            return None

        try:
            config = cls.provider_resolver(provider_name)
        except Exception:
            logger.exception(
                "OAuth provider_resolver raised for provider %r.",
                provider_name,
            )
            return None

        if config is None:
            return None

        try:
            client = OAuthClient(
                provider_name=provider_name,
                provider_config=config,
            )
        except ValueError:
            logger.exception(
                "OAuth provider %r is configured but rejected at "
                "client construction time.",
                provider_name,
            )
            return None

        rtnval = client
        return rtnval

    # --------------------------------------------------------------
    # Endpoint: kickoff (GET /login).
    # --------------------------------------------------------------

    @classmethod
    @SecurityBlueprint.read(
        leaf="login",
        doc=Doc(
            summary="Start OAuth login",
            description="Generate the OAuth state cookie and "
                        "redirect the browser to the configured "
                        "provider's authorization endpoint."
        ),
        on_conflict="replace"
    )
    def kickoff(cls, request: Any) -> Dict[str, Any]:
        """
            Initiate the OAuth login flow with the named provider.

            Reads ``provider`` and ``register`` from the query
            string, builds an authorization URL, signs the
            ``{provider, state, nonce, register}`` payload onto a
            short-lived cookie, and returns a 302 redirect to the
            provider with the cookie attached.

            Failure modes redirect to :attr:`error_redirect_url`
            with one of:

              * ``oauth_provider_unavailable`` — no providers are
                configured at all.
              * ``unknown_provider`` — the requested provider is
                not in the site's provider map.
              * ``oauth_not_configured`` — no signing secret is
                wired (deployment misconfiguration).

            :param request: Incoming HTTP request.

            :returns: A response dictionary with ``status``,
                      ``body``, ``content_type``, and ``headers``
                      keys.
        """
        if not cls.is_endpoint_enabled("kickoff"):
            return cls._build_disabled_response("login")

        pre_error = cls.pre_authenticate(request)
        if pre_error is not None:
            response = cls._build_auth_error_response(error=pre_error, status_code=401)
            return response

        if cls.state_cookie_secret_resolver is None:
            logger.error(
                "OAuth kickoff: state_cookie_secret_resolver is "
                "not configured."
            )
            response = cls._build_error_redirect(
                error_code=cls.NOT_CONFIGURED_ERROR_CODE,
            )
            return response

        # Read provider name (default to ``default_provider_name``
        # when the query string omits it; this preserves the
        # legacy "/login-oauth-local" link shape that some sites'
        # button widgets emit).
        provider_name = cls._read_query_param(request, cls.OAUTH_PARAM_PROVIDER)
        if provider_name == "":
            provider_name = cls.default_provider_name

        register_raw = cls._read_query_param(request, cls.OAUTH_PARAM_REGISTER).lower()
        is_register_flow = register_raw in cls.REGISTER_FLAG_TRUTHY_VALUES

        client = cls._resolve_oauth_client(provider_name)
        if client is None:
            configured: List[str] = []
            if cls.provider_name_lister is not None:
                try:
                    configured = list(cls.provider_name_lister())
                except Exception:
                    logger.exception(
                        "OAuth provider_name_lister raised."
                    )
                    configured = []

            if len(configured) == 0:
                logger.warning(
                    "OAuth login requested but no providers are "
                    "configured."
                )
                response = cls._build_error_redirect(
                    error_code=cls.PROVIDER_UNAVAILABLE_ERROR_CODE,
                )
                return response

            logger.warning(
                "OAuth login requested for unknown provider %r "
                "(configured: %s).",
                provider_name,
                sorted(configured),
            )
            response = cls._build_error_redirect(
                error_code=cls.UNKNOWN_PROVIDER_ERROR_CODE,
            )
            return response

        state_value = generate_oauth_state()
        nonce_value = generate_oauth_nonce()

        redirect_uri = cls._build_callback_url(
            request=request,
            provider_name=provider_name,
        )

        extra_params = cls._resolve_provider_extras(
            provider_name=provider_name,
            is_register_flow=is_register_flow,
        )

        try:
            authorization_url = client.build_authorization_url(
                redirect_uri=redirect_uri,
                state=state_value,
                nonce=nonce_value,
                extra_params=extra_params,
            )
        except Exception:
            logger.exception(
                "OAuth kickoff: failed to build authorization URL "
                "for provider %r.",
                provider_name,
            )
            response = cls._build_error_redirect(
                error_code=cls.PROVIDER_UNAVAILABLE_ERROR_CODE,
            )
            return response

        cookie_value = cls._sign_state_payload({
            cls.OAUTH_PARAM_PROVIDER: provider_name,
            cls.OAUTH_PARAM_STATE: state_value,
            cls.OAUTH_PARAM_NONCE: nonce_value,
            cls.OAUTH_PARAM_REGISTER: is_register_flow,
        })

        if cookie_value is None:
            response = cls._build_error_redirect(
                error_code=cls.NOT_CONFIGURED_ERROR_CODE,
            )
            return response

        set_cookie_header = cls._build_state_set_cookie(cookie_value)

        logger.info(
            "OAuth kickoff (provider=%s, register=%s)",
            provider_name,
            is_register_flow,
        )

        response = cls._build_redirect_response(
            location=authorization_url,
            set_cookies=[set_cookie_header],
        )
        return response

    # --------------------------------------------------------------
    # Endpoint: registration intent (POST /register).
    # --------------------------------------------------------------

    @classmethod
    @SecurityBlueprint.create(
        leaf="register",
        doc=Doc(
            summary="OAuth registration intent",
            description="Captcha-verified entry point for the "
                        "registration flow. Returns the kickoff URL "
                        "the client should redirect to with "
                        "``register=1``."
        ),
        on_conflict="replace"
    )
    def register_intent(cls, request: Any) -> Dict[str, Any]:
        """
            Confirm a captcha-verified OAuth registration intent and
            return the kickoff URL the client should redirect to.

            The caller is responsible for redirecting the browser to
            the returned URL; the endpoint itself returns JSON so
            single-page applications can branch on the response
            without a hard-page reload.

            :param request: Incoming HTTP request. Body is JSON or
                            form-encoded with at minimum
                            ``captcha_response`` and optionally
                            ``provider``.

            :returns: ``200`` with ``{"success": true,
                      "redirect_url": "..."}`` on success;
                      ``400`` with ``{"success": false, "error":
                      "missing_captcha" | "captcha_failed"}``
                      otherwise.
        """
        if not cls.is_endpoint_enabled("register"):
            return cls._build_disabled_response("register")

        pre_error = cls.pre_authenticate(request)
        if pre_error is not None:
            response = cls._build_auth_error_response(error=pre_error, status_code=401)
            return response

        body = cls._read_request_body(request)

        captcha_token_raw = body.get(cls.OAUTH_PARAM_CAPTCHA_RESPONSE)
        captcha_token = (
            str(captcha_token_raw).strip()
            if captcha_token_raw is not None
            else ""
        )

        if captcha_token == "":
            response = cls._build_json_response(
                body={"success": False, "error": cls.MISSING_CAPTCHA_ERROR_CODE},
                status_code=400,
            )
            return response

        if cls.captcha_verifier is not None:
            try:
                captcha_ok = bool(cls.captcha_verifier(captcha_token))
            except Exception:
                logger.exception("OAuth captcha_verifier raised.")
                captcha_ok = False

            if not captcha_ok:
                response = cls._build_json_response(
                    body={"success": False, "error": cls.CAPTCHA_FAILED_ERROR_CODE},
                    status_code=400,
                )
                return response

        provider_name = str(body.get(cls.OAUTH_PARAM_PROVIDER) or "").strip()
        if provider_name == "":
            provider_name = cls.default_provider_name

        kickoff_path = "{}{}".format(cls._get_base_path() or "", cls.LOGIN_LEAF)
        redirect_url = "{}?{}".format(
            kickoff_path,
            urlencode({cls.OAUTH_PARAM_PROVIDER: provider_name, cls.OAUTH_PARAM_REGISTER: "1"}),
        )

        response = cls._build_json_response(
            body={"success": True, "redirect_url": redirect_url},
            status_code=200,
        )
        return response

    # --------------------------------------------------------------
    # Endpoint: callback (GET /callback).
    # --------------------------------------------------------------

    @classmethod
    @SecurityBlueprint.read(
        leaf="callback",
        doc=Doc(
            summary="OAuth callback",
            description="Validate the signed state cookie, exchange "
                        "the code for a token, parse the OAuth "
                        "claims, look up or create the matching "
                        "user, and establish the site session."
        ),
        on_conflict="replace"
    )
    def callback(cls, request: Any) -> Dict[str, Any]:
        """
            OAuth callback handler.

            Verifies the signed state cookie, exchanges the
            authorization code for a token, parses the returned
            userinfo claims (id_token for OIDC providers, userinfo
            endpoint for non-OIDC providers), hands the parsed
            claims to :attr:`user_resolver` to obtain a
            :class:`Principal`, optionally invokes
            :attr:`token_persister`, calls
            :meth:`SessionAuthBlueprint.establish_session`, and
            redirects to :attr:`post_login_redirect_url` with the
            session cookie attached and the state cookie cleared.

            :param request: Incoming HTTP request.

            :returns: A response dictionary with ``status``,
                      ``body``, ``content_type``, and ``headers``
                      keys.
        """
        if not cls.is_endpoint_enabled("callback"):
            return cls._build_disabled_response("callback")

        pre_error = cls.pre_authenticate(request)
        if pre_error is not None:
            response = cls._build_auth_error_response(error=pre_error, status_code=401)
            return response

        provider_error = cls._read_query_param(request, cls.OAUTH_PARAM_ERROR)
        if provider_error != "":
            provider_name_for_log = cls._read_query_param(
                request,
                cls.OAUTH_PARAM_PROVIDER,
            )
            logger.warning(
                "OAuth provider %r returned error: %s",
                provider_name_for_log,
                provider_error,
            )
            response = cls._build_error_redirect(
                error_code=cls.AUTHORIZATION_FAILED_ERROR_CODE,
                extra_query={cls.OAUTH_PARAM_PROVIDER_ERROR: provider_error},
                set_cookies=[cls._build_state_clear_cookie()],
            )
            return response

        provider_name = cls._read_query_param(request, cls.OAUTH_PARAM_PROVIDER)
        if provider_name == "":
            response = cls._build_error_redirect(
                error_code=cls.PROVIDER_MISSING_ON_CALLBACK_ERROR_CODE,
                set_cookies=[cls._build_state_clear_cookie()],
            )
            return response

        cookie_value = cls._read_state_cookie(request)
        payload = cls._unsign_state_payload(cookie_value)
        if payload is None:
            response = cls._build_error_redirect(
                error_code=cls.TOKEN_PARSE_FAILED_ERROR_CODE,
                set_cookies=[cls._build_state_clear_cookie()],
            )
            return response

        expected_state = str(payload.get(cls.OAUTH_PARAM_STATE) or "").strip()
        expected_nonce_raw = str(payload.get(cls.OAUTH_PARAM_NONCE) or "").strip()
        expected_nonce: Optional[str] = (
            expected_nonce_raw if expected_nonce_raw != "" else None
        )
        expected_provider = str(payload.get(cls.OAUTH_PARAM_PROVIDER) or "").strip()
        is_register_flow = bool(payload.get(cls.OAUTH_PARAM_REGISTER))

        if expected_provider != "" and expected_provider != provider_name:
            logger.warning(
                "OAuth callback provider mismatch: cookie=%r "
                "query=%r",
                expected_provider,
                provider_name,
            )
            response = cls._build_error_redirect(
                error_code=cls.TOKEN_PARSE_FAILED_ERROR_CODE,
                set_cookies=[cls._build_state_clear_cookie()],
            )
            return response

        state_from_provider = cls._read_query_param(request, cls.OAUTH_PARAM_STATE)
        if (
            expected_state == ""
            or state_from_provider == ""
            or expected_state != state_from_provider
        ):
            logger.warning(
                "OAuth callback state mismatch (provider=%r).",
                provider_name,
            )
            response = cls._build_error_redirect(
                error_code=cls.TOKEN_PARSE_FAILED_ERROR_CODE,
                set_cookies=[cls._build_state_clear_cookie()],
            )
            return response

        code_value = cls._read_query_param(request, cls.OAUTH_PARAM_CODE)
        if code_value == "":
            response = cls._build_error_redirect(
                error_code=cls.NO_TOKEN_ERROR_CODE,
                set_cookies=[cls._build_state_clear_cookie()],
            )
            return response

        client = cls._resolve_oauth_client(provider_name)
        if client is None:
            response = cls._build_error_redirect(
                error_code=cls.UNKNOWN_PROVIDER_ERROR_CODE,
                set_cookies=[cls._build_state_clear_cookie()],
            )
            return response

        redirect_uri = cls._build_callback_url(
            request=request,
            provider_name=provider_name,
        )

        try:
            token = client.exchange_code_for_token(
                redirect_uri=redirect_uri,
                code=code_value,
                state=state_from_provider,
            )
        except Exception:
            logger.exception(
                "OAuth token exchange failed for provider %r.",
                provider_name,
            )
            response = cls._build_error_redirect(
                error_code=cls.AUTHORIZATION_FAILED_ERROR_CODE,
                set_cookies=[cls._build_state_clear_cookie()],
            )
            return response

        if token is None or not isinstance(token, dict):
            response = cls._build_error_redirect(
                error_code=cls.NO_TOKEN_ERROR_CODE,
                set_cookies=[cls._build_state_clear_cookie()],
            )
            return response

        # Parse the userinfo claims. OIDC providers (Google) return
        # an id_token; non-OIDC providers (GitHub) need a follow-up
        # userinfo fetch.
        user_info: Dict[str, Any] = {}
        if cls.OAUTH_PARAM_ID_TOKEN in token:
            try:
                user_info = client.parse_id_token(
                    token,
                    nonce=expected_nonce,
                )
            except Exception:
                logger.exception(
                    "OAuth id_token parse failed for provider %r.",
                    provider_name,
                )
                response = cls._build_error_redirect(
                    error_code=cls.TOKEN_PARSE_FAILED_ERROR_CODE,
                    set_cookies=[cls._build_state_clear_cookie()],
                )
                return response
        else:
            try:
                user_info = client.fetch_userinfo(token)
            except Exception:
                logger.exception(
                    "OAuth userinfo fetch failed for provider %r.",
                    provider_name,
                )
                response = cls._build_error_redirect(
                    error_code=cls.TOKEN_PARSE_FAILED_ERROR_CODE,
                    set_cookies=[cls._build_state_clear_cookie()],
                )
                return response

        if not isinstance(user_info, dict) or len(user_info) == 0:
            response = cls._build_error_redirect(
                error_code=cls.TOKEN_PARSE_FAILED_ERROR_CODE,
                set_cookies=[cls._build_state_clear_cookie()],
            )
            return response

        if cls.user_resolver is None:
            logger.error(
                "OAuth callback: user_resolver is not configured."
            )
            response = cls._build_error_redirect(
                error_code=cls.NOT_CONFIGURED_ERROR_CODE,
                set_cookies=[cls._build_state_clear_cookie()],
            )
            return response

        try:
            resolve_result = cls.user_resolver(
                provider_name,
                user_info,
                is_register_flow,
                request,
            )
        except Exception:
            logger.exception(
                "OAuth user_resolver raised for provider %r.",
                provider_name,
            )
            response = cls._build_error_redirect(
                error_code=cls.AUTHORIZATION_FAILED_ERROR_CODE,
                set_cookies=[cls._build_state_clear_cookie()],
            )
            return response

        if not isinstance(resolve_result, OAuthCallbackResult):
            logger.error(
                "OAuth user_resolver returned %r, expected "
                "OAuthCallbackResult.",
                type(resolve_result).__name__,
            )
            response = cls._build_error_redirect(
                error_code=cls.AUTHORIZATION_FAILED_ERROR_CODE,
                set_cookies=[cls._build_state_clear_cookie()],
            )
            return response

        # Failure path — error_code wins over a stray principal.
        if resolve_result.error_code is not None:
            error_value = str(resolve_result.error_code).strip()
            if error_value != "":
                logger.info(
                    "OAuth callback failed (provider=%s, error=%s)",
                    provider_name,
                    error_value,
                )
                response = cls._build_error_redirect(
                    error_code=error_value,
                    set_cookies=[cls._build_state_clear_cookie()],
                )
                return response

        # Short-circuit redirect (e.g. divert to /convert-user-to-oauth).
        if resolve_result.short_circuit_redirect_url is not None:
            short_circuit = str(
                resolve_result.short_circuit_redirect_url,
            ).strip()
            if short_circuit != "":
                logger.info(
                    "OAuth callback short-circuit redirect "
                    "(provider=%s, url=%s)",
                    provider_name,
                    short_circuit,
                )
                response = cls._build_redirect_response(
                    location=short_circuit,
                    set_cookies=[cls._build_state_clear_cookie()],
                )
                return response

        principal = resolve_result.principal
        if principal is None:
            logger.error(
                "OAuth user_resolver returned no principal, no "
                "error_code, and no short-circuit URL."
            )
            response = cls._build_error_redirect(
                error_code=cls.AUTHORIZATION_FAILED_ERROR_CODE,
                set_cookies=[cls._build_state_clear_cookie()],
            )
            return response

        # Optional token persistence — failures are non-fatal; the
        # login itself can still succeed even when the token storage
        # path glitches (the user just won't auto-refresh later).
        if cls.token_persister is not None:
            user_id = (
                resolve_result.user_id
                if resolve_result.user_id is not None
                else principal.identifier
            )
            provider_ref_id = resolve_result.provider_ref_id

            if provider_ref_id is None:
                # Falls back to the standard claim names; sites can
                # also pre-resolve and pass via the result.
                fallback = ""
                for claim_name in cls.PROVIDER_ID_CLAIM_FALLBACKS:
                    candidate = user_info.get(claim_name)
                    if candidate:
                        fallback = candidate
                        break
                provider_ref_id = str(fallback).strip()

            try:
                cls.token_persister(
                    str(user_id),
                    provider_name,
                    str(provider_ref_id),
                    token,
                )
            except Exception:
                logger.exception(
                    "OAuth token_persister raised (user_id=%s, "
                    "provider=%r); login proceeds without "
                    "token persistence.",
                    user_id,
                    provider_name,
                )

        if cls.session_blueprint is None:
            logger.error(
                "OAuth callback: session_blueprint is not configured."
            )
            response = cls._build_error_redirect(
                error_code=cls.NOT_CONFIGURED_ERROR_CODE,
                set_cookies=[cls._build_state_clear_cookie()],
            )
            return response

        extra_attributes: Dict[str, Any] = {cls.OAUTH_PROVIDER_ATTRIBUTE: provider_name}
        if resolve_result.extra_attributes is not None:
            extra_attributes.update(resolve_result.extra_attributes)

        success_message = cls.success_message_template.format(
            provider=provider_name,
        )

        try:
            session_response = cls.session_blueprint.establish_session(
                principal=principal,
                request=request,
                scheme=cls.scheme_label,
                success_message=success_message,
                extra_attributes=extra_attributes,
            )
        except Exception:
            logger.exception(
                "OAuth callback: establish_session raised."
            )
            response = cls._build_error_redirect(
                error_code=cls.AUTHORIZATION_FAILED_ERROR_CODE,
                set_cookies=[cls._build_state_clear_cookie()],
            )
            return response

        session_cookie = ""
        if isinstance(session_response, dict):
            session_headers = session_response.get("headers")
            if isinstance(session_headers, dict):
                session_cookie = str(
                    session_headers.get(cls.SET_COOKIE_HEADER) or "",
                )

        logger.info(
            "OAuth callback succeeded (provider=%s, principal=%s, "
            "register=%s)",
            provider_name,
            principal.identifier,
            is_register_flow,
        )

        response = cls._build_redirect_response(
            location=cls.post_login_redirect_url,
            set_cookies=[
                session_cookie,
                cls._build_state_clear_cookie(),
            ],
        )
        return response

    # --------------------------------------------------------------
    # CSRF integration helper.
    # --------------------------------------------------------------

    @classmethod
    def get_csrf_exempt_paths(cls) -> List[str]:
        """
            Return the list of paths sites should add to their CSRF
            middleware exempt set.

            The kickoff and callback handlers are GET (no CSRF
            applies) but the registration handler is POST and runs
            before any session exists, so the site's CSRF middleware
            would otherwise reject it. Sites read this list during
            bootstrap to populate their middleware config.

            :returns: A list with the absolute path of the
                      registration endpoint.
        """
        base = cls._get_base_path() or ""
        rtnval = ["{}{}".format(base, cls.REGISTER_LEAF)]
        return rtnval


__all__ = [
    "DEFAULT_STATE_COOKIE_MAX_AGE_SECONDS",
    "DEFAULT_STATE_COOKIE_NAME",
    "DEFAULT_STATE_COOKIE_SIGNATURE_SALT",
    "ERROR_AUTHORIZATION_FAILED",
    "ERROR_NOT_CONFIGURED",
    "ERROR_NO_TOKEN",
    "ERROR_PROVIDER_MISSING_ON_CALLBACK",
    "ERROR_PROVIDER_UNAVAILABLE",
    "ERROR_TOKEN_PARSE_FAILED",
    "ERROR_UNKNOWN_PROVIDER",
    "OAuthCallbackResult",
    "OAuthClientBlueprint",
]
