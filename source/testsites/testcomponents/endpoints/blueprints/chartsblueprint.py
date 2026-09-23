"""
    chartsblueprint.py

    RestBlueprint serving the 'Project & SCM Charts' component group: its index page
    and the interactive per-component test pages.
"""

from ccai.webworks.endpoints.doc import Doc
from ccai.webworks.endpoints.restblueprint import RestBlueprint
from ccai.webworks.routing.request import Request
from ccai.webworks.routing.response import HTMLResponse

from testcomponents.endpoints.blueprints.groupserving import serve_component_page
from testcomponents.endpoints.blueprints.groupserving import serve_group_index


class ChartsBlueprint(RestBlueprint):
    """
        Serves the index and per-component test pages for the
        'Project & SCM Charts' component group.
    """

    base_path = "/components/charts"
    methods = ["GET"]
    tags = ["charts"]

    @staticmethod
    @RestBlueprint.attach_at(
        path="/components/charts",
        methods=["GET"],
        absolute=True,
        doc=Doc(
            summary="Project & SCM Charts group index",
            description="Browse the components in the Project & SCM Charts group.",
        ),
    )
    def group_index(request: Request) -> HTMLResponse:
        """
            Serve the Project & SCM Charts group index page.

            :param request: The incoming HTTP request.

            :returns: An HTMLResponse containing the group index page.
        """

        response = serve_group_index("charts")

        return response

    @staticmethod
    @RestBlueprint.attach_at(
        path="/components/charts/{tag}",
        methods=["GET"],
        absolute=True,
        doc=Doc(
            summary="Project & SCM Charts component test page",
            description="Interactive documentation and test page for a "
                        "single Project & SCM Charts component.",
        ),
    )
    def component_page(request: Request) -> HTMLResponse:
        """
            Serve an interactive component test page.

            :param request: The incoming HTTP request.

            :returns: An HTMLResponse containing the component test page.
        """

        tag = request.path_params.get("tag", "")
        response = serve_component_page("charts", tag)

        return response
