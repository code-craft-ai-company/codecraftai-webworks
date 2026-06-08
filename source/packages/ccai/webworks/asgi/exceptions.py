"""
    ASGI Layer exceptions module.
    
    This module defines the exception hierarchy for the ASGI layer including
    request body errors, client disconnection, and protocol-specific errors.
"""


class ASGIError(Exception):
    """
        Base exception for ASGI layer errors.
    """
    pass


class ClientDisconnected(ASGIError):
    """
        Client disconnected during request processing.
        
        Raised when the client disconnects while the server is reading
        the request body or processing the request.
    """
    
    def __init__(self, message: str = "Client disconnected"):
        """
            Construct a ClientDisconnected exception.
            
            :param message: Description of the disconnection.
        """
        self._message = message
        super().__init__(message)
        return
    
    @property
    def message(self) -> str:
        """
            Get the disconnection message.
            
            :returns: Disconnection message string.
        """
        return self._message


class RequestEntityTooLarge(ASGIError):
    """
        Request body exceeds configured limit.
        
        Raised when the request body size exceeds the maximum allowed size.
        This results in an HTTP 413 response.
    """
    
    def __init__(self, max_size: int, actual_size: int):
        """
            Construct a RequestEntityTooLarge exception.
            
            :param max_size: Maximum allowed body size in bytes.
            :param actual_size: Actual body size in bytes.
        """
        self._max_size = max_size
        self._actual_size = actual_size
        self._status_code = 413
        message = f"Request body too large: {actual_size} > {max_size}"
        super().__init__(message)
        return
    
    @property
    def status_code(self) -> int:
        """
            Get the HTTP status code.
            
            :returns: HTTP status code (413).
        """
        return self._status_code
    
    @property
    def max_size(self) -> int:
        """
            Get the maximum allowed size.
            
            :returns: Maximum size in bytes.
        """
        return self._max_size
    
    @property
    def actual_size(self) -> int:
        """
            Get the actual body size.
            
            :returns: Actual size in bytes.
        """
        return self._actual_size


class WebSocketError(ASGIError):
    """
        Error during WebSocket handling.
        
        Raised when an error occurs during WebSocket connection handling.
    """
    
    def __init__(self, code: int, reason: str = ""):
        """
            Construct a WebSocketError exception.
            
            :param code: WebSocket close code.
            :param reason: Close reason string.
        """
        self._code = code
        self._reason = reason
        message = f"WebSocket error {code}: {reason}"
        super().__init__(message)
        return
    
    @property
    def code(self) -> int:
        """
            Get the WebSocket close code.
            
            :returns: WebSocket close code.
        """
        return self._code
    
    @property
    def reason(self) -> str:
        """
            Get the close reason.
            
            :returns: Close reason string.
        """
        return self._reason


class LifespanError(ASGIError):
    """
        Error during lifespan handling.
        
        Base exception for lifespan-related errors.
    """
    pass


class StartupError(LifespanError):
    """
        Error during application startup.
        
        Raised when a startup handler fails.
    """
    
    def __init__(self, message: str):
        """
            Construct a StartupError exception.
            
            :param message: Description of the startup failure.
        """
        self._message = message
        super().__init__(message)
        return
    
    @property
    def message(self) -> str:
        """
            Get the error message.
            
            :returns: Error message string.
        """
        return self._message


class ShutdownError(LifespanError):
    """
        Error during application shutdown.
        
        Raised when a shutdown handler fails.
    """
    
    def __init__(self, message: str):
        """
            Construct a ShutdownError exception.
            
            :param message: Description of the shutdown failure.
        """
        self._message = message
        super().__init__(message)
        return
    
    @property
    def message(self) -> str:
        """
            Get the error message.
            
            :returns: Error message string.
        """
        return self._message


class BadRequestBody(ASGIError):
    """
        Request body is malformed.
        
        Raised when the request body cannot be parsed due to invalid
        format, encoding, or structure. Results in HTTP 400 response.
    """
    
    def __init__(self, detail: str):
        """
            Construct a BadRequestBody exception.
            
            :param detail: Description of what is wrong with the body.
        """
        self._detail = detail
        self._status_code = 400
        super().__init__(detail)
        return
    
    @property
    def status_code(self) -> int:
        """
            Get the HTTP status code.
            
            :returns: HTTP status code (400).
        """
        return self._status_code
    
    @property
    def detail(self) -> str:
        """
            Get the error detail.
            
            :returns: Error detail string.
        """
        return self._detail

