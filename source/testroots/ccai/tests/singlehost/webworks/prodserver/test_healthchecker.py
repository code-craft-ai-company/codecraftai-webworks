"""
    Tests for the production server HealthChecker class.

    This module contains unit tests for health check functionality
    including liveness checks, readiness checks, health check endpoint
    handling, configurable health check paths, and status reporting.
"""

from ccai.webworks.prodserver.healthchecker import HealthChecker
from ccai.webworks.prodserver.serverconfig import ServerConfig, ServerState


# =============================================================================
# Unit Tests for HealthChecker - Liveness Checks
# =============================================================================

def test_check_liveness_returns_true():
    """
        Test that check_liveness always returns True when the process is running.
    """
    config = ServerConfig()
    checker = HealthChecker(config=config)

    result = checker.check_liveness()

    if result is not True:
        errmsg = f"Expected liveness check to return True, got {result}"
        raise AssertionError(errmsg)

    return


def test_check_liveness_returns_true_during_shutdown():
    """
        Test that check_liveness returns True even during shutdown.
    """
    config = ServerConfig()
    checker = HealthChecker(config=config)
    checker.set_server_state(ServerState.SHUTTING_DOWN)

    result = checker.check_liveness()

    if result is not True:
        errmsg = f"Expected liveness check to return True during shutdown, got {result}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for HealthChecker - Readiness Checks
# =============================================================================

def test_check_readiness_returns_true_when_running():
    """
        Test that check_readiness returns True when server is RUNNING.
    """
    config = ServerConfig()
    checker = HealthChecker(config=config)
    checker.set_server_state(ServerState.RUNNING)

    result = checker.check_readiness()

    if result is not True:
        errmsg = f"Expected readiness check to return True when RUNNING, got {result}"
        raise AssertionError(errmsg)

    return


def test_check_readiness_returns_false_when_shutting_down():
    """
        Test that check_readiness returns False when server is SHUTTING_DOWN.
    """
    config = ServerConfig()
    checker = HealthChecker(config=config)
    checker.set_server_state(ServerState.SHUTTING_DOWN)

    result = checker.check_readiness()

    if result is not False:
        errmsg = f"Expected readiness check to return False when SHUTTING_DOWN, got {result}"
        raise AssertionError(errmsg)

    return


def test_check_readiness_returns_false_when_starting():
    """
        Test that check_readiness returns False when server is STARTING.
    """
    config = ServerConfig()
    checker = HealthChecker(config=config)
    checker.set_server_state(ServerState.STARTING)

    result = checker.check_readiness()

    if result is not False:
        errmsg = f"Expected readiness check to return False when STARTING, got {result}"
        raise AssertionError(errmsg)

    return


def test_check_readiness_returns_false_when_stopped():
    """
        Test that check_readiness returns False when server is STOPPED.
    """
    config = ServerConfig()
    checker = HealthChecker(config=config)
    checker.set_server_state(ServerState.STOPPED)

    result = checker.check_readiness()

    if result is not False:
        errmsg = f"Expected readiness check to return False when STOPPED, got {result}"
        raise AssertionError(errmsg)

    return


def test_check_readiness_returns_true_when_no_state_set():
    """
        Test that check_readiness returns True when no server state is set.
    """
    config = ServerConfig()
    checker = HealthChecker(config=config)

    result = checker.check_readiness()

    if result is not True:
        errmsg = f"Expected readiness check to return True with no state, got {result}"
        raise AssertionError(errmsg)

    return


def test_check_readiness_with_passing_custom_check():
    """
        Test that check_readiness returns True when custom checks pass.
    """
    config = ServerConfig()
    checker = HealthChecker(config=config)
    checker.set_server_state(ServerState.RUNNING)
    checker.register_check(lambda: True)

    result = checker.check_readiness()

    if result is not True:
        errmsg = f"Expected readiness to return True with passing custom check, got {result}"
        raise AssertionError(errmsg)

    return


def test_check_readiness_with_failing_custom_check():
    """
        Test that check_readiness returns False when a custom check fails.
    """
    config = ServerConfig()
    checker = HealthChecker(config=config)
    checker.set_server_state(ServerState.RUNNING)
    checker.register_check(lambda: False)

    result = checker.check_readiness()

    if result is not False:
        errmsg = f"Expected readiness to return False with failing custom check, got {result}"
        raise AssertionError(errmsg)

    return


def test_check_readiness_with_exception_in_custom_check():
    """
        Test that check_readiness returns False when a custom check raises.
    """
    config = ServerConfig()
    checker = HealthChecker(config=config)
    checker.set_server_state(ServerState.RUNNING)

    def bad_check():
        raise RuntimeError("check failed")

    checker.register_check(bad_check)

    result = checker.check_readiness()

    if result is not False:
        errmsg = f"Expected readiness to return False with exception in check, got {result}"
        raise AssertionError(errmsg)

    return


def test_check_readiness_with_multiple_custom_checks():
    """
        Test that all custom checks must pass for readiness.
    """
    config = ServerConfig()
    checker = HealthChecker(config=config)
    checker.set_server_state(ServerState.RUNNING)
    checker.register_check(lambda: True)
    checker.register_check(lambda: True)
    checker.register_check(lambda: False)

    result = checker.check_readiness()

    if result is not False:
        errmsg = f"Expected readiness to return False when one check fails, got {result}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for HealthChecker - Health Check Endpoint
# =============================================================================

def test_handle_health_request_returns_200_when_healthy():
    """
        Test that handle_health_request returns 200 when server is healthy.
    """
    config = ServerConfig()
    checker = HealthChecker(config=config)
    checker.set_server_state(ServerState.RUNNING)

    result = checker.handle_health_request()

    if result["status_code"] != 200:
        errmsg = f"Expected status_code 200, got {result['status_code']}"
        raise AssertionError(errmsg)

    return


def test_handle_health_request_returns_503_when_unhealthy():
    """
        Test that handle_health_request returns 503 when server is unhealthy.
    """
    config = ServerConfig()
    checker = HealthChecker(config=config)
    checker.set_server_state(ServerState.SHUTTING_DOWN)

    result = checker.handle_health_request()

    if result["status_code"] != 503:
        errmsg = f"Expected status_code 503, got {result['status_code']}"
        raise AssertionError(errmsg)

    return


def test_handle_health_request_returns_503_when_stopped():
    """
        Test that handle_health_request returns 503 when server is stopped.
    """
    config = ServerConfig()
    checker = HealthChecker(config=config)
    checker.set_server_state(ServerState.STOPPED)

    result = checker.handle_health_request()

    if result["status_code"] != 503:
        errmsg = f"Expected status_code 503, got {result['status_code']}"
        raise AssertionError(errmsg)

    return


def test_handle_health_request_body_contains_status():
    """
        Test that the health response body contains a status field.
    """
    config = ServerConfig()
    checker = HealthChecker(config=config)
    checker.set_server_state(ServerState.RUNNING)

    result = checker.handle_health_request()
    body = result["body"]

    if "status" not in body:
        errmsg = "Expected 'status' field in response body"
        raise AssertionError(errmsg)

    if body["status"] != "healthy":
        errmsg = f"Expected status 'healthy', got '{body['status']}'"
        raise AssertionError(errmsg)

    return


def test_handle_health_request_body_contains_unhealthy_status():
    """
        Test that the health response body contains unhealthy status when shutting down.
    """
    config = ServerConfig()
    checker = HealthChecker(config=config)
    checker.set_server_state(ServerState.SHUTTING_DOWN)

    result = checker.handle_health_request()
    body = result["body"]

    if body["status"] != "unhealthy":
        errmsg = f"Expected status 'unhealthy', got '{body['status']}'"
        raise AssertionError(errmsg)

    return


def test_handle_health_request_body_contains_json_fields():
    """
        Test that the health response body contains all expected JSON fields.
    """
    config = ServerConfig()
    checker = HealthChecker(config=config)
    checker.set_server_state(ServerState.RUNNING)

    result = checker.handle_health_request()
    body = result["body"]

    expected_keys = {"status", "uptime", "workers", "checks"}
    actual_keys = set(body.keys())

    if actual_keys != expected_keys:
        errmsg = f"Expected keys {expected_keys}, got {actual_keys}"
        raise AssertionError(errmsg)

    return


def test_handle_health_request_body_workers_info():
    """
        Test that the health response body includes worker information.
    """
    config = ServerConfig()
    checker = HealthChecker(config=config)
    checker.set_server_state(ServerState.RUNNING)
    checker.set_worker_info(
        worker_count=4,
        worker_statuses={0: "active", 1: "active", 2: "idle", 3: "active"}
    )

    result = checker.handle_health_request()
    body = result["body"]

    if body["workers"]["count"] != 4:
        errmsg = f"Expected worker count 4, got {body['workers']['count']}"
        raise AssertionError(errmsg)

    if len(body["workers"]["statuses"]) != 4:
        errmsg = f"Expected 4 worker statuses, got {len(body['workers']['statuses'])}"
        raise AssertionError(errmsg)

    return


def test_handle_health_request_body_checks_info():
    """
        Test that the health response body includes check results.
    """
    config = ServerConfig()
    checker = HealthChecker(config=config)
    checker.set_server_state(ServerState.RUNNING)

    result = checker.handle_health_request()
    body = result["body"]

    if body["checks"]["liveness"] is not True:
        errmsg = f"Expected liveness True, got {body['checks']['liveness']}"
        raise AssertionError(errmsg)

    if body["checks"]["readiness"] is not True:
        errmsg = f"Expected readiness True, got {body['checks']['readiness']}"
        raise AssertionError(errmsg)

    return


def test_handle_health_request_content_type():
    """
        Test that the health response specifies JSON content type.
    """
    config = ServerConfig()
    checker = HealthChecker(config=config)
    checker.set_server_state(ServerState.RUNNING)

    result = checker.handle_health_request()

    if result["content_type"] != "application/json":
        errmsg = f"Expected content_type 'application/json', got '{result['content_type']}'"
        raise AssertionError(errmsg)

    return


def test_handle_health_request_uptime_is_positive():
    """
        Test that the health response uptime is a positive number.
    """
    config = ServerConfig()
    checker = HealthChecker(config=config)
    checker.set_server_state(ServerState.RUNNING)

    result = checker.handle_health_request()
    body = result["body"]

    if body["uptime"] < 0:
        errmsg = f"Expected positive uptime, got {body['uptime']}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for HealthChecker - Configurable Health Check Path
# =============================================================================

def test_health_check_path_default():
    """
        Test that the default health check path is /health.
    """
    config = ServerConfig()
    checker = HealthChecker(config=config)

    if checker.health_check_path != "/health":
        errmsg = f"Expected '/health', got '{checker.health_check_path}'"
        raise AssertionError(errmsg)

    return


def test_health_check_path_custom():
    """
        Test that a custom health check path is used.
    """
    config = ServerConfig(health_check_path="/status")
    checker = HealthChecker(config=config)

    if checker.health_check_path != "/status":
        errmsg = f"Expected '/status', got '{checker.health_check_path}'"
        raise AssertionError(errmsg)

    return


def test_is_health_check_path_matches():
    """
        Test that is_health_check_path returns True for matching path.
    """
    config = ServerConfig(health_check_path="/health")
    checker = HealthChecker(config=config)

    result = checker.is_health_check_path("/health")

    if result is not True:
        errmsg = "Expected is_health_check_path to return True for '/health'"
        raise AssertionError(errmsg)

    return


def test_is_health_check_path_does_not_match():
    """
        Test that is_health_check_path returns False for non-matching path.
    """
    config = ServerConfig(health_check_path="/health")
    checker = HealthChecker(config=config)

    result = checker.is_health_check_path("/api/users")

    if result is not False:
        errmsg = "Expected is_health_check_path to return False for '/api/users'"
        raise AssertionError(errmsg)

    return


def test_is_health_check_path_custom_path_matches():
    """
        Test that is_health_check_path matches a custom configured path.
    """
    config = ServerConfig(health_check_path="/ready")
    checker = HealthChecker(config=config)

    result = checker.is_health_check_path("/ready")

    if result is not True:
        errmsg = "Expected is_health_check_path to return True for '/ready'"
        raise AssertionError(errmsg)

    return


def test_is_health_check_path_does_not_match_partial():
    """
        Test that is_health_check_path does not match partial paths.
    """
    config = ServerConfig(health_check_path="/health")
    checker = HealthChecker(config=config)

    result = checker.is_health_check_path("/health/detailed")

    if result is not False:
        errmsg = "Expected is_health_check_path to return False for '/health/detailed'"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for HealthChecker - is_healthy
# =============================================================================

def test_is_healthy_returns_true_when_running():
    """
        Test that is_healthy returns True when server is running.
    """
    config = ServerConfig()
    checker = HealthChecker(config=config)
    checker.set_server_state(ServerState.RUNNING)

    result = checker.is_healthy()

    if result is not True:
        errmsg = f"Expected is_healthy True when RUNNING, got {result}"
        raise AssertionError(errmsg)

    return


def test_is_healthy_returns_false_when_shutting_down():
    """
        Test that is_healthy returns False when server is shutting down.
    """
    config = ServerConfig()
    checker = HealthChecker(config=config)
    checker.set_server_state(ServerState.SHUTTING_DOWN)

    result = checker.is_healthy()

    if result is not False:
        errmsg = f"Expected is_healthy False when SHUTTING_DOWN, got {result}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for HealthChecker - get_status
# =============================================================================

def test_get_status_returns_expected_fields():
    """
        Test that get_status returns all expected fields.
    """
    config = ServerConfig()
    checker = HealthChecker(config=config)
    checker.set_server_state(ServerState.RUNNING)

    status = checker.get_status()

    expected_keys = {"status", "uptime", "workers", "checks"}
    actual_keys = set(status.keys())

    if actual_keys != expected_keys:
        errmsg = f"Expected keys {expected_keys}, got {actual_keys}"
        raise AssertionError(errmsg)

    return


def test_get_status_healthy_when_running():
    """
        Test that get_status reports healthy when server is running.
    """
    config = ServerConfig()
    checker = HealthChecker(config=config)
    checker.set_server_state(ServerState.RUNNING)

    status = checker.get_status()

    if status["status"] != "healthy":
        errmsg = f"Expected status 'healthy', got '{status['status']}'"
        raise AssertionError(errmsg)

    return


def test_get_status_unhealthy_when_shutting_down():
    """
        Test that get_status reports unhealthy when server is shutting down.
    """
    config = ServerConfig()
    checker = HealthChecker(config=config)
    checker.set_server_state(ServerState.SHUTTING_DOWN)

    status = checker.get_status()

    if status["status"] != "unhealthy":
        errmsg = f"Expected status 'unhealthy', got '{status['status']}'"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for HealthChecker - register_check
# =============================================================================

def test_register_check_adds_check():
    """
        Test that register_check adds a custom check.
    """
    config = ServerConfig()
    checker = HealthChecker(config=config)
    checker.set_server_state(ServerState.RUNNING)

    checker.register_check(lambda: True)

    result = checker.check_readiness()

    if result is not True:
        errmsg = f"Expected readiness True after registering passing check, got {result}"
        raise AssertionError(errmsg)

    return


def test_register_multiple_checks():
    """
        Test that multiple custom checks can be registered.
    """
    config = ServerConfig()
    checker = HealthChecker(config=config)
    checker.set_server_state(ServerState.RUNNING)

    checker.register_check(lambda: True)
    checker.register_check(lambda: True)

    result = checker.check_readiness()

    if result is not True:
        errmsg = f"Expected readiness True with all passing checks, got {result}"
        raise AssertionError(errmsg)

    return
