"""
    ASGI Body Reader module.
    
    This module provides the BodyReader class that reads request bodies
    from ASGI receive callables, supporting both buffered and streaming
    body reading with size limits and disconnection handling.
    
    Also provides async body parsing for form-encoded, multipart, and JSON
    request bodies.
"""

import json
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Awaitable, Callable, Dict, Optional, Tuple
from urllib.parse import parse_qs

from ccai.webworks.asgi.constants import (
    MESSAGE_HTTP_REQUEST,
    MESSAGE_HTTP_DISCONNECT,
)
from ccai.webworks.asgi.exceptions import (
    BadRequestBody,
    ClientDisconnected,
    RequestEntityTooLarge,
)


@dataclass
class UploadedFile:
    """
        Represents an uploaded file from multipart form data.
        
        This dataclass holds the metadata and content of a file uploaded
        via multipart/form-data encoding.
    """
    
    filename: str
    content_type: str
    content: bytes
    size: int
    
    async def save(self, path: str) -> None:
        """
            Save the uploaded file to disk asynchronously.
            
            Note: This performs synchronous file I/O. For true async file
            operations, consider using aiofiles or similar library.
            
            :param path: File path to save to.
        """
        with open(path, "wb") as file_handle:
            file_handle.write(self.content)
        return
    
    def read(self) -> bytes:
        """
            Read the file content.
            
            :returns: File content as bytes.
        """
        rtnval = self.content
        return rtnval


class BodyReader:
    """
        Reads request body from ASGI receive callable.
        
        This class provides methods to read request bodies either as a
        complete buffer or as a stream of chunks. It supports size limiting
        and handles client disconnection gracefully.
    """
    
    def __init__(self, max_size: int = 0):
        """
            Construct a BodyReader instance.
            
            :param max_size: Maximum body size in bytes. 0 means unlimited.
        """
        self._max_size = max_size
        return
    
    @property
    def max_size(self) -> int:
        """
            Get the maximum body size.
            
            :returns: Maximum size in bytes, 0 for unlimited.
        """
        return self._max_size
    
    async def read(
        self,
        receive: Callable[[], Awaitable[Dict[str, Any]]],
        content_length: Optional[int] = None
    ) -> bytes:
        """
            Read the complete request body.
            
            This method accumulates all body chunks from the receive callable
            until more_body is False, returning the complete body as bytes.
            
            :param receive: ASGI receive callable.
            :param content_length: Expected content length (optional).
            
            :returns: Complete body as bytes.
            
            :raises RequestEntityTooLarge: If body exceeds max_size.
            :raises ClientDisconnected: If client disconnects during read.
        """
        body_parts: list[bytes] = []
        total_size = 0
        
        # Check content_length against max_size before reading
        if self._max_size > 0:
            if content_length is not None and content_length > self._max_size:
                raise RequestEntityTooLarge(
                    max_size=self._max_size,
                    actual_size=content_length
                )
        
        while True:
            message = await receive()
            message_type = message.get("type", "")
            
            # Check for client disconnection
            if message_type == MESSAGE_HTTP_DISCONNECT:
                raise ClientDisconnected("Client disconnected during body reading")
            
            # Process body chunk
            if message_type == MESSAGE_HTTP_REQUEST:
                body_chunk = message.get("body", b"")
                
                if isinstance(body_chunk, bytes) and len(body_chunk) > 0:
                    chunk_size = len(body_chunk)
                    total_size = total_size + chunk_size
                    
                    # Check size limit
                    if self._max_size > 0 and total_size > self._max_size:
                        raise RequestEntityTooLarge(
                            max_size=self._max_size,
                            actual_size=total_size
                        )
                    
                    body_parts.append(body_chunk)
                
                # Check if more body chunks are expected
                more_body = message.get("more_body", False)
                if not more_body:
                    break
            else:
                # Unknown message type, continue waiting for body
                # This handles edge cases where other message types arrive
                continue
        
        # Combine all body parts
        if len(body_parts) == 0:
            rtnval = b""
        elif len(body_parts) == 1:
            rtnval = body_parts[0]
        else:
            rtnval = b"".join(body_parts)
        
        return rtnval
    
    async def stream(
        self,
        receive: Callable[[], Awaitable[Dict[str, Any]]]
    ) -> AsyncGenerator[bytes, None]:
        """
            Stream request body chunks.
            
            This method yields body chunks as they are received, allowing
            processing without buffering the entire body in memory.
            
            :param receive: ASGI receive callable.
            
            :yields: Body chunks as bytes.
            
            :raises RequestEntityTooLarge: If body exceeds max_size.
            :raises ClientDisconnected: If client disconnects during read.
        """
        total_size = 0
        
        while True:
            message = await receive()
            message_type = message.get("type", "")
            
            # Check for client disconnection
            if message_type == MESSAGE_HTTP_DISCONNECT:
                raise ClientDisconnected("Client disconnected during body streaming")
            
            # Process body chunk
            if message_type == MESSAGE_HTTP_REQUEST:
                body_chunk = message.get("body", b"")
                
                if isinstance(body_chunk, bytes) and len(body_chunk) > 0:
                    chunk_size = len(body_chunk)
                    total_size = total_size + chunk_size
                    
                    # Check size limit
                    if self._max_size > 0 and total_size > self._max_size:
                        raise RequestEntityTooLarge(
                            max_size=self._max_size,
                            actual_size=total_size
                        )
                    
                    yield body_chunk
                
                # Check if more body chunks are expected
                more_body = message.get("more_body", False)
                if not more_body:
                    break
            else:
                # Unknown message type, continue waiting for body
                continue
        
        return
    
    async def read_form(
        self,
        receive: Callable[[], Awaitable[Dict[str, Any]]],
        content_type: str
    ) -> Dict[str, str]:
        """
            Parse application/x-www-form-urlencoded body asynchronously.
            
            Reads the complete body and parses it as URL-encoded form data.
            
            :param receive: ASGI receive callable.
            :param content_type: Content-Type header value.
            
            :returns: Dict of form field names to values (single values).
            
            :raises BadRequestBody: If body cannot be parsed.
            :raises ClientDisconnected: If client disconnects during read.
            :raises RequestEntityTooLarge: If body exceeds max_size.
        """
        # Read the complete body
        body = await self.read(receive)
        
        try:
            # Decode body to string
            body_str = body.decode("utf-8")
            
            # Parse the form data
            parsed = parse_qs(body_str, keep_blank_values=True)
            
            # Convert to single values (take first value for each key)
            rtnval: Dict[str, str] = {}
            for key, values in parsed.items():
                if len(values) > 0:
                    rtnval[key] = values[0]
                else:
                    rtnval[key] = ""
            
            return rtnval
            
        except UnicodeDecodeError as err:
            raise BadRequestBody(f"Invalid UTF-8 encoding in form data: {err}") from err
        except Exception as err:
            if isinstance(err, BadRequestBody):
                raise
            raise BadRequestBody(f"Failed to parse form data: {err}") from err


    async def read_multipart(
        self,
        receive: Callable[[], Awaitable[Dict[str, Any]]],
        content_type: str
    ) -> Tuple[Dict[str, str], Dict[str, UploadedFile]]:
        """
            Parse multipart/form-data body asynchronously.
            
            Reads the complete body and parses it as multipart form data,
            extracting both regular form fields and uploaded files.
            
            :param receive: ASGI receive callable.
            :param content_type: Content-Type header with boundary parameter.
            
            :returns: Tuple of (form_fields, uploaded_files).
            
            :raises BadRequestBody: If body cannot be parsed.
            :raises ClientDisconnected: If client disconnects during read.
            :raises RequestEntityTooLarge: If body exceeds max_size.
        """
        # Extract boundary from content type
        boundary = self._extract_boundary(content_type)
        if boundary is None:
            raise BadRequestBody("Missing boundary in multipart/form-data Content-Type")
        
        # Read the complete body
        body = await self.read(receive)
        
        # Parse the multipart data
        form_fields: Dict[str, str] = {}
        uploaded_files: Dict[str, UploadedFile] = {}
        
        # Split by boundary
        boundary_bytes = b"--" + boundary.encode("utf-8")
        parts = body.split(boundary_bytes)
        
        # Skip the first empty part and process remaining parts
        for part in parts[1:]:
            # Check for closing boundary
            if part.startswith(b"--"):
                continue
            
            # Strip leading CRLF
            if part.startswith(b"\r\n"):
                part = part[2:]
            
            # Find the header/body separator
            separator_pos = part.find(b"\r\n\r\n")
            if separator_pos == -1:
                continue
            
            headers_section = part[:separator_pos]
            body_section = part[separator_pos + 4:]
            
            # Remove trailing CRLF from body
            if body_section.endswith(b"\r\n"):
                body_section = body_section[:-2]
            
            # Parse part headers
            part_headers = self._parse_part_headers(headers_section)
            
            # Extract content disposition
            content_disposition = part_headers.get("content-disposition", "")
            disposition_params = self._parse_content_disposition(content_disposition)
            
            field_name = disposition_params.get("name")
            if field_name is None:
                continue
            
            filename = disposition_params.get("filename")
            
            if filename is not None:
                # This is a file upload
                part_content_type = part_headers.get("content-type", "application/octet-stream")
                uploaded_file = UploadedFile(
                    filename=filename,
                    content_type=part_content_type,
                    content=body_section,
                    size=len(body_section)
                )
                uploaded_files[field_name] = uploaded_file
            else:
                # This is a regular form field
                try:
                    form_fields[field_name] = body_section.decode("utf-8")
                except UnicodeDecodeError:
                    form_fields[field_name] = body_section.decode("latin-1")
        
        rtnval = (form_fields, uploaded_files)
        return rtnval
    
    def _extract_boundary(self, content_type: str) -> Optional[str]:
        """
            Extract boundary parameter from Content-Type header.
            
            :param content_type: Content-Type header value.
            
            :returns: Boundary string or None if not found.
        """
        rtnval: Optional[str] = None
        
        parts = content_type.split(";")
        for part in parts[1:]:
            part = part.strip()
            if part.lower().startswith("boundary="):
                boundary_value = part[9:]
                # Remove quotes if present
                if boundary_value.startswith('"') and boundary_value.endswith('"'):
                    boundary_value = boundary_value[1:-1]
                rtnval = boundary_value
                break
        
        return rtnval
    
    def _parse_part_headers(self, headers_section: bytes) -> Dict[str, str]:
        """
            Parse headers from a multipart part.
            
            :param headers_section: Raw header bytes.
            
            :returns: Dict of header names (lowercase) to values.
        """
        rtnval: Dict[str, str] = {}
        
        try:
            headers_str = headers_section.decode("utf-8")
        except UnicodeDecodeError:
            headers_str = headers_section.decode("latin-1")
        
        lines = headers_str.split("\r\n")
        for line in lines:
            if ":" in line:
                name, value = line.split(":", 1)
                rtnval[name.strip().lower()] = value.strip()
        
        return rtnval
    
    def _parse_content_disposition(self, disposition: str) -> Dict[str, str]:
        """
            Parse Content-Disposition header value.
            
            :param disposition: Content-Disposition header value.
            
            :returns: Dict of parameter names to values.
        """
        rtnval: Dict[str, str] = {}
        
        parts = disposition.split(";")
        for part in parts[1:]:
            part = part.strip()
            if "=" in part:
                name, value = part.split("=", 1)
                name = name.strip()
                value = value.strip()
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                rtnval[name] = value
        
        return rtnval
    
    async def read_json(
        self,
        receive: Callable[[], Awaitable[Dict[str, Any]]]
    ) -> Any:
        """
            Parse application/json body asynchronously.
            
            Reads the complete body and parses it as JSON.
            
            :param receive: ASGI receive callable.
            
            :returns: Parsed JSON value.
            
            :raises BadRequestBody: If JSON is invalid.
            :raises ClientDisconnected: If client disconnects during read.
            :raises RequestEntityTooLarge: If body exceeds max_size.
        """
        # Read the complete body
        body = await self.read(receive)
        
        try:
            # Decode body to string
            body_str = body.decode("utf-8")
            
            # Parse JSON
            rtnval = json.loads(body_str)
            
            return rtnval
            
        except UnicodeDecodeError as err:
            raise BadRequestBody(f"Invalid UTF-8 encoding in JSON body: {err}") from err
        except json.JSONDecodeError as err:
            raise BadRequestBody(f"Invalid JSON: {err}") from err
        except Exception as err:
            if isinstance(err, BadRequestBody):
                raise
            raise BadRequestBody(f"Failed to parse JSON body: {err}") from err
