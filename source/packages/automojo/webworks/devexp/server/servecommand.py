"""
    Serve command for the webworks CLI.

    This module provides the :class:`ServeCommand` that starts a
    development HTTP server with configurable host, port, debug mode,
    and auto-reload options.

    The command integrates with the :class:`DevelopmentServer` and
    handles port-in-use errors by displaying a user-friendly message
    with alternative port suggestions.
"""

from typing import Any, Dict, TYPE_CHECKING

from automojo.webworks.devexp.cli.command import CLICommand
from automojo.webworks.devexp.cli.exitcodes import EXIT_ERROR
from automojo.webworks.devexp.cli.exitcodes import EXIT_SUCCESS
from automojo.webworks.devexp.server.devserver import (
    DevelopmentServer,
    PortInUseError,
    format_port_in_use_message,
)

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace


class ServeCommand(CLICommand):
    """
        CLI command for starting the development server.

        The ``serve`` command creates a :class:`DevelopmentServer` with
        the specified options and starts it. Debug mode is enabled by
        default and can be disabled with ``--no-debug``. Auto-reload
        can be enabled with ``--reload``.

        Usage::

            webworks serve
            webworks serve --host 0.0.0.0 --port 9000
            webworks serve --reload
            webworks serve --no-debug
    """

    name = "serve"
    help = "Start the development server."

    def add_arguments(self, parser: "ArgumentParser") -> None:
        """
            Add server-specific arguments to the parser.

            Registers ``--host``, ``--port``, ``--reload``, and
            ``--no-debug`` options.

            :param parser: The argument parser to add arguments to.
        """
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
            help="Enable auto-reload on file changes."
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

        return

    def execute(self, args: "Namespace", config: Dict[str, Any]) -> int:
        """
            Execute the serve command.

            Resolves the host and port from command-line arguments,
            configuration, or defaults. Creates a :class:`DevelopmentServer`
            and starts it. If the port is already in use, prints an error
            message with suggestions and returns ``EXIT_ERROR``.

            :param args: Parsed command-line arguments.
            :param config: Loaded configuration dictionary.

            :returns: Exit code where 0 indicates success.
        """
        server_config = config.get("server", {})

        host = getattr(args, "host", None)
        if host is None:
            host = server_config.get("host", "127.0.0.1")

        port = getattr(args, "port", None)
        if port is None:
            port = server_config.get("port", 8000)

        reload_enabled = getattr(args, "reload", False)

        no_debug = getattr(args, "no_debug", False)
        debug = not no_debug

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

        server = DevelopmentServer(
            app=None,
            host=host,
            port=port,
            debug=debug,
            reload=reload_enabled,
            watch_patterns=watch_patterns,
        )

        try:
            server.serve_forever()
        except PortInUseError:
            message = format_port_in_use_message(host, port)
            print(message)
            return EXIT_ERROR

        return EXIT_SUCCESS
