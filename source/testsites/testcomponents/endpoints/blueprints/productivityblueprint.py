"""
    productivityblueprint.py

    RestBlueprint serving the 'Application & Productivity' component group: its index page
    and the interactive per-component test pages.
"""

from automojo.webworks.endpoints.doc import Doc
from automojo.webworks.endpoints.restblueprint import RestBlueprint
from automojo.webworks.routing.request import Request
from automojo.webworks.routing.response import HTMLResponse

from testcomponents.endpoints.blueprints.groupserving import serve_component_page
from testcomponents.endpoints.blueprints.groupserving import serve_group_index


class ProductivityBlueprint(RestBlueprint):
    """
        Serves the index and per-component test pages for the
        'Application & Productivity' component group.
    """

    base_path = "/components/productivity"
    methods = ["GET"]
    tags = ["productivity"]

    @RestBlueprint.attach_at(
        path="/components/productivity",
        methods=["GET"],
        absolute=True,
        doc=Doc(
            summary="Application & Productivity group index",
            description="Browse the components in the Application & Productivity group.",
        ),
    )
    def group_index(request: Request) -> HTMLResponse:
        """
            Serve the Application & Productivity group index page.

            :param request: The incoming HTTP request.

            :returns: An HTMLResponse containing the group index page.
        """

        response = serve_group_index("productivity")

        return response

    @RestBlueprint.attach_at(
        path="/components/productivity/{tag}",
        methods=["GET"],
        absolute=True,
        doc=Doc(
            summary="Application & Productivity component test page",
            description="Interactive documentation and test page for a "
                        "single Application & Productivity component.",
        ),
    )
    def component_page(request: Request) -> HTMLResponse:
        """
            Serve an interactive component test page.

            :param request: The incoming HTTP request.

            :returns: An HTMLResponse containing the component test page.
        """

        tag = request.path_params.get("tag", "")
        response = serve_component_page("productivity", tag)

        return response
