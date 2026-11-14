"""
    Auto-reload supervisor for the development server.

    Reloading code inside a running interpreter is unreliable: modules
    that were already imported keep their old objects, and state built at
    import time survives. The supervisor therefore never serves requests
    itself. It runs the server in a child process and, when a watched file
    changes, stops that process and starts a fresh one, which imports the
    application code from scratch. This is the model used by the reloaders
    of werkzeug and uvicorn.

    The child process is started by re-running the command that started
    the current process, with :data:`RELOAD_CHILD_ENV` set in its
    environment. A process that finds the marker set serves requests
    directly instead of supervising.
"""

import logging
import os
import signal
import subprocess
import sys
import threading

from typing import Dict, List, Optional

from ccai.webworks.devexp.server.filewatcher import FileWatcher


logger = logging.getLogger(__name__)


RELOAD_CHILD_ENV = "WEBWORKS_RELOAD_CHILD"
"""Environment variable set to ``1`` in the server process the supervisor starts."""

SUPERVISOR_POLL_SECONDS: float = 0.2
"""Seconds between checks of the child process while no restart is requested."""

DEFAULT_CHILD_STOP_TIMEOUT_SECONDS: float = 10.0
"""Seconds a child process is given to shut down before it is killed."""


class ReloadNotSupportedError(Exception):
    """
        Raised when the command that started this process cannot be re-run.

        Auto-reload restarts the server by running the same command again,
        which needs a script file, a ``python -m`` module or a console
        script. An interactive session or ``python -c`` has none of these.
    """


class ReloadChildError(Exception):
    """
        Records that the server process ended on its own with an error.

        The usual cause is application code that fails while it is imported
        (a ``SyntaxError`` or ``ImportError`` in the file that was just
        saved). The supervisor keeps watching and starts a new process at
        the next file change.
    """

    def __init__(self, return_code: int):
        """
            Construct a ReloadChildError.

            :param return_code: The exit code of the server process.
        """
        self._return_code = return_code
        message = "The server process exited with code {}.".format(return_code)
        super().__init__(message)
        return

    @property
    def return_code(self) -> int:
        """
            The exit code of the server process.

            :returns: The exit code.
        """
        return self._return_code


def is_reload_child() -> bool:
    """
        Whether this process is a server process started by a supervisor.

        :returns: ``True`` if the reload marker is set in the environment.
    """
    is_child = os.environ.get(RELOAD_CHILD_ENV, "") == "1"
    return is_child


def get_reload_command() -> List[str]:
    """
        Build the command that re-runs the current process.

        Handles the three ways a server is normally started: a script
        (``python app.py``), a module (``python -m package``) and a console
        script (``webworks serve``).

        :returns: The command as an argument list.

        :raises ReloadNotSupportedError: If the current process was not
            started from a file or module that can be run again.
    """
    import __main__

    command = [sys.executable]
    arguments = list(sys.argv[1:])

    main_spec = getattr(__main__, "__spec__", None)

    if main_spec is not None and main_spec.name:
        # Started with 'python -m <module>'.
        module_name = main_spec.name
        main_suffix = ".__main__"

        if module_name.endswith(main_suffix):
            module_name = module_name[:-len(main_suffix)]

        command.extend(["-m", module_name])
    else:
        script = sys.argv[0] if len(sys.argv) > 0 else ""
        script_path = os.path.abspath(script)

        if len(script) > 0 and os.path.isfile(script_path):
            command.append(script_path)
        elif len(script) > 0 and os.path.isfile(script_path + ".exe"):
            # A console script on Windows is an executable launcher, not a
            # Python file; it is run directly.
            command = [script_path + ".exe"]
        else:
            errmsg = (
                "Auto-reload restarts the server by re-running the command that started it, "
                "but this process was not started from a script, a module or a console script "
                "(sys.argv[0] is {!r}). Start the server from a file, or disable reload.".format(script)
            )
            raise ReloadNotSupportedError(errmsg)

    command.extend(arguments)

    return command


class ReloadSupervisor:
    """
        Runs the server in a child process and restarts it on file changes.

        Restart requests are handled one at a time by the supervising
        loop. Requests that arrive while a restart is in progress are
        coalesced into a single further restart, so two saves in quick
        succession cannot start two servers on one port.

        :param command: The command that starts the server process.
        :param watch_patterns: Glob patterns of the files to watch.
        :param exclude_patterns: Patterns of files and directories to ignore.
        :param base_directory: The directory to watch. Defaults to the
            current working directory.
        :param poll_interval: Seconds between file system polls. ``None``
            uses the file watcher's default.
        :param child_stop_timeout: Seconds a server process is given to
            shut down before it is killed.
    """

    def __init__(
        self,
        command: List[str],
        watch_patterns: List[str],
        exclude_patterns: List[str],
        base_directory: Optional[str] = None,
        poll_interval: Optional[float] = None,
        child_stop_timeout: float = DEFAULT_CHILD_STOP_TIMEOUT_SECONDS,
    ):
        """
            Construct a ReloadSupervisor.

            :param command: The command that starts the server process.
            :param watch_patterns: Glob patterns of the files to watch.
            :param exclude_patterns: Patterns of files and directories to ignore.
            :param base_directory: The directory to watch.
            :param poll_interval: Seconds between file system polls.
            :param child_stop_timeout: Seconds to wait for a server process
                to shut down before killing it.
        """
        self._command = list(command)
        self._watch_patterns = list(watch_patterns)
        self._exclude_patterns = list(exclude_patterns)
        self._base_directory = base_directory
        self._poll_interval = poll_interval
        self._child_stop_timeout = child_stop_timeout

        self._child: Optional[subprocess.Popen] = None
        self._watcher: Optional[FileWatcher] = None
        self._restart_event = threading.Event()
        self._stop_event = threading.Event()
        self._restart_count: int = 0
        self._last_error: Optional[Exception] = None
        self._running: bool = False

        return

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def command(self) -> List[str]:
        """
            The command that starts the server process.

            :returns: A copy of the argument list.
        """
        return list(self._command)

    @property
    def restart_count(self) -> int:
        """
            The number of times the server process was restarted because a
            watched file changed.

            :returns: The restart count.
        """
        return self._restart_count

    @property
    def last_error(self) -> Optional[Exception]:
        """
            The error of the most recent server process that ended on its
            own, or ``None`` when the current process is healthy.

            :returns: A :class:`ReloadChildError` or ``None``.
        """
        return self._last_error

    @property
    def running(self) -> bool:
        """
            Whether the supervising loop is running.

            :returns: ``True`` while :meth:`run` is active.
        """
        return self._running

    @property
    def watcher(self) -> Optional[FileWatcher]:
        """
            The file watcher, while the supervisor is running.

            :returns: The :class:`FileWatcher` or ``None``.
        """
        return self._watcher

    @property
    def child_pid(self) -> Optional[int]:
        """
            The process ID of the current server process.

            :returns: The PID, or ``None`` when no server process is running.
        """
        pid = None

        if self._child is not None:
            pid = self._child.pid

        return pid

    # -------------------------------------------------------------------------
    # Control
    # -------------------------------------------------------------------------

    def request_restart(self) -> None:
        """
            Ask the supervisor to restart the server process.

            Safe to call from any thread; this is the file watcher's
            callback. Requests made before the supervisor acts on them
            collapse into one restart.
        """
        self._restart_event.set()
        return

    def stop(self) -> None:
        """
            Ask the supervisor to stop the server process and return.

            Safe to call from any thread.
        """
        self._stop_event.set()
        # Wake the supervising loop at once.
        self._restart_event.set()
        return

    def run(self) -> int:
        """
            Supervise the server process until it is stopped.

            Starts the file watcher and the server process, then waits. A
            file change restarts the server process. A server process that
            ends with an error is not restarted until the next file change,
            so a syntax error in the file being edited does not end the
            session. A server process that ends cleanly (it was told to
            shut down) ends the supervisor.

            :returns: The exit code of the last server process that ended on
                its own, or ``0``.
        """
        self._stop_event.clear()
        self._restart_event.clear()
        self._running = True

        exit_code = 0
        previous_sigterm = self._install_sigterm_handler()

        watcher_arguments: Dict[str, object] = {
            "patterns": self._watch_patterns,
            "excludes": self._exclude_patterns,
            "callback": self.request_restart,
        }

        if self._base_directory is not None:
            watcher_arguments["base_directory"] = self._base_directory

        if self._poll_interval is not None:
            watcher_arguments["poll_interval"] = self._poll_interval

        self._watcher = FileWatcher(**watcher_arguments)

        try:
            self._watcher.start()
            self._spawn_child()

            while not self._stop_event.is_set():
                restart_requested = self._restart_event.wait(timeout=SUPERVISOR_POLL_SECONDS)

                if self._stop_event.is_set():
                    break

                if restart_requested:
                    self._restart_event.clear()

                    logger.info("File change detected. Restarting the server process...")

                    self._stop_child()
                    self._spawn_child()

                    self._restart_count += 1
                    self._last_error = None

                    logger.info(
                        "Server process restarted (restart #%d).",
                        self._restart_count,
                    )
                    continue

                if self._child is not None:
                    return_code = self._child.poll()

                    if return_code is not None:
                        self._child = None

                        if return_code == 0:
                            # The server shut down on request.
                            exit_code = 0
                            break

                        exit_code = return_code
                        self._last_error = ReloadChildError(return_code)

                        logger.error(
                            "The server process exited with code %d. "
                            "Watching for file changes to retry...",
                            return_code,
                        )
        except KeyboardInterrupt:
            logger.info("Interrupted. Stopping the server process.")
            exit_code = 0
        finally:
            self._stop_child()

            if self._watcher is not None:
                self._watcher.stop()
                self._watcher = None

            self._restore_sigterm_handler(previous_sigterm)
            self._running = False

        return exit_code

    # -------------------------------------------------------------------------
    # Child Process Management
    # -------------------------------------------------------------------------

    def _spawn_child(self) -> None:
        """
            Start a new server process with the reload marker set.
        """
        child_env = dict(os.environ)
        child_env[RELOAD_CHILD_ENV] = "1"

        self._child = subprocess.Popen(self._command, env=child_env)

        logger.debug(
            "Started server process %d: %s",
            self._child.pid,
            " ".join(self._command),
        )

        return

    def _stop_child(self) -> None:
        """
            Stop the current server process, if there is one.

            The process is asked to terminate so it can shut down
            gracefully, and is killed if it has not ended within the stop
            timeout.
        """
        child = self._child

        if child is None:
            return

        self._child = None

        if child.poll() is None:
            child.terminate()

            try:
                child.wait(timeout=self._child_stop_timeout)
            except subprocess.TimeoutExpired:
                logger.warning(
                    "Server process %d did not stop within %s seconds. Killing it.",
                    child.pid,
                    self._child_stop_timeout,
                )
                child.kill()
                child.wait()

        return

    # -------------------------------------------------------------------------
    # Signal Handling
    # -------------------------------------------------------------------------

    def _install_sigterm_handler(self) -> Optional[object]:
        """
            Make SIGTERM stop the supervisor and its server process.

            Signal handlers can only be installed from the main thread; from
            any other thread the supervisor is stopped with :meth:`stop`.

            :returns: The previous handler, or ``None`` if none was installed.
        """
        previous = None

        if threading.current_thread() is threading.main_thread():
            def _on_sigterm(signum: int, frame: object) -> None:
                self.stop()
                return

            try:
                previous = signal.signal(signal.SIGTERM, _on_sigterm)
            except (ValueError, OSError):
                # The platform or the embedding does not allow a handler here.
                previous = None

        return previous

    def _restore_sigterm_handler(self, previous: Optional[object]) -> None:
        """
            Put back the SIGTERM handler that was active before :meth:`run`.

            :param previous: The value returned by :meth:`_install_sigterm_handler`.
        """
        if previous is not None:
            try:
                signal.signal(signal.SIGTERM, previous)
            except (ValueError, OSError):
                # Restoring is best effort; the process is on its way out.
                pass

        return
