"""
    Tests for the production server ProcessManager class.

    This module contains unit tests for process management functionality
    including PID file handling, daemon mode, privilege dropping, and
    working directory changes.
"""

import os
import signal
import tempfile

from automojo.webworks.prodserver.serverconfig import ServerConfig
from automojo.webworks.prodserver.processmanager import (
    DaemonError,
    PidFileError,
    PrivilegeError,
    ProcessManager,
    ProcessManagerError,
)


# =============================================================================
# Unit Tests for PID File Handling
# =============================================================================

def test_pid_file_path_none_by_default():
    """
        Test that pid_file_path is None with default configuration.
    """
    config = ServerConfig()
    manager = ProcessManager(config)

    if manager.pid_file_path is not None:
        errmsg = "Expected pid_file_path to be None with default config"
        raise AssertionError(errmsg)

    return


def test_pid_file_path_returns_configured_value():
    """
        Test that pid_file_path returns the configured path.
    """
    config = ServerConfig(pid_file="/tmp/test.pid")
    manager = ProcessManager(config)

    if manager.pid_file_path != "/tmp/test.pid":
        errmsg = f"Expected '/tmp/test.pid', got '{manager.pid_file_path}'"
        raise AssertionError(errmsg)

    return


def test_pid_file_not_written_initially():
    """
        Test that pid_file_written is False before write_pid_file is called.
    """
    config = ServerConfig(pid_file="/tmp/test.pid")
    manager = ProcessManager(config)

    if manager.pid_file_written:
        errmsg = "Expected pid_file_written to be False initially"
        raise AssertionError(errmsg)

    return


def test_write_pid_file_no_op_when_not_configured():
    """
        Test that write_pid_file does nothing when pid_file is None.
    """
    config = ServerConfig()
    manager = ProcessManager(config)

    # Should not raise
    manager.write_pid_file()

    if manager.pid_file_written:
        errmsg = "Expected pid_file_written to remain False when not configured"
        raise AssertionError(errmsg)

    return


def test_write_pid_file_creates_file():
    """
        Test that write_pid_file creates a file with the current PID.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        pid_path = os.path.join(tmpdir, "server.pid")
        config = ServerConfig(pid_file=pid_path)
        manager = ProcessManager(config)

        manager.write_pid_file()

        if not manager.pid_file_written:
            errmsg = "Expected pid_file_written to be True after writing"
            raise AssertionError(errmsg)

        if not os.path.exists(pid_path):
            errmsg = f"Expected PID file to exist at '{pid_path}'"
            raise AssertionError(errmsg)

        with open(pid_path, "r") as fh:
            content = fh.read().strip()

        expected_pid = str(os.getpid())
        if content != expected_pid:
            errmsg = f"Expected PID '{expected_pid}', got '{content}'"
            raise AssertionError(errmsg)

    return


def test_write_pid_file_raises_when_running_process_exists():
    """
        Test that write_pid_file raises PidFileError when the PID file
        contains a PID of a running process.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        pid_path = os.path.join(tmpdir, "server.pid")

        # Write our own PID to simulate a running process
        current_pid = os.getpid()
        with open(pid_path, "w") as fh:
            fh.write(str(current_pid))

        config = ServerConfig(pid_file=pid_path)
        manager = ProcessManager(config)

        raised = False
        try:
            manager.write_pid_file()
        except PidFileError:
            raised = True

        if not raised:
            errmsg = "Expected PidFileError when PID file has running process"
            raise AssertionError(errmsg)

    return


def test_write_pid_file_overwrites_stale_pid():
    """
        Test that write_pid_file overwrites a PID file with a non-running PID.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        pid_path = os.path.join(tmpdir, "server.pid")

        # Write a PID that is very unlikely to be running
        with open(pid_path, "w") as fh:
            fh.write("999999999")

        config = ServerConfig(pid_file=pid_path)
        manager = ProcessManager(config)

        # Should succeed since the PID is not running
        manager.write_pid_file()

        if not manager.pid_file_written:
            errmsg = "Expected pid_file_written to be True after overwriting stale PID"
            raise AssertionError(errmsg)

        with open(pid_path, "r") as fh:
            content = fh.read().strip()

        expected_pid = str(os.getpid())
        if content != expected_pid:
            errmsg = f"Expected PID '{expected_pid}', got '{content}'"
            raise AssertionError(errmsg)

    return


def test_write_pid_file_raises_on_invalid_path():
    """
        Test that write_pid_file raises PidFileError for an invalid path.
    """
    config = ServerConfig(pid_file="/nonexistent/directory/server.pid")
    manager = ProcessManager(config)

    raised = False
    try:
        manager.write_pid_file()
    except PidFileError:
        raised = True

    if not raised:
        errmsg = "Expected PidFileError for invalid PID file path"
        raise AssertionError(errmsg)

    return


def test_cleanup_pid_file_removes_file():
    """
        Test that cleanup_pid_file removes the PID file.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        pid_path = os.path.join(tmpdir, "server.pid")
        config = ServerConfig(pid_file=pid_path)
        manager = ProcessManager(config)

        manager.write_pid_file()
        manager.cleanup_pid_file()

        if os.path.exists(pid_path):
            errmsg = "Expected PID file to be removed after cleanup"
            raise AssertionError(errmsg)

        if manager.pid_file_written:
            errmsg = "Expected pid_file_written to be False after cleanup"
            raise AssertionError(errmsg)

    return


def test_cleanup_pid_file_no_op_when_not_written():
    """
        Test that cleanup_pid_file does nothing when PID file was not written.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        pid_path = os.path.join(tmpdir, "server.pid")

        # Create a PID file externally
        with open(pid_path, "w") as fh:
            fh.write("12345")

        config = ServerConfig(pid_file=pid_path)
        manager = ProcessManager(config)

        # Should not remove the file since we did not write it
        manager.cleanup_pid_file()

        if not os.path.exists(pid_path):
            errmsg = "Expected PID file to remain when not written by this instance"
            raise AssertionError(errmsg)

    return


def test_cleanup_pid_file_no_op_when_not_configured():
    """
        Test that cleanup_pid_file does nothing when pid_file is None.
    """
    config = ServerConfig()
    manager = ProcessManager(config)

    # Should not raise
    manager.cleanup_pid_file()

    return


def test_cleanup_pid_file_handles_already_removed():
    """
        Test that cleanup_pid_file handles the case where the file
        was already removed externally.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        pid_path = os.path.join(tmpdir, "server.pid")
        config = ServerConfig(pid_file=pid_path)
        manager = ProcessManager(config)

        manager.write_pid_file()

        # Remove the file externally
        os.remove(pid_path)

        # Should not raise
        manager.cleanup_pid_file()

        if manager.pid_file_written:
            errmsg = "Expected pid_file_written to be False after cleanup"
            raise AssertionError(errmsg)

    return


def test_read_pid_file_returns_pid():
    """
        Test that read_pid_file returns the PID from the file.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        pid_path = os.path.join(tmpdir, "server.pid")
        config = ServerConfig(pid_file=pid_path)
        manager = ProcessManager(config)

        manager.write_pid_file()

        result = manager.read_pid_file()
        expected = os.getpid()

        if result != expected:
            errmsg = f"Expected PID {expected}, got {result}"
            raise AssertionError(errmsg)

    return


def test_read_pid_file_returns_none_when_missing():
    """
        Test that read_pid_file returns None when the file does not exist.
    """
    config = ServerConfig(pid_file="/nonexistent/server.pid")
    manager = ProcessManager(config)

    result = manager.read_pid_file()

    if result is not None:
        errmsg = f"Expected None for missing PID file, got {result}"
        raise AssertionError(errmsg)

    return


def test_read_pid_file_returns_none_when_not_configured():
    """
        Test that read_pid_file returns None when pid_file is not configured.
    """
    config = ServerConfig()
    manager = ProcessManager(config)

    result = manager.read_pid_file()

    if result is not None:
        errmsg = f"Expected None when not configured, got {result}"
        raise AssertionError(errmsg)

    return


def test_read_pid_file_returns_none_for_invalid_content():
    """
        Test that read_pid_file returns None when the file has invalid content.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        pid_path = os.path.join(tmpdir, "server.pid")

        with open(pid_path, "w") as fh:
            fh.write("not-a-number")

        config = ServerConfig(pid_file=pid_path)
        manager = ProcessManager(config)

        result = manager.read_pid_file()

        if result is not None:
            errmsg = f"Expected None for invalid content, got {result}"
            raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Daemon Mode
# =============================================================================

def test_daemonize_no_op_when_not_configured():
    """
        Test that daemonize does nothing when daemon is False.
    """
    config = ServerConfig(daemon=False)
    manager = ProcessManager(config)

    # Should not raise or fork
    manager.daemonize()

    return


# =============================================================================
# Unit Tests for Privilege Dropping
# =============================================================================

def test_drop_privileges_no_op_with_defaults():
    """
        Test that drop_privileges does nothing with default configuration.
    """
    config = ServerConfig()
    manager = ProcessManager(config)

    # Should not raise since user, group are None and umask is 0
    manager.drop_privileges()

    return


def test_apply_umask_sets_value():
    """
        Test that drop_privileges applies the configured umask.
    """
    original_umask = os.umask(0o022)
    os.umask(original_umask)

    config = ServerConfig(umask=0o077)
    manager = ProcessManager(config)

    manager.drop_privileges()

    # Read back the umask (setting it returns the previous value)
    current = os.umask(original_umask)

    if current != 0o077:
        errmsg = f"Expected umask 0o077, got {oct(current)}"
        # Restore original before raising
        os.umask(original_umask)
        raise AssertionError(errmsg)

    return


def test_apply_umask_skipped_when_zero():
    """
        Test that umask is not changed when configured as 0.
    """
    original_umask = os.umask(0o022)
    os.umask(original_umask)

    config = ServerConfig(umask=0)
    manager = ProcessManager(config)

    manager.drop_privileges()

    current = os.umask(original_umask)
    os.umask(original_umask)

    if current != original_umask:
        errmsg = f"Expected umask to remain {oct(original_umask)}, got {oct(current)}"
        raise AssertionError(errmsg)

    return


def test_apply_user_raises_for_nonexistent_user():
    """
        Test that drop_privileges raises PrivilegeError for a
        nonexistent user.
    """
    config = ServerConfig(user="nonexistent_user_xyz_12345")
    manager = ProcessManager(config)

    raised = False
    try:
        manager.drop_privileges()
    except PrivilegeError:
        raised = True

    if not raised:
        errmsg = "Expected PrivilegeError for nonexistent user"
        raise AssertionError(errmsg)

    return


def test_apply_group_raises_for_nonexistent_group():
    """
        Test that drop_privileges raises PrivilegeError for a
        nonexistent group.
    """
    config = ServerConfig(group="nonexistent_group_xyz_12345")
    manager = ProcessManager(config)

    raised = False
    try:
        manager.drop_privileges()
    except PrivilegeError:
        raised = True

    if not raised:
        errmsg = "Expected PrivilegeError for nonexistent group"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Working Directory Change
# =============================================================================

def test_change_directory_no_op_when_not_configured():
    """
        Test that change_directory does nothing when chdir is None.
    """
    original_dir = os.getcwd()
    config = ServerConfig()
    manager = ProcessManager(config)

    manager.change_directory()

    current_dir = os.getcwd()
    if current_dir != original_dir:
        os.chdir(original_dir)
        errmsg = f"Expected directory to remain '{original_dir}', got '{current_dir}'"
        raise AssertionError(errmsg)

    return


def test_change_directory_changes_to_target():
    """
        Test that change_directory changes to the configured directory.
    """
    original_dir = os.getcwd()

    with tempfile.TemporaryDirectory() as tmpdir:
        config = ServerConfig(chdir=tmpdir)
        manager = ProcessManager(config)

        manager.change_directory()

        current_dir = os.getcwd()

        # Resolve symlinks for comparison (macOS /tmp -> /private/tmp)
        resolved_current = os.path.realpath(current_dir)
        resolved_target = os.path.realpath(tmpdir)

        # Restore before assertions
        os.chdir(original_dir)

        if resolved_current != resolved_target:
            errmsg = f"Expected directory '{resolved_target}', got '{resolved_current}'"
            raise AssertionError(errmsg)

    return


def test_change_directory_raises_for_nonexistent():
    """
        Test that change_directory raises ProcessManagerError for a
        nonexistent directory.
    """
    config = ServerConfig(chdir="/nonexistent/directory/xyz")
    manager = ProcessManager(config)

    raised = False
    try:
        manager.change_directory()
    except ProcessManagerError:
        raised = True

    if not raised:
        errmsg = "Expected ProcessManagerError for nonexistent directory"
        raise AssertionError(errmsg)

    return


def test_restore_directory_restores_original():
    """
        Test that restore_directory returns to the original directory.
    """
    original_dir = os.getcwd()

    with tempfile.TemporaryDirectory() as tmpdir:
        config = ServerConfig(chdir=tmpdir)
        manager = ProcessManager(config)

        manager.change_directory()
        manager.restore_directory()

        current_dir = os.getcwd()
        resolved_current = os.path.realpath(current_dir)
        resolved_original = os.path.realpath(original_dir)

        if resolved_current != resolved_original:
            os.chdir(original_dir)
            errmsg = f"Expected directory '{resolved_original}', got '{resolved_current}'"
            raise AssertionError(errmsg)

    return


def test_restore_directory_no_op_when_not_changed():
    """
        Test that restore_directory does nothing when directory was not changed.
    """
    original_dir = os.getcwd()
    config = ServerConfig()
    manager = ProcessManager(config)

    # Should not raise
    manager.restore_directory()

    current_dir = os.getcwd()
    if current_dir != original_dir:
        os.chdir(original_dir)
        errmsg = "Expected directory to remain unchanged"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Status
# =============================================================================

def test_get_status_returns_expected_fields():
    """
        Test that get_status returns all expected fields.
    """
    config = ServerConfig(
        pid_file="/tmp/test.pid",
        daemon=True,
        user="testuser",
        group="testgroup",
        umask=0o077,
        chdir="/tmp",
    )
    manager = ProcessManager(config)

    status = manager.get_status()

    expected_keys = {
        "pid", "pid_file", "pid_file_written", "daemon",
        "user", "group", "umask", "chdir", "working_directory",
    }

    missing = expected_keys - set(status.keys())
    if missing:
        errmsg = f"Missing status keys: {missing}"
        raise AssertionError(errmsg)

    if status["pid"] != os.getpid():
        errmsg = f"Expected pid {os.getpid()}, got {status['pid']}"
        raise AssertionError(errmsg)

    if status["pid_file"] != "/tmp/test.pid":
        errmsg = f"Expected pid_file '/tmp/test.pid', got '{status['pid_file']}'"
        raise AssertionError(errmsg)

    if status["daemon"] is not True:
        errmsg = "Expected daemon to be True"
        raise AssertionError(errmsg)

    if status["user"] != "testuser":
        errmsg = f"Expected user 'testuser', got '{status['user']}'"
        raise AssertionError(errmsg)

    if status["group"] != "testgroup":
        errmsg = f"Expected group 'testgroup', got '{status['group']}'"
        raise AssertionError(errmsg)

    if status["umask"] != 0o077:
        errmsg = f"Expected umask 0o077, got {oct(status['umask'])}"
        raise AssertionError(errmsg)

    return


def test_is_process_running_detects_current_process():
    """
        Test that _is_process_running returns True for the current process.
    """
    result = ProcessManager._is_process_running(os.getpid())

    if not result:
        errmsg = "Expected current process to be detected as running"
        raise AssertionError(errmsg)

    return


def test_is_process_running_returns_false_for_nonexistent():
    """
        Test that _is_process_running returns False for a non-running PID.
    """
    result = ProcessManager._is_process_running(999999999)

    if result:
        errmsg = "Expected non-running PID to return False"
        raise AssertionError(errmsg)

    return
