"""
    Tests for the TemplateContext class.
    
    This module tests the TemplateContext including:
    - Dictionary-like interface (__getitem__, __setitem__, __contains__)
    - get() method with default values
    - update() method for bulk updates
    - merge() method for combining contexts
    - to_dict() method for conversion
    - Edge cases and boundary conditions
"""

from ccai.webworks.templating.context import TemplateContext
from ccai.webworks.templating.exceptions import UndefinedVariableError


# =============================================================================
# __init__() Method Tests
# =============================================================================

def test_init_with_no_arguments():
    """
        Test that __init__() creates an empty context with no arguments.
    """
    context = TemplateContext()
    
    result = context.to_dict()
    
    if result != {}:
        raise AssertionError(f"Expected empty dict, got {result}")
    
    return


def test_init_with_none():
    """
        Test that __init__() creates an empty context when passed None.
    """
    context = TemplateContext(None)
    
    result = context.to_dict()
    
    if result != {}:
        raise AssertionError(f"Expected empty dict, got {result}")
    
    return


def test_init_with_initial_data():
    """
        Test that __init__() initializes context with provided data.
    """
    initial = {"title": "Home", "count": 42}
    context = TemplateContext(initial)
    
    result = context.to_dict()
    
    if result != initial:
        raise AssertionError(f"Expected {initial}, got {result}")
    
    return


def test_init_copies_initial_data():
    """
        Test that __init__() copies the initial data (not reference).
    """
    initial = {"title": "Home"}
    context = TemplateContext(initial)
    
    # Modify original dict
    initial["title"] = "Modified"
    
    # Context should not be affected
    if context["title"] != "Home":
        raise AssertionError("Context should not be affected by changes to initial dict")
    
    return


def test_init_with_empty_dict():
    """
        Test that __init__() works with an empty dictionary.
    """
    context = TemplateContext({})
    
    result = context.to_dict()
    
    if result != {}:
        raise AssertionError(f"Expected empty dict, got {result}")
    
    return


def test_init_with_nested_data():
    """
        Test that __init__() handles nested data structures.
    """
    initial = {
        "user": {"name": "Alice", "age": 30},
        "items": [1, 2, 3]
    }
    context = TemplateContext(initial)
    
    result = context.to_dict()
    
    if result != initial:
        raise AssertionError(f"Expected {initial}, got {result}")
    
    return


# =============================================================================
# __getitem__() Method Tests
# =============================================================================

def test_getitem_returns_value():
    """
        Test that __getitem__() returns the value for an existing key.
    """
    context = TemplateContext({"title": "Home"})
    
    result = context["title"]
    
    if result != "Home":
        raise AssertionError(f"Expected 'Home', got {result}")
    
    return


def test_getitem_raises_keyerror_for_missing_key():
    """
        Test that __getitem__() raises KeyError for missing key.
    """
    context = TemplateContext({"title": "Home"})
    
    try:
        _ = context["missing"]
        raise AssertionError("Expected KeyError to be raised")
    except KeyError:
        pass
    
    return


def test_getitem_with_various_value_types():
    """
        Test that __getitem__() works with various value types.
    """
    context = TemplateContext({
        "string": "hello",
        "number": 42,
        "float": 3.14,
        "boolean": True,
        "none": None,
        "list": [1, 2, 3],
        "dict": {"nested": "value"}
    })
    
    if context["string"] != "hello":
        raise AssertionError("String value mismatch")
    
    if context["number"] != 42:
        raise AssertionError("Number value mismatch")
    
    if context["float"] != 3.14:
        raise AssertionError("Float value mismatch")
    
    if context["boolean"] is not True:
        raise AssertionError("Boolean value mismatch")
    
    if context["none"] is not None:
        raise AssertionError("None value mismatch")
    
    if context["list"] != [1, 2, 3]:
        raise AssertionError("List value mismatch")
    
    if context["dict"] != {"nested": "value"}:
        raise AssertionError("Dict value mismatch")
    
    return


# =============================================================================
# __setitem__() Method Tests
# =============================================================================

def test_setitem_adds_new_key():
    """
        Test that __setitem__() adds a new key to the context.
    """
    context = TemplateContext()
    
    context["title"] = "Home"
    
    if context["title"] != "Home":
        raise AssertionError(f"Expected 'Home', got {context['title']}")
    
    return


def test_setitem_overwrites_existing_key():
    """
        Test that __setitem__() overwrites an existing key.
    """
    context = TemplateContext({"title": "Home"})
    
    context["title"] = "About"
    
    if context["title"] != "About":
        raise AssertionError(f"Expected 'About', got {context['title']}")
    
    return


def test_setitem_with_none_value():
    """
        Test that __setitem__() can set None as a value.
    """
    context = TemplateContext()
    
    context["nullable"] = None
    
    if context["nullable"] is not None:
        raise AssertionError("Expected None value")
    
    if "nullable" not in context:
        raise AssertionError("Key should exist in context")
    
    return


def test_setitem_with_complex_value():
    """
        Test that __setitem__() can set complex values.
    """
    context = TemplateContext()
    
    complex_value = {"nested": {"deep": [1, 2, {"key": "value"}]}}
    context["complex"] = complex_value
    
    if context["complex"] != complex_value:
        raise AssertionError(f"Expected {complex_value}, got {context['complex']}")
    
    return


# =============================================================================
# __contains__() Method Tests
# =============================================================================

def test_contains_returns_true_for_existing_key():
    """
        Test that __contains__() returns True for existing key.
    """
    context = TemplateContext({"title": "Home"})
    
    result = "title" in context
    
    if result is not True:
        raise AssertionError(f"Expected True, got {result}")
    
    return


def test_contains_returns_false_for_missing_key():
    """
        Test that __contains__() returns False for missing key.
    """
    context = TemplateContext({"title": "Home"})
    
    result = "missing" in context
    
    if result is not False:
        raise AssertionError(f"Expected False, got {result}")
    
    return


def test_contains_returns_true_for_none_value():
    """
        Test that __contains__() returns True when value is None.
    """
    context = TemplateContext({"nullable": None})
    
    result = "nullable" in context
    
    if result is not True:
        raise AssertionError(f"Expected True, got {result}")
    
    return


def test_contains_on_empty_context():
    """
        Test that __contains__() returns False on empty context.
    """
    context = TemplateContext()
    
    result = "anything" in context
    
    if result is not False:
        raise AssertionError(f"Expected False, got {result}")
    
    return


# =============================================================================
# get() Method Tests
# =============================================================================

def test_get_returns_value_for_existing_key():
    """
        Test that get() returns the value for an existing key.
    """
    context = TemplateContext({"title": "Home"})
    
    result = context.get("title")
    
    if result != "Home":
        raise AssertionError(f"Expected 'Home', got {result}")
    
    return


def test_get_returns_none_for_missing_key():
    """
        Test that get() returns None for missing key by default.
    """
    context = TemplateContext({"title": "Home"})
    
    result = context.get("missing")
    
    if result is not None:
        raise AssertionError(f"Expected None, got {result}")
    
    return


def test_get_returns_default_for_missing_key():
    """
        Test that get() returns the default value for missing key.
    """
    context = TemplateContext({"title": "Home"})
    
    result = context.get("missing", "default_value")
    
    if result != "default_value":
        raise AssertionError(f"Expected 'default_value', got {result}")
    
    return


def test_get_returns_value_not_default_for_existing_key():
    """
        Test that get() returns value, not default, for existing key.
    """
    context = TemplateContext({"title": "Home"})
    
    result = context.get("title", "default_value")
    
    if result != "Home":
        raise AssertionError(f"Expected 'Home', got {result}")
    
    return


def test_get_returns_none_value_not_default():
    """
        Test that get() returns None value, not default, when value is None.
    """
    context = TemplateContext({"nullable": None})
    
    result = context.get("nullable", "default_value")
    
    if result is not None:
        raise AssertionError(f"Expected None, got {result}")
    
    return


def test_get_with_various_default_types():
    """
        Test that get() works with various default value types.
    """
    context = TemplateContext()
    
    if context.get("missing", 0) != 0:
        raise AssertionError("Integer default failed")
    
    if context.get("missing", []) != []:
        raise AssertionError("List default failed")
    
    if context.get("missing", {}) != {}:
        raise AssertionError("Dict default failed")
    
    if context.get("missing", False) is not False:
        raise AssertionError("Boolean default failed")
    
    return


# =============================================================================
# update() Method Tests
# =============================================================================

def test_update_adds_new_keys():
    """
        Test that update() adds new keys to the context.
    """
    context = TemplateContext({"title": "Home"})
    
    context.update({"count": 42, "active": True})
    
    if context["title"] != "Home":
        raise AssertionError("Original key should remain")
    
    if context["count"] != 42:
        raise AssertionError("New key 'count' should be added")
    
    if context["active"] is not True:
        raise AssertionError("New key 'active' should be added")
    
    return


def test_update_overwrites_existing_keys():
    """
        Test that update() overwrites existing keys.
    """
    context = TemplateContext({"title": "Home", "count": 10})
    
    context.update({"title": "About", "count": 42})
    
    if context["title"] != "About":
        raise AssertionError(f"Expected 'About', got {context['title']}")
    
    if context["count"] != 42:
        raise AssertionError(f"Expected 42, got {context['count']}")
    
    return


def test_update_with_empty_dict():
    """
        Test that update() with empty dict does nothing.
    """
    context = TemplateContext({"title": "Home"})
    
    context.update({})
    
    result = context.to_dict()
    
    if result != {"title": "Home"}:
        raise AssertionError(f"Expected {{'title': 'Home'}}, got {result}")
    
    return


def test_update_on_empty_context():
    """
        Test that update() works on empty context.
    """
    context = TemplateContext()
    
    context.update({"title": "Home", "count": 42})
    
    if context["title"] != "Home":
        raise AssertionError("Key 'title' should be added")
    
    if context["count"] != 42:
        raise AssertionError("Key 'count' should be added")
    
    return


def test_update_does_not_affect_original_dict():
    """
        Test that update() copies data, not references.
    """
    context = TemplateContext()
    data = {"title": "Home"}
    
    context.update(data)
    
    # Modify original dict
    data["title"] = "Modified"
    
    # Context should not be affected
    if context["title"] != "Home":
        raise AssertionError("Context should not be affected by changes to update dict")
    
    return


# =============================================================================
# merge() Method Tests
# =============================================================================

def test_merge_creates_new_context():
    """
        Test that merge() creates a new context instance.
    """
    context1 = TemplateContext({"title": "Home"})
    context2 = TemplateContext({"count": 42})
    
    merged = context1.merge(context2)
    
    if merged is context1:
        raise AssertionError("Merged context should be a new instance")
    
    if merged is context2:
        raise AssertionError("Merged context should be a new instance")
    
    return


def test_merge_combines_both_contexts():
    """
        Test that merge() combines variables from both contexts.
    """
    context1 = TemplateContext({"title": "Home"})
    context2 = TemplateContext({"count": 42})
    
    merged = context1.merge(context2)
    
    if merged["title"] != "Home":
        raise AssertionError("Merged context should have 'title'")
    
    if merged["count"] != 42:
        raise AssertionError("Merged context should have 'count'")
    
    return


def test_merge_other_takes_precedence():
    """
        Test that merge() gives precedence to the other context.
    """
    context1 = TemplateContext({"title": "Home", "count": 10})
    context2 = TemplateContext({"title": "About"})
    
    merged = context1.merge(context2)
    
    if merged["title"] != "About":
        raise AssertionError("Other context should take precedence")
    
    if merged["count"] != 10:
        raise AssertionError("Non-conflicting key should be preserved")
    
    return


def test_merge_does_not_modify_original_contexts():
    """
        Test that merge() does not modify the original contexts.
    """
    context1 = TemplateContext({"title": "Home"})
    context2 = TemplateContext({"count": 42})
    
    merged = context1.merge(context2)
    
    # Modify merged context
    merged["new_key"] = "new_value"
    
    # Original contexts should not be affected
    if "new_key" in context1:
        raise AssertionError("context1 should not be modified")
    
    if "new_key" in context2:
        raise AssertionError("context2 should not be modified")
    
    if "count" in context1:
        raise AssertionError("context1 should not have 'count'")
    
    if "title" in context2:
        raise AssertionError("context2 should not have 'title'")
    
    return


def test_merge_with_empty_other():
    """
        Test that merge() with empty other context returns copy of self.
    """
    context1 = TemplateContext({"title": "Home"})
    context2 = TemplateContext()
    
    merged = context1.merge(context2)
    
    result = merged.to_dict()
    
    if result != {"title": "Home"}:
        raise AssertionError(f"Expected {{'title': 'Home'}}, got {result}")
    
    return


def test_merge_with_empty_self():
    """
        Test that merge() with empty self returns copy of other.
    """
    context1 = TemplateContext()
    context2 = TemplateContext({"title": "Home"})
    
    merged = context1.merge(context2)
    
    result = merged.to_dict()
    
    if result != {"title": "Home"}:
        raise AssertionError(f"Expected {{'title': 'Home'}}, got {result}")
    
    return


def test_merge_both_empty():
    """
        Test that merge() with both empty returns empty context.
    """
    context1 = TemplateContext()
    context2 = TemplateContext()
    
    merged = context1.merge(context2)
    
    result = merged.to_dict()
    
    if result != {}:
        raise AssertionError(f"Expected empty dict, got {result}")
    
    return


# =============================================================================
# to_dict() Method Tests
# =============================================================================

def test_to_dict_returns_dictionary():
    """
        Test that to_dict() returns a dictionary.
    """
    context = TemplateContext({"title": "Home"})
    
    result = context.to_dict()
    
    if not isinstance(result, dict):
        raise AssertionError(f"Expected dict, got {type(result)}")
    
    return


def test_to_dict_returns_copy():
    """
        Test that to_dict() returns a copy, not the internal dict.
    """
    context = TemplateContext({"title": "Home"})
    
    result = context.to_dict()
    
    # Modify the returned dict
    result["title"] = "Modified"
    
    # Context should not be affected
    if context["title"] != "Home":
        raise AssertionError("Context should not be affected by changes to to_dict result")
    
    return


def test_to_dict_contains_all_keys():
    """
        Test that to_dict() contains all context keys.
    """
    initial = {"title": "Home", "count": 42, "active": True}
    context = TemplateContext(initial)
    
    result = context.to_dict()
    
    if result != initial:
        raise AssertionError(f"Expected {initial}, got {result}")
    
    return


def test_to_dict_on_empty_context():
    """
        Test that to_dict() returns empty dict for empty context.
    """
    context = TemplateContext()
    
    result = context.to_dict()
    
    if result != {}:
        raise AssertionError(f"Expected empty dict, got {result}")
    
    return


# =============================================================================
# Edge Cases
# =============================================================================

def test_empty_string_key():
    """
        Test that context handles empty string as key.
    """
    context = TemplateContext()
    
    context[""] = "empty_key_value"
    
    if context[""] != "empty_key_value":
        raise AssertionError("Should handle empty string key")
    
    if "" not in context:
        raise AssertionError("Should find empty string key")
    
    return


def test_special_characters_in_key():
    """
        Test that context handles special characters in keys.
    """
    context = TemplateContext()
    
    context["key-with-dashes"] = "value1"
    context["key_with_underscores"] = "value2"
    context["key.with.dots"] = "value3"
    context["key with spaces"] = "value4"
    
    if context["key-with-dashes"] != "value1":
        raise AssertionError("Should handle dashes in key")
    
    if context["key_with_underscores"] != "value2":
        raise AssertionError("Should handle underscores in key")
    
    if context["key.with.dots"] != "value3":
        raise AssertionError("Should handle dots in key")
    
    if context["key with spaces"] != "value4":
        raise AssertionError("Should handle spaces in key")
    
    return


def test_callable_value():
    """
        Test that context can store callable values.
    """
    def my_function():
        return "called"
    
    context = TemplateContext()
    context["func"] = my_function
    
    retrieved = context["func"]
    
    if retrieved is not my_function:
        raise AssertionError("Should store callable by reference")
    
    if retrieved() != "called":
        raise AssertionError("Callable should be invocable")
    
    return


def test_class_instance_value():
    """
        Test that context can store class instances.
    """
    class User:
        def __init__(self, name):
            self.name = name
    
    user = User("Alice")
    context = TemplateContext()
    context["user"] = user
    
    retrieved = context["user"]
    
    if retrieved is not user:
        raise AssertionError("Should store instance by reference")
    
    if retrieved.name != "Alice":
        raise AssertionError("Instance attributes should be accessible")
    
    return


def test_large_context():
    """
        Test that context handles large number of keys.
    """
    initial = {f"key_{i}": f"value_{i}" for i in range(1000)}
    context = TemplateContext(initial)
    
    result = context.to_dict()
    
    if len(result) != 1000:
        raise AssertionError(f"Expected 1000 keys, got {len(result)}")
    
    if context["key_500"] != "value_500":
        raise AssertionError("Should retrieve correct value for key_500")
    
    return


def test_unicode_keys_and_values():
    """
        Test that context handles unicode keys and values.
    """
    context = TemplateContext()
    
    context["日本語"] = "Japanese"
    context["emoji"] = "🎉"
    context["mixed"] = "Hello 世界 🌍"
    
    if context["日本語"] != "Japanese":
        raise AssertionError("Should handle unicode key")
    
    if context["emoji"] != "🎉":
        raise AssertionError("Should handle emoji value")
    
    if context["mixed"] != "Hello 世界 🌍":
        raise AssertionError("Should handle mixed unicode value")
    
    return


def test_chained_operations():
    """
        Test that context supports chained operations.
    """
    context = TemplateContext({"a": 1})
    context["b"] = 2
    context.update({"c": 3})
    
    other = TemplateContext({"d": 4})
    merged = context.merge(other)
    
    result = merged.to_dict()
    expected = {"a": 1, "b": 2, "c": 3, "d": 4}
    
    if result != expected:
        raise AssertionError(f"Expected {expected}, got {result}")
    
    return


def test_nested_dict_modification():
    """
        Test that nested dict modifications affect context.
    """
    nested = {"inner": "value"}
    context = TemplateContext({"nested": nested})
    
    # Modify the nested dict through context
    context["nested"]["inner"] = "modified"
    
    # The change should be reflected
    if context["nested"]["inner"] != "modified":
        raise AssertionError("Nested dict modification should be reflected")
    
    return


def test_list_modification():
    """
        Test that list modifications affect context.
    """
    items = [1, 2, 3]
    context = TemplateContext({"items": items})
    
    # Modify the list through context
    context["items"].append(4)
    
    # The change should be reflected
    if context["items"] != [1, 2, 3, 4]:
        raise AssertionError("List modification should be reflected")
    
    return


# =============================================================================
# resolve() Method Tests - Nested Dictionary Access (Requirement 3.2)
# =============================================================================

def test_resolve_simple_key():
    """
        Test that resolve() returns value for a simple key.
    """
    context = TemplateContext({"title": "Home"})
    
    result = context.resolve("title")
    
    if result != "Home":
        raise AssertionError(f"Expected 'Home', got {result}")
    
    return


def test_resolve_nested_dict_one_level():
    """
        Test that resolve() handles one level of nested dictionary access.
    """
    context = TemplateContext({
        "user": {"name": "Alice"}
    })
    
    result = context.resolve("user.name")
    
    if result != "Alice":
        raise AssertionError(f"Expected 'Alice', got {result}")
    
    return


def test_resolve_nested_dict_two_levels():
    """
        Test that resolve() handles two levels of nested dictionary access.
    """
    context = TemplateContext({
        "user": {
            "profile": {
                "email": "alice@example.com"
            }
        }
    })
    
    result = context.resolve("user.profile.email")
    
    if result != "alice@example.com":
        raise AssertionError(f"Expected 'alice@example.com', got {result}")
    
    return


def test_resolve_nested_dict_three_levels():
    """
        Test that resolve() handles three levels of nested dictionary access.
    """
    context = TemplateContext({
        "config": {
            "database": {
                "connection": {
                    "host": "localhost"
                }
            }
        }
    })
    
    result = context.resolve("config.database.connection.host")
    
    if result != "localhost":
        raise AssertionError(f"Expected 'localhost', got {result}")
    
    return


def test_resolve_nested_dict_returns_dict():
    """
        Test that resolve() can return a nested dictionary.
    """
    context = TemplateContext({
        "user": {
            "profile": {"name": "Alice", "age": 30}
        }
    })
    
    result = context.resolve("user.profile")
    
    expected = {"name": "Alice", "age": 30}
    if result != expected:
        raise AssertionError(f"Expected {expected}, got {result}")
    
    return


def test_resolve_raises_keyerror_for_missing_key():
    """
        Test that resolve() raises KeyError for missing key.
    """
    context = TemplateContext({"title": "Home"})
    
    try:
        context.resolve("missing")
        raise AssertionError("Expected KeyError to be raised")
    except KeyError as err:
        if "missing" not in str(err):
            raise AssertionError(f"Error message should mention 'missing': {err}")
    
    return


def test_resolve_raises_keyerror_for_missing_nested_key():
    """
        Test that resolve() raises KeyError for missing nested key.
    """
    context = TemplateContext({
        "user": {"name": "Alice"}
    })
    
    try:
        context.resolve("user.email")
        raise AssertionError("Expected KeyError to be raised")
    except KeyError as err:
        if "email" not in str(err):
            raise AssertionError(f"Error message should mention 'email': {err}")
    
    return


def test_resolve_raises_keyerror_for_empty_path():
    """
        Test that resolve() raises KeyError for empty path.
    """
    context = TemplateContext({"title": "Home"})
    
    try:
        context.resolve("")
        raise AssertionError("Expected KeyError to be raised")
    except KeyError as err:
        if "Empty path" not in str(err):
            raise AssertionError(f"Error message should mention 'Empty path': {err}")
    
    return


# =============================================================================
# resolve() Method Tests - List/Sequence Iteration (Requirement 3.3)
# =============================================================================

def test_resolve_list_index_zero():
    """
        Test that resolve() handles list index 0.
    """
    context = TemplateContext({
        "items": ["first", "second", "third"]
    })
    
    result = context.resolve("items.0")
    
    if result != "first":
        raise AssertionError(f"Expected 'first', got {result}")
    
    return


def test_resolve_list_index_positive():
    """
        Test that resolve() handles positive list indices.
    """
    context = TemplateContext({
        "items": ["a", "b", "c", "d"]
    })
    
    if context.resolve("items.1") != "b":
        raise AssertionError("Index 1 should return 'b'")
    
    if context.resolve("items.2") != "c":
        raise AssertionError("Index 2 should return 'c'")
    
    if context.resolve("items.3") != "d":
        raise AssertionError("Index 3 should return 'd'")
    
    return


def test_resolve_list_index_negative():
    """
        Test that resolve() handles negative list indices.
    """
    context = TemplateContext({
        "items": ["first", "second", "third"]
    })
    
    result = context.resolve("items.-1")
    
    if result != "third":
        raise AssertionError(f"Expected 'third', got {result}")
    
    return


def test_resolve_tuple_index():
    """
        Test that resolve() handles tuple indexing.
    """
    context = TemplateContext({
        "coords": (10, 20, 30)
    })
    
    if context.resolve("coords.0") != 10:
        raise AssertionError("Index 0 should return 10")
    
    if context.resolve("coords.1") != 20:
        raise AssertionError("Index 1 should return 20")
    
    return


def test_resolve_nested_list_in_dict():
    """
        Test that resolve() handles lists nested in dictionaries.
    """
    context = TemplateContext({
        "user": {
            "emails": ["primary@example.com", "secondary@example.com"]
        }
    })
    
    result = context.resolve("user.emails.0")
    
    if result != "primary@example.com":
        raise AssertionError(f"Expected 'primary@example.com', got {result}")
    
    return


def test_resolve_dict_in_list():
    """
        Test that resolve() handles dictionaries nested in lists.
    """
    context = TemplateContext({
        "users": [
            {"name": "Alice"},
            {"name": "Bob"}
        ]
    })
    
    if context.resolve("users.0.name") != "Alice":
        raise AssertionError("Should resolve users.0.name to 'Alice'")
    
    if context.resolve("users.1.name") != "Bob":
        raise AssertionError("Should resolve users.1.name to 'Bob'")
    
    return


def test_resolve_list_index_out_of_range():
    """
        Test that resolve() raises KeyError for out of range index.
    """
    context = TemplateContext({
        "items": ["a", "b", "c"]
    })
    
    try:
        context.resolve("items.10")
        raise AssertionError("Expected KeyError to be raised")
    except KeyError as err:
        if "out of range" not in str(err).lower():
            raise AssertionError(f"Error message should mention 'out of range': {err}")
    
    return


def test_resolve_nested_lists():
    """
        Test that resolve() handles nested lists.
    """
    context = TemplateContext({
        "matrix": [
            [1, 2, 3],
            [4, 5, 6],
            [7, 8, 9]
        ]
    })
    
    if context.resolve("matrix.0.0") != 1:
        raise AssertionError("matrix.0.0 should be 1")
    
    if context.resolve("matrix.1.1") != 5:
        raise AssertionError("matrix.1.1 should be 5")
    
    if context.resolve("matrix.2.2") != 9:
        raise AssertionError("matrix.2.2 should be 9")
    
    return


# =============================================================================
# resolve() Method Tests - Callable Object Invocation (Requirement 3.4)
# =============================================================================

def test_resolve_callable_function():
    """
        Test that resolve() invokes callable functions.
    """
    def get_title():
        return "Home Page"
    
    context = TemplateContext({
        "get_title": get_title
    })
    
    result = context.resolve("get_title")
    
    if result != "Home Page":
        raise AssertionError(f"Expected 'Home Page', got {result}")
    
    return


def test_resolve_callable_lambda():
    """
        Test that resolve() invokes lambda functions.
    """
    context = TemplateContext({
        "get_count": lambda: 42
    })
    
    result = context.resolve("get_count")
    
    if result != 42:
        raise AssertionError(f"Expected 42, got {result}")
    
    return


def test_resolve_nested_callable():
    """
        Test that resolve() invokes callables in nested structures.
    """
    context = TemplateContext({
        "config": {
            "get_version": lambda: "1.0.0"
        }
    })
    
    result = context.resolve("config.get_version")
    
    if result != "1.0.0":
        raise AssertionError(f"Expected '1.0.0', got {result}")
    
    return


def test_resolve_callable_returning_dict():
    """
        Test that resolve() handles callables returning dictionaries.
    """
    def get_user():
        return {"name": "Alice", "age": 30}
    
    context = TemplateContext({
        "get_user": get_user
    })
    
    result = context.resolve("get_user")
    
    expected = {"name": "Alice", "age": 30}
    if result != expected:
        raise AssertionError(f"Expected {expected}, got {result}")
    
    return


def test_resolve_callable_returning_list():
    """
        Test that resolve() handles callables returning lists.
    """
    context = TemplateContext({
        "get_items": lambda: [1, 2, 3]
    })
    
    result = context.resolve("get_items")
    
    if result != [1, 2, 3]:
        raise AssertionError(f"Expected [1, 2, 3], got {result}")
    
    return


def test_resolve_does_not_invoke_class_types():
    """
        Test that resolve() does not invoke class types (only instances).
    """
    class MyClass:
        pass
    
    context = TemplateContext({
        "MyClass": MyClass
    })
    
    result = context.resolve("MyClass")
    
    if result is not MyClass:
        raise AssertionError("Should return class type without invoking")
    
    return


# =============================================================================
# resolve() Method Tests - Object Attribute Access (Requirement 3.9)
# =============================================================================

def test_resolve_object_attribute():
    """
        Test that resolve() accesses object attributes.
    """
    class User:
        def __init__(self, name):
            self.name = name
    
    user = User("Alice")
    context = TemplateContext({"user": user})
    
    result = context.resolve("user.name")
    
    if result != "Alice":
        raise AssertionError(f"Expected 'Alice', got {result}")
    
    return


def test_resolve_object_multiple_attributes():
    """
        Test that resolve() accesses multiple object attributes.
    """
    class User:
        def __init__(self, name, email, age):
            self.name = name
            self.email = email
            self.age = age
    
    user = User("Alice", "alice@example.com", 30)
    context = TemplateContext({"user": user})
    
    if context.resolve("user.name") != "Alice":
        raise AssertionError("Should resolve user.name")
    
    if context.resolve("user.email") != "alice@example.com":
        raise AssertionError("Should resolve user.email")
    
    if context.resolve("user.age") != 30:
        raise AssertionError("Should resolve user.age")
    
    return


def test_resolve_object_method():
    """
        Test that resolve() invokes object methods.
    """
    class User:
        def __init__(self, name):
            self._name = name
        
        def get_name(self):
            return self._name
    
    user = User("Alice")
    context = TemplateContext({"user": user})
    
    result = context.resolve("user.get_name")
    
    if result != "Alice":
        raise AssertionError(f"Expected 'Alice', got {result}")
    
    return


def test_resolve_nested_object_attributes():
    """
        Test that resolve() handles nested object attributes.
    """
    class Address:
        def __init__(self, city, country):
            self.city = city
            self.country = country
    
    class User:
        def __init__(self, name, address):
            self.name = name
            self.address = address
    
    address = Address("New York", "USA")
    user = User("Alice", address)
    context = TemplateContext({"user": user})
    
    if context.resolve("user.address.city") != "New York":
        raise AssertionError("Should resolve user.address.city")
    
    if context.resolve("user.address.country") != "USA":
        raise AssertionError("Should resolve user.address.country")
    
    return


def test_resolve_object_with_dict_attribute():
    """
        Test that resolve() handles objects with dict attributes.
    """
    class Config:
        def __init__(self):
            self.settings = {"debug": True, "timeout": 30}
    
    config = Config()
    context = TemplateContext({"config": config})
    
    if context.resolve("config.settings.debug") is not True:
        raise AssertionError("Should resolve config.settings.debug")
    
    if context.resolve("config.settings.timeout") != 30:
        raise AssertionError("Should resolve config.settings.timeout")
    
    return


def test_resolve_object_with_list_attribute():
    """
        Test that resolve() handles objects with list attributes.
    """
    class User:
        def __init__(self, name, roles):
            self.name = name
            self.roles = roles
    
    user = User("Alice", ["admin", "editor", "viewer"])
    context = TemplateContext({"user": user})
    
    if context.resolve("user.roles.0") != "admin":
        raise AssertionError("Should resolve user.roles.0")
    
    if context.resolve("user.roles.1") != "editor":
        raise AssertionError("Should resolve user.roles.1")
    
    return


def test_resolve_object_missing_attribute():
    """
        Test that resolve() raises KeyError for missing object attribute.
    """
    class User:
        def __init__(self, name):
            self.name = name
    
    user = User("Alice")
    context = TemplateContext({"user": user})
    
    try:
        context.resolve("user.email")
        raise AssertionError("Expected KeyError to be raised")
    except KeyError as err:
        if "email" not in str(err):
            raise AssertionError(f"Error message should mention 'email': {err}")
    
    return


def test_resolve_object_property():
    """
        Test that resolve() accesses object properties.
    """
    class User:
        def __init__(self, first_name, last_name):
            self._first_name = first_name
            self._last_name = last_name
        
        @property
        def full_name(self):
            return f"{self._first_name} {self._last_name}"
    
    user = User("Alice", "Smith")
    context = TemplateContext({"user": user})
    
    result = context.resolve("user.full_name")
    
    if result != "Alice Smith":
        raise AssertionError(f"Expected 'Alice Smith', got {result}")
    
    return


# =============================================================================
# resolve() Method Tests - Mixed Access Patterns
# =============================================================================

def test_resolve_mixed_dict_and_object():
    """
        Test that resolve() handles mixed dict and object access.
    """
    class User:
        def __init__(self, name):
            self.name = name
    
    context = TemplateContext({
        "data": {
            "user": User("Alice")
        }
    })
    
    result = context.resolve("data.user.name")
    
    if result != "Alice":
        raise AssertionError(f"Expected 'Alice', got {result}")
    
    return


def test_resolve_mixed_list_and_object():
    """
        Test that resolve() handles mixed list and object access.
    """
    class User:
        def __init__(self, name):
            self.name = name
    
    context = TemplateContext({
        "users": [User("Alice"), User("Bob")]
    })
    
    if context.resolve("users.0.name") != "Alice":
        raise AssertionError("Should resolve users.0.name")
    
    if context.resolve("users.1.name") != "Bob":
        raise AssertionError("Should resolve users.1.name")
    
    return


def test_resolve_complex_nested_structure():
    """
        Test that resolve() handles complex nested structures.
    """
    class Address:
        def __init__(self, city):
            self.city = city
    
    class User:
        def __init__(self, name, address):
            self.name = name
            self.address = address
    
    context = TemplateContext({
        "company": {
            "departments": [
                {
                    "name": "Engineering",
                    "lead": User("Alice", Address("New York"))
                },
                {
                    "name": "Marketing",
                    "lead": User("Bob", Address("Los Angeles"))
                }
            ]
        }
    })
    
    result = context.resolve("company.departments.0.lead.address.city")
    
    if result != "New York":
        raise AssertionError(f"Expected 'New York', got {result}")
    
    result = context.resolve("company.departments.1.lead.name")
    
    if result != "Bob":
        raise AssertionError(f"Expected 'Bob', got {result}")
    
    return


def test_resolve_callable_in_nested_structure():
    """
        Test that resolve() invokes callables in nested structures.
    """
    class User:
        def __init__(self, name):
            self._name = name
        
        def get_greeting(self):
            return f"Hello, {self._name}!"
    
    context = TemplateContext({
        "data": {
            "users": [User("Alice"), User("Bob")]
        }
    })
    
    result = context.resolve("data.users.0.get_greeting")
    
    if result != "Hello, Alice!":
        raise AssertionError(f"Expected 'Hello, Alice!', got {result}")
    
    return


# =============================================================================
# resolve() Method Tests - Edge Cases
# =============================================================================

def test_resolve_none_value():
    """
        Test that resolve() returns None values correctly.
    """
    context = TemplateContext({
        "nullable": None
    })
    
    result = context.resolve("nullable")
    
    if result is not None:
        raise AssertionError(f"Expected None, got {result}")
    
    return


def test_resolve_nested_none_value():
    """
        Test that resolve() returns nested None values correctly.
    """
    context = TemplateContext({
        "user": {"email": None}
    })
    
    result = context.resolve("user.email")
    
    if result is not None:
        raise AssertionError(f"Expected None, got {result}")
    
    return


def test_resolve_empty_list():
    """
        Test that resolve() handles empty list access.
    """
    context = TemplateContext({
        "items": []
    })
    
    try:
        context.resolve("items.0")
        raise AssertionError("Expected KeyError to be raised")
    except KeyError:
        pass
    
    return


def test_resolve_boolean_values():
    """
        Test that resolve() handles boolean values correctly.
    """
    context = TemplateContext({
        "flags": {
            "active": True,
            "disabled": False
        }
    })
    
    if context.resolve("flags.active") is not True:
        raise AssertionError("Should resolve flags.active to True")
    
    if context.resolve("flags.disabled") is not False:
        raise AssertionError("Should resolve flags.disabled to False")
    
    return


def test_resolve_numeric_values():
    """
        Test that resolve() handles numeric values correctly.
    """
    context = TemplateContext({
        "numbers": {
            "integer": 42,
            "float": 3.14,
            "negative": -10,
            "zero": 0
        }
    })
    
    if context.resolve("numbers.integer") != 42:
        raise AssertionError("Should resolve numbers.integer")
    
    if context.resolve("numbers.float") != 3.14:
        raise AssertionError("Should resolve numbers.float")
    
    if context.resolve("numbers.negative") != -10:
        raise AssertionError("Should resolve numbers.negative")
    
    if context.resolve("numbers.zero") != 0:
        raise AssertionError("Should resolve numbers.zero")
    
    return


def test_resolve_string_with_dots():
    """
        Test that resolve() handles string values containing dots.
    """
    context = TemplateContext({
        "domain": "example.com"
    })
    
    result = context.resolve("domain")
    
    if result != "example.com":
        raise AssertionError(f"Expected 'example.com', got {result}")
    
    return


def test_resolve_unicode_values():
    """
        Test that resolve() handles unicode values correctly.
    """
    context = TemplateContext({
        "messages": {
            "greeting": "こんにちは",
            "emoji": "🎉"
        }
    })
    
    if context.resolve("messages.greeting") != "こんにちは":
        raise AssertionError("Should resolve unicode greeting")
    
    if context.resolve("messages.emoji") != "🎉":
        raise AssertionError("Should resolve emoji")
    
    return


def test_resolve_dict_key_takes_precedence_over_attribute():
    """
        Test that dict key access takes precedence over attribute access.
    """
    # Create a dict subclass with an attribute
    class CustomDict(dict):
        @property
        def name(self):
            return "attribute_value"
    
    custom = CustomDict()
    custom["name"] = "dict_value"
    
    context = TemplateContext({"data": custom})
    
    result = context.resolve("data.name")
    
    # Dict key should take precedence
    if result != "dict_value":
        raise AssertionError(f"Expected 'dict_value', got {result}")
    
    return


# =============================================================================
# GlobalContext Tests
# =============================================================================

from ccai.webworks.templating.context import GlobalContext


def test_global_context_set_and_get():
    """
        Test that GlobalContext.set() stores a value and get() retrieves it.
    """
    GlobalContext.clear()

    GlobalContext.set("app_name", "TestApp")

    result = GlobalContext.get("app_name")
    if result != "TestApp":
        raise AssertionError(f"Expected 'TestApp', got {result!r}")

    GlobalContext.clear()
    return


def test_global_context_get_default():
    """
        Test that GlobalContext.get() returns the default for missing keys.
    """
    GlobalContext.clear()

    result = GlobalContext.get("missing_key", "fallback")
    if result != "fallback":
        raise AssertionError(f"Expected 'fallback', got {result!r}")

    result_none = GlobalContext.get("missing_key")
    if result_none is not None:
        raise AssertionError(f"Expected None, got {result_none!r}")

    return


def test_global_context_contains():
    """
        Test that GlobalContext.contains() checks for key existence.
    """
    GlobalContext.clear()

    GlobalContext.set("exists", True)

    if not GlobalContext.contains("exists"):
        raise AssertionError("Expected contains('exists') to be True")

    if GlobalContext.contains("does_not_exist"):
        raise AssertionError("Expected contains('does_not_exist') to be False")

    GlobalContext.clear()
    return


def test_global_context_remove():
    """
        Test that GlobalContext.remove() deletes a key.
    """
    GlobalContext.clear()

    GlobalContext.set("to_remove", "value")
    GlobalContext.remove("to_remove")

    if GlobalContext.contains("to_remove"):
        raise AssertionError("Key should have been removed")

    GlobalContext.clear()
    return


def test_global_context_remove_missing_key_raises():
    """
        Test that GlobalContext.remove() raises KeyError for missing keys.
    """
    GlobalContext.clear()

    try:
        GlobalContext.remove("nonexistent")
        raise AssertionError("Expected KeyError")
    except KeyError:
        pass

    return


def test_global_context_update():
    """
        Test that GlobalContext.update() adds multiple variables at once.
    """
    GlobalContext.clear()

    GlobalContext.update({"a": 1, "b": 2, "c": 3})

    if GlobalContext.get("a") != 1:
        raise AssertionError(f"Expected 1, got {GlobalContext.get('a')!r}")
    if GlobalContext.get("b") != 2:
        raise AssertionError(f"Expected 2, got {GlobalContext.get('b')!r}")
    if GlobalContext.get("c") != 3:
        raise AssertionError(f"Expected 3, got {GlobalContext.get('c')!r}")

    GlobalContext.clear()
    return


def test_global_context_update_overwrites():
    """
        Test that GlobalContext.update() overwrites existing keys.
    """
    GlobalContext.clear()

    GlobalContext.set("key", "old")
    GlobalContext.update({"key": "new"})

    result = GlobalContext.get("key")
    if result != "new":
        raise AssertionError(f"Expected 'new', got {result!r}")

    GlobalContext.clear()
    return


def test_global_context_to_dict():
    """
        Test that GlobalContext.to_dict() returns a copy of all globals.
    """
    GlobalContext.clear()

    GlobalContext.set("x", 10)
    GlobalContext.set("y", 20)

    result = GlobalContext.to_dict()

    if result != {"x": 10, "y": 20}:
        raise AssertionError(f"Expected {{'x': 10, 'y': 20}}, got {result!r}")

    # Verify it is a copy
    result["z"] = 30
    if GlobalContext.contains("z"):
        raise AssertionError("to_dict() should return a copy, not a reference")

    GlobalContext.clear()
    return


def test_global_context_clear():
    """
        Test that GlobalContext.clear() removes all variables.
    """
    GlobalContext.clear()

    GlobalContext.set("a", 1)
    GlobalContext.set("b", 2)
    GlobalContext.clear()

    result = GlobalContext.to_dict()
    if result != {}:
        raise AssertionError(f"Expected empty dict, got {result!r}")

    return


def test_global_context_set_overwrites():
    """
        Test that setting the same key twice overwrites the first value.
    """
    GlobalContext.clear()

    GlobalContext.set("key", "first")
    GlobalContext.set("key", "second")

    result = GlobalContext.get("key")
    if result != "second":
        raise AssertionError(f"Expected 'second', got {result!r}")

    GlobalContext.clear()
    return


def test_global_context_various_value_types():
    """
        Test that GlobalContext supports various value types.
    """
    GlobalContext.clear()

    GlobalContext.set("string", "hello")
    GlobalContext.set("number", 42)
    GlobalContext.set("float", 3.14)
    GlobalContext.set("bool", True)
    GlobalContext.set("none", None)
    GlobalContext.set("list", [1, 2, 3])
    GlobalContext.set("dict", {"nested": "value"})

    if GlobalContext.get("string") != "hello":
        raise AssertionError("String value mismatch")
    if GlobalContext.get("number") != 42:
        raise AssertionError("Number value mismatch")
    if GlobalContext.get("float") != 3.14:
        raise AssertionError("Float value mismatch")
    if GlobalContext.get("bool") is not True:
        raise AssertionError("Bool value mismatch")
    if GlobalContext.get("none") is not None:
        raise AssertionError("None value mismatch")
    if GlobalContext.get("list") != [1, 2, 3]:
        raise AssertionError("List value mismatch")
    if GlobalContext.get("dict") != {"nested": "value"}:
        raise AssertionError("Dict value mismatch")

    GlobalContext.clear()
    return


# =============================================================================
# RequestContext Tests
# =============================================================================

from ccai.webworks.templating.context import RequestContext


def test_request_context_init_empty():
    """
        Test that RequestContext can be created with no arguments.
    """
    GlobalContext.clear()

    ctx = RequestContext()

    result = ctx.to_dict()
    if result != {}:
        raise AssertionError(f"Expected empty dict, got {result!r}")

    return


def test_request_context_init_with_data():
    """
        Test that RequestContext can be created with initial data.
    """
    GlobalContext.clear()

    ctx = RequestContext({"user": "Alice", "csrf": "token123"})

    if ctx["user"] != "Alice":
        raise AssertionError(f"Expected 'Alice', got {ctx['user']!r}")
    if ctx["csrf"] != "token123":
        raise AssertionError(f"Expected 'token123', got {ctx['csrf']!r}")

    return


def test_request_context_inherits_template_context():
    """
        Test that RequestContext supports all TemplateContext operations.
    """
    GlobalContext.clear()

    ctx = RequestContext({"a": 1})
    ctx["b"] = 2
    ctx.update({"c": 3})

    if "a" not in ctx:
        raise AssertionError("Expected 'a' in context")
    if ctx.get("b") != 2:
        raise AssertionError(f"Expected 2, got {ctx.get('b')!r}")
    if ctx.get("c") != 3:
        raise AssertionError(f"Expected 3, got {ctx.get('c')!r}")

    return


def test_request_context_build_context_with_globals():
    """
        Test that build_context() merges global variables with request variables.
    """
    GlobalContext.clear()

    GlobalContext.set("app_name", "TestApp")
    GlobalContext.set("version", "1.0")

    ctx = RequestContext({"user": "Alice"})
    full = ctx.build_context()

    result = full.to_dict()
    if result.get("app_name") != "TestApp":
        raise AssertionError(f"Expected 'TestApp', got {result.get('app_name')!r}")
    if result.get("version") != "1.0":
        raise AssertionError(f"Expected '1.0', got {result.get('version')!r}")
    if result.get("user") != "Alice":
        raise AssertionError(f"Expected 'Alice', got {result.get('user')!r}")

    GlobalContext.clear()
    return


def test_request_context_build_context_request_overrides_globals():
    """
        Test that request-scoped variables override global variables.
    """
    GlobalContext.clear()

    GlobalContext.set("title", "Global Title")
    ctx = RequestContext({"title": "Request Title"})
    full = ctx.build_context()

    result = full.to_dict()
    if result["title"] != "Request Title":
        raise AssertionError(f"Expected 'Request Title', got {result['title']!r}")

    GlobalContext.clear()
    return


def test_request_context_build_context_extra_overrides_all():
    """
        Test that extra variables override both global and request variables.
    """
    GlobalContext.clear()

    GlobalContext.set("key", "global")
    ctx = RequestContext({"key": "request"})
    full = ctx.build_context(extra={"key": "extra"})

    result = full.to_dict()
    if result["key"] != "extra":
        raise AssertionError(f"Expected 'extra', got {result['key']!r}")

    GlobalContext.clear()
    return


def test_request_context_build_context_without_globals():
    """
        Test that build_context() excludes globals when include_globals is False.
    """
    GlobalContext.clear()

    GlobalContext.set("app_name", "TestApp")
    ctx = RequestContext({"user": "Alice"}, include_globals=False)
    full = ctx.build_context()

    result = full.to_dict()
    if "app_name" in result:
        raise AssertionError("Global variable should not be included")
    if result.get("user") != "Alice":
        raise AssertionError(f"Expected 'Alice', got {result.get('user')!r}")

    GlobalContext.clear()
    return


def test_request_context_build_context_with_extra():
    """
        Test that build_context() merges extra variables.
    """
    GlobalContext.clear()

    ctx = RequestContext({"a": 1})
    full = ctx.build_context(extra={"b": 2, "c": 3})

    result = full.to_dict()
    if result.get("a") != 1:
        raise AssertionError(f"Expected 1, got {result.get('a')!r}")
    if result.get("b") != 2:
        raise AssertionError(f"Expected 2, got {result.get('b')!r}")
    if result.get("c") != 3:
        raise AssertionError(f"Expected 3, got {result.get('c')!r}")

    return


def test_request_context_build_context_returns_template_context():
    """
        Test that build_context() returns a TemplateContext instance.
    """
    GlobalContext.clear()

    ctx = RequestContext({"x": 1})
    full = ctx.build_context()

    if not isinstance(full, TemplateContext):
        raise AssertionError(f"Expected TemplateContext, got {type(full).__name__}")

    return


def test_request_context_build_context_no_extra():
    """
        Test that build_context() works with no extra argument.
    """
    GlobalContext.clear()

    ctx = RequestContext({"user": "Bob"})
    full = ctx.build_context()

    result = full.to_dict()
    if result.get("user") != "Bob":
        raise AssertionError(f"Expected 'Bob', got {result.get('user')!r}")

    return


def test_request_context_build_context_empty():
    """
        Test that build_context() works with empty request context and no globals.
    """
    GlobalContext.clear()

    ctx = RequestContext()
    full = ctx.build_context()

    result = full.to_dict()
    if result != {}:
        raise AssertionError(f"Expected empty dict, got {result!r}")

    return


# =============================================================================
# ContextProcessorRegistry Tests
# =============================================================================

from ccai.webworks.templating.context import ContextProcessorRegistry


def test_context_processor_registry_init():
    """
        Test that ContextProcessorRegistry starts with no processors.
    """
    registry = ContextProcessorRegistry()

    if registry.count != 0:
        raise AssertionError(f"Expected 0 processors, got {registry.count}")

    return


def test_context_processor_registry_register():
    """
        Test that register() adds a processor.
    """
    registry = ContextProcessorRegistry()

    def my_processor(ctx):
        return {"added": True}

    registry.register(my_processor)

    if registry.count != 1:
        raise AssertionError(f"Expected 1 processor, got {registry.count}")

    return


def test_context_processor_registry_process_single():
    """
        Test that process() invokes a single processor and returns its result.
    """
    registry = ContextProcessorRegistry()

    def add_year(ctx):
        return {"year": 2024}

    registry.register(add_year)

    result = registry.process({"title": "Home"})
    if result != {"year": 2024}:
        raise AssertionError(f"Expected {{'year': 2024}}, got {result!r}")

    return


def test_context_processor_registry_process_multiple():
    """
        Test that process() invokes multiple processors and merges results.
    """
    registry = ContextProcessorRegistry()

    registry.register(lambda ctx: {"a": 1})
    registry.register(lambda ctx: {"b": 2})

    result = registry.process({})
    if result != {"a": 1, "b": 2}:
        raise AssertionError(f"Expected {{'a': 1, 'b': 2}}, got {result!r}")

    return


def test_context_processor_registry_process_later_overrides():
    """
        Test that later processors override earlier ones for conflicting keys.
    """
    registry = ContextProcessorRegistry()

    registry.register(lambda ctx: {"key": "first"})
    registry.register(lambda ctx: {"key": "second"})

    result = registry.process({})
    if result["key"] != "second":
        raise AssertionError(f"Expected 'second', got {result['key']!r}")

    return


def test_context_processor_registry_process_receives_context():
    """
        Test that processors receive the current context dictionary.
    """
    registry = ContextProcessorRegistry()

    def greeting_processor(ctx):
        name = ctx.get("user", "Guest")
        return {"greeting": f"Hello, {name}!"}

    registry.register(greeting_processor)

    result = registry.process({"user": "Alice"})
    if result["greeting"] != "Hello, Alice!":
        raise AssertionError(f"Expected 'Hello, Alice!', got {result['greeting']!r}")

    return


def test_context_processor_registry_process_empty():
    """
        Test that process() returns empty dict when no processors are registered.
    """
    registry = ContextProcessorRegistry()

    result = registry.process({"title": "Home"})
    if result != {}:
        raise AssertionError(f"Expected empty dict, got {result!r}")

    return


def test_context_processor_registry_process_none_return():
    """
        Test that process() handles processors that return None gracefully.
    """
    registry = ContextProcessorRegistry()

    def returns_none(ctx):
        return None

    def returns_data(ctx):
        return {"valid": True}

    registry.register(returns_none)
    registry.register(returns_data)

    result = registry.process({})
    if result != {"valid": True}:
        raise AssertionError(f"Expected {{'valid': True}}, got {result!r}")

    return


def test_context_processor_registry_unregister():
    """
        Test that unregister() removes a processor.
    """
    registry = ContextProcessorRegistry()

    def my_processor(ctx):
        return {"added": True}

    registry.register(my_processor)
    registry.unregister(my_processor)

    if registry.count != 0:
        raise AssertionError(f"Expected 0 processors, got {registry.count}")

    result = registry.process({})
    if result != {}:
        raise AssertionError(f"Expected empty dict, got {result!r}")

    return


def test_context_processor_registry_unregister_missing_raises():
    """
        Test that unregister() raises ValueError for unregistered processors.
    """
    registry = ContextProcessorRegistry()

    def not_registered(ctx):
        return {}

    try:
        registry.unregister(not_registered)
        raise AssertionError("Expected ValueError")
    except ValueError:
        pass

    return


def test_context_processor_registry_clear():
    """
        Test that clear() removes all processors.
    """
    registry = ContextProcessorRegistry()

    registry.register(lambda ctx: {"a": 1})
    registry.register(lambda ctx: {"b": 2})
    registry.clear()

    if registry.count != 0:
        raise AssertionError(f"Expected 0 processors, got {registry.count}")

    result = registry.process({})
    if result != {}:
        raise AssertionError(f"Expected empty dict, got {result!r}")

    return


def test_context_processor_registry_count():
    """
        Test that count property reflects the number of registered processors.
    """
    registry = ContextProcessorRegistry()

    if registry.count != 0:
        raise AssertionError(f"Expected 0, got {registry.count}")

    registry.register(lambda ctx: {})
    if registry.count != 1:
        raise AssertionError(f"Expected 1, got {registry.count}")

    registry.register(lambda ctx: {})
    if registry.count != 2:
        raise AssertionError(f"Expected 2, got {registry.count}")

    registry.clear()
    if registry.count != 0:
        raise AssertionError(f"Expected 0 after clear, got {registry.count}")

    return

# =============================================================================
# Undefined Variable Handling Tests
# =============================================================================

def test_undefined_behavior_default_raises_keyerror():
    """
        Test that the default undefined_behavior (None) raises KeyError
        for missing keys, preserving backward compatibility.
    """
    context = TemplateContext({"name": "Alice"})

    try:
        context.resolve("missing")
        raise AssertionError("Expected KeyError to be raised")
    except KeyError:
        pass

    return


def test_undefined_behavior_silent_returns_empty_string():
    """
        Test that silent mode returns an empty string for missing keys.
    """
    context = TemplateContext({"name": "Alice"}, undefined_behavior="silent")

    result = context.resolve("missing")

    if result != "":
        raise AssertionError(f"Expected empty string, got {result!r}")

    return


def test_undefined_behavior_silent_nested_missing():
    """
        Test that silent mode returns an empty string for missing nested keys.
    """
    context = TemplateContext(
        {"user": {"name": "Alice"}},
        undefined_behavior="silent"
    )

    result = context.resolve("user.email")

    if result != "":
        raise AssertionError(f"Expected empty string, got {result!r}")

    return


def test_undefined_behavior_silent_top_level_missing():
    """
        Test that silent mode returns an empty string when the top-level
        key is missing in a nested path.
    """
    context = TemplateContext(
        {"name": "Alice"},
        undefined_behavior="silent"
    )

    result = context.resolve("user.name")

    if result != "":
        raise AssertionError(f"Expected empty string, got {result!r}")

    return


def test_undefined_behavior_strict_raises_undefined_variable_error():
    """
        Test that strict mode raises UndefinedVariableError for missing keys.
    """
    context = TemplateContext({"name": "Alice"}, undefined_behavior="strict")

    try:
        context.resolve("missing")
        raise AssertionError("Expected UndefinedVariableError to be raised")
    except UndefinedVariableError as exc:
        if exc.variable_name != "missing":
            raise AssertionError(
                f"Expected variable_name 'missing', got {exc.variable_name!r}"
            )

    return


def test_undefined_behavior_strict_nested_missing():
    """
        Test that strict mode raises UndefinedVariableError for missing
        nested keys.
    """
    context = TemplateContext(
        {"user": {"name": "Alice"}},
        undefined_behavior="strict"
    )

    try:
        context.resolve("user.email")
        raise AssertionError("Expected UndefinedVariableError to be raised")
    except UndefinedVariableError as exc:
        if exc.variable_name != "user.email":
            raise AssertionError(
                f"Expected variable_name 'user.email', got {exc.variable_name!r}"
            )

    return


def test_undefined_behavior_strict_top_level_missing():
    """
        Test that strict mode raises UndefinedVariableError when the
        top-level key is missing in a nested path.
    """
    context = TemplateContext(
        {"name": "Alice"},
        undefined_behavior="strict"
    )

    try:
        context.resolve("user.name")
        raise AssertionError("Expected UndefinedVariableError to be raised")
    except UndefinedVariableError as exc:
        if exc.variable_name != "user.name":
            raise AssertionError(
                f"Expected variable_name 'user.name', got {exc.variable_name!r}"
            )

    return


def test_undefined_behavior_silent_existing_key_resolves():
    """
        Test that silent mode still resolves existing keys normally.
    """
    context = TemplateContext(
        {"user": {"name": "Alice"}},
        undefined_behavior="silent"
    )

    result = context.resolve("user.name")

    if result != "Alice":
        raise AssertionError(f"Expected 'Alice', got {result!r}")

    return


def test_undefined_behavior_strict_existing_key_resolves():
    """
        Test that strict mode still resolves existing keys normally.
    """
    context = TemplateContext(
        {"user": {"name": "Alice"}},
        undefined_behavior="strict"
    )

    result = context.resolve("user.name")

    if result != "Alice":
        raise AssertionError(f"Expected 'Alice', got {result!r}")

    return


def test_undefined_behavior_configurable():
    """
        Test that undefined_behavior can be configured per context instance.
    """
    silent_ctx = TemplateContext({"a": 1}, undefined_behavior="silent")
    strict_ctx = TemplateContext({"a": 1}, undefined_behavior="strict")
    default_ctx = TemplateContext({"a": 1})

    # Silent returns empty string
    result = silent_ctx.resolve("missing")
    if result != "":
        raise AssertionError(f"Expected empty string for silent, got {result!r}")

    # Strict raises UndefinedVariableError
    try:
        strict_ctx.resolve("missing")
        raise AssertionError("Expected UndefinedVariableError for strict")
    except UndefinedVariableError:
        pass

    # Default raises KeyError
    try:
        default_ctx.resolve("missing")
        raise AssertionError("Expected KeyError for default")
    except KeyError:
        pass

    return


def test_undefined_behavior_strict_error_message():
    """
        Test that UndefinedVariableError contains a descriptive message.
    """
    context = TemplateContext(undefined_behavior="strict")

    try:
        context.resolve("nonexistent")
        raise AssertionError("Expected UndefinedVariableError to be raised")
    except UndefinedVariableError as exc:
        message = str(exc)
        if "nonexistent" not in message:
            raise AssertionError(
                f"Expected 'nonexistent' in error message, got: {message}"
            )

    return


def test_undefined_behavior_silent_empty_path_still_raises():
    """
        Test that empty path still raises KeyError even in silent mode,
        since empty path is an invalid input, not a missing variable.
    """
    context = TemplateContext({"a": 1}, undefined_behavior="silent")

    try:
        context.resolve("")
        raise AssertionError("Expected KeyError for empty path")
    except KeyError:
        pass

    return


# =============================================================================
# Property-Based Tests
# =============================================================================

import random
import string


def _generate_random_key(min_length: int = 1, max_length: int = 8) -> str:
    """
        Generate a random valid dictionary key for property testing.

        Keys are lowercase alphabetic strings to avoid conflicts with
        numeric segments (which are interpreted as list indices).

        :param min_length: Minimum key length.
        :param max_length: Maximum key length.

        :returns: Random alphabetic string suitable as a dictionary key.
    """
    length = random.randint(min_length, max_length)
    return "".join(random.choice(string.ascii_lowercase) for _ in range(length))


def _generate_leaf_value() -> object:
    """
        Generate a random leaf value for nested dictionaries.

        :returns: A random value of type int, float, str, bool, or None.
    """
    choice = random.randint(0, 4)
    if choice == 0:
        return random.randint(-1000, 1000)
    elif choice == 1:
        return random.uniform(-1000.0, 1000.0)
    elif choice == 2:
        length = random.randint(0, 20)
        return "".join(random.choice(string.ascii_letters + string.digits + " ") for _ in range(length))
    elif choice == 3:
        return random.choice([True, False])
    else:
        return None


def _generate_nested_dict(max_depth: int = 4, current_depth: int = 0):
    """
        Generate a random nested dictionary structure along with a list of
        valid (path, expected_value) pairs.

        :param max_depth: Maximum nesting depth.
        :param current_depth: Current depth in the recursion.

        :returns: A tuple of (dict, list_of_(path, value)_pairs).
    """
    result = {}
    paths = []

    num_keys = random.randint(1, 4)

    for _ in range(num_keys):
        key = _generate_random_key()

        # Avoid duplicate keys in the same dict
        while key in result:
            key = _generate_random_key()

        if current_depth < max_depth and random.random() < 0.5:
            # Create a nested dict
            child_dict, child_paths = _generate_nested_dict(max_depth, current_depth + 1)
            result[key] = child_dict

            # Prepend this key to all child paths
            for child_path, child_value in child_paths:
                paths.append((f"{key}.{child_path}", child_value))

            # Also add the dict itself as a valid path
            paths.append((key, child_dict))
        else:
            # Create a leaf value
            value = _generate_leaf_value()
            result[key] = value
            paths.append((key, value))

    return result, paths


def _generate_invalid_path(existing_keys: set) -> str:
    """
        Generate a dot-notation path that does not exist in the context.

        :param existing_keys: Set of top-level keys to avoid.

        :returns: A path string guaranteed not to resolve.
    """
    # Generate a key that is not in the existing top-level keys
    key = _generate_random_key(min_length=3, max_length=10)
    while key in existing_keys:
        key = _generate_random_key(min_length=3, max_length=10)

    # Optionally add nested segments
    depth = random.randint(0, 3)
    segments = [key]
    for _ in range(depth):
        segments.append(_generate_random_key())

    return ".".join(segments)


def test_property_context_variable_access():
    """
        Property test for context variable access.

        **Property 4: Context Variable Access**

        *For any* context dictionary with nested structures, template expressions
        using dot notation SHALL correctly access nested values, and missing keys
        SHALL return empty string (in silent mode) or raise UndefinedVariableError
        (in strict mode).

        **Validates: Requirements 3.2, 3.7, 3.8**

        This property test verifies that:
        1. For randomly generated nested dictionaries, resolve() with dot notation
           correctly accesses nested values.
        2. For missing keys in silent mode (undefined_behavior="silent"),
           resolve() returns "".
        3. For missing keys in strict mode (undefined_behavior="strict"),
           resolve() raises UndefinedVariableError.

        Test strategy:
        - Generate random nested dictionary structures (varying depth, key names,
          value types)
        - Construct valid dot-notation paths from the generated structure
        - Verify resolve() returns the correct value for valid paths
        - Generate invalid paths and verify silent mode returns "" and strict mode
          raises UndefinedVariableError
        - Run at least 100 iterations
    """
    iterations = 100

    for iteration in range(iterations):
        # Generate a random nested dictionary with known valid paths
        nested_dict, valid_paths = _generate_nested_dict()

        if not valid_paths:
            continue

        # --- Test 1: Valid paths resolve correctly (default behavior) ---
        context_default = TemplateContext(nested_dict)

        for path, expected_value in valid_paths:
            resolved = context_default.resolve(path)

            if isinstance(expected_value, float):
                # Float comparison with tolerance
                if abs(resolved - expected_value) > 1e-9:
                    raise AssertionError(
                        f"Iteration {iteration}: resolve('{path}') returned "
                        f"{resolved!r}, expected {expected_value!r}"
                    )
            else:
                if resolved != expected_value:
                    raise AssertionError(
                        f"Iteration {iteration}: resolve('{path}') returned "
                        f"{resolved!r}, expected {expected_value!r}"
                    )

        # --- Test 2: Invalid paths in silent mode return "" ---
        context_silent = TemplateContext(nested_dict, undefined_behavior="silent")
        top_level_keys = set(nested_dict.keys())
        invalid_path = _generate_invalid_path(top_level_keys)

        result = context_silent.resolve(invalid_path)
        if result != "":
            raise AssertionError(
                f"Iteration {iteration}: silent mode resolve('{invalid_path}') "
                f"returned {result!r}, expected empty string"
            )

        # --- Test 3: Invalid paths in strict mode raise UndefinedVariableError ---
        context_strict = TemplateContext(nested_dict, undefined_behavior="strict")

        try:
            context_strict.resolve(invalid_path)
            raise AssertionError(
                f"Iteration {iteration}: strict mode resolve('{invalid_path}') "
                f"did not raise UndefinedVariableError"
            )
        except UndefinedVariableError:
            pass

    return
