"""
    Tests for the ProductionMiddleware class.

    The middleware is driven the way a WSGI worker drives it: on_worker_start,
    requests with an environ and a start_response, the body iterated and
    closed, on_worker_exit. The production components are the real ones; the
    worker is a stand-in that records a shutdown request.
"""

import io
import json
import logging
import os
import shutil
import tempfile

from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

from ccai.webworks.prodserver.healthchecker import HealthChecker
from ccai.webworks.prodserver.metricscollector import MetricsCollector
from ccai.webworks.prodserver.metricsstore import MetricsStore
from ccai.webworks.prodserver.productionmiddleware import (
    ProductionMiddleware,
    RequestIdLogFilter,
    current_request_id,
)
from ccai.webworks.prodserver.requesttracer import RequestTracer
from ccai.webworks.prodserver.resourcelimiter import ResourceLimiter
from ccai.webworks.prodserver.serverconfig import ServerConfig
from ccai.webworks.prodserver.sslmanager import SSLManager
from ccai.webworks.prodserver.structuredlogger import StructuredLogger
from ccai.webworks.wsgi.constants import ENVIRON_REQUEST_ID, ENVIRON_REQUEST_TIMEOUT


# =============================================================================
# Helpers
# =============================================================================

class FakeWorker:
    """
        Stands in for the WSGI worker the middleware runs in.
    """

    def __init__(self, worker_id: int = 3):
        self.worker_id = worker_id
        self.shutdown_requested = False
        self.shutdown_calls: List[bool] = []
        return

    def request_shutdown(self, graceful: bool = True) -> None:
        self.shutdown_calls.append(graceful)
        self.shutdown_requested = True
        return


class RecordingApp:
    """
        A WSGI application that records what it saw.
    """

    def __init__(self, status: str = "200 OK", headers: Optional[List[Tuple[str, str]]] = None, body: bytes = b"app body"):
        self.status = status
        self.headers = headers if headers is not None else [("Content-Type", "text/plain")]
        self.body = body
        self.environs: List[Dict[str, Any]] = []
        self.context_ids: List[Optional[str]] = []
        self.events: List[str] = []
        self.can_serve = True
        return

    def on_worker_start(self, worker: Any) -> None:
        self.events.append("start")
        return

    def on_worker_exit(self, worker: Any) -> None:
        self.events.append("exit")
        return

    def __call__(self, environ: Dict[str, Any], start_response: Callable) -> Iterable[bytes]:
        self.environs.append(environ)
        self.context_ids.append(current_request_id.get())
        start_response(self.status, list(self.headers))
        return [self.body]


class Harness:
    """
        A ProductionMiddleware with its components, in a temporary directory.
    """

    def __init__(self, app: Any = None, **config_values: Any):
        self.directory = tempfile.mkdtemp(prefix="prodmiddleware-")
        self.access_log_path = os.path.join(self.directory, "access.log")
        config_values.setdefault("access_log", self.access_log_path)
        config_values.setdefault("log_format", "json")
        self.config = ServerConfig(**config_values)
        self.app = app if app is not None else RecordingApp()
        self.worker = FakeWorker()
        self.health_checker = HealthChecker(self.config)
        self.metrics_collector = MetricsCollector(self.config)
        self.metrics_store = MetricsStore(self.directory, self.config)
        self.request_tracer = RequestTracer(self.config)
        self.structured_logger = StructuredLogger(self.config)
        self.structured_logger.open_log_files()
        self.resource_limiter = ResourceLimiter(self.config)
        self.ssl_manager = SSLManager(self.config)
        self.middleware = ProductionMiddleware(
            self.app,
            self.config,
            health_checker=self.health_checker,
            metrics_collector=self.metrics_collector,
            metrics_store=self.metrics_store,
            request_tracer=self.request_tracer,
            structured_logger=self.structured_logger,
            resource_limiter=self.resource_limiter,
            ssl_manager=self.ssl_manager,
        )
        return

    def start(self) -> "Harness":
        self.middleware.on_worker_start(self.worker)
        return self

    def close(self) -> None:
        self.structured_logger.close_log_files()
        shutil.rmtree(self.directory, ignore_errors=True)
        return

    def request(self, method: str = "GET", path: str = "/", headers: Optional[Dict[str, str]] = None, extra_environ: Optional[Dict[str, Any]] = None) -> Tuple[str, List[Tuple[str, str]], bytes]:
        environ: Dict[str, Any] = {
            "REQUEST_METHOD": method,
            "PATH_INFO": path,
            "QUERY_STRING": "",
            "REQUEST_URI": path,
            "SERVER_NAME": "127.0.0.1",
            "SERVER_PORT": "8000",
            "SERVER_PROTOCOL": "HTTP/1.1",
            "REMOTE_ADDR": "10.0.0.9",
            "wsgi.url_scheme": "http",
            "wsgi.input": io.BytesIO(b""),
        }
        for name, value in (headers or {}).items():
            environ["HTTP_" + name.upper().replace("-", "_")] = value
        environ.update(extra_environ or {})

        captured: Dict[str, Any] = {}

        def start_response(status: str, response_headers: List[Tuple[str, str]], exc_info: Any = None) -> Callable:
            captured["status"] = status
            captured["headers"] = response_headers
            return lambda data: None

        body_iterable = self.middleware(environ, start_response)
        try:
            body = b"".join(body_iterable)
        finally:
            body_iterable.close()

        rtnval = (captured["status"], captured["headers"], body)
        return rtnval

    def access_entries(self) -> List[Dict[str, Any]]:
        with open(self.access_log_path, "r", encoding="utf-8") as access_log:
            rtnval = [json.loads(line) for line in access_log if line.strip()]
        return rtnval


def header(headers: List[Tuple[str, str]], name: str) -> List[str]:
    """
        The values of one header.
    """
    rtnval = [value for header_name, value in headers if header_name.lower() == name.lower()]
    return rtnval


# =============================================================================
# Request IDs
# =============================================================================

def test_request_id_is_generated_passed_on_and_returned():
    """
        A request without an ID gets one: the application sees it in the
        header and in the context, the client in the response.
    """
    harness = Harness().start()

    try:
        status, headers, body = harness.request()
        environ = harness.app.environs[0]
        context_id = harness.app.context_ids[0]
        after_request = current_request_id.get()
    finally:
        harness.close()

    response_ids = header(headers, "X-Request-ID")

    if len(response_ids) != 1 or len(response_ids[0]) != 36:
        errmsg = f"Expected one generated X-Request-ID, got {response_ids}"
        raise AssertionError(errmsg)

    request_id = response_ids[0]

    if environ.get("HTTP_X_REQUEST_ID") != request_id or environ.get(ENVIRON_REQUEST_ID) != request_id:
        errmsg = f"Expected the application to see {request_id}, got {environ.get('HTTP_X_REQUEST_ID')}"
        raise AssertionError(errmsg)

    if context_id != request_id or after_request is not None:
        errmsg = f"Expected the ID in the context during the request only, got {context_id} and {after_request}"
        raise AssertionError(errmsg)

    return


def test_received_request_id_is_kept_and_invalid_one_replaced():
    """
        A plain-token ID from the client is used; anything else is replaced.
    """
    harness = Harness().start()

    try:
        _, kept_headers, _ = harness.request(headers={"X-Request-ID": "client-id-7"})
        _, replaced_headers, _ = harness.request(headers={"X-Request-ID": "two words"})
    finally:
        harness.close()

    if header(kept_headers, "X-Request-ID") != ["client-id-7"]:
        errmsg = f"Expected the client's ID, got {header(kept_headers, 'X-Request-ID')}"
        raise AssertionError(errmsg)

    replaced = header(replaced_headers, "X-Request-ID")
    if replaced == ["two words"] or len(replaced) != 1:
        errmsg = f"Expected a generated ID instead of the invalid one, got {replaced}"
        raise AssertionError(errmsg)

    return


def test_request_id_header_of_the_application_is_not_duplicated():
    """
        An application that sets the header itself keeps its value.
    """
    app = RecordingApp(headers=[("X-Request-ID", "set-by-app")])
    harness = Harness(app=app).start()

    try:
        _, headers, _ = harness.request()
    finally:
        harness.close()

    if header(headers, "X-Request-ID") != ["set-by-app"]:
        errmsg = f"Expected only the application's header, got {header(headers, 'X-Request-ID')}"
        raise AssertionError(errmsg)

    return


def test_log_filter_adds_the_request_id():
    """
        Log records written during a request carry its ID.
    """
    records: List[logging.LogRecord] = []

    class Collect(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    handler = Collect()
    handler.addFilter(RequestIdLogFilter())
    logger = logging.getLogger("prodmiddleware.test")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    def logging_app(environ: Dict[str, Any], start_response: Callable) -> Iterable[bytes]:
        logger.info("inside")
        start_response("200 OK", [])
        return [b""]

    harness = Harness(app=logging_app).start()

    try:
        _, headers, _ = harness.request(headers={"X-Request-ID": "log-id-1"})
        logger.info("outside")
    finally:
        logger.removeHandler(handler)
        harness.close()

    ids = [record.request_id for record in records]
    if ids != ["log-id-1", "-"]:
        errmsg = f"Expected the request ID inside the request and '-' outside, got {ids}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Production endpoints
# =============================================================================

def test_health_endpoint_bypasses_the_application():
    """
        GET /health is answered with the JSON status, the application is not called.
    """
    harness = Harness().start()

    try:
        status, headers, body = harness.request(path="/health")
        post_status, _, _ = harness.request(method="POST", path="/health")
    finally:
        harness.close()

    answer = json.loads(body)

    if status != "200 OK" or answer["status"] != "healthy":
        errmsg = f"Expected 200 healthy, got {status} {answer}"
        raise AssertionError(errmsg)

    if len(harness.app.environs) != 1 or harness.app.environs[0]["REQUEST_METHOD"] != "POST":
        errmsg = "Expected only the POST to reach the application"
        raise AssertionError(errmsg)

    if header(headers, "Content-Type") != ["application/json"] or post_status != "200 OK":
        errmsg = f"Expected a JSON answer, got {headers}"
        raise AssertionError(errmsg)

    return


def test_health_endpoint_reports_503_when_draining_or_not_serving():
    """
        A worker that is stopping, or an application that failed to start,
        is unhealthy.
    """
    harness = Harness().start()

    try:
        harness.app.can_serve = False
        app_down_status, _, _ = harness.request(path="/health")

        harness.app.can_serve = True
        harness.worker.shutdown_requested = True
        draining_status, _, body = harness.request(path="/health")
    finally:
        harness.close()

    if app_down_status != "503 Service Unavailable" or draining_status != "503 Service Unavailable":
        errmsg = f"Expected 503 twice, got {app_down_status} and {draining_status}"
        raise AssertionError(errmsg)

    if json.loads(body)["status"] != "unhealthy":
        errmsg = f"Expected an unhealthy status, got {body!r}"
        raise AssertionError(errmsg)

    return


def test_metrics_endpoint_reports_the_counted_requests():
    """
        GET /metrics answers Prometheus text with the requests counted so far.
    """
    harness = Harness().start()

    try:
        for _ in range(3):
            harness.request(path="/things")
        status, headers, body = harness.request(path="/metrics")
    finally:
        harness.close()

    text = body.decode("utf-8")

    if status != "200 OK" or not header(headers, "Content-Type")[0].startswith("text/plain; version=0.0.4"):
        errmsg = f"Expected Prometheus text, got {status} {headers}"
        raise AssertionError(errmsg)

    if 'webworks_requests_per_endpoint_total{method="GET",endpoint="/things"} 3' not in text:
        errmsg = f"Expected the three requests in the metrics, got:\n{text}"
        raise AssertionError(errmsg)

    if 'webworks_worker_status{worker_id="3",state="active"} 1' not in text:
        errmsg = f"Expected the worker status, got:\n{text}"
        raise AssertionError(errmsg)

    return


def test_oversized_header_field_answers_431():
    """
        A header field over limit_request_field_size is refused before the application.
    """
    harness = Harness(limit_request_field_size=16).start()

    try:
        status, _, _ = harness.request(headers={"X-Big": "y" * 17})
        small_status, _, _ = harness.request(headers={"X-Small": "y" * 16})
    finally:
        harness.close()

    if status != "431 Request Header Fields Too Large" or small_status != "200 OK":
        errmsg = f"Expected 431 then 200, got {status} and {small_status}"
        raise AssertionError(errmsg)

    if len(harness.app.environs) != 1:
        errmsg = "Expected the refused request not to reach the application"
        raise AssertionError(errmsg)

    return


def test_ssl_redirect_redirects_http_requests_only():
    """
        With ssl_redirect, http requests (as the proxy reports them) are redirected.
    """
    harness = Harness(ssl_redirect=True).start()

    try:
        status, headers, _ = harness.request(
            path="/page",
            headers={"Host": "example.test", "X-Forwarded-Proto": "http"},
            extra_environ={"REQUEST_URI": "/page?x=1"},
        )
        https_status, _, _ = harness.request(path="/page", headers={"Host": "example.test", "X-Forwarded-Proto": "https"})
        tls_status, _, _ = harness.request(path="/page", extra_environ={"wsgi.url_scheme": "https"})
    finally:
        harness.close()

    if status != "301 Moved Permanently" or header(headers, "Location") != ["https://example.test/page?x=1"]:
        errmsg = f"Expected a redirect to https, got {status} {headers}"
        raise AssertionError(errmsg)

    if https_status != "200 OK" or tls_status != "200 OK":
        errmsg = f"Expected https requests to be served, got {https_status} and {tls_status}"
        raise AssertionError(errmsg)

    return


def test_request_timeout_is_handed_to_the_application():
    """
        The timeout option reaches the ASGI bridge through the environ.
    """
    harness = Harness(timeout=12).start()

    try:
        harness.request()
        harness.request(extra_environ={ENVIRON_REQUEST_TIMEOUT: 3.0})
    finally:
        harness.close()

    timeouts = [environ.get(ENVIRON_REQUEST_TIMEOUT) for environ in harness.app.environs]
    if timeouts != [12.0, 3.0]:
        errmsg = f"Expected the configured timeout unless one was set, got {timeouts}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Access log, metrics, limits, tracing
# =============================================================================

def test_access_log_entry_describes_the_request():
    """
        Every request writes a structured access log entry.
    """
    harness = Harness(app=RecordingApp(status="201 Created", body=b"12345")).start()

    try:
        harness.request(method="POST", path="/items", headers={"X-Request-ID": "access-1"})
        entries = harness.access_entries()
    finally:
        harness.close()

    entry = entries[-1]
    expected = {
        "method": "POST",
        "path": "/items",
        "status_code": 201,
        "request_id": "access-1",
        "worker_id": 3,
        "client": "10.0.0.9",
        "bytes_sent": 5,
    }

    for name, value in expected.items():
        if entry.get(name) != value:
            errmsg = f"Access log {name}: expected {value!r}, got {entry.get(name)!r} in {entry}"
            raise AssertionError(errmsg)

    if "latency_ms" not in entry or "timestamp" not in entry:
        errmsg = f"Expected latency and timestamp in {entry}"
        raise AssertionError(errmsg)

    return


def test_application_error_is_recorded_as_500():
    """
        An application that raises is counted and logged as 500; the error
        reaches the server.
    """
    def failing_app(environ: Dict[str, Any], start_response: Callable) -> Iterable[bytes]:
        raise RuntimeError("broken")

    harness = Harness(app=failing_app).start()

    try:
        try:
            harness.request(path="/broken")
        except RuntimeError:
            raised = True
        else:
            raised = False
        errors = harness.metrics_collector.get_error_count(status_code=500)
        entries = harness.access_entries()
        active = harness.metrics_collector.get_active_connections()
    finally:
        harness.close()

    if not raised or errors != 1 or entries[-1]["status_code"] != 500 or active != 0:
        errmsg = f"Expected the error to propagate and be recorded, raised={raised} errors={errors} active={active}"
        raise AssertionError(errmsg)

    return


def test_worker_over_its_memory_limit_is_recycled():
    """
        A worker whose resident memory passed limit_memory is asked to stop.
    """
    from ccai.errors.exceptions import SkipError
    from ccai.webworks.prodserver.resourcelimiter import current_memory_usage

    if current_memory_usage() == 0:
        raise SkipError("This platform reports no resident memory.")

    harness = Harness(limit_memory=1024).start()

    try:
        harness.request()
    finally:
        harness.close()

    if harness.worker.shutdown_calls != [True]:
        errmsg = f"Expected one graceful shutdown request, got {harness.worker.shutdown_calls}"
        raise AssertionError(errmsg)

    return


def test_tracing_exports_a_span_per_request():
    """
        With tracing enabled every request is exported as a span with its status.
    """
    harness = Harness(enable_tracing=True).start()
    exported: List[Dict[str, Any]] = []
    harness.request_tracer.register_export_backend(exported.extend)

    try:
        harness.request(path="/traced", headers={
            "X-Request-ID": "trace-1",
            "traceparent": "00-0123456789abcdef0123456789abcdef-0123456789abcdef-01",
        })
    finally:
        harness.close()

    if len(exported) != 1:
        errmsg = f"Expected one span, got {exported}"
        raise AssertionError(errmsg)

    span = exported[0]
    if span["request_id"] != "trace-1" or span["parent_span_id"] != "0123456789abcdef" or span["attributes"].get("http.status_code") != 200:
        errmsg = f"Expected the span of the request, got {span}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Worker lifecycle
# =============================================================================

def test_worker_lifecycle_is_passed_on_to_the_application():
    """
        on_worker_start and on_worker_exit reach the application; the exit
        leaves a final metrics snapshot with the worker stopped.
    """
    harness = Harness()

    try:
        harness.middleware.on_worker_start(harness.worker)
        harness.request()
        harness.middleware.on_worker_exit(harness.worker)
        totals = harness.metrics_store.collect()
    finally:
        harness.close()

    if harness.app.events != ["start", "exit"]:
        errmsg = f"Expected start and exit to reach the application, got {harness.app.events}"
        raise AssertionError(errmsg)

    if totals.get_request_count() != 1 or totals.get_worker_statuses() != {3: "stopped"}:
        errmsg = f"Expected the final snapshot, got {totals.get_request_count()} {totals.get_worker_statuses()}"
        raise AssertionError(errmsg)

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
