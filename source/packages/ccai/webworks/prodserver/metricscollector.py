"""
    Metrics collection module for the production server.

    This module provides the MetricsCollector class that tracks request
    counts, latency histograms, error rates, active connections, and
    worker status. It supports exporting metrics in Prometheus exposition
    format and sending metrics to a StatsD server.
"""

import logging
import socket
import threading
import time
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ccai.webworks.prodserver.serverconfig import ServerConfig
    from ccai.webworks.prodserver.workerstate import WorkerState


# Default logger for metrics collector
_logger = logging.getLogger("webworks.prodserver.metricscollector")


class MetricsCollector:
    """
        Collects and exposes server metrics for monitoring.

        Tracks request count per endpoint, request latency histograms,
        error rates by status code, active connection count, and worker
        process status. Supports Prometheus exposition format and StatsD
        export.
    """

    def __init__(self, config: "ServerConfig"):
        """
            Construct a MetricsCollector.

            :param config: Server configuration containing metrics settings.
        """
        self._config = config
        self._lock = threading.Lock()

        # Request count per endpoint: (method, endpoint) -> count
        self._request_counts: Dict[str, int] = {}

        # Request latency per endpoint: (method, endpoint) -> list of latencies in ms
        self._request_latencies: Dict[str, List[float]] = {}

        # Error count by status code: status_code -> count
        self._error_counts: Dict[int, int] = {}

        # Total request count
        self._total_requests: int = 0

        # Active connection count
        self._active_connections: int = 0

        # Worker status: worker_id -> WorkerState value string
        self._worker_statuses: Dict[int, str] = {}

        return

    @property
    def metrics_path(self) -> str:
        """
            Get the configured metrics endpoint path.

            :returns: The metrics endpoint path.
        """
        return self._config.metrics_path

    def record_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        latency_ms: float
    ) -> None:
        """
            Record metrics for a completed request.

            Increments the request count for the endpoint, records the
            latency, and tracks error counts for non-2xx status codes.

            :param endpoint: The request endpoint path.
            :param method: HTTP method (GET, POST, etc.).
            :param status_code: Response status code.
            :param latency_ms: Request latency in milliseconds.
        """
        key = f"{method} {endpoint}"

        with self._lock:
            self._total_requests += 1

            # Track request count per endpoint
            if key not in self._request_counts:
                self._request_counts[key] = 0
            self._request_counts[key] += 1

            # Track latency per endpoint
            if key not in self._request_latencies:
                self._request_latencies[key] = []
            self._request_latencies[key].append(latency_ms)

            # Track error counts by status code
            if status_code >= 400:
                if status_code not in self._error_counts:
                    self._error_counts[status_code] = 0
                self._error_counts[status_code] += 1

        return

    def increment_connections(self) -> None:
        """
            Increment the active connection count.
        """
        with self._lock:
            self._active_connections += 1

        return

    def decrement_connections(self) -> None:
        """
            Decrement the active connection count.
        """
        with self._lock:
            if self._active_connections > 0:
                self._active_connections -= 1

        return

    def update_worker_status(self, worker_id: int, state: "WorkerState") -> None:
        """
            Update the status of a worker.

            :param worker_id: The worker identifier.
            :param state: The current worker state.
        """
        with self._lock:
            self._worker_statuses[worker_id] = state.value

        return

    def remove_worker_status(self, worker_id: int) -> None:
        """
            Remove a worker from status tracking.

            :param worker_id: The worker identifier to remove.
        """
        with self._lock:
            self._worker_statuses.pop(worker_id, None)

        return

    def get_request_count(self, endpoint: Optional[str] = None, method: Optional[str] = None) -> int:
        """
            Get the request count, optionally filtered by endpoint and method.

            :param endpoint: Optional endpoint path to filter by.
            :param method: Optional HTTP method to filter by.

            :returns: The request count.
        """
        with self._lock:
            if endpoint is None and method is None:
                return self._total_requests

            if endpoint is not None and method is not None:
                key = f"{method} {endpoint}"
                return self._request_counts.get(key, 0)

            # Filter by partial match
            total = 0
            for key, count in self._request_counts.items():
                parts = key.split(" ", 1)
                if len(parts) == 2:
                    k_method, k_endpoint = parts
                    if method is not None and k_method == method:
                        total += count
                    elif endpoint is not None and k_endpoint == endpoint:
                        total += count
            return total

    def get_request_latencies(self, endpoint: Optional[str] = None, method: Optional[str] = None) -> List[float]:
        """
            Get recorded latencies, optionally filtered by endpoint and method.

            :param endpoint: Optional endpoint path to filter by.
            :param method: Optional HTTP method to filter by.

            :returns: List of latency values in milliseconds.
        """
        with self._lock:
            if endpoint is not None and method is not None:
                key = f"{method} {endpoint}"
                return list(self._request_latencies.get(key, []))

            # Return all latencies
            all_latencies: List[float] = []
            for latencies in self._request_latencies.values():
                all_latencies.extend(latencies)
            return all_latencies

    def get_error_count(self, status_code: Optional[int] = None) -> int:
        """
            Get the error count, optionally filtered by status code.

            :param status_code: Optional status code to filter by.

            :returns: The error count.
        """
        with self._lock:
            if status_code is not None:
                return self._error_counts.get(status_code, 0)

            total = 0
            for count in self._error_counts.values():
                total += count
            return total

    def get_active_connections(self) -> int:
        """
            Get the current active connection count.

            :returns: The number of active connections.
        """
        with self._lock:
            return self._active_connections

    def get_worker_statuses(self) -> Dict[int, str]:
        """
            Get the current worker statuses.

            :returns: Dictionary mapping worker IDs to state strings.
        """
        with self._lock:
            return dict(self._worker_statuses)

    def is_metrics_path(self, request_path: str) -> bool:
        """
            Check if a request path matches the metrics endpoint.

            :param request_path: The request path to check.

            :returns: True if the path matches the metrics endpoint.
        """
        rtnval = request_path == self._config.metrics_path

        return rtnval

    def get_prometheus_metrics(self) -> str:
        """
            Export metrics in Prometheus exposition format.

            Generates a text representation of all collected metrics
            following the Prometheus exposition format specification.

            :returns: Prometheus-formatted metrics string.
        """
        lines: List[str] = []

        with self._lock:
            # Total request count
            lines.append("# HELP webworks_requests_total Total number of requests.")
            lines.append("# TYPE webworks_requests_total counter")
            lines.append(f"webworks_requests_total {self._total_requests}")

            # Request count per endpoint
            lines.append("# HELP webworks_requests_per_endpoint_total Requests per endpoint.")
            lines.append("# TYPE webworks_requests_per_endpoint_total counter")
            for key, count in sorted(self._request_counts.items()):
                parts = key.split(" ", 1)
                if len(parts) == 2:
                    method, endpoint = parts
                    lines.append(
                        f'webworks_requests_per_endpoint_total{{method="{method}",endpoint="{endpoint}"}} {count}'
                    )

            # Request latency summary
            lines.append("# HELP webworks_request_latency_ms Request latency in milliseconds.")
            lines.append("# TYPE webworks_request_latency_ms summary")
            for key, latencies in sorted(self._request_latencies.items()):
                parts = key.split(" ", 1)
                if len(parts) == 2 and len(latencies) > 0:
                    method, endpoint = parts
                    count = len(latencies)
                    total = sum(latencies)
                    lines.append(
                        f'webworks_request_latency_ms_count{{method="{method}",endpoint="{endpoint}"}} {count}'
                    )
                    lines.append(
                        f'webworks_request_latency_ms_sum{{method="{method}",endpoint="{endpoint}"}} {total:.2f}'
                    )

            # Error counts by status code
            lines.append("# HELP webworks_errors_total Total errors by status code.")
            lines.append("# TYPE webworks_errors_total counter")
            for status_code, count in sorted(self._error_counts.items()):
                lines.append(
                    f'webworks_errors_total{{status_code="{status_code}"}} {count}'
                )

            # Active connections gauge
            lines.append("# HELP webworks_active_connections Current active connections.")
            lines.append("# TYPE webworks_active_connections gauge")
            lines.append(f"webworks_active_connections {self._active_connections}")

            # Worker status
            lines.append("# HELP webworks_worker_status Worker process status.")
            lines.append("# TYPE webworks_worker_status gauge")
            for worker_id, state in sorted(self._worker_statuses.items()):
                lines.append(
                    f'webworks_worker_status{{worker_id="{worker_id}",state="{state}"}} 1'
                )

        # Prometheus format requires trailing newline
        rtnval = "\n".join(lines) + "\n"

        return rtnval

    def send_to_statsd(self) -> bool:
        """
            Send metrics to a StatsD server.

            Sends the current metrics to the configured StatsD host
            and port using UDP. Returns True if metrics were sent
            successfully, False otherwise.

            :returns: True if metrics were sent, False on error or if not configured.
        """
        if self._config.statsd_host is None:
            return False

        host = self._config.statsd_host
        port = self._config.statsd_port

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            try:
                with self._lock:
                    # Send total request count
                    msg = f"webworks.requests.total:{self._total_requests}|c"
                    sock.sendto(msg.encode("utf-8"), (host, port))

                    # Send request counts per endpoint
                    for key, count in self._request_counts.items():
                        safe_key = key.replace(" ", ".").replace("/", "_")
                        msg = f"webworks.requests.{safe_key}:{count}|c"
                        sock.sendto(msg.encode("utf-8"), (host, port))

                    # Send error counts
                    for status_code, count in self._error_counts.items():
                        msg = f"webworks.errors.{status_code}:{count}|c"
                        sock.sendto(msg.encode("utf-8"), (host, port))

                    # Send active connections
                    msg = f"webworks.connections.active:{self._active_connections}|g"
                    sock.sendto(msg.encode("utf-8"), (host, port))

            finally:
                sock.close()

        except OSError as exc:
            _logger.warning("Failed to send metrics to StatsD at %s:%d: %s", host, port, exc)
            return False

        return True

    def handle_metrics_request(self) -> Dict[str, Any]:
        """
            Handle a metrics endpoint request.

            Returns a dictionary containing the HTTP status code and
            Prometheus-formatted metrics body.

            :returns: Dictionary with 'status_code', 'body', and 'content_type' keys.
        """
        body = self.get_prometheus_metrics()

        rtnval = {
            "status_code": 200,
            "body": body,
            "content_type": "text/plain; version=0.0.4; charset=utf-8",
        }

        return rtnval

    def get_metrics_summary(self) -> Dict[str, Any]:
        """
            Get a summary of all collected metrics.

            :returns: Dictionary with aggregated metrics including
                      total_requests, error_counts, active_connections,
                      worker_statuses, and per-endpoint breakdowns.
        """
        with self._lock:
            latency_summary: Dict[str, Dict[str, Any]] = {}
            for key, latencies in self._request_latencies.items():
                if len(latencies) > 0:
                    latency_summary[key] = {
                        "count": len(latencies),
                        "min": min(latencies),
                        "max": max(latencies),
                        "avg": sum(latencies) / len(latencies),
                    }

            rtnval: Dict[str, Any] = {
                "total_requests": self._total_requests,
                "request_counts": dict(self._request_counts),
                "error_counts": dict(self._error_counts),
                "active_connections": self._active_connections,
                "worker_statuses": dict(self._worker_statuses),
                "latency_summary": latency_summary,
            }

        return rtnval

    def reset(self) -> None:
        """
            Reset all collected metrics.
        """
        with self._lock:
            self._request_counts.clear()
            self._request_latencies.clear()
            self._error_counts.clear()
            self._total_requests = 0
            self._active_connections = 0
            self._worker_statuses.clear()

        return
