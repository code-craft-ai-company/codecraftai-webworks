"""
.. module:: webworks
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Package containing web application infrastructure for the automojo framework.

.. moduleauthor:: Automation Mojo LLC

This package provides web application infrastructure including:

- ASGI application layer (HTTP handlers, WebSocket, SSE, background tasks)
- WSGI application layer (server, workers, middleware, request/response handling)
- Web application persona system for establishing application identity
- Authentication infrastructure with pluggable authenticators
- Endpoint routing and access policy enforcement
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from automojo.webworks.wellknown import (
    THISWEBAPPLICATION_SINGLETON,
    ThisWebApplicationSingleton
)

# Import authentication module for convenient access
from automojo.webworks import authentication

__all__ = [
    "authentication",
    "THISWEBAPPLICATION_SINGLETON",
    "ThisWebApplicationSingleton"
]
