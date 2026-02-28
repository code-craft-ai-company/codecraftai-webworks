"""
    Tests for the Doc dataclass.
    
    This module contains unit tests for the documentation metadata dataclass.
"""

from automojo.webworks.endpoints.doc import Doc


# =============================================================================
# Unit Tests for Doc - Basic Construction
# =============================================================================

def test_doc_default_values():
    """
        Test that Doc has correct default values.
    """
    doc = Doc()
    
    if doc.summary is not None:
        errmsg = f"Expected summary to be None, got '{doc.summary}'"
        raise AssertionError(errmsg)
    
    if doc.description is not None:
        errmsg = f"Expected description to be None, got '{doc.description}'"
        raise AssertionError(errmsg)
    
    if doc.deprecated is not False:
        errmsg = f"Expected deprecated to be False, got {doc.deprecated}"
        raise AssertionError(errmsg)
    
    if doc.external_docs is not None:
        errmsg = f"Expected external_docs to be None, got '{doc.external_docs}'"
        raise AssertionError(errmsg)
    
    return


def test_doc_with_summary():
    """
        Test that Doc can be created with a summary.
    """
    doc = Doc(summary="Get user status")
    
    if doc.summary != "Get user status":
        errmsg = f"Expected summary 'Get user status', got '{doc.summary}'"
        raise AssertionError(errmsg)
    
    return


def test_doc_with_description():
    """
        Test that Doc can be created with a description.
    """
    doc = Doc(description="Returns the current status of the user account.")
    
    if doc.description != "Returns the current status of the user account.":
        errmsg = f"Expected description to match, got '{doc.description}'"
        raise AssertionError(errmsg)
    
    return


def test_doc_with_deprecated_true():
    """
        Test that Doc can be created with deprecated=True.
    """
    doc = Doc(deprecated=True)
    
    if doc.deprecated is not True:
        errmsg = f"Expected deprecated to be True, got {doc.deprecated}"
        raise AssertionError(errmsg)
    
    return


def test_doc_with_external_docs():
    """
        Test that Doc can be created with external_docs URL.
    """
    doc = Doc(external_docs="https://docs.example.com/api/users")
    
    if doc.external_docs != "https://docs.example.com/api/users":
        errmsg = f"Expected external_docs URL to match, got '{doc.external_docs}'"
        raise AssertionError(errmsg)
    
    return


def test_doc_with_all_fields():
    """
        Test that Doc can be created with all fields populated.
    """
    doc = Doc(
        summary="Get user status",
        description="Returns the current status of the user account.",
        deprecated=True,
        external_docs="https://docs.example.com/api/users"
    )
    
    if doc.summary != "Get user status":
        errmsg = f"Expected summary 'Get user status', got '{doc.summary}'"
        raise AssertionError(errmsg)
    
    if doc.description != "Returns the current status of the user account.":
        errmsg = f"Expected description to match, got '{doc.description}'"
        raise AssertionError(errmsg)
    
    if doc.deprecated is not True:
        errmsg = f"Expected deprecated to be True, got {doc.deprecated}"
        raise AssertionError(errmsg)
    
    if doc.external_docs != "https://docs.example.com/api/users":
        errmsg = f"Expected external_docs URL to match, got '{doc.external_docs}'"
        raise AssertionError(errmsg)
    
    return


def test_doc_is_dataclass():
    """
        Test that Doc is a proper dataclass with equality.
    """
    doc1 = Doc(summary="Test", description="Test description")
    doc2 = Doc(summary="Test", description="Test description")
    
    if doc1 != doc2:
        errmsg = "Expected equal Doc instances to be equal"
        raise AssertionError(errmsg)
    
    return


def test_doc_inequality():
    """
        Test that different Doc instances are not equal.
    """
    doc1 = Doc(summary="Test 1")
    doc2 = Doc(summary="Test 2")
    
    if doc1 == doc2:
        errmsg = "Expected different Doc instances to not be equal"
        raise AssertionError(errmsg)
    
    return
