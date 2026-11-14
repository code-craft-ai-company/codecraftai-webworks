"""
.. module:: apikey
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: API key authentication blueprint providing key management endpoints.

.. moduleauthor:: Code Craft AI LLC

This module provides the :class:`APIKeyBlueprint` class which extends
:class:`SecurityBlueprint` to offer pre-built endpoints for API key
management. The blueprint supports key generation, listing, retrieval,
and revocation. Key values are only returned once at creation time.

Endpoints:
    - ``POST <base_path>`` — Generate a new API key.
    - ``GET <base_path>`` — List all active API keys.
    - ``GET <base_path>/{key_id}`` — Get details for a specific API key.
    - ``DELETE <base_path>/{key_id}`` — Revoke an API key.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


import hmac
import inspect
import logging
import math
import secrets
import threading
import time

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ccai.webworks.authentication.apikey import hash_api_key
from ccai.webworks.authentication.core import Principal

from ccai.webworks.authentication.blueprints.responses import AuthError
from ccai.webworks.authentication.blueprints.schemas import (
    APIKeyCreateRequest,
    APIKeyResponse
)
from ccai.webworks.authentication.blueprints.security import (
    SecurityBlueprint,
    run_async as _run_async
)
from ccai.webworks.endpoints.doc import Doc


# Module-level logger for the API key blueprint.
logger = logging.getLogger(__name__)


class APIKeyStore:
    """
        Abstract interface for API key persistence.

        Implementations of this class handle the storage, retrieval,
        validation and revocation of API keys. The store persists the
        digest of the key (see
        :func:`ccai.webworks.authentication.apikey.hash_api_key`), never
        the raw key value, together with the key's metadata and the
        identifier of the principal that owns it.

        The same store serves both sides of API key authentication: the
        :class:`APIKeyBlueprint` endpoints write keys through it and
        :class:`ccai.webworks.authentication.apikey.APIKeyAuthenticator`
        validates presented keys through :meth:`validate_key`.

        Subclasses must implement all async methods except
        :meth:`validate_key`, which is built on :meth:`get_key_by_hash`.
    """

    async def store_key(
        self,
        key_id: str,
        key_hash: str,
        name: str,
        scopes: List[str],
        created_at: str,
        expires_at: Optional[str],
        owner: Optional[str] = None
    ) -> None:
        """
            Store a new API key record.

            :param key_id: The unique identifier for the key.
            :param key_hash: The digest of the key value. The raw key is
                             never handed to the store.
            :param name: The human-readable name for the key.
            :param scopes: The permission scopes assigned to the key.
            :param created_at: ISO 8601 timestamp of creation.
            :param expires_at: Optional ISO 8601 timestamp of expiration.
            :param owner: Identifier of the principal that created the
                          key. It must be returned as ``owner`` by
                          :meth:`get_key`, :meth:`list_keys` and
                          :meth:`get_key_by_hash`.
        """
        raise NotImplementedError

    async def get_key(self, key_id: str) -> Optional[Dict[str, Any]]:
        """
            Retrieve metadata for a specific API key.

            The returned dictionary should contain key_id, name, scopes,
            created_at, expires_at and owner fields. It must NOT contain
            the raw key value.

            :param key_id: The unique identifier of the key to retrieve.

            :returns: A dictionary of key metadata, or None if not found.
        """
        raise NotImplementedError

    async def list_keys(self) -> List[Dict[str, Any]]:
        """
            List all active (non-revoked) API keys.

            Each dictionary in the returned list should contain key_id,
            name, scopes, created_at, expires_at and owner fields. Raw
            key values must NOT be included.

            :returns: A list of key metadata dictionaries.
        """
        raise NotImplementedError

    async def revoke_key(self, key_id: str) -> bool:
        """
            Revoke an API key, making it immediately invalid.

            :param key_id: The unique identifier of the key to revoke.

            :returns: True if the key was found and revoked, False otherwise.
        """
        raise NotImplementedError

    async def get_key_by_hash(self, key_hash: str) -> Optional[Dict[str, Any]]:
        """
            Retrieve the metadata of the active key with a given digest.

            :param key_hash: The digest of a presented key value.

            :returns: The key metadata dictionary (as for :meth:`get_key`),
                      or None if no active key has that digest.
        """
        raise NotImplementedError

    async def validate_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """
            Validate a presented API key.

            This is the method
            :class:`ccai.webworks.authentication.apikey.APIKeyAuthenticator`
            calls. The key is hashed and looked up by digest; a revoked,
            unknown or expired key is refused.

            :param api_key: The raw API key value from the request.

            :returns: None if the key is not valid, otherwise a
                      dictionary describing it: ``client_id`` (the owner,
                      which becomes the principal identifier), ``name``,
                      ``key_id``, ``permissions`` and ``scopes`` (the
                      key's scopes) and ``expires_at``.
        """
        key_hash = hash_api_key(api_key)

        record = await self.get_key_by_hash(key_hash)
        if record is None:
            return None

        if is_key_record_expired(record):
            return None

        scopes = list(record.get("scopes") or [])

        key_info = {
            "key_id": record.get("key_id"),
            "name": record.get("name"),
            "permissions": scopes,
            "scopes": scopes,
            "expires_at": record.get("expires_at"),
        }

        owner = record.get("owner")
        if owner is not None:
            key_info["client_id"] = owner

        return key_info


def is_key_record_expired(record: Dict[str, Any]) -> bool:
    """
        Check whether an API key record has passed its expiration.

        An ``expires_at`` value that cannot be parsed counts as expired.

        :param record: The key metadata dictionary.

        :returns: True if the key has expired.
    """
    expires_at = record.get("expires_at")
    if expires_at is None:
        return False

    try:
        expires_dt = datetime.fromisoformat(str(expires_at))
    except ValueError:
        return True

    if expires_dt.tzinfo is None:
        expires_dt = expires_dt.replace(tzinfo=timezone.utc)

    rtnval = datetime.now(tz=timezone.utc) > expires_dt
    return rtnval


class InMemoryAPIKeyStore(APIKeyStore):
    """
        In-memory :class:`APIKeyStore` used when none is configured.

        Suitable for development and tests: keys are private to one
        process and lost on restart. Only the digest of each key is kept.
    """

    def __init__(self):
        """
            Initialize an empty store.
        """
        self._records: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        return

    async def store_key(
        self,
        key_id: str,
        key_hash: str,
        name: str,
        scopes: List[str],
        created_at: str,
        expires_at: Optional[str],
        owner: Optional[str] = None
    ) -> None:
        """
            Store a new API key record.

            :param key_id: The unique identifier for the key.
            :param key_hash: The digest of the key value.
            :param name: The human-readable name for the key.
            :param scopes: The permission scopes assigned to the key.
            :param created_at: ISO 8601 timestamp of creation.
            :param expires_at: Optional ISO 8601 timestamp of expiration.
            :param owner: Identifier of the principal that owns the key.
        """
        with self._lock:
            self._records[key_id] = {
                "key_id": key_id,
                "key_hash": key_hash,
                "name": name,
                "scopes": list(scopes),
                "created_at": created_at,
                "expires_at": expires_at,
                "owner": owner,
            }
        return

    async def get_key(self, key_id: str) -> Optional[Dict[str, Any]]:
        """
            Retrieve metadata for a specific API key.

            :param key_id: The unique identifier of the key to retrieve.

            :returns: A dictionary of key metadata, or None if not found.
        """
        with self._lock:
            record = self._records.get(key_id)

        if record is None:
            return None

        rtnval = self._to_metadata(record)
        return rtnval

    async def list_keys(self) -> List[Dict[str, Any]]:
        """
            List all active API keys.

            :returns: A list of key metadata dictionaries.
        """
        with self._lock:
            records = list(self._records.values())

        rtnval = [self._to_metadata(record) for record in records]
        return rtnval

    async def revoke_key(self, key_id: str) -> bool:
        """
            Revoke an API key, making it immediately invalid.

            :param key_id: The unique identifier of the key to revoke.

            :returns: True if the key was found and revoked, False otherwise.
        """
        with self._lock:
            record = self._records.pop(key_id, None)

        rtnval = record is not None
        return rtnval

    async def get_key_by_hash(self, key_hash: str) -> Optional[Dict[str, Any]]:
        """
            Retrieve the metadata of the active key with a given digest.

            :param key_hash: The digest of a presented key value.

            :returns: The key metadata dictionary, or None.
        """
        with self._lock:
            records = list(self._records.values())

        for record in records:
            if hmac.compare_digest(str(record.get("key_hash")), key_hash):
                rtnval = self._to_metadata(record)
                return rtnval

        return None

    def get_key_count(self) -> int:
        """
            Get the number of active keys in the store.

            :returns: The number of keys.
        """
        with self._lock:
            rtnval = len(self._records)
        return rtnval

    def _to_metadata(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
            Copy a stored record without its key digest.

            :param record: The stored record.

            :returns: The key metadata dictionary.
        """
        rtnval = {
            "key_id": record.get("key_id"),
            "name": record.get("name"),
            "scopes": list(record.get("scopes") or []),
            "created_at": record.get("created_at"),
            "expires_at": record.get("expires_at"),
            "owner": record.get("owner"),
        }
        return rtnval


class APIKeyBlueprint(SecurityBlueprint):
    """
        Blueprint for API Key management endpoints.

        Provides endpoints for generating, listing, retrieving, and
        revoking API keys. Key values are only returned once at creation
        time and are never exposed in subsequent list or get responses.

        Key generation produces a cryptographically secure random key
        value. The blueprint supports configurable key expiration and
        permission scoping.

        Default Endpoints:
            - ``POST /auth/keys`` — Generate a new API key.
            - ``GET /auth/keys`` — List all active API keys.
            - ``GET /auth/keys/{key_id}`` — Get details for a specific
              API key.
            - ``DELETE /auth/keys/{key_id}`` — Revoke an API key.

        Class Attributes:
            base_path: Base URL path for all endpoints. Defaults to
                       ``"/auth/keys"``.
            tags: Documentation tags applied to all endpoints.
            key_store: Optional :class:`APIKeyStore` for persisting keys.
                       When None, an :class:`InMemoryAPIKeyStore` private
                       to the blueprint class is used.
            default_expiration: Default key lifetime in seconds. When None,
                                keys do not expire unless the request
                                specifies an ``expires_in`` value.

        Ownership:
            Every endpoint requires an authenticated caller: the
            blueprint reads the principal the authentication middleware
            stored on the request (``request.auth``) and answers 401
            without one. A key is owned by the principal that created
            it; list, get and revoke only ever see the caller's own keys.
            A key can be given only scopes its owner holds (see
            :meth:`get_allowed_scopes`).

        Authenticating with issued keys:
            Only the SHA-256 digest of a key is stored. Give the store
            returned by :meth:`get_key_store` to
            :class:`ccai.webworks.authentication.apikey.APIKeyAuthenticator`
            to accept the keys this blueprint issues.
    """

    base_path: str = "/auth/keys"
    tags: List[str] = ["Authentication", "API Keys"]

    key_store: Optional[APIKeyStore] = None
    default_expiration: Optional[int] = None

    # --- Class constants ---
    # Override these on a subclass to rebrand wire-format strings or change
    # entropy bit-widths without rewriting handler bodies.

    # Error codes
    ENDPOINT_DISABLED_ERROR_CODE: str = "endpoint_disabled"
    INVALID_REQUEST_ERROR_CODE: str = "invalid_request"
    INVALID_SCOPE_ERROR_CODE: str = "invalid_scope"
    NOT_FOUND_ERROR_CODE: str = "not_found"
    SERVER_ERROR_CODE: str = "server_error"

    # Name of the route parameter that carries the key identifier
    KEY_ID_PATH_PARAMETER: str = "key_id"

    # Success / response messages
    KEY_REVOKED_MESSAGE: str = "API key revoked"

    # Random-byte lengths used for key generation
    KEY_VALUE_BYTE_LENGTH: int = 32
    KEY_ID_BYTE_LENGTH: int = 16

    @classmethod
    def get_key_store(cls) -> APIKeyStore:
        """
            Get the store the blueprint persists keys in.

            Returns the configured :attr:`key_store`, or an
            :class:`InMemoryAPIKeyStore` that belongs to this blueprint
            class alone (a subclass gets its own).

            :returns: The :class:`APIKeyStore` in use.
        """
        if cls.key_store is not None:
            return cls.key_store

        store = cls.__dict__.get("_default_key_store")
        if store is None:
            store = InMemoryAPIKeyStore()
            cls._default_key_store = store
            cls.note_memory_fallback("key_store")

        return store

    @classmethod
    def get_allowed_scopes(cls, principal: Principal) -> List[str]:
        """
            Get the scopes a principal may assign to its API keys.

            The default is the principal's ``permissions``, so a key can
            never do more than its owner. Override this on a subclass to
            derive grantable scopes differently.

            :param principal: The authenticated caller.

            :returns: The scopes the caller may assign.
        """
        rtnval = sorted(str(permission) for permission in principal.permissions)
        return rtnval

    @classmethod
    def _resolve_key_id(cls, request: Any, key_id: Optional[str]) -> Optional[str]:
        """
            Determine the key identifier a request addresses.

            The dispatcher calls handlers with the request only and
            exposes route parameters through ``request.path_params``; a
            direct caller may pass the identifier explicitly.

            :param request: The incoming HTTP request object.
            :param key_id: The identifier passed by a direct caller.

            :returns: The key identifier, or None if there is none.
        """
        if key_id:
            return str(key_id)

        path_params = getattr(request, "path_params", None)
        if isinstance(path_params, dict):
            value = path_params.get(cls.KEY_ID_PATH_PARAMETER)
            if value:
                return str(value)

        return None

    @classmethod
    def _get_owned_key(
        cls,
        principal: Principal,
        key_id: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """
            Look up a key and return it only if the caller owns it.

            :param principal: The authenticated caller.
            :param key_id: The key identifier, or None.

            :returns: The key metadata, or None when the key does not
                      exist or belongs to someone else.
        """
        if key_id is None:
            return None

        key_record = _run_async(cls.get_key_store().get_key(key_id))
        if not isinstance(key_record, dict):
            return None

        if key_record.get("owner") != principal.identifier:
            return None

        return key_record

    @classmethod
    def _key_not_found_response(cls) -> dict:
        """
            Build the 404 response for a key the caller cannot see.

            The same response is used for a key that does not exist and
            one that belongs to another principal, so key identifiers
            cannot be probed.

            :returns: A response dictionary with a 404 status.
        """
        error = AuthError(
            error=cls.NOT_FOUND_ERROR_CODE,
            error_description="API key not found"
        )
        response = cls.format_error(error, status_code=404)
        return response

    @classmethod
    def _to_public_record(cls, key_record: Dict[str, Any]) -> Dict[str, Any]:
        """
            Reduce a key record to the fields a response may carry.

            :param key_record: The key metadata from the store.

            :returns: The metadata without key material.
        """
        rtnval = {
            "key_id": key_record.get("key_id"),
            "name": key_record.get("name"),
            "scopes": key_record.get("scopes", []),
            "created_at": key_record.get("created_at"),
            "expires_at": key_record.get("expires_at"),
        }
        return rtnval

    @classmethod
    def _generate_key_value(cls) -> str:
        """
            Generate a cryptographically secure API key value.

            The key is a URL-safe base64-encoded string of 32 random bytes,
            providing 256 bits of entropy.

            :returns: A random API key string.
        """
        key_value = secrets.token_urlsafe(cls.KEY_VALUE_BYTE_LENGTH)
        return key_value

    @classmethod
    def _generate_key_id(cls) -> str:
        """
            Generate a unique identifier for an API key.

            The identifier is a URL-safe base64-encoded string of 16
            random bytes.

            :returns: A random key identifier string.
        """
        key_id = secrets.token_urlsafe(cls.KEY_ID_BYTE_LENGTH)
        return key_id

    @classmethod
    def _compute_expires_at(cls, expires_in: Optional[int]) -> Optional[str]:
        """
            Compute the expiration timestamp for a key.

            Uses the provided ``expires_in`` value if given, otherwise
            falls back to the blueprint's ``default_expiration``. Returns
            None if neither is set.

            :param expires_in: Optional lifetime in seconds from the request.

            :returns: An ISO 8601 timestamp string, or None if no expiration.
        """
        effective_expiration = expires_in
        if effective_expiration is None:
            effective_expiration = cls.default_expiration

        if effective_expiration is None:
            return None

        now = time.time()
        expires_ts = now + effective_expiration
        expires_at = datetime.fromtimestamp(
            expires_ts, tz=timezone.utc
        ).isoformat()
        return expires_at

    @classmethod
    @SecurityBlueprint.create(
        path="",
        request_schema=APIKeyCreateRequest,
        response_schema=APIKeyResponse,
        doc=Doc(
            summary="Generate API key",
            description="Create a new API key. The key value is only "
                        "returned once in this response."
        ),
        on_conflict="replace"
    )
    def create_key(cls, request: Any) -> dict:
        """
            Generate a new API key.

            Creates a cryptographically secure API key and stores its
            metadata. The raw key value is included in the creation
            response and is never returned again by any other endpoint.

            The endpoint can be disabled via the ``enabled_endpoints``
            configuration. When disabled, a 404 response is returned.

            :param request: The incoming HTTP request object. The request
                            body must contain a ``name`` field and may
                            optionally include ``scopes`` and ``expires_in``.

            :returns: A response dictionary with ``status``, ``body``, and
                      ``content_type`` keys.
        """
        if not cls.is_endpoint_enabled("create"):
            error = AuthError(
                error=cls.ENDPOINT_DISABLED_ERROR_CODE,
                error_description="Create key endpoint is disabled"
            )
            response = cls.format_error(error, status_code=404)
            return response

        # Pre-authentication hook
        pre_error = cls.pre_authenticate(request)
        if pre_error is not None:
            response = cls.format_error(pre_error)
            return response

        # A key belongs to the principal that creates it
        principal = cls.get_authenticated_principal(request)
        if principal is None:
            response = cls.authentication_required_response()
            return response

        body = cls.read_request_data(request)
        if body is None:
            response = cls.invalid_body_response()
            return response

        name = body.get("name")

        if not name or not isinstance(name, str):
            error = AuthError(
                error=cls.INVALID_REQUEST_ERROR_CODE,
                error_description="Key name is required"
            )
            response = cls.format_error(error, status_code=400)
            return response

        scopes = body.get("scopes")
        if scopes is None:
            scopes = []

        scopes_are_valid = isinstance(scopes, list)
        if scopes_are_valid:
            for scope in scopes:
                if not isinstance(scope, str):
                    scopes_are_valid = False
                    break

        if not scopes_are_valid:
            error = AuthError(
                error=cls.INVALID_REQUEST_ERROR_CODE,
                error_description="scopes must be a list of strings"
            )
            response = cls.format_error(error, status_code=400)
            return response

        # A key never carries a scope its owner does not hold
        allowed_scopes = set(cls.get_allowed_scopes(principal))
        for scope in scopes:
            if scope not in allowed_scopes:
                error = AuthError(
                    error=cls.INVALID_SCOPE_ERROR_CODE,
                    error_description="A requested scope is not held by the caller"
                )
                response = cls.format_error(error, status_code=403)
                return response

        expires_in = body.get("expires_in")
        if expires_in is not None:
            expires_in_is_valid = (
                not isinstance(expires_in, bool)
                and isinstance(expires_in, (int, float))
                and math.isfinite(expires_in)
                and expires_in > 0
            )
            if not expires_in_is_valid:
                error = AuthError(
                    error=cls.INVALID_REQUEST_ERROR_CODE,
                    error_description="expires_in must be a positive number of seconds"
                )
                response = cls.format_error(error, status_code=400)
                return response

        key_store = cls.get_key_store()

        # The store must be able to record the owner, otherwise the
        # key could not be confined to its creator afterwards.
        if not _accepts_owner(key_store.store_key):
            logger.error(
                "%s: key store %s does not accept the 'owner' argument of "
                "store_key; refusing to create an unowned key",
                cls.__name__,
                type(key_store).__name__,
            )
            error = AuthError(
                error=cls.SERVER_ERROR_CODE,
                error_description="API key storage is not configured correctly"
            )
            response = cls.format_error(error, status_code=500)
            return response

        # Generate key identifiers
        key_id = cls._generate_key_id()
        key_value = cls._generate_key_value()

        # Compute timestamps
        now = datetime.now(tz=timezone.utc)
        created_at = now.isoformat()
        expires_at = cls._compute_expires_at(expires_in)

        # Only the digest of the key is persisted. The raw value exists
        # in this response alone and cannot be recovered afterwards.
        _run_async(
            key_store.store_key(
                key_id=key_id,
                key_hash=hash_api_key(key_value),
                name=name,
                scopes=scopes,
                created_at=created_at,
                expires_at=expires_at,
                owner=principal.identifier
            )
        )

        # Build response — key value is ONLY returned here
        response_body = {
            "key_id": key_id,
            "name": name,
            "key": key_value,
            "scopes": scopes,
            "created_at": created_at,
            "expires_at": expires_at,
        }

        response = {
            "status": 201,
            "body": response_body,
            "content_type": cls.JSON_CONTENT_TYPE
        }
        return response

    @classmethod
    @SecurityBlueprint.read(
        path="",
        response_schema=APIKeyResponse,
        doc=Doc(
            summary="List API keys",
            description="List all active API keys for the authenticated "
                        "user. Key values are not included."
        ),
        on_conflict="replace"
    )
    def list_keys(cls, request: Any) -> dict:
        """
            List the caller's active API keys.

            Returns metadata for the non-revoked API keys owned by the
            authenticated caller. The raw key value is never included in
            list responses.

            The endpoint can be disabled via the ``enabled_endpoints``
            configuration. When disabled, a 404 response is returned.

            :param request: The incoming HTTP request object.

            :returns: A response dictionary with ``status``, ``body``, and
                      ``content_type`` keys. The body contains a ``keys``
                      list of key metadata objects.
        """
        if not cls.is_endpoint_enabled("list"):
            error = AuthError(
                error=cls.ENDPOINT_DISABLED_ERROR_CODE,
                error_description="List keys endpoint is disabled"
            )
            response = cls.format_error(error, status_code=404)
            return response

        principal = cls.get_authenticated_principal(request)
        if principal is None:
            response = cls.authentication_required_response()
            return response

        keys = _run_async(cls.get_key_store().list_keys())

        # Only the caller's own keys are listed, and never key material
        sanitized_keys = []
        for key_record in keys:
            if key_record.get("owner") != principal.identifier:
                continue
            sanitized_keys.append(cls._to_public_record(key_record))

        response = {
            "status": 200,
            "body": {"keys": sanitized_keys},
            "content_type": cls.JSON_CONTENT_TYPE
        }
        return response

    @classmethod
    @SecurityBlueprint.read(
        path="{key_id}",
        response_schema=APIKeyResponse,
        doc=Doc(
            summary="Get API key details",
            description="Retrieve details about a specific API key. "
                        "The key value is not included."
        ),
        on_conflict="replace"
    )
    def get_key(cls, request: Any, key_id: Optional[str] = None) -> dict:
        """
            Get details for a specific API key.

            Returns metadata for the requested API key when the caller
            owns it. The raw key value is never included in get
            responses.

            The endpoint can be disabled via the ``enabled_endpoints``
            configuration. When disabled, a 404 response is returned.

            :param request: The incoming HTTP request object. The key
                            identifier is read from its ``key_id`` path
                            parameter.
            :param key_id: The unique identifier of the key to retrieve,
                           for callers that invoke the handler directly.

            :returns: A response dictionary with ``status``, ``body``, and
                      ``content_type`` keys.
        """
        if not cls.is_endpoint_enabled("get"):
            error = AuthError(
                error=cls.ENDPOINT_DISABLED_ERROR_CODE,
                error_description="Get key endpoint is disabled"
            )
            response = cls.format_error(error, status_code=404)
            return response

        principal = cls.get_authenticated_principal(request)
        if principal is None:
            response = cls.authentication_required_response()
            return response

        key_record = cls._get_owned_key(
            principal, cls._resolve_key_id(request, key_id)
        )

        if key_record is None:
            response = cls._key_not_found_response()
            return response

        # Ensure no key value is leaked in get responses
        response_body = cls._to_public_record(key_record)

        response = {
            "status": 200,
            "body": response_body,
            "content_type": cls.JSON_CONTENT_TYPE
        }
        return response

    @classmethod
    @SecurityBlueprint.delete(
        path="{key_id}",
        doc=Doc(
            summary="Revoke API key",
            description="Revoke an API key, making it immediately invalid."
        ),
        on_conflict="replace"
    )
    def revoke_key(cls, request: Any, key_id: Optional[str] = None) -> dict:
        """
            Revoke an API key.

            Marks the specified API key as revoked when the caller owns
            it, making it immediately invalid for authentication.

            The endpoint can be disabled via the ``enabled_endpoints``
            configuration. When disabled, a 404 response is returned.

            :param request: The incoming HTTP request object. The key
                            identifier is read from its ``key_id`` path
                            parameter.
            :param key_id: The unique identifier of the key to revoke,
                           for callers that invoke the handler directly.

            :returns: A response dictionary with ``status``, ``body``, and
                      ``content_type`` keys.
        """
        if not cls.is_endpoint_enabled("revoke"):
            error = AuthError(
                error=cls.ENDPOINT_DISABLED_ERROR_CODE,
                error_description="Revoke key endpoint is disabled"
            )
            response = cls.format_error(error, status_code=404)
            return response

        principal = cls.get_authenticated_principal(request)
        if principal is None:
            response = cls.authentication_required_response()
            return response

        key_record = cls._get_owned_key(
            principal, cls._resolve_key_id(request, key_id)
        )

        if key_record is None:
            response = cls._key_not_found_response()
            return response

        revoked = _run_async(
            cls.get_key_store().revoke_key(str(key_record.get("key_id")))
        )

        if not revoked:
            response = cls._key_not_found_response()
            return response

        response = {
            "status": 200,
            "body": {"message": cls.KEY_REVOKED_MESSAGE},
            "content_type": cls.JSON_CONTENT_TYPE
        }
        return response


def _accepts_owner(store_key: Any) -> bool:
    """
        Check that a store's ``store_key`` can record the key owner.

        :param store_key: The bound ``store_key`` method of a key store.

        :returns: True if it has an ``owner`` parameter or accepts
                  arbitrary keyword arguments.
    """
    try:
        parameters = inspect.signature(store_key).parameters
    except (TypeError, ValueError):
        return False

    if "owner" in parameters:
        return True

    for parameter in parameters.values():
        if parameter.kind == inspect.Parameter.VAR_KEYWORD:
            return True

    return False
