"""
    Server configuration module for the production server.

    This module provides the ServerConfig dataclass for configuring the
    production server including binding, workers, connection management,
    limits, SSL/TLS, process management, logging, health checks, metrics,
    and tracing options. It also provides the ServerState enum for server
    lifecycle states and exit code constants.
"""

import os
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from automojo.webworks.prodserver.exceptions import ConfigurationError


# Server exit codes
EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_CONFIG_ERROR = 2
EXIT_BIND_ERROR = 3
EXIT_APP_LOAD_ERROR = 4
EXIT_PID_FILE_ERROR = 5


# Valid worker classes
VALID_WORKER_CLASSES = {"sync", "async", "gevent"}

# Valid log levels
VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}

# Valid log formats
VALID_LOG_FORMATS = {"standard", "json"}


class ServerState(Enum):
    """
        Server lifecycle states.

        Represents the possible states of the production server during
        its lifecycle from startup through shutdown.
    """
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    SHUTTING_DOWN = "shutting_down"
    RELOADING = "reloading"


@dataclass
class ServerConfig:
    """
        Configuration for the production server.

        This dataclass contains all configuration options for the production
        server including binding, workers, connection management, limits,
        SSL/TLS, process management, logging, health checks, metrics,
        and tracing options.
    """

    # Binding
    host: str = "0.0.0.0"
    port: int = 8000

    # Workers
    workers: int = 0  # 0 = auto-detect based on CPU cores
    threads: int = 1
    worker_class: str = "sync"
    max_requests: Optional[int] = None
    max_requests_jitter: int = 0
    timeout: int = 30
    graceful_timeout: int = 30

    # Connection
    backlog: int = 2048
    keep_alive: int = 5
    max_connections: Optional[int] = None

    # Limits
    limit_request_line: int = 4094
    limit_request_fields: int = 100
    limit_request_field_size: int = 8190
    limit_request_body: int = 0  # 0 = unlimited
    limit_memory: Optional[int] = None

    # SSL/TLS
    ssl_certfile: Optional[str] = None
    ssl_keyfile: Optional[str] = None
    ssl_ca_certs: Optional[str] = None
    ssl_ciphers: str = "TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256"
    ssl_version: str = "TLSv1_2"
    ssl_redirect: bool = False

    # Process
    pid_file: Optional[str] = None
    daemon: bool = False
    user: Optional[str] = None
    group: Optional[str] = None
    umask: int = 0
    chdir: Optional[str] = None
    preload: bool = False

    # Logging
    log_format: str = "standard"  # "standard" or "json"
    access_log: Optional[str] = None
    error_log: Optional[str] = None
    log_level: str = "INFO"

    # Health checks
    health_check_path: str = "/health"

    # Metrics
    metrics_path: str = "/metrics"
    statsd_host: Optional[str] = None
    statsd_port: int = 8125

    # Tracing
    trace_header: str = "X-Request-ID"
    enable_tracing: bool = False

    # Hooks
    on_starting: Optional[Callable] = None
    on_reload: Optional[Callable] = None
    when_ready: Optional[Callable] = None
    on_exit: Optional[Callable] = None

    def resolve_workers(self) -> int:
        """
            Resolve the effective worker count.

            When workers is set to 0, auto-detects based on CPU cores
            using the formula: CPU cores * 2 + 1.

            :returns: The resolved number of worker processes.
        """
        if self.workers == 0:
            cpu_count = os.cpu_count()
            if cpu_count is None:
                cpu_count = 1
            rtnval = cpu_count * 2 + 1
        else:
            rtnval = self.workers

        return rtnval

    def validate(self) -> None:
        """
            Validate configuration values and raise on errors.

            Checks that all configuration values are within acceptable ranges
            and that required combinations of settings are valid.

            :raises: ConfigurationError if validation fails.
        """
        errors: List[str] = []

        # Validate port range
        if self.port < 0 or self.port > 65535:
            errors.append(f"Port must be between 0 and 65535, got {self.port}")

        # Validate workers (0 is valid for auto-detect)
        if self.workers < 0:
            errors.append(f"Workers must be non-negative, got {self.workers}")

        # Validate threads
        if self.threads < 1:
            errors.append(f"Threads must be at least 1, got {self.threads}")

        # Validate worker_class
        if self.worker_class not in VALID_WORKER_CLASSES:
            errors.append(
                f"Worker class must be one of {VALID_WORKER_CLASSES}, got '{self.worker_class}'"
            )

        # Validate timeouts
        if self.timeout < 0:
            errors.append(f"Timeout must be non-negative, got {self.timeout}")

        if self.graceful_timeout < 0:
            errors.append(f"Graceful timeout must be non-negative, got {self.graceful_timeout}")

        # Validate connection settings
        if self.backlog < 1:
            errors.append(f"Backlog must be at least 1, got {self.backlog}")

        if self.keep_alive < 0:
            errors.append(f"Keep-alive must be non-negative, got {self.keep_alive}")

        # Validate limits
        if self.limit_request_line < 0:
            errors.append(
                f"Limit request line must be non-negative, got {self.limit_request_line}"
            )

        if self.limit_request_fields < 0:
            errors.append(
                f"Limit request fields must be non-negative, got {self.limit_request_fields}"
            )

        if self.limit_request_field_size < 0:
            errors.append(
                f"Limit request field size must be non-negative, got {self.limit_request_field_size}"
            )

        if self.limit_request_body < 0:
            errors.append(
                f"Limit request body must be non-negative, got {self.limit_request_body}"
            )

        # Validate SSL configuration
        if self.ssl_certfile is not None or self.ssl_keyfile is not None:
            if self.ssl_certfile is None:
                errors.append("SSL certificate file required when SSL key file is specified")
            if self.ssl_keyfile is None:
                errors.append("SSL key file required when SSL certificate file is specified")

        # Validate log level
        if self.log_level.upper() not in VALID_LOG_LEVELS:
            errors.append(
                f"Log level must be one of {VALID_LOG_LEVELS}, got '{self.log_level}'"
            )

        # Validate log format
        if self.log_format not in VALID_LOG_FORMATS:
            errors.append(
                f"Log format must be one of {VALID_LOG_FORMATS}, got '{self.log_format}'"
            )

        if len(errors) > 0:
            raise ConfigurationError(errors)

        return

    def as_dict(self) -> Dict[str, Any]:
        """
            Convert configuration to a dictionary.

            Excludes callable hook fields from the output since they
            are not serializable.

            :returns: Dictionary representation of the configuration.
        """
        rtnval: Dict[str, Any] = {
            "host": self.host,
            "port": self.port,
            "workers": self.workers,
            "threads": self.threads,
            "worker_class": self.worker_class,
            "max_requests": self.max_requests,
            "max_requests_jitter": self.max_requests_jitter,
            "timeout": self.timeout,
            "graceful_timeout": self.graceful_timeout,
            "backlog": self.backlog,
            "keep_alive": self.keep_alive,
            "max_connections": self.max_connections,
            "limit_request_line": self.limit_request_line,
            "limit_request_fields": self.limit_request_fields,
            "limit_request_field_size": self.limit_request_field_size,
            "limit_request_body": self.limit_request_body,
            "limit_memory": self.limit_memory,
            "ssl_certfile": self.ssl_certfile,
            "ssl_keyfile": self.ssl_keyfile,
            "ssl_ca_certs": self.ssl_ca_certs,
            "ssl_ciphers": self.ssl_ciphers,
            "ssl_version": self.ssl_version,
            "ssl_redirect": self.ssl_redirect,
            "pid_file": self.pid_file,
            "daemon": self.daemon,
            "user": self.user,
            "group": self.group,
            "umask": self.umask,
            "chdir": self.chdir,
            "preload": self.preload,
            "log_format": self.log_format,
            "access_log": self.access_log,
            "error_log": self.error_log,
            "log_level": self.log_level,
            "health_check_path": self.health_check_path,
            "metrics_path": self.metrics_path,
            "statsd_host": self.statsd_host,
            "statsd_port": self.statsd_port,
            "trace_header": self.trace_header,
            "enable_tracing": self.enable_tracing,
        }

        return rtnval
