"""
    WSGI Layer exceptions module.
    
    This module defines the exception hierarchy for the WSGI layer including
    request parsing errors, body size limits, and server errors.
"""


class WSGIError(Exception):
    """
        Base exception for WSGI layer errors.
    """
    pass


class HTTPException(WSGIError):
    """
        Base exception for HTTP-related errors that should result in
        specific HTTP status codes.
    """
    
    def __init__(self, status_code: int, message: str):
        """
            Construct an HTTP exception.
            
            :param status_code: HTTP status code to return.
            :param message: Error message.
        """
        self._status_code = status_code
        self._message = message
        super().__init__(message)
        return
    
    @property
    def status_code(self) -> int:
        """
            Get the HTTP status code.
            
            :returns: HTTP status code.
        """
        return self._status_code
    
    @property
    def message(self) -> str:
        """
            Get the error message.
            
            :returns: Error message string.
        """
        return self._message


class RequestEntityTooLarge(HTTPException):
    """
        Request body exceeds configured limit.
        
        Raised when the request body size exceeds the maximum allowed size.
    """
    
    def __init__(self, max_size: int, actual_size: int):
        """
            Construct a RequestEntityTooLarge exception.
            
            :param max_size: Maximum allowed body size in bytes.
            :param actual_size: Actual body size in bytes.
        """
        self._max_size = max_size
        self._actual_size = actual_size
        message = f"Request body too large: {actual_size} > {max_size}"
        super().__init__(413, message)
        return
    
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


class BadRequestBody(HTTPException):
    """
        Request body is malformed.
        
        Raised when the request body cannot be parsed or is invalid.
    """
    
    def __init__(self, detail: str):
        """
            Construct a BadRequestBody exception.
            
            :param detail: Description of what is wrong with the body.
        """
        message = f"Bad request body: {detail}"
        super().__init__(400, message)
        return


class RequestParseError(HTTPException):
    """
        Failed to parse HTTP request.
        
        Raised when the HTTP request is malformed.
    """
    
    def __init__(self, detail: str):
        """
            Construct a RequestParseError exception.
            
            :param detail: Description of the parse error.
        """
        message = f"Bad request: {detail}"
        super().__init__(400, message)
        return


class HeaderTooLarge(RequestParseError):
    """
        Request headers exceed size limit.
        
        Raised when the total header size exceeds the maximum allowed.
    """
    
    def __init__(self, max_size: int):
        """
            Construct a HeaderTooLarge exception.
            
            :param max_size: Maximum allowed header size in bytes.
        """
        detail = f"Headers exceed maximum size of {max_size} bytes"
        super().__init__(detail)
        return


class TooManyHeaders(RequestParseError):
    """
        Too many request headers.
        
        Raised when the number of headers exceeds the maximum allowed.
    """
    
    def __init__(self, max_headers: int):
        """
            Construct a TooManyHeaders exception.
            
            :param max_headers: Maximum allowed number of headers.
        """
        detail = f"Request has more than {max_headers} headers"
        super().__init__(detail)
        return


class RequestTimeout(HTTPException):
    """
        Request processing timed out.
        
        Raised when request processing exceeds the timeout limit.
    """
    
    def __init__(self, timeout: int):
        """
            Construct a RequestTimeout exception.
            
            :param timeout: Timeout value in seconds.
        """
        message = f"Request timeout after {timeout} seconds"
        super().__init__(408, message)
        return


class ServerError(WSGIError):
    """
        Base exception for server errors.
    """
    pass


class BindError(ServerError):
    """
        Failed to bind to address.
        
        Raised when the server cannot bind to the specified address.
    """
    
    def __init__(self, address: str, detail: str):
        """
            Construct a BindError exception.
            
            :param address: Address that failed to bind.
            :param detail: Description of the bind failure.
        """
        self._address = address
        message = f"Failed to bind to {address}: {detail}"
        super().__init__(message)
        return
    
    @property
    def address(self) -> str:
        """
            Get the address that failed to bind.
            
            :returns: Address string.
        """
        return self._address


class WorkerError(ServerError):
    """
        Worker process error.
        
        Raised when a worker process encounters an error.
    """
    
    def __init__(self, worker_id: int, detail: str):
        """
            Construct a WorkerError exception.
            
            :param worker_id: ID of the worker that encountered the error.
            :param detail: Description of the error.
        """
        self._worker_id = worker_id
        message = f"Worker {worker_id} error: {detail}"
        super().__init__(message)
        return
    
    @property
    def worker_id(self) -> int:
        """
            Get the worker ID.
            
            :returns: Worker ID.
        """
        return self._worker_id
