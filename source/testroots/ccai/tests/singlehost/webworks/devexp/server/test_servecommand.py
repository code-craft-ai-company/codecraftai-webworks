"""
    Tests for the ServeCommand CLI command.

    This module contains unit tests for the ServeCommand class including
    argument parsing, default values, configuration resolution, and
    port-in-use error handling.
"""

import os
import shutil
import socket
import sys
import tempfile

from argparse import ArgumentParser, Namespace
from typing import Any, Dict

from ccai.webworks.devexp.apploader import ApplicationLoadError
from ccai.webworks.devexp.cli.exitcodes import EXIT_CONFIG_ERROR
from ccai.webworks.devexp.cli.exitcodes import EXIT_ERROR
from ccai.webworks.devexp.cli.exitcodes import EXIT_SUCCESS
from ccai.webworks.devexp.server.servecommand import ServeCommand


# =============================================================================
# Test Helpers
# =============================================================================

_APP_MODULE_SOURCE = """
async def app(scope, receive, send):
    return

not_callable = 42
"""


class _AppModule:
    """
        A temporary importable module that exposes an ASGI callable as
        'app', for commands that take an application import target.
    """

    def __init__(self, module_name):
        self.module_name = module_name
        self.directory = tempfile.mkdtemp()

        with open(os.path.join(self.directory, module_name + ".py"), "w") as module_file:
            module_file.write(_APP_MODULE_SOURCE)

        sys.path.insert(0, self.directory)

    @property
    def target(self):
        return self.module_name + ":app"

    def remove(self):
        sys.modules.pop(self.module_name, None)

        if self.directory in sys.path:
            sys.path.remove(self.directory)

        shutil.rmtree(self.directory)


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

def test_serve_command_execute_fails_without_an_application():
    """
        Test that execute does not report success when there is no
        application to serve: it returns EXIT_CONFIG_ERROR.
    """
    cmd = ServeCommand()

    args = Namespace(host="127.0.0.1", port=0, reload=False, no_debug=False)
    config: Dict[str, Any] = {}

    temp_dir = tempfile.mkdtemp()
    previous_cwd = os.getcwd()

    try:
        # A directory without app.py, so no application can be discovered.
        os.chdir(temp_dir)

        exit_code = cmd.execute(args, config)
    finally:
        os.chdir(previous_cwd)
        shutil.rmtree(temp_dir)

    if exit_code != EXIT_CONFIG_ERROR:
        errmsg = "Expected EXIT_CONFIG_ERROR ({}), got {}".format(EXIT_CONFIG_ERROR, exit_code)
        raise AssertionError(errmsg)

    return


def test_serve_command_execute_fails_for_unimportable_application():
    """
        Test that execute returns EXIT_ERROR when the application target
        cannot be imported.
    """
    cmd = ServeCommand()

    args = Namespace(
        app="serve_test_module_that_does_not_exist:app",
        host="127.0.0.1", port=0, reload=False, no_debug=False,
    )

    exit_code = cmd.execute(args, {})

    if exit_code != EXIT_ERROR:
        errmsg = "Expected EXIT_ERROR ({}), got {}".format(EXIT_ERROR, exit_code)
        raise AssertionError(errmsg)

    return


def test_create_server_imports_the_application_target():
    """
        Test that create_server imports the --app target and hands the
        application object to the server.
    """
    module = _AppModule("serve_probe_import")

    try:
        cmd = ServeCommand()
        args = Namespace(app=module.target, host="127.0.0.1", port=0, reload=False, no_debug=False)

        server = cmd.create_server(args, {})

        if not callable(server.app):
            errmsg = "Expected the server to hold the imported ASGI callable, got {!r}".format(server.app)
            raise AssertionError(errmsg)
    finally:
        module.remove()

    return


def test_create_server_uses_server_app_config_key():
    """
        Test that the application target can come from the server.app
        configuration key.
    """
    module = _AppModule("serve_probe_config")

    try:
        cmd = ServeCommand()
        args = Namespace(host="127.0.0.1", port=0, reload=False, no_debug=False)

        server = cmd.create_server(args, {"server": {"app": module.target}})

        if not callable(server.app):
            errmsg = "Expected the application from the server.app config key."
            raise AssertionError(errmsg)
    finally:
        module.remove()

    return


def test_create_server_rejects_target_that_is_not_callable():
    """
        Test that a target naming a non-callable object is rejected.
    """
    module = _AppModule("serve_probe_notcallable")

    try:
        cmd = ServeCommand()
        args = Namespace(
            app=module.module_name + ":not_callable",
            host="127.0.0.1", port=0, reload=False, no_debug=False,
        )

        raised = False
        try:
            cmd.create_server(args, {})
        except ApplicationLoadError:
            raised = True

        if raised is not True:
            errmsg = "Expected ApplicationLoadError for a target that is not callable."
            raise AssertionError(errmsg)
    finally:
        module.remove()

    return


def test_create_server_with_reload_leaves_the_import_to_the_server_process():
    """
        Test that with reload enabled the supervising process keeps the
        import target and does not import the application itself.
    """
    cmd = ServeCommand()
    args = Namespace(
        app="serve_reload_target_never_imported:app",
        host="127.0.0.1", port=0, reload=True, no_debug=False,
    )

    server = cmd.create_server(args, {})

    if server.app != "serve_reload_target_never_imported:app":
        errmsg = "Expected the import target to be kept as a string, got {!r}".format(server.app)
        raise AssertionError(errmsg)

    if "serve_reload_target_never_imported" in sys.modules:
        errmsg = "Did not expect the supervising process to import the application."
        raise AssertionError(errmsg)

    return


def test_serve_command_execute_returns_error_on_occupied_port():
    """
        Test that execute returns EXIT_ERROR when the port is occupied.
    """
    # Occupy a port the way another server does: listening on it.
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    sock.listen(1)
    occupied_port = sock.getsockname()[1]

    module = _AppModule("serve_probe_occupied")

    try:
        cmd = ServeCommand()
        args = Namespace(
            app=module.target, host="127.0.0.1", port=occupied_port, reload=False, no_debug=False
        )
        config: Dict[str, Any] = {}

        exit_code = cmd.execute(args, config)

        if exit_code != EXIT_ERROR:
            errmsg = "Expected EXIT_ERROR ({}), got {}".format(EXIT_ERROR, exit_code)
            raise AssertionError(errmsg)
    finally:
        module.remove()
        sock.close()

    return


def test_serve_command_uses_config_host_when_arg_is_none():
    """
        Test that the config host is used when --host is not provided.
    """
    module = _AppModule("serve_probe_confighost")

    try:
        cmd = ServeCommand()
        args = Namespace(app=module.target, host=None, port=0, reload=False, no_debug=False)
        config = {"server": {"host": "127.0.0.9", "port": 8000}}

        server = cmd.create_server(args, config)

        if server.host != "127.0.0.9":
            errmsg = "Expected host '127.0.0.9' from the configuration, got '{}'".format(server.host)
            raise AssertionError(errmsg)
    finally:
        module.remove()

    return


def test_serve_command_uses_config_port_when_arg_is_none():
    """
        Test that the config port is used when --port is not provided.
    """
    module = _AppModule("serve_probe_configport")

    try:
        cmd = ServeCommand()
        args = Namespace(app=module.target, host=None, port=None, reload=False, no_debug=False)
        config = {"server": {"host": "127.0.0.1", "port": 8123}}

        server = cmd.create_server(args, config)

        if server.port != 8123:
            errmsg = "Expected port 8123 from the configuration, got {}".format(server.port)
            raise AssertionError(errmsg)
    finally:
        module.remove()

    return


# =============================================================================
# Unit Tests for Debug Mode Resolution
# =============================================================================

def test_resolve_debug_follows_configuration():
    """
        Test that server.debug=False in the configuration disables debug
        mode when neither --debug nor --no-debug is given.
    """
    cmd = ServeCommand()
    args = Namespace(debug=False, no_debug=False)

    debug = cmd.resolve_debug(args, {"server": {"debug": False}}, "127.0.0.1")

    if debug is not False:
        errmsg = "Expected debug=False from the configuration, got {}".format(debug)
        raise AssertionError(errmsg)

    return


def test_resolve_debug_defaults_to_on_for_loopback():
    """
        Test that debug mode is on by default on a loopback address.
    """
    cmd = ServeCommand()
    args = Namespace(debug=False, no_debug=False)

    debug = cmd.resolve_debug(args, {"server": {"debug": True}}, "127.0.0.1")

    if debug is not True:
        errmsg = "Expected debug=True on loopback, got {}".format(debug)
        raise AssertionError(errmsg)

    return


def test_resolve_debug_no_debug_flag_wins():
    """
        Test that --no-debug disables debug mode whatever the configuration says.
    """
    cmd = ServeCommand()
    args = Namespace(debug=False, no_debug=True)

    debug = cmd.resolve_debug(args, {"server": {"debug": True}}, "127.0.0.1")

    if debug is not False:
        errmsg = "Expected debug=False with --no-debug, got {}".format(debug)
        raise AssertionError(errmsg)

    return


def test_resolve_debug_is_turned_off_on_non_loopback_address():
    """
        Test that debug mode coming from configuration is turned off when
        the server binds to an address other machines can reach.
    """
    cmd = ServeCommand()
    args = Namespace(debug=False, no_debug=False)

    debug = cmd.resolve_debug(args, {"server": {"debug": True}}, "0.0.0.0")

    if debug is not False:
        errmsg = "Expected debug to be turned off on 0.0.0.0, got {}".format(debug)
        raise AssertionError(errmsg)

    return


def test_resolve_debug_explicit_flag_is_kept_on_non_loopback_address():
    """
        Test that an explicit --debug is honoured on a non-loopback address.
    """
    cmd = ServeCommand()
    args = Namespace(debug=True, no_debug=False)

    debug = cmd.resolve_debug(args, {"server": {"debug": False}}, "0.0.0.0")

    if debug is not True:
        errmsg = "Expected debug=True with an explicit --debug, got {}".format(debug)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Logging Options
# =============================================================================

def test_serve_command_adds_log_level_and_log_file_arguments():
    """
        Test that the serve command registers --log-level and --log-file.
    """
    cmd = ServeCommand()
    parser = ArgumentParser()
    cmd.add_arguments(parser)

    parsed = parser.parse_args(["--log-level", "warning", "--log-file", "server.log"])

    if parsed.log_level != "WARNING":
        errmsg = "Expected log_level 'WARNING', got '{}'".format(parsed.log_level)
        raise AssertionError(errmsg)

    if parsed.log_file != "server.log":
        errmsg = "Expected log_file 'server.log', got '{}'".format(parsed.log_file)
        raise AssertionError(errmsg)

    return


def test_create_logger_prefers_command_line_options():
    """
        Test that --log-level and --log-file override the configuration.
    """
    cmd = ServeCommand()
    args = Namespace(log_level="ERROR", log_file="cli.log")
    config = {"logging": {"level": "DEBUG", "file": "config.log"}}

    dev_logger = cmd.create_logger(args, config, debug=True)

    if dev_logger.log_level != "ERROR":
        errmsg = "Expected log level 'ERROR', got '{}'".format(dev_logger.log_level)
        raise AssertionError(errmsg)

    if dev_logger.log_file != "cli.log":
        errmsg = "Expected log file 'cli.log', got '{}'".format(dev_logger.log_file)
        raise AssertionError(errmsg)

    return


