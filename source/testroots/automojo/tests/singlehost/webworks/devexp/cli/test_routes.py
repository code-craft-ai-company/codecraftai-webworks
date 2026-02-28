"""
    Tests for the CLI routes command.

    This module contains unit tests for the :class:`RoutesCommand`,
    :class:`RouteEntry`, :class:`RouteRegistry`, and the helper
    functions :func:`resolve_registry`, :func:`filter_routes`,
    :func:`format_table`, :func:`format_json`, :func:`format_csv`,
    :func:`format_methods`, and :func:`format_auth_indicator`.
"""

from argparse import ArgumentParser, Namespace
from typing import Any, Dict, List

from automojo.webworks.devexp.cli.exitcodes import EXIT_CONFIG_ERROR
from automojo.webworks.devexp.cli.exitcodes import EXIT_SUCCESS
from automojo.webworks.devexp.cli.routes import RouteEntry
from automojo.webworks.devexp.cli.routes import RouteRegistry
from automojo.webworks.devexp.cli.routes import RoutesCommand
from automojo.webworks.devexp.cli.routes import SUPPORTED_FORMATS
from automojo.webworks.devexp.cli.routes import filter_routes
from automojo.webworks.devexp.cli.routes import format_auth_indicator
from automojo.webworks.devexp.cli.routes import format_csv
from automojo.webworks.devexp.cli.routes import format_json
from automojo.webworks.devexp.cli.routes import format_methods
from automojo.webworks.devexp.cli.routes import format_table
from automojo.webworks.devexp.cli.routes import resolve_registry


# =============================================================================
# Test Helpers
# =============================================================================

class _TestRegistry(RouteRegistry):
    """
        A concrete route registry for testing.

        Returns a configurable list of route entries.
    """

    def __init__(self, routes: List[RouteEntry] = None):
        self._routes = routes if routes is not None else []
        self._fail = False
        return

    def get_routes(self) -> List[RouteEntry]:
        if self._fail:
            raise RuntimeError("Failed to retrieve routes")
        return list(self._routes)


def _make_route(
    path: str = "/",
    methods: List[str] = None,
    handler: str = "index",
    access_policy: str = "public",
    metadata: Dict[str, Any] = None
) -> RouteEntry:
    """
        Create a RouteEntry for testing.

        :returns: A RouteEntry instance.
    """
    if methods is None:
        methods = ["GET"]

    return RouteEntry(
        path=path,
        methods=methods,
        handler=handler,
        access_policy=access_policy,
        metadata=metadata,
    )


def _make_args(**kwargs) -> Namespace:
    """
        Create a Namespace object with the given keyword arguments.

        :returns: A Namespace instance.
    """
    defaults = {
        "output_format": "table",
        "path_filter": None,
        "verbose": False,
    }
    defaults.update(kwargs)
    return Namespace(**defaults)


def _make_config(registry=None) -> Dict[str, Any]:
    """
        Create a configuration dictionary for testing.

        :param registry: Optional route registry instance.

        :returns: A configuration dictionary.
    """
    config = {}

    if registry is not None:
        config["route_registry"] = registry

    return config


def _sample_routes() -> List[RouteEntry]:
    """
        Create a standard set of sample routes for testing.

        :returns: A list of RouteEntry instances.
    """
    return [
        _make_route(
            path="/",
            methods=["GET"],
            handler="home_handler",
            access_policy="public",
        ),
        _make_route(
            path="/api/users",
            methods=["GET", "POST"],
            handler="users_handler",
            access_policy="authenticated",
            metadata={"version": "v1", "deprecated": False},
        ),
        _make_route(
            path="/api/users/{id}",
            methods=["GET", "PUT", "DELETE"],
            handler="user_detail_handler",
            access_policy="authenticated",
            metadata={"version": "v1"},
        ),
        _make_route(
            path="/admin/dashboard",
            methods=["GET"],
            handler="admin_dashboard",
            access_policy="admin",
        ),
        _make_route(
            path="/health",
            methods=["GET"],
            handler="health_check",
            access_policy="public",
        ),
    ]


# =============================================================================
# Unit Tests for RouteEntry
# =============================================================================

def test_route_entry_attributes():
    """
        Test that RouteEntry stores all attributes correctly.
    """
    route = RouteEntry(
        path="/api/test",
        methods=["GET", "POST"],
        handler="test_handler",
        access_policy="authenticated",
        metadata={"version": "v2"},
    )

    if route.path != "/api/test":
        errmsg = "Expected path '/api/test', got '{}'.".format(route.path)
        raise AssertionError(errmsg)

    if route.methods != ["GET", "POST"]:
        errmsg = "Expected methods ['GET', 'POST'], got {}.".format(route.methods)
        raise AssertionError(errmsg)

    if route.handler != "test_handler":
        errmsg = "Expected handler 'test_handler', got '{}'.".format(route.handler)
        raise AssertionError(errmsg)

    if route.access_policy != "authenticated":
        errmsg = "Expected access_policy 'authenticated', got '{}'.".format(route.access_policy)
        raise AssertionError(errmsg)

    if route.metadata != {"version": "v2"}:
        errmsg = "Expected metadata with version v2, got {}.".format(route.metadata)
        raise AssertionError(errmsg)

    return


def test_route_entry_default_access_policy():
    """
        Test that RouteEntry defaults access_policy to 'public'.
    """
    route = RouteEntry(path="/", methods=["GET"], handler="index")

    if route.access_policy != "public":
        errmsg = "Expected default access_policy 'public', got '{}'.".format(route.access_policy)
        raise AssertionError(errmsg)

    return


def test_route_entry_default_metadata():
    """
        Test that RouteEntry defaults metadata to an empty dict.
    """
    route = RouteEntry(path="/", methods=["GET"], handler="index")

    if route.metadata != {}:
        errmsg = "Expected default metadata {{}}, got {}.".format(route.metadata)
        raise AssertionError(errmsg)

    return


def test_route_entry_requires_auth_public():
    """
        Test that a public route does not require authentication.
    """
    route = _make_route(access_policy="public")

    if route.requires_auth() is not False:
        errmsg = "Expected requires_auth() to be False for public route."
        raise AssertionError(errmsg)

    return


def test_route_entry_requires_auth_authenticated():
    """
        Test that an authenticated route requires authentication.
    """
    route = _make_route(access_policy="authenticated")

    if route.requires_auth() is not True:
        errmsg = "Expected requires_auth() to be True for authenticated route."
        raise AssertionError(errmsg)

    return


def test_route_entry_requires_auth_admin():
    """
        Test that an admin route requires authentication.
    """
    route = _make_route(access_policy="admin")

    if route.requires_auth() is not True:
        errmsg = "Expected requires_auth() to be True for admin route."
        raise AssertionError(errmsg)

    return


def test_route_entry_to_dict():
    """
        Test that to_dict returns the expected dictionary.
    """
    route = _make_route(
        path="/api/test",
        methods=["GET", "POST"],
        handler="test_handler",
        access_policy="authenticated",
    )

    result = route.to_dict()

    if result["path"] != "/api/test":
        errmsg = "Expected path '/api/test' in dict, got '{}'.".format(result["path"])
        raise AssertionError(errmsg)

    if result["methods"] != ["GET", "POST"]:
        errmsg = "Expected methods ['GET', 'POST'] in dict, got {}.".format(result["methods"])
        raise AssertionError(errmsg)

    if result["handler"] != "test_handler":
        errmsg = "Expected handler 'test_handler' in dict, got '{}'.".format(result["handler"])
        raise AssertionError(errmsg)

    if result["access_policy"] != "authenticated":
        errmsg = "Expected access_policy 'authenticated' in dict."
        raise AssertionError(errmsg)

    if result["auth_required"] is not True:
        errmsg = "Expected auth_required True in dict."
        raise AssertionError(errmsg)

    return


def test_route_entry_to_dict_does_not_include_metadata():
    """
        Test that to_dict does not include metadata.
    """
    route = _make_route(metadata={"version": "v1"})

    result = route.to_dict()

    if "metadata" in result:
        errmsg = "Expected to_dict to not include metadata key."
        raise AssertionError(errmsg)

    return


def test_route_entry_to_verbose_dict_includes_metadata():
    """
        Test that to_verbose_dict includes metadata.
    """
    route = _make_route(metadata={"version": "v1", "deprecated": False})

    result = route.to_verbose_dict()

    if "metadata" not in result:
        errmsg = "Expected to_verbose_dict to include metadata key."
        raise AssertionError(errmsg)

    if result["metadata"] != {"version": "v1", "deprecated": False}:
        errmsg = "Expected metadata to match, got {}.".format(result["metadata"])
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for resolve_registry
# =============================================================================

def test_resolve_registry_returns_registry():
    """
        Test that resolve_registry returns the registry when configured.
    """
    registry = _TestRegistry()
    config = {"route_registry": registry}

    result = resolve_registry(config)

    if result is not registry:
        errmsg = "Expected the configured registry instance."
        raise AssertionError(errmsg)

    return


def test_resolve_registry_returns_none_when_missing():
    """
        Test that resolve_registry returns None when no registry is configured.
    """
    config = {}

    result = resolve_registry(config)

    if result is not None:
        errmsg = "Expected None when no registry configured."
        raise AssertionError(errmsg)

    return


def test_resolve_registry_returns_none_for_non_registry():
    """
        Test that resolve_registry returns None when the value is not a RouteRegistry.
    """
    config = {"route_registry": "not-a-registry"}

    result = resolve_registry(config)

    if result is not None:
        errmsg = "Expected None for non-RouteRegistry value."
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for filter_routes
# =============================================================================

def test_filter_routes_matches_pattern():
    """
        Test that filter_routes returns routes matching the pattern.
    """
    routes = _sample_routes()

    result = filter_routes(routes, "/api/*")

    if len(result) != 2:
        errmsg = "Expected 2 matching routes, got {}.".format(len(result))
        raise AssertionError(errmsg)

    paths = [r.path for r in result]

    if "/api/users" not in paths:
        errmsg = "Expected '/api/users' in filtered results."
        raise AssertionError(errmsg)

    if "/api/users/{id}" not in paths:
        errmsg = "Expected '/api/users/{{id}}' in filtered results."
        raise AssertionError(errmsg)

    return


def test_filter_routes_no_match():
    """
        Test that filter_routes returns empty list when no routes match.
    """
    routes = _sample_routes()

    result = filter_routes(routes, "/nonexistent/*")

    if len(result) != 0:
        errmsg = "Expected 0 matching routes, got {}.".format(len(result))
        raise AssertionError(errmsg)

    return


def test_filter_routes_exact_match():
    """
        Test that filter_routes supports exact path matching.
    """
    routes = _sample_routes()

    result = filter_routes(routes, "/health")

    if len(result) != 1:
        errmsg = "Expected 1 matching route, got {}.".format(len(result))
        raise AssertionError(errmsg)

    if result[0].path != "/health":
        errmsg = "Expected path '/health', got '{}'.".format(result[0].path)
        raise AssertionError(errmsg)

    return


def test_filter_routes_wildcard_all():
    """
        Test that filter_routes with '*' matches all top-level routes.
    """
    routes = [
        _make_route(path="/a"),
        _make_route(path="/b"),
    ]

    result = filter_routes(routes, "/*")

    if len(result) != 2:
        errmsg = "Expected 2 matching routes, got {}.".format(len(result))
        raise AssertionError(errmsg)

    return


def test_filter_routes_admin_pattern():
    """
        Test that filter_routes matches admin routes.
    """
    routes = _sample_routes()

    result = filter_routes(routes, "/admin/*")

    if len(result) != 1:
        errmsg = "Expected 1 matching route, got {}.".format(len(result))
        raise AssertionError(errmsg)

    if result[0].path != "/admin/dashboard":
        errmsg = "Expected path '/admin/dashboard', got '{}'.".format(result[0].path)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for format_methods
# =============================================================================

def test_format_methods_single():
    """
        Test that format_methods formats a single method.
    """
    result = format_methods(["GET"])

    if result != "GET":
        errmsg = "Expected 'GET', got '{}'.".format(result)
        raise AssertionError(errmsg)

    return


def test_format_methods_multiple_sorted():
    """
        Test that format_methods sorts and joins multiple methods.
    """
    result = format_methods(["POST", "GET", "DELETE"])

    if result != "DELETE,GET,POST":
        errmsg = "Expected 'DELETE,GET,POST', got '{}'.".format(result)
        raise AssertionError(errmsg)

    return


def test_format_methods_empty():
    """
        Test that format_methods handles empty list.
    """
    result = format_methods([])

    if result != "":
        errmsg = "Expected empty string, got '{}'.".format(result)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for format_auth_indicator
# =============================================================================

def test_format_auth_indicator_requires_auth():
    """
        Test that format_auth_indicator returns '[auth]' when auth is required.
    """
    result = format_auth_indicator(True)

    if result != "[auth]":
        errmsg = "Expected '[auth]', got '{}'.".format(result)
        raise AssertionError(errmsg)

    return


def test_format_auth_indicator_no_auth():
    """
        Test that format_auth_indicator returns empty string when no auth.
    """
    result = format_auth_indicator(False)

    if result != "":
        errmsg = "Expected empty string, got '{}'.".format(result)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for format_table
# =============================================================================

def test_format_table_no_routes():
    """
        Test that format_table returns a message when no routes exist.
    """
    result = format_table([])

    if result != "No routes registered.":
        errmsg = "Expected 'No routes registered.', got '{}'.".format(result)
        raise AssertionError(errmsg)

    return


def test_format_table_contains_headers():
    """
        Test that format_table output contains column headers.
    """
    routes = [_make_route(path="/test", handler="test_handler")]

    result = format_table(routes)

    if "Path" not in result:
        errmsg = "Expected 'Path' header in table output."
        raise AssertionError(errmsg)

    if "Methods" not in result:
        errmsg = "Expected 'Methods' header in table output."
        raise AssertionError(errmsg)

    if "Handler" not in result:
        errmsg = "Expected 'Handler' header in table output."
        raise AssertionError(errmsg)

    if "Access Policy" not in result:
        errmsg = "Expected 'Access Policy' header in table output."
        raise AssertionError(errmsg)

    if "Auth" not in result:
        errmsg = "Expected 'Auth' header in table output."
        raise AssertionError(errmsg)

    return


def test_format_table_contains_route_data():
    """
        Test that format_table output contains route data.
    """
    routes = [
        _make_route(
            path="/api/users",
            methods=["GET", "POST"],
            handler="users_handler",
            access_policy="authenticated",
        ),
    ]

    result = format_table(routes)

    if "/api/users" not in result:
        errmsg = "Expected '/api/users' in table output."
        raise AssertionError(errmsg)

    if "users_handler" not in result:
        errmsg = "Expected 'users_handler' in table output."
        raise AssertionError(errmsg)

    if "authenticated" not in result:
        errmsg = "Expected 'authenticated' in table output."
        raise AssertionError(errmsg)

    if "[auth]" not in result:
        errmsg = "Expected '[auth]' indicator in table output."
        raise AssertionError(errmsg)

    return


def test_format_table_contains_separator():
    """
        Test that format_table output contains a separator line.
    """
    routes = [_make_route()]

    result = format_table(routes)
    lines = result.split("\n")

    if len(lines) < 3:
        errmsg = "Expected at least 3 lines (header, separator, data), got {}.".format(len(lines))
        raise AssertionError(errmsg)

    separator = lines[1]
    has_dashes = "-" in separator

    if has_dashes is not True:
        errmsg = "Expected separator line with dashes."
        raise AssertionError(errmsg)

    return


def test_format_table_verbose_includes_metadata():
    """
        Test that format_table with verbose includes metadata column.
    """
    routes = [
        _make_route(metadata={"version": "v1"}),
    ]

    result = format_table(routes, verbose=True)

    if "Metadata" not in result:
        errmsg = "Expected 'Metadata' header in verbose table output."
        raise AssertionError(errmsg)

    if "version=v1" not in result:
        errmsg = "Expected 'version=v1' in verbose table output."
        raise AssertionError(errmsg)

    return


def test_format_table_public_route_no_auth_indicator():
    """
        Test that format_table shows no auth indicator for public routes.
    """
    routes = [_make_route(access_policy="public")]

    result = format_table(routes)

    if "[auth]" in result:
        errmsg = "Expected no '[auth]' indicator for public route."
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for format_json
# =============================================================================

def test_format_json_empty_routes():
    """
        Test that format_json returns empty JSON array for no routes.
    """
    import json as json_mod

    result = format_json([])
    parsed = json_mod.loads(result)

    if parsed != []:
        errmsg = "Expected empty JSON array, got {}.".format(parsed)
        raise AssertionError(errmsg)

    return


def test_format_json_contains_route_data():
    """
        Test that format_json output contains route data.
    """
    import json as json_mod

    routes = [
        _make_route(
            path="/api/test",
            methods=["GET"],
            handler="test_handler",
            access_policy="public",
        ),
    ]

    result = format_json(routes)
    parsed = json_mod.loads(result)

    if len(parsed) != 1:
        errmsg = "Expected 1 route in JSON, got {}.".format(len(parsed))
        raise AssertionError(errmsg)

    entry = parsed[0]

    if entry["path"] != "/api/test":
        errmsg = "Expected path '/api/test' in JSON."
        raise AssertionError(errmsg)

    if entry["handler"] != "test_handler":
        errmsg = "Expected handler 'test_handler' in JSON."
        raise AssertionError(errmsg)

    if entry["auth_required"] is not False:
        errmsg = "Expected auth_required False in JSON."
        raise AssertionError(errmsg)

    return


def test_format_json_no_metadata_by_default():
    """
        Test that format_json does not include metadata by default.
    """
    import json as json_mod

    routes = [_make_route(metadata={"version": "v1"})]

    result = format_json(routes, verbose=False)
    parsed = json_mod.loads(result)

    if "metadata" in parsed[0]:
        errmsg = "Expected no metadata key in non-verbose JSON."
        raise AssertionError(errmsg)

    return


def test_format_json_verbose_includes_metadata():
    """
        Test that format_json with verbose includes metadata.
    """
    import json as json_mod

    routes = [_make_route(metadata={"version": "v1"})]

    result = format_json(routes, verbose=True)
    parsed = json_mod.loads(result)

    if "metadata" not in parsed[0]:
        errmsg = "Expected metadata key in verbose JSON."
        raise AssertionError(errmsg)

    if parsed[0]["metadata"] != {"version": "v1"}:
        errmsg = "Expected metadata to match."
        raise AssertionError(errmsg)

    return


def test_format_json_auth_required_field():
    """
        Test that format_json includes auth_required field.
    """
    import json as json_mod

    routes = [
        _make_route(access_policy="authenticated"),
        _make_route(access_policy="public"),
    ]

    result = format_json(routes)
    parsed = json_mod.loads(result)

    if parsed[0]["auth_required"] is not True:
        errmsg = "Expected auth_required True for authenticated route."
        raise AssertionError(errmsg)

    if parsed[1]["auth_required"] is not False:
        errmsg = "Expected auth_required False for public route."
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for format_csv
# =============================================================================

def test_format_csv_headers():
    """
        Test that format_csv output starts with headers.
    """
    result = format_csv([])
    lines = result.split("\n")

    expected_header = "path,methods,handler,access_policy,auth_required"

    if lines[0] != expected_header:
        errmsg = "Expected CSV header '{}', got '{}'.".format(expected_header, lines[0])
        raise AssertionError(errmsg)

    return


def test_format_csv_contains_route_data():
    """
        Test that format_csv output contains route data.
    """
    routes = [
        _make_route(
            path="/api/test",
            methods=["GET"],
            handler="test_handler",
            access_policy="public",
        ),
    ]

    result = format_csv(routes)
    lines = result.split("\n")

    if len(lines) != 2:
        errmsg = "Expected 2 lines (header + 1 data), got {}.".format(len(lines))
        raise AssertionError(errmsg)

    if "/api/test" not in lines[1]:
        errmsg = "Expected '/api/test' in CSV data line."
        raise AssertionError(errmsg)

    if "test_handler" not in lines[1]:
        errmsg = "Expected 'test_handler' in CSV data line."
        raise AssertionError(errmsg)

    if "false" not in lines[1]:
        errmsg = "Expected 'false' auth_required in CSV data line."
        raise AssertionError(errmsg)

    return


def test_format_csv_auth_required_true():
    """
        Test that format_csv shows 'true' for authenticated routes.
    """
    routes = [_make_route(access_policy="authenticated")]

    result = format_csv(routes)
    lines = result.split("\n")

    if "true" not in lines[1]:
        errmsg = "Expected 'true' auth_required in CSV data line."
        raise AssertionError(errmsg)

    return


def test_format_csv_verbose_includes_metadata_header():
    """
        Test that format_csv with verbose includes metadata header.
    """
    result = format_csv([], verbose=True)
    lines = result.split("\n")

    if "metadata" not in lines[0]:
        errmsg = "Expected 'metadata' in verbose CSV header."
        raise AssertionError(errmsg)

    return


def test_format_csv_verbose_includes_metadata_data():
    """
        Test that format_csv with verbose includes metadata in data rows.
    """
    routes = [_make_route(metadata={"version": "v1"})]

    result = format_csv(routes, verbose=True)
    lines = result.split("\n")

    if "version=v1" not in lines[1]:
        errmsg = "Expected 'version=v1' in verbose CSV data line."
        raise AssertionError(errmsg)

    return


def test_format_csv_multiple_routes():
    """
        Test that format_csv handles multiple routes.
    """
    routes = [
        _make_route(path="/a", handler="handler_a"),
        _make_route(path="/b", handler="handler_b"),
    ]

    result = format_csv(routes)
    lines = result.split("\n")

    if len(lines) != 3:
        errmsg = "Expected 3 lines (header + 2 data), got {}.".format(len(lines))
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for RoutesCommand
# =============================================================================

def test_routes_command_name():
    """
        Test that RoutesCommand has the correct name.
    """
    cmd = RoutesCommand()

    if cmd.name != "routes":
        errmsg = "Expected name 'routes', got '{}'.".format(cmd.name)
        raise AssertionError(errmsg)

    return


def test_routes_command_help():
    """
        Test that RoutesCommand has help text.
    """
    cmd = RoutesCommand()

    if len(cmd.help) == 0:
        errmsg = "Expected non-empty help text."
        raise AssertionError(errmsg)

    return


def test_routes_command_adds_format_argument():
    """
        Test that RoutesCommand adds the --format argument.
    """
    cmd = RoutesCommand()
    parser = ArgumentParser()

    cmd.add_arguments(parser)

    parsed = parser.parse_args(["--format", "json"])

    if parsed.output_format != "json":
        errmsg = "Expected output_format 'json', got '{}'.".format(parsed.output_format)
        raise AssertionError(errmsg)

    return


def test_routes_command_adds_filter_argument():
    """
        Test that RoutesCommand adds the --filter argument.
    """
    cmd = RoutesCommand()
    parser = ArgumentParser()

    cmd.add_arguments(parser)

    parsed = parser.parse_args(["--filter", "/api/*"])

    if parsed.path_filter != "/api/*":
        errmsg = "Expected path_filter '/api/*', got '{}'.".format(parsed.path_filter)
        raise AssertionError(errmsg)

    return


def test_routes_command_adds_verbose_argument():
    """
        Test that RoutesCommand adds the --verbose argument.
    """
    cmd = RoutesCommand()
    parser = ArgumentParser()

    cmd.add_arguments(parser)

    parsed = parser.parse_args(["--verbose"])

    if parsed.verbose is not True:
        errmsg = "Expected verbose True."
        raise AssertionError(errmsg)

    return


def test_routes_command_format_default_is_table():
    """
        Test that the --format argument defaults to 'table'.
    """
    cmd = RoutesCommand()
    parser = ArgumentParser()

    cmd.add_arguments(parser)

    parsed = parser.parse_args([])

    if parsed.output_format != "table":
        errmsg = "Expected default output_format 'table', got '{}'.".format(parsed.output_format)
        raise AssertionError(errmsg)

    return


def test_routes_command_filter_default_is_none():
    """
        Test that the --filter argument defaults to None.
    """
    cmd = RoutesCommand()
    parser = ArgumentParser()

    cmd.add_arguments(parser)

    parsed = parser.parse_args([])

    if parsed.path_filter is not None:
        errmsg = "Expected default path_filter None, got '{}'.".format(parsed.path_filter)
        raise AssertionError(errmsg)

    return


def test_routes_command_verbose_default_is_false():
    """
        Test that the --verbose argument defaults to False.
    """
    cmd = RoutesCommand()
    parser = ArgumentParser()

    cmd.add_arguments(parser)

    parsed = parser.parse_args([])

    if parsed.verbose is not False:
        errmsg = "Expected default verbose False."
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for RoutesCommand.execute
# =============================================================================

def test_routes_command_no_registry_returns_config_error():
    """
        Test that execute returns EXIT_CONFIG_ERROR when no registry is configured.
    """
    args = _make_args()
    config = {}

    cmd = RoutesCommand()
    exit_code = cmd.execute(args, config)

    if exit_code != EXIT_CONFIG_ERROR:
        errmsg = "Expected EXIT_CONFIG_ERROR, got {}.".format(exit_code)
        raise AssertionError(errmsg)

    return


def test_routes_command_success_with_routes():
    """
        Test that execute returns EXIT_SUCCESS when routes are available.
    """
    routes = _sample_routes()
    registry = _TestRegistry(routes=routes)
    args = _make_args()
    config = _make_config(registry=registry)

    cmd = RoutesCommand()
    exit_code = cmd.execute(args, config)

    if exit_code != EXIT_SUCCESS:
        errmsg = "Expected EXIT_SUCCESS, got {}.".format(exit_code)
        raise AssertionError(errmsg)

    return


def test_routes_command_success_with_empty_routes():
    """
        Test that execute returns EXIT_SUCCESS when no routes are registered.
    """
    registry = _TestRegistry(routes=[])
    args = _make_args()
    config = _make_config(registry=registry)

    cmd = RoutesCommand()
    exit_code = cmd.execute(args, config)

    if exit_code != EXIT_SUCCESS:
        errmsg = "Expected EXIT_SUCCESS, got {}.".format(exit_code)
        raise AssertionError(errmsg)

    return


def test_routes_command_registry_failure_returns_config_error():
    """
        Test that execute returns EXIT_CONFIG_ERROR when registry fails.
    """
    registry = _TestRegistry()
    registry._fail = True
    args = _make_args()
    config = _make_config(registry=registry)

    cmd = RoutesCommand()
    exit_code = cmd.execute(args, config)

    if exit_code != EXIT_CONFIG_ERROR:
        errmsg = "Expected EXIT_CONFIG_ERROR, got {}.".format(exit_code)
        raise AssertionError(errmsg)

    return


def test_routes_command_with_filter():
    """
        Test that execute applies the path filter.
    """
    routes = _sample_routes()
    registry = _TestRegistry(routes=routes)
    args = _make_args(path_filter="/api/*")
    config = _make_config(registry=registry)

    cmd = RoutesCommand()
    exit_code = cmd.execute(args, config)

    if exit_code != EXIT_SUCCESS:
        errmsg = "Expected EXIT_SUCCESS, got {}.".format(exit_code)
        raise AssertionError(errmsg)

    return


def test_routes_command_with_json_format():
    """
        Test that execute succeeds with JSON format.
    """
    routes = _sample_routes()
    registry = _TestRegistry(routes=routes)
    args = _make_args(output_format="json")
    config = _make_config(registry=registry)

    cmd = RoutesCommand()
    exit_code = cmd.execute(args, config)

    if exit_code != EXIT_SUCCESS:
        errmsg = "Expected EXIT_SUCCESS, got {}.".format(exit_code)
        raise AssertionError(errmsg)

    return


def test_routes_command_with_csv_format():
    """
        Test that execute succeeds with CSV format.
    """
    routes = _sample_routes()
    registry = _TestRegistry(routes=routes)
    args = _make_args(output_format="csv")
    config = _make_config(registry=registry)

    cmd = RoutesCommand()
    exit_code = cmd.execute(args, config)

    if exit_code != EXIT_SUCCESS:
        errmsg = "Expected EXIT_SUCCESS, got {}.".format(exit_code)
        raise AssertionError(errmsg)

    return


def test_routes_command_with_verbose():
    """
        Test that execute succeeds with verbose option.
    """
    routes = _sample_routes()
    registry = _TestRegistry(routes=routes)
    args = _make_args(verbose=True)
    config = _make_config(registry=registry)

    cmd = RoutesCommand()
    exit_code = cmd.execute(args, config)

    if exit_code != EXIT_SUCCESS:
        errmsg = "Expected EXIT_SUCCESS, got {}.".format(exit_code)
        raise AssertionError(errmsg)

    return


def test_routes_command_with_all_options():
    """
        Test that execute succeeds with all options combined.
    """
    routes = _sample_routes()
    registry = _TestRegistry(routes=routes)
    args = _make_args(output_format="json", path_filter="/api/*", verbose=True)
    config = _make_config(registry=registry)

    cmd = RoutesCommand()
    exit_code = cmd.execute(args, config)

    if exit_code != EXIT_SUCCESS:
        errmsg = "Expected EXIT_SUCCESS, got {}.".format(exit_code)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for SUPPORTED_FORMATS
# =============================================================================

def test_supported_formats_contains_table():
    """
        Test that SUPPORTED_FORMATS includes 'table'.
    """
    if "table" not in SUPPORTED_FORMATS:
        errmsg = "Expected 'table' in SUPPORTED_FORMATS."
        raise AssertionError(errmsg)

    return


def test_supported_formats_contains_json():
    """
        Test that SUPPORTED_FORMATS includes 'json'.
    """
    if "json" not in SUPPORTED_FORMATS:
        errmsg = "Expected 'json' in SUPPORTED_FORMATS."
        raise AssertionError(errmsg)

    return


def test_supported_formats_contains_csv():
    """
        Test that SUPPORTED_FORMATS includes 'csv'.
    """
    if "csv" not in SUPPORTED_FORMATS:
        errmsg = "Expected 'csv' in SUPPORTED_FORMATS."
        raise AssertionError(errmsg)

    return
