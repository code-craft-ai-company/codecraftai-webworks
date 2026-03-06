"""
.. module:: securityschemes
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Security scheme dataclasses for OpenAPI 3.0+ specification generation.

.. moduleauthor:: Automation Mojo LLC

This module provides the security scheme dataclasses used to define authentication
and authorization methods for OpenAPI specification generation. These include the
base SecurityScheme class and specialized subclasses for API key, HTTP, and OAuth2
security schemes as defined in the OpenAPI 3.0 specification.
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class OAuthFlow:
    """
        Single OAuth2 flow configuration.

        Represents an individual OAuth2 flow as defined in the OpenAPI 3.0
        specification. The scopes field is required and maps scope names to
        their descriptions. The URL fields are optional and their applicability
        depends on the flow type.
    """

    scopes: Dict[str, str] = field(default_factory=dict)
    authorization_url: Optional[str] = None
    token_url: Optional[str] = None
    refresh_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """
            Convert to an OpenAPI-compatible OAuth2 flow dictionary.

            The scopes field is always included. URL fields are only included
            when they have non-None values. The field names are serialized
            using camelCase per the OpenAPI specification.

            :returns: A dictionary representation of the OAuth2 flow.
        """
        result = {"scopes": self.scopes}

        if self.authorization_url is not None:
            result["authorizationUrl"] = self.authorization_url

        if self.token_url is not None:
            result["tokenUrl"] = self.token_url

        if self.refresh_url is not None:
            result["refreshUrl"] = self.refresh_url

        return result


@dataclass
class OAuthFlows:
    """
        OAuth2 flows configuration.

        Represents the collection of OAuth2 flows as defined in the OpenAPI 3.0
        specification. Each flow type is optional and corresponds to a different
        OAuth2 grant type.
    """

    implicit: Optional[OAuthFlow] = None
    password: Optional[OAuthFlow] = None
    client_credentials: Optional[OAuthFlow] = None
    authorization_code: Optional[OAuthFlow] = None

    def to_dict(self) -> Dict[str, Any]:
        """
            Convert to an OpenAPI-compatible OAuth2 flows dictionary.

            Only includes flow types that have non-None values. The field names
            are serialized using camelCase per the OpenAPI specification where
            applicable (client_credentials becomes clientCredentials, and
            authorization_code becomes authorizationCode).

            :returns: A dictionary representation of the OAuth2 flows.
        """
        result = {}

        if self.implicit is not None:
            result["implicit"] = self.implicit.to_dict()

        if self.password is not None:
            result["password"] = self.password.to_dict()

        if self.client_credentials is not None:
            result["clientCredentials"] = self.client_credentials.to_dict()

        if self.authorization_code is not None:
            result["authorizationCode"] = self.authorization_code.to_dict()

        return result


@dataclass
class SecurityScheme:
    """
        Base class for OpenAPI security schemes.

        Represents the base security scheme object as defined in the OpenAPI 3.0
        specification. The type field is required and identifies the security
        scheme type. Subclasses provide specialized fields for each scheme type.
    """

    type: str
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """
            Convert to an OpenAPI-compatible security scheme dictionary.

            The type field is always included. The description field is only
            included when it has a non-None value.

            :returns: A dictionary representation of the security scheme.
        """
        result = {"type": self.type}

        if self.description is not None:
            result["description"] = self.description

        return result


@dataclass
class APIKeySecurityScheme(SecurityScheme):
    """
        API key security scheme.

        Represents an API key security scheme as defined in the OpenAPI 3.0
        specification. The API key can be sent in a header, query parameter,
        or cookie.
    """

    type: str = "apiKey"
    name: str = "X-API-Key"
    in_: str = "header"

    def to_dict(self) -> Dict[str, Any]:
        """
            Convert to an OpenAPI-compatible API key security scheme dictionary.

            Includes the base security scheme fields plus the name and in fields.
            The in_ field is serialized as 'in' per the OpenAPI specification.

            :returns: A dictionary representation of the API key security scheme.
        """
        result = super().to_dict()
        result["name"] = self.name
        result["in"] = self.in_

        return result


@dataclass
class HTTPSecurityScheme(SecurityScheme):
    """
        HTTP security scheme for bearer and basic authentication.

        Represents an HTTP security scheme as defined in the OpenAPI 3.0
        specification. Supports bearer token and basic authentication schemes.
    """

    type: str = "http"
    scheme: str = "bearer"
    bearer_format: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """
            Convert to an OpenAPI-compatible HTTP security scheme dictionary.

            Includes the base security scheme fields plus the scheme field.
            The bearer_format field is only included when it has a non-None
            value and is serialized as 'bearerFormat' per the OpenAPI specification.

            :returns: A dictionary representation of the HTTP security scheme.
        """
        result = super().to_dict()
        result["scheme"] = self.scheme

        if self.bearer_format is not None:
            result["bearerFormat"] = self.bearer_format

        return result


@dataclass
class OAuth2SecurityScheme(SecurityScheme):
    """
        OAuth2 security scheme.

        Represents an OAuth2 security scheme as defined in the OpenAPI 3.0
        specification. Contains the OAuth2 flows configuration describing
        the available grant types.
    """

    type: str = "oauth2"
    flows: Optional[OAuthFlows] = None

    def to_dict(self) -> Dict[str, Any]:
        """
            Convert to an OpenAPI-compatible OAuth2 security scheme dictionary.

            Includes the base security scheme fields. The flows field is only
            included when it has a non-None value and is converted by calling
            to_dict() on the OAuthFlows instance.

            :returns: A dictionary representation of the OAuth2 security scheme.
        """
        result = super().to_dict()

        if self.flows is not None:
            result["flows"] = self.flows.to_dict()

        return result
