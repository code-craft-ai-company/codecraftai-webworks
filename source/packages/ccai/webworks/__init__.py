"""
.. module:: webworks
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Package containing web application infrastructure for the ccai framework.

.. moduleauthor:: Code Craft AI LLC

This package provides web application infrastructure including:

- ASGI application layer (HTTP handlers, WebSocket, SSE, background tasks)
- WSGI application layer (server, workers, middleware, request/response handling)
- Web application persona system for establishing application identity
- Authentication infrastructure with pluggable authenticators
- Endpoint routing and access policy enforcement
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from ccai.webworks.wellknown import (
    THISWEBAPPLICATION_SINGLETON,
    ThisWebApplicationSingleton
)

# Import authentication module for convenient access
from ccai.webworks import authentication

__all__ = [
    "authentication",
    "THISWEBAPPLICATION_SINGLETON",
    "ThisWebApplicationSingleton"
]
