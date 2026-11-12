"""
    Tests for the application loader of the developer tools.

    This module contains unit tests for parsing an import target,
    resolving the target from arguments and configuration, and importing
    the application the target names.
"""

import os
import shutil
import sys
import tempfile

from argparse import Namespace

from ccai.webworks.devexp.apploader import ApplicationLoadError
from ccai.webworks.devexp.apploader import load_application
from ccai.webworks.devexp.apploader import parse_app_target
from ccai.webworks.devexp.apploader import resolve_app_target


# =============================================================================
# Test Helpers
# =============================================================================

def _write_module(directory, module_name, source):
    """
        Write a module file into a directory and make the directory importable.
    """
    module_path = os.path.join(directory, module_name + ".py")

    with open(module_path, "w") as module_file:
        module_file.write(source)

    if directory not in sys.path:
        sys.path.insert(0, directory)

    return module_path


def _forget_module(directory, module_name):
    """
        Undo _write_module: drop the module and the path entry.
    """
    sys.modules.pop(module_name, None)

    if directory in sys.path:
        sys.path.remove(directory)

    return


# =============================================================================
# Unit Tests for parse_app_target
# =============================================================================

def test_parse_app_target_splits_module_and_attribute():
    """
        Test that 'module:attribute' is split at the colon.
    """
    result = parse_app_target("mysite.app:application")

    if result != ("mysite.app", "application"):
        errmsg = "Expected ('mysite.app', 'application'), got {}".format(result)
        raise AssertionError(errmsg)

    return


def test_parse_app_target_defaults_attribute_to_app():
    """
        Test that a target naming only a module uses the attribute 'app'.
    """
    result = parse_app_target("mysite")

    if result != ("mysite", "app"):
        errmsg = "Expected ('mysite', 'app'), got {}".format(result)
        raise AssertionError(errmsg)

    return


def test_parse_app_target_rejects_malformed_targets():
    """
        Test that targets that are not dotted identifiers are rejected.
    """
    for bad_target in ["", "  ", "my-site:app", "mysite:", ":app", "a b:c", "mysite:app()"]:
        raised = False

        try:
            parse_app_target(bad_target)
        except ApplicationLoadError:
            raised = True

        if raised is not True:
            errmsg = "Expected ApplicationLoadError for the target {!r}".format(bad_target)
            raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for resolve_app_target
# =============================================================================

def test_resolve_app_target_prefers_command_line_option():
    """
        Test that --app takes precedence over the server.app configuration key.
    """
    args = Namespace(app="cli_module:app")
    config = {"server": {"app": "config_module:app"}}

    target = resolve_app_target(args, config)

    if target != "cli_module:app":
        errmsg = "Expected 'cli_module:app', got '{}'".format(target)
        raise AssertionError(errmsg)

    return


def test_resolve_app_target_uses_server_app_config_key():
    """
        Test that the server.app configuration key is used without --app.
    """
    target = resolve_app_target(Namespace(app=None), {"server": {"app": "config_module:app"}})

    if target != "config_module:app":
        errmsg = "Expected 'config_module:app', got '{}'".format(target)
        raise AssertionError(errmsg)

    return


def test_resolve_app_target_finds_app_py_in_current_directory():
    """
        Test that 'app:app' is the target when ./app.py exists.
    """
    temp_dir = tempfile.mkdtemp()
    previous_cwd = os.getcwd()

    try:
        with open(os.path.join(temp_dir, "app.py"), "w") as app_file:
            app_file.write("app = None\n")

        os.chdir(temp_dir)

        target = resolve_app_target(Namespace(), {})

        if target != "app:app":
            errmsg = "Expected 'app:app', got '{}'".format(target)
            raise AssertionError(errmsg)
    finally:
        os.chdir(previous_cwd)
        shutil.rmtree(temp_dir)

    return


def test_resolve_app_target_returns_none_when_nothing_is_configured():
    """
        Test that no target is resolved without --app, configuration or app.py.
    """
    temp_dir = tempfile.mkdtemp()
    previous_cwd = os.getcwd()

    try:
        os.chdir(temp_dir)

        target = resolve_app_target(Namespace(), {})

        if target is not None:
            errmsg = "Expected None, got '{}'".format(target)
            raise AssertionError(errmsg)
    finally:
        os.chdir(previous_cwd)
        shutil.rmtree(temp_dir)

    return


# =============================================================================
# Unit Tests for load_application
# =============================================================================

def test_load_application_imports_the_named_attribute():
    """
        Test that the object named by the target is returned.
    """
    temp_dir = tempfile.mkdtemp()
    module_name = "apploader_probe_good"

    try:
        _write_module(temp_dir, module_name, "application = 'the-application'\n")

        loaded = load_application(module_name + ":application")

        if loaded != "the-application":
            errmsg = "Expected 'the-application', got {!r}".format(loaded)
            raise AssertionError(errmsg)
    finally:
        _forget_module(temp_dir, module_name)
        shutil.rmtree(temp_dir)

    return


def test_load_application_reports_missing_module():
    """
        Test that a target whose module does not exist raises
        ApplicationLoadError naming the module.
    """
    raised = False

    try:
        load_application("apploader_module_that_does_not_exist:app")
    except ApplicationLoadError as err:
        raised = True
        if "apploader_module_that_does_not_exist" not in str(err):
            errmsg = "Expected the module name in the error, got '{}'".format(err)
            raise AssertionError(errmsg)

    if raised is not True:
        errmsg = "Expected ApplicationLoadError for a missing module."
        raise AssertionError(errmsg)

    return


def test_load_application_reports_missing_attribute():
    """
        Test that a target whose attribute does not exist raises
        ApplicationLoadError.
    """
    temp_dir = tempfile.mkdtemp()
    module_name = "apploader_probe_noattr"

    try:
        _write_module(temp_dir, module_name, "something_else = 1\n")

        raised = False
        try:
            load_application(module_name + ":app")
        except ApplicationLoadError:
            raised = True

        if raised is not True:
            errmsg = "Expected ApplicationLoadError for a missing attribute."
            raise AssertionError(errmsg)
    finally:
        _forget_module(temp_dir, module_name)
        shutil.rmtree(temp_dir)

    return


def test_load_application_reports_error_raised_by_the_module():
    """
        Test that an error in the application module's own code is
        reported as ApplicationLoadError with the cause chained.
    """
    temp_dir = tempfile.mkdtemp()
    module_name = "apploader_probe_broken"

    try:
        _write_module(temp_dir, module_name, "def broken(:\n    pass\n")

        raised = False
        try:
            load_application(module_name + ":app")
        except ApplicationLoadError as err:
            raised = True
            if not isinstance(err.__cause__, SyntaxError):
                errmsg = "Expected the SyntaxError as the cause, got {!r}".format(err.__cause__)
                raise AssertionError(errmsg)

        if raised is not True:
            errmsg = "Expected ApplicationLoadError for a module with a syntax error."
            raise AssertionError(errmsg)
    finally:
        _forget_module(temp_dir, module_name)
        shutil.rmtree(temp_dir)

    return
