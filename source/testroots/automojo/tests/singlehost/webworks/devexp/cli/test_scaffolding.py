"""
    Tests for the project scaffolding commands.

    This module contains unit tests for the :class:`NewProjectCommand`,
    the :data:`PROJECT_TEMPLATES` dictionary, and the
    :func:`create_project_structure` helper function.

    Tests that verify file creation use temporary directories that are
    cleaned up after each test.
"""

import os
import shutil
import tempfile

from argparse import ArgumentParser, Namespace
from typing import Any, Dict

from automojo.webworks.devexp.cli.exitcodes import EXIT_ERROR
from automojo.webworks.devexp.cli.exitcodes import EXIT_SUCCESS
from automojo.webworks.devexp.cli.scaffolding import APP_TEMPLATES
from automojo.webworks.devexp.cli.scaffolding import CONFIG_TEMPLATE
from automojo.webworks.devexp.cli.scaffolding import NewProjectCommand
from automojo.webworks.devexp.cli.scaffolding import PROJECT_TEMPLATES
from automojo.webworks.devexp.cli.scaffolding import create_project_structure


# =============================================================================
# Unit Tests for PROJECT_TEMPLATES
# =============================================================================

def test_project_templates_contains_minimal():
    """
        Test that PROJECT_TEMPLATES contains the minimal template.
    """
    if "minimal" not in PROJECT_TEMPLATES:
        errmsg = "Expected 'minimal' key in PROJECT_TEMPLATES."
        raise AssertionError(errmsg)

    return


def test_project_templates_contains_api():
    """
        Test that PROJECT_TEMPLATES contains the api template.
    """
    if "api" not in PROJECT_TEMPLATES:
        errmsg = "Expected 'api' key in PROJECT_TEMPLATES."
        raise AssertionError(errmsg)

    return


def test_project_templates_contains_webapp():
    """
        Test that PROJECT_TEMPLATES contains the webapp template.
    """
    if "webapp" not in PROJECT_TEMPLATES:
        errmsg = "Expected 'webapp' key in PROJECT_TEMPLATES."
        raise AssertionError(errmsg)

    return


def test_minimal_template_has_app_and_config():
    """
        Test that the minimal template includes app.py and config.py.
    """
    files = PROJECT_TEMPLATES["minimal"]["files"]

    if "app.py" not in files:
        errmsg = "Expected 'app.py' in minimal template files."
        raise AssertionError(errmsg)

    if "config.py" not in files:
        errmsg = "Expected 'config.py' in minimal template files."
        raise AssertionError(errmsg)

    return


def test_api_template_has_blueprints_and_models():
    """
        Test that the api template includes blueprints and models directories.
    """
    files = PROJECT_TEMPLATES["api"]["files"]

    if "blueprints/" not in files:
        errmsg = "Expected 'blueprints/' in api template files."
        raise AssertionError(errmsg)

    if "models/" not in files:
        errmsg = "Expected 'models/' in api template files."
        raise AssertionError(errmsg)

    return


def test_webapp_template_has_templates_and_static():
    """
        Test that the webapp template includes templates and static directories.
    """
    files = PROJECT_TEMPLATES["webapp"]["files"]

    if "templates/" not in files:
        errmsg = "Expected 'templates/' in webapp template files."
        raise AssertionError(errmsg)

    if "static/" not in files:
        errmsg = "Expected 'static/' in webapp template files."
        raise AssertionError(errmsg)

    return


def test_all_templates_have_description():
    """
        Test that every template has a non-empty description.
    """
    for template_name, template_data in PROJECT_TEMPLATES.items():
        description = template_data.get("description", "")
        if len(description) == 0:
            errmsg = "Template '{}' has an empty description.".format(template_name)
            raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for NewProjectCommand Class Attributes
# =============================================================================

def test_new_project_command_name():
    """
        Test that NewProjectCommand has the correct name attribute.
    """
    cmd = NewProjectCommand()

    if cmd.name != "new":
        errmsg = "Expected name 'new', got '{}'.".format(cmd.name)
        raise AssertionError(errmsg)

    return


def test_new_project_command_help():
    """
        Test that NewProjectCommand has non-empty help text.
    """
    cmd = NewProjectCommand()

    if len(cmd.help) == 0:
        errmsg = "Expected non-empty help text for NewProjectCommand."
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for NewProjectCommand.add_arguments
# =============================================================================

def test_add_arguments_registers_project_name():
    """
        Test that add_arguments registers the project_name positional argument.
    """
    cmd = NewProjectCommand()
    parser = ArgumentParser()
    cmd.add_arguments(parser)

    parsed = parser.parse_args(["my-project"])

    if parsed.project_name != "my-project":
        errmsg = "Expected project_name 'my-project', got '{}'.".format(parsed.project_name)
        raise AssertionError(errmsg)

    return


def test_add_arguments_registers_template_option():
    """
        Test that add_arguments registers the --template option.
    """
    cmd = NewProjectCommand()
    parser = ArgumentParser()
    cmd.add_arguments(parser)

    parsed = parser.parse_args(["my-project", "--template", "api"])

    if parsed.template != "api":
        errmsg = "Expected template 'api', got '{}'.".format(parsed.template)
        raise AssertionError(errmsg)

    return


def test_add_arguments_template_defaults_to_minimal():
    """
        Test that the --template option defaults to minimal.
    """
    cmd = NewProjectCommand()
    parser = ArgumentParser()
    cmd.add_arguments(parser)

    parsed = parser.parse_args(["my-project"])

    if parsed.template != "minimal":
        errmsg = "Expected default template 'minimal', got '{}'.".format(parsed.template)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for create_project_structure
# =============================================================================

def test_create_project_structure_minimal():
    """
        Test that create_project_structure creates the minimal template files.
    """
    temp_dir = tempfile.mkdtemp()

    try:
        project_path = os.path.join(temp_dir, "test-project")
        created_files = create_project_structure(project_path, "minimal")

        if "app.py" not in created_files:
            errmsg = "Expected 'app.py' in created files."
            raise AssertionError(errmsg)

        if "config.py" not in created_files:
            errmsg = "Expected 'config.py' in created files."
            raise AssertionError(errmsg)

        app_path = os.path.join(project_path, "app.py")
        if os.path.isfile(app_path) is not True:
            errmsg = "Expected app.py to exist on disk."
            raise AssertionError(errmsg)

        config_path = os.path.join(project_path, "config.py")
        if os.path.isfile(config_path) is not True:
            errmsg = "Expected config.py to exist on disk."
            raise AssertionError(errmsg)
    finally:
        shutil.rmtree(temp_dir)

    return


def test_create_project_structure_api():
    """
        Test that create_project_structure creates the api template structure.
    """
    temp_dir = tempfile.mkdtemp()

    try:
        project_path = os.path.join(temp_dir, "api-project")
        created_files = create_project_structure(project_path, "api")

        blueprints_dir = os.path.join(project_path, "blueprints")
        if os.path.isdir(blueprints_dir) is not True:
            errmsg = "Expected 'blueprints' directory to exist."
            raise AssertionError(errmsg)

        models_dir = os.path.join(project_path, "models")
        if os.path.isdir(models_dir) is not True:
            errmsg = "Expected 'models' directory to exist."
            raise AssertionError(errmsg)

        tests_dir = os.path.join(project_path, "tests")
        if os.path.isdir(tests_dir) is not True:
            errmsg = "Expected 'tests' directory to exist."
            raise AssertionError(errmsg)

        # Verify __init__.py files in subdirectories
        bp_init = os.path.join(blueprints_dir, "__init__.py")
        if os.path.isfile(bp_init) is not True:
            errmsg = "Expected __init__.py in blueprints directory."
            raise AssertionError(errmsg)
    finally:
        shutil.rmtree(temp_dir)

    return


def test_create_project_structure_webapp():
    """
        Test that create_project_structure creates the webapp template structure.
    """
    temp_dir = tempfile.mkdtemp()

    try:
        project_path = os.path.join(temp_dir, "webapp-project")
        created_files = create_project_structure(project_path, "webapp")

        templates_dir = os.path.join(project_path, "templates")
        if os.path.isdir(templates_dir) is not True:
            errmsg = "Expected 'templates' directory to exist."
            raise AssertionError(errmsg)

        static_dir = os.path.join(project_path, "static")
        if os.path.isdir(static_dir) is not True:
            errmsg = "Expected 'static' directory to exist."
            raise AssertionError(errmsg)
    finally:
        shutil.rmtree(temp_dir)

    return


def test_create_project_structure_invalid_template():
    """
        Test that create_project_structure raises ValueError for unknown template.
    """
    temp_dir = tempfile.mkdtemp()

    try:
        project_path = os.path.join(temp_dir, "bad-project")
        raised = False

        try:
            create_project_structure(project_path, "nonexistent")
        except ValueError:
            raised = True

        if raised is not True:
            errmsg = "Expected ValueError for unknown template name."
            raise AssertionError(errmsg)
    finally:
        shutil.rmtree(temp_dir)

    return


def test_create_project_structure_app_contains_project_name():
    """
        Test that the generated app.py contains the project name.
    """
    temp_dir = tempfile.mkdtemp()

    try:
        project_path = os.path.join(temp_dir, "my-cool-app")
        create_project_structure(project_path, "minimal")

        app_path = os.path.join(project_path, "app.py")
        with open(app_path, "r") as app_file:
            content = app_file.read()

        if "my-cool-app" not in content:
            errmsg = "Expected project name 'my-cool-app' in app.py content."
            raise AssertionError(errmsg)
    finally:
        shutil.rmtree(temp_dir)

    return


def test_create_project_structure_config_contains_project_name():
    """
        Test that the generated config.py contains the project name.
    """
    temp_dir = tempfile.mkdtemp()

    try:
        project_path = os.path.join(temp_dir, "my-cool-app")
        create_project_structure(project_path, "minimal")

        config_path = os.path.join(project_path, "config.py")
        with open(config_path, "r") as config_file:
            content = config_file.read()

        if "my-cool-app" not in content:
            errmsg = "Expected project name 'my-cool-app' in config.py content."
            raise AssertionError(errmsg)
    finally:
        shutil.rmtree(temp_dir)

    return


def test_create_project_structure_fails_if_dir_exists():
    """
        Test that create_project_structure raises OSError if the directory exists.
    """
    temp_dir = tempfile.mkdtemp()

    try:
        project_path = os.path.join(temp_dir, "existing-project")
        os.makedirs(project_path)

        raised = False

        try:
            create_project_structure(project_path, "minimal")
        except OSError:
            raised = True

        if raised is not True:
            errmsg = "Expected OSError when project directory already exists."
            raise AssertionError(errmsg)
    finally:
        shutil.rmtree(temp_dir)

    return


# =============================================================================
# Unit Tests for NewProjectCommand.execute
# =============================================================================

def test_execute_creates_project_in_cwd():
    """
        Test that execute creates the project directory in the current
        working directory and returns EXIT_SUCCESS.
    """
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()

    try:
        os.chdir(temp_dir)

        cmd = NewProjectCommand()
        args = Namespace(project_name="test-proj", template="minimal")
        config = {}

        exit_code = cmd.execute(args, config)

        if exit_code != EXIT_SUCCESS:
            errmsg = "Expected EXIT_SUCCESS (0), got {}.".format(exit_code)
            raise AssertionError(errmsg)

        project_path = os.path.join(temp_dir, "test-proj")
        if os.path.isdir(project_path) is not True:
            errmsg = "Expected project directory 'test-proj' to be created."
            raise AssertionError(errmsg)
    finally:
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir)

    return


def test_execute_returns_error_if_dir_exists():
    """
        Test that execute returns EXIT_ERROR when the project directory
        already exists.
    """
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()

    try:
        os.chdir(temp_dir)

        existing_path = os.path.join(temp_dir, "existing-proj")
        os.makedirs(existing_path)

        cmd = NewProjectCommand()
        args = Namespace(project_name="existing-proj", template="minimal")
        config = {}

        exit_code = cmd.execute(args, config)

        if exit_code != EXIT_ERROR:
            errmsg = "Expected EXIT_ERROR (1), got {}.".format(exit_code)
            raise AssertionError(errmsg)
    finally:
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir)

    return


def test_execute_with_api_template():
    """
        Test that execute creates the api template structure.
    """
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()

    try:
        os.chdir(temp_dir)

        cmd = NewProjectCommand()
        args = Namespace(project_name="api-proj", template="api")
        config = {}

        exit_code = cmd.execute(args, config)

        if exit_code != EXIT_SUCCESS:
            errmsg = "Expected EXIT_SUCCESS (0), got {}.".format(exit_code)
            raise AssertionError(errmsg)

        blueprints_dir = os.path.join(temp_dir, "api-proj", "blueprints")
        if os.path.isdir(blueprints_dir) is not True:
            errmsg = "Expected 'blueprints' directory in api project."
            raise AssertionError(errmsg)
    finally:
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir)

    return


def test_execute_with_webapp_template():
    """
        Test that execute creates the webapp template structure.
    """
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()

    try:
        os.chdir(temp_dir)

        cmd = NewProjectCommand()
        args = Namespace(project_name="webapp-proj", template="webapp")
        config = {}

        exit_code = cmd.execute(args, config)

        if exit_code != EXIT_SUCCESS:
            errmsg = "Expected EXIT_SUCCESS (0), got {}.".format(exit_code)
            raise AssertionError(errmsg)

        templates_dir = os.path.join(temp_dir, "webapp-proj", "templates")
        if os.path.isdir(templates_dir) is not True:
            errmsg = "Expected 'templates' directory in webapp project."
            raise AssertionError(errmsg)

        static_dir = os.path.join(temp_dir, "webapp-proj", "static")
        if os.path.isdir(static_dir) is not True:
            errmsg = "Expected 'static' directory in webapp project."
            raise AssertionError(errmsg)
    finally:
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir)

    return
