"""
    Tests for the CLICommand base class.

    This module contains unit tests for the CLICommand class attributes,
    the add_arguments method, and the execute method behavior.
"""

import random
import string

from argparse import ArgumentParser, Namespace
from typing import Any, Dict

from automojo.webworks.devexp.cli.command import CLICommand


# =============================================================================
# Test Helpers
# =============================================================================

class _ConcreteCommand(CLICommand):
    """
        A minimal concrete subclass of CLICommand for testing purposes.
    """

    name = "test-cmd"
    help = "A test command"

    def execute(self, args: "Namespace", config: Dict[str, Any]) -> int:
        """
            Execute the test command.

            :param args: Parsed command-line arguments.
            :param config: Loaded configuration dictionary.

            :returns: Exit code 0 for success.
        """
        return 0


class _CommandWithArguments(CLICommand):
    """
        A concrete command that adds custom arguments for testing.
    """

    name = "args-cmd"
    help = "A command with arguments"

    def add_arguments(self, parser: "ArgumentParser") -> None:
        """
            Add a --name argument to the parser.

            :param parser: The argument parser to add arguments to.
        """
        parser.add_argument("--name", type=str, default="world")
        return

    def execute(self, args: "Namespace", config: Dict[str, Any]) -> int:
        """
            Execute the command using the --name argument.

            :param args: Parsed command-line arguments.
            :param config: Loaded configuration dictionary.

            :returns: Exit code 0 for success.
        """
        return 0


def _generate_random_string(min_length: int = 1, max_length: int = 20) -> str:
    """
        Generate a random string of alphanumeric characters.

        :param min_length: Minimum length of the generated string.
        :param max_length: Maximum length of the generated string.

        :returns: A random alphanumeric string.
    """
    length = random.randint(min_length, max_length)
    result = "".join(random.choices(string.ascii_lowercase + string.digits, k=length))
    return result


# =============================================================================
# Unit Tests for CLICommand Class Attributes
# =============================================================================

def test_command_has_name_attribute():
    """
        Test that a concrete CLICommand subclass exposes the name attribute.
    """
    cmd = _ConcreteCommand()

    if cmd.name != "test-cmd":
        errmsg = "Expected name 'test-cmd', got '{}'".format(cmd.name)
        raise AssertionError(errmsg)

    return


def test_command_has_help_attribute():
    """
        Test that a concrete CLICommand subclass exposes the help attribute.
    """
    cmd = _ConcreteCommand()

    if cmd.help != "A test command":
        errmsg = "Expected help 'A test command', got '{}'".format(cmd.help)
        raise AssertionError(errmsg)

    return


def test_command_default_name_is_empty():
    """
        Test that the base CLICommand class has an empty name by default.
    """
    # Create a minimal subclass that only implements execute
    class _MinimalCommand(CLICommand):
        def execute(self, args, config):
            return 0

    cmd = _MinimalCommand()

    if cmd.name != "":
        errmsg = "Expected default name to be empty string, got '{}'".format(cmd.name)
        raise AssertionError(errmsg)

    return


def test_command_default_help_is_empty():
    """
        Test that the base CLICommand class has empty help text by default.
    """
    class _MinimalCommand(CLICommand):
        def execute(self, args, config):
            return 0

    cmd = _MinimalCommand()

    if cmd.help != "":
        errmsg = "Expected default help to be empty string, got '{}'".format(cmd.help)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for add_arguments Method
# =============================================================================

def test_command_add_arguments_does_not_raise():
    """
        Test that the base add_arguments method does not raise an exception.
    """
    cmd = _ConcreteCommand()
    parser = ArgumentParser()

    cmd.add_arguments(parser)

    return


def test_command_add_arguments_registers_custom_args():
    """
        Test that a subclass can add custom arguments via add_arguments.
    """
    cmd = _CommandWithArguments()
    parser = ArgumentParser()

    cmd.add_arguments(parser)

    parsed = parser.parse_args(["--name", "kiro"])

    if parsed.name != "kiro":
        errmsg = "Expected parsed name 'kiro', got '{}'".format(parsed.name)
        raise AssertionError(errmsg)

    return


def test_command_add_arguments_default_values():
    """
        Test that custom arguments have correct default values.
    """
    cmd = _CommandWithArguments()
    parser = ArgumentParser()

    cmd.add_arguments(parser)

    parsed = parser.parse_args([])

    if parsed.name != "world":
        errmsg = "Expected default name 'world', got '{}'".format(parsed.name)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for execute Method
# =============================================================================

def test_command_execute_raises_not_implemented():
    """
        Test that the base CLICommand.execute raises NotImplementedError.
    """
    cmd = CLICommand()
    args = Namespace()
    config = {}

    raised = False
    try:
        cmd.execute(args, config)
    except NotImplementedError:
        raised = True

    if raised is not True:
        errmsg = "Expected NotImplementedError to be raised by base execute method."
        raise AssertionError(errmsg)

    return


def test_command_execute_returns_exit_code():
    """
        Test that a concrete command's execute method returns an integer exit code.
    """
    cmd = _ConcreteCommand()
    args = Namespace()
    config = {}

    exit_code = cmd.execute(args, config)

    if exit_code != 0:
        errmsg = "Expected exit code 0, got {}".format(exit_code)
        raise AssertionError(errmsg)

    return


def test_command_execute_receives_config():
    """
        Test that the execute method receives the config dictionary.
    """
    received_config = {}

    class _ConfigCapture(CLICommand):
        name = "config-cmd"
        help = "Captures config"

        def execute(self, args: "Namespace", config: Dict[str, Any]) -> int:
            received_config.update(config)
            return 0

    cmd = _ConfigCapture()
    args = Namespace()
    test_config = {"server": {"host": "localhost", "port": 8000}}

    cmd.execute(args, test_config)

    if received_config.get("server") is None:
        errmsg = "Expected config to contain 'server' key."
        raise AssertionError(errmsg)

    server_config = received_config["server"]
    if server_config.get("host") != "localhost":
        errmsg = "Expected server host 'localhost', got '{}'".format(server_config.get("host"))
        raise AssertionError(errmsg)

    return


def test_command_execute_receives_args():
    """
        Test that the execute method receives parsed arguments.
    """
    received_args = [None]

    class _ArgsCapture(CLICommand):
        name = "args-cmd"
        help = "Captures args"

        def execute(self, args: "Namespace", config: Dict[str, Any]) -> int:
            received_args[0] = args
            return 0

    cmd = _ArgsCapture()
    args = Namespace(verbose=True, config="test.cfg")
    config = {}

    cmd.execute(args, config)

    captured = received_args[0]
    if captured is None:
        errmsg = "Expected args to be captured, got None."
        raise AssertionError(errmsg)

    if captured.verbose is not True:
        errmsg = "Expected verbose=True, got {}".format(captured.verbose)
        raise AssertionError(errmsg)

    return
