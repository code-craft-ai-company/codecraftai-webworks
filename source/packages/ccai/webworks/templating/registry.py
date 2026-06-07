"""
    Template engine registry module.
    
    This module provides the TemplateEngineRegistry class for managing
    template engine adapters. The registry enables pluggable template
    engine support by allowing registration and retrieval of engine
    adapter classes.
    
    The registry supports:
    - Registration of template engine adapter classes
    - Retrieval of registered engine classes
    - Creation of engine instances with configuration
    - Setting a default engine for the application
    - Listing all registered engines
    
    Example:
        # Register an engine adapter
        TemplateEngineRegistry.register("jinja2", Jinja2Adapter)
        
        # Create an engine instance
        engine = TemplateEngineRegistry.create("jinja2", template_dirs=["/templates"])
        
        # Set default engine
        TemplateEngineRegistry.set_default("jinja2")
"""

from typing import Any, Dict

from ccai.webworks.templating.engine import TemplateEngine
from ccai.webworks.templating.exceptions import TemplateEngineNotFoundError


class TemplateEngineRegistry:
    """
        Registry for template engine adapters.
        
        Provides a central registry for template engine adapter classes,
        enabling pluggable template engine support. Engine adapters can
        be registered by name and later retrieved or instantiated.
        
        The registry maintains:
        - A dictionary mapping engine names to adapter classes
        - A default engine name for when no engine is specified
        
        All methods are class methods, allowing the registry to be used
        without instantiation.
        
        Example:
            # Register engines
            TemplateEngineRegistry.register("jinja2", Jinja2Adapter)
            TemplateEngineRegistry.register("mako", MakoAdapter)
            
            # Get engine class
            engine_class = TemplateEngineRegistry.get("jinja2")
            
            # Create engine instance
            engine = TemplateEngineRegistry.create("jinja2", template_dirs=["/templates"])
            
            # List registered engines
            engines = TemplateEngineRegistry.list_engines()  # ["jinja2", "mako"]
    """
    
    _engines: Dict[str, type] = {}
    _default_engine: str = "jinja2"
    
    @classmethod
    def register(
        cls,
        name: str,
        engine_class: type
    ) -> None:
        """
            Register a template engine adapter.
            
            Registers an engine adapter class with the given name. The class
            should be a subclass of TemplateEngine. If an engine with the
            same name is already registered, it will be replaced.
            
            :param name: Engine name (e.g., "jinja2", "mako").
            :param engine_class: Engine adapter class (subclass of TemplateEngine).
            
            Example:
                TemplateEngineRegistry.register("jinja2", Jinja2Adapter)
        """
        cls._engines[name] = engine_class
        return
    
    @classmethod
    def get(cls, name: str) -> type:
        """
            Get a registered engine class.
            
            Retrieves the engine adapter class registered with the given name.
            
            :param name: Engine name.
            
            :returns: Engine adapter class.
            
            :raises TemplateEngineNotFoundError: If engine not registered.
            
            Example:
                engine_class = TemplateEngineRegistry.get("jinja2")
                engine = engine_class(template_dirs=["/templates"])
        """
        if name not in cls._engines:
            raise TemplateEngineNotFoundError(
                engine_name=name,
                available_engines=list(cls._engines.keys())
            )
        
        return cls._engines[name]
    
    @classmethod
    def create(
        cls,
        name: str,
        **kwargs: Any
    ) -> TemplateEngine:
        """
            Create an engine instance.
            
            Creates and returns an instance of the engine adapter registered
            with the given name, passing the provided keyword arguments to
            the engine constructor.
            
            :param name: Engine name.
            :param kwargs: Engine configuration options passed to constructor.
            
            :returns: Configured engine instance.
            
            :raises TemplateEngineNotFoundError: If engine not registered.
            
            Example:
                engine = TemplateEngineRegistry.create(
                    "jinja2",
                    template_dirs=["/templates"],
                    auto_escape=True
                )
        """
        engine_class = cls.get(name)
        return engine_class(**kwargs)
    
    @classmethod
    def set_default(cls, name: str) -> None:
        """
            Set the default template engine.
            
            Sets the engine to use when no engine is explicitly specified.
            The engine must be registered before it can be set as default.
            
            :param name: Engine name to use as default.
            
            :raises TemplateEngineNotFoundError: If engine not registered.
            
            Example:
                TemplateEngineRegistry.set_default("mako")
        """
        # Verify the engine exists before setting as default
        if name not in cls._engines:
            raise TemplateEngineNotFoundError(
                engine_name=name,
                available_engines=list(cls._engines.keys())
            )
        
        cls._default_engine = name
        return
    
    @classmethod
    def list_engines(cls) -> list:
        """
            Return list of registered engine names.
            
            Returns a list of all engine names that have been registered
            with the registry.
            
            :returns: List of registered engine names.
            
            Example:
                engines = TemplateEngineRegistry.list_engines()
                # ["jinja2", "mako"]
        """
        return list(cls._engines.keys())
    
    @classmethod
    def get_default(cls) -> str:
        """
            Get the default engine name.
            
            Returns the name of the currently configured default engine.
            
            :returns: Default engine name.
            
            Example:
                default = TemplateEngineRegistry.get_default()
                # "jinja2"
        """
        return cls._default_engine
    
    @classmethod
    def is_registered(cls, name: str) -> bool:
        """
            Check if an engine is registered.
            
            Returns True if an engine with the given name is registered,
            False otherwise.
            
            :param name: Engine name to check.
            
            :returns: True if registered, False otherwise.
            
            Example:
                if TemplateEngineRegistry.is_registered("jinja2"):
                    engine = TemplateEngineRegistry.create("jinja2")
        """
        return name in cls._engines
    
    @classmethod
    def unregister(cls, name: str) -> None:
        """
            Unregister a template engine adapter.
            
            Removes the engine adapter registered with the given name.
            If the engine is not registered, this method does nothing.
            
            :param name: Engine name to unregister.
            
            Example:
                TemplateEngineRegistry.unregister("mako")
        """
        if name in cls._engines:
            del cls._engines[name]
        return
    
    @classmethod
    def clear(cls) -> None:
        """
            Clear all registered engines.
            
            Removes all registered engine adapters from the registry.
            This is primarily useful for testing.
            
            Example:
                TemplateEngineRegistry.clear()
        """
        cls._engines.clear()
        return
