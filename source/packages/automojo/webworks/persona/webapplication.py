"""
.. module:: webapplication
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module containing the `WebApplication` class for web applications.

.. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from automojo.thisapp.wellknown import ThisApplication
from automojo.errors.exceptions import SemanticError


class WebApplication(ThisApplication):
    """
        Root class for web applications extending ThisApplication with
        database lifecycle hooks.
        
        This class provides the foundational infrastructure for web applications
        in the automojo framework, including database preparation, connection,
        startup, and readiness verification hooks.
    """

    def __init__(self, *, name: str, logger_name: str, log_basename: str,
                 presence_dir: str, log_directory: str, settings_file: str,
                 extensions: str, service_name: str, **other):
        """
            Constructs a WebApplication object.

            :param name: A one-word short name for the application.
            :param logger_name: Name for the logger.
            :param log_basename: Base name for log files.
            :param presence_dir: The directory for application presence.
            :param log_directory: The directory for log files.
            :param settings_file: The path to the settings file.
            :param extensions: Extension modules to load.
            :param service_name: Service identifier for distributed systems.
            
            :raises SemanticError: If `from_establish_webapp_persona` is not passed.
        """
        if "from_establish_webapp_persona" not in other:
            errmsg = "The `WebApplication` singleton object should not be instantiated directly. " \
                     "Call `establish_webapp_persona` to establish application wide presence settings " \
                     "and then use the wellknown singleton to access the application presence instance."
            raise SemanticError(errmsg)

        # Pass from_establish_app_persona=True to satisfy parent's instantiation guard
        super().__init__(
            name=name,
            logger_name=logger_name,
            log_basename=log_basename,
            presence_dir=presence_dir,
            log_directory=log_directory,
            settings_file=settings_file,
            extensions=extensions,
            service_name=service_name,
            from_establish_app_persona=True
        )

        return

    def prepare_database(self) -> None:
        """
            Hook for database preparation tasks such as running migrations.
            Override in subclasses to implement project-specific logic.
        """
        pass

    def connect_database(self) -> None:
        """
            Hook for establishing database connections and session pools.
            Override in subclasses to implement project-specific logic.
        """
        pass

    def startup_database(self) -> None:
        """
            Hook for database startup operations.
            Override in subclasses to implement project-specific logic.
        """
        pass

    def ensure_database_ready(self) -> bool:
        """
            Hook for verifying database readiness.
            Override in subclasses to implement project-specific logic.

            :returns: True if database is ready, False otherwise.
        """
        return True
