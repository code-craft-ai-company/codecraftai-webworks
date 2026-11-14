"""
    Run a server in a child process for a test and talk to it over a socket.

    The server tests start real servers: they bind a port, fork workers and
    install signal handlers, so they run in a child process of their own and
    the test talks to them with http.client. ServerProcess starts the child,
    waits until the port accepts connections (no fixed sleeps), and always
    stops it, by its pid, when the test is done.

    Ports come from 18100-18199, the range the server tests use.
"""

import http.client
import os
import shutil
import signal
import socket
import ssl
import subprocess
import sys
import tempfile
import time

from typing import Dict, List, Optional, Tuple


PORT_RANGE_START = 18100
PORT_RANGE_END = 18199

DEFAULT_READY_TIMEOUT = 60.0
DEFAULT_STOP_TIMEOUT = 45.0

_this_dir = os.path.dirname(os.path.abspath(__file__))
# testshared/servers -> testshared -> ccai -> testroots -> source
_source_dir = os.path.normpath(os.path.join(_this_dir, os.pardir, os.pardir, os.pardir, os.pardir))
TESTROOTS_DIR = os.path.join(_source_dir, "testroots")
PACKAGES_DIR = os.path.join(_source_dir, "packages")
TESTSITES_DIR = os.path.join(_source_dir, "testsites")

_next_port = PORT_RANGE_START


def find_free_port() -> int:
    """
        Find a port in 18100-18199 that nothing listens on.

        The ports are handed out in turn, so two servers started one after
        the other in a test get different ports even if the first one has not
        released its port yet.

        :returns: The port.

        :raises AssertionError: If every port of the range is taken.
    """
    global _next_port

    for _ in range(PORT_RANGE_END - PORT_RANGE_START + 1):
        port = _next_port
        _next_port += 1
        if _next_port > PORT_RANGE_END:
            _next_port = PORT_RANGE_START

        probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            probe.bind(("127.0.0.1", port))
            return port
        except OSError:
            continue
        finally:
            probe.close()

    errmsg = f"No free port in {PORT_RANGE_START}-{PORT_RANGE_END}."
    raise AssertionError(errmsg)


def child_environment(extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """
        Build the environment of a server child process.

        :param extra: Variables to add.

        :returns: The environment, with the test roots, the packages and the
            test sites importable.
    """
    env = dict(os.environ)

    python_path_entries = [TESTROOTS_DIR, PACKAGES_DIR, TESTSITES_DIR]
    existing = env.get("PYTHONPATH")
    if existing:
        python_path_entries.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(python_path_entries)
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    if extra is not None:
        env.update(extra)

    return env


class ServerProcess:
    """
        A server running in a child process.

        Use it as a context manager, so the server is stopped however the
        test ends::

            with ServerProcess(code, port) as server:
                status, headers, body = server.request("GET", "/hello")
    """

    def __init__(
        self,
        code: str,
        port: int,
        args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
        use_tls: bool = False,
        ready_timeout: float = DEFAULT_READY_TIMEOUT,
    ):
        """
            Describe the server to run.

            :param code: Python code the child runs with ``python -c``.
            :param port: The port the server listens on.
            :param args: Arguments passed to the code (sys.argv[1:]).
            :param env: Extra environment variables.
            :param use_tls: True if the server speaks TLS.
            :param ready_timeout: Seconds to wait for the port to accept.
        """
        self.code = code
        self.port = port
        self.args = list(args or [])
        self.env = child_environment(env)
        self.use_tls = use_tls
        self.ready_timeout = ready_timeout
        self.process: Optional[subprocess.Popen] = None
        self.returncode: Optional[int] = None
        # The log directory is created when the server is started
        self._log_dir: Optional[str] = None
        self.log_path: Optional[str] = None
        self._log_file = None
        self._final_output: Optional[str] = None
        return

    def __enter__(self) -> "ServerProcess":
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.stop()
        return

    @property
    def pid(self) -> int:
        """
            :returns: The pid of the server's master process.
        """
        return self.process.pid

    def start(self) -> None:
        """
            Start the child and wait until the server accepts connections.

            :raises AssertionError: If the child ends or the port does not
                accept connections within the ready timeout.
        """
        self._log_dir = tempfile.mkdtemp(prefix="webworks-server-test-")
        self.log_path = os.path.join(self._log_dir, "server.log")
        self._log_file = open(self.log_path, "w", encoding="utf-8")
        self.process = subprocess.Popen(
            [sys.executable, "-c", self.code] + self.args,
            env=self.env,
            stdout=self._log_file,
            stderr=subprocess.STDOUT,
        )

        started = False
        try:
            self.wait_until_ready()
            started = True
        finally:
            if not started:
                self.stop()

        return

    def wait_until_ready(self) -> None:
        """
            Poll the port until it accepts a connection.

            :raises AssertionError: If the child ends first, or the timeout passes.
        """
        deadline = time.monotonic() + self.ready_timeout

        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                errmsg = (
                    f"The server process ended with {self.process.returncode} before it "
                    f"accepted connections. Output:\n{self.output()}"
                )
                raise AssertionError(errmsg)

            try:
                probe = socket.create_connection(("127.0.0.1", self.port), timeout=1.0)
                probe.close()
                return
            except OSError:
                time.sleep(0.05)

        errmsg = f"The server did not accept connections on port {self.port} within {self.ready_timeout} seconds. Output:\n{self.output()}"
        raise AssertionError(errmsg)

    def stop(self, signum: int = signal.SIGTERM, timeout: float = DEFAULT_STOP_TIMEOUT) -> Optional[int]:
        """
            Stop the server and wait for it to end.

            :param signum: The signal to stop it with.
            :param timeout: Seconds to wait before it is killed.

            :returns: The exit code of the master process.
        """
        if self.process is None:
            return None

        if self.process.poll() is None:
            self.process.send_signal(signum)
            try:
                self.process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=10)

        self.returncode = self.process.returncode

        if self._log_file is not None:
            self._log_file.close()
            self._log_file = None

        # The output stays readable after the log directory is removed
        if self._final_output is None:
            self._final_output = self.output()
            shutil.rmtree(self._log_dir, ignore_errors=True)

        return self.returncode

    def wait_for_exit(self, timeout: float = DEFAULT_STOP_TIMEOUT) -> int:
        """
            Wait for the server to end by itself.

            :param timeout: Seconds to wait.

            :returns: The exit code.

            :raises AssertionError: If it does not end in time; it is stopped then.
        """
        try:
            self.returncode = self.process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            self.stop()
            errmsg = f"The server did not end within {timeout} seconds. Output:\n{self.output()}"
            raise AssertionError(errmsg)
        return self.returncode

    def output(self) -> str:
        """
            :returns: What the server process wrote so far.
        """
        if self._final_output is not None:
            return self._final_output

        if self.log_path is None:
            return ""

        if self._log_file is not None:
            self._log_file.flush()
        try:
            with open(self.log_path, "r", encoding="utf-8", errors="replace") as log_file:
                rtnval = log_file.read()
        except FileNotFoundError:
            rtnval = ""
        return rtnval

    def connection(self, timeout: float = 10.0) -> http.client.HTTPConnection:
        """
            Open a connection to the server.

            :param timeout: Socket timeout in seconds.

            :returns: An HTTP or HTTPS connection; HTTPS does not verify the
                server's certificate (the tests use a self-signed one).
        """
        if self.use_tls:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            rtnval = http.client.HTTPSConnection("127.0.0.1", self.port, timeout=timeout, context=context)
        else:
            rtnval = http.client.HTTPConnection("127.0.0.1", self.port, timeout=timeout)
        return rtnval

    def request(
        self,
        method: str,
        path: str,
        body: Optional[bytes] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 10.0,
    ) -> Tuple[int, http.client.HTTPMessage, bytes]:
        """
            Make one request on a new connection.

            :param method: HTTP method.
            :param path: Request target.
            :param body: Request body.
            :param headers: Request headers.
            :param timeout: Socket timeout in seconds.

            :returns: Status, headers and body of the response.
        """
        connection = self.connection(timeout=timeout)
        try:
            connection.request(method, path, body=body, headers=headers or {})
            response = connection.getresponse()
            response_body = response.read()
            rtnval = (response.status, response.headers, response_body)
        finally:
            connection.close()
        return rtnval
