"""
    Endpoint Abstractions package.
    
    This package provides a declarative, composable system for defining HTTP
    endpoints with centralized access control, metadata, and routing configuration.
    It supports both single-endpoint handlers and blueprint-style attachments,
    enabling a repository-wide endpoint map to be derived from code without
    manual duplication.
"""

from ccai.webworks.endpoints.doc import Doc
from ccai.webworks.endpoints.ratelimit import RateLimit
from ccai.webworks.endpoints.accesspolicy import AccessPolicy
from ccai.webworks.endpoints.constraints import EndpointConstraints
from ccai.webworks.endpoints.descriptor import EndpointDescriptor
from ccai.webworks.endpoints.registry import EndpointRegistry, EndpointConflictError
from ccai.webworks.endpoints.exceptions import EndpointRegistrationError, SchemaInspectionError
from ccai.webworks.endpoints.endpoint import Endpoint
from ccai.webworks.endpoints.blueprint import Blueprint, BlueprintConfig
from ccai.webworks.endpoints.merging import ConstraintMerger
from ccai.webworks.endpoints.restendpoint import RestEndpoint
from ccai.webworks.endpoints.restblueprint import RestBlueprint
from ccai.webworks.endpoints.router import Router


__all__ = [
    "Doc",
    "RateLimit",
    "AccessPolicy",
    "EndpointConstraints",
    "EndpointDescriptor",
    "EndpointRegistry",
    "EndpointConflictError",
    "EndpointRegistrationError",
    "SchemaInspectionError",
    "Endpoint",
    "Blueprint",
    "BlueprintConfig",
    "ConstraintMerger",
    "RestEndpoint",
    "RestBlueprint",
    "Router",
]
