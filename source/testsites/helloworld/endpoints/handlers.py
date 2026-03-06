"""
    Endpoint handlers for the helloworld test site.

    This module defines the HTTP endpoint handlers for the helloworld
    site. Each handler is registered with the EndpointRegistry via the
    ``Endpoint.attach_at`` decorator so the Router can discover them
    at application startup.
"""

from automojo.webworks.endpoints.endpoint import Endpoint
from automojo.webworks.routing.request import Request
from automojo.webworks.routing.response import HTMLResponse
from automojo.webworks.routing.response import JSONResponse


@Endpoint.attach_at(path="/", methods=["GET"])
def hello_world(request: Request) -> HTMLResponse:
    """
        Handle GET requests to the root path.

        :param request: The incoming HTTP request.

        :returns: An HTMLResponse containing "Hello, World!" with status 200.
    """

    response = HTMLResponse(content="Hello, World!", status_code=200)

    return response


@Endpoint.attach_at(path="/health", methods=["GET"])
def health_check(request: Request) -> JSONResponse:
    """
        Handle GET requests to the health check path.

        :param request: The incoming HTTP request.

        :returns: A JSONResponse containing the health status with status 200.
    """

    content = {"status": "ok"}
    response = JSONResponse(content=content, status_code=200)

    return response
