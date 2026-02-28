"""
.. module:: exceptions
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Exception classes for the configuration system.

.. moduleauthor:: Automation Mojo LLC

This module contains the exception classes used throughout the configuration
system for error handling and reporting.
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from pathlib import Path
from typing import Any, List, Optional, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from automojo.webworks.configuration.core import ValidationError


class ConfigurationError(Exception):
    """
        Base exception for configuration-related errors.
        
        This is the base class for all configuration exceptions. It provides
        a consistent interface with an optional key parameter to identify
        which configuration key caused the error.
        
        :param message: Human-readable error message.
        :param key: Optional configuration key that caused the error.
    """
    
    def __init__(self, message: str, key: Optional[str] = None):
        """
            Initialize the ConfigurationError.
            
            :param message: Human-readable error message.
            :param key: Optional configuration key that caused the error.
        """
        self.key = key
        self.message = message
        super().__init__(message)


class ConfigurationValidationError(ConfigurationError):
    """
        Raised when configuration validation fails.
        
        This exception is raised when one or more configuration values fail
        validation against their schema definitions. It contains a list of
        all validation errors that occurred.
        
        :param errors: List of ValidationError instances describing each failure.
    """
    
    def __init__(self, errors: List['ValidationError']):
        """
            Initialize the ConfigurationValidationError.
            
            :param errors: List of ValidationError instances describing each failure.
        """
        self.errors = errors
        message = f"Configuration validation failed with {len(errors)} error(s):\n"
        for error in errors:
            message += f"  - {error.key}: {error.message}\n"
        super().__init__(message)


class ConfigurationFileNotFoundError(ConfigurationError):
    """
        Raised when a referenced configuration file does not exist.
        
        This exception is raised when a configuration file that is required
        or referenced (e.g., via an include directive) cannot be found.
        
        :param path: The path to the configuration file that was not found.
        :param referenced_from: Optional path to the file that referenced the missing file.
    """
    
    def __init__(self, path: Path, referenced_from: Optional[Path] = None):
        """
            Initialize the ConfigurationFileNotFoundError.
            
            :param path: The path to the configuration file that was not found.
            :param referenced_from: Optional path to the file that referenced the missing file.
        """
        self.path = path
        self.referenced_from = referenced_from
        message = f"Configuration file not found: {path}"
        if referenced_from:
            message += f" (referenced from {referenced_from})"
        super().__init__(message)


class ConfigurationFrozenError(ConfigurationError):
    """
        Raised when attempting to modify frozen configuration.
        
        This exception is raised when an attempt is made to modify a
        configuration value after the configuration has been frozen.
        
        :param key: The configuration key that was attempted to be modified.
    """
    
    def __init__(self, key: str):
        """
            Initialize the ConfigurationFrozenError.
            
            :param key: The configuration key that was attempted to be modified.
        """
        super().__init__(
            f"Cannot modify configuration key '{key}': configuration is frozen",
            key=key
        )


class ConfigurationTypeError(ConfigurationError):
    """
        Raised when configuration type coercion fails.
        
        This exception is raised when a configuration value cannot be
        coerced to its declared type in the schema.
        
        :param key: The configuration key that failed type coercion.
        :param expected_type: The expected type from the schema.
        :param actual_value: The actual value that could not be coerced.
    """
    
    def __init__(self, key: str, expected_type: Type, actual_value: Any):
        """
            Initialize the ConfigurationTypeError.
            
            :param key: The configuration key that failed type coercion.
            :param expected_type: The expected type from the schema.
            :param actual_value: The actual value that could not be coerced.
        """
        self.expected_type = expected_type
        self.actual_value = actual_value
        super().__init__(
            f"Cannot coerce '{key}' value '{actual_value}' to type {expected_type.__name__}",
            key=key
        )
