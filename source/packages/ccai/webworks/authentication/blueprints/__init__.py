"""
.. module:: blueprints
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Authentication blueprint classes providing pre-built endpoints.

.. moduleauthor:: Code Craft AI LLC

This module provides specialized blueprint classes that offer pre-built
authentication endpoints for each authentication method. Each blueprint
provides default endpoint implementations that can be customized or extended.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from ccai.webworks.authentication.blueprints.responses import (
    AuthResponse,
    AuthError
)
from ccai.webworks.authentication.blueprints.schemas import (
    APIKeyCreateRequest,
    APIKeyResponse,
    LoginRequest,
    LoginResponse,
    SessionInfo,
    SessionLoginRequest,
    TokenRequest,
    TokenResponse
)
from ccai.webworks.authentication.blueprints.security import (
    SecurityBlueprint
)
from ccai.webworks.authentication.blueprints.basic import (
    BasicAuthBlueprint
)
from ccai.webworks.authentication.blueprints.bearer import (
    BearerAuthBlueprint
)
from ccai.webworks.authentication.blueprints.apikey import (
    APIKeyBlueprint,
    APIKeyStore
)
from ccai.webworks.authentication.blueprints.session import (
    SessionAuthBlueprint,
    SessionStore
)
from ccai.webworks.authentication.blueprints.magiclink import (
    MagicLinkBlueprint,
    MagicLinkConsumeResult,
    TokenConsumer,
    TokenIssuer
)
from ccai.webworks.authentication.blueprints.oauthclient import (
    OAuthCallbackResult,
    OAuthClientBlueprint
)
from ccai.webworks.authentication.blueprints.oauth2 import (
    OAuth2Blueprint,
    OAuth2ClientStore,
    AuthorizationCodeStore
)
from ccai.webworks.authentication.blueprints.schemas import (
    OAuth2AuthorizeRequest,
    OAuth2TokenRequest,
    OIDCDiscovery,
    UserInfo
)
from ccai.webworks.authentication.blueprints.oidc import (
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
    "TokenIssuer",
    "TokenRequest",
    "TokenResponse",
    "UserInfo",
]
