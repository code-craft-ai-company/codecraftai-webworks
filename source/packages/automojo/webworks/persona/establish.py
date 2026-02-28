"""
.. module:: establish
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module containing the establish_webapp_persona function.

.. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


import os

from typing import Optional, Type, TYPE_CHECKING

from automojo.thisapp.persona import AppPersona
from automojo.thisapp.wellknown import (
    SINGLETON_LOCK,
    PersonaVariablesDesc
)
from automojo.errors.exceptions import SemanticError

import automojo.webworks.wellknown as webworks_wellknown
import automojo.thisapp.wellknown as thisapp_wellknown

if TYPE_CHECKING:
    from automojo.webworks.persona.webapplication import WebApplication


# Module-level flag to prevent double establishment
WEBAPP_PERSONA_ESTABLISHED: bool = False


class PersonaAlreadyEstablishedError(Exception):
    """
        Raised when attempting to establish a persona that already exists.
    """

    def __init__(self, existing_name: str):
        self.existing_name = existing_name
        super().__init__(
            f"Persona already established with name '{existing_name}'. "
            "Cannot establish a new persona."
        )
        return


def establish_webapp_persona(
    *,
    name: str,
    logger_name: str,
    log_basename: str,
    presence_dir: Optional[str] = None,
    log_directory: Optional[str] = None,
    settings_file: Optional[str] = None,
    extensions: Optional[str] = None,
    service_name: Optional[str] = None,
    application_cls: Optional[Type['WebApplication']] = None
) -> 'WebApplication':
    """
        Establish the web application persona and initialize the singleton.

        Mirrors the pattern used by automojo.thisapp.persona.establish_app_persona
        but instantiates WebApplication and wires it into both wellknown modules.

        :param name: Application name used for defaults and identification.
        :param logger_name: Name for the logger.
        :param log_basename: Base name for log files.
        :param presence_dir: Root directory for app presence (defaults to ~/<name>).
        :param log_directory: Directory for log files (defaults to <presence_dir>/logs).
        :param settings_file: Path to settings file (defaults to <presence_dir>/settings.config).
        :param extensions: Extension modules to load.
        :param service_name: Service identifier for distributed systems.
        :param application_cls: Custom WebApplication subclass to instantiate.

        :returns: The initialized WebApplication singleton.

        :raises PersonaAlreadyEstablishedError: If persona was already established.
        :raises SemanticError: If THISAPPLICATION_SINGLETON is already set.
    """
    global WEBAPP_PERSONA_ESTABLISHED

    # Import WebApplication here to avoid circular imports
    from automojo.webworks.persona.webapplication import WebApplication

    # Check if persona is already established
    if WEBAPP_PERSONA_ESTABLISHED:
        raise PersonaAlreadyEstablishedError(AppPersona.AM_NAME)

    # Mark as established early to prevent race conditions
    WEBAPP_PERSONA_ESTABLISHED = True

    # Compute default paths
    # Default presence_dir to ~/<appname>
    if presence_dir is not None:
        resolved_presence_dir = presence_dir
    else:
        resolved_presence_dir = os.path.join("~", name.lower())

    # Default log_directory to <presence_dir>/logs
    if log_directory is not None:
        resolved_log_directory = log_directory
    else:
        resolved_log_directory = os.path.join(resolved_presence_dir, "logs")

    # Default settings_file to <presence_dir>/settings.config
    if settings_file is not None:
        # If we are only given the filename, the file must be located in the presence directory
        if os.path.basename(settings_file) == settings_file:
            resolved_settings_file = os.path.join(resolved_presence_dir, settings_file)
        else:
            resolved_settings_file = os.path.abspath(
                os.path.expandvars(os.path.expanduser(settings_file))
            )
    else:
        resolved_settings_file = os.path.join(resolved_presence_dir, "settings.config")

    # Populate AppPersona class attributes (same pattern as establish_app_persona)
    AppPersona.AM_NAME = name
    AppPersona.AM_LOGGER_NAME = logger_name
    AppPersona.AM_LOG_BASENAME = log_basename
    AppPersona.AM_PRESENCE_DIR = resolved_presence_dir
    AppPersona.AM_LOG_DIRECTORY = resolved_log_directory
    AppPersona.AM_SETTINGS_FILENAME = resolved_settings_file
    AppPersona.AM_EXTENSIONS = extensions
    AppPersona.AM_SERVICE_NAME = service_name

    # Check that THISAPPLICATION_SINGLETON is not already set
    if thisapp_wellknown.THISAPPLICATION_SINGLETON is not None:
        errmsg = "The singleton 'wellknown.THISAPPLICATION_SINGLETON' must not be set " \
                 "when calling 'establish_webapp_persona'"
        raise SemanticError(errmsg)

    # Determine which class to instantiate
    if application_cls is None:
        application_cls = WebApplication

    # Create the singleton instance
    this_app = application_cls(
        name=name,
        logger_name=logger_name,
        log_basename=log_basename,
        presence_dir=resolved_presence_dir,
        log_directory=resolved_log_directory,
        settings_file=resolved_settings_file,
        extensions=extensions,
        service_name=service_name,
        from_establish_webapp_persona=True
    )

    # Wire into both wellknown modules under the lock
    SINGLETON_LOCK.acquire()
    try:
        webworks_wellknown.THISWEBAPPLICATION_SINGLETON = this_app
        thisapp_wellknown.THISAPPLICATION_SINGLETON = this_app
    finally:
        SINGLETON_LOCK.release()

    # Override variable values for PersonaVariablesDesc
    this_app.override_variable_value(PersonaVariablesDesc.AM_NAME, this_app.name)
    this_app.override_variable_value(PersonaVariablesDesc.AM_LOGGER_NAME, logger_name)
    this_app.override_variable_value(PersonaVariablesDesc.AM_LOG_BASENAME, log_basename)
    this_app.override_variable_value(PersonaVariablesDesc.AM_LOG_DIRECTORY, resolved_log_directory)
    this_app.override_variable_value(PersonaVariablesDesc.AM_PRESENCE_DIR, resolved_presence_dir)
    this_app.override_variable_value(PersonaVariablesDesc.AM_SERVICE_NAME, service_name)
    this_app.override_variable_value(PersonaVariablesDesc.AM_EXTENSIONS, extensions)

    return this_app


def reset_webapp_persona() -> None:
    """
        Reset the webapp persona state for testing purposes.

        This function resets the WEBAPP_PERSONA_ESTABLISHED flag and clears
        the singleton references. It should only be used in test scenarios.

        .. warning::
            This function is intended for testing purposes only. Do not use
            in production code.
    """
    global WEBAPP_PERSONA_ESTABLISHED

    SINGLETON_LOCK.acquire()
    try:
        WEBAPP_PERSONA_ESTABLISHED = False
        webworks_wellknown.THISWEBAPPLICATION_SINGLETON = None
        thisapp_wellknown.THISAPPLICATION_SINGLETON = None
    finally:
        SINGLETON_LOCK.release()

    return
