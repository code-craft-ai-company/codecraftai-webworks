"""
    handlers.py

    Top-level endpoint handlers for the testcomponents site:

      - ``/``                       the browse-by-group landing page
      - ``/static/{assetpath:path}`` serves the mj-* component library and
        design tokens out of the ccai.webworks static directory

    The per-group index pages and per-component test pages are served by
    the group blueprints (see endpoints/blueprints).
"""

import mimetypes
import os

import ccai.webworks as _webworks

from ccai.webworks.endpoints.endpoint import Endpoint
from ccai.webworks.routing.request import Request
from ccai.webworks.routing.response import HTMLResponse
from ccai.webworks.routing.response import Response

from testcomponents.rendering import render_browse_page
from testcomponents.rendering import render_charts_page
from testcomponents.rendering import render_chart_type_page


# Absolute path to the shipped mj-* component library / design tokens.
_STATIC_ROOT = os.path.realpath(
    os.path.join(os.path.dirname(_webworks.__file__), "static")
)

# Explicit content types for asset extensions the standard library may
# resolve inconsistently across platforms.
_CONTENT_TYPE_OVERRIDES = {
    ".js": "text/javascript; charset=utf-8",
    ".mjs": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".html": "text/html; charset=utf-8",
}


def _content_type_for(path: str) -> str:
    """
        Resolve the Content-Type header value for an asset path.

        :param path: The filesystem path of the asset.

        :returns: A MIME type string.
    """

    _root, extension = os.path.splitext(path)
    lowered = extension.lower()

    override = _CONTENT_TYPE_OVERRIDES.get(lowered)
    if override is not None:
        return override

    guessed, _encoding = mimetypes.guess_type(path)
    if guessed is not None:
        return guessed

    fallback = "application/octet-stream"
    return fallback


@Endpoint.attach_at(path="/", methods=["GET"])
def browse_page(request: Request) -> HTMLResponse:
    """
        Serve the browse-by-group landing page.

        :param request: The incoming HTTP request.

        :returns: An HTMLResponse with the rendered browse page.
    """

    content = render_browse_page()
    response = HTMLResponse(content=content, status_code=200)
    return response


@Endpoint.attach_at(path="/charts", methods=["GET"])
def charts_page(request: Request) -> HTMLResponse:
    """
        Serve the dedicated Charts landing page.

        :param request: The incoming HTTP request.

        :returns: An HTMLResponse with the rendered charts page.
    """

    content = render_charts_page()
    response = HTMLResponse(content=content, status_code=200)
    return response


@Endpoint.attach_at(path="/chart-type/{type_key}", methods=["GET"])
def chart_type_page(request: Request) -> HTMLResponse:
    """
        Serve the interactive playground page for one <mj-chart> chart
        type from the comprehensive chart library.

        :param request: The incoming HTTP request.

        :returns: An HTMLResponse with the rendered page, or 404 on miss.
    """

    type_key = request.path_params.get("type_key", "")
    content = render_chart_type_page(type_key)
    if content is None:
        not_found = HTMLResponse(
            content=f"<h1>Unknown chart type</h1><p>No chart type named "
                    f"&quot;{type_key}&quot;.</p>",
            status_code=404,
        )
        return not_found

    response = HTMLResponse(content=content, status_code=200)
    return response


@Endpoint.attach_at(path="/static/{assetpath:path}", methods=["GET"])
def serve_static(request: Request) -> Response:
    """
        Serve a static asset from the mj-* component library directory.

        The requested path is resolved beneath the static root and a
        traversal guard rejects any path that escapes that directory.

        :param request: The incoming HTTP request.

        :returns: A Response with the asset bytes, or a 404 Response.
    """

    relative = request.path_params.get("assetpath", "")

    candidate = os.path.realpath(os.path.join(_STATIC_ROOT, relative))

    within_root = candidate.startswith(_STATIC_ROOT + os.sep)
    if within_root is False:
        not_found = Response(status_code=404, body=b"Not found")
        return not_found

    is_file = os.path.isfile(candidate)
    if is_file is False:
        not_found = Response(status_code=404, body=b"Not found")
        return not_found

    with open(candidate, "rb") as asset_file:
        data = asset_file.read()

    headers = {
        "Content-Type": _content_type_for(candidate),
        "Cache-Control": "no-cache",
    }
    response = Response(status_code=200, headers=headers, body=data)
    return response
