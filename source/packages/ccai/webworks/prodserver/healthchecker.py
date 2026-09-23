"""
    Health check module for the production server.

    This module provides the HealthChecker class that implements liveness
    and readiness checks, handles health check HTTP requests, and supports
    configurable health check paths that bypass normal application routing.
"""

import logging
import time
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ccai.webworks.prodserver.serverconfig import ServerConfig, ServerState


# Default logger for health checker
_logger = logging.getLogger("webworks.prodserver.healthchecker")


class HealthChecker:
    """
        Provides health check endpoints for load balancers and orchestrators.

        Implements liveness checks that verify the process is running and
        readiness checks that verify the application can handle requests.
        Supports configurable health check paths and custom health checks.
    """

    def __init__(self, config: "ServerConfig"):
        """
            Construct a HealthChecker.

            :param config: Server configuration containing health check settings.
        """
        self._config = config
        self._custom_checks: List[Callable[[], bool]] = []
        self._server_state: Optional["ServerState"] = None
        self._start_time: float = time.time()
        self._worker_count: int = 0
        self._worker_statuses: Dict[int, str] = {}

        return

    @property
    def health_check_path(self) -> str:
        """
            Get the configured health check path.

            :returns: The health check endpoint path.
        """
        return self._config.health_check_path

    def set_server_state(self, state: "ServerState") -> None:
        """
            Update the current server state.

            :param state: The current server lifecycle state.
        """
        self._server_state = state

        return

    def set_worker_info(self, worker_count: int, worker_statuses: Dict[int, str]) -> None:
        """
            Update worker information for health status reporting.

            :param worker_count: The number of active workers.
            :param worker_statuses: Dictionary mapping worker IDs to state strings.
        """
        self._worker_count = worker_count
        self._worker_statuses = dict(worker_statuses)

        return

    def register_check(self, check: Callable[[], bool]) -> None:
        """
            Register a custom health check.

            Custom checks are evaluated during readiness checks. Each
            check is a callable that returns True if healthy and False
            if unhealthy.

            :param check: A callable that returns a boolean health status.
        """
        self._custom_checks.append(check)

        return

    def check_liveness(self) -> bool:
        """
            Check if the server process is alive.

            The liveness check verifies that the process is running.
            This always returns True as long as the process is executing.

            :returns: True if the process is running.
        """
        return True

    def check_readiness(self) -> bool:
        """
            Check if the server is ready to handle requests.

            The readiness check verifies that the server is in the
            RUNNING state and all custom health checks pass. Returns
            False if the server is shutting down or any custom check
            fails.

            :returns: True if the server is ready to handle requests.
        """
        from ccai.webworks.prodserver.serverconfig import ServerState

        if self._server_state is not None:
            if self._server_state != ServerState.RUNNING:
                return False

        for check in self._custom_checks:
            try:
                if not check():
                    return False
            except Exception:
                _logger.exception("Custom health check failed with exception")
                return False

        return True

    def is_healthy(self) -> bool:
        """
            Determine overall health status.

            The server is considered healthy when both the liveness
            and readiness checks pass.

            :returns: True if the server is healthy.
        """
        rtnval = self.check_liveness() and self.check_readiness()

        return rtnval

    def get_status(self) -> Dict[str, Any]:
        """
            Get detailed server status information.

            :returns: Dictionary with status information including
                      status, uptime, workers, and checks.
        """
        healthy = self.is_healthy()
        uptime = time.time() - self._start_time

        rtnval: Dict[str, Any] = {
            "status": "healthy" if healthy else "unhealthy",
            "uptime": round(uptime, 2),
            "workers": {
                "count": self._worker_count,
                "statuses": dict(self._worker_statuses),
            },
            "checks": {
                "liveness": self.check_liveness(),
                "readiness": self.check_readiness(),
            },
        }

        return rtnval

    def is_health_check_path(self, request_path: str) -> bool:
        """
            Check if a request path matches the health check endpoint.

            This is used to bypass normal application routing for health
            check requests.

            :param request_path: The request path to check.

            :returns: True if the path matches the health check endpoint.
        """
        rtnval = request_path == self._config.health_check_path

        return rtnval

    def handle_health_request(self) -> Dict[str, Any]:
        """
            Handle a health check request.

            Returns a dictionary containing the HTTP status code and
            JSON response body. Returns status 200 when healthy and
            503 when unhealthy or shutting down.

            :returns: Dictionary with 'status_code' and 'body' keys.
        """
        healthy = self.is_healthy()
        status_info = self.get_status()

        if healthy:
            status_code = 200
        else:
            status_code = 503

        rtnval = {
            "status_code": status_code,
            "body": status_info,
            "content_type": "application/json",
        }

        return rtnval
