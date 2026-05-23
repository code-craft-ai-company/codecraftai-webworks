"""
    overlaysblueprint.py

    RestBlueprint serving the 'Dialogs & Overlays' component group: its index page
    and the interactive per-component test pages.
"""

from automojo.webworks.endpoints.doc import Doc
from automojo.webworks.endpoints.restblueprint import RestBlueprint
from automojo.webworks.routing.request import Request
from automojo.webworks.routing.response import HTMLResponse

from testcomponents.endpoints.blueprints.groupserving import serve_component_page
from testcomponents.endpoints.blueprints.groupserving import serve_group_index


class OverlaysBlueprint(RestBlueprint):
    """
        Serves the index and per-component test pages for the
        'Dialogs & Overlays' component group.
    """

    base_path = "/components/overlays"
    methods = ["GET"]
    tags = ["overlays"]

    @RestBlueprint.attach_at(
        path="/components/overlays",
        methods=["GET"],
        absolute=True,
        doc=Doc(
            summary="Dialogs & Overlays group index",
            description="Browse the components in the Dialogs & Overlays group.",
        ),
    )
    def group_index(request: Request) -> HTMLResponse:
        """
            Serve the Dialogs & Overlays group index page.

            :param request: The incoming HTTP request.

            :returns: An HTMLResponse containing the group index page.
        """

        response = serve_group_index("overlays")

        return response

    @RestBlueprint.attach_at(
        path="/components/overlays/{tag}",
        methods=["GET"],
        absolute=True,
        doc=Doc(
            summary="Dialogs & Overlays component test page",
            description="Interactive documentation and test page for a "
                        "single Dialogs & Overlays component.",
        ),
    )
    def component_page(request: Request) -> HTMLResponse:
        """
            Serve an interactive component test page.

            :param request: The incoming HTTP request.

            :returns: An HTMLResponse containing the component test page.
        """

        tag = request.path_params.get("tag", "")
        response = serve_component_page("overlays", tag)

        return response
