"""
    datablueprint.py

    RestBlueprint serving the 'Tables, Lists & Data' component group: its index page
    and the interactive per-component test pages.
"""

from automojo.webworks.endpoints.doc import Doc
from automojo.webworks.endpoints.restblueprint import RestBlueprint
from automojo.webworks.routing.request import Request
from automojo.webworks.routing.response import HTMLResponse

from testcomponents.endpoints.blueprints.groupserving import serve_component_page
from testcomponents.endpoints.blueprints.groupserving import serve_group_index


class DataBlueprint(RestBlueprint):
    """
        Serves the index and per-component test pages for the
        'Tables, Lists & Data' component group.
    """

    base_path = "/components/data"
    methods = ["GET"]
    tags = ["data"]

    @RestBlueprint.attach_at(
        path="/components/data",
        methods=["GET"],
        absolute=True,
        doc=Doc(
            summary="Tables, Lists & Data group index",
            description="Browse the components in the Tables, Lists & Data group.",
        ),
    )
    def group_index(request: Request) -> HTMLResponse:
        """
            Serve the Tables, Lists & Data group index page.

            :param request: The incoming HTTP request.

            :returns: An HTMLResponse containing the group index page.
        """

        response = serve_group_index("data")

        return response

    @RestBlueprint.attach_at(
        path="/components/data/{tag}",
        methods=["GET"],
        absolute=True,
        doc=Doc(
            summary="Tables, Lists & Data component test page",
            description="Interactive documentation and test page for a "
                        "single Tables, Lists & Data component.",
        ),
    )
    def component_page(request: Request) -> HTMLResponse:
        """
            Serve an interactive component test page.

            :param request: The incoming HTTP request.

            :returns: An HTMLResponse containing the component test page.
        """

        tag = request.path_params.get("tag", "")
        response = serve_component_page("data", tag)

        return response
