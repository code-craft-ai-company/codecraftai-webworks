"""
    Production serve command for the webworks CLI.

    This module provides the :class:`ProdServeCommand` that runs an
    application with the production server
    (:class:`ccai.webworks.prodserver.ProductionServer`): pre-forked worker
    processes, graceful shutdown on SIGTERM/SIGINT, worker replacement on
    SIGHUP, health and metrics endpoints, request IDs and a structured access
    log.

    The application is named the way ``webworks serve`` names it: ``--app``
    with an import target (``module:attribute``), the ``server.app``
    configuration key, or ``app:app`` when ``./app.py`` exists. A
    WebApplication, the ASGI application of a site, or a WSGI callable can be
    named; with ``--factory`` the target is a callable that returns one.

    Every option has a key of the same name (with underscores) in the
    ``prodserver`` configuration section, so ``WEBWORKS_PRODSERVER_WORKERS=4``
    in the environment or ``{"prodserver": {"workers": 4}}`` in the
    configuration file sets ``--workers``. Options given on the command line
    win over the configuration.
"""

import argparse
import dataclasses
import functools
import sys

from typing import Any, Dict, TYPE_CHECKING, Union

from ccai.webworks.devexp.apploader import ApplicationLoadError
from ccai.webworks.devexp.apploader import load_application
from ccai.webworks.devexp.apploader import parse_app_target
from ccai.webworks.devexp.apploader import resolve_app_target
from ccai.webworks.devexp.cli.command import CLICommand
from ccai.webworks.devexp.cli.exitcodes import EXIT_CONFIG_ERROR
from ccai.webworks.prodserver.exceptions import ConfigurationError
from ccai.webworks.prodserver.productionserver import ProductionServer
from ccai.webworks.prodserver.serverconfig import (
    ServerConfig,
    VALID_LOG_FORMATS,
    VALID_LOG_LEVELS,
    VALID_WORKER_CLASSES,
)
from ccai.webworks.wsgi.application import resolve_wsgi_application

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace


CONFIG_SECTION = "prodserver"
"""Configuration section the options of ``prodserve`` are read from."""

# ServerConfig fields that hold code (lifecycle hooks); they are set in code,
# not from the command line or a configuration file.
_CODE_ONLY_FIELDS = frozenset({"on_starting", "on_reload", "when_ready", "on_exit"})

# Strings read as True for a boolean option from the environment
_TRUE_STRINGS = frozenset({"true", "1", "yes", "on"})


def load_production_application(target: str, is_factory: bool) -> Any:
    """
        Load the application an import target names, for the production server.

        :param target: The import target, ``module:attribute``.
        :param is_factory: True if the target names a callable that returns
            the application.

        :returns: The WSGI callable to serve.

        :raises ApplicationLoadError: If the target cannot be imported, or a
            factory target is not callable.
    """
    if is_factory:
        factory = load_application(target)

        if not callable(factory):
            errmsg = "The application factory '{}' names a {} object, which cannot be called.".format(
                target, type(factory).__name__
            )
            raise ApplicationLoadError(errmsg)

        # Imported here: as_wsgi_application imports the web application
        from ccai.webworks.wsgi.application import as_wsgi_application

        rtnval = as_wsgi_application(factory())
    else:
        rtnval = resolve_wsgi_application(target)

    return rtnval


def _coerce_config_value(field: "dataclasses.Field", value: Any) -> Any:
    """
        Convert a value of the configuration section to the type of its option.

        Values that come from the environment are strings.

        :param field: The ServerConfig field of the option.
        :param value: The configured value.

        :returns: The value with the type of the field.

        :raises ConfigurationError: If the value cannot be converted.
    """
    if not isinstance(value, str):
        return value

    field_type = field.type
    optional = False

    if getattr(field_type, "__origin__", None) is Union:
        arguments = [argument for argument in field_type.__args__ if argument is not type(None)]
        optional = True
        if len(arguments) == 1:
            field_type = arguments[0]

    if optional and value.strip().lower() == "none":
        return None

    if field_type is bool:
        rtnval = value.strip().lower() in _TRUE_STRINGS
        return rtnval

    if field_type is int:
        try:
            rtnval = int(value.strip(), 0)
        except ValueError as value_err:
            errors = [f"{CONFIG_SECTION}.{field.name} must be a whole number, got {value!r}"]
            raise ConfigurationError(errors) from value_err
        return rtnval

    return value


def _umask_value(text: str) -> int:
    """
        Read a umask given on the command line.

        :param text: The umask, octal ("022", "0o022") or another integer literal.

        :returns: The umask as an integer.
    """
    stripped = text.strip()

    if stripped.startswith(("0x", "0X", "0o", "0O", "0b", "0B")):
        rtnval = int(stripped, 0)
    else:
        rtnval = int(stripped, 8)

    return rtnval


class ProdServeCommand(CLICommand):
    """
        CLI command that runs an application with the production server.

        Usage::

            webworks prodserve --app mysite.app:webapp --workers 4 --port 8000
            webworks prodserve --app mysite.app:create_app --factory --preload
            webworks prodserve --app mysite.app:webapp --pid-file /run/mysite.pid \\
                --user www-data --log-format json --access-log /var/log/mysite/access.log
    """

    name = "prodserve"
    help = "Run an application with the production server."

    def add_arguments(self, parser: "ArgumentParser") -> None:
        """
            Add the production server options to the parser.

            Options left out are taken from the ``prodserver`` configuration
            section, then from the ServerConfig defaults.

            :param parser: The argument parser to add arguments to.
        """
        parser.add_argument(
            "--app",
            type=str,
            default=argparse.SUPPRESS,
            help=(
                "Application to serve as an import target 'module:attribute', for example "
                "'mysite.app:webapp'. Default: the 'server.app' configuration key, then "
                "'app:app' when ./app.py exists."
            ),
        )
        parser.add_argument(
            "--factory",
            action="store_true",
            default=False,
            help="The --app target is a callable without arguments that returns the application.",
        )

        binding = parser.add_argument_group("binding")
        binding.add_argument("--host", type=str, default=None, help="Address to bind to. Default: 0.0.0.0.")
        binding.add_argument("--port", type=int, default=None, help="Port to bind to. Default: 8000.")
        binding.add_argument("--backlog", type=int, default=None, help="Connection queue size. Default: 2048.")

        workers = parser.add_argument_group("workers")
        workers.add_argument(
            "--workers", type=int, default=None,
            help="Number of worker processes, 0 for 2 x CPU cores + 1. Default: 0.",
        )
        workers.add_argument("--threads", type=int, default=None, help="Threads per worker. Default: 1.")
        workers.add_argument(
            "--worker-class", type=str, choices=sorted(VALID_WORKER_CLASSES), default=None,
            help="Worker class; 'gevent' needs the gevent extra. Default: sync.",
        )
        workers.add_argument(
            "--max-requests", type=int, default=None,
            help="Replace a worker after it served this many requests. Default: never.",
        )
        workers.add_argument(
            "--max-requests-jitter", type=int, default=None,
            help="Add a random 0..N to --max-requests per worker. Default: 0.",
        )
        workers.add_argument(
            "--timeout", type=int, default=None,
            help="Seconds a request may take to start its response, and the socket timeout. Default: 30.",
        )
        workers.add_argument(
            "--graceful-timeout", type=int, default=None,
            help="Seconds in-flight requests get to finish at shutdown. Default: 30.",
        )
        workers.add_argument(
            "--keep-alive", type=int, default=None,
            help="Seconds an idle keep-alive connection is kept. Default: 5.",
        )
        workers.add_argument(
            "--max-connections", type=int, default=None,
            help="Concurrent connections per worker. Default: 1000.",
        )
        workers.add_argument(
            "--preload", action="store_true", default=None,
            help="Load the application in the master before the workers are forked.",
        )

        limits = parser.add_argument_group("limits")
        limits.add_argument("--limit-request-line", type=int, default=None, help="Request line bytes, 0 for no limit. Default: 4094.")
        limits.add_argument("--limit-request-fields", type=int, default=None, help="Header fields, 0 for no limit. Default: 100.")
        limits.add_argument("--limit-request-field-size", type=int, default=None, help="Bytes per header field, 0 for no limit. Default: 8190.")
        limits.add_argument("--limit-request-body", type=int, default=None, help="Request body bytes, 0 for no limit. Default: 16 MiB.")
        limits.add_argument("--limit-memory", type=int, default=None, help="Resident bytes per worker before it is replaced.")
        limits.add_argument("--worker-tmp-dir", type=str, default=None, help="Directory for the workers' shared temporary files.")

        tls = parser.add_argument_group("TLS")
        tls.add_argument("--ssl-certfile", type=str, default=None, help="TLS certificate file.")
        tls.add_argument("--ssl-keyfile", type=str, default=None, help="TLS private key file.")
        tls.add_argument("--ssl-ca-certs", type=str, default=None, help="CA certificates; clients must present a certificate.")
        tls.add_argument("--ssl-ciphers", type=str, default=None, help="Cipher suites to allow.")
        tls.add_argument("--ssl-version", type=str, choices=["TLSv1_2", "TLSv1_3"], default=None, help="Minimum TLS version. Default: TLSv1_2.")
        tls.add_argument(
            "--ssl-redirect", action="store_true", default=None,
            help="Redirect requests made over http (or X-Forwarded-Proto: http) to https.",
        )

        process = parser.add_argument_group("process")
        process.add_argument("--pid-file", type=str, default=None, help="Write the master PID to this file.")
        process.add_argument("--daemon", action="store_true", default=None, help="Run in the background.")
        process.add_argument("--user", type=str, default=None, help="User to switch to after binding.")
        process.add_argument("--group", type=str, default=None, help="Group to switch to after binding.")
        process.add_argument("--umask", type=_umask_value, default=None, help="File creation mask, octal.")
        process.add_argument("--chdir", type=str, default=None, help="Change to this directory before loading the application.")

        logging_group = parser.add_argument_group("logging and observability")
        logging_group.add_argument("--log-format", type=str, choices=sorted(VALID_LOG_FORMATS), default=None, help="Format of the access and error log. Default: standard.")
        logging_group.add_argument("--log-level", type=str.upper, choices=sorted(VALID_LOG_LEVELS), default=None, help="Log level. Default: INFO.")
        logging_group.add_argument("--access-log", type=str, default=None, help="Access log file. Default: standard output.")
        logging_group.add_argument("--error-log", type=str, default=None, help="Error log file. Default: standard error.")
        logging_group.add_argument("--health-check-path", type=str, default=None, help="Path of the health endpoint. Default: /health.")
        logging_group.add_argument("--metrics-path", type=str, default=None, help="Path of the Prometheus metrics endpoint. Default: /metrics.")
        logging_group.add_argument("--statsd-host", type=str, default=None, help="StatsD host.")
        logging_group.add_argument("--statsd-port", type=int, default=None, help="StatsD port. Default: 8125.")
        logging_group.add_argument("--trace-header", type=str, default=None, help="Request ID header. Default: X-Request-ID.")
        logging_group.add_argument("--enable-tracing", action="store_true", default=None, help="Create a tracing span for every request.")

        return

    def build_config(self, args: "Namespace", config: Dict[str, Any]) -> ServerConfig:
        """
            Build the server configuration from the options and the
            ``prodserver`` configuration section.

            :param args: Parsed command-line arguments.
            :param config: Loaded configuration dictionary.

            :returns: The ServerConfig; it has not been validated yet.

            :raises ConfigurationError: If the configuration section has a key
                that is not an option, or a value of the wrong type.
        """
        fields_by_name: Dict[str, "dataclasses.Field"] = {}
        for field in dataclasses.fields(ServerConfig):
            if field.name not in _CODE_ONLY_FIELDS:
                fields_by_name[field.name] = field

        section = config.get(CONFIG_SECTION, {})
        if section is None:
            section = {}

        if not isinstance(section, dict):
            errors = [f"The '{CONFIG_SECTION}' configuration section must be a mapping, got {type(section).__name__}"]
            raise ConfigurationError(errors)

        unknown = sorted(key for key in section.keys() if key not in fields_by_name)
        if len(unknown) > 0:
            errors = [f"Unknown '{CONFIG_SECTION}' configuration keys: {', '.join(unknown)}"]
            raise ConfigurationError(errors)

        values: Dict[str, Any] = {}
        for key, value in section.items():
            values[key] = _coerce_config_value(fields_by_name[key], value)

        for field_name in fields_by_name.keys():
            option_value = getattr(args, field_name, None)
            if option_value is not None:
                values[field_name] = option_value

        rtnval = ServerConfig(**values)
        return rtnval

    def execute(self, args: "Namespace", config: Dict[str, Any]) -> int:
        """
            Run the production server until it is stopped.

            :param args: Parsed command-line arguments.
            :param config: Loaded configuration dictionary.

            :returns: The exit code of the server: 0 after a clean shutdown,
                non-zero when it could not bind, the PID file is held by a
                running server, or the application could not be loaded.

            :raises ConfigurationError: If the options are invalid; the server
                is not started.
        """
        target = resolve_app_target(args, config)

        if target is None:
            print(
                "Error: No application to serve. Name one with --app 'module:attribute' "
                "(for example --app mysite.app:webapp), set the 'server.app' configuration key, "
                "or run the command in a directory that contains app.py.",
                file=sys.stderr,
            )
            return EXIT_CONFIG_ERROR

        try:
            parse_app_target(target)
        except ApplicationLoadError as target_err:
            print("Error: {}".format(target_err), file=sys.stderr)
            return EXIT_CONFIG_ERROR

        server_config = self.build_config(args, config)

        app_factory = functools.partial(load_production_application, target, args.factory is True)

        server = ProductionServer(app_factory=app_factory, config=server_config)
        exit_code = server.serve()

        return exit_code
