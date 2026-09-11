"""
    Process management module for the production server.

    This module provides the ProcessManager class that handles PID file
    management, daemon mode, privilege dropping (user/group/umask), and
    working directory changes for production deployments.
"""

import logging
import os
import signal
import sys
from typing import Any, Dict, Optional, TYPE_CHECKING

from ccai.errors.exceptions import ConfigurationError

# The POSIX account database modules do not exist on Windows. Importing
# them conditionally keeps the rest of the process manager (PID files,
# working directory, status) usable there; the privilege-dropping paths
# that need them raise ConfigurationError when they are configured on a
# platform that cannot honour them.
try:
    import grp
    import pwd
except ImportError:
    grp = None
    pwd = None

if TYPE_CHECKING:
    from ccai.webworks.prodserver.serverconfig import ServerConfig


# Default logger for process manager
_logger = logging.getLogger("webworks.prodserver.processmanager")


class ProcessManagerError(Exception):
    """
        Raised when a process management operation fails.
    """
    pass


class PidFileError(ProcessManagerError):
    """
        Raised when PID file operations fail.
    """
    pass


class DaemonError(ProcessManagerError):
    """
        Raised when daemonization fails.
    """
    pass


class PrivilegeError(ProcessManagerError):
    """
        Raised when privilege dropping fails.
    """
    pass


class ProcessManager:
    """
        Manages process-level concerns for the production server.

        Handles PID file creation and cleanup, daemonization, privilege
        dropping (user, group, umask), and working directory changes.
    """

    def __init__(self, config: "ServerConfig"):
        """
            Construct a ProcessManager.

            :param config: Server configuration containing process settings.
        """
        self._config = config
        self._pid_file_written = False
        self._original_dir: Optional[str] = None
        self._original_umask: Optional[int] = None

        return

    @property
    def pid_file_path(self) -> Optional[str]:
        """
            Get the configured PID file path.

            :returns: The PID file path or None if not configured.
        """
        return self._config.pid_file

    @property
    def pid_file_written(self) -> bool:
        """
            Check if the PID file has been written.

            :returns: True if the PID file was written by this instance.
        """
        return self._pid_file_written

    # =========================================================================
    # PID File Handling
    # =========================================================================

    def write_pid_file(self) -> None:
        """
            Write the current process PID to the configured PID file.

            If no PID file path is configured, this method does nothing.
            If a PID file already exists with a running process, raises
            PidFileError to prevent duplicate instances.

            :raises PidFileError: If the PID file exists with a running
                process or if writing fails.
        """
        pid_path = self._config.pid_file
        if pid_path is None:
            return

        self._check_existing_pid_file(pid_path)

        try:
            pid = os.getpid()
            with open(pid_path, "w") as fh:
                fh.write(str(pid))
            self._pid_file_written = True
            _logger.info("PID file written: %s (pid=%d)", pid_path, pid)
        except OSError as err:
            errmsg = f"Failed to write PID file '{pid_path}': {err}"
            raise PidFileError(errmsg) from err

        return

    def cleanup_pid_file(self) -> None:
        """
            Remove the PID file if it was written by this instance.

            Silently ignores missing files since the file may have
            already been removed.
        """
        pid_path = self._config.pid_file
        if pid_path is None:
            return

        if not self._pid_file_written:
            return

        try:
            os.remove(pid_path)
            self._pid_file_written = False
            _logger.info("PID file removed: %s", pid_path)
        except FileNotFoundError:
            self._pid_file_written = False
            _logger.debug("PID file already removed: %s", pid_path)
        except OSError as err:
            _logger.warning("Failed to remove PID file '%s': %s", pid_path, err)

        return

    def read_pid_file(self) -> Optional[int]:
        """
            Read the PID from the configured PID file.

            :returns: The PID value or None if the file does not exist
                or cannot be read.
        """
        pid_path = self._config.pid_file
        if pid_path is None:
            return None

        rtnval = self._read_pid_from_file(pid_path)

        return rtnval

    def _check_existing_pid_file(self, pid_path: str) -> None:
        """
            Check if a PID file exists with a running process.

            :param pid_path: Path to the PID file.

            :raises PidFileError: If the PID file exists and the
                referenced process is still running.
        """
        existing_pid = self._read_pid_from_file(pid_path)
        if existing_pid is None:
            return

        if self._is_process_running(existing_pid):
            errmsg = (
                f"PID file '{pid_path}' exists with running process "
                f"(pid={existing_pid}). Refusing to start."
            )
            raise PidFileError(errmsg)

        _logger.warning(
            "Stale PID file found at '%s' (pid=%d is not running). Overwriting.",
            pid_path,
            existing_pid,
        )

        return

    @staticmethod
    def _read_pid_from_file(pid_path: str) -> Optional[int]:
        """
            Read and parse a PID value from a file.

            :param pid_path: Path to the PID file.

            :returns: The PID as an integer, or None if the file does
                not exist or contains invalid content.
        """
        rtnval = None

        try:
            with open(pid_path, "r") as fh:
                content = fh.read().strip()
            if content:
                rtnval = int(content)
        except FileNotFoundError:
            pass
        except (ValueError, OSError):
            _logger.warning("Invalid PID file content at '%s'", pid_path)

        return rtnval

    @staticmethod
    def _is_process_running(pid: int) -> bool:
        """
            Check if a process with the given PID is running.

            On POSIX, uses signal 0 to check process existence without
            actually sending a signal. On Windows ``os.kill(pid, 0)`` is
            not a probe, it terminates the target, so the process is
            queried through the Win32 API instead.

            :param pid: The process ID to check.

            :returns: True if the process is running.
        """
        if sys.platform == "win32":
            return ProcessManager._is_process_running_windows(pid)

        try:
            os.kill(pid, 0)
            rtnval = True
        except ProcessLookupError:
            rtnval = False
        except PermissionError:
            # Process exists but we lack permission to signal it
            rtnval = True

        return rtnval

    @staticmethod
    def _is_process_running_windows(pid: int) -> bool:
        """
            Check if a process with the given PID is running on Windows.

            Opens the process with the least privilege that allows its
            exit code to be read. A process that cannot be opened for
            lack of access still exists; one whose PID is unknown does
            not. An opened process is only considered running while its
            exit code reads as STILL_ACTIVE.

            :param pid: The process ID to check.

            :returns: True if the process is running.
        """
        import ctypes
        from ctypes import wintypes

        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        ERROR_ACCESS_DENIED = 5
        STILL_ACTIVE = 259

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenProcess.restype = wintypes.HANDLE
        kernel32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
        kernel32.GetExitCodeProcess.restype = wintypes.BOOL
        kernel32.GetExitCodeProcess.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
        kernel32.CloseHandle.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)

        handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            # Access denied means the process exists but is not ours to
            # inspect; any other failure means there is no such process.
            rtnval = ctypes.get_last_error() == ERROR_ACCESS_DENIED
            return rtnval

        try:
            exit_code = wintypes.DWORD()
            if kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                rtnval = exit_code.value == STILL_ACTIVE
            else:
                rtnval = True
        finally:
            kernel32.CloseHandle(handle)

        return rtnval

    # =========================================================================
    # Daemon Mode
    # =========================================================================

    def daemonize(self) -> None:
        """
            Daemonize the current process using the double-fork technique.

            After daemonization the process runs in the background with
            stdin, stdout, and stderr redirected to /dev/null.

            :raises DaemonError: If daemonization fails.
        """
        if not self._config.daemon:
            return

        try:
            self._double_fork()
            _logger.info("Process daemonized (pid=%d)", os.getpid())
        except OSError as err:
            errmsg = f"Failed to daemonize: {err}"
            raise DaemonError(errmsg) from err

        return

    def _double_fork(self) -> None:
        """
            Perform the double-fork daemonization sequence.

            First fork: detach from parent.
            setsid: become session leader.
            Second fork: prevent acquiring a controlling terminal.
            Redirect standard file descriptors to /dev/null.

            :raises OSError: If fork or setsid fails.
        """
        # First fork
        pid = os.fork()
        if pid > 0:
            # Parent exits
            os._exit(0)

        # Become session leader
        os.setsid()

        # Second fork
        pid = os.fork()
        if pid > 0:
            # First child exits
            os._exit(0)

        # Redirect standard file descriptors
        devnull = os.open(os.devnull, os.O_RDWR)
        os.dup2(devnull, sys.stdin.fileno())
        os.dup2(devnull, sys.stdout.fileno())
        os.dup2(devnull, sys.stderr.fileno())
        os.close(devnull)

        return

    # =========================================================================
    # Privilege Dropping
    # =========================================================================

    def drop_privileges(self) -> None:
        """
            Drop process privileges based on configuration.

            Applies umask, group, and user settings in the correct order.
            Group must be set before user to avoid losing permission to
            change the group.

            :raises PrivilegeError: If privilege operations fail.
        """
        self._apply_umask()
        self._apply_group()
        self._apply_user()

        return

    def _apply_umask(self) -> None:
        """
            Apply the configured umask value.

            Stores the original umask so it can be restored if needed.
        """
        if self._config.umask != 0:
            self._original_umask = os.umask(self._config.umask)
            _logger.info("Umask set to %04o", self._config.umask)

        return

    def _apply_group(self) -> None:
        """
            Change the process group to the configured group.

            :raises ConfigurationError: If a group is configured on a
                platform without the POSIX account database.
            :raises PrivilegeError: If the group does not exist or
                the operation fails.
        """
        group_name = self._config.group
        if group_name is None:
            return

        if grp is None:
            errmsg = (
                f"Cannot apply group '{group_name}': POSIX group lookup is not "
                f"available on platform '{sys.platform}'. Remove the 'group' "
                "setting from the server configuration on this platform."
            )
            raise ConfigurationError(errmsg)

        try:
            group_info = grp.getgrnam(group_name)
            os.setgid(group_info.gr_gid)
            _logger.info("Process group set to '%s' (gid=%d)", group_name, group_info.gr_gid)
        except KeyError:
            errmsg = f"Group '{group_name}' does not exist"
            raise PrivilegeError(errmsg)
        except OSError as err:
            errmsg = f"Failed to set group to '{group_name}': {err}"
            raise PrivilegeError(errmsg) from err

        return

    def _apply_user(self) -> None:
        """
            Change the process user to the configured user.

            Also sets supplementary groups and initializes the
            user's group access list.

            :raises ConfigurationError: If a user is configured on a
                platform without the POSIX account database.
            :raises PrivilegeError: If the user does not exist or
                the operation fails.
        """
        user_name = self._config.user
        if user_name is None:
            return

        if pwd is None:
            errmsg = (
                f"Cannot apply user '{user_name}': POSIX user lookup is not "
                f"available on platform '{sys.platform}'. Remove the 'user' "
                "setting from the server configuration on this platform."
            )
            raise ConfigurationError(errmsg)

        try:
            user_info = pwd.getpwnam(user_name)
            # Initialize supplementary groups before dropping to user
            try:
                os.initgroups(user_name, user_info.pw_gid)
            except PermissionError:
                _logger.debug("Cannot set supplementary groups (not root)")
            os.setuid(user_info.pw_uid)
            _logger.info("Process user set to '%s' (uid=%d)", user_name, user_info.pw_uid)
        except KeyError:
            errmsg = f"User '{user_name}' does not exist"
            raise PrivilegeError(errmsg)
        except OSError as err:
            errmsg = f"Failed to set user to '{user_name}': {err}"
            raise PrivilegeError(errmsg) from err

        return

    # =========================================================================
    # Working Directory
    # =========================================================================

    def change_directory(self) -> None:
        """
            Change the working directory to the configured path.

            Stores the original directory so it can be restored if needed.

            :raises ProcessManagerError: If the directory does not exist
                or the change fails.
        """
        target_dir = self._config.chdir
        if target_dir is None:
            return

        self._original_dir = os.getcwd()

        if not os.path.isdir(target_dir):
            errmsg = f"Working directory '{target_dir}' does not exist"
            raise ProcessManagerError(errmsg)

        try:
            os.chdir(target_dir)
            _logger.info("Working directory changed to '%s'", target_dir)
        except OSError as err:
            errmsg = f"Failed to change directory to '{target_dir}': {err}"
            raise ProcessManagerError(errmsg) from err

        return

    def restore_directory(self) -> None:
        """
            Restore the original working directory.

            Does nothing if the directory was not changed or the
            original directory is no longer accessible.
        """
        if self._original_dir is None:
            return

        try:
            os.chdir(self._original_dir)
            _logger.info("Working directory restored to '%s'", self._original_dir)
            self._original_dir = None
        except OSError as err:
            _logger.warning(
                "Failed to restore working directory to '%s': %s",
                self._original_dir,
                err,
            )

        return

    # =========================================================================
    # Status
    # =========================================================================

    def get_status(self) -> Dict[str, Any]:
        """
            Get the current process management status.

            :returns: Dictionary with process management state.
        """
        rtnval: Dict[str, Any] = {
            "pid": os.getpid(),
            "pid_file": self._config.pid_file,
            "pid_file_written": self._pid_file_written,
            "daemon": self._config.daemon,
            "user": self._config.user,
            "group": self._config.group,
            "umask": self._config.umask,
            "chdir": self._config.chdir,
            "working_directory": os.getcwd(),
        }

        return rtnval
