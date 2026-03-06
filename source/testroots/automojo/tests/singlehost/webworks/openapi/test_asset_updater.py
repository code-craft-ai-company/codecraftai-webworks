"""
    Unit tests for the AssetUpdater class in the OpenAPI assets module.

    This module tests the AssetUpdater class including GitHub API parsing,
    file downloading with checksum computation, manifest writing, and the
    high-level update methods for Swagger UI and ReDoc. All HTTP calls are
    mocked to avoid network access during testing.

    **Validates: Requirements 7.4, 7.5, 7.6**
"""

import hashlib
import json
import os
import shutil
import tempfile

from automojo.testbase.mocking import Mock, create_module_patch

from automojo.webworks.openapi.assets import AssetUpdater


# =============================================================================
# Helper Functions
# =============================================================================

def _create_temp_static_dir():
    """
        Create a temporary directory structure mimicking the static asset layout.

        :returns: The path to the temporary static directory.
    """
    temp_dir = tempfile.mkdtemp(prefix="test_asset_updater_")
    os.makedirs(os.path.join(temp_dir, "swagger-ui"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "redoc"), exist_ok=True)

    return temp_dir


def _cleanup_temp_dir(temp_dir):
    """
        Remove a temporary directory and all its contents.

        :param temp_dir: Path to the temporary directory.
    """
    if os.path.isdir(temp_dir):
        shutil.rmtree(temp_dir)

    return


def _create_mock_response(status_code, content=None, json_data=None):
    """
        Create a mock HTTP response object.

        :param status_code: The HTTP status code.
        :param content: The binary content for the response body.
        :param json_data: The JSON data to return from .json().

        :returns: A configured mock response.
    """
    mock_resp = Mock()
    mock_resp.configure(recursive=True)
    ctx = mock_resp.mock_context()
    ctx.set_attribute("status_code", status_code)

    if content is not None:
        ctx.set_attribute("content", content)

    if json_data is not None:
        ctx.mock_method("json", return_value=json_data)

    return mock_resp


# =============================================================================
# Unit Tests for AssetUpdater Initialization
# =============================================================================

def test_asset_updater_creates_with_default_static_dir():
    """
        Verify that AssetUpdater can be instantiated with the default
        static directory.
    """
    updater = AssetUpdater()

    assert updater is not None
    assert updater._static_dir.endswith("static")

    return


def test_asset_updater_creates_with_custom_static_dir():
    """
        Verify that AssetUpdater accepts a custom static directory path.
    """
    temp_dir = _create_temp_static_dir()

    try:
        updater = AssetUpdater(static_dir=temp_dir)

        if updater._static_dir != temp_dir:
            raise AssertionError(
                "Expected static_dir '{}', got '{}'".format(temp_dir, updater._static_dir)
            )
    finally:
        _cleanup_temp_dir(temp_dir)

    return


# =============================================================================
# Unit Tests for _get_latest_release
# =============================================================================

def test_get_latest_release_parses_github_api_response():
    """
        Verify that _get_latest_release correctly parses the GitHub API
        response and strips the leading 'v' from the tag name.
    """
    import requests

    mock_response = _create_mock_response(
        status_code=200,
        json_data={"tag_name": "v5.18.2"}
    )

    patch = create_module_patch(requests, "get", recursive=True)
    mock_get = patch.activate()
    mock_get.configure(return_value=mock_response)

    try:
        updater = AssetUpdater()
        version = updater._get_latest_release("swagger-api/swagger-ui")

        if version != "5.18.2":
            raise AssertionError(
                "Expected version '5.18.2', got '{}'".format(version)
            )
    finally:
        patch.deactivate()

    return


def test_get_latest_release_handles_tag_without_v_prefix():
    """
        Verify that _get_latest_release handles tag names that do not
        have a leading 'v' prefix.
    """
    import requests

    mock_response = _create_mock_response(
        status_code=200,
        json_data={"tag_name": "2.1.5"}
    )

    patch = create_module_patch(requests, "get", recursive=True)
    mock_get = patch.activate()
    mock_get.configure(return_value=mock_response)

    try:
        updater = AssetUpdater()
        version = updater._get_latest_release("Redocly/redoc")

        if version != "2.1.5":
            raise AssertionError(
                "Expected version '2.1.5', got '{}'".format(version)
            )
    finally:
        patch.deactivate()

    return


def test_get_latest_release_raises_on_http_error():
    """
        Verify that _get_latest_release raises RuntimeError when the
        GitHub API returns a non-200 status code.
    """
    import requests

    mock_response = _create_mock_response(status_code=403)

    patch = create_module_patch(requests, "get", recursive=True)
    mock_get = patch.activate()
    mock_get.configure(return_value=mock_response)

    try:
        updater = AssetUpdater()
        raised = False

        try:
            updater._get_latest_release("swagger-api/swagger-ui")
        except RuntimeError:
            raised = True

        if raised is not True:
            raise AssertionError("Expected RuntimeError to be raised")
    finally:
        patch.deactivate()

    return


# =============================================================================
# Unit Tests for _download_file
# =============================================================================

def test_download_file_computes_correct_sha256():
    """
        Verify that _download_file writes the file and returns the
        correct SHA-256 checksum.
    """
    import requests

    file_content = b"Hello, this is test content for checksum verification."
    expected_sha = hashlib.sha256(file_content).hexdigest()

    mock_response = _create_mock_response(
        status_code=200,
        content=file_content
    )

    patch = create_module_patch(requests, "get", recursive=True)
    mock_get = patch.activate()
    mock_get.configure(return_value=mock_response)

    temp_dir = _create_temp_static_dir()

    try:
        updater = AssetUpdater(static_dir=temp_dir)
        dest_path = os.path.join(temp_dir, "test_file.js")
        checksum = updater._download_file(
            url="https://example.com/test_file.js",
            dest=dest_path
        )

        if checksum != expected_sha:
            raise AssertionError(
                "Expected checksum '{}', got '{}'".format(expected_sha, checksum)
            )

        if not os.path.isfile(dest_path):
            raise AssertionError("Expected file to be written at '{}'".format(dest_path))

        with open(dest_path, "rb") as fh:
            written_content = fh.read()

        if written_content != file_content:
            raise AssertionError("Written file content does not match downloaded content")
    finally:
        patch.deactivate()
        _cleanup_temp_dir(temp_dir)

    return


def test_download_file_raises_on_http_error():
    """
        Verify that _download_file raises RuntimeError when the HTTP
        response has a non-200 status code.
    """
    import requests

    mock_response = _create_mock_response(status_code=404)

    patch = create_module_patch(requests, "get", recursive=True)
    mock_get = patch.activate()
    mock_get.configure(return_value=mock_response)

    temp_dir = _create_temp_static_dir()

    try:
        updater = AssetUpdater(static_dir=temp_dir)
        dest_path = os.path.join(temp_dir, "missing_file.js")
        raised = False

        try:
            updater._download_file(
                url="https://example.com/missing_file.js",
                dest=dest_path
            )
        except RuntimeError:
            raised = True

        if raised is not True:
            raise AssertionError("Expected RuntimeError to be raised")
    finally:
        patch.deactivate()
        _cleanup_temp_dir(temp_dir)

    return


# =============================================================================
# Unit Tests for _update_manifest
# =============================================================================

def test_update_manifest_writes_valid_json():
    """
        Verify that _update_manifest writes a valid JSON file with the
        correct structure.
    """
    temp_dir = _create_temp_static_dir()

    try:
        updater = AssetUpdater(static_dir=temp_dir)

        files_info = {
            "swagger-ui-bundle.js": {
                "url": "https://example.com/swagger-ui-bundle.js",
                "sha256": "abc123def456",
            },
        }

        updater._update_manifest(
            group="swagger-ui",
            version="5.18.2",
            files=files_info
        )

        manifest_path = os.path.join(temp_dir, "manifest.json")

        if not os.path.isfile(manifest_path):
            raise AssertionError("Expected manifest.json to be created")

        with open(manifest_path, "r", encoding="utf-8") as mf:
            manifest = json.load(mf)

        if "swagger-ui" not in manifest:
            raise AssertionError("Expected 'swagger-ui' key in manifest")

        swagger_data = manifest["swagger-ui"]

        if swagger_data.get("version") != "5.18.2":
            raise AssertionError(
                "Expected version '5.18.2', got '{}'".format(swagger_data.get("version"))
            )

        if "files" not in swagger_data:
            raise AssertionError("Expected 'files' key in swagger-ui data")

        if "swagger-ui-bundle.js" not in swagger_data["files"]:
            raise AssertionError("Expected 'swagger-ui-bundle.js' in files")

        file_entry = swagger_data["files"]["swagger-ui-bundle.js"]

        if file_entry.get("sha256") != "abc123def456":
            raise AssertionError(
                "Expected sha256 'abc123def456', got '{}'".format(file_entry.get("sha256"))
            )
    finally:
        _cleanup_temp_dir(temp_dir)

    return


def test_update_manifest_preserves_existing_groups():
    """
        Verify that _update_manifest preserves existing groups when
        updating a single group.
    """
    temp_dir = _create_temp_static_dir()

    try:
        # Write an initial manifest with a redoc entry
        manifest_path = os.path.join(temp_dir, "manifest.json")
        initial_manifest = {
            "redoc": {
                "version": "2.1.5",
                "files": {
                    "redoc.standalone.js": {
                        "url": "https://example.com/redoc.standalone.js",
                        "sha256": "existing_checksum",
                    },
                },
            },
        }
        with open(manifest_path, "w", encoding="utf-8") as mf:
            json.dump(initial_manifest, mf)

        updater = AssetUpdater(static_dir=temp_dir)

        swagger_files = {
            "swagger-ui-bundle.js": {
                "url": "https://example.com/swagger-ui-bundle.js",
                "sha256": "new_checksum",
            },
        }

        updater._update_manifest(
            group="swagger-ui",
            version="5.18.2",
            files=swagger_files
        )

        with open(manifest_path, "r", encoding="utf-8") as mf:
            manifest = json.load(mf)

        if "redoc" not in manifest:
            raise AssertionError("Expected existing 'redoc' group to be preserved")

        if manifest["redoc"]["version"] != "2.1.5":
            raise AssertionError("Expected redoc version to remain '2.1.5'")

        if "swagger-ui" not in manifest:
            raise AssertionError("Expected 'swagger-ui' group to be added")

        if manifest["swagger-ui"]["version"] != "5.18.2":
            raise AssertionError("Expected swagger-ui version '5.18.2'")
    finally:
        _cleanup_temp_dir(temp_dir)

    return


def test_update_manifest_overwrites_existing_group():
    """
        Verify that _update_manifest overwrites an existing group entry
        with the new version and files.
    """
    temp_dir = _create_temp_static_dir()

    try:
        manifest_path = os.path.join(temp_dir, "manifest.json")
        initial_manifest = {
            "swagger-ui": {
                "version": "5.17.0",
                "files": {
                    "swagger-ui-bundle.js": {
                        "url": "https://example.com/old.js",
                        "sha256": "old_checksum",
                    },
                },
            },
        }
        with open(manifest_path, "w", encoding="utf-8") as mf:
            json.dump(initial_manifest, mf)

        updater = AssetUpdater(static_dir=temp_dir)

        new_files = {
            "swagger-ui-bundle.js": {
                "url": "https://example.com/new.js",
                "sha256": "new_checksum",
            },
        }

        updater._update_manifest(
            group="swagger-ui",
            version="5.18.2",
            files=new_files
        )

        with open(manifest_path, "r", encoding="utf-8") as mf:
            manifest = json.load(mf)

        swagger_data = manifest["swagger-ui"]

        if swagger_data["version"] != "5.18.2":
            raise AssertionError(
                "Expected version '5.18.2', got '{}'".format(swagger_data["version"])
            )

        if swagger_data["files"]["swagger-ui-bundle.js"]["sha256"] != "new_checksum":
            raise AssertionError("Expected sha256 to be updated to 'new_checksum'")
    finally:
        _cleanup_temp_dir(temp_dir)

    return


# =============================================================================
# Unit Tests for update_swagger_ui
# =============================================================================

def test_update_swagger_ui_downloads_all_expected_files():
    """
        Verify that update_swagger_ui downloads all expected Swagger UI
        files and returns a summary with version and checksums.
    """
    import requests

    temp_dir = _create_temp_static_dir()

    js_content = b"// swagger-ui-bundle.js content"
    css_content = b"/* swagger-ui.css content */"
    png_content = b"\x89PNG\r\n\x1a\n fake png data"

    call_index = [0]
    responses = [
        _create_mock_response(status_code=200, content=js_content),
        _create_mock_response(status_code=200, content=css_content),
        _create_mock_response(status_code=200, content=png_content),
    ]

    def get_side_effect(*args, **kwargs):
        idx = call_index[0]
        call_index[0] += 1
        if idx < len(responses):
            rtnval = responses[idx]
        else:
            rtnval = _create_mock_response(status_code=404)
        return rtnval

    patch = create_module_patch(requests, "get", recursive=True)
    mock_get = patch.activate()
    mock_get.configure(side_effect=get_side_effect)

    try:
        updater = AssetUpdater(static_dir=temp_dir)
        result = updater.update_swagger_ui(version="5.18.2")

        if result["version"] != "5.18.2":
            raise AssertionError(
                "Expected version '5.18.2', got '{}'".format(result["version"])
            )

        expected_files = ["swagger-ui-bundle.js", "swagger-ui.css", "favicon-32x32.png"]
        for fname in expected_files:
            if fname not in result["files"]:
                raise AssertionError(
                    "Expected '{}' in result files".format(fname)
                )

            file_path = os.path.join(temp_dir, "swagger-ui", fname)
            if not os.path.isfile(file_path):
                raise AssertionError(
                    "Expected file to exist at '{}'".format(file_path)
                )

        # Verify checksums match expected content
        js_sha = hashlib.sha256(js_content).hexdigest()
        if result["files"]["swagger-ui-bundle.js"]["sha256"] != js_sha:
            raise AssertionError("Checksum mismatch for swagger-ui-bundle.js")

        css_sha = hashlib.sha256(css_content).hexdigest()
        if result["files"]["swagger-ui.css"]["sha256"] != css_sha:
            raise AssertionError("Checksum mismatch for swagger-ui.css")

        # Verify manifest was updated
        manifest_path = os.path.join(temp_dir, "manifest.json")
        if not os.path.isfile(manifest_path):
            raise AssertionError("Expected manifest.json to be created")

        with open(manifest_path, "r", encoding="utf-8") as mf:
            manifest = json.load(mf)

        if "swagger-ui" not in manifest:
            raise AssertionError("Expected 'swagger-ui' in manifest")

        if manifest["swagger-ui"]["version"] != "5.18.2":
            raise AssertionError("Expected manifest version '5.18.2'")
    finally:
        patch.deactivate()
        _cleanup_temp_dir(temp_dir)

    return


# =============================================================================
# Unit Tests for update_redoc
# =============================================================================

def test_update_redoc_downloads_expected_file():
    """
        Verify that update_redoc downloads the ReDoc standalone bundle
        and returns a summary with version and checksum.
    """
    import requests

    temp_dir = _create_temp_static_dir()

    js_content = b"// redoc.standalone.js content"

    mock_response = _create_mock_response(
        status_code=200,
        content=js_content
    )

    patch = create_module_patch(requests, "get", recursive=True)
    mock_get = patch.activate()
    mock_get.configure(return_value=mock_response)

    try:
        updater = AssetUpdater(static_dir=temp_dir)
        result = updater.update_redoc(version="2.1.5")

        if result["version"] != "2.1.5":
            raise AssertionError(
                "Expected version '2.1.5', got '{}'".format(result["version"])
            )

        if "redoc.standalone.js" not in result["files"]:
            raise AssertionError("Expected 'redoc.standalone.js' in result files")

        file_path = os.path.join(temp_dir, "redoc", "redoc.standalone.js")
        if not os.path.isfile(file_path):
            raise AssertionError(
                "Expected file to exist at '{}'".format(file_path)
            )

        expected_sha = hashlib.sha256(js_content).hexdigest()
        actual_sha = result["files"]["redoc.standalone.js"]["sha256"]
        if actual_sha != expected_sha:
            raise AssertionError(
                "Expected sha256 '{}', got '{}'".format(expected_sha, actual_sha)
            )

        # Verify manifest was updated
        manifest_path = os.path.join(temp_dir, "manifest.json")
        if not os.path.isfile(manifest_path):
            raise AssertionError("Expected manifest.json to be created")

        with open(manifest_path, "r", encoding="utf-8") as mf:
            manifest = json.load(mf)

        if "redoc" not in manifest:
            raise AssertionError("Expected 'redoc' in manifest")

        if manifest["redoc"]["version"] != "2.1.5":
            raise AssertionError("Expected manifest version '2.1.5'")
    finally:
        patch.deactivate()
        _cleanup_temp_dir(temp_dir)

    return


# =============================================================================
# Unit Tests for update_swagger_ui with latest version resolution
# =============================================================================

def test_update_swagger_ui_resolves_latest_version():
    """
        Verify that update_swagger_ui queries GitHub for the latest
        version when no version is specified.
    """
    import requests

    temp_dir = _create_temp_static_dir()

    js_content = b"// bundle content"
    css_content = b"/* css content */"
    png_content = b"\x89PNG fake"

    # First call: GitHub API for latest release
    # Subsequent calls: file downloads
    call_index = [0]
    github_response = _create_mock_response(
        status_code=200,
        json_data={"tag_name": "v5.20.0"}
    )
    file_responses = [
        _create_mock_response(status_code=200, content=js_content),
        _create_mock_response(status_code=200, content=css_content),
        _create_mock_response(status_code=200, content=png_content),
    ]

    def get_side_effect(*args, **kwargs):
        idx = call_index[0]
        call_index[0] += 1
        if idx == 0:
            rtnval = github_response
        elif idx - 1 < len(file_responses):
            rtnval = file_responses[idx - 1]
        else:
            rtnval = _create_mock_response(status_code=404)
        return rtnval

    patch = create_module_patch(requests, "get", recursive=True)
    mock_get = patch.activate()
    mock_get.configure(side_effect=get_side_effect)

    try:
        updater = AssetUpdater(static_dir=temp_dir)
        result = updater.update_swagger_ui(version=None)

        if result["version"] != "5.20.0":
            raise AssertionError(
                "Expected version '5.20.0', got '{}'".format(result["version"])
            )
    finally:
        patch.deactivate()
        _cleanup_temp_dir(temp_dir)

    return


# =============================================================================
# Unit Tests for UpdateAssetsCommand
# =============================================================================

def test_update_assets_command_name():
    """
        Verify that the UpdateAssetsCommand has the correct name attribute.
    """
    from automojo.webworks.openapi.cli import UpdateAssetsCommand

    cmd = UpdateAssetsCommand()

    if cmd.name != "update-assets":
        raise AssertionError(
            "Expected name 'update-assets', got '{}'".format(cmd.name)
        )

    return


def test_update_assets_command_help():
    """
        Verify that the UpdateAssetsCommand has a non-empty help string.
    """
    from automojo.webworks.openapi.cli import UpdateAssetsCommand

    cmd = UpdateAssetsCommand()

    if not cmd.help:
        raise AssertionError("Expected non-empty help string")

    return


def test_update_assets_command_default_args():
    """
        Verify that the UpdateAssetsCommand default arguments are correct.
    """
    import argparse
    from automojo.webworks.openapi.cli import UpdateAssetsCommand

    cmd = UpdateAssetsCommand()
    parser = argparse.ArgumentParser()
    cmd.add_arguments(parser)
    args = parser.parse_args([])

    if args.swagger_version is not None:
        raise AssertionError(
            "Expected default swagger_version None, got '{}'".format(args.swagger_version)
        )

    if args.redoc_version is not None:
        raise AssertionError(
            "Expected default redoc_version None, got '{}'".format(args.redoc_version)
        )

    return


def test_update_assets_command_custom_args():
    """
        Verify that the UpdateAssetsCommand parses custom version arguments.
    """
    import argparse
    from automojo.webworks.openapi.cli import UpdateAssetsCommand

    cmd = UpdateAssetsCommand()
    parser = argparse.ArgumentParser()
    cmd.add_arguments(parser)
    args = parser.parse_args(["--swagger-version", "5.18.2", "--redoc-version", "2.1.5"])

    if args.swagger_version != "5.18.2":
        raise AssertionError(
            "Expected swagger_version '5.18.2', got '{}'".format(args.swagger_version)
        )

    if args.redoc_version != "2.1.5":
        raise AssertionError(
            "Expected redoc_version '2.1.5', got '{}'".format(args.redoc_version)
        )

    return


def test_create_openapi_group_has_update_assets_command():
    """
        Verify that the openapi group contains the update-assets command.
    """
    from automojo.webworks.openapi.cli import create_openapi_group

    group = create_openapi_group()
    commands = group.commands
    command_names = [cmd.name for cmd in commands]

    if "update-assets" not in command_names:
        raise AssertionError(
            "Expected 'update-assets' in commands, got {}".format(command_names)
        )

    return


def test_create_openapi_group_has_three_commands():
    """
        Verify that the openapi group now contains three commands
        (generate, validate, update-assets).
    """
    from automojo.webworks.openapi.cli import create_openapi_group

    group = create_openapi_group()
    commands = group.commands

    if len(commands) != 3:
        raise AssertionError(
            "Expected 3 commands, got {}".format(len(commands))
        )

    return
