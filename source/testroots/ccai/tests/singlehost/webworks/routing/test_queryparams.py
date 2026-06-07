"""
    Tests for the QueryParams class.
    
    This module contains unit tests for query string parsing functionality.
"""

from ccai.webworks.routing.queryparams import QueryParams


# =============================================================================
# Unit Tests for QueryParams - Basic Parsing
# =============================================================================

def test_queryparams_parses_simple_query_string():
    """
        Test that QueryParams parses a simple query string.
    """
    qp = QueryParams(b"name=test&id=123")
    
    result = qp.get("name")
    
    expected = "test"
    if result != expected:
        errmsg = f"Expected '{expected}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_queryparams_getitem_returns_first_value():
    """
        Test that __getitem__ returns the first value for a key.
    """
    qp = QueryParams(b"name=first&name=second")
    
    result = qp["name"]
    
    expected = "first"
    if result != expected:
        errmsg = f"Expected '{expected}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_queryparams_getitem_raises_keyerror_for_missing_key():
    """
        Test that __getitem__ raises KeyError for missing key.
    """
    qp = QueryParams(b"name=test")
    
    try:
        _ = qp["missing"]
        errmsg = "Expected KeyError for missing key"
        raise AssertionError(errmsg)
    except KeyError:
        pass
    
    return


def test_queryparams_get_returns_default_for_missing_key():
    """
        Test that get() returns default for missing key.
    """
    qp = QueryParams(b"name=test")
    
    result = qp.get("missing", "default_value")
    
    expected = "default_value"
    if result != expected:
        errmsg = f"Expected '{expected}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_queryparams_get_returns_none_when_no_default():
    """
        Test that get() returns None when no default provided.
    """
    qp = QueryParams(b"name=test")
    
    result = qp.get("missing")
    
    if result is not None:
        errmsg = f"Expected None, got '{result}'"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for QueryParams - Multi-Value Keys
# =============================================================================

def test_queryparams_getlist_returns_all_values():
    """
        Test that getlist() returns all values for a key.
    """
    qp = QueryParams(b"tag=python&tag=web&tag=api")
    
    result = qp.getlist("tag")
    
    expected = ["python", "web", "api"]
    if result != expected:
        errmsg = f"Expected {expected}, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_queryparams_getlist_returns_empty_list_for_missing_key():
    """
        Test that getlist() returns empty list for missing key.
    """
    qp = QueryParams(b"name=test")
    
    result = qp.getlist("missing")
    
    expected = []
    if result != expected:
        errmsg = f"Expected {expected}, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_queryparams_getlist_returns_single_item_list():
    """
        Test that getlist() returns single-item list for single value.
    """
    qp = QueryParams(b"name=test")
    
    result = qp.getlist("name")
    
    expected = ["test"]
    if result != expected:
        errmsg = f"Expected {expected}, got {result}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for QueryParams - Dict-Like Interface
# =============================================================================

def test_queryparams_keys_returns_all_keys():
    """
        Test that keys() returns all parameter names.
    """
    qp = QueryParams(b"name=test&id=123&active=true")
    
    result = list(qp.keys())
    
    expected_keys = {"name", "id", "active"}
    if set(result) != expected_keys:
        errmsg = f"Expected keys {expected_keys}, got {set(result)}"
        raise AssertionError(errmsg)
    
    return


def test_queryparams_items_returns_first_values():
    """
        Test that items() returns first value per key.
    """
    qp = QueryParams(b"name=first&name=second&id=123")
    
    result = dict(qp.items())
    
    expected = {"name": "first", "id": "123"}
    if result != expected:
        errmsg = f"Expected {expected}, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_queryparams_contains_returns_true_for_existing_key():
    """
        Test that __contains__ returns True for existing key.
    """
    qp = QueryParams(b"name=test")
    
    result = "name" in qp
    
    if not result:
        errmsg = "Expected 'name' to be in QueryParams"
        raise AssertionError(errmsg)
    
    return


def test_queryparams_contains_returns_false_for_missing_key():
    """
        Test that __contains__ returns False for missing key.
    """
    qp = QueryParams(b"name=test")
    
    result = "missing" in qp
    
    if result:
        errmsg = "Did not expect 'missing' to be in QueryParams"
        raise AssertionError(errmsg)
    
    return


def test_queryparams_len_returns_number_of_keys():
    """
        Test that __len__ returns number of unique keys.
    """
    qp = QueryParams(b"name=test&id=123&tag=a&tag=b")
    
    result = len(qp)
    
    expected = 3
    if result != expected:
        errmsg = f"Expected length {expected}, got {result}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for QueryParams - Edge Cases
# =============================================================================

def test_queryparams_handles_empty_query_string():
    """
        Test that QueryParams handles empty query string.
    """
    qp = QueryParams(b"")
    
    result = len(qp)
    
    expected = 0
    if result != expected:
        errmsg = f"Expected length {expected}, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_queryparams_handles_blank_values():
    """
        Test that QueryParams handles blank values.
    """
    qp = QueryParams(b"name=&id=123")
    
    result = qp.get("name")
    
    expected = ""
    if result != expected:
        errmsg = f"Expected empty string, got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_queryparams_handles_url_encoded_values():
    """
        Test that QueryParams handles URL-encoded values.
    """
    qp = QueryParams(b"name=hello%20world&path=%2Fapi%2Fusers")
    
    name_result = qp.get("name")
    path_result = qp.get("path")
    
    if name_result != "hello world":
        errmsg = f"Expected 'hello world', got '{name_result}'"
        raise AssertionError(errmsg)
    
    if path_result != "/api/users":
        errmsg = f"Expected '/api/users', got '{path_result}'"
        raise AssertionError(errmsg)
    
    return


def test_queryparams_handles_string_input():
    """
        Test that QueryParams handles string input (not just bytes).
    """
    # The class should handle string input gracefully
    qp = QueryParams("name=test&id=123")  # type: ignore
    
    result = qp.get("name")
    
    expected = "test"
    if result != expected:
        errmsg = f"Expected '{expected}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_queryparams_repr_shows_dict():
    """
        Test that __repr__ shows dict representation.
    """
    qp = QueryParams(b"name=test&id=123")
    
    result = repr(qp)
    
    if "QueryParams" not in result:
        errmsg = f"Expected 'QueryParams' in repr, got '{result}'"
        raise AssertionError(errmsg)
    
    return
