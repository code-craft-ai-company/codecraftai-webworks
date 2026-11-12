"""
    Worker manager module for the WSGI layer.
    
    This module provides the WorkerManager class for managing worker processes
    in the built-in WSGI server. The manager handles spawning, monitoring,
    and graceful shutdown of worker processes.
"""

import logging
import multiprocessing
import os
import signal
import sys
import time
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Optional

from ccai.webworks.wsgi.constants import WORKER_BOOT_ERROR_EXIT_CODE
from ccai.webworks.wsgi.exceptions import WorkerBootError
from ccai.webworks.wsgi.serverconfig import ServerConfig
from ccai.webworks.wsgi.socketlistener import SocketListener
from ccai.webworks.wsgi.worker import Worker


# Default logger for worker manager
_logger = logging.getLogger("webworks.wsgi.workermanager")

# Exit code of a worker process that ended with an error while serving
_WORKER_ERROR_EXIT_CODE = 1

# Callable told about every worker process that ended: (pid, worker_id, exit_code).
# The exit code is None when the process was ended by a signal.
WorkerExitCallback = Callable[[int, int, Optional[int]], None]


def prepare_worker_process(config: ServerConfig) -> None:
    """
        Prepare a new worker process before its Worker is created.
        
        For the gevent worker class the standard library is patched for
        cooperative I/O here, before anything in the worker creates threads,
        sockets or locks. The handler threads of the worker then run as
        greenlets.
        
        :param config: The server configuration.
    """
    if config.worker_class == "gevent":
        from gevent import monkey
        monkey.patch_all()
    
    return


def _report_worker_end(worker_id: int, exit_code: int) -> int:
    """
        Decide the exit code of a worker process from how it ended.
        
        Called in the 'finally' of a forked worker process, which must end
        with os._exit and never return into the code of the server it was
        forked from. An exception that is not an Exception (a
        ConfigurationError or SemanticError of the application) is printed
        with its traceback and ends the worker as a failed boot, so the
        server stops instead of starting workers that fail the same way.
        
        :param worker_id: ID of the worker.
        :param exit_code: The exit code decided so far.
        
        :returns: The exit code to end the process with.
    """
    passing_error = sys.exc_info()[1]
    
    if passing_error is not None and not isinstance(passing_error, Exception):
        sys.stderr.write(f"Worker {worker_id} ended with {type(passing_error).__name__}:\n")
        traceback.print_exception(type(passing_error), passing_error, passing_error.__traceback__)
        sys.stderr.flush()
        exit_code = WORKER_BOOT_ERROR_EXIT_CODE
    
    return exit_code


@dataclass
class WorkerInfo:
    """
        Information about a worker process.
    """
    pid: int
    worker_id: int
    start_time: float
    last_heartbeat: float = field(default_factory=time.time)
    request_count: int = 0
    is_alive: bool = True


class WorkerManager:
    """
        Manager for worker processes.
        
        This class handles spawning, monitoring, and graceful shutdown of
        worker processes for the built-in WSGI server. It supports both
        fork (Unix) and spawn (Windows/macOS) process creation methods.
    """
    
    def __init__(
        self,
        app: Callable[[Dict[str, Any], Callable], Iterable[bytes]],
        listener: SocketListener,
        config: Optional[ServerConfig] = None,
        exit_callback: Optional[WorkerExitCallback] = None
    ):
        """
            Construct a worker manager.
            
            :param app: The WSGI application callable.
            :param listener: The socket listener for accepting connections.
            :param config: Server configuration. If None, uses defaults.
            :param exit_callback: Called in this process for every worker
                                  process that ended, with its pid, worker id
                                  and exit code.
        """
        self._app = app
        self._listener = listener
        self._exit_callback = exit_callback
        
        # Set when a worker could not start serving. No replacement is
        # started then, it would fail the same way; the server stops.
        self._boot_failed = False
        
        if config is not None:
            self._config = config
        else:
            self._config = ServerConfig()
        
        # Worker tracking: pid -> WorkerInfo
        self._workers: Dict[int, WorkerInfo] = {}
        self._next_worker_id = 0
        
        # Process objects of the workers that were started with the spawn
        # method: pid -> Process. Forked workers are tracked by pid alone.
        self._processes: Dict[int, Any] = {}
        
        # Manager state
        self._running = False
        self._shutdown_requested = False
        
        # Determine spawn method based on platform
        if sys.platform == "win32":
            self._spawn_method = "spawn"
        else:
            self._spawn_method = "fork"
        
        return

    @property
    def is_running(self) -> bool:
        """Check if the manager is running."""
        return self._running
    
    @property
    def worker_count(self) -> int:
        """Get the number of active workers."""
        return len(self._workers)
    
    @property
    def worker_pids(self) -> List[int]:
        """Get list of worker PIDs."""
        return list(self._workers.keys())
    
    @property
    def config(self) -> ServerConfig:
        """Get the server configuration."""
        return self._config
    
    @property
    def boot_failed(self) -> bool:
        """
            Check whether a worker failed to start serving.
            
            :returns: True once a worker ended with the boot error exit code.
        """
        return self._boot_failed

    def spawn(self, num_workers: Optional[int] = None) -> None:
        """
            Spawn worker processes.
            
            :param num_workers: Number of workers to spawn. If None, uses config.workers.
            
            :raises ValueError: If num_workers is less than 1.
        """
        if num_workers is None:
            num_workers = self._config.workers
        
        if num_workers < 1:
            errmsg = f"Number of workers must be at least 1, got {num_workers}"
            raise ValueError(errmsg)
        
        self._running = True
        self._shutdown_requested = False
        
        _logger.info("Spawning %d worker processes (method=%s)", num_workers, self._spawn_method)
        
        for _ in range(num_workers):
            self._spawn_worker()
        
        return
    
    def _spawn_worker(self) -> int:
        """
            Spawn a single worker process.
            
            :returns: PID of the spawned worker.
        """
        worker_id = self._next_worker_id
        self._next_worker_id += 1
        
        if self._spawn_method == "fork":
            pid = self._spawn_worker_fork(worker_id)
        else:
            pid = self._spawn_worker_spawn(worker_id)
        
        # Record worker info
        self._workers[pid] = WorkerInfo(
            pid=pid,
            worker_id=worker_id,
            start_time=time.time()
        )
        
        _logger.info("Spawned worker %d (pid=%d)", worker_id, pid)
        
        return pid
    
    def _spawn_worker_fork(self, worker_id: int) -> int:
        """
            Spawn a worker using fork (Unix).
            
            :param worker_id: ID for the new worker.
            
            :returns: PID of the spawned worker (in parent process).
        """
        pid = os.fork()
        
        if pid == 0:
            # Child process - run worker. It never returns from here.
            exit_code = 0
            try:
                self._run_worker_process(worker_id)
            except WorkerBootError as boot_err:
                _logger.error("Worker %d failed to boot: %s", worker_id, str(boot_err), exc_info=boot_err)
                exit_code = WORKER_BOOT_ERROR_EXIT_CODE
            except Exception as exc:
                _logger.exception("Worker %d crashed: %s", worker_id, str(exc))
                exit_code = _WORKER_ERROR_EXIT_CODE
            finally:
                exit_code = _report_worker_end(worker_id, exit_code)
                os._exit(exit_code)
        
        # Parent process - return child PID
        return pid
    
    def _spawn_worker_spawn(self, worker_id: int) -> int:
        """
            Spawn a worker using multiprocessing spawn (cross-platform).
            
            :param worker_id: ID for the new worker.
            
            :returns: PID of the spawned worker.
        """
        ctx = multiprocessing.get_context("spawn")
        
        # The child is given the listening socket itself and the whole
        # configuration. A child that binds the address again would get a
        # listener of its own, and one built from the address alone would
        # not have the TLS settings.
        process = ctx.Process(
            target=_worker_process_entry,
            args=(
                self._app,
                self._config,
                worker_id,
                self._listener.socket,
            )
        )
        process.start()
        
        pid = process.pid
        self._processes[pid] = process
        
        return pid
    
    def _run_worker_process(self, worker_id: int) -> None:
        """
            Run the worker process main loop.
            
            :param worker_id: ID of this worker.
        """
        # Reset signal handlers in child
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        if hasattr(signal, "SIGHUP"):
            signal.signal(signal.SIGHUP, signal.SIG_IGN)
        
        prepare_worker_process(self._config)
        
        # Create and run worker
        worker = Worker(
            self._app,
            self._listener,
            self._config,
            worker_id=worker_id
        )
        
        # Setup signal handlers for shutdown. A handler runs on the main
        # thread, in between whatever that thread was doing, so it only
        # records the request. The worker finishes the requests in flight
        # and returns from run() by itself.
        def handle_term(signum: int, frame: Any) -> None:
            worker.request_shutdown(graceful=True)
            return
        
        def handle_int(signum: int, frame: Any) -> None:
            worker.request_shutdown(graceful=False)
            return
        
        signal.signal(signal.SIGTERM, handle_term)
        signal.signal(signal.SIGINT, handle_int)
        
        # Run worker
        worker.run()
        
        return


    def monitor(self) -> None:
        """
            Monitor worker health.
            
            Checks for terminated workers and restarts them.
        """
        # Reap terminated workers
        self._reap_workers()
        
        # Restart workers if needed (unless shutting down)
        if not self._shutdown_requested:
            self._maintain_worker_count()
        
        return
    
    def _reap_workers(self) -> None:
        """
            Reap terminated worker processes.
        """
        if len(self._processes) > 0:
            self._reap_spawned_workers()
        
        if sys.platform == "win32":
            return
        
        # Unix: use waitpid with WNOHANG
        while True:
            try:
                pid, status = os.waitpid(-1, os.WNOHANG)
                
                if pid == 0:
                    break
                
                if pid in self._workers:
                    worker_info = self._workers.pop(pid)
                    exit_code: Optional[int] = None
                    
                    if os.WIFEXITED(status):
                        exit_code = os.WEXITSTATUS(status)
                        _logger.info(
                            "Worker %d (pid=%d) exited with code %d",
                            worker_info.worker_id, pid, exit_code
                        )
                    elif os.WIFSIGNALED(status):
                        sig = os.WTERMSIG(status)
                        _logger.warning(
                            "Worker %d (pid=%d) killed by signal %d",
                            worker_info.worker_id, pid, sig
                        )
                    else:
                        _logger.warning(
                            "Worker %d (pid=%d) terminated unexpectedly",
                            worker_info.worker_id, pid
                        )
                    
                    self._worker_ended(pid, worker_info.worker_id, exit_code)
            except ChildProcessError:
                break
            except OSError:
                break
        
        return
    
    def _reap_spawned_workers(self) -> None:
        """
            Reap terminated workers that were started with the spawn method.
            
            The process object is asked whether the worker is alive. Probing
            with 'os.kill(pid, 0)' is not an option: on Windows that call does
            not probe, it terminates the process.
        """
        dead_pids: List[int] = []
        
        for pid, process in self._processes.items():
            if not process.is_alive():
                dead_pids.append(pid)
        
        for pid in dead_pids:
            process = self._processes.pop(pid)
            
            # Collect the exit status so the process does not linger
            process.join(timeout=0)
            
            worker_info = self._workers.pop(pid, None)
            if worker_info is not None:
                _logger.info(
                    "Worker %d (pid=%d) terminated (exit code %s)",
                    worker_info.worker_id, pid, process.exitcode
                )
                
                exit_code = process.exitcode
                if exit_code is not None and exit_code < 0:
                    # A negative exit code is the signal that ended the process
                    exit_code = None
                
                self._worker_ended(pid, worker_info.worker_id, exit_code)
        
        return
    
    def _worker_ended(self, pid: int, worker_id: int, exit_code: Optional[int]) -> None:
        """
            Record the end of a worker process.
            
            :param pid: PID of the worker process.
            :param worker_id: ID of the worker.
            :param exit_code: Its exit code, None when a signal ended it.
        """
        if exit_code == WORKER_BOOT_ERROR_EXIT_CODE:
            self._boot_failed = True
            _logger.error(
                "Worker %d (pid=%d) failed to boot, no replacement is started",
                worker_id, pid
            )
        
        if self._exit_callback is not None:
            try:
                self._exit_callback(pid, worker_id, exit_code)
            except Exception as callback_err:
                _logger.exception(
                    "The worker exit callback failed for worker %d (pid=%d): %s",
                    worker_id, pid, str(callback_err)
                )
        
        return
    
    def _maintain_worker_count(self) -> None:
        """Maintain the configured number of workers."""
        # Only maintain workers if the manager has been started
        if not self._running:
            return
        
        # A worker that could not boot is not replaced, the next one would
        # fail the same way
        if self._boot_failed:
            return
        
        current_count = len(self._workers)
        target_count = self._config.workers
        
        if current_count < target_count:
            deficit = target_count - current_count
            _logger.info(
                "Spawning %d replacement workers (current=%d, target=%d)",
                deficit, current_count, target_count
            )
            
            for _ in range(deficit):
                try:
                    self._spawn_worker()
                except Exception as exc:
                    _logger.error("Failed to spawn replacement worker: %s", str(exc))
        
        return


    def replace_workers(self) -> None:
        """
            Replace every worker with a fresh one, without dropping connections.
            
            New workers are started first and take connections from the
            listener at once. The old workers are then asked to stop
            gracefully: they finish the requests in flight and exit, and are
            reaped by monitor(). This is what a reload (SIGHUP) of the
            production server does.
        """
        if not self._running or self._shutdown_requested:
            return
        
        old_pids = list(self._workers.keys())
        
        _logger.info("Replacing %d workers", len(old_pids))
        
        for _ in range(self._config.workers):
            self._spawn_worker()
        
        for pid in old_pids:
            worker_info = self._workers.get(pid)
            if worker_info is None:
                continue
            
            try:
                process = self._processes.get(pid)
                if process is not None and sys.platform == "win32":
                    process.terminate()
                else:
                    os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                _logger.debug("Worker %d (pid=%d) already ended", worker_info.worker_id, pid)
        
        return
    
    def shutdown(self, graceful: bool = True) -> None:
        """
            Shutdown all worker processes.
            
            :param graceful: If True, wait for workers to finish current requests.
        """
        _logger.info("Worker manager shutdown requested (graceful=%s)", graceful)
        
        self._shutdown_requested = True
        
        if graceful:
            self.signal_workers(signal.SIGTERM)
            
            timeout = self._config.graceful_timeout
            start_time = time.time()
            
            while len(self._workers) > 0:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    _logger.warning(
                        "Graceful timeout exceeded, %d workers remaining",
                        len(self._workers)
                    )
                    self._force_kill_workers()
                    break
                
                self._reap_workers()
                
                if len(self._workers) > 0:
                    time.sleep(0.1)
        else:
            self._force_kill_workers()
        
        self._workers.clear()
        self._processes.clear()
        self._running = False
        
        _logger.info("Worker manager shutdown complete")
        
        return
    
    def _force_kill_workers(self) -> None:
        """Force kill all remaining workers."""
        for pid, worker_info in list(self._workers.items()):
            _logger.warning("Force killing worker %d (pid=%d)", worker_info.worker_id, pid)
            
            try:
                process = self._processes.get(pid)
                if process is not None:
                    # A spawned worker is killed through its process object,
                    # there is no SIGKILL on Windows.
                    process.kill()
                else:
                    os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                # The worker already exited, which is the outcome the force kill wanted.
                pass
            except Exception as exc:
                _logger.error("Error killing worker %d: %s", worker_info.worker_id, str(exc))
        
        return

    def signal_workers(self, signum: int) -> None:
        """
            Send a signal to all worker processes.
            
            :param signum: Signal number to send.
        """
        for pid, worker_info in self._workers.items():
            try:
                process = self._processes.get(pid)
                if process is not None and sys.platform == "win32":
                    # Windows cannot deliver a signal to another process,
                    # 'os.kill' would terminate it whatever the signal is.
                    # Say so by terminating through the process object.
                    process.terminate()
                else:
                    os.kill(pid, signum)
                _logger.debug("Sent signal %d to worker %d (pid=%d)", signum, worker_info.worker_id, pid)
            except ProcessLookupError:
                _logger.debug("Worker %d (pid=%d) already dead", worker_info.worker_id, pid)
            except PermissionError:
                _logger.error("Permission denied sending signal to worker %d (pid=%d)", worker_info.worker_id, pid)
            except Exception as exc:
                _logger.error("Error sending signal to worker %d: %s", worker_info.worker_id, str(exc))
        
        return

    def update_worker_heartbeat(self, pid: int) -> None:
        """
            Update the heartbeat timestamp for a worker.
            
            :param pid: PID of the worker to update.
        """
        if pid in self._workers:
            self._workers[pid].last_heartbeat = time.time()
        
        return

    def get_worker_stats(self) -> Dict[str, Any]:
        """
            Get worker manager statistics.
            
            :returns: Dictionary with manager statistics.
        """
        current_time = time.time()
        worker_stats: List[Dict[str, Any]] = []
        
        for pid, worker_info in self._workers.items():
            worker_stats.append({
                "pid": pid,
                "worker_id": worker_info.worker_id,
                "uptime": current_time - worker_info.start_time,
                "request_count": worker_info.request_count,
                "is_alive": worker_info.is_alive,
            })
        
        rtnval = {
            "running": self._running,
            "shutdown_requested": self._shutdown_requested,
            "worker_count": len(self._workers),
            "target_workers": self._config.workers,
            "spawn_method": self._spawn_method,
            "workers": worker_stats,
        }
        
        return rtnval


def _worker_process_entry(
    app: Callable,
    config: ServerConfig,
    worker_id: int,
    listen_socket: Any
) -> None:
    """
        Entry point for spawned worker processes.
        
        This function is called in the child process when using spawn method.
        
        :param app: The WSGI application callable.
        :param config: The full server configuration.
        :param worker_id: ID of this worker.
        :param listen_socket: The listening socket of the server, shared with
                              the parent process.
    """
    prepare_worker_process(config)
    
    # Use the listener of the parent. Binding again would create a second
    # listener, and the TLS settings come from the full configuration.
    listener = SocketListener(config)
    listener.attach(listen_socket)
    
    if config.ssl_certfile is not None:
        listener.setup_ssl()
    
    # Create and run worker
    worker = Worker(app, listener, config, worker_id=worker_id)
    
    def handle_term(signum: int, frame: Any) -> None:
        worker.request_shutdown(graceful=True)
        return
    
    def handle_int(signum: int, frame: Any) -> None:
        worker.request_shutdown(graceful=False)
        return
    
    signal.signal(signal.SIGTERM, handle_term)
    signal.signal(signal.SIGINT, handle_int)
    
    try:
        worker.run()
    except WorkerBootError as boot_err:
        _logger.error("Worker %d failed to boot: %s", worker_id, str(boot_err), exc_info=boot_err)
        listener.close()
        sys.exit(WORKER_BOOT_ERROR_EXIT_CODE)
    finally:
        listener.close()
    
    return

