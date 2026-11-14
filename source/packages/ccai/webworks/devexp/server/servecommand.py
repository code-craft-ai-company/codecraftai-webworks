"""
    Serve command for the webworks CLI.

    This module provides the :class:`ServeCommand` that starts a
    development HTTP server with configurable host, port, debug mode,
    and auto-reload options.

    The application to serve is named by an import target
    (``module:attribute``) given with ``--app``, with the ``server.app``
    configuration key, or found as ``app:app`` in the current directory.

    The command integrates with the :class:`DevelopmentServer` and
    handles port-in-use errors by displaying a user-friendly message
    with alternative port suggestions.
"""

import argparse
import sys

from typing import Any, Dict, List, Optional, TYPE_CHECKING

from ccai.webworks.devexp.apploader import ApplicationLoadError
from ccai.webworks.devexp.apploader import load_application
from ccai.webworks.devexp.apploader import parse_app_target
from ccai.webworks.devexp.apploader import resolve_app_target
from ccai.webworks.devexp.cli.command import CLICommand
from ccai.webworks.devexp.cli.exitcodes import EXIT_CONFIG_ERROR
from ccai.webworks.devexp.cli.exitcodes import EXIT_ERROR
from ccai.webworks.devexp.cli.exitcodes import EXIT_SUCCESS
from ccai.webworks.devexp.logging.devlogger import DevLogger
from ccai.webworks.devexp.server.devserver import (
    DevelopmentServer,
    PortInUseError,
    format_port_in_use_message,
    is_loopback_host,
)
from ccai.webworks.devexp.server.reloader import ReloadNotSupportedError
from ccai.webworks.devexp.server.reloader import is_reload_child

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace


LOG_LEVEL_CHOICES = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
"""Values accepted by the ``--log-level`` option."""


class ServeCommand(CLICommand):
    """
        CLI command for starting the development server.

        The ``serve`` command imports the application named by the
        ``--app`` import target, creates a :class:`DevelopmentServer` with
        the specified options and starts it. Debug mode follows the
        ``server.debug`` configuration key (on by default) and can be
        disabled with ``--no-debug``. Auto-reload can be enabled with
        ``--reload``.

        Debug responses contain tracebacks, so debug mode is only used on
        a loopback address unless ``--debug`` asks for it explicitly.

        Usage::

            webworks serve --app app:app
            webworks serve --app mysite.app:app --host 0.0.0.0 --port 9000
            webworks serve --reload
            webworks serve --no-debug
            webworks serve --log-level INFO --log-file server.log
    """

    name = "serve"
    help = "Start the development server."

    def add_arguments(self, parser: "ArgumentParser") -> None:
        """
            Add server-specific arguments to the parser.

            Registers ``--app``, ``--host``, ``--port``, ``--reload``,
            ``--debug``, ``--no-debug``, ``--extra-files``, ``--log-level``
            and ``--log-file`` options.

            :param parser: The argument parser to add arguments to.
        """
        parser.add_argument(
            "--app",
            type=str,
            default=argparse.SUPPRESS,
            help=(
                "Application to serve as an import target 'module:attribute', "
                "for example 'app:app'. Default: the 'server.app' configuration "
                "key, then 'app:app' when ./app.py exists."
            ),
        )

        parser.add_argument(
            "--host",
            type=str,
            default=None,
            help="Host address to bind to. Default: 127.0.0.1."
        )

        parser.add_argument(
            "--port",
            type=int,
            default=None,
            help="Port number to bind to. Default: 8000."
        )

        parser.add_argument(
            "--reload",
            action="store_true",
            default=False,
            help="Restart the server in a fresh process when source files change."
        )

        parser.add_argument(
            "--debug",
            action="store_true",
            default=False,
            help=(
                "Enable debug mode explicitly. Required to use debug mode "
                "when binding to an address other machines can reach."
            ),
        )

        parser.add_argument(
            "--no-debug",
            action="store_true",
            default=False,
            help="Disable debug mode."
        )

        parser.add_argument(
            "--extra-files",
            type=str,
            default=None,
            help=(
                "Additional file patterns to watch for auto-reload, "
                "separated by commas. For example: '*.html,*.css,*.js'."
            ),
        )

        parser.add_argument(
            "--log-level",
            type=str.upper,
            choices=list(LOG_LEVEL_CHOICES),
            default=None,
            help="Log verbosity. Default: the 'logging.level' configuration key."
        )

        parser.add_argument(
            "--log-file",
            type=str,
            default=None,
            help="Also write the log to this file."
        )

        return

    # -------------------------------------------------------------------------
    # Option Resolution
    # -------------------------------------------------------------------------

    def resolve_debug(self, args: "Namespace", config: Dict[str, Any], host: str) -> bool:
        """
            Decide whether the server runs in debug mode.

            ``--no-debug`` turns debug off and ``--debug`` turns it on.
            Without either, the ``server.debug`` configuration key decides
            (``WEBWORKS_SERVER_DEBUG`` in the environment).

            Debug responses expose tracebacks, file paths and exception
            messages. When the server binds to an address that other
            machines can reach, debug mode that comes only from
            configuration or defaults is turned off and a warning is
            printed; it takes the explicit ``--debug`` option to keep it.

            :param args: Parsed command-line arguments.
            :param config: Loaded configuration dictionary.
            :param host: The host address the server will bind to.

            :returns: ``True`` if debug mode is to be enabled.
        """
        server_config = config.get("server", {})

        no_debug = getattr(args, "no_debug", False)
        explicit_debug = getattr(args, "debug", False)

        if no_debug:
            debug = False
        elif explicit_debug:
            debug = True
        else:
            debug = server_config.get("debug", True) is True

        if debug and not is_loopback_host(host):
            if explicit_debug:
                print(
                    "WARNING: debug mode is enabled on '{}', which other machines can reach. "
                    "Debug responses include tracebacks, file paths and exception messages.".format(host),
                    file=sys.stderr,
                )
            else:
                debug = False
                print(
                    "WARNING: debug mode was turned off because the server binds to '{}', "
                    "which other machines can reach. Pass --debug to enable it anyway.".format(host),
                    file=sys.stderr,
                )

        return debug

    def resolve_watch_patterns(self, args: "Namespace") -> Optional[List[str]]:
        """
            Build the file patterns watched for auto-reload.

            :param args: Parsed command-line arguments.

            :returns: The watch patterns, or ``None`` to use the server's
                defaults.
        """
        extra_files_raw = getattr(args, "extra_files", None)
        watch_patterns = None

        if extra_files_raw is not None:
            extra_patterns = [
                p.strip() for p in extra_files_raw.split(",") if p.strip()
            ]
            # Merge default Python patterns with extra file patterns
            watch_patterns = ["**/*.py"]
            for pattern in extra_patterns:
                # Ensure patterns use recursive glob format
                if not pattern.startswith("**/"):
                    pattern = "**/" + pattern
                watch_patterns.append(pattern)

        return watch_patterns

    def create_logger(self, args: "Namespace", config: Dict[str, Any], debug: bool) -> DevLogger:
        """
            Build the development logger for the server.

            ``--log-level`` and ``--log-file`` take precedence over the
            ``logging.level`` and ``logging.file`` configuration keys.

            :param args: Parsed command-line arguments.
            :param config: Loaded configuration dictionary.
            :param debug: Whether debug mode is enabled.

            :returns: A :class:`DevLogger` that has not been set up yet.
        """
        logging_config = config.get("logging", {})

        log_level = getattr(args, "log_level", None)
        if log_level is None:
            log_level = logging_config.get("level", None)

        log_file = getattr(args, "log_file", None)
        if log_file is None:
            log_file = logging_config.get("file", None)

        dev_logger = DevLogger(
            debug=debug,
            log_level=log_level,
            log_format=logging_config.get("format", None),
            use_colors=logging_config.get("colors", True),
            log_file=log_file,
        )

        return dev_logger

    def create_server(self, args: "Namespace", config: Dict[str, Any]) -> DevelopmentServer:
        """
            Build the development server for the given options.

            Resolves the application target, host, port, debug mode and
            reload setting from command-line arguments, configuration, or
            defaults. The application is imported here, except when this
            process will only supervise a reloading server process: then
            the import target is handed to the server and imported by the
            process that serves.

            :param args: Parsed command-line arguments.
            :param config: Loaded configuration dictionary.

            :returns: A :class:`DevelopmentServer` that has not been started.

            :raises ApplicationLoadError: If no application target is
                configured, the target cannot be imported, or it does not
                name a callable.
        """
        server_config = config.get("server", {})

        host = getattr(args, "host", None)
        if host is None:
            host = server_config.get("host", "127.0.0.1")

        port = getattr(args, "port", None)
        if port is None:
            port = server_config.get("port", 8000)

        reload_enabled = getattr(args, "reload", False) is True
        if not reload_enabled:
            reload_enabled = server_config.get("reload", False) is True

        debug = self.resolve_debug(args, config, host)
        watch_patterns = self.resolve_watch_patterns(args)

        target = resolve_app_target(args, config)

        if target is None:
            errmsg = (
                "No application to serve. Name one with --app 'module:attribute' "
                "(for example --app app:app), set the 'server.app' configuration key, "
                "or run the command in a directory that contains app.py."
            )
            raise ApplicationLoadError(errmsg)

        if reload_enabled and not is_reload_child():
            # This process only supervises; the server process imports the
            # application. Check the shape of the target now so a typo is
            # reported before anything is started.
            parse_app_target(target)
            application = target
        else:
            application = load_application(target)

            if not callable(application):
                errmsg = "The application target '{}' names a {} object, which is not a callable ASGI application.".format(
                    target, type(application).__name__
                )
                raise ApplicationLoadError(errmsg)

        server = DevelopmentServer(
            app=application,
            host=host,
            port=port,
            debug=debug,
            reload=reload_enabled,
            watch_patterns=watch_patterns,
            max_body_bytes=server_config.get("max_body_bytes", None),
        )

        return server

    # -------------------------------------------------------------------------
    # Execution
    # -------------------------------------------------------------------------

    def execute(self, args: "Namespace", config: Dict[str, Any]) -> int:
        """
            Execute the serve command.

            Builds the server, sets up development logging and serves until
            the server is stopped. If no application can be loaded, prints
            the reason and returns a non-zero exit code. If the port is
            already in use, prints an error message with suggestions and
            returns ``EXIT_ERROR``.

            :param args: Parsed command-line arguments.
            :param config: Loaded configuration dictionary.

            :returns: Exit code where 0 indicates success.
        """
        try:
            server = self.create_server(args, config)
        except ApplicationLoadError as err:
            print("Error: {}".format(err), file=sys.stderr)

            if resolve_app_target(args, config) is None:
                return EXIT_CONFIG_ERROR

            return EXIT_ERROR

        dev_logger = self.create_logger(args, config, server.debug)
        dev_logger.setup()

        exit_code = EXIT_SUCCESS

        try:
            server.serve_forever()

            if server.startup_failed:
                print("Error: the application failed to start.", file=sys.stderr)
                exit_code = EXIT_ERROR
        except PortInUseError:
            message = format_port_in_use_message(server.host, server.port)
            print(message, file=sys.stderr)
            exit_code = EXIT_ERROR
        except ApplicationLoadError as err:
            print("Error: {}".format(err), file=sys.stderr)
            exit_code = EXIT_ERROR
        except ReloadNotSupportedError as err:
            print("Error: {}".format(err), file=sys.stderr)
            exit_code = EXIT_ERROR
        finally:
            dev_logger.teardown()

        return exit_code
