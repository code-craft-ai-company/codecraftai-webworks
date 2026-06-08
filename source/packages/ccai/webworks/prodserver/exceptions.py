"""
    Production Server exceptions module.

    This module defines the exception hierarchy for the production server
    including configuration errors and server lifecycle errors.
"""

from typing import List


class ProductionServerError(Exception):
    """
        Base exception for production server errors.
    """
    pass


class ConfigurationError(ProductionServerError):
    """
        Configuration validation error.

        Raised when server configuration values are invalid.
    """

    def __init__(self, errors: List[str]):
        """
            Construct a ConfigurationError exception.

            :param errors: List of validation error messages.
        """
        self._errors = errors
        message = "Configuration validation failed: " + "; ".join(errors)
        super().__init__(message)
        return

    @property
    def errors(self) -> List[str]:
        """
            Get the list of validation errors.

            :returns: List of error messages.
        """
        return self._errors
