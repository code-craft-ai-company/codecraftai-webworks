"""
.. module:: test_restprocessing
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: End-to-end tests of the REST request/response processing a
               WebApplication applies to every route declaring REST
               metadata, served through ``webapp.asgi_app``.

.. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from dataclasses import dataclass
from typing import Any, Callable, List

import ccai.webworks.webapplication as webapp_module

from ccai.testbase.mocking import Mock, create_module_patch

from ccai.webworks.devexp.testing.testclient import TestClient
from ccai.webworks.endpoints.blueprint import Blueprint
from ccai.webworks.endpoints.endpoint import Endpoint
from ccai.webworks.endpoints.rest import ResourceEndpoint, get_rest_payload, is_rest_processed_handler
from ccai.webworks.endpoints.restendpoint import RestEndpoint
from ccai.webworks.routing.request import Request
from ccai.webworks.routing.response import JSONResponse
from ccai.webworks.webapplication import establish_webapp_persona, reset_webapp_persona


# =============================================================================
# Schemas
# =============================================================================

@dataclass
class NoteIn:
    """Request schema of the note routes."""
    title: str
    words: int


@dataclass
class NoteOut:
    """Response schema of the note routes."""
    id: int
    title: str
    words: int


# =============================================================================
# Helpers
# =============================================================================

def _serve(declare_routes: Callable[[Any], None], check: Callable[[TestClient, Any], None]) -> None:
    """
        Establish a web application, let ``declare_routes`` add its routes,
        start it with the configuration registry mocked, and run ``check``
        with a TestClient on ``webapp.asgi_app`` (lifespan running).

        :param declare_routes: Called with the application before startup.
        :param check: Called with the client and the application.
    """
    reset_webapp_persona()

    patch = None

    try:
        app = establish_webapp_persona(name="restapp", logger_name="restapp", log_basename="restapp")

        declare_routes(app)

        mock_config = Mock()
        mock_config.configure(recursive=True)
        patch = create_module_patch(webapp_module, "ManagedConfigRegistry")
        mock_cls = patch.activate()
        mock_cls.configure(return_value=mock_config)

        app.startup()

        with TestClient(app.asgi_app) as client:
            check(client, app)

        app.shutdown()

    finally:
        if patch is not None:
            patch.deactivate()
        reset_webapp_persona()

    return


def _expect(condition: bool, message: str) -> None:
    """
        Raise an AssertionError with ``message`` unless ``condition`` holds.

        :param condition: The checked condition.
        :param message: The failure message.
    """
    if condition is not True:
        raise AssertionError(message)
    return


# =============================================================================
# attach_route
# =============================================================================

def test_attach_route_with_schemas_is_served_through_rest_processing():
    """
        A route declared with attach_route(request_schema=..., response_schema=...)
        answers 415 for a wrong Content-Type, 400 for an invalid body, 406 for
        an unsatisfiable Accept, and hands the handler the validated payload,
        whose serialized result is sent with 201.
    """
    seen_payloads: List[Any] = []

    def declare(app):
        @app.attach_route("/notes", methods=["POST"], request_schema=NoteIn, response_schema=NoteOut)
        def create_note(request):
            payload = get_rest_payload(request)
            seen_payloads.append(payload)
            return NoteOut(id=11, title=payload.title, words=payload.words)

        return

    def check(client, app):
        created = client.post("/notes", json={"title": "hello", "words": 2})
        _expect(created.status_code == 201, "Expected 201, got {} {}".format(created.status_code, created.text))
        _expect(created.json == {"id": 11, "title": "hello", "words": 2}, "Unexpected body {}".format(created.json))
        _expect(created.headers.get("Content-Type") == "application/json",
                "Expected a JSON response, got {}".format(created.headers))
        _expect(len(seen_payloads) == 1 and isinstance(seen_payloads[0], NoteIn),
                "Expected the handler to receive a NoteIn payload, got {}".format(seen_payloads))

        wrong_type = client.post("/notes", content=b"title=hello", headers={"Content-Type": "text/plain"})
        _expect(wrong_type.status_code == 415, "Expected 415, got {}".format(wrong_type.status_code))
        _expect(wrong_type.json.get("error") == "unsupported_media_type",
                "Expected a RESTError body, got {}".format(wrong_type.json))

        invalid = client.post("/notes", json={"title": "hello"})
        _expect(invalid.status_code == 400, "Expected 400, got {}".format(invalid.status_code))
        _expect(invalid.json.get("error") == "validation_error", "Unexpected body {}".format(invalid.json))
        fields = [field_error["field"] for field_error in invalid.json.get("field_errors", [])]
        _expect(fields == ["words"], "Expected a field error for 'words', got {}".format(fields))

        not_acceptable = client.post("/notes", json={"title": "a", "words": 1}, headers={"Accept": "application/xml"})
        _expect(not_acceptable.status_code == 406, "Expected 406, got {}".format(not_acceptable.status_code))
        _expect(not_acceptable.json.get("error") == "not_acceptable", "Unexpected body {}".format(not_acceptable.json))

        _expect(len(seen_payloads) == 1, "Expected the rejected requests never to reach the handler")
        return

    _serve(declare, check)

    return


def test_mapped_exception_is_answered_with_the_rest_error_shape():
    """An exception the REST error handler maps (KeyError -> 404) is answered with a RESTError body."""

    def declare(app):
        @app.attach_route("/notes/{note_id}", methods=["GET"], response_schema=NoteOut)
        def get_note(request):
            raise KeyError(request.path_params["note_id"])

        return

    def check(client, app):
        response = client.get("/notes/42")
        _expect(response.status_code == 404, "Expected 404, got {}".format(response.status_code))
        _expect(response.json.get("error") == "not_found", "Expected the not_found RESTError, got {}".format(response.json))
        _expect("message" in response.json, "Expected a message in the RESTError body, got {}".format(response.json))
        return

    _serve(declare, check)

    return


def test_opted_out_route_sees_the_raw_request():
    """rest_processing=False serves the handler with the raw request; its schemas only document it."""
    raw_bodies: List[bytes] = []

    def declare(app):
        @app.attach_route("/raw", methods=["POST"], request_schema=NoteIn, rest_processing=False)
        def raw(request):
            raw_bodies.append(request.body)
            return JSONResponse({"payload": get_rest_payload(request, default="none")}, status_code=202)

        return

    def check(client, app):
        response = client.post("/raw", content=b"not json at all", headers={"Content-Type": "text/plain"})
        _expect(response.status_code == 202, "Expected the handler's own 202, got {}".format(response.status_code))
        _expect(response.json == {"payload": "none"}, "Expected no payload to be attached, got {}".format(response.json))
        _expect(raw_bodies == [b"not json at all"], "Expected the raw body, got {}".format(raw_bodies))

        match = app.router.match(Request("POST", "/raw"))
        _expect(is_rest_processed_handler(match.handler) is False, "Expected the opted-out handler to be served as declared")
        return

    _serve(declare, check)

    return


def test_route_without_rest_metadata_is_untouched():
    """A route without REST metadata keeps the dispatcher's plain behaviour (200, JSON of the result)."""

    def declare(app):
        @app.attach_route("/plain", methods=["POST"])
        def plain(request):
            return {"length": len(request.body)}

        return

    def check(client, app):
        response = client.post("/plain", content=b"abc", headers={"Content-Type": "text/plain"})
        _expect(response.status_code == 200, "Expected 200, got {}".format(response.status_code))
        _expect(response.json == {"length": 3}, "Unexpected body {}".format(response.json))
        return

    _serve(declare, check)

    return


# =============================================================================
# Endpoint.attach_at / RestEndpoint / blueprints, collected by the registry
# =============================================================================

@RestEndpoint.create(path="/collected/notes", request_schema=NoteIn, response_schema=NoteOut)
def _collected_create(request):
    payload = get_rest_payload(request)
    return NoteOut(id=5, title=payload.title, words=payload.words)


@Endpoint.attach_at(path="/collected/async", methods=["POST"], request_schema=NoteIn, response_schema=NoteOut)
async def _collected_async(request):
    payload = get_rest_payload(request)
    return NoteOut(id=6, title=payload.title, words=payload.words)


class _NotesBlueprint(Blueprint):
    """A blueprint whose route declares schemas."""
    base_path = "/bp"


@_NotesBlueprint.attach_at(leaf="notes", methods=["PUT"], request_schema=NoteIn, response_schema=NoteOut)
def _blueprint_update(request):
    payload = get_rest_payload(request)
    return NoteOut(id=7, title=payload.title, words=payload.words)


def test_collected_attach_at_routes_are_processed_sync_and_async():
    """Routes collected by the endpoint registry are processed, including an async handler."""

    def declare(app):
        app.registry.collect_from(_collected_create, _collected_async)
        return

    def check(client, app):
        created = client.post("/collected/notes", json={"title": "t", "words": 1})
        _expect(created.status_code == 201, "Expected 201, got {} {}".format(created.status_code, created.text))
        _expect(created.json == {"id": 5, "title": "t", "words": 1}, "Unexpected body {}".format(created.json))

        created_async = client.post("/collected/async", json={"title": "u", "words": 2})
        _expect(created_async.status_code == 201, "Expected 201, got {} {}".format(created_async.status_code, created_async.text))
        _expect(created_async.json == {"id": 6, "title": "u", "words": 2}, "Unexpected body {}".format(created_async.json))

        invalid_async = client.post("/collected/async", json={"words": "many"})
        _expect(invalid_async.status_code == 400, "Expected 400, got {}".format(invalid_async.status_code))
        return

    _serve(declare, check)

    return


def test_blueprint_route_with_schemas_is_processed():
    """A blueprint route declaring schemas is processed when the blueprint is attached."""

    def declare(app):
        app.attach_blueprint_to_route(_NotesBlueprint)
        return

    def check(client, app):
        updated = client.put("/bp/notes", json={"title": "v", "words": 3})
        _expect(updated.status_code == 200, "Expected 200 for a PUT, got {} {}".format(updated.status_code, updated.text))
        _expect(updated.json == {"id": 7, "title": "v", "words": 3}, "Unexpected body {}".format(updated.json))

        missing_body = client.put("/bp/notes")
        _expect(missing_body.status_code == 400, "Expected 400 for a missing body, got {}".format(missing_body.status_code))
        return

    _serve(declare, check)

    return


class _Ledger(ResourceEndpoint):
    """A resource endpoint served by a web application."""

    resource_name = "ledger"
    request_schema = NoteIn
    response_schema = NoteOut
    allowed_methods = ["POST"]

    def create(self, payload):
        return NoteOut(id=8, title=payload.title, words=payload.words)


def test_resource_endpoint_is_served_by_its_own_handlers():
    """ResourceEndpoint routes are not wrapped a second time by the application's router."""

    def declare(app):
        app.attach_blueprint_to_route(_Ledger)
        return

    def check(client, app):
        created = client.post("/ledger", json={"title": "w", "words": 4})
        _expect(created.status_code == 201, "Expected 201, got {} {}".format(created.status_code, created.text))
        _expect(created.json == {"id": 8, "title": "w", "words": 4}, "Unexpected body {}".format(created.json))

        match = app.router.match(Request("POST", "/ledger"))
        registered = [descriptor for descriptor in app.registry.collect() if descriptor.path == "/ledger"]
        _expect(len(registered) == 1, "Expected the ledger route in the registry")
        _expect(match.handler is registered[0].handler,
                "Expected the resource's generated handler to be served unwrapped")
        return

    _serve(declare, check)

    return
