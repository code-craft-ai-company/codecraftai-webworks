"""
    CLI command group for organizing related commands.

    This module defines the :class:`CLIGroup` class that organizes related
    :class:`CLICommand` instances under a common namespace. Groups create
    subparsers on an :class:`ArgumentParser` so each command in the group
    receives its own argument parser and help text.
"""

from typing import List, TYPE_CHECKING

from automojo.webworks.devexp.cli.command import CLICommand

if TYPE_CHECKING:
    from argparse import ArgumentParser


class CLIGroup:
    """
        A group of related CLI commands.

        Groups organize commands under a shared namespace so they can
        be invoked as subcommands. For example, a group named ``server``
        with commands ``start`` and ``stop`` would be invoked as
        ``webworks server start`` and ``webworks server stop``.

        Class attributes:
            name: The group name used on the command line.
            help: Help text displayed when ``--help`` is used.
    """

    name: str = ""
    help: str = ""

    def __init__(self, name: str = "", help: str = "", commands: List[CLICommand] = None):
        """
            Initialize a CLIGroup instance.

            :param name: The group name used on the command line.
            :param help: Help text displayed when ``--help`` is used.
            :param commands: A list of :class:`CLICommand` instances belonging to this group.
        """
        if name != "":
            self.name = name

        if help != "":
            self.help = help

        if commands is not None:
            self._commands = list(commands)
        else:
            self._commands = []

        return

    @property
    def commands(self) -> List[CLICommand]:
        """
            The list of commands in this group.

            :returns: A list of :class:`CLICommand` instances.
        """
        return list(self._commands)

    def add_command(self, command: CLICommand) -> None:
        """
            Add a command to this group.

            :param command: The :class:`CLICommand` instance to add.
        """
        self._commands.append(command)
        return

    def register_commands(self, parser: "ArgumentParser") -> None:
        """
            Register all commands in this group as subparsers.

            Creates a subparser group on the provided parser and adds
            each command as a subparser with its own arguments and help
            text. Each subparser stores a reference to its command via
            the ``command_handler`` default so the CLI framework can
            dispatch execution to the correct command.

            :param parser: The argument parser to register subparsers on.
        """
        subparsers = parser.add_subparsers(dest="command")

        for cmd in self._commands:
            sub_parser = subparsers.add_parser(cmd.name, help=cmd.help)
            cmd.add_arguments(sub_parser)
            sub_parser.set_defaults(command_handler=cmd)

        return
