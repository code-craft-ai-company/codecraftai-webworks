"""
.. module:: exceptions
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Exception classes for endpoint registration errors.

.. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

from typing import Any, List, Optional


class EndpointRegistrationError(Exception):
    """
        Raised when endpoint registration fails due to missing
        mandatory metadata or invalid configuration.
        
        This exception provides detailed information about what
        went wrong during registration, including the endpoint
        class and any missing required fields.
        
        :param message: Description of the registration error.
        :param endpoint: The endpoint class that failed registration.
        :param missing_fields: List of field names that were missing.
    """
    
    def __init__(
        self,
        message: str,
        endpoint: Optional[Any] = None,
        missing_fields: Optional[List[str]] = None
    ):
        self.endpoint = endpoint
        self.missing_fields = missing_fields or []
        super().__init__(message)


class SchemaInspectionError(Exception):
    """
        Raised when schema inspection fails for request/response schemas.
        
        This exception is raised when the system cannot extract
        JSON schema information from a provided schema type.
        
        :param schema: The schema type that failed inspection.
        :param reason: Description of why inspection failed.
    """
    
    def __init__(self, schema: Any, reason: str):
        self.schema = schema
        self.reason = reason
        schema_name = getattr(schema, "__name__", str(schema))
        super().__init__(f"Failed to inspect schema {schema_name}: {reason}")
