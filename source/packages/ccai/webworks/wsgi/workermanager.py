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
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

from ccai.webworks.wsgi.serverconfig import ServerConfig
from ccai.webworks.wsgi.socketlistener import SocketListener
from ccai.webworks.wsgi.worker import Worker
from ccai.webworks.wsgi.exceptions import WorkerError


# Default logger for worker manager
_logger = logging.getLogger("webworks.wsgi.workermanager")


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
        config: Optional[ServerConfig] = None
    ):
        """
            Construct a worker manager.
            
            :param app: The WSGI application callable.
            :param listener: The socket listener for accepting connections.
            :param config: Server configuration. If None, uses defaults.
        """
        self._app = app
        self._listener = listener
        
        if config is not None:
            self._config = config
        else:
            self._config = ServerConfig()
        
        # Worker tracking: pid -> WorkerInfo
        self._workers: Dict[int, WorkerInfo] = {}
        self._next_worker_id = 0
        
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
            # Child process - run worker
            try:
                self._run_worker_process(worker_id)
            except Exception as exc:
                _logger.exception("Worker %d crashed: %s", worker_id, str(exc))
            finally:
                os._exit(0)
        
        # Parent process - return child PID
        return pid
    
    def _spawn_worker_spawn(self, worker_id: int) -> int:
        """
            Spawn a worker using multiprocessing spawn (cross-platform).
            
            :param worker_id: ID for the new worker.
            
            :returns: PID of the spawned worker.
        """
        ctx = multiprocessing.get_context("spawn")
        
        process = ctx.Process(
            target=_worker_process_entry,
            args=(
                self._app,
                self._config,
                worker_id,
                self._listener.config.host,
                self._listener.config.port,
                self._listener.config.unix_socket,
            )
        )
        process.start()
        
        return process.pid
    
    def _run_worker_process(self, worker_id: int) -> None:
        """
            Run the worker process main loop.
            
            :param worker_id: ID of this worker.
        """
        # Reset signal handlers in child
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        
        # Create and run worker
        worker = Worker(
            self._app,
            self._listener,
            self._config,
            worker_id=worker_id
        )
        
        # Setup signal handlers for graceful shutdown
        def handle_term(signum: int, frame: Any) -> None:
            worker.shutdown(graceful=True)
        
        def handle_int(signum: int, frame: Any) -> None:
            worker.shutdown(graceful=False)
        
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
        if sys.platform == "win32":
            self._reap_workers_windows()
            return
        
        # Unix: use waitpid with WNOHANG
        while True:
            try:
                pid, status = os.waitpid(-1, os.WNOHANG)
                
                if pid == 0:
                    break
                
                if pid in self._workers:
                    worker_info = self._workers.pop(pid)
                    
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
            except ChildProcessError:
                break
            except OSError:
                break
        
        return
    
    def _reap_workers_windows(self) -> None:
        """Reap terminated workers on Windows."""
        dead_pids: List[int] = []
        
        for pid, worker_info in self._workers.items():
            try:
                os.kill(pid, 0)
            except OSError:
                dead_pids.append(pid)
                _logger.info(
                    "Worker %d (pid=%d) terminated",
                    worker_info.worker_id, pid
                )
        
        for pid in dead_pids:
            del self._workers[pid]
        
        return
    
    def _maintain_worker_count(self) -> None:
        """Maintain the configured number of workers."""
        # Only maintain workers if the manager has been started
        if not self._running:
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
        self._running = False
        
        _logger.info("Worker manager shutdown complete")
        
        return
    
    def _force_kill_workers(self) -> None:
        """Force kill all remaining workers."""
        for pid, worker_info in list(self._workers.items()):
            _logger.warning("Force killing worker %d (pid=%d)", worker_info.worker_id, pid)
            
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
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
    host: str,
    port: int,
    unix_socket: Optional[str]
) -> None:
    """
        Entry point for spawned worker processes.
        
        This function is called in the child process when using spawn method.
    """
    # Recreate listener in child process
    listener_config = ServerConfig(host=host, port=port, unix_socket=unix_socket)
    listener = SocketListener(listener_config)
    listener.bind()
    
    # Create and run worker
    worker = Worker(app, listener, config, worker_id=worker_id)
    
    def handle_term(signum: int, frame: Any) -> None:
        worker.shutdown(graceful=True)
    
    def handle_int(signum: int, frame: Any) -> None:
        worker.shutdown(graceful=False)
    
    signal.signal(signal.SIGTERM, handle_term)
    signal.signal(signal.SIGINT, handle_int)
    
    try:
        worker.run()
    finally:
        listener.close()
    
    return

