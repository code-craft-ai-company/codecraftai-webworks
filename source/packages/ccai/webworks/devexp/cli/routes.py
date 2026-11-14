"""
    CLI routes command for the webworks developer experience.

    This module provides the :class:`RoutesCommand` that displays all
    registered endpoints in the application. The command supports multiple
    output formats (table, JSON, CSV), path pattern filtering, verbose
    metadata display, and authentication indicators.

    Route information is obtained from a :class:`RouteRegistry`. The
    command builds one from the application named by ``--app`` (or the
    ``server.app`` configuration key): :class:`WebApplicationRouteRegistry`
    reads the routes of the application's web application persona. A
    custom registry instance can also be supplied under the
    ``route_registry`` configuration key. Each route entry contains the
    path, HTTP methods, handler name, access policy, and optional metadata.
"""

import argparse
import fnmatch
import json
import sys

from typing import Any, Dict, List, Optional, TYPE_CHECKING

from ccai.webworks.devexp.apploader import ApplicationLoadError
from ccai.webworks.devexp.apploader import find_webapp_persona
from ccai.webworks.devexp.apploader import load_application
from ccai.webworks.devexp.apploader import resolve_app_target
from ccai.webworks.devexp.cli.command import CLICommand
from ccai.webworks.devexp.cli.exitcodes import EXIT_CONFIG_ERROR
from ccai.webworks.devexp.cli.exitcodes import EXIT_SUCCESS

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace


# =============================================================================
# Route Data Structures
# =============================================================================

class RouteEntry:
    """
        Represents a single registered route in the application.

        Each route entry contains the path pattern, allowed HTTP methods,
        the handler function name, the access policy, and optional
        metadata for verbose display.
    """

    def __init__(
        self,
        path: str,
        methods: List[str],
        handler: str,
        access_policy: str = "public",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
            Initialize a RouteEntry instance.

            :param path: The URL path pattern for this route.
            :param methods: A list of HTTP methods this route accepts.
            :param handler: The name of the handler function or class.
            :param access_policy: The access policy (e.g. ``"public"``,
                ``"authenticated"``, ``"admin"``).
            :param metadata: Optional dictionary of additional metadata.
        """
        self.path = path
        self.methods = list(methods)
        self.handler = handler
        self.access_policy = access_policy
        self.metadata = metadata if metadata is not None else {}

        return

    def requires_auth(self) -> bool:
        """
            Determine whether this route requires authentication.

            A route requires authentication when its access policy is
            anything other than ``"public"``.

            :returns: ``True`` if authentication is required.
        """
        return self.access_policy != "public"

    def to_dict(self) -> Dict[str, Any]:
        """
            Convert the route entry to a dictionary.

            :returns: A dictionary representation of the route entry.
        """
        result = {
            "path": self.path,
            "methods": list(self.methods),
            "handler": self.handler,
            "access_policy": self.access_policy,
            "auth_required": self.requires_auth(),
        }

        return result

    def to_verbose_dict(self) -> Dict[str, Any]:
        """
            Convert the route entry to a dictionary with metadata.

            :returns: A dictionary representation including metadata.
        """
        result = self.to_dict()
        result["metadata"] = dict(self.metadata)

        return result


# =============================================================================
# Route Registry Interface
# =============================================================================

class RouteRegistry:
    """
        Abstract interface for retrieving registered routes.

        Users of the framework provide a concrete implementation of this
        class to supply route information from their application. The
        CLI routes command delegates route retrieval to the registry,
        keeping the CLI framework independent of any specific routing
        implementation.
    """

    def get_routes(self) -> List[RouteEntry]:
        """
            Get all registered routes.

            :returns: A list of :class:`RouteEntry` instances.

            :raises: NotImplementedError
        """
        raise NotImplementedError("Subclasses must implement the get_routes method.")


class WebApplicationRouteRegistry(RouteRegistry):
    """
        Route registry that reads the routes of a web application persona.

        The routes come from the application's router, which holds every
        endpoint the application serves: handlers collected into its
        endpoint registry, routes attached with ``attach_route`` and the
        endpoints of its blueprints. Before the router exists (the
        application has not been started) the endpoint registry is used.

        :param webapp: The ``WebApplication`` persona to read routes from.
    """

    def __init__(self, webapp: Any):
        """
            Construct a WebApplicationRouteRegistry.

            :param webapp: The ``WebApplication`` persona to read routes from.
        """
        self._webapp = webapp
        return

    def get_routes(self) -> List[RouteEntry]:
        """
            Get the routes of the web application.

            Routes that share a path and handler are merged into one entry
            listing all their methods, ordered by path.

            :returns: A list of :class:`RouteEntry` instances.
        """
        from ccai.webworks.persona.lifecycle import LifecycleError

        pairs = []

        try:
            router = self._webapp.router
        except LifecycleError:
            # The application was not started, so no router exists yet.
            router = None

        if router is not None:
            # The router keeps its route table as (path, method, descriptor)
            # tuples and offers no public accessor for it.
            for path, method, descriptor in getattr(router, "_routes", []):
                pairs.append((path, method, descriptor))
        else:
            for descriptor in self._webapp.registry.collect():
                path = self._get_descriptor_path(descriptor)
                for method in descriptor.methods:
                    pairs.append((path, method.upper(), descriptor))

        entries: Dict[Any, RouteEntry] = {}

        for path, method, descriptor in pairs:
            key = (path, id(descriptor))

            if key in entries:
                if method not in entries[key].methods:
                    entries[key].methods.append(method)
            else:
                entries[key] = self._build_entry(path, method, descriptor)

        routes = sorted(entries.values(), key=lambda entry: (entry.path, entry.handler))

        return routes

    def _get_descriptor_path(self, descriptor: Any) -> str:
        """
            Get the URL path an endpoint descriptor is served at.

            :param descriptor: The endpoint descriptor.

            :returns: The URL path string.
        """
        if descriptor.path is not None:
            path = descriptor.path
        elif descriptor.leaf is not None:
            path = "/{}".format(descriptor.leaf)
        else:
            path = "/"

        return path

    def _build_entry(self, path: str, method: str, descriptor: Any) -> RouteEntry:
        """
            Build a route entry from an endpoint descriptor.

            :param path: The path the route is served at.
            :param method: The first HTTP method of the route.
            :param descriptor: The endpoint descriptor.

            :returns: The :class:`RouteEntry`.
        """
        handler = descriptor.handler
        handler_name = getattr(handler, "__qualname__", getattr(handler, "__name__", repr(handler)))
        handler_label = "{}.{}".format(descriptor.module, handler_name)

        access_policy = "public"
        policy = descriptor.constraints.access_policy

        if policy is not None and policy.require_auth:
            access_policy = "authenticated"

        metadata: Dict[str, Any] = {}

        if policy is not None and policy.roles:
            metadata["roles"] = ",".join(sorted(policy.roles))

        if policy is not None and policy.scopes:
            metadata["scopes"] = ",".join(sorted(policy.scopes))

        if descriptor.version is not None:
            metadata["version"] = descriptor.version

        if descriptor.tags:
            metadata["tags"] = ",".join(descriptor.tags)

        if descriptor.doc is not None and descriptor.doc.summary:
            metadata["summary"] = descriptor.doc.summary

        entry = RouteEntry(
            path=path,
            methods=[method],
            handler=handler_label,
            access_policy=access_policy,
            metadata=metadata,
        )

        return entry


# =============================================================================
# Helper Functions
# =============================================================================

def resolve_registry(config: Dict[str, Any], args: Any = None) -> Optional[RouteRegistry]:
    """
        Resolve the route registry for the routes command.

        A :class:`RouteRegistry` instance under the ``route_registry``
        configuration key is used when present. Otherwise the application
        named by ``--app`` or the ``server.app`` configuration key is
        imported and its web application persona is wrapped in a
        :class:`WebApplicationRouteRegistry`.

        :param config: Loaded configuration dictionary.
        :param args: Parsed command-line arguments, or ``None``.

        :returns: The route registry instance or None if no registry is
            configured and no application target is given.

        :raises ApplicationLoadError: If the application target cannot be
            imported or the application established no persona.
    """
    registry = config.get("route_registry", None)

    if registry is not None and isinstance(registry, RouteRegistry):
        return registry

    target = resolve_app_target(args, config)

    if target is None:
        return None

    application = load_application(target)
    webapp = find_webapp_persona(application)

    if webapp is None:
        errmsg = (
            "The application '{}' did not establish a web application persona, "
            "so its routes cannot be listed.".format(target)
        )
        raise ApplicationLoadError(errmsg)

    registry = WebApplicationRouteRegistry(webapp)

    return registry


def filter_routes(routes: List[RouteEntry], pattern: str) -> List[RouteEntry]:
    """
        Filter routes by path pattern using glob-style matching.

        The pattern is matched against each route's path using
        :func:`fnmatch.fnmatch`. Routes whose path matches the
        pattern are included in the result.

        :param routes: The list of routes to filter.
        :param pattern: The glob-style pattern to match against paths.

        :returns: A list of matching route entries.
    """
    matched = []

    for route in routes:
        if fnmatch.fnmatch(route.path, pattern):
            matched.append(route)

    return matched


# =============================================================================
# Output Formatters
# =============================================================================

def format_methods(methods: List[str]) -> str:
    """
        Format a list of HTTP methods as a comma-separated string.

        :param methods: A list of HTTP method names.

        :returns: A comma-separated string of methods.
    """
    return ",".join(sorted(methods))


def format_auth_indicator(requires_auth: bool) -> str:
    """
        Format the authentication indicator for display.

        :param requires_auth: Whether the route requires authentication.

        :returns: A string indicator for authentication status.
    """
    if requires_auth:
        return "[auth]"

    return ""


def format_table(routes: List[RouteEntry], verbose: bool = False) -> str:
    """
        Format routes as a text table.

        The table includes columns for path, methods, handler, access
        policy, and authentication indicator. When verbose is enabled,
        an additional metadata column is included.

        :param routes: The list of routes to format.
        :param verbose: Whether to include metadata in the output.

        :returns: A formatted table string.
    """
    if len(routes) == 0:
        return "No routes registered."

    headers = ["Path", "Methods", "Handler", "Access Policy", "Auth"]

    if verbose:
        headers.append("Metadata")

    rows = []

    for route in routes:
        auth_indicator = format_auth_indicator(route.requires_auth())
        row = [
            route.path,
            format_methods(route.methods),
            route.handler,
            route.access_policy,
            auth_indicator,
        ]

        if verbose:
            metadata_str = _format_metadata(route.metadata)
            row.append(metadata_str)

        rows.append(row)

    col_widths = []

    for col_index in range(len(headers)):
        header_width = len(headers[col_index])
        max_data_width = 0

        for row in rows:
            cell_width = len(row[col_index])
            if cell_width > max_data_width:
                max_data_width = cell_width

        col_width = max(header_width, max_data_width)
        col_widths.append(col_width)

    lines = []

    header_parts = []
    for col_index in range(len(headers)):
        header_parts.append(headers[col_index].ljust(col_widths[col_index]))
    header_line = "  ".join(header_parts)
    lines.append(header_line)

    separator_parts = []
    for width in col_widths:
        separator_parts.append("-" * width)
    separator_line = "  ".join(separator_parts)
    lines.append(separator_line)

    for row in rows:
        row_parts = []
        for col_index in range(len(row)):
            row_parts.append(row[col_index].ljust(col_widths[col_index]))
        row_line = "  ".join(row_parts)
        lines.append(row_line)

    return "\n".join(lines)


def _format_metadata(metadata: Dict[str, Any]) -> str:
    """
        Format metadata dictionary as a compact string.

        :param metadata: The metadata dictionary.

        :returns: A compact string representation.
    """
    if len(metadata) == 0:
        return ""

    parts = []

    for key in sorted(metadata.keys()):
        parts.append("{}={}".format(key, metadata[key]))

    return "; ".join(parts)


def format_json(routes: List[RouteEntry], verbose: bool = False) -> str:
    """
        Format routes as a JSON string.

        :param routes: The list of routes to format.
        :param verbose: Whether to include metadata in the output.

        :returns: A JSON-formatted string.
    """
    if verbose:
        data = [route.to_verbose_dict() for route in routes]
    else:
        data = [route.to_dict() for route in routes]

    return json.dumps(data, indent=2)


def format_csv(routes: List[RouteEntry], verbose: bool = False) -> str:
    """
        Format routes as CSV text.

        :param routes: The list of routes to format.
        :param verbose: Whether to include metadata in the output.

        :returns: A CSV-formatted string.
    """
    headers = ["path", "methods", "handler", "access_policy", "auth_required"]

    if verbose:
        headers.append("metadata")

    lines = [",".join(headers)]

    for route in routes:
        auth_required = "true" if route.requires_auth() else "false"
        row = [
            route.path,
            format_methods(route.methods),
            route.handler,
            route.access_policy,
            auth_required,
        ]

        if verbose:
            metadata_str = _format_metadata(route.metadata)
            row.append(metadata_str)

        lines.append(",".join(row))

    return "\n".join(lines)


# =============================================================================
# RoutesCommand
# =============================================================================

SUPPORTED_FORMATS = ("table", "json", "csv")


class RoutesCommand(CLICommand):
    """
        CLI command for displaying all registered endpoints.

        The ``routes`` command retrieves route information from the
        configured route registry and displays it in the requested
        format. It supports filtering by path pattern, verbose output
        with additional metadata, and authentication indicators.

        Usage::

            webworks routes
            webworks routes --format json
            webworks routes --filter "/api/*"
            webworks routes --verbose
            webworks routes --format csv --filter "/admin/*" --verbose
    """

    name = "routes"
    help = "Display all registered endpoints."

    def add_arguments(self, parser: "ArgumentParser") -> None:
        """
            Add command-specific arguments to the parser.

            Registers the ``--app``, ``--format``, ``--filter``, and
            ``--verbose`` options.

            ``--app`` and ``--verbose`` also exist as global options. They
            have no default here, so a value given before the command name
            (``webworks --verbose routes``) is not overwritten by this
            command's default.

            :param parser: The argument parser to add arguments to.
        """
        parser.add_argument(
            "--app",
            type=str,
            default=argparse.SUPPRESS,
            help="Application import target 'module:attribute', for example 'app:app'."
        )

        parser.add_argument(
            "--format",
            type=str,
            default="table",
            choices=list(SUPPORTED_FORMATS),
            dest="output_format",
            help="Output format: table, json, or csv. Default is table."
        )

        parser.add_argument(
            "--filter",
            type=str,
            default=None,
            dest="path_filter",
            help="Filter routes by path pattern (glob-style matching)."
        )

        parser.add_argument(
            "--verbose",
            action="store_true",
            default=argparse.SUPPRESS,
            help="Show additional endpoint metadata."
        )

        return

    def execute(self, args: "Namespace", config: Dict[str, Any]) -> int:
        """
            Execute the routes command.

            Resolves the route registry from configuration, retrieves
            all routes, applies optional filtering, and formats the
            output according to the requested format.

            :param args: Parsed command-line arguments.
            :param config: Loaded configuration dictionary.

            :returns: Exit code where 0 indicates success.
        """
        try:
            registry = resolve_registry(config, args)
        except ApplicationLoadError as err:
            print("Error: {}".format(err), file=sys.stderr)
            return EXIT_CONFIG_ERROR

        if registry is None:
            print(
                "Error: No route registry configured. Name the application with "
                "--app 'module:attribute' or the 'server.app' configuration key."
            )
            return EXIT_CONFIG_ERROR

        try:
            routes = registry.get_routes()
        except Exception as err:
            errmsg = "Error: Failed to retrieve routes: {}".format(str(err))
            print(errmsg)
            return EXIT_CONFIG_ERROR

        path_filter = getattr(args, "path_filter", None)

        if path_filter is not None:
            routes = filter_routes(routes, path_filter)

        output_format = getattr(args, "output_format", "table")
        verbose = getattr(args, "verbose", False)

        if output_format == "json":
            output = format_json(routes, verbose=verbose)
        elif output_format == "csv":
            output = format_csv(routes, verbose=verbose)
        else:
            output = format_table(routes, verbose=verbose)

        print(output)

        return EXIT_SUCCESS
