"""
    Property-Based Tests for Health Check Consistency (Property 4).

    Property 4: Health Check Consistency
    For any server state, the health check endpoint SHALL return HTTP 200
    when the server is healthy and running, and HTTP 503 when the server
    is unhealthy or shutting down, with response body containing valid
    JSON status information.

    Validates: Requirements 5.2, 5.3, 5.4, 5.7, 5.8
"""

import random

from automojo.webworks.prodserver.healthchecker import HealthChecker
from automojo.webworks.prodserver.serverconfig import ServerConfig, ServerState


# =============================================================================
# Helpers
# =============================================================================

# States where the server is considered healthy
HEALTHY_STATES = [ServerState.RUNNING]

# States where the server is considered unhealthy
UNHEALTHY_STATES = [
    ServerState.STOPPED,
    ServerState.STARTING,
    ServerState.SHUTTING_DOWN,
    ServerState.RELOADING,
]

ALL_STATES = HEALTHY_STATES + UNHEALTHY_STATES

VALID_HEALTH_CHECK_PATHS = [
    "/health",
    "/status",
    "/ready",
    "/healthz",
    "/livez",
    "/readyz",
    "/_health",
    "/api/health",
]

NON_HEALTH_PATHS = [
    "/",
    "/api/users",
    "/index.html",
    "/static/style.css",
    "/login",
]


# =============================================================================
# Random Generators
# =============================================================================

def generate_server_state() -> ServerState:
    """
        Generate a random server state.
    """
    return random.choice(ALL_STATES)


def generate_healthy_state() -> ServerState:
    """
        Generate a random healthy server state.
    """
    return random.choice(HEALTHY_STATES)


def generate_unhealthy_state() -> ServerState:
    """
        Generate a random unhealthy server state.
    """
    return random.choice(UNHEALTHY_STATES)


def generate_health_check_path() -> str:
    """
        Generate a random health check path.
    """
    return random.choice(VALID_HEALTH_CHECK_PATHS)


def generate_non_health_path() -> str:
    """
        Generate a random non-health-check path.
    """
    return random.choice(NON_HEALTH_PATHS)


def generate_worker_count() -> int:
    """
        Generate a random worker count between 1 and 16.
    """
    return random.randint(1, 16)


def generate_worker_statuses(count: int) -> dict:
    """
        Generate random worker statuses for a given count.
    """
    states = ["active", "idle", "shutting_down"]
    rtnval = {}
    for i in range(count):
        rtnval[i] = random.choice(states)
    return rtnval


# =============================================================================
# Property-Based Tests
# =============================================================================

# Feature: production-server, Property 4: Health Check Consistency
# *For any* server state, the health check endpoint SHALL return HTTP 200
# when the server is healthy and running, and HTTP 503 when the server
# is unhealthy or shutting down, with response body containing valid
# JSON status information.
# **Validates: Requirements 5.2, 5.3, 5.4, 5.7, 5.8**


def test_property_4_healthy_state_returns_200():
    """
        Property 4: Healthy State Returns 200

        For any healthy server state, the health check endpoint SHALL
        return HTTP 200.

        **Validates: Requirement 5.2**
    """
    for iteration in range(100):
        state = generate_healthy_state()
        config = ServerConfig()
        checker = HealthChecker(config=config)
        checker.set_server_state(state)

        result = checker.handle_health_request()

        if result["status_code"] != 200:
            errmsg = (
                f"Iteration {iteration}: expected status_code 200 for "
                f"state {state.value}, got {result['status_code']}"
            )
            raise AssertionError(errmsg)

    return


def test_property_4_unhealthy_state_returns_503():
    """
        Property 4: Unhealthy State Returns 503

        For any unhealthy server state, the health check endpoint SHALL
        return HTTP 503.

        **Validates: Requirement 5.3**
    """
    for iteration in range(100):
        state = generate_unhealthy_state()
        config = ServerConfig()
        checker = HealthChecker(config=config)
        checker.set_server_state(state)

        result = checker.handle_health_request()

        if result["status_code"] != 503:
            errmsg = (
                f"Iteration {iteration}: expected status_code 503 for "
                f"state {state.value}, got {result['status_code']}"
            )
            raise AssertionError(errmsg)

    return


def test_property_4_response_body_contains_valid_json_fields():
    """
        Property 4: Response Body Contains Valid JSON Fields

        For any server state, the health check response body SHALL
        contain status, uptime, workers, and checks fields.

        **Validates: Requirement 5.4**
    """
    expected_keys = {"status", "uptime", "workers", "checks"}

    for iteration in range(100):
        state = generate_server_state()
        worker_count = generate_worker_count()
        worker_statuses = generate_worker_statuses(worker_count)

        config = ServerConfig()
        checker = HealthChecker(config=config)
        checker.set_server_state(state)
        checker.set_worker_info(
            worker_count=worker_count,
            worker_statuses=worker_statuses
        )

        result = checker.handle_health_request()
        body = result["body"]
        actual_keys = set(body.keys())

        if actual_keys != expected_keys:
            errmsg = (
                f"Iteration {iteration}: expected keys {expected_keys}, "
                f"got {actual_keys} for state {state.value}"
            )
            raise AssertionError(errmsg)

        if not isinstance(body["uptime"], (int, float)):
            errmsg = (
                f"Iteration {iteration}: expected uptime to be numeric, "
                f"got {type(body['uptime']).__name__}"
            )
            raise AssertionError(errmsg)

        if body["status"] not in ("healthy", "unhealthy"):
            errmsg = (
                f"Iteration {iteration}: expected status 'healthy' or "
                f"'unhealthy', got '{body['status']}'"
            )
            raise AssertionError(errmsg)

    return


def test_property_4_configurable_health_check_path():
    """
        Property 4: Configurable Health Check Path

        For any configured health check path, the health checker SHALL
        correctly identify requests to that path and bypass normal routing.

        **Validates: Requirement 5.7**
    """
    for iteration in range(100):
        health_path = generate_health_check_path()
        non_health_path = generate_non_health_path()

        config = ServerConfig(health_check_path=health_path)
        checker = HealthChecker(config=config)

        if not checker.is_health_check_path(health_path):
            errmsg = (
                f"Iteration {iteration}: expected is_health_check_path "
                f"to return True for '{health_path}'"
            )
            raise AssertionError(errmsg)

        if checker.is_health_check_path(non_health_path):
            errmsg = (
                f"Iteration {iteration}: expected is_health_check_path "
                f"to return False for '{non_health_path}'"
            )
            raise AssertionError(errmsg)

    return


def test_property_4_health_check_bypasses_routing():
    """
        Property 4: Health Check Bypasses Normal Routing

        For any configured health check path, the health check endpoint
        SHALL be accessible regardless of server state and return a
        valid response.

        **Validates: Requirement 5.8**
    """
    for iteration in range(100):
        state = generate_server_state()
        health_path = generate_health_check_path()

        config = ServerConfig(health_check_path=health_path)
        checker = HealthChecker(config=config)
        checker.set_server_state(state)

        is_health = checker.is_health_check_path(health_path)

        if is_health is not True:
            errmsg = (
                f"Iteration {iteration}: health check path '{health_path}' "
                f"not recognized in state {state.value}"
            )
            raise AssertionError(errmsg)

        result = checker.handle_health_request()

        if result["status_code"] not in (200, 503):
            errmsg = (
                f"Iteration {iteration}: expected status_code 200 or 503, "
                f"got {result['status_code']} for state {state.value}"
            )
            raise AssertionError(errmsg)

        if result["content_type"] != "application/json":
            errmsg = (
                f"Iteration {iteration}: expected content_type "
                f"'application/json', got '{result['content_type']}'"
            )
            raise AssertionError(errmsg)

    return


def test_property_4_status_code_matches_health():
    """
        Property 4: Status Code Matches Health State

        For any server state, the HTTP status code SHALL be 200 if and
        only if the server is healthy, and 503 otherwise.

        **Validates: Requirements 5.2, 5.3**
    """
    for iteration in range(100):
        state = generate_server_state()
        config = ServerConfig()
        checker = HealthChecker(config=config)
        checker.set_server_state(state)

        result = checker.handle_health_request()
        is_healthy = checker.is_healthy()

        if is_healthy and result["status_code"] != 200:
            errmsg = (
                f"Iteration {iteration}: server is healthy in state "
                f"{state.value} but status_code is {result['status_code']}"
            )
            raise AssertionError(errmsg)

        if not is_healthy and result["status_code"] != 503:
            errmsg = (
                f"Iteration {iteration}: server is unhealthy in state "
                f"{state.value} but status_code is {result['status_code']}"
            )
            raise AssertionError(errmsg)

    return
