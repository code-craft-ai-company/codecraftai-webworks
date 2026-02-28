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
import random
import string

from automojo.thisapp.persona import AppPersona
from automojo.webworks.persona import (
    establish_webapp_persona,
    reset_webapp_persona,
)


# =============================================================================
# Helper Functions for Generating Random Test Data
# =============================================================================

def generate_app_name():
    """Generate a random valid application name (lowercase alpha, 3-12 chars)."""
    length = random.randint(3, 12)
    return ''.join(random.choices(string.ascii_lowercase, k=length))


def generate_random_string(min_len=3, max_len=15):
    """Generate a random alphanumeric string suitable for persona values."""
    length = random.randint(min_len, max_len)
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


def generate_filename():
    """Generate a random filename without directory separators."""
    name = generate_random_string(3, 10)
    ext = random.choice([".config", ".ini", ".cfg", ".conf", ".settings"])
    return f"{name}{ext}"


def generate_absolute_path():
    """Generate a random absolute path for settings_file."""
    depth = random.randint(1, 4)
    parts = [generate_random_string(3, 8) for _ in range(depth)]
    filename = generate_filename()
    return os.path.join("/", *parts, filename)


def generate_relative_path_with_dirs():
    """Generate a random relative path that contains directory separators."""
    depth = random.randint(1, 3)
    parts = [generate_random_string(3, 8) for _ in range(depth)]
    filename = generate_filename()
    return os.path.join(*parts, filename)


def generate_home_relative_path():
    """Generate a path starting with ~ for home directory expansion."""
    depth = random.randint(1, 3)
    parts = [generate_random_string(3, 8) for _ in range(depth)]
    filename = generate_filename()
    return os.path.join("~", *parts, filename)


# =============================================================================
# Property 4: Absolute Path Preservation - Filename-only settings_file
# Feature: webapp-persona, Property 4: Absolute Path Preservation
# Validates: Requirements 2.8, 2.9
# =============================================================================

def test_property_filename_only_joined_with_presence_dir():
    """
        Property 4: Absolute Path Preservation

        For any settings_file that is just a filename (os.path.basename equals
        the full value), establish_webapp_persona SHALL join it with the
        resolved presence_dir.

        This test generates random bare filenames and verifies they are
        joined with the presence_dir across 100 iterations.

        **Feature: webapp-persona, Property 4: Absolute Path Preservation**
        **Validates: Requirement 2.8**
    """
    for iteration in range(100):
        app_name = generate_app_name()
        logger_name = f"logger_{generate_random_string()}"
        log_basename = f"logbase_{generate_random_string()}"
        bare_filename = generate_filename()

        # Randomly supply an explicit presence_dir or use the default
        use_explicit_presence = random.choice([True, False])

        if use_explicit_presence:
            presence_dir = f"/tmp/prop4test_{generate_random_string()}"
        else:
            presence_dir = None

        # Compute the expected presence_dir
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

            if actual_settings_file != expected_settings_file:
                errmsg = (
                    f"Iteration {iteration}: Filename-only settings_file not joined "
                    f"with presence_dir. bare_filename='{bare_filename}', "
                    f"presence_dir='{expected_presence_dir}', "
                    f"expected='{expected_settings_file}', got='{actual_settings_file}'"
                )
                raise AssertionError(errmsg)

        finally:
            reset_webapp_persona()

    return


def test_property_absolute_path_preserved_via_abspath():
    """
        Property 4: Absolute Path Preservation

        For any absolute path passed as settings_file to
        establish_webapp_persona, the resulting persona SHALL use the path
        resolved through os.path.abspath(os.path.expandvars(
        os.path.expanduser(settings_file))), which for clean absolute paths
        returns the path unchanged.

        This test generates random absolute paths and verifies they are
        preserved across 100 iterations.

        **Feature: webapp-persona, Property 4: Absolute Path Preservation**
        **Validates: Requirement 2.9**
    """
    for iteration in range(100):
        app_name = generate_app_name()
        logger_name = f"logger_{generate_random_string()}"
        log_basename = f"logbase_{generate_random_string()}"
        absolute_path = generate_absolute_path()

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

            if actual_settings_file != expected_settings_file:
                errmsg = (
                    f"Iteration {iteration}: Absolute path not preserved. "
                    f"input='{absolute_path}', expected='{expected_settings_file}', "
                    f"got='{actual_settings_file}'"
                )
                raise AssertionError(errmsg)

        finally:
            reset_webapp_persona()

    return


def test_property_relative_path_with_dirs_resolved():
    """
        Property 4: Absolute Path Preservation

        For any relative path containing directory separators passed as
        settings_file, establish_webapp_persona SHALL resolve it via
        os.path.abspath(os.path.expandvars(os.path.expanduser(
        settings_file))), converting it to an absolute path.

        This test generates random relative paths with directory components
        and verifies they are resolved to absolute paths across 100 iterations.

        **Feature: webapp-persona, Property 4: Absolute Path Preservation**
        **Validates: Requirement 2.9**
    """
    for iteration in range(100):
        app_name = generate_app_name()
        logger_name = f"logger_{generate_random_string()}"
        log_basename = f"logbase_{generate_random_string()}"
        relative_path = generate_relative_path_with_dirs()

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

            if actual_settings_file != expected_settings_file:
                errmsg = (
                    f"Iteration {iteration}: Relative path with dirs not resolved. "
                    f"input='{relative_path}', expected='{expected_settings_file}', "
                    f"got='{actual_settings_file}'"
                )
                raise AssertionError(errmsg)

        finally:
            reset_webapp_persona()

    return


def test_property_home_tilde_path_expanded():
    """
        Property 4: Absolute Path Preservation

        For any path starting with ~ passed as settings_file,
        establish_webapp_persona SHALL expand the home directory via
        os.path.expanduser and then resolve via os.path.abspath.

        This test generates random ~-prefixed paths and verifies they are
        expanded and resolved across 100 iterations.

        **Feature: webapp-persona, Property 4: Absolute Path Preservation**
        **Validates: Requirement 2.9**
    """
    for iteration in range(100):
        app_name = generate_app_name()
        logger_name = f"logger_{generate_random_string()}"
        log_basename = f"logbase_{generate_random_string()}"
        home_path = generate_home_relative_path()

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

            if actual_settings_file != expected_settings_file:
                errmsg = (
                    f"Iteration {iteration}: Home tilde path not expanded. "
                    f"input='{home_path}', expected='{expected_settings_file}', "
                    f"got='{actual_settings_file}'"
                )
                raise AssertionError(errmsg)

        finally:
            reset_webapp_persona()

    return
