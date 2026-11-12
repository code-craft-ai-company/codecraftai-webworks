"""
    Tests for the WorkerManager class in the WSGI layer.
"""

import os
import signal
import subprocess
import sys
import time
from typing import List, Optional

from ccai.webworks.wsgi.workermanager import WorkerManager, WorkerInfo
from ccai.webworks.wsgi.serverconfig import ServerConfig
from ccai.webworks.wsgi.socketlistener import SocketListener


def create_simple_app():
    """Create a simple WSGI application for testing."""
    def app(environ, start_response):
        status = "200 OK"
        headers = [("Content-Type", "text/plain"), ("Content-Length", "13")]
        start_response(status, headers)
        return [b"Hello, World!"]
    return app


def create_mock_listener(host="127.0.0.1", port=0):
    """Create a mock socket listener for testing."""
    config = ServerConfig(host=host, port=port)
    listener = SocketListener(config)
    listener.bind()
    return listener


def test_workermanager_init_with_defaults():
    """Test WorkerManager initialization with default configuration."""
    app = create_simple_app()
    listener = create_mock_listener()
    
    try:
        manager = WorkerManager(app, listener)
        
        if manager.is_running is True:
            errmsg = f"Expected is_running False, got {manager.is_running}"
            raise AssertionError(errmsg)
        
        if manager.worker_count != 0:
            errmsg = f"Expected worker_count 0, got {manager.worker_count}"
            raise AssertionError(errmsg)
        
        if manager.config.workers != 1:
            errmsg = f"Expected config.workers 1, got {manager.config.workers}"
            raise AssertionError(errmsg)
    finally:
        listener.close()
    
    return


def test_workermanager_init_with_custom_config():
    """Test WorkerManager initialization with custom configuration."""
    app = create_simple_app()
    config = ServerConfig(host="127.0.0.1", port=0, workers=4, threads=2, timeout=60)
    listener = create_mock_listener()
    
    try:
        manager = WorkerManager(app, listener, config)
        
        if manager.config.workers != 4:
            errmsg = f"Expected workers 4, got {manager.config.workers}"
            raise AssertionError(errmsg)
        
        if manager.config.threads != 2:
            errmsg = f"Expected threads 2, got {manager.config.threads}"
            raise AssertionError(errmsg)
    finally:
        listener.close()
    
    return


def test_workerinfo_creation():
    """Test WorkerInfo dataclass creation."""
    current_time = time.time()
    info = WorkerInfo(pid=12345, worker_id=1, start_time=current_time)
    
    if info.pid != 12345:
        errmsg = f"Expected pid 12345, got {info.pid}"
        raise AssertionError(errmsg)
    
    if info.worker_id != 1:
        errmsg = f"Expected worker_id 1, got {info.worker_id}"
        raise AssertionError(errmsg)
    
    if info.request_count != 0:
        errmsg = f"Expected request_count 0, got {info.request_count}"
        raise AssertionError(errmsg)
    
    return


def test_workermanager_worker_pids_empty():
    """Test WorkerManager.worker_pids returns empty list when no workers."""
    app = create_simple_app()
    listener = create_mock_listener()
    
    try:
        manager = WorkerManager(app, listener)
        pids = manager.worker_pids
        
        if len(pids) != 0:
            errmsg = f"Expected empty list, got {pids}"
            raise AssertionError(errmsg)
    finally:
        listener.close()
    
    return


def test_workermanager_get_worker_stats_empty():
    """Test WorkerManager.get_worker_stats() with no workers."""
    app = create_simple_app()
    listener = create_mock_listener()
    
    try:
        manager = WorkerManager(app, listener)
        stats = manager.get_worker_stats()
        
        if stats["running"] is True:
            errmsg = f"Expected running False, got {stats['running']}"
            raise AssertionError(errmsg)
        
        if stats["worker_count"] != 0:
            errmsg = f"Expected worker_count 0, got {stats['worker_count']}"
            raise AssertionError(errmsg)
        
        if stats["target_workers"] != 1:
            errmsg = f"Expected target_workers 1, got {stats['target_workers']}"
            raise AssertionError(errmsg)
    finally:
        listener.close()
    
    return


def test_workermanager_shutdown_when_not_running():
    """Test WorkerManager.shutdown() when manager is not running."""
    app = create_simple_app()
    listener = create_mock_listener()
    
    try:
        manager = WorkerManager(app, listener)
        manager.shutdown(graceful=True)
        
        if manager.is_running is True:
            errmsg = f"Expected is_running False, got {manager.is_running}"
            raise AssertionError(errmsg)
    finally:
        listener.close()
    
    return


def test_workermanager_signal_workers_empty():
    """Test WorkerManager.signal_workers() with no workers."""
    app = create_simple_app()
    listener = create_mock_listener()
    
    try:
        manager = WorkerManager(app, listener)
        manager.signal_workers(signal.SIGTERM)
    finally:
        listener.close()
    
    return


def test_workermanager_update_heartbeat_nonexistent():
    """Test WorkerManager.update_worker_heartbeat() with nonexistent PID."""
    app = create_simple_app()
    listener = create_mock_listener()
    
    try:
        manager = WorkerManager(app, listener)
        manager.update_worker_heartbeat(99999)
    finally:
        listener.close()
    
    return


def test_workermanager_spawn_invalid_count():
    """Test WorkerManager.spawn() with invalid worker count."""
    app = create_simple_app()
    listener = create_mock_listener()
    
    try:
        manager = WorkerManager(app, listener)
        
        try:
            manager.spawn(num_workers=0)
            errmsg = "Expected ValueError for num_workers=0"
            raise AssertionError(errmsg)
        except ValueError as val_err:
            if "at least 1" not in str(val_err):
                errmsg = f"Expected 'at least 1' in error message, got: {val_err}"
                raise AssertionError(errmsg)
    finally:
        listener.close()
    
    return


def test_workermanager_monitor_no_workers():
    """Test WorkerManager.monitor() with no workers."""
    app = create_simple_app()
    listener = create_mock_listener()
    
    try:
        manager = WorkerManager(app, listener)
        manager.monitor()
        
        if manager.worker_count != 0:
            errmsg = f"Expected worker_count 0, got {manager.worker_count}"
            raise AssertionError(errmsg)
    finally:
        listener.close()
    
    return


def test_workermanager_spawn_and_shutdown():
    """Test WorkerManager spawning and shutting down workers (Unix only)."""
    if sys.platform == "win32":
        return
    
    app = create_simple_app()
    config = ServerConfig(host="127.0.0.1", port=0, workers=1, timeout=5, graceful_timeout=2)
    listener = create_mock_listener()
    
    try:
        manager = WorkerManager(app, listener, config)
        manager.spawn(num_workers=1)
        time.sleep(0.5)
        
        if manager.is_running is not True:
            errmsg = f"Expected is_running True, got {manager.is_running}"
            raise AssertionError(errmsg)
        
        if manager.worker_count != 1:
            errmsg = f"Expected worker_count 1, got {manager.worker_count}"
            raise AssertionError(errmsg)
        
        manager.shutdown(graceful=False)
        time.sleep(0.5)
        
        if manager.is_running is True:
            errmsg = f"Expected is_running False after shutdown, got {manager.is_running}"
            raise AssertionError(errmsg)
    finally:
        listener.close()
    
    return


def test_workermanager_spawn_multiple_workers():
    """Test WorkerManager spawning multiple workers (Unix only)."""
    if sys.platform == "win32":
        return
    
    app = create_simple_app()
    config = ServerConfig(host="127.0.0.1", port=0, workers=2, timeout=5, graceful_timeout=2)
    listener = create_mock_listener()
    
    try:
        manager = WorkerManager(app, listener, config)
        manager.spawn(num_workers=2)
        time.sleep(0.5)
        
        if manager.worker_count != 2:
            errmsg = f"Expected worker_count 2, got {manager.worker_count}"
            raise AssertionError(errmsg)
        
        pids = manager.worker_pids
        if len(pids) != 2:
            errmsg = f"Expected 2 PIDs, got {len(pids)}"
            raise AssertionError(errmsg)
        
        if len(set(pids)) != 2:
            errmsg = f"Expected unique PIDs, got {pids}"
            raise AssertionError(errmsg)
        
        manager.shutdown(graceful=False)
        time.sleep(0.5)
    finally:
        listener.close()
    
    return


# =============================================================================
# Tests for the supervision of workers started with the spawn method
# =============================================================================

class FakeProcess:
    """
        Stand-in for a multiprocessing.Process that records what is asked of it.
    """
    
    def __init__(self, pid: int, alive: bool):
        """
            Construct a fake process.
        """
        self.pid = pid
        self.alive = alive
        self.exitcode: Optional[int] = None
        self.calls: List[str] = []
        return
    
    def is_alive(self) -> bool:
        """
            Report whether the process is alive.
        """
        self.calls.append("is_alive")
        return self.alive
    
    def join(self, timeout: Optional[float] = None) -> None:
        """
            Record that the process was joined.
        """
        self.calls.append("join")
        return
    
    def kill(self) -> None:
        """
            Record that the process was killed.
        """
        self.calls.append("kill")
        self.alive = False
        return
    
    def terminate(self) -> None:
        """
            Record that the process was terminated.
        """
        self.calls.append("terminate")
        self.alive = False
        return


def get_finished_pid() -> int:
    """
        Get the PID of a process that has run and been collected, so no
        signal sent to it by mistake can reach a live process of this test.
    """
    finished = subprocess.Popen([sys.executable, "-c", "pass"])
    finished.wait()
    return finished.pid


def create_manager_with_spawned_worker(process: FakeProcess) -> WorkerManager:
    """
        Create a manager that tracks one worker started with the spawn method.
    """
    config = ServerConfig(workers=1)
    listener = SocketListener(config)
    manager = WorkerManager(create_simple_app(), listener, config)
    manager._workers[process.pid] = WorkerInfo(pid=process.pid, worker_id=0, start_time=time.time())
    manager._processes[process.pid] = process
    return manager


def test_reap_removes_spawned_worker_whose_process_ended():
    """
        Test that a spawned worker is reaped when its process object says it ended.
    """
    # The PID is that of this test process, which is alive. Only asking the
    # process object can find that the worker has ended.
    process = FakeProcess(pid=os.getpid(), alive=False)
    manager = create_manager_with_spawned_worker(process)
    
    manager._reap_workers()
    
    if manager.worker_count != 0:
        errmsg = f"Expected the ended worker to be reaped, {manager.worker_count} workers remain"
        raise AssertionError(errmsg)
    
    return


def test_reap_keeps_spawned_worker_whose_process_is_alive():
    """
        Test that a spawned worker stays tracked while its process object says it is alive.
    """
    # The PID belongs to no process. Only asking the process object can find
    # that the worker is alive, and nothing may be sent to the PID.
    process = FakeProcess(pid=get_finished_pid(), alive=True)
    manager = create_manager_with_spawned_worker(process)
    
    manager._reap_workers()
    
    if manager.worker_count != 1:
        errmsg = f"Expected the live worker to stay tracked, {manager.worker_count} workers remain"
        raise AssertionError(errmsg)
    
    if "kill" in process.calls or "terminate" in process.calls:
        errmsg = f"Expected the liveness check not to end the worker, got {process.calls}"
        raise AssertionError(errmsg)
    
    return


def test_force_kill_uses_process_object_for_spawned_worker():
    """
        Test that a spawned worker is force killed through its process object.
    """
    process = FakeProcess(pid=get_finished_pid(), alive=True)
    manager = create_manager_with_spawned_worker(process)
    
    manager._force_kill_workers()
    
    if "kill" not in process.calls:
        errmsg = f"Expected the process object to be killed, got {process.calls}"
        raise AssertionError(errmsg)
    
    return


def test_shutdown_forgets_spawned_process_objects():
    """
        Test that shutdown leaves no process object of a spawned worker behind.
    """
    process = FakeProcess(pid=get_finished_pid(), alive=True)
    manager = create_manager_with_spawned_worker(process)
    
    manager.shutdown(graceful=False)
    
    if len(manager._processes) != 0:
        errmsg = f"Expected no tracked process objects after shutdown, got {manager._processes}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Tests for boot failures, exit reporting and worker replacement
# =============================================================================

class BootFailingApp:
    """
        A WSGI application that cannot start in a worker.
    """
    
    def on_worker_start(self, worker) -> None:
        raise RuntimeError("cannot start here")
    
    def __call__(self, environ, start_response):
        start_response("200 OK", [])
        return [b""]


def test_worker_that_ended_with_boot_error_stops_replacement():
    """
        A worker that ends with the boot error exit code marks the manager as
        failed, and no replacement is started.
    """
    from ccai.webworks.wsgi.constants import WORKER_BOOT_ERROR_EXIT_CODE
    
    ended: List[tuple] = []
    process = FakeProcess(pid=get_finished_pid(), alive=False)
    process.exitcode = WORKER_BOOT_ERROR_EXIT_CODE
    manager = create_manager_with_spawned_worker(process)
    manager._exit_callback = lambda pid, worker_id, exit_code: ended.append((pid, worker_id, exit_code))
    manager._running = True
    
    manager._reap_workers()
    manager._maintain_worker_count()
    
    if manager.boot_failed is not True:
        errmsg = "Expected the manager to record the boot failure"
        raise AssertionError(errmsg)
    
    if manager.worker_count != 0:
        errmsg = f"Expected no replacement worker, got {manager.worker_count} workers"
        raise AssertionError(errmsg)
    
    if ended != [(process.pid, 0, WORKER_BOOT_ERROR_EXIT_CODE)]:
        errmsg = f"Expected the exit callback to be told about the worker, got {ended}"
        raise AssertionError(errmsg)
    
    return


def test_worker_that_ended_normally_is_reported_and_not_a_boot_failure():
    """
        A worker that exits with 0 is reported to the exit callback only.
    """
    ended: List[tuple] = []
    process = FakeProcess(pid=get_finished_pid(), alive=False)
    process.exitcode = 0
    manager = create_manager_with_spawned_worker(process)
    manager._exit_callback = lambda pid, worker_id, exit_code: ended.append((pid, worker_id, exit_code))
    
    manager._reap_workers()
    
    if manager.boot_failed is not False or ended != [(process.pid, 0, 0)]:
        errmsg = f"Expected a normal exit to be reported, got boot_failed={manager.boot_failed} {ended}"
        raise AssertionError(errmsg)
    
    return


def _wait_for(condition, timeout: float = 15.0, monitor: Optional[WorkerManager] = None) -> bool:
    """
        Poll a condition, letting the manager reap its workers meanwhile.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        if monitor is not None:
            monitor._reap_workers()
        if condition():
            return True
        time.sleep(0.05)
    return False


def test_forked_worker_that_cannot_boot_is_detected():
    """
        A forked worker whose application fails on_worker_start exits with the
        boot error code, and the manager stops replacing it.
    """
    if not hasattr(os, "fork"):
        from ccai.errors.exceptions import SkipError
        raise SkipError("os.fork is not available on this platform.")
    
    config = ServerConfig(host="127.0.0.1", port=0, workers=1, graceful_timeout=2)
    listener = SocketListener(config)
    listener.bind()
    manager = WorkerManager(BootFailingApp(), listener, config)
    
    try:
        manager.spawn()
        detected = _wait_for(lambda: manager.boot_failed, monitor=manager)
        manager.monitor()
        remaining = manager.worker_count
    finally:
        manager.shutdown(graceful=False)
        listener.close()
    
    if not detected or remaining != 0:
        errmsg = f"Expected the boot failure to be detected and not replaced, detected={detected} workers={remaining}"
        raise AssertionError(errmsg)
    
    return


def test_replace_workers_starts_new_workers_and_retires_old_ones():
    """
        replace_workers() starts fresh workers before the old ones stop.
    """
    if not hasattr(os, "fork"):
        from ccai.errors.exceptions import SkipError
        raise SkipError("os.fork is not available on this platform.")
    
    config = ServerConfig(host="127.0.0.1", port=0, workers=1, graceful_timeout=2)
    listener = SocketListener(config)
    listener.bind()
    manager = WorkerManager(create_simple_app(), listener, config)
    
    try:
        manager.spawn()
        old_pids = set(manager.worker_pids)
        
        manager.replace_workers()
        during = set(manager.worker_pids)
        
        replaced = _wait_for(lambda: len(set(manager.worker_pids) & old_pids) == 0, monitor=manager)
        final_pids = set(manager.worker_pids)
    finally:
        manager.shutdown(graceful=False)
        listener.close()
    
    if len(during) != 2 or not old_pids.issubset(during):
        errmsg = f"Expected the new worker to start next to the old one, got {during} (old {old_pids})"
        raise AssertionError(errmsg)
    
    if not replaced or len(final_pids) != 1 or final_pids & old_pids:
        errmsg = f"Expected one new worker in place of the old one, got {final_pids} (old {old_pids})"
        raise AssertionError(errmsg)
    
    return
