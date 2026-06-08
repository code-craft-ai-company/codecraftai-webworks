"""
    Resource limits module for the production server.

    This module provides the ResourceLimiter class for enforcing resource
    limits on worker processes including memory limits, request body size
    limits, header field size limits, and resource usage warnings. It also
    manages worker temporary directories.
"""

import logging
import os
import tempfile
from typing import TYPE_CHECKING, Dict, Optional

if TYPE_CHECKING:
    from ccai.webworks.prodserver.serverconfig import ServerConfig


# Default logger for resource limiter
_logger = logging.getLogger("webworks.prodserver.resourcelimiter")

# Warning threshold as a fraction of the limit (80%)
RESOURCE_WARNING_THRESHOLD = 0.8


class RequestBodyTooLargeError(Exception):
    """
        Raised when a request body exceeds the configured limit.

        Corresponds to HTTP 413 Payload Too Large.
    """

    def __init__(self, body_size: int, limit: int):
        """
            Construct a RequestBodyTooLargeError.

            :param body_size: The actual body size in bytes.
            :param limit: The configured limit in bytes.
        """
        self._body_size = body_size
        self._limit = limit
        message = (
            f"Request body too large: {body_size} bytes "
            f"exceeds limit of {limit} bytes"
        )
        super().__init__(message)
        return

    @property
    def body_size(self) -> int:
        """
            Get the actual body size.

            :returns: The body size in bytes.
        """
        return self._body_size

    @property
    def limit(self) -> int:
        """
            Get the configured limit.

            :returns: The limit in bytes.
        """
        return self._limit

    @property
    def status_code(self) -> int:
        """
            Get the HTTP status code for this error.

            :returns: 413 (Payload Too Large).
        """
        return 413



class HeaderFieldTooLargeError(Exception):
    """
        Raised when a request header field value exceeds the configured limit.

        Corresponds to HTTP 431 Request Header Fields Too Large.
    """

    def __init__(self, field_size: int, limit: int):
        """
            Construct a HeaderFieldTooLargeError.

            :param field_size: The actual field size in bytes.
            :param limit: The configured limit in bytes.
        """
        self._field_size = field_size
        self._limit = limit
        message = (
            f"Request header field too large: {field_size} bytes "
            f"exceeds limit of {limit} bytes"
        )
        super().__init__(message)
        return

    @property
    def field_size(self) -> int:
        """
            Get the actual field size.

            :returns: The field size in bytes.
        """
        return self._field_size

    @property
    def limit(self) -> int:
        """
            Get the configured limit.

            :returns: The limit in bytes.
        """
        return self._limit

    @property
    def status_code(self) -> int:
        """
            Get the HTTP status code for this error.

            :returns: 431 (Request Header Fields Too Large).
        """
        return 431


class ResourceLimiter:
    """
        Enforces resource limits on worker processes.

        Monitors and enforces memory limits, request body size limits,
        header field size limits, and provides resource usage warnings
        when approaching configured thresholds. Also manages worker
        temporary directories.
    """

    def __init__(self, config: "ServerConfig"):
        """
            Construct a ResourceLimiter.

            :param config: Server configuration containing limit settings.
        """
        self._config = config
        self._worker_memory: Dict[int, int] = {}
        self._worker_tmp_dir: Optional[str] = None
        self._warnings: list = []

        return

    @property
    def memory_limit(self) -> Optional[int]:
        """
            Get the configured memory limit in bytes.

            :returns: The memory limit, or None if unlimited.
        """
        return self._config.limit_memory

    @property
    def request_body_limit(self) -> int:
        """
            Get the configured request body size limit in bytes.

            A value of 0 means unlimited.

            :returns: The request body limit.
        """
        return self._config.limit_request_body

    @property
    def request_field_size_limit(self) -> int:
        """
            Get the configured request header field size limit in bytes.

            :returns: The header field size limit.
        """
        return self._config.limit_request_field_size

    @property
    def worker_tmp_dir(self) -> Optional[str]:
        """
            Get the worker temporary directory path.

            :returns: The temp directory path, or None if not configured.
        """
        return self._worker_tmp_dir

    def update_worker_memory(self, worker_id: int, memory_bytes: int) -> None:
        """
            Update the tracked memory usage for a worker.

            :param worker_id: The worker identifier.
            :param memory_bytes: Current memory usage in bytes.
        """
        self._worker_memory[worker_id] = memory_bytes

        return

    def get_worker_memory(self, worker_id: int) -> int:
        """
            Get the tracked memory usage for a worker.

            :param worker_id: The worker identifier.

            :returns: Memory usage in bytes, or 0 if not tracked.
        """
        rtnval = self._worker_memory.get(worker_id, 0)

        return rtnval

    def check_worker_memory(self, worker_id: int) -> bool:
        """
            Check if a worker exceeds the configured memory limit.

            When a memory limit is configured and the worker's tracked
            memory usage exceeds it, this method returns True indicating
            the worker should be restarted.

            :param worker_id: The worker identifier.

            :returns: True if the worker exceeds the memory limit.
        """
        limit = self._config.limit_memory

        if limit is None or limit <= 0:
            return False

        current = self._worker_memory.get(worker_id, 0)

        if current > limit:
            _logger.warning(
                "Worker %d memory usage %d bytes exceeds limit of %d bytes",
                worker_id,
                current,
                limit,
            )
            return True

        return False

    def get_workers_exceeding_memory(self) -> list:
        """
            Get a list of worker IDs that exceed the memory limit.

            :returns: List of worker IDs exceeding the memory limit.
        """
        limit = self._config.limit_memory

        if limit is None or limit <= 0:
            return []

        rtnval = []
        for worker_id, memory in self._worker_memory.items():
            if memory > limit:
                rtnval.append(worker_id)

        return rtnval

    def remove_worker(self, worker_id: int) -> None:
        """
            Remove a worker from memory tracking.

            :param worker_id: The worker identifier to remove.
        """
        self._worker_memory.pop(worker_id, None)

        return

    def validate_request_body(self, body_size: int) -> None:
        """
            Validate that a request body does not exceed the configured limit.

            A limit of 0 means unlimited and no validation is performed.

            :param body_size: The request body size in bytes.

            :raises: RequestBodyTooLargeError if the body exceeds the limit.
        """
        limit = self._config.limit_request_body

        if limit <= 0:
            return

        if body_size > limit:
            _logger.warning(
                "Request body size %d bytes exceeds limit of %d bytes",
                body_size,
                limit,
            )
            raise RequestBodyTooLargeError(body_size=body_size, limit=limit)

        return

    def validate_header_field_size(self, field_value: str) -> None:
        """
            Validate that a request header field value does not exceed
            the configured limit.

            A limit of 0 means unlimited and no validation is performed.

            :param field_value: The header field value string.

            :raises: HeaderFieldTooLargeError if the field exceeds the limit.
        """
        limit = self._config.limit_request_field_size

        if limit <= 0:
            return

        field_size = len(field_value)

        if field_size > limit:
            _logger.warning(
                "Request header field size %d bytes exceeds limit of %d bytes",
                field_size,
                limit,
            )
            raise HeaderFieldTooLargeError(field_size=field_size, limit=limit)

        return

    def check_resource_warnings(self) -> list:
        """
            Check all resource usage and return warnings for resources
            approaching their limits.

            A warning is generated when usage exceeds the warning threshold
            (80% of the configured limit).

            :returns: List of warning message strings.
        """
        warnings = []

        # Check memory warnings for each tracked worker
        limit = self._config.limit_memory
        if limit is not None and limit > 0:
            threshold = int(limit * RESOURCE_WARNING_THRESHOLD)
            for worker_id, memory in self._worker_memory.items():
                if memory > threshold and memory <= limit:
                    msg = (
                        f"Worker {worker_id} memory usage {memory} bytes "
                        f"approaching limit of {limit} bytes "
                        f"(threshold: {threshold} bytes)"
                    )
                    _logger.warning(msg)
                    warnings.append(msg)

        self._warnings = warnings

        return warnings

    def get_last_warnings(self) -> list:
        """
            Get the warnings from the last check_resource_warnings call.

            :returns: List of warning message strings.
        """
        return list(self._warnings)

    def setup_worker_tmp_dir(self) -> Optional[str]:
        """
            Set up the worker temporary directory.

            Creates a temporary directory for worker use. If the server
            configuration does not specify a worker temp directory, a
            system default temporary directory is created.

            :returns: The path to the temporary directory, or None on failure.
        """
        try:
            tmp_dir = tempfile.mkdtemp(prefix="webworks_worker_")
            self._worker_tmp_dir = tmp_dir
            _logger.info("Worker temp directory created: %s", tmp_dir)
        except OSError as exc:
            _logger.error("Failed to create worker temp directory: %s", exc)
            return None

        return self._worker_tmp_dir

    def cleanup_worker_tmp_dir(self) -> None:
        """
            Clean up the worker temporary directory.

            Removes the temporary directory and all its contents if it
            exists.
        """
        if self._worker_tmp_dir is not None and os.path.isdir(self._worker_tmp_dir):
            try:
                os.rmdir(self._worker_tmp_dir)
                _logger.info(
                    "Worker temp directory removed: %s",
                    self._worker_tmp_dir,
                )
            except OSError as exc:
                _logger.warning(
                    "Failed to remove worker temp directory %s: %s",
                    self._worker_tmp_dir,
                    exc,
                )

        self._worker_tmp_dir = None

        return

    def get_status(self) -> dict:
        """
            Get the current resource limiter status.

            :returns: Dictionary with resource limit status information.
        """
        rtnval = {
            "memory_limit": self._config.limit_memory,
            "request_body_limit": self._config.limit_request_body,
            "request_field_size_limit": self._config.limit_request_field_size,
            "worker_memory": dict(self._worker_memory),
            "worker_tmp_dir": self._worker_tmp_dir,
            "warnings": list(self._warnings),
        }

        return rtnval

    def reset(self) -> None:
        """
            Reset the resource limiter state.

            Clears all tracked worker memory and warnings.
        """
        self._worker_memory.clear()
        self._warnings.clear()

        return
