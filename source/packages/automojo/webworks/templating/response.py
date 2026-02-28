"""
    Template response integration module.
    
    This module provides helper functions for rendering templates and
    returning them as HTTP response objects. It bridges the template
    rendering system with HTTP response handling by providing convenient
    functions that render a template and wrap the output in a response
    object with appropriate headers.
    
    The module defines two lightweight response classes:
    
    - TemplateResponse: Holds a rendered template body along with
      status code, content type, and headers.
    - StreamingTemplateResponse: Holds a streaming iterator body for
      large template output, along with status code, content type,
      and headers.
    
    Two helper functions are provided:
    
    - render_template(): Renders a template and returns a TemplateResponse.
    - render_template_stream(): Renders a template as a stream and returns
      a StreamingTemplateResponse.
    
    Both functions accept an optional request_context parameter for
    injecting request-scoped variables into the template context.
"""

from typing import Any, Dict, Iterator, Optional

from automojo.webworks.templating.renderer import TemplateRenderer


class TemplateResponse:
    """
        HTTP response containing a rendered template body.
        
        This is a lightweight response class that holds the rendered
        template output along with HTTP metadata such as status code,
        content type, and headers. It does not depend on any external
        web framework, making it suitable for use as a library component.
        
        :param body: The rendered template content as a string.
        :param status_code: The HTTP status code for the response.
        :param content_type: The Content-Type header value.
        :param headers: Dictionary of additional HTTP headers.
    """

    def __init__(
        self,
        body: str,
        status_code: int = 200,
        content_type: str = "text/html; charset=utf-8",
        headers: Optional[Dict[str, str]] = None
    ) -> None:
        """
            Construct a TemplateResponse.
            
            :param body: The rendered template content as a string.
            :param status_code: The HTTP status code for the response.
            :param content_type: The Content-Type header value.
            :param headers: Optional dictionary of additional HTTP headers.
        """
        self._body = body
        self._status_code = status_code
        self._content_type = content_type
        self._headers: Dict[str, str] = {}
        
        # Always set Content-Type in headers
        self._headers["Content-Type"] = content_type
        
        if headers is not None:
            self._headers.update(headers)
        
        return
    
    @property
    def body(self) -> str:
        """
            Get the rendered template body.
            
            :returns: The rendered template content as a string.
        """
        return self._body
    
    @property
    def status_code(self) -> int:
        """
            Get the HTTP status code.
            
            :returns: The HTTP status code for this response.
        """
        return self._status_code
    
    @property
    def content_type(self) -> str:
        """
            Get the Content-Type header value.
            
            :returns: The Content-Type header value.
        """
        return self._content_type
    
    @property
    def headers(self) -> Dict[str, str]:
        """
            Get the response headers.
            
            :returns: A copy of the response headers dictionary.
        """
        return dict(self._headers)


class StreamingTemplateResponse:
    """
        HTTP response containing a streaming template body.
        
        This is a lightweight response class that holds a streaming
        iterator for the rendered template output. It is suitable for
        large templates where buffering the entire output in memory
        is undesirable.
        
        :param body_iterator: An iterator yielding chunks of rendered
            template content.
        :param status_code: The HTTP status code for the response.
        :param content_type: The Content-Type header value.
        :param headers: Dictionary of additional HTTP headers.
    """

    def __init__(
        self,
        body_iterator: Iterator[str],
        status_code: int = 200,
        content_type: str = "text/html; charset=utf-8",
        headers: Optional[Dict[str, str]] = None
    ) -> None:
        """
            Construct a StreamingTemplateResponse.
            
            :param body_iterator: An iterator yielding chunks of rendered
                template content.
            :param status_code: The HTTP status code for the response.
            :param content_type: The Content-Type header value.
            :param headers: Optional dictionary of additional HTTP headers.
        """
        self._body_iterator = body_iterator
        self._status_code = status_code
        self._content_type = content_type
        self._headers: Dict[str, str] = {}
        
        # Always set Content-Type in headers
        self._headers["Content-Type"] = content_type
        
        if headers is not None:
            self._headers.update(headers)
        
        return
    
    @property
    def body_iterator(self) -> Iterator[str]:
        """
            Get the streaming body iterator.
            
            :returns: An iterator yielding chunks of rendered template content.
        """
        return self._body_iterator
    
    @property
    def status_code(self) -> int:
        """
            Get the HTTP status code.
            
            :returns: The HTTP status code for this response.
        """
        return self._status_code
    
    @property
    def content_type(self) -> str:
        """
            Get the Content-Type header value.
            
            :returns: The Content-Type header value.
        """
        return self._content_type
    
    @property
    def headers(self) -> Dict[str, str]:
        """
            Get the response headers.
            
            :returns: A copy of the response headers dictionary.
        """
        return dict(self._headers)


def render_template(
    template_name: str,
    context: Optional[Dict[str, Any]] = None,
    status_code: int = 200,
    content_type: str = "text/html; charset=utf-8",
    headers: Optional[Dict[str, str]] = None,
    renderer: Optional[TemplateRenderer] = None,
    request_context: Optional[Dict[str, Any]] = None,
    **kwargs: Any
) -> TemplateResponse:
    """
        Render a template and return an HTTP response.
        
        Renders the specified template using the provided renderer and
        wraps the output in a TemplateResponse with the given status code,
        content type, and headers. An optional request_context parameter
        allows injecting request-scoped variables into the template context.
        
        The context building order is:
        1. Start with request_context variables (if provided)
        2. Merge the passed context dictionary
        3. Merge keyword arguments (highest priority)
        
        :param template_name: Name/path of the template file.
        :param context: Optional dictionary of variables to pass to the template.
        :param status_code: HTTP status code (default 200).
        :param content_type: Content-Type header value
            (default "text/html; charset=utf-8").
        :param headers: Optional dictionary of additional response headers.
        :param renderer: The TemplateRenderer instance to use for rendering.
            Must be provided.
        :param request_context: Optional dictionary of request-scoped variables
            to inject into the template context.
        :param kwargs: Additional variables merged into context with highest
            priority.
        
        :returns: A TemplateResponse with the rendered template body.
        
        :raises ValueError: If renderer is None.
        :raises TemplateNotFoundError: If the template file does not exist.
        :raises TemplateError: If template rendering fails.
    """
    if renderer is None:
        raise ValueError(
            "A TemplateRenderer instance must be provided via the "
            "'renderer' parameter."
        )
    
    # Build the merged context
    merged_context: Dict[str, Any] = {}
    
    if request_context is not None:
        merged_context.update(request_context)
    
    if context is not None:
        merged_context.update(context)
    
    if kwargs:
        merged_context.update(kwargs)
    
    # Render the template
    body = renderer.render(template_name, merged_context)
    
    # Build the response
    response = TemplateResponse(
        body=body,
        status_code=status_code,
        content_type=content_type,
        headers=headers
    )
    
    return response


def render_template_stream(
    template_name: str,
    context: Optional[Dict[str, Any]] = None,
    status_code: int = 200,
    content_type: str = "text/html; charset=utf-8",
    headers: Optional[Dict[str, str]] = None,
    renderer: Optional[TemplateRenderer] = None,
    request_context: Optional[Dict[str, Any]] = None,
    **kwargs: Any
) -> StreamingTemplateResponse:
    """
        Render a template as a streaming HTTP response.
        
        Renders the specified template using the provided renderer's
        streaming method and wraps the output in a StreamingTemplateResponse.
        This is suitable for large templates where buffering the entire
        output in memory is undesirable.
        
        The context building order is:
        1. Start with request_context variables (if provided)
        2. Merge the passed context dictionary
        3. Merge keyword arguments (highest priority)
        
        :param template_name: Name/path of the template file.
        :param context: Optional dictionary of variables to pass to the template.
        :param status_code: HTTP status code (default 200).
        :param content_type: Content-Type header value
            (default "text/html; charset=utf-8").
        :param headers: Optional dictionary of additional response headers.
        :param renderer: The TemplateRenderer instance to use for rendering.
            Must be provided.
        :param request_context: Optional dictionary of request-scoped variables
            to inject into the template context.
        :param kwargs: Additional variables merged into context with highest
            priority.
        
        :returns: A StreamingTemplateResponse with the rendered template body
            as a streaming iterator.
        
        :raises ValueError: If renderer is None.
        :raises TemplateNotFoundError: If the template file does not exist.
        :raises TemplateError: If template rendering fails.
    """
    if renderer is None:
        raise ValueError(
            "A TemplateRenderer instance must be provided via the "
            "'renderer' parameter."
        )
    
    # Build the merged context
    merged_context: Dict[str, Any] = {}
    
    if request_context is not None:
        merged_context.update(request_context)
    
    if context is not None:
        merged_context.update(context)
    
    if kwargs:
        merged_context.update(kwargs)
    
    # Render the template as a stream
    body_iterator = renderer.render_stream(template_name, merged_context)
    
    # Build the streaming response
    response = StreamingTemplateResponse(
        body_iterator=body_iterator,
        status_code=status_code,
        content_type=content_type,
        headers=headers
    )
    
    return response
