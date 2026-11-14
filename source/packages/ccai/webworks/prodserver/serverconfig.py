"""
    Server configuration module for the production server.

    This module provides the ServerConfig dataclass for configuring the
    production server including binding, workers, connection management,
    limits, SSL/TLS, process management, logging, health checks, metrics,
    and tracing options. It also provides the ServerState enum for server
    lifecycle states and exit code constants.

    The production server runs on the built-in WSGI server: to_wsgi_config()
    gives the ccai.webworks.wsgi ServerConfig that binds, parses and runs the
    workers with these settings.
"""

import os
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from ccai.webworks.prodserver.exceptions import ConfigurationError
from ccai.webworks.wsgi.constants import DEFAULT_MAX_REQUEST_BODY_SIZE
from ccai.webworks.wsgi.serverconfig import ServerConfig as WSGIServerConfig
from ccai.webworks.wsgi.serverconfig import is_gevent_available


# Server exit codes
EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_CONFIG_ERROR = 2
EXIT_BIND_ERROR = 3
EXIT_APP_LOAD_ERROR = 4
EXIT_PID_FILE_ERROR = 5


# Valid worker classes. Both serve WSGI applications, and a WebApplication
# through its wsgi_app; its async handlers run on the event loop of the ASGI
# bridge in every worker, so there is no separate async worker class.
VALID_WORKER_CLASSES = {"sync", "gevent"}

# Header field count the parser accepts when limit_request_fields is 0 (unlimited)
UNLIMITED_REQUEST_FIELDS = 32768

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
    # The body is read into memory before the application is called, so the
    # default is a limit. 0 = unlimited.
    limit_request_body: int = DEFAULT_MAX_REQUEST_BODY_SIZE
    limit_memory: Optional[int] = None  # bytes of resident memory per worker
    worker_tmp_dir: Optional[str] = None  # parent of the workers' shared temp directory

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
        elif self.worker_class == "gevent" and not is_gevent_available():
            errors.append(
                "Worker class 'gevent' needs the gevent package, which is not installed. "
                "Install the 'gevent' extra: pip install 'codecraftai-webworks[gevent]'"
            )

        # Validate worker recycling
        if self.max_requests is not None and self.max_requests < 0:
            errors.append(f"Max requests must be non-negative, got {self.max_requests}")

        if self.max_requests_jitter < 0:
            errors.append(f"Max requests jitter must be non-negative, got {self.max_requests_jitter}")

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

        if self.max_connections is not None and self.max_connections < 1:
            errors.append(f"Max connections must be at least 1, got {self.max_connections}")

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

        if self.limit_memory is not None and self.limit_memory < 1:
            errors.append(f"Limit memory must be a positive number of bytes, got {self.limit_memory}")

        # The production endpoints are matched against the request path
        for option_name, path_value in (
            ("health_check_path", self.health_check_path),
            ("metrics_path", self.metrics_path),
        ):
            if not isinstance(path_value, str) or not path_value.startswith("/"):
                errors.append(f"{option_name} must be a path starting with '/', got {path_value!r}")

        if not isinstance(self.trace_header, str) or self.trace_header.strip() == "":
            errors.append(f"Trace header must be a header name, got {self.trace_header!r}")

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
            "worker_tmp_dir": self.worker_tmp_dir,
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

    def to_wsgi_config(self) -> WSGIServerConfig:
        """
            Build the configuration of the built-in WSGI server that runs
            the production server.

            The WSGI server binds the address, parses HTTP and runs the
            pre-forked workers with these settings:

            - workers, threads, worker class, max-requests recycling, timeouts
              and backlog are passed on,
            - limit_request_line, limit_request_fields and limit_request_body
              are enforced by its HTTP parser (414/431/413 before the
              application is called); limit_request_field_size bounds each
              header field in the production middleware and, times the field
              count, the whole header section in the parser,
            - its own access log is turned off, the production layer writes
              the structured access log.

            :returns: The WSGI server configuration.
        """
        if self.max_connections is not None:
            max_connections = self.max_connections
        else:
            max_connections = WSGIServerConfig.max_connections

        if self.max_requests is not None:
            max_requests = self.max_requests
        else:
            max_requests = 0

        # 0 means unlimited for every limit; the parser needs a count of
        # header fields, so "unlimited" fields is its largest sensible count.
        if self.limit_request_fields > 0:
            max_headers = self.limit_request_fields
        else:
            max_headers = UNLIMITED_REQUEST_FIELDS

        if self.limit_request_fields > 0 and self.limit_request_field_size > 0:
            max_header_size = self.limit_request_fields * (self.limit_request_field_size + 2)
        else:
            max_header_size = 0

        rtnval = WSGIServerConfig(
            host=self.host,
            port=self.port,
            backlog=self.backlog,
            workers=self.resolve_workers(),
            threads=self.threads,
            worker_class=self.worker_class,
            max_requests=max_requests,
            max_requests_jitter=self.max_requests_jitter,
            timeout=self.timeout,
            keepalive=self.keep_alive,
            graceful_timeout=self.graceful_timeout,
            max_request_size=self.limit_request_body,
            max_request_line=self.limit_request_line,
            max_header_size=max_header_size,
            max_headers=max_headers,
            max_connections=max_connections,
            ssl_certfile=self.ssl_certfile,
            ssl_keyfile=self.ssl_keyfile,
            ssl_ca_certs=self.ssl_ca_certs,
            reload=False,
            debug=False,
            access_log=False,
            error_log=True,
            log_level=self.log_level.lower(),
        )

        return rtnval
