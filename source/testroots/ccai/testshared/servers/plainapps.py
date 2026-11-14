"""
    Applications that are not web applications, for the tests of the WSGI
    application resolution: a plain ASGI application and a plain WSGI
    application. Importing this module establishes nothing.
"""

from typing import Any, Callable, Dict, Iterable, List


async def asgi_app(scope: Dict[str, Any], receive: Callable, send: Callable) -> None:
    """
        An ASGI application that answers every request with "asgi".
    """
    if scope["type"] == "lifespan":
        while True:
            message = await receive()
            if message["type"] == "lifespan.startup":
                await send({"type": "lifespan.startup.complete"})
            elif message["type"] == "lifespan.shutdown":
                await send({"type": "lifespan.shutdown.complete"})
                return

    await send({"type": "http.response.start", "status": 200, "headers": [(b"content-type", b"text/plain")]})
    await send({"type": "http.response.body", "body": b"asgi"})
    return


def wsgi_app(environ: Dict[str, Any], start_response: Callable) -> Iterable[bytes]:
    """
        A WSGI application that answers every request with "wsgi".
    """
    start_response("200 OK", [("Content-Type", "text/plain")])
    rtnval: List[bytes] = [b"wsgi"]
    return rtnval


def make_wsgi_app() -> Callable:
    """
        An application factory returning the WSGI application.
    """
    return wsgi_app


not_an_application = 42
