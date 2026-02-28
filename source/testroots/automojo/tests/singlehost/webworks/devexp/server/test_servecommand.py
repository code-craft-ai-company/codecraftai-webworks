"""
    Tests for the ServeCommand CLI command.

    This module contains unit tests for the ServeCommand class including
    argument parsing, default values, configuration resolution, and
    port-in-use error handling.
"""

import socket

from argparse import ArgumentParser, Namespace
from typing import Any, Dict

from automojo.webworks.devexp.cli.exitcodes import EXIT_ERROR
from automojo.webworks.devexp.cli.exitcodes import EXIT_SUCCESS
from automojo.webworks.devexp.server.servecommand import ServeCommand


# =============================================================================
# Unit Tests for ServeCommand Metadata
# =============================================================================

def test_serve_command_name():
    """
        Test that the serve command has the correct name.
    """
    cmd = ServeCommand()

    if cmd.name != "serve":
        errmsg = "Expected name 'serve', got '{}'".format(cmd.name)
        raise AssertionError(errmsg)

    return


def test_serve_command_help():
    """
        Test that the serve command has non-empty help text.
    """
    cmd = ServeCommand()

    if not cmd.help:
        errmsg = "Expected non-empty help text."
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Argument Parsing
# =============================================================================

def test_serve_command_adds_host_argument():
    """
        Test that the serve command registers a --host argument.
    """
    cmd = ServeCommand()
    parser = ArgumentParser()
    cmd.add_arguments(parser)

    parsed = parser.parse_args(["--host", "0.0.0.0"])

    if parsed.host != "0.0.0.0":
        errmsg = "Expected host '0.0.0.0', got '{}'".format(parsed.host)
        raise AssertionError(errmsg)

    return


def test_serve_command_adds_port_argument():
    """
        Test that the serve command registers a --port argument.
    """
    cmd = ServeCommand()
    parser = ArgumentParser()
    cmd.add_arguments(parser)

    parsed = parser.parse_args(["--port", "9000"])

    if parsed.port != 9000:
        errmsg = "Expected port 9000, got {}".format(parsed.port)
        raise AssertionError(errmsg)

    return


def test_serve_command_adds_reload_argument():
    """
        Test that the serve command registers a --reload argument.
    """
    cmd = ServeCommand()
    parser = ArgumentParser()
    cmd.add_arguments(parser)

    parsed = parser.parse_args(["--reload"])

    if parsed.reload is not True:
        errmsg = "Expected reload=True, got {}".format(parsed.reload)
        raise AssertionError(errmsg)

    return


def test_serve_command_adds_no_debug_argument():
    """
        Test that the serve command registers a --no-debug argument.
    """
    cmd = ServeCommand()
    parser = ArgumentParser()
    cmd.add_arguments(parser)

    parsed = parser.parse_args(["--no-debug"])

    if parsed.no_debug is not True:
        errmsg = "Expected no_debug=True, got {}".format(parsed.no_debug)
        raise AssertionError(errmsg)

    return


def test_serve_command_default_host_is_none():
    """
        Test that the default host argument is None (resolved from config).
    """
    cmd = ServeCommand()
    parser = ArgumentParser()
    cmd.add_arguments(parser)

    parsed = parser.parse_args([])

    if parsed.host is not None:
        errmsg = "Expected default host None, got '{}'".format(parsed.host)
        raise AssertionError(errmsg)

    return


def test_serve_command_default_port_is_none():
    """
        Test that the default port argument is None (resolved from config).
    """
    cmd = ServeCommand()
    parser = ArgumentParser()
    cmd.add_arguments(parser)

    parsed = parser.parse_args([])

    if parsed.port is not None:
        errmsg = "Expected default port None, got {}".format(parsed.port)
        raise AssertionError(errmsg)

    return


def test_serve_command_default_reload_is_false():
    """
        Test that the default reload argument is False.
    """
    cmd = ServeCommand()
    parser = ArgumentParser()
    cmd.add_arguments(parser)

    parsed = parser.parse_args([])

    if parsed.reload is not False:
        errmsg = "Expected default reload=False, got {}".format(parsed.reload)
        raise AssertionError(errmsg)

    return


def test_serve_command_default_no_debug_is_false():
    """
        Test that the default no_debug argument is False.
    """
    cmd = ServeCommand()
    parser = ArgumentParser()
    cmd.add_arguments(parser)

    parsed = parser.parse_args([])

    if parsed.no_debug is not False:
        errmsg = "Expected default no_debug=False, got {}".format(parsed.no_debug)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Execute
# =============================================================================

def test_serve_command_execute_returns_success_on_free_port():
    """
        Test that execute returns EXIT_SUCCESS when the port is free.
    """
    cmd = ServeCommand()

    # Use port 0 to let the OS assign a free port
    args = Namespace(host="127.0.0.1", port=0, reload=False, no_debug=False)
    config: Dict[str, Any] = {}

    exit_code = cmd.execute(args, config)

    if exit_code != EXIT_SUCCESS:
        errmsg = "Expected EXIT_SUCCESS ({}), got {}".format(EXIT_SUCCESS, exit_code)
        raise AssertionError(errmsg)

    return


def test_serve_command_execute_returns_error_on_occupied_port():
    """
        Test that execute returns EXIT_ERROR when the port is occupied.
    """
    # Occupy a port
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", 0))
    occupied_port = sock.getsockname()[1]

    try:
        cmd = ServeCommand()
        args = Namespace(
            host="127.0.0.1", port=occupied_port, reload=False, no_debug=False
        )
        config: Dict[str, Any] = {}

        exit_code = cmd.execute(args, config)

        if exit_code != EXIT_ERROR:
            errmsg = "Expected EXIT_ERROR ({}), got {}".format(EXIT_ERROR, exit_code)
            raise AssertionError(errmsg)
    finally:
        sock.close()

    return


def test_serve_command_uses_config_host_when_arg_is_none():
    """
        Test that execute uses the config host when --host is not provided.
    """
    cmd = ServeCommand()
    args = Namespace(host=None, port=0, reload=False, no_debug=False)
    config = {"server": {"host": "0.0.0.0", "port": 8000}}

    # This should succeed because port 0 is always free
    exit_code = cmd.execute(args, config)

    if exit_code != EXIT_SUCCESS:
        errmsg = "Expected EXIT_SUCCESS, got {}".format(exit_code)
        raise AssertionError(errmsg)

    return


def test_serve_command_uses_config_port_when_arg_is_none():
    """
        Test that execute uses the config port when --port is not provided.
    """
    # Occupy the config port to verify it's being used
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", 0))
    occupied_port = sock.getsockname()[1]

    try:
        cmd = ServeCommand()
        args = Namespace(host=None, port=None, reload=False, no_debug=False)
        config = {"server": {"host": "127.0.0.1", "port": occupied_port}}

        exit_code = cmd.execute(args, config)

        # Should fail because the config port is occupied
        if exit_code != EXIT_ERROR:
            errmsg = "Expected EXIT_ERROR when config port is occupied, got {}".format(
                exit_code
            )
            raise AssertionError(errmsg)
    finally:
        sock.close()

    return
