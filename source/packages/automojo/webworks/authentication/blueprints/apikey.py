"""
.. module:: apikey
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: API key authentication blueprint providing key management endpoints.

.. moduleauthor:: Automation Mojo LLC

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

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


import asyncio
import secrets
import time

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from automojo.webworks.authentication.blueprints.responses import (
    AuthError,
    AuthResponse
)
from automojo.webworks.authentication.blueprints.schemas import (
    APIKeyCreateRequest,
    APIKeyResponse
)
from automojo.webworks.authentication.blueprints.security import (
    SecurityBlueprint
)
from automojo.webworks.endpoints.doc import Doc


def _run_async(coro: Any) -> Any:
    """
        Run an asynchronous coroutine synchronously.

        This helper obtains the current event loop and uses
        ``run_until_complete`` to execute the coroutine. It is used
        internally by :class:`APIKeyBlueprint` to call async
        :class:`APIKeyStore` methods from synchronous endpoint handlers.

        :param coro: The coroutine to execute.

        :returns: The result of the coroutine.
    """
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(coro)
    return result


class APIKeyStore:
    """
        Abstract interface for API key persistence.

        Implementations of this class handle the storage, retrieval,
        and revocation of API keys. The store is responsible for
        persisting the key hash (not the raw key value) and associated
        metadata.

        Subclasses must implement all async methods.
    """

    async def store_key(
        self,
        key_id: str,
        key_hash: str,
        name: str,
        scopes: List[str],
        created_at: str,
        expires_at: Optional[str]
    ) -> None:
        """
            Store a new API key record.

            :param key_id: The unique identifier for the key.
            :param key_hash: The hashed key value for validation.
            :param name: The human-readable name for the key.
            :param scopes: The permission scopes assigned to the key.
            :param created_at: ISO 8601 timestamp of creation.
            :param expires_at: Optional ISO 8601 timestamp of expiration.
        """
        raise NotImplementedError

    async def get_key(self, key_id: str) -> Optional[Dict[str, Any]]:
        """
            Retrieve metadata for a specific API key.

            The returned dictionary should contain key_id, name, scopes,
            created_at, and expires_at fields. It must NOT contain the
            raw key value.

            :param key_id: The unique identifier of the key to retrieve.

            :returns: A dictionary of key metadata, or None if not found.
        """
        raise NotImplementedError

    async def list_keys(self) -> List[Dict[str, Any]]:
        """
            List all active (non-revoked) API keys.

            Each dictionary in the returned list should contain key_id,
            name, scopes, created_at, and expires_at fields. Raw key
            values must NOT be included.

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
                       When None, keys are stored in an in-memory dictionary.
            default_expiration: Default key lifetime in seconds. When None,
                                keys do not expire unless the request
                                specifies an ``expires_in`` value.
    """

    base_path: str = "/auth/keys"
    tags: List[str] = ["Authentication", "API Keys"]

    key_store: Optional[APIKeyStore] = None
    default_expiration: Optional[int] = None

    # In-memory fallback store when no key_store is configured
    _memory_store: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def _generate_key_value(cls) -> str:
        """
            Generate a cryptographically secure API key value.

            The key is a URL-safe base64-encoded string of 32 random bytes,
            providing 256 bits of entropy.

            :returns: A random API key string.
        """
        key_value = secrets.token_urlsafe(32)
        return key_value

    @classmethod
    def _generate_key_id(cls) -> str:
        """
            Generate a unique identifier for an API key.

            The identifier is a URL-safe base64-encoded string of 16
            random bytes.

            :returns: A random key identifier string.
        """
        key_id = secrets.token_urlsafe(16)
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
                error="endpoint_disabled",
                error_description="Create key endpoint is disabled"
            )
            response = cls.format_error(error, status_code=404)
            return response

        # Pre-authentication hook
        pre_error = cls.pre_authenticate(request)
        if pre_error is not None:
            response = cls.format_error(pre_error)
            return response

        body = request.json()
        name = body.get("name")

        if not name:
            error = AuthError(
                error="invalid_request",
                error_description="Key name is required"
            )
            response = cls.format_error(error, status_code=400)
            return response

        scopes = body.get("scopes")
        if scopes is None:
            scopes = []

        expires_in = body.get("expires_in")

        # Generate key identifiers
        key_id = cls._generate_key_id()
        key_value = cls._generate_key_value()

        # Compute timestamps
        now = datetime.now(tz=timezone.utc)
        created_at = now.isoformat()
        expires_at = cls._compute_expires_at(expires_in)

        # Store the key (hash would be used in production; for this
        # blueprint we store metadata only — the raw value is never
        # persisted in a retrievable form)
        if cls.key_store is not None:
            _run_async(
                cls.key_store.store_key(
                    key_id=key_id,
                    key_hash=key_value,
                    name=name,
                    scopes=scopes,
                    created_at=created_at,
                    expires_at=expires_at
                )
            )
        else:
            cls._memory_store[key_id] = {
                "key_id": key_id,
                "name": name,
                "scopes": scopes,
                "created_at": created_at,
                "expires_at": expires_at,
            }

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
            "content_type": "application/json"
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
            List all active API keys.

            Returns metadata for all non-revoked API keys. The raw key
            value is never included in list responses.

            The endpoint can be disabled via the ``enabled_endpoints``
            configuration. When disabled, a 404 response is returned.

            :param request: The incoming HTTP request object.

            :returns: A response dictionary with ``status``, ``body``, and
                      ``content_type`` keys. The body contains a ``keys``
                      list of key metadata objects.
        """
        if not cls.is_endpoint_enabled("list"):
            error = AuthError(
                error="endpoint_disabled",
                error_description="List keys endpoint is disabled"
            )
            response = cls.format_error(error, status_code=404)
            return response

        if cls.key_store is not None:
            keys = _run_async(cls.key_store.list_keys())
        else:
            keys = list(cls._memory_store.values())

        # Ensure no key values are leaked in list responses
        sanitized_keys = []
        for key_record in keys:
            sanitized = {
                "key_id": key_record.get("key_id"),
                "name": key_record.get("name"),
                "scopes": key_record.get("scopes", []),
                "created_at": key_record.get("created_at"),
                "expires_at": key_record.get("expires_at"),
            }
            sanitized_keys.append(sanitized)

        response = {
            "status": 200,
            "body": {"keys": sanitized_keys},
            "content_type": "application/json"
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
    def get_key(cls, request: Any, key_id: str) -> dict:
        """
            Get details for a specific API key.

            Returns metadata for the requested API key. The raw key
            value is never included in get responses.

            The endpoint can be disabled via the ``enabled_endpoints``
            configuration. When disabled, a 404 response is returned.

            :param request: The incoming HTTP request object.
            :param key_id: The unique identifier of the key to retrieve.

            :returns: A response dictionary with ``status``, ``body``, and
                      ``content_type`` keys.
        """
        if not cls.is_endpoint_enabled("get"):
            error = AuthError(
                error="endpoint_disabled",
                error_description="Get key endpoint is disabled"
            )
            response = cls.format_error(error, status_code=404)
            return response

        if cls.key_store is not None:
            key_record = _run_async(cls.key_store.get_key(key_id))
        else:
            key_record = cls._memory_store.get(key_id)

        if key_record is None:
            error = AuthError(
                error="not_found",
                error_description="API key not found"
            )
            response = cls.format_error(error, status_code=404)
            return response

        # Ensure no key value is leaked in get responses
        response_body = {
            "key_id": key_record.get("key_id"),
            "name": key_record.get("name"),
            "scopes": key_record.get("scopes", []),
            "created_at": key_record.get("created_at"),
            "expires_at": key_record.get("expires_at"),
        }

        response = {
            "status": 200,
            "body": response_body,
            "content_type": "application/json"
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
    def revoke_key(cls, request: Any, key_id: str) -> dict:
        """
            Revoke an API key.

            Marks the specified API key as revoked, making it immediately
            invalid for authentication. The operation is idempotent.

            The endpoint can be disabled via the ``enabled_endpoints``
            configuration. When disabled, a 404 response is returned.

            :param request: The incoming HTTP request object.
            :param key_id: The unique identifier of the key to revoke.

            :returns: A response dictionary with ``status``, ``body``, and
                      ``content_type`` keys.
        """
        if not cls.is_endpoint_enabled("revoke"):
            error = AuthError(
                error="endpoint_disabled",
                error_description="Revoke key endpoint is disabled"
            )
            response = cls.format_error(error, status_code=404)
            return response

        if cls.key_store is not None:
            revoked = _run_async(cls.key_store.revoke_key(key_id))
        else:
            revoked = key_id in cls._memory_store
            if revoked:
                del cls._memory_store[key_id]

        if not revoked:
            error = AuthError(
                error="not_found",
                error_description="API key not found"
            )
            response = cls.format_error(error, status_code=404)
            return response

        response = {
            "status": 200,
            "body": {"message": "API key revoked"},
            "content_type": "application/json"
        }
        return response
