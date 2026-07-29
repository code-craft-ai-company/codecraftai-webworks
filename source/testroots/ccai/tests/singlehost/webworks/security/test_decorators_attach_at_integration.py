"""
.. module:: test_decorators_attach_at_integration
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Integration tests for security decorators flowing through
        Endpoint.attach_at, RestEndpoint.attach_at, and the blueprint
        variants into the EndpointDescriptor's effective AccessPolicy.

.. moduleauthor:: Code Craft AI LLC

The security decorators (``@require_auth``, ``@require_roles``,
``@require_scopes``, ``@public_endpoint``) attach an :class:`AccessPolicy`
to the handler function via the ``_access_policy`` attribute. Prior to
the wiring fix shipped alongside these tests, that attribute was
silently ignored at registration time — :meth:`Endpoint.attach_at` only
read ``access_policy`` from explicit kwargs and the class default. These
tests verify the end-to-end behavior: a handler decorated with one of
the security decorators ends up with the corresponding policy on its
:class:`EndpointDescriptor`.
"""

from ccai.webworks.endpoints.descriptor import ENDPOINT_DESCRIPTORS_ATTR
from ccai.webworks.endpoints.endpoint import Endpoint
from ccai.webworks.endpoints.restendpoint import RestEndpoint
from ccai.webworks.security.accesspolicy import AccessPolicy
from ccai.webworks.security.decorators import (
    public_endpoint,
    require_auth,
    require_roles,
    require_scopes,
)


# =============================================================================
# Helpers
# =============================================================================

def _last_descriptor_for(handler):
    """
        Return the :class:`EndpointDescriptor` that ``attach_at`` recorded
        for the supplied callable.

        This used to scan a registry for a descriptor whose handler matched.
        A descriptor now lives on the handler that declared it, so the
        handler can be asked directly and the answer does not depend on any
        registry having collected it, nor on registration order.
    """
    descriptors = list(getattr(handler, ENDPOINT_DESCRIPTORS_ATTR, ()))
    if not descriptors:
        errmsg = "No EndpointDescriptor found for handler {!r}".format(handler)
        raise AssertionError(errmsg)

    return descriptors[-1]


# =============================================================================
# Endpoint.attach_at honors @require_roles / @require_auth / @require_scopes
# =============================================================================

def test_require_roles_propagates_into_descriptor_via_attach_at():
    """
        ``@require_roles("admin")`` followed by ``@Endpoint.attach_at(...)``
        produces an :class:`EndpointDescriptor` whose effective access
        policy includes ``"admin"``.
    """
    @Endpoint.attach_at(leaf="rr-admin-only")
    @require_roles("admin")
    def handler_admin_only():
        return

    desc = _last_descriptor_for(handler_admin_only)
    policy = desc.constraints.access_policy

    if policy is None:
        errmsg = "Expected an AccessPolicy on the descriptor, got None"
        raise AssertionError(errmsg)

    if "admin" not in policy.roles:
        errmsg = "Expected 'admin' in policy.roles, got {!r}".format(policy.roles)
        raise AssertionError(errmsg)

    if policy.require_auth is not True:
        errmsg = "Expected require_auth=True from @require_roles, got {!r}".format(
            policy.require_auth
        )
        raise AssertionError(errmsg)

    return


def test_require_auth_propagates_into_descriptor_via_attach_at():
    """
        ``@require_auth`` (no roles) attaches a policy that requires
        authentication on the resulting descriptor.
    """
    @Endpoint.attach_at(leaf="ra-auth-only")
    @require_auth
    def handler_auth_only():
        return

    desc = _last_descriptor_for(handler_auth_only)
    policy = desc.constraints.access_policy

    if policy is None:
        errmsg = "Expected an AccessPolicy on the descriptor, got None"
        raise AssertionError(errmsg)

    if policy.require_auth is not True:
        errmsg = "Expected require_auth=True, got {!r}".format(policy.require_auth)
        raise AssertionError(errmsg)

    return


def test_require_scopes_propagates_into_descriptor_via_attach_at():
    """
        ``@require_scopes("read:posts")`` flows through to the descriptor
        as a scope on the effective access policy.
    """
    @Endpoint.attach_at(leaf="rs-read-posts")
    @require_scopes("read:posts")
    def handler_read_posts():
        return

    desc = _last_descriptor_for(handler_read_posts)
    policy = desc.constraints.access_policy

    if policy is None:
        errmsg = "Expected an AccessPolicy on the descriptor, got None"
        raise AssertionError(errmsg)

    if "read:posts" not in policy.scopes:
        errmsg = "Expected 'read:posts' in policy.scopes, got {!r}".format(policy.scopes)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Merging behavior — decorator policy combines with explicit kwargs and
# class defaults rather than replacing them.
# =============================================================================

def test_decorator_policy_merges_with_explicit_access_policy_kwarg():
    """
        When both a security decorator and an explicit ``access_policy=``
        kwarg supply roles, the merged result is the union — neither side
        is silently dropped.
    """
    @Endpoint.attach_at(
        leaf="merge-explicit",
        access_policy=AccessPolicy(roles=("editor",))
    )
    @require_roles("admin")
    def handler_admin_or_editor():
        return

    desc = _last_descriptor_for(handler_admin_or_editor)
    policy = desc.constraints.access_policy

    if "admin" not in policy.roles:
        errmsg = "Expected 'admin' in merged roles, got {!r}".format(policy.roles)
        raise AssertionError(errmsg)

    if "editor" not in policy.roles:
        errmsg = "Expected 'editor' in merged roles, got {!r}".format(policy.roles)
        raise AssertionError(errmsg)

    return


def test_decorator_policy_merges_with_class_default_access_policy():
    """
        A subclass of :class:`Endpoint` may declare a class-level
        ``access_policy`` default. Decorator-supplied roles must merge
        with — not replace — that default.
    """
    class HeroEndpoint(Endpoint):
        access_policy = AccessPolicy(roles=("hero",))

    @HeroEndpoint.attach_at(leaf="merge-class")
    @require_roles("guest")
    def handler_hero_or_guest():
        return

    desc = _last_descriptor_for(handler_hero_or_guest)
    policy = desc.constraints.access_policy

    if "hero" not in policy.roles:
        errmsg = "Expected class-default role 'hero' in merged roles, got {!r}".format(
            policy.roles
        )
        raise AssertionError(errmsg)

    if "guest" not in policy.roles:
        errmsg = "Expected decorator role 'guest' in merged roles, got {!r}".format(
            policy.roles
        )
        raise AssertionError(errmsg)

    return


def test_stacked_security_decorators_all_propagate_via_attach_at():
    """
        Stacking ``@require_roles`` and ``@require_scopes`` produces a
        single merged policy (via the decorator's own merge logic), and
        attach_at must forward that merged policy into the descriptor.
    """
    @Endpoint.attach_at(leaf="stack-rs-rr")
    @require_roles("admin")
    @require_scopes("write:posts")
    def handler_admin_write():
        return

    desc = _last_descriptor_for(handler_admin_write)
    policy = desc.constraints.access_policy

    if "admin" not in policy.roles:
        errmsg = "Expected 'admin' in policy.roles, got {!r}".format(policy.roles)
        raise AssertionError(errmsg)

    if "write:posts" not in policy.scopes:
        errmsg = "Expected 'write:posts' in policy.scopes, got {!r}".format(policy.scopes)
        raise AssertionError(errmsg)

    return


# =============================================================================
# RestEndpoint mirrors Endpoint behavior
# =============================================================================

def test_require_roles_propagates_into_descriptor_via_rest_attach_at():
    """
        :meth:`RestEndpoint.attach_at` honors handler-attached policy the
        same way :meth:`Endpoint.attach_at` does.
    """
    @RestEndpoint.attach_at(leaf="rest-admin-only")
    @require_roles("admin")
    def handler_rest_admin_only():
        return

    desc = _last_descriptor_for(handler_rest_admin_only)
    policy = desc.constraints.access_policy

    if policy is None:
        errmsg = "Expected an AccessPolicy on the REST descriptor, got None"
        raise AssertionError(errmsg)

    if "admin" not in policy.roles:
        errmsg = "Expected 'admin' in policy.roles, got {!r}".format(policy.roles)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Public endpoint requires-auth False propagates
# =============================================================================

def test_public_endpoint_propagates_require_auth_false_via_attach_at():
    """
        ``@public_endpoint`` attaches a policy with ``require_auth=False``.
        When no other source of policy is present, the descriptor's
        effective policy reflects that.
    """
    @Endpoint.attach_at(leaf="public-only")
    @public_endpoint
    def handler_public():
        return

    desc = _last_descriptor_for(handler_public)
    policy = desc.constraints.access_policy

    if policy is None:
        errmsg = "Expected an AccessPolicy on the descriptor, got None"
        raise AssertionError(errmsg)

    if policy.require_auth is not False:
        errmsg = "Expected require_auth=False from @public_endpoint, got {!r}".format(
            policy.require_auth
        )
        raise AssertionError(errmsg)

    return
