"""
    Tests for the production server MetricsCollector class.

    This module contains unit tests for metrics collection functionality
    including request counting, latency tracking, error rate tracking,
    active connection tracking, worker status tracking, Prometheus
    exposition format, and StatsD export.
"""

from automojo.webworks.prodserver.metricscollector import MetricsCollector
from automojo.webworks.prodserver.serverconfig import ServerConfig
from automojo.webworks.prodserver.workerstate import WorkerState


# =============================================================================
# Unit Tests for MetricsCollector - Request Counting
# =============================================================================

def test_record_request_increments_total():
    """
        Test that recording a request increments the total request count.
    """
    config = ServerConfig()
    collector = MetricsCollector(config=config)

    collector.record_request("/api/users", "GET", 200, 15.0)

    result = collector.get_request_count()

    if result != 1:
        errmsg = f"Expected total request count 1, got {result}"
        raise AssertionError(errmsg)

    return


def test_record_multiple_requests_increments_total():
    """
        Test that recording multiple requests increments the total count.
    """
    config = ServerConfig()
    collector = MetricsCollector(config=config)

    collector.record_request("/api/users", "GET", 200, 10.0)
    collector.record_request("/api/users", "POST", 201, 20.0)
    collector.record_request("/api/items", "GET", 200, 5.0)

    result = collector.get_request_count()

    if result != 3:
        errmsg = f"Expected total request count 3, got {result}"
        raise AssertionError(errmsg)

    return


def test_record_request_tracks_per_endpoint():
    """
        Test that request counts are tracked per endpoint.
    """
    config = ServerConfig()
    collector = MetricsCollector(config=config)

    collector.record_request("/api/users", "GET", 200, 10.0)
    collector.record_request("/api/users", "GET", 200, 12.0)
    collector.record_request("/api/items", "GET", 200, 5.0)

    users_count = collector.get_request_count(endpoint="/api/users", method="GET")
    items_count = collector.get_request_count(endpoint="/api/items", method="GET")

    if users_count != 2:
        errmsg = f"Expected 2 requests for GET /api/users, got {users_count}"
        raise AssertionError(errmsg)

    if items_count != 1:
        errmsg = f"Expected 1 request for GET /api/items, got {items_count}"
        raise AssertionError(errmsg)

    return


def test_record_request_tracks_different_methods():
    """
        Test that request counts distinguish between HTTP methods.
    """
    config = ServerConfig()
    collector = MetricsCollector(config=config)

    collector.record_request("/api/users", "GET", 200, 10.0)
    collector.record_request("/api/users", "POST", 201, 20.0)

    get_count = collector.get_request_count(endpoint="/api/users", method="GET")
    post_count = collector.get_request_count(endpoint="/api/users", method="POST")

    if get_count != 1:
        errmsg = f"Expected 1 GET request, got {get_count}"
        raise AssertionError(errmsg)

    if post_count != 1:
        errmsg = f"Expected 1 POST request, got {post_count}"
        raise AssertionError(errmsg)

    return


def test_get_request_count_returns_zero_for_unknown():
    """
        Test that get_request_count returns 0 for unknown endpoints.
    """
    config = ServerConfig()
    collector = MetricsCollector(config=config)

    result = collector.get_request_count(endpoint="/unknown", method="GET")

    if result != 0:
        errmsg = f"Expected 0 for unknown endpoint, got {result}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for MetricsCollector - Latency Tracking
# =============================================================================

def test_record_request_tracks_latency():
    """
        Test that request latencies are recorded.
    """
    config = ServerConfig()
    collector = MetricsCollector(config=config)

    collector.record_request("/api/users", "GET", 200, 15.5)
    collector.record_request("/api/users", "GET", 200, 22.3)

    latencies = collector.get_request_latencies(endpoint="/api/users", method="GET")

    if len(latencies) != 2:
        errmsg = f"Expected 2 latency entries, got {len(latencies)}"
        raise AssertionError(errmsg)

    if abs(latencies[0] - 15.5) > 0.001:
        errmsg = f"Expected first latency 15.5, got {latencies[0]}"
        raise AssertionError(errmsg)

    if abs(latencies[1] - 22.3) > 0.001:
        errmsg = f"Expected second latency 22.3, got {latencies[1]}"
        raise AssertionError(errmsg)

    return


def test_get_request_latencies_returns_empty_for_unknown():
    """
        Test that get_request_latencies returns empty list for unknown endpoints.
    """
    config = ServerConfig()
    collector = MetricsCollector(config=config)

    latencies = collector.get_request_latencies(endpoint="/unknown", method="GET")

    if len(latencies) != 0:
        errmsg = f"Expected empty latencies for unknown endpoint, got {len(latencies)}"
        raise AssertionError(errmsg)

    return


def test_get_all_latencies():
    """
        Test that get_request_latencies returns all latencies when no filter.
    """
    config = ServerConfig()
    collector = MetricsCollector(config=config)

    collector.record_request("/api/users", "GET", 200, 10.0)
    collector.record_request("/api/items", "GET", 200, 20.0)

    latencies = collector.get_request_latencies()

    if len(latencies) != 2:
        errmsg = f"Expected 2 total latencies, got {len(latencies)}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for MetricsCollector - Error Rate Tracking
# =============================================================================

def test_record_request_tracks_errors():
    """
        Test that error counts are tracked for 4xx and 5xx status codes.
    """
    config = ServerConfig()
    collector = MetricsCollector(config=config)

    collector.record_request("/api/users", "GET", 404, 5.0)
    collector.record_request("/api/users", "POST", 500, 10.0)
    collector.record_request("/api/users", "GET", 200, 8.0)

    error_404 = collector.get_error_count(status_code=404)
    error_500 = collector.get_error_count(status_code=500)
    total_errors = collector.get_error_count()

    if error_404 != 1:
        errmsg = f"Expected 1 error for 404, got {error_404}"
        raise AssertionError(errmsg)

    if error_500 != 1:
        errmsg = f"Expected 1 error for 500, got {error_500}"
        raise AssertionError(errmsg)

    if total_errors != 2:
        errmsg = f"Expected 2 total errors, got {total_errors}"
        raise AssertionError(errmsg)

    return


def test_record_request_does_not_track_success_as_error():
    """
        Test that 2xx and 3xx status codes are not counted as errors.
    """
    config = ServerConfig()
    collector = MetricsCollector(config=config)

    collector.record_request("/api/users", "GET", 200, 5.0)
    collector.record_request("/api/users", "GET", 201, 5.0)
    collector.record_request("/api/users", "GET", 301, 5.0)

    total_errors = collector.get_error_count()

    if total_errors != 0:
        errmsg = f"Expected 0 errors for success codes, got {total_errors}"
        raise AssertionError(errmsg)

    return


def test_get_error_count_returns_zero_for_unknown_code():
    """
        Test that get_error_count returns 0 for unrecorded status codes.
    """
    config = ServerConfig()
    collector = MetricsCollector(config=config)

    result = collector.get_error_count(status_code=418)

    if result != 0:
        errmsg = f"Expected 0 for unknown status code, got {result}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for MetricsCollector - Active Connections
# =============================================================================

def test_increment_connections():
    """
        Test that increment_connections increases the count.
    """
    config = ServerConfig()
    collector = MetricsCollector(config=config)

    collector.increment_connections()
    collector.increment_connections()

    result = collector.get_active_connections()

    if result != 2:
        errmsg = f"Expected 2 active connections, got {result}"
        raise AssertionError(errmsg)

    return


def test_decrement_connections():
    """
        Test that decrement_connections decreases the count.
    """
    config = ServerConfig()
    collector = MetricsCollector(config=config)

    collector.increment_connections()
    collector.increment_connections()
    collector.decrement_connections()

    result = collector.get_active_connections()

    if result != 1:
        errmsg = f"Expected 1 active connection, got {result}"
        raise AssertionError(errmsg)

    return


def test_decrement_connections_does_not_go_negative():
    """
        Test that decrement_connections does not go below zero.
    """
    config = ServerConfig()
    collector = MetricsCollector(config=config)

    collector.decrement_connections()

    result = collector.get_active_connections()

    if result != 0:
        errmsg = f"Expected 0 active connections (not negative), got {result}"
        raise AssertionError(errmsg)

    return


def test_initial_active_connections_is_zero():
    """
        Test that initial active connection count is zero.
    """
    config = ServerConfig()
    collector = MetricsCollector(config=config)

    result = collector.get_active_connections()

    if result != 0:
        errmsg = f"Expected 0 initial active connections, got {result}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for MetricsCollector - Worker Status
# =============================================================================

def test_update_worker_status():
    """
        Test that worker status is tracked correctly.
    """
    config = ServerConfig()
    collector = MetricsCollector(config=config)

    collector.update_worker_status(0, WorkerState.ACTIVE)
    collector.update_worker_status(1, WorkerState.IDLE)

    statuses = collector.get_worker_statuses()

    if statuses.get(0) != "active":
        errmsg = f"Expected worker 0 state 'active', got '{statuses.get(0)}'"
        raise AssertionError(errmsg)

    if statuses.get(1) != "idle":
        errmsg = f"Expected worker 1 state 'idle', got '{statuses.get(1)}'"
        raise AssertionError(errmsg)

    return


def test_update_worker_status_overwrites():
    """
        Test that updating worker status overwrites the previous state.
    """
    config = ServerConfig()
    collector = MetricsCollector(config=config)

    collector.update_worker_status(0, WorkerState.IDLE)
    collector.update_worker_status(0, WorkerState.ACTIVE)

    statuses = collector.get_worker_statuses()

    if statuses.get(0) != "active":
        errmsg = f"Expected worker 0 state 'active' after update, got '{statuses.get(0)}'"
        raise AssertionError(errmsg)

    return


def test_remove_worker_status():
    """
        Test that remove_worker_status removes a worker from tracking.
    """
    config = ServerConfig()
    collector = MetricsCollector(config=config)

    collector.update_worker_status(0, WorkerState.ACTIVE)
    collector.remove_worker_status(0)

    statuses = collector.get_worker_statuses()

    if 0 in statuses:
        errmsg = "Expected worker 0 to be removed from statuses"
        raise AssertionError(errmsg)

    return


def test_remove_worker_status_nonexistent():
    """
        Test that removing a nonexistent worker does not raise.
    """
    config = ServerConfig()
    collector = MetricsCollector(config=config)

    # Should not raise
    collector.remove_worker_status(99)

    return


# =============================================================================
# Unit Tests for MetricsCollector - Prometheus Metrics
# =============================================================================

def test_get_prometheus_metrics_contains_total_requests():
    """
        Test that Prometheus output contains total request count.
    """
    config = ServerConfig()
    collector = MetricsCollector(config=config)

    collector.record_request("/api/users", "GET", 200, 10.0)

    output = collector.get_prometheus_metrics()

    if "webworks_requests_total 1" not in output:
        errmsg = f"Expected 'webworks_requests_total 1' in output, got:\n{output}"
        raise AssertionError(errmsg)

    return


def test_get_prometheus_metrics_contains_per_endpoint():
    """
        Test that Prometheus output contains per-endpoint request counts.
    """
    config = ServerConfig()
    collector = MetricsCollector(config=config)

    collector.record_request("/api/users", "GET", 200, 10.0)

    output = collector.get_prometheus_metrics()

    expected = 'webworks_requests_per_endpoint_total{method="GET",endpoint="/api/users"} 1'
    if expected not in output:
        errmsg = f"Expected per-endpoint metric in output, got:\n{output}"
        raise AssertionError(errmsg)

    return


def test_get_prometheus_metrics_contains_latency():
    """
        Test that Prometheus output contains latency metrics.
    """
    config = ServerConfig()
    collector = MetricsCollector(config=config)

    collector.record_request("/api/users", "GET", 200, 15.5)

    output = collector.get_prometheus_metrics()

    if "webworks_request_latency_ms_count" not in output:
        errmsg = f"Expected latency count metric in output, got:\n{output}"
        raise AssertionError(errmsg)

    if "webworks_request_latency_ms_sum" not in output:
        errmsg = f"Expected latency sum metric in output, got:\n{output}"
        raise AssertionError(errmsg)

    return


def test_get_prometheus_metrics_contains_errors():
    """
        Test that Prometheus output contains error count metrics.
    """
    config = ServerConfig()
    collector = MetricsCollector(config=config)

    collector.record_request("/api/users", "GET", 500, 10.0)

    output = collector.get_prometheus_metrics()

    expected = 'webworks_errors_total{status_code="500"} 1'
    if expected not in output:
        errmsg = f"Expected error metric in output, got:\n{output}"
        raise AssertionError(errmsg)

    return


def test_get_prometheus_metrics_contains_active_connections():
    """
        Test that Prometheus output contains active connections gauge.
    """
    config = ServerConfig()
    collector = MetricsCollector(config=config)

    collector.increment_connections()
    collector.increment_connections()

    output = collector.get_prometheus_metrics()

    if "webworks_active_connections 2" not in output:
        errmsg = f"Expected 'webworks_active_connections 2' in output, got:\n{output}"
        raise AssertionError(errmsg)

    return


def test_get_prometheus_metrics_contains_worker_status():
    """
        Test that Prometheus output contains worker status metrics.
    """
    config = ServerConfig()
    collector = MetricsCollector(config=config)

    collector.update_worker_status(0, WorkerState.ACTIVE)

    output = collector.get_prometheus_metrics()

    expected = 'webworks_worker_status{worker_id="0",state="active"} 1'
    if expected not in output:
        errmsg = f"Expected worker status metric in output, got:\n{output}"
        raise AssertionError(errmsg)

    return


def test_get_prometheus_metrics_ends_with_newline():
    """
        Test that Prometheus output ends with a newline.
    """
    config = ServerConfig()
    collector = MetricsCollector(config=config)

    output = collector.get_prometheus_metrics()

    if not output.endswith("\n"):
        errmsg = "Expected Prometheus output to end with newline"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for MetricsCollector - StatsD Export
# =============================================================================

def test_send_to_statsd_returns_false_when_not_configured():
    """
        Test that send_to_statsd returns False when no host is configured.
    """
    config = ServerConfig(statsd_host=None)
    collector = MetricsCollector(config=config)

    result = collector.send_to_statsd()

    if result is not False:
        errmsg = f"Expected False when StatsD not configured, got {result}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for MetricsCollector - Metrics Endpoint
# =============================================================================

def test_handle_metrics_request_returns_200():
    """
        Test that handle_metrics_request returns status 200.
    """
    config = ServerConfig()
    collector = MetricsCollector(config=config)

    result = collector.handle_metrics_request()

    if result["status_code"] != 200:
        errmsg = f"Expected status_code 200, got {result['status_code']}"
        raise AssertionError(errmsg)

    return


def test_handle_metrics_request_content_type():
    """
        Test that handle_metrics_request returns Prometheus content type.
    """
    config = ServerConfig()
    collector = MetricsCollector(config=config)

    result = collector.handle_metrics_request()

    expected_ct = "text/plain; version=0.0.4; charset=utf-8"
    if result["content_type"] != expected_ct:
        errmsg = f"Expected content_type '{expected_ct}', got '{result['content_type']}'"
        raise AssertionError(errmsg)

    return


def test_handle_metrics_request_body_is_string():
    """
        Test that handle_metrics_request body is a string.
    """
    config = ServerConfig()
    collector = MetricsCollector(config=config)

    result = collector.handle_metrics_request()

    if not isinstance(result["body"], str):
        errmsg = f"Expected body to be str, got {type(result['body']).__name__}"
        raise AssertionError(errmsg)

    return


def test_is_metrics_path_matches():
    """
        Test that is_metrics_path returns True for matching path.
    """
    config = ServerConfig(metrics_path="/metrics")
    collector = MetricsCollector(config=config)

    result = collector.is_metrics_path("/metrics")

    if result is not True:
        errmsg = "Expected is_metrics_path to return True for '/metrics'"
        raise AssertionError(errmsg)

    return


def test_is_metrics_path_does_not_match():
    """
        Test that is_metrics_path returns False for non-matching path.
    """
    config = ServerConfig(metrics_path="/metrics")
    collector = MetricsCollector(config=config)

    result = collector.is_metrics_path("/api/users")

    if result is not False:
        errmsg = "Expected is_metrics_path to return False for '/api/users'"
        raise AssertionError(errmsg)

    return


def test_metrics_path_property():
    """
        Test that metrics_path property returns configured path.
    """
    config = ServerConfig(metrics_path="/custom-metrics")
    collector = MetricsCollector(config=config)

    if collector.metrics_path != "/custom-metrics":
        errmsg = f"Expected '/custom-metrics', got '{collector.metrics_path}'"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for MetricsCollector - Metrics Summary
# =============================================================================

def test_get_metrics_summary_contains_all_fields():
    """
        Test that get_metrics_summary returns all expected fields.
    """
    config = ServerConfig()
    collector = MetricsCollector(config=config)

    summary = collector.get_metrics_summary()

    expected_keys = {
        "total_requests", "request_counts", "error_counts",
        "active_connections", "worker_statuses", "latency_summary"
    }
    actual_keys = set(summary.keys())

    if actual_keys != expected_keys:
        errmsg = f"Expected keys {expected_keys}, got {actual_keys}"
        raise AssertionError(errmsg)

    return


def test_get_metrics_summary_latency_stats():
    """
        Test that metrics summary includes latency statistics.
    """
    config = ServerConfig()
    collector = MetricsCollector(config=config)

    collector.record_request("/api/users", "GET", 200, 10.0)
    collector.record_request("/api/users", "GET", 200, 20.0)
    collector.record_request("/api/users", "GET", 200, 30.0)

    summary = collector.get_metrics_summary()
    latency = summary["latency_summary"].get("GET /api/users")

    if latency is None:
        errmsg = "Expected latency summary for 'GET /api/users'"
        raise AssertionError(errmsg)

    if latency["count"] != 3:
        errmsg = f"Expected latency count 3, got {latency['count']}"
        raise AssertionError(errmsg)

    if abs(latency["min"] - 10.0) > 0.001:
        errmsg = f"Expected latency min 10.0, got {latency['min']}"
        raise AssertionError(errmsg)

    if abs(latency["max"] - 30.0) > 0.001:
        errmsg = f"Expected latency max 30.0, got {latency['max']}"
        raise AssertionError(errmsg)

    if abs(latency["avg"] - 20.0) > 0.001:
        errmsg = f"Expected latency avg 20.0, got {latency['avg']}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for MetricsCollector - Reset
# =============================================================================

def test_reset_clears_all_metrics():
    """
        Test that reset clears all collected metrics.
    """
    config = ServerConfig()
    collector = MetricsCollector(config=config)

    collector.record_request("/api/users", "GET", 200, 10.0)
    collector.record_request("/api/users", "GET", 500, 10.0)
    collector.increment_connections()
    collector.update_worker_status(0, WorkerState.ACTIVE)

    collector.reset()

    if collector.get_request_count() != 0:
        errmsg = "Expected 0 total requests after reset"
        raise AssertionError(errmsg)

    if collector.get_error_count() != 0:
        errmsg = "Expected 0 errors after reset"
        raise AssertionError(errmsg)

    if collector.get_active_connections() != 0:
        errmsg = "Expected 0 active connections after reset"
        raise AssertionError(errmsg)

    if len(collector.get_worker_statuses()) != 0:
        errmsg = "Expected empty worker statuses after reset"
        raise AssertionError(errmsg)

    return
