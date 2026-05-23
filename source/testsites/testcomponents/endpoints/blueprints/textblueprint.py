"""
    textblueprint.py

    RestBlueprint serving the 'Text & Data Entry' component group: its index page
    and the interactive per-component test pages.
"""

from automojo.webworks.endpoints.doc import Doc
from automojo.webworks.endpoints.restblueprint import RestBlueprint
from automojo.webworks.routing.request import Request
from automojo.webworks.routing.response import HTMLResponse

from testcomponents.endpoints.blueprints.groupserving import serve_component_page
from testcomponents.endpoints.blueprints.groupserving import serve_group_index


class TextBlueprint(RestBlueprint):
    """
        Serves the index and per-component test pages for the
        'Text & Data Entry' component group.
    """

    base_path = "/components/text"
    methods = ["GET"]
    tags = ["text"]

    @RestBlueprint.attach_at(
        path="/components/text",
        methods=["GET"],
        absolute=True,
        doc=Doc(
            summary="Text & Data Entry group index",
            description="Browse the components in the Text & Data Entry group.",
        ),
    )
    def group_index(request: Request) -> HTMLResponse:
        """
            Serve the Text & Data Entry group index page.

            :param request: The incoming HTTP request.

            :returns: An HTMLResponse containing the group index page.
        """

        response = serve_group_index("text")

        return response

    @RestBlueprint.attach_at(
        path="/components/text/{tag}",
        methods=["GET"],
        absolute=True,
        doc=Doc(
            summary="Text & Data Entry component test page",
            description="Interactive documentation and test page for a "
                        "single Text & Data Entry component.",
        ),
    )
    def component_page(request: Request) -> HTMLResponse:
        """
            Serve an interactive component test page.

            :param request: The incoming HTTP request.

            :returns: An HTMLResponse containing the component test page.
        """

        tag = request.path_params.get("tag", "")
        response = serve_component_page("text", tag)

        return response
