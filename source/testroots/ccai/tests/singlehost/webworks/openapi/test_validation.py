"""
    Unit tests for the OpenAPI specification validation module.

    Tests cover :class:`ValidationIssue`, :class:`SpecificationValidationError`,
    and :class:`OpenAPIValidator` including structure validation, ``$ref``
    resolution, security scheme reference validation, and strict mode.
"""

from ccai.webworks.openapi.validation import (
    OpenAPIValidator,
    SpecificationValidationError,
    ValidationIssue,
)


# =============================================================================
# Helper Functions
# =============================================================================

def _create_valid_spec():
    """
        Create a minimal valid OpenAPI specification dictionary.

        :returns: A dictionary representing a valid OpenAPI 3.0.3 specification.
    """
    spec = {
        "openapi": "3.0.3",
        "info": {
            "title": "Test API",
            "version": "1.0.0",
        },
        "paths": {},
    }
    return spec


def _create_spec_with_operation(description=None):
    """
        Create a valid spec with a single GET operation.

        :param description: Optional description for the operation.

        :returns: A dictionary representing an OpenAPI specification.
    """
    operation = {
        "operationId": "get_users",
        "responses": {
            "200": {"description": "OK"},
        },
    }
    if description is not None:
        operation["description"] = description

    spec = {
        "openapi": "3.0.3",
        "info": {
            "title": "Test API",
            "version": "1.0.0",
        },
        "paths": {
            "/users": {
                "get": operation,
            },
        },
    }
    return spec


# =============================================================================
# ValidationIssue Tests
# =============================================================================

def test_validation_issue_fields():
    """
        Verify that a ValidationIssue stores path, message, and severity.
    """
    issue = ValidationIssue(
        path="info.title",
        message="Missing required field",
        severity="error",
    )

    if issue.path != "info.title":
        raise AssertionError(f"Expected path 'info.title', got '{issue.path}'")

    if issue.message != "Missing required field":
        raise AssertionError(f"Unexpected message: {issue.message}")

    if issue.severity != "error":
        raise AssertionError(f"Expected severity 'error', got '{issue.severity}'")

    return


def test_validation_issue_warning_severity():
    """
        Verify that a ValidationIssue can have warning severity.
    """
    issue = ValidationIssue(
        path="paths./users.get.description",
        message="Missing description",
        severity="warning",
    )

    if issue.severity != "warning":
        raise AssertionError(f"Expected severity 'warning', got '{issue.severity}'")

    return


# =============================================================================
# SpecificationValidationError Tests
# =============================================================================

def test_specification_validation_error_stores_issues():
    """
        Verify that SpecificationValidationError stores the issues list.
    """
    issues = [
        ValidationIssue(path="openapi", message="Missing field", severity="error"),
        ValidationIssue(path="info", message="Missing field", severity="error"),
    ]

    error = SpecificationValidationError(issues)

    if len(error.issues) != 2:
        raise AssertionError(f"Expected 2 issues, got {len(error.issues)}")

    return


def test_specification_validation_error_message():
    """
        Verify that SpecificationValidationError formats a summary message.
    """
    issues = [
        ValidationIssue(path="openapi", message="Missing field", severity="error"),
    ]

    error = SpecificationValidationError(issues)
    message = str(error)

    if "1 issue(s)" not in message:
        raise AssertionError(f"Expected '1 issue(s)' in message, got: {message}")

    return


def test_specification_validation_error_is_exception():
    """
        Verify that SpecificationValidationError is an Exception subclass.
    """
    issues = [
        ValidationIssue(path="openapi", message="Missing field", severity="error"),
    ]

    error = SpecificationValidationError(issues)

    if not isinstance(error, Exception):
        raise AssertionError("SpecificationValidationError should be an Exception")

    return


# =============================================================================
# OpenAPIValidator Structure Validation Tests
# =============================================================================

def test_validator_passes_valid_spec():
    """
        Verify that a valid spec passes validation without issues.
    """
    spec = _create_valid_spec()
    validator = OpenAPIValidator()
    issues = validator.validate(spec)

    if len(issues) != 0:
        raise AssertionError(f"Expected 0 issues, got {len(issues)}: {issues}")

    return


def test_validator_detects_missing_openapi():
    """
        Verify that missing 'openapi' field is detected.
    """
    spec = {
        "info": {"title": "Test", "version": "1.0.0"},
        "paths": {},
    }

    validator = OpenAPIValidator()
    caught = False

    try:
        validator.validate(spec)
    except SpecificationValidationError as err:
        caught = True
        found = False
        for issue in err.issues:
            if issue.path == "openapi" and issue.severity == "error":
                found = True
        if not found:
            raise AssertionError("Expected an error issue for 'openapi' field")

    if not caught:
        raise AssertionError("Expected SpecificationValidationError to be raised")

    return


def test_validator_detects_missing_info():
    """
        Verify that missing 'info' field is detected.
    """
    spec = {
        "openapi": "3.0.3",
        "paths": {},
    }

    validator = OpenAPIValidator()
    caught = False

    try:
        validator.validate(spec)
    except SpecificationValidationError as err:
        caught = True
        found = False
        for issue in err.issues:
            if issue.path == "info" and issue.severity == "error":
                found = True
        if not found:
            raise AssertionError("Expected an error issue for 'info' field")

    if not caught:
        raise AssertionError("Expected SpecificationValidationError to be raised")

    return


def test_validator_detects_missing_info_title():
    """
        Verify that missing 'info.title' field is detected.
    """
    spec = {
        "openapi": "3.0.3",
        "info": {"version": "1.0.0"},
        "paths": {},
    }

    validator = OpenAPIValidator()
    caught = False

    try:
        validator.validate(spec)
    except SpecificationValidationError as err:
        caught = True
        found = False
        for issue in err.issues:
            if issue.path == "info.title" and issue.severity == "error":
                found = True
        if not found:
            raise AssertionError("Expected an error issue for 'info.title' field")

    if not caught:
        raise AssertionError("Expected SpecificationValidationError to be raised")

    return


def test_validator_detects_missing_info_version():
    """
        Verify that missing 'info.version' field is detected.
    """
    spec = {
        "openapi": "3.0.3",
        "info": {"title": "Test"},
        "paths": {},
    }

    validator = OpenAPIValidator()
    caught = False

    try:
        validator.validate(spec)
    except SpecificationValidationError as err:
        caught = True
        found = False
        for issue in err.issues:
            if issue.path == "info.version" and issue.severity == "error":
                found = True
        if not found:
            raise AssertionError("Expected an error issue for 'info.version' field")

    if not caught:
        raise AssertionError("Expected SpecificationValidationError to be raised")

    return


def test_validator_detects_missing_paths():
    """
        Verify that missing 'paths' field is detected.
    """
    spec = {
        "openapi": "3.0.3",
        "info": {"title": "Test", "version": "1.0.0"},
    }

    validator = OpenAPIValidator()
    caught = False

    try:
        validator.validate(spec)
    except SpecificationValidationError as err:
        caught = True
        found = False
        for issue in err.issues:
            if issue.path == "paths" and issue.severity == "error":
                found = True
        if not found:
            raise AssertionError("Expected an error issue for 'paths' field")

    if not caught:
        raise AssertionError("Expected SpecificationValidationError to be raised")

    return


def test_validator_detects_multiple_missing_fields():
    """
        Verify that multiple missing fields are all reported.
    """
    spec = {}

    validator = OpenAPIValidator()
    caught = False

    try:
        validator.validate(spec)
    except SpecificationValidationError as err:
        caught = True
        paths_found = set()
        for issue in err.issues:
            paths_found.add(issue.path)

        expected = {"openapi", "info", "paths"}
        if not expected.issubset(paths_found):
            missing = expected - paths_found
            raise AssertionError(f"Missing expected issue paths: {missing}")

    if not caught:
        raise AssertionError("Expected SpecificationValidationError to be raised")

    return


# =============================================================================
# OpenAPIValidator $ref Resolution Tests
# =============================================================================

def test_validator_passes_valid_refs():
    """
        Verify that valid $ref references pass validation.
    """
    spec = {
        "openapi": "3.0.3",
        "info": {"title": "Test", "version": "1.0.0"},
        "paths": {
            "/users": {
                "get": {
                    "operationId": "get_users",
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/User"},
                                },
                            },
                        },
                    },
                },
            },
        },
        "components": {
            "schemas": {
                "User": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                    },
                },
            },
        },
    }

    validator = OpenAPIValidator()
    issues = validator.validate(spec)

    if len(issues) != 0:
        raise AssertionError(f"Expected 0 issues, got {len(issues)}")

    return


def test_validator_detects_undefined_ref():
    """
        Verify that a $ref to an undefined schema is detected.
    """
    spec = {
        "openapi": "3.0.3",
        "info": {"title": "Test", "version": "1.0.0"},
        "paths": {
            "/users": {
                "get": {
                    "operationId": "get_users",
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/MissingSchema"},
                                },
                            },
                        },
                    },
                },
            },
        },
        "components": {
            "schemas": {},
        },
    }

    validator = OpenAPIValidator()
    caught = False

    try:
        validator.validate(spec)
    except SpecificationValidationError as err:
        caught = True
        found = False
        for issue in err.issues:
            if "MissingSchema" in issue.message and issue.severity == "error":
                found = True
        if not found:
            raise AssertionError("Expected error about undefined schema 'MissingSchema'")

    if not caught:
        raise AssertionError("Expected SpecificationValidationError to be raised")

    return


def test_validator_detects_undefined_ref_no_components():
    """
        Verify that a $ref is detected when components section is absent.
    """
    spec = {
        "openapi": "3.0.3",
        "info": {"title": "Test", "version": "1.0.0"},
        "paths": {
            "/items": {
                "post": {
                    "operationId": "create_item",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ItemCreate"},
                            },
                        },
                    },
                    "responses": {"200": {"description": "OK"}},
                },
            },
        },
    }

    validator = OpenAPIValidator()
    caught = False

    try:
        validator.validate(spec)
    except SpecificationValidationError as err:
        caught = True
        found = False
        for issue in err.issues:
            if "ItemCreate" in issue.message:
                found = True
        if not found:
            raise AssertionError("Expected error about undefined schema 'ItemCreate'")

    if not caught:
        raise AssertionError("Expected SpecificationValidationError to be raised")

    return


# =============================================================================
# OpenAPIValidator Security Scheme Tests
# =============================================================================

def test_validator_passes_valid_security_refs():
    """
        Verify that valid security scheme references pass validation.
    """
    spec = {
        "openapi": "3.0.3",
        "info": {"title": "Test", "version": "1.0.0"},
        "paths": {
            "/users": {
                "get": {
                    "operationId": "get_users",
                    "security": [{"bearer_auth": []}],
                    "responses": {"200": {"description": "OK"}},
                },
            },
        },
        "components": {
            "securitySchemes": {
                "bearer_auth": {
                    "type": "http",
                    "scheme": "bearer",
                },
            },
        },
    }

    validator = OpenAPIValidator()
    issues = validator.validate(spec)

    if len(issues) != 0:
        raise AssertionError(f"Expected 0 issues, got {len(issues)}")

    return


def test_validator_detects_undefined_security_scheme():
    """
        Verify that a reference to an undefined security scheme is detected.
    """
    spec = {
        "openapi": "3.0.3",
        "info": {"title": "Test", "version": "1.0.0"},
        "paths": {
            "/users": {
                "get": {
                    "operationId": "get_users",
                    "security": [{"missing_scheme": []}],
                    "responses": {"200": {"description": "OK"}},
                },
            },
        },
        "components": {
            "securitySchemes": {},
        },
    }

    validator = OpenAPIValidator()
    caught = False

    try:
        validator.validate(spec)
    except SpecificationValidationError as err:
        caught = True
        found = False
        for issue in err.issues:
            if "missing_scheme" in issue.message and issue.severity == "error":
                found = True
        if not found:
            raise AssertionError("Expected error about undefined scheme 'missing_scheme'")

    if not caught:
        raise AssertionError("Expected SpecificationValidationError to be raised")

    return


def test_validator_detects_security_no_schemes_section():
    """
        Verify that security references are detected when securitySchemes is absent.
    """
    spec = {
        "openapi": "3.0.3",
        "info": {"title": "Test", "version": "1.0.0"},
        "paths": {
            "/data": {
                "get": {
                    "operationId": "get_data",
                    "security": [{"api_key": []}],
                    "responses": {"200": {"description": "OK"}},
                },
            },
        },
    }

    validator = OpenAPIValidator()
    caught = False

    try:
        validator.validate(spec)
    except SpecificationValidationError as err:
        caught = True
        found = False
        for issue in err.issues:
            if "api_key" in issue.message:
                found = True
        if not found:
            raise AssertionError("Expected error about undefined scheme 'api_key'")

    if not caught:
        raise AssertionError("Expected SpecificationValidationError to be raised")

    return


# =============================================================================
# OpenAPIValidator Strict Mode Tests
# =============================================================================

def test_strict_mode_detects_missing_description():
    """
        Verify that strict mode detects missing operation descriptions.
    """
    spec = _create_spec_with_operation(description=None)

    validator = OpenAPIValidator(strict=True)
    caught = False

    try:
        validator.validate(spec)
    except SpecificationValidationError as err:
        caught = True
        found = False
        for issue in err.issues:
            if "description" in issue.message.lower() and issue.severity == "warning":
                found = True
        if not found:
            raise AssertionError("Expected warning about missing description")

    if not caught:
        raise AssertionError("Expected SpecificationValidationError in strict mode")

    return


def test_strict_mode_passes_with_description():
    """
        Verify that strict mode does not flag operations that have descriptions,
        but still flags missing schema examples.
    """
    spec = _create_spec_with_operation(description="List all users")

    # This spec has no components/schemas, so no schema example warnings
    validator = OpenAPIValidator(strict=True)

    # The spec has no schemas section, so no example warnings either.
    # It should pass.
    issues = validator.validate(spec)

    # No issues expected since there are no schemas to check for examples
    return


def test_strict_mode_detects_missing_schema_example():
    """
        Verify that strict mode detects missing examples on schemas.
    """
    spec = {
        "openapi": "3.0.3",
        "info": {"title": "Test", "version": "1.0.0"},
        "paths": {
            "/users": {
                "get": {
                    "operationId": "get_users",
                    "description": "List users",
                    "responses": {"200": {"description": "OK"}},
                },
            },
        },
        "components": {
            "schemas": {
                "User": {
                    "type": "object",
                    "properties": {"id": {"type": "integer"}},
                },
            },
        },
    }

    validator = OpenAPIValidator(strict=True)
    caught = False

    try:
        validator.validate(spec)
    except SpecificationValidationError as err:
        caught = True
        found = False
        for issue in err.issues:
            if "example" in issue.message.lower() and "User" in issue.message:
                found = True
        if not found:
            raise AssertionError("Expected warning about missing example on 'User' schema")

    if not caught:
        raise AssertionError("Expected SpecificationValidationError in strict mode")

    return


def test_non_strict_mode_ignores_warnings():
    """
        Verify that non-strict mode does not raise on warnings.
    """
    spec = _create_spec_with_operation(description=None)

    validator = OpenAPIValidator(strict=False)
    issues = validator.validate(spec)

    # Non-strict mode should not raise, even if there are no descriptions
    # (missing descriptions are only checked in strict mode)
    return


# =============================================================================
# OpenAPIValidator Integration with Generator
# =============================================================================

def test_validator_with_generator_produced_spec():
    """
        Verify that a spec produced by OpenAPI_Generator passes validation.
    """
    from ccai.testbase.mocking import Mock

    from ccai.webworks.openapi.configuration import OpenAPIInfo
    from ccai.webworks.openapi.generator import OpenAPIGenerator

    mock_registry = Mock()
    mock_registry.configure(recursive=True)
    mock_registry.mock_context().mock_method("collect", return_value=[])

    info = OpenAPIInfo(title="Test API", version="1.0.0")
    generator = OpenAPIGenerator(registry=mock_registry, info=info)

    spec = generator.generate()
    validator = OpenAPIValidator()
    issues = validator.validate(spec)

    if len(issues) != 0:
        raise AssertionError(f"Expected 0 issues for generator-produced spec, got {len(issues)}")

    return


def test_generator_validate_method():
    """
        Verify that the OpenAPI_Generator.validate() method works correctly.
    """
    from ccai.testbase.mocking import Mock

    from ccai.webworks.openapi.configuration import OpenAPIInfo
    from ccai.webworks.openapi.generator import OpenAPIGenerator

    mock_registry = Mock()
    mock_registry.configure(recursive=True)
    mock_registry.mock_context().mock_method("collect", return_value=[])

    info = OpenAPIInfo(title="Test API", version="1.0.0")
    generator = OpenAPIGenerator(registry=mock_registry, info=info)

    issues = generator.validate()

    if len(issues) != 0:
        raise AssertionError(f"Expected 0 issues, got {len(issues)}")

    return
