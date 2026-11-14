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
    
    def __init__(self, detail: str, status_code: int = 400):
        """
            Construct a RequestParseError exception.
            
            :param detail: Description of the parse error.
            :param status_code: HTTP status code the server answers with.
        """
        message = f"Bad request: {detail}"
        super().__init__(status_code, message)
        return


class RequestLineTooLong(RequestParseError):
    """
        Request line exceeds the size limit.
        
        Raised while the request line is being read, as soon as it is longer
        than the maximum allowed. Answered with 414 URI Too Long.
    """
    
    def __init__(self, max_size: int):
        """
            Construct a RequestLineTooLong exception.
            
            :param max_size: Maximum allowed request line size in bytes.
        """
        detail = f"Request line exceeds maximum size of {max_size} bytes"
        super().__init__(detail, status_code=414)
        return


class HeaderTooLarge(RequestParseError):
    """
        Request headers exceed size limit.
        
        Raised when the total header size exceeds the maximum allowed.
        Answered with 431 Request Header Fields Too Large.
    """
    
    def __init__(self, max_size: int):
        """
            Construct a HeaderTooLarge exception.
            
            :param max_size: Maximum allowed header size in bytes.
        """
        detail = f"Headers exceed maximum size of {max_size} bytes"
        super().__init__(detail, status_code=431)
        return


class TooManyHeaders(RequestParseError):
    """
        Too many request headers.
        
        Raised when the number of headers exceeds the maximum allowed.
        Answered with 431 Request Header Fields Too Large.
    """
    
    def __init__(self, max_headers: int):
        """
            Construct a TooManyHeaders exception.
            
            :param max_headers: Maximum allowed number of headers.
        """
        detail = f"Request has more than {max_headers} headers"
        super().__init__(detail, status_code=431)
        return


class IncompleteRequest(RequestParseError):
    """
        The client closed the connection part way through a request.
        
        Raised when the stream ends inside the request line, the headers or
        the body. A request that was cut short must never be handed to the
        application.
    """
    
    def __init__(self, detail: str):
        """
            Construct an IncompleteRequest exception.
            
            :param detail: Description of where the request was cut short.
        """
        super().__init__(detail, status_code=400)
        return


class ConnectionClosed(WSGIError):
    """
        The client closed the connection before sending a request.
        
        This is the normal end of a keep-alive connection. It is not an
        error of the client and is not answered with a response.
    """
    
    def __init__(self, detail: str = "Connection closed by the client"):
        """
            Construct a ConnectionClosed exception.
            
            :param detail: Description of the condition.
        """
        self._detail = detail
        super().__init__(detail)
        return
    
    @property
    def detail(self) -> str:
        """
            Get the description of the condition.
            
            :returns: Description string.
        """
        return self._detail


class LineTooLong(WSGIError):
    """
        A line read from a connection is longer than the caller allowed.
        
        Raised by the socket reader as soon as the limit is passed, so the
        bytes of an over-long line are never accumulated. The HTTP parser
        reclassifies this into the error that matches what was being read.
    """
    
    def __init__(self, max_size: int):
        """
            Construct a LineTooLong exception.
            
            :param max_size: Maximum allowed line size in bytes.
        """
        self._max_size = max_size
        message = f"Line exceeds maximum size of {max_size} bytes"
        super().__init__(message)
        return
    
    @property
    def max_size(self) -> int:
        """
            Get the maximum allowed line size.
            
            :returns: Maximum size in bytes.
        """
        return self._max_size


class InvalidResponseHeader(WSGIError, ValueError):
    """
        A response status line or header is not safe to put on the wire.
        
        Raised when an application supplies a status, header name or header
        value that contains CR, LF or NUL, or a header name that is not an
        HTTP token. Writing such a value would let whoever controls it inject
        headers or a second response.
    """
    
    def __init__(self, detail: str):
        """
            Construct an InvalidResponseHeader exception.
            
            :param detail: Description of what is wrong with the header.
        """
        self._detail = detail
        message = f"Invalid response header: {detail}"
        super().__init__(message)
        return
    
    @property
    def detail(self) -> str:
        """
            Get the description of what is wrong.
            
            :returns: Description string.
        """
        return self._detail


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


class WorkerBootError(WorkerError):
    """
        A worker process could not start serving.
        
        Raised when preparing the application in a new worker process fails,
        for example when the application cannot be loaded there. A worker
        that fails to boot ends with WORKER_BOOT_ERROR_EXIT_CODE, and the
        server stops instead of starting replacement workers that would fail
        the same way.
    """
    pass


class IncompleteResponse(WSGIError):
    """
        A response ended before all of it was produced.
        
        Raised from the body iterator of a response when the application
        stopped after it had started the response but before it sent the
        last part of the body. The server closes the connection, which is
        how the client learns that the response was cut short.
    """
    pass
