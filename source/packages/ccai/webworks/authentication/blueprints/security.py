"""
.. module:: security
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Base security blueprint class for authentication endpoints.

.. moduleauthor:: Code Craft AI LLC

This module provides the :class:`SecurityBlueprint` base class which extends
:class:`RestBlueprint` with authentication-specific functionality. All
authentication blueprints (Basic, Bearer, OAuth2, etc.) inherit from this
class to share common security patterns including error formatting,
pre/post authentication hooks, endpoint enable/disable control, and
integration with the :class:`AuthenticationSystem`.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from typing import Any, Callable, Dict, List, Optional, Set, Type, TypeVar, TYPE_CHECKING

from ccai.webworks.endpoints.restblueprint import RestBlueprint
from ccai.webworks.endpoints.accesspolicy import AccessPolicy
from ccai.webworks.endpoints.constraints import EndpointConstraints
from ccai.webworks.endpoints.ratelimit import RateLimit
from ccai.webworks.endpoints.descriptor import EndpointDescriptor
from ccai.webworks.endpoints.doc import Doc
from ccai.webworks.endpoints.registry import EndpointRegistry
from ccai.webworks.authentication.system import AuthenticationSystem
from ccai.webworks.authentication.core import AuthenticationContext
from ccai.webworks.authentication.errors import (
    sanitize_credentials,
    sanitize_dict
)

from ccai.webworks.authentication.blueprints.responses import (
    AuthResponse,
    AuthError
)


# Default set of keys whose values are considered sensitive and must be
# redacted from error response bodies.
_SENSITIVE_BODY_KEYS: Set[str] = {
    "password", "passwd", "pwd", "secret", "token", "access_token",
    "refresh_token", "id_token", "api_key", "apikey", "api-key",
    "client_secret", "credentials", "credential", "session_id",
    "sessionid", "nonce", "authorization", "auth",
}

if TYPE_CHECKING:
    from ccai.webworks.endpoints.router import Router as RouterProtocol
    from ccai.webworks.authentication.middleware import AuthenticationMiddleware


# Type variable for preserving function signatures in decorators
F = TypeVar("F", bound=Callable[..., Any])

# Attribute name used to store endpoint metadata on handler functions
_ENDPOINT_META_ATTR = "_security_endpoint_meta"


class SecurityBlueprint(RestBlueprint):
    """
        Base class for authentication blueprints.

        Provides common functionality for authentication endpoints including
        error handling, hooks, and integration with the authentication system.
        All authentication blueprint subclasses (BasicAuthBlueprint,
        BearerAuthBlueprint, etc.) extend this class to inherit shared
        security behavior.

        The :meth:`configure` class method associates the blueprint with an
        :class:`AuthenticationSystem` instance and optionally customizes the
        base path and set of enabled endpoints.

        Subclasses may override :meth:`pre_authenticate` and
        :meth:`post_authenticate` to inject custom logic before and after
        credential validation. The :meth:`format_error` and
        :meth:`format_success` methods produce standardized response
        dictionaries that follow RFC 6749 conventions.

        Endpoint decorators (:meth:`create`, :meth:`read`, etc.) store
        metadata on the handler function rather than registering with the
        global :class:`EndpointRegistry`. The :meth:`register` method
        builds :class:`EndpointDescriptor` instances at call time,
        resolving paths against the subclass ``base_path``.

        Class Attributes:
            auth_system: The AuthenticationSystem instance used for
                         credential validation. Set via :meth:`configure`.
            enabled_endpoints: Set of endpoint names that are active.
                               Defaults to ``{"all"}`` which enables every
                               endpoint. Provide a specific set to selectively
                               enable endpoints.
            error_format: Format for error responses. Currently supports
                          ``"json"`` (default).
            cors_origins: Optional list of allowed CORS origins for
                          cross-origin authentication requests. When set,
                          :meth:`get_cors_headers` returns appropriate
                          CORS headers for allowed origins.
    """

    auth_system: Optional[AuthenticationSystem] = None
    enabled_endpoints: set = None
    error_format: str = "json"
    cors_origins: Optional[List[str]] = None

    # --- Class constants ---
    # Override these on a subclass to rebrand error codes / response shape
    # without rewriting the handler bodies. Every literal a handler used to
    # emit lives here as an UPPERCASE attribute referenced via ``cls.NAME``.

    # Response content types
    JSON_CONTENT_TYPE: str = "application/json"

    # Generic error codes / messages used by base-class handlers
    SERVER_ERROR_CODE: str = "server_error"
    SERVER_ERROR_MESSAGE: str = "An internal error occurred"

    # CORS literals
    CORS_DEFAULT_METHODS: str = "GET, POST, PUT, DELETE, OPTIONS"
    CORS_DEFAULT_HEADERS: str = "Authorization, Content-Type"
    CORS_ALLOW_CREDENTIALS: str = "true"
    CORS_ALLOW_ORIGIN_HEADER: str = "Access-Control-Allow-Origin"
    CORS_ALLOW_METHODS_HEADER: str = "Access-Control-Allow-Methods"
    CORS_ALLOW_HEADERS_HEADER: str = "Access-Control-Allow-Headers"
    CORS_ALLOW_CREDENTIALS_HEADER: str = "Access-Control-Allow-Credentials"
    CORS_WILDCARD_ORIGIN: str = "*"

    # Endpoint enablement / metadata
    ENABLE_ALL_TOKEN: str = "all"
    DEFAULT_ENDPOINT_TYPE: str = "auth"

    @classmethod
    def configure(
        cls,
        auth_system: AuthenticationSystem,
        base_path: Optional[str] = None,
        enabled_endpoints: Optional[set] = None,
        access_policy: Optional[AccessPolicy] = None,
        rate_limit: Optional[RateLimit] = None,
        cors_origins: Optional[List[str]] = None
    ) -> None:
        """
            Configure the blueprint with an authentication system and options.

            Associates the given :class:`AuthenticationSystem` with this
            blueprint class so that endpoint handlers can delegate credential
            validation. Optionally overrides the base URL path, the set
            of enabled endpoints, and security constraints.

            :param auth_system: The authentication system instance to use
                                for credential validation.
            :param base_path: Optional base path override for all endpoints
                              registered by this blueprint.
            :param enabled_endpoints: Optional set of endpoint names to
                                      enable. When provided, only the named
                                      endpoints will respond to requests.
            :param access_policy: Optional :class:`AccessPolicy` to apply
                                  to all endpoints in this blueprint.
            :param rate_limit: Optional :class:`RateLimit` to apply to all
                               endpoints in this blueprint.
            :param cors_origins: Optional list of allowed CORS origins for
                                 cross-origin authentication requests.
        """
        cls.auth_system = auth_system

        if base_path is not None:
            cls.base_path = base_path

        if enabled_endpoints is not None:
            cls.enabled_endpoints = enabled_endpoints

        if access_policy is not None:
            cls.access_policy = access_policy

        if rate_limit is not None:
            cls.rate_limit = rate_limit

        if cors_origins is not None:
            cls.cors_origins = cors_origins

        return

    @classmethod
    def is_endpoint_enabled(cls, endpoint_name: str) -> bool:
        """
            Check whether a specific endpoint is enabled.

            An endpoint is considered enabled when the ``enabled_endpoints``
            set contains ``"all"`` or contains the given *endpoint_name*.

            :param endpoint_name: The name of the endpoint to check.

            :returns: True if the endpoint is enabled, False otherwise.
        """
        endpoints = cls.enabled_endpoints
        if endpoints is None:
            endpoints = {cls.ENABLE_ALL_TOKEN}

        is_enabled = cls.ENABLE_ALL_TOKEN in endpoints or endpoint_name in endpoints
        return is_enabled

    @classmethod
    def pre_authenticate(cls, request: Any) -> Optional[AuthError]:
        """
            Hook called before authentication processing.

            Override this method in a subclass to add custom
            pre-authentication logic such as rate limiting, request
            validation, or IP filtering. Return an :class:`AuthError`
            instance to abort the authentication flow and send an error
            response to the client.

            :param request: The incoming HTTP request object.

            :returns: None to continue authentication, or an AuthError
                      to abort with an error response.
        """
        return None

    @classmethod
    def post_authenticate(
        cls,
        request: Any,
        context: AuthenticationContext
    ) -> None:
        """
            Hook called after successful authentication.

            Override this method in a subclass to add custom
            post-authentication logic such as audit logging, session
            creation, or context enrichment.

            :param request: The incoming HTTP request object.
            :param context: The authentication context produced by
                            successful credential validation.
        """
        return

    @classmethod
    def format_error(cls, error: AuthError, status_code: int = 401) -> dict:
        """
            Format an authentication error into a response dictionary.

            Produces a standardized error response following RFC 6749
            conventions. The response dictionary contains the HTTP status
            code, a JSON-serializable body, and the content type.

            :param error: The authentication error to format.
            :param status_code: The HTTP status code for the response.
                                Defaults to 401.

            :returns: A dictionary with ``status``, ``body``, and
                      ``content_type`` keys suitable for returning from
                      an endpoint handler.
        """
        response = {
            "status": status_code,
            "body": error.to_dict(),
            "content_type": cls.JSON_CONTENT_TYPE
        }
        return response

    @classmethod
    def format_success(cls, response: AuthResponse, status_code: int = 200) -> dict:
        """
            Format a successful authentication result into a response dictionary.

            Produces a standardized success response. The response dictionary
            contains the HTTP status code, a JSON-serializable body, and the
            content type.

            :param response: The authentication response to format.
            :param status_code: The HTTP status code for the response.
                                Defaults to 200.

            :returns: A dictionary with ``status``, ``body``, and
                      ``content_type`` keys suitable for returning from
                      an endpoint handler.
        """
        result = {
            "status": status_code,
            "body": response.to_dict(),
            "content_type": cls.JSON_CONTENT_TYPE
        }
        return result

    @classmethod
    def sanitize_error_response(cls, response: dict) -> dict:
        """
            Sanitize an error response to remove sensitive data.

            Inspects the ``body`` of the response dictionary and redacts
            any values associated with sensitive keys (passwords, tokens,
            secrets, etc.). String values in the body are also scanned
            for embedded credential patterns and redacted accordingly.

            :param response: The response dictionary to sanitize. Expected
                             to contain a ``body`` key with a dict value.

            :returns: A new response dictionary with sensitive data removed
                      from the body.
        """
        sanitized = dict(response)
        body = sanitized.get("body")

        if isinstance(body, dict):
            sanitized["body"] = sanitize_dict(body, _SENSITIVE_BODY_KEYS)
        elif isinstance(body, str):
            sanitized["body"] = sanitize_credentials(body)

        return sanitized

    @classmethod
    def handle_internal_error(cls, error: Exception) -> dict:
        """
            Handle an internal error and return a safe response.

            Converts any exception into a generic ``server_error`` response
            that does not expose stack traces, exception class names, or
            other internal details to the client.

            :param error: The exception that occurred during request
                          processing.

            :returns: A response dictionary with a 500 status code and a
                      generic error body safe for client consumption.
        """
        safe_error = AuthError(
            error=cls.SERVER_ERROR_CODE,
            error_description=cls.SERVER_ERROR_MESSAGE
        )
        response = cls.format_error(safe_error, status_code=500)
        return response

    @classmethod
    def get_cors_headers(cls, origin: Optional[str] = None) -> Dict[str, str]:
        """
            Build CORS response headers for the given origin.

            When ``cors_origins`` is configured on the blueprint, this
            method checks whether the provided *origin* is in the allowed
            list and returns the appropriate CORS headers. A wildcard
            entry ``"*"`` in ``cors_origins`` allows any origin.

            :param origin: The ``Origin`` header value from the incoming
                           request. When None or not in the allowed list,
                           an empty dictionary is returned.

            :returns: A dictionary of CORS headers to include in the
                      response. Returns an empty dict when CORS is not
                      configured or the origin is not allowed.
        """
        cors_origins = cls.cors_origins
        if cors_origins is None:
            return {}

        if not origin:
            return {}

        # Check if the origin is allowed
        if cls.CORS_WILDCARD_ORIGIN in cors_origins:
            allowed_origin = cls.CORS_WILDCARD_ORIGIN
        elif origin in cors_origins:
            allowed_origin = origin
        else:
            return {}

        headers = {
            cls.CORS_ALLOW_ORIGIN_HEADER: allowed_origin,
            cls.CORS_ALLOW_METHODS_HEADER: cls.CORS_DEFAULT_METHODS,
            cls.CORS_ALLOW_HEADERS_HEADER: cls.CORS_DEFAULT_HEADERS,
            cls.CORS_ALLOW_CREDENTIALS_HEADER: cls.CORS_ALLOW_CREDENTIALS,
        }
        return headers

    @classmethod
    def set_access_policy(cls, policy: AccessPolicy) -> None:
        """
            Set the access policy for all endpoints in this blueprint.

            The access policy is applied as the class-level default and
            will be inherited by all endpoint descriptors registered via
            ``attach_at`` unless overridden at the endpoint level.

            :param policy: The :class:`AccessPolicy` to apply to all
                           endpoints in this blueprint.
        """
        cls.access_policy = policy
        return

    @classmethod
    def set_rate_limit(cls, rate_limit: RateLimit) -> None:
        """
            Set the rate limit for all endpoints in this blueprint.

            The rate limit is applied as the class-level default and
            will be inherited by all endpoint descriptors registered via
            ``attach_at`` unless overridden at the endpoint level.

            :param rate_limit: The :class:`RateLimit` to apply to all
                               endpoints in this blueprint.
        """
        cls.rate_limit = rate_limit
        return

    # -----------------------------------------------------------------
    # Decorator overrides
    # -----------------------------------------------------------------
    # The base RestEndpoint decorators (create, read, update, delete,
    # attach_at) register descriptors with the global EndpointRegistry
    # at class-definition time.  Because SecurityBlueprint subclasses
    # share leaf names (e.g. both BasicAuth and Session define "login"),
    # this causes EndpointConflictError.
    #
    # The overrides below store endpoint metadata on the handler
    # function itself.  The register() method later reads this metadata
    # and builds properly-pathed descriptors on demand.
    # -----------------------------------------------------------------

    @classmethod
    def attach_at(
        cls,
        leaf: Optional[str] = None,
        path: Optional[str] = None,
        methods: Optional[List[str]] = None,
        version: Optional[str] = None,
        tags: Optional[List[str]] = None,
        access_policy: Optional[AccessPolicy] = None,
        rate_limit: Optional[RateLimit] = None,
        request_schema: Optional[Type] = None,
        response_schema: Optional[Type] = None,
        error_map: Optional[Dict[int, Type]] = None,
        doc: Optional[Doc] = None,
        on_conflict: str = "error",
        absolute: bool = False,
        **extras
    ) -> Callable[[F], F]:
        """
            Decorator that stores endpoint metadata on the handler function.

            Unlike the parent :meth:`RestBlueprint.attach_at`, this method
            does **not** register with the global :class:`EndpointRegistry`.
            Instead it stores the metadata dictionary on the handler under
            the ``_security_endpoint_meta`` attribute.  The :meth:`register`
            method reads this metadata at call time and builds descriptors
            with paths resolved against the calling subclass's ``base_path``.

            :param leaf: URL leaf segment relative to blueprint base.
            :param path: URL path relative to blueprint base (or absolute
                         when *absolute* is True).
            :param methods: HTTP methods for this endpoint.
            :param version: API version string.
            :param tags: Documentation tags.
            :param access_policy: Endpoint-level access policy.
            :param rate_limit: Endpoint-level rate limit.
            :param request_schema: Request body schema.
            :param response_schema: Response body schema.
            :param error_map: Mapping of status codes to error schemas.
            :param doc: Documentation metadata.
            :param on_conflict: Conflict handling (unused, kept for API compat).
            :param absolute: If True, *path* is used as-is without prepending
                             the blueprint base.
            :param extras: Additional metadata.

            :returns: Decorator that returns the original function unchanged.
        """
        def decorator(func: F) -> F:
            meta = {
                "leaf": leaf,
                "path": path,
                "methods": methods if methods is not None else list(cls.methods),
                "version": version if version is not None else cls.version,
                "tags": tags if tags is not None else list(cls.tags),
                "access_policy": access_policy,
                "rate_limit": rate_limit,
                "request_schema": request_schema,
                "response_schema": response_schema,
                "error_map": error_map,
                "doc": doc,
                "absolute": absolute,
                "extras": extras,
            }
            setattr(func, _ENDPOINT_META_ATTR, meta)
            return func

        return decorator

    @classmethod
    def create(
        cls,
        leaf: Optional[str] = None,
        path: Optional[str] = None,
        version: Optional[str] = None,
        tags: Optional[List[str]] = None,
        access_policy: Optional[AccessPolicy] = None,
        rate_limit: Optional[RateLimit] = None,
        request_schema: Optional[Type] = None,
        response_schema: Optional[Type] = None,
        error_map: Optional[Dict[int, Type]] = None,
        doc: Optional[Doc] = None,
        on_conflict: str = "error",
        **extras
    ) -> Callable[[F], F]:
        """
            Convenience decorator for POST endpoints.

            Delegates to :meth:`attach_at` with ``methods=["POST"]``.
        """
        return cls.attach_at(
            leaf=leaf,
            path=path,
            methods=["POST"],
            version=version,
            tags=tags,
            access_policy=access_policy,
            rate_limit=rate_limit,
            request_schema=request_schema,
            response_schema=response_schema,
            error_map=error_map,
            doc=doc,
            on_conflict=on_conflict,
            **extras
        )

    @classmethod
    def read(
        cls,
        leaf: Optional[str] = None,
        path: Optional[str] = None,
        version: Optional[str] = None,
        tags: Optional[List[str]] = None,
        access_policy: Optional[AccessPolicy] = None,
        rate_limit: Optional[RateLimit] = None,
        response_schema: Optional[Type] = None,
        error_map: Optional[Dict[int, Type]] = None,
        doc: Optional[Doc] = None,
        on_conflict: str = "error",
        **extras
    ) -> Callable[[F], F]:
        """
            Convenience decorator for GET endpoints.

            Delegates to :meth:`attach_at` with ``methods=["GET"]``.
        """
        return cls.attach_at(
            leaf=leaf,
            path=path,
            methods=["GET"],
            version=version,
            tags=tags,
            access_policy=access_policy,
            rate_limit=rate_limit,
            request_schema=None,
            response_schema=response_schema,
            error_map=error_map,
            doc=doc,
            on_conflict=on_conflict,
            **extras
        )

    @classmethod
    def delete(
        cls,
        leaf: Optional[str] = None,
        path: Optional[str] = None,
        version: Optional[str] = None,
        tags: Optional[List[str]] = None,
        access_policy: Optional[AccessPolicy] = None,
        rate_limit: Optional[RateLimit] = None,
        error_map: Optional[Dict[int, Type]] = None,
        doc: Optional[Doc] = None,
        on_conflict: str = "error",
        **extras
    ) -> Callable[[F], F]:
        """
            Convenience decorator for DELETE endpoints.

            Delegates to :meth:`attach_at` with ``methods=["DELETE"]``.
        """
        return cls.attach_at(
            leaf=leaf,
            path=path,
            methods=["DELETE"],
            version=version,
            tags=tags,
            access_policy=access_policy,
            rate_limit=rate_limit,
            request_schema=None,
            response_schema=None,
            error_map=error_map,
            doc=doc,
            on_conflict=on_conflict,
            **extras
        )

    # -----------------------------------------------------------------
    # Registration
    # -----------------------------------------------------------------

    @classmethod
    def register(
        cls,
        router: Optional["RouterProtocol"] = None
    ) -> List[EndpointDescriptor]:
        """
            Register all child endpoints and return their descriptors.

            Scans the class hierarchy for methods decorated with
            :meth:`attach_at` (or its convenience wrappers ``create``,
            ``read``, ``delete``).  For each decorated method the stored
            metadata is combined with the calling subclass's ``base_path``
            to produce an :class:`EndpointDescriptor` with a fully
            resolved path.

            Blueprint-level ``access_policy`` and ``rate_limit`` are
            propagated to descriptors that do not carry their own.

            :param router: Optional router to add endpoints to.  If None,
                          descriptors are returned without router registration.

            :returns: List of EndpointDescriptor objects for all registered
                      endpoints.
        """
        base = cls._get_base_path()
        descriptors = []
        seen_handlers = set()

        # Walk the MRO to collect decorated methods (subclass first)
        for klass in cls.__mro__:
            if klass is SecurityBlueprint:
                break
            if klass is RestBlueprint:
                break

            for attr_name in list(vars(klass)):
                obj = vars(klass).get(attr_name)

                # The underlying function is where ``attach_at``
                # stashes its metadata marker; we read the metadata
                # from there. ``staticmethod`` / ``classmethod``
                # wrappers store the function on ``__func__``;
                # plain functions are themselves the underlying.
                if isinstance(obj, (classmethod, staticmethod)):
                    underlying = obj.__func__
                else:
                    underlying = obj

                if not callable(underlying):
                    continue

                meta = getattr(underlying, _ENDPOINT_META_ATTR, None)
                if meta is None:
                    continue

                # Avoid duplicates when a subclass overrides a parent
                # method (de-dup on the underlying function so a
                # bound-method instance per access doesn't fool us).
                handler_id = id(underlying)
                if handler_id in seen_handlers:
                    continue
                seen_handlers.add(handler_id)

                # Resolve the bound form so the request dispatcher
                # can call ``descriptor.handler(request)`` directly:
                #
                # * ``classmethod`` ⇒ bound method that injects the
                #   *most-derived* subclass as the first argument
                #   (so site-supplied collaborators on the subclass
                #   are visible inside the handler — anchoring to the
                #   ``klass`` we found the method on would freeze
                #   ``cls`` at the ancestor that *defined* the
                #   method, hiding subclass overrides).
                # * ``staticmethod`` ⇒ unwrapped function (no
                #   implicit ``self`` / ``cls`` to thread).
                # * plain function ⇒ the function itself.
                #
                # Using ``getattr(cls, attr_name)`` triggers Python's
                # descriptor binding, which produces the right
                # shape for each case without us reproducing the
                # binding rules by hand.
                bound_handler = getattr(cls, attr_name)

                descriptor = cls._build_descriptor(
                    bound_handler,
                    meta,
                    base,
                )
                descriptors.append(descriptor)

        # Add to router if provided
        if router is not None:
            for descriptor in descriptors:
                router.add_endpoint(descriptor)

        return descriptors

    @classmethod
    def _build_descriptor(
        cls,
        handler: Callable,
        meta: Dict[str, Any],
        base: Optional[str]
    ) -> EndpointDescriptor:
        """
            Build an :class:`EndpointDescriptor` from handler metadata.

            Resolves the endpoint path against the blueprint *base* path,
            merges tags, and propagates blueprint-level constraints when
            the endpoint does not define its own.

            :param handler: The endpoint handler callable.
            :param meta: The metadata dictionary stored by the decorator.
            :param base: The blueprint base path, or None.

            :returns: A fully resolved EndpointDescriptor.
        """
        leaf = meta.get("leaf")
        raw_path = meta.get("path")
        absolute = meta.get("absolute", False)

        # Resolve the full path
        full_path = cls._resolve_path(leaf, raw_path, base, absolute)

        # Build constraints
        ep_access = meta.get("access_policy")
        ep_rate = meta.get("rate_limit")

        if ep_access is None:
            ep_access = getattr(cls, "access_policy", None)
        if ep_rate is None:
            ep_rate = getattr(cls, "rate_limit", None)

        constraints = EndpointConstraints(
            access_policy=ep_access,
            rate_limit=ep_rate,
            scopes=ep_access.scopes if ep_access else [],
            roles=ep_access.roles if ep_access else []
        )

        # Merge tags
        ep_tags = meta.get("tags") or []
        merged_tags = cls._merge_blueprint_tags(ep_tags)

        # Mark every SecurityBlueprint descriptor as ``"auth"`` so
        # the OpenAPI generator's default filter (which only emits
        # endpoints with ``endpoint_type in {"rest", "auth"}``)
        # includes auth flows in the generated spec. Without this
        # mark the magic-link / OAuth / session endpoints would be
        # silently excluded from the API docs even though they
        # carry full :class:`Doc` metadata. Subclasses that already
        # set their own ``endpoint_type`` (e.g. via
        # ``@attach_at(..., endpoint_type="rest")``) win — their
        # value is preserved.
        descriptor_extras: Dict[str, Any] = dict(meta.get("extras", {}))
        descriptor_extras.setdefault("endpoint_type", cls.DEFAULT_ENDPOINT_TYPE)

        descriptor = EndpointDescriptor(
            handler=handler,
            module=handler.__module__,
            leaf=None,
            path=full_path,
            methods=list(meta.get("methods", ["GET"])),
            version=meta.get("version"),
            tags=merged_tags if merged_tags else [],
            constraints=constraints,
            doc=meta.get("doc"),
            extras=descriptor_extras,
        )

        return descriptor

    @classmethod
    def _resolve_path(
        cls,
        leaf: Optional[str],
        path: Optional[str],
        base: Optional[str],
        absolute: bool
    ) -> str:
        """
            Compute the full endpoint path.

            When *absolute* is True the *path* is returned unchanged.
            Otherwise the path is constructed from *leaf* or *path* and
            prepended with *base*.

            :param leaf: Leaf segment (e.g. ``"login"``).
            :param path: Explicit path (e.g. ``""`` or ``"/.well-known/..."``).
            :param base: Blueprint base path.
            :param absolute: Whether the path is absolute.

            :returns: The resolved path string.
        """
        # Determine the raw relative path
        if absolute and path is not None:
            return path

        if path is not None:
            raw = path
        elif leaf is not None:
            raw = "/{}".format(leaf)
        else:
            raw = ""

        # Absolute well-known paths bypass the base prefix
        if raw.startswith("/.well-known"):
            return raw

        if base is None:
            return raw

        # Normalise: avoid double slashes
        if raw.startswith("/"):
            return "{}{}".format(base, raw)
        elif raw == "":
            return base
        else:
            return "{}/{}".format(base, raw)

    @classmethod
    def register_with_middleware(
        cls,
        middleware: "AuthenticationMiddleware",
        exclude: bool = False,
        optional: bool = False,
        policy: Optional[AccessPolicy] = None
    ) -> None:
        """
            Register this blueprint's paths with an AuthenticationMiddleware.

            This method configures the middleware to handle authentication
            for the blueprint's endpoint paths. Paths can be excluded from
            authentication, marked as optional, or associated with a
            specific access policy.

            :param middleware: The :class:`AuthenticationMiddleware` to
                               register with.
            :param exclude: If True, blueprint paths are excluded from
                            authentication.
            :param optional: If True, authentication is optional for
                             blueprint paths.
            :param policy: Optional :class:`AccessPolicy` to associate
                           with blueprint paths in the middleware.
        """
        base = cls._get_base_path()
        if base is None:
            return

        # Add paths to middleware configuration
        if exclude:
            middleware.exclude_paths.add(base)
            middleware.exclude_paths.add("{}/{}".format(base, "*"))
        elif optional:
            middleware.optional_paths.add(base)
            middleware.optional_paths.add("{}/{}".format(base, "*"))

        # Register access policy for the base path
        if policy is not None:
            middleware.path_policies[base] = policy
        elif getattr(cls, "access_policy", None) is not None:
            middleware.path_policies[base] = cls.access_policy

        return

    @classmethod
    def get_endpoint_paths(cls) -> List[str]:
        """
            Get all endpoint paths registered by this blueprint.

            Collects the paths from all endpoint descriptors that belong
            to this blueprint, resolved against the blueprint's base path.

            :returns: List of path strings for all registered endpoints.
        """
        descriptors = cls.register()

        paths = []
        for descriptor in descriptors:
            if descriptor.path is not None:
                paths.append(descriptor.path)
            elif descriptor.leaf is not None:
                paths.append("/{}".format(descriptor.leaf))

        return paths

    @classmethod
    def register_with_registry(
        cls,
        registry: Optional[EndpointRegistry] = None,
        on_conflict: str = "replace"
    ) -> List[EndpointDescriptor]:
        """
            Register all blueprint endpoints with an EndpointRegistry.

            Builds endpoint descriptors from decorated handler methods and
            registers each one with the given :class:`EndpointRegistry`.
            A registry is required -- there is no global one to fall back
            to, because a registry belongs to the application that built
            it.

            This method enables integration with the webworks endpoint
            infrastructure so that blueprint endpoints appear alongside
            other registered endpoints in security maps, documentation
            generation, and bulk router loading.

            :param registry: The :class:`EndpointRegistry` to register with.
                             Required; passing None raises ValueError.
            :param on_conflict: Conflict handling strategy passed to the
                                registry. Defaults to ``"replace"`` so that
                                re-registration overwrites previous entries.

            :returns: List of EndpointDescriptor objects that were registered.
        """
        if registry is None:
            errmsg = "register_with_registry requires a registry. Endpoints " \
                     "belong to the application that collected them; there " \
                     "is no process-wide registry to default to."
            raise ValueError(errmsg)

        descriptors = cls.register()

        for descriptor in descriptors:
            registry.register(descriptor, on_conflict=on_conflict)

        return descriptors

    @classmethod
    def integrate(
        cls,
        router: Optional["RouterProtocol"] = None,
        registry: Optional[EndpointRegistry] = None,
        middleware: Optional["AuthenticationMiddleware"] = None,
        access_policy: Optional[AccessPolicy] = None,
        rate_limit: Optional[RateLimit] = None,
        exclude_from_auth: bool = False,
        optional_auth: bool = False
    ) -> List[EndpointDescriptor]:
        """
            Perform full integration with webworks infrastructure.

            This convenience method registers the blueprint's endpoints
            with the :class:`EndpointRegistry`, :class:`Router`, and
            :class:`AuthenticationMiddleware` in a single call. It also
            applies access policy and rate limiting configuration before
            registration so that all descriptors carry the correct
            constraints.

            :param router: Optional :class:`Router` to register endpoints
                           with for request routing.
            :param registry: Optional :class:`EndpointRegistry` to register
                             endpoints with. Defaults to the global registry.
            :param middleware: Optional :class:`AuthenticationMiddleware` to
                              register paths with for authentication handling.
            :param access_policy: Optional :class:`AccessPolicy` to apply
                                  to all blueprint endpoints before
                                  registration.
            :param rate_limit: Optional :class:`RateLimit` to apply to all
                               blueprint endpoints before registration.
            :param exclude_from_auth: If True, blueprint paths are excluded
                                      from authentication in the middleware.
            :param optional_auth: If True, authentication is optional for
                                  blueprint paths in the middleware.

            :returns: List of EndpointDescriptor objects for all registered
                      endpoints.
        """
        # Apply access policy and rate limit before building descriptors
        if access_policy is not None:
            cls.set_access_policy(access_policy)

        if rate_limit is not None:
            cls.set_rate_limit(rate_limit)

        # Register with router (also builds descriptors)
        descriptors = cls.register(router=router)

        # Register with the endpoint registry, when one was supplied. There
        # is no global registry to fall back to.
        if registry is not None:
            for descriptor in descriptors:
                registry.register(descriptor, on_conflict="replace")

        # Register with middleware
        if middleware is not None:
            cls.register_with_middleware(
                middleware,
                exclude=exclude_from_auth,
                optional=optional_auth,
                policy=access_policy
            )

        return descriptors

