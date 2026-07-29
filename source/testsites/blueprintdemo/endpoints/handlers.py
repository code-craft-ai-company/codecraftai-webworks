"""
    Endpoint handlers for the blueprintdemo test site.

    This module defines the HTTP endpoint handlers for the blueprintdemo
    site using the RestBlueprint pattern. ``ItemsBlueprint`` groups related
    item handlers under a shared ``/api/items`` base path using the
    ``RestBlueprint.attach_at`` decorator so the Router can discover them
    at application startup.

    ``ItemsV2Blueprint`` extends ``ItemsBlueprint`` with a different
    base path ``/api/v2/items`` and overrides the ``list_items`` handler
    to return augmented item records with version metadata. Non-overridden
    endpoints are inherited from the parent blueprint.
"""

from ccai.webworks.endpoints.doc import Doc
from ccai.webworks.endpoints.endpoint import Endpoint
from ccai.webworks.endpoints.restblueprint import RestBlueprint
from ccai.webworks.routing.request import Request
from ccai.webworks.routing.response import HTMLResponse
from ccai.webworks.routing.response import JSONResponse
from ccai.webworks.routing.response import RedirectResponse


_MAIN_PAGE_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Blueprint Demo</title>
    <style>
        body { font-family: sans-serif; max-width: 640px; margin: 2rem auto; padding: 0 1rem; }
        h1 { color: #333; }
        h2 { color: #555; margin-top: 1.5rem; }
        ul { list-style: none; padding: 0; }
        li { margin: 0.4rem 0; }
        a { color: #0066cc; text-decoration: none; }
        a:hover { text-decoration: underline; }
        code { background: #f4f4f4; padding: 0.15rem 0.3rem; border-radius: 3px; font-size: 0.9em; }
    </style>
</head>
<body>
    <h1>Blueprint Demo</h1>
    <p>This site demonstrates the RestBlueprint endpoint pattern.</p>

    <h2>Base Blueprint <code>/api/items</code></h2>
    <ul>
        <li><a href="/api/items/list">GET /api/items/list</a> &mdash; List all items</li>
        <li><a href="/api/items/detail">GET /api/items/detail</a> &mdash; Get item detail</li>
        <li><code>POST /api/items/create</code> &mdash; Create an item</li>
    </ul>

    <h2>Extended Blueprint <code>/api/v2/items</code></h2>
    <ul>
        <li><a href="/api/v2/items/list">GET /api/v2/items/list</a> &mdash; List items (v2, with version metadata)</li>
    </ul>

    <h2>Documentation</h2>
    <ul>
        <li><a href="/docs">Swagger UI</a></li>
        <li><a href="/openapi.json">OpenAPI Specification (JSON)</a></li>
    </ul>
</body>
</html>
"""


@Endpoint.attach_at(path="/", methods=["GET"])
def root_page(request: Request) -> RedirectResponse:
    """
        Handle GET requests to the root path by redirecting to /home.

        :param request: The incoming HTTP request.

        :returns: A RedirectResponse to /home with status 302.
    """

    response = RedirectResponse(url="/home", status_code=302)

    return response


@Endpoint.attach_at(path="/home", methods=["GET"])
def main_page(request: Request) -> HTMLResponse:
    """
        Serve the main index page with links to all demo endpoints.

        :param request: The incoming HTTP request.

        :returns: An HTMLResponse containing the index page with status 200.
    """

    response = HTMLResponse(content=_MAIN_PAGE_HTML, status_code=200)

    return response


ITEMS = [
    {"id": 1, "name": "Widget"},
    {"id": 2, "name": "Gadget"},
]


class ItemsBlueprint(RestBlueprint):
    base_path = "/api/items"
    methods = ["GET"]
    tags = ["items"]

    @RestBlueprint.attach_at(
        leaf="list",
        methods=["GET"],
        doc=Doc(
            summary="List Items",
            description="Retrieve a list of all available items.",
        ),
    )
    def list_items(request: Request) -> JSONResponse:
        """
            Handle GET requests to the items list path.

            :param request: The incoming HTTP request.

            :returns: A JSONResponse containing all items with status 200.
        """

        content = {"items": ITEMS}
        response = JSONResponse(content=content, status_code=200)

        return response

    @RestBlueprint.attach_at(
        leaf="detail",
        methods=["GET"],
        doc=Doc(
            summary="Get Item Detail",
            description="Retrieve a single item record.",
        ),
    )
    def get_item(request: Request) -> JSONResponse:
        """
            Handle GET requests to the item detail path.

            :param request: The incoming HTTP request.

            :returns: A JSONResponse containing a single item with status 200.
        """

        content = {"id": 1, "name": "Widget"}
        response = JSONResponse(content=content, status_code=200)

        return response

    @RestBlueprint.attach_at(
        leaf="create",
        methods=["POST"],
        doc=Doc(
            summary="Create Item",
            description="Create a new item record.",
        ),
    )
    def create_item(request: Request) -> JSONResponse:
        """
            Handle POST requests to the item create path.

            :param request: The incoming HTTP request.

            :returns: A JSONResponse containing the created item with status 201.
        """

        content = {"id": 3, "name": "NewItem", "created": True}
        response = JSONResponse(content=content, status_code=201)

        return response


class ItemsV2Blueprint(ItemsBlueprint):
    base_path = "/api/v2/items"
    tags = ["items-v2"]

    @RestBlueprint.attach_at(
        leaf="list",
        methods=["GET"],
        doc=Doc(
            summary="List Items (V2)",
            description="Retrieve items with version metadata and total count.",
        ),
    )
    def list_items(request: Request) -> JSONResponse:
        """
            Handle GET requests to the v2 items list path.

            Returns an augmented response with version metadata and a total
            count field in addition to the base item records.

            :param request: The incoming HTTP request.

            :returns: A JSONResponse containing versioned items with status 200.
        """

        versioned_items = [
            {**item, "version": "v2"} for item in ITEMS
        ]

        content = {"items": versioned_items, "total": len(versioned_items)}
        response = JSONResponse(content=content, status_code=200)

        return response
