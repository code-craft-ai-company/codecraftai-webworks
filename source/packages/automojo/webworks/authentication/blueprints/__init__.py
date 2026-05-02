"""
.. module:: blueprints
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Authentication blueprint classes providing pre-built endpoints.

.. moduleauthor:: Automation Mojo LLC

This module provides specialized blueprint classes that offer pre-built
authentication endpoints for each authentication method. Each blueprint
provides default endpoint implementations that can be customized or extended.
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from automojo.webworks.authentication.blueprints.responses import (
    AuthResponse,
    AuthError
)
from automojo.webworks.authentication.blueprints.schemas import (
    APIKeyCreateRequest,
    APIKeyResponse,
    LoginRequest,
    LoginResponse,
    SessionInfo,
    SessionLoginRequest,
    TokenRequest,
    TokenResponse
)
from automojo.webworks.authentication.blueprints.security import (
    SecurityBlueprint
)
from automojo.webworks.authentication.blueprints.basic import (
    BasicAuthBlueprint
)
from automojo.webworks.authentication.blueprints.bearer import (
    BearerAuthBlueprint
)
from automojo.webworks.authentication.blueprints.apikey import (
    APIKeyBlueprint,
    APIKeyStore
)
from automojo.webworks.authentication.blueprints.session import (
    SessionAuthBlueprint,
    SessionStore
)
from automojo.webworks.authentication.blueprints.magiclink import (
    MagicLinkBlueprint,
    MagicLinkConsumeResult,
    TokenConsumer
)
from automojo.webworks.authentication.blueprints.oauthclient import (
    OAuthCallbackResult,
    OAuthClientBlueprint
)
from automojo.webworks.authentication.blueprints.oauth2 import (
    OAuth2Blueprint,
    OAuth2ClientStore,
    AuthorizationCodeStore
)
from automojo.webworks.authentication.blueprints.schemas import (
    OAuth2AuthorizeRequest,
    OAuth2TokenRequest,
    OIDCDiscovery,
    UserInfo
)
from automojo.webworks.authentication.blueprints.oidc import (
    OIDCBlueprint
)


__all__ = [
    "APIKeyBlueprint",
    "APIKeyCreateRequest",
    "APIKeyResponse",
    "APIKeyStore",
    "AuthError",
    "AuthResponse",
    "AuthorizationCodeStore",
    "BasicAuthBlueprint",
    "BearerAuthBlueprint",
    "LoginRequest",
    "LoginResponse",
    "MagicLinkBlueprint",
    "MagicLinkConsumeResult",
    "OAuth2AuthorizeRequest",
    "OAuthCallbackResult",
    "OAuthClientBlueprint",
    "OAuth2Blueprint",
    "OAuth2ClientStore",
    "OAuth2TokenRequest",
    "OIDCBlueprint",
    "OIDCDiscovery",
    "SecurityBlueprint",
    "SessionAuthBlueprint",
    "SessionInfo",
    "SessionLoginRequest",
    "SessionStore",
    "TokenConsumer",
    "TokenRequest",
    "TokenResponse",
    "UserInfo",
]
