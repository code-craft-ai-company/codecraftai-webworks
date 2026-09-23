"""
    Tests for the WorkerManager class in the WSGI layer.
"""

import signal
import sys
import time

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
