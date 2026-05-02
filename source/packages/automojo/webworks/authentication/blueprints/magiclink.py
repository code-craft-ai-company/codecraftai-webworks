"""
.. module:: magiclink
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Magic-link authentication blueprint providing a single
        redemption endpoint for single-use first-login tokens.

.. moduleauthor:: Automation Mojo LLC

This module provides the :class:`MagicLinkBlueprint` class which extends
:class:`SecurityBlueprint` to offer a pre-built endpoint for consuming
single-use magic-link tokens. The blueprint delegates the actual token
lookup, expiration, and single-use bookkeeping to a site-supplied
``token_consumer`` callable, then issues a session via the configured
:class:`SessionAuthBlueprint` subclass and redirects the browser to a
configurable next-page URL.

Sites typically use magic links for first-time login flows: an
administrator provisions a new user, the framework emails a one-time
URL of the form ``/auth/magic/{token}``, and the user lands on the
redemption endpoint which logs them in and redirects to a
"set-password" page so they can pick a personal credential.

The blueprint owns the framework-side concerns (defensive token-format
validation, session establishment, error redirects, structured
logging) while the site keeps ownership of the token storage, the
:class:`Principal` construction, and the email rendering. This split
matches the contract documented in the migration spec
``upstream-oauth-magic-blueprints``.

Endpoints:
    - ``GET <base_path>/{token}`` — Redeem a single-use magic-link token.
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


import logging
import re

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Type
from urllib.parse import urlencode

from automojo.webworks.authentication.core import Principal
from automojo.webworks.authentication.blueprints.responses import AuthError
from automojo.webworks.authentication.blueprints.security import (
    SecurityBlueprint
)
from automojo.webworks.authentication.blueprints.session import (
    SessionAuthBlueprint
)
from automojo.webworks.endpoints.doc import Doc


logger = logging.getLogger(__name__)


# Default token-format validation pattern. URL-safe base64 (``A-Z``,
# ``a-z``, ``0-9``, ``-``, ``_``) with a generous length cap that
# accommodates ``secrets.token_urlsafe(48)`` and similar.
DEFAULT_TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9_\-]{8,256}$")


# Recognised error codes returned by ``token_consumer``. The blueprint
# does not enforce this set — sites can pass any short string — but it
# documents the canonical vocabulary so logs and error redirects stay
# consistent across deployments.
ERROR_CODE_INVALID = "magic_link_invalid"
ERROR_CODE_EXPIRED = "magic_link_expired"
ERROR_CODE_CONSUMED = "magic_link_consumed"
ERROR_CODE_INTERNAL = "magic_link_failed"


@dataclass
class MagicLinkConsumeResult:
    """
        Result returned by a site-supplied ``token_consumer`` callable.

        Exactly one of :attr:`principal` or :attr:`error_code` should be
        populated. The blueprint treats a populated :attr:`principal`
        as the success path and any non-empty :attr:`error_code` as the
        failure path; if both are populated the failure path wins.

        :param principal: The :class:`Principal` to log in on success.
                          ``None`` on the failure path.
        :param error_code: A short, URL-safe error code on the failure
                           path (e.g. ``"magic_link_invalid"``,
                           ``"magic_link_expired"``,
                           ``"magic_link_consumed"``). Surfaced to the
                           browser as ``?error=<code>`` on the error
                           redirect. ``None`` on the success path.
        :param token_id: Optional opaque token identifier (e.g. database
                         row id) recorded on the success path's
                         :class:`AuthenticationContext.attributes` so
                         downstream subscribers can audit the channel.
                         ``None`` when the site does not surface a token
                         id.
        :param extra_attributes: Optional extra attributes merged into
                                 the :class:`AuthenticationContext` on
                                 the success path. Useful for recording
                                 channel-specific metadata beyond the
                                 token id.
    """

    principal: Optional[Principal] = None
    error_code: Optional[str] = None
    token_id: Optional[str] = None
    extra_attributes: Optional[Dict[str, Any]] = None


# Type alias for the site-supplied callable that consumes a raw token
# string and returns a :class:`MagicLinkConsumeResult`.
TokenConsumer = Callable[[str], MagicLinkConsumeResult]


class MagicLinkBlueprint(SecurityBlueprint):
    """
        Blueprint for magic-link authentication endpoints.

        Provides a single ``GET`` redemption endpoint that consumes a
        single-use token, establishes a session for the matching
        principal, and redirects to a configurable next-page URL.

        Token storage, expiration semantics, single-use bookkeeping,
        and :class:`Principal` construction live in the site's
        :attr:`token_consumer` callable. The blueprint adds defensive
        token-format validation in front of the consumer, builds the
        redirect responses, and threads the session cookie through
        :meth:`SessionAuthBlueprint.establish_session`.

        Default Endpoint:
            - ``GET /auth/magic/{token}`` — Redeem a single-use
              magic-link token and redirect to the post-redemption URL.

        Class Attributes:
            base_path: Base URL path for the redemption endpoint.
                       Defaults to ``"/auth/magic"``. Sites that need to
                       preserve a legacy URL (e.g. ``"/login/magic"``)
                       override this on their subclass.
            tags: Documentation tags applied to the endpoint.
            token_consumer: Site-supplied callable that maps a raw
                            token string to a
                            :class:`MagicLinkConsumeResult`. Must be set
                            before the endpoint can process requests.
            session_blueprint: The :class:`SessionAuthBlueprint`
                               subclass used to issue the session cookie
                               on success. Required.
            post_redemption_redirect_url: Location for the success
                                          redirect. Defaults to
                                          ``"/set-password"`` to suit
                                          the first-login use case.
            error_redirect_url: Location for the failure redirect. The
                                blueprint appends ``?error=<code>`` so
                                the target page can display a
                                contextual message. Defaults to
                                ``"/login"``.
            scheme_label: ``scheme`` value recorded on the resulting
                          :class:`AuthenticationContext`. Defaults to
                          ``"MagicLink"``.
            success_message: ``message`` field included in the
                             ``establish_session`` response body. Has no
                             user-visible effect on the redirect path
                             (the body is discarded) but does flow into
                             the post-authenticate hook for sites that
                             wire one up.
            token_pattern: Compiled :mod:`re` pattern used to defensively
                           validate the raw token before calling the
                           consumer. Defaults to
                           :data:`DEFAULT_TOKEN_PATTERN`.
    """

    base_path: str = "/auth/magic"
    tags: List[str] = ["Authentication", "MagicLink"]

    token_consumer: Optional[TokenConsumer] = None
    session_blueprint: Optional[Type[SessionAuthBlueprint]] = None
    post_redemption_redirect_url: str = "/set-password"
    error_redirect_url: str = "/login"
    scheme_label: str = "MagicLink"
    success_message: str = "Welcome — your link has been redeemed"
    token_pattern: "re.Pattern[str]" = DEFAULT_TOKEN_PATTERN

    @classmethod
    def _extract_raw_token(cls, request: Any) -> str:
        """
            Extract the raw token string from the request path parameters.

            Supports both attribute-style (``request.path_params``) and
            mapping-style (``request["path_params"]``) accessors so the
            blueprint can run against ASGI-style scope wrappers and
            mock-request fixtures alike.

            :param request: The incoming HTTP request object.

            :returns: The raw token value, or an empty string when the
                      ``token`` path parameter is missing.
        """
        path_params: Dict[str, Any] = {}

        attr_value = getattr(request, "path_params", None)
        if isinstance(attr_value, dict):
            path_params = attr_value

        if len(path_params) == 0 and isinstance(request, dict):
            mapped = request.get("path_params")
            if isinstance(mapped, dict):
                path_params = mapped

        raw_value = path_params.get("token")
        if raw_value is None:
            return ""

        rtnval = str(raw_value).strip()
        return rtnval

    @classmethod
    def _build_redirect_response(
        cls,
        location: str,
        set_cookie: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
            Build a 302 redirect response dictionary.

            The shape mirrors the ``establish_session`` response shape so
            ASGI adapters that consume blueprint responses can apply the
            same headers / status pipeline. The ``Set-Cookie`` header is
            attached only when *set_cookie* is a non-empty string.

            :param location: The URL to redirect to.
            :param set_cookie: Optional ``Set-Cookie`` header value to
                               attach to the redirect.

            :returns: A response dictionary with ``status``, ``body``,
                      ``content_type``, and ``headers`` keys.
        """
        headers: Dict[str, str] = {"Location": location}

        if set_cookie is not None:
            cookie_value = str(set_cookie).strip()
            if cookie_value != "":
                headers["Set-Cookie"] = cookie_value

        response = {
            "status": 302,
            "body": b"",
            "content_type": "text/html; charset=utf-8",
            "headers": headers,
        }
        return response

    @classmethod
    def _build_error_redirect(cls, error_code: str) -> Dict[str, Any]:
        """
            Build a 302 redirect to :attr:`error_redirect_url` with an
            ``?error=<code>`` query parameter.

            The query parameter is always URL-encoded. When the error
            redirect URL already contains a query string the parameter is
            appended with ``&``; otherwise it is appended with ``?``.

            :param error_code: A short, URL-safe error code identifying
                               the failure mode.

            :returns: A redirect response dictionary.
        """
        encoded_pair = urlencode({"error": str(error_code)})

        base = cls.error_redirect_url

        if "?" in base:
            location = "{}&{}".format(base, encoded_pair)
        else:
            location = "{}?{}".format(base, encoded_pair)

        response = cls._build_redirect_response(location=location)
        return response

    @classmethod
    @SecurityBlueprint.read(
        path="/{token}",
        doc=Doc(
            summary="Redeem a magic-link token",
            description="Consume a single-use magic-link token, "
                        "establish a session for the associated user, "
                        "and redirect to the configured post-redemption "
                        "URL."
        ),
        on_conflict="replace"
    )
    def redeem(cls, request: Any) -> Dict[str, Any]:
        """
            Handle a magic-link redemption request.

            Reads the ``token`` path parameter, defensively validates
            its format, calls the site-supplied :attr:`token_consumer`,
            and then either:

              * On success — calls
                :meth:`SessionAuthBlueprint.establish_session` on
                :attr:`session_blueprint` and returns a 302 redirect to
                :attr:`post_redemption_redirect_url` with the
                ``Set-Cookie`` header attached.
              * On failure — returns a 302 redirect to
                :attr:`error_redirect_url` with an ``?error=<code>``
                query parameter.

            The endpoint can be disabled via the ``enabled_endpoints``
            configuration. When disabled, a 404 response is returned.

            :param request: The incoming HTTP request object. The token
                            is read from the ``token`` path parameter.

            :returns: A response dictionary with ``status``, ``body``,
                      ``content_type``, and ``headers`` keys.
        """
        if not cls.is_endpoint_enabled("redeem"):
            error = AuthError(
                error="endpoint_disabled",
                error_description="Magic-link redemption is disabled"
            )
            response = cls.format_error(error, status_code=404)
            return response

        # Pre-redemption hook (subclasses can short-circuit with
        # rate-limiting / IP gating / etc.).
        pre_error = cls.pre_authenticate(request)
        if pre_error is not None:
            response = cls.format_error(pre_error)
            return response

        # Defensive token-format check — saves the consumer from having
        # to defend against pathological inputs.
        raw_token = cls._extract_raw_token(request)

        if raw_token == "":
            logger.info(
                "magiclink redemption rejected: missing token"
            )
            response = cls._build_error_redirect(
                error_code=ERROR_CODE_INVALID
            )
            return response

        if cls.token_pattern is not None:
            match = cls.token_pattern.match(raw_token)
            if match is None:
                logger.info(
                    "magiclink redemption rejected: token failed format check"
                )
                response = cls._build_error_redirect(
                    error_code=ERROR_CODE_INVALID
                )
                return response

        # Both collaborators must be wired before the endpoint can run.
        if cls.token_consumer is None:
            logger.error(
                "magiclink redemption: token_consumer is not configured"
            )
            response = cls._build_error_redirect(
                error_code=ERROR_CODE_INTERNAL
            )
            return response

        if cls.session_blueprint is None:
            logger.error(
                "magiclink redemption: session_blueprint is not configured"
            )
            response = cls._build_error_redirect(
                error_code=ERROR_CODE_INTERNAL
            )
            return response

        try:
            consume_result = cls.token_consumer(raw_token)
        except Exception:
            # The consumer is site code; an unexpected exception is
            # logged but never leaked to the browser. The user lands on
            # the generic error page.
            logger.exception(
                "magiclink redemption: token_consumer raised"
            )
            response = cls._build_error_redirect(
                error_code=ERROR_CODE_INTERNAL
            )
            return response

        if not isinstance(consume_result, MagicLinkConsumeResult):
            logger.error(
                "magiclink redemption: token_consumer returned %r, "
                "expected MagicLinkConsumeResult",
                type(consume_result).__name__,
            )
            response = cls._build_error_redirect(
                error_code=ERROR_CODE_INTERNAL
            )
            return response

        # Failure path — error_code wins over a stray principal.
        error_code = consume_result.error_code
        if error_code is not None and str(error_code).strip() != "":
            normalised_error = str(error_code).strip()
            logger.info(
                "magiclink redemption failed: %s",
                normalised_error,
            )
            response = cls._build_error_redirect(
                error_code=normalised_error
            )
            return response

        principal = consume_result.principal
        if principal is None:
            logger.error(
                "magiclink redemption: token_consumer returned no "
                "principal and no error_code"
            )
            response = cls._build_error_redirect(
                error_code=ERROR_CODE_INTERNAL
            )
            return response

        # Build the extra_attributes dict forwarded to the session
        # establishment hook.
        extra_attributes: Dict[str, Any] = {}
        if consume_result.extra_attributes is not None:
            extra_attributes.update(consume_result.extra_attributes)

        if consume_result.token_id is not None:
            token_id_value = str(consume_result.token_id).strip()
            if token_id_value != "":
                extra_attributes["token_id"] = token_id_value

        try:
            session_response = cls.session_blueprint.establish_session(
                principal=principal,
                request=request,
                scheme=cls.scheme_label,
                success_message=cls.success_message,
                extra_attributes=extra_attributes,
            )
        except Exception:
            logger.exception(
                "magiclink redemption: establish_session raised"
            )
            response = cls._build_error_redirect(
                error_code=ERROR_CODE_INTERNAL
            )
            return response

        set_cookie_value = ""
        if isinstance(session_response, dict):
            session_headers = session_response.get("headers")
            if isinstance(session_headers, dict):
                set_cookie_value = str(
                    session_headers.get("Set-Cookie") or ""
                )

        logger.info(
            "magiclink redemption succeeded for principal %s",
            principal.identifier,
        )

        response = cls._build_redirect_response(
            location=cls.post_redemption_redirect_url,
            set_cookie=set_cookie_value,
        )
        return response


__all__ = [
    "DEFAULT_TOKEN_PATTERN",
    "ERROR_CODE_CONSUMED",
    "ERROR_CODE_EXPIRED",
    "ERROR_CODE_INTERNAL",
    "ERROR_CODE_INVALID",
    "MagicLinkBlueprint",
    "MagicLinkConsumeResult",
    "TokenConsumer",
]
