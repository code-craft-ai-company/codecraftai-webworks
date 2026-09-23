"""
.. module:: test_variable_override_precedence_properties
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Property-based tests for variable override precedence.

.. moduleauthor:: Code Craft AI LLC

This module contains property-based tests for the VariableSource flag
combinations and variable override precedence, validating Property 8:
Variable Override Precedence across many generated inputs.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

import os
import tempfile

from configparser import ConfigParser

import ccai.testbase as testbase

from ccai.testbase.properties import given
from ccai.testbase.properties import strategies as st

from ccai.thisapp.appvardesc import AppVarDesc, VariableSource
from ccai.thisapp.personavariables import PersonaVariablesDesc
from ccai.webworks.webapplication import WebApplication


# =============================================================================
# Strategies for Generating Random Test Data
# =============================================================================

random_string_strategy = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789",
    min_size=3,
    max_size=15,
)

var_suffix_strategy = st.text(
    alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    min_size=6,
    max_size=6,
)

source_flags_strategy = st.sampled_from([
    VariableSource.NONE,
    VariableSource.ENVIRONMENT,
    VariableSource.SETTINGS,
    VariableSource.BOTH,
])

env_source_strategy = st.sampled_from([
    VariableSource.ENVIRONMENT,
    VariableSource.BOTH,
])

non_env_source_strategy = st.sampled_from([
    VariableSource.NONE,
    VariableSource.SETTINGS,
])

settings_source_strategy = st.sampled_from([
    VariableSource.SETTINGS,
    VariableSource.BOTH,
])

non_settings_source_strategy = st.sampled_from([
    VariableSource.NONE,
    VariableSource.ENVIRONMENT,
])


# =============================================================================
# Helper Functions
# =============================================================================

def create_app_with_settings(settings_dict=None):
    """
        Create a WebApplication instance with an optional settings file.

        Returns a tuple of (app, settings_file_path) where settings_file_path
        is the path to the temporary settings file, or a non-existent path
        if no settings were provided.
    """
    if settings_dict is not None:
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

@given(
    iteration=st.integers(0, 999),
    var_suffix=var_suffix_strategy,
    source_flags=source_flags_strategy,
    env_value_suffix=random_string_strategy,
    settings_value_suffix=random_string_strategy,
    default_value_suffix=random_string_strategy,
    override_value_suffix=random_string_strategy,
    constraints={"max_examples": 100},
)
def test_property_override_takes_precedence_over_all_sources(
    iteration, var_suffix, source_flags, env_value_suffix,
    settings_value_suffix, default_value_suffix, override_value_suffix
):
    """
        Property 8: Variable Override Precedence

        For any variable with VariableSource flags set, explicit overrides via
        override_variable_value SHALL take precedence over all sources
        (environment, settings, and defaults).

        **Feature: webapp-persona, Property 8: Variable Override Precedence**
        **Validates: Requirements 3.7, 4.1**
    """
    var_name = f"AM_TEST_{iteration}_{var_suffix}"
    env_value = f"env_{env_value_suffix}"
    settings_value = f"settings_{settings_value_suffix}"
    default_value = f"default_{default_value_suffix}"
    override_value = f"override_{override_value_suffix}"

    os.environ[var_name] = env_value

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

        app.override_variable_value(var_desc, override_value)

        result = app.get_variable_value(var_desc)

        testbase.assert_equal(
            result, override_value,
            f"Override did not take precedence. source={source_flags}, "
            f"expected override_value='{override_value}', got='{result}'. "
            f"env_value='{env_value}', settings_value='{settings_value}', "
            f"default_value='{default_value}'"
        )

    finally:
        cleanup_settings_file(settings_path)
        cleanup_env_var(var_name)

    return


@given(
    iteration=st.integers(0, 999),
    var_suffix=var_suffix_strategy,
    include_env=st.booleans(),
    default_value_suffix=random_string_strategy,
    env_value_suffix=random_string_strategy,
    constraints={"max_examples": 100},
)
def test_property_environment_source_lookup_order(
    iteration, var_suffix, include_env, default_value_suffix, env_value_suffix
):
    """
        Property 8: Variable Override Precedence

        For any variable with VariableSource.ENVIRONMENT flag set, the lookup
        SHALL check environment variables. When the ENVIRONMENT flag is set and
        an environment variable exists, it SHALL be used. When the ENVIRONMENT
        flag is not set, environment variables SHALL be ignored even if present.

        **Feature: webapp-persona, Property 8: Variable Override Precedence**
        **Validates: Requirements 3.7, 4.1**
    """
    var_name = f"AM_TEST_{iteration}_{var_suffix}"
    default_value = f"default_{default_value_suffix}"
    env_value = f"env_{env_value_suffix}"

    if include_env:
        source_flags = VariableSource.ENVIRONMENT
    else:
        source_flags = VariableSource.NONE

    os.environ[var_name] = env_value

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
            testbase.assert_equal(
                result, env_value,
                f"Environment value not used when ENVIRONMENT flag is set. "
                f"source={source_flags}, expected='{env_value}', got='{result}'"
            )
        else:
            testbase.assert_equal(
                result, default_value,
                f"Environment value used when ENVIRONMENT flag is NOT set. "
                f"source={source_flags}, expected default='{default_value}', got='{result}'"
            )

    finally:
        cleanup_settings_file(settings_path)
        cleanup_env_var(var_name)

    return


@given(
    iteration=st.integers(0, 999),
    var_suffix=var_suffix_strategy,
    include_settings=st.booleans(),
    default_value_suffix=random_string_strategy,
    settings_value_suffix=random_string_strategy,
    constraints={"max_examples": 100},
)
def test_property_settings_source_lookup_order(
    iteration, var_suffix, include_settings, default_value_suffix, settings_value_suffix
):
    """
        Property 8: Variable Override Precedence

        For any variable with VariableSource.SETTINGS flag set, the lookup
        SHALL check the settings file. When the SETTINGS flag is set and a
        value exists in the settings file, it SHALL be used (if no environment
        variable takes precedence). When the SETTINGS flag is not set, settings
        file values SHALL be ignored.

        **Feature: webapp-persona, Property 8: Variable Override Precedence**
        **Validates: Requirements 3.7, 4.1**
    """
    var_name = f"AM_TEST_{iteration}_{var_suffix}"
    default_value = f"default_{default_value_suffix}"
    settings_value = f"settings_{settings_value_suffix}"

    cleanup_env_var(var_name)

    if include_settings:
        source_flags = VariableSource.SETTINGS
    else:
        source_flags = VariableSource.NONE

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
            testbase.assert_equal(
                result, settings_value,
                f"Settings value not used when SETTINGS flag is set. "
                f"source={source_flags}, expected='{settings_value}', got='{result}'"
            )
        else:
            testbase.assert_equal(
                result, default_value,
                f"Settings value used when SETTINGS flag is NOT set. "
                f"source={source_flags}, expected default='{default_value}', got='{result}'"
            )

    finally:
        cleanup_settings_file(settings_path)

    return


@given(
    iteration=st.integers(0, 999),
    var_suffix=var_suffix_strategy,
    env_value_suffix=random_string_strategy,
    settings_value_suffix=random_string_strategy,
    default_value_suffix=random_string_strategy,
    constraints={"max_examples": 100},
)
def test_property_environment_precedes_settings_when_both_set(
    iteration, var_suffix, env_value_suffix, settings_value_suffix, default_value_suffix
):
    """
        Property 8: Variable Override Precedence

        For any variable with VariableSource.BOTH flag set, when both an
        environment variable and a settings file value exist, the environment
        variable SHALL take precedence over the settings file value.

        **Feature: webapp-persona, Property 8: Variable Override Precedence**
        **Validates: Requirements 3.7, 4.1**
    """
    var_name = f"AM_TEST_{iteration}_{var_suffix}"
    env_value = f"env_{env_value_suffix}"
    settings_value = f"settings_{settings_value_suffix}"
    default_value = f"default_{default_value_suffix}"

    os.environ[var_name] = env_value

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

        testbase.assert_equal(
            result, env_value,
            f"Environment did not take precedence over settings when BOTH flags set. "
            f"expected env_value='{env_value}', got='{result}', "
            f"settings_value='{settings_value}'"
        )

    finally:
        cleanup_settings_file(settings_path)
        cleanup_env_var(var_name)

    return


@given(
    app_name_suffix=random_string_strategy,
    logger_suffix=random_string_strategy,
    logbase_suffix=random_string_strategy,
    presence_suffix=random_string_strategy,
    service_suffix=random_string_strategy,
    use_extensions=st.booleans(),
    ext_suffix=random_string_strategy,
    constraints={"max_examples": 100},
)
def test_property_persona_variables_override_via_establish(
    app_name_suffix, logger_suffix, logbase_suffix,
    presence_suffix, service_suffix, use_extensions, ext_suffix
):
    """
        Property 8: Variable Override Precedence

        For any established web application persona, the PersonaVariablesDesc
        variables SHALL have their values set via override_variable_value,
        and get_variable_value SHALL return those overridden values.

        **Feature: webapp-persona, Property 8: Variable Override Precedence**
        **Validates: Requirements 3.7, 4.1**
    """
    from ccai.webworks.webapplication import (
        establish_webapp_persona,
        reset_webapp_persona,
    )

    app_name = f"Prop8App{app_name_suffix}"
    logger_name = f"logger_{logger_suffix}"
    log_basename = f"logbase_{logbase_suffix}"
    presence_dir = f"/tmp/prop8test_{presence_suffix}"
    log_directory = f"{presence_dir}/logs"
    service_name = f"svc_{service_suffix}"
    extensions = ext_suffix if use_extensions else ""

    try:
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

        testbase.assert_equal(
            app.get_variable_value(PersonaVariablesDesc.AM_NAME), app_name,
            f"AM_NAME override mismatch. expected='{app_name}', "
            f"got='{app.get_variable_value(PersonaVariablesDesc.AM_NAME)}'"
        )

        testbase.assert_equal(
            app.get_variable_value(PersonaVariablesDesc.AM_LOGGER_NAME), logger_name,
            f"AM_LOGGER_NAME override mismatch. expected='{logger_name}', "
            f"got='{app.get_variable_value(PersonaVariablesDesc.AM_LOGGER_NAME)}'"
        )

        testbase.assert_equal(
            app.get_variable_value(PersonaVariablesDesc.AM_LOG_BASENAME), log_basename,
            f"AM_LOG_BASENAME override mismatch. expected='{log_basename}', "
            f"got='{app.get_variable_value(PersonaVariablesDesc.AM_LOG_BASENAME)}'"
        )

        testbase.assert_equal(
            app.get_variable_value(PersonaVariablesDesc.AM_LOG_DIRECTORY), log_directory,
            f"AM_LOG_DIRECTORY override mismatch. expected='{log_directory}', "
            f"got='{app.get_variable_value(PersonaVariablesDesc.AM_LOG_DIRECTORY)}'"
        )

        testbase.assert_equal(
            app.get_variable_value(PersonaVariablesDesc.AM_PRESENCE_DIR), presence_dir,
            f"AM_PRESENCE_DIR override mismatch. expected='{presence_dir}', "
            f"got='{app.get_variable_value(PersonaVariablesDesc.AM_PRESENCE_DIR)}'"
        )

        testbase.assert_equal(
            app.get_variable_value(PersonaVariablesDesc.AM_SERVICE_NAME), service_name,
            f"AM_SERVICE_NAME override mismatch. expected='{service_name}', "
            f"got='{app.get_variable_value(PersonaVariablesDesc.AM_SERVICE_NAME)}'"
        )

        testbase.assert_equal(
            app.get_variable_value(PersonaVariablesDesc.AM_EXTENSIONS), extensions,
            f"AM_EXTENSIONS override mismatch. expected='{extensions}', "
            f"got='{app.get_variable_value(PersonaVariablesDesc.AM_EXTENSIONS)}'"
        )

    finally:
        reset_webapp_persona()

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
