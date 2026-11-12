"""
    Unit tests for the RequestLoggingMiddleware.

    These tests cover what the middleware writes to the log for input a
    client controls: control characters in the path, secrets in the query
    string, and the completion line of a request whose handler raises.
"""

import asyncio
import logging

from ccai.webworks.routing.middleware import MiddlewarePipeline
from ccai.webworks.routing.middleware.logging import REDACTED, RequestLoggingMiddleware
from ccai.webworks.routing.request import Request
from ccai.webworks.routing.response import Response


class _ListHandler(logging.Handler):
    """
        Logging handler that keeps the formatted messages in a list.
    """

    def __init__(self):
        super().__init__()
        self.messages = []
        return

    def emit(self, record):
        self.messages.append(record.getMessage())
        return


def _make_logger(name):
    """
        Create a logger that records its messages.
    """
    logger = logging.getLogger("test_logging_unit." + name)
    logger.handlers = []
    logger.propagate = False
    logger.setLevel(logging.DEBUG)
    handler = _ListHandler()
    logger.addHandler(handler)
    return logger, handler


def _ok_handler(request):
    """
        Endpoint stand-in returning a plain 200 response.
    """
    return Response(status_code=200)


def test_logging_escapes_line_feed_in_path():
    """
        A decoded line feed in the path can not start a forged log line.
    """
    logger, handler = _make_logger("escape")
    middleware = RequestLoggingMiddleware(logger=logger)

    middleware(Request(method="GET", path="/x\nINFO forged entry"), _ok_handler)

    request_msg = handler.messages[0]

    assert "\n" not in request_msg, f"The log line contains a raw line feed: {request_msg!r}"
    assert "\\n" in request_msg, f"Expected the escaped line feed, got {request_msg!r}"
    return


def test_logging_redacts_sensitive_query_parameters():
    """
        The value of a credential parameter is not written to the log.
    """
    logger, handler = _make_logger("redact")
    middleware = RequestLoggingMiddleware(logger=logger)

    request = Request(method="GET", path="/login", query_string=b"api_key=SECRET123&page=2")
    middleware(request, _ok_handler)

    request_msg = handler.messages[0]

    assert "SECRET123" not in request_msg, f"The secret was logged: {request_msg}"
    assert REDACTED in request_msg, f"Expected the redaction marker, got {request_msg}"
    assert "page" in request_msg and "2" in request_msg, f"Other parameters should be logged: {request_msg}"
    return


def test_logging_redacts_configured_parameters():
    """
        The list of sensitive parameters is configurable.
    """
    logger, handler = _make_logger("configured")
    middleware = RequestLoggingMiddleware(logger=logger, sensitive_params=["invite"])

    request = Request(method="GET", path="/join", query_string=b"invite=abc123")
    middleware(request, _ok_handler)

    assert "abc123" not in handler.messages[0], f"The secret was logged: {handler.messages[0]}"
    return


def test_logging_writes_completion_line_when_handler_raises():
    """
        A completion line is logged, and the exception still propagates,
        when the next handler raises.
    """
    logger, handler = _make_logger("failure")
    middleware = RequestLoggingMiddleware(logger=logger)

    def failing_handler(request):
        raise RuntimeError("boom")

    raised = False
    try:
        middleware(Request(method="GET", path="/fail"), failing_handler)
    except RuntimeError:
        raised = True

    assert raised, "The exception must propagate"
    assert len(handler.messages) == 2, f"Expected a request and a completion line, got {handler.messages}"
    assert "RuntimeError" in handler.messages[1], f"Unexpected completion line {handler.messages[1]}"
    return


def test_logging_runs_in_async_pipeline():
    """
        The logging middleware works in the asynchronous pipeline.
    """
    logger, handler = _make_logger("async")
    pipeline = MiddlewarePipeline()
    pipeline.add(RequestLoggingMiddleware(logger=logger))

    async def async_handler(request):
        return Response(status_code=204)

    response = asyncio.run(pipeline.execute_async(Request(method="GET", path="/a"), async_handler))

    assert response.status_code == 204, f"Expected 204, got {response.status_code}"
    assert len(handler.messages) == 2, f"Expected two log lines, got {handler.messages}"
    assert "204" in handler.messages[1], f"Unexpected completion line {handler.messages[1]}"
    return
