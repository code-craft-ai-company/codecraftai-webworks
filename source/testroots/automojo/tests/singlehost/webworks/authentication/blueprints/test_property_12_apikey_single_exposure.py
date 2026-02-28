"""
    Property test for API key single exposure.

    Property 12: API Key Single Exposure
        For any API key created via the create_key endpoint, the key value
        SHALL be present in the creation response and SHALL NOT be present
        in any subsequent get_key or list_keys responses.

    **Validates: Requirements 4.5**
"""

import random
import string

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


def _random_name(min_len=1, max_len=50):
    """
        Generate a random key name string.

        :param min_len: Minimum name length.
        :param max_len: Maximum name length.

        :returns: A random string suitable for use as a key name.
    """
    length = random.randint(min_len, max_len)
    chars = string.ascii_letters + string.digits + " -_"
    name = "".join(random.choice(chars) for _ in range(length))
    return name


def _random_scopes():
    """
        Generate a random list of scope strings.

        :returns: A list of 0 to 5 random scope strings.
    """
    num_scopes = random.randint(0, 5)
    scope_pool = [
        "read", "write", "admin", "delete", "read:users",
        "write:users", "read:data", "write:data", "manage",
        "audit", "export", "import",
    ]
    scopes = random.sample(scope_pool, min(num_scopes, len(scope_pool)))
    return scopes


def _random_expires_in():
    """
        Generate a random expiration value or None.

        :returns: An integer number of seconds, or None.
    """
    if random.random() < 0.3:
        return None
    return random.randint(60, 86400 * 365)


def _create_fresh_blueprint(use_store=False):
    """
        Create a fresh APIKeyBlueprint subclass to avoid class-level
        state leakage between iterations.

        :param use_store: If True, attach a MockAPIKeyStore.

        :returns: A tuple of (blueprint_class, store_or_None).
    """

    class FreshBlueprint(APIKeyBlueprint):
        pass

    FreshBlueprint.key_store = None
    FreshBlueprint.default_expiration = None
    FreshBlueprint.enabled_endpoints = None
    FreshBlueprint.auth_system = None
    FreshBlueprint.base_path = "/auth/keys"
    FreshBlueprint._memory_store = {}

    store = None
    if use_store:
        store = MockAPIKeyStore()
        FreshBlueprint.key_store = store

    return FreshBlueprint, store


# =============================================================================
# Property Tests
# =============================================================================

def test_property_12_apikey_single_exposure():
    """
        Property 12: API Key Single Exposure.

        For any API key created via the create_key endpoint, the key value
        SHALL be present in the creation response and SHALL NOT be present
        in any subsequent get_key or list_keys responses.

        For each iteration:
        1. Generate a random key name, scopes, and optional expiration.
        2. Randomly choose to use an in-memory store or a MockAPIKeyStore.
        3. Create a key via the create_key endpoint.
        4. Verify the creation response contains a non-empty ``key`` field.
        5. Call get_key with the returned key_id and verify the response
           does NOT contain a ``key`` field.
        6. Call list_keys and verify no record in the response contains
           a ``key`` field.

        **Validates: Requirements 4.5**
    """
    num_iterations = 100

    for iteration in range(num_iterations):
        name = _random_name()
        scopes = _random_scopes()
        expires_in = _random_expires_in()
        use_store = random.choice([True, False])

        blueprint, store = _create_fresh_blueprint(use_store=use_store)

        if expires_in is None and random.random() < 0.3:
            blueprint.default_expiration = random.randint(60, 86400)

        # Step 1: Create a key
        create_body = {"name": name, "scopes": scopes}
        if expires_in is not None:
            create_body["expires_in"] = expires_in

        create_request = MockJsonRequest(create_body)
        create_response = blueprint.create_key(create_request)

        if create_response["status"] != 201:
            errmsg = (
                "Iteration {}: Expected status 201 on create, got {}. "
                "name={!r}, use_store={}".format(
                    iteration, create_response["status"], name, use_store
                )
            )
            raise AssertionError(errmsg)

        create_body_resp = create_response["body"]

        # Step 2: Verify key value IS present in creation response
        if "key" not in create_body_resp:
            errmsg = (
                "Iteration {}: Creation response missing 'key' field. "
                "name={!r}".format(iteration, name)
            )
            raise AssertionError(errmsg)

        key_value = create_body_resp["key"]
        if not key_value or len(key_value) == 0:
            errmsg = (
                "Iteration {}: Creation response has empty key value. "
                "name={!r}".format(iteration, name)
            )
            raise AssertionError(errmsg)

        key_id = create_body_resp["key_id"]

        # Step 3: Verify key value is NOT present in get_key response
        get_request = MockJsonRequest({})
        get_response = blueprint.get_key(get_request, key_id)

        if get_response["status"] != 200:
            errmsg = (
                "Iteration {}: Expected status 200 on get_key, got {}. "
                "key_id={!r}".format(
                    iteration, get_response["status"], key_id
                )
            )
            raise AssertionError(errmsg)

        get_body = get_response["body"]

        if "key" in get_body:
            errmsg = (
                "Iteration {}: get_key response must NOT contain 'key' "
                "field. key_id={!r}, got key={!r}".format(
                    iteration, key_id, get_body.get("key")
                )
            )
            raise AssertionError(errmsg)

        # Step 4: Verify key value is NOT present in list_keys response
        list_request = MockJsonRequest({})
        list_response = blueprint.list_keys(list_request)

        if list_response["status"] != 200:
            errmsg = (
                "Iteration {}: Expected status 200 on list_keys, got {}".format(
                    iteration, list_response["status"]
                )
            )
            raise AssertionError(errmsg)

        list_body = list_response["body"]
        keys_list = list_body.get("keys", [])

        for idx, key_record in enumerate(keys_list):
            if "key" in key_record:
                errmsg = (
                    "Iteration {}: list_keys response record {} must NOT "
                    "contain 'key' field. key_id={!r}, got key={!r}".format(
                        iteration, idx,
                        key_record.get("key_id"),
                        key_record.get("key")
                    )
                )
                raise AssertionError(errmsg)

    return
