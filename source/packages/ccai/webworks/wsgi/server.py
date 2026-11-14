"""
    WSGI Server module for the webworks framework.
    
    This module provides the WSGIServer class, a built-in WSGI server for running
    applications without external dependencies. The server supports process-based
    concurrency with optional threading per worker, graceful shutdown, signal
    handling, and development mode with auto-reload.
"""

import logging
import os
import signal
import sys
import threading
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Iterable, List, Optional

from ccai.webworks.wsgi.serverconfig import ServerConfig
from ccai.webworks.wsgi.socketlistener import SocketListener
from ccai.webworks.wsgi.workermanager import WorkerManager
from ccai.webworks.wsgi.exceptions import ServerError


# Default logger for WSGI server
_logger = logging.getLogger("webworks.wsgi.server")


class WSGIServer:
    """
        Built-in WSGI server for running applications without external dependencies.
        
        This server provides process-based concurrency with optional threading per
        worker. It supports graceful shutdown, signal handling, request logging,
        and development mode with auto-reload on code changes.
        
        The server follows the WSGI specification (PEP 3333) and can serve any
        compliant WSGI application, including a WebApplication through its
        'wsgi_app'.
        
        A subclass adds behaviour at fixed points of serve_forever() by
        overriding the hook methods: _setup_ssl() installs TLS on the bound
        listener, _after_bind() runs once the address is bound and before any
        worker exists (the production server drops privileges there),
        _create_worker_manager() builds the worker manager, and _after_spawn()
        runs once the workers have been started.
    """
    
    def __init__(
        self,
        app: Callable[[Dict[str, Any], Callable], Iterable[bytes]],
        config: Optional[ServerConfig] = None
    ):
        """
            Construct a WSGI server.
            
            :param app: The WSGI application callable. Must accept environ dict
                       and start_response callable, returning an iterable of bytes.
            :param config: Server configuration. If None, uses default configuration.
        """
        self._app = app
        
        if config is not None:
            self._config = config
        else:
            self._config = ServerConfig()
        
        # Server components
        self._listener: Optional[SocketListener] = None
        self._worker_manager: Optional[WorkerManager] = None
        
        # Server state
        self._running = False
        self._shutdown_requested = False
        self._shutdown_graceful = True
        
        # Stopping the workers is done once, by whichever thread gets to it
        # first: the thread that called shutdown() or the main loop after a
        # signal asked for the shutdown.
        self._shutdown_lock = threading.Lock()
        self._workers_stopped = False
        
        # Set when a worker could not start serving
        self._boot_failed = False
        
        # Signal handling
        self._original_sigterm: Optional[signal.Handlers] = None
        self._original_sigint: Optional[signal.Handlers] = None
        self._original_sighup: Optional[signal.Handlers] = None
        
        # Development mode - file watching
        self._reload_thread: Optional[threading.Thread] = None
        self._watched_files: Dict[str, str] = {}  # path -> signature
        self._reload_requested = False
        
        # Request logging
        self._request_count = 0
        self._start_time: Optional[float] = None
        self._lock = threading.Lock()
        
        return
    
    @property
    def is_running(self) -> bool:
        """
            Check if the server is running.
            
            :returns: True if server is running, False otherwise.
        """
        return self._running
    
    @property
    def config(self) -> ServerConfig:
        """
            Get the server configuration.
            
            :returns: ServerConfig instance.
        """
        return self._config
    
    @property
    def listener(self) -> Optional[SocketListener]:
        """
            Get the socket listener.
            
            :returns: SocketListener instance or None if not bound.
        """
        return self._listener
    
    @property
    def worker_manager(self) -> Optional[WorkerManager]:
        """
            Get the worker manager.
            
            :returns: WorkerManager instance or None if not started.
        """
        return self._worker_manager
    
    @property
    def boot_failed(self) -> bool:
        """
            Check whether the server stopped because a worker failed to boot.
            
            :returns: True if serve_forever() ended because a worker could not
                start serving.
        """
        return self._boot_failed
    
    @property
    def request_count(self) -> int:
        """
            Get the total number of requests processed.
            
            :returns: Total request count.
        """
        with self._lock:
            rtnval = self._request_count
        return rtnval
    
    @property
    def uptime(self) -> float:
        """
            Get the server uptime in seconds.
            
            :returns: Uptime in seconds, or 0 if not running.
        """
        if self._start_time is None:
            return 0.0
        
        rtnval = time.time() - self._start_time
        return rtnval


    def serve_forever(self) -> None:
        """
            Start the server and block until shutdown.
            
            This method binds the socket, spawns worker processes, and enters
            the main monitoring loop. It blocks until shutdown() is called
            or a shutdown signal is received.
            
            :raises: BindError if socket binding fails.
            :raises: ServerError if server startup fails.
        """
        if self._running is True:
            errmsg = "Server is already running"
            raise ServerError(errmsg)
        
        # Validate configuration
        self._config.validate()
        
        # Setup logging
        self._setup_logging()
        
        # Log startup
        self._log_startup()
        
        try:
            # Create and bind socket listener
            self._listener = SocketListener(self._config)
            self._listener.bind()
            
            # Setup SSL if configured
            self._setup_ssl()
            
            # Everything that needs the bound address and comes before any
            # worker exists
            self._after_bind()
            
            # Setup signal handlers
            self._setup_signals()
            
            # Create worker manager
            self._worker_manager = self._create_worker_manager()
            
            # Mark server as running
            self._running = True
            self._shutdown_requested = False
            self._workers_stopped = False
            self._boot_failed = False
            self._start_time = time.time()
            
            # Start development mode file watcher if enabled
            if self._config.reload is True:
                self._start_reload_watcher()
            
            # Spawn worker processes
            self._worker_manager.spawn()
            
            _logger.info(
                "Server started on %s (workers=%d, threads=%d)",
                self._get_bind_address(),
                self._config.workers,
                self._config.threads
            )
            
            self._after_spawn()
            
            # Enter main monitoring loop
            self._main_loop()
            
            # A signal only asks for the shutdown, it is carried out here,
            # on the main thread and outside of the signal handler.
            self._stop_workers()
            
        except Exception as exc:
            _logger.error("Server failed: %s", str(exc))
            raise
        finally:
            self._cleanup()
        
        return
    
    def _setup_ssl(self) -> None:
        """
            Install TLS on the bound listener when it is configured.
            
            Override to install a TLS context built elsewhere.
        """
        if self._config.ssl_certfile is not None:
            self._listener.setup_ssl()
        return
    
    def _after_bind(self) -> None:
        """
            Hook run once the listener is bound and before any worker exists.
            
            The base server does nothing here. Raising stops the server.
        """
        return
    
    def _create_worker_manager(self) -> WorkerManager:
        """
            Build the worker manager of the server.
            
            :returns: The WorkerManager that runs the workers.
        """
        rtnval = WorkerManager(
            self._app,
            self._listener,
            self._config
        )
        return rtnval
    
    def _after_spawn(self) -> None:
        """
            Hook run once the workers have been started.
            
            The base server does nothing here.
        """
        return
    
    def _main_loop(self) -> None:
        """
            Main server monitoring loop.
            
            Monitors worker health and handles shutdown requests.
        """
        while not self._shutdown_requested:
            try:
                # Monitor workers
                if self._worker_manager is not None:
                    self._worker_manager.monitor()
                    
                    if self._worker_manager.boot_failed:
                        # A worker could not start serving, a replacement
                        # would fail the same way
                        _logger.error("A worker failed to boot, stopping the server")
                        self._boot_failed = True
                        self._shutdown_graceful = True
                        self._shutdown_requested = True
                        break
                
                # Check for reload request in development mode
                if self._reload_requested is True:
                    self._handle_reload()
                
                # Sleep briefly to avoid busy-waiting
                time.sleep(0.5)
                
            except InterruptedError:
                # Signal interrupted sleep, check shutdown flag
                continue
            except Exception as exc:
                _logger.error("Error in main loop: %s", str(exc))
                continue
        
        return
    
    def _get_bind_address(self) -> str:
        """
            Get the bind address string for logging.
            
            :returns: Bind address string.
        """
        if self._config.unix_socket is not None:
            rtnval = f"unix:{self._config.unix_socket}"
        else:
            scheme = "https" if self._config.ssl_certfile else "http"
            rtnval = f"{scheme}://{self._config.host}:{self._config.port}"
        
        return rtnval

    def shutdown(self, graceful: bool = True) -> None:
        """
            Shutdown the server.
            
            Signals the server to stop accepting new connections. If graceful
            is True, waits for active requests to complete before terminating
            workers.
            
            :param graceful: If True, wait for active requests to complete.
        """
        if self._running is not True:
            return
        
        _logger.info("Server shutdown requested (graceful=%s)", graceful)
        
        self._shutdown_graceful = graceful
        self._shutdown_requested = True
        
        self._stop_workers()
        
        return
    
    def _stop_workers(self) -> None:
        """
            Stop the reload watcher and shut the worker manager down.
            
            The work is done once. A second caller waits until the first one
            has finished and then returns.
        """
        with self._shutdown_lock:
            if self._workers_stopped is True:
                return
            
            self._workers_stopped = True
            
            # Stop reload watcher if running
            self._stop_reload_watcher()
            
            # Shutdown worker manager
            if self._worker_manager is not None:
                self._worker_manager.shutdown(graceful=self._shutdown_graceful)
        
        return
    
    def _cleanup(self) -> None:
        """
            Clean up server resources.
            
            Closes socket listener, restores signal handlers, and resets state.
        """
        # Stop reload watcher
        self._stop_reload_watcher()
        
        # Close socket listener
        if self._listener is not None:
            self._listener.close()
            self._listener = None
        
        # Restore signal handlers
        self._restore_signals()
        
        # Reset state
        self._running = False
        self._worker_manager = None
        
        _logger.info("Server shutdown complete")
        
        return


    def _setup_signals(self) -> None:
        """
            Setup signal handlers for graceful shutdown.
            
            Handles SIGTERM, SIGINT, and SIGHUP signals.
            Signal handlers can only be set in the main thread.
        """
        # Only setup signal handlers on Unix-like systems
        if sys.platform == "win32":
            return
        
        # Signal handlers can only be set in the main thread
        if threading.current_thread() is not threading.main_thread():
            _logger.debug("Skipping signal setup - not in main thread")
            return
        
        # Save original handlers
        self._original_sigterm = signal.signal(signal.SIGTERM, self._handle_sigterm)
        self._original_sigint = signal.signal(signal.SIGINT, self._handle_sigint)
        
        # SIGHUP for reload (Unix only)
        if hasattr(signal, "SIGHUP"):
            self._original_sighup = signal.signal(signal.SIGHUP, self._handle_sighup)
        
        return
    
    def _restore_signals(self) -> None:
        """
            Restore original signal handlers.
        """
        if sys.platform == "win32":
            return
        
        # Signal handlers can only be restored in the main thread
        if threading.current_thread() is not threading.main_thread():
            return
        
        if self._original_sigterm is not None:
            signal.signal(signal.SIGTERM, self._original_sigterm)
            self._original_sigterm = None
        
        if self._original_sigint is not None:
            signal.signal(signal.SIGINT, self._original_sigint)
            self._original_sigint = None
        
        if self._original_sighup is not None and hasattr(signal, "SIGHUP"):
            signal.signal(signal.SIGHUP, self._original_sighup)
            self._original_sighup = None
        
        return
    
    def _handle_sigterm(self, signum: int, frame: Any) -> None:
        """
            Handle SIGTERM signal for graceful shutdown.
            
            The handler interrupts the main thread wherever it is, so it only
            records the request. The main loop sees the request and carries
            the shutdown out.
            
            :param signum: Signal number.
            :param frame: Current stack frame.
        """
        self._shutdown_graceful = True
        self._shutdown_requested = True
        return
    
    def _handle_sigint(self, signum: int, frame: Any) -> None:
        """
            Handle SIGINT signal for immediate shutdown.
            
            Only records the request, see the SIGTERM handler.
            
            :param signum: Signal number.
            :param frame: Current stack frame.
        """
        self._shutdown_graceful = False
        self._shutdown_requested = True
        return
    
    def _handle_sighup(self, signum: int, frame: Any) -> None:
        """
            Handle SIGHUP signal for reload.
            
            :param signum: Signal number.
            :param frame: Current stack frame.
        """
        self._reload_requested = True
        return

    def _setup_logging(self) -> None:
        """
            Setup logging based on configuration.
        """
        # Set log level
        log_level = getattr(logging, self._config.log_level.upper(), logging.INFO)
        
        # Configure root logger for webworks
        webworks_logger = logging.getLogger("webworks")
        webworks_logger.setLevel(log_level)
        
        # Add handler if none exists
        if len(webworks_logger.handlers) == 0:
            handler = logging.StreamHandler(sys.stderr)
            handler.setLevel(log_level)
            formatter = logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            handler.setFormatter(formatter)
            webworks_logger.addHandler(handler)
        
        return
    
    def _log_startup(self) -> None:
        """
            Log server startup information.
        """
        _logger.info("Starting WSGI server")
        _logger.info("  Bind: %s", self._get_bind_address())
        _logger.info("  Workers: %d", self._config.workers)
        _logger.info("  Threads: %d", self._config.threads)
        _logger.info("  Timeout: %ds", self._config.timeout)
        _logger.info("  Keep-alive: %ds", self._config.keepalive)
        
        if self._config.reload is True:
            _logger.info("  Development mode: auto-reload enabled")
        
        if self._config.debug is True:
            _logger.info("  Debug mode: enabled")
        
        return

    def log_request(
        self,
        method: str,
        path: str,
        status_code: int,
        elapsed: float,
        client_addr: str = "-"
    ) -> None:
        """
            Log a request in common log format.
            
            :param method: HTTP method.
            :param path: Request path.
            :param status_code: Response status code.
            :param elapsed: Request processing time in seconds.
            :param client_addr: Client IP address.
        """
        if self._config.access_log is not True:
            return
        
        with self._lock:
            self._request_count += 1
        
        timestamp = datetime.now(timezone.utc).strftime("%d/%b/%Y:%H:%M:%S %z")
        
        _logger.info(
            '%s - - [%s] "%s %s" %d %.3fs',
            client_addr,
            timestamp,
            method,
            path,
            status_code,
            elapsed
        )
        
        return


    def _start_reload_watcher(self) -> None:
        """
            Start the file watcher thread for development mode auto-reload.
        """
        if self._reload_thread is not None:
            return
        
        # Initialize watched files with their current signatures
        self._watched_files = self._get_python_file_signatures()
        
        # Start watcher thread
        self._reload_thread = threading.Thread(
            target=self._reload_watcher_loop,
            daemon=True,
            name="wsgi-reload-watcher"
        )
        self._reload_thread.start()
        
        _logger.debug("Started file watcher for auto-reload")
        
        return
    
    def _stop_reload_watcher(self) -> None:
        """
            Stop the file watcher thread.
        """
        if self._reload_thread is None:
            return
        
        # Thread will exit when shutdown_requested is True
        # Wait briefly for thread to finish
        self._reload_thread.join(timeout=1.0)
        self._reload_thread = None
        
        return
    
    def _reload_watcher_loop(self) -> None:
        """
            File watcher loop for development mode.
            
            Checks for file changes every second and sets reload flag if
            changes are detected.
        """
        while not self._shutdown_requested:
            try:
                # Get current file signatures
                current_hashes = self._get_python_file_signatures()
                
                # Check for changes
                if self._files_changed(current_hashes):
                    _logger.info("File changes detected, requesting reload")
                    self._reload_requested = True
                    self._watched_files = current_hashes
                
                # Sleep before next check
                time.sleep(1.0)
                
            except Exception as exc:
                _logger.debug("Error in reload watcher: %s", str(exc))
                time.sleep(1.0)
        
        return
    
    def _get_python_file_signatures(self) -> Dict[str, str]:
        """
            Get signatures of all Python files in the current directory tree.
            
            :returns: Dictionary mapping file paths to their signatures.
        """
        hashes: Dict[str, str] = {}
        
        # Get list of directories to watch
        watch_dirs = self._get_watch_directories()
        
        for watch_dir in watch_dirs:
            if not os.path.isdir(watch_dir):
                continue
            
            for root, dirs, files in os.walk(watch_dir):
                # Skip hidden directories and common non-source directories
                dirs[:] = [
                    d for d in dirs
                    if not d.startswith(".")
                    and d not in ("__pycache__", "node_modules", ".git", ".venv", "venv")
                ]
                
                for filename in files:
                    if filename.endswith(".py"):
                        filepath = os.path.join(root, filename)
                        try:
                            file_hash = self._file_signature(filepath)
                            hashes[filepath] = file_hash
                        except (IOError, OSError):
                            # Skip files that can't be read
                            pass
        
        return hashes
    
    def _get_watch_directories(self) -> List[str]:
        """
            Get list of directories to watch for file changes.
            
            :returns: List of directory paths.
        """
        # Watch current working directory by default
        watch_dirs: List[str] = [os.getcwd()]
        
        # Also watch directories in sys.path that are under cwd
        cwd = os.getcwd()
        for path in sys.path:
            if path and os.path.isdir(path):
                try:
                    if os.path.commonpath([cwd, path]) == cwd:
                        if path not in watch_dirs:
                            watch_dirs.append(path)
                except ValueError:
                    # Different drives on Windows
                    pass
        
        return watch_dirs
    
    def _file_signature(self, filepath: str) -> str:
        """
            Get a signature of a file that changes when the file is saved.
            
            The signature is built from the modification time and the size,
            which the file system already knows. The content of the file is
            not read, the watcher runs once a second over every source file.
            
            :param filepath: Path to the file.
            
            :returns: Signature string of the file.
        """
        file_stat = os.stat(filepath)
        rtnval = f"{file_stat.st_mtime_ns}:{file_stat.st_size}"
        return rtnval
    
    def _files_changed(self, current_hashes: Dict[str, str]) -> bool:
        """
            Check if any watched files have changed.
            
            :param current_hashes: Current file hashes.
            
            :returns: True if files have changed, False otherwise.
        """
        # Check for new or modified files
        for filepath, file_hash in current_hashes.items():
            if filepath not in self._watched_files:
                return True
            if self._watched_files[filepath] != file_hash:
                return True
        
        # Check for deleted files
        for filepath in self._watched_files:
            if filepath not in current_hashes:
                return True
        
        return False
    
    def _handle_reload(self) -> None:
        """
            Handle a reload request.
            
            Stops the workers and starts the server process again from the
            beginning. New workers forked from this process would run the
            modules it imported at startup, so changed code would never be
            loaded. Only a fresh process imports the code again.
        """
        _logger.info("Reloading: restarting the server process to load the changed code")
        
        self._reload_requested = False
        
        if self._worker_manager is not None:
            # Let the workers finish what they are doing
            self._worker_manager.shutdown(graceful=True)
        
        try:
            self._restart_process()
        except OSError as exec_err:
            # The process could not be replaced. Serving the code that is
            # loaded is better than not serving at all.
            _logger.error(
                "Reload failed, the server process could not be restarted: %s",
                str(exec_err)
            )
            if self._worker_manager is not None:
                self._worker_manager.spawn()
        
        return
    
    def _restart_process(self) -> None:
        """
            Replace the server process with a new run of the same command line.
            
            Does not return when it succeeds. The listening socket is closed by
            the operating system when the process is replaced and is bound again
            by the new process.
            
            :raises: OSError if the process could not be replaced.
        """
        arguments = list(sys.orig_argv)
        os.execv(sys.executable, arguments)
        return

    def get_stats(self) -> Dict[str, Any]:
        """
            Get server statistics.
            
            :returns: Dictionary with server statistics.
        """
        stats: Dict[str, Any] = {
            "running": self._running,
            "uptime": self.uptime,
            "request_count": self.request_count,
            "config": {
                "host": self._config.host,
                "port": self._config.port,
                "workers": self._config.workers,
                "threads": self._config.threads,
            },
        }
        
        if self._worker_manager is not None:
            stats["workers"] = self._worker_manager.get_worker_stats()
        
        if self._listener is not None:
            stats["bound_address"] = self._listener.bound_address
        
        return stats


def run_server(
    app: Callable[[Dict[str, Any], Callable], Iterable[bytes]],
    host: str = "127.0.0.1",
    port: int = 8000,
    workers: int = 1,
    threads: int = 1,
    reload: bool = False,
    debug: bool = False,
    **kwargs: Any
) -> None:
    """
        Convenience function to run a WSGI application.
        
        Creates a WSGIServer with the specified configuration and runs it.
        
        :param app: The WSGI application callable.
        :param host: Host address to bind to.
        :param port: Port number to bind to.
        :param workers: Number of worker processes.
        :param threads: Number of threads per worker.
        :param reload: Enable auto-reload on code changes.
        :param debug: Enable debug mode.
        :param kwargs: Additional configuration options.
    """
    config = ServerConfig(
        host=host,
        port=port,
        workers=workers,
        threads=threads,
        reload=reload,
        debug=debug,
        **kwargs
    )
    
    server = WSGIServer(app, config)
    server.serve_forever()
    
    return

