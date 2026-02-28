"""
    Server configuration module for the WSGI layer.
    
    This module provides the ServerConfig dataclass for configuring the built-in
    WSGI server including network binding, worker configuration, timeouts, limits,
    and SSL/TLS settings.
"""

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from automojo.webworks.wsgi.exceptions import ServerError


class ConfigurationError(ServerError):
    """
        Configuration validation error.
        
        Raised when server configuration values are invalid.
    """
    
    def __init__(self, errors: List[str]):
        """
            Construct a ConfigurationError exception.
            
            :param errors: List of validation error messages.
        """
        self._errors = errors
        message = "Configuration validation failed: " + "; ".join(errors)
        super().__init__(message)
        return
    
    @property
    def errors(self) -> List[str]:
        """
            Get the list of validation errors.
            
            :returns: List of error messages.
        """
        return self._errors


@dataclass
class ServerConfig:
    """
        Configuration for the built-in WSGI server.
        
        This dataclass contains all configuration options for the WSGI server
        including network binding, worker configuration, timeouts, limits,
        and SSL/TLS settings.
    """
    
    # Network binding
    host: str = "127.0.0.1"
    port: int = 8000
    unix_socket: Optional[str] = None
    backlog: int = 2048
    
    # Worker configuration
    workers: int = 1
    threads: int = 1
    worker_class: str = "sync"
    
    # Timeouts (in seconds)
    timeout: int = 30
    keepalive: int = 2
    graceful_timeout: int = 30
    
    # Limits
    max_request_size: int = 0  # 0 = unlimited
    max_header_size: int = 8192  # 8KB default
    max_headers: int = 100
    max_connections: int = 1000  # Per worker
    
    # SSL/TLS
    ssl_certfile: Optional[str] = None
    ssl_keyfile: Optional[str] = None
    ssl_ca_certs: Optional[str] = None
    
    # Development options
    reload: bool = False
    debug: bool = False
    
    # Logging
    access_log: bool = True
    error_log: bool = True
    log_level: str = "info"

    
    @classmethod
    def from_environ(cls) -> "ServerConfig":
        """
            Create configuration from environment variables.
            
            Environment variables are prefixed with WSGI_SERVER_ and use
            uppercase names with underscores. For example:
            - WSGI_SERVER_HOST
            - WSGI_SERVER_PORT
            - WSGI_SERVER_WORKERS
            
            :returns: ServerConfig instance populated from environment.
        """
        config_dict: Dict[str, Any] = {}
        
        # String fields
        string_fields = [
            ("host", "WSGI_SERVER_HOST"),
            ("unix_socket", "WSGI_SERVER_UNIX_SOCKET"),
            ("worker_class", "WSGI_SERVER_WORKER_CLASS"),
            ("ssl_certfile", "WSGI_SERVER_SSL_CERTFILE"),
            ("ssl_keyfile", "WSGI_SERVER_SSL_KEYFILE"),
            ("ssl_ca_certs", "WSGI_SERVER_SSL_CA_CERTS"),
            ("log_level", "WSGI_SERVER_LOG_LEVEL"),
        ]
        
        for field_name, env_var in string_fields:
            value = os.environ.get(env_var)
            if value is not None:
                config_dict[field_name] = value
        
        # Integer fields
        int_fields = [
            ("port", "WSGI_SERVER_PORT"),
            ("backlog", "WSGI_SERVER_BACKLOG"),
            ("workers", "WSGI_SERVER_WORKERS"),
            ("threads", "WSGI_SERVER_THREADS"),
            ("timeout", "WSGI_SERVER_TIMEOUT"),
            ("keepalive", "WSGI_SERVER_KEEPALIVE"),
            ("graceful_timeout", "WSGI_SERVER_GRACEFUL_TIMEOUT"),
            ("max_request_size", "WSGI_SERVER_MAX_REQUEST_SIZE"),
            ("max_header_size", "WSGI_SERVER_MAX_HEADER_SIZE"),
            ("max_headers", "WSGI_SERVER_MAX_HEADERS"),
            ("max_connections", "WSGI_SERVER_MAX_CONNECTIONS"),
        ]
        
        for field_name, env_var in int_fields:
            value = os.environ.get(env_var)
            if value is not None:
                try:
                    config_dict[field_name] = int(value)
                except ValueError:
                    # Skip invalid integer values, validation will catch them
                    pass
        
        # Boolean fields
        bool_fields = [
            ("reload", "WSGI_SERVER_RELOAD"),
            ("debug", "WSGI_SERVER_DEBUG"),
            ("access_log", "WSGI_SERVER_ACCESS_LOG"),
            ("error_log", "WSGI_SERVER_ERROR_LOG"),
        ]
        
        for field_name, env_var in bool_fields:
            value = os.environ.get(env_var)
            if value is not None:
                # Accept common boolean representations
                config_dict[field_name] = value.lower() in ("true", "1", "yes", "on")
        
        rtnval = cls(**config_dict)
        return rtnval
    
    @classmethod
    def from_file(cls, path: str) -> "ServerConfig":
        """
            Load configuration from a JSON file.
            
            The file should contain a JSON object with configuration keys
            matching the ServerConfig field names.
            
            :param path: Path to the configuration file.
            
            :returns: ServerConfig instance populated from file.
            
            :raises: ConfigurationError if file cannot be read or parsed.
        """
        errors: List[str] = []
        
        if not os.path.exists(path):
            errors.append(f"Configuration file not found: {path}")
            raise ConfigurationError(errors)
        
        try:
            with open(path, "r", encoding="utf-8") as config_file:
                config_data = json.load(config_file)
        except json.JSONDecodeError as json_err:
            errors.append(f"Invalid JSON in configuration file: {json_err}")
            raise ConfigurationError(errors) from json_err
        except IOError as io_err:
            errors.append(f"Failed to read configuration file: {io_err}")
            raise ConfigurationError(errors) from io_err
        
        if not isinstance(config_data, dict):
            errors.append("Configuration file must contain a JSON object")
            raise ConfigurationError(errors)
        
        # Filter to only known fields
        known_fields = {
            "host", "port", "unix_socket", "backlog",
            "workers", "threads", "worker_class",
            "timeout", "keepalive", "graceful_timeout",
            "max_request_size", "max_header_size", "max_headers", "max_connections",
            "ssl_certfile", "ssl_keyfile", "ssl_ca_certs",
            "reload", "debug",
            "access_log", "error_log", "log_level",
        }
        
        config_dict: Dict[str, Any] = {}
        for key, value in config_data.items():
            if key in known_fields:
                config_dict[key] = value
        
        rtnval = cls(**config_dict)
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
        
        # Validate backlog
        if self.backlog < 1:
            errors.append(f"Backlog must be at least 1, got {self.backlog}")
        
        # Validate workers
        if self.workers < 1:
            errors.append(f"Workers must be at least 1, got {self.workers}")
        
        # Validate threads
        if self.threads < 1:
            errors.append(f"Threads must be at least 1, got {self.threads}")
        
        # Validate worker_class
        valid_worker_classes = {"sync", "thread"}
        if self.worker_class not in valid_worker_classes:
            errors.append(f"Worker class must be one of {valid_worker_classes}, got '{self.worker_class}'")
        
        # Validate timeouts
        if self.timeout < 0:
            errors.append(f"Timeout must be non-negative, got {self.timeout}")
        
        if self.keepalive < 0:
            errors.append(f"Keepalive must be non-negative, got {self.keepalive}")
        
        if self.graceful_timeout < 0:
            errors.append(f"Graceful timeout must be non-negative, got {self.graceful_timeout}")
        
        # Validate limits
        if self.max_request_size < 0:
            errors.append(f"Max request size must be non-negative, got {self.max_request_size}")
        
        if self.max_header_size < 0:
            errors.append(f"Max header size must be non-negative, got {self.max_header_size}")
        
        if self.max_headers < 1:
            errors.append(f"Max headers must be at least 1, got {self.max_headers}")
        
        if self.max_connections < 1:
            errors.append(f"Max connections must be at least 1, got {self.max_connections}")
        
        # Validate SSL configuration
        if self.ssl_certfile is not None or self.ssl_keyfile is not None:
            if self.ssl_certfile is None:
                errors.append("SSL certificate file required when SSL key file is specified")
            if self.ssl_keyfile is None:
                errors.append("SSL key file required when SSL certificate file is specified")
        
        if self.ssl_certfile is not None:
            if not os.path.exists(self.ssl_certfile):
                errors.append(f"SSL certificate file not found: {self.ssl_certfile}")
        
        if self.ssl_keyfile is not None:
            if not os.path.exists(self.ssl_keyfile):
                errors.append(f"SSL key file not found: {self.ssl_keyfile}")
        
        if self.ssl_ca_certs is not None:
            if not os.path.exists(self.ssl_ca_certs):
                errors.append(f"SSL CA certificates file not found: {self.ssl_ca_certs}")
        
        # Validate log_level
        valid_log_levels = {"debug", "info", "warning", "error", "critical"}
        if self.log_level.lower() not in valid_log_levels:
            errors.append(f"Log level must be one of {valid_log_levels}, got '{self.log_level}'")
        
        if len(errors) > 0:
            raise ConfigurationError(errors)
        
        return
    
    def as_dict(self, brief: bool = False) -> Dict[str, Any]:
        """
            Convert configuration to a dictionary.
            
            :param brief: If True, only include non-default values.
            
            :returns: Dictionary representation of the configuration.
        """
        rtnval: Dict[str, Any] = {
            "host": self.host,
            "port": self.port,
            "unix_socket": self.unix_socket,
            "backlog": self.backlog,
            "workers": self.workers,
            "threads": self.threads,
            "worker_class": self.worker_class,
            "timeout": self.timeout,
            "keepalive": self.keepalive,
            "graceful_timeout": self.graceful_timeout,
            "max_request_size": self.max_request_size,
            "max_header_size": self.max_header_size,
            "max_headers": self.max_headers,
            "max_connections": self.max_connections,
            "ssl_certfile": self.ssl_certfile,
            "ssl_keyfile": self.ssl_keyfile,
            "ssl_ca_certs": self.ssl_ca_certs,
            "reload": self.reload,
            "debug": self.debug,
            "access_log": self.access_log,
            "error_log": self.error_log,
            "log_level": self.log_level,
        }
        
        if brief is True:
            # Filter out None values for brief representation
            rtnval = {k: v for k, v in rtnval.items() if v is not None}
        
        return rtnval
    
    def to_json(self) -> str:
        """
            Serialize configuration to JSON string.
            
            :returns: JSON string representation of the configuration.
        """
        rtnval = json.dumps(self.as_dict(), indent=2)
        return rtnval
