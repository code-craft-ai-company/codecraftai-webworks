"""
    Tests for the code generation commands.

    This module contains unit tests for the :class:`GenerateEndpointCommand`,
    :class:`GenerateBlueprintCommand`, and the helper functions
    :func:`to_snake_case`, :func:`to_pascal_case`,
    :func:`generate_endpoint_content`, :func:`generate_blueprint_content`,
    and :func:`write_generated_file`.

    Tests that verify file creation use temporary directories that are
    cleaned up after each test.
"""

import os
import shutil
import tempfile

from argparse import ArgumentParser, Namespace
from typing import Any, Dict

from ccai.webworks.devexp.cli.exitcodes import EXIT_ERROR
from ccai.webworks.devexp.cli.exitcodes import EXIT_SUCCESS
from ccai.webworks.devexp.cli.generators import GenerateBlueprintCommand
from ccai.webworks.devexp.cli.generators import GenerateEndpointCommand
from ccai.webworks.devexp.cli.generators import generate_blueprint_content
from ccai.webworks.devexp.cli.generators import generate_endpoint_content
from ccai.webworks.devexp.cli.generators import to_pascal_case
from ccai.webworks.devexp.cli.generators import to_snake_case
from ccai.webworks.devexp.cli.generators import write_generated_file


# =============================================================================
# Unit Tests for to_snake_case
# =============================================================================

def test_to_snake_case_from_kebab():
    """
        Test that to_snake_case converts kebab-case to snake_case.
    """
    result = to_snake_case("user-profile")

    if result != "user_profile":
        errmsg = "Expected 'user_profile', got '{}'.".format(result)
        raise AssertionError(errmsg)

    return


def test_to_snake_case_from_camel():
    """
        Test that to_snake_case converts camelCase to snake_case.
    """
    result = to_snake_case("userProfile")

    if result != "user_profile":
        errmsg = "Expected 'user_profile', got '{}'.".format(result)
        raise AssertionError(errmsg)

    return


def test_to_snake_case_from_pascal():
    """
        Test that to_snake_case converts PascalCase to snake_case.
    """
    result = to_snake_case("UserProfile")

    if result != "user_profile":
        errmsg = "Expected 'user_profile', got '{}'.".format(result)
        raise AssertionError(errmsg)

    return


def test_to_snake_case_already_snake():
    """
        Test that to_snake_case preserves an already snake_case name.
    """
    result = to_snake_case("user_profile")

    if result != "user_profile":
        errmsg = "Expected 'user_profile', got '{}'.".format(result)
        raise AssertionError(errmsg)

    return


def test_to_snake_case_single_word():
    """
        Test that to_snake_case handles a single word.
    """
    result = to_snake_case("users")

    if result != "users":
        errmsg = "Expected 'users', got '{}'.".format(result)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for to_pascal_case
# =============================================================================

def test_to_pascal_case_from_snake():
    """
        Test that to_pascal_case converts snake_case to PascalCase.
    """
    result = to_pascal_case("user_profile")

    if result != "UserProfile":
        errmsg = "Expected 'UserProfile', got '{}'.".format(result)
        raise AssertionError(errmsg)

    return


def test_to_pascal_case_from_kebab():
    """
        Test that to_pascal_case converts kebab-case to PascalCase.
    """
    result = to_pascal_case("user-profile")

    if result != "UserProfile":
        errmsg = "Expected 'UserProfile', got '{}'.".format(result)
        raise AssertionError(errmsg)

    return


def test_to_pascal_case_single_word():
    """
        Test that to_pascal_case capitalizes a single word.
    """
    result = to_pascal_case("users")

    if result != "Users":
        errmsg = "Expected 'Users', got '{}'.".format(result)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for generate_endpoint_content
# =============================================================================

def test_generate_endpoint_content_contains_function():
    """
        Test that generate_endpoint_content produces content with
        a function definition using the snake_case name.
    """
    content = generate_endpoint_content("user-profile")

    expected_def = "def user_profile(request):"
    if expected_def not in content:
        errmsg = "Expected '{}' in generated content.".format(expected_def)
        raise AssertionError(errmsg)

    return


def test_generate_endpoint_content_contains_docstring():
    """
        Test that generate_endpoint_content produces content with
        a docstring referencing the endpoint name.
    """
    content = generate_endpoint_content("user-profile")

    if "user_profile" not in content:
        errmsg = "Expected 'user_profile' in generated endpoint content."
        raise AssertionError(errmsg)

    return


def test_generate_endpoint_content_contains_return():
    """
        Test that generate_endpoint_content produces content with
        a return statement.
    """
    content = generate_endpoint_content("health-check")

    if "return rtnval" not in content:
        errmsg = "Expected 'return rtnval' in generated endpoint content."
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for generate_blueprint_content
# =============================================================================

def test_generate_blueprint_content_contains_class():
    """
        Test that generate_blueprint_content produces content with
        a class definition using PascalCase.
    """
    content = generate_blueprint_content("user-management")

    expected_class = "class UserManagementBlueprint:"
    if expected_class not in content:
        errmsg = "Expected '{}' in generated content.".format(expected_class)
        raise AssertionError(errmsg)

    return


def test_generate_blueprint_content_contains_url_prefix():
    """
        Test that generate_blueprint_content produces content with
        a url_prefix using hyphenated form.
    """
    content = generate_blueprint_content("user-management")

    if '"/user-management"' not in content:
        errmsg = "Expected url_prefix '/user-management' in generated content."
        raise AssertionError(errmsg)

    return


def test_generate_blueprint_content_contains_register_method():
    """
        Test that generate_blueprint_content produces content with
        a register method.
    """
    content = generate_blueprint_content("user-management")

    if "def register(self, app):" not in content:
        errmsg = "Expected 'def register(self, app):' in generated content."
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for write_generated_file
# =============================================================================

def test_write_generated_file_creates_file():
    """
        Test that write_generated_file creates the file on disk.
    """
    temp_dir = tempfile.mkdtemp()

    try:
        file_path = os.path.join(temp_dir, "test_endpoint.py")
        content = "# test content\n"

        exit_code = write_generated_file(file_path, content, dry_run=False)

        if exit_code != EXIT_SUCCESS:
            errmsg = "Expected EXIT_SUCCESS, got {}.".format(exit_code)
            raise AssertionError(errmsg)

        if os.path.isfile(file_path) is not True:
            errmsg = "Expected file to exist at '{}'.".format(file_path)
            raise AssertionError(errmsg)

        with open(file_path, "r") as fh:
            written = fh.read()

        if written != content:
            errmsg = "File content does not match expected content."
            raise AssertionError(errmsg)
    finally:
        shutil.rmtree(temp_dir)

    return


def test_write_generated_file_returns_error_if_exists():
    """
        Test that write_generated_file returns EXIT_ERROR when the
        target file already exists.
    """
    temp_dir = tempfile.mkdtemp()

    try:
        file_path = os.path.join(temp_dir, "existing.py")

        with open(file_path, "w") as fh:
            fh.write("# existing\n")

        exit_code = write_generated_file(file_path, "# new\n", dry_run=False)

        if exit_code != EXIT_ERROR:
            errmsg = "Expected EXIT_ERROR, got {}.".format(exit_code)
            raise AssertionError(errmsg)
    finally:
        shutil.rmtree(temp_dir)

    return


def test_write_generated_file_dry_run_does_not_create():
    """
        Test that write_generated_file in dry-run mode does not
        create the file on disk.
    """
    temp_dir = tempfile.mkdtemp()

    try:
        file_path = os.path.join(temp_dir, "preview.py")
        content = "# preview content\n"

        exit_code = write_generated_file(file_path, content, dry_run=True)

        if exit_code != EXIT_SUCCESS:
            errmsg = "Expected EXIT_SUCCESS for dry run, got {}.".format(exit_code)
            raise AssertionError(errmsg)

        if os.path.exists(file_path) is True:
            errmsg = "File should not exist in dry-run mode."
            raise AssertionError(errmsg)
    finally:
        shutil.rmtree(temp_dir)

    return


# =============================================================================
# Unit Tests for GenerateEndpointCommand Class Attributes
# =============================================================================

def test_generate_endpoint_command_name():
    """
        Test that GenerateEndpointCommand has the correct name attribute.
    """
    cmd = GenerateEndpointCommand()

    if cmd.name != "endpoint":
        errmsg = "Expected name 'endpoint', got '{}'.".format(cmd.name)
        raise AssertionError(errmsg)

    return


def test_generate_endpoint_command_help():
    """
        Test that GenerateEndpointCommand has non-empty help text.
    """
    cmd = GenerateEndpointCommand()

    if len(cmd.help) == 0:
        errmsg = "Expected non-empty help text for GenerateEndpointCommand."
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for GenerateEndpointCommand.add_arguments
# =============================================================================

def test_endpoint_add_arguments_registers_name():
    """
        Test that add_arguments registers the name positional argument.
    """
    cmd = GenerateEndpointCommand()
    parser = ArgumentParser()
    cmd.add_arguments(parser)

    parsed = parser.parse_args(["user-profile"])

    if parsed.name != "user-profile":
        errmsg = "Expected name 'user-profile', got '{}'.".format(parsed.name)
        raise AssertionError(errmsg)

    return


def test_endpoint_add_arguments_registers_output_dir():
    """
        Test that add_arguments registers the --output-dir option.
    """
    cmd = GenerateEndpointCommand()
    parser = ArgumentParser()
    cmd.add_arguments(parser)

    parsed = parser.parse_args(["user-profile", "--output-dir", "/tmp/out"])

    if parsed.output_dir != "/tmp/out":
        errmsg = "Expected output_dir '/tmp/out', got '{}'.".format(parsed.output_dir)
        raise AssertionError(errmsg)

    return


def test_endpoint_add_arguments_registers_dry_run():
    """
        Test that add_arguments registers the --dry-run flag.
    """
    cmd = GenerateEndpointCommand()
    parser = ArgumentParser()
    cmd.add_arguments(parser)

    parsed = parser.parse_args(["user-profile", "--dry-run"])

    if parsed.dry_run is not True:
        errmsg = "Expected dry_run to be True."
        raise AssertionError(errmsg)

    return


def test_endpoint_add_arguments_dry_run_defaults_false():
    """
        Test that the --dry-run flag defaults to False.
    """
    cmd = GenerateEndpointCommand()
    parser = ArgumentParser()
    cmd.add_arguments(parser)

    parsed = parser.parse_args(["user-profile"])

    if parsed.dry_run is not False:
        errmsg = "Expected dry_run to default to False."
        raise AssertionError(errmsg)

    return


def test_endpoint_add_arguments_output_dir_defaults_to_dot():
    """
        Test that the --output-dir option defaults to the current directory.
    """
    cmd = GenerateEndpointCommand()
    parser = ArgumentParser()
    cmd.add_arguments(parser)

    parsed = parser.parse_args(["user-profile"])

    if parsed.output_dir != ".":
        errmsg = "Expected output_dir '.', got '{}'.".format(parsed.output_dir)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for GenerateEndpointCommand.execute
# =============================================================================

def test_endpoint_execute_creates_file():
    """
        Test that execute creates the endpoint file and returns EXIT_SUCCESS.
    """
    temp_dir = tempfile.mkdtemp()

    try:
        cmd = GenerateEndpointCommand()
        args = Namespace(name="user-profile", output_dir=temp_dir, dry_run=False)
        config = {}

        exit_code = cmd.execute(args, config)

        if exit_code != EXIT_SUCCESS:
            errmsg = "Expected EXIT_SUCCESS, got {}.".format(exit_code)
            raise AssertionError(errmsg)

        expected_path = os.path.join(temp_dir, "user_profile.py")
        if os.path.isfile(expected_path) is not True:
            errmsg = "Expected file 'user_profile.py' to be created."
            raise AssertionError(errmsg)

        with open(expected_path, "r") as fh:
            content = fh.read()

        if "def user_profile(request):" not in content:
            errmsg = "Expected endpoint function in generated file."
            raise AssertionError(errmsg)
    finally:
        shutil.rmtree(temp_dir)

    return


def test_endpoint_execute_dry_run():
    """
        Test that execute with --dry-run does not create the file.
    """
    temp_dir = tempfile.mkdtemp()

    try:
        cmd = GenerateEndpointCommand()
        args = Namespace(name="user-profile", output_dir=temp_dir, dry_run=True)
        config = {}

        exit_code = cmd.execute(args, config)

        if exit_code != EXIT_SUCCESS:
            errmsg = "Expected EXIT_SUCCESS for dry run, got {}.".format(exit_code)
            raise AssertionError(errmsg)

        expected_path = os.path.join(temp_dir, "user_profile.py")
        if os.path.exists(expected_path) is True:
            errmsg = "File should not exist in dry-run mode."
            raise AssertionError(errmsg)
    finally:
        shutil.rmtree(temp_dir)

    return


def test_endpoint_execute_returns_error_if_file_exists():
    """
        Test that execute returns EXIT_ERROR when the target file exists.
    """
    temp_dir = tempfile.mkdtemp()

    try:
        existing_path = os.path.join(temp_dir, "user_profile.py")
        with open(existing_path, "w") as fh:
            fh.write("# existing\n")

        cmd = GenerateEndpointCommand()
        args = Namespace(name="user-profile", output_dir=temp_dir, dry_run=False)
        config = {}

        exit_code = cmd.execute(args, config)

        if exit_code != EXIT_ERROR:
            errmsg = "Expected EXIT_ERROR, got {}.".format(exit_code)
            raise AssertionError(errmsg)
    finally:
        shutil.rmtree(temp_dir)

    return


# =============================================================================
# Unit Tests for GenerateBlueprintCommand Class Attributes
# =============================================================================

def test_generate_blueprint_command_name():
    """
        Test that GenerateBlueprintCommand has the correct name attribute.
    """
    cmd = GenerateBlueprintCommand()

    if cmd.name != "blueprint":
        errmsg = "Expected name 'blueprint', got '{}'.".format(cmd.name)
        raise AssertionError(errmsg)

    return


def test_generate_blueprint_command_help():
    """
        Test that GenerateBlueprintCommand has non-empty help text.
    """
    cmd = GenerateBlueprintCommand()

    if len(cmd.help) == 0:
        errmsg = "Expected non-empty help text for GenerateBlueprintCommand."
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for GenerateBlueprintCommand.add_arguments
# =============================================================================

def test_blueprint_add_arguments_registers_name():
    """
        Test that add_arguments registers the name positional argument.
    """
    cmd = GenerateBlueprintCommand()
    parser = ArgumentParser()
    cmd.add_arguments(parser)

    parsed = parser.parse_args(["user-management"])

    if parsed.name != "user-management":
        errmsg = "Expected name 'user-management', got '{}'.".format(parsed.name)
        raise AssertionError(errmsg)

    return


def test_blueprint_add_arguments_registers_output_dir():
    """
        Test that add_arguments registers the --output-dir option.
    """
    cmd = GenerateBlueprintCommand()
    parser = ArgumentParser()
    cmd.add_arguments(parser)

    parsed = parser.parse_args(["user-management", "--output-dir", "/tmp/bp"])

    if parsed.output_dir != "/tmp/bp":
        errmsg = "Expected output_dir '/tmp/bp', got '{}'.".format(parsed.output_dir)
        raise AssertionError(errmsg)

    return


def test_blueprint_add_arguments_registers_dry_run():
    """
        Test that add_arguments registers the --dry-run flag.
    """
    cmd = GenerateBlueprintCommand()
    parser = ArgumentParser()
    cmd.add_arguments(parser)

    parsed = parser.parse_args(["user-management", "--dry-run"])

    if parsed.dry_run is not True:
        errmsg = "Expected dry_run to be True."
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for GenerateBlueprintCommand.execute
# =============================================================================

def test_blueprint_execute_creates_file():
    """
        Test that execute creates the blueprint file and returns EXIT_SUCCESS.
    """
    temp_dir = tempfile.mkdtemp()

    try:
        cmd = GenerateBlueprintCommand()
        args = Namespace(name="user-management", output_dir=temp_dir, dry_run=False)
        config = {}

        exit_code = cmd.execute(args, config)

        if exit_code != EXIT_SUCCESS:
            errmsg = "Expected EXIT_SUCCESS, got {}.".format(exit_code)
            raise AssertionError(errmsg)

        expected_path = os.path.join(temp_dir, "user_management.py")
        if os.path.isfile(expected_path) is not True:
            errmsg = "Expected file 'user_management.py' to be created."
            raise AssertionError(errmsg)

        with open(expected_path, "r") as fh:
            content = fh.read()

        if "class UserManagementBlueprint:" not in content:
            errmsg = "Expected blueprint class in generated file."
            raise AssertionError(errmsg)
    finally:
        shutil.rmtree(temp_dir)

    return


def test_blueprint_execute_dry_run():
    """
        Test that execute with --dry-run does not create the file.
    """
    temp_dir = tempfile.mkdtemp()

    try:
        cmd = GenerateBlueprintCommand()
        args = Namespace(name="user-management", output_dir=temp_dir, dry_run=True)
        config = {}

        exit_code = cmd.execute(args, config)

        if exit_code != EXIT_SUCCESS:
            errmsg = "Expected EXIT_SUCCESS for dry run, got {}.".format(exit_code)
            raise AssertionError(errmsg)

        expected_path = os.path.join(temp_dir, "user_management.py")
        if os.path.exists(expected_path) is True:
            errmsg = "File should not exist in dry-run mode."
            raise AssertionError(errmsg)
    finally:
        shutil.rmtree(temp_dir)

    return


def test_blueprint_execute_returns_error_if_file_exists():
    """
        Test that execute returns EXIT_ERROR when the target file exists.
    """
    temp_dir = tempfile.mkdtemp()

    try:
        existing_path = os.path.join(temp_dir, "user_management.py")
        with open(existing_path, "w") as fh:
            fh.write("# existing\n")

        cmd = GenerateBlueprintCommand()
        args = Namespace(name="user-management", output_dir=temp_dir, dry_run=False)
        config = {}

        exit_code = cmd.execute(args, config)

        if exit_code != EXIT_ERROR:
            errmsg = "Expected EXIT_ERROR, got {}.".format(exit_code)
            raise AssertionError(errmsg)
    finally:
        shutil.rmtree(temp_dir)

    return
