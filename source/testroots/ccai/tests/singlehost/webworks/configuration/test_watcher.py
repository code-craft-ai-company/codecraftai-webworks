"""
    Tests for the configuration watcher module.
    
    This module contains unit tests for the ConfigWatcher class which monitors
    configuration files for changes and triggers reload callbacks.
"""

import os
import tempfile
import time
from pathlib import Path
from typing import List

from ccai.webworks.configuration import (
    ConfigRegistry,
    ConfigSchema,
    ConfigWatcher
)


# =============================================================================
# Unit Tests for ConfigWatcher Creation
# =============================================================================

def test_config_watcher_creation():
    """
        Test that ConfigWatcher can be created with a registry.
    """
    registry = ConfigRegistry()
    watcher = ConfigWatcher(registry)
    
    if watcher.registry is not registry:
        errmsg = "Expected watcher.registry to be the provided registry"
        raise AssertionError(errmsg)
    
    return


def test_config_watcher_default_poll_interval():
    """
        Test that ConfigWatcher has default poll interval of 1.0 seconds.
    """
    registry = ConfigRegistry()
    watcher = ConfigWatcher(registry)
    
    if watcher.poll_interval != 1.0:
        errmsg = f"Expected poll_interval 1.0, got {watcher.poll_interval}"
        raise AssertionError(errmsg)
    
    return


def test_config_watcher_custom_poll_interval():
    """
        Test that ConfigWatcher can be created with custom poll interval.
    """
    registry = ConfigRegistry()
    watcher = ConfigWatcher(registry, poll_interval=0.5)
    
    if watcher.poll_interval != 0.5:
        errmsg = f"Expected poll_interval 0.5, got {watcher.poll_interval}"
        raise AssertionError(errmsg)
    
    return


def test_config_watcher_poll_interval_setter():
    """
        Test that poll_interval can be changed after creation.
    """
    registry = ConfigRegistry()
    watcher = ConfigWatcher(registry)
    
    watcher.poll_interval = 2.0
    
    if watcher.poll_interval != 2.0:
        errmsg = f"Expected poll_interval 2.0, got {watcher.poll_interval}"
        raise AssertionError(errmsg)
    
    return


def test_config_watcher_poll_interval_setter_rejects_non_positive():
    """
        Test that poll_interval setter rejects non-positive values.
    """
    registry = ConfigRegistry()
    watcher = ConfigWatcher(registry)
    
    try:
        watcher.poll_interval = 0
        errmsg = "Expected ValueError for poll_interval = 0"
        raise AssertionError(errmsg)
    except ValueError:
        pass
    
    try:
        watcher.poll_interval = -1.0
        errmsg = "Expected ValueError for poll_interval = -1.0"
        raise AssertionError(errmsg)
    except ValueError:
        pass
    
    return


def test_config_watcher_initial_state_not_running():
    """
        Test that ConfigWatcher is not running initially.
    """
    registry = ConfigRegistry()
    watcher = ConfigWatcher(registry)
    
    if watcher.is_running:
        errmsg = "Expected is_running to be False initially"
        raise AssertionError(errmsg)
    
    return


def test_config_watcher_initial_watched_paths_empty():
    """
        Test that ConfigWatcher has no watched paths initially.
    """
    registry = ConfigRegistry()
    watcher = ConfigWatcher(registry)
    
    if len(watcher.watched_paths) != 0:
        errmsg = f"Expected 0 watched paths, got {len(watcher.watched_paths)}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for watch() Method
# =============================================================================

def test_config_watcher_watch_adds_path():
    """
        Test that watch() adds a path to the watched paths.
    """
    registry = ConfigRegistry()
    watcher = ConfigWatcher(registry)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".yaml") as f:
        temp_path = Path(f.name)
    
    try:
        watcher.watch(temp_path)
        
        watched = watcher.watched_paths
        if temp_path.resolve() not in watched:
            errmsg = f"Expected {temp_path.resolve()} in watched paths"
            raise AssertionError(errmsg)
    finally:
        temp_path.unlink()
    
    return


def test_config_watcher_watch_accepts_string_path():
    """
        Test that watch() accepts string paths.
    """
    registry = ConfigRegistry()
    watcher = ConfigWatcher(registry)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".yaml") as f:
        temp_path = f.name
    
    try:
        watcher.watch(temp_path)
        
        watched = watcher.watched_paths
        if Path(temp_path).resolve() not in watched:
            errmsg = f"Expected {Path(temp_path).resolve()} in watched paths"
            raise AssertionError(errmsg)
    finally:
        Path(temp_path).unlink()
    
    return


def test_config_watcher_watch_multiple_paths():
    """
        Test that watch() can add multiple paths.
    """
    registry = ConfigRegistry()
    watcher = ConfigWatcher(registry)
    
    temp_files = []
    try:
        for i in range(3):
            f = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{i}.yaml")
            temp_files.append(Path(f.name))
            f.close()
        
        for path in temp_files:
            watcher.watch(path)
        
        watched = watcher.watched_paths
        if len(watched) != 3:
            errmsg = f"Expected 3 watched paths, got {len(watched)}"
            raise AssertionError(errmsg)
        
        for path in temp_files:
            if path.resolve() not in watched:
                errmsg = f"Expected {path.resolve()} in watched paths"
                raise AssertionError(errmsg)
    finally:
        for path in temp_files:
            path.unlink()
    
    return


def test_config_watcher_watch_same_path_twice_no_duplicate():
    """
        Test that watching the same path twice doesn't create duplicates.
    """
    registry = ConfigRegistry()
    watcher = ConfigWatcher(registry)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".yaml") as f:
        temp_path = Path(f.name)
    
    try:
        watcher.watch(temp_path)
        watcher.watch(temp_path)
        
        watched = watcher.watched_paths
        if len(watched) != 1:
            errmsg = f"Expected 1 watched path, got {len(watched)}"
            raise AssertionError(errmsg)
    finally:
        temp_path.unlink()
    
    return


def test_config_watcher_watch_nonexistent_path():
    """
        Test that watch() can add a path that doesn't exist yet.
    """
    registry = ConfigRegistry()
    watcher = ConfigWatcher(registry)
    
    nonexistent_path = Path("/tmp/nonexistent_config_file_12345.yaml")
    
    # Ensure it doesn't exist
    if nonexistent_path.exists():
        nonexistent_path.unlink()
    
    watcher.watch(nonexistent_path)
    
    watched = watcher.watched_paths
    if nonexistent_path.resolve() not in watched:
        errmsg = f"Expected {nonexistent_path.resolve()} in watched paths"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for unwatch() Method
# =============================================================================

def test_config_watcher_unwatch_removes_path():
    """
        Test that unwatch() removes a path from watched paths.
    """
    registry = ConfigRegistry()
    watcher = ConfigWatcher(registry)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".yaml") as f:
        temp_path = Path(f.name)
    
    try:
        watcher.watch(temp_path)
        result = watcher.unwatch(temp_path)
        
        if not result:
            errmsg = "Expected unwatch() to return True"
            raise AssertionError(errmsg)
        
        watched = watcher.watched_paths
        if temp_path.resolve() in watched:
            errmsg = f"Expected {temp_path.resolve()} to be removed from watched paths"
            raise AssertionError(errmsg)
    finally:
        temp_path.unlink()
    
    return


def test_config_watcher_unwatch_nonexistent_returns_false():
    """
        Test that unwatch() returns False for paths not being watched.
    """
    registry = ConfigRegistry()
    watcher = ConfigWatcher(registry)
    
    result = watcher.unwatch(Path("/tmp/not_watched.yaml"))
    
    if result:
        errmsg = "Expected unwatch() to return False for non-watched path"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for clear() Method
# =============================================================================

def test_config_watcher_clear_removes_all_paths():
    """
        Test that clear() removes all watched paths.
    """
    registry = ConfigRegistry()
    watcher = ConfigWatcher(registry)
    
    temp_files = []
    try:
        for i in range(3):
            f = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{i}.yaml")
            temp_files.append(Path(f.name))
            f.close()
            watcher.watch(temp_files[-1])
        
        watcher.clear()
        
        watched = watcher.watched_paths
        if len(watched) != 0:
            errmsg = f"Expected 0 watched paths after clear(), got {len(watched)}"
            raise AssertionError(errmsg)
    finally:
        for path in temp_files:
            path.unlink()
    
    return


# =============================================================================
# Unit Tests for start() and stop() Methods
# =============================================================================

def test_config_watcher_start_sets_running():
    """
        Test that start() sets is_running to True.
    """
    registry = ConfigRegistry()
    watcher = ConfigWatcher(registry, poll_interval=0.1)
    
    try:
        watcher.start()
        
        if not watcher.is_running:
            errmsg = "Expected is_running to be True after start()"
            raise AssertionError(errmsg)
    finally:
        watcher.stop()
    
    return


def test_config_watcher_stop_clears_running():
    """
        Test that stop() sets is_running to False.
    """
    registry = ConfigRegistry()
    watcher = ConfigWatcher(registry, poll_interval=0.1)
    
    watcher.start()
    watcher.stop()
    
    if watcher.is_running:
        errmsg = "Expected is_running to be False after stop()"
        raise AssertionError(errmsg)
    
    return


def test_config_watcher_start_twice_is_safe():
    """
        Test that calling start() twice is safe.
    """
    registry = ConfigRegistry()
    watcher = ConfigWatcher(registry, poll_interval=0.1)
    
    try:
        watcher.start()
        watcher.start()  # Should not raise
        
        if not watcher.is_running:
            errmsg = "Expected is_running to be True"
            raise AssertionError(errmsg)
    finally:
        watcher.stop()
    
    return


def test_config_watcher_stop_twice_is_safe():
    """
        Test that calling stop() twice is safe.
    """
    registry = ConfigRegistry()
    watcher = ConfigWatcher(registry, poll_interval=0.1)
    
    watcher.start()
    watcher.stop()
    watcher.stop()  # Should not raise
    
    if watcher.is_running:
        errmsg = "Expected is_running to be False"
        raise AssertionError(errmsg)
    
    return


def test_config_watcher_stop_without_start_is_safe():
    """
        Test that calling stop() without start() is safe.
    """
    registry = ConfigRegistry()
    watcher = ConfigWatcher(registry, poll_interval=0.1)
    
    watcher.stop()  # Should not raise
    
    if watcher.is_running:
        errmsg = "Expected is_running to be False"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for Context Manager
# =============================================================================

def test_config_watcher_context_manager_starts_and_stops():
    """
        Test that ConfigWatcher works as a context manager.
    """
    registry = ConfigRegistry()
    watcher = ConfigWatcher(registry, poll_interval=0.1)
    
    with watcher:
        if not watcher.is_running:
            errmsg = "Expected is_running to be True inside context"
            raise AssertionError(errmsg)
    
    if watcher.is_running:
        errmsg = "Expected is_running to be False after context"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for File Change Detection
# =============================================================================

def test_config_watcher_detects_file_modification():
    """
        Test that ConfigWatcher detects file modifications.
    """
    registry = ConfigRegistry()
    
    changes_detected: List[Path] = []
    
    def on_change(path: Path):
        changes_detected.append(path)
    
    watcher = ConfigWatcher(registry, poll_interval=0.1, on_change=on_change)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".yaml", mode='w') as f:
        temp_path = Path(f.name)
        f.write("key: value1\n")
    
    try:
        watcher.watch(temp_path)
        watcher.start()
        
        # Wait for initial state to be recorded
        time.sleep(0.2)
        
        # Modify the file
        with open(temp_path, 'w') as f:
            f.write("key: value2\n")
        
        # Wait for change to be detected
        time.sleep(0.3)
        
        watcher.stop()
        
        # Check that change was detected
        resolved_path = temp_path.resolve()
        if resolved_path not in changes_detected:
            errmsg = f"Expected {resolved_path} in changes_detected, got {changes_detected}"
            raise AssertionError(errmsg)
    finally:
        temp_path.unlink()
    
    return


def test_config_watcher_check_now_returns_changed_paths():
    """
        Test that check_now() returns paths that have changed.
    """
    registry = ConfigRegistry()
    watcher = ConfigWatcher(registry, poll_interval=10.0)  # Long interval
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".yaml", mode='w') as f:
        temp_path = Path(f.name)
        f.write("key: value1\n")
    
    try:
        watcher.watch(temp_path)
        
        # Initial check to record mtime
        watcher.check_now()
        
        # Modify the file
        time.sleep(0.1)  # Ensure mtime changes
        with open(temp_path, 'w') as f:
            f.write("key: value2\n")
        
        # Check for changes
        changed = watcher.check_now()
        
        resolved_path = temp_path.resolve()
        if resolved_path not in changed:
            errmsg = f"Expected {resolved_path} in changed paths, got {changed}"
            raise AssertionError(errmsg)
    finally:
        temp_path.unlink()
    
    return


def test_config_watcher_check_now_returns_empty_when_no_changes():
    """
        Test that check_now() returns empty set when no changes.
    """
    registry = ConfigRegistry()
    watcher = ConfigWatcher(registry, poll_interval=10.0)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".yaml", mode='w') as f:
        temp_path = Path(f.name)
        f.write("key: value1\n")
    
    try:
        watcher.watch(temp_path)
        
        # Initial check to record mtime
        watcher.check_now()
        
        # Check again without modifying
        changed = watcher.check_now()
        
        if len(changed) != 0:
            errmsg = f"Expected empty changed set, got {changed}"
            raise AssertionError(errmsg)
    finally:
        temp_path.unlink()
    
    return


def test_config_watcher_detects_file_deletion():
    """
        Test that ConfigWatcher detects file deletion.
    """
    registry = ConfigRegistry()
    
    changes_detected: List[Path] = []
    
    def on_change(path: Path):
        changes_detected.append(path)
    
    watcher = ConfigWatcher(registry, poll_interval=0.1, on_change=on_change)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".yaml", mode='w') as f:
        temp_path = Path(f.name)
        f.write("key: value1\n")
    
    try:
        watcher.watch(temp_path)
        watcher.start()
        
        # Wait for initial state to be recorded
        time.sleep(0.2)
        
        # Delete the file
        resolved_path = temp_path.resolve()
        temp_path.unlink()
        
        # Wait for change to be detected
        time.sleep(0.3)
        
        watcher.stop()
        
        # Check that deletion was detected
        if resolved_path not in changes_detected:
            errmsg = f"Expected {resolved_path} in changes_detected for deletion"
            raise AssertionError(errmsg)
    except FileNotFoundError:
        # File already deleted, that's fine
        pass
    
    return


def test_config_watcher_detects_new_file_creation():
    """
        Test that ConfigWatcher detects when a watched path is created.
    """
    registry = ConfigRegistry()
    
    changes_detected: List[Path] = []
    
    def on_change(path: Path):
        changes_detected.append(path)
    
    watcher = ConfigWatcher(registry, poll_interval=0.1, on_change=on_change)
    
    # Create a path that doesn't exist yet
    temp_dir = tempfile.mkdtemp()
    temp_path = Path(temp_dir) / "new_config.yaml"
    
    try:
        # Watch the non-existent path
        watcher.watch(temp_path)
        watcher.start()
        
        # Wait a bit
        time.sleep(0.2)
        
        # Create the file
        with open(temp_path, 'w') as f:
            f.write("key: value\n")
        
        # Wait for change to be detected
        time.sleep(0.3)
        
        watcher.stop()
        
        # Check that creation was detected
        resolved_path = temp_path.resolve()
        if resolved_path not in changes_detected:
            errmsg = f"Expected {resolved_path} in changes_detected for creation"
            raise AssertionError(errmsg)
    finally:
        if temp_path.exists():
            temp_path.unlink()
        Path(temp_dir).rmdir()
    
    return


# =============================================================================
# Unit Tests for Custom Callback
# =============================================================================

def test_config_watcher_custom_callback_receives_path():
    """
        Test that custom callback receives the changed path.
    """
    registry = ConfigRegistry()
    
    received_paths: List[Path] = []
    
    def custom_callback(path: Path):
        received_paths.append(path)
    
    watcher = ConfigWatcher(registry, poll_interval=0.1, on_change=custom_callback)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".yaml", mode='w') as f:
        temp_path = Path(f.name)
        f.write("key: value1\n")
    
    try:
        watcher.watch(temp_path)
        watcher.start()
        
        # Wait for initial state
        time.sleep(0.2)
        
        # Modify file
        with open(temp_path, 'w') as f:
            f.write("key: value2\n")
        
        # Wait for detection
        time.sleep(0.3)
        
        watcher.stop()
        
        resolved_path = temp_path.resolve()
        if resolved_path not in received_paths:
            errmsg = f"Expected callback to receive {resolved_path}"
            raise AssertionError(errmsg)
    finally:
        temp_path.unlink()
    
    return


def test_config_watcher_callback_exception_does_not_stop_watcher():
    """
        Test that exceptions in callback don't stop the watcher.
    """
    registry = ConfigRegistry()
    
    call_count = [0]
    
    def failing_callback(path: Path):
        call_count[0] += 1
        raise RuntimeError("Callback error")
    
    watcher = ConfigWatcher(registry, poll_interval=0.1, on_change=failing_callback)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".yaml", mode='w') as f:
        temp_path = Path(f.name)
        f.write("key: value1\n")
    
    try:
        watcher.watch(temp_path)
        watcher.start()
        
        # Wait for initial state
        time.sleep(0.2)
        
        # Modify file multiple times
        for i in range(2):
            time.sleep(0.15)
            with open(temp_path, 'w') as f:
                f.write(f"key: value{i+2}\n")
        
        time.sleep(0.3)
        
        # Watcher should still be running despite callback errors
        if not watcher.is_running:
            errmsg = "Expected watcher to still be running after callback errors"
            raise AssertionError(errmsg)
        
        watcher.stop()
    finally:
        temp_path.unlink()
    
    return


# =============================================================================
# Unit Tests for Default Behavior (Registry Reload)
# =============================================================================

def test_config_watcher_default_behavior_reloads_registry():
    """
        Test that without custom callback, watcher reloads the registry.
    """
    schema = ConfigSchema()
    schema.define("key", str, default="default_value")
    
    registry = ConfigRegistry(schema=schema)
    
    watcher = ConfigWatcher(registry, poll_interval=0.1)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode='w') as f:
        temp_path = Path(f.name)
        f.write('{"key": "initial_value"}\n')
    
    try:
        # Import FileSource to register the file
        from ccai.webworks.configuration import FileSource
        
        file_source = FileSource(paths=[temp_path])
        registry.register_source(file_source)
        registry.load()
        
        # Verify initial value
        initial_value = registry.get("key")
        if initial_value != "initial_value":
            errmsg = f"Expected initial value 'initial_value', got {initial_value}"
            raise AssertionError(errmsg)
        
        watcher.watch(temp_path)
        watcher.start()
        
        # Wait for initial state
        time.sleep(0.2)
        
        # Modify file
        with open(temp_path, 'w') as f:
            f.write('{"key": "updated_value"}\n')
        
        # Wait for reload
        time.sleep(0.4)
        
        watcher.stop()
        
        # Check that registry was reloaded
        updated_value = registry.get("key")
        if updated_value != "updated_value":
            errmsg = f"Expected updated value 'updated_value', got {updated_value}"
            raise AssertionError(errmsg)
    finally:
        temp_path.unlink()
    
    return
