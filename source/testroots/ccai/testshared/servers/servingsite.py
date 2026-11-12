"""
    A web application the server tests serve over WSGI and with the
    production server.

    Importing this module establishes the web application persona, which is
    process-global, so it is imported in a server child process only, never
    in the test process (see the "testsites share the process-global
    persona" note in AGENTS.md).

    Environment of the child process:

    - SERVINGSITE_PRESENCE_DIR: presence directory of the persona (required).
    - SERVINGSITE_EVENTS: file the lifespan handlers append
      "startup <pid>" / "shutdown <pid>" lines to, and /slow a
      "slow-start <pid>" line when it begins (optional).
    - SERVINGSITE_FAIL_STARTUP: when "1", the lifespan startup handler raises.

    The application's request body limit is set with a ``servingsite.json``
    file in the presence directory: {"server": {"max_request_body_size": N}}.

    Routes:

    ======================== =====================================================
    GET  /hello              "hello" as text
    POST /echo               JSON with the length and the text of the body
    GET  /stream             "first" now, "second" 1.5 seconds later (streamed)
    GET  /cookies            two Set-Cookie headers
    GET  /error              a handler that raises RuntimeError (500)
    GET  /teapot             raises an HTTPException(418), answered by the
                             dispatcher's error handling
    GET  /slow?seconds=N     answers after N seconds
    GET  /pid                the pid of the process that served it
    GET  /request-id         the X-Request-ID header the handler saw, and the
                             request ID of the production server's context
    GET  /private            needs Basic authentication (user "alice", "secret")
    ======================== =====================================================
"""

import asyncio
import os
import time

from typing import Optional

from ccai.webworks.authentication.basic import BasicAuthenticator
from ccai.webworks.authentication.core import Principal
from ccai.webworks.endpoints.accesspolicy import AccessPolicy
from ccai.webworks.routing.exceptions import HTTPException
from ccai.webworks.routing.request import Request
from ccai.webworks.routing.response import JSONResponse, Response, StreamingResponse
from ccai.webworks.webapplication import establish_webapp_persona
from ccai.webworks.webapplication import reset_webapp_persona


USERNAME = "alice"
PASSWORD = "secret"


class _UserList:
    """
        The identity provider of the Basic authenticator: one user.
    """

    async def validate_credentials(self, username: str, password: str) -> Optional[Principal]:
        rtnval = None
        if username == USERNAME and password == PASSWORD:
            rtnval = Principal(identifier=username)
        return rtnval

    async def get_principal(self, identifier: str) -> Optional[Principal]:
        rtnval = None
        if identifier == USERNAME:
            rtnval = Principal(identifier=identifier)
        return rtnval


def _record_event(event: str) -> None:
    """
        Append a lifespan event to the events file, when one is configured.

        :param event: The event name.
    """
    events_path = os.environ.get("SERVINGSITE_EVENTS")
    if events_path:
        with open(events_path, "a", encoding="utf-8") as events_file:
            events_file.write(f"{event} {os.getpid()}\n")
    return


reset_webapp_persona()

webapp = establish_webapp_persona(
    name="servingsite",
    logger_name="servingsite",
    log_basename="servingsite",
    presence_dir=os.environ["SERVINGSITE_PRESENCE_DIR"],
)


@webapp.attach_route("/hello", methods=["GET"])
def hello(request: Request) -> Response:
    return Response(status_code=200, headers={"Content-Type": "text/plain; charset=utf-8"}, body=b"hello")


@webapp.attach_route("/echo", methods=["POST"])
def echo(request: Request) -> Response:
    body = request.body
    return JSONResponse({"length": len(body), "text": body.decode("utf-8", errors="replace")})


@webapp.attach_route("/stream", methods=["GET"])
async def stream(request: Request) -> Response:
    async def produce():
        yield b"first\n"
        await asyncio.sleep(1.5)
        yield b"second\n"
    return StreamingResponse(produce(), media_type="text/plain")


@webapp.attach_route("/cookies", methods=["GET"])
def cookies(request: Request) -> Response:
    response = Response(status_code=200, headers={"Content-Type": "text/plain; charset=utf-8"}, body=b"cookies")
    response.set_cookie("first", "1")
    response.set_cookie("second", "2")
    return response


@webapp.attach_route("/error", methods=["GET"])
def error(request: Request) -> Response:
    raise RuntimeError("the handler failed on purpose")


@webapp.attach_route("/teapot", methods=["GET"])
def teapot(request: Request) -> Response:
    raise HTTPException(status_code=418, detail="I'm a teapot")


@webapp.attach_route("/slow", methods=["GET"])
def slow(request: Request) -> Response:
    _record_event("slow-start")
    seconds = float(request.query_params.get("seconds", "1"))
    time.sleep(seconds)
    return Response(status_code=200, headers={"Content-Type": "text/plain; charset=utf-8"}, body=b"slow done")


@webapp.attach_route("/pid", methods=["GET"])
def pid(request: Request) -> Response:
    return JSONResponse({"pid": os.getpid()})


@webapp.attach_route("/request-id", methods=["GET"])
def request_id(request: Request) -> Response:
    from ccai.webworks.prodserver.productionmiddleware import current_request_id
    return JSONResponse({
        "header": request.headers.get("X-Request-Id"),
        "context": current_request_id.get(),
    })


@webapp.attach_route("/private", methods=["GET"], access_policy=AccessPolicy(require_auth=True))
def private(request: Request) -> Response:
    return Response(status_code=200, headers={"Content-Type": "text/plain; charset=utf-8"}, body=b"private")


webapp.startup()


async def _on_startup() -> None:
    _record_event("startup")
    if os.environ.get("SERVINGSITE_FAIL_STARTUP") == "1":
        raise RuntimeError("the startup handler failed on purpose")
    return


async def _on_shutdown() -> None:
    _record_event("shutdown")
    return


webapp.asgi_app.lifespan_handler.on_startup(_on_startup)
webapp.asgi_app.lifespan_handler.on_shutdown(_on_shutdown)

webapp.register_authenticator(BasicAuthenticator(identity_provider=_UserList(), realm="servingsite"))
webapp.configure_auth_middleware(optional_patterns=["/**"], realm="servingsite")

# The ASGI application, as a site module exports it
app = webapp.asgi_app
