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

import random
import string

from automojo.thisapp.persona import AppPersona
from automojo.webworks.persona import (
    establish_webapp_persona,
    reset_webapp_persona,
)
from automojo.webworks.persona.establish import PersonaAlreadyEstablishedError
import automojo.webworks.wellknown as webworks_wellknown
import automojo.thisapp.wellknown as thisapp_wellknown


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
# Property 10: Singleton Establishment Guard
# Feature: webapp-persona, Property 10: Singleton Establishment Guard
# Validates: Requirements 5.7
# =============================================================================

def test_property_second_establish_raises_error():
    """
        Property 10: Singleton Establishment Guard

        For any sequence of establish_webapp_persona calls, only the first
        call SHALL succeed; subsequent calls SHALL raise
        PersonaAlreadyEstablishedError.

        This test establishes a persona, then attempts a second establishment
        with different random parameters and verifies the correct exception
        is raised, across 100 iterations.

        **Feature: webapp-persona, Property 10: Singleton Establishment Guard**
        **Validates: Requirements 5.7**
    """
    for iteration in range(100):
        first_name = generate_app_name()
        first_logger = f"logger_{generate_random_string()}"
        first_logbase = f"logbase_{generate_random_string()}"

        second_name = generate_app_name()
        second_logger = f"logger_{generate_random_string()}"
        second_logbase = f"logbase_{generate_random_string()}"

        try:
            reset_webapp_persona()

            # First call should succeed
            establish_webapp_persona(
                name=first_name,
                logger_name=first_logger,
                log_basename=first_logbase,
            )

            # Second call should raise PersonaAlreadyEstablishedError
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
                        f"Iteration {iteration}: Expected PersonaAlreadyEstablishedError "
                        f"on second call, got {exception_type.__name__}"
                    )
                else:
                    errmsg = (
                        f"Iteration {iteration}: Expected PersonaAlreadyEstablishedError "
                        f"on second call, but no exception was raised"
                    )
                raise AssertionError(errmsg)

        finally:
            reset_webapp_persona()

    return


def test_property_original_singleton_preserved_after_second_call():
    """
        Property 10: Singleton Establishment Guard

        For any sequence of establish_webapp_persona calls, the original
        singleton SHALL remain unchanged after a failed second establishment
        attempt.

        This test verifies that the singleton identity and persona attributes
        from the first establishment are preserved after the second call
        raises PersonaAlreadyEstablishedError, across 100 iterations.

        **Feature: webapp-persona, Property 10: Singleton Establishment Guard**
        **Validates: Requirements 5.7**
    """
    for iteration in range(100):
        first_name = generate_app_name()
        first_logger = f"logger_{generate_random_string()}"
        first_logbase = f"logbase_{generate_random_string()}"

        second_name = generate_app_name()
        second_logger = f"logger_{generate_random_string()}"
        second_logbase = f"logbase_{generate_random_string()}"

        try:
            reset_webapp_persona()

            # First call should succeed
            original_app = establish_webapp_persona(
                name=first_name,
                logger_name=first_logger,
                log_basename=first_logbase,
            )

            # Capture original singleton references
            original_web_singleton = webworks_wellknown.THISWEBAPPLICATION_SINGLETON
            original_app_singleton = thisapp_wellknown.THISAPPLICATION_SINGLETON
            original_persona_name = AppPersona.AM_NAME

            # Second call should raise PersonaAlreadyEstablishedError
            try:
                establish_webapp_persona(
                    name=second_name,
                    logger_name=second_logger,
                    log_basename=second_logbase,
                )
            except PersonaAlreadyEstablishedError:
                pass

            # Verify the original singleton is preserved (identity check)
            if webworks_wellknown.THISWEBAPPLICATION_SINGLETON is not original_app:
                errmsg = (
                    f"Iteration {iteration}: THISWEBAPPLICATION_SINGLETON changed "
                    f"after failed second establishment"
                )
                raise AssertionError(errmsg)

            if thisapp_wellknown.THISAPPLICATION_SINGLETON is not original_app:
                errmsg = (
                    f"Iteration {iteration}: THISAPPLICATION_SINGLETON changed "
                    f"after failed second establishment"
                )
                raise AssertionError(errmsg)

            # Verify persona name was not overwritten
            if AppPersona.AM_NAME != first_name:
                errmsg = (
                    f"Iteration {iteration}: AppPersona.AM_NAME changed from "
                    f"'{first_name}' to '{AppPersona.AM_NAME}' after failed "
                    f"second establishment"
                )
                raise AssertionError(errmsg)

        finally:
            reset_webapp_persona()

    return


def test_property_error_contains_existing_persona_name():
    """
        Property 10: Singleton Establishment Guard

        For any failed second establishment attempt, the raised
        PersonaAlreadyEstablishedError SHALL include the name of the
        existing persona in its message.

        This test verifies that the error message references the original
        persona name across 100 iterations with random names.

        **Feature: webapp-persona, Property 10: Singleton Establishment Guard**
        **Validates: Requirements 5.7**
    """
    for iteration in range(100):
        first_name = generate_app_name()
        first_logger = f"logger_{generate_random_string()}"
        first_logbase = f"logbase_{generate_random_string()}"

        second_name = generate_app_name()
        second_logger = f"logger_{generate_random_string()}"
        second_logbase = f"logbase_{generate_random_string()}"

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

            if caught_error is None:
                errmsg = (
                    f"Iteration {iteration}: Expected PersonaAlreadyEstablishedError "
                    f"but no exception was raised"
                )
                raise AssertionError(errmsg)

            error_message = str(caught_error)

            if first_name not in error_message:
                errmsg = (
                    f"Iteration {iteration}: Error message does not contain "
                    f"existing persona name '{first_name}'. "
                    f"Got: '{error_message}'"
                )
                raise AssertionError(errmsg)

            if caught_error.existing_name != first_name:
                errmsg = (
                    f"Iteration {iteration}: existing_name attribute mismatch. "
                    f"Expected '{first_name}', got '{caught_error.existing_name}'"
                )
                raise AssertionError(errmsg)

        finally:
            reset_webapp_persona()

    return


def test_property_multiple_subsequent_calls_all_fail():
    """
        Property 10: Singleton Establishment Guard

        For any number of subsequent establish_webapp_persona calls after
        the first, ALL subsequent calls SHALL raise
        PersonaAlreadyEstablishedError and the original singleton SHALL
        remain unchanged throughout.

        This test establishes a persona once, then attempts a random number
        of additional calls (2-5), verifying each one fails correctly,
        across 100 iterations.

        **Feature: webapp-persona, Property 10: Singleton Establishment Guard**
        **Validates: Requirements 5.7**
    """
    for iteration in range(100):
        first_name = generate_app_name()
        first_logger = f"logger_{generate_random_string()}"
        first_logbase = f"logbase_{generate_random_string()}"

        try:
            reset_webapp_persona()

            original_app = establish_webapp_persona(
                name=first_name,
                logger_name=first_logger,
                log_basename=first_logbase,
            )

            # Attempt a random number of subsequent calls
            num_attempts = random.randint(2, 5)

            for attempt in range(num_attempts):
                attempt_name = generate_app_name()
                attempt_logger = f"logger_{generate_random_string()}"
                attempt_logbase = f"logbase_{generate_random_string()}"

                exception_raised = False

                try:
                    establish_webapp_persona(
                        name=attempt_name,
                        logger_name=attempt_logger,
                        log_basename=attempt_logbase,
                    )
                except PersonaAlreadyEstablishedError:
                    exception_raised = True

                if not exception_raised:
                    errmsg = (
                        f"Iteration {iteration}, attempt {attempt + 1}/{num_attempts}: "
                        f"Expected PersonaAlreadyEstablishedError but no exception raised"
                    )
                    raise AssertionError(errmsg)

            # After all failed attempts, original singleton must still be intact
            if webworks_wellknown.THISWEBAPPLICATION_SINGLETON is not original_app:
                errmsg = (
                    f"Iteration {iteration}: THISWEBAPPLICATION_SINGLETON changed "
                    f"after {num_attempts} failed establishment attempts"
                )
                raise AssertionError(errmsg)

            if thisapp_wellknown.THISAPPLICATION_SINGLETON is not original_app:
                errmsg = (
                    f"Iteration {iteration}: THISAPPLICATION_SINGLETON changed "
                    f"after {num_attempts} failed establishment attempts"
                )
                raise AssertionError(errmsg)

            if AppPersona.AM_NAME != first_name:
                errmsg = (
                    f"Iteration {iteration}: AppPersona.AM_NAME changed from "
                    f"'{first_name}' to '{AppPersona.AM_NAME}' after "
                    f"{num_attempts} failed establishment attempts"
                )
                raise AssertionError(errmsg)

        finally:
            reset_webapp_persona()

    return
