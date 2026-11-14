"""
    Production request pipeline module for the production server.

    This module provides ProductionMiddleware, the WSGI middleware the
    production server puts in front of the application it serves. Every
    request of every worker goes through it, so the production features are
    on the real request path:

    - request IDs: the ID the client sent in the trace header (X-Request-ID by
      default) is used when it is a plain token, otherwise one is generated;
      it is passed on to the application in that header, returned in the
      response header, attached to every log record of the request
      (``record.request_id``, through RequestIdLogFilter) and written to the
      access log,
    - per-field header size limit: a header field over
      ``limit_request_field_size`` is answered with 431,
    - the health endpoint (``health_check_path``, 200 or 503 with a JSON
      status) and the metrics endpoint (``metrics_path``, Prometheus text
      with the totals of all workers) are answered before the application's
      routing,
    - HTTP to HTTPS redirect for requests whose scheme is http, when
      ``ssl_redirect`` is on,
    - the request time limit: ``timeout`` is put in the environ under
      ``webworks.request_timeout``, which the ASGI bridge of a WebApplication
      enforces with 504,
    - metrics, the structured access log and tracing spans for every request,
    - the memory limit: a worker whose resident memory passed ``limit_memory``
      stops gracefully after the request and is replaced.

    The middleware also takes part in the life of each worker process
    (on_worker_start / on_worker_exit, called by the WSGI worker) and passes
    those calls on to the application, so the lifespan of a WebApplication
    runs in every worker.
"""

import contextvars
import json
import logging
import os
import time

from typing import Any, Callable, Dict, Iterable, Iterator, List, Optional, Tuple, TYPE_CHECKING

from ccai.webworks.prodserver.healthchecker import HealthChecker
from ccai.webworks.prodserver.metricscollector import MetricsCollector
from ccai.webworks.prodserver.metricsstore import MetricsStore
from ccai.webworks.prodserver.requesttracer import RequestTracer
from ccai.webworks.prodserver.resourcelimiter import (
    HeaderFieldTooLargeError,
    ResourceLimiter,
    current_memory_usage,
)
from ccai.webworks.prodserver.serverconfig import ServerState
from ccai.webworks.prodserver.sslmanager import SSLManager
from ccai.webworks.prodserver.structuredlogger import StructuredLogger
from ccai.webworks.prodserver.workerstate import WorkerState
from ccai.webworks.wsgi.constants import (
    ENVIRON_REQUEST_ID,
    ENVIRON_REQUEST_TIMEOUT,
    HTTP_STATUS_PHRASES,
)

if TYPE_CHECKING:
    from ccai.webworks.prodserver.serverconfig import ServerConfig


# Default logger for the production middleware
_logger = logging.getLogger("webworks.prodserver.productionmiddleware")


# The ID of the request being served. The ASGI bridge runs a WebApplication
# in a copy of the calling thread's context, so the handlers of the request
# see it as well.
current_request_id: "contextvars.ContextVar[Optional[str]]" = contextvars.ContextVar(
    "webworks_request_id",
    default=None,
)

# Placeholder written to log records outside of a request
NO_REQUEST_ID = "-"

# Content type of the Prometheus text exposition format
PROMETHEUS_CONTENT_TYPE = "text/plain; version=0.0.4; charset=utf-8"


class RequestIdLogFilter(logging.Filter):
    """
        Adds the ID of the request being served to every log record.

        The ID is set as ``record.request_id`` (``"-"`` outside of a request),
        so a log format can show it with ``%(request_id)s``.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """
            Add the request ID to a record.

            :param record: The log record.

            :returns: True, the record is always logged.
        """
        request_id = current_request_id.get()
        if request_id is None:
            request_id = NO_REQUEST_ID
        record.request_id = request_id
        return True


def install_request_id_log_filter() -> None:
    """
        Attach a RequestIdLogFilter to every handler of the root logger.

        Called in each worker process. A handler that has one already is
        left alone.
    """
    for handler in logging.getLogger().handlers:
        has_filter = False
        for existing in handler.filters:
            if isinstance(existing, RequestIdLogFilter):
                has_filter = True
                break
        if not has_filter:
            handler.addFilter(RequestIdLogFilter())
    return


class _RequestRecord:
    """
        What the middleware remembers about one request until it ends.
    """

    def __init__(self, environ: Dict[str, Any], request_id: str, started: float):
        """
            Construct the record of a request.

            :param environ: The WSGI environ.
            :param request_id: The ID of the request.
            :param started: When the request started, a 'time.monotonic' value.
        """
        self.method: str = environ.get("REQUEST_METHOD", "-")
        self.path: str = environ.get("PATH_INFO", "-") or "/"
        self.target: str = environ.get("REQUEST_URI", self.path)
        self.client: str = environ.get("REMOTE_ADDR", "-")
        self.request_id = request_id
        self.started = started
        self.status: Optional[str] = None
        self.bytes_sent: int = 0
        self.failed: bool = False
        self.context_token: Optional[contextvars.Token] = None
        self.span: Any = None
        self.finished: bool = False
        return

    @property
    def status_code(self) -> int:
        """
            The status code of the response.

            :returns: The code, 500 when the application failed before it
                started a response.
        """
        rtnval = 500
        if self.status is not None:
            try:
                rtnval = int(self.status.split(None, 1)[0])
            except (ValueError, IndexError):
                rtnval = 500
        return rtnval


class _ObservedBody:
    """
        The response body of a request, passed on unchanged.

        Counts the bytes the server takes and ends the request record when
        the server closes the body.
    """

    def __init__(self, body: Iterable[bytes], record: _RequestRecord, finish: Callable[[_RequestRecord], None]):
        """
            Construct the observed body.

            :param body: The body the application returned.
            :param record: The record of the request.
            :param finish: Called once with the record when the body is closed.
        """
        self._body = body
        self._iterator: Optional[Iterator[bytes]] = None
        self._record = record
        self._finish = finish
        return

    def __iter__(self) -> "_ObservedBody":
        """
            :returns: The body itself.
        """
        self._iterator = iter(self._body)
        return self

    def __next__(self) -> bytes:
        """
            :returns: The next chunk of the application's body.
        """
        if self._iterator is None:
            self._iterator = iter(self._body)

        chunk = next(self._iterator)
        self._record.bytes_sent += len(chunk)
        return chunk

    def close(self) -> None:
        """
            Close the application's body and end the request.
        """
        try:
            close_body = getattr(self._body, "close", None)
            if close_body is not None:
                close_body()
        finally:
            self._finish(self._record)
        return


class ProductionMiddleware:
    """
        The production layer of the request pipeline.

        See the module documentation for what it does on each request. One
        instance is built by the production server in its master process; each
        worker process works on its own copy.
    """

    def __init__(
        self,
        app: Callable[..., Iterable[bytes]],
        config: "ServerConfig",
        health_checker: HealthChecker,
        metrics_collector: MetricsCollector,
        metrics_store: MetricsStore,
        request_tracer: RequestTracer,
        structured_logger: StructuredLogger,
        resource_limiter: ResourceLimiter,
        ssl_manager: SSLManager,
    ):
        """
            Construct the production middleware.

            :param app: The WSGI application to serve.
            :param config: The production server configuration.
            :param health_checker: Answers the health endpoint.
            :param metrics_collector: Counts the requests of this worker.
            :param metrics_store: Shares the metrics between the workers.
            :param request_tracer: Assigns request IDs and creates spans.
            :param structured_logger: Writes the access log.
            :param resource_limiter: Enforces the header and memory limits.
            :param ssl_manager: Decides the HTTPS redirect.
        """
        self._app = app
        self._config = config
        self._health_checker = health_checker
        self._metrics_collector = metrics_collector
        self._metrics_store = metrics_store
        self._request_tracer = request_tracer
        self._structured_logger = structured_logger
        self._resource_limiter = resource_limiter
        self._ssl_manager = ssl_manager

        self._trace_header = config.trace_header
        self._trace_header_lower = config.trace_header.lower()
        self._trace_environ_key = "HTTP_" + config.trace_header.upper().replace("-", "_")

        self._worker: Any = None
        self._checks_registered = False
        return

    # =========================================================================
    # Properties
    # =========================================================================

    @property
    def app(self) -> Callable[..., Iterable[bytes]]:
        """
            Get the application behind the middleware.

            :returns: The WSGI application.
        """
        return self._app

    @property
    def worker(self) -> Any:
        """
            Get the worker this process serves as.

            :returns: The WSGI worker, or None before on_worker_start().
        """
        return self._worker

    # =========================================================================
    # Worker lifecycle
    # =========================================================================

    def on_worker_start(self, worker: Any) -> None:
        """
            Prepare this worker process and start the application in it.

            :param worker: The WSGI worker that is starting.
        """
        self._worker = worker

        self._structured_logger.set_context(worker_id=worker.worker_id, pid=os.getpid())
        install_request_id_log_filter()

        if not self._checks_registered:
            self._health_checker.register_check(self._worker_is_serving)
            self._health_checker.register_check(self._application_is_serving)
            self._checks_registered = True

        start_hook = getattr(self._app, "on_worker_start", None)
        if start_hook is not None:
            start_hook(worker)

        # The health answer of a worker describes the server's worker count
        # and this worker; the other workers answer for themselves.
        worker_config = getattr(worker, "config", None)
        configured_workers = getattr(worker_config, "workers", 1)
        self._health_checker.set_worker_info(configured_workers, {worker.worker_id: WorkerState.ACTIVE.value})

        self._health_checker.set_server_state(ServerState.RUNNING)
        self._metrics_collector.update_worker_status(worker.worker_id, WorkerState.ACTIVE)
        self._metrics_store.write_snapshot(self._metrics_collector)
        self._metrics_store.start_snapshot_writer(self._metrics_collector)

        return

    def on_worker_exit(self, worker: Any) -> None:
        """
            Stop the application in this worker process.

            The last metrics snapshot of the worker is written first, so the
            master can fold its counts into the totals when it reaps it.

            :param worker: The WSGI worker that has stopped serving.
        """
        self._health_checker.set_server_state(ServerState.SHUTTING_DOWN)
        self._metrics_store.stop_snapshot_writer()
        self._metrics_collector.update_worker_status(worker.worker_id, WorkerState.STOPPED)
        self._metrics_store.write_snapshot(self._metrics_collector)

        exit_hook = getattr(self._app, "on_worker_exit", None)
        if exit_hook is not None:
            exit_hook(worker)

        return

    def _worker_is_serving(self) -> bool:
        """
            Health check: the worker has not been asked to stop.

            :returns: False while the worker drains for a shutdown or recycle.
        """
        rtnval = True
        if self._worker is not None and self._worker.shutdown_requested:
            rtnval = False
        return rtnval

    def _application_is_serving(self) -> bool:
        """
            Health check: the application passes requests on.

            :returns: False when the application reports that it cannot serve,
                as the ASGI bridge does after a failed lifespan startup.
        """
        can_serve = getattr(self._app, "can_serve", True)
        rtnval = can_serve is True
        return rtnval

    # =========================================================================
    # Requests
    # =========================================================================

    def __call__(self, environ: Dict[str, Any], start_response: Callable[..., Any]) -> Iterable[bytes]:
        """
            Serve one request.

            :param environ: The WSGI environ.
            :param start_response: The WSGI start_response callable.

            :returns: The response body.
        """
        request_id = self._assign_request_id(environ)
        record = _RequestRecord(environ, request_id, time.monotonic())
        record.context_token = current_request_id.set(request_id)

        if self._request_tracer.enable_tracing:
            record.span = self._start_span(environ, record)

        self._metrics_collector.increment_connections()

        if self._config.timeout > 0 and ENVIRON_REQUEST_TIMEOUT not in environ:
            environ[ENVIRON_REQUEST_TIMEOUT] = float(self._config.timeout)

        def observing_start_response(status: str, headers: List[Tuple[str, str]], exc_info: Any = None) -> Any:
            record.status = status

            has_trace_header = False
            for name, _value in headers:
                if name.lower() == self._trace_header_lower:
                    has_trace_header = True
                    break

            response_headers = list(headers)
            if not has_trace_header:
                response_headers.append((self._trace_header, request_id))

            if exc_info is not None:
                rtnval = start_response(status, response_headers, exc_info)
            else:
                rtnval = start_response(status, response_headers)
            return rtnval

        body: Optional[Iterable[bytes]] = None
        try:
            body = self._answer_locally(environ, observing_start_response)
            if body is None:
                body = self._app(environ, observing_start_response)
        finally:
            if body is None:
                # The application raised before it returned a body; the
                # server answers it with 500.
                record.failed = True
                self._finish(record)

        rtnval = _ObservedBody(body, record, self._finish)
        return rtnval

    def _assign_request_id(self, environ: Dict[str, Any]) -> str:
        """
            Decide the ID of a request and pass it on to the application.

            :param environ: The WSGI environ; the trace header in it is set to
                the ID, and the ID is stored under ``webworks.request_id``.

            :returns: The request ID.
        """
        received: Dict[str, str] = {}
        received_value = environ.get(self._trace_environ_key)
        if received_value is not None:
            received[self._trace_header] = str(received_value)

        request_id = self._request_tracer.get_or_create_request_id(received)

        environ[self._trace_environ_key] = request_id
        environ[ENVIRON_REQUEST_ID] = request_id

        return request_id

    def _start_span(self, environ: Dict[str, Any], record: _RequestRecord) -> Any:
        """
            Open the tracing span of a request.

            A W3C traceparent header the client sent makes the span a child
            of the client's span.

            :param environ: The WSGI environ.
            :param record: The record of the request.

            :returns: The span.
        """
        parent_span_id = None
        traceparent = environ.get("HTTP_TRACEPARENT")
        if traceparent is not None:
            parsed = self._request_tracer.parse_traceparent({"traceparent": str(traceparent)})
            if parsed is not None:
                parent_span_id = parsed["parent_id"]

        span = self._request_tracer.create_span("http.request", record.request_id, parent_span_id)
        span.set_attribute("http.method", record.method)
        span.set_attribute("http.target", record.target)
        if self._worker is not None:
            span.set_attribute("worker_id", self._worker.worker_id)
        return span

    def _answer_locally(self, environ: Dict[str, Any], start_response: Callable[..., Any]) -> Optional[Iterable[bytes]]:
        """
            Answer the requests the production layer handles itself.

            :param environ: The WSGI environ.
            :param start_response: The start_response of the middleware.

            :returns: The response body, or None to pass the request on to
                the application.
        """
        for key, value in environ.items():
            # The trace header holds the request ID the middleware decided on
            # (a received ID is used only when it is a short token)
            if key.startswith("HTTP_") and key != self._trace_environ_key:
                try:
                    self._resource_limiter.validate_header_field_size(str(value))
                except HeaderFieldTooLargeError as too_large:
                    rtnval = self._plain_response(start_response, too_large.status_code, "Request Header Fields Too Large")
                    return rtnval

        method = environ.get("REQUEST_METHOD", "GET").upper()
        path = environ.get("PATH_INFO", "")

        if method in ("GET", "HEAD"):
            if self._health_checker.is_health_check_path(path):
                result = self._health_checker.handle_health_request()
                body = json.dumps(result["body"]).encode("utf-8")
                rtnval = self._bytes_response(start_response, result["status_code"], body, result["content_type"])
                return rtnval

            if self._metrics_collector.is_metrics_path(path):
                self._metrics_store.write_snapshot(self._metrics_collector)
                totals = self._metrics_store.collect()
                body = totals.get_prometheus_metrics().encode("utf-8")
                rtnval = self._bytes_response(start_response, 200, body, PROMETHEUS_CONTENT_TYPE)
                return rtnval

        if self._ssl_manager.should_redirect_http(self._effective_scheme(environ)):
            rtnval = self._redirect_to_https(environ, start_response)
            return rtnval

        return None

    @staticmethod
    def _effective_scheme(environ: Dict[str, Any]) -> str:
        """
            Find the scheme the client used.

            Behind a proxy that terminates TLS the proxy reports it in
            X-Forwarded-Proto; otherwise it is the scheme of the connection.

            :param environ: The WSGI environ.

            :returns: "http" or "https".
        """
        forwarded = environ.get("HTTP_X_FORWARDED_PROTO")
        if forwarded is not None and str(forwarded).strip() != "":
            rtnval = str(forwarded).split(",", 1)[0].strip().lower()
        else:
            rtnval = str(environ.get("wsgi.url_scheme", "http")).lower()
        return rtnval

    def _redirect_to_https(self, environ: Dict[str, Any], start_response: Callable[..., Any]) -> Iterable[bytes]:
        """
            Redirect a request to the same URL over HTTPS.

            :param environ: The WSGI environ.
            :param start_response: The start_response of the middleware.

            :returns: The response body.
        """
        host = environ.get("HTTP_HOST") or environ.get("SERVER_NAME", "localhost")
        target = environ.get("REQUEST_URI")
        if target is None or target == "":
            target = environ.get("PATH_INFO", "/") or "/"
            query = environ.get("QUERY_STRING", "")
            if query:
                target = target + "?" + query

        location = self._ssl_manager.get_redirect_url("http", host, target)
        body = b"Moved Permanently"
        headers = [
            ("Location", location),
            ("Content-Type", "text/plain; charset=utf-8"),
            ("Content-Length", str(len(body))),
        ]
        start_response("301 Moved Permanently", headers)
        rtnval = [body]
        return rtnval

    @staticmethod
    def _bytes_response(start_response: Callable[..., Any], status_code: int, body: bytes, content_type: str) -> List[bytes]:
        """
            Answer with a complete body.

            :param start_response: The start_response of the middleware.
            :param status_code: HTTP status code.
            :param body: The body.
            :param content_type: Its content type.

            :returns: The response body.
        """
        reason = HTTP_STATUS_PHRASES.get(status_code, "Unknown")
        headers = [
            ("Content-Type", content_type),
            ("Content-Length", str(len(body))),
            ("Cache-Control", "no-store"),
        ]
        start_response(f"{status_code} {reason}", headers)
        rtnval = [body]
        return rtnval

    def _plain_response(self, start_response: Callable[..., Any], status_code: int, message: str) -> List[bytes]:
        """
            Answer with a short text body.

            :param start_response: The start_response of the middleware.
            :param status_code: HTTP status code.
            :param message: The body text.

            :returns: The response body.
        """
        rtnval = self._bytes_response(start_response, status_code, message.encode("utf-8"), "text/plain; charset=utf-8")
        return rtnval

    # =========================================================================
    # End of a request
    # =========================================================================

    def _finish(self, record: _RequestRecord) -> None:
        """
            Record a request that ended: metrics, access log, span, limits.

            :param record: The record of the request.
        """
        if record.finished:
            return
        record.finished = True

        latency_ms = (time.monotonic() - record.started) * 1000.0
        status_code = record.status_code

        self._metrics_collector.record_request(record.path, record.method, status_code, latency_ms)
        self._metrics_collector.decrement_connections()

        worker_id = None
        if self._worker is not None:
            worker_id = self._worker.worker_id

        self._structured_logger.access_log(
            record.method,
            record.target,
            status_code,
            latency_ms,
            request_id=record.request_id,
            worker_id=worker_id,
            client=record.client,
            bytes_sent=record.bytes_sent,
        )

        if record.span is not None:
            record.span.set_attribute("http.status_code", status_code)
            record.span.end()
            self._request_tracer.export_traces()

        self._check_memory_limit(worker_id)

        self._reset_request_id(record)
        return

    def _check_memory_limit(self, worker_id: Optional[int]) -> None:
        """
            Recycle the worker when its memory passed the configured limit.

            :param worker_id: The ID of this worker, None outside a worker.
        """
        limit = self._config.limit_memory
        if limit is None or worker_id is None:
            return

        usage = current_memory_usage()
        self._resource_limiter.update_worker_memory(worker_id, usage)
        self._resource_limiter.check_resource_warnings()

        if self._resource_limiter.check_worker_memory(worker_id) and not self._worker.shutdown_requested:
            _logger.warning(
                "Worker %d uses %d bytes, over the memory limit of %d bytes; it stops and is replaced",
                worker_id,
                usage,
                limit,
            )
            self._worker.request_shutdown(graceful=True)

        return

    @staticmethod
    def _reset_request_id(record: _RequestRecord) -> None:
        """
            Forget the ID of a request that ended.

            :param record: The record of the request.
        """
        token = record.context_token
        record.context_token = None

        if token is None:
            return

        try:
            current_request_id.reset(token)
        except ValueError:
            # The server closed the body on another thread than the one it
            # called the application on; that thread's value is cleared.
            current_request_id.set(None)

        return
