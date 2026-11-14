"""
    groupserving.py

    Shared serving helpers used by every group blueprint. The blueprints
    themselves are thin: they declare their routes and delegate to these
    functions, so the index/component rendering logic lives in one place.
"""

from ccai.webworks.routing.response import HTMLResponse

from testcomponents.rendering import render_component_page
from testcomponents.rendering import render_group_index
from testcomponents.rendering import render_not_found


def serve_group_index(group_key: str) -> HTMLResponse:
    """
        Serve the index page for a component group.

        :param group_key: The group key to render.

        :returns: An HTMLResponse with the group index, or a 404 page.
    """

    content = render_group_index(group_key)
    if content is None:
        response = not_found_response(f"Unknown component group '{group_key}'.")
        return response

    response = HTMLResponse(content=content, status_code=200)
    return response


def serve_component_page(group_key: str, tag: str, example_key: "str | None" = None) -> HTMLResponse:
    """
        Serve the interactive test page for a single component.

        :param group_key: The owning group key.
        :param tag: The component tag from the request path.
        :param example_key: The ``?example=`` gallery key, or None for the first.

        :returns: An HTMLResponse with the component page, or a 404 page.
    """

    content = render_component_page(group_key, tag, example_key=example_key)
    if content is None:
        message = f"No component '{tag}' in group '{group_key}'."
        response = not_found_response(message)
        return response

    response = HTMLResponse(content=content, status_code=200)
    return response


def not_found_response(message: str) -> HTMLResponse:
    """
        Build the styled 404 HTMLResponse.

        :param message: The plain-text not-found message (escaped when rendered).

        :returns: An HTMLResponse with status 404.
    """

    content = render_not_found(message)
    response = HTMLResponse(content=content, status_code=404)
    return response
