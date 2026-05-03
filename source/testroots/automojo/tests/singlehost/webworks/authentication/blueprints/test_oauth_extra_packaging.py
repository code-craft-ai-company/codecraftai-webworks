"""
    Packaging regression tests for the ``oauth`` extra.

    The OAuth client / blueprint / state-cookie machinery depends on
    three third-party libraries (``authlib``, ``itsdangerous``,
    ``joserfc``). After these were moved from main webworks deps to
    the ``oauth`` extra, importing the blueprint and OAuth client
    *modules* must continue to succeed even when the libraries are
    not installed — only *using* the OAuth functionality (calling
    ``build_authorization_url``, signing a state cookie, validating
    an id_token) should require them. These tests lock in that
    boundary so a future change can't accidentally hoist a library
    import back to module scope and break the no-extras install.

    The library-blocking is implemented as a temporary ``builtins.__import__``
    swap that raises ``ModuleNotFoundError`` for the three optional
    libraries' top-level modules (and submodules). This simulates a
    fresh ``pip install automojo-webworks`` (without ``[oauth]``)
    runtime exactly as cleanly as deleting the libraries from the
    venv.
"""

import builtins
import importlib
import sys

from typing import Any, Iterable


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
# Module-level import succeeds without the OAuth libraries
# =============================================================================


def test_oauth_module_imports_without_oauth_libraries(monkeypatch):
    """
        ``automojo.webworks.authentication.oauth`` must import
        cleanly when the ``oauth`` extra is not installed.
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
        must import cleanly without the ``oauth`` extra.
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
# OAuthClient construction succeeds; using it raises diagnostically
# =============================================================================


def test_oauth_client_constructor_succeeds_without_authlib(monkeypatch):
    """
        Constructing an :class:`OAuthClient` doesn't import authlib;
        only the flow methods do.
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
        errmsg = "Constructor failed silently without authlib"
        raise AssertionError(errmsg)

    return


def test_build_authorization_url_raises_diagnostic_without_authlib(monkeypatch):
    """
        Calling ``build_authorization_url`` without authlib installed
        must raise ``ImportError`` with a message pointing the
        consumer at ``pip install automojo-webworks[oauth]``.
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

    raised = False
    raised_message = ""
    try:
        client.build_authorization_url(
            redirect_uri="https://app.example.com/callback",
            state="state-1",
        )
    except ImportError as exc:
        raised = True
        raised_message = str(exc)

    if not raised:
        errmsg = "Expected ImportError diagnostic without authlib"
        raise AssertionError(errmsg)

    if "automojo-webworks[oauth]" not in raised_message:
        errmsg = (
            "Diagnostic should mention 'automojo-webworks[oauth]', got "
            "{!r}".format(raised_message)
        )
        raise AssertionError(errmsg)

    return


def test_state_cookie_serializer_raises_diagnostic_without_itsdangerous(monkeypatch):
    """
        ``OAuthClientBlueprint._build_state_serializer`` raises
        ``ImportError`` with the ``oauth`` extra hint when
        ``itsdangerous`` isn't installed.
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

    class _Fresh(bp_mod.OAuthClientBlueprint):
        pass

    _Fresh.state_cookie_secret_resolver = staticmethod(lambda: "sec")

    raised = False
    raised_message = ""
    try:
        _Fresh._build_state_serializer()
    except ImportError as exc:
        raised = True
        raised_message = str(exc)

    if not raised:
        errmsg = "Expected ImportError diagnostic without itsdangerous"
        raise AssertionError(errmsg)

    if "automojo-webworks[oauth]" not in raised_message:
        errmsg = (
            "Diagnostic should mention 'automojo-webworks[oauth]', got "
            "{!r}".format(raised_message)
        )
        raise AssertionError(errmsg)

    return
