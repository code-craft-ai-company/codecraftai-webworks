"""
.. module:: test_default_path_computation_properties
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Property-based tests for default path computation.

.. moduleauthor:: Code Craft AI LLC

This module contains property-based tests for the default path computation
logic in establish_webapp_persona, validating Property 3: Default Path
Computation across many generated inputs.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

import os

import ccai.testbase as testbase

from ccai.testbase.properties import given
from ccai.testbase.properties import strategies as st

from ccai.thisapp.persona import AppPersona
from ccai.webworks.webapplication import (
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


# =============================================================================
# Property 3: Default Path Computation - Presence Directory
# Feature: webapp-persona, Property 3: Default Path Computation
# Validates: Requirements 2.5, 2.6, 2.7
# =============================================================================

@given(
    app_name=app_name_strategy,
    suffix=random_string_strategy,
    constraints={"max_examples": 100},
)
def test_property_default_presence_dir(app_name, suffix):
    """
        Property 3: Default Path Computation

        For any application name, when establish_webapp_persona is called
        without an explicit presence_dir, the resolved presence_dir SHALL
        default to ~/<appname> (using os.path.join("~", name.lower())).

        **Feature: webapp-persona, Property 3: Default Path Computation**
        **Validates: Requirement 2.5**
    """
    logger_name = f"logger_{suffix}"
    log_basename = f"logbase_{suffix}"

    expected_presence_dir = os.path.join("~", app_name.lower())

    try:
        reset_webapp_persona()

        establish_webapp_persona(
            name=app_name,
            logger_name=logger_name,
            log_basename=log_basename,
        )

        actual_presence_dir = AppPersona.AM_PRESENCE_DIR

        testbase.assert_equal(
            actual_presence_dir, expected_presence_dir,
            f"Default presence_dir mismatch. name='{app_name}', "
            f"expected='{expected_presence_dir}', got='{actual_presence_dir}'"
        )

    finally:
        reset_webapp_persona()

    return


@given(
    app_name=app_name_strategy,
    suffix=random_string_strategy,
    use_explicit_presence=st.booleans(),
    presence_suffix=random_string_strategy,
    constraints={"max_examples": 100},
)
def test_property_default_log_directory(app_name, suffix, use_explicit_presence, presence_suffix):
    """
        Property 3: Default Path Computation

        For any application name, when establish_webapp_persona is called
        without an explicit log_directory, the resolved log_directory SHALL
        default to <presence_dir>/logs.

        **Feature: webapp-persona, Property 3: Default Path Computation**
        **Validates: Requirement 2.6**
    """
    logger_name = f"logger_{suffix}"
    log_basename = f"logbase_{suffix}"

    if use_explicit_presence:
        presence_dir = f"/tmp/prop3test_{presence_suffix}"
    else:
        presence_dir = None

    if presence_dir is not None:
        expected_presence_dir = presence_dir
    else:
        expected_presence_dir = os.path.join("~", app_name.lower())

    expected_log_directory = os.path.join(expected_presence_dir, "logs")

    try:
        reset_webapp_persona()

        kwargs = dict(
            name=app_name,
            logger_name=logger_name,
            log_basename=log_basename,
        )
        if presence_dir is not None:
            kwargs["presence_dir"] = presence_dir

        establish_webapp_persona(**kwargs)

        actual_log_directory = AppPersona.AM_LOG_DIRECTORY

        testbase.assert_equal(
            actual_log_directory, expected_log_directory,
            f"Default log_directory mismatch. name='{app_name}', "
            f"presence_dir='{expected_presence_dir}', "
            f"expected='{expected_log_directory}', got='{actual_log_directory}'"
        )

    finally:
        reset_webapp_persona()

    return


@given(
    app_name=app_name_strategy,
    suffix=random_string_strategy,
    use_explicit_presence=st.booleans(),
    presence_suffix=random_string_strategy,
    constraints={"max_examples": 100},
)
def test_property_default_settings_file(app_name, suffix, use_explicit_presence, presence_suffix):
    """
        Property 3: Default Path Computation

        For any application name, when establish_webapp_persona is called
        without an explicit settings_file, the resolved settings_file SHALL
        default to <presence_dir>/settings.config.

        **Feature: webapp-persona, Property 3: Default Path Computation**
        **Validates: Requirement 2.7**
    """
    logger_name = f"logger_{suffix}"
    log_basename = f"logbase_{suffix}"

    if use_explicit_presence:
        presence_dir = f"/tmp/prop3test_{presence_suffix}"
    else:
        presence_dir = None

    if presence_dir is not None:
        expected_presence_dir = presence_dir
    else:
        expected_presence_dir = os.path.join("~", app_name.lower())

    expected_settings_file = os.path.join(expected_presence_dir, "settings.config")

    try:
        reset_webapp_persona()

        kwargs = dict(
            name=app_name,
            logger_name=logger_name,
            log_basename=log_basename,
        )
        if presence_dir is not None:
            kwargs["presence_dir"] = presence_dir

        establish_webapp_persona(**kwargs)

        actual_settings_file = AppPersona.AM_SETTINGS_FILENAME

        testbase.assert_equal(
            actual_settings_file, expected_settings_file,
            f"Default settings_file mismatch. name='{app_name}', "
            f"presence_dir='{expected_presence_dir}', "
            f"expected='{expected_settings_file}', got='{actual_settings_file}'"
        )

    finally:
        reset_webapp_persona()

    return


@given(
    app_name=app_name_strategy,
    suffix=random_string_strategy,
    constraints={"max_examples": 100},
)
def test_property_all_defaults_consistent(app_name, suffix):
    """
        Property 3: Default Path Computation

        For any application name, when establish_webapp_persona is called
        with no optional path arguments, all three default paths SHALL be
        internally consistent: presence_dir = ~/<appname>,
        log_directory = <presence_dir>/logs,
        settings_file = <presence_dir>/settings.config.

        **Feature: webapp-persona, Property 3: Default Path Computation**
        **Validates: Requirements 2.5, 2.6, 2.7**
    """
    logger_name = f"logger_{suffix}"
    log_basename = f"logbase_{suffix}"

    expected_presence_dir = os.path.join("~", app_name.lower())
    expected_log_directory = os.path.join(expected_presence_dir, "logs")
    expected_settings_file = os.path.join(expected_presence_dir, "settings.config")

    try:
        reset_webapp_persona()

        establish_webapp_persona(
            name=app_name,
            logger_name=logger_name,
            log_basename=log_basename,
        )

        testbase.assert_equal(
            AppPersona.AM_PRESENCE_DIR, expected_presence_dir,
            f"presence_dir mismatch in consistency check. name='{app_name}', "
            f"expected='{expected_presence_dir}', got='{AppPersona.AM_PRESENCE_DIR}'"
        )

        testbase.assert_equal(
            AppPersona.AM_LOG_DIRECTORY, expected_log_directory,
            f"log_directory mismatch in consistency check. name='{app_name}', "
            f"expected='{expected_log_directory}', got='{AppPersona.AM_LOG_DIRECTORY}'"
        )

        testbase.assert_equal(
            AppPersona.AM_SETTINGS_FILENAME, expected_settings_file,
            f"settings_file mismatch in consistency check. name='{app_name}', "
            f"expected='{expected_settings_file}', got='{AppPersona.AM_SETTINGS_FILENAME}'"
        )

    finally:
        reset_webapp_persona()

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
