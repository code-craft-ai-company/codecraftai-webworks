"""
    layoutblueprint.py

    RestBlueprint serving the 'Layout & Containers' component group: its index page
    and the interactive per-component test pages.
"""

from ccai.webworks.endpoints.doc import Doc
from ccai.webworks.endpoints.restblueprint import RestBlueprint
from ccai.webworks.routing.request import Request
from ccai.webworks.routing.response import HTMLResponse

from testcomponents.endpoints.blueprints.groupserving import serve_component_page
from testcomponents.endpoints.blueprints.groupserving import serve_group_index


class LayoutBlueprint(RestBlueprint):
    """
        Serves the index and per-component test pages for the
        'Layout & Containers' component group.
    """

    base_path = "/components/layout"
    methods = ["GET"]
    tags = ["layout"]

    @RestBlueprint.attach_at(
        path="/components/layout",
        methods=["GET"],
        absolute=True,
        doc=Doc(
            summary="Layout & Containers group index",
            description="Browse the components in the Layout & Containers group.",
        ),
    )
    def group_index(request: Request) -> HTMLResponse:
        """
            Serve the Layout & Containers group index page.

            :param request: The incoming HTTP request.

            :returns: An HTMLResponse containing the group index page.
        """

        response = serve_group_index("layout")

        return response

    @RestBlueprint.attach_at(
        path="/components/layout/{tag}",
        methods=["GET"],
        absolute=True,
        doc=Doc(
            summary="Layout & Containers component test page",
            description="Interactive documentation and test page for a "
                        "single Layout & Containers component.",
        ),
    )
    def component_page(request: Request) -> HTMLResponse:
        """
            Serve an interactive component test page.

            :param request: The incoming HTTP request.

            :returns: An HTMLResponse containing the component test page.
        """

        tag = request.path_params.get("tag", "")
        response = serve_component_page("layout", tag)

        return response
