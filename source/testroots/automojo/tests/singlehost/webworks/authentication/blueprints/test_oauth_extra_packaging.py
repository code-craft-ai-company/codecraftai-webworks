"""
    Dependency-removal regression tests for the OAuth stack.

    The OAuth client / blueprint / state-cookie machinery once
    depended on three third-party libraries (``authlib``,
    ``itsdangerous``, ``joserfc``). Those have been replaced by
    in-house implementations
    (``automojo.webworks.authentication.oauth``,
    ``automojo.webworks.security.signedserializer``, and
    ``automojo.webworks.security.jsonwebtoken``), so none of the three
    libraries may be imported on any OAuth code path any longer.

    These tests lock in that boundary: with ``authlib`` / ``joserfc``
    / ``itsdangerous`` imports forced to fail, importing the modules,
    constructing the client, building an authorization URL, and
    signing + reading a state cookie must all still succeed. A future
    change that reintroduces a dependency on one of those libraries
    will trip these tests.

    The library-blocking is implemented as a temporary
    ``builtins.__import__`` swap that raises ``ModuleNotFoundError``
    for the three libraries' top-level modules (and submodules). This
    simulates an environment where the libraries simply are not
    installed.
"""

import builtins
import importlib
import sys

from typing import Iterable


# =============================================================================
# Library-import blocker
# =============================================================================


_BLOCKED_PREFIXES = ("authlib", "joserfc", "itsdangerous")


def _make_blocking_import(blocked: Iterable[str]):
    """
        Build an ``__import__`` replacement that raises
        ``ModuleNotFoundError`` for the listed top-level modules and
        their submodules. Other imports flow through to the real
        importer unchanged.

        :param blocked: Tuple / iterable of module names whose import
                        should raise.

        :returns: A callable suitable for assigning to
                  ``builtins.__import__``.
    """
    blocked_set = tuple(blocked)
    real_import = builtins.__import__

    def _blocking_import(name, *args, **kwargs):
        if name in blocked_set or any(
            name.startswith(b + ".") for b in blocked_set
        ):
            errmsg = "No module named {!r}".format(name)
            raise ModuleNotFoundError(errmsg)
        return real_import(name, *args, **kwargs)

    rtnval = _blocking_import
    return rtnval


def _drop_cached_modules(prefixes: Iterable[str]) -> None:
    """
        Pop already-imported modules under any of the listed prefixes
        from ``sys.modules`` so that subsequent ``importlib.reload``
        / ``importlib.import_module`` calls go through the
        ``__import__`` blocker instead of returning a cached result.

        :param prefixes: Top-level module names to evict.
    """
    targets = []
    for cached in list(sys.modules.keys()):
        for prefix in prefixes:
            if cached == prefix or cached.startswith(prefix + "."):
                targets.append(cached)
                break

    for cached in targets:
        del sys.modules[cached]

    return


# =============================================================================
# Module-level import succeeds without the formerly-required libraries
# =============================================================================


def test_oauth_module_imports_without_oauth_libraries(monkeypatch):
    """
        ``automojo.webworks.authentication.oauth`` must import cleanly
        when authlib / joserfc / itsdangerous are absent.
    """
    _drop_cached_modules(_BLOCKED_PREFIXES + ("automojo.webworks.authentication.oauth",))

    monkeypatch.setattr(
        builtins,
        "__import__",
        _make_blocking_import(_BLOCKED_PREFIXES),
    )

    oauth_mod = importlib.import_module(
        "automojo.webworks.authentication.oauth",
    )
    if not hasattr(oauth_mod, "OAuthClient"):
        errmsg = "OAuthClient export missing after no-libs import"
        raise AssertionError(errmsg)

    return


def test_oauthclient_blueprint_module_imports_without_oauth_libraries(monkeypatch):
    """
        ``automojo.webworks.authentication.blueprints.oauthclient``
        must import cleanly without the formerly-required libraries.
    """
    _drop_cached_modules(
        _BLOCKED_PREFIXES + (
            "automojo.webworks.authentication.oauth",
            "automojo.webworks.authentication.blueprints.oauthclient",
        ),
    )

    monkeypatch.setattr(
        builtins,
        "__import__",
        _make_blocking_import(_BLOCKED_PREFIXES),
    )

    bp_mod = importlib.import_module(
        "automojo.webworks.authentication.blueprints.oauthclient",
    )
    if not hasattr(bp_mod, "OAuthClientBlueprint"):
        errmsg = "OAuthClientBlueprint export missing after no-libs import"
        raise AssertionError(errmsg)

    return


# =============================================================================
# OAuthClient construction and use succeed without the libraries
# =============================================================================


def test_oauth_client_constructor_succeeds_without_oauth_libraries(monkeypatch):
    """
        Constructing an :class:`OAuthClient` must not require any of
        the removed libraries.
    """
    _drop_cached_modules(
        _BLOCKED_PREFIXES + (
            "automojo.webworks.authentication.oauth",
        ),
    )

    monkeypatch.setattr(
        builtins,
        "__import__",
        _make_blocking_import(_BLOCKED_PREFIXES),
    )

    oauth_mod = importlib.import_module(
        "automojo.webworks.authentication.oauth",
    )

    client = oauth_mod.OAuthClient(
        provider_name="google",
        provider_config={
            "client_id": "id",
            "client_secret": "secret",
            "authorize_url": "https://provider.example.com/auth",
            "access_token_url": "https://provider.example.com/token",
        },
    )

    if client.provider_name != "google":
        errmsg = "Constructor failed silently without the OAuth libraries"
        raise AssertionError(errmsg)

    return


def test_build_authorization_url_succeeds_without_oauth_libraries(monkeypatch):
    """
        ``build_authorization_url`` is pure standard-library URL
        assembly now, so it must succeed with authlib / joserfc /
        itsdangerous all blocked, producing an authorization-code
        request URL.
    """
    _drop_cached_modules(
        _BLOCKED_PREFIXES + (
            "automojo.webworks.authentication.oauth",
        ),
    )

    monkeypatch.setattr(
        builtins,
        "__import__",
        _make_blocking_import(_BLOCKED_PREFIXES),
    )

    oauth_mod = importlib.import_module(
        "automojo.webworks.authentication.oauth",
    )

    client = oauth_mod.OAuthClient(
        provider_name="google",
        provider_config={
            "client_id": "id",
            "client_secret": "secret",
            "authorize_url": "https://provider.example.com/auth",
            "access_token_url": "https://provider.example.com/token",
        },
    )

    url = client.build_authorization_url(
        redirect_uri="https://app.example.com/callback",
        state="state-1",
    )

    if not url.startswith("https://provider.example.com/auth?"):
        errmsg = "Authorization URL did not target the authorize endpoint: {!r}".format(url)
        raise AssertionError(errmsg)

    for required_fragment in ("response_type=code", "client_id=id", "state=state-1"):
        if required_fragment not in url:
            errmsg = "Authorization URL missing {!r}: {!r}".format(required_fragment, url)
            raise AssertionError(errmsg)

    return


def test_state_cookie_serializer_succeeds_without_oauth_libraries(monkeypatch):
    """
        ``OAuthClientBlueprint._build_state_serializer`` uses the
        in-house signed serializer, so building it and round-tripping
        a payload must succeed with the removed libraries blocked.
    """
    _drop_cached_modules(
        _BLOCKED_PREFIXES + (
            "automojo.webworks.authentication.oauth",
            "automojo.webworks.authentication.blueprints.oauthclient",
            "automojo.webworks.security.signedserializer",
        ),
    )

    monkeypatch.setattr(
        builtins,
        "__import__",
        _make_blocking_import(_BLOCKED_PREFIXES),
    )

    bp_mod = importlib.import_module(
        "automojo.webworks.authentication.blueprints.oauthclient",
    )

    class _Fresh(bp_mod.OAuthClientBlueprint):
        pass

    _Fresh.state_cookie_secret_resolver = staticmethod(lambda: "sec")

    serializer = _Fresh._build_state_serializer()
    if serializer is None:
        errmsg = "Serializer should be built when a secret resolver is wired"
        raise AssertionError(errmsg)

    payload = {"provider": "google", "state": "abc"}
    token = serializer.dumps(payload)
    recovered = serializer.loads(token, max_age=600)

    if recovered != payload:
        errmsg = "State cookie round-trip mismatch: {!r}".format(recovered)
        raise AssertionError(errmsg)

    return
