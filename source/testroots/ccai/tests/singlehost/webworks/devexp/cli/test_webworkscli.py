"""
    Tests for the WebworksCLI main entry point class.

    This module contains unit tests for the WebworksCLI class including
    construction, command registration, group registration, argument
    parsing with global options, and command dispatch.
"""

from argparse import ArgumentParser, Namespace
from typing import Any, Dict

from ccai.webworks.devexp.cli.command import CLICommand
from ccai.webworks.devexp.cli.group import CLIGroup
from ccai.webworks.devexp.cli.webworkscli import WebworksCLI


# =============================================================================
# Test Helpers
# =============================================================================

class _HelloCommand(CLICommand):
    """
        A concrete command that records execution for testing.
    """

    name = "hello"
    help = "Say hello"

    def __init__(self):
        """
            Initialize the hello command with execution tracking.
        """
        self.executed = False
        self.received_args = None
        self.received_config = None
        self.exit_code = 0
        return

    def execute(self, args: "Namespace", config: Dict[str, Any]) -> int:
        """
            Execute the hello command and record the call.

            :param args: Parsed command-line arguments.
            :param config: Loaded configuration dictionary.

            :returns: The configured exit code.
        """
        self.executed = True
        self.received_args = args
        self.received_config = config
        return self.exit_code


class _GreetCommand(CLICommand):
    """
        A command with a custom --name argument for testing.
    """

    name = "greet"
    help = "Greet someone"

    def __init__(self):
        """
            Initialize the greet command with execution tracking.
        """
        self.executed = False
        self.received_args = None
        return

    def add_arguments(self, parser: "ArgumentParser") -> None:
        """
            Add a --name argument to the parser.

            :param parser: The argument parser to add arguments to.
        """
        parser.add_argument("--name", type=str, default="world")
        return

    def execute(self, args: "Namespace", config: Dict[str, Any]) -> int:
        """
            Execute the greet command and record the call.

            :param args: Parsed command-line arguments.
            :param config: Loaded configuration dictionary.

            :returns: Exit code 0 for success.
        """
        self.executed = True
        self.received_args = args
        return 0


class _FailCommand(CLICommand):
    """
        A command that returns a non-zero exit code for testing.
    """

    name = "fail"
    help = "A command that fails"

    def execute(self, args: "Namespace", config: Dict[str, Any]) -> int:
        """
            Execute the fail command.

            :param args: Parsed command-line arguments.
            :param config: Loaded configuration dictionary.

            :returns: Exit code 1 for failure.
        """
        return 1


class _StartCommand(CLICommand):
    """
        A concrete command for testing group registration.
    """

    name = "start"
    help = "Start the server"

    def __init__(self):
        """
            Initialize the start command with execution tracking.
        """
        self.executed = False
        self.received_args = None
        return

    def add_arguments(self, parser: "ArgumentParser") -> None:
        """
            Add --port argument to the parser.

            :param parser: The argument parser to add arguments to.
        """
        parser.add_argument("--port", type=int, default=8000)
        return

    def execute(self, args: "Namespace", config: Dict[str, Any]) -> int:
        """
            Execute the start command and record the call.

            :param args: Parsed command-line arguments.
            :param config: Loaded configuration dictionary.

            :returns: Exit code 0 for success.
        """
        self.executed = True
        self.received_args = args
        return 0


class _StopCommand(CLICommand):
    """
        A concrete command for testing group registration.
    """

    name = "stop"
    help = "Stop the server"

    def __init__(self):
        """
            Initialize the stop command with execution tracking.
        """
        self.executed = False
        return

    def execute(self, args: "Namespace", config: Dict[str, Any]) -> int:
        """
            Execute the stop command and record the call.

            :param args: Parsed command-line arguments.
            :param config: Loaded configuration dictionary.

            :returns: Exit code 0 for success.
        """
        self.executed = True
        return 0


# =============================================================================
# Unit Tests for WebworksCLI Construction
# =============================================================================

def test_cli_default_config_path_is_none():
    """
        Test that a WebworksCLI created with no arguments has None config_path.
    """
    cli = WebworksCLI()

    if cli.config_path is not None:
        errmsg = "Expected config_path to be None, got '{}'".format(cli.config_path)
        raise AssertionError(errmsg)

    return


def test_cli_constructor_sets_config_path():
    """
        Test that the config_path parameter is stored correctly.
    """
    cli = WebworksCLI(config_path="/etc/webworks.cfg")

    if cli.config_path != "/etc/webworks.cfg":
        errmsg = "Expected config_path '/etc/webworks.cfg', got '{}'".format(cli.config_path)
        raise AssertionError(errmsg)

    return


def test_cli_default_config_is_empty_dict():
    """
        Test that a new WebworksCLI has an empty config dictionary.
    """
    cli = WebworksCLI()

    if len(cli.config) != 0:
        errmsg = "Expected empty config dict, got {} entries".format(len(cli.config))
        raise AssertionError(errmsg)

    return


def test_cli_default_commands_is_empty():
    """
        Test that a new WebworksCLI has no registered commands.
    """
    cli = WebworksCLI()

    if len(cli.commands) != 0:
        errmsg = "Expected empty commands dict, got {} entries".format(len(cli.commands))
        raise AssertionError(errmsg)

    return


def test_cli_default_groups_is_empty():
    """
        Test that a new WebworksCLI has no registered groups.
    """
    cli = WebworksCLI()

    if len(cli.groups) != 0:
        errmsg = "Expected empty groups dict, got {} entries".format(len(cli.groups))
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Command Registration
# =============================================================================

def test_cli_register_command_adds_command():
    """
        Test that register_command adds a command to the CLI.
    """
    cli = WebworksCLI()
    cmd = _HelloCommand()

    cli.register_command(cmd)

    commands = cli.commands
    if len(commands) != 1:
        errmsg = "Expected 1 command, got {}".format(len(commands))
        raise AssertionError(errmsg)

    return


def test_cli_register_command_stores_by_name():
    """
        Test that the command is stored under its name key.
    """
    cli = WebworksCLI()
    cmd = _HelloCommand()

    cli.register_command(cmd)

    commands = cli.commands
    if "hello" not in commands:
        errmsg = "Expected 'hello' key in commands dict."
        raise AssertionError(errmsg)

    return


def test_cli_register_multiple_commands():
    """
        Test that multiple commands can be registered.
    """
    cli = WebworksCLI()
    hello_cmd = _HelloCommand()
    greet_cmd = _GreetCommand()

    cli.register_command(hello_cmd)
    cli.register_command(greet_cmd)

    commands = cli.commands
    if len(commands) != 2:
        errmsg = "Expected 2 commands, got {}".format(len(commands))
        raise AssertionError(errmsg)

    if "hello" not in commands:
        errmsg = "Expected 'hello' key in commands dict."
        raise AssertionError(errmsg)

    if "greet" not in commands:
        errmsg = "Expected 'greet' key in commands dict."
        raise AssertionError(errmsg)

    return


def test_cli_commands_returns_copy():
    """
        Test that the commands property returns a copy of the internal dict.
    """
    cli = WebworksCLI()
    cmd = _HelloCommand()
    cli.register_command(cmd)

    commands_a = cli.commands
    commands_b = cli.commands

    if commands_a is commands_b:
        errmsg = "Expected commands property to return a new dict each time."
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Group Registration
# =============================================================================

def test_cli_register_group_adds_group():
    """
        Test that register_group adds a group to the CLI.
    """
    cli = WebworksCLI()
    group = CLIGroup(name="server", help="Server commands")

    cli.register_group(group)

    groups = cli.groups
    if len(groups) != 1:
        errmsg = "Expected 1 group, got {}".format(len(groups))
        raise AssertionError(errmsg)

    return


def test_cli_register_group_stores_by_name():
    """
        Test that the group is stored under its name key.
    """
    cli = WebworksCLI()
    group = CLIGroup(name="server", help="Server commands")

    cli.register_group(group)

    groups = cli.groups
    if "server" not in groups:
        errmsg = "Expected 'server' key in groups dict."
        raise AssertionError(errmsg)

    return


def test_cli_register_multiple_groups():
    """
        Test that multiple groups can be registered.
    """
    cli = WebworksCLI()
    server_group = CLIGroup(name="server", help="Server commands")
    db_group = CLIGroup(name="db", help="Database commands")

    cli.register_group(server_group)
    cli.register_group(db_group)

    groups = cli.groups
    if len(groups) != 2:
        errmsg = "Expected 2 groups, got {}".format(len(groups))
        raise AssertionError(errmsg)

    return


def test_cli_groups_returns_copy():
    """
        Test that the groups property returns a copy of the internal dict.
    """
    cli = WebworksCLI()
    group = CLIGroup(name="server", help="Server commands")
    cli.register_group(group)

    groups_a = cli.groups
    groups_b = cli.groups

    if groups_a is groups_b:
        errmsg = "Expected groups property to return a new dict each time."
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for run Method - Command Dispatch
# =============================================================================

def test_cli_run_dispatches_to_command():
    """
        Test that run dispatches execution to the correct command.
    """
    cli = WebworksCLI()
    cmd = _HelloCommand()
    cli.register_command(cmd)

    cli.run(["hello"])

    if cmd.executed is not True:
        errmsg = "Expected hello command to be executed."
        raise AssertionError(errmsg)

    return


def test_cli_run_returns_command_exit_code():
    """
        Test that run returns the exit code from the command.
    """
    cli = WebworksCLI()
    cmd = _HelloCommand()
    cmd.exit_code = 0
    cli.register_command(cmd)

    exit_code = cli.run(["hello"])

    if exit_code != 0:
        errmsg = "Expected exit code 0, got {}".format(exit_code)
        raise AssertionError(errmsg)

    return


def test_cli_run_returns_nonzero_exit_code():
    """
        Test that run returns a non-zero exit code from a failing command.
    """
    cli = WebworksCLI()
    cmd = _FailCommand()
    cli.register_command(cmd)

    exit_code = cli.run(["fail"])

    if exit_code != 1:
        errmsg = "Expected exit code 1, got {}".format(exit_code)
        raise AssertionError(errmsg)

    return


def test_cli_run_passes_config_to_command():
    """
        Test that run passes the CLI config to the command's execute method.
    """
    cli = WebworksCLI()
    cmd = _HelloCommand()
    cli.register_command(cmd)

    cli.run(["hello"])

    if cmd.received_config is None:
        errmsg = "Expected config to be passed to command, got None."
        raise AssertionError(errmsg)

    return


def test_cli_run_no_command_returns_usage_error():
    """
        Test that run returns exit code 2 when no command is specified.
    """
    cli = WebworksCLI()
    cmd = _HelloCommand()
    cli.register_command(cmd)

    exit_code = cli.run([])

    if exit_code != 2:
        errmsg = "Expected exit code 2 for no command, got {}".format(exit_code)
        raise AssertionError(errmsg)

    return


def test_cli_run_dispatches_correct_command():
    """
        Test that run dispatches to the correct command when multiple are registered.
    """
    cli = WebworksCLI()
    hello_cmd = _HelloCommand()
    greet_cmd = _GreetCommand()
    cli.register_command(hello_cmd)
    cli.register_command(greet_cmd)

    cli.run(["greet"])

    if hello_cmd.executed is True:
        errmsg = "Expected hello command to NOT be executed."
        raise AssertionError(errmsg)

    if greet_cmd.executed is not True:
        errmsg = "Expected greet command to be executed."
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for run Method - Global Options
# =============================================================================

def test_cli_run_parses_verbose_flag():
    """
        Test that the --verbose global option is parsed and available.
    """
    cli = WebworksCLI()
    cmd = _HelloCommand()
    cli.register_command(cmd)

    cli.run(["--verbose", "hello"])

    verbose = getattr(cmd.received_args, "verbose", None)
    if verbose is not True:
        errmsg = "Expected verbose=True, got {}".format(verbose)
        raise AssertionError(errmsg)

    return


def test_cli_run_verbose_defaults_to_false():
    """
        Test that verbose defaults to False when not specified.
    """
    cli = WebworksCLI()
    cmd = _HelloCommand()
    cli.register_command(cmd)

    cli.run(["hello"])

    verbose = getattr(cmd.received_args, "verbose", None)
    if verbose is not False:
        errmsg = "Expected verbose=False, got {}".format(verbose)
        raise AssertionError(errmsg)

    return


def test_cli_run_parses_config_option():
    """
        Test that the --config global option is parsed and available.
    """
    import json
    import os
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
        json.dump({"server": {"port": 9123}}, tmp)
        config_path = tmp.name

    try:
        cli = WebworksCLI()
        cmd = _HelloCommand()
        cli.register_command(cmd)

        cli.run(["--config", config_path, "hello"])

        config_val = getattr(cmd.received_args, "config", None)
        if config_val != config_path:
            errmsg = "Expected config '{}', got '{}'".format(config_path, config_val)
            raise AssertionError(errmsg)

        if cli.config["server"]["port"] != 9123:
            errmsg = "Expected the port from the config file, got {}".format(cli.config["server"]["port"])
            raise AssertionError(errmsg)
    finally:
        os.unlink(config_path)

    return


def test_cli_run_config_defaults_to_none():
    """
        Test that config defaults to None when not specified.
    """
    cli = WebworksCLI()
    cmd = _HelloCommand()
    cli.register_command(cmd)

    cli.run(["hello"])

    config_val = getattr(cmd.received_args, "config", None)
    if config_val is not None:
        errmsg = "Expected config=None, got '{}'".format(config_val)
        raise AssertionError(errmsg)

    return


def test_cli_run_parses_env_option():
    """
        Test that the --env global option is parsed and available.
    """
    cli = WebworksCLI()
    cmd = _HelloCommand()
    cli.register_command(cmd)

    cli.run(["--env", "production", "hello"])

    env_val = getattr(cmd.received_args, "env", None)
    if env_val != "production":
        errmsg = "Expected env 'production', got '{}'".format(env_val)
        raise AssertionError(errmsg)

    return


def test_cli_run_env_defaults_to_none():
    """
        Test that env defaults to None when not specified.
    """
    cli = WebworksCLI()
    cmd = _HelloCommand()
    cli.register_command(cmd)

    cli.run(["hello"])

    env_val = getattr(cmd.received_args, "env", None)
    if env_val is not None:
        errmsg = "Expected env=None, got '{}'".format(env_val)
        raise AssertionError(errmsg)

    return


def test_cli_run_config_option_updates_config_path():
    """
        Test that --config updates the CLI's config_path property.
    """
    cli = WebworksCLI()
    cmd = _HelloCommand()
    cli.register_command(cmd)

    cli.run(["--config", "/new/path.cfg", "hello"])

    if cli.config_path != "/new/path.cfg":
        errmsg = "Expected config_path '/new/path.cfg', got '{}'".format(cli.config_path)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for run Method - Command Arguments
# =============================================================================

def test_cli_run_passes_command_specific_args():
    """
        Test that command-specific arguments are parsed and passed.
    """
    cli = WebworksCLI()
    cmd = _GreetCommand()
    cli.register_command(cmd)

    cli.run(["greet", "--name", "kiro"])

    name_val = getattr(cmd.received_args, "name", None)
    if name_val != "kiro":
        errmsg = "Expected name 'kiro', got '{}'".format(name_val)
        raise AssertionError(errmsg)

    return


def test_cli_run_command_args_with_global_options():
    """
        Test that global options and command-specific args work together.
    """
    cli = WebworksCLI()
    cmd = _GreetCommand()
    cli.register_command(cmd)

    cli.run(["--verbose", "--env", "dev", "greet", "--name", "ccai"])

    verbose = getattr(cmd.received_args, "verbose", None)
    if verbose is not True:
        errmsg = "Expected verbose=True, got {}".format(verbose)
        raise AssertionError(errmsg)

    env_val = getattr(cmd.received_args, "env", None)
    if env_val != "dev":
        errmsg = "Expected env 'dev', got '{}'".format(env_val)
        raise AssertionError(errmsg)

    name_val = getattr(cmd.received_args, "name", None)
    if name_val != "ccai":
        errmsg = "Expected name 'ccai', got '{}'".format(name_val)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for run Method - Group Dispatch
# =============================================================================

def test_cli_run_dispatches_to_group_command():
    """
        Test that run dispatches to a command within a registered group.
    """
    cli = WebworksCLI()
    start_cmd = _StartCommand()
    group = CLIGroup(name="server", help="Server commands", commands=[start_cmd])
    cli.register_group(group)

    cli.run(["server", "start"])

    if start_cmd.executed is not True:
        errmsg = "Expected start command to be executed."
        raise AssertionError(errmsg)

    return


def test_cli_run_group_command_with_args():
    """
        Test that group command arguments are parsed correctly.
    """
    cli = WebworksCLI()
    start_cmd = _StartCommand()
    group = CLIGroup(name="server", help="Server commands", commands=[start_cmd])
    cli.register_group(group)

    cli.run(["server", "start", "--port", "9000"])

    port_val = getattr(start_cmd.received_args, "port", None)
    if port_val != 9000:
        errmsg = "Expected port 9000, got {}".format(port_val)
        raise AssertionError(errmsg)

    return


def test_cli_run_group_command_with_global_options():
    """
        Test that global options work with group commands.
    """
    cli = WebworksCLI()
    start_cmd = _StartCommand()
    group = CLIGroup(name="server", help="Server commands", commands=[start_cmd])
    cli.register_group(group)

    cli.run(["--verbose", "server", "start"])

    verbose = getattr(start_cmd.received_args, "verbose", None)
    if verbose is not True:
        errmsg = "Expected verbose=True, got {}".format(verbose)
        raise AssertionError(errmsg)

    return


def test_cli_run_dispatches_correct_group_command():
    """
        Test that the correct command within a group is dispatched.
    """
    cli = WebworksCLI()
    start_cmd = _StartCommand()
    stop_cmd = _StopCommand()
    group = CLIGroup(
        name="server",
        help="Server commands",
        commands=[start_cmd, stop_cmd]
    )
    cli.register_group(group)

    cli.run(["server", "stop"])

    if start_cmd.executed is True:
        errmsg = "Expected start command to NOT be executed."
        raise AssertionError(errmsg)

    if stop_cmd.executed is not True:
        errmsg = "Expected stop command to be executed."
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for the Console Entry Point and Error Reporting
# =============================================================================

class _FailingCommand(CLICommand):
    """
        A command that always raises, to observe how the CLI reports it.
    """

    name = "explode"
    help = "Raise an error"

    def execute(self, args: "Namespace", config: Dict[str, Any]) -> int:
        raise RuntimeError("the reactor is on fire")


def _run_capturing_stderr(cli, argv):
    """
        Run the CLI and return (exit_code, text written to stderr).
    """
    import contextlib
    import io

    buffer = io.StringIO()

    with contextlib.redirect_stderr(buffer):
        exit_code = cli.run(argv)

    return exit_code, buffer.getvalue()


def test_create_default_cli_registers_builtin_commands():
    """
        Test that the default CLI has the built-in commands and groups.
    """
    from ccai.webworks.devexp.cli.webworkscli import create_default_cli

    cli = create_default_cli()

    command_names = sorted(cli.commands.keys())
    group_names = sorted(cli.groups.keys())

    if command_names != ["new", "prodserve", "routes", "serve", "shell"]:
        errmsg = "Unexpected built-in commands: {}".format(command_names)
        raise AssertionError(errmsg)

    if group_names != ["db", "generate"]:
        errmsg = "Unexpected built-in groups: {}".format(group_names)
        raise AssertionError(errmsg)

    return


def test_run_prints_command_exception_to_stderr():
    """
        Test that an exception raised by a command is reported on stderr.
    """
    cli = WebworksCLI()
    cli.register_command(_FailingCommand())

    exit_code, stderr_text = _run_capturing_stderr(cli, ["explode"])

    if exit_code != 1:
        errmsg = "Expected exit code 1, got {}".format(exit_code)
        raise AssertionError(errmsg)

    if "RuntimeError: the reactor is on fire" not in stderr_text:
        errmsg = "Expected the error on stderr, got: {!r}".format(stderr_text)
        raise AssertionError(errmsg)

    if "Traceback" in stderr_text:
        errmsg = "Did not expect a traceback without --verbose."
        raise AssertionError(errmsg)

    return


def test_run_verbose_prints_traceback():
    """
        Test that --verbose adds the traceback of a failing command.
    """
    cli = WebworksCLI()
    cli.register_command(_FailingCommand())

    _exit_code, stderr_text = _run_capturing_stderr(cli, ["--verbose", "explode"])

    if "Traceback (most recent call last)" not in stderr_text:
        errmsg = "Expected a traceback with --verbose, got: {!r}".format(stderr_text)
        raise AssertionError(errmsg)

    return


def test_run_fails_for_missing_config_file():
    """
        Test that an explicitly given config file that does not exist
        stops the run with EXIT_CONFIG_ERROR and names the file.
    """
    from ccai.webworks.devexp.cli.exitcodes import EXIT_CONFIG_ERROR

    cli = WebworksCLI()
    cmd = _HelloCommand()
    cli.register_command(cmd)

    exit_code, stderr_text = _run_capturing_stderr(cli, ["--config", "/nonexistent/typo.json", "hello"])

    if exit_code != EXIT_CONFIG_ERROR:
        errmsg = "Expected EXIT_CONFIG_ERROR, got {}".format(exit_code)
        raise AssertionError(errmsg)

    if "/nonexistent/typo.json" not in stderr_text:
        errmsg = "Expected the config path on stderr, got: {!r}".format(stderr_text)
        raise AssertionError(errmsg)

    if cmd.executed is not False:
        errmsg = "Did not expect the command to run with an unusable config file."
        raise AssertionError(errmsg)

    return


def test_global_app_option_is_parsed():
    """
        Test that the global --app option is available to commands.
    """
    cli = WebworksCLI()
    cmd = _HelloCommand()
    cli.register_command(cmd)

    cli.run(["--app", "mysite.app:app", "hello"])

    app_val = getattr(cmd.received_args, "app", None)
    if app_val != "mysite.app:app":
        errmsg = "Expected app 'mysite.app:app', got '{}'".format(app_val)
        raise AssertionError(errmsg)

    return


def test_module_entry_point_prints_help():
    """
        Test that 'python -m ccai.webworks.devexp.cli --help' runs and
        lists the built-in commands.
    """
    import subprocess
    import sys

    completed = subprocess.run(
        [sys.executable, "-m", "ccai.webworks.devexp.cli", "--help"],
        capture_output=True, text=True, timeout=120,
    )

    if completed.returncode != 0:
        errmsg = "Expected exit code 0 from --help, got {}: {}".format(
            completed.returncode, completed.stderr[-500:]
        )
        raise AssertionError(errmsg)

    for name in ["serve", "prodserve", "new", "routes", "shell", "generate", "db"]:
        if name not in completed.stdout:
            errmsg = "Expected '{}' in the help output.".format(name)
            raise AssertionError(errmsg)

    return


def test_module_entry_point_lists_routes_of_scaffolded_project():
    """
        Test the command line end to end: scaffold a project with 'new',
        then list its routes with 'routes' from the project directory.
    """
    import json
    import os
    import shutil
    import subprocess
    import sys
    import tempfile

    temp_dir = tempfile.mkdtemp()

    try:
        created = subprocess.run(
            [sys.executable, "-m", "ccai.webworks.devexp.cli", "new", "cli-demo", "--template", "api"],
            cwd=temp_dir, capture_output=True, text=True, timeout=120,
        )

        if created.returncode != 0:
            errmsg = "'new' failed: {}".format(created.stderr[-500:])
            raise AssertionError(errmsg)

        listed = subprocess.run(
            [sys.executable, "-m", "ccai.webworks.devexp.cli", "routes", "--format", "json"],
            cwd=os.path.join(temp_dir, "cli-demo"), capture_output=True, text=True, timeout=120,
        )

        if listed.returncode != 0:
            errmsg = "'routes' failed: {}{}".format(listed.stdout[-300:], listed.stderr[-500:])
            raise AssertionError(errmsg)

        paths = sorted(route["path"] for route in json.loads(listed.stdout))

        if paths != ["/", "/api/health", "/api/items/list"]:
            errmsg = "Unexpected routes for the scaffolded project: {}".format(paths)
            raise AssertionError(errmsg)
    finally:
        shutil.rmtree(temp_dir)

    return
