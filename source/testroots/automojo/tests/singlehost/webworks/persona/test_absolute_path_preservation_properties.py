"""
.. module:: test_absolute_path_preservation_properties
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Property-based tests for absolute path preservation.

.. moduleauthor:: Automation Mojo LLC

This module contains property-based tests for the absolute path preservation
logic in establish_webapp_persona, validating Property 4: Absolute Path
Preservation across many generated inputs.

When settings_file is just a filename (basename equals the full value), it
SHALL be joined with presence_dir. When settings_file is a path (contains
directory separators), it SHALL be resolved via os.path.abspath(
os.path.expandvars(os.path.expanduser(settings_file))).
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

import os

import automojo.testbase as testbase

from automojo.testbase.properties import given
from automojo.testbase.properties import strategies as st
from automojo.testbase.properties.strategies import composite

from automojo.thisapp.persona import AppPersona
from automojo.webworks.webapplication import (
    establish_webapp_persona,
    reset_webapp_persona,
)


# =============================================================================
# Strategies for Generating Random Test Data
# =============================================================================

app_name_strategy = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz",
    min_size=3,
    max_size=12,
)

random_string_strategy = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789",
    min_size=3,
    max_size=15,
)

path_segment_strategy = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789",
    min_size=3,
    max_size=8,
)

extension_strategy = st.sampled_from([".config", ".ini", ".cfg", ".conf", ".settings"])


@composite
def filename_strategy(draw):
    """Generate a random filename without directory separators."""
    name = draw(path_segment_strategy)
    ext = draw(extension_strategy)
    return f"{name}{ext}"


@composite
def absolute_path_strategy(draw):
    """Generate a random absolute path for settings_file."""
    depth = draw(st.integers(1, 4))
    parts = [draw(path_segment_strategy) for _ in range(depth)]
    filename = draw(filename_strategy())
    return os.path.join("/", *parts, filename)


@composite
def relative_path_with_dirs_strategy(draw):
    """Generate a random relative path that contains directory separators."""
    depth = draw(st.integers(1, 3))
    parts = [draw(path_segment_strategy) for _ in range(depth)]
    filename = draw(filename_strategy())
    return os.path.join(*parts, filename)


@composite
def home_relative_path_strategy(draw):
    """Generate a path starting with ~ for home directory expansion."""
    depth = draw(st.integers(1, 3))
    parts = [draw(path_segment_strategy) for _ in range(depth)]
    filename = draw(filename_strategy())
    return os.path.join("~", *parts, filename)


# =============================================================================
# Property 4: Absolute Path Preservation - Filename-only settings_file
# Feature: webapp-persona, Property 4: Absolute Path Preservation
# Validates: Requirements 2.8, 2.9
# =============================================================================

@given(
    app_name=app_name_strategy,
    suffix=random_string_strategy,
    bare_filename=filename_strategy(),
    use_explicit_presence=st.booleans(),
    presence_suffix=random_string_strategy,
    constraints={"max_examples": 100},
)
def test_property_filename_only_joined_with_presence_dir(app_name, suffix, bare_filename, use_explicit_presence, presence_suffix):
    """
        Property 4: Absolute Path Preservation

        For any settings_file that is just a filename (os.path.basename equals
        the full value), establish_webapp_persona SHALL join it with the
        resolved presence_dir.

        **Feature: webapp-persona, Property 4: Absolute Path Preservation**
        **Validates: Requirement 2.8**
    """
    logger_name = f"logger_{suffix}"
    log_basename = f"logbase_{suffix}"

    if use_explicit_presence:
        presence_dir = f"/tmp/prop4test_{presence_suffix}"
    else:
        presence_dir = None

    if presence_dir is not None:
        expected_presence_dir = presence_dir
    else:
        expected_presence_dir = os.path.join("~", app_name.lower())

    expected_settings_file = os.path.join(expected_presence_dir, bare_filename)

    try:
        reset_webapp_persona()

        kwargs = dict(
            name=app_name,
            logger_name=logger_name,
            log_basename=log_basename,
            settings_file=bare_filename,
        )
        if presence_dir is not None:
            kwargs["presence_dir"] = presence_dir

        establish_webapp_persona(**kwargs)

        actual_settings_file = AppPersona.AM_SETTINGS_FILENAME

        testbase.assert_equal(
            actual_settings_file, expected_settings_file,
            f"Filename-only settings_file not joined with presence_dir. "
            f"bare_filename='{bare_filename}', presence_dir='{expected_presence_dir}', "
            f"expected='{expected_settings_file}', got='{actual_settings_file}'"
        )

    finally:
        reset_webapp_persona()

    return


@given(
    app_name=app_name_strategy,
    suffix=random_string_strategy,
    absolute_path=absolute_path_strategy(),
    constraints={"max_examples": 100},
)
def test_property_absolute_path_preserved_via_abspath(app_name, suffix, absolute_path):
    """
        Property 4: Absolute Path Preservation

        For any absolute path passed as settings_file to
        establish_webapp_persona, the resulting persona SHALL use the path
        resolved through os.path.abspath(os.path.expandvars(
        os.path.expanduser(settings_file))), which for clean absolute paths
        returns the path unchanged.

        **Feature: webapp-persona, Property 4: Absolute Path Preservation**
        **Validates: Requirement 2.9**
    """
    logger_name = f"logger_{suffix}"
    log_basename = f"logbase_{suffix}"

    expected_settings_file = os.path.abspath(
        os.path.expandvars(os.path.expanduser(absolute_path))
    )

    try:
        reset_webapp_persona()

        establish_webapp_persona(
            name=app_name,
            logger_name=logger_name,
            log_basename=log_basename,
            settings_file=absolute_path,
        )

        actual_settings_file = AppPersona.AM_SETTINGS_FILENAME

        testbase.assert_equal(
            actual_settings_file, expected_settings_file,
            f"Absolute path not preserved. input='{absolute_path}', "
            f"expected='{expected_settings_file}', got='{actual_settings_file}'"
        )

    finally:
        reset_webapp_persona()

    return


@given(
    app_name=app_name_strategy,
    suffix=random_string_strategy,
    relative_path=relative_path_with_dirs_strategy(),
    constraints={"max_examples": 100},
)
def test_property_relative_path_with_dirs_resolved(app_name, suffix, relative_path):
    """
        Property 4: Absolute Path Preservation

        For any relative path containing directory separators passed as
        settings_file, establish_webapp_persona SHALL resolve it via
        os.path.abspath(os.path.expandvars(os.path.expanduser(
        settings_file))), converting it to an absolute path.

        **Feature: webapp-persona, Property 4: Absolute Path Preservation**
        **Validates: Requirement 2.9**
    """
    logger_name = f"logger_{suffix}"
    log_basename = f"logbase_{suffix}"

    expected_settings_file = os.path.abspath(
        os.path.expandvars(os.path.expanduser(relative_path))
    )

    try:
        reset_webapp_persona()

        establish_webapp_persona(
            name=app_name,
            logger_name=logger_name,
            log_basename=log_basename,
            settings_file=relative_path,
        )

        actual_settings_file = AppPersona.AM_SETTINGS_FILENAME

        testbase.assert_equal(
            actual_settings_file, expected_settings_file,
            f"Relative path with dirs not resolved. input='{relative_path}', "
            f"expected='{expected_settings_file}', got='{actual_settings_file}'"
        )

    finally:
        reset_webapp_persona()

    return


@given(
    app_name=app_name_strategy,
    suffix=random_string_strategy,
    home_path=home_relative_path_strategy(),
    constraints={"max_examples": 100},
)
def test_property_home_tilde_path_expanded(app_name, suffix, home_path):
    """
        Property 4: Absolute Path Preservation

        For any path starting with ~ passed as settings_file,
        establish_webapp_persona SHALL expand the home directory via
        os.path.expanduser and then resolve via os.path.abspath.

        **Feature: webapp-persona, Property 4: Absolute Path Preservation**
        **Validates: Requirement 2.9**
    """
    logger_name = f"logger_{suffix}"
    log_basename = f"logbase_{suffix}"

    expected_settings_file = os.path.abspath(
        os.path.expandvars(os.path.expanduser(home_path))
    )

    try:
        reset_webapp_persona()

        establish_webapp_persona(
            name=app_name,
            logger_name=logger_name,
            log_basename=log_basename,
            settings_file=home_path,
        )

        actual_settings_file = AppPersona.AM_SETTINGS_FILENAME

        testbase.assert_equal(
            actual_settings_file, expected_settings_file,
            f"Home tilde path not expanded. input='{home_path}', "
            f"expected='{expected_settings_file}', got='{actual_settings_file}'"
        )

    finally:
        reset_webapp_persona()

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
