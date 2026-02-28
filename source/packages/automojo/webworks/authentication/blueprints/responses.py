"""
.. module:: responses
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Standard authentication response and error dataclasses for blueprints.

.. moduleauthor:: Automation Mojo LLC

This module provides the :class:`AuthResponse` and :class:`AuthError` dataclasses
used across all authentication blueprints for consistent response formatting.
The error format follows RFC 6749 conventions for OAuth 2.0 error responses.
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from dataclasses import dataclass
from typing import Optional


@dataclass
class AuthResponse:
    """
        Standard authentication response structure.

        Encapsulates the fields commonly returned by authentication endpoints
        including access tokens, refresh tokens, and scope information.

        :param access_token: The issued access token.
        :param token_type: The type of token issued (default "Bearer").
        :param expires_in: Token lifetime in seconds.
        :param refresh_token: An optional refresh token for obtaining new access tokens.
        :param scope: The scope of the access token.
    """

    access_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_in: Optional[int] = None
    refresh_token: Optional[str] = None
    scope: Optional[str] = None

    def to_dict(self) -> dict:
        """
            Convert the response to a dictionary, omitting unset fields.

            :returns: A dictionary representation of the response containing
                      only fields that have been set.
        """
        result = {}

        if self.access_token:
            result["access_token"] = self.access_token
            result["token_type"] = self.token_type

        if self.expires_in:
            result["expires_in"] = self.expires_in

        if self.refresh_token:
            result["refresh_token"] = self.refresh_token

        if self.scope:
            result["scope"] = self.scope

        return result


@dataclass
class AuthError:
    """
        Standard authentication error response per RFC 6749.

        Provides a structured error representation with an error code,
        optional human-readable description, and optional URI pointing
        to additional error documentation.

        :param error: A single ASCII error code string.
        :param error_description: Optional human-readable description of the error.
        :param error_uri: Optional URI identifying a human-readable web page with
                          information about the error.
    """

    error: str
    error_description: Optional[str] = None
    error_uri: Optional[str] = None

    def to_dict(self) -> dict:
        """
            Convert the error to a dictionary, omitting unset fields.

            :returns: A dictionary representation of the error containing
                      the error code and any optional fields that have been set.
        """
        result = {"error": self.error}

        if self.error_description:
            result["error_description"] = self.error_description

        if self.error_uri:
            result["error_uri"] = self.error_uri

        return result
