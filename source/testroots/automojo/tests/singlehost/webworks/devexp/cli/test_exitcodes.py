"""
    Tests for the exit codes module and CLI exit code handling.

    This module contains unit tests for the exit code constants defined
    in the exitcodes module and for the exit code behavior of the
    :class:`WebworksCLI` run method, including exception handling for
    configuration errors and unhandled command exceptions.
"""

from argparse import ArgumentParser, Namespace
from typing import Any, Dict

from automojo.webworks.devexp.cli.command import CLICommand
from automojo.webworks.devexp.cli.exitcodes import EXIT_CONFIG_ERROR
from automojo.webworks.devexp.cli.exitcodes import EXIT_ERROR
from automojo.webworks.devexp.cli.exitcodes import EXIT_NOT_FOUND
from automojo.webworks.devexp.cli.exitcodes import EXIT_SUCCESS
from automojo.webworks.devexp.cli.exitcodes import EXIT_USAGE_ERROR
from automojo.webworks.devexp.cli.webworkscli import WebworksCLI


# =============================================================================
# Test Helpers
# =============================================================================

class _SuccessCommand(CLICommand):
    """
        A command that returns EXIT_SUCCESS for testing.
    """

    name = "succeed"
    help = "A command that succeeds"

    def execute(self, args: "Namespace", config: Dict[str, Any]) -> int:
        """
            Execute the command and return success.

            :param args: Parsed command-line arguments.
            :param config: Loaded configuration dictionary.

            :returns: EXIT_SUCCESS exit code.
        """
        return EXIT_SUCCESS


class _ExplodingCommand(CLICommand):
    """
        A command that raises an unhandled exception for testing.
    """

    name = "explode"
    help = "A command that raises an exception"

    def execute(self, args: "Namespace", config: Dict[str, Any]) -> int:
        """
            Execute the command and raise a RuntimeError.

            :param args: Parsed command-line arguments.
            :param config: Loaded configuration dictionary.

            :raises RuntimeError: Always raised to simulate an unhandled error.
        """
        raise RuntimeError("Something went wrong")


class _TypeErrorCommand(CLICommand):
    """
        A command that raises a TypeError for testing.
    """

    name = "typeerr"
    help = "A command that raises a TypeError"

    def execute(self, args: "Namespace", config: Dict[str, Any]) -> int:
        """
            Execute the command and raise a TypeError.

            :param args: Parsed command-line arguments.
            :param config: Loaded configuration dictionary.

            :raises TypeError: Always raised to simulate a type error.
        """
        raise TypeError("Bad type encountered")


# =============================================================================
# Unit Tests for Exit Code Constants
# =============================================================================

def test_exit_success_is_zero():
    """
        Test that EXIT_SUCCESS is defined as 0.
    """
    if EXIT_SUCCESS != 0:
        errmsg = "Expected EXIT_SUCCESS to be 0, got {}".format(EXIT_SUCCESS)
        raise AssertionError(errmsg)

    return


def test_exit_error_is_one():
    """
        Test that EXIT_ERROR is defined as 1.
    """
    if EXIT_ERROR != 1:
        errmsg = "Expected EXIT_ERROR to be 1, got {}".format(EXIT_ERROR)
        raise AssertionError(errmsg)

    return


def test_exit_usage_error_is_two():
    """
        Test that EXIT_USAGE_ERROR is defined as 2.
    """
    if EXIT_USAGE_ERROR != 2:
        errmsg = "Expected EXIT_USAGE_ERROR to be 2, got {}".format(EXIT_USAGE_ERROR)
        raise AssertionError(errmsg)

    return


def test_exit_config_error_is_three():
    """
        Test that EXIT_CONFIG_ERROR is defined as 3.
    """
    if EXIT_CONFIG_ERROR != 3:
        errmsg = "Expected EXIT_CONFIG_ERROR to be 3, got {}".format(EXIT_CONFIG_ERROR)
        raise AssertionError(errmsg)

    return


def test_exit_not_found_is_four():
    """
        Test that EXIT_NOT_FOUND is defined as 4.
    """
    if EXIT_NOT_FOUND != 4:
        errmsg = "Expected EXIT_NOT_FOUND to be 4, got {}".format(EXIT_NOT_FOUND)
        raise AssertionError(errmsg)

    return


def test_exit_codes_are_integers():
    """
        Test that all exit codes are integer values.
    """
    codes = [EXIT_SUCCESS, EXIT_ERROR, EXIT_USAGE_ERROR, EXIT_CONFIG_ERROR, EXIT_NOT_FOUND]

    for code in codes:
        if not isinstance(code, int):
            errmsg = "Expected exit code to be int, got {} for value {}".format(type(code).__name__, code)
            raise AssertionError(errmsg)

    return


def test_exit_codes_are_unique():
    """
        Test that all exit codes have distinct values.
    """
    codes = [EXIT_SUCCESS, EXIT_ERROR, EXIT_USAGE_ERROR, EXIT_CONFIG_ERROR, EXIT_NOT_FOUND]
    unique_codes = set(codes)

    if len(unique_codes) != len(codes):
        errmsg = "Expected all exit codes to be unique, got {} unique out of {}".format(
            len(unique_codes), len(codes)
        )
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for CLI Exit Code Behavior
# =============================================================================

def test_cli_run_returns_exit_success_on_successful_command():
    """
        Test that run returns EXIT_SUCCESS when a command completes
        successfully with exit code 0.
    """
    cli = WebworksCLI()
    cmd = _SuccessCommand()
    cli.register_command(cmd)

    exit_code = cli.run(["succeed"])

    if exit_code != EXIT_SUCCESS:
        errmsg = "Expected EXIT_SUCCESS ({}), got {}".format(EXIT_SUCCESS, exit_code)
        raise AssertionError(errmsg)

    return


def test_cli_run_returns_exit_usage_error_when_no_command():
    """
        Test that run returns EXIT_USAGE_ERROR when no command is specified.
    """
    cli = WebworksCLI()
    cmd = _SuccessCommand()
    cli.register_command(cmd)

    exit_code = cli.run([])

    if exit_code != EXIT_USAGE_ERROR:
        errmsg = "Expected EXIT_USAGE_ERROR ({}), got {}".format(EXIT_USAGE_ERROR, exit_code)
        raise AssertionError(errmsg)

    return


def test_cli_run_returns_exit_error_on_unhandled_exception():
    """
        Test that run returns EXIT_ERROR when a command raises an
        unhandled exception.
    """
    cli = WebworksCLI()
    cmd = _ExplodingCommand()
    cli.register_command(cmd)

    exit_code = cli.run(["explode"])

    if exit_code != EXIT_ERROR:
        errmsg = "Expected EXIT_ERROR ({}), got {}".format(EXIT_ERROR, exit_code)
        raise AssertionError(errmsg)

    return


def test_cli_run_returns_exit_error_on_type_error():
    """
        Test that run returns EXIT_ERROR when a command raises a
        TypeError during execution.
    """
    cli = WebworksCLI()
    cmd = _TypeErrorCommand()
    cli.register_command(cmd)

    exit_code = cli.run(["typeerr"])

    if exit_code != EXIT_ERROR:
        errmsg = "Expected EXIT_ERROR ({}), got {}".format(EXIT_ERROR, exit_code)
        raise AssertionError(errmsg)

    return


def test_cli_run_returns_exit_config_error_on_config_failure():
    """
        Test that run returns EXIT_CONFIG_ERROR when configuration
        loading raises an exception.
    """
    import automojo.webworks.devexp.cli.webworkscli as cli_module
    from automojo.testbase.mocking import create_module_patch

    def _failing_load_config(config_path=None):
        """
            A replacement for load_config that always raises an exception.
        """
        raise ValueError("Invalid configuration format")

    patch = create_module_patch(cli_module, "load_config")
    mock = patch.activate()
    mock.configure(side_effect=_failing_load_config)

    try:
        cli = WebworksCLI()
        cmd = _SuccessCommand()
        cli.register_command(cmd)

        exit_code = cli.run(["succeed"])

        if exit_code != EXIT_CONFIG_ERROR:
            errmsg = "Expected EXIT_CONFIG_ERROR ({}), got {}".format(EXIT_CONFIG_ERROR, exit_code)
            raise AssertionError(errmsg)
    finally:
        patch.deactivate()

    return


def test_cli_run_does_not_propagate_command_exception():
    """
        Test that run catches command exceptions and does not let
        them propagate to the caller.
    """
    cli = WebworksCLI()
    cmd = _ExplodingCommand()
    cli.register_command(cmd)

    exception_raised = False

    try:
        cli.run(["explode"])
    except RuntimeError:
        exception_raised = True

    if exception_raised is True:
        errmsg = "Expected run to catch the RuntimeError, but it propagated."
        raise AssertionError(errmsg)

    return


# =============================================================================
# Property-Based Test for CLI Exit Code Consistency
# =============================================================================
#
# **Validates: Requirements 1.8**
#
# Property 4: CLI Exit Code Consistency
# For any CLI command execution, the exit code SHALL be 0 if and only if
# the command completed successfully without errors.
# =============================================================================

import random


class _RandomExitCodeCommand(CLICommand):
    """
        A command that returns a configurable exit code for property testing.
    """

    name = "random-exit"
    help = "A command that returns a configurable exit code"

    def __init__(self, exit_code: int):
        """
            Initialize with the exit code to return.

            :param exit_code: The exit code this command will return.
        """
        super().__init__()
        self._exit_code = exit_code
        return

    def execute(self, args: "Namespace", config: Dict[str, Any]) -> int:
        """
            Execute the command and return the configured exit code.

            :param args: Parsed command-line arguments.
            :param config: Loaded configuration dictionary.

            :returns: The configured exit code.
        """
        return self._exit_code


class _RandomExceptionCommand(CLICommand):
    """
        A command that raises a randomly selected exception for property testing.
    """

    name = "random-exception"
    help = "A command that raises a random exception"

    _EXCEPTION_TYPES = [
        RuntimeError,
        ValueError,
        TypeError,
        KeyError,
        IOError,
        AttributeError,
        IndexError,
        OSError,
    ]

    def __init__(self, exception_index: int):
        """
            Initialize with the index of the exception type to raise.

            :param exception_index: Index into the exception types list.
        """
        super().__init__()
        self._exception_index = exception_index % len(self._EXCEPTION_TYPES)
        return

    def execute(self, args: "Namespace", config: Dict[str, Any]) -> int:
        """
            Execute the command and raise the selected exception.

            :param args: Parsed command-line arguments.
            :param config: Loaded configuration dictionary.

            :raises Exception: Always raises the configured exception type.
        """
        exc_type = self._EXCEPTION_TYPES[self._exception_index]
        raise exc_type("Randomly generated error for property testing")


def test_property_exit_code_consistency_success_returns_zero():
    """
        **Validates: Requirements 1.8**

        Property test: when a command completes successfully by returning
        EXIT_SUCCESS (0), the CLI run method SHALL return exit code 0.

        This test generates 100 random iterations where a command returns
        EXIT_SUCCESS and verifies the CLI always returns 0.
    """
    rng = random.Random(42)

    for iteration in range(100):
        cli = WebworksCLI()
        cmd = _RandomExitCodeCommand(EXIT_SUCCESS)
        cmd.name = "success-{}".format(iteration)
        cli.register_command(cmd)

        exit_code = cli.run([cmd.name])

        if exit_code != EXIT_SUCCESS:
            errmsg = (
                "Iteration {}: Expected EXIT_SUCCESS (0) for successful command, "
                "got {}".format(iteration, exit_code)
            )
            raise AssertionError(errmsg)

        if not isinstance(exit_code, int):
            errmsg = (
                "Iteration {}: Expected exit code to be int, got {}".format(
                    iteration, type(exit_code).__name__
                )
            )
            raise AssertionError(errmsg)

    return


def test_property_exit_code_consistency_exception_returns_nonzero():
    """
        **Validates: Requirements 1.8**

        Property test: when a command raises any exception, the CLI run
        method SHALL return a non-zero exit code.

        This test generates 100 random iterations with different exception
        types and verifies the CLI always returns a non-zero integer exit code.
    """
    rng = random.Random(42)

    for iteration in range(100):
        exception_index = rng.randint(0, 7)

        cli = WebworksCLI()
        cmd = _RandomExceptionCommand(exception_index)
        cmd.name = "exception-{}".format(iteration)
        cli.register_command(cmd)

        exit_code = cli.run([cmd.name])

        if exit_code == EXIT_SUCCESS:
            errmsg = (
                "Iteration {}: Expected non-zero exit code for command that raised "
                "{}, got EXIT_SUCCESS (0)".format(
                    iteration,
                    _RandomExceptionCommand._EXCEPTION_TYPES[exception_index % 8].__name__
                )
            )
            raise AssertionError(errmsg)

        if not isinstance(exit_code, int):
            errmsg = (
                "Iteration {}: Expected exit code to be int, got {}".format(
                    iteration, type(exit_code).__name__
                )
            )
            raise AssertionError(errmsg)

    return


def test_property_exit_code_consistency_nonzero_return_is_nonzero():
    """
        **Validates: Requirements 1.8**

        Property test: when a command returns a non-zero exit code
        (indicating failure), the CLI run method SHALL propagate that
        non-zero exit code.

        This test generates 100 random non-zero exit codes and verifies
        the CLI returns the exact same non-zero value.
    """
    rng = random.Random(42)

    non_zero_codes = [EXIT_ERROR, EXIT_USAGE_ERROR, EXIT_CONFIG_ERROR, EXIT_NOT_FOUND]

    for iteration in range(100):
        chosen_code = rng.choice(non_zero_codes)

        cli = WebworksCLI()
        cmd = _RandomExitCodeCommand(chosen_code)
        cmd.name = "nonzero-{}".format(iteration)
        cli.register_command(cmd)

        exit_code = cli.run([cmd.name])

        if exit_code != chosen_code:
            errmsg = (
                "Iteration {}: Expected exit code {}, got {}".format(
                    iteration, chosen_code, exit_code
                )
            )
            raise AssertionError(errmsg)

        if exit_code == EXIT_SUCCESS:
            errmsg = (
                "Iteration {}: Command returned non-zero code {} but CLI "
                "returned EXIT_SUCCESS (0)".format(iteration, chosen_code)
            )
            raise AssertionError(errmsg)

        if not isinstance(exit_code, int):
            errmsg = (
                "Iteration {}: Expected exit code to be int, got {}".format(
                    iteration, type(exit_code).__name__
                )
            )
            raise AssertionError(errmsg)

    return


def test_property_exit_code_consistency_bidirectional():
    """
        **Validates: Requirements 1.8**

        Property test: the exit code SHALL be 0 if and only if the command
        completed successfully. This verifies the bidirectional property
        by randomly generating both successful and failing command scenarios
        and checking that exit code 0 corresponds exactly to success.

        This test generates 100 random iterations mixing successful commands,
        failing commands (non-zero return), and exception-raising commands.
    """
    rng = random.Random(42)

    non_zero_codes = [EXIT_ERROR, EXIT_USAGE_ERROR, EXIT_CONFIG_ERROR, EXIT_NOT_FOUND]

    for iteration in range(100):
        scenario = rng.choice(["success", "nonzero_return", "exception"])

        cli = WebworksCLI()

        if scenario == "success":
            cmd = _RandomExitCodeCommand(EXIT_SUCCESS)
            cmd.name = "bidir-{}".format(iteration)
            cli.register_command(cmd)
            expected_success = True

        elif scenario == "nonzero_return":
            chosen_code = rng.choice(non_zero_codes)
            cmd = _RandomExitCodeCommand(chosen_code)
            cmd.name = "bidir-{}".format(iteration)
            cli.register_command(cmd)
            expected_success = False

        else:
            exception_index = rng.randint(0, 7)
            cmd = _RandomExceptionCommand(exception_index)
            cmd.name = "bidir-{}".format(iteration)
            cli.register_command(cmd)
            expected_success = False

        exit_code = cli.run([cmd.name])

        if not isinstance(exit_code, int):
            errmsg = (
                "Iteration {} ({}): Expected exit code to be int, got {}".format(
                    iteration, scenario, type(exit_code).__name__
                )
            )
            raise AssertionError(errmsg)

        is_zero = (exit_code == 0)

        if expected_success and not is_zero:
            errmsg = (
                "Iteration {} ({}): Command succeeded but exit code was {} "
                "instead of 0".format(iteration, scenario, exit_code)
            )
            raise AssertionError(errmsg)

        if not expected_success and is_zero:
            errmsg = (
                "Iteration {} ({}): Command failed but exit code was 0 "
                "instead of non-zero".format(iteration, scenario)
            )
            raise AssertionError(errmsg)

    return

