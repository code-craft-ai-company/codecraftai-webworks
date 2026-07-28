"""
    OpenAPI integration tests for the auth blueprints that mount
    HTTP endpoints (``MagicLinkBlueprint``, ``OAuthClientBlueprint``,
    ``SessionAuthBlueprint``).

    Verifies that endpoints registered via
    :meth:`SecurityBlueprint.register_with_registry` appear in the
    spec produced by :class:`OpenAPIGenerator`. This is what closes
    the loop on the API-docs surface for the auth flows: when
    consumers point ReDoc / Swagger UI at the generated spec they
    should see ``/auth/oauth/login``, ``/auth/oauth/register``,
    ``/auth/oauth/callback``, the magic-link redemption endpoint,
    and the session login / logout / info endpoints — not just the
    ``RestBlueprint``-tagged routes.
"""

from typing import Any, Dict, Set

from ccai.webworks.authentication.blueprints.magiclink import (
    MagicLinkBlueprint,
    MagicLinkConsumeResult,
)
from ccai.webworks.authentication.blueprints.oauthclient import (
    OAuthCallbackResult,
    OAuthClientBlueprint,
)
from ccai.webworks.authentication.blueprints.session import (
    SessionAuthBlueprint,
)
from ccai.webworks.authentication.core import Principal
from ccai.webworks.endpoints.registry import EndpointRegistry
from ccai.webworks.openapi.generator import OpenAPIGenerator
from ccai.webworks.openapi.configuration import OpenAPIInfo


# =============================================================================
# Helpers
# =============================================================================


def _make_session_blueprint() -> type:
    class _FreshSession(SessionAuthBlueprint):
        pass

    _FreshSession.identity_provider = None
    _FreshSession.session_store = None
    _FreshSession.session_duration = 3600
    _FreshSession.cookie_name = "site_session"
    _FreshSession.cookie_secure = True
    _FreshSession.cookie_httponly = True
    _FreshSession.cookie_samesite = "Lax"
    _FreshSession.enabled_endpoints = None
    _FreshSession.auth_system = None
    _FreshSession.base_path = "/auth/session"
    _FreshSession._memory_store = {}

    rtnval = _FreshSession
    return rtnval


def _make_magic_blueprint() -> type:
    class _Fresh(MagicLinkBlueprint):
        pass

    _Fresh.token_consumer = staticmethod(
        lambda token: MagicLinkConsumeResult(
            principal=Principal(identifier="u-1"),
        )
    )
    _Fresh.session_blueprint = _make_session_blueprint()
    _Fresh.enabled_endpoints = None
    _Fresh.auth_system = None
    _Fresh.base_path = "/auth/magic"

    rtnval = _Fresh
    return rtnval


def _make_oauth_blueprint() -> type:
    class _Fresh(OAuthClientBlueprint):
        pass

    _Fresh.provider_resolver = staticmethod(lambda name: None)
    _Fresh.user_resolver = staticmethod(
        lambda *args, **kwargs: OAuthCallbackResult(),
    )
    _Fresh.state_cookie_secret_resolver = staticmethod(lambda: "secret")
    _Fresh.session_blueprint = _make_session_blueprint()
    _Fresh.enabled_endpoints = None
    _Fresh.auth_system = None
    _Fresh.base_path = "/auth/oauth"

    rtnval = _Fresh
    return rtnval


def _build_spec_for(blueprint_cls) -> Dict[str, Any]:
    """
        Register the blueprint's descriptors with a registry built for
        :class:`EndpointRegistry` and invoke the
        :class:`OpenAPIGenerator` against it. Returns the generated
        spec dict.
    """
    registry = EndpointRegistry()
    blueprint_cls.register_with_registry(registry=registry, on_conflict="replace")

    info = OpenAPIInfo(title="Test", version="0.0.0")
    generator = OpenAPIGenerator(registry=registry, info=info)

    rtnval = generator.generate()
    return rtnval


def _paths_in(spec: Dict[str, Any]) -> Set[str]:
    return set((spec.get("paths") or {}).keys())


# =============================================================================
# MagicLinkBlueprint
# =============================================================================


def test_magiclink_redemption_endpoint_appears_in_openapi_spec():
    blueprint = _make_magic_blueprint()
    spec = _build_spec_for(blueprint)

    paths = _paths_in(spec)
    if "/auth/magic/{token}" not in paths:
        errmsg = (
            "Expected /auth/magic/{{token}} in OpenAPI spec paths, got "
            "{!r}".format(sorted(paths))
        )
        raise AssertionError(errmsg)

    return


def test_magiclink_endpoint_carries_doc_summary_in_spec():
    blueprint = _make_magic_blueprint()
    spec = _build_spec_for(blueprint)

    operation = spec["paths"]["/auth/magic/{token}"]["get"]
    summary = operation.get("summary", "")
    if summary == "":
        errmsg = "Expected non-empty summary on magic-link operation, got {!r}".format(
            operation,
        )
        raise AssertionError(errmsg)

    return


# =============================================================================
# OAuthClientBlueprint
# =============================================================================


def test_oauthclient_three_endpoints_appear_in_openapi_spec():
    blueprint = _make_oauth_blueprint()
    spec = _build_spec_for(blueprint)

    paths = _paths_in(spec)
    expected = {
        "/auth/oauth/login",
        "/auth/oauth/register",
        "/auth/oauth/callback",
    }
    missing = expected - paths
    if len(missing) > 0:
        errmsg = "Missing OAuth endpoints in spec: {!r}; got {!r}".format(
            sorted(missing),
            sorted(paths),
        )
        raise AssertionError(errmsg)

    return


def test_oauthclient_register_endpoint_is_post_in_spec():
    blueprint = _make_oauth_blueprint()
    spec = _build_spec_for(blueprint)

    register_item = spec["paths"]["/auth/oauth/register"]
    if "post" not in register_item:
        errmsg = "Expected POST operation on /auth/oauth/register, got {!r}".format(
            list(register_item.keys()),
        )
        raise AssertionError(errmsg)

    return


# =============================================================================
# SessionAuthBlueprint (existing — should also be picked up)
# =============================================================================


def test_session_endpoints_appear_in_openapi_spec():
    blueprint = _make_session_blueprint()
    spec = _build_spec_for(blueprint)

    paths = _paths_in(spec)
    expected = {
        "/auth/session/login",
        "/auth/session/logout",
        "/auth/session",
    }
    missing = expected - paths
    if len(missing) > 0:
        errmsg = "Missing session endpoints in spec: {!r}; got {!r}".format(
            sorted(missing),
            sorted(paths),
        )
        raise AssertionError(errmsg)

    return


# =============================================================================
# Tags
# =============================================================================


def test_oauthclient_endpoints_carry_authentication_tag():
    blueprint = _make_oauth_blueprint()
    spec = _build_spec_for(blueprint)

    operation = spec["paths"]["/auth/oauth/login"]["get"]
    tags = set(operation.get("tags") or [])
    if "Authentication" not in tags:
        errmsg = "Expected 'Authentication' tag on OAuth login operation, got {!r}".format(
            tags,
        )
        raise AssertionError(errmsg)

    return
