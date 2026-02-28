"""
    Tests for the CLIGroup class.

    This module contains unit tests for the CLIGroup class including
    construction, command management, and subparser registration.
"""

from argparse import ArgumentParser, Namespace
from typing import Any, Dict

from automojo.webworks.devexp.cli.command import CLICommand
from automojo.webworks.devexp.cli.group import CLIGroup


# =============================================================================
# Test Helpers
# =============================================================================

class _StartCommand(CLICommand):
    """
        A concrete command for testing group registration.
    """

    name = "start"
    help = "Start the server"

    def add_arguments(self, parser: "ArgumentParser") -> None:
        """
            Add --port argument to the parser.

            :param parser: The argument parser to add arguments to.
        """
        parser.add_argument("--port", type=int, default=8000)
        return

    def execute(self, args: "Namespace", config: Dict[str, Any]) -> int:
        """
            Execute the start command.

            :param args: Parsed command-line arguments.
            :param config: Loaded configuration dictionary.

            :returns: Exit code 0 for success.
        """
        return 0


class _StopCommand(CLICommand):
    """
        A concrete command for testing group registration.
    """

    name = "stop"
    help = "Stop the server"

    def execute(self, args: "Namespace", config: Dict[str, Any]) -> int:
        """
            Execute the stop command.

            :param args: Parsed command-line arguments.
            :param config: Loaded configuration dictionary.

            :returns: Exit code 0 for success.
        """
        return 0


# =============================================================================
# Unit Tests for CLIGroup Construction
# =============================================================================

def test_group_default_name_is_empty():
    """
        Test that a CLIGroup created with no arguments has an empty name.
    """
    group = CLIGroup()

    if group.name != "":
        errmsg = "Expected default name to be empty string, got '{}'".format(group.name)
        raise AssertionError(errmsg)

    return


def test_group_default_help_is_empty():
    """
        Test that a CLIGroup created with no arguments has empty help text.
    """
    group = CLIGroup()

    if group.help != "":
        errmsg = "Expected default help to be empty string, got '{}'".format(group.help)
        raise AssertionError(errmsg)

    return


def test_group_default_commands_is_empty():
    """
        Test that a CLIGroup created with no arguments has an empty commands list.
    """
    group = CLIGroup()

    if len(group.commands) != 0:
        errmsg = "Expected empty commands list, got {} commands".format(len(group.commands))
        raise AssertionError(errmsg)

    return


def test_group_constructor_sets_name():
    """
        Test that the name parameter is stored correctly.
    """
    group = CLIGroup(name="server")

    if group.name != "server":
        errmsg = "Expected name 'server', got '{}'".format(group.name)
        raise AssertionError(errmsg)

    return


def test_group_constructor_sets_help():
    """
        Test that the help parameter is stored correctly.
    """
    group = CLIGroup(help="Server management commands")

    if group.help != "Server management commands":
        errmsg = "Expected help 'Server management commands', got '{}'".format(group.help)
        raise AssertionError(errmsg)

    return


def test_group_constructor_sets_commands():
    """
        Test that the commands parameter is stored correctly.
    """
    start_cmd = _StartCommand()
    stop_cmd = _StopCommand()

    group = CLIGroup(name="server", commands=[start_cmd, stop_cmd])

    if len(group.commands) != 2:
        errmsg = "Expected 2 commands, got {}".format(len(group.commands))
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for add_command Method
# =============================================================================

def test_group_add_command_increases_count():
    """
        Test that add_command adds a command to the group.
    """
    group = CLIGroup(name="server")
    start_cmd = _StartCommand()

    group.add_command(start_cmd)

    if len(group.commands) != 1:
        errmsg = "Expected 1 command after add_command, got {}".format(len(group.commands))
        raise AssertionError(errmsg)

    return


def test_group_add_command_preserves_order():
    """
        Test that commands are returned in the order they were added.
    """
    group = CLIGroup(name="server")
    start_cmd = _StartCommand()
    stop_cmd = _StopCommand()

    group.add_command(start_cmd)
    group.add_command(stop_cmd)

    commands = group.commands
    if commands[0].name != "start":
        errmsg = "Expected first command to be 'start', got '{}'".format(commands[0].name)
        raise AssertionError(errmsg)

    if commands[1].name != "stop":
        errmsg = "Expected second command to be 'stop', got '{}'".format(commands[1].name)
        raise AssertionError(errmsg)

    return


def test_group_commands_returns_copy():
    """
        Test that the commands property returns a copy, not the internal list.
    """
    group = CLIGroup(name="server")
    start_cmd = _StartCommand()
    group.add_command(start_cmd)

    commands_a = group.commands
    commands_b = group.commands

    if commands_a is commands_b:
        errmsg = "Expected commands property to return a new list each time."
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for register_commands Method
# =============================================================================

def test_group_register_commands_creates_subparsers():
    """
        Test that register_commands creates subparsers for each command.
    """
    group = CLIGroup(name="server", commands=[_StartCommand(), _StopCommand()])
    parser = ArgumentParser()

    group.register_commands(parser)

    # Parsing "start" should succeed without error
    parsed = parser.parse_args(["start"])

    if parsed.command != "start":
        errmsg = "Expected parsed command 'start', got '{}'".format(parsed.command)
        raise AssertionError(errmsg)

    return


def test_group_register_commands_sets_command_handler():
    """
        Test that register_commands sets the command_handler default on each subparser.
    """
    start_cmd = _StartCommand()
    group = CLIGroup(name="server", commands=[start_cmd])
    parser = ArgumentParser()

    group.register_commands(parser)

    parsed = parser.parse_args(["start"])

    handler = getattr(parsed, "command_handler", None)
    if handler is None:
        errmsg = "Expected command_handler to be set on parsed args."
        raise AssertionError(errmsg)

    if handler is not start_cmd:
        errmsg = "Expected command_handler to be the start command instance."
        raise AssertionError(errmsg)

    return


def test_group_register_commands_passes_arguments():
    """
        Test that command-specific arguments are registered on the subparser.
    """
    group = CLIGroup(name="server", commands=[_StartCommand()])
    parser = ArgumentParser()

    group.register_commands(parser)

    parsed = parser.parse_args(["start", "--port", "9000"])

    if parsed.port != 9000:
        errmsg = "Expected port 9000, got {}".format(parsed.port)
        raise AssertionError(errmsg)

    return


def test_group_register_commands_default_arguments():
    """
        Test that command-specific default argument values are preserved.
    """
    group = CLIGroup(name="server", commands=[_StartCommand()])
    parser = ArgumentParser()

    group.register_commands(parser)

    parsed = parser.parse_args(["start"])

    if parsed.port != 8000:
        errmsg = "Expected default port 8000, got {}".format(parsed.port)
        raise AssertionError(errmsg)

    return


def test_group_register_commands_multiple_commands():
    """
        Test that multiple commands can be parsed after registration.
    """
    group = CLIGroup(name="server", commands=[_StartCommand(), _StopCommand()])
    parser = ArgumentParser()

    group.register_commands(parser)

    parsed_start = parser.parse_args(["start"])
    parsed_stop = parser.parse_args(["stop"])

    if parsed_start.command != "start":
        errmsg = "Expected 'start' command, got '{}'".format(parsed_start.command)
        raise AssertionError(errmsg)

    if parsed_stop.command != "stop":
        errmsg = "Expected 'stop' command, got '{}'".format(parsed_stop.command)
        raise AssertionError(errmsg)

    return


def test_group_register_commands_empty_group():
    """
        Test that register_commands on an empty group does not raise.
    """
    group = CLIGroup(name="empty")
    parser = ArgumentParser()

    group.register_commands(parser)

    return
