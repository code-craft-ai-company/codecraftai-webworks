"""
    Tests for the OpenAPI security scheme dataclasses module.

    This module contains unit tests for the SecurityScheme, APIKeySecurityScheme,
    HTTPSecurityScheme, OAuth2SecurityScheme, OAuthFlows, and OAuthFlow dataclasses.
"""

from automojo.webworks.openapi.securityschemes import (
    APIKeySecurityScheme,
    HTTPSecurityScheme,
    OAuth2SecurityScheme,
    OAuthFlow,
    OAuthFlows,
    SecurityScheme,
)


# =============================================================================
# Unit Tests for OAuthFlow
# =============================================================================

def test_oauth_flow_creation_with_all_fields():
    """
        Test that OAuthFlow can be created with all fields populated.
    """
    scopes = {"read": "Read access", "write": "Write access"}
    flow = OAuthFlow(
        scopes=scopes,
        authorization_url="https://example.com/auth",
        token_url="https://example.com/token",
        refresh_url="https://example.com/refresh"
    )

    if flow.scopes != scopes:
        errmsg = f"Expected scopes {scopes!r}, got {flow.scopes!r}"
        raise AssertionError(errmsg)

    if flow.authorization_url != "https://example.com/auth":
        errmsg = f"Expected authorization_url 'https://example.com/auth', got {flow.authorization_url!r}"
        raise AssertionError(errmsg)

    if flow.token_url != "https://example.com/token":
        errmsg = f"Expected token_url 'https://example.com/token', got {flow.token_url!r}"
        raise AssertionError(errmsg)

    if flow.refresh_url != "https://example.com/refresh":
        errmsg = f"Expected refresh_url 'https://example.com/refresh', got {flow.refresh_url!r}"
        raise AssertionError(errmsg)

    return


def test_oauth_flow_defaults():
    """
        Test that OAuthFlow URL fields default to None and scopes defaults to empty dict.
    """
    flow = OAuthFlow()

    if len(flow.scopes) != 0:
        errmsg = f"Expected empty scopes dict, got {flow.scopes!r}"
        raise AssertionError(errmsg)

    if flow.authorization_url is not None:
        errmsg = f"Expected authorization_url to be None, got {flow.authorization_url!r}"
        raise AssertionError(errmsg)

    if flow.token_url is not None:
        errmsg = f"Expected token_url to be None, got {flow.token_url!r}"
        raise AssertionError(errmsg)

    if flow.refresh_url is not None:
        errmsg = f"Expected refresh_url to be None, got {flow.refresh_url!r}"
        raise AssertionError(errmsg)

    return


def test_oauth_flow_to_dict_all_fields():
    """
        Test that OAuthFlow.to_dict() includes all populated fields with camelCase keys.
    """
    scopes = {"read": "Read access"}
    flow = OAuthFlow(
        scopes=scopes,
        authorization_url="https://example.com/auth",
        token_url="https://example.com/token",
        refresh_url="https://example.com/refresh"
    )
    result = flow.to_dict()

    expected = {
        "scopes": {"read": "Read access"},
        "authorizationUrl": "https://example.com/auth",
        "tokenUrl": "https://example.com/token",
        "refreshUrl": "https://example.com/refresh"
    }

    if result != expected:
        errmsg = f"Expected {expected}, got {result}"
        raise AssertionError(errmsg)

    return


def test_oauth_flow_to_dict_scopes_only():
    """
        Test that OAuthFlow.to_dict() only includes scopes when URLs are None.
    """
    scopes = {"admin": "Admin access"}
    flow = OAuthFlow(scopes=scopes)
    result = flow.to_dict()

    expected = {"scopes": {"admin": "Admin access"}}

    if result != expected:
        errmsg = f"Expected {expected}, got {result}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for OAuthFlows
# =============================================================================

def test_oauth_flows_creation_with_all_flow_types():
    """
        Test that OAuthFlows can be created with all flow types populated.
    """
    implicit_flow = OAuthFlow(scopes={"read": "Read"}, authorization_url="https://example.com/auth")
    password_flow = OAuthFlow(scopes={"write": "Write"}, token_url="https://example.com/token")
    client_creds_flow = OAuthFlow(scopes={"admin": "Admin"}, token_url="https://example.com/token")
    auth_code_flow = OAuthFlow(
        scopes={"read": "Read"},
        authorization_url="https://example.com/auth",
        token_url="https://example.com/token"
    )

    flows = OAuthFlows(
        implicit=implicit_flow,
        password=password_flow,
        client_credentials=client_creds_flow,
        authorization_code=auth_code_flow
    )

    if flows.implicit is not implicit_flow:
        errmsg = "Expected implicit flow to match the provided flow instance"
        raise AssertionError(errmsg)

    if flows.password is not password_flow:
        errmsg = "Expected password flow to match the provided flow instance"
        raise AssertionError(errmsg)

    if flows.client_credentials is not client_creds_flow:
        errmsg = "Expected client_credentials flow to match the provided flow instance"
        raise AssertionError(errmsg)

    if flows.authorization_code is not auth_code_flow:
        errmsg = "Expected authorization_code flow to match the provided flow instance"
        raise AssertionError(errmsg)

    return


def test_oauth_flows_defaults_to_none():
    """
        Test that OAuthFlows fields default to None.
    """
    flows = OAuthFlows()

    if flows.implicit is not None:
        errmsg = f"Expected implicit to be None, got {flows.implicit!r}"
        raise AssertionError(errmsg)

    if flows.password is not None:
        errmsg = f"Expected password to be None, got {flows.password!r}"
        raise AssertionError(errmsg)

    if flows.client_credentials is not None:
        errmsg = f"Expected client_credentials to be None, got {flows.client_credentials!r}"
        raise AssertionError(errmsg)

    if flows.authorization_code is not None:
        errmsg = f"Expected authorization_code to be None, got {flows.authorization_code!r}"
        raise AssertionError(errmsg)

    return


def test_oauth_flows_to_dict_all_flow_types():
    """
        Test that OAuthFlows.to_dict() includes all populated flow types with correct keys.
    """
    implicit_flow = OAuthFlow(scopes={"read": "Read"}, authorization_url="https://example.com/auth")
    client_creds_flow = OAuthFlow(scopes={"admin": "Admin"}, token_url="https://example.com/token")

    flows = OAuthFlows(implicit=implicit_flow, client_credentials=client_creds_flow)
    result = flows.to_dict()

    if "implicit" not in result:
        errmsg = f"Expected 'implicit' key in result, got keys: {list(result.keys())}"
        raise AssertionError(errmsg)

    if "clientCredentials" not in result:
        errmsg = f"Expected 'clientCredentials' key in result, got keys: {list(result.keys())}"
        raise AssertionError(errmsg)

    if len(result) != 2:
        errmsg = f"Expected 2 keys in result, got {len(result)}: {list(result.keys())}"
        raise AssertionError(errmsg)

    return


def test_oauth_flows_to_dict_empty():
    """
        Test that OAuthFlows.to_dict() returns empty dict when no flows are set.
    """
    flows = OAuthFlows()
    result = flows.to_dict()

    if len(result) != 0:
        errmsg = f"Expected empty dict, got {result}"
        raise AssertionError(errmsg)

    return


def test_oauth_flows_to_dict_camel_case_keys():
    """
        Test that OAuthFlows.to_dict() uses camelCase for client_credentials and authorization_code.
    """
    client_creds_flow = OAuthFlow(scopes={"admin": "Admin"}, token_url="https://example.com/token")
    auth_code_flow = OAuthFlow(
        scopes={"read": "Read"},
        authorization_url="https://example.com/auth",
        token_url="https://example.com/token"
    )

    flows = OAuthFlows(client_credentials=client_creds_flow, authorization_code=auth_code_flow)
    result = flows.to_dict()

    if "clientCredentials" not in result:
        errmsg = f"Expected 'clientCredentials' key (camelCase), got keys: {list(result.keys())}"
        raise AssertionError(errmsg)

    if "authorizationCode" not in result:
        errmsg = f"Expected 'authorizationCode' key (camelCase), got keys: {list(result.keys())}"
        raise AssertionError(errmsg)

    if "client_credentials" in result:
        errmsg = "Found snake_case key 'client_credentials' instead of camelCase 'clientCredentials'"
        raise AssertionError(errmsg)

    if "authorization_code" in result:
        errmsg = "Found snake_case key 'authorization_code' instead of camelCase 'authorizationCode'"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for SecurityScheme
# =============================================================================

def test_security_scheme_creation():
    """
        Test that SecurityScheme can be created with type and description.
    """
    scheme = SecurityScheme(type="apiKey", description="API key authentication")

    if scheme.type != "apiKey":
        errmsg = f"Expected type 'apiKey', got {scheme.type!r}"
        raise AssertionError(errmsg)

    if scheme.description != "API key authentication":
        errmsg = f"Expected description 'API key authentication', got {scheme.description!r}"
        raise AssertionError(errmsg)

    return


def test_security_scheme_description_defaults_to_none():
    """
        Test that SecurityScheme description defaults to None.
    """
    scheme = SecurityScheme(type="http")

    if scheme.description is not None:
        errmsg = f"Expected description to be None, got {scheme.description!r}"
        raise AssertionError(errmsg)

    return


def test_security_scheme_to_dict_with_description():
    """
        Test that SecurityScheme.to_dict() includes type and description.
    """
    scheme = SecurityScheme(type="apiKey", description="Key-based auth")
    result = scheme.to_dict()

    expected = {"type": "apiKey", "description": "Key-based auth"}

    if result != expected:
        errmsg = f"Expected {expected}, got {result}"
        raise AssertionError(errmsg)

    return


def test_security_scheme_to_dict_without_description():
    """
        Test that SecurityScheme.to_dict() omits description when None.
    """
    scheme = SecurityScheme(type="http")
    result = scheme.to_dict()

    expected = {"type": "http"}

    if result != expected:
        errmsg = f"Expected {expected}, got {result}"
        raise AssertionError(errmsg)

    if "description" in result:
        errmsg = "Expected 'description' key to be absent when description is None"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for APIKeySecurityScheme
# =============================================================================

def test_api_key_scheme_defaults():
    """
        Test that APIKeySecurityScheme has correct default values.
    """
    scheme = APIKeySecurityScheme()

    if scheme.type != "apiKey":
        errmsg = f"Expected type 'apiKey', got {scheme.type!r}"
        raise AssertionError(errmsg)

    if scheme.name != "X-API-Key":
        errmsg = f"Expected name 'X-API-Key', got {scheme.name!r}"
        raise AssertionError(errmsg)

    if scheme.in_ != "header":
        errmsg = f"Expected in_ 'header', got {scheme.in_!r}"
        raise AssertionError(errmsg)

    if scheme.description is not None:
        errmsg = f"Expected description to be None, got {scheme.description!r}"
        raise AssertionError(errmsg)

    return


def test_api_key_scheme_custom_values():
    """
        Test that APIKeySecurityScheme can be created with custom values.
    """
    scheme = APIKeySecurityScheme(
        name="api_key",
        in_="query",
        description="Query parameter API key"
    )

    if scheme.name != "api_key":
        errmsg = f"Expected name 'api_key', got {scheme.name!r}"
        raise AssertionError(errmsg)

    if scheme.in_ != "query":
        errmsg = f"Expected in_ 'query', got {scheme.in_!r}"
        raise AssertionError(errmsg)

    if scheme.description != "Query parameter API key":
        errmsg = f"Expected description 'Query parameter API key', got {scheme.description!r}"
        raise AssertionError(errmsg)

    return


def test_api_key_scheme_to_dict_defaults():
    """
        Test that APIKeySecurityScheme.to_dict() includes type, name, and in fields.
    """
    scheme = APIKeySecurityScheme()
    result = scheme.to_dict()

    expected = {
        "type": "apiKey",
        "name": "X-API-Key",
        "in": "header"
    }

    if result != expected:
        errmsg = f"Expected {expected}, got {result}"
        raise AssertionError(errmsg)

    return


def test_api_key_scheme_to_dict_with_description():
    """
        Test that APIKeySecurityScheme.to_dict() includes description when set.
    """
    scheme = APIKeySecurityScheme(description="API key in cookie")
    result = scheme.to_dict()

    if "description" not in result:
        errmsg = f"Expected 'description' key in result, got keys: {list(result.keys())}"
        raise AssertionError(errmsg)

    if result["description"] != "API key in cookie":
        errmsg = f"Expected description 'API key in cookie', got {result['description']!r}"
        raise AssertionError(errmsg)

    return


def test_api_key_scheme_to_dict_uses_in_not_in_underscore():
    """
        Test that APIKeySecurityScheme.to_dict() serializes in_ as 'in' per OpenAPI spec.
    """
    scheme = APIKeySecurityScheme(in_="cookie")
    result = scheme.to_dict()

    if "in" not in result:
        errmsg = f"Expected 'in' key in result, got keys: {list(result.keys())}"
        raise AssertionError(errmsg)

    if "in_" in result:
        errmsg = "Found 'in_' key instead of 'in' in result"
        raise AssertionError(errmsg)

    if result["in"] != "cookie":
        errmsg = f"Expected in value 'cookie', got {result['in']!r}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for HTTPSecurityScheme
# =============================================================================

def test_http_scheme_defaults():
    """
        Test that HTTPSecurityScheme has correct default values.
    """
    scheme = HTTPSecurityScheme()

    if scheme.type != "http":
        errmsg = f"Expected type 'http', got {scheme.type!r}"
        raise AssertionError(errmsg)

    if scheme.scheme != "bearer":
        errmsg = f"Expected scheme 'bearer', got {scheme.scheme!r}"
        raise AssertionError(errmsg)

    if scheme.bearer_format is not None:
        errmsg = f"Expected bearer_format to be None, got {scheme.bearer_format!r}"
        raise AssertionError(errmsg)

    return


def test_http_scheme_basic_auth():
    """
        Test that HTTPSecurityScheme can be configured for basic authentication.
    """
    scheme = HTTPSecurityScheme(scheme="basic", description="Basic authentication")

    if scheme.scheme != "basic":
        errmsg = f"Expected scheme 'basic', got {scheme.scheme!r}"
        raise AssertionError(errmsg)

    if scheme.description != "Basic authentication":
        errmsg = f"Expected description 'Basic authentication', got {scheme.description!r}"
        raise AssertionError(errmsg)

    return


def test_http_scheme_to_dict_defaults():
    """
        Test that HTTPSecurityScheme.to_dict() includes type and scheme fields.
    """
    scheme = HTTPSecurityScheme()
    result = scheme.to_dict()

    expected = {
        "type": "http",
        "scheme": "bearer"
    }

    if result != expected:
        errmsg = f"Expected {expected}, got {result}"
        raise AssertionError(errmsg)

    return


def test_http_scheme_to_dict_with_bearer_format():
    """
        Test that HTTPSecurityScheme.to_dict() includes bearerFormat when set.
    """
    scheme = HTTPSecurityScheme(bearer_format="JWT")
    result = scheme.to_dict()

    expected = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT"
    }

    if result != expected:
        errmsg = f"Expected {expected}, got {result}"
        raise AssertionError(errmsg)

    return


def test_http_scheme_to_dict_without_bearer_format():
    """
        Test that HTTPSecurityScheme.to_dict() omits bearerFormat when None.
    """
    scheme = HTTPSecurityScheme()
    result = scheme.to_dict()

    if "bearerFormat" in result:
        errmsg = "Expected 'bearerFormat' key to be absent when bearer_format is None"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for OAuth2SecurityScheme
# =============================================================================

def test_oauth2_scheme_defaults():
    """
        Test that OAuth2SecurityScheme has correct default values.
    """
    scheme = OAuth2SecurityScheme()

    if scheme.type != "oauth2":
        errmsg = f"Expected type 'oauth2', got {scheme.type!r}"
        raise AssertionError(errmsg)

    if scheme.flows is not None:
        errmsg = f"Expected flows to be None, got {scheme.flows!r}"
        raise AssertionError(errmsg)

    return


def test_oauth2_scheme_with_flows():
    """
        Test that OAuth2SecurityScheme can be created with OAuthFlows.
    """
    implicit_flow = OAuthFlow(
        scopes={"read": "Read access"},
        authorization_url="https://example.com/auth"
    )
    flows = OAuthFlows(implicit=implicit_flow)
    scheme = OAuth2SecurityScheme(flows=flows)

    if scheme.flows is not flows:
        errmsg = "Expected flows to match the provided OAuthFlows instance"
        raise AssertionError(errmsg)

    return


def test_oauth2_scheme_to_dict_without_flows():
    """
        Test that OAuth2SecurityScheme.to_dict() omits flows when None.
    """
    scheme = OAuth2SecurityScheme()
    result = scheme.to_dict()

    expected = {"type": "oauth2"}

    if result != expected:
        errmsg = f"Expected {expected}, got {result}"
        raise AssertionError(errmsg)

    if "flows" in result:
        errmsg = "Expected 'flows' key to be absent when flows is None"
        raise AssertionError(errmsg)

    return


def test_oauth2_scheme_to_dict_with_flows():
    """
        Test that OAuth2SecurityScheme.to_dict() includes flows when set.
    """
    auth_code_flow = OAuthFlow(
        scopes={"read": "Read", "write": "Write"},
        authorization_url="https://example.com/auth",
        token_url="https://example.com/token"
    )
    flows = OAuthFlows(authorization_code=auth_code_flow)
    scheme = OAuth2SecurityScheme(flows=flows, description="OAuth2 auth")
    result = scheme.to_dict()

    if "flows" not in result:
        errmsg = f"Expected 'flows' key in result, got keys: {list(result.keys())}"
        raise AssertionError(errmsg)

    flows_dict = result["flows"]

    if "authorizationCode" not in flows_dict:
        errmsg = f"Expected 'authorizationCode' in flows dict, got keys: {list(flows_dict.keys())}"
        raise AssertionError(errmsg)

    auth_code_dict = flows_dict["authorizationCode"]

    if auth_code_dict["scopes"] != {"read": "Read", "write": "Write"}:
        errmsg = f"Expected scopes {{'read': 'Read', 'write': 'Write'}}, got {auth_code_dict['scopes']!r}"
        raise AssertionError(errmsg)

    if result["description"] != "OAuth2 auth":
        errmsg = f"Expected description 'OAuth2 auth', got {result['description']!r}"
        raise AssertionError(errmsg)

    return


def test_oauth2_scheme_to_dict_nested_structure():
    """
        Test that OAuth2SecurityScheme.to_dict() produces correct nested structure.
    """
    implicit_flow = OAuthFlow(
        scopes={"profile": "Profile access"},
        authorization_url="https://example.com/authorize"
    )
    password_flow = OAuthFlow(
        scopes={"admin": "Admin access"},
        token_url="https://example.com/token"
    )
    flows = OAuthFlows(implicit=implicit_flow, password=password_flow)
    scheme = OAuth2SecurityScheme(flows=flows)
    result = scheme.to_dict()

    if result["type"] != "oauth2":
        errmsg = f"Expected type 'oauth2', got {result['type']!r}"
        raise AssertionError(errmsg)

    flows_dict = result["flows"]

    if len(flows_dict) != 2:
        errmsg = f"Expected 2 flow types, got {len(flows_dict)}: {list(flows_dict.keys())}"
        raise AssertionError(errmsg)

    implicit_dict = flows_dict["implicit"]

    if implicit_dict["authorizationUrl"] != "https://example.com/authorize":
        errmsg = f"Expected authorizationUrl 'https://example.com/authorize', got {implicit_dict['authorizationUrl']!r}"
        raise AssertionError(errmsg)

    password_dict = flows_dict["password"]

    if password_dict["tokenUrl"] != "https://example.com/token":
        errmsg = f"Expected tokenUrl 'https://example.com/token', got {password_dict['tokenUrl']!r}"
        raise AssertionError(errmsg)

    return
