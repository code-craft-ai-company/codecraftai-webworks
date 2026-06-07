"""
    WSGI Request Body Parser module.
    
    This module provides the RequestBodyParser class that parses request bodies
    in various formats including raw bytes, form-encoded, multipart, and JSON.
"""

import json
from dataclasses import dataclass
from io import BytesIO
from typing import Any, Dict, IO, Optional, Tuple
from urllib.parse import parse_qs

from ccai.webworks.wsgi.exceptions import BadRequestBody, RequestEntityTooLarge


@dataclass
class UploadedFile:
    """
        Represents an uploaded file from multipart form data.
    """
    
    filename: str
    content_type: str
    content: bytes
    size: int
    
    def save(self, path: str) -> None:
        """
            Save the uploaded file to disk.
            
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



class RequestBodyParser:
    """
        Parses request bodies in various formats.
        
        Supports raw bytes, form-encoded, multipart form data, and JSON bodies.
        Enforces configurable size limits to prevent resource exhaustion.
    """
    
    def __init__(self, max_size: int = 0):
        """
            Construct a body parser.
            
            :param max_size: Maximum body size in bytes (0 = unlimited).
        """
        self._max_size = max_size
        return
    
    @property
    def max_size(self) -> int:
        """
            Get the maximum body size.
            
            :returns: Maximum size in bytes.
        """
        rtnval = self._max_size
        return rtnval
    
    def parse_raw(
        self,
        wsgi_input: IO[bytes],
        content_length: Optional[int]
    ) -> bytes:
        """
            Read raw bytes from wsgi.input.
            
            :param wsgi_input: The wsgi.input file-like object.
            :param content_length: Content-Length header value.
            
            :returns: Raw body bytes.
            
            :raises: RequestEntityTooLarge if body exceeds max_size.
        """
        # Check content length against max size before reading
        if content_length is not None:
            if self._max_size > 0 and content_length > self._max_size:
                raise RequestEntityTooLarge(self._max_size, content_length)
        
        # Determine how many bytes to read
        if content_length is not None:
            bytes_to_read = content_length
        else:
            # No content length, read all available data
            bytes_to_read = -1
        
        # Read the body
        if bytes_to_read == -1:
            # Read all available data, but check size limit
            rtnval = wsgi_input.read()
            if self._max_size > 0 and len(rtnval) > self._max_size:
                raise RequestEntityTooLarge(self._max_size, len(rtnval))
        else:
            rtnval = wsgi_input.read(bytes_to_read)
        
        return rtnval
    
    def parse_form(self, body: bytes, content_type: str) -> Dict[str, str]:
        """
            Parse application/x-www-form-urlencoded body.
            
            :param body: Raw body bytes.
            :param content_type: Content-Type header value.
            
            :returns: Dict of form fields (single values).
            
            :raises: BadRequestBody if body cannot be parsed.
        """
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
            raise BadRequestBody(f"Failed to parse form data: {err}") from err
    
    def parse_form_multi(self, body: bytes, content_type: str) -> Dict[str, list]:
        """
            Parse application/x-www-form-urlencoded body preserving multiple values.
            
            :param body: Raw body bytes.
            :param content_type: Content-Type header value.
            
            :returns: Dict of form fields (lists of values).
            
            :raises: BadRequestBody if body cannot be parsed.
        """
        try:
            # Decode body to string
            body_str = body.decode("utf-8")
            
            # Parse the form data
            rtnval = parse_qs(body_str, keep_blank_values=True)
            
            return rtnval
            
        except UnicodeDecodeError as err:
            raise BadRequestBody(f"Invalid UTF-8 encoding in form data: {err}") from err
        except Exception as err:
            raise BadRequestBody(f"Failed to parse form data: {err}") from err


    def parse_multipart(
        self,
        wsgi_input: IO[bytes],
        content_type: str,
        content_length: Optional[int]
    ) -> Tuple[Dict[str, str], Dict[str, UploadedFile]]:
        """
            Parse multipart/form-data body.
            
            :param wsgi_input: The wsgi.input file-like object.
            :param content_type: Content-Type header with boundary.
            :param content_length: Content-Length header value.
            
            :returns: Tuple of (form_fields, uploaded_files).
            
            :raises: BadRequestBody if body cannot be parsed.
            :raises: RequestEntityTooLarge if body exceeds max_size.
        """
        # Extract boundary from content type
        boundary = self._extract_boundary(content_type)
        if boundary is None:
            raise BadRequestBody("Missing boundary in multipart/form-data Content-Type")
        
        # Read the raw body first (with size checking)
        body = self.parse_raw(wsgi_input, content_length)
        
        # Parse the multipart data
        form_fields: Dict[str, str] = {}
        uploaded_files: Dict[str, UploadedFile] = {}
        
        # Split by boundary
        boundary_bytes = b"--" + boundary.encode("utf-8")
        parts = body.split(boundary_bytes)
        
        # Skip the first empty part and the last closing part
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


    def parse_json(self, body: bytes) -> Any:
        """
            Parse application/json body.
            
            :param body: Raw body bytes.
            
            :returns: Parsed JSON value.
            
            :raises: BadRequestBody if JSON is invalid.
        """
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
            raise BadRequestBody(f"Failed to parse JSON body: {err}") from err
    
    def parse(
        self,
        wsgi_input: IO[bytes],
        content_type: Optional[str],
        content_length: Optional[int]
    ) -> Tuple[bytes, Optional[Any]]:
        """
            Parse request body based on content type.
            
            :param wsgi_input: The wsgi.input file-like object.
            :param content_type: Content-Type header value.
            :param content_length: Content-Length header value.
            
            :returns: Tuple of (raw_body, parsed_data).
                      parsed_data is None for unknown content types.
            
            :raises: BadRequestBody if body cannot be parsed.
            :raises: RequestEntityTooLarge if body exceeds max_size.
        """
        # Read raw body first
        raw_body = self.parse_raw(wsgi_input, content_length)
        
        # If no content type, return raw body only
        if content_type is None:
            rtnval = (raw_body, None)
            return rtnval
        
        # Normalize content type (remove parameters for comparison)
        content_type_lower = content_type.lower().split(";")[0].strip()
        
        parsed_data: Optional[Any] = None
        
        if content_type_lower == "application/x-www-form-urlencoded":
            parsed_data = self.parse_form(raw_body, content_type)
        elif content_type_lower == "application/json":
            parsed_data = self.parse_json(raw_body)
        elif content_type_lower == "multipart/form-data":
            # For multipart, we need to re-parse from the raw body
            # Create a new BytesIO from the raw body
            form_fields, uploaded_files = self.parse_multipart(
                BytesIO(raw_body),
                content_type,
                len(raw_body)
            )
            parsed_data = {"fields": form_fields, "files": uploaded_files}
        
        rtnval = (raw_body, parsed_data)
        return rtnval
    
    def encode_form(self, data: Dict[str, str]) -> bytes:
        """
            Encode form data to application/x-www-form-urlencoded format.
            
            :param data: Dict of form fields.
            
            :returns: Encoded form data as bytes.
        """
        from urllib.parse import urlencode
        
        encoded = urlencode(data)
        rtnval = encoded.encode("utf-8")
        return rtnval
    
    def encode_json(self, data: Any) -> bytes:
        """
            Encode data to JSON format.
            
            :param data: Data to encode.
            
            :returns: JSON encoded data as bytes.
        """
        encoded = json.dumps(data)
        rtnval = encoded.encode("utf-8")
        return rtnval
    
    def encode_multipart(
        self,
        fields: Dict[str, str],
        files: Optional[Dict[str, UploadedFile]] = None,
        boundary: Optional[str] = None
    ) -> Tuple[bytes, str]:
        """
            Encode data to multipart/form-data format.
            
            :param fields: Dict of form fields.
            :param files: Dict of uploaded files.
            :param boundary: Optional boundary string (generated if not provided).
            
            :returns: Tuple of (encoded_body, boundary).
        """
        import uuid
        
        if boundary is None:
            boundary = f"----WebWorksFormBoundary{uuid.uuid4().hex}"
        
        parts: list = []
        boundary_bytes = boundary.encode("utf-8")
        
        # Add form fields
        for name, value in fields.items():
            part = b"--" + boundary_bytes + b"\r\n"
            part += f'Content-Disposition: form-data; name="{name}"\r\n'.encode("utf-8")
            part += b"\r\n"
            part += value.encode("utf-8")
            parts.append(part)
        
        # Add files
        if files is not None:
            for name, uploaded_file in files.items():
                part = b"--" + boundary_bytes + b"\r\n"
                part += f'Content-Disposition: form-data; name="{name}"; filename="{uploaded_file.filename}"\r\n'.encode("utf-8")
                part += f"Content-Type: {uploaded_file.content_type}\r\n".encode("utf-8")
                part += b"\r\n"
                part += uploaded_file.content
                parts.append(part)
        
        # Join parts with CRLF and add closing boundary
        body = b"\r\n".join(parts)
        if len(parts) > 0:
            body += b"\r\n"
        body += b"--" + boundary_bytes + b"--\r\n"
        
        rtnval = (body, boundary)
        return rtnval
