"""
.. module:: ratelimit
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Rate limiting constraint dataclass for endpoint throttling.

.. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

from dataclasses import dataclass
from typing import Optional


@dataclass
class RateLimit:
    """
        Rate limiting constraint for an endpoint.
        
        This dataclass defines request throttling parameters that can be
        applied to endpoints to limit the number of requests within a
        time window.
        
        :param requests: Maximum number of requests allowed in the window.
        :param window: Time window in seconds.
    """
    
    requests: int
    window: int  # seconds
    
    @classmethod
    def most_restrictive(cls, *limits: Optional["RateLimit"]) -> Optional["RateLimit"]:
        """
            Return the most restrictive rate limit from a set.
            
            The most restrictive limit is determined by the lowest
            requests-per-second ratio.
            
            :param limits: Rate limits to compare (None values ignored).
            
            :returns: The most restrictive RateLimit, or None if all are None.
        """
        valid_limits = [limit for limit in limits if limit is not None]
        
        if not valid_limits:
            return None
        
        # Calculate requests per second for comparison
        # Lower ratio = more restrictive
        def requests_per_second(limit: "RateLimit") -> float:
            if limit.window == 0:
                return float('inf')
            return limit.requests / limit.window
        
        return min(valid_limits, key=requests_per_second)
