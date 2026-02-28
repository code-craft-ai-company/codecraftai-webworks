"""
    Endpoint Abstractions package.
    
    This package provides a declarative, composable system for defining HTTP
    endpoints with centralized access control, metadata, and routing configuration.
    It supports both single-endpoint handlers and blueprint-style attachments,
    enabling a repository-wide endpoint map to be derived from code without
    manual duplication.
"""

from automojo.webworks.endpoints.doc import Doc
from automojo.webworks.endpoints.ratelimit import RateLimit
from automojo.webworks.endpoints.accesspolicy import AccessPolicy
from automojo.webworks.endpoints.constraints import EndpointConstraints
from automojo.webworks.endpoints.descriptor import EndpointDescriptor
from automojo.webworks.endpoints.registry import EndpointRegistry, EndpointConflictError
from automojo.webworks.endpoints.exceptions import EndpointRegistrationError, SchemaInspectionError
from automojo.webworks.endpoints.endpoint import Endpoint
from automojo.webworks.endpoints.blueprint import Blueprint, BlueprintConfig
from automojo.webworks.endpoints.merging import ConstraintMerger
from automojo.webworks.endpoints.restendpoint import RestEndpoint
from automojo.webworks.endpoints.restblueprint import RestBlueprint
from automojo.webworks.endpoints.router import Router


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
