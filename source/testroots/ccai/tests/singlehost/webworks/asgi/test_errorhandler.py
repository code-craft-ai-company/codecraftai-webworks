"""
    Tests for the ErrorHandler class.
    
    This module contains unit tests for the ASGI error handler functionality
    including HTTP error handling, unhandled exception handling, debug vs
    production formatting, and custom error handler registration.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from ccai.webworks.asgi.errorhandler import (
    ErrorHandler,
    ErrorResponse,
    HTTPException,
)
from ccai.webworks.asgi.constants import (
    MESSAGE_HTTP_RESPONSE_START,
    MESSAGE_HTTP_RESPONSE_BODY,
    MESSAGE_WEBSOCKET_CLOSE,
    WS_CLOSE_INTERNAL_ERROR,
)
from ccai.webworks.asgi.exceptions import (
    BadRequestBody,
    RequestEntityTooLarge,
)


# =============================================================================
# Helper Functions for Creating Mock Send Callables
# =============================================================================

def create_send_callable() -> tuple:
    """
        Create a mock send callable that records sent messages.
        
        :returns: Tuple of (send_callable, sent_messages_list).
    """
    sent_messages: List[Dict[str, Any]] = []
    
    async def send(message: Dict[str, Any]) -> None:
        sent_messages.append(message)
        return
    
    return send, sent_messages


def create_http_scope(
    method: str = "GET",
    path: str = "/",
) -> Dict[str, Any]:
    """
        Create a mock HTTP scope for testing.
        
        :param method: HTTP method.
        :param path: Request path.
        
        :returns: ASGI HTTP scope dictionary.
    """
    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "query_string": b"",
        "headers": [],
    }
    return scope


def create_websocket_scope(
    path: str = "/ws",
) -> Dict[str, Any]:
    """
        Create a mock WebSocket scope for testing.
        
        :param path: Request path.
        
        :returns: ASGI WebSocket scope dictionary.
    """
    scope = {
        "type": "websocket",
        "path": path,
        "query_string": b"",
        "headers": [],
    }
    return scope


# =============================================================================
# Unit Tests for ErrorHandler - Constructor
# =============================================================================

def test_errorhandler_constructor_default_values():
    """
        Test that ErrorHandler constructor uses default values.
    """
    handler = ErrorHandler()
    
    if handler is None:
        errmsg = "Expected ErrorHandler instance, got None"
        raise AssertionError(errmsg)
    
    if handler.debug is not False:
        errmsg = f"Expected debug=False, got {handler.debug}"
        raise AssertionError(errmsg)
    
    return


def test_errorhandler_constructor_with_debug_true():
    """
        Test that ErrorHandler constructor accepts debug=True.
    """
    handler = ErrorHandler(debug=True)
    
    if handler.debug is not True:
        errmsg = f"Expected debug=True, got {handler.debug}"
        raise AssertionError(errmsg)
    
    return


def test_errorhandler_constructor_with_custom_logger():
    """
        Test that ErrorHandler constructor accepts custom logger.
    """
    custom_logger = logging.getLogger("test_logger")
    handler = ErrorHandler(logger=custom_logger)
    
    if handler.logger is not custom_logger:
        errmsg = "Expected custom logger to be used"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for ErrorResponse
# =============================================================================

def test_errorresponse_constructor():
    """
        Test that ErrorResponse constructor creates instance.
    """
    response = ErrorResponse(
        status_code=500,
        body=b'{"error": "test"}',
    )
    
    if response.status_code != 500:
        errmsg = f"Expected status_code=500, got {response.status_code}"
        raise AssertionError(errmsg)
    
    if response.body != b'{"error": "test"}':
        errmsg = f"Expected body to match, got {response.body}"
        raise AssertionError(errmsg)
    
    return


def test_errorresponse_default_headers():
    """
        Test that ErrorResponse sets default headers.
    """
    body = b'{"error": "test"}'
    response = ErrorResponse(
        status_code=500,
        body=body,
    )
    
    headers = response.headers
    
    if "Content-Type" not in headers:
        errmsg = "Expected Content-Type header"
        raise AssertionError(errmsg)
    
    if "Content-Length" not in headers:
        errmsg = "Expected Content-Length header"
        raise AssertionError(errmsg)
    
    if headers["Content-Length"] != str(len(body)):
        errmsg = f"Expected Content-Length={len(body)}, got {headers['Content-Length']}"
        raise AssertionError(errmsg)
    
    return


def test_errorresponse_custom_headers():
    """
        Test that ErrorResponse accepts custom headers.
    """
    custom_headers = {
        "Content-Type": "text/plain",
        "X-Custom": "value",
    }
    
    response = ErrorResponse(
        status_code=500,
        body=b"error",
        headers=custom_headers,
    )
    
    if response.headers != custom_headers:
        errmsg = f"Expected custom headers, got {response.headers}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for HTTPException
# =============================================================================

def test_httpexception_constructor():
    """
        Test that HTTPException constructor creates instance.
    """
    exc = HTTPException(status_code=404)
    
    if exc.status_code != 404:
        errmsg = f"Expected status_code=404, got {exc.status_code}"
        raise AssertionError(errmsg)
    
    return


def test_httpexception_with_detail():
    """
        Test that HTTPException accepts detail message.
    """
    exc = HTTPException(status_code=400, detail="Invalid input")
    
    if exc.detail != "Invalid input":
        errmsg = f"Expected detail='Invalid input', got {exc.detail}"
        raise AssertionError(errmsg)
    
    return


def test_httpexception_message_includes_status_phrase():
    """
        Test that HTTPException message includes status phrase.
    """
    exc = HTTPException(status_code=404)
    
    if "Not Found" not in str(exc):
        errmsg = f"Expected 'Not Found' in message, got {str(exc)}"
        raise AssertionError(errmsg)
    
    return


def test_httpexception_message_includes_detail():
    """
        Test that HTTPException message includes detail when provided.
    """
    exc = HTTPException(status_code=400, detail="Missing field")
    
    if "Missing field" not in str(exc):
        errmsg = f"Expected 'Missing field' in message, got {str(exc)}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for ErrorHandler - handle_http_error() Method
# =============================================================================

def test_handle_http_error_sends_response_for_httpexception():
    """
        Test that handle_http_error() sends response for HTTPException.
        
        Requirements: 10.1
    """
    handler = ErrorHandler(debug=False)
    send, sent_messages = create_send_callable()
    scope = create_http_scope()
    
    exc = HTTPException(status_code=404, detail="Resource not found")
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle_http_error(exc, send, scope)
    )
    
    if len(sent_messages) != 2:
        errmsg = f"Expected 2 messages, got {len(sent_messages)}"
        raise AssertionError(errmsg)
    
    # Check start message
    start_msg = sent_messages[0]
    if start_msg.get("type") != MESSAGE_HTTP_RESPONSE_START:
        errmsg = f"Expected response start, got {start_msg.get('type')}"
        raise AssertionError(errmsg)
    
    if start_msg.get("status") != 404:
        errmsg = f"Expected status 404, got {start_msg.get('status')}"
        raise AssertionError(errmsg)
    
    return


def test_handle_http_error_sends_500_for_unhandled_exception():
    """
        Test that handle_http_error() sends 500 for unhandled exceptions.
        
        Requirements: 10.2
    """
    handler = ErrorHandler(debug=False)
    send, sent_messages = create_send_callable()
    scope = create_http_scope()
    
    exc = ValueError("Something went wrong")
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle_http_error(exc, send, scope)
    )
    
    start_msg = sent_messages[0]
    
    if start_msg.get("status") != 500:
        errmsg = f"Expected status 500, got {start_msg.get('status')}"
        raise AssertionError(errmsg)
    
    return


def test_handle_http_error_handles_badrequestbody():
    """
        Test that handle_http_error() handles BadRequestBody exception.
        
        Requirements: 10.1
    """
    handler = ErrorHandler(debug=False)
    send, sent_messages = create_send_callable()
    scope = create_http_scope()
    
    exc = BadRequestBody("Invalid JSON")
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle_http_error(exc, send, scope)
    )
    
    start_msg = sent_messages[0]
    
    if start_msg.get("status") != 400:
        errmsg = f"Expected status 400, got {start_msg.get('status')}"
        raise AssertionError(errmsg)
    
    return


def test_handle_http_error_handles_requestentitytoolarge():
    """
        Test that handle_http_error() handles RequestEntityTooLarge exception.
        
        Requirements: 10.1
    """
    handler = ErrorHandler(debug=False)
    send, sent_messages = create_send_callable()
    scope = create_http_scope()
    
    exc = RequestEntityTooLarge(max_size=1000, actual_size=2000)
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle_http_error(exc, send, scope)
    )
    
    start_msg = sent_messages[0]
    
    if start_msg.get("status") != 413:
        errmsg = f"Expected status 413, got {start_msg.get('status')}"
        raise AssertionError(errmsg)
    
    return


def test_handle_http_error_sends_json_body():
    """
        Test that handle_http_error() sends JSON body.
    """
    handler = ErrorHandler(debug=False)
    send, sent_messages = create_send_callable()
    scope = create_http_scope()
    
    exc = HTTPException(status_code=404)
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle_http_error(exc, send, scope)
    )
    
    body_msg = sent_messages[1]
    body_bytes = body_msg.get("body")
    
    # Should be valid JSON
    try:
        body_data = json.loads(body_bytes)
    except json.JSONDecodeError:
        errmsg = f"Expected valid JSON body, got {body_bytes}"
        raise AssertionError(errmsg)
    
    if "error" not in body_data:
        errmsg = f"Expected 'error' key in body, got {body_data}"
        raise AssertionError(errmsg)
    
    return


def test_handle_http_error_body_contains_status():
    """
        Test that error body contains status code.
    """
    handler = ErrorHandler(debug=False)
    send, sent_messages = create_send_callable()
    scope = create_http_scope()
    
    exc = HTTPException(status_code=403)
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle_http_error(exc, send, scope)
    )
    
    body_msg = sent_messages[1]
    body_data = json.loads(body_msg.get("body"))
    
    if body_data["error"]["status"] != 403:
        errmsg = f"Expected status 403 in body, got {body_data['error']['status']}"
        raise AssertionError(errmsg)
    
    return


def test_handle_http_error_body_contains_message():
    """
        Test that error body contains message.
    """
    handler = ErrorHandler(debug=False)
    send, sent_messages = create_send_callable()
    scope = create_http_scope()
    
    exc = HTTPException(status_code=404)
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle_http_error(exc, send, scope)
    )
    
    body_msg = sent_messages[1]
    body_data = json.loads(body_msg.get("body"))
    
    if "message" not in body_data["error"]:
        errmsg = f"Expected 'message' in error body, got {body_data}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for ErrorHandler - Debug vs Production Formatting
# =============================================================================

def test_handle_http_error_production_hides_details():
    """
        Test that production mode hides internal error details.
        
        Requirements: 10.4
    """
    handler = ErrorHandler(debug=False)
    send, sent_messages = create_send_callable()
    scope = create_http_scope()
    
    exc = ValueError("Internal implementation detail")
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle_http_error(exc, send, scope)
    )
    
    body_msg = sent_messages[1]
    body_data = json.loads(body_msg.get("body"))
    
    # Should not contain traceback in production
    if "traceback" in body_data["error"]:
        errmsg = "Expected no traceback in production mode"
        raise AssertionError(errmsg)
    
    # Should not contain exception type in production
    if "type" in body_data["error"]:
        errmsg = "Expected no exception type in production mode"
        raise AssertionError(errmsg)
    
    return


def test_handle_http_error_debug_includes_traceback():
    """
        Test that debug mode includes stack traces.
        
        Requirements: 10.5
    """
    handler = ErrorHandler(debug=True)
    send, sent_messages = create_send_callable()
    scope = create_http_scope()
    
    exc = ValueError("Test error")
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle_http_error(exc, send, scope)
    )
    
    body_msg = sent_messages[1]
    body_data = json.loads(body_msg.get("body"))
    
    if "traceback" not in body_data["error"]:
        errmsg = "Expected traceback in debug mode"
        raise AssertionError(errmsg)
    
    return


def test_handle_http_error_debug_includes_exception_type():
    """
        Test that debug mode includes exception type.
        
        Requirements: 10.5
    """
    handler = ErrorHandler(debug=True)
    send, sent_messages = create_send_callable()
    scope = create_http_scope()
    
    exc = ValueError("Test error")
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle_http_error(exc, send, scope)
    )
    
    body_msg = sent_messages[1]
    body_data = json.loads(body_msg.get("body"))
    
    if body_data["error"].get("type") != "ValueError":
        errmsg = f"Expected type='ValueError', got {body_data['error'].get('type')}"
        raise AssertionError(errmsg)
    
    return


def test_handle_http_error_debug_includes_detail():
    """
        Test that debug mode includes error detail.
        
        Requirements: 10.5
    """
    handler = ErrorHandler(debug=True)
    send, sent_messages = create_send_callable()
    scope = create_http_scope()
    
    exc = ValueError("Specific error message")
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle_http_error(exc, send, scope)
    )
    
    body_msg = sent_messages[1]
    body_data = json.loads(body_msg.get("body"))
    
    if "Specific error message" not in body_data["error"].get("detail", ""):
        errmsg = f"Expected detail to contain error message, got {body_data['error'].get('detail')}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for ErrorHandler - Custom Error Handler Registration
# =============================================================================

def test_register_handler_stores_handler():
    """
        Test that register_handler() stores the handler.
        
        Requirements: 10.8
    """
    handler = ErrorHandler()
    
    async def custom_handler(exc: Exception) -> ErrorResponse:
        return ErrorResponse(status_code=418, body=b'{"error": "teapot"}')
    
    handler.register_handler(ValueError, custom_handler)
    
    stored_handler = handler.get_handler(ValueError)
    
    if stored_handler is not custom_handler:
        errmsg = "Expected custom handler to be stored"
        raise AssertionError(errmsg)
    
    return


def test_register_handler_uses_custom_handler():
    """
        Test that handle_http_error() uses registered custom handler.
        
        Requirements: 10.8
    """
    handler = ErrorHandler()
    send, sent_messages = create_send_callable()
    scope = create_http_scope()
    
    async def custom_handler(exc: Exception) -> ErrorResponse:
        return ErrorResponse(
            status_code=418,
            body=b'{"error": {"status": 418, "message": "I am a teapot"}}',
        )
    
    handler.register_handler(ValueError, custom_handler)
    
    exc = ValueError("Test")
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle_http_error(exc, send, scope)
    )
    
    start_msg = sent_messages[0]
    
    if start_msg.get("status") != 418:
        errmsg = f"Expected status 418 from custom handler, got {start_msg.get('status')}"
        raise AssertionError(errmsg)
    
    return


def test_register_handler_matches_subclasses():
    """
        Test that custom handler matches exception subclasses.
        
        Requirements: 10.8
    """
    handler = ErrorHandler()
    send, sent_messages = create_send_callable()
    scope = create_http_scope()
    
    async def custom_handler(exc: Exception) -> ErrorResponse:
        return ErrorResponse(
            status_code=422,
            body=b'{"error": {"status": 422, "message": "Custom"}}',
        )
    
    # Register handler for base Exception
    handler.register_handler(Exception, custom_handler)
    
    # Raise a ValueError (subclass of Exception)
    exc = ValueError("Test")
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle_http_error(exc, send, scope)
    )
    
    start_msg = sent_messages[0]
    
    if start_msg.get("status") != 422:
        errmsg = f"Expected status 422 from custom handler, got {start_msg.get('status')}"
        raise AssertionError(errmsg)
    
    return


def test_unregister_handler_removes_handler():
    """
        Test that unregister_handler() removes the handler.
    """
    handler = ErrorHandler()
    
    async def custom_handler(exc: Exception) -> ErrorResponse:
        return ErrorResponse(status_code=418, body=b'{}')
    
    handler.register_handler(ValueError, custom_handler)
    handler.unregister_handler(ValueError)
    
    stored_handler = handler.get_handler(ValueError)
    
    if stored_handler is not None:
        errmsg = "Expected handler to be removed"
        raise AssertionError(errmsg)
    
    return


def test_register_handler_exact_match_takes_precedence():
    """
        Test that exact exception type match takes precedence over parent.
    """
    handler = ErrorHandler()
    send, sent_messages = create_send_callable()
    scope = create_http_scope()
    
    async def base_handler(exc: Exception) -> ErrorResponse:
        return ErrorResponse(
            status_code=400,
            body=b'{"error": {"status": 400, "message": "Base"}}',
        )
    
    async def specific_handler(exc: Exception) -> ErrorResponse:
        return ErrorResponse(
            status_code=422,
            body=b'{"error": {"status": 422, "message": "Specific"}}',
        )
    
    handler.register_handler(Exception, base_handler)
    handler.register_handler(ValueError, specific_handler)
    
    exc = ValueError("Test")
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle_http_error(exc, send, scope)
    )
    
    start_msg = sent_messages[0]
    
    if start_msg.get("status") != 422:
        errmsg = f"Expected status 422 from specific handler, got {start_msg.get('status')}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for ErrorHandler - log_exception() Method
# =============================================================================

def test_log_exception_logs_error():
    """
        Test that log_exception() logs the error.
        
        Requirements: 10.3
    """
    # Create a handler to capture log records
    log_records = []
    
    class TestHandler(logging.Handler):
        def emit(self, record):
            log_records.append(record)
    
    test_logger = logging.getLogger("test_log_exception")
    test_logger.setLevel(logging.ERROR)
    test_handler = TestHandler()
    test_logger.addHandler(test_handler)
    
    handler = ErrorHandler(logger=test_logger)
    scope = create_http_scope(method="POST", path="/api/test")
    
    exc = ValueError("Test error message")
    
    handler.log_exception(exc, scope)
    
    if len(log_records) == 0:
        errmsg = "Expected log record to be created"
        raise AssertionError(errmsg)
    
    log_message = log_records[0].getMessage()
    
    if "ValueError" not in log_message:
        errmsg = f"Expected 'ValueError' in log message, got {log_message}"
        raise AssertionError(errmsg)
    
    if "Test error message" not in log_message:
        errmsg = f"Expected error message in log, got {log_message}"
        raise AssertionError(errmsg)
    
    # Clean up
    test_logger.removeHandler(test_handler)
    
    return


def test_log_exception_includes_path():
    """
        Test that log_exception() includes request path.
        
        Requirements: 10.3
    """
    log_records = []
    
    class TestHandler(logging.Handler):
        def emit(self, record):
            log_records.append(record)
    
    test_logger = logging.getLogger("test_log_path")
    test_logger.setLevel(logging.ERROR)
    test_handler = TestHandler()
    test_logger.addHandler(test_handler)
    
    handler = ErrorHandler(logger=test_logger)
    scope = create_http_scope(method="GET", path="/api/users/123")
    
    exc = ValueError("Test")
    
    handler.log_exception(exc, scope)
    
    log_message = log_records[0].getMessage()
    
    if "/api/users/123" not in log_message:
        errmsg = f"Expected path in log message, got {log_message}"
        raise AssertionError(errmsg)
    
    # Clean up
    test_logger.removeHandler(test_handler)
    
    return


# =============================================================================
# Unit Tests for ErrorHandler - handle_websocket_error() Method
# =============================================================================

def test_handle_websocket_error_sends_close_message():
    """
        Test that handle_websocket_error() sends close message.
        
        Requirements: 10.6
    """
    handler = ErrorHandler(debug=False)
    send, sent_messages = create_send_callable()
    scope = create_websocket_scope()
    
    exc = ValueError("WebSocket error")
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle_websocket_error(exc, send, scope)
    )
    
    if len(sent_messages) != 1:
        errmsg = f"Expected 1 message, got {len(sent_messages)}"
        raise AssertionError(errmsg)
    
    close_msg = sent_messages[0]
    
    if close_msg.get("type") != MESSAGE_WEBSOCKET_CLOSE:
        errmsg = f"Expected websocket.close, got {close_msg.get('type')}"
        raise AssertionError(errmsg)
    
    return


def test_handle_websocket_error_uses_internal_error_code():
    """
        Test that handle_websocket_error() uses internal error close code.
        
        Requirements: 10.6
    """
    handler = ErrorHandler(debug=False)
    send, sent_messages = create_send_callable()
    scope = create_websocket_scope()
    
    exc = ValueError("Error")
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle_websocket_error(exc, send, scope)
    )
    
    close_msg = sent_messages[0]
    
    if close_msg.get("code") != WS_CLOSE_INTERNAL_ERROR:
        errmsg = f"Expected code {WS_CLOSE_INTERNAL_ERROR}, got {close_msg.get('code')}"
        raise AssertionError(errmsg)
    
    return


def test_handle_websocket_error_production_hides_reason():
    """
        Test that production mode hides error reason in WebSocket close.
        
        Requirements: 10.4
    """
    handler = ErrorHandler(debug=False)
    send, sent_messages = create_send_callable()
    scope = create_websocket_scope()
    
    exc = ValueError("Secret internal error")
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle_websocket_error(exc, send, scope)
    )
    
    close_msg = sent_messages[0]
    reason = close_msg.get("reason", "")
    
    if "Secret internal error" in reason:
        errmsg = "Expected internal error details to be hidden in production"
        raise AssertionError(errmsg)
    
    return


def test_handle_websocket_error_debug_includes_reason():
    """
        Test that debug mode includes error reason in WebSocket close.
        
        Requirements: 10.5
    """
    handler = ErrorHandler(debug=True)
    send, sent_messages = create_send_callable()
    scope = create_websocket_scope()
    
    exc = ValueError("Debug error message")
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle_websocket_error(exc, send, scope)
    )
    
    close_msg = sent_messages[0]
    reason = close_msg.get("reason", "")
    
    if "ValueError" not in reason:
        errmsg = f"Expected exception type in reason, got {reason}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for ErrorHandler - format_error_body() Method
# =============================================================================

def test_format_error_body_returns_bytes():
    """
        Test that format_error_body() returns bytes.
    """
    handler = ErrorHandler()
    
    body = handler.format_error_body(
        status_code=500,
        message="Internal Server Error",
    )
    
    if not isinstance(body, bytes):
        errmsg = f"Expected bytes, got {type(body)}"
        raise AssertionError(errmsg)
    
    return


def test_format_error_body_returns_valid_json():
    """
        Test that format_error_body() returns valid JSON.
    """
    handler = ErrorHandler()
    
    body = handler.format_error_body(
        status_code=404,
        message="Not Found",
    )
    
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        errmsg = f"Expected valid JSON, got {body}"
        raise AssertionError(errmsg)
    
    return


def test_format_error_body_includes_status():
    """
        Test that format_error_body() includes status in body.
    """
    handler = ErrorHandler()
    
    body = handler.format_error_body(
        status_code=403,
        message="Forbidden",
    )
    
    data = json.loads(body)
    
    if data["error"]["status"] != 403:
        errmsg = f"Expected status 403, got {data['error']['status']}"
        raise AssertionError(errmsg)
    
    return


def test_format_error_body_includes_message():
    """
        Test that format_error_body() includes message in body.
    """
    handler = ErrorHandler()
    
    body = handler.format_error_body(
        status_code=500,
        message="Custom Error Message",
    )
    
    data = json.loads(body)
    
    if data["error"]["message"] != "Custom Error Message":
        errmsg = f"Expected message 'Custom Error Message', got {data['error']['message']}"
        raise AssertionError(errmsg)
    
    return


def test_format_error_body_includes_detail_when_provided():
    """
        Test that format_error_body() includes detail when provided.
    """
    handler = ErrorHandler()
    
    body = handler.format_error_body(
        status_code=400,
        message="Bad Request",
        detail="Missing required field 'name'",
    )
    
    data = json.loads(body)
    
    if data["error"].get("detail") != "Missing required field 'name'":
        errmsg = f"Expected detail, got {data['error'].get('detail')}"
        raise AssertionError(errmsg)
    
    return


def test_format_error_body_with_exception_includes_type():
    """
        Test that format_error_body() includes exception type when provided.
    """
    handler = ErrorHandler()
    
    exc = ValueError("Test error")
    
    body = handler.format_error_body(
        status_code=500,
        message="Internal Server Error",
        exc=exc,
    )
    
    data = json.loads(body)
    
    if data["error"].get("type") != "ValueError":
        errmsg = f"Expected type 'ValueError', got {data['error'].get('type')}"
        raise AssertionError(errmsg)
    
    return


def test_format_error_body_with_exception_includes_traceback():
    """
        Test that format_error_body() includes traceback when exception provided.
    """
    handler = ErrorHandler()
    
    try:
        raise ValueError("Test error")
    except ValueError as exc:
        body = handler.format_error_body(
            status_code=500,
            message="Internal Server Error",
            exc=exc,
        )
    
    data = json.loads(body)
    
    if "traceback" not in data["error"]:
        errmsg = "Expected traceback in error body"
        raise AssertionError(errmsg)
    
    if not isinstance(data["error"]["traceback"], list):
        errmsg = f"Expected traceback to be list, got {type(data['error']['traceback'])}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Random Generators for Property-Based Tests
# =============================================================================

import random
import string

# HTTP error status codes that have phrases in the constants module
HTTP_ERROR_STATUS_CODES = [
    400, 401, 403, 404, 405, 406, 408, 409, 410,
    413, 415, 422, 429, 500, 501, 502, 503, 504,
]

COMMON_EXCEPTION_MESSAGES = [
    "something went wrong",
    "not found",
    "access denied",
    "invalid input",
    "timeout exceeded",
    "connection refused",
    "resource unavailable",
    "",
]


def generate_random_string(min_length: int = 1, max_length: int = 30) -> str:
    """Generate a random alphanumeric string."""
    length = random.randint(min_length, max_length)
    chars = string.ascii_letters + string.digits + " _-"
    rtnval = "".join(random.choice(chars) for _ in range(length))
    return rtnval


def generate_random_error_status_code() -> int:
    """Generate a random HTTP error status code."""
    rtnval = random.choice(HTTP_ERROR_STATUS_CODES)
    return rtnval


def generate_random_http_scope() -> Dict[str, Any]:
    """Generate a random HTTP scope for error testing."""
    methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]
    paths = ["/", "/api/users", "/api/items/42", "/health", "/admin/settings"]
    scope = {
        "type": "http",
        "method": random.choice(methods),
        "path": random.choice(paths),
        "query_string": b"",
        "headers": [],
    }
    return scope


def generate_random_detail() -> Optional[str]:
    """Generate a random detail message or None."""
    if random.random() < 0.3:
        return None
    return generate_random_string(5, 50)


# =============================================================================
# Property-Based Tests
# =============================================================================

# Feature: asgi-layer, Property 12: Error Response Correctness
# *For any* HTTPException raised during request handling, the application
# SHALL return a response with the exception's status code. *For any*
# unhandled exception, the application SHALL return HTTP 500 and log the
# exception with stack trace. In production mode, error responses SHALL NOT
# contain internal details; in debug mode, they SHALL contain stack traces.
# **Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5, 10.8**


def test_property_12_httpexception_returns_matching_status_code():
    """
        Property 12: Error Response Correctness - HTTPException Status Codes

        For any HTTPException with a random valid error status code and
        optional detail, handle_http_error() SHALL send a response whose
        status code matches the exception's status code.

        **Validates: Requirement 10.1**
    """
    handler = ErrorHandler(debug=False)

    for iteration in range(100):
        send, sent_messages = create_send_callable()
        scope = generate_random_http_scope()

        status_code = generate_random_error_status_code()
        detail = generate_random_detail()

        exc = HTTPException(status_code=status_code, detail=detail)

        asyncio.get_event_loop().run_until_complete(
            handler.handle_http_error(exc, send, scope)
        )

        # Property: at least two messages sent (start + body)
        if len(sent_messages) < 2:
            errmsg = (
                f"Iteration {iteration}: expected at least 2 messages, "
                f"got {len(sent_messages)}"
            )
            raise AssertionError(errmsg)

        # Property: first message is response start
        start_msg = sent_messages[0]
        if start_msg.get("type") != MESSAGE_HTTP_RESPONSE_START:
            errmsg = (
                f"Iteration {iteration}: first message type should be "
                f"'{MESSAGE_HTTP_RESPONSE_START}', got '{start_msg.get('type')}'"
            )
            raise AssertionError(errmsg)

        # Property: response status matches exception status (Req 10.1)
        if start_msg.get("status") != status_code:
            errmsg = (
                f"Iteration {iteration}: response status {start_msg.get('status')} "
                f"!= exception status {status_code}"
            )
            raise AssertionError(errmsg)

        # Property: body message follows start
        body_msg = sent_messages[1]
        if body_msg.get("type") != MESSAGE_HTTP_RESPONSE_BODY:
            errmsg = (
                f"Iteration {iteration}: second message type should be "
                f"'{MESSAGE_HTTP_RESPONSE_BODY}', got '{body_msg.get('type')}'"
            )
            raise AssertionError(errmsg)

        # Property: body is valid JSON with error.status matching
        body_data = json.loads(body_msg.get("body", b"{}"))
        if body_data.get("error", {}).get("status") != status_code:
            errmsg = (
                f"Iteration {iteration}: body error.status "
                f"{body_data.get('error', {}).get('status')} != {status_code}"
            )
            raise AssertionError(errmsg)

        # Property: body has more_body=False (complete response)
        if body_msg.get("more_body") is not False:
            errmsg = (
                f"Iteration {iteration}: body more_body should be False, "
                f"got {body_msg.get('more_body')}"
            )
            raise AssertionError(errmsg)

    return


def test_property_12_unhandled_exception_returns_500():
    """
        Property 12: Error Response Correctness - Unhandled Exceptions

        For any unhandled exception (not an HTTPException), handle_http_error()
        SHALL return HTTP 500 Internal Server Error.

        **Validates: Requirement 10.2**
    """
    handler = ErrorHandler(debug=False)

    # Various exception types that are not HTTPException
    exception_factories = [
        lambda msg: ValueError(msg),
        lambda msg: TypeError(msg),
        lambda msg: KeyError(msg),
        lambda msg: RuntimeError(msg),
        lambda msg: IOError(msg),
        lambda msg: AttributeError(msg),
        lambda msg: IndexError(msg),
        lambda msg: ZeroDivisionError(msg),
    ]

    for iteration in range(100):
        send, sent_messages = create_send_callable()
        scope = generate_random_http_scope()

        factory = random.choice(exception_factories)
        message = generate_random_string(3, 40)
        exc = factory(message)

        asyncio.get_event_loop().run_until_complete(
            handler.handle_http_error(exc, send, scope)
        )

        # Property: response sent
        if len(sent_messages) < 2:
            errmsg = (
                f"Iteration {iteration}: expected at least 2 messages, "
                f"got {len(sent_messages)}"
            )
            raise AssertionError(errmsg)

        # Property: status code is 500 (Req 10.2)
        start_msg = sent_messages[0]
        if start_msg.get("status") != 500:
            errmsg = (
                f"Iteration {iteration}: unhandled exception should produce "
                f"status 500, got {start_msg.get('status')}"
            )
            raise AssertionError(errmsg)

        # Property: body contains error with status 500
        body_data = json.loads(sent_messages[1].get("body", b"{}"))
        if body_data.get("error", {}).get("status") != 500:
            errmsg = (
                f"Iteration {iteration}: body error.status should be 500, "
                f"got {body_data.get('error', {}).get('status')}"
            )
            raise AssertionError(errmsg)

    return


def test_property_12_unhandled_exception_is_logged():
    """
        Property 12: Error Response Correctness - Exception Logging

        For any unhandled exception, handle_http_error() SHALL log the
        exception with stack trace information.

        **Validates: Requirement 10.3**
    """

    for iteration in range(100):
        # Use a custom logger to capture log output
        test_logger = logging.getLogger(f"test_property_12_logging_{iteration}")
        test_logger.setLevel(logging.DEBUG)

        log_records: List[logging.LogRecord] = []

        class RecordHandler(logging.Handler):
            def emit(self, record):
                log_records.append(record)

        record_handler = RecordHandler()
        test_logger.addHandler(record_handler)

        try:
            handler = ErrorHandler(debug=False, logger=test_logger)
            send, sent_messages = create_send_callable()
            scope = generate_random_http_scope()

            message = generate_random_string(3, 40)
            exc = RuntimeError(message)

            asyncio.get_event_loop().run_until_complete(
                handler.handle_http_error(exc, send, scope)
            )

            # Property: at least one error log record was created (Req 10.3)
            error_records = [r for r in log_records if r.levelno >= logging.ERROR]
            if len(error_records) < 1:
                errmsg = (
                    f"Iteration {iteration}: expected at least 1 error log record, "
                    f"got {len(error_records)}"
                )
                raise AssertionError(errmsg)

            # Property: log message contains exception type name
            log_message = error_records[0].getMessage()
            if "RuntimeError" not in log_message:
                errmsg = (
                    f"Iteration {iteration}: log should contain exception type "
                    f"'RuntimeError', got: {log_message[:100]}"
                )
                raise AssertionError(errmsg)

        finally:
            test_logger.removeHandler(record_handler)

    return


def test_property_12_production_mode_hides_internal_details():
    """
        Property 12: Error Response Correctness - Production Mode

        For any exception handled in production mode (debug=False), the
        error response body SHALL NOT contain traceback, exception type,
        or internal detail information.

        **Validates: Requirement 10.4**
    """
    handler = ErrorHandler(debug=False)

    exception_factories = [
        lambda msg: ValueError(msg),
        lambda msg: TypeError(msg),
        lambda msg: RuntimeError(msg),
        lambda msg: HTTPException(status_code=generate_random_error_status_code(), detail=msg),
    ]

    for iteration in range(100):
        send, sent_messages = create_send_callable()
        scope = generate_random_http_scope()

        factory = random.choice(exception_factories)
        message = generate_random_string(5, 40)
        exc = factory(message)

        asyncio.get_event_loop().run_until_complete(
            handler.handle_http_error(exc, send, scope)
        )

        # Parse the response body
        body_data = json.loads(sent_messages[1].get("body", b"{}"))
        error_obj = body_data.get("error", {})

        # Property: no traceback in production mode (Req 10.4)
        if "traceback" in error_obj:
            errmsg = (
                f"Iteration {iteration}: production mode should NOT include "
                f"traceback in error response"
            )
            raise AssertionError(errmsg)

        # Property: no exception type in production mode (Req 10.4)
        if "type" in error_obj:
            errmsg = (
                f"Iteration {iteration}: production mode should NOT include "
                f"exception type in error response"
            )
            raise AssertionError(errmsg)

    return


def test_property_12_debug_mode_includes_stack_traces():
    """
        Property 12: Error Response Correctness - Debug Mode

        For any exception handled in debug mode (debug=True), the error
        response body SHALL contain traceback and exception type information.

        **Validates: Requirement 10.5**
    """
    handler = ErrorHandler(debug=True)

    exception_factories = [
        lambda: ValueError("test value error"),
        lambda: TypeError("test type error"),
        lambda: RuntimeError("test runtime error"),
        lambda: KeyError("test key error"),
    ]

    for iteration in range(100):
        send, sent_messages = create_send_callable()
        scope = generate_random_http_scope()

        factory = random.choice(exception_factories)

        # Raise and catch to get a real traceback
        try:
            raise factory()
        except Exception as exc:
            asyncio.get_event_loop().run_until_complete(
                handler.handle_http_error(exc, send, scope)
            )

        # Parse the response body
        body_data = json.loads(sent_messages[1].get("body", b"{}"))
        error_obj = body_data.get("error", {})

        # Property: traceback present in debug mode (Req 10.5)
        if "traceback" not in error_obj:
            errmsg = (
                f"Iteration {iteration}: debug mode should include "
                f"traceback in error response"
            )
            raise AssertionError(errmsg)

        # Property: traceback is a list of strings
        tb = error_obj["traceback"]
        if not isinstance(tb, list):
            errmsg = (
                f"Iteration {iteration}: traceback should be a list, "
                f"got {type(tb).__name__}"
            )
            raise AssertionError(errmsg)

        if len(tb) < 1:
            errmsg = (
                f"Iteration {iteration}: traceback should have at least "
                f"1 entry, got {len(tb)}"
            )
            raise AssertionError(errmsg)

        # Property: exception type present in debug mode (Req 10.5)
        if "type" not in error_obj:
            errmsg = (
                f"Iteration {iteration}: debug mode should include "
                f"exception type in error response"
            )
            raise AssertionError(errmsg)

    return


def test_property_12_custom_handler_is_invoked():
    """
        Property 12: Error Response Correctness - Custom Error Handlers

        For any exception type with a registered custom handler,
        handle_http_error() SHALL invoke the custom handler and send
        the response it returns, rather than the default error response.

        **Validates: Requirement 10.8**
    """
    handler = ErrorHandler(debug=False)

    for iteration in range(100):
        send, sent_messages = create_send_callable()
        scope = generate_random_http_scope()

        # Generate a random custom status code for the custom handler response
        custom_status = random.choice([418, 422, 503, 451, 429])
        custom_body_text = generate_random_string(5, 30)
        custom_body = json.dumps({"custom": custom_body_text}).encode("utf-8")

        # Create a custom handler that returns a specific ErrorResponse
        async def custom_error_handler(exc, _status=custom_status, _body=custom_body):
            return ErrorResponse(
                status_code=_status,
                body=_body,
            )

        # Register the custom handler for ValueError
        handler.register_handler(ValueError, custom_error_handler)

        try:
            exc = ValueError(generate_random_string(3, 20))

            asyncio.get_event_loop().run_until_complete(
                handler.handle_http_error(exc, send, scope)
            )

            # Property: response was sent
            if len(sent_messages) < 2:
                errmsg = (
                    f"Iteration {iteration}: expected at least 2 messages, "
                    f"got {len(sent_messages)}"
                )
                raise AssertionError(errmsg)

            # Property: status code matches custom handler response (Req 10.8)
            start_msg = sent_messages[0]
            if start_msg.get("status") != custom_status:
                errmsg = (
                    f"Iteration {iteration}: custom handler status "
                    f"{start_msg.get('status')} != expected {custom_status}"
                )
                raise AssertionError(errmsg)

            # Property: body matches custom handler response (Req 10.8)
            body_msg = sent_messages[1]
            if body_msg.get("body") != custom_body:
                errmsg = (
                    f"Iteration {iteration}: custom handler body does not match"
                )
                raise AssertionError(errmsg)

        finally:
            handler.unregister_handler(ValueError)

    return


def test_property_12_error_response_is_valid_json():
    """
        Property 12: Error Response Correctness - JSON Validity

        For any exception (HTTPException or unhandled), the error response
        body SHALL be valid JSON containing at minimum an error object with
        status and message fields.

        **Validates: Requirements 10.1, 10.2**
    """
    for debug_mode in (True, False):
        handler = ErrorHandler(debug=debug_mode)

        for iteration in range(50):
            send, sent_messages = create_send_callable()
            scope = generate_random_http_scope()

            # Alternate between HTTPException and unhandled exceptions
            if random.random() < 0.5:
                status_code = generate_random_error_status_code()
                detail = generate_random_detail()
                try:
                    raise HTTPException(status_code=status_code, detail=detail)
                except HTTPException as exc:
                    asyncio.get_event_loop().run_until_complete(
                        handler.handle_http_error(exc, send, scope)
                    )
            else:
                try:
                    raise RuntimeError(generate_random_string(3, 30))
                except RuntimeError as exc:
                    asyncio.get_event_loop().run_until_complete(
                        handler.handle_http_error(exc, send, scope)
                    )

            # Property: body is valid JSON
            body_bytes = sent_messages[1].get("body", b"{}")
            try:
                body_data = json.loads(body_bytes)
            except json.JSONDecodeError as parse_exc:
                errmsg = (
                    f"Iteration {iteration} (debug={debug_mode}): "
                    f"body is not valid JSON: {parse_exc}"
                )
                raise AssertionError(errmsg)

            # Property: contains error.status
            error_obj = body_data.get("error")
            if error_obj is None:
                errmsg = (
                    f"Iteration {iteration} (debug={debug_mode}): "
                    f"body missing 'error' key"
                )
                raise AssertionError(errmsg)

            if "status" not in error_obj:
                errmsg = (
                    f"Iteration {iteration} (debug={debug_mode}): "
                    f"error object missing 'status' key"
                )
                raise AssertionError(errmsg)

            # Property: contains error.message
            if "message" not in error_obj:
                errmsg = (
                    f"Iteration {iteration} (debug={debug_mode}): "
                    f"error object missing 'message' key"
                )
                raise AssertionError(errmsg)

    return
