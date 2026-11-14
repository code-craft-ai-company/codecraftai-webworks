"""
    handlers.py

    Top-level endpoint handlers for the testcomponents site:

      - ``/``                        the browse-by-group landing page
      - ``/charts``                  the Charts landing page
      - ``/chart-type/{type_key}``   the sandbox page of one <mj-chart> type
      - ``/chart-part/{tag}``        the sandbox page of one chart part
      - ``/static/{assetpath:path}`` serves the mj-* component library and
        design tokens out of the ccai.webworks static directory, with
        ETag / Last-Modified validators and 304 responses

    The per-group index pages and per-component test pages are served by
    the group blueprints (see endpoints/blueprints).
"""

import email.utils
import mimetypes
import os

import ccai.webworks as _webworks

from ccai.webworks.endpoints.endpoint import Endpoint
from ccai.webworks.routing.request import Request
from ccai.webworks.routing.response import HTMLResponse
from ccai.webworks.routing.response import Response

from testcomponents.endpoints.blueprints.groupserving import not_found_response
from testcomponents.rendering import render_browse_page
from testcomponents.rendering import render_chart_part_page
from testcomponents.rendering import render_chart_type_page
from testcomponents.rendering import render_charts_page


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

# The library is edited while the site runs, so a browser may keep a copy
# but must revalidate it on every use: with the validators below an
# unchanged file costs a 304 with no body instead of a full download.
_STATIC_CACHE_CONTROL = "public, max-age=0, must-revalidate"


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


def static_validators(path: str) -> "tuple[str, str, int]":
    """
        Compute the cache validators of a static file.

        :param path: The filesystem path of the file.

        :returns: (etag, last_modified, mtime_seconds): a weak ETag derived from
            the modification time and size, the HTTP-date of the modification
            time, and the modification time truncated to whole seconds.
    """

    status = os.stat(path)
    etag = 'W/"{:x}-{:x}"'.format(status.st_mtime_ns, status.st_size)
    mtime_seconds = int(status.st_mtime)
    last_modified = email.utils.formatdate(mtime_seconds, usegmt=True)
    return etag, last_modified, mtime_seconds


def is_not_modified(request: Request, etag: str, mtime_seconds: int) -> bool:
    """
        Decide whether a conditional GET can be answered with 304.

        ``If-None-Match`` wins over ``If-Modified-Since`` (RFC 9110 13.1.3);
        the ETag comparison is weak.

        :param request: The incoming request.
        :param etag: The current ETag of the resource.
        :param mtime_seconds: The modification time in whole seconds.

        :returns: True when the client's copy is current.
    """

    if_none_match = request.get_header("if-none-match")
    if if_none_match is not None:
        current = etag
        if current.startswith("W/"):
            current = current[2:]
        matched = False
        for candidate in if_none_match.split(","):
            tag = candidate.strip()
            if tag == "*":
                matched = True
            if tag.startswith("W/"):
                tag = tag[2:]
            if tag == current:
                matched = True
        return matched

    if_modified_since = request.get_header("if-modified-since")
    if if_modified_since is not None:
        try:
            since = email.utils.parsedate_to_datetime(if_modified_since)
        except (TypeError, ValueError):
            return False
        if since is None:
            return False
        not_modified = mtime_seconds <= int(since.timestamp())
        return not_modified

    return False


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
        Serve the sandbox page for one <mj-chart> chart type from the
        comprehensive chart library.

        :param request: The incoming HTTP request.

        :returns: An HTMLResponse with the rendered page, or 404 on miss.
    """

    type_key = request.path_params.get("type_key", "")
    example_key = request.query_params.get("example")
    content = render_chart_type_page(type_key, example_key=example_key)
    if content is None:
        # The message is escaped by the not-found page: the key comes from the URL.
        response = not_found_response(f"No chart type named \"{type_key}\".")
        return response

    response = HTMLResponse(content=content, status_code=200)
    return response


@Endpoint.attach_at(path="/chart-part/{tag}", methods=["GET"])
def chart_part_page(request: Request) -> HTMLResponse:
    """
        Serve the sandbox page for one chart part component
        (<mj-chart-title>, <mj-chart-legend>, <mj-chart-data-table>).

        :param request: The incoming HTTP request.

        :returns: An HTMLResponse with the rendered page, or 404 on miss.
    """

    tag = request.path_params.get("tag", "")
    example_key = request.query_params.get("example")
    content = render_chart_part_page(tag, example_key=example_key)
    if content is None:
        response = not_found_response(f"No chart part named \"{tag}\".")
        return response

    response = HTMLResponse(content=content, status_code=200)
    return response


@Endpoint.attach_at(path="/static/{assetpath:path}", methods=["GET"])
def serve_static(request: Request) -> Response:
    """
        Serve a static asset from the mj-* component library directory.

        The requested path is resolved beneath the static root and a
        traversal guard rejects any path that escapes that directory. The
        response carries an ETag and Last-Modified; a conditional request
        whose validators still match is answered 304 Not Modified.

        :param request: The incoming HTTP request.

        :returns: A Response with the asset bytes, a 304, or a 404 Response.
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

    etag, last_modified, mtime_seconds = static_validators(candidate)
    headers = {
        "ETag": etag,
        "Last-Modified": last_modified,
        "Cache-Control": _STATIC_CACHE_CONTROL,
    }

    not_modified = is_not_modified(request, etag, mtime_seconds)
    if not_modified is True:
        response = Response(status_code=304, headers=headers, body=b"")
        return response

    with open(candidate, "rb") as asset_file:
        data = asset_file.read()

    headers["Content-Type"] = _content_type_for(candidate)
    response = Response(status_code=200, headers=headers, body=data)
    return response
