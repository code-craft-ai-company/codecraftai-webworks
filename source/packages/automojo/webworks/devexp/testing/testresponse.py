"""
    Response object returned by the TestClient.

    This module defines the :class:`TestResponse` dataclass that wraps
    the status code, headers, and body returned by an in-process request.
    Convenience properties provide decoded text and parsed JSON access.
"""

import json as _json_module

from typing import Any, Dict, Optional


class TestResponse:
    """
        Response object returned by :class:`TestClient`.

        Wraps the raw response data from an in-process request and
        provides convenience accessors for the response body as text
        or parsed JSON.

        :param status_code: The HTTP status code.
        :param headers: A dictionary of response header name-value pairs.
        :param body: The raw response body as bytes.
    """

    def __init__(
        self,
        status_code: int,
        headers: Dict[str, str],
        body: bytes,
    ):
        """
            Construct a TestResponse.

            :param status_code: The HTTP status code.
            :param headers: A dictionary of response headers.
            :param body: The raw response body bytes.
        """
        self._status_code = status_code
        self._headers = dict(headers)
        self._body = bytes(body)
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

            :returns: A dictionary of header name-value pairs.
        """
        return dict(self._headers)

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
