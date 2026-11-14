"""
.. module:: accesspolicy
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Immutable access policy defining roles, scopes, and authentication
        requirements for an endpoint.

.. moduleauthor:: Code Craft AI LLC

This module provides the :class:`AccessPolicy` frozen dataclass that represents a
security constraint for an endpoint. An :class:`AccessPolicy` specifies which roles,
scopes, and authentication requirements must be satisfied for access to be granted.
Policies are immutable after creation and can be merged together to form combined
constraints via :meth:`AccessPolicy.merge_with`.

The :meth:`AccessPolicy.check` method evaluates whether a subject satisfies the policy.
The same policy can be evaluated against any of three subject shapes that webworks
ships:

    - :class:`ccai.webworks.security.securitycontext.SecurityContext` — the
      flat, immutable security context with ``user_id`` / ``roles`` / ``scopes``.
    - :class:`ccai.webworks.authentication.core.AuthenticationContext` — the
      authentication-stack context wrapping a :class:`Principal`.
    - Any object satisfying the duck-typed *User* shape (``is_authenticated``,
      ``roles``, ``scopes`` attributes).

Discrimination is performed at call time by attribute presence, so adding or
removing a subject shape requires no consumer changes. The convenience methods
:meth:`AccessPolicy.check_authentication_context`, :meth:`AccessPolicy.check_roles`,
and :meth:`AccessPolicy.check_permissions` are explicit, named entry points that
existing call sites continue to import.

Construction
------------

``roles`` and ``scopes`` are stored internally as tuples. Constructors accept any
iterable of strings (lists, tuples, generators) and the values are coerced to
tuples in ``__post_init__``. This keeps the dataclass frozen-immutable while
still being friendly to callers that prefer list literals.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

from dataclasses import dataclass, field
from typing import Any, ClassVar, Dict, Iterable, Optional, Tuple, TYPE_CHECKING

from ccai.webworks.security.securitycontext import SecurityContext

if TYPE_CHECKING:
    from ccai.webworks.authentication.core import AuthenticationContext


def _coerce_to_tuple(value: Any) -> Tuple[str, ...]:
    """
        Normalize an iterable of role / scope names to an immutable tuple of strings.

        Accepts ``None`` (treated as empty), tuples, lists, sets, and any other
        iterable. The resulting tuple preserves caller-supplied ordering for
        list and tuple inputs; for unordered inputs (e.g. ``set``) the order
        matches the iteration order of the source.

        :param value: Source iterable, or ``None`` for empty.

        :returns: A tuple of strings representing the supplied values.
    """
    if value is None:
        return tuple()

    if isinstance(value, tuple):
        return value

    if isinstance(value, str):
        # Treat a bare string as a single role/scope name rather than
        # iterating its characters, which is almost certainly a caller bug.
        return (value,)

    if isinstance(value, Iterable):
        return tuple(value)

    return tuple()


def _coerce_groups(value: Any) -> Tuple[Tuple[str, ...], ...]:
    """
        Normalize an iterable of role groups to a tuple of tuples of strings.

        :param value: Source iterable of iterables, or ``None`` for empty.

        :returns: A tuple holding one tuple of role names per group.
    """
    if value is None:
        return tuple()

    if isinstance(value, str):
        # A bare string is one group holding one role.
        return ((value,),)

    groups = []
    for group in value:
        groups.append(_coerce_to_tuple(group))

    rtnval = tuple(groups)
    return rtnval


@dataclass(frozen=True)
class AccessPolicy:
    """
        Security constraint defining roles, scopes, and authentication
        requirements for an endpoint. Immutable after creation.

        :param roles: Iterable of role names required for access. When non-empty,
            the subject must have at least one of these roles (OR logic). Stored
            as a tuple regardless of input collection type. On a policy
            produced by :meth:`merge_with` this is the union of the roles
            named by the merged policies, kept for display and reporting;
            what is enforced is ``role_groups``.
        :param scopes: Iterable of scope names required for access. When non-empty,
            the subject must have all of these scopes (AND logic). Stored as a
            tuple regardless of input collection type.
        :param require_auth: Whether authentication is mandatory for this policy.
        :param constraints: Additional custom constraint types as a dictionary.
            Callers should treat this as read-only to preserve the immutability
            intent of the policy.
        :param role_groups: The role requirement in the form it is enforced:
            a tuple of groups, each a tuple of role names. The subject must
            hold at least one role from **every** group. A policy
            constructed with ``roles`` has the single group ``(roles,)``;
            merging two policies keeps the groups of both, so a policy
            inherited from a blueprint and the policy of a handler must
            each be satisfied. Normally left unset and derived.
    """

    # Class-level convention. When set to a non-empty role name, any
    # principal whose roles set contains that name satisfies
    # :meth:`check_roles` regardless of the policy's ``roles`` tuple.
    # The default ``None`` preserves the strict-intersection
    # behaviour for sites that don't use a "do-everything" role.
    # Sites opt in by assigning the class attribute at boot, e.g.::
    #
    #     from ccai.webworks.security.accesspolicy import AccessPolicy
    #     AccessPolicy.SUPERUSER_ROLE_NAME = "superuser"
    #
    # The check is purely additive — no existing behaviour changes
    # for sites that leave it unset.
    SUPERUSER_ROLE_NAME: ClassVar[Optional[str]] = None

    roles: Tuple[str, ...] = field(default_factory=tuple)
    scopes: Tuple[str, ...] = field(default_factory=tuple)
    require_auth: bool = True
    constraints: Dict[str, Any] = field(default_factory=dict)
    role_groups: Tuple[Tuple[str, ...], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        """
            Normalize iterable inputs to tuples after the frozen dataclass is
            constructed, and bring ``roles`` and ``role_groups`` into
            agreement.

            ``object.__setattr__`` is used because frozen dataclasses block
            ordinary assignment. Coercion is one-shot at construction time;
            once the policy exists it remains immutable.

            ``role_groups`` is derived when it is not given: one group
            holding ``roles``. When only ``role_groups`` is given, ``roles``
            becomes the union of the groups. When both are given and name
            different roles -- ``dataclasses.replace(policy, roles=...)`` --
            the explicit ``roles`` win and form the single group.
        """
        coerced_roles = _coerce_to_tuple(self.roles)
        if coerced_roles is not self.roles:
            object.__setattr__(self, "roles", coerced_roles)

        coerced_scopes = _coerce_to_tuple(self.scopes)
        if coerced_scopes is not self.scopes:
            object.__setattr__(self, "scopes", coerced_scopes)

        coerced_groups = []
        for group in _coerce_groups(self.role_groups):
            if len(group) > 0:
                coerced_groups.append(group)

        named_by_groups = []
        for group in coerced_groups:
            for role in group:
                if role not in named_by_groups:
                    named_by_groups.append(role)

        if len(coerced_groups) == 0:
            if len(coerced_roles) > 0:
                coerced_groups = [coerced_roles]
        elif len(coerced_roles) == 0:
            object.__setattr__(self, "roles", tuple(named_by_groups))
        elif set(coerced_roles) != set(named_by_groups):
            coerced_groups = [coerced_roles]

        object.__setattr__(self, "role_groups", tuple(coerced_groups))

        return

    def has_required_roles(self, subject_roles: Iterable[str]) -> bool:
        """
            Decide whether a set of roles satisfies the role requirement of
            this policy.

            The subject needs at least one role from every group in
            ``role_groups``. When the application has opted in to a
            "do everything" role via :data:`SUPERUSER_ROLE_NAME`, a subject
            holding that role satisfies any role requirement.

            :param subject_roles: The roles the subject holds.

            :returns: ``True`` when the roles satisfy every group, or when
                the policy requires no roles.
        """
        rtnval = True

        if len(self.role_groups) > 0:
            held_roles = set(subject_roles or ())

            superuser_role = type(self).SUPERUSER_ROLE_NAME
            superuser_granted = (
                superuser_role is not None
                and superuser_role in held_roles
            )

            if not superuser_granted:
                for group in self.role_groups:
                    if len(held_roles.intersection(group)) == 0:
                        rtnval = False
                        break

        return rtnval

    def merge_with(
        self,
        other: "AccessPolicy",
        replace_roles: bool = False,
        replace_scopes: bool = False
    ) -> "AccessPolicy":
        """
            Merge this policy with another, combining constraints.

            The merged policy enforces all constraints via logical AND: a
            subject satisfies it only if it satisfies ``self`` and
            ``other``. Scopes are all-of, so the merged scopes are the
            union. Roles are any-of *within* a policy, so they can not be
            pooled -- a subject holding only a role of ``other`` would then
            pass a requirement of ``self`` it does not meet. The role
            groups of both policies are kept instead, and the subject needs
            a role from each. ``roles`` of the result is the deduplicated
            union (the original ordering of ``self`` followed by any new
            entries from ``other``) and serves reporting; ``role_groups``
            is what is enforced.

            When replace flags are set, the other policy's values
            fully replace this policy's values for that field.

            ``require_auth`` is the logical OR of the two policies' values
            (i.e. if either requires auth, the merge requires auth). Custom
            ``constraints`` dicts are shallow-merged with ``other`` taking
            precedence on key conflicts.

            :param other: Policy to merge with.
            :param replace_roles: If True, ``other.roles`` replaces ``self.roles``
                instead of both being required.
            :param replace_scopes: If True, ``other.scopes`` replaces
                ``self.scopes`` instead of performing a union.

            :returns: A new :class:`AccessPolicy` with combined constraints.
        """
        if replace_roles is True:
            merged_roles = other.roles
            merged_groups = other.role_groups
        else:
            seen = set()
            combined = []
            for role in self.roles:
                if role not in seen:
                    seen.add(role)
                    combined.append(role)
            for role in other.roles:
                if role not in seen:
                    seen.add(role)
                    combined.append(role)
            merged_roles = tuple(combined)

            # Keep the groups of both policies; a group both name is
            # required once.
            seen_groups = set()
            combined_groups = []
            for group in self.role_groups + other.role_groups:
                group_key = frozenset(group)
                if group_key not in seen_groups:
                    seen_groups.add(group_key)
                    combined_groups.append(group)
            merged_groups = tuple(combined_groups)

        if replace_scopes is True:
            merged_scopes = other.scopes
        else:
            seen = set()
            combined = []
            for scope in self.scopes:
                if scope not in seen:
                    seen.add(scope)
                    combined.append(scope)
            for scope in other.scopes:
                if scope not in seen:
                    seen.add(scope)
                    combined.append(scope)
            merged_scopes = tuple(combined)

        merged_require_auth = self.require_auth or other.require_auth

        merged_constraints = dict(self.constraints)
        merged_constraints.update(other.constraints)

        rtnval = AccessPolicy(
            roles=merged_roles,
            scopes=merged_scopes,
            require_auth=merged_require_auth,
            constraints=merged_constraints,
            role_groups=merged_groups
        )

        return rtnval

    def check(self, subject: Any) -> bool:
        """
            Polymorphic check: does ``subject`` satisfy this policy?

            Discriminates the subject shape at call time:

                - If ``subject`` exposes a ``principal`` attribute it is
                  treated as an :class:`AuthenticationContext` and routed to
                  :meth:`check_authentication_context`.
                - If ``subject`` exposes a ``user_id`` attribute it is treated
                  as a :class:`SecurityContext`.
                - Otherwise the subject is treated as a duck-typed *User*
                  with ``is_authenticated``, ``roles`` and ``scopes``
                  attributes.

            Each shape evaluates the same three rules in order:

                1. If ``require_auth`` is True, the subject must be authenticated.
                2. If ``roles`` is non-empty, the subject must have at least
                   one of the required roles (OR logic) -- one from every
                   group of ``role_groups`` when the policy was merged.
                3. If ``scopes`` is non-empty, the subject must have all of the
                   required scopes (AND logic). For
                   :class:`AuthenticationContext` the scope check is performed
                   against the principal's *permissions* set, since
                   :class:`Principal` exposes scopes-equivalent values under
                   ``permissions``.

            :param subject: SecurityContext, AuthenticationContext, or any
                object satisfying the duck-typed User shape.

            :returns: ``True`` if the subject satisfies all constraints,
                ``False`` otherwise. Returns ``False`` when the subject does
                not match any of the supported shapes.
        """
        if subject is None:
            # Unauthenticated. Pass only when require_auth is False and no
            # role / scope constraints are set.
            if self.require_auth is True:
                return False
            if len(self.roles) > 0:
                return False
            if len(self.scopes) > 0:
                return False
            return True

        if hasattr(subject, "principal"):
            rtnval = self.check_authentication_context(subject)
            return rtnval

        if hasattr(subject, "user_id"):
            rtnval = self._check_security_context(subject)
            return rtnval

        rtnval = self._check_user(subject)
        return rtnval

    def check_authentication_context(
        self,
        context: Optional["AuthenticationContext"]
    ) -> bool:
        """
            Check whether an :class:`AuthenticationContext` satisfies this
            policy.

            Roles are compared against ``context.principal.roles``. Scopes
            are compared against ``context.principal.permissions``, since
            :class:`ccai.webworks.authentication.core.Principal` carries
            scope-equivalent grants in its ``permissions`` set.

            :param context: AuthenticationContext to check against this
                policy, or ``None`` for an unauthenticated request.

            :returns: ``True`` when the context satisfies all constraints.
        """
        # An expired context authenticates nobody: it is treated as an
        # unauthenticated request whether or not the policy demands
        # authentication, so its roles and permissions grant nothing.
        if context is not None and getattr(context, "is_expired", False) is not False:
            context = None

        if self.require_auth is True:
            if context is None:
                return False

        if context is None:
            # require_auth is False — anonymous access is allowed iff no
            # role or scope constraints are set.
            if len(self.roles) > 0:
                return False
            if len(self.scopes) > 0:
                return False
            return True

        principal = context.principal

        # Role groups, with the optional class-level "do everything"
        # role applied by :meth:`has_required_roles` -- the same rule
        # :meth:`check_roles` applies, so the two check paths agree.
        if self.has_required_roles(principal.roles) is not True:
            return False

        if len(self.scopes) > 0:
            principal_permissions = set(principal.permissions)
            required_scopes = set(self.scopes)
            if not required_scopes.issubset(principal_permissions):
                return False

        rtnval = True
        return rtnval

    def check_roles(self, context: Optional["AuthenticationContext"]) -> bool:
        """
            Convenience helper that checks only the role constraint of this
            policy against an :class:`AuthenticationContext`.

            Returns ``True`` immediately when ``self.roles`` is empty, since
            a policy with no role constraint trivially satisfies its role
            check. An expired or ``None`` context fails the check whenever
            roles are required.

            :param context: AuthenticationContext to check, or ``None``.

            :returns: ``True`` when the context has at least one required
                role from every role group, or when no roles are required.
        """
        if len(self.roles) == 0:
            return True

        if context is None:
            return False

        if getattr(context, "is_expired", False) is not False:
            return False

        # Role groups plus the optional class-level "do everything"
        # role; see :meth:`has_required_roles`.
        rtnval = self.has_required_roles(context.principal.roles)
        return rtnval

    def check_permissions(self, context: Optional["AuthenticationContext"]) -> bool:
        """
            Convenience helper that checks only the scope constraint of this
            policy against an :class:`AuthenticationContext`.

            Scopes are compared against ``context.principal.permissions``.
            Returns ``True`` immediately when ``self.scopes`` is empty.

            :param context: AuthenticationContext to check, or ``None``.

            :returns: ``True`` when the context has all required permissions,
                or when no scopes are required.
        """
        if len(self.scopes) == 0:
            return True

        if context is None:
            return False

        if getattr(context, "is_expired", False) is not False:
            return False

        principal_permissions = set(context.principal.permissions)
        required_scopes = set(self.scopes)

        rtnval = required_scopes.issubset(principal_permissions)
        return rtnval

    def _check_security_context(self, context: SecurityContext) -> bool:
        """
            Internal helper: evaluate this policy against a :class:`SecurityContext`.

            Same three rules as :meth:`check_authentication_context` but
            using ``SecurityContext.is_authenticated`` /
            ``SecurityContext.has_any_role`` / ``SecurityContext.has_all_scopes``.

            :param context: SecurityContext to evaluate.

            :returns: ``True`` when the context satisfies all constraints.
        """
        # ``is_authenticated`` is False for a guest and for an expired
        # context. Roles and scopes of a context that is not authenticated
        # grant nothing, whether or not the policy demands authentication.
        is_auth = context.is_authenticated

        if self.require_auth is True:
            if is_auth is not True:
                return False

        if len(self.roles) > 0:
            if is_auth is not True:
                return False
            if self.has_required_roles(context.roles) is not True:
                return False

        if len(self.scopes) > 0:
            if is_auth is not True:
                return False
            has_all_required_scopes = context.has_all_scopes(*self.scopes)
            if has_all_required_scopes is not True:
                return False

        rtnval = True
        return rtnval

    def _check_user(self, user: Any) -> bool:
        """
            Internal helper: evaluate this policy against a duck-typed *User*.

            The user object must expose ``is_authenticated`` (bool),
            ``roles`` (iterable of role names), and ``scopes`` (iterable of
            scope names).

            :param user: User-shaped object.

            :returns: ``True`` when the user satisfies all constraints.
        """
        if self.require_auth is True:
            is_auth = getattr(user, "is_authenticated", False)
            if is_auth is not True:
                return False

        if len(self.roles) > 0:
            user_roles = getattr(user, "roles", ()) or ()
            if self.has_required_roles(user_roles) is not True:
                return False

        if len(self.scopes) > 0:
            user_scopes = set(getattr(user, "scopes", ()) or ())
            required_scopes = set(self.scopes)
            if not required_scopes.issubset(user_scopes):
                return False

        rtnval = True
        return rtnval

    def get_denial_reason(self, subject: Any) -> Optional[str]:
        """
            Return a human-readable reason why ``subject`` fails this policy.

            Evaluates the same conditions as :meth:`check` and returns a
            short string describing the first constraint that is not
            satisfied. Returns ``None`` when ``subject`` passes all checks.

            :param subject: SecurityContext, AuthenticationContext, or
                duck-typed User. ``None`` is supported and indicates an
                unauthenticated request.

            :returns: Human-readable denial reason, or ``None`` if the check
                passes.
        """
        if subject is None or hasattr(subject, "principal"):
            return self._authentication_context_denial(subject)

        if hasattr(subject, "user_id"):
            return self._security_context_denial(subject)

        return self._user_denial(subject)

    def _authentication_context_denial(
        self,
        context: Optional["AuthenticationContext"]
    ) -> Optional[str]:
        expired = context is not None and getattr(context, "is_expired", False) is not False

        if self.require_auth is True:
            if context is None:
                return "Authentication is required"
            if expired:
                return "Authentication has expired"

        if expired:
            context = None

        if context is None:
            if len(self.roles) > 0:
                return "Missing required role"
            if len(self.scopes) > 0:
                return "Missing required scope"
            return None

        principal = context.principal

        if self.has_required_roles(principal.roles) is not True:
            return "Missing required role"

        if len(self.scopes) > 0:
            principal_permissions = set(principal.permissions)
            required_scopes = set(self.scopes)
            if not required_scopes.issubset(principal_permissions):
                return "Missing required scope"

        return None

    def _security_context_denial(self, context: SecurityContext) -> Optional[str]:
        is_auth = context.is_authenticated

        if self.require_auth is True:
            if is_auth is not True:
                return "Authentication is required"

        if len(self.roles) > 0:
            if is_auth is not True or self.has_required_roles(context.roles) is not True:
                return "Missing required role"

        if len(self.scopes) > 0:
            if is_auth is not True or context.has_all_scopes(*self.scopes) is not True:
                return "Missing required scope"

        return None

    def _user_denial(self, user: Any) -> Optional[str]:
        if self.require_auth is True:
            is_auth = getattr(user, "is_authenticated", False)
            if is_auth is not True:
                return "Authentication is required"

        if len(self.roles) > 0:
            user_roles = getattr(user, "roles", ()) or ()
            if self.has_required_roles(user_roles) is not True:
                return "Missing required role"

        if len(self.scopes) > 0:
            user_scopes = set(getattr(user, "scopes", ()) or ())
            required_scopes = set(self.scopes)
            if not required_scopes.issubset(user_scopes):
                return "Missing required scope"

        return None
