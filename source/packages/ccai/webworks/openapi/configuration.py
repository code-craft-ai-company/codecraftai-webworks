"""
.. module:: configuration
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Configuration dataclasses for OpenAPI 3.0+ specification generation.

.. moduleauthor:: Code Craft AI LLC

This module provides the configuration dataclasses used to define metadata
for OpenAPI specification generation. These include the info object, contact
and license information, server definitions, server variables, and external
documentation links.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ContactObject:
    """
        OpenAPI contact object containing API contact information.

        Represents the contact information for the exposed API as defined
        in the OpenAPI 3.0 specification.
    """

    name: Optional[str] = None
    url: Optional[str] = None
    email: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """
            Convert to an OpenAPI-compatible contact dictionary.

            Only includes fields that have non-None values.

            :returns: A dictionary representation of the contact object.
        """
        result = {}

        if self.name is not None:
            result["name"] = self.name

        if self.url is not None:
            result["url"] = self.url

        if self.email is not None:
            result["email"] = self.email

        return result


@dataclass
class LicenseObject:
    """
        OpenAPI license object containing API license information.

        Represents the license information for the exposed API as defined
        in the OpenAPI 3.0 specification.
    """

    name: str
    url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """
            Convert to an OpenAPI-compatible license dictionary.

            The name field is always included. The url field is only
            included when it has a non-None value.

            :returns: A dictionary representation of the license object.
        """
        result = {"name": self.name}

        if self.url is not None:
            result["url"] = self.url

        return result


@dataclass
class OpenAPIInfo:
    """
        OpenAPI info object configuration.

        Represents the metadata about the API as defined in the OpenAPI 3.0
        specification. The title and version fields are required by the
        OpenAPI specification.
    """

    title: str
    version: str
    description: Optional[str] = None
    terms_of_service: Optional[str] = None
    contact: Optional[ContactObject] = None
    license: Optional[LicenseObject] = None

    def to_dict(self) -> Dict[str, Any]:
        """
            Convert to an OpenAPI-compatible info dictionary.

            The title and version fields are always included. Optional fields
            are only included when they have non-None values. The terms_of_service
            field is serialized as 'termsOfService' per the OpenAPI specification.

            :returns: A dictionary representation of the info object.
        """
        result = {
            "title": self.title,
            "version": self.version
        }

        if self.description is not None:
            result["description"] = self.description

        if self.terms_of_service is not None:
            result["termsOfService"] = self.terms_of_service

        if self.contact is not None:
            result["contact"] = self.contact.to_dict()

        if self.license is not None:
            result["license"] = self.license.to_dict()

        return result


@dataclass
class ServerVariable:
    """
        OpenAPI server variable for URL template substitution.

        Represents a server variable for server URL template substitution
        as defined in the OpenAPI 3.0 specification.
    """

    default: str
    enum: Optional[List[str]] = None
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """
            Convert to an OpenAPI-compatible server variable dictionary.

            The default field is always included. Optional fields are only
            included when they have non-None values.

            :returns: A dictionary representation of the server variable.
        """
        result = {"default": self.default}

        if self.enum is not None:
            result["enum"] = self.enum

        if self.description is not None:
            result["description"] = self.description

        return result


@dataclass
class ServerObject:
    """
        OpenAPI server object describing an API server URL.

        Represents a server object as defined in the OpenAPI 3.0 specification.
        The url field is required and may contain server variables in curly braces.
    """

    url: str
    description: Optional[str] = None
    variables: Optional[Dict[str, ServerVariable]] = None

    def to_dict(self) -> Dict[str, Any]:
        """
            Convert to an OpenAPI-compatible server dictionary.

            The url field is always included. The variables field is converted
            by calling to_dict() on each ServerVariable value.

            :returns: A dictionary representation of the server object.
        """
        result = {"url": self.url}

        if self.description is not None:
            result["description"] = self.description

        if self.variables is not None:
            result["variables"] = {
                k: v.to_dict() for k, v in self.variables.items()
            }

        return result


@dataclass
class ExternalDocs:
    """
        OpenAPI external documentation object.

        Represents a reference to external documentation as defined in
        the OpenAPI 3.0 specification.
    """

    url: str
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """
            Convert to an OpenAPI-compatible external documentation dictionary.

            The url field is always included. The description field is only
            included when it has a non-None value.

            :returns: A dictionary representation of the external docs object.
        """
        result = {"url": self.url}

        if self.description is not None:
            result["description"] = self.description

        return result
