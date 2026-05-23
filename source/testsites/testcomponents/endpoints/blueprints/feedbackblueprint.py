"""
    feedbackblueprint.py

    RestBlueprint serving the 'Feedback & Status' component group: its index page
    and the interactive per-component test pages.
"""

from automojo.webworks.endpoints.doc import Doc
from automojo.webworks.endpoints.restblueprint import RestBlueprint
from automojo.webworks.routing.request import Request
from automojo.webworks.routing.response import HTMLResponse

from testcomponents.endpoints.blueprints.groupserving import serve_component_page
from testcomponents.endpoints.blueprints.groupserving import serve_group_index


class FeedbackBlueprint(RestBlueprint):
    """
        Serves the index and per-component test pages for the
        'Feedback & Status' component group.
    """

    base_path = "/components/feedback"
    methods = ["GET"]
    tags = ["feedback"]

    @RestBlueprint.attach_at(
        path="/components/feedback",
        methods=["GET"],
        absolute=True,
        doc=Doc(
            summary="Feedback & Status group index",
            description="Browse the components in the Feedback & Status group.",
        ),
    )
    def group_index(request: Request) -> HTMLResponse:
        """
            Serve the Feedback & Status group index page.

            :param request: The incoming HTTP request.

            :returns: An HTMLResponse containing the group index page.
        """

        response = serve_group_index("feedback")

        return response

    @RestBlueprint.attach_at(
        path="/components/feedback/{tag}",
        methods=["GET"],
        absolute=True,
        doc=Doc(
            summary="Feedback & Status component test page",
            description="Interactive documentation and test page for a "
                        "single Feedback & Status component.",
        ),
    )
    def component_page(request: Request) -> HTMLResponse:
        """
            Serve an interactive component test page.

            :param request: The incoming HTTP request.

            :returns: An HTMLResponse containing the component test page.
        """

        tag = request.path_params.get("tag", "")
        response = serve_component_page("feedback", tag)

        return response
