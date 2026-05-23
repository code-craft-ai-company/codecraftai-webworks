"""
    selectionblueprint.py

    RestBlueprint serving the 'Selection & Pickers' component group: its index page
    and the interactive per-component test pages.
"""

from automojo.webworks.endpoints.doc import Doc
from automojo.webworks.endpoints.restblueprint import RestBlueprint
from automojo.webworks.routing.request import Request
from automojo.webworks.routing.response import HTMLResponse

from testcomponents.endpoints.blueprints.groupserving import serve_component_page
from testcomponents.endpoints.blueprints.groupserving import serve_group_index


class SelectionBlueprint(RestBlueprint):
    """
        Serves the index and per-component test pages for the
        'Selection & Pickers' component group.
    """

    base_path = "/components/selection"
    methods = ["GET"]
    tags = ["selection"]

    @RestBlueprint.attach_at(
        path="/components/selection",
        methods=["GET"],
        absolute=True,
        doc=Doc(
            summary="Selection & Pickers group index",
            description="Browse the components in the Selection & Pickers group.",
        ),
    )
    def group_index(request: Request) -> HTMLResponse:
        """
            Serve the Selection & Pickers group index page.

            :param request: The incoming HTTP request.

            :returns: An HTMLResponse containing the group index page.
        """

        response = serve_group_index("selection")

        return response

    @RestBlueprint.attach_at(
        path="/components/selection/{tag}",
        methods=["GET"],
        absolute=True,
        doc=Doc(
            summary="Selection & Pickers component test page",
            description="Interactive documentation and test page for a "
                        "single Selection & Pickers component.",
        ),
    )
    def component_page(request: Request) -> HTMLResponse:
        """
            Serve an interactive component test page.

            :param request: The incoming HTTP request.

            :returns: An HTMLResponse containing the component test page.
        """

        tag = request.path_params.get("tag", "")
        response = serve_component_page("selection", tag)

        return response
