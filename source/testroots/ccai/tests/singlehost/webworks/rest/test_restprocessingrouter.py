"""
.. module:: test_restprocessingrouter
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Tests for the RestProcessingRouter, which serves every route
               that declares REST metadata through the REST processing.

.. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

import asyncio
import inspect
import json

from dataclasses import dataclass
from typing import Any, Dict, Optional

from ccai.webworks.authentication.blueprints.basic import BasicAuthBlueprint
from ccai.webworks.endpoints.descriptor import (
    REST_MANAGED_EXTRA,
    REST_PROCESSING_EXTRA,
    EndpointDescriptor,
)
from ccai.webworks.endpoints.endpoint import Endpoint
from ccai.webworks.endpoints.rest import (
    ResourceEndpoint,
    RestProcessingRouter,
    apply_rest_processing,
    create_rest_middleware,
    get_rest_payload,
    is_rest_processed_handler,
    needs_rest_processing,
)
from ccai.webworks.endpoints.rest.middleware import REST_PROCESSED_HANDLER_ATTR
from ccai.webworks.routing.dispatcher import Dispatcher
from ccai.webworks.routing.request import Request
from ccai.webworks.routing.router import Router


# =============================================================================
# Schemas and helpers
# =============================================================================

@dataclass
class WidgetIn:
    """Request schema of the routes under test."""
    name: str
    size: int


@dataclass
class WidgetOut:
    """Response schema of the routes under test."""
    id: int
    name: str
    size: int


def _json_request(method: str, path: str, body: Any = None, headers: Optional[Dict[str, str]] = None) -> Request:
    """
        Build a routing Request with a JSON body.

        :param method: The HTTP method.
        :param path: The request path.
        :param body: The value to send as JSON, or None for no body.
        :param headers: Extra request headers.

        :returns: The Request.
    """
    request_headers: Dict[str, str] = {}
    if headers is not None:
        request_headers.update(headers)

    raw_body = b""
    if body is not None:
        raw_body = json.dumps(body).encode("utf-8")
        request_headers.setdefault("Content-Type", "application/json")

    rtnval = Request(method, path, headers=request_headers, body=raw_body)
    return rtnval


def _descriptor_for(handler) -> EndpointDescriptor:
    """
        Get the single descriptor attach_at recorded on a handler.

        :param handler: The decorated handler.

        :returns: Its descriptor.
    """
    marks = Endpoint._find_descriptors_for_handler(handler)
    if len(marks) != 1:
        raise AssertionError("Expected one descriptor on {}, got {}".format(handler.__name__, len(marks)))
    rtnval = marks[0]
    return rtnval


# =============================================================================
# needs_rest_processing / apply_rest_processing
# =============================================================================

def test_route_declaring_schemas_needs_rest_processing():
    """A route declared with a request and a response schema is to be REST processed."""

    @Endpoint.attach_at(path="/widgets", methods=["POST"], request_schema=WidgetIn, response_schema=WidgetOut)
    def create_widget(request):
        return None

    descriptor = _descriptor_for(create_widget)

    if needs_rest_processing(descriptor) is not True:
        raise AssertionError("Expected a route declaring schemas to need REST processing")

    if descriptor.extras["rest"].get(REST_MANAGED_EXTRA) is not True:
        raise AssertionError("Expected the declaration to mark the route as REST managed")

    return


def test_route_without_rest_metadata_needs_no_processing():
    """A route that declares no REST metadata is served as it is."""

    @Endpoint.attach_at(path="/plain", methods=["GET"])
    def plain(request):
        return {"plain": True}

    descriptor = _descriptor_for(plain)

    if needs_rest_processing(descriptor) is not False:
        raise AssertionError("Expected a route without REST metadata not to be processed")

    middleware = create_rest_middleware()
    routed = apply_rest_processing(descriptor, middleware)

    if routed is not descriptor or routed.handler is not plain:
        raise AssertionError("Expected the descriptor and its handler to be returned unchanged")

    return


def test_opted_out_route_needs_no_processing():
    """rest_processing=False records the opt-out and leaves the route unprocessed."""

    @Endpoint.attach_at(
        path="/raw", methods=["POST"], request_schema=WidgetIn, rest_processing=False
    )
    def raw(request):
        return {"raw": True}

    descriptor = _descriptor_for(raw)

    if descriptor.extras["rest"].get(REST_PROCESSING_EXTRA) is not False:
        raise AssertionError("Expected the opt-out to be recorded under extras['rest']")

    if REST_MANAGED_EXTRA in descriptor.extras["rest"]:
        raise AssertionError("Expected an opted-out route not to be marked REST managed")

    if needs_rest_processing(descriptor) is not False:
        raise AssertionError("Expected an opted-out route not to be processed")

    return


def test_apply_rest_processing_serves_a_copy_and_leaves_the_declaration_alone():
    """The routed descriptor is a copy with a wrapper; the declared descriptor (the mark) keeps its handler."""

    @Endpoint.attach_at(path="/widgets/copy", methods=["POST"], request_schema=WidgetIn)
    def create_copy(request):
        return None

    declared = _descriptor_for(create_copy)
    middleware = create_rest_middleware()

    routed = apply_rest_processing(declared, middleware)

    if routed is declared:
        raise AssertionError("Expected a copy of the declared descriptor")

    if declared.handler is not create_copy:
        raise AssertionError("Expected the declared descriptor to keep the declared handler")

    if is_rest_processed_handler(routed.handler) is not True:
        raise AssertionError("Expected the routed handler to be a REST processing wrapper")

    if routed.handler.descriptor is not routed:
        raise AssertionError("Expected the routed descriptor to be attached to the wrapper")

    if routed.handler.__name__ != "create_copy":
        raise AssertionError("Expected the wrapper to keep the handler's name, got {}".format(routed.handler.__name__))

    if routed.extras["rest"].get(REST_MANAGED_EXTRA) is not True:
        raise AssertionError("Expected the routed descriptor to be marked REST managed")

    return


def test_hand_built_descriptor_with_rest_extras_is_processed():
    """A descriptor built by hand with extras['rest'] is processed and marked managed on the copy only."""

    def hand_built(request):
        return {"name": "x"}

    descriptor = EndpointDescriptor(
        handler=hand_built,
        module=__name__,
        path="/hand",
        methods=["GET"],
        extras={"rest": {"response_schema": WidgetOut}},
    )

    routed = apply_rest_processing(descriptor, create_rest_middleware())

    if is_rest_processed_handler(routed.handler) is not True:
        raise AssertionError("Expected the hand-built route to be wrapped")

    if REST_MANAGED_EXTRA in descriptor.extras["rest"]:
        raise AssertionError("Expected the original extras not to be modified")

    return


def test_wrap_handler_marks_its_result_and_is_not_wrapped_twice():
    """A handler that already runs the REST processing is never wrapped a second time."""
    middleware = create_rest_middleware()

    def handler(request):
        return {"ok": True}

    wrapper = middleware.wrap_handler(handler)

    if getattr(wrapper, REST_PROCESSED_HANDLER_ATTR, False) is not True:
        raise AssertionError("Expected wrap_handler to mark its result")

    descriptor = EndpointDescriptor(
        handler=wrapper,
        module=__name__,
        path="/wrapped",
        methods=["GET"],
        extras={"rest": {"response_schema": WidgetOut}},
    )

    if needs_rest_processing(descriptor) is not False:
        raise AssertionError("Expected an already wrapped handler not to need processing")

    if apply_rest_processing(descriptor, middleware) is not descriptor:
        raise AssertionError("Expected an already wrapped route to be returned unchanged")

    return


def test_wrap_handler_of_a_coroutine_function_is_a_coroutine_function():
    """An async handler gets an async wrapper, so the dispatcher runs it on the event loop."""
    middleware = create_rest_middleware()

    async def async_handler(request):
        return {"ok": True}

    def sync_handler(request):
        return {"ok": True}

    if inspect.iscoroutinefunction(middleware.wrap_handler(async_handler)) is not True:
        raise AssertionError("Expected the wrapper of an async handler to be a coroutine function")

    if inspect.iscoroutinefunction(middleware.wrap_handler(sync_handler)) is not False:
        raise AssertionError("Expected the wrapper of a sync handler to be a plain function")

    return


# =============================================================================
# RestProcessingRouter
# =============================================================================

def _dispatch(router: Router, request: Request):
    """
        Dispatch a request synchronously through a dispatcher on the router.

        :param router: The router.
        :param request: The request.

        :returns: The response.
    """
    rtnval = Dispatcher(router).dispatch(request)
    return rtnval


def test_router_validates_and_serializes_a_declared_route():
    """A route added to the RestProcessingRouter validates its body and serializes its result."""
    router = RestProcessingRouter(rest_middleware=create_rest_middleware())

    @Endpoint.attach_at(path="/widgets/served", methods=["POST"], request_schema=WidgetIn, response_schema=WidgetOut)
    def create_served(request):
        payload = get_rest_payload(request)
        return WidgetOut(id=3, name=payload.name, size=payload.size)

    router.add_endpoint(_descriptor_for(create_served))

    response = _dispatch(router, _json_request("POST", "/widgets/served", {"name": "a", "size": 2}))

    if response.status_code != 201:
        raise AssertionError("Expected 201 for a created resource, got {}".format(response.status_code))

    body = json.loads(response.body)
    if body != {"id": 3, "name": "a", "size": 2}:
        raise AssertionError("Unexpected body: {}".format(body))

    invalid = _dispatch(router, _json_request("POST", "/widgets/served", {"name": "a"}))

    if invalid.status_code != 400:
        raise AssertionError("Expected 400 for an invalid body, got {}".format(invalid.status_code))

    if json.loads(invalid.body).get("error") != "validation_error":
        raise AssertionError("Expected a RESTError validation_error body, got {}".format(invalid.body))

    return


def test_plain_router_serves_the_declared_handler_unprocessed():
    """A plain Router, outside an application, still serves the declared handler as it is."""
    router = Router()

    @Endpoint.attach_at(path="/widgets/plain", methods=["POST"], request_schema=WidgetIn)
    def create_plain(request):
        return {"raw": request.body.decode("utf-8")}

    router.add_endpoint(_descriptor_for(create_plain))

    response = _dispatch(router, _json_request("POST", "/widgets/plain", {"anything": 1}))

    if response.status_code != 200:
        raise AssertionError("Expected the handler's own 200, got {}".format(response.status_code))

    return


def test_router_runs_an_async_declared_route():
    """An async handler declaring schemas is processed and awaited through dispatch_async."""
    router = RestProcessingRouter(rest_middleware=create_rest_middleware())

    @Endpoint.attach_at(path="/widgets/async", methods=["POST"], request_schema=WidgetIn, response_schema=WidgetOut)
    async def create_async(request):
        payload = get_rest_payload(request)
        return WidgetOut(id=9, name=payload.name, size=payload.size)

    router.add_endpoint(_descriptor_for(create_async))

    dispatcher = Dispatcher(router)
    response = asyncio.run(dispatcher.dispatch_async(_json_request("POST", "/widgets/async", {"name": "b", "size": 4})))

    if response.status_code != 201:
        raise AssertionError("Expected 201, got {}".format(response.status_code))

    if json.loads(response.body) != {"id": 9, "name": "b", "size": 4}:
        raise AssertionError("Unexpected body: {}".format(response.body))

    return


class _Gizmo(ResourceEndpoint):
    """A resource endpoint whose generated handlers run the REST processing themselves."""

    resource_name = "gizmos"
    request_schema = WidgetIn
    response_schema = WidgetOut
    allowed_methods = ["GET", "POST"]

    def get(self, id):
        return WidgetOut(id=id, name="gizmo", size=1)

    def create(self, payload):
        return WidgetOut(id=1, name=payload.name, size=payload.size)


def test_resource_endpoint_routes_are_not_wrapped_twice():
    """The RestProcessingRouter adds ResourceEndpoint routes with their own handlers."""
    router = RestProcessingRouter(rest_middleware=create_rest_middleware())

    descriptors = _Gizmo.register(router=router)

    for descriptor in descriptors:
        match = router.match(Request(descriptor.methods[0], descriptor.path.replace("{id:int}", "5")))
        if match is None:
            raise AssertionError("Expected {} to be routed".format(descriptor.path))
        if match.handler is not descriptor.handler:
            raise AssertionError("Expected the resource's own handler to be served for {}".format(descriptor.path))

    response = _dispatch(router, _json_request("POST", "/gizmos", {"name": "g", "size": 3}))

    if response.status_code != 201:
        raise AssertionError("Expected 201, got {}".format(response.status_code))

    return


def test_authentication_blueprint_routes_opt_out_of_rest_processing():
    """The authentication blueprints declare schemas but are served with their own handlers."""
    descriptors = BasicAuthBlueprint.register()

    schema_routes = []
    for descriptor in descriptors:
        rest_extras = descriptor.extras.get("rest")
        if isinstance(rest_extras, dict):
            schema_routes.append(descriptor)

    if len(schema_routes) == 0:
        raise AssertionError("Expected the basic auth blueprint to declare schemas on a route")

    middleware = create_rest_middleware()

    for descriptor in schema_routes:
        if descriptor.extras["rest"].get(REST_PROCESSING_EXTRA) is not False:
            raise AssertionError("Expected {} to opt out of REST processing".format(descriptor.path))

        if apply_rest_processing(descriptor, middleware) is not descriptor:
            raise AssertionError("Expected {} to be served unprocessed".format(descriptor.path))

    return
