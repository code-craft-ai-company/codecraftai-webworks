"""
    groupserving.py

    Shared serving helpers used by every group blueprint. The blueprints
    themselves are thin: they declare their routes and delegate to these
    functions, so the index/component rendering logic lives in one place.
"""

import html

from ccai.webworks.routing.response import HTMLResponse

from testcomponents.rendering import page_shell
from testcomponents.rendering import render_component_page
from testcomponents.rendering import render_group_index


def serve_group_index(group_key: str) -> HTMLResponse:
    """
        Serve the index page for a component group.

        :param group_key: The group key to render.

        :returns: An HTMLResponse with the group index, or a 404 page.
    """

    content = render_group_index(group_key)
    if content is None:
        return _not_found_response(f"Unknown component group '{group_key}'.")

    response = HTMLResponse(content=content, status_code=200)
    return response


def serve_component_page(group_key: str, tag: str) -> HTMLResponse:
    """
        Serve the interactive test page for a single component.

        :param group_key: The owning group key.
        :param tag: The component tag from the request path.

        :returns: An HTMLResponse with the component page, or a 404 page.
    """

    content = render_component_page(group_key, tag)
    if content is None:
        message = f"No component '{tag}' in group '{group_key}'."
        return _not_found_response(message)

    response = HTMLResponse(content=content, status_code=200)
    return response


def _not_found_response(message: str) -> HTMLResponse:
    """
        Build a styled 404 HTMLResponse.

        :param message: The human-readable not-found message.

        :returns: An HTMLResponse with status 404.
    """

    safe_message = html.escape(message)
    body = f"""
    <h1 data-testid="not-found">Not found</h1>
    <p>{safe_message}</p>
    <p><a href="/">Return to the component browser</a></p>"""

    content = page_shell(title="Not found", body_html=body)
    response = HTMLResponse(content=content, status_code=404)
    return response
