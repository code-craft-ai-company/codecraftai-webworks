"""
    Template exception classes module.
    
    This module defines custom exceptions for template-related errors.
    These exceptions provide detailed error information including
    template names, line numbers, and context to aid debugging.
"""


class TemplateError(Exception):
    """
        Base exception for all template-related errors.
        
        Provides a common base class for template exceptions,
        enabling catch-all handling of template errors.
    """
    pass


class TemplateNotFoundError(TemplateError):
    """
        Exception raised when a template file cannot be found.
        
        This exception is raised when attempting to load a template that
        does not exist in any of the configured template directories.
        
        :ivar template_name: The name of the template that was not found.
        :ivar searched_paths: List of directories that were searched.
        
        Example:
            try:
                loader.load("missing.html")
            except TemplateNotFoundError as exc:
                print(f"Template '{exc.template_name}' not found")
                print(f"Searched: {exc.searched_paths}")
    """
    
    def __init__(
        self,
        template_name: str,
        searched_paths: list = None
    ):
        """
            Construct a TemplateNotFoundError.
            
            :param template_name: The name of the template that was not found.
            :param searched_paths: List of directories that were searched.
        """
        self.template_name = template_name
        self.searched_paths = searched_paths or []
        
        if self.searched_paths:
            paths_str = ", ".join(self.searched_paths)
            message = (
                f"Template '{template_name}' not found. "
                f"Searched paths: {paths_str}"
            )
        else:
            message = (
                f"Template '{template_name}' not found. "
                f"No template directories configured."
            )
        
        super().__init__(message)
        return


class TemplateEngineNotFoundError(TemplateError):
    """
        Exception raised when a requested template engine is not registered.
        
        This exception is raised when attempting to get or create a template
        engine that has not been registered with the TemplateEngineRegistry.
        
        :ivar engine_name: The name of the engine that was not found.
        :ivar available_engines: List of registered engine names.
        
        Example:
            try:
                engine = TemplateEngineRegistry.get("unknown")
            except TemplateEngineNotFoundError as exc:
                print(f"Engine '{exc.engine_name}' not found")
                print(f"Available: {exc.available_engines}")
    """
    
    def __init__(
        self,
        engine_name: str,
        available_engines: list = None
    ):
        """
            Construct a TemplateEngineNotFoundError.
            
            :param engine_name: The name of the engine that was not found.
            :param available_engines: List of registered engine names.
        """
        self.engine_name = engine_name
        self.available_engines = available_engines or []
        
        if self.available_engines:
            available_str = ", ".join(sorted(self.available_engines))
            message = (
                f"Template engine '{engine_name}' is not registered. "
                f"Available engines: {available_str}"
            )
        else:
            message = (
                f"Template engine '{engine_name}' is not registered. "
                f"No engines are currently registered."
            )
        
        super().__init__(message)
        return


class UndefinedVariableError(TemplateError):
    """
        Exception raised when an undefined variable is accessed in strict mode.

        This exception is raised when a template attempts to access a variable
        that does not exist in the context and the undefined behavior is set
        to strict mode.

        :ivar variable_name: The name of the undefined variable.

        Example:
            try:
                context.resolve("missing_key")
            except UndefinedVariableError as exc:
                print(f"Undefined variable: {exc.variable_name}")
    """

    def __init__(
        self,
        variable_name: str
    ):
        """
            Construct an UndefinedVariableError.

            :param variable_name: The name of the variable that was not found.
        """
        self.variable_name = variable_name

        message = (
            f"Undefined variable '{variable_name}' accessed in strict mode"
        )

        super().__init__(message)
        return


class TemplateInheritanceError(TemplateError):
    """
        Exception raised when a template inheritance error is detected.
        
        This exception is raised when circular template inheritance is
        detected or other inheritance chain errors occur.
        
        :ivar chain: List of template names in the inheritance chain.
        
        Example:
            try:
                adapter.render("circular_child.html", {})
            except TemplateInheritanceError as exc:
                print(f"Inheritance error: {exc}")
                print(f"Chain: {exc.chain}")
    """
    
    def __init__(
        self,
        message: str,
        chain: list = None
    ):
        """
            Construct a TemplateInheritanceError.
            
            :param message: Description of the inheritance error.
            :param chain: List of template names in the inheritance chain.
        """
        self.chain = chain or []
        
        if self.chain:
            chain_str = " -> ".join(self.chain)
            full_message = f"{message}. Inheritance chain: {chain_str}"
        else:
            full_message = message
        
        super().__init__(full_message)
        return


class TemplateSyntaxError(TemplateError):
    """
        Exception raised when a template contains syntax errors.
        
        This exception is raised when a template cannot be compiled due
        to invalid syntax. It includes the template name, line number,
        and optional source context to aid debugging.
        
        :ivar template_name: The name of the template with the syntax error.
        :ivar line_number: The line number where the error occurred.
        :ivar source_context: Optional source code context around the error.
        
        Example:
            try:
                engine.render("broken.html", {})
            except TemplateSyntaxError as exc:
                print(f"Syntax error in '{exc.template_name}' at line {exc.line_number}")
    """
    
    def __init__(
        self,
        template_name: str,
        line_number: int,
        message: str,
        source_context: str = None
    ):
        """
            Construct a TemplateSyntaxError.
            
            :param template_name: The name of the template with the syntax error.
            :param line_number: The line number where the error occurred.
            :param message: Description of the syntax error.
            :param source_context: Optional source code context around the error.
        """
        self.template_name = template_name
        self.line_number = line_number
        self.source_context = source_context
        
        full_message = (
            f"Syntax error in '{template_name}' at line {line_number}: {message}"
        )
        
        if source_context:
            full_message = f"{full_message}\n  Source: {source_context}"
        
        super().__init__(full_message)
        return


class TemplateRenderError(TemplateError):
    """
        Exception raised when an error occurs during template rendering.
        
        This exception is raised when rendering fails due to context errors,
        missing variables, or other runtime issues during template evaluation.
        
        :ivar template_name: The name of the template being rendered.
        :ivar variable_name: The name of the variable that caused the error, if applicable.
        :ivar line_number: The line number where the error occurred, if known.
        
        Example:
            try:
                engine.render("page.html", {"items": None})
            except TemplateRenderError as exc:
                print(f"Render error in '{exc.template_name}'")
                if exc.variable_name:
                    print(f"Variable: {exc.variable_name}")
    """
    
    def __init__(
        self,
        template_name: str,
        message: str,
        variable_name: str = None,
        line_number: int = None
    ):
        """
            Construct a TemplateRenderError.
            
            :param template_name: The name of the template being rendered.
            :param message: Description of the rendering error.
            :param variable_name: The name of the variable that caused the error.
            :param line_number: The line number where the error occurred.
        """
        self.template_name = template_name
        self.variable_name = variable_name
        self.line_number = line_number
        
        full_message = f"Render error in '{template_name}'"
        
        if line_number is not None:
            full_message = f"{full_message} at line {line_number}"
        
        full_message = f"{full_message}: {message}"
        
        if variable_name:
            full_message = f"{full_message} (variable: '{variable_name}')"
        
        super().__init__(full_message)
        return


class TemplateFilterNotFoundError(TemplateError):
    """
        Exception raised when a requested template filter is not registered.
        
        This exception is raised when a template references a filter that
        has not been registered with the template engine.
        
        :ivar filter_name: The name of the filter that was not found.
        :ivar available_filters: List of registered filter names.
        
        Example:
            try:
                engine.apply_filter("unknown_filter", value)
            except TemplateFilterNotFoundError as exc:
                print(f"Filter '{exc.filter_name}' not found")
                print(f"Available: {exc.available_filters}")
    """
    
    def __init__(
        self,
        filter_name: str,
        available_filters: list = None
    ):
        """
            Construct a TemplateFilterNotFoundError.
            
            :param filter_name: The name of the filter that was not found.
            :param available_filters: List of registered filter names.
        """
        self.filter_name = filter_name
        self.available_filters = available_filters or []
        
        if self.available_filters:
            available_str = ", ".join(sorted(self.available_filters))
            message = (
                f"Template filter '{filter_name}' is not registered. "
                f"Available filters: {available_str}"
            )
        else:
            message = (
                f"Template filter '{filter_name}' is not registered. "
                f"No filters are currently registered."
            )
        
        super().__init__(message)
        return


class TemplateConfigurationError(TemplateError):
    """
        Exception raised when invalid template configuration is provided.
        
        This exception is raised when template configuration validation
        fails, such as invalid engine names, missing directories, or
        incompatible option combinations.
        
        :ivar field_name: The configuration field that caused the error, if applicable.
        
        Example:
            try:
                config.validate()
            except TemplateConfigurationError as exc:
                print(f"Configuration error: {exc}")
                if exc.field_name:
                    print(f"Field: {exc.field_name}")
    """
    
    def __init__(
        self,
        message: str,
        field_name: str = None
    ):
        """
            Construct a TemplateConfigurationError.
            
            :param message: Description of the configuration error.
            :param field_name: The configuration field that caused the error.
        """
        self.field_name = field_name
        
        if field_name:
            full_message = (
                f"Template configuration error ({field_name}): {message}"
            )
        else:
            full_message = f"Template configuration error: {message}"
        
        super().__init__(full_message)
        return




