"""
    Response object returned by the TestClient.

    This module defines the :class:`TestResponse` dataclass that wraps
    the status code, headers, and body returned by an in-process request.
    Convenience properties provide decoded text and parsed JSON access.

    A response may carry several headers with the same name (two
    ``Set-Cookie`` headers, for example). The headers are therefore kept
    as an ordered list of ``(name, value)`` tuples; :attr:`headers` is a
    dictionary view of that list and :meth:`get_headers` returns every
    value of one header.
"""

import json as _json_module

from typing import Any, Dict, List, Optional, Sequence, Tuple, Union


class TestResponse:
    """
        Response object returned by :class:`TestClient`.

        Wraps the raw response data from an in-process request and
        provides convenience accessors for the response body as text
        or parsed JSON.

        :param status_code: The HTTP status code.
        :param headers: The response headers, as a dictionary or as a
            list of ``(name, value)`` tuples.
        :param body: The raw response body as bytes.
        :param chunks: The body as the application sent it, piece by
            piece. Defaults to the whole body as one piece.
        :param history: The redirect responses that led to this response.
    """

    def __init__(
        self,
        status_code: int,
        headers: Union[Dict[str, str], Sequence[Tuple[str, str]]],
        body: bytes,
        chunks: Optional[Sequence[bytes]] = None,
        history: Optional[Sequence["TestResponse"]] = None,
    ):
        """
            Construct a TestResponse.

            :param status_code: The HTTP status code.
            :param headers: The response headers, as a dictionary or as a
                list of ``(name, value)`` tuples.
            :param body: The raw response body bytes.
            :param chunks: The body pieces as the application sent them.
            :param history: The redirect responses followed to get here.
        """
        self._status_code = status_code

        if isinstance(headers, dict):
            self._header_list: List[Tuple[str, str]] = list(headers.items())
        else:
            self._header_list = [(name, value) for name, value in headers]

        # The dictionary view keeps the first spelling of each header name
        # and joins repeated values the way HTTP combines them.
        self._headers: Dict[str, str] = {}
        seen_names: Dict[str, str] = {}

        for name, value in self._header_list:
            lower_name = name.lower()

            if lower_name in seen_names:
                first_name = seen_names[lower_name]
                self._headers[first_name] = "{}, {}".format(self._headers[first_name], value)
            else:
                seen_names[lower_name] = name
                self._headers[name] = value

        self._body = bytes(body)

        if chunks is not None:
            self._chunks = [bytes(chunk) for chunk in chunks]
        else:
            self._chunks = [self._body]

        if history is not None:
            self._history = list(history)
        else:
            self._history = []

        return

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def status_code(self) -> int:
        """
            The HTTP status code of the response.

            :returns: An integer status code.
        """
        return self._status_code

    @property
    def headers(self) -> Dict[str, str]:
        """
            The response headers as a dictionary.

            A header that occurs more than once appears once, with its
            values joined by ``", "``. Use :attr:`raw_headers` or
            :meth:`get_headers` when each value matters, as it does for
            ``Set-Cookie``.

            :returns: A dictionary of header name-value pairs.
        """
        return dict(self._headers)

    @property
    def raw_headers(self) -> List[Tuple[str, str]]:
        """
            The response headers in the order the application sent them.

            :returns: A list of ``(name, value)`` tuples; repeated headers
                appear once per occurrence.
        """
        return list(self._header_list)

    @property
    def chunks(self) -> List[bytes]:
        """
            The response body as the application sent it, piece by piece.

            A streamed response has one entry per body message.

            :returns: A list of byte strings.
        """
        return list(self._chunks)

    @property
    def history(self) -> List["TestResponse"]:
        """
            The redirect responses that were followed to reach this response.

            :returns: A list of :class:`TestResponse` objects, oldest first.
        """
        return list(self._history)

    @property
    def body(self) -> bytes:
        """
            The raw response body.

            :returns: The body as bytes.
        """
        return self._body

    @property
    def text(self) -> str:
        """
            The response body decoded as UTF-8 text.

            :returns: The body as a string.
        """
        return self._body.decode("utf-8")

    @property
    def json(self) -> Any:
        """
            The response body parsed as JSON.

            :returns: The parsed JSON value.

            :raises ValueError: If the body is not valid JSON.
        """
        try:
            return _json_module.loads(self._body)
        except _json_module.JSONDecodeError as exc:
            raise ValueError(
                "Response body is not valid JSON: {}".format(str(exc))
            ) from exc

    # -------------------------------------------------------------------------
    # Methods
    # -------------------------------------------------------------------------

    def get_header(
        self,
        name: str,
        default: Optional[str] = None,
    ) -> Optional[str]:
        """
            Get a response header value by name (case-insensitive).

            :param name: The header name to look up.
            :param default: The value to return if the header is not found.

            :returns: The header value or the default.
        """
        lower_name = name.lower()

        for header_name, header_value in self._headers.items():
            if header_name.lower() == lower_name:
                return header_value

        return default

    def get_headers(self, name: str) -> List[str]:
        """
            Get every value of a response header (case-insensitive).

            :param name: The header name to look up.

            :returns: The values in the order they were sent; an empty
                list if the header is absent.
        """
        lower_name = name.lower()

        values = []
        for header_name, header_value in self._header_list:
            if header_name.lower() == lower_name:
                values.append(header_value)

        return values
