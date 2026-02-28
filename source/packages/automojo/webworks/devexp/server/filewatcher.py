"""
    File watcher for the development server auto-reload feature.

    This module provides the :class:`FileWatcher` class that monitors
    source files for changes and triggers a callback when modifications
    are detected. The watcher supports configurable watch patterns and
    exclude patterns to control which files are monitored.

    The watcher uses a polling approach for maximum portability across
    platforms. It checks file modification times at a configurable
    interval and invokes the callback when changes are detected.
"""

import fnmatch
import logging
import os
import threading
import time

from typing import Callable, Dict, List, Optional


logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

DEFAULT_POLL_INTERVAL: float = 1.0
"""Default interval in seconds between file system polls."""


# =============================================================================
# FileWatcher
# =============================================================================

class FileWatcher:
    """
        Watches files for changes and triggers a callback.

        The watcher monitors files matching the configured patterns
        while excluding files that match any exclude pattern. When a
        change is detected, the registered callback is invoked.

        The watcher runs in a background thread using a polling
        strategy that checks file modification times.
    """

    def __init__(
        self,
        patterns: List[str],
        excludes: List[str],
        callback: Callable[[], None],
        poll_interval: float = DEFAULT_POLL_INTERVAL,
        base_directory: Optional[str] = None,
    ):
        """
            Construct a FileWatcher.

            :param patterns: Glob patterns for files to watch (e.g. ``["**/*.py"]``).
            :param excludes: Patterns for files or directories to exclude
                (e.g. ``[".git", "__pycache__", ".venv", "*.pyc"]``).
            :param callback: A callable invoked when a watched file changes.
            :param poll_interval: Seconds between file system polls.
            :param base_directory: The root directory to watch. Defaults to
                the current working directory.
        """
        self._patterns = list(patterns)
        self._excludes = list(excludes)
        self._callback = callback
        self._poll_interval = poll_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._file_mtimes: Dict[str, float] = {}
        self._last_error: Optional[Exception] = None

        if base_directory is not None:
            self._base_directory = base_directory
        else:
            self._base_directory = os.getcwd()

        return

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def patterns(self) -> List[str]:
        """
            The glob patterns for files being watched.

            :returns: A list of pattern strings.
        """
        return list(self._patterns)

    @property
    def excludes(self) -> List[str]:
        """
            The patterns for excluded files and directories.

            :returns: A list of exclusion pattern strings.
        """
        return list(self._excludes)

    @property
    def running(self) -> bool:
        """
            Whether the watcher is currently running.

            :returns: ``True`` if the watcher is actively polling.
        """
        return self._running

    @property
    def poll_interval(self) -> float:
        """
            The polling interval in seconds.

            :returns: The interval as a float.
        """
        return self._poll_interval

    @property
    def base_directory(self) -> str:
        """
            The root directory being watched.

            :returns: The directory path string.
        """
        return self._base_directory

    @property
    def last_error(self) -> Optional[Exception]:
        """
            The last error encountered during polling, if any.

            :returns: The exception or ``None``.
        """
        return self._last_error

    # -------------------------------------------------------------------------
    # Lifecycle Methods
    # -------------------------------------------------------------------------

    def start(self) -> None:
        """
            Start watching for file changes.

            Performs an initial scan of the file system to establish
            baseline modification times, then starts a background
            thread that polls for changes.
        """
        if self._running is True:
            return

        self._file_mtimes = self._scan_files()
        self._running = True

        self._thread = threading.Thread(
            target=self._poll_loop,
            name="filewatcher-poll",
            daemon=True,
        )
        self._thread.start()

        logger.info(
            "FileWatcher started watching %d files in '%s'.",
            len(self._file_mtimes),
            self._base_directory,
        )

        return

    def stop(self) -> None:
        """
            Stop watching for file changes.

            Signals the polling thread to stop and waits for it to
            finish.
        """
        self._running = False

        if self._thread is not None:
            self._thread.join(timeout=self._poll_interval * 2)
            self._thread = None

        logger.info("FileWatcher stopped.")

        return

    # -------------------------------------------------------------------------
    # Pattern Matching
    # -------------------------------------------------------------------------

    def should_watch(self, path: str) -> bool:
        """
            Check if a file path should be watched.

            A path is watched if it matches at least one watch pattern
            and does not match any exclude pattern. Exclude patterns
            are checked against each component of the path as well as
            the full path and the filename.

            :param path: The file path to check. Can be absolute or
                relative.

            :returns: ``True`` if the path should be watched.
        """
        is_excluded = self._matches_exclude(path)

        if is_excluded is True:
            return False

        matches_pattern = self._matches_watch_pattern(path)

        return matches_pattern

    def _matches_exclude(self, path: str) -> bool:
        """
            Check if a path matches any exclude pattern.

            The exclude patterns are tested against the full path,
            the filename, and each individual path component. This
            allows patterns like ``.git`` to match the directory
            name anywhere in the path.

            :param path: The file path to check.

            :returns: ``True`` if the path matches an exclude pattern.
        """
        normalized = os.path.normpath(path)
        parts = normalized.replace("\\", "/").split("/")
        filename = os.path.basename(normalized)

        for exclude in self._excludes:
            # Check the full path
            if fnmatch.fnmatch(normalized, exclude):
                return True

            # Check the filename alone
            if fnmatch.fnmatch(filename, exclude):
                return True

            # Check each path component
            for part in parts:
                if fnmatch.fnmatch(part, exclude):
                    return True

        return False

    def _matches_watch_pattern(self, path: str) -> bool:
        """
            Check if a path matches any watch pattern.

            Uses :func:`fnmatch.fnmatch` against the full path and
            the filename for simple extension patterns.

            :param path: The file path to check.

            :returns: ``True`` if the path matches a watch pattern.
        """
        normalized = os.path.normpath(path)
        filename = os.path.basename(normalized)

        for pattern in self._patterns:
            # Check the full path against the pattern
            if fnmatch.fnmatch(normalized, pattern):
                return True

            # Check the filename against the pattern
            if fnmatch.fnmatch(filename, pattern):
                return True

            # For recursive glob patterns like **/*.py, extract the
            # file-level pattern and match against the filename
            if pattern.startswith("**/"):
                file_pattern = pattern[3:]
                if fnmatch.fnmatch(filename, file_pattern):
                    return True

        return False

    # -------------------------------------------------------------------------
    # File Scanning
    # -------------------------------------------------------------------------

    def _scan_files(self) -> Dict[str, float]:
        """
            Scan the base directory for files matching watch patterns.

            Walks the directory tree, skipping excluded directories,
            and records the modification time of each matching file.

            :returns: A dictionary mapping file paths to their
                modification times.
        """
        mtimes: Dict[str, float] = {}

        for dirpath, dirnames, filenames in os.walk(self._base_directory):
            # Filter out excluded directories in-place so os.walk
            # does not descend into them
            filtered_dirs = []
            for dirname in dirnames:
                full_dir = os.path.join(dirpath, dirname)
                is_excluded = self._matches_exclude(full_dir)
                if is_excluded is False:
                    filtered_dirs.append(dirname)
            dirnames[:] = filtered_dirs

            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                should_watch = self.should_watch(filepath)

                if should_watch is True:
                    try:
                        mtime = os.path.getmtime(filepath)
                        mtimes[filepath] = mtime
                    except OSError:
                        # File may have been deleted between listing
                        # and stat; skip it silently
                        pass

        return mtimes

    # -------------------------------------------------------------------------
    # Change Detection
    # -------------------------------------------------------------------------

    def _poll_loop(self) -> None:
        """
            Background polling loop that checks for file changes.

            Runs until :attr:`_running` is set to ``False``. On each
            iteration, scans the file system and compares modification
            times against the stored baseline.
        """
        while self._running is True:
            time.sleep(self._poll_interval)

            if self._running is False:
                break

            try:
                self._check_for_changes()
            except Exception as exc:
                self._last_error = exc
                logger.warning(
                    "FileWatcher encountered an error during polling: %s",
                    exc,
                )

        return

    def _check_for_changes(self) -> None:
        """
            Check for file changes and invoke the callback if any
            are detected.

            Compares the current file modification times against the
            stored baseline. If any file has been added, removed, or
            modified, the callback is invoked and the baseline is
            updated.
        """
        current_mtimes = self._scan_files()

        changed = False

        # Check for modified or new files
        for filepath, mtime in current_mtimes.items():
            old_mtime = self._file_mtimes.get(filepath)

            if old_mtime is None:
                # New file
                logger.debug("New file detected: %s", filepath)
                changed = True
                break

            if mtime != old_mtime:
                # Modified file
                logger.debug("File modified: %s", filepath)
                changed = True
                break

        if changed is False:
            # Check for deleted files
            for filepath in self._file_mtimes:
                if filepath not in current_mtimes:
                    logger.debug("File deleted: %s", filepath)
                    changed = True
                    break

        if changed is True:
            self._file_mtimes = current_mtimes
            self._on_change()

        return

    def _on_change(self) -> None:
        """
            Handle a detected file change by invoking the callback.

            If the callback raises an exception, it is caught and
            stored as :attr:`last_error` so the watcher can continue
            monitoring for further changes.
        """
        try:
            self._callback()
        except Exception as exc:
            self._last_error = exc
            logger.warning(
                "FileWatcher callback raised an exception: %s",
                exc,
            )

        return
