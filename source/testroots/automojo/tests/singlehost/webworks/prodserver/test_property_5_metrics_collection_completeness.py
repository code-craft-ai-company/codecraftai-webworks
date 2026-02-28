"""
    Property-Based Tests for Metrics Collection Completeness (Property 5).

    Property 5: Metrics Collection Completeness
    For any completed request, the MetricsCollector SHALL record the
    request count, latency, and status code, and these metrics SHALL
    be accurately reflected in the Prometheus exposition format output.

    Validates: Requirements 6.1, 6.2, 6.3, 6.6
"""

import random
import string

from automojo.webworks.prodserver.metricscollector import MetricsCollector
from automojo.webworks.prodserver.serverconfig import ServerConfig
from automojo.webworks.prodserver.workerstate import WorkerState


# =============================================================================
# Helpers
# =============================================================================

HTTP_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]

SUCCESS_STATUS_CODES = [200, 201, 204, 301, 302, 304]
ERROR_STATUS_CODES = [400, 401, 403, 404, 405, 409, 413, 429, 500, 502, 503, 504]
ALL_STATUS_CODES = SUCCESS_STATUS_CODES + ERROR_STATUS_CODES

ENDPOINTS = [
    "/api/users",
    "/api/items",
    "/api/orders",
    "/api/products",
    "/api/auth/login",
    "/api/auth/logout",
    "/health",
    "/metrics",
    "/",
    "/api/v2/data",
]

WORKER_STATES = [WorkerState.IDLE, WorkerState.ACTIVE, WorkerState.SHUTTING_DOWN, WorkerState.STOPPED]


# =============================================================================
# Random Generators
# =============================================================================

def generate_method() -> str:
    """
        Generate a random HTTP method.
    """
    return random.choice(HTTP_METHODS)


def generate_endpoint() -> str:
    """
        Generate a random endpoint path.
    """
    return random.choice(ENDPOINTS)


def generate_status_code() -> int:
    """
        Generate a random HTTP status code.
    """
    return random.choice(ALL_STATUS_CODES)


def generate_latency() -> float:
    """
        Generate a random latency value between 0.1 and 5000.0 ms.
    """
    return round(random.uniform(0.1, 5000.0), 2)


def generate_request_batch(count: int) -> list:
    """
        Generate a batch of random request records.

        :param count: Number of requests to generate.

        :returns: List of tuples (endpoint, method, status_code, latency_ms).
    """
    batch = []
    for _ in range(count):
        batch.append((
            generate_endpoint(),
            generate_method(),
            generate_status_code(),
            generate_latency(),
        ))
    return batch


# =============================================================================
# Property-Based Tests
# =============================================================================

# Feature: production-server, Property 5: Metrics Collection Completeness
# *For any* completed request, the MetricsCollector SHALL record the
# request count, latency, and status code, and these metrics SHALL
# be accurately reflected in the Prometheus exposition format output.
# **Validates: Requirements 6.1, 6.2, 6.3, 6.6**


def test_property_5_request_count_per_endpoint():
    """
        Property 5: Request Count Per Endpoint

        For any sequence of requests, the MetricsCollector SHALL
        accurately track the request count per endpoint.

        **Validates: Requirement 6.1**
    """
    for iteration in range(50):
        config = ServerConfig()
        collector = MetricsCollector(config=config)

        batch_size = random.randint(1, 30)
        batch = generate_request_batch(batch_size)

        # Track expected counts
        expected_counts = {}
        for endpoint, method, status_code, latency_ms in batch:
            key = f"{method} {endpoint}"
            if key not in expected_counts:
                expected_counts[key] = 0
            expected_counts[key] += 1

        # Record all requests
        for endpoint, method, status_code, latency_ms in batch:
            collector.record_request(endpoint, method, status_code, latency_ms)

        # Verify total count
        total = collector.get_request_count()
        if total != batch_size:
            errmsg = (
                f"Iteration {iteration}: expected total count {batch_size}, "
                f"got {total}"
            )
            raise AssertionError(errmsg)

        # Verify per-endpoint counts
        for key, expected in expected_counts.items():
            parts = key.split(" ", 1)
            method, endpoint = parts[0], parts[1]
            actual = collector.get_request_count(endpoint=endpoint, method=method)
            if actual != expected:
                errmsg = (
                    f"Iteration {iteration}: expected count {expected} for "
                    f"'{key}', got {actual}"
                )
                raise AssertionError(errmsg)

    return


def test_property_5_latency_tracking():
    """
        Property 5: Latency Tracking

        For any sequence of requests, the MetricsCollector SHALL
        record all latency values accurately.

        **Validates: Requirement 6.2**
    """
    for iteration in range(50):
        config = ServerConfig()
        collector = MetricsCollector(config=config)

        batch_size = random.randint(1, 30)
        batch = generate_request_batch(batch_size)

        # Track expected latencies
        expected_latencies = {}
        for endpoint, method, status_code, latency_ms in batch:
            key = f"{method} {endpoint}"
            if key not in expected_latencies:
                expected_latencies[key] = []
            expected_latencies[key].append(latency_ms)

        # Record all requests
        for endpoint, method, status_code, latency_ms in batch:
            collector.record_request(endpoint, method, status_code, latency_ms)

        # Verify latencies per endpoint
        for key, expected in expected_latencies.items():
            parts = key.split(" ", 1)
            method, endpoint = parts[0], parts[1]
            actual = collector.get_request_latencies(endpoint=endpoint, method=method)

            if len(actual) != len(expected):
                errmsg = (
                    f"Iteration {iteration}: expected {len(expected)} latencies "
                    f"for '{key}', got {len(actual)}"
                )
                raise AssertionError(errmsg)

            for idx in range(len(expected)):
                if abs(actual[idx] - expected[idx]) > 0.001:
                    errmsg = (
                        f"Iteration {iteration}: latency mismatch at index {idx} "
                        f"for '{key}': expected {expected[idx]}, got {actual[idx]}"
                    )
                    raise AssertionError(errmsg)

    return


def test_property_5_error_rate_tracking():
    """
        Property 5: Error Rate Tracking

        For any sequence of requests, the MetricsCollector SHALL
        accurately track error counts by status code for all
        status codes >= 400.

        **Validates: Requirement 6.3**
    """
    for iteration in range(50):
        config = ServerConfig()
        collector = MetricsCollector(config=config)

        batch_size = random.randint(1, 30)
        batch = generate_request_batch(batch_size)

        # Track expected error counts
        expected_errors = {}
        for endpoint, method, status_code, latency_ms in batch:
            if status_code >= 400:
                if status_code not in expected_errors:
                    expected_errors[status_code] = 0
                expected_errors[status_code] += 1

        expected_total_errors = sum(expected_errors.values())

        # Record all requests
        for endpoint, method, status_code, latency_ms in batch:
            collector.record_request(endpoint, method, status_code, latency_ms)

        # Verify total error count
        actual_total = collector.get_error_count()
        if actual_total != expected_total_errors:
            errmsg = (
                f"Iteration {iteration}: expected total errors "
                f"{expected_total_errors}, got {actual_total}"
            )
            raise AssertionError(errmsg)

        # Verify per-status-code error counts
        for status_code, expected in expected_errors.items():
            actual = collector.get_error_count(status_code=status_code)
            if actual != expected:
                errmsg = (
                    f"Iteration {iteration}: expected {expected} errors for "
                    f"status {status_code}, got {actual}"
                )
                raise AssertionError(errmsg)

    return


def test_property_5_prometheus_reflects_recorded_metrics():
    """
        Property 5: Prometheus Reflects Recorded Metrics

        For any sequence of recorded requests, the Prometheus exposition
        format output SHALL accurately reflect the total request count,
        per-endpoint counts, and error counts.

        **Validates: Requirement 6.6**
    """
    for iteration in range(50):
        config = ServerConfig()
        collector = MetricsCollector(config=config)

        batch_size = random.randint(1, 20)
        batch = generate_request_batch(batch_size)

        # Track expected values
        expected_total = batch_size
        expected_per_endpoint = {}
        expected_errors = {}

        for endpoint, method, status_code, latency_ms in batch:
            key = f"{method} {endpoint}"
            if key not in expected_per_endpoint:
                expected_per_endpoint[key] = 0
            expected_per_endpoint[key] += 1

            if status_code >= 400:
                if status_code not in expected_errors:
                    expected_errors[status_code] = 0
                expected_errors[status_code] += 1

        # Record all requests
        for endpoint, method, status_code, latency_ms in batch:
            collector.record_request(endpoint, method, status_code, latency_ms)

        # Get Prometheus output
        output = collector.get_prometheus_metrics()

        # Verify total request count in output
        expected_total_line = f"webworks_requests_total {expected_total}"
        if expected_total_line not in output:
            errmsg = (
                f"Iteration {iteration}: expected '{expected_total_line}' "
                f"in Prometheus output"
            )
            raise AssertionError(errmsg)

        # Verify per-endpoint counts in output
        for key, count in expected_per_endpoint.items():
            parts = key.split(" ", 1)
            method, endpoint = parts[0], parts[1]
            expected_line = (
                f'webworks_requests_per_endpoint_total'
                f'{{method="{method}",endpoint="{endpoint}"}} {count}'
            )
            if expected_line not in output:
                errmsg = (
                    f"Iteration {iteration}: expected '{expected_line}' "
                    f"in Prometheus output"
                )
                raise AssertionError(errmsg)

        # Verify error counts in output
        for status_code, count in expected_errors.items():
            expected_line = (
                f'webworks_errors_total{{status_code="{status_code}"}} {count}'
            )
            if expected_line not in output:
                errmsg = (
                    f"Iteration {iteration}: expected '{expected_line}' "
                    f"in Prometheus output"
                )
                raise AssertionError(errmsg)

        # Verify output ends with newline
        if not output.endswith("\n"):
            errmsg = (
                f"Iteration {iteration}: Prometheus output must end with newline"
            )
            raise AssertionError(errmsg)

    return


def test_property_5_prometheus_latency_sum_matches():
    """
        Property 5: Prometheus Latency Sum Matches

        For any sequence of recorded requests, the latency sum in
        Prometheus output SHALL match the sum of recorded latencies.

        **Validates: Requirements 6.2, 6.6**
    """
    for iteration in range(50):
        config = ServerConfig()
        collector = MetricsCollector(config=config)

        # Use a single endpoint to simplify verification
        endpoint = generate_endpoint()
        method = generate_method()
        batch_size = random.randint(1, 20)

        expected_sum = 0.0
        for _ in range(batch_size):
            latency = generate_latency()
            expected_sum += latency
            collector.record_request(endpoint, method, 200, latency)

        output = collector.get_prometheus_metrics()

        # Find the latency sum line
        expected_prefix = (
            f'webworks_request_latency_ms_sum'
            f'{{method="{method}",endpoint="{endpoint}"}}'
        )

        found = False
        for line in output.split("\n"):
            if line.startswith(expected_prefix):
                found = True
                parts = line.split(" ")
                actual_sum = float(parts[-1])
                if abs(actual_sum - expected_sum) > 0.1:
                    errmsg = (
                        f"Iteration {iteration}: expected latency sum "
                        f"{expected_sum:.2f}, got {actual_sum:.2f}"
                    )
                    raise AssertionError(errmsg)
                break

        if not found:
            errmsg = (
                f"Iteration {iteration}: latency sum metric not found "
                f"for {method} {endpoint}"
            )
            raise AssertionError(errmsg)

    return


def test_property_5_prometheus_latency_count_matches():
    """
        Property 5: Prometheus Latency Count Matches

        For any sequence of recorded requests, the latency count in
        Prometheus output SHALL match the number of recorded requests.

        **Validates: Requirements 6.2, 6.6**
    """
    for iteration in range(50):
        config = ServerConfig()
        collector = MetricsCollector(config=config)

        endpoint = generate_endpoint()
        method = generate_method()
        batch_size = random.randint(1, 20)

        for _ in range(batch_size):
            latency = generate_latency()
            collector.record_request(endpoint, method, 200, latency)

        output = collector.get_prometheus_metrics()

        expected_line = (
            f'webworks_request_latency_ms_count'
            f'{{method="{method}",endpoint="{endpoint}"}} {batch_size}'
        )

        if expected_line not in output:
            errmsg = (
                f"Iteration {iteration}: expected '{expected_line}' "
                f"in Prometheus output"
            )
            raise AssertionError(errmsg)

    return
