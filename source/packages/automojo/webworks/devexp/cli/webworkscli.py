"""
    Main CLI entry point for the webworks developer experience.

    This module defines the :class:`WebworksCLI` class that serves as the
    root entry point for all webworks CLI subcommands. It provides command
    and group registration, argument parsing with global options, and
    dispatches execution to the appropriate command handler.

    Global options such as ``--verbose``, ``--config``, and ``--env`` are
    available to all commands and are parsed before command-specific
    arguments.
"""

import argparse
import sys

from typing import Any, Dict, List, Optional

from automojo.webworks.devexp.cli.command import CLICommand
from automojo.webworks.devexp.cli.config import load_config
from automojo.webworks.devexp.cli.exitcodes import EXIT_CONFIG_ERROR
from automojo.webworks.devexp.cli.exitcodes import EXIT_ERROR
from automojo.webworks.devexp.cli.exitcodes import EXIT_SUCCESS
from automojo.webworks.devexp.cli.exitcodes import EXIT_USAGE_ERROR
from automojo.webworks.devexp.cli.group import CLIGroup


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

            When configuration loading fails, the method returns
            ``EXIT_CONFIG_ERROR``. When an unhandled exception occurs
            during command execution, the method returns ``EXIT_ERROR``.

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

        # Update config_path from --config if provided
        if parsed.config is not None:
            self._config_path = parsed.config

        try:
            self._config = load_config(self._config_path)
        except Exception:
            return EXIT_CONFIG_ERROR

        handler = getattr(parsed, "command_handler", None)

        if handler is None:
            parser.print_help()
            return EXIT_USAGE_ERROR

        try:
            exit_code = handler.execute(parsed, self._config)
        except Exception:
            return EXIT_ERROR

        return exit_code
