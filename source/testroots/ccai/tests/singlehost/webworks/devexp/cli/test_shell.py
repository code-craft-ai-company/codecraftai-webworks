"""
    Tests for the CLI shell command.

    This module contains unit tests for the :class:`ShellCommand`,
    :class:`ShellApplication`, and the helper functions
    :func:`resolve_shell_app`, :func:`build_shell_namespace`,
    :func:`build_banner`, :func:`load_startup_file`, and
    :func:`check_ipython_available`.
"""

import os
import tempfile

from argparse import ArgumentParser, Namespace
from typing import Any, Dict

from ccai.webworks.devexp.cli.exitcodes import EXIT_ERROR
from ccai.webworks.devexp.cli.exitcodes import EXIT_SUCCESS
from ccai.webworks.devexp.cli.shell import DEFAULT_COMMON_IMPORTS
from ccai.webworks.devexp.cli.shell import DEFAULT_STARTUP_FILENAME
from ccai.webworks.devexp.cli.shell import ShellApplication
from ccai.webworks.devexp.cli.shell import ShellCommand
from ccai.webworks.devexp.cli.shell import build_banner
from ccai.webworks.devexp.cli.shell import build_shell_namespace
from ccai.webworks.devexp.cli.shell import check_ipython_available
from ccai.webworks.devexp.cli.shell import load_startup_file
from ccai.webworks.devexp.cli.shell import resolve_shell_app


# =============================================================================
# Test Helpers
# =============================================================================

class _TestShellApp(ShellApplication):
    """
        A concrete shell application for testing.

        Returns a configurable application instance and common imports.
    """

    def __init__(self, instance=None, common_imports=None):
        self._instance = instance if instance is not None else "test-app"
        self._common_imports = common_imports if common_imports is not None else {}
        self._fail_instance = False
        self._fail_imports = False

        return

    def get_instance(self) -> Any:
        if self._fail_instance:
            raise RuntimeError("Failed to get instance")
        return self._instance

    def get_common_imports(self) -> Dict[str, Any]:
        if self._fail_imports:
            raise RuntimeError("Failed to get imports")
        return dict(self._common_imports)


def _make_args(**kwargs) -> Namespace:
    """
        Create a Namespace object with the given keyword arguments.

        :returns: A Namespace instance.
    """
    defaults = {
        "no_ipython": False,
        "startup_file": None,
        "no_banner": False,
    }
    defaults.update(kwargs)
    return Namespace(**defaults)


def _make_config(shell_app=None) -> Dict[str, Any]:
    """
        Create a configuration dictionary for testing.

        :param shell_app: Optional shell application instance.

        :returns: A configuration dictionary.
    """
    config = {}

    if shell_app is not None:
        config["shell_app"] = shell_app

    return config


def _create_temp_startup_file(content: str) -> str:
    """
        Create a temporary startup file with the given content.

        :param content: The Python source code to write.

        :returns: The path to the temporary file.
    """
    fd, path = tempfile.mkstemp(suffix=".py")
    with os.fdopen(fd, "w") as fh:
        fh.write(content)
    return path


# =============================================================================
# Tests: ShellApplication Interface
# =============================================================================

def test_shell_application_get_instance_raises():
    """
        Verify that the base ShellApplication raises NotImplementedError
        when get_instance is called.
    """
    app = ShellApplication()
    raised = False

    try:
        app.get_instance()
    except NotImplementedError:
        raised = True

    assert raised, "Expected NotImplementedError from get_instance"

    return


def test_shell_application_get_common_imports_raises():
    """
        Verify that the base ShellApplication raises NotImplementedError
        when get_common_imports is called.
    """
    app = ShellApplication()
    raised = False

    try:
        app.get_common_imports()
    except NotImplementedError:
        raised = True

    assert raised, "Expected NotImplementedError from get_common_imports"

    return


# =============================================================================
# Tests: resolve_shell_app
# =============================================================================

def test_resolve_shell_app_returns_app():
    """
        Verify that resolve_shell_app returns the shell application
        when configured.
    """
    shell_app = _TestShellApp()
    config = _make_config(shell_app=shell_app)

    result = resolve_shell_app(config)

    assert result is shell_app, "Expected the configured shell application"

    return


def test_resolve_shell_app_returns_none_when_missing():
    """
        Verify that resolve_shell_app returns None when no shell
        application is configured.
    """
    config = _make_config()

    result = resolve_shell_app(config)

    assert result is None, "Expected None when shell_app is not configured"

    return


def test_resolve_shell_app_returns_none_for_non_shell_app():
    """
        Verify that resolve_shell_app returns None when the configured
        value is not a ShellApplication instance.
    """
    config = {"shell_app": "not-a-shell-app"}

    result = resolve_shell_app(config)

    assert result is None, "Expected None for non-ShellApplication value"

    return


# =============================================================================
# Tests: build_shell_namespace
# =============================================================================

def test_build_namespace_includes_default_imports():
    """
        Verify that the namespace includes default common imports
        (os, sys) even without a shell application.
    """
    namespace = build_shell_namespace(None, {})

    assert "os" in namespace, "Expected 'os' in namespace"
    assert "sys" in namespace, "Expected 'sys' in namespace"

    return


def test_build_namespace_includes_app_instance():
    """
        Verify that the namespace includes the application instance
        as 'app' when a shell application is configured.
    """
    shell_app = _TestShellApp(instance="my-app")
    namespace = build_shell_namespace(shell_app, {})

    assert "app" in namespace, "Expected 'app' in namespace"
    assert namespace["app"] == "my-app", "Expected app to be 'my-app'"

    return


def test_build_namespace_includes_common_imports():
    """
        Verify that the namespace includes common imports from the
        shell application.
    """
    common = {"Model": "model-class", "db": "database"}
    shell_app = _TestShellApp(common_imports=common)
    namespace = build_shell_namespace(shell_app, {})

    assert "Model" in namespace, "Expected 'Model' in namespace"
    assert namespace["Model"] == "model-class", "Expected Model to be 'model-class'"
    assert "db" in namespace, "Expected 'db' in namespace"
    assert namespace["db"] == "database", "Expected db to be 'database'"

    return


def test_build_namespace_handles_instance_failure():
    """
        Verify that the namespace is still built when get_instance
        raises an exception.
    """
    shell_app = _TestShellApp()
    shell_app._fail_instance = True
    namespace = build_shell_namespace(shell_app, {})

    assert "app" not in namespace, "Expected 'app' not in namespace on failure"
    assert "os" in namespace, "Expected default imports still present"

    return


def test_build_namespace_handles_imports_failure():
    """
        Verify that the namespace is still built when get_common_imports
        raises an exception.
    """
    shell_app = _TestShellApp(instance="my-app")
    shell_app._fail_imports = True
    namespace = build_shell_namespace(shell_app, {})

    assert "app" in namespace, "Expected 'app' still present"
    assert "os" in namespace, "Expected default imports still present"

    return


# =============================================================================
# Tests: build_banner
# =============================================================================

def test_build_banner_contains_title():
    """
        Verify that the banner contains the shell title.
    """
    namespace = {"os": os}
    banner = build_banner(namespace)

    assert "Webworks Interactive Shell" in banner, "Expected title in banner"

    return


def test_build_banner_contains_available_objects_header():
    """
        Verify that the banner contains the 'Available objects' header.
    """
    namespace = {"os": os}
    banner = build_banner(namespace)

    assert "Available objects:" in banner, "Expected 'Available objects:' in banner"

    return


def test_build_banner_lists_namespace_entries():
    """
        Verify that the banner lists all namespace entries.
    """
    namespace = {"app": "my-app", "os": os}
    banner = build_banner(namespace)

    assert "app" in banner, "Expected 'app' in banner"
    assert "os" in banner, "Expected 'os' in banner"

    return


def test_build_banner_shows_type_info():
    """
        Verify that the banner shows type information for objects.
    """
    namespace = {"app": "my-app"}
    banner = build_banner(namespace)

    assert "str" in banner, "Expected type 'str' in banner for string object"

    return


def test_build_banner_shows_function_kind():
    """
        Verify that the banner shows 'function' for callable objects.
    """
    def my_func():
        pass

    namespace = {"helper": my_func}
    banner = build_banner(namespace)

    assert "function" in banner, "Expected 'function' in banner for callable"

    return


def test_build_banner_shows_class_kind():
    """
        Verify that the banner shows 'class' for class objects.
    """
    namespace = {"MyClass": ShellApplication}
    banner = build_banner(namespace)

    assert "class" in banner, "Expected 'class' in banner for class type"

    return


def test_build_banner_sorted_names():
    """
        Verify that the banner lists names in sorted order.
    """
    namespace = {"zebra": 1, "alpha": 2, "middle": 3}
    banner = build_banner(namespace)

    alpha_pos = banner.index("alpha")
    middle_pos = banner.index("middle")
    zebra_pos = banner.index("zebra")

    assert alpha_pos < middle_pos, "Expected 'alpha' before 'middle'"
    assert middle_pos < zebra_pos, "Expected 'middle' before 'zebra'"

    return


def test_build_banner_empty_namespace():
    """
        Verify that the banner handles an empty namespace.
    """
    namespace = {}
    banner = build_banner(namespace)

    assert "Webworks Interactive Shell" in banner, "Expected title in banner"
    assert "Available objects:" in banner, "Expected header in banner"

    return


# =============================================================================
# Tests: load_startup_file
# =============================================================================

def test_load_startup_file_not_found():
    """
        Verify that load_startup_file returns (False, None) when the
        file does not exist.
    """
    loaded, error = load_startup_file("/nonexistent/path/startup.py", {})

    assert loaded is False, "Expected loaded to be False"
    assert error is None, "Expected no error message for missing file"

    return


def test_load_startup_file_executes_code():
    """
        Verify that load_startup_file executes the startup file and
        adds defined names to the namespace.
    """
    path = _create_temp_startup_file("SHELL_VAR = 42\n")

    try:
        namespace = {}
        loaded, error = load_startup_file(path, namespace)

        assert loaded is True, "Expected loaded to be True"
        assert error is None, "Expected no error message"
        assert "SHELL_VAR" in namespace, "Expected SHELL_VAR in namespace"
        assert namespace["SHELL_VAR"] == 42, "Expected SHELL_VAR to be 42"
    finally:
        os.unlink(path)

    return


def test_load_startup_file_syntax_error():
    """
        Verify that load_startup_file returns an error message when
        the startup file has a syntax error.
    """
    path = _create_temp_startup_file("def broken(\n")

    try:
        namespace = {}
        loaded, error = load_startup_file(path, namespace)

        assert loaded is False, "Expected loaded to be False"
        assert error is not None, "Expected an error message"
        assert "Error loading startup file" in error, "Expected error prefix"
    finally:
        os.unlink(path)

    return


def test_load_startup_file_runtime_error():
    """
        Verify that load_startup_file returns an error message when
        the startup file raises a runtime error.
    """
    path = _create_temp_startup_file("raise ValueError('test error')\n")

    try:
        namespace = {}
        loaded, error = load_startup_file(path, namespace)

        assert loaded is False, "Expected loaded to be False"
        assert error is not None, "Expected an error message"
        assert "test error" in error, "Expected error details in message"
    finally:
        os.unlink(path)

    return


# =============================================================================
# Tests: ShellCommand Metadata
# =============================================================================

def test_shell_command_name():
    """
        Verify that the ShellCommand has the correct name.
    """
    cmd = ShellCommand()

    assert cmd.name == "shell", "Expected command name to be 'shell'"

    return


def test_shell_command_help():
    """
        Verify that the ShellCommand has non-empty help text.
    """
    cmd = ShellCommand()

    assert len(cmd.help) > 0, "Expected non-empty help text"

    return


# =============================================================================
# Tests: ShellCommand.add_arguments
# =============================================================================

def test_shell_command_adds_no_ipython_argument():
    """
        Verify that the ShellCommand adds the --no-ipython argument.
    """
    cmd = ShellCommand()
    parser = ArgumentParser()
    cmd.add_arguments(parser)

    args = parser.parse_args([])
    assert hasattr(args, "no_ipython"), "Expected 'no_ipython' attribute"
    assert args.no_ipython is False, "Expected default no_ipython to be False"

    return


def test_shell_command_adds_startup_file_argument():
    """
        Verify that the ShellCommand adds the --startup-file argument.
    """
    cmd = ShellCommand()
    parser = ArgumentParser()
    cmd.add_arguments(parser)

    args = parser.parse_args([])
    assert hasattr(args, "startup_file"), "Expected 'startup_file' attribute"
    assert args.startup_file is None, "Expected default startup_file to be None"

    return


def test_shell_command_adds_no_banner_argument():
    """
        Verify that the ShellCommand adds the --no-banner argument.
    """
    cmd = ShellCommand()
    parser = ArgumentParser()
    cmd.add_arguments(parser)

    args = parser.parse_args([])
    assert hasattr(args, "no_banner"), "Expected 'no_banner' attribute"
    assert args.no_banner is False, "Expected default no_banner to be False"

    return


def test_shell_command_no_ipython_flag_sets_true():
    """
        Verify that --no-ipython sets the flag to True.
    """
    cmd = ShellCommand()
    parser = ArgumentParser()
    cmd.add_arguments(parser)

    args = parser.parse_args(["--no-ipython"])
    assert args.no_ipython is True, "Expected no_ipython to be True"

    return


def test_shell_command_startup_file_accepts_path():
    """
        Verify that --startup-file accepts a file path.
    """
    cmd = ShellCommand()
    parser = ArgumentParser()
    cmd.add_arguments(parser)

    args = parser.parse_args(["--startup-file", "/tmp/custom.py"])
    assert args.startup_file == "/tmp/custom.py", "Expected custom startup file path"

    return


def test_shell_command_no_banner_flag_sets_true():
    """
        Verify that --no-banner sets the flag to True.
    """
    cmd = ShellCommand()
    parser = ArgumentParser()
    cmd.add_arguments(parser)

    args = parser.parse_args(["--no-banner"])
    assert args.no_banner is True, "Expected no_banner to be True"

    return


# =============================================================================
# Tests: ShellCommand.execute
# =============================================================================

def test_shell_command_execute_success_no_app():
    """
        Verify that the shell command succeeds without a configured
        shell application. The launcher is replaced with a no-op
        to avoid blocking.
    """
    launched = []

    def mock_launcher(namespace, banner):
        launched.append({"namespace": namespace, "banner": banner})

    cmd = ShellCommand()
    cmd._standard_launcher = mock_launcher
    cmd._ipython_checker = lambda: False

    args = _make_args(startup_file="/nonexistent/startup.py")
    config = _make_config()

    result = cmd.execute(args, config)

    assert result == EXIT_SUCCESS, "Expected EXIT_SUCCESS"
    assert len(launched) == 1, "Expected launcher to be called once"

    return


def test_shell_command_execute_success_with_app():
    """
        Verify that the shell command pre-loads the application
        instance into the namespace.
    """
    launched = []

    def mock_launcher(namespace, banner):
        launched.append({"namespace": namespace, "banner": banner})

    shell_app = _TestShellApp(instance="my-app", common_imports={"db": "database"})
    cmd = ShellCommand()
    cmd._standard_launcher = mock_launcher
    cmd._ipython_checker = lambda: False

    args = _make_args(startup_file="/nonexistent/startup.py")
    config = _make_config(shell_app=shell_app)

    result = cmd.execute(args, config)

    assert result == EXIT_SUCCESS, "Expected EXIT_SUCCESS"
    assert len(launched) == 1, "Expected launcher to be called once"

    ns = launched[0]["namespace"]
    assert "app" in ns, "Expected 'app' in namespace"
    assert ns["app"] == "my-app", "Expected app to be 'my-app'"
    assert "db" in ns, "Expected 'db' in namespace"

    return


def test_shell_command_execute_uses_ipython_when_available():
    """
        Verify that the shell command uses IPython when available
        and --no-ipython is not set.
    """
    ipython_launched = []
    standard_launched = []

    def mock_ipython(namespace, banner):
        ipython_launched.append(True)

    def mock_standard(namespace, banner):
        standard_launched.append(True)

    cmd = ShellCommand()
    cmd._ipython_launcher = mock_ipython
    cmd._standard_launcher = mock_standard
    cmd._ipython_checker = lambda: True

    args = _make_args(no_ipython=False, startup_file="/nonexistent/startup.py")
    config = _make_config()

    result = cmd.execute(args, config)

    assert result == EXIT_SUCCESS, "Expected EXIT_SUCCESS"
    assert len(ipython_launched) == 1, "Expected IPython launcher to be called"
    assert len(standard_launched) == 0, "Expected standard launcher not to be called"

    return


def test_shell_command_execute_falls_back_to_standard():
    """
        Verify that the shell command falls back to the standard
        shell when IPython is not available.
    """
    ipython_launched = []
    standard_launched = []

    def mock_ipython(namespace, banner):
        ipython_launched.append(True)

    def mock_standard(namespace, banner):
        standard_launched.append(True)

    cmd = ShellCommand()
    cmd._ipython_launcher = mock_ipython
    cmd._standard_launcher = mock_standard
    cmd._ipython_checker = lambda: False

    args = _make_args(no_ipython=False, startup_file="/nonexistent/startup.py")
    config = _make_config()

    result = cmd.execute(args, config)

    assert result == EXIT_SUCCESS, "Expected EXIT_SUCCESS"
    assert len(ipython_launched) == 0, "Expected IPython launcher not to be called"
    assert len(standard_launched) == 1, "Expected standard launcher to be called"

    return


def test_shell_command_execute_no_ipython_flag():
    """
        Verify that --no-ipython forces the standard shell even
        when IPython is available.
    """
    ipython_launched = []
    standard_launched = []

    def mock_ipython(namespace, banner):
        ipython_launched.append(True)

    def mock_standard(namespace, banner):
        standard_launched.append(True)

    cmd = ShellCommand()
    cmd._ipython_launcher = mock_ipython
    cmd._standard_launcher = mock_standard
    cmd._ipython_checker = lambda: True

    args = _make_args(no_ipython=True, startup_file="/nonexistent/startup.py")
    config = _make_config()

    result = cmd.execute(args, config)

    assert result == EXIT_SUCCESS, "Expected EXIT_SUCCESS"
    assert len(ipython_launched) == 0, "Expected IPython launcher not to be called"
    assert len(standard_launched) == 1, "Expected standard launcher to be called"

    return


def test_shell_command_execute_no_banner():
    """
        Verify that --no-banner suppresses the banner.
    """
    launched = []

    def mock_launcher(namespace, banner):
        launched.append({"banner": banner})

    cmd = ShellCommand()
    cmd._standard_launcher = mock_launcher
    cmd._ipython_checker = lambda: False

    args = _make_args(no_banner=True, startup_file="/nonexistent/startup.py")
    config = _make_config()

    result = cmd.execute(args, config)

    assert result == EXIT_SUCCESS, "Expected EXIT_SUCCESS"
    assert launched[0]["banner"] == "", "Expected empty banner"

    return


def test_shell_command_execute_with_banner():
    """
        Verify that the banner is passed to the launcher when
        --no-banner is not set.
    """
    launched = []

    def mock_launcher(namespace, banner):
        launched.append({"banner": banner})

    cmd = ShellCommand()
    cmd._standard_launcher = mock_launcher
    cmd._ipython_checker = lambda: False

    args = _make_args(no_banner=False, startup_file="/nonexistent/startup.py")
    config = _make_config()

    result = cmd.execute(args, config)

    assert result == EXIT_SUCCESS, "Expected EXIT_SUCCESS"
    assert "Webworks Interactive Shell" in launched[0]["banner"], "Expected banner content"

    return


def test_shell_command_execute_loads_startup_file():
    """
        Verify that the shell command loads the startup file and
        adds its definitions to the namespace.
    """
    path = _create_temp_startup_file("STARTUP_VAR = 'loaded'\n")
    launched = []

    def mock_launcher(namespace, banner):
        launched.append({"namespace": dict(namespace)})

    cmd = ShellCommand()
    cmd._standard_launcher = mock_launcher
    cmd._ipython_checker = lambda: False

    try:
        args = _make_args(startup_file=path)
        config = _make_config()

        result = cmd.execute(args, config)

        assert result == EXIT_SUCCESS, "Expected EXIT_SUCCESS"
        ns = launched[0]["namespace"]
        assert "STARTUP_VAR" in ns, "Expected STARTUP_VAR in namespace"
        assert ns["STARTUP_VAR"] == "loaded", "Expected STARTUP_VAR to be 'loaded'"
    finally:
        os.unlink(path)

    return


def test_shell_command_execute_startup_error_returns_error():
    """
        Verify that the shell command returns EXIT_ERROR when the
        startup file has an error.
    """
    path = _create_temp_startup_file("raise ValueError('startup failed')\n")
    launched = []

    def mock_launcher(namespace, banner):
        launched.append(True)

    cmd = ShellCommand()
    cmd._standard_launcher = mock_launcher
    cmd._ipython_checker = lambda: False

    try:
        args = _make_args(startup_file=path)
        config = _make_config()

        result = cmd.execute(args, config)

        assert result == EXIT_ERROR, "Expected EXIT_ERROR"
        assert len(launched) == 0, "Expected launcher not to be called"
    finally:
        os.unlink(path)

    return


def test_shell_command_execute_launcher_exception():
    """
        Verify that the shell command returns EXIT_ERROR when the
        launcher raises an exception.
    """
    def failing_launcher(namespace, banner):
        raise RuntimeError("Shell crashed")

    cmd = ShellCommand()
    cmd._standard_launcher = failing_launcher
    cmd._ipython_checker = lambda: False

    args = _make_args(startup_file="/nonexistent/startup.py")
    config = _make_config()

    result = cmd.execute(args, config)

    assert result == EXIT_ERROR, "Expected EXIT_ERROR"

    return


def test_shell_command_execute_handles_system_exit():
    """
        Verify that the shell command handles SystemExit from the
        launcher gracefully and returns EXIT_SUCCESS.
    """
    def exit_launcher(namespace, banner):
        raise SystemExit(0)

    cmd = ShellCommand()
    cmd._standard_launcher = exit_launcher
    cmd._ipython_checker = lambda: False

    args = _make_args(startup_file="/nonexistent/startup.py")
    config = _make_config()

    result = cmd.execute(args, config)

    assert result == EXIT_SUCCESS, "Expected EXIT_SUCCESS after SystemExit"

    return


# =============================================================================
# Tests: DEFAULT_STARTUP_FILENAME
# =============================================================================

def test_default_startup_filename():
    """
        Verify the default startup filename constant.
    """
    assert DEFAULT_STARTUP_FILENAME == ".webworks_shell.py", \
        "Expected default startup filename to be '.webworks_shell.py'"

    return


# =============================================================================
# Tests: DEFAULT_COMMON_IMPORTS
# =============================================================================

def test_default_common_imports_contains_os():
    """
        Verify that default common imports include os.
    """
    assert "os" in DEFAULT_COMMON_IMPORTS, "Expected 'os' in default imports"

    return


def test_default_common_imports_contains_sys():
    """
        Verify that default common imports include sys.
    """
    assert "sys" in DEFAULT_COMMON_IMPORTS, "Expected 'sys' in default imports"

    return
