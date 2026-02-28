"""
.. module:: constraints
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Endpoint constraints dataclass for normalized constraint objects.

.. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

from dataclasses import dataclass, field
from typing import List, Optional

from automojo.webworks.endpoints.accesspolicy import AccessPolicy
from automojo.webworks.endpoints.ratelimit import RateLimit


@dataclass
class EndpointConstraints:
    """
        Normalized constraint objects for policy engines to introspect.
        
        This dataclass aggregates all security and rate limiting constraints
        for an endpoint into a single object that can be easily inspected
        and merged during endpoint registration.
        
        :param access_policy: The access policy for the endpoint.
        :param rate_limit: The rate limit for the endpoint.
        :param scopes: List of OAuth scopes required for the endpoint.
        :param roles: List of roles that grant access to the endpoint.
    """
    
    access_policy: Optional[AccessPolicy] = None
    rate_limit: Optional[RateLimit] = None
    scopes: List[str] = field(default_factory=list)
    roles: List[str] = field(default_factory=list)
    
    @classmethod
    def merge(
        cls,
        parent: "EndpointConstraints",
        child: "EndpointConstraints",
        replace_scopes: bool = False,
        replace_roles: bool = False
    ) -> "EndpointConstraints":
        """
            Merge parent and child constraints following inheritance rules.
            
            Security-related attributes follow a "parent defaults, child overrides"
            strategy. For list-like fields (roles, scopes), the default behavior
            is union (parent union child). When replace flags are set, the child
            list fully replaces the parent list.
            
            Rate limits stack with the most restrictive window applying unless
            the child explicitly opts out via rate_limit=None on the child.
            
            :param parent: Parent constraint set.
            :param child: Child constraint set.
            :param replace_scopes: If True, child scopes replace parent scopes.
            :param replace_roles: If True, child roles replace parent roles.
            
            :returns: Merged EndpointConstraints with combined policies.
        """
        # Merge access policies
        merged_access_policy = cls._merge_access_policies(
            parent.access_policy,
            child.access_policy,
            replace_roles=replace_roles,
            replace_scopes=replace_scopes
        )
        
        # Merge rate limits - most restrictive wins
        merged_rate_limit = cls._merge_rate_limits(
            parent.rate_limit,
            child.rate_limit
        )
        
        # Merge scopes
        merged_scopes = cls._merge_list_field(
            parent.scopes,
            child.scopes,
            replace=replace_scopes
        )
        
        # Merge roles
        merged_roles = cls._merge_list_field(
            parent.roles,
            child.roles,
            replace=replace_roles
        )
        
        return cls(
            access_policy=merged_access_policy,
            rate_limit=merged_rate_limit,
            scopes=merged_scopes,
            roles=merged_roles
        )
    
    @staticmethod
    def _merge_access_policies(
        parent_policy: Optional[AccessPolicy],
        child_policy: Optional[AccessPolicy],
        replace_roles: bool = False,
        replace_scopes: bool = False
    ) -> Optional[AccessPolicy]:
        """
            Merge parent and child access policies.
            
            If child does not set a policy, inherit from parent.
            If child sets a policy, merge with parent policy.
            
            :param parent_policy: Parent access policy.
            :param child_policy: Child access policy.
            :param replace_roles: If True, child roles replace parent roles.
            :param replace_scopes: If True, child scopes replace parent scopes.
            
            :returns: Merged AccessPolicy or None if both are None.
        """
        if parent_policy is None and child_policy is None:
            return None
        
        if parent_policy is None:
            return child_policy
        
        if child_policy is None:
            return parent_policy
        
        # Both exist - merge them
        return parent_policy.merge_with(
            child_policy,
            replace_roles=replace_roles,
            replace_scopes=replace_scopes
        )
    
    @staticmethod
    def _merge_rate_limits(
        parent_limit: Optional[RateLimit],
        child_limit: Optional[RateLimit]
    ) -> Optional[RateLimit]:
        """
            Merge parent and child rate limits.
            
            The most restrictive rate limit applies. If child explicitly
            sets rate_limit, it participates in the comparison.
            
            :param parent_limit: Parent rate limit.
            :param child_limit: Child rate limit.
            
            :returns: Most restrictive RateLimit or None if both are None.
        """
        return RateLimit.most_restrictive(parent_limit, child_limit)
    
    @staticmethod
    def _merge_list_field(
        parent_list: List[str],
        child_list: List[str],
        replace: bool = False
    ) -> List[str]:
        """
            Merge parent and child list fields.
            
            By default, performs union (parent union child) preserving order.
            When replace is True, child list fully replaces parent list.
            
            :param parent_list: Parent list values.
            :param child_list: Child list values.
            :param replace: If True, child replaces parent.
            
            :returns: Merged list.
        """
        if replace:
            return list(child_list)
        
        # Union preserving order (parent first, then child)
        merged = list(parent_list)
        for item in child_list:
            if item not in merged:
                merged.append(item)
        
        return merged
