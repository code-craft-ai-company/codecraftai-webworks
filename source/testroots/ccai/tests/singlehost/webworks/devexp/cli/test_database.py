"""
    Tests for the CLI database commands.

    This module contains unit tests for the :class:`DatabaseGroup`,
    :class:`DbInitCommand`, :class:`DbMigrateCommand`,
    :class:`DbRollbackCommand`, :class:`DbSeedCommand`, and
    :class:`DbStatusCommand` classes, as well as the helper functions
    :func:`resolve_env`, :func:`resolve_backend`, and
    :func:`add_env_argument`.
"""

from argparse import ArgumentParser, Namespace
from typing import Any, Dict, List

from ccai.webworks.devexp.cli.database import DatabaseBackend
from ccai.webworks.devexp.cli.database import DatabaseGroup
from ccai.webworks.devexp.cli.database import DbInitCommand
from ccai.webworks.devexp.cli.database import DbMigrateCommand
from ccai.webworks.devexp.cli.database import DbRollbackCommand
from ccai.webworks.devexp.cli.database import DbSeedCommand
from ccai.webworks.devexp.cli.database import DbStatusCommand
from ccai.webworks.devexp.cli.database import add_env_argument
from ccai.webworks.devexp.cli.database import resolve_backend
from ccai.webworks.devexp.cli.database import resolve_env
from ccai.webworks.devexp.cli.exitcodes import EXIT_CONFIG_ERROR
from ccai.webworks.devexp.cli.exitcodes import EXIT_ERROR
from ccai.webworks.devexp.cli.exitcodes import EXIT_SUCCESS


# =============================================================================
# Test Helpers
# =============================================================================

class _TestBackend(DatabaseBackend):
    """
        A concrete database backend for testing.

        Records all calls made to its methods so tests can verify
        the correct operations were performed.
    """

    def __init__(self):
        self.calls = []
        self._pending = []
        self._applied = []
        self._status = {"applied": [], "pending": [], "current": None}
        self._fail_on = None
        self._rollback_fail = False
        return

    def initialize(self, env: str) -> None:
        self.calls.append(("initialize", env))
        if self._fail_on == "initialize":
            raise RuntimeError("Initialization failed")
        return

    def get_pending_migrations(self, env: str) -> List[str]:
        self.calls.append(("get_pending_migrations", env))
        if self._fail_on == "get_pending_migrations":
            raise RuntimeError("Failed to get pending migrations")
        return list(self._pending)

    def apply_migration(self, migration_name: str, env: str) -> None:
        self.calls.append(("apply_migration", migration_name, env))
        if self._fail_on == migration_name:
            raise RuntimeError("Migration '{}' failed".format(migration_name))
        return

    def rollback_migration(self, migration_name: str, env: str) -> None:
        self.calls.append(("rollback_migration", migration_name, env))
        if self._rollback_fail is True:
            raise RuntimeError("Rollback of '{}' failed".format(migration_name))
        return

    def get_applied_migrations(self, env: str) -> List[str]:
        self.calls.append(("get_applied_migrations", env))
        if self._fail_on == "get_applied_migrations":
            raise RuntimeError("Failed to get applied migrations")
        return list(self._applied)

    def seed(self, env: str) -> None:
        self.calls.append(("seed", env))
        if self._fail_on == "seed":
            raise RuntimeError("Seeding failed")
        return

    def get_status(self, env: str) -> Dict[str, Any]:
        self.calls.append(("get_status", env))
        if self._fail_on == "get_status":
            raise RuntimeError("Failed to get status")
        return dict(self._status)


def _make_args(**kwargs) -> Namespace:
    """
        Create a Namespace object with the given keyword arguments.

        :returns: A Namespace instance.
    """
    return Namespace(**kwargs)


def _make_config(backend=None, env=None) -> Dict[str, Any]:
    """
        Create a configuration dictionary for testing.

        :param backend: Optional database backend instance.
        :param env: Optional environment name.

        :returns: A configuration dictionary.
    """
    config = {}

    if backend is not None:
        config["database_backend"] = backend

    if env is not None:
        config["env"] = env

    return config


# =============================================================================
# Unit Tests for resolve_env
# =============================================================================

def test_resolve_env_from_args():
    """
        Test that resolve_env returns the env from args when provided.
    """
    args = _make_args(env="staging")
    config = {"env": "production"}

    result = resolve_env(args, config)

    if result != "staging":
        errmsg = "Expected 'staging', got '{}'.".format(result)
        raise AssertionError(errmsg)

    return


def test_resolve_env_from_config():
    """
        Test that resolve_env returns the env from config when args has no env.
    """
    args = _make_args(env=None)
    config = {"env": "production"}

    result = resolve_env(args, config)

    if result != "production":
        errmsg = "Expected 'production', got '{}'.".format(result)
        raise AssertionError(errmsg)

    return


def test_resolve_env_default():
    """
        Test that resolve_env returns 'development' when neither args nor config has env.
    """
    args = _make_args(env=None)
    config = {}

    result = resolve_env(args, config)

    if result != "development":
        errmsg = "Expected 'development', got '{}'.".format(result)
        raise AssertionError(errmsg)

    return


def test_resolve_env_args_takes_precedence():
    """
        Test that args env takes precedence over config env.
    """
    args = _make_args(env="test")
    config = {"env": "production"}

    result = resolve_env(args, config)

    if result != "test":
        errmsg = "Expected 'test', got '{}'.".format(result)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for resolve_backend
# =============================================================================

def test_resolve_backend_returns_backend():
    """
        Test that resolve_backend returns the backend when configured.
    """
    backend = _TestBackend()
    config = {"database_backend": backend}

    result = resolve_backend(config)

    if result is not backend:
        errmsg = "Expected the configured backend instance."
        raise AssertionError(errmsg)

    return


def test_resolve_backend_returns_none_when_missing():
    """
        Test that resolve_backend returns None when no backend is configured.
    """
    config = {}

    result = resolve_backend(config)

    if result is not None:
        errmsg = "Expected None when no backend configured, got '{}'.".format(type(result))
        raise AssertionError(errmsg)

    return


def test_resolve_backend_returns_none_for_non_backend():
    """
        Test that resolve_backend returns None when the value is not a DatabaseBackend.
    """
    config = {"database_backend": "not-a-backend"}

    result = resolve_backend(config)

    if result is not None:
        errmsg = "Expected None for non-DatabaseBackend value."
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for add_env_argument
# =============================================================================

def test_add_env_argument_registers_env():
    """
        Test that add_env_argument adds the --env argument to the parser.
    """
    parser = ArgumentParser()

    add_env_argument(parser)

    parsed = parser.parse_args(["--env", "staging"])

    if parsed.env != "staging":
        errmsg = "Expected env 'staging', got '{}'.".format(parsed.env)
        raise AssertionError(errmsg)

    return


def test_add_env_argument_defaults_to_none():
    """
        Test that the --env argument defaults to None.
    """
    parser = ArgumentParser()

    add_env_argument(parser)

    parsed = parser.parse_args([])

    if parsed.env is not None:
        errmsg = "Expected env default None, got '{}'.".format(parsed.env)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for DatabaseGroup
# =============================================================================

def test_database_group_name():
    """
        Test that DatabaseGroup has the correct name.
    """
    group = DatabaseGroup()

    if group.name != "db":
        errmsg = "Expected name 'db', got '{}'.".format(group.name)
        raise AssertionError(errmsg)

    return


def test_database_group_help():
    """
        Test that DatabaseGroup has help text.
    """
    group = DatabaseGroup()

    if len(group.help) == 0:
        errmsg = "Expected non-empty help text."
        raise AssertionError(errmsg)

    return


def test_database_group_has_five_commands():
    """
        Test that DatabaseGroup contains five commands.
    """
    group = DatabaseGroup()

    if len(group.commands) != 5:
        errmsg = "Expected 5 commands, got {}.".format(len(group.commands))
        raise AssertionError(errmsg)

    return


def test_database_group_command_names():
    """
        Test that DatabaseGroup contains the expected command names.
    """
    group = DatabaseGroup()
    command_names = [cmd.name for cmd in group.commands]
    expected_names = ["init", "migrate", "rollback", "seed", "status"]

    for expected in expected_names:
        if expected not in command_names:
            errmsg = "Expected command '{}' in group, got {}.".format(expected, command_names)
            raise AssertionError(errmsg)

    return


def test_database_group_register_commands():
    """
        Test that DatabaseGroup registers subparsers correctly.
    """
    group = DatabaseGroup()
    parser = ArgumentParser()

    group.register_commands(parser)

    parsed = parser.parse_args(["init"])

    if parsed.command != "init":
        errmsg = "Expected parsed command 'init', got '{}'.".format(parsed.command)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for DbInitCommand
# =============================================================================

def test_db_init_command_name():
    """
        Test that DbInitCommand has the correct name.
    """
    cmd = DbInitCommand()

    if cmd.name != "init":
        errmsg = "Expected name 'init', got '{}'.".format(cmd.name)
        raise AssertionError(errmsg)

    return


def test_db_init_command_help():
    """
        Test that DbInitCommand has help text.
    """
    cmd = DbInitCommand()

    if len(cmd.help) == 0:
        errmsg = "Expected non-empty help text."
        raise AssertionError(errmsg)

    return


def test_db_init_adds_env_argument():
    """
        Test that DbInitCommand adds the --env argument.
    """
    cmd = DbInitCommand()
    parser = ArgumentParser()

    cmd.add_arguments(parser)

    parsed = parser.parse_args(["--env", "staging"])

    if parsed.env != "staging":
        errmsg = "Expected env 'staging', got '{}'.".format(parsed.env)
        raise AssertionError(errmsg)

    return


def test_db_init_success():
    """
        Test that db init returns EXIT_SUCCESS on successful initialization.
    """
    backend = _TestBackend()
    args = _make_args(env="development")
    config = _make_config(backend=backend)

    cmd = DbInitCommand()
    exit_code = cmd.execute(args, config)

    if exit_code != EXIT_SUCCESS:
        errmsg = "Expected EXIT_SUCCESS, got {}.".format(exit_code)
        raise AssertionError(errmsg)

    return


def test_db_init_calls_backend_initialize():
    """
        Test that db init calls the backend's initialize method.
    """
    backend = _TestBackend()
    args = _make_args(env="staging")
    config = _make_config(backend=backend)

    cmd = DbInitCommand()
    cmd.execute(args, config)

    found = False
    for call in backend.calls:
        if call[0] == "initialize" and call[1] == "staging":
            found = True

    if found is not True:
        errmsg = "Expected backend.initialize to be called with 'staging'."
        raise AssertionError(errmsg)

    return


def test_db_init_no_backend_returns_config_error():
    """
        Test that db init returns EXIT_CONFIG_ERROR when no backend is configured.
    """
    args = _make_args(env="development")
    config = {}

    cmd = DbInitCommand()
    exit_code = cmd.execute(args, config)

    if exit_code != EXIT_CONFIG_ERROR:
        errmsg = "Expected EXIT_CONFIG_ERROR, got {}.".format(exit_code)
        raise AssertionError(errmsg)

    return


def test_db_init_failure_returns_error():
    """
        Test that db init returns EXIT_ERROR when initialization fails.
    """
    backend = _TestBackend()
    backend._fail_on = "initialize"
    args = _make_args(env="development")
    config = _make_config(backend=backend)

    cmd = DbInitCommand()
    exit_code = cmd.execute(args, config)

    if exit_code != EXIT_ERROR:
        errmsg = "Expected EXIT_ERROR, got {}.".format(exit_code)
        raise AssertionError(errmsg)

    return


def test_db_init_uses_env_from_args():
    """
        Test that db init uses the env from args.
    """
    backend = _TestBackend()
    args = _make_args(env="production")
    config = _make_config(backend=backend, env="staging")

    cmd = DbInitCommand()
    cmd.execute(args, config)

    found = False
    for call in backend.calls:
        if call[0] == "initialize" and call[1] == "production":
            found = True

    if found is not True:
        errmsg = "Expected backend.initialize to be called with 'production'."
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for DbMigrateCommand
# =============================================================================

def test_db_migrate_command_name():
    """
        Test that DbMigrateCommand has the correct name.
    """
    cmd = DbMigrateCommand()

    if cmd.name != "migrate":
        errmsg = "Expected name 'migrate', got '{}'.".format(cmd.name)
        raise AssertionError(errmsg)

    return


def test_db_migrate_command_help():
    """
        Test that DbMigrateCommand has help text.
    """
    cmd = DbMigrateCommand()

    if len(cmd.help) == 0:
        errmsg = "Expected non-empty help text."
        raise AssertionError(errmsg)

    return


def test_db_migrate_adds_env_argument():
    """
        Test that DbMigrateCommand adds the --env argument.
    """
    cmd = DbMigrateCommand()
    parser = ArgumentParser()

    cmd.add_arguments(parser)

    parsed = parser.parse_args(["--env", "staging"])

    if parsed.env != "staging":
        errmsg = "Expected env 'staging', got '{}'.".format(parsed.env)
        raise AssertionError(errmsg)

    return


def test_db_migrate_no_pending():
    """
        Test that db migrate returns EXIT_SUCCESS when no migrations are pending.
    """
    backend = _TestBackend()
    backend._pending = []
    args = _make_args(env="development")
    config = _make_config(backend=backend)

    cmd = DbMigrateCommand()
    exit_code = cmd.execute(args, config)

    if exit_code != EXIT_SUCCESS:
        errmsg = "Expected EXIT_SUCCESS, got {}.".format(exit_code)
        raise AssertionError(errmsg)

    return


def test_db_migrate_applies_pending():
    """
        Test that db migrate applies all pending migrations.
    """
    backend = _TestBackend()
    backend._pending = ["001_create_users", "002_create_posts"]
    args = _make_args(env="development")
    config = _make_config(backend=backend)

    cmd = DbMigrateCommand()
    exit_code = cmd.execute(args, config)

    if exit_code != EXIT_SUCCESS:
        errmsg = "Expected EXIT_SUCCESS, got {}.".format(exit_code)
        raise AssertionError(errmsg)

    apply_calls = [c for c in backend.calls if c[0] == "apply_migration"]

    if len(apply_calls) != 2:
        errmsg = "Expected 2 apply_migration calls, got {}.".format(len(apply_calls))
        raise AssertionError(errmsg)

    return


def test_db_migrate_no_backend_returns_config_error():
    """
        Test that db migrate returns EXIT_CONFIG_ERROR when no backend is configured.
    """
    args = _make_args(env="development")
    config = {}

    cmd = DbMigrateCommand()
    exit_code = cmd.execute(args, config)

    if exit_code != EXIT_CONFIG_ERROR:
        errmsg = "Expected EXIT_CONFIG_ERROR, got {}.".format(exit_code)
        raise AssertionError(errmsg)

    return


def test_db_migrate_failure_returns_error():
    """
        Test that db migrate returns EXIT_ERROR when a migration fails.
    """
    backend = _TestBackend()
    backend._pending = ["001_create_users", "002_create_posts"]
    backend._fail_on = "002_create_posts"
    args = _make_args(env="development")
    config = _make_config(backend=backend)

    cmd = DbMigrateCommand()
    exit_code = cmd.execute(args, config)

    if exit_code != EXIT_ERROR:
        errmsg = "Expected EXIT_ERROR, got {}.".format(exit_code)
        raise AssertionError(errmsg)

    return


def test_db_migrate_rollback_on_failure():
    """
        Test that db migrate attempts rollback when a migration fails.
    """
    backend = _TestBackend()
    backend._pending = ["001_create_users", "002_create_posts"]
    backend._fail_on = "002_create_posts"
    args = _make_args(env="development")
    config = _make_config(backend=backend)

    cmd = DbMigrateCommand()
    cmd.execute(args, config)

    rollback_calls = [c for c in backend.calls if c[0] == "rollback_migration"]

    if len(rollback_calls) != 1:
        errmsg = "Expected 1 rollback_migration call, got {}.".format(len(rollback_calls))
        raise AssertionError(errmsg)

    if rollback_calls[0][1] != "002_create_posts":
        errmsg = "Expected rollback of '002_create_posts', got '{}'.".format(rollback_calls[0][1])
        raise AssertionError(errmsg)

    return


def test_db_migrate_rollback_failure_still_returns_error():
    """
        Test that db migrate returns EXIT_ERROR even when rollback also fails.
    """
    backend = _TestBackend()
    backend._pending = ["001_create_users"]
    backend._fail_on = "001_create_users"
    backend._rollback_fail = True
    args = _make_args(env="development")
    config = _make_config(backend=backend)

    cmd = DbMigrateCommand()
    exit_code = cmd.execute(args, config)

    if exit_code != EXIT_ERROR:
        errmsg = "Expected EXIT_ERROR, got {}.".format(exit_code)
        raise AssertionError(errmsg)

    return


def test_db_migrate_get_pending_failure():
    """
        Test that db migrate returns EXIT_ERROR when getting pending migrations fails.
    """
    backend = _TestBackend()
    backend._fail_on = "get_pending_migrations"
    args = _make_args(env="development")
    config = _make_config(backend=backend)

    cmd = DbMigrateCommand()
    exit_code = cmd.execute(args, config)

    if exit_code != EXIT_ERROR:
        errmsg = "Expected EXIT_ERROR, got {}.".format(exit_code)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for DbRollbackCommand
# =============================================================================

def test_db_rollback_command_name():
    """
        Test that DbRollbackCommand has the correct name.
    """
    cmd = DbRollbackCommand()

    if cmd.name != "rollback":
        errmsg = "Expected name 'rollback', got '{}'.".format(cmd.name)
        raise AssertionError(errmsg)

    return


def test_db_rollback_command_help():
    """
        Test that DbRollbackCommand has help text.
    """
    cmd = DbRollbackCommand()

    if len(cmd.help) == 0:
        errmsg = "Expected non-empty help text."
        raise AssertionError(errmsg)

    return


def test_db_rollback_adds_env_argument():
    """
        Test that DbRollbackCommand adds the --env argument.
    """
    cmd = DbRollbackCommand()
    parser = ArgumentParser()

    cmd.add_arguments(parser)

    parsed = parser.parse_args(["--env", "staging"])

    if parsed.env != "staging":
        errmsg = "Expected env 'staging', got '{}'.".format(parsed.env)
        raise AssertionError(errmsg)

    return


def test_db_rollback_no_migrations():
    """
        Test that db rollback returns EXIT_SUCCESS when no migrations are applied.
    """
    backend = _TestBackend()
    backend._applied = []
    args = _make_args(env="development")
    config = _make_config(backend=backend)

    cmd = DbRollbackCommand()
    exit_code = cmd.execute(args, config)

    if exit_code != EXIT_SUCCESS:
        errmsg = "Expected EXIT_SUCCESS, got {}.".format(exit_code)
        raise AssertionError(errmsg)

    return


def test_db_rollback_reverts_last_migration():
    """
        Test that db rollback reverts the last applied migration.
    """
    backend = _TestBackend()
    backend._applied = ["001_create_users", "002_create_posts"]
    args = _make_args(env="development")
    config = _make_config(backend=backend)

    cmd = DbRollbackCommand()
    exit_code = cmd.execute(args, config)

    if exit_code != EXIT_SUCCESS:
        errmsg = "Expected EXIT_SUCCESS, got {}.".format(exit_code)
        raise AssertionError(errmsg)

    rollback_calls = [c for c in backend.calls if c[0] == "rollback_migration"]

    if len(rollback_calls) != 1:
        errmsg = "Expected 1 rollback_migration call, got {}.".format(len(rollback_calls))
        raise AssertionError(errmsg)

    if rollback_calls[0][1] != "002_create_posts":
        errmsg = "Expected rollback of '002_create_posts', got '{}'.".format(rollback_calls[0][1])
        raise AssertionError(errmsg)

    return


def test_db_rollback_no_backend_returns_config_error():
    """
        Test that db rollback returns EXIT_CONFIG_ERROR when no backend is configured.
    """
    args = _make_args(env="development")
    config = {}

    cmd = DbRollbackCommand()
    exit_code = cmd.execute(args, config)

    if exit_code != EXIT_CONFIG_ERROR:
        errmsg = "Expected EXIT_CONFIG_ERROR, got {}.".format(exit_code)
        raise AssertionError(errmsg)

    return


def test_db_rollback_failure_returns_error():
    """
        Test that db rollback returns EXIT_ERROR when rollback fails.
    """
    backend = _TestBackend()
    backend._applied = ["001_create_users"]
    backend._rollback_fail = True
    args = _make_args(env="development")
    config = _make_config(backend=backend)

    cmd = DbRollbackCommand()
    exit_code = cmd.execute(args, config)

    if exit_code != EXIT_ERROR:
        errmsg = "Expected EXIT_ERROR, got {}.".format(exit_code)
        raise AssertionError(errmsg)

    return


def test_db_rollback_get_applied_failure():
    """
        Test that db rollback returns EXIT_ERROR when getting applied migrations fails.
    """
    backend = _TestBackend()
    backend._fail_on = "get_applied_migrations"
    args = _make_args(env="development")
    config = _make_config(backend=backend)

    cmd = DbRollbackCommand()
    exit_code = cmd.execute(args, config)

    if exit_code != EXIT_ERROR:
        errmsg = "Expected EXIT_ERROR, got {}.".format(exit_code)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for DbSeedCommand
# =============================================================================

def test_db_seed_command_name():
    """
        Test that DbSeedCommand has the correct name.
    """
    cmd = DbSeedCommand()

    if cmd.name != "seed":
        errmsg = "Expected name 'seed', got '{}'.".format(cmd.name)
        raise AssertionError(errmsg)

    return


def test_db_seed_command_help():
    """
        Test that DbSeedCommand has help text.
    """
    cmd = DbSeedCommand()

    if len(cmd.help) == 0:
        errmsg = "Expected non-empty help text."
        raise AssertionError(errmsg)

    return


def test_db_seed_adds_env_argument():
    """
        Test that DbSeedCommand adds the --env argument.
    """
    cmd = DbSeedCommand()
    parser = ArgumentParser()

    cmd.add_arguments(parser)

    parsed = parser.parse_args(["--env", "staging"])

    if parsed.env != "staging":
        errmsg = "Expected env 'staging', got '{}'.".format(parsed.env)
        raise AssertionError(errmsg)

    return


def test_db_seed_success():
    """
        Test that db seed returns EXIT_SUCCESS on successful seeding.
    """
    backend = _TestBackend()
    args = _make_args(env="development")
    config = _make_config(backend=backend)

    cmd = DbSeedCommand()
    exit_code = cmd.execute(args, config)

    if exit_code != EXIT_SUCCESS:
        errmsg = "Expected EXIT_SUCCESS, got {}.".format(exit_code)
        raise AssertionError(errmsg)

    return


def test_db_seed_calls_backend_seed():
    """
        Test that db seed calls the backend's seed method.
    """
    backend = _TestBackend()
    args = _make_args(env="staging")
    config = _make_config(backend=backend)

    cmd = DbSeedCommand()
    cmd.execute(args, config)

    found = False
    for call in backend.calls:
        if call[0] == "seed" and call[1] == "staging":
            found = True

    if found is not True:
        errmsg = "Expected backend.seed to be called with 'staging'."
        raise AssertionError(errmsg)

    return


def test_db_seed_no_backend_returns_config_error():
    """
        Test that db seed returns EXIT_CONFIG_ERROR when no backend is configured.
    """
    args = _make_args(env="development")
    config = {}

    cmd = DbSeedCommand()
    exit_code = cmd.execute(args, config)

    if exit_code != EXIT_CONFIG_ERROR:
        errmsg = "Expected EXIT_CONFIG_ERROR, got {}.".format(exit_code)
        raise AssertionError(errmsg)

    return


def test_db_seed_failure_returns_error():
    """
        Test that db seed returns EXIT_ERROR when seeding fails.
    """
    backend = _TestBackend()
    backend._fail_on = "seed"
    args = _make_args(env="development")
    config = _make_config(backend=backend)

    cmd = DbSeedCommand()
    exit_code = cmd.execute(args, config)

    if exit_code != EXIT_ERROR:
        errmsg = "Expected EXIT_ERROR, got {}.".format(exit_code)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for DbStatusCommand
# =============================================================================

def test_db_status_command_name():
    """
        Test that DbStatusCommand has the correct name.
    """
    cmd = DbStatusCommand()

    if cmd.name != "status":
        errmsg = "Expected name 'status', got '{}'.".format(cmd.name)
        raise AssertionError(errmsg)

    return


def test_db_status_command_help():
    """
        Test that DbStatusCommand has help text.
    """
    cmd = DbStatusCommand()

    if len(cmd.help) == 0:
        errmsg = "Expected non-empty help text."
        raise AssertionError(errmsg)

    return


def test_db_status_adds_env_argument():
    """
        Test that DbStatusCommand adds the --env argument.
    """
    cmd = DbStatusCommand()
    parser = ArgumentParser()

    cmd.add_arguments(parser)

    parsed = parser.parse_args(["--env", "staging"])

    if parsed.env != "staging":
        errmsg = "Expected env 'staging', got '{}'.".format(parsed.env)
        raise AssertionError(errmsg)

    return


def test_db_status_success():
    """
        Test that db status returns EXIT_SUCCESS on success.
    """
    backend = _TestBackend()
    backend._status = {
        "applied": ["001_create_users"],
        "pending": ["002_create_posts"],
        "current": "001_create_users",
    }
    args = _make_args(env="development")
    config = _make_config(backend=backend)

    cmd = DbStatusCommand()
    exit_code = cmd.execute(args, config)

    if exit_code != EXIT_SUCCESS:
        errmsg = "Expected EXIT_SUCCESS, got {}.".format(exit_code)
        raise AssertionError(errmsg)

    return


def test_db_status_calls_backend_get_status():
    """
        Test that db status calls the backend's get_status method.
    """
    backend = _TestBackend()
    args = _make_args(env="staging")
    config = _make_config(backend=backend)

    cmd = DbStatusCommand()
    cmd.execute(args, config)

    found = False
    for call in backend.calls:
        if call[0] == "get_status" and call[1] == "staging":
            found = True

    if found is not True:
        errmsg = "Expected backend.get_status to be called with 'staging'."
        raise AssertionError(errmsg)

    return


def test_db_status_no_backend_returns_config_error():
    """
        Test that db status returns EXIT_CONFIG_ERROR when no backend is configured.
    """
    args = _make_args(env="development")
    config = {}

    cmd = DbStatusCommand()
    exit_code = cmd.execute(args, config)

    if exit_code != EXIT_CONFIG_ERROR:
        errmsg = "Expected EXIT_CONFIG_ERROR, got {}.".format(exit_code)
        raise AssertionError(errmsg)

    return


def test_db_status_failure_returns_error():
    """
        Test that db status returns EXIT_ERROR when getting status fails.
    """
    backend = _TestBackend()
    backend._fail_on = "get_status"
    args = _make_args(env="development")
    config = _make_config(backend=backend)

    cmd = DbStatusCommand()
    exit_code = cmd.execute(args, config)

    if exit_code != EXIT_ERROR:
        errmsg = "Expected EXIT_ERROR, got {}.".format(exit_code)
        raise AssertionError(errmsg)

    return


def test_db_status_empty_status():
    """
        Test that db status handles empty status correctly.
    """
    backend = _TestBackend()
    backend._status = {"applied": [], "pending": [], "current": None}
    args = _make_args(env="development")
    config = _make_config(backend=backend)

    cmd = DbStatusCommand()
    exit_code = cmd.execute(args, config)

    if exit_code != EXIT_SUCCESS:
        errmsg = "Expected EXIT_SUCCESS, got {}.".format(exit_code)
        raise AssertionError(errmsg)

    return
