"""
    CLI database commands for the webworks developer experience.

    This module provides the :class:`DatabaseGroup` command group containing
    commands for database operations including initialization, migration,
    rollback, seeding, and status display. Each command delegates actual
    database operations to a user-provided database backend, making the
    framework agnostic to the underlying database technology.

    The backend is found from the application named by ``--app`` (or the
    ``server.app`` configuration key): a :class:`DatabaseBackend` the
    application exposes as ``database_backend`` is used directly, and
    otherwise :class:`WebApplicationDatabaseBackend` drives the database
    hooks of the application's web application persona. A backend instance
    can also be supplied under the ``database_backend`` configuration key.

    All commands support an ``--env`` option to specify the target
    environment. Migration commands include error handling that rolls
    back changes on failure.
"""

import argparse
import sys

from typing import Any, Dict, List, Optional, TYPE_CHECKING

from ccai.webworks.devexp.apploader import ApplicationLoadError
from ccai.webworks.devexp.apploader import find_webapp_persona
from ccai.webworks.devexp.apploader import load_application
from ccai.webworks.devexp.apploader import parse_app_target
from ccai.webworks.devexp.apploader import resolve_app_target
from ccai.webworks.devexp.cli.command import CLICommand
from ccai.webworks.devexp.cli.exitcodes import EXIT_CONFIG_ERROR
from ccai.webworks.devexp.cli.exitcodes import EXIT_ERROR
from ccai.webworks.devexp.cli.exitcodes import EXIT_SUCCESS
from ccai.webworks.devexp.cli.group import CLIGroup

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace


# =============================================================================
# Database Backend Interface
# =============================================================================

class DatabaseBackend:
    """
        Abstract interface for database operations.

        Users of the framework provide a concrete implementation of this
        class to perform actual database operations. The CLI commands
        delegate all database work to the backend, keeping the CLI
        framework independent of any specific database technology.
    """

    def initialize(self, env: str) -> None:
        """
            Initialize the database schema.

            :param env: The target environment name.

            :raises: RuntimeError if initialization fails.
        """
        raise NotImplementedError("Subclasses must implement the initialize method.")

    def get_pending_migrations(self, env: str) -> List[str]:
        """
            Get the list of pending migration names.

            :param env: The target environment name.

            :returns: A list of pending migration names.
        """
        raise NotImplementedError("Subclasses must implement the get_pending_migrations method.")

    def apply_migration(self, migration_name: str, env: str) -> None:
        """
            Apply a single migration.

            :param migration_name: The name of the migration to apply.
            :param env: The target environment name.

            :raises: RuntimeError if the migration fails.
        """
        raise NotImplementedError("Subclasses must implement the apply_migration method.")

    def rollback_migration(self, migration_name: str, env: str) -> None:
        """
            Rollback a single migration.

            :param migration_name: The name of the migration to rollback.
            :param env: The target environment name.

            :raises: RuntimeError if the rollback fails.
        """
        raise NotImplementedError("Subclasses must implement the rollback_migration method.")

    def get_applied_migrations(self, env: str) -> List[str]:
        """
            Get the list of applied migration names in order.

            :param env: The target environment name.

            :returns: A list of applied migration names.
        """
        raise NotImplementedError("Subclasses must implement the get_applied_migrations method.")

    def seed(self, env: str) -> None:
        """
            Populate the database with seed data.

            :param env: The target environment name.

            :raises: RuntimeError if seeding fails.
        """
        raise NotImplementedError("Subclasses must implement the seed method.")

    def get_status(self, env: str) -> Dict[str, Any]:
        """
            Get the current migration status.

            :param env: The target environment name.

            :returns: A dictionary containing migration status information
                with keys ``applied``, ``pending``, and ``current``.
        """
        raise NotImplementedError("Subclasses must implement the get_status method.")


class WebApplicationDatabaseBackend(DatabaseBackend):
    """
        Database backend that drives the hooks of a web application persona.

        ``WebApplication`` defines the database lifecycle as overridable
        hooks: ``prepare_database``, ``connect_database``,
        ``startup_database`` and ``ensure_database_ready``. ``db init``
        runs them in that order.

        The persona has no hooks for individual migrations or seed data.
        Those operations are forwarded to methods of the same name on the
        persona when the application's ``WebApplication`` subclass defines
        them, and otherwise fail with a message that says what to provide.

        :param webapp: The ``WebApplication`` persona.
    """

    def __init__(self, webapp: Any):
        """
            Construct a WebApplicationDatabaseBackend.

            :param webapp: The ``WebApplication`` persona.
        """
        self._webapp = webapp
        return

    def _call_persona(self, method_name: str, *args: Any) -> Any:
        """
            Call a database operation the persona may implement.

            :param method_name: The name of the operation.
            :param args: The arguments of the operation.

            :returns: The operation's result.

            :raises NotImplementedError: If the persona does not define the
                operation.
        """
        method = getattr(self._webapp, method_name, None)

        if method is None or not callable(method):
            errmsg = (
                "The application's {} does not implement '{}'. Define it on the "
                "WebApplication subclass, or expose a DatabaseBackend as 'database_backend' "
                "in the application module.".format(type(self._webapp).__name__, method_name)
            )
            raise NotImplementedError(errmsg)

        result = method(*args)

        return result

    def initialize(self, env: str) -> None:
        """
            Run the persona's database hooks in lifecycle order.

            :param env: The target environment name.

            :raises RuntimeError: If the persona reports that the database
                is not ready after its hooks ran.
        """
        self._webapp.prepare_database()
        self._webapp.connect_database()
        self._webapp.startup_database()

        ready = self._webapp.ensure_database_ready()

        if ready is not True:
            errmsg = "The application reports that the database is not ready."
            raise RuntimeError(errmsg)

        return

    def get_pending_migrations(self, env: str) -> List[str]:
        """
            Get the list of pending migration names from the persona.

            :param env: The target environment name.

            :returns: A list of pending migration names.
        """
        pending = self._call_persona("get_pending_migrations", env)
        return pending

    def apply_migration(self, migration_name: str, env: str) -> None:
        """
            Apply a single migration through the persona.

            :param migration_name: The name of the migration to apply.
            :param env: The target environment name.
        """
        self._call_persona("apply_migration", migration_name, env)
        return

    def rollback_migration(self, migration_name: str, env: str) -> None:
        """
            Rollback a single migration through the persona.

            :param migration_name: The name of the migration to rollback.
            :param env: The target environment name.
        """
        self._call_persona("rollback_migration", migration_name, env)
        return

    def get_applied_migrations(self, env: str) -> List[str]:
        """
            Get the list of applied migration names from the persona.

            :param env: The target environment name.

            :returns: A list of applied migration names.
        """
        applied = self._call_persona("get_applied_migrations", env)
        return applied

    def seed(self, env: str) -> None:
        """
            Populate the database with seed data through the persona.

            :param env: The target environment name.
        """
        self._call_persona("seed_database", env)
        return

    def get_status(self, env: str) -> Dict[str, Any]:
        """
            Get the current migration status from the persona.

            :param env: The target environment name.

            :returns: A dictionary with keys ``applied``, ``pending``, and
                ``current``.
        """
        applied = list(self.get_applied_migrations(env))
        pending = list(self.get_pending_migrations(env))

        current = None
        if len(applied) > 0:
            current = applied[-1]

        status = {
            "applied": applied,
            "pending": pending,
            "current": current,
        }

        return status


# =============================================================================
# Helper Functions
# =============================================================================

def resolve_env(args: "Namespace", config: Dict[str, Any]) -> str:
    """
        Resolve the target environment from arguments and configuration.

        The ``--env`` argument takes precedence over the ``env`` key in
        the configuration dictionary. If neither is provided, the default
        environment is ``development``.

        :param args: Parsed command-line arguments.
        :param config: Loaded configuration dictionary.

        :returns: The resolved environment name.
    """
    env_from_args = getattr(args, "env", None)

    if env_from_args is not None:
        return env_from_args

    env_from_config = config.get("env", None)

    if env_from_config is not None:
        return env_from_config

    return "development"


def resolve_backend(config: Dict[str, Any], args: Any = None) -> Optional[DatabaseBackend]:
    """
        Resolve the database backend for the database commands.

        The backend is found, in order, from:

        1. a :class:`DatabaseBackend` instance under the
           ``database_backend`` configuration key;
        2. the application named by ``--app`` or the ``server.app``
           configuration key, when its module or its web application
           persona exposes a :class:`DatabaseBackend` as
           ``database_backend``;
        3. the database hooks of that application's web application
           persona, wrapped in a :class:`WebApplicationDatabaseBackend`.

        :param config: Loaded configuration dictionary.
        :param args: Parsed command-line arguments, or ``None``.

        :returns: The database backend instance or None if no backend is
            configured and no application target is given.

        :raises ApplicationLoadError: If the application target cannot be
            imported, or the application offers neither a backend nor a
            persona.
    """
    backend = config.get("database_backend", None)

    if backend is not None and isinstance(backend, DatabaseBackend):
        return backend

    target = resolve_app_target(args, config)

    if target is None:
        return None

    application = load_application(target)

    # A backend exposed next to the application in its module.
    module_path, _attribute_path = parse_app_target(target)
    app_module = sys.modules.get(module_path, None)
    module_backend = getattr(app_module, "database_backend", None)

    if isinstance(module_backend, DatabaseBackend):
        return module_backend

    webapp = find_webapp_persona(application)

    if webapp is None:
        errmsg = (
            "The application '{}' exposes no 'database_backend' and did not establish "
            "a web application persona, so there are no database hooks to run.".format(target)
        )
        raise ApplicationLoadError(errmsg)

    persona_backend = getattr(webapp, "database_backend", None)

    if isinstance(persona_backend, DatabaseBackend):
        return persona_backend

    backend = WebApplicationDatabaseBackend(webapp)

    return backend


def find_backend(config: Dict[str, Any], args: Any) -> Optional[DatabaseBackend]:
    """
        Resolve the database backend for a command and report failures.

        Prints the reason to standard error when the application cannot be
        loaded, and a hint when nothing is configured.

        :param config: Loaded configuration dictionary.
        :param args: Parsed command-line arguments.

        :returns: The database backend, or None after an error was printed.
    """
    backend = None

    try:
        backend = resolve_backend(config, args)
    except ApplicationLoadError as err:
        print("Error: {}".format(err), file=sys.stderr)
        return None

    if backend is None:
        print(
            "Error: No database backend configured. Name the application with "
            "--app 'module:attribute' or the 'server.app' configuration key."
        )

    return backend


def add_env_argument(parser: "ArgumentParser") -> None:
    """
        Add the ``--env`` and ``--app`` arguments to a command parser.

        Both also exist as global options. They have no default here: a
        default on the subcommand would overwrite a value given before the
        command name, so ``webworks --env production db migrate`` would run
        against the default environment instead.

        :param parser: The argument parser to add the argument to.
    """
    parser.add_argument(
        "--env",
        type=str,
        default=argparse.SUPPRESS,
        help="Target environment (e.g., development, staging, production)."
    )

    parser.add_argument(
        "--app",
        type=str,
        default=argparse.SUPPRESS,
        help="Application import target 'module:attribute', for example 'app:app'."
    )

    return


# =============================================================================
# DbInitCommand
# =============================================================================

class DbInitCommand(CLICommand):
    """
        CLI command for initializing the database schema.

        The ``init`` command delegates to the configured database backend
        to create the initial database schema. It supports an ``--env``
        option to specify the target environment.

        Usage::

            webworks db init
            webworks db init --env production
    """

    name = "init"
    help = "Initialize the database schema."

    def add_arguments(self, parser: "ArgumentParser") -> None:
        """
            Add the ``--env`` argument to the parser.

            :param parser: The argument parser to add arguments to.
        """
        add_env_argument(parser)
        return

    def execute(self, args: "Namespace", config: Dict[str, Any]) -> int:
        """
            Execute the database initialization command.

            Resolves the database backend from configuration and calls
            its :meth:`initialize` method. If no backend is configured,
            an error message is printed and ``EXIT_CONFIG_ERROR`` is
            returned.

            :param args: Parsed command-line arguments.
            :param config: Loaded configuration dictionary.

            :returns: Exit code where 0 indicates success.
        """
        backend = find_backend(config, args)

        if backend is None:
            return EXIT_CONFIG_ERROR

        env = resolve_env(args, config)

        try:
            backend.initialize(env)
        except Exception as err:
            errmsg = "Error: Database initialization failed: {}".format(str(err))
            print(errmsg)
            return EXIT_ERROR

        print("Database initialized for '{}' environment.".format(env))
        return EXIT_SUCCESS


# =============================================================================
# DbMigrateCommand
# =============================================================================

class DbMigrateCommand(CLICommand):
    """
        CLI command for applying pending database migrations.

        The ``migrate`` command applies all pending migrations in order.
        If a migration fails, the command attempts to rollback the
        failed migration and reports the error.

        Usage::

            webworks db migrate
            webworks db migrate --env staging
    """

    name = "migrate"
    help = "Apply pending database migrations."

    def add_arguments(self, parser: "ArgumentParser") -> None:
        """
            Add the ``--env`` argument to the parser.

            :param parser: The argument parser to add arguments to.
        """
        add_env_argument(parser)
        return

    def execute(self, args: "Namespace", config: Dict[str, Any]) -> int:
        """
            Execute the database migration command.

            Retrieves pending migrations from the backend and applies
            them in order. If a migration fails, the command attempts
            to rollback the failed migration and returns ``EXIT_ERROR``.

            :param args: Parsed command-line arguments.
            :param config: Loaded configuration dictionary.

            :returns: Exit code where 0 indicates success.
        """
        backend = find_backend(config, args)

        if backend is None:
            return EXIT_CONFIG_ERROR

        env = resolve_env(args, config)

        try:
            pending = backend.get_pending_migrations(env)
        except Exception as err:
            errmsg = "Error: Failed to retrieve pending migrations: {}".format(str(err))
            print(errmsg)
            return EXIT_ERROR

        if len(pending) == 0:
            print("No pending migrations.")
            return EXIT_SUCCESS

        applied_count = 0

        for migration_name in pending:
            try:
                backend.apply_migration(migration_name, env)
                applied_count += 1
                print("Applied migration: {}".format(migration_name))
            except Exception as err:
                errmsg = "Error: Migration '{}' failed: {}".format(migration_name, str(err))
                print(errmsg)

                try:
                    backend.rollback_migration(migration_name, env)
                    print("Rolled back failed migration: {}".format(migration_name))
                except Exception as rollback_err:
                    rollback_msg = "Error: Rollback of '{}' also failed: {}".format(
                        migration_name, str(rollback_err)
                    )
                    print(rollback_msg)

                return EXIT_ERROR

        print("Applied {} migration(s) for '{}' environment.".format(applied_count, env))
        return EXIT_SUCCESS


# =============================================================================
# DbRollbackCommand
# =============================================================================

class DbRollbackCommand(CLICommand):
    """
        CLI command for reverting the last database migration.

        The ``rollback`` command reverts the most recently applied
        migration by delegating to the configured database backend.

        Usage::

            webworks db rollback
            webworks db rollback --env staging
    """

    name = "rollback"
    help = "Revert the last database migration."

    def add_arguments(self, parser: "ArgumentParser") -> None:
        """
            Add the ``--env`` argument to the parser.

            :param parser: The argument parser to add arguments to.
        """
        add_env_argument(parser)
        return

    def execute(self, args: "Namespace", config: Dict[str, Any]) -> int:
        """
            Execute the database rollback command.

            Retrieves the list of applied migrations and rolls back
            the most recent one. If no migrations have been applied,
            a message is printed and ``EXIT_SUCCESS`` is returned.

            :param args: Parsed command-line arguments.
            :param config: Loaded configuration dictionary.

            :returns: Exit code where 0 indicates success.
        """
        backend = find_backend(config, args)

        if backend is None:
            return EXIT_CONFIG_ERROR

        env = resolve_env(args, config)

        try:
            applied = backend.get_applied_migrations(env)
        except Exception as err:
            errmsg = "Error: Failed to retrieve applied migrations: {}".format(str(err))
            print(errmsg)
            return EXIT_ERROR

        if len(applied) == 0:
            print("No migrations to rollback.")
            return EXIT_SUCCESS

        last_migration = applied[-1]

        try:
            backend.rollback_migration(last_migration, env)
        except Exception as err:
            errmsg = "Error: Rollback of '{}' failed: {}".format(last_migration, str(err))
            print(errmsg)
            return EXIT_ERROR

        print("Rolled back migration: {}".format(last_migration))
        return EXIT_SUCCESS


# =============================================================================
# DbSeedCommand
# =============================================================================

class DbSeedCommand(CLICommand):
    """
        CLI command for populating the database with seed data.

        The ``seed`` command delegates to the configured database backend
        to populate the database with initial or test data.

        Usage::

            webworks db seed
            webworks db seed --env staging
    """

    name = "seed"
    help = "Populate the database with seed data."

    def add_arguments(self, parser: "ArgumentParser") -> None:
        """
            Add the ``--env`` argument to the parser.

            :param parser: The argument parser to add arguments to.
        """
        add_env_argument(parser)
        return

    def execute(self, args: "Namespace", config: Dict[str, Any]) -> int:
        """
            Execute the database seed command.

            Delegates to the backend's :meth:`seed` method to populate
            the database with seed data.

            :param args: Parsed command-line arguments.
            :param config: Loaded configuration dictionary.

            :returns: Exit code where 0 indicates success.
        """
        backend = find_backend(config, args)

        if backend is None:
            return EXIT_CONFIG_ERROR

        env = resolve_env(args, config)

        try:
            backend.seed(env)
        except Exception as err:
            errmsg = "Error: Database seeding failed: {}".format(str(err))
            print(errmsg)
            return EXIT_ERROR

        print("Database seeded for '{}' environment.".format(env))
        return EXIT_SUCCESS


# =============================================================================
# DbStatusCommand
# =============================================================================

class DbStatusCommand(CLICommand):
    """
        CLI command for displaying migration status and history.

        The ``status`` command retrieves the current migration status
        from the database backend and displays applied migrations,
        pending migrations, and the current migration version.

        Usage::

            webworks db status
            webworks db status --env production
    """

    name = "status"
    help = "Display migration status and history."

    def add_arguments(self, parser: "ArgumentParser") -> None:
        """
            Add the ``--env`` argument to the parser.

            :param parser: The argument parser to add arguments to.
        """
        add_env_argument(parser)
        return

    def execute(self, args: "Namespace", config: Dict[str, Any]) -> int:
        """
            Execute the database status command.

            Retrieves migration status from the backend and displays
            applied migrations, pending migrations, and the current
            migration version.

            :param args: Parsed command-line arguments.
            :param config: Loaded configuration dictionary.

            :returns: Exit code where 0 indicates success.
        """
        backend = find_backend(config, args)

        if backend is None:
            return EXIT_CONFIG_ERROR

        env = resolve_env(args, config)

        try:
            status = backend.get_status(env)
        except Exception as err:
            errmsg = "Error: Failed to retrieve migration status: {}".format(str(err))
            print(errmsg)
            return EXIT_ERROR

        applied = status.get("applied", [])
        pending = status.get("pending", [])
        current = status.get("current", None)

        print("Migration status for '{}' environment:".format(env))
        print("")

        if current is not None:
            print("Current migration: {}".format(current))
        else:
            print("Current migration: (none)")

        print("")
        print("Applied migrations ({})".format(len(applied)))

        for migration_name in applied:
            print("  [x] {}".format(migration_name))

        print("")
        print("Pending migrations ({})".format(len(pending)))

        for migration_name in pending:
            print("  [ ] {}".format(migration_name))

        return EXIT_SUCCESS


# =============================================================================
# DatabaseGroup
# =============================================================================

class DatabaseGroup(CLIGroup):
    """
        CLI command group for database operations.

        The ``db`` group organizes database-related commands under the
        ``webworks db`` namespace. It includes commands for initializing
        the database schema, applying and rolling back migrations,
        seeding data, and displaying migration status.

        Usage::

            webworks db init
            webworks db migrate
            webworks db rollback
            webworks db seed
            webworks db status
    """

    name = "db"
    help = "Database management commands."

    def __init__(self):
        """
            Initialize the DatabaseGroup with all database commands.
        """
        commands = [
            DbInitCommand(),
            DbMigrateCommand(),
            DbRollbackCommand(),
            DbSeedCommand(),
            DbStatusCommand(),
        ]

        super().__init__(name=self.name, help=self.help, commands=commands)

        return
