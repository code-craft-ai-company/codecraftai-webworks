"""
    Response module.
    
    This module provides the Response class and its subclasses for building
    HTTP responses with status codes, headers, and body content.
    
    The Response class provides a clean abstraction over WSGI/ASGI response
    formats, allowing handlers to build responses without dealing with
    protocol-specific details.
"""

import json
from http.cookies import SimpleCookie
from typing import Any, AsyncIterable, AsyncIterator, Dict, Iterable, Iterator, List, Optional, Tuple, Union


# HTTP status phrases for common status codes
HTTP_STATUS_PHRASES: Dict[int, str] = {
    100: "Continue",
    101: "Switching Protocols",
    200: "OK",
    201: "Created",
    202: "Accepted",
    204: "No Content",
    301: "Moved Permanently",
    302: "Found",
    303: "See Other",
    304: "Not Modified",
    307: "Temporary Redirect",
    308: "Permanent Redirect",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    406: "Not Acceptable",
    408: "Request Timeout",
    409: "Conflict",
    410: "Gone",
    413: "Payload Too Large",
    415: "Unsupported Media Type",
    422: "Unprocessable Entity",
    429: "Too Many Requests",
    500: "Internal Server Error",
    501: "Not Implemented",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout",
}


# Characters that end a header line or a C string. A header name or value
# that carries one can start a second header or split the response, so
# none is ever stored on a response.
_FORBIDDEN_HEADER_CHARS: Tuple[str, ...] = ("\r", "\n", "\x00")

# Cookie name prefixes that browsers only honour on cookies set with the
# Secure attribute.
_SECURE_COOKIE_PREFIXES: Tuple[str, ...] = ("__Host-", "__Secure-")


def validate_header(name: Any, value: Any) -> None:
    """
        Verify that a header name and value are safe to write to the wire.

        :param name: The header name.
        :param value: The header value.

        :raises ValueError: When the name is empty, or the name or the
            value contains a carriage return, a line feed or a NUL
            character.
    """
    name_text = str(name)
    value_text = str(value)

    if name_text == "":
        raise ValueError("A response header name must not be empty.")

    for forbidden in _FORBIDDEN_HEADER_CHARS:
        if forbidden in name_text:
            errmsg = (
                f"Response header name {name_text!r} contains a CR, LF or NUL character."
            )
            raise ValueError(errmsg)

        if forbidden in value_text:
            errmsg = (
                f"The value of response header {name_text!r} contains a CR, LF or NUL "
                f"character; header values must be a single line."
            )
            raise ValueError(errmsg)

    return


class ResponseHeaders(dict):
    """
        The header mapping of a :class:`Response`.

        A ``dict`` that refuses names and values carrying CR, LF or NUL,
        whichever way they are stored -- ``set_header``, the constructor,
        item assignment, ``update`` or ``setdefault``.
    """

    def __init__(self, *args: Any, **kwargs: Any):
        """
            Construct the mapping, validating every initial header.

            :param args: Positional arguments accepted by ``dict``.
            :param kwargs: Keyword arguments accepted by ``dict``.
        """
        super().__init__()
        self.update(*args, **kwargs)
        return

    def __setitem__(self, name: str, value: str) -> None:
        """
            Store a header after validating it.

            :param name: Header name.
            :param value: Header value.

            :raises ValueError: When the header is not safe to send.
        """
        validate_header(name, value)
        super().__setitem__(name, value)
        return

    def update(self, *args: Any, **kwargs: Any) -> None:
        """
            Store several headers, validating each one.

            :param args: A mapping or an iterable of ``(name, value)`` pairs.
            :param kwargs: Headers given as keyword arguments.

            :raises ValueError: When a header is not safe to send.
        """
        for name, value in dict(*args, **kwargs).items():
            self[name] = value
        return

    def setdefault(self, name: str, default: Any = None) -> Any:
        """
            Store a header unless it is already set, validating it.

            :param name: Header name.
            :param default: Value stored when the header is not set.

            :returns: The value of the header.

            :raises ValueError: When the header is not safe to send.
        """
        if name not in self:
            self[name] = default
        return self[name]


class Response:
    """
        HTTP response abstraction for building responses with status,
        headers, and body content.
        
        This class provides a clean interface for constructing HTTP responses
        that can be converted to both WSGI and ASGI formats.
        
        Header names and values may not contain CR, LF or NUL: a value
        taken from a request (a redirect target, an echoed header) could
        otherwise inject a header or split the response. Storing such a
        header raises :class:`ValueError`.
        
        :param status_code: HTTP status code (default 200).
        :param headers: Optional dictionary of response headers.
        :param body: Response body as bytes.
        
        Example:
            response = Response(200, {"Content-Type": "text/plain"}, b"Hello")
            response.set_header("X-Custom", "value")
            response.set_cookie("session", "abc123", httponly=True)
    """
    
    def __init__(
        self,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
        body: bytes = b""
    ):
        """
            Construct a Response.
            
            :param status_code: HTTP status code (default 200).
            :param headers: Response headers dict.
            :param body: Response body as bytes.
        """
        self._status_code = status_code
        self._headers: Dict[str, str] = ResponseHeaders()
        self._body = body
        self._cookies: SimpleCookie = SimpleCookie()
        self._raw_set_cookies: List[str] = []

        # Initialize headers
        if headers is not None:
            for name, value in headers.items():
                self._headers[name] = value

        return

    @property
    def status_code(self) -> int:
        """
            Get the HTTP status code.
            
            :returns: HTTP status code.
        """
        return self._status_code
    
    @status_code.setter
    def status_code(self, value: int) -> None:
        """
            Set the HTTP status code.
            
            :param value: HTTP status code.
        """
        self._status_code = value
        return
    
    @property
    def headers(self) -> Dict[str, str]:
        """
            Get the response headers.
            
            :returns: Dictionary of header names to values.
        """
        return self._headers
    
    @property
    def body(self) -> bytes:
        """
            Get the response body.
            
            :returns: Response body as bytes.
        """
        return self._body
    
    @body.setter
    def body(self, value: bytes) -> None:
        """
            Set the response body.
            
            :param value: Response body as bytes.
        """
        self._body = value
        return
    
    def set_header(self, name: str, value: str) -> None:
        """
            Set a response header.
            
            :param name: Header name.
            :param value: Header value.

            :raises ValueError: When the name or value contains CR, LF or NUL.
        """
        self._headers[name] = value
        return
    
    def set_cookie(
        self,
        name: str,
        value: str,
        max_age: Optional[int] = None,
        expires: Optional[str] = None,
        path: str = "/",
        domain: Optional[str] = None,
        secure: bool = False,
        httponly: bool = True,
        samesite: Optional[str] = "Lax"
    ) -> None:
        """
            Set a response cookie.

            The defaults are the safe ones: the cookie is not readable by
            scripts (``HttpOnly``) and is not sent on cross-site requests
            other than top-level navigations (``SameSite=Lax``). Pass
            ``httponly=False`` for a cookie a script must read and
            ``samesite=None`` to omit the attribute. ``Secure`` can not be
            defaulted from here because a response does not know the scheme
            of its request; pass ``secure=True`` for cookies set over HTTPS.
            A cookie whose name starts with ``__Host-`` or ``__Secure-`` is
            always marked ``Secure``, since browsers discard it otherwise.
            
            :param name: Cookie name.
            :param value: Cookie value.
            :param max_age: Maximum age in seconds.
            :param expires: Expiration date string.
            :param path: Cookie path (default "/").
            :param domain: Cookie domain.
            :param secure: Whether cookie requires HTTPS.
            :param httponly: Whether cookie is HTTP-only (default True).
            :param samesite: SameSite attribute (Strict, Lax, None);
                default "Lax", ``None`` omits the attribute.

            :raises ValueError: When an attribute contains CR, LF or NUL.
        """
        # Cookie attributes are written to the header as they are given.
        for attribute_name, attribute_value in (
                ("expires", expires), ("path", path),
                ("domain", domain), ("samesite", samesite)):
            if attribute_value is not None:
                validate_header(f"Set-Cookie {attribute_name}", attribute_value)

        self._cookies[name] = value
        morsel = self._cookies[name]

        if name.startswith(_SECURE_COOKIE_PREFIXES):
            secure = True
        
        if max_age is not None:
            morsel["max-age"] = str(max_age)
        if expires is not None:
            morsel["expires"] = expires
        if path:
            morsel["path"] = path
        if domain is not None:
            morsel["domain"] = domain
        if secure:
            morsel["secure"] = True
        if httponly:
            morsel["httponly"] = True
        if samesite is not None:
            morsel["samesite"] = samesite
        
        return
    
    def add_raw_set_cookie(self, header_value: str) -> None:
        """
            Append a pre-built ``Set-Cookie`` header line to be
            emitted verbatim as its own header.

            Use this when the cookie string (name, value and
            attributes) was assembled elsewhere. HTTP carries
            multiple cookies as multiple ``Set-Cookie`` headers —
            never joined into one value — and header values must not
            contain CR/LF, so each call contributes one distinct
            header line.

            :param header_value: Complete ``Set-Cookie`` value, e.g.
                                 ``"sid=abc; Path=/; HttpOnly"``.

            :raises ValueError: When the value contains CR or LF.
        """
        value = str(header_value or "").strip()
        if value == "":
            return

        if ("\r" in value) or ("\n" in value):
            errmsg = (
                "Set-Cookie header values must not contain CR/LF; "
                "pass one cookie per add_raw_set_cookie call."
            )
            raise ValueError(errmsg)

        self._raw_set_cookies.append(value)
        return

    def delete_cookie(
        self,
        name: str,
        path: str = "/",
        domain: Optional[str] = None,
        secure: bool = False,
        httponly: bool = True,
        samesite: Optional[str] = "Lax"
    ) -> None:
        """
            Delete a cookie by setting it to expire.

            A browser replaces a cookie only when the path and domain match
            the ones it was set with, and accepts a ``__Host-`` or
            ``__Secure-`` cookie only with ``Secure``; pass the same
            attributes the cookie was set with.
            
            :param name: Cookie name.
            :param path: Cookie path (default "/").
            :param domain: Cookie domain.
            :param secure: Whether the cookie was set with Secure.
            :param httponly: Whether the cookie was set with HttpOnly.
            :param samesite: SameSite attribute the cookie was set with.
        """
        self.set_cookie(
            name=name,
            value="",
            max_age=0,
            expires="Thu, 01 Jan 1970 00:00:00 GMT",
            path=path,
            domain=domain,
            secure=secure,
            httponly=httponly,
            samesite=samesite
        )
        return

    def without_body(self) -> "Response":
        """
            Get a response with the status, headers and cookies of this one
            and no body -- the answer to a ``HEAD`` request.

            :returns: A new plain :class:`Response` with an empty body.
        """
        rtnval = Response(
            status_code=self._status_code,
            headers=dict(self._headers),
            body=b""
        )
        rtnval._cookies = self._cookies
        rtnval._raw_set_cookies = list(self._raw_set_cookies)

        return rtnval

    def _get_status_line(self) -> str:
        """
            Get the HTTP status line.
            
            :returns: Status line string (e.g., "200 OK").
        """
        phrase = HTTP_STATUS_PHRASES.get(self._status_code, "Unknown")
        return f"{self._status_code} {phrase}"
    
    def _get_all_headers(self) -> List[Tuple[str, str]]:
        """
            Get all headers including cookies.
            
            :returns: List of (name, value) tuples.
        """
        headers_list: List[Tuple[str, str]] = []
        
        # Add regular headers
        for name, value in self._headers.items():
            headers_list.append((name, value))
        
        # Add cookie headers
        for cookie_name in self._cookies:
            cookie_header = self._cookies[cookie_name].OutputString()
            headers_list.append(("Set-Cookie", cookie_header))

        # Add pre-built Set-Cookie lines registered via
        # add_raw_set_cookie — one header per line.
        for raw_cookie in self._raw_set_cookies:
            headers_list.append(("Set-Cookie", raw_cookie))

        # Last check before the wire: nothing leaves with a CR, LF or NUL,
        # whichever way it was stored.
        for name, value in headers_list:
            validate_header(name, value)

        return headers_list
    
    def to_wsgi(self) -> Tuple[str, List[Tuple[str, str]], Iterable[bytes]]:
        """
            Convert to WSGI response format.
            
            :returns: Tuple of (status, headers, body_iterable).
        """
        status = self._get_status_line()
        headers = self._get_all_headers()
        body_iterable: Iterable[bytes] = [self._body] if self._body else []
        
        return (status, headers, body_iterable)
    
    def to_asgi_start(self) -> Dict[str, Any]:
        """
            Build the ASGI ``http.response.start`` event of this response.

            :returns: The start event with the status and every header,
                      one entry per ``Set-Cookie``.
        """
        headers_list: List[List[bytes]] = []
        for name, value in self._get_all_headers():
            headers_list.append([name.encode("latin-1"), str(value).encode("latin-1")])
        
        start_event = {
            "type": "http.response.start",
            "status": self._status_code,
            "headers": headers_list,
        }

        return start_event

    def to_asgi(self) -> Dict[str, Any]:
        """
            Convert to ASGI response events.

            The body event carries the whole body. For a streaming response
            that means the content is read to its end here; use
            ``iter_content`` to send it chunk by chunk instead.
            
            :returns: Dictionary with 'start' and 'body' events.
        """
        start_event = self.to_asgi_start()
        
        # Read through the property, not the attribute: a streaming
        # response has no body stored until its content is consumed.
        body_event = {
            "type": "http.response.body",
            "body": self.body,
            "more_body": False,
        }
        
        return {
            "start": start_event,
            "body": body_event,
        }
    
    def __repr__(self) -> str:
        """
            Get string representation.
            
            :returns: String representation.
        """
        return f"Response({self._status_code})"


class JSONResponse(Response):
    """
        Response with JSON body and automatic Content-Type header.
        
        This class automatically serializes Python objects to JSON and
        sets the appropriate Content-Type header.
        
        :param content: Python object to serialize as JSON.
        :param status_code: HTTP status code (default 200).
        :param headers: Optional additional headers.
        
        Example:
            response = JSONResponse({"message": "Hello"})
            response = JSONResponse({"error": "Not found"}, status_code=404)
    """
    
    def __init__(
        self,
        content: Any,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None
    ):
        """
            Construct a JSON response.
            
            :param content: Python object to serialize as JSON.
            :param status_code: HTTP status code.
            :param headers: Additional headers.
        """
        # Serialize content to JSON
        body = json.dumps(content, ensure_ascii=False).encode("utf-8")
        
        # Initialize base response
        super().__init__(status_code=status_code, headers=headers, body=body)
        
        # Set Content-Type header
        self.set_header("Content-Type", "application/json; charset=utf-8")
        
        return
    
    def __repr__(self) -> str:
        """
            Get string representation.
            
            :returns: String representation.
        """
        return f"JSONResponse({self._status_code})"


class HTMLResponse(Response):
    """
        Response with HTML body and automatic Content-Type header.
        
        :param content: HTML content as string.
        :param status_code: HTTP status code (default 200).
        :param headers: Optional additional headers.
        
        Example:
            response = HTMLResponse("<h1>Hello</h1>")
    """
    
    def __init__(
        self,
        content: str,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None
    ):
        """
            Construct an HTML response.
            
            :param content: HTML content as string.
            :param status_code: HTTP status code.
            :param headers: Additional headers.
        """
        body = content.encode("utf-8")
        
        super().__init__(status_code=status_code, headers=headers, body=body)
        
        self.set_header("Content-Type", "text/html; charset=utf-8")
        
        return
    
    def __repr__(self) -> str:
        """
            Get string representation.
            
            :returns: String representation.
        """
        return f"HTMLResponse({self._status_code})"


class RedirectResponse(Response):
    """
        HTTP redirect response.
        
        :param url: URL to redirect to.
        :param status_code: HTTP status code (default 307 Temporary Redirect).
        :param headers: Optional additional headers.
        
        Example:
            response = RedirectResponse("/new-location")
            response = RedirectResponse("/permanent", status_code=301)
    """
    
    def __init__(
        self,
        url: str,
        status_code: int = 307,
        headers: Optional[Dict[str, str]] = None
    ):
        """
            Construct a redirect response.
            
            :param url: URL to redirect to.
            :param status_code: HTTP status code (default 307).
            :param headers: Additional headers.
        """
        super().__init__(status_code=status_code, headers=headers, body=b"")
        
        self.set_header("Location", url)
        
        return
    
    def __repr__(self) -> str:
        """
            Get string representation.
            
            :returns: String representation.
        """
        location = self._headers.get("Location", "")
        return f"RedirectResponse({self._status_code}, {location!r})"


class StreamingResponse(Response):
    """
        Response that streams body content.
        
        This class is used for streaming large responses where the body
        is generated incrementally.
        
        :param content: Iterable of bytes chunks.
        :param status_code: HTTP status code (default 200).
        :param headers: Optional additional headers.
        :param media_type: Optional media type for Content-Type header.
        
        Example:
            def generate():
                yield b"chunk1"
                yield b"chunk2"
            response = StreamingResponse(generate())
    """
    
    def __init__(
        self,
        content: Union[Iterable[bytes], AsyncIterable[bytes]],
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
        media_type: Optional[str] = None
    ):
        """
            Construct a streaming response.
            
            :param content: Iterable or async iterable of bytes chunks.
            :param status_code: HTTP status code.
            :param headers: Additional headers.
            :param media_type: Optional media type.
        """
        super().__init__(status_code=status_code, headers=headers, body=b"")
        
        self._content_iterator = content
        
        # Set once the content has been read to its end through ``body``;
        # the iterator is then exhausted and the collected body is used.
        self._body_collected = False
        
        if media_type is not None:
            self.set_header("Content-Type", media_type)
        
        return
    
    @property
    def is_async(self) -> bool:
        """
            Whether the content is an async iterable, which has to be read
            with ``async for``.
            
            :returns: True for async content.
        """
        rtnval = hasattr(self._content_iterator, "__aiter__")
        return rtnval
    
    @property
    def body(self) -> bytes:
        """
            Get the whole response body.
            
            This reads the content to its end and holds all of it in
            memory, which defeats the purpose of streaming; an unbounded
            stream never returns. Servers send a streaming response
            through :meth:`iter_content` instead. The collected body is
            kept, so later reads (and :meth:`iter_content`) return it.
            
            :returns: Response body as bytes.
            
            :raises TypeError: If the content is an async iterable, which
                can not be collected from synchronous code; iterate
                :meth:`iter_content` with ``async for`` instead.
        """
        if not self._body_collected:
            if self.is_async:
                errmsg = (
                    "The body of a StreamingResponse with async content can not be "
                    "collected synchronously; iterate iter_content() with 'async for'."
                )
                raise TypeError(errmsg)
            
            chunks = list(self._content_iterator)
            self._body = b"".join(chunks)
            self._body_collected = True
        
        return self._body
    
    def iter_content(self) -> Union[Iterator[bytes], AsyncIterator[bytes]]:
        """
            Iterate over body content chunks without collecting them.
            
            Ordinary content is returned as an iterator. Async content is
            returned as it is, an async iterator, to be read with
            ``async for`` (see :attr:`is_async`). If the body has already
            been collected through the ``body`` property, the collected
            body is yielded as a single chunk.
            
            :returns: Iterator or async iterator of bytes chunks.
        """
        if self._body_collected:
            rtnval = iter([self._body])
        elif self.is_async:
            content = self._content_iterator
            if hasattr(content, "__anext__"):
                rtnval = content
            else:
                rtnval = content.__aiter__()
        else:
            rtnval = iter(self._content_iterator)
        
        return rtnval
    
    def to_wsgi(self) -> Tuple[str, List[Tuple[str, str]], Iterable[bytes]]:
        """
            Convert to WSGI response format.
            
            :returns: Tuple of (status, headers, body_iterable).
        """
        status = self._get_status_line()
        headers = self._get_all_headers()
        
        return (status, headers, self._content_iterator)
    
    def __repr__(self) -> str:
        """
            Get string representation.
            
            :returns: String representation.
        """
        return f"StreamingResponse({self._status_code})"
