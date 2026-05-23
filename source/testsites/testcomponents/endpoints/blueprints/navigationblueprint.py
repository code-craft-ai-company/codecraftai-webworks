"""
    navigationblueprint.py

    RestBlueprint serving the 'Navigation' component group: its index page
    and the interactive per-component test pages.
"""

from automojo.webworks.endpoints.doc import Doc
from automojo.webworks.endpoints.restblueprint import RestBlueprint
from automojo.webworks.routing.request import Request
from automojo.webworks.routing.response import HTMLResponse

from testcomponents.endpoints.blueprints.groupserving import serve_component_page
from testcomponents.endpoints.blueprints.groupserving import serve_group_index


class NavigationBlueprint(RestBlueprint):
    """
        Serves the index and per-component test pages for the
        'Navigation' component group.
    """

    base_path = "/components/navigation"
    methods = ["GET"]
    tags = ["navigation"]

    @RestBlueprint.attach_at(
        path="/components/navigation",
        methods=["GET"],
        absolute=True,
        doc=Doc(
            summary="Navigation group index",
            description="Browse the components in the Navigation group.",
        ),
    )
    def group_index(request: Request) -> HTMLResponse:
        """
            Serve the Navigation group index page.

            :param request: The incoming HTTP request.

            :returns: An HTMLResponse containing the group index page.
        """

        response = serve_group_index("navigation")

        return response

    @RestBlueprint.attach_at(
        path="/components/navigation/{tag}",
        methods=["GET"],
        absolute=True,
        doc=Doc(
            summary="Navigation component test page",
            description="Interactive documentation and test page for a "
                        "single Navigation component.",
        ),
    )
    def component_page(request: Request) -> HTMLResponse:
        """
            Serve an interactive component test page.

            :param request: The incoming HTTP request.

            :returns: An HTMLResponse containing the component test page.
        """

        tag = request.path_params.get("tag", "")
        response = serve_component_page("navigation", tag)

        return response
