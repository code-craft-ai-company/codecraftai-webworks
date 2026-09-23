"""
.. module:: test_custom_class_instantiation_properties
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Property-based tests for custom class instantiation.

.. moduleauthor:: Code Craft AI LLC

This module contains property-based tests for the custom class instantiation
logic in establish_webapp_persona, validating Property 5: Custom Class
Instantiation across many generated inputs.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

import ccai.testbase as testbase

from ccai.testbase.properties import given
from ccai.testbase.properties import strategies as st

from ccai.thisapp.persona import AppPersona
from ccai.thisapp.wellknown import ThisApplication
from ccai.webworks.webapplication import (
    establish_webapp_persona,
    reset_webapp_persona,
)
from ccai.webworks.webapplication import WebApplication
import ccai.webworks.wellknown as webworks_wellknown
import ccai.thisapp.wellknown as thisapp_wellknown


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

custom_cls_strategy = st.sampled_from(CUSTOM_SUBCLASSES)


# =============================================================================
# Property 5: Custom Class Instantiation
# Feature: webapp-persona, Property 5: Custom Class Instantiation
# Validates: Requirements 2.4
# =============================================================================

@given(
    app_name=app_name_strategy,
    suffix=random_string_strategy,
    chosen_cls=custom_cls_strategy,
    constraints={"max_examples": 100},
)
def test_property_custom_cls_is_exact_type(app_name, suffix, chosen_cls):
    """
        Property 5: Custom Class Instantiation

        For any custom WebApplication subclass passed via application_cls
        parameter, establish_webapp_persona SHALL instantiate that specific
        class and the singleton SHALL be an instance of that class.

        **Feature: webapp-persona, Property 5: Custom Class Instantiation**
        **Validates: Requirement 2.4**
    """
    logger_name = f"logger_{suffix}"
    log_basename = f"logbase_{suffix}"

    try:
        reset_webapp_persona()

        app = establish_webapp_persona(
            name=app_name,
            logger_name=logger_name,
            log_basename=log_basename,
            application_cls=chosen_cls,
        )

        testbase.assert_true(
            type(app) is chosen_cls,
            f"Expected exact type {chosen_cls.__name__}, got {type(app).__name__}. "
            f"app_name='{app_name}'"
        )

    finally:
        reset_webapp_persona()

    return


@given(
    app_name=app_name_strategy,
    suffix=random_string_strategy,
    chosen_cls=custom_cls_strategy,
    constraints={"max_examples": 100},
)
def test_property_custom_cls_isinstance_of_webapplication(app_name, suffix, chosen_cls):
    """
        Property 5: Custom Class Instantiation

        For any custom WebApplication subclass passed via application_cls,
        the resulting singleton SHALL also be an instance of WebApplication
        and ThisApplication, preserving the full inheritance chain.

        **Feature: webapp-persona, Property 5: Custom Class Instantiation**
        **Validates: Requirements 2.4, 1.1**
    """
    logger_name = f"logger_{suffix}"
    log_basename = f"logbase_{suffix}"

    try:
        reset_webapp_persona()

        app = establish_webapp_persona(
            name=app_name,
            logger_name=logger_name,
            log_basename=log_basename,
            application_cls=chosen_cls,
        )

        testbase.assert_true(
            isinstance(app, WebApplication),
            f"Singleton of type {type(app).__name__} is not an instance of WebApplication. "
            f"app_name='{app_name}', chosen_cls='{chosen_cls.__name__}'"
        )

        testbase.assert_true(
            isinstance(app, ThisApplication),
            f"Singleton of type {type(app).__name__} is not an instance of ThisApplication. "
            f"app_name='{app_name}', chosen_cls='{chosen_cls.__name__}'"
        )

    finally:
        reset_webapp_persona()

    return


@given(
    app_name=app_name_strategy,
    suffix=random_string_strategy,
    chosen_cls=custom_cls_strategy,
    constraints={"max_examples": 100},
)
def test_property_custom_cls_wired_into_both_singletons(app_name, suffix, chosen_cls):
    """
        Property 5: Custom Class Instantiation

        For any custom WebApplication subclass, the singleton created by
        establish_webapp_persona SHALL be wired into both
        THISWEBAPPLICATION_SINGLETON and THISAPPLICATION_SINGLETON, and
        both SHALL reference the same object.

        **Feature: webapp-persona, Property 5: Custom Class Instantiation**
        **Validates: Requirements 2.4, 2.2**
    """
    logger_name = f"logger_{suffix}"
    log_basename = f"logbase_{suffix}"

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

        testbase.assert_true(
            web_singleton is app,
            f"THISWEBAPPLICATION_SINGLETON is not the returned app instance for "
            f"{chosen_cls.__name__}. app_name='{app_name}'"
        )

        testbase.assert_true(
            app_singleton is app,
            f"THISAPPLICATION_SINGLETON is not the returned app instance for "
            f"{chosen_cls.__name__}. app_name='{app_name}'"
        )

        testbase.assert_true(
            web_singleton is app_singleton,
            f"THISWEBAPPLICATION_SINGLETON and THISAPPLICATION_SINGLETON are not "
            f"the same object for {chosen_cls.__name__}. app_name='{app_name}'"
        )

    finally:
        reset_webapp_persona()

    return


@given(
    app_name=app_name_strategy,
    suffix=random_string_strategy,
    chosen_cls=custom_cls_strategy,
    constraints={"max_examples": 100},
)
def test_property_custom_cls_persona_attributes_set(app_name, suffix, chosen_cls):
    """
        Property 5: Custom Class Instantiation

        For any custom WebApplication subclass, the persona attributes on
        AppPersona SHALL be correctly populated with the values passed to
        establish_webapp_persona, regardless of which subclass is used.

        **Feature: webapp-persona, Property 5: Custom Class Instantiation**
        **Validates: Requirements 2.4, 2.12**
    """
    logger_name = f"logger_{suffix}"
    log_basename = f"logbase_{suffix}"

    try:
        reset_webapp_persona()

        establish_webapp_persona(
            name=app_name,
            logger_name=logger_name,
            log_basename=log_basename,
            application_cls=chosen_cls,
        )

        testbase.assert_equal(
            AppPersona.AM_NAME, app_name,
            f"AppPersona.AM_NAME mismatch for {chosen_cls.__name__}. "
            f"Expected '{app_name}', got '{AppPersona.AM_NAME}'"
        )

        testbase.assert_equal(
            AppPersona.AM_LOGGER_NAME, logger_name,
            f"AppPersona.AM_LOGGER_NAME mismatch for {chosen_cls.__name__}. "
            f"Expected '{logger_name}', got '{AppPersona.AM_LOGGER_NAME}'"
        )

        testbase.assert_equal(
            AppPersona.AM_LOG_BASENAME, log_basename,
            f"AppPersona.AM_LOG_BASENAME mismatch for {chosen_cls.__name__}. "
            f"Expected '{log_basename}', got '{AppPersona.AM_LOG_BASENAME}'"
        )

    finally:
        reset_webapp_persona()

    return


@given(
    app_name=app_name_strategy,
    suffix=random_string_strategy,
    constraints={"max_examples": 100},
)
def test_property_default_cls_is_webapplication(app_name, suffix):
    """
        Property 5: Custom Class Instantiation

        When application_cls is not provided (None), establish_webapp_persona
        SHALL default to instantiating the base WebApplication class.

        **Feature: webapp-persona, Property 5: Custom Class Instantiation**
        **Validates: Requirement 2.4**
    """
    logger_name = f"logger_{suffix}"
    log_basename = f"logbase_{suffix}"

    try:
        reset_webapp_persona()

        app = establish_webapp_persona(
            name=app_name,
            logger_name=logger_name,
            log_basename=log_basename,
        )

        testbase.assert_true(
            type(app) is WebApplication,
            f"Expected default type WebApplication, got {type(app).__name__}. "
            f"app_name='{app_name}'"
        )

    finally:
        reset_webapp_persona()

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
