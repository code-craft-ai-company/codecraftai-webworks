"""
.. module:: test_establishment_guard_properties
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Property-based tests for singleton establishment guard.

.. moduleauthor:: Automation Mojo LLC

This module contains property-based tests for the singleton establishment
guard logic in establish_webapp_persona, validating Property 10: Singleton
Establishment Guard across many generated inputs.
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

import automojo.testbase as testbase

from automojo.testbase.properties import given
from automojo.testbase.properties import strategies as st

from automojo.thisapp.persona import AppPersona
from automojo.webworks.webapplication import (
    establish_webapp_persona,
    reset_webapp_persona,
)
from automojo.webworks.webapplication import PersonaAlreadyEstablishedError
import automojo.webworks.wellknown as webworks_wellknown
import automojo.thisapp.wellknown as thisapp_wellknown


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
# Property 10: Singleton Establishment Guard
# Feature: webapp-persona, Property 10: Singleton Establishment Guard
# Validates: Requirements 5.7
# =============================================================================

@given(
    first_name=app_name_strategy,
    first_suffix=random_string_strategy,
    second_name=app_name_strategy,
    second_suffix=random_string_strategy,
    constraints={"max_examples": 100},
)
def test_property_second_establish_raises_error(first_name, first_suffix, second_name, second_suffix):
    """
        Property 10: Singleton Establishment Guard

        For any sequence of establish_webapp_persona calls, only the first
        call SHALL succeed; subsequent calls SHALL raise
        PersonaAlreadyEstablishedError.

        **Feature: webapp-persona, Property 10: Singleton Establishment Guard**
        **Validates: Requirements 5.7**
    """
    first_logger = f"logger_{first_suffix}"
    first_logbase = f"logbase_{first_suffix}"
    second_logger = f"logger_{second_suffix}"
    second_logbase = f"logbase_{second_suffix}"

    try:
        reset_webapp_persona()

        establish_webapp_persona(
            name=first_name,
            logger_name=first_logger,
            log_basename=first_logbase,
        )

        exception_raised = False
        exception_type = None

        try:
            establish_webapp_persona(
                name=second_name,
                logger_name=second_logger,
                log_basename=second_logbase,
            )
        except PersonaAlreadyEstablishedError:
            exception_raised = True
        except Exception as err:
            exception_type = type(err)

        if not exception_raised:
            if exception_type is not None:
                errmsg = (
                    f"Expected PersonaAlreadyEstablishedError on second call, "
                    f"got {exception_type.__name__}. "
                    f"first_name='{first_name}', second_name='{second_name}'"
                )
            else:
                errmsg = (
                    f"Expected PersonaAlreadyEstablishedError on second call, "
                    f"but no exception was raised. "
                    f"first_name='{first_name}', second_name='{second_name}'"
                )
            raise AssertionError(errmsg)

    finally:
        reset_webapp_persona()

    return


@given(
    first_name=app_name_strategy,
    first_suffix=random_string_strategy,
    second_name=app_name_strategy,
    second_suffix=random_string_strategy,
    constraints={"max_examples": 100},
)
def test_property_original_singleton_preserved_after_second_call(first_name, first_suffix, second_name, second_suffix):
    """
        Property 10: Singleton Establishment Guard

        For any sequence of establish_webapp_persona calls, the original
        singleton SHALL remain unchanged after a failed second establishment
        attempt.

        **Feature: webapp-persona, Property 10: Singleton Establishment Guard**
        **Validates: Requirements 5.7**
    """
    first_logger = f"logger_{first_suffix}"
    first_logbase = f"logbase_{first_suffix}"
    second_logger = f"logger_{second_suffix}"
    second_logbase = f"logbase_{second_suffix}"

    try:
        reset_webapp_persona()

        original_app = establish_webapp_persona(
            name=first_name,
            logger_name=first_logger,
            log_basename=first_logbase,
        )

        try:
            establish_webapp_persona(
                name=second_name,
                logger_name=second_logger,
                log_basename=second_logbase,
            )
        except PersonaAlreadyEstablishedError:
            pass

        testbase.assert_true(
            webworks_wellknown.THISWEBAPPLICATION_SINGLETON is original_app,
            f"THISWEBAPPLICATION_SINGLETON changed after failed second establishment. "
            f"first_name='{first_name}', second_name='{second_name}'"
        )

        testbase.assert_true(
            thisapp_wellknown.THISAPPLICATION_SINGLETON is original_app,
            f"THISAPPLICATION_SINGLETON changed after failed second establishment. "
            f"first_name='{first_name}', second_name='{second_name}'"
        )

        testbase.assert_equal(
            AppPersona.AM_NAME, first_name,
            f"AppPersona.AM_NAME changed from '{first_name}' to '{AppPersona.AM_NAME}' "
            f"after failed second establishment."
        )

    finally:
        reset_webapp_persona()

    return


@given(
    first_name=app_name_strategy,
    first_suffix=random_string_strategy,
    second_name=app_name_strategy,
    second_suffix=random_string_strategy,
    constraints={"max_examples": 100},
)
def test_property_error_contains_existing_persona_name(first_name, first_suffix, second_name, second_suffix):
    """
        Property 10: Singleton Establishment Guard

        For any failed second establishment attempt, the raised
        PersonaAlreadyEstablishedError SHALL include the name of the
        existing persona in its message.

        **Feature: webapp-persona, Property 10: Singleton Establishment Guard**
        **Validates: Requirements 5.7**
    """
    first_logger = f"logger_{first_suffix}"
    first_logbase = f"logbase_{first_suffix}"
    second_logger = f"logger_{second_suffix}"
    second_logbase = f"logbase_{second_suffix}"

    try:
        reset_webapp_persona()

        establish_webapp_persona(
            name=first_name,
            logger_name=first_logger,
            log_basename=first_logbase,
        )

        caught_error = None

        try:
            establish_webapp_persona(
                name=second_name,
                logger_name=second_logger,
                log_basename=second_logbase,
            )
        except PersonaAlreadyEstablishedError as err:
            caught_error = err

        testbase.assert_true(
            caught_error is not None,
            f"Expected PersonaAlreadyEstablishedError but no exception was raised. "
            f"first_name='{first_name}', second_name='{second_name}'"
        )

        error_message = str(caught_error)

        testbase.assert_true(
            first_name in error_message,
            f"Error message does not contain existing persona name '{first_name}'. "
            f"Got: '{error_message}'"
        )

        testbase.assert_equal(
            caught_error.existing_name, first_name,
            f"existing_name attribute mismatch. Expected '{first_name}', "
            f"got '{caught_error.existing_name}'"
        )

    finally:
        reset_webapp_persona()

    return


@given(
    first_name=app_name_strategy,
    first_suffix=random_string_strategy,
    num_attempts=st.integers(2, 5),
    constraints={"max_examples": 100},
)
def test_property_multiple_subsequent_calls_all_fail(first_name, first_suffix, num_attempts):
    """
        Property 10: Singleton Establishment Guard

        For any number of subsequent establish_webapp_persona calls after
        the first, ALL subsequent calls SHALL raise
        PersonaAlreadyEstablishedError and the original singleton SHALL
        remain unchanged throughout.

        **Feature: webapp-persona, Property 10: Singleton Establishment Guard**
        **Validates: Requirements 5.7**
    """
    first_logger = f"logger_{first_suffix}"
    first_logbase = f"logbase_{first_suffix}"

    try:
        reset_webapp_persona()

        original_app = establish_webapp_persona(
            name=first_name,
            logger_name=first_logger,
            log_basename=first_logbase,
        )

        for attempt in range(num_attempts):
            exception_raised = False

            try:
                establish_webapp_persona(
                    name=f"attempt_{attempt}",
                    logger_name=f"logger_attempt_{attempt}",
                    log_basename=f"logbase_attempt_{attempt}",
                )
            except PersonaAlreadyEstablishedError:
                exception_raised = True

            testbase.assert_true(
                exception_raised,
                f"Attempt {attempt + 1}/{num_attempts}: Expected "
                f"PersonaAlreadyEstablishedError but no exception raised. "
                f"first_name='{first_name}'"
            )

        testbase.assert_true(
            webworks_wellknown.THISWEBAPPLICATION_SINGLETON is original_app,
            f"THISWEBAPPLICATION_SINGLETON changed after {num_attempts} failed "
            f"establishment attempts. first_name='{first_name}'"
        )

        testbase.assert_true(
            thisapp_wellknown.THISAPPLICATION_SINGLETON is original_app,
            f"THISAPPLICATION_SINGLETON changed after {num_attempts} failed "
            f"establishment attempts. first_name='{first_name}'"
        )

        testbase.assert_equal(
            AppPersona.AM_NAME, first_name,
            f"AppPersona.AM_NAME changed from '{first_name}' to '{AppPersona.AM_NAME}' "
            f"after {num_attempts} failed establishment attempts."
        )

    finally:
        reset_webapp_persona()

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
