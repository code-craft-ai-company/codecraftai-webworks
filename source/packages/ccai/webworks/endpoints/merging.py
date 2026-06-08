"""
.. module:: merging
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Constraint merge utilities for blueprint endpoint inheritance.

.. moduleauthor:: Code Craft AI LLC

This module provides the ConstraintMerger utility class for merging parent
and child constraints following the blueprint inheritance rules. It handles
access policies, rate limits, and tags with configurable merge behaviors.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

from typing import List, Optional

from ccai.webworks.endpoints.accesspolicy import AccessPolicy
from ccai.webworks.endpoints.ratelimit import RateLimit


class ConstraintMerger:
    """
        Utility class for merging parent and child constraints following
        the blueprint inheritance rules.
        
        This class provides static methods for merging:
        - Access policies (roles, scopes, authentication requirements)
        - Rate limits (most restrictive wins)
        - Tags (merge, replace, or child-wins behaviors)
        
        All methods are static and the class is not meant to be instantiated.
    """
    
    @staticmethod
    def merge_access_policies(
        parent: Optional[AccessPolicy],
        child: Optional[AccessPolicy],
        replace_roles: bool = False,
        replace_scopes: bool = False
    ) -> Optional[AccessPolicy]:
        """
            Merge parent and child access policies.
            
            Rules:
            - If child is None, inherit parent
            - If parent is None, use child
            - If both exist, merge with logical AND for combined constraints
            - For roles/scopes: union by default, replace if flag set
            - Combined policy enforces all constraints (logical AND)
            
            :param parent: Parent access policy.
            :param child: Child access policy.
            :param replace_roles: If True, child roles replace parent roles.
            :param replace_scopes: If True, child scopes replace parent scopes.
            
            :returns: Merged AccessPolicy or None if both are None.
        """
        # Handle None cases
        if parent is None and child is None:
            return None
        
        if child is None:
            # Inherit parent
            return parent
        
        if parent is None:
            # Use child
            return child
        
        # Both exist - merge them using AccessPolicy.merge_with
        # This enforces all constraints via logical AND
        return parent.merge_with(
            child,
            replace_roles=replace_roles,
            replace_scopes=replace_scopes
        )
    
    @staticmethod
    def merge_rate_limits(
        parent: Optional[RateLimit],
        child: Optional[RateLimit]
    ) -> Optional[RateLimit]:
        """
            Merge parent and child rate limits.
            
            Rules:
            - If child is None, inherit parent
            - If parent is None, use child
            - If both exist, return most restrictive limit
            - Child can explicitly opt out by setting rate_limit=None
              (handled by caller passing None for child)
            
            :param parent: Parent rate limit.
            :param child: Child rate limit.
            
            :returns: Most restrictive RateLimit or None if both are None.
        """
        # Handle None cases - inherit parent if child not set
        if child is None:
            return parent
        
        if parent is None:
            return child
        
        # Both exist - return most restrictive
        return RateLimit.most_restrictive(parent, child)
    
    @staticmethod
    def merge_tags(
        parent: List[str],
        child: List[str],
        merge: bool = False,
        replace: bool = False
    ) -> List[str]:
        """
            Merge parent and child tags.
            
            Rules:
            - If replace=True, child tags fully replace parent
            - If merge=True, parent tags are appended to child tags
            - Otherwise (default), child tags win if set, else inherit parent
            
            :param parent: Parent tags.
            :param child: Child tags.
            :param merge: If True, merge parent and child tags (parent appended to child).
            :param replace: If True, child replaces parent entirely.
            
            :returns: Merged tag list.
        """
        # Handle replace mode - child fully replaces parent
        if replace:
            return list(child)
        
        # Handle merge mode - parent tags appended to child tags
        if merge:
            merged = list(child)
            for tag in parent:
                if tag not in merged:
                    merged.append(tag)
            return merged
        
        # Default behavior: child wins if set, else inherit parent
        if child:
            return list(child)
        else:
            return list(parent)
