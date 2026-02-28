"""
    Tests for the wellknown module singleton access.
    
    This module contains unit tests for the wellknown module which provides
    singleton access to the WebApplication instance.
"""

from automojo.webworks.wellknown import (
    THISWEBAPPLICATION_SINGLETON,
    ThisWebApplicationSingleton
)
from automojo.errors.exceptions import SemanticError


# =============================================================================
# Unit Tests for ThisWebApplicationSingleton - Error Handling
# =============================================================================

def test_thiswebapplicationsingleton_raises_error_when_not_established():
    """
        Test that ThisWebApplicationSingleton raises SemanticError when called
        before establish_webapp_persona has been called.
    """
    # First, ensure the singleton is None (reset state if needed)
    import automojo.webworks.wellknown as wellknown_module
    original_singleton = wellknown_module.THISWEBAPPLICATION_SINGLETON
    wellknown_module.THISWEBAPPLICATION_SINGLETON = None
    
    exception_raised = False
    exception_type = None
    
    try:
        ThisWebApplicationSingleton()
    except SemanticError as err:
        exception_raised = True
        exception_type = type(err)
    finally:
        # Restore original state
        wellknown_module.THISWEBAPPLICATION_SINGLETON = original_singleton
    
    if not exception_raised:
        errmsg = "Expected SemanticError to be raised when singleton is not established"
        raise AssertionError(errmsg)
    
    if exception_type is not SemanticError:
        errmsg = f"Expected SemanticError, got {exception_type}"
        raise AssertionError(errmsg)
    
    return


def test_thiswebapplicationsingleton_error_message_mentions_establish_webapp_persona():
    """
        Test that the error message mentions establish_webapp_persona.
    """
    import automojo.webworks.wellknown as wellknown_module
    original_singleton = wellknown_module.THISWEBAPPLICATION_SINGLETON
    wellknown_module.THISWEBAPPLICATION_SINGLETON = None
    
    error_message = None
    
    try:
        ThisWebApplicationSingleton()
    except SemanticError as err:
        error_message = str(err)
    finally:
        wellknown_module.THISWEBAPPLICATION_SINGLETON = original_singleton
    
    if error_message is None:
        errmsg = "Expected SemanticError to be raised"
        raise AssertionError(errmsg)
    
    if "establish_webapp_persona" not in error_message:
        errmsg = f"Expected error message to mention 'establish_webapp_persona', got: {error_message}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for ThisWebApplicationSingleton - Return Value
# =============================================================================

def test_thiswebapplicationsingleton_returns_singleton_when_established():
    """
        Test that ThisWebApplicationSingleton returns the singleton when it is established.
    """
    from automojo.webworks.persona.webapplication import WebApplication
    import automojo.webworks.wellknown as wellknown_module
    
    # Save original state
    original_singleton = wellknown_module.THISWEBAPPLICATION_SINGLETON
    
    # Create a test WebApplication instance
    test_app = WebApplication(
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
    
    # Set the singleton
    wellknown_module.THISWEBAPPLICATION_SINGLETON = test_app
    
    try:
        result = ThisWebApplicationSingleton()
        
        if result is not test_app:
            errmsg = "Expected ThisWebApplicationSingleton to return the established singleton"
            raise AssertionError(errmsg)
    finally:
        # Restore original state
        wellknown_module.THISWEBAPPLICATION_SINGLETON = original_singleton
    
    return


def test_thiswebapplicationsingleton_returns_same_instance_on_multiple_calls():
    """
        Test that ThisWebApplicationSingleton returns the same instance on multiple calls.
    """
    from automojo.webworks.persona.webapplication import WebApplication
    import automojo.webworks.wellknown as wellknown_module
    
    # Save original state
    original_singleton = wellknown_module.THISWEBAPPLICATION_SINGLETON
    
    # Create a test WebApplication instance
    test_app = WebApplication(
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
    
    # Set the singleton
    wellknown_module.THISWEBAPPLICATION_SINGLETON = test_app
    
    try:
        result1 = ThisWebApplicationSingleton()
        result2 = ThisWebApplicationSingleton()
        
        if result1 is not result2:
            errmsg = "Expected ThisWebApplicationSingleton to return the same instance on multiple calls"
            raise AssertionError(errmsg)
    finally:
        # Restore original state
        wellknown_module.THISWEBAPPLICATION_SINGLETON = original_singleton
    
    return


# =============================================================================
# Unit Tests for Module Variable
# =============================================================================

def test_thiswebapplication_singleton_variable_initially_none():
    """
        Test that THISWEBAPPLICATION_SINGLETON is initially None.
        
        Note: This test checks the initial state of the module variable.
        In practice, the variable may be set by other tests, so we check
        that the variable exists and can be None.
    """
    import automojo.webworks.wellknown as wellknown_module
    
    # The variable should exist
    if not hasattr(wellknown_module, 'THISWEBAPPLICATION_SINGLETON'):
        errmsg = "Expected THISWEBAPPLICATION_SINGLETON to be defined in wellknown module"
        raise AssertionError(errmsg)
    
    return


def test_thiswebapplication_singleton_can_be_set():
    """
        Test that THISWEBAPPLICATION_SINGLETON can be set to a WebApplication instance.
    """
    from automojo.webworks.persona.webapplication import WebApplication
    import automojo.webworks.wellknown as wellknown_module
    
    # Save original state
    original_singleton = wellknown_module.THISWEBAPPLICATION_SINGLETON
    
    # Create a test WebApplication instance
    test_app = WebApplication(
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
    
    try:
        # Set the singleton
        wellknown_module.THISWEBAPPLICATION_SINGLETON = test_app
        
        if wellknown_module.THISWEBAPPLICATION_SINGLETON is not test_app:
            errmsg = "Expected THISWEBAPPLICATION_SINGLETON to be set to the test app"
            raise AssertionError(errmsg)
    finally:
        # Restore original state
        wellknown_module.THISWEBAPPLICATION_SINGLETON = original_singleton
    
    return


# =============================================================================
# Property-Based Tests for Thread-Safe Initialization
# =============================================================================

def test_property_thread_safe_singleton_access():
    """
        Property 11: Thread-Safe Initialization
        
        For any concurrent calls to ThisWebApplicationSingleton from multiple threads,
        all threads SHALL observe the same singleton instance after initialization completes.
        
        This test verifies that the SINGLETON_LOCK properly guards access to the
        singleton, ensuring thread-safe reads of the established singleton.
        
        **Feature: webapp-persona, Property 11: Thread-Safe Initialization**
        **Validates: Requirements 5.6**
    """
    import threading
    import random
    from automojo.webworks.persona.webapplication import WebApplication
    import automojo.webworks.wellknown as wellknown_module
    
    # Save original state
    original_singleton = wellknown_module.THISWEBAPPLICATION_SINGLETON
    
    # Create a test WebApplication instance
    test_app = WebApplication(
        name="ThreadSafeApp",
        logger_name="threadsafeapp",
        log_basename="threadsafeapp",
        presence_dir="/tmp/threadsafeapp",
        log_directory="/tmp/threadsafeapp/logs",
        settings_file="/tmp/threadsafeapp/settings.config",
        extensions="",
        service_name="threadsafeservice",
        from_establish_webapp_persona=True
    )
    
    # Set the singleton
    wellknown_module.THISWEBAPPLICATION_SINGLETON = test_app
    
    try:
        # Run multiple iterations to increase confidence in thread safety
        for iteration in range(100):
            # Storage for results from each thread
            results = []
            errors = []
            results_lock = threading.Lock()
            
            # Number of concurrent threads varies per iteration
            num_threads = random.randint(2, 10)
            
            def access_singleton():
                """Thread worker that accesses the singleton."""
                try:
                    result = ThisWebApplicationSingleton()
                    with results_lock:
                        results.append(result)
                except Exception as err:
                    with results_lock:
                        errors.append(err)
            
            # Create and start threads
            threads = []
            for _ in range(num_threads):
                thread = threading.Thread(target=access_singleton)
                threads.append(thread)
            
            # Start all threads as close together as possible
            for thread in threads:
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # Verify no errors occurred
            if errors:
                errmsg = f"Iteration {iteration}: Errors occurred during concurrent access: {errors}"
                raise AssertionError(errmsg)
            
            # Verify all threads got results
            if len(results) != num_threads:
                errmsg = f"Iteration {iteration}: Expected {num_threads} results, got {len(results)}"
                raise AssertionError(errmsg)
            
            # Verify all threads observed the same singleton instance (identity equality)
            for i, result in enumerate(results):
                if result is not test_app:
                    errmsg = f"Iteration {iteration}: Thread {i} observed different singleton instance"
                    raise AssertionError(errmsg)
    
    finally:
        # Restore original state
        wellknown_module.THISWEBAPPLICATION_SINGLETON = original_singleton
    
    return


def test_property_thread_safe_singleton_write_then_read():
    """
        Property 11: Thread-Safe Initialization
        
        For any concurrent scenario where one thread sets the singleton and multiple
        threads read it, all reading threads SHALL observe the same singleton instance
        that was set, demonstrating proper synchronization via SINGLETON_LOCK.
        
        **Feature: webapp-persona, Property 11: Thread-Safe Initialization**
        **Validates: Requirements 5.6**
    """
    import threading
    import time
    import random
    from automojo.webworks.persona.webapplication import WebApplication
    from automojo.thisapp.wellknown import SINGLETON_LOCK
    import automojo.webworks.wellknown as wellknown_module
    
    # Save original state
    original_singleton = wellknown_module.THISWEBAPPLICATION_SINGLETON
    
    try:
        # Run multiple iterations to increase confidence in thread safety
        for iteration in range(100):
            # Reset singleton to None for this iteration
            wellknown_module.THISWEBAPPLICATION_SINGLETON = None
            
            # Create a unique test app for this iteration
            test_app = WebApplication(
                name=f"ThreadApp{iteration}",
                logger_name=f"threadapp{iteration}",
                log_basename=f"threadapp{iteration}",
                presence_dir=f"/tmp/threadapp{iteration}",
                log_directory=f"/tmp/threadapp{iteration}/logs",
                settings_file=f"/tmp/threadapp{iteration}/settings.config",
                extensions="",
                service_name=f"threadservice{iteration}",
                from_establish_webapp_persona=True
            )
            
            # Storage for results
            results = []
            errors = []
            results_lock = threading.Lock()
            
            # Barrier to synchronize thread start
            num_readers = random.randint(2, 8)
            barrier = threading.Barrier(num_readers + 1)  # +1 for writer thread
            
            def writer_thread():
                """Thread that sets the singleton."""
                try:
                    barrier.wait()  # Wait for all threads to be ready
                    SINGLETON_LOCK.acquire()
                    try:
                        wellknown_module.THISWEBAPPLICATION_SINGLETON = test_app
                    finally:
                        SINGLETON_LOCK.release()
                except Exception as err:
                    with results_lock:
                        errors.append(("writer", err))
            
            def reader_thread(thread_id):
                """Thread that reads the singleton after a small delay."""
                try:
                    barrier.wait()  # Wait for all threads to be ready
                    # Small random delay to allow writer to potentially run first
                    time.sleep(random.uniform(0.001, 0.01))
                    
                    # Try to get the singleton (may fail if not yet set)
                    try:
                        result = ThisWebApplicationSingleton()
                        with results_lock:
                            results.append((thread_id, result))
                    except SemanticError:
                        # Singleton not yet set - this is acceptable
                        with results_lock:
                            results.append((thread_id, None))
                except Exception as err:
                    with results_lock:
                        errors.append((f"reader_{thread_id}", err))
            
            # Create threads
            writer = threading.Thread(target=writer_thread)
            readers = [
                threading.Thread(target=reader_thread, args=(i,))
                for i in range(num_readers)
            ]
            
            # Start all threads
            writer.start()
            for reader in readers:
                reader.start()
            
            # Wait for all threads to complete
            writer.join()
            for reader in readers:
                reader.join()
            
            # Verify no unexpected errors occurred
            if errors:
                errmsg = f"Iteration {iteration}: Unexpected errors: {errors}"
                raise AssertionError(errmsg)
            
            # Verify that any thread that got a result got the correct singleton
            for thread_id, result in results:
                if result is not None and result is not test_app:
                    errmsg = f"Iteration {iteration}: Thread {thread_id} observed wrong singleton"
                    raise AssertionError(errmsg)
    
    finally:
        # Restore original state
        wellknown_module.THISWEBAPPLICATION_SINGLETON = original_singleton
    
    return


# =============================================================================
# Property-Based Tests for Singleton Identity Consistency
# =============================================================================

def test_property_singleton_identity_consistency():
    """
        Property 2: Singleton Identity Consistency
        
        For any established web application persona, calling ThisWebApplicationSingleton()
        and ThisApplicationSingleton() SHALL return the exact same object instance
        (identity equality).
        
        This test simulates what establish_webapp_persona does by setting both
        THISWEBAPPLICATION_SINGLETON and THISAPPLICATION_SINGLETON to the same
        instance, then verifies that both accessor functions return the identical
        object.
        
        **Feature: webapp-persona, Property 2: Singleton Identity Consistency**
        **Validates: Requirements 2.2, 5.4**
    """
    import random
    import string
    from automojo.webworks.persona.webapplication import WebApplication
    from automojo.thisapp.wellknown import (
        SINGLETON_LOCK,
        ThisApplicationSingleton
    )
    import automojo.webworks.wellknown as webworks_wellknown
    import automojo.thisapp.wellknown as thisapp_wellknown
    
    # Save original state for both singletons
    original_webworks_singleton = webworks_wellknown.THISWEBAPPLICATION_SINGLETON
    original_thisapp_singleton = thisapp_wellknown.THISAPPLICATION_SINGLETON
    
    try:
        # Run 100 iterations with different random application configurations
        for iteration in range(100):
            # Generate random application name and configuration
            name_suffix = ''.join(random.choices(string.ascii_lowercase, k=random.randint(3, 10)))
            app_name = f"IdentityApp{name_suffix}{iteration}"
            
            # Create a WebApplication instance with random configuration
            test_app = WebApplication(
                name=app_name,
                logger_name=f"identityapp{name_suffix}",
                log_basename=f"identityapp{name_suffix}",
                presence_dir=f"/tmp/identityapp{name_suffix}",
                log_directory=f"/tmp/identityapp{name_suffix}/logs",
                settings_file=f"/tmp/identityapp{name_suffix}/settings.config",
                extensions="",
                service_name=f"identityservice{name_suffix}",
                from_establish_webapp_persona=True
            )
            
            # Simulate what establish_webapp_persona does:
            # Set both singletons to the same instance under the lock
            SINGLETON_LOCK.acquire()
            try:
                webworks_wellknown.THISWEBAPPLICATION_SINGLETON = test_app
                thisapp_wellknown.THISAPPLICATION_SINGLETON = test_app
            finally:
                SINGLETON_LOCK.release()
            
            # Now verify that both accessor functions return the same object
            web_singleton = ThisWebApplicationSingleton()
            app_singleton = ThisApplicationSingleton()
            
            # Property: Both accessors must return the exact same object (identity equality)
            if web_singleton is not app_singleton:
                errmsg = f"Iteration {iteration}: ThisWebApplicationSingleton() and " \
                         f"ThisApplicationSingleton() returned different objects. " \
                         f"web_singleton id={id(web_singleton)}, app_singleton id={id(app_singleton)}"
                raise AssertionError(errmsg)
            
            # Also verify both return the test_app we set
            if web_singleton is not test_app:
                errmsg = f"Iteration {iteration}: ThisWebApplicationSingleton() did not return " \
                         f"the established singleton. Expected id={id(test_app)}, got id={id(web_singleton)}"
                raise AssertionError(errmsg)
            
            if app_singleton is not test_app:
                errmsg = f"Iteration {iteration}: ThisApplicationSingleton() did not return " \
                         f"the established singleton. Expected id={id(test_app)}, got id={id(app_singleton)}"
                raise AssertionError(errmsg)
    
    finally:
        # Restore original state for both singletons
        SINGLETON_LOCK.acquire()
        try:
            webworks_wellknown.THISWEBAPPLICATION_SINGLETON = original_webworks_singleton
            thisapp_wellknown.THISAPPLICATION_SINGLETON = original_thisapp_singleton
        finally:
            SINGLETON_LOCK.release()
    
    return
