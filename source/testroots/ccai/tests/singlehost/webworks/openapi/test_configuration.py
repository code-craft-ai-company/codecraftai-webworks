"""
    Tests for the OpenAPI configuration dataclasses module.

    This module contains unit tests for the ContactObject, LicenseObject,
    OpenAPIInfo, ServerVariable, ServerObject, and ExternalDocs dataclasses.
"""

from ccai.webworks.openapi.configuration import (
    ContactObject,
    ExternalDocs,
    LicenseObject,
    OpenAPIInfo,
    ServerObject,
    ServerVariable,
)


# =============================================================================
# Unit Tests for ContactObject
# =============================================================================

def test_contact_object_creation_with_all_fields():
    """
        Test that ContactObject can be created with all fields populated.
    """
    contact = ContactObject(name="API Support", url="https://example.com/support", email="support@example.com")

    if contact.name != "API Support":
        errmsg = f"Expected name 'API Support', got {contact.name!r}"
        raise AssertionError(errmsg)

    if contact.url != "https://example.com/support":
        errmsg = f"Expected url 'https://example.com/support', got {contact.url!r}"
        raise AssertionError(errmsg)

    if contact.email != "support@example.com":
        errmsg = f"Expected email 'support@example.com', got {contact.email!r}"
        raise AssertionError(errmsg)

    return


def test_contact_object_defaults_to_none():
    """
        Test that ContactObject fields default to None.
    """
    contact = ContactObject()

    if contact.name is not None:
        errmsg = f"Expected name to be None, got {contact.name!r}"
        raise AssertionError(errmsg)

    if contact.url is not None:
        errmsg = f"Expected url to be None, got {contact.url!r}"
        raise AssertionError(errmsg)

    if contact.email is not None:
        errmsg = f"Expected email to be None, got {contact.email!r}"
        raise AssertionError(errmsg)

    return


def test_contact_object_to_dict_all_fields():
    """
        Test that ContactObject.to_dict() includes all populated fields.
    """
    contact = ContactObject(name="API Support", url="https://example.com", email="api@example.com")
    result = contact.to_dict()

    expected = {
        "name": "API Support",
        "url": "https://example.com",
        "email": "api@example.com"
    }

    if result != expected:
        errmsg = f"Expected {expected}, got {result}"
        raise AssertionError(errmsg)

    return


def test_contact_object_to_dict_empty():
    """
        Test that ContactObject.to_dict() returns empty dict when no fields set.
    """
    contact = ContactObject()
    result = contact.to_dict()

    if len(result) != 0:
        errmsg = f"Expected empty dict, got {result}"
        raise AssertionError(errmsg)

    return


def test_contact_object_to_dict_partial_fields():
    """
        Test that ContactObject.to_dict() only includes non-None fields.
    """
    contact = ContactObject(name="Support Team")
    result = contact.to_dict()

    if "name" not in result:
        errmsg = "Expected 'name' key in result"
        raise AssertionError(errmsg)

    if "url" in result:
        errmsg = "Did not expect 'url' key in result when url is None"
        raise AssertionError(errmsg)

    if "email" in result:
        errmsg = "Did not expect 'email' key in result when email is None"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for LicenseObject
# =============================================================================

def test_license_object_creation():
    """
        Test that LicenseObject can be created with required and optional fields.
    """
    lic = LicenseObject(name="MIT", url="https://opensource.org/licenses/MIT")

    if lic.name != "MIT":
        errmsg = f"Expected name 'MIT', got {lic.name!r}"
        raise AssertionError(errmsg)

    if lic.url != "https://opensource.org/licenses/MIT":
        errmsg = f"Expected url 'https://opensource.org/licenses/MIT', got {lic.url!r}"
        raise AssertionError(errmsg)

    return


def test_license_object_url_defaults_to_none():
    """
        Test that LicenseObject url defaults to None.
    """
    lic = LicenseObject(name="Apache-2.0")

    if lic.url is not None:
        errmsg = f"Expected url to be None, got {lic.url!r}"
        raise AssertionError(errmsg)

    return


def test_license_object_to_dict_with_url():
    """
        Test that LicenseObject.to_dict() includes name and url.
    """
    lic = LicenseObject(name="MIT", url="https://opensource.org/licenses/MIT")
    result = lic.to_dict()

    expected = {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }

    if result != expected:
        errmsg = f"Expected {expected}, got {result}"
        raise AssertionError(errmsg)

    return


def test_license_object_to_dict_without_url():
    """
        Test that LicenseObject.to_dict() omits url when None.
    """
    lic = LicenseObject(name="Apache-2.0")
    result = lic.to_dict()

    if result != {"name": "Apache-2.0"}:
        errmsg = f"Expected {{'name': 'Apache-2.0'}}, got {result}"
        raise AssertionError(errmsg)

    if "url" in result:
        errmsg = "Did not expect 'url' key when url is None"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for OpenAPIInfo
# =============================================================================

def test_openapi_info_creation_required_fields():
    """
        Test that OpenAPIInfo can be created with only required fields.
    """
    info = OpenAPIInfo(title="My API", version="1.0.0")

    if info.title != "My API":
        errmsg = f"Expected title 'My API', got {info.title!r}"
        raise AssertionError(errmsg)

    if info.version != "1.0.0":
        errmsg = f"Expected version '1.0.0', got {info.version!r}"
        raise AssertionError(errmsg)

    if info.description is not None:
        errmsg = f"Expected description to be None, got {info.description!r}"
        raise AssertionError(errmsg)

    if info.terms_of_service is not None:
        errmsg = f"Expected terms_of_service to be None, got {info.terms_of_service!r}"
        raise AssertionError(errmsg)

    if info.contact is not None:
        errmsg = f"Expected contact to be None, got {info.contact!r}"
        raise AssertionError(errmsg)

    if info.license is not None:
        errmsg = f"Expected license to be None, got {info.license!r}"
        raise AssertionError(errmsg)

    return


def test_openapi_info_creation_all_fields():
    """
        Test that OpenAPIInfo can be created with all fields populated.
    """
    contact = ContactObject(name="Dev Team", email="dev@example.com")
    lic = LicenseObject(name="MIT")

    info = OpenAPIInfo(
        title="Test API",
        version="2.0.0",
        description="A test API",
        terms_of_service="https://example.com/tos",
        contact=contact,
        license=lic
    )

    if info.title != "Test API":
        errmsg = f"Expected title 'Test API', got {info.title!r}"
        raise AssertionError(errmsg)

    if info.description != "A test API":
        errmsg = f"Expected description 'A test API', got {info.description!r}"
        raise AssertionError(errmsg)

    if info.contact is not contact:
        errmsg = "Expected contact to be the provided ContactObject instance"
        raise AssertionError(errmsg)

    if info.license is not lic:
        errmsg = "Expected license to be the provided LicenseObject instance"
        raise AssertionError(errmsg)

    return


def test_openapi_info_to_dict_required_only():
    """
        Test that OpenAPIInfo.to_dict() includes only title and version when
        optional fields are None.
    """
    info = OpenAPIInfo(title="My API", version="1.0.0")
    result = info.to_dict()

    expected = {"title": "My API", "version": "1.0.0"}

    if result != expected:
        errmsg = f"Expected {expected}, got {result}"
        raise AssertionError(errmsg)

    return


def test_openapi_info_to_dict_all_fields():
    """
        Test that OpenAPIInfo.to_dict() includes all populated fields with
        correct OpenAPI key names.
    """
    contact = ContactObject(name="Dev Team", email="dev@example.com")
    lic = LicenseObject(name="MIT", url="https://opensource.org/licenses/MIT")

    info = OpenAPIInfo(
        title="Test API",
        version="2.0.0",
        description="A test API",
        terms_of_service="https://example.com/tos",
        contact=contact,
        license=lic
    )

    result = info.to_dict()

    if result["title"] != "Test API":
        errmsg = f"Expected title 'Test API', got {result['title']!r}"
        raise AssertionError(errmsg)

    if result["version"] != "2.0.0":
        errmsg = f"Expected version '2.0.0', got {result['version']!r}"
        raise AssertionError(errmsg)

    if result["description"] != "A test API":
        errmsg = f"Expected description 'A test API', got {result['description']!r}"
        raise AssertionError(errmsg)

    if result.get("termsOfService") != "https://example.com/tos":
        errmsg = f"Expected termsOfService 'https://example.com/tos', got {result.get('termsOfService')!r}"
        raise AssertionError(errmsg)

    if "terms_of_service" in result:
        errmsg = "Key should be 'termsOfService' not 'terms_of_service' per OpenAPI spec"
        raise AssertionError(errmsg)

    contact_dict = result.get("contact")
    if contact_dict is None:
        errmsg = "Expected 'contact' key in result"
        raise AssertionError(errmsg)

    if contact_dict != {"name": "Dev Team", "email": "dev@example.com"}:
        errmsg = f"Expected contact dict with name and email, got {contact_dict}"
        raise AssertionError(errmsg)

    license_dict = result.get("license")
    if license_dict is None:
        errmsg = "Expected 'license' key in result"
        raise AssertionError(errmsg)

    if license_dict != {"name": "MIT", "url": "https://opensource.org/licenses/MIT"}:
        errmsg = f"Expected license dict with name and url, got {license_dict}"
        raise AssertionError(errmsg)

    return


def test_openapi_info_to_dict_with_description_only():
    """
        Test that OpenAPIInfo.to_dict() includes description when set but
        omits other optional fields.
    """
    info = OpenAPIInfo(title="My API", version="1.0.0", description="An API description")
    result = info.to_dict()

    if result.get("description") != "An API description":
        errmsg = f"Expected description 'An API description', got {result.get('description')!r}"
        raise AssertionError(errmsg)

    if "termsOfService" in result:
        errmsg = "Did not expect 'termsOfService' when terms_of_service is None"
        raise AssertionError(errmsg)

    if "contact" in result:
        errmsg = "Did not expect 'contact' when contact is None"
        raise AssertionError(errmsg)

    if "license" in result:
        errmsg = "Did not expect 'license' when license is None"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for ServerVariable
# =============================================================================

def test_server_variable_creation():
    """
        Test that ServerVariable can be created with all fields.
    """
    var = ServerVariable(
        default="v1",
        enum=["v1", "v2", "v3"],
        description="API version"
    )

    if var.default != "v1":
        errmsg = f"Expected default 'v1', got {var.default!r}"
        raise AssertionError(errmsg)

    if var.enum != ["v1", "v2", "v3"]:
        errmsg = f"Expected enum ['v1', 'v2', 'v3'], got {var.enum!r}"
        raise AssertionError(errmsg)

    if var.description != "API version":
        errmsg = f"Expected description 'API version', got {var.description!r}"
        raise AssertionError(errmsg)

    return


def test_server_variable_defaults():
    """
        Test that ServerVariable optional fields default to None.
    """
    var = ServerVariable(default="production")

    if var.enum is not None:
        errmsg = f"Expected enum to be None, got {var.enum!r}"
        raise AssertionError(errmsg)

    if var.description is not None:
        errmsg = f"Expected description to be None, got {var.description!r}"
        raise AssertionError(errmsg)

    return


def test_server_variable_to_dict_all_fields():
    """
        Test that ServerVariable.to_dict() includes all populated fields.
    """
    var = ServerVariable(default="v1", enum=["v1", "v2"], description="Version")
    result = var.to_dict()

    expected = {
        "default": "v1",
        "enum": ["v1", "v2"],
        "description": "Version"
    }

    if result != expected:
        errmsg = f"Expected {expected}, got {result}"
        raise AssertionError(errmsg)

    return


def test_server_variable_to_dict_default_only():
    """
        Test that ServerVariable.to_dict() includes only default when
        optional fields are None.
    """
    var = ServerVariable(default="production")
    result = var.to_dict()

    if result != {"default": "production"}:
        errmsg = f"Expected {{'default': 'production'}}, got {result}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for ServerObject
# =============================================================================

def test_server_object_creation():
    """
        Test that ServerObject can be created with all fields.
    """
    variables = {
        "version": ServerVariable(default="v1", enum=["v1", "v2"])
    }
    server = ServerObject(
        url="https://api.example.com/{version}",
        description="Production server",
        variables=variables
    )

    if server.url != "https://api.example.com/{version}":
        errmsg = f"Expected url 'https://api.example.com/{{version}}', got {server.url!r}"
        raise AssertionError(errmsg)

    if server.description != "Production server":
        errmsg = f"Expected description 'Production server', got {server.description!r}"
        raise AssertionError(errmsg)

    if server.variables is not variables:
        errmsg = "Expected variables to be the provided dict instance"
        raise AssertionError(errmsg)

    return


def test_server_object_defaults():
    """
        Test that ServerObject optional fields default to None.
    """
    server = ServerObject(url="https://api.example.com")

    if server.description is not None:
        errmsg = f"Expected description to be None, got {server.description!r}"
        raise AssertionError(errmsg)

    if server.variables is not None:
        errmsg = f"Expected variables to be None, got {server.variables!r}"
        raise AssertionError(errmsg)

    return


def test_server_object_to_dict_url_only():
    """
        Test that ServerObject.to_dict() includes only url when optional
        fields are None.
    """
    server = ServerObject(url="https://api.example.com")
    result = server.to_dict()

    if result != {"url": "https://api.example.com"}:
        errmsg = f"Expected {{'url': 'https://api.example.com'}}, got {result}"
        raise AssertionError(errmsg)

    return


def test_server_object_to_dict_all_fields():
    """
        Test that ServerObject.to_dict() includes all fields and converts
        variables using their to_dict() method.
    """
    variables = {
        "version": ServerVariable(default="v1", enum=["v1", "v2"]),
        "env": ServerVariable(default="prod", description="Environment")
    }
    server = ServerObject(
        url="https://{env}.api.example.com/{version}",
        description="Configurable server",
        variables=variables
    )

    result = server.to_dict()

    if result["url"] != "https://{env}.api.example.com/{version}":
        errmsg = f"Expected url with template variables, got {result['url']!r}"
        raise AssertionError(errmsg)

    if result["description"] != "Configurable server":
        errmsg = f"Expected description 'Configurable server', got {result['description']!r}"
        raise AssertionError(errmsg)

    result_variables = result.get("variables")
    if result_variables is None:
        errmsg = "Expected 'variables' key in result"
        raise AssertionError(errmsg)

    version_var = result_variables.get("version")
    if version_var is None:
        errmsg = "Expected 'version' key in variables"
        raise AssertionError(errmsg)

    if version_var != {"default": "v1", "enum": ["v1", "v2"]}:
        errmsg = f"Expected version variable dict, got {version_var}"
        raise AssertionError(errmsg)

    env_var = result_variables.get("env")
    if env_var is None:
        errmsg = "Expected 'env' key in variables"
        raise AssertionError(errmsg)

    if env_var != {"default": "prod", "description": "Environment"}:
        errmsg = f"Expected env variable dict, got {env_var}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for ExternalDocs
# =============================================================================

def test_external_docs_creation():
    """
        Test that ExternalDocs can be created with all fields.
    """
    docs = ExternalDocs(url="https://docs.example.com", description="Full documentation")

    if docs.url != "https://docs.example.com":
        errmsg = f"Expected url 'https://docs.example.com', got {docs.url!r}"
        raise AssertionError(errmsg)

    if docs.description != "Full documentation":
        errmsg = f"Expected description 'Full documentation', got {docs.description!r}"
        raise AssertionError(errmsg)

    return


def test_external_docs_defaults():
    """
        Test that ExternalDocs description defaults to None.
    """
    docs = ExternalDocs(url="https://docs.example.com")

    if docs.description is not None:
        errmsg = f"Expected description to be None, got {docs.description!r}"
        raise AssertionError(errmsg)

    return


def test_external_docs_to_dict_with_description():
    """
        Test that ExternalDocs.to_dict() includes url and description.
    """
    docs = ExternalDocs(url="https://docs.example.com", description="Full docs")
    result = docs.to_dict()

    expected = {"url": "https://docs.example.com", "description": "Full docs"}

    if result != expected:
        errmsg = f"Expected {expected}, got {result}"
        raise AssertionError(errmsg)

    return


def test_external_docs_to_dict_url_only():
    """
        Test that ExternalDocs.to_dict() omits description when None.
    """
    docs = ExternalDocs(url="https://docs.example.com")
    result = docs.to_dict()

    if result != {"url": "https://docs.example.com"}:
        errmsg = f"Expected {{'url': 'https://docs.example.com'}}, got {result}"
        raise AssertionError(errmsg)

    if "description" in result:
        errmsg = "Did not expect 'description' key when description is None"
        raise AssertionError(errmsg)

    return
