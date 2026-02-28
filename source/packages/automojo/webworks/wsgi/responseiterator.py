"""
    WSGI Response Iterator module.
    
    This module provides the ResponseIterator class that implements the WSGI
    response iterator protocol per PEP 3333. It yields body chunks as bytes
    and handles resource cleanup via the close() method.
"""

from typing import Any, Callable, Generator, IO, Iterable, Iterator, List, Optional, Union


class ResponseIterator:
    """
        WSGI response iterator that yields body chunks and handles cleanup.
        
        Implements the iterator protocol and close() method per PEP 3333.
        Supports bytes, lists, generators, and file-like objects as content sources.
    """
    
    DEFAULT_CHUNK_SIZE = 8192
    
    def __init__(
        self,
        content: Union[bytes, Iterable[bytes], Generator[bytes, None, None], IO[bytes]],
        close_callback: Optional[Callable[[], None]] = None
    ):
        """
            Construct a response iterator.
            
            :param content: Response body content (bytes, iterable, generator, or file).
            :param close_callback: Optional callback to invoke on close().
        """
        self._close_callback = close_callback
        self._closed = False
        self._file_handle: Optional[IO[bytes]] = None
        self._iterator: Optional[Iterator[bytes]] = None
        
        # Determine content type and set up iterator
        if isinstance(content, bytes):
            # Single bytes object - wrap in list
            self._iterator = iter([content])
        elif hasattr(content, "read"):
            # File-like object
            self._file_handle = content  # type: ignore
            self._iterator = self._file_iterator(content, self.DEFAULT_CHUNK_SIZE)  # type: ignore
        elif hasattr(content, "__iter__"):
            # Iterable or generator
            self._iterator = iter(content)  # type: ignore
        else:
            errmsg = f"Unsupported content type: {type(content)}"
            raise TypeError(errmsg)
        
        return
    
    def _file_iterator(self, file_obj: IO[bytes], chunk_size: int) -> Generator[bytes, None, None]:
        """
            Create an iterator that reads from a file in chunks.
            
            :param file_obj: File-like object to read from.
            :param chunk_size: Size of chunks to yield.
            
            :yields: Bytes chunks from the file.
        """
        while True:
            chunk = file_obj.read(chunk_size)
            if chunk is None or len(chunk) == 0:
                break
            yield chunk
        
        return
    
    def __iter__(self) -> "ResponseIterator":
        """
            Return self as iterator.
            
            :returns: Self.
        """
        return self
    
    def __next__(self) -> bytes:
        """
            Yield next body chunk.
            
            :returns: Next bytes chunk.
            
            :raises: StopIteration when iteration is complete.
            :raises: RuntimeError if iterator is closed.
        """
        if self._closed:
            errmsg = "Cannot iterate over closed ResponseIterator"
            raise RuntimeError(errmsg)
        
        if self._iterator is None:
            raise StopIteration
        
        try:
            chunk = next(self._iterator)
            
            # Ensure chunk is bytes
            if not isinstance(chunk, bytes):
                if isinstance(chunk, str):
                    chunk = chunk.encode("utf-8")
                else:
                    errmsg = f"ResponseIterator yielded non-bytes content: {type(chunk)}"
                    raise TypeError(errmsg)
            
            rtnval = chunk
            return rtnval
        except StopIteration:
            raise
        
        return
    
    def close(self) -> None:
        """
            Clean up resources.
            
            Closes file handles, releases resources, and invokes close_callback.
        """
        if self._closed:
            return
        
        self._closed = True
        
        # Close file handle if present
        if self._file_handle is not None:
            try:
                self._file_handle.close()
            except Exception:
                # Ignore errors during close
                pass
            self._file_handle = None
        
        # Invoke close callback if provided
        if self._close_callback is not None:
            try:
                self._close_callback()
            except Exception:
                # Ignore errors during callback
                pass
        
        # Clear iterator reference
        self._iterator = None
        
        return
    
    @property
    def closed(self) -> bool:
        """
            Check if the iterator has been closed.
            
            :returns: True if closed, False otherwise.
        """
        return self._closed
    
    @classmethod
    def from_bytes(cls, data: bytes) -> "ResponseIterator":
        """
            Create iterator from bytes.
            
            :param data: Bytes data to iterate over.
            
            :returns: ResponseIterator instance.
        """
        rtnval = cls([data])
        return rtnval
    
    @classmethod
    def from_generator(
        cls,
        gen: Generator[bytes, None, None],
        close_callback: Optional[Callable[[], None]] = None
    ) -> "ResponseIterator":
        """
            Create iterator from generator.
            
            :param gen: Generator yielding bytes.
            :param close_callback: Optional callback to invoke on close().
            
            :returns: ResponseIterator instance.
        """
        rtnval = cls(gen, close_callback=close_callback)
        return rtnval
    
    @classmethod
    def from_file(
        cls,
        file_obj: IO[bytes],
        chunk_size: int = 8192,
        close_callback: Optional[Callable[[], None]] = None
    ) -> "ResponseIterator":
        """
            Create iterator from file-like object.
            
            :param file_obj: File-like object to read from.
            :param chunk_size: Size of chunks to yield.
            :param close_callback: Optional callback to invoke on close().
            
            :returns: ResponseIterator instance.
        """
        # Create a custom iterator that uses the specified chunk size
        instance = cls.__new__(cls)
        instance._close_callback = close_callback
        instance._closed = False
        instance._file_handle = file_obj
        instance._iterator = instance._file_iterator(file_obj, chunk_size)
        
        rtnval = instance
        return rtnval
    
    @classmethod
    def empty(cls) -> "ResponseIterator":
        """
            Create an empty iterator.
            
            :returns: ResponseIterator instance that yields nothing.
        """
        rtnval = cls([])
        return rtnval

