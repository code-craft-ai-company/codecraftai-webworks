"""
    buttonsblueprint.py

    RestBlueprint serving the 'Buttons & Actions' component group: its index page
    and the interactive per-component test pages.
"""

from ccai.webworks.endpoints.doc import Doc
from ccai.webworks.endpoints.restblueprint import RestBlueprint
from ccai.webworks.routing.request import Request
from ccai.webworks.routing.response import HTMLResponse

from testcomponents.endpoints.blueprints.groupserving import serve_component_page
from testcomponents.endpoints.blueprints.groupserving import serve_group_index


class ButtonsBlueprint(RestBlueprint):
    """
        Serves the index and per-component test pages for the
        'Buttons & Actions' component group.
    """

    base_path = "/components/buttons"
    methods = ["GET"]
    tags = ["buttons"]

    @staticmethod
    @RestBlueprint.attach_at(
        path="/components/buttons",
        methods=["GET"],
        absolute=True,
        doc=Doc(
            summary="Buttons & Actions group index",
            description="Browse the components in the Buttons & Actions group.",
        ),
    )
    def group_index(request: Request) -> HTMLResponse:
        """
            Serve the Buttons & Actions group index page.

            :param request: The incoming HTTP request.

            :returns: An HTMLResponse containing the group index page.
        """

        response = serve_group_index("buttons")

        return response

    @staticmethod
    @RestBlueprint.attach_at(
        path="/components/buttons/{tag}",
        methods=["GET"],
        absolute=True,
        doc=Doc(
            summary="Buttons & Actions component test page",
            description="Interactive documentation and test page for a "
                        "single Buttons & Actions component.",
        ),
    )
    def component_page(request: Request) -> HTMLResponse:
        """
            Serve an interactive component test page.

            :param request: The incoming HTTP request.

            :returns: An HTMLResponse containing the component test page.
        """

        tag = request.path_params.get("tag", "")
        response = serve_component_page("buttons", tag)

        return response
