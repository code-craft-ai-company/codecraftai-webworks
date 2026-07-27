"""
    Application entry point for the testcomponents test site.

    This site exists solely to exercise and document the codecraftai-webworks
    mj-* web component library. It serves a browse-by-group landing page
    and an interactive test/documentation page for every component. The
    component groups are served by dedicated RestBlueprint classes and the
    site requires no authentication.

    The module-level ``app`` variable is the ASGI application instance
    ready to be served by any ASGI server.
"""

import os

from ccai.webworks.webapplication import establish_webapp_persona
from ccai.webworks.webapplication import reset_webapp_persona
from ccai.webworks.wellknown import ThisWebApplicationSingleton

# Importing the handlers module triggers Endpoint.attach_at registration
# for the landing page and the static asset route.
from testcomponents.endpoints import handlers  # noqa: F401

# Importing the blueprints package triggers RestBlueprint.attach_at
# registration for every component group blueprint.
from testcomponents.endpoints import blueprints  # noqa: F401


# Establish the persona with a presence directory under .output/testsites.
_PRESENCE_DIR = os.path.join(".output", "testsites", "testcomponents")

# These sites are fixtures, and a test run imports all three into one
# process. Establishing a persona and registering endpoints are
# process-global, so each site claims them from whichever site ran
# before it. The reset has to sit here rather than in a test package's
# __init__: discovery imports every package before any module, so a
# reset there runs long before this line.
reset_webapp_persona()

webapp = establish_webapp_persona(
    name="testcomponents",
    logger_name="testcomponents",
    log_basename="testcomponents",
    presence_dir=_PRESENCE_DIR,
)

webapp.startup()

# The ASGI application instance for serving.
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
        Start the testcomponents site using the ASGI development server.

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
        watch_patterns=["**/*.py", "**/*.html", "**/*.js", "**/*.css"],
    )

    server.serve_forever(host=host, port=port)

    return


if __name__ == "__main__":
    run_development_server()
