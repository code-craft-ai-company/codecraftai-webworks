"""
.. module:: watcher
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Configuration file watcher for monitoring changes and triggering reloads.

.. moduleauthor:: Code Craft AI LLC

This module contains the ConfigWatcher class which monitors configuration files
for changes and triggers reload callbacks when modifications are detected.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


import logging
import os
import threading
import time

from pathlib import Path
from typing import Callable, Dict, Optional, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from ccai.webworks.configuration.registry import ConfigRegistry


# Module-level logger. The watcher swallows OSError/Exception so a
# transient filesystem hiccup doesn't kill the background thread —
# breadcrumbs in the journal let the operator see whether config
# reloads are silently being skipped.
logger = logging.getLogger(__name__)


class ConfigWatcher:
    """
        Monitors configuration files for changes and triggers reloads.
        
        The ConfigWatcher provides file system monitoring capabilities for
        configuration files. When a watched file is modified, the watcher
        triggers a reload callback to update the configuration.
        
        The watcher uses a polling-based approach for cross-platform compatibility.
        It periodically checks the modification times of watched files and
        triggers callbacks when changes are detected.
        
        Example usage::
        
            from ccai.webworks.configuration import ConfigRegistry, ConfigWatcher
            from pathlib import Path
            
            # Create registry
            registry = ConfigRegistry()
            
            # Create watcher
            watcher = ConfigWatcher(registry)
            
            # Add paths to watch
            watcher.watch(Path("config.yaml"))
            watcher.watch(Path("secrets.yaml"))
            
            # Start watching
            watcher.start()
            
            # ... application runs ...
            
            # Stop watching on shutdown
            watcher.stop()
        
        :param registry: The ConfigRegistry to notify on configuration changes.
        :param poll_interval: Interval in seconds between file checks (default: 1.0).
        :param on_change: Optional callback to invoke when files change.
                         If not provided, registry.load() is called.
    """
    
    # Default polling interval in seconds
    DEFAULT_POLL_INTERVAL = 1.0
    
    def __init__(
        self,
        registry: 'ConfigRegistry',
        poll_interval: float = DEFAULT_POLL_INTERVAL,
        on_change: Optional[Callable[[Path], None]] = None
    ):
        """
            Initialize the ConfigWatcher.
            
            :param registry: The ConfigRegistry to notify on changes.
            :param poll_interval: Interval in seconds between file checks.
            :param on_change: Optional callback to invoke when files change.
                             Receives the path of the changed file.
        """
        self._registry = registry
        self._poll_interval = poll_interval
        self._on_change = on_change
        self._watched_paths: Set[Path] = set()
        self._file_mtimes: Dict[Path, float] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
    
    @property
    def registry(self) -> 'ConfigRegistry':
        """
            Get the associated ConfigRegistry.
            
            :returns: The ConfigRegistry instance.
        """
        return self._registry
    
    @property
    def poll_interval(self) -> float:
        """
            Get the polling interval.
            
            :returns: The polling interval in seconds.
        """
        return self._poll_interval
    
    @poll_interval.setter
    def poll_interval(self, value: float) -> None:
        """
            Set the polling interval.
            
            :param value: The new polling interval in seconds.
            
            :raises ValueError: If value is not positive.
        """
        if value <= 0:
            raise ValueError("Poll interval must be positive")
        self._poll_interval = value
    
    @property
    def watched_paths(self) -> Set[Path]:
        """
            Get the set of watched paths.
            
            :returns: A copy of the set of watched Path objects.
        """
        with self._lock:
            return set(self._watched_paths)
    
    @property
    def is_running(self) -> bool:
        """
            Check if the watcher is currently running.
            
            :returns: True if running, False otherwise.
        """
        return self._running
    
    def watch(self, path: Path) -> None:
        """
            Add a path to watch for changes.
            
            The path can be a file or directory. If the path is a directory,
            all files within it will be monitored for changes.
            
            If the path does not exist, it will still be added to the watch
            list and will be monitored once it is created.
            
            :param path: The file or directory path to watch.
        """
        # Ensure path is a Path object
        if isinstance(path, str):
            path = Path(path)
        
        # Resolve to absolute path
        path = path.resolve()
        
        with self._lock:
            if path not in self._watched_paths:
                self._watched_paths.add(path)
                # Initialize mtime if file exists
                if path.exists() and path.is_file():
                    try:
                        self._file_mtimes[path] = path.stat().st_mtime
                    except OSError:
                        # File may have been deleted between check and stat
                        pass
    
    def unwatch(self, path: Path) -> bool:
        """
            Remove a path from the watch list.
            
            :param path: The path to stop watching.
            
            :returns: True if the path was being watched and was removed,
                     False if the path was not in the watch list.
        """
        # Ensure path is a Path object
        if isinstance(path, str):
            path = Path(path)
        
        # Resolve to absolute path
        path = path.resolve()
        
        with self._lock:
            if path in self._watched_paths:
                self._watched_paths.discard(path)
                self._file_mtimes.pop(path, None)
                return True
            return False
    
    def clear(self) -> None:
        """
            Remove all paths from the watch list.
        """
        with self._lock:
            self._watched_paths.clear()
            self._file_mtimes.clear()
    
    def start(self) -> None:
        """
            Start watching for file changes.
            
            This method starts a background thread that periodically checks
            the watched files for modifications. When a change is detected,
            the configured callback is invoked.
            
            If the watcher is already running, this method does nothing.
        """
        if self._running:
            return
        
        self._running = True
        self._stop_event.clear()
        
        # Initialize mtimes for all watched paths
        with self._lock:
            for path in self._watched_paths:
                if path.exists() and path.is_file():
                    try:
                        self._file_mtimes[path] = path.stat().st_mtime
                    except OSError:
                        pass
        
        # Start the watcher thread
        self._thread = threading.Thread(
            target=self._watch_loop,
            name="ConfigWatcher",
            daemon=True
        )
        self._thread.start()
    
    def stop(self) -> None:
        """
            Stop watching for file changes.
            
            This method signals the watcher thread to stop and waits for
            it to terminate. After calling stop(), the watcher can be
            restarted by calling start() again.
        """
        if not self._running:
            return
        
        self._running = False
        self._stop_event.set()
        
        if self._thread is not None:
            self._thread.join(timeout=self._poll_interval * 2)
            self._thread = None
    
    def _watch_loop(self) -> None:
        """
            Main loop for the watcher thread.
            
            This method runs in a background thread and periodically checks
            all watched files for modifications.
        """
        while not self._stop_event.is_set():
            try:
                self._check_for_changes()
            except Exception:
                # Don't let exceptions kill the watcher thread, but
                # surface them so a watcher that's silently
                # skipping every poll is visible in the journal.
                logger.exception(
                    "ConfigWatcher: _check_for_changes raised; continuing"
                )
            
            # Wait for the poll interval or until stop is signaled
            self._stop_event.wait(timeout=self._poll_interval)
    
    def _check_for_changes(self) -> None:
        """
            Check all watched paths for changes.
            
            This method compares the current modification times of watched
            files against their stored values and triggers callbacks for
            any files that have changed.
        """
        with self._lock:
            paths_to_check = set(self._watched_paths)
        
        for path in paths_to_check:
            if not path.exists():
                # File was deleted - check if we had it before
                with self._lock:
                    if path in self._file_mtimes:
                        del self._file_mtimes[path]
                        # Trigger change callback for deleted file
                        self._trigger_change(path)
                continue
            
            if path.is_dir():
                # For directories, check all files within
                self._check_directory(path)
            else:
                # Check single file
                self._check_file(path)
    
    def _check_file(self, path: Path) -> None:
        """
            Check a single file for changes.
            
            :param path: The file path to check.
        """
        try:
            current_mtime = path.stat().st_mtime
        except OSError:
            # File may have been deleted
            return
        
        with self._lock:
            previous_mtime = self._file_mtimes.get(path)
            
            if previous_mtime is None:
                # New file - store mtime and trigger change
                self._file_mtimes[path] = current_mtime
                self._trigger_change(path)
            elif current_mtime != previous_mtime:
                # File was modified
                self._file_mtimes[path] = current_mtime
                self._trigger_change(path)
    
    def _check_directory(self, directory: Path) -> None:
        """
            Check all files in a directory for changes.
            
            :param directory: The directory path to check.
        """
        try:
            for entry in directory.iterdir():
                if entry.is_file():
                    self._check_file(entry)
                elif entry.is_dir():
                    # Recursively check subdirectories
                    self._check_directory(entry)
        except OSError:
            # Directory may have been deleted or permission denied
            pass
    
    def _trigger_change(self, path: Path) -> None:
        """
            Trigger the change callback for a modified file.
            
            :param path: The path of the changed file.
        """
        if self._on_change is not None:
            try:
                self._on_change(path)
            except Exception:
                # Don't let callback exceptions break the watcher,
                # but surface them so a misbehaving subscriber is
                # visible in the journal.
                logger.exception(
                    "ConfigWatcher: on_change callback raised for path=%s",
                    path,
                )
        else:
            # Default behavior: reload the registry
            try:
                self._registry.load(validate=False)
            except Exception:
                # Don't let reload exceptions break the watcher.
                # Operator must be able to see why a config-file
                # change isn't being picked up.
                logger.exception(
                    "ConfigWatcher: registry.load() raised after change to %s",
                    path,
                )
    
    def check_now(self) -> Set[Path]:
        """
            Manually check for changes immediately.
            
            This method performs an immediate check of all watched files
            without waiting for the next poll interval. It returns the
            set of paths that have changed.
            
            :returns: Set of paths that have changed since the last check.
        """
        changed_paths: Set[Path] = set()
        
        with self._lock:
            paths_to_check = set(self._watched_paths)
        
        for path in paths_to_check:
            if not path.exists():
                with self._lock:
                    if path in self._file_mtimes:
                        del self._file_mtimes[path]
                        changed_paths.add(path)
                continue
            
            if path.is_file():
                try:
                    current_mtime = path.stat().st_mtime
                    with self._lock:
                        previous_mtime = self._file_mtimes.get(path)
                        if previous_mtime is None or current_mtime != previous_mtime:
                            self._file_mtimes[path] = current_mtime
                            changed_paths.add(path)
                except OSError:
                    pass
        
        # Trigger callbacks for changed files
        for path in changed_paths:
            self._trigger_change(path)
        
        return changed_paths
    
    def __enter__(self) -> 'ConfigWatcher':
        """
            Context manager entry - start watching.
            
            :returns: Self for use in with statement.
        """
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
            Context manager exit - stop watching.
        """
        self.stop()
