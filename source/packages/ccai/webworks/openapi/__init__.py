"""
.. module:: openapi
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Package providing OpenAPI 3.0+ specification generation and interactive
        documentation hosting for the ccai web framework.

.. moduleauthor:: Code Craft AI LLC

This package provides OpenAPI specification generation and documentation hosting including:

- Automatic OpenAPI 3.0+ specification generation from endpoint descriptors
- Schema conversion from Python types (dataclasses, Pydantic models) to JSON Schema
- Interactive API documentation via Swagger UI and ReDoc
- Specification validation against the OpenAPI 3.0 schema
- Specification caching for production and development modes
- Export to JSON and YAML formats
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


# Configuration dataclasses
from ccai.webworks.openapi.configuration import (
    OpenAPIInfo,
    ContactObject,
    LicenseObject,
    ServerObject,
    ServerVariable,
    ExternalDocs,
)

# Security scheme dataclasses
from ccai.webworks.openapi.securityschemes import (
    SecurityScheme,
    APIKeySecurityScheme,
    HTTPSecurityScheme,
    OAuth2SecurityScheme,
    OAuthFlows,
    OAuthFlow,
)

# Schema converter
from ccai.webworks.openapi.schemaconverter import SchemaConverter

# OpenAPI generator
from ccai.webworks.openapi.generator import OpenAPIGenerator

# Validation
from ccai.webworks.openapi.validation import (
    OpenAPIValidator,
    ValidationIssue,
    SpecificationValidationError,
)

# Swagger UI blueprint
from ccai.webworks.openapi.swaggerui import SwaggerUIBlueprint

# ReDoc blueprint
from ccai.webworks.openapi.redoc import ReDocBlueprint

# Specification caching
from ccai.webworks.openapi.cache import (
    SpecificationCache,
    CachedOpenAPIGenerator,
)

# CLI tooling
from ccai.webworks.openapi.cli import (
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
