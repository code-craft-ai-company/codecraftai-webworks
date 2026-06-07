"""
    Tests for the routing exceptions module.
    
    This module tests the HTTPException base class and its standard subclasses
    (NotFound, BadRequest, Unauthorized, Forbidden, MethodNotAllowed).
"""

from ccai.webworks.routing.exceptions import (
    HTTPException,
    NotFound,
    BadRequest,
    Unauthorized,
    Forbidden,
    MethodNotAllowed,
)


# =============================================================================
# HTTPException Tests
# =============================================================================

def test_httpexception_constructor():
    """
        Test that HTTPException constructor creates instance with status_code.
    """
    exc = HTTPException(404)
    
    if exc.status_code != 404:
        raise AssertionError(f"Expected status_code 404, got {exc.status_code}")
    
    return


def test_httpexception_with_detail():
    """
        Test that HTTPException accepts detail message.
    """
    exc = HTTPException(400, detail="Invalid input")
    
    if exc.detail != "Invalid input":
        raise AssertionError(f"Expected detail 'Invalid input', got {exc.detail}")
    
    return


def test_httpexception_with_headers():
    """
        Test that HTTPException accepts headers dict.
    """
    headers = {"X-Custom": "value", "Retry-After": "60"}
    exc = HTTPException(503, detail="Service unavailable", headers=headers)
    
    if exc.headers != headers:
        raise AssertionError(f"Expected headers {headers}, got {exc.headers}")
    
    return


def test_httpexception_default_headers():
    """
        Test that HTTPException has empty headers by default.
    """
    exc = HTTPException(500)
    
    if exc.headers != {}:
        raise AssertionError(f"Expected empty headers, got {exc.headers}")
    
    return


def test_httpexception_message_includes_status():
    """
        Test that HTTPException message includes status code.
    """
    exc = HTTPException(404)
    message = str(exc)
    
    if "404" not in message:
        raise AssertionError(f"Expected '404' in message, got '{message}'")
    
    return


def test_httpexception_message_includes_phrase():
    """
        Test that HTTPException message includes status phrase.
    """
    exc = HTTPException(404)
    message = str(exc)
    
    if "Not Found" not in message:
        raise AssertionError(f"Expected 'Not Found' in message, got '{message}'")
    
    return


def test_httpexception_message_includes_detail():
    """
        Test that HTTPException message includes detail when provided.
    """
    exc = HTTPException(400, detail="Missing field")
    message = str(exc)
    
    if "Missing field" not in message:
        raise AssertionError(f"Expected 'Missing field' in message, got '{message}'")
    
    return


def test_httpexception_is_exception():
    """
        Test that HTTPException is an Exception subclass.
    """
    exc = HTTPException(500)
    
    if not isinstance(exc, Exception):
        raise AssertionError("HTTPException should be an Exception subclass")
    
    return


# =============================================================================
# NotFound Tests
# =============================================================================

def test_notfound_status_code():
    """
        Test that NotFound has status code 404.
    """
    exc = NotFound()
    
    if exc.status_code != 404:
        raise AssertionError(f"Expected status_code 404, got {exc.status_code}")
    
    return


def test_notfound_default_detail():
    """
        Test that NotFound has default detail message.
    """
    exc = NotFound()
    
    if exc.detail != "Not Found":
        raise AssertionError(f"Expected detail 'Not Found', got {exc.detail}")
    
    return


def test_notfound_custom_detail():
    """
        Test that NotFound accepts custom detail message.
    """
    exc = NotFound("User with ID 123 not found")
    
    if exc.detail != "User with ID 123 not found":
        raise AssertionError(f"Expected custom detail, got {exc.detail}")
    
    return


def test_notfound_is_httpexception():
    """
        Test that NotFound is an HTTPException subclass.
    """
    exc = NotFound()
    
    if not isinstance(exc, HTTPException):
        raise AssertionError("NotFound should be an HTTPException subclass")
    
    return


# =============================================================================
# BadRequest Tests
# =============================================================================

def test_badrequest_status_code():
    """
        Test that BadRequest has status code 400.
    """
    exc = BadRequest()
    
    if exc.status_code != 400:
        raise AssertionError(f"Expected status_code 400, got {exc.status_code}")
    
    return


def test_badrequest_default_detail():
    """
        Test that BadRequest has default detail message.
    """
    exc = BadRequest()
    
    if exc.detail != "Bad Request":
        raise AssertionError(f"Expected detail 'Bad Request', got {exc.detail}")
    
    return


def test_badrequest_custom_detail():
    """
        Test that BadRequest accepts custom detail message.
    """
    exc = BadRequest("Missing required field 'email'")
    
    if exc.detail != "Missing required field 'email'":
        raise AssertionError(f"Expected custom detail, got {exc.detail}")
    
    return


def test_badrequest_is_httpexception():
    """
        Test that BadRequest is an HTTPException subclass.
    """
    exc = BadRequest()
    
    if not isinstance(exc, HTTPException):
        raise AssertionError("BadRequest should be an HTTPException subclass")
    
    return


# =============================================================================
# Unauthorized Tests
# =============================================================================

def test_unauthorized_status_code():
    """
        Test that Unauthorized has status code 401.
    """
    exc = Unauthorized()
    
    if exc.status_code != 401:
        raise AssertionError(f"Expected status_code 401, got {exc.status_code}")
    
    return


def test_unauthorized_default_detail():
    """
        Test that Unauthorized has default detail message.
    """
    exc = Unauthorized()
    
    if exc.detail != "Unauthorized":
        raise AssertionError(f"Expected detail 'Unauthorized', got {exc.detail}")
    
    return


def test_unauthorized_custom_detail():
    """
        Test that Unauthorized accepts custom detail message.
    """
    exc = Unauthorized("Invalid or expired token")
    
    if exc.detail != "Invalid or expired token":
        raise AssertionError(f"Expected custom detail, got {exc.detail}")
    
    return


def test_unauthorized_is_httpexception():
    """
        Test that Unauthorized is an HTTPException subclass.
    """
    exc = Unauthorized()
    
    if not isinstance(exc, HTTPException):
        raise AssertionError("Unauthorized should be an HTTPException subclass")
    
    return


# =============================================================================
# Forbidden Tests
# =============================================================================

def test_forbidden_status_code():
    """
        Test that Forbidden has status code 403.
    """
    exc = Forbidden()
    
    if exc.status_code != 403:
        raise AssertionError(f"Expected status_code 403, got {exc.status_code}")
    
    return


def test_forbidden_default_detail():
    """
        Test that Forbidden has default detail message.
    """
    exc = Forbidden()
    
    if exc.detail != "Forbidden":
        raise AssertionError(f"Expected detail 'Forbidden', got {exc.detail}")
    
    return


def test_forbidden_custom_detail():
    """
        Test that Forbidden accepts custom detail message.
    """
    exc = Forbidden("You do not have permission to delete this resource")
    
    if exc.detail != "You do not have permission to delete this resource":
        raise AssertionError(f"Expected custom detail, got {exc.detail}")
    
    return


def test_forbidden_is_httpexception():
    """
        Test that Forbidden is an HTTPException subclass.
    """
    exc = Forbidden()
    
    if not isinstance(exc, HTTPException):
        raise AssertionError("Forbidden should be an HTTPException subclass")
    
    return


# =============================================================================
# MethodNotAllowed Tests
# =============================================================================

def test_methodnotallowed_status_code():
    """
        Test that MethodNotAllowed has status code 405.
    """
    exc = MethodNotAllowed()
    
    if exc.status_code != 405:
        raise AssertionError(f"Expected status_code 405, got {exc.status_code}")
    
    return


def test_methodnotallowed_default_detail():
    """
        Test that MethodNotAllowed has default detail message.
    """
    exc = MethodNotAllowed()
    
    if exc.detail != "Method Not Allowed":
        raise AssertionError(f"Expected detail 'Method Not Allowed', got {exc.detail}")
    
    return


def test_methodnotallowed_custom_detail():
    """
        Test that MethodNotAllowed accepts custom detail message.
    """
    exc = MethodNotAllowed("POST not allowed on this resource")
    
    if exc.detail != "POST not allowed on this resource":
        raise AssertionError(f"Expected custom detail, got {exc.detail}")
    
    return


def test_methodnotallowed_allowed_methods():
    """
        Test that MethodNotAllowed accepts allowed methods list.
    """
    exc = MethodNotAllowed(allowed=["GET", "HEAD"])
    
    if exc.allowed != ["GET", "HEAD"]:
        raise AssertionError(f"Expected allowed ['GET', 'HEAD'], got {exc.allowed}")
    
    return


def test_methodnotallowed_allow_header():
    """
        Test that MethodNotAllowed sets Allow header.
    """
    exc = MethodNotAllowed(allowed=["GET", "HEAD", "OPTIONS"])
    
    expected_header = "GET, HEAD, OPTIONS"
    if exc.headers.get("Allow") != expected_header:
        raise AssertionError(f"Expected Allow header '{expected_header}', got {exc.headers.get('Allow')}")
    
    return


def test_methodnotallowed_no_allow_header_without_methods():
    """
        Test that MethodNotAllowed has no Allow header when no methods provided.
    """
    exc = MethodNotAllowed()
    
    if "Allow" in exc.headers:
        raise AssertionError(f"Expected no Allow header, got {exc.headers}")
    
    return


def test_methodnotallowed_is_httpexception():
    """
        Test that MethodNotAllowed is an HTTPException subclass.
    """
    exc = MethodNotAllowed()
    
    if not isinstance(exc, HTTPException):
        raise AssertionError("MethodNotAllowed should be an HTTPException subclass")
    
    return



# =============================================================================
# RoutingError Tests
# =============================================================================

from ccai.webworks.routing.exceptions import RoutingError


def test_routingerror_constructor():
    """
        Test that RoutingError constructor creates instance with message.
    """
    exc = RoutingError("Route conflict")
    
    if str(exc) != "Route conflict":
        raise AssertionError(f"Expected message 'Route conflict', got '{str(exc)}'")
    
    return


def test_routingerror_with_path():
    """
        Test that RoutingError accepts path parameter.
    """
    exc = RoutingError("Route conflict", path="/users")
    
    if exc.path != "/users":
        raise AssertionError(f"Expected path '/users', got {exc.path}")
    
    return


def test_routingerror_with_method():
    """
        Test that RoutingError accepts method parameter.
    """
    exc = RoutingError("Route conflict", method="GET")
    
    if exc.method != "GET":
        raise AssertionError(f"Expected method 'GET', got {exc.method}")
    
    return


def test_routingerror_with_existing_handler():
    """
        Test that RoutingError accepts existing_handler parameter.
    """
    def existing_handler():
        pass
    
    exc = RoutingError("Route conflict", existing_handler=existing_handler)
    
    if exc.existing_handler is not existing_handler:
        raise AssertionError("Expected existing_handler to be set")
    
    return


def test_routingerror_all_parameters():
    """
        Test that RoutingError accepts all parameters.
    """
    def existing_handler():
        pass
    
    exc = RoutingError(
        "Route conflict: GET /users already registered",
        path="/users",
        method="GET",
        existing_handler=existing_handler
    )
    
    if exc.path != "/users":
        raise AssertionError(f"Expected path '/users', got {exc.path}")
    
    if exc.method != "GET":
        raise AssertionError(f"Expected method 'GET', got {exc.method}")
    
    if exc.existing_handler is not existing_handler:
        raise AssertionError("Expected existing_handler to be set")
    
    if "Route conflict" not in str(exc):
        raise AssertionError(f"Expected 'Route conflict' in message, got '{str(exc)}'")
    
    return


def test_routingerror_default_values():
    """
        Test that RoutingError has None defaults for optional parameters.
    """
    exc = RoutingError("Some error")
    
    if exc.path is not None:
        raise AssertionError(f"Expected path None, got {exc.path}")
    
    if exc.method is not None:
        raise AssertionError(f"Expected method None, got {exc.method}")
    
    if exc.existing_handler is not None:
        raise AssertionError(f"Expected existing_handler None, got {exc.existing_handler}")
    
    return


def test_routingerror_is_exception():
    """
        Test that RoutingError is an Exception subclass.
    """
    exc = RoutingError("Error")
    
    if not isinstance(exc, Exception):
        raise AssertionError("RoutingError should be an Exception subclass")
    
    return
