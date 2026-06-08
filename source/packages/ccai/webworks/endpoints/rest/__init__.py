"""
.. module:: ccai.webworks.endpoints.rest
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: REST API support module providing resource-oriented helpers,
               serialization/validation infrastructure, and standard REST error model.

.. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

from ccai.webworks.endpoints.rest.models import (
    FieldError,
    RESTError,
    ErrorMapping,
    PaginationInfo,
    PaginatedResponse,
    select_status_code,
    build_location_header,
    METHOD_STATUS_CODES as MODELS_METHOD_STATUS_CODES,
    ACTION_POST_STATUS,
    apply_json_merge_patch,
    extract_patch_fields,
    get_removed_fields,
)

from ccai.webworks.endpoints.rest.exceptions import (
    HTTPException,
    NotAcceptable,
    UnsupportedMediaType,
    ValidationError,
)

from ccai.webworks.endpoints.rest.serialization import (
    Serializer,
    Deserializer,
    JSONSerializer,
    JSONDeserializer,
    SerializerRegistry,
    create_default_registry,
)

from ccai.webworks.endpoints.rest.validation import (
    Validator,
)

from ccai.webworks.endpoints.rest.errors import (
    ErrorHandler,
    merge_error_maps,
)

from ccai.webworks.endpoints.rest.negotiation import (
    ContentNegotiator,
    DEFAULT_CONTENT_TYPE,
)

from ccai.webworks.endpoints.rest.resourceendpoint import (
    ResourceEndpoint,
    METHOD_TO_OPERATION,
    METHOD_STATUS_CODES,
    ALL_CRUD_METHODS,
)

from ccai.webworks.endpoints.rest.collectionendpoint import (
    CollectionEndpoint,
)

from ccai.webworks.endpoints.rest.middleware import (
    RESTMiddleware,
    create_rest_middleware,
)

__all__ = [
    # Models
    "FieldError",
    "RESTError",
    "ErrorMapping",
    "PaginationInfo",
    "PaginatedResponse",
    "select_status_code",
    "build_location_header",
    "ACTION_POST_STATUS",
    "apply_json_merge_patch",
    "extract_patch_fields",
    "get_removed_fields",
    # Exceptions
    "HTTPException",
    "NotAcceptable",
    "UnsupportedMediaType",
    "ValidationError",
    # Serialization
    "Serializer",
    "Deserializer",
    "JSONSerializer",
    "JSONDeserializer",
    "SerializerRegistry",
    "create_default_registry",
    # Validation
    "Validator",
    # Error Handling
    "ErrorHandler",
    "merge_error_maps",
    # Content Negotiation
    "ContentNegotiator",
    "DEFAULT_CONTENT_TYPE",
    # Resource Endpoint
    "ResourceEndpoint",
    "METHOD_TO_OPERATION",
    "METHOD_STATUS_CODES",
    "ALL_CRUD_METHODS",
    # Collection Endpoint
    "CollectionEndpoint",
    # Middleware
    "RESTMiddleware",
    "create_rest_middleware",
]
