"""
    Production Server package for the webworks framework.

    The production server is the built-in WSGI server (ccai.webworks.wsgi)
    with a production layer on top: gunicorn-style configuration, pre-forked
    workers with max-requests recycling, privilege drop after bind, a PID
    file, request IDs, health and metrics endpoints, a structured access log,
    request size and time limits, an HTTPS redirect and graceful shutdown and
    reload. It serves a WebApplication through its wsgi_app.

    From the command line: ``webworks prodserve --app mysite.app:webapp``.
"""

from ccai.webworks.prodserver.exceptions import ConfigurationError, ProductionServerError
from ccai.webworks.prodserver.healthchecker import HealthChecker
from ccai.webworks.prodserver.metricscollector import MetricsCollector
from ccai.webworks.prodserver.metricsstore import MetricsStore
from ccai.webworks.prodserver.productionmiddleware import (
    ProductionMiddleware,
    RequestIdLogFilter,
    current_request_id,
)
from ccai.webworks.prodserver.productionserver import ProductionServer
from ccai.webworks.prodserver.serverconfig import (
    ServerConfig,
    ServerState,
    EXIT_SUCCESS,
    EXIT_ERROR,
    EXIT_CONFIG_ERROR,
    EXIT_BIND_ERROR,
    EXIT_APP_LOAD_ERROR,
    EXIT_PID_FILE_ERROR,
)

__all__ = [
    "ConfigurationError",
    "ProductionServerError",
    "HealthChecker",
    "MetricsCollector",
    "MetricsStore",
    "ProductionMiddleware",
    "RequestIdLogFilter",
    "current_request_id",
    "ProductionServer",
    "ServerConfig",
    "ServerState",
    "EXIT_SUCCESS",
    "EXIT_ERROR",
    "EXIT_CONFIG_ERROR",
    "EXIT_BIND_ERROR",
    "EXIT_APP_LOAD_ERROR",
    "EXIT_PID_FILE_ERROR",
]
