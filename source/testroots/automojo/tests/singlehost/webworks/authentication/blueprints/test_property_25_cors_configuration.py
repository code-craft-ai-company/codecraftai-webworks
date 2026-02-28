"""
    Property test for CORS header configuration.

    This module verifies Property 25: CORS Header Configuration.

    For any Security_Blueprint with configured cors_origins, responses
    SHALL include appropriate CORS headers for those origins.

    **Validates: Requirements 10.6**
"""

import random
import string

from automojo.webworks.authentication.blueprints.security import SecurityBlueprint
from automojo.webworks.authentication.blueprints.basic import BasicAuthBlueprint
from automojo.webworks.authentication.blueprints.bearer import BearerAuthBlueprint
from automojo.webworks.authentication.blueprints.apikey import APIKeyBlueprint
from automojo.webworks.authentication.blueprints.session import SessionAuthBlueprint
from automojo.webworks.authentication.blueprints.oauth2 import OAuth2Blueprint
from automojo.webworks.authentication.blueprints.oidc import OIDCBlueprint


# =============================================================================
# Blueprint classes under test
# =============================================================================

ALL_BLUEPRINT_CLASSES = [
    BasicAuthBlueprint,
    BearerAuthBlueprint,
    APIKeyBlueprint,
    SessionAuthBlueprint,
    OAuth2Blueprint,
    OIDCBlueprint,
]


# =============================================================================
# Test Helpers
# =============================================================================

def _cleanup_blueprint(blueprint_cls):
    """
        Remove cors_origins from a blueprint class to prevent state leaks.
    """
    blueprint_cls.cors_origins = None
    return


def _random_origin():
    """
        Generate a random origin URL.
    """
    domain = "".join(random.choices(string.ascii_lowercase, k=random.randint(4, 10)))
    tld = random.choice(["com", "org", "net", "io", "dev"])
    scheme = random.choice(["https", "http"])
    port = random.choice(["", ":3000", ":8080", ":443"])
    origin = "{}://{}.{}{}".format(scheme, domain, tld, port)
    return origin



# =============================================================================
# Property Tests
# =============================================================================

def test_property_25_cors_headers_for_allowed_origin():
    """
        Property 25: CORS Header Configuration - allowed origins.

        For any Security_Blueprint with configured cors_origins, when
        a request arrives from an allowed origin, the response SHALL
        include Access-Control-Allow-Origin matching that origin.

        **Validates: Requirements 10.6**
    """
    num_iterations = 100

    for iteration in range(num_iterations):
        blueprint_cls = random.choice(ALL_BLUEPRINT_CLASSES)
        num_origins = random.randint(1, 5)
        allowed_origins = [_random_origin() for _ in range(num_origins)]
        request_origin = random.choice(allowed_origins)

        try:
            blueprint_cls.cors_origins = allowed_origins
            headers = blueprint_cls.get_cors_headers(origin=request_origin)

            if "Access-Control-Allow-Origin" not in headers:
                errmsg = (
                    "Iteration {}: {}: Missing Access-Control-Allow-Origin "
                    "header for allowed origin '{}'.".format(
                        iteration, blueprint_cls.__name__, request_origin
                    )
                )
                raise AssertionError(errmsg)

            if headers["Access-Control-Allow-Origin"] != request_origin:
                errmsg = (
                    "Iteration {}: {}: Access-Control-Allow-Origin is "
                    "'{}', expected '{}'.".format(
                        iteration, blueprint_cls.__name__,
                        headers["Access-Control-Allow-Origin"], request_origin
                    )
                )
                raise AssertionError(errmsg)

            # Verify other required CORS headers are present
            for required_header in (
                "Access-Control-Allow-Methods",
                "Access-Control-Allow-Headers",
            ):
                if required_header not in headers:
                    errmsg = (
                        "Iteration {}: {}: Missing required CORS header "
                        "'{}'.".format(
                            iteration, blueprint_cls.__name__, required_header
                        )
                    )
                    raise AssertionError(errmsg)
        finally:
            _cleanup_blueprint(blueprint_cls)

    return


def test_property_25_cors_headers_rejected_for_disallowed_origin():
    """
        Property 25: CORS Header Configuration - disallowed origins.

        For any Security_Blueprint with configured cors_origins, when
        a request arrives from an origin NOT in the allowed list, the
        response SHALL NOT include CORS headers.

        **Validates: Requirements 10.6**
    """
    num_iterations = 100

    for iteration in range(num_iterations):
        blueprint_cls = random.choice(ALL_BLUEPRINT_CLASSES)
        allowed_origins = [_random_origin() for _ in range(random.randint(1, 3))]

        # Generate a disallowed origin that is not in the list
        disallowed_origin = _random_origin()
        while disallowed_origin in allowed_origins:
            disallowed_origin = _random_origin()

        try:
            blueprint_cls.cors_origins = allowed_origins
            headers = blueprint_cls.get_cors_headers(origin=disallowed_origin)

            if len(headers) != 0:
                errmsg = (
                    "Iteration {}: {}: CORS headers returned for "
                    "disallowed origin '{}'. Headers: {}".format(
                        iteration, blueprint_cls.__name__,
                        disallowed_origin, headers
                    )
                )
                raise AssertionError(errmsg)
        finally:
            _cleanup_blueprint(blueprint_cls)

    return


def test_property_25_cors_wildcard_allows_any_origin():
    """
        Property 25: CORS Header Configuration - wildcard origin.

        For any Security_Blueprint with cors_origins containing '*',
        any origin SHALL be allowed and Access-Control-Allow-Origin
        SHALL be set to '*'.

        **Validates: Requirements 10.6**
    """
    num_iterations = 100

    for iteration in range(num_iterations):
        blueprint_cls = random.choice(ALL_BLUEPRINT_CLASSES)
        request_origin = _random_origin()

        try:
            blueprint_cls.cors_origins = ["*"]
            headers = blueprint_cls.get_cors_headers(origin=request_origin)

            if "Access-Control-Allow-Origin" not in headers:
                errmsg = (
                    "Iteration {}: {}: Missing Access-Control-Allow-Origin "
                    "for wildcard CORS with origin '{}'.".format(
                        iteration, blueprint_cls.__name__, request_origin
                    )
                )
                raise AssertionError(errmsg)

            if headers["Access-Control-Allow-Origin"] != "*":
                errmsg = (
                    "Iteration {}: {}: Access-Control-Allow-Origin is "
                    "'{}', expected '*' for wildcard config.".format(
                        iteration, blueprint_cls.__name__,
                        headers["Access-Control-Allow-Origin"]
                    )
                )
                raise AssertionError(errmsg)
        finally:
            _cleanup_blueprint(blueprint_cls)

    return


def test_property_25_no_cors_headers_when_not_configured():
    """
        Property 25: CORS Header Configuration - unconfigured.

        For any Security_Blueprint without cors_origins configured,
        get_cors_headers SHALL return an empty dictionary.

        **Validates: Requirements 10.6**
    """
    num_iterations = 100

    for iteration in range(num_iterations):
        blueprint_cls = random.choice(ALL_BLUEPRINT_CLASSES)
        request_origin = _random_origin()

        try:
            blueprint_cls.cors_origins = None
            headers = blueprint_cls.get_cors_headers(origin=request_origin)

            if len(headers) != 0:
                errmsg = (
                    "Iteration {}: {}: CORS headers returned when "
                    "cors_origins is None. Headers: {}".format(
                        iteration, blueprint_cls.__name__, headers
                    )
                )
                raise AssertionError(errmsg)
        finally:
            _cleanup_blueprint(blueprint_cls)

    return


def test_property_25_cors_configure_method():
    """
        Property 25: CORS Header Configuration - configure method.

        When configure() is called with cors_origins, the blueprint
        SHALL use those origins for CORS header generation.

        **Validates: Requirements 10.6**
    """
    num_iterations = 100

    for iteration in range(num_iterations):
        blueprint_cls = random.choice(ALL_BLUEPRINT_CLASSES)
        allowed_origins = [_random_origin() for _ in range(random.randint(1, 4))]
        request_origin = random.choice(allowed_origins)

        try:
            blueprint_cls.configure(
                auth_system=None,
                cors_origins=allowed_origins,
            )

            headers = blueprint_cls.get_cors_headers(origin=request_origin)

            if "Access-Control-Allow-Origin" not in headers:
                errmsg = (
                    "Iteration {}: {}: Missing Access-Control-Allow-Origin "
                    "after configure(cors_origins=...) for origin "
                    "'{}'.".format(
                        iteration, blueprint_cls.__name__, request_origin
                    )
                )
                raise AssertionError(errmsg)
        finally:
            _cleanup_blueprint(blueprint_cls)
            blueprint_cls.auth_system = None

    return
