"""
    Base class for CLI commands in the webworks developer experience.

    This module defines the :class:`CLICommand` base class that all CLI
    commands must subclass. Commands declare metadata via class attributes
    and implement the :meth:`execute` method to perform their specific
    development task.

    The :class:`CLICommand` integrates with Python's :mod:`argparse` module
    to provide argument parsing and built-in ``--help`` support for each
    command.
"""

from typing import Any, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace


class CLICommand:
    """
        Base class for CLI commands.

        Subclass this to create custom CLI commands that integrate with
        the webworks CLI framework. Commands declare metadata via class
        attributes and implement the :meth:`execute` method to perform
        their specific task.

        Class attributes:
            name: The command name used on the command line.
            help: Help text displayed when ``--help`` is used.
    """

    name: str = ""
    help: str = ""

    def add_arguments(self, parser: "ArgumentParser") -> None:
        """
            Add command-specific arguments to the argument parser.

            Override this method to register additional arguments or
            options that the command accepts. The base implementation
            does nothing, allowing commands with no extra arguments
            to skip overriding this method.

            :param parser: The argument parser to add arguments to.
        """
        return

    def execute(self, args: "Namespace", config: Dict[str, Any]) -> int:
        """
            Execute the command.

            Subclasses must override this method to implement the
            command's functionality. The base implementation raises
            :class:`NotImplementedError` to ensure subclasses provide
            their own implementation.

            :param args: Parsed command-line arguments.
            :param config: Loaded configuration dictionary.

            :returns: Exit code where 0 indicates success and non-zero indicates an error.

            :raises: NotImplementedError
        """
        raise NotImplementedError("Subclasses must implement the execute method.")
