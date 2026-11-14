"""
    Tests for the auto-reload supervisor.

    This module contains unit tests for the :class:`ReloadSupervisor`,
    which runs the server in a child process and replaces it when a
    watched file changes, and an end-to-end test that edits an
    application file under a reloading server and checks that the new
    code is the code that answers.
"""

import http.client
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time

from ccai.webworks.devexp.server.reloader import RELOAD_CHILD_ENV
from ccai.webworks.devexp.server.reloader import ReloadChildError
from ccai.webworks.devexp.server.reloader import ReloadSupervisor
from ccai.webworks.devexp.server.reloader import is_reload_child


# =============================================================================
# Test Helpers
# =============================================================================

_IDLE_CHILD = "import time; time.sleep(120)"
"""Child process code that stays alive like a healthy server."""

_MARKER_CHILD = (
    "import os, sys, time; "
    "open(sys.argv[1], 'a').write(os.environ.get('WEBWORKS_RELOAD_CHILD', '') + '\\n'); "
    "time.sleep(120)"
)
"""Child process code that records the reload marker it was started with."""


def _wait_until(predicate, timeout=20.0):
    """
        Poll a condition until it holds or the timeout expires.

        :returns: True if the condition held in time.
    """
    deadline = time.time() + timeout

    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(0.05)

    return predicate()


class _RunningSupervisor:
    """
        Runs a ReloadSupervisor in a thread over an empty watch directory.
    """

    def __init__(self, command):
        self.watch_dir = tempfile.mkdtemp()

        self.supervisor = ReloadSupervisor(
            command=command,
            watch_patterns=["**/*.py"],
            exclude_patterns=[],
            base_directory=self.watch_dir,
            poll_interval=0.2,
        )

        self.exit_codes = []
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        self.exit_codes.append(self.supervisor.run())

    def close(self):
        self.supervisor.stop()
        self.thread.join(timeout=20.0)
        shutil.rmtree(self.watch_dir, ignore_errors=True)


def _free_port():
    """
        Return a port number that is free on the loopback interface.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()

    return port


def _http_get(port, path="/"):
    """
        Request a path from a local server.

        :returns: The response body, or None if the server is not reachable.
    """
    body = None

    try:
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
        connection.request("GET", path, headers={"Connection": "close"})
        response = connection.getresponse()
        body = response.read()
        connection.close()
    except OSError:
        body = None

    return body


# =============================================================================
# Unit Tests for the Reload Marker
# =============================================================================

def test_is_reload_child_reads_the_environment_marker():
    """
        Test that a process is a reload child only when the marker is set.
    """
    previous = os.environ.pop(RELOAD_CHILD_ENV, None)

    try:
        if is_reload_child() is not False:
            raise AssertionError("Expected is_reload_child() to be False without the marker.")

        os.environ[RELOAD_CHILD_ENV] = "1"

        if is_reload_child() is not True:
            raise AssertionError("Expected is_reload_child() to be True with the marker set.")
    finally:
        os.environ.pop(RELOAD_CHILD_ENV, None)
        if previous is not None:
            os.environ[RELOAD_CHILD_ENV] = previous

    return


def test_supervisor_starts_child_with_reload_marker():
    """
        Test that the server process is started with the reload marker in
        its environment, so it serves instead of supervising.
    """
    marker_dir = tempfile.mkdtemp()
    marker_file = os.path.join(marker_dir, "marker.txt")

    running = _RunningSupervisor([sys.executable, "-c", _MARKER_CHILD, marker_file])

    try:
        if not _wait_until(lambda: os.path.isfile(marker_file) and os.path.getsize(marker_file) > 0):
            raise AssertionError("Expected the server process to start and write its marker.")

        with open(marker_file) as handle:
            recorded = handle.read().strip()

        if recorded != "1":
            errmsg = "Expected the reload marker '1' in the child environment, got '{}'".format(recorded)
            raise AssertionError(errmsg)
    finally:
        running.close()
        shutil.rmtree(marker_dir, ignore_errors=True)

    return


# =============================================================================
# Unit Tests for Restarts
# =============================================================================

def test_restart_request_replaces_the_server_process():
    """
        Test that a restart request stops the server process and starts
        a new one.
    """
    running = _RunningSupervisor([sys.executable, "-c", _IDLE_CHILD])

    try:
        if not _wait_until(lambda: running.supervisor.child_pid is not None):
            raise AssertionError("Expected the supervisor to start a server process.")

        first_pid = running.supervisor.child_pid

        running.supervisor.request_restart()

        if not _wait_until(lambda: running.supervisor.restart_count == 1):
            errmsg = "Expected restart_count 1, got {}".format(running.supervisor.restart_count)
            raise AssertionError(errmsg)

        if not _wait_until(lambda: running.supervisor.child_pid not in (None, first_pid)):
            raise AssertionError("Expected a different server process after the restart.")
    finally:
        running.close()

    return


def test_file_change_restarts_the_server_process():
    """
        Test that changing a watched file restarts the server process.
    """
    running = _RunningSupervisor([sys.executable, "-c", _IDLE_CHILD])

    try:
        if not _wait_until(lambda: running.supervisor.child_pid is not None):
            raise AssertionError("Expected the supervisor to start a server process.")

        with open(os.path.join(running.watch_dir, "edited.py"), "w") as handle:
            handle.write("VALUE = 1\n")

        if not _wait_until(lambda: running.supervisor.restart_count >= 1):
            raise AssertionError("Expected a restart after a watched file was created.")
    finally:
        running.close()

    return


def test_simultaneous_restart_requests_are_coalesced():
    """
        Test that a burst of restart requests does not start a server
        process per request.
    """
    running = _RunningSupervisor([sys.executable, "-c", _IDLE_CHILD])

    try:
        if not _wait_until(lambda: running.supervisor.child_pid is not None):
            raise AssertionError("Expected the supervisor to start a server process.")

        for _ in range(10):
            running.supervisor.request_restart()

        if not _wait_until(lambda: running.supervisor.restart_count >= 1):
            raise AssertionError("Expected at least one restart.")

        # Give any (wrongly) queued restarts the time to happen.
        time.sleep(1.0)

        if running.supervisor.restart_count > 2:
            errmsg = "Expected the 10 requests to collapse into at most 2 restarts, got {}".format(
                running.supervisor.restart_count
            )
            raise AssertionError(errmsg)
    finally:
        running.close()

    return


def test_failed_server_process_is_recorded_and_supervision_continues():
    """
        Test that a server process that exits with an error is recorded
        and that the next restart request starts a new process.
    """
    running = _RunningSupervisor([sys.executable, "-c", "import sys; sys.exit(3)"])

    try:
        if not _wait_until(lambda: running.supervisor.last_error is not None):
            raise AssertionError("Expected the failed server process to be recorded.")

        error = running.supervisor.last_error

        if not isinstance(error, ReloadChildError) or error.return_code != 3:
            errmsg = "Expected ReloadChildError with exit code 3, got {!r}".format(error)
            raise AssertionError(errmsg)

        if running.supervisor.running is not True:
            raise AssertionError("Expected the supervisor to keep running after a failed process.")

        running.supervisor.request_restart()

        if not _wait_until(lambda: running.supervisor.restart_count == 1):
            raise AssertionError("Expected a restart request to start a new process after a failure.")
    finally:
        running.close()

    return


def test_stop_ends_the_server_process_and_the_watcher():
    """
        Test that stopping the supervisor terminates the server process,
        stops the file watcher and makes run() return.
    """
    running = _RunningSupervisor([sys.executable, "-c", _IDLE_CHILD])

    try:
        if not _wait_until(lambda: running.supervisor.child_pid is not None):
            raise AssertionError("Expected the supervisor to start a server process.")
    finally:
        running.close()

    if running.thread.is_alive():
        raise AssertionError("Expected run() to return after stop().")

    if running.supervisor.child_pid is not None:
        raise AssertionError("Expected no server process after stop().")

    if running.supervisor.watcher is not None:
        raise AssertionError("Expected the file watcher to be stopped after stop().")

    if running.supervisor.running is not False:
        raise AssertionError("Expected running to be False after stop().")

    return


def test_clean_exit_of_server_process_ends_supervision():
    """
        Test that a server process that shuts down cleanly ends the
        supervisor with exit code 0.
    """
    running = _RunningSupervisor([sys.executable, "-c", "pass"])

    try:
        running.thread.join(timeout=20.0)

        if running.thread.is_alive():
            raise AssertionError("Expected run() to return after the server process exited cleanly.")

        if running.exit_codes != [0]:
            errmsg = "Expected exit code [0], got {}".format(running.exit_codes)
            raise AssertionError(errmsg)
    finally:
        running.close()

    return


# =============================================================================
# End-to-End Test: Edited Code Is Served
# =============================================================================

_APP_SOURCE = '''
VERSION = "{version}"


async def app(scope, receive, send):
    if scope["type"] != "http":
        return

    await receive()
    await send({{"type": "http.response.start", "status": 200, "headers": [(b"content-type", b"text/plain")]}})
    await send({{"type": "http.response.body", "body": VERSION.encode("ascii")}})
'''


def test_reload_serves_the_edited_application_code():
    """
        Test that editing the application file under 'serve --reload'
        makes the server answer with the new code.

        Requirements: 10.2
    """
    project_dir = tempfile.mkdtemp()
    app_file = os.path.join(project_dir, "app.py")

    with open(app_file, "w") as handle:
        handle.write(_APP_SOURCE.format(version="first"))

    port = _free_port()

    process = subprocess.Popen(
        [
            sys.executable, "-m", "ccai.webworks.devexp.cli",
            "serve", "--reload", "--port", str(port), "--log-level", "WARNING",
        ],
        cwd=project_dir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        if not _wait_until(lambda: _http_get(port) == b"first", timeout=30.0):
            raise AssertionError("Expected the server to answer with the original code.")

        # The watcher compares modification times; make sure the edit
        # gets a later one even on a coarse file system clock.
        time.sleep(1.1)

        with open(app_file, "w") as handle:
            handle.write(_APP_SOURCE.format(version="second"))

        if not _wait_until(lambda: _http_get(port) == b"second", timeout=30.0):
            errmsg = "Expected the server to answer with the edited code, got {!r}".format(_http_get(port))
            raise AssertionError(errmsg)
    finally:
        process.terminate()

        try:
            process.wait(timeout=20.0)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

        shutil.rmtree(project_dir, ignore_errors=True)

    return
