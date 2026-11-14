"""
.. module:: ccai.tests.singlehost.webworks.rest.test_collectionendpoint
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Tests for the CollectionEndpoint class.

.. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

from typing import Any, Dict, List, Optional

from ccai.webworks.endpoints.rest.collectionendpoint import CollectionEndpoint
from ccai.webworks.endpoints.rest.models import PaginatedResponse, PaginationInfo


# =============================================================================
# Test Fixtures
# =============================================================================

class TestCollectionEndpoint(CollectionEndpoint):
    """
        Test implementation of CollectionEndpoint for testing purposes.
    """
    
    resource_name = "items"
    filter_fields = ["status", "category", "name"]
    sort_fields = ["name", "created_at", "updated_at"]
    default_page_size = 10
    max_page_size = 50
    
    def __init__(self):
        self._items = []
    
    def list(
        self,
        page: int = 1,
        page_size: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        sort: Optional[List[str]] = None
    ) -> PaginatedResponse:
        """Test implementation of list method."""
        effective_page_size = self.get_effective_page_size(page_size)
        
        # Apply filters
        items = list(self._items)
        if filters:
            for field, value in filters.items():
                items = [i for i in items if i.get(field) == value]

        # Apply sorting
        if sort:
            for sort_spec in reversed(sort):
                if sort_spec.startswith('-'):
                    field = sort_spec[1:]
                    reverse = True
                else:
                    field = sort_spec
                    reverse = False
                items = sorted(items, key=lambda x: x.get(field, ''), reverse=reverse)
        
        # Calculate pagination
        total = len(items)
        start_idx = (page - 1) * effective_page_size
        end_idx = start_idx + effective_page_size
        page_items = items[start_idx:end_idx]
        
        pagination = PaginationInfo.create(
            total=total,
            page=page,
            page_size=effective_page_size,
            base_url="/items"
        )
        
        return PaginatedResponse(items=page_items, pagination=pagination)


# =============================================================================
# Task 10.1: CollectionEndpoint class attributes
# =============================================================================

def test_collection_endpoint_extends_resource_endpoint():
    """
        Verify CollectionEndpoint extends ResourceEndpoint.
        
        **Validates: Requirements 2.1**
    """
    from ccai.webworks.endpoints.rest.resourceendpoint import ResourceEndpoint
    
    if not issubclass(CollectionEndpoint, ResourceEndpoint):
        raise AssertionError("CollectionEndpoint should extend ResourceEndpoint")


def test_collection_endpoint_has_default_page_size_attribute():
    """
        Verify CollectionEndpoint has default_page_size attribute with default value 20.
        
        **Validates: Requirements 2.3**
    """
    if not hasattr(CollectionEndpoint, 'default_page_size'):
        raise AssertionError("CollectionEndpoint should have default_page_size attribute")
    
    if CollectionEndpoint.default_page_size != 20:
        raise AssertionError(
            f"default_page_size should default to 20, got {CollectionEndpoint.default_page_size}"
        )


def test_collection_endpoint_has_max_page_size_attribute():
    """
        Verify CollectionEndpoint has max_page_size attribute with default value 100.
        
        **Validates: Requirements 2.3**
    """
    if not hasattr(CollectionEndpoint, 'max_page_size'):
        raise AssertionError("CollectionEndpoint should have max_page_size attribute")
    
    if CollectionEndpoint.max_page_size != 100:
        raise AssertionError(
            f"max_page_size should default to 100, got {CollectionEndpoint.max_page_size}"
        )


def test_collection_endpoint_has_filter_fields_attribute():
    """
        Verify CollectionEndpoint has filter_fields attribute with empty list default.
        
        **Validates: Requirements 2.4**
    """
    if not hasattr(CollectionEndpoint, 'filter_fields'):
        raise AssertionError("CollectionEndpoint should have filter_fields attribute")
    
    if CollectionEndpoint.filter_fields != []:
        raise AssertionError(
            f"filter_fields should default to empty list, got {CollectionEndpoint.filter_fields}"
        )


def test_collection_endpoint_has_sort_fields_attribute():
    """
        Verify CollectionEndpoint has sort_fields attribute with empty list default.
        
        **Validates: Requirements 2.5**
    """
    if not hasattr(CollectionEndpoint, 'sort_fields'):
        raise AssertionError("CollectionEndpoint should have sort_fields attribute")
    
    if CollectionEndpoint.sort_fields != []:
        raise AssertionError(
            f"sort_fields should default to empty list, got {CollectionEndpoint.sort_fields}"
        )


def test_collection_endpoint_has_bulk_enabled_attribute():
    """Verify CollectionEndpoint has bulk_enabled attribute with False default."""
    if not hasattr(CollectionEndpoint, 'bulk_enabled'):
        raise AssertionError("CollectionEndpoint should have bulk_enabled attribute")
    
    if CollectionEndpoint.bulk_enabled != False:
        raise AssertionError(
            f"bulk_enabled should default to False, got {CollectionEndpoint.bulk_enabled}"
        )


def test_collection_endpoint_has_atomic_bulk_attribute():
    """Verify CollectionEndpoint has atomic_bulk attribute with False default."""
    if not hasattr(CollectionEndpoint, 'atomic_bulk'):
        raise AssertionError("CollectionEndpoint should have atomic_bulk attribute")
    
    if CollectionEndpoint.atomic_bulk != False:
        raise AssertionError(
            f"atomic_bulk should default to False, got {CollectionEndpoint.atomic_bulk}"
        )


# =============================================================================
# Task 10.2: list() method with pagination support
# =============================================================================

def test_list_method_raises_not_implemented_by_default():
    """
        Verify list() raises NotImplementedError when not overridden.
        
        **Validates: Requirements 2.1**
    """
    endpoint = CollectionEndpoint()
    
    raised = False
    try:
        endpoint.list()
    except NotImplementedError as e:
        raised = True
        if "Subclass must implement list()" not in str(e):
            raise AssertionError(f"NotImplementedError should have appropriate message, got: {e}")
    
    if not raised:
        raise AssertionError("list() should raise NotImplementedError")


def test_get_effective_page_size_uses_default_when_none():
    """
        Verify get_effective_page_size returns default_page_size when None is passed.
        
        **Validates: Requirements 2.3**
    """
    result = TestCollectionEndpoint.get_effective_page_size(None)
    if result != 10:  # TestCollectionEndpoint.default_page_size
        raise AssertionError(f"Should return default_page_size when None is passed, got {result}")


def test_get_effective_page_size_clamps_to_max():
    """
        Verify get_effective_page_size clamps to max_page_size.
        
        **Validates: Requirements 2.3**
    """
    result = TestCollectionEndpoint.get_effective_page_size(1000)
    if result != 50:  # TestCollectionEndpoint.max_page_size
        raise AssertionError(f"Should clamp to max_page_size, got {result}")


def test_get_effective_page_size_returns_requested_when_valid():
    """
        Verify get_effective_page_size returns requested size when within limits.
        
        **Validates: Requirements 2.3**
    """
    result = TestCollectionEndpoint.get_effective_page_size(25)
    if result != 25:
        raise AssertionError(f"Should return requested page_size when within limits, got {result}")


def test_get_effective_page_size_minimum_is_one():
    """
        Verify get_effective_page_size returns at least 1.
        
        **Validates: Requirements 2.3**
    """
    result = TestCollectionEndpoint.get_effective_page_size(0)
    if result != 1:
        raise AssertionError(f"Should return at least 1, got {result}")
    
    result = TestCollectionEndpoint.get_effective_page_size(-5)
    if result != 1:
        raise AssertionError(f"Should return at least 1 for negative values, got {result}")


def test_parse_pagination_params_extracts_page_and_page_size():
    """
        Verify parse_pagination_params extracts page and page_size from query params.
        
        **Validates: Requirements 2.2**
    """
    query_params = {'page': 3, 'page_size': 25}
    page, page_size = TestCollectionEndpoint.parse_pagination_params(query_params)
    
    if page != 3:
        raise AssertionError(f"Should extract page parameter, got {page}")
    if page_size != 25:
        raise AssertionError(f"Should extract page_size parameter, got {page_size}")


def test_parse_pagination_params_handles_string_values():
    """
        Verify parse_pagination_params handles string values from query params.
        
        **Validates: Requirements 2.2**
    """
    query_params = {'page': '2', 'page_size': '15'}
    page, page_size = TestCollectionEndpoint.parse_pagination_params(query_params)
    
    if page != 2:
        raise AssertionError(f"Should parse string page parameter, got {page}")
    if page_size != 15:
        raise AssertionError(f"Should parse string page_size parameter, got {page_size}")


def test_parse_pagination_params_uses_defaults_when_missing():
    """
        Verify parse_pagination_params uses defaults when params are missing.
        
        **Validates: Requirements 2.2, 2.3**
    """
    query_params = {}
    page, page_size = TestCollectionEndpoint.parse_pagination_params(query_params)
    
    if page != 1:
        raise AssertionError(f"Should default page to 1, got {page}")
    if page_size != 10:  # TestCollectionEndpoint.default_page_size
        raise AssertionError(f"Should use default_page_size, got {page_size}")


def test_parse_pagination_params_handles_invalid_page():
    """
        Verify parse_pagination_params handles invalid page values.
        
        **Validates: Requirements 2.2**
    """
    query_params = {'page': 'invalid', 'page_size': 10}
    page, page_size = TestCollectionEndpoint.parse_pagination_params(query_params)
    
    if page != 1:
        raise AssertionError(f"Should default to 1 for invalid page, got {page}")


def test_parse_pagination_params_handles_negative_page():
    """
        Verify parse_pagination_params handles negative page values.
        
        **Validates: Requirements 2.2**
    """
    query_params = {'page': -5, 'page_size': 10}
    page, page_size = TestCollectionEndpoint.parse_pagination_params(query_params)
    
    if page != 1:
        raise AssertionError(f"Should default to 1 for negative page, got {page}")


# =============================================================================
# Task 10.3: Filtering support
# =============================================================================

def test_parse_filter_params_extracts_allowed_filters():
    """
        Verify parse_filter_params extracts only allowed filter fields.
        
        **Validates: Requirements 2.4**
    """
    query_params = {
        'status': 'active',
        'category': 'electronics',
        'name': 'test',
        'unknown_field': 'ignored'
    }
    filters = TestCollectionEndpoint.parse_filter_params(query_params)
    
    expected = {'status': 'active', 'category': 'electronics', 'name': 'test'}
    if filters != expected:
        raise AssertionError(f"Should extract only allowed filter fields, got {filters}")


def test_parse_filter_params_ignores_unknown_fields():
    """
        Verify parse_filter_params ignores fields not in filter_fields.
        
        **Validates: Requirements 2.4**
    """
    query_params = {
        'unknown1': 'value1',
        'unknown2': 'value2'
    }
    filters = TestCollectionEndpoint.parse_filter_params(query_params)
    
    if filters != {}:
        raise AssertionError(f"Should return empty dict when no allowed filters present, got {filters}")


def test_parse_filter_params_returns_empty_dict_when_no_filters():
    """
        Verify parse_filter_params returns empty dict when no query params.
        
        **Validates: Requirements 2.4**
    """
    query_params = {}
    filters = TestCollectionEndpoint.parse_filter_params(query_params)
    
    if filters != {}:
        raise AssertionError(f"Should return empty dict when no query params, got {filters}")


def test_parse_filter_params_preserves_filter_values():
    """
        Verify parse_filter_params preserves various filter value types.
        
        **Validates: Requirements 2.4**
    """
    query_params = {
        'status': 'active',
        'category': 123,
        'name': ['a', 'b']
    }
    filters = TestCollectionEndpoint.parse_filter_params(query_params)
    
    if filters['status'] != 'active':
        raise AssertionError(f"Should preserve string values, got {filters['status']}")
    if filters['category'] != 123:
        raise AssertionError(f"Should preserve integer values, got {filters['category']}")
    if filters['name'] != ['a', 'b']:
        raise AssertionError(f"Should preserve list values, got {filters['name']}")


# =============================================================================
# Task 10.4: Sorting support
# =============================================================================

def test_parse_sort_params_extracts_allowed_sort_fields():
    """
        Verify parse_sort_params extracts only allowed sort fields.
        
        **Validates: Requirements 2.5**
    """
    query_params = {'sort': 'name,created_at'}
    sort = TestCollectionEndpoint.parse_sort_params(query_params)
    
    if sort != ['name', 'created_at']:
        raise AssertionError(f"Should extract allowed sort fields, got {sort}")


def test_parse_sort_params_handles_descending_prefix():
    """
        Verify parse_sort_params handles descending sort with '-' prefix.
        
        **Validates: Requirements 2.5**
    """
    query_params = {'sort': 'name,-created_at'}
    sort = TestCollectionEndpoint.parse_sort_params(query_params)
    
    if sort != ['name', '-created_at']:
        raise AssertionError(f"Should preserve descending prefix, got {sort}")


def test_parse_sort_params_ignores_unknown_fields():
    """
        Verify parse_sort_params ignores fields not in sort_fields.
        
        **Validates: Requirements 2.5**
    """
    query_params = {'sort': 'name,unknown_field,created_at'}
    sort = TestCollectionEndpoint.parse_sort_params(query_params)
    
    if sort != ['name', 'created_at']:
        raise AssertionError(f"Should ignore unknown sort fields, got {sort}")


def test_parse_sort_params_returns_empty_list_when_no_sort():
    """
        Verify parse_sort_params returns empty list when no sort param.
        
        **Validates: Requirements 2.5**
    """
    query_params = {}
    sort = TestCollectionEndpoint.parse_sort_params(query_params)
    
    if sort != []:
        raise AssertionError(f"Should return empty list when no sort param, got {sort}")


def test_parse_sort_params_handles_list_input():
    """
        Verify parse_sort_params handles list input for sort param.
        
        **Validates: Requirements 2.5**
    """
    query_params = {'sort': ['name', '-created_at']}
    sort = TestCollectionEndpoint.parse_sort_params(query_params)
    
    if sort != ['name', '-created_at']:
        raise AssertionError(f"Should handle list input, got {sort}")


def test_parse_sort_params_handles_whitespace():
    """
        Verify parse_sort_params handles whitespace in sort param.
        
        **Validates: Requirements 2.5**
    """
    query_params = {'sort': ' name , -created_at '}
    sort = TestCollectionEndpoint.parse_sort_params(query_params)
    
    if sort != ['name', '-created_at']:
        raise AssertionError(f"Should trim whitespace, got {sort}")


def test_parse_sort_params_handles_empty_string():
    """
        Verify parse_sort_params handles empty string sort param.
        
        **Validates: Requirements 2.5**
    """
    query_params = {'sort': ''}
    sort = TestCollectionEndpoint.parse_sort_params(query_params)
    
    if sort != []:
        raise AssertionError(f"Should return empty list for empty string, got {sort}")


# =============================================================================
# Integration tests
# =============================================================================

def test_list_with_pagination():
    """
        Verify list() method works with pagination.
        
        **Validates: Requirements 2.1, 2.2, 2.3**
    """
    endpoint = TestCollectionEndpoint()
    endpoint._items = [{'id': i, 'name': f'item{i}'} for i in range(25)]
    
    result = endpoint.list(page=2, page_size=10)
    
    if not isinstance(result, PaginatedResponse):
        raise AssertionError("Should return PaginatedResponse")
    if len(result.items) != 10:
        raise AssertionError(f"Should return correct number of items, got {len(result.items)}")
    if result.pagination.page != 2:
        raise AssertionError(f"Should have correct page number, got {result.pagination.page}")
    if result.pagination.total != 25:
        raise AssertionError(f"Should have correct total count, got {result.pagination.total}")


def test_list_with_filters():
    """
        Verify list() method works with filters.
        
        **Validates: Requirements 2.4**
    """
    endpoint = TestCollectionEndpoint()
    endpoint._items = [
        {'id': 1, 'name': 'item1', 'status': 'active'},
        {'id': 2, 'name': 'item2', 'status': 'inactive'},
        {'id': 3, 'name': 'item3', 'status': 'active'},
    ]
    
    result = endpoint.list(filters={'status': 'active'})
    
    if len(result.items) != 2:
        raise AssertionError(f"Should filter items correctly, got {len(result.items)}")
    if result.pagination.total != 2:
        raise AssertionError(f"Should have correct filtered total, got {result.pagination.total}")


def test_list_with_sorting():
    """
        Verify list() method works with sorting.
        
        **Validates: Requirements 2.5**
    """
    endpoint = TestCollectionEndpoint()
    endpoint._items = [
        {'id': 1, 'name': 'charlie'},
        {'id': 2, 'name': 'alice'},
        {'id': 3, 'name': 'bob'},
    ]
    
    result = endpoint.list(sort=['name'])
    
    if result.items[0]['name'] != 'alice':
        raise AssertionError(f"Should sort items correctly, got {result.items[0]['name']}")
    if result.items[1]['name'] != 'bob':
        raise AssertionError(f"Should sort items correctly, got {result.items[1]['name']}")
    if result.items[2]['name'] != 'charlie':
        raise AssertionError(f"Should sort items correctly, got {result.items[2]['name']}")


def test_list_with_descending_sort():
    """
        Verify list() method works with descending sort.
        
        **Validates: Requirements 2.5**
    """
    endpoint = TestCollectionEndpoint()
    endpoint._items = [
        {'id': 1, 'name': 'alice'},
        {'id': 2, 'name': 'bob'},
        {'id': 3, 'name': 'charlie'},
    ]
    
    result = endpoint.list(sort=['-name'])
    
    if result.items[0]['name'] != 'charlie':
        raise AssertionError(f"Should sort items in descending order, got {result.items[0]['name']}")
    if result.items[2]['name'] != 'alice':
        raise AssertionError(f"Should sort items in descending order, got {result.items[2]['name']}")


# =============================================================================
# Bulk operation method stubs
# =============================================================================

def test_bulk_create_raises_not_implemented():
    """Verify bulk_create() raises NotImplementedError when not overridden."""
    endpoint = CollectionEndpoint()
    
    raised = False
    try:
        endpoint.bulk_create([])
    except NotImplementedError as e:
        raised = True
        if "Subclass must implement bulk_create()" not in str(e):
            raise AssertionError(f"NotImplementedError should have appropriate message, got: {e}")
    
    if not raised:
        raise AssertionError("bulk_create() should raise NotImplementedError")


def test_bulk_update_raises_not_implemented():
    """Verify bulk_update() raises NotImplementedError when not overridden."""
    endpoint = CollectionEndpoint()
    
    raised = False
    try:
        endpoint.bulk_update([])
    except NotImplementedError as e:
        raised = True
        if "Subclass must implement bulk_update()" not in str(e):
            raise AssertionError(f"NotImplementedError should have appropriate message, got: {e}")
    
    if not raised:
        raise AssertionError("bulk_update() should raise NotImplementedError")


def test_bulk_delete_raises_not_implemented():
    """Verify bulk_delete() raises NotImplementedError when not overridden."""
    endpoint = CollectionEndpoint()
    
    raised = False
    try:
        endpoint.bulk_delete([])
    except NotImplementedError as e:
        raised = True
        if "Subclass must implement bulk_delete()" not in str(e):
            raise AssertionError(f"NotImplementedError should have appropriate message, got: {e}")
    
    if not raised:
        raise AssertionError("bulk_delete() should raise NotImplementedError")


# =============================================================================
# Task 12: Bulk Operations
# =============================================================================

import random
import string

from ccai.webworks.endpoints.rest.models import (
    BulkItemError,
    BulkOperationResult,
    RESTError,
)
from ccai.webworks.endpoints.rest.collectionendpoint import BulkOperationError


# =============================================================================
# Random Data Generators for Property Tests
# =============================================================================

def generate_random_string(min_length: int = 1, max_length: int = 20) -> str:
    """Generate a random string of alphanumeric characters."""
    length = random.randint(min_length, max_length)
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


def generate_random_item() -> Dict[str, Any]:
    """Generate a random item for bulk operations."""
    return {
        'id': random.randint(1, 10000),
        'name': generate_random_string(3, 15),
        'status': random.choice(['active', 'inactive', 'pending']),
        'value': random.randint(0, 1000),
    }


def generate_random_items(count: int) -> List[Dict[str, Any]]:
    """Generate a list of random items."""
    return [generate_random_item() for _ in range(count)]


def generate_random_ids(count: int) -> List[int]:
    """Generate a list of random IDs."""
    return [random.randint(1, 10000) for _ in range(count)]


# =============================================================================
# Unit Tests: BulkItemError
# =============================================================================

def test_bulk_item_error_has_index():
    """Verify BulkItemError has index attribute."""
    error = RESTError(error="test_error", message="Test message")
    item_error = BulkItemError(index=5, item={'id': 1}, error=error)
    
    if item_error.index != 5:
        raise AssertionError(f"Expected index 5, got {item_error.index}")


def test_bulk_item_error_has_item():
    """Verify BulkItemError has item attribute."""
    error = RESTError(error="test_error", message="Test message")
    item = {'id': 1, 'name': 'test'}
    item_error = BulkItemError(index=0, item=item, error=error)
    
    if item_error.item != item:
        raise AssertionError(f"Expected item {item}, got {item_error.item}")


def test_bulk_item_error_has_error():
    """Verify BulkItemError has error attribute."""
    error = RESTError(error="test_error", message="Test message")
    item_error = BulkItemError(index=0, item={'id': 1}, error=error)
    
    if item_error.error != error:
        raise AssertionError("BulkItemError should have error attribute")


# =============================================================================
# Unit Tests: BulkOperationResult
# =============================================================================

def test_bulk_operation_result_has_succeeded():
    """Verify BulkOperationResult has succeeded attribute."""
    result = BulkOperationResult(succeeded=[1, 2, 3], failed=[])
    
    if result.succeeded != [1, 2, 3]:
        raise AssertionError(f"Expected succeeded [1, 2, 3], got {result.succeeded}")


def test_bulk_operation_result_has_failed():
    """Verify BulkOperationResult has failed attribute."""
    error = RESTError(error="test_error", message="Test message")
    item_error = BulkItemError(index=0, item={'id': 1}, error=error)
    result = BulkOperationResult(succeeded=[], failed=[item_error])
    
    if len(result.failed) != 1:
        raise AssertionError(f"Expected 1 failed item, got {len(result.failed)}")


def test_bulk_operation_result_success_count():
    """Verify BulkOperationResult.success_count property."""
    result = BulkOperationResult(succeeded=[1, 2, 3], failed=[])
    
    if result.success_count != 3:
        raise AssertionError(f"Expected success_count 3, got {result.success_count}")


def test_bulk_operation_result_failure_count():
    """Verify BulkOperationResult.failure_count property."""
    error = RESTError(error="test_error", message="Test message")
    failed = [
        BulkItemError(index=0, item={'id': 1}, error=error),
        BulkItemError(index=1, item={'id': 2}, error=error),
    ]
    result = BulkOperationResult(succeeded=[], failed=failed)
    
    if result.failure_count != 2:
        raise AssertionError(f"Expected failure_count 2, got {result.failure_count}")


def test_bulk_operation_result_all_succeeded_true():
    """Verify BulkOperationResult.all_succeeded is True when no failures."""
    result = BulkOperationResult(succeeded=[1, 2, 3], failed=[])
    
    if not result.all_succeeded:
        raise AssertionError("Expected all_succeeded to be True")


def test_bulk_operation_result_all_succeeded_false():
    """Verify BulkOperationResult.all_succeeded is False when there are failures."""
    error = RESTError(error="test_error", message="Test message")
    item_error = BulkItemError(index=0, item={'id': 1}, error=error)
    result = BulkOperationResult(succeeded=[1, 2], failed=[item_error])
    
    if result.all_succeeded:
        raise AssertionError("Expected all_succeeded to be False")


def test_bulk_operation_result_to_dict():
    """Verify BulkOperationResult.to_dict() method."""
    error = RESTError(error="test_error", message="Test message")
    item_error = BulkItemError(index=1, item={'id': 2}, error=error)
    result = BulkOperationResult(succeeded=[{'id': 1}], failed=[item_error])
    
    result_dict = result.to_dict()
    
    if result_dict['succeeded'] != [{'id': 1}]:
        raise AssertionError(f"Expected succeeded [{{id: 1}}], got {result_dict['succeeded']}")
    if result_dict['success_count'] != 1:
        raise AssertionError(f"Expected success_count 1, got {result_dict['success_count']}")
    if result_dict['failure_count'] != 1:
        raise AssertionError(f"Expected failure_count 1, got {result_dict['failure_count']}")
    if result_dict['all_succeeded'] != False:
        raise AssertionError("Expected all_succeeded False")
    if len(result_dict['failed']) != 1:
        raise AssertionError(f"Expected 1 failed item, got {len(result_dict['failed'])}")


# =============================================================================
# Unit Tests: execute_bulk_operation
# =============================================================================

def test_execute_bulk_operation_all_succeed():
    """Verify execute_bulk_operation returns all items in succeeded when all pass."""
    items = [1, 2, 3, 4, 5]
    
    def operation(index: int, item: Any) -> Any:
        return item * 2
    
    result = CollectionEndpoint.execute_bulk_operation(items, operation)
    
    if result.success_count != 5:
        raise AssertionError(f"Expected 5 succeeded, got {result.success_count}")
    if result.failure_count != 0:
        raise AssertionError(f"Expected 0 failed, got {result.failure_count}")
    if result.succeeded != [2, 4, 6, 8, 10]:
        raise AssertionError(f"Expected [2, 4, 6, 8, 10], got {result.succeeded}")


def test_execute_bulk_operation_some_fail():
    """Verify execute_bulk_operation handles partial failures."""
    items = [1, 2, 3, 4, 5]
    
    def operation(index: int, item: Any) -> Any:
        if item % 2 == 0:
            raise ValueError(f"Even number not allowed: {item}")
        return item * 2
    
    result = CollectionEndpoint.execute_bulk_operation(items, operation)
    
    if result.success_count != 3:
        raise AssertionError(f"Expected 3 succeeded, got {result.success_count}")
    if result.failure_count != 2:
        raise AssertionError(f"Expected 2 failed, got {result.failure_count}")


def test_execute_bulk_operation_validation_first():
    """Verify execute_bulk_operation validates all items before processing."""
    items = [1, 2, 3, 4, 5]
    processed = []
    
    def operation(index: int, item: Any) -> Any:
        processed.append(item)
        return item * 2
    
    def validate(index: int, item: Any) -> Optional[RESTError]:
        if item == 3:
            return RESTError(error="invalid", message="Item 3 is invalid")
        return None
    
    result = CollectionEndpoint.execute_bulk_operation(items, operation, validate=validate)
    
    # No items should be processed because validation failed
    if len(processed) != 0:
        raise AssertionError(f"Expected 0 items processed, got {len(processed)}")
    
    # All items should be in failed (validation failed for item 3)
    if result.success_count != 0:
        raise AssertionError(f"Expected 0 succeeded, got {result.success_count}")
    if result.failure_count != 1:
        raise AssertionError(f"Expected 1 failed, got {result.failure_count}")


def test_execute_bulk_operation_atomic_raises_on_failure():
    """Verify execute_bulk_operation raises BulkOperationError in atomic mode."""
    items = [1, 2, 3]
    
    def operation(index: int, item: Any) -> Any:
        if item == 2:
            raise ValueError("Item 2 failed")
        return item * 2
    
    raised = False
    try:
        CollectionEndpoint.execute_bulk_operation(items, operation, atomic=True)
    except BulkOperationError as e:
        raised = True
        # Items 1 and 3 succeed, item 2 fails
        if e.result.success_count != 2:
            raise AssertionError(f"Expected 2 succeeded, got {e.result.success_count}")
        if e.result.failure_count != 1:
            raise AssertionError(f"Expected 1 failed, got {e.result.failure_count}")
    
    if not raised:
        raise AssertionError("Expected BulkOperationError to be raised")


# =============================================================================
# Unit Tests: get_bulk_routes
# =============================================================================

def test_get_bulk_routes_disabled():
    """Verify get_bulk_routes returns empty list when bulk_enabled=False."""
    routes = CollectionEndpoint.get_bulk_routes()
    
    if routes != []:
        raise AssertionError(f"Expected empty list, got {routes}")


def test_get_bulk_routes_enabled():
    """Verify get_bulk_routes returns routes when bulk_enabled=True."""
    
    class BulkEnabledEndpoint(CollectionEndpoint):
        bulk_enabled = True
    
    routes = BulkEnabledEndpoint.get_bulk_routes()
    
    if len(routes) != 3:
        raise AssertionError(f"Expected 3 routes, got {len(routes)}")
    
    # Check POST /bulk route
    post_route = [r for r in routes if r[0] == "POST"]
    if len(post_route) != 1:
        raise AssertionError("Expected POST /bulk route")
    if post_route[0][1] != "/bulk":
        raise AssertionError(f"Expected path '/bulk', got {post_route[0][1]}")
    if post_route[0][2] != "bulk_create":
        raise AssertionError(f"Expected handler 'bulk_create', got {post_route[0][2]}")
    
    # Check PUT /bulk route
    put_route = [r for r in routes if r[0] == "PUT"]
    if len(put_route) != 1:
        raise AssertionError("Expected PUT /bulk route")
    if put_route[0][2] != "bulk_update":
        raise AssertionError(f"Expected handler 'bulk_update', got {put_route[0][2]}")
    
    # Check DELETE /bulk route
    delete_route = [r for r in routes if r[0] == "DELETE"]
    if len(delete_route) != 1:
        raise AssertionError("Expected DELETE /bulk route")
    if delete_route[0][2] != "bulk_delete":
        raise AssertionError(f"Expected handler 'bulk_delete', got {delete_route[0][2]}")


# =============================================================================
# Unit Tests: BulkOperationError
# =============================================================================

def test_bulk_operation_error_has_message():
    """Verify BulkOperationError has message attribute."""
    result = BulkOperationResult(succeeded=[], failed=[])
    error = BulkOperationError("Test error", result)
    
    if error.message != "Test error":
        raise AssertionError(f"Expected message 'Test error', got {error.message}")


def test_bulk_operation_error_has_result():
    """Verify BulkOperationError has result attribute."""
    result = BulkOperationResult(succeeded=[1, 2], failed=[])
    error = BulkOperationError("Test error", result)
    
    if error.result != result:
        raise AssertionError("BulkOperationError should have result attribute")


# =============================================================================
# Property-Based Tests
# =============================================================================

# Feature: rest-api-support, Property 10: Bulk Operation Results
# *For any* bulk operation (create, update, delete) with N items, the
# BulkOperationResult SHALL contain exactly N results split between succeeded
# and failed lists, with each failed item including its index and error details.
# **Validates: Requirements 12.1, 12.2, 12.3, 12.5, 12.6**

def test_property_10_bulk_operation_result_count():
    """
        Property 10: Bulk Operation Results (result count equals input count)
        
        For any bulk operation with N items, the BulkOperationResult SHALL
        contain exactly N results split between succeeded and failed lists.
        
        **Validates: Requirements 12.1, 12.2, 12.3, 12.5, 12.6**
    """
    # Run 100 iterations with random item counts
    for iteration in range(100):
        # Generate random number of items (1 to 50)
        num_items = random.randint(1, 50)
        items = list(range(num_items))
        
        # Randomly decide which items will fail (0 to all)
        fail_indices = set(random.sample(range(num_items), random.randint(0, num_items)))
        
        def operation(index: int, item: Any) -> Any:
            if index in fail_indices:
                raise ValueError(f"Item {item} failed")
            return item * 2
        
        result = CollectionEndpoint.execute_bulk_operation(items, operation)
        
        # Property: succeeded + failed count must equal input count
        total_results = result.success_count + result.failure_count
        if total_results != num_items:
            errmsg = f"Iteration {iteration}: Expected {num_items} total results, got {total_results}"
            raise AssertionError(errmsg)
    
    return


def test_property_10_bulk_operation_failed_items_have_index():
    """
        Property 10: Bulk Operation Results (failed items have index)
        
        For any bulk operation, each failed item SHALL include its index
        in the original request list.
        
        **Validates: Requirements 12.5**
    """
    # Run 100 iterations with random item counts
    for iteration in range(100):
        # Generate random number of items (1 to 30)
        num_items = random.randint(1, 30)
        items = list(range(num_items))
        
        # Randomly decide which items will fail (at least 1)
        num_failures = random.randint(1, max(1, num_items))
        fail_indices = set(random.sample(range(num_items), num_failures))
        
        def operation(index: int, item: Any) -> Any:
            if index in fail_indices:
                raise ValueError(f"Item {item} failed")
            return item * 2
        
        result = CollectionEndpoint.execute_bulk_operation(items, operation)
        
        # Property: each failed item must have a valid index
        for item_error in result.failed:
            if not isinstance(item_error.index, int):
                errmsg = f"Iteration {iteration}: Failed item index must be int, got {type(item_error.index)}"
                raise AssertionError(errmsg)
            
            if item_error.index < 0 or item_error.index >= num_items:
                errmsg = f"Iteration {iteration}: Failed item index {item_error.index} out of range [0, {num_items})"
                raise AssertionError(errmsg)
            
            if item_error.index not in fail_indices:
                errmsg = f"Iteration {iteration}: Failed item index {item_error.index} was not expected to fail"
                raise AssertionError(errmsg)
    
    return


def test_property_10_bulk_operation_failed_items_have_error():
    """
        Property 10: Bulk Operation Results (failed items have error details)
        
        For any bulk operation, each failed item SHALL include error details.
        
        **Validates: Requirements 12.5**
    """
    # Run 100 iterations with random item counts
    for iteration in range(100):
        # Generate random number of items (1 to 30)
        num_items = random.randint(1, 30)
        items = list(range(num_items))
        
        # Randomly decide which items will fail (at least 1)
        num_failures = random.randint(1, max(1, num_items))
        fail_indices = set(random.sample(range(num_items), num_failures))
        
        def operation(index: int, item: Any) -> Any:
            if index in fail_indices:
                raise ValueError(f"Item {item} failed")
            return item * 2
        
        result = CollectionEndpoint.execute_bulk_operation(items, operation)
        
        # Property: each failed item must have error details
        for item_error in result.failed:
            if item_error.error is None:
                errmsg = f"Iteration {iteration}: Failed item must have error details"
                raise AssertionError(errmsg)
            
            if not isinstance(item_error.error, RESTError):
                errmsg = f"Iteration {iteration}: Error must be RESTError, got {type(item_error.error)}"
                raise AssertionError(errmsg)
            
            if not item_error.error.error:
                errmsg = f"Iteration {iteration}: Error must have error code"
                raise AssertionError(errmsg)
            
            if not item_error.error.message:
                errmsg = f"Iteration {iteration}: Error must have message"
                raise AssertionError(errmsg)
    
    return


def test_property_10_bulk_operation_validation_first():
    """
        Property 10: Bulk Operation Results (validation-first processing)
        
        For any bulk operation with validation, if any item fails validation,
        no items SHALL be processed.
        
        **Validates: Requirements 12.6**
    """
    # Run 100 iterations with random item counts
    for iteration in range(100):
        # Generate random number of items (2 to 30)
        num_items = random.randint(2, 30)
        items = list(range(num_items))
        
        # Randomly decide which items will fail validation (at least 1)
        num_validation_failures = random.randint(1, max(1, num_items // 2))
        fail_validation_indices = set(random.sample(range(num_items), num_validation_failures))
        
        processed_items = []
        
        def operation(index: int, item: Any) -> Any:
            processed_items.append(item)
            return item * 2
        
        def validate(index: int, item: Any) -> Optional[RESTError]:
            if index in fail_validation_indices:
                return RESTError(error="validation_error", message=f"Item {item} invalid")
            return None
        
        result = CollectionEndpoint.execute_bulk_operation(items, operation, validate=validate)
        
        # Property: no items should be processed when validation fails
        if len(processed_items) != 0:
            errmsg = f"Iteration {iteration}: Expected 0 items processed when validation fails, got {len(processed_items)}"
            raise AssertionError(errmsg)
        
        # Property: succeeded should be empty
        if result.success_count != 0:
            errmsg = f"Iteration {iteration}: Expected 0 succeeded when validation fails, got {result.success_count}"
            raise AssertionError(errmsg)
        
        # Property: failed should contain only validation failures
        if result.failure_count != num_validation_failures:
            errmsg = f"Iteration {iteration}: Expected {num_validation_failures} failed, got {result.failure_count}"
            raise AssertionError(errmsg)
    
    return


def test_property_10_bulk_operation_all_succeed():
    """
        Property 10: Bulk Operation Results (all items succeed)
        
        For any bulk operation where all items succeed, the BulkOperationResult
        SHALL have all items in succeeded and none in failed.
        
        **Validates: Requirements 12.1, 12.2, 12.3**
    """
    # Run 100 iterations with random item counts
    for iteration in range(100):
        # Generate random number of items (1 to 50)
        num_items = random.randint(1, 50)
        items = generate_random_items(num_items)
        
        def operation(index: int, item: Any) -> Any:
            return {'processed': True, **item}
        
        result = CollectionEndpoint.execute_bulk_operation(items, operation)
        
        # Property: all items should succeed
        if result.success_count != num_items:
            errmsg = f"Iteration {iteration}: Expected {num_items} succeeded, got {result.success_count}"
            raise AssertionError(errmsg)
        
        # Property: no items should fail
        if result.failure_count != 0:
            errmsg = f"Iteration {iteration}: Expected 0 failed, got {result.failure_count}"
            raise AssertionError(errmsg)
        
        # Property: all_succeeded should be True
        if not result.all_succeeded:
            errmsg = f"Iteration {iteration}: Expected all_succeeded to be True"
            raise AssertionError(errmsg)
    
    return


def test_property_10_bulk_operation_mixed_results():
    """
        Property 10: Bulk Operation Results (mixed success and failure)
        
        For any bulk operation with mixed results, the BulkOperationResult
        SHALL correctly partition items between succeeded and failed.
        
        **Validates: Requirements 12.1, 12.2, 12.3, 12.5**
    """
    # Run 100 iterations with random item counts
    for iteration in range(100):
        # Generate random number of items (2 to 50)
        num_items = random.randint(2, 50)
        items = list(range(num_items))
        
        # Randomly decide which items will fail (at least 1, at most num_items - 1)
        num_failures = random.randint(1, max(1, num_items - 1))
        fail_indices = set(random.sample(range(num_items), num_failures))
        expected_successes = num_items - num_failures
        
        def operation(index: int, item: Any) -> Any:
            if index in fail_indices:
                raise ValueError(f"Item {item} failed")
            return item * 2
        
        result = CollectionEndpoint.execute_bulk_operation(items, operation)
        
        # Property: success count should match expected
        if result.success_count != expected_successes:
            errmsg = f"Iteration {iteration}: Expected {expected_successes} succeeded, got {result.success_count}"
            raise AssertionError(errmsg)
        
        # Property: failure count should match expected
        if result.failure_count != num_failures:
            errmsg = f"Iteration {iteration}: Expected {num_failures} failed, got {result.failure_count}"
            raise AssertionError(errmsg)
        
        # Property: total should equal input count
        total = result.success_count + result.failure_count
        if total != num_items:
            errmsg = f"Iteration {iteration}: Expected total {num_items}, got {total}"
            raise AssertionError(errmsg)
        
        # Property: all_succeeded should be False
        if result.all_succeeded:
            errmsg = f"Iteration {iteration}: Expected all_succeeded to be False"
            raise AssertionError(errmsg)
        
        # Property: failed indices should match expected
        failed_indices_actual = {item_error.index for item_error in result.failed}
        if failed_indices_actual != fail_indices:
            errmsg = f"Iteration {iteration}: Failed indices mismatch. Expected {fail_indices}, got {failed_indices_actual}"
            raise AssertionError(errmsg)
    
    return


# =============================================================================
# The list and bulk routes are registered and served
# =============================================================================

import json

from dataclasses import dataclass

from ccai.webworks.routing.dispatcher import Dispatcher
from ccai.webworks.routing.request import Request
from ccai.webworks.routing.router import Router


@dataclass
class NoteIn:
    """Request schema for the served collection tests."""
    text: str


class NoteCollection(CollectionEndpoint):
    """A collection endpoint that records how its operations were called."""

    resource_name = "notes"
    request_schema = NoteIn
    filter_fields = ["author"]
    sort_fields = ["created"]
    max_page_size = 50
    bulk_enabled = True

    calls: List[Any] = []

    def list(self, page=1, page_size=None, filters=None, sort=None):
        type(self).calls.append(("list", page, page_size, filters, sort))
        return PaginatedResponse(
            items=[{"text": "first"}],
            pagination=PaginationInfo.create(total=1, page=page, page_size=page_size, base_url="/notes"),
        )

    def get(self, id):
        return {"id": id}

    def bulk_create(self, payloads):
        type(self).calls.append(("bulk_create", payloads))
        return BulkOperationResult(succeeded=[{"text": payload.text} for payload in payloads], failed=[])

    def bulk_delete(self, ids):
        type(self).calls.append(("bulk_delete", ids))
        return BulkOperationResult(succeeded=list(ids), failed=[])


def _serve_notes(method: str, path: str, body=None, query: bytes = b""):
    """Register NoteCollection on a Router and dispatch one request to it."""
    NoteCollection.calls = []

    router = Router()
    NoteCollection.register(router)

    headers = {}
    raw_body = b""
    if body is not None:
        raw_body = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    response = Dispatcher(router).dispatch(Request(method, path, query_string=query, headers=headers, body=raw_body))
    return response


def test_register_includes_a_list_route():
    """register() returns a GET route for the collection path."""
    descriptors = NoteCollection.register()

    list_routes = [d for d in descriptors if d.path == "/notes" and d.methods == ["GET"]]

    if len(list_routes) != 1:
        raise AssertionError(f"Expected one GET /notes route, got {[(d.path, d.methods) for d in descriptors]}")


def test_register_includes_the_bulk_routes_when_enabled():
    """register() returns the POST, PUT and DELETE bulk routes of get_bulk_routes()."""
    descriptors = NoteCollection.register()

    bulk_methods = sorted(d.methods[0] for d in descriptors if d.path == "/notes/bulk")

    if bulk_methods != ["DELETE", "POST", "PUT"]:
        raise AssertionError(f"Expected bulk routes for DELETE, POST and PUT, got {bulk_methods}")


def test_register_omits_the_bulk_routes_when_disabled():
    """A collection without bulk_enabled registers no bulk route."""

    class PlainCollection(CollectionEndpoint):
        resource_name = "plain"

    paths = [d.path for d in PlainCollection.register()]

    if "/plain/bulk" in paths:
        raise AssertionError(f"Expected no bulk route, got {paths}")


def test_served_list_parses_pagination_filters_and_sort_from_the_query():
    """GET /notes passes the page, clamped page size, allowed filters and allowed sort fields to list()."""
    response = _serve_notes("GET", "/notes", query=b"page=2&page_size=500&author=ann&ignored=x&sort=-created,bogus")

    if response.status_code != 200:
        raise AssertionError(f"Expected 200, got {response.status_code}: {response.body!r}")

    expected_call = ("list", 2, 50, {"author": "ann"}, ["-created"])
    if NoteCollection.calls != [expected_call]:
        raise AssertionError(f"Expected list() to be called as {expected_call}, got {NoteCollection.calls}")


def test_served_list_returns_the_paginated_response_layout():
    """GET /notes returns the items with the pagination block of PaginatedResponse.to_dict()."""
    response = _serve_notes("GET", "/notes")
    body = json.loads(response.body)

    if body["items"] != [{"text": "first"}]:
        raise AssertionError(f"Unexpected items: {body['items']}")

    if body["pagination"]["page"] != 1 or "links" not in body["pagination"]:
        raise AssertionError(f"Unexpected pagination block: {body['pagination']}")


def test_served_list_route_does_not_shadow_the_item_route():
    """GET /notes/3 still reaches get(3) beside the list route."""
    response = _serve_notes("GET", "/notes/3")

    if response.status_code != 200 or json.loads(response.body) != {"id": 3}:
        raise AssertionError(f"Unexpected response: {response.status_code} {response.body!r}")


def test_served_bulk_create_validates_each_item_and_returns_200():
    """POST /notes/bulk validates every item into the request schema and reports the result with 200."""
    response = _serve_notes("POST", "/notes/bulk", body=[{"text": "a"}, {"text": "b"}])
    body = json.loads(response.body)

    if response.status_code != 200 or body["success_count"] != 2:
        raise AssertionError(f"Expected 200 with two successes, got {response.status_code} {body}")

    if NoteCollection.calls != [("bulk_create", [NoteIn(text="a"), NoteIn(text="b")])]:
        raise AssertionError(f"Expected bulk_create to receive validated items, got {NoteCollection.calls}")


def test_served_bulk_create_reports_invalid_items_by_index():
    """An invalid item rejects the whole bulk request, its errors prefixed with the item's index."""
    response = _serve_notes("POST", "/notes/bulk", body=[{"text": "a"}, {"text": 5}])
    body = json.loads(response.body)

    if response.status_code != 400:
        raise AssertionError(f"Expected 400, got {response.status_code} {body}")

    if [field_error["field"] for field_error in body["field_errors"]] != ["1.text"]:
        raise AssertionError(f"Expected a field error for '1.text', got {body['field_errors']}")

    if len(NoteCollection.calls) != 0:
        raise AssertionError("bulk_create must not be called when an item is invalid")


def test_served_bulk_delete_passes_the_identifiers():
    """DELETE /notes/bulk passes the JSON array of identifiers to bulk_delete()."""
    response = _serve_notes("DELETE", "/notes/bulk", body=[1, 2, 3])

    if response.status_code != 200:
        raise AssertionError(f"Expected 200, got {response.status_code}: {response.body!r}")

    if NoteCollection.calls != [("bulk_delete", [1, 2, 3])]:
        raise AssertionError(f"Expected bulk_delete([1, 2, 3]), got {NoteCollection.calls}")


def test_served_bulk_route_rejects_a_body_that_is_not_an_array():
    """A bulk request whose body is not a JSON array is a 400."""
    response = _serve_notes("POST", "/notes/bulk", body={"text": "a"})

    if response.status_code != 400:
        raise AssertionError(f"Expected 400, got {response.status_code}: {response.body!r}")


def test_list_query_params_are_declared_for_documentation():
    """The list route declares its pagination, sort and filter query parameters."""
    descriptors = NoteCollection.register()
    list_route = [d for d in descriptors if d.path == "/notes" and d.methods == ["GET"]][0]

    declared = list_route.extras["rest"]["query_params"]

    if declared != {"page": int, "page_size": int, "sort": str, "author": str}:
        raise AssertionError(f"Unexpected query parameters: {declared}")
