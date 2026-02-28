"""
.. module:: wellknown
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module containing wellknown singleton access for web applications.

.. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from typing import Optional, TYPE_CHECKING

from automojo.thisapp.wellknown import SINGLETON_LOCK
from automojo.errors.exceptions import SemanticError

if TYPE_CHECKING:
    from automojo.webworks.persona.webapplication import WebApplication


THISWEBAPPLICATION_SINGLETON: Optional['WebApplication'] = None


def ThisWebApplicationSingleton() -> 'WebApplication':
    """
        Return the global WebApplication singleton.

        This function provides access to the WebApplication singleton instance
        that was established via `establish_webapp_persona`. It mirrors the
        behavior of `automojo.thisapp.wellknown.ThisApplicationSingleton()` but
        surfaces the richer WebApplication type.

        :returns: The WebApplication instance.

        :raises SemanticError: If no persona has been established.
    """
    global THISWEBAPPLICATION_SINGLETON

    SINGLETON_LOCK.acquire()
    try:
        if THISWEBAPPLICATION_SINGLETON is None:
            errmsg = "You must call 'establish_webapp_persona' early in your application startup to define " \
                     "your application's presence settings before attempting to use the `WebApplication` " \
                     "object or its corresponding singleton."
            raise SemanticError(errmsg)
    finally:
        SINGLETON_LOCK.release()

    return THISWEBAPPLICATION_SINGLETON
