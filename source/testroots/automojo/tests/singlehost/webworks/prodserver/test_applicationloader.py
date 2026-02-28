"""
    Tests for the ApplicationLoader class.

    This module contains unit tests for the production server ApplicationLoader
    class including application preloading, factory support, lifecycle hooks,
    and application load error handling.
"""

from automojo.testbase.mocking import Mock
from automojo.webworks.prodserver.applicationloader import (
    ApplicationLoader,
    ApplicationLoadError,
)
from automojo.webworks.prodserver.serverconfig import ServerConfig, EXIT_APP_LOAD_ERROR


def _create_config(**overrides):
    """
        Create a ServerConfig with optional overrides.

        :returns: A ServerConfig instance.
    """
    config = ServerConfig(**overrides)
    return config


def _create_mock_app():
    """
        Create a mock application object.

        :returns: A Mock application instance.
    """
    mock_app = Mock()
    mock_app.configure(recursive=True)
    return mock_app


# =============================================================================
# Unit Tests for ApplicationLoader Initialization
# =============================================================================

def test_application_loader_initial_app_is_none():
    """
        Test that a new ApplicationLoader has no app loaded.
    """
    config = _create_config()
    loader = ApplicationLoader(config)

    if loader.app is not None:
        errmsg = "Expected loader.app to be None initially"
        raise AssertionError(errmsg)

    return


def test_application_loader_initial_preloaded_is_false():
    """
        Test that a new ApplicationLoader has preloaded set to False.
    """
    config = _create_config()
    loader = ApplicationLoader(config)

    if loader.preloaded is not False:
        errmsg = "Expected loader.preloaded to be False initially"
        raise AssertionError(errmsg)

    return


def test_application_loader_initial_factory_is_none():
    """
        Test that a new ApplicationLoader has no factory set.
    """
    config = _create_config()
    loader = ApplicationLoader(config)

    if loader.factory is not None:
        errmsg = "Expected loader.factory to be None initially"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for set_app and set_factory
# =============================================================================

def test_set_app_stores_application():
    """
        Test that set_app stores the application instance.
    """
    config = _create_config()
    loader = ApplicationLoader(config)
    mock_app = _create_mock_app()

    loader.set_app(mock_app)

    if loader.app is not mock_app:
        errmsg = "Expected loader.app to be the provided mock app"
        raise AssertionError(errmsg)

    return


def test_set_factory_stores_factory_callable():
    """
        Test that set_factory stores the factory callable.
    """
    config = _create_config()
    loader = ApplicationLoader(config)

    def my_factory():
        return _create_mock_app()

    loader.set_factory(my_factory)

    if loader.factory is not my_factory:
        errmsg = "Expected loader.factory to be the provided factory callable"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for load_app
# =============================================================================

def test_load_app_with_direct_app():
    """
        Test that load_app accepts a directly provided application.
    """
    config = _create_config()
    loader = ApplicationLoader(config)
    mock_app = _create_mock_app()

    result = loader.load_app(app=mock_app)

    if result is not mock_app:
        errmsg = "Expected load_app to return the provided app"
        raise AssertionError(errmsg)

    if loader.app is not mock_app:
        errmsg = "Expected loader.app to be set after load_app"
        raise AssertionError(errmsg)

    return


def test_load_app_with_factory():
    """
        Test that load_app uses the factory when set.

        Validates: Requirements 12.3
    """
    config = _create_config()
    loader = ApplicationLoader(config)
    mock_app = _create_mock_app()

    loader.set_factory(lambda: mock_app)

    result = loader.load_app()

    if result is not mock_app:
        errmsg = "Expected load_app to return the factory-created app"
        raise AssertionError(errmsg)

    return


def test_load_app_with_previously_set_app():
    """
        Test that load_app returns a previously set app when no
        direct app or factory is provided.
    """
    config = _create_config()
    loader = ApplicationLoader(config)
    mock_app = _create_mock_app()

    loader.set_app(mock_app)
    result = loader.load_app()

    if result is not mock_app:
        errmsg = "Expected load_app to return the previously set app"
        raise AssertionError(errmsg)

    return


def test_load_app_raises_when_no_app_or_factory():
    """
        Test that load_app raises ApplicationLoadError when no app
        or factory is available.

        Validates: Requirements 12.8
    """
    config = _create_config()
    loader = ApplicationLoader(config)

    raised = False
    try:
        loader.load_app()
    except ApplicationLoadError:
        raised = True

    if not raised:
        errmsg = "Expected ApplicationLoadError when no app or factory is provided"
        raise AssertionError(errmsg)

    return


def test_load_app_factory_raises_wraps_in_application_load_error():
    """
        Test that when the factory raises an exception, it is wrapped
        in an ApplicationLoadError.

        Validates: Requirements 12.8
    """
    config = _create_config()
    loader = ApplicationLoader(config)

    def bad_factory():
        raise RuntimeError("Factory failed")

    loader.set_factory(bad_factory)

    raised = False
    original_error = None
    try:
        loader.load_app()
    except ApplicationLoadError as ex:
        raised = True
        original_error = ex.original_error

    if not raised:
        errmsg = "Expected ApplicationLoadError when factory raises"
        raise AssertionError(errmsg)

    if not isinstance(original_error, RuntimeError):
        errmsg = "Expected original_error to be the RuntimeError from the factory"
        raise AssertionError(errmsg)

    return


def test_load_app_factory_takes_priority_over_direct_app():
    """
        Test that the factory is used even when a direct app is provided.
    """
    config = _create_config()
    loader = ApplicationLoader(config)
    direct_app = _create_mock_app()
    factory_app = _create_mock_app()

    loader.set_factory(lambda: factory_app)

    result = loader.load_app(app=direct_app)

    if result is not factory_app:
        errmsg = "Expected factory to take priority over direct app"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Preloading
# =============================================================================

def test_preload_loads_app_when_enabled():
    """
        Test that preload loads the application when preload is enabled.

        Validates: Requirements 12.1, 12.2
    """
    config = _create_config(preload=True)
    loader = ApplicationLoader(config)
    mock_app = _create_mock_app()

    result = loader.preload(app=mock_app)

    if result is not mock_app:
        errmsg = "Expected preload to return the loaded app"
        raise AssertionError(errmsg)

    if loader.preloaded is not True:
        errmsg = "Expected loader.preloaded to be True after preload"
        raise AssertionError(errmsg)

    return


def test_preload_skips_when_disabled():
    """
        Test that preload skips loading when preload is disabled.

        Validates: Requirements 12.1
    """
    config = _create_config(preload=False)
    loader = ApplicationLoader(config)
    mock_app = _create_mock_app()

    loader.preload(app=mock_app)

    if loader.preloaded is not False:
        errmsg = "Expected loader.preloaded to be False when preload is disabled"
        raise AssertionError(errmsg)

    return


def test_preload_stores_app_even_when_disabled():
    """
        Test that preload stores the app reference even when preload
        is disabled, so it can be used later.
    """
    config = _create_config(preload=False)
    loader = ApplicationLoader(config)
    mock_app = _create_mock_app()

    loader.preload(app=mock_app)

    if loader.app is not mock_app:
        errmsg = "Expected loader.app to be set even when preload is disabled"
        raise AssertionError(errmsg)

    return


def test_preload_with_factory():
    """
        Test that preload uses the factory when set and preload is enabled.

        Validates: Requirements 12.1, 12.3
    """
    config = _create_config(preload=True)
    loader = ApplicationLoader(config)
    mock_app = _create_mock_app()

    loader.set_factory(lambda: mock_app)

    result = loader.preload()

    if result is not mock_app:
        errmsg = "Expected preload to return the factory-created app"
        raise AssertionError(errmsg)

    if loader.preloaded is not True:
        errmsg = "Expected loader.preloaded to be True"
        raise AssertionError(errmsg)

    return


def test_preload_raises_on_load_failure():
    """
        Test that preload raises ApplicationLoadError when loading fails.

        Validates: Requirements 12.8
    """
    config = _create_config(preload=True)
    loader = ApplicationLoader(config)

    loader.set_factory(lambda: (_ for _ in ()).throw(RuntimeError("boom")))

    raised = False
    try:
        loader.preload()
    except ApplicationLoadError:
        raised = True

    if not raised:
        errmsg = "Expected ApplicationLoadError when preload fails"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for get_app_for_worker
# =============================================================================

def test_get_app_for_worker_returns_preloaded_app():
    """
        Test that get_app_for_worker returns the preloaded app.

        Validates: Requirements 12.2
    """
    config = _create_config(preload=True)
    loader = ApplicationLoader(config)
    mock_app = _create_mock_app()

    loader.preload(app=mock_app)

    result = loader.get_app_for_worker()

    if result is not mock_app:
        errmsg = "Expected get_app_for_worker to return the preloaded app"
        raise AssertionError(errmsg)

    return


def test_get_app_for_worker_creates_new_app_via_factory_when_not_preloaded():
    """
        Test that get_app_for_worker creates a new app via factory
        when preloading is not enabled.

        Validates: Requirements 12.3
    """
    config = _create_config(preload=False)
    loader = ApplicationLoader(config)

    call_count = [0]

    def counting_factory():
        call_count[0] += 1
        return _create_mock_app()

    loader.set_factory(counting_factory)

    loader.get_app_for_worker()
    loader.get_app_for_worker()

    if call_count[0] != 2:
        errmsg = f"Expected factory to be called twice, got {call_count[0]}"
        raise AssertionError(errmsg)

    return


def test_get_app_for_worker_returns_stored_app_when_no_factory():
    """
        Test that get_app_for_worker returns the stored app when
        no factory is set and app is not preloaded.
    """
    config = _create_config(preload=False)
    loader = ApplicationLoader(config)
    mock_app = _create_mock_app()

    loader.set_app(mock_app)

    result = loader.get_app_for_worker()

    if result is not mock_app:
        errmsg = "Expected get_app_for_worker to return the stored app"
        raise AssertionError(errmsg)

    return


def test_get_app_for_worker_raises_when_no_app_available():
    """
        Test that get_app_for_worker raises ApplicationLoadError
        when no app is available.

        Validates: Requirements 12.8
    """
    config = _create_config()
    loader = ApplicationLoader(config)

    raised = False
    try:
        loader.get_app_for_worker()
    except ApplicationLoadError:
        raised = True

    if not raised:
        errmsg = "Expected ApplicationLoadError when no app is available"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Lifecycle Hooks
# =============================================================================

def test_call_on_starting_invokes_hook():
    """
        Test that call_on_starting invokes the on_starting hook.

        Validates: Requirements 12.4
    """
    call_log = []

    def on_starting_hook(config):
        call_log.append(("on_starting", config))

    config = _create_config(on_starting=on_starting_hook)
    loader = ApplicationLoader(config)

    loader.call_on_starting()

    if len(call_log) != 1:
        errmsg = f"Expected on_starting to be called once, got {len(call_log)}"
        raise AssertionError(errmsg)

    if call_log[0][0] != "on_starting":
        errmsg = "Expected on_starting hook to be called"
        raise AssertionError(errmsg)

    if call_log[0][1] is not config:
        errmsg = "Expected on_starting hook to receive the config"
        raise AssertionError(errmsg)

    return


def test_call_on_starting_does_nothing_when_no_hook():
    """
        Test that call_on_starting does nothing when no hook is set.
    """
    config = _create_config()
    loader = ApplicationLoader(config)

    # Should not raise
    loader.call_on_starting()

    return


def test_call_on_starting_logs_but_does_not_raise_on_hook_error():
    """
        Test that call_on_starting catches exceptions from the hook.

        Validates: Requirements 12.4
    """
    def bad_hook(config):
        raise RuntimeError("hook failed")

    config = _create_config(on_starting=bad_hook)
    loader = ApplicationLoader(config)

    # Should not raise
    loader.call_on_starting()

    return


def test_call_on_reload_invokes_hook():
    """
        Test that call_on_reload invokes the on_reload hook.

        Validates: Requirements 12.5
    """
    call_log = []

    def on_reload_hook(config):
        call_log.append(("on_reload", config))

    config = _create_config(on_reload=on_reload_hook)
    loader = ApplicationLoader(config)

    loader.call_on_reload()

    if len(call_log) != 1:
        errmsg = f"Expected on_reload to be called once, got {len(call_log)}"
        raise AssertionError(errmsg)

    return


def test_call_on_reload_does_nothing_when_no_hook():
    """
        Test that call_on_reload does nothing when no hook is set.
    """
    config = _create_config()
    loader = ApplicationLoader(config)

    loader.call_on_reload()

    return


def test_call_on_reload_catches_hook_errors():
    """
        Test that call_on_reload catches exceptions from the hook.

        Validates: Requirements 12.5
    """
    def bad_hook(config):
        raise RuntimeError("reload hook failed")

    config = _create_config(on_reload=bad_hook)
    loader = ApplicationLoader(config)

    loader.call_on_reload()

    return


def test_call_when_ready_invokes_hook():
    """
        Test that call_when_ready invokes the when_ready hook.

        Validates: Requirements 12.6
    """
    call_log = []

    def when_ready_hook(config):
        call_log.append(("when_ready", config))

    config = _create_config(when_ready=when_ready_hook)
    loader = ApplicationLoader(config)

    loader.call_when_ready()

    if len(call_log) != 1:
        errmsg = f"Expected when_ready to be called once, got {len(call_log)}"
        raise AssertionError(errmsg)

    return


def test_call_when_ready_does_nothing_when_no_hook():
    """
        Test that call_when_ready does nothing when no hook is set.
    """
    config = _create_config()
    loader = ApplicationLoader(config)

    loader.call_when_ready()

    return


def test_call_when_ready_catches_hook_errors():
    """
        Test that call_when_ready catches exceptions from the hook.

        Validates: Requirements 12.6
    """
    def bad_hook(config):
        raise RuntimeError("ready hook failed")

    config = _create_config(when_ready=bad_hook)
    loader = ApplicationLoader(config)

    loader.call_when_ready()

    return


def test_call_on_exit_invokes_hook():
    """
        Test that call_on_exit invokes the on_exit hook.

        Validates: Requirements 12.7
    """
    call_log = []

    def on_exit_hook(config):
        call_log.append(("on_exit", config))

    config = _create_config(on_exit=on_exit_hook)
    loader = ApplicationLoader(config)

    loader.call_on_exit()

    if len(call_log) != 1:
        errmsg = f"Expected on_exit to be called once, got {len(call_log)}"
        raise AssertionError(errmsg)

    return


def test_call_on_exit_does_nothing_when_no_hook():
    """
        Test that call_on_exit does nothing when no hook is set.
    """
    config = _create_config()
    loader = ApplicationLoader(config)

    loader.call_on_exit()

    return


def test_call_on_exit_catches_hook_errors():
    """
        Test that call_on_exit catches exceptions from the hook.

        Validates: Requirements 12.7
    """
    def bad_hook(config):
        raise RuntimeError("exit hook failed")

    config = _create_config(on_exit=bad_hook)
    loader = ApplicationLoader(config)

    loader.call_on_exit()

    return


# =============================================================================
# Unit Tests for update_hook
# =============================================================================

def test_update_hook_replaces_existing_hook():
    """
        Test that update_hook replaces an existing hook.
    """
    call_log = []

    def original_hook(config):
        call_log.append("original")

    def replacement_hook(config):
        call_log.append("replacement")

    config = _create_config(on_starting=original_hook)
    loader = ApplicationLoader(config)

    loader.update_hook("on_starting", replacement_hook)
    loader.call_on_starting()

    if len(call_log) != 1:
        errmsg = f"Expected one call, got {len(call_log)}"
        raise AssertionError(errmsg)

    if call_log[0] != "replacement":
        errmsg = "Expected the replacement hook to be called"
        raise AssertionError(errmsg)

    return


def test_update_hook_removes_hook_with_none():
    """
        Test that update_hook removes a hook when None is provided.
    """
    call_log = []

    def my_hook(config):
        call_log.append("called")

    config = _create_config(on_starting=my_hook)
    loader = ApplicationLoader(config)

    loader.update_hook("on_starting", None)
    loader.call_on_starting()

    if len(call_log) != 0:
        errmsg = "Expected no calls after removing the hook"
        raise AssertionError(errmsg)

    return


def test_update_hook_raises_for_invalid_hook_name():
    """
        Test that update_hook raises ValueError for an invalid hook name.
    """
    config = _create_config()
    loader = ApplicationLoader(config)

    raised = False
    try:
        loader.update_hook("invalid_hook", lambda c: None)
    except ValueError:
        raised = True

    if not raised:
        errmsg = "Expected ValueError for invalid hook name"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Error Handling
# =============================================================================

def test_application_load_error_stores_original_error():
    """
        Test that ApplicationLoadError stores the original exception.
    """
    original = RuntimeError("original error")
    error = ApplicationLoadError("load failed", original_error=original)

    if error.original_error is not original:
        errmsg = "Expected original_error to be the provided RuntimeError"
        raise AssertionError(errmsg)

    return


def test_application_load_error_original_error_is_none_by_default():
    """
        Test that ApplicationLoadError has None original_error by default.
    """
    error = ApplicationLoadError("load failed")

    if error.original_error is not None:
        errmsg = "Expected original_error to be None by default"
        raise AssertionError(errmsg)

    return


def test_get_exit_code_for_load_error():
    """
        Test that get_exit_code_for_load_error returns EXIT_APP_LOAD_ERROR.

        Validates: Requirements 12.8
    """
    config = _create_config()
    loader = ApplicationLoader(config)

    exit_code = loader.get_exit_code_for_load_error()

    if exit_code != EXIT_APP_LOAD_ERROR:
        errmsg = f"Expected exit code {EXIT_APP_LOAD_ERROR}, got {exit_code}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Preloaded App Sharing Across Workers
# =============================================================================

def test_preloaded_app_is_same_instance_for_all_workers():
    """
        Test that when preloaded, all workers get the same app instance.

        Validates: Requirements 12.2
    """
    config = _create_config(preload=True)
    loader = ApplicationLoader(config)
    mock_app = _create_mock_app()

    loader.preload(app=mock_app)

    worker1_app = loader.get_app_for_worker()
    worker2_app = loader.get_app_for_worker()
    worker3_app = loader.get_app_for_worker()

    if worker1_app is not mock_app:
        errmsg = "Expected worker 1 to get the preloaded app"
        raise AssertionError(errmsg)

    if worker2_app is not mock_app:
        errmsg = "Expected worker 2 to get the preloaded app"
        raise AssertionError(errmsg)

    if worker3_app is not mock_app:
        errmsg = "Expected worker 3 to get the preloaded app"
        raise AssertionError(errmsg)

    return
