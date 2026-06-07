"""
.. module:: router
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Router protocol defining the minimal interface for endpoint registration.

.. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from ccai.webworks.endpoints.descriptor import EndpointDescriptor


@runtime_checkable
class Router(Protocol):
    """
        Protocol defining the minimal router interface for endpoint registration.
        
        This protocol specifies the contract that routers must implement to
        receive endpoint descriptors from the endpoint registration system.
        Routers consume descriptors via the `add_endpoint` method, which is
        called during blueprint registration or direct endpoint attachment.
        
        The protocol is marked as runtime_checkable to allow isinstance()
        checks against router implementations.
        
        Example implementation::
        
            class MyRouter:
                def __init__(self):
                    self._endpoints = []
                
                def add_endpoint(self, descriptor: EndpointDescriptor) -> None:
                    self._endpoints.append(descriptor)
                    # Configure routing based on descriptor.path/leaf and methods
    """
    
    def add_endpoint(self, descriptor: "EndpointDescriptor") -> None:
        """
            Add an endpoint descriptor to the router.
            
            This method is called by blueprints and endpoint registration
            mechanisms to register endpoints with the router. The router
            should use the descriptor's path, methods, and handler to
            configure routing.
            
            :param descriptor: The EndpointDescriptor containing handler
                              reference and merged metadata for routing.
        """
        ...
