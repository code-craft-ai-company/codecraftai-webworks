"""
.. module:: ccai.webworks.endpoints.rest.collectionendpoint
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Collection-oriented endpoint class providing list operations
               with pagination, filtering, and sorting support.

.. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

import logging

from typing import Any, Callable, Dict, List, Optional, Tuple, Type

from ccai.webworks.endpoints.descriptor import EndpointDescriptor
from ccai.webworks.endpoints.rest.exceptions import ValidationError
from ccai.webworks.endpoints.rest.middleware import RESTMiddleware
from ccai.webworks.endpoints.rest.resourceendpoint import ResourceEndpoint
from ccai.webworks.endpoints.rest.models import (
    BulkItemError,
    BulkOperationResult,
    FieldError,
    PaginatedResponse,
    RESTError,
)


# Module-level logger. Bulk operations swallow per-item exceptions
# so a single failed item doesn't kill the batch — the operator
# wants the underlying traceback so they can investigate the cause
# (database error, validation gap, etc.) without re-running the
# bulk job.
logger = logging.getLogger(__name__)


class CollectionEndpoint(ResourceEndpoint):
    """
        Collection-oriented endpoint with pagination, filtering, and sorting.
        
        CollectionEndpoint extends ResourceEndpoint with list operations and
        support for pagination, filtering, and sorting. It provides a standard
        pattern for building collection endpoints that return paginated results.
        
        Subclasses should override the list() method to implement their
        specific query logic, using the provided pagination, filter, and
        sort parameters.
        
        Class Attributes:
            default_page_size: Default number of items per page when not
                               specified in the request. Default is 20.
            max_page_size: Maximum allowed page size. Requests for larger
                           page sizes will be clamped to this value. Default is 100.
            filter_fields: List of field names that can be used for filtering.
                           Only query parameters matching these names will be
                           parsed as filters.
            sort_fields: List of field names that can be used for sorting.
                         Only sort parameters matching these names will be
                         accepted.
            bulk_enabled: Whether bulk operations are enabled. Default is False.
            atomic_bulk: Whether bulk operations should be atomic (rollback
                         all on any failure). Default is False.
    """
    
    # Pagination configuration
    default_page_size: int = 20
    max_page_size: int = 100
    
    # Filtering and sorting configuration
    filter_fields: List[str] = []
    sort_fields: List[str] = []
    
    # Bulk operations configuration
    bulk_enabled: bool = False
    atomic_bulk: bool = False
    
    def list(
        self,
        page: int = 1,
        page_size: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        sort: Optional[List[str]] = None
    ) -> PaginatedResponse:
        """
            List resources with pagination, filtering, and sorting.
            
            Override this method in subclasses to implement resource listing.
            The method receives pagination parameters, filter criteria, and
            sort specifications parsed from the request query parameters.
            
            Args:
                page: Page number (1-indexed). Defaults to 1.
                page_size: Number of items per page. If not specified, uses
                           default_page_size. Will be clamped to max_page_size.
                filters: Dictionary of filter criteria parsed from query
                         parameters. Only includes fields in filter_fields.
                sort: List of sort specifications. Each item is a field name,
                      optionally prefixed with '-' for descending order.
            
            Returns:
                PaginatedResponse containing the items for the current page
                and pagination metadata.
            
            Raises:
                NotImplementedError: If not overridden in subclass.
        """
        raise NotImplementedError("Subclass must implement list()")
    
    def bulk_create(self, payloads: List[Any]) -> Any:
        """
            Create multiple resources in a single request.
            
            Override this method in subclasses to implement bulk creation.
            The method receives a list of deserialized request bodies.
            
            Args:
                payloads: List of deserialized request bodies, each matching
                          the request_schema.
            
            Returns:
                BulkOperationResult with per-item results indicating success
                or failure for each item.
            
            Raises:
                NotImplementedError: If not overridden in subclass.
        """
        raise NotImplementedError("Subclass must implement bulk_create()")
    
    def bulk_update(self, updates: List[Dict[str, Any]]) -> Any:
        """
            Update multiple resources in a single request.
            
            Override this method in subclasses to implement bulk updates.
            The method receives a list of update objects, each containing
            an 'id' field and the fields to update.
            
            Args:
                updates: List of update objects. Each object should have an
                         'id' field identifying the resource and additional
                         fields to update.
            
            Returns:
                BulkOperationResult with per-item results indicating success
                or failure for each item.
            
            Raises:
                NotImplementedError: If not overridden in subclass.
        """
        raise NotImplementedError("Subclass must implement bulk_update()")
    
    def bulk_delete(self, ids: List[Any]) -> Any:
        """
            Delete multiple resources in a single request.
            
            Override this method in subclasses to implement bulk deletion.
            The method receives a list of resource identifiers to delete.
            
            Args:
                ids: List of resource identifiers to delete.
            
            Returns:
                BulkOperationResult with per-item results indicating success
                or failure for each item.
            
            Raises:
                NotImplementedError: If not overridden in subclass.
        """
        raise NotImplementedError("Subclass must implement bulk_delete()")
    
    @classmethod
    def get_effective_page_size(cls, requested_page_size: Optional[int]) -> int:
        """
            Get the effective page size, applying defaults and limits.
            
            This method applies the default_page_size when no page size is
            requested, and clamps the requested page size to max_page_size.
            
            Args:
                requested_page_size: The page size requested by the client,
                                     or None to use the default.
            
            Returns:
                The effective page size to use for the query.
        """
        if requested_page_size is None:
            return cls.default_page_size
        
        # Ensure page_size is at least 1
        if requested_page_size < 1:
            return 1
        
        # Clamp to max_page_size
        if requested_page_size > cls.max_page_size:
            return cls.max_page_size
        
        return requested_page_size
    
    @classmethod
    def parse_pagination_params(
        cls,
        query_params: Dict[str, Any]
    ) -> Tuple[int, int]:
        """
            Parse pagination parameters from query parameters.
            
            This method extracts and validates the 'page' and 'page_size'
            query parameters, applying defaults and limits as needed.
            
            Args:
                query_params: Dictionary of query parameters from the request.
            
            Returns:
                Tuple of (page, page_size) with validated values.
        """
        # Parse page parameter
        page = query_params.get('page', 1)
        if isinstance(page, str):
            try:
                page = int(page)
            except ValueError:
                page = 1
        if not isinstance(page, int) or page < 1:
            page = 1
        
        # Parse page_size parameter
        page_size = query_params.get('page_size')
        if page_size is not None:
            if isinstance(page_size, str):
                try:
                    page_size = int(page_size)
                except ValueError:
                    page_size = None
        
        effective_page_size = cls.get_effective_page_size(page_size)
        
        return (page, effective_page_size)
    
    @classmethod
    def parse_filter_params(
        cls,
        query_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
            Parse filter parameters from query parameters.
            
            This method extracts filter criteria from query parameters,
            only including fields that are in the filter_fields list.
            
            Args:
                query_params: Dictionary of query parameters from the request.
            
            Returns:
                Dictionary of filter criteria with field names as keys.
        """
        filters: Dict[str, Any] = {}
        
        for field_name in cls.filter_fields:
            if field_name in query_params:
                filters[field_name] = query_params[field_name]
        
        return filters
    
    @classmethod
    def parse_sort_params(
        cls,
        query_params: Dict[str, Any]
    ) -> List[str]:
        """
            Parse sort parameters from query parameters.
            
            This method extracts sort specifications from the 'sort' query
            parameter. The sort parameter can be a comma-separated list of
            field names, optionally prefixed with '-' for descending order.
            
            Only fields in sort_fields are accepted. Invalid field names
            are silently ignored.
            
            Args:
                query_params: Dictionary of query parameters from the request.
            
            Returns:
                List of validated sort specifications.
        """
        sort_param = query_params.get('sort')
        
        if sort_param is None:
            return []
        
        # Handle string or list input
        if isinstance(sort_param, str):
            sort_items = [s.strip() for s in sort_param.split(',')]
        elif isinstance(sort_param, list):
            sort_items = sort_param
        else:
            return []
        
        validated_sorts: List[str] = []
        
        for sort_item in sort_items:
            if not sort_item:
                continue
            
            # Check for descending prefix
            if sort_item.startswith('-'):
                field_name = sort_item[1:]
                prefix = '-'
            else:
                field_name = sort_item
                prefix = ''
            
            # Only include if field is in sort_fields
            if field_name in cls.sort_fields:
                validated_sorts.append(f"{prefix}{field_name}")
        
        return validated_sorts
    
    # =========================================================================
    # Bulk Operation Helpers
    # =========================================================================
    
    @classmethod
    def execute_bulk_operation(
        cls,
        items: List[Any],
        operation: Callable[[int, Any], Any],
        validate: Optional[Callable[[int, Any], Optional[RESTError]]] = None,
        atomic: bool = False
    ) -> BulkOperationResult:
        """
            Execute a bulk operation with validation-first processing.
            
            This method provides a standard pattern for executing bulk operations
            with the following features:
            
            - Validation-first: All items are validated before any are processed
            - Atomic mode: If atomic=True, all changes are rolled back on any failure
            - Per-item error tracking: Each failed item includes its index and error
            
            Args:
                items: List of items to process.
                operation: Callable that takes (index, item) and returns the result.
                           Should raise an exception on failure.
                validate: Optional callable that takes (index, item) and returns
                          a RESTError if validation fails, or None if valid.
                atomic: If True, raise an exception on any failure to trigger rollback.
            
            Returns:
                BulkOperationResult with succeeded and failed items.
            
            Raises:
                BulkOperationError: If atomic=True and any item fails.
        """
        succeeded: List[Any] = []
        failed: List[BulkItemError] = []
        
        # Phase 1: Validation-first - validate all items before processing any
        if validate is not None:
            validation_errors: List[BulkItemError] = []
            for index, item in enumerate(items):
                error = validate(index, item)
                if error is not None:
                    validation_errors.append(BulkItemError(
                        index=index,
                        item=item,
                        error=error
                    ))
            
            # If any validation errors, return immediately without processing
            if validation_errors:
                # In validation-first mode, we don't process any items if validation fails
                # All items that passed validation are not in succeeded (they weren't processed)
                # All items that failed validation are in failed
                return BulkOperationResult(
                    succeeded=[],
                    failed=validation_errors
                )
        
        # Phase 2: Process all items
        processed_results: List[Tuple[int, Any, Optional[Any], Optional[RESTError]]] = []
        
        for index, item in enumerate(items):
            try:
                result = operation(index, item)
                processed_results.append((index, item, result, None))
                succeeded.append(result)
            except Exception as e:
                logger.exception(
                    "CollectionEndpoint bulk: item %d (%s) failed",
                    index,
                    type(e).__name__,
                )
                error = RESTError(
                    error="operation_failed",
                    message=str(e),
                    details={"exception_type": type(e).__name__}
                )
                processed_results.append((index, item, None, error))
                failed.append(BulkItemError(
                    index=index,
                    item=item,
                    error=error
                ))
        
        # Phase 3: Handle atomic mode - if any failures, we need to indicate rollback
        if atomic and failed:
            # In atomic mode, if any item failed, we should rollback all changes
            # The caller is responsible for implementing the actual rollback
            # We raise an exception to signal that rollback is needed
            raise BulkOperationError(
                message=f"Bulk operation failed: {len(failed)} items failed",
                result=BulkOperationResult(succeeded=succeeded, failed=failed)
            )
        
        return BulkOperationResult(succeeded=succeeded, failed=failed)
    
    @classmethod
    def get_list_query_params(cls) -> Dict[str, Type]:
        """
            Get the query parameters the list route reads: the pagination
            parameters, ``sort`` when sorting is configured, and one
            parameter per filter field.

            Returns:
                Mapping of query parameter name to Python type.
        """
        query_params: Dict[str, Type] = {
            "page": int,
            "page_size": int,
        }

        if len(cls.sort_fields) > 0:
            query_params["sort"] = str

        for field_name in cls.filter_fields:
            query_params[field_name] = str

        return query_params

    @classmethod
    def build_routes(
        cls,
        instance: "ResourceEndpoint",
        middleware: RESTMiddleware
    ) -> List[EndpointDescriptor]:
        """
            Build the descriptors for this collection's routes: the list
            route, the bulk routes when ``bulk_enabled`` is set, and the
            CRUD routes of :class:`ResourceEndpoint`.

            - GET /{resource_name} calls :meth:`list` with the page, page
              size, filters and sort order parsed from the query string.
            - POST, PUT and DELETE /{resource_name}/bulk call
              :meth:`bulk_create`, :meth:`bulk_update` and
              :meth:`bulk_delete` with the JSON array in the request body.

            The list route is only built when GET is an allowed method.

            Args:
                instance: The collection endpoint instance the routes serve.
                middleware: The REST middleware to run the operations inside.

            Returns:
                List of EndpointDescriptor objects, one per route.
        """
        descriptors: List[EndpointDescriptor] = []
        allowed = [method.upper() for method in cls.get_effective_allowed_methods()]
        resource_title = cls.resource_name.replace("_", " ").replace("-", " ").title()

        # List route
        if "GET" in allowed:
            def list_operation(request: Any) -> Any:
                query_params = cls.read_query_params(request)
                page, page_size = cls.parse_pagination_params(query_params)
                filters = cls.parse_filter_params(query_params)
                sort = cls.parse_sort_params(query_params)
                return instance.list(page=page, page_size=page_size, filters=filters, sort=sort)

            descriptors.append(cls.build_route(
                instance=instance,
                middleware=middleware,
                operation=list_operation,
                name=f"list_{cls.resource_name}",
                path=f"/{cls.resource_name}",
                methods=["GET"],
                summary=f"List {resource_title}",
                extras=cls.build_route_extras(
                    with_request_schema=False,
                    with_response_schema=False,
                    query_params=cls.get_list_query_params()
                )
            ))

        # Bulk routes. They are built before the item route so that a
        # router which tries routes in registration order reaches the
        # literal "bulk" segment before the identifier parameter.
        for method, path_suffix, handler_name in cls.get_bulk_routes():
            descriptors.append(cls.build_route(
                instance=instance,
                middleware=middleware,
                operation=cls.build_bulk_operation(instance, middleware, handler_name),
                name=f"{handler_name}_{cls.resource_name}",
                path=f"/{cls.resource_name}{path_suffix}",
                methods=[method],
                summary=f"{handler_name.replace('_', ' ').capitalize()} {resource_title}",
                extras=cls.build_route_extras(
                    with_request_schema=False,
                    with_response_schema=False
                )
            ))

        descriptors.extend(super().build_routes(instance, middleware))

        return descriptors

    @staticmethod
    def read_query_params(request: Any) -> Dict[str, Any]:
        """
            Read the query parameters of a request into a plain dictionary,
            as the ``parse_*_params`` helpers expect them.

            Args:
                request: The HTTP request object.

            Returns:
                Dictionary of query parameter name to value. A parameter
                given more than once keeps its first value.
        """
        rtnval: Dict[str, Any] = {}

        query_params = getattr(request, "query_params", None)
        if query_params is None:
            return rtnval

        for key in query_params.keys():
            if key not in rtnval:
                rtnval[key] = query_params.get(key)

        return rtnval

    @classmethod
    def build_bulk_operation(
        cls,
        instance: "ResourceEndpoint",
        middleware: RESTMiddleware,
        handler_name: str
    ) -> Callable[[Any], Any]:
        """
            Build the operation behind one bulk route.

            The request body must be a JSON array. For ``bulk_create`` each
            item is validated into ``request_schema`` first, and any invalid
            item rejects the whole request with its index in the field path
            (``2.email``); ``bulk_update`` receives the items as sent and
            ``bulk_delete`` the list of identifiers. The result is returned
            with status 200: a bulk request reports per-item outcomes rather
            than creating one resource.

            Args:
                instance: The collection endpoint instance.
                middleware: The REST middleware, used to parse the body and
                            validate items.
                handler_name: ``bulk_create``, ``bulk_update`` or
                              ``bulk_delete``.

            Returns:
                Callable taking the request and returning ``(result, 200)``.
        """
        def bulk_operation(request: Any) -> Any:
            items = middleware.read_body(request)
            if not isinstance(items, list):
                raise ValidationError(
                    message="Expected a JSON array",
                    field_errors=[
                        FieldError(
                            field="$",
                            code="type_error",
                            message=f"Expected list, got {type(items).__name__}"
                        )
                    ]
                )

            if handler_name == "bulk_create" and cls.request_schema is not None:
                items = cls.validate_bulk_items(middleware, items)

            result = getattr(instance, handler_name)(items)

            return (result, 200)

        return bulk_operation

    @classmethod
    def validate_bulk_items(cls, middleware: RESTMiddleware, items: List[Any]) -> List[Any]:
        """
            Validate every item of a bulk create request into
            ``request_schema`` before any of them is processed.

            Args:
                middleware: The REST middleware whose validator is used.
                items: The parsed items of the request body.

            Returns:
                The validated items, in request order.

            Raises:
                ValidationError: If any item is invalid. The field path of
                                 each error starts with the item's index.
        """
        validated_items: List[Any] = []
        field_errors: List[FieldError] = []

        for index, item in enumerate(items):
            try:
                validated_items.append(middleware.validator.validate(item, cls.request_schema))
            except ValidationError as exc:
                for field_error in exc.field_errors:
                    if field_error.field == "$":
                        item_field = str(index)
                    else:
                        item_field = f"{index}.{field_error.field}"
                    field_errors.append(FieldError(
                        field=item_field,
                        code=field_error.code,
                        message=field_error.message
                    ))

        if len(field_errors) > 0:
            raise ValidationError(
                message="Request validation failed",
                field_errors=field_errors
            )

        return validated_items

    @classmethod
    def get_bulk_routes(cls) -> List[Tuple[str, str, str]]:
        """
            Get the bulk operation routes for this endpoint.
            
            Returns a list of tuples containing (method, path_suffix, handler_name)
            for each bulk operation route.
            
            Returns:
                List of route tuples for bulk operations.
        """
        if not cls.bulk_enabled:
            return []
        
        routes = []
        
        # POST /resource/bulk - bulk create
        routes.append(("POST", "/bulk", "bulk_create"))
        
        # PUT /resource/bulk - bulk update
        routes.append(("PUT", "/bulk", "bulk_update"))
        
        # DELETE /resource/bulk - bulk delete
        routes.append(("DELETE", "/bulk", "bulk_delete"))
        
        return routes


class BulkOperationError(Exception):
    """
        Exception raised when a bulk operation fails in atomic mode.
        
        This exception is raised when atomic_bulk=True and any item in
        the bulk operation fails. It contains the partial result with
        both succeeded and failed items, allowing the caller to implement
        rollback logic.
        
        Attributes:
            message: Human-readable description of the failure.
            result: BulkOperationResult containing succeeded and failed items.
    """
    
    def __init__(self, message: str, result: BulkOperationResult):
        """
            Initialize a BulkOperationError.
            
            Args:
                message: Human-readable description of the failure.
                result: BulkOperationResult containing succeeded and failed items.
        """
        self.message = message
        self.result = result
        super().__init__(message)


# Export the classes
__all__ = [
    "BulkOperationError",
    "CollectionEndpoint",
]
