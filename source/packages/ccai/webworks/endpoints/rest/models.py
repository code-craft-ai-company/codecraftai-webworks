"""
.. module:: ccai.webworks.endpoints.rest.models
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Core data models for REST API support including error structures
               and response helpers.

.. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

import logging

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ccai.webworks.endpoints.rest.exceptions import ValidationError


# Module-level logger. ``build_location_header`` falls back to ID
# extraction when a user-supplied ``get_resource_url_func`` raises;
# the breadcrumb makes the fallback visible without breaking the
# response.
logger = logging.getLogger(__name__)


@dataclass
class FieldError:
    """
        Single field validation error.
        
        This dataclass represents a validation error for a specific field
        in a request payload. It includes the field path, an error code,
        and a human-readable message.
        
        Attributes:
            field: Field path, e.g., "user.email" for nested fields.
            code: Error code, e.g., "required", "invalid", "type_error".
            message: Human-readable error message.
    """
    
    field: str
    code: str
    message: str


@dataclass
class RESTError:
    """
        Standard REST error response structure.
        
        This dataclass represents the standardized error response format
        for REST APIs. It provides a consistent structure that clients
        can reliably parse and handle.
        
        Attributes:
            error: Error code string, e.g., "validation_error", "not_found".
            message: Human-readable description of the error.
            details: Optional dictionary with additional context about the error.
            field_errors: Optional list of field-level validation errors.
    """
    
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    field_errors: Optional[List[FieldError]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """
            Convert the RESTError to a dictionary for serialization.
            
            Returns:
                Dictionary representation of the error suitable for JSON serialization.
                Only includes non-None optional fields.
        """
        result: Dict[str, Any] = {
            "error": self.error,
            "message": self.message
        }
        
        if self.details is not None:
            result["details"] = self.details
        
        if self.field_errors is not None:
            result["field_errors"] = [
                {"field": fe.field, "code": fe.code, "message": fe.message}
                for fe in self.field_errors
            ]
        
        return result


@dataclass
class ErrorMapping:
    """
        Mapping from exception type to HTTP error response.
        
        This dataclass defines how a specific exception type should be
        converted to an HTTP error response. It includes the HTTP status
        code, error code, and an optional message template that supports
        attribute interpolation from the exception.
        
        Attributes:
            status_code: HTTP status code to return (e.g., 400, 404, 500).
            error_code: Error code string for the response (e.g., "not_found").
            message_template: Optional message template supporting {attr} interpolation
                              from exception attributes.
    """
    
    status_code: int
    error_code: str
    message_template: Optional[str] = None
    
    def build_response(self, exception: Exception) -> RESTError:
        """
            Build a RESTError from an exception using this mapping.
            
            The message is constructed by interpolating exception attributes
            into the message_template. If no template is provided, the
            string representation of the exception is used.
            
            Args:
                exception: The caught exception to convert.
            
            Returns:
                RESTError with the mapped error code and interpolated message.
        """
        if self.message_template is not None:
            # Interpolate exception attributes into the template
            try:
                # Build a dict of exception attributes for interpolation
                attrs = {}
                for attr_name in dir(exception):
                    if not attr_name.startswith('_'):
                        try:
                            attrs[attr_name] = getattr(exception, attr_name)
                        except Exception:
                            pass
                
                # Also add the string representation as a default
                attrs[''] = str(exception)
                
                message = self.message_template.format(**attrs)
            except (KeyError, IndexError, ValueError):
                # If interpolation fails, fall back to exception string
                message = str(exception)
        else:
            message = str(exception)
        
        # Handle ValidationError specially to include field_errors
        field_errors = None
        if hasattr(exception, 'field_errors'):
            field_errors = getattr(exception, 'field_errors', None)
        
        return RESTError(
            error=self.error_code,
            message=message,
            field_errors=field_errors
        )


@dataclass
class PaginationInfo:
    """
        Pagination metadata for collection responses.
        
        This dataclass contains all pagination information needed for
        paginated collection responses, including the current page,
        total counts, and navigation links.
        
        Attributes:
            total: Total number of items across all pages.
            page: Current page number (1-indexed).
            page_size: Number of items per page.
            total_pages: Total number of pages.
            next: URL to the next page, or None if on last page.
            prev: URL to the previous page, or None if on first page.
            first: URL to the first page.
            last: URL to the last page.
    """
    
    total: int
    page: int
    page_size: int
    total_pages: int
    next: Optional[str] = None
    prev: Optional[str] = None
    first: Optional[str] = None
    last: Optional[str] = None
    
    @classmethod
    def create(
        cls,
        total: int,
        page: int,
        page_size: int,
        base_url: str
    ) -> "PaginationInfo":
        """
            Create PaginationInfo with computed fields and navigation links.
            
            This factory method computes the total_pages and generates
            navigation links based on the provided parameters.
            
            Args:
                total: Total number of items.
                page: Current page number (1-indexed).
                page_size: Number of items per page.
                base_url: Base URL for constructing navigation links.
            
            Returns:
                PaginationInfo instance with all fields populated.
        """
        # Handle edge cases
        if total < 0:
            total = 0
        if page_size <= 0:
            page_size = 1
        if page < 1:
            page = 1
        
        # Compute total pages (ceiling division)
        if total == 0:
            total_pages = 1
        else:
            total_pages = (total + page_size - 1) // page_size
        
        # Clamp page to valid range
        if page > total_pages:
            page = total_pages
        
        # Build navigation links
        # Ensure base_url doesn't have trailing ?
        base_url = base_url.rstrip('?')
        
        # Determine separator for query params
        separator = '&' if '?' in base_url else '?'
        
        def build_link(target_page: int) -> str:
            return f"{base_url}{separator}page={target_page}&page_size={page_size}"
        
        # First and last links
        first_link = build_link(1)
        last_link = build_link(total_pages)
        
        # Next link (None if on last page)
        next_link = build_link(page + 1) if page < total_pages else None
        
        # Prev link (None if on first page)
        prev_link = build_link(page - 1) if page > 1 else None
        
        return cls(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            next=next_link,
            prev=prev_link,
            first=first_link,
            last=last_link
        )


@dataclass
class PaginatedResponse:
    """
        Paginated collection response.
        
        This dataclass represents a paginated response containing a list
        of items and pagination metadata. It provides a standard structure
        for collection endpoints that support pagination.
        
        Attributes:
            items: List of items for the current page.
            pagination: PaginationInfo with pagination metadata.
    """
    
    items: List[Any]
    pagination: PaginationInfo
    
    def to_dict(self) -> Dict[str, Any]:
        """
            Convert the PaginatedResponse to a dictionary for serialization.
            
            Returns:
                Dictionary representation suitable for JSON serialization.
                The structure includes items and nested pagination info
                with navigation links.
        """
        return {
            "items": self.items,
            "pagination": {
                "total": self.pagination.total,
                "page": self.pagination.page,
                "page_size": self.pagination.page_size,
                "total_pages": self.pagination.total_pages,
                "links": {
                    "next": self.pagination.next,
                    "prev": self.pagination.prev,
                    "first": self.pagination.first,
                    "last": self.pagination.last,
                }
            }
        }


@dataclass
class BulkItemError:
    """
        Error for a single item in a bulk operation.
        
        This dataclass represents an error that occurred while processing
        a single item in a bulk operation. It includes the index of the
        item in the original request list, the item itself, and the error
        details.
        
        Attributes:
            index: Index of the item in the original request list (0-indexed).
            item: The item that failed processing.
            error: RESTError containing error details.
    """
    
    index: int
    item: Any
    error: "RESTError"


@dataclass
class BulkOperationResult:
    """
        Result of a bulk operation with per-item status.
        
        This dataclass represents the result of a bulk operation (create,
        update, or delete). It contains lists of successfully processed
        items and failed items with their errors.
        
        The total number of results (succeeded + failed) should always
        equal the number of items in the original request.
        
        Attributes:
            succeeded: List of successfully processed items.
            failed: List of BulkItemError objects for failed items.
    """
    
    succeeded: List[Any]
    failed: List[BulkItemError]
    
    @property
    def success_count(self) -> int:
        """
            Get the number of successfully processed items.
            
            Returns:
                Count of items in the succeeded list.
        """
        return len(self.succeeded)
    
    @property
    def failure_count(self) -> int:
        """
            Get the number of failed items.
            
            Returns:
                Count of items in the failed list.
        """
        return len(self.failed)
    
    @property
    def all_succeeded(self) -> bool:
        """
            Check if all items were processed successfully.
            
            Returns:
                True if no items failed, False otherwise.
        """
        return len(self.failed) == 0
    
    def to_dict(self) -> Dict[str, Any]:
        """
            Convert the BulkOperationResult to a dictionary for serialization.
            
            Returns:
                Dictionary representation suitable for JSON serialization.
        """
        return {
            "succeeded": self.succeeded,
            "failed": [
                {
                    "index": item_error.index,
                    "item": item_error.item,
                    "error": item_error.error.to_dict()
                }
                for item_error in self.failed
            ],
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "all_succeeded": self.all_succeeded
        }


# HTTP method to default status code mapping
# This defines the standard REST convention for response status codes
METHOD_STATUS_CODES: Dict[str, int] = {
    "GET": 200,
    "POST": 201,  # Created
    "PUT": 200,
    "PATCH": 200,
    "DELETE": 204,  # No Content
}

# Status code for POST that doesn't create (action endpoints)
ACTION_POST_STATUS: int = 200


def select_status_code(
    method: str,
    handler_result: Any,
    status_code_override: Optional[int] = None
) -> tuple:
    """
        Select the appropriate HTTP status code for a response.
        
        This function implements the status code selection logic for REST
        responses. It supports:
        
        1. Default status codes based on HTTP method (GET→200, POST→201,
           PUT→200, PATCH→200, DELETE→204)
        2. Override via status_code_override parameter (from endpoint attribute)
        3. Handler returning (data, status_code) tuple for custom status codes
        
        Args:
            method: HTTP method string (e.g., "GET", "POST").
            handler_result: The result returned by the handler. Can be:
                - Any data value (uses default or override status code)
                - A tuple of (data, status_code) for custom status codes
            status_code_override: Optional status code from endpoint's
                                  status_code attribute.
        
        Returns:
            A tuple of (data, status_code) where data is the response data
            and status_code is the selected HTTP status code.
    """
    # Check if handler returned a (data, status_code) tuple
    if isinstance(handler_result, tuple) and len(handler_result) == 2:
        data, explicit_status = handler_result
        # Validate that the second element looks like a status code
        if isinstance(explicit_status, int) and 100 <= explicit_status < 600:
            return (data, explicit_status)
        # If not a valid status code, treat the whole tuple as data
        data = handler_result
    else:
        data = handler_result
    
    # Use status_code_override if provided
    if status_code_override is not None:
        return (data, status_code_override)
    
    # Use default status code for the HTTP method
    method_upper = method.upper()
    default_status = METHOD_STATUS_CODES.get(method_upper, 200)
    
    return (data, default_status)


def build_location_header(
    method: str,
    status_code: int,
    resource: Any,
    get_resource_url_func: Optional[callable] = None
) -> Optional[str]:
    """
        Build the Location header for created resources.
        
        This function generates the Location header value for POST requests
        that create resources (status code 201). The Location header contains
        the URL of the newly created resource.
        
        Args:
            method: HTTP method string (e.g., "POST").
            status_code: The response status code.
            resource: The created resource object.
            get_resource_url_func: Optional callable that takes a resource
                                   and returns its URL. If not provided,
                                   attempts to extract ID from resource.
        
        Returns:
            The Location header value (URL string) or None if:
            - The method is not POST
            - The status code is not 201
            - The resource has no identifier
            - The URL cannot be determined
    """
    # Only generate Location header for POST/201 responses
    if method.upper() != "POST" or status_code != 201:
        return None
    
    if resource is None:
        return None
    
    # Use provided function if available
    if get_resource_url_func is not None:
        try:
            url = get_resource_url_func(resource)
            return url
        except Exception:
            # Caller-supplied URL builders are best-effort; log so a
            # silently-falling-back implementation is visible in the
            # journal.
            logger.exception(
                "build_location_header: get_resource_url_func raised; "
                "falling back to id-based extraction"
            )
    
    # Fall back to extracting ID from resource
    resource_id = None
    
    # Try common ID attribute names
    for attr_name in ('id', 'pk', 'identifier', 'resource_id'):
        if hasattr(resource, attr_name):
            resource_id = getattr(resource, attr_name)
            if resource_id is not None:
                break
    
    # Try dict-like access
    if resource_id is None and hasattr(resource, '__getitem__'):
        for key in ('id', 'pk', 'identifier', 'resource_id'):
            try:
                resource_id = resource[key]
                if resource_id is not None:
                    break
            except (KeyError, TypeError):
                pass
    
    if resource_id is None:
        return None
    
    # Return just the ID - the full URL construction depends on context
    # The caller should prepend the base path
    return str(resource_id)


# Sentinel value to indicate a field should be removed
_REMOVE_FIELD = object()


def apply_json_merge_patch(
    original: Dict[str, Any],
    patch: Dict[str, Any],
    remove_null_fields: bool = True
) -> Dict[str, Any]:
    """
        Apply a JSON Merge Patch (RFC 7396) to an original object.
        
        JSON Merge Patch semantics:
        - Fields present in patch with non-null values: update the field
        - Fields present in patch with null values: remove the field (if remove_null_fields=True)
        - Fields not present in patch: retain original value
        
        This function implements RFC 7396 semantics for partial updates,
        where null values in the patch indicate field removal.
        
        Args:
            original: The original object as a dictionary.
            patch: The patch to apply as a dictionary.
            remove_null_fields: If True, null values in patch remove fields.
                               If False, null values are treated as actual values.
        
        Returns:
            A new dictionary with the patch applied. The original is not modified.
        
        Example:
            >>> original = {"name": "Alice", "email": "alice@example.com", "age": 30}
            >>> patch = {"email": None, "age": 31}
            >>> result = apply_json_merge_patch(original, patch)
            >>> result
            {"name": "Alice", "age": 31}  # email removed, age updated, name preserved
    """
    if not isinstance(original, dict):
        # If original is not a dict, the patch replaces it entirely
        return dict(patch) if isinstance(patch, dict) else patch
    
    if not isinstance(patch, dict):
        # If patch is not a dict, it replaces the original
        return patch
    
    # Start with a copy of the original
    result = dict(original)
    
    for key, value in patch.items():
        if value is None and remove_null_fields:
            # Null value means remove the field (RFC 7396)
            if key in result:
                del result[key]
        elif isinstance(value, dict) and key in result and isinstance(result[key], dict):
            # Recursively merge nested objects
            result[key] = apply_json_merge_patch(result[key], value, remove_null_fields)
        else:
            # Set or update the field
            result[key] = value
    
    return result


def extract_patch_fields(
    patch: Dict[str, Any],
    include_null: bool = True
) -> Dict[str, Any]:
    """
        Extract the fields from a patch that should be updated.
        
        This function separates the patch into fields to update and fields
        to remove (null values). It's useful for applying partial updates
        to objects where you need to know which fields were explicitly set.
        
        Args:
            patch: The patch dictionary.
            include_null: If True, include null values in the result.
                         If False, exclude null values (they indicate removal).
        
        Returns:
            A dictionary containing only the fields to update.
            If include_null is False, null values are excluded.
    """
    if not isinstance(patch, dict):
        return {}
    
    if include_null:
        return dict(patch)
    
    return {k: v for k, v in patch.items() if v is not None}


def get_removed_fields(patch: Dict[str, Any]) -> List[str]:
    """
        Get the list of fields that should be removed according to JSON Merge Patch.
        
        In JSON Merge Patch (RFC 7396), a field with a null value indicates
        that the field should be removed from the target object.
        
        Args:
            patch: The patch dictionary.
        
        Returns:
            A list of field names that have null values (should be removed).
    """
    if not isinstance(patch, dict):
        return []
    
    return [k for k, v in patch.items() if v is None]
