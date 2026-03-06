"""
.. module:: openapi
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Package providing OpenAPI 3.0+ specification generation and interactive
        documentation hosting for the automojo web framework.

.. moduleauthor:: Automation Mojo LLC

This package provides OpenAPI specification generation and documentation hosting including:

- Automatic OpenAPI 3.0+ specification generation from endpoint descriptors
- Schema conversion from Python types (dataclasses, Pydantic models) to JSON Schema
- Interactive API documentation via Swagger UI and ReDoc
- Specification validation against the OpenAPI 3.0 schema
- Specification caching for production and development modes
- Export to JSON and YAML formats
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


# Configuration dataclasses
from automojo.webworks.openapi.configuration import (
    OpenAPIInfo,
    ContactObject,
    LicenseObject,
    ServerObject,
    ServerVariable,
    ExternalDocs,
)

# Security scheme dataclasses
from automojo.webworks.openapi.securityschemes import (
    SecurityScheme,
    APIKeySecurityScheme,
    HTTPSecurityScheme,
    OAuth2SecurityScheme,
    OAuthFlows,
    OAuthFlow,
)

# Schema converter
from automojo.webworks.openapi.schemaconverter import SchemaConverter

# OpenAPI generator
from automojo.webworks.openapi.generator import OpenAPIGenerator

# Validation
from automojo.webworks.openapi.validation import (
    OpenAPIValidator,
    ValidationIssue,
    SpecificationValidationError,
)

# Swagger UI blueprint
from automojo.webworks.openapi.swaggerui import SwaggerUIBlueprint

# ReDoc blueprint
from automojo.webworks.openapi.redoc import ReDocBlueprint

# Specification caching
from automojo.webworks.openapi.cache import (
    SpecificationCache,
    CachedOpenAPIGenerator,
)

# CLI tooling
from automojo.webworks.openapi.cli import (
    GenerateCommand,
    ValidateCommand,
    create_openapi_group,
)


__all__ = [
    # Configuration
    "OpenAPIInfo",
    "ContactObject",
    "LicenseObject",
    "ServerObject",
    "ServerVariable",
    "ExternalDocs",

    # Security Schemes
    "SecurityScheme",
    "APIKeySecurityScheme",
    "HTTPSecurityScheme",
    "OAuth2SecurityScheme",
    "OAuthFlows",
    "OAuthFlow",

    # Schema Converter
    "Schema_Converter",

    # Generator
    "OpenAPI_Generator",

    # Validation
    "OpenAPIValidator",
    "ValidationIssue",
    "SpecificationValidationError",

    # Swagger UI
    "Swagger_UI_Blueprint",

    # ReDoc
    "ReDoc_Blueprint",

    # Caching
    "SpecificationCache",
    "CachedOpenAPIGenerator",

    # CLI
    "GenerateCommand",
    "ValidateCommand",
    "create_openapi_group",
]
