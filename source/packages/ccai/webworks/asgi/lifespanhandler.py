"""
    ASGI Lifespan Handler module.
    
    This module provides the LifespanHandler class that handles ASGI lifespan
    startup/shutdown events. It manages application lifecycle by executing
    registered startup and shutdown handlers in the correct order.
"""

import inspect
import logging
import traceback
from typing import Any, Awaitable, Callable, Dict, List, Optional, Union


# Type alias for lifespan handler functions. A handler is normally an async
# function, a plain function is accepted as well.
LifespanCallable = Callable[[], Union[Awaitable[None], None]]


class LifespanHandler:
    """
        Handles ASGI lifespan startup/shutdown events.
        
        The LifespanHandler manages application lifecycle by receiving lifespan
        events from the ASGI server and executing registered startup and shutdown
        handlers. Startup handlers are executed in registration order, while
        shutdown handlers are executed in reverse registration order.
        
        If a startup handler fails, the application signals startup failure and
        should not accept requests.

        Besides the startup and shutdown handlers an application registers,
        two kinds of callbacks mark when the application starts and stops
        serving (a :class:`WebApplication` uses them to fire its extensions'
        ``on_app_ready`` and ``on_app_shutdown`` hooks):

        * ready callbacks (:meth:`on_ready`) run once every startup handler
          has succeeded, in registration order, before
          ``lifespan.startup.complete`` is sent; requests are still refused
          while they run. A ready callback that raises fails the startup
          like a startup handler.
        * stopping callbacks (:meth:`on_stopping`) run when the shutdown
          event arrives, in registration order, before the shutdown
          handlers, so what they stop can still use what the shutdown
          handlers release. A stopping callback that raises is reported like
          a failing shutdown handler and the rest still run.

        Neither runs while lifespan is disabled.
    """
    
    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        enabled: bool = True,
    ):
        """
            Construct a LifespanHandler instance.
            
            :param logger: Optional logger for error logging. If not provided,
                          a default logger will be created.
            :param enabled: If True, lifespan protocol is enabled and startup/shutdown
                           handlers will be executed. If False, lifespan events are
                           acknowledged but handlers are not executed.
        """
        self._startup_handlers: List[LifespanCallable] = []
        self._shutdown_handlers: List[LifespanCallable] = []
        self._ready_callbacks: List[LifespanCallable] = []
        self._stopping_callbacks: List[LifespanCallable] = []
        self._startup_complete: bool = False
        self._startup_failed: bool = False
        self._startup_in_progress: bool = False
        self._enabled: bool = enabled
        
        if logger is None:
            self._logger = logging.getLogger(__name__)
        else:
            self._logger = logger
        
        return
    
    @property
    def startup_complete(self) -> bool:
        """
            Check if startup has completed successfully.
            
            :returns: True if startup completed without errors.
        """
        return self._startup_complete
    
    @property
    def startup_failed(self) -> bool:
        """
            Check if startup has failed.
            
            :returns: True if startup failed.
        """
        return self._startup_failed
    
    @property
    def startup_in_progress(self) -> bool:
        """
            Check if the startup handlers are running.
            
            :returns: True from the startup event until startup completed or failed.
        """
        return self._startup_in_progress
    
    @property
    def requests_blocked(self) -> bool:
        """
            Check if requests have to be refused.
            
            Requests are refused while the startup handlers are running and
            after one of them failed, because what the request handlers rely
            on has not been set up. A server that does not send lifespan
            events never starts the startup, so nothing is refused there.
            
            :returns: True if requests must be answered with 503.
        """
        rtnval = self._startup_failed or self._startup_in_progress
        return rtnval
    
    @property
    def enabled(self) -> bool:
        """
            Check if lifespan protocol is enabled.
            
            :returns: True if lifespan protocol is enabled.
        """
        return self._enabled
    
    @property
    def startup_handler_count(self) -> int:
        """
            Get the number of registered startup handlers.
            
            :returns: Number of startup handlers.
        """
        return len(self._startup_handlers)
    
    @property
    def shutdown_handler_count(self) -> int:
        """
            Get the number of registered shutdown handlers.
            
            :returns: Number of shutdown handlers.
        """
        return len(self._shutdown_handlers)

    
    def on_startup(
        self,
        handler: LifespanCallable,
    ) -> LifespanCallable:
        """
            Register a startup handler.
            
            Startup handlers are executed in registration order when the
            application receives the "lifespan.startup" event.
            
            Can be used as a decorator:
            
                @lifespan.on_startup
                async def setup_database():
                    await db.connect()
            
            :param handler: Async function to run on startup.
            
            :returns: The handler (for decorator use).
        """
        self._startup_handlers.append(handler)
        return handler
    
    def on_ready(
        self,
        callback: LifespanCallable,
    ) -> LifespanCallable:
        """
            Register a callback that runs once every startup handler has
            succeeded, before the startup is reported complete.

            :param callback: Function (or async function) to run.

            :returns: The callback (for decorator use).
        """
        self._ready_callbacks.append(callback)
        return callback

    def on_stopping(
        self,
        callback: LifespanCallable,
    ) -> LifespanCallable:
        """
            Register a callback that runs when the shutdown event arrives,
            before the shutdown handlers.

            :param callback: Function (or async function) to run.

            :returns: The callback (for decorator use).
        """
        self._stopping_callbacks.append(callback)
        return callback

    def on_shutdown(
        self,
        handler: LifespanCallable,
    ) -> LifespanCallable:
        """
            Register a shutdown handler.
            
            Shutdown handlers are executed in reverse registration order when
            the application receives the "lifespan.shutdown" event.
            
            Can be used as a decorator:
            
                @lifespan.on_shutdown
                async def cleanup_database():
                    await db.disconnect()
            
            :param handler: Async function to run on shutdown.
            
            :returns: The handler (for decorator use).
        """
        self._shutdown_handlers.append(handler)
        return handler
    
    async def handle(
        self,
        scope: Dict[str, Any],
        receive: Callable[[], Awaitable[Dict[str, Any]]],
        send: Callable[[Dict[str, Any]], Awaitable[None]],
    ) -> None:
        """
            Handle lifespan events.
            
            This method processes the lifespan scope by receiving startup and
            shutdown events and executing the appropriate handlers.
            
            :param scope: ASGI lifespan scope dictionary.
            :param receive: Async callable to receive messages.
            :param send: Async callable to send messages.
        """
        while True:
            message = await receive()
            message_type = message.get("type", "")
            
            if message_type == "lifespan.startup":
                await self._run_startup(send)
            elif message_type == "lifespan.shutdown":
                await self._run_shutdown(send)
                return
            else:
                # Unknown message type, ignore
                pass
        
        return
    
    async def _run_startup(
        self,
        send: Callable[[Dict[str, Any]], Awaitable[None]],
    ) -> None:
        """
            Run startup handlers in registration order, then the ready
            callbacks.
            
            If lifespan is disabled, immediately sends "lifespan.startup.complete"
            without executing handlers.
            
            If all handlers succeed, sends "lifespan.startup.complete".
            If any handler fails, sends "lifespan.startup.failed" with the
            error message.
            
            :param send: Async callable to send messages.
        """
        # If lifespan is disabled, just acknowledge startup without running handlers
        if not self._enabled:
            self._startup_complete = True
            self._startup_failed = False
            await send({
                "type": "lifespan.startup.complete",
            })
            return
        
        self._startup_in_progress = True
        
        try:
            for handler in self._startup_handlers:
                await self._call_handler(handler)

            # The application is ready to serve once all of its startup
            # handlers have succeeded.
            for callback in self._ready_callbacks:
                await self._call_handler(callback)
            
            self._startup_complete = True
            self._startup_failed = False
            self._startup_in_progress = False
            
            await send({
                "type": "lifespan.startup.complete",
            })
        except Exception as err:
            self._startup_complete = False
            self._startup_failed = True
            self._startup_in_progress = False
            
            error_message = self._format_error_message(err)
            self._log_startup_error(err)
            
            await send({
                "type": "lifespan.startup.failed",
                "message": error_message,
            })
        
        return
    
    async def _run_shutdown(
        self,
        send: Callable[[Dict[str, Any]], Awaitable[None]],
    ) -> None:
        """
            Run the stopping callbacks, then the shutdown handlers in
            reverse registration order.
            
            If lifespan is disabled, immediately sends "lifespan.shutdown.complete"
            without executing handlers.
            
            Every handler is run, also after one of them failed: a handler
            that raises must not keep the handlers after it from releasing
            what they hold.
            
            If all handlers succeed, sends "lifespan.shutdown.complete".
            If any handler fails, sends "lifespan.shutdown.failed" with the
            error messages of the handlers that failed.
            
            :param send: Async callable to send messages.
        """
        # If lifespan is disabled, just acknowledge shutdown without running handlers
        if not self._enabled:
            await send({
                "type": "lifespan.shutdown.complete",
            })
            return
        
        error_messages: List[str] = []

        # The application stops serving before the shutdown handlers
        # release what it uses.
        for callback in self._stopping_callbacks:
            try:
                await self._call_handler(callback)
            except Exception as err:
                error_messages.append(self._format_error_message(err))
                self._log_shutdown_error(err)
        
        # Execute shutdown handlers in reverse order
        for handler in reversed(self._shutdown_handlers):
            try:
                await self._call_handler(handler)
            except Exception as err:
                error_messages.append(self._format_error_message(err))
                self._log_shutdown_error(err)
        
        if len(error_messages) == 0:
            await send({
                "type": "lifespan.shutdown.complete",
            })
        else:
            await send({
                "type": "lifespan.shutdown.failed",
                "message": "; ".join(error_messages),
            })
        
        return
    
    async def _call_handler(self, handler: LifespanCallable) -> None:
        """
            Call a startup or shutdown handler.
            
            :param handler: Async function, or plain function, to call.
        """
        result = handler()
        
        if inspect.isawaitable(result):
            await result
        
        return
    
    def _format_error_message(self, error: Exception) -> str:
        """
            Format an exception into an error message string.
            
            :param error: The exception to format.
            
            :returns: Formatted error message.
        """
        return f"{type(error).__name__}: {error}"
    
    def _log_startup_error(self, error: Exception) -> None:
        """
            Log a startup error with stack trace.
            
            :param error: The exception that occurred.
        """
        tb_str = traceback.format_exc()
        self._logger.error(
            f"Lifespan startup handler failed: "
            f"{type(error).__name__}: {error}\n{tb_str}"
        )
        return
    
    def _log_shutdown_error(self, error: Exception) -> None:
        """
            Log a shutdown error with stack trace.
            
            :param error: The exception that occurred.
        """
        tb_str = traceback.format_exc()
        self._logger.error(
            f"Lifespan shutdown handler failed: "
            f"{type(error).__name__}: {error}\n{tb_str}"
        )
        return
    
    def can_accept_requests(self) -> bool:
        """
            Check if the application can accept requests.
            
            The application can accept requests only if startup has completed
            successfully. If startup failed or has not been run, requests
            should not be accepted.
            
            :returns: True if the application can accept requests.
        """
        return self._startup_complete and not self._startup_failed

