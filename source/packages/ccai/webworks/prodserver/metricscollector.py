"""
    Metrics collection module for the production server.

    This module provides the MetricsCollector class that tracks request
    counts, latency histograms, error rates, active connections, and
    worker status. It supports exporting metrics in Prometheus exposition
    format and sending metrics to a StatsD server.

    Memory stays bounded however long a worker runs: latencies are kept as
    histogram bucket counts plus a window of the most recent values, and the
    number of distinct endpoints is capped (further endpoints are counted
    under OTHER_ENDPOINT). A collector's state can be exported and merged
    into another collector, which is how the production server adds up the
    metrics of its worker processes (see MetricsStore).
"""

import logging
import socket
import threading
from collections import deque
from typing import Any, Deque, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ccai.webworks.prodserver.serverconfig import ServerConfig
    from ccai.webworks.prodserver.workerstate import WorkerState


# Default logger for metrics collector
_logger = logging.getLogger("webworks.prodserver.metricscollector")


# Upper bounds of the latency histogram buckets, in milliseconds. The last
# bucket, +Inf, is implied.
LATENCY_BUCKETS_MS: List[float] = [5.0, 10.0, 25.0, 50.0, 100.0, 250.0, 500.0, 1000.0, 2500.0, 5000.0, 10000.0]

# Number of recent latencies kept per endpoint for get_request_latencies()
RECENT_LATENCY_WINDOW: int = 1000

# Largest number of distinct (method, endpoint) keys tracked. Request paths
# come from clients, so without a cap every distinct URL would add a series.
MAX_ENDPOINT_KEYS: int = 1000

# The endpoint label requests are counted under once the cap is reached
OTHER_ENDPOINT: str = "__other__"


def _escape_label(value: str) -> str:
    """
        Escape a value for use inside a Prometheus label.

        :param value: The label value.

        :returns: The value with backslash, quote and newline escaped.
    """
    rtnval = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return rtnval


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

        # Most recent latencies per endpoint: (method, endpoint) -> window of latencies in ms
        self._request_latencies: Dict[str, Deque[float]] = {}

        # Latency histogram per endpoint: count, sum and bucket counts (not
        # cumulative, one more than LATENCY_BUCKETS_MS for +Inf)
        self._latency_counts: Dict[str, int] = {}
        self._latency_sums: Dict[str, float] = {}
        self._latency_buckets: Dict[str, List[int]] = {}

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
        with self._lock:
            key = self._endpoint_key(method, endpoint)

            self._total_requests += 1

            # Track request count per endpoint
            if key not in self._request_counts:
                self._request_counts[key] = 0
            self._request_counts[key] += 1

            # Track latency per endpoint
            if key not in self._request_latencies:
                self._request_latencies[key] = deque(maxlen=RECENT_LATENCY_WINDOW)
            self._request_latencies[key].append(latency_ms)
            self._add_to_histogram(key, latency_ms)

            # Track error counts by status code
            if status_code >= 400:
                if status_code not in self._error_counts:
                    self._error_counts[status_code] = 0
                self._error_counts[status_code] += 1

        return

    def _endpoint_key(self, method: str, endpoint: str) -> str:
        """
            Build the key a request is counted under.

            Called with the lock held. Once MAX_ENDPOINT_KEYS keys exist, an
            endpoint that has no key yet is counted under OTHER_ENDPOINT.

            :param method: HTTP method.
            :param endpoint: The request endpoint path.

            :returns: The key "<method> <endpoint>".
        """
        key = f"{method} {endpoint}"

        if key not in self._request_counts and len(self._request_counts) >= MAX_ENDPOINT_KEYS:
            key = f"{method} {OTHER_ENDPOINT}"

        return key

    def _add_to_histogram(self, key: str, latency_ms: float) -> None:
        """
            Add one latency to the histogram of an endpoint.

            Called with the lock held.

            :param key: The endpoint key.
            :param latency_ms: The latency in milliseconds.
        """
        if key not in self._latency_buckets:
            self._latency_buckets[key] = [0] * (len(LATENCY_BUCKETS_MS) + 1)
            self._latency_counts[key] = 0
            self._latency_sums[key] = 0.0

        bucket_index = len(LATENCY_BUCKETS_MS)
        for index, upper_bound in enumerate(LATENCY_BUCKETS_MS):
            if latency_ms <= upper_bound:
                bucket_index = index
                break

        self._latency_buckets[key][bucket_index] += 1
        self._latency_counts[key] += 1
        self._latency_sums[key] += latency_ms

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
                    method = _escape_label(parts[0])
                    endpoint = _escape_label(parts[1])
                    lines.append(
                        f'webworks_requests_per_endpoint_total{{method="{method}",endpoint="{endpoint}"}} {count}'
                    )

            # Request latency histogram
            lines.append("# HELP webworks_request_latency_ms Request latency in milliseconds.")
            lines.append("# TYPE webworks_request_latency_ms histogram")
            for key in sorted(self._latency_counts.keys()):
                parts = key.split(" ", 1)
                if len(parts) != 2:
                    continue
                method = _escape_label(parts[0])
                endpoint = _escape_label(parts[1])
                labels = f'method="{method}",endpoint="{endpoint}"'
                cumulative = 0
                buckets = self._latency_buckets[key]
                for index, upper_bound in enumerate(LATENCY_BUCKETS_MS):
                    cumulative += buckets[index]
                    lines.append(
                        f'webworks_request_latency_ms_bucket{{{labels},le="{upper_bound:g}"}} {cumulative}'
                    )
                cumulative += buckets[len(LATENCY_BUCKETS_MS)]
                lines.append(f'webworks_request_latency_ms_bucket{{{labels},le="+Inf"}} {cumulative}')
                lines.append(
                    f'webworks_request_latency_ms_count{{{labels}}} {self._latency_counts[key]}'
                )
                lines.append(
                    f'webworks_request_latency_ms_sum{{{labels}}} {self._latency_sums[key]:.2f}'
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
            self._latency_counts.clear()
            self._latency_sums.clear()
            self._latency_buckets.clear()
            self._error_counts.clear()
            self._total_requests = 0
            self._active_connections = 0
            self._worker_statuses.clear()

        return

    # =========================================================================
    # Sharing between processes
    # =========================================================================

    def export_state(self) -> Dict[str, Any]:
        """
            Export the counters of this collector.

            The state holds the counters, histograms and gauges, not the
            window of recent latencies. It is plain JSON data, so a worker
            process can write it to a file for the others to read.

            :returns: Dictionary with the state of the collector.
        """
        with self._lock:
            rtnval: Dict[str, Any] = {
                "total_requests": self._total_requests,
                "request_counts": dict(self._request_counts),
                "latency_counts": dict(self._latency_counts),
                "latency_sums": dict(self._latency_sums),
                "latency_buckets": {key: list(value) for key, value in self._latency_buckets.items()},
                "error_counts": {str(code): count for code, count in self._error_counts.items()},
                "active_connections": self._active_connections,
                "worker_statuses": {str(wid): state for wid, state in self._worker_statuses.items()},
            }

        return rtnval

    def merge_state(self, state: Dict[str, Any], include_gauges: bool = True) -> None:
        """
            Add an exported state to this collector.

            Counters and histograms are added up. The gauges (active
            connections, worker status) describe a live process and are
            added only when include_gauges is True.

            :param state: A state returned by export_state().
            :param include_gauges: False for the state of a process that has ended.
        """
        bucket_count = len(LATENCY_BUCKETS_MS) + 1

        with self._lock:
            self._total_requests += int(state.get("total_requests", 0))

            for key, count in state.get("request_counts", {}).items():
                self._request_counts[key] = self._request_counts.get(key, 0) + int(count)

            for key, count in state.get("latency_counts", {}).items():
                self._latency_counts[key] = self._latency_counts.get(key, 0) + int(count)

            for key, total in state.get("latency_sums", {}).items():
                self._latency_sums[key] = self._latency_sums.get(key, 0.0) + float(total)

            for key, buckets in state.get("latency_buckets", {}).items():
                merged = self._latency_buckets.get(key)
                if merged is None:
                    merged = [0] * bucket_count
                    self._latency_buckets[key] = merged
                for index in range(min(bucket_count, len(buckets))):
                    merged[index] += int(buckets[index])

            for code, count in state.get("error_counts", {}).items():
                status_code = int(code)
                self._error_counts[status_code] = self._error_counts.get(status_code, 0) + int(count)

            if include_gauges:
                self._active_connections += int(state.get("active_connections", 0))
                for worker_id, worker_state in state.get("worker_statuses", {}).items():
                    self._worker_statuses[int(worker_id)] = str(worker_state)

        return
