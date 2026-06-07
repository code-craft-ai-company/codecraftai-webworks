"""
    CLI database commands for the webworks developer experience.

    This module provides the :class:`DatabaseGroup` command group containing
    commands for database operations including initialization, migration,
    rollback, seeding, and status display. Each command delegates actual
    database operations to a user-provided database backend, making the
    framework agnostic to the underlying database technology.

    All commands support an ``--env`` option to specify the target
    environment. Migration commands include error handling that rolls
    back changes on failure.
"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING

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


def resolve_backend(config: Dict[str, Any]) -> Optional[DatabaseBackend]:
    """
        Resolve the database backend from configuration.

        Looks for a ``database_backend`` key in the configuration
        dictionary. The value must be an instance of :class:`DatabaseBackend`.

        :param config: Loaded configuration dictionary.

        :returns: The database backend instance or None if not configured.
    """
    backend = config.get("database_backend", None)

    if backend is not None and isinstance(backend, DatabaseBackend):
        return backend

    return None


def add_env_argument(parser: "ArgumentParser") -> None:
    """
        Add the ``--env`` argument to a command parser.

        :param parser: The argument parser to add the argument to.
    """
    parser.add_argument(
        "--env",
        type=str,
        default=None,
        help="Target environment (e.g., development, staging, production)."
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
        backend = resolve_backend(config)

        if backend is None:
            print("Error: No database backend configured.")
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
        backend = resolve_backend(config)

        if backend is None:
            print("Error: No database backend configured.")
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
        backend = resolve_backend(config)

        if backend is None:
            print("Error: No database backend configured.")
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
        backend = resolve_backend(config)

        if backend is None:
            print("Error: No database backend configured.")
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
        backend = resolve_backend(config)

        if backend is None:
            print("Error: No database backend configured.")
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
