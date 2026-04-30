"""
.. module:: accesspolicy
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Immutable access policy defining roles, scopes, and authentication
        requirements for an endpoint.

.. moduleauthor:: Automation Mojo LLC

This module provides the :class:`AccessPolicy` frozen dataclass that represents a
security constraint for an endpoint. An :class:`AccessPolicy` specifies which roles,
scopes, and authentication requirements must be satisfied for access to be granted.
Policies are immutable after creation and can be merged together to form combined
constraints via :meth:`AccessPolicy.merge_with`.

The :meth:`AccessPolicy.check` method evaluates whether a subject satisfies the policy.
The same policy can be evaluated against any of three subject shapes that webworks
ships:

    - :class:`automojo.webworks.security.securitycontext.SecurityContext` — the
      flat, immutable security context with ``user_id`` / ``roles`` / ``scopes``.
    - :class:`automojo.webworks.authentication.core.AuthenticationContext` — the
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

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Optional, Tuple, TYPE_CHECKING

from automojo.webworks.security.securitycontext import SecurityContext

if TYPE_CHECKING:
    from automojo.webworks.authentication.core import AuthenticationContext


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


@dataclass(frozen=True)
class AccessPolicy:
    """
        Security constraint defining roles, scopes, and authentication
        requirements for an endpoint. Immutable after creation.

        :param roles: Iterable of role names required for access. When non-empty,
            the subject must have at least one of these roles (OR logic). Stored
            as a tuple regardless of input collection type.
        :param scopes: Iterable of scope names required for access. When non-empty,
            the subject must have all of these scopes (AND logic). Stored as a
            tuple regardless of input collection type.
        :param require_auth: Whether authentication is mandatory for this policy.
        :param constraints: Additional custom constraint types as a dictionary.
            Callers should treat this as read-only to preserve the immutability
            intent of the policy.
    """

    roles: Tuple[str, ...] = field(default_factory=tuple)
    scopes: Tuple[str, ...] = field(default_factory=tuple)
    require_auth: bool = True
    constraints: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """
            Normalize iterable inputs to tuples after the frozen dataclass is
            constructed.

            ``object.__setattr__`` is used because frozen dataclasses block
            ordinary assignment. Coercion is one-shot at construction time;
            once the policy exists it remains immutable.
        """
        coerced_roles = _coerce_to_tuple(self.roles)
        if coerced_roles is not self.roles:
            object.__setattr__(self, "roles", coerced_roles)

        coerced_scopes = _coerce_to_tuple(self.scopes)
        if coerced_scopes is not self.scopes:
            object.__setattr__(self, "scopes", coerced_scopes)

        return

    def merge_with(
        self,
        other: "AccessPolicy",
        replace_roles: bool = False,
        replace_scopes: bool = False
    ) -> "AccessPolicy":
        """
            Merge this policy with another, combining constraints.

            The merged policy enforces all constraints via logical AND. By default,
            roles and scopes are combined as a union (deduplicated, preserving the
            original ordering of ``self`` followed by any new entries from
            ``other``). When replace flags are set, the other policy's values
            fully replace this policy's values for that field.

            ``require_auth`` is the logical OR of the two policies' values
            (i.e. if either requires auth, the merge requires auth). Custom
            ``constraints`` dicts are shallow-merged with ``other`` taking
            precedence on key conflicts.

            :param other: Policy to merge with.
            :param replace_roles: If True, ``other.roles`` replaces ``self.roles``
                instead of performing a union.
            :param replace_scopes: If True, ``other.scopes`` replaces
                ``self.scopes`` instead of performing a union.

            :returns: A new :class:`AccessPolicy` with combined constraints.
        """
        if replace_roles is True:
            merged_roles = other.roles
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
            constraints=merged_constraints
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
                   one of the required roles (OR logic).
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
            :class:`automojo.webworks.authentication.core.Principal` carries
            scope-equivalent grants in its ``permissions`` set.

            :param context: AuthenticationContext to check against this
                policy, or ``None`` for an unauthenticated request.

            :returns: ``True`` when the context satisfies all constraints.
        """
        if self.require_auth is True:
            if context is None:
                return False
            if getattr(context, "is_expired", False) is True:
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

        if len(self.roles) > 0:
            principal_roles = set(principal.roles)
            required_roles = set(self.roles)
            if len(principal_roles.intersection(required_roles)) == 0:
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
                role, or when no roles are required.
        """
        if len(self.roles) == 0:
            return True

        if context is None:
            return False

        if getattr(context, "is_expired", False) is True:
            return False

        principal_roles = set(context.principal.roles)
        required_roles = set(self.roles)

        rtnval = len(principal_roles.intersection(required_roles)) > 0
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

        if getattr(context, "is_expired", False) is True:
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
        if self.require_auth is True:
            is_auth = context.is_authenticated
            if is_auth is not True:
                return False

        if len(self.roles) > 0:
            has_required_role = context.has_any_role(*self.roles)
            if has_required_role is not True:
                return False

        if len(self.scopes) > 0:
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
            user_roles = set(getattr(user, "roles", ()) or ())
            required_roles = set(self.roles)
            if len(user_roles.intersection(required_roles)) == 0:
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
        if self.require_auth is True:
            if context is None:
                return "Authentication is required"
            if getattr(context, "is_expired", False) is True:
                return "Authentication has expired"

        if context is None:
            if len(self.roles) > 0:
                return "Missing required role"
            if len(self.scopes) > 0:
                return "Missing required scope"
            return None

        principal = context.principal

        if len(self.roles) > 0:
            principal_roles = set(principal.roles)
            required_roles = set(self.roles)
            if len(principal_roles.intersection(required_roles)) == 0:
                return "Missing required role"

        if len(self.scopes) > 0:
            principal_permissions = set(principal.permissions)
            required_scopes = set(self.scopes)
            if not required_scopes.issubset(principal_permissions):
                return "Missing required scope"

        return None

    def _security_context_denial(self, context: SecurityContext) -> Optional[str]:
        if self.require_auth is True:
            if context.is_authenticated is not True:
                return "Authentication is required"

        if len(self.roles) > 0:
            if context.has_any_role(*self.roles) is not True:
                return "Missing required role"

        if len(self.scopes) > 0:
            if context.has_all_scopes(*self.scopes) is not True:
                return "Missing required scope"

        return None

    def _user_denial(self, user: Any) -> Optional[str]:
        if self.require_auth is True:
            is_auth = getattr(user, "is_authenticated", False)
            if is_auth is not True:
                return "Authentication is required"

        if len(self.roles) > 0:
            user_roles = set(getattr(user, "roles", ()) or ())
            required_roles = set(self.roles)
            if len(user_roles.intersection(required_roles)) == 0:
                return "Missing required role"

        if len(self.scopes) > 0:
            user_scopes = set(getattr(user, "scopes", ()) or ())
            required_scopes = set(self.scopes)
            if not required_scopes.issubset(user_scopes):
                return "Missing required scope"

        return None
