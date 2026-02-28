"""
.. module:: test_default_path_computation_properties
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Property-based tests for default path computation.

.. moduleauthor:: Automation Mojo LLC

This module contains property-based tests for the default path computation
logic in establish_webapp_persona, validating Property 3: Default Path
Computation across many generated inputs.
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


# =============================================================================
# Property 3: Default Path Computation - Presence Directory
# Feature: webapp-persona, Property 3: Default Path Computation
# Validates: Requirements 2.5, 2.6, 2.7
# =============================================================================

def test_property_default_presence_dir():
    """
        Property 3: Default Path Computation

        For any application name, when establish_webapp_persona is called
        without an explicit presence_dir, the resolved presence_dir SHALL
        default to ~/<appname> (using os.path.join("~", name.lower())).

        This test generates random application names and verifies the
        default presence_dir computation across 100 iterations.

        **Feature: webapp-persona, Property 3: Default Path Computation**
        **Validates: Requirement 2.5**
    """
    for iteration in range(100):
        app_name = generate_app_name()
        logger_name = f"logger_{generate_random_string()}"
        log_basename = f"logbase_{generate_random_string()}"

        expected_presence_dir = os.path.join("~", app_name.lower())

        try:
            reset_webapp_persona()

            app = establish_webapp_persona(
                name=app_name,
                logger_name=logger_name,
                log_basename=log_basename,
                # presence_dir intentionally omitted
            )

            actual_presence_dir = AppPersona.AM_PRESENCE_DIR

            if actual_presence_dir != expected_presence_dir:
                errmsg = (
                    f"Iteration {iteration}: Default presence_dir mismatch. "
                    f"name='{app_name}', expected='{expected_presence_dir}', "
                    f"got='{actual_presence_dir}'"
                )
                raise AssertionError(errmsg)

        finally:
            reset_webapp_persona()

    return


def test_property_default_log_directory():
    """
        Property 3: Default Path Computation

        For any application name, when establish_webapp_persona is called
        without an explicit log_directory, the resolved log_directory SHALL
        default to <presence_dir>/logs.

        This test generates random application names with both default and
        explicit presence_dir values, verifying the default log_directory
        computation across 100 iterations.

        **Feature: webapp-persona, Property 3: Default Path Computation**
        **Validates: Requirement 2.6**
    """
    for iteration in range(100):
        app_name = generate_app_name()
        logger_name = f"logger_{generate_random_string()}"
        log_basename = f"logbase_{generate_random_string()}"

        # Randomly decide whether to supply an explicit presence_dir
        use_explicit_presence = random.choice([True, False])

        if use_explicit_presence:
            presence_dir = f"/tmp/prop3test_{generate_random_string()}"
        else:
            presence_dir = None

        # Compute the expected presence_dir for deriving log_directory
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
                # log_directory intentionally omitted
            )
            if presence_dir is not None:
                kwargs["presence_dir"] = presence_dir

            app = establish_webapp_persona(**kwargs)

            actual_log_directory = AppPersona.AM_LOG_DIRECTORY

            if actual_log_directory != expected_log_directory:
                errmsg = (
                    f"Iteration {iteration}: Default log_directory mismatch. "
                    f"name='{app_name}', presence_dir='{expected_presence_dir}', "
                    f"expected='{expected_log_directory}', got='{actual_log_directory}'"
                )
                raise AssertionError(errmsg)

        finally:
            reset_webapp_persona()

    return


def test_property_default_settings_file():
    """
        Property 3: Default Path Computation

        For any application name, when establish_webapp_persona is called
        without an explicit settings_file, the resolved settings_file SHALL
        default to <presence_dir>/settings.config.

        This test generates random application names with both default and
        explicit presence_dir values, verifying the default settings_file
        computation across 100 iterations.

        **Feature: webapp-persona, Property 3: Default Path Computation**
        **Validates: Requirement 2.7**
    """
    for iteration in range(100):
        app_name = generate_app_name()
        logger_name = f"logger_{generate_random_string()}"
        log_basename = f"logbase_{generate_random_string()}"

        # Randomly decide whether to supply an explicit presence_dir
        use_explicit_presence = random.choice([True, False])

        if use_explicit_presence:
            presence_dir = f"/tmp/prop3test_{generate_random_string()}"
        else:
            presence_dir = None

        # Compute the expected presence_dir for deriving settings_file
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
                # settings_file intentionally omitted
            )
            if presence_dir is not None:
                kwargs["presence_dir"] = presence_dir

            app = establish_webapp_persona(**kwargs)

            actual_settings_file = AppPersona.AM_SETTINGS_FILENAME

            if actual_settings_file != expected_settings_file:
                errmsg = (
                    f"Iteration {iteration}: Default settings_file mismatch. "
                    f"name='{app_name}', presence_dir='{expected_presence_dir}', "
                    f"expected='{expected_settings_file}', got='{actual_settings_file}'"
                )
                raise AssertionError(errmsg)

        finally:
            reset_webapp_persona()

    return


def test_property_all_defaults_consistent():
    """
        Property 3: Default Path Computation

        For any application name, when establish_webapp_persona is called
        with no optional path arguments, all three default paths SHALL be
        internally consistent: presence_dir = ~/<appname>,
        log_directory = <presence_dir>/logs,
        settings_file = <presence_dir>/settings.config.

        This test verifies the consistency of all three default paths
        together across 100 iterations.

        **Feature: webapp-persona, Property 3: Default Path Computation**
        **Validates: Requirements 2.5, 2.6, 2.7**
    """
    for iteration in range(100):
        app_name = generate_app_name()
        logger_name = f"logger_{generate_random_string()}"
        log_basename = f"logbase_{generate_random_string()}"

        expected_presence_dir = os.path.join("~", app_name.lower())
        expected_log_directory = os.path.join(expected_presence_dir, "logs")
        expected_settings_file = os.path.join(expected_presence_dir, "settings.config")

        try:
            reset_webapp_persona()

            app = establish_webapp_persona(
                name=app_name,
                logger_name=logger_name,
                log_basename=log_basename,
            )

            actual_presence = AppPersona.AM_PRESENCE_DIR
            actual_logdir = AppPersona.AM_LOG_DIRECTORY
            actual_settings = AppPersona.AM_SETTINGS_FILENAME

            if actual_presence != expected_presence_dir:
                errmsg = (
                    f"Iteration {iteration}: presence_dir mismatch in consistency check. "
                    f"name='{app_name}', expected='{expected_presence_dir}', "
                    f"got='{actual_presence}'"
                )
                raise AssertionError(errmsg)

            if actual_logdir != expected_log_directory:
                errmsg = (
                    f"Iteration {iteration}: log_directory mismatch in consistency check. "
                    f"name='{app_name}', expected='{expected_log_directory}', "
                    f"got='{actual_logdir}'"
                )
                raise AssertionError(errmsg)

            if actual_settings != expected_settings_file:
                errmsg = (
                    f"Iteration {iteration}: settings_file mismatch in consistency check. "
                    f"name='{app_name}', expected='{expected_settings_file}', "
                    f"got='{actual_settings}'"
                )
                raise AssertionError(errmsg)

        finally:
            reset_webapp_persona()

    return
