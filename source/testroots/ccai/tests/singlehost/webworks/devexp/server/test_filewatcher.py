"""
    Tests for the FileWatcher class.

    This module contains unit tests and property-based tests for the
    :class:`FileWatcher` class including pattern matching, exclude
    pattern handling, and the auto-reload file exclusion property.
"""

import os
import random
import string
import tempfile
import time

from ccai.webworks.devexp.server.filewatcher import (
    DEFAULT_POLL_INTERVAL,
    FileWatcher,
)


# =============================================================================
# Test Helpers
# =============================================================================

def _make_callback():
    """
        Create a callback that records whether it was called.

        :returns: A tuple of (callback_fn, state_dict) where
            state_dict["called"] is True after the callback fires
            and state_dict["count"] tracks the number of invocations.
    """
    state = {"called": False, "count": 0}

    def callback():
        state["called"] = True
        state["count"] += 1
        return

    return callback, state


# =============================================================================
# Unit Tests for FileWatcher Construction
# =============================================================================

def test_filewatcher_stores_patterns():
    """
        Test that the patterns are stored correctly.
    """
    patterns = ["**/*.py", "**/*.html"]
    callback, _ = _make_callback()

    watcher = FileWatcher(
        patterns=patterns,
        excludes=[],
        callback=callback,
    )

    if watcher.patterns != patterns:
        errmsg = "Expected patterns {}, got {}".format(patterns, watcher.patterns)
        raise AssertionError(errmsg)

    return


def test_filewatcher_stores_excludes():
    """
        Test that the exclude patterns are stored correctly.
    """
    excludes = [".git", "__pycache__"]
    callback, _ = _make_callback()

    watcher = FileWatcher(
        patterns=["**/*.py"],
        excludes=excludes,
        callback=callback,
    )

    if watcher.excludes != excludes:
        errmsg = "Expected excludes {}, got {}".format(excludes, watcher.excludes)
        raise AssertionError(errmsg)

    return


def test_filewatcher_not_running_initially():
    """
        Test that the watcher is not running after construction.
    """
    callback, _ = _make_callback()

    watcher = FileWatcher(
        patterns=["**/*.py"],
        excludes=[],
        callback=callback,
    )

    if watcher.running is not False:
        errmsg = "Expected running=False initially, got {}".format(watcher.running)
        raise AssertionError(errmsg)

    return


def test_filewatcher_default_poll_interval():
    """
        Test that the default poll interval is used when not specified.
    """
    callback, _ = _make_callback()

    watcher = FileWatcher(
        patterns=["**/*.py"],
        excludes=[],
        callback=callback,
    )

    if watcher.poll_interval != DEFAULT_POLL_INTERVAL:
        errmsg = "Expected poll_interval {}, got {}".format(
            DEFAULT_POLL_INTERVAL, watcher.poll_interval
        )
        raise AssertionError(errmsg)

    return


def test_filewatcher_custom_poll_interval():
    """
        Test that a custom poll interval is stored correctly.
    """
    callback, _ = _make_callback()

    watcher = FileWatcher(
        patterns=["**/*.py"],
        excludes=[],
        callback=callback,
        poll_interval=0.5,
    )

    if watcher.poll_interval != 0.5:
        errmsg = "Expected poll_interval 0.5, got {}".format(watcher.poll_interval)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for should_watch
# =============================================================================

def test_should_watch_matches_python_file():
    """
        Test that a .py file matches the **/*.py pattern.
    """
    callback, _ = _make_callback()

    watcher = FileWatcher(
        patterns=["**/*.py"],
        excludes=[],
        callback=callback,
    )

    result = watcher.should_watch("src/app.py")

    if result is not True:
        errmsg = "Expected True for 'src/app.py', got {}".format(result)
        raise AssertionError(errmsg)

    return


def test_should_watch_rejects_non_matching_extension():
    """
        Test that a .txt file does not match the **/*.py pattern.
    """
    callback, _ = _make_callback()

    watcher = FileWatcher(
        patterns=["**/*.py"],
        excludes=[],
        callback=callback,
    )

    result = watcher.should_watch("src/readme.txt")

    if result is not False:
        errmsg = "Expected False for 'src/readme.txt', got {}".format(result)
        raise AssertionError(errmsg)

    return


def test_should_watch_excludes_git_directory():
    """
        Test that files in .git directory are excluded.
    """
    callback, _ = _make_callback()

    watcher = FileWatcher(
        patterns=["**/*.py"],
        excludes=[".git"],
        callback=callback,
    )

    result = watcher.should_watch(".git/hooks/pre-commit.py")

    if result is not False:
        errmsg = "Expected False for '.git/hooks/pre-commit.py', got {}".format(result)
        raise AssertionError(errmsg)

    return


def test_should_watch_excludes_pycache():
    """
        Test that files in __pycache__ directory are excluded.
    """
    callback, _ = _make_callback()

    watcher = FileWatcher(
        patterns=["**/*.py"],
        excludes=["__pycache__"],
        callback=callback,
    )

    result = watcher.should_watch("src/__pycache__/module.cpython-310.pyc")

    if result is not False:
        errmsg = "Expected False for __pycache__ path, got {}".format(result)
        raise AssertionError(errmsg)

    return


def test_should_watch_excludes_pyc_files():
    """
        Test that .pyc files are excluded by the *.pyc pattern.
    """
    callback, _ = _make_callback()

    watcher = FileWatcher(
        patterns=["**/*.py"],
        excludes=["*.pyc"],
        callback=callback,
    )

    result = watcher.should_watch("src/module.pyc")

    if result is not False:
        errmsg = "Expected False for 'src/module.pyc', got {}".format(result)
        raise AssertionError(errmsg)

    return


def test_should_watch_excludes_venv():
    """
        Test that files in .venv directory are excluded.
    """
    callback, _ = _make_callback()

    watcher = FileWatcher(
        patterns=["**/*.py"],
        excludes=[".venv"],
        callback=callback,
    )

    result = watcher.should_watch(".venv/lib/python3.10/site-packages/module.py")

    if result is not False:
        errmsg = "Expected False for .venv path, got {}".format(result)
        raise AssertionError(errmsg)

    return


def test_should_watch_allows_non_excluded_python_file():
    """
        Test that a Python file not in an excluded directory is watched.
    """
    callback, _ = _make_callback()

    watcher = FileWatcher(
        patterns=["**/*.py"],
        excludes=[".git", "__pycache__", ".venv", "*.pyc"],
        callback=callback,
    )

    result = watcher.should_watch("source/packages/mymodule.py")

    if result is not True:
        errmsg = "Expected True for 'source/packages/mymodule.py', got {}".format(result)
        raise AssertionError(errmsg)

    return


def test_should_watch_multiple_patterns():
    """
        Test that multiple watch patterns are all checked.
    """
    callback, _ = _make_callback()

    watcher = FileWatcher(
        patterns=["**/*.py", "**/*.html"],
        excludes=[],
        callback=callback,
    )

    py_result = watcher.should_watch("src/app.py")
    html_result = watcher.should_watch("templates/index.html")

    if py_result is not True:
        errmsg = "Expected True for .py file, got {}".format(py_result)
        raise AssertionError(errmsg)

    if html_result is not True:
        errmsg = "Expected True for .html file, got {}".format(html_result)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for FileWatcher Lifecycle
# =============================================================================

def test_filewatcher_start_sets_running():
    """
        Test that start() sets the running flag to True.
    """
    callback, _ = _make_callback()

    with tempfile.TemporaryDirectory() as tmpdir:
        watcher = FileWatcher(
            patterns=["**/*.py"],
            excludes=[],
            callback=callback,
            base_directory=tmpdir,
            poll_interval=0.1,
        )

        watcher.start()

        try:
            if watcher.running is not True:
                errmsg = "Expected running=True after start, got {}".format(
                    watcher.running
                )
                raise AssertionError(errmsg)
        finally:
            watcher.stop()

    return


def test_filewatcher_stop_clears_running():
    """
        Test that stop() sets the running flag to False.
    """
    callback, _ = _make_callback()

    with tempfile.TemporaryDirectory() as tmpdir:
        watcher = FileWatcher(
            patterns=["**/*.py"],
            excludes=[],
            callback=callback,
            base_directory=tmpdir,
            poll_interval=0.1,
        )

        watcher.start()
        watcher.stop()

        if watcher.running is not False:
            errmsg = "Expected running=False after stop, got {}".format(
                watcher.running
            )
            raise AssertionError(errmsg)

    return


def test_filewatcher_detects_file_change():
    """
        Test that the watcher detects a file modification and calls
        the callback.
    """
    callback, state = _make_callback()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create an initial file
        filepath = os.path.join(tmpdir, "test_module.py")
        with open(filepath, "w") as fh:
            fh.write("# initial content\n")

        watcher = FileWatcher(
            patterns=["**/*.py"],
            excludes=[],
            callback=callback,
            base_directory=tmpdir,
            poll_interval=0.1,
        )

        watcher.start()

        try:
            # Modify the file
            time.sleep(0.2)
            with open(filepath, "w") as fh:
                fh.write("# modified content\n")

            # Wait for the watcher to detect the change
            time.sleep(0.5)

            if state["called"] is not True:
                errmsg = "Expected callback to be called after file change."
                raise AssertionError(errmsg)
        finally:
            watcher.stop()

    return


def test_filewatcher_does_not_trigger_for_excluded_file():
    """
        Test that modifying an excluded file does not trigger the callback.
    """
    callback, state = _make_callback()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a .pyc file (excluded)
        filepath = os.path.join(tmpdir, "module.pyc")
        with open(filepath, "w") as fh:
            fh.write("initial")

        watcher = FileWatcher(
            patterns=["**/*.py"],
            excludes=["*.pyc"],
            callback=callback,
            base_directory=tmpdir,
            poll_interval=0.1,
        )

        watcher.start()

        try:
            # Modify the excluded file
            time.sleep(0.2)
            with open(filepath, "w") as fh:
                fh.write("modified")

            # Wait and verify callback was NOT called
            time.sleep(0.5)

            if state["called"] is True:
                errmsg = "Callback should NOT be called for excluded .pyc file."
                raise AssertionError(errmsg)
        finally:
            watcher.stop()

    return



# =============================================================================
# Property Test Helpers
# =============================================================================

# Common directory names used as exclude patterns
_COMMON_EXCLUDE_DIRS = [
    ".git", "__pycache__", ".venv", "node_modules", ".tox",
    ".mypy_cache", ".pytest_cache", "dist", "build", ".eggs",
    ".hg", ".svn", ".idea", ".vscode",
]

# Common file extension exclude patterns
_COMMON_EXCLUDE_EXTENSIONS = [
    "*.pyc", "*.pyo", "*.so", "*.o", "*.a", "*.lib",
    "*.egg", "*.whl", "*.log", "*.tmp", "*.bak",
]

# Common watch patterns
_COMMON_WATCH_PATTERNS = [
    "**/*.py", "**/*.html", "**/*.css", "**/*.js",
    "**/*.yaml", "**/*.yml", "**/*.json", "**/*.toml",
]


def _random_filename(extension=None):
    """
        Generate a random filename with the given extension.

        :param extension: The file extension including the dot
            (e.g. ``.py``). If ``None``, a random extension is chosen.

        :returns: A random filename string.
    """
    name_length = random.randint(3, 15)
    name = "".join(random.choices(string.ascii_lowercase, k=name_length))

    if extension is None:
        ext_choices = [".py", ".pyc", ".html", ".css", ".js", ".txt", ".log"]
        extension = random.choice(ext_choices)

    filename = name + extension

    return filename


def _random_directory_path(depth=None):
    """
        Generate a random directory path with the given depth.

        :param depth: Number of directory components. If ``None``,
            a random depth between 1 and 5 is chosen.

        :returns: A path string with forward slashes.
    """
    if depth is None:
        depth = random.randint(1, 5)

    parts = []
    for _ in range(depth):
        part_length = random.randint(2, 10)
        part = "".join(random.choices(string.ascii_lowercase, k=part_length))
        parts.append(part)

    path = "/".join(parts)

    return path


def _generate_excluded_path(excludes):
    """
        Generate a file path that contains at least one excluded
        component.

        :param excludes: The list of exclude patterns.

        :returns: A file path string that should be excluded.
    """
    # Separate directory excludes from file extension excludes
    dir_excludes = []
    ext_excludes = []

    for pattern in excludes:
        if pattern.startswith("*."):
            ext_excludes.append(pattern)
        else:
            dir_excludes.append(pattern)

    strategy = random.choice(["dir", "ext"])

    if strategy == "dir" and len(dir_excludes) > 0:
        # Place an excluded directory name in the path
        excluded_dir = random.choice(dir_excludes)
        prefix = _random_directory_path(depth=random.randint(0, 3))
        suffix = _random_filename(extension=".py")

        if prefix:
            path = "{}/{}/{}".format(prefix, excluded_dir, suffix)
        else:
            path = "{}/{}".format(excluded_dir, suffix)

        return path

    if strategy == "ext" and len(ext_excludes) > 0:
        # Use an excluded file extension
        ext_pattern = random.choice(ext_excludes)
        # Extract the extension from the pattern (e.g. "*.pyc" -> ".pyc")
        extension = ext_pattern[1:]  # Remove the leading *
        prefix = _random_directory_path(depth=random.randint(1, 4))
        filename = _random_filename(extension=extension)
        path = "{}/{}".format(prefix, filename)

        return path

    # Fallback: use any available exclude
    if len(dir_excludes) > 0:
        excluded_dir = random.choice(dir_excludes)
        suffix = _random_filename(extension=".py")
        path = "{}/{}".format(excluded_dir, suffix)
        return path

    if len(ext_excludes) > 0:
        ext_pattern = random.choice(ext_excludes)
        extension = ext_pattern[1:]
        filename = _random_filename(extension=extension)
        path = "src/{}".format(filename)
        return path

    # Should not reach here if excludes is non-empty
    return ".git/config"


# =============================================================================
# Property 5: Auto-Reload File Exclusion
# Feature: developer-experience, Property 5: Auto-Reload File Exclusion
# Validates: Requirements 4.4
# =============================================================================

_PROPERTY_ITERATIONS = 100


def test_property_5_excluded_files_not_watched():
    """
        Property 5: Auto-Reload File Exclusion

        For any file path matching an exclude pattern, the FileWatcher
        SHALL NOT trigger a reload callback when that file changes.

        This test generates random file paths that match exclude patterns
        and verifies that should_watch returns False for all of them,
        across 100 iterations.

        **Feature: developer-experience, Property 5: Auto-Reload File Exclusion**
        **Validates: Requirements 4.4**
    """
    for iteration in range(_PROPERTY_ITERATIONS):
        # Generate a random set of exclude patterns
        num_dir_excludes = random.randint(1, 5)
        num_ext_excludes = random.randint(1, 4)

        dir_excludes = random.sample(
            _COMMON_EXCLUDE_DIRS,
            k=min(num_dir_excludes, len(_COMMON_EXCLUDE_DIRS)),
        )
        ext_excludes = random.sample(
            _COMMON_EXCLUDE_EXTENSIONS,
            k=min(num_ext_excludes, len(_COMMON_EXCLUDE_EXTENSIONS)),
        )
        excludes = dir_excludes + ext_excludes

        # Use a broad watch pattern so the exclusion logic is the deciding factor
        watch_patterns = ["**/*.py", "**/*.html", "**/*.css", "**/*.js",
                          "**/*.pyc", "**/*.pyo", "**/*.so", "**/*.log"]

        callback, state = _make_callback()

        watcher = FileWatcher(
            patterns=watch_patterns,
            excludes=excludes,
            callback=callback,
        )

        # Generate multiple excluded paths and verify each one
        num_paths = random.randint(1, 5)

        for path_idx in range(num_paths):
            excluded_path = _generate_excluded_path(excludes)

            result = watcher.should_watch(excluded_path)

            if result is not False:
                errmsg = (
                    "Iteration {}, path {}: should_watch returned True "
                    "for excluded path '{}'. Excludes: {}"
                ).format(iteration, path_idx, excluded_path, excludes)
                raise AssertionError(errmsg)

    return


def test_property_5_excluded_dir_in_any_position():
    """
        Property 5: Auto-Reload File Exclusion

        For any file path where an excluded directory name appears at
        any depth in the path, the FileWatcher SHALL NOT trigger a
        reload callback.

        This test verifies that exclude patterns match directory names
        regardless of their position in the path hierarchy.

        **Feature: developer-experience, Property 5: Auto-Reload File Exclusion**
        **Validates: Requirements 4.4**
    """
    for iteration in range(_PROPERTY_ITERATIONS):
        # Pick a random excluded directory name
        excluded_dir = random.choice(_COMMON_EXCLUDE_DIRS)

        # Generate a path with the excluded dir at a random depth
        depth_before = random.randint(0, 4)
        depth_after = random.randint(0, 3)

        parts_before = []
        for _ in range(depth_before):
            part_len = random.randint(2, 8)
            part = "".join(random.choices(string.ascii_lowercase, k=part_len))
            parts_before.append(part)

        parts_after = []
        for _ in range(depth_after):
            part_len = random.randint(2, 8)
            part = "".join(random.choices(string.ascii_lowercase, k=part_len))
            parts_after.append(part)

        filename = _random_filename(extension=".py")

        all_parts = parts_before + [excluded_dir] + parts_after + [filename]
        path = "/".join(all_parts)

        callback, _ = _make_callback()

        watcher = FileWatcher(
            patterns=["**/*.py"],
            excludes=[excluded_dir],
            callback=callback,
        )

        result = watcher.should_watch(path)

        if result is not False:
            errmsg = (
                "Iteration {}: should_watch returned True for path '{}' "
                "which contains excluded dir '{}'"
            ).format(iteration, path, excluded_dir)
            raise AssertionError(errmsg)

    return


def test_property_5_excluded_extension_always_rejected():
    """
        Property 5: Auto-Reload File Exclusion

        For any file path with an excluded file extension, the
        FileWatcher SHALL NOT trigger a reload callback, regardless
        of the directory structure.

        **Feature: developer-experience, Property 5: Auto-Reload File Exclusion**
        **Validates: Requirements 4.4**
    """
    for iteration in range(_PROPERTY_ITERATIONS):
        # Pick a random excluded extension pattern
        ext_pattern = random.choice(_COMMON_EXCLUDE_EXTENSIONS)
        extension = ext_pattern[1:]  # Remove leading *

        # Generate a random directory path (no excluded dirs)
        safe_dirs = ["src", "lib", "app", "core", "utils", "modules"]
        depth = random.randint(1, 4)
        dir_parts = [random.choice(safe_dirs) for _ in range(depth)]

        filename = _random_filename(extension=extension)
        path = "/".join(dir_parts + [filename])

        # Use broad watch patterns that would match the extension
        watch_patterns = ["**/*" + extension, "**/*.py"]

        callback, _ = _make_callback()

        watcher = FileWatcher(
            patterns=watch_patterns,
            excludes=[ext_pattern],
            callback=callback,
        )

        result = watcher.should_watch(path)

        if result is not False:
            errmsg = (
                "Iteration {}: should_watch returned True for path '{}' "
                "with excluded extension pattern '{}'"
            ).format(iteration, path, ext_pattern)
            raise AssertionError(errmsg)

    return
