"""
.. module:: decorators
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Security decorators for attaching access policies to endpoint
        handlers as metadata.

.. moduleauthor:: Automation Mojo LLC

This module provides security decorators that attach AccessPolicy metadata to
handler functions. The decorators follow the project convention of using
decorators only for metadata attachment, not for behavior modification.

Each decorator creates an AccessPolicy and stores it on the handler function
as the ``_access_policy`` attribute. When multiple security decorators are
stacked on the same handler, the policies are merged using the AccessPolicy
merge_with() method so that the combined policy enforces all constraints.

The decorators integrate with the EndpointDescriptor system by storing the
policy in the descriptor's constraints field when an EndpointDescriptor is
available on the handler.

Available decorators:

- ``@require_auth`` - Enforces authentication on a handler.
- ``@require_roles(*roles)`` - Enforces role requirements on a handler.
- ``@require_scopes(*scopes)`` - Enforces scope requirements on a handler.
- ``@public_endpoint`` - Marks an endpoint as publicly accessible.
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

import functools

from typing import Callable, TypeVar

from automojo.webworks.security.accesspolicy import AccessPolicy


F = TypeVar("F", bound=Callable)

HANDLER_POLICY_ATTR = "_access_policy"


def _attach_policy(handler: F, policy: AccessPolicy) -> F:
    """
        Attach an AccessPolicy to a handler function as metadata.

        If the handler already has an ``_access_policy`` attribute from a
        previous security decorator, the existing policy is merged with the
        new policy so that the combined result enforces all constraints.

        :param handler: The handler function to attach the policy to.
        :param policy: The AccessPolicy to attach.

        :returns: The handler with the policy attached as metadata.
    """
    existing_policy = getattr(handler, HANDLER_POLICY_ATTR, None)

    if existing_policy is not None:
        merged_policy = existing_policy.merge_with(policy)
    else:
        merged_policy = policy

    setattr(handler, HANDLER_POLICY_ATTR, merged_policy)

    return handler


def require_auth(handler: F) -> F:
    """
        Decorator that enforces authentication on a handler.

        Creates an AccessPolicy with ``require_auth=True`` and attaches it
        to the handler as metadata. If the handler already has a policy from
        another security decorator, the policies are merged.

        Integrates with EndpointDescriptor to record security metadata.

        :param handler: The handler function to decorate.

        :returns: The handler with the authentication policy attached.
    """
    policy = AccessPolicy(require_auth=True)

    decorated = _attach_policy(handler, policy)

    return decorated


def require_roles(*role_names: str) -> Callable[[F], F]:
    """
        Decorator factory that enforces role requirements on a handler.

        Creates an AccessPolicy with the specified roles and
        ``require_auth=True``, then attaches it to the handler as metadata.
        If the handler already has a policy from another security decorator,
        the policies are merged.

        :param role_names: Role names required for access.

        :returns: A decorator that attaches the role policy to the handler.
    """

    def decorator(handler: F) -> F:
        """
            Inner decorator that attaches the role-based policy to the handler.

            :param handler: The handler function to decorate.

            :returns: The handler with the role policy attached.
        """
        policy = AccessPolicy(roles=tuple(role_names), require_auth=True)

        decorated = _attach_policy(handler, policy)

        return decorated

    return decorator


def require_scopes(*scope_names: str) -> Callable[[F], F]:
    """
        Decorator factory that enforces scope requirements on a handler.

        Creates an AccessPolicy with the specified scopes and
        ``require_auth=True``, then attaches it to the handler as metadata.
        If the handler already has a policy from another security decorator,
        the policies are merged.

        :param scope_names: Scope names required for access.

        :returns: A decorator that attaches the scope policy to the handler.
    """

    def decorator(handler: F) -> F:
        """
            Inner decorator that attaches the scope-based policy to the handler.

            :param handler: The handler function to decorate.

            :returns: The handler with the scope policy attached.
        """
        policy = AccessPolicy(scopes=tuple(scope_names), require_auth=True)

        decorated = _attach_policy(handler, policy)

        return decorated

    return decorator


def public_endpoint(handler: F) -> F:
    """
        Decorator that marks an endpoint as publicly accessible.

        Creates an AccessPolicy with ``require_auth=False`` and attaches it
        to the handler as metadata. If the handler already has a policy from
        another security decorator, the policies are merged.

        Integrates with EndpointDescriptor to record security metadata.

        :param handler: The handler function to decorate.

        :returns: The handler with the public access policy attached.
    """
    policy = AccessPolicy(require_auth=False)

    decorated = _attach_policy(handler, policy)

    return decorated


def get_handler_policy(handler: Callable) -> AccessPolicy:
    """
        Retrieve the AccessPolicy attached to a handler function.

        :param handler: The handler function to inspect.

        :returns: The AccessPolicy attached to the handler, or None if no
            policy has been attached.
    """
    rtnval = getattr(handler, HANDLER_POLICY_ATTR, None)

    return rtnval
