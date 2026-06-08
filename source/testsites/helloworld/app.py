"""
    Application entry point for the helloworld test site.

    This module establishes a web application persona under
    ``.output/testsites/helloworld`` and uses the ``ThisWebApplicationSingleton``
    to access the fully wired ASGI application. The module-level ``app``
    variable is the ASGI application instance ready to be served by any
    ASGI server.
"""

import os

from ccai.webworks.webapplication import establish_webapp_persona
from ccai.webworks.wellknown import ThisWebApplicationSingleton

# Import endpoint handlers to trigger Endpoint.attach_at registration
from helloworld.endpoints import handlers  # noqa: F401


# Establish the persona with a presence directory under .output/testsites
_PRESENCE_DIR = os.path.join(".output", "testsites", "helloworld")

webapp = establish_webapp_persona(
    name="helloworld",
    logger_name="helloworld",
    log_basename="helloworld",
    presence_dir=_PRESENCE_DIR,
)

webapp.startup()

# The ASGI application instance for serving
app = ThisWebApplicationSingleton().asgi_app


def run_development_server(
    host: str = "127.0.0.1",
    port: int = 8000,
    debug: bool = True,
    reload: bool = True,
) -> None:
    """
        Start the helloworld site using the ASGI development server.

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
