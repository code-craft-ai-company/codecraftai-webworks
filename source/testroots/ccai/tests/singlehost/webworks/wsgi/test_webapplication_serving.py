"""
    Tests for serving a WebApplication over WSGI.

    ``WebApplication.wsgi_app`` is served by the built-in WSGIServer in a
    child process, and the tests talk to it over a real socket with
    http.client. The application is ccai.testshared.servers.servingsite: it
    has authentication middleware, a custom error handler, lifespan handlers,
    a streaming route and a request body limit from its configuration, so
    each of those is checked on the WSGI path. A parity test serves the same
    requests through ``asgi_app`` and ``wsgi_app`` and compares the answers.

    The documented entry point for external servers,
    ``gunicorn 'ccai.webworks.wsgi.application:get_wsgi_application()'``, is
    resolved the way Gunicorn resolves it and served by the built-in server.
"""

import base64
import functools
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

from typing import Callable, Dict, List, Optional

from ccai.errors.exceptions import SkipError

from ccai.testshared.servers.serverprocess import ServerProcess, child_environment, find_free_port


# The child serves servingsite's wsgi_app with the built-in server.
# argv: port, workers
WSGI_SERVER_CODE = r"""
import sys
from ccai.webworks.wsgi import ServerConfig, WSGIServer
import ccai.testshared.servers.servingsite as site

config = ServerConfig(host="127.0.0.1", port=int(sys.argv[1]), workers=int(sys.argv[2]), threads=4,
                      timeout=10, graceful_timeout=10, access_log=False)
WSGIServer(site.webapp.wsgi_app, config).serve_forever()
"""

# The child resolves the application spec the way Gunicorn does
# ('module:expression', the expression called when it is a call) and serves
# what it returns. argv: port, spec
GUNICORN_STYLE_CODE = r"""
import importlib
import sys
from ccai.webworks.wsgi import ServerConfig, WSGIServer

module_name, expression = sys.argv[2].split(":", 1)
module = importlib.import_module(module_name)
if expression.endswith("()"):
    application = getattr(module, expression[:-2])()
else:
    application = getattr(module, expression)

config = ServerConfig(host="127.0.0.1", port=int(sys.argv[1]), workers=1, threads=2, access_log=False)
WSGIServer(application, config).serve_forever()
"""

# The child serves the same requests through asgi_app and wsgi_app with the
# in-process test client and prints both sets of answers.
PARITY_PROBE_CODE = r"""
import json
from ccai.webworks.devexp.testing.testclient import TestClient
import ccai.testshared.servers.servingsite as site

AUTH = {"Authorization": "Basic YWxpY2U6c2VjcmV0"}
REQUESTS = [
    ("GET", "/hello", None, {}),
    ("POST", "/echo", b"posted body", {"Content-Type": "text/plain"}),
    ("POST", "/echo", b"x" * 100, {"Content-Type": "text/plain"}),
    ("GET", "/cookies", None, {}),
    ("GET", "/error", None, {}),
    ("GET", "/teapot", None, {}),
    ("GET", "/private", None, {}),
    ("GET", "/private", None, AUTH),
    ("GET", "/missing", None, {}),
    ("DELETE", "/hello", None, {}),
]

def run(client):
    answers = []
    for method, path, body, headers in REQUESTS:
        response = client.request(method, path, content=body, headers=headers)
        answers.append([method, path, response.status_code, response.body.decode("utf-8", "replace")])
    return answers

with TestClient(site.app, transport="asgi", raise_app_exceptions=False) as asgi_client:
    asgi_answers = run(asgi_client)
with TestClient(site.webapp.wsgi_app, transport="wsgi", raise_app_exceptions=False) as wsgi_client:
    wsgi_answers = run(wsgi_client)
site.webapp.wsgi_app.shutdown()
print("PARITY=" + json.dumps({"asgi": asgi_answers, "wsgi": wsgi_answers}))
"""

# The child serves one request through wsgi_app, then shuts the WebApplication
# down and prints the lifespan events recorded before and after, and the
# status of a request that arrives after the shutdown. argv: events path
WEBAPP_SHUTDOWN_PROBE_CODE = r"""
import sys
from wsgiref.util import setup_testing_defaults
import ccai.testshared.servers.servingsite as site

def events():
    with open(sys.argv[1], encoding="utf-8") as events_file:
        return ",".join(line.split()[0] for line in events_file if line.strip())

def call(application, path):
    environ = {"PATH_INFO": path, "REQUEST_METHOD": "GET"}
    setup_testing_defaults(environ)
    statuses = []
    body = application(environ, lambda status, headers, exc_info=None: statuses.append(status))
    try:
        for _ in body:
            pass
    finally:
        if hasattr(body, "close"):
            body.close()
    return statuses[0].split()[0]

bridge = site.webapp.wsgi_app
print("STATUS=" + call(bridge, "/hello"))
print("BEFORE=" + events())
site.webapp.shutdown()
print("AFTER=" + events())
print("LATE=" + call(bridge, "/hello"))
"""

AUTH_HEADER = "Basic " + base64.b64encode(b"alice:secret").decode("ascii")


# Directories the tests created; removed by cleanup_directories() after each test
_created_directories: List[str] = []


def _make_directory(prefix: str) -> str:
    """
        Create a temporary directory that is removed after the test.
    """
    directory = tempfile.mkdtemp(prefix=prefix)
    _created_directories.append(directory)
    return directory


def removes_its_directories(test_function: Callable[[], None]) -> Callable[[], None]:
    """
        Remove the temporary directories a test created when it ends.
    """
    @functools.wraps(test_function)
    def run_test() -> None:
        try:
            test_function()
        finally:
            while len(_created_directories) > 0:
                shutil.rmtree(_created_directories.pop(), ignore_errors=True)
        return

    return run_test


def _presence_dir(max_request_body_size: Optional[int] = None) -> str:
    """
        Create a presence directory for servingsite.

        :param max_request_body_size: The application's body limit, written to
            its configuration file when given.

        :returns: The directory.
    """
    presence_dir = _make_directory("servingsite-")
    if max_request_body_size is not None:
        config_path = os.path.join(presence_dir, "servingsite.json")
        with open(config_path, "w", encoding="utf-8") as config_file:
            json.dump({"server": {"max_request_body_size": max_request_body_size}}, config_file)
    return presence_dir


def _require_fork() -> None:
    """
        The built-in server forks its workers in these tests.
    """
    if not hasattr(os, "fork"):
        raise SkipError("The built-in WSGI server serves a WebApplication with forked workers here.")
    return


def _wsgi_server(workers: int = 1, env: Optional[Dict[str, str]] = None, max_request_body_size: Optional[int] = None) -> ServerProcess:
    """
        Describe a WSGIServer child serving servingsite.
    """
    port = find_free_port()
    child_env = {"SERVINGSITE_PRESENCE_DIR": _presence_dir(max_request_body_size)}
    child_env.update(env or {})
    rtnval = ServerProcess(WSGI_SERVER_CODE, port, args=[str(port), str(workers)], env=child_env)
    return rtnval


def _wait_for_lines(path: str, prefix: str, count: int, timeout: float = 30.0) -> List[str]:
    """
        Wait until a file holds at least count lines starting with prefix.
    """
    deadline = time.monotonic() + timeout
    lines: List[str] = []

    while time.monotonic() < deadline:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as events_file:
                lines = [line.strip() for line in events_file if line.startswith(prefix)]
            if len(lines) >= count:
                return lines
        time.sleep(0.05)

    errmsg = f"Expected {count} '{prefix}' lines in {path}, found {lines}"
    raise AssertionError(errmsg)


# The child checks the wsgi_app property of a fresh persona.
WSGI_APP_PROPERTY_PROBE = r"""
import sys
from ccai.webworks.persona.lifecycle import LifecycleError
from ccai.webworks.webapplication import establish_webapp_persona, reset_webapp_persona
from ccai.webworks.wsgi.asgibridge import ASGIBridge

reset_webapp_persona()
webapp = establish_webapp_persona(name="wsgiprobe", logger_name="wsgiprobe", log_basename="wsgiprobe",
                                  presence_dir=sys.argv[1])
try:
    webapp.wsgi_app
    print("BEFORE=served")
except LifecycleError:
    print("BEFORE=LifecycleError")

webapp.startup()
first = webapp.wsgi_app
second = webapp.wsgi_app
print("SAME=" + str(first is second))
print("BRIDGE=" + str(isinstance(first, ASGIBridge)))
"""


@removes_its_directories
def test_wsgi_app_property_is_one_bridge_after_infrastructure_setup():
    """
        wsgi_app is refused before the infrastructure exists and is the same
        ASGIBridge on every call afterwards.
    """
    completed = subprocess.run(
        [sys.executable, "-c", WSGI_APP_PROPERTY_PROBE, _make_directory("wsgiprobe-")],
        env=child_environment(),
        capture_output=True,
        text=True,
        timeout=120,
    )

    for expected in ("BEFORE=LifecycleError", "SAME=True", "BRIDGE=True"):
        if expected not in completed.stdout:
            errmsg = f"Expected {expected} from the probe, got {completed.returncode}:\n{completed.stdout}\n{completed.stderr}"
            raise AssertionError(errmsg)

    return


# =============================================================================
# Served over a real socket
# =============================================================================

@removes_its_directories
def test_route_is_served_over_wsgi():
    """
        A route of the WebApplication answers through the built-in WSGI server.
    """
    _require_fork()

    with _wsgi_server() as server:
        status, headers, body = server.request("GET", "/hello")

    if status != 200 or body != b"hello":
        errmsg = f"Expected 200 hello, got {status} {body!r}"
        raise AssertionError(errmsg)

    return


@removes_its_directories
def test_request_body_reaches_the_handler():
    """
        A POST body is fed to the application and read by the handler.
    """
    _require_fork()

    payload = ("w" * 100000).encode("ascii")

    with _wsgi_server() as server:
        status, headers, body = server.request("POST", "/echo", body=payload, headers={"Content-Type": "text/plain"})

    answer = json.loads(body)
    if status != 200 or answer["length"] != len(payload):
        errmsg = f"Expected the handler to read {len(payload)} bytes, got {status} {answer.get('length')}"
        raise AssertionError(errmsg)

    return


@removes_its_directories
def test_application_body_limit_answers_413():
    """
        server.max_request_body_size of the application applies over WSGI.
    """
    _require_fork()

    with _wsgi_server(max_request_body_size=64) as server:
        small_status, _, _ = server.request("POST", "/echo", body=b"s" * 10, headers={"Content-Type": "text/plain"})
        large_status, _, _ = server.request("POST", "/echo", body=b"l" * 100, headers={"Content-Type": "text/plain"})

    if small_status != 200 or large_status != 413:
        errmsg = f"Expected 200 below the limit and 413 above it, got {small_status} and {large_status}"
        raise AssertionError(errmsg)

    return


@removes_its_directories
def test_authentication_middleware_applies():
    """
        The authentication middleware configured on the application runs over WSGI.
    """
    _require_fork()

    with _wsgi_server() as server:
        anonymous_status, anonymous_headers, _ = server.request("GET", "/private")
        wrong_status, _, _ = server.request("GET", "/private", headers={"Authorization": "Basic " + base64.b64encode(b"alice:wrong").decode("ascii")})
        status, _, body = server.request("GET", "/private", headers={"Authorization": AUTH_HEADER})

    if anonymous_status != 401:
        errmsg = f"Expected 401 without credentials, got {anonymous_status}"
        raise AssertionError(errmsg)

    if wrong_status != 401:
        errmsg = f"Expected 401 with a wrong password, got {wrong_status}"
        raise AssertionError(errmsg)

    if status != 200 or body != b"private":
        errmsg = f"Expected 200 with valid credentials, got {status} {body!r}"
        raise AssertionError(errmsg)

    return


@removes_its_directories
def test_error_handlers_apply():
    """
        A failing handler gets 500, an HTTPException its own status and detail.
    """
    _require_fork()

    with _wsgi_server() as server:
        error_status, _, _ = server.request("GET", "/error")
        teapot_status, _, teapot_body = server.request("GET", "/teapot")
        missing_status, _, _ = server.request("GET", "/missing")

    if (error_status, teapot_status, missing_status) != (500, 418, 404):
        errmsg = f"Expected 500, 418 and 404, got {error_status}, {teapot_status} and {missing_status}"
        raise AssertionError(errmsg)

    if b"I'm a teapot" not in teapot_body:
        errmsg = f"Expected the detail of the HTTPException, got {teapot_body!r}"
        raise AssertionError(errmsg)

    return


@removes_its_directories
def test_repeated_set_cookie_headers_reach_the_client():
    """
        Two cookies set by the handler arrive as two Set-Cookie headers.
    """
    _require_fork()

    with _wsgi_server() as server:
        status, headers, _ = server.request("GET", "/cookies")

    cookies = headers.get_all("Set-Cookie") or []
    names = sorted(cookie.split("=", 1)[0] for cookie in cookies)

    if status != 200 or names != ["first", "second"]:
        errmsg = f"Expected the cookies 'first' and 'second', got {cookies}"
        raise AssertionError(errmsg)

    return


@removes_its_directories
def test_head_request_has_no_body():
    """
        A HEAD request is answered with the headers of the GET and no body.
    """
    _require_fork()

    with _wsgi_server() as server:
        status, headers, body = server.request("HEAD", "/hello")

    if status != 200 or body != b"":
        errmsg = f"Expected 200 without a body, got {status} {body!r}"
        raise AssertionError(errmsg)

    return


@removes_its_directories
def test_streaming_response_is_not_buffered():
    """
        The first chunk of a streaming route arrives before the stream ends.
    """
    _require_fork()

    with _wsgi_server() as server:
        connection = server.connection(timeout=10.0)
        try:
            started = time.monotonic()
            connection.request("GET", "/stream")
            response = connection.getresponse()
            first_line = response.read(len(b"first\n"))
            first_at = time.monotonic() - started
            rest = response.read()
            total = time.monotonic() - started
        finally:
            connection.close()

    if first_line != b"first\n" or b"second\n" not in rest:
        errmsg = f"Expected 'first' then 'second', got {first_line!r} and {rest!r}"
        raise AssertionError(errmsg)

    # The second chunk is produced 1.5 seconds after the first one
    if first_at >= 1.0 or total < 1.4:
        errmsg = f"Expected the first chunk at once and the stream to end later, got {first_at:.2f}s and {total:.2f}s"
        raise AssertionError(errmsg)

    return


@removes_its_directories
def test_lifespan_runs_in_every_worker():
    """
        Each worker process runs the startup handlers before it serves and the
        shutdown handlers when the server stops.
    """
    _require_fork()

    events_path = os.path.join(_make_directory("servingsite-events-"), "events.txt")
    server = _wsgi_server(workers=2, env={"SERVINGSITE_EVENTS": events_path})

    with server:
        startups = _wait_for_lines(events_path, "startup", 2)
        status, _, _ = server.request("GET", "/hello")

    shutdowns = _wait_for_lines(events_path, "shutdown", 2)

    startup_pids = sorted(line.split()[1] for line in startups)
    shutdown_pids = sorted(line.split()[1] for line in shutdowns)

    if len(set(startup_pids)) != 2 or startup_pids != shutdown_pids:
        errmsg = f"Expected a startup and a shutdown in each of two workers, got {startups} and {shutdowns}"
        raise AssertionError(errmsg)

    if str(server.pid) in startup_pids:
        errmsg = "Expected the lifespan to run in the workers, not in the master"
        raise AssertionError(errmsg)

    if status != 200:
        errmsg = f"Expected 200, got {status}"
        raise AssertionError(errmsg)

    return


@removes_its_directories
def test_failed_startup_answers_503():
    """
        A worker whose lifespan startup failed refuses requests with 503.
    """
    _require_fork()

    with _wsgi_server(env={"SERVINGSITE_FAIL_STARTUP": "1"}) as server:
        status, _, _ = server.request("GET", "/hello")

    if status != 503:
        errmsg = f"Expected 503 after a failed startup, got {status}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Entry points for external servers
# =============================================================================

@removes_its_directories
def test_gunicorn_entry_point_serves_the_application():
    """
        'ccai.webworks.wsgi.application:get_wsgi_application()' with
        WEBWORKS_SERVER_APP serves the application, as the documentation says.
    """
    _require_fork()

    port = find_free_port()
    env = {
        "SERVINGSITE_PRESENCE_DIR": _presence_dir(),
        "WEBWORKS_SERVER_APP": "ccai.testshared.servers.servingsite:webapp",
    }
    spec = "ccai.webworks.wsgi.application:get_wsgi_application()"

    with ServerProcess(GUNICORN_STYLE_CODE, port, args=[str(port), spec], env=env) as server:
        status, _, body = server.request("GET", "/hello")
        private_status, _, _ = server.request("GET", "/private")

    if status != 200 or body != b"hello" or private_status != 401:
        errmsg = f"Expected the application behind the entry point, got {status} {body!r} {private_status}"
        raise AssertionError(errmsg)

    return


@removes_its_directories
def test_module_attribute_entry_point_serves_the_site_asgi_app():
    """
        'ccai.webworks.wsgi.application:application' (the uWSGI style), with
        WEBWORKS_SERVER_APP naming the ASGI app a site exports, serves it.
    """
    _require_fork()

    port = find_free_port()
    env = {
        "SERVINGSITE_PRESENCE_DIR": _presence_dir(),
        "WEBWORKS_SERVER_APP": "ccai.testshared.servers.servingsite:app",
    }
    spec = "ccai.webworks.wsgi.application:application"

    with ServerProcess(GUNICORN_STYLE_CODE, port, args=[str(port), spec], env=env) as server:
        status, _, body = server.request("GET", "/hello")

    if status != 200 or body != b"hello":
        errmsg = f"Expected 200 hello, got {status} {body!r}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Parity with asgi_app
# =============================================================================

@removes_its_directories
def test_wsgi_app_answers_like_asgi_app():
    """
        The same requests through asgi_app and wsgi_app get the same answers.
    """
    env = child_environment({"SERVINGSITE_PRESENCE_DIR": _presence_dir(max_request_body_size=64)})

    completed = subprocess.run(
        [sys.executable, "-c", PARITY_PROBE_CODE],
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )

    result_line = None
    for line in completed.stdout.splitlines():
        if line.startswith("PARITY="):
            result_line = line[len("PARITY="):]

    if completed.returncode != 0 or result_line is None:
        errmsg = f"The parity probe failed ({completed.returncode}):\n{completed.stdout}\n{completed.stderr}"
        raise AssertionError(errmsg)

    answers = json.loads(result_line)

    if answers["asgi"] != answers["wsgi"]:
        errmsg = f"asgi_app and wsgi_app answered differently:\nASGI: {answers['asgi']}\nWSGI: {answers['wsgi']}"
        raise AssertionError(errmsg)

    statuses = [answer[2] for answer in answers["wsgi"]]
    if statuses != [200, 200, 413, 200, 500, 418, 401, 200, 404, 405]:
        errmsg = f"Unexpected statuses for the probe requests: {statuses}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# WebApplication.shutdown() with a WSGI-served application
# =============================================================================

@removes_its_directories
def test_webapplication_shutdown_runs_the_lifespan_shutdown_of_the_wsgi_bridge():
    """
        After wsgi_app served a request in this process, WebApplication.shutdown()
        runs the lifespan shutdown handlers at once (not only at process exit),
        and the bridge answers 503 afterwards.
    """
    events_path = os.path.join(_make_directory("servingsite-events-"), "events.txt")
    env = child_environment({
        "SERVINGSITE_PRESENCE_DIR": _presence_dir(),
        "SERVINGSITE_EVENTS": events_path,
    })

    completed = subprocess.run(
        [sys.executable, "-c", WEBAPP_SHUTDOWN_PROBE_CODE, events_path],
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )

    expected_lines = ["BEFORE=startup", "AFTER=startup,shutdown", "STATUS=200", "LATE=503"]
    for expected in expected_lines:
        if expected not in completed.stdout.splitlines():
            errmsg = f"Expected {expected} from the probe, got {completed.returncode}:\n{completed.stdout}\n{completed.stderr}"
            raise AssertionError(errmsg)

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
