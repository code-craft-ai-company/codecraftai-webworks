"""
.. module:: errors
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Security error classes for standardized error responses.

.. moduleauthor:: Code Craft AI LLC

This module provides security-related exception classes that produce
structured error responses for authentication failures, authorization
denials, policy validation issues, and security completeness checks.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

from typing import Any, Dict, List, Optional


class SecurityError(Exception):
    """
        Base class for security-related errors.

        Provides a structured error representation with an error code,
        HTTP status code, human-readable message, and optional details
        dictionary. The :meth:`to_response_body` method converts the
        error into a dictionary suitable for HTTP response bodies.
    """

    def __init__(self, message: str, error_code: str, status_code: int,
                 details: Optional[Dict[str, Any]] = None):
        """
            Initializes a SecurityError.

            :param message: Human-readable error message.
            :param error_code: Machine-readable error code string.
            :param status_code: HTTP status code for the error response.
            :param details: Optional dictionary of additional error details.
        """
        self.message = message
        self.error_code = error_code
        self.status_code = status_code

        if details is not None:
            self.details = details
        else:
            self.details = {}

        super().__init__(message)
        return

    def to_response_body(self, include_details: bool = False) -> Dict[str, Any]:
        """
            Convert this error to a response body dictionary.

            The returned dictionary always contains 'error' and 'message'
            keys. When *include_details* is True the 'details' key is
            also included.

            :param include_details: Whether to include the details dict.

            :returns: A dictionary suitable for an HTTP error response body.
        """
        body: Dict[str, Any] = {
            "error": self.error_code,
            "message": self.message,
        }

        if include_details is True:
            body["details"] = self.details

        return body



class AuthenticationError(SecurityError):
    """
        Raised when authentication fails.

        Always uses HTTP 401 status code. Tracks the authentication
        schemes supported by the server so a ``WWW-Authenticate``
        header can be generated for the response.
    """

    def __init__(self, message: str = "Authentication required",
                 schemes: Optional[List[str]] = None):
        """
            Initializes an AuthenticationError.

            :param message: Human-readable error message.
            :param schemes: List of supported authentication scheme names.
        """
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_REQUIRED",
            status_code=401,
        )

        if schemes is not None:
            self.schemes = schemes
        else:
            self.schemes = []

        return

    def get_www_authenticate_header(self) -> str:
        """
            Build the value for a ``WWW-Authenticate`` response header.

            When schemes are configured the header lists each scheme
            separated by a comma and space. When no schemes are
            configured the header defaults to ``Bearer``.

            :returns: A string suitable for the WWW-Authenticate header.
        """
        if len(self.schemes) > 0:
            header_value = ", ".join(self.schemes)
        else:
            header_value = "Bearer"

        return header_value


class AuthorizationError(SecurityError):
    """
        Raised when authorization fails.

        Always uses HTTP 403 status code. Stores an internal reason
        for logging and debugging purposes, but the reason is never
        exposed in the response body to avoid leaking security details.
    """

    def __init__(self, message: str = "Access denied",
                 reason: Optional[str] = None):
        """
            Initializes an AuthorizationError.

            :param message: Human-readable error message.
            :param reason: Internal reason for the denial (not exposed in responses).
        """
        super().__init__(
            message=message,
            error_code="ACCESS_DENIED",
            status_code=403,
        )
        self._internal_reason = reason
        return

    def to_response_body(self, include_details: bool = False) -> Dict[str, Any]:
        """
            Convert this error to a response body dictionary.

            Overrides the base implementation to ensure the internal
            reason is never included in the response body, even when
            *include_details* is True.

            :param include_details: Whether to include the details dict.

            :returns: A dictionary suitable for an HTTP error response body.
        """
        body: Dict[str, Any] = {
            "error": self.error_code,
            "message": self.message,
        }

        if include_details is True:
            # Filter out any internal reason from details
            safe_details = {}
            for key, value in self.details.items():
                safe_details[key] = value
            body["details"] = safe_details

        return body


class PolicyValidationError(SecurityError):
    """
        Raised when an invalid policy is attached to an endpoint.

        Stores a reference to the offending policy object for
        diagnostic purposes. Uses HTTP 500 status code since this
        represents a server-side configuration error.
    """

    def __init__(self, message: str, policy: Any):
        """
            Initializes a PolicyValidationError.

            :param message: Human-readable description of the validation failure.
            :param policy: The invalid policy object that caused the error.
        """
        super().__init__(
            message=message,
            error_code="INVALID_POLICY",
            status_code=500,
        )
        self.policy = policy
        return


class SecurityCompletenessError(SecurityError):
    """
        Raised when security completeness validation fails at startup.

        Contains the list of endpoint paths that do not have an
        explicit or inherited security policy. Uses HTTP 500 status
        code since this represents a server-side configuration error.
    """

    def __init__(self, unprotected_endpoints: List[str]):
        """
            Initializes a SecurityCompletenessError.

            :param unprotected_endpoints: List of endpoint paths without policies.
        """
        endpoint_count = len(unprotected_endpoints)
        message = (
            f"Security completeness check failed: "
            f"{endpoint_count} unprotected endpoints"
        )

        super().__init__(
            message=message,
            error_code="SECURITY_INCOMPLETE",
            status_code=500,
        )
        self.unprotected_endpoints = unprotected_endpoints
        return
