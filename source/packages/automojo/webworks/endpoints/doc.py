"""
.. module:: doc
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Documentation metadata dataclass for endpoint descriptions.

.. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

from dataclasses import dataclass
from typing import Optional


@dataclass
class Doc:
    """
        Documentation metadata for an endpoint.
        
        This dataclass holds documentation information that can be used
        for generating OpenAPI specifications and other documentation
        artifacts.
        
        :param summary: A brief summary of the endpoint's purpose.
        :param description: A detailed description of the endpoint.
        :param deprecated: Whether the endpoint is deprecated.
        :param external_docs: URL to external documentation.
    """
    
    summary: Optional[str] = None
    description: Optional[str] = None
    deprecated: bool = False
    external_docs: Optional[str] = None
