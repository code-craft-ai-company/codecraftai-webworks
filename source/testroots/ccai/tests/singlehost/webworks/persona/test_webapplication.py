"""
    Tests for the WebApplication class.
    
    This module contains unit tests for the WebApplication class which extends
    ThisApplication with database lifecycle hooks.
"""

from ccai.webworks.webapplication import WebApplication
from ccai.thisapp.wellknown import ThisApplication
from ccai.errors.exceptions import SemanticError


# =============================================================================
# Unit Tests for WebApplication - Construction
# =============================================================================

def test_webapplication_raises_error_without_establish_flag():
    """
        Test that WebApplication raises SemanticError when instantiated directly
        without the from_establish_webapp_persona flag.
    """
    exception_raised = False
    exception_type = None
    
    try:
        app = WebApplication(
            name="TestApp",
            logger_name="testapp",
            log_basename="testapp",
            presence_dir="/tmp/testapp",
            log_directory="/tmp/testapp/logs",
            settings_file="/tmp/testapp/settings.config",
            extensions="",
            service_name="testservice"
        )
    except SemanticError as err:
        exception_raised = True
        exception_type = type(err)
    
    if not exception_raised:
        errmsg = "Expected SemanticError to be raised when instantiating WebApplication directly"
        raise AssertionError(errmsg)
    
    if exception_type is not SemanticError:
        errmsg = f"Expected SemanticError, got {exception_type}"
        raise AssertionError(errmsg)
    
    return


def test_webapplication_error_message_mentions_establish_webapp_persona():
    """
        Test that the error message mentions establish_webapp_persona.
    """
    error_message = None
    
    try:
        app = WebApplication(
            name="TestApp",
            logger_name="testapp",
            log_basename="testapp",
            presence_dir="/tmp/testapp",
            log_directory="/tmp/testapp/logs",
            settings_file="/tmp/testapp/settings.config",
            extensions="",
            service_name="testservice"
        )
    except SemanticError as err:
        error_message = str(err)
    
    if error_message is None:
        errmsg = "Expected SemanticError to be raised"
        raise AssertionError(errmsg)
    
    if "establish_webapp_persona" not in error_message:
        errmsg = f"Expected error message to mention 'establish_webapp_persona', got: {error_message}"
        raise AssertionError(errmsg)
    
    return


def test_webapplication_can_be_instantiated_with_establish_flag():
    """
        Test that WebApplication can be instantiated when the
        from_establish_webapp_persona flag is provided.
    """
    app = WebApplication(
        name="TestApp",
        logger_name="testapp",
        log_basename="testapp",
        presence_dir="/tmp/testapp",
        log_directory="/tmp/testapp/logs",
        settings_file="/tmp/testapp/settings.config",
        extensions="",
        service_name="testservice",
        from_establish_webapp_persona=True
    )
    
    if app is None:
        errmsg = "Expected WebApplication instance to be created"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for WebApplication - Inheritance
# =============================================================================

def test_webapplication_extends_thisapplication():
    """
        Test that WebApplication extends ThisApplication.
    """
    app = WebApplication(
        name="TestApp",
        logger_name="testapp",
        log_basename="testapp",
        presence_dir="/tmp/testapp",
        log_directory="/tmp/testapp/logs",
        settings_file="/tmp/testapp/settings.config",
        extensions="",
        service_name="testservice",
        from_establish_webapp_persona=True
    )
    
    if not isinstance(app, ThisApplication):
        errmsg = f"Expected WebApplication to be instance of ThisApplication, got {type(app)}"
        raise AssertionError(errmsg)
    
    return


def test_webapplication_inherits_name_property():
    """
        Test that WebApplication inherits the name property from ThisApplication.
    """
    app = WebApplication(
        name="TestApp",
        logger_name="testapp",
        log_basename="testapp",
        presence_dir="/tmp/testapp",
        log_directory="/tmp/testapp/logs",
        settings_file="/tmp/testapp/settings.config",
        extensions="",
        service_name="testservice",
        from_establish_webapp_persona=True
    )
    
    if app.name != "TestApp":
        errmsg = f"Expected name 'TestApp', got '{app.name}'"
        raise AssertionError(errmsg)
    
    return


def test_webapplication_inherits_presence_dir_property():
    """
        Test that WebApplication inherits the presence_dir property from ThisApplication.
    """
    app = WebApplication(
        name="TestApp",
        logger_name="testapp",
        log_basename="testapp",
        presence_dir="/tmp/testapp",
        log_directory="/tmp/testapp/logs",
        settings_file="/tmp/testapp/settings.config",
        extensions="",
        service_name="testservice",
        from_establish_webapp_persona=True
    )
    
    if app.presence_dir != "/tmp/testapp":
        errmsg = f"Expected presence_dir '/tmp/testapp', got '{app.presence_dir}'"
        raise AssertionError(errmsg)
    
    return


def test_webapplication_inherits_logger_name_property():
    """
        Test that WebApplication inherits the logger_name property from ThisApplication.
    """
    app = WebApplication(
        name="TestApp",
        logger_name="testapp",
        log_basename="testapp",
        presence_dir="/tmp/testapp",
        log_directory="/tmp/testapp/logs",
        settings_file="/tmp/testapp/settings.config",
        extensions="",
        service_name="testservice",
        from_establish_webapp_persona=True
    )
    
    if app.logger_name != "testapp":
        errmsg = f"Expected logger_name 'testapp', got '{app.logger_name}'"
        raise AssertionError(errmsg)
    
    return


def test_webapplication_inherits_log_directory_property():
    """
        Test that WebApplication inherits the log_directory property from ThisApplication.
    """
    app = WebApplication(
        name="TestApp",
        logger_name="testapp",
        log_basename="testapp",
        presence_dir="/tmp/testapp",
        log_directory="/tmp/testapp/logs",
        settings_file="/tmp/testapp/settings.config",
        extensions="",
        service_name="testservice",
        from_establish_webapp_persona=True
    )
    
    if app.log_directory != "/tmp/testapp/logs":
        errmsg = f"Expected log_directory '/tmp/testapp/logs', got '{app.log_directory}'"
        raise AssertionError(errmsg)
    
    return


def test_webapplication_inherits_context_property():
    """
        Test that WebApplication inherits the context property from ThisApplication.
    """
    app = WebApplication(
        name="TestApp",
        logger_name="testapp",
        log_basename="testapp",
        presence_dir="/tmp/testapp",
        log_directory="/tmp/testapp/logs",
        settings_file="/tmp/testapp/settings.config",
        extensions="",
        service_name="testservice",
        from_establish_webapp_persona=True
    )
    
    if app.context is None:
        errmsg = "Expected context property to be available"
        raise AssertionError(errmsg)
    
    return


def test_webapplication_inherits_config_parser_property():
    """
        Test that WebApplication inherits the config_parser property from ThisApplication.
    """
    app = WebApplication(
        name="TestApp",
        logger_name="testapp",
        log_basename="testapp",
        presence_dir="/tmp/testapp",
        log_directory="/tmp/testapp/logs",
        settings_file="/tmp/testapp/settings.config",
        extensions="",
        service_name="testservice",
        from_establish_webapp_persona=True
    )
    
    if app.config_parser is None:
        errmsg = "Expected config_parser property to be available"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for WebApplication - Database Hooks
# =============================================================================

def test_webapplication_has_prepare_database_method():
    """
        Test that WebApplication has the prepare_database method.
    """
    app = WebApplication(
        name="TestApp",
        logger_name="testapp",
        log_basename="testapp",
        presence_dir="/tmp/testapp",
        log_directory="/tmp/testapp/logs",
        settings_file="/tmp/testapp/settings.config",
        extensions="",
        service_name="testservice",
        from_establish_webapp_persona=True
    )
    
    if not hasattr(app, 'prepare_database'):
        errmsg = "Expected WebApplication to have prepare_database method"
        raise AssertionError(errmsg)
    
    if not callable(app.prepare_database):
        errmsg = "Expected prepare_database to be callable"
        raise AssertionError(errmsg)
    
    return


def test_webapplication_has_connect_database_method():
    """
        Test that WebApplication has the connect_database method.
    """
    app = WebApplication(
        name="TestApp",
        logger_name="testapp",
        log_basename="testapp",
        presence_dir="/tmp/testapp",
        log_directory="/tmp/testapp/logs",
        settings_file="/tmp/testapp/settings.config",
        extensions="",
        service_name="testservice",
        from_establish_webapp_persona=True
    )
    
    if not hasattr(app, 'connect_database'):
        errmsg = "Expected WebApplication to have connect_database method"
        raise AssertionError(errmsg)
    
    if not callable(app.connect_database):
        errmsg = "Expected connect_database to be callable"
        raise AssertionError(errmsg)
    
    return


def test_webapplication_has_startup_database_method():
    """
        Test that WebApplication has the startup_database method.
    """
    app = WebApplication(
        name="TestApp",
        logger_name="testapp",
        log_basename="testapp",
        presence_dir="/tmp/testapp",
        log_directory="/tmp/testapp/logs",
        settings_file="/tmp/testapp/settings.config",
        extensions="",
        service_name="testservice",
        from_establish_webapp_persona=True
    )
    
    if not hasattr(app, 'startup_database'):
        errmsg = "Expected WebApplication to have startup_database method"
        raise AssertionError(errmsg)
    
    if not callable(app.startup_database):
        errmsg = "Expected startup_database to be callable"
        raise AssertionError(errmsg)
    
    return


def test_webapplication_has_ensure_database_ready_method():
    """
        Test that WebApplication has the ensure_database_ready method.
    """
    app = WebApplication(
        name="TestApp",
        logger_name="testapp",
        log_basename="testapp",
        presence_dir="/tmp/testapp",
        log_directory="/tmp/testapp/logs",
        settings_file="/tmp/testapp/settings.config",
        extensions="",
        service_name="testservice",
        from_establish_webapp_persona=True
    )
    
    if not hasattr(app, 'ensure_database_ready'):
        errmsg = "Expected WebApplication to have ensure_database_ready method"
        raise AssertionError(errmsg)
    
    if not callable(app.ensure_database_ready):
        errmsg = "Expected ensure_database_ready to be callable"
        raise AssertionError(errmsg)
    
    return


def test_webapplication_prepare_database_returns_none():
    """
        Test that the default prepare_database implementation returns None.
    """
    app = WebApplication(
        name="TestApp",
        logger_name="testapp",
        log_basename="testapp",
        presence_dir="/tmp/testapp",
        log_directory="/tmp/testapp/logs",
        settings_file="/tmp/testapp/settings.config",
        extensions="",
        service_name="testservice",
        from_establish_webapp_persona=True
    )
    
    result = app.prepare_database()
    
    if result is not None:
        errmsg = f"Expected prepare_database to return None, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_webapplication_connect_database_returns_none():
    """
        Test that the default connect_database implementation returns None.
    """
    app = WebApplication(
        name="TestApp",
        logger_name="testapp",
        log_basename="testapp",
        presence_dir="/tmp/testapp",
        log_directory="/tmp/testapp/logs",
        settings_file="/tmp/testapp/settings.config",
        extensions="",
        service_name="testservice",
        from_establish_webapp_persona=True
    )
    
    result = app.connect_database()
    
    if result is not None:
        errmsg = f"Expected connect_database to return None, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_webapplication_startup_database_returns_none():
    """
        Test that the default startup_database implementation returns None.
    """
    app = WebApplication(
        name="TestApp",
        logger_name="testapp",
        log_basename="testapp",
        presence_dir="/tmp/testapp",
        log_directory="/tmp/testapp/logs",
        settings_file="/tmp/testapp/settings.config",
        extensions="",
        service_name="testservice",
        from_establish_webapp_persona=True
    )
    
    result = app.startup_database()
    
    if result is not None:
        errmsg = f"Expected startup_database to return None, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_webapplication_ensure_database_ready_returns_true():
    """
        Test that the default ensure_database_ready implementation returns True.
    """
    app = WebApplication(
        name="TestApp",
        logger_name="testapp",
        log_basename="testapp",
        presence_dir="/tmp/testapp",
        log_directory="/tmp/testapp/logs",
        settings_file="/tmp/testapp/settings.config",
        extensions="",
        service_name="testservice",
        from_establish_webapp_persona=True
    )
    
    result = app.ensure_database_ready()
    
    if result is not True:
        errmsg = f"Expected ensure_database_ready to return True, got {result}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for WebApplication - Subclassing
# =============================================================================

def test_webapplication_can_be_subclassed():
    """
        Test that WebApplication can be subclassed.
    """
    class CustomWebApplication(WebApplication):
        pass
    
    app = CustomWebApplication(
        name="CustomApp",
        logger_name="customapp",
        log_basename="customapp",
        presence_dir="/tmp/customapp",
        log_directory="/tmp/customapp/logs",
        settings_file="/tmp/customapp/settings.config",
        extensions="",
        service_name="customservice",
        from_establish_webapp_persona=True
    )
    
    if not isinstance(app, WebApplication):
        errmsg = f"Expected CustomWebApplication to be instance of WebApplication"
        raise AssertionError(errmsg)
    
    if not isinstance(app, ThisApplication):
        errmsg = f"Expected CustomWebApplication to be instance of ThisApplication"
        raise AssertionError(errmsg)
    
    return


def test_webapplication_subclass_can_override_prepare_database():
    """
        Test that a subclass can override the prepare_database method.
    """
    prepare_called = [False]
    
    class CustomWebApplication(WebApplication):
        def prepare_database(self) -> None:
            prepare_called[0] = True
            return
    
    app = CustomWebApplication(
        name="CustomApp",
        logger_name="customapp",
        log_basename="customapp",
        presence_dir="/tmp/customapp",
        log_directory="/tmp/customapp/logs",
        settings_file="/tmp/customapp/settings.config",
        extensions="",
        service_name="customservice",
        from_establish_webapp_persona=True
    )
    
    app.prepare_database()
    
    if not prepare_called[0]:
        errmsg = "Expected overridden prepare_database to be called"
        raise AssertionError(errmsg)
    
    return


def test_webapplication_subclass_can_override_connect_database():
    """
        Test that a subclass can override the connect_database method.
    """
    connect_called = [False]
    
    class CustomWebApplication(WebApplication):
        def connect_database(self) -> None:
            connect_called[0] = True
            return
    
    app = CustomWebApplication(
        name="CustomApp",
        logger_name="customapp",
        log_basename="customapp",
        presence_dir="/tmp/customapp",
        log_directory="/tmp/customapp/logs",
        settings_file="/tmp/customapp/settings.config",
        extensions="",
        service_name="customservice",
        from_establish_webapp_persona=True
    )
    
    app.connect_database()
    
    if not connect_called[0]:
        errmsg = "Expected overridden connect_database to be called"
        raise AssertionError(errmsg)
    
    return


def test_webapplication_subclass_can_override_startup_database():
    """
        Test that a subclass can override the startup_database method.
    """
    startup_called = [False]
    
    class CustomWebApplication(WebApplication):
        def startup_database(self) -> None:
            startup_called[0] = True
            return
    
    app = CustomWebApplication(
        name="CustomApp",
        logger_name="customapp",
        log_basename="customapp",
        presence_dir="/tmp/customapp",
        log_directory="/tmp/customapp/logs",
        settings_file="/tmp/customapp/settings.config",
        extensions="",
        service_name="customservice",
        from_establish_webapp_persona=True
    )
    
    app.startup_database()
    
    if not startup_called[0]:
        errmsg = "Expected overridden startup_database to be called"
        raise AssertionError(errmsg)
    
    return


def test_webapplication_subclass_can_override_ensure_database_ready():
    """
        Test that a subclass can override the ensure_database_ready method.
    """
    class CustomWebApplication(WebApplication):
        def ensure_database_ready(self) -> bool:
            return False
    
    app = CustomWebApplication(
        name="CustomApp",
        logger_name="customapp",
        log_basename="customapp",
        presence_dir="/tmp/customapp",
        log_directory="/tmp/customapp/logs",
        settings_file="/tmp/customapp/settings.config",
        extensions="",
        service_name="customservice",
        from_establish_webapp_persona=True
    )
    
    result = app.ensure_database_ready()
    
    if result is not False:
        errmsg = f"Expected overridden ensure_database_ready to return False, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_webapplication_subclass_can_add_custom_attributes():
    """
        Test that a subclass can add custom attributes.
    """
    class CustomWebApplication(WebApplication):
        def __init__(self, *, custom_attr: str = "default", **kwargs):
            super().__init__(**kwargs)
            self.custom_attr = custom_attr
            return
    
    app = CustomWebApplication(
        name="CustomApp",
        logger_name="customapp",
        log_basename="customapp",
        presence_dir="/tmp/customapp",
        log_directory="/tmp/customapp/logs",
        settings_file="/tmp/customapp/settings.config",
        extensions="",
        service_name="customservice",
        custom_attr="custom_value",
        from_establish_webapp_persona=True
    )
    
    if app.custom_attr != "custom_value":
        errmsg = f"Expected custom_attr 'custom_value', got '{app.custom_attr}'"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Property-Based Tests for WebApplication Inheritance
# =============================================================================

def test_property_webapplication_inheritance_preservation():
    """
        Property 1: WebApplication Inheritance Preservation
        
        For any WebApplication instance or subclass, the instance SHALL be an
        instance of ThisApplication and SHALL have access to all inherited
        persona and variable stack functionality.
        
        This test generates random application configurations and verifies that:
        1. WebApplication instances are always instances of ThisApplication
        2. All inherited properties (name, presence_dir, logger_name, log_directory,
           context, config_parser) are accessible
        3. Subclasses maintain the inheritance chain
        
        **Feature: webapp-persona, Property 1: WebApplication Inheritance Preservation**
        **Validates: Requirements 1.1, 1.6**
    """
    import random
    import string
    
    def generate_random_string(min_len=3, max_len=15):
        """Generate a random alphanumeric string."""
        length = random.randint(min_len, max_len)
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    
    def generate_random_path():
        """Generate a random filesystem path."""
        segments = random.randint(1, 4)
        path_parts = [generate_random_string(3, 10) for _ in range(segments)]
        return "/tmp/" + "/".join(path_parts)
    
    # Run 100 iterations with different random configurations
    for iteration in range(100):
        # Generate random application configuration
        app_name = f"App{generate_random_string()}"
        logger_name = generate_random_string()
        log_basename = generate_random_string()
        presence_dir = generate_random_path()
        log_directory = f"{presence_dir}/logs"
        settings_file = f"{presence_dir}/settings.config"
        extensions = generate_random_string() if random.random() > 0.5 else ""
        service_name = generate_random_string()
        
        # Create WebApplication instance
        app = WebApplication(
            name=app_name,
            logger_name=logger_name,
            log_basename=log_basename,
            presence_dir=presence_dir,
            log_directory=log_directory,
            settings_file=settings_file,
            extensions=extensions,
            service_name=service_name,
            from_establish_webapp_persona=True
        )
        
        # Property 1a: WebApplication must be an instance of ThisApplication
        if not isinstance(app, ThisApplication):
            errmsg = f"Iteration {iteration}: WebApplication is not an instance of ThisApplication. " \
                     f"Type: {type(app)}, MRO: {type(app).__mro__}"
            raise AssertionError(errmsg)
        
        # Property 1b: Inherited name property must be accessible and correct
        if app.name != app_name:
            errmsg = f"Iteration {iteration}: Inherited name property mismatch. " \
                     f"Expected '{app_name}', got '{app.name}'"
            raise AssertionError(errmsg)
        
        # Property 1c: Inherited presence_dir property must be accessible and correct
        if app.presence_dir != presence_dir:
            errmsg = f"Iteration {iteration}: Inherited presence_dir property mismatch. " \
                     f"Expected '{presence_dir}', got '{app.presence_dir}'"
            raise AssertionError(errmsg)
        
        # Property 1d: Inherited logger_name property must be accessible and correct
        if app.logger_name != logger_name:
            errmsg = f"Iteration {iteration}: Inherited logger_name property mismatch. " \
                     f"Expected '{logger_name}', got '{app.logger_name}'"
            raise AssertionError(errmsg)
        
        # Property 1e: Inherited log_directory property must be accessible and correct
        if app.log_directory != log_directory:
            errmsg = f"Iteration {iteration}: Inherited log_directory property mismatch. " \
                     f"Expected '{log_directory}', got '{app.log_directory}'"
            raise AssertionError(errmsg)
        
        # Property 1f: Inherited context property must be accessible (not None)
        if app.context is None:
            errmsg = f"Iteration {iteration}: Inherited context property is None"
            raise AssertionError(errmsg)
        
        # Property 1g: Inherited config_parser property must be accessible (not None)
        if app.config_parser is None:
            errmsg = f"Iteration {iteration}: Inherited config_parser property is None"
            raise AssertionError(errmsg)
    
    return


def test_property_webapplication_subclass_inheritance_preservation():
    """
        Property 1: WebApplication Inheritance Preservation (Subclass variant)
        
        For any WebApplication subclass, the subclass instance SHALL be an
        instance of both WebApplication and ThisApplication, and SHALL have
        access to all inherited persona and variable stack functionality while
        being able to add custom functionality.
        
        This test generates random subclasses with custom attributes and methods,
        verifying that the inheritance chain is preserved.
        
        **Feature: webapp-persona, Property 1: WebApplication Inheritance Preservation**
        **Validates: Requirements 1.1, 1.6**
    """
    import random
    import string
    
    def generate_random_string(min_len=3, max_len=15):
        """Generate a random alphanumeric string."""
        length = random.randint(min_len, max_len)
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    
    def generate_random_path():
        """Generate a random filesystem path."""
        segments = random.randint(1, 4)
        path_parts = [generate_random_string(3, 10) for _ in range(segments)]
        return "/tmp/" + "/".join(path_parts)
    
    # Run 100 iterations with different random configurations and subclass variations
    for iteration in range(100):
        # Generate random application configuration
        app_name = f"SubApp{generate_random_string()}"
        logger_name = generate_random_string()
        log_basename = generate_random_string()
        presence_dir = generate_random_path()
        log_directory = f"{presence_dir}/logs"
        settings_file = f"{presence_dir}/settings.config"
        extensions = generate_random_string() if random.random() > 0.5 else ""
        service_name = generate_random_string()
        
        # Generate random custom attribute value
        custom_value = generate_random_string()
        
        # Create a dynamic subclass with custom attributes
        class CustomWebApplication(WebApplication):
            def __init__(self, *, custom_attr: str = "default", **kwargs):
                super().__init__(**kwargs)
                self.custom_attr = custom_attr
                return
            
            def custom_method(self) -> str:
                return f"custom_{self.name}"
        
        # Create subclass instance
        app = CustomWebApplication(
            name=app_name,
            logger_name=logger_name,
            log_basename=log_basename,
            presence_dir=presence_dir,
            log_directory=log_directory,
            settings_file=settings_file,
            extensions=extensions,
            service_name=service_name,
            custom_attr=custom_value,
            from_establish_webapp_persona=True
        )
        
        # Property 1a: Subclass must be an instance of WebApplication
        if not isinstance(app, WebApplication):
            errmsg = f"Iteration {iteration}: Subclass is not an instance of WebApplication. " \
                     f"Type: {type(app)}"
            raise AssertionError(errmsg)
        
        # Property 1b: Subclass must be an instance of ThisApplication
        if not isinstance(app, ThisApplication):
            errmsg = f"Iteration {iteration}: Subclass is not an instance of ThisApplication. " \
                     f"Type: {type(app)}, MRO: {type(app).__mro__}"
            raise AssertionError(errmsg)
        
        # Property 1c: Inherited name property must be accessible and correct
        if app.name != app_name:
            errmsg = f"Iteration {iteration}: Inherited name property mismatch. " \
                     f"Expected '{app_name}', got '{app.name}'"
            raise AssertionError(errmsg)
        
        # Property 1d: Inherited presence_dir property must be accessible and correct
        if app.presence_dir != presence_dir:
            errmsg = f"Iteration {iteration}: Inherited presence_dir property mismatch. " \
                     f"Expected '{presence_dir}', got '{app.presence_dir}'"
            raise AssertionError(errmsg)
        
        # Property 1e: Inherited context property must be accessible (not None)
        if app.context is None:
            errmsg = f"Iteration {iteration}: Inherited context property is None"
            raise AssertionError(errmsg)
        
        # Property 1f: Inherited config_parser property must be accessible (not None)
        if app.config_parser is None:
            errmsg = f"Iteration {iteration}: Inherited config_parser property is None"
            raise AssertionError(errmsg)
        
        # Property 1g: Custom attribute must be accessible and correct
        if app.custom_attr != custom_value:
            errmsg = f"Iteration {iteration}: Custom attribute mismatch. " \
                     f"Expected '{custom_value}', got '{app.custom_attr}'"
            raise AssertionError(errmsg)
        
        # Property 1h: Custom method must work correctly
        expected_custom_result = f"custom_{app_name}"
        actual_custom_result = app.custom_method()
        if actual_custom_result != expected_custom_result:
            errmsg = f"Iteration {iteration}: Custom method result mismatch. " \
                     f"Expected '{expected_custom_result}', got '{actual_custom_result}'"
            raise AssertionError(errmsg)
        
        # Property 1i: Database hooks must be accessible from subclass
        if not callable(app.prepare_database):
            errmsg = f"Iteration {iteration}: prepare_database is not callable"
            raise AssertionError(errmsg)
        
        if not callable(app.connect_database):
            errmsg = f"Iteration {iteration}: connect_database is not callable"
            raise AssertionError(errmsg)
        
        if not callable(app.startup_database):
            errmsg = f"Iteration {iteration}: startup_database is not callable"
            raise AssertionError(errmsg)
        
        if not callable(app.ensure_database_ready):
            errmsg = f"Iteration {iteration}: ensure_database_ready is not callable"
            raise AssertionError(errmsg)
    
    return
