"""
    Template configuration module.
    
    This module provides the TemplateConfig dataclass for configuring
    template rendering behavior. The configuration supports all template
    engine settings including directories, caching, auto-escaping,
    encoding, and engine-specific options.
    
    Configuration can be created directly, loaded from a dictionary
    (e.g., from application configuration files), and validated to
    ensure correctness before use.
    
    Example:
        # Create with defaults
        config = TemplateConfig()
        
        # Create with custom settings
        config = TemplateConfig(
            engine="jinja2",
            directories=["/app/templates"],
            cache_size=200,
            auto_reload=True
        )
        
        # Validate configuration
        config.validate()
        
        # Load from dictionary
        config = TemplateConfig.from_dict({
            "engine": "jinja2",
            "directories": ["/app/templates"],
            "cache_size": 200
        })
"""

from dataclasses import dataclass, field
from typing import Any, Dict

from ccai.webworks.templating.exceptions import TemplateConfigurationError


VALID_UNDEFINED_BEHAVIORS = ("silent", "strict", "debug")


@dataclass
class TemplateConfig:
    """
        Configuration for template rendering.
        
        Stores all settings needed to configure a template engine,
        including template directories, caching behavior, auto-escaping,
        encoding, and engine-specific options.
        
        All fields have sensible defaults suitable for production use.
        Call validate() to check that the configuration is valid before
        using it to initialize a template engine.
        
        :ivar engine: The template engine name (e.g., "jinja2", "mako").
        :ivar directories: List of directories to search for templates.
        :ivar extensions: List of recognized template file extensions.
        :ivar auto_escape: Whether to enable auto-escaping by default.
        :ivar cache_enabled: Whether to enable template caching.
        :ivar cache_size: Maximum number of cached templates.
        :ivar auto_reload: Whether to reload templates when modified.
        :ivar encoding: Template file encoding.
        :ivar undefined_behavior: How to handle undefined variables.
            Must be one of "silent", "strict", or "debug".
        :ivar engine_options: Additional engine-specific options.
        
        Example:
            config = TemplateConfig(
                engine="jinja2",
                directories=["/app/templates"],
                auto_escape=True,
                cache_size=400,
                auto_reload=False,
                encoding="utf-8",
                undefined_behavior="silent"
            )
            config.validate()
    """
    
    engine: str = "jinja2"
    directories: list = field(default_factory=list)
    extensions: list = field(default_factory=lambda: [".html", ".htm", ".xml", ".txt"])
    auto_escape: bool = True
    cache_enabled: bool = True
    cache_size: int = 400
    auto_reload: bool = False
    encoding: str = "utf-8"
    undefined_behavior: str = "silent"
    engine_options: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> None:
        """
            Validate the configuration.
            
            Checks that all configuration fields have valid values.
            Raises TemplateConfigurationError if any field is invalid.
            
            :raises TemplateConfigurationError: If the configuration is invalid.
            
            Example:
                config = TemplateConfig(cache_size=-1)
                config.validate()  # Raises TemplateConfigurationError
        """
        if not isinstance(self.engine, str) or len(self.engine.strip()) == 0:
            raise TemplateConfigurationError(
                "engine must be a non-empty string",
                field_name="engine"
            )
        
        if not isinstance(self.directories, list):
            raise TemplateConfigurationError(
                "directories must be a list",
                field_name="directories"
            )
        
        if not isinstance(self.cache_size, int) or self.cache_size < 1:
            raise TemplateConfigurationError(
                "cache_size must be a positive integer",
                field_name="cache_size"
            )
        
        if self.undefined_behavior not in VALID_UNDEFINED_BEHAVIORS:
            valid_str = ", ".join(VALID_UNDEFINED_BEHAVIORS)
            raise TemplateConfigurationError(
                f"undefined_behavior must be one of: {valid_str}",
                field_name="undefined_behavior"
            )
        
        if not isinstance(self.encoding, str) or len(self.encoding.strip()) == 0:
            raise TemplateConfigurationError(
                "encoding must be a non-empty string",
                field_name="encoding"
            )
        
        return
    
    @classmethod
    def from_dict(cls, data: dict) -> "TemplateConfig":
        """
            Create a TemplateConfig from a dictionary.
            
            Supports loading configuration from application config files
            or environment-specific settings. Unknown keys in the dictionary
            are ignored. Nested engine options are supported via the
            ``engine_options`` key.
            
            :param data: Dictionary of configuration values.
            
            :returns: A new TemplateConfig instance.
            
            Example:
                config = TemplateConfig.from_dict({
                    "engine": "jinja2",
                    "directories": ["/app/templates"],
                    "cache_size": 200,
                    "engine_options": {
                        "trim_blocks": True,
                        "lstrip_blocks": True
                    }
                })
        """
        known_fields = {
            "engine", "directories", "extensions", "auto_escape",
            "cache_enabled", "cache_size", "auto_reload", "encoding",
            "undefined_behavior", "engine_options"
        }
        
        filtered = {
            key: value for key, value in data.items()
            if key in known_fields
        }
        
        return cls(**filtered)
