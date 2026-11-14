"""
    Tests for the ExtensionMiddleware adapter.

    This module contains unit tests for putting a middleware component
    registered through the ``register_middleware`` hook on the request
    pipeline, synchronously and asynchronously.
"""

import asyncio
import threading

from typing import Any, List

from ccai.webworks.extensibility.componenthooks import REGISTER_MIDDLEWARE
from ccai.webworks.extensibility.extensionmiddleware import (
    ExtensionMiddleware,
    register_extension_middleware,
)
from ccai.webworks.routing.middleware import MiddlewarePipeline
from ccai.webworks.routing.middlewareregistry import MiddlewareRegistry
from ccai.webworks.routing.request import Request
from ccai.webworks.routing.response import JSONResponse, Response


class _RecordingComponent:
    """A middleware component that records its calls and tags responses."""

    name = "recording"
    priority = 10

    def __init__(self, log: List[str], short_circuit: bool = False):
        self._log = log
        self._short_circuit = short_circuit
        self.threads: List[str] = []
        return

    def process_request(self, request: Any) -> Any:
        self._log.append("process_request")
        self.threads.append(threading.current_thread().name)
        rtnval = None
        if self._short_circuit is True:
            rtnval = JSONResponse({"short": True}, status_code=403)
        return rtnval

    def process_response(self, request: Any, response: Any) -> Any:
        self._log.append("process_response")
        response.set_header("X-Recorded", "yes")
        return None


class _AsyncComponent:
    """A middleware component whose methods are coroutine functions."""

    def __init__(self, log: List[str]):
        self._log = log
        return

    async def process_request(self, request: Any) -> Any:
        self._log.append("async_request")
        return None

    async def process_response(self, request: Any, response: Any) -> Any:
        self._log.append("async_response")
        replacement = Response(status_code=299, body=b"replaced")
        return replacement


def _handler_recording(log: List[str]):
    """
        Build a handler that records it ran.

        :param log: The shared log.

        :returns: The handler.
    """
    def handler(request: Any) -> Any:
        log.append("handler")
        return JSONResponse({"ok": True})
    return handler


def test_adapter_runs_around_the_handler_in_the_sync_pipeline():
    """
        Test that process_request runs before and process_response after the
        rest of the pipeline, and may change the response in place.
    """
    log: List[str] = []
    pipeline = MiddlewarePipeline()
    pipeline.add(ExtensionMiddleware(_RecordingComponent(log)))

    response = pipeline.execute(Request("GET", "/"), _handler_recording(log))

    if log != ["process_request", "handler", "process_response"]:
        raise AssertionError("Unexpected sequence {}".format(log))

    if response.headers.get("X-Recorded") != "yes":
        raise AssertionError("Expected process_response to tag the response, got {}".format(response.headers))

    return


def test_process_request_response_short_circuits_the_pipeline():
    """
        Test that a response returned by process_request is sent without
        calling the rest of the pipeline, and still passes process_response.
    """
    log: List[str] = []
    pipeline = MiddlewarePipeline()
    pipeline.add(ExtensionMiddleware(_RecordingComponent(log, short_circuit=True)))

    response = pipeline.execute(Request("GET", "/"), _handler_recording(log))

    if log != ["process_request", "process_response"]:
        raise AssertionError("Expected the handler to be skipped, got {}".format(log))

    if response.status_code != 403 or response.headers.get("X-Recorded") != "yes":
        raise AssertionError("Expected the short-circuit response, tagged, got {}".format(response.status_code))

    return


def test_async_pipeline_awaits_coroutine_methods_and_takes_replacements():
    """
        Test that coroutine methods are awaited in the async pipeline and a
        response returned by process_response replaces the response.
    """
    log: List[str] = []
    pipeline = MiddlewarePipeline()
    pipeline.add(ExtensionMiddleware(_AsyncComponent(log)))

    async def handler(request: Any) -> Any:
        log.append("handler")
        return JSONResponse({"ok": True})

    response = asyncio.run(pipeline.execute_async(Request("GET", "/"), handler))

    if log != ["async_request", "handler", "async_response"]:
        raise AssertionError("Unexpected sequence {}".format(log))

    if response.status_code != 299:
        raise AssertionError("Expected the replacement response, got {}".format(response.status_code))

    return


def test_async_pipeline_runs_plain_methods_off_the_event_loop():
    """
        Test that plain methods run on a worker thread in the async pipeline.
    """
    log: List[str] = []
    component = _RecordingComponent(log)
    pipeline = MiddlewarePipeline()
    pipeline.add(ExtensionMiddleware(component))

    async def handler(request: Any) -> Any:
        log.append("handler")
        return JSONResponse({"ok": True})

    loop_threads: List[str] = []

    async def run() -> Any:
        loop_threads.append(threading.current_thread().name)
        rtnval = await pipeline.execute_async(Request("GET", "/"), handler)
        return rtnval

    asyncio.run(run())

    if log != ["process_request", "handler", "process_response"]:
        raise AssertionError("Unexpected sequence {}".format(log))

    if component.threads[0] == loop_threads[0]:
        raise AssertionError("Expected process_request to run off the event loop thread")

    return


def test_sync_pipeline_drives_coroutine_methods():
    """
        Test that coroutine methods are driven to completion in the sync pipeline.
    """
    log: List[str] = []
    pipeline = MiddlewarePipeline()
    pipeline.add(ExtensionMiddleware(_AsyncComponent(log)))

    response = pipeline.execute(Request("GET", "/"), _handler_recording(log))

    if log != ["async_request", "handler", "async_response"] or response.status_code != 299:
        raise AssertionError("Unexpected sequence {} / status {}".format(log, response.status_code))

    return


def test_register_extension_middleware_adds_global_middleware_with_its_placement():
    """
        Test that the component is registered as global middleware with its
        name and priority and recorded as an extension component.
    """
    registry = MiddlewareRegistry()
    component = _RecordingComponent([])

    adapter = register_extension_middleware(registry, component)

    entries = registry.get_middleware_by_scope("global")
    if len(entries) != 1 or entries[0].middleware is not adapter:
        raise AssertionError("Expected the adapter on the global scope, got {}".format(entries))

    if entries[0].name != "recording" or entries[0].priority != 10:
        raise AssertionError("Expected name 'recording' and priority 10, got {}".format(entries[0]))

    if registry.get_registered_components(REGISTER_MIDDLEWARE) != [component]:
        raise AssertionError("Expected the component to be recorded as an extension component")

    return


def test_adapter_refuses_a_priority_of_the_wrong_type():
    """
        Test that a non-integer priority is refused.
    """
    class _BadPriority(_RecordingComponent):
        priority = "high"

    caught = None
    try:
        ExtensionMiddleware(_BadPriority([]))
    except TypeError as err:
        caught = err

    if caught is None:
        raise AssertionError("Expected TypeError for a string priority")

    return
