"""
.. module:: persona
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Package containing web application persona and presence infrastructure.

.. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from automojo.webworks.persona.establish import (
    establish_webapp_persona,
    reset_webapp_persona,
    PersonaAlreadyEstablishedError
)
from automojo.webworks.persona.webapplication import WebApplication

__all__ = [
    "establish_webapp_persona",
    "PersonaAlreadyEstablishedError",
    "reset_webapp_persona",
    "WebApplication"
]
