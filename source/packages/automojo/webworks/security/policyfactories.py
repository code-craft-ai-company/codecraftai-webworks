"""
.. module:: policyfactories
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Convenience factory functions for creating common AccessPolicy
        configurations.

.. moduleauthor:: Automation Mojo LLC

This module provides factory functions that create AccessPolicy instances for
common security patterns. The factories simplify the creation of policies for
public endpoints, authenticated-only endpoints, role-based access, and
scope-based access.

Each factory returns an immutable AccessPolicy instance that can be passed
directly to attach_at() or attach_child() when configuring endpoint security.
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

from automojo.webworks.security.accesspolicy import AccessPolicy


def public() -> AccessPolicy:
    """
        Create a policy that allows unauthenticated access.

        This factory is intended for endpoints that should be accessible
        without any authentication, such as health checks or public pages.

        :returns: An AccessPolicy with require_auth set to False.
    """
    rtnval = AccessPolicy(require_auth=False)

    return rtnval


def authenticated() -> AccessPolicy:
    """
        Create a policy requiring any authenticated user.

        This factory is intended for endpoints that require a valid
        authenticated identity but do not impose any specific role
        or scope requirements.

        :returns: An AccessPolicy with require_auth set to True and no
            role or scope requirements.
    """
    rtnval = AccessPolicy(require_auth=True)

    return rtnval


def roles(*role_names: str) -> AccessPolicy:
    """
        Create a policy requiring specific roles.

        The resulting policy requires authentication and checks that the
        user has at least one of the specified roles (OR logic).

        :param role_names: Role names required for access.

        :returns: An AccessPolicy with the specified roles and
            require_auth set to True.
    """
    rtnval = AccessPolicy(roles=tuple(role_names), require_auth=True)

    return rtnval


def scopes(*scope_names: str) -> AccessPolicy:
    """
        Create a policy requiring specific scopes.

        The resulting policy requires authentication and checks that the
        user has all of the specified scopes (AND logic).

        :param scope_names: Scope names required for access.

        :returns: An AccessPolicy with the specified scopes and
            require_auth set to True.
    """
    rtnval = AccessPolicy(scopes=tuple(scope_names), require_auth=True)

    return rtnval
