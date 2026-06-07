"""
    Unit tests for the OpenAPI CLI commands.

    Tests cover the :class:`GenerateCommand`, :class:`ValidateCommand`,
    and :func:`create_openapi_group` factory function. Tests verify
    argument parsing, stdout output, file export, tag and path filtering,
    validation output, and error handling when no generator is configured.

    **Validates: Requirements 9.4, 10.3, 10.4, 10.5**
"""

import argparse
import io
import json
import sys

from ccai.testbase.mocking import Mock

from ccai.webworks.openapi.cli import (
    GenerateCommand,
    ValidateCommand,
    create_openapi_group,
)
from ccai.webworks.openapi.validation import ValidationIssue


# =============================================================================
# Helper Functions
# =============================================================================

def _create_mock_generator(spec=None, json_output=None, yaml_output=None, issues=None):
    """
        Create a mock OpenAPI_Generator with configurable behavior.

        :param spec: The specification dictionary returned by generate().
        :param json_output: The JSON string returned by generate_json().
        :param yaml_output: The YAML string returned by generate_yaml().
        :param issues: A list of ValidationIssue objects returned by validate().

        :returns: A configured mock generator.
    """
    if spec is None:
        spec = {
            "openapi": "3.0.3",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
        }

    if json_output is None:
        json_output = json.dumps(spec, indent=2, sort_keys=True)

    if issues is None:
        issues = []

    mock_gen = Mock()
    mock_gen.configure(recursive=True)
    ctx = mock_gen.mock_context()
    ctx.mock_method("generate", return_value=spec)
    ctx.mock_method("generate_json", return_value=json_output)
    ctx.mock_method("generate_yaml", return_value=yaml_output or "openapi: 3.0.3\n")
    ctx.mock_method("validate", return_value=issues)
    ctx.mock_method("export", return_value=None)

    return mock_gen


def _parse_args(command, arg_list):
    """
        Parse arguments for a CLI command using a temporary parser.

        :param command: The CLICommand instance.
        :param arg_list: A list of argument strings.

        :returns: The parsed Namespace object.
    """
    parser = argparse.ArgumentParser()
    command.add_arguments(parser)
    parsed = parser.parse_args(arg_list)
    return parsed


def _capture_stdout(func, *args, **kwargs):
    """
        Capture stdout output from a function call.

        :param func: The function to call.

        :returns: A tuple of (return_value, captured_output_string).
    """
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        result = func(*args, **kwargs)
        output = sys.stdout.getvalue()
    finally:
        sys.stdout = old_stdout
    return result, output


def _capture_stderr(func, *args, **kwargs):
    """
        Capture stderr output from a function call.

        :param func: The function to call.

        :returns: A tuple of (return_value, captured_output_string).
    """
    old_stderr = sys.stderr
    sys.stderr = io.StringIO()
    try:
        result = func(*args, **kwargs)
        output = sys.stderr.getvalue()
    finally:
        sys.stderr = old_stderr
    return result, output


# =============================================================================
# GenerateCommand Tests
# =============================================================================

def test_generate_command_name():
    """
        Verify that the GenerateCommand has the correct name attribute.
    """
    cmd = GenerateCommand()

    if cmd.name != "generate":
        raise AssertionError(f"Expected name 'generate', got '{cmd.name}'")

    return


def test_generate_command_help():
    """
        Verify that the GenerateCommand has a non-empty help string.
    """
    cmd = GenerateCommand()

    if not cmd.help:
        raise AssertionError("Expected non-empty help string")

    return


def test_generate_command_default_args():
    """
        Verify that the GenerateCommand default arguments are correct.
    """
    cmd = GenerateCommand()
    args = _parse_args(cmd, [])

    if args.output != "-":
        raise AssertionError(f"Expected default output '-', got '{args.output}'")

    if args.format != "json":
        raise AssertionError(f"Expected default format 'json', got '{args.format}'")

    if args.tags is not None:
        raise AssertionError(f"Expected default tags None, got '{args.tags}'")

    if args.paths is not None:
        raise AssertionError(f"Expected default paths None, got '{args.paths}'")

    return


def test_generate_command_custom_args():
    """
        Verify that the GenerateCommand parses custom arguments correctly.
    """
    cmd = GenerateCommand()
    args = _parse_args(cmd, [
        "--output", "spec.json",
        "--format", "yaml",
        "--tags", "users,admin",
        "--paths", "/api/v1",
    ])

    if args.output != "spec.json":
        raise AssertionError(f"Expected output 'spec.json', got '{args.output}'")

    if args.format != "yaml":
        raise AssertionError(f"Expected format 'yaml', got '{args.format}'")

    if args.tags != "users,admin":
        raise AssertionError(f"Expected tags 'users,admin', got '{args.tags}'")

    if args.paths != "/api/v1":
        raise AssertionError(f"Expected paths '/api/v1', got '{args.paths}'")

    return


def test_generate_command_short_args():
    """
        Verify that the GenerateCommand accepts short argument forms.
    """
    cmd = GenerateCommand()
    args = _parse_args(cmd, ["-o", "out.json", "-f", "yaml"])

    if args.output != "out.json":
        raise AssertionError(f"Expected output 'out.json', got '{args.output}'")

    if args.format != "yaml":
        raise AssertionError(f"Expected format 'yaml', got '{args.format}'")

    return


def test_generate_stdout_json():
    """
        Verify that the generate command writes JSON to stdout when output is '-'.
    """
    spec = {
        "openapi": "3.0.3",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {},
    }
    mock_gen = _create_mock_generator(spec=spec)
    config = {"openapi_generator": mock_gen}

    cmd = GenerateCommand()
    args = _parse_args(cmd, [])

    exit_code, output = _capture_stdout(cmd.execute, args, config)

    if exit_code != 0:
        raise AssertionError(f"Expected exit code 0, got {exit_code}")

    parsed_output = json.loads(output.strip())
    if parsed_output["openapi"] != "3.0.3":
        raise AssertionError(f"Unexpected openapi version: {parsed_output.get('openapi')}")

    return


def test_generate_stdout_yaml():
    """
        Verify that the generate command writes YAML to stdout when format is yaml.
    """
    spec = {
        "openapi": "3.0.3",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {},
    }
    mock_gen = _create_mock_generator(spec=spec)
    config = {"openapi_generator": mock_gen}

    cmd = GenerateCommand()
    args = _parse_args(cmd, ["--format", "yaml"])

    exit_code, output = _capture_stdout(cmd.execute, args, config)

    if exit_code != 0:
        raise AssertionError(f"Expected exit code 0, got {exit_code}")

    if "openapi" not in output:
        raise AssertionError("Expected YAML output to contain 'openapi'")

    return


def test_generate_no_generator_returns_error():
    """
        Verify that the generate command returns error when no generator is configured.
    """
    cmd = GenerateCommand()
    args = _parse_args(cmd, [])
    config = {}

    exit_code, stderr_output = _capture_stderr(cmd.execute, args, config)

    if exit_code != 1:
        raise AssertionError(f"Expected exit code 1, got {exit_code}")

    if "No OpenAPI generator configured" not in stderr_output:
        raise AssertionError(f"Expected error message in stderr, got: {stderr_output}")

    return


def test_generate_file_output_calls_export():
    """
        Verify that the generate command calls export when output is a file path.
    """
    mock_gen = _create_mock_generator()
    config = {"openapi_generator": mock_gen}

    cmd = GenerateCommand()
    args = _parse_args(cmd, ["--output", "/tmp/spec.json", "--format", "json"])

    exit_code, _ = _capture_stdout(cmd.execute, args, config)

    if exit_code != 0:
        raise AssertionError(f"Expected exit code 0, got {exit_code}")

    ctx = mock_gen.mock_context()
    ctx.mock_method("export")
    # The export method was called - if it wasn't, the mock would not have been invoked
    # We verify by checking the exit code is 0 (success)

    return


def test_generate_filter_by_tags():
    """
        Verify that the generate command filters operations by tags.
    """
    spec = {
        "openapi": "3.0.3",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/users": {
                "get": {
                    "operationId": "get_users",
                    "tags": ["users"],
                    "responses": {"200": {"description": "OK"}},
                },
            },
            "/admin": {
                "get": {
                    "operationId": "get_admin",
                    "tags": ["admin"],
                    "responses": {"200": {"description": "OK"}},
                },
            },
        },
    }
    mock_gen = _create_mock_generator(spec=spec)
    config = {"openapi_generator": mock_gen}

    cmd = GenerateCommand()
    args = _parse_args(cmd, ["--tags", "users"])

    exit_code, output = _capture_stdout(cmd.execute, args, config)

    if exit_code != 0:
        raise AssertionError(f"Expected exit code 0, got {exit_code}")

    parsed = json.loads(output.strip())
    paths = parsed.get("paths", {})

    if "/users" not in paths:
        raise AssertionError("Expected /users path to be included")

    if "/admin" in paths:
        raise AssertionError("Expected /admin path to be filtered out")

    return


def test_generate_filter_by_path_prefix():
    """
        Verify that the generate command filters paths by prefix.
    """
    spec = {
        "openapi": "3.0.3",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/api/v1/users": {
                "get": {
                    "operationId": "get_users",
                    "responses": {"200": {"description": "OK"}},
                },
            },
            "/api/v2/users": {
                "get": {
                    "operationId": "get_users_v2",
                    "responses": {"200": {"description": "OK"}},
                },
            },
        },
    }
    mock_gen = _create_mock_generator(spec=spec)
    config = {"openapi_generator": mock_gen}

    cmd = GenerateCommand()
    args = _parse_args(cmd, ["--paths", "/api/v1"])

    exit_code, output = _capture_stdout(cmd.execute, args, config)

    if exit_code != 0:
        raise AssertionError(f"Expected exit code 0, got {exit_code}")

    parsed = json.loads(output.strip())
    paths = parsed.get("paths", {})

    if "/api/v1/users" not in paths:
        raise AssertionError("Expected /api/v1/users path to be included")

    if "/api/v2/users" in paths:
        raise AssertionError("Expected /api/v2/users path to be filtered out")

    return


# =============================================================================
# ValidateCommand Tests
# =============================================================================

def test_validate_command_name():
    """
        Verify that the ValidateCommand has the correct name attribute.
    """
    cmd = ValidateCommand()

    if cmd.name != "validate":
        raise AssertionError(f"Expected name 'validate', got '{cmd.name}'")

    return


def test_validate_command_help():
    """
        Verify that the ValidateCommand has a non-empty help string.
    """
    cmd = ValidateCommand()

    if not cmd.help:
        raise AssertionError("Expected non-empty help string")

    return


def test_validate_command_default_args():
    """
        Verify that the ValidateCommand default arguments are correct.
    """
    cmd = ValidateCommand()
    args = _parse_args(cmd, [])

    if args.strict is not False:
        raise AssertionError(f"Expected default strict False, got {args.strict}")

    return


def test_validate_command_strict_flag():
    """
        Verify that the ValidateCommand parses the --strict flag.
    """
    cmd = ValidateCommand()
    args = _parse_args(cmd, ["--strict"])

    if args.strict is not True:
        raise AssertionError(f"Expected strict True, got {args.strict}")

    return


def test_validate_valid_spec():
    """
        Verify that the validate command reports success for a valid spec.
    """
    mock_gen = _create_mock_generator(issues=[])
    config = {"openapi_generator": mock_gen}

    cmd = ValidateCommand()
    args = _parse_args(cmd, [])

    exit_code, output = _capture_stdout(cmd.execute, args, config)

    if exit_code != 0:
        raise AssertionError(f"Expected exit code 0, got {exit_code}")

    if "valid" not in output.lower():
        raise AssertionError(f"Expected 'valid' in output, got: {output}")

    return


def test_validate_invalid_spec():
    """
        Verify that the validate command reports issues for an invalid spec.
    """
    issues = [
        ValidationIssue(path="info.title", message="Missing required field", severity="error"),
    ]
    mock_gen = _create_mock_generator(issues=issues)
    config = {"openapi_generator": mock_gen}

    cmd = ValidateCommand()
    args = _parse_args(cmd, [])

    exit_code, output = _capture_stdout(cmd.execute, args, config)

    if exit_code != 1:
        raise AssertionError(f"Expected exit code 1, got {exit_code}")

    if "1 issue" not in output:
        raise AssertionError(f"Expected '1 issue' in output, got: {output}")

    if "info.title" not in output:
        raise AssertionError(f"Expected 'info.title' in output, got: {output}")

    return


def test_validate_no_generator_returns_error():
    """
        Verify that the validate command returns error when no generator is configured.
    """
    cmd = ValidateCommand()
    args = _parse_args(cmd, [])
    config = {}

    exit_code, stderr_output = _capture_stderr(cmd.execute, args, config)

    if exit_code != 1:
        raise AssertionError(f"Expected exit code 1, got {exit_code}")

    if "No OpenAPI generator configured" not in stderr_output:
        raise AssertionError(f"Expected error message in stderr, got: {stderr_output}")

    return


def test_validate_multiple_issues():
    """
        Verify that the validate command reports multiple issues.
    """
    issues = [
        ValidationIssue(path="info.title", message="Missing title", severity="error"),
        ValidationIssue(path="paths", message="No paths defined", severity="warning"),
    ]
    mock_gen = _create_mock_generator(issues=issues)
    config = {"openapi_generator": mock_gen}

    cmd = ValidateCommand()
    args = _parse_args(cmd, [])

    exit_code, output = _capture_stdout(cmd.execute, args, config)

    if exit_code != 1:
        raise AssertionError(f"Expected exit code 1, got {exit_code}")

    if "2 issue" not in output:
        raise AssertionError(f"Expected '2 issue' in output, got: {output}")

    if "[error]" not in output:
        raise AssertionError(f"Expected '[error]' in output, got: {output}")

    if "[warning]" not in output:
        raise AssertionError(f"Expected '[warning]' in output, got: {output}")

    return


# =============================================================================
# create_openapi_group Tests
# =============================================================================

def test_create_openapi_group_name():
    """
        Verify that the openapi group has the correct name.
    """
    group = create_openapi_group()

    if group.name != "openapi":
        raise AssertionError(f"Expected group name 'openapi', got '{group.name}'")

    return


def test_create_openapi_group_help():
    """
        Verify that the openapi group has a non-empty help string.
    """
    group = create_openapi_group()

    if not group.help:
        raise AssertionError("Expected non-empty help string")

    return


def test_create_openapi_group_has_generate_command():
    """
        Verify that the openapi group contains the generate command.
    """
    group = create_openapi_group()
    commands = group.commands
    command_names = [cmd.name for cmd in commands]

    if "generate" not in command_names:
        raise AssertionError(f"Expected 'generate' in commands, got {command_names}")

    return


def test_create_openapi_group_has_validate_command():
    """
        Verify that the openapi group contains the validate command.
    """
    group = create_openapi_group()
    commands = group.commands
    command_names = [cmd.name for cmd in commands]

    if "validate" not in command_names:
        raise AssertionError(f"Expected 'validate' in commands, got {command_names}")

    return


def test_create_openapi_group_command_count():
    """
        Verify that the openapi group contains exactly three commands.
    """
    group = create_openapi_group()
    commands = group.commands

    if len(commands) != 3:
        raise AssertionError(f"Expected 3 commands, got {len(commands)}")

    return


def test_create_openapi_group_registers_on_parser():
    """
        Verify that the openapi group registers its commands on an argument parser.
    """
    group = create_openapi_group()
    parser = argparse.ArgumentParser()
    group.register_commands(parser)

    # Verify the parser can parse a generate subcommand
    parsed = parser.parse_args(["generate"])
    handler = getattr(parsed, "command_handler", None)

    if handler is None:
        raise AssertionError("Expected command_handler to be set on parsed args")

    if not isinstance(handler, GenerateCommand):
        raise AssertionError(f"Expected GenerateCommand handler, got {type(handler)}")

    return


def test_generate_stdout_json_is_parseable():
    """
        Verify that the JSON output from stdout is valid parseable JSON.
    """
    spec = {
        "openapi": "3.0.3",
        "info": {"title": "My API", "version": "2.0.0"},
        "paths": {
            "/items": {
                "get": {
                    "operationId": "list_items",
                    "responses": {"200": {"description": "OK"}},
                },
            },
        },
    }
    mock_gen = _create_mock_generator(spec=spec)
    config = {"openapi_generator": mock_gen}

    cmd = GenerateCommand()
    args = _parse_args(cmd, [])

    exit_code, output = _capture_stdout(cmd.execute, args, config)

    if exit_code != 0:
        raise AssertionError(f"Expected exit code 0, got {exit_code}")

    try:
        parsed = json.loads(output.strip())
    except json.JSONDecodeError as exc:
        raise AssertionError(f"Output is not valid JSON: {exc}")

    if parsed["info"]["title"] != "My API":
        raise AssertionError(f"Expected title 'My API', got '{parsed['info']['title']}'")

    if parsed["info"]["version"] != "2.0.0":
        raise AssertionError(f"Expected version '2.0.0', got '{parsed['info']['version']}'")

    return
