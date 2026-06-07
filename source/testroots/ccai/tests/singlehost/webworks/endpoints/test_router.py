"""
.. module:: test_router
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Tests for the Router protocol.

.. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

from ccai.webworks.endpoints.router import Router
from ccai.webworks.endpoints.descriptor import EndpointDescriptor
from ccai.webworks.endpoints.constraints import EndpointConstraints


def test_router_protocol_exists():
    """
        Verify that the Router protocol is defined and importable.
    """
    if Router is None:
        raise AssertionError("Router protocol should be defined")
    return


def test_router_protocol_is_runtime_checkable():
    """
        Verify that the Router protocol is runtime checkable.
    """
    # Create a class that implements the Router protocol
    class TestRouter:
        def __init__(self):
            self.endpoints = []
        
        def add_endpoint(self, descriptor: EndpointDescriptor) -> None:
            self.endpoints.append(descriptor)
    
    router = TestRouter()
    
    # Verify isinstance check works
    if not isinstance(router, Router):
        raise AssertionError("TestRouter should be recognized as implementing Router protocol")
    
    return


def test_router_protocol_rejects_non_conforming_class():
    """
        Verify that classes not implementing add_endpoint are not recognized.
    """
    class NotARouter:
        def some_other_method(self):
            pass
    
    not_router = NotARouter()
    
    if isinstance(not_router, Router):
        raise AssertionError("NotARouter should not be recognized as implementing Router protocol")
    
    return


def test_router_implementation_receives_descriptor():
    """
        Verify that a Router implementation can receive EndpointDescriptor.
    """
    class TestRouter:
        def __init__(self):
            self.endpoints = []
        
        def add_endpoint(self, descriptor: EndpointDescriptor) -> None:
            self.endpoints.append(descriptor)
    
    def sample_handler():
        return "hello"
    
    descriptor = EndpointDescriptor(
        handler=sample_handler,
        module="test_module",
        leaf="test",
        methods=["GET"],
        constraints=EndpointConstraints()
    )
    
    router = TestRouter()
    router.add_endpoint(descriptor)
    
    if len(router.endpoints) != 1:
        raise AssertionError(f"Expected 1 endpoint, got {len(router.endpoints)}")
    
    if router.endpoints[0].leaf != "test":
        raise AssertionError(f"Expected leaf='test', got {router.endpoints[0].leaf}")
    
    return


def test_router_protocol_has_add_endpoint_method():
    """
        Verify that the Router protocol defines add_endpoint method.
    """
    if not hasattr(Router, "add_endpoint"):
        raise AssertionError("Router protocol should have add_endpoint method")
    
    return


def test_router_can_be_imported_from_package():
    """
        Verify that Router can be imported from the endpoints package.
    """
    from ccai.webworks.endpoints import Router as PackageRouter
    
    if PackageRouter is None:
        raise AssertionError("Router should be importable from endpoints package")
    
    if PackageRouter is not Router:
        raise AssertionError("Router from package should be same as direct import")
    
    return
