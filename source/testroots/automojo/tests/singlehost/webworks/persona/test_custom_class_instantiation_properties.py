"""
.. module:: test_custom_class_instantiation_properties
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Property-based tests for custom class instantiation.

.. moduleauthor:: Automation Mojo LLC

This module contains property-based tests for the custom class instantiation
logic in establish_webapp_persona, validating Property 5: Custom Class
Instantiation across many generated inputs.
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

import random
import string

from automojo.thisapp.persona import AppPersona
from automojo.thisapp.wellknown import ThisApplication
from automojo.webworks.persona import (
    establish_webapp_persona,
    reset_webapp_persona,
)
from automojo.webworks.persona.webapplication import WebApplication
from automojo.webworks.wellknown import ThisWebApplicationSingleton
import automojo.webworks.wellknown as webworks_wellknown
import automojo.thisapp.wellknown as thisapp_wellknown


# =============================================================================
# Custom WebApplication Subclasses for Testing
# =============================================================================

class PortalWebApp(WebApplication):
    """A custom subclass simulating a portal application."""
    portal_initialized = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        PortalWebApp.portal_initialized = True


class AnalyticsWebApp(WebApplication):
    """A custom subclass simulating an analytics application."""
    analytics_tag = "analytics"


class MinimalWebApp(WebApplication):
    """A minimal custom subclass with no additions."""
    pass


class DatabaseWebApp(WebApplication):
    """A custom subclass that overrides database hooks."""

    def prepare_database(self) -> None:
        self._db_prepared = True

    def ensure_database_ready(self) -> bool:
        return getattr(self, '_db_prepared', False)


CUSTOM_SUBCLASSES = [PortalWebApp, AnalyticsWebApp, MinimalWebApp, DatabaseWebApp]


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
# Property 5: Custom Class Instantiation
# Feature: webapp-persona, Property 5: Custom Class Instantiation
# Validates: Requirements 2.4
# =============================================================================

def test_property_custom_cls_is_exact_type():
    """
        Property 5: Custom Class Instantiation

        For any custom WebApplication subclass passed via application_cls
        parameter, establish_webapp_persona SHALL instantiate that specific
        class and the singleton SHALL be an instance of that class.

        This test randomly selects a custom subclass on each iteration and
        verifies the singleton's exact type matches across 100 iterations.

        **Feature: webapp-persona, Property 5: Custom Class Instantiation**
        **Validates: Requirement 2.4**
    """
    for iteration in range(100):
        app_name = generate_app_name()
        logger_name = f"logger_{generate_random_string()}"
        log_basename = f"logbase_{generate_random_string()}"
        chosen_cls = random.choice(CUSTOM_SUBCLASSES)

        try:
            reset_webapp_persona()

            app = establish_webapp_persona(
                name=app_name,
                logger_name=logger_name,
                log_basename=log_basename,
                application_cls=chosen_cls,
            )

            if type(app) is not chosen_cls:
                errmsg = (
                    f"Iteration {iteration}: Expected exact type {chosen_cls.__name__}, "
                    f"got {type(app).__name__}"
                )
                raise AssertionError(errmsg)

        finally:
            reset_webapp_persona()

    return


def test_property_custom_cls_isinstance_of_webapplication():
    """
        Property 5: Custom Class Instantiation

        For any custom WebApplication subclass passed via application_cls,
        the resulting singleton SHALL also be an instance of WebApplication
        and ThisApplication, preserving the full inheritance chain.

        This test verifies isinstance checks against both parent classes
        across 100 iterations with randomly selected subclasses.

        **Feature: webapp-persona, Property 5: Custom Class Instantiation**
        **Validates: Requirements 2.4, 1.1**
    """
    for iteration in range(100):
        app_name = generate_app_name()
        logger_name = f"logger_{generate_random_string()}"
        log_basename = f"logbase_{generate_random_string()}"
        chosen_cls = random.choice(CUSTOM_SUBCLASSES)

        try:
            reset_webapp_persona()

            app = establish_webapp_persona(
                name=app_name,
                logger_name=logger_name,
                log_basename=log_basename,
                application_cls=chosen_cls,
            )

            if not isinstance(app, WebApplication):
                errmsg = (
                    f"Iteration {iteration}: Singleton of type {type(app).__name__} "
                    f"is not an instance of WebApplication"
                )
                raise AssertionError(errmsg)

            if not isinstance(app, ThisApplication):
                errmsg = (
                    f"Iteration {iteration}: Singleton of type {type(app).__name__} "
                    f"is not an instance of ThisApplication"
                )
                raise AssertionError(errmsg)

        finally:
            reset_webapp_persona()

    return


def test_property_custom_cls_wired_into_both_singletons():
    """
        Property 5: Custom Class Instantiation

        For any custom WebApplication subclass, the singleton created by
        establish_webapp_persona SHALL be wired into both
        THISWEBAPPLICATION_SINGLETON and THISAPPLICATION_SINGLETON, and
        both SHALL reference the same object.

        This test verifies identity equality of both singleton references
        across 100 iterations with randomly selected subclasses.

        **Feature: webapp-persona, Property 5: Custom Class Instantiation**
        **Validates: Requirements 2.4, 2.2**
    """
    for iteration in range(100):
        app_name = generate_app_name()
        logger_name = f"logger_{generate_random_string()}"
        log_basename = f"logbase_{generate_random_string()}"
        chosen_cls = random.choice(CUSTOM_SUBCLASSES)

        try:
            reset_webapp_persona()

            app = establish_webapp_persona(
                name=app_name,
                logger_name=logger_name,
                log_basename=log_basename,
                application_cls=chosen_cls,
            )

            web_singleton = webworks_wellknown.THISWEBAPPLICATION_SINGLETON
            app_singleton = thisapp_wellknown.THISAPPLICATION_SINGLETON

            if web_singleton is not app:
                errmsg = (
                    f"Iteration {iteration}: THISWEBAPPLICATION_SINGLETON is not "
                    f"the returned app instance for {chosen_cls.__name__}"
                )
                raise AssertionError(errmsg)

            if app_singleton is not app:
                errmsg = (
                    f"Iteration {iteration}: THISAPPLICATION_SINGLETON is not "
                    f"the returned app instance for {chosen_cls.__name__}"
                )
                raise AssertionError(errmsg)

            if web_singleton is not app_singleton:
                errmsg = (
                    f"Iteration {iteration}: THISWEBAPPLICATION_SINGLETON and "
                    f"THISAPPLICATION_SINGLETON are not the same object for "
                    f"{chosen_cls.__name__}"
                )
                raise AssertionError(errmsg)

        finally:
            reset_webapp_persona()

    return


def test_property_custom_cls_persona_attributes_set():
    """
        Property 5: Custom Class Instantiation

        For any custom WebApplication subclass, the persona attributes on
        AppPersona SHALL be correctly populated with the values passed to
        establish_webapp_persona, regardless of which subclass is used.

        This test verifies persona attribute consistency across 100
        iterations with randomly selected subclasses.

        **Feature: webapp-persona, Property 5: Custom Class Instantiation**
        **Validates: Requirements 2.4, 2.12**
    """
    for iteration in range(100):
        app_name = generate_app_name()
        logger_name = f"logger_{generate_random_string()}"
        log_basename = f"logbase_{generate_random_string()}"
        chosen_cls = random.choice(CUSTOM_SUBCLASSES)

        try:
            reset_webapp_persona()

            app = establish_webapp_persona(
                name=app_name,
                logger_name=logger_name,
                log_basename=log_basename,
                application_cls=chosen_cls,
            )

            if AppPersona.AM_NAME != app_name:
                errmsg = (
                    f"Iteration {iteration}: AppPersona.AM_NAME mismatch for "
                    f"{chosen_cls.__name__}. Expected '{app_name}', "
                    f"got '{AppPersona.AM_NAME}'"
                )
                raise AssertionError(errmsg)

            if AppPersona.AM_LOGGER_NAME != logger_name:
                errmsg = (
                    f"Iteration {iteration}: AppPersona.AM_LOGGER_NAME mismatch for "
                    f"{chosen_cls.__name__}. Expected '{logger_name}', "
                    f"got '{AppPersona.AM_LOGGER_NAME}'"
                )
                raise AssertionError(errmsg)

            if AppPersona.AM_LOG_BASENAME != log_basename:
                errmsg = (
                    f"Iteration {iteration}: AppPersona.AM_LOG_BASENAME mismatch for "
                    f"{chosen_cls.__name__}. Expected '{log_basename}', "
                    f"got '{AppPersona.AM_LOG_BASENAME}'"
                )
                raise AssertionError(errmsg)

        finally:
            reset_webapp_persona()

    return


def test_property_default_cls_is_webapplication():
    """
        Property 5: Custom Class Instantiation

        When application_cls is not provided (None), establish_webapp_persona
        SHALL default to instantiating the base WebApplication class.

        This test verifies the default behavior across 100 iterations to
        confirm the contrast with custom class behavior.

        **Feature: webapp-persona, Property 5: Custom Class Instantiation**
        **Validates: Requirement 2.4**
    """
    for iteration in range(100):
        app_name = generate_app_name()
        logger_name = f"logger_{generate_random_string()}"
        log_basename = f"logbase_{generate_random_string()}"

        try:
            reset_webapp_persona()

            app = establish_webapp_persona(
                name=app_name,
                logger_name=logger_name,
                log_basename=log_basename,
                # application_cls intentionally omitted
            )

            if type(app) is not WebApplication:
                errmsg = (
                    f"Iteration {iteration}: Expected default type WebApplication, "
                    f"got {type(app).__name__}"
                )
                raise AssertionError(errmsg)

        finally:
            reset_webapp_persona()

    return
