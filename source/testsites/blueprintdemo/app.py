"""
    Application entry point for the blueprintdemo test site.

    This module establishes a web application persona under
    ``.output/testsites/blueprintdemo`` and uses the
    ``ThisWebApplicationSingleton`` to access the fully wired ASGI
    application with interactive API documentation. The module-level
    ``app`` variable is the ASGI application instance ready to be served
    by any ASGI server.
"""

import os

from ccai.webworks.endpoints.registry import EndpointRegistry
from ccai.webworks.openapi.configuration import OpenAPIInfo
from ccai.webworks.openapi.generator import OpenAPIGenerator
from ccai.webworks.openapi.swaggerui import SwaggerUIBlueprint
from ccai.webworks.routing.request import Request
from ccai.webworks.routing.response import HTMLResponse
from ccai.webworks.routing.response import JSONResponse
from ccai.webworks.routing.response import Response
from ccai.webworks.webapplication import establish_webapp_persona
from ccai.webworks.webapplication import reset_webapp_persona
from ccai.webworks.wellknown import ThisWebApplicationSingleton

# Import endpoint handlers to trigger RestBlueprint.attach_at registration
from blueprintdemo.endpoints import handlers  # noqa: F401


# Establish the persona with a presence directory under .output/testsites
_PRESENCE_DIR = os.path.join(".output", "testsites", "blueprintdemo")

# These sites are fixtures, and a test run imports all three into one
# process. Establishing a persona and registering endpoints are
# process-global, so each site claims them from whichever site ran
# before it. The reset has to sit here rather than in a test package's
# __init__: discovery imports every package before any module, so a
# reset there runs long before this line.
reset_webapp_persona()

webapp = establish_webapp_persona(
    name="blueprintdemo",
    logger_name="blueprintdemo",
    log_basename="blueprintdemo",
    presence_dir=_PRESENCE_DIR,
)

# Set up OpenAPI generator and Swagger UI
openapi_info = OpenAPIInfo(
    title="Blueprint Demo API",
    version="1.0.0",
    description="Demonstrates RestBlueprint patterns with Swagger UI.",
)

openapi_generator = OpenAPIGenerator(
    registry=EndpointRegistry,
    info=openapi_info,
    derive_tags_from_path=True,
)

swagger_ui = SwaggerUIBlueprint(
    generator=openapi_generator,
    ui_path="/docs",
    spec_path="/openapi.json",
)


# Register Swagger UI endpoints via attach_route before startup so they
# are queued and flushed into the Router during setup_infrastructure.

@webapp.attach_route("/docs", methods=["GET"])
def _serve_swagger_ui(request: Request) -> HTMLResponse:
    """
        Wrapper handler that serves the Swagger UI HTML page as a proper Response.
    """
    html_content, status_code, _ = swagger_ui.serve_ui()
    return HTMLResponse(content=html_content, status_code=status_code)


@webapp.attach_route("/openapi.json", methods=["GET"])
def _serve_openapi_spec(request: Request) -> JSONResponse:
    """
        Wrapper handler that serves the OpenAPI spec as a proper JSONResponse.
    """
    import json as _json
    json_str, status_code, _ = swagger_ui.serve_spec()
    spec_dict = _json.loads(json_str)
    return JSONResponse(content=spec_dict, status_code=status_code)


@webapp.attach_route("/_swagger/{filename}", methods=["GET"])
def _serve_swagger_static(request: Request) -> Response:
    """
        Wrapper handler that serves bundled Swagger UI static assets.

        Delegates to the SwaggerUIBlueprint.serve_static method which
        resolves the requested file from the vendored asset directory
        and returns the content with appropriate Content-Type and
        Cache-Control headers.
    """
    filename = request.path_params.get("filename", "")
    content_bytes, status_code, headers = swagger_ui.serve_static(filename)
    return Response(status_code=status_code, headers=headers, body=content_bytes)


webapp.startup()

# The ASGI application instance for serving
app = ThisWebApplicationSingleton().asgi_app

# The router and dispatcher the application built during startup.
# Exported because the wiring tests assert against them directly.
router = webapp.router
dispatcher = webapp.dispatcher


def run_development_server(
    host: str = "127.0.0.1",
    port: int = 8000,
    debug: bool = True,
    reload: bool = True,
) -> None:
    """
        Start the blueprintdemo site using the ASGI development server.

        The development server binds a TCP socket, accepts HTTP/1.1
        connections, and invokes the ASGI application.  It supports
        lifespan events, keep-alive connections, graceful shutdown
        via SIGINT/SIGTERM, and optional auto-reload on file changes.

        :param host: The host address to bind to.
        :param port: The port number to bind to.
        :param debug: Whether to enable debug mode with verbose error pages.
        :param reload: Whether to enable auto-reload on file changes.
    """

    from ccai.webworks.devexp.server.devserver import DevelopmentServer

    server = DevelopmentServer(
        app=app,
        debug=debug,
        reload=reload,
        watch_patterns=["**/*.py", "**/*.html"],
    )

    server.serve_forever(host=host, port=port)

    return


if __name__ == "__main__":
    run_development_server()
