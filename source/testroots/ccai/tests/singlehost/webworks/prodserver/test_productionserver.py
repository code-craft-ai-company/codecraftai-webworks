"""
    Tests for the ProductionServer class.

    The first part checks the server without starting it: construction, the
    validation done before it starts, the order of the startup steps (the
    privileges are dropped after the PID file and the log files and before
    any application code runs) and where the application is loaded.

    The second part starts real production servers in child processes,
    serving the WebApplication ccai.testshared.servers.servingsite on ports of
    18100-18199, and talks to them with http.client: routes, the health and
    metrics endpoints, request IDs, size and time limits, graceful shutdown
    with a request in flight, max-requests recycling, crash replacement,
    reload, the PID file, the access log, TLS and the HTTPS redirect.
"""

import json
import os
import shutil
import signal
import tempfile
import threading
import time

from typing import Any, Dict, List, Optional

from ccai.errors.exceptions import SemanticError, SkipError

from ccai.testshared.servers.serverprocess import ServerProcess, find_free_port
from ccai.testshared.servers.tlscert import create_self_signed_certificate

from ccai.webworks.prodserver.exceptions import ConfigurationError
from ccai.webworks.prodserver.productionmiddleware import ProductionMiddleware
from ccai.webworks.prodserver.productionserver import ProductionServer
from ccai.webworks.prodserver.serverconfig import (
    EXIT_APP_LOAD_ERROR,
    EXIT_PID_FILE_ERROR,
    EXIT_SUCCESS,
    ServerConfig,
    ServerState,
)
from ccai.webworks.wsgi.serverconfig import is_gevent_available


def plain_wsgi_app(environ: Dict[str, Any], start_response: Any) -> List[bytes]:
    """
        A WSGI application for the tests that do not serve.
    """
    start_response("200 OK", [("Content-Type", "text/plain")])
    return [b"plain"]


# =============================================================================
# Without serving
# =============================================================================

def test_server_needs_exactly_one_of_app_and_factory():
    """
        An application or an application factory, not both and not neither.
    """
    for kwargs in ({}, {"app": plain_wsgi_app, "app_factory": lambda: plain_wsgi_app}):
        try:
            ProductionServer(**kwargs)
        except SemanticError:
            continue
        errmsg = f"Expected SemanticError for ProductionServer(**{list(kwargs)})"
        raise AssertionError(errmsg)

    return


def test_server_exposes_both_configurations():
    """
        config is the production configuration, wsgi_config the one of the
        WSGI server underneath.
    """
    config = ServerConfig(host="127.0.0.1", port=18100, workers=2, keep_alive=9)
    server = ProductionServer(app=plain_wsgi_app, config=config)

    if server.config is not config or server.state != ServerState.STOPPED:
        errmsg = "Expected the production configuration and the STOPPED state"
        raise AssertionError(errmsg)

    if server.wsgi_config.workers != 2 or server.wsgi_config.keepalive != 9:
        errmsg = f"Expected the WSGI configuration built from it, got {server.wsgi_config}"
        raise AssertionError(errmsg)

    if server.app is not plain_wsgi_app or server.middleware is not None:
        errmsg = "Expected the application and no pipeline before the start"
        raise AssertionError(errmsg)

    return


def test_serve_refuses_an_invalid_configuration():
    """
        A configuration error ends serve() before anything is bound.
    """
    server = ProductionServer(app=plain_wsgi_app, config=ServerConfig(port=70000))

    try:
        server.serve()
    except ConfigurationError:
        if server.state != ServerState.STOPPED:
            errmsg = f"Expected the server to stay STOPPED, got {server.state}"
            raise AssertionError(errmsg)
        return

    errmsg = "Expected ConfigurationError for port 70000"
    raise AssertionError(errmsg)


def test_serve_refuses_gevent_when_it_is_not_installed():
    """
        Selecting the gevent worker class without gevent fails early.
    """
    if is_gevent_available():
        raise SkipError("gevent is installed, the worker class is valid here.")

    server = ProductionServer(app=plain_wsgi_app, config=ServerConfig(worker_class="gevent"))

    try:
        server.serve()
    except ConfigurationError as err:
        if "gevent" not in str(err):
            errmsg = f"Expected the message to name gevent, got {err}"
            raise AssertionError(errmsg)
        return

    errmsg = "Expected ConfigurationError for the gevent worker class"
    raise AssertionError(errmsg)


def test_serve_refuses_a_certificate_that_cannot_be_loaded():
    """
        A TLS key file that is not a key is a configuration error.
    """
    directory = tempfile.mkdtemp(prefix="prodserver-tls-")
    certfile = os.path.join(directory, "cert.pem")
    keyfile = os.path.join(directory, "key.pem")
    for path in (certfile, keyfile):
        with open(path, "w", encoding="utf-8") as pem_file:
            pem_file.write("not a certificate")

    server = ProductionServer(app=plain_wsgi_app, config=ServerConfig(ssl_certfile=certfile, ssl_keyfile=keyfile))

    try:
        server.serve()
    except ConfigurationError:
        return
    finally:
        shutil.rmtree(directory)

    errmsg = "Expected ConfigurationError for an invalid certificate"
    raise AssertionError(errmsg)


class StepRecorder:
    """
        Wraps component methods of a server to record the order they run in.
    """

    def __init__(self, server: ProductionServer):
        self.steps: List[str] = []
        self.ssl_context_at_drop: List[bool] = []
        self._wrap(server.process_manager, "write_pid_file")
        self._wrap(server.structured_logger, "open_log_files")
        self._wrap(server.resource_limiter, "setup_worker_tmp_dir")
        self._wrap(server.application_loader, "preload")

        original_drop = server.process_manager.drop_privileges
        ssl_manager = server.ssl_manager

        def recording_drop() -> None:
            self.steps.append("drop_privileges")
            self.ssl_context_at_drop.append(ssl_manager.ssl_context is not None)
            original_drop()
            return

        server.process_manager.drop_privileges = recording_drop
        return

    def _wrap(self, component: Any, method_name: str) -> None:
        original = getattr(component, method_name)

        def recording(*args: Any, **kwargs: Any) -> Any:
            self.steps.append(method_name)
            return original(*args, **kwargs)

        setattr(component, method_name, recording)
        return


def test_startup_drops_privileges_after_pid_file_and_logs_and_before_application_code():
    """
        The PID file and the log files are written with the privileges the
        server was started with; the worker directory and the application
        come after the drop.
    """
    directory = tempfile.mkdtemp(prefix="prodserver-steps-")
    factory_calls: List[str] = []

    def factory():
        factory_calls.append("factory")
        return plain_wsgi_app

    config = ServerConfig(
        preload=True,
        pid_file=os.path.join(directory, "server.pid"),
        access_log=os.path.join(directory, "access.log"),
    )
    server = ProductionServer(app_factory=factory, config=config)
    recorder = StepRecorder(server)

    try:
        server._after_bind()
    finally:
        server._release()
        shutil.rmtree(directory)

    expected = ["write_pid_file", "open_log_files", "drop_privileges", "setup_worker_tmp_dir", "preload"]
    if recorder.steps != expected:
        errmsg = f"Expected the steps {expected}, got {recorder.steps}"
        raise AssertionError(errmsg)

    if factory_calls != ["factory"] or not isinstance(server.middleware, ProductionMiddleware):
        errmsg = "Expected the factory to be called once in the master and the pipeline built"
        raise AssertionError(errmsg)

    return


def test_tls_key_is_loaded_before_privileges_are_dropped():
    """
        The TLS context, which reads the private key, exists at the drop.
    """
    directory = tempfile.mkdtemp(prefix="prodserver-tls-")

    try:
        certfile, keyfile = create_self_signed_certificate(directory)
        server = ProductionServer(app=plain_wsgi_app, config=ServerConfig(ssl_certfile=certfile, ssl_keyfile=keyfile))
        recorder = StepRecorder(server)

        server._validate_before_start()
        server._after_bind()
        server._release()
    finally:
        shutil.rmtree(directory)

    if recorder.ssl_context_at_drop != [True]:
        errmsg = f"Expected the TLS context to exist when privileges are dropped, got {recorder.ssl_context_at_drop}"
        raise AssertionError(errmsg)

    return


def test_application_from_a_factory_without_preload_is_loaded_in_each_worker():
    """
        Without preload the master does not call the factory; a worker does,
        when it starts.
    """
    factory_calls: List[str] = []

    def factory():
        factory_calls.append("factory")
        return plain_wsgi_app

    server = ProductionServer(app_factory=factory, config=ServerConfig(preload=False))
    application = server._load_application()

    calls_in_master = list(factory_calls)
    application.on_worker_start(None)

    environ = {"REQUEST_METHOD": "GET", "PATH_INFO": "/"}
    body = application(environ, lambda status, headers, exc_info=None: None)

    if calls_in_master != [] or factory_calls != ["factory"] or body != [b"plain"]:
        errmsg = f"Expected the factory to run in the worker only, got {calls_in_master} then {factory_calls}"
        raise AssertionError(errmsg)

    if application.can_serve is not True:
        errmsg = "Expected the loaded application to serve"
        raise AssertionError(errmsg)

    return


def test_sigint_shuts_down_gracefully():
    """
        SIGINT is a graceful shutdown for the production server.
    """
    server = ProductionServer(app=plain_wsgi_app)
    server._handle_sigint(signal.SIGINT, None)

    if server._shutdown_requested is not True or server._shutdown_graceful is not True:
        errmsg = "Expected SIGINT to request a graceful shutdown"
        raise AssertionError(errmsg)

    return


def test_reload_when_not_running_does_nothing():
    """
        reload() before the server runs is refused.
    """
    server = ProductionServer(app=plain_wsgi_app)
    server.reload()

    if server._reload_requested is not False:
        errmsg = "Expected no reload request while the server is stopped"
        raise AssertionError(errmsg)

    return


def test_get_status_describes_the_server():
    """
        get_status reports the state, the address and the components.
    """
    server = ProductionServer(app=plain_wsgi_app, config=ServerConfig(host="127.0.0.1", port=18101))
    status = server.get_status()

    for key in ("state", "host", "port", "ssl", "process", "resources"):
        if key not in status:
            errmsg = f"Expected '{key}' in the status, got {sorted(status)}"
            raise AssertionError(errmsg)

    if status["state"] != "stopped" or status["port"] != 18101:
        errmsg = f"Expected a stopped server on 18101, got {status}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Serving
# =============================================================================

# The child serves servingsite with the production server.
# argv: configuration as JSON, application mode
PRODSERVER_CODE = r"""
import json
import sys
from ccai.webworks.prodserver import ProductionServer, ServerConfig

config = ServerConfig(**json.loads(sys.argv[1]))
mode = sys.argv[2]

def load_site():
    import ccai.testshared.servers.servingsite as site
    return site.webapp

def failing_factory():
    raise RuntimeError("the application cannot be loaded")

if mode == "object":
    server = ProductionServer(app=load_site(), config=config)
elif mode == "factory":
    server = ProductionServer(app_factory=load_site, config=config)
else:
    server = ProductionServer(app_factory=failing_factory, config=config)

sys.exit(server.serve())
"""


def _require_fork() -> None:
    """
        The production server forks its workers.
    """
    if not hasattr(os, "fork"):
        raise SkipError("The production server needs os.fork.")
    return


class SiteFixture:
    """
        The files a served servingsite uses: presence directory, events file.
    """

    def __init__(self, max_request_body_size: Optional[int] = None):
        self.directory = tempfile.mkdtemp(prefix="prodserver-site-")
        self.presence_dir = os.path.join(self.directory, "presence")
        os.makedirs(self.presence_dir)
        self.events_path = os.path.join(self.directory, "events.txt")
        if max_request_body_size is not None:
            with open(os.path.join(self.presence_dir, "servingsite.json"), "w", encoding="utf-8") as config_file:
                json.dump({"server": {"max_request_body_size": max_request_body_size}}, config_file)
        return

    def path(self, name: str) -> str:
        return os.path.join(self.directory, name)

    def env(self, **extra: str) -> Dict[str, str]:
        rtnval = {"SERVINGSITE_PRESENCE_DIR": self.presence_dir, "SERVINGSITE_EVENTS": self.events_path}
        rtnval.update(extra)
        return rtnval

    def events(self, prefix: str) -> List[str]:
        if not os.path.exists(self.events_path):
            return []
        with open(self.events_path, "r", encoding="utf-8") as events_file:
            rtnval = [line.split()[1] for line in events_file if line.startswith(prefix + " ")]
        return rtnval

    def wait_for_events(self, prefix: str, count: int, timeout: float = 30.0) -> List[str]:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            found = self.events(prefix)
            if len(found) >= count:
                return found
            time.sleep(0.05)
        errmsg = f"Expected {count} '{prefix}' events, got {self.events(prefix)}"
        raise AssertionError(errmsg)

    def close(self) -> None:
        shutil.rmtree(self.directory, ignore_errors=True)
        return


def production_server(site: SiteFixture, mode: str = "object", use_tls: bool = False, env: Optional[Dict[str, str]] = None, **config_values: Any) -> ServerProcess:
    """
        Describe a production server child serving servingsite.
    """
    port = find_free_port()
    values: Dict[str, Any] = {
        "host": "127.0.0.1",
        "port": port,
        "workers": 1,
        "threads": 4,
        "graceful_timeout": 10,
        "log_format": "json",
    }
    values.update(config_values)
    rtnval = ServerProcess(PRODSERVER_CODE, port, args=[json.dumps(values), mode], env=site.env(**(env or {})), use_tls=use_tls)
    return rtnval


def wait_for_metric(server: ServerProcess, line: str, timeout: float = 15.0) -> str:
    """
        Scrape the metrics endpoint until it shows a line.
    """
    deadline = time.monotonic() + timeout
    text = ""
    while time.monotonic() < deadline:
        status, _, body = server.request("GET", "/metrics")
        text = body.decode("utf-8")
        if status == 200 and line in text.splitlines():
            return text
        time.sleep(0.1)
    errmsg = f"Expected the metrics line {line!r}, last scrape:\n{text}"
    raise AssertionError(errmsg)


def test_serves_a_web_application_with_request_ids():
    """
        A route of the WebApplication is served; every response carries a
        request ID, which the handler saw in its header and in its context.
    """
    _require_fork()
    site = SiteFixture()

    try:
        with production_server(site, workers=2) as server:
            status, headers, body = server.request("GET", "/hello")
            id_status, id_headers, id_body = server.request("GET", "/request-id", headers={"X-Request-ID": "client-42"})
            generated_status, generated_headers, generated_body = server.request("GET", "/request-id")
    finally:
        site.close()

    if status != 200 or body != b"hello" or len(headers.get("X-Request-ID", "")) != 36:
        errmsg = f"Expected 200 hello with a generated request ID, got {status} {body!r} {headers.get('X-Request-ID')}"
        raise AssertionError(errmsg)

    seen = json.loads(id_body)
    if id_headers.get("X-Request-ID") != "client-42" or seen != {"header": "client-42", "context": "client-42"}:
        errmsg = f"Expected the client's ID everywhere, got {id_headers.get('X-Request-ID')} {seen}"
        raise AssertionError(errmsg)

    generated = generated_headers.get("X-Request-ID")
    seen_generated = json.loads(generated_body)
    if seen_generated != {"header": generated, "context": generated}:
        errmsg = f"Expected the generated ID {generated} in the handler, got {seen_generated}"
        raise AssertionError(errmsg)

    return


def test_health_and_metrics_endpoints():
    """
        /health answers 200 JSON; /metrics adds up the requests of all workers.
    """
    _require_fork()
    site = SiteFixture()

    try:
        with production_server(site, workers=2) as server:
            health_status, health_headers, health_body = server.request("GET", "/health")
            for _ in range(20):
                status, _, _ = server.request("GET", "/hello")
                if status != 200:
                    errmsg = f"Expected 200 from /hello, got {status}"
                    raise AssertionError(errmsg)
            text = wait_for_metric(server, 'webworks_requests_per_endpoint_total{method="GET",endpoint="/hello"} 20')
    finally:
        site.close()

    health = json.loads(health_body)
    if health_status != 200 or health["status"] != "healthy" or health_headers.get("Content-Type") != "application/json":
        errmsg = f"Expected a healthy JSON answer, got {health_status} {health}"
        raise AssertionError(errmsg)

    worker_lines = [line for line in text.splitlines() if line.startswith("webworks_worker_status{")]
    if len(worker_lines) != 2:
        errmsg = f"Expected the status of the two workers, got {worker_lines}"
        raise AssertionError(errmsg)

    return


def test_health_reports_503_when_the_application_failed_to_start():
    """
        A worker whose application lifespan failed is unhealthy and refuses requests.
    """
    _require_fork()
    site = SiteFixture()

    try:
        with production_server(site, env={"SERVINGSITE_FAIL_STARTUP": "1"}) as server:
            health_status, _, health_body = server.request("GET", "/health")
            status, _, _ = server.request("GET", "/hello")
    finally:
        site.close()

    if health_status != 503 or json.loads(health_body)["status"] != "unhealthy" or status != 503:
        errmsg = f"Expected 503 from /health and /hello, got {health_status} and {status}"
        raise AssertionError(errmsg)

    return


def test_size_limits_are_enforced():
    """
        A body over limit_request_body gets 413, a header field over
        limit_request_field_size 431, both before the application.
    """
    _require_fork()
    site = SiteFixture()

    try:
        with production_server(site, limit_request_body=1024, limit_request_field_size=100) as server:
            small_status, _, _ = server.request("POST", "/echo", body=b"s" * 1000, headers={"Content-Type": "text/plain"})
            large_status, _, _ = server.request("POST", "/echo", body=b"l" * 2000, headers={"Content-Type": "text/plain"})
            header_status, _, _ = server.request("GET", "/hello", headers={"X-Long": "h" * 200})
    finally:
        site.close()

    if (small_status, large_status, header_status) != (200, 413, 431):
        errmsg = f"Expected 200, 413 and 431, got {small_status}, {large_status} and {header_status}"
        raise AssertionError(errmsg)

    return


def test_request_time_limit_answers_504():
    """
        A handler that runs longer than the timeout is answered with 504.
    """
    _require_fork()
    site = SiteFixture()

    try:
        with production_server(site, timeout=1) as server:
            started = time.monotonic()
            status, _, _ = server.request("GET", "/slow?seconds=4", timeout=15.0)
            elapsed = time.monotonic() - started
    finally:
        site.close()

    if status != 504 or elapsed > 3.5:
        errmsg = f"Expected 504 after about a second, got {status} after {elapsed:.1f}s"
        raise AssertionError(errmsg)

    return


def test_graceful_shutdown_finishes_the_request_in_flight():
    """
        SIGTERM while a request is being served: the request is answered and
        the server ends with exit code 0.
    """
    _require_fork()
    site = SiteFixture()
    results: List[Any] = []

    try:
        server = production_server(site)
        with server:
            def slow_request() -> None:
                results.append(server.request("GET", "/slow?seconds=2", timeout=20.0))
                return

            client = threading.Thread(target=slow_request)
            client.start()
            site.wait_for_events("slow-start", 1)

            exit_code = server.stop(signal.SIGTERM)
            client.join(timeout=20.0)
    finally:
        site.close()

    if len(results) != 1 or results[0][0] != 200 or results[0][2] != b"slow done":
        errmsg = f"Expected the request in flight to be answered, got {results}"
        raise AssertionError(errmsg)

    if exit_code != EXIT_SUCCESS:
        errmsg = f"Expected exit code {EXIT_SUCCESS}, got {exit_code}:\n{server.output()}"
        raise AssertionError(errmsg)

    return


def test_workers_are_recycled_after_max_requests():
    """
        A worker that served max_requests requests is replaced; no request fails.
    """
    _require_fork()
    site = SiteFixture()
    pids: List[int] = []

    try:
        with production_server(site, max_requests=3) as server:
            for _ in range(7):
                status, _, body = server.request("GET", "/pid")
                if status != 200:
                    errmsg = f"Expected every request to succeed, got {status}"
                    raise AssertionError(errmsg)
                pids.append(json.loads(body)["pid"])
    finally:
        site.close()

    if pids[0:3] != [pids[0]] * 3 or pids[3:6] != [pids[3]] * 3 or len(set(pids)) != 3:
        errmsg = f"Expected a new worker after every 3 requests, got {pids}"
        raise AssertionError(errmsg)

    return


def test_crashed_worker_is_replaced():
    """
        A worker that is killed is replaced by a new one that serves.
    """
    _require_fork()
    site = SiteFixture()

    try:
        with production_server(site) as server:
            _, _, body = server.request("GET", "/pid")
            first_pid = json.loads(body)["pid"]
            os.kill(first_pid, signal.SIGKILL)

            new_pid = None
            deadline = time.monotonic() + 30.0
            while time.monotonic() < deadline:
                try:
                    status, _, body = server.request("GET", "/pid", timeout=5.0)
                except OSError:
                    time.sleep(0.1)
                    continue
                if status == 200 and json.loads(body)["pid"] != first_pid:
                    new_pid = json.loads(body)["pid"]
                    break
                time.sleep(0.1)
    finally:
        site.close()

    if new_pid is None:
        errmsg = f"Expected a replacement worker for {first_pid}"
        raise AssertionError(errmsg)

    return


def test_sighup_replaces_the_workers():
    """
        SIGHUP starts new workers and stops the old ones gracefully; requests
        keep being served.
    """
    _require_fork()
    site = SiteFixture()

    try:
        with production_server(site, workers=2) as server:
            old_workers = sorted(site.wait_for_events("startup", 2))

            os.kill(server.pid, signal.SIGHUP)

            all_startups = site.wait_for_events("startup", 4)
            retired = site.wait_for_events("shutdown", 2)
            status, _, _ = server.request("GET", "/hello")
    finally:
        site.close()

    new_workers = sorted(set(all_startups) - set(old_workers))

    if sorted(retired) != old_workers or len(new_workers) != 2:
        errmsg = f"Expected the two old workers to stop and two new ones to start, got old={old_workers} retired={retired} new={new_workers}"
        raise AssertionError(errmsg)

    if status != 200:
        errmsg = f"Expected the new workers to serve, got {status}"
        raise AssertionError(errmsg)

    return


def test_pid_file_is_written_held_and_removed():
    """
        The PID file holds the master's PID while it runs, keeps a second
        server from starting, and is removed at the end.
    """
    _require_fork()
    site = SiteFixture()
    pid_file = site.path("server.pid")

    try:
        with production_server(site, pid_file=pid_file) as server:
            with open(pid_file, "r", encoding="utf-8") as pid_handle:
                recorded_pid = int(pid_handle.read().strip())

            second = production_server(site, pid_file=pid_file)
            second_exit = _run_to_exit(second)

        removed = not os.path.exists(pid_file)
        exit_code = server.returncode
    finally:
        site.close()

    if recorded_pid != server.pid:
        errmsg = f"Expected the master PID {server.pid} in the PID file, got {recorded_pid}"
        raise AssertionError(errmsg)

    if second_exit != EXIT_PID_FILE_ERROR:
        errmsg = f"Expected the second server to end with {EXIT_PID_FILE_ERROR}, got {second_exit}"
        raise AssertionError(errmsg)

    if not removed or exit_code != EXIT_SUCCESS:
        errmsg = f"Expected the PID file removed and exit code 0, got removed={removed} exit={exit_code}"
        raise AssertionError(errmsg)

    return


def _run_to_exit(server: ServerProcess, timeout: float = 60.0) -> int:
    """
        Run a server child that is expected to end by itself.
    """
    import subprocess
    import sys

    completed = subprocess.run(
        [sys.executable, "-c", server.code] + server.args,
        env=server.env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return completed.returncode


def test_application_that_cannot_be_loaded_ends_the_server():
    """
        A factory that fails, in the master (preload) or in the workers, ends
        the server with EXIT_APP_LOAD_ERROR instead of a restart loop.
    """
    _require_fork()
    site = SiteFixture()

    try:
        in_workers = _run_to_exit(production_server(site, mode="failing-factory", preload=False))
        in_master = _run_to_exit(production_server(site, mode="failing-factory", preload=True))
    finally:
        site.close()

    if (in_workers, in_master) != (EXIT_APP_LOAD_ERROR, EXIT_APP_LOAD_ERROR):
        errmsg = f"Expected exit code {EXIT_APP_LOAD_ERROR} both times, got {in_workers} and {in_master}"
        raise AssertionError(errmsg)

    return


def test_application_from_a_factory_is_served_by_every_worker():
    """
        Without preload each worker loads the application from the factory.
    """
    _require_fork()
    site = SiteFixture()

    try:
        with production_server(site, mode="factory", workers=2, preload=False) as server:
            status, _, body = server.request("GET", "/hello")
            startups = site.wait_for_events("startup", 2)
    finally:
        site.close()

    if status != 200 or body != b"hello" or len(set(startups)) != 2:
        errmsg = f"Expected the factory application in two workers, got {status} {body!r} {startups}"
        raise AssertionError(errmsg)

    return


def test_access_log_is_written_as_json():
    """
        Each request is written to the access log file as a JSON entry.
    """
    _require_fork()
    site = SiteFixture()
    access_log = site.path("access.log")

    try:
        with production_server(site, access_log=access_log) as server:
            server.request("GET", "/hello", headers={"X-Request-ID": "logged-1"})

        with open(access_log, "r", encoding="utf-8") as log_file:
            entries = [json.loads(line) for line in log_file if line.strip()]
    finally:
        site.close()

    matching = [entry for entry in entries if entry.get("request_id") == "logged-1"]
    if len(matching) != 1:
        errmsg = f"Expected one access log entry for the request, got {entries}"
        raise AssertionError(errmsg)

    entry = matching[0]
    if entry["path"] != "/hello" or entry["status_code"] != 200 or "worker_id" not in entry:
        errmsg = f"Expected the request in the entry, got {entry}"
        raise AssertionError(errmsg)

    return


def test_https_redirect_for_requests_made_over_http():
    """
        With ssl_redirect, a request the proxy reports as http is redirected.
    """
    _require_fork()
    site = SiteFixture()

    try:
        with production_server(site, ssl_redirect=True) as server:
            status, headers, _ = server.request("GET", "/hello?x=1", headers={"X-Forwarded-Proto": "http", "Host": "example.test"})
            https_status, _, _ = server.request("GET", "/hello", headers={"X-Forwarded-Proto": "https"})
    finally:
        site.close()

    if status != 301 or headers.get("Location") != "https://example.test/hello?x=1" or https_status != 200:
        errmsg = f"Expected a redirect to https and https served, got {status} {headers.get('Location')} {https_status}"
        raise AssertionError(errmsg)

    return


def test_tls_end_to_end():
    """
        With a certificate the server speaks HTTPS with TLS 1.2 or later.
    """
    _require_fork()
    site = SiteFixture()

    try:
        certfile, keyfile = create_self_signed_certificate(site.directory)

        with production_server(site, use_tls=True, ssl_certfile=certfile, ssl_keyfile=keyfile) as server:
            connection = server.connection()
            try:
                connection.request("GET", "/hello")
                response = connection.getresponse()
                body = response.read()
                tls_version = connection.sock.version()
            finally:
                connection.close()
    finally:
        site.close()

    if response.status != 200 or body != b"hello" or tls_version not in ("TLSv1.2", "TLSv1.3"):
        errmsg = f"Expected 200 hello over TLS 1.2+, got {response.status} {body!r} {tls_version}"
        raise AssertionError(errmsg)

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
