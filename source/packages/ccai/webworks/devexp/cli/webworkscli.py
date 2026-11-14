"""
    Main CLI entry point for the webworks developer experience.

    This module defines the :class:`WebworksCLI` class that serves as the
    root entry point for all webworks CLI subcommands. It provides command
    and group registration, argument parsing with global options, and
    dispatches execution to the appropriate command handler.

    Global options such as ``--verbose``, ``--config``, ``--env`` and
    ``--app`` are available to all commands and are parsed before
    command-specific arguments.

    :func:`main` is the function behind the ``webworks`` console script
    and ``python -m ccai.webworks.devexp.cli``. It builds a CLI with the
    built-in commands registered (see :func:`create_default_cli`).
"""

import argparse
import sys
import traceback

from typing import Any, Dict, List, Optional

from ccai.webworks.devexp.cli.command import CLICommand
from ccai.webworks.devexp.cli.config import ConfigFileError
from ccai.webworks.devexp.cli.config import load_config
from ccai.webworks.devexp.cli.exitcodes import EXIT_CONFIG_ERROR
from ccai.webworks.devexp.cli.exitcodes import EXIT_ERROR
from ccai.webworks.devexp.cli.exitcodes import EXIT_USAGE_ERROR
from ccai.webworks.devexp.cli.group import CLIGroup


class WebworksCLI:
    """
        Main CLI entry point providing command registration and execution.

        The :class:`WebworksCLI` manages a collection of top-level commands
        and command groups. It builds an :class:`argparse.ArgumentParser`
        with global options and delegates execution to the matched command
        handler based on the parsed arguments.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
            Initialize the WebworksCLI instance.

            :param config_path: Optional path to a configuration file.
        """
        self._config_path = config_path
        self._config: Dict[str, Any] = {}
        self._commands: Dict[str, CLICommand] = {}
        self._groups: Dict[str, CLIGroup] = {}
        return

    @property
    def config_path(self) -> Optional[str]:
        """
            The path to the configuration file.

            :returns: The configuration file path or None.
        """
        return self._config_path

    @property
    def config(self) -> Dict[str, Any]:
        """
            The loaded configuration dictionary.

            :returns: A dictionary of configuration values.
        """
        return self._config

    @property
    def commands(self) -> Dict[str, CLICommand]:
        """
            The registered top-level commands.

            :returns: A dictionary mapping command names to command instances.
        """
        return dict(self._commands)

    @property
    def groups(self) -> Dict[str, CLIGroup]:
        """
            The registered command groups.

            :returns: A dictionary mapping group names to group instances.
        """
        return dict(self._groups)

    def register_command(self, command: CLICommand) -> None:
        """
            Register a top-level command.

            :param command: The :class:`CLICommand` instance to register.
        """
        self._commands[command.name] = command
        return

    def register_group(self, group: CLIGroup) -> None:
        """
            Register a command group.

            :param group: The :class:`CLIGroup` instance to register.
        """
        self._groups[group.name] = group
        return

    def _build_parser(self) -> argparse.ArgumentParser:
        """
            Build the argument parser with global options and registered
            commands and groups.

            Global options are added to the root parser. Each registered
            command and group is added as a subparser so the user can
            invoke them by name.

            :returns: The configured argument parser.
        """
        parser = argparse.ArgumentParser(
            prog="webworks",
            description="Webworks developer experience CLI."
        )

        parser.add_argument(
            "--verbose",
            action="store_true",
            default=False,
            help="Enable verbose output."
        )
        parser.add_argument(
            "--config",
            type=str,
            default=None,
            help="Path to configuration file."
        )
        parser.add_argument(
            "--env",
            type=str,
            default=None,
            help="Target environment name."
        )
        parser.add_argument(
            "--app",
            type=str,
            default=None,
            help=(
                "Application import target 'module:attribute', for example 'app:app'. "
                "Used by serve, prodserve, routes, shell and db."
            ),
        )

        subparsers = parser.add_subparsers(dest="subcommand")

        for cmd_name, cmd in self._commands.items():
            sub_parser = subparsers.add_parser(cmd_name, help=cmd.help)
            cmd.add_arguments(sub_parser)
            sub_parser.set_defaults(command_handler=cmd)

        for group_name, group in self._groups.items():
            group_parser = subparsers.add_parser(group_name, help=group.help)
            group.register_commands(group_parser)

        return parser

    def run(self, args: Optional[List[str]] = None) -> int:
        """
            Parse arguments and execute the appropriate command.

            Builds the argument parser, parses the provided arguments
            (or sys.argv if None), and dispatches execution to the
            matched command handler. If no command is specified, the
            help text is printed and a usage error exit code is returned.

            When configuration loading fails, the reason is printed to
            standard error and the method returns ``EXIT_CONFIG_ERROR``.
            When an unhandled exception occurs during command execution,
            the error is printed to standard error -- with its traceback
            when ``--verbose`` is given -- and the method returns
            ``EXIT_ERROR``.

            :param args: Optional list of argument strings. If None,
                sys.argv[1:] is used.

            :returns: Exit code where 0 indicates success and non-zero
                indicates an error.
        """
        parser = self._build_parser()

        if args is None:
            parsed = parser.parse_args()
        else:
            parsed = parser.parse_args(args)

        verbose = getattr(parsed, "verbose", False) is True

        # Update config_path from --config if provided
        if parsed.config is not None:
            self._config_path = parsed.config

        try:
            self._config = load_config(self._config_path)
        except ConfigFileError as err:
            print("Error: {}".format(err), file=sys.stderr)
            return EXIT_CONFIG_ERROR
        except Exception as err:
            print(
                "Error: failed to load configuration: {}: {}".format(type(err).__name__, err),
                file=sys.stderr,
            )
            if verbose:
                traceback.print_exc(file=sys.stderr)
            return EXIT_CONFIG_ERROR

        handler = getattr(parsed, "command_handler", None)

        if handler is None:
            parser.print_help()
            return EXIT_USAGE_ERROR

        try:
            exit_code = handler.execute(parsed, self._config)
        except Exception as err:
            print(
                "Error: {}: {}".format(type(err).__name__, err),
                file=sys.stderr,
            )
            if verbose:
                traceback.print_exc(file=sys.stderr)
            else:
                print("Run the command with --verbose for the full traceback.", file=sys.stderr)
            return EXIT_ERROR

        return exit_code


# =============================================================================
# Console Entry Point
# =============================================================================

def create_default_cli(config_path: Optional[str] = None) -> WebworksCLI:
    """
        Create a :class:`WebworksCLI` with the built-in commands registered.

        Registers ``serve``, ``prodserve``, ``new``, ``routes`` and ``shell``
        as top-level commands and the ``generate`` and ``db`` command groups.

        :param config_path: Optional path to a configuration file.

        :returns: The configured CLI.
    """
    # Imported here because the command modules import this package's
    # framework classes; importing them at module scope would be circular
    # for callers that import a command module first.
    from ccai.webworks.devexp.cli.database import DatabaseGroup
    from ccai.webworks.devexp.cli.generators import GenerateGroup
    from ccai.webworks.devexp.cli.prodserve import ProdServeCommand
    from ccai.webworks.devexp.cli.routes import RoutesCommand
    from ccai.webworks.devexp.cli.scaffolding import NewProjectCommand
    from ccai.webworks.devexp.cli.shell import ShellCommand
    from ccai.webworks.devexp.server.servecommand import ServeCommand

    cli = WebworksCLI(config_path=config_path)

    cli.register_command(ServeCommand())
    cli.register_command(ProdServeCommand())
    cli.register_command(NewProjectCommand())
    cli.register_command(RoutesCommand())
    cli.register_command(ShellCommand())

    cli.register_group(GenerateGroup())
    cli.register_group(DatabaseGroup())

    return cli


def main(args: Optional[List[str]] = None) -> int:
    """
        Run the ``webworks`` command line.

        This is the target of the ``webworks`` console script declared in
        ``pyproject.toml`` and of ``python -m ccai.webworks.devexp.cli``.

        :param args: Optional list of argument strings. If None,
            sys.argv[1:] is used.

        :returns: The exit code of the command.
    """
    cli = create_default_cli()

    try:
        exit_code = cli.run(args)
    except KeyboardInterrupt:
        # Ctrl-C is how a developer ends 'serve' and 'shell'.
        exit_code = 130

    return exit_code
