"""
    Unit tests for APIKeyBlueprint.

    This module verifies the APIKeyBlueprint endpoints including key
    creation, listing, retrieval, and revocation. It validates that
    key values are only returned on creation and never in subsequent
    list or get responses.

    **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7**
"""

from automojo.webworks.authentication.blueprints.apikey import (
    APIKeyBlueprint,
    APIKeyStore,
)


# =============================================================================
# Test Helpers
# =============================================================================


class MockJsonRequest:
    """
        A simple mock request that returns a JSON body dictionary.
    """

    def __init__(self, data):
        self._data = data

    def json(self):
        return self._data


class MockAPIKeyStore(APIKeyStore):
    """
        A mock API key store that stores keys in memory.
    """

    def __init__(self):
        self._keys = {}
        self._revoked = set()

    async def store_key(self, key_id, key_hash, name, scopes, created_at, expires_at):
        self._keys[key_id] = {
            "key_id": key_id,
            "key_hash": key_hash,
            "name": name,
            "scopes": scopes,
            "created_at": created_at,
            "expires_at": expires_at,
        }

    async def get_key(self, key_id):
        if key_id in self._revoked:
            return None
        record = self._keys.get(key_id)
        if record is None:
            return None
        # Return metadata without the key hash
        return {
            "key_id": record["key_id"],
            "name": record["name"],
            "scopes": record["scopes"],
            "created_at": record["created_at"],
            "expires_at": record["expires_at"],
        }

    async def list_keys(self):
        result = []
        for key_id, record in self._keys.items():
            if key_id not in self._revoked:
                result.append({
                    "key_id": record["key_id"],
                    "name": record["name"],
                    "scopes": record["scopes"],
                    "created_at": record["created_at"],
                    "expires_at": record["expires_at"],
                })
        return result

    async def revoke_key(self, key_id):
        if key_id in self._keys and key_id not in self._revoked:
            self._revoked.add(key_id)
            return True
        return False


def _create_fresh_blueprint():
    """
        Create a fresh APIKeyBlueprint subclass to avoid class-level
        state leakage between tests.
    """

    class FreshBlueprint(APIKeyBlueprint):
        pass

    FreshBlueprint.key_store = None
    FreshBlueprint.default_expiration = None
    FreshBlueprint.enabled_endpoints = None
    FreshBlueprint.auth_system = None
    FreshBlueprint.base_path = "/auth/keys"
    FreshBlueprint._memory_store = {}

    return FreshBlueprint


# =============================================================================
# Create Key Endpoint Tests (Requirement 4.1, 4.5)
# =============================================================================

def test_create_key_returns_key_value():
    """
        Verify that the create_key endpoint returns the key value in
        the creation response.

        **Validates: Requirements 4.1, 4.5**
    """
    blueprint = _create_fresh_blueprint()

    request = MockJsonRequest({
        "name": "My API Key",
        "scopes": ["read", "write"],
    })

    response = blueprint.create_key(request)

    if response["status"] != 201:
        errmsg = "Expected status 201, got {}".format(response["status"])
        raise AssertionError(errmsg)

    body = response["body"]

    if "key" not in body:
        errmsg = "Expected key field in creation response"
        raise AssertionError(errmsg)

    if not body["key"]:
        errmsg = "Expected non-empty key value in creation response"
        raise AssertionError(errmsg)

    if "key_id" not in body:
        errmsg = "Expected key_id field in creation response"
        raise AssertionError(errmsg)

    if body.get("name") != "My API Key":
        errmsg = "Expected name 'My API Key', got {!r}".format(body.get("name"))
        raise AssertionError(errmsg)

    if body.get("scopes") != ["read", "write"]:
        errmsg = "Expected scopes ['read', 'write'], got {!r}".format(
            body.get("scopes")
        )
        raise AssertionError(errmsg)

    return


def test_create_key_missing_name():
    """
        Verify that the create_key endpoint returns 400 when name is missing.

        **Validates: Requirements 4.1**
    """
    blueprint = _create_fresh_blueprint()

    request = MockJsonRequest({})

    response = blueprint.create_key(request)

    if response["status"] != 400:
        errmsg = "Expected status 400, got {}".format(response["status"])
        raise AssertionError(errmsg)

    body = response["body"]

    if body.get("error") != "invalid_request":
        errmsg = "Expected error 'invalid_request', got {!r}".format(
            body.get("error")
        )
        raise AssertionError(errmsg)

    return


def test_create_key_with_key_store():
    """
        Verify that the create_key endpoint stores the key via the key store.

        **Validates: Requirements 4.1**
    """
    store = MockAPIKeyStore()
    blueprint = _create_fresh_blueprint()
    blueprint.key_store = store

    request = MockJsonRequest({
        "name": "Stored Key",
        "scopes": ["admin"],
    })

    response = blueprint.create_key(request)

    if response["status"] != 201:
        errmsg = "Expected status 201, got {}".format(response["status"])
        raise AssertionError(errmsg)

    key_id = response["body"]["key_id"]

    if key_id not in store._keys:
        errmsg = "Expected key to be stored in key store"
        raise AssertionError(errmsg)

    return


def test_create_key_default_scopes():
    """
        Verify that the create_key endpoint defaults to empty scopes
        when none are provided.

        **Validates: Requirements 4.7**
    """
    blueprint = _create_fresh_blueprint()

    request = MockJsonRequest({
        "name": "No Scopes Key",
    })

    response = blueprint.create_key(request)

    if response["status"] != 201:
        errmsg = "Expected status 201, got {}".format(response["status"])
        raise AssertionError(errmsg)

    body = response["body"]

    if body.get("scopes") != []:
        errmsg = "Expected empty scopes list, got {!r}".format(
            body.get("scopes")
        )
        raise AssertionError(errmsg)

    return


# =============================================================================
# List Keys Endpoint Tests (Requirement 4.2, 4.5)
# =============================================================================

def test_list_keys_returns_keys_without_values():
    """
        Verify that the list_keys endpoint returns keys without the
        raw key value.

        **Validates: Requirements 4.2, 4.5**
    """
    blueprint = _create_fresh_blueprint()

    # Create a key first
    create_request = MockJsonRequest({
        "name": "List Test Key",
        "scopes": ["read"],
    })
    blueprint.create_key(create_request)

    # List keys
    list_request = MockJsonRequest({})
    response = blueprint.list_keys(list_request)

    if response["status"] != 200:
        errmsg = "Expected status 200, got {}".format(response["status"])
        raise AssertionError(errmsg)

    body = response["body"]
    keys = body.get("keys", [])

    if len(keys) != 1:
        errmsg = "Expected 1 key in list, got {}".format(len(keys))
        raise AssertionError(errmsg)

    key_record = keys[0]

    if "key" in key_record:
        errmsg = "Key value must NOT be present in list response"
        raise AssertionError(errmsg)

    if key_record.get("name") != "List Test Key":
        errmsg = "Expected name 'List Test Key', got {!r}".format(
            key_record.get("name")
        )
        raise AssertionError(errmsg)

    return


def test_list_keys_empty():
    """
        Verify that the list_keys endpoint returns an empty list when
        no keys exist.

        **Validates: Requirements 4.2**
    """
    blueprint = _create_fresh_blueprint()

    request = MockJsonRequest({})
    response = blueprint.list_keys(request)

    if response["status"] != 200:
        errmsg = "Expected status 200, got {}".format(response["status"])
        raise AssertionError(errmsg)

    body = response["body"]
    keys = body.get("keys", [])

    if len(keys) != 0:
        errmsg = "Expected 0 keys in list, got {}".format(len(keys))
        raise AssertionError(errmsg)

    return


# =============================================================================
# Get Key Endpoint Tests (Requirement 4.4, 4.5)
# =============================================================================

def test_get_key_returns_details_without_value():
    """
        Verify that the get_key endpoint returns key details without
        the raw key value.

        **Validates: Requirements 4.4, 4.5**
    """
    blueprint = _create_fresh_blueprint()

    # Create a key first
    create_request = MockJsonRequest({
        "name": "Get Test Key",
        "scopes": ["read", "write"],
    })
    create_response = blueprint.create_key(create_request)
    key_id = create_response["body"]["key_id"]

    # Get key details
    get_request = MockJsonRequest({})
    response = blueprint.get_key(get_request, key_id)

    if response["status"] != 200:
        errmsg = "Expected status 200, got {}".format(response["status"])
        raise AssertionError(errmsg)

    body = response["body"]

    if "key" in body:
        errmsg = "Key value must NOT be present in get response"
        raise AssertionError(errmsg)

    if body.get("key_id") != key_id:
        errmsg = "Expected key_id {!r}, got {!r}".format(
            key_id, body.get("key_id")
        )
        raise AssertionError(errmsg)

    if body.get("name") != "Get Test Key":
        errmsg = "Expected name 'Get Test Key', got {!r}".format(
            body.get("name")
        )
        raise AssertionError(errmsg)

    return


def test_get_key_not_found():
    """
        Verify that the get_key endpoint returns 404 for a non-existent key.

        **Validates: Requirements 4.4**
    """
    blueprint = _create_fresh_blueprint()

    request = MockJsonRequest({})
    response = blueprint.get_key(request, "nonexistent-key-id")

    if response["status"] != 404:
        errmsg = "Expected status 404, got {}".format(response["status"])
        raise AssertionError(errmsg)

    body = response["body"]

    if body.get("error") != "not_found":
        errmsg = "Expected error 'not_found', got {!r}".format(
            body.get("error")
        )
        raise AssertionError(errmsg)

    return


# =============================================================================
# Revoke Key Endpoint Tests (Requirement 4.3)
# =============================================================================

def test_revoke_key_success():
    """
        Verify that the revoke_key endpoint revokes an existing key.

        **Validates: Requirements 4.3**
    """
    blueprint = _create_fresh_blueprint()

    # Create a key first
    create_request = MockJsonRequest({
        "name": "Revoke Test Key",
    })
    create_response = blueprint.create_key(create_request)
    key_id = create_response["body"]["key_id"]

    # Revoke the key
    revoke_request = MockJsonRequest({})
    response = blueprint.revoke_key(revoke_request, key_id)

    if response["status"] != 200:
        errmsg = "Expected status 200, got {}".format(response["status"])
        raise AssertionError(errmsg)

    # Verify the key is no longer accessible
    get_request = MockJsonRequest({})
    get_response = blueprint.get_key(get_request, key_id)

    if get_response["status"] != 404:
        errmsg = "Expected revoked key to return 404, got {}".format(
            get_response["status"]
        )
        raise AssertionError(errmsg)

    return


def test_revoke_key_not_found():
    """
        Verify that the revoke_key endpoint returns 404 for a non-existent key.

        **Validates: Requirements 4.3**
    """
    blueprint = _create_fresh_blueprint()

    request = MockJsonRequest({})
    response = blueprint.revoke_key(request, "nonexistent-key-id")

    if response["status"] != 404:
        errmsg = "Expected status 404, got {}".format(response["status"])
        raise AssertionError(errmsg)

    return


def test_revoke_key_with_key_store():
    """
        Verify that the revoke_key endpoint revokes via the key store.

        **Validates: Requirements 4.3**
    """
    store = MockAPIKeyStore()
    blueprint = _create_fresh_blueprint()
    blueprint.key_store = store

    # Create a key first
    create_request = MockJsonRequest({
        "name": "Store Revoke Key",
    })
    create_response = blueprint.create_key(create_request)
    key_id = create_response["body"]["key_id"]

    # Revoke the key
    revoke_request = MockJsonRequest({})
    response = blueprint.revoke_key(revoke_request, key_id)

    if response["status"] != 200:
        errmsg = "Expected status 200, got {}".format(response["status"])
        raise AssertionError(errmsg)

    # Verify the key is revoked in the store
    if key_id not in store._revoked:
        errmsg = "Expected key to be revoked in key store"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Key Expiration Tests (Requirement 4.6)
# =============================================================================

def test_create_key_with_expiration():
    """
        Verify that the create_key endpoint supports configurable expiration.

        **Validates: Requirements 4.6**
    """
    blueprint = _create_fresh_blueprint()

    request = MockJsonRequest({
        "name": "Expiring Key",
        "expires_in": 3600,
    })

    response = blueprint.create_key(request)

    if response["status"] != 201:
        errmsg = "Expected status 201, got {}".format(response["status"])
        raise AssertionError(errmsg)

    body = response["body"]

    if body.get("expires_at") is None:
        errmsg = "Expected expires_at to be set when expires_in is provided"
        raise AssertionError(errmsg)

    return


def test_create_key_with_default_expiration():
    """
        Verify that the create_key endpoint uses default_expiration when
        no expires_in is provided in the request.

        **Validates: Requirements 4.6**
    """
    blueprint = _create_fresh_blueprint()
    blueprint.default_expiration = 7200

    request = MockJsonRequest({
        "name": "Default Expiry Key",
    })

    response = blueprint.create_key(request)

    if response["status"] != 201:
        errmsg = "Expected status 201, got {}".format(response["status"])
        raise AssertionError(errmsg)

    body = response["body"]

    if body.get("expires_at") is None:
        errmsg = "Expected expires_at to be set when default_expiration is configured"
        raise AssertionError(errmsg)

    return


def test_create_key_no_expiration():
    """
        Verify that the create_key endpoint returns no expiration when
        neither expires_in nor default_expiration is set.

        **Validates: Requirements 4.6**
    """
    blueprint = _create_fresh_blueprint()

    request = MockJsonRequest({
        "name": "No Expiry Key",
    })

    response = blueprint.create_key(request)

    if response["status"] != 201:
        errmsg = "Expected status 201, got {}".format(response["status"])
        raise AssertionError(errmsg)

    body = response["body"]

    if body.get("expires_at") is not None:
        errmsg = "Expected expires_at to be None when no expiration is configured"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Key Scoping Tests (Requirement 4.7)
# =============================================================================

def test_create_key_with_scopes():
    """
        Verify that the create_key endpoint supports key scoping with
        permissions.

        **Validates: Requirements 4.7**
    """
    blueprint = _create_fresh_blueprint()

    request = MockJsonRequest({
        "name": "Scoped Key",
        "scopes": ["read:users", "write:users", "admin"],
    })

    response = blueprint.create_key(request)

    if response["status"] != 201:
        errmsg = "Expected status 201, got {}".format(response["status"])
        raise AssertionError(errmsg)

    body = response["body"]

    expected_scopes = ["read:users", "write:users", "admin"]
    if body.get("scopes") != expected_scopes:
        errmsg = "Expected scopes {!r}, got {!r}".format(
            expected_scopes, body.get("scopes")
        )
        raise AssertionError(errmsg)

    return


# =============================================================================
# Endpoint Enable/Disable Tests
# =============================================================================

def test_disabled_create_endpoint():
    """
        Verify that the create_key endpoint returns 404 when disabled.
    """
    blueprint = _create_fresh_blueprint()
    blueprint.enabled_endpoints = {"list", "get", "revoke"}

    request = MockJsonRequest({
        "name": "Disabled Create",
    })

    response = blueprint.create_key(request)

    if response["status"] != 404:
        errmsg = "Expected status 404 for disabled endpoint, got {}".format(
            response["status"]
        )
        raise AssertionError(errmsg)

    return


def test_disabled_list_endpoint():
    """
        Verify that the list_keys endpoint returns 404 when disabled.
    """
    blueprint = _create_fresh_blueprint()
    blueprint.enabled_endpoints = {"create", "get", "revoke"}

    request = MockJsonRequest({})

    response = blueprint.list_keys(request)

    if response["status"] != 404:
        errmsg = "Expected status 404 for disabled endpoint, got {}".format(
            response["status"]
        )
        raise AssertionError(errmsg)

    return


def test_pre_authenticate_hook_blocks_create():
    """
        Verify that the pre_authenticate hook can block key creation.
    """
    from automojo.webworks.authentication.blueprints.responses import AuthError

    class HookBlueprint(APIKeyBlueprint):
        pass

    HookBlueprint.key_store = None
    HookBlueprint.default_expiration = None
    HookBlueprint.enabled_endpoints = None
    HookBlueprint.auth_system = None
    HookBlueprint.base_path = "/auth/keys"
    HookBlueprint._memory_store = {}

    @classmethod
    def blocking_pre_auth(cls, request):
        return AuthError(
            error="rate_limited",
            error_description="Too many requests"
        )

    HookBlueprint.pre_authenticate = blocking_pre_auth

    request = MockJsonRequest({
        "name": "Blocked Key",
    })

    response = HookBlueprint.create_key(request)

    if response["status"] != 401:
        errmsg = "Expected status 401 from pre_authenticate hook, got {}".format(
            response["status"]
        )
        raise AssertionError(errmsg)

    body = response["body"]

    if body.get("error") != "rate_limited":
        errmsg = "Expected error 'rate_limited', got {!r}".format(
            body.get("error")
        )
        raise AssertionError(errmsg)

    return
