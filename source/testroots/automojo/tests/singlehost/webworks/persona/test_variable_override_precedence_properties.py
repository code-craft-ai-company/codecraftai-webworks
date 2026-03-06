"""
.. module:: test_variable_override_precedence_properties
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Property-based tests for variable override precedence.

.. moduleauthor:: Automation Mojo LLC

This module contains property-based tests for the VariableSource flag
combinations and variable override precedence, validating Property 8:
Variable Override Precedence across many generated inputs.
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

import os
import random
import string
import tempfile

from configparser import ConfigParser

from automojo.thisapp.appvardesc import AppVarDesc, VariableSource
from automojo.thisapp.appvarset import AppVarSet
from automojo.thisapp.personavariables import PersonaVariablesDesc
from automojo.webworks.webapplication import WebApplication


# =============================================================================
# Helper Functions for Generating Random Test Data
# =============================================================================

def generate_random_string(min_len=3, max_len=15):
    """Generate a random alphanumeric string suitable for variable values."""
    length = random.randint(min_len, max_len)
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


def generate_variable_name(iteration):
    """Generate a valid environment variable name unique to the iteration."""
    suffix = ''.join(random.choices(string.ascii_uppercase, k=6))
    return f"AM_TEST_{iteration}_{suffix}"


def generate_random_source():
    """Generate a random VariableSource flag combination."""
    return random.choice([
        VariableSource.NONE,
        VariableSource.ENVIRONMENT,
        VariableSource.SETTINGS,
        VariableSource.BOTH,
    ])


def create_app_with_settings(settings_dict=None):
    """
        Create a WebApplication instance with an optional settings file.

        Returns a tuple of (app, settings_file_path) where settings_file_path
        is the path to the temporary settings file, or a non-existent path
        if no settings were provided.
    """
    if settings_dict is not None:
        # Write a temporary settings file
        tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.config', delete=False)
        parser = ConfigParser()
        for section, values in settings_dict.items():
            if section != 'DEFAULT':
                parser.add_section(section)
            for key, val in values.items():
                parser.set(section, key, val)
        parser.write(tmp)
        tmp.close()
        settings_path = tmp.name
    else:
        settings_path = "/tmp/nonexistent_settings.config"

    app = WebApplication(
        name="PrecedenceTestApp",
        logger_name="precedencetestapp",
        log_basename="precedencetestapp",
        presence_dir="/tmp/precedencetestapp",
        log_directory="/tmp/precedencetestapp/logs",
        settings_file=settings_path,
        extensions="",
        service_name="precedenceservice",
        from_establish_webapp_persona=True
    )

    return app, settings_path


def cleanup_settings_file(settings_path):
    """Remove a temporary settings file if it exists."""
    if os.path.exists(settings_path):
        os.unlink(settings_path)
    return


def cleanup_env_var(var_name):
    """Remove an environment variable if it exists."""
    if var_name in os.environ:
        del os.environ[var_name]
    return


# =============================================================================
# Property 8: Variable Override Precedence
# Feature: webapp-persona, Property 8: Variable Override Precedence
# Validates: Requirements 3.7, 4.1
# =============================================================================

def test_property_override_takes_precedence_over_all_sources():
    """
        Property 8: Variable Override Precedence

        For any variable with VariableSource flags set, explicit overrides via
        override_variable_value SHALL take precedence over all sources
        (environment, settings, and defaults).

        This test creates variables with different VariableSource flag
        combinations, sets values in environment and settings, then calls
        override_variable_value and verifies the override value is always
        returned by get_variable_value.

        **Feature: webapp-persona, Property 8: Variable Override Precedence**
        **Validates: Requirements 3.7, 4.1**
    """
    env_vars_to_clean = []

    try:
        for iteration in range(100):
            # Generate unique variable name for this iteration
            var_name = generate_variable_name(iteration)
            source_flags = generate_random_source()

            # Generate distinct values for each source
            env_value = f"env_{generate_random_string()}"
            settings_value = f"settings_{generate_random_string()}"
            default_value = f"default_{generate_random_string()}"
            override_value = f"override_{generate_random_string()}"

            # Set environment variable
            os.environ[var_name] = env_value
            env_vars_to_clean.append(var_name)

            # Create a settings file with the variable in the DEFAULT section
            settings_dict = {'DEFAULT': {var_name: settings_value}}
            app, settings_path = create_app_with_settings(settings_dict)

            try:
                # Create a variable descriptor with the generated source flags
                # We use a custom AppVarSet subclass to properly bind the descriptor
                var_desc = AppVarDesc(
                    source=source_flags,
                    default=default_value
                )

                # Manually bind the descriptor name (simulating __set_name__)
                var_desc._name = var_name
                var_desc._key = f"DEFAULT->{var_name}"
                var_desc._owner = type(app)

                # First, apply the override
                app.override_variable_value(var_desc, override_value)

                # Now get the variable value - it must be the override value
                result = app.get_variable_value(var_desc)

                if result != override_value:
                    errmsg = (
                        f"Iteration {iteration}: Override did not take precedence. "
                        f"source={source_flags}, expected override_value='{override_value}', "
                        f"got='{result}'. env_value='{env_value}', "
                        f"settings_value='{settings_value}', default_value='{default_value}'"
                    )
                    raise AssertionError(errmsg)

            finally:
                cleanup_settings_file(settings_path)

    finally:
        for var_name in env_vars_to_clean:
            cleanup_env_var(var_name)

    return


def test_property_environment_source_lookup_order():
    """
        Property 8: Variable Override Precedence

        For any variable with VariableSource.ENVIRONMENT flag set, the lookup
        SHALL check environment variables. When the ENVIRONMENT flag is set and
        an environment variable exists, it SHALL be used. When the ENVIRONMENT
        flag is not set, environment variables SHALL be ignored even if present.

        This test verifies the environment source lookup behavior across
        different VariableSource flag combinations.

        **Feature: webapp-persona, Property 8: Variable Override Precedence**
        **Validates: Requirements 3.7, 4.1**
    """
    env_vars_to_clean = []

    try:
        for iteration in range(100):
            var_name = generate_variable_name(iteration)
            default_value = f"default_{generate_random_string()}"
            env_value = f"env_{generate_random_string()}"

            # Randomly decide whether to include ENVIRONMENT in the source flags
            include_env = random.choice([True, False])

            if include_env:
                source_flags = random.choice([
                    VariableSource.ENVIRONMENT,
                    VariableSource.BOTH,
                ])
            else:
                source_flags = random.choice([
                    VariableSource.NONE,
                    VariableSource.SETTINGS,
                ])

            # Set the environment variable
            os.environ[var_name] = env_value
            env_vars_to_clean.append(var_name)

            # Create app without a settings file (so settings source is empty)
            app, settings_path = create_app_with_settings()

            try:
                var_desc = AppVarDesc(
                    source=source_flags,
                    default=default_value
                )
                var_desc._name = var_name
                var_desc._key = f"DEFAULT->{var_name}"
                var_desc._owner = type(app)

                result = app.get_variable_value(var_desc)

                if include_env:
                    # When ENVIRONMENT flag is set, the env value should be used
                    if result != env_value:
                        errmsg = (
                            f"Iteration {iteration}: Environment value not used when "
                            f"ENVIRONMENT flag is set. source={source_flags}, "
                            f"expected='{env_value}', got='{result}'"
                        )
                        raise AssertionError(errmsg)
                else:
                    # When ENVIRONMENT flag is not set, the default should be used
                    if result != default_value:
                        errmsg = (
                            f"Iteration {iteration}: Environment value used when "
                            f"ENVIRONMENT flag is NOT set. source={source_flags}, "
                            f"expected default='{default_value}', got='{result}'"
                        )
                        raise AssertionError(errmsg)

            finally:
                cleanup_settings_file(settings_path)

    finally:
        for var_name in env_vars_to_clean:
            cleanup_env_var(var_name)

    return


def test_property_settings_source_lookup_order():
    """
        Property 8: Variable Override Precedence

        For any variable with VariableSource.SETTINGS flag set, the lookup
        SHALL check the settings file. When the SETTINGS flag is set and a
        value exists in the settings file, it SHALL be used (if no environment
        variable takes precedence). When the SETTINGS flag is not set, settings
        file values SHALL be ignored.

        This test verifies the settings source lookup behavior across
        different VariableSource flag combinations, with no environment
        variable present.

        **Feature: webapp-persona, Property 8: Variable Override Precedence**
        **Validates: Requirements 3.7, 4.1**
    """
    for iteration in range(100):
        var_name = generate_variable_name(iteration)
        default_value = f"default_{generate_random_string()}"
        settings_value = f"settings_{generate_random_string()}"

        # Ensure no environment variable is set for this name
        cleanup_env_var(var_name)

        # Randomly decide whether to include SETTINGS in the source flags
        include_settings = random.choice([True, False])

        if include_settings:
            source_flags = random.choice([
                VariableSource.SETTINGS,
                VariableSource.BOTH,
            ])
        else:
            source_flags = random.choice([
                VariableSource.NONE,
                VariableSource.ENVIRONMENT,
            ])

        # Create app with a settings file containing the variable
        settings_dict = {'DEFAULT': {var_name: settings_value}}
        app, settings_path = create_app_with_settings(settings_dict)

        try:
            var_desc = AppVarDesc(
                source=source_flags,
                default=default_value
            )
            var_desc._name = var_name
            var_desc._key = f"DEFAULT->{var_name}"
            var_desc._owner = type(app)

            result = app.get_variable_value(var_desc)

            if include_settings:
                # When SETTINGS flag is set and no env var, settings value should be used
                if result != settings_value:
                    errmsg = (
                        f"Iteration {iteration}: Settings value not used when "
                        f"SETTINGS flag is set. source={source_flags}, "
                        f"expected='{settings_value}', got='{result}'"
                    )
                    raise AssertionError(errmsg)
            else:
                # When SETTINGS flag is not set, the default should be used
                if result != default_value:
                    errmsg = (
                        f"Iteration {iteration}: Settings value used when "
                        f"SETTINGS flag is NOT set. source={source_flags}, "
                        f"expected default='{default_value}', got='{result}'"
                    )
                    raise AssertionError(errmsg)

        finally:
            cleanup_settings_file(settings_path)

    return


def test_property_environment_precedes_settings_when_both_set():
    """
        Property 8: Variable Override Precedence

        For any variable with VariableSource.BOTH flag set, when both an
        environment variable and a settings file value exist, the environment
        variable SHALL take precedence over the settings file value. This
        validates the lookup order: environment -> settings -> defaults.

        **Feature: webapp-persona, Property 8: Variable Override Precedence**
        **Validates: Requirements 3.7, 4.1**
    """
    env_vars_to_clean = []

    try:
        for iteration in range(100):
            var_name = generate_variable_name(iteration)
            env_value = f"env_{generate_random_string()}"
            settings_value = f"settings_{generate_random_string()}"
            default_value = f"default_{generate_random_string()}"

            # Set environment variable
            os.environ[var_name] = env_value
            env_vars_to_clean.append(var_name)

            # Create app with settings file containing the same variable
            settings_dict = {'DEFAULT': {var_name: settings_value}}
            app, settings_path = create_app_with_settings(settings_dict)

            try:
                var_desc = AppVarDesc(
                    source=VariableSource.BOTH,
                    default=default_value
                )
                var_desc._name = var_name
                var_desc._key = f"DEFAULT->{var_name}"
                var_desc._owner = type(app)

                result = app.get_variable_value(var_desc)

                # Environment should take precedence over settings
                if result != env_value:
                    errmsg = (
                        f"Iteration {iteration}: Environment did not take precedence "
                        f"over settings when BOTH flags set. "
                        f"expected env_value='{env_value}', got='{result}', "
                        f"settings_value='{settings_value}'"
                    )
                    raise AssertionError(errmsg)

            finally:
                cleanup_settings_file(settings_path)

    finally:
        for var_name in env_vars_to_clean:
            cleanup_env_var(var_name)

    return


def test_property_persona_variables_override_via_establish():
    """
        Property 8: Variable Override Precedence

        For any established web application persona, the PersonaVariablesDesc
        variables SHALL have their values set via override_variable_value,
        and get_variable_value SHALL return those overridden values. This
        validates that establish_webapp_persona correctly wires overrides
        for all persona variables.

        **Feature: webapp-persona, Property 8: Variable Override Precedence**
        **Validates: Requirements 3.7, 4.1**
    """
    from automojo.webworks.webapplication import (
        establish_webapp_persona,
        reset_webapp_persona,
    )

    for iteration in range(100):
        # Generate random persona values
        app_name = f"Prop8App{generate_random_string()}"
        logger_name = f"logger_{generate_random_string()}"
        log_basename = f"logbase_{generate_random_string()}"
        presence_dir = f"/tmp/prop8test_{generate_random_string()}"
        log_directory = f"{presence_dir}/logs"
        service_name = f"svc_{generate_random_string()}"
        extensions = generate_random_string() if random.choice([True, False]) else ""

        try:
            # Reset state before each iteration
            reset_webapp_persona()

            app = establish_webapp_persona(
                name=app_name,
                logger_name=logger_name,
                log_basename=log_basename,
                presence_dir=presence_dir,
                log_directory=log_directory,
                service_name=service_name,
                extensions=extensions,
            )

            # Verify that all PersonaVariablesDesc variables return the
            # overridden values via get_variable_value
            name_val = app.get_variable_value(PersonaVariablesDesc.AM_NAME)
            if name_val != app_name:
                errmsg = (
                    f"Iteration {iteration}: AM_NAME override mismatch. "
                    f"expected='{app_name}', got='{name_val}'"
                )
                raise AssertionError(errmsg)

            logger_val = app.get_variable_value(PersonaVariablesDesc.AM_LOGGER_NAME)
            if logger_val != logger_name:
                errmsg = (
                    f"Iteration {iteration}: AM_LOGGER_NAME override mismatch. "
                    f"expected='{logger_name}', got='{logger_val}'"
                )
                raise AssertionError(errmsg)

            logbase_val = app.get_variable_value(PersonaVariablesDesc.AM_LOG_BASENAME)
            if logbase_val != log_basename:
                errmsg = (
                    f"Iteration {iteration}: AM_LOG_BASENAME override mismatch. "
                    f"expected='{log_basename}', got='{logbase_val}'"
                )
                raise AssertionError(errmsg)

            logdir_val = app.get_variable_value(PersonaVariablesDesc.AM_LOG_DIRECTORY)
            if logdir_val != log_directory:
                errmsg = (
                    f"Iteration {iteration}: AM_LOG_DIRECTORY override mismatch. "
                    f"expected='{log_directory}', got='{logdir_val}'"
                )
                raise AssertionError(errmsg)

            presence_val = app.get_variable_value(PersonaVariablesDesc.AM_PRESENCE_DIR)
            if presence_val != presence_dir:
                errmsg = (
                    f"Iteration {iteration}: AM_PRESENCE_DIR override mismatch. "
                    f"expected='{presence_dir}', got='{presence_val}'"
                )
                raise AssertionError(errmsg)

            svc_val = app.get_variable_value(PersonaVariablesDesc.AM_SERVICE_NAME)
            if svc_val != service_name:
                errmsg = (
                    f"Iteration {iteration}: AM_SERVICE_NAME override mismatch. "
                    f"expected='{service_name}', got='{svc_val}'"
                )
                raise AssertionError(errmsg)

            ext_val = app.get_variable_value(PersonaVariablesDesc.AM_EXTENSIONS)
            if ext_val != extensions:
                errmsg = (
                    f"Iteration {iteration}: AM_EXTENSIONS override mismatch. "
                    f"expected='{extensions}', got='{ext_val}'"
                )
                raise AssertionError(errmsg)

        finally:
            reset_webapp_persona()

    return
